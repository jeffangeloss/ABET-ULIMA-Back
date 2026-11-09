---
name: Carga del export
description: Recepción, validación y carga en una sola transacción del export de Blackboard de una sección, con su huella, sus rechazos y sin datos personales.
targets:
  - ../../../abet_carga/lector.py
  - ../../../abet_carga/validacion.py
  - ../../../abet_carga/carga.py
  - ../../../app/rutas/cargas.py
---

# Carga del export

> **Estado al 2026-11-09.** Las reglas BR-CARGA-03, 05 a 08, 11 y 14 a 17 suman el bloque fechado de la spec 003 (`specs/003-exports-blackboard/`), escrito antes del código, con los tres formatos del export de Blackboard. **Estado al 2026-10-30.** Reglas de la fase 1 de contrato (T011), escritas antes del código. Los archivos de `targets` nacen en la fase 3, y la sección Verification se llenó el 2026-10-30 con la corrida del corte 1 (T061); las reglas del corte 2 la reciben con T088.

Esta spec viva fija cómo la interfaz de programación de aplicaciones (application programming interface, API) recibe el export de una sección, que es el archivo de calificaciones que exporta Blackboard, lo valida y lo guarda en el esquema `abet`. Cada regla de negocio (business rule, BR) nombra su fuente en `specs/001-mvp-carga-r17/spec.md`, sean historias de usuario (user stories, US), requisitos funcionales (functional requirements, FR), criterios de éxito (success criteria, SC) o decisiones abiertas (D). Cada regla nombra también la restricción o la consulta de control de la base que la respalda y el escenario de `specs/001-mvp-carga-r17/aceptacion/carga.feature` que la prueba, citado por su título. Los textos entre «» son literales, y lo marcado «(propuesta)» no está fijado en las decisiones de la spec, como en los `.feature`, aunque algún escenario ya lo compruebe. Las reglas del corte 2 llevan esa marca en su título. La forma de cada respuesta está en `docs/03-api/contrato.md` del Front, y los ejemplos usan solo datos inventados.

## User Stories

| ID | Descripción | Corte |
| --- | --- | --- |
| US-07 | Subir el export y cargarlo en una sola transacción | 1 |
| US-08 | Rechazar exports con códigos que no son inventados | 1 |
| US-09 | Reconocer un export ya cargado | 1 |
| US-10 | Rechazar filas inválidas y avisar de columnas dudosas | 1 |
| US-11 | Detener un archivo ilegible sin dejar rastro | 1 |
| US-12 | Rechazar la carga por su estructura | 1 |
| US-13 | Rechazar el export de otra sección o periodo | 1 |
| US-14 | Descartar nombres y valores leídos | 1 |
| US-18 | Reemplazar la carga publicada de una sección | 2 |
| US-19 | Ver las cargas al alcance del usuario | 2 |
| US-21 | Confirmar la sección cuando el archivo no la declara | 2 |
| US-26 a US-32, US-34 y US-36 | Exports de Blackboard en .xlsx, .csv y .xls, encabezados reales y export sin niveles (spec 003) | 1 |

## Business Rules

### BR-CARGA-01: Ruta de subida y su respuesta
- `POST /api/secciones/{seccion_id}/cargas` recibe el export en el campo `archivo` de un formulario multipart (`multipart/form-data`) y llama a `cargar(bytes, seccion_id, usuario_id)` de `abet_carga/carga.py`, la misma función que usa el comando de carga, en una biblioteca que no importa FastAPI.
- En el corte 1 solo sube el profesor que `acceso.docente_seccion` asigna a la sección. El coordinador y cualquier otro profesor reciben el 403 de BR-ACCESO-08, y `archivo_origen`, `carga` y `estudiante` no ganan filas. En el corte 2 el coordinador reemplaza en cualquier sección (BR-CARGA-19).
- `carga.subida_por` guarda el usuario de la sesión (`fk_carga_subida_por`, columna nueva de V1_09), y la constancia muestra su correo (valor provisional de D-12).
- Una carga nueva, PUBLICADA o RECHAZADA, responde 201 con la constancia de BR-R17-10, y su campo `estado` dice cuál. El mismo archivo ya publicado en la sección responde 200 (BR-CARGA-09).
- El conjunto de reglas de la carga nueva sale de `CONJUNTO_REGLAS` (BR-PERIODO-02).
- Una sección sin filas en `abet.plan_medicion` para su asignatura y su periodo responde 422 con «La carrera aún no registra el plan de medición de esta sección.» (propuesta) y no deja rastro.
- **Fuente**: US-07, FR-008, FR-010, FR-012, D-12 y Principio VI de la constitución.
- **Prueba**: «El export correcto queda publicado entero», «Un profesor no sube a una sección que no tiene asignada» y «El coordinador no sube en el corte 1».

### BR-CARGA-02: Una sola transacción
- `cargar()` escribe `archivo_origen`, `carga`, `carga_columna`, `carga_fila`, `estudiante`, `medicion` y `rechazo_fila` en una sola transacción de psycopg 3 con `prepare_threshold=None`, o no escribe nada.
- Un fallo en cualquier punto deshace la transacción entera y responde 500 con «La carga no se completó y no se guardó ningún dato. Intente de nuevo.». Ninguna carga queda EN_CURSO al terminar la petición, aunque la conexión con Neon se corte.
- Una restricción violada al final, como un nivel 5 que llega a `ck_medicion_nivel`, también deshace la carga entera. Si una violación llega a la base, el programa tiene un defecto, y ese defecto se corrige con una prueba nueva (Principio I de la constitución).
- La carga entra EN_CURSO y se cierra con `terminada_en = clock_timestamp()`, porque `now()` devuelve la hora de inicio de la transacción y dejaría iguales el inicio y el fin.
- Los identificadores `GENERATED ALWAYS AS IDENTITY` se consumen aunque la transacción se deshaga, así que las pruebas toman el `carga_id` de la respuesta y nunca lo suponen.
- **Fuente**: US-07, FR-012, Principio III de la constitución, `ck_carga_estado` y `ck_carga_terminada`.
- **Prueba**: «Un fallo en cualquier punto de la transacción no deja nada escrito», «Una restricción violada al final deshace la carga entera» y «El export correcto queda publicado entero».

