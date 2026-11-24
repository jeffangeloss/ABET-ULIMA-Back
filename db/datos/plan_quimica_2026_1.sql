-- Vigencia de IND-2026 en 2026-1 y plan de medición de Química General (5643) en 2026-1 (script de datos, no
-- migración; spec 008, US-69, FR-006, BR-PERIODO-03 y D-48). Registra la vigencia de IND-2026 para la carrera IND en
-- 2026-1 y la fila del plan de 5643 con el PI de -v pi (6.1 por omisión, el de los R-17 de los profesores, valor
-- provisional de D-48), el instrumento del par 5643 y SO 6 de IND-2026 («Portafolio 3») y la descripción del
-- instrumento de la variable de entorno DESCRIPCION_INSTRUMENTO, que llega por \getenv y nunca queda escrita en el
-- repositorio, en un argumento ni en la salida.
-- Corre en seco salvo con -v aplicar=1. En seco hace lo mismo en una transacción que se deshace al final, así el
-- informe dice lo que registraría y una fila que no cabe detiene la corrida igual. Cada INSERT usa ON CONFLICT DO
-- NOTHING, así que repetirlo no duplica ni cambia filas, y el bloque final detiene todo, y lo deshace, si la vigencia
-- de IND en 2026-1 no es IND-2026 o si el plan de 5643 en 2026-1 trae otra fila, otro instrumento u otra descripción.
-- Sin el par 5643 y SO 6 en IND-2026, fk_plan_medicion_asig_so rechaza el plan y la vigencia tampoco queda.
-- Va después de V1_12 y de V1_14 con db/datos/alcance_coordinacion_ambiental.sql, porque la vigencia de IND-2026 en
-- 2026-1 abre las secciones de 5643 a quien tenga alcance de Industrial (orden de FR-020). Se corre con el usuario
-- dueño de la base y la conexión directa. En Neon lo corre Jefferson desde el Windows con en_windows.py, que pasa
-- DESCRIPCION_INSTRUMENTO sin dejarla en archivos, primero en la rama develop, nunca desde la Mac.
--
--   psql "host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=verify-full sslrootcert=system" \
--        -X -v ON_ERROR_STOP=1 -v aplicar=1 -v pi=6.1 -f db/datos/plan_quimica_2026_1.sql

\set ON_ERROR_STOP 1
\set QUIET on
\if :{?aplicar}
\else
    \set aplicar 0
\endif
\if :{?pi}
\else
    \set pi 6.1
\endif
\getenv descripcion DESCRIPCION_INSTRUMENTO
\if :{?descripcion}
\else
    DO $$ BEGIN RAISE EXCEPTION 'Falta la descripción del instrumento, por ejemplo con \getenv DESCRIPCION_INSTRUMENTO.'; END $$;
\endif

BEGIN;

-- Los bloques DO no ven las variables de psql, así que el PI y la descripción pasan por variables de la transacción.
SELECT set_config('abet.plan_pi', :'pi', true), set_config('abet.plan_descripcion', :'descripcion', true) \gset sin_

WITH nuevas AS (
    INSERT INTO abet.catalogo_vigencia (periodo_id, carrera_id, catalogo_version_id)
    SELECT pe.periodo_id, cv.carrera_id, cv.catalogo_version_id
    FROM abet.periodo pe
    JOIN abet.catalogo_version cv ON cv.codigo = 'IND-2026'
    JOIN abet.carrera c ON c.carrera_id = cv.carrera_id AND c.codigo = 'IND'
    WHERE pe.codigo = '2026-1'
    ON CONFLICT DO NOTHING
    RETURNING 1
)
SELECT count(*) AS plan_vigencias FROM nuevas \gset

