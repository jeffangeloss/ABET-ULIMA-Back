# Feature Specification: Evolución del curso y competencias por estadío

**Feature Branch**: `docs/011-historico-y-competencias` del Back (PR a `develop`), con el contrato en el Front y la implementación en `feat/011-historico-y-competencias` después de la aprobación
**Created**: 2026-11-25
**Status**: Borrador, espera la aprobación de Jefferson
**Input**: «Si falta data, genera data, todo para que se pueda ver que el sistema funciona de punta a punta :)», en respuesta al resumen de las páginas «Histórico por Profesor» y «Resumen Competencias - Nivel» del tablero de Stefanny Montaño que el sistema todavía no replica, donde la primera necesita al menos dos periodos y choca con D-57, y la segunda necesita la «Base cursos - Nivel» de Industrial (D-60) o mediciones de Ambiental

## Épica

> **EP-11. Evolución del curso y competencias por estadío (propuesta).** El tablero `Resumen de indicadores ABET - Cursos de Carrera.pbix` de Stefanny Montaño trae dos páginas que el sistema no replica. «Histórico por Profesor» muestra por periodo el promedio de la calificación y los alumnos que aprueban y que no, y «Resumen Competencias - Nivel» muestra lo mismo por competencia y por nivel de la asignatura, con las secciones en la meta y una tabla por sección. Hoy la base tiene un solo periodo con cargas, Química General (5643) de Industrial en 2026-1, y Ambiental tiene en la base el mapeo de competencias y estadíos (V1_03, 95 pares) sin mediciones. Esta épica lleva al sistema la evolución del curso y de sus secciones a lo largo de los periodos, sin profesores, y el logro de cada competencia en los estadíos INICIAL, REFUERZO y LOGRADO, y genera los datos inventados que faltan para verlas de punta a punta, desde el export hasta la pantalla, con el flujo normal de carga.

Convenciones de esta spec. Todos los datos de los escenarios son inventados y se recalculan a mano. Los estudiantes de la demostración usan el rango propio 99500000 a 99599999, fuera de los 99000001 a 99000055 de las pruebas. Los correos son del dominio reservado `example.invalid`, los profesores se llaman «Profesor Inventado» seguido de palabras con letras (AD-61 de la spec 010) y las secciones nuevas llevan el curso SINTETICO_AAAAC_ASIGNATURA_NUMERO. La siembra de Química de la spec 008 (`db/datos/quimica_2026_1_inventado.sql`) sigue igual, con la 701 a la 704 de 5643 en 2026-1, `docente701@example.invalid` a `docente703@example.invalid`, la 704 sin profesor y `coordinador.quimica@example.invalid`, y la coordinación de Ambiental es `coordinacion@example.invalid`, con la fila de la carrera AMB. Ningún escenario toma un valor de las filas del tablero, y el tablero y las tablas maestras reales viven fuera de todo repositorio.

Prefijos e identificadores. La épica continúa la numeración (EP-11). Las historias siguen desde US-100, porque la spec 010 termina en US-99. Las decisiones de la carrera son D-59 y D-60, que en la spec 010 aparecen solo como rótulos de candidatas que salieron, y las de Jefferson desde J-72. Las decisiones del crítico siguen desde AD-83. Las rutas nuevas son la 22, la 23 y la 24 (propuestas), porque la 19 está reservada (J-55), y viven en la §17 del contrato del Front. Las pantallas nuevas son P9 y P10, el registro de la decisión es ADR-011 del Front y las reglas nuevas de la spec viva `resultados` son BR-RESULTADOS-16 a BR-RESULTADOS-19 (propuestas). Esta spec no necesita migraciones.

Siglas y términos. Las de las specs 001 a 010 valen aquí. El indicador de desempeño (performance indicator, PI) y el resultado del estudiante (student outcome, SO) conservan su sentido. «Nivel esperado o superior» nombra lo que el tablero llama «Aprobados» o «3-4». Una «medición» es el nivel de un estudiante en un PI de una carga PUBLICADA (`uq_medicion` sobre carga, PI y estudiante), y es la unidad de P10. El «estadío» es el nivel de la asignatura en la malla para una competencia (INICIAL, REFUERZO o LOGRADO de `abet.asignatura_competencia`), que el tablero llama «Nivel Asignatura».

Los escenarios viven en `specs/011-historico-y-competencias/aceptacion/`, en español (`# language: es`), en cinco archivos. `evolucion_del_curso.feature` contiene US-100, `pantalla_evolucion_del_curso.feature` US-101, `competencias_por_estadio.feature` US-102 y US-104, `pantalla_competencias.feature` US-103 y US-104, y `datos_de_demostracion.feature` US-105 a US-108. La revisión por refutación está en `revision-historias.md`.

## Datos inventados de la demostración

Química General (5643) de Industrial, PI 6.1, con la meta de 80 % y el nivel esperado 3 de R-2026-BORRADOR de Industrial. Los niveles van como [n1, n2, n3, n4], que son los alumnos calificados en los niveles 1 a 4.

| Periodo | Sección | Niveles | Sin evidencia | Calificados | Con 3 o 4 | % | Promedio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-1 | 701 | [0, 1, 2, 2] | 0 | 5 | 4 | 80,0 | 3,20 |
| 2025-1 | 702 | [1, 2, 2, 0] | 0 | 5 | 2 | 40,0 | 2,20 |
| 2025-2 | 701 | [0, 1, 2, 1] | 0 | 4 | 3 | 75,0 | 3,00 |
| 2025-2 | 702 | [0, 1, 3, 1] | 0 | 5 | 4 | 80,0 | 3,00 |
| 2025-2 | 703 | [1, 1, 1, 0] | 1 | 3 | 1 | 33,3 | 2,00 |
| 2026-1 | 701 | [0, 0, 3, 2] | 0 | 5 | 5 | 100,0 | 3,40 |
| 2026-1 | 702 | [0, 1, 2, 2] | 0 | 5 | 4 | 80,0 | 3,20 |
| 2026-1 | 703 | [1, 1, 2, 1] | 0 | 5 | 3 | 60,0 | 2,60 |
| 2026-1 | 704 | sin carga | — | — | — | — | — |

El curso queda así en cada periodo.

- **2025-1.** Niveles [1, 3, 4, 2], 6 de 10 (60,0 %), promedio 27 / 10 = 2,70 y 1 de 2 secciones publicadas en la meta.
- **2025-2.** Niveles [1, 3, 6, 2], 8 de 12 (66,7 %), promedio 33 / 12 = 2,75, 1 alumno sin evidencia y 1 de 3 secciones en la meta. El promedio simple de los tres porcentajes daría 62,8, y esa cifra no debe salir.
- **2026-1.** Niveles [1, 2, 7, 5], 12 de 15 (80,0 %, en la meta), promedio 46 / 15 = 3,07 y 2 de 3 secciones publicadas en la meta, con la 704 sin carga.

Ambiental (AMB-2026), con la meta de 80 % y el nivel esperado 3 de R-2026-BORRADOR de Ambiental. En AMB-2026 cada SO tiene una sola competencia, así que G4 sale del SO 5, G3 del SO 3, G8 del SO 4 y E2 del SO 2. La base de los escenarios es la de `scripts/api_local.sh` con lo que suma T025, y no carga `db/pruebas/datos_sinteticos.sql`, así que en 2024-2 y 2026-2 trae estas secciones de Ambiental y ninguna otra.

