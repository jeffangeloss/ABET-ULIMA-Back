# Exports inventados de prueba

Esta carpeta guarda los exports de Blackboard inventados que prueban la carga y el R-17 de la spec 001 (`specs/001-mvp-carga-r17/`). Todo es inventado. Los códigos de estudiante van de 99000001 a 99000011 en la sección 410 de 450002, de 99000012 a 99000022 en la 411 y de 99000023 a 99000055 en las tres secciones del profesor con varias secciones, los nombres son genéricos («Inventado 01» y «Estudiante») y ningún archivo sale de un export real.

La regla 2 de `scripts/preflight.sh` busca en esta carpeta números de exactamente 8 dígitos que no empiezan con 99 y lee cada archivo por su contenido, sin mirar la extensión. En cada zip lee solo las hojas (`xl/worksheets/*.xml`) y las cadenas compartidas (`xl/sharedStrings.xml`), que son las partes donde van los códigos, y si `unzip` no puede abrirlo lo lee por sus bytes. Todo lo demás, también los textos UTF-16 y Windows-1252, pasa por `LC_ALL=C tr -d '\000'` antes de contar, y este README se revisa igual. Un contenedor OLE falla la regla, porque sus celdas no se pueden revisar, salvo que su SHA-256 esté en la lista `OLE_REVISADOS` del script, que hoy solo trae `protegido_410.xlsx`.

Las demás partes de cada libro que escribe openpyxl, también las de la copia byte a byte del export de ejemplo, traen 27 números de 8 dígitos que no empiezan con 99 y que no son códigos. Son 25 colores de la paleta `indexedColors` de `xl/styles.xml` cuyas 8 cifras hexadecimales no traen letras, y el ángulo de 270 grados de los dos degradados de `xl/theme/theme1.xml`, que el formato escribe multiplicado por 60 000. `tests/test_generador_exports.py` revisa también lo que la regla no lee. Descomprime todas las partes de cada libro, incluso las que conserva el zip cortado, y lee tal como están los bytes de `pdf_renombrado.xlsx` y de `protegido_410.xlsx`. En todo ese contenido exige que cada número de 8 dígitos empiece con 99, salvo en los atributos `rgb` de `xl/styles.xml` y `ang` de `xl/theme/theme1.xml`.

`scripts/generar_exports_inventados.py` escribe los archivos con los mismos bytes en cada corrida. Su plantilla es `export_inventado_410_con_error.xlsx`, la copia byte a byte del export inventado de ejemplo. De esa plantilla copia la hoja `gc_SINTETICO_20262_450002_410_f`, el encabezado, las columnas de identificación y de acceso, las 18 actividades y las columnas de los indicadores de desempeño (performance indicators, PI) 5.1, 5.2 y 5.3, con un puntaje posible de 4, 4 y 20. Los niveles de cada PI salen de los datos de la 410 en `db/pruebas/datos_sinteticos.sql`. Los tres exports del profesor con varias secciones conservan esas columnas de identificación, de acceso y de actividades, con los ids de Blackboard de su propio curso, y llevan al final las columnas de PI del plan de su asignatura, todas con un puntaje posible de 4.

## Archivos

La tabla nombra, junto a cada archivo, las historias de usuario (user stories, US) y los escenarios de `carga.feature`, `r17_constancia.feature`, `reemplazo_y_cargas.feature` y `varias_secciones.feature` que lo usan.

