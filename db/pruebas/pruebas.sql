-- Pruebas de la base. Se corren sobre una base desechable con las migraciones, los datos sintéticos, los datos de
-- 2026-2 de db/datos/periodo_2026_2_inventado.sql y los del profesor con varias secciones de
-- db/datos/varias_secciones_2026_2_inventado.sql. correr_pruebas.sh aplica dos veces cada script de datos, en ese orden,
-- después de los sintéticos.
-- Cada aserción lanza ERROR si no se cumple; psql se detiene en el primer error (ON_ERROR_STOP).
-- Los bloques DO de este archivo son el arnés de pruebas y no forman parte del esquema.
\set ON_ERROR_STOP 1
SET client_min_messages = notice;

-- ---------------------------------------------------------------------------------------------
-- 1. Catálogo cargado por V1_03
-- ---------------------------------------------------------------------------------------------
DO $$
DECLARE
    v_esperado int;
    v_real     int;
    v_tabla    text;
BEGIN
    FOR v_tabla, v_esperado, v_real IN
        SELECT 'so', 7, count(*) FROM abet.so
        UNION ALL SELECT 'pi', 17, count(*) FROM abet.pi
        UNION ALL SELECT 'rubrica_nivel', 102, count(*) FROM abet.rubrica_nivel
        UNION ALL SELECT 'competencia', 11, count(*) FROM abet.competencia
        UNION ALL SELECT 'competencia_so', 7, count(*) FROM abet.competencia_so
        UNION ALL SELECT 'asignatura', 53, count(*) FROM abet.asignatura
        UNION ALL SELECT 'plan_estudios', 53, count(*) FROM abet.plan_estudios
        UNION ALL SELECT 'asignatura_so', 61, count(*) FROM abet.asignatura_so
        UNION ALL SELECT 'asignatura_so sin instrumento', 10, count(*) FROM abet.asignatura_so WHERE instrumento_id IS NULL
        UNION ALL SELECT 'asignatura_competencia', 95, count(*) FROM abet.asignatura_competencia
        UNION ALL SELECT 'asignatura de 4 dígitos', 6, count(*) FROM abet.asignatura WHERE length(codigo) = 4
    LOOP
        IF v_real <> v_esperado THEN
            RAISE EXCEPTION 'FALLA catálogo: % tiene % filas y se esperaban %', v_tabla, v_real, v_esperado;
        END IF;
    END LOOP;
    IF (SELECT string_agg(k.codigo, ',' ORDER BY k.codigo)
          FROM abet.competencia k
         WHERE NOT EXISTS (SELECT 1 FROM abet.competencia_so x WHERE x.competencia_id = k.competencia_id))
       IS DISTINCT FROM 'G1,G2,G5,G7' THEN
        RAISE EXCEPTION 'FALLA catálogo: las competencias sin SO deben ser G1, G2, G5 y G7';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM abet.pi WHERE codigo = '6.1') OR EXISTS (SELECT 1 FROM abet.pi WHERE codigo = '6.10') THEN
        RAISE EXCEPTION 'FALLA catálogo: 6.1 debe existir y 6.10 no';
    END IF;
    IF (SELECT huella_fuente FROM abet.catalogo_version WHERE codigo = 'AMB-2026') !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION 'FALLA catálogo: AMB-2026 sin huella SHA-256';
    END IF;
    RAISE NOTICE 'ok C01 catálogo AMB-2026 con los conteos de la referencia';
END $$;

-- ---------------------------------------------------------------------------------------------
-- 2. Casos que deben aceptarse
-- ---------------------------------------------------------------------------------------------
-- A01. La misma sección 301 en dos asignaturas distintas del mismo periodo.
INSERT INTO abet.seccion (periodo_id, asignatura_id, numero)
SELECT pe.periodo_id, a.asignatura_id, '301'
FROM abet.periodo pe, abet.asignatura a
WHERE pe.codigo = '2026-2' AND a.codigo IN ('450002', '450020');

DO $$
BEGIN
    IF (SELECT count(*) FROM abet.seccion WHERE numero = '301') <> 2 THEN
        RAISE EXCEPTION 'FALLA A01: se esperaban dos secciones 301';
    END IF;
    RAISE NOTICE 'ok A01 sección 301 en dos asignaturas distintas';
END $$;

-- A02. Reemplazo de una carga publicada en 450020-301 (PI 1.1, tres estudiantes inventados).
BEGIN;
INSERT INTO abet.archivo_origen (sha256, nombre_archivo, filas_de_datos)
VALUES (encode(sha256(convert_to('sintetico 450020 301 primera', 'UTF8')), 'hex'), 'sintetico_450020_301_v1.csv', 3),
       (encode(sha256(convert_to('sintetico 450020 301 segunda', 'UTF8')), 'hex'), 'sintetico_450020_301_v2.csv', 3);

INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version)
SELECT s.seccion_id, ao.archivo_id, ao.filas_de_datos, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba'
FROM abet.seccion s
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450020'
JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'sintetico_450020_301_v1.csv'
JOIN abet.conjunto_reglas cr ON cr.version = 'R-2026-BORRADOR'
WHERE s.numero = '301';

INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id, pi_id,
                                pi_codigo, posicion, encabezado, bb_columna_id, puntaje_maximo_declarado)
SELECT c.carga_id, s.seccion_id, c.carrera_id, s.periodo_id, s.asignatura_id, pm.plan_medicion_id, pm.pi_id,
       '1.1', 5, '1.1 [Total Pts: 4 Score] |9000011', '9000011', 4
FROM abet.carga c
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_450020_301_v1.csv'
JOIN abet.seccion s ON s.seccion_id = c.seccion_id
JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id;

INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id)
SELECT c.carga_id, v.fila, e.estudiante_id
FROM (VALUES ('99000001', 2), ('99000002', 3), ('99000003', 4)) AS v (codigo, fila)
JOIN abet.estudiante e ON e.codigo = v.codigo
JOIN abet.carga c ON true
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_450020_301_v1.csv';

INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
SELECT cc.carga_id, cc.carga_columna_id, cc.pi_id, e.estudiante_id, 'CALIFICADO', v.nivel, v.fila
FROM (VALUES ('99000001', 2, 4), ('99000002', 3, 2), ('99000003', 4, 3)) AS v (codigo, fila, nivel)
JOIN abet.estudiante e ON e.codigo = v.codigo
JOIN abet.carga c ON true
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_450020_301_v1.csv'
JOIN abet.carga_columna cc ON cc.carga_id = c.carga_id;

UPDATE abet.carga c
SET estado = 'PUBLICADA', filas_leidas = 3, filas_aceptadas = 3, filas_rechazadas = 0, terminada_en = now()
FROM abet.archivo_origen ao
WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_450020_301_v1.csv';
COMMIT;

-- Segunda carga corregida: la tercera fila llega vacía (SIN_EVIDENCIA).
BEGIN;
INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version, reemplaza_carga_id)
SELECT c1.seccion_id, ao2.archivo_id, ao2.filas_de_datos, c1.carrera_id, c1.conjunto_reglas_id, 'v0.0.0-prueba', c1.carga_id
FROM abet.carga c1
JOIN abet.archivo_origen ao1 ON ao1.archivo_id = c1.archivo_id AND ao1.nombre_archivo = 'sintetico_450020_301_v1.csv'
JOIN abet.archivo_origen ao2 ON ao2.nombre_archivo = 'sintetico_450020_301_v2.csv';

INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id, pi_id,
                                pi_codigo, posicion, encabezado, bb_columna_id, puntaje_maximo_declarado)
SELECT c.carga_id, s.seccion_id, c.carrera_id, s.periodo_id, s.asignatura_id, pm.plan_medicion_id, pm.pi_id,
       '1.1', 5, '1.1 [Total Pts: 4 Score] |9000011', '9000011', 4
FROM abet.carga c
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_450020_301_v2.csv'
JOIN abet.seccion s ON s.seccion_id = c.seccion_id
JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id;

INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id)
SELECT c.carga_id, v.fila, e.estudiante_id
FROM (VALUES ('99000001', 2), ('99000002', 3), ('99000003', 4)) AS v (codigo, fila)
JOIN abet.estudiante e ON e.codigo = v.codigo
JOIN abet.carga c ON true
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_450020_301_v2.csv';

INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
SELECT cc.carga_id, cc.carga_columna_id, cc.pi_id, e.estudiante_id,
       CASE WHEN v.nivel IS NULL THEN 'SIN_EVIDENCIA' ELSE 'CALIFICADO' END, v.nivel, v.fila
FROM (VALUES ('99000001', 2, 4), ('99000002', 3, 2), ('99000003', 4, NULL)) AS v (codigo, fila, nivel)
JOIN abet.estudiante e ON e.codigo = v.codigo
JOIN abet.carga c ON true
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_450020_301_v2.csv'
JOIN abet.carga_columna cc ON cc.carga_id = c.carga_id;

-- Primero la anterior pasa a REEMPLAZADA y luego la nueva a PUBLICADA (una sola publicada por sección).
UPDATE abet.carga c
SET estado = 'REEMPLAZADA'
FROM abet.archivo_origen ao
WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_450020_301_v1.csv';

UPDATE abet.carga c
SET estado = 'PUBLICADA', filas_leidas = 3, filas_aceptadas = 3, filas_rechazadas = 0, terminada_en = now()
FROM abet.archivo_origen ao
WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_450020_301_v2.csv';
COMMIT;

DO $$
DECLARE
    r record;
BEGIN
    IF (SELECT string_agg(c.estado, ',' ORDER BY ao.nombre_archivo)
          FROM abet.carga c JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
         WHERE ao.nombre_archivo LIKE 'sintetico_450020_301_%') IS DISTINCT FROM 'REEMPLAZADA,PUBLICADA' THEN
        RAISE EXCEPTION 'FALLA A02: la anterior debe quedar REEMPLAZADA y la nueva PUBLICADA';
    END IF;
    SELECT * INTO r FROM abet.v_r17_por_pi WHERE codigo_asignatura = '450020' AND seccion = '301' AND pi = '1.1';
    IF NOT FOUND OR r.n_total <> 3 OR r.n_sin_evidencia <> 1 OR r.n_esperado_o_superior <> 1
       OR r.n_debajo_del_esperado <> 1 OR r.pct_logro_sobre_calificados <> 50.0
       OR r.pct_logro_sobre_total_con_sin_evidencia <> 33.3 THEN
        RAISE EXCEPTION 'FALLA A02: la vista del R-17 no refleja la carga de reemplazo (%)', r;
    END IF;
    IF (SELECT count(*) FROM abet.v_r17_por_pi WHERE codigo_asignatura = '450020') <> 1 THEN
        RAISE EXCEPTION 'FALLA A02: la carga REEMPLAZADA no debe aparecer en la vista del R-17';
    END IF;
    IF (SELECT count(*) FROM abet.v_tabla_maestra_pi WHERE "CÓDIGO DEL CURSO" = '450020') <> 3
       OR (SELECT count(*) FROM abet.v_tabla_maestra_pi
            WHERE "CÓDIGO DEL CURSO" = '450020' AND "ESTADO DE EVIDENCIA" = 'SIN_EVIDENCIA' AND "CALIFICACIÓN" IS NULL) <> 1 THEN
        RAISE EXCEPTION 'FALLA A02: la tabla maestra debe traer solo las 3 filas de la carga vigente';
    END IF;
    RAISE NOTICE 'ok A02 reemplazo de carga publicada (anterior REEMPLAZADA, nueva PUBLICADA)';
END $$;

-- A03. La carrera aprueba sus reglas y la carga publicada de 450020-301 se reprocesa con el MISMO archivo y el
-- conjunto aprobado, por reemplazo (H57). La carga anterior conserva las reglas con que se publicó.
-- Las reglas de R-PRUEBA-APROBADO son inventadas para la prueba; no son decisiones de la carrera.
BEGIN;
INSERT INTO abet.conjunto_reglas (carrera_id, version, estado, aprobado_por, aprobado_en)
SELECT carrera_id, 'R-PRUEBA-APROBADO', 'APROBADO', 'Comité de prueba', DATE '2026-10-01'
FROM abet.carrera WHERE codigo = 'AMB';
INSERT INTO abet.parametro_valor (conjunto_reglas_id, clave, estado, valor_numero, valor_texto)
SELECT cr.conjunto_reglas_id, v.clave, 'DEFINIDO', v.numero, v.texto
FROM (VALUES ('META_LOGRO',           CAST(0.70 AS numeric(9, 4)), CAST(NULL AS varchar(40))),
             ('NIVEL_ESPERADO',       2,    NULL),
             ('CORTE_ROJO',           0.50, NULL),
             ('CONVERSION_NIVEL_0_1', NULL, NULL),
             ('TRATO_SIN_EVIDENCIA',  NULL, 'SE_EXCLUYE_DEL_DENOMINADOR')) AS v (clave, numero, texto)
JOIN abet.conjunto_reglas cr ON cr.version = 'R-PRUEBA-APROBADO';
INSERT INTO abet.conversion_nivel_0_1 (conjunto_reglas_id, nivel_original, valor_0_1)
SELECT cr.conjunto_reglas_id, v.nivel, v.valor
FROM (VALUES (1, 0.0), (2, 0.3333), (3, 0.6667), (4, 1.0)) AS v (nivel, valor)
JOIN abet.conjunto_reglas cr ON cr.version = 'R-PRUEBA-APROBADO';

-- Carga nueva EN_CURSO con el mismo archivo mientras la anterior sigue PUBLICADA.
INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version, reemplaza_carga_id)
SELECT c.seccion_id, c.archivo_id, c.filas_de_datos, c.carrera_id, cr.conjunto_reglas_id, 'v0.0.1-prueba', c.carga_id
FROM abet.carga c
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_450020_301_v2.csv'
JOIN abet.conjunto_reglas cr ON cr.version = 'R-PRUEBA-APROBADO'
WHERE c.estado = 'PUBLICADA';

INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id, pi_id,
                                pi_codigo, posicion, encabezado, bb_columna_id, puntaje_maximo_declarado)
SELECT n.carga_id, cc.seccion_id, cc.carrera_id, cc.periodo_id, cc.asignatura_id, cc.plan_medicion_id, cc.pi_id,
       cc.pi_codigo, cc.posicion, cc.encabezado, cc.bb_columna_id, cc.puntaje_maximo_declarado
FROM abet.carga n
JOIN abet.conjunto_reglas cr ON cr.conjunto_reglas_id = n.conjunto_reglas_id AND cr.version = 'R-PRUEBA-APROBADO'
JOIN abet.carga_columna cc ON cc.carga_id = n.reemplaza_carga_id
WHERE n.estado = 'EN_CURSO';

INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id)
SELECT n.carga_id, f.fila_origen, f.estudiante_id
FROM abet.carga n
JOIN abet.conjunto_reglas cr ON cr.conjunto_reglas_id = n.conjunto_reglas_id AND cr.version = 'R-PRUEBA-APROBADO'
JOIN abet.carga_fila f ON f.carga_id = n.reemplaza_carga_id
WHERE n.estado = 'EN_CURSO';

INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
SELECT n.carga_id, ncc.carga_columna_id, m.pi_id, m.estudiante_id, m.estado_evidencia, m.nivel_original, m.fila_origen
FROM abet.carga n
JOIN abet.conjunto_reglas cr ON cr.conjunto_reglas_id = n.conjunto_reglas_id AND cr.version = 'R-PRUEBA-APROBADO'
JOIN abet.medicion m ON m.carga_id = n.reemplaza_carga_id
JOIN abet.carga_columna ncc ON ncc.carga_id = n.carga_id AND ncc.pi_id = m.pi_id
WHERE n.estado = 'EN_CURSO';

UPDATE abet.carga a
SET estado = 'REEMPLAZADA'
FROM abet.carga n
JOIN abet.conjunto_reglas cr ON cr.conjunto_reglas_id = n.conjunto_reglas_id AND cr.version = 'R-PRUEBA-APROBADO'
WHERE n.estado = 'EN_CURSO' AND a.carga_id = n.reemplaza_carga_id;

UPDATE abet.carga n
SET estado = 'PUBLICADA', filas_leidas = 3, filas_aceptadas = 3, filas_rechazadas = 0, terminada_en = now()
FROM abet.conjunto_reglas cr
WHERE cr.conjunto_reglas_id = n.conjunto_reglas_id AND cr.version = 'R-PRUEBA-APROBADO' AND n.estado = 'EN_CURSO';
COMMIT;

