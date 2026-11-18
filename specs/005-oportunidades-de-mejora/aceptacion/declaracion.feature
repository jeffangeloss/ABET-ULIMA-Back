# language: es
#
# Escenarios de aceptación de la declaración de las causas y las acciones de mejora, de las historias de
# usuario (user stories, US) US-47, US-48, US-49, US-53 y US-54 de la spec 005-oportunidades-de-mejora (épica
# EP-05, propuesta). Jefferson pide el 2026-11-18 que el profesor complete en el sistema los recuadros A
# (causas) y B (acciones) del R-17, que hoy salen vacíos y editables, y que ningún R-17 llegue a la
# acreditación sin ellos (spec.md, Input, y C-03 a C-05, C-10, C-11 y C-13 de la síntesis de la auditoría).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid y los códigos de
# estudiante 99000001 a 99000011. Ninguna contraseña aparece escrita aquí, porque la prueba asigna al azar la
# contraseña con que abre cada sesión, sin guardarla en el repositorio.
# - Los textos de la declaración de la 410 son las causas «La entrega coincidió con la semana de parciales.»
#   y las acciones «Mover la entrega a la semana 10 y revisar el avance en clase.», los mismos de
#   r17_desde_la_base.feature. La corrección usa las causas «La entrega coincidió con la semana de parciales
#   y de feriado.» y las acciones «Mover la entrega a la semana 10 y revisar el avance en tutoría.»
#   (propuestas).
# - Los exports viven en tests/datos_inventados/. Su carga PUBLICADA sale de «que "sintetico_20262_450002_410
#   .xlsx" está subido a la sección 410 con respuesta 201 y su carga_id» de la spec 001.
#
# Vocabulario de los pasos, el de carga.feature, reemplazo_y_cargas.feature y r17_constancia.feature de la
# spec 001 y el de resultados.feature de la spec 004.
# - Ruta 14 (propuesta) GET /api/cargas/{carga_id}/mejora. Responde declaracion (causas, acciones,
#   declarada_en) o nulo, borrador (causas, acciones, version, actualizado_en) o nulo, borrador_pendiente (hay
#   un borrador posterior a la última declaración), heredado_de (US-54) y puede_editar.
# - Ruta 15 (propuesta) PUT /api/cargas/{carga_id}/mejora/borrador con {causas, acciones, version}.
# - Ruta 16 (propuesta) POST /api/cargas/{carga_id}/mejora/declaracion con {version}, que declara esa versión
#   exacta del borrador. Responde 201 con declarada_en.
# - «guarda el borrador» es un PUT a la ruta 15 con la versión que la ruta 14 devolvió (0 si no hay borrador)
#   y «declara la versión N» es un POST a la ruta 16 con {"version": N}. Escribe solo el profesor asignado,
#   con puede_declarar() de app/permisos.py. El coordinador lee con puede_leer() y nunca recibe el texto del
#   borrador. Orden de las respuestas 401, 403, 422 y 409, con el cuerpo leído a mano después del alcance.
# - La ruta 7 es GET /api/cargas/{carga_id}/r17.xlsx. «con sus causas y acciones declaradas» llama a
#   declarar() de tests/cargas_de_prueba.py (FR-017).
# - Texto (AD-10). El Back normaliza a NFC, cambia \r\n por \n, rechaza los caracteres de control salvo \n y
#   \t y cuenta puntos de código, hasta 2000 por campo.
# - El patrón de códigos y correos (AD-11) es un número de exactamente 8 dígitos no rodeado de otros dígitos
#   o un correo. Es el mismo en las rutas y en los CHECK ck_mejora_borrador_sin_codigos y
#   ck_mejora_declaracion_sin_codigos. Un nombre de estudiante escrito en el texto no se detecta, y Jefferson
#   acepta que BR-R17-07 y la regla 6 de AGENTS.md se cumplan en estos dos campos por aviso y no por
#   construcción (J-36).
# - Cada escenario corre en una base desechable propia, así que los carga_id salen de la API o de la base y
#   nunca se suponen.
# - @delegado_a_vitest marca un escenario de la pantalla P4 (o de P2 y P5) que prueba Vitest en el Front.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec. D-36, D-37
#   y D-34 siguen abiertas con la Coordinación, y J-32 y J-33 esperan la respuesta de Jefferson.