| Periodo | Asignatura | Sección | Origen | Carga | PI del plan | Celdas a las que aporta |
| --- | --- | --- | --- | --- | --- | --- |
| 2024-2 | 450002 | 413 | Semilla de US-106 | PUBLICADA | 5.1, 5.2 y 5.3 | G4 en REFUERZO |
| 2026-2 | 450002 | 410 y 411 | `periodo_2026_2_inventado.sql` | Sin carga | 5.1, 5.2 y 5.3 | G4 en REFUERZO, sin dato |
| 2026-2 | 450002 | 412 | `varias_secciones_2026_2_inventado.sql` | Sin carga | 5.1, 5.2 y 5.3 | G4 en REFUERZO, sin dato |
| 2026-2 | 450002 | 413 | Semilla de US-106 | PUBLICADA | 5.1, 5.2 y 5.3 | G4 en REFUERZO |
| 2026-2 | 450010 | 410 y 412 | `varias_secciones_2026_2_inventado.sql` | Sin carga | 2.1, 2.2 y 5.1 | G4 y E2 en REFUERZO, sin dato |
| 2026-2 | 6511 | 401 | Semilla de US-106 | PUBLICADA | 3.1 y 5.1 | G3 y G4 en INICIAL |
| 2026-2 | 5674 | 401 | Semilla de US-106 | PUBLICADA | 5.1 y 5.2 | G4 en LOGRADO |

En `asignatura_competencia`, 450002 tiene también G8 en REFUERZO y 5674 tiene G3 en LOGRADO, pero sus planes no miden el SO 4 ni el SO 3, así que no aportan secciones a esas celdas (FR-005). Las asignaturas con G3 en REFUERZO (450006, 450009 y 560046) no tienen secciones ni plan en la demostración. Cada carga publicada tiene 5 estudiantes, ninguno sin evidencia, con estos niveles por PI.

| Periodo | Sección | PI | Niveles | Con 3 o 4 | Suma de niveles |
| --- | --- | --- | --- | --- | --- |
| 2024-2 | 450002-413 | 5.1 | [0, 2, 2, 1] | 3 | 2·2 + 3·2 + 4·1 = 14 |
| 2024-2 | 450002-413 | 5.2 | [1, 1, 2, 1] | 3 | 1 + 2 + 6 + 4 = 13 |
| 2024-2 | 450002-413 | 5.3 | [0, 2, 2, 1] | 3 | 14 |
| 2026-2 | 450002-413 | 5.1 | [1, 0, 2, 2] | 4 | 1 + 6 + 8 = 15 |
| 2026-2 | 450002-413 | 5.2 | [0, 1, 2, 2] | 4 | 2 + 6 + 8 = 16 |
| 2026-2 | 450002-413 | 5.3 | [0, 1, 3, 1] | 4 | 2 + 9 + 4 = 15 |
| 2026-2 | 6511-401 | 3.1 | [1, 2, 1, 1] | 2 | 1 + 4 + 3 + 4 = 12 |
| 2026-2 | 6511-401 | 5.1 | [0, 2, 2, 1] | 3 | 4 + 6 + 4 = 14 |
| 2026-2 | 5674-401 | 5.1 | [0, 0, 3, 2] | 5 | 9 + 8 = 17 |
| 2026-2 | 5674-401 | 5.2 | [0, 1, 2, 2] | 4 | 2 + 6 + 8 = 16 |

Las celdas con secciones quedan así, con `conteo_secciones` en el orden total, publicadas, en la meta, debajo de la meta y sin dato.

| Periodo | Celda | Secciones de la celda | Mediciones por nivel | Con 3 o 4 | % | Promedio | En la meta | Conteo de secciones |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2024-2 | G4 en REFUERZO | 450002-413 | [1, 5, 6, 3] | 3 + 3 + 3 = 9 de 15 | 60,0 | (14 + 13 + 14) / 15 = 41 / 15 = 2,73 | No | 1, 1, 0, 1, 0 |
| 2026-2 | G4 en INICIAL | 6511-401, PI 5.1 | [0, 2, 2, 1] | 3 de 5 | 60,0 | 14 / 5 = 2,80 | No | 1, 1, 0, 1, 0 |
| 2026-2 | G4 en REFUERZO | 450002-410, 411, 412 y 413 y 450010-410 y 412 | [1, 2, 7, 5], todas de la 413 | 4 + 4 + 4 = 12 de 15 | 80,0 | (15 + 16 + 15) / 15 = 46 / 15 = 3,07 | Sí | 6, 1, 1, 0, 5 |
| 2026-2 | G4 en LOGRADO | 5674-401 | [0, 1, 5, 4] | 5 + 4 = 9 de 10 | 90,0 | (17 + 16) / 10 = 3,30 | Sí | 1, 1, 1, 0, 0 |
| 2026-2 | G3 en INICIAL | 6511-401, PI 3.1 | [1, 2, 1, 1] | 2 de 5 | 40,0 | 12 / 5 = 2,40 | No | 1, 1, 0, 1, 0 |
| 2026-2 | E2 en REFUERZO | 450010-410 y 412 | [0, 0, 0, 0] | 0 de 0 | null | null | null | 2, 0, 0, 0, 2 |

- En 2026-2 las demás celdas no tienen secciones y traen `conteo_secciones` en 0, que son G3 en REFUERZO (450006, 450009 y 560046 sin secciones) y en LOGRADO (5674 sin plan del SO 3), E2 en INICIAL y en LOGRADO, y G6, G8, E1 y E3 en los tres estadíos (450002 no mide el SO 4).
- En 2024-2 solo G4 en REFUERZO tiene secciones, así que G4 en INICIAL y en LOGRADO dicen «Sin medición en el periodo».
- G1, G2, G5 y G7 no tienen SO en AMB-2026.

Las cifras exactas viven en el oráculo escrito a mano `tests/datos_inventados/oraculo_011.md` (propuesta), que copia las tablas de esta sección con su cuenta, junto a las tablas maestras inventadas de las que salen los exports (US-107). En el clúster desechable las tres filas de Química y todas las celdas de Ambiental coinciden con el oráculo. En la rama `demo-011` de Neon la siembra excluye 5643 en 2026-1, que develop ya tiene, así que la fila de 2026-1 de P9 muestra lo que develop tenga, y las celdas de 2026-2 coinciden con el oráculo solo si develop no tiene cargas de 450002, 6511 ni 5674 en 2026-2 (SC-003 y J-72).

## Equivalencias con el tablero

### «Histórico por Profesor» en P9

| Visual de la página | En P9 | Razón |
| --- | --- | --- |
| Segmentador de año y ciclo, con 2026 guardado | Sin filtro. P9 muestra todos los periodos visibles de la ruta 18 | La evolución necesita todos los periodos (US-100) |
| Segmentador de curso | Selector de curso con la ruta 21 del periodo de la cabecera y la asignatura del fragmento | AD-89, como en P8 |
| Segmentador de PI | Un bloque por PI del plan en la misma respuesta | Como en la spec 009, sin recalcular en el Front (BR-RESULTADOS-11) |
| Segmentador de profesor | Se omite y la página pasa a ser del curso y de sus secciones | D-57, D-59 y BR-RESULTADOS-10 |
| Segmentadores de competencia y de nivel | Se llevan a P10 | Pertenecen a las competencias por estadío (US-103 y US-104) |
| Gráfico de área del promedio de la calificación por periodo | «Promedio de calificación» de cada periodo | US-100 y US-101, con D-56, cerrada el 2026-11-25 en la spec 009 |
| Gráfico de líneas de alumnos aprobados y desaprobados por periodo | Una barra de dos tramos por periodo con sus dos conteos escritos | J-24 de la spec 004, sin una línea que una periodos sin carga (AD-108) |
| Orden por valor descendente de los dos gráficos | Orden por año y ciclo | BR-RESULTADOS-10 y AD-109 |

### «Resumen Competencias - Nivel» en P10

