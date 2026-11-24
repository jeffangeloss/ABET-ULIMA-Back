# language: es
#
# Escenarios de aceptación de US-92 de la spec 009-resumen-del-curso (épica EP-09, propuesta). P8 «Resumen del
# curso» dibuja lo que trae la ruta 20, con la tabla y las barras de la página «Resumen Curso» del tablero de
# Stefanny Montaño, sin profesores, sin torta y sin biblioteca de gráficos (J-24 de ADR-008 y ADR-010, propuesta).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid.
#
# Vocabulario de los pasos.
# - Los escenarios de pantalla los prueba Vitest en el Front con la respuesta simulada del primer escenario de
#   resumen_del_curso.feature y llevan @delegado_a_vitest, y los de Playwright llevan @playwright.
# - P8 escribe lo que trae la API y no recalcula ninguna cifra (BR-RESULTADOS-11).
# - Los rótulos «En la meta», «Debajo de la meta», «Sin carga publicada» y «Meta 80 %» son los de P6.

Característica: Pantalla del resumen del curso
  Como coordinación de Química General, quiero ver en una página las cifras del curso, una barra por sección y la
  tabla de secciones, para ubicar qué secciones necesitan un plan de acción.

  @spec009 @corte1 @US-92 @delegado_a_vitest
  Escenario: P8 escribe las cifras del curso con su barra de dos tramos
    Dado la respuesta de la ruta 20 con el curso en 23 de 33 y 69,7 %
    Cuando la coordinación abre P8 de 5643 en 2026-1
    Entonces P8 dice «23 de 33 alumnos en el nivel esperado o superior (69,7 %)»
    Y dice «Promedio de calificación 2,91 de 4»
    Y dice «1 de 3 secciones publicadas en la meta» y «1 sección sin carga publicada»
    Y la barra del curso dice «Nivel esperado o superior, 23 alumnos, 69,7 %» y «Debajo del nivel esperado, 10 alumnos, 30,3 %»

  @spec009 @corte1 @US-92 @delegado_a_vitest
  Escenario: P8 trae una fila por sección con su barra y la línea de la meta
    Dado la respuesta de la ruta 20 con la 701, la 702, la 703 y la 704
    Cuando la coordinación abre P8
    Entonces la tabla trae la 701, la 702, la 703 y la 704 en ese orden
    Y cada fila escribe calificados, porcentaje, promedio y «En la meta» o «Debajo de la meta»
    Y la 704 dice «Sin carga publicada» y no dibuja una barra de 0 %
    Y cada barra marca «Meta 80 %» y lleva aria-hidden, con su cifra escrita en la fila

  @spec009 @corte1 @US-92 @delegado_a_vitest
  Escenario: P8 no muestra profesores ni ordena por resultado
    Dado la respuesta de la ruta 20 con secciones de 90,0, 53,8 y 70,0 %
    Cuando la coordinación abre P8
    Entonces las filas van en orden de número de sección y no de porcentaje
    Y ninguna celda trae un correo ni un nombre de profesor
    Y P8 no trae una torta ni la tarjeta de porcentaje de profesores

  @spec009 @corte1 @US-92 @delegado_a_vitest
  Escenario: P8 marca las cifras provisionales
    Dado la respuesta de la ruta 20 con provisional verdadero
    Cuando la coordinación abre P8
    Entonces P8 muestra la franja «Cifras provisionales» de P6

  @spec009 @corte1 @US-92 @delegado_a_vitest
  Escenario: P8 de un curso sin cargas no dibuja barras de 0 %
    Dado la respuesta de la ruta 20 con calificados 0 y nulos
    Cuando la coordinación abre P8
    Entonces P8 dice «Todavía no hay cargas publicadas en este curso.»
    Y no dibuja la barra del curso

  @spec009 @corte1 @US-92 @delegado_a_vitest
  Escenario: Solo la coordinación ve «Resumen del curso» en el menú
    Dado una sesión de coordinador.quimica@example.invalid y otra de docente701@example.invalid
    Cuando cada una abre el menú
    Entonces la coordinación ve «Resumen del curso» y el profesor no
    Y P7 de la coordinación enlaza cada curso con su P8

  @spec009 @corte1 @US-92 @playwright
  Escenario: P8 a 375 px no se desplaza a lo ancho y se recorre con teclado
    Dado la coordinación en P8 con la API simulada a 375 px de ancho
    Entonces la página no se desplaza a lo ancho
    Y cada barra tiene su cifra en texto y el foco recorre la tabla en orden
