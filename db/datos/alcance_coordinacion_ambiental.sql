-- Alcance de carrera AMB para las coordinaciones que ya existen (script de datos, no migración; spec 008, US-70,
-- FR-008, FR-020 y BR-ACCESO-13). Desde V1_14, una cuenta COORDINADOR ve solo lo que le dan sus filas de
-- acceso.coordinacion_alcance, así que este guion corre después de V1_14 y antes del despliegue del Back con el
-- _ALCANCE nuevo y antes de la vigencia de IND-2026 (orden de FR-020). Da la carrera AMB a cada cuenta COORDINADOR
-- activa que todavía no tiene ninguna fila de alcance, que antes de la spec 008 son solo las de Ambiental. Una cuenta
-- con alcance, como la coordinación de un curso, no recibe la carrera.
-- Corre en seco salvo con -v aplicar=1. En seco hace lo mismo en una transacción que se deshace al final, así el
-- informe dice lo que guardaría. El informe da solo conteos, nunca un correo. Se puede repetir, porque una cuenta que
-- ya tiene la fila de AMB no la recibe otra vez, y el bloque final detiene todo si una coordinación activa queda sin
-- alcance. Se corre con el usuario dueño de la base y la conexión directa. En Neon lo corre Jefferson desde el Windows
-- (ssh windows-worker), primero en la rama develop, nunca desde la Mac.
--
--   psql "host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=verify-full sslrootcert=system" \
--        -X -v ON_ERROR_STOP=1 -v aplicar=1 -f db/datos/alcance_coordinacion_ambiental.sql

\set ON_ERROR_STOP 1
\set QUIET on
\if :{?aplicar}
\else
    \set aplicar 0
\endif

BEGIN;

WITH nuevas AS (
    INSERT INTO acceso.coordinacion_alcance (usuario_id, carrera_id)
    SELECT u.usuario_id, c.carrera_id
    FROM acceso.usuario_autorizado u
    JOIN abet.carrera c ON c.codigo = 'AMB'
    WHERE u.rol = 'COORDINADOR' AND u.activo
      AND NOT EXISTS (SELECT 1 FROM acceso.coordinacion_alcance ca WHERE ca.usuario_id = u.usuario_id)
    ON CONFLICT DO NOTHING
    RETURNING 1
)
SELECT count(*) AS alcance_nuevas FROM nuevas \gset

-- Comprobación final. Ninguna coordinación activa queda sin alcance y la carrera AMB existe.
DO $$
DECLARE
    v_sin_alcance integer;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM abet.carrera WHERE codigo = 'AMB') THEN
        RAISE EXCEPTION 'La base no tiene la carrera AMB, que crea V1_03.';
    END IF;
    SELECT count(*) INTO v_sin_alcance
    FROM acceso.usuario_autorizado u
    WHERE u.rol = 'COORDINADOR' AND u.activo
      AND NOT EXISTS (SELECT 1 FROM acceso.coordinacion_alcance ca WHERE ca.usuario_id = u.usuario_id);
    IF v_sin_alcance <> 0 THEN
        RAISE EXCEPTION '% coordinaciones activas siguen sin alcance.', v_sin_alcance;
    END IF;
END
$$;

\if :aplicar
    COMMIT;
    \echo 'Alcance de Ambiental guardado.' :alcance_nuevas 'filas nuevas de alcance de la carrera AMB.'
\else
    ROLLBACK;
    \echo 'Alcance de Ambiental en seco.' :alcance_nuevas 'filas nuevas de alcance de la carrera AMB. No se guardó nada, y -v aplicar=1 lo guarda.'
\endif
