-- PI del plan de medición de un periodo sin descripción del instrumento (spec 005, US-51, BR-R17-11 y AD-29).
-- Consulta informativa de solo lectura, que no es un control de db/pruebas/pruebas.sql, porque un PI sin
-- descripción es válido mientras la Coordinación no la fija (D-34) y su R-17 sale con G17:I19 vacía. Lista la
-- asignatura, el PI y el nombre del instrumento de cada fila de abet.plan_medicion del periodo con
-- descripcion_instrumento nula, ordenadas por asignatura y PI, y al final cuántas son. Sirve para saber qué falta
-- antes y después de correr db/datos/descripcion_instrumento_2026_2.sql en cada rama de Neon.
-- Se corre con abet_respaldo o con el usuario dueño de la base, desde el Windows de Jefferson.
--
--   psql "host=$NEON_HOST dbname=$NEON_DB user=abet_respaldo sslmode=verify-full sslrootcert=system" \
--        -X -v ON_ERROR_STOP=1 -v periodo=2026-2 -f db/plataforma/neon/pi_sin_descripcion_instrumento.sql
--
-- No escribe. La sesión pasa a solo lectura antes de la primera consulta, así que no cambia nada aunque la corra el
-- dueño. Sin la variable periodo, el script se detiene antes de consultar.

\set ON_ERROR_STOP 1
\if :{?periodo}
\else
    \echo 'Falta el periodo, por ejemplo -v periodo=2026-2.'
    SELECT CAST('falta el periodo' AS integer);
\endif
SET default_transaction_read_only = on;
SHOW default_transaction_read_only;

\echo 'PI del plan del periodo sin descripción del instrumento (asignatura, PI e instrumento).'
SELECT a.codigo AS asignatura, p.codigo AS pi, coalesce(i.nombre, '-') AS instrumento
FROM abet.plan_medicion pm
JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id
JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id
JOIN abet.pi p ON p.pi_id = pm.pi_id
LEFT JOIN abet.instrumento i ON i.instrumento_id = pm.instrumento_id
WHERE pe.codigo = :'periodo' AND pm.descripcion_instrumento IS NULL
ORDER BY a.codigo, p.so_numero, p.numero;

\echo 'Cantidad de PI del plan del periodo sin descripción.'
SELECT count(*) AS pi_sin_descripcion
FROM abet.plan_medicion pm
JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id
WHERE pe.codigo = :'periodo' AND pm.descripcion_instrumento IS NULL;