| Archivo | Contenido | Historias y escenarios |
| --- | --- | --- |
| `sintetico_20262_450002_410.xlsx` | Export correcto de la 410, con 11 filas (99000001 a 99000011) y la columna 5.3 de 20 puntos. Es la plantilla con un 3 en el PI 5.2 de la fila 3, el nivel de 99000002, sin otro cambio. Da 63,6 %, 63,6 % y 72,7 % de estudiantes con nivel 3 o 4 en 5.1, 5.2 y 5.3 (7, 7 y 8 de 11). | US-07 «El export correcto queda publicado entero» y los escenarios que suben este export o una copia suya (US-07 a US-13 y US-21), US-15 «R-17 del export correcto», US-16 «Constancia del export correcto en el R-17», el reemplazo de US-18 y US-06 «El profesor de varias secciones no alcanza una sección que no dicta» de `varias_secciones.feature`, que lo publica en la 410 a nombre de docente410 y lo manda otra vez a esa sección con la sesión de `docente.varias@example.invalid` |
| `export_inventado_410_con_error.xlsx` | Copia byte a byte del export inventado de ejemplo, con un 5 en el PI 5.2 de la fila 3. Da 11 filas leídas, 10 aceptadas y 1 rechazada por NIVEL_FUERA_DE_ESCALA, y 60,0 %, 60,0 % y 70,0 % (6, 6 y 7 de 10). | US-07 «Otro archivo no entra en una sección que ya tiene carga publicada» y «Dos subidas a la vez dejan una sola publicada», US-10 «El 5 de la fila 3 rechaza esa fila completa», los cuatro escenarios de US-14, US-15 «R-17 del export con el 5 en la fila 3», US-16 «Constancia del export con el 5 en la fila 3», US-18 y la prueba de humo de la tarea T053 |
| `export_inventado_411.xlsx` | Export correcto de la 411, con la hoja `gc_SINTETICO_20262_450002_411_f`, los códigos 99000012 a 99000022 y los niveles de la 410 en orden inverso, que dan los mismos porcentajes. Así la consulta de control Q08 no ve a un estudiante en dos secciones. | US-07 «Un profesor no sube a una sección que no tiene asignada», US-09 «Un archivo rechazado en una sección se publica después en la suya», US-13 «El export de la 411 subido en la 410 se rechaza», US-19 y US-21 «La confirmación no pasa por encima de una sección declarada distinta» |
| `danado_410.xlsx` | Primera mitad de los bytes del export correcto. Empieza como un zip y no abre, porque le falta el directorio central. | US-11, ejemplo «cortada a la mitad de sus bytes», y US-18 «Un reemplazo con un archivo ilegible no cambia nada» |
| `protegido_410.xlsx` | Contenedor de vinculación e incrustación de objetos (Object Linking and Embedding, OLE) con la firma hexadecimal D0 CF 11 E0 y los flujos EncryptionInfo y EncryptedPackage, la forma de un libro cifrado con contraseña. EncryptionInfo trae un descriptor bien formado del cifrado ágil, con sal y valores cifrados inventados, y EncryptedPackage trae bytes pseudoaleatorios. El archivo imita solo esa forma, así que no esconde ninguna clave, ninguna contraseña lo abre y dentro no hay un libro. | US-11, ejemplo «protegida con contraseña» |
| `pdf_renombrado.xlsx` | Documento en formato de documento portátil (Portable Document Format, PDF) inventado, de una página, con un nombre que termina en .xlsx. | US-11, ejemplos «export_410.pdf» y «export_410.xlsx», que suben estos mismos bytes con cada nombre |
| `vacio_410.xlsx` | Encabezado del export correcto sin filas de datos. | US-12, ejemplo ARCHIVO_SIN_FILAS |
| `sin_5_2_410.xlsx` | Export correcto sin la columna del PI 5.2. Conserva 5.1 y la columna 5.3 de 20 puntos. | US-12, ejemplo PI_DEL_PLAN_AUSENTE y «Después de un rechazo, un archivo distinto es otro archivo y se publica», US-15 «Una carga rechazada no tiene R-17» y US-16 «Una carga rechazada también tiene constancia» |
| `sin_username_ni_student_id_410.xlsx` | Export correcto sin las columnas `Username` y `Student ID`. | US-12, ejemplo COLUMNA_CODIGO_AUSENTE |
| `hoja1_sin_seccion.xlsx` | Export correcto con la hoja «Hoja1», que no declara su sección, y un nombre de archivo que tampoco la declara. | US-13 «Un export que no declara su sección se detiene sin dejar rastro», subido como notas.xlsx, y «Si la hoja no declara la sección, se coteja el nombre del archivo», subido como gc_SINTETICO_20262_450002_411_fullgc_2026-10-20.xlsx, y los escenarios de US-21 |
| `sintetico_20262_450002_412.xlsx` | Export correcto de la 412 de 450002, con la hoja `gc_SINTETICO_20262_450002_412_f`, 11 filas (99000023 a 99000033) y las columnas 5.1, 5.2 y 5.3 de 4 puntos. Su R-17 da 81,8 % (9 de 11) en 5.1, 54,5 % (6 de 11) en 5.2 y 90,9 % (10 de 11) en 5.3 de estudiantes con nivel 3 o 4. | US-07 «Cada export del profesor de varias secciones se publica solo en su sección», US-06 «El profesor de varias secciones no alcanza una sección que no dicta», que lo sube a la 410 de 450002, y US-09 «Un archivo publicado en una sección del profesor se detiene en otra de sus secciones», que lo sube después en la 410 de 450010, todos de `varias_secciones.feature` |
| `sintetico_20262_450010_410.xlsx` | Export correcto de la 410 de 450010, con la hoja `gc_SINTETICO_20262_450010_410_f`, 11 filas (99000034 a 99000044) y las columnas 2.1, 2.2 y 5.1 de 4 puntos. Su R-17 da 72,7 % (8 de 11) en 2.1, 45,5 % (5 de 11) en 2.2 y 36,4 % (4 de 11) en 5.1 de estudiantes con nivel 3 o 4. | US-07 «Cada export del profesor de varias secciones se publica solo en su sección» y US-13 «El export de una sección del profesor no entra en otra de sus secciones de la misma asignatura», que lo sube en la 412 de 450010, de `varias_secciones.feature` |
| `sintetico_20262_450010_412.xlsx` | Export correcto de la 412 de 450010, con la hoja `gc_SINTETICO_20262_450010_412_f`, 11 filas (99000045 a 99000055) y las columnas 2.1, 2.2 y 5.1 de 4 puntos. Su R-17 da 90,9 % (10 de 11) en 2.1, 63,6 % (7 de 11) en 2.2 y 54,5 % (6 de 11) en 5.1 de estudiantes con nivel 3 o 4. | US-07 «Cada export del profesor de varias secciones se publica solo en su sección» y US-13 «El mismo número de sección en otra asignatura no basta para cargar el export», que lo sube en la 412 de 450002, de `varias_secciones.feature` |
| `gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv` | Export de la 410 con la forma real de Blackboard (spec 003), con 31 columnas, 11 filas (99000001 a 99000011) y Student ID vacío. Va en UTF-8 con BOM, separado por comas, con comillas dobles en todos los campos (`csv.QUOTE_ALL`), saltos LF y salto final. Los niveles de 5.1, 5.2 y 5.3 de `NIVELES_410` van escritos «3.00». Da 63,6 %, 63,6 % y 72,7 % de estudiantes con nivel 3 o 4 (7, 7 y 8 de 11), 33 mediciones y 5 avisos (PUNTAJE_MAXIMO_DISTINTO en 5.1, 5.2 y 5.3 de 100 puntos y COLUMNA_PI_FUERA_DEL_PLAN en 4.1 y 4.2). | US-26 a US-36 de `specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`, que lo sube y arma copias suyas, sobre todo US-27 |
| `gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls` | El mismo contenido en UTF-16 LE con BOM `FF FE`, separado por tabuladores, con comillas dobles y saltos LF. No es un libro de Excel. Mismas cifras. | US-28 y los escenarios que lo comparan con el .csv (mismas notas, otro archivo) |
| `gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-36-02.xlsx` | Libro con la hoja `gc_SINTETICO_20262_450002_410_f`, Username como entero, Student ID vacío, la fecha de acceso como fecha y los niveles como números. Mismas cifras. | US-26 «El .xlsx con los encabezados reales queda publicado» y los escenarios de US-29 y US-30 que lo suben |
| `gc_SINTETICO_20262_450002_411_fullgc_2026-11-04-14-40-10.xls` | Como el .xls de la 410, con los códigos 99000012 a 99000022, «Inventado 12» a «Inventado 22» y los niveles de la 410 en orden inverso, como `export_411`. Mismas cifras. | US-30, el cotejo de la sección con el nombre del export de texto, y US-28 |

