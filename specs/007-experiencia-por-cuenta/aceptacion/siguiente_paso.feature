# language: es
#
# Escenarios de aceptación de US-59 de la spec 007-experiencia-por-cuenta (épica EP-07, propuesta, etapa A).
# P2 «Mis secciones» del profesor dice en una línea aparte lo que falta en cada sección. La historia fusiona
# las candidatas C-P01 y C-T02 y la línea de la lista vacía de C-T03 (revision-historias.md).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid. Ninguna
# contraseña aparece escrita aquí.
#
# Vocabulario de los pasos.
# - La ruta 4 es GET /api/secciones y la ruta 8 es GET /api/cargas, del contrato del Front (secciones 5 y 7).
#   Ninguna de las dos cambia. P2 pide la ruta 8 sin seccion_id, una sola vez, y la ruta 8 entrega las cargas
#   de la más reciente a la más antigua (constancia.resumenes, ORDER BY iniciada_en DESC, carga_id DESC).
# - Los textos de hoy («Sin carga», «Publicada, 11 de 11 filas aceptadas» y «La carrera aún no registra el
#   plan de medición de esta sección») no cambian, porque los citan acceso.feature (línea 131) y
#   varias_secciones.feature (línea 78) de la spec 001. La línea nueva va debajo, en un párrafo propio.
# - Una sección «con la última carga rechazada» es una sección en SIN_CARGA para la ruta 4 que tiene en la
#   ruta 8 al menos una carga RECHAZADA (J-45).
# - Todos los escenarios se prueban con Vitest en el Front y aquí quedan como criterio escrito. Todos llevan
#   @delegado_a_vitest.
# - Los Antecedentes escriben la sesión con «una sesión de "…" con rol "…"», un texto que la expresión
#   _sesion_iniciada de tests/aceptacion/pasos/conftest.py no captura, así que su paso solo registra la prueba
#   de Vitest y no abre la base.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: P2 dice al profesor lo que falta en cada sección
  Como profesor, quiero ver en cada sección de P2 lo que falta hacer, para registrar la medición en la
  semana 15 sin abrir cada pantalla ni volver al material de la capacitación.

  Antecedentes:
    Dado una sesión de "docente410@example.invalid" con rol "PROFESOR" y la sección 410 de "450002" en "2026-2"

  @US-59 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Esquema del escenario: La línea de lo que falta sale del estado de la sección
    Dado que la ruta 4 responde la sección 410 con tiene_plan "<plan>" y estado "<estado>"
    Y que la ruta 8 responde para la sección 410 las cargas en estado "<cargas>"
    Cuando el profesor abre P2 «Mis secciones»
    Entonces la fila de la sección 410 conserva el texto «<texto_actual>»
    Y debajo dice «<lo_que_falta>» (propuesta)

    Ejemplos:
      | plan  | estado    | cargas    | texto_actual                                                   | lo_que_falta                                                                                   |
      | true  | SIN_CARGA | ninguna   | Sin carga                                                      | Falta subir el export de Blackboard de esta sección.                                           |
      | true  | SIN_CARGA | RECHAZADA | Sin carga                                                      | La última carga se rechazó y no se publicó. Falta subir un export corregido.                   |
      | true  | PUBLICADA | PUBLICADA | Publicada, 11 de 11 filas aceptadas                            | Revise el resultado de la carga para completar lo que falte y descargar el R-17.               |
      | false | SIN_CARGA | ninguna   | La carrera aún no registra el plan de medición de esta sección | Por ahora no hay nada que hacer. La Coordinación de la carrera registra el plan de medición. |

  @US-59 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: El botón de la fila anuncia lo que falta y, desactivado, su motivo
    Dado que la ruta 4 responde la sección 410 de "450002" en estado "SIN_CARGA" con tiene_plan "true" y la sección 410 de "450010" con tiene_plan "false"
    Y que la ruta 8 responde una lista vacía
    Cuando el profesor abre P2 «Mis secciones»
    Entonces el botón «Subir export» de la sección de 450002 tiene aria-describedby hacia la línea «Falta subir el export de Blackboard de esta sección.»
    Y el botón «Subir export» desactivado de la sección de 450010 tiene aria-describedby hacia el texto «La carrera aún no registra el plan de medición de esta sección»

  @US-59 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: «Ver por qué se rechazó» abre P4 de la carga rechazada más reciente
    Dado que la ruta 4 responde la sección 410 con tiene_plan "true", estado "SIN_CARGA" y carga_id null
    Y que la ruta 8 responde para la sección 410 las cargas 9 y 8, las dos en estado "RECHAZADA", con la 9 primero
    Cuando el profesor pulsa «Ver por qué se rechazó» (propuesta) en la fila de la sección 410
    Entonces P4 muestra la constancia de la carga 9
    Y la fila de la sección 410 conserva el botón «Subir export» activo

  @US-59 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: Si la ruta 8 falla, P2 sigue con la ruta 4 y no muestra error
    Dado que la ruta 4 responde la sección 410 con tiene_plan "true" y estado "SIN_CARGA"
    Y que la ruta 8 responde 500
    Cuando el profesor abre P2 «Mis secciones»
    Entonces la fila de la sección 410 dice «Falta subir el export de Blackboard de esta sección.» (propuesta)
    Y P2 no muestra ningún mensaje de error de la ruta 8
    Y la fila no ofrece «Ver por qué se rechazó»

  @US-59 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: Sin secciones asignadas, P2 dice a quién acudir y no pide la ruta 8
    Dado que la ruta 4 responde una lista vacía
    Cuando el profesor abre P2 «Mis secciones»
    Entonces ve «No tiene secciones asignadas en este periodo.»
    Y debajo ve «Si dicta una sección con medición ABET en este periodo, escriba a la Coordinación de la carrera.» (propuesta, D-46)
    Y P2 no pide la ruta 8

  @US-59 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: La coordinación no recibe las líneas del profesor
    Dado una sesión de "coordinacion@example.invalid" con rol "COORDINADOR" en lugar de la del profesor
    Y que la ruta 4 responde la sección 410 de "450002" en estado "SIN_CARGA" con tiene_plan "true"
    Cuando abre P2
    Entonces ninguna fila dice «Falta subir el export de Blackboard de esta sección.»
    Y P2 no pide la ruta 8
