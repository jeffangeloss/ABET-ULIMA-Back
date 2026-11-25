# language: es
#
# Escenarios de aceptación de US-100 de la spec 011-historico-y-competencias (épica EP-11, propuesta). La ruta 22 da a
# la coordinación, para un curso, las cifras del curso y de cada sección en cada periodo visible, como la página
# «Histórico por Profesor» del tablero de Stefanny Montaño sin el segmentador de profesor (D-57 y D-59).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid y estudiantes del rango
# 99500000 a 99599999.
#
# Vocabulario de los pasos.
# - La base tiene db/datos/quimica_2026_1_inventado.sql y plan_quimica_2026_1.sql de la spec 008 y la semilla
#   db/datos/historico_quimica_inventado.sql de US-105 (propuesta), con 5643 y su PI 6.1 en 2025-1, 2025-2 y 2026-1,
#   la 701 y la 702 en 2025-1, la 701 a la 703 en 2025-2 y la 701 a la 704 en 2026-1, y la coordinación del curso
#   coordinador.quimica@example.invalid con una fila de alcance de 5643 en cada periodo.
# - «Las cargas del oráculo» son las de tests/datos_inventados/oraculo_011.md (propuesta), publicadas con
#   R-2026-BORRADOR de Industrial y con los niveles [n1, n2, n3, n4] de la tabla de la spec.
# - Los porcentajes se redondean a un decimal y los promedios a dos en PostgreSQL con numeric, y cifra() los convierte
#   en números JSON, así que 2,70 viaja como 2.7.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Evolución del curso para su coordinación
  Como coordinación de Química General, quiero recibir de una sola vez las cifras del curso y de cada sección en cada
  periodo con carga, para saber si el curso mejora entre ciclos.

  Antecedentes:
    Dado una base desechable de la spec 011 con la siembra de Química de 2026-1 y la semilla histórica de 2025-1 y 2025-2

  @spec011 @corte1 @US-100
  Escenario: La evolución trae un elemento por periodo en orden cronológico
    Dado las cargas del oráculo de 5643 en 2025-1, 2025-2 y 2026-1
    Cuando coordinador.quimica@example.invalid pide GET /api/resumen-curso/evolucion?asignatura=5643 (propuesta)
    Entonces la respuesta es 200
    Y el PI 6.1 trae periodos 2025-1, 2025-2 y 2026-1 en ese orden
    Y en curso trae logrados 6, 8 y 12 y calificados 10, 12 y 15 en ese orden
    Y en curso trae pct_sobre_calificados 60.0, 66.7 y 80.0 y en_meta falso, falso y verdadero en ese orden

  @spec011 @corte1 @US-100
  Escenario: Cada periodo suma alumnos y no promedia porcentajes
    Dado en 2025-2 la 701 con los niveles [0, 1, 2, 1], la 702 con [0, 1, 3, 1] y la 703 con [1, 1, 1, 0] y un alumno sin evidencia
    Cuando coordinador.quimica@example.invalid pide la evolución de 5643
    Entonces el periodo 2025-2 trae en curso pct_sobre_calificados 66.7
    Y no trae 62.8, que es el promedio de 75.0, 80.0 y 33.3

  @spec011 @corte1 @US-100
  Escenario: Cada periodo trae sus niveles, su promedio y sus alumnos sin evidencia
    Dado las cargas del oráculo de 5643 en 2025-1, 2025-2 y 2026-1
    Cuando coordinador.quimica@example.invalid pide la evolución de 5643
    Entonces el periodo 2025-1 trae en curso estudiantes_por_nivel [1, 3, 4, 2] y promedio_nivel 2.7
    Y el periodo 2025-2 trae en curso calificados 12, sin_evidencia 1, total 13 y promedio_nivel 2.75
    Y el periodo 2026-1 trae en curso promedio_nivel 3.07

  @spec011 @corte1 @US-100
  Escenario: El conteo de secciones de cada periodo cuenta la meta solo sobre las publicadas
    Dado las cargas del oráculo de 5643 en 2025-1, 2025-2 y 2026-1
    Cuando coordinador.quimica@example.invalid pide la evolución de 5643
    Entonces conteo_secciones de 2025-1 trae total 2, publicadas 2, en_meta 1, debajo_de_la_meta 1 y sin_dato 0
    Y conteo_secciones de 2025-2 trae total 3, publicadas 3, en_meta 1, debajo_de_la_meta 2 y sin_dato 0
    Y conteo_secciones de 2026-1 trae total 4, publicadas 3, en_meta 2, debajo_de_la_meta 1 y sin_dato 1

  @spec011 @corte1 @US-100
  Escenario: Las secciones van dentro de su periodo y en orden de número
    Dado las cargas del oráculo de 5643 en 2025-1, 2025-2 y 2026-1
    Cuando coordinador.quimica@example.invalid pide la evolución de 5643
    Entonces secciones de 2025-2 trae la 701, la 702 y la 703 en ese orden
    Y la 703 de 2025-2 trae pct_sobre_calificados 33.3 y en_meta falso
    Y la 701 de 2025-1 y la 701 de 2025-2 traen seccion_id distintos y cada una aparece solo dentro de su periodo

  @spec011 @corte1 @US-100
  Escenario: Un periodo con secciones y sin cargas publicadas trae nulos y no ceros
    Dado las cargas del oráculo de 5643 en 2025-2 y 2026-1 y ninguna carga publicada en 2025-1
    Cuando coordinador.quimica@example.invalid pide la evolución de 5643
    Entonces el periodo 2025-1 trae en curso calificados 0 y pct_sobre_calificados, promedio_nivel y en_meta en null
    Y conteo_secciones de 2025-1 trae publicadas 0 y sin_dato 2

  @spec011 @corte1 @US-100
  Escenario: Metas distintas dentro de un periodo dejan nula solo la meta de ese periodo
    Dado la 701 de 2025-1 publicada con R-2026-BORRADOR de Industrial, con META_LOGRO 0,80
    Y la 702 de 2025-1 publicada con R-2025-INVENTADO, un conjunto de Industrial creado en la prueba con META_LOGRO 0,70 DEFINIDO
    Y las cargas del oráculo de 5643 en 2025-2 y 2026-1
    Cuando coordinador.quimica@example.invalid pide la evolución de 5643
    Entonces el periodo 2025-1 trae meta_pct en null y en curso en_meta en null
    Y los periodos 2025-2 y 2026-1 traen meta_pct 80.0

  @spec011 @corte1 @US-100
  Escenario: Los periodos siguen el año y el ciclo y no el resultado
    Dado el periodo 2025-0 creado en la prueba con la vigencia de IND-2026, la 701 de 5643, su fila de alcance y una carga con los niveles [0, 0, 0, 5]
    Y las cargas del oráculo de 5643 en 2025-1, 2025-2 y 2026-1
    Cuando coordinador.quimica@example.invalid pide la evolución de 5643
    Entonces el PI 6.1 trae periodos 2025-0, 2025-1, 2025-2 y 2026-1 en ese orden
    Y el orden no cambia aunque 2025-0 tenga el porcentaje más alto

  @spec011 @corte1 @US-100
  Escenario: La coordinación del curso ve solo los periodos de su alcance
    Dado coordinador.quimica@example.invalid sin la fila de alcance de 5643 en 2025-1
    Y las cargas del oráculo de 5643 en 2025-1, 2025-2 y 2026-1
    Cuando pide la evolución de 5643
    Entonces el PI 6.1 trae solo los periodos 2025-2 y 2026-1

  @spec011 @corte1 @US-100
  Escenario: Cada periodo trae las mismas cifras que la ruta 20 de ese periodo
    Dado las cargas del oráculo de 5643 en 2025-1, 2025-2 y 2026-1
    Cuando coordinador.quimica@example.invalid pide la evolución de 5643 y GET /api/resumen-curso?periodo=2025-2&asignatura=5643
    Entonces curso, conteo_secciones y secciones del periodo 2025-2 son iguales a los del PI 6.1 de la ruta 20

  @spec011 @corte1 @US-100
  Escenario: Con un conjunto de reglas provisional cada periodo sale provisional
    Dado las cargas del oráculo publicadas con R-2026-BORRADOR de Industrial, que tiene parámetros PENDIENTE
    Cuando coordinador.quimica@example.invalid pide la evolución de 5643
    Entonces cada periodo del PI 6.1 trae provisional verdadero

  @spec011 @corte1 @US-100
  Escenario: La respuesta de la evolución trae solo las claves de su lista cerrada
    Dado las cargas del oráculo de 5643 con «Profesor Inventado Setecientos Uno» en la 701 de cada periodo
    Cuando coordinador.quimica@example.invalid pide la evolución de 5643
    Entonces la respuesta trae solo las claves de la lista cerrada de la ruta 22 del contrato
    Y no trae correos, nombres de personas, usuario_id, subida_por, nombre_archivo ni sha256
    Y ni el texto «Profesor Inventado» ni un número de 8 cifras aparecen en el cuerpo de la respuesta

  @spec011 @corte1 @US-100
  Escenario: El profesor recibe 403 en la evolución del curso
    Dado docente701@example.invalid con sesión
    Cuando pide GET /api/resumen-curso/evolucion?asignatura=5643
    Entonces la respuesta es 403 con «Esta página es de la Coordinación.»

  @spec011 @corte1 @US-100
  Escenario: Sin sesión la evolución responde 401
    Cuando alguien sin sesión pide GET /api/resumen-curso/evolucion?asignatura=5643
    Entonces la respuesta es 401

  @spec011 @corte1 @US-100
  Escenario: Una asignatura mal formada responde 422 sin leer la base
    Cuando coordinador.quimica@example.invalid pide GET /api/resumen-curso/evolucion?asignatura=56A3
    Entonces la respuesta es 422 con «La asignatura no tiene la forma de un código de 4 o 6 cifras.»
    Y sin asignatura la respuesta también es 422

  @spec011 @corte1 @US-100
  Escenario: La coordinación de Ambiental recibe la evolución de 5643 sin indicadores
    Dado coordinacion@example.invalid con alcance de la carrera AMB
    Y las cargas del oráculo de 5643 en 2025-1, 2025-2 y 2026-1
    Cuando pide GET /api/resumen-curso/evolucion?asignatura=5643
    Entonces la respuesta es 200 con indicadores vacío y el nombre de la asignatura en null
