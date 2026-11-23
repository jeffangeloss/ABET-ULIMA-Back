# language: es
#
# Escenarios de aceptación de US-61 y US-62 de la spec 007-experiencia-por-cuenta (épica EP-07, propuesta,
# etapa A). P4 de una carga rechazada dice qué corregir en Blackboard (US-61, candidata C-P03 corregida), y
# P4 y P3 dejan de afirmar algo falso sobre la carga publicada de la sección (US-62, candidata C-P05 en su
# versión mínima). Las dos historias tocan solo la rama de P4 de una carga que no está PUBLICADA y el párrafo
# del modo reemplazo de P3, y no tocan las secciones «Cómo va su sección» ni «Análisis por indicador» que la
# spec 005 agrega a P4.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid.
#
# Vocabulario de los pasos.
# - La ruta 6 es GET /api/cargas/{carga_id} y la ruta 9 es POST /api/secciones/{seccion_id}/cargas?reemplaza=
#   {carga_id}, del contrato del Front (secciones 6 y 7). Ninguna cambia.
# - Los motivos RECHAZA_CARGA son los de BR-CARGA-11 a BR-CARGA-13 y BR-CARGA-16 (contrato, sección 6). El
#   texto «Qué corregir» vive en una tabla del Front por motivo (J-43), y el mensaje de la API se muestra sin
#   reescribir, como hoy (Mensaje.tsx).
# - La línea «0 filas leídas, 0 aceptadas y 0 rechazadas» y la constancia completa no cambian en esta spec.
# - Todos los escenarios se prueban con Vitest en el Front y llevan @delegado_a_vitest.
# - Los Antecedentes escriben las cuentas con «… con rol "…"», un texto que la expresión _sesion_iniciada de
#   tests/aceptacion/pasos/conftest.py no captura, así que su paso solo registra la prueba de Vitest y no abre
#   la base. «El profesor» es docente410@example.invalid y «el coordinador» es coordinacion@example.invalid.
# - permisos.puede_subir() no deja al coordinador una carga nueva, así que el consejo de SECCION_NO_COINCIDE que
#   él lee lo remite al profesor de la sección (propuesta, J-43).
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: P4 de una carga rechazada dice qué corregir y no afirma nada falso
  Como profesor, quiero que P4 de una carga rechazada me diga qué corregir en Blackboard y que no me haga creer
  que perdí mi carga publicada, para subir un export válido sin adivinar durante el registro.

  Antecedentes:
    Dado una sesión de "docente410@example.invalid" con rol "PROFESOR" y la sección 410 de "450002" en "2026-2"
    Y la cuenta "coordinacion@example.invalid" con rol "COORDINADOR", que abre P4 cuando el escenario nombra al coordinador

  @US-61 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Esquema del escenario: Cada motivo de rechazo de toda la carga trae su forma de corregir
    Dado que la ruta 6 responde la carga 8 de la sección 410 de "450002" en "2026-2" en estado "RECHAZADA" con filas_leidas 0 y un rechazo RECHAZA_CARGA con motivo "<motivo>" y pi "<pi>"
    Cuando <cuenta> abre P4 de la carga 8
    Entonces P4 muestra el mensaje de la API sin cambios
    Y debajo muestra «Qué corregir. <corregir>» (propuesta, J-43)
    Y P4 conserva la línea «0 filas leídas, 0 aceptadas y 0 rechazadas»

    Ejemplos:
      | cuenta          | motivo                 | pi   | corregir                                                                                                                                      |
      | el profesor     | PI_DEL_PLAN_AUSENTE    | 5.2  | Revise en Blackboard que cada PI del plan de esta sección tenga su columna, y cree o renombre la del PI 5.2 como ABET SO5.2. Después exporte otra vez y suba el archivo nuevo. |
      | el profesor     | PI_REPETIDO            | 5.1  | Deje en Blackboard una sola columna del PI 5.1, exporte otra vez y suba el archivo nuevo.                                                      |
      | el profesor     | COLUMNA_CODIGO_AUSENTE | null | Exporte otra vez el Centro de calificaciones completo, que trae la columna Username, y suba ese archivo.                                       |
      | el profesor     | ARCHIVO_SIN_FILAS      | null | Exporte otra vez el Centro de calificaciones de la sección con sus estudiantes y suba ese archivo.                                             |
      | el profesor     | SIN_CALIFICACIONES     | null | Registre en Blackboard el nivel de cada estudiante en las columnas de los PI del plan, exporte otra vez y suba el archivo nuevo.                |
      | el profesor     | SECCION_NO_COINCIDE    | null | Exporte el Centro de calificaciones de 450002, sección 410, o suba este archivo en la sección que le corresponde.                             |
      | el coordinador  | SECCION_NO_COINCIDE    | null | El archivo no es de 450002, sección 410. Pida al profesor de esa sección que exporte su Centro de calificaciones y lo suba otra vez.           |
      | el profesor     | PERIODO_NO_COINCIDE    | null | Exporte el Centro de calificaciones del curso de 2026-2 y suba ese archivo.                                                                    |

  @US-61 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: Si ninguna fila se acepta, P4 remite a la tabla de rechazos y conserva los conteos
    Dado que la ruta 6 responde la carga 8 en estado "RECHAZADA" con 11 filas leídas, 0 aceptadas y 11 rechazadas por NIVEL_FUERA_DE_ESCALA y sin ningún rechazo RECHAZA_CARGA
    Cuando el profesor abre P4 de la carga 8
    Entonces P4 muestra «11 filas leídas, 0 aceptadas y 11 rechazadas»
    Y muestra «Qué corregir. Corrija en Blackboard cada fila de la tabla de rechazos, exporte otra vez y suba el archivo nuevo.» (propuesta, J-43)

  @US-61 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: Un motivo que el Front no conoce muestra solo el mensaje de la API
    Dado que la ruta 6 responde la carga 8 en estado "RECHAZADA" con un rechazo RECHAZA_CARGA con motivo "MOTIVO_NUEVO"
    Cuando el profesor abre P4 de la carga 8
    Entonces P4 muestra el mensaje de la API sin cambios
    Y P4 no muestra ningún texto que empieza con «Qué corregir»

  @US-61 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: Una carga publicada no muestra «Qué corregir»
    Dado que la ruta 6 responde la carga 7 en estado "PUBLICADA" con 11 filas leídas, 10 aceptadas y 1 rechazada
    Cuando el profesor abre P4 de la carga 7
    Entonces P4 no muestra ningún texto que empieza con «Qué corregir»

  @US-62 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Esquema del escenario: Una carga sin R-17 lo dice sin afirmar nada sobre la sección
    Dado que la ruta 6 responde la carga 12 en estado "<estado>", con reemplaza_carga_id null y reemplazada_por null
    Cuando el profesor abre P4 de la carga 12
    Entonces P4 muestra «Esta carga no tiene R-17.» (propuesta)
    Y P4 no muestra «No hay una carga publicada para esta sección»
    Y P4 no ofrece «Descargar R-17»

    Ejemplos:
      | estado      |
      | RECHAZADA   |
      | EN_CURSO    |
      | REEMPLAZADA |

  @US-62 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: Un reemplazo rechazado no dice que la sección quedó sin carga publicada
    Dado que la sección 410 tiene la carga 7 en estado "PUBLICADA"
    Y que la ruta 9 con reemplaza 7 responde 201 con la carga 12 en estado "RECHAZADA", reemplaza_carga_id null y el motivo "PI_DEL_PLAN_AUSENTE"
    Cuando P3 pasa a P4 de la carga 12
    Entonces P4 muestra «Esta carga no tiene R-17.» (propuesta)
    Y P4 no muestra «No hay una carga publicada para esta sección»

  @US-62 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: Una carga reemplazada con sucesora conocida conserva su texto de hoy
    Dado que la ruta 6 responde la carga 7 en estado "REEMPLAZADA" con reemplazada_por 11
    Cuando el profesor abre P4 de la carga 7
    Entonces P4 muestra «La carga 11 la reemplaza, así que esta carga no tiene R-17.»
    Y P4 no muestra «Esta carga no tiene R-17.»

  @US-62 @spec007 @corte1 @etapa_a @delegado_a_vitest
  Escenario: P3 en modo reemplazo dice que la carga publicada no se pierde
    Dado que la sección 410 tiene la carga 7 en estado "PUBLICADA"
    Cuando el profesor abre P3 desde «Reemplazar carga» de la carga 7 en P5
    Entonces P3 conserva el párrafo «Reemplaza a la carga 7, la publicada de esta sección.»
    Y en un párrafo propio dice «Si la carga nueva queda rechazada, la carga 7 sigue publicada.» (propuesta)
