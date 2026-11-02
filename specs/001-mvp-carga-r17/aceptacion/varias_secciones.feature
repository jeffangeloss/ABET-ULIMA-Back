# language: es
#
# Escenarios de aceptación del profesor que dicta varias secciones de varias asignaturas, de las
# historias de usuario (user stories, US) US-06, US-07, US-09 y US-13 del corte 1 de la spec
# 001-mvp-carga-r17. Jefferson pide el 2026-10-28 que cada profesor cargue el export de cada sección
# solo en esa sección y aprueba sumar estos seis escenarios a la spec (spec.md, Clarifications). Los
# datos de periodo_2026_2_inventado.sql tienen un profesor por sección y una sola asignatura, así que
# este archivo suma un profesor con tres secciones de dos asignaturas. Las reglas de negocio (business
# rules, BR) que prueba son BR-ACCESO-07 y BR-ACCESO-08 de acceso.spec.md y BR-CARGA-03, BR-CARGA-09 y
# BR-CARGA-11 de carga-export.spec.md.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid. Ninguna
# contraseña aparece escrita aquí, porque el script de datos no crea credenciales y la prueba asigna al
# azar la contraseña con que abre la sesión, sin guardarla en el repositorio.
# - db/datos/varias_secciones_2026_2_inventado.sql corre después de periodo_2026_2_inventado.sql, solo
#   en las bases desechables de estas pruebas y nunca en Neon, donde D-09 y D-13 fijan los datos del
#   piloto. Registra a docente.varias@example.invalid, activo y con rol PROFESOR, y le asigna la 412
#   de 450002 «Principios de Ingeniería Sostenible» y la 410 y la 412 de 450010 «Gestión Sostenible de
#   Residuos».
#   Siembra además el plan de medición de 450010 en 2026-2 con los indicadores de desempeño
#   (performance indicators, PI) 2.1 y 2.2 del resultado del estudiante (student outcome, SO) 2 y el PI
#   5.1 del SO 5, los dos SO que asignatura_so le asigna con el instrumento Trabajo Integrador. El plan
#   de 450002 conserva 5.1, 5.2 y 5.3.
# - La 410 de 450002 sigue siendo solo de docente410@example.invalid, la 411 solo de
#   docente411@example.invalid y el coordinador sigue sin secciones.
# - Las dos secciones 412 son de asignaturas distintas, para probar que el mismo número de sección en
#   otra asignatura no se confunde. abet.seccion identifica cada sección por periodo, asignatura y
#   número (uq_seccion).
# - Los exports viven en tests/datos_inventados/, con 11 filas y la hoja
#   gc_SINTETICO_20262_<asignatura>_<sección>_f. sintetico_20262_450002_412.xlsx trae los códigos
#   99000023 a 99000033, sintetico_20262_450010_410.xlsx los 99000034 a 99000044 y
#   sintetico_20262_450010_412.xlsx los 99000045 a 99000055. Ningún rango se cruza con otro, para que la
#   consulta de control Q08 no vea a un estudiante en dos secciones de la misma asignatura. Cada
#   export trae una columna por PI del plan de su asignatura, con niveles de 1 a 4 en sus 11 filas.
#
# Vocabulario de los pasos, el de carga.feature con la asignatura a la vista.
# - «el profesor» es docente.varias@example.invalid, con la sesión que abren los Antecedentes.
# - «subir X a la sección N de A» es la petición POST /api/secciones/{seccion_id de la sección N de A en
#   2026-2}/cargas a la interfaz de programación de aplicaciones
#   (application programming interface, API). Lleva X en el campo multipart «archivo» y la cookie
#   abet_sesion del profesor.
# - Una sección se nombra siempre con su número y su asignatura, porque la 412 existe en 450002 y en 450010.
# - «no gana ninguna fila» compara el conteo de la tabla antes y después de la petición.
# - Cada escenario corre en una base desechable propia, así que los carga_id y los seccion_id salen de
#   la API o de la base y nunca se suponen.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.
# Los pasos de pantalla, que nombran P2, los comprueban las pruebas de Vitest del Front (T045), y los
# demás corren con pytest contra un PostgreSQL 16 desechable (propuesta, con los pasos de T050 en
# US-07, US-09 y US-13 y con T051 en US-06).