DO $$
DECLARE
    r record;
BEGIN
    IF (SELECT string_agg(c.estado || ':' || ao.nombre_archivo || ':' || cr.version, ',' ORDER BY c.carga_id)
          FROM abet.carga c
          JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
          JOIN abet.conjunto_reglas cr ON cr.conjunto_reglas_id = c.conjunto_reglas_id
         WHERE ao.nombre_archivo LIKE 'sintetico_450020_301_%')
       IS DISTINCT FROM 'REEMPLAZADA:sintetico_450020_301_v1.csv:R-2026-BORRADOR,'
                     || 'REEMPLAZADA:sintetico_450020_301_v2.csv:R-2026-BORRADOR,'
                     || 'PUBLICADA:sintetico_450020_301_v2.csv:R-PRUEBA-APROBADO' THEN
        RAISE EXCEPTION 'FALLA A03: el reemplazo con el mismo archivo debe conservar las reglas de la carga anterior';
    END IF;
    SELECT * INTO r FROM abet.v_r17_por_pi WHERE codigo_asignatura = '450020' AND seccion = '301' AND pi = '1.1';
    IF NOT FOUND OR r.conjunto_reglas <> 'R-PRUEBA-APROBADO' OR r.provisional IS NOT FALSE
       OR r.nivel_esperado <> 2 OR r.n_esperado_o_superior <> 2 OR r.n_debajo_del_esperado <> 0
       OR r.n_total <> 3 OR r.n_sin_evidencia <> 1
       OR r.pct_logro_sobre_calificados <> 100.0 OR r.pct_logro_sobre_total_con_sin_evidencia <> 66.7
       OR r.trato_sin_evidencia <> 'SE_EXCLUYE_DEL_DENOMINADOR' OR r.pct_logro_segun_regla <> 100.0
       OR r.meta_logro_pct <> 70.0 THEN
        RAISE EXCEPTION 'FALLA A03: la vista del R-17 no usa las reglas aprobadas (%)', r;
    END IF;
    IF (SELECT count(*) FROM abet.v_r17_por_pi WHERE codigo_asignatura = '450020') <> 1
       OR (SELECT count(*) FROM abet.v_tabla_maestra_pi WHERE "CÓDIGO DEL CURSO" = '450020') <> 3 THEN
        RAISE EXCEPTION 'FALLA A03: solo la carga vigente debe aparecer en las vistas';
    END IF;
    RAISE NOTICE 'ok A03 reemplazo con el mismo archivo y reglas aprobadas (R-17 oficial, la anterior guarda sus reglas)';
END $$;

-- A04. V1_09 crea el esquema acceso con sus seis tablas, la columna carga.subida_por y los motivos nuevos (US-04).
DO $$
BEGIN
    IF (SELECT string_agg(table_name, ',' ORDER BY table_name) FROM information_schema.tables
         WHERE table_schema = 'acceso')
       IS DISTINCT FROM 'codigo_acceso,credencial,docente_seccion,intento_fallido,sesion,usuario_autorizado' THEN
        RAISE EXCEPTION 'FALLA A04: acceso debe tener usuario_autorizado, credencial, sesion, intento_fallido, docente_seccion y codigo_acceso';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'abet' AND table_name = 'carga' AND column_name = 'subida_por'
                      AND is_nullable = 'YES' AND data_type = 'integer')
       OR NOT EXISTS (SELECT 1 FROM pg_constraint
                       WHERE conname = 'fk_carga_subida_por' AND conrelid = 'abet.carga'::regclass
                         AND confrelid = 'acceso.usuario_autorizado'::regclass) THEN
        RAISE EXCEPTION 'FALLA A04: abet.carga.subida_por debe admitir nulo y apuntar a acceso.usuario_autorizado';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'acceso' AND c.relkind = 'r' AND obj_description(c.oid, 'pg_class') IS NULL)
       OR obj_description('acceso'::regnamespace, 'pg_namespace') IS NULL THEN
        RAISE EXCEPTION 'FALLA A04: el esquema acceso y cada una de sus tablas deben llevar COMMENT ON';
    END IF;
    IF EXISTS (SELECT 1 FROM abet.carga WHERE subida_por IS NOT NULL) THEN
        RAISE EXCEPTION 'FALLA A04: las cargas de los datos sintéticos y de A02 y A03 no registran quién las sube';
    END IF;
    RAISE NOTICE 'ok A04 V1_09 crea acceso con sus seis tablas comentadas y abet.carga.subida_por nulo con su FK';
END $$;

-- A05. Datos de 2026-2 de db/datos/periodo_2026_2_inventado.sql. correr_pruebas.sh los aplica dos veces después de
-- datos_sinteticos.sql, y ninguna fila se duplica ni choca con las de los datos sintéticos (US-03 y US-04). Los datos
-- del profesor con varias secciones, que llegan después, tienen su propia aserción en A08.
DO $$
BEGIN
    IF (SELECT count(*) FROM abet.catalogo_vigencia) <> 1
       OR (SELECT string_agg(s.numero || '=' || s.curso_blackboard, ',' ORDER BY s.numero)
             FROM abet.seccion s JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002'
            WHERE s.numero IN ('410', '411'))
          IS DISTINCT FROM '410=SINTETICO_20262_450002_410,411=SINTETICO_20262_450002_411'
       OR (SELECT string_agg(p.codigo, ',' ORDER BY p.codigo)
             FROM abet.plan_medicion pm JOIN abet.pi p ON p.pi_id = pm.pi_id
             JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id AND a.codigo = '450002')
          IS DISTINCT FROM '5.1,5.2,5.3'
       OR (SELECT count(*) FROM abet.plan_medicion pm
             JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id AND a.codigo IN ('450002', '450020')) <> 4 THEN
        RAISE EXCEPTION 'FALLA A05: la vigencia, las secciones 410 y 411 y el plan de 2026-2 deben estar una sola vez';
    END IF;
    IF (SELECT string_agg(u.correo || '=' || u.rol || ':' || u.activo, ',' ORDER BY u.correo)
          FROM acceso.usuario_autorizado u
         WHERE u.correo IN ('coordinacion@example.invalid', 'docente410@example.invalid', 'docente411@example.invalid'))
       IS DISTINCT FROM 'coordinacion@example.invalid=COORDINADOR:true,docente410@example.invalid=PROFESOR:true,'
                        || 'docente411@example.invalid=PROFESOR:true'
       OR (SELECT string_agg(u.correo || '=' || s.numero, ',' ORDER BY u.correo)
             FROM acceso.docente_seccion d JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
             JOIN abet.seccion s ON s.seccion_id = d.seccion_id
            WHERE u.correo IN ('coordinacion@example.invalid', 'docente410@example.invalid', 'docente411@example.invalid'))
          IS DISTINCT FROM 'docente410@example.invalid=410,docente411@example.invalid=411'
       OR (SELECT count(*) FROM acceso.credencial) + (SELECT count(*) FROM acceso.sesion)
          + (SELECT count(*) FROM acceso.intento_fallido) + (SELECT count(*) FROM acceso.codigo_acceso) <> 0 THEN
        RAISE EXCEPTION 'FALLA A05: los 3 usuarios de 2026-2 deben quedar activos, con 2 asignaciones, y la base sin credenciales, sesiones, intentos ni códigos';
    END IF;
    RAISE NOTICE 'ok A05 datos de 2026-2 aplicados dos veces sobre los datos sintéticos, sin duplicar ni chocar';
END $$;

-- A06. Filas válidas de las tablas de acceso, una carga con subida_por y los 14 motivos de rechazo con su efecto,
-- en una transacción que se deshace. El hash Argon2id es inventado y no corresponde a ninguna contraseña.
BEGIN;
INSERT INTO acceso.credencial (usuario_id, hash_clave)
SELECT usuario_id, '$argon2id$v=19$m=65536,t=3,p=4$cHJ1ZWJh$cHJ1ZWJh'
FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid';

-- Sesión con la vigencia por defecto de 12 horas, cerrada después sin borrarla, con el cierre del COMMENT de
-- acceso.sesion.expira_en.
INSERT INTO acceso.sesion (usuario_id, hash_token)
SELECT usuario_id, encode(sha256(convert_to('sesion A06', 'UTF8')), 'hex')
FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid';
UPDATE acceso.sesion SET expira_en = least(expira_en, clock_timestamp())
WHERE hash_token = encode(sha256(convert_to('sesion A06', 'UTF8')), 'hex');

-- Intento fallido con un correo que no está en usuario_autorizado, guardado como hash en hexadecimal minúscula.
INSERT INTO acceso.intento_fallido (hash_cuenta)
VALUES (encode(sha256(convert_to('desconocido@example.invalid', 'UTF8')), 'hex'));

-- Código del corte 2 con la vigencia por defecto de 10 minutos y sus 5 intentos agotados.
INSERT INTO acceso.codigo_acceso (usuario_id, hash_codigo, intentos)
SELECT usuario_id, encode(sha256(convert_to('codigo A06', 'UTF8')), 'hex'), 5
FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid';

-- Carga RECHAZADA de la 411 subida por su profesor, con un registro por cada motivo de la lista de V1_09.
INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)
VALUES (encode(sha256(convert_to('sondeo motivos V1_09', 'UTF8')), 'hex'), 'sondeo_motivos.xlsx', 'Hoja1', 2);
INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version,
                        estado, terminada_en, subida_por)
SELECT s.seccion_id, ao.archivo_id, 2, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba', 'RECHAZADA', now(),
       u.usuario_id
FROM abet.seccion s JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002',
     abet.archivo_origen ao, abet.conjunto_reglas cr, acceso.usuario_autorizado u
WHERE s.numero = '411' AND ao.nombre_archivo = 'sondeo_motivos.xlsx' AND cr.version = 'R-2026-BORRADOR'
  AND u.correo = 'docente411@example.invalid';
INSERT INTO abet.rechazo_fila (carga_id, fila_origen, motivo, efecto)
SELECT c.carga_id, v.fila, v.motivo, v.efecto
FROM (VALUES (2, 'CODIGO_VACIO', 'RECHAZA_FILA'), (2, 'CODIGO_INVALIDO', 'RECHAZA_FILA'),
             (2, 'CODIGO_DUPLICADO', 'RECHAZA_FILA'), (2, 'NIVEL_FUERA_DE_ESCALA', 'RECHAZA_FILA'),
             (2, 'NIVEL_NO_NUMERICO', 'RECHAZA_FILA'), (NULL, 'COLUMNA_PI_FUERA_DEL_PLAN', 'AVISO'),
             (NULL, 'PI_DEL_PLAN_AUSENTE', 'RECHAZA_CARGA'), (NULL, 'ARCHIVO_SIN_FILAS', 'RECHAZA_CARGA'),
             (NULL, 'SECCION_NO_COINCIDE', 'RECHAZA_CARGA'), (NULL, 'PUNTAJE_MAXIMO_DISTINTO', 'AVISO'),
             (NULL, 'COLUMNA_CODIGO_AUSENTE', 'RECHAZA_CARGA'), (NULL, 'PI_REPETIDO', 'RECHAZA_CARGA'),
             (NULL, 'PERIODO_NO_COINCIDE', 'RECHAZA_CARGA'), (NULL, 'SECCION_SIN_DECLARAR', 'AVISO'))
     AS v (fila, motivo, efecto)
JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'sondeo_motivos.xlsx'
JOIN abet.carga c ON c.archivo_id = ao.archivo_id;

DO $$
BEGIN
    IF (SELECT count(*) FROM acceso.credencial WHERE actualizado_en IS NOT NULL) <> 1
       OR (SELECT count(*) FROM acceso.sesion WHERE expira_en <= clock_timestamp() AND expira_en > creada_en) <> 1
       OR (SELECT count(*) FROM acceso.intento_fallido WHERE intentado_en = now()) <> 1
       OR (SELECT count(*) FROM acceso.codigo_acceso WHERE expira_en = creado_en + interval '10 minutes' AND usado_en IS NULL) <> 1 THEN
        RAISE EXCEPTION 'FALLA A06: credencial, sesión cerrada, intento fallido y código del corte 2 válidos deben aceptarse';
    END IF;
    IF (SELECT count(DISTINCT r.motivo) FROM abet.rechazo_fila r JOIN abet.carga c ON c.carga_id = r.carga_id
          JOIN acceso.usuario_autorizado u ON u.usuario_id = c.subida_por AND u.correo = 'docente411@example.invalid') <> 14 THEN
        RAISE EXCEPTION 'FALLA A06: los 14 motivos deben aceptarse en una carga con subida_por';
    END IF;
    RAISE NOTICE 'ok A06 credencial, sesión cerrada sin borrar, intento fallido de un correo desconocido, código del corte 2, carga con subida_por y 14 motivos aceptados';
END $$;
ROLLBACK;

-- A07. rechazo_fila.pi_id guarda el PI del plan en PI_DEL_PLAN_AUSENTE y en PI_REPETIDO (V1_09, US-12 y FR-016). Dos
-- cargas RECHAZADAS de la 410, como las de un export sin la columna del PI 5.2 y de otro con dos columnas del PI 5.1,
-- quedan cada una con filas_leidas 0, un solo rechazo y ninguna columna, en una transacción que se deshace.
BEGIN;
INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)
VALUES (encode(sha256(convert_to('sondeo A07 sin 5.2', 'UTF8')), 'hex'), 'sondeo_sin_5_2.xlsx', 'Hoja1', 11),
       (encode(sha256(convert_to('sondeo A07 5.1 repetido', 'UTF8')), 'hex'), 'sondeo_5_1_repetido.xlsx', 'Hoja1', 11);
INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version,
                        estado, terminada_en, subida_por)
SELECT s.seccion_id, ao.archivo_id, ao.filas_de_datos, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba',
       'RECHAZADA', now(), u.usuario_id
FROM abet.seccion s
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002'
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
JOIN abet.archivo_origen ao ON ao.nombre_archivo IN ('sondeo_sin_5_2.xlsx', 'sondeo_5_1_repetido.xlsx')
JOIN abet.conjunto_reglas cr ON cr.version = 'R-2026-BORRADOR'
JOIN acceso.usuario_autorizado u ON u.correo = 'docente410@example.invalid'
WHERE s.numero = '410';
-- El PI de cada rechazo sale del plan de medición de la sección, como lo toma el programa de carga.
INSERT INTO abet.rechazo_fila (carga_id, fila_origen, motivo, efecto, pi_id)
SELECT c.carga_id, NULL, v.motivo, 'RECHAZA_CARGA', pm.pi_id
FROM (VALUES ('sondeo_sin_5_2.xlsx', 'PI_DEL_PLAN_AUSENTE', '5.2'), ('sondeo_5_1_repetido.xlsx', 'PI_REPETIDO', '5.1'))
     AS v (archivo, motivo, pi)
JOIN abet.archivo_origen ao ON ao.nombre_archivo = v.archivo
JOIN abet.carga c ON c.archivo_id = ao.archivo_id
JOIN abet.seccion s ON s.seccion_id = c.seccion_id
JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
                          AND pm.carrera_id = c.carrera_id
JOIN abet.pi p ON p.pi_id = pm.pi_id AND p.codigo = v.pi;

