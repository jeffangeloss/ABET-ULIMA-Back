# Revisión por refutación de las historias del export real de Blackboard

**Fecha**: 2026-11-09
**Spec**: [spec.md](./spec.md)
**Entrada**: 15 historias candidatas (C-01 a C-15), escritas desde tres ángulos (el profesor que sube su export, la coordinación con la base y la privacidad y la seguridad del lector)
**Salida**: 11 historias (US-26 a US-36 de la spec), una de ellas nueva por las faltantes, y 4 piezas que pasan a tareas de cierre o a «Fuera de alcance»
**Fuentes**: `spec003/contexto_y_candidatas.md`, `spec003/auditoria_necesidad.md`, `spec003/auditoria_solapamiento.md`, `spec003/auditoria_verificabilidad.md` y `spec003/critica_arquitectura.md`, en la carpeta de notas de la sesión del plan (fuera del repositorio)

## Método

Cada candidata parte refutada y sobrevive solo si resiste tres lentes independientes, como en la spec 001. La lente de necesidad pregunta si la exige el objetivo del sprint, el pedido literal o un requisito del lanzamiento, y si cambia algo que la spec 001 no fija ya con prueba. La lente de solapamiento y tamaño aplica INVEST (independiente, negociable, valiosa, estimable, pequeña y comprobable) contra las demás candidatas y contra las historias US-07 a US-14 y US-21 de la spec 001. La lente de verificabilidad coteja cada escenario con V1_07 a V1_09, `db/pruebas/pruebas.sql`, `db/pruebas/datos_sinteticos.sql`, el lector, la validación, la carga y la constancia, y recalcula las cifras en memoria. Un crítico aparte ataca las doce decisiones técnicas AD-01 a AD-12. Las tres lentes corren con Sonnet y esfuerzo medio, y el crítico con el modelo de la sesión y esfuerzo alto, porque varias decisiones tocan la seguridad del lector.

Los veredictos posibles son SOBREVIVE, CORREGIR, FUSIONAR, PARTIR, MOVER_A_DESPUES y REFUTADA. Una candidata queda en el sprint si al menos dos lentes no la sacan, y las fusiones y particiones se aplican. Este archivo registra los veredictos y su destino, y el razonamiento completo con su evidencia está en cada informe.

## Veredictos por candidata

Abreviaturas. S es SOBREVIVE, C es CORREGIR, F es FUSIONAR, P es PARTIR, M es MOVER_A_DESPUES y R es REFUTADA.

