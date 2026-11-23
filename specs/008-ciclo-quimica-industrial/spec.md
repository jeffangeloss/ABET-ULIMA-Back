# Feature Specification: Ciclo de punta a punta de Química General en Ingeniería Industrial

**Feature Branch**: `docs/008-ciclo-quimica-industrial` del Back y del Front (PR a `develop`), con la implementación en `feat/008-ciclo-quimica-industrial` después de la aprobación
**Created**: 2026-11-23
**Status**: Aprobada por Jefferson en el chat el 2026-11-23 («Sí, apruébala») y en construcción en `feat/008-ciclo-quimica-industrial`, sin push. Al 2026-11-23 el Back tiene la base y el Back de US-67 a US-76, US-78, US-83 y US-86 (T010 a T037, salvo T026 de Jefferson, que hizo Claude Code), y el Front tiene T011 y T040 a T043. Faltan el resto del Back (T038 y T039), del Front (T044 a T049), las pruebas y el humo, la auditoría y el despliegue, y D-48 a D-55 y J-49 a J-59 siguen abiertas con el valor que propone la spec (cambio del 2026-11-23)
**Input**: «haremos una capacitación del sistema. Para el curso de química se me otorgarán datos reales para tener una mejor representación del sistema. Hay que mejorarlo, visualmente se tiene que ver mejor. Quizá puedas usar alguna herramienta para mejorar la UX/UI del frontend, busca alguna skill. usa codex con cuidado y la API para optimizar costos. El objetivo es generar todo el ciclo de punta a punta. para eso deberá existir un coordinador del curso de química que tenga la capacidad de ver todas las secciones de dicho curso» (Jefferson, 2026-11-23). «con stefanny quedamos en lograr el flujo de punta a punta, que todas las historias y requerimientos se cumplan, construye specs y prueba usando BDD, TDD, ATDD de forma continua, escribe en Gherkin y no olvides nada. Al final la magia está entonces que se logre eso. está bien que los correos de los profes sean de ejemplo, solo será para capacitación» (Jefferson, 2026-11-23)

## Épica

> **EP-08. Ciclo de punta a punta de Química General en Ingeniería Industrial (propuesta).** La versión 0.3.0 mide solo Ingeniería Ambiental en 2026-2. La capacitación usa en cambio Química General (5643) de Ingeniería Industrial en 2026-1, un ciclo ya terminado, con 18 secciones, un profesor por sección y un solo indicador, el PI 6.1 del SO6, medido con el «Portafolio 3» en la escala de 1 a 4. Hoy la base no conoce Industrial, el profesor de 5643 entra a P2 y lee que no tiene secciones porque el Front pide siempre el periodo vigente, la subida falla sin el conjunto de reglas de Industrial, el R-17 diría «Carrera de Ingeniería Ambiental», la coordinación de Ambiental vería las secciones de Química en cuanto Industrial esté vigente, nadie tiene la cuenta de coordinación de un curso y los profesores de química no calificaron en Blackboard, así que no tienen export que subir. Esta épica cierra el ciclo completo, desde el catálogo de Industrial hasta la conciliación de cada R-17 con la tabla maestra que Stefanny verificó igual a los 18 R-17 llenados a mano, con un rediseño visual del Front, la etapa B de la spec 007 para la coordinación y la guía de la capacitación.

Convenciones de esta spec. Todos los datos de los escenarios son inventados. Las secciones de prueba de Química General son la 701, la 702, la 703 y la 704 de 5643 en 2026-1, con el curso de Blackboard `SINTETICO_20261_5643_70N`, los profesores `docente701@example.invalid`, `docente702@example.invalid` y `docente703@example.invalid`, la 704 sin profesor y la coordinación del curso `coordinador.quimica@example.invalid`, en `db/datos/quimica_2026_1_inventado.sql` (propuesta). Ambiental conserva la 410 y la 411 de 450002 en 2026-2 y la coordinación `coordinacion@example.invalid`. Los códigos de estudiante son del rango 99000000 a 99999999. Los números reales de las 18 secciones, el correo real de la coordinación de Química General, la tabla maestra, los 18 R-17 de los profesores y los exports generados con datos reales viven fuera de todo repositorio, porque los dos repositorios son públicos (D-10). Las cuentas de la capacitación usan correos de ejemplo de la forma `docenteNNN@example.invalid`, que Jefferson acepta, y su correspondencia con cada persona tampoco entra a git. Lo que el redactor decide sin fuente va marcado «(propuesta)».

Prefijos e identificadores. La épica continúa la numeración (EP-08). Las historias US siguen desde US-67, porque la spec 007 termina en US-66. Las decisiones de la carrera y de la Oficina de Calidad siguen desde D-48 y las de Jefferson desde J-49, porque la spec 007 usa D-46, D-47 y J-43 a J-48. Las reglas nuevas son BR-PERIODO-05, BR-PERIODO-06, BR-ACCESO-13, BR-ACCESO-14 y BR-R17-13, porque la spec 007 reserva BR-ACCESO-12 y la spec 005 reserva BR-R17-12. Las migraciones son V1_12 a V1_14, las consultas de control nuevas Q18 a Q21 y la ruta nueva la 18, según la reserva de `revision-historias.md`. Los requisitos funcionales FR (functional requirement), los criterios de éxito SC (success criterion) y las tareas T se numeran dentro de esta spec. Las candidatas de la auditoría se llaman C-01 a C-09, C-20 a C-28, C-40 a C-49 y C-60 a C-68.

Siglas y términos. Las de las specs 001 a 007 valen aquí. El indicador de desempeño (performance indicator, PI), el resultado del estudiante (student outcome, SO), la interfaz de programación de aplicaciones (application programming interface, API) y la experiencia de uso (user experience, UX) conservan su sentido. La interfaz de usuario (user interface, UI) es lo que el pedido llama UI. El desarrollo guiado por el comportamiento (behavior-driven development, BDD), el desarrollo guiado por pruebas (test-driven development, TDD) y el desarrollo guiado por pruebas de aceptación (acceptance test-driven development, ATDD) son los tres métodos que pide Jefferson, y en esta spec se cumplen con un escenario en Gherkin por comportamiento, una prueba que falla antes del código y la corrida de los `.feature` como prueba de aceptación. AA es el nivel de conformidad de las pautas de accesibilidad para el contenido web (Web Content Accessibility Guidelines, WCAG) 2.2. La tabla maestra es la tabla conglomerada de Stefanny con las columnas AÑO, CICLO, CÓDIGO DEL CURSO, CURSO, CICLO DEL CURSO, SO, PI, PROFESOR, CÓDIGO DEL ESTUDIANTE, SECCIÓN, CALIFICACIÓN y ARCHIVO. El porcentaje de cumplimiento es el número de alumnos con nivel 3 o 4 entre los alumnos con nota, con meta de 80 %, la misma regla de BR-R17-03 con NIVEL_ESPERADO 3 y META_LOGRO 0,8. La coordinación de carrera es una cuenta COORDINADOR con alcance de una carrera, y la coordinación del curso, una cuenta COORDINADOR con alcance de una asignatura en un periodo.

Los escenarios viven en `specs/008-ciclo-quimica-industrial/aceptacion/`, en español (`# language: es`), en doce archivos que el analizador de pytest-bdd 9 lee con 202 escenarios y 257 casos. `catalogo_industrial.feature` contiene US-67 a US-69, `alcance_coordinacion.feature` US-70 a US-72, `periodo_elegido.feature` US-73, `exports_capacitacion.feature` US-74, `carga_quimica.feature` US-75 a US-77, `r17_industrial.feature` US-78, `avance_del_curso.feature` US-79 y US-80, `sistema_visual.feature` US-81 y US-82, `ensayo_y_conciliacion.feature` US-83 y US-84, `capacitacion_en_develop.feature` US-85, US-86 y US-89, `guia_y_privacidad.feature` US-87 y US-88 y `matriz_cumplimiento.feature` US-90. Cada escenario lleva `@spec008`, `@corte1` y `@US-NN` (cambio del 2026-11-23). Los de pantalla llevan además `@delegado_a_vitest`, porque los prueba Vitest en el Front, y los del navegador llevan `@playwright`, porque los prueba Playwright en `e2e/` del Front.

## Clarifications

### Session 2026-11-23

- Jefferson pide el ciclo de punta a punta de Química General para la capacitación, un Front que se vea mejor y una coordinación del curso que vea todas sus secciones. Después agrega que con Stefanny acordaron lograr el flujo de punta a punta con todas las historias y requerimientos cumplidos, con BDD, TDD y ATDD continuos y en Gherkin, y acepta correos de ejemplo para los profesores.
- Stefanny Montaño (Oficina de Calidad) verifica el 2026-11-23 los hechos de Química General. El curso es 5643 de Ingeniería Industrial en 2026-1, con 18 secciones, un profesor por sección, un solo PI medido (6.1, SO6) con el «Portafolio 3», la escala de 1 a 4 y ningún alumno sin nota. La tabla maestra coincide alumno por alumno con los 18 R-17 que llenó cada profesor, así que es el oráculo de la conciliación.
- Los profesores de química no calificaron en Blackboard. La decisión A de Jefferson genera para la capacitación 18 exports con el formato de Blackboard desde la tabla maestra, con los códigos y los niveles reales y sin nombres, y cada profesor sube el suyo. El generador entra al Back solo con datos inventados en sus pruebas, y su corrida con la tabla real se hace fuera del repositorio.
- Los R-17 de los profesores traen el mapa curricular de Industrial (7 SO, 21 PI y 53 cursos), sin rúbricas por nivel ni estadio. El estadio «Inicial» de 5643 se toma de Ambiental como supuesto (D-49), y el catálogo queda en BORRADOR hasta la «Plantilla Base - Final» de Industrial (D-50). Un programa de los profesores dice «PI 6.2» y los R-17 dicen 6.1, así que la spec usa 6.1 con el PI como parámetro (D-48).
- La auditoría revisa 37 candidatas con tres lentes y el crítico de arquitectura (`revision-historias.md`). Sobreviven 24 historias. C-24, C-25 como historia propia, C-27 y el paso a main de C-67 quedan en «Fuera de alcance», porque dos lentes las marcan REFUTADA o MOVER_A_DESPUES.
- El crítico cambia el modelo de la coordinación del curso. El rol COORDINADOR se conserva y el alcance vive en una tabla nueva, `acceso.coordinacion_alcance`, por carrera o por asignatura, que ata también a la coordinación de Ambiental a su carrera. El Front distingue el curso por el campo aditivo `alcance` de `GET /api/sesion`.
- El crítico sostiene el selector de periodo frente a fijar `PERIODO_VIGENTE=2026-1` en develop, porque cambiar la variable esconde 450002 de 2026-2 y rompe el humo de la spec 007.
- La etapa B de la spec 007 (US-64 y US-65) no tiene código y la coordinación del curso la necesita, así que esta spec la construye con el alcance nuevo (J-57). US-66 sigue esperando a D-47 en Ambiental y a D-51 en Industrial. Si la etapa B no llega antes de la capacitación, la coordinación del curso sigue el avance en P2.
- La spec 005 (oportunidades de mejora, hojas III y IV del R-17) no entra antes de la capacitación (J-57). El R-17 del sistema sale sin las hojas III y IV, que los R-17 a mano sí traen, y la conciliación compara solo códigos, niveles, conteos y porcentaje.
- La capacitación corre en la versión de prueba (develop) con fecha por confirmar, en la semana 14 (23 al 28-11-2026) o en la siguiente, antes o al comienzo del registro de los profesores del 30-11 al 12-12 (J-56).
- El rediseño sigue la skill frontend-design con tokens de Tailwind 4 y fuentes del sistema, sin dependencias nuevas (J-59). Codex se usa solo para piezas chicas y sin datos reales, y no hay clave de la API de OpenAI (plan, «Restricciones»).

### Cambios del 2026-11-23 en la construcción

