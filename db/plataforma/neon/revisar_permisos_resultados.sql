-- Revisa en solo lectura que el rol de la aplicación lee cada tabla y vista que usa GET /api/resultados, la ruta 12
-- de la spec 004 (T020 y T021, FR-020 y J-26). La spec no trae migración, porque abet_app ya lee abet.v_r17_por_pi,
-- abet.so, abet.pi, abet.instrumento y abet.plan_medicion desde crear_rol_app.sql, y este guion lo comprueba junto con
-- lo que leen la sesión (app/sesion.py) y la regla de alcance (app/permisos.py).
--
-- No escribe nada. Corre dentro de una transacción READ ONLY que se deshace al final, y se puede repetir. Jefferson lo
-- corre en la rama develop de Neon desde su Windows antes de fusionar el PR del Back, con una conexión de solo lectura,
-- y las pruebas lo corren contra la base desechable (tests/test_permisos_resultados.py).
--
--   psql "<conexión>" -X -q -v ON_ERROR_STOP=1 -v rol_app=abet_app -f db/plataforma/neon/revisar_permisos_resultados.sql
--
-- El nombre del rol llega en la variable de psql rol_app y vale abet_app si no se pasa. Esperado: una línea por objeto,
-- todas con t, y la línea «Faltan 0 permisos de lectura de la ruta 12.». Si falta alguno, su línea lleva f, el error
-- nombra el objeto y psql sale con un código distinto de 0.

\set ON_ERROR_STOP 1
\pset format unaligned
\pset tuples_only on
\if :{?rol_app}
\else
    \set rol_app abet_app
\endif

-- Lo que lee la ruta 12 (app/rutas/resultados.py), su sesión (app/sesion.py) y su regla de alcance (app/permisos.py).
\set objetos '{abet.asignatura,abet.carga,abet.catalogo_vigencia,abet.conjunto_reglas,abet.instrumento,abet.parametro_valor,abet.periodo,abet.pi,abet.plan_estudios,abet.plan_medicion,abet.seccion,abet.so,abet.v_r17_por_pi,acceso.docente_seccion,acceso.sesion,acceso.usuario_autorizado}'

BEGIN TRANSACTION READ ONLY;

-- Los bloques DO no ven las variables de psql, así que el rol y la lista pasan por variables de la transacción.
SET LOCAL abet.rol_app = :'rol_app';
SET LOCAL abet.objetos = :'objetos';

SELECT objeto, has_table_privilege(:'rol_app', objeto, 'SELECT')
FROM unnest(CAST(:'objetos' AS text[])) AS objeto
ORDER BY objeto;

SELECT count(*) AS faltan
FROM unnest(CAST(:'objetos' AS text[])) AS objeto
WHERE NOT has_table_privilege(:'rol_app', objeto, 'SELECT') \gset
\echo 'Faltan' :faltan 'permisos de lectura de la ruta 12.'

DO $$
DECLARE
    v_rol    text := current_setting('abet.rol_app');
    v_faltan text;
BEGIN
    SELECT string_agg(objeto, ', ' ORDER BY objeto) INTO v_faltan
    FROM unnest(CAST(current_setting('abet.objetos') AS text[])) AS objeto
    WHERE NOT has_table_privilege(v_rol, objeto, 'SELECT');
    IF v_faltan IS NOT NULL THEN
        RAISE EXCEPTION 'El rol % no lee %, que usa la ruta 12', v_rol, v_faltan;
    END IF;
END
$$;

ROLLBACK;
