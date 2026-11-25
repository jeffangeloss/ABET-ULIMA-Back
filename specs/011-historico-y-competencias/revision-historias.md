# Revisión por refutación de las historias de la evolución del curso y de las competencias por estadío

**Fecha**: 2026-11-25
**Spec**: [spec.md](./spec.md)
**Entrada**: 58 candidatas escritas desde cuatro ángulos, el de la coordinación del curso y de la carrera (C-01 a C-16), el de la base, el Back y las cifras (C-20 a C-37), el de los datos inventados de la demostración de punta a punta (C-40 a C-54) y el del acceso, la privacidad y la evidencia (C-60 a C-72), cada una con su pantalla, sus tablas y restricciones y su Gherkin en español. Salen del pedido de Jefferson del 2026-11-25 sobre las páginas «Histórico por Profesor» y «Resumen Competencias - Nivel» del tablero de Power BI de Stefanny Montaño, con la frase «Si falta data, genera data, todo para que se pueda ver que el sistema funciona de punta a punta :)»
**Salida**: 9 historias (US-100 a US-108) en 5 archivos `.feature`
**Fuentes**: los informes de las tres lentes y del crítico de arquitectura de la sesión del 2026-11-25 y las tres exploraciones de solo lectura (tablero, base y pantallas). El tablero es `infodata/Resumen de indicadores ABET - Cursos de Carrera.pbix`, fuera de todo repositorio, y su lectura solo toma la forma de los visuales. Ninguna candidata ni esta revisión copia un valor de las filas del tablero ni un dato real

## Método

Cada candidata parte refutada y sobrevive solo si resiste tres lentes independientes, como en las specs 001 y 003 a 010. La lente de necesidad pregunta si la exige el pedido, una regla vigente o la demostración, y si cambia algo que `develop` no hace ya. La lente de solapamiento y tamaño aplica INVEST (independiente, negociable, valiosa, estimable, pequeña y verificable) y busca choques con las historias que ya existen. La lente de verificabilidad recalcula las cifras de cada escenario y comprueba sus columnas, restricciones y mensajes contra el código y la base. Un crítico de arquitectura juzga aparte las decisiones técnicas con SE_SOSTIENE, CAMBIAR o DUDOSA.

Los veredictos de las lentes son SOBREVIVE (S), CORREGIR (C), FUSIONAR (F), PARTIR (P), MOVER_A_DESPUES (M) y REFUTADA (R). Una candidata sale cuando dos lentes o más la marcan R o M. Las que quedan aplican sus FUSIONAR, PARTIR y CORREGIR, y cada decisión con CAMBIAR del crítico toma su alternativa.

## Las dos páginas del tablero

El tablero usa el formato PBIR (Power BI Enhanced Report), así que cada visual se lee en `Report/definition/pages/*/visuals/*/visual.json`. Ninguna de las dos páginas trae tarjetas ni radar, y ningún visual tiene filtros propios.

- **«Histórico por Profesor».** Un gráfico de área con el promedio de la calificación por periodo, un gráfico de líneas con «Alumnos Aprobados» y «Alumnos Desaprobados» por periodo y seis segmentadores de año y ciclo (con 2026 guardado), curso, PI, profesor (con un profesor guardado), competencia y nivel de asignatura. Los dos gráficos ordenan por valor descendente y no por periodo. El único corte por persona es el segmentador de profesor, así que la página sin él queda como evolución del curso por periodo.
- **«Resumen Competencias - Nivel».** Es la página de destino de un drillthrough por periodo. Trae un gráfico de área con el promedio de la calificación por periodo, barras de «Secciones Aprobadas» y «Secciones No Aprobadas» por periodo, una barra al 100 % de alumnos aprobados y desaprobados por periodo, una tabla de sección, profesor, «Alumnos Aprobados», «Promedio Nota» y «% Alumnos 3-4» con un color de fondo relativo al rango de la tabla, y segmentadores de periodo, SO, PI, nivel de asignatura y competencia. Las competencias y los niveles entran solo por la tabla «Competencia - Nivel» de los segmentadores.

Las fórmulas DAX (Data Analysis Expressions) de «Alumnos Aprobados», «Alumnos Desaprobados» y «Secciones No Aprobadas» viven en el `DataModel` comprimido y esta revisión no las leyó. D-56 se cierra el 2026-11-25 en la spec 009, porque las medidas del tablero coinciden con el valor provisional (rama `docs/009-cierre-d56`).

## Veredictos por candidata

### Ángulo 1. La coordinación del curso y de la carrera