- **Asignaturas reutilizadas (T026 y T013).** Contra `db/migration/V1_03__cargar_referencia_ambiental.sql`, 15 de las 53 asignaturas de `db/referencia/industrial_2026.json` ya están en `abet.asignatura`, y no 10. Son 510003, 510005, 560040, 560041, 560042, 560044, 560045, 560046, 560060, 560066, 5643, 6384, 6503, 6508 y 6511, así que V1_12 suma 38 asignaturas y `abet.asignatura` queda con 91 filas y no con 96. Cambian la Base y el escenario 2 de US-67, los Antecedentes y el escenario «Una asignatura compartida se reutiliza sin tocar Ambiental» de `catalogo_industrial.feature` y la fila de verificabilidad de `revision-historias.md`. La hoja escribe en mayúsculas los nombres de las 15, y dos de ellos difieren además en palabras de los de V1_03, que son 560044 («FUNDAMENTOS DE LA PROGRAMACIÓN» frente a «Fundamentos de Programación») y 6508 («METODOLOGÍA DE INVESTIGACIÓN» frente a «Metodología de la Investigación»). T020 decide cómo compara `generar_v1_12.py` esos nombres sin que el esquema «el nombre distinto del ya registrado» rechace la referencia real.
- **Referencia curricular (T026).** Claude Code corre el 2026-11-23, fuera del repositorio, `herramientas_neon/extraer_referencia_industrial.py`, que lee solo la hoja «Información por Asignatura» de un R-17 de profesor, y las 18 hojas de los R-17 de Química General son idénticas. `db/referencia/industrial_2026.json` trae solo datos curriculares (7 SO, 21 PI, 64 pares de asignatura y PI y 53 asignaturas) y el campo `inconsistencias_de_la_fuente`, con 560071 escrito «PROYECTO DE INGENIERÍA APLICADA I» y «PROYECTOS DE INGENIERÍA APLICADA I». V1_12 usa la primera forma.
- **Nombres de las asignaturas reutilizadas (T020).** `generar_v1_12.py` compara el nombre de la hoja con el de V1_03 sin distinguir mayúsculas y con las tildes, y acepta 560044 y 6508 por la lista `EQUIVALENCIAS` del generador, así la referencia real pasa y «Quimica general» sigue rechazada. 560071 usa la primera forma de `inconsistencias_de_la_fuente`. La hoja trae además «PROYECTO DE INGENIERÍA APLICADA II» con dos códigos, 560073 (PI 2.3 y 7.3) y 530073 (PI 6.3), y 530073 parece una errata de la fuente. V1_12 conserva los dos códigos, porque la referencia declara 53 asignaturas, y la duda queda para Stefanny junto a D-50. Los 64 pares de asignatura y PI dan 64 pares de asignatura y SO, y solo el par 5643 y SO 6 lleva instrumento, el «Portafolio 3».
- **Plan en los escenarios de la carga de 5643 (T021 y T024).** `cargar()` busca el plan de medición de la sección antes que el conjunto de reglas, así que sin plan la carga de la 701 termina con el texto de la sección sin plan y nunca llega a las reglas. Los Antecedentes de dos escenarios de US-68 en `catalogo_industrial.feature` suman el plan y V1_14, que piden los datos inventados de Química, y pasan a «Dado la base con V1_12 a V1_14 aplicadas, el plan de 5643 en 2026-1 y los datos de db/datos/quimica_2026_1_inventado.sql» y «Dado la base con V1_12 y V1_14 sin V1_13, el plan de 5643 en 2026-1 y los datos de db/datos/quimica_2026_1_inventado.sql», sin cambiar los conteos de escenarios ni de casos. La copia de los `.feature` del Front espera el mismo cambio. El escenario sin V1_13 prueba hoy el 500 de la ruta 5 porque la API arranca con el conjunto de Ambiental, y cuando T033 sume la comprobación por carrera su paso arranca la API antes de quitar el conjunto de Industrial.
- **Q19 y Q20 (T021 y T023).** Q19 lista la carrera con plan de medición y ningún conjunto de reglas, sin mirar la versión, porque CONJUNTO_REGLAS es una variable de la API que la base no conoce, y la comprobación de arranque de T033 revisa la versión. Q20 vería a `coordinacion@example.invalid` en toda base de prueba con los datos de 2026-2 y sin alcance, así que `periodo_2026_2_inventado.sql` le da la carrera AMB cuando la tabla de V1_14 existe, como `alcance_coordinacion_ambiental.sql` en Neon. Q21 marcaría en Neon un curso de Blackboard real que no termine en `_<periodo>_<asignatura>_<sección>`, y el paso de controles del final de la siembra lo muestra.
- **Etiqueta del corte (T013).** El principio V de la constitución pide `@corte1` o `@corte2` en cada escenario, y `test_lectura_gherkin_es.py` lo exige en cada `.feature` que lee. Los 202 escenarios suman `@corte1`, como los de las specs 006 y 007, sin cambiar los conteos de 202 escenarios y 257 casos. De ellos, 41 llevan `@delegado_a_vitest` y 14 `@playwright`, y ninguno las dos.
- **Plan en los Antecedentes de US-70, US-71 y US-73 (T030 y T033).** Una carga PUBLICADA de la 701, de la 702 o de la 703 y la subida en 2026-1 exigen el plan de 5643, y sin la vigencia de IND-2026 en 2026-1 el escenario «La coordinación de Ambiental no ve las secciones de Química General» pasaría también con el `_ALCANCE` de antes. Los Antecedentes de `alcance_coordinacion.feature` y `periodo_elegido.feature` pasan a «Dado una base desechable de la spec 008 con el plan de 5643 en 2026-1 y los datos de periodo_2026_2_inventado.sql y quimica_2026_1_inventado.sql», sin cambiar los conteos de escenarios ni de casos, y `conftest.py` ata esa forma a la variante con el plan. La copia de los `.feature` del Front espera el mismo cambio.
- **Periodo que no existe en US-72 (T032).** V1_03 registra 2025-1, 2025-2, 2026-1 y 2026-2, así que el ejemplo «el periodo 2025-2, que no existe en abet.periodo» del esquema «Un argumento inválido se rechaza antes de escribir» era imposible. La fila pasa a 2027-1, el periodo que ya usa como inexistente BR-PERIODO-01.
- **Comprobación de arranque en cualquier periodo (T033).** El escenario «El arranque de la API revisa el conjunto de reglas de cada carrera con plan» no tiene secciones en 2026-1, así que FR-007 y BR-PERIODO-06 se cumplen con cada carrera con plan de medición en cualquier periodo, como Q19, y no solo en un periodo con secciones. El mensaje del conjunto que falta nombra la carrera, así que la fila de R-NO-EXISTE del esquema «La API no arranca con un periodo o un conjunto de reglas que la base no conoce» de `specs/001-mvp-carga-r17/aceptacion/base_neon.feature` pasa a «CONJUNTO_REGLAS R-NO-EXISTE no existe para la carrera AMB.», con su nota fechada, y el texto de la spec 001 queda como historia. Sin ningún plan en la base, la versión debe existir para alguna carrera, como antes. El escenario de la biblioteca sin el conjunto de IND abre la sesión del profesor con V1_13 y quita después el conjunto de IND, y el de la carga de 450002 suma V1_14, que el Back con el `_ALCANCE` nuevo lee, como en el orden de FR-020.
- **Campo aditivo de la sesión (T031).** El paso de `acceso.feature` de la spec 001 que comparaba el cuerpo entero de `GET /api/sesion` compara ahora el correo y el rol, porque el campo `alcance` es aditivo, y la prueba de BR-ACCESO-03 de `tests/test_api_sesion.py` espera el alcance SECCIONES del profesor.
- **Texto del PI en la ruta 12 (T036).** BR-RESULTADOS-09 cierra las claves de cada indicador de la ruta 12 sin el texto del PI, así que el paso «el PI 6.1 trae el texto inventado de IND-2026» del escenario «El SO y el PI de la ruta 12 salen del catálogo de Industrial y no del de Ambiental» de `r17_industrial.feature` no tiene campo que comprobar. El paso pasa a «el PI 6.1 trae el instrumento «Portafolio 3» del plan de IND-2026 y la respuesta no repite ningún texto inventado de AMB-2026», que prueba el mismo catálogo sin agregar una clave al contrato.
- **Huella en el manifiesto (T034).** Una huella SHA-256 en hexadecimal trae con frecuencia ocho cifras seguidas, así que el paso del escenario «El manifiesto resume cada export sin códigos» de `exports_capacitacion.feature` dice ahora «el manifiesto, sin contar el campo sha256, no trae ningún número de ocho cifras ni ningún nombre», como el escenario del registro de US-76.
- **Permiso del rol de la API sobre el alcance (T023 y T027, corrección del 2026-11-23).** En Neon `abet_app` nace antes de V1_14 y `crear_rol_app.sql` da el SELECT de `acceso.coordinacion_alcance` solo si la tabla ya existe cuando corre, y ningún paso de FR-020 lo vuelve a correr. Con el Back nuevo, `_ALCANCE` y `alcance_de()` nombran esa tabla, PostgreSQL revisa el permiso de toda tabla de la consulta y cada cuenta recibiría 42501 con un 500 de la API. El callback `db/callbacks/afterMigrate__permisos_lectura.sql` da ahora ese SELECT al rol de la API en el mismo `migrate` que crea la tabla, así que el paso de las migraciones lo deja listo antes del despliegue. El escenario de la siembra completa crea el rol en V1_11, migra por la siembra y pide con ese rol el ingreso, `GET /api/sesion`, `GET /api/secciones` y el R-17 de la 410, y falla sin el cambio con 42501.
- **Siembra en seco sobre una rama sin V1_12 a V1_14 (T027, corrección del 2026-11-23).** En seco el paso de las migraciones corre solo `flyway info`, así que `alcance_coordinacion_ambiental.sql`, el plan de Química, la programación, la coordinación y los controles fallaban en una base en V1_11, como develop y main antes de la siembra. `sembrar_quimica.py` anuncia en seco esos pasos sin correrlos mientras `acceso.coordinacion_alcance` no existe, y el escenario «La siembra completa deja la misma huella de Ambiental y los controles limpios» corre la siembra completa en seco sobre una base en V1_11 antes de aplicarla.
- **Huella de Ambiental en el segundo tramo (T027, corrección del 2026-11-23).** La siembra con `--aplicar` se detiene en el despliegue y se reanuda con `--desde plan_quimica --back-desplegado`, que salta `huella_antes`, así que la comparación de la huella se perdía en silencio. El primer tramo escribe la huella en la orden para reanudar, el segundo la recibe con `--huella-antes`, y una corrida en la que `huella_despues` corre sin `huella_antes` ni `--huella-antes` termina con 2 antes de conectarse. `tests/test_sembrar_quimica.py` lo prueba sin base, y el escenario de la siembra completa, en los dos tramos.
- **Correo de la coordinación y en_windows.py (T027, corrección del 2026-11-23).** `~/.claude/scripts/en_windows.py` vive fuera del repositorio y solo corre por SSH en el Windows de Jefferson, así que una prueba del clúster desechable no puede correrlo. El escenario «Ninguna salida de la siembra repite el correo de la coordinación» pasa a «Cuando la siembra corre el registro de la coordinación con la variable en su entorno, como la deja en_windows.py» y «Entonces ni los informes ni la salida de la siembra muestran el valor de esa variable», sin cambiar los conteos. La salida del propio en_windows.py se revisa en T071.
- **Formas del generador (T034, propuesta).** `scripts/generar_exports_desde_maestra.py` recorta la hoja a los 31 caracteres que admite Excel, como Blackboard, y comprueba con `seccion_declarada()` de `abet_carga` que la hoja y el nombre declaren la sección. Una fila defectuosa nombra las dos filas de un estudiante repetido. `--ejercicio N` usa el curso EJERCICIO_AAAAC_ASIGNATURA_SECCION, no pide la programación y escribe códigos nuevos del rango 99 en cada archivo. `--tarjetas` lee un CSV con las columnas seccion y archivo, ignora las demás y compara cada fila con `--manifiesto`.
- **Formas del conciliador (T037, propuesta).** `db/herramientas/conciliar_tabla_maestra.py` toma la conexión de las variables de libpq, como `sembrar_quimica.py`, abre cada transacción READ ONLY y termina con 3 si la base no responde, un código que FR-018 no nombraba. Sin `--datos-reales` exige códigos del rango 99 y rechaza por su número de fila, sin mostrar el código, la que trae otro, y con `--datos-reales` acepta cualquier código de ocho cifras. Compara el logro como los estudiantes con nivel 3 o 4, el criterio de M25 del R-17 a mano, sobre los calificados, y el porcentaje con el redondeo de ROUND de PostgreSQL. En los PI distintos de `--pi` solo cuenta las filas de cada lado. Las pruebas leen «las filas de la 702 en el PI 6.2» como las mismas cinco filas con el PI 6.2 en lugar del 6.1, y el escenario «La conciliación no escribe en la base», sin Dado propio, publica las tres cargas y descarga sus R-17 en el paso Cuando antes de tomar el conteo, porque sin cargas no habría nada que leer. Ningún texto del `.feature` cambia.