Característica: Profesor con varias secciones de varias asignaturas
  El pedido de Jefferson en el chat, el 2026-10-28, dice «se espera lo siguiente / un profesor está
  dictando muchos cursos de muchas secciones / él solo puede cargar el export de su sección que le
  corresponde en el lugar donde le corresponde». Un profesor que dicta tres secciones de dos asignaturas
  ve solo esas secciones, y cada export entra solo en la sección que declara su hoja, aunque otra
  sección del mismo profesor comparta el plan de medición o el número.

  Antecedentes:
    Dado una base PostgreSQL 16 desechable con las migraciones V1_01 a V1_09, los datos de db/datos/periodo_2026_2_inventado.sql y, después, los de db/datos/varias_secciones_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y abet.seccion registra en "2026-2" la sección 412 de "450002" y las secciones 410 y 412 de "450010" con curso_blackboard "SINTETICO_20262_450002_412", "SINTETICO_20262_450010_410" y "SINTETICO_20262_450010_412"
    Y plan_medicion registra los PI 5.1, 5.2 y 5.3 para la asignatura "450002" en "2026-2" y los PI 2.1, 2.2 y 5.1 para "450010", con el instrumento "Trabajo Integrador" que asignatura_so le asigna en los SO 2 y 5
    Y "docente.varias@example.invalid" figura activo con rol "PROFESOR" y acceso.docente_seccion le asigna la sección 412 de "450002" y las secciones 410 y 412 de "450010" en "2026-2", y ninguna otra
    Y acceso.docente_seccion asigna la sección 410 de "450002" solo a "docente410@example.invalid" y la 411 solo a "docente411@example.invalid", y no tiene filas de "coordinacion@example.invalid"
    Y "docente.varias@example.invalid" tiene la sesión iniciada
    Y ninguna de las cinco secciones de 2026-2 tiene cargas

  # (propuesta) El valor "SIN_CARGA" del estado, como en acceso.feature.
  @US-06 @corte1
  Escenario: El profesor de varias secciones ve sus tres secciones y ninguna otra
    Cuando se envía GET /api/secciones?periodo=2026-2
    Entonces la API responde 200 con 3 secciones
    Y una es la 412 de 450002 "Principios de Ingeniería Sostenible" en 2026-2, con los PI 5.1, 5.2 y 5.3
    Y las otras dos son la 410 y la 412 de 450010 "Gestión Sostenible de Residuos" en 2026-2, cada una con los PI 2.1, 2.2 y 5.1
    Y las 3 traen tiene_plan verdadero y el estado de carga "SIN_CARGA"
    Y las dos secciones 412 traen seccion_id distintos
    Pero la respuesta no trae ningún dato de las secciones 410 y 411 de 450002, ni sus seccion_id
    Y la pantalla P2 «Mis secciones» muestra 3 filas, una por sección, con su asignatura, su número, sus PI, el estado "Sin carga" y el botón "Subir export" activo
    Y en P2 el botón "Subir export" de cada fila abre la pantalla P3 con la asignatura y el número de esa fila, y P3 sube el archivo a POST /api/secciones/{seccion_id de esa fila}/cargas, también en las dos filas 412

  # Cada export declara en su hoja la asignatura y la sección de su curso de Blackboard, y solo se publica
  # en la sección elegida que coincide con esa hoja (BR-CARGA-11). Las otras dos secciones del profesor
  # no reciben nada.
  @US-07 @corte1
  Esquema del escenario: Cada export del profesor de varias secciones se publica solo en su sección
    Cuando el profesor sube "<export>" a la sección <sección> de "<asignatura>"
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y abet.archivo_origen tiene 1 fila con nombre_archivo "<export>", hoja "<hoja>", filas_de_datos 11 y tipo_fuente "BLACKBOARD_EXPORT"
    Y la sección <sección> de "<asignatura>" tiene 1 sola carga, en estado "PUBLICADA" y con el archivo_id de esa fila
    Y carga.subida_por apunta a la fila de acceso.usuario_autorizado de "docente.varias@example.invalid"
    Y abet.carga_columna de esa carga tiene los PI <pi>
    Y abet.medicion tiene 33 filas de esa carga
    Y abet.estudiante tiene los códigos <desde> a <hasta> y ningún otro
    Y las consultas de control Q01, Q02, Q03, Q06, Q12 y Q13 devuelven 0 filas
    Pero las otras dos secciones del profesor y las secciones 410 y 411 de "450002" no tienen ninguna carga
    Y GET /api/secciones?periodo=2026-2 trae la sección <sección> de "<asignatura>" con el estado de carga "PUBLICADA" y filas_aceptadas 11, y las otras dos secciones del profesor con "SIN_CARGA"

    Ejemplos:
      | export                          | asignatura | sección | hoja                            | pi             | desde    | hasta    |
      | sintetico_20262_450002_412.xlsx | 450002     | 412     | gc_SINTETICO_20262_450002_412_f | 5.1, 5.2 y 5.3 | 99000023 | 99000033 |
      | sintetico_20262_450010_410.xlsx | 450010     | 410     | gc_SINTETICO_20262_450010_410_f | 2.1, 2.2 y 5.1 | 99000034 | 99000044 |
      | sintetico_20262_450010_412.xlsx | 450010     | 412     | gc_SINTETICO_20262_450010_412_f | 2.1, 2.2 y 5.1 | 99000045 | 99000055 |

  # Las dos secciones de 450010 comparten el plan de medición, así que solo el cotejo de la hoja con la
  # sección elegida impide publicar el export en la sección equivocada (BR-CARGA-11). La carga queda
  # RECHAZADA en la sección elegida y no pasa a la sección que declara la hoja. (propuesta) El texto del
  # mensaje con estas dos secciones, que sigue la forma de BR-CARGA-11.
  @US-13 @corte1
  Escenario: El export de una sección del profesor no entra en otra de sus secciones de la misma asignatura
    Cuando el profesor sube "sintetico_20262_450010_410.xlsx" a la sección 412 de "450010"
    Entonces la respuesta es 201 y su cuerpo trae estado "RECHAZADA" y el mensaje "El archivo corresponde a la sección 410 y usted eligió la 412. No se publicó."
    Y abet.archivo_origen tiene 1 fila con hoja "gc_SINTETICO_20262_450010_410_f"
    Y la carga queda en la sección 412 de "450010", en estado "RECHAZADA" y con filas_leidas 0, filas_aceptadas 0 y filas_rechazadas 0
    Y abet.rechazo_fila tiene exactamente 1 fila de esa carga, con motivo "SECCION_NO_COINCIDE", efecto "RECHAZA_CARGA" y fila_origen nulo
    Y abet.carga_columna, abet.carga_fila y abet.medicion no tienen filas de esa carga
    Y la sección 412 de "450010" no tiene ninguna carga "PUBLICADA"
    Y la sección 410 de "450010" no tiene ninguna carga
    Y abet.estudiante no tiene ninguno de los códigos 99000034 a 99000044

  # La 412 de 450002 y la 412 de 450010 comparten el número y son secciones distintas, así que el cotejo
  # compara la asignatura además del número, y SECCION_NO_COINCIDE cubre también la asignatura distinta.
  # El export trae 2.1, 2.2 y 5.1, mientras el plan de 450002 pide 5.1, 5.2 y 5.3. Como la sección
  # declarada se coteja antes que la estructura (BR-CARGA-03, paso 9), el motivo es SECCION_NO_COINCIDE y
  # no PI_DEL_PLAN_AUSENTE.
  # (propuesta) El texto del mensaje de otra asignatura, el de BR-CARGA-11.
  @US-13 @corte1
  Escenario: El mismo número de sección en otra asignatura no basta para cargar el export
    Cuando el profesor sube "sintetico_20262_450010_412.xlsx" a la sección 412 de "450002"
    Entonces la respuesta es 201 y su cuerpo trae estado "RECHAZADA" y el mensaje "El archivo corresponde a la asignatura 450010 y usted eligió la 450002. No se publicó."
    Y abet.archivo_origen tiene 1 fila con hoja "gc_SINTETICO_20262_450010_412_f"
    Y la carga queda en la sección 412 de "450002", en estado "RECHAZADA" y con filas_leidas 0, filas_aceptadas 0 y filas_rechazadas 0
    Y abet.rechazo_fila tiene exactamente 1 fila de esa carga, con motivo "SECCION_NO_COINCIDE", efecto "RECHAZA_CARGA" y fila_origen nulo
    Y abet.carga_columna, abet.carga_fila y abet.medicion no tienen filas de esa carga
    Y la sección 412 de "450002" no tiene ninguna carga "PUBLICADA"
    Y la sección 412 de "450010" no tiene ninguna carga
    Y abet.estudiante no tiene ninguno de los códigos 99000045 a 99000055

  # El alcance se comprueba antes que la huella y que el cotejo de la hoja (BR-CARGA-03, paso 1). La fila
  # del export propio de la 412 de 450002 prueba que el 403 llega antes que el cotejo de la hoja y no deja
  # una carga RECHAZADA. La fila del export que la 410 de 450002 ya tiene publicado prueba que llega antes
  # que la búsqueda de la huella (paso 6), porque una ruta que busca primero la huella responde 200 con la
  # constancia de la carga de docente410@example.invalid (BR-CARGA-09).
  @US-06 @corte1
  Esquema del escenario: El profesor de varias secciones no alcanza una sección que no dicta
    Dado que la sección 410 de "450002" tiene una carga PUBLICADA de "sintetico_20262_450002_410.xlsx", subida por "docente410@example.invalid", con los códigos 99000001 a 99000011
    Cuando el profesor envía <método> <ruta> <cuerpo>
    Entonces la API responde 403 con el cuerpo {"detail": "La sección no está a su cargo."}
    Y la respuesta no trae ningún dato de la sección 410 de "450002" ni de su carga
    Y abet.archivo_origen, abet.carga y abet.estudiante no ganan ninguna fila

    Ejemplos:
      | método | ruta                                             | cuerpo                                                                |
      | POST   | /api/secciones/{sección 410 de 450002}/cargas    | con "sintetico_20262_450002_412.xlsx" en el campo multipart «archivo» |
      | POST   | /api/secciones/{sección 410 de 450002}/cargas    | con "sintetico_20262_450002_410.xlsx" en el campo multipart «archivo» |
      | GET    | /api/cargas/{carga de la 410 de 450002}          | sin cuerpo                                                            |
      | GET    | /api/cargas/{carga de la 410 de 450002}/r17.xlsx | sin cuerpo                                                            |

  # La huella se busca antes que el cotejo de la hoja (BR-CARGA-03, pasos 6 y 9), así que el 409 llega
  # antes que un SECCION_NO_COINCIDE y no queda ninguna carga RECHAZADA. El 409 no dice en qué sección
  # está publicado el archivo, aunque las dos secciones sean del mismo profesor (BR-CARGA-09).
  @US-09 @corte1
  Escenario: Un archivo publicado en una sección del profesor se detiene en otra de sus secciones
    Dado que "sintetico_20262_450002_412.xlsx" está subido a la sección 412 de "450002" con respuesta 201 y su carga_id
    Cuando el profesor sube otra vez "sintetico_20262_450002_412.xlsx", ahora a la sección 410 de "450010"
    Entonces la respuesta es 409 con detail "Este archivo ya está publicado en otra sección. No se cargó."
    Pero el cuerpo de la respuesta no contiene ese carga_id, la huella del archivo, el número 412 ni la asignatura 450002
    Y abet.archivo_origen, abet.carga, abet.rechazo_fila y abet.estudiante no ganan ninguna fila
    Y la sección 410 de "450010" no tiene ninguna carga
    Y la sección 412 de "450002" sigue con 1 carga "PUBLICADA", la de "sintetico_20262_450002_412.xlsx", y sus 33 mediciones
