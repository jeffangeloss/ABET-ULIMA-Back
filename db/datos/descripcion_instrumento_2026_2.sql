-- Descripción del instrumento de medición de los PI 5.1, 5.2 y 5.3 de 450002 en 2026-2 (script de datos, no
-- migración; spec 005, US-51, J-31, AD-20 y BR-R17-11). Escribe un texto de prueba distinto en
-- abet.plan_medicion.descripcion_instrumento de cada PI, que el R-17 lleva a G17, G18 y G19. Cada texto empieza por
-- «Texto de prueba.», porque el contenido real lo decide la Coordinación de Ambiental (D-34) y este guion se
-- reemplaza entonces por otro con los textos aprobados. No trae nombres, correos ni códigos de estudiante.
-- Se corre con el usuario dueño de la base y la conexión directa, después de V1_11 y de
-- db/datos/periodo_2026_2_inventado.sql. En Neon lo corre Jefferson desde el Windows (ssh windows-worker), en la rama
-- develop y después en la principal, nunca desde la Mac. Se puede repetir, porque cada UPDATE fija el mismo texto
-- en la misma fila, y el bloque final detiene el script, y deshace todo, si un PI del plan falta o queda sin su texto.
--
--   psql "host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=verify-full sslrootcert=system" \
--        -X -v ON_ERROR_STOP=1 -f db/datos/descripcion_instrumento_2026_2.sql

\set ON_ERROR_STOP 1

BEGIN;

CREATE TEMPORARY TABLE descripcion_de_prueba (pi_codigo varchar(5) PRIMARY KEY, texto varchar(400) NOT NULL)
    ON COMMIT DROP;
INSERT INTO descripcion_de_prueba (pi_codigo, texto) VALUES
    ('5.1', 'Texto de prueba. Informe del trabajo integrador en el que el equipo identifica los aspectos ambientales '
            'del caso asignado y formula el problema con datos de campo. Se califica con la rúbrica del PI 5.1.'),
    ('5.2', 'Texto de prueba. Exposición del trabajo integrador en la que el equipo compara alternativas de solución '
            'y justifica la elegida con criterios técnicos y normativos. Se califica con la rúbrica del PI 5.2.'),
    ('5.3', 'Texto de prueba. Entrega final del trabajo integrador con el plan de implementación, sus indicadores y '
            'el presupuesto de la solución elegida. Se califica con la rúbrica del PI 5.3.');

UPDATE abet.plan_medicion pm
SET descripcion_instrumento = d.texto
FROM descripcion_de_prueba d, abet.pi p, abet.asignatura a, abet.periodo pe
WHERE p.pi_id = pm.pi_id AND p.codigo = d.pi_codigo
  AND a.asignatura_id = pm.asignatura_id AND a.codigo = '450002'
  AND pe.periodo_id = pm.periodo_id AND pe.codigo = '2026-2'
  AND pm.descripcion_instrumento IS DISTINCT FROM d.texto;

-- Cada PI del guion tiene su fila en el plan de 450002 en 2026-2 y queda con su texto.
DO $$
DECLARE
    v_con_texto integer;
BEGIN
    SELECT count(*) INTO v_con_texto
    FROM descripcion_de_prueba d
    JOIN abet.pi p ON p.codigo = d.pi_codigo
    JOIN abet.plan_medicion pm ON pm.pi_id = p.pi_id AND pm.descripcion_instrumento = d.texto
    JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id AND a.codigo = '450002'
    JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id AND pe.codigo = '2026-2';
    IF v_con_texto <> 3 THEN
        RAISE EXCEPTION 'El plan de 450002 en 2026-2 no tiene los PI 5.1, 5.2 y 5.3 con su descripción (% de 3).',
            v_con_texto;
    END IF;
END $$;

COMMIT;
