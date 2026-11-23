-- Huella de Ingeniería Ambiental, de solo lectura (spec 008, US-69, US-86, FR-020 y SC-005). Resume en una huella
-- SHA-256 todo lo que mide Ambiental, para comparar la base antes y después de la siembra de Química, que no debe
-- cambiar nada de Ambiental. Cubre los catálogos de la carrera AMB con sus SO, PI, rúbricas, plan de estudios, pares
-- asignatura y SO, instrumentos y competencias, sus vigencias, su plan de medición con la descripción del instrumento,
-- sus conjuntos de reglas con sus parámetros, las secciones de las asignaturas que Ambiental mide en cada periodo con
-- sus profesores (por usuario_id) y las cargas de la carrera con sus columnas, filas, mediciones y rechazos.
-- No cubre acceso.coordinacion_alcance ni las cuentas, que la siembra cambia a propósito (V1_14,
-- alcance_coordinacion_ambiental.sql y registrar_coordinacion.py).
-- La salida trae una fila por parte, con su número de filas y los primeros 16 caracteres de su huella, y la fila
-- final «HUELLA DE AMBIENTAL» con el total de filas y la huella completa. Nunca muestra un correo, un nombre ni un
-- código de estudiante, porque los códigos entran solo a la huella. La sesión pasa a solo lectura antes de la primera
-- consulta, así que el script no escribe aunque lo corra el dueño de la base. En Neon lo corre Jefferson desde el
-- Windows con abet_respaldo y lectura_neon.sh.
--
--   psql "host=$NEON_HOST dbname=$NEON_DB user=abet_respaldo sslmode=verify-full sslrootcert=system" \
--        -X -f db/plataforma/neon/huella_ambiental.sql

\set ON_ERROR_STOP 1
SET default_transaction_read_only = on;
\pset footer off

