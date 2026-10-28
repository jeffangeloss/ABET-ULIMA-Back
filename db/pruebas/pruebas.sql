-- Pruebas de la entrega 1. Se corren sobre una base desechable con las migraciones y los datos sintéticos.
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
$q$, '23503', 'fk_rechazo_fila_columna');

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
INSERT INTO abet.seccion (periodo_id, asignatura_id, numero) SELECT periodo_id, asignatura_id, '411' FROM abet.seccion WHERE numero = '410';
INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version)
SELECT s.seccion_id, ao.archivo_id, 1, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba'
FROM abet.seccion s, abet.archivo_origen ao, abet.conjunto_reglas cr
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

\echo 'TODAS LAS PRUEBAS PASARON'
