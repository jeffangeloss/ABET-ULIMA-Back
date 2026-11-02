-- Datos de prueba del profesor con varias secciones en 2026-2, con datos inventados (script de datos, no migración).
-- Sirven a las historias de usuario (user stories, US) US-04, US-06, US-07, US-09 y US-13 y a las reglas de negocio
-- (business rules, BR) BR-ACCESO-07, BR-ACCESO-08, BR-CARGA-09, BR-CARGA-11 y BR-CARGA-12.
-- Completa los datos de periodo_2026_2_inventado.sql con un profesor que dicta tres secciones de dos asignaturas, la
-- 412 de 450002 «Principios de Ingeniería Sostenible» y la 410 y la 412 de 450010 «Gestión Sostenible de Residuos»,
-- cada una con el curso de Blackboard que declara la hoja de su export inventado. Siembra el plan de medición de
-- 450010 en 2026-2, las tres secciones, el usuario docente.varias@example.invalid, PROFESOR, activo y sin contraseña,
-- y sus tres asignaciones en acceso.docente_seccion. Las dos secciones 412 de asignaturas distintas prueban que el
-- mismo número de sección en otra asignatura no se confunde.
-- Corre en las bases desechables de varias_secciones.feature y de db/pruebas/correr_pruebas.sh y, cuando haga falta,
-- en abet_sis_med_dev. No entra en Neon (T027), porque D-09 y D-13 fijan para el piloto el plan de 450002 y un
-- coordinador con dos profesores de prueba, y los escenarios que usan estos datos nunca corren en Neon.
-- El plan de 450010 mide los indicadores de desempeño (performance indicators, PI) 2.1 y 2.2 del resultado del
-- estudiante (student outcome, SO) 2 y el PI 5.1 del SO 5, los dos SO que asignatura_so le asigna, con su instrumento
-- Trabajo Integrador. Lleva tres PI porque los bloques I y II del R-17 tienen tres filas fijas
-- (plantillas/README.md). El SO 2 entra completo porque 450002 no lo mide, y el 5.1 es el PI que comparte con el
-- plan de 450002, así que la misma columna de PI en dos asignaturas comprueba que el R-17 de cada sección sale de su
-- propia carga.
-- La 410 de 450002 sigue solo con docente410@example.invalid, la 411 solo con docente411@example.invalid y el
-- coordinador sin secciones. El archivo no cambia ninguna fila de periodo_2026_2_inventado.sql, no asigna contraseñas
-- y no crea estudiantes ni cargas. Todo es inventado. El correo nuevo termina en @example.invalid y el archivo no trae
-- códigos de estudiante.
-- Se corre con el usuario dueño de la base, después de periodo_2026_2_inventado.sql, y se puede repetir. La
-- condición previa detiene el script si faltan los datos de ese archivo. Cada INSERT usa ON CONFLICT DO NOTHING, así
-- que otra corrida no duplica filas ni cambia las que ya existen. La comprobación final detiene el script, y deshace
-- todo, si el plan, los cursos de Blackboard, el rol y el estado del profesor, sus tres secciones, el único profesor
-- de prueba de cada sección o el coordinador sin secciones no quedan como los describe esta cabecera. No revisa
-- acceso.credencial, porque la contraseña se asigna aparte, como en periodo_2026_2_inventado.sql, y otra corrida
-- del archivo no debe fallar después de asignarla.
-- En las pruebas, db/pruebas/correr_pruebas.sh lo aplica dos veces después de periodo_2026_2_inventado.sql.
--
--   psql -X -v ON_ERROR_STOP=1 -d <base desechable> -f db/datos/varias_secciones_2026_2_inventado.sql

\set ON_ERROR_STOP 1

BEGIN;

-- Condición previa. periodo_2026_2_inventado.sql siembra la vigencia del catálogo en 2026-2, la 410 y la 411 de 450002
-- y los tres usuarios de prueba, y este archivo los completa sin repetirlos.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1
                   FROM abet.catalogo_vigencia v
                   JOIN abet.periodo pe ON pe.periodo_id = v.periodo_id AND pe.codigo = '2026-2'
                   JOIN abet.catalogo_version cv ON cv.catalogo_version_id = v.catalogo_version_id
                                                AND cv.codigo = 'AMB-2026')
       OR (SELECT count(*)
             FROM abet.seccion s
             JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
             JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002'
            WHERE s.numero IN ('410', '411')) <> 2
       OR (SELECT count(*)
             FROM acceso.usuario_autorizado
            WHERE correo IN ('coordinacion@example.invalid', 'docente410@example.invalid',
                             'docente411@example.invalid')) <> 3 THEN
        RAISE EXCEPTION 'Faltan los datos de db/datos/periodo_2026_2_inventado.sql, que se aplica antes de este archivo';
    END IF;