## User Scenarios & Testing *(mandatory)*

### US-67: Catálogo IND-2026 de Ingeniería Industrial desde su referencia curricular (Priority: P1)

Como administrador técnico, quiero cargar Ingeniería Industrial con su catálogo IND-2026 de 7 SO, 21 PI y 53 asignaturas desde una referencia generada de la hoja «Información por Asignatura», para que 5643 tenga un PI 6.1 de Industrial al que apuntar sin tocar AMB-2026.

**Why this priority**: sin el catálogo no existe el PI 6.1 de Industrial, cuyo texto es distinto del de Ambiental, y `fk_plan_medicion_pi` y `fk_plan_medicion_asig_so` impiden el plan de 5643. Todo el ciclo empieza aquí.

**Independent Test**: en una base desechable con V1_01 a V1_11, Flyway aplica V1_12 y la base tiene IND-2026 en BORRADOR con 7 SO, 21 PI, 53 filas de plan de estudios, el par 5643 y SO 6 y «Portafolio 3», mientras AMB-2026 conserva sus filas.

**Base**: `abet.carrera` (IND en la facultad FI), `abet.catalogo_version` (IND-2026 en BORRADOR con `ck_catalogo_version_huella`), `abet.so`, `abet.pi` (`uq_pi_codigo`, `ck_pi_codigo_so`, `descripcion` varchar(300)), `abet.rubrica_nivel` (0 filas), `abet.asignatura` (38 nuevas y 15 reutilizadas, `uq_asignatura_codigo`, cambio del 2026-11-23), `abet.plan_estudios` (`ck_plan_estudios_ciclo`), `abet.asignatura_so` y `abet.instrumento` (`uq_instrumento`). `db/referencia/industrial_2026.json`, `db/herramientas/generar_v1_12.py`, `db/migration/V1_12__cargar_referencia_industrial.sql` y `db/pruebas/pruebas.sql`.
**Pantalla**: ninguna propia. P2 muestra después «Química General» desde `abet.asignatura`.

**Acceptance Scenarios** (`specs/008-ciclo-quimica-industrial/aceptacion/catalogo_industrial.feature`):

1. **V1_12 carga IND-2026 con sus conteos**, el PI 6.1 del SO 6, el par 5643 y SO 6 y «Portafolio 3».
2. **5643 se reutiliza sin tocar Ambiental**, y `abet.asignatura` gana 38 filas y queda con 91 (cambio del 2026-11-23).
3. **La sección 1 de `pruebas.sql` cuenta por catálogo** y la corrida termina sin «FALLA».
4. **`generar_v1_12.py` es determinista** y la prueba regenera V1_12 sin diferencias.
5. **Una referencia mal formada se rechaza antes de escribir (esquema)**, con el SO del PI, el PI repetido, el código, el nombre distinto, el largo de la descripción y el ciclo de malla.
6. **La aserción final detiene la migración** con un conteo que no coincide, sin dejar filas de IND-2026.

---

### US-68: Reglas de Industrial y comprobación de arranque por carrera (Priority: P1)

Como administrador técnico, quiero que Industrial tenga su conjunto R-2026-BORRADOR con NIVEL_ESPERADO 3 y META_LOGRO 0,80 y que la API revise al arrancar el conjunto de cada carrera con plan, para que la carga de 5643 use las reglas de su carrera y calcule el porcentaje con la misma regla de los R-17 a mano.

**Why this priority**: `abet_carga/carga.py` busca el conjunto por la carrera del plan, y V1_06 solo siembra Ambiental, así que la primera subida de química termina en un 500. La comprobación de arranque de `app/configuracion.py` pasa con el conjunto de Ambiental y no lo detecta.

**Independent Test**: con V1_13, una carga inventada de la 701 queda PUBLICADA con el conjunto de IND y la vista da 6 de 10, 60,0 y 80,0, mientras sin V1_13 `cargar()` lanza ConfiguracionInvalida y la API no arranca.

**Base**: `abet.conjunto_reglas` (`uq_conjunto_reglas_carrera`), `abet.parametro_valor`, `abet.carga` (`fk_carga_reglas`), `abet.v_r17_por_pi`, `db/migration/V1_13__cargar_reglas_industrial.sql`, `abet_carga/carga.py`, `app/configuracion.py` y la consulta de control Q19.
**Pantalla**: P4 y la hoja «Constancia» del R-17 muestran el conjunto de IND en BORRADOR.

**Acceptance Scenarios** (`catalogo_industrial.feature`):

1. **V1_13 siembra R-2026-BORRADOR de IND** con META_LOGRO 0,80, NIVEL_ESPERADO 3 y los demás parámetros en PENDIENTE.
2. **La carga de 5643 toma las reglas de Industrial**, con 6 de 10, `pct_logro_sobre_calificados` 60,0, `meta_logro_pct` 80,0 y provisional verdadero.
3. **La carga de 450002 sigue con las reglas de Ambiental.**
4. **Sin el conjunto de IND la biblioteca no guarda nada**, y la ruta 5 responde el 500 genérico sin nombrar la variable.
5. **El arranque revisa cada carrera con plan** y su mensaje no dice «Ambiental».
6. **Q19 lista la carrera con plan sin conjunto de reglas.**

---

### US-69: Vigencia de IND-2026 en 2026-1 y plan de medición de 5643 (Priority: P1)

Como administrador técnico, quiero registrar IND-2026 como catálogo vigente de Industrial en 2026-1 y el plan de 5643 con el PI 6.1, el «Portafolio 3» y su descripción, primero en seco y después aplicado, para que las 18 secciones de Química General tengan plan y el R-17 escriba la descripción del instrumento.

**Why this priority**: `fk_plan_medicion_vigencia` exige la vigencia antes del plan, y BR-PERIODO-03 deja la vigencia y el plan fuera de las migraciones. Sin este guion, P2 dice «La carrera aún no registra el plan de medición de esta sección» y «Subir export» queda desactivado.

**Independent Test**: `plan_quimica_2026_1.sql` sin `aplicar` informa 1 vigencia y 1 fila de plan sin escribir, y con `-v aplicar=1` deja la vigencia de IND-2026 en 2026-1 y el plan de 5643 con el PI 6.1, mientras la huella de Ambiental no cambia.

**Base**: `abet.periodo` (2026-1 desde V1_03), `abet.catalogo_vigencia`, `abet.plan_medicion` (`uq_plan_medicion`, `fk_plan_medicion_vigencia`, `fk_plan_medicion_asig_so`, `descripcion_instrumento` varchar(400) con `ck_plan_medicion_descripcion`), `db/datos/plan_quimica_2026_1.sql` (en seco salvo `-v aplicar=1`, el PI por `-v pi` y la descripción por `\getenv DESCRIPCION_INSTRUMENTO`), `db/plataforma/neon/huella_ambiental.sql` y las consultas Q05 y Q18.
**Pantalla**: P2 deja de mostrar el texto de la sección sin plan en 5643 y P3 nombra el PI 6.1.

**Acceptance Scenarios** (`catalogo_industrial.feature`):

1. **La corrida en seco informa y no escribe.**
2. **Con `aplicar` quedan la vigencia y el plan** con el PI 6.1, «Portafolio 3» y la descripción de la variable.
3. **Repetir el guion no duplica ni cambia filas.**
4. **Una fila de plan distinta detiene todo.**
5. **Una descripción inválida no entra (esquema)**, ausente, con un blanco al final o de 401 caracteres.
6. **Sin el par 5643 y SO 6 el plan no entra**, por `fk_plan_medicion_asig_so`.
7. **Ambiental en 2026-2 queda igual**, con la misma huella y Q05 y Q18 en 0 filas.
8. **Q18 detecta un curso con plan de dos carreras en el mismo periodo**, sin correos ni códigos.

---

### US-70: La coordinación de una carrera ve solo su carrera (Priority: P1)

Como coordinación de Ingeniería Ambiental, quiero ver solo las secciones de mi carrera aunque el sistema sume Industrial, para no leer ni reemplazar cargas que mide otra carrera.

**Why this priority**: `_ALCANCE` de `app/permisos.py` da al COORDINADOR toda sección de una asignatura del plan de estudios de cualquier catálogo vigente del periodo. En cuanto IND-2026 esté vigente en 2026-1, la coordinación de Ambiental vería las 18 secciones de 5643 con datos reales, contra BR-ACCESO-07.

**Independent Test**: con V1_14 y la fila de alcance de AMB, `coordinacion@example.invalid` recibe 0 secciones en 2026-1 y la 410 y la 411 en 2026-2, y recibe 403 con el identificador de la 701.

**Base**: `acceso.coordinacion_alcance` (nueva, V1_14) con `usuario_id`, `carrera_id`, `asignatura_id`, `periodo_id` y `asignado_en`, `ck_coordinacion_alcance_uno`, `ck_coordinacion_alcance_periodo` (J-49), `uq_coordinacion_alcance` con NULLS NOT DISTINCT y sus claves foráneas, solo SELECT para `abet_app` en `db/plataforma/neon/crear_rol_app.sql`, `db/pruebas/probar_rol_app.sql`, `crear_roles_lectura.sql` vuelto a correr, `db/datos/alcance_coordinacion_ambiental.sql`, `_ALCANCE` y la consulta Q20. BR-ACCESO-07 y BR-ACCESO-08 con un cambio fechado y BR-ACCESO-13 (propuesta).
**Pantalla**: P2, P5, P6 y P7 sin cambio visual, con menos secciones.

**Acceptance Scenarios** (`alcance_coordinacion.feature`):

1. **Ambiental no ve Química en 2026-1.**
2. **Ambiental conserva la 410 y la 411 en 2026-2.**
3. **Una sección o una carga de Química responde el 403 de siempre (esquema)**, en las rutas 8, 6 y 7.
4. **Un coordinador sin alcance no ve nada y Q20 lo lista** sin el correo, y su sesión trae el tipo CARRERA con las dos listas vacías.
5. **Con las dos carreras vigentes, el curso compartido sigue el valor provisional de J-50.**
6. **El guion de alcance de Ambiental corre antes del código nuevo** y se puede repetir.
7. **La base exige un solo alcance por fila (esquema)**, con las tres restricciones.
8. **`abet_app` solo lee la tabla de alcance**, con el SQLSTATE 42501.

---

### US-71: La coordinación de Química General ve todas las secciones de su curso (Priority: P1)

Como coordinador de Química General, quiero ver todas las secciones de 5643 en 2026-1, sus cargas, su constancia y su R-17 sin ver otro curso, para seguir el registro de los 18 profesores en la capacitación.

**Why this priority**: es la cuenta que el pedido exige con todas sus palabras, y hoy no existe ninguna forma de dar a una cuenta las secciones de un solo curso.

**Independent Test**: con la fila de alcance de 5643 en 2026-1, `coordinador.quimica@example.invalid` recibe la 701 a la 704 en ese orden y ninguna de 450002, su sesión trae el alcance CURSO, la subida sin `reemplaza` responde 403 y P2 dice «Secciones del curso» sin «Subir export».

