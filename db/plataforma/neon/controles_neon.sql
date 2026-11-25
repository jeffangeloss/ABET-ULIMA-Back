-- Consultas de control Q01 a Q14, Q16 y Q17 desde la spec 005 y Q18 a Q21 desde la spec 008 para la base de Neon
-- (US-01, FR-001, SC-002, T027, FR-018 de la spec 005 y FR-021 de la spec 008). Son copia literal de las de db/pruebas/pruebas.sql, escritas como consultas sueltas, y
-- db/pruebas/correr_pruebas.sh comprueba que no se aparten de ellas. Cada consulta debe devolver 0 filas.
-- Se corre con el usuario abet_respaldo, de solo lectura, y la conexión directa, en cada rama de Neon.
--
--   psql "host=$NEON_HOST dbname=$NEON_DB user=abet_respaldo sslmode=verify-full sslrootcert=system" \
--        -f db/plataforma/neon/controles_neon.sql
--
-- La sesión pasa a solo lectura antes de la primera consulta, así que el script no escribe aunque lo corra el dueño
-- de la base. Q16 y Q17 leen las tablas de V1_15 y corren solo si la base ya las tiene, así que el archivo sigue
-- sirviendo en una rama anterior a V1_15. Al final informa si las veinte consultas devuelven 0 filas; si alguna devuelve filas, termina con
-- error para que la terminal o la integración continua (continuous integration, CI) lo noten. Las filas que muestra
-- una consulta con falla son identificadores internos y nombres de columnas, nunca códigos ni nombres de estudiantes.

\set ON_ERROR_STOP 1
SET default_transaction_read_only = on;
SHOW default_transaction_read_only;

\echo 'Q01. Filas leídas distintas de las filas de datos del archivo (C1).'
 SELECT c.carga_id FROM abet.carga c JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
 WHERE c.estado IN ('PUBLICADA', 'REEMPLAZADA') AND c.filas_leidas <> ao.filas_de_datos;
\set q01 :ROW_COUNT

\echo 'Q02. Columna con menos o más mediciones que filas aceptadas (C1; un rechazo descarta la fila completa).'
 SELECT cc.carga_columna_id FROM abet.carga_columna cc JOIN abet.carga c ON c.carga_id = cc.carga_id
 LEFT JOIN abet.medicion m ON m.carga_columna_id = cc.carga_columna_id
 WHERE c.estado IN ('PUBLICADA', 'REEMPLAZADA')
 GROUP BY cc.carga_columna_id, c.filas_aceptadas HAVING count(m.medicion_id) <> c.filas_aceptadas;
\set q02 :ROW_COUNT

\echo 'Q03. Filas rechazadas sin su registro de rechazo.'
 SELECT c.carga_id FROM abet.carga c
 LEFT JOIN abet.rechazo_fila r ON r.carga_id = c.carga_id AND r.efecto = 'RECHAZA_FILA'
 GROUP BY c.carga_id, c.filas_rechazadas HAVING count(DISTINCT r.fila_origen) <> c.filas_rechazadas;
\set q03 :ROW_COUNT

\echo 'Q04. Columnas con nombres de personas o datos de contacto (privacidad).'
 SELECT table_name, column_name FROM information_schema.columns
 WHERE table_schema = 'abet'
   AND (column_name ~ '(apellido|first_name|last_name|correo|email|telefono|dni)'
        OR (table_name IN ('estudiante', 'medicion', 'carga', 'rechazo_fila', 'carga_columna') AND column_name LIKE '%nombre%'));
\set q04 :ROW_COUNT

\echo 'Q05. Asignatura con planes de dos versiones de catálogo de la misma carrera en el mismo periodo (H26).'
 SELECT pm.periodo_id, pm.asignatura_id, pm.carrera_id FROM abet.plan_medicion pm
 GROUP BY pm.periodo_id, pm.asignatura_id, pm.carrera_id HAVING count(DISTINCT pm.catalogo_version_id) > 1;
\set q05 :ROW_COUNT

\echo 'Q06. Carga PUBLICADA o REEMPLAZADA sin columnas reconocidas.'
 SELECT c.carga_id FROM abet.carga c
 WHERE c.estado IN ('PUBLICADA', 'REEMPLAZADA')
   AND NOT EXISTS (SELECT 1 FROM abet.carga_columna cc WHERE cc.carga_id = c.carga_id);
\set q06 :ROW_COUNT

