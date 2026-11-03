-- Marca la base de una rama de Neon con el entorno de Vercel que la usa, production en la rama principal y preview en
-- develop (T077). Al arrancar en Vercel, comprobar_base de app/configuracion.py compara esa marca con VERCEL_ENV y
-- detiene la API si no coinciden, así que una DATABASE_URL de Preview pegada con la rama principal no llega a escribir
-- en la base del piloto, y al revés.
--
--   psql "host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=require channel_binding=require" \
--        -v ON_ERROR_STOP=1 -v entorno=production -f db/plataforma/neon/marcar_entorno.sql
--
-- Se corre con el usuario dueño de la base y la conexión directa, una vez en cada rama, y se puede repetir. La marca
-- es el comentario de la base, «abet.entorno=production» o «abet.entorno=preview», así que ese comentario queda
-- reservado para ella. Lo cambia solo el dueño de la base, que en Neon no es superusuario, y lo lee cualquier rol con
-- shobj_description, también abet_app. No se usa ALTER DATABASE ... SET abet.entorno porque, desde PostgreSQL 15, un
-- parámetro personalizado solo lo guarda un superusuario o quien tenga SET sobre él, y en Neon nadie lo tiene.
--
-- Neon copia el comentario al crear o restablecer una rama desde otra, así que esa rama nace con la marca production.
-- Hasta que este script la vuelve a marcar con preview, la API de Preview no arranca contra ella y la de Production
-- arrancaría si su DATABASE_URL apuntara por error a esa rama. Por eso volver a marcar es el primer paso después de
-- crear o restablecer develop, antes de cualquier despliegue. pg_restore en una base nueva tampoco trae el comentario.

\set ON_ERROR_STOP 1

BEGIN;
-- Sin -v entorno, psql deja :'entorno' sin reemplazar y la sentencia falla con 42601.
SET LOCAL abet.marca_pedida = :'entorno';
DO $$
DECLARE
    pedida text := current_setting('abet.marca_pedida');
BEGIN
    IF pedida NOT IN ('production', 'preview') THEN
        RAISE EXCEPTION 'El entorno debe ser production o preview, no «%».', pedida;
    END IF;
    EXECUTE format('COMMENT ON DATABASE %I IS %L', current_database(), 'abet.entorno=' || pedida);
    RAISE NOTICE 'La base % queda marcada para %.', current_database(), pedida;
END
$$;
COMMIT;