| Candidata | Título | Necesidad | Solapamiento y tamaño | Verificabilidad | Destino |
| --- | --- | --- | --- | --- | --- |
| C-01 | La coordinación ve cómo evoluciona su curso | S, los dos gráficos de la página 2 usan el periodo como eje y Claudia León pide la «evolución histórica» | S, es la historia de P9 y reutiliza las piezas de P8 | S, 6 de 10, 8 de 12 y 12 de 15 dan 60,0, 66,7 y 80,0 con `en_meta()` | US-101 |
| C-02 | Alumnos que alcanzan y que no, por periodo | S, el gráfico de líneas de la página 2 cruza los dos conteos | F con C-01, el objeto `curso` de la §16.2 ya los trae | S, `calificados` es `n_total` menos `n_sin_evidencia` y da 12 y no 13 | Escenarios de US-100 y US-101 |
| C-03 | Promedio de nivel por periodo | S, los gráficos de área promedian la calificación | F con C-01 y C-21, US-91 ya lo calcula | S, 27 / 10 da 2,70 con `ROUND(numeric, 2)` | Escenarios de US-100 y US-101, con la duda del crítico (AD-106) |
| C-04 | Secciones en la meta por periodo | S, las barras de la página 3 cuentan secciones por periodo | F con C-01, `conteo_secciones` ya existe | S, `_conteo_de_secciones()` da 4, 3, 2, 1 y 1 en 2026-1 | Escenarios de US-100 y US-101 |
| C-05 | Detalle por sección dentro de cada periodo | S, la tabla de la página 3 lista secciones, sin la columna de profesor | F con C-01, es `TablaDeSecciones` repetida | S, la 703 de 2025-2 da 33,3 con 1 de 3 | Escenario de US-101, con C-25 y C-33 |
| C-06 | Elegir el curso de la evolución | S, el segmentador de curso de la página 2 | F con C-01, con la ruta 21 del periodo de la cabecera | C, un plan sin secciones no sale, así que el Dado suma secciones | Escenario de US-101, con la ruta 21 del periodo de la cabecera (AD-89) |
| C-07 | Llegar a P9 desde P7 y P8 y volver | F, el menú basta y `ir()` ya resuelve «Atrás» | F con C-01, sigue el patrón de J-63 | S, `Vista`, `vistaDe` e `ir()` existen | Escenario de US-101 |
| C-08 | Pasar de un periodo de P9 al resumen de ese periodo | M, el drillthrough del tablero va a la página de competencias | M, el selector de la cabecera ya abre P8 en cualquier periodo | C, con dos periodos la cabecera muestra un selector y no un texto | Sale por dos lentes, a «Fuera de alcance» |
| C-09 | Logro por competencia y estadío | S, núcleo de la página 3 y del pedido para Ambiental | S, es la historia de P10 | C, la 410 de 450002 ya tiene una carga de 11 estudiantes en `datos_sinteticos.sql`, así que la demostración usa la 413 | US-103 |
| C-10 | Qué cursos componen cada celda | C, pasa a ser el detalle por sección de una competencia y un estadío, sin profesor | F con C-09, asignaturas y secciones de cada celda en la misma respuesta | C, la 413 en lugar de la 410 y la lista cerrada suma `asignaturas` y `conteo_secciones` | Escenarios de US-102 y US-103 |
| C-11 | Una competencia por SO y por PI | C, la página filtra por PI y el SO queda como rótulo | F con C-09, en AMB-2026 cada competencia tiene un solo SO | S, la unión de los PI medidos de G4 da 5.1, 5.2 y 5.3 | Escenarios de US-102 y US-103. El desglose por PI de cada celda reemplaza el segmentador, como el bloque por PI de la spec 009 |
| C-12 | Evolución de una competencia por periodo | S, los tres gráficos de la página 3 usan el periodo como eje | M, Ambiental tendría un solo periodo medido | C, una vigencia de AMB en 2026-1 deja a la coordinación de Ambiental ver las secciones de 5643 | US-104, con un segundo periodo de Ambiental (J-75) |
| C-13 | Industrial dice por qué no tiene competencias | F con C-09, es un estado vacío | F con C-09 | S, `V1_12:246-264` exige 0 filas para IND-2026 | Escenarios de US-102 y US-103 |
| C-14 | Barra de dos tramos por periodo | F con C-02 | F con C-01, es `BarraDelCurso` (J-24 y J-62) | S, 6 y 4 de 10 dan 60,0 y 40,0 | Escenario de US-101 |
| C-15 | Franja provisional en P9 y P10 | S, D-32 sigue abierta y J-60 exige la franja | F con C-01 y C-09, `Franja` ya existe | S, R-2026-BORRADOR tiene parámetros PENDIENTE | Escenarios de US-100 a US-103 |
| C-16 | Un periodo sin cargas no inventa cifras | F con C-01 | F con C-21 | S, `_curso_del_resumen(None)` ya da nulos | Escenarios de US-100 y US-101 |

### Ángulo 2. La base, el Back y las cifras