## El profesor con varias secciones

Tres exports prueban que un profesor que dicta varias secciones de varias asignaturas sube cada export solo en la sección que le corresponde, como piden las reglas de negocio (business rules, BR) BR-ACCESO-07, BR-ACCESO-08, BR-CARGA-09 y BR-CARGA-11. El profesor es `docente.varias@example.invalid`, que `db/datos/varias_secciones_2026_2_inventado.sql` registra en 2026-2 con la 412 de 450002 y con la 410 y la 412 de 450010. Cada export declara su sección en la hoja `gc_SINTETICO_20262_<asignatura>_<sección>_f`, que coincide con el curso de Blackboard de esa sección en la base, y trae las columnas del plan de su asignatura, 5.1, 5.2 y 5.3 en 450002 y 2.1, 2.2 y 5.1 en 450010. Las dos secciones 412 de asignaturas distintas prueban que el mismo número de sección en otra asignatura no se confunde.

Las columnas de PI declaran un puntaje posible de 4, así que estas cargas no llevan el aviso PUNTAJE_MAXIMO_DISTINTO de la columna 5.3 de 20 puntos del export de ejemplo. Los ids de Blackboard de cada export pertenecen al curso de su sección, porque cada curso de Blackboard numera sus columnas por su cuenta, y empiezan con 9001 en la 412 de 450002, con 9002 en la 410 de 450010 y con 9003 en la 412 de 450010. Los códigos de las tres secciones no se repiten entre ellas ni con los de la 410 y la 411, de modo que la consulta de control Q08 sigue en 0 filas con todas las cargas publicadas. Los tres archivos tienen además huellas distintas, así que el export publicado en una sección no detiene en la búsqueda de la huella el de otra. El export de la 410 de 450010 subido en la 412 no tiene la huella registrada, pasa esa búsqueda y se detiene en el cotejo de la hoja con SECCION_NO_COINCIDE.