DO $$
BEGIN
    -- El programa de carga escribe esta columna, así que su tipo y su nulidad quedan fijos, como los de subida_por.
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'abet' AND table_name = 'rechazo_fila' AND column_name = 'pi_id'
                      AND is_nullable = 'YES' AND data_type = 'smallint') THEN
        RAISE EXCEPTION 'FALLA A07: abet.rechazo_fila.pi_id debe ser smallint, como abet.pi.pi_id, y admitir nulo';
    END IF;
    -- La constancia lee el PI de cada rechazo por pi_id, y ese PI es del plan de la sección de la carga.
    IF (SELECT string_agg(c.estado || ':' || c.filas_leidas || ':' || r.motivo || ':' || r.efecto || ':' || p.codigo,
                          ',' ORDER BY r.motivo)
          FROM abet.rechazo_fila r
          JOIN abet.carga c ON c.carga_id = r.carga_id
          JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
               AND ao.nombre_archivo IN ('sondeo_sin_5_2.xlsx', 'sondeo_5_1_repetido.xlsx')
          JOIN abet.seccion s ON s.seccion_id = c.seccion_id
          JOIN abet.plan_medicion pm ON pm.pi_id = r.pi_id AND pm.periodo_id = s.periodo_id
                                    AND pm.asignatura_id = s.asignatura_id AND pm.carrera_id = c.carrera_id
          JOIN abet.pi p ON p.pi_id = r.pi_id)
       IS DISTINCT FROM 'RECHAZADA:0:PI_DEL_PLAN_AUSENTE:RECHAZA_CARGA:5.2,RECHAZADA:0:PI_REPETIDO:RECHAZA_CARGA:5.1' THEN
        RAISE EXCEPTION 'FALLA A07: PI_DEL_PLAN_AUSENTE y PI_REPETIDO deben guardar en pi_id el PI 5.2 y el 5.1 del plan de la 410';
    END IF;
    IF (SELECT count(*) FROM abet.rechazo_fila r JOIN abet.carga c ON c.carga_id = r.carga_id
          JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
         WHERE ao.nombre_archivo IN ('sondeo_sin_5_2.xlsx', 'sondeo_5_1_repetido.xlsx')) <> 2
       OR EXISTS (SELECT 1 FROM abet.carga_columna cc JOIN abet.carga c ON c.carga_id = cc.carga_id
                    JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
                   WHERE ao.nombre_archivo IN ('sondeo_sin_5_2.xlsx', 'sondeo_5_1_repetido.xlsx')) THEN
        RAISE EXCEPTION 'FALLA A07: cada carga rechazada debe quedar con un solo rechazo y sin columnas';
    END IF;
    RAISE NOTICE 'ok A07 rechazo_fila.pi_id, smallint y con nulo admitido, guarda el PI 5.2 de PI_DEL_PLAN_AUSENTE y el 5.1 de PI_REPETIDO, del plan de la 410, en dos cargas RECHAZADAS sin columnas';
END $$;
ROLLBACK;

-- A08. Datos del profesor con varias secciones de db/datos/varias_secciones_2026_2_inventado.sql, que
-- correr_pruebas.sh aplica dos veces después de los de 2026-2 (US-04, US-06, BR-ACCESO-07 y D-09).
-- docente.varias@example.invalid dicta la 412 de 450002 y la 410 y la 412 de 450010, y ninguna más. La 410 y la 411
-- de 450002 siguen con su profesor, el coordinador sigue sin secciones y nada se duplica. Los textos se ordenan con
-- COLLATE "C", porque docente.varias y docente410 no quedan en el mismo orden en todas las configuraciones regionales.
DO $$
BEGIN
    -- El plan de 450010 mide 2.1 y 2.2 del SO 2 y 5.1 del SO 5, los dos SO que asignatura_so le asigna, con su
    -- instrumento, en la versión vigente de Ambiental. Las 7 filas de plan son las 4 de los datos sintéticos y estas 3.
    IF (SELECT string_agg(p.codigo || '=' || p.so_numero || '=' || i.nombre || '=' || cv.codigo || '=' || c.codigo, ','
                          ORDER BY p.codigo COLLATE "C")
          FROM abet.plan_medicion pm
          JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id AND pe.codigo = '2026-2'
          JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id AND a.codigo = '450010'
          JOIN abet.pi p ON p.pi_id = pm.pi_id
          JOIN abet.instrumento i ON i.instrumento_id = pm.instrumento_id
          JOIN abet.catalogo_version cv ON cv.catalogo_version_id = pm.catalogo_version_id
          JOIN abet.carrera c ON c.carrera_id = pm.carrera_id)
       IS DISTINCT FROM '2.1=2=Trabajo Integrador=AMB-2026=AMB,2.2=2=Trabajo Integrador=AMB-2026=AMB,'
                        || '5.1=5=Trabajo Integrador=AMB-2026=AMB'
       OR (SELECT count(*) FROM abet.plan_medicion) <> 7 THEN
        RAISE EXCEPTION 'FALLA A08: el plan de 450010 en 2026-2 debe ser 2.1 y 2.2 del SO 2 y 5.1 del SO 5 con Trabajo Integrador, una sola vez';
    END IF;
    -- Las cinco secciones con curso de Blackboard, una sola vez cada una, y la 412 en dos asignaturas con cursos
    -- distintos. Las 7 secciones de 2026-2 son esas cinco y las dos 301 de A01, que no tienen curso.
    IF (SELECT string_agg(a.codigo || '-' || s.numero || '=' || s.curso_blackboard, ','
                          ORDER BY a.codigo COLLATE "C", s.numero COLLATE "C")
          FROM abet.seccion s
          JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
          JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
         WHERE s.curso_blackboard IS NOT NULL)
       IS DISTINCT FROM '450002-410=SINTETICO_20262_450002_410,450002-411=SINTETICO_20262_450002_411,'
                        || '450002-412=SINTETICO_20262_450002_412,450010-410=SINTETICO_20262_450010_410,'
                        || '450010-412=SINTETICO_20262_450010_412'
       OR (SELECT count(*) FROM abet.seccion) <> 7 THEN
        RAISE EXCEPTION 'FALLA A08: la 412 de 450002 y la 410 y la 412 de 450010 deben estar una sola vez, con su curso de Blackboard';
    END IF;
    -- Cuatro usuarios activos y cinco asignaciones en toda la base, las tres de docente.varias entre ellas.
    IF (SELECT string_agg(u.correo || '=' || u.rol || '=' || u.activo, ',' ORDER BY u.correo COLLATE "C")
          FROM acceso.usuario_autorizado u)
       IS DISTINCT FROM 'coordinacion@example.invalid=COORDINADOR=true,docente.varias@example.invalid=PROFESOR=true,'
                        || 'docente410@example.invalid=PROFESOR=true,docente411@example.invalid=PROFESOR=true'
       OR (SELECT string_agg(a.codigo || '-' || s.numero || '=' || u.correo, ','
                             ORDER BY a.codigo COLLATE "C", s.numero COLLATE "C", u.correo COLLATE "C")
             FROM acceso.docente_seccion d
             JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
             JOIN abet.seccion s ON s.seccion_id = d.seccion_id
             JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id)
          IS DISTINCT FROM '450002-410=docente410@example.invalid,450002-411=docente411@example.invalid,'
                           || '450002-412=docente.varias@example.invalid,450010-410=docente.varias@example.invalid,'
                           || '450010-412=docente.varias@example.invalid' THEN
        RAISE EXCEPTION 'FALLA A08: deben quedar 4 usuarios activos y 5 asignaciones, las de docente.varias@example.invalid solo en la 412 de 450002 y en la 410 y la 412 de 450010';
    END IF;
    -- Lo que la regla de visibilidad le muestra a docente.varias en 2026-2 (BR-ACCESO-07 y BR-PERIODO-04), que son sus
    -- tres secciones con los PI del plan de su asignatura, sin carga PUBLICADA y sin la 410 ni la 411 de 450002.
    IF (SELECT string_agg(a.codigo || '-' || s.numero || '='
                          || coalesce((SELECT string_agg(p.codigo, ' ' ORDER BY p.codigo COLLATE "C")
                                         FROM abet.plan_medicion pm JOIN abet.pi p ON p.pi_id = pm.pi_id
                                        WHERE pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id),
                                      'sin plan')
                          || '=' || CASE WHEN EXISTS (SELECT 1 FROM abet.carga c
                                                       WHERE c.seccion_id = s.seccion_id AND c.estado = 'PUBLICADA')
                                         THEN 'PUBLICADA' ELSE 'SIN_CARGA' END,
                          ',' ORDER BY a.codigo COLLATE "C", s.numero COLLATE "C")
          FROM acceso.docente_seccion d
          JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id AND u.correo = 'docente.varias@example.invalid'
          JOIN abet.seccion s ON s.seccion_id = d.seccion_id
          JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
          JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id)
       IS DISTINCT FROM '450002-412=5.1 5.2 5.3=SIN_CARGA,450010-410=2.1 2.2 5.1=SIN_CARGA,'
                        || '450010-412=2.1 2.2 5.1=SIN_CARGA' THEN
        RAISE EXCEPTION 'FALLA A08: docente.varias@example.invalid debe ver solo sus tres secciones, cada una con su plan y sin carga';
    END IF;
    RAISE NOTICE 'ok A08 datos de varias secciones aplicados dos veces, sin duplicar, con el plan 2.1, 2.2 y 5.1 de 450010 y las tres secciones de docente.varias@example.invalid, y solo esas';
END $$;

-- A09. V1_10: ck_carga_columna_encabezado acepta el prefijo del export real de Blackboard (spec 003, US-26 y J-19) y
-- sigue rechazando lo que no es el PI. Cada encabezado se prueba sobre la columna del PI 5.1 de la carga de la 410,
-- dentro de un subbloque cuyo error final deshace los UPDATE, así que los datos de las secciones siguientes no cambian.
DO $$
DECLARE
    v_encabezado text;
    v_filas      int;
BEGIN
    BEGIN
        FOREACH v_encabezado IN ARRAY ARRAY[
            'ABET SO5.1 [Total Pts: 100 Score] |9000051',
            'ABET SO 5.1 [Total Pts: 100 Score] |9000051',
            'abet so 5.1 [Total Pts: 100 Score] |9000051',
            'PI 5.1 [Total Pts: 100 Score] |9000051',
            '5.1[Total Pts: 100 Score] |9000051',
            '5.1 [Total Pts: 4 Score] |9000051'] LOOP
            UPDATE abet.carga_columna cc SET encabezado = v_encabezado
            FROM abet.pi p, abet.carga c, abet.archivo_origen ao
            WHERE p.pi_id = cc.pi_id AND p.codigo = '5.1' AND c.carga_id = cc.carga_id
              AND ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx';
            GET DIAGNOSTICS v_filas = ROW_COUNT;
            IF v_filas <> 1 THEN
                RAISE EXCEPTION 'FALLA A09: el encabezado «%» debe actualizar la columna del PI 5.1 de la 410 (filas: %)', v_encabezado, v_filas;
            END IF;
        END LOOP;
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'deshacer A09';
    EXCEPTION WHEN SQLSTATE 'P0001' THEN
        IF SQLERRM <> 'deshacer A09' THEN
            RAISE;
        END IF;
    END;
    IF (SELECT count(*) FROM abet.carga_columna cc JOIN abet.pi p ON p.pi_id = cc.pi_id AND p.codigo = '5.1'
          WHERE cc.encabezado !~ '^5\.1 \[') > 0 THEN
        RAISE EXCEPTION 'FALLA A09: los encabezados de prueba deben deshacerse';
    END IF;
    RAISE NOTICE 'ok A09 encabezados con prefijo (ABET SO5.1, ABET SO 5.1, abet so 5.1, PI 5.1, 5.1[ y 5.1 [) aceptados para el PI 5.1';
END $$;

-- A10. V1_10: SIN_CALIFICACIONES entra en ck_rechazo_fila_motivo con RECHAZA_CARGA (spec 003, US-36 y D-31). El
-- rechazo se inserta en un subbloque que se deshace. R60 sigue probando que un motivo desconocido no entra.
DO $$
DECLARE
    v_filas int;
BEGIN
    BEGIN
        INSERT INTO abet.rechazo_fila (carga_id, fila_origen, motivo, efecto)
        SELECT c.carga_id, NULL, 'SIN_CALIFICACIONES', 'RECHAZA_CARGA'
        FROM abet.carga c JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
             AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx';
        GET DIAGNOSTICS v_filas = ROW_COUNT;
        IF v_filas <> 1 THEN
            RAISE EXCEPTION 'FALLA A10: SIN_CALIFICACIONES con RECHAZA_CARGA debe aceptarse (filas: %)', v_filas;
        END IF;
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'deshacer A10';
    EXCEPTION WHEN SQLSTATE 'P0001' THEN
        IF SQLERRM <> 'deshacer A10' THEN
            RAISE;
        END IF;
    END;
    IF EXISTS (SELECT 1 FROM abet.rechazo_fila WHERE motivo = 'SIN_CALIFICACIONES') THEN
        RAISE EXCEPTION 'FALLA A10: el rechazo de prueba debe deshacerse';
    END IF;
    RAISE NOTICE 'ok A10 SIN_CALIFICACIONES aceptado con RECHAZA_CARGA en ck_rechazo_fila_motivo';
END $$;

-- ---------------------------------------------------------------------------------------------
-- 3. Números del R-17 de la sección 410 de 450002 (misma distribución que el caso real)
-- ---------------------------------------------------------------------------------------------
DO $$
DECLARE
    r record;
    v_n int := 0;
BEGIN
    FOR r IN
        SELECT v.pi, v.nivel_esperado, v.n_debajo_del_esperado, v.n_esperado_o_superior, v.n_sin_evidencia, v.n_total,
               v.pct_logro_sobre_calificados, v.pct_logro_sobre_total_con_sin_evidencia, v.meta_logro_pct, v.provisional,
               v.trato_sin_evidencia, v.pct_logro_segun_regla, v.n_nivel_1, v.n_nivel_2, v.n_nivel_3, v.n_nivel_4, e.*
        FROM abet.v_r17_por_pi v
        JOIN (VALUES ('5.1', 4, 7, 63.6, 1, 3, 4, 3), ('5.2', 4, 7, 63.6, 1, 3, 4, 3), ('5.3', 3, 8, 72.7, 1, 2, 5, 3))
             AS e (pi_e, bajo_e, ok_e, pct_e, n1_e, n2_e, n3_e, n4_e)
          ON e.pi_e = v.pi
        WHERE v.periodo = '2026-2' AND v.codigo_asignatura = '450002' AND v.seccion = '410'
        ORDER BY v.pi
    LOOP
        v_n := v_n + 1;
        IF r.nivel_esperado <> 3 OR r.n_debajo_del_esperado <> r.bajo_e OR r.n_esperado_o_superior <> r.ok_e
           OR r.n_sin_evidencia <> 0 OR r.n_total <> 11
           OR r.pct_logro_sobre_calificados <> r.pct_e OR r.pct_logro_sobre_total_con_sin_evidencia <> r.pct_e
           OR r.meta_logro_pct <> 80.0 OR r.provisional IS NOT TRUE
           OR r.trato_sin_evidencia IS NOT NULL OR r.pct_logro_segun_regla IS NOT NULL
           OR (r.n_nivel_1, r.n_nivel_2, r.n_nivel_3, r.n_nivel_4) IS DISTINCT FROM (r.n1_e, r.n2_e, r.n3_e, r.n4_e) THEN
            RAISE EXCEPTION 'FALLA R-17 en PI %: %', r.pi, r;
        END IF;
        RAISE NOTICE 'ok R-17 PI %: % de 11 en nivel 3 o más = % %% (meta % %%)', r.pi, r.n_esperado_o_superior,
                     r.pct_logro_sobre_calificados, r.meta_logro_pct;
    END LOOP;
    IF v_n <> 3 THEN
        RAISE EXCEPTION 'FALLA R-17: se esperaban 3 PI en la sección 410 y hay %', v_n;
    END IF;
END $$;
-- El R-17 del export con error (60,0 / 60,0 / 70,0) está en la sección 7, porque comprueba además Q01 a Q14
-- dentro de su transacción.

-- R-17 con TRATO_SIN_EVIDENCIA DEFINIDO en un conjunto que sigue en BORRADOR: el porcentaje según la regla
-- sale del trato, pero la vista sigue provisional porque el conjunto no está APROBADO.
BEGIN;
UPDATE abet.parametro_valor pv SET estado = 'DEFINIDO', valor_texto = 'CUENTA_COMO_NO_LOGRADO'
FROM abet.conjunto_reglas cr
WHERE cr.conjunto_reglas_id = pv.conjunto_reglas_id AND cr.version = 'R-2026-BORRADOR' AND pv.clave = 'TRATO_SIN_EVIDENCIA';
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM abet.v_r17_por_pi
                WHERE codigo_asignatura = '450002' AND seccion = '410'
                  AND (provisional IS NOT TRUE
                       OR pct_logro_segun_regla IS DISTINCT FROM pct_logro_sobre_total_con_sin_evidencia))
       OR (SELECT count(*) FROM abet.v_r17_por_pi WHERE codigo_asignatura = '450002' AND seccion = '410') <> 3 THEN
        RAISE EXCEPTION 'FALLA R-17 con TRATO DEFINIDO en BORRADOR: debe seguir provisional y usar el porcentaje sobre el total';
    END IF;
    RAISE NOTICE 'ok R-17 con TRATO DEFINIDO en BORRADOR sigue provisional y elige el porcentaje según la regla';
