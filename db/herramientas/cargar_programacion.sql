-- Carga de la programación docente del ciclo en una sola transacción (spec 006, US-55 a US-57, FR-004 a FR-007).
-- Lo corre db/herramientas/cargar_programacion.py, que revisa antes la forma de cada fila (FR-003) y entrega todas
-- las filas por la entrada estándar, cada una con su número y la marca de su falla de forma. No se corre a mano.
--
--   psql -X -w -q -A -t -v ON_ERROR_STOP=1 -v periodo=2026-2 -v aplicar=0 [-v con_nombre=1] -f db/herramientas/cargar_programacion.sql
--
-- La corrida en seco (aplicar=0) y la corrida con --aplicar (aplicar=1) ejecutan este mismo SQL. La primera termina
-- con ROLLBACK y la segunda con COMMIT, así que el informe en seco cuenta exactamente lo que la corrida real
-- escribiría (FR-006). Cualquier error de la base detiene psql con ON_ERROR_STOP y deshace la transacción entera.
--
-- Revisiones de la base (FR-004). El periodo existe en abet.periodo, cada asignatura existe en abet.asignatura,
-- ningún curso de Blackboard del archivo es de otra sección en la base (uq_seccion_curso_bb, que es global) y una
-- sección que ya tiene otro curso no lo cambia. Solo se revisan las filas sin falla de forma, con un motivo por
-- fila en ese orden. Con una sola falla, de forma o de la base, el SQL escribe los motivos y cierra con ROLLBACK
-- antes de cualquier INSERT, y el guion termina con código 1.
--
-- Escritura (FR-005 y AD-03). Solo INSERT con ON CONFLICT DO NOTHING sobre la restricción única que corresponde,
-- nombrada en cada uno, y dos UPDATE, que completan el curso_blackboard nulo de una sección que ya existe y, desde la
-- spec 010 (FR-005), el nombre nulo de un usuario PROFESOR que ya existe. Un nombre ya guardado no cambia, y el
-- informe lo avisa sin escribir ningún nombre, y una cuenta COORDINADOR nunca recibe nombre. Con
-- el objetivo nombrado, un choque de uq_seccion_curso_bb que la revisión no ve, por otra carga que corre a la vez,
-- llega como error de la base y no se salta en silencio. Nunca borra, nunca cambia rol ni activo y no toca
-- acceso.credencial, abet.plan_medicion ni ninguna tabla de cargas.
--
-- La columna nombre (spec 010). con_nombre vale 1 cuando el archivo trae la columna, y 0 por omisión. Una base que todavía
-- no tiene V1_16 sigue cargando un archivo sin la columna como en la spec 006, y con la columna se detiene con un error
-- antes de escribir nada. Los pasos que tocan acceso.usuario_autorizado.nombre van dentro de \if, así que psql nunca
-- manda a una base sin V1_16 una sentencia que nombra la columna.
--
-- Salida. Cada línea es un arreglo JSON que el guion lee y convierte en el informe, sin reenviar nunca el texto de
-- un error de psql. ["E", fila, motivo, ...] es una falla de la base, ["P", periodo] un periodo que no existe,
-- ["R", secciones, usuarios, asignaciones, cursos, nombres] el resumen, ["A", tipo, ...] un aviso y ["FIN", estado] la línea
-- centinela, que es RECHAZADO, SECO o GUARDADO. GUARDADO sale solo después de un COMMIT que la base aceptó.

\set ON_ERROR_STOP 1
\set VERBOSITY sqlstate
\if :{?periodo}
\else
    \echo 'Falta el periodo, por ejemplo -v periodo=2026-2.'
    SELECT CAST('falta el periodo' AS integer);
\endif
\if :{?aplicar}
\else
    \echo 'Falta aplicar, por ejemplo -v aplicar=0.'
    SELECT CAST('falta aplicar' AS integer);
\endif
\if :{?con_nombre}
\else
    \set con_nombre 0
\endif
\pset format unaligned
\pset tuples_only on

BEGIN;

-- Si la base tiene la columna nombre de V1_16 (spec 010). El archivo con la columna en una base sin ella se detiene.
SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'acceso'
               AND table_name = 'usuario_autorizado' AND column_name = 'nombre')::integer AS base_con_nombre
\gset
SELECT (:con_nombre = 1 AND :base_con_nombre = 0)::integer AS falta_v1_16
\gset
\if :falta_v1_16
    SELECT CAST('falta V1_16' AS integer);
