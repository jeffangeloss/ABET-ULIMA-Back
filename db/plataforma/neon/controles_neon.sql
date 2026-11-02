-- Consultas de control Q01 a Q14 para la base de Neon (US-01, FR-001, SC-002 y T027). Son copia literal de las de
-- db/pruebas/pruebas.sql, escritas como consultas sueltas, y db/pruebas/correr_pruebas.sh comprueba que no se
-- aparten de ellas. Cada consulta debe devolver 0 filas.
-- Se corre con el usuario abet_respaldo, de solo lectura, y la conexión directa, en cada rama de Neon.
--
--   psql "host=$NEON_HOST dbname=$NEON_DB user=abet_respaldo sslmode=verify-full sslrootcert=system" \
--        -f db/plataforma/neon/controles_neon.sql
--
-- La sesión pasa a solo lectura antes de la primera consulta, así que el script no escribe aunque lo corra el dueño
-- de la base. Al final informa si las catorce consultas devuelven 0 filas; si alguna devuelve filas, termina con
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

SELECT (:q01 + :q02 + :q03 + :q04 + :q05 + :q06 + :q07 + :q08 + :q09 + :q10 + :q11 + :q12 + :q13 + :q14) = 0
       AS controles_en_cero \gset
\if :controles_en_cero
    \echo 'RESULTADO: Q01 a Q14 devuelven 0 filas.'
\else
    \echo 'RESULTADO: al menos una consulta de control devuelve filas, con el detalle en su bloque de arriba.'
    DO $$ BEGIN RAISE EXCEPTION 'Consultas de control con filas'; END $$;
\endif