END $$;
ROLLBACK;

-- R-17 con un conjunto de reglas cuyo NIVEL_ESPERADO está PENDIENTE: porcentajes NULL, nunca 0 (H80).
-- El UPDATE de conjunto_reglas_id es solo un sondeo que se deshace; en la operación las reglas de una carga
-- publicada cambian por reemplazo (A03), nunca editando la carga.
BEGIN;
INSERT INTO abet.conjunto_reglas (carrera_id, version)
SELECT carrera_id, 'R-PRUEBA-PEND' FROM abet.carrera WHERE codigo = 'AMB';
INSERT INTO abet.parametro_valor (conjunto_reglas_id, clave, estado)
SELECT conjunto_reglas_id, 'NIVEL_ESPERADO', 'PENDIENTE' FROM abet.conjunto_reglas WHERE version = 'R-PRUEBA-PEND';
UPDATE abet.carga c
SET conjunto_reglas_id = (SELECT conjunto_reglas_id FROM abet.conjunto_reglas WHERE version = 'R-PRUEBA-PEND')
FROM abet.archivo_origen ao
WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx';
DO $$
DECLARE
    r record;
    v_n int := 0;
BEGIN
    FOR r IN SELECT * FROM abet.v_r17_por_pi WHERE codigo_asignatura = '450002' AND seccion = '410' LOOP
        v_n := v_n + 1;
        IF r.conjunto_reglas <> 'R-PRUEBA-PEND' OR r.nivel_esperado IS NOT NULL
           OR r.n_debajo_del_esperado IS NOT NULL OR r.n_esperado_o_superior IS NOT NULL
           OR r.pct_logro_sobre_calificados IS NOT NULL OR r.pct_logro_sobre_total_con_sin_evidencia IS NOT NULL
           OR r.meta_logro_pct IS NOT NULL OR r.n_total <> 11
           OR r.n_nivel_1 + r.n_nivel_2 + r.n_nivel_3 + r.n_nivel_4 <> 11 THEN
            RAISE EXCEPTION 'FALLA R-17 con NIVEL_ESPERADO PENDIENTE en PI %: %', r.pi, r;
        END IF;
    END LOOP;
    IF v_n <> 3 THEN
        RAISE EXCEPTION 'FALLA R-17 con NIVEL_ESPERADO PENDIENTE: se esperaban 3 PI y hay %', v_n;
    END IF;
    RAISE NOTICE 'ok R-17 con NIVEL_ESPERADO PENDIENTE da porcentajes NULL y conserva el conteo por nivel';
END $$;
ROLLBACK;

-- 4. Tabla_Maestra_PI con las columnas que espera Power BI
DO $$
BEGIN
    IF (SELECT string_agg(column_name, '|' ORDER BY ordinal_position)
          FROM information_schema.columns
         WHERE table_schema = 'abet' AND table_name = 'v_tabla_maestra_pi')
       IS DISTINCT FROM 'AÑO|CICLO|CÓDIGO DEL CURSO|CURSO|CICLO DEL CURSO|SO|PI|PROFESOR|CÓDIGO DEL ESTUDIANTE|SECCIÓN|CALIFICACIÓN|ARCHIVO|ESTADO DE EVIDENCIA' THEN
        RAISE EXCEPTION 'FALLA T01: las columnas de v_tabla_maestra_pi no son las que espera Power BI';
    END IF;
    IF (SELECT count(*) FROM abet.v_tabla_maestra_pi
         WHERE "CÓDIGO DEL CURSO" = '450002' AND "SECCIÓN" = '410' AND "AÑO" = 2026 AND "CICLO" = 2
           AND "SO" = 5 AND "PI" IN ('5.1', '5.2', '5.3') AND "CICLO DEL CURSO" = 4 AND "PROFESOR" IS NULL
           AND "ESTADO DE EVIDENCIA" = 'CALIFICADO' AND "ARCHIVO" = 'sintetico_20262_450002_410.xlsx') <> 33 THEN
        RAISE EXCEPTION 'FALLA T01: la tabla maestra debe traer 33 filas de 450002-410 con SO y ciclo del catálogo';
    END IF;
    IF (SELECT pg_typeof("PI")::text FROM abet.v_tabla_maestra_pi LIMIT 1) <> 'character varying' THEN
        RAISE EXCEPTION 'FALLA T01: el PI debe salir como texto';
    END IF;
    RAISE NOTICE 'ok T01 tabla maestra con las columnas de Power BI, PI como texto y PROFESOR NULL';
END $$;

-- ---------------------------------------------------------------------------------------------
-- 5. Casos que deben fallar con ERROR. Cada caso indica la restricción que debe rechazarlo.
-- ---------------------------------------------------------------------------------------------
CREATE TEMP TABLE caso_rechazo (
    id          text PRIMARY KEY,
    descripcion text NOT NULL,
    sentencia   text NOT NULL,
    sqlstate    text NOT NULL,
    restriccion text NULL
);

INSERT INTO caso_rechazo VALUES
('R01', 'columna con el código de PI «6.10», que no existe en el catálogo', $q$
 UPDATE abet.carga_columna cc SET pi_codigo = '6.10', encabezado = '6.10 [Total Pts: 4 Score] |9000051'
 FROM abet.pi p WHERE p.pi_id = cc.pi_id AND p.codigo = '5.1'
$q$, '23503', 'fk_carga_columna_pi_codigo'),
('R02', 'PI con código «6.1» guardado para el número 10', $q$
 INSERT INTO abet.pi (catalogo_version_id, so_id, so_numero, numero, codigo, descripcion)
 SELECT s.catalogo_version_id, s.so_id, 6, 10, '6.1', 'prueba' FROM abet.so s WHERE s.numero = 6
$q$, '23514', 'ck_pi_codigo_so'),
('R03', 'sección duplicada en el mismo periodo y asignatura', $q$
 INSERT INTO abet.seccion (periodo_id, asignatura_id, numero)
 SELECT pe.periodo_id, a.asignatura_id, '410' FROM abet.periodo pe, abet.asignatura a
 WHERE pe.codigo = '2026-2' AND a.codigo = '450002'
$q$, '23505', 'uq_seccion'),
('R04', 'segunda carga PUBLICADA en la misma sección sin reemplazo', $q$
 WITH ao AS (INSERT INTO abet.archivo_origen (sha256, nombre_archivo, filas_de_datos)
             VALUES (encode(sha256(convert_to('otra publicada 410', 'UTF8')), 'hex'), 'otra.csv', 11) RETURNING archivo_id)
 INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version, estado,
                         filas_leidas, filas_aceptadas, filas_rechazadas, terminada_en)
 SELECT c.seccion_id, ao.archivo_id, 11, c.carrera_id, c.conjunto_reglas_id, 'v0.0.0-prueba', 'PUBLICADA', 11, 11, 0, now()
 FROM ao, abet.carga c JOIN abet.archivo_origen x ON x.archivo_id = c.archivo_id
 WHERE x.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
$q$, '23505', 'uq_carga_publicada_por_seccion'),
('R05', 'mismo archivo (misma huella) registrado dos veces', $q$
 INSERT INTO abet.archivo_origen (sha256, nombre_archivo, filas_de_datos)
 VALUES (encode(sha256(convert_to('sintetico 2026-2 450002 410', 'UTF8')), 'hex'), 'copia_con_otro_nombre.xlsx', 11)
$q$, '23505', 'uq_archivo_origen_sha256'),
('R06', 'nivel 5', $q$
 INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
 SELECT m.carga_id, m.carga_columna_id, m.pi_id, m.estudiante_id, 'CALIFICADO', 5, 99 FROM abet.medicion m LIMIT 1
$q$, '23514', 'ck_medicion_nivel'),
('R07', 'nivel 0', $q$
 INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
 SELECT m.carga_id, m.carga_columna_id, m.pi_id, m.estudiante_id, 'CALIFICADO', 0, 99 FROM abet.medicion m LIMIT 1
$q$, '23514', 'ck_medicion_nivel'),
('R08', 'CALIFICADO sin nivel', $q$
 INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
 SELECT m.carga_id, m.carga_columna_id, m.pi_id, m.estudiante_id, 'CALIFICADO', NULL, 99 FROM abet.medicion m LIMIT 1
$q$, '23514', 'ck_medicion_estado_nivel'),
('R09', 'SIN_EVIDENCIA con nivel', $q$
 INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
 SELECT m.carga_id, m.carga_columna_id, m.pi_id, m.estudiante_id, 'SIN_EVIDENCIA', 3, 99 FROM abet.medicion m LIMIT 1
$q$, '23514', 'ck_medicion_estado_nivel'),
('R10', 'carga_columna que apunta al plan de otra asignatura', $q$
 INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id, pi_id,
                                 pi_codigo, posicion, encabezado)
 SELECT c.carga_id, s.seccion_id, c.carrera_id, s.periodo_id, s.asignatura_id, pm.plan_medicion_id, pm.pi_id,
        '1.1', 9, '1.1 [Total Pts: 4 Score] |9000099'
 FROM abet.carga c JOIN abet.seccion s ON s.seccion_id = c.seccion_id
 JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
 JOIN abet.asignatura otra ON otra.codigo = '450020'
 JOIN abet.plan_medicion pm ON pm.asignatura_id = otra.asignatura_id AND pm.periodo_id = s.periodo_id
$q$, '23503', 'fk_carga_columna_plan'),
('R11', 'carga_columna que copia la asignatura del plan ajeno y ya no coincide con su sección', $q$
 INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id, pi_id,
                                 pi_codigo, posicion, encabezado)
 SELECT c.carga_id, s.seccion_id, c.carrera_id, s.periodo_id, pm.asignatura_id, pm.plan_medicion_id, pm.pi_id,
        '1.1', 9, '1.1 [Total Pts: 4 Score] |9000099'
 FROM abet.carga c JOIN abet.seccion s ON s.seccion_id = c.seccion_id
 JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
 JOIN abet.asignatura otra ON otra.codigo = '450020'
 JOIN abet.plan_medicion pm ON pm.asignatura_id = otra.asignatura_id AND pm.periodo_id = s.periodo_id
$q$, '23503', 'fk_carga_columna_seccion'),
('R12', 'aceptadas + rechazadas distinto de leídas', $q$
 UPDATE abet.carga c SET filas_rechazadas = 1
 FROM abet.archivo_origen ao WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
$q$, '23514', 'ck_carga_filas'),
('R13', 'código de estudiante de 7 dígitos', $q$
 INSERT INTO abet.estudiante (codigo) VALUES ('9900001')
$q$, '23514', 'ck_estudiante_codigo'),
('R14', 'META_LOGRO 80 en lugar de 0,80', $q$
 UPDATE abet.parametro_valor SET valor_numero = 80 WHERE clave = 'META_LOGRO'
$q$, '23514', 'ck_parametro_valor_meta_logro'),
('R15', 'NIVEL_ESPERADO 7', $q$
 UPDATE abet.parametro_valor SET valor_numero = 7 WHERE clave = 'NIVEL_ESPERADO'
$q$, '23514', 'ck_parametro_valor_nivel_esperado'),
('R16', 'parámetro PENDIENTE con valor', $q$
 UPDATE abet.parametro_valor SET valor_numero = 0.5 WHERE clave = 'CORTE_ROJO'
$q$, '23514', 'ck_parametro_valor_pendiente'),
('R17', 'filas de conversión 0-1 mientras el parámetro está PENDIENTE', $q$
 INSERT INTO abet.conversion_nivel_0_1 (conjunto_reglas_id, nivel_original, valor_0_1)
 SELECT conjunto_reglas_id, 1, 0 FROM abet.conjunto_reglas WHERE version = 'R-2026-BORRADOR'
$q$, '23503', 'fk_conversion_nivel_0_1_valor'),
('R18', 'aprobar el conjunto de reglas sin decir quién ni cuándo', $q$
 UPDATE abet.conjunto_reglas SET estado = 'APROBADO' WHERE version = 'R-2026-BORRADOR'
$q$, '23514', 'ck_conjunto_reglas_aprobado'),
('R19', 'plan con un PI de un SO que la asignatura no tributa (450002 no tributa SO1)', $q$
 INSERT INTO abet.plan_medicion (periodo_id, asignatura_id, carrera_id, catalogo_version_id, so_id, pi_id)
 SELECT pe.periodo_id, a.asignatura_id, cv.carrera_id, p.catalogo_version_id, p.so_id, p.pi_id
 FROM abet.periodo pe, abet.asignatura a, abet.pi p JOIN abet.catalogo_version cv ON cv.catalogo_version_id = p.catalogo_version_id
 WHERE pe.codigo = '2026-2' AND a.codigo = '450002' AND p.codigo = '1.1'
$q$, '23503', 'fk_plan_medicion_asig_so'),
('R20', 'publicar una carga con cero filas', $q$
 WITH ao AS (INSERT INTO abet.archivo_origen (sha256, nombre_archivo, filas_de_datos)
             VALUES (encode(sha256(convert_to('vacio', 'UTF8')), 'hex'), 'vacio.csv', 0) RETURNING archivo_id)
 INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version, estado, terminada_en)
 SELECT s.seccion_id, ao.archivo_id, 0, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba', 'PUBLICADA', now()
 FROM ao, abet.seccion s JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id, abet.conjunto_reglas cr
 WHERE a.codigo = '450002' AND s.numero = '301'
$q$, '23514', 'ck_carga_publicable'),
('R21', 'mismo estudiante dos veces en la misma carga y PI', $q$
 INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
 SELECT m.carga_id, m.carga_columna_id, m.pi_id, m.estudiante_id, 'CALIFICADO', 3, 99 FROM abet.medicion m LIMIT 1
$q$, '23505', 'uq_medicion'),
('R22', 'reemplazar una carga de otra sección', $q$
 WITH ao AS (INSERT INTO abet.archivo_origen (sha256, nombre_archivo, filas_de_datos)
             VALUES (encode(sha256(convert_to('reemplazo cruzado', 'UTF8')), 'hex'), 'cruzado.csv', 3) RETURNING archivo_id)
 INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version, reemplaza_carga_id)
 SELECT s.seccion_id, ao.archivo_id, 3, c.carrera_id, c.conjunto_reglas_id, 'v0.0.0-prueba', c.carga_id
 FROM ao, abet.carga c JOIN abet.archivo_origen x ON x.archivo_id = c.archivo_id,
      abet.seccion s JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
 WHERE x.nombre_archivo = 'sintetico_20262_450002_410.xlsx' AND a.codigo = '450002' AND s.numero = '301'