| Visual de la página | En P10 | Razón |
| --- | --- | --- |
| Drillthrough por periodo y segmentador de periodo | Periodo de la cabecera, como en P2 a P8 | La ruta 18 ya existe (US-73) y C-08 sale |
| Segmentador de SO | Rótulo de la fila de cada competencia | En AMB-2026 cada competencia tiene un solo SO |
| Segmentador de PI | Desglose por PI en el detalle de cada celda | Sin recalcular en el Front (BR-RESULTADOS-11) |
| Segmentador de nivel de asignatura | Las tres columnas INICIAL, REFUERZO y LOGRADO | US-103 |
| Segmentador de competencia | Una fila por competencia y, para la evolución, el selector de competencia | US-103 y US-104 |
| Gráfico de área del promedio por periodo | Promedio de cada celda y evolución por periodo de una competencia | US-102 y US-104 |
| Barras de secciones aprobadas y no aprobadas por periodo | Conteo escrito de secciones en la meta de cada celda | J-62 de la spec 009 |
| Barra al 100 % de alumnos aprobados y desaprobados | Barra de dos tramos de cada celda, en mediciones | AD-104 y D-32 |
| Tabla de sección, profesor, aprobados, promedio y % | Detalle de cada celda por asignatura y sección, sin profesor y en orden de código y número | D-57 y BR-RESULTADOS-10 |
| Color del porcentaje relativo al rango de la tabla | «En la meta» o «Debajo de la meta» con la meta absoluta del conjunto de reglas | BR-RESULTADOS-06 y BR-RESULTADOS-14 |

## Clarifications

### Session 2026-11-25

- Q: ¿Por qué P9 no es «por profesor»? → A: D-57 sigue abierta con el valor «no las ve», BR-RESULTADOS-10 prohíbe un orden de docentes y la «evolución histórica» que pide Claudia León se responde por curso y por sección. D-59 le pregunta si eso basta. El único corte por persona de la página es el segmentador de profesor, así que sin él los gráficos no cambian.
- Q: ¿Por qué P10 no se demuestra con Industrial? → A: IND-2026 no tiene rúbricas por nivel (D-50 de la spec 008) ni competencias ni estadíos (D-60), y las aserciones de `V1_12:246-264` exigen 0 filas en `rubrica_nivel`, `competencia` y `asignatura_competencia`. Inventar ese mapeo sería una migración con datos curriculares falsos. P10 se demuestra con Ambiental y dice con texto que Industrial aún no tiene el mapeo.
- Q: ¿Por qué el segundo periodo de Ambiental es 2024-2? → A: La coordinación de una carrera ve toda sección de una asignatura de su plan de estudios en un periodo con vigencia, y 5643 está en el plan de AMB-2026. Una vigencia de AMB en 2025-1, 2025-2 o 2026-1 deja a la coordinación de Ambiental ver las secciones de Química General de la demostración, así que la semilla crea el periodo 2024-2, que no tiene secciones de 5643 (J-75).
- Q: ¿Por qué la demostración no va a develop de Neon? → A: develop ya tiene 18 secciones de 5643 en 2026-1 con cargas de la capacitación, el ensayo se niega a cargar una asignatura con cargas en el periodo y J-52 pide una base aparte. La demostración vive en una rama de Neon creada desde develop, y retirarla es borrar esa rama (J-72).
- Q: ¿Las cargas de la demostración son R-17 antiguos? → A: No. Son exports inventados con el formato de Blackboard, así que quedan como BLACKBOARD_EXPORT. R17_HISTORICO queda para el lector de los R-17 de periodos anteriores (H34), que esta spec no construye y que hará falta cuando lleguen los R-17 reales.

Decisiones del dueño técnico del 2026-11-25. Cada una queda como valor provisional hasta la aprobación de la spec.

- Q: ¿Qué secciones forman una celda de la ruta 23? → A: Las de las asignaturas del plan de estudios de la carrera que tienen ese estadío para esa competencia en `abet.asignatura_competencia` y un `plan_medicion` de un PI de un SO de esa competencia en el periodo. Las que tienen carga PUBLICADA suman sus mediciones, y las demás, sin carga o con una carga RECHAZADA, cuentan en `conteo_secciones.sin_dato`, igual que en la ruta 20. El oráculo se recalcula con todas las secciones que la base de los escenarios trae, así que G4 en REFUERZO de 2026-2 tiene seis secciones y cinco sin dato, y la base de los escenarios no carga `db/pruebas/datos_sinteticos.sql` (FR-005, FR-006 y 2026-11-25).
- Q: ¿Dónde se comprueba el rango de códigos de la demostración? → A: En `sembrar_demostracion.py`, una sola vez antes de la primera carga y sobre los exports de todos los manifiestos juntos, y no en `ensayar_capacitacion.py`, que carga un manifiesto por corrida sin mirar el rango (FR-013, FR-014 y 2026-11-25).
- Q: ¿Qué siembra la demostración en 2026-1 de la rama `demo-011`? → A: Nada. La siembra excluye 5643 en 2026-1, que develop ya tiene, y `demo-011` hereda de develop los datos reales de 2026-1 que D-10 autoriza en Neon. Las cuentas inventadas de la vista previa ya los ven hoy en develop, y ninguna captura ni humo de Playwright los registra, por el preflight de la spec 008, que impide versionar capturas y resultados de Playwright (FR-022 de esa spec). Las celdas de 2026-2 del oráculo se comprueban en el clúster desechable, y en `demo-011` solo si develop no tiene cargas de esas asignaturas en 2026-2. Si las tiene, la siembra las informa y omite su ensayo (FR-014, SC-003, J-72 y 2026-11-25).
- Q: ¿La siembra se detiene entera o por asignatura ante cargas ajenas? → A: Depende del periodo. En los periodos que la demostración crea (2024-2, 2025-1 y 2025-2) una carga de una sección sin el prefijo SINTETICO_ es inesperada y la siembra entera se detiene antes de escribir. En un periodo que ya existe, como 2026-2, la siembra informa la asignatura con cargas ajenas y omite su ensayo, sin detenerse, que es lo que suponen SC-003 y J-72 (FR-014 y 2026-11-25).
- Q: ¿En qué orden arma `scripts/api_local.sh` la base de los escenarios? → A: Primero `sembrar_demostracion.py`, con su comprobación del rango, y después el ensayo de 5643 en 2026-1, porque esos exports no están en los manifiestos de la demostración y la comprobación del rango los leería como cargas ajenas. `plan_quimica_2026_1.sql` recibe una `DESCRIPCION_INSTRUMENTO` inventada (T025 y 2026-11-25).
- Q: ¿Qué recibe en la ruta 24 una cuenta con alcance CURSO? → A: 200 con la lista de periodos vacía, igual que la ruta 23, y la ruta 24 acepta el mismo parámetro opcional `carrera` (FR-009 y 2026-11-25).
- Q: ¿Quién decide la falta de la «Base cursos - Nivel» de Industrial? → A: La coordinación de Industrial, en la decisión nueva D-60, con el valor provisional «P10 muestra solo Ambiental». D-50 vuelve a su dueña, Stefanny Montaño, y a su alcance de la spec 008, que son las rúbricas por nivel de los PI de Industrial (2026-11-25).
- Q: ¿Siguen abiertas D-56 y D-32? → A: D-56 no. Se cierra el 2026-11-25 en la spec 009, porque las medidas DAX (Data Analysis Expressions) del tablero coinciden con el valor provisional (rama `docs/009-cierre-d56`). D-32 sigue abierta y nace en la spec 004 como el resumen de un PI medido en varias secciones y de un SO a partir de sus PI (H06 y P14), y esta spec no le atribuye PA-13, que en la spec 004 es solo la propuesta del SO en la meta (2026-11-25).

## User Scenarios & Testing *(mandatory)*

### US-100: La coordinación recibe la evolución del curso en la ruta 22 (Priority: P1)

Como coordinación de un curso o de una carrera, quiero recibir de una sola vez las cifras del curso y de cada sección en cada periodo con carga, para saber si el curso mejora entre ciclos sin abrir un resumen por periodo.

**Why this priority**: sin estas cifras P9 no tiene qué mostrar, y hoy ninguna ruta da más de un periodo. La historia no calcula nada nuevo, porque llama a `resumen_del_curso()` de la spec 009 una vez por periodo visible.

**Independent Test**: en una base desechable con las semillas de US-105 y las cargas de US-107, `GET /api/resumen-curso/evolucion?asignatura=5643` da al PI 6.1 tres periodos en el orden 2025-1, 2025-2 y 2026-1, con 60,0, 66,7 y 80,0, y solo 2026-1 en la meta.

