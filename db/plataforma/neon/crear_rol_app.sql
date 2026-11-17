-- Crea el rol de la aplicación con privilegio mínimo en la base de Neon (US-02, FR-004, J-02 y Principio VI).
-- Se corre a mano con el usuario dueño del proyecto de Neon y la conexión directa, después de V1_09, y se puede
-- repetir. Cada corrida deja los permisos del rol tal como los declara este archivo, en una sola transacción.
--
--   export APP_DB_CLAVE="$(openssl rand -hex 32)"    # se guarda en el gestor de claves
--   psql "host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=verify-full sslrootcert=system" \
--        -v ON_ERROR_STOP=1 -f db/plataforma/neon/crear_rol_app.sql
--
-- La clave va en hexadecimal porque la aplicación la usa dentro de DATABASE_URL, donde una «/» de base64 corta la
-- cadena de conexión si no va codificada en porcentaje.
--
-- El nombre del rol llega en la variable de psql rol_app y vale abet_app si no se pasa. Las pruebas de db/pruebas/
-- usan -v rol_app=<nombre único> en cada corrida, porque los roles son del clúster y no de una base.
--
-- Permisos que deja el script.
--   abet     SELECT sobre organización, catálogo, plan de medición, reglas, registro de cargas y las dos vistas;
--            INSERT en archivo_origen, carga, carga_columna, carga_fila, estudiante, medicion y rechazo_fila;
--            UPDATE solo de estado, filas_leidas, filas_aceptadas, filas_rechazadas y terminada_en de carga.
--   acceso   SELECT de usuario_autorizado, credencial, docente_seccion, sesion e intento_fallido; INSERT solo de
--            sesion.usuario_id, sesion.hash_token e intento_fallido.hash_cuenta, porque las fechas de una sesión
--            y de un intento salen de los valores por defecto de la base; UPDATE solo de sesion.expira_en, para el
--            cierre de sesión.
-- El rol no tiene DELETE ni TRUNCATE en ninguna tabla, no escribe conjunto_reglas, parametro_valor, catalogo_*,
-- plan_medicion, seccion, usuario_autorizado, credencial ni docente_seccion, y no cambia conjunto_reglas_id,
-- subida_por, archivo_id, seccion_id ni reemplaza_carga_id de una carga. Tampoco toca acceso.codigo_acceso, que
-- llega con el corte 2, cuando T083 le suma SELECT, INSERT y el UPDATE de intentos y usado_en.
--
-- Las repetibles R__ borran y recrean sus vistas, y con eso el rol pierde el SELECT de v_r17_por_pi y de
-- v_tabla_maestra_pi. Desde T023, db/callbacks/afterMigrate__permisos_lectura.sql repone esos dos permisos al final
-- de cada migrate de Flyway. En los caminos con psql, este script se repite después de volver a aplicar una R__.
--
-- El rol se crea por SQL y no desde la consola de Neon, porque Neon da a los roles de la consola el rol
-- neon_superuser, con atributos de administración que la aplicación no necesita, igual que en
-- crear_roles_lectura.sql. Convive con abet_lectura, powerbi_lectura y abet_respaldo, que siguen de solo lectura.
--
-- La contraseña se lee de la variable de entorno APP_DB_CLAVE con \getenv, así que no pasa por la línea de
-- comandos, por el historial ni por la salida. Neon pide recibirla en texto plano para revisar que sea robusta,
-- por eso no se usa \password. Si la variable falta, el rol queda sin contraseña nueva y el script lo avisa (T028).

\set ON_ERROR_STOP 1
\set ECHO none
\if :{?rol_app}
\else
    \set rol_app abet_app
\endif

BEGIN;

-- Los bloques DO no ven las variables de psql, así que el nombre del rol pasa por una variable de la sesión.
SET abet.rol_app = :'rol_app';

-- El rol de la aplicación nunca es uno de lectura ni el usuario que corre el script.
DO $$
DECLARE
    v_rol text := current_setting('abet.rol_app');
BEGIN
    IF v_rol IN ('abet_lectura', 'powerbi_lectura', 'abet_respaldo') OR v_rol IN (current_user, session_user) THEN
        RAISE EXCEPTION 'El rol % no puede ser el rol de la aplicación', v_rol;
    END IF;
END
$$;

SELECT format('CREATE ROLE %I LOGIN', :'rol_app')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'rol_app') \gexec

-- Permisos desde cero. REVOKE ALL sobre una tabla quita también los permisos por columna.
REVOKE ALL ON DATABASE :"DBNAME" FROM :"rol_app";
REVOKE ALL ON SCHEMA abet, acceso FROM :"rol_app";
REVOKE ALL ON ALL TABLES IN SCHEMA abet, acceso FROM :"rol_app";
REVOKE ALL ON ALL SEQUENCES IN SCHEMA abet, acceso FROM :"rol_app";

