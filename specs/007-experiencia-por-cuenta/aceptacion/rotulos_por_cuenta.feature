# language: es
#
# Escenarios de aceptación de US-63 de la spec 007-experiencia-por-cuenta (épica EP-07, propuesta, etapa A).
# La cabecera y los textos propios del Front hablan de la carrera a la coordinación y de sus secciones al
# profesor, y la cabecera marca la pantalla actual. La historia toma la parte (b) de la candidata C-C03 y el
# menú con aria-current de C-T06 (revision-historias.md). La entrada de la coordinación a P7 es de US-65.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid.
#
# Vocabulario de los pasos.
# - El rol sale de GET /api/sesion (ruta 2), en Usuario.rol de src/servicios/tipos.ts, sin ruta nueva.
# - Los textos del profesor no cambian, porque los citan resultados.feature de la spec 004 (líneas 179 y 182) y
#   las pruebas de Vitest del Front.
# - Todos los escenarios se prueban con Vitest en el Front y llevan @delegado_a_vitest. La sesión se escribe
#   «una sesión de "…" con rol "…"», un texto que la expresión _sesion_iniciada de
#   tests/aceptacion/pasos/conftest.py no captura, así que su paso solo registra la prueba de Vitest.
# - El esquema del menú lleva la etapa en cada bloque de Ejemplos, porque la fila de P7 es de la etapa B.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Cada cuenta lee rótulos de su rol y sabe en qué pantalla está
  Como coordinación de la carrera, quiero leer rótulos que hablan de la carrera y no de secciones propias, para
  que la capacitación de la semana 14 y el seguimiento del registro no muestren textos de otra cuenta.

  @US-63 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Esquema del escenario: La cabecera nombra lo que ve cada cuenta
    Dado una sesión de "<correo>" con rol "<rol>"
    Cuando mira la cabecera
    Entonces ve los botones «<secciones>», «Cargas» y «<logros>»
    Y P2 lleva el título «<secciones>»

    Ejemplos:
      | correo                       | rol         | secciones               | logros                               |
      | docente410@example.invalid   | PROFESOR    | Mis secciones           | Ver mis logros por SO                |
      | coordinacion@example.invalid | COORDINADOR | Secciones de la carrera | Ver los logros por SO de la carrera |

  @US-63 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Esquema del escenario: Una lista vacía se explica según la cuenta
    Dado una sesión con rol "<rol>" y la ruta de <pantalla> con una lista vacía
    Cuando abre <pantalla>
    Entonces ve «<texto>»

    Ejemplos:
      | rol         | pantalla | texto                                          |
      | PROFESOR    | P2       | No tiene secciones asignadas en este periodo.  |
      | PROFESOR    | P5       | No tiene secciones asignadas en este periodo.  |
      | PROFESOR    | P6       | No tiene secciones asignadas en este periodo.  |
      | COORDINADOR | P2       | La carrera no tiene secciones en este periodo. |
      | COORDINADOR | P5       | La carrera no tiene secciones en este periodo. |
      | COORDINADOR | P6       | La carrera no tiene secciones en este periodo. |

  @US-63 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Esquema del escenario: El aviso de espera de P6 habla de la cuenta que lo lee
    Dado una sesión con rol "<rol>" y la ruta 12 sin responder todavía
    Cuando abre P6
    Entonces ve «<espera>»

    Ejemplos:
      | rol         | espera                              |
      | PROFESOR    | Cargando sus logros…                |
      | COORDINADOR | Cargando los logros de la carrera…  |

  @US-63 @spec007 @corte1 @delegado_a_vitest
  Esquema del escenario: El menú marca la pantalla actual
    Dado una sesión de "<correo>" con rol "<rol>"
    Cuando abre <pantalla>
    Entonces la cabecera es un nav con aria-label «Menú principal» (propuesta)
    Y <marca>

    @etapa_a
    Ejemplos: Etapa A
      | correo                       | rol         | pantalla                        | marca                                                                |
      | docente410@example.invalid   | PROFESOR    | P2 «Mis secciones»              | solo el botón «Mis secciones» lleva aria-current="page"              |
      | docente410@example.invalid   | PROFESOR    | P5 «Cargas»                     | solo el botón «Cargas» lleva aria-current="page"                     |
      | docente410@example.invalid   | PROFESOR    | P6 «Mis logros por SO»          | solo el botón «Ver mis logros por SO» lleva aria-current="page"      |
      | docente410@example.invalid   | PROFESOR    | P3 de la sección 410 de 450002  | ningún botón lleva aria-current                                      |
      | docente410@example.invalid   | PROFESOR    | P4 de la carga 7                | ningún botón lleva aria-current                                      |
      | coordinacion@example.invalid | COORDINADOR | P2 «Secciones de la carrera»    | solo el botón «Secciones de la carrera» lleva aria-current="page"    |

    @etapa_b
    Ejemplos: Etapa B
      | correo                       | rol         | pantalla                        | marca                                                                |
      | coordinacion@example.invalid | COORDINADOR | P7 «Avance del registro»        | solo el botón «Avance del registro» lleva aria-current="page"        |
