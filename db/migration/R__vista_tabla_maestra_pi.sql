-- R__vista_tabla_maestra_pi  Tabla_Maestra_PI con las columnas que Power BI espera hoy, más ESTADO DE EVIDENCIA.
-- Cubre H21 y C6 (PI como texto), C7 y C8 (SO y ciclo del curso desde el catálogo, no desde el número de sección)
-- y C9 (solo cargas PUBLICADAS, sin duplicados de cargas reemplazadas).
-- PROFESOR queda NULL en la entrega 1; docentes, roles y ámbitos entran en la entrega 2.
-- security_barrier impide que una función escrita por quien consulta se evalúe antes del filtro de la vista
-- y vea filas que la vista oculta, como las de cargas que no están PUBLICADAS.
-- Migración repetible: Flyway la vuelve a aplicar cada vez que cambia su contenido.

DROP VIEW IF EXISTS abet.v_tabla_maestra_pi CASCADE;

CREATE VIEW abet.v_tabla_maestra_pi WITH (security_barrier = true) AS
SELECT pe.anio                       AS "AÑO",
       pe.ciclo                      AS "CICLO",
       a.codigo                      AS "CÓDIGO DEL CURSO",
       a.nombre                      AS "CURSO",
       pes.ciclo_malla               AS "CICLO DEL CURSO",
       p.so_numero                   AS "SO",
       p.codigo                      AS "PI",
       CAST(NULL AS varchar(120))    AS "PROFESOR",
       e.codigo                      AS "CÓDIGO DEL ESTUDIANTE",
       s.numero                      AS "SECCIÓN",
       m.nivel_original              AS "CALIFICACIÓN",
       ao.nombre_archivo             AS "ARCHIVO",
       m.estado_evidencia            AS "ESTADO DE EVIDENCIA"
FROM abet.medicion m
JOIN abet.carga_columna cc  ON cc.carga_columna_id = m.carga_columna_id
JOIN abet.carga c           ON c.carga_id = m.carga_id
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
JOIN abet.seccion s         ON s.seccion_id = c.seccion_id
JOIN abet.periodo pe        ON pe.periodo_id = s.periodo_id
JOIN abet.asignatura a      ON a.asignatura_id = s.asignatura_id
JOIN abet.plan_medicion pm  ON pm.plan_medicion_id = cc.plan_medicion_id
JOIN abet.plan_estudios pes ON pes.catalogo_version_id = pm.catalogo_version_id AND pes.asignatura_id = pm.asignatura_id
JOIN abet.pi p              ON p.pi_id = m.pi_id
JOIN abet.estudiante e      ON e.estudiante_id = m.estudiante_id
WHERE c.estado = 'PUBLICADA';

COMMENT ON VIEW abet.v_tabla_maestra_pi IS 'Tabla_Maestra_PI para Power BI; solo cargas PUBLICADAS. PROFESOR es NULL hasta la entrega 2.';
