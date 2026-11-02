# Plantilla del R-17

Esta carpeta guarda la plantilla del R-17, el reporte de medición de los indicadores de desempeño (performance indicators, PI) de una sección, y el logotipo que `abet_carga/r17.py` le vuelve a insertar (T034 y T035 de `specs/001-mvp-carga-r17/tasks.md`). `R017_ambiental_general.xlsx` es la hoja «Cursos de Carrera» de la plantilla oficial de Ingeniería Ambiental, vaciada de todo dato, y `R017_logotipo.png` es su logotipo en formato de gráficos de red portátiles (Portable Network Graphics, PNG). Las reglas de negocio (business rules, BR) que la plantilla sirve están en `specs/features/r17/r17.spec.md`, de BR-R17-02 a BR-R17-08.

## Origen

La fuente es «Plantilla Base - Final.xlsx», el libro de la carrera que vive en la carpeta `infodata/` del proyecto, fuera de este repositorio, y que nunca se versiona. El vaciado trabaja sobre una copia hecha con `cp`, cuya huella SHA-256 (Secure Hash Algorithm de 256 bits) es `a46e9353ff1ba1c6f022f1e7e4f376b0cb72f6bd61c6484222f0cb4cbafef4d0`, y la fuente queda sin cambios. Lo hace el 2026-10-28 un guion de un solo uso con openpyxl 3.1.5 y Pillow 12.3.0, que no se versiona porque lee el archivo real. Sus pasos son estos, en orden.

1. Comprueba la huella de la copia y no escribe nada si no coincide.
2. Reguarda con Pillow el logotipo de `xl/media/image1.png` desde sus píxeles, sin los trozos `sRGB`, `gAMA` ni `pHYs`, como `R017_logotipo.png`.
3. Abre la copia con `openpyxl.load_workbook(keep_links=False)`, borra las otras cuatro hojas y retira de «Cursos de Carrera» la imagen, los comentarios y las validaciones de datos.
4. Vacía las 15 celdas con datos o fórmulas que lista la tabla de abajo y deja la selección en A1. Si queda un valor fuera de los 32 rótulos, se detiene sin escribir la plantilla.
5. Fija el creador y el último autor en «ABET_SIS_MED» y la creación y la modificación en `2026-10-28T00:00:00Z`, guarda y reescribe el zip con la fecha fija 1980-01-01 en cada parte, así que dos corridas dan los mismos bytes.

Una segunda corrida del mismo día, sobre una copia nueva con la misma huella, da los mismos bytes, con la huella `2ff9e4ade2c3c3a5f0f03d81dadc23527095ebe87565576a61e2fc8ca2ed6a95` para la plantilla y `cf6e379b3b750eede86aacecfff5b63023766bc1e0e7cb4829decd81831611e3` para el logotipo.

El libro resultante tiene 11 partes, que son `[Content_Types].xml`, `_rels/.rels`, `docProps/app.xml`, `docProps/core.xml`, `xl/workbook.xml` con su `.rels`, `xl/styles.xml`, `xl/theme/theme1.xml`, `xl/worksheets/sheet1.xml` con su `.rels` y `xl/tables/table1.xml`. Los 32 rótulos van como texto dentro de la hoja, porque openpyxl 3.1.5 escribe las cadenas en línea y no crea `xl/sharedStrings.xml`. Fuera de los rótulos, las partes traen solo textos de estructura, que son las dos propiedades fijas, el nombre y la versión de openpyxl, los tres umbrales de los formatos condicionales y los nombres de la hoja, de la tabla, de sus columnas y de su estilo, de dos estilos de celda y del tema de Office.

## Lo que se retiró

La tabla cuenta lo retirado por categoría, sin copiar ningún valor. La tabla de estudiantes y las celdas de la cabecera ya vienen vacías en la fuente, y el libro entero no trae correos, firmas, fechas en sus celdas ni números de 8 dígitos.

