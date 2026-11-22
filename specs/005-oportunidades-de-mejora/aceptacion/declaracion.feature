# language: es
#
# Escenarios de aceptación del análisis por indicador, con la oportunidad de mejora (OM) o la buena práctica
# (BP) de cada PI, de las historias de usuario (user stories, US) US-47, US-48, US-49, US-53 y US-54 de la spec
# 005-oportunidades-de-mejora (épica EP-05, propuesta). Jefferson pide el 2026-11-18 que el profesor complete
# en el sistema los recuadros A (causas) y B (acciones) del R-17, que hoy salen vacíos y editables, y que
# ningún R-17 llegue a la acreditación sin ellos. El cambio del 2026-11-21 (borrador, pendiente de la
# reaprobación de Jefferson) lleva el registro a cada PI, con una causa y una acción que el sistema rotula OM o
# BP según el semáforo, como piden Mechelle Prado (19-11-2026) y Claudia León (19 o 20-11-2026) en sus correos
# (spec.md, Input y Session 2026-11-21, y C-P01, C-P03, C-C03, C-B01, C-B03 y C-B06 de revision-historias.md).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid y los códigos de
# estudiante 99000001 a 99000011 y 99000023 a 99000033. Ninguna contraseña aparece escrita aquí, porque la
# prueba asigna al azar la contraseña con que abre cada sesión, sin guardarla en el repositorio.
# - (propuesta) Los registros de prueba de la 410, los tres OPORTUNIDAD_MEJORA con R-2026-BORRADOR, son 5.1
#   con la causa «La entrega coincidió con la semana de parciales.» y la acción «Mover la entrega a la semana
#   10 y revisar el avance en clase.», 5.2 con «Los grupos no recibieron la rúbrica antes de la entrega.» y
#   «Publicar la rúbrica en la semana 8.», y 5.3 con «El trabajo en equipo se evaluó solo al final.» y
#   «Revisar el trabajo en equipo en dos avances.».
# - (propuesta) Los registros de prueba de la 412 de 450002, con 5.1 y 5.3 BUENA_PRACTICA y 5.2
#   OPORTUNIDAD_MEJORA, son 5.1 con «Los grupos presentaron avances semanales en clase.» y «Mantener las
#   revisiones semanales del avance.», 5.2 con «La entrega coincidió con la semana de parciales.» y «Mover la
#   entrega a la semana 10 y revisar el avance en clase.», y 5.3 con «Los roles del equipo rotaron en cada
#   entrega.» y «Compartir la rotación de roles con las otras secciones.».
# - (propuesta) La corrección de la 410 cambia solo 5.1, con «La entrega coincidió con la semana de parciales
#   y de feriado.» y «Mover la entrega a la semana 10 y revisar el avance en tutoría.».
# - Cifras con R-2026-BORRADOR. La 410 da 63,6 %, 63,6 % y 72,7 %, los tres ROJO. La 412 de 450002 da 81,8 %
#   VERDE, 54,5 % ROJO y 90,9 % VERDE. Con R-PRUEBA-APROBADO (nivel esperado 2 y meta 70 %), la 410 da 90,9 %
#   VERDE en los tres PI. La copia de la 410 con la columna 5.3 vacía en la fila 9 da 5.3 en 80,0 % VERDE.
# - Los exports viven en tests/datos_inventados/. Su carga PUBLICADA sale de «que "sintetico_20262_450002_410
#   .xlsx" está subido a la sección 410 con respuesta 201 y su carga_id» de la spec 001, y las copias se arman
#   en tmp_path con REGLAS_DE_COPIA.
#
# Vocabulario de los pasos, el de carga.feature, reemplazo_y_cargas.feature y r17_constancia.feature de la
# spec 001, el de resultados.feature de la spec 004 y el de semaforo.feature.
# - Ruta 13 GET /api/cargas/{carga_id}/indicadores, con semaforo, hallazgo y tipo_registro por PI (US-45).
# - Ruta 14 (propuesta) GET /api/cargas/{carga_id}/mejora. Responde declaracion (declarada_en e indicadores
#   [{pi, tipo, causa, accion, estado}]) o nulo, borrador (version, actualizado_en e indicadores [{pi, tipo,
#   causa, accion}]) o nulo, borrador_pendiente (hay un borrador posterior a la última declaración),
#   heredado_de (US-54) y puede_editar. El estado PROPUESTA de cada indicador declarado lo deriva la ruta, y
#   la base no lo guarda (D-42).
# - Ruta 15 (propuesta) PUT /api/cargas/{carga_id}/mejora/borrador con {version, indicadores: [{pi, tipo,
#   causa, accion}]}, una sola versión por carga. El PUT reemplaza el conjunto de registros de la carga, y un
#   PI que falta en el arreglo queda con causa y accion nulas.
# - Ruta 16 (propuesta) POST /api/cargas/{carga_id}/mejora/declaracion con {version}, que declara esa versión
#   exacta del borrador. Responde 201 con declarada_en e indicadores [{pi, tipo, causa, accion, estado}].
# - «guarda el borrador con …» es un PUT a la ruta 15 con la versión que la ruta 14 devolvió (0 si no hay
#   borrador) y, en cada indicador, el tipo_registro que devuelve la ruta 13. «declara la versión N» es un
#   POST a la ruta 16 con {"version": N}. Escribe solo el profesor asignado, con puede_declarar() de
#   app/permisos.py. El coordinador lee con puede_leer() y nunca recibe el texto del borrador. Orden de las
#   respuestas 401, 403, 422 y 409, con el cuerpo leído a mano después del alcance. El 409 de una carga que no
#   está PUBLICADA manda sobre los demás 409, y el de una regla sin definir manda sobre el 422 de la
#   declaración incompleta.
# - La ruta 7 es GET /api/cargas/{carga_id}/r17.xlsx. «con su análisis declarado» llama a declarar() de
#   tests/cargas_de_prueba.py, que registra y declara los registros de prueba de su sección en cada PI con
#   calificados (FR-017).
# - Texto (J-39 y AD-10). El Back normaliza cada causa y cada acción a NFC, cambia \r\n por \n, rechaza los
#   caracteres de control salvo \n y \t y cuenta puntos de código, hasta 800 por campo.
# - V1_12 (J-38, propuesta) crea abet.mejora_borrador (cabecera por carga con versión), abet.mejora_borrador_pi
#   (un registro por PI, FK a abet.carga_columna), abet.mejora_declaracion (cabecera de solo INSERT) y
#   abet.mejora_declaracion_pi (registro declarado con tipo y la foto logro_pct, meta_pct y semaforo), sin
#   columnas de estado, responsable ni plazo. La declaración vigente de una carga es la de mayor
#   declaracion_id.
# - El patrón de códigos y correos (AD-11) es un número de exactamente 8 dígitos no rodeado de otros dígitos
#   o un correo. Es el mismo en las rutas y en los CHECK ck_mejora_borrador_pi_sin_codigos y
#   ck_mejora_declaracion_pi_sin_codigos. Un nombre de estudiante escrito en el texto no se detecta, y
#   Jefferson acepta que BR-R17-07 y la regla 6 de AGENTS.md se cumplan en estos campos por aviso y no por
#   construcción (J-36).
# - Cada escenario corre en una base desechable propia, así que los carga_id salen de la API o de la base y
#   nunca se suponen.
# - @delegado_a_vitest marca un escenario de la pantalla P4 (o de P2 y P5) que prueba Vitest en el Front.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec. D-36, D-37,
#   D-39, D-40 y D-42 siguen abiertas con la Coordinación, y J-38 a J-41 esperan la reaprobación de Jefferson.

