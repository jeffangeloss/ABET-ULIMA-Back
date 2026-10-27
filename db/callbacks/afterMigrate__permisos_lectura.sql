-- Callback de Flyway que corre al final de cada migrate, haya o no migraciones pendientes.
-- Repone los permisos de los roles de lectura que crea db/plataforma/neon/crear_roles_lectura.sql.
--   abet_lectura    uso del esquema abet y SELECT solo sobre las dos vistas, que es lo que lee Power BI.
--   abet_respaldo   SELECT sobre todas las tablas y secuencias de abet, que pg_dump necesita para el respaldo.
-- Hace falta repetirlo en cada migrate porque las repetibles R__ borran y recrean las vistas, y con eso
-- PostgreSQL borra los permisos que tenían, y porque una migración nueva puede crear tablas nuevas.
-- Si un rol no existe, como en la base local o en el CI, su parte no hace nada, así que el mismo callback
-- sirve en todos los entornos.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'abet_lectura') THEN
        GRANT USAGE ON SCHEMA abet TO abet_lectura;
        GRANT SELECT ON abet.v_tabla_maestra_pi, abet.v_r17_por_pi TO abet_lectura;
        RAISE NOTICE 'Permisos de abet_lectura repuestos sobre las dos vistas';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'abet_respaldo') THEN
        GRANT USAGE ON SCHEMA abet TO abet_respaldo;
        GRANT SELECT ON ALL TABLES IN SCHEMA abet TO abet_respaldo;
        GRANT SELECT ON ALL SEQUENCES IN SCHEMA abet TO abet_respaldo;
        RAISE NOTICE 'Permisos de abet_respaldo repuestos sobre las tablas y secuencias de abet';
    END IF;
END
$$;
