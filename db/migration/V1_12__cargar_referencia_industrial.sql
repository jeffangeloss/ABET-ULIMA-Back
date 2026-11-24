-- V1_12  Datos de referencia curriculares de Ingeniería Industrial (solo datos, spec 008, US-67).
-- GENERADO por herramientas/generar_v1_12.py desde referencia/industrial_2026.json; no se edita a mano.
-- SHA-256 del JSON de referencia: 90d387140e8b29443a0260c66bc24f8dc80ece226f64b679473981261bb1e59b
-- Carga la carrera IND, el catálogo IND-2026 en BORRADOR (D-50), sus SO y PI, el plan de estudios con el ciclo
-- de malla y los pares asignatura y SO, con el «Portafolio 3» de 5643 y SO 6. No trae rúbricas, competencias ni
-- estadíos. 15 asignaturas ya están en V1_03 y se reutilizan con su nombre, y las 38 nuevas se insertan aquí.

INSERT INTO abet.carrera (facultad_id, codigo, nombre)
SELECT facultad_id, 'IND', 'Ingeniería Industrial' FROM abet.facultad WHERE codigo = 'FI';

INSERT INTO abet.catalogo_version (carrera_id, codigo, estado, huella_fuente)
SELECT carrera_id, 'IND-2026', 'BORRADOR', '90d387140e8b29443a0260c66bc24f8dc80ece226f64b679473981261bb1e59b' FROM abet.carrera WHERE codigo = 'IND';

INSERT INTO abet.asignatura (codigo, nombre) VALUES
 ('510004', 'Ética Cívica'),
 ('530073', 'Proyecto de Ingeniería Aplicada II'),
 ('560012', 'Planeamiento y Control de Operaciones'),
 ('560038', 'Sistemas Organizacionales'),
 ('560039', 'Diseño Asistido por el Computador'),
 ('560043', 'Costeo de Operaciones'),
 ('560047', 'Cálculo III'),
 ('560048', 'Investigación de Operaciones I'),
 ('560049', 'Fundamentos de Operaciones y Logística'),
 ('560050', 'Ingeniería Económica'),
 ('560051', 'Electricidad y Electrónica'),
 ('560052', 'Ecuaciones Diferenciales'),
 ('560053', 'Diseño de Experimentos'),
 ('560054', 'Investigación de Operaciones II'),
 ('560055', 'Ergonomía y Diseño del Trabajo'),
 ('560056', 'Innovación en Ingeniería'),
 ('560057', 'Procesos Industriales'),
 ('560058', 'Ingeniería Financiera'),
 ('560059', 'Diseño de Instalaciones'),
 ('560061', 'Modelos de Sistemas Logísticos'),
 ('560062', 'Calidad/Quality'),
 ('560063', 'Procesos de Manufactura'),
 ('560064', 'Simulación de Procesos'),
 ('560065', 'Modelamiento Predictivo de Datos'),
 ('560067', 'Gestión de Proyectos'),
 ('560068', 'Análisis de Problemas de Ingeniería'),
 ('560069', 'Automatización Industrial'),
 ('560070', 'Ética y Gestión Humana'),
 ('560071', 'Proyecto de Ingeniería Aplicada I'),
 ('560072', 'Ingeniería Comercial/ Commercial Engineering'),
 ('560073', 'Proyecto de Ingeniería Aplicada II'),
 ('560074', 'Gerencia Estratégica / Strategic Management'),
 ('5647', 'Mecánica'),
 ('6382', 'Matemática Básica'),
 ('6505', 'Desarrollo Personal y Social'),
 ('6510', 'Economía y Empresa'),
 ('6512', 'Procesos Sociales y Políticos'),
 ('6513', 'Temas de Filosofía');