END
$$;

-- Plan de medición de 450010 en 2026-2, con el instrumento del par asignatura y SO.
INSERT INTO abet.plan_medicion (periodo_id, asignatura_id, carrera_id, catalogo_version_id, so_id, pi_id, instrumento_id)
SELECT pe.periodo_id, a.asignatura_id, cv.carrera_id, cv.catalogo_version_id, p.so_id, p.pi_id, aso.instrumento_id
FROM abet.periodo pe
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026'
JOIN abet.asignatura a ON a.codigo = '450010'
JOIN abet.pi p ON p.catalogo_version_id = cv.catalogo_version_id AND p.codigo IN ('2.1', '2.2', '5.1')
JOIN abet.asignatura_so aso ON aso.catalogo_version_id = cv.catalogo_version_id
                           AND aso.asignatura_id = a.asignatura_id AND aso.so_id = p.so_id
WHERE pe.codigo = '2026-2'
ON CONFLICT DO NOTHING;

-- La 412 de 450002 y la 410 y la 412 de 450010, con el curso de Blackboard que declara la hoja de cada export
-- inventado. Una sección que ya existe con otro curso de Blackboard, o un curso de Blackboard que ya usa otra
-- sección, no se pisa, y la comprobación final lo detecta.
INSERT INTO abet.seccion (periodo_id, asignatura_id, numero, curso_blackboard)
SELECT pe.periodo_id, a.asignatura_id, v.numero, v.curso_blackboard
FROM (VALUES ('450002', '412', 'SINTETICO_20262_450002_412'),
             ('450010', '410', 'SINTETICO_20262_450010_410'),
             ('450010', '412', 'SINTETICO_20262_450010_412')) AS v (asignatura, numero, curso_blackboard)
JOIN abet.periodo pe ON pe.codigo = '2026-2'
JOIN abet.asignatura a ON a.codigo = v.asignatura
ON CONFLICT DO NOTHING;

-- Profesor de prueba con varias secciones, activo y sin contraseña.
INSERT INTO acceso.usuario_autorizado (correo, rol)
VALUES ('docente.varias@example.invalid', 'PROFESOR')
ON CONFLICT DO NOTHING;

-- Las tres secciones que dicta. Cada fila de VALUES va en su propia línea, porque db/pruebas/correr_pruebas.sh quita la
-- de la 410 de 450010 en una copia de este archivo para probar que la comprobación final ve la asignación que falta.
INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)
SELECT u.usuario_id, s.seccion_id
FROM (VALUES ('450002', '412'),
             ('450010', '410'),
             ('450010', '412')) AS v (asignatura, numero)
JOIN acceso.usuario_autorizado u ON u.correo = 'docente.varias@example.invalid'
JOIN abet.periodo pe ON pe.codigo = '2026-2'
JOIN abet.asignatura a ON a.codigo = v.asignatura
JOIN abet.seccion s ON s.periodo_id = pe.periodo_id AND s.asignatura_id = a.asignatura_id AND s.numero = v.numero
ON CONFLICT DO NOTHING;

-- Comprobación final. Cada dato queda como lo describe la cabecera, aunque ya existiera antes. Los textos se ordenan
-- con COLLATE "C", así la comparación no depende de la configuración regional del servidor.
DO $$
DECLARE
    v_texto text;
