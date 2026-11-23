# language: es
#
# Escenarios de aceptación de US-70, US-71 y US-72 de la spec 008-ciclo-quimica-industrial (épica EP-08,
# propuesta). La coordinación de una carrera ve solo las secciones de su carrera (US-70, C-44 con C-26), la
# coordinación de Química General ve todas las secciones de 5643 y ninguna otra (US-71, C-20 con la parte de
# alcance de C-45) y Jefferson registra esa cuenta con una corrida en seco antes de escribir (US-72, C-21 con
# el guion de C-45).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid. El correo real
# del coordinador de Química General nunca se escribe en el repositorio, y en estos escenarios lo reemplaza
# coordinador.quimica@example.invalid.
#
# Vocabulario de los pasos.
# - El modelo sigue el veredicto CAMBIAR del crítico. El rol COORDINADOR se conserva, ck_usuario_autorizado_rol
#   no cambia y el alcance vive en la tabla nueva acceso.coordinacion_alcance (V1_14), con una fila por carrera
#   o por asignatura (ck_coordinacion_alcance_uno, num_nonnulls de carrera_id y asignatura_id igual a 1), el
#   periodo obligatorio en la fila de asignatura (ck_coordinacion_alcance_periodo, valor provisional de J-49) y
#   uq_coordinacion_alcance con NULLS NOT DISTINCT. abet_app solo la lee.
# - La base de los escenarios del Back es una base desechable de la spec 008 con db/datos/periodo_2026_2_inventado.sql
#   (las secciones 410 y 411 de 450002 en 2026-2) y db/datos/quimica_2026_1_inventado.sql (las secciones 701 a 704
#   de 5643 en 2026-1, con docente701@example.invalid a docente703@example.invalid y la 704 sin profesor).
# - La respuesta de GET /api/sesion suma el campo aditivo alcance (propuesta), con tipo SECCIONES, CARRERA o
#   CURSO, para que el Front rotule la pantalla sin un rol nuevo.
# - Los escenarios de pantalla los prueba Vitest en el Front y llevan @delegado_a_vitest.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Alcance de la coordinación por carrera y por curso
  Como coordinación de una carrera o de un curso, quiero ver todas las secciones que me tocan y ninguna otra,
  para seguir el registro sin leer lo que mide otra carrera u otro curso.

  Antecedentes:
    Dado una base desechable de la spec 008 con los datos de periodo_2026_2_inventado.sql y quimica_2026_1_inventado.sql
    Y "coordinacion@example.invalid" con rol "COORDINADOR", activo y con alcance de la carrera "AMB"
    Y "coordinador.quimica@example.invalid" con rol "COORDINADOR", activo y con alcance de la asignatura "5643" en "2026-1"

  @spec008 @corte1 @US-70
  Escenario: La coordinación de Ambiental no ve las secciones de Química General
    Dado "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/secciones?periodo=2026-1
    Entonces recibe 200 con una lista vacía, porque AMB-2026 no tiene vigencia en 2026-1

  @spec008 @corte1 @US-70
  Escenario: La coordinación de Ambiental conserva lo que ya veía
    Dado "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/secciones?periodo=2026-2
    Entonces recibe 200 con la 410 y la 411 de "450002", como antes del cambio

  @spec008 @corte1 @US-70
  Esquema del escenario: Una sección o una carga de Química pedida por la coordinación de Ambiental responde el 403 de siempre
    Dado "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Y la carga PUBLICADA inventada de la 701
    Cuando pide <ruta> con el identificador de la 701
    Entonces recibe 403 con «La sección no está a su cargo.»
    Y la respuesta no trae datos de la 701

    Ejemplos:
      | ruta                                 |
      | GET /api/cargas?seccion_id={seccion} |
      | GET /api/cargas/{carga}              |
      | GET /api/cargas/{carga}/r17.xlsx     |

  @spec008 @corte1 @US-70
  Escenario: Un coordinador sin alcance no ve ninguna sección y Q20 lo lista
    Dado "coordinacion2@example.invalid" con rol "COORDINADOR", activo y sin fila en acceso.coordinacion_alcance
    Y "coordinacion2@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/secciones?periodo=2026-2
    Entonces recibe 200 con una lista vacía
    Y la consulta de control Q20 devuelve 1 fila con su usuario_id y su rol, sin el correo
    Y GET /api/sesion trae el alcance de tipo "CARRERA" con las carreras [] y las asignaturas []

  @spec008 @corte1 @US-70
  Escenario: Con las dos carreras vigentes en el mismo periodo, el curso compartido sigue el valor provisional de J-50
    Dado AMB-2026 también vigente en 2026-1, con 5643 en su plan de estudios y sin plan de medición de Ambiental para 5643
    Y "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/secciones?periodo=2026-1
    Entonces recibe las secciones 701 a 704 de "5643", porque la regla provisional es el plan de estudios del catálogo vigente de su carrera

  @spec008 @corte1 @US-70
  Escenario: El guion de alcance de Ambiental corre antes del código nuevo y no deja a la coordinación sin alcance
    Dado una base desechable con periodo_2026_2_inventado.sql, V1_14 aplicada y "coordinacion@example.invalid" sin fila en acceso.coordinacion_alcance
    Cuando psql corre db/datos/alcance_coordinacion_ambiental.sql con -v aplicar=1
    Entonces "coordinacion@example.invalid" queda con el alcance de la carrera "AMB"
    Y con el _ALCANCE nuevo sigue viendo la 410 y la 411 de 2026-2
    Y una segunda corrida no suma filas

  @spec008 @corte1 @US-70
  Esquema del escenario: La base exige un solo alcance por fila
    Cuando el dueño de la base inserta en acceso.coordinacion_alcance una fila con <valores>
    Entonces PostgreSQL la rechaza con <restriccion>

    Ejemplos:
      | valores                                                   | restriccion                     |
      | la carrera "AMB" y la asignatura 5643 a la vez            | ck_coordinacion_alcance_uno     |
      | ni carrera ni asignatura                                  | ck_coordinacion_alcance_uno     |
      | la asignatura 5643 sin periodo                            | ck_coordinacion_alcance_periodo |
      | la carrera "AMB" repetida para el mismo usuario           | uq_coordinacion_alcance         |

  @spec008 @corte1 @US-70
  Escenario: El rol de la aplicación solo lee el alcance
    Cuando abet_app inserta una fila en acceso.coordinacion_alcance
    Entonces PostgreSQL responde el SQLSTATE 42501
    Y db/pruebas/probar_rol_app.sql lista SELECT como único privilegio de abet_app en esa tabla

  @spec008 @corte1 @US-71
  Escenario: La coordinación del curso ve las secciones de 5643 en orden y ninguna otra
    Dado "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/secciones?periodo=2026-1
    Entonces recibe 200 con la 701, la 702, la 703 y la 704 de "5643" en ese orden
    Y la respuesta no trae la 410 ni la 411 de "450002"

  @spec008 @corte1 @US-71
  Escenario: La sesión dice el alcance del curso sin un rol nuevo
    Dado "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/sesion
    Entonces recibe 200 con el rol "COORDINADOR" y el alcance de tipo "CURSO" con las asignaturas ["5643"] (propuesta)
    Y la sesión de "docente701@example.invalid" trae el alcance de tipo "SECCIONES"
    Y la sesión de "coordinacion@example.invalid" trae el alcance de tipo "CARRERA" con las carreras ["AMB"]

  @spec008 @corte1 @US-71
  Escenario: Una cuenta con alcance de carrera y de curso recibe el tipo más amplio
    Dado "coordinacion@example.invalid" también con alcance de la asignatura "5643" en "2026-1"
    Y "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/sesion y GET /api/secciones?periodo=2026-1
    Entonces el alcance es de tipo "CARRERA" con las carreras ["AMB"] y las asignaturas ["5643"]
    Y recibe la 701, la 702, la 703 y la 704 de "5643", la unión de las dos filas

  @spec008 @corte1 @US-71
  Escenario: La asignación vale solo en su periodo
    Dado la sección 701 de "5643" también en 2026-2, sin fila de alcance de 5643 en 2026-2
    Y "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/secciones?periodo=2026-2
    Entonces recibe 200 con una lista vacía

  @spec008 @corte1 @US-71
  Escenario: Lee la constancia y el R-17 de una sección de su curso
    Dado la carga PUBLICADA inventada de la 702, subida por "docente702@example.invalid"
    Y "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/cargas/{carga} y GET /api/cargas/{carga}/r17.xlsx de esa carga
    Entonces las dos rutas responden 200

  @spec008 @corte1 @US-71
  Esquema del escenario: La coordinación del curso no alcanza otro curso
    Dado la carga PUBLICADA inventada de la 410 de "450002"
    Y "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide <ruta> con el identificador de la 410
    Entonces recibe 403 con «La sección no está a su cargo.»

    Ejemplos:
      | ruta                                 |
      | GET /api/cargas?seccion_id={seccion} |
      | GET /api/cargas/{carga}              |
      | GET /api/cargas/{carga}/r17.xlsx     |

  @spec008 @corte1 @US-71
  Escenario: La coordinación del curso no sube una carga nueva
    Dado "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando sube un export inventado válido a POST /api/secciones/{701}/cargas sin reemplaza
    Entonces recibe 403 con «La sección no está a su cargo.»
    Y abet.carga y abet.archivo_origen no ganan ninguna fila

  @spec008 @corte1 @US-71
  Escenario: La coordinación del curso reemplaza en su curso con el valor provisional de D-52
    Dado la carga PUBLICADA inventada de la 703
    Y "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando sube un export corregido de la 703 con reemplaza igual a esa carga
    Entonces recibe 201 con la carga nueva PUBLICADA y la anterior REEMPLAZADA
    Y subida_por de la carga nueva es el usuario de "coordinador.quimica@example.invalid"
    Y las consultas de control Q06, Q07, Q10 y Q14 devuelven 0 filas

  @spec008 @corte1 @US-71
  Escenario: Una cuenta de coordinación dada de baja no alcanza nada
    Dado "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Y su cuenta pasa a activo falso
    Cuando pide GET /api/secciones?periodo=2026-1 con su cookie anterior
    Entonces recibe 401 y ninguna sección

  @spec008 @corte1 @US-71
  Escenario: El profesor del curso sigue viendo solo su sección
    Dado "docente701@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando pide GET /api/secciones?periodo=2026-1
    Entonces recibe 200 solo con la 701

  @spec008 @corte1 @US-71
  Escenario: Q20 lista una coordinación de curso con una sección propia en acceso.docente_seccion
    Dado "coordinador.quimica@example.invalid" asignado también a la 704 en acceso.docente_seccion
    Cuando corre la consulta de control Q20
    Entonces devuelve 1 fila con su usuario_id y su rol, sin el correo

  @spec008 @corte1 @US-71 @delegado_a_vitest
  Escenario: P2 rotula el curso y no ofrece subir
    Dado una sesión de "coordinador.quimica@example.invalid" con rol "COORDINADOR" y alcance "CURSO"
    Cuando llega a P2
    Entonces el título y el botón del menú dicen «Secciones del curso» (propuesta)
    Y ninguna fila muestra el botón «Subir export»
    Y el enlace a P6 dice «Ver los logros por SO del curso» (propuesta)
    Y la lista vacía dice «El curso no tiene secciones en este periodo.» (propuesta)

  @spec008 @corte1 @US-71 @delegado_a_vitest
  Escenario: La coordinación de la carrera conserva sus rótulos
    Dado una sesión de "coordinacion@example.invalid" con rol "COORDINADOR" y alcance "CARRERA"
    Cuando llega a P2
    Entonces el título dice «Secciones de la carrera», como fija la spec 007

  @spec008 @corte1 @US-71 @delegado_a_vitest
  Escenario: El consejo de una sección cruzada remite al profesor también para la coordinación del curso
    Dado una sesión de "coordinador.quimica@example.invalid" con rol "COORDINADOR" y alcance "CURSO"
    Y que la ruta 6 responde la carga 8 de la sección 701 de "5643" en "2026-1" RECHAZADA por SECCION_NO_COINCIDE
    Cuando abre P4 de la carga 8
    Entonces ve «Qué corregir. El archivo no es de 5643, sección 701. Pida al profesor de esa sección que exporte su Centro de calificaciones y lo suba otra vez.»

  @spec008 @corte1 @US-72
  Escenario: La corrida en seco del registro de la coordinación informa sin repetir el correo
    Dado la variable CORREO_COORDINACION con "otra.coordinacion@example.invalid"
    Cuando db/herramientas/registrar_coordinacion.py corre con --asignatura 5643 --periodo 2026-1 sin --aplicar
    Entonces el informe dice que registraría 1 cuenta de coordinación nueva con el alcance de 5643 en 2026-1
    Y el informe no repite el correo
    Y acceso.usuario_autorizado y acceso.coordinacion_alcance no ganan ninguna fila
    Y el guion termina con código 0

  @spec008 @corte1 @US-72
  Escenario: Con --aplicar escribe una vez y se puede repetir
    Dado la variable CORREO_COORDINACION con " Otra.Coordinacion@EXAMPLE.invalid "
    Cuando el guion corre con --asignatura 5643 --periodo 2026-1 y --aplicar dos veces
    Entonces acceso.usuario_autorizado tiene 1 fila "otra.coordinacion@example.invalid" con rol "COORDINADOR", activa y sin fila en acceso.credencial
    Y acceso.coordinacion_alcance tiene 1 fila de 5643 en 2026-1 para esa cuenta
    Y la segunda corrida informa 0 filas nuevas

  @spec008 @corte1 @US-72
  Escenario: Un correo que ya es profesor detiene el guion sin cambiar su rol
    Dado la variable CORREO_COORDINACION con "docente701@example.invalid"
    Cuando el guion corre con --asignatura 5643 --periodo 2026-1 y --aplicar
    Entonces termina con código 1 y el informe dice que la cuenta ya existe con otro rol
    Y el rol de "docente701@example.invalid" sigue siendo "PROFESOR"
    Y acceso.coordinacion_alcance no gana ninguna fila

  @spec008 @corte1 @US-72
  Escenario: Una cuenta dada de baja no se reactiva
    Dado "otra.coordinacion@example.invalid" con rol "COORDINADOR" y activo falso
    Y la variable CORREO_COORDINACION con "otra.coordinacion@example.invalid"
    Cuando el guion corre con --asignatura 5643 --periodo 2026-1 y --aplicar
    Entonces termina con código 1, activo sigue falso y el informe dice que la cuenta está dada de baja

  @spec008 @corte1 @US-72
  Esquema del escenario: Un argumento inválido se rechaza antes de escribir
    Dado la variable CORREO_COORDINACION con "otra.coordinacion@example.invalid"
    Cuando el guion corre con <argumentos> y --aplicar
    Entonces termina con código 1 y el informe nombra <motivo>
    Y ninguna tabla de acceso gana filas

    Ejemplos:
      | argumentos                            | motivo                                           |
      | --asignatura 9999 --periodo 2026-1    | la asignatura 9999                               |
      | --asignatura 5643 --periodo 2026-3    | el periodo 2026-3                                |
      | --asignatura 5643 --periodo 2025-2    | el periodo 2025-2, que no existe en abet.periodo |

  @spec008 @corte1 @US-72
  Escenario: Sin la variable del correo el guion no adivina
    Dado la variable CORREO_COORDINACION sin definir
    Cuando el guion corre con --asignatura 5643 --periodo 2026-1
    Entonces termina con código 2 y dice «Falta la variable CORREO_COORDINACION.» (propuesta)

  @spec008 @corte1 @US-72
  Escenario: Una asignatura sin plan de medición entra con aviso
    Dado la variable CORREO_COORDINACION con "coordinacion.ambiental@example.invalid"
    Cuando el guion corre con --asignatura 450010 --periodo 2026-1 sin --aplicar
    Entonces el informe avisa que la asignatura 450010 no tiene plan de medición en 2026-1

  @spec008 @corte1 @US-72
  Escenario: El guion no escribe contraseñas ni las muestra
    Dado la variable CORREO_COORDINACION con "otra.coordinacion@example.invalid"
    Cuando el guion corre con --asignatura 5643 --periodo 2026-1 y --aplicar
    Entonces acceso.credencial no gana ninguna fila
    Y la salida no contiene la palabra «contraseña» seguida de un valor