| Categoría | Cantidad | Dónde estaba |
| --- | --- | --- |
| Hojas | 4 | La hoja de cursos Capstone, la base de asignaturas con sus resultados del estudiante (student outcomes, SO), la matriz de asignaturas con competencias e instrumentos y la hoja de PI con su rúbrica, con 535 textos, 306 números, 208 fórmulas, 3 tablas, 2 comentarios, 1 imagen, 4 validaciones y 6 formatos condicionales en total |
| Fórmulas de «Cursos de Carrera» | 8 | Dos búsquedas con `#REF!` (D8 y C17), tres mensajes del plan de acción (H24 a H26) y tres conteos (M24 a M26) |
| Textos del instrumento de un curso | 3 | E17, G17 y C24 |
| Metas escritas como número | 3 | G24 a G26 |
| Texto suelto fuera del reporte | 1 | J41, un texto que forma parte de un encabezado de la tabla de la hoja de Capstone |
| Validaciones de datos con `#REF!` | 2 | Listas de D9:I9 y de F43:F184 |
| Comentarios | 2 | D8 y B15, de 1 autor, con su dibujo en lenguaje de marcado vectorial (Vector Markup Language, VML) |
| Imágenes | 1 | El logotipo, que pasa a `R017_logotipo.png` |
| Propiedades con personas | 3 | El creador y el último autor de `docProps/core.xml` y la empresa de `docProps/app.xml` |
| Fechas | 2 | La creación y la modificación del libro, reemplazadas por la fecha fija |
| Rastros del archivo | 2 | La ruta absoluta (`absPath`) y el identificador de coautoría (`revisionPtr`) de `xl/workbook.xml` |
| Identificadores de revisión | 56 | Los atributos `xr:uid`, `xr2:uid` y `xr3:uid` de la vista del libro, las 5 hojas, las 6 validaciones, las 4 tablas con sus 4 filtros, sus 32 columnas y los 4 comentarios |
| Partes del zip | 24 de 35 | Las hojas retiradas con sus relaciones y tablas, los dos dibujos con su VML y la imagen, los comentarios, tres configuraciones de impresora (`printerSettings`), la cadena de cálculo (`calcChain.xml`) y las 297 cadenas compartidas del libro entero (`xl/sharedStrings.xml`) |

## Lo que trae la hoja original y lo que openpyxl pierde

La tabla resume el inventario de «Cursos de Carrera» parte por parte del zip y lo que hace openpyxl 3.1.5 al guardar, comprobado el 2026-10-28 con una ida y vuelta de la copia. Con Pillow instalado, openpyxl conserva las imágenes y los gráficos que sabe leer, y pierde siempre las formas, así que lo único que pierde de esta hoja son rastros sin efecto visible.

| Pieza de la hoja original | Cantidad | Qué hace openpyxl al guardar | Qué queda en la plantilla |
| --- | --- | --- | --- |
| Imagen del logotipo, en `xl/drawings/drawing2.xml`, que comparte `xl/media/image1.png` con la hoja de Capstone | 1 | La conserva con los mismos bytes y la misma ancla, sin sus extensiones de Office 2010 (`a16:creationId`, `a14:useLocalDpi` y `a14:hiddenFill`). Sin Pillow la descarta sin aviso | Nada, porque `r17.py` inserta `R017_logotipo.png` y la salida tiene un solo logotipo |
| Gráficos | 0 | Conserva los que sabe leer | Nada |
| Formas de dibujo | 0 | Las pierde siempre | Nada |
| Comentarios, con 2 formas de nota en su VML | 2 | Los conserva y rehace su VML | Nada |
| Validaciones de datos, las dos con `#REF!` | 2 | Las conserva | Nada |
| Formatos condicionales, en E24:F26 y M26 | 7 reglas | Las conserva. La regla de prioridad 4 de E24:F26 pasa del estilo diferencial 43 al 13, que es idéntico, y tres estilos pierden `patternType="none"` y dos `<i val="0"/>`, sin cambio visible porque E24:F26 no tiene relleno ni cursiva | Las 7 reglas |
| Tabla `Tabla26` | 1 | La conserva | La tabla |
| Configuración de impresora (`printerSettings1.bin`) | 1 | La pierde, junto con el `r:id` de `pageSetup` | La página A4 vertical de `pageSetup` |
| Atributos `xr:uid`, `x14ac:dyDescent` y `spans` | Varios | Los pierde, sin cambio visible | Nada |

La plantilla conserva además los 32 rótulos, las 45 celdas combinadas, los anchos de las columnas A a L, los altos de las filas, el estilo de cada celda, la vista sin cuadrícula al 90 % y el color de la pestaña. Una comparación celda por celda de la fuente y la plantilla, del 2026-10-28, no encuentra ningún estilo distinto.