### BR-CARGA-03: Orden de las comprobaciones
- La API sigue siempre este orden, y los pasos 1 a 8 responden sin escribir nada cuando fallan.
  1. La sesión, el alcance de la sección (BR-ACCESO-06 y BR-ACCESO-08) y el plan de medición de la sección (BR-CARGA-01).
  2. La huella SHA-256 (Secure Hash Algorithm de 256 bits) de los bytes recibidos (BR-CARGA-06), que se calcula aquí sobre todo cuerpo que llega, aunque el archivo se rechace después, porque el registro de la aplicación la guarda de cada rechazo por tamaño, por archivo ilegible o por la guardia (BR-CARGA-08).
  3. El tamaño (BR-CARGA-04).
  4. La extensión, los primeros bytes, la revisión del zip y la apertura del libro (BR-CARGA-05).
  5. La guardia de códigos inventados (BR-CARGA-07).
  6. La búsqueda de la huella en `abet.archivo_origen` (BR-CARGA-09).
  7. La carga PUBLICADA de otro archivo en la sección (BR-CARGA-10).
  8. El 422 del corte 1 para el archivo que no declara su sección (BR-CARGA-11).
  9. La lectura y la validación de las filas en memoria y, después, la transacción de BR-CARGA-02. La transacción registra el archivo y la carga y aplica, en este orden, la sección y el periodo declarados (BR-CARGA-11 y BR-CARGA-12), la estructura (BR-CARGA-13), las columnas (BR-CARGA-14) y las filas (BR-CARGA-15) antes de cerrar la carga (BR-CARGA-16).
- Los 401, 403, 409 y 422 de los pasos 1 a 8 no dejan rastro en `archivo_origen`, `carga`, `carga_columna`, `carga_fila`, `medicion`, `rechazo_fila` ni `estudiante`. Que el 409 del paso 7 no escriba `archivo_origen` es (propuesta).
- La huella va antes del tope de 1 MB porque el cuerpo ya está en la memoria de la función cuando llega a la API, y Vercel detiene todo cuerpo de más de 4,5 MB antes de que llegue a FastAPI (BR-CARGA-04). Así, el registro de cada archivo que se detiene en los pasos 3 y 4, incluido el de 1,2 MB, trae la huella, la hora y el motivo que pide US-11 (escenario 4). La huella no se busca en `abet.archivo_origen` hasta el paso 6, después de la guardia, y ningún paso anterior al 9 escribe en la base.
- **Fuente**: FR-012, FR-013, FR-014, US-08, US-09, US-11 y US-13.
- **Prueba**: «Un archivo publicado en otra sección se detiene sin datos de esa sección», que revisa la huella antes que la sección, «Un solo código que no es inventado rechaza el archivo entero sin dejar rastro», «Un archivo que no se puede leer se detiene antes de registrar nada» y «Un export que no declara su sección se detiene sin dejar rastro»; con el alcance antes que la huella, «El profesor no alcanza una sección ajena escribiendo la ruta» (`acceso.feature`); con el profesor de varias secciones, «El profesor de varias secciones no alcanza una sección que no dicta», que comprueba el alcance antes que la huella, «Un archivo publicado en una sección del profesor se detiene en otra de sus secciones», que busca la huella antes que el cotejo de la hoja, y «El mismo número de sección en otra asignatura no basta para cargar el export», que coteja la sección antes que la estructura (`varias_secciones.feature`).
- **Cambio del 2026-11-09 (spec 003, US-27, US-31 y US-32).** El paso 4 pasa a ser la extensión, el formato por el contenido y su lectura, que es la revisión del zip y la apertura del libro o la decodificación y la lectura del texto, con el tope de 5 000 filas de datos (BR-CARGA-05). Los pasos 5 a 9 no cambian, así que un texto ilegible se detiene antes de la guardia y la guardia, antes del 409 de BR-CARGA-10. **Prueba**: «El orden de BR-CARGA-03 se mantiene con un export de texto» (`specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`).

### BR-CARGA-04: Tope de 1 MB
- Un archivo de más de 1 MB (1 048 576 bytes, propuesta) recibe 422 con «El archivo supera el máximo de 1 MB.» antes de leerse, y `archivo_origen`, `carga`, `rechazo_fila` y `estudiante` no ganan filas.
- El tope queda muy por debajo de los 4,5 MB por petición de Vercel. Un cuerpo mayor recibe el 413 de Vercel antes de llegar a FastAPI, y el Front muestra el mismo mensaje (sección 8 de `docs/03-api/contrato.md` del Front).
- **Fuente**: FR-012, Edge Cases de la spec 001 y plan.md (Technical Context).
- **Prueba**: «Un archivo que no se puede leer se detiene antes de registrar nada», con el ejemplo del .xlsx inventado de 1,2 MB.

