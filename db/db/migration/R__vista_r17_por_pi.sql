-- R__vista_r17_por_pi  Números del R-17 por carga PUBLICADA y PI, recalculados desde la base.
-- Cubre H12 y C12 (valores calculados, sin fórmulas copiadas), H80 (un PI planificado sin medición
-- sale sin porcentaje, nunca como logrado), H71 (conteo por nivel 1 a 4 sin transformar) y H08 (SIN_EVIDENCIA
-- se cuenta aparte y se muestran los dos porcentajes mientras la carrera decide). El nivel esperado y la meta
-- salen del conjunto de reglas de la carga; si el nivel esperado no está DEFINIDO, los conteos contra el
-- esperado y los porcentajes salen NULL, nunca 0. La columna provisional es verdadera mientras el conjunto
-- de reglas no esté APROBADO o le falte DEFINIR NIVEL_ESPERADO, META_LOGRO o TRATO_SIN_EVIDENCIA.
-- pct_logro_segun_regla toma el porcentaje que fija TRATO_SIN_EVIDENCIA y sale NULL mientras esté PENDIENTE.
-- Migración repetible: Flyway la vuelve a aplicar cada vez que cambia su contenido.

DROP VIEW IF EXISTS abet.v_r17_por_pi CASCADE;

CREATE VIEW abet.v_r17_por_pi AS
WITH regla AS (
    SELECT cr.conjunto_reglas_id,
           cr.version,
           CAST(MAX(CASE WHEN pv.clave = 'NIVEL_ESPERADO' AND pv.estado = 'DEFINIDO' THEN pv.valor_numero END) AS smallint) AS nivel_esperado,
           MAX(CASE WHEN pv.clave = 'META_LOGRO' AND pv.estado = 'DEFINIDO' THEN pv.valor_numero END) AS meta_logro,
           MAX(CASE WHEN pv.clave = 'TRATO_SIN_EVIDENCIA' AND pv.estado = 'DEFINIDO' THEN pv.valor_texto END) AS trato_sin_evidencia,
           -- Oficial solo con el conjunto APROBADO y los tres parámetros que usa la vista DEFINIDOS.
           cr.estado <> 'APROBADO'
           OR COUNT(CASE WHEN pv.clave IN ('NIVEL_ESPERADO', 'META_LOGRO', 'TRATO_SIN_EVIDENCIA')
                          AND pv.estado = 'DEFINIDO' THEN 1 END) < 3 AS provisional
    FROM abet.conjunto_reglas cr
    LEFT JOIN abet.parametro_valor pv ON pv.conjunto_reglas_id = cr.conjunto_reglas_id
    GROUP BY cr.conjunto_reglas_id, cr.version, cr.estado
),
conteo AS (
    SELECT c.carga_id,
           pm.pi_id,
           r.version AS conjunto_reglas,
           r.nivel_esperado,
           r.meta_logro,
           r.trato_sin_evidencia,
           r.provisional,
           SUM(CASE WHEN m.nivel_original = 1 THEN 1 ELSE 0 END)                        AS n_nivel_1,
           SUM(CASE WHEN m.nivel_original = 2 THEN 1 ELSE 0 END)                        AS n_nivel_2,
           SUM(CASE WHEN m.nivel_original = 3 THEN 1 ELSE 0 END)                        AS n_nivel_3,
           SUM(CASE WHEN m.nivel_original = 4 THEN 1 ELSE 0 END)                        AS n_nivel_4,
           -- Sin nivel esperado DEFINIDO no hay con qué comparar: NULL, no 0.
           CASE WHEN r.nivel_esperado IS NOT NULL
                THEN SUM(CASE WHEN m.nivel_original < r.nivel_esperado THEN 1 ELSE 0 END) END  AS n_debajo_del_esperado,
           CASE WHEN r.nivel_esperado IS NOT NULL
                THEN SUM(CASE WHEN m.nivel_original >= r.nivel_esperado THEN 1 ELSE 0 END) END AS n_esperado_o_superior,
           SUM(CASE WHEN m.estado_evidencia = 'SIN_EVIDENCIA' THEN 1 ELSE 0 END)        AS n_sin_evidencia,
           SUM(CASE WHEN m.estado_evidencia = 'CALIFICADO' THEN 1 ELSE 0 END)           AS n_calificados,
           COUNT(m.medicion_id)                                                         AS n_total
    FROM abet.carga c
    JOIN abet.seccion s        ON s.seccion_id = c.seccion_id
    -- Solo los PI del plan de la carrera de la carga.
    JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
                              AND pm.carrera_id = c.carrera_id
    JOIN regla r               ON r.conjunto_reglas_id = c.conjunto_reglas_id
    LEFT JOIN abet.carga_columna cc ON cc.carga_id = c.carga_id AND cc.pi_id = pm.pi_id
    LEFT JOIN abet.medicion m       ON m.carga_columna_id = cc.carga_columna_id
    WHERE c.estado = 'PUBLICADA'
    GROUP BY c.carga_id, pm.pi_id, r.version, r.nivel_esperado, r.meta_logro, r.trato_sin_evidencia, r.provisional
),
porcentaje AS (
    SELECT k.*,
           ROUND(100.0 * k.n_esperado_o_superior / NULLIF(k.n_calificados, 0), 1) AS pct_sobre_calificados,
           ROUND(100.0 * k.n_esperado_o_superior / NULLIF(k.n_total, 0), 1)       AS pct_sobre_total
    FROM conteo k
)
SELECT pe.codigo                AS periodo,
       a.codigo                 AS codigo_asignatura,
       a.nombre                 AS asignatura,
       s.numero                 AS seccion,
       k.carga_id,
       k.conjunto_reglas,
       k.provisional,
       p.so_numero              AS so,
       p.codigo                 AS pi,
       k.nivel_esperado,
       k.n_nivel_1,
       k.n_nivel_2,
       k.n_nivel_3,
       k.n_nivel_4,
       k.n_debajo_del_esperado,
       k.n_esperado_o_superior,
       k.n_sin_evidencia,
       k.n_total,
       k.pct_sobre_calificados  AS pct_logro_sobre_calificados,
       k.pct_sobre_total        AS pct_logro_sobre_total_con_sin_evidencia,
       k.trato_sin_evidencia,
       -- El porcentaje que vale según la regla; NULL mientras TRATO_SIN_EVIDENCIA esté PENDIENTE.
       CASE k.trato_sin_evidencia
            WHEN 'CUENTA_COMO_NO_LOGRADO'     THEN k.pct_sobre_total
            WHEN 'SE_EXCLUYE_DEL_DENOMINADOR' THEN k.pct_sobre_calificados
       END                      AS pct_logro_segun_regla,
       ROUND(100.0 * k.meta_logro, 1) AS meta_logro_pct
FROM porcentaje k
JOIN abet.carga c      ON c.carga_id = k.carga_id
JOIN abet.seccion s    ON s.seccion_id = c.seccion_id
JOIN abet.periodo pe   ON pe.periodo_id = s.periodo_id
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
JOIN abet.pi p         ON p.pi_id = k.pi_id;

COMMENT ON VIEW abet.v_r17_por_pi IS 'R-17 por carga PUBLICADA y PI. Muestra el porcentaje sobre calificados, el porcentaje sobre el total con SIN_EVIDENCIA y el que vale según TRATO_SIN_EVIDENCIA (NULL mientras esté PENDIENTE, H08). Es provisional mientras el conjunto de reglas no esté APROBADO con NIVEL_ESPERADO, META_LOGRO y TRATO_SIN_EVIDENCIA DEFINIDOS; sin NIVEL_ESPERADO DEFINIDO los porcentajes son NULL.';
