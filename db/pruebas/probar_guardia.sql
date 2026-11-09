-- Pruebas de la guardia de datos inventados (US-08, FR-005 y SC-007) y de los datos de 2026-2 en una base sin cargas
-- (US-03 y US-04). db/pruebas/correr_pruebas.sh las corre en una base desechable aparte, con V1_01 a V1_10, las
-- vistas, crear_rol_app.sql, guardia_datos_inventados.sql y periodo_2026_2_inventado.sql (los dos últimos dos
-- veces), y con -v rol_app=<rol de prueba de nombre único>. La base de pruebas.sql no lleva la guardia, igual que
-- abet_sis_med_dev, porque la guardia vale solo en Neon.
-- Los códigos 10000004 y 98999999 son los valores de prueba de la guardia de la spec; nunca se guardan, porque la
-- base los rechaza dentro de una transacción que se deshace. Los mensajes de esta prueba no los repiten.
\set ON_ERROR_STOP 1
SET client_min_messages = notice;
\if :{?rol_app}
\else
    \echo 'Falta -v rol_app=<rol de prueba>.'
    DO $$ BEGIN RAISE EXCEPTION 'probar_guardia.sql necesita la variable rol_app'; END $$;
\endif
SET prueba.rol_app = :'rol_app';

-- G01. Los datos de 2026-2 quedan sin duplicar después de dos corridas y sin estudiantes, cargas ni mediciones.
DO $$
BEGIN
    IF (SELECT count(*) FROM abet.catalogo_vigencia) <> 1
       OR (SELECT string_agg(s.numero || '=' || s.curso_blackboard, ',' ORDER BY s.numero) FROM abet.seccion s)
          IS DISTINCT FROM '410=SINTETICO_20262_450002_410,411=SINTETICO_20262_450002_411'
       OR (SELECT string_agg(p.codigo, ',' ORDER BY p.codigo) FROM abet.plan_medicion pm JOIN abet.pi p ON p.pi_id = pm.pi_id)
          IS DISTINCT FROM '5.1,5.2,5.3'
       OR (SELECT count(DISTINCT so_id) FROM abet.plan_medicion) <> 1 THEN
        RAISE EXCEPTION 'FALLA G01: la vigencia, las secciones 410 y 411 y el plan de 450002 deben estar una sola vez';
    END IF;
    IF (SELECT count(*) FROM acceso.usuario_autorizado WHERE activo) <> 3
       OR (SELECT count(*) FROM acceso.docente_seccion) <> 2 OR (SELECT count(*) FROM acceso.credencial) <> 0 THEN
        RAISE EXCEPTION 'FALLA G01: deben quedar 3 usuarios activos, 2 asignaciones y ninguna credencial';
    END IF;
    IF (SELECT count(*) FROM abet.estudiante) + (SELECT count(*) FROM abet.carga)
       + (SELECT count(*) FROM abet.medicion) <> 0 THEN
        RAISE EXCEPTION 'FALLA G01: el script de datos no debe crear estudiantes, cargas ni mediciones';
    END IF;
    RAISE NOTICE 'ok G01 datos de 2026-2 sin duplicar tras dos corridas y sin estudiantes, cargas ni mediciones';
END $$;

-- G02. La guardia existe, está validada, tiene su regla y su comentario, y la segunda corrida no la duplica.
DO $$
BEGIN
    IF (SELECT count(*) FROM pg_constraint
         WHERE conrelid = 'abet.estudiante'::regclass AND conname = 'ck_estudiante_codigo_inventado'
           AND convalidated AND pg_get_constraintdef(oid) = 'CHECK (((codigo)::text ~~ ''99%''::text))'
           AND obj_description(oid, 'pg_constraint') LIKE 'Guardia de datos inventados%') <> 1 THEN
        RAISE EXCEPTION 'FALLA G02: falta la guardia ck_estudiante_codigo_inventado validada y comentada';
    END IF;
    RAISE NOTICE 'ok G02 ck_estudiante_codigo_inventado validada, con CHECK (codigo LIKE ''99%%'') y comentario';
END $$;