### BR-CARGA-05: Archivo ilegible sin rastro
- El tipo se comprueba primero por la extensión y después por los primeros bytes. Un nombre que no termina en `.xlsx` recibe «Solo se admiten exports de Blackboard en formato .xlsx.», y un contenido que no es un libro de Excel bajo un nombre `.xlsx` recibe «El contenido del archivo no es un libro de Excel aunque su nombre termine en .xlsx.».
- Un libro protegido con contraseña recibe «El archivo está protegido con contraseña. Guárdelo sin contraseña y súbalo.».
- Antes de abrir el libro, `abet_carga/lector.py` revisa el zip con `zipfile`, con su tamaño descomprimido y su número de partes, y rechaza `xl/vbaProject.bin` y `xl/externalLinks/` con «El archivo trae macros o vínculos externos y no se admite.». Un contenido que supera 20 MB al descomprimirse recibe «El contenido del archivo supera el tamaño admitido al descomprimirse.» (propuesta, el límite y el texto), y el tope del número de partes también es (propuesta).
- Un zip cortado o que no abre recibe «No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard.».
- El lector abre el libro con `openpyxl.load_workbook(read_only=True, data_only=True)`, sin pandas y con defusedxml activo.
- Todos estos casos responden 422, y `archivo_origen`, `carga`, `rechazo_fila` y `estudiante` no ganan filas, porque `archivo_origen.filas_de_datos` es obligatorio y un archivo ilegible no se puede medir.
- **Fuente**: US-11, FR-013 y Principio III de la constitución.
- **Prueba**: «Un archivo que no se puede leer se detiene antes de registrar nada» y «Un libro que se infla al descomprimirse se rechaza». Una prueba unitaria de `lector.py` falla si `openpyxl.xml.DEFUSEDXML` es `False` (US-11, escenario 3, fuera del `.feature`).
- **Cambio del 2026-11-09 (spec 003, US-28, US-31 y US-32, J-18 y J-20).** Esta lista reemplaza la primera viñeta de la regla, y las demás siguen para el libro.
  - El nombre sin ruta termina en `.xlsx`, `.csv` o `.xls`, en cualquier combinación de mayúsculas. Otro nombre recibe «Solo se admiten exports de Blackboard en formato .xlsx, .csv o .xls.» (TIPO_NO_ADMITIDO).
  - El contenido elige el lector, en este orden. Un archivo vacío no abre. Un zip (`PK\x03\x04`) es un libro y sigue la revisión de esta regla. Un OLE (`D0 CF 11 E0 A1 B1 1A E1`) con los flujos EncryptionInfo y EncryptedPackage es un libro protegido, y otro OLE, como un libro binario de Excel 97-2003, recibe «El contenido del archivo no es un export de Blackboard aunque su nombre termine en .xlsx, .csv o .xls.» (CONTENIDO_NO_ES_LIBRO, texto nuevo). `EF BB BF` es texto UTF-8 y `FF FE` es texto UTF-16 LE, y el lector quita ese BOM una sola vez, mientras `FE FF` (UTF-16 BE) no se admite. Sin ninguna de esas firmas, un nombre `.csv` o `.xls` se lee como UTF-8 sin BOM y un nombre `.xlsx` recibe CONTENIDO_NO_ES_LIBRO.
  - El texto se decodifica en modo estricto. La primera línea, hasta el primer `\r\n`, `\r` o `\n`, elige el separador, que es el tabulador si la línea trae uno y la coma si no. `csv` de la biblioteca estándar lee el texto con `strict=True` y comillas dobles, sin `csv.Sniffer`, y el lector no cambia `csv.field_size_limit()`, que queda en 131 072 caracteres.
  - Un texto que no se decodifica, que conserva un U+FEFF al comienzo, que trae el carácter U+0000 o que queda vacío, una primera línea sin tabulador ni coma, una primera línea con «;» cuyo encabezado no trae Username ni Student ID, una comilla sin cerrar, un campo de más de 131 072 caracteres o una fila de más de 16 384 columnas reciben «No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard.» (NO_SE_PUDO_ABRIR). El mismo motivo detiene, en el texto y en el libro, un archivo con más de 5 000 filas de datos (J-20). También detiene, con el detalle FILAS, un archivo cuyo recorrido pasa de 1 000 000 de celdas, contando las filas vacías del final, porque openpyxl rellena cada fila hasta su última celda y un libro de 112 KB con 20 000 filas vacías hasta la columna XFD tardaba 10,7 s (propuesta de la revisión de seguridad del 2026-11-09). Un nombre de archivo con un carácter de control, de U+0000 a U+001F o U+007F, recibe TIPO_NO_ADMITIDO antes de leerse, porque la base no lo guardaría y la carga respondería 500.
  - ArchivoIlegible lleva además un detalle de una lista cerrada (VACIO, CODIFICACION, CARACTER_NULO, SEPARADOR, COMILLAS, CAMPO_LARGO, COLUMNAS, FILAS) que va solo al registro de la aplicación (BR-CARGA-08). El lector de texto convierte cualquier error en ArchivoIlegible sin encadenar la excepción original, que podría llevar los bytes del archivo.
  - Todos estos casos responden 422 sin escribir en `archivo_origen`, `carga`, `rechazo_fila` ni `estudiante`, como el libro.
  - **Fuente**: US-28, US-31 y US-32, FR-001 a FR-003, J-18 y J-20 de la spec 003. **Prueba**: «Un archivo que no es un export admitido se detiene sin rastro», «Un texto dañado o armado a mano se detiene sin rastro» y «Las variantes del .xls se leen igual» (`exports_blackboard.feature`).

### BR-CARGA-06: Huella SHA-256 de los bytes recibidos
- La huella SHA-256 se calcula sobre los bytes recibidos, antes de cualquier transformación, y se guarda en `archivo_origen.sha256` con 64 caracteres hexadecimales en minúscula (`ck_archivo_origen_sha256`), igual a la salida de `shasum -a 256` del archivo.
- Una huella se registra una sola vez (`uq_archivo_origen_sha256`). Un export abierto y guardado otra vez en Excel cambia sus bytes, así que cuenta como archivo distinto.
- El sistema no conserva los bytes después de la transacción, y del archivo solo queda su huella (BR-CARGA-17).
- **Fuente**: FR-014, US-07, US-09, `uq_archivo_origen_sha256` y `ck_archivo_origen_sha256`.
- **Prueba**: «El export correcto queda publicado entero», «La base impide registrar dos veces la misma huella» y «Un export abierto y guardado de nuevo es otro archivo».
- **Cambio del 2026-11-09 (spec 003, US-27).** La huella de un export de texto incluye su BOM, porque se calcula sobre los bytes recibidos, así que la misma copia sin BOM es otro archivo. **Prueba**: «La huella del .csv incluye su BOM» (`exports_blackboard.feature`).

### BR-CARGA-07: Guardia de códigos inventados
- Con `GUARDIA_DATOS_INVENTADOS=1`, un solo Username no vacío fuera de 99000000 a 99999999, incluido uno mal formado como 9900001, detiene el archivo entero con 422 y «El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada.», con el número de la primera fila que falla (propuesta).
- El cuerpo de la respuesta no trae el código, y `archivo_origen`, `carga`, `carga_columna`, `carga_fila`, `medicion`, `rechazo_fila` y `estudiante` no ganan filas.
- Los extremos 99000000 y 99999999 pasan la guardia y se cargan.
- Ningún campo de la petición apaga la guardia, ni el campo multipart `guardia` ni el parámetro de consulta `guardia`. Solo la cambia la variable del despliegue, y apagarla exige un cambio revisado en una solicitud de integración (pull request, PR).
- La base repite la regla en Neon con `ck_estudiante_codigo_inventado CHECK (codigo LIKE '99%')` sobre `abet.estudiante`, que aplica `db/plataforma/neon/guardia_datos_inventados.sql` solo en Neon.
- La guardia revisa la columna de la que sale el código, que es Username o, si el archivo no la trae, Student ID (propuesta, BR-CARGA-15).
- Con la guardia encendida, CODIGO_INVALIDO no se alcanza, porque todo código mal formado detiene el archivo. Ese motivo solo aparece con la guardia apagada en una base desechable (BR-CARGA-15).
- **Fuente**: US-08, FR-005, D-10, Principio II de la constitución y `ck_estudiante_codigo_inventado` (script de plataforma).
- **Prueba**: «Un solo código que no es inventado rechaza el archivo entero sin dejar rastro», «Los extremos del rango inventado pasan la guardia», «Ningún campo de la petición apaga la guardia» y «La guardia de la base rechaza un código que no es inventado aunque el programa falle»; en el piloto, «La guardia de datos inventados está encendida en el piloto» (`despliegue.feature`).
- **Cambio del 2026-11-09 (spec 003, US-27 y US-28).** La guardia revisa igual el código de un export de texto, que llega como texto, y la fila que nombra es el número de registro del archivo, con el encabezado como fila 1. **Prueba**: «Un código que no es inventado en el .csv detiene el archivo» y «Un código que no es inventado en el .xls detiene el archivo» (`exports_blackboard.feature`).