**Base**: `acceso.usuario_autorizado` (rol COORDINADOR, `ck_usuario_autorizado_rol` sin cambios), `acceso.coordinacion_alcance` (fila de asignatura con periodo), `app/permisos.py` (`secciones_visibles()`, `puede_leer()` y `puede_reemplazar()` por el alcance, `puede_subir()` en falso), `app/sesion.py` y la ruta 2 con el campo `alcance`, y la consulta Q20. D-52 fija el reemplazo en su curso.
**Pantalla**: P2 con «Secciones del curso», «Ver los logros por SO del curso» y «El curso no tiene secciones en este periodo.» (propuestas) en `src/servicios/rotulos.ts`, elegidos por `alcance.tipo`, sin cambiar el tipo Rol.

**Acceptance Scenarios** (`alcance_coordinacion.feature`):

1. **Ve la 701 a la 704 en orden y ninguna de 450002.**
2. **La sesión dice el alcance** CURSO, CARRERA o SECCIONES sin un rol nuevo.
3. **Una cuenta con alcance de carrera y de curso recibe el tipo más amplio**, CARRERA, con la unión de las dos filas.
4. **La asignación vale solo en su periodo.**
5. **Lee la constancia y el R-17 de una sección de su curso.**
6. **No alcanza otro curso (esquema)**, con el 403 de siempre en las rutas 8, 6 y 7.
7. **No sube una carga nueva.**
8. **Reemplaza en su curso con el valor provisional de D-52**, con `subida_por` y Q06, Q07, Q10 y Q14 en 0 filas.
9. **Una cuenta dada de baja no alcanza nada.**
10. **El profesor del curso sigue viendo solo su sección.**
11. **Q20 lista una coordinación de curso con una sección propia.**
12. **P2 rotula el curso y no ofrece subir** (Vitest).
13. **La coordinación de la carrera conserva sus rótulos** (Vitest).
14. **El consejo de una sección cruzada remite al profesor** (Vitest).

---

### US-72: Registro de la coordinación del curso con corrida en seco (Priority: P1)

Como administrador técnico, quiero registrar la cuenta de la coordinación de un curso con su asignatura y su periodo, en seco primero y con `--aplicar` después desde el Windows, para habilitarla sin escribir el correo real en el repositorio ni en un argumento.

**Why this priority**: la cuenta debe existir en Neon antes de la capacitación, y el correo real nunca entra a git, así que llega solo por una variable que lleva `en_windows.py`.

**Independent Test**: con `CORREO_COORDINACION` inventada, el guion sin `--aplicar` informa 1 cuenta y 1 alcance sin repetir el correo y sin escribir, y con `--aplicar` dos veces deja 1 fila en cada tabla y sin contraseña.

**Base**: `acceso.usuario_autorizado` (`uq_usuario_autorizado_correo`, `ck_usuario_autorizado_correo`), `acceso.coordinacion_alcance`, `abet.asignatura`, `abet.periodo` y `abet.plan_medicion` para el aviso, y `db/herramientas/registrar_coordinacion.py` (propuesta), que usa INSERT con ON CONFLICT DO NOTHING y nunca UPDATE de rol ni de `activo`. BR-ACCESO-14 (propuesta).
**Pantalla**: ninguna. Guion de línea de comandos que corre desde el Windows de Jefferson.

**Acceptance Scenarios** (`alcance_coordinacion.feature`):

1. **La corrida en seco informa sin repetir el correo.**
2. **Con `--aplicar` escribe una vez y se puede repetir**, con el correo normalizado.
3. **Un correo que ya es profesor detiene el guion** con código 1, sin cambiar su rol.
4. **Una cuenta dada de baja no se reactiva.**
5. **Un argumento inválido se rechaza antes de escribir (esquema)**, con la asignatura o el periodo.
6. **Sin la variable el guion no adivina**, con código 2.
7. **Una asignatura sin plan entra con aviso.**
8. **El guion no escribe contraseñas ni las muestra.**

---

### US-73: Cada cuenta elige el periodo que trabaja (Priority: P1)

Como profesor o coordinación de Química General, quiero trabajar en 2026-1 aunque `PERIODO_VIGENTE` sea 2026-2, para registrar y revisar la medición de un ciclo ya cerrado sin cambiar la configuración de la carrera.

**Why this priority**: `listarSecciones()` y `obtenerResultados()` se llaman sin periodo y la ruta 8 sin `seccion_id` usa siempre el periodo vigente, así que el profesor de 5643 lee en P2 «No tiene secciones asignadas en este periodo.» y el flujo se corta en el primer paso.

**Independent Test**: con `PERIODO_VIGENTE` 2026-2, la ruta 18 da a `docente701@example.invalid` los periodos ["2026-1"], P2 abre en 2026-1 con «5643 Química General, sección 701, 2026-1» y la ruta 8 con `periodo=2026-1` trae su carga, mientras sin periodo la ruta 8 sigue como hoy.

**Base**: `abet.periodo` (`uq_periodo_codigo`, `ck_periodo_codigo`), `abet.seccion`, `app/permisos.secciones_visibles()`, la ruta 18 nueva `GET /api/periodos` (`app/rutas/periodos.py`, propuesta), la ruta 8 con el parámetro aditivo `periodo` y `tests/rutas_registradas.py`. BR-PERIODO-05 (propuesta) y BR-CARGA-20 con un cambio fechado.
**Pantalla**: la cabecera de `App.tsx` con «Periodo 2026-1» o el selector «Periodo» (propuestas), que P2, P3, P4, P5, P6 y P7 respetan, con el estado en memoria y `src/servicios/api.ts` que pasa el periodo a las rutas 4, 8, 12 y 17.

**Acceptance Scenarios** (`periodo_elegido.feature`):

1. **La ruta 18 lista solo los periodos con secciones al alcance de cada cuenta.**
2. **Con secciones en dos periodos los da del más reciente al más antiguo.**
3. **Sin sesión responde 401** y figura en las rutas registradas.
4. **La ruta 8 con periodo lista solo ese periodo**, y sin periodo sigue como hoy.
5. **Un periodo mal formado responde 422 (esquema).**
6. **Un periodo sin secciones da una lista vacía.**
7. **Pedir otro periodo no agrega secciones ajenas.**
8. **La subida en 2026-1 no exige el periodo vigente.**
9. **Un export de otro periodo se rechaza** con el texto de `_OTRO_PERIODO`.
10. **Sin secciones en el periodo vigente, P2 abre en el más reciente con secciones** (Vitest).
11. **Con dos periodos la cabecera ofrece el selector** (Vitest).
12. **Cambiar el periodo vuelve a pedir P2, P5 y P6** (Vitest).
13. **La marca de la última carga rechazada sale del periodo elegido** (Vitest).
14. **El periodo se conserva en el recorrido y no se guarda en el navegador** (Vitest).
15. **Si la ruta 18 falla, P2 usa el vigente sin error** (Vitest).
16. **En un periodo sin secciones, P2 remite al selector** (Vitest).
17. **La coordinación del curso trabaja 2026-1 en P2, P5, P6 y P7** (Vitest).

---

### US-74: Exports de capacitación generados desde la tabla maestra (Priority: P1)

Como Oficina de Calidad, quiero un export por sección con el formato que el sistema lee, los códigos y los niveles de la tabla maestra y sin nombres, para que cada profesor de química suba el suyo en la capacitación.

**Why this priority**: los profesores de química no calificaron en Blackboard, así que sin estos archivos no hay nada que subir y el ciclo no corre con la medición real (decisión A de Jefferson).

**Independent Test**: con una tabla maestra y una programación inventadas, el generador escribe tres archivos que el lector reconoce por su nombre y su hoja y que `validar()` acepta sin rechazos, con los mismos niveles de la tabla, y se niega a escribir dentro de un repositorio.

**Base**: `abet.seccion.curso_blackboard` (`uq_seccion_curso_bb`), `abet.estudiante` (`ck_estudiante_codigo`), `abet.medicion` (`ck_medicion_nivel`), `abet.carga_columna` (`ck_carga_columna_encabezado`), `_CURSO` y `_NOMBRE_DE_BLACKBOARD` de `abet_carga/validacion.py`, `_ENCABEZADO_DE_PI` y `COLUMNAS_DE_CODIGO` de `abet_carga/lector.py`, la consulta Q04 y `scripts/generar_exports_desde_maestra.py` (propuesta), que reutiliza la escritura determinista de `scripts/generar_exports_inventados.py`.
**Pantalla**: ninguna. Los archivos entran por P3.

**Acceptance Scenarios** (`exports_capacitacion.feature`):

1. **Cada sección da un export que el lector y la validación aceptan.**
2. **La ida y vuelta por el lector da los mismos códigos y niveles.**
3. **El export trae solo el código y la columna del PI**, sin nombres ni el profesor.
4. **Un código con cero a la izquierda se escribe como texto.**
5. **El curso de cada archivo es el de la programación.**
6. **Dos corridas dan los mismos archivos byte a byte.**
7. **El manifiesto resume cada export sin códigos.**
8. **Las filas de otro periodo, asignatura o PI se omiten y se cuentan.**
9. **El PI llega por parámetro para D-48.**
10. **Una fila defectuosa detiene la generación sin mostrar el valor (esquema).**
11. **Sin la columna CALIFICACIÓN el generador no adivina.**
12. **La carpeta de salida dentro de un repositorio se rechaza.**
13. **La salida no muestra códigos ni nombres.**
14. **Un archivo de ejercicio por profesor tiene su propia huella.**

---

### US-75: El export de 5643 se publica entero en Ingeniería Industrial (Priority: P1)

Como profesor de una sección de Química General, quiero subir el export de mi sección y que el sistema lo publique con todas sus filas en Ingeniería Industrial, para tener mi R-17 sin llenarlo a mano.

**Why this priority**: es el corazón del ciclo, y ningún escenario prueba hoy una asignatura de cuatro cifras de Industrial ni la carrera de la carga.

**Independent Test**: el export inventado de 34 filas de la 701 queda PUBLICADA con 34 de 34 filas, `abet.carga.carrera_id` de IND, 34 mediciones del PI 6.1 de IND-2026 y los controles en 0 filas.

**Base**: `abet.archivo_origen`, `abet.carga` (`fk_carga_reglas`, `ck_carga_publicable`, `uq_carga_publicada_por_seccion`), `abet.carga_columna`, `abet.carga_fila`, `abet.medicion`, `abet.estudiante`, `abet.seccion.curso_blackboard`, `abet_carga/validacion.py` y la consulta Q21 nueva. BR-CARGA-03, BR-CARGA-11, BR-CARGA-12, BR-CARGA-14 y BR-CARGA-15 sin cambios.
**Pantalla**: P3 «Subir export» y P4 «Resultado de la carga».

**Acceptance Scenarios** (`carga_quimica.feature`):

1. **34 filas de 1 a 4 quedan PUBLICADA enteras en Industrial**, con Q01, Q02, Q03, Q04, Q06, Q10, Q12 y Q13 en 0 filas.
2. **La asignatura de cuatro cifras se lee en el nombre de un export de texto.**
3. **El export que arma el generador con la programación se publica sin rechazos.**
4. **Q21 detecta una sección cuyo curso de Blackboard declara otra sección.**

---

### US-76: Los errores probables de la sala se rechazan sin mostrar notas ni códigos (Priority: P2)

Como profesor de química en la capacitación, quiero que el archivo de otra sección, el Excel con la nota sobre 20, un nivel con medio punto, un libro sin Username o el mismo archivo dos veces tengan una respuesta clara y sin valores, para corregir en la sala sin exponer datos de mis alumnos.

**Base**: `abet.rechazo_fila` (`ck_rechazo_fila_motivo`, sin columna de valor), `abet.carga` (RECHAZADA), `abet.archivo_origen` (`uq_archivo_origen_sha256`), `abet.carga_columna` (`ck_carga_columna_puntaje`), BR-CARGA-08, BR-CARGA-09 y BR-CARGA-10, y la consulta Q04.
**Pantalla**: P3 y P4.

