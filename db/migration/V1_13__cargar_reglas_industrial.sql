-- V1_13  Conjunto de reglas R-2026-BORRADOR de Ingeniería Industrial (solo datos, spec 008, US-68 y FR-005).
-- abet_carga/carga.py busca el conjunto de CONJUNTO_REGLAS para la carrera del plan de medición, y V1_06 lo siembra
-- solo para Ambiental, así que sin esta migración la primera carga de 5643 termina en ConfiguracionInvalida. El
-- conjunto de Industrial repite los parámetros de V1_06, que son los de los R-17 llenados a mano (meta 0,80 y nivel
-- esperado 3), y deja PENDIENTE lo que la carrera todavía no decide, sin valores inventados. Va después de V1_12, que
-- crea la carrera IND, y la aserción final detiene la migración si la carrera falta o el conjunto no queda completo.

INSERT INTO abet.conjunto_reglas (carrera_id, version, estado)
SELECT carrera_id, 'R-2026-BORRADOR', 'BORRADOR'
FROM abet.carrera
WHERE codigo = 'IND';

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
JOIN abet.carrera c ON c.carrera_id = cr.carrera_id AND c.codigo = 'IND';

-- Aserción de carga. El conjunto de IND queda con los cinco parámetros, dos de ellos DEFINIDOS.
DO $$
DECLARE
    v_texto text;
BEGIN
    SELECT string_agg(pv.clave || '=' || pv.estado, ',' ORDER BY pv.clave) INTO v_texto
    FROM abet.parametro_valor pv
    JOIN abet.conjunto_reglas cr ON cr.conjunto_reglas_id = pv.conjunto_reglas_id AND cr.version = 'R-2026-BORRADOR'
    JOIN abet.carrera c ON c.carrera_id = cr.carrera_id AND c.codigo = 'IND';
    IF v_texto IS DISTINCT FROM 'CONVERSION_NIVEL_0_1=PENDIENTE,CORTE_ROJO=PENDIENTE,META_LOGRO=DEFINIDO,'
                                || 'NIVEL_ESPERADO=DEFINIDO,TRATO_SIN_EVIDENCIA=PENDIENTE' THEN
        RAISE EXCEPTION 'R-2026-BORRADOR de IND no quedó con sus cinco parámetros (%)', coalesce(v_texto, 'ninguno');
    END IF;
END
$$;