### BR-CARGA-08: Registro de la aplicación sin el contenido del export
- La guardia evita guardar, pero el archivo ya está en la función de Vercel cuando se rechaza. Por eso el registro de la aplicación guarda de un rechazo por la guardia solo la huella SHA-256 y la hora, nunca el cuerpo, los códigos, los nombres, la hoja ni el número de fila.
- De un archivo que se detiene por su tamaño o porque no se puede leer (BR-CARGA-04 y BR-CARGA-05), el registro guarda la huella, la hora y el motivo, y ningún nombre de hoja, celda ni código. La huella existe en estos casos porque la API la calcula antes del tope de 1 MB (BR-CARGA-03).
- De un error de integridad que llega a la base (BR-CARGA-02), el registro guarda solo el SQLSTATE y el nombre de la restricción, nunca el campo DETAIL del error, que repite los valores de la fila. El SQLSTATE es el código de cinco caracteres con que PostgreSQL identifica el error.
- **Fuente**: Principio II de la constitución, US-08 (escenario 3), US-11 (escenario 4), FR-018, SC-006 y T038.
- **Prueba**: una prueba unitaria de `app/rutas/cargas.py`, fuera del `.feature` (T038); en el piloto, «La guardia de datos inventados está encendida en el piloto» (`despliegue.feature`).
- **Cambio del 2026-11-09 (spec 003, US-31 y US-32).** El registro de un archivo detenido suma el detalle de BR-CARGA-05, como en `evento=archivo_detenido hora=… sha256=… motivo=NO_SE_PUDO_ABRIR detalle=COMILLAS`, y sigue sin nombre de archivo, hoja, celda ni código. **Prueba**: prueba unitaria de `app/rutas/cargas.py` y «Un texto dañado o armado a mano se detiene sin rastro» (`exports_blackboard.feature`).

### BR-CARGA-09: Archivo ya registrado
- Si la huella ya tiene una carga PUBLICADA en la misma sección, la API responde 200 con la constancia existente, aunque el archivo llegue con otro nombre, y no escribe nada. `archivo_origen.nombre_archivo` conserva el primer nombre, y `medicion` y `v_tabla_maestra_pi` siguen con las mismas filas de la sección.
- Si la huella ya tiene una carga PUBLICADA en otra sección, la API responde 409 con «Este archivo ya está publicado en otra sección. No se cargó.» antes de escribir, sin el `carga_id`, la huella ni el número de la otra sección, porque el índice único parcial `uq_carga_archivo_util` impediría publicar la carga nueva (caso R34 de `db/pruebas/pruebas.sql`).
- Si la huella solo tiene cargas RECHAZADA o REEMPLAZADA, la carga nueva reutiliza su `archivo_id`, lo que `uq_carga_archivo_util` permite porque solo limita las PUBLICADA. El estado REEMPLAZADA aparece desde el corte 2 (BR-CARGA-19).
- **Fuente**: US-09, FR-012, FR-014, `uq_archivo_origen_sha256` y `uq_carga_archivo_util`.
- **Prueba**: «Subir otra vez el export publicado devuelve su constancia y no cambia nada», «El mismo contenido con otro nombre se reconoce por la huella», «Un archivo publicado en otra sección se detiene sin datos de esa sección» y «Un archivo rechazado en una sección se publica después en la suya»; con dos secciones del mismo profesor, «Un archivo publicado en una sección del profesor se detiene en otra de sus secciones» (`varias_secciones.feature`); en el corte 2, «Volver al export anterior reutiliza su archivo» (`reemplazo_y_cargas.feature`).

### BR-CARGA-10: Una sola carga publicada por sección
- Si la sección ya tiene una carga PUBLICADA de otro archivo, la API responde 409 con «La sección 410 ya tiene una carga publicada. No se cargó el archivo.», con el número de la sección elegida, y `archivo_origen` y `carga` no ganan filas.
- Dos subidas simultáneas de archivos distintos dejan una sola carga PUBLICADA. La transacción que llega segunda a publicar choca con el índice único parcial `uq_carga_publicada_por_seccion`, se deshace entera y responde el mismo 409, sin carga EN_CURSO.
- En el corte 2 la pantalla P3 ofrece el reemplazo (BR-CARGA-19), y sin el parámetro `reemplaza` la respuesta sigue en 409.
- **Fuente**: US-07 (escenarios 4 y 5), FR-012 y `uq_carga_publicada_por_seccion`.
- **Prueba**: «Otro archivo no entra en una sección que ya tiene carga publicada», «Dos subidas a la vez dejan una sola publicada» y «Un export abierto y guardado de nuevo es otro archivo»; en el corte 2, «Subir sin pedir el reemplazo no pisa la carga publicada» (`reemplazo_y_cargas.feature`).

### BR-CARGA-11: Sección declarada por el archivo
- El profesor elige la sección (D-02), y el sistema la coteja con el nombre de la hoja y, si la hoja no la declara, con el nombre del archivo.
- La hoja de Blackboard tiene la forma `gc_<curso_blackboard>_f`, como `gc_SINTETICO_20262_450002_410_f`, y los tres últimos segmentos numéricos de `curso_blackboard` dan el periodo (20262 es 2026-2), la asignatura y la sección (propuesta, la regla de lectura). El nombre del archivo de Blackboard tiene la forma `gc_<curso_blackboard>_fullgc_<fecha>.xlsx`.
- Blackboard corta el nombre de hoja a 31 caracteres, así que el cotejo tolera el sufijo `_f` cortado, y `gc_SINTETICO_20262_450002_410` publica en la 410.
- Si la hoja o el nombre declaran otra sección u otra asignatura, la carga queda RECHAZADA con SECCION_NO_COINCIDE y RECHAZA_CARGA, `filas_leidas` 0 y el mensaje «El archivo corresponde a la sección 411 y usted eligió la 410. No se publicó.». La 410 sigue sin carga publicada, y `estudiante` no gana los códigos del archivo. Para otra asignatura, el texto es «El archivo corresponde a la asignatura 450010 y usted eligió la 450002. No se publicó.» (propuesta).
- Si ni la hoja ni el nombre declaran la sección, el corte 1 responde 422 con «El archivo no indica su sección. Sube el export de Blackboard sin cambiar el nombre de su hoja.» y no deja rastro (valor provisional de D-02). En el corte 2 lo reemplaza la confirmación de BR-CARGA-18.
- **Fuente**: US-13, FR-012, FR-016, D-02, `seccion.curso_blackboard` (`uq_seccion_curso_bb`) y `archivo_origen.hoja`.
- **Prueba**: «El export de la 411 subido en la 410 se rechaza», «Un curso o un periodo distinto en el nombre de hoja rechaza la carga» (ejemplo de 450010), «Si la hoja no declara la sección, se coteja el nombre del archivo», «Una hoja truncada a 31 caracteres se coteja igual» y «Un export que no declara su sección se detiene sin dejar rastro»; con un profesor que dicta tres secciones de dos asignaturas, «Cada export del profesor de varias secciones se publica solo en su sección», «El export de una sección del profesor no entra en otra de sus secciones de la misma asignatura» y «El mismo número de sección en otra asignatura no basta para cargar el export» (`varias_secciones.feature`).
- **Cambio del 2026-11-09 (spec 003, US-30, D-02).** El nombre del archivo de Blackboard tiene la forma `gc_<curso_blackboard>_fullgc_<fecha>.xlsx`, `.csv` o `.xls`, sin distinguir mayúsculas en la extensión. Un export de texto no tiene hoja, así que `archivo_origen.hoja` queda nula y su sección y su periodo salen solo del nombre, y en ese caso el cotejo vale lo que vale el nombre. Si ni la hoja ni el nombre declaran la sección, el 422 del corte 1 dice, para los tres formatos, «El archivo no indica su sección. Suba el export de Blackboard sin cambiar el nombre del archivo ni el de su hoja.». **Prueba**: «La sección sale del nombre del archivo de texto» y «Un .xlsx sin sección en la hoja ni en el nombre recibe el texto nuevo» (`exports_blackboard.feature`), y el escenario de US-13 «Un export que no declara su sección se detiene sin dejar rastro» con el texto nuevo.

