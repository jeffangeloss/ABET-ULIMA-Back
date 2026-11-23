# language: es
#
# Escenarios de aceptación de US-78 de la spec 008-ciclo-quimica-industrial (épica EP-08, propuesta). El R-17 de
# una sección de 5643 dice la carrera de su carga y trae el instrumento, los conteos y el porcentaje del PI 6.1,
# y la ruta 12 y P6 toman el SO y el PI del catálogo de esa carrera (C-06 corregida, con el escenario del catálogo
# de C-08 y la fila de P6 que no depende solo del color).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid. El texto del PI y la
# descripción del instrumento salen de la base inventada del escenario.
#
# Vocabulario de los pasos.
# - La plantilla sigue siendo plantillas/R017_ambiental_general.xlsx, cuya única cadena de Ambiental es B6, y el
#   R-17 escribe en B6 «Carrera de» más abet.carrera.nombre de abet.carga.carrera_id (BR-R17-13, propuesta).
# - _frecuencias() escribe en M24 los estudiantes con nivel 1 o 2, en M25 los de nivel 3 o 4 y en M26 la
#   fracción de M25 sobre los dos, y el bloque II escribe en E24 la fracción de pct_logro_sobre_calificados con el
#   formato 0.0 % y en G24 la meta. K24 y K25 son rótulos.
# - Con R-2026-BORRADOR en BORRADOR, abet.v_r17_por_pi marca provisional verdadero, así que el nombre del R-17
#   lleva siempre _PROVISIONAL en la capacitación (valor provisional de D-54).
# - Los escenarios de pantalla los prueba Vitest en el Front y llevan @delegado_a_vitest.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: R-17 y logros de Química General con la carrera de su carga
  Como profesor de 5643, quiero que el R-17 y mis logros digan mi carrera, mi SO, mi PI y mis cifras, para
  entregar el R-17 del sistema en lugar del que llené a mano.

  Antecedentes:
    Dado una base desechable de la spec 008 con el plan de 5643 en 2026-1 para "IND" con el PI 6.1, el instrumento «Portafolio 3» y la descripción "Texto de prueba del Portafolio 3"
    Y la carga PUBLICADA inventada de la 701 con 3 de nivel 1, 5 de nivel 2, 20 de nivel 3 y 6 de nivel 4
    Y "docente701@example.invalid" tiene la sesión iniciada con rol "PROFESOR"

  @spec008 @corte1 @US-78
  Esquema del escenario: El encabezado dice la carrera de la carga
    Dado una carga PUBLICADA inventada de <asignatura> cuyo plan es de <carrera>
    Cuando se descarga su R-17
    Entonces la celda B6 dice «Carrera de <nombre>»

    Ejemplos:
      | asignatura | carrera | nombre                |
      | 5643       | IND     | Ingeniería Industrial |
      | 450002     | AMB     | Ingeniería Ambiental  |

  @spec008 @corte1 @US-78
  Escenario: Ninguna otra celda de la plantilla nombra a Ambiental
    Cuando se recorren todas las celdas de todas las hojas del R-17 de la 701
    Entonces ninguna celda dice «Ambiental»

  @spec008 @corte1 @US-78
  Escenario: La cabecera y el bloque I traen la sección, el periodo y el instrumento
    Cuando el profesor descarga el R-17 de la carga de la 701
    Entonces el archivo se llama "R017_5643_701_2026-1_PROVISIONAL.xlsx"
    Y D8 dice "5643", D11 dice "701" e I11 dice "2026-1"
    Y B15 dice «Student Outcome (SO) 6»
    Y E17 dice «Portafolio 3» y G17 dice "Texto de prueba del Portafolio 3"

  @spec008 @corte1 @US-78
  Escenario: Las cifras del R-17 siguen la regla de la meta de Industrial
    Cuando el profesor descarga el R-17 de la carga de la 701
    Entonces M24 vale 8, M25 vale 26 y M26 vale 26 / 34
    Y E24 vale 0,765 con el formato 0.0 % y G24 vale 0,8
    Y H24 trae el texto de NO_LOGRADO, «El indicador aún no alcanza lo esperado, pero es una buena oportunidad para mejorar»

  @spec008 @corte1 @US-78
  Escenario: La franja provisional nombra el conjunto de Industrial
    Cuando el profesor descarga el R-17 de la carga de la 701
    Entonces B7 dice «R-17 PROVISIONAL. Las reglas de la carrera (conjunto R-2026-BORRADOR) aún no están aprobadas. No usar como evidencia oficial.»

  @spec008 @corte1 @US-78
  Escenario: La tabla de estudiantes trae SO, PI, código y nivel, sin nombres ni el profesor
    Cuando el profesor descarga el R-17 de la carga de la 701
    Entonces las filas 43 a 76 traen en B, C, E y F el SO 6, el PI 6.1, el código y el nivel de cada estudiante
    Y la columna D y la celda D10 quedan vacías, como fija BR-R17-07
    Y ninguna celda contiene una fórmula

  @spec008 @corte1 @US-78
  Escenario: Un PI sin descriptores de rúbrica no cambia el R-17
    Dado que IND-2026 tiene 0 filas en abet.rubrica_nivel
    Cuando el profesor descarga el R-17 de la carga de la 701
    Entonces la ruta 7 responde 200 con el mismo libro que con descriptores, porque abet_carga/r17.py no lee abet.rubrica_nivel

  @spec008 @corte1 @US-78
  Escenario: Otro profesor del curso no descarga el R-17 de la 701
    Dado "docente702@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando pide GET /api/cargas/{carga}/r17.xlsx de la carga de la 701
    Entonces recibe 403 con «La sección no está a su cargo.»

  @spec008 @corte1 @US-78
  Escenario: El SO y el PI de la ruta 12 salen del catálogo de Industrial y no del de Ambiental
    Dado el PI 6.1 y el SO 6 en AMB-2026 y en IND-2026 con textos inventados distintos en cada catálogo
    Cuando el profesor pide GET /api/resultados?periodo=2026-1
    Entonces el PI 6.1 trae el texto inventado de IND-2026
    Y el SO 6 trae el texto inventado de IND-2026
    Y la 701 trae logrados 26, calificados 34, pct_sobre_calificados 76.5, meta_pct 80.0 y en_meta falso

  @spec008 @corte1 @US-78 @delegado_a_vitest
  Escenario: La fila de P6 dice la cifra, la meta y el resultado con palabras
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" con "2026-1" elegido
    Y que la ruta 12 responde la 701 de "5643" con el PI 6.1 en 76,5 %, 26 de 34, meta 80 % y en_meta false
    Cuando el profesor abre P6
    Entonces ve «Periodo 2026-1.»
    Y la fila dice «6.1 · Sección 701 de 5643 · 76,5 % (26 de 34) · Debajo de la meta»
    Y la barra del logro tiene un aria-label que contiene «76,5 %» y «meta 80 %» (propuesta)

  @spec008 @corte1 @US-78 @delegado_a_vitest
  Escenario: Una sección que llega a la meta lo dice con palabras
    Dado una sesión de "docente702@example.invalid" con rol "PROFESOR" con "2026-1" elegido
    Y que la ruta 12 responde la 702 de "5643" con el PI 6.1 en 86,7 %, 26 de 30 y en_meta true
    Cuando el profesor abre P6
    Entonces la fila dice «En la meta»