$q$, '23503', 'fk_carga_reemplaza'),
('R23', 'competencia con espacio en el código («E1 »)', $q$
 INSERT INTO abet.competencia (catalogo_version_id, codigo, nombre, tipo)
 SELECT catalogo_version_id, 'E1 ', 'prueba', 'ESPECIFICA' FROM abet.catalogo_version WHERE codigo = 'AMB-2026'
$q$, '23514', 'ck_competencia_codigo'),
('R24', 'nombre de archivo con ruta local', $q$
 INSERT INTO abet.archivo_origen (sha256, nombre_archivo, filas_de_datos)
 VALUES (encode(sha256(convert_to('con ruta', 'UTF8')), 'hex'), 'carpeta/archivo.csv', 1)
$q$, '23514', 'ck_archivo_origen_nombre'),
('R25', 'sección «0410» con cero a la izquierda junto a la 410', $q$
 INSERT INTO abet.seccion (periodo_id, asignatura_id, numero)
 SELECT periodo_id, asignatura_id, '0410' FROM abet.seccion WHERE numero = '410'
$q$, '23514', 'ck_seccion_numero'),
('R26', 'encabezado «5.10 …» reconocido como el PI 5.1 (la colisión 6.10 / 6.1 del C6)', $q$
 UPDATE abet.carga_columna cc SET encabezado = '5.10 [Total Pts: 4 Score] |9000051'
 FROM abet.pi p WHERE p.pi_id = cc.pi_id AND p.codigo = '5.1'
$q$, '23514', 'ck_carga_columna_encabezado'),
('R27', 'carga PUBLICADA que dice haber leído 12 filas de un archivo de 11', $q$
 UPDATE abet.carga c SET filas_leidas = 12, filas_aceptadas = 12
 FROM abet.archivo_origen ao WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
$q$, '23514', 'ck_carga_conciliada'),
('R28', 'carga que copia mal las filas de datos de su archivo', $q$
 UPDATE abet.carga c SET filas_de_datos = 12, filas_leidas = 12, filas_aceptadas = 12
 FROM abet.archivo_origen ao WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
$q$, '23503', 'fk_carga_archivo'),
('R29', 'carga de Ambiental con el conjunto de reglas de otra carrera', $q$
 WITH ca AS (INSERT INTO abet.carrera (facultad_id, codigo, nombre)
             SELECT facultad_id, 'IND', 'Carrera de prueba' FROM abet.facultad WHERE codigo = 'FI' RETURNING carrera_id),
      cr AS (INSERT INTO abet.conjunto_reglas (carrera_id, version) SELECT carrera_id, 'R-IND' FROM ca RETURNING conjunto_reglas_id)
 UPDATE abet.carga c SET conjunto_reglas_id = cr.conjunto_reglas_id
 FROM cr, abet.archivo_origen ao WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
$q$, '23503', 'fk_carga_reglas'),
('R30', 'dos versiones de catálogo vigentes para la misma carrera y periodo', $q$
 WITH v AS (INSERT INTO abet.catalogo_version (carrera_id, codigo)
            SELECT carrera_id, 'AMB-2026B' FROM abet.carrera WHERE codigo = 'AMB' RETURNING catalogo_version_id, carrera_id)
 INSERT INTO abet.catalogo_vigencia (periodo_id, carrera_id, catalogo_version_id)
 SELECT pe.periodo_id, v.carrera_id, v.catalogo_version_id FROM v, abet.periodo pe WHERE pe.codigo = '2026-2'
$q$, '23505', 'pk_catalogo_vigencia'),
('R31', 'plan de medición con una versión que no rige en el periodo (2026-1 sin vigencia)', $q$
 INSERT INTO abet.plan_medicion (periodo_id, asignatura_id, carrera_id, catalogo_version_id, so_id, pi_id)
 SELECT pe.periodo_id, a.asignatura_id, cv.carrera_id, p.catalogo_version_id, p.so_id, p.pi_id
 FROM abet.periodo pe, abet.asignatura a, abet.pi p JOIN abet.catalogo_version cv ON cv.catalogo_version_id = p.catalogo_version_id
 WHERE pe.codigo = '2026-1' AND a.codigo = '450002' AND p.codigo = '5.1'
$q$, '23503', 'fk_plan_medicion_vigencia'),
('R32', 'aprobar la versión de catálogo sin decir quién ni cuándo', $q$
 UPDATE abet.catalogo_version
 SET estado = 'APROBADA', vigente_desde_periodo_id = (SELECT periodo_id FROM abet.periodo WHERE codigo = '2026-2')
 WHERE codigo = 'AMB-2026'
$q$, '23514', 'ck_catalogo_version_aprobacion'),
('R33', 'archivo con un tipo de fuente fuera de la lista', $q$
 INSERT INTO abet.archivo_origen (sha256, nombre_archivo, filas_de_datos, tipo_fuente)
 VALUES (encode(sha256(convert_to('otra fuente', 'UTF8')), 'hex'), 'otra_fuente.csv', 1, 'PLANILLA')
$q$, '23514', 'ck_archivo_origen_tipo'),
('R34', 'el archivo de una carga PUBLICADA publicado otra vez en otra sección', $q$
 INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version, estado,
                         filas_leidas, filas_aceptadas, filas_rechazadas, terminada_en)
 SELECT s.seccion_id, c.archivo_id, c.filas_de_datos, c.carrera_id, c.conjunto_reglas_id, 'v0.0.0-prueba', 'PUBLICADA',
        11, 11, 0, now()
 FROM abet.carga c JOIN abet.archivo_origen x ON x.archivo_id = c.archivo_id,
      abet.seccion s JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
 WHERE x.nombre_archivo = 'sintetico_20262_450002_410.xlsx' AND a.codigo = '450002' AND s.numero = '301'
$q$, '23505', 'uq_carga_archivo_util'),
('R35', 'una misma fila del archivo con dos estudiantes', $q$
 INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id)
 SELECT f.carga_id, f.fila_origen, e.estudiante_id
 FROM abet.carga_fila f JOIN abet.carga c ON c.carga_id = f.carga_id
 JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx',
      abet.estudiante e
 WHERE f.fila_origen = 2 AND e.codigo = '99000002'
$q$, '23505', 'pk_carga_fila'),
('R36', 'el mismo estudiante en dos filas de la misma carga', $q$
 INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id)
 SELECT f.carga_id, 13, f.estudiante_id
 FROM abet.carga_fila f JOIN abet.carga c ON c.carga_id = f.carga_id
 JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
 WHERE f.fila_origen = 2
$q$, '23505', 'uq_carga_fila_estudiante'),
('R37', 'medición de un estudiante sin fila aceptada en la carga', $q$
 WITH e AS (INSERT INTO abet.estudiante (codigo) VALUES ('99000099') RETURNING estudiante_id)
 INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
 SELECT m.carga_id, m.carga_columna_id, m.pi_id, e.estudiante_id, 'CALIFICADO', 3, 99
 FROM e, (SELECT * FROM abet.medicion LIMIT 1) AS m
$q$, '23503', 'fk_medicion_fila'),
('R38', 'rechazo que apunta a una columna de otra carga', $q$
 INSERT INTO abet.rechazo_fila (carga_id, fila_origen, carga_columna_id, motivo, efecto)
 SELECT c410.carga_id, 2, cc.carga_columna_id, 'NIVEL_FUERA_DE_ESCALA', 'RECHAZA_FILA'
 FROM abet.carga c410 JOIN abet.archivo_origen a410 ON a410.archivo_id = c410.archivo_id
      AND a410.nombre_archivo = 'sintetico_20262_450002_410.xlsx',
      abet.carga_columna cc JOIN abet.carga c ON c.carga_id = cc.carga_id
 WHERE c.carga_id <> c410.carga_id
 LIMIT 1
$q$, '23503', 'fk_rechazo_fila_columna'),
-- V1_09. Los usuarios de prueba vienen de db/datos/periodo_2026_2_inventado.sql (US-04, FR-003).
('R39', 'usuario con el rol ADMIN, que no existe', $q$
 INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES ('otro@example.invalid', 'ADMIN')
$q$, '23514', 'ck_usuario_autorizado_rol'),
('R40', 'otra vez el usuario docente410@example.invalid con rol PROFESOR', $q$
 INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES ('docente410@example.invalid', 'PROFESOR')
$q$, '23505', 'uq_usuario_autorizado_correo'),
('R41', 'correo sin normalizar « Docente412@EXAMPLE.invalid »', $q$
 INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES (' Docente412@EXAMPLE.invalid ', 'PROFESOR')
$q$, '23514', 'ck_usuario_autorizado_correo'),
('R42', 'correo sin arroba', $q$
 INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES ('sin-arroba.example.invalid', 'PROFESOR')
$q$, '23514', 'ck_usuario_autorizado_correo'),
('R43', 'otra vez la sección 410 a docente410@example.invalid', $q$
 INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)
 SELECT d.usuario_id, d.seccion_id FROM acceso.docente_seccion d
 JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id AND u.correo = 'docente410@example.invalid'
$q$, '23505', 'uq_docente_seccion'),
('R44', 'sección que no existe asignada a docente410@example.invalid', $q$
 INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)
 SELECT u.usuario_id, (SELECT max(seccion_id) + 1000 FROM abet.seccion) FROM acceso.usuario_autorizado u
 WHERE u.correo = 'docente410@example.invalid'
$q$, '23503', 'fk_docente_seccion_seccion'),
('R45', 'sección asignada a un usuario que no existe', $q$
 INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)
 SELECT (SELECT max(usuario_id) + 1000 FROM acceso.usuario_autorizado), seccion_id FROM abet.seccion WHERE numero = '411'
$q$, '23503', 'fk_docente_seccion_usuario'),
('R46', 'credencial con un texto que no es un hash Argon2id', $q$
 INSERT INTO acceso.credencial (usuario_id, hash_clave)
 SELECT usuario_id, 'texto-que-no-es-un-hash' FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid'
$q$, '23514', 'ck_credencial_hash'),
('R47', 'dos credenciales para el mismo usuario', $q$
 INSERT INTO acceso.credencial (usuario_id, hash_clave)
 SELECT usuario_id, '$argon2id$v=19$m=65536,t=3,p=4$cHJ1ZWJh$cHJ1ZWJh' FROM acceso.usuario_autorizado, generate_series(1, 2)
 WHERE correo = 'docente410@example.invalid'
$q$, '23505', 'pk_credencial'),
('R48', 'credencial de un usuario que no existe', $q$
 INSERT INTO acceso.credencial (usuario_id, hash_clave)
 SELECT max(usuario_id) + 1000, '$argon2id$v=19$m=65536,t=3,p=4$cHJ1ZWJh$cHJ1ZWJh' FROM acceso.usuario_autorizado
$q$, '23503', 'fk_credencial_usuario'),
('R49', 'intento fallido que guarda el correo y no su hash', $q$
 INSERT INTO acceso.intento_fallido (hash_cuenta) VALUES ('docente410@example.invalid')
$q$, '23514', 'ck_intento_fallido_hash'),
('R50', 'intento fallido con el hash en mayúsculas, que contaría aparte los intentos del mismo correo', $q$
 INSERT INTO acceso.intento_fallido (hash_cuenta)
 VALUES (upper(encode(sha256(convert_to('docente410@example.invalid', 'UTF8')), 'hex')))
$q$, '23514', 'ck_intento_fallido_hash'),
('R51', 'sesión que guarda el token y no su hash SHA-256', $q$
 INSERT INTO acceso.sesion (usuario_id, hash_token)
 SELECT usuario_id, 'token-en-claro' FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid'
$q$, '23514', 'ck_sesion_token'),
('R52', 'dos sesiones con el mismo hash de token', $q$
 INSERT INTO acceso.sesion (usuario_id, hash_token)
 SELECT usuario_id, encode(sha256(convert_to('sesion repetida', 'UTF8')), 'hex')
 FROM acceso.usuario_autorizado, generate_series(1, 2) WHERE correo = 'docente410@example.invalid'
$q$, '23505', 'uq_sesion_token'),
('R53', 'sesión de 13 horas, más larga que la cookie abet_sesion', $q$
 INSERT INTO acceso.sesion (usuario_id, hash_token, expira_en)
 SELECT usuario_id, encode(sha256(convert_to('sesion larga', 'UTF8')), 'hex'), now() + interval '13 hours'
 FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid'
$q$, '23514', 'ck_sesion_vigencia'),
('R54', 'sesión de un usuario que no existe', $q$
 INSERT INTO acceso.sesion (usuario_id, hash_token)
 SELECT max(usuario_id) + 1000, encode(sha256(convert_to('sesion sin usuario', 'UTF8')), 'hex')
 FROM acceso.usuario_autorizado
$q$, '23503', 'fk_sesion_usuario'),
('R55', 'código de acceso guardado en claro', $q$
 INSERT INTO acceso.codigo_acceso (usuario_id, hash_codigo)
 SELECT usuario_id, '123456' FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid'
$q$, '23514', 'ck_codigo_acceso_hash'),
('R56', 'código de acceso con 6 intentos', $q$
 INSERT INTO acceso.codigo_acceso (usuario_id, hash_codigo, intentos)
 SELECT usuario_id, encode(sha256(convert_to('codigo con intentos', 'UTF8')), 'hex'), 6
 FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid'
$q$, '23514', 'ck_codigo_acceso_intentos'),
('R57', 'código de acceso vigente 11 minutos', $q$
 INSERT INTO acceso.codigo_acceso (usuario_id, hash_codigo, expira_en)
 SELECT usuario_id, encode(sha256(convert_to('codigo largo', 'UTF8')), 'hex'), now() + interval '11 minutes'
 FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid'
$q$, '23514', 'ck_codigo_acceso_vigencia'),
('R58', 'código de acceso de un usuario que no existe', $q$
 INSERT INTO acceso.codigo_acceso (usuario_id, hash_codigo)
 SELECT max(usuario_id) + 1000, encode(sha256(convert_to('codigo sin usuario', 'UTF8')), 'hex')
 FROM acceso.usuario_autorizado
$q$, '23503', 'fk_codigo_acceso_usuario'),
('R59', 'carga subida por un usuario que no existe', $q$
 UPDATE abet.carga c SET subida_por = (SELECT max(usuario_id) + 1000 FROM acceso.usuario_autorizado)
 FROM abet.archivo_origen ao WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
$q$, '23503', 'fk_carga_subida_por'),
('R60', 'rechazo con un motivo que no existe (CODIGO_RARO)', $q$
 INSERT INTO abet.rechazo_fila (carga_id, fila_origen, motivo, efecto)
 SELECT carga_id, NULL, 'CODIGO_RARO', 'RECHAZA_CARGA' FROM abet.carga LIMIT 1
$q$, '23514', 'ck_rechazo_fila_motivo'),
('R61', 'rechazo CODIGO_VACIO con el PI 5.1 del plan en pi_id, que solo admiten PI_DEL_PLAN_AUSENTE y PI_REPETIDO', $q$
 INSERT INTO abet.rechazo_fila (carga_id, fila_origen, motivo, efecto, pi_id)
 SELECT c.carga_id, 2, 'CODIGO_VACIO', 'RECHAZA_FILA', p.pi_id
 FROM abet.carga c JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
      AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx',
      abet.pi p
 WHERE p.codigo = '5.1'
$q$, '23514', 'ck_rechazo_fila_pi'),
('R62', 'rechazo PI_REPETIDO con un pi_id que no existe en abet.pi', $q$
 INSERT INTO abet.rechazo_fila (carga_id, fila_origen, motivo, efecto, pi_id)
 SELECT c.carga_id, NULL, 'PI_REPETIDO', 'RECHAZA_CARGA', (SELECT max(pi_id) + 1000 FROM abet.pi)
 FROM abet.carga c JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
      AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
$q$, '23503', 'fk_rechazo_fila_pi'),
('R63', 'encabezado «ABET SO 5.10 …» para el PI 5.1: el prefijo no deja que «5.10» pase como 5.1 (V1_10, J-19)', $q$
 UPDATE abet.carga_columna cc SET encabezado = 'ABET SO 5.10 [Total Pts: 100 Score] |9000051'
 FROM abet.pi p WHERE p.pi_id = cc.pi_id AND p.codigo = '5.1'
$q$, '23514', 'ck_carga_columna_encabezado'),
('R64', 'encabezado «Actividad 5.1 …»: una palabra distinta de ABET, SO y PI antes del código (V1_10, J-19)', $q$
 UPDATE abet.carga_columna cc SET encabezado = 'Actividad 5.1 [Total Pts: 4 Score] |9000051'
 FROM abet.pi p WHERE p.pi_id = cc.pi_id AND p.codigo = '5.1'
$q$, '23514', 'ck_carga_columna_encabezado'),
('R65', 'encabezado «ABET SO 5.1» sin el corchete que sigue al código (V1_10, J-19)', $q$
 UPDATE abet.carga_columna cc SET encabezado = 'ABET SO 5.1'
 FROM abet.pi p WHERE p.pi_id = cc.pi_id AND p.codigo = '5.1'
$q$, '23514', 'ck_carga_columna_encabezado');

DO $$
DECLARE
    c             record;
    v_sqlstate    text;
    v_restriccion text;
    v_ok          int := 0;
BEGIN
    FOR c IN SELECT * FROM caso_rechazo ORDER BY id LOOP
        v_sqlstate := NULL;
        v_restriccion := NULL;
        BEGIN
            EXECUTE c.sentencia;
        EXCEPTION WHEN others THEN
            GET STACKED DIAGNOSTICS v_sqlstate = RETURNED_SQLSTATE, v_restriccion = CONSTRAINT_NAME;
        END;
        IF v_sqlstate IS NULL THEN
            RAISE EXCEPTION 'FALLA %: se aceptó %', c.id, c.descripcion;
        ELSIF v_sqlstate <> c.sqlstate OR (c.restriccion IS NOT NULL AND v_restriccion IS DISTINCT FROM c.restriccion) THEN
            RAISE EXCEPTION 'FALLA %: % falló por % (%) y se esperaba % (%)',
                c.id, c.descripcion, v_restriccion, v_sqlstate, c.restriccion, c.sqlstate;
        END IF;
        v_ok := v_ok + 1;
        RAISE NOTICE 'ok % rechazado: % (%)', c.id, c.descripcion, coalesce(c.restriccion, 'NOT NULL');
    END LOOP;
    RAISE NOTICE 'ok %/% casos de rechazo', v_ok, (SELECT count(*) FROM caso_rechazo);
