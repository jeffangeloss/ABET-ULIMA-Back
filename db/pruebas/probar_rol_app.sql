-- Pruebas del rol de la aplicación (US-02, US-04, FR-004, SC-008 y Principio VI). db/pruebas/correr_pruebas.sh las
-- corre en la base de ensayo de Neon, que repite el camino de T021 y T027. Esa base recibe V1_01 a V1_08 y las vistas,
-- la carga de datos_sinteticos.sql, V1_09, crear_rol_app.sql, guardia_datos_inventados.sql y
-- periodo_2026_2_inventado.sql, y las pruebas llegan con -v rol_app=<rol de prueba de nombre único>.
-- Cada bloque actúa como el rol con SET ROLE. PostgreSQL aplica así los permisos del rol igual que en una conexión
-- propia, y la prueba no depende de cómo autentica el servidor. Cada aserción lanza ERROR si no se cumple, y psql
-- se detiene en el primer error (ON_ERROR_STOP).
\set ON_ERROR_STOP 1
SET client_min_messages = notice;
\if :{?rol_app}
\else
    \echo 'Falta -v rol_app=<rol de prueba>.'
    DO $$ BEGIN RAISE EXCEPTION 'probar_rol_app.sql necesita la variable rol_app'; END $$;
\endif
SET prueba.rol_app = :'rol_app';

-- ---------------------------------------------------------------------------------------------
-- 1. Antecedentes y atributos del rol
-- ---------------------------------------------------------------------------------------------
-- N01. La carga de la 410, anterior a V1_09, sigue PUBLICADA con subida_por nulo y 33 mediciones (US-04).
DO $$
BEGIN
    IF (SELECT string_agg(c.estado || ':' || coalesce(CAST(c.subida_por AS text), 'nulo') || ':'
                          || (SELECT count(*) FROM abet.medicion m WHERE m.carga_id = c.carga_id), ',')
          FROM abet.carga c JOIN abet.seccion s ON s.seccion_id = c.seccion_id
         WHERE s.numero = '410') IS DISTINCT FROM 'PUBLICADA:nulo:33' THEN
        RAISE EXCEPTION 'FALLA N01: la carga de la 410 anterior a V1_09 debe seguir PUBLICADA, con subida_por nulo y 33 mediciones';
    END IF;
    RAISE NOTICE 'ok N01 la carga de la 410 anterior a V1_09 sigue PUBLICADA con subida_por nulo y 33 mediciones';
END $$;

-- N02. El rol inicia sesión y no tiene atributos de administración, membresías ni permiso para crear objetos.
DO $$
DECLARE
    v_rol text := current_setting('prueba.rol_app');
    r     record;
BEGIN
    SELECT * INTO r FROM pg_roles WHERE rolname = v_rol;
    IF NOT FOUND OR NOT r.rolcanlogin OR r.rolsuper OR r.rolbypassrls OR r.rolcreaterole OR r.rolcreatedb
       OR r.rolreplication THEN
        RAISE EXCEPTION 'FALLA N02: el rol de la aplicación debe iniciar sesión y no tener atributos de administración';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles g WHERE g.rolname <> v_rol AND pg_has_role(v_rol, g.oid, 'MEMBER'))
       OR NOT has_database_privilege(v_rol, current_database(), 'CONNECT')
       OR has_schema_privilege(v_rol, 'abet', 'CREATE') OR has_schema_privilege(v_rol, 'acceso', 'CREATE') THEN
        RAISE EXCEPTION 'FALLA N02: el rol no debe pertenecer a otro rol ni crear objetos, y debe poder conectarse';
    END IF;
    RAISE NOTICE 'ok N02 el rol inicia sesión, sin atributos de administración ni membresías';
END $$;

-- ---------------------------------------------------------------------------------------------
-- 2. Lo que el rol debe poder hacer
-- ---------------------------------------------------------------------------------------------
-- N03. Lee las vistas del R-17 y las tablas de acceso que la aplicación consulta.
BEGIN;
SET LOCAL ROLE :"rol_app";
DO $$
DECLARE
    r   record;
    v_n int := 0;