\echo 'Q07. Carga publicada que dice reemplazar a otra que no está REEMPLAZADA (H57).'
 SELECT c.carga_id FROM abet.carga c JOIN abet.carga ant ON ant.carga_id = c.reemplaza_carga_id
 WHERE c.estado IN ('PUBLICADA', 'REEMPLAZADA') AND ant.estado <> 'REEMPLAZADA';
\set q07 :ROW_COUNT

\echo 'Q08. Estudiante y PI en cargas publicadas de dos secciones del mismo curso y periodo.'
 SELECT m.estudiante_id, m.pi_id, s.periodo_id, s.asignatura_id
 FROM abet.medicion m JOIN abet.carga c ON c.carga_id = m.carga_id JOIN abet.seccion s ON s.seccion_id = c.seccion_id
 WHERE c.estado = 'PUBLICADA'
 GROUP BY m.estudiante_id, m.pi_id, s.periodo_id, s.asignatura_id HAVING count(DISTINCT s.seccion_id) > 1;
\set q08 :ROW_COUNT

\echo 'Q09. Parámetro CONVERSION_NIVEL_0_1 DEFINIDO sin sus 4 niveles.'
 SELECT pv.conjunto_reglas_id FROM abet.parametro_valor pv
 LEFT JOIN abet.conversion_nivel_0_1 cn ON cn.conjunto_reglas_id = pv.conjunto_reglas_id
 WHERE pv.clave = 'CONVERSION_NIVEL_0_1' AND pv.estado = 'DEFINIDO'
 GROUP BY pv.conjunto_reglas_id HAVING count(cn.nivel_original) <> 4;
\set q09 :ROW_COUNT

\echo 'Q10. Cargas publicadas del mismo curso, periodo y carrera con conjuntos de reglas distintos.'
 SELECT s.periodo_id, s.asignatura_id, c.carrera_id
 FROM abet.carga c JOIN abet.seccion s ON s.seccion_id = c.seccion_id
 WHERE c.estado = 'PUBLICADA'
 GROUP BY s.periodo_id, s.asignatura_id, c.carrera_id HAVING count(DISTINCT c.conjunto_reglas_id) > 1;
\set q10 :ROW_COUNT

\echo 'Q11. Conjunto de reglas APROBADO con algún parámetro sin DEFINIR.'
 SELECT cr.conjunto_reglas_id, p.clave
 FROM abet.conjunto_reglas cr CROSS JOIN abet.parametro p
 LEFT JOIN abet.parametro_valor pv ON pv.conjunto_reglas_id = cr.conjunto_reglas_id AND pv.clave = p.clave
 WHERE cr.estado = 'APROBADO' AND pv.estado IS DISTINCT FROM 'DEFINIDO';
\set q11 :ROW_COUNT

\echo 'Q12. Fila aceptada fuera del rango de filas de datos del archivo.'
 SELECT f.carga_id, f.fila_origen FROM abet.carga_fila f JOIN abet.carga c ON c.carga_id = f.carga_id
 WHERE f.fila_origen > c.filas_de_datos + 1;
\set q12 :ROW_COUNT

\echo 'Q13. Carga PUBLICADA o REEMPLAZADA con filas aceptadas distintas de sus filas registradas.'
 SELECT c.carga_id FROM abet.carga c LEFT JOIN abet.carga_fila f ON f.carga_id = c.carga_id
 WHERE c.estado IN ('PUBLICADA', 'REEMPLAZADA')
 GROUP BY c.carga_id, c.filas_aceptadas HAVING count(f.fila_origen) <> c.filas_aceptadas;
\set q13 :ROW_COUNT

\echo 'Q14. Carga REEMPLAZADA sin ninguna carga que la reemplace (H57).'
 SELECT a.carga_id FROM abet.carga a
 WHERE a.estado = 'REEMPLAZADA' AND NOT EXISTS (SELECT 1 FROM abet.carga n WHERE n.reemplaza_carga_id = a.carga_id);
\set q14 :ROW_COUNT

SELECT to_regclass('abet.mejora_borrador') IS NOT NULL AS con_v1_15 \gset
\if :con_v1_15
\echo 'Q16. Causa o acción del análisis por indicador con un código de 8 dígitos o un correo (spec 005).'
 SELECT 'mejora_borrador_pi' AS tabla, b.carga_id, b.pi_id FROM abet.mejora_borrador_pi b
 WHERE b.causa ~ '(^|[^0-9])[0-9]{8}([^0-9]|$)|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+'
    OR b.accion ~ '(^|[^0-9])[0-9]{8}([^0-9]|$)|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+'
 UNION ALL
 SELECT 'mejora_declaracion_pi', d.declaracion_id, d.pi_id FROM abet.mejora_declaracion_pi d
 WHERE d.causa ~ '(^|[^0-9])[0-9]{8}([^0-9]|$)|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+'
    OR d.accion ~ '(^|[^0-9])[0-9]{8}([^0-9]|$)|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+';
