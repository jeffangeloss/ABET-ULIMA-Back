# language: es
#
# Escenarios de aceptación de la base de Capstone (spec 002, historias US-01, US-02 y US-24).
# Todos los datos son inventados. Los códigos de estudiante empiezan con 99, los correos usan el dominio
# reservado example.invalid y los RUC empiezan con 20999, cumplen el dígito verificador módulo 11 y no
# corresponden a ninguna organización real.
#
# Vocabulario de los pasos.
# - «la base migrada hasta V1_10» es un PostgreSQL 16 desechable con V1_01 a V1_10 y las vistas R__
#   aplicadas con psql, como db/pruebas/correr_pruebas.sh, más db/datos/periodo_2026_2_inventado.sql.
# - «la sección 420 coherente» es la sección 420 de "450024" en "2026-2" con la carga PUBLICADA del export
#   inventado (99000101 a 99000111, PI 1.1, 1.2 y 1.3) y la subida de plantilla PUBLICADA con 11 filas de
#   abet.proyecto_estudiante en 4 grupos, armadas por db/pruebas/datos_sinteticos.sql.
# - Cada anomalía se arma en una transacción que se deshace al final, como los sondeos de Q06 a Q14.
# - Lo marcado «(propuesta)» no está fijado y lo decide la revisión de la spec.

