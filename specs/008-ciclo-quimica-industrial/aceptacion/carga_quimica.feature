# language: es
#
# Escenarios de aceptación de US-75, US-76 y US-77 de la spec 008-ciclo-quimica-industrial (épica EP-08,
# propuesta). El export de una sección de 5643 de 2026-1 se publica entero en Ingeniería Industrial (US-75, la
# parte a de C-03 con el escenario de la programación de C-43), los errores probables de la sala se rechazan
# sin mostrar notas ni códigos (US-76, la parte b de C-03 con la parte del Back de C-66) y P4 dice qué corregir
# en las filas rechazadas y en el aviso del puntaje máximo, sin remitir a Blackboard (US-77, C-05 corregida con
# la parte de pantalla de C-66).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid y códigos del rango
# 99. Ningún export nuevo entra a tests/datos_inventados/, porque los pasos los arman en memoria.
#
# Vocabulario de los pasos.
# - La base de los escenarios del Back es una base desechable de la spec 008 con V1_12 a V1_14, el plan de 5643
#   en 2026-1 con el PI 6.1 y db/datos/quimica_2026_1_inventado.sql. Corre en el clúster desechable, nunca en
#   localhost:5432.
# - El mismo archivo subido otra vez en la misma sección devuelve 200 con la constancia existente (BR-CARGA-09),
#   y 409 solo si está publicado en otra sección (BR-CARGA-10), como fija el veredicto CAMBIAR del crítico.
# - Los consejos de P4 viven en la tabla de J-43 de src/servicios/ayudas.ts, que suma los motivos RECHAZA_FILA
#   y el aviso PUNTAJE_MAXIMO_DISTINTO, y el texto de la carga sin filas aceptadas deja de decir «Corrija en
#   Blackboard» con un cambio fechado en la spec 007. El botón de reemplazo en P4 no entra (J-53, valor
#   provisional), y la guía enseña el reemplazo desde P5.
# - Los escenarios de pantalla los prueba Vitest en el Front y llevan @delegado_a_vitest.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: El export de Química General se publica en Ingeniería Industrial y sus errores se corrigen sin exponer datos
  Como profesor de una sección de 5643, quiero subir el export de mi sección y, si algo falla, leer qué corregir
  sin que se muestre una nota o un código, para tener mi R-17 sin llenarlo a mano.

  Antecedentes:
    Dado una base desechable de la spec 008 con el plan de 5643 en 2026-1 y los datos de quimica_2026_1_inventado.sql
    Y "docente701@example.invalid" tiene la sesión iniciada con rol "PROFESOR"

  @spec008 @corte1 @US-75
  Escenario: Un export de 34 filas con niveles de 1 a 4 queda PUBLICADA entero en Industrial
    Dado el export "gc_SINTETICO_20261_5643_701_fullgc_2026-07-15-00-00-00.xlsx" con la hoja "gc_SINTETICO_20261_5643_701_f"
    Y las columnas "Username" y "ABET SO6.1 [Total Pts: 4 Score] |9000061"
    Y 34 filas con 3 de nivel 1, 5 de nivel 2, 20 de nivel 3 y 6 de nivel 4
    Cuando el profesor sube el export en la sección 701
    Entonces la carga queda PUBLICADA con 34 de 34 filas aceptadas
    Y abet.carga.carrera_id es el de "IND" y su conjunto de reglas es R-2026-BORRADOR de "IND"
    Y abet.medicion gana 34 filas del PI 6.1 de IND-2026
    Y las consultas de control Q01, Q02, Q03, Q04, Q06, Q10, Q12 y Q13 devuelven 0 filas

  @spec008 @corte1 @US-75
  Escenario: La asignatura de cuatro cifras se lee también en el nombre de un export de texto
    Dado un export de texto "gc_SINTETICO_20261_5643_701_fullgc_2026-07-15-00-00-00.csv" sin hoja
    Cuando el profesor lo sube en la sección 701
    Entonces la carga queda PUBLICADA sin el aviso SECCION_SIN_DECLARAR

  @spec008 @corte1 @US-75
  Escenario: El export que arma el generador con la programación de la sección se publica sin rechazos
    Dado el CSV inventado de la programación con el curso_blackboard "SINTETICO_20261_5643_701" de la 701
    Y el export de la 701 que el generador de US-74 arma con esa programación
    Cuando el profesor lo sube en la sección 701
    Entonces la carga queda PUBLICADA con 0 filas rechazadas y sin avisos

  @spec008 @corte1 @US-75
  Escenario: Q21 detecta una sección cuyo curso de Blackboard declara otra sección
    Dado la sección 701 de 5643 en 2026-1 con el curso_blackboard "SINTETICO_20261_5643_702"
    Cuando corre la consulta de control Q21
    Entonces devuelve 1 fila que nombra la sección 701 de 5643 en 2026-1

  @spec008 @corte1 @US-76
  Escenario: El export de otra sección del curso se rechaza con el número de las dos
    Dado el export inventado de la sección 702 de "5643" en "2026-1"
    Cuando el profesor lo sube en la sección 701
    Entonces la carga queda RECHAZADA con SECCION_NO_COINCIDE y 0 filas leídas
    Y el mensaje es «El archivo corresponde a la sección 702 y usted eligió la 701. No se publicó.»
    Y abet.medicion no gana ninguna fila

  @spec008 @corte1 @US-76
  Esquema del escenario: Un nombre de columna que el lector no reconoce deja la carga sin el PI 6.1
    Dado el export inventado de la 701 con la columna "<encabezado>"
    Cuando el profesor lo sube en la sección 701
    Entonces la carga queda RECHAZADA con PI_DEL_PLAN_AUSENTE y el PI 6.1

    Ejemplos:
      | encabezado                         |
      | Portafolio 3 [Total Pts: 20 Score] |
      | 6.1 Portafolio                     |

  @spec008 @corte1 @US-76
  Escenario: La nota sobre 20 entre otras filas válidas publica solo los niveles
    Dado el export inventado de la 701 con "ABET SO6.1 [Total Pts: 20 Score] |9000061"
    Y 30 filas con notas de 10 a 20 y 4 filas con nivel 3
    Cuando el profesor lo sube en la sección 701
    Entonces la carga queda PUBLICADA con 4 de 34 filas aceptadas
    Y la constancia trae 30 rechazos NIVEL_FUERA_DE_ESCALA y el aviso PUNTAJE_MAXIMO_DISTINTO del PI 6.1
    Y ningún rechazo trae el valor de la celda

  @spec008 @corte1 @US-76
  Escenario: Un Excel con todas las notas sobre 20 queda RECHAZADA sin repetir las notas
    Dado el export inventado de la 701 con "ABET SO6.1 [Total Pts: 20 Score] |9000061" y las notas 17, 19 y 12
    Cuando el profesor lo sube en la sección 701
    Entonces la carga queda RECHAZADA con «Ninguna fila se pudo aceptar. La carga no se publicó.»
    Y la constancia trae 3 rechazos NIVEL_FUERA_DE_ESCALA y el aviso PUNTAJE_MAXIMO_DISTINTO
    Y ni la respuesta de la ruta 5 ni la constancia de la ruta 6 traen un campo valor ni valor_leido

  @spec008 @corte1 @US-76
  Escenario: Un nivel con medio punto se rechaza como no numérico
    Dado el export inventado de la 701 con una fila de nivel "3,5"
    Cuando el profesor lo sube en la sección 701
    Entonces esa fila queda rechazada con NIVEL_NO_NUMERICO

  @spec008 @corte1 @US-76
  Escenario: Un libro sin Username ni Student ID se rechaza entero
    Dado un libro inventado de la 701 con las columnas "Código" y "ABET SO6.1 [Total Pts: 4 Score] |9000061"
    Cuando el profesor lo sube en la sección 701
    Entonces la carga queda RECHAZADA con COLUMNA_CODIGO_AUSENTE

  @spec008 @corte1 @US-76
  Escenario: El mismo export subido dos veces en la misma sección devuelve la constancia existente
    Dado que la 701 ya tiene publicada la carga del export inventado de la 701
    Cuando el profesor sube otra vez el mismo archivo con otro nombre
    Entonces recibe 200 con la constancia de la carga existente
    Y abet.carga no gana ninguna fila

  @spec008 @corte1 @US-76
  Escenario: Los nombres de un libro con Last Name y First Name no llegan a la base
    Dado el export inventado de la 701 con las columnas "Last Name" y "First Name" y el apellido "Inventadoapellido"
    Cuando el profesor lo sube en la sección 701
    Entonces la carga queda PUBLICADA
    Y ninguna tabla del esquema abet trae "Inventadoapellido"
    Y la consulta de control Q04 devuelve 0 filas

  @spec008 @corte1 @US-76
  Escenario: El registro de la aplicación no trae códigos ni notas fuera de la huella del archivo
    Dado el export inventado de la 701 con "ABET SO6.1 [Total Pts: 20 Score] |9000061" y las notas 17, 19 y 12
    Cuando el profesor lo sube en la sección 701
    Entonces el registro de esa petición, sin contar el campo sha256, no trae ningún código de ocho cifras ni ninguna nota

  @spec008 @corte1 @US-77 @delegado_a_vitest
  Esquema del escenario: El consejo sigue al motivo de las filas rechazadas de una carga publicada
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" y la sección 701 de "5643" en "2026-1"
    Y que la ruta 6 responde la carga 31 PUBLICADA con 30 de 34 filas aceptadas y 4 rechazos <motivo>
    Cuando el profesor abre P4 de la carga 31
    Entonces ve «Qué corregir. <consejo>» (propuesta, J-43)
    Y la tabla de rechazos conserva su forma de hoy, sin valores de celda

    Ejemplos:
      | motivo                | consejo                                                                                                                              |
      | NIVEL_FUERA_DE_ESCALA | Algunas filas traen un valor fuera de 1 a 4. Si registró la nota sobre 20, conviértala al nivel de 1 a 4 de la rúbrica del curso.   |
      | NIVEL_NO_NUMERICO     | Algunas filas traen un nivel que no es un entero, como 3,5. Escriba un nivel entero de 1 a 4.                                       |
      | CODIGO_VACIO          | Algunas filas no traen el código del estudiante. Complete la columna Username o Student ID.                                          |
      | CODIGO_DUPLICADO      | Un mismo código aparece en dos filas. Deje una sola fila por estudiante.                                                             |
      | CODIGO_INVALIDO       | Algunos códigos no tienen 8 cifras. Revise la columna Username o Student ID.                                                         |

  @spec008 @corte1 @US-77 @delegado_a_vitest
  Escenario: El aviso del puntaje máximo se muestra antes de la constancia
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" y la sección 701 de "5643" en "2026-1"
    Y que la ruta 6 responde la carga 31 PUBLICADA con el aviso PUNTAJE_MAXIMO_DISTINTO del PI 6.1
    Cuando el profesor abre P4 de la carga 31
    Entonces ve arriba, en un aviso con role="status", «La columna del PI 6.1 no declara un puntaje máximo de 4. Revise que cada celda sea el nivel de 1 a 4 y no la nota del instrumento.» (propuesta)

  @spec008 @corte1 @US-77 @delegado_a_vitest
  Escenario: Una carga rechazada sin filas aceptadas remite a la tabla sin nombrar Blackboard
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" y la sección 701 de "5643" en "2026-1"
    Y que la ruta 6 responde la carga 8 RECHAZADA con 3 filas leídas, 0 aceptadas y 3 rechazos NIVEL_FUERA_DE_ESCALA
    Cuando el profesor abre P4 de la carga 8
    Entonces ve «Qué corregir. Corrija el archivo en cada fila de la tabla de rechazos y suba el archivo nuevo. Si recibió el export de la Oficina de Calidad, pídale uno corregido.» (propuesta)
    Y ningún texto de P4 dice «Corrija en Blackboard»
    Y cada celda de la tabla de rechazos es una fila, un PI, un motivo o un efecto, y ninguna trae un valor leído

  @spec008 @corte1 @US-77 @delegado_a_vitest
  Escenario: Una carga publicada sin rechazos ni avisos no muestra consejo
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" y la sección 701 de "5643" en "2026-1"
    Y que la ruta 6 responde la carga 31 PUBLICADA con 34 de 34 filas aceptadas y sin avisos
    Cuando el profesor abre P4 de la carga 31
    Entonces no ve «Qué corregir.»

  @spec008 @corte1 @US-77 @delegado_a_vitest
  Escenario: Un motivo de fila desconocido no muestra consejo y la prueba recorre los motivos del contrato
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" y la sección 701 de "5643" en "2026-1"
    Y que la ruta 6 responde la carga 31 PUBLICADA con un rechazo de fila de motivo "MOTIVO_NUEVO"
    Cuando el profesor abre P4 de la carga 31
    Entonces no ve «Qué corregir.»
    Y una prueba que recorre los motivos RECHAZA_FILA de la sección 6 del contrato exige un consejo para cada uno

  @spec008 @corte1 @US-77 @delegado_a_vitest
  Escenario: P4 de una carga publicada remite al reemplazo de P5
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" y la sección 701 de "5643" en "2026-1"
    Y que la ruta 6 responde la carga 31 PUBLICADA con 4 rechazos de fila
    Cuando el profesor abre P4 de la carga 31
    Entonces debajo del consejo ve «Para cambiar esta carga, use «Reemplazar carga» en Cargas.» (propuesta, J-53)
    Y P4 no muestra un botón de reemplazo