| Candidata | Título | Necesidad | Solapamiento y tamaño | Verificabilidad | Destino |
| --- | --- | --- | --- | --- | --- |
| C-20 | Consulta de la evolución sin vista nueva | F, es la tarea de C-01 | R, duplica `resumen_del_curso()`, que basta llamar una vez por periodo | S, la vista ya filtra PUBLICADA | US-100, con `resumen_del_curso()` por periodo (AD-83) |
| C-21 | Ruta 22 con lista cerrada de claves | F con C-01 | C, es el ancla del Back y recorre `periodos_visibles()` y `resumen_del_curso()` | C, la lista suma `nivel_esperado`, `meta_pct` y `provisional` por periodo | US-100 |
| C-22 | Cada periodo suma alumnos | F, BR-RESULTADOS-13 ya lo exige | F con C-21 | S, 8 / 12 da 66,7 y el promedio de porcentajes daría 62,8 | Escenario de US-100 |
| C-23 | Meta y nivel esperado por periodo | M, la demostración usa un solo conjunto por carrera | F con C-21, la regla de `resultados.py:111-128` por periodo | C, una meta de 0,70 pide un segundo conjunto de IND | Escenario de US-100 con R-2025-INVENTADO solo en la prueba |
| C-24 | Orden cronológico por año y ciclo | F con C-61 | F con C-21, usar los periodos de la demostración | C, 2025-0 no existe en `V1_03` | Escenario de US-100 con 2025-0 creado solo en la prueba (AD-109) |
| C-25 | La sección no es una serie entre periodos | F con C-05 | F con C-01 | S, `uq_seccion` hace distinta cada 701 | Escenarios de US-100 y US-101 |
| C-26 | Unión de la medición con la competencia y el estadío | F con C-09 | S, es el ancla del Back de las competencias | C, la vista no expone `so_id` ni `catalogo_version_id`, así que la unión pasa por `carga`, `seccion`, `plan_medicion` y `pi` | US-102, con la consulta en `resultados.py` (AD-84) |
| C-27 | La unidad es la medición estudiante por PI | F con C-09 | F con C-26 | C, la 413 en lugar de la 410 | Escenarios de US-102 y US-103 |
| C-28 | Lo que no tiene estadío queda fuera | C, entra el primer escenario y sale el contador | F con C-26 | C, el primer escenario necesita la vigencia de AMB en la prueba y el segundo no se puede preparar sin tocar el catálogo | Escenario de US-102 y una aserción de 0 mediciones sin estadío |
| C-29 | Competencias sin SO se listan sin cifra | R, nada lo pide | F con C-09, salen del catálogo | S, G1, G2, G5 y G7 no tienen fila en `competencia_so` | Escenarios de US-102 y US-103 |
| C-30 | Ruta 23 de competencias para la coordinación de carrera | F con C-09 | F con C-26 | C, faltan el 422 de la carrera y las claves `so`, `pis`, `asignaturas` y `conteo_secciones` | US-102, con la ruta `GET /api/resumen-carrera/competencias` (AD-112) |
| C-31 | Permiso de lectura de una vista nueva | R, `crear_rol_app.sql` ya da SELECT de las tablas de competencias | F con C-26, desaparece sin vista | C, el escenario pasaría sin el arreglo | Sin escenario. El crítico quita la vista (AD-84), así que no nace GRANT |
| C-32 | Los periodos históricos aparecen en la ruta 18 | F con C-40 | F con C-40 | C, el Dado necesita una fila de alcance por periodo | Escenario de US-105 |
| C-33 | La meta es el 80 % absoluto | F con C-05 | R, BR-RESULTADOS-06 y 14 ya la fijan | S, `en_meta()` compara con mayor o igual | Escenario de US-101 |
| C-34 | Promedio exacto con numeric | F con C-03 | R, ya es decisión SE_SOSTIENE de la spec 009 | F con C-03, la ruta lleva el número 2.7 y P9 escribe «2,70» | Escenarios de US-100 y US-101 |
| C-35 | El conciliador compara la evolución | M, la conciliación real espera los R-17 históricos (H34) y D-56 | R, basta correrlo una vez por periodo | C, `--periodo` es un solo valor | Sale por dos lentes. El ensayo corre el conciliador por periodo (US-107) |
| C-36 | El estadío agrupa y no cambia el nivel esperado | F, D-38 ya fija un solo nivel | F con C-26 | S, un solo NIVEL_ESPERADO por conjunto | Escenario de US-102 |
| C-37 | Contrato y ADR antes del código | R, es una tarea del plan | F con C-21 y C-26, como tareas | S, los documentos existen en el Front | Tareas T011 y T012 |

### Ángulo 3. Los datos inventados de la demostración