END $$;

-- ---------------------------------------------------------------------------------------------
-- 6. Consultas de control que deben devolver 0 filas (las mismas corren en CI)
-- ---------------------------------------------------------------------------------------------
CREATE TEMP TABLE control_cero (id text PRIMARY KEY, descripcion text NOT NULL, consulta text NOT NULL);
INSERT INTO control_cero VALUES
('Q01', 'filas leídas distintas de las filas de datos del archivo (C1)', $q$
 SELECT c.carga_id FROM abet.carga c JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
 WHERE c.estado IN ('PUBLICADA', 'REEMPLAZADA') AND c.filas_leidas <> ao.filas_de_datos
$q$),
('Q02', 'columna con menos o más mediciones que filas aceptadas (C1; un rechazo descarta la fila completa)', $q$
 SELECT cc.carga_columna_id FROM abet.carga_columna cc JOIN abet.carga c ON c.carga_id = cc.carga_id
 LEFT JOIN abet.medicion m ON m.carga_columna_id = cc.carga_columna_id
 WHERE c.estado IN ('PUBLICADA', 'REEMPLAZADA')
 GROUP BY cc.carga_columna_id, c.filas_aceptadas HAVING count(m.medicion_id) <> c.filas_aceptadas
$q$),
('Q03', 'filas rechazadas sin su registro de rechazo', $q$
 SELECT c.carga_id FROM abet.carga c
 LEFT JOIN abet.rechazo_fila r ON r.carga_id = c.carga_id AND r.efecto = 'RECHAZA_FILA'
 GROUP BY c.carga_id, c.filas_rechazadas HAVING count(DISTINCT r.fila_origen) <> c.filas_rechazadas
$q$),
('Q04', 'columnas con nombres de personas o datos de contacto (privacidad)', $q$
 SELECT table_name, column_name FROM information_schema.columns
 WHERE table_schema = 'abet'
   AND (column_name ~ '(apellido|first_name|last_name|correo|email|telefono|dni)'
        OR (table_name IN ('estudiante', 'medicion', 'carga', 'rechazo_fila', 'carga_columna') AND column_name LIKE '%nombre%'))
$q$),
('Q05', 'asignatura con planes de dos versiones de catálogo de la misma carrera en el mismo periodo (H26)', $q$
 SELECT pm.periodo_id, pm.asignatura_id, pm.carrera_id FROM abet.plan_medicion pm
 GROUP BY pm.periodo_id, pm.asignatura_id, pm.carrera_id HAVING count(DISTINCT pm.catalogo_version_id) > 1
$q$),
('Q06', 'carga PUBLICADA o REEMPLAZADA sin columnas reconocidas', $q$
 SELECT c.carga_id FROM abet.carga c
 WHERE c.estado IN ('PUBLICADA', 'REEMPLAZADA')
   AND NOT EXISTS (SELECT 1 FROM abet.carga_columna cc WHERE cc.carga_id = c.carga_id)
$q$),
('Q07', 'carga publicada que dice reemplazar a otra que no quedó REEMPLAZADA (H57)', $q$
 SELECT c.carga_id FROM abet.carga c JOIN abet.carga ant ON ant.carga_id = c.reemplaza_carga_id
 WHERE c.estado IN ('PUBLICADA', 'REEMPLAZADA') AND ant.estado <> 'REEMPLAZADA'
$q$),
('Q08', 'estudiante y PI en cargas publicadas de dos secciones del mismo curso y periodo', $q$
 SELECT m.estudiante_id, m.pi_id, s.periodo_id, s.asignatura_id
 FROM abet.medicion m JOIN abet.carga c ON c.carga_id = m.carga_id JOIN abet.seccion s ON s.seccion_id = c.seccion_id
 WHERE c.estado = 'PUBLICADA'
 GROUP BY m.estudiante_id, m.pi_id, s.periodo_id, s.asignatura_id HAVING count(DISTINCT s.seccion_id) > 1
$q$),
('Q09', 'parámetro CONVERSION_NIVEL_0_1 DEFINIDO sin sus 4 niveles', $q$
 SELECT pv.conjunto_reglas_id FROM abet.parametro_valor pv
 LEFT JOIN abet.conversion_nivel_0_1 cn ON cn.conjunto_reglas_id = pv.conjunto_reglas_id
 WHERE pv.clave = 'CONVERSION_NIVEL_0_1' AND pv.estado = 'DEFINIDO'
 GROUP BY pv.conjunto_reglas_id HAVING count(cn.nivel_original) <> 4
$q$),
('Q10', 'cargas publicadas del mismo curso, periodo y carrera con conjuntos de reglas distintos', $q$
 SELECT s.periodo_id, s.asignatura_id, c.carrera_id
 FROM abet.carga c JOIN abet.seccion s ON s.seccion_id = c.seccion_id
 WHERE c.estado = 'PUBLICADA'
 GROUP BY s.periodo_id, s.asignatura_id, c.carrera_id HAVING count(DISTINCT c.conjunto_reglas_id) > 1
$q$),
('Q11', 'conjunto de reglas APROBADO con algún parámetro sin DEFINIR', $q$
 SELECT cr.conjunto_reglas_id, p.clave
 FROM abet.conjunto_reglas cr CROSS JOIN abet.parametro p
 LEFT JOIN abet.parametro_valor pv ON pv.conjunto_reglas_id = cr.conjunto_reglas_id AND pv.clave = p.clave
 WHERE cr.estado = 'APROBADO' AND pv.estado IS DISTINCT FROM 'DEFINIDO'
$q$),
('Q12', 'fila aceptada fuera del rango de filas de datos del archivo', $q$
 SELECT f.carga_id, f.fila_origen FROM abet.carga_fila f JOIN abet.carga c ON c.carga_id = f.carga_id
 WHERE f.fila_origen > c.filas_de_datos + 1
$q$),
('Q13', 'carga PUBLICADA o REEMPLAZADA con filas aceptadas distintas de sus filas registradas', $q$
 SELECT c.carga_id FROM abet.carga c LEFT JOIN abet.carga_fila f ON f.carga_id = c.carga_id
 WHERE c.estado IN ('PUBLICADA', 'REEMPLAZADA')
 GROUP BY c.carga_id, c.filas_aceptadas HAVING count(f.fila_origen) <> c.filas_aceptadas
$q$),
('Q14', 'carga REEMPLAZADA sin ninguna carga que la reemplace (H57)', $q$
 SELECT a.carga_id FROM abet.carga a
 WHERE a.estado = 'REEMPLAZADA' AND NOT EXISTS (SELECT 1 FROM abet.carga n WHERE n.reemplaza_carga_id = a.carga_id)
$q$);

-- Cada consulta de control nueva debe ver el caso que vigila. Se arma en una transacción que se deshace.
BEGIN;
INSERT INTO abet.archivo_origen (sha256, nombre_archivo, filas_de_datos)
VALUES (encode(sha256(convert_to('sondeo rechazada', 'UTF8')), 'hex'), 'sondeo_rechazada.csv', 1),
       (encode(sha256(convert_to('sondeo sin columnas', 'UTF8')), 'hex'), 'sondeo_sin_columnas.csv', 1),
       (encode(sha256(convert_to('sondeo 411', 'UTF8')), 'hex'), 'sondeo_411.csv', 1);
-- Q06 y Q07: carga PUBLICADA sin columnas que reemplaza a una carga RECHAZADA de la misma sección.
INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version, estado, terminada_en)
SELECT s.seccion_id, ao.archivo_id, 1, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba', 'RECHAZADA', now()
FROM abet.seccion s JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002',
     abet.archivo_origen ao, abet.conjunto_reglas cr
WHERE s.numero = '301' AND ao.nombre_archivo = 'sondeo_rechazada.csv' AND cr.version = 'R-2026-BORRADOR';
INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version, estado,
                        reemplaza_carga_id, filas_leidas, filas_aceptadas, terminada_en)
SELECT c.seccion_id, ao.archivo_id, 1, c.carrera_id, c.conjunto_reglas_id, 'v0.0.0-prueba', 'PUBLICADA', c.carga_id, 1, 1, now()
FROM abet.carga c JOIN abet.archivo_origen r ON r.archivo_id = c.archivo_id AND r.nombre_archivo = 'sondeo_rechazada.csv',
     abet.archivo_origen ao
WHERE ao.nombre_archivo = 'sondeo_sin_columnas.csv';
-- Q08: el estudiante 99000001 también aparece con el PI 5.1 en la sección 411 del mismo curso y periodo.
-- Q10: la 411 se publica con R-PRUEBA-APROBADO mientras la 410 sigue con R-2026-BORRADOR.
-- La 411 ya existe cuando la base trae los datos de 2026-2, y entonces el INSERT no hace nada. La 410 y la 411 se buscan
-- con su asignatura y no solo por su número, porque 450010 también tiene una 410 (C13).
INSERT INTO abet.seccion (periodo_id, asignatura_id, numero)
SELECT s.periodo_id, s.asignatura_id, '411'
FROM abet.seccion s JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002'
WHERE s.numero = '410'
ON CONFLICT DO NOTHING;
INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version)
SELECT s.seccion_id, ao.archivo_id, 1, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba'
FROM abet.seccion s JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002',
     abet.archivo_origen ao, abet.conjunto_reglas cr
WHERE s.numero = '411' AND ao.nombre_archivo = 'sondeo_411.csv' AND cr.version = 'R-PRUEBA-APROBADO';
INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id, pi_id,
                                pi_codigo, posicion, encabezado)
SELECT c.carga_id, s.seccion_id, c.carrera_id, s.periodo_id, s.asignatura_id, pm.plan_medicion_id, pm.pi_id,
       p.codigo, 5, '5.1 [Total Pts: 4 Score] |9000451'
FROM abet.carga c JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sondeo_411.csv'
JOIN abet.seccion s ON s.seccion_id = c.seccion_id
JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id AND pm.carrera_id = c.carrera_id
JOIN abet.pi p ON p.pi_id = pm.pi_id AND p.codigo = '5.1';
INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id)
SELECT c.carga_id, 2, e.estudiante_id
FROM abet.carga c JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sondeo_411.csv',
     abet.estudiante e
WHERE e.codigo = '99000001';
INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
SELECT cc.carga_id, cc.carga_columna_id, cc.pi_id, e.estudiante_id, 'CALIFICADO', 3, 2
FROM abet.carga_columna cc JOIN abet.carga c ON c.carga_id = cc.carga_id
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sondeo_411.csv',
     abet.estudiante e
WHERE e.codigo = '99000001';
UPDATE abet.carga c SET estado = 'PUBLICADA', filas_leidas = 1, filas_aceptadas = 1, terminada_en = now()
FROM abet.archivo_origen ao WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sondeo_411.csv';
-- Q12 y Q13: una fila 50 en un archivo de una sola fila de datos, que además deja dos filas para una aceptada.
INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id)
SELECT c.carga_id, 50, e.estudiante_id
FROM abet.carga c JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sondeo_411.csv',
     abet.estudiante e
WHERE e.codigo = '99000002';
-- Q14: la carga publicada sin columnas pasa a REEMPLAZADA sin que otra la reemplace (Q06 y Q07 la siguen viendo).
UPDATE abet.carga c SET estado = 'REEMPLAZADA'
FROM abet.archivo_origen ao WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sondeo_sin_columnas.csv';
-- Q09: la conversión pasa a DEFINIDO sin ninguna fila.
UPDATE abet.parametro_valor SET estado = 'DEFINIDO' WHERE clave = 'CONVERSION_NIVEL_0_1';
-- Q11: el conjunto aprobado vuelve a dejar CORTE_ROJO PENDIENTE.
UPDATE abet.parametro_valor pv SET estado = 'PENDIENTE', valor_numero = NULL
FROM abet.conjunto_reglas cr
WHERE cr.conjunto_reglas_id = pv.conjunto_reglas_id AND cr.version = 'R-PRUEBA-APROBADO' AND pv.clave = 'CORTE_ROJO';
DO $$
DECLARE
    q   record;
    v_n bigint;
BEGIN
    FOR q IN SELECT * FROM control_cero WHERE id IN ('Q06', 'Q07', 'Q08', 'Q09', 'Q10', 'Q11', 'Q12', 'Q13', 'Q14') ORDER BY id LOOP
        EXECUTE 'SELECT count(*) FROM (' || q.consulta || ') AS t' INTO v_n;
        IF v_n = 0 THEN
            RAISE EXCEPTION 'FALLA %: no detectó el caso que vigila (%)', q.id, q.descripcion;
        END IF;
        RAISE NOTICE 'ok % detecta su caso (% filas)', q.id, v_n;
    END LOOP;
END $$;
ROLLBACK;

DO $$
DECLARE
    q   record;
    v_n bigint;
BEGIN
    FOR q IN SELECT * FROM control_cero ORDER BY id LOOP
        EXECUTE 'SELECT count(*) FROM (' || q.consulta || ') AS t' INTO v_n;
        IF v_n <> 0 THEN
            RAISE EXCEPTION 'FALLA %: % devolvió % filas', q.id, q.descripcion, v_n;
        END IF;
        RAISE NOTICE 'ok % 0 filas: %', q.id, q.descripcion;
    END LOOP;
END $$;

-- Q15 (US-04). El filtro de columnas de Q04 aplicado al esquema acceso solo encuentra el correo de
-- usuario_autorizado, que es el único dato de contacto de la base.
DO $$
BEGIN
    IF (SELECT string_agg(table_name || '.' || column_name, ',' ORDER BY table_name, column_name)
          FROM information_schema.columns
         WHERE table_schema = 'acceso'
           AND (column_name ~ '(apellido|first_name|last_name|correo|email|telefono|dni)'
                OR (table_name IN ('estudiante', 'medicion', 'carga', 'rechazo_fila', 'carga_columna') AND column_name LIKE '%nombre%')))
       IS DISTINCT FROM 'usuario_autorizado.correo' THEN
        RAISE EXCEPTION 'FALLA Q15: en acceso solo usuario_autorizado.correo debe pasar el filtro de Q04';
    END IF;
    RAISE NOTICE 'ok Q15 el filtro de Q04 sobre acceso solo encuentra usuario_autorizado.correo';
END $$;

-- db/plataforma/neon/controles_neon.sql debe traer Q01 a Q14 iguales a las de arriba, salvo espacios, cada una sola
-- entre su \echo y su \set qNN :ROW_COUNT, y su cierre debe sumar las catorce (T025). Las órdenes de psql que fijan
-- variables en ese archivo son solo \set ON_ERROR_STOP 1, un \set qNN :ROW_COUNT por consulta y el \gset del cierre,
-- sin repetirse. Así, un \set qNN de más, un \set que no lee :ROW_COUNT, un control que falta, una condición agregada
-- a una consulta o una consulta comentada rompen la prueba. correr_pruebas.sh pasa la ruta del archivo en la variable
-- controles_neon; sin ella, la comparación se salta con un aviso.
\if :{?controles_neon}
\set texto_controles_neon `cat :'controles_neon'`
CREATE TEMP TABLE texto_controles_neon AS SELECT CAST(:'texto_controles_neon' AS text) AS texto;
DO $$
DECLARE
    q        record;
    v_crudo  text;
    v_bloque text;
    v_suma   text;
    v_sobra  text;
    v_falta  text;