**Base**: `abet.v_r17_por_pi`, `abet.seccion`, `abet.carga`, `abet.plan_medicion`, `abet.pi`, `abet.so`, `abet.periodo` (`anio` y `ciclo`) y `acceso.coordinacion_alcance` por `app/permisos.periodos_visibles()`, `secciones_visibles()` y `puede_ver_avance()`, con `abet_carga/resultados.resumen_del_curso()`. Sin migración.
**Pantalla**: ninguna propia. P9 la consume (US-101).

**Acceptance Scenarios** (`specs/011-historico-y-competencias/aceptacion/evolucion_del_curso.feature`):

1. **La evolución trae un elemento por periodo en orden cronológico**, con 6 de 10, 8 de 12 y 12 de 15 y solo 2026-1 en la meta.
2. **Cada periodo suma alumnos y no promedia porcentajes**, con 66,7 y no 62,8 en 2025-2.
3. **Cada periodo trae sus niveles, su promedio y sus alumnos sin evidencia.**
4. **El conteo de secciones de cada periodo cuenta la meta solo sobre las publicadas.**
5. **Las secciones van dentro de su periodo y en orden de número.**
6. **Un periodo con secciones y sin cargas publicadas trae nulos y no ceros.**
7. **Metas distintas dentro de un periodo dejan nula solo la meta de ese periodo.**
8. **Los periodos siguen el año y el ciclo y no el resultado.**
9. **La coordinación del curso ve solo los periodos de su alcance.**
10. **Cada periodo trae las mismas cifras que la ruta 20 de ese periodo.**
11. **Con un conjunto de reglas provisional cada periodo sale provisional.**
12. **La respuesta de la evolución trae solo las claves de su lista cerrada**, sin profesores ni estudiantes.
13. **El profesor recibe 403 en la evolución del curso.**
14. **Sin sesión la evolución responde 401.**
15. **Una asignatura mal formada responde 422 sin leer la base.**
16. **La coordinación de Ambiental recibe la evolución de 5643 sin indicadores.**

---

### US-101: P9 muestra la evolución del curso (Priority: P1)

Como coordinación de Química General, quiero ver en una página una fila por periodo con la cifra del curso, su barra, su promedio y sus secciones en la meta, y abrir cada periodo para ver sus secciones, para saber si el curso mejora entre ciclos, que es la «evolución histórica» que pidió Claudia León.

**Why this priority**: es lo que la coordinación ve de la página «Histórico por Profesor». Sin P9 la ruta 22 no llega a nadie.

**Independent Test**: con la respuesta simulada del primer escenario de US-100, Vitest encuentra en P9 tres filas en el orden 2025-1, 2025-2 y 2026-1 con «6 de 10 alumnos en el nivel esperado o superior (60,0 %)», «Promedio de calificación 2,70 de 4» y ninguna celda con un profesor.

**Base**: ninguna directa. P9 escribe lo que traen las rutas 22 y 21 (BR-RESULTADOS-11).
**Pantalla**: P9 «Evolución del curso» (propuesta), solo para la cuenta COORDINADOR, en el menú después de «Resumen del curso», enlazada desde cada curso de P7 y desde P8, con el fragmento `#/evolucion?asignatura=` y montada con `key` por asignatura. Reutiliza `BarraDelCurso`, `LineaDeMeta`, `TablaDeSecciones`, `Franja` y `SelectorDeCurso` de `src/pantallas/ResumenCurso.tsx`, exportados.

**Acceptance Scenarios** (`specs/011-historico-y-competencias/aceptacion/pantalla_evolucion_del_curso.feature`):

1. **P9 escribe una fila por periodo en orden cronológico con su cifra.**
2. **Cada fila escribe su promedio, sus alumnos sin evidencia y sus secciones en la meta.**
3. **La barra de cada periodo lleva su cifra escrita.**
4. **El detalle de un periodo trae sus secciones en orden de número con la meta absoluta.**
5. **Un periodo sin cargas publicadas no dibuja una barra de 0 %.**
6. **P9 no muestra profesores ni ordena por resultado.**
7. **P9 marca las cifras provisionales.**
8. **La coordinación de la carrera elige el curso de la evolución.**
9. **Solo la coordinación ve la evolución y la abre desde P7 y P8.**
10. **P9 a 375 px no se desplaza a lo ancho y se recorre con teclado** (Playwright).

---

### US-102: La coordinación de la carrera recibe el logro por competencia y estadío en la ruta 23 (Priority: P1)

Como coordinación de Ambiental, quiero recibir, para un periodo, las mediciones con nivel esperado o superior de cada competencia en cada estadío, con las asignaturas, las secciones y los PI que las componen, para saber si la carrera progresa a lo largo de la malla.

**Why this priority**: sin estas cifras P10 no tiene qué mostrar, y hoy ningún módulo de `abet_carga` ni de `app` lee `asignatura_competencia` ni `competencia_so`.

**Independent Test**: en una base desechable con las semillas de US-106 y las cargas de US-107, `GET /api/resumen-carrera/competencias?periodo=2026-2` da a G4 3 de 5 (60,0 %) en INICIAL, 12 de 15 (80,0 %) en REFUERZO y 9 de 10 (90,0 %) en LOGRADO, con REFUERZO y LOGRADO en la meta y 5 de las 6 secciones de REFUERZO sin dato.

**Base**: `abet.seccion` de `secciones_visibles()` unida a `abet.catalogo_vigencia` y `abet.plan_estudios` de la carrera en el periodo, a `abet.asignatura_competencia` por versión y asignatura (`pk_asignatura_competencia`, `ck_asignatura_competencia_estadio`), a `abet.competencia_so` por competencia y versión y a `abet.plan_medicion` de la carrera por periodo, asignatura y SO, con `abet.pi` por `pm.pi_id` y su código, y `abet.v_r17_por_pi` de las cargas PUBLICADA de esas secciones por `carga_id` con `abet.carga` (`carrera_id` y `seccion_id`). La carrera sale de `app/permisos.alcance_de()` y las secciones de `secciones_visibles()`. `abet_app` ya lee esas tablas (`crear_rol_app.sql:82-91`). Sin migración ni vista nueva (AD-84).
**Pantalla**: ninguna propia. P10 la consume (US-103).

**Acceptance Scenarios** (`specs/011-historico-y-competencias/aceptacion/competencias_por_estadio.feature`):

1. **G4 trae una celda por estadío con sus mediciones**, con 60,0, 80,0 y 90,0.
2. **Cada celda trae sus asignaturas, sus secciones y su desglose por PI**, con las seis secciones de G4 en REFUERZO y cinco sin dato.
3. **La 450002 suma a G4 por el SO 5 y no a G8.**
4. **La unidad de la celda es la medición de un estudiante en un PI.**
5. **Una celda sin mediciones trae nulos y no ceros.**
6. **Una sección sin carga publicada cuenta como sin dato en su celda.**
7. **Las competencias sin SO vienen sin celdas.**
8. **El plan de Industrial de 5643 no suma a E3 de Ambiental.**
9. **Todos los estadíos cuentan con el mismo nivel esperado.**
10. **Las competencias y los estadíos van en un orden fijo.**
11. **Cada celda trae sus mediciones por nivel y su promedio.**
12. **Con un conjunto de reglas provisional las celdas salen provisionales.**
13. **La respuesta de las competencias trae solo las claves de su lista cerrada.**
14. **La coordinación de un curso recibe la lista de competencias vacía.**
15. **Una carrera sin el mapeo de competencias recibe la lista vacía.**
16. **El profesor recibe 403 en las competencias y sin sesión la ruta responde 401.**
17. **Un periodo o una carrera mal formados responden 422 sin leer la base.**
18. **Una carrera fuera del alcance responde 200 con la lista vacía.**

---

### US-103: P10 muestra las competencias por estadío (Priority: P1)