BEGIN
    IF current_user <> current_setting('prueba.rol_app') THEN
        RAISE EXCEPTION 'FALLA N03: la prueba no actúa como el rol de la aplicación';
    END IF;
    FOR r IN
        SELECT v.pi, v.n_total, v.n_esperado_o_superior, v.pct_logro_sobre_calificados, e.ok_e, e.pct_e
        FROM abet.v_r17_por_pi v
        JOIN (VALUES ('5.1', 7, 63.6), ('5.2', 7, 63.6), ('5.3', 8, 72.7)) AS e (pi_e, ok_e, pct_e) ON e.pi_e = v.pi
        WHERE v.periodo = '2026-2' AND v.codigo_asignatura = '450002' AND v.seccion = '410'
    LOOP
        v_n := v_n + 1;
        IF r.n_total <> 11 OR r.n_esperado_o_superior <> r.ok_e OR r.pct_logro_sobre_calificados <> r.pct_e THEN
            RAISE EXCEPTION 'FALLA N03: el rol lee otro R-17 de la 410 en el PI % (%)', r.pi, r;
        END IF;
    END LOOP;
    IF v_n <> 3 OR (SELECT count(*) FROM abet.v_tabla_maestra_pi WHERE "SECCIÓN" = '410') <> 33 THEN
        RAISE EXCEPTION 'FALLA N03: el rol debe ver 3 PI de la 410 en v_r17_por_pi y 33 filas en v_tabla_maestra_pi';
    END IF;
    IF (SELECT count(*) FROM acceso.usuario_autorizado) <> 3 OR (SELECT count(*) FROM acceso.docente_seccion) <> 2
       OR (SELECT count(*) FROM acceso.credencial) <> 0 OR (SELECT count(*) FROM acceso.sesion) <> 0
       OR (SELECT count(*) FROM acceso.intento_fallido) <> 0 THEN
        RAISE EXCEPTION 'FALLA N03: el rol debe leer los 3 usuarios, las 2 asignaciones y ninguna credencial, sesión ni intento fallido';
    END IF;
    RAISE NOTICE 'ok N03 el rol lee v_r17_por_pi (63,6 / 63,6 / 72,7 en la 410), v_tabla_maestra_pi y las tablas de acceso';
END $$;
COMMIT;

-- N04. Publica una carga completa de la 411 en una sola transacción, como la aplicación (US-02), con 11 estudiantes
-- inventados de 99000012 a 99000022, 11 filas, 33 mediciones y el aviso del Total Pts de 20 en el PI 5.3. Las filas
-- son las de tests/datos_inventados/export_inventado_411.xlsx, con los niveles de la 410 en orden inverso, así que su
-- R-17 da los mismos 63,6 / 63,6 / 72,7 de la 410 con otros estudiantes.
BEGIN;
SET LOCAL ROLE :"rol_app";
INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)
VALUES (encode(sha256(convert_to('export inventado 2026-2 450002 411', 'UTF8')), 'hex'),
        'export_inventado_411.xlsx', 'gc_SINTETICO_20262_450002_411_f', 11);

INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version, subida_por)
SELECT s.seccion_id, ao.archivo_id, ao.filas_de_datos, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba', u.usuario_id
FROM abet.seccion s
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002'
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'export_inventado_411.xlsx'
JOIN abet.conjunto_reglas cr ON cr.version = 'R-2026-BORRADOR'
JOIN acceso.usuario_autorizado u ON u.correo = 'docente411@example.invalid'
WHERE s.numero = '411';

INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id, pi_id,
                                pi_codigo, posicion, encabezado, bb_columna_id, puntaje_maximo_declarado)
SELECT c.carga_id, s.seccion_id, c.carrera_id, s.periodo_id, s.asignatura_id, pm.plan_medicion_id, pm.pi_id,
       p.codigo, v.posicion, v.pi || ' [Total Pts: ' || v.puntos || ' Score] |' || v.bb_id, v.bb_id, v.puntos
FROM (VALUES ('5.1', 5, '9000051', 4), ('5.2', 6, '9000052', 4), ('5.3', 7, '9000053', 20))
     AS v (pi, posicion, bb_id, puntos)
JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'export_inventado_411.xlsx'
JOIN abet.carga c ON c.archivo_id = ao.archivo_id
JOIN abet.seccion s ON s.seccion_id = c.seccion_id
JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
                          AND pm.carrera_id = c.carrera_id
JOIN abet.pi p ON p.pi_id = pm.pi_id AND p.codigo = v.pi;

INSERT INTO abet.rechazo_fila (carga_id, fila_origen, carga_columna_id, motivo, efecto)
SELECT cc.carga_id, NULL, cc.carga_columna_id, 'PUNTAJE_MAXIMO_DISTINTO', 'AVISO'
FROM abet.carga_columna cc
JOIN abet.carga c ON c.carga_id = cc.carga_id
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'export_inventado_411.xlsx'
WHERE cc.pi_codigo = '5.3';

INSERT INTO abet.estudiante (codigo)
SELECT CAST(99000000 + n AS varchar(8)) FROM generate_series(12, 22) AS g (n);

-- 99000012 está en la fila 2 y 99000022 en la fila 12.
INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id)
SELECT c.carga_id, CAST(e.codigo AS integer) - 99000010, e.estudiante_id
FROM abet.estudiante e
JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'export_inventado_411.xlsx'
JOIN abet.carga c ON c.archivo_id = ao.archivo_id
WHERE e.codigo BETWEEN '99000012' AND '99000022';

-- Niveles por fila (5.1, 5.2, 5.3) de export_inventado_411.xlsx. 99000012 lleva los de 99000011 y 99000022 los de
-- 99000001, así que en nivel 3 o más quedan 7, 7 y 8 de 11 estudiantes.
INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
SELECT cc.carga_id, cc.carga_columna_id, cc.pi_id, f.estudiante_id, 'CALIFICADO',
       CASE cc.pi_codigo WHEN '5.1' THEN v.n51 WHEN '5.2' THEN v.n52 ELSE v.n53 END, f.fila_origen
