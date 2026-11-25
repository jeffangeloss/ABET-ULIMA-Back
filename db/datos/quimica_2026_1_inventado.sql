-- Datos inventados de Química General (5643) en 2026-1 (script de datos, no migración; spec 008, FR-002, US-75 y
-- US-86). Siembra las secciones 701, 702, 703 y 704 de 5643 en 2026-1, con el curso de Blackboard
-- SINTETICO_20261_5643_70N que declara la hoja de cada export inventado, los profesores docente701@example.invalid a
-- docente703@example.invalid con su sección, la 704 sin profesor y la coordinación del curso
-- coordinador.quimica@example.invalid con el alcance de 5643 en 2026-1 (V1_14). No registra la vigencia de IND-2026 ni
-- el plan de medición, que llegan con db/datos/plan_quimica_2026_1.sql, ni contraseñas, estudiantes o cargas.
-- Todo es inventado. Los correos terminan en @example.invalid y el archivo no trae códigos de estudiante. Las secciones
-- de la capacitación real viven fuera del repositorio (D-10).
-- Se corre con el usuario dueño de la base y la conexión directa, después de V1_12 y V1_14 y de
-- db/datos/alcance_coordinacion_ambiental.sql, y se puede repetir. Cada INSERT usa ON CONFLICT DO NOTHING, así que
-- otra corrida no duplica filas ni cambia las que ya existen, y la comprobación final detiene el script, y deshace
-- todo, si una fila existente no es la que el script espera. db/pruebas/correr_pruebas.sh lo aplica dos veces.
--
--   psql "host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=verify-full sslrootcert=system" \
--        -X -v ON_ERROR_STOP=1 -f db/datos/quimica_2026_1_inventado.sql

\set ON_ERROR_STOP 1

BEGIN;

INSERT INTO abet.seccion (periodo_id, asignatura_id, numero, curso_blackboard)
SELECT pe.periodo_id, a.asignatura_id, v.numero, v.curso_blackboard
FROM (VALUES ('701', 'SINTETICO_20261_5643_701'),
             ('702', 'SINTETICO_20261_5643_702'),
             ('703', 'SINTETICO_20261_5643_703'),
             ('704', 'SINTETICO_20261_5643_704')) AS v (numero, curso_blackboard)
JOIN abet.periodo pe ON pe.codigo = '2026-1'
JOIN abet.asignatura a ON a.codigo = '5643'
ON CONFLICT DO NOTHING;

INSERT INTO acceso.usuario_autorizado (correo, rol)
VALUES ('docente701@example.invalid', 'PROFESOR'),
       ('docente702@example.invalid', 'PROFESOR'),
       ('docente703@example.invalid', 'PROFESOR'),
       ('coordinador.quimica@example.invalid', 'COORDINADOR')
ON CONFLICT DO NOTHING;

-- Desde V1_16 (spec 010, FR-013) cada profesor lleva su nombre inventado y la coordinación queda sin nombre. Una segunda
-- corrida completa solo el nombre nulo de un usuario que ya existe y no cambia uno que ya tiene.
DO $$
BEGIN
    -- Una base anterior a V1_16 no tiene la columna nombre y solo recibe los usuarios del INSERT anterior, así que las
    -- bases de prueba que migran por partes siguen sirviendo.
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'acceso'
               AND table_name = 'usuario_autorizado' AND column_name = 'nombre') THEN
        INSERT INTO acceso.usuario_autorizado (correo, rol, nombre)
        VALUES ('docente701@example.invalid', 'PROFESOR', 'Profesor Inventado Setecientos Uno'),
               ('docente702@example.invalid', 'PROFESOR', 'Profesor Inventado Setecientos Dos'),
               ('docente703@example.invalid', 'PROFESOR', 'Profesor Inventado Setecientos Tres'),
               ('coordinador.quimica@example.invalid', 'COORDINADOR', NULL)
        ON CONFLICT (correo) DO UPDATE SET nombre = coalesce(acceso.usuario_autorizado.nombre, EXCLUDED.nombre);
    END IF;
END
$$;

-- Un profesor por sección, y la 704 queda sin profesor (SIN_PROFESOR en la ruta 17).
INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)
SELECT u.usuario_id, s.seccion_id
FROM (VALUES ('docente701@example.invalid', '701'),
             ('docente702@example.invalid', '702'),
             ('docente703@example.invalid', '703')) AS v (correo, numero)
JOIN acceso.usuario_autorizado u ON u.correo = v.correo
JOIN abet.periodo pe ON pe.codigo = '2026-1'
JOIN abet.asignatura a ON a.codigo = '5643'
JOIN abet.seccion s ON s.periodo_id = pe.periodo_id AND s.asignatura_id = a.asignatura_id AND s.numero = v.numero
ON CONFLICT DO NOTHING;

