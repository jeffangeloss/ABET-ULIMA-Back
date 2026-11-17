-- V1_03  Datos de referencia curriculares de Ingeniería Ambiental (solo datos).
-- GENERADO por herramientas/generar_v1_03.py desde referencia/ambiental_2026.json; no se edita a mano.
-- SHA-256 del JSON de referencia: 888f357faf6862ca1b234255a9e6c590c744e0602022fb9d2b3931d87d82fe60
-- Cubre H02 (facultad y carrera), H23 (códigos únicos y depurados), H21 y C6 (PI como texto SO.número),
-- C8 (ciclo de malla), H26 (todo cuelga de la versión de catálogo AMB-2026, en BORRADOR) y H35 (instrumentos).

INSERT INTO abet.facultad (codigo, nombre) VALUES ('FI', 'Facultad de Ingeniería');

INSERT INTO abet.carrera (facultad_id, codigo, nombre)
SELECT facultad_id, 'AMB', 'Ingeniería Ambiental' FROM abet.facultad WHERE codigo = 'FI';

INSERT INTO abet.periodo (anio, ciclo, codigo) VALUES
 (2025, 1, '2025-1'),
 (2025, 2, '2025-2'),
 (2026, 1, '2026-1'),
 (2026, 2, '2026-2');

INSERT INTO abet.catalogo_version (carrera_id, codigo, estado, huella_fuente)
SELECT carrera_id, 'AMB-2026', 'BORRADOR', '888f357faf6862ca1b234255a9e6c590c744e0602022fb9d2b3931d87d82fe60' FROM abet.carrera WHERE codigo = 'AMB';

INSERT INTO abet.asignatura (codigo, nombre) VALUES
 ('450001', 'Sistemas de Información Geográfica'),
 ('450002', 'Principios de Ingeniería Sostenible'),
 ('450003', 'Biología Ambiental'),
 ('450004', 'Química Ambiental'),
 ('450005', 'Derecho y Legislación Ambiental'),
 ('450006', 'Cambio Climático'),
 ('450007', 'Termodinámica'),
 ('450008', 'Ciencia del Suelo'),
 ('450009', 'Técnicas Instrumentales de Análisis'),
 ('450010', 'Gestión Sostenible de Residuos'),
 ('450011', 'Costeo de Proyectos Ambientales'),
 ('450012', 'Tecnologías de Control de la Contaminación del Aire'),
 ('450013', 'Energías Renovables'),
 ('450014', 'Mecánica de Fluidos'),
 ('450015', 'Microbiología Ambiental'),
 ('450016', 'Medio Ambiente y Sociedad'),
 ('450017', 'Recursos Naturales y Ecosistemas'),
 ('450018', 'Tecnologías de Control de la Contaminación del Agua'),
 ('450019', 'Ética y Responsabilidad Social'),
 ('450020', 'Evaluación del Impacto Ambiental'),
 ('450021', 'Tecnologías de Control de la Contaminación del Suelo'),
 ('450022', 'Gestión de Recursos Energéticos'),
 ('450023', 'Ecotoxicología Ambiental'),
 ('450024', 'Proyecto de Ingeniería Aplicada I'),
 ('450025', 'Formulación y Evaluación de Proyectos Sostenibles'),
 ('450026', 'Proyecto de Ingeniería Aplicada II'),
 ('450027', 'Restauración y Compensación Ambiental'),
 ('450045', 'Economía Ambiental'),
 ('450046', 'Cálculo III'),
 ('450047', 'Estadística Aplicada'),
 ('450048', 'Hidrología'),
 ('510003', 'Lenguaje y Comunicación I'),
 ('510005', 'Introducción a la Ingeniería'),
 ('510006', 'Procesos Psicológicos'),
 ('510007', 'Ética Ciudadana'),
 ('510010', 'Filosofía Aplicada'),
 ('510011', 'Introducción al Comercio Internacional'),
 ('510014', 'Precálculo'),
 ('510015', 'Fundamentos de Economía'),
 ('560040', 'Inteligencia Artificial Aplicada'),
 ('560041', 'Física I'),
 ('560042', 'Cálculo II'),
 ('560044', 'Fundamentos de Programación'),
 ('560045', 'Física II'),
 ('560046', 'Estadística y Probabilidad'),
 ('560060', 'Inteligencia de Negocios'),
 ('560066', 'Sistemas Integrados de Gestión'),
 ('5643', 'Química General'),
 ('5674', 'Gestión de Proyectos'),
 ('6384', 'Álgebra lineal'),
 ('6503', 'Cálculo I'),
 ('6508', 'Metodología de la Investigación'),
 ('6511', 'Lenguaje y Comunicación II');

