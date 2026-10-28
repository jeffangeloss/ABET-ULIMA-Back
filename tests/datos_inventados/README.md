# Exports inventados de prueba

Esta carpeta guarda los exports de Blackboard inventados que prueban la carga y el R-17 de la spec 001 (`specs/001-mvp-carga-r17/`). Todo es inventado. Los códigos de estudiante van de 99000001 a 99000011 en la sección 410 y de 99000012 a 99000022 en la 411, los nombres son genéricos («Inventado 01» y «Estudiante») y ningún archivo sale de un export real.

La regla 2 de `scripts/preflight.sh` busca en esta carpeta números de exactamente 8 dígitos que no empiezan con 99. En cada .xlsx que abre como zip lee solo las hojas (`xl/worksheets/*.xml`) y las cadenas compartidas (`xl/sharedStrings.xml`), que son las partes donde van los códigos, y en un .csv, .tsv o .txt lee el texto entero. Los tres .xlsx que no abren como zip y este archivo quedan fuera de esa lectura.

Las demás partes de cada libro que escribe openpyxl, también las de la copia byte a byte del export de ejemplo, traen 27 números de 8 dígitos que no empiezan con 99 y que no son códigos. Son 25 colores de la paleta `indexedColors` de `xl/styles.xml` cuyas 8 cifras hexadecimales no traen letras, y el ángulo de 270 grados de los dos degradados de `xl/theme/theme1.xml`, que el formato escribe multiplicado por 60 000. `tests/test_generador_exports.py` revisa también lo que la regla no lee. Descomprime todas las partes de cada libro, incluso las que conserva el zip cortado, y lee tal como están los bytes de `pdf_renombrado.xlsx` y de `protegido_410.xlsx`. En todo ese contenido exige que cada número de 8 dígitos empiece con 99, salvo en los atributos `rgb` de `xl/styles.xml` y `ang` de `xl/theme/theme1.xml`.

`scripts/generar_exports_inventados.py` escribe los archivos con los mismos bytes en cada corrida. Su plantilla es `export_inventado_410_con_error.xlsx`, la copia byte a byte del export inventado de ejemplo. De esa plantilla copia la hoja `gc_SINTETICO_20262_450002_410_f`, el encabezado, las columnas de identificación y de acceso, las 18 actividades y las columnas de los indicadores de desempeño (performance indicators, PI) 5.1, 5.2 y 5.3, con un puntaje posible de 4, 4 y 20. Los niveles de cada PI salen de los datos de la 410 en `db/pruebas/datos_sinteticos.sql`.

## Archivos

La tabla nombra, junto a cada archivo, las historias de usuario (user stories, US) y los escenarios de `carga.feature`, `r17_constancia.feature` y `reemplazo_y_cargas.feature` que lo usan.