Como coordinación de Ambiental, quiero ver una matriz de competencia por estadío con la cifra escrita en cada celda y abrir cada celda para ver sus asignaturas, sus secciones y sus PI, para llevar al comité el logro de la carrera a lo largo de la malla, como en la página «Resumen Competencias - Nivel».

**Why this priority**: es lo que la coordinación ve de la página 3 del tablero. Sin P10 la ruta 23 no llega a nadie.

**Independent Test**: con la respuesta simulada del primer escenario de US-102, Vitest encuentra en P10 la fila «G4 · SO 5 · PI 5.1, 5.2 y 5.3» con «12 de 15 mediciones en el nivel esperado o superior (80,0 %)» en REFUERZO, la fila G1 con «Sin SO asociado» y ninguna celda con la palabra «alumnos».

**Base**: ninguna directa. P10 escribe lo que trae la ruta 23 (BR-RESULTADOS-11).
**Pantalla**: P10 «Competencias por estadío» (propuesta), en el menú solo de la cuenta COORDINADOR con alcance CARRERA, con el fragmento `#/competencias` y el periodo de la cabecera. La matriz va en una región desplazable con nombre «Matriz de competencias», con barras HTML de dos tramos, `LineaDeMeta` y la cifra escrita, sin radar (AD-107).

**Acceptance Scenarios** (`specs/011-historico-y-competencias/aceptacion/pantalla_competencias.feature`):

1. **P10 escribe la matriz de G4 con una cifra por estadío.**
2. **La fila de cada competencia dice su SO y sus PI medidos.**
3. **El detalle de una celda trae sus asignaturas, secciones y PI sin profesores.**
4. **Una celda sin medición no dibuja una barra de 0 %.**
5. **Las competencias sin SO lo dicen en la fila.**
6. **P10 rotula mediciones y marca las cifras provisionales.**
7. **Una carrera sin el mapeo de competencias lo dice con texto.**
8. **La coordinación de un curso lee que la página es de la carrera.**
9. **P10 no ordena por resultado.**
10. **Solo la coordinación de la carrera ve las competencias en el menú.**
11. **P10 a 375 px solo desplaza a lo ancho la matriz y se recorre con teclado** (Playwright).

---

### US-104: La coordinación de la carrera ve la evolución de una competencia (Priority: P2)

Como coordinación de Ambiental, quiero elegir una competencia y ver sus tres estadíos en cada periodo con mediciones, para replicar los gráficos por periodo de la página «Resumen Competencias - Nivel».

**Why this priority**: los tres gráficos de la página 3 usan el periodo como eje, pero la matriz de US-103 ya responde la pregunta principal de la coordinación en un periodo, así que la evolución va después.

**Independent Test**: `GET /api/resumen-carrera/competencias/evolucion?competencia=G4` (propuesta) da a la coordinación de Ambiental 2024-2 y 2026-2 en ese orden, con REFUERZO en 60,0 y 80,0 e INICIAL sin medición en 2024-2.

**Base**: la consulta de US-102 una vez por periodo de `periodos_visibles()`, en la misma transacción de solo lectura.
**Pantalla**: P10, con el selector «Competencia» y la tabla de periodos por estadío.

**Acceptance Scenarios** (`competencias_por_estadio.feature` y `pantalla_competencias.feature`):

1. **La evolución de G4 trae los periodos visibles en orden cronológico.**
2. **Un periodo sin la vigencia de la carrera no aparece en la evolución.**
3. **Una competencia mal formada responde 422 y el profesor recibe 403.**
4. **La evolución de las competencias trata el alcance y la carrera como la ruta 23.**
5. **P10 escribe la evolución de G4 con una fila por periodo.**

---

### US-105: La semilla de Química suma 2025-1 y 2025-2 (Priority: P1)

Como dueño técnico, quiero una semilla `db/datos/historico_quimica_inventado.sql` (propuesta) con la vigencia de IND-2026, el plan de 5643 con el PI 6.1, las secciones, sus profesores y la fila de alcance de la coordinación del curso en 2025-1 y 2025-2, para que 5643 tenga tres periodos con carga y P9 muestre una evolución.

**Why this priority**: es el «si falta data, genera data» del pedido. Sin un segundo periodo, P9 tiene un solo punto.

**Independent Test**: en un clúster desechable con la siembra de Química de la spec 008, la semilla con `-v aplicar=1` deja a 5643 con plan del PI 6.1 en 2025-1, 2025-2 y 2026-1, y la ruta 18 ofrece a `coordinador.quimica@example.invalid` 2026-1, 2025-2 y 2025-1.

**Base**: `abet.catalogo_vigencia` (`pk_catalogo_vigencia`), `abet.plan_medicion` (`fk_plan_medicion_vigencia` y `uq_plan_medicion`), `abet.seccion` (`uq_seccion` y `uq_seccion_curso_bb`), `acceso.docente_seccion` (`uq_docente_seccion`) y `acceso.coordinacion_alcance` (`ck_coordinacion_alcance_periodo`), con la huella de `db/plataforma/neon/huella_ambiental.sql` y la lista `SEMILLAS` de `tests/semillas_inventadas.py`. La vigencia de IND-2026 en 2025 es una ficción del catálogo (H26) que vive solo en la rama de la demostración y en el clúster desechable (J-75).
**Pantalla**: ninguna. Da los datos de P9.

**Acceptance Scenarios** (`specs/011-historico-y-competencias/aceptacion/datos_de_demostracion.feature`):

1. **La semilla histórica corre en seco salvo con aplicar.**
2. **Con aplicar 5643 queda con plan, secciones, profesores y alcance en 2025-1 y 2025-2.**
3. **La ruta 18 ofrece los tres periodos a la coordinación del curso.**
4. **Las semillas de la demostración no cambian el catálogo.**
5. **Una segunda corrida de las semillas no duplica filas.**

---

### US-106: La semilla de Ambiental cubre los tres estadíos y un segundo periodo (Priority: P1)

Como dueño técnico, quiero una semilla `db/datos/competencias_ambiental_inventado.sql` (propuesta) con una asignatura por estadío de G4 en 2026-2 (6511 en INICIAL, 450002 en REFUERZO y 5674 en LOGRADO) y la 450002 en el periodo nuevo 2024-2, para que P10 muestre las tres columnas con datos y US-104 tenga dos periodos.

**Why this priority**: sin esta semilla Ambiental no tiene mediciones en INICIAL ni en LOGRADO, y P10 sale casi vacía.

**Independent Test**: en un clúster desechable con `periodo_2026_2_inventado.sql`, la semilla con `-v aplicar=1` deja el plan de 6511 con 3.1 y 5.1 y el de 5674 con 5.1 y 5.2 en 2026-2, la sección 413 de 450002 en 2026-2 y en 2024-2, y ningún plan con un SO que su asignatura no tributa.

**Base**: `abet.periodo` (2024-2, con `ck_periodo_anio` y `ck_periodo_ciclo`), `abet.catalogo_vigencia` (AMB-2026 en 2024-2, ficción del catálogo de J-75, y en 2026-2, que ya existe), `abet.plan_medicion` (`fk_plan_medicion_asig_so` y `fk_plan_medicion_pi`), `abet.asignatura_so`, `abet.seccion` y `acceso.docente_seccion`, con un profesor inventado por sección nueva. Reutiliza `coordinacion@example.invalid` y no crea otra cuenta de coordinación.
**Pantalla**: ninguna. Da los datos de P10.

**Acceptance Scenarios** (`specs/011-historico-y-competencias/aceptacion/datos_de_demostracion.feature`):

1. **La semilla de Ambiental respeta el SO de cada asignatura.**
2. **La semilla crea 2024-2 sin abrir Química a la coordinación de Ambiental.**
3. **Cada sección nueva de Ambiental tiene un profesor inventado.**

---

### US-107: Las tablas maestras inventadas suben por el flujo normal de carga (Priority: P1)