FROM (VALUES
 ( 2, 2, 2, 2),
 ( 3, 3, 4, 3),
 ( 4, 4, 3, 4),
 ( 5, 2, 1, 1),
 ( 6, 3, 4, 3),
 ( 7, 4, 3, 4),
 ( 8, 1, 2, 2),
 ( 9, 3, 2, 3),
 (10, 2, 3, 3),
 (11, 4, 3, 4),
 (12, 3, 4, 3)
) AS v (fila, n51, n52, n53)
JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'export_inventado_411.xlsx'
JOIN abet.carga c ON c.archivo_id = ao.archivo_id
JOIN abet.carga_fila f ON f.carga_id = c.carga_id AND f.fila_origen = v.fila
JOIN abet.carga_columna cc ON cc.carga_id = c.carga_id;

UPDATE abet.carga c
SET estado = 'PUBLICADA', filas_leidas = 11, filas_aceptadas = 11, filas_rechazadas = 0, terminada_en = clock_timestamp()
FROM abet.archivo_origen ao
WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'export_inventado_411.xlsx';
COMMIT;

BEGIN;
SET LOCAL ROLE :"rol_app";
DO $$
DECLARE
    r   record;
    v_n int := 0;
BEGIN
    FOR r IN
        SELECT v.pi, v.n_total, v.n_esperado_o_superior, v.pct_logro_sobre_calificados, v.provisional,
               v.n_nivel_1, v.n_nivel_2, v.n_nivel_3, v.n_nivel_4, e.*
        FROM abet.v_r17_por_pi v
        JOIN (VALUES ('5.1', 7, 63.6, 1, 3, 4, 3), ('5.2', 7, 63.6, 1, 3, 4, 3), ('5.3', 8, 72.7, 1, 2, 5, 3))
             AS e (pi_e, ok_e, pct_e, n1_e, n2_e, n3_e, n4_e) ON e.pi_e = v.pi
        WHERE v.periodo = '2026-2' AND v.codigo_asignatura = '450002' AND v.seccion = '411'
    LOOP
        v_n := v_n + 1;
        IF r.n_total <> 11 OR r.n_esperado_o_superior <> r.ok_e OR r.pct_logro_sobre_calificados <> r.pct_e
           OR r.provisional IS NOT TRUE
           OR (r.n_nivel_1, r.n_nivel_2, r.n_nivel_3, r.n_nivel_4) IS DISTINCT FROM (r.n1_e, r.n2_e, r.n3_e, r.n4_e) THEN
            RAISE EXCEPTION 'FALLA N04: R-17 de la 411 en el PI % (%)', r.pi, r;
        END IF;
    END LOOP;
    IF v_n <> 3 OR (SELECT count(*) FROM abet.v_tabla_maestra_pi WHERE "SECCIÓN" = '411') <> 33 THEN
        RAISE EXCEPTION 'FALLA N04: la 411 debe tener 3 PI en v_r17_por_pi y 33 filas en v_tabla_maestra_pi';
    END IF;
    -- Mismos porcentajes que la 410, así que la separación por sección se mira en los códigos de cada una.
    IF (SELECT min("CÓDIGO DEL ESTUDIANTE") || '-' || max("CÓDIGO DEL ESTUDIANTE") || ':'
               || count(DISTINCT "CÓDIGO DEL ESTUDIANTE")
          FROM abet.v_tabla_maestra_pi WHERE "SECCIÓN" = '411') IS DISTINCT FROM '99000012-99000022:11'
       OR (SELECT min("CÓDIGO DEL ESTUDIANTE") || '-' || max("CÓDIGO DEL ESTUDIANTE") || ':'
                  || count(DISTINCT "CÓDIGO DEL ESTUDIANTE")
             FROM abet.v_tabla_maestra_pi WHERE "SECCIÓN" = '410') IS DISTINCT FROM '99000001-99000011:11' THEN
        RAISE EXCEPTION 'FALLA N04: la tabla maestra debe llevar 99000012 a 99000022 en la 411 y 99000001 a 99000011 en la 410';
    END IF;
    IF (SELECT c.estado || ' ' || c.filas_leidas || '/' || c.filas_aceptadas || '/' || c.filas_rechazadas || ' ' || u.correo
          FROM abet.carga c
          JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'export_inventado_411.xlsx'
          JOIN acceso.usuario_autorizado u ON u.usuario_id = c.subida_por)
       IS DISTINCT FROM 'PUBLICADA 11/11/0 docente411@example.invalid' THEN
        RAISE EXCEPTION 'FALLA N04: la carga de la 411 debe quedar PUBLICADA con 11 / 11 / 0 y subida por docente411';
    END IF;
    -- Q08 con la 410 y la 411 publicadas, sin ningún estudiante en las dos secciones.
    IF EXISTS (SELECT m.estudiante_id, m.pi_id, s.periodo_id, s.asignatura_id
                 FROM abet.medicion m JOIN abet.carga c ON c.carga_id = m.carga_id
                 JOIN abet.seccion s ON s.seccion_id = c.seccion_id
                WHERE c.estado = 'PUBLICADA'
                GROUP BY m.estudiante_id, m.pi_id, s.periodo_id, s.asignatura_id
               HAVING count(DISTINCT s.seccion_id) > 1) THEN
        RAISE EXCEPTION 'FALLA N04: Q08 ve un estudiante en la 410 y en la 411';
    END IF;
    RAISE NOTICE 'ok N04 el rol publica la carga de la 411 en una transacción (11 / 11 / 0, 33 mediciones, 63,6 / 63,6 / 72,7 con 99000012 a 99000022) y Q08 sigue en 0 filas';