Los niveles dan en cada sección un porcentaje distinto para cada PI, también en el 5.1, que miden las dos asignaturas, así que el R-17 de cada sección se reconoce por sus cifras. La tabla da esas cifras esperadas por PI, con los estudiantes de cada nivel y la proporción con nivel 3 o 4 sobre los 11 calificados. La sección 9 de `db/pruebas/pruebas.sql` las comprueba en `abet.v_r17_por_pi`, y `tests/test_generador_exports.py` las calcula aparte desde cada libro.

| Sección | PI | Nivel 1 | Nivel 2 | Nivel 3 | Nivel 4 | Nivel 3 o 4 |
| --- | --- | --- | --- | --- | --- | --- |
| 412 de 450002 | 5.1 | 1 | 1 | 5 | 4 | 81,8 % (9 de 11) |
| 412 de 450002 | 5.2 | 2 | 3 | 4 | 2 | 54,5 % (6 de 11) |
| 412 de 450002 | 5.3 | 0 | 1 | 4 | 6 | 90,9 % (10 de 11) |
| 410 de 450010 | 2.1 | 1 | 2 | 4 | 4 | 72,7 % (8 de 11) |
| 410 de 450010 | 2.2 | 2 | 4 | 3 | 2 | 45,5 % (5 de 11) |
| 410 de 450010 | 5.1 | 3 | 4 | 3 | 1 | 36,4 % (4 de 11) |
| 412 de 450010 | 2.1 | 0 | 1 | 5 | 5 | 90,9 % (10 de 11) |
| 412 de 450010 | 2.2 | 1 | 3 | 5 | 2 | 63,6 % (7 de 11) |
| 412 de 450010 | 5.1 | 2 | 3 | 3 | 3 | 54,5 % (6 de 11) |

Los seis escenarios de `specs/001-mvp-carga-r17/aceptacion/varias_secciones.feature` usan estos exports como resume la tabla.