| Archivo | Contenido | Historias y escenarios |
| --- | --- | --- |
| `sintetico_20262_450002_410.xlsx` | Export correcto de la 410, con 11 filas (99000001 a 99000011) y la columna 5.3 de 20 puntos. Es la plantilla con un 3 en el PI 5.2 de la fila 3, el nivel de 99000002, sin otro cambio. Da 63,6 %, 63,6 % y 72,7 % de estudiantes con nivel 3 o 4 en 5.1, 5.2 y 5.3 (7, 7 y 8 de 11). | US-07 «El export correcto queda publicado entero» y los escenarios que suben este export o una copia suya (US-07 a US-13 y US-21), US-15 «R-17 del export correcto», US-16 «Constancia del export correcto en el R-17» y el reemplazo de US-18 |
| `export_inventado_410_con_error.xlsx` | Copia byte a byte del export inventado de ejemplo, con un 5 en el PI 5.2 de la fila 3. Da 11 filas leídas, 10 aceptadas y 1 rechazada por NIVEL_FUERA_DE_ESCALA, y 60,0 %, 60,0 % y 70,0 % (6, 6 y 7 de 10). | US-07 «Otro archivo no entra en una sección que ya tiene carga publicada» y «Dos subidas a la vez dejan una sola publicada», US-10 «El 5 de la fila 3 rechaza esa fila completa», los cuatro escenarios de US-14, US-15 «R-17 del export con el 5 en la fila 3», US-16 «Constancia del export con el 5 en la fila 3», US-18 y la prueba de humo de la tarea T053 |
| `export_inventado_411.xlsx` | Export correcto de la 411, con la hoja `gc_SINTETICO_20262_450002_411_f`, los códigos 99000012 a 99000022 y los niveles de la 410 en orden inverso, que dan los mismos porcentajes. Así la consulta de control Q08 no ve a un estudiante en dos secciones. | US-07 «Un profesor no sube a una sección que no tiene asignada», US-09 «Un archivo rechazado en una sección se publica después en la suya», US-13 «El export de la 411 subido en la 410 se rechaza», US-19 y US-21 «La confirmación no pasa por encima de una sección declarada distinta» |
| `danado_410.xlsx` | Primera mitad de los bytes del export correcto. Empieza como un zip y no abre, porque le falta el directorio central. | US-11, ejemplo «cortada a la mitad de sus bytes», y US-18 «Un reemplazo con un archivo ilegible no cambia nada» |
| `protegido_410.xlsx` | Contenedor de vinculación e incrustación de objetos (Object Linking and Embedding, OLE) con la firma hexadecimal D0 CF 11 E0 y los flujos EncryptionInfo y EncryptedPackage, la forma de un libro cifrado con contraseña. EncryptionInfo trae un descriptor bien formado del cifrado ágil, con sal y valores cifrados inventados, y EncryptedPackage trae bytes pseudoaleatorios. El archivo imita solo esa forma, así que no esconde ninguna clave, ninguna contraseña lo abre y dentro no hay un libro. | US-11, ejemplo «protegida con contraseña» |
| `pdf_renombrado.xlsx` | Documento en formato de documento portátil (Portable Document Format, PDF) inventado, de una página, con un nombre que termina en .xlsx. | US-11, ejemplos «export_410.pdf» y «export_410.xlsx», que suben estos mismos bytes con cada nombre |
| `vacio_410.xlsx` | Encabezado del export correcto sin filas de datos. | US-12, ejemplo ARCHIVO_SIN_FILAS |
| `sin_5_2_410.xlsx` | Export correcto sin la columna del PI 5.2. Conserva 5.1 y la columna 5.3 de 20 puntos. | US-12, ejemplo PI_DEL_PLAN_AUSENTE y «Después de un rechazo, un archivo distinto es otro archivo y se publica», US-15 «Una carga rechazada no tiene R-17» y US-16 «Una carga rechazada también tiene constancia» |
| `sin_username_ni_student_id_410.xlsx` | Export correcto sin las columnas `Username` y `Student ID`. | US-12, ejemplo COLUMNA_CODIGO_AUSENTE |
| `hoja1_sin_seccion.xlsx` | Export correcto con la hoja «Hoja1», que no declara su sección, y un nombre de archivo que tampoco la declara. | US-13 «Un export que no declara su sección se detiene sin dejar rastro», subido como notas.xlsx, y «Si la hoja no declara la sección, se coteja el nombre del archivo», subido como gc_SINTETICO_20262_450002_411_fullgc_2026-10-20.xlsx, y los escenarios de US-21 |

## El export de la guardia

El escenario «Un solo código que no es inventado rechaza el archivo entero sin dejar rastro» (US-08) y la tarea T052 usan el export correcto con un código fuera del rango inventado en la fila 4. Ese archivo nunca entra a esta carpeta, porque la regla 2 lo rechaza. `escribir_export_guardia(ruta)` lo arma en la ruta que elige la prueba, dentro de `tmp_path`, y falla si la ruta cae en esta carpeta, también cuando llega por `..` o con otras mayúsculas, que en la Mac nombran la misma carpeta.

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

Las partes de los .xlsx van comprimidas con deflate, y otra versión de zlib puede dar otros bytes con el mismo contenido. Por eso `tests/test_generador_exports.py` compara esta carpeta con una salida nueva parte por parte, y los escenarios toman la huella de `shasum -a 256` sobre el archivo versionado, nunca de una constante. La misma prueba revisa además que dos corridas dan los mismos bytes, los porcentajes de los exports de la 410 y de la 411 y que cada archivo dañado es lo que dice ser y no abre como libro. También revisa la regla 2 de cada archivo con el alcance de `scripts/preflight.sh` y con el de todas sus partes.