END $$;
COMMIT;

-- N05. Reconoce un estudiante que ya existe sin error, con INSERT ... ON CONFLICT DO NOTHING.
BEGIN;
SET LOCAL ROLE :"rol_app";
INSERT INTO abet.estudiante (codigo) VALUES ('99000012') ON CONFLICT (codigo) DO NOTHING;
DO $$
BEGIN
    IF (SELECT count(*) FROM abet.estudiante WHERE codigo = '99000012') <> 1 THEN
        RAISE EXCEPTION 'FALLA N05: el estudiante existente debe seguir con una sola fila';
    END IF;
    RAISE NOTICE 'ok N05 el rol reutiliza un estudiante existente con ON CONFLICT DO NOTHING';
END $$;
ROLLBACK;

-- N06. Registra intentos fallidos y abre y cierra sesiones (US-05). El dueño de la base crea la credencial, como el
-- comando de asignar contraseña, y una sesión ya vencida, cuyas fechas el rol no puede escribir. El hash Argon2id es
-- inventado y no corresponde a ninguna contraseña, y el hash de cada correo es un SHA-256 sin secreto que solo imita
-- el formato del código de autenticación de mensajes basado en hash (hash-based message authentication code, HMAC)
-- que calcula la aplicación.
BEGIN;
INSERT INTO acceso.credencial (usuario_id, hash_clave)
SELECT usuario_id, '$argon2id$v=19$m=65536,t=3,p=4$cHJ1ZWJh$cHJ1ZWJh'
FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid';
INSERT INTO acceso.sesion (usuario_id, hash_token, creada_en, expira_en)
SELECT usuario_id, encode(sha256(convert_to('sesion vencida N06', 'UTF8')), 'hex'),
       now() - interval '13 hours', now() - interval '1 hour'
FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid';
SET LOCAL ROLE :"rol_app";
-- Cinco intentos con el correo de docente410, que tiene credencial, y cinco con un correo que no existe.
INSERT INTO acceso.intento_fallido (hash_cuenta)
SELECT encode(sha256(convert_to(v.correo, 'UTF8')), 'hex')
FROM (VALUES ('docente410@example.invalid'), ('desconocido@example.invalid')) AS v (correo), generate_series(1, 5);
-- Una sesión nueva y el cierre del COMMENT de acceso.sesion.expira_en sobre ella y sobre la vencida.
INSERT INTO acceso.sesion (usuario_id, hash_token)
SELECT usuario_id, encode(sha256(convert_to('sesion de prueba N06', 'UTF8')), 'hex')
FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid';
UPDATE acceso.sesion SET expira_en = least(expira_en, clock_timestamp())
WHERE hash_token IN (encode(sha256(convert_to('sesion de prueba N06', 'UTF8')), 'hex'),
                     encode(sha256(convert_to('sesion vencida N06', 'UTF8')), 'hex'));
DO $$
DECLARE
    v_estado      text;
    v_restriccion text;