GRANT CONNECT ON DATABASE :"DBNAME" TO :"rol_app";
GRANT USAGE ON SCHEMA abet, acceso TO :"rol_app";

-- Lectura de organización, catálogo, plan de medición, reglas, registro de cargas y vistas del R-17. La lista
-- deja fuera flyway_schema_history, que la aplicación no necesita.
GRANT SELECT ON
    abet.facultad, abet.carrera, abet.periodo, abet.asignatura, abet.seccion,
    abet.catalogo_version, abet.catalogo_vigencia, abet.so, abet.pi, abet.rubrica_nivel, abet.instrumento,
    abet.plan_estudios, abet.asignatura_so, abet.competencia, abet.competencia_so, abet.asignatura_competencia,
    abet.plan_medicion,
    abet.conjunto_reglas, abet.parametro, abet.parametro_valor, abet.conversion_nivel_0_1,
    abet.archivo_origen, abet.carga, abet.carga_columna, abet.carga_fila, abet.estudiante, abet.medicion,
    abet.rechazo_fila,
    abet.v_r17_por_pi, abet.v_tabla_maestra_pi
    TO :"rol_app";

-- Escritura de una carga en una sola transacción de la aplicación (Principio III).
GRANT INSERT ON abet.archivo_origen, abet.carga, abet.carga_columna, abet.carga_fila, abet.estudiante,
                abet.medicion, abet.rechazo_fila TO :"rol_app";
-- Cierre de la carga. conjunto_reglas_id no está en la lista, así que una carga publicada conserva sus reglas.
GRANT UPDATE (estado, filas_leidas, filas_aceptadas, filas_rechazadas, terminada_en) ON abet.carga TO :"rol_app";

-- La aplicación lee usuarios, credenciales, asignaciones, sesiones e intentos fallidos, abre y cierra sesiones y
-- registra cada intento fallido. El INSERT va por columnas, así que creada_en, expira_en e intentado_en salen
-- siempre de now() y el tope de 12 horas de ck_sesion_vigencia corre desde la hora real de la sesión. Las altas,
-- las bajas, las contraseñas y las asignaciones quedan para el dueño de la base.
GRANT SELECT ON acceso.usuario_autorizado, acceso.credencial, acceso.docente_seccion, acceso.sesion,
                acceso.intento_fallido TO :"rol_app";
GRANT INSERT (usuario_id, hash_token) ON acceso.sesion TO :"rol_app";
GRANT UPDATE (expira_en) ON acceso.sesion TO :"rol_app";
GRANT INSERT (hash_cuenta) ON acceso.intento_fallido TO :"rol_app";

-- Comprobación final. Se detiene, y la transacción se deshace, si algo queda distinto de lo que promete el archivo.
-- Las funciones has_*_privilege cuentan también lo que llega por PUBLIC.
DO $$
DECLARE
    v_rol   text := current_setting('abet.rol_app');
    r       record;
    v_texto text;