\endif

-- Filas del archivo. Una fila con falla de forma llega sin sus valores y con_error verdadero.
CREATE TEMP TABLE programacion_archivo (
    fila              integer NOT NULL,
    con_error         boolean NOT NULL,
    asignatura        text,
    seccion           text,
    correo            text,
    curso_blackboard  text,
    nombre            text
) ON COMMIT DROP;
\copy programacion_archivo FROM pstdin WITH (FORMAT csv)

-- Fallas de la base de las filas sin falla de forma, con el primer motivo de cada fila.
CREATE TEMP TABLE programacion_falla ON COMMIT DROP AS
SELECT fila, registro FROM (
SELECT ar.fila,
       CASE
           WHEN a.asignatura_id IS NULL THEN json_build_array('E', ar.fila, 'ASIGNATURA', ar.asignatura)
           WHEN otra.seccion_id IS NOT NULL THEN
               json_build_array('E', ar.fila, 'CURSO_DE_OTRA', ar.curso_blackboard, otra.numero, otra.asignatura)
           WHEN propia.curso_blackboard IS NOT NULL AND ar.curso_blackboard IS NOT NULL
                AND propia.curso_blackboard <> ar.curso_blackboard THEN
               json_build_array('E', ar.fila, 'OTRO_CURSO', ar.seccion, ar.asignatura)
       END AS registro
FROM programacion_archivo ar
LEFT JOIN abet.asignatura a ON a.codigo = ar.asignatura
LEFT JOIN abet.periodo pe ON pe.codigo = :'periodo'
LEFT JOIN abet.seccion propia ON propia.periodo_id = pe.periodo_id AND propia.asignatura_id = a.asignatura_id
                             AND propia.numero = ar.seccion
-- Sin periodo en la base no hay sección propia que comparar, así que el curso no se informa como de otra sección,
-- un motivo que parecería contradecir la fila. El periodo inexistente ya rechaza el archivo.
LEFT JOIN LATERAL (
    SELECT s.seccion_id, s.numero, sa.codigo AS asignatura
    FROM abet.seccion s
    JOIN abet.asignatura sa ON sa.asignatura_id = s.asignatura_id
    WHERE s.curso_blackboard = ar.curso_blackboard AND pe.periodo_id IS NOT NULL
      AND (s.periodo_id IS DISTINCT FROM pe.periodo_id OR s.asignatura_id <> a.asignatura_id OR s.numero <> ar.seccion)
) otra ON true
WHERE NOT ar.con_error
) revisadas
WHERE registro IS NOT NULL;

SELECT (EXISTS (SELECT 1 FROM programacion_archivo WHERE con_error)
        OR EXISTS (SELECT 1 FROM programacion_falla)
        OR NOT EXISTS (SELECT 1 FROM abet.periodo WHERE codigo = :'periodo'))::integer AS rechazar
\gset

\if :rechazar
    SELECT json_build_array('P', CAST(:'periodo' AS text))
    WHERE NOT EXISTS (SELECT 1 FROM abet.periodo WHERE codigo = :'periodo');
    SELECT registro FROM programacion_falla ORDER BY fila;
    SELECT json_build_array('FIN', 'RECHAZADO');
    ROLLBACK;