Como dueño técnico, quiero que las tablas maestras inventadas de cada periodo y asignatura pasen por `scripts/generar_exports_desde_maestra.py` y suban con `db/herramientas/ensayar_capacitacion.py` como el profesor de cada sección, para que la demostración recorra el lector, la validación, la publicación, el R-17 y el conciliador reales, sin INSERT directos en `abet.medicion`.

**Why this priority**: es lo que muestra el sistema de punta a punta. Sin cargas, P9 y P10 solo muestran nulos.

**Independent Test**: en el clúster desechable de `scripts/api_local.sh` con las semillas de US-105 y US-106, el ensayo de cada periodo y asignatura termina con «Ensayo sin diferencias», sin comprobar el rango de códigos, y las rutas 22 y 23 dan los conteos del oráculo `tests/datos_inventados/oraculo_011.md`.

**Base**: las tablas maestras inventadas de `tests/datos_inventados/maestras_011/` (propuesta), con códigos del rango 99500000 a 99599999, `generar_exports_desde_maestra.py` con `--pi` como lista (AD-97), `ensayar_capacitacion.py` con un manifiesto de varios PI y una corrida del conciliador por PI, sin la comprobación del rango, que vive en `sembrar_demostracion.py` (US-108), `abet_carga/carga.py` (`cargar()`, `tipo_fuente` BLACKBOARD_EXPORT por `ck_archivo_origen_tipo`, `fk_carga_reglas` y `ck_carga_conciliada`), `uq_archivo_origen_sha256`, `uq_carga_columna_pi`, `ck_carga_columna_encabezado`, `uq_estudiante_codigo` y `ck_estudiante_codigo`.
**Pantalla**: P4 (constancia de cada carga), y da los datos de P9 y P10.

**Acceptance Scenarios** (`specs/011-historico-y-competencias/aceptacion/datos_de_demostracion.feature`):

1. **El generador arma un export por sección con todos sus PI.**
2. **Dos corridas del generador dan los mismos bytes.**
3. **Ningún export de la demostración repite la huella de otro.**
4. **Un mismo estudiante inventado aparece en dos periodos con un solo registro**, sin que el ensayo compruebe el rango.
5. **Cada export sube por el flujo normal y queda publicado con su R-17.**
6. **Una segunda corrida del ensayo no sube nada.**
7. **El oráculo escrito a mano coincide con las tablas maestras y con las rutas.**

---

### US-108: La demostración se siembra en una rama de Neon aparte desde el Windows (Priority: P1)

Como Jefferson, quiero que las semillas y las cargas de la demostración corran desde DESKTOP-FKQ5ENS con `en_windows.py` en una rama de Neon creada desde develop, con respaldo previo, corrida en seco y negativa ante la rama principal, para ver P9 y P10 en una vista previa sin tocar develop ni la rama principal.

**Why this priority**: el pedido es que se vea que el sistema funciona, y eso pasa por una vista previa con datos en Neon. La regla global de Jefferson exige que toda escritura en una base salga del Windows.

**Independent Test**: sin `--aplicar`, `db/herramientas/sembrar_demostracion.py --rama demo` (propuesta) informa el respaldo, la huella, la comprobación del rango, las filas que escribiría y los ensayos que correría, sin 5643 en 2026-1, y no escribe, y con `--rama principal --aplicar` sin `--confirmo-principal` termina con 2 antes de conectarse.

**Base**: `db/herramientas/respaldar_neon.sh`, `db/plataforma/neon/huella_ambiental.sql`, `db/plataforma/neon/controles_neon.sql`, las semillas de US-105 y US-106 y el ensayo de US-107, con `~/.claude/scripts/en_windows.py` para las variables de libpq. El guion sigue el molde de `sembrar_quimica.py`, comprueba el rango de códigos una sola vez antes de la primera carga, nunca carga 5643 en 2026-1, se detiene si uno de los periodos que la demostración crea (2024-2, 2025-1 y 2025-2) tiene cargas de secciones cuyo `curso_blackboard` no empieza con SINTETICO_, y en un periodo que ya existe, como 2026-2, omite, con aviso, el ensayo de una asignatura que ya tiene en el periodo cargas que no son de la demostración (FR-014).
**Pantalla**: P9 y P10 en la vista previa de Vercel que apunta a la rama de la demostración (J-72).

**Acceptance Scenarios** (`specs/011-historico-y-competencias/aceptacion/datos_de_demostracion.feature`):

1. **Sin --aplicar la siembra de la demostración no escribe y no toca 5643 en 2026-1.**
2. **La rama principal pide --confirmo-principal y termina antes de conectarse.**
3. **La siembra comprueba el rango de códigos una sola vez antes de la primera carga.**
4. **Un estudiante del rango en la base detiene la siembra antes de escribir.**
5. **Un export con un código fuera del rango detiene la siembra antes de conectarse.**
6. **La siembra se detiene ante cargas de secciones sin el prefijo SINTETICO_.**
7. **La siembra informa y omite una asignatura con cargas que no son de la demostración.**
8. **Una segunda corrida de la siembra no sube nada.**
9. **Las consultas de control no dan filas después de la siembra.**

### Edge Cases

- Una asignatura cuyo plan cambia de PI entre periodos trae en la ruta 22 un elemento por PI, y cada PI lista solo los periodos en que su plan lo mide.
- Un periodo con plan y sin secciones visibles no aparece en la ruta 22 ni en la 24, igual que en la ruta 18.
- Una sección sin carga PUBLICADA, porque no tiene carga o porque su carga quedó RECHAZADA, cuenta en `conteo_secciones.sin_dato` de su periodo y de cada celda a la que aporta, igual que en la ruta 20, y no suma mediciones.
- Una asignatura con un estadío para una competencia y sin plan de un PI de un SO de esa competencia en el periodo no aporta secciones a esa celda, como 450002 en G8 y 5674 en G3 en 2026-2.
- Una sección cuyo plan mide PI de dos competencias aporta a las celdas de las dos, y cada celda suma solo las mediciones de sus PI, como la 401 de 6511 en G3 y en G4 de INICIAL.
- Un alumno sin evidencia no cuenta en los calificados ni en el promedio de su periodo, y una medición sin evidencia no cuenta en los calificados de su celda.
- Toda medición de AMB-2026 tiene estadío, porque los 61 pares asignatura-SO de AMB-2026 tienen su competencia y su estadío. Una prueba afirma que la consulta de US-102 deja 0 mediciones sin estadío con las semillas de la demostración.
- Un SO con dos competencias en una versión futura hace que una medición sume a las dos filas, y ninguna pantalla suma filas de competencias distintas (AD-85).
- El periodo de verano (ciclo 0) va antes del ciclo 1 del mismo año.
- Una cuenta COORDINADOR con varias carreras pide la carrera con el parámetro opcional `carrera` de las rutas 23 y 24. Sin el parámetro, cada ruta usa la primera en orden de código (propuesta).

## Requirements *(mandatory)*