## Logotipo

`R017_logotipo.png` mide 176 × 173 píxeles en modo RGBA (rojo, verde, azul y transparencia) y trae solo los trozos `IHDR`, `IDAT` e `IEND`, con los mismos píxeles de la fuente. En la fuente se ancla con `twoCellAnchor` y `editAs="oneCell"`. Las medidas van en unidades métricas inglesas (English Metric Units, EMU), con 9525 por píxel a 96 puntos por pulgada.

| Dato | Valor |
| --- | --- |
| Desde | Columna B (`col` 1) con `colOff` 19 050 y fila 1 (`row` 0) con `rowOff` 0 |
| Hasta | Columna B (`col` 1) con `colOff` 744 818 y fila 4 (`row` 3) con `rowOff` 140 297 |
| Tamaño visible | 725 768 × 711 797 EMU, unos 76 × 75 píxeles o 2,02 × 1,98 cm |

`r17.py` repite esa ancla, o una de una celda en B1 con el mismo desplazamiento y la misma extensión, como en este ejemplo (propuesta). El ejemplo, probado el 2026-10-28 sobre esta plantilla, deja un solo dibujo con esa ancla y los mismos bytes del PNG, y openpyxl lo vuelve a leer como una imagen.

```python
from openpyxl.drawing.image import Image
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, TwoCellAnchor

logotipo = Image("plantillas/R017_logotipo.png")
logotipo.anchor = TwoCellAnchor(editAs="oneCell", _from=AnchorMarker(col=1, colOff=19050, row=0, rowOff=0),
                                to=AnchorMarker(col=1, colOff=744818, row=3, rowOff=140297))
hoja.add_image(logotipo)
```

## Mapa de celdas que usa r17.py

`r17.py` escribe valores, nunca fórmulas, en estas celdas de «Cursos de Carrera» (BR-R17-04). Todas están vacías en la plantilla, y `tests/test_plantilla_r17.py` comprueba sus rótulos, sus celdas combinadas, sus formatos y que no traen valor. Lo marcado «(propuesta)» no lo fija la spec, y la primera celda de cada rango combinado es la que recibe el valor. El mapa vale para cualquier asignatura del plan de medición, y el apartado «Cualquier asignatura del plan» fija lo que cambia con el número de PI y de SO.

### Cabecera y franja PROVISIONAL

| Celda | Rótulo vecino | Contenido | Fuente |
| --- | --- | --- | --- |
| D8 (D8:I8) | «Código:» en B8:C8 | Código de la asignatura, como «450002» | `v_r17_por_pi.codigo_asignatura` |
| D9 (D9:I9) | «Asignatura:» en B9:C9 | Nombre de la asignatura | `v_r17_por_pi.asignatura` |
| D10 (D10:I10) | «Profesor:» en B10:C10 | Vacía, porque el R-17 no lleva el nombre del profesor (D-12 y BR-R17-07) | Ninguna |
| D11 (D11:G11) | «Sección:» en B11 | Sección, como «410» | `v_r17_por_pi.seccion` |
| I11 | «Período:» en H11 | Periodo, como «2026-2» | `v_r17_por_pi.periodo` |
| B7:I7 | Bajo el título de E6 | Fila libre y sin combinar. `r17.py` la combina y escribe la franja solo si `v_r17_por_pi.provisional` es verdadero (BR-R17-05) | `v_r17_por_pi.provisional` y `conjunto_reglas` |

### Bloque I, filas fijas de PI 17 a 19

Una fila por PI del plan, ordenados por SO y por número de PI (`abet.pi.so_numero` y `abet.pi.numero`). B15:I15 conserva el rótulo «Student Outcome (SO)», y `r17.py` le agrega el número del SO, como «Student Outcome (SO) 5» (propuesta), desde `v_r17_por_pi.so`.

| Celdas | Contenido | Fuente |
| --- | --- | --- |
| B17, B18 y B19 | Código del PI, como «5.1» | `v_r17_por_pi.pi` |
| C17:D17, C18:D18 y C19:D19 | Descripción del PI (propuesta) | `abet.pi.descripcion` |
| E17:F17, E18:F18 y E19:F19 | Instrumento de medición (propuesta) | `abet.instrumento.nombre` del plan de medición |
| G17:I17, G18:I18 y G19:I19 | Descripción del instrumento, vacía y editable | Ninguna, porque la base no la guarda |

