-- Alcance de la capacitación de Química General, de solo lectura (spec 008, US-86, SC-006 y T071). Después de la
-- siembra de la capacitación en la rama develop, cuenta las secciones de la asignatura en el periodo con plan de
-- medición, sus filas de acceso.docente_seccion, los profesores distintos de esas filas (cuentas PROFESOR activas,
-- cada una una sola vez aunque tenga dos secciones), las filas de acceso.coordinacion_alcance de la asignatura en el
-- periodo y cuántas de sus secciones cubre el alcance de una cuenta COORDINADOR activa. Con la capacitación de 5643 en
-- 2026-1 espera 18 secciones, 18 filas, 18 profesores, 1 fila de alcance y 18 secciones cubiertas.
-- La salida trae una línea «etiqueta|valor» por conteo, con la asignatura y el periodo al comienzo. Nunca muestra un
-- correo, un nombre, un número de sección, un curso de Blackboard ni un código de estudiante. La sesión pasa a solo
-- lectura antes de la primera consulta, así que no cambia nada aunque la corra el dueño de la base.
-- La corre Jefferson desde el Windows con sql_lectura de herramientas_neon/lectura_neon.sh, que la pasa por la
-- entrada estándar de psql sin variables, así que la asignatura y el periodo toman 5643 y 2026-1 por omisión. Con psql
-- directo se pueden cambiar con -v.
--
--   source herramientas_neon/lectura_neon.sh
--   sql_lectura develop < db/plataforma/neon/alcance_capacitacion.sql
--   psql -X -At -v ON_ERROR_STOP=1 -v asignatura=5643 -v periodo=2026-1 -f db/plataforma/neon/alcance_capacitacion.sql
--
-- Las pruebas de capacitacion_en_develop.feature la corren con la cabecera y el filtro de sql_lectura, que rechaza
-- las sentencias que escriben, así que este archivo no las nombra ni en los comentarios.

\set ON_ERROR_STOP 1
\if :{?asignatura}
\else
    \set asignatura 5643
\endif
\if :{?periodo}
\else
    \set periodo 2026-1
\endif
SET default_transaction_read_only = on;
\pset footer off

WITH curso AS (
    SELECT s.seccion_id, s.asignatura_id, s.periodo_id
    FROM abet.seccion s
    JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
    JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id
    WHERE a.codigo = :'asignatura' AND pe.codigo = :'periodo'
),
asignaciones AS (
    SELECT d.usuario_id, u.rol, u.activo
    FROM acceso.docente_seccion d
    JOIN curso c ON c.seccion_id = d.seccion_id
    JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
),
alcance AS (
    SELECT ca.asignatura_id, ca.periodo_id, u.rol, u.activo
    FROM acceso.coordinacion_alcance ca
    JOIN abet.asignatura a ON a.asignatura_id = ca.asignatura_id
    JOIN abet.periodo pe ON pe.periodo_id = ca.periodo_id
    JOIN acceso.usuario_autorizado u ON u.usuario_id = ca.usuario_id
    WHERE a.codigo = :'asignatura' AND pe.codigo = :'periodo'
)
SELECT etiqueta, valor FROM (
    SELECT 1 AS orden, 'asignatura' AS etiqueta, :'asignatura' AS valor
    UNION ALL
    SELECT 2, 'periodo', :'periodo'
    UNION ALL
    SELECT 3, 'secciones con plan', count(*)::text
    FROM curso c
    WHERE EXISTS (SELECT 1 FROM abet.plan_medicion pm
                  WHERE pm.asignatura_id = c.asignatura_id AND pm.periodo_id = c.periodo_id)
    UNION ALL
    SELECT 4, 'filas de acceso.docente_seccion', count(*)::text FROM asignaciones
    UNION ALL
    SELECT 5, 'profesores distintos', count(DISTINCT usuario_id)::text
    FROM asignaciones WHERE rol = 'PROFESOR' AND activo
    UNION ALL
    SELECT 6, 'filas de alcance', count(*)::text FROM alcance
    UNION ALL
    SELECT 7, 'secciones que cubre el alcance', count(*)::text
    FROM curso c
    WHERE EXISTS (SELECT 1 FROM alcance x
                  WHERE x.asignatura_id = c.asignatura_id AND x.periodo_id = c.periodo_id
                    AND x.rol = 'COORDINADOR' AND x.activo)
) AS conteos
ORDER BY orden;