INSERT INTO abet.plan_estudios (catalogo_version_id, asignatura_id, ciclo_malla)
SELECT cv.catalogo_version_id, a.asignatura_id, v.ciclo_malla FROM (VALUES
 ('450001', 3),
 ('450002', 4),
 ('450003', 4),
 ('450004', 4),
 ('450005', 5),
 ('450006', 5),
 ('450007', 5),
 ('450008', 5),
 ('450009', 5),
 ('450010', 6),
 ('450011', 6),
 ('450012', 6),
 ('450013', 6),
 ('450014', 6),
 ('450015', 6),
 ('450016', 7),
 ('450017', 7),
 ('450018', 7),
 ('450019', 7),
 ('450020', 8),
 ('450021', 8),
 ('450022', 8),
 ('450023', 9),
 ('450024', 9),
 ('450025', 8),
 ('450026', 10),
 ('450027', 10),
 ('450045', 7),
 ('450046', 4),
 ('450047', 5),
 ('450048', 8),
 ('510003', 1),
 ('510005', 1),
 ('510006', 1),
 ('510007', 1),
 ('510010', 2),
 ('510011', 2),
 ('510014', 1),
 ('510015', 2),
 ('560040', 3),
 ('560041', 3),
 ('560042', 3),
 ('560044', 3),
 ('560045', 4),
 ('560046', 4),
 ('560060', 9),
 ('560066', 7),
 ('5643', 3),
 ('5674', 10),
 ('6384', 2),
 ('6503', 2),
 ('6508', 1),
 ('6511', 2)
) AS v (codigo, ciclo_malla)
JOIN abet.asignatura a ON a.codigo = v.codigo
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026';

INSERT INTO abet.so (catalogo_version_id, numero, descripcion)
SELECT cv.catalogo_version_id, v.numero, v.descripcion FROM (VALUES
 (1, 'Habilidad para identificar, formular y resolver problemas de ingeniería complejos al aplicar los principios de ingeniería, ciencias y matemáticas.'),
 (2, 'Habilidad para aplicar diseños de ingeniería para producir soluciones que cumplan necesidades específicas según la salud pública, la seguridad y el bienestar, así como los factores globales,'),
 (3, 'Habilidad para comunicarse efectivamente con una variedad de audiencias.'),
 (4, 'Habilidad para reconocer responsabilidades éticas y profesionales en situaciones de ingeniería y realizar juicios informados, los cuales deben considerar el impacto de soluciones de ingeniería en contextos globales, económicos, ambientales y sociales.'),
 (5, 'Habilidad para trabajar efectivamente en un equipo cuyos miembros provean liderazgo, la creación de un ambiente colaborativo e inclusivo, de modo que se establezcan metas, planifiquen tareas y tracen objetivos.'),
 (6, 'Habilidad para desarrollar y realizar experimentos apropiados, analizar e interpretar la data y usar juicios ingenieriles para obtener conclusiones.'),
 (7, 'Habilidad para adquirir y aplicar nuevos conocimientos según sean necesarios al usar apropiadas estrategias de aprendizaje.')
) AS v (numero, descripcion)
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026';

INSERT INTO abet.pi (catalogo_version_id, so_id, so_numero, numero, codigo, descripcion)
SELECT cv.catalogo_version_id, s.so_id, s.numero, v.numero, v.codigo, v.descripcion FROM (VALUES
 (1, 1, '1.1', 'Identifica problemas complejos de ingeniería'),
 (1, 2, '1.2', 'Formula soluciones de problemas complejos aplicando principios de ingeniería, ciencias y matemáticas'),
 (1, 3, '1.3', 'Resuelve problemas complejos de ingeniería aplicando principios de ingeniería, ciencias y matemáticas'),
 (2, 1, '2.1', 'Desarrolla la ingeniería conceptual de una solución considerando necesidades específicas, criterios técnicos y factores contextuales'),
 (2, 2, '2.2', 'Desarrolla la ingeniería de detalle de la solución mediante entregables técnicos coherentes con el diseño conceptual'),
 (3, 1, '3.1', 'Estructura el mensaje técnico de acuerdo con la audiencia y el propósito comunicativo'),
 (3, 2, '3.2', 'Emplea herramientas y recursos de comunicación de manera pertinente para apoyar la comprensión del mensaje'),
 (4, 1, '4.1', 'Aplica responsabilidades éticas y profesionales en una situación de ingeniería'),
 (4, 2, '4.2', 'Justifica un juicio informado sobre una solución o decisión de ingeniería'),
 (4, 3, '4.3', 'Valora el impacto de las soluciones de ingeniería en contextos globales, económicos, ambientales y sociales'),
 (5, 1, '5.1', 'Contribuye al cumplimiento de tareas y metas del equipo'),
 (5, 2, '5.2', 'Participa en la planificación y organización del trabajo para el logro de objetivos'),
 (5, 3, '5.3', 'Favorece un entorno colaborativo e inclusivo y ejerce liderazgo compartido cuando corresponde'),
 (6, 1, '6.1', 'Desarrollo de experimentos'),
 (6, 2, '6.2', 'Interpreta datos experimentales y concluye sobre el resultado del experimento'),
 (7, 1, '7.1', 'Adquiere nuevos conocimientos'),
 (7, 2, '7.2', 'Aplica el nuevo conocimiento')
) AS v (so_numero, numero, codigo, descripcion)
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026'
JOIN abet.so s ON s.catalogo_version_id = cv.catalogo_version_id AND s.numero = v.so_numero;

