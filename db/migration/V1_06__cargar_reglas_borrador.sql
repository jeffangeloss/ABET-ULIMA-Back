-- V1_06  Conjunto de reglas inicial en BORRADOR (solo datos).
-- Fija solo lo que la plantilla R-17 ya usa (meta 0,80 y nivel esperado 3); lo que la carrera
-- todavía no decide queda PENDIENTE, sin valores inventados (H08, H01, corte rojo del semáforo).

INSERT INTO abet.parametro (clave, tipo, descripcion) VALUES
 ('META_LOGRO',           'NUMERO', 'Proporción mínima de estudiantes en el nivel esperado o superior para dar el PI por logrado'),
 ('NIVEL_ESPERADO',       'NUMERO', 'Nivel de 1 a 4 desde el que un estudiante cuenta como logrado'),
 ('CORTE_ROJO',           'NUMERO', 'Proporción bajo la que el tablero pinta rojo el semáforo'),
 ('CONVERSION_NIVEL_0_1', 'TABLA',  'Conversión de los niveles 1 a 4 a la escala 0 a 1 (filas en conversion_nivel_0_1)'),
 ('TRATO_SIN_EVIDENCIA',  'TEXTO',  'Cómo cuenta en el porcentaje el estudiante sin evidencia (H08)');

INSERT INTO abet.conjunto_reglas (carrera_id, version, estado)
SELECT carrera_id, 'R-2026-BORRADOR', 'BORRADOR'
FROM abet.carrera
WHERE codigo = 'AMB';

INSERT INTO abet.parametro_valor (conjunto_reglas_id, clave, estado, valor_numero)
SELECT cr.conjunto_reglas_id, v.clave, v.estado, v.valor
FROM (VALUES
 ('META_LOGRO',           'DEFINIDO',  CAST(0.80 AS numeric(9, 4))),
 ('NIVEL_ESPERADO',       'DEFINIDO',  CAST(3 AS numeric(9, 4))),
 ('CORTE_ROJO',           'PENDIENTE', CAST(NULL AS numeric(9, 4))),
 ('CONVERSION_NIVEL_0_1', 'PENDIENTE', CAST(NULL AS numeric(9, 4))),
 ('TRATO_SIN_EVIDENCIA',  'PENDIENTE', CAST(NULL AS numeric(9, 4)))
) AS v (clave, estado, valor)
JOIN abet.conjunto_reglas cr ON cr.version = 'R-2026-BORRADOR'
JOIN abet.carrera c ON c.carrera_id = cr.carrera_id AND c.codigo = 'AMB';
