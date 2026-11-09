-- Revisión previa a V1_10 en la base de Neon (spec 003, US-26 y J-19). V1_10 reemplaza ck_carga_columna_encabezado
-- por la regla del encabezado con prefijo («ABET» opcional, «SO» o «PI» opcional, el código del PI y «[»). Esa
-- regla acepta todo lo que aceptaba la de V1_07, así que las filas que ya existen deben cumplirla. Este script lo
-- comprueba ANTES de migrar: cuenta las filas de abet.carga_columna que no cumplirían la restricción nueva, que
-- deben ser 0, y muestra la versión actual de flyway_schema_history (debe ser 1.09 antes de V1_10).
-- Se corre con el usuario dueño de la base o con abet_respaldo, y la conexión directa, en cada rama de Neon.
--
--   psql "host=$NEON_HOST dbname=$NEON_DB user=abet_respaldo sslmode=verify-full sslrootcert=system" \
--        -f db/plataforma/neon/revisar_antes_de_v1_10.sql
--
-- No escribe. La sesión pasa a solo lectura antes de la primera consulta, así que no cambia nada aunque la corra el
-- dueño. Si alguna fila no cumpliría la restricción nueva, termina con error para que la terminal o la integración
-- continua (continuous integration, CI) lo noten, y V1_10 no debe aplicarse hasta revisarla. Las filas que muestra
-- son identificadores internos y el PI, nunca el encabezado completo, que trae el código de una columna de
-- Blackboard.

\set ON_ERROR_STOP 1
SET default_transaction_read_only = on;
SHOW default_transaction_read_only;

\echo 'Versión actual de flyway_schema_history (la última migración versionada aplicada).'
SELECT version, description, success
FROM abet.flyway_schema_history
WHERE version IS NOT NULL
ORDER BY installed_rank DESC
LIMIT 1;

\echo 'Filas de abet.carga_columna que no cumplirían ck_carga_columna_encabezado de V1_10 (deben ser 0).'
SELECT count(*) AS filas_que_no_cumplen
FROM abet.carga_columna
WHERE NOT (encabezado ~ ('^([Aa][Bb][Ee][Tt] {0,3})?(([Ss][Oo]|[Pp][Ii]) {0,3})?' || replace(pi_codigo, '.', '\.') || ' {0,3}\['));

\echo 'Detalle de esas filas, si las hay (identificador de la columna y PI).'
SELECT carga_columna_id, carga_id, pi_codigo
FROM abet.carga_columna
WHERE NOT (encabezado ~ ('^([Aa][Bb][Ee][Tt] {0,3})?(([Ss][Oo]|[Pp][Ii]) {0,3})?' || replace(pi_codigo, '.', '\.') || ' {0,3}\['))
ORDER BY carga_columna_id;

SELECT count(*) > 0 AS hay_filas_que_no_cumplen
FROM abet.carga_columna
WHERE NOT (encabezado ~ ('^([Aa][Bb][Ee][Tt] {0,3})?(([Ss][Oo]|[Pp][Ii]) {0,3})?' || replace(pi_codigo, '.', '\.') || ' {0,3}\[')) \gset
\if :hay_filas_que_no_cumplen
    \echo 'FALLA: hay filas que no cumplirían ck_carga_columna_encabezado de V1_10. No migres.'
    \quit 3
\else
    \echo 'ok: 0 filas no cumplirían ck_carga_columna_encabezado de V1_10.'
\endif