| Candidata | Título de la candidata | Necesidad | Solapamiento y tamaño | Verificabilidad | Historia final |
| --- | --- | --- | --- | --- | --- |
| C-01 | Cargar el .csv de Blackboard | S con C, sin las variantes que nadie pidió y con la huella y Q04 | S con C, absorbe C-11 y C-12 | C, falta nombrar `pct_logro_sobre_calificados`, los avisos de 4.1 y 4.2 no guardan su PI y Q01 a Q14 van completos | US-27 |
| C-02 | Cargar el .xls de texto de Blackboard | S con C, sin la variante CRLF repetida | S con C, el renombrado a .xlsx pasa a C-06 | C y F del esquema con C-01; falta fijar el salto de línea de la base y el UTF-16 BE | US-28 |
| C-03 | Reconocer las columnas ABET con sus encabezados reales | S, con los ejemplos reales y los negativos | C, absorbe C-09, porque sin V1_10 no se prueba sola | C, «ABET SO 5.10 [» es el PI 5.10 y no «no PI», y faltan filas y cuentas | US-26, con la parte de la base de C-09 |
| C-04 | Leer los niveles con decimales | S con C, sin los ejemplos que repiten la spec 001 | S con C, suma «3.00» dentro de un .xlsx | C, la regla tiene que escribirse como expresión, «1,000» no puede leerse como 1 y faltan 11 / 10 / 1 y 60,0 / 60,0 / 70,0 | US-29 |
| C-05 | Tratar «Needs Grading» en una columna de PI | R, la decisión 5 no cambia D-03 y el «Needs Grading» real está en las actividades | R, ya está en `carga.feature` | F con C-04, como una fila de su esquema | Una fila del esquema de US-29 |
| C-06 | Saber por qué no se admite un archivo | S, partida y fusionada, sin la fila de 1,2 MB y con LIBRO_EXCEL_97 a después | S con C, solo el tipo, con el renombrado de C-02 y las mayúsculas | C, cada defecto se arma en `tmp_path`, el OLE de Excel 97 con nombre .xlsx cambia de motivo y faltan los motivos de la línea sin separador y de otro OLE | US-31 |
| C-07 | Cotejar la sección con el nombre del export de texto | S con C, sin «(1)» ni periodo | S con C, declara los escenarios de la spec 001 que reescribe | C, cada fila del esquema corre en una base limpia porque comparte huella, y `hoja` nula rompe hoy `seccion_declarada` | US-30 |
| C-08 | Elegir el .csv o el .xls en P3 | S con C, sin el tercer escenario | C, historia fina del Front con el contrato | C, «P3 no revisa el tipo» se comprueba con `applyAccept` en falso | US-33 |
| C-09 | Aceptar en la base los encabezados con prefijo | S partida, el paso en Neon pasa a criterio de cierre | F con C-03 | C, se prueba con UPDATE como R26 y con una prueba de paridad entre el lector y la base | US-26; el paso en Neon, T072 |
| C-10 | Leer el texto sin abrir una puerta nueva | F con C-06 | C, el rol es el profesor y el UTF-16 sin BOM equivale al byte nulo | C, el tope de 1 048 576 filas es inalcanzable con 1 MB y los defectos se arman con bytes precisos | US-32 |
| C-11 | Descartar nombres y valores también en el texto | F con C-02 | F con C-01 y C-02 | C, la búsqueda necesita una consulta exacta sobre las tablas que escribe la carga | US-27 y US-28 |
| C-12 | Reconocer el mismo export de texto | R, BR-CARGA-06, 09 y 10 ya lo fijan | F con C-01 | C, faltan el 409 de otra sección y la copia sin BOM | US-27 |
| C-13 | Constancia de un export sin hoja | S con C | S | S con un ajuste en `r17.py:353` y en `tipos.ts` | US-34 |
| C-14 | Versionar exports de texto sin abrir una vía a los reales | S con C, tres filas | P, la revisión previa y el generador por separado | C, `tr -d '\000'` es más portable que `iconv` y los ids de Blackboard deben ser inventados | US-35; el generador, T014 |
| C-15 | Probar los exports de texto en la vista previa de develop | C, es la comprobación de cierre y no una historia | C, mezcla operación y prueba de humo | C, tarea de cierre con cuentas y Production sin cambios | T070 a T076 y SC-004 |

Cuentas por lente, tomadas de las tablas de cada informe.

| Lente | S | C | F | P | M | R |
| --- | --- | --- | --- | --- | --- | --- |
| Necesidad | 10 | 1 | 2 | 0 | 0 | 2 |
| Solapamiento y tamaño | 3 | 5 | 5 | 1 | 0 | 1 |
| Verificabilidad | 1 | 13 | 1 | 0 | 0 | 0 |

La tabla de necesidad marca varias candidatas como «SOBREVIVE (corregir)», y aquí cuentan como S. La lente de necesidad mueve además la fila de LIBRO_EXCEL_97 de C-06 a después, mientras las otras dos la conservan, así que la fila queda sujeta a J-18.

## Historias faltantes

| Faltante | La proponen | Historia o requisito final |
| --- | --- | --- |
| El export real con las columnas ABET vacías, que hoy se publicaría con 33 mediciones SIN_EVIDENCIA y dejaría la sección bloqueada en el corte 1, porque nadie reemplaza una carga publicada hasta US-18 | Necesidad (F-1), solapamiento (F-02) | US-36, con D-31 |
| V1_10 en la rama principal de Neon antes de llevar la versión a `main` | Necesidad (F-2) | FR-014 y T076 |
| Regresión de los .xlsx de la spec 001 con el lector nuevo | Necesidad (F-3), verificabilidad (F-01) | US-26, escenario 2, y la suite completa (FR-013) |
| Guardia de códigos inventados en un export de texto | Solapamiento (F-01), verificabilidad (F-04) | US-27, escenario 6, y US-28, escenario 4 |
| Orden de BR-CARGA-03 con un export de texto | Verificabilidad (F-03) | US-32, escenario 2 |
| Numeración por registro y no por línea | Verificabilidad (F-06) | US-27, escenario 4 |
| Separador por la primera línea, cruzado entre formatos | Solapamiento (F-03), verificabilidad (F-07) | US-27, escenario 2, y US-28, escenario 2 |
| Extensión en mayúsculas | Solapamiento (F-04), verificabilidad (F-08) | US-31 y US-27, escenario 2 |
| Estructura en texto (sin filas y sin Username) | Verificabilidad (F-11 y F-12) | US-27, escenario 5 |
| «3,00» como texto dentro de un .xlsx | Verificabilidad (F-13) | US-29, escenario 2 |
| Ids de Blackboard inventados | Verificabilidad (H-3 y F-10) | T014 y `tests/test_generador_exports.py` |
| Textos de la spec 001 que cambian | Solapamiento (F-07), verificabilidad (H-4 y F-09) | FR-013 y T030 |
| Reemplazo entre formatos | Solapamiento (F-05) | Fuera de alcance, llega con US-18 |

## Defectos transversales de verificabilidad

| Defecto | Resolución en la spec |
| --- | --- |
| COLUMNA_PI_FUERA_DEL_PLAN no guarda qué PI queda fuera, porque `ck_rechazo_fila_pi` admite `pi_id` solo en PI_DEL_PLAN_AUSENTE y PI_REPETIDO | Los escenarios cuentan dos avisos con `pi_id`, `carga_columna_id` y `fila_origen` nulos, sin ampliar la restricción (H-1) |
| Las copias con el mismo contenido comparten huella | Cada fila de un esquema corre en su propia base desechable, como cada escenario de pytest-bdd (H-2) |
| Los ids de Blackboard y el prefijo del curso de la nota de análisis salen del export real | Los datos versionados usan ids inventados con la misma forma (H-3) |
| Cambian textos que ya prueban la spec 001 y el Front | FR-013 lista los escenarios y las pruebas por actualizar (H-4) |
| El OLE de Excel 97 con nombre `.xlsx` cambia de motivo si se acepta LIBRO_EXCEL_97 | Queda declarado en BR-CARGA-05 y sujeto a J-18 (H-5) |
| El OLE de Excel 97 no puede versionarse en la carpeta de datos inventados | Las pruebas lo arman en `tmp_path` (H-6) |
| Más de 1 048 576 filas no caben en 1 MB | El límite queda como defensa en el código, sin escenario (H-7) |

## Veredicto del crítico de arquitectura

| N.º | Decisión | Veredicto | Lo que adopta la spec |
| --- | --- | --- | --- |
| AD-01 | El contenido decide el lector y la extensión solo filtra | SE_SOSTIENE con condiciones | Tabla de precedencia cerrada en BR-CARGA-05. Se quita un solo BOM de UTF-8, y un U+FEFF que queda al comienzo detiene el archivo. `FF FE` es UTF-16 LE, y `FE FF` (UTF-16 BE) no se admite. Un texto vacío o con el carácter U+0000 tampoco se admite, lo que detiene también un UTF-32 o un UTF-16 sin BOM (US-32) |
| AD-02 | `csv` de la biblioteca estándar con `strict=True` y el separador de la primera línea | SE_SOSTIENE con condiciones | `csv.reader` sobre `io.StringIO(texto, newline="")`, sin `splitlines()`, y la primera línea cortada en el primer `\r\n`, `\r` o `\n`. El U+0000 se revisa antes de `csv`, porque `csv` de Python 3.12 lo acepta. Una primera línea con «;» cuyo encabezado no trae Username ni Student ID detiene el archivo, para que el texto que Excel en español guarda con punto y coma reciba un 422 y no una carga RECHAZADA con COLUMNA_CODIGO_AUSENTE |
| AD-03 | Excel 97-2003 se reconoce por la subcadena Workbook o Book | CAMBIAR | La subcadena no distingue un libro de otro OLE. Si J-18 pide un mensaje propio, el lector lee los nombres de las entradas del directorio del contenedor; si no, todo OLE sin cifrado sigue en CONTENIDO_NO_ES_LIBRO con el texto nuevo, sin leer el directorio |
| AD-04 | El texto reutiliza `_clasificar` y `_filas_de_datos` y numera por registro | SE_SOSTIENE con condiciones | `_filas_del_texto`, hermano de `_filas_del_archivo`, revisa los límites fila a fila, numera con `enumerate`, nunca arma una lista entera y convierte todo error en ArchivoIlegible sin encadenar la excepción original |
| AD-05 | Un patrón de encabezado con `re.IGNORECASE` y `~*` | CAMBIAR | Letras en clases explícitas, de cero a tres espacios entre las partes, `re.ASCII` en Python y `~` en PostgreSQL, porque con `re.IGNORECASE` la «ſ» coincide con la «s» y `\s` toma el espacio duro, y porque espacios ilimitados podían dejar el código del PI después del carácter 200 que guarda la base. La misma lista de casos corre en `tests/test_lector.py` y en `db/pruebas/pruebas.sql` |
| AD-06 | «3.00» vale el entero | CAMBIAR | La expresión es `[+-]?[0-9]+(?:[.,]0{1,2})?`, así que «1,000» y «3.000» siguen en NIVEL_NO_NUMERICO. Un texto con más de cuatro cifras significativas da NIVEL_FUERA_DE_ESCALA sin llamar a `int()`, que lanza `ValueError` y deja la carga en 500 desde las 4 300 cifras, un defecto que la spec 001 ya tiene con el `.xlsx` |
| AD-07 | `archivo_origen.hoja` nula y sección solo por el nombre | SE_SOSTIENE con cambios obligatorios | `seccion_declarada` y `LibroLeido.hoja` aceptan la hoja nula, porque hoy `hoja.startswith` lanza `AttributeError` y da 500, y `r17.py` escribe «Sin hoja (export de texto)» en lugar de la celda vacía sin guardarlo en la base. BR-CARGA-11 dice que en un export de texto el cotejo vale lo que vale el nombre |
| AD-08 | Los errores del texto reutilizan NO_SE_PUDO_ABRIR | DUDOSA | El texto al profesor no cambia. ArchivoIlegible gana un detalle de lista cerrada (CODIFICACION, CARACTER_NULO, COMILLAS, SEPARADOR, COLUMNAS, CAMPO_LARGO, FILAS y VACIO) que va solo al registro de la aplicación, nunca a la respuesta ni a la base |
| AD-09 | Sin columna para el formato | DUDOSA | Se sostiene sin columna nueva (propuesta). La hoja nula marca el export de texto, el nombre guarda su extensión y la huella identifica los bytes. La alternativa del crítico, `archivo_origen.formato` con su restricción, queda en «Fuera de alcance» |
| AD-10 | Los límites de la cuadrícula de Excel y de `csv` | CAMBIAR | Un tope de 5 000 filas de datos por archivo (propuesta, J-20), para el texto y para el libro, porque 1 MB de líneas vacías con una fila al final da cerca de un millón de rechazos CODIGO_VACIO y una escritura de ese tamaño en Neon. El lector no llama a `csv.field_size_limit()`, que es estado global, y una prueba fija el valor de 131 072 |
| AD-11 | V1_10 en develop y en la principal desde el Windows | SE_SOSTIENE con condiciones | DROP y ADD de la restricción en la misma migración, sin NOT VALID. Antes de migrar, una consulta de solo lectura cuenta las filas que no cumplirían y debe dar 0. Primero la migración y después el código. Para volver atrás se revierte el código y V1_10 se queda, porque su patrón acepta todo lo que aceptaba el LIKE |
| AD-12 | La revisión previa decodifica con `iconv` | CAMBIAR | Sin `iconv`. La regla 2 revisa por contenido cada archivo de la carpeta, falla con un OLE, lee un zip con `unzip -p` y pasa lo demás por `LC_ALL=C tr -d '\000'`, y `codigos_reales` cuenta con `LC_ALL=C grep -a`, porque hoy `grep` toma por binario un texto con un byte nulo o en Windows-1252 y cuenta 0 |

El crítico suma riesgos que la spec atiende así. Un U+FEFF o un U+200B dentro de un encabezado impide reconocer su PI, y la carga cae en PI_DEL_PLAN_AUSENTE con un mensaje claro (Edge Cases). `cargar()` atrapa solo ArchivoIlegible y CodigoNoInventado, así que el lector de texto no deja escapar ninguna otra excepción (FR-003). Un export real renombrado `.txt` fuera de la carpeta de datos no lo revisa ninguna regla de la revisión previa, y queda anotado como riesgo residual en `docs/devops.md`. La detección del cifrado por subcadena, que la spec 001 ya usa, queda como está.
