# Feature Specification: El export real de Blackboard en .xlsx, .csv y .xls

**Feature Branch**: `docs/003-exports-blackboard` (PR a `develop`), con la implementación en `feat/003-exports-blackboard` del Back y del Front
**Created**: 2026-11-09
**Status**: Aprobada por Jefferson en el chat el 2026-11-09 («Apruebo»), con las decisiones de la sesión de abajo
**Input**: «que ABET-ULIMA-Back cargue los exports reales de Blackboard en tres formatos: .xlsx, .csv (texto UTF-8 con BOM, separado por comas y con comillas) y el .xls de Blackboard (texto UTF-16 LE con BOM, separado por tabuladores, que no es Excel). También debe reconocer las columnas de PI con los encabezados reales, como «ABET SO5.1 [Total Pts: 100 Score] |1629477» y «ABET SO 5.3 […]». Hoy no los reconoce: abet_carga/lector.py:263 exige que el encabezado empiece con «N.N [», así que tampoco se carga un .xlsx real.» (pedido de la sesión del plan del 2026-11-09, sobre los exports reales que Jefferson descarga de Blackboard el 2026-11-04).

## Épica

> **EP-03. El profesor sube el export tal como lo descarga de Blackboard.** Hoy la interfaz de programación de aplicaciones (application programming interface, API) admite solo el `.xlsx` y reconoce una columna de indicador de desempeño (performance indicator, PI) solo si su encabezado empieza por «5.1 [». El export real de la sección 410 de 450002 llega en `.csv` (texto UTF-8 con marca de orden de bytes, byte order mark, BOM), en `.xls` (texto UTF-16 LE con BOM y tabuladores, que no es un libro de Excel) o en `.xlsx`, y sus columnas se llaman «ABET SO5.1 [Total Pts: 100 Score] |1629477» o «ABET SO 5.3 [Total Pts: 100 Score] |1635606». El `.csv` y el `.xls` reciben 422 por su extensión, y el `.xlsx` queda RECHAZADO con PI_DEL_PLAN_AUSENTE aunque trae las columnas. Si el lector las reconociera, la base rechazaría el encabezado con `ck_carga_columna_encabezado` y la carga respondería 500. Esta épica deja que el profesor suba el archivo que descarga, sin abrirlo ni convertirlo, con los controles de privacidad y de evidencia de la spec 001.

Convenciones de esta spec. Todos los datos son inventados y siguen las convenciones de la spec 001. La sección de prueba es la 410 de 450002 «Principios de Ingeniería Sostenible» en 2026-2, con los PI 5.1, 5.2 y 5.3 del resultado del estudiante (student outcome, SO) 5 en su plan de medición, los códigos 99000001 a 99000011 y los niveles de `db/pruebas/datos_sinteticos.sql`, y la 411 usa los códigos 99000012 a 99000022 con los mismos niveles en orden inverso. Nadie abre ni copia los exports reales que Jefferson guarda en `~/Downloads`, que traen nombres y códigos de estudiantes. De esos exports esta spec toma solo la forma, que describe la nota de análisis del 2026-11-09, es decir, los 31 encabezados, el orden de las columnas, la codificación, el separador, las comillas y el nombre del archivo `gc_<curso_blackboard>_fullgc_<fecha y hora>.<extensión>`. Los encabezados son nombres de actividades del curso y no traen datos de personas.

Prefijos e identificadores. La épica lleva el prefijo EP y continúa la numeración de las specs 001 (EP-01) y 002 (EP-02). Las historias US continúan desde US-26, porque la spec 002 de la rama `docs/002-capstone` usa US-22 a US-25, y las decisiones abiertas siguen desde D-30 y J-18 por la misma razón. Los requisitos funcionales FR (functional requirement), los criterios de éxito SC (success criterion) y las tareas T se numeran dentro de esta spec, como en la 002, así que una regla viva que cite uno de ellos nombra la spec, como «FR-003 de la spec 003». Las candidatas de la auditoría se llaman C-01 a C-15, con letra cuando una se parte, y F-NN es una historia que falta según un informe de auditoría. Lo que el redactor decide sin fuente va marcado «(propuesta)», y lo que no existe en V1_01 a V1_09 va marcado «(V1_10)».

Siglas y términos. Las de la spec 001 valen aquí. CSV es el formato de valores separados por comas (comma-separated values), UTF-8 y UTF-16 son las codificaciones Unicode de 8 y de 16 bits, LE es el orden de bytes de menor a mayor (little endian), OLE es el contenedor de vinculación e incrustación de objetos (Object Linking and Embedding) de los libros de Excel 97-2003 y de los libros cifrados, CRLF y LF son los saltos de línea de Windows y de Unix, y SO es el resultado del estudiante. Un export de texto es el `.csv` o el `.xls` de Blackboard, que no tienen hoja, y un libro es un `.xlsx`.

Cifras de prueba, comprobadas contra `db/pruebas/datos_sinteticos.sql`. Los cuatro archivos nuevos los genera `scripts/generar_exports_inventados.py` con los 31 encabezados reales, Student ID vacío, «Complete», «Incomplete», «Needs Grading» y «19.00» en las actividades y las columnas «ABET SO 4.1» y «ABET SO4.2» vacías.

| Archivo de `tests/datos_inventados/` (por crear) | Formato | Filas de datos / leídas / aceptadas / rechazadas | Mediciones | R-17 (5.1, 5.2, 5.3) | Filas en `rechazo_fila` |
| --- | --- | --- | --- | --- | --- |
| `gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv` | UTF-8 con BOM, comas, comillas dobles y saltos LF; niveles escritos «3.00» | 11 / 11 / 11 / 0 | 33 | 63,6 % (7 de 11), 63,6 % (7 de 11), 72,7 % (8 de 11) | 5 avisos, PUNTAJE_MAXIMO_DISTINTO en 5.1, 5.2 y 5.3 (100 puntos) y COLUMNA_PI_FUERA_DEL_PLAN en 4.1 y 4.2 |
| `gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls` | UTF-16 LE con BOM, tabuladores, comillas dobles y saltos LF; niveles escritos «3.00» | 11 / 11 / 11 / 0 | 33 | las mismas | los mismos 5 avisos |
| `gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-36-02.xlsx` | libro con la hoja `gc_SINTETICO_20262_450002_410_f` y niveles numéricos | 11 / 11 / 11 / 0 | 33 | las mismas | los mismos 5 avisos |
| `gc_SINTETICO_20262_450002_411_fullgc_2026-11-04-14-40-10.xls` | como el `.xls` de la 410, con los códigos 99000012 a 99000022 | 11 / 11 / 11 / 0 | 33 | las mismas | los mismos 5 avisos |

Los escenarios de esta spec viven en `specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`, en español (`# language: es`), y sus pasos en `tests/aceptacion/pasos/test_exports_blackboard_feature.py`, que reutiliza los Antecedentes y los pasos comunes de `tests/aceptacion/pasos/conftest.py`. Cada escenario lleva `@US-NN`, `@corte1` (el principio V de la constitución) y `@spec003`. Cuando un texto literal de pantalla o de la API difiere, manda el del `.feature`.

## Clarifications

### Session 2026-11-09

- Jefferson responde en el chat las cuatro primeras preguntas de la auditoría. Sobre los formatos dice «Se supone que el sistema debería poder recibir cualquiera de los dos», es decir, el `.csv` y el `.xls` de Blackboard, y la spec aplica J-18 con el contenido como criterio y sin motivo propio para el libro binario de Excel 97-2003, que Blackboard no produce. Sobre los encabezados dice «el sistema debe tener la capacidad de leer ABET SO5.3 o ABET SO 5.3 como lo mismo», y la spec aplica J-19 con «ABET», «SO» y «PI» opcionales. PI_REPETIDO queda solo para el error poco común de dos columnas del mismo PI en un archivo.
- Elige «Decimales nulos; Needs rechaza» (D-03), «Rechazar la carga» para el export sin niveles (D-31), «Pedir el nombre original» para el export de texto sin sección (D-02), «Sí, 5 000 filas» (J-20) y «Títulos reales, ids inventados» para los datos de prueba, y aprueba la spec («Apruebo»).
- Los datos inventados nuevos copian los títulos de las actividades del export real, que no traen datos de personas, y cambian los números de columna de Blackboard por números inventados que empiezan con 9, como los de la spec 001.

## User Scenarios & Testing *(mandatory)*

### US-26: Reconocer las columnas de PI con sus encabezados reales, en el lector y en la base (Priority: P1)

Como profesor, quiero que el sistema reconozca «ABET SO5.1 [Total Pts: 100 Score] |9000051» y «ABET SO 5.3 [Total Pts: 100 Score] |9000053» como las columnas de los PI 5.1 y 5.3 para que mi export real no quede RECHAZADO por PI_DEL_PLAN_AUSENTE.

**Why this priority**: es el bloqueo que más pesa, porque sin él el export real no se carga en ningún formato, ni siquiera en `.xlsx`, y el lector y la base tienen que cambiar juntos para que la carga no termine en 500.

**Independent Test**: el `.xlsx` inventado con los encabezados reales deja una carga PUBLICADA con 11 / 11 / 0, 3 filas en `carga_columna` con su encabezado tal como viene y los 5 avisos, mientras el código de `develop` 37f4d72 la deja RECHAZADA con PI_DEL_PLAN_AUSENTE del PI 5.1.

**Base**: `carga_columna` (`encabezado` tal como viene, `pi_codigo`, `bb_columna_id`, `puntaje_maximo_declarado` 100.00, `uq_carga_columna_pi`, `fk_carga_columna_plan` y `ck_carga_columna_encabezado`, que V1_10 reemplaza); `V1_10__encabezado_pi_con_prefijo.sql` (V1_10); `rechazo_fila` (PI_REPETIDO con `pi_id`, COLUMNA_PI_FUERA_DEL_PLAN con `pi_id` y `carga_columna_id` nulos, PUNTAJE_MAXIMO_DISTINTO con `carga_columna_id`, `ck_rechazo_fila_pi`); casos nuevos de `db/pruebas/pruebas.sql` junto a R26.
**Pantalla**: P4 Resultado de la carga.

**Acceptance Scenarios** (`specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`):

1. **El .xlsx con los encabezados reales queda publicado.** **Dado** la 410 sin cargas, **Cuando** el profesor sube `gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-36-02.xlsx`, **Entonces** la carga queda PUBLICADA con 11 / 11 / 0 y 33 mediciones, `carga_columna` guarda para 5.1 el encabezado «ABET SO5.1 [Total Pts: 100 Score] |9000051», `bb_columna_id` 9000051 y `puntaje_maximo_declarado` 100.00, y `rechazo_fila` tiene los 5 avisos.
2. **Los exports de la spec 001 dan las mismas cifras.** **Dado** el lector nuevo, **Cuando** el profesor sube `sintetico_20262_450002_410.xlsx` y, en otra base, `export_inventado_410_con_error.xlsx`, **Entonces** quedan con 11 / 11 / 0 y 63,6 / 63,6 / 72,7 % y con 11 / 10 / 1 y 60,0 / 60,0 / 70,0 %, como en la spec 001.
3. **Qué encabezados son de un PI (esquema).** **Dado** cada encabezado de la lista común de casos, **Cuando** el lector lo clasifica, **Entonces** «ABET SO5.1 [», «ABET SO 5.3 [», «abet so 5.2 [» y «5.1[» dan su PI, «ABET SO 5.10 [» da el PI 5.10 y nunca el 5.1, y «ABET SO5 [», «Actividad 5.1 [», «9. Casos de Circularidad [» y «7. Ejercicio en clase: Conceptos y Métricas LCA (10 ejercicios) [» quedan como columnas que no son de PI.
4. **La base acepta o rechaza el encabezado de la columna del PI 5.1 (esquema).** **Dado** la carga sintética de la 410 en una base desechable migrada hasta V1_10, **Cuando** se actualiza el encabezado de su columna del PI 5.1, como en R26, **Entonces** la base acepta las escrituras de J-19 y rechaza con SQLSTATE 23514 y `ck_carga_columna_encabezado` «ABET SO 5.10 [», «5.10 [» y «Actividad 5.1 [».
5. **El lector y la base aceptan los mismos encabezados.** **Dado** la lista común de casos, **Cuando** se compara la clasificación del lector con `ck_carga_columna_encabezado` en la base desechable, **Entonces** cada encabezado que el lector clasifica como PI del plan entra en la base y cada uno que rechaza no entra.
6. **Dos columnas del mismo PI con distinta escritura rechazan la carga.** **Dado** una copia del `.csv` inventado de la 410 con una segunda columna «ABET SO 5.1 [Total Pts: 100 Score] |9000061», **Cuando** el profesor la sube, **Entonces** la carga queda RECHAZADA con 0 / 0 / 0, el mensaje «El PI 5.1 aparece en dos columnas del archivo.» y 1 fila en `rechazo_fila`, PI_REPETIDO con RECHAZA_CARGA y el `pi_id` del PI 5.1.
7. **Las columnas del SO 4 se ignoran con aviso y sin leer sus valores.** **Dado** una copia del `.csv` inventado con 75 en «ABET SO 4.1» y «Needs Grading» en «ABET SO4.2» de la fila 3, **Cuando** el profesor la sube, **Entonces** la carga queda PUBLICADA con 11 / 11 / 0, `rechazo_fila` tiene 2 avisos COLUMNA_PI_FUERA_DEL_PLAN con `pi_id`, `carga_columna_id` y `fila_origen` nulos, y `carga_columna` no tiene filas de 4.1 ni de 4.2.

---

### US-27: Cargar el .csv de Blackboard tal como se descarga (Priority: P1)

Como profesor, quiero subir el `.csv` que descargo de Blackboard, sin abrirlo ni convertirlo, para que mis niveles lleguen a la base igual que con el `.xlsx`.

**Why this priority**: es el primer formato que nombra el pedido, y hoy recibe 422 por su extensión antes de que el lector mire su contenido.

**Independent Test**: el `.csv` inventado de la 410 deja una carga PUBLICADA con 11 / 11 / 0, 33 mediciones, 63,6 / 63,6 / 72,7 en `pct_logro_sobre_calificados`, los 5 avisos y `archivo_origen.hoja` nula.

**Base**: `archivo_origen` (`hoja` NULL, `nombre_archivo`, `filas_de_datos`, `sha256` de los bytes con su BOM, `uq_archivo_origen_sha256`, `ck_archivo_origen_tipo`); `carga` (`ck_carga_conciliada`, `ck_carga_filas`, `ck_carga_publicable`, `uq_carga_publicada_por_seccion`, `uq_carga_archivo_util`); `carga_columna`; `carga_fila`; `estudiante` (`ck_estudiante_codigo`, `ck_estudiante_codigo_inventado` en Neon); `medicion`; `rechazo_fila`; consultas Q01 a Q14; vista `v_r17_por_pi`.
**Pantalla**: P3 Subir export y P4 Resultado de la carga.

**Acceptance Scenarios** (`specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`):

1. **El .csv inventado de la 410 queda publicado entero.** **Dado** la 410 sin cargas, **Cuando** el profesor sube `gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv`, **Entonces** la respuesta es 201 con estado PUBLICADA y 11 / 11 / 0, `archivo_origen` guarda ese nombre, la hoja nula, 11 filas de datos y BLACKBOARD_EXPORT, `medicion` tiene 33 filas, `pct_logro_sobre_calificados` da 63,6, 63,6 y 72,7, `rechazo_fila` tiene 5 avisos y ningún RECHAZA_FILA, y Q01 a Q14 devuelven 0 filas.
2. **Las variantes del texto del .csv se leen igual (esquema).** **Dado** una copia del `.csv` inventado con saltos CRLF, sin BOM, con dos líneas vacías al final, sin comillas, con tabuladores en lugar de comas, con Username como primera columna o con la extensión `.CSV`, **Cuando** el profesor la sube, **Entonces** la carga queda PUBLICADA con 11 / 11 / 0 y 33 mediciones.
3. **Una línea vacía entre filas con datos cuenta como fila.** **Dado** una copia con una línea vacía después de la línea 4 del archivo, **Cuando** el profesor la sube, **Entonces** la carga queda PUBLICADA con 12 / 11 / 1, el rechazo CODIGO_VACIO de la fila 5 y `carga_fila` con las filas 2 a 4 y 6 a 13.
4. **Un salto de línea dentro de comillas no cambia la numeración.** **Dado** una copia con un salto de línea dentro de las comillas de Last Name en la fila 3 y «3.50» en la columna 5.2 de la fila 4, **Cuando** el profesor la sube, **Entonces** la carga queda con 11 / 10 / 1 y el rechazo NIVEL_NO_NUMERICO nombra la fila 4.
5. **Un defecto de estructura en el .csv rechaza la carga entera (esquema).** **Dado** una copia del `.csv` sin filas de datos, sin las columnas Username ni Student ID o sin la columna del PI 5.2, **Cuando** el profesor la sube, **Entonces** la carga queda RECHAZADA con 0 / 0 / 0 y el motivo ARCHIVO_SIN_FILAS, COLUMNA_CODIGO_AUSENTE o PI_DEL_PLAN_AUSENTE de la spec 001, con su mensaje.
6. **Un código que no es inventado en el .csv detiene el archivo.** **Dado** una copia con el Username 10000004 en la fila 4, **Cuando** el profesor la sube, **Entonces** la respuesta es 422 con «El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada.» y ninguna tabla gana filas.
7. **La huella del .csv incluye su BOM.** **Dado** la 410 sin cargas, **Cuando** el profesor sube el `.csv` inventado, **Entonces** `archivo_origen.sha256` es igual a la salida de `shasum -a 256` sobre el archivo versionado y distinta de la huella de su copia sin BOM.
8. **El mismo .csv otra vez devuelve su constancia.** **Dado** el `.csv` inventado publicado en la 410, **Cuando** el profesor sube los mismos bytes con el nombre `copia de notas 410.csv`, **Entonces** la respuesta es 200 con la misma constancia y `archivo_origen.nombre_archivo` conserva el primer nombre.
9. **El mismo .csv publicado en la 410 no entra en la 411.** **Dado** el `.csv` inventado publicado en la 410, **Cuando** docente411 sube los mismos bytes a la 411, **Entonces** la respuesta es 409 con «Este archivo ya está publicado en otra sección. No se cargó.».

---

### US-28: Cargar el .xls de texto de Blackboard (Priority: P1)

Como profesor, quiero subir el `.xls` que Blackboard descarga, aunque no sea un libro de Excel, para no tener que convertirlo ni guardarlo otra vez.

**Why this priority**: es el segundo formato del pedido, y hoy recibe 422 por su extensión y, si se renombra a `.xlsx`, CONTENIDO_NO_ES_LIBRO, porque sus primeros bytes son el BOM de UTF-16.

**Independent Test**: el `.xls` inventado de la 410 deja las mismas cifras que el `.csv` de US-27, con otra huella.

**Base**: la de US-27, más la consulta exacta de nombres y valores de `db/pruebas/` (propuesta) sobre las tablas que escribe la carga.
**Pantalla**: P3 Subir export y P4 Resultado de la carga.

**Acceptance Scenarios** (`specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`):

1. **El .xls de texto inventado de la 410 queda publicado entero.** **Dado** la 410 sin cargas, **Cuando** el profesor sube `gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls`, **Entonces** se cumple todo lo del escenario 1 de US-27 y la huella es distinta de la del `.csv`.
2. **Las variantes del .xls se leen igual (esquema).** **Dado** una copia del `.xls` inventado con saltos CRLF, con comas en lugar de tabuladores, con la extensión `.XLS` o con el nombre terminado en `.xlsx`, **Cuando** el profesor la sube, **Entonces** la carga queda PUBLICADA con 11 / 11 / 0, porque el contenido elige el lector.
3. **El .xls con las mismas notas que el .csv es otro archivo.** **Dado** el `.csv` inventado publicado en la 410, **Cuando** el profesor sube el `.xls` inventado de la 410, **Entonces** la respuesta es 409 con «La sección 410 ya tiene una carga publicada. No se cargó el archivo.» y `archivo_origen` no gana filas.
4. **Un código que no es inventado en el .xls detiene el archivo.** **Dado** una copia del `.xls` con el Username 10000004 en la fila 4, **Cuando** el profesor la sube, **Entonces** la respuesta es el 422 de la guardia con la fila 4 y ninguna tabla gana filas.
5. **Los nombres y las actividades del .xls no llegan a ninguna tabla.** **Dado** el `.xls` inventado publicado en la 410, **Cuando** se buscan con igualdad exacta «Estudiante», «Inventado 01» a «Inventado 11», «Complete», «Incomplete», «Needs Grading» y «19.00» en las columnas de texto de las tablas que escribe la carga y de `acceso`, **Entonces** la búsqueda da 0 coincidencias y Q04 devuelve 0 filas.

---

### US-29: Leer el nivel que Blackboard escribe con decimales nulos (Priority: P1)

Como profesor, quiero que el nivel que Blackboard escribe «3.00» en el texto cuente como 3 para que mis filas no se rechacen por la forma del número.

**Why this priority**: Blackboard escribe con dos decimales los puntajes de una columna Score, así que sin esta regla cada fila de un export de texto con niveles queda rechazada con NIVEL_NO_NUMERICO.

**Independent Test**: el `.csv` inventado, que trae todos sus niveles como «N.00», queda con 11 / 11 / 0, y una copia con «3.50» en la columna 5.2 de la fila 3 queda con 11 / 10 / 1 y NIVEL_NO_NUMERICO.

**Base**: `medicion` (`nivel_original`, `estado_evidencia`, `ck_medicion_nivel`, `ck_medicion_estado_nivel`); `rechazo_fila` (NIVEL_NO_NUMERICO, NIVEL_FUERA_DE_ESCALA, `fk_rechazo_fila_columna`); vista `v_r17_por_pi`.
**Pantalla**: P4 Resultado de la carga.

**Acceptance Scenarios** (`specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`):

1. **El texto de un nivel en el PI 5.2 de la fila 3 (esquema).** **Dado** una copia del `.csv` inventado cuya columna 5.2 trae el valor entre comillas en la fila 3, **Cuando** el profesor la sube, **Entonces** «3.00» y «3,00» dejan la medición CALIFICADO con nivel 3, «4.0» la deja con nivel 4 y 63,6 / 63,6 / 72,7 %, y «3.50», «1,000» y «Needs Grading» rechazan la fila con NIVEL_NO_NUMERICO, mientras «0.00», «19.00» y «75» la rechazan con NIVEL_FUERA_DE_ESCALA, en todos los casos con 11 / 10 / 1, 30 mediciones y 60,0 / 60,0 / 70,0 %.
2. **El texto de un nivel dentro de un .xlsx.** **Dado** una copia del `.xlsx` inventado con los textos «3.00», «3,00» o «3.50» en la celda 5.2 de la fila 3, **Cuando** el profesor la sube, **Entonces** los dos primeros valen 3 y el tercero rechaza la fila con NIVEL_NO_NUMERICO.
3. **Un nivel con miles de cifras no deja la carga en 500.** **Dado** una copia del `.csv` con un texto de 5 000 cifras en la columna 5.2 de la fila 3, **Cuando** el profesor la sube, **Entonces** la respuesta es 201 y la fila 3 queda rechazada con NIVEL_FUERA_DE_ESCALA.

---

### US-30: Cotejar la sección con el nombre del export de texto (Priority: P1)

Como profesor, quiero que el sistema reconozca la sección por el nombre del `.csv` o del `.xls`, que no tienen hoja, para que el cotejo de BR-CARGA-11 me proteja igual que con el `.xlsx`.

**Why this priority**: sin este cambio todo export de texto recibe 422 «El archivo no indica su sección», porque el patrón del nombre exige `.xlsx` y el texto no trae hoja.

**Independent Test**: el `.csv` inventado de la 410 subido en la 410 queda PUBLICADA, y la misma copia con el nombre de la 411 queda RECHAZADA con SECCION_NO_COINCIDE.

**Base**: `archivo_origen.hoja` NULL; `seccion.curso_blackboard` (`uq_seccion_curso_bb`); `rechazo_fila` (SECCION_NO_COINCIDE y PERIODO_NO_COINCIDE con RECHAZA_CARGA).
**Pantalla**: P3 Subir export y P4 Resultado de la carga.

**Acceptance Scenarios** (`specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`):

1. **La sección sale del nombre del archivo de texto (esquema).** **Dado** una copia del `.csv` inventado de la 410 con otro nombre, cada una en una base limpia, **Cuando** el profesor la sube a la 410, **Entonces** «…14-35-59 (1).csv» y un nombre con otro prefijo de curso quedan PUBLICADA, el de la 411 queda RECHAZADA con SECCION_NO_COINCIDE y «El archivo corresponde a la sección 411 y usted eligió la 410. No se publicó.», el de 2026-1 con PERIODO_NO_COINCIDE, el de 450010 con el mensaje de asignatura, y `notas 410.csv` recibe 422 con el texto de D-02 sin dejar rastro.
2. **Un .xlsx sin sección en la hoja ni en el nombre recibe el texto nuevo.** **Dado** `hoja1_sin_seccion.xlsx` subido como `notas.xlsx`, **Cuando** el profesor lo sube, **Entonces** la respuesta es 422 con el texto de D-02 y nada se escribe.

---

### US-31: Saber por qué no se admite un archivo (Priority: P1)

Como profesor, quiero un mensaje que me diga qué hacer cuando mi archivo no es un export admitido para no adivinar el formato que acepta el sistema.

**Why this priority**: con tres formatos, los textos de hoy, «Solo se admiten exports de Blackboard en formato .xlsx.» y «… aunque su nombre termine en .xlsx.», pasan a ser falsos.

**Independent Test**: un PDF inventado llamado `export_410.pdf` recibe 422 con el texto nuevo de TIPO_NO_ADMITIDO, y ninguna tabla gana filas.

**Base**: `archivo_origen`, `carga`, `rechazo_fila` y `estudiante` sin filas nuevas; registro de la aplicación (`evento=archivo_detenido` con la huella, la hora, el motivo y su detalle, BR-CARGA-08).
**Pantalla**: P3 Subir export.

**Acceptance Scenarios** (`specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`):

1. **Un archivo que no es un export admitido se detiene sin rastro (esquema).** **Dado** el PDF inventado como `export_410.pdf`, `export_410.xlsx` o `export_410.csv`, un OLE sin cifrado armado en la prueba como `export_410.xls`, `protegido_410.xlsx` como `export_410.xls`, un zip que no es un libro como `export_410.csv` o un archivo de 0 bytes como `export_410.csv`, **Cuando** el profesor lo sube, **Entonces** recibe 422 con TIPO_NO_ADMITIDO, CONTENIDO_NO_ES_LIBRO, NO_SE_PUDO_ABRIR o PROTEGIDO_CON_CONTRASENA según BR-CARGA-05, ninguna tabla gana filas y el registro trae la huella, el motivo y su detalle, sin el nombre del archivo.

---

### US-32: Detener un export de texto dañado sin dejar rastro (Priority: P1)

Como profesor, quiero que un `.csv` o un `.xls` dañado reciba un mensaje que me pida descargarlo otra vez, sin que quede nada a medias en la base.

**Why this priority**: leer texto de terceros abre defectos nuevos (codificación, comillas, separador y tamaño) que no pueden terminar en 500 ni copiar el contenido del archivo al registro.

**Independent Test**: un `.csv` con una comilla sin cerrar recibe 422 con «No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard.», y el registro trae solo la huella, la hora, el motivo NO_SE_PUDO_ABRIR y el detalle COMILLAS.

**Base**: sin escritura en `archivo_origen`, `carga`, `rechazo_fila` ni `estudiante`; registro de la aplicación.
**Pantalla**: P3 Subir export.

**Acceptance Scenarios** (`specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`):

1. **Un texto dañado o armado a mano se detiene sin rastro (esquema).** **Dado** una copia del `.csv` inventado en Windows-1252, con una comilla sin cerrar, con un carácter U+0000, en UTF-16 sin BOM, en UTF-16 BE con BOM, con dos BOM, con una primera línea sin separador, separada por punto y coma, con una fila de 16 385 columnas, con un campo de 131 073 caracteres, con 5 001 filas de datos o solo con el BOM, **Cuando** el profesor la sube, **Entonces** recibe 422 con NO_SE_PUDO_ABRIR, ninguna tabla gana filas y el registro trae su detalle de la lista cerrada, sin texto del archivo.
2. **El orden de BR-CARGA-03 se mantiene con un export de texto (esquema).** **Dado** un `.csv` de 1,2 MB con una comilla sin cerrar, un `.csv` con el código 10000004 y una comilla sin cerrar, o un `.csv` con el código 10000004 subido a una sección con carga publicada, **Cuando** el profesor lo sube, **Entonces** recibe el 422 del tamaño, el 422 de NO_SE_PUDO_ABRIR y el 422 de la guardia, en ese orden de BR-CARGA-03.

---

### US-33: Elegir el .csv o el .xls en la pantalla de subida (Priority: P1)

Como profesor, quiero que el selector de P3 me muestre mis `.csv` y `.xls` para no tener que cambiar el filtro del diálogo del navegador.

**Why this priority**: sin este cambio el diálogo oculta los dos formatos nuevos, y la etiqueta y el aviso dicen que solo vale `.xlsx`.

**Independent Test**: `npm test` del Front pasa con `tests/pantallas/SubirExport.test.tsx`, que exige `accept=".xlsx,.csv,.xls"` y la etiqueta nueva.

**Base**: sin base.
**Pantalla**: P3 Subir export.

**Acceptance Scenarios** (`tests/pantallas/SubirExport.test.tsx` del Front y `specs/003-exports-blackboard/aceptacion/exports_blackboard.feature` como criterio escrito):

1. **El selector admite los tres formatos.** **Dado** P3 de la sección 410, **Cuando** se dibuja, **Entonces** el campo `archivo` tiene `accept` «.xlsx,.csv,.xls» y la etiqueta «Export de Blackboard (.xlsx, .csv o .xls, hasta 1 MB)».
2. **Sin archivo, P3 pide el export.** **Dado** P3 sin archivo elegido, **Cuando** el profesor pulsa «Subir», **Entonces** P3 muestra «Elija el archivo del export (.xlsx, .csv o .xls).» y no llama a la API.
3. **P3 envía el archivo tal cual y la API decide.** **Dado** un archivo `export_410.pdf` elegido sin el filtro del diálogo, **Cuando** el profesor pulsa «Subir», **Entonces** P3 lo envía una vez con su nombre, no muestra un aviso propio y, ante el 422, muestra el `detail` de la API.

---

### US-34: Ver la constancia de un export sin hoja (Priority: P2)

Como profesor, quiero que la constancia de un `.csv` o un `.xls` diga que el archivo no tiene hoja para que el resultado no muestre un campo vacío.

**Base**: `archivo_origen.hoja`; `abet_carga/constancia.py`; hoja «Constancia» del R-17 (`abet_carga/r17.py`).
**Pantalla**: P4 Resultado de la carga.

**Acceptance Scenarios** (`specs/003-exports-blackboard/aceptacion/exports_blackboard.feature` y `tests/pantallas/ResultadoCarga.test.tsx` del Front):

1. **La constancia del .csv no inventa una hoja.** **Dado** el `.csv` inventado publicado en la 410, **Cuando** el profesor pide su constancia y descarga su R-17, **Entonces** `GET /api/cargas/{carga_id}` trae `hoja` nulo, P4 muestra «Sin hoja (export de texto)» y la hoja «Constancia» del R-17 muestra el mismo texto.
2. **La constancia del .xlsx sigue mostrando su hoja.** **Dado** el `.xlsx` inventado con los encabezados reales publicado, **Cuando** el profesor pide su constancia, **Entonces** `hoja` es «gc_SINTETICO_20262_450002_410_f» en el cuerpo, en P4 y en el R-17.

---

### US-35: Revisar por contenido los datos inventados antes de versionarlos (Priority: P1)

Como administrador técnico, quiero que la revisión previa lea por su contenido cada archivo de `tests/datos_inventados/`, también un texto UTF-16 o un `.xls`, para que un export real no entre al repositorio por un formato que hoy nadie revisa.

**Why this priority**: la regla 2 de `scripts/preflight.sh` cuenta 0 en un `.xls` y en un texto UTF-16 o con un byte nulo, justo los formatos que este sprint versiona.

**Independent Test**: `bash scripts/probar_preflight.sh` pasa con los casos nuevos, y un `.xls` UTF-16 con el código 20231234 falla por la regla 2 sin mostrar el código.

**Base**: sin base; `scripts/preflight.sh` y `scripts/probar_preflight.sh`.
**Pantalla**: sin pantalla.

**Acceptance Scenarios** (`scripts/probar_preflight.sh` y `specs/003-exports-blackboard/aceptacion/exports_blackboard.feature` como criterio escrito):

1. **La revisión previa lee el contenido antes de contar los códigos (esquema).** **Dado** en la carpeta de datos inventados un `.xls` UTF-16 con BOM, un `.csv` UTF-16 o UTF-8, un texto en Windows-1252, un `.txt` o un archivo con otra extensión, cada uno con el código 20231234, o un `.xls` que es un OLE, **Cuando** corre `bash scripts/preflight.sh --staged`, **Entonces** falla por la regla 2 sin mostrar el código, y el mismo `.xls` UTF-16 con los códigos 99000001 y 99000002 pasa.
2. **Los exports inventados nuevos pasan la revisión previa.** **Dado** los cuatro exports nuevos versionados, **Cuando** corre `bash scripts/preflight.sh`, **Entonces** termina sin fallas de la regla 2.

---

### US-36: No publicar un export sin ningún nivel en los PI del plan (Priority: P1)

Como profesor, quiero que un export con las columnas de los PI del plan vacías no se publique para que mi sección quede libre para el export que trae los niveles.

**Why this priority**: el export real de hoy llega con las columnas ABET vacías, y publicado deja 33 mediciones SIN_EVIDENCIA, un R-17 sin porcentajes y la sección bloqueada en el corte 1, porque nadie reemplaza una carga publicada hasta US-18.

**Independent Test**: una copia del `.csv` inventado con las tres columnas del plan vacías deja una carga RECHAZADA con el motivo de D-31, y la 410 sigue sin carga publicada.

**Base**: `rechazo_fila` (`ck_rechazo_fila_motivo` con SIN_CALIFICACIONES de V1_10 (propuesta, D-31), RECHAZA_CARGA, `fila_origen` nulo); `carga` (RECHAZADA, `filas_leidas` 0, `ck_carga_terminada`); `carga_columna`, `carga_fila` y `medicion` sin filas de la carga; `uq_carga_publicada_por_seccion`; vista `v_r17_por_pi`.
**Pantalla**: P3 Subir export y P4 Resultado de la carga.

**Acceptance Scenarios** (`specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`):

1. **Un export sin ningún nivel en los PI del plan no se publica.** **Dado** una copia del `.csv` inventado con las columnas 5.1, 5.2 y 5.3 vacías en sus 11 filas, **Cuando** el profesor la sube, **Entonces** la respuesta es 201 con estado RECHAZADA, 0 / 0 / 0 y el mensaje de D-31, `rechazo_fila` tiene 1 fila SIN_CALIFICACIONES con RECHAZA_CARGA y `carga_columna`, `carga_fila` y `medicion` no tienen filas de esa carga.
2. **Un solo nivel basta para publicar.** **Dado** la misma copia con «3.00» en la columna 5.1 de la fila 2, **Cuando** el profesor la sube, **Entonces** la carga queda PUBLICADA con 11 / 11 / 0, 1 medición CALIFICADO y 32 SIN_EVIDENCIA.
3. **La sección queda libre para el export con niveles.** **Dado** la carga RECHAZADA del escenario 1, **Cuando** el profesor sube el `.csv` inventado de la 410, **Entonces** la carga queda PUBLICADA con 11 / 11 / 0.

---

### Edge Cases

- Un export de texto con el nombre cambiado pierde su única señal de sección, así que en texto el cotejo de BR-CARGA-11 vale lo que vale el nombre (D-02).
- Un U+FEFF o un U+200B dentro de un encabezado impide reconocer su PI, y la carga cae en PI_DEL_PLAN_AUSENTE con el mensaje que nombra el PI que falta.
- El texto que Excel en español guarda otra vez sale separado por punto y coma y, a veces, en Windows-1252, y los dos casos reciben NO_SE_PUDO_ABRIR, cuyo texto pide descargar otra vez el export.
- Un `.xlsx` que trae un texto UTF-16 con BOM se lee como texto por su contenido, y su hoja queda nula.
- Una línea vacía al final no cuenta como fila, y una línea vacía entre filas con datos cuenta con su número, como en el libro (BR-CARGA-16).
- Las columnas «ABET SO 4.1» y «ABET SO4.2» del export real no están en el plan de 450002, así que cada carga real trae dos avisos COLUMNA_PI_FUERA_DEL_PLAN, y cada columna de 100 puntos del plan trae el aviso PUNTAJE_MAXIMO_DISTINTO (D-04 y D-30).
- Un archivo con más de 5 000 filas de datos se detiene con NO_SE_PUDO_ABRIR (propuesta, J-20), porque ninguna sección se acerca a esa cifra y un archivo armado con un millón de filas vacías llenaría la transacción de rechazos.

## Requirements *(mandatory)*

- **FR-001** El lector admite un nombre de archivo terminado en `.xlsx`, `.csv` o `.xls`, en cualquier combinación de mayúsculas, y elige cómo leerlo por su contenido (J-18). Un zip es un libro y sigue la revisión de la spec 001, un OLE con los flujos EncryptionInfo y EncryptedPackage es un libro protegido, otro OLE no es un export, un texto con BOM de UTF-8 o de UTF-16 es un export de texto y, sin ninguna de esas firmas, un nombre `.csv` o `.xls` se lee como UTF-8 sin BOM y un nombre `.xlsx` no es un libro.
- **FR-002** El lector de texto decodifica en modo estricto, rechaza un texto con un byte nulo, toma como separador el tabulador si la primera línea trae uno y la coma si no, rechaza una primera línea sin separador, lee con `csv` de la biblioteca estándar con `strict=True` y comillas dobles, y entrega las mismas tuplas que el libro, con la fila 1 como encabezado y la fila de un rechazo igual al número de registro del archivo.
- **FR-003** El lector de texto aplica los límites de la cuadrícula de Excel (1 048 576 filas y 16 384 columnas) y el tope de un campo de `csv` (131 072 caracteres), además del tope de 1 MB de la spec 001, y cada falla de lectura responde 422 sin rastro, nunca 500.
- **FR-004** Un encabezado es de PI cuando, sin espacios a los lados y dentro de los 200 caracteres que guarda `carga_columna.encabezado`, empieza por las escrituras que fija J-19, seguidas del código del PI y de «[», y el código guardado en `carga_columna.pi_codigo` es siempre la forma N.N del catálogo.
- **FR-005** `V1_10` (nueva) reemplaza `ck_carga_columna_encabezado` por la misma regla de FR-004, sin perder la regla C6 de V1_07 («6.10 [» no pasa como 6.1), y `db/pruebas/pruebas.sql` gana un caso que debe pasar y uno que no por cada escritura.
- **FR-006** Un nivel escrito como texto con decimales nulos, como «3.00», vale el entero, en un export de texto y en una celda de texto de un libro, y cualquier otro texto que no es un entero sigue con NIVEL_NO_NUMERICO (D-03).
- **FR-007** Un export de texto deja `archivo_origen.hoja` nulo, y su sección y su periodo salen solo del nombre `gc_<curso_blackboard>_fullgc_<fecha>.csv` o `.xls`, con las reglas de BR-CARGA-11 y BR-CARGA-12 de la spec 001.
- **FR-008** La constancia de `GET /api/cargas/{carga_id}` trae `hoja` nulo para un export de texto, y P4 y la hoja «Constancia» del R-17 muestran en su lugar «Sin hoja (export de texto)» (propuesta).
- **FR-009** P3 ofrece en su selector los tres formatos y lo dice en su etiqueta y en su aviso, sin revisar el tipo del archivo, que decide la API.
- **FR-010** La regla 2 de `scripts/preflight.sh` lee como texto UTF-16 todo `.csv`, `.tsv`, `.txt` o `.xls` de `tests/datos_inventados/` que empieza con el BOM de UTF-16, lee como texto los demás `.xls` y falla con un `.xls` que es un OLE, porque sus celdas no se pueden revisar, siempre sin mostrar el contenido encontrado.
- **FR-011** `scripts/generar_exports_inventados.py` escribe con los mismos bytes en cada corrida los cuatro exports de la tabla de cifras, y `tests/test_generador_exports.py` comprueba sus encabezados, sus cifras y que ningún número de 8 dígitos deja de empezar con 99, también en UTF-16.
- **FR-012** Antes de implementar, las reglas de `specs/features/carga-export/carga-export.spec.md` (BR-CARGA-03, BR-CARGA-05, BR-CARGA-11, BR-CARGA-14 a BR-CARGA-17) y de `specs/features/r17/r17.spec.md` (BR-R17-10) reciben su bloque fechado, y el Front actualiza `docs/03-api/contrato.md`, `docs/specs/api-contracts.md` y `docs/01-arquitectura/frontend.md`.
- **FR-013** Los escenarios de la spec 001 cuyo texto literal cambia (el tipo no admitido, el contenido que no es un libro y el archivo sin sección de `carga.feature`, y el escenario 1 de US-21) se actualizan en el mismo cambio, y la suite completa sigue pasando.
- **FR-014** `V1_10` se aplica en la rama `develop` de Neon después de restablecerla desde la principal y en la rama principal antes de llevar la versión a `main`, siempre desde el Windows de Jefferson por Tailscale y con su permiso, y Production no recibe el lector nuevo antes que su base.
- **FR-015** Cada cambio actualiza `MEMORIA.md` y `CHANGELOG.md` en el mismo commit y pasa `bash scripts/preflight.sh`, como en la spec 001.

## Success Criteria *(mandatory)*

- **SC-001** Los tres exports inventados de la 410 (`.csv`, `.xls` y `.xlsx`) dan cada uno 11 / 11 / 11 / 0, 33 mediciones, 63,6 / 63,6 / 72,7 % y 5 avisos, sin ninguna diferencia entre formatos.
- **SC-002** El 100 % de los escenarios de esta spec tiene una prueba que pasa en la integración continua, y los de la spec 001 siguen pasando con sus textos actualizados.
- **SC-003** Ningún archivo de la batería de pruebas del lector, sea libro o texto, sano o dañado, produce un 500; cada uno responde 201 o 422 con su mensaje.
- **SC-004** En la vista previa de `develop`, el `.csv` inventado de la 410 y el `.xls` inventado de la 411 quedan PUBLICADA con 11 de 11 filas aceptadas y R-17 de 63,6 / 63,6 / 72,7 %, y Q01 a Q14 devuelven 0 filas en la rama `develop` de Neon.
- **SC-005** Ningún archivo de `tests/datos_inventados/` trae un número de 8 dígitos que no empiece con 99, también en los textos UTF-16, según la regla 2 de `scripts/preflight.sh` y `tests/test_generador_exports.py`.

## Decisiones abiertas

De la carrera (D). Mientras no se decidan, el sistema aplica el valor provisional y el R-17 sale con la franja PROVISIONAL, como en la spec 001. Dos decisiones de la spec 001 se precisan para los exports de texto y conservan su número.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| D-02 | Sección cuando el archivo no la declara (spec 001), precisada para el export de texto, que no tiene hoja | Sin cambio para el `.xlsx`. Un export de texto declara su sección solo con su nombre, y si el nombre no la declara la API responde 422 sin rastro con «El archivo no indica su sección. Suba el export de Blackboard sin cambiar el nombre del archivo ni el de su hoja.», el mismo texto para los tres formatos (decidida por Jefferson el 2026-11-09) | Coordinación de Ambiental |
| D-03 | Celdas con «-» o «NP» (spec 001), precisada para «Needs Grading» y para el nivel escrito con decimales | Un texto con decimales nulos, como «3.00», «3,00» o «4.0», vale el entero, con la expresión `[+-]?[0-9]+(?:[.,]0{1,2})?`, y «3.50», «1,000» y «Needs Grading» siguen en NIVEL_NO_NUMERICO, que rechaza la fila (decidida por Jefferson el 2026-11-09) | Coordinación de Ambiental |
| D-30 | Escala de las columnas ABET de 100 puntos, es decir, si el profesor escribe niveles 1 a 4 o un puntaje de 0 a 100 que una rúbrica convierte en nivel | El profesor escribe niveles 1 a 4; un valor fuera de esa escala, como 75, da NIVEL_FUERA_DE_ESCALA (D-06), y cada columna de 100 puntos deja el aviso PUNTAJE_MAXIMO_DISTINTO (D-04), sin conversión | Stefanny Montaño o la Oficina de Calidad, con la Coordinación de Ambiental |
| D-31 | Export sin ningún nivel en las columnas de los PI del plan | La carga queda RECHAZADA con el motivo nuevo SIN_CALIFICACIONES (V1_10), RECHAZA_CARGA y «El archivo no trae ningún nivel en las columnas de los PI del plan. La carga no se publicó.», y la sección queda libre (decidida por Jefferson el 2026-11-09) | Coordinación de Ambiental |

De Jefferson (J).

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| J-18 | Formatos admitidos y cómo se decide el formato | Se admiten `.xlsx`, `.csv` y `.xls` en cualquier combinación de mayúsculas, y el contenido elige el lector según BR-CARGA-05. Un OLE sin cifrado, como un libro de Excel 97-2003, recibe CONTENIDO_NO_ES_LIBRO con el texto nuevo, sin motivo propio ni dependencia nueva (decidida por Jefferson el 2026-11-09) | Jefferson |
| J-19 | Escrituras del encabezado que el sistema reconoce como columna de PI | «ABET» opcional, luego «SO» o «PI» opcional y luego el código N.N y «[», con cero a tres espacios entre las partes y sin distinguir mayúsculas en las letras ASCII. «ABET SO5.1» y «ABET SO 5.1» son el mismo PI, así que dos columnas así dan PI_REPETIDO, y un SO fuera del plan sigue en COLUMNA_PI_FUERA_DEL_PLAN (decidida por Jefferson el 2026-11-09) | Jefferson |
| J-20 | Tope de filas de datos por archivo | 5 000 filas de datos, para el texto y para el libro, con NO_SE_PUDO_ABRIR y el detalle FILAS en el registro (decidida por Jefferson el 2026-11-09) | Jefferson |

## Fuera de alcance

- Leer un libro binario de Excel 97-2003, que exigiría una dependencia nueva como xlrd para un formato que Blackboard no produce.
- Un texto separado por punto y coma, que Excel escribe en las configuraciones regionales con coma decimal, y una codificación distinta de UTF-8 y UTF-16, como Windows-1252.
- Convertir un puntaje de 0 a 100 en un nivel de 1 a 4, que espera a D-30.
- Avisar de una columna que parece de PI y no se reconoce, como «ABET SO5 [», que hoy se descarta sin aviso como cualquier columna que no es de PI.
- Tomar el código de Student ID fila por fila cuando Username llega vacío en esa fila.
- Reemplazar una carga con un export de otro formato, que llega con el reemplazo del corte 2 (US-18) y no necesita reglas propias.