Característica: Análisis por indicador, con la oportunidad de mejora o la buena práctica de cada PI, desde P4 y guardado en la base
  Como profesor de Ingeniería Ambiental, quiero registrar en P4 una causa y una acción para cada PI de mi
  carga, que el sistema rotula como oportunidad de mejora o como buena práctica según el semáforo, y que el
  R-17 de mi sección solo se entregue con ese análisis declarado, para que el análisis de cada indicador
  quede en la base y en el reporte.

  Antecedentes:
    Dado una base PostgreSQL 18 desechable con las migraciones V1_01 a V1_12, los datos de db/datos/periodo_2026_2_inventado.sql y, después, los de db/datos/varias_secciones_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y plan_medicion registra los PI 5.1, 5.2 y 5.3 para la asignatura "450002" en "2026-2"
    Y acceso.docente_seccion asigna la sección 410 de "450002" a "docente410@example.invalid", la 411 de "450002" a "docente411@example.invalid" y la 412 de "450002" a "docente.varias@example.invalid"
    Y "coordinacion@example.invalid" activo con rol "COORDINADOR" y sin secciones en acceso.docente_seccion
    Y ninguna sección de 2026-2 tiene cargas

  # US-47: Registrar por indicador la oportunidad de mejora o la buena práctica en P4
  # (propuesta) El tipo lo fija el semáforo de la ruta 13 (D-39). VERDE da BUENA_PRACTICA, y AMBAR y ROJO dan
  # OPORTUNIDAD_MEJORA. Un PI sin calificaciones no lleva registro (D-40). La ruta 16 escribe la foto de
  # abet.v_r17_por_pi en la misma transacción (J-40).

  @US-47 @spec005 @corte1
  Esquema del escenario: El profesor registra y declara los tres PI de la 412, con dos buenas prácticas y una oportunidad de mejora
    Dado que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_412.xlsx" está subido a la sección 412 con respuesta 201 y su carga_id
    Cuando "docente.varias@example.invalid" guarda el borrador con los registros de prueba de la 412 y version 0
    Y declara la versión 1
    Entonces la API responde 201 con declarada_en y tres indicadores
    Y abet.mejora_declaracion_pi guarda el PI <pi> con tipo "<tipo>", logro_pct <logro>, meta_pct 80.0 y semaforo "<semaforo>"
    Y GET /api/cargas/{carga_id}/mejora responde 200 con el PI <pi> declarado con tipo "<tipo>", su causa y su acción de prueba y estado "PROPUESTA"
    Y borrador_pendiente es falso

    Ejemplos:
      | pi  | tipo               | logro | semaforo |
      | 5.1 | BUENA_PRACTICA     | 81.8  | VERDE    |
      | 5.2 | OPORTUNIDAD_MEJORA | 54.5  | ROJO     |
      | 5.3 | BUENA_PRACTICA     | 90.9  | VERDE    |

  @US-47 @spec005 @corte1
  Escenario: Una carga sin texto responde con la declaración y el borrador nulos
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/cargas/{carga_id}/mejora
    Entonces la API responde 200 con declaracion nulo, borrador nulo y puede_editar verdadero

  @US-47 @spec005 @corte1
  Esquema del escenario: Declarar con un registro incompleto no crea ninguna declaración
    Dado que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_412.xlsx" está subido a la sección 412 con respuesta 201 y su carga_id
    Y que "docente.varias@example.invalid" guardó en la versión 1 los registros de prueba de la 412, salvo <falta>
    Cuando "docente.varias@example.invalid" declara la versión 1
    Entonces la API responde 422 con el mensaje "Complete la causa y la acción de cada indicador." (propuesta)
    Y abet.mejora_declaracion y abet.mejora_declaracion_pi no ganan ninguna fila

    Ejemplos:
      | falta                                   |
      | la acción de 5.2, que queda nula        |
      | la causa de 5.1, que queda nula         |
      | la acción de 5.3, que queda en "   "    |
      | el registro entero de 5.3               |

  @US-47 @spec005 @corte1
  Escenario: Declarar la versión 0 sin ningún borrador no crea ninguna declaración
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" declara la versión 0
    Entonces la API responde 422 con el mensaje "Complete la causa y la acción de cada indicador." (propuesta)
    Y abet.mejora_declaracion no gana ninguna fila

  # D-40 (valor provisional, no). Un PI sin calificaciones no exige registro ni lo admite.
  @US-47 @spec005 @corte1
  Escenario: Un PI sin calificaciones no exige registro y no lo admite
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en sus 11 filas está subida a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" guarda el borrador con los registros de prueba de la 410 de 5.1 y 5.2 y version 0
    Y declara la versión 1
    Entonces la API responde 201 con dos indicadores, 5.1 y 5.2
    Y abet.mejora_declaracion_pi no tiene ninguna fila de 5.3
    Cuando "docente410@example.invalid" guarda el borrador con un registro de 5.3 y version 1
    Entonces la API responde 422 con el mensaje "El indicador 5.3 no lleva registro porque su semáforo no tiene dato." (propuesta)

  @US-47 @spec005 @corte1
  Escenario: Un PI que la carga no mide se rechaza en la ruta y en la base
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" guarda el borrador con un registro del PI 2.1 y version 0
    Entonces la API responde 422 con el mensaje "El indicador 2.1 no pertenece a esta carga." (propuesta)
    Y abet.mejora_borrador_pi no gana ninguna fila
    Cuando una conexión directa con el rol abet_app inserta en abet.mejora_borrador_pi un registro del PI 2.1 para esa carga
    Entonces la base rechaza la inserción por la FK de abet.mejora_borrador_pi a abet.carga_columna

  # D-39 (valor provisional). El profesor no elige el tipo, y la base ata el tipo a la foto del semáforo.
  @US-47 @spec005 @corte1
  Escenario: El tipo de registro lo fija el semáforo, en la ruta y en la base
    Dado que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_412.xlsx" está subido a la sección 412 con respuesta 201 y su carga_id
    Cuando "docente.varias@example.invalid" guarda el borrador con los registros de prueba de la 412, con 5.2 de tipo "BUENA_PRACTICA", y version 0
    Entonces la API responde 422 con el mensaje "El tipo de registro de cada indicador lo fija su semáforo." (propuesta)
    Y abet.mejora_borrador no gana ninguna fila
    Cuando una conexión directa del dueño de la base inserta en abet.mejora_declaracion_pi el PI 5.2 con tipo "BUENA_PRACTICA" y semaforo "ROJO"
    Entonces la base rechaza la inserción por la restricción "ck_mejora_declaracion_pi_coherencia"

  # J-39 (valor provisional). El tope es de 800 puntos de código por campo. El borrador guardado antes no cambia.
  @US-47 @spec005 @corte1
  Esquema del escenario: Un texto demasiado largo o con caracteres de control se rechaza y nada cambia
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" guarda el borrador con la causa de 5.1 <causa> y la acción de 5.1 "Mover la entrega a la semana 10." con version 0
    Entonces la API responde 422 con el mensaje "<mensaje>" (propuesta)
    Y abet.mejora_borrador y abet.mejora_borrador_pi no ganan ninguna fila

    Ejemplos:
      | causa                                              | mensaje                                             |
      | un texto de 801 puntos de código                   | Cada campo admite hasta 800 caracteres.             |
      | "Entrega tardía" con el carácter de control U+0007 | El texto trae caracteres que no se pueden guardar.  |

  @US-47 @spec005 @corte1
  Escenario: Una causa de 800 puntos de código se acepta
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" guarda el borrador con la causa de 5.1 de 800 puntos de código y version 0
    Entonces la API responde 200 con version 1

  # (propuesta, D-42) Claudia pide que el responsable y el plazo los defina el coordinador del curso, quizá solo
  # en el R-18, y que el estado nazca como Propuesta. El profesor no los escribe y V1_12 no los guarda.
  @US-47 @spec005 @corte1
  Esquema del escenario: El profesor no fija responsable, plazo ni estado
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que "docente410@example.invalid" guardó en la versión 1 los registros de prueba de la 410
    Cuando se envía <método> <ruta> con un cuerpo válido más la clave "<clave>"
    Entonces la API responde 422 con el mensaje "El cuerpo trae claves que esta ruta no admite." (propuesta)
    Y abet.mejora_borrador conserva la versión 1 y abet.mejora_declaracion no gana ninguna fila

    Ejemplos:
      | método | ruta                                      | clave       |
      | PUT    | /api/cargas/{carga_id}/mejora/borrador    | responsable |
      | PUT    | /api/cargas/{carga_id}/mejora/borrador    | plazo       |
      | POST   | /api/cargas/{carga_id}/mejora/declaracion | estado      |

  @US-47 @spec005 @corte1
  Escenario: Un PI repetido en el cuerpo se rechaza
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" guarda el borrador con dos registros del PI 5.1 y version 0
    Entonces la API responde 422 con el mensaje "Cada indicador va una sola vez en el cuerpo." (propuesta)
    Y abet.mejora_borrador no gana ninguna fila

  @US-47 @spec005 @corte1
  Escenario: Las tablas de V1_12 no tienen estado, responsable ni plazo, y abet_app no corrige una declaración
    Dado la base con V1_12 y db/plataforma/neon/crear_rol_app.sql aplicado
    Cuando se consultan las columnas de abet.mejora_borrador, abet.mejora_borrador_pi, abet.mejora_declaracion y abet.mejora_declaracion_pi en information_schema.columns
    Entonces ninguna columna se llama estado, responsable ni plazo
    Y has_table_privilege de abet_app es verdadero para INSERT y falso para UPDATE y DELETE en abet.mejora_declaracion y abet.mejora_declaracion_pi
    Y has_table_privilege de abet_app es falso para DELETE en abet.mejora_borrador y abet.mejora_borrador_pi

  @US-47 @spec005 @corte1
  Esquema del escenario: Solo el profesor asignado escribe, aunque el cuerpo no sea JSON
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que "<correo>" tiene la sesión iniciada con rol "<rol>"
    Cuando se envía <método> <ruta> con un cuerpo que no es JSON
    Entonces la API responde 403 con el mensaje "La sección no está a su cargo."
    Y las cuatro tablas de V1_12 no ganan ninguna fila

    Ejemplos:
      | correo                       | rol         | método | ruta                                         |
      | coordinacion@example.invalid | COORDINADOR | PUT    | /api/cargas/{carga_id}/mejora/borrador       |
      | coordinacion@example.invalid | COORDINADOR | POST   | /api/cargas/{carga_id}/mejora/declaracion    |
      | docente411@example.invalid   | PROFESOR    | PUT    | /api/cargas/{carga_id}/mejora/borrador       |
      | docente411@example.invalid   | PROFESOR    | POST   | /api/cargas/{carga_id}/mejora/declaracion    |

  # Una carga RECHAZADA o REEMPLAZADA no se declara. La respuesta de una REEMPLAZADA trae reemplazada_por.
  @US-47 @spec005 @corte1
  Esquema del escenario: Una carga que no está publicada responde 409 al guardar y al declarar
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que <carga>
    Cuando se envía <método> <ruta> con un cuerpo JSON válido
    Entonces la API responde 409 con el mensaje "La carga no está publicada y no admite causas ni acciones." (propuesta), <reemplazo>

    Ejemplos:
      | carga                                                                                                                                         | método | ruta                                      | reemplazo                       |
      | una copia de "sintetico_20262_450002_410.xlsx" sin la columna del PI 5.2 está subida a la sección 410 y su carga está "RECHAZADA"             | PUT    | /api/cargas/{carga_id}/mejora/borrador    | sin reemplazada_por             |
      | una copia de "sintetico_20262_450002_410.xlsx" sin la columna del PI 5.2 está subida a la sección 410 y su carga está "RECHAZADA"             | POST   | /api/cargas/{carga_id}/mejora/declaracion | sin reemplazada_por             |
      | la carga A REEMPLAZADA y la carga B PUBLICADA que la reemplaza en la sección 410, y se escribe en A                                           | PUT    | /api/cargas/{carga_id}/mejora/borrador    | con reemplazada_por igual a B   |
      | la carga A REEMPLAZADA y la carga B PUBLICADA que la reemplaza en la sección 410, y se escribe en A                                           | POST   | /api/cargas/{carga_id}/mejora/declaracion | con reemplazada_por igual a B   |

  # El dueño de la base deja META_LOGRO sin DEFINIR solo en la base desechable. Ningún texto del profesor
  # resuelve una regla sin definir, así que este 409 manda sobre el 422 de la declaración incompleta.
  @US-47 @spec005 @corte1
  Escenario: Una regla sin definir detiene la declaración
    Dado que la base tiene un conjunto de reglas de prueba de Ambiental con META_LOGRO sin DEFINIR, y la API configurada con ese CONJUNTO_REGLAS
    Y que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" declara la versión 0
    Entonces la API responde 409 con el mensaje "El conjunto de reglas no define la meta o el nivel esperado. La declaración espera a la Coordinación." (propuesta)
    Y abet.mejora_declaracion no gana ninguna fila

  # D-37 (valor provisional, sí). La declaración anterior sigue vigente hasta que se declara la versión nueva, y
  # la nueva vuelve a nacer con el estado PROPUESTA.
  @US-47 @spec005 @corte1
  Escenario: Corregir una declaración deja la anterior guardada y vigente hasta declarar la nueva
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id, con su análisis declarado
    Cuando "docente410@example.invalid" guarda otro borrador con la corrección de la 410 y version 1
    Entonces GET /api/cargas/{carga_id}/mejora responde 200 con la declaración anterior vigente y borrador_pendiente verdadero
    Y el R-17 de esa carga sigue saliendo con el texto de la declaración anterior
    Cuando "docente410@example.invalid" declara la versión 2
    Entonces el R-17 de esa carga toma el texto nuevo de 5.1
    Y GET /api/cargas/{carga_id}/mejora responde los tres indicadores declarados con estado "PROPUESTA"
    Y abet.mejora_declaracion tiene 2 filas de esa carga, con la anterior y sus tres filas de abet.mejora_declaracion_pi intactas

  @US-47 @spec005 @corte1
  Escenario: El coordinador lee la declaración sin editarla ni ver el borrador
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id, con su análisis declarado
    Y que "docente410@example.invalid" guardó un borrador posterior en la versión 2
    Y que "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando se envía GET /api/cargas/{carga_id}/mejora
    Entonces la API responde 200 con la declaración vigente, borrador nulo y puede_editar falso

  @US-47 @spec005 @corte1 @delegado_a_vitest
  Esquema del escenario: P4 del coordinador muestra lo declarado sin campos ni botón
    Dado una respuesta de la ruta 14 <respuesta>
    Cuando "coordinacion@example.invalid" abre la pantalla P4 de esa carga
    Entonces P4 <resultado>

    Ejemplos:
      | respuesta                                                | resultado                                                                                                                                                  |
      | con la declaración vigente y puede_editar falso          | muestra cada registro declarado con el rótulo de su tipo y la marca «Propuesta», sin campos y sin el botón «Guardar declaración» (propuesta)               |
      | con solo un borrador, borrador nulo y puede_editar falso | dice «El profesor todavía no declara el análisis por indicador.» (propuesta), sin ningún texto                                                            |

  # (propuesta) P4, sección «Análisis por indicador», debajo de «Cómo va su sección». Un bloque por PI que lleva
  # registro, con el hallazgo de la ruta 13 copiado sin cambios y el rótulo de su tipo. Una OM rotula «Causa
  # probable» y «Acción de mejora», y una BP «Causa del logro» y «Buena práctica que conviene mantener o
  # compartir». Los enunciados de B28 y B33 siguen en el R-17 y no se repiten sobre los campos.
  @US-47 @spec005 @corte1 @delegado_a_vitest
  Escenario: P4 del profesor muestra un bloque por PI con los rótulos de su tipo
    Dado la respuesta de la ruta 13 de la 412 de 450002 y una respuesta de la ruta 14 con declaracion nulo, borrador nulo y puede_editar verdadero
    Cuando "docente.varias@example.invalid" abre la pantalla P4 de esa carga
    Entonces P4 muestra debajo de «Cómo va su sección» tres bloques, «5.1 · Buena práctica», «5.2 · Oportunidad de mejora» y «5.3 · Buena práctica» (propuestas)
    Y cada bloque empieza con el hallazgo de su PI copiado sin cambios de la ruta 13
    Y el bloque de 5.2 rotula sus campos «Causa probable» y «Acción de mejora» (propuestas)
    Y los bloques de 5.1 y 5.3 rotulan sus campos «Causa del logro» y «Buena práctica que conviene mantener o compartir» (propuestas)
    Y P4 no muestra ningún campo de responsable, plazo ni estado
    Y el botón «Guardar declaración» (propuesta) está deshabilitado mientras falte un campo
    Cuando el profesor completa los seis campos y declara
    Entonces P4 dice «Declarado el 21/11/2026 15:10» (propuesta) con la marca «Propuesta» (propuesta) en cada registro, y los bloques siguen disponibles para corregir

  @US-47 @spec005 @corte1 @delegado_a_vitest
  Escenario: Un PI sin calificaciones muestra su hallazgo sin campos
    Dado la respuesta de la ruta 13 del escenario «Un PI sin calificaciones sale sin dato, nunca en rojo y sin tipo de registro» de semaforo.feature
    Cuando "docente410@example.invalid" abre la pantalla P4 de esa carga
    Entonces P4 muestra los bloques de 5.1 y 5.2 con sus campos
    Y P4 muestra para 5.3 solo «5.3: sin calificaciones en esta carga.» (propuesta), sin campos

  # US-48: El borrador se guarda solo y no se pierde
  # La ruta 15 lleva una sola version por carga, y un PUT guarda todos los registros. Un PUT con una versión que
  # no es la guardada responde 409, y P4 ofrece elegir cuál conservar.

  @US-48 @spec005 @corte1
  Escenario: Un borrador parcial se acepta
    Dado que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_412.xlsx" está subido a la sección 412 con respuesta 201 y su carga_id
    Cuando "docente.varias@example.invalid" guarda el borrador con solo la causa de 5.2 «La entrega coincidió con la semana de parciales.» y version 0
    Entonces la API responde 200 con version 1
    Y GET /api/cargas/{carga_id}/mejora devuelve en el borrador esa causa en 5.2 y causa y accion nulas en los demás campos de 5.1, 5.2 y 5.3

  @US-48 @spec005 @corte1
  Escenario: Dos pestañas no se pisan el borrador
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que "docente410@example.invalid" guardó el borrador hasta la versión 3
    Cuando "docente410@example.invalid" guarda el borrador con otro texto en 5.1 y version 2
    Entonces la API responde 409 con el mensaje "Otra pestaña guardó un texto más reciente." (propuesta), los registros guardados y la versión 3
    Y el borrador guardado no cambia

  @US-48 @spec005 @corte1 @delegado_a_vitest
  Escenario: El borrador vuelve al abrir P4
    Dado una respuesta de la ruta 14 con un borrador de los registros de prueba de la 412 en la versión 3
    Cuando "docente.varias@example.invalid" abre la pantalla P4 de esa carga
    Entonces cada bloque trae la causa y la acción de su PI del borrador

  @US-48 @spec005 @corte1 @delegado_a_vitest
  Escenario: El guardado automático sale 2,5 segundos después de escribir y al salir de un campo
    Dado "docente.varias@example.invalid" en la pantalla P4 de la 412 con los bloques vacíos
    Cuando escribe en la causa de 5.2 y pasan 2,5 segundos
    Entonces sale un PUT a la ruta 15 con los tres indicadores y P4 dice «Borrador guardado a las …» (propuesta)
    Cuando escribe en la acción de 5.1 y sale del campo
    Entonces sale otro PUT sin esperar los 2,5 segundos

  @US-48 @spec005 @corte1 @delegado_a_vitest
  Escenario: Si el guardado falla, el texto sigue en pantalla
    Dado "docente410@example.invalid" en la pantalla P4 con texto escrito en la causa de 5.1
    Cuando el PUT a la ruta 15 responde 500
    Entonces P4 dice «No se pudo guardar el borrador. Su texto sigue en pantalla.» (propuesta)
    Y la causa de 5.1 conserva lo escrito

  @US-48 @spec005 @corte1 @delegado_a_vitest
  Escenario: Un 401 durante el guardado no pierde el texto
    Dado "docente410@example.invalid" en la pantalla P4 con texto escrito en la causa de 5.1
    Cuando el PUT a la ruta 15 responde 401
    Entonces P4 muestra el ingreso con el texto en memoria
    Y cuando el mismo usuario ingresa otra vez, el guardado se reintenta con la misma versión
    Pero con otro usuario, o después de «Salir», el texto se descarta

  @US-48 @spec005 @corte1 @delegado_a_vitest
  Escenario: El navegador no guarda el texto
    Dado "docente410@example.invalid" en la pantalla P4 con los bloques vacíos
    Cuando escribe en los campos de los tres bloques
    Entonces localStorage y sessionStorage quedan con 0 entradas

  # US-49: El R-17 solo con la declaración vigente completa
  # (propuesta) DeclaracionPendiente, subclase de R17NoDisponible, con 409 cuando la carga no tiene declaración
  # o cuando a la vigente le falta la fila de un PI con calificados, la misma regla de Q17. El 409 de una carga
  # no PUBLICADA manda sobre el de la declaración. Vale también para el coordinador (J-33), y toda carga
  # publicada antes de V1_12 queda en 409 hasta declarar, sin excepción por fecha (J-37). Cambia los escenarios
  # 1 a 4 de US-15 y la prueba de humo de US-17, que ahora declaran antes de descargar.

  @US-49 @spec005 @corte1
  Esquema del escenario: Sin declaración el R-17 no se entrega
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que la carga <situación>
    Cuando "docente410@example.invalid" descarga el R-17 de esa carga
    Entonces la API responde 409 con el mensaje "Complete la causa y la acción de cada indicador en la página de la carga antes de descargar el R-17." (propuesta)
    Y la respuesta no trae ningún archivo

    Ejemplos:
      | situación                                       |
      | no tiene ningún texto                           |
      | tiene solo un borrador con los tres registros   |

  @US-49 @spec005 @corte1
  Escenario: Con la declaración el R-17 se entrega
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id, con su análisis declarado
    Cuando "docente410@example.invalid" descarga el R-17 de esa carga
    Entonces la API responde 200 con el archivo "R017_450002_410_2026-2_PROVISIONAL.xlsx"

  @US-49 @spec005 @corte1
  Esquema del escenario: El coordinador recibe el mismo 409 sin declaración y el archivo con ella
    Dado que "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id<declarada>
    Cuando "coordinacion@example.invalid" descarga el R-17 de esa carga
    Entonces la API responde <respuesta>

    Ejemplos:
      | declarada                       | respuesta                                                                                                                                         |
      |                                 | 409 con el mensaje "Complete la causa y la acción de cada indicador en la página de la carga antes de descargar el R-17." (propuesta)            |
      | , con su análisis declarado     | 200 con el archivo "R017_450002_410_2026-2_PROVISIONAL.xlsx"                                                                                      |

  # D-36 (valor provisional, sí). Con R-PRUEBA-APROBADO (nivel esperado 2 y meta 70 %), los tres PI de la 410
  # quedan en 90,9 % VERDE, y la sección igual registra una BP por PI antes de obtener el R-17. El caso
  # muestra que también se analizan las causas cuando se supera el valor de referencia.
  @US-49 @spec005 @corte1
  Escenario: Una sección con todos sus PI en la meta también registra sus buenas prácticas
    Dado que la base tiene el conjunto "R-PRUEBA-APROBADO" de Ambiental en estado "APROBADO" con META_LOGRO 0,70, NIVEL_ESPERADO 2, CORTE_ROJO 0,50, TRATO_SIN_EVIDENCIA "SE_EXCLUYE_DEL_DENOMINADOR" y la conversión de sus 4 niveles, como en el caso A03 de pruebas.sql
    Y la API configurada con CONJUNTO_REGLAS "R-PRUEBA-APROBADO"
    Y que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/cargas/{carga_id}/indicadores
    Entonces los tres PI traen pct_sobre_calificados 90.9, semaforo "VERDE" y tipo_registro "BUENA_PRACTICA"
    Cuando "docente410@example.invalid" descarga el R-17 de esa carga
    Entonces la API responde 409 con el mensaje "Complete la causa y la acción de cada indicador en la página de la carga antes de descargar el R-17." (propuesta)
    Cuando "docente410@example.invalid" guarda el borrador con los registros de prueba de la 410 y version 0, y declara la versión 1
    Entonces abet.mejora_declaracion_pi guarda los tres PI con tipo "BUENA_PRACTICA"
    Y la descarga del R-17 de esa carga responde 200

  @US-49 @spec005 @corte1
  Escenario: El 409 de una carga rechazada manda sobre el de la declaración
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que una copia de "sintetico_20262_450002_410.xlsx" sin la columna del PI 5.2 está subida a la sección 410 y su carga está "RECHAZADA" con PI_DEL_PLAN_AUSENTE
    Cuando "docente410@example.invalid" descarga el R-17 de esa carga
    Entonces la API responde 409 con el mensaje "La carga no está publicada y no tiene R-17."
    Y la carga no tiene ninguna declaración

  @US-49 @spec005 @corte1
  Escenario: El comando r17 de una carga sin declaración termina sin escribir ningún archivo
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el administrador técnico corre el comando python -m abet_carga r17 para esa carga
    Entonces el comando termina con el mensaje "Complete la causa y la acción de cada indicador en la página de la carga antes de descargar el R-17." (propuesta)
    Y el comando no escribe ningún archivo

  @US-49 @spec005 @corte1 @delegado_a_vitest
  Escenario: P4 deshabilita el R-17 hasta que la carga tiene declaración
    Dado una respuesta de la ruta 14 con declaracion nulo
    Cuando "docente410@example.invalid" abre la pantalla P4 de esa carga
    Entonces P4 muestra «Descargar R-17» deshabilitado con «El R-17 se habilita cuando registre y declare la causa y la acción de cada indicador.» (propuesta)
    Y después de declarar P4 ofrece el enlace «Descargar R-17»
    Cuando "coordinacion@example.invalid" abre la pantalla P4 de esa carga sin declaración
    Entonces P4 dice «El R-17 se habilita cuando el profesor de la sección declare el análisis por indicador.» (propuesta)

  # (propuesta, J-32) P4 es el único lugar que ofrece el R-17, y P6 de la spec 004 cambia su enlace al R-17
  # (FR-015 de esa spec) por «Ver la carga de la sección N de A», de modo que ningún enlace abre un 409 en
  # JSON.
  @US-49 @spec005 @corte1 @delegado_a_vitest
  Escenario: P2, P5 y P6 no ofrecen el R-17 y llevan a P4
    Dado una sección 410 de "450002" con una carga PUBLICADA
    Cuando "coordinacion@example.invalid" abre P2 y P5, y "docente410@example.invalid" abre P6
    Entonces P2 y P5 no ofrecen «Descargar R-17» y llevan a P4
    Y P6 ofrece «Ver la carga de la sección 410 de 450002» (propuesta) en lugar del enlace al R-17

  # US-53: El análisis por indicador no lleva datos de estudiantes
  # (AD-11) El mismo patrón en las rutas 15 y 16 y en los CHECK de causa y accion de las tablas por PI. La
  # violación del CHECK sale como 422 y nunca como 500. La validación corre después del 403, y ni el error ni
  # el registro de la aplicación repiten el texto. Q16 busca códigos y correos en las cuatro columnas de texto
  # de abet.mejora_borrador_pi y abet.mejora_declaracion_pi, y Q17 lista cada declaración vigente de una carga
  # PUBLICADA a la que le falta la fila de un PI de abet.carga_columna con al menos una medición CALIFICADO.
  # Los dos van iguales en db/plataforma/neon/controles_neon.sql.

  @US-53 @spec005 @corte1
  Esquema del escenario: Un código o un correo de estudiante se rechaza y no se guarda ni como borrador
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" guarda el borrador con <campo> <texto>, los demás registros de prueba de la 410 y version 0
    Entonces la API responde 422 con el mensaje "La declaración no puede llevar códigos ni correos. Describa las causas y las acciones sin datos de estudiantes." (propuesta)
    Y abet.mejora_borrador y abet.mejora_borrador_pi no ganan ninguna fila
    Y el cuerpo de la respuesta no contiene el texto <texto>

    Ejemplos:
      | campo             | texto                                    |
      | la causa de 5.2   | "99000004 no entregó"                    |
      | la acción de 5.1  | "escribir a alguien@example.invalid"     |

  @US-53 @spec005 @corte1
  Esquema del escenario: Un número de 9 dígitos o una fecha no son un código de estudiante
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" guarda el borrador con la causa de 5.1 <texto> y la acción de 5.1 "Mover la entrega a la semana 10." con version 0
    Entonces la API responde 200 con version 1

    Ejemplos:
      | texto                                   |
      | "Resolución 990000041 del periodo"      |
      | "Entrega del 18/11/2026 en parciales"   |

  @US-53 @spec005 @corte1
  Escenario: La base rechaza un código en el borrador aunque la API se salte la validación
    Dado una conexión directa con el rol abet_app y la carga PUBLICADA de la sección 410 con la cabecera de su borrador
    Cuando esa conexión inserta en abet.mejora_borrador_pi la causa "99000004 no entregó" para el PI 5.1
    Entonces la base rechaza la inserción por la restricción "ck_mejora_borrador_pi_sin_codigos"

  @US-53 @spec005 @corte1
  Escenario: La base rechaza un correo en la declaración
    Dado una conexión directa del dueño de la base y la carga PUBLICADA de la sección 410 con la cabecera de una declaración
    Cuando esa conexión inserta en abet.mejora_declaracion_pi la acción "escribir a alguien@example.invalid" para el PI 5.1
    Entonces la base rechaza la inserción por la restricción "ck_mejora_declaracion_pi_sin_codigos"

  @US-53 @spec005 @corte1 @delegado_a_vitest
  Escenario: Un 422 durante el guardado automático deja el texto y no reintenta en bucle
    Dado "docente410@example.invalid" en la pantalla P4 con la causa de 5.1 que trae «99000004 no entregó»
    Cuando el PUT a la ruta 15 responde 422
    Entonces P4 deja el texto en pantalla con el mensaje «La declaración no puede llevar códigos ni correos. Describa las causas y las acciones sin datos de estudiantes.» (propuesta)
    Y P4 no repite el PUT mientras el texto no cambie
    Y P4 muestra sobre los bloques de «Análisis por indicador» la nota «No escriba nombres, códigos ni correos de estudiantes.» (propuesta)

  @US-53 @spec005 @corte1
  Escenario: Las rutas 13 a 16 no se guardan en caché y no traen datos de estudiantes
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando se envían GET /api/cargas/{carga_id}/indicadores, GET /api/cargas/{carga_id}/mejora, PUT /api/cargas/{carga_id}/mejora/borrador y POST /api/cargas/{carga_id}/mejora/declaracion con cuerpos válidos
    Entonces cada respuesta trae Cache-Control: no-store
    Y ningún cuerpo contiene los códigos "99000001" a "99000011", nombres ni correos de estudiantes

  @US-53 @spec005 @corte1
  Escenario: Q16 y Q17 dan 0 filas con declaraciones sanas
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id, con su análisis declarado
    Y que "sintetico_20262_450002_412.xlsx" está subido a la sección 412 con respuesta 201 y su carga_id, con su análisis declarado
    Cuando el dueño de la base corre db/pruebas/pruebas.sql
    Entonces Q16 y Q17 devuelven 0 filas

  # El caso arma la falta en una transacción que se deshace, como los casos de Q06 a Q14 de pruebas.sql.
  @US-53 @spec005 @corte1
  Escenario: Q17 ve un PI con calificados sin su registro en la declaración vigente
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id, con su análisis declarado
    Y una transacción del dueño de la base que quita la fila de 5.3 de la declaración vigente de esa carga y se deshace al final
    Cuando corre Q17 dentro de esa transacción
    Entonces Q17 devuelve 1 fila con esa carga y el PI 5.3, sin ningún texto del profesor

  @US-53 @spec005 @corte1
  Escenario: Neon corre los mismos controles
    Dado db/plataforma/neon/controles_neon.sql
    Cuando pruebas.sql lo compara con sus controles de 0 filas
    Entonces trae Q16 y Q17 iguales salvo espacios, cada uno con su \set qNN :ROW_COUNT, y su cierre los suma

  # US-54: El reemplazo trae el análisis anterior como borrador
  # (AD-17) La herencia ocurre al leer, sin escribir en la transacción de la subida, y va por pi_id. Copia solo
  # los PI que la carga nueva mide y que en ella llevan registro, cada uno con el tipo que fija el semáforo de
  # la carga nueva. El texto se guarda en la carga nueva recién con el primer PUT.

  @US-54 @spec005 @corte1
  Escenario: La carga nueva hereda el análisis declarado con el tipo de sus cifras
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id A, con su análisis declarado
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={A} con una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en la fila 9
    Y se envía GET /api/cargas/{B}/mejora
    Entonces la API responde 200 con borrador con los registros declarados de A en 5.1, 5.2 y 5.3, version 0 y heredado_de igual a A
    Y 5.1 y 5.2 traen tipo "OPORTUNIDAD_MEJORA", y 5.3 trae tipo "BUENA_PRACTICA" con su causa y su acción de A
    Y el R-17 de la carga B responde 409 hasta declarar

  @US-54 @spec005 @corte1
  Escenario: Un PI que queda sin calificaciones en la carga nueva no se hereda
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id A, con su análisis declarado
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={A} con una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en sus 11 filas
    Y se envía GET /api/cargas/{B}/mejora
    Entonces la API responde 200 con borrador con los registros de A solo en 5.1 y 5.2 y heredado_de igual a A

  @US-54 @spec005 @corte1
  Esquema del escenario: Sin texto declarado se hereda lo que haya, o nada
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id A<texto_de_A>
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={A} con una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en la fila 9
    Y se envía GET /api/cargas/{B}/mejora
    Entonces la API responde 200 con <herencia>

    Ejemplos:
      | texto_de_A                                                    | herencia                                                                         |
      |                                                               | borrador nulo y heredado_de nulo                                                 |
      | , con un borrador guardado y sin declaración                  | el borrador de A como borrador, version 0 y heredado_de igual a A                |

  @US-54 @spec005 @corte1
  Escenario: Subir el mismo archivo no cambia nada
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id A, con su análisis declarado
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={A} con el archivo "sintetico_20262_450002_410.xlsx"
    Entonces la API responde 200 sin carga nueva
    Y abet.carga, abet.mejora_borrador y abet.mejora_borrador_pi no ganan ninguna fila

  # El coordinador no sube una carga nueva (BR-ACCESO-08), pero desde el corte 2 reemplaza la carga publicada de
  # cualquier sección de la carrera (D-11, BR-CARGA-19 y app/permisos.puede_reemplazar()), así que este reemplazo existe.
  @US-54 @spec005 @corte1
  Escenario: Un reemplazo hecho por coordinación hereda igual y coordinación no ve el texto heredado
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id A, con su análisis declarado
    Y que "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando "coordinacion@example.invalid" reemplaza A con una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en la fila 9
    Y se envía GET /api/cargas/{B}/mejora
    Entonces la API responde 200 con heredado_de igual a A y borrador nulo
    Y la respuesta no trae el texto heredado
    Y GET /api/cargas/{B}/mejora de "docente410@example.invalid" trae el borrador heredado

  @US-54 @spec005 @corte1
  Escenario: Un PUT a la carga reemplazada responde 409 con la carga nueva
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que la carga A REEMPLAZADA y la carga B PUBLICADA que la reemplaza en la sección 410
    Cuando "docente410@example.invalid" guarda el borrador en la carga A con la causa de 5.1 «La entrega coincidió con la semana de parciales.» y version 0
    Entonces la API responde 409 con el mensaje "La carga no está publicada y no admite causas ni acciones." (propuesta) y reemplazada_por igual a B

  @US-54 @spec005 @corte1 @delegado_a_vitest
  Escenario: P4 de la carga reemplazada conserva el texto y lo lleva a la nueva
    Dado una respuesta 409 de la ruta 15 con reemplazada_por igual a la carga 2
    Cuando "docente410@example.invalid" está en la pantalla P4 de la carga reemplazada con texto escrito en sus bloques
    Entonces P4 conserva el texto y ofrece «Llevar el texto a la carga 2» (propuesta)