-- El instrumento sale del par asignatura y SO del catálogo. Sin el par, el LEFT JOIN deja el instrumento nulo y
-- fk_plan_medicion_asig_so rechaza la fila.
WITH nuevas AS (
    INSERT INTO abet.plan_medicion (periodo_id, asignatura_id, carrera_id, catalogo_version_id, so_id, pi_id,
                                    instrumento_id, descripcion_instrumento)
    SELECT pe.periodo_id, a.asignatura_id, cv.carrera_id, cv.catalogo_version_id, p.so_id, p.pi_id,
           aso.instrumento_id, :'descripcion'
    FROM abet.periodo pe
    JOIN abet.catalogo_version cv ON cv.codigo = 'IND-2026'
    JOIN abet.asignatura a ON a.codigo = '5643'
    JOIN abet.pi p ON p.catalogo_version_id = cv.catalogo_version_id AND p.codigo = :'pi'
    LEFT JOIN abet.asignatura_so aso ON aso.catalogo_version_id = cv.catalogo_version_id
                                   AND aso.asignatura_id = a.asignatura_id AND aso.so_id = p.so_id
    WHERE pe.codigo = '2026-1'
    ON CONFLICT DO NOTHING
    RETURNING 1
)
SELECT count(*) AS plan_filas FROM nuevas \gset

-- Comprobación final. Cada dato queda como lo describe la cabecera, aunque ya existiera antes.
DO $$
DECLARE
    v_pi          text := current_setting('abet.plan_pi');
    v_descripcion text := current_setting('abet.plan_descripcion');
    v_texto       text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM abet.pi p JOIN abet.catalogo_version cv ON cv.catalogo_version_id = p.catalogo_version_id
                   WHERE cv.codigo = 'IND-2026' AND p.codigo = v_pi) THEN
        RAISE EXCEPTION 'IND-2026 no tiene el PI %, que pide -v pi.', v_pi;
    END IF;
    SELECT string_agg(cv.codigo, ',') INTO v_texto
    FROM abet.catalogo_vigencia v
    JOIN abet.periodo pe ON pe.periodo_id = v.periodo_id AND pe.codigo = '2026-1'
    JOIN abet.carrera c ON c.carrera_id = v.carrera_id AND c.codigo = 'IND'
    JOIN abet.catalogo_version cv ON cv.catalogo_version_id = v.catalogo_version_id;
    IF v_texto IS DISTINCT FROM 'IND-2026' THEN
        RAISE EXCEPTION 'Industrial no tiene IND-2026 como versión vigente en 2026-1 (%).', coalesce(v_texto, 'ninguna');
    END IF;
    -- Toda fila del plan de 5643 en 2026-1, de cualquier carrera, debe ser la que registra este guion.
    SELECT string_agg(c.codigo || ' ' || p.codigo || ' ' || coalesce(i.nombre, 'sin instrumento') || ' '
                      || CASE WHEN pm.descripcion_instrumento IS NOT DISTINCT FROM v_descripcion
                              THEN 'con la descripción' ELSE 'con otra descripción' END, ', ' ORDER BY p.codigo)
      INTO v_texto
    FROM abet.plan_medicion pm
    JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id AND pe.codigo = '2026-1'
    JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id AND a.codigo = '5643'
    JOIN abet.carrera c ON c.carrera_id = pm.carrera_id
    JOIN abet.pi p ON p.pi_id = pm.pi_id
    LEFT JOIN abet.instrumento i ON i.instrumento_id = pm.instrumento_id;
    IF v_texto IS DISTINCT FROM 'IND ' || v_pi || ' Portafolio 3 con la descripción' THEN
        RAISE EXCEPTION 'La fila de 5643 en 2026-1 del plan de medición no es la que registra el guion (%).',
            coalesce(v_texto, 'ninguna');
    END IF;
END
$$;

SELECT format('%s %s y %s %s de plan de medición.', :plan_vigencias,
              CASE WHEN :plan_vigencias = 1 THEN 'vigencia' ELSE 'vigencias' END, :plan_filas,
              CASE WHEN :plan_filas = 1 THEN 'fila' ELSE 'filas' END) AS plan_resumen \gset
\if :aplicar
    COMMIT;
    \echo 'Plan de Química General en 2026-1 guardado. Registró' :plan_resumen
\else
    ROLLBACK;
    \echo 'Plan de Química General en 2026-1 en seco. Registraría' :plan_resumen 'No se guardó nada, y -v aplicar=1 lo guarda.'
\endif
