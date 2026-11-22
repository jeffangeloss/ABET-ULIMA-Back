# language: es
#
# Escenarios de aceptación de US-64, US-65 y US-66 de la spec 007-experiencia-por-cuenta (épica EP-07,
# propuesta, etapa B). La ruta 17 GET /api/avance da a la coordinación la etapa de cada sección del periodo
# (US-64), la pantalla nueva P7 «Avance del registro» la muestra con un resumen y un filtro y es la página de
# entrada del coordinador (US-65), y P7 muestra y copia los correos de los profesores de las secciones que
# faltan (US-66, que espera D-47). Salen de las candidatas C-C01, C-C02 y la parte (a) de C-C03, con C-T01
# absorbida por C-C01 (revision-historias.md).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid. Ninguna
# contraseña aparece escrita aquí, porque la prueba inicia las sesiones con una contraseña generada al azar.
#
# Vocabulario de los pasos.
# - La base de los Antecedentes es una base PostgreSQL 18 desechable que siembra un ayudante nuevo de
#   tests/cargas_de_prueba.py (propuesta). Su paso no empieza con «una base PostgreSQL 18 desechable con las
#   migraciones V1_01 a V1_», para que la expresión de tests/aceptacion/pasos/conftest.py que crea la base
#   «periodo» no lo capture, como en la spec 006.
# - 450020 «Evaluación del Impacto Ambiental» es una asignatura del plan de estudios vigente de AMB-2026
#   (V1_03) sin filas en abet.plan_medicion en 2026-2, con las secciones de prueba 414 y 417.
# - La etapa la decide el Back en cada lectura, sin guardarla (J-48, valor provisional). Una sección es
#   SIN_PLAN si abet.plan_medicion no tiene filas de su asignatura en el periodo. Si no, es PUBLICADA con una
#   carga PUBLICADA, aunque ya no tenga un profesor activo. Si no, es SIN_PROFESOR si ningún usuario activo con
#   rol PROFESOR la tiene en acceso.docente_seccion, la condición de secciones_sin_docente.sql de la spec 006.
#   Si no, es CON_RECHAZO con al menos una carga RECHAZADA, y SIN_CARGA en otro caso, también con una carga
#   EN_CURSO.
# - Los escenarios de la ruta 17 los prueba pytest-bdd en el Back. Los de P7 se prueban con Vitest en el Front
#   y llevan @delegado_a_vitest.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Avance del registro de la carrera para la coordinación
  Como coordinación de la carrera, quiero ver en una sola página la etapa de cada sección del periodo, cuántas
  faltan y a quién recordar el registro, para seguir a los profesores en las semanas 15 y 16 sin abrir sección
  por sección.

  Antecedentes:
    Dado una base desechable del avance de la spec 007 con la vigencia de AMB-2026 en 2026-2 y el plan de medición de 450002 y 450010
    Y "coordinacion@example.invalid" con rol "COORDINADOR", activo
    Y la 410 de "450002" asignada a "docente410@example.invalid" con una carga PUBLICADA
    Y la 411 de "450002" asignada a "docente411@example.invalid" con una sola carga RECHAZADA
    Y la 412 de "450010" asignada a "docente410@example.invalid" y sin cargas
    Y la 413 de "450010" sin ningún usuario activo con rol PROFESOR en acceso.docente_seccion
    Y la 414 de "450020" asignada a "docente411@example.invalid" y sin cargas

  @US-64 @spec007 @corte1 @etapa_b
  Escenario: La ruta 17 da la etapa de cada sección en el orden de asignatura y número
    Cuando "coordinacion@example.invalid" pide GET /api/avance?periodo=2026-2
    Entonces recibe 200 con Cache-Control no-store y estas secciones, en este orden
      | asignatura | seccion | etapa        | carga_id         |
      | 450002     | 410     | PUBLICADA    | la de la 410     |
      | 450002     | 411     | CON_RECHAZO  | null             |
      | 450010     | 412     | SIN_CARGA    | null             |
      | 450010     | 413     | SIN_PROFESOR | null             |
      | 450020     | 414     | SIN_PLAN     | null             |
    Y el conteo trae 5 secciones, 1 PUBLICADA, 1 CON_RECHAZO, 1 SIN_CARGA, 1 SIN_PROFESOR y 1 SIN_PLAN
    Y ninguna sección trae un porcentaje de logro, un nivel ni un dato de estudiantes

  @US-64 @spec007 @corte1 @etapa_b
  Esquema del escenario: La precedencia de J-48 decide la etapa de cada sección
    Dado la <seccion> de "<asignatura>" <estado>
    Cuando "coordinacion@example.invalid" pide GET /api/avance?periodo=2026-2
    Entonces la <seccion> de "<asignatura>" trae la etapa <etapa>

    Ejemplos:
      | seccion | asignatura | estado                                                           | etapa        |
      | 417     | 450020     | sin plan de medición y sin profesor                              | SIN_PLAN     |
      | 415     | 450010     | con un profesor dado de baja y sin otro activo                   | SIN_PROFESOR |
      | 415     | 450010     | asignada solo a "coordinacion@example.invalid"                   | SIN_PROFESOR |
      | 415     | 450010     | con una carga PUBLICADA y su único profesor dado de baja después | PUBLICADA    |
      | 415     | 450010     | con un profesor activo y una carga EN_CURSO                      | SIN_CARGA    |
      | 415     | 450010     | con una carga RECHAZADA y después una PUBLICADA                  | PUBLICADA    |
      | 415     | 450010     | con una carga REEMPLAZADA y la que la reemplaza PUBLICADA        | PUBLICADA    |

  @US-64 @spec007 @corte1 @etapa_b
  Escenario: Solo la coordinación lee el avance, en el orden 401, 403 y 422
    Cuando "docente410@example.invalid" pide GET /api/avance?periodo=2026-2
    Entonces recibe 403 con detail "Esta página es de la Coordinación."
    Y "docente410@example.invalid" recibe el mismo 403 con el periodo "2026"
    Y la misma ruta sin sesión responde 401
    Y "coordinacion@example.invalid" con el periodo "2026" recibe 422 con detail "El periodo no tiene la forma AAAA-C."

  @US-64 @spec007 @corte1 @etapa_b
  Escenario: Sin periodo, la ruta 17 usa el periodo vigente
    Dado la API configurada con PERIODO_VIGENTE "2026-2"
    Cuando "coordinacion@example.invalid" pide GET /api/avance sin periodo
    Entonces recibe 200 con periodo "2026-2" y las mismas 5 secciones

  @US-65 @spec007 @corte1 @etapa_b @delegado_a_vitest
  Escenario: P7 muestra el avance con texto, agrupado por asignatura
    Dado la respuesta de la ruta 17 del primer escenario
    Cuando "coordinacion@example.invalid" abre P7 «Avance del registro» (propuesta)
    Entonces ve con role="status" «1 de 5 secciones con carga publicada.» (propuesta)
    Y ve «1 sección sin plan de medición, en la que su profesor no puede subir el export.» (propuesta)
    Y ve bajo su asignatura las filas «410 · Publicada», «411 · La última carga se rechazó», «412 · Sin carga», «413 · Sin profesor asignado» y «414 · Sin plan de medición» (propuestas)
    Y cada etapa lleva su texto, además de cualquier color
    Y la fila de la 410 ofrece «Ver la carga» (propuesta), que abre P4 de su carga publicada

  @US-65 @spec007 @corte1 @etapa_b @delegado_a_vitest
  Escenario: El filtro deja solo las secciones que faltan
    Dado P7 con la respuesta de la ruta 17 del primer escenario
    Cuando la coordinación marca «Mostrar solo las secciones que faltan» (propuesta)
    Entonces ve la 411, la 412, la 413 y la 414 en el mismo orden, y no la 410
    Y el resumen sigue diciendo «1 de 5 secciones con carga publicada.»
    Y localStorage y sessionStorage siguen con 0 entradas

  @US-65 @spec007 @corte1 @etapa_b @delegado_a_vitest
  Esquema del escenario: Cada cuenta entra a su página
    Dado una sesión de "<correo>" con rol "<rol>"
    Cuando ingresa desde P1
    Entonces ve la página «<pagina>»
    Y la cabecera <avance>

    Ejemplos:
      | correo                       | rol         | pagina              | avance                                                |
      | docente410@example.invalid   | PROFESOR    | Mis secciones       | no ofrece «Avance del registro»                       |
      | coordinacion@example.invalid | COORDINADOR | Avance del registro | ofrece «Avance del registro» antes de «Secciones de la carrera» |

  @US-65 @spec007 @corte1 @etapa_b @delegado_a_vitest
  Escenario: Atrás desde P4 abierta con «Ver la carga» vuelve a P7
    Dado P7 con la respuesta de la ruta 17 del primer escenario
    Y la navegación por fragmento de US-52 de la spec 005
    Cuando la coordinación pulsa «Ver la carga» en la fila de la 410 y después el botón atrás del navegador
    Entonces la dirección termina en «#/avance» (propuesta)
    Y P7 vuelve a pedir la ruta 17 y muestra «1 de 5 secciones con carga publicada.»
    Y al recargar la página en «#/avance» la coordinación sigue en P7

  @US-65 @spec007 @corte1 @etapa_b @delegado_a_vitest
  Escenario: P7 sin secciones lo dice con el texto de la carrera
    Dado una sesión de "coordinacion@example.invalid" con rol "COORDINADOR" y la ruta 17 con secciones vacías
    Cuando abre P7
    Entonces ve «La carrera no tiene secciones en este periodo.»
    Y no ve el resumen ni el filtro

  @US-66 @spec007 @corte1 @etapa_b
  Escenario: La ruta 17 trae solo los correos de los profesores activos de las secciones que faltan
    Dado la 416 de "450010" asignada a "docente411@example.invalid" y a "docente.baja@example.invalid", dado de baja, sin cargas
    Cuando "coordinacion@example.invalid" pide GET /api/avance?periodo=2026-2
    Entonces la 411 de "450002" trae profesores ["docente411@example.invalid"]
    Y la 412 de "450010" trae profesores ["docente410@example.invalid"]
    Y la 416 de "450010" trae profesores ["docente411@example.invalid"], sin el usuario dado de baja
    Y la 410 de "450002", la 413 de "450010" y la 414 de "450020" traen profesores []
    Y ninguna sección trae nombres, contraseñas ni datos de acceso.credencial

  @US-66 @spec007 @corte1 @etapa_b @delegado_a_vitest
  Escenario: P7 muestra los correos en las filas que faltan y los copia sin repetirlos
    Dado P7 con la respuesta del escenario anterior
    Cuando la coordinación pulsa «Copiar los correos de los profesores que faltan» (propuesta)
    Entonces las filas de la 411, la 412 y la 416 muestran el correo de su profesor
    Y la fila de la 410 no muestra ningún correo
    Y el portapapeles recibe «docente410@example.invalid; docente411@example.invalid»
    Y P7 dice «Se copiaron 2 correos.» (propuesta)

  @US-66 @spec007 @corte1 @etapa_b @delegado_a_vitest
  Escenario: Sin portapapeles, los correos quedan seleccionables y no se guardan
    Dado P7 en un navegador que rechaza el acceso al portapapeles
    Cuando la coordinación pulsa «Copiar los correos de los profesores que faltan»
    Entonces P7 muestra los mismos correos en un cuadro de texto de solo lectura y seleccionado
    Y localStorage y sessionStorage siguen con 0 entradas