\else
    -- Una fila por sección del archivo, con su curso, que la revisión de forma deja en uno solo o en ninguno.
    CREATE TEMP TABLE programacion_seccion ON COMMIT DROP AS
    SELECT pe.periodo_id, a.asignatura_id, a.codigo AS asignatura, ar.seccion AS numero,
           max(ar.curso_blackboard) AS curso_blackboard, min(ar.fila) AS fila
    FROM programacion_archivo ar
    JOIN abet.asignatura a ON a.codigo = ar.asignatura
    JOIN abet.periodo pe ON pe.codigo = :'periodo'
    GROUP BY pe.periodo_id, a.asignatura_id, a.codigo, ar.seccion;

    -- El único UPDATE de FR-005, el curso nulo de una sección que ya existe.
    WITH completados AS (
        UPDATE abet.seccion s SET curso_blackboard = ps.curso_blackboard
        FROM programacion_seccion ps
        WHERE s.periodo_id = ps.periodo_id AND s.asignatura_id = ps.asignatura_id AND s.numero = ps.numero
          AND s.curso_blackboard IS NULL AND ps.curso_blackboard IS NOT NULL
        RETURNING 1
    )
    SELECT count(*) AS cursos_completados FROM completados
    \gset

    WITH nuevas AS (
        INSERT INTO abet.seccion (periodo_id, asignatura_id, numero, curso_blackboard)
        SELECT periodo_id, asignatura_id, numero, curso_blackboard FROM programacion_seccion ORDER BY fila
        ON CONFLICT (periodo_id, asignatura_id, numero) DO NOTHING
        RETURNING 1
    )
    SELECT count(*) AS secciones_nuevas FROM nuevas
    \gset

    -- Un nombre por correo. El guion de Python rechaza el archivo si un correo trae dos nombres distintos, y una celda
    -- vacía llega como texto vacío, que aquí es sin nombre.
    CREATE TEMP TABLE programacion_nombre ON COMMIT DROP AS
    SELECT correo, max(nullif(nombre, '')) AS nombre FROM programacion_archivo GROUP BY correo;
    -- Los correos de la base que ya tienen otro nombre, para el aviso, que no puede nombrar la columna en una base sin V1_16.
    CREATE TEMP TABLE programacion_otro_nombre (correo text NOT NULL, fila integer NOT NULL) ON COMMIT DROP;

    \if :base_con_nombre
        -- El segundo UPDATE de FR-005 de la spec 010, antes del INSERT de usuarios para contar solo a quien ya existía.
        -- Solo completa el nombre nulo de un PROFESOR. Un nombre guardado, el rol y el estado no cambian.
        WITH completados AS (
            UPDATE acceso.usuario_autorizado u SET nombre = pn.nombre
            FROM programacion_nombre pn
            WHERE u.correo = pn.correo AND u.rol = 'PROFESOR' AND u.nombre IS NULL AND pn.nombre IS NOT NULL
            RETURNING 1
        )
        SELECT count(*) AS nombres_completados FROM completados
        \gset

        -- Un correo nuevo entra con rol PROFESOR, activo, sin contraseña (D-45) y con el nombre del archivo, si lo trae.
        -- Uno que ya existe no cambia aquí.
        WITH nuevos AS (
            INSERT INTO acceso.usuario_autorizado (correo, rol, nombre)
            SELECT pn.correo, 'PROFESOR', pn.nombre
            FROM programacion_nombre pn JOIN programacion_archivo ar ON ar.correo = pn.correo
            GROUP BY pn.correo, pn.nombre ORDER BY min(ar.fila)
            ON CONFLICT (correo) DO NOTHING
            RETURNING 1
        )
        SELECT count(*) AS usuarios_nuevos FROM nuevos
        \gset

        INSERT INTO programacion_otro_nombre (correo, fila)
        SELECT u.correo, min(ar.fila)
        FROM programacion_archivo ar
        JOIN programacion_nombre pn ON pn.correo = ar.correo
        JOIN acceso.usuario_autorizado u ON u.correo = ar.correo
        WHERE pn.nombre IS NOT NULL AND u.nombre IS NOT NULL AND u.nombre <> pn.nombre
        GROUP BY u.correo;
    \else
        SELECT 0 AS nombres_completados
        \gset

        -- Un correo nuevo entra con rol PROFESOR, activo y sin contraseña (D-45). Uno que ya existe no cambia.
        WITH nuevos AS (
            INSERT INTO acceso.usuario_autorizado (correo, rol)
            SELECT correo, 'PROFESOR' FROM programacion_archivo GROUP BY correo ORDER BY min(fila)
            ON CONFLICT (correo) DO NOTHING
            RETURNING 1
        )
        SELECT count(*) AS usuarios_nuevos FROM nuevos
        \gset
    \endif

    WITH nuevas AS (
        INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)
        SELECT u.usuario_id, s.seccion_id
        FROM programacion_archivo ar
        JOIN acceso.usuario_autorizado u ON u.correo = ar.correo
        JOIN programacion_seccion ps ON ps.asignatura = ar.asignatura AND ps.numero = ar.seccion
        JOIN abet.seccion s ON s.periodo_id = ps.periodo_id AND s.asignatura_id = ps.asignatura_id
                           AND s.numero = ps.numero
        GROUP BY u.usuario_id, s.seccion_id
        ORDER BY min(ar.fila)
        ON CONFLICT (usuario_id, seccion_id) DO NOTHING
        RETURNING 1
    )
    SELECT count(*) AS asignaciones_nuevas FROM nuevas
    \gset

    SELECT json_build_array('R', :secciones_nuevas, :usuarios_nuevos, :asignaciones_nuevas, :cursos_completados,
                            :nombres_completados);

    -- Avisos de FR-007. Primero los de las filas del archivo, en el orden de las filas, y después lo que la base
    -- tiene en el periodo y el archivo no trae, por asignatura, sección y correo.
    WITH archivo AS (
        SELECT ar.fila, ar.correo, ps.asignatura, ps.numero, ps.asignatura_id, ps.periodo_id
        FROM programacion_archivo ar
        JOIN programacion_seccion ps ON ps.asignatura = ar.asignatura AND ps.numero = ar.seccion
    ),
    avisos AS (
        SELECT 1 AS grupo, min(ar.fila) AS fila, ar.asignatura, ar.numero, 1 AS tipo, u.correo,
               json_build_array('A', 'COORDINADOR', u.correo, ar.numero, ar.asignatura) AS registro
        FROM archivo ar JOIN acceso.usuario_autorizado u ON u.correo = ar.correo
        WHERE u.rol = 'COORDINADOR'
        GROUP BY u.correo, ar.asignatura, ar.numero
        UNION ALL
        SELECT 1, min(ar.fila), ar.asignatura, ar.numero, 2, u.correo,
               json_build_array('A', 'BAJA', u.correo, ar.numero, ar.asignatura)
        FROM archivo ar JOIN acceso.usuario_autorizado u ON u.correo = ar.correo
        WHERE NOT u.activo
        GROUP BY u.correo, ar.asignatura, ar.numero
        UNION ALL
        SELECT 1, ps.fila, ps.asignatura, ps.numero, 3, '',
               json_build_array('A', 'SIN_PLAN', ps.asignatura, CAST(:'periodo' AS text), ps.numero)
        FROM programacion_seccion ps
        WHERE NOT EXISTS (SELECT 1 FROM abet.plan_medicion pm
                          WHERE pm.periodo_id = ps.periodo_id AND pm.asignatura_id = ps.asignatura_id)
        UNION ALL
        SELECT 1, ps.fila, ps.asignatura, ps.numero, 4, '',
               json_build_array('A', 'FUERA_DEL_PLAN', ps.asignatura, CAST(:'periodo' AS text), ps.numero)
        FROM programacion_seccion ps
        WHERE NOT EXISTS (SELECT 1 FROM abet.catalogo_vigencia v
                          JOIN abet.plan_estudios pl ON pl.catalogo_version_id = v.catalogo_version_id
                          WHERE v.periodo_id = ps.periodo_id AND pl.asignatura_id = ps.asignatura_id)
        UNION ALL
        SELECT 2, 0, a.codigo, s.numero, 5, '',
               json_build_array('A', 'SECCION_AUSENTE', s.numero, a.codigo,
                                (SELECT count(*) FROM acceso.docente_seccion d WHERE d.seccion_id = s.seccion_id))
        FROM abet.seccion s
        JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
        JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = :'periodo'
        WHERE NOT EXISTS (SELECT 1 FROM programacion_seccion ps
                          WHERE ps.asignatura_id = s.asignatura_id AND ps.numero = s.numero)
        UNION ALL
        -- Spec 010. El correo ya tiene en la base otro nombre, que no se cambia. El aviso lleva el correo y ningún nombre.
        SELECT 1, o.fila, '', '0', 7, o.correo, json_build_array('A', 'OTRO_NOMBRE', o.correo)
        FROM programacion_otro_nombre o
        UNION ALL
        SELECT 2, 0, a.codigo, s.numero, 6, u.correo,
               json_build_array('A', 'ASIGNACION_AUSENTE', s.numero, a.codigo, u.correo)
        FROM acceso.docente_seccion d
        JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
        JOIN abet.seccion s ON s.seccion_id = d.seccion_id
        JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
        JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = :'periodo'
        WHERE NOT EXISTS (SELECT 1 FROM archivo ar
                          WHERE ar.asignatura_id = s.asignatura_id AND ar.numero = s.numero AND ar.correo = u.correo)
    )
    SELECT registro FROM avisos
    ORDER BY grupo, fila, CASE WHEN grupo = 2 THEN asignatura END, CAST(numero AS integer), tipo, correo;

    \if :aplicar
        COMMIT;
        SELECT json_build_array('FIN', 'GUARDADO');
    \else
        ROLLBACK;
        SELECT json_build_array('FIN', 'SECO');
    \endif
\endif