BEGIN
    SELECT texto INTO v_crudo FROM texto_controles_neon;
    -- Cada orden que fija variables, con el resto de su línea y los espacios reducidos a uno, aun dentro de un
    -- comentario, frente a las que el archivo debe traer. EXCEPT ALL cuenta las repetidas.
    WITH archivo AS (
        SELECT btrim(regexp_replace(m[1], '\s+', ' ', 'g')) AS orden
        FROM regexp_matches(v_crudo, '(\\(?:set|gset|getenv|prompt|unset)\M[^\n]*)', 'g') AS m
    ), esperado AS (
        SELECT '\set ON_ERROR_STOP 1' AS orden
        UNION ALL SELECT '\set ' || lower(id) || ' :ROW_COUNT' FROM control_cero
        UNION ALL SELECT '\gset'
    )
    SELECT (SELECT string_agg(orden, ' | ' ORDER BY orden COLLATE "C")
              FROM (SELECT orden FROM archivo EXCEPT ALL SELECT orden FROM esperado) AS s),
           (SELECT string_agg(orden, ' | ' ORDER BY orden COLLATE "C")
              FROM (SELECT orden FROM esperado EXCEPT ALL SELECT orden FROM archivo) AS f)
      INTO v_sobra, v_falta;
    IF v_sobra IS NOT NULL OR v_falta IS NOT NULL THEN
        RAISE EXCEPTION 'FALLA controles_neon.sql: las órdenes que fijan variables no son las esperadas (sobra %; falta %)',
            coalesce(v_sobra, 'nada'), coalesce(v_falta, 'nada');
    END IF;
    FOR q IN SELECT * FROM control_cero ORDER BY id LOOP
        v_bloque := (regexp_match(v_crudo, '\\echo ''' || q.id || '\.[^\n]*\n(.*?)\n\\set ' || lower(q.id)
                                           || ' :ROW_COUNT\n'))[1];
        IF v_bloque IS NULL OR btrim(regexp_replace(v_bloque, '\s+', ' ', 'g'))
                               IS DISTINCT FROM btrim(regexp_replace(q.consulta, '\s+', ' ', 'g')) || ';' THEN
            RAISE EXCEPTION 'FALLA %: controles_neon.sql no trae entre su \echo y su \set la misma consulta que pruebas.sql', q.id;
        END IF;
    END LOOP;
    SELECT '(' || string_agg(':' || lower(id), ' + ' ORDER BY id) || ') = 0' INTO v_suma FROM control_cero;
    IF position('SELECT ' || v_suma || ' AS controles_en_cero \gset' IN regexp_replace(v_crudo, '\s+', ' ', 'g')) = 0 THEN
        RAISE EXCEPTION 'FALLA controles_neon.sql: su cierre no suma las catorce consultas como %', v_suma;
    END IF;
    RAISE NOTICE 'ok controles_neon.sql trae Q01 a Q14 iguales a las de pruebas.sql, cada una con su único \set qNN :ROW_COUNT, solo las órdenes esperadas que fijan variables y el cierre que las suma todas';
END $$;
\else
\echo '  aviso: sin -v controles_neon=<ruta> no se compara controles_neon.sql con estas consultas'
\endif

-- ---------------------------------------------------------------------------------------------
-- 7. R-17 del export con error de la sección 410 (60,0 / 60,0 / 70,0), junto al del export correcto de la sección 3
-- ---------------------------------------------------------------------------------------------
-- export_inventado_410_con_error.xlsx trae los mismos 11 estudiantes con un 5 en el PI 5.2 de la fila 3 (99000002).
-- La fila completa queda fuera con NIVEL_FUERA_DE_ESCALA y RECHAZA_FILA, así que la carga lee 11 filas, acepta 10,
-- guarda 30 mediciones y el R-17 da 6 de 10, 6 de 10 y 7 de 10. La 410 admite una sola carga PUBLICADA, así que la
-- carga entra como reemplazo de la del export correcto, y la transacción se deshace al final (US-10 y US-15).
BEGIN;
INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)
VALUES (encode(sha256(convert_to('export inventado 2026-2 450002 410 con error', 'UTF8')), 'hex'),
        'export_inventado_410_con_error.xlsx', 'gc_SINTETICO_20262_450002_410_f', 11);

INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version,
                        reemplaza_carga_id, subida_por)
SELECT a.seccion_id, ao.archivo_id, ao.filas_de_datos, a.carrera_id, a.conjunto_reglas_id, 'v0.0.0-prueba', a.carga_id,
       u.usuario_id
FROM abet.carga a
JOIN abet.archivo_origen aa ON aa.archivo_id = a.archivo_id AND aa.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'export_inventado_410_con_error.xlsx'
JOIN acceso.usuario_autorizado u ON u.correo = 'docente410@example.invalid';

-- Las mismas tres columnas del export correcto, con el Total Pts de 20 en el PI 5.3.
INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id, pi_id,
                                pi_codigo, posicion, encabezado, bb_columna_id, puntaje_maximo_declarado)
SELECT b.carga_id, cc.seccion_id, cc.carrera_id, cc.periodo_id, cc.asignatura_id, cc.plan_medicion_id, cc.pi_id,
       cc.pi_codigo, cc.posicion, cc.encabezado, cc.bb_columna_id, cc.puntaje_maximo_declarado
FROM abet.carga b
JOIN abet.archivo_origen bo ON bo.archivo_id = b.archivo_id AND bo.nombre_archivo = 'export_inventado_410_con_error.xlsx'
JOIN abet.carga_columna cc ON cc.carga_id = b.reemplaza_carga_id;

-- El rechazo de la fila 3 en la columna de 5.2 y el aviso de 5.3, sin el valor leído.
INSERT INTO abet.rechazo_fila (carga_id, fila_origen, carga_columna_id, motivo, efecto)
SELECT cc.carga_id, v.fila, cc.carga_columna_id, v.motivo, v.efecto
FROM (VALUES ('5.2', 3, 'NIVEL_FUERA_DE_ESCALA', 'RECHAZA_FILA'), ('5.3', NULL, 'PUNTAJE_MAXIMO_DISTINTO', 'AVISO'))
     AS v (pi, fila, motivo, efecto)
JOIN abet.carga_columna cc ON cc.pi_codigo = v.pi
JOIN abet.carga b ON b.carga_id = cc.carga_id
JOIN abet.archivo_origen bo ON bo.archivo_id = b.archivo_id AND bo.nombre_archivo = 'export_inventado_410_con_error.xlsx';

-- Las 10 filas aceptadas y sus 30 mediciones, con los mismos niveles del export correcto salvo la fila 3.
INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id)
SELECT b.carga_id, f.fila_origen, f.estudiante_id
FROM abet.carga b
JOIN abet.archivo_origen bo ON bo.archivo_id = b.archivo_id AND bo.nombre_archivo = 'export_inventado_410_con_error.xlsx'
JOIN abet.carga_fila f ON f.carga_id = b.reemplaza_carga_id
WHERE f.fila_origen <> 3;

INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
SELECT b.carga_id, nc.carga_columna_id, m.pi_id, m.estudiante_id, m.estado_evidencia, m.nivel_original, m.fila_origen
FROM abet.carga b
JOIN abet.archivo_origen bo ON bo.archivo_id = b.archivo_id AND bo.nombre_archivo = 'export_inventado_410_con_error.xlsx'
JOIN abet.medicion m ON m.carga_id = b.reemplaza_carga_id AND m.fila_origen <> 3
JOIN abet.carga_columna nc ON nc.carga_id = b.carga_id AND nc.pi_id = m.pi_id;

UPDATE abet.carga a SET estado = 'REEMPLAZADA'
FROM abet.archivo_origen aa
WHERE aa.archivo_id = a.archivo_id AND aa.nombre_archivo = 'sintetico_20262_450002_410.xlsx';

UPDATE abet.carga b
SET estado = 'PUBLICADA', filas_leidas = 11, filas_aceptadas = 10, filas_rechazadas = 1, terminada_en = clock_timestamp()
FROM abet.archivo_origen bo
WHERE bo.archivo_id = b.archivo_id AND bo.nombre_archivo = 'export_inventado_410_con_error.xlsx';

DO $$
DECLARE
    r   record;
    q   record;
    v_n int := 0;
    v_c bigint;
BEGIN
    FOR r IN
        SELECT v.pi, v.n_total, v.n_esperado_o_superior, v.n_sin_evidencia, v.pct_logro_sobre_calificados,
               v.pct_logro_sobre_total_con_sin_evidencia, v.provisional, ao.nombre_archivo, e.*
        FROM abet.v_r17_por_pi v
        JOIN abet.carga c ON c.carga_id = v.carga_id
        JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
        JOIN (VALUES ('5.1', 6, 60.0), ('5.2', 6, 60.0), ('5.3', 7, 70.0)) AS e (pi_e, ok_e, pct_e) ON e.pi_e = v.pi
        WHERE v.periodo = '2026-2' AND v.codigo_asignatura = '450002' AND v.seccion = '410'
        ORDER BY v.pi
    LOOP
        v_n := v_n + 1;
        IF r.nombre_archivo <> 'export_inventado_410_con_error.xlsx' OR r.n_total <> 10 OR r.n_sin_evidencia <> 0
           OR r.n_esperado_o_superior <> r.ok_e OR r.pct_logro_sobre_calificados <> r.pct_e
           OR r.pct_logro_sobre_total_con_sin_evidencia <> r.pct_e OR r.provisional IS NOT TRUE THEN
            RAISE EXCEPTION 'FALLA R-17 con error en PI %: %', r.pi, r;
        END IF;
        RAISE NOTICE 'ok R-17 con error PI %: % de 10 en nivel 3 o más = % %%', r.pi, r.n_esperado_o_superior,
                     r.pct_logro_sobre_calificados;
    END LOOP;
    IF v_n <> 3 THEN
        RAISE EXCEPTION 'FALLA R-17 con error: se esperaban 3 PI en la sección 410 y hay %', v_n;
    END IF;
    -- 30 filas de medición, 3 PI por 10 estudiantes, sin el estudiante de la fila 3.
    IF (SELECT sum(n_total) FROM abet.v_r17_por_pi WHERE codigo_asignatura = '450002' AND seccion = '410') <> 30
       OR (SELECT count(*) FROM abet.v_tabla_maestra_pi
            WHERE "CÓDIGO DEL CURSO" = '450002' AND "SECCIÓN" = '410'
              AND "ARCHIVO" = 'export_inventado_410_con_error.xlsx') <> 30
       OR EXISTS (SELECT 1 FROM abet.v_tabla_maestra_pi
                   WHERE "SECCIÓN" = '410' AND "CÓDIGO DEL ESTUDIANTE" = '99000002') THEN
        RAISE EXCEPTION 'FALLA R-17 con error: se esperaban 30 filas de medición sin el estudiante de la fila 3';
    END IF;
    -- Lo que muestra la constancia: 11 / 10 / 1, quién sube la carga, el rechazo de la fila 3 en 5.2 y el aviso de 5.3.
    IF (SELECT c.filas_leidas || '/' || c.filas_aceptadas || '/' || c.filas_rechazadas || ' ' || u.correo
          FROM abet.carga c
          JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
                                     AND ao.nombre_archivo = 'export_inventado_410_con_error.xlsx'
          JOIN acceso.usuario_autorizado u ON u.usuario_id = c.subida_por)
       IS DISTINCT FROM '11/10/1 docente410@example.invalid'
       OR (SELECT string_agg(rf.motivo || ':' || rf.efecto || ':' || coalesce(CAST(rf.fila_origen AS text), '-') || ':'
                             || cc.pi_codigo, ',' ORDER BY rf.motivo)
             FROM abet.rechazo_fila rf
             JOIN abet.carga c ON c.carga_id = rf.carga_id
             JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
                                        AND ao.nombre_archivo = 'export_inventado_410_con_error.xlsx'
             JOIN abet.carga_columna cc ON cc.carga_columna_id = rf.carga_columna_id)
          IS DISTINCT FROM 'NIVEL_FUERA_DE_ESCALA:RECHAZA_FILA:3:5.2,PUNTAJE_MAXIMO_DISTINTO:AVISO:-:5.3' THEN
        RAISE EXCEPTION 'FALLA R-17 con error: la carga debe quedar en 11 / 10 / 1, subida por docente410, con el rechazo de la fila 3 y el aviso de 5.3';
    END IF;
    -- Q01 a Q14 en cero con la carga del export con error publicada y la del export correcto REEMPLAZADA.
    FOR q IN SELECT * FROM control_cero ORDER BY id LOOP
        EXECUTE 'SELECT count(*) FROM (' || q.consulta || ') AS t' INTO v_c;
        IF v_c <> 0 THEN
            RAISE EXCEPTION 'FALLA R-17 con error: % devolvió % filas (%)', q.id, v_c, q.descripcion;
        END IF;
    END LOOP;
    RAISE NOTICE 'ok R-17 del export con error: 11 / 10 / 1, 30 mediciones sin la fila 3 y Q01 a Q14 en 0 filas';
END $$;
ROLLBACK;

-- ---------------------------------------------------------------------------------------------
-- 8. Q08 con la 410 y la 411 publicadas (FR-030)
-- ---------------------------------------------------------------------------------------------
-- export_inventado_411.xlsx, de tests/datos_inventados/, trae los códigos 99000012 a 99000022 y los niveles de la 410
-- en orden inverso, así que su R-17 repite 63,6 / 63,6 / 72,7 sin ningún estudiante de la 410. La carga de la 411 se
-- publica junto a la de la 410 en una transacción que se deshace al final, y Q01 a Q14, Q08 entre ellas, deben
-- seguir en 0 filas (US-02 y US-06).
BEGIN;
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

-- Las tres columnas del export, con los mismos ids de Blackboard inventados de la 410 y el Total Pts de 20 en 5.3.
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

-- Niveles por fila (5.1, 5.2, 5.3) del export. 99000012 lleva los de 99000011 y 99000022 los de 99000001.
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

DO $$
DECLARE
    r   record;
    q   record;
    v_n int := 0;
    v_c bigint;
BEGIN
    FOR r IN
        SELECT v.pi, v.n_total, v.n_esperado_o_superior, v.pct_logro_sobre_calificados, v.provisional,
               v.n_nivel_1, v.n_nivel_2, v.n_nivel_3, v.n_nivel_4, e.*
        FROM abet.v_r17_por_pi v
        JOIN (VALUES ('5.1', 7, 63.6, 1, 3, 4, 3), ('5.2', 7, 63.6, 1, 3, 4, 3), ('5.3', 8, 72.7, 1, 2, 5, 3))
             AS e (pi_e, ok_e, pct_e, n1_e, n2_e, n3_e, n4_e) ON e.pi_e = v.pi
        WHERE v.periodo = '2026-2' AND v.codigo_asignatura = '450002' AND v.seccion = '411'
        ORDER BY v.pi
    LOOP
        v_n := v_n + 1;
        IF r.n_total <> 11 OR r.n_esperado_o_superior <> r.ok_e OR r.pct_logro_sobre_calificados <> r.pct_e
           OR r.provisional IS NOT TRUE
           OR (r.n_nivel_1, r.n_nivel_2, r.n_nivel_3, r.n_nivel_4) IS DISTINCT FROM (r.n1_e, r.n2_e, r.n3_e, r.n4_e) THEN
            RAISE EXCEPTION 'FALLA R-17 de la 411 en PI %: %', r.pi, r;
        END IF;
        RAISE NOTICE 'ok R-17 de la 411 PI %: % de 11 en nivel 3 o más = % %%', r.pi, r.n_esperado_o_superior,
                     r.pct_logro_sobre_calificados;
    END LOOP;
    IF v_n <> 3 THEN
        RAISE EXCEPTION 'FALLA R-17 de la 411: se esperaban 3 PI en la sección 411 y hay %', v_n;
    END IF;
    -- Las dos secciones publicadas, cada una con sus 33 mediciones y sus propios estudiantes.
    IF (SELECT string_agg(s.numero || ':' || (SELECT count(*) FROM abet.medicion m WHERE m.carga_id = c.carga_id), ','
                          ORDER BY s.numero)
          FROM abet.carga c JOIN abet.seccion s ON s.seccion_id = c.seccion_id
          JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002'
         WHERE c.estado = 'PUBLICADA') IS DISTINCT FROM '410:33,411:33'
       OR (SELECT min("CÓDIGO DEL ESTUDIANTE") || '-' || max("CÓDIGO DEL ESTUDIANTE")
             FROM abet.v_tabla_maestra_pi WHERE "CÓDIGO DEL CURSO" = '450002' AND "SECCIÓN" = '411')
          IS DISTINCT FROM '99000012-99000022' THEN
        RAISE EXCEPTION 'FALLA Q08 con dos secciones: la 410 y la 411 deben quedar PUBLICADAS con 33 mediciones cada una y la 411 con 99000012 a 99000022';
    END IF;
    FOR q IN SELECT * FROM control_cero ORDER BY id LOOP
        EXECUTE 'SELECT count(*) FROM (' || q.consulta || ') AS t' INTO v_c;
        IF v_c <> 0 THEN
            RAISE EXCEPTION 'FALLA Q08 con dos secciones: % devolvió % filas (%)', q.id, v_c, q.descripcion;
        END IF;
    END LOOP;
    RAISE NOTICE 'ok Q08 con la 410 y la 411 publicadas: 33 mediciones en cada una, 63,6 / 63,6 / 72,7 en la 411 y Q01 a Q14 en 0 filas';