| Escenario | Export | Sección elegida | Resultado |
| --- | --- | --- | --- |
| US-06 «El profesor de varias secciones ve sus tres secciones y ninguna otra» | Ninguno | Ninguna | `GET /api/secciones?periodo=2026-2` y la pantalla P2 «Mis secciones» muestran sus tres secciones con los PI de su plan y el estado de carga SIN_CARGA, sin ningún dato de la 410 ni de la 411 de 450002 |
| US-07 «Cada export del profesor de varias secciones se publica solo en su sección» | Los tres, uno por ejemplo | La que declara su hoja | 201 con el estado PUBLICADA y 11 filas leídas, 11 aceptadas y 0 rechazadas, una sola carga PUBLICADA en esa sección y ninguna carga de ese archivo en las otras dos |
| US-13 «El export de una sección del profesor no entra en otra de sus secciones de la misma asignatura» | `sintetico_20262_450010_410.xlsx` | 412 de 450010 | 201 con la carga RECHAZADA, el motivo SECCION_NO_COINCIDE con RECHAZA_CARGA y el mensaje «El archivo corresponde a la sección 410 y usted eligió la 412. No se publicó.», sin carga PUBLICADA en la 412 ni carga en la 410 y sin los códigos del archivo en `abet.estudiante` |
| US-13 «El mismo número de sección en otra asignatura no basta para cargar el export» | `sintetico_20262_450010_412.xlsx` | 412 de 450002 | 201 con la carga RECHAZADA, el motivo SECCION_NO_COINCIDE con RECHAZA_CARGA y el mensaje de asignatura de BR-CARGA-11, «El archivo corresponde a la asignatura 450010 y usted eligió la 450002. No se publicó.», sin carga PUBLICADA en la 412 de 450002 ni carga en la 412 de 450010 |
| US-06 «El profesor de varias secciones no alcanza una sección que no dicta», con dos subidas, la constancia y el R-17 | `sintetico_20262_450002_412.xlsx` en una subida y `sintetico_20262_450002_410.xlsx`, ya publicado en esa sección, en la otra. Las dos reciben el 403 antes de la búsqueda de la huella y del cotejo de la hoja (BR-CARGA-03, paso 1) | 410 de 450002, con la carga PUBLICADA de `sintetico_20262_450002_410.xlsx` que sube docente410 | 403 con «La sección no está a su cargo.» al subir, al leer su carga y al pedir su R-17, sin datos de esa sección y sin filas nuevas en `abet.archivo_origen`, `abet.carga` ni `abet.estudiante` |
| US-09 «Un archivo publicado en una sección del profesor se detiene en otra de sus secciones» | `sintetico_20262_450002_412.xlsx`, publicado antes en la 412 de 450002 | 410 de 450010 | 409 con «Este archivo ya está publicado en otra sección. No se cargó.», sin datos de la otra sección y sin carga nueva, porque la huella se busca antes que la sección (BR-CARGA-03) |

## El export de la guardia

El escenario «Un solo código que no es inventado rechaza el archivo entero sin dejar rastro» (US-08) y la tarea T052 usan el export correcto con un código fuera del rango inventado en la fila 4. Ese archivo nunca entra a esta carpeta, porque la regla 2 lo rechaza. `escribir_export_guardia(ruta)` lo arma en la ruta que elige la prueba, dentro de `tmp_path`, y falla si la ruta cae en esta carpeta, también cuando llega por `..` o con otras mayúsculas, que en la Mac nombran la misma carpeta.

## Exports con la forma real de Blackboard

Los cuatro archivos de la spec 003 los escribe el mismo generador, sin la plantilla de la spec 001. Las 31 columnas siguen este orden. «Last Name», «First Name», «Username», «Student ID», «Last Access» y «Availability», y luego las actividades con sus títulos reales, que no traen datos de personas. Las columnas 25, 28, 29, 30 y 31 son «ABET SO5.1», «ABET SO5.2», «ABET SO 5.3», «ABET SO 4.1» y «ABET SO4.2», con 100 puntos y los ids 9000051, 9000052, 9000053, 9000041 y 9000042. Los números de columna de Blackboard son inventados, de 7 cifras y empiezan con 9 (9000101 a 9000120 en las demás), y nunca los reales, que empiezan con 16.

Cada fila lleva «Inventado NN», «Estudiante», el Username, Student ID vacío, el último acceso fijo (`2026-10-21 21:43`), Availability «Yes», las actividades con «Complete», «Incomplete», «Needs Grading» y «19.00» repartidos de forma fija y, en 5.1, 5.2 y 5.3, los niveles de `NIVELES_410`. «ABET SO 4.1» y «ABET SO4.2» van vacías. Los saltos de línea son LF en todos los archivos, y las copias con CRLF las arman las pruebas en `tmp_path`.

Los pasos de aceptación arman sus copias con estas funciones públicas del generador.