**Acceptance Scenarios** (`carga_quimica.feature`): el archivo de otra sección (SECCION_NO_COINCIDE con 0 filas leídas), una columna que el lector no reconoce (esquema, PI_DEL_PLAN_AUSENTE), la nota sobre 20 entre filas válidas (PUBLICADA con 4 de 34 y el aviso PUNTAJE_MAXIMO_DISTINTO), el Excel con todas las notas sobre 20 (RECHAZADA sin campo de valor), el medio punto (NIVEL_NO_NUMERICO), el libro sin Username ni Student ID (COLUMNA_CODIGO_AUSENTE), el mismo archivo dos veces (200 con la constancia existente), los nombres que no llegan a la base (Q04 en 0) y el registro sin códigos ni notas fuera del campo `sha256`.

---

### US-77: P4 dice qué corregir en filas rechazadas y avisos sin remitir a Blackboard (Priority: P2)

Como profesor de química cuya carga se publicó con filas rechazadas o con el aviso del puntaje máximo, quiero leer en P4 qué corregir, para que mi R-17 no quede incompleto ni con notas sobre 20 tomadas como niveles.

**Base**: la constancia de la ruta 6 con rechazos y avisos (BR-R17-10), la tabla de J-43 de `src/servicios/ayudas.ts` con los motivos RECHAZA_FILA y el aviso PUNTAJE_MAXIMO_DISTINTO, y `queCorregir()` que acepta también una carga PUBLICADA. El texto `CORREGIR_SIN_FILAS_ACEPTADAS` cambia con una fecha en la spec 007.
**Pantalla**: P4 «Resultado de la carga».

**Acceptance Scenarios** (`carga_quimica.feature`, todos `@delegado_a_vitest`): un consejo por motivo de fila (esquema de cinco motivos), el aviso del puntaje máximo arriba con role="status", la carga sin filas aceptadas que remite a la tabla sin nombrar Blackboard, la carga sin rechazos sin consejo, el motivo desconocido sin consejo con la prueba que recorre los motivos del contrato y la remisión al reemplazo de P5 sin botón en P4 (J-53).

---

### US-78: El R-17 y P6 dicen la carrera, el SO y el PI de Industrial (Priority: P1)

Como profesor de Química General, quiero un R-17 que diga «Carrera de Ingeniería Industrial» y traiga el «Portafolio 3», mis conteos y mi porcentaje contra la meta de 80 %, y unos logros con el texto del PI de mi carrera, para entregar el R-17 del sistema en lugar del que llené a mano.

**Why this priority**: la plantilla dice en B6 «Carrera de Ingeniería Ambiental» y `_cabecera()` no la cambia, así que el profesor lo notaría al comparar con el suyo, cuyo encabezado dice Ingeniería Industrial.

**Independent Test**: el R-17 de la carga inventada de la 701 dice «Carrera de Ingeniería Industrial» en B6, se llama `R017_5643_701_2026-1_PROVISIONAL.xlsx`, trae M24 8, M25 26, E24 0,765 y G24 0,8, y el de una carga de 450002 sigue diciendo Ambiental.

**Base**: `abet.carrera.nombre` por `abet.carga.carrera_id`, `abet.v_r17_por_pi`, `abet.plan_medicion.descripcion_instrumento`, `abet.instrumento`, `abet.so` y `abet.pi` de IND-2026, `abet_carga/r17.py` (`_cabecera`) y `plantillas/R017_ambiental_general.xlsx`, sin migración. BR-R17-13 (propuesta) y BR-RESULTADOS-04 sin cambios.
**Pantalla**: P4 y P5 con «Descargar R-17», y P6 «Mis logros por SO».

**Acceptance Scenarios** (`r17_industrial.feature`):

1. **B6 dice la carrera de la carga (esquema)**, con IND y AMB.
2. **Ninguna otra celda nombra a Ambiental.**
3. **La cabecera y el bloque I** traen D8, D11, I11, B15, E17 y G17 y el nombre con _PROVISIONAL.
4. **Las cifras siguen la regla de la meta**, con M24 a M26, E24, G24 y el texto de NO_LOGRADO en H24.
5. **La franja provisional nombra el conjunto.**
6. **La tabla de estudiantes no trae nombres ni el profesor** y no tiene fórmulas.
7. **Un PI sin descriptores de rúbrica no cambia el R-17.**
8. **Otro profesor del curso no descarga el R-17.**
9. **El SO y el PI de la ruta 12 salen de IND-2026**, con 26 de 34 y 76.5.
10. **La fila de P6 dice la cifra, la meta y el resultado con palabras** y la barra tiene su aria-label (Vitest).
11. **Una sección en la meta lo dice con palabras** (Vitest).

---

### US-79: La ruta 17 y P7 alcanzan a la coordinación del curso (Priority: P2)

Como coordinador de Química General, quiero ver en una sola página cuántas secciones de mi curso tienen su carga publicada y cuáles faltan, para recordar el registro sin abrir sección por sección.

**Base**: la ruta 17 `GET /api/avance` y P7 de la etapa B de la spec 007 (US-64 y US-65, J-47 y J-48), construidas aquí con el alcance de `secciones_visibles()` y sin una rama por rol, `abet_carga/avance.py`, `app/rutas/avance.py` y `src/pantallas/Avance.tsx`.
**Pantalla**: P7 «Avance del registro del curso» (propuesta) para el alcance CURSO, con `pantallaDeLlegada(usuario)` de J-46.

**Acceptance Scenarios** (`avance_del_curso.feature`): la etapa de las cuatro secciones del curso sin la 410 ni la 411, el periodo sin secciones vacío, el 403 del profesor, la coordinación de Ambiental sin las secciones de Química, P7 con el título del curso como llegada (Vitest), «Ver la carga» hacia P4 (Vitest) y el seguimiento en P2 si P7 no llega (Vitest). Los escenarios de `avance_del_registro.feature` de la spec 007 siguen vigentes.

---

### US-80: Cumplimiento del curso con la suma de estudiantes, si D-32 se responde (Priority: P3)

Como coordinador de Química General, quiero ver el porcentaje de alumnos con nivel 3 o 4 de cada sección y del curso entero frente a la meta de 80 %, para saber si el curso cumple el PI 6.1 y qué secciones lo bajan.

**Base**: `abet.v_r17_por_pi` como única fuente de las cifras (BR-R17-02), la ruta 12 con el campo aditivo `agregados` solo para el COORDINADOR (propuesta), D-32 y D-33 de la spec 004, y BR-RESULTADOS-03, BR-RESULTADOS-05, BR-RESULTADOS-06 y BR-RESULTADOS-09 con un cambio fechado. Se construye solo si D-32 se responde antes (J-54).
**Pantalla**: P6 «Logros por SO del curso» con la fila del curso sobre las de las secciones (propuesta).

**Acceptance Scenarios** (`avance_del_curso.feature`): el porcentaje de cada sección como en su R-17 (70.0, 90.0 y 53.8), el agregado de 23 de 33 con 69.7 que no vale el promedio de 71.3, el curso sin cargas sin un porcentaje inventado, el profesor sin el agregado (D-33), ninguna cifra que revele a un estudiante y P6 con el curso antes de las secciones (Vitest).

---

### US-81: Sistema visual común, claro y accesible AA (Priority: P1)

Como profesor o coordinación que usa el sistema una o dos veces por ciclo, quiero pantallas con jerarquía clara, estados reconocibles, el camino de cada sección y buen contraste, para completar el registro sin perderme.

**Why this priority**: el pedido literal dice que el sistema se tiene que ver mejor, y hoy cada pantalla es una serie de párrafos de igual peso con un solo gris de `src/componentes/estilos.ts`, sin tokens ni prueba de contraste, y el botón principal de P2 es siempre «Subir export» aunque la sección ya esté publicada.

**Independent Test**: la prueba de contraste calcula cada par de los tokens de `src/index.css` con al menos 4,5 a 1, P2 de una sección PUBLICADA muestra «Ver resultado» como botón principal y el paso actual con `aria-current="step"`, y las pruebas de Vitest de la spec 007 pasan sin cambios salvo las que nombra FR-019.

**Base**: ninguna tabla. `src/index.css` (`@theme`), `src/componentes/estilos.ts`, `Mensaje.tsx`, `Titulo.tsx`, `AvisosCarga.tsx` y `TablaRechazos.tsx`, con la dirección visual de la skill frontend-design, fuentes del sistema (J-59) y sin dependencias nuevas.
**Pantalla**: Ingreso, la cabecera de `App.tsx`, P2 a P7 y `AvisoSesion`.

**Acceptance Scenarios** (`sistema_visual.feature`, todos `@delegado_a_vitest`): el contraste AA de los tokens, el componente y el rol de cada estado (esquema), los rótulos fijados sin cambios, la tarjeta de P2 con el camino y el paso actual (esquema), el botón principal del paso actual, la sección sin plan sin pasos, la marca del paso escrita, la coordinación sin pasos ni ruta 8, el error de Ingreso junto al formulario, el bloqueo por intentos, el movimiento reducido y ningún recurso de terceros ni dependencia nueva.

---

### US-82: Uso a 375 px y con teclado (Priority: P2)

Como profesor que abre el sistema desde el celular o solo con el teclado, quiero que ninguna pantalla se desplace de lado y que el foco se vea, para registrar desde cualquier equipo.

**Base**: `e2e/` de Playwright 1.64.1 con la API simulada, sin axe-core (C-T06 de la spec 007).
**Pantalla**: Ingreso y P2 a P7.

**Acceptance Scenarios** (`sistema_visual.feature`, todos `@playwright`): ningún desplazamiento lateral a 375 px y botones de al menos 24 por 24 px (esquema de siete pantallas), la tabla de rechazos en su región desplazable, el foco visible en orden de lectura en P3 y el menú principal con el teclado.

---

### US-83: El conciliador compara la base y los R-17 con la tabla maestra sin mostrar códigos (Priority: P1)

Como Oficina de Calidad, quiero comparar lo que el sistema mide y los R-17 que genera con la tabla maestra por sección, por estudiante y por nivel, para confiar en que el sistema reproduce el R-17 de cada profesor.

**Why this priority**: lo que Jefferson y Stefanny llaman la magia es que el sistema dé el mismo R-17 que el profesor llenó a mano, y la tabla maestra, igual alumno por alumno a esos R-17, es el único oráculo independiente. Hacerlo a ojo en 18 secciones es lento y propenso a error.

**Independent Test**: con tres cargas inventadas iguales a la tabla, el conciliador dice «3 de 3 secciones iguales.» y termina con código 0, y con un nivel cambiado dice qué sección y qué tipo de diferencia sin un solo número de ocho cifras.

**Base**: `abet.v_tabla_maestra_pi`, `abet.v_r17_por_pi`, `abet.carga` (PUBLICADA), `abet.medicion`, el rol `abet_respaldo` en READ ONLY, las celdas M24 a M26, E24 y la tabla desde la fila 43 del R-17, y `db/herramientas/conciliar_tabla_maestra.py` (propuesta) con openpyxl.
**Pantalla**: ninguna. La guía muestra el informe en la sala.

**Acceptance Scenarios** (`ensayo_y_conciliacion.feature`): todo igual en la base, la vista y los R-17, una calificación distinta sin el código, cada diferencia por su tipo (esquema), la sección sin carga publicada, el mismo cociente con otro redondeo, la carga reemplazada sin filas duplicadas, el orden y la columna PROFESOR que no cuentan, los códigos que no empiezan con 99, la negativa a leer dentro de un repositorio y la lectura sin escritura.

---

### US-84: Ensayo de punta a punta de los exports antes de la capacitación (Priority: P1)

Como Oficina de Calidad, quiero un ensayo que suba los exports generados en una base aparte, descargue cada R-17 y pase el conciliador, para saber antes de la sala que las 18 secciones salen iguales a los R-17 de los profesores.

**Why this priority**: el ensayo prueba a la vez el generador, el lector, la regla de la meta, el R-17 y el conciliador, y encuentra antes de la sala una diferencia de redondeo o del PI 6.2. Correrlo en una base aparte importa porque `uq_archivo_origen_sha256` haría que la subida en la sala devolviera la constancia del ensayo.