Característica: Base de Capstone con el tipo de curso, las tablas de proyecto y sus controles
  Como administrador técnico de Ingeniería Ambiental, quiero que la base distinga las asignaturas Capstone,
  guarde los datos de proyecto con privilegio mínimo y los vigile con consultas de control, para que la
  tabla maestra y el R-17 de Capstone salgan de datos coherentes.

  # US-01: Marcar las asignaturas Capstone en el plan de estudios

  @US-01 @corte1
  Escenario: V1_10 deja todas las asignaturas como de carrera
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09 y las vistas R__
    Cuando se aplica V1_10 con psql
    Entonces abet.plan_estudios tiene la columna tipo_curso NOT NULL con valor por omisión "CARRERA"
    Y abet.plan_estudios sigue con 53 filas en la versión "AMB-2026"
    Y ninguna fila de abet.plan_estudios tiene tipo_curso distinto de "CARRERA"
    Y las consultas de control Q01 a Q14 devuelven 0 filas

  @US-01 @corte1
  Esquema del escenario: Solo se aceptan los dos tipos de curso
    Dado la base migrada hasta V1_10
    Cuando el administrador técnico fija tipo_curso "<tipo>" en la fila de "450024" de "AMB-2026"
    Entonces la operación <resultado>

    Ejemplos:
      | tipo     | resultado                                                       |
      | CAPSTONE | termina bien                                                    |
      | CARRERA  | termina bien                                                    |
      | TESIS    | falla por ck_plan_estudios_tipo_curso y no cambia ninguna fila  |

  @US-01 @corte1
  Escenario: La semilla inventada marca 450024 y 450026 como Capstone con valor provisional
    Dado la base migrada hasta V1_09 y V1_10 sin datos del periodo
    Cuando el administrador técnico ejecuta db/datos/periodo_2026_2_inventado.sql
    Entonces abet.plan_estudios tiene tipo_curso "CAPSTONE" solo en "450024" y "450026" de "AMB-2026"
    Y abet.seccion tiene las secciones 420 y 421 de "450024" en "2026-2"
    Y abet.plan_medicion tiene 3 filas de "450024" en "2026-2" con los PI "1.1", "1.2" y "1.3"
    Y el script trae el comentario "valor provisional de D-14" junto a la marca

  @US-01 @corte1
  Escenario: V1_10 amplía el tipo de fuente y crea las tablas de proyecto
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09 y la carga PUBLICADA de la 410 de db/pruebas/datos_sinteticos.sql
    Cuando se aplica V1_10 con psql
    Entonces abet.archivo_origen.tipo_fuente es varchar(20) y ck_archivo_origen_tipo admite "BLACKBOARD_EXPORT", "R17_HISTORICO" y "PLANTILLA_PROYECTOS"
    Y el esquema abet tiene las tablas carga_proyecto, proyecto_estudiante y rechazo_proyecto
    Y la carga de la 410 sigue PUBLICADA y abet.v_tabla_maestra_pi devuelve las mismas 33 filas
    Y un INSERT en abet.archivo_origen con tipo_fuente "OTRO" falla por ck_archivo_origen_tipo

  # US-02: Dar a abet_app solo los permisos de la carga de proyectos

  @US-02 @corte1
  Escenario: abet_app publica una subida de plantilla
    Dado la base migrada hasta V1_10, el rol abet_app creado con db/plataforma/neon/crear_rol_app.sql y la carga PUBLICADA de la 420
    Cuando abet_app inserta en una sola transacción el archivo de la plantilla, la subida, 11 filas de abet.proyecto_estudiante y el aviso, y deja la subida PUBLICADA con 11 / 11 / 0 y terminada_en no nulo
    Entonces la transacción confirma
    Y abet_app lee abet.carga_proyecto, abet.proyecto_estudiante, abet.rechazo_proyecto y abet.v_tabla_maestra_capstone sin error de permisos

  @US-02 @corte1
  Esquema del escenario: abet_app no modifica ni borra los datos de proyecto
    Dado una conexión abet_app y la sección 420 coherente
    Cuando abet_app ejecuta <orden>
    Entonces PostgreSQL responde «permission denied for table <tabla>»
    Y abet.proyecto_estudiante sigue con 11 filas de la 420

    Ejemplos:
      | orden                                                   | tabla               |
      | UPDATE abet.proyecto_estudiante SET titulo = 'Otro'     | proyecto_estudiante |
      | DELETE FROM abet.proyecto_estudiante                    | proyecto_estudiante |
      | TRUNCATE abet.proyecto_estudiante                       | proyecto_estudiante |
      | DELETE FROM abet.carga_proyecto                         | carga_proyecto      |
      | UPDATE abet.carga_proyecto SET carga_id = carga_id      | carga_proyecto      |
      | DELETE FROM abet.rechazo_proyecto                       | rechazo_proyecto    |
      | UPDATE abet.plan_estudios SET tipo_curso = 'CARRERA'    | plan_estudios       |

  @US-02 @corte1
  Escenario: abet_app solo actualiza el estado, los conteos y el cierre de una subida
    Dado una conexión abet_app y una subida de plantilla EN_CURSO de la 420
    Cuando abet_app actualiza estado, filas_leidas, filas_aceptadas, filas_rechazadas y terminada_en de esa subida
    Entonces la actualización termina bien
    Y has_column_privilege da falso para UPDATE de carga_id, archivo_id, subida_por y reemplaza_carga_proyecto_id

  @US-02 @corte1
  Escenario: Los permisos sobreviven a la recreación de las vistas
    Dado abet_app creado con crear_rol_app.sql y la base migrada hasta V1_10
    Cuando la prueba vuelve a aplicar R__vista_tabla_maestra_capstone.sql y R__vista_r17_por_pi.sql y después crear_rol_app.sql
    Entonces has_table_privilege da verdadero para SELECT en abet.v_tabla_maestra_capstone y en abet.v_r17_por_pi y para INSERT en abet.proyecto_estudiante
    Y da falso para DELETE en abet.proyecto_estudiante

  # US-24: Vigilar los datos de proyecto con consultas de control

  @US-24 @corte1
  Escenario: Una base Capstone coherente deja las consultas de control en cero
    Dado la base migrada hasta V1_10 y la sección 420 coherente
    Cuando el administrador técnico corre las consultas de control de db/pruebas/pruebas.sql
    Entonces Q01 a Q14 y Q16 a Q20 devuelven 0 filas cada una
    Y Q15 sigue con el resultado de la spec 001, que solo encuentra acceso.usuario_autorizado.correo

  @US-24 @corte1
  Esquema del escenario: Cada anomalía la ve su consulta
    Dado la base migrada hasta V1_10 y la sección 420 coherente
    Cuando la prueba <anomalia> en una transacción que se deshace
    Entonces la consulta <consulta> devuelve 1 fila
    Y las demás consultas de Q16 a Q20 devuelven 0 filas

    Ejemplos:
      | anomalia                                                                   | consulta |
      | pasa la carga del export de la 420 a REEMPLAZADA y deja su subida PUBLICADA | Q16      |
      | deja la subida de la 420 con filas_aceptadas 10 y filas_rechazadas 1        | Q17      |
      | vuelve "CARRERA" el tipo_curso de "450024" en "AMB-2026"                    | Q18      |
      | cambia el título del integrante 99000106 del grupo 2                        | Q19      |
      | pasa la subida de la 420 a REEMPLAZADA sin ninguna que la reemplace         | Q20      |

  @US-24 @corte1
  Escenario: Un estudiante del export sin proyecto no es una anomalía
    Dado la base migrada hasta V1_10 y la sección 420 con la carga PUBLICADA y una subida PUBLICADA sin las filas de 99000110 y 99000111
    Cuando el administrador técnico corre Q16 a Q20
    Entonces cada consulta devuelve 0 filas
    Y la consulta de seguimiento S01 devuelve 2 filas, una por 99000110 y otra por 99000111

  @US-24 @corte1
  Escenario: Los controles de Neon traen las consultas nuevas iguales a las de las pruebas
    Dado db/pruebas/pruebas.sql y db/plataforma/neon/controles_neon.sql
    Cuando corre la prueba de paridad de db/pruebas/pruebas.sql
    Entonces controles_neon.sql trae Q01 a Q14 y Q16 a Q20 iguales a las de pruebas.sql, cada una con su único \set qNN :ROW_COUNT
    Y la sesión de abet_respaldo que corre controles_neon.sql no cambia el número de filas de abet.carga_proyecto
