-- Datos sintéticos para las pruebas. Todo es inventado: ningún código, nombre ni id de Blackboard real.
-- Imitan la forma del export de la sección 410 de 450002 en 2026-2 (PI 5.1, 5.2 y 5.3) con 11 estudiantes
-- inventados (99000001 a 99000011) y la misma distribución agregada del caso real:
--   PI 5.1  4 en niveles 1-2 y 7 en niveles 3-4  (63,6 %)
--   PI 5.2  4 en niveles 1-2 y 7 en niveles 3-4  (63,6 %)
--   PI 5.3  3 en niveles 1-2 y 8 en niveles 3-4  (72,7 %)
-- La columna 5.3 declara Total Pts 20 aunque guarda notas 1-4, como el export real; se registra un AVISO.
-- Se aplica con psql -1 (una sola transacción) después de las migraciones.

-- Versión de catálogo que rige en 2026-2 para Ambiental (dato operativo, como el plan)
INSERT INTO abet.catalogo_vigencia (periodo_id, carrera_id, catalogo_version_id)
SELECT pe.periodo_id, cv.carrera_id, cv.catalogo_version_id
FROM abet.periodo pe, abet.catalogo_version cv
WHERE pe.codigo = '2026-2' AND cv.codigo = 'AMB-2026';

-- Sección y plan de medición del periodo
INSERT INTO abet.seccion (periodo_id, asignatura_id, numero, curso_blackboard)
SELECT pe.periodo_id, a.asignatura_id, '410', 'SINTETICO_20262_450002_410'
FROM abet.periodo pe, abet.asignatura a
WHERE pe.codigo = '2026-2' AND a.codigo = '450002';

INSERT INTO abet.plan_medicion (periodo_id, asignatura_id, carrera_id, catalogo_version_id, so_id, pi_id, instrumento_id)
SELECT pe.periodo_id, a.asignatura_id, cv.carrera_id, cv.catalogo_version_id, p.so_id, p.pi_id, aso.instrumento_id
FROM abet.periodo pe
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026'
JOIN abet.asignatura a ON a.codigo IN ('450002', '450020')
JOIN abet.pi p ON p.catalogo_version_id = cv.catalogo_version_id
JOIN abet.asignatura_so aso ON aso.catalogo_version_id = cv.catalogo_version_id
                           AND aso.asignatura_id = a.asignatura_id AND aso.so_id = p.so_id
WHERE pe.codigo = '2026-2'
  AND ((a.codigo = '450002' AND p.codigo IN ('5.1', '5.2', '5.3'))
    OR (a.codigo = '450020' AND p.codigo = '1.1'));

-- Archivo y carga
INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)
VALUES (encode(sha256(convert_to('sintetico 2026-2 450002 410', 'UTF8')), 'hex'),
        'sintetico_20262_450002_410.xlsx', 'sintetico_20262_450002_410', 11);

INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version)
SELECT s.seccion_id, ao.archivo_id, ao.filas_de_datos, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba'
FROM abet.seccion s
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002'
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
JOIN abet.conjunto_reglas cr ON cr.version = 'R-2026-BORRADOR'
WHERE s.numero = '410';

-- Columnas de PI reconocidas (ids de Blackboard inventados)
INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id, pi_id,
                                pi_codigo, posicion, encabezado, bb_columna_id, puntaje_maximo_declarado)
SELECT c.carga_id, s.seccion_id, c.carrera_id, s.periodo_id, s.asignatura_id, pm.plan_medicion_id, pm.pi_id,
       p.codigo, v.posicion, v.pi || ' [Total Pts: ' || v.puntos || ' Score] |' || v.bb_id, v.bb_id, v.puntos
FROM (VALUES ('5.1', 5, '9000051', 4), ('5.2', 6, '9000052', 4), ('5.3', 7, '9000053', 20))
     AS v (pi, posicion, bb_id, puntos)
JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
JOIN abet.carga c ON c.archivo_id = ao.archivo_id
JOIN abet.seccion s ON s.seccion_id = c.seccion_id
JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
                          AND pm.carrera_id = c.carrera_id
JOIN abet.pi p ON p.pi_id = pm.pi_id AND p.codigo = v.pi;

INSERT INTO abet.rechazo_fila (carga_id, fila_origen, carga_columna_id, motivo, efecto)
SELECT cc.carga_id, NULL, cc.carga_columna_id, 'PUNTAJE_MAXIMO_DISTINTO', 'AVISO'
FROM abet.carga_columna cc
JOIN abet.pi p ON p.pi_id = cc.pi_id AND p.codigo = '5.3'
JOIN abet.carga c ON c.carga_id = cc.carga_id
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx';

-- Estudiantes inventados
INSERT INTO abet.estudiante (codigo)
SELECT CAST(99000000 + n AS varchar(8)) FROM generate_series(1, 11) AS g (n);

-- Filas aceptadas: 99000001 está en la fila 2 y 99000011 en la fila 12
INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id)
SELECT c.carga_id, CAST(e.codigo AS integer) - 99000000 + 1, e.estudiante_id
FROM abet.estudiante e
JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
JOIN abet.carga c ON c.archivo_id = ao.archivo_id
WHERE e.codigo BETWEEN '99000001' AND '99000011';

-- Niveles por estudiante (fila del archivo, nivel en 5.1, 5.2 y 5.3)
INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original, fila_origen)
SELECT cc.carga_id, cc.carga_columna_id, cc.pi_id, e.estudiante_id, 'CALIFICADO',
       CASE p.codigo WHEN '5.1' THEN v.n51 WHEN '5.2' THEN v.n52 ELSE v.n53 END, v.fila
FROM (VALUES
 ('99000001',  2, 3, 4, 3),
 ('99000002',  3, 4, 3, 4),
 ('99000003',  4, 2, 3, 3),
 ('99000004',  5, 3, 2, 3),
 ('99000005',  6, 1, 2, 2),
 ('99000006',  7, 4, 3, 4),
 ('99000007',  8, 3, 4, 3),
 ('99000008',  9, 2, 1, 1),
 ('99000009', 10, 4, 3, 4),
 ('99000010', 11, 3, 4, 3),
 ('99000011', 12, 2, 2, 2)
) AS v (codigo, fila, n51, n52, n53)
JOIN abet.estudiante e ON e.codigo = v.codigo
JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx'
JOIN abet.carga c ON c.archivo_id = ao.archivo_id
JOIN abet.carga_columna cc ON cc.carga_id = c.carga_id
JOIN abet.pi p ON p.pi_id = cc.pi_id;

-- Cierre de la carga: 11 filas leídas, 11 aceptadas, 0 rechazadas
UPDATE abet.carga c
SET estado = 'PUBLICADA', filas_leidas = 11, filas_aceptadas = 11, filas_rechazadas = 0, terminada_en = now()
FROM abet.archivo_origen ao
WHERE ao.archivo_id = c.archivo_id AND ao.nombre_archivo = 'sintetico_20262_450002_410.xlsx';
