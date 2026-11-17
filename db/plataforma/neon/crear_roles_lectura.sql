-- Crea los roles de solo lectura de la base en Neon. Se corre a mano con el usuario dueño del proyecto de Neon
-- y la conexión directa, y se puede repetir sin romper nada.
--
--   export POWERBI_CLAVE="$(openssl rand -base64 24)"    # se guarda en el gestor de contraseñas
--   export RESPALDO_DB_CLAVE="$(openssl rand -base64 24)"
--   psql "host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=verify-full sslrootcert=system" \
--        -v ON_ERROR_STOP=1 -f plataforma/neon/crear_roles_lectura.sql
--
-- Hay tres roles.
--   abet_lectura      rol de grupo, sin inicio de sesión, con uso del esquema abet y SELECT solo sobre las dos
--                     vistas. El callback db/callbacks/afterMigrate__permisos_lectura.sql le repone esos permisos
--                     después de cada migrate.
--   powerbi_lectura   usuario de Power BI, miembro de abet_lectura, con un máximo de 5 conexiones.
--   abet_respaldo     usuario del respaldo diario, con SELECT sobre todas las tablas y secuencias de abet y, desde
--                     V1_09, de acceso, que pg_dump necesita. Así el secreto que guarda GitHub no sirve para
--                     cambiar ni borrar la base.
--
-- El control real son los permisos. Las sesiones de los dos usuarios empiezan además en solo lectura, pero eso
-- es solo un valor por defecto que el propio usuario puede apagar, así que sirve como defensa adicional.
--
-- Los roles se crean por SQL y no desde la consola de Neon, porque Neon da a los roles de la consola el rol
-- neon_superuser, con atributos de administración (CREATEROLE, CREATEDB, BYPASSRLS) que un usuario de lectura
-- no necesita.
--
-- Las contraseñas se leen de las variables de entorno POWERBI_CLAVE y RESPALDO_DB_CLAVE, así que no pasan por
-- la línea de comandos ni por el historial. Neon pide recibirlas en texto plano para revisar que sean robustas,
-- por eso no se usa \password, que las manda ya cifradas. Si una variable falta, ese usuario queda sin
-- contraseña nueva y el script lo avisa.

\set ON_ERROR_STOP 1
\set ECHO none

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'abet_lectura') THEN
        CREATE ROLE abet_lectura NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'powerbi_lectura') THEN
        CREATE ROLE powerbi_lectura LOGIN CONNECTION LIMIT 5;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'abet_respaldo') THEN
        CREATE ROLE abet_respaldo LOGIN CONNECTION LIMIT 2;
    END IF;
END
$$;

SET client_min_messages = warning;
GRANT abet_lectura TO powerbi_lectura;
RESET client_min_messages;

ALTER ROLE powerbi_lectura CONNECTION LIMIT 5;
ALTER ROLE abet_respaldo CONNECTION LIMIT 2;
ALTER ROLE powerbi_lectura SET default_transaction_read_only = on;
ALTER ROLE abet_respaldo SET default_transaction_read_only = on;

-- Sin tablas ni funciones temporales para quien no es dueño, porque una función temporal escrita por el lector
-- es la vía para intentar ver filas que una vista oculta. El dueño de la base conserva ese permiso.
REVOKE TEMPORARY ON DATABASE :"DBNAME" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"DBNAME" TO abet_lectura, abet_respaldo;

-- Las funciones que creen las migraciones futuras no quedan ejecutables por cualquiera.
ALTER DEFAULT PRIVILEGES IN SCHEMA abet REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

-- Los mismos permisos que da el callback, para no esperar al próximo migrate.
GRANT USAGE ON SCHEMA abet TO abet_lectura, abet_respaldo;
GRANT SELECT ON abet.v_tabla_maestra_pi, abet.v_r17_por_pi TO abet_lectura;
GRANT SELECT ON ALL TABLES IN SCHEMA abet TO abet_respaldo;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA abet TO abet_respaldo;

-- Desde V1_09, abet_respaldo lee también las tablas y secuencias de acceso, porque pg_dump bloquea cada tabla que
-- vuelca, aunque de credencial, sesion, intento_fallido y codigo_acceso guarde solo la definición.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'acceso') THEN
        GRANT USAGE ON SCHEMA acceso TO abet_respaldo;
        GRANT SELECT ON ALL TABLES IN SCHEMA acceso TO abet_respaldo;
        GRANT SELECT ON ALL SEQUENCES IN SCHEMA acceso TO abet_respaldo;
    END IF;
END
$$;

