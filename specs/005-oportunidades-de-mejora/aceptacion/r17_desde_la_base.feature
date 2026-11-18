# language: es
#
# Escenarios de aceptación del R-17 que lleva desde la base las causas, las acciones y la descripción del
# instrumento, de las historias de usuario (user stories, US) US-50 y US-51 de la spec
# 005-oportunidades-de-mejora (épica EP-05, propuesta). Jefferson pide el 2026-11-18 que el R-17 deje de
# salir con los recuadros A y B y con la descripción del instrumento vacíos y editables, y que el reporte y la
# base digan lo mismo (C-06 y C-07 de la síntesis de la auditoría). Cierra J-27 de la spec 004 (J-31).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid y los códigos de
# estudiante 99000001 a 99000011. Ninguna contraseña aparece escrita aquí, porque la prueba asigna al azar la
# contraseña con que abre cada sesión, sin guardarla en el repositorio.
# - Declaración de la 410 de los escenarios 1 y 3 de US-50. Causas «La entrega coincidió con la semana de
#   parciales.» y acciones «Mover la entrega a la semana 10 y revisar el avance en clase.»
# - Las descripciones de US-51 son textos de prueba distintos por PI que empiezan por «Texto de prueba.», como
#   los del guion db/datos/descripcion_instrumento_2026_2.sql. El contenido real lo decide D-34 con la
#   Coordinación.
#
# Vocabulario de los pasos, el de r17_constancia.feature de la spec 001 y el de declaracion.feature.
# - «descarga el R-17 de esa carga» es GET /api/cargas/{carga_id}/r17.xlsx (ruta 7) y el libro se lee con
#   openpyxl en la prueba. Con US-49, el R-17 solo sale con la declaración, así que «con sus causas y
#   acciones declaradas» llama a declarar() de tests/cargas_de_prueba.py (FR-017).
# - B29 y B34 son las celdas de los recuadros A (causas) y B (acciones). Los rangos B29:I31 y B34:I36 son sus
#   rangos combinados, y B a I mide 208,6 unidades de ancho. Las filas 29 a 31 llevan también la tabla
#   K28:Q31, así que el alto de la fila 31 y el de la 36 lo calcula r17.py de forma determinista por líneas,
#   con un ancho conservador, sin tocar las filas 29, 30, 34 y 35.
# - G17, G18 y G19 son las celdas de la descripción del instrumento de los PI 5.1, 5.2 y 5.3 (G17:I19, con
#   las filas 17 a 19 de unos 76 puntos, que admiten unos 400 caracteres).
# - V1_11 agrega abet.plan_medicion.descripcion_instrumento varchar(400) nulo, con
#   ck_plan_medicion_descripcion, que exige al menos un carácter visible y ningún blanco a los lados con la
#   misma definición de blanco del Back, la de str.isspace() de Python (29 caracteres, BR-R17-11). abet_app no
#   la escribe.
# - Los Antecedentes nombran V1_11 mientras V1_12 no existe. US-50 los lleva a V1_12 en el mismo cambio que
#   crea esa migración, y US-49 (T037) suma entonces «, con sus causas y acciones declaradas» a los dos
#   primeros escenarios de US-51, porque desde US-49 el R-17 sale solo con la declaración.
# - «el dueño de la base» corre scripts y consultas solo en la base desechable de la prueba. En Neon, las
#   escrituras las hace Jefferson desde el Windows (AD-20).
# - Cada escenario corre en una base desechable propia, así que los carga_id salen de la API o de la base y
#   nunca se suponen.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: El R-17 escribe desde la base las causas, las acciones y la descripción del instrumento
  Como coordinación, quiero que el R-17 de cada carga lleve el texto declarado por el profesor y la
  descripción del instrumento de cada PI, ambos guardados en la base, para que el reporte y la base digan lo
  mismo y nadie complete esos recuadros a mano en el archivo.

  Antecedentes:
    Dado una base PostgreSQL 18 desechable con las migraciones V1_01 a V1_11 y los datos de db/datos/periodo_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y plan_medicion registra los PI 5.1, 5.2 y 5.3 para la asignatura "450002" en "2026-2"
    Y acceso.docente_seccion asigna la sección 410 de "450002" a "docente410@example.invalid"
    Y "coordinacion@example.invalid" activo con rol "COORDINADOR" y sin secciones en acceso.docente_seccion
    Y ninguna sección de 2026-2 tiene cargas

  # US-50: El R-17 lleva las causas y las acciones desde la base
  # Cambia BR-R17-04 («vacíos y editables» pasa a «desde la base») y, por ADR-009 del Front (propuesta), el
  # invariante 2 de ADR-005 («Ninguna celda del libro empieza por "="» pasa a «Ninguna celda del libro es una
  # fórmula»). El recuadro de comentario de BR-R17-04 se cierra, porque la hoja no lo tiene.

  @US-50 @spec005 @corte1
  Escenario: B29 y B34 traen el texto declarado de la 410
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que la carga tiene declaradas las causas «La entrega coincidió con la semana de parciales.» y las acciones «Mover la entrega a la semana 10 y revisar el avance en clase.»
    Cuando "docente410@example.invalid" descarga el R-17 de esa carga
    Entonces B29 trae como cadena «La entrega coincidió con la semana de parciales.»
    Y B34 trae como cadena «Mover la entrega a la semana 10 y revisar el avance en clase.»

  @US-50 @spec005 @corte1
  Escenario: Unas causas de 2000 caracteres se ven completas y no tapan la tabla de frecuencias
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que la carga tiene declaradas unas causas de 2000 caracteres y unas acciones de «Mover la entrega a la semana 10.»
    Cuando "docente410@example.invalid" descarga el R-17 de esa carga
    Entonces B29 tiene ajuste de texto y alineación arriba
    Y el alto de la fila 31 crece hasta mostrar el texto completo, según el cálculo de r17.py
    Y K31:Q31 conserva sus valores
    Y las filas 29, 30, 34 y 35 conservan su alto

  @US-50 @spec005 @corte1
  Escenario: Un texto que parece fórmula queda como cadena
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que la carga tiene declaradas las causas «=SUMA(1;2)» y las acciones «Mover la entrega a la semana 10.»
    Cuando "docente410@example.invalid" descarga el R-17 de esa carga
    Entonces B29 trae como cadena «=SUMA(1;2)»
    Y ninguna celda del libro es una fórmula

  # D-37 (valor provisional, sí). La declaración corregida del escenario «Corregir una declaración deja la
  # anterior guardada y vigente hasta declarar la nueva» de declaracion.feature.
  @US-50 @spec005 @corte1
  Escenario: El R-17 trae el texto de la última declaración
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id, con sus causas y acciones declaradas
    Y que "docente410@example.invalid" corrigió la declaración con las causas «La entrega coincidió con la semana de parciales y de feriado.» y las acciones «Mover la entrega a la semana 10 y revisar el avance en tutoría.»
    Cuando "docente410@example.invalid" descarga el R-17 de esa carga
    Entonces B29 trae como cadena «La entrega coincidió con la semana de parciales y de feriado.»
    Y B34 trae como cadena «Mover la entrega a la semana 10 y revisar el avance en tutoría.»
    Y abet.mejora_declaracion conserva la declaración anterior

  # US-51: La descripción del instrumento sale de la base
  # BR-R17-11. _PLAN de r17.py la lee y _bloques la escribe en G de cada fila del bloque I, y deja vacía la
  # celda de un PI sin descripción. D-34 (quién redacta la descripción y con qué campos) sigue abierta.

  @US-51 @spec005 @corte1
  Escenario: G17, G18 y G19 traen la descripción de cada PI
    Dado que el dueño de la base fija en abet.plan_medicion de "450002" en "2026-2" una descripción distinta para 5.1, 5.2 y 5.3, cada una «Texto de prueba.» seguido del número de su PI
    Y que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" descarga el R-17 de esa carga
    Entonces G17 trae el texto del PI 5.1, G18 el del PI 5.2 y G19 el del PI 5.3
    Y los tres textos son distintos entre sí

  @US-51 @spec005 @corte1
  Escenario: Sin descripción en la base, G17:I19 queda vacía
    Dado que abet.plan_medicion de "450002" en "2026-2" no tiene descripcion_instrumento en ningún PI
    Y que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" descarga el R-17 de esa carga
    Entonces G17, G18 y G19 están vacías
    Y el R-17 no inventa ningún texto de descripción

  # La definición de blanco es la del Back. El texto de 401 caracteres pasa el CHECK, y PostgreSQL lo rechaza
  # por el largo de la columna (SQLSTATE 22001) antes de evaluar la restricción. El cambio va sobre la fila del
  # PI 5.1 de "450002" en "2026-2".
  @US-51 @spec005 @corte1
  Esquema del escenario: La base rechaza una descripción en blanco, con blancos a los lados o demasiado larga
    Dado una conexión directa del dueño de la base
    Cuando esa conexión fija en abet.plan_medicion la descripcion_instrumento <texto>
    Entonces la base rechaza el cambio por <rechazo>
    Y abet.plan_medicion conserva su descripción anterior

    Ejemplos:
      | texto                                    | rechazo                                       |
      | "   "                                    | la restricción "ck_plan_medicion_descripcion" |
      | " Texto de prueba." (blanco al comienzo) | la restricción "ck_plan_medicion_descripcion" |
      | "Texto de prueba. " (blanco al final)    | la restricción "ck_plan_medicion_descripcion" |
      | un texto de 401 caracteres               | el largo de la columna                        |

  @US-51 @spec005 @corte1
  Escenario: El guion de datos se corre dos veces y deja las mismas tres descripciones
    Dado una conexión directa del dueño de la base
    Cuando esa conexión corre dos veces db/datos/descripcion_instrumento_2026_2.sql
    Entonces abet.plan_medicion de "450002" en "2026-2" tiene las mismas 3 descripciones tras la primera y tras la segunda corrida
    Y ninguna de las tres descripciones está repetida en otro PI
