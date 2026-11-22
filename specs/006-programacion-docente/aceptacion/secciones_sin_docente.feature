# language: es
#
# Escenarios de aceptación de la consulta informativa de las secciones sin profesor activo, de la historia de
# usuario (user story, US) US-58 de la spec 006-programacion-docente (épica EP-06, propuesta). Después de
# cargar la programación docente, la Coordinación de Ambiental necesita saber qué secciones con plan de
# medición no tienen ningún profesor que pueda subir su export en la semana 15.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid.
#
# Vocabulario de los pasos (propuesta).
# - «la consulta» es db/plataforma/neon/secciones_sin_docente.sql, corrida con psql -X -v ON_ERROR_STOP=1 y
#   -v periodo=2026-2 por el usuario dueño de la base desechable. En Neon la corre abet_respaldo, de solo
#   lectura, desde el Windows de Jefferson.
# - «el guion» y «el archivo base» son los de programacion_docente.feature, con la 410 y la 411 de 450002 de
#   docente410@example.invalid y docente411@example.invalid.
# - La consulta es informativa y no es un control de db/pruebas/pruebas.sql, porque la base de ese archivo
#   tiene a propósito dos secciones 301 sin profesor (casos de Q06 y Q07).
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Secciones con plan de medición y sin profesor activo
  Como coordinación de la carrera, quiero listar las secciones del periodo con plan de medición que no tienen
  ningún profesor activo para pedir la asignación que falta antes de que los profesores registren.

  Antecedentes:
    Dado una base desechable de partida de la spec 006, en PostgreSQL 18 con las migraciones V1_01 a V1_11, la vigencia de AMB-2026 en 2026-2 y el plan de medición de 450002 y 450010, sin secciones ni profesores
    Y "coordinacion@example.invalid" activo con rol "COORDINADOR" y sin secciones en acceso.docente_seccion
    Y que el administrador corrió el guion con el archivo base y con --aplicar

  # US-58: Saber qué secciones quedan sin profesor antes de la semana 15

  @US-58 @spec006 @corte1
  Esquema del escenario: La consulta encuentra la sección sin profesor activo
    Dado la 412 de "450010" en "2026-2" <asignacion>, sembrada por el dueño de la base
    Cuando corre la consulta con -v periodo=2026-2
    Entonces la consulta lista la 412 de "450010" y ninguna sección de "450002"
    Y la cantidad final es 1

    Ejemplos:
      | asignacion                                                                       |
      | sin ninguna asignación                                                           |
      | asignada solo a "docente.varias@example.invalid", con rol "PROFESOR" y activo falso |
      | asignada solo a "coordinacion@example.invalid"                                   |

  @US-58 @spec006 @corte1
  Escenario: Una sección de una asignatura sin plan de medición no aparece
    Dado la 413 de "450020" en "2026-2" sin ninguna asignación, sembrada por el dueño de la base
    Y que la base no tiene plan de medición de "450020" en "2026-2"
    Cuando corre la consulta con -v periodo=2026-2
    Entonces la cantidad final es 0

  @US-58 @spec006 @corte1
  Escenario: La consulta no escribe
    Cuando corre la consulta con -v periodo=2026-2
    Entonces la sesión de la consulta queda en solo lectura antes de la primera consulta
    Y ninguna tabla de los esquemas abet y acceso cambia su número de filas

  @US-58 @spec006 @corte1
  Escenario: La consulta pide el periodo
    Cuando corre la consulta sin -v periodo
    Entonces psql termina con un error antes de consultar
    Y la salida dice «Falta el periodo, por ejemplo -v periodo=2026-2.»