INSERT INTO abet.plan_estudios (catalogo_version_id, asignatura_id, ciclo_malla)
SELECT cv.catalogo_version_id, a.asignatura_id, v.ciclo_malla FROM (VALUES
 ('510003', 1),
 ('510004', 1),
 ('510005', 1),
 ('530073', 10),
 ('560012', 6),
 ('560038', 3),
 ('560039', 3),
 ('560040', 3),
 ('560041', 3),
 ('560042', 3),
 ('560043', 4),
 ('560044', 4),
 ('560045', 4),
 ('560046', 4),
 ('560047', 4),
 ('560048', 5),
 ('560049', 5),
 ('560050', 5),
 ('560051', 5),
 ('560052', 5),
 ('560053', 5),
 ('560054', 6),
 ('560055', 6),
 ('560056', 6),
 ('560057', 6),
 ('560058', 7),
 ('560059', 7),
 ('560060', 7),
 ('560061', 7),
 ('560062', 7),
 ('560063', 7),
 ('560064', 8),
 ('560065', 8),
 ('560066', 8),
 ('560067', 8),
 ('560068', 8),
 ('560069', 8),
 ('560070', 9),
 ('560071', 9),
 ('560072', 9),
 ('560073', 10),
 ('560074', 10),
 ('5643', 3),
 ('5647', 4),
 ('6382', 1),
 ('6384', 2),
 ('6503', 2),
 ('6505', 1),
 ('6508', 1),
 ('6510', 2),
 ('6511', 2),
 ('6512', 2),
 ('6513', 2)
) AS v (codigo, ciclo_malla)
JOIN abet.asignatura a ON a.codigo = v.codigo
JOIN abet.catalogo_version cv ON cv.codigo = 'IND-2026';

INSERT INTO abet.so (catalogo_version_id, numero, descripcion)
SELECT cv.catalogo_version_id, v.numero, v.descripcion FROM (VALUES
 (1, 'Habilidad para identificar, formular y resolver problemas de ingeniería complejos aplicando principios de ingeniería, ciencias y matemáticas.'),
 (2, 'Habilidad para aplicar diseños de ingeniería para producir soluciones que cumplan necesidades específicas considerando la salud, seguridad y el bienestar general, así como factores globales, culturales, sociales, ambientales y económicos.'),
 (3, 'Habilidad para comunicarse efectivamente ante una variedad de audiencias.'),
 (4, 'Habilidad para reconocer responsabilidades éticas y profesionales en situaciones de ingeniería y realizar juicios informados, los cuales deben considerar el impacto de soluciones de ingeniería en contextos globales, económicos, ambientales y sociales.'),
 (5, 'Habilidad para trabajar efectivamente en un equipo cuyos miembros provean liderazgo , la creación de un ambiente colaborativo e inclusivo, estableciendo metas, planificando tareas y trazando objetivos.'),
 (6, 'Habilidad para desarrollar y realizar experimentos apropiados, analizar e interpretar los datos y usar juicios de ingeniería para obtener conclusiones.'),
 (7, 'Habilidad para adquirir y aplicar nuevos conocimientos según sean necesarios, usando estrategias de aprendizaje apropiadas.')
) AS v (numero, descripcion)
JOIN abet.catalogo_version cv ON cv.codigo = 'IND-2026';