**Independent Test**: los tres exports inventados quedan PUBLICADA sin rechazos, sus huellas son las del manifiesto, el conciliador dice «3 de 3 secciones iguales.» y los controles quedan en 0 filas.

**Base**: la biblioteca `abet_carga` (`cargar()` y `r17.generar()`), el manifiesto de US-74, el conciliador de US-83, `db/herramientas/ensayar_capacitacion.py` (propuesta), que sube cada export del manifiesto con `cargar()`, descarga su R-17 con `r17.generar()` y llama al conciliador, con 0 si todo es igual y 1 ante una diferencia, y, en la corrida real, una rama hija de develop en Neon desde el Windows (J-52).
**Pantalla**: ninguna.

**Acceptance Scenarios** (`ensayo_y_conciliacion.feature`): las secciones iguales con los controles en 0, el manifiesto que coincide por huella y por conteo, un nivel distinto que detiene la conclusión y el ensayo en una base aparte que no deja huellas en la de la capacitación.

---

### US-85: Humo con Playwright de punta a punta en la vista previa (Priority: P1)

Como equipo del sistema, quiero una prueba de humo con Playwright que recorra la vista previa de develop con un profesor de Química General y con la coordinación del curso, para comprobar en el despliegue de la capacitación que el profesor sube y descarga su R-17 y que la coordinación ve las secciones de su curso y nada más.

**Why this priority**: el ensayo de US-84 prueba la biblioteca, pero la capacitación corre en Vercel con Neon, cookies y la protección del proyecto, y solo el humo dice antes de la sala si P2 abre en 2026-1, si la carga encuentra las reglas de Industrial y si el alcance del curso funciona.

**Independent Test**: en la vista previa con la siembra inventada, `docente701@example.invalid` sube su export y descarga un R-17 con «Carrera de Ingeniería Industrial» en B6, y `coordinador.quimica@example.invalid` llega a P7 o a P2 con las cuatro secciones del curso y no puede subir.

**Base**: `acceso.usuario_autorizado`, `acceso.docente_seccion`, `acceso.coordinacion_alcance`, `acceso.credencial` (contraseñas con getpass de `asignar_claves.py`), `abet.carga`, `e2e/humo_quimica.spec.ts` (propuesta) y `herramientas_neon/lectura_neon.sh` para contar cargas desde el Windows.
**Pantalla**: P1 a P7.

**Acceptance Scenarios** (`capacitacion_en_develop.feature`, todos `@playwright`): el profesor que sube y descarga su R-17, el profesor que no alcanza otra sección, la coordinación con las secciones del curso y el avance, la coordinación en P2 sin la etapa B, la coordinación que no sube ni ve otro curso, las capturas sin datos sensibles, la vista previa ya usada que se detiene y el humo que no corre sobre la siembra de la capacitación.

---

### US-86: Siembra de Química en develop desde el Windows, en orden y sin cambiar Ambiental (Priority: P1)

Como administrador técnico, quiero sembrar en la rama develop de Neon, desde el Windows y con los ayudantes de `herramientas_neon`, las migraciones V1_12 a V1_14, el alcance de Ambiental, el plan de Química, la programación de las 18 secciones, la coordinación y las contraseñas, cada paso en seco antes de aplicarlo y con una huella de Ambiental antes y después, para que la capacitación arranque sin tocar 450002.

**Why this priority**: la regla global de Jefferson exige que toda escritura en una base salga del Windows, y el orden importa, porque la vigencia de IND-2026 antes del alcance nuevo dejaría a la coordinación de Ambiental ver Química.

**Independent Test**: en una base que imita develop, la siembra completa deja la misma huella de Ambiental, `controles_neon.sql` termina con «RESULTADO: Q01 a Q14 y Q18 a Q21 devuelven 0 filas.» y una segunda siembra suma 0 filas.

**Base**: `db/herramientas/respaldar_neon.sh`, `herramientas_neon/migrar_neon.sh`, `db/datos/alcance_coordinacion_ambiental.sql`, `db/datos/plan_quimica_2026_1.sql`, `db/herramientas/cargar_programacion.py` con `--periodo 2026-1`, `db/herramientas/registrar_coordinacion.py`, `herramientas_neon/asignar_claves.py`, `db/plataforma/neon/huella_ambiental.sql` (nueva, solo lectura), `controles_neon.sql`, `marcar_entorno.sql`, `~/.claude/scripts/en_windows.py` y `db/herramientas/sembrar_quimica.py` (propuesta), que corre en orden los pasos de FR-020, en seco por omisión, se detiene en el primer paso con código distinto de 0, exige `--confirmo-principal` con `--rama principal` y hace la comprobación previa de la guardia, que lee `GUARDIA_DATOS_INVENTADOS` de la API y consulta en `pg_constraint` si `abet.estudiante` conserva `ck_estudiante_codigo_inventado` (`db/plataforma/neon/guardia_datos_inventados.sql`). La lectura de comprobación de la siembra real (propuesta) corre con `herramientas_neon/lectura_neon.sh`. BR-ACCESO-11 sin cambios.
**Pantalla**: ninguna.

**Acceptance Scenarios** (`capacitacion_en_develop.feature`): la misma huella y los controles limpios, el alcance de Ambiental antes de la vigencia de Industrial, la programación de 2026-1 con asignatura de cuatro cifras y Q21 en 0, la segunda siembra sin filas nuevas, el paso que falla y detiene los siguientes, la rama principal con su confirmación aparte, ninguna salida con el correo de la coordinación, la guardia de datos inventados apagada en la vista previa y en la base, y la lectura sin correos que confirma el alcance de las 18 secciones después de la siembra de la capacitación.

---

### US-87: Guía de la capacitación con rótulos verificados contra el Front (Priority: P1)

Como Oficina de Calidad, quiero una guía por rol con los pasos, los rótulos exactos de cada pantalla y un ejercicio de error guiado, para que cada profesor suba el export de su sección y la coordinación revise el avance sin ayuda individual en la sala.

**Why this priority**: la capacitación es el objetivo del pedido, y el rediseño de US-81 cambia las pantallas, así que una guía sin cotejo se desactualiza en silencio.

**Independent Test**: la prueba de cotejo encuentra en `src/` cada rótulo citado en `docs/capacitacion/guia_quimica.md` y falla si un rótulo cambia, y la guía no trae correos fuera de example.invalid, números de ocho cifras ni contraseñas.

**Base**: `acceso.usuario_autorizado` con correos de ejemplo, `abet.rechazo_fila` (SECCION_NO_COINCIDE), `src/pantallas` y `src/servicios/ayudas.ts`, el archivo de ejercicio de US-74 y el manifiesto para las tarjetas, que viven fuera de los repositorios.
**Pantalla**: P1 a P7 desde la guía.

**Acceptance Scenarios** (`guia_y_privacidad.feature`): cada rótulo citado existe, un rótulo cambiado hace fallar la guía, la guía sin datos que no debe, la fecha sin confirmar, el orden de las pantallas del profesor, el recorrido del profesor en la vista previa (Playwright), el ejercicio de error con un export inventado (Playwright), la guía de la coordinación sin correos mientras D-51 no se responda y las tarjetas que nombran el archivo del manifiesto, con `--tarjetas` del generador.

---

### US-88: Barrido de privacidad en los dos repositorios (Priority: P1)

Como responsable de los datos, quiero que cada cambio del Back y del Front se detenga si trae un código real, una tabla maestra, el correo real de la coordinación, una tarjeta o una captura, para que los repositorios públicos sigan sin datos reales durante y después de la capacitación.

**Why this priority**: la capacitación trae por primera vez códigos reales y el correo real de una coordinación a la máquina del equipo mientras se escriben specs, pruebas y capturas, y `scripts/preflight.sh` revisa hoy los códigos 99 solo en `tests/datos_inventados/`.

**Independent Test**: con la huella de un correo inventado en `HUELLAS_CORREOS_PROHIBIDOS`, un cambio que agrega ese correo falla sin repetirlo, una captura de Playwright falla, y el contenido actual de los dos repositorios pasa sin falsos positivos.

**Base**: `scripts/preflight.sh` del Back y del Front y su hook `pre-commit`, `.gitignore`, la consulta Q04 y BR-CARGA-08.
**Pantalla**: ninguna.

**Acceptance Scenarios** (`guia_y_privacidad.feature`): el correo por su huella, el aviso sin huellas, el código de ocho cifras fuera del rango (esquema con huellas, fechas, cifras de siete dígitos, los códigos de prueba de la spec 001 y los colores ya versionados que pasan), la captura, la tabla maestra por otro nombre con los archivos legítimos que pasan, la tarjeta dentro del repositorio, ningún falso positivo en el contenido actual y el historial sin el correo prohibido.

---

### US-89: Cierre de la capacitación sin perder evidencia (Priority: P2)

Como Oficina de Calidad, quiero un cierre que dé de baja las cuentas de ejemplo, compruebe el respaldo de los archivos de la capacitación por su huella e informe qué se puede borrar sin borrarlo, para que los datos reales no queden sueltos ni se pierdan.

**Base**: `acceso.usuario_autorizado.activo` (BR-ACCESO-06), `acceso.sesion`, el manifiesto de US-74, el respaldo de la skill respaldar-en-windows y `db/herramientas/cerrar_capacitacion.py` (propuesta), en seco por omisión y con `--aplicar` desde el Windows.
**Pantalla**: P1 con la cuenta dada de baja.

**Acceptance Scenarios** (`capacitacion_en_develop.feature`): la baja en seco y después aplicada con la pérdida de la sesión, el respaldo comprobado sin borrar nada, el respaldo incompleto, el cierre que no toca develop ni main sin D-55 y la conciliación que sigue disponible después del cierre.

---

### US-90: Matriz de cumplimiento de las specs 007 y 008 (Priority: P2)

Como Oficina de Calidad, quiero una matriz generada que ligue cada historia y cada regla de las specs 007 y 008 con su escenario, su prueba y su última corrida, para saber antes de la capacitación qué se cumple y que nada del flujo queda sin prueba.

**Base**: `specs/*/spec.md`, `specs/features/*/*.spec.md`, los `.feature`, `pytest --junitxml`, el reporte JSON de Vitest y `scripts/matriz_cumplimiento.py` (propuesta), con la traza en `specs/008-ciclo-quimica-industrial/cumplimiento.md`.
**Pantalla**: ninguna.

**Acceptance Scenarios** (`matriz_cumplimiento.feature`): la historia con escenario, prueba y corrida, la historia sin escenario que hace fallar la generación, la regla con prueba nombrada que no es hueco, el escenario delegado buscado en Vitest por su título, lo pendiente por decisión, la etiqueta sin historia, el tramo de la capacitación en una sola tabla, el archivo versionado que no cambia con cada corrida y la matriz sin datos reales.

### Edge Cases