BEGIN
    SELECT string_agg(p.codigo || ' del SO ' || p.so_numero || ' con ' || coalesce(i.nombre, 'ningún instrumento'), ', '
                      ORDER BY p.codigo COLLATE "C") INTO v_texto
    FROM abet.plan_medicion pm
    JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id AND pe.codigo = '2026-2'
    JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id AND a.codigo = '450010'
    JOIN abet.pi p ON p.pi_id = pm.pi_id
    LEFT JOIN abet.instrumento i ON i.instrumento_id = pm.instrumento_id;
    IF v_texto IS DISTINCT FROM '2.1 del SO 2 con Trabajo Integrador, 2.2 del SO 2 con Trabajo Integrador, '
                                || '5.1 del SO 5 con Trabajo Integrador' THEN
        RAISE EXCEPTION 'El plan de medición de 450010 en 2026-2 no es 2.1, 2.2 y 5.1 con Trabajo Integrador (%)',
            coalesce(v_texto, 'vacío');
    END IF;

    SELECT string_agg(a.codigo || '-' || s.numero || '=' || coalesce(s.curso_blackboard, 'sin curso'), ','
                      ORDER BY a.codigo COLLATE "C", s.numero COLLATE "C") INTO v_texto
    FROM abet.seccion s
    JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
    JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
    WHERE (a.codigo, s.numero) IN (('450002', '412'), ('450010', '410'), ('450010', '412'));
    IF v_texto IS DISTINCT FROM '450002-412=SINTETICO_20262_450002_412,450010-410=SINTETICO_20262_450010_410,'
                                || '450010-412=SINTETICO_20262_450010_412' THEN
        RAISE EXCEPTION 'La 412 de 450002 y la 410 y la 412 de 450010 en 2026-2 no tienen el curso de Blackboard esperado (%)',
            coalesce(v_texto, 'ninguna');
    END IF;

    SELECT u.rol || CASE WHEN u.activo THEN ' activo' ELSE ' inactivo' END INTO v_texto
    FROM acceso.usuario_autorizado u
    WHERE u.correo = 'docente.varias@example.invalid';
    IF v_texto IS DISTINCT FROM 'PROFESOR activo' THEN
        RAISE EXCEPTION 'docente.varias@example.invalid no es un PROFESOR activo (%)', coalesce(v_texto, 'no existe');
    END IF;

    SELECT string_agg(a.codigo || '-' || s.numero, ',' ORDER BY a.codigo COLLATE "C", s.numero COLLATE "C") INTO v_texto
    FROM acceso.docente_seccion d
    JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id AND u.correo = 'docente.varias@example.invalid'
    JOIN abet.seccion s ON s.seccion_id = d.seccion_id
    JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
    JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id;
    IF v_texto IS DISTINCT FROM '450002-412,450010-410,450010-412' THEN
        RAISE EXCEPTION 'docente.varias@example.invalid no dicta exactamente la 412 de 450002 y la 410 y la 412 de 450010 en 2026-2 (%)',
            coalesce(v_texto, 'ninguna');
    END IF;

    -- Cada una de las cinco secciones de 450002 y 450010 con curso de Blackboard tiene un solo profesor de prueba.
    SELECT string_agg(a.codigo || '-' || s.numero || '=' || u.correo, ','
                      ORDER BY a.codigo COLLATE "C", s.numero COLLATE "C", u.correo COLLATE "C") INTO v_texto
    FROM acceso.docente_seccion d
    JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
    JOIN abet.seccion s ON s.seccion_id = d.seccion_id
    JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
    JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
    WHERE (a.codigo, s.numero) IN (('450002', '410'), ('450002', '411'), ('450002', '412'),
                                   ('450010', '410'), ('450010', '412'));
    IF v_texto IS DISTINCT FROM '450002-410=docente410@example.invalid,450002-411=docente411@example.invalid,'
                                || '450002-412=docente.varias@example.invalid,450010-410=docente.varias@example.invalid,'
                                || '450010-412=docente.varias@example.invalid' THEN
        RAISE EXCEPTION 'Las secciones de 450002 y 450010 en 2026-2 no tienen solo su profesor de prueba (%)',
            coalesce(v_texto, 'ninguna');
    END IF;
    IF EXISTS (SELECT 1 FROM acceso.docente_seccion d
               JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
               WHERE u.correo = 'coordinacion@example.invalid') THEN
        RAISE EXCEPTION 'coordinacion@example.invalid tiene secciones asignadas y el coordinador ve todas sin asignación';
    END IF;
    RAISE NOTICE 'Datos de varias secciones listos (plan 2.1, 2.2 y 5.1 de 450010 y docente.varias@example.invalid en tres secciones)';
END
$$;

COMMIT;