END $$;
ROLLBACK;

-- ---------------------------------------------------------------------------------------------
-- 9. Cada export del profesor con varias secciones publicado en su sección (BR-ACCESO-07 y BR-CARGA-11)
-- ---------------------------------------------------------------------------------------------
-- sintetico_20262_450002_412.xlsx, sintetico_20262_450010_410.xlsx y sintetico_20262_450010_412.xlsx, de
-- tests/datos_inventados/, traen 11 filas cada uno, con los códigos 99000023 a 99000033, 99000034 a 99000044 y
-- 99000045 a 99000055, y las tres columnas del plan de su asignatura con Total Pts 4 en las posiciones 25 a 27. Las
-- tres cargas, subidas por docente.varias@example.invalid, se publican junto a la de la 410 de 450002 en una
-- transacción que se deshace al final. Cada sección queda con una sola carga PUBLICADA y con su propio R-17, la 412 de
-- 450002 y la 412 de 450010 no se mezclan, la 410 de 450002 conserva sus cifras y Q01 a Q14, Q08 entre ellas, siguen
-- en 0 filas. tests/test_generador_exports.py comprueba que las columnas y los niveles de abajo son los de los tres
-- exports.
BEGIN;
INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)
SELECT encode(sha256(convert_to('export inventado 2026-2 ' || v.asignatura || ' ' || v.numero, 'UTF8')), 'hex'),
       'sintetico_20262_' || v.asignatura || '_' || v.numero || '.xlsx',
       'gc_SINTETICO_20262_' || v.asignatura || '_' || v.numero || '_f', 11
FROM (VALUES ('450002', '412'), ('450010', '410'), ('450010', '412')) AS v (asignatura, numero);

-- Una carga por sección de docente.varias, con el archivo cuyo nombre declara su asignatura y su número.
INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version, subida_por)
SELECT s.seccion_id, ao.archivo_id, ao.filas_de_datos, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba', u.usuario_id
FROM acceso.usuario_autorizado u
JOIN acceso.docente_seccion d ON d.usuario_id = u.usuario_id
JOIN abet.seccion s ON s.seccion_id = d.seccion_id
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'sintetico_20262_' || a.codigo || '_' || s.numero || '.xlsx'
JOIN abet.conjunto_reglas cr ON cr.version = 'R-2026-BORRADOR'
WHERE u.correo = 'docente.varias@example.invalid';

-- Las columnas de cada export, con el id de Blackboard del curso de su sección.
INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id, pi_id,
                                pi_codigo, posicion, encabezado, bb_columna_id, puntaje_maximo_declarado)
SELECT c.carga_id, s.seccion_id, c.carrera_id, s.periodo_id, s.asignatura_id, pm.plan_medicion_id, pm.pi_id,
       p.codigo, v.posicion, p.codigo || ' [Total Pts: 4 Score] |' || v.bb_id, v.bb_id, 4
FROM (VALUES ('sintetico_20262_450002_412.xlsx', '5.1', 25, '9001051'),
             ('sintetico_20262_450002_412.xlsx', '5.2', 26, '9001052'),
             ('sintetico_20262_450002_412.xlsx', '5.3', 27, '9001053'),
             ('sintetico_20262_450010_410.xlsx', '2.1', 25, '9002021'),
             ('sintetico_20262_450010_410.xlsx', '2.2', 26, '9002022'),
             ('sintetico_20262_450010_410.xlsx', '5.1', 27, '9002051'),
             ('sintetico_20262_450010_412.xlsx', '2.1', 25, '9003021'),
             ('sintetico_20262_450010_412.xlsx', '2.2', 26, '9003022'),
             ('sintetico_20262_450010_412.xlsx', '5.1', 27, '9003051')) AS v (archivo, pi, posicion, bb_id)
JOIN abet.archivo_origen ao ON ao.nombre_archivo = v.archivo
JOIN abet.carga c ON c.archivo_id = ao.archivo_id
JOIN abet.seccion s ON s.seccion_id = c.seccion_id
JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
                          AND pm.carrera_id = c.carrera_id
JOIN abet.pi p ON p.pi_id = pm.pi_id AND p.codigo = v.pi;

INSERT INTO abet.estudiante (codigo)
SELECT CAST(99000000 + n AS varchar(8)) FROM generate_series(23, 55) AS g (n);

-- Fila del export, código y niveles de las columnas 25, 26 y 27 (5.1, 5.2 y 5.3 en 450002, y 2.1, 2.2 y 5.1 en
-- 450010).
CREATE TEMP TABLE nivel_varias AS
SELECT * FROM (VALUES
 ('sintetico_20262_450002_412.xlsx',  2, '99000023', 4, 3, 4),
 ('sintetico_20262_450002_412.xlsx',  3, '99000024', 3, 2, 4),
 ('sintetico_20262_450002_412.xlsx',  4, '99000025', 4, 4, 3),
 ('sintetico_20262_450002_412.xlsx',  5, '99000026', 3, 1, 4),
 ('sintetico_20262_450002_412.xlsx',  6, '99000027', 2, 2, 3),
 ('sintetico_20262_450002_412.xlsx',  7, '99000028', 3, 3, 4),
 ('sintetico_20262_450002_412.xlsx',  8, '99000029', 4, 2, 2),
 ('sintetico_20262_450002_412.xlsx',  9, '99000030', 1, 1, 3),
 ('sintetico_20262_450002_412.xlsx', 10, '99000031', 3, 3, 4),
 ('sintetico_20262_450002_412.xlsx', 11, '99000032', 3, 4, 3),
 ('sintetico_20262_450002_412.xlsx', 12, '99000033', 4, 3, 4),
 ('sintetico_20262_450010_410.xlsx',  2, '99000034', 3, 2, 2),
 ('sintetico_20262_450010_410.xlsx',  3, '99000035', 4, 3, 1),
 ('sintetico_20262_450010_410.xlsx',  4, '99000036', 2, 1, 2),
 ('sintetico_20262_450010_410.xlsx',  5, '99000037', 4, 4, 3),
 ('sintetico_20262_450010_410.xlsx',  6, '99000038', 3, 2, 1),
 ('sintetico_20262_450010_410.xlsx',  7, '99000039', 1, 1, 2),
 ('sintetico_20262_450010_410.xlsx',  8, '99000040', 4, 3, 3),
 ('sintetico_20262_450010_410.xlsx',  9, '99000041', 3, 2, 4),
 ('sintetico_20262_450010_410.xlsx', 10, '99000042', 2, 2, 1),
 ('sintetico_20262_450010_410.xlsx', 11, '99000043', 4, 4, 2),
 ('sintetico_20262_450010_410.xlsx', 12, '99000044', 3, 3, 3),
 ('sintetico_20262_450010_412.xlsx',  2, '99000045', 4, 3, 3),
 ('sintetico_20262_450010_412.xlsx',  3, '99000046', 3, 2, 1),
 ('sintetico_20262_450010_412.xlsx',  4, '99000047', 4, 4, 4),
 ('sintetico_20262_450010_412.xlsx',  5, '99000048', 3, 3, 2),
 ('sintetico_20262_450010_412.xlsx',  6, '99000049', 2, 1, 2),
 ('sintetico_20262_450010_412.xlsx',  7, '99000050', 4, 3, 4),
 ('sintetico_20262_450010_412.xlsx',  8, '99000051', 3, 2, 1),
 ('sintetico_20262_450010_412.xlsx',  9, '99000052', 4, 3, 3),
 ('sintetico_20262_450010_412.xlsx', 10, '99000053', 3, 4, 2),
 ('sintetico_20262_450010_412.xlsx', 11, '99000054', 4, 2, 4),
 ('sintetico_20262_450010_412.xlsx', 12, '99000055', 3, 3, 3)
) AS v (archivo, fila, codigo, n25, n26, n27);

INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id)
SELECT c.carga_id, v.fila, e.estudiante_id
FROM nivel_varias v
JOIN abet.archivo_origen ao ON ao.nombre_archivo = v.archivo
JOIN abet.carga c ON c.archivo_id = ao.archivo_id
JOIN abet.estudiante e ON e.codigo = v.codigo;

INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
SELECT cc.carga_id, cc.carga_columna_id, cc.pi_id, f.estudiante_id, 'CALIFICADO',
       CASE cc.posicion WHEN 25 THEN v.n25 WHEN 26 THEN v.n26 ELSE v.n27 END, v.fila
FROM nivel_varias v
JOIN abet.archivo_origen ao ON ao.nombre_archivo = v.archivo
JOIN abet.carga c ON c.archivo_id = ao.archivo_id
JOIN abet.carga_fila f ON f.carga_id = c.carga_id AND f.fila_origen = v.fila
JOIN abet.carga_columna cc ON cc.carga_id = c.carga_id;

UPDATE abet.carga c
SET estado = 'PUBLICADA', filas_leidas = 11, filas_aceptadas = 11, filas_rechazadas = 0, terminada_en = clock_timestamp()
FROM abet.archivo_origen ao
WHERE ao.archivo_id = c.archivo_id
  AND ao.nombre_archivo IN ('sintetico_20262_450002_412.xlsx', 'sintetico_20262_450010_410.xlsx',
                            'sintetico_20262_450010_412.xlsx');

DO $$
DECLARE
    r   record;
    q   record;
    v_n int := 0;
    v_c bigint;
BEGIN
    -- Cifras del R-17 por sección y PI, que tests/datos_inventados/README.md anota como esperadas.
    FOR r IN
        SELECT v.codigo_asignatura, v.seccion, v.pi, v.n_total, v.n_esperado_o_superior, v.pct_logro_sobre_calificados,
               v.provisional, v.n_nivel_1, v.n_nivel_2, v.n_nivel_3, v.n_nivel_4, e.*
        FROM abet.v_r17_por_pi v
        JOIN (VALUES ('450002', '412', '5.1',  9, 81.8, 1, 1, 5, 4),
                     ('450002', '412', '5.2',  6, 54.5, 2, 3, 4, 2),
                     ('450002', '412', '5.3', 10, 90.9, 0, 1, 4, 6),
                     ('450010', '410', '2.1',  8, 72.7, 1, 2, 4, 4),
                     ('450010', '410', '2.2',  5, 45.5, 2, 4, 3, 2),
                     ('450010', '410', '5.1',  4, 36.4, 3, 4, 3, 1),
                     ('450010', '412', '2.1', 10, 90.9, 0, 1, 5, 5),
                     ('450010', '412', '2.2',  7, 63.6, 1, 3, 5, 2),
                     ('450010', '412', '5.1',  6, 54.5, 2, 3, 3, 3))
             AS e (asignatura_e, seccion_e, pi_e, ok_e, pct_e, n1_e, n2_e, n3_e, n4_e)
          ON e.asignatura_e = v.codigo_asignatura AND e.seccion_e = v.seccion AND e.pi_e = v.pi
        WHERE v.periodo = '2026-2'
        ORDER BY v.codigo_asignatura, v.seccion, v.pi
    LOOP
        v_n := v_n + 1;
        IF r.n_total <> 11 OR r.n_esperado_o_superior <> r.ok_e OR r.pct_logro_sobre_calificados <> r.pct_e
           OR r.provisional IS NOT TRUE
           OR (r.n_nivel_1, r.n_nivel_2, r.n_nivel_3, r.n_nivel_4) IS DISTINCT FROM (r.n1_e, r.n2_e, r.n3_e, r.n4_e) THEN
            RAISE EXCEPTION 'FALLA R-17 de la % de % en el PI %: %', r.seccion, r.codigo_asignatura, r.pi, r;
        END IF;
        RAISE NOTICE 'ok R-17 de la % de % PI %: % de 11 en nivel 3 o más = % %%', r.seccion, r.codigo_asignatura,
                     r.pi, r.n_esperado_o_superior, r.pct_logro_sobre_calificados;
    END LOOP;
    IF v_n <> 9
       OR (SELECT count(*) FROM abet.v_r17_por_pi
            WHERE periodo = '2026-2'
              AND (codigo_asignatura, seccion) IN (('450002', '412'), ('450010', '410'), ('450010', '412'))) <> 9 THEN
        RAISE EXCEPTION 'FALLA R-17 de varias secciones: se esperaban 9 filas, 3 PI en cada sección, y hay %', v_n;
    END IF;
    -- Una sola carga PUBLICADA en cada sección de 450002 y 450010, con sus 33 mediciones y quien la sube.
    IF (SELECT string_agg(a.codigo || '-' || s.numero || '=' || (SELECT count(*) FROM abet.medicion m WHERE m.carga_id = c.carga_id)
                          || '=' || coalesce(u.correo, 'sin usuario'), ',' ORDER BY a.codigo COLLATE "C", s.numero COLLATE "C")
          FROM abet.carga c
          JOIN abet.seccion s ON s.seccion_id = c.seccion_id
          JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo IN ('450002', '450010')
          LEFT JOIN acceso.usuario_autorizado u ON u.usuario_id = c.subida_por
         WHERE c.estado = 'PUBLICADA')
       IS DISTINCT FROM '450002-410=33=sin usuario,450002-412=33=docente.varias@example.invalid,'
                        || '450010-410=33=docente.varias@example.invalid,450010-412=33=docente.varias@example.invalid' THEN
        RAISE EXCEPTION 'FALLA varias secciones: cada sección de 450002 y 450010 debe tener una sola carga PUBLICADA con 33 mediciones';
    END IF;
    -- La 412 de 450002 y la 412 de 450010 no se mezclan, y cada sección muestra sus PI y sus propios códigos.
    IF (SELECT string_agg(t.linea, ',' ORDER BY t.linea COLLATE "C")
          FROM (SELECT "CÓDIGO DEL CURSO" || '-' || "SECCIÓN" || '=' || string_agg(DISTINCT "PI", ' ' ORDER BY "PI")
                       || '=' || min("CÓDIGO DEL ESTUDIANTE") || '-' || max("CÓDIGO DEL ESTUDIANTE") || '=' || count(*)
                       AS linea
                  FROM abet.v_tabla_maestra_pi
                 WHERE "AÑO" = 2026 AND "CICLO" = 2
                   AND ("CÓDIGO DEL CURSO", "SECCIÓN") IN (('450002', '412'), ('450010', '410'), ('450010', '412'))
                 GROUP BY "CÓDIGO DEL CURSO", "SECCIÓN") AS t)
       IS DISTINCT FROM '450002-412=5.1 5.2 5.3=99000023-99000033=33,450010-410=2.1 2.2 5.1=99000034-99000044=33,'
                        || '450010-412=2.1 2.2 5.1=99000045-99000055=33' THEN
        RAISE EXCEPTION 'FALLA varias secciones: la tabla maestra debe separar las tres secciones con sus PI y sus códigos';
    END IF;
    -- La 410 de 450002 conserva el R-17 del export correcto aunque 450010 también tenga una 410 publicada.
    IF (SELECT string_agg(pi || '=' || pct_logro_sobre_calificados, ',' ORDER BY pi)
          FROM abet.v_r17_por_pi WHERE periodo = '2026-2' AND codigo_asignatura = '450002' AND seccion = '410')
       IS DISTINCT FROM '5.1=63.6,5.2=63.6,5.3=72.7' THEN
        RAISE EXCEPTION 'FALLA varias secciones: la 410 de 450002 debe seguir con 63,6 / 63,6 / 72,7';
    END IF;
    FOR q IN SELECT * FROM control_cero ORDER BY id LOOP
        EXECUTE 'SELECT count(*) FROM (' || q.consulta || ') AS t' INTO v_c;
        IF v_c <> 0 THEN
            RAISE EXCEPTION 'FALLA varias secciones: % devolvió % filas (%)', q.id, v_c, q.descripcion;
        END IF;
    END LOOP;
    RAISE NOTICE 'ok varias secciones: tres cargas PUBLICADAS de docente.varias@example.invalid, una en cada sección, con sus cifras propias, la 410 de 450002 sin cambios y Q01 a Q14 en 0 filas';
END $$;
ROLLBACK;

\echo 'TODAS LAS PRUEBAS PASARON'
