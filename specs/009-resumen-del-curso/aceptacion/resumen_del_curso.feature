# language: es
#
# Escenarios de aceptación de US-91 y US-93 de la spec 009-resumen-del-curso (épica EP-09, propuesta). La ruta 20
# da a la coordinación, para un curso y un periodo, las cifras del curso y de cada sección por PI, como la página
# «Resumen Curso» del tablero de Stefanny Montaño, con las cifras de la base y sin Power BI.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid.
#
# Vocabulario de los pasos.
# - La base tiene db/datos/quimica_2026_1_inventado.sql, con la 701 de docente701@example.invalid, la 702 de
#   docente702@example.invalid, la 703 de docente703@example.invalid, la 704 sin profesor y la coordinación del
#   curso coordinador.quimica@example.invalid, más db/datos/periodo_2026_2_inventado.sql y el plan de 5643 en
#   2026-1 con el PI 6.1.
# - «Los niveles [a, b, c, d]» son los alumnos calificados en los niveles 1, 2, 3 y 4 de la carga PUBLICADA de la
#   sección. Las cifras salen de abet.v_r17_por_pi, con calificados igual a n_total menos n_sin_evidencia y con
#   NIVEL_ESPERADO y META_LOGRO de R-2026-BORRADOR de Industrial.
# - Los porcentajes se redondean a un decimal y los promedios a dos en PostgreSQL con numeric, y en_meta sale de la
#   misma función que el plan de acción del R-17.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Cifras del curso para su coordinación
  Como coordinación de Química General, quiero recibir de una sola vez las cifras del curso y de cada sección,
  para saber si el curso cumple el PI sin abrir un R-17 por sección.

  Antecedentes:
    Dado una base desechable de la spec 009 con el plan de 5643 en 2026-1 y los datos inventados de Química

  @spec009 @corte1 @US-91
  Escenario: El curso suma alumnos de las secciones publicadas y no promedia porcentajes
    Dado la 701 publicada con los niveles [1, 2, 4, 3]
    Y la 702 publicada con los niveles [0, 1, 5, 4]
    Y la 703 publicada con los niveles [2, 4, 4, 3] y un alumno sin evidencia
    Cuando coordinador.quimica@example.invalid pide GET /api/resumen-curso?periodo=2026-1&asignatura=5643
    Entonces la respuesta es 200
    Y el PI 6.1 trae en curso logrados 23, calificados 33, sin_evidencia 1 y total 34
    Y el PI 6.1 trae en curso pct_sobre_calificados 69.7, promedio_nivel 2.91 y en_meta falso
    Y el PI 6.1 trae en curso estudiantes_por_nivel [3, 7, 13, 10]

  @spec009 @corte1 @US-91
  Escenario: Cada sección trae sus cifras en orden de número y la sección sin carga no inventa un porcentaje
    Dado la 701, la 702 y la 703 publicadas con los niveles del escenario anterior y la 704 sin carga
    Cuando coordinador.quimica@example.invalid pide el resumen de 5643 en 2026-1
    Entonces secciones trae la 701, la 702, la 703 y la 704 en ese orden
    Y la 701 trae pct_sobre_calificados 70.0, promedio_nivel 2.90 y en_meta falso
    Y la 702 trae pct_sobre_calificados 90.0, promedio_nivel 3.30 y en_meta verdadero
    Y la 703 trae pct_sobre_calificados 53.8, promedio_nivel 2.62 y en_meta falso
    Y la 704 trae estado "SIN_CARGA" con pct_sobre_calificados, promedio_nivel y en_meta en null

  @spec009 @corte1 @US-91
  Escenario: El conteo de secciones cuenta la meta solo sobre las publicadas
    Dado la 701, la 702 y la 703 publicadas con los niveles del primer escenario y la 704 sin carga
    Cuando coordinador.quimica@example.invalid pide el resumen de 5643 en 2026-1
    Entonces conteo_secciones trae total 4, publicadas 3, en_meta 1, debajo_de_la_meta 2 y sin_dato 1

  @spec009 @corte1 @US-91
  Escenario: Cada porcentaje de sección es el de su R-17
    Dado la 701 publicada con los niveles [1, 2, 4, 3]
    Cuando coordinador.quimica@example.invalid pide el resumen de 5643 en 2026-1
    Entonces pct_sobre_calificados de la 701 es igual a pct_logro_sobre_calificados de abet.v_r17_por_pi para su carga
    Y es igual al porcentaje del bloque II del R-17 de esa carga

  @spec009 @corte1 @US-91
  Escenario: El curso cumple con el 80,0 justo y no cumple con 75,0, igual que el R-17
    Dado la 701 publicada con los niveles [0, 1, 3, 1]
    Cuando coordinador.quimica@example.invalid pide el resumen de 5643 en 2026-1
    Entonces el PI 6.1 trae en curso pct_sobre_calificados 80.0 y en_meta verdadero
    Pero con la 701 publicada con los niveles [0, 1, 2, 1] el curso trae 75.0 y en_meta falso

  @spec009 @corte1 @US-91
  Escenario: Un curso sin cargas publicadas trae nulos y no ceros
    Dado ninguna carga publicada de 5643 en 2026-1
    Cuando coordinador.quimica@example.invalid pide el resumen de 5643 en 2026-1
    Entonces el PI 6.1 trae en curso calificados 0 y pct_sobre_calificados, promedio_nivel y en_meta en null
    Y conteo_secciones trae publicadas 0 y sin_dato 4

  @spec009 @corte1 @US-91
  Escenario: Con un conjunto de reglas provisional el curso sale provisional
    Dado la 701 publicada con R-2026-BORRADOR de Industrial, que tiene parámetros PENDIENTE
    Cuando coordinador.quimica@example.invalid pide el resumen de 5643 en 2026-1
    Entonces el PI 6.1 trae provisional verdadero

  @spec009 @corte1 @US-91
  Escenario: La respuesta del resumen trae solo las claves de su lista cerrada
    Dado la 701 publicada con los niveles [1, 2, 4, 3]
    Cuando coordinador.quimica@example.invalid pide el resumen de 5643 en 2026-1
    Entonces la respuesta trae solo las claves de la lista cerrada de la ruta 20 del contrato
    Y no trae correos, nombres, códigos de estudiantes, subida_por, nombre_archivo ni sha256

  @spec009 @corte1 @US-91
  Escenario: El profesor recibe 403 en el resumen del curso
    Dado docente701@example.invalid con sesión
    Cuando pide GET /api/resumen-curso?periodo=2026-1&asignatura=5643
    Entonces la respuesta es 403 con el código "SOLO_COORDINACION"

  @spec009 @corte1 @US-91
  Escenario: La coordinación de Ambiental recibe el resumen de 5643 sin indicadores
    Dado coordinacion@example.invalid con alcance de la carrera AMB
    Cuando pide GET /api/resumen-curso?periodo=2026-1&asignatura=5643
    Entonces la respuesta es 200 con indicadores vacío
    Y la respuesta no dice si 5643 tiene secciones en 2026-1

  @spec009 @corte1 @US-91
  Escenario: Sin sesión el resumen responde 401
    Cuando alguien sin sesión pide GET /api/resumen-curso?periodo=2026-1&asignatura=5643
    Entonces la respuesta es 401

  @spec009 @corte1 @US-91
  Escenario: Un periodo o una asignatura mal formados responden 422 sin leer la base
    Cuando coordinador.quimica@example.invalid pide GET /api/resumen-curso?periodo=2026&asignatura=5643
    Entonces la respuesta es 422
    Y con asignatura=Q43 la respuesta también es 422

  @spec009 @corte1 @US-93
  Escenario: La coordinación de la carrera recibe la lista de sus cursos con plan en el periodo
    Dado coordinacion@example.invalid con alcance de la carrera AMB
    Cuando pide GET /api/resumen-curso/cursos?periodo=2026-2 (propuesta)
    Entonces la respuesta trae 450002 y 450010 en orden de código, con su nombre
    Y no trae cursos de otra carrera

  @spec009 @corte1 @US-93
  Escenario: La coordinación del curso recibe solo su curso
    Dado coordinador.quimica@example.invalid con alcance de la asignatura 5643 en 2026-1
    Cuando pide GET /api/resumen-curso/cursos?periodo=2026-1 (propuesta)
    Entonces la respuesta trae solo 5643