BEGIN
    SELECT rolsuper, rolbypassrls, rolcreaterole, rolcreatedb, rolreplication, rolcanlogin
      INTO r FROM pg_roles WHERE rolname = v_rol;
    IF r.rolsuper OR r.rolbypassrls OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication THEN
        RAISE EXCEPTION 'El rol % tiene un atributo de administración y la aplicación no debe usarlo', v_rol;
    END IF;
    IF NOT r.rolcanlogin THEN
        RAISE EXCEPTION 'El rol % no puede iniciar sesión', v_rol;
    END IF;
    -- Membresías directas e indirectas. El rol no hereda permisos de ningún otro.
    IF EXISTS (SELECT 1 FROM pg_roles g WHERE g.rolname <> v_rol AND pg_has_role(v_rol, g.oid, 'MEMBER')) THEN
        RAISE EXCEPTION 'El rol % pertenece a otro rol y heredaría sus permisos', v_rol;
    END IF;
    IF NOT has_database_privilege(v_rol, current_database(), 'CONNECT')
       OR NOT has_schema_privilege(v_rol, 'abet', 'USAGE') OR NOT has_schema_privilege(v_rol, 'acceso', 'USAGE')
       OR has_schema_privilege(v_rol, 'abet', 'CREATE') OR has_schema_privilege(v_rol, 'acceso', 'CREATE') THEN
        RAISE EXCEPTION 'El rol % no tiene la conexión y el uso de los esquemas, o puede crear objetos en ellos', v_rol;
    END IF;
    -- Ningún UPDATE de tabla completa, DELETE, TRUNCATE, REFERENCES ni TRIGGER, que el dueño de una tabla sí tendría.
    -- REFERENCES admite permisos por columna, así que se mira con has_any_column_privilege.
    SELECT string_agg(n.nspname || '.' || c.relname, ', ' ORDER BY n.nspname, c.relname) INTO v_texto
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname IN ('abet', 'acceso') AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
      AND (has_table_privilege(v_rol, c.oid, 'UPDATE') OR has_table_privilege(v_rol, c.oid, 'DELETE')
           OR has_table_privilege(v_rol, c.oid, 'TRUNCATE') OR has_any_column_privilege(v_rol, c.oid, 'REFERENCES')
           OR has_table_privilege(v_rol, c.oid, 'TRIGGER'));
    IF v_texto IS NOT NULL THEN
        RAISE EXCEPTION 'El rol % puede modificar o vaciar %', v_rol, v_texto;
    END IF;
    -- INSERT de tabla completa solo en las siete tablas de una carga.
    SELECT string_agg(n.nspname || '.' || c.relname, ',' ORDER BY n.nspname, c.relname) INTO v_texto
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname IN ('abet', 'acceso') AND c.relkind IN ('r', 'p', 'v', 'm', 'f')
      AND has_table_privilege(v_rol, c.oid, 'INSERT');
    IF v_texto IS DISTINCT FROM 'abet.archivo_origen,abet.carga,abet.carga_columna,abet.carga_fila,abet.estudiante,'
                                || 'abet.medicion,abet.rechazo_fila' THEN
        RAISE EXCEPTION 'El rol % inserta filas completas en otras tablas que las de una carga (%)', v_rol, v_texto;
    END IF;
    -- INSERT por columnas, que has_table_privilege no ve, solo en las columnas de sesion e intento_fallido que no
    -- tienen valor por defecto.
    SELECT string_agg(n.nspname || '.' || c.relname || '.' || a.attname, ',' ORDER BY n.nspname, c.relname, a.attnum)
      INTO v_texto
    FROM pg_attribute a
    JOIN pg_class c ON c.oid = a.attrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname IN ('abet', 'acceso') AND c.relkind IN ('r', 'p', 'v', 'm', 'f') AND a.attnum > 0
      AND NOT a.attisdropped AND NOT has_table_privilege(v_rol, c.oid, 'INSERT')
      AND has_column_privilege(v_rol, c.oid, a.attnum, 'INSERT');
    IF v_texto IS DISTINCT FROM 'acceso.intento_fallido.hash_cuenta,acceso.sesion.usuario_id,acceso.sesion.hash_token' THEN
        RAISE EXCEPTION 'El rol % inserta otras columnas que usuario_id y hash_token de sesion y hash_cuenta de intento_fallido (%)', v_rol, v_texto;
    END IF;
    SELECT string_agg(n.nspname || '.' || c.relname || '.' || a.attname, ',' ORDER BY n.nspname, c.relname, a.attnum)
      INTO v_texto
    FROM pg_attribute a
    JOIN pg_class c ON c.oid = a.attrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname IN ('abet', 'acceso') AND c.relkind IN ('r', 'p') AND a.attnum > 0 AND NOT a.attisdropped
      AND has_column_privilege(v_rol, c.oid, a.attnum, 'UPDATE');
    IF v_texto IS DISTINCT FROM 'abet.carga.estado,abet.carga.filas_leidas,abet.carga.filas_aceptadas,'
                                || 'abet.carga.filas_rechazadas,abet.carga.terminada_en,acceso.sesion.expira_en' THEN
        RAISE EXCEPTION 'El rol % actualiza otras columnas que el estado y los conteos de la carga y el vencimiento de la sesión (%)', v_rol, v_texto;
    END IF;
    IF NOT has_table_privilege(v_rol, 'abet.v_r17_por_pi', 'SELECT')
       OR NOT has_table_privilege(v_rol, 'abet.v_tabla_maestra_pi', 'SELECT')
       OR NOT has_table_privilege(v_rol, 'abet.parametro_valor', 'SELECT')
       OR NOT has_table_privilege(v_rol, 'acceso.credencial', 'SELECT')
       OR NOT has_table_privilege(v_rol, 'acceso.intento_fallido', 'SELECT')
       OR has_any_column_privilege(v_rol, 'acceso.codigo_acceso', 'SELECT') THEN
        RAISE EXCEPTION 'El rol % no lee las vistas del R-17, las reglas, las credenciales o los intentos fallidos, o ya lee los códigos del corte 2', v_rol;
    END IF;
    RAISE NOTICE 'Rol % listo, sin atributos de administración y con los permisos de la aplicación', v_rol;
END
$$;

\getenv clave_app APP_DB_CLAVE
\if :{?clave_app}
    ALTER ROLE :"rol_app" PASSWORD :'clave_app';
    \echo 'Contraseña del rol' :rol_app 'fijada desde APP_DB_CLAVE.'
\else
    \echo 'Aviso: falta APP_DB_CLAVE, así que el rol' :rol_app 'no recibe contraseña nueva (T028).'
\endif
\unset clave_app

COMMIT;