INSERT INTO abet.rubrica_nivel (pi_id, nivel, descriptor)
SELECT p.pi_id, v.nivel, v.descriptor FROM (VALUES
 ('1.1', -1, 'Presenta una identificación incorrecta del problema de ingeniería, sin distinguir con claridad la brecha técnica a resolver.'),
 ('1.1', 1, 'Describe de forma incompleta la situación técnica del sistema; no distingue con claridad la brecha técnica que debe resolverse.'),
 ('1.1', 2, 'Identifica el problema mediante una descripción cualitativa de la situación técnica del sistema en el contexto del proyecto.'),
 ('1.1', 3, 'Identifica el problema estableciendo la brecha técnica del sistema; diferencia el desempeño actual del desempeño esperado.'),
 ('1.1', 4, 'Identifica el problema mediante un análisis cuantitativo de la brecha técnica del sistema; expresa la diferencia entre el desempeño actual y el requerido mediante variables medibles.'),
 ('1.1', 5, 'Identifica el problema complejo mediante un análisis cuantitativo y cualitativo de la brecha técnica y de su impacto en el sistema; reconoce variables relevantes, distingue su incidencia y establece criterios para priorizarlas aplicando principios de ingeniería, ciencias y matemáticas.'),
 ('1.2', -1, 'Formula una solución de manera incorrecta.'),
 ('1.2', 1, 'Formula soluciones generales con sustento limitado, sin representar de manera clara variables, relaciones o supuestos del sistema.'),
 ('1.2', 2, 'Formula una solución utilizando relaciones, ecuaciones o modelos proporcionados en la actividad o proyecto.'),
 ('1.2', 3, 'Formula una solución mediante un modelo básico aplicando principios de ingeniería, ciencias y matemáticas; representa variables principales y relaciones básicas del sistema.'),
 ('1.2', 4, 'Formula soluciones mediante modelos coherentes; establece indicadores verificables considerando supuestos y restricciones y aplicando principios de ingeniería, ciencias y matemáticas.'),
 ('1.2', 5, 'Formula soluciones integrando modelos, variables, supuestos y restricciones del sistema; fundamenta técnicamente la propuesta y justifica los indicadores establecidos aplicando principios de ingeniería, ciencias y matemáticas.'),
 ('1.3', -1, 'No desarrolla una solución del problema de ingeniería.'),
 ('1.3', 1, 'Presenta un intento de resolución, pero evidencia errores en la selección o ejecución de los procedimientos utilizados.'),
 ('1.3', 2, 'Resuelve el problema utilizando procedimientos o métodos proporcionados en la actividad.'),
 ('1.3', 3, 'Resuelve parcialmente el problema aplicando algunos principios de ingeniería, ciencias o matemáticas.'),
 ('1.3', 4, 'Resuelve el problema verificando resultados y analizando limitaciones de la solución propuesta en un escenario real aplicando principios de ingeniería, ciencias y matemáticas.'),
 ('1.3', 5, 'Resuelve el problema validando la aplicabilidad de la solución en un escenario real y complejo, justificando decisiones técnicas y comparando alternativas o ajustes cuando corresponde, aplicando principios de ingeniería, ciencias y matemáticas.'),
 ('2.1', -1, 'No reconoce ni comprende herramientas de ingeniería pertinentes para plantear una solución de diseño.'),
 ('2.1', 1, 'Reconoce algunas herramientas o enfoques de diseño, pero no logra aplicarlos a la necesidad planteada.'),
 ('2.1', 2, 'Propone una solución conceptual utilizando herramientas de ingeniería pertinentes, aunque sin articular de manera consistente la necesidad, los criterios técnicos y la configuración del diseño.'),
 ('2.1', 3, 'Integra herramientas de ingeniería pertinentes para plantear un diseño conceptual coherente con la necesidad identificada, explicando de manera básica por qué la solución propuesta debería funcionar.'),
 ('2.1', 4, 'Desarrolla la ingeniería conceptual de la solución considerando necesidades específicas, criterios técnicos, restricciones, normas técnicas, estándares de diseño y factores contextuales; integra consideraciones de salud pública, seguridad y bienestar para justificar por qué la solución debería funcionar.'),
 ('2.1', 5, 'Desarrolla una ingeniería conceptual sólida integrando necesidades, criterios técnicos, restricciones, normas técnicas, estándares de diseño y factores contextuales; sustenta la solución mediante principios de ingeniería e integra de manera consistente consideraciones de salud pública, seguridad, bienestar y factores globales, culturales, sociales, ambientales y económicos, anticipando implicancias para su implementación y desempeño.'),
 ('2.2', -1, 'No reconoce ni desarrolla entregables técnicos pertinentes para detallar la solución propuesta.'),
 ('2.2', 1, 'Reconoce algunos entregables técnicos pertinentes, pero los presenta de forma incompleta o sin relación clara con el diseño conceptual de la solución.'),
 ('2.2', 2, 'Elabora entregables técnicos básicos coherentes con el diseño conceptual de la solución; sin embargo, los presenta como elementos aislados y aún no reconoce con claridad la relación entre ellos.'),
 ('2.2', 3, 'Desarrolla entregables técnicos coherentes con el diseño conceptual y reconoce la relación entre ellos para comprender la estructura, el funcionamiento o la implementación básica de la solución.'),
 ('2.2', 4, 'Desarrolla la ingeniería de detalle mediante entregables técnicos articulados entre sí y consistentes con el diseño conceptual, los criterios de diseño y las restricciones; incorpora consideraciones de salud pública, seguridad y bienestar en la definición técnica de la solución, basándose en normas técnicas, estándares de diseño de ingeniería y condiciones de implementación.'),
 ('2.2', 5, 'Desarrolla la ingeniería de detalle mediante entregables técnicos articulados entre sí y coherentes con el diseño conceptual, los criterios de diseño y las restricciones; integra de manera explícita consideraciones de salud pública, seguridad, bienestar y factores globales, culturales, sociales, ambientales y económicos en la definición técnica de la solución, basándose en normas técnicas, estándares de diseño de ingeniería y condiciones de implementación, y sustentando su implementación, evaluación o mejora.'),
 ('3.1', -1, 'Presenta un mensaje desorganizado o incomprensible; no se identifica con claridad una idea principal ni guarda relación con el propósito comunicativo o la audiencia.'),
 ('3.1', 1, 'Presenta una idea principal de forma general, pero sin organización clara ni ideas secundarias que la desarrollen; no emplea lenguaje técnico pertinente.'),
 ('3.1', 2, 'Presenta una idea principal reconocible y algunas ideas secundarias relacionadas, con claridad parcial; emplea algunos términos técnicos, aunque con uso limitado o poco preciso.'),
 ('3.1', 3, 'Estructura el mensaje con una idea principal clara y ideas secundarias que la desarrollan de manera coherente; emplea lenguaje técnico pertinente y responde de manera adecuada al propósito comunicativo.'),
 ('3.1', 4, 'Estructura el mensaje con efectividad mediante una idea principal claramente definida y ideas secundarias que la explican o sustentan; adapta el lenguaje técnico, los ejemplos y el nivel de detalle según la audiencia y el propósito comunicativo.'),
 ('3.1', 5, 'Estructura el mensaje mediante una idea principal sólida y ideas secundarias jerarquizadas que la desarrollan, sustentan o amplían; selecciona y adapta el lenguaje técnico según la audiencia, el propósito comunicativo y la comprensión evidenciada.'),
 ('3.2', -1, 'No emplea herramientas o recursos de apoyo, o los utiliza de forma que dificultan la comprensión del mensaje.'),
 ('3.2', 1, 'Emplea herramientas o recursos de manera limitada, con escasa relación con el mensaje o el propósito comunicativo.'),
 ('3.2', 2, 'Emplea herramientas o recursos básicos acordes al mensaje, aunque con aporte parcial a su comprensión.'),
 ('3.2', 3, 'Emplea herramientas y recursos pertinentes que apoyan la comprensión del mensaje y guardan relación con el propósito comunicativo.'),
 ('3.2', 4, 'Emplea herramientas y recursos apropiados según la audiencia y el propósito comunicativo, reforzando la claridad y comprensión del mensaje.'),
 ('3.2', 5, 'Selecciona y emplea herramientas y recursos de comunicación para distintos tipos de audiencia; ajusta su uso según retroalimentación o evidencias de comprensión del mensaje.'),
 ('4.1', -1, 'Presenta un tratamiento insuficiente de normas, códigos o criterios éticos; omite, distorsiona o presenta como válida información no verificable o falsa en el trabajo académico analizado.'),
 ('4.1', 1, 'Menciona normas, códigos o criterios éticos de forma general, sin vincularlos claramente con el trabajo académico desarrollado.'),
 ('4.1', 2, 'Identifica normas, códigos o criterios éticos pertinentes al trabajo académico y los incorpora como referencia básica para orientar su análisis.'),
 ('4.1', 3, 'Aplica normas, códigos y responsabilidades profesionales pertinentes para sustentar decisiones o actuaciones en la situación de ingeniería analizada.'),
 ('4.1', 4, 'Sustenta decisiones de ingeniería integrando normas, códigos y responsabilidades profesionales de manera consistente y técnicamente pertinente.'),
 ('4.1', 5, 'Integra normas, códigos y responsabilidades profesionales para justificar decisiones de ingeniería, explicando sus implicancias técnicas, éticas, sociales y académicas.'),
 ('4.2', -1, 'Presenta una valoración insuficiente de la situación; omite, distorsiona o sustenta su posición con información no verificable o presentada falsamente como válida.'),
 ('4.2', 1, 'Expresa una opinión general sobre la solución o decisión de ingeniería, con sustento limitado o poco pertinente en el trabajo académico.'),
 ('4.2', 2, 'Identifica información relevante y formula un juicio básico sobre la solución o decisión de ingeniería, con apoyo guiado.'),
 ('4.2', 3, 'Emite un juicio informado sobre la solución o decisión de ingeniería, sustentándolo con información pertinente y criterios básicos de análisis.'),
 ('4.2', 4, 'Justifica su juicio considerando evidencia, criterios técnicos y consecuencias relevantes de la solución o decisión de ingeniería.'),
 ('4.2', 5, 'Justifica su juicio comparando alternativas o implicancias de la decisión, sustentando su posición con evidencia y criterios técnicos y éticos pertinentes.'),
 ('4.3', -1, 'Presenta una valoración insuficiente de los impactos de la solución de ingeniería; omite, minimiza o distorsiona información relevante sobre dimensiones del contexto.'),
 ('4.3', 1, 'Menciona de forma general posibles impactos de la solución de ingeniería, sin diferenciarlos claramente por contexto en el trabajo académico.'),
 ('4.3', 2, 'Identifica impactos de la solución de ingeniería en al menos una dimensión contextual relevante, con sustento guiado.'),
 ('4.3', 3, 'Valora impactos de la solución de ingeniería en contextos globales, económicos, ambientales y sociales, con sustento básico.'),
 ('4.3', 4, 'Valora impactos a corto y mediano plazo en contextos globales, económicos, ambientales y sociales, y justifica su análisis con información pertinente, evidencia o criterios técnicos.'),
 ('4.3', 5, 'Valora impactos de corto y largo plazo en contextos globales, económicos, ambientales y sociales; compara implicancias y sustenta su posición con criterios técnicos, éticos y evidencia relevante.'),
 ('5.1', -1, 'No asume tareas ni contribuye al avance del equipo.'),
 ('5.1', 1, 'Asume tareas de forma limitada y las cumple parcialmente o fuera de plazo.'),
 ('5.1', 2, 'Asume tareas asignadas, y las cumple requiriendo apoyo del equipo.'),
 ('5.1', 3, 'Cumple sus tareas con calidad y puntualidad; contribuye al logro de metas comunes limitandose a su rol.'),
 ('5.1', 4, 'Cumple sus tareas de manera autónoma; contribuye al logro eficiente de las metas comunes y responde a necesidades del equipo relacionadas con su trabajo.'),
 ('5.1', 5, 'Cumple sus tareas de manera autónoma; anticipa necesidades del trabajo del equipo, apoya el cumplimiento de tareas más allá de su rol y contribuye al logro eficiente de las metas comunes'),
 ('5.2', -1, 'No participa en la organización ni planificación del trabajo del equipo.'),
 ('5.2', 1, 'Participa de forma limitada en la organización de tareas sin aportar al proceso.'),
 ('5.2', 2, 'Participa en la planificación básica del trabajo y en la organización de tareas asignadas.'),
 ('5.2', 3, 'Contribuye activamente a la planificación, organización y seguimiento del trabajo del equipo.'),
 ('5.2', 4, 'Organiza tareas, da seguimiento al avance y contribuye al cumplimiento de los objetivos del equipo.'),
 ('5.2', 5, 'Planifica estratégicamente el trabajo, propone ajustes oportunos y contribuye al logro sostenido de los objetivos del equipo.'),
 ('5.3', -1, 'No favorece la colaboración ni la integración del equipo.'),
 ('5.3', 1, 'Escucha opiniones con dificultad para incorporarlas al trabajo del equipo.'),
 ('5.3', 2, 'Escucha y acepta sugerencias; participa en el trabajo colaborativo del equipo.'),
 ('5.3', 3, 'Favorece la cooperación e integración del equipo respetando la participación de sus integrantes.'),
 ('5.3', 4, 'Facilita la colaboración, integra aportes diversos y apoya la toma de decisiones del equipo.'),
 ('5.3', 5, 'Promueve activamente un entorno inclusivo, gestiona desacuerdos cuando corresponde y ejerce liderazgo compartido para el logro de los objetivos del equipo.'),
 ('6.1', -1, 'No ejecuta el experimento o no sigue los procedimientos básicos establecidos; el registro no permite identificar variables, método ni condiciones de ejecución.'),
 ('6.1', 1, 'Ejecuta experimentos de forma básica, sin identificar variables relevantes ni justificar el procedimiento empleado.'),
 ('6.1', 2, 'Ejecuta experimentos siguiendo los procedimientos y métodos establecidos; identifica algunas variables relevantes del proceso.'),
 ('6.1', 3, 'Desarrolla y ejecuta experimentos identificando variables, materiales y condiciones de trabajo; aplica los procedimientos establecidos y resuelve, con criterio técnico, dificultades operativas o desviaciones simples surgidas durante la ejecución.'),
 ('6.1', 4, 'Desarrolla y ejecuta experimentos considerando variables, controles y condiciones relevantes; resuelve dificultades operativas determinantes para el logro del objetivo experimental mediante ajustes técnicamente pertinentes.'),
 ('6.1', 5, 'Diseña, planifica y desarrolla experimentos de forma sistemática; integra variables, controles, condiciones y criterios de ejecución, y anticipa resultados o comportamientos esperados con base en el diseño experimental.'),
 ('6.2', -1, 'No reconoce la relación entre los datos obtenidos y el resultado del experimento.'),
 ('6.2', 1, 'Describe o presenta los datos obtenidos, pero no los analiza ni formula conclusiones sustentadas en ellos.'),
 ('6.2', 2, 'Analiza los datos obtenidos en relación con el experimento, pero no los interpreta para sustentar conclusiones.'),
 ('6.2', 3, 'Interpreta los resultados utilizando conceptos básicos del experimento y formula conclusiones coherentes con los datos obtenidos.'),
 ('6.2', 4, 'Interpreta los resultados considerando variaciones, tendencias y relaciones entre variables; sustenta las conclusiones con criterios técnicos y evidencia experimental.'),
 ('6.2', 5, 'Interpreta y proyecta los resultados utilizando juicios ingenieriles; sustenta conclusiones con evidencia experimental, criterios técnicos y, cuando corresponde, modelos o relaciones cuantitativas para explicar el comportamiento observado.'),
 ('7.1', -1, 'No se evidencia adquisición de conceptos o información técnica, a pesar de que se proporcionan fuentes para la actividad y se solicita su uso.'),
 ('7.1', 1, 'Intenta adquirir conceptos o información técnica a partir de las fuentes proporcionadas, pero presenta errores en la identificación, interpretación o registro de la información contenida en dichas fuentes.'),
 ('7.1', 2, 'Adquiere conceptos o información técnica pertinentes al tema del proyecto mediante la consulta de las fuentes proporcionadas en la actividad cuando se solicita explícitamente su uso.'),
 ('7.1', 3, 'Adquiere nuevos conceptos o información técnica relacionados con el tema del proyecto mediante la consulta de fuentes adicionales identificadas por el estudiante, sin aplicar criterios explícitos de verificación de confiabilidad.'),
 ('7.1', 4, 'Adquiere nuevos conceptos o información técnica pertinentes al tema del proyecto mediante la consulta de fuentes adicionales cuya confiabilidad verifica explícitamente utilizando criterios como autoría identificable, publicación académica o indexación en bases de datos reconocidas.'),
 ('7.1', 5, 'Adquiere nuevos conceptos o información técnica pertinentes al tema del proyecto mediante la aplicación de una estrategia estructurada de búsqueda de información, que incluye definición de palabras clave, uso de bases de datos o repositorios especializados y criterios de selección de fuentes.'),
 ('7.2', -1, 'No se evidencia aplicación de conceptos o información técnica en el desarrollo del proyecto, a pesar de que se solicita su uso.'),
 ('7.2', 1, 'Intenta aplicar conceptos o información técnica en el desarrollo del proyecto, pero presenta errores en su selección, interpretación o implementación.'),
 ('7.2', 2, 'Aplica conceptos o información técnica proporcionados en las fuentes indicadas cuando se solicita su uso en el desarrollo del proyecto.'),
 ('7.2', 3, 'Aplica nuevos conceptos o información técnica en una parte del desarrollo del proyecto, incorporándolos en procedimientos, cálculos, modelos o análisis relacionados con el problema abordado.'),
 ('7.2', 4, 'Aplica nuevos conceptos o información técnica pertinentes al problema del proyecto mediante su incorporación explícita en el desarrollo de la solución, describiendo cómo estos conceptos influyen en el procedimiento o en las decisiones técnicas del trabajo.'),
 ('7.2', 5, 'Aplica nuevos conceptos o información técnica pertinentes al problema del proyecto mediante su integración sistemática en el diseño, desarrollo o análisis de la solución, mostrando la relación entre dichos conceptos y las decisiones técnicas adoptadas.')
) AS v (pi_codigo, nivel, descriptor)
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026'
JOIN abet.pi p ON p.catalogo_version_id = cv.catalogo_version_id AND p.codigo = v.pi_codigo;

