-- Datos operativos del periodo 2026-2 con datos inventados (script de datos, no migración; US-03, US-04, FR-006,
-- D-09 y D-13). Siembra la vigencia del catálogo AMB-2026 en 2026-2, las secciones 410 y 411 de 450002, su plan de
-- medición con los PI 5.1, 5.2 y 5.3 del SO 5, un coordinador y dos profesores de prueba y la sección de cada
-- profesor. No asigna contraseñas, que el comando de US-05 guarda aparte como hash, ni crea estudiantes ni cargas.
-- Todo es inventado. Los correos terminan en @example.invalid y el archivo no trae códigos de estudiante.
-- Se corre con el usuario dueño de la base y la conexión directa, después de V1_09, y se puede repetir. Cada INSERT
-- usa ON CONFLICT DO NOTHING, así que otra corrida no duplica filas ni cambia las que ya existen, y la comprobación
-- final detiene el script, y deshace todo, si una fila existente no es la que el script espera.
-- En las pruebas va después de db/pruebas/datos_sinteticos.sql, que ya trae la vigencia, la sección 410 y su plan.
--
--   psql "host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=verify-full sslrootcert=system" \
--        -v ON_ERROR_STOP=1 -f db/datos/periodo_2026_2_inventado.sql

\set ON_ERROR_STOP 1

BEGIN;

-- Versión de catálogo que rige en 2026-2 para Ambiental; el plan de medición solo acepta esa versión.
INSERT INTO abet.catalogo_vigencia (periodo_id, carrera_id, catalogo_version_id)
SELECT pe.periodo_id, cv.carrera_id, cv.catalogo_version_id
FROM abet.periodo pe
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026'
WHERE pe.codigo = '2026-2'
ON CONFLICT DO NOTHING;

-- Secciones 410 y 411 de 450002, con el curso de Blackboard que declara la hoja de cada export inventado.
INSERT INTO abet.seccion (periodo_id, asignatura_id, numero, curso_blackboard)
SELECT pe.periodo_id, a.asignatura_id, v.numero, v.curso_blackboard
FROM (VALUES ('410', 'SINTETICO_20262_450002_410'),
             ('411', 'SINTETICO_20262_450002_411')) AS v (numero, curso_blackboard)
JOIN abet.periodo pe ON pe.codigo = '2026-2'
JOIN abet.asignatura a ON a.codigo = '450002'
ON CONFLICT DO NOTHING;

-- Plan de medición de 450002 en 2026-2 (valor provisional de D-09), con el instrumento del par asignatura y SO.
INSERT INTO abet.plan_medicion (periodo_id, asignatura_id, carrera_id, catalogo_version_id, so_id, pi_id, instrumento_id)
SELECT pe.periodo_id, a.asignatura_id, cv.carrera_id, cv.catalogo_version_id, p.so_id, p.pi_id, aso.instrumento_id
FROM abet.periodo pe
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026'
JOIN abet.asignatura a ON a.codigo = '450002'
JOIN abet.pi p ON p.catalogo_version_id = cv.catalogo_version_id AND p.codigo IN ('5.1', '5.2', '5.3')
JOIN abet.asignatura_so aso ON aso.catalogo_version_id = cv.catalogo_version_id
                           AND aso.asignatura_id = a.asignatura_id AND aso.so_id = p.so_id
WHERE pe.codigo = '2026-2'
ON CONFLICT DO NOTHING;

-- Usuarios de prueba del piloto (valor provisional de D-13), activos y sin contraseña.
INSERT INTO acceso.usuario_autorizado (correo, rol)
VALUES ('coordinacion@example.invalid', 'COORDINADOR'),
       ('docente410@example.invalid', 'PROFESOR'),
       ('docente411@example.invalid', 'PROFESOR')
ON CONFLICT DO NOTHING;

-- Cada profesor dicta su sección. El coordinador no tiene secciones, porque ve todas las de la carrera.
INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)
SELECT u.usuario_id, s.seccion_id
FROM (VALUES ('docente410@example.invalid', '410'),
             ('docente411@example.invalid', '411')) AS v (correo, numero)
