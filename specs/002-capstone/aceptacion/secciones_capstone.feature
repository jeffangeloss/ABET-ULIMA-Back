# language: es
#
# Escenarios de aceptación del estado de proyectos en la lista de secciones (spec 002, historia US-23).
# Todos los datos son inventados. Las secciones 422, 423 y 424 de 450024 y la 425 de 450026 existen solo en
# los datos de la prueba, asignadas a docente420@example.invalid, y no en db/datos/periodo_2026_2_inventado.sql.
#
# Vocabulario de los pasos.
# - «pedir sus secciones» es GET /api/secciones?periodo=2026-2 con la cookie abet_sesion del usuario.
# - Los campos nuevos (tipo_curso, proyectos_estado, carga_proyecto_id, estudiantes_con_proyecto y
#   estudiantes_en_export) se suman a los de la spec 001 sin quitar ninguno.
# - Lo marcado «(propuesta)» no está fijado y lo decide la revisión de la spec.

Característica: Estado de los proyectos en Mis secciones
  Como profesor de varias secciones Capstone, quiero ver en mi lista de secciones si cada una tiene su
  export, su plantilla y cuántos estudiantes tienen proyecto, para saber qué me falta subir.

  Antecedentes:
    Dado una base PostgreSQL 16 desechable con las migraciones V1_01 a V1_10 y los datos de db/datos/periodo_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2"
    Y la asignatura "450024" con tipo_curso "CAPSTONE" y la asignatura "450002" con tipo_curso "CARRERA" en "AMB-2026"

  # US-23: Ver el estado de proyectos de mis secciones

  @US-23 @corte1
  Esquema del escenario: El estado de proyectos refleja la situación de cada sección
    Dado que "<usuario>" tiene la sesión iniciada con rol "PROFESOR" y dicta la sección <seccion> de "<asignatura>" en "2026-2" con <situacion>
    Cuando pide sus secciones
    Entonces la sección <seccion> trae tipo_curso "<tipo>" y proyectos_estado "<estado>"
    Y la respuesta no trae ningún dato de secciones que ese profesor no dicta

    Ejemplos:
      | usuario                    | seccion | asignatura | situacion                                     | tipo     | estado     |
      | docente420@example.invalid | 420     | 450024     | el export publicado y la plantilla publicada  | CAPSTONE | PUBLICADA  |
      | docente420@example.invalid | 422     | 450024     | el export publicado y ninguna plantilla       | CAPSTONE | PENDIENTE  |
      | docente420@example.invalid | 423     | 450024     | ninguna carga                                 | CAPSTONE | SIN_EXPORT |
      | docente420@example.invalid | 424     | 450024     | el export publicado y una plantilla solo RECHAZADA | CAPSTONE | PENDIENTE  |
      | docente410@example.invalid | 410     | 450002     | el export publicado                           | CARRERA  | NO_APLICA  |

  @US-23 @corte1
  Escenario: La sección con plantilla completa trae sus conteos
    Dado que "docente420@example.invalid" tiene la sesión iniciada y la 420 tiene el export publicado y la plantilla publicada con 11 proyectos
    Cuando pide sus secciones
    Entonces la sección 420 trae carga_proyecto_id igual al de la subida, estudiantes_con_proyecto 11 y estudiantes_en_export 11
    Y conserva los campos de la spec 001, entre ellos estado "PUBLICADA" y filas_aceptadas 11

  @US-23 @corte1
  Escenario: La sección con plantilla incompleta muestra cuántos faltan
    Dado que "docente420@example.invalid" tiene la sesión iniciada y la 420 tiene el export publicado y una plantilla publicada sin las filas de 99000110 y 99000111
    Cuando pide sus secciones
    Entonces la sección 420 trae proyectos_estado "PUBLICADA", estudiantes_con_proyecto 9 y estudiantes_en_export 11

  @US-23 @corte1
  Escenario: Las secciones sin datos de proyecto traen los conteos nulos
    Dado que "docente420@example.invalid" tiene la sesión iniciada y la 423 no tiene ninguna carga
    Cuando pide sus secciones
    Entonces la sección 423 trae carga_proyecto_id, estudiantes_con_proyecto y estudiantes_en_export nulos

  @US-23 @corte1
  Escenario: El coordinador ve el estado de proyectos de toda la carrera
    Dado que "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Y que la 420 tiene el export publicado y la plantilla publicada y la 410 tiene su export publicado
    Cuando pide sus secciones
    Entonces la respuesta trae la 420 con proyectos_estado "PUBLICADA" y la 410 con proyectos_estado "NO_APLICA"

  @US-23 @corte1
  Escenario: Una sección sin plan de medición no tiene tipo de curso
    Dado que "docente420@example.invalid" tiene la sesión iniciada y dicta la sección 425 de "450026" en "2026-2"
    Y que abet.plan_medicion no tiene filas de "450026" en "2026-2"
    Cuando pide sus secciones
    Entonces la sección 425 trae tipo_curso nulo y proyectos_estado "NO_APLICA" (propuesta)
    Y carga_proyecto_id, estudiantes_con_proyecto y estudiantes_en_export nulos