INSERT INTO abet.pi (catalogo_version_id, so_id, so_numero, numero, codigo, descripcion)
SELECT cv.catalogo_version_id, s.so_id, s.numero, v.numero, v.codigo, v.descripcion FROM (VALUES
 (1, 1, '1.1', 'Identifica, define, interpreta y formula un problema de ingeniería asociándolo a los principios de ingeniería, ciencias y matemáticas.'),
 (1, 2, '1.2', 'Formula, analiza y resuelve problemas de ingeniería aplicando principios de ingeniería, ciencias y matemáticas.'),
 (1, 3, '1.3', 'Formula, analiza y resuelve problemas de ingeniería complejos, aplicando principios de ingeniería, ciencias y matemáticas.'),
 (2, 1, '2.1', 'Define y comprende la importancia del diseño de ingeniería para proponer soluciones que resuelvan necesidades específicas de su entorno.'),
 (2, 2, '2.2', 'Aplica el diseño de ingeniería para proponer soluciones apropiadas que resuelvan necesidades específicas de su entorno.'),
 (2, 3, '2.3', 'Aplica el diseño de ingeniería para proponer soluciones que resuelvan necesidades específicas de su entorno considerando la salud, seguridad y el bienestar general, así como factores globales, culturales, sociales, ambientales y económicos.'),
 (3, 1, '3.1', 'Define y comprende la importancia de la comunicación efectiva en sus diversas modalidades: oral, escrita y corporal.'),
 (3, 2, '3.2', 'Demuestra habilidad para comunicarse de manera efectiva.'),
 (3, 3, '3.3', 'Aplica una comunicación efectiva ante una variedad de audiencias.'),
 (4, 1, '4.1', 'Reconoce responsabilidades éticas y profesionales en situaciones de ingeniería y realiza juicios informados sobre una situación determinada.'),
 (4, 2, '4.2', 'Demuestra conocimiento de responsabilidades éticas y profesionales, y aplica juicios informados en situaciones de ingeniería.'),
 (4, 3, '4.3', 'Propone soluciones de ingeniería en contextos globales, económicos, ambientales y sociales, que demuestran su responsabilidad ética, profesional y utilización de juicios informados.'),
 (5, 1, '5.1', 'Aprende a trabajar en equipo, desarrolla habilidades de liderazgo y trabaja de manera colaborativa.'),
 (5, 2, '5.2', 'Desarrolla proyectos de manera colaborativa, participa en la definición de objetivos y plan de acción para su logro.'),
 (5, 3, '5.3', 'Participa de manera efectiva en un equipo donde de manera colaborativa, contribuye con la definición de objetivos, metas y elaboración de un plan para su logro.'),
 (6, 1, '6.1', 'Desarrolla y realiza experimentos en el entorno de la ingeniería industrial.'),
 (6, 2, '6.2', 'Analiza e interpreta datos obtenidos de un experimento.'),
 (6, 3, '6.3', 'Diseña y realiza experimentos apropiados, analiza e interpreta los datos y usa juicios de ingeniería para obtener conclusiones.'),
 (7, 1, '7.1', 'Aprende a buscar nuevos conocimientos con un determinado propósito.'),
 (7, 2, '7.2', 'Aplica estrategias de aprendizaje apropiadas a un fin establecido.'),
 (7, 3, '7.3', 'Adquiere, consolida y aplica nuevos conocimientos, haciendo uso de estrategias de aprendizaje apropiadas para un propósito.')
) AS v (so_numero, numero, codigo, descripcion)
JOIN abet.catalogo_version cv ON cv.codigo = 'IND-2026'
JOIN abet.so s ON s.catalogo_version_id = cv.catalogo_version_id AND s.numero = v.so_numero;

INSERT INTO abet.instrumento (catalogo_version_id, nombre)
SELECT cv.catalogo_version_id, v.nombre FROM (VALUES
 ('Portafolio 3')
) AS v (nombre)
JOIN abet.catalogo_version cv ON cv.codigo = 'IND-2026';

