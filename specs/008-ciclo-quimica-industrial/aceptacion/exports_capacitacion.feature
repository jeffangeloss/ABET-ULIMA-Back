# language: es
#
# Escenarios de aceptación de US-74 de la spec 008-ciclo-quimica-industrial (épica EP-08, propuesta). El
# generador scripts/generar_exports_desde_maestra.py (propuesta) arma desde la tabla maestra conglomerada un
# export con el formato de Blackboard por sección, con los códigos y los niveles de la tabla y sin nombres, para
# que cada profesor suba el suyo en la capacitación (C-60 con C-04, decisión A de Jefferson).
#
# Este archivo usa solo datos inventados. La tabla maestra de las pruebas es inventada, con las secciones 701,
# 702 y 703 de 5643 en 2026-1, códigos del rango 99 y el PI 6.1, y la programación inventada trae el
# curso_blackboard SINTETICO_20261_5643_70N de cada sección. El generador nunca lee la tabla real en una prueba,
# y la corrida con la tabla real se hace fuera del repositorio, desde una carpeta que no está en git.
#
# Vocabulario de los pasos.
# - Las entradas son la tabla maestra (.xlsx o .csv con las columnas AÑO, CICLO, CÓDIGO DEL CURSO, CURSO, CICLO
#   DEL CURSO, SO, PI, PROFESOR, CÓDIGO DEL ESTUDIANTE, SECCIÓN, CALIFICACIÓN y ARCHIVO) y el CSV de la
#   programación de la spec 006, única fuente del curso_blackboard (veredicto SE_SOSTIENE del crítico).
# - Los parámetros son --periodo, --asignatura, --pi y --fecha, que fija la fecha del nombre del archivo para que
#   la salida sea determinista (propuesta). La escritura reutiliza la de scripts/generar_exports_inventados.py.
# - Las filas de otro periodo, de otra asignatura o de otro PI se omiten y se cuentan en el manifiesto, y una
#   fila defectuosa de lo que se exporta detiene toda la generación sin mostrar su valor.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Exports de capacitación generados desde la tabla maestra
  Como Oficina de Calidad, quiero un export por sección con el formato que el sistema lee, los códigos y los
  niveles de la tabla maestra y sin nombres, para que cada profesor de química suba el suyo en la capacitación.

  Antecedentes:
    Dado una tabla maestra inventada con las filas de las secciones "701", "702" y "703" de "5643" en 2026 ciclo 1 con el PI "6.1"
    Y la programación inventada con el curso_blackboard "SINTETICO_20261_5643_701", "SINTETICO_20261_5643_702" y "SINTETICO_20261_5643_703"
    Y una carpeta de salida fuera de todo repositorio git

  @spec008 @US-74
  Escenario: Cada sección da un export que el lector y la validación aceptan sin rechazos
    Cuando el generador corre con --periodo 2026-1 --asignatura 5643 --pi 6.1 --fecha 2026-07-15-00-00-00
    Entonces la carpeta de salida tiene 3 archivos .xlsx y "manifiesto.json"
    Y el archivo de la 701 se llama "gc_SINTETICO_20261_5643_701_fullgc_2026-07-15-00-00-00.xlsx" y su hoja "gc_SINTETICO_20261_5643_701_f"
    Y el lector declara de ese archivo el periodo "2026-1", la asignatura "5643" y la sección "701"
    Y el lector clasifica la columna "ABET SO6.1 [Total Pts: 4 Score] |9000061" como la columna del PI 6.1
    Y validar() acepta todas las filas de la 701 sin rechazos

  @spec008 @US-74
  Escenario: La ida y vuelta por el lector da los mismos códigos y niveles que la tabla maestra
    Dado en la tabla maestra la 702 con "99000004" en 1, "99000005" en 3 y "99000006" en 4
    Cuando el generador corre y el lector lee el archivo de la 702
    Entonces lo leído trae en Username "99000004", "99000005" y "99000006" con los niveles 1, 3 y 4
    Y el conteo por nivel de lo leído es igual al de la tabla maestra para la 702
    Y ningún código de la 701 ni de la 703 aparece en el archivo de la 702

  @spec008 @US-74
  Escenario: El export trae solo el código y la columna del PI, sin nombres ni el profesor
    Dado en la tabla maestra la columna PROFESOR con "Docente Inventado Uno" en la 701
    Cuando el generador corre
    Entonces cada archivo tiene solo las columnas "Username" y "ABET SO6.1 [Total Pts: 4 Score] |9000061" (propuesta)
    Y ninguna columna se llama como las que busca la consulta de control Q04
    Y ninguna celda repite "Docente Inventado Uno" ni un valor de la columna ARCHIVO de la tabla maestra

  @spec008 @US-74
  Escenario: Un código con cero a la izquierda se escribe como texto
    Dado una fila de la 701 con un código de ocho cifras que empieza con cero, armado por la prueba
    Cuando el generador corre
    Entonces la celda del código es texto y el lector lee las mismas ocho cifras, con el cero

  @spec008 @US-74
  Escenario: El curso de cada archivo es el de la programación y no uno armado por el generador
    Dado la programación inventada con el curso_blackboard "SINTETICO_20261_5643_701" de la 701
    Cuando el generador corre
    Entonces el nombre y la hoja del archivo de la 701 llevan exactamente ese curso
    Y una sección de la tabla maestra sin fila en la programación detiene el generador con «Fila 5. La sección no está en la programación del curso.» (propuesta)

  @spec008 @US-74
  Escenario: Dos corridas dan los mismos archivos byte a byte
    Cuando el generador corre dos veces con los mismos parámetros sobre la misma tabla maestra
    Entonces cada archivo tiene la misma huella SHA-256 en las dos corridas

  @spec008 @US-74
  Escenario: El manifiesto resume cada export sin códigos
    Cuando el generador corre
    Entonces "manifiesto.json" trae una entrada por sección con la sección, el nombre del archivo, su huella SHA-256, las filas y el conteo de los niveles 1, 2, 3 y 4
    Y el manifiesto no trae ningún número de ocho cifras ni ningún nombre

  @spec008 @US-74
  Escenario: Las filas de otro periodo, otra asignatura u otro PI se omiten y se cuentan
    Dado 5 filas de 2025 ciclo 2, 2 filas de la asignatura "450002" y 3 filas del PI "6.2" en la tabla maestra
    Cuando el generador corre con --periodo 2026-1 --asignatura 5643 --pi 6.1
    Entonces esas 10 filas no entran a ningún archivo
    Y el manifiesto las cuenta como 5 omitidas por periodo, 2 por asignatura y 3 por PI (propuesta)

  @spec008 @US-74
  Escenario: El PI llega por parámetro para la decisión abierta D-48
    Dado la tabla maestra con todas sus filas en el PI "6.2"
    Cuando el generador corre con --pi 6.2
    Entonces los archivos llevan la columna "ABET SO6.2 [Total Pts: 4 Score] |9000062"
    Y con --pi 6.1 el generador termina con código 1 y dice «Ninguna fila es del PI 6.1.» (propuesta)

  @spec008 @US-74
  Esquema del escenario: Una fila defectuosa detiene la generación entera sin mostrar el valor
    Dado en la tabla maestra la fila 5 con <defecto>
    Cuando el generador corre
    Entonces el generador termina con código 1 y la carpeta de salida queda sin exports
    Y el informe dice «Fila 5. <motivo>» (propuesta)
    Y el informe no repite el código ni la calificación

    Ejemplos:
      | defecto                                                   | motivo                                            |
      | el código "9900001" de siete cifras                       | El código del estudiante no tiene 8 cifras.       |
      | la calificación 5                                         | La calificación no es un entero de 1 a 4.         |
      | la calificación 17                                        | La calificación no es un entero de 1 a 4.         |
      | la calificación 3,5                                       | La calificación no es un entero de 1 a 4.         |
      | la calificación vacía                                     | La calificación está vacía.                       |
      | el código "99000001" que también está en la 702           | El estudiante aparece en dos secciones del curso. |
      | el código "99000002" repetido en la 701                   | El estudiante aparece dos veces en la sección.    |

  @spec008 @US-74
  Escenario: Sin la columna CALIFICACIÓN el generador no adivina
    Dado una tabla maestra sin la columna CALIFICACIÓN
    Cuando el generador corre
    Entonces termina con código 1 y dice «Falta la columna CALIFICACIÓN de la tabla maestra.» (propuesta)

  @spec008 @US-74
  Escenario: La carpeta de salida dentro de un repositorio se rechaza
    Dado una carpeta de salida dentro de la copia de trabajo del Back
    Cuando el generador corre
    Entonces termina con código 2 sin escribir nada
    Y dice «La carpeta de salida está dentro de un repositorio git. Elija una carpeta fuera de los repositorios.» (propuesta)

  @spec008 @US-74
  Escenario: La salida del generador no muestra códigos ni nombres
    Cuando el generador corre
    Entonces la salida dice por sección el número de filas y el conteo por nivel
    Y la salida no contiene ningún número de ocho cifras

  @spec008 @US-74
  Escenario: Un archivo de ejercicio por profesor tiene su propia huella
    Cuando el generador corre con --ejercicio 3 sobre una tabla maestra inventada de la sección ficticia "799" (propuesta)
    Entonces la carpeta de salida tiene 3 archivos de ejercicio de la 799 con códigos 99 distintos
    Y las 3 huellas SHA-256 son distintas, para que uq_archivo_origen_sha256 no confunda dos subidas