BEGIN
    -- Los dos correos suman 5 intentos en los últimos 15 minutos, así que la API responde igual a los dos.
    IF (SELECT string_agg(v.correo || '=' || (SELECT count(*) FROM acceso.intento_fallido i
                                               WHERE i.hash_cuenta = encode(sha256(convert_to(v.correo, 'UTF8')), 'hex')
                                                 AND i.intentado_en > now() - interval '15 minutes'),
                          ',' ORDER BY v.correo)
          FROM (VALUES ('docente410@example.invalid'), ('desconocido@example.invalid')) AS v (correo))
       IS DISTINCT FROM 'desconocido@example.invalid=5,docente410@example.invalid=5' THEN
        RAISE EXCEPTION 'FALLA N06: los dos correos deben quedar con 5 intentos fallidos en los últimos 15 minutos';
    END IF;
    -- La sesión nueva vence a la hora del cierre, la vencida conserva su vencimiento y las dos siguen en la tabla.
    IF (SELECT count(*) FROM acceso.sesion WHERE expira_en <= clock_timestamp() AND expira_en > creada_en) <> 2
       OR (SELECT expira_en FROM acceso.sesion
            WHERE hash_token = encode(sha256(convert_to('sesion vencida N06', 'UTF8')), 'hex'))
          IS DISTINCT FROM now() - interval '1 hour'
       OR (SELECT count(*) FROM acceso.credencial) <> 1 THEN
        RAISE EXCEPTION 'FALLA N06: el cierre debe vencer la sesión nueva, dejar igual la vencida y no borrar ninguna';
    END IF;
    -- Sin least(), el cierre de la sesión vencida pasa el tope de 12 horas y ck_sesion_vigencia lo rechaza.
    BEGIN
        UPDATE acceso.sesion SET expira_en = clock_timestamp()
        WHERE hash_token = encode(sha256(convert_to('sesion vencida N06', 'UTF8')), 'hex');
    EXCEPTION WHEN others THEN
        GET STACKED DIAGNOSTICS v_estado = RETURNED_SQLSTATE, v_restriccion = CONSTRAINT_NAME;
    END;
    IF v_estado IS DISTINCT FROM '23514' OR v_restriccion IS DISTINCT FROM 'ck_sesion_vigencia' THEN
        RAISE EXCEPTION 'FALLA N06: el cierre sin least() de una sesión vencida terminó con % (%) y no con ck_sesion_vigencia',
            coalesce(v_estado, 'aceptado'), v_restriccion;
    END IF;
    RAISE NOTICE 'ok N06 el rol registra 5 intentos de un correo autorizado y 5 de uno desconocido, abre una sesión y la cierra con least() sin borrarla, y la sesión vencida queda igual';
END $$;
ROLLBACK;

-- N07. Registra dos cargas RECHAZADAS de la 410, una por PI_DEL_PLAN_AUSENTE con el PI 5.2 que falta y otra por
-- PI_REPETIDO con el PI 5.1 que se repite, como la aplicación (US-12 y FR-016). Cada carga entra EN_CURSO, recibe su
-- único rechazo con el pi_id del plan de la sección y se cierra con el UPDATE de estado y terminada_en, sin columnas
-- ni filas. La base le rechaza además al rol un pi_id en un CODIGO_VACIO, con ck_rechazo_fila_pi.
BEGIN;
SET LOCAL ROLE :"rol_app";
INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)
VALUES (encode(sha256(convert_to('rol N07 sin 5.2', 'UTF8')), 'hex'), 'rol_sin_5_2.xlsx', 'Hoja1', 11),
       (encode(sha256(convert_to('rol N07 5.1 repetido', 'UTF8')), 'hex'), 'rol_5_1_repetido.xlsx', 'Hoja1', 11);

INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version, subida_por)
SELECT s.seccion_id, ao.archivo_id, ao.filas_de_datos, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba', u.usuario_id
FROM abet.seccion s
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002'
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
JOIN abet.archivo_origen ao ON ao.nombre_archivo IN ('rol_sin_5_2.xlsx', 'rol_5_1_repetido.xlsx')
JOIN abet.conjunto_reglas cr ON cr.version = 'R-2026-BORRADOR'
JOIN acceso.usuario_autorizado u ON u.correo = 'docente410@example.invalid'
WHERE s.numero = '410';

INSERT INTO abet.rechazo_fila (carga_id, fila_origen, motivo, efecto, pi_id)
SELECT c.carga_id, NULL, v.motivo, 'RECHAZA_CARGA', pm.pi_id
FROM (VALUES ('rol_sin_5_2.xlsx', 'PI_DEL_PLAN_AUSENTE', '5.2'), ('rol_5_1_repetido.xlsx', 'PI_REPETIDO', '5.1'))
     AS v (archivo, motivo, pi)
JOIN abet.archivo_origen ao ON ao.nombre_archivo = v.archivo
JOIN abet.carga c ON c.archivo_id = ao.archivo_id
JOIN abet.seccion s ON s.seccion_id = c.seccion_id
JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
                          AND pm.carrera_id = c.carrera_id
JOIN abet.pi p ON p.pi_id = pm.pi_id AND p.codigo = v.pi;

UPDATE abet.carga c SET estado = 'RECHAZADA', terminada_en = clock_timestamp()
FROM abet.archivo_origen ao
WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo IN ('rol_sin_5_2.xlsx', 'rol_5_1_repetido.xlsx');

DO $$
DECLARE
    v_estado      text;
    v_restriccion text;