INSERT INTO abet.asignatura_so (catalogo_version_id, asignatura_id, so_id, instrumento_id)
SELECT cv.catalogo_version_id, a.asignatura_id, s.so_id, i.instrumento_id FROM (VALUES
 ('510003', 3, NULL),
 ('510003', 5, NULL),
 ('510004', 1, NULL),
 ('510004', 4, NULL),
 ('510005', 1, NULL),
 ('530073', 6, NULL),
 ('560012', 2, NULL),
 ('560038', 2, NULL),
 ('560038', 7, NULL),
 ('560039', 2, NULL),
 ('560040', 2, NULL),
 ('560040', 5, NULL),
 ('560041', 6, NULL),
 ('560042', 1, NULL),
 ('560043', 3, NULL),
 ('560044', 6, NULL),
 ('560045', 6, NULL),
 ('560046', 3, NULL),
 ('560046', 6, NULL),
 ('560047', 1, NULL),
 ('560048', 2, NULL),
 ('560049', 4, NULL),
 ('560050', 7, NULL),
 ('560051', 6, NULL),
 ('560052', 3, NULL),
 ('560053', 6, NULL),
 ('560054', 2, NULL),
 ('560055', 4, NULL),
 ('560056', 5, NULL),
 ('560056', 7, NULL),
 ('560057', 1, NULL),
 ('560057', 5, NULL),
 ('560058', 7, NULL),
 ('560059', 4, NULL),
 ('560060', 3, NULL),
 ('560061', 2, NULL),
 ('560062', 5, NULL),
 ('560063', 6, NULL),
 ('560064', 2, NULL),
 ('560065', 1, NULL),
 ('560066', 3, NULL),
 ('560067', 5, NULL),
 ('560068', 1, NULL),
 ('560069', 6, NULL),
 ('560070', 4, NULL),
 ('560071', 1, NULL),
 ('560071', 4, NULL),
 ('560071', 5, NULL),
 ('560072', 7, NULL),
 ('560073', 2, NULL),
 ('560073', 7, NULL),
 ('560074', 3, NULL),
 ('5643', 6, 'Portafolio 3'),
 ('5647', 1, NULL),
 ('6382', 1, NULL),
 ('6384', 1, NULL),
 ('6503', 1, NULL),
 ('6505', 4, NULL),
 ('6508', 7, NULL),
 ('6510', 5, NULL),
 ('6511', 3, NULL),
 ('6511', 5, NULL),
 ('6512', 4, NULL),
 ('6513', 3, NULL)
) AS v (codigo, so_numero, instrumento)
JOIN abet.catalogo_version cv ON cv.codigo = 'IND-2026'
JOIN abet.asignatura a ON a.codigo = v.codigo
JOIN abet.so s ON s.catalogo_version_id = cv.catalogo_version_id AND s.numero = v.so_numero
LEFT JOIN abet.instrumento i ON i.catalogo_version_id = cv.catalogo_version_id AND i.nombre = v.instrumento;

-- Aserción de carga. La migración falla, y Flyway la deshace, si algún conteo de IND-2026 no coincide con el
-- JSON. Cuenta solo las filas de IND-2026, así AMB-2026 y las asignaturas de otras carreras no la mueven.
DO $$
DECLARE
    v_version smallint;
    v_n       bigint;
BEGIN
    SELECT catalogo_version_id INTO v_version FROM abet.catalogo_version WHERE codigo = 'IND-2026';
    SELECT count(*) FROM abet.so WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 7 THEN
        RAISE EXCEPTION 'abet.so de IND-2026: se esperaban 7 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.pi WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 21 THEN
        RAISE EXCEPTION 'abet.pi de IND-2026: se esperaban 21 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.rubrica_nivel r JOIN abet.pi p ON p.pi_id = r.pi_id WHERE p.catalogo_version_id = v_version INTO v_n;
    IF v_n <> 0 THEN
        RAISE EXCEPTION 'abet.rubrica_nivel de IND-2026: se esperaban 0 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.competencia WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 0 THEN
        RAISE EXCEPTION 'abet.competencia de IND-2026: se esperaban 0 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.plan_estudios WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 53 THEN
        RAISE EXCEPTION 'abet.plan_estudios de IND-2026: se esperaban 53 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.asignatura_so WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 64 THEN
        RAISE EXCEPTION 'abet.asignatura_so de IND-2026: se esperaban 64 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.asignatura_competencia WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 0 THEN
        RAISE EXCEPTION 'abet.asignatura_competencia de IND-2026: se esperaban 0 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.instrumento WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 1 THEN
        RAISE EXCEPTION 'abet.instrumento de IND-2026: se esperaban 1 filas y hay %', v_n;
    END IF;
END;
$$;