- Un profesor con secciones en 2026-1 y en 2026-2 ve el selector y abre en el vigente, y un profesor con secciones solo en 2026-1 ve «Periodo 2026-1» sin selector y abre en ese periodo.
- La ruta 18 de una coordinación con alcance de carrera lista los periodos en que su carrera tiene catálogo vigente con secciones, y la de una coordinación de curso, los periodos de sus filas de alcance con secciones de esa asignatura.
- Una cuenta con filas de alcance de carrera y de asignatura recibe en la sesión el tipo CARRERA, que es el más amplio, y ve la unión de las dos.
- Una tabla maestra con un estudiante en dos secciones del curso detiene el generador, porque Q08 marcaría la misma situación en la base.
- Un archivo de ejercicio subido por dos profesores tendría la misma huella, así que el generador arma uno distinto por profesor con `--ejercicio`.
- El R-17 de la capacitación sale con la franja PROVISIONAL y el sufijo _PROVISIONAL mientras R-2026-BORRADOR esté en BORRADOR (D-54), y el conciliador compara las cifras sin mirar la franja.
- El R-17 del sistema no trae las hojas III y IV de oportunidades de mejora y buenas prácticas que traen los R-17 a mano, hasta que se construya la spec 005 (J-57).
- El estadio «Inicial» de 5643 es un supuesto tomado de Ambiental, y con un solo NIVEL_ESPERADO (D-38) no cambia ninguna cifra.
- Un PI sin descriptores de rúbrica no cambia el R-17, porque `abet_carga/r17.py` no lee `abet.rubrica_nivel`, y P3 y P4 no muestran rúbricas.
- La sección 704 sin profesor queda en SIN_PROFESOR para la ruta 17 y en `secciones_sin_docente.sql`, y nadie puede subir en ella.
- Un profesor que sube el export de otra sección del curso recibe SECCION_NO_COINCIDE si el archivo no está publicado, y 409 con «Este archivo ya está publicado en otra sección. No se cargó.» si ya lo publicó su dueño.
- La consulta de una sección sin carga publicada no es un control de 0 filas, porque durante el registro siempre tiene filas, y su lugar es la ruta 17.
- Un restablecimiento de develop durante la ventana de registro borraría las cargas reales, así que develop queda congelada hasta el 12-12-2026 (J-56) y el humo se niega a correr sobre la siembra de la capacitación.
- P3 conserva «Antes de subir» con «En Blackboard, una columna por PI…», porque el export generado sigue el formato de Blackboard y la spec 007 fija esas líneas.

## Requirements *(mandatory)*

- **FR-001** La spec cubre el ciclo de punta a punta de Química General y construye además la etapa B de la spec 007 (US-64 y US-65) con el alcance nuevo (J-57). US-66 espera a D-47 y a D-51, y la spec 005 queda fuera, así que el R-17 sale sin las hojas III y IV.
- **FR-002** Los escenarios del Back usan un solo juego de datos inventados de Química, `db/datos/quimica_2026_1_inventado.sql` (propuesta), que `db/pruebas/correr_pruebas.sh` aplica dos veces para probar que se repite sin filas nuevas, junto a `periodo_2026_2_inventado.sql`.
- **FR-003** V1_12 nace de `db/herramientas/generar_v1_12.py` sobre `db/referencia/industrial_2026.json`, determinista como `generar_v1_03.py`, con un bloque DO que comprueba los conteos de IND-2026 y detiene la migración si no coinciden. La referencia la arma un extractor que corre fuera del repositorio y lee solo la hoja «Información por Asignatura», nunca las hojas con estudiantes. IND-2026 queda en BORRADOR, sin filas en `abet.rubrica_nivel` hasta D-50, y la sección 1 de `db/pruebas/pruebas.sql` cuenta por catálogo.
- **FR-004** Las migraciones de esta spec son V1_12 (catálogo), V1_13 (reglas) y V1_14 (`acceso.coordinacion_alcance`), en el orden de construcción. La V1_12 de la spec 005 pasa a V1_15 con un cambio fechado en su `tasks.md`, su FR-017 y la expresión de `tests/aceptacion/pasos/conftest.py` que hoy admite solo 09, 10 u 11 (veredicto CAMBIAR del crítico). Aprobar esta spec aprueba ese cambio.
- **FR-005** V1_13 siembra R-2026-BORRADOR para IND con los mismos parámetros de Ambiental, META_LOGRO 0,80 y NIVEL_ESPERADO 3 definidos y CORTE_ROJO, CONVERSION_NIVEL_0_1 y TRATO_SIN_EVIDENCIA en PENDIENTE.
- **FR-006** `db/datos/plan_quimica_2026_1.sql` registra la vigencia de IND-2026 en 2026-1 y el plan de 5643 con el PI de `-v pi` (6.1 por omisión, D-48), «Portafolio 3» y la descripción de `\getenv DESCRIPCION_INSTRUMENTO`, en seco salvo `-v aplicar=1`, con ON CONFLICT DO NOTHING, una fila existente distinta que detiene todo y la descripción que nunca queda escrita en el repositorio.
- **FR-007** `app/configuracion.py` exige al arrancar el conjunto de CONJUNTO_REGLAS para cada carrera con plan de medición en un periodo con secciones, con un mensaje que nombra la carrera y no dice «Ambiental» (BR-PERIODO-06, propuesta). La ruta 5 no traduce ConfiguracionInvalida a un mensaje propio, porque es un defecto del despliegue, y responde el 500 de ERROR_INTERNO.
- **FR-008** `acceso.coordinacion_alcance` da a una cuenta COORDINADOR el alcance de una carrera (las secciones de las asignaturas del plan de estudios del catálogo vigente de esa carrera en el periodo) o de una asignatura en un periodo (sus secciones en ese periodo). `_ALCANCE` une las filas de la cuenta, `puede_leer()` y `puede_reemplazar()` siguen ese alcance (D-11 y D-52), `puede_subir()` sigue solo con `acceso.docente_seccion` del PROFESOR y una cuenta COORDINADOR sin filas no ve nada (BR-ACCESO-13, propuesta). `ck_usuario_autorizado_rol` no cambia.
- **FR-009** `GET /api/sesion` suma el campo aditivo `alcance` con `tipo` (SECCIONES, CARRERA o CURSO), `carreras` y `asignaturas` (propuesta), sin datos de personas, y el Front elige sus rótulos por `alcance.tipo` sin cambiar el tipo Rol.
- **FR-010** `db/herramientas/registrar_coordinacion.py` (propuesta) lee el correo solo de `CORREO_COORDINACION`, lo normaliza, no lo repite en el informe, corre en seco por omisión, escribe con `--aplicar` en una transacción, nunca hace UPDATE de rol ni de `activo`, termina con 1 ante otro rol, una baja, una asignatura o un periodo inválidos y con 2 sin la variable, y no toca `acceso.credencial` (BR-ACCESO-14, propuesta).
- **FR-011** La ruta 18 `GET /api/periodos` exige la sesión, responde `vigente` y `periodos` con los periodos de las secciones al alcance del usuario del más reciente al más antiguo, lleva `Cache-Control: no-store` y entra en `tests/rutas_registradas.py` (BR-PERIODO-05, propuesta). La ruta 8 sin `seccion_id` acepta `periodo` con la validación de la ruta 4, y sin él sigue con `PERIODO_VIGENTE` (cambio fechado en BR-CARGA-20). El Front guarda el periodo en el estado de `App.tsx`, lo pasa a las rutas 4, 8, 12 y 17, muestra el selector solo con dos periodos o más y, si la ruta 18 falla, sigue como hoy.
- **FR-012** La tabla de J-43 suma un consejo por motivo RECHAZA_FILA y otro para el aviso PUNTAJE_MAXIMO_DISTINTO, `queCorregir()` acepta también una carga PUBLICADA con rechazos de fila o con ese aviso y `CORREGIR_SIN_FILAS_ACEPTADAS` pasa a «Corrija el archivo en cada fila de la tabla de rechazos y suba el archivo nuevo. Si recibió el export de la Oficina de Calidad, pídale uno corregido.» (propuesta), con un cambio fechado en `que_corregir.feature` de la spec 007. P4 no gana un botón de reemplazo (J-53).
- **FR-013** `scripts/generar_exports_desde_maestra.py` (propuesta) lee la tabla maestra y el CSV de la programación, filtra por `--periodo`, `--asignatura` y `--pi`, cuenta lo omitido, toma el curso de Blackboard solo de la programación, escribe un .xlsx por sección con «Username» y la columna del PI y nada más, con el código como texto, en una carpeta fuera de todo repositorio, con un manifiesto sin códigos, y se detiene ante una fila defectuosa sin mostrar su valor. El curso_blackboard de las secciones de la capacitación es CAPACITACION_20261_5643_NNN (propuesta), que cumple _CURSO y Q21.
- **FR-014** La ruta 17 y P7 se construyen como fija la spec 007 (FR-008 a FR-013 de esa spec), con el alcance de `secciones_visibles()` y el título «Avance del registro del curso» para el alcance CURSO. Si no llegan antes de la capacitación, la coordinación del curso sigue el avance en P2.
- **FR-015** El R-17 escribe en B6 «Carrera de» más `abet.carrera.nombre` de la carrera de la carga, sin otra plantilla ni migración (BR-R17-13, propuesta), y ninguna otra celda nombra una carrera.
- **FR-016** El campo `agregados` de la ruta 12 suma estudiantes por PI y curso desde `abet.v_r17_por_pi`, solo para el COORDINADOR y solo si D-32 se responde antes de construirlo (J-54).
- **FR-017** El rediseño define colores, tipografía y espaciado como tokens literales en el bloque `@theme` de `src/index.css`, usa fuentes del sistema (J-59), no suma dependencias ni recursos de otro dominio, respeta `prefers-reduced-motion` y conserva los rótulos que citan los `.feature` de las specs 001 a 007. Una función propia del Front calcula la razón de contraste de cada par.
- **FR-018** `db/herramientas/conciliar_tabla_maestra.py` (propuesta) lee la base con `abet_respaldo` en READ ONLY, la tabla maestra y, opcionalmente, una carpeta de R-17, compara por sección, estudiante y nivel, conteo y porcentaje (como cociente y con un decimal), no compara PROFESOR, ARCHIVO ni ESTADO DE EVIDENCIA, termina con 0 si todo es igual, 1 ante una diferencia y 2 ante un archivo dentro de un repositorio, y nunca escribe un número de ocho cifras. Termina con 3 si la base no responde y, sin `--datos-reales`, rechaza los códigos que no son del rango 99 (cambio del 2026-11-23, T037).
- **FR-019** Las pruebas de Vitest que cambian son las que esperan `CORREGIR_SIN_FILAS_ACEPTADAS` con «Corrija en Blackboard», las que esperan que `listarSecciones()`, `listarCargas()` y `obtenerResultados()` se llamen sin periodo y las de la llegada que esperan una cabecera sin periodo. Cada cambio se fecha en la spec 007.
- **FR-020** La siembra corre cada paso primero en seco y desde el Windows, en el orden de respaldo, V1_12, V1_13, V1_14 con `alcance_coordinacion_ambiental.sql`, despliegue del Back con el alcance nuevo, plan de Química, programación, coordinación y contraseñas, con la huella de Ambiental antes y después. `db/herramientas/sembrar_quimica.py` (propuesta) corre en orden esos pasos, en seco por omisión, se detiene en el primer paso con código distinto de 0, exige `--confirmo-principal` con `--rama principal` y hace la comprobación previa de la guardia. En seco anuncia sin correr los pasos que necesitan V1_12 a V1_14 mientras sigan pendientes, y el segundo tramo, después del despliegue, recibe la huella de Ambiental de antes con `--huella-antes`. El `migrate` de V1_14 da al rol de la API el SELECT de `acceso.coordinacion_alcance` con el callback afterMigrate, antes del despliegue (cambio del 2026-11-23). Tras restablecer develop, la siembra vuelve a empezar en V1_12 antes de que la vista previa se use. La ventana sigue J-56.
- **FR-021** Las consultas de control nuevas son Q18 (curso con plan de dos carreras en el mismo periodo), Q19 (carrera con plan sin conjunto de reglas), Q20 (cuenta COORDINADOR activa sin alcance o con filas en `acceso.docente_seccion`) y Q21 (sección cuyo curso de Blackboard no declara su periodo, su asignatura y su número), cada una con su caso que falla en `db/pruebas/pruebas.sql` y copia literal en `controles_neon.sql`, cuya línea final pasa a «RESULTADO: Q01 a Q14 y Q18 a Q21 devuelven 0 filas.» (propuesta). Ninguna devuelve correos ni códigos. Q16 y Q17 siguen reservadas para la spec 005.
- **FR-022** Ningún dato real entra a git. La tabla maestra, los 18 R-17 de los profesores, los exports generados con datos reales, los informes de la conciliación real, las tarjetas, el CSV de la programación real y el correo real de la coordinación viven fuera de los repositorios. `scripts/preflight.sh` del Back y del Front detecta los correos de `HUELLAS_CORREOS_PROHIBIDOS` por su huella, los códigos de ocho cifras con límite de palabra fuera del rango 99 y fuera de una huella de 64 caracteres, salvo los valores de la lista cerrada CODIGOS_DE_PRUEBA (10000004 y 98999999, de las pruebas de la guardia de la spec 001), y revisa solo las líneas que agrega un cambio (`--staged` o `--pr`) para no tomar colores ni decimales del contenido anterior, en `specs/`, `tests/`, `e2e/` y `docs/`, los archivos tabulares cuya primera línea trae «CÓDIGO DEL ESTUDIANTE» y «CALIFICACIÓN», las capturas y resultados de Playwright y las tarjetas de profesor. El historial se barre una vez antes de publicar esta spec.
- **FR-023** El humo con Playwright vive en `e2e/humo_quimica.spec.ts` (propuesta), corre contra la vista previa de develop con la siembra inventada, lee las contraseñas de un archivo temporal con permisos 600 que se borra al terminar, deja las capturas fuera de los repositorios y se niega a correr si la 701 ya tiene una carga o si develop tiene la siembra de la capacitación.
- **FR-024** La guía vive en `docs/capacitacion/guia_quimica.md` del Front (propuesta), por rol y en el orden de las pantallas, con solo correos de ejemplo, «Fecha por confirmar» mientras J-56 no se cierre y el ejercicio de error con un archivo inventado. Una prueba de Vitest coteja cada rótulo entre comillas latinas con `src/`. La opción `--tarjetas` de `scripts/generar_exports_desde_maestra.py` (propuesta) compara cada tarjeta con el manifiesto y falla ante el archivo de otra sección.
- **FR-025** `db/herramientas/cerrar_capacitacion.py` (propuesta) da de baja las cuentas de la capacitación que lista el CSV de la programación y la cuenta de la coordinación, en seco por omisión, comprueba el respaldo por huella contra el manifiesto e informa qué se puede borrar, sin borrar nada, sin restablecer develop y sin escribir en main.
- **FR-026** `scripts/matriz_cumplimiento.py` (propuesta) genera la traza de las specs 007 y 008 en `cumplimiento.md` y falla ante una historia de la spec 008 sin escenario, una etiqueta sin historia o un escenario delegado cuyo título no existe en Vitest. La corrida de la integración continua lleva el resultado y la fecha.
- **FR-027** Los escenarios del Back corren con pytest-bdd 9 en el clúster desechable de `tests/cluster_desechable.py`, nunca en localhost:5432, con los pasos compartidos de `conftest.py` ampliados para la base de la spec 008, el rol en mayúsculas con guion bajo, las tablas de `acceso` en LISTA y los rangos de consultas. Los escenarios `@delegado_a_vitest` registran el nombre de su prueba de Vitest y los `@playwright` el de su prueba de `e2e/`. Cada historia se construye con su prueba primero.
- **FR-028** Una carga de 5643 se publica en la carrera de su plan (`abet.carga.carrera_id` de IND) con todas sus filas válidas, y los rechazos de la sala siguen BR-CARGA-08 a BR-CARGA-10 sin mostrar una nota ni un código (US-75 y US-76).
- **FR-029** Ninguna pantalla se desplaza de lado a 375 px, cada control mide al menos 24 por 24 px, el foco se ve y sigue el orden de lectura, y el menú principal se usa solo con el teclado (US-82).
- **FR-030** El ensayo corre en una base aparte (J-52) con `db/herramientas/ensayar_capacitacion.py` (propuesta) y termina con 0 solo si el conciliador dice que todas las secciones son iguales (US-84).