BEGIN
    IF current_user <> current_setting('prueba.rol_app') THEN
        RAISE EXCEPTION 'FALLA N07: la prueba no actúa como el rol de la aplicación';
    END IF;
    IF (SELECT string_agg(c.estado || ':' || c.filas_leidas || ':' || r.motivo || ':' || r.efecto || ':' || p.codigo
                          || ':' || u.correo, ',' ORDER BY r.motivo)
          FROM abet.rechazo_fila r
          JOIN abet.carga c ON c.carga_id = r.carga_id
          JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
               AND ao.nombre_archivo IN ('rol_sin_5_2.xlsx', 'rol_5_1_repetido.xlsx')
          JOIN abet.pi p ON p.pi_id = r.pi_id
          JOIN acceso.usuario_autorizado u ON u.usuario_id = c.subida_por)
       IS DISTINCT FROM 'RECHAZADA:0:PI_DEL_PLAN_AUSENTE:RECHAZA_CARGA:5.2:docente410@example.invalid,'
                        || 'RECHAZADA:0:PI_REPETIDO:RECHAZA_CARGA:5.1:docente410@example.invalid'
       OR EXISTS (SELECT 1 FROM abet.carga_columna cc JOIN abet.carga c ON c.carga_id = cc.carga_id
                    JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
                   WHERE ao.nombre_archivo IN ('rol_sin_5_2.xlsx', 'rol_5_1_repetido.xlsx')) THEN
        RAISE EXCEPTION 'FALLA N07: el rol debe dejar las dos cargas RECHAZADAS de la 410 con el PI 5.2 y el 5.1 en pi_id y sin columnas';
    END IF;
    BEGIN
        INSERT INTO abet.rechazo_fila (carga_id, fila_origen, motivo, efecto, pi_id)
        SELECT r.carga_id, 2, 'CODIGO_VACIO', 'RECHAZA_FILA', r.pi_id
        FROM abet.rechazo_fila r JOIN abet.carga c ON c.carga_id = r.carga_id
        JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'rol_sin_5_2.xlsx';
    EXCEPTION WHEN others THEN
        GET STACKED DIAGNOSTICS v_estado = RETURNED_SQLSTATE, v_restriccion = CONSTRAINT_NAME;
    END;
    IF v_estado IS DISTINCT FROM '23514' OR v_restriccion IS DISTINCT FROM 'ck_rechazo_fila_pi' THEN
        RAISE EXCEPTION 'FALLA N07: el CODIGO_VACIO con pi_id del rol terminó con % (%) y no con ck_rechazo_fila_pi',
            coalesce(v_estado, 'aceptado'), v_restriccion;
    END IF;
    RAISE NOTICE 'ok N07 el rol registra PI_DEL_PLAN_AUSENTE con el PI 5.2 y PI_REPETIDO con el 5.1 del plan en dos cargas RECHAZADAS de la 410, y la base le rechaza un pi_id en un CODIGO_VACIO';
END $$;
ROLLBACK;

-- ---------------------------------------------------------------------------------------------
-- 3. Lo que el rol no debe poder hacer (SC-008)
-- ---------------------------------------------------------------------------------------------
-- N08. Cada sentencia recibe «permission denied» (42501) con el nombre de su tabla o esquema en el mensaje, y la
-- base queda igual. Los ejemplos son los de base_neon.feature más los de credencial, sesion, intento_fallido,
-- codigo_acceso, rechazo_fila y CREATE TABLE, entre ellos una sesión y un intento con fechas que elige el rol y el
-- cambio del PI de un rechazo ya registrado. Se comprueba el SQLSTATE y el nombre del objeto porque el resto del
-- mensaje depende del idioma del servidor.
BEGIN;
SET LOCAL ROLE :"rol_app";
DO $$
DECLARE
    c          record;
    v_estado   text;
    v_mensaje  text;
    v_antes    text;
    v_despues  text;
    v_ok       int := 0;
    v_total    int := 0;
    v_foto     text := $f$
        SELECT (SELECT string_agg(c.carga_id || ':' || c.estado || ':' || c.conjunto_reglas_id || ':'
                                  || coalesce(CAST(c.subida_por AS text), 'nulo') || ':' || c.archivo_id || ':'
                                  || c.seccion_id || ':' || coalesce(CAST(c.reemplaza_carga_id AS text), 'nulo'),
                                  ',' ORDER BY c.carga_id) FROM abet.carga c)
            || '|' || (SELECT count(*) FROM abet.medicion m JOIN abet.carga c ON c.carga_id = m.carga_id
                        JOIN abet.seccion s ON s.seccion_id = c.seccion_id WHERE s.numero = '410')
            || '|' || (SELECT count(*) FROM abet.medicion) || '|' || (SELECT count(*) FROM abet.carga_fila)
            || '|' || (SELECT count(*) FROM abet.archivo_origen) || '|' || (SELECT count(*) FROM abet.rechazo_fila)
            || '|' || (SELECT count(*) FROM abet.estudiante)
            || '|' || (SELECT string_agg(cr.version || ':' || cr.estado, ',' ORDER BY cr.version) FROM abet.conjunto_reglas cr)
            || '|' || (SELECT string_agg(pv.clave || ':' || pv.estado || ':' || coalesce(CAST(pv.valor_numero AS text), '-'),
                                         ',' ORDER BY pv.clave) FROM abet.parametro_valor pv)
            || '|' || (SELECT string_agg(cv.codigo || ':' || cv.estado, ',') FROM abet.catalogo_version cv)
            || '|' || (SELECT count(*) FROM abet.catalogo_vigencia) || '|' || (SELECT count(*) FROM abet.plan_medicion)
            || '|' || (SELECT string_agg(s.numero || ':' || coalesce(s.curso_blackboard, '-'), ',' ORDER BY s.numero) FROM abet.seccion s)
            || '|' || (SELECT string_agg(u.correo || ':' || u.rol || ':' || u.activo, ',' ORDER BY u.correo) FROM acceso.usuario_autorizado u)
            || '|' || (SELECT count(*) FROM acceso.docente_seccion) || '|' || (SELECT count(*) FROM acceso.credencial)
            || '|' || (SELECT count(*) FROM acceso.sesion) || '|' || (SELECT count(*) FROM acceso.intento_fallido)
    $f$;