INSERT INTO abet.instrumento (catalogo_version_id, nombre)
SELECT cv.catalogo_version_id, v.nombre FROM (VALUES
 ('CII'),
 ('CIS'),
 ('Exposición'),
 ('Portafolio'),
 ('Proyecto'),
 ('Trabajo Integrador'),
 ('Trabajo Integrador / Portafolio')
) AS v (nombre)
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026';

INSERT INTO abet.asignatura_so (catalogo_version_id, asignatura_id, so_id, instrumento_id)
SELECT cv.catalogo_version_id, a.asignatura_id, s.so_id, i.instrumento_id FROM (VALUES
 ('450001', 2, 'Trabajo Integrador'),
 ('450001', 7, 'Trabajo Integrador'),
 ('450002', 4, 'Trabajo Integrador'),
 ('450002', 5, 'Trabajo Integrador'),
 ('450003', 1, 'Trabajo Integrador'),
 ('450004', 6, 'Portafolio'),
 ('450005', 4, 'Trabajo Integrador'),
 ('450006', 3, 'Exposición'),
 ('450007', 1, 'Trabajo Integrador'),
 ('450008', 1, 'Trabajo Integrador'),
 ('450009', 3, 'Exposición'),
 ('450010', 2, 'Trabajo Integrador'),
 ('450010', 5, 'Trabajo Integrador'),
 ('450011', 5, 'Trabajo Integrador'),
 ('450012', 2, 'Trabajo Integrador'),
 ('450012', 7, 'Trabajo Integrador'),
 ('450013', 2, 'Trabajo Integrador'),
 ('450014', 2, 'Trabajo Integrador'),
 ('450014', 7, 'Trabajo Integrador'),
 ('450015', 6, 'Portafolio'),
 ('450016', 4, 'Trabajo Integrador'),
 ('450017', 6, 'Portafolio'),
 ('450018', 2, 'Trabajo Integrador'),
 ('450018', 7, 'Trabajo Integrador'),
 ('450019', 4, 'Trabajo Integrador'),
 ('450020', 1, 'Trabajo Integrador'),
 ('450021', 2, 'Trabajo Integrador'),
 ('450022', 1, 'Trabajo Integrador'),
 ('450023', 1, 'Trabajo Integrador / Portafolio'),
 ('450023', 6, 'Trabajo Integrador / Portafolio'),
 ('450024', 1, 'Proyecto'),
 ('450024', 7, 'Proyecto'),
 ('450025', 2, 'Trabajo Integrador'),
 ('450026', 2, 'Proyecto'),
 ('450026', 3, 'Proyecto'),
 ('450026', 6, 'Proyecto'),
 ('450027', 5, 'Trabajo Integrador'),
 ('450045', 5, 'Trabajo Integrador'),
 ('450046', 1, 'Trabajo Integrador'),
 ('450047', 6, 'Trabajo Integrador / Portafolio'),
 ('450047', 7, 'Trabajo Integrador / Portafolio'),
 ('450048', 7, 'Trabajo Integrador'),
 ('510003', 3, NULL),
 ('510003', 5, NULL),
 ('510006', 4, NULL),
 ('510007', 4, NULL),
 ('510010', 4, NULL),
 ('510011', 4, NULL),
 ('510015', 7, NULL),
 ('560041', 6, 'CII'),
 ('560042', 1, 'CII'),
 ('560045', 6, 'CII'),
 ('560046', 3, 'CII'),
 ('560060', 3, 'CII'),
 ('560066', 3, 'CII'),
 ('5643', 6, 'CII'),
 ('5674', 3, 'CIS'),
 ('5674', 5, 'CIS'),
 ('6508', 7, NULL),
 ('6511', 3, NULL),
 ('6511', 5, NULL)
) AS v (codigo, so_numero, instrumento)
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026'
JOIN abet.asignatura a ON a.codigo = v.codigo
JOIN abet.so s ON s.catalogo_version_id = cv.catalogo_version_id AND s.numero = v.so_numero
LEFT JOIN abet.instrumento i ON i.catalogo_version_id = cv.catalogo_version_id AND i.nombre = v.instrumento;