- **FR-001** La ruta 22, `GET /api/resumen-curso/evolucion?asignatura=CODIGO` (propuesta), atiende solo a la cuenta COORDINADOR con el guardián de la ruta 20 y responde 401 sin sesión, 403 `SOLO_COORDINACION` al PROFESOR y 422 `ASIGNATURA_MAL_FORMADA` sin leer la base, en ese orden.
- **FR-002** La ruta 22 recorre `periodos_visibles()` y, en cada periodo, toma las secciones de la asignatura dentro de `secciones_visibles()` y llama a `resultados.resumen_del_curso()` sin copiar su suma, su redondeo ni su trato de metas, todo en una sola transacción READ ONLY con REPEATABLE READ. Un periodo sin secciones visibles de la asignatura no aparece, y fuera del alcance la ruta responde 200 con `indicadores` vacío y el nombre en `null`.
- **FR-003** La respuesta de la ruta 22 trae `asignatura` (`codigo` y `nombre`) e `indicadores`, con un elemento por PI en orden de SO y PI con `so`, `pi` y `periodos`. Cada periodo trae `periodo`, `nivel_esperado`, `meta_pct`, `provisional`, `curso`, `conteo_secciones` y `secciones`, con el mismo contenido de la §16.2 del contrato, en orden de año y ciclo ascendente, y nada más (lista cerrada, propuesta).
- **FR-004** La ruta 23, `GET /api/resumen-carrera/competencias?periodo=AAAA-C[&carrera=CODIGO]` (propuesta), atiende solo a la cuenta COORDINADOR, toma la carrera de `alcance_de()` y responde 401, 403 `SOLO_COORDINACION` y 422 con `PERIODO_MAL_FORMADO` o con «La carrera no tiene la forma de un código de 2 a 10 letras mayúsculas.» (propuesta, según `ck_carrera_codigo`) sin leer la base. Sin periodo usa PERIODO_VIGENTE. Una cuenta con alcance CURSO, una carrera fuera de sus filas de alcance y una carrera sin mapeo reciben 200 con `competencias` vacío.
- **FR-005** La consulta de la ruta 23 vive en `abet_carga/resultados.py` (AD-84). Las secciones de una celda (competencia, estadío y periodo) son las de `secciones_visibles()` cuya asignatura está en el plan de estudios de la versión vigente de la carrera en el periodo, tiene ese estadío para esa competencia en `abet.asignatura_competencia` de esa versión y tiene en el periodo un `plan_medicion` de la carrera con un PI de un SO de esa competencia según `abet.competencia_so`. Las secciones con carga PUBLICADA de la carrera suman a la celda sus mediciones de esos PI desde `abet.v_r17_por_pi`, unida por `carga_id` con `abet.carga`, `abet.plan_medicion` y `abet.pi` dentro de la versión del plan. Las demás, sin carga o con una carga RECHAZADA, cuentan en `conteo_secciones.sin_dato`, igual que en la ruta 20. No nace vista ni GRANT.
- **FR-006** La respuesta de la ruta 23 trae `periodo`, `carrera` (`codigo` y `nombre`) y `competencias`, en el orden de las genéricas G1 a G8 y después las específicas E1 a E3, cada una con `codigo`, `nombre`, `so`, `pis` y `estadios`, donde `pis` son los PI del plan de medición que aportan a sus celdas en el periodo, en orden de código. Una competencia sin SO trae `so` en `null` y `estadios` vacío. Una con SO trae los tres estadios en el orden INICIAL, REFUERZO y LOGRADO, cada uno con `estadio`, `nivel_esperado`, `meta_pct`, `provisional`, `mediciones_por_nivel`, `logrados`, `calificados`, `sin_evidencia`, `pct_sobre_calificados`, `promedio_nivel`, `en_meta`, `conteo_secciones` (con `total`, `publicadas`, `en_meta`, `debajo_de_la_meta` y `sin_dato`, como la ruta 20), `pis` (con `pi`, `logrados`, `calificados` y `pct_sobre_calificados`) y `asignaturas` (con `codigo`, `nombre` y `secciones`, en orden de código, y cada sección con `numero`, `estado`, que es PUBLICADA o SIN_CARGA como en la ruta 20, `logrados`, `calificados`, `pct_sobre_calificados` y `en_meta`, en orden de número y con los cuatro últimos en `null` sin carga publicada), y nada más (lista cerrada, propuesta).
- **FR-007** Cada celda suma mediciones de estudiante por PI de las cargas PUBLICADA y nunca promedia porcentajes. El porcentaje es la suma de logrados entre la suma de calificados con `ROUND(numeric, 1)`, el promedio es la suma de cada nivel por su conteo entre la suma de los conteos con `ROUND(numeric, 2)` y `en_meta` sale de `en_meta()` sobre el porcentaje redondeado. Una celda sin mediciones trae `calificados` 0 y el porcentaje, el promedio y `en_meta` en `null`, y una celda sin secciones trae además `conteo_secciones` en 0 y `asignaturas` vacío. Si las metas de sus cargas difieren, `meta_pct` y `en_meta` de la celda quedan en `null`.
- **FR-008** El estadío solo agrupa, y el nivel esperado de cada celda es el NIVEL_ESPERADO del conjunto de reglas de sus cargas (D-38).
- **FR-009** La ruta 24, `GET /api/resumen-carrera/competencias/evolucion?competencia=CODIGO[&carrera=CODIGO]` (propuesta), atiende solo a la cuenta COORDINADOR, responde 401 y 403 `SOLO_COORDINACION` como la ruta 23, toma la carrera de `alcance_de()` con el mismo parámetro opcional `carrera` y valida sin leer la base `competencia` con «La competencia no tiene la forma de una letra G o E seguida de su número.» (propuesta, según `ck_competencia_codigo`) y `carrera` con el mensaje de FR-004. Devuelve `carrera`, `competencia` (`codigo`, `nombre` y `so`) y `periodos`, con un elemento por periodo de `periodos_visibles()` en orden ascendente, y cada uno con `periodo` y los tres estadios de esa competencia con las claves de FR-006 salvo `asignaturas`. Una cuenta con alcance CURSO, una carrera fuera de sus filas de alcance y una carrera sin mapeo reciben 200 con `periodos` vacío, igual que la ruta 23.
- **FR-010** Ninguna respuesta de las rutas 22, 23 y 24 trae correos, nombres de personas, `usuario_id`, códigos de estudiantes, `subida_por`, `nombre_archivo` ni `sha256`, y las tres rutas entran a la lista de rutas con sesión de la prueba de J-25 y a `tests/rutas_registradas.py`.
- **FR-011** P9 y P10 escriben las cifras de sus rutas sin recalcularlas, dibujan las barras con HTML y Tailwind, con el ancho en `style` y `aria-hidden`, sin biblioteca de gráficos, en un orden que no depende de la cifra, sin profesores y con la franja «Cifras provisionales.» cuando la respuesta trae `provisional` verdadero. P10 rotula su unidad «mediciones» y nunca «alumnos».
- **FR-012** La semilla de US-105 y la de US-106 corren en seco salvo con `-v aplicar=1`, son idempotentes, entran a `SEMILLAS` de `tests/semillas_inventadas.py` y dejan iguales las partes 1 a 6 de `huella_ambiental.sql` y las aserciones de `V1_12:246-264`.
- **FR-013** `generar_exports_desde_maestra.py` acepta varios `--pi` y escribe un export por sección con todos sus PI, con bytes fijos y salida fuera de todo repositorio. `ensayar_capacitacion.py` acepta un manifiesto con varios PI y corre el conciliador una vez por PI, y no comprueba el rango de códigos de la demostración, que es de `sembrar_demostracion.py` (FR-014).
- **FR-014** `db/herramientas/sembrar_demostracion.py` (propuesta) corre en orden respaldo, huella, comprobación del rango, semillas, ensayo por periodo y asignatura y consultas de control de `controles_neon.sql`, en seco sin `--aplicar`, con `--rama demo|develop|principal` y con `--confirmo-principal` exigido antes de conectarse para la principal.
  - Antes de conectarse lee los exports de todos los manifiestos y termina con 1 si alguno trae un código fuera de 99500000 a 99599999, con «Un export de la demostración trae códigos fuera del rango 99500000 a 99599999.» (propuesta), que nombra el periodo, la asignatura y la sección sin el código.
  - Ya conectada, comprueba el rango una sola vez, antes de la primera escritura y sobre todos los manifiestos juntos, y termina con 1 sin escribir, con «El rango de códigos de la demostración ya está en uso.» (propuesta), si `abet.estudiante` tiene un código del rango sin mediciones o con alguna medición de una carga cuyo archivo no tiene la huella SHA-256 de un export de los manifiestos. Si pasa, el informe lo dice una sola vez con «Rango de códigos de la demostración libre.» (propuesta), y ningún ensayo lo vuelve a comprobar.
  - Nunca carga 5643 en 2026-1, que develop ya tiene, y no escribe en 2026-1. En el clúster desechable esas cargas las hace `scripts/api_local.sh` con el ensayo (T025).
  - Se detiene sin escribir ante un periodo que escribe con cargas de secciones sin el prefijo SINTETICO_. Una asignatura que ya tiene en el periodo cargas de secciones SINTETICO_ que no son de la demostración se informa con «ASIGNATURA en PERIODO ya tiene cargas que no son de la demostración. Se omite su ensayo.» (propuesta) y su ensayo no corre, y un export cuya carga ya existe por su huella se informa como cargado y no se sube.
  - Se lanza desde el Windows con `en_windows.py`, y sus comandos y salidas esperadas quedan en `db/README.md`.
