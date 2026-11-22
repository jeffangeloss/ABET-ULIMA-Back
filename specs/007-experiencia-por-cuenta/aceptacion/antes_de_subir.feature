# language: es
#
# Escenarios de aceptación de US-60 de la spec 007-experiencia-por-cuenta (épica EP-07, propuesta, etapa A).
# P3 «Subir export» dice antes del campo de archivo qué debe tener listo el profesor en Blackboard. La historia
# fusiona las candidatas C-P02 y C-T04 (revision-historias.md).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid.
#
# Vocabulario de los pasos.
# - Los nombres de columna siguen el valor provisional de D-43 de la spec 005 (una actividad por PI, como
#   «ABET SO4.1») y la regla _ENCABEZADO_DE_PI de abet_carga/lector.py, la misma de
#   ck_carga_columna_encabezado en V1_10 (J-19). Las líneas viven en una constante del Front (J-44).
# - P3 arma el apartado con el campo pi de la sección que ya recibe de P2 o de P5 (ruta 4), sin otra petición.
# - Los escenarios de P3 se prueban con Vitest en el Front y llevan @delegado_a_vitest. El último escenario
#   lo prueba pytest-bdd en el Back, sin base, y comprueba que el lector acepta el nombre que propone P3.
# - El archivo no tiene Antecedentes, porque el esquema del lector corre sin base y no hereda ninguna sesión.
#   Los escenarios de P3 escriben la sesión con «una sesión de "…" con rol "…"», un texto que la expresión
#   _sesion_iniciada de tests/aceptacion/pasos/conftest.py no captura, así que su paso solo registra la prueba
#   de Vitest y no abre la base.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: P3 dice antes de subir qué debe tener listo el profesor en Blackboard
  Como profesor, quiero ver en P3 qué columnas y qué notas espera el sistema para mi sección, para preparar
  Blackboard y subir el export una sola vez.

  @US-60 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: P3 lista antes del campo de archivo lo que el profesor debe tener listo
    Dado una sesión de "docente410@example.invalid" con rol "PROFESOR" y la sección 410 de "450002" en "2026-2"
    Y que la ruta 4 responde la sección 410 con tiene_plan "true" y pi "5.1", "5.2" y "5.3"
    Cuando el profesor pulsa «Subir export» en la fila de la sección 410
    Entonces P3 muestra, antes del campo de archivo, el apartado «Antes de subir» (propuesta) con estas líneas, en este orden
      | Línea                                                                                                                                      |
      | En Blackboard, una columna por PI, con el nombre ABET SO5.1, ABET SO5.2 y ABET SO5.3.                                                       |
      | En cada columna, un nivel entero de 1 a 4 por estudiante. El puntaje máximo de la columna es 4, y otro puntaje máximo solo deja un aviso.  |
      | Conserve la columna Username y no cambie el nombre de las columnas.                                                                        |
      | Suba el export completo del Centro de calificaciones sin cambiarle el nombre, porque la hoja o el nombre que le pone Blackboard indican la sección. |
    # Las cuatro líneas son propuestas que siguen el valor provisional de D-43, D-06 y D-04.

  @US-60 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Esquema del escenario: La primera línea nombra los PI de la sección elegida
    Dado una sesión de "docente410@example.invalid" con rol "PROFESOR" y la sección 410 de "450002" en "2026-2"
    Y que la ruta 4 responde la sección 410 con tiene_plan "true" y pi <pi>
    Cuando el profesor abre P3 de la sección 410
    Entonces la primera línea del apartado «Antes de subir» dice «<linea>»

    Ejemplos:
      | pi              | linea                                                                            |
      | "5.1"           | En Blackboard, una columna por PI, con el nombre ABET SO5.1.                      |
      | "6.1" y "6.10"  | En Blackboard, una columna por PI, con el nombre ABET SO6.1 y ABET SO6.10.         |

  @US-60 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: El apartado sale solo del plan y no lee el archivo
    Dado una sesión de "docente410@example.invalid" con rol "PROFESOR" y la sección 410 de "450002" en "2026-2"
    Y que la ruta 4 responde la sección 410 con tiene_plan "true" y pi "5.1", "5.2" y "5.3"
    Cuando el profesor abre P3 de la sección 410 y elige un archivo
    Entonces el apartado «Antes de subir» no cambia
    Y P3 no hace ninguna petición hasta que el profesor pulsa «Subir»

  @US-60 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: El modo reemplazo muestra el mismo apartado
    Dado una sesión de "docente410@example.invalid" con rol "PROFESOR" y la sección 410 de "450002" en "2026-2"
    Y que la ruta 4 responde la sección 410 con tiene_plan "true" y pi "5.1", "5.2" y "5.3"
    Y que la sección 410 tiene la carga 7 en estado "PUBLICADA"
    Cuando el profesor abre P3 desde «Reemplazar carga» de la carga 7 en P5
    Entonces P3 muestra el apartado «Antes de subir» con las mismas cuatro líneas

  @US-60 @spec007 @corte1 @etapa_a
  Esquema del escenario: El lector de exports reconoce el nombre que propone P3 y no el que lleva guiones
    Dado el encabezado de Blackboard «<encabezado>»
    Cuando el lector de exports de abet_carga/lector.py clasifica la columna
    Entonces la columna queda como <resultado>

    Ejemplos:
      | encabezado                                       | resultado                   |
      | ABET SO5.1 [Total Pts: 4 Score] \|9000051         | columna del PI 5.1          |
      | ABET SO6.10 [Total Pts: 4 Score] \|9000610        | columna del PI 6.10         |
      | ABET-SO5-PI5.1 [Total Pts: 4 Score] \|9000051     | columna que no es de un PI  |