INSERT INTO abet.competencia (catalogo_version_id, codigo, nombre, tipo)
SELECT cv.catalogo_version_id, v.codigo, v.nombre, v.tipo FROM (VALUES
 ('G1', 'Pensamiento sistémico', 'GENERICA'),
 ('G2', 'Solución de problemas', 'GENERICA'),
 ('G3', 'Comunicación efectiva', 'GENERICA'),
 ('G4', 'Trabajo colaborativo', 'GENERICA'),
 ('G5', 'Investigación', 'GENERICA'),
 ('G6', 'Autogestión del aprendizaje', 'GENERICA'),
 ('G7', 'Pensamiento crítico', 'GENERICA'),
 ('G8', 'Comportamiento ético', 'GENERICA'),
 ('E1', 'Solución de problemas complejos', 'ESPECIFICA'),
 ('E2', 'Diseño de soluciones', 'ESPECIFICA'),
 ('E3', 'Experimentación y análisis de datos', 'ESPECIFICA')
) AS v (codigo, nombre, tipo)
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026';

-- G1, G2, G5 y G7 no aportan a ningún SO y no tienen fila.
INSERT INTO abet.competencia_so (catalogo_version_id, competencia_id, so_id)
SELECT cv.catalogo_version_id, k.competencia_id, s.so_id FROM (VALUES
 ('G3', 3),
 ('G4', 5),
 ('G6', 7),
 ('G8', 4),
 ('E1', 1),
 ('E2', 2),
 ('E3', 6)
) AS v (codigo, so_numero)
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026'
JOIN abet.competencia k ON k.catalogo_version_id = cv.catalogo_version_id AND k.codigo = v.codigo
JOIN abet.so s ON s.catalogo_version_id = cv.catalogo_version_id AND s.numero = v.so_numero;