- **FR-015** Las cargas de la demostración quedan con `tipo_fuente` BLACKBOARD_EXPORT, y R17_HISTORICO sigue reservado para el lector de H34 (AD-98).
- **FR-016** La §17 del contrato del Front describe las rutas 22, 23 y 24 con su lista cerrada de claves y un ejemplo inventado, la tabla general las suma y conserva la ruta 19 como reservada, y ADR-011 enmienda ADR-010 y la §16.4 para la evolución por curso y sección y las competencias por estadío, sin vistas por profesor.

## Success Criteria *(mandatory)*

- **SC-001** Los escenarios de los cinco `.feature` tienen su prueba en pytest-bdd, en Vitest o en Playwright, y pasan.
- **SC-002** En el clúster desechable de `scripts/api_local.sh` con las semillas y las cargas de la demostración, el humo con Playwright ve en P9 60,0 %, 66,7 % y 80,0 % en ese orden y en P10 60,0 %, 80,0 % y 90,0 % para G4.
- **SC-003** En la vista previa que apunta a la rama `demo-011`, P9 de 5643 muestra 2025-1 y 2025-2 con las cifras del oráculo y P10 de Ambiental muestra la celda del oráculo de 2024-2. Las celdas de 2026-2 se comprueban en el clúster desechable (SC-002), y en `demo-011` solo si develop no tiene cargas de 450002, 6511 ni 5674 en 2026-2. Si las tiene, la siembra las informa y omite su ensayo, y SC-003 no compara esas celdas. En `demo-011` se comparan logrados, calificados, porcentaje y promedio, y no `conteo_secciones`, que depende de las secciones de 2026-2 que develop tenga. La fila de 2026-1 de P9 muestra los datos reales de develop (D-10), que el humo no afirma ni captura.
- **SC-004** Ninguna respuesta ni pantalla de esta spec trae un dato de personas, como comprueban los escenarios de las listas cerradas y el barrido de privacidad de la spec 008.
- **SC-005** Develop y la rama principal de Neon quedan sin filas de la demostración, como muestra la huella de develop antes y después de la siembra.

## Decisiones abiertas

De la carrera, de la Oficina de Calidad, de Claudia León y de Stefanny (D). Mientras no se decidan, el sistema aplica el valor provisional.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| D-59 | Si la «evolución histórica» que pide Claudia León es la del curso y de sus secciones por periodo, en lugar de la del profesor | Curso y secciones por periodo, sin profesores, mientras D-57 siga con «no las ve» | Claudia León y la coordinación de la carrera |
| D-32 | Cómo se resume un PI medido en varias secciones y un SO a partir de sus PI (D-32 de la spec 004, H06 y P14) y, en esta spec, una competencia medida por varios PI y asignaturas | Suma de mediciones de estudiante por PI en cada celda, rotulada «mediciones», con la franja provisional | Coordinación de Ambiental y Oficina de Calidad |
| D-38 | Si cada estadío tiene su propio nivel esperado | Un solo NIVEL_ESPERADO por conjunto de reglas, y el estadío solo agrupa | Coordinación de Ambiental |
| D-50 | Rúbricas por nivel de los PI de Industrial (spec 008) | IND-2026 en BORRADOR sin filas en `abet.rubrica_nivel` hasta la «Plantilla Base - Final» de Industrial, como en la spec 008 | Stefanny Montaño |
| D-56 | Fórmulas DAX de «Alumnos Aprobados», «Alumnos Desaprobados», «Secciones No Aprobadas» y «Promedio Nota» | Cerrada el 2026-11-25 en la spec 009, porque las medidas del tablero coinciden con el valor provisional, sobre los calificados (rama `docs/009-cierre-d56`) | Stefanny Montaño |
| D-57 | Si la coordinación ve vistas por profesor | No las ve | Coordinación de la carrera y Oficina de Calidad |
| D-60 | La «Base cursos - Nivel» de Industrial, con las competencias y el estadío de cada asignatura de IND-2026 | P10 muestra solo Ambiental, y P10 de Industrial dice con texto que la carrera aún no tiene el mapeo | Coordinación de Industrial |

De Jefferson (J).

| ID | Decisión | Valor provisional |
| --- | --- | --- |
| J-72 | Dónde vive la demostración en Neon y cómo se ve | Una rama `demo-011` creada desde develop, sembrada desde el Windows con respaldo previo y corrida en seco. La siembra excluye 5643 en 2026-1, que develop ya tiene, y `demo-011` hereda los datos reales de 2026-1 que D-10 autoriza en Neon, que las cuentas inventadas de la vista previa ya ven hoy en develop y que ninguna captura ni humo de Playwright registra (preflight de la spec 008). Las celdas de 2026-2 del oráculo valen en `demo-011` solo si develop no tiene cargas de esas asignaturas en 2026-2 (SC-003). La vista previa de una rama de git propia del Back y del Front apunta a ella con variables de vista previa limitadas a esa rama, que pone Jefferson, y el retiro es borrar la rama. La alternativa de la lente de necesidad es develop solo en los periodos sin cargas reales |
| J-73 | Ruta 22 y P9 propias en lugar de un modo de varios periodos en la ruta 20 o una pestaña en P8 | Ruta 22 y P9, enlazada desde el menú, P7 y P8 |
| J-74 | Consulta de las competencias en `resultados.py` o vista R__ nueva | Consulta en `resultados.py`, y una vista nace solo si Power BI la pide, con su decisión |
| J-75 | Ficciones del catálogo de la demostración | IND-2026 en 2025-1 y 2025-2 y AMB-2026 en el periodo nuevo 2024-2, solo en la rama de la demostración y en el clúster desechable, declaradas en cada semilla |
| J-76 | Construir P9 y P10 con D-32 y D-59 abiertas, con D-56 ya cerrada en la spec 009 | Sí, con la franja provisional, como J-60 de la spec 009 |
| J-77 | Cuándo se construye | Después de construir la spec 010 y fuera de la ventana congelada de la capacitación (J-56), con unas 62,5 h con el contrato, el humo, la carga en Neon y el cierre |

## Fuera de alcance

- Pasar de un periodo de P9 al resumen de ese periodo en P8 (C-08), porque el selector de la cabecera ya abre P8 en cualquier periodo.
- La conciliación de varios periodos en una sola corrida (C-35), porque el ensayo corre el conciliador por periodo.
- Un guion de retiro que borre filas en develop (C-49), porque el retiro es borrar la rama de la demostración.
- El umbral de celda pequeña (C-66), que pediría una decisión de la carrera para las rutas 20, 22, 23 y 24 a la vez.
- El aviso de datos de demostración (C-67). Si hiciera falta, la alternativa del crítico es un aviso por entorno en la vista previa, sin tocar el contrato.
- Las vistas por profesor del tablero, hasta D-57.
- El lector de los R-17 de periodos anteriores (H34) y la conciliación con datos reales de periodos anteriores, que esperan esos R-17.
- El mapeo de competencias y estadíos de Industrial, hasta D-60, y sus rúbricas por nivel, hasta D-50 de la spec 008.
- Ningún valor de las filas del tablero entra a git, ni como oráculo ni como ejemplo (C-69 como restricción), y la igualdad con el tablero se prueba fuera del repositorio, como en el cierre de D-56 de la spec 009.
