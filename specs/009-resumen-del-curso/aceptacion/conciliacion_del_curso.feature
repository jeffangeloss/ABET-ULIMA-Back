# language: es
#
# Escenarios de aceptación de US-94 de la spec 009-resumen-del-curso (épica EP-09, propuesta). El conciliador de la
# spec 008 compara también las cifras del curso y de cada sección de la ruta 20 con la tabla maestra, para mostrar a
# Stefanny Montaño que P8 da lo mismo que su tablero.
#
# Este archivo usa solo datos inventados. La corrida con la tabla maestra real ocurre fuera de todo repositorio, y
# su salida dice solo «igual» o «distinto», sin códigos, nombres ni cifras de una sección real.
#
# Vocabulario de los pasos.
# - La tabla maestra inventada es la de ensayo_y_conciliacion.feature de la spec 008, con la 701, la 702 y la 703 de
#   5643 en 2026-1, y las cargas salen del ensayo de esa spec.
# - El promedio de la tabla maestra es la media de CALIFICACIÓN de los alumnos calificados, redondeada a dos
#   decimales, y el porcentaje cuenta los alumnos en el nivel esperado o superior (D-56, cerrada el 2026-11-25 sin cambio).

Característica: Conciliación del resumen del curso con la tabla maestra
  Como dueño técnico, quiero que el conciliador compare el resumen del curso con la tabla maestra, para probar
  que P8 da las mismas cifras que el tablero de Stefanny.

  Antecedentes:
    Dado una base desechable de la spec 009 con el ensayo inventado de 5643 en 2026-1 publicado

  @spec009 @corte1 @US-94
  Escenario: El conciliador dice que el curso es igual a la tabla maestra
    Cuando corre el conciliador con la tabla maestra inventada y la opción --curso (propuesta)
    Entonces la salida trae «Curso igual en alumnos en el nivel esperado o superior, en el porcentaje, en el promedio y en las secciones en la meta.»
    Y cada sección trae su línea de la spec 008 y además «promedio igual»
    Y el código de salida es 0

  @spec009 @corte1 @US-94
  Escenario: Una calificación cambiada en la tabla maestra hace distinto al curso
    Dado la tabla maestra inventada con una calificación de la 702 cambiada de 4 a 2
    Cuando corre el conciliador con --curso
    Entonces la salida dice que el curso y la 702 son distintos en el promedio y en el porcentaje
    Y no muestra el código del estudiante ni la calificación
    Y el código de salida es 1