JOIN acceso.usuario_autorizado u ON u.correo = v.correo
JOIN abet.periodo pe ON pe.codigo = '2026-2'
JOIN abet.asignatura a ON a.codigo = '450002'
JOIN abet.seccion s ON s.periodo_id = pe.periodo_id AND s.asignatura_id = a.asignatura_id AND s.numero = v.numero
ON CONFLICT DO NOTHING;

-- Comprobación final. Cada dato del periodo queda como lo describe la cabecera, aunque ya existiera antes.
DO $$
DECLARE
    v_texto text;
BEGIN
    SELECT string_agg(cv.codigo, ',') INTO v_texto
    FROM abet.catalogo_vigencia v
    JOIN abet.periodo pe ON pe.periodo_id = v.periodo_id AND pe.codigo = '2026-2'
    JOIN abet.carrera c ON c.carrera_id = v.carrera_id AND c.codigo = 'AMB'
    JOIN abet.catalogo_version cv ON cv.catalogo_version_id = v.catalogo_version_id;
    IF v_texto IS DISTINCT FROM 'AMB-2026' THEN
        RAISE EXCEPTION 'Ambiental no tiene AMB-2026 como versión vigente en 2026-2 (%)', coalesce(v_texto, 'ninguna');
    END IF;

    SELECT string_agg(s.numero || '=' || coalesce(s.curso_blackboard, 'sin curso'), ',' ORDER BY s.numero) INTO v_texto
    FROM abet.seccion s
    JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
    JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002'
    WHERE s.numero IN ('410', '411');
    IF v_texto IS DISTINCT FROM '410=SINTETICO_20262_450002_410,411=SINTETICO_20262_450002_411' THEN
        RAISE EXCEPTION 'Las secciones 410 y 411 de 450002 en 2026-2 no son las esperadas (%)', coalesce(v_texto, 'ninguna');
    END IF;

    SELECT string_agg(p.codigo, ',' ORDER BY p.codigo) INTO v_texto
    FROM abet.plan_medicion pm
    JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id AND pe.codigo = '2026-2'
    JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id AND a.codigo = '450002'
    JOIN abet.pi p ON p.pi_id = pm.pi_id;
    IF v_texto IS DISTINCT FROM '5.1,5.2,5.3' THEN
        RAISE EXCEPTION 'El plan de medición de 450002 en 2026-2 no es 5.1, 5.2 y 5.3 (%)', coalesce(v_texto, 'vacío');
    END IF;

    SELECT string_agg(u.correo || '=' || u.rol || CASE WHEN u.activo THEN '' ELSE ' inactivo' END, ',' ORDER BY u.correo)
      INTO v_texto
    FROM acceso.usuario_autorizado u
    WHERE u.correo IN ('coordinacion@example.invalid', 'docente410@example.invalid', 'docente411@example.invalid');
    IF v_texto IS DISTINCT FROM 'coordinacion@example.invalid=COORDINADOR,docente410@example.invalid=PROFESOR,'
                                || 'docente411@example.invalid=PROFESOR' THEN
        RAISE EXCEPTION 'Los usuarios de prueba no tienen el rol o el estado esperados (%)', coalesce(v_texto, 'ninguno');
    END IF;

    SELECT string_agg(u.correo || '=' || s.numero, ',' ORDER BY u.correo, s.numero) INTO v_texto
    FROM acceso.docente_seccion d
    JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
    JOIN abet.seccion s ON s.seccion_id = d.seccion_id
    JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
    JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002'
    WHERE u.correo IN ('coordinacion@example.invalid', 'docente410@example.invalid', 'docente411@example.invalid');
    IF v_texto IS DISTINCT FROM 'docente410@example.invalid=410,docente411@example.invalid=411' THEN
        RAISE EXCEPTION 'Las secciones de 450002 en 2026-2 de los usuarios de prueba no son las esperadas (%)',
            coalesce(v_texto, 'ninguna');
    END IF;
    IF EXISTS (SELECT 1 FROM acceso.docente_seccion d
               JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
               WHERE u.correo = 'coordinacion@example.invalid') THEN
        RAISE EXCEPTION 'coordinacion@example.invalid tiene secciones asignadas y el coordinador ve todas sin asignación';
    END IF;
    RAISE NOTICE 'Datos de 2026-2 listos (vigencia AMB-2026, secciones 410 y 411 de 450002, plan 5.1 a 5.3 y usuarios de prueba)';
END
$$;

COMMIT;