### BR-CARGA-12: Periodo declarado por el archivo
- Si la hoja o el nombre del archivo declaran otro periodo, como `gc_SINTETICO_20261_450002_410_f` subido en la 410 de 2026-2, la carga queda RECHAZADA con PERIODO_NO_COINCIDE, motivo que agrega V1_09, y RECHAZA_CARGA, con la forma de BR-CARGA-13.
- El texto es «El archivo corresponde al periodo 2026-1 y la sección elegida es de 2026-2. No se publicó.» (propuesta).
- Si difieren el periodo y la sección, manda SECCION_NO_COINCIDE (propuesta).
- **Fuente**: US-13, FR-016 y `ck_rechazo_fila_motivo` en la versión de V1_09.
- **Prueba**: «Un curso o un periodo distinto en el nombre de hoja rechaza la carga» (ejemplo de 20261).

### BR-CARGA-13: Rechazo por estructura
- La carga queda RECHAZADA con efecto RECHAZA_CARGA en cuatro casos. El primero es el archivo sin filas de datos (ARCHIVO_SIN_FILAS, «El archivo no trae filas de estudiantes.»), y el segundo, la falta de la columna de un indicador de desempeño (performance indicator, PI) del plan (PI_DEL_PLAN_AUSENTE, «Falta la columna del PI 5.2 que el plan de medición pide para esta sección.»).
- Los otros dos casos son la falta de Username y de Student ID (COLUMNA_CODIGO_AUSENTE, «El archivo no tiene la columna Username ni Student ID.») y un PI en dos columnas (PI_REPETIDO, «El PI 5.1 aparece en dos columnas del archivo.»), motivos que agrega V1_09.
- La API responde 201 con el estado RECHAZADA y el mensaje. La carga queda con `filas_leidas`, `filas_aceptadas` y `filas_rechazadas` en 0, `terminada_en` no nulo (`ck_carga_terminada`) y `subida_por` del usuario.
- `rechazo_fila` tiene exactamente 1 fila de la carga, con el motivo, RECHAZA_CARGA, `fila_origen` nulo y `carga_columna_id` nulo. En PI_DEL_PLAN_AUSENTE y PI_REPETIDO esta fila guarda además el PI que falta o que se repite en `pi_id`, columna de V1_09 (`fk_rechazo_fila_pi`), y `ck_rechazo_fila_pi` deja `pi_id` nulo en los demás motivos. La carga no registra columnas, filas, mediciones ni avisos, ni siquiera PUNTAJE_MAXIMO_DISTINTO, y `v_r17_por_pi` no la ve.
- `ck_rechazo_fila_motivo` rechaza un motivo fuera de la lista, como «CODIGO_RARO».
- Después de un rechazo, un archivo distinto es otro archivo y se publica, y la carga RECHAZADA conserva su fila de `rechazo_fila`.
- Con varios defectos manda el primero en el orden sección, periodo, ARCHIVO_SIN_FILAS, COLUMNA_CODIGO_AUSENTE, PI_DEL_PLAN_AUSENTE y PI_REPETIDO, y entre varios PI ausentes, el primero del plan (propuesta).
- **Fuente**: US-12, FR-016, `ck_carga_estado`, `ck_carga_terminada`, `ck_rechazo_fila_motivo`, `ck_rechazo_fila_pi`, `fk_rechazo_fila_pi` y la consulta de control Q03.
- **Prueba**: «Un defecto de estructura rechaza la carga entera y deja su motivo», «La base no acepta un motivo que no existe» y «Después de un rechazo, un archivo distinto es otro archivo y se publica».

