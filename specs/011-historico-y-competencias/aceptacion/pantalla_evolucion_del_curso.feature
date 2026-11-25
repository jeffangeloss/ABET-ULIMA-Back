# language: es
#
# Escenarios de aceptación de US-101 de la spec 011-historico-y-competencias (épica EP-11, propuesta). P9 «Evolución
# del curso» dibuja lo que trae la ruta 22, con una fila por periodo y el detalle de sus secciones, sin profesores y sin
# biblioteca de gráficos (J-24 de la spec 004, que recogen ADR-008 y ADR-010, y ADR-011, propuesta).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid.
#
# Vocabulario de los pasos.
# - Los escenarios de pantalla los prueba Vitest en el Front con la respuesta simulada del primer escenario de
#   evolucion_del_curso.feature y llevan @delegado_a_vitest, y los de Playwright llevan @playwright.
# - P9 escribe lo que trae la API y no recalcula ninguna cifra (BR-RESULTADOS-11).
# - Los rótulos «En la meta», «Debajo de la meta», «Sin carga publicada», «Meta 80 %» y «Cifras provisionales.» son
#   los de P6 y P8.

Característica: Pantalla de la evolución del curso
  Como coordinación de Química General, quiero ver una fila por periodo con la cifra del curso y abrir cada periodo
  para ver sus secciones, para saber si el curso mejora entre ciclos.

  @spec011 @corte1 @US-101 @delegado_a_vitest
  Escenario: P9 escribe una fila por periodo en orden cronológico con su cifra
    Dado la respuesta de la ruta 22 con 5643 en 2025-1, 2025-2 y 2026-1
    Cuando la coordinación abre P9 de 5643
    Entonces P9 trae las filas 2025-1, 2025-2 y 2026-1 en ese orden
    Y la fila de 2025-1 dice «6 de 10 alumnos en el nivel esperado o superior (60,0 %)» y «Debajo de la meta»
    Y la fila de 2025-2 dice «8 de 12 alumnos en el nivel esperado o superior (66,7 %)» y «Debajo de la meta»
    Y la fila de 2026-1 dice «12 de 15 alumnos en el nivel esperado o superior (80,0 %)» y «En la meta»

  @spec011 @corte1 @US-101 @delegado_a_vitest
  Escenario: Cada fila escribe su promedio, sus alumnos sin evidencia y sus secciones en la meta
    Dado la respuesta de la ruta 22 con 5643 en 2025-1, 2025-2 y 2026-1
    Cuando la coordinación abre P9 de 5643
    Entonces la fila de 2025-1 dice «Promedio de calificación 2,70 de 4» y «1 de 2 secciones publicadas en la meta»
    Y la fila de 2025-2 dice «1 alumno sin evidencia» y «1 de 3 secciones publicadas en la meta»
    Y la fila de 2026-1 dice «2 de 3 secciones publicadas en la meta» y «1 sección sin carga publicada»

  @spec011 @corte1 @US-101 @delegado_a_vitest
  Escenario: La barra de cada periodo lleva su cifra escrita
    Dado la respuesta de la ruta 22 con 5643 en 2025-1, 2025-2 y 2026-1
    Cuando la coordinación abre P9 de 5643
    Entonces la barra de 2025-1 dice «Nivel esperado o superior, 6 alumnos, 60,0 %» y «Debajo del nivel esperado, 4 alumnos, 40,0 %»
    Y cada barra marca «Meta 80 %» y lleva aria-hidden, con su cifra escrita en la fila

  @spec011 @corte1 @US-101 @delegado_a_vitest
  Escenario: El detalle de un periodo trae sus secciones en orden de número con la meta absoluta
    Dado la respuesta de la ruta 22 con 5643 en 2025-1, 2025-2 y 2026-1
    Cuando la coordinación despliega el periodo 2025-2 y después el 2026-1
    Entonces 2025-2 trae la 701 con «75,0 %» y «Debajo de la meta», la 702 con «80,0 %» y «En la meta» y la 703 con «33,3 %» y «Debajo de la meta»
    Y en 2026-1 la 702 dice «80,0 %» y «En la meta» aunque sea el menor porcentaje en la meta de la tabla

  @spec011 @corte1 @US-101 @delegado_a_vitest
  Escenario: Un periodo sin cargas publicadas no dibuja una barra de 0 %
    Dado la respuesta de la ruta 22 con el periodo 2025-1 en calificados 0 y nulos
    Cuando la coordinación abre P9 de 5643
    Entonces la fila de 2025-1 dice «Sin carga publicada» y no dibuja barra ni porcentaje
    Y las filas de 2025-2 y 2026-1 conservan su barra

  @spec011 @corte1 @US-101 @delegado_a_vitest
  Escenario: P9 no muestra profesores ni ordena por resultado
    Dado la respuesta de la ruta 22 con 5643 en 2025-1, 2025-2 y 2026-1
    Cuando la coordinación abre P9 de 5643
    Entonces las filas van en orden de periodo y no de porcentaje, y ningún control ordena por porcentaje
    Y ninguna celda trae un correo ni el texto «Profesor Inventado»
    Y ninguna línea ni fila une la 701 de un periodo con la 701 de otro

  @spec011 @corte1 @US-101 @delegado_a_vitest
  Escenario: P9 marca las cifras provisionales
    Dado la respuesta de la ruta 22 con provisional verdadero en cada periodo
    Cuando la coordinación abre P9 de 5643
    Entonces P9 muestra la franja «Cifras provisionales.» sobre la tabla

  @spec011 @corte1 @US-101 @delegado_a_vitest
  Escenario: La coordinación de la carrera elige el curso de la evolución
    Dado coordinacion@example.invalid con la respuesta de la ruta 21 de 2026-2 con 450002, 450010, 5674 y 6511
    Cuando abre P9
    Entonces el selector «Curso» ofrece 450002, 450010, 5674 y 6511 en orden de código
    Y al elegir 6511 la dirección termina en «#/evolucion?asignatura=6511»
    Pero coordinador.quimica@example.invalid, con la ruta 21 de 2026-1 solo con 5643, no ve el selector

  @spec011 @corte1 @US-101 @delegado_a_vitest
  Escenario: Solo la coordinación ve la evolución y la abre desde P7 y P8
    Dado una sesión de coordinador.quimica@example.invalid y otra de docente701@example.invalid
    Cuando cada una abre el menú
    Entonces la coordinación ve «Evolución del curso» después de «Resumen del curso» y el profesor no
    Y la dirección «#/evolucion» lleva al profesor a su pantalla de llegada
    Y en P8 de 5643 la coordinación pulsa «Ver la evolución del curso» y la dirección termina en «#/evolucion?asignatura=5643»
    Y al pulsar «Atrás» vuelve al resumen del curso 5643, y P7 enlaza cada curso con su P9

  @spec011 @corte1 @US-101 @playwright
  Escenario: P9 a 375 px no se desplaza a lo ancho y se recorre con teclado
    Dado la coordinación en P9 con la API simulada a 375 px de ancho
    Entonces la página no se desplaza a lo ancho
    Y cada barra tiene su cifra en texto y el foco recorre los periodos y sus secciones en orden