### Bloque II, filas fijas de PI 24 a 26

Las filas siguen el orden del bloque I.

| Celdas | Contenido | Fuente | Formato |
| --- | --- | --- | --- |
| B24, B25 y B26 | Código del PI | `v_r17_por_pi.pi` | General |
| C24:D24, C25:D25 y C26:D26 | Instrumento de medición (propuesta) | El mismo del bloque I | General |
| E24:F24, E25:F25 y E26:F26 | Porcentaje de logro sobre calificados, como fracción | `pct_logro_sobre_calificados` / 100 | `0%` en la plantilla. `r17.py` aplica `0.0%` para mostrar 63,6 % (BR-R17-02) |
| G24, G25 y G26 | Meta, como fracción | `meta_logro_pct` / 100 | `0.00%` |
| H24:I24, H25:I25 y H26:I26 | Plan de acción | La fórmula de la fuente elige entre dos textos fijos con el umbral de 0,8 que usan también los formatos condicionales, «¡Felicidades! Logró alcanzar el indicador. Lo animamos a seguir mejorando con nuevas iniciativas.» si E lo alcanza y «El indicador aún no alcanza lo esperado, pero es una buena oportunidad para mejorar» si no. `r17.py` escribe el texto que corresponde con `meta_logro_pct` de la carga (propuesta) | General |
| M24 | Estudiantes con nivel 1 o 2, sumados sobre todos los PI | Suma de `n_nivel_1` y `n_nivel_2` | `0` |
| M25 | Estudiantes con nivel 3 o 4, sumados sobre todos los PI | Suma de `n_nivel_3` y `n_nivel_4` | `0` |
| M26 | M25 / (M24 + M25) | Calculado por `r17.py` | `0%` |

M24 a M26 repiten lo que calculaban las fórmulas de la fuente sobre F43:F184, que cuentan las mediciones de todos los PI juntas. E24:F26 trae seis reglas de formato condicional con umbrales fijos de 0,75, 0,79 y 0,8, con fuente roja por debajo de 0,8, y M26 trae una regla verde por encima de 0,8. Esos umbrales no siguen `META_LOGRO`, así que con una meta de 70 % los colores quedan en 80 %.

### Recuadros y tabla de estudiantes

| Celdas | Contenido | Fuente |
| --- | --- | --- |
| B29:I31 | Recuadro de causas, bajo el rótulo A. de B28, vacío y editable (BR-R17-04) | Ninguna |
| B34:I36 | Recuadro de acciones, bajo el rótulo B. de B33:H33, vacío y editable (BR-R17-04) | Ninguna |
| B42:F184 | Tabla `Tabla26`, con estilo `TableStyleLight10`, filtro y encabezados en la fila 42 | Ninguna |
| B43 a B184 | SO | `abet.pi.so_numero` |
| C43 a C184 | PI | `abet.pi.codigo` |
| D43 a D184 | Profesor, vacía (D-12) | Ninguna |
| E43 a E184 | Código del estudiante | `abet.estudiante.codigo` |
| F43 a F184 | Calificación, vacía en una medición SIN_EVIDENCIA (propuesta) | `abet.medicion.nivel_original` |

La tabla tiene 142 filas, de la 43 a la 184, una por medición de la carga, ordenadas por PI y por fila de origen, así que con 3 PI caben 47 estudiantes (BR-R17-08). Una carga con más de 142 mediciones recibe la respuesta 422 en lugar de una tabla truncada (propuesta de BR-R17-08), y el rango de la tabla no cambia.

### Cualquier asignatura del plan

Ninguna celda del mapa depende de 450002. La cabecera sale de `v_r17_por_pi` para el `carga_id`, y los bloques y la tabla salen de los PI que `abet.plan_medicion` fija para la asignatura y el periodo de la sección. En el catálogo AMB-2026 (`V1_03__cargar_referencia_ambiental.sql`), cada SO tiene 2 o 3 PI, así que el plan de un solo SO cabe siempre en las tres filas fijas. En `abet.asignatura_so`, en cambio, 27 de las 37 asignaturas tributan a un SO, 9 a dos y 1 a tres, y el plan de esas 10 puede pasar de 3 PI.