### BR-CARGA-14: Columnas del plan y avisos de columna
- Un encabezado es de PI cuando empieza por un código con la forma número, punto y número seguido de « [» (propuesta), como «5.1 [Total Pts: 4 Score] |9000051». Las columnas «Actividad 01» a «Actividad 18» traen también «[Total Pts», pero no empiezan por un código de PI.
- Solo los encabezados de los PI del plan de la sección entran a `carga_columna` (`fk_carga_columna_plan`), con su posición, el encabezado tal como viene, el número de Blackboard tras «|» (`bb_columna_id`) y el Total Pts que declara (`puntaje_maximo_declarado`). Un encabezado «6.10 [» no pasa como el PI 6.1 (`ck_carga_columna_encabezado`).
- Un Total Pts distinto de 4 deja el AVISO PUNTAJE_MAXIMO_DISTINTO, con `fila_origen` nulo y la `carga_columna_id` de esa columna, y la carga sigue (valor provisional de D-04). En el export inventado la columna 5.3 declara 20 puntos.
- Una columna de un PI que no está en el plan, como «4.1 [Total Pts: 4 Score] |9000041», se ignora con el AVISO COLUMNA_PI_FUERA_DEL_PLAN, con `fila_origen` nulo y `carga_columna_id` nulo.
- Las columnas que no son de PI se descartan al leer (BR-CARGA-17).
- **Fuente**: US-10, FR-015, D-04, `fk_carga_columna_plan`, `ck_carga_columna_encabezado`, `ck_carga_columna_puntaje` y `uq_carga_columna_pi`.
- **Prueba**: «El export correcto queda publicado entero» (columnas 5.1, 5.2 y 5.3 con 4, 4 y 20 puntos), «El 5 de la fila 3 rechaza esa fila completa» (aviso de 5.3) y «Una columna de PI que no está en el plan se ignora con aviso».
- **Cambio del 2026-11-09 (spec 003, US-26, J-19).** Esta regla reemplaza la primera viñeta. Un encabezado es de PI cuando, sin espacios a los lados, sus primeros 200 caracteres, que son los que guarda `carga_columna.encabezado`, cumplen desde el comienzo `(?:[Aa][Bb][Ee][Tt] {0,3})?(?:(?:[Ss][Oo]|[Pp][Ii]) {0,3})?(?P<pi>[0-9]+\.[0-9]+) {0,3}\[`, con `re.ASCII`. Así, «ABET SO5.1 [Total Pts: 100 Score] |9000051», «ABET SO 5.3 […]», «SO 5.1 [», «PI 5.1 [», «abet so5.1 [», «5.1[» y «5.1 [» de la spec 001 son PI, «ABET SO 5.10 [» es el PI 5.10 y nunca el 5.1, y «ABET SO5 [», «Actividad 5.1 [» y «9. Casos de Circularidad [» no son de PI.
  - V1_10 reemplaza `ck_carga_columna_encabezado` por `encabezado ~ ('^([Aa][Bb][Ee][Tt] {0,3})?(([Ss][Oo]|[Pp][Ii]) {0,3})?' || replace(pi_codigo, '.', '\.') || ' {0,3}\[')`, que acepta exactamente lo mismo que el lector, conserva la regla C6 y acepta todo lo que aceptaba el LIKE de V1_07. La misma lista de casos corre en `tests/test_lector.py` y en `db/pruebas/pruebas.sql`.
  - «ABET SO5.1» y «ABET SO 5.1» son el mismo PI, así que dos columnas así en un archivo dan PI_REPETIDO (BR-CARGA-13). Las columnas del export real «ABET SO 4.1» y «ABET SO4.2» quedan fuera del plan de 450002 y dejan cada una el AVISO COLUMNA_PI_FUERA_DEL_PLAN, y cada columna de 100 puntos del plan deja PUNTAJE_MAXIMO_DISTINTO (D-04 y D-30).
  - **Prueba**: «El .xlsx con los encabezados reales queda publicado», «Qué encabezados son de un PI», «La base acepta o rechaza el encabezado de la columna del PI 5.1», «El lector y la base aceptan los mismos encabezados», «Dos columnas del mismo PI con distinta escritura rechazan la carga» y «Las columnas del SO 4 se ignoran con aviso y sin leer sus valores» (`exports_blackboard.feature`).

### BR-CARGA-15: Rechazo de filas
- Una celda inválida rechaza la fila completa con efecto RECHAZA_FILA, y ese estudiante sale de todos los PI de la carga (valor provisional de D-01).
- Un nivel -1, 0 o 5 da NIVEL_FUERA_DE_ESCALA (valor provisional de D-06). Un valor que no es un nivel entero, como «3,5», «Needs Grading», «-» o «NP», da NIVEL_NO_NUMERICO (valor provisional de D-03).
- Una celda de PI vacía no rechaza la fila y se guarda como SIN_EVIDENCIA, con `nivel_original` nulo (`ck_medicion_estado_nivel`).
- El código sale de Username, porque Student ID viene vacío en el export conocido, y si falta la columna Username sale de Student ID (propuesta). Un Username vacío da CODIGO_VACIO, y un código repetido rechaza su segunda aparición con CODIGO_DUPLICADO y conserva la primera (propuesta). Con la guardia apagada, un código mal formado como 9900001 da CODIGO_INVALIDO (`ck_estudiante_codigo`).
- Cada fila aceptada registra su estudiante en `abet.estudiante` o toma el que ya existe con ese código (`uq_estudiante_codigo`).
- Cada fila rechazada deja una sola fila en `rechazo_fila` con su `fila_origen` (`ck_rechazo_fila_con_fila`), el motivo y, si el motivo es de nivel, la `carga_columna_id` del PI, nunca el valor leído. Con varias celdas inválidas manda la primera en el orden código y columnas de PI (propuesta).
- El mensaje de cada rechazo nombra la fila y el motivo, y también el PI cuando el motivo es de nivel, como «Fila 3, PI 5.2, nivel fuera de la escala 1 a 4. La fila completa queda fuera, también de 5.1 y 5.3.». Un rechazo por código (CODIGO_VACIO, CODIGO_DUPLICADO o CODIGO_INVALIDO) no tiene PI, y en la constancia su `pi` es nulo (BR-R17-10).
- Con el export inventado que trae un 5 en el PI 5.2 de la fila 3, la carga lee 11 filas, acepta 10, rechaza 1 y guarda 30 mediciones, y `v_r17_por_pi` da 60,0, 60,0 y 70,0 en 5.1, 5.2 y 5.3.
- **Fuente**: US-10, FR-015, D-01, D-03, D-06, `ck_rechazo_fila_con_fila`, `ck_rechazo_fila_fila`, `uq_carga_fila_estudiante` y la consulta de control Q03.
- **Prueba**: «El 5 de la fila 3 rechaza esa fila completa», «Una celda de PI inválida en la fila 3 rechaza esa fila», «Una celda de PI vacía se carga como SIN_EVIDENCIA y no rechaza la fila», «Un código vacío o repetido rechaza su fila», «Con la guardia apagada, un código mal formado rechaza solo su fila» y «El rechazo dice fila, PI y motivo, nunca el valor leído».
- **Cambio del 2026-11-09 (spec 003, US-29, D-03).** Un texto de nivel vale el entero si, sin espacios a los lados, cumple `[+-]?[0-9]+(?:[.,]0{1,2})?`, como «3.00», «3,00» o «4.0», en un export de texto y en una celda de texto de un libro. «3.50», «1,000», «3.000» y «Needs Grading» siguen en NIVEL_NO_NUMERICO, que rechaza la fila (D-01 y D-03). Un texto con más de cuatro cifras significativas da NIVEL_FUERA_DE_ESCALA sin convertirse a entero, porque `int()` lanza `ValueError` desde las 4 300 cifras. **Prueba**: «El texto de un nivel en el PI 5.2 de la fila 3», «El texto de un nivel dentro de un .xlsx» y «Un nivel con miles de cifras no deja la carga en 500» (`exports_blackboard.feature`).

### BR-CARGA-16: Conciliación y publicación
- El programa cuenta las filas de datos antes de interpretarlas y guarda la cifra en `archivo_origen.filas_de_datos`. Una fila sin ningún valor no cuenta como fila de datos (propuesta).
- Una carga publicada cumple `filas_leidas = filas_de_datos` (`ck_carga_conciliada` y Q01) y `filas_aceptadas + filas_rechazadas = filas_leidas` (`ck_carga_filas`), con una medición por PI y fila aceptada (Q02), una fila de `carga_fila` por fila aceptada (Q12 y Q13) y columnas reconocidas (Q06).
- La carga se publica sola cuando termina con al menos una fila aceptada (`ck_carga_publicable`). Si no acepta ninguna, queda RECHAZADA, por ejemplo con 11 leídas, 0 aceptadas y 11 rechazadas, responde 201 con el mensaje «Ninguna fila se pudo aceptar. La carga no se publicó.» (propuesta), y `carga_fila` y `medicion` no tienen filas de ella.
- Un defecto que deja cuentas que no cuadran choca con `ck_carga_conciliada` o con `ck_carga_filas` al publicar.
- **Fuente**: FR-017, US-07, US-10, `ck_carga_conciliada`, `ck_carga_filas`, `ck_carga_publicable` y las consultas de control Q01, Q02, Q03, Q06, Q12 y Q13.
- **Prueba**: «El export correcto queda publicado entero», «Si todas las filas se rechazan, la carga no se publica» y «La base no deja publicar cuentas que no cuadran».
- **Cambio del 2026-11-09 (spec 003, US-36, D-31).** Una carga que acepta filas sin ningún nivel en las columnas de los PI del plan queda RECHAZADA con SIN_CALIFICACIONES, motivo que agrega V1_10, y RECHAZA_CARGA, con la forma de BR-CARGA-13 (`filas_leidas` 0, una sola fila de `rechazo_fila` y ninguna columna, fila, medición ni aviso) y el mensaje «El archivo no trae ningún nivel en las columnas de los PI del plan. La carga no se publicó.». Si ninguna fila se acepta, sigue el rechazo de esta regla con «Ninguna fila se pudo aceptar. La carga no se publicó.». La sección queda libre, porque `uq_carga_publicada_por_seccion` solo limita las PUBLICADA. **Prueba**: «Un export sin ningún nivel en los PI del plan no se publica», «Un solo nivel basta para publicar» y «La sección queda libre para el export con niveles» (`exports_blackboard.feature`).

### BR-CARGA-17: Descarte de nombres y valores leídos
- La base guarda del estudiante solo su código de 8 dígitos (`ck_estudiante_codigo`) y de cada fila solo las celdas de los PI del plan. El lector descarta al leer Last Name, First Name, Last Access, Availability, las columnas «Actividad 01» a «Actividad 18» y los valores de las celdas.
- `rechazo_fila` solo tiene `rechazo_id`, `carga_id`, `fila_origen`, `carga_columna_id`, `motivo`, `efecto` y `pi_id`, que V1_09 agrega para el PI que falta o que se repite (BR-CARGA-13). Ninguna de estas columnas guarda el valor leído, y ningún rechazo de una respuesta trae un campo `valor` ni `valor_leido`.
- `archivo_origen.nombre_archivo` guarda el nombre sin ruta. Un navegador que envía «C:\Users\docente\Descargas\export_inventado_410_con_error.xlsx» deja `export_inventado_410_con_error.xlsx`, y `ck_archivo_origen_nombre` rechaza un nombre con «/» o «\».
- Ninguna tabla de `abet` ni de `acceso` tiene una columna de tipo `bytea`, así que los bytes del export no se guardan.
- La consulta de control Q04 devuelve 0 filas, y la búsqueda de cada nombre inventado del export en las columnas de texto de `abet` y `acceso` devuelve 0 coincidencias.
- **Fuente**: US-14, FR-018, Principio II de la constitución, `ck_estudiante_codigo`, `ck_archivo_origen_nombre` y la consulta de control Q04.
- **Prueba**: «Los nombres del export no llegan a ninguna tabla», «El rechazo dice fila, PI y motivo, nunca el valor leído», «Las columnas que no son PI del plan se descartan» y «El nombre del archivo se guarda sin ruta».
- **Cambio del 2026-11-09 (spec 003, US-27 y US-28).** El lector de texto descarta las mismas columnas al leer cada registro, así que los nombres, los accesos y los valores de las actividades de un `.csv` o un `.xls`, como «Complete», «Needs Grading» o «19.00», no llegan a ninguna tabla. **Prueba**: «Los nombres y las actividades del .xls no llegan a ninguna tabla» (`exports_blackboard.feature`).

### BR-CARGA-18: Confirmación de la sección (corte 2)
- Un export sin sección declarada en la hoja ni en el nombre responde 422 con «El archivo no indica su sección. ¿Confirma que es de la sección 410 de 450002 en 2026-2?» y `requiere_confirmacion` verdadero, sin escribir nada (propuesta, el código y el campo).
- Con el campo multipart `confirmar_seccion=true`, la carga sigue en la sección elegida, se publica y registra el AVISO SECCION_SIN_DECLARAR de V1_09, con `fila_origen` nulo y `carga_columna_id` nulo, y `subida_por` dice quién confirma.
- El campo solo admite «true», y un número de sección responde 422 con «La sección confirmada no es la sección elegida. No se guardó nada.».
- La confirmación no pasa por encima de una sección declarada distinta, que sigue en SECCION_NO_COINCIDE.
- Esta regla retira para ese caso el 422 del corte 1 de BR-CARGA-11 (T084).
- **Fuente**: US-21, D-02 y `ck_rechazo_fila_motivo` en la versión de V1_09.
- **Prueba**: «Un export que no declara su sección espera la confirmación sin escribir nada», «La sección confirmada publica la carga y la constancia lo dice», «La confirmación no vale si nombra otra sección» y «La confirmación no pasa por encima de una sección declarada distinta».

### BR-CARGA-19: Reemplazo de la carga publicada (corte 2)
- `POST /api/secciones/{seccion_id}/cargas?reemplaza={carga_id}` sigue las reglas de esta spec y, en una sola transacción, deja la carga anterior REEMPLAZADA antes de publicar la nueva con `reemplaza_carga_id` igual a la anterior (`fk_carga_reemplaza`). Nada se borra.
- `reemplaza_carga_id` se fija en el INSERT solo si la carga nueva se publica, lo que la validación en memoria de BR-CARGA-03 sabe antes de escribir. Una carga nueva RECHAZADA lo deja nulo desde el INSERT, sin UPDATE de esa columna, y la anterior sigue PUBLICADA, porque `uq_carga_reemplaza` bloquearía el siguiente reemplazo válido.
- El profesor reemplaza en su sección y el coordinador en cualquiera de la carrera, sin fecha de cierre (valor provisional de D-11). Una sección ajena responde 403 (BR-ACCESO-08).
- El mismo archivo de la carga publicada responde 200 con su constancia y el aviso «Es el mismo archivo de la carga publicada. No se reemplazó.» (propuesta), y `carga` no gana filas.
- Reemplazar una carga que ya no es la PUBLICADA vigente responde 409 (propuesta). Un archivo que no abre responde 422 con «No se pudo abrir el archivo. La carga publicada no cambió.», y nada cambia.
- Volver al export anterior reutiliza su `archivo_id` (BR-CARGA-09), y las consultas de control Q06, Q07, Q10 y Q14 quedan en 0 filas.
- **Fuente**: US-18, FR-025, D-11, `uq_carga_reemplaza`, `ck_carga_reemplaza`, `fk_carga_reemplaza` y `uq_carga_publicada_por_seccion`.
- **Prueba** (`reemplazo_y_cargas.feature`): «El export corregido reemplaza a la carga con el error», «Subir sin pedir el reemplazo no pisa la carga publicada», «Un reemplazo con un archivo ilegible no cambia nada», «Un reemplazo que rechaza todas las filas no quita la carga vigente», «Un reemplazo fallido no bloquea el siguiente», «El mismo archivo de la carga publicada no la reemplaza», «Volver al export anterior reutiliza su archivo», «No se reemplaza una carga que ya no es la vigente», «El profesor no reemplaza la carga de otra sección», «La base impide dos cargas publicadas en la misma sección» y «La base no deja que una carga reemplace a otra de otra sección».

### BR-CARGA-20: Lista de cargas al alcance del usuario (corte 2)
- `GET /api/cargas?seccion_id=` devuelve las cargas al alcance del usuario, de la más reciente a la más antigua. Cada una trae su sección, su estado, sus conteos, el nombre del archivo, los primeros 12 caracteres de la huella y el correo de quien la sube, junto con `iniciada_en` y `terminada_en` con el desfase «-05:00», el motivo de una carga RECHAZADA y la carga a la que reemplaza.
- Sin `seccion_id`, la ruta lista las cargas del periodo vigente al alcance del usuario (propuesta). Un `seccion_id` ajeno responde 403 (BR-ACCESO-08).
- La constancia de una carga REEMPLAZADA sigue disponible y dice qué carga la reemplaza, pero su R-17, el reporte de medición de la sección, responde 409 (BR-R17-01).
- La lista no trae nombres de estudiantes, valores leídos ni rutas locales.
- **Fuente**: US-19 y FR-026.
- **Prueba** (`reemplazo_y_cargas.feature`): «El coordinador ve las cargas de todas las secciones», «El coordinador filtra por sección», «El profesor ve solo las cargas de su sección», «La constancia de una carga reemplazada sigue disponible» y «La lista no expone datos que la base no guarda».

## Verification

Corrida del 2026-10-30 en el Back, rama `feat/001-mvp-carga-r17`, sobre un PostgreSQL 16 desechable que arma la propia suite. La más reciente va primero y cada línea lleva la fecha, el comando, el archivo de prueba y las reglas que cubre.

```text
- 2026-11-09 · uv run --frozen --no-build pytest -q · test_exports_blackboard_feature.py, test_lector.py, test_validacion.py, test_carga.py, test_api_cargas.py, test_generador_exports.py → bloques de la spec 003 en BR-CARGA-03, 05 a 08, 11 y 14 a 17
- 2026-10-30 · uv run --frozen pytest -q tests/aceptacion -rA · test_acceso_feature.py, test_carga_feature.py, test_varias_secciones_feature.py → BR-CARGA-01 a BR-CARGA-07, BR-CARGA-09 a BR-CARGA-17
- 2026-10-30 · uv run --frozen pytest -q tests -rA · test_api_cargas.py, test_carga.py, test_comando.py, test_demo_punta_a_punta.py, test_lector.py, test_validacion.py, test_varias_secciones.py → BR-CARGA-01 a BR-CARGA-17
```

Resultado del 2026-11-09 (spec 003, rama `feat/003-exports-blackboard`, PostgreSQL 18 desechable): suite completa, 1180 passed y 19 skipped in 124.87s (0:02:04), con los 104 casos de `specs/003-exports-blackboard/aceptacion/exports_blackboard.feature` aprobados; el detalle por historia está en `specs/003-exports-blackboard/audit.md`.

Resultado: aceptación, 170 passed, 19 skipped in 116.97s (0:01:56); suite completa, 852 passed, 20 skipped in 241.50s (0:04:01). Las pantallas P1 a P4 tienen sus pruebas en el Front (`npm test`, 8 archivos y 76 pruebas aprobadas), que `audit.md` lista por grupo.

### Resultado por regla

Las columnas de escenarios cuentan los del corte 1 que la regla cita en su **Prueba**. Un escenario omitido o pendiente se nombra en `audit.md`, que lista su razón.

| Regla | Escenarios (aprobados, omitidos, pendientes) | Pruebas unitarias aprobadas | Resultado |
| --- | --- | --- | --- |
| BR-CARGA-01 | 3, 0, 0 | 16 | Aprobada |
| BR-CARGA-02 | 3, 0, 0 | 18 | Aprobada |
| BR-CARGA-03 | 8, 0, 0 | 19 | Aprobada |
| BR-CARGA-04 | 1, 0, 0 | 4 | Aprobada |
| BR-CARGA-05 | 2, 0, 0 | 41 | Aprobada |
| BR-CARGA-06 | 3, 0, 0 | 2 | Aprobada |
| BR-CARGA-07 | 4, 0, 1 | 42 | Aprobada en local; 1 pendiente (ver audit.md) |
| BR-CARGA-08 | 0, 0, 1 | 1 | Parcial, solo prueba unitaria; 1 pendiente (ver audit.md) |
| BR-CARGA-09 | 5, 0, 0 | 17 | Aprobada |
| BR-CARGA-10 | 3, 0, 0 | 5 | Aprobada |
| BR-CARGA-11 | 8, 0, 0 | 56 | Aprobada |
| BR-CARGA-12 | 1, 0, 0 | 3 | Aprobada |
| BR-CARGA-13 | 3, 0, 0 | 27 | Aprobada |
| BR-CARGA-14 | 3, 0, 0 | 31 | Aprobada |
| BR-CARGA-15 | 6, 0, 0 | 56 | Aprobada |
| BR-CARGA-16 | 3, 0, 0 | 13 | Aprobada |
| BR-CARGA-17 | 4, 0, 0 | 18 | Aprobada |
| BR-CARGA-18 | 0, 0, 0 | 0 | Corte 2, pendiente (T088) |
| BR-CARGA-19 | 0, 0, 0 | 0 | Corte 2, pendiente (T088) |
| BR-CARGA-20 | 0, 0, 0 | 0 | Corte 2, pendiente (T088) |