## Success Criteria *(mandatory)*

- **SC-001** Los 202 escenarios y 257 casos de los doce `.feature` tienen su prueba, en pytest-bdd, en Vitest o en Playwright, y pasan, salvo los de US-80 si J-54 lo deja fuera, que quedan como «Pendiente por decisión» en la matriz.
- **SC-002** En el ensayo con los datos reales, 18 de 18 R-17 del sistema son iguales a los del profesor, porque el conciliador dice «18 de 18 secciones iguales.» frente a la tabla maestra, que Stefanny verificó igual alumno por alumno a los 18 R-17 a mano, en códigos, niveles, conteo por nivel y porcentaje, y la revisión visual de una sección en la sala no encuentra diferencias en esas cifras.
- **SC-003** Después de la capacitación, el conciliador sobre develop da otra vez 18 de 18 secciones iguales, el total de alumnos y el conteo por nivel de 5643 en 2026-1 son los que la Oficina de Calidad entrega (guardados fuera del repositorio) y ningún alumno queda sin nota.
- **SC-004** En la capacitación, cada uno de los 18 profesores publica su carga con el export generado en un intento, con 0 filas rechazadas.
- **SC-005** La huella de Ambiental, tomada después del último restablecimiento de develop, es la misma antes y después de la siembra, y el R-17 de la 410 sale con las mismas celdas.
- **SC-006** La coordinación de Ambiental recibe 0 secciones de 5643 en 2026-1, la coordinación del curso recibe las 18 secciones de 5643 y 0 de otra asignatura, como confirma en develop la lectura sin correos de US-86, y ninguna cuenta recibe un dato fuera de su alcance en los escenarios de 403.
- **SC-007** Q01 a Q14 y Q18 a Q21 devuelven 0 filas después de la siembra, del ensayo y de la capacitación.
- **SC-008** El humo con Playwright pasa en la vista previa con el profesor y con la coordinación del curso antes de la siembra de la capacitación.
- **SC-009** Cada par de color de texto supera 4,5 a 1 y cada componente 3 a 1, ninguna pantalla se desplaza de lado a 375 px y las pruebas de Vitest de la spec 007 pasan sin cambios salvo las de FR-019.
- **SC-010** `bash scripts/preflight.sh` del Back y del Front pasa sin falsos positivos con las reglas nuevas, el barrido del historial no encuentra el correo prohibido y ninguna salida del generador, del conciliador, de la siembra ni del cierre trae un número de ocho cifras.
- **SC-011** La matriz de cumplimiento de las specs 007 y 008 no tiene huecos.

## Decisiones abiertas

De la Oficina de Calidad y de la carrera (D). Mientras no se decidan, el sistema aplica el valor provisional.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| D-48 | Si 5643 mide el PI 6.1 o el 6.2 de Industrial, porque un programa dice 6.2 y los R-17 dicen 6.1 | 6.1, el de los R-17, como parámetro del guion del plan y del generador | Stefanny Montaño |
| D-49 | Estadio de 5643 en la malla de Industrial | «Inicial», tomado de Ambiental hasta la «Base cursos - Nivel» de Industrial, con un solo NIVEL_ESPERADO de 3 (D-38) | Stefanny Montaño |
| D-50 | Rúbricas por nivel de los PI de Industrial | IND-2026 en BORRADOR sin filas en `abet.rubrica_nivel` hasta la «Plantilla Base - Final» de Industrial | Stefanny Montaño |
| D-51 | Si la coordinación del curso ve en P7 el correo del profesor de cada sección que falta | No mientras no se responda. La ruta 17 de Industrial sale sin el campo profesores y la guía no lo promete (US-87). Si la respuesta es sí, se construye como D-47 | Oficina de Calidad y coordinación de Industrial |
| D-52 | Si la coordinación del curso reemplaza la carga publicada de una sección de su curso | Sí, el valor provisional de D-11 para la coordinación, limitado a su curso y su periodo | Stefanny Montaño |
| D-53 | Quién entrega a la Oficina de Calidad los R-17 de Química General | Cada profesor descarga el suyo, y la coordinación del curso puede abrir cada carga | Oficina de Calidad |
| D-54 | Si el R-17 de la capacitación puede salir OFICIAL | No. Sale PROVISIONAL mientras R-2026-BORRADOR de Industrial esté en BORRADOR | Oficina de Calidad |
| D-55 | Destino de las cargas de Química General de 2026-1 después de la capacitación | Quedan en develop, sin pasar a main, y el cierre no toca ninguna de las dos ramas | Oficina de Calidad con Jefferson |

De Jefferson (J), con el valor que propone la spec.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| J-49 | Si la fila de alcance por asignatura lleva periodo | Sí, obligatorio en la fila de asignatura y nulo en la de carrera, con `ck_coordinacion_alcance_periodo` | Jefferson |
| J-50 | Regla del curso compartido 5643 para la coordinación de carrera cuando las dos carreras están vigentes en el mismo periodo | La de hoy, por el plan de estudios del catálogo vigente de la carrera de la fila de alcance. Jefferson la cierra con Stefanny antes de que Química se mida en un periodo con AMB-2026 vigente | Jefferson |
| J-51 | Si el profesor que coordina el curso usa una sola cuenta | Cuentas separadas para la capacitación. Jefferson confirma con Stefanny si la coordinación real dicta una sección | Jefferson |
| J-52 | Base del ensayo con los datos reales | Una rama hija de develop en Neon, creada y borrada desde el Windows, porque D-10 autoriza Neon y no un clúster local | Jefferson |
| J-53 | Botón de reemplazo en P4 antes de la spec 005 | No. P4 remite a «Reemplazar carga» de P5 y la guía lo enseña | Jefferson |
| J-54 | Si el agregado del curso (US-80) entra antes de la capacitación | No. Entra en esta spec solo si D-32 se responde antes de construirlo | Jefferson |
| J-55 | Archivo con los R-17 del curso | Después de la capacitación, como ruta 19, si D-53 pide la entrega por la coordinación | Jefferson |
| J-56 | Entorno, fecha y ventana de la capacitación | La versión de prueba (develop) con fecha por confirmar. El humo corre una sola vez con la siembra inventada, después se restablece develop, se siembra Química con los datos de la capacitación y develop queda congelada hasta el 12-12-2026. Tras restablecer develop, la siembra vuelve a empezar en V1_12 antes de que la vista previa se use | Jefferson |
| J-57 | Qué alcanza el pedido de que todas las historias y requerimientos se cumplan | La spec 008 y la etapa B de la spec 007 (US-64 y US-65). US-66 espera a D-47 y D-51, y la spec 005 queda para después, con el R-17 sin las hojas III y IV | Jefferson |
| J-58 | Cómo recibe su contraseña la cuenta real de la coordinación, que `asignar_claves.py` rechaza por no ser de example.invalid | Un modo de `herramientas_neon/asignar_claves.py` que lee el correo de una variable por `en_windows.py`, lo oculta en la salida y pide la contraseña con getpass | Jefferson |
| J-59 | Tipografía del rediseño | Fuentes del sistema, sin servicios de fuentes de terceros, para no exponer a cada profesor a otro dominio | Jefferson |

## Fuera de alcance

- El archivo con los R-17 publicados del curso (C-24), porque dos lentes lo marcan REFUTADA o MOVER_A_DESPUES. Vuelve como ruta 19 si D-53 pide la entrega por la coordinación (J-55).
- El reemplazo por la coordinación del curso como historia propia con dos valores de una decisión (C-25). Su único escenario con el valor provisional de D-52 queda en US-71.
- El profesor que coordina el curso con una sola cuenta (C-27), que espera la respuesta de J-51.
- El paso de las cargas de Química General a la página oficial (parte b de C-67), que espera a D-55.
- La spec 005 completa, con el semáforo, la declaración de oportunidades de mejora y buenas prácticas por PI y las hojas III y IV del R-17 (J-57).
- El campo de correos de los profesores en P7 (US-66 de la spec 007), que espera a D-47 y a D-51.
- El botón de reemplazo en P4 (C-P04 de la spec 007), que espera a la spec 005 y a US-52 (J-53).
- La revisión con axe-core, que pide una dependencia nueva con la espera de 14 días de Dependabot.
- Las rúbricas por nivel de los PI de Industrial y el estadio de cada curso, que esperan a D-49 y D-50.
- La hoja del portafolio sobre 20 de cada profesor como entrada del sistema, porque la decisión A de Jefferson genera los exports desde la tabla maestra.
- El envío de correos desde la aplicación, el borrado automático de archivos reales en la Mac y cualquier escritura en la rama principal de Neon.
- El uso de la API de OpenAI, porque no hay clave, y de Codex para cualquier pieza con datos reales.