WITH amb AS (SELECT carrera_id FROM abet.carrera WHERE codigo = 'AMB'),
versiones AS (SELECT cv.catalogo_version_id FROM abet.catalogo_version cv JOIN amb USING (carrera_id)),
secciones AS (
    SELECT DISTINCT s.seccion_id, pe.codigo || '/' || a.codigo || '/' || s.numero AS clave, s.curso_blackboard
    FROM abet.seccion s
    JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id
    JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
    JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
    JOIN amb ON amb.carrera_id = pm.carrera_id
),
cargas AS (SELECT c.* FROM abet.carga c JOIN amb USING (carrera_id)),
partes AS (
SELECT 1 AS orden, 'catálogo' AS parte, count(*) AS filas,
       string_agg(concat_ws('|', cv.codigo, cv.estado, cv.huella_fuente, cv.vigente_desde_periodo_id, cv.aprobado_por,
                            cv.aprobado_en), E'\n' ORDER BY cv.codigo) AS texto
FROM abet.catalogo_version cv JOIN versiones USING (catalogo_version_id)
UNION ALL
SELECT 2, 'SO y PI', count(*), string_agg(concat_ws('|', p.catalogo_version_id, s.numero, s.descripcion, p.codigo,
                                                    p.descripcion), E'\n' ORDER BY p.catalogo_version_id, p.codigo)
FROM abet.pi p JOIN abet.so s ON s.so_id = p.so_id JOIN versiones v ON v.catalogo_version_id = p.catalogo_version_id
UNION ALL
SELECT 3, 'rúbricas', count(*), string_agg(concat_ws('|', p.codigo, r.nivel, r.descriptor), E'\n'
                                           ORDER BY p.catalogo_version_id, p.codigo, r.nivel)
FROM abet.rubrica_nivel r JOIN abet.pi p ON p.pi_id = r.pi_id JOIN versiones v ON v.catalogo_version_id = p.catalogo_version_id
UNION ALL
SELECT 4, 'plan de estudios', count(*), string_agg(concat_ws('|', pe.catalogo_version_id, a.codigo, a.nombre,
                                                             pe.ciclo_malla), E'\n' ORDER BY pe.catalogo_version_id, a.codigo)
FROM abet.plan_estudios pe JOIN abet.asignatura a USING (asignatura_id)
JOIN versiones v ON v.catalogo_version_id = pe.catalogo_version_id
UNION ALL
SELECT 5, 'asignatura y SO', count(*), string_agg(concat_ws('|', x.catalogo_version_id, a.codigo, s.numero, i.nombre),
                                                  E'\n' ORDER BY x.catalogo_version_id, a.codigo, s.numero)
FROM abet.asignatura_so x JOIN abet.asignatura a ON a.asignatura_id = x.asignatura_id JOIN abet.so s ON s.so_id = x.so_id
LEFT JOIN abet.instrumento i ON i.instrumento_id = x.instrumento_id
JOIN versiones v ON v.catalogo_version_id = x.catalogo_version_id
UNION ALL
SELECT 6, 'competencias', count(*), string_agg(concat_ws('|', k.catalogo_version_id, k.codigo, k.nombre, k.tipo,
                                                         (SELECT string_agg(s.numero::text, ',' ORDER BY s.numero)
                                                            FROM abet.competencia_so x JOIN abet.so s ON s.so_id = x.so_id
                                                           WHERE x.competencia_id = k.competencia_id),
                                                         (SELECT string_agg(a.codigo || '=' || ac.estadio, ','
                                                                            ORDER BY a.codigo)
                                                            FROM abet.asignatura_competencia ac
                                                            JOIN abet.asignatura a ON a.asignatura_id = ac.asignatura_id
                                                           WHERE ac.competencia_id = k.competencia_id)),
                                               E'\n' ORDER BY k.catalogo_version_id, k.codigo)
FROM abet.competencia k JOIN versiones v ON v.catalogo_version_id = k.catalogo_version_id
UNION ALL
SELECT 7, 'vigencias', count(*), string_agg(concat_ws('|', pe.codigo, v.catalogo_version_id), E'\n' ORDER BY pe.codigo)
FROM abet.catalogo_vigencia v JOIN amb USING (carrera_id) JOIN abet.periodo pe ON pe.periodo_id = v.periodo_id
UNION ALL
SELECT 8, 'plan de medición', count(*), string_agg(concat_ws('|', pe.codigo, a.codigo, p.codigo, i.nombre,
                                                             pm.descripcion_instrumento), E'\n'
                                                   ORDER BY pe.codigo, a.codigo, p.codigo)
FROM abet.plan_medicion pm JOIN amb USING (carrera_id) JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id
JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id JOIN abet.pi p ON p.pi_id = pm.pi_id
LEFT JOIN abet.instrumento i ON i.instrumento_id = pm.instrumento_id
UNION ALL
SELECT 9, 'reglas', count(*), string_agg(concat_ws('|', cr.version, cr.estado, cr.aprobado_por, cr.aprobado_en, pv.clave,
                                                   pv.estado, pv.valor_numero, pv.valor_texto,
                                                   (SELECT string_agg(cn.nivel_original || '=' || cn.valor_0_1, ','
                                                                      ORDER BY cn.nivel_original)
                                                      FROM abet.conversion_nivel_0_1 cn
                                                     WHERE cn.conjunto_reglas_id = cr.conjunto_reglas_id)),
                                         E'\n' ORDER BY cr.version, pv.clave)
FROM abet.conjunto_reglas cr JOIN amb USING (carrera_id)
LEFT JOIN abet.parametro_valor pv ON pv.conjunto_reglas_id = cr.conjunto_reglas_id
UNION ALL
SELECT 10, 'secciones', count(*), string_agg(concat_ws('|', s.clave, s.curso_blackboard,
                                                       (SELECT string_agg(d.usuario_id::text, ',' ORDER BY d.usuario_id)
                                                          FROM acceso.docente_seccion d WHERE d.seccion_id = s.seccion_id)),
                                             E'\n' ORDER BY s.clave)
FROM secciones s
UNION ALL
SELECT 11, 'cargas', count(*), string_agg(concat_ws('|', c.carga_id, s.clave, c.estado, c.filas_de_datos, c.filas_leidas,
                                                    c.filas_aceptadas, c.filas_rechazadas, cr.version, c.subida_por,
                                                    c.reemplaza_carga_id, ao.sha256), E'\n' ORDER BY c.carga_id)
FROM cargas c JOIN abet.seccion x ON x.seccion_id = c.seccion_id
JOIN abet.periodo pe ON pe.periodo_id = x.periodo_id JOIN abet.asignatura a ON a.asignatura_id = x.asignatura_id
CROSS JOIN LATERAL (SELECT pe.codigo || '/' || a.codigo || '/' || x.numero AS clave) AS s
JOIN abet.conjunto_reglas cr ON cr.conjunto_reglas_id = c.conjunto_reglas_id
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
UNION ALL
SELECT 12, 'mediciones', count(*), string_agg(concat_ws('|', m.carga_id, p.codigo, e.codigo, m.estado_evidencia,
                                                        m.nivel_original, m.fila_origen), E'\n'
                                              ORDER BY m.carga_id, p.codigo, m.fila_origen)
FROM abet.medicion m JOIN cargas c ON c.carga_id = m.carga_id JOIN abet.pi p ON p.pi_id = m.pi_id
JOIN abet.estudiante e ON e.estudiante_id = m.estudiante_id
UNION ALL
SELECT 13, 'rechazos', count(*), string_agg(concat_ws('|', r.carga_id, r.fila_origen, r.motivo, r.efecto, r.pi_id),
                                            E'\n' ORDER BY r.carga_id, r.fila_origen, r.motivo)
FROM abet.rechazo_fila r JOIN cargas c ON c.carga_id = r.carga_id
)
SELECT parte, filas, huella FROM (
    SELECT orden, parte, filas, left(encode(sha256(convert_to(coalesce(texto, ''), 'UTF8')), 'hex'), 16) AS huella
    FROM partes
    UNION ALL
    SELECT 99, 'HUELLA DE AMBIENTAL', sum(filas),
           encode(sha256(convert_to(string_agg(parte || E'\n' || coalesce(texto, ''), E'\n' ORDER BY orden), 'UTF8')), 'hex')
    FROM partes
) AS t
ORDER BY orden;