-- Comprobación final. Se detiene si algo quedó distinto de lo que este archivo promete.
DO $$
DECLARE
    r record;
BEGIN
    FOR r IN SELECT rolname, rolsuper, rolbypassrls, rolcreaterole, rolcreatedb, rolreplication, rolcanlogin
             FROM pg_roles WHERE rolname IN ('abet_lectura', 'powerbi_lectura', 'abet_respaldo') LOOP
        IF r.rolsuper OR r.rolbypassrls OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication THEN
            RAISE EXCEPTION 'El rol % tiene un atributo de administración y no debe usarse para leer', r.rolname;
        END IF;
        IF r.rolname = 'abet_lectura' AND r.rolcanlogin THEN
            RAISE EXCEPTION 'abet_lectura es un rol de grupo y no debe poder iniciar sesión';
        END IF;
    END LOOP;
    -- Membresías directas e indirectas: powerbi_lectura solo llega a abet_lectura y abet_respaldo a ninguno.
    IF EXISTS (SELECT 1 FROM pg_roles g
               WHERE g.rolname NOT IN ('powerbi_lectura', 'abet_lectura')
                 AND pg_has_role('powerbi_lectura', g.oid, 'MEMBER')) THEN
        RAISE EXCEPTION 'powerbi_lectura pertenece, directa o indirectamente, a otro rol además de abet_lectura';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles g
               WHERE g.rolname <> 'abet_respaldo' AND pg_has_role('abet_respaldo', g.oid, 'MEMBER')) THEN
        RAISE EXCEPTION 'abet_respaldo pertenece a otro rol';
    END IF;
    IF has_database_privilege('powerbi_lectura', current_database(), 'TEMPORARY') THEN
        RAISE EXCEPTION 'powerbi_lectura todavía puede crear objetos temporales';
    END IF;
    IF has_table_privilege('powerbi_lectura', 'abet.medicion', 'SELECT') THEN
        RAISE EXCEPTION 'powerbi_lectura puede leer una tabla de base y solo debe leer las vistas';
    END IF;
    -- Los IF van anidados porque has_schema_privilege falla si el esquema acceso todavía no existe.
    IF EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'acceso') THEN
        IF has_schema_privilege('powerbi_lectura', 'acceso', 'USAGE') THEN
            RAISE EXCEPTION 'powerbi_lectura puede entrar al esquema acceso, que guarda los usuarios y sus credenciales';
        END IF;
        IF NOT has_schema_privilege('abet_respaldo', 'acceso', 'USAGE') THEN
            RAISE EXCEPTION 'abet_respaldo no puede entrar al esquema acceso, y el respaldo fallaría';
        END IF;
    END IF;
    IF NOT has_schema_privilege('abet_respaldo', 'abet', 'USAGE')
       OR EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                  WHERE n.nspname IN ('abet', 'acceso') AND c.relkind IN ('r', 'p', 'S')
                    AND NOT has_table_privilege('abet_respaldo', c.oid, 'SELECT')) THEN
        RAISE EXCEPTION 'abet_respaldo no puede leer alguna tabla o secuencia de abet o acceso, y el respaldo fallaría';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
               WHERE n.nspname = 'abet' AND c.relname IN ('v_tabla_maestra_pi', 'v_r17_por_pi')
                 AND NOT coalesce(c.reloptions @> ARRAY['security_barrier=true'], false)) THEN
        RAISE EXCEPTION 'Una de las vistas no tiene security_barrier; hace falta flyway migrate antes de este script';
    END IF;
    RAISE NOTICE 'Roles de lectura listos, sin atributos de administración y con las vistas protegidas';
END
$$;

\getenv clave_powerbi POWERBI_CLAVE
\if :{?clave_powerbi}
    ALTER ROLE powerbi_lectura PASSWORD :'clave_powerbi';
    \echo 'Contraseña de powerbi_lectura fijada desde POWERBI_CLAVE.'
\else
    \echo 'Aviso: falta POWERBI_CLAVE, así que powerbi_lectura no recibe contraseña nueva.'
\endif
\unset clave_powerbi

\getenv clave_respaldo RESPALDO_DB_CLAVE
\if :{?clave_respaldo}
    ALTER ROLE abet_respaldo PASSWORD :'clave_respaldo';
    \echo 'Contraseña de abet_respaldo fijada desde RESPALDO_DB_CLAVE.'
\else
    \echo 'Aviso: falta RESPALDO_DB_CLAVE, así que abet_respaldo no recibe contraseña nueva.'
\endif
\unset clave_respaldo