INSERT INTO abet.asignatura_competencia (catalogo_version_id, asignatura_id, competencia_id, estadio)
SELECT cv.catalogo_version_id, a.asignatura_id, k.competencia_id, v.estadio FROM (VALUES
 ('450001', 'G6', 'INICIAL'),
 ('450001', 'E2', 'INICIAL'),
 ('450002', 'G4', 'REFUERZO'),
 ('450002', 'G8', 'REFUERZO'),
 ('450003', 'G2', 'REFUERZO'),
 ('450003', 'E1', 'REFUERZO'),
 ('450004', 'E3', 'REFUERZO'),
 ('450005', 'G5', 'REFUERZO'),
 ('450005', 'G8', 'REFUERZO'),
 ('450006', 'G1', 'REFUERZO'),
 ('450006', 'G3', 'REFUERZO'),
 ('450007', 'G2', 'REFUERZO'),
 ('450007', 'E1', 'REFUERZO'),
 ('450008', 'G7', 'REFUERZO'),
 ('450008', 'E1', 'REFUERZO'),
 ('450009', 'G3', 'REFUERZO'),
 ('450009', 'G5', 'REFUERZO'),
 ('450010', 'G4', 'REFUERZO'),
 ('450010', 'E2', 'REFUERZO'),
 ('450011', 'G4', 'REFUERZO'),
 ('450012', 'G6', 'REFUERZO'),
 ('450012', 'E2', 'REFUERZO'),
 ('450013', 'G5', 'REFUERZO'),
 ('450013', 'E2', 'REFUERZO'),
 ('450014', 'G6', 'REFUERZO'),
 ('450014', 'E2', 'REFUERZO'),
 ('450015', 'G7', 'REFUERZO'),
 ('450015', 'E3', 'REFUERZO'),
 ('450016', 'G7', 'LOGRADO'),
 ('450016', 'G8', 'LOGRADO'),
 ('450017', 'G5', 'LOGRADO'),
 ('450017', 'E3', 'LOGRADO'),
 ('450018', 'G6', 'LOGRADO'),
 ('450018', 'E2', 'LOGRADO'),
 ('450019', 'G8', 'LOGRADO'),
 ('450020', 'G5', 'LOGRADO'),
 ('450020', 'E1', 'LOGRADO'),
 ('450021', 'E2', 'LOGRADO'),
 ('450022', 'G2', 'LOGRADO'),
 ('450022', 'E1', 'LOGRADO'),
 ('450023', 'E1', 'LOGRADO'),
 ('450023', 'E3', 'LOGRADO'),
 ('450024', 'G6', 'LOGRADO'),
 ('450024', 'G8', 'LOGRADO'),
 ('450024', 'E1', 'LOGRADO'),
 ('450025', 'E2', 'LOGRADO'),
 ('450026', 'G3', 'LOGRADO'),
 ('450026', 'E2', 'LOGRADO'),
 ('450026', 'E3', 'LOGRADO'),
 ('450027', 'G4', 'LOGRADO'),
 ('450027', 'G5', 'LOGRADO'),
 ('450045', 'G4', 'LOGRADO'),
 ('450046', 'G2', 'REFUERZO'),
 ('450046', 'E1', 'REFUERZO'),
 ('450047', 'G6', 'REFUERZO'),
 ('450047', 'E3', 'REFUERZO'),
 ('450048', 'G1', 'LOGRADO'),
 ('450048', 'G6', 'LOGRADO'),
 ('510003', 'G3', 'INICIAL'),
 ('510003', 'G4', 'INICIAL'),
 ('510005', 'G2', 'INICIAL'),
 ('510006', 'G1', 'INICIAL'),
 ('510006', 'G8', 'INICIAL'),
 ('510007', 'G2', 'INICIAL'),
 ('510007', 'G8', 'INICIAL'),
 ('510010', 'G7', 'INICIAL'),
 ('510010', 'G8', 'INICIAL'),
 ('510011', 'G7', 'INICIAL'),
 ('510011', 'G8', 'INICIAL'),
 ('510014', 'G1', 'INICIAL'),
 ('510014', 'G2', 'INICIAL'),
 ('510015', 'G6', 'INICIAL'),
 ('510015', 'G7', 'INICIAL'),
 ('560040', 'G1', 'INICIAL'),
 ('560040', 'G7', 'INICIAL'),
 ('560041', 'E3', 'INICIAL'),
 ('560042', 'G2', 'INICIAL'),
 ('560042', 'E1', 'INICIAL'),
 ('560044', 'G5', 'INICIAL'),
 ('560045', 'E3', 'REFUERZO'),
 ('560046', 'G3', 'REFUERZO'),
 ('560060', 'G3', 'LOGRADO'),
 ('560066', 'G1', 'LOGRADO'),
 ('560066', 'G3', 'LOGRADO'),
 ('5643', 'E3', 'INICIAL'),
 ('5674', 'G3', 'LOGRADO'),
 ('5674', 'G4', 'LOGRADO'),
 ('6384', 'G1', 'INICIAL'),
 ('6384', 'G2', 'INICIAL'),
 ('6503', 'G1', 'INICIAL'),
 ('6503', 'G2', 'INICIAL'),
 ('6508', 'G5', 'INICIAL'),
 ('6508', 'G6', 'INICIAL'),
 ('6511', 'G3', 'INICIAL'),
 ('6511', 'G4', 'INICIAL')
) AS v (codigo, competencia, estadio)
JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026'
JOIN abet.asignatura a ON a.codigo = v.codigo
JOIN abet.competencia k ON k.catalogo_version_id = cv.catalogo_version_id AND k.codigo = v.competencia;

