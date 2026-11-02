-- Guardia de datos inventados en la base de Neon (script de plataforma; US-08, FR-005, SC-007 y Principio II).
-- Agrega a abet.estudiante la restricción ck_estudiante_codigo_inventado, que junto con ck_estudiante_codigo de
-- V1_08 solo admite códigos de 99000000 a 99999999. Repite en la base la regla que la interfaz de
-- programación de aplicaciones (application programming interface, API) aplica con GUARDIA_DATOS_INVENTADOS=1,
-- para que un código real no entre aunque el programa falle.
-- Vive fuera de db/migration porque vale solo en Neon y solo mientras la universidad no autorice los datos reales
-- (D-10). Las bases de db/pruebas/pruebas.sql y abet_sis_med_dev no la llevan, así que CODIGO_INVALIDO sigue al
-- alcance de las pruebas con la guardia apagada. Se corre con el usuario dueño y la conexión directa, después de
-- V1_09, y se puede repetir.
-- Cuando la guardia rechaza una fila, PostgreSQL repite esa fila, con el código del estudiante, en el DETAIL del
-- error 23514. Por eso la API registra y responde de ese error solo el SQLSTATE y el nombre de la restricción,
-- nunca su DETAIL (FR-018 y SC-006).
--
--   psql "host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=verify-full sslrootcert=system" \
--        -v ON_ERROR_STOP=1 -f db/plataforma/neon/guardia_datos_inventados.sql
--
-- Cómo se retira. Solo con la autorización de la universidad y en una solicitud de integración (pull request, PR)
-- revisada, que también apaga GUARDIA_DATOS_INVENTADOS en Vercel, el dueño de la base corre en cada rama de Neon
-- la sentencia de abajo. db/pruebas/probar_guardia.sql la ensaya en una base desechable.
--
--   ALTER TABLE abet.estudiante DROP CONSTRAINT ck_estudiante_codigo_inventado;

\set ON_ERROR_STOP 1

BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conrelid = 'abet.estudiante'::regclass AND conname = 'ck_estudiante_codigo_inventado') THEN
        -- La restricción revisa también las filas que ya existen; un código que no empieza con 99 detiene el script.
        ALTER TABLE abet.estudiante ADD CONSTRAINT ck_estudiante_codigo_inventado CHECK (codigo LIKE '99%');
        RAISE NOTICE 'Guardia ck_estudiante_codigo_inventado agregada a abet.estudiante';
    ELSE
        RAISE NOTICE 'La guardia ck_estudiante_codigo_inventado ya estaba en abet.estudiante';
    END IF;
END
$$;

COMMENT ON CONSTRAINT ck_estudiante_codigo_inventado ON abet.estudiante IS 'Guardia de datos inventados, solo en Neon (US-08). Con ck_estudiante_codigo admite solo 99000000 a 99999999; se retira con la autorización de la universidad (D-10) en un PR revisado.';

-- Comprobación final. La guardia existe, ya cubre las filas existentes y tiene exactamente esta regla.
DO $$
DECLARE
    v_definicion text;
BEGIN
    SELECT pg_get_constraintdef(oid) INTO v_definicion
    FROM pg_constraint
    WHERE conrelid = 'abet.estudiante'::regclass AND conname = 'ck_estudiante_codigo_inventado' AND convalidated;
    IF v_definicion IS DISTINCT FROM 'CHECK (((codigo)::text ~~ ''99%''::text))' THEN
        RAISE EXCEPTION 'La guardia de abet.estudiante no es CHECK (codigo LIKE ''99%%'') validada (%)',
            coalesce(v_definicion, 'ausente');
    END IF;
    RAISE NOTICE 'Guardia de datos inventados activa en abet.estudiante';
END
$$;

COMMIT;