| Función | Qué hace |
| --- | --- |
| `leer_export_texto(datos, hoja="", separador=None)` | Lee bytes de un .csv o .xls de texto a un `Export` de celdas de texto. Detecta UTF-16 LE, UTF-8 con BOM y UTF-8 sin BOM, y la coma o el tabulador por el encabezado. `hoja` no se usa para el texto y solo se copia. |
| `leer_export_texto_versionado(nombre, carpeta=...)` | Lo mismo con un archivo versionado de esta carpeta, por su nombre. |
| `a_texto(export, separador=",", codificacion="utf-8-sig", salto="\n", comillas=True)` | Bytes del export como texto. `separador` es coma o tabulador, `codificacion` es `utf-8`, `utf-8-sig` (con BOM) o `utf-16` (UTF-16 LE con BOM), `salto` es LF o CRLF y `comillas=True` cita todos los campos, mientras `False` los cita solo donde hace falta. Escribe siempre el salto final. |
| `escribir_texto(export, destino, **opciones)` | Escribe `a_texto` en `destino` y devuelve la ruta. |
| `export_real_410(texto=True)` y `export_real_411()` | Arman los `Export` de los archivos de esta tabla. `texto=False` da el contenido del libro. |
| `encabezado_real()` | Las 31 columnas con sus ids inventados. |
| `Export.indice("5.2")` | Encuentra también «ABET SO5.2 […]» y «ABET SO 5.3 […]» con la regla J-19, `(?:[Aa][Bb][Ee][Tt] {0,3})?(?:(?:[Ss][Oo]|[Pp][Ii]) {0,3})?5\.2 {0,3}\[` al comienzo del encabezado, y sigue encontrando «5.2 [». |

```python
export = generador.leer_export_texto_versionado("gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv")
copia = generador.con_celda(export, 3, "5.2", "NP")
generador.escribir_texto(copia, tmp_path / "copia.csv", salto="\r\n", comillas=False)
```

## Copias que arman las pruebas

Los demás ejemplos de `carga.feature` dicen «una copia de X con …» y no se versionan. Los pasos de la tarea T050 los arman en `tmp_path` con las funciones del generador, a partir del export correcto. Así salen el 5, el 0, el -1, «3,5», «Needs Grading», «-» y «NP» en el PI 5.2 de la fila 3, la celda vacía, el Username vacío o repetido, la columna 4.1 fuera del plan, la segunda columna 5.1 y las hojas renombradas.

```python
plantilla, _ = generador.leer_plantilla()
copia = generador.con_celda(generador.export_410(plantilla), 3, "5.2", "NP")
generador.escribir(copia, tmp_path / "copia.xlsx")
```

La fixture `generador` de `tests/conftest.py` carga el módulo por su ruta, porque `scripts/` no es un paquete.

## Cómo se regeneran

Los comandos corren desde la raíz del repositorio, con el entorno que deja `uv sync`.

```bash
uv run python -I scripts/generar_exports_inventados.py
uv run pytest -q tests/test_generador_exports.py
```

Antes de escribir, el generador compara la huella de la plantilla, calculada con el algoritmo de resumen seguro de 256 bits (Secure Hash Algorithm, SHA-256), con la que empieza por `2b94db8d`. Si no coincide, termina con error y no escribe nada. `--salida` escribe en otra carpeta, y `--plantilla` lee la plantilla de otra ruta, por ejemplo de la copia original del export de ejemplo si la de esta carpeta se pierde.

Las partes de los .xlsx van comprimidas con deflate, y otra versión de zlib puede dar otros bytes con el mismo contenido. Por eso `tests/test_generador_exports.py` compara esta carpeta con una salida nueva parte por parte, y los escenarios toman la huella de `shasum -a 256` sobre el archivo versionado, nunca de una constante. La misma prueba revisa además que dos corridas dan los mismos bytes, los porcentajes de los exports de la 410 y de la 411 y que cada archivo dañado es lo que dice ser y no abre como libro. También revisa la regla 2 de cada archivo con el alcance de `scripts/preflight.sh` y con el de todas sus partes. En los tres exports del profesor con varias secciones compara las cifras del R-17 que calcula desde cada libro con las que escribe a mano y con las de esta carpeta. Comprueba también que sus columnas y sus niveles son los de la sección 9 de `db/pruebas/pruebas.sql` y que ninguna sección comparte códigos, huella, ids de Blackboard ni el porcentaje de un PI con otra.