-- Aserción de carga: la migración falla si algún conteo no coincide con el JSON.
-- Es la única excepción a «sin plpgsql» de la entrega 1; en T-SQL se traduce a IF ... THROW.
DO $$
DECLARE
    v_version smallint;
    v_n       bigint;
BEGIN
    SELECT catalogo_version_id INTO v_version FROM abet.catalogo_version WHERE codigo = 'AMB-2026';
    SELECT count(*) FROM abet.so WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 7 THEN
        RAISE EXCEPTION 'abet.so: se esperaban 7 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.pi WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 17 THEN
        RAISE EXCEPTION 'abet.pi: se esperaban 17 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.rubrica_nivel r JOIN abet.pi p ON p.pi_id = r.pi_id WHERE p.catalogo_version_id = v_version INTO v_n;
    IF v_n <> 102 THEN
        RAISE EXCEPTION 'abet.rubrica_nivel: se esperaban 102 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.competencia WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 11 THEN
        RAISE EXCEPTION 'abet.competencia: se esperaban 11 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.competencia_so WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 7 THEN
        RAISE EXCEPTION 'abet.competencia_so: se esperaban 7 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.asignatura INTO v_n;
    IF v_n <> 53 THEN
        RAISE EXCEPTION 'abet.asignatura: se esperaban 53 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.plan_estudios WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 53 THEN
        RAISE EXCEPTION 'abet.plan_estudios: se esperaban 53 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.asignatura_so WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 61 THEN
        RAISE EXCEPTION 'abet.asignatura_so: se esperaban 61 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.asignatura_competencia WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 95 THEN
        RAISE EXCEPTION 'abet.asignatura_competencia: se esperaban 95 filas y hay %', v_n;
    END IF;
    SELECT count(*) FROM abet.instrumento WHERE catalogo_version_id = v_version INTO v_n;
    IF v_n <> 7 THEN
        RAISE EXCEPTION 'abet.instrumento: se esperaban 7 filas y hay %', v_n;
    END IF;
END;
$$;