\set q16 :ROW_COUNT

\echo 'Q17. Declaración vigente de una carga PUBLICADA sin la fila de un PI con calificados (spec 005).'
 SELECT d.carga_id, p.codigo AS pi FROM abet.mejora_declaracion d
 JOIN abet.carga c ON c.carga_id = d.carga_id AND c.estado = 'PUBLICADA'
 JOIN abet.carga_columna cc ON cc.carga_id = d.carga_id JOIN abet.pi p ON p.pi_id = cc.pi_id
 WHERE d.declaracion_id = (SELECT max(v.declaracion_id) FROM abet.mejora_declaracion v WHERE v.carga_id = d.carga_id)
   AND EXISTS (SELECT 1 FROM abet.medicion m WHERE m.carga_columna_id = cc.carga_columna_id AND m.estado_evidencia = 'CALIFICADO')
   AND NOT EXISTS (SELECT 1 FROM abet.mejora_declaracion_pi dp WHERE dp.declaracion_id = d.declaracion_id AND dp.pi_id = cc.pi_id);
\set q17 :ROW_COUNT
\else
\echo 'Q16 y Q17 esperan a V1_15 (spec 005), que esta base todavía no tiene.'
\set q16 0
\set q17 0
\endif

\echo 'Q18. Curso con plan de medición de dos carreras en el mismo periodo (spec 008).'
 SELECT a.codigo AS asignatura, pe.codigo AS periodo FROM abet.plan_medicion pm
 JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id
 GROUP BY a.codigo, pe.codigo HAVING count(DISTINCT pm.carrera_id) > 1;
\set q18 :ROW_COUNT

\echo 'Q19. Carrera con plan de medición sin conjunto de reglas (spec 008).'
 SELECT DISTINCT c.codigo AS carrera, pe.codigo AS periodo FROM abet.plan_medicion pm
 JOIN abet.carrera c ON c.carrera_id = pm.carrera_id JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id
 WHERE NOT EXISTS (SELECT 1 FROM abet.conjunto_reglas cr WHERE cr.carrera_id = pm.carrera_id);
\set q19 :ROW_COUNT

\echo 'Q20. Cuenta COORDINADOR activa sin alcance o con secciones propias en acceso.docente_seccion (spec 008).'
 SELECT u.usuario_id, u.rol FROM acceso.usuario_autorizado u
 WHERE u.rol = 'COORDINADOR' AND u.activo
   AND (NOT EXISTS (SELECT 1 FROM acceso.coordinacion_alcance ca WHERE ca.usuario_id = u.usuario_id)
        OR EXISTS (SELECT 1 FROM acceso.docente_seccion d WHERE d.usuario_id = u.usuario_id));
\set q20 :ROW_COUNT

\echo 'Q21. Sección cuyo curso de Blackboard no declara su periodo, su asignatura y su número (spec 008).'
 SELECT s.seccion_id, s.numero, a.codigo AS asignatura, pe.codigo AS periodo FROM abet.seccion s
 JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id
 WHERE s.curso_blackboard IS NOT NULL
   AND s.curso_blackboard !~ ('(^|_)' || pe.anio || pe.ciclo || '_' || a.codigo || '_' || s.numero || '$');
\set q21 :ROW_COUNT

SELECT (:q01 + :q02 + :q03 + :q04 + :q05 + :q06 + :q07 + :q08 + :q09 + :q10 + :q11 + :q12 + :q13 + :q14 + :q16 + :q17 + :q18 + :q19 + :q20 + :q21) = 0
       AS controles_en_cero \gset
\if :controles_en_cero
    \if :con_v1_15
        \echo 'RESULTADO: Q01 a Q14 y Q16 a Q21 devuelven 0 filas.'
    \else
        \echo 'RESULTADO: Q01 a Q14 y Q18 a Q21 devuelven 0 filas.'
    \endif
\else
    \echo 'RESULTADO: al menos una consulta de control devuelve filas, con el detalle en su bloque de arriba.'
    DO $$ BEGIN RAISE EXCEPTION 'Consultas de control con filas'; END $$;
\endif