| Candidata | Título | Necesidad | Solapamiento y tamaño | Verificabilidad | Destino |
| --- | --- | --- | --- | --- | --- |
| C-40 | Semilla de periodos anteriores de Química | S, el pedido dice «si falta data, genera data» | S, ningún archivo de `db/datos/` cubre 2025 | S, las restricciones existen y el seco repite `plan_quimica_2026_1.sql` | US-105, con la ficción del catálogo solo en la rama y el clúster (J-75) |
| C-41 | Exports inventados reproducibles por periodo | S, recorre el flujo real con datos inventados | S, extiende `generar_exports_desde_maestra.py` y `ensayar_capacitacion.py` | S, el generador ya escribe bytes fijos | US-107, con una sola fuente, la tabla maestra inventada (AD-96) |
| C-42 | Rango propio de códigos 99 | F con C-41 | F con C-41 | C, los dos escenarios chocan si la guardia corre antes de cada carga | Escenario de US-107, con la comprobación una sola vez (AD-101) |
| C-43 | Las cargas siguen el flujo normal | S, es lo que muestra el sistema de punta a punta | F con C-41 | C, el ensayo toma un solo PI del manifiesto, así que Ambiental pide extenderlo | US-107 |
| C-44 | Semilla de Ambiental en los tres estadíos | C, falta un segundo periodo de Ambiental | S, P10 necesita tres columnas con datos | C, la 413 en lugar de la 410 y un profesor por sección | US-106, con 2024-2 como segundo periodo (J-75) |
| C-45 | Varios PI por export | F con C-41 | F con C-41 | F con C-41, `ck_carga_columna_encabezado` acepta «5.1 [» | Escenario de US-107 |
| C-46 | El catálogo no cambia con la demostración | F con C-40 y C-44 | F con C-40 y C-44 | C, la huella está en `db/plataforma/neon/` y sus partes 7 a 13 cambian por fuerza | Escenario de US-105, con las partes 1 a 6 de la huella |
| C-47 | Siembra en Neon desde el Windows | S, la demostración debe verse en la vista previa | C, en una rama de Neon aparte y con su J | C, la rama la fija `--rama` y las consultas de control son las de `controles_neon.sql` | US-108, en la rama `demo-011` (J-72) |
| C-48 | La demostración no se mezcla con datos reales | C, pasa a ser la decisión de dónde vive la demostración | F con C-47 | C, el discriminador es el prefijo SINTETICO_ y no un código real | Escenario de US-108 y J-72 |
| C-49 | Retiro de la demostración | R, nada lo pide | R, con la rama aparte se borra la rama | C, el orden de borrado sigue las FK | REFUTADA. El retiro es borrar la rama (AD-100) |
| C-50 | Humo de P9 y P10 en un clúster desechable | F con C-01 y C-09 | F, es tarea `[Front]` | C, `api_local.sh` suma las semillas y cargas y no se usa `api_simulada.ts` | Tareas T025 y T045 |
| C-51 | Oráculo de cifras escrito a mano | F con C-41 | F con C-41 | S, `tests/datos_inventados/README.md` ya documenta cifras a mano | Escenario de US-107 |
| C-52 | Cuenta de demostración de Ambiental | F con C-44 | R, `coordinacion@example.invalid` ya existe | C, se reutiliza esa cuenta | US-106 reutiliza `coordinacion@example.invalid` |
| C-53 | Volver a cargar no duplica | F con C-43 | R, la negativa del ensayo ya lo impide | S, la segunda corrida deja 6 de 10 | Escenario de US-107 |
| C-54 | Guía corta de la demostración | F con C-47 | F con C-47, es documentación | S, `db/README.md:442` | Parte de la tarea T024 |

### Ángulo 4. Acceso, privacidad y evidencia

| Candidata | Título | Necesidad | Solapamiento y tamaño | Verificabilidad | Destino |
| --- | --- | --- | --- | --- | --- |
| C-60 | Ningún profesor en P9, P10 ni en sus rutas | S, D-57 y BR-RESULTADOS-10 | F con C-21 y C-26 | S, «Profesor Inventado Setecientos Uno» sirve de prueba | Escenarios de US-100 a US-103 |
| C-61 | Sin orden por resultado | S, el tablero ordena por valor | F con C-01 y C-09 | S, los órdenes por periodo, número y código son fijos | Escenarios de US-100 a US-103 |
| C-62 | Solo la coordinación | S, D-33 | F con C-21 y C-26 | S, `SOLO_COORDINACION` existe | Escenarios de US-100 a US-104 |
| C-63 | La coordinación del curso ve solo sus periodos | F con C-62 | F con C-21 | S, `_ALCANCE` une la fila por periodo | Escenario de US-100 |
| C-64 | La coordinación de un curso no ve la matriz | F con C-62 | F con C-26 | S, `alcance_de()` distingue CURSO de CARRERA | Escenarios de US-102 y US-103 |
| C-65 | Sin datos de estudiantes en las respuestas | F con C-60 | F con C-21 y C-26 | S, ninguna consulta lee `abet.estudiante` | Escenarios de US-100 y US-102 |
| C-66 | Celda con muy pocos calificados | R, nada lo pide y P8 no suprime celdas | M, crearía cifras distintas de P8 para la misma sección | C, el umbral pide número | Sale por dos lentes, a «Fuera de alcance» |
| C-67 | Aviso de datos de demostración | R, con la rama aparte no hay mezcla | M, solapa con la franja provisional | S | Sale por dos lentes, a «Fuera de alcance» |
| C-68 | Barrido de privacidad de semillas y exports | F con C-40 | F con C-40 y C-44 | C, el barrido cubre lo que git rastrea y los exports se revisan en `tests/test_generador_exports.py` | Escenarios de US-105 y US-106 |
| C-69 | Nada del tablero entra al repositorio | R, AGENTS.md y D-56 ya lo fijan | R, sin comportamiento verificable | C, la prueba sería que git no rastrea `.pbix` | Sale por dos lentes. Queda como restricción de la spec |
| C-70 | Teclado, lector de pantalla y 375 px | F con C-01 | F con C-01 y C-09 | S, P9 y P10 entran a `PANTALLAS` | Escenarios de US-101 y US-103 |
| C-71 | Evidencia de cierre | R, es el cierre de toda spec | R, no es historia | S | Sale por dos lentes. Es la tarea T051 |
| C-72 | La demostración no llega a producción sin permiso | F con C-47 | F con C-47 | F con C-47, `--rama principal` pide `--confirmo-principal` | Escenario de US-108 |

## Veredicto del crítico de arquitectura

| ID | Decisión | Veredicto | Razón | Alternativa que adopta la spec |
| --- | --- | --- | --- | --- |
| AD-83 | La evolución sale de una consulta sobre `abet.v_r17_por_pi` sin vista nueva (C-20) | SE_SOSTIENE | La vista ya trae periodo, asignatura, sección, meta y conteos | `resumen_del_curso()` una vez por periodo visible, sin copiar la suma ni el trato de metas |
| AD-84 | El cruce con la competencia y el estadío va en una vista R__ nueva (C-26 y C-31) | CAMBIAR | `abet_app` ya lee las tablas de competencias, y una vista nueva obliga a tocar el callback de permisos | Consulta en `resultados.py` que une la vista con `carga`, `seccion`, `plan_medicion` y `pi` dentro de la versión del plan. Vista solo si Power BI la pide, con su decisión (J-74) |
| AD-85 | La unión toma `competencia_so` por SO y `asignatura_competencia` por versión, asignatura y competencia | SE_SOSTIENE | La PK de `competencia_so` admite un SO con varias competencias | La unión iguala también `catalogo_version_id` en `competencia_so`, y ninguna pantalla suma filas de competencias distintas |
| AD-86 | 5643 de Industrial queda fuera de E3 de Ambiental por la versión del plan (C-28) | SE_SOSTIENE | IND-2026 tiene 0 filas en `asignatura_competencia` | La unión por `plan_medicion.catalogo_version_id`, sin regla especial |
| AD-87 | Ruta 22 nueva en lugar de un modo de varios periodos en la ruta 20 (C-21) | SE_SOSTIENE | La ruta 20 tiene un contrato por periodo y P8 se vuelve a montar con el periodo | Ruta 22 con el objeto de la §16.2 por periodo y un solo nombre, `/api/resumen-curso/evolucion` (J-73) |
| AD-88 | La ruta 22 recorre `periodos_visibles()` y `secciones_visibles()` por periodo (C-63) | SE_SOSTIENE | Respeta la fila de alcance por periodo (J-49) y el costo es bajo con pocos periodos | Una sola consulta con `periodo = ANY(...)` solo si la latencia en Neon lo exige |
| AD-89 | El selector de curso de P9 sale de una variante de la ruta 21 sin periodo (C-06) | DUDOSA | Una variante sin periodo es un cambio de contrato que la demostración no necesita | La ruta 21 del periodo de la cabecera y la asignatura del fragmento, como en P8 |
| AD-90 | La evolución va en una pantalla nueva P9 (C-01 y C-07) | SE_SOSTIENE | P8 depende del periodo de la cabecera y P9 lo ignora | P9 con `key` por asignatura y fragmento `#/evolucion?asignatura=` |
| AD-91 | Las competencias van en una pantalla nueva P10 (C-09) | SE_SOSTIENE | Su alcance es la carrera y su unidad es la medición | Ninguna |
| AD-92 | La evolución de una competencia va en P10 o en P9 (C-12) | DUDOSA | Con un solo periodo de Ambiental la serie tiene un punto | Solo en P10 y con un segundo periodo sembrado de Ambiental (J-75) |
| AD-93 | Pulsar un periodo de P9 abre P8 en ese periodo (C-08) | SE_SOSTIENE | Equivale al drillthrough | Sin efecto, porque C-08 sale por dos lentes |
| AD-94 | Los datos de Química salen de tablas maestras inventadas, del generador y del ensayo | SE_SOSTIENE | 5643 mide un solo PI y el ensayo recorre lector, meta, R-17 y conciliador | Una corrida del ensayo por periodo |
| AD-95 | Ninguna medición entra por INSERT directo (C-43) | SE_SOSTIENE | Solo `cargar()` prueba el sistema de punta a punta | Ninguna |
| AD-96 | Un guion nuevo arma los exports desde una semilla fija (C-41) | CAMBIAR | Dos generadores de `.xlsx` dejan dos caminos para la misma demostración | Una sola fuente, las tablas maestras inventadas, con el generador existente y salida fuera del repositorio |
| AD-97 | El generador acepta varios PI por sección (C-45) | SE_SOSTIENE | 6511, 450002 y 5674 miden varios PI | `--pi` como lista en `generar_exports_desde_maestra.py` |
| AD-98 | El histórico usa `tipo_fuente` R17_HISTORICO | CAMBIAR | Los archivos son exports inventados con formato de Blackboard y H34 no tiene lector | BLACKBOARD_EXPORT, y R17_HISTORICO queda para el lector de H34 |
| AD-99 | La siembra y las cargas van a develop de Neon (C-47 y C-48) | CAMBIAR | develop tiene 18 secciones de 5643 en 2026-1 con cargas, el ensayo se niega ante cargas del curso y J-52 pide una base aparte | Rama de Neon aparte creada desde develop, sembrada desde el Windows, y una vista previa que apunta a ella con el permiso de Jefferson (J-72) |
| AD-100 | Un guion de retiro borra en orden de clave foránea (foreign key, FK) (C-49) | CAMBIAR | Un DELETE selectivo en una base compartida es la operación más riesgosa | Borrar la rama de Neon |
| AD-101 | Rango propio de códigos con una guardia ante cada carga (C-42 y C-53) | CAMBIAR | La carga de 2025-1 detendría la de 2025-2 | Comprobar el rango una vez al iniciar y dejar la idempotencia a `uq_archivo_origen_sha256` y al ensayo |
| AD-102 | La vigencia de IND-2026 se extiende a 2025-1 y 2025-2 (C-40) | DUDOSA | Es una ficción del catálogo que ocupa el par carrera y periodo del catálogo real de 2025 | Solo en la rama de la demostración y en el clúster desechable, declarado en la semilla (J-75) |
| AD-103 | Ambiental se siembra con 6511, 450002 y 5674 en 2026-2 (C-44) | SE_SOSTIENE | Los planes respetan `fk_plan_medicion_asig_so` | La misma semilla suma los profesores inventados y reutiliza la cuenta de la coordinación |
| AD-104 | La cifra por competencia suma mediciones y no promedia porcentajes (C-22 y C-27) | SE_SOSTIENE | Cumple BR-RESULTADOS-13 y el invariante 1 del registro de decisión de arquitectura (Architecture Decision Record, ADR) 010 | Rótulo «mediciones» con la franja provisional mientras D-32 siga abierta |
| AD-105 | El estadío solo agrupa (C-36) | SE_SOSTIENE | NIVEL_ESPERADO es uno por conjunto | Ninguna |
| AD-106 | Promedio de nivel por periodo calculado desde los conteos (C-03 y C-34) | DUDOSA | Promediar una escala ordinal agrega una cifra que ninguna regla define | Se mantiene, porque la spec 009 ya lo publica en la ruta 20 y la ruta 22 reutiliza ese objeto. Su definición sigue en D-56 |
| AD-107 | P10 no lleva radar | SE_SOSTIENE | J-24 descarta bibliotecas y un radar dibujaría ceros en G1, G2, G5 y G7 | Matriz de competencia por estadío con barras HTML y la cifra escrita |
| AD-108 | P9 dibuja una barra por periodo en lugar de una polilínea | SE_SOSTIENE | Una polilínea sugiere continuidad entre periodos sin carga | `BarraDelCurso` y `LineaDeMeta` por periodo |
| AD-109 | Los periodos van por año y ciclo (C-24) | SE_SOSTIENE | `periodos_visibles()` ya ordena así | El periodo 2025-0 solo en la prueba |
| AD-110 | La sección no forma una serie entre periodos (C-25) | SE_SOSTIENE | `uq_seccion` identifica la sección por periodo | Ninguna |
| AD-111 | La meta y el nivel esperado se resuelven dentro de cada periodo (C-23) | SE_SOSTIENE | La regla de `resultados.py:111-128` ya vacía la meta si difiere | La misma regla por periodo, sin copiarla |
| AD-112 | Ruta 23 `GET /api/competencias?periodo=&carrera=` (C-30 y C-64) | CAMBIAR | Recibir la carrera por parámetro abre el caso de una carrera ajena | `GET /api/resumen-carrera/competencias?periodo=`, con la carrera tomada del alcance y un parámetro opcional solo para una cuenta con varias carreras |
| AD-113 | Una celda con menos de 3 calificados va sin porcentaje (C-66) | DUDOSA | P8 no aplica ese umbral | Sin efecto, porque C-66 sale por dos lentes |
| AD-114 | Una clave booleana avisa los datos de demostración (C-67) | CAMBIAR | Acopla el contrato a una convención de nombres | Sin efecto en esta spec, porque C-67 sale por dos lentes. Un aviso por entorno en la vista previa queda en «Fuera de alcance» |
| AD-115 | El conciliador acepta varios periodos (C-35) | DUDOSA | El ensayo ya lo corre por periodo | Correr el ensayo por periodo sin tocar el conciliador |
| AD-116 | Las cifras esperadas viven en un oráculo a mano (C-51) | SE_SOSTIENE | Evita comparar el sistema consigo mismo | Ninguna |
| AD-117 | Los humos corren en un clúster desechable (C-50) | SE_SOSTIENE | El clúster de localhost:5432 aloja bases de otros proyectos | Ninguna |
| AD-118 | Los periodos antiguos aparecen en la ruta 18 solo con secciones (C-32) | SE_SOSTIENE | Es la §15.2 del contrato | Ninguna |
| AD-119 | La §17 del contrato y ADR-011 antes del código (C-37) | SE_SOSTIENE | ADR-010 y la §16.4 dejan fuera las vistas por profesor | Ninguna |

## Hechos del código que corrigen supuestos de las candidatas

- La coordinación de una carrera ve una sección si su carrera tiene vigencia en ese periodo y la asignatura está en su plan de estudios (`_ALCANCE` de `app/permisos.py`). 5643 está en el plan de estudios de AMB-2026 (`V1_03:125`), así que una vigencia de AMB en 2025-1, 2025-2 o 2026-1, que son los periodos con secciones de 5643, deja a `coordinacion@example.invalid` ver Química General. Por eso el segundo periodo de Ambiental es 2024-2, que crea la semilla, y no el 2025-2 que propone la lente de verificabilidad para C-12 (J-75).
- La 410 de 450002 en 2026-2 ya tiene una carga de 11 estudiantes en `db/pruebas/datos_sinteticos.sql`, así que la demostración usa la 413, libre en `db`, `tests` y `scripts`. La base de los escenarios no carga ese archivo, pero sí trae la 410 y la 411 de 450002 de `periodo_2026_2_inventado.sql` y la 412 de 450002 y la 410 y la 412 de 450010 de `varias_secciones_2026_2_inventado.sql`, todas sin carga, que `scripts/api_local.sh` carga hoy (corrección del 2026-11-25).
- `abet.v_r17_por_pi` no expone `so_id`, `pi_id` ni `catalogo_version_id`, y `uq_pi_codigo` repite «5.1» entre versiones, así que la consulta de competencias toma la versión desde `plan_medicion`.
- `ensayar_capacitacion.py` toma del manifiesto un periodo, una asignatura y un PI, exige una base aparte por host y nombre (J-52) y se niega si la base ya tiene cargas de la asignatura en el periodo. `conciliar_tabla_maestra.py` toma un solo `--pi`.
- `sembrar_quimica.py` elige la rama con `--rama develop|principal`, y con `--rama principal --aplicar` sin `--confirmo-principal` termina con 2 antes de conectarse. La rama no se detecta por la conexión.
- `cifra()` convierte `promedio_nivel` en un número JSON, así que la ruta lleva 2.7 y P9 escribe «2,70».
- La huella de Ambiental vive en `db/plataforma/neon/huella_ambiental.sql`, y sus partes 7 a 13 (vigencias, plan de medición, secciones, cargas, mediciones y rechazos) cambian por fuerza con cualquier siembra.
- `coordinacion@example.invalid` ya tiene la fila de la carrera AMB en `periodo_2026_2_inventado.sql`, y `api_local.sh` le asigna una contraseña.
- Toda respuesta de `/api` ya lleva `Cache-Control: no-store` (`app/main.py`).
- Las competencias de AMB-2026 son de tipo GENERICA (G1 a G8) o ESPECIFICA (E1 a E3), con `ck_competencia_codigo`.

## Faltantes que la spec cubre

- Una tabla de equivalencias de cada visual de las dos páginas con P9 y P10, con lo que se omite y por qué.
- El orden cronológico de los periodos, en lugar del orden por valor de los gráficos del tablero.
- La regla de la meta absoluta, en lugar del color relativo al rango de la tabla del tablero.
- La unidad «mediciones» de P10 frente a los «alumnos» de P8 y P9.
- La negativa de la siembra ante un periodo con cargas de secciones sin el prefijo SINTETICO_.

## Lista final del sprint

| Historia | Prioridad | Candidatas | Estimación |
| --- | --- | --- | --- |
| US-100 La coordinación recibe la evolución del curso en la ruta 22 | P1 | C-21, C-20, C-02, C-03, C-04, C-16, C-22, C-23, C-24, C-25, C-34, C-60, C-61, C-62, C-63 y C-65 | 4 h |
| US-101 P9 muestra la evolución del curso | P1 | C-01, C-02, C-04, C-05, C-06, C-07, C-14, C-15, C-25, C-33, C-61, C-62 y C-70 | 7 h |
| US-102 La coordinación de la carrera recibe el logro por competencia y estadío en la ruta 23 | P1 | C-26, C-10, C-11, C-13, C-27, C-28, C-29, C-30, C-36, C-60, C-62, C-64 y C-65 | 6 h |
| US-103 P10 muestra las competencias por estadío | P1 | C-09, C-10, C-11, C-13, C-15, C-27, C-29, C-61, C-64 y C-70 | 6 h |
| US-104 La coordinación de la carrera ve la evolución de una competencia | P2 | C-12 | 5 h |
| US-105 La semilla de Química suma 2025-1 y 2025-2 | P1 | C-40, C-32, C-46 y C-68 | 3 h |
| US-106 La semilla de Ambiental cubre los tres estadíos y un segundo periodo | P1 | C-44, C-46, C-52 y C-68 | 3 h |
| US-107 Las tablas maestras inventadas suben por el flujo normal de carga | P1 | C-41, C-42, C-43, C-45, C-51 y C-53 | 7 h |
| US-108 La demostración se siembra en una rama de Neon aparte desde el Windows | P1 | C-47, C-48, C-54 y C-72 | 6 h |

C-37 queda como las tareas del contrato y del ADR-011, C-50 como las tareas del humo y del clúster y C-71 como el cierre. La estimación de las historias suma unas 47 h, y con el contrato, el humo, la carga en Neon y el cierre `tasks.md` suma unas 62,5 h.

## Decisiones que salen de la revisión

- D-59 a Claudia León y a la coordinación de la carrera, si la «evolución histórica» que pide es la del curso y de sus secciones por periodo, en lugar de la del profesor.
- D-32, D-38 y D-57 siguen abiertas con el valor provisional de sus specs, y la spec dice cómo las toca. D-50 sigue en la spec 008 con Stefanny Montaño, D-56 se cierra el 2026-11-25 en la spec 009 y la falta de la «Base cursos - Nivel» de Industrial pasa a D-60, de la coordinación de Industrial (corrección del 2026-11-25).
- J-72 a J-77 a Jefferson, que la spec lista con su valor provisional.

## Correcciones del 2026-11-25

El dueño técnico revisa la spec el 2026-11-25 y fija seis decisiones como valor provisional, anotadas con fecha en las Clarifications de `spec.md`. La revisión recalcula a mano las cifras de Ambiental contra todas las secciones que la base de los escenarios trae.

| Tema | Antes | Después | Dónde |
| --- | --- | --- | --- |
| Celda de la ruta 23 | FR-005 tomaba solo las secciones con carga de la carrera, así que G4 en REFUERZO de 2026-2 traía la 413 sola, con 1 publicada y 1 en la meta | La celda toma las secciones de las asignaturas del plan de estudios con ese estadío y con un plan de un PI de un SO de la competencia en el periodo. Las que tienen carga PUBLICADA suman, y las demás, sin carga o con carga RECHAZADA, van a `sin_dato`, como en la ruta 20. G4 en REFUERZO de 2026-2 trae seis secciones (410 a 413 de 450002 y 410 y 412 de 450010) y cinco sin dato, y E2 en REFUERZO trae dos sin dato | FR-005, FR-006, FR-007, Edge Cases, «Datos inventados de la demostración», US-102, `competencias_por_estadio.feature` y `pantalla_competencias.feature` |
| Base de los escenarios | Los Antecedentes nombraban solo la semilla de Ambiental | Los Antecedentes nombran `periodo_2026_2_inventado.sql`, `varias_secciones_2026_2_inventado.sql` y la semilla, y dicen que la base no carga `db/pruebas/datos_sinteticos.sql`. T025 suma a `api_local.sh` las dos semillas de Química de la spec 008 | `competencias_por_estadio.feature`, `datos_de_demostracion.feature` y T025 |
| Sección de la respuesta | Cada sección de una celda traía `numero`, `logrados`, `calificados`, `pct_sobre_calificados` y `en_meta` | Suma `estado` (PUBLICADA o SIN_CARGA), y `conteo_secciones` nombra sus cinco claves de la ruta 20. Los `pis` de la competencia son los del plan que aporta a sus celdas | FR-006 |
| Rango de códigos | La comprobación vivía en `ensayar_capacitacion.py`, y el escenario no decía qué corrida la hacía | La comprobación vive en `sembrar_demostracion.py`, una sola vez antes de la primera carga y sobre todos los manifiestos juntos, con un control de los exports antes de conectarse y una regla de uso que deja pasar la segunda corrida. El ensayo no mira el rango | FR-013, FR-014, US-107, US-108, T023, T024 y `datos_de_demostracion.feature` |
| Siembra en `demo-011` | 2026-1 conservaba lo que develop tuviera y SC-003 pedía las celdas de 2026-2 sin condición | La siembra excluye 5643 en 2026-1. SC-003 compara las celdas de 2026-2 en `demo-011` solo si develop no tiene cargas de 450002, 6511 ni 5674 en 2026-2, y si las tiene la siembra las informa y omite su ensayo. `demo-011` hereda los datos reales de 2026-1 que D-10 autoriza, que las cuentas inventadas ya ven en develop y que ningún humo ni captura de Playwright registra | FR-014, US-108, SC-003, J-72, Clarifications, `plan.md`, T045 y T052 |
| Ruta 24 | FR-009 decía «con alcance de carrera» sin el caso CURSO ni el parámetro `carrera` | Una cuenta con alcance CURSO recibe 200 con `periodos` vacío, y la ruta acepta el parámetro opcional `carrera` con su 422. La respuesta nombra `carrera`, `competencia` y `periodos` | FR-009, Edge Cases, US-104, T032 y `competencias_por_estadio.feature` |
| D-50 y D-60 | D-50 era de la coordinación de Industrial y cubría la «Base cursos - Nivel» | D-50 vuelve a Stefanny Montaño y a las rúbricas por nivel de los PI de Industrial de la spec 008, y la «Base cursos - Nivel» pasa a D-60, de la coordinación de Industrial, con el valor provisional «P10 muestra solo Ambiental» | Input, prefijos, Clarifications, decisiones abiertas, «Fuera de alcance», T003 y esta revisión |
| D-56 | Abierta, con las fórmulas DAX por leer | Cerrada el 2026-11-25 en la spec 009, porque las medidas del tablero coinciden con el valor provisional (rama `docs/009-cierre-d56`) | Equivalencias, decisiones abiertas, J-76, «Fuera de alcance», `plan.md`, `tasks.md` y esta revisión |
| D-32 | Citaba PA-13 como su origen | Cita su origen en la spec 004 (H06 y P14), sin PA-13, que allí es solo la propuesta del SO en la meta | Decisiones abiertas y Clarifications |
| J-24 | `pantalla_evolucion_del_curso.feature` lo atribuía a ADR-008 | Lo atribuye a la spec 004, y ADR-008 y ADR-010 quedan como los registros que lo recogen | `pantalla_evolucion_del_curso.feature` y la tabla de equivalencias |

Cifras del oráculo de Ambiental, recalculadas a mano con 5 estudiantes por carga y ninguno sin evidencia.

| Periodo | Celda | Mediciones por nivel | Con 3 o 4 | % | Promedio | Conteo de secciones (total, publicadas, en la meta, debajo, sin dato) |
| --- | --- | --- | --- | --- | --- | --- |
| 2024-2 | G4 en REFUERZO | [1, 5, 6, 3] | 9 de 15 | 60,0 | 41 / 15 = 2,73 | 1, 1, 0, 1, 0 |
| 2026-2 | G4 en INICIAL | [0, 2, 2, 1] | 3 de 5 | 60,0 | 14 / 5 = 2,80 | 1, 1, 0, 1, 0 |
| 2026-2 | G4 en REFUERZO | [1, 2, 7, 5] | 12 de 15 | 80,0 | 46 / 15 = 3,07 | 6, 1, 1, 0, 5 |
| 2026-2 | G4 en LOGRADO | [0, 1, 5, 4] | 9 de 10 | 90,0 | 33 / 10 = 3,30 | 1, 1, 1, 0, 0 |
| 2026-2 | G3 en INICIAL | [1, 2, 1, 1] | 2 de 5 | 40,0 | 12 / 5 = 2,40 | 1, 1, 0, 1, 0 |
| 2026-2 | E2 en REFUERZO | [0, 0, 0, 0] | 0 de 0 | null | null | 2, 0, 0, 0, 2 |

Los porcentajes y los promedios que la spec ya daba no cambian. Cambian el conteo de secciones de G4 en REFUERZO de 2026-2, de 1 a 6 con 5 sin dato, y la celda de E2 en REFUERZO, que antes no figuraba. Los niveles por PI de 2024-2, de 6511 y de 5674 son nuevos y salen de la tabla por PI de `spec.md`. Las cifras de Química no cambian, porque la base de los escenarios no trae otras secciones de 5643 en 2025-1, 2025-2 ni 2026-1.

Lo que queda abierto para la aprobación.

- La decisión de la siembra habla de las cargas «de esas secciones», y `ensayar_capacitacion.py` se niega por asignatura y periodo, así que la spec condiciona SC-003 a las cargas de 450002, 6511 y 5674 en 2026-2 y no solo a las de la 413 y las dos 401.
- La regla de uso del rango, que deja pasar a los estudiantes que solo tienen mediciones de las cargas de la demostración, es propia de esta revisión y no del dueño técnico. Sin ella, la segunda corrida de la siembra se detendría por sus propias cargas.
- La clave `estado` de cada sección de la ruta 23 y las claves `carrera`, `competencia` y `periodos` de la ruta 24 son propuestas de esta revisión para que la lista cerrada cuadre con la ruta 20 y con el caso CURSO.
- `test_lectura_gherkin_es.py` todavía no lee los cinco `.feature` de esta spec, y su registro en esa prueba queda para la implementación, después de la aprobación de la spec. Una lectura aparte con el analizador de pytest-bdd 9 los lee sin errores.

## Segunda revisión del 2026-11-25

La revisión independiente que sigue a las correcciones recalcula a mano el oráculo de Química y de Ambiental y no encuentra diferencias. Corrige seis puntos en los archivos de la spec, que son el nivel de la 701 de 2026-1 en el escenario de E3, la ruta 21 de 2026-2 con 450010 en el selector de P9, la atribución de J-24 en `pantalla_competencias.feature`, la descripción de `ensayar_capacitacion.py` en `plan.md`, las asignaturas de G3 en REFUERZO (450006, 450009 y 560046) y la cuenta `coordinador.quimica@example.invalid` en T025. Deja tres puntos que el dueño técnico decide el mismo día y que la sesión de Clarifications registra, que son la negativa de la siembra por periodo creado o existente, el orden de `api_local.sh` con `DESCRIPCION_INSTRUMENTO` y la segunda corrida del ensayo, que termina con 1 por CON_CARGAS. Siguen como propuestas de la revisión la regla de uso del rango, la clave `estado` de la ruta 23 y las claves `carrera`, `competencia` y `periodos` de la ruta 24, y el registro de los `.feature` de la spec 011 en `test_lectura_gherkin_es.py` queda para la implementación.