BEGIN
    EXECUTE v_foto INTO v_antes;
    FOR c IN SELECT * FROM (VALUES
        ('P01', 'DELETE FROM abet.medicion', 'medicion'),
        ('P02', 'DELETE FROM abet.carga_fila', 'carga_fila'),
        ('P03', 'DELETE FROM abet.carga', 'carga'),
        ('P04', 'DELETE FROM abet.archivo_origen', 'archivo_origen'),
        ('P05', 'DELETE FROM abet.rechazo_fila', 'rechazo_fila'),
        ('P06', 'DELETE FROM abet.estudiante', 'estudiante'),
        ('P07', 'TRUNCATE abet.medicion', 'medicion'),
        ('P08', 'TRUNCATE abet.carga', 'carga'),
        ('P09', $q$UPDATE abet.carga SET conjunto_reglas_id = conjunto_reglas_id
                   WHERE seccion_id = (SELECT seccion_id FROM abet.seccion WHERE numero = '410')$q$, 'carga'),
        ('P10', $q$UPDATE abet.carga SET subida_por = (SELECT usuario_id FROM acceso.usuario_autorizado
                                                      WHERE correo = 'docente411@example.invalid')
                   WHERE seccion_id = (SELECT seccion_id FROM abet.seccion WHERE numero = '410')$q$, 'carga'),
        ('P11', $q$UPDATE abet.carga SET archivo_id = (SELECT archivo_id FROM abet.archivo_origen
                                                      WHERE nombre_archivo = 'export_inventado_411.xlsx')
                   WHERE seccion_id = (SELECT seccion_id FROM abet.seccion WHERE numero = '410')$q$, 'carga'),
        ('P12', $q$UPDATE abet.carga SET seccion_id = (SELECT seccion_id FROM abet.seccion WHERE numero = '411')
                   WHERE seccion_id = (SELECT seccion_id FROM abet.seccion WHERE numero = '410')$q$, 'carga'),
        ('P13', $q$UPDATE abet.carga SET reemplaza_carga_id = (SELECT min(carga_id) FROM abet.carga)
                   WHERE seccion_id = (SELECT seccion_id FROM abet.seccion WHERE numero = '411')$q$, 'carga'),
        ('P14', $q$UPDATE abet.conjunto_reglas SET estado = 'APROBADO', aprobado_por = 'Prueba', aprobado_en = current_date$q$,
                'conjunto_reglas'),
        ('P15', $q$INSERT INTO abet.conjunto_reglas (carrera_id, version)
                   SELECT carrera_id, 'R-PRUEBA-APP' FROM abet.carrera WHERE codigo = 'AMB'$q$, 'conjunto_reglas'),
        ('P16', $q$UPDATE abet.parametro_valor SET valor_numero = 0.5 WHERE clave = 'META_LOGRO'$q$, 'parametro_valor'),
        ('P17', $q$INSERT INTO abet.parametro_valor (conjunto_reglas_id, clave, estado)
                   SELECT conjunto_reglas_id, 'CORTE_ROJO', 'PENDIENTE' FROM abet.conjunto_reglas$q$, 'parametro_valor'),
        ('P18', $q$UPDATE abet.catalogo_version SET estado = 'BORRADOR'$q$, 'catalogo_version'),
        ('P19', $q$INSERT INTO abet.catalogo_vigencia (periodo_id, carrera_id, catalogo_version_id)
                   SELECT pe.periodo_id, cv.carrera_id, cv.catalogo_version_id
                   FROM abet.periodo pe, abet.catalogo_version cv WHERE pe.codigo = '2026-1'$q$, 'catalogo_vigencia'),
        ('P20', $q$INSERT INTO abet.plan_medicion (periodo_id, asignatura_id, carrera_id, catalogo_version_id, so_id, pi_id)
                   SELECT periodo_id, asignatura_id, carrera_id, catalogo_version_id, so_id, pi_id
                   FROM abet.plan_medicion$q$, 'plan_medicion'),
        ('P21', $q$UPDATE abet.seccion SET curso_blackboard = NULL WHERE numero = '411'$q$, 'seccion'),
        ('P22', 'DELETE FROM acceso.usuario_autorizado', 'usuario_autorizado'),
        ('P23', 'DELETE FROM acceso.sesion', 'sesion'),
        ('P24', 'DELETE FROM acceso.credencial', 'credencial'),
        ('P25', 'DELETE FROM acceso.docente_seccion', 'docente_seccion'),
        ('P26', $q$INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES ('nuevo@example.invalid', 'PROFESOR')$q$,
                'usuario_autorizado'),
        ('P27', $q$UPDATE acceso.usuario_autorizado SET rol = 'COORDINADOR' WHERE correo = 'docente410@example.invalid'$q$,
                'usuario_autorizado'),
        ('P28', $q$INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)
                   SELECT u.usuario_id, s.seccion_id FROM acceso.usuario_autorizado u, abet.seccion s
                   WHERE u.correo = 'docente410@example.invalid' AND s.numero = '411'$q$, 'docente_seccion'),
        ('P29', $q$UPDATE acceso.usuario_autorizado SET activo = true$q$, 'usuario_autorizado'),
        ('P30', $q$UPDATE acceso.credencial SET hash_clave = hash_clave$q$, 'credencial'),
        ('P31', $q$INSERT INTO acceso.credencial (usuario_id, hash_clave)
                   SELECT usuario_id, hash_clave FROM acceso.credencial$q$, 'credencial'),
        ('P32', $q$UPDATE acceso.sesion SET usuario_id = usuario_id$q$, 'sesion'),
        ('P33', 'TRUNCATE acceso.sesion', 'sesion'),
        ('P34', $q$INSERT INTO acceso.codigo_acceso (usuario_id, hash_codigo)
                   SELECT usuario_id, repeat('a', 64) FROM acceso.usuario_autorizado$q$, 'codigo_acceso'),
        ('P35', 'SELECT count(*) FROM acceso.codigo_acceso', 'codigo_acceso'),
        ('P36', 'CREATE TABLE abet.tabla_del_rol (x integer)', 'abet'),
        ('P37', 'CREATE TABLE acceso.tabla_del_rol (x integer)', 'acceso'),
        ('P38', $q$INSERT INTO acceso.sesion (usuario_id, hash_token, creada_en, expira_en)
                   SELECT usuario_id, encode(sha256(convert_to('sesion futura', 'UTF8')), 'hex'),
                          now() + interval '50 years', now() + interval '50 years 12 hours'
                   FROM acceso.usuario_autorizado WHERE correo = 'coordinacion@example.invalid'$q$, 'sesion'),
        ('P39', $q$INSERT INTO acceso.sesion (usuario_id, hash_token, expira_en)
                   SELECT usuario_id, encode(sha256(convert_to('sesion con vencimiento propio', 'UTF8')), 'hex'),
                          now() + interval '1 hour'
                   FROM acceso.usuario_autorizado WHERE correo = 'coordinacion@example.invalid'$q$, 'sesion'),
        ('P40', $q$INSERT INTO acceso.intento_fallido (hash_cuenta, intentado_en)
                   VALUES (repeat('b', 64), now() - interval '1 hour')$q$, 'intento_fallido'),
        ('P41', $q$UPDATE acceso.intento_fallido SET intentado_en = now() - interval '1 hour'$q$, 'intento_fallido'),
        ('P42', 'DELETE FROM acceso.intento_fallido', 'intento_fallido'),
        ('P43', 'UPDATE abet.rechazo_fila SET pi_id = NULL', 'rechazo_fila')
    ) AS t (id, sentencia, objeto) ORDER BY id LOOP
        v_total := v_total + 1;
        v_estado := NULL;
        v_mensaje := NULL;
        BEGIN
            EXECUTE c.sentencia;
        EXCEPTION WHEN others THEN
            GET STACKED DIAGNOSTICS v_estado = RETURNED_SQLSTATE, v_mensaje = MESSAGE_TEXT;
        END;
        IF v_estado IS NULL THEN
            RAISE EXCEPTION 'FALLA %: el rol de la aplicación pudo ejecutar %', c.id, c.sentencia;
        ELSIF v_estado <> '42501' OR position(c.objeto IN v_mensaje) = 0 THEN
            RAISE EXCEPTION 'FALLA %: se esperaba permission denied sobre % y PostgreSQL respondió % (%)',
                c.id, c.objeto, v_estado, v_mensaje;
        END IF;
        v_ok := v_ok + 1;
        RAISE NOTICE 'ok % denegado al rol: % (%)', c.id, regexp_replace(c.sentencia, '\s+', ' ', 'g'), v_mensaje;
    END LOOP;
    EXECUTE v_foto INTO v_despues;
    IF v_despues IS DISTINCT FROM v_antes THEN
        RAISE EXCEPTION 'FALLA N08: la base cambió después de las sentencias denegadas';
    END IF;
    RAISE NOTICE 'ok N08 %/% sentencias denegadas al rol y la base sin cambios (la 410 sigue con 33 mediciones)', v_ok, v_total;
END $$;
ROLLBACK;

\echo 'ROL DE LA APLICACIÓN: TODAS LAS PRUEBAS PASARON'