| Caso | Qué hace `r17.py` con la plantilla |
| --- | --- |
| Plan de k PI, con k de 1 a 3 | Llena las filas 17 a 16 + k del bloque I y 24 a 23 + k del bloque II, y deja vacías las demás, con su formato |
| PI sin instrumento en el plan (`plan_medicion.instrumento_id` nulo) | Deja vacías en su fila E:F del bloque I y C:D del bloque II |
| PI sin mediciones calificadas | Escribe el PI y sus conteos y deja vacío el porcentaje, porque la vista lo da nulo y nunca como logrado (H80 de `R__vista_r17_por_pi.sql`) |
| Plan con PI de varios SO | El rótulo de B15 lleva los números de los SO, como «Student Outcome (SO) 2 y 7» (propuesta), y la columna B de la tabla, el SO de cada PI |
| Plan de más de 3 PI | No cabe en las filas fijas, y ninguna regla de la spec lo resuelve. La salida queda para T035 y para la coordinación (D-08), sin truncar los bloques, como BR-R17-08 pide para la tabla (propuesta) |
| Tabla de estudiantes con k PI | Caben 142 / k estudiantes, redondeado hacia abajo, que son 142 con 1 PI, 71 con 2 y 47 con 3 |

### Lo que la hoja no trae

Estas piezas de la spec no tienen celda en la hoja original, y `r17.py` las agrega con sus propios rótulos.

| Pieza | Regla | Propuesta |
| --- | --- | --- |
| Conteo por nivel de cada PI (`n_nivel_1` a `n_nivel_4`), la cifra «(7 de 11)» y el porcentaje sobre el total con SIN_EVIDENCIA | BR-R17-02, BR-R17-03 y D-05 | Una tabla en K28:Q31, con «PI», «Nivel 1» a «Nivel 4», «Logran / calificados» y «% sobre el total» en la fila 28 y una fila por PI de la 29 a la 31, en la zona libre a la derecha de los recuadros (propuesta) |
| Recuadro de comentario | BR-R17-04 | La hoja trae solo los recuadros de causas y de acciones, así que la spec o la coordinación (D-08) decide si el plan de acción hace de comentario |
| Un cuarto PI | BR-R17-02 | Los bloques I y II tienen tres filas fijas, y un plan con más PI no cabe sin un cambio de la plantilla (apartado «Cualquier asignatura del plan») |
| Hoja «Constancia» y título con «PROVISIONAL» | BR-R17-05 y BR-R17-09 | `r17.py` agrega la hoja al final del libro y fija el título de las propiedades |

## Cómo se prueba

Los comandos corren desde la raíz del repositorio.

```bash
uv run --frozen pytest -q tests/test_plantilla_r17.py
bash scripts/preflight.sh
bash scripts/probar_preflight.sh
```

`tests/test_plantilla_r17.py` abre la plantilla con openpyxl y revisa la hoja, los 32 rótulos de la lista cerrada, el mapa, la estructura, las propiedades sin personas y con fechas fijas, las 11 partes de la lista cerrada del zip, cada texto de cada parte y el logotipo, y cada revisión corre también sobre una copia alterada que debe fallar. La lista cerrada de textos abarca el texto de los nodos y los atributos de texto libre, como el nombre de una hoja, de una tabla o de una columna, así que una cadena compartida huérfana, un encabezado de página, un nombre definido o un título en las propiedades también hacen fallar la prueba.

La regla 1 de `scripts/preflight.sh` admite la plantilla solo en `plantillas/R017_ambiental_general.xlsx`, con esas mismas mayúsculas, y `.gitignore` la exceptúa en esa misma ruta. La regla 2 lee el texto y los atributos de texto libre de todas sus partes en lenguaje de marcado extensible (Extensible Markup Language, XML), sin los demás atributos, donde van anchos de columna como `33.42578125` y colores como `00808080`, y falla con un número de 8 dígitos que no empieza con 99 o con un correo en cualquier parte. `scripts/probar_preflight.sh` prueba en un repositorio temporal los casos que deben pasar y los que deben fallar.

## Cómo se actualiza

Si la coordinación de la carrera cambia la plantilla oficial (D-08), el vaciado se repite con los pasos de «Origen» sobre una copia nueva, y la lista cerrada de rótulos, las listas cerradas de partes y de textos, el mapa y la estructura de `tests/test_plantilla_r17.py` cambian en el mismo commit que la plantilla.