-- G03. Con el rol de la aplicación, 99000001 entra, los dos códigos que no empiezan con 99 se rechazan por la
-- guardia y un código de 7 dígitos sigue rechazado por ck_estudiante_codigo.
BEGIN;
SET LOCAL ROLE :"rol_app";
DO $$
DECLARE
    c             record;
    v_estado      text;
    v_restriccion text;
BEGIN
    FOR c IN SELECT * FROM (VALUES
        ('G03a', 'código inventado dentro del rango', '99000001', NULL, NULL),
        ('G03b', 'código de 8 dígitos que empieza con 10', '10000004', '23514', 'ck_estudiante_codigo_inventado'),
        ('G03c', 'código de 8 dígitos que empieza con 98', '98999999', '23514', 'ck_estudiante_codigo_inventado'),
        ('G03d', 'código de 7 dígitos que empieza con 99', '9900001', '23514', 'ck_estudiante_codigo')
    ) AS t (id, descripcion, codigo, sqlstate, restriccion) ORDER BY id LOOP
        v_estado := NULL;
        v_restriccion := NULL;
        BEGIN
            INSERT INTO abet.estudiante (codigo) VALUES (c.codigo);
        EXCEPTION WHEN others THEN
            GET STACKED DIAGNOSTICS v_estado = RETURNED_SQLSTATE, v_restriccion = CONSTRAINT_NAME;
        END;
        IF v_estado IS DISTINCT FROM c.sqlstate OR v_restriccion IS DISTINCT FROM c.restriccion THEN
            RAISE EXCEPTION 'FALLA %: % terminó con % (%) y se esperaba % (%)', c.id, c.descripcion,
                coalesce(v_estado, 'aceptado'), v_restriccion, coalesce(c.sqlstate, 'aceptado'), c.restriccion;
        END IF;
        RAISE NOTICE 'ok % %: %', c.id, c.descripcion, coalesce('rechazado por ' || c.restriccion, 'entra');
    END LOOP;
    IF (SELECT string_agg(codigo, ',') FROM abet.estudiante) IS DISTINCT FROM '99000001' THEN
        RAISE EXCEPTION 'FALLA G03: abet.estudiante debe tener solo el código inventado';
    END IF;
END $$;
ROLLBACK;

-- G04. El rol de la aplicación no puede retirar la guardia, porque no es dueño de abet.estudiante.
BEGIN;
SET LOCAL ROLE :"rol_app";
DO $$
DECLARE
    v_estado text;
BEGIN
    BEGIN
        ALTER TABLE abet.estudiante DROP CONSTRAINT ck_estudiante_codigo_inventado;
    EXCEPTION WHEN others THEN
        GET STACKED DIAGNOSTICS v_estado = RETURNED_SQLSTATE;
    END;
    IF v_estado IS DISTINCT FROM '42501' THEN
        RAISE EXCEPTION 'FALLA G04: el rol de la aplicación pudo retirar la guardia o falló por otra causa (%)', v_estado;
    END IF;
    RAISE NOTICE 'ok G04 el rol de la aplicación no puede retirar la guardia (42501)';
END $$;
ROLLBACK;

-- G05. La sentencia de retiro escrita en guardia_datos_inventados.sql quita la guardia, en una transacción que se
-- deshace, y la guardia sigue en la base después.
BEGIN;
ALTER TABLE abet.estudiante DROP CONSTRAINT ck_estudiante_codigo_inventado;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_constraint
                WHERE conrelid = 'abet.estudiante'::regclass AND conname = 'ck_estudiante_codigo_inventado') THEN
        RAISE EXCEPTION 'FALLA G05: la sentencia de retiro no quitó la guardia';
    END IF;
END $$;
ROLLBACK;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                    WHERE conrelid = 'abet.estudiante'::regclass AND conname = 'ck_estudiante_codigo_inventado') THEN
        RAISE EXCEPTION 'FALLA G05: la guardia debe seguir después de deshacer el retiro';
    END IF;
    RAISE NOTICE 'ok G05 la sentencia de retiro quita la guardia y, deshecha, la guardia sigue';
END $$;

\echo 'GUARDIA DE DATOS INVENTADOS: TODAS LAS PRUEBAS PASARON'