-- La coordinación del curso ve las secciones de 5643 en 2026-1 y ninguna otra (US-71).
INSERT INTO acceso.coordinacion_alcance (usuario_id, asignatura_id, periodo_id)
SELECT u.usuario_id, a.asignatura_id, pe.periodo_id
FROM acceso.usuario_autorizado u
JOIN abet.asignatura a ON a.codigo = '5643'
JOIN abet.periodo pe ON pe.codigo = '2026-1'
WHERE u.correo = 'coordinador.quimica@example.invalid'
ON CONFLICT DO NOTHING;

-- Comprobación final. Cada dato queda como lo describe la cabecera, aunque ya existiera antes.
DO $$
DECLARE
    v_texto text;
BEGIN
    SELECT string_agg(s.numero || '=' || coalesce(s.curso_blackboard, 'sin curso'), ',' ORDER BY s.numero) INTO v_texto
    FROM abet.seccion s
    JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-1'
    JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '5643'
    WHERE s.numero IN ('701', '702', '703', '704');
    IF v_texto IS DISTINCT FROM '701=SINTETICO_20261_5643_701,702=SINTETICO_20261_5643_702,'
                                || '703=SINTETICO_20261_5643_703,704=SINTETICO_20261_5643_704' THEN
        RAISE EXCEPTION 'Las secciones 701 a 704 de 5643 en 2026-1 no son las esperadas (%)', coalesce(v_texto, 'ninguna');
    END IF;

    SELECT string_agg(u.correo || '=' || u.rol || CASE WHEN u.activo THEN '' ELSE ' inactivo' END, ',' ORDER BY u.correo)
      INTO v_texto
    FROM acceso.usuario_autorizado u
    WHERE u.correo IN ('docente701@example.invalid', 'docente702@example.invalid', 'docente703@example.invalid',
                       'coordinador.quimica@example.invalid');
    IF v_texto IS DISTINCT FROM 'coordinador.quimica@example.invalid=COORDINADOR,docente701@example.invalid=PROFESOR,'
                                || 'docente702@example.invalid=PROFESOR,docente703@example.invalid=PROFESOR' THEN
        RAISE EXCEPTION 'Los usuarios de prueba de Química no tienen el rol o el estado esperados (%)', coalesce(v_texto, 'ninguno');
    END IF;

    -- Las secciones de 5643 en 2026-1 tienen solo su profesor de prueba, y la coordinación del curso no dicta ninguna.
    SELECT string_agg(s.numero || '=' || u.correo, ',' ORDER BY s.numero, u.correo) INTO v_texto
    FROM acceso.docente_seccion d
    JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
    JOIN abet.seccion s ON s.seccion_id = d.seccion_id
    JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-1'
    JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '5643'
    WHERE s.numero IN ('701', '702', '703', '704')
       OR u.correo IN ('docente701@example.invalid', 'docente702@example.invalid', 'docente703@example.invalid',
                       'coordinador.quimica@example.invalid');
    IF v_texto IS DISTINCT FROM '701=docente701@example.invalid,702=docente702@example.invalid,'
                                || '703=docente703@example.invalid' THEN
        RAISE EXCEPTION 'Las secciones 701 a 704 de 5643 en 2026-1 no tienen solo su profesor de prueba (%)',
            coalesce(v_texto, 'ninguna');
    END IF;

    SELECT string_agg(coalesce(c.codigo, a.codigo || ' en ' || pe.codigo), ',' ORDER BY ca.coordinacion_alcance_id)
      INTO v_texto
    FROM acceso.coordinacion_alcance ca
    JOIN acceso.usuario_autorizado u ON u.usuario_id = ca.usuario_id AND u.correo = 'coordinador.quimica@example.invalid'
    LEFT JOIN abet.carrera c ON c.carrera_id = ca.carrera_id
    LEFT JOIN abet.asignatura a ON a.asignatura_id = ca.asignatura_id
    LEFT JOIN abet.periodo pe ON pe.periodo_id = ca.periodo_id;
    IF v_texto IS DISTINCT FROM '5643 en 2026-1' THEN
        RAISE EXCEPTION 'coordinador.quimica@example.invalid no tiene solo el alcance de 5643 en 2026-1 (%)',
            coalesce(v_texto, 'ninguno');
    END IF;
    RAISE NOTICE 'Datos de Química General en 2026-1 listos (secciones 701 a 704 de 5643, tres profesores y la coordinación del curso)';
END
$$;

COMMIT;
