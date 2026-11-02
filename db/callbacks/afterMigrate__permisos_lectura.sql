-- Callback de Flyway que corre al final de cada migrate, haya o no migraciones pendientes.
-- Repone los permisos de los roles de lectura que crea db/plataforma/neon/crear_roles_lectura.sql.
--   abet_lectura    uso del esquema abet y SELECT solo sobre las dos vistas, que es lo que lee Power BI.
--   abet_respaldo   SELECT sobre todas las tablas y secuencias de abet y, desde V1_09, de acceso, que pg_dump
--                   necesita para el respaldo. pg_dump bloquea cada tabla que vuelca, también las de acceso cuyos
--                   datos no guarda, así que abet_respaldo puede leer credenciales y sesiones aunque el archivo
--                   del respaldo no las traiga.
--   rol de la API   SELECT sobre las dos vistas, que la API lee para el R-17. Es abet_app en Neon y otro nombre en
--                   las pruebas, así que el callback lo reconoce por lo que puede hacer, que es insertar en
--                   abet.carga sin ser su dueño ni tener atributos de administración. El resto de sus permisos lo da
--                   db/plataforma/neon/crear_rol_app.sql, y una R__ no lo toca.
-- Hace falta repetirlo en cada migrate porque las repetibles R__ borran y recrean las vistas, y con eso
-- PostgreSQL borra los permisos que tenían, y porque una migración nueva puede crear tablas nuevas.
-- Si un rol no existe, como en la base local o en el CI, su parte no hace nada, y lo mismo pasa con acceso antes
-- de V1_09, así que el mismo callback sirve en todos los entornos.
DO $$
DECLARE
    r record;
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
        IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'acceso') THEN
            GRANT USAGE ON SCHEMA acceso TO abet_respaldo;
            GRANT SELECT ON ALL TABLES IN SCHEMA acceso TO abet_respaldo;
            GRANT SELECT ON ALL SEQUENCES IN SCHEMA acceso TO abet_respaldo;
            RAISE NOTICE 'Permisos de abet_respaldo repuestos sobre las tablas y secuencias de acceso';
        END IF;
    END IF;
    IF to_regclass('abet.carga') IS NOT NULL THEN
        FOR r IN SELECT rolname FROM pg_roles
                 WHERE NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb AND NOT rolbypassrls
                   AND NOT rolreplication AND rolname <> current_user AND rolname !~ '^pg_'
                   AND rolname <> (SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid = 'abet.carga'::regclass)
                   AND has_table_privilege(rolname, 'abet.carga', 'INSERT')
        LOOP
            EXECUTE format('GRANT SELECT ON abet.v_tabla_maestra_pi, abet.v_r17_por_pi TO %I', r.rolname);
            RAISE NOTICE 'Permisos de % repuestos sobre las dos vistas', r.rolname;
        END LOOP;
    END IF;
END
$$;