Característica: Declaración de las causas y las acciones de mejora, desde P4 y guardada en la base
  Como profesor de Ingeniería Ambiental, quiero completar en P4 los recuadros A y B del R-17 y que el R-17 de
  mi sección solo se entregue con esa declaración, para que las causas de mi resultado y las acciones para
  mejorarlo queden en la base y en el reporte.

  Antecedentes:
    Dado una base PostgreSQL 18 desechable con las migraciones V1_01 a V1_12 y los datos de db/datos/periodo_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y plan_medicion registra los PI 5.1, 5.2 y 5.3 para la asignatura "450002" en "2026-2"
    Y acceso.docente_seccion asigna la sección 410 de "450002" a "docente410@example.invalid" y la 411 de "450002" a "docente411@example.invalid"
    Y "coordinacion@example.invalid" activo con rol "COORDINADOR" y sin secciones en acceso.docente_seccion
    Y ninguna sección de 2026-2 tiene cargas

  # US-47: Declarar las causas y las acciones en P4
  # (propuesta) Base de J-30. V1_12 crea abet.mejora_borrador (una fila por carga, con versión) y
  # abet.mejora_declaracion (solo INSERT, causas y acciones no nulos y no en blanco). La declaración vigente de
  # una carga es la última.

  @US-47 @spec005 @corte1
  Escenario: El profesor guarda el borrador y declara la versión 1
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" guarda el borrador con las causas «La entrega coincidió con la semana de parciales.» y las acciones «Mover la entrega a la semana 10 y revisar el avance en clase.» con version 0
    Y declara la versión 1
    Entonces la API responde 201 con declarada_en
    Y GET /api/cargas/{carga_id}/mejora responde 200 con la declaración de los mismos dos textos y borrador_pendiente falso

  @US-47 @spec005 @corte1
  Escenario: Una carga sin texto responde con la declaración y el borrador nulos
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/cargas/{carga_id}/mejora
    Entonces la API responde 200 con declaracion nulo, borrador nulo y puede_editar verdadero

  @US-47 @spec005 @corte1
  Esquema del escenario: Declarar con un campo vacío o en blanco no crea ninguna declaración
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que "docente410@example.invalid" guardó en la versión 1 un borrador con las causas <causas> y las acciones <acciones>
    Cuando "docente410@example.invalid" declara la versión 1
    Entonces la API responde 422 con el mensaje "Complete las causas y las acciones." (propuesta)
    Y abet.mejora_declaracion no gana ninguna fila

    Ejemplos:
      | causas                                | acciones                          |
      | ""                                    | "Mover la entrega a la semana 10." |
      | "La entrega coincidió con parciales." | ""                                |
      | "   "                                 | "   "                             |

  # Los 2001 puntos de código y el carácter de control U+0007 se rechazan al guardar el borrador. El borrador
  # guardado antes no cambia.
  @US-47 @spec005 @corte1
  Esquema del escenario: Un texto demasiado largo o con caracteres de control se rechaza y nada cambia
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" guarda el borrador con las causas <causas> y las acciones "Mover la entrega a la semana 10." con version 0
    Entonces la API responde 422 con el mensaje "<mensaje>" (propuesta)
    Y abet.mejora_borrador no gana ninguna fila

    Ejemplos:
      | causas                                         | mensaje                                             |
      | un texto de 2001 puntos de código              | Cada campo admite hasta 2000 caracteres.            |
      | "Entrega tardía" con el carácter de control U+0007 | El texto trae caracteres que no se pueden guardar.  |

  @US-47 @spec005 @corte1
  Esquema del escenario: Solo el profesor asignado escribe, aunque el cuerpo no sea JSON
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que "<correo>" tiene la sesión iniciada con rol "<rol>"
    Cuando se envía <método> <ruta> con un cuerpo que no es JSON
    Entonces la API responde 403 con el mensaje "La sección no está a su cargo."
    Y abet.mejora_borrador y abet.mejora_declaracion no ganan ninguna fila

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

  # D-37 (valor provisional, sí). La declaración anterior sigue vigente hasta que se declara la versión nueva.
  @US-47 @spec005 @corte1
  Escenario: Corregir una declaración deja la anterior guardada y vigente hasta declarar la nueva
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id, con sus causas y acciones declaradas
    Cuando "docente410@example.invalid" guarda otro borrador con las causas «La entrega coincidió con la semana de parciales y de feriado.» y las acciones «Mover la entrega a la semana 10 y revisar el avance en tutoría.» con version 1
    Entonces GET /api/cargas/{carga_id}/mejora responde 200 con la declaración anterior vigente y borrador_pendiente verdadero
    Y el R-17 de esa carga sigue saliendo con el texto de la declaración anterior
    Cuando "docente410@example.invalid" declara la versión 2
    Entonces el R-17 de esa carga toma el texto nuevo
    Y abet.mejora_declaracion tiene 2 filas de esa carga, con la anterior intacta

  @US-47 @spec005 @corte1
  Escenario: El coordinador lee la declaración sin editarla ni ver el borrador
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id, con sus causas y acciones declaradas
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
      | respuesta                                                | resultado                                                                                                                                  |
      | con la declaración vigente y puede_editar falso          | muestra los textos declarados, sin campos y sin el botón «Guardar declaración» (propuesta)                                                 |
      | con solo un borrador, borrador nulo y puede_editar falso | dice «El profesor todavía no declara las causas y las acciones.» (propuesta), sin ningún texto                                             |

  @US-47 @spec005 @corte1 @delegado_a_vitest
  Escenario: P4 del profesor muestra los enunciados del R-17 y habilita la declaración solo con los dos campos
    Dado una respuesta de la ruta 14 con declaracion nulo, borrador nulo y puede_editar verdadero
    Cuando "docente410@example.invalid" abre la pantalla P4 de esa carga
    Entonces P4 muestra los enunciados de las celdas B28 y B33 de la plantilla sobre cada campo
    Y el botón «Guardar declaración» (propuesta) está deshabilitado mientras falte un campo
    Cuando el profesor completa los dos campos y declara
    Entonces P4 dice «Declarado el 18/11/2026 15:10» (propuesta) con los dos textos declarados y el formulario sigue disponible para corregir

  # US-48: El borrador se guarda solo y no se pierde
  # La ruta 15 lleva version. Un PUT con una versión que no es la guardada responde 409, y P4 ofrece elegir
  # cuál conservar.

  @US-48 @spec005 @corte1
  Escenario: Un borrador parcial se acepta
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" guarda el borrador con solo las causas «La entrega coincidió con la semana de parciales.» con version 0
    Entonces la API responde 200 con version 1
    Y GET /api/cargas/{carga_id}/mejora devuelve esas causas y acciones nulo

  @US-48 @spec005 @corte1
  Escenario: Dos pestañas no se pisan el borrador
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que "docente410@example.invalid" guardó el borrador hasta la versión 3
    Cuando "docente410@example.invalid" guarda el borrador con otro texto y version 2
    Entonces la API responde 409 con el mensaje "Otra pestaña guardó un texto más reciente." (propuesta), el texto guardado y la versión 3
    Y el borrador guardado no cambia

  @US-48 @spec005 @corte1 @delegado_a_vitest
  Escenario: El borrador vuelve al abrir P4
    Dado una respuesta de la ruta 14 con un borrador de causas y acciones en la versión 3
    Cuando "docente410@example.invalid" abre la pantalla P4 de esa carga
    Entonces los dos campos traen el texto del borrador

  @US-48 @spec005 @corte1 @delegado_a_vitest
  Escenario: El guardado automático sale 2,5 segundos después de escribir y al salir del campo
    Dado "docente410@example.invalid" en la pantalla P4 con el formulario vacío
    Cuando escribe en el campo A y pasan 2,5 segundos
    Entonces sale un PUT a la ruta 15 y P4 dice «Borrador guardado a las …» (propuesta)
    Cuando escribe en el campo B y sale del campo
    Entonces sale otro PUT sin esperar los 2,5 segundos

  @US-48 @spec005 @corte1 @delegado_a_vitest
  Escenario: Si el guardado falla, el texto sigue en pantalla
    Dado "docente410@example.invalid" en la pantalla P4 con texto escrito en el campo A
    Cuando el PUT a la ruta 15 responde 500
    Entonces P4 dice «No se pudo guardar el borrador. Su texto sigue en pantalla.» (propuesta)
    Y el campo A conserva lo escrito

  @US-48 @spec005 @corte1 @delegado_a_vitest
  Escenario: Un 401 durante el guardado no pierde el texto
    Dado "docente410@example.invalid" en la pantalla P4 con texto escrito en el campo A
    Cuando el PUT a la ruta 15 responde 401
    Entonces P4 muestra el ingreso con el texto en memoria
    Y cuando el mismo usuario ingresa otra vez, el guardado se reintenta con la misma versión
    Pero con otro usuario, o después de «Salir», el texto se descarta

  @US-48 @spec005 @corte1 @delegado_a_vitest
  Escenario: El navegador no guarda el texto
    Dado "docente410@example.invalid" en la pantalla P4 con el formulario vacío
    Cuando escribe en los dos campos
    Entonces localStorage y sessionStorage quedan con 0 entradas

  # US-49: El R-17 solo con la declaración
  # (propuesta) DeclaracionPendiente, subclase de R17NoDisponible, con 409. El 409 de una carga no PUBLICADA
  # manda sobre el de la declaración. Vale también para el coordinador (J-33), y toda carga publicada antes de
  # V1_12 queda en 409 hasta declarar, sin excepción por fecha (J-37). Cambia los escenarios 1 a 4 de US-15 y
  # la prueba de humo de US-17, que ahora declaran antes de descargar.

  @US-49 @spec005 @corte1
  Esquema del escenario: Sin declaración el R-17 no se entrega
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que la carga <situación>
    Cuando "docente410@example.invalid" descarga el R-17 de esa carga
    Entonces la API responde 409 con el mensaje "Complete las causas y las acciones en la página de la carga antes de descargar el R-17." (propuesta)
    Y la respuesta no trae ningún archivo

    Ejemplos:
      | situación                          |
      | no tiene ningún texto              |
      | tiene solo un borrador             |

  @US-49 @spec005 @corte1
  Escenario: Con la declaración el R-17 se entrega
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id, con sus causas y acciones declaradas
    Cuando "docente410@example.invalid" descarga el R-17 de esa carga
    Entonces la API responde 200 con el archivo "R017_450002_410_2026-2_PROVISIONAL.xlsx"

  @US-49 @spec005 @corte1
  Esquema del escenario: El coordinador recibe el mismo 409 sin declaración y el archivo con ella
    Dado que "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id<declarada>
    Cuando "coordinacion@example.invalid" descarga el R-17 de esa carga
    Entonces la API responde <respuesta>

    Ejemplos:
      | declarada                                  | respuesta                                                                                                          |
      |                                            | 409 con el mensaje "Complete las causas y las acciones en la página de la carga antes de descargar el R-17." (propuesta) |
      | , con sus causas y acciones declaradas     | 200 con el archivo "R017_450002_410_2026-2_PROVISIONAL.xlsx"                                                       |

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
    Entonces el comando termina con el mensaje "Complete las causas y las acciones en la página de la carga antes de descargar el R-17." (propuesta)
    Y el comando no escribe ningún archivo

  @US-49 @spec005 @corte1 @delegado_a_vitest
  Escenario: P4 deshabilita el R-17 hasta que la carga tiene declaración
    Dado una respuesta de la ruta 14 con declaracion nulo
    Cuando "docente410@example.invalid" abre la pantalla P4 de esa carga
    Entonces P4 muestra «Descargar R-17» deshabilitado con «El R-17 se habilita cuando complete y guarde las causas y las acciones.» (propuesta)
    Y después de declarar P4 ofrece el enlace «Descargar R-17»
    Cuando "coordinacion@example.invalid" abre la pantalla P4 de esa carga sin declaración
    Entonces P4 dice «El R-17 se habilita cuando el profesor de la sección declare las causas y las acciones.» (propuesta)

  # (propuesta, J-32) P4 es el único lugar que ofrece el R-17, y P6 de la spec 004 cambia su enlace al R-17
  # (FR-015 de esa spec) por «Ver la carga de la sección N de A», de modo que ningún enlace abre un 409 en
  # JSON.
  @US-49 @spec005 @corte1 @delegado_a_vitest
  Escenario: P2, P5 y P6 no ofrecen el R-17 y llevan a P4
    Dado una sección 410 de "450002" con una carga PUBLICADA
    Cuando "coordinacion@example.invalid" abre P2 y P5, y "docente410@example.invalid" abre P6
    Entonces P2 y P5 no ofrecen «Descargar R-17» y llevan a P4
    Y P6 ofrece «Ver la carga de la sección 410 de 450002» (propuesta) en lugar del enlace al R-17

  # US-53: La declaración no lleva datos de estudiantes
  # (AD-11) El mismo patrón en las rutas 15 y 16 y en los CHECK. La violación del CHECK sale como 422 y nunca
  # como 500. La validación corre después del 403, y ni el error ni el registro de la aplicación repiten el
  # texto.

  @US-53 @spec005 @corte1
  Esquema del escenario: Un código o un correo de estudiante se rechaza y no se guarda ni como borrador
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" guarda el borrador con <campo> <texto> y el otro campo sin datos de estudiantes con version 0
    Entonces la API responde 422 con el mensaje "La declaración no puede llevar códigos ni correos. Describa las causas y las acciones sin datos de estudiantes." (propuesta)
    Y abet.mejora_borrador no gana ninguna fila
    Y el cuerpo de la respuesta no contiene el texto <texto>

    Ejemplos:
      | campo           | texto                                    |
      | las causas      | "99000004 no entregó"                    |
      | las acciones    | "escribir a alguien@example.invalid"     |

  @US-53 @spec005 @corte1
  Esquema del escenario: Un número de 9 dígitos o una fecha no son un código de estudiante
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando "docente410@example.invalid" guarda el borrador con las causas <texto> y las acciones "Mover la entrega a la semana 10." con version 0
    Entonces la API responde 200 con version 1

    Ejemplos:
      | texto                                   |
      | "Resolución 990000041 del periodo"      |
      | "Entrega del 18/11/2026 en parciales"   |

  @US-53 @spec005 @corte1
  Escenario: La base rechaza un código en el borrador aunque la API se salte la validación
    Dado una conexión directa con el rol abet_app y una carga EN_CURSO de la sección 410
    Cuando esa conexión inserta en abet.mejora_borrador las causas "99000004 no entregó"
    Entonces la base rechaza la inserción por la restricción "ck_mejora_borrador_sin_codigos"

  @US-53 @spec005 @corte1 @delegado_a_vitest
  Escenario: Un 422 durante el guardado automático deja el texto y no reintenta en bucle
    Dado "docente410@example.invalid" en la pantalla P4 con el campo A que trae «99000004 no entregó»
    Cuando el PUT a la ruta 15 responde 422
    Entonces P4 deja el texto en pantalla con el mensaje «La declaración no puede llevar códigos ni correos. Describa las causas y las acciones sin datos de estudiantes.» (propuesta)
    Y P4 no repite el PUT mientras el texto no cambie
    Y P4 muestra sobre el formulario la nota «No escriba nombres, códigos ni correos de estudiantes.» (propuesta)

  @US-53 @spec005 @corte1
  Escenario: Las rutas 13 a 16 no se guardan en caché y no traen datos de estudiantes
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando se envían GET /api/cargas/{carga_id}/indicadores, GET /api/cargas/{carga_id}/mejora, PUT /api/cargas/{carga_id}/mejora/borrador y POST /api/cargas/{carga_id}/mejora/declaracion con cuerpos válidos
    Entonces cada respuesta trae Cache-Control: no-store
    Y ningún cuerpo contiene los códigos "99000001" a "99000011", nombres ni correos de estudiantes

  # US-54: El reemplazo trae el texto anterior como borrador
  # (AD-17) La herencia ocurre al leer, sin escribir en la transacción de la subida. El texto se guarda en la
  # carga nueva recién con el primer PUT.

  @US-54 @spec005 @corte1
  Escenario: La carga nueva hereda como borrador la declaración de la carga reemplazada
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id A, con sus causas y acciones declaradas
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={A} con una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en la fila 9
    Y se envía GET /api/cargas/{B}/mejora
    Entonces la API responde 200 con borrador con los textos declarados de A, version 0 y heredado_de igual a A
    Y el R-17 de la carga B responde 409 hasta declarar

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
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id A, con sus causas y acciones declaradas
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={A} con el archivo "sintetico_20262_450002_410.xlsx"
    Entonces la API responde 200 sin carga nueva
    Y abet.carga y abet.mejora_borrador no ganan ninguna fila

  # El coordinador no sube una carga nueva (BR-ACCESO-08), pero desde el corte 2 reemplaza la carga publicada de
  # cualquier sección de la carrera (D-11, BR-CARGA-19 y app/permisos.puede_reemplazar()), así que este reemplazo existe.
  @US-54 @spec005 @corte1
  Escenario: Un reemplazo hecho por coordinación hereda igual y coordinación no ve el texto heredado
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id A, con sus causas y acciones declaradas
    Y que "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando "coordinacion@example.invalid" reemplaza A con una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en la fila 9
    Y se envía GET /api/cargas/{B}/mejora
    Entonces la API responde 200 con heredado_de igual a A y borrador nulo
    Y la respuesta no trae el texto heredado

  @US-54 @spec005 @corte1
  Escenario: Un PUT a la carga reemplazada responde 409 con la carga nueva
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que la carga A REEMPLAZADA y la carga B PUBLICADA que la reemplaza en la sección 410
    Cuando "docente410@example.invalid" guarda el borrador en la carga A con las causas «La entrega coincidió con la semana de parciales.» y version 0
    Entonces la API responde 409 con el mensaje "La carga no está publicada y no admite causas ni acciones." (propuesta) y reemplazada_por igual a B

  @US-54 @spec005 @corte1 @delegado_a_vitest
  Escenario: P4 de la carga reemplazada conserva el texto y lo lleva a la nueva
    Dado una respuesta 409 de la ruta 15 con reemplazada_por igual a la carga 2
    Cuando "docente410@example.invalid" está en la pantalla P4 de la carga reemplazada con texto escrito
    Entonces P4 conserva el texto y ofrece «Llevar el texto a la carga 2» (propuesta)
