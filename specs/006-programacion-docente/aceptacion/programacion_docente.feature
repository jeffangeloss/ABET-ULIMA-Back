# language: es
#
# Escenarios de aceptación de la carga de la programación docente del ciclo, de las historias de usuario (user
# stories, US) US-55, US-56 y US-57 de la spec 006-programacion-docente (épica EP-06, propuesta). Claudia León
# pide en su correo del 19 o 20 de noviembre de 2026 que la sección y el docente lleguen solos con la
# programación docente post-matrícula, y su correo del 18 de noviembre fija la capacitación en la semana 14 y
# los registros en la 15. Sin esta carga, ningún profesor real encuentra su sección en P2 (C-C01 de la
# auditoría del cambio del 2026-11-21 de la spec 005, en revision-historias.md).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid. El archivo de la
# programación se arma en tmp_path y nunca entra a tests/datos_inventados/. Ninguna contraseña aparece escrita
# aquí, porque la prueba asigna al azar la contraseña con que abre cada sesión, sin guardarla en el repositorio.
#
# Vocabulario de los pasos (propuesta).
# - «el guion» es db/herramientas/cargar_programacion.py, corrido con python -I, --periodo 2026-2 y --archivo
#   con la ruta del archivo en tmp_path, y con --aplicar solo cuando el paso lo dice. Recibe la conexión del
#   dueño de la base desechable por las variables PGHOST, PGPORT, PGDATABASE y PGUSER, nunca por argumentos.
# - «el informe» es la salida estándar del guion. Un paso que cita una línea entre «» exige esa línea completa.
# - «el archivo base» es programacion_20262_inventada.csv, con las filas de los Antecedentes. La fila 1 es la de
#   los encabezados, así que la primera fila de datos es la fila 2. «con la fila N cambiada a X» cambia solo la
#   columna que el valor indica, y «con una fila N que …» agrega esa fila al final.
# - «ninguna de las tres tablas cambia» compara el número de filas y el contenido de abet.seccion,
#   acceso.usuario_autorizado y acceso.docente_seccion antes y después de la corrida.
# - Cada escenario corre en una base desechable propia del clúster de tests/cluster_desechable.py, nunca en
#   localhost:5432, así que los identificadores salen de la base y nunca se suponen.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec. D-44 y D-45
#   siguen abiertas con la Coordinación de Ambiental, y J-42 espera la respuesta de Jefferson.

Característica: Carga de la programación docente del ciclo desde el archivo de la carrera
  Como administrador técnico de la carrera, quiero cargar las secciones, los profesores y sus asignaciones
  desde el archivo de la programación docente, primero en seco y después con --aplicar, para que cada profesor
  encuentre su sección en P2 sin que nadie escriba SQL a mano.

  Antecedentes:
    Dado una base desechable de partida de la spec 006, en PostgreSQL 18 con las migraciones V1_01 a V1_11, la vigencia de AMB-2026 en 2026-2 y el plan de medición de 450002 y 450010, sin secciones ni profesores
    Y "coordinacion@example.invalid" activo con rol "COORDINADOR" y sin secciones en acceso.docente_seccion
    Y el archivo base programacion_20262_inventada.csv en tmp_path con estas filas
      | periodo | asignatura | seccion | correo                     | curso_blackboard           |
      | 2026-2  | 450002     | 410     | docente410@example.invalid | SINTETICO_20262_450002_410 |
      | 2026-2  | 450002     | 411     | docente411@example.invalid | SINTETICO_20262_450002_411 |

  # US-55: Cargar la programación docente con una corrida en seco antes de escribir

  @US-55 @spec006 @corte1
  Escenario: La corrida en seco informa y no escribe
    Cuando el administrador corre el guion con el archivo base y sin --aplicar
    Entonces el guion termina con código 0
    Y el informe dice «Resumen. 2 secciones nuevas, 2 usuarios nuevos y 2 asignaciones nuevas.» (propuesta)
    Y el informe termina con «Corrida en seco. Nada se escribió.» (propuesta)
    Y ninguna de las tres tablas cambia

  @US-55 @spec006 @corte1
  Escenario: La corrida con --aplicar escribe y se puede repetir
    Cuando el administrador corre el guion con el archivo base y con --aplicar
    Entonces el guion termina con código 0
    Y el informe dice «Cambios guardados.» (propuesta)
    Y abet.seccion tiene la 410 de "450002" con el curso "SINTETICO_20262_450002_410" y la 411 de "450002" con el curso "SINTETICO_20262_450002_411" en "2026-2"
    Y acceso.usuario_autorizado tiene a "docente410@example.invalid" y a "docente411@example.invalid" con rol "PROFESOR" y activos
    Y acceso.docente_seccion asigna la 410 de "450002" a "docente410@example.invalid" y la 411 de "450002" a "docente411@example.invalid"
    Cuando el administrador corre otra vez el guion con el archivo base y con --aplicar
    Entonces el guion termina con código 0
    Y el informe dice «Resumen. 0 secciones nuevas, 0 usuarios nuevos y 0 asignaciones nuevas.» (propuesta)
    Y el informe termina con «Sin cambios.» (propuesta)
    Y ninguna de las tres tablas cambia en la segunda corrida

  @US-55 @spec006 @corte1
  Escenario: El profesor cargado recibe solo su sección en GET /api/secciones
    Dado la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y que el administrador corrió el guion con el archivo base y con --aplicar
    Y que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando se envía GET /api/secciones?periodo=2026-2
    Entonces la API responde 200 con 1 sección, la 410 de "450002"
    Y la respuesta no trae la 411 de "450002"

  @US-55 @spec006 @corte1
  Escenario: Un correo con mayúsculas o espacios se normaliza
    Dado que el administrador corrió el guion con el archivo base y con --aplicar
    Y el archivo base con la fila 2 cambiada al correo « Docente410@EXAMPLE.invalid »
    Cuando el administrador corre el guion con ese archivo y con --aplicar
    Entonces el informe dice «Resumen. 0 secciones nuevas, 0 usuarios nuevos y 0 asignaciones nuevas.» (propuesta)
    Y acceso.usuario_autorizado tiene una sola fila con el correo "docente410@example.invalid"

  @US-55 @spec006 @corte1
  Escenario: Dos profesores en la misma sección dan dos asignaciones
    Dado el archivo base con una fila 4 que asigna la 411 de "450002" a "docente.varias@example.invalid" con el curso "SINTETICO_20262_450002_411"
    Cuando el administrador corre el guion con ese archivo y con --aplicar
    Entonces el informe dice «Resumen. 2 secciones nuevas, 3 usuarios nuevos y 3 asignaciones nuevas.» (propuesta)
    Y acceso.docente_seccion asigna la 411 de "450002" a "docente411@example.invalid" y a "docente.varias@example.invalid"

  @US-55 @spec006 @corte1
  Escenario: El guion no asigna contraseñas
    Cuando el administrador corre el guion con el archivo base y con --aplicar
    Entonces acceso.credencial no gana ninguna fila
    Y el informe dice «Los usuarios nuevos no tienen contraseña. Asígnela con asignar_claves.py o con el código por correo.» (propuesta)

  # US-56: Lo que ya está en la base no se borra ni cambia sin aviso

  @US-56 @spec006 @corte1
  Escenario: Una asignación que el archivo no trae se informa y no se borra
    Dado la 412 de "450002" en "2026-2" asignada a "docente.varias@example.invalid", sembrada por el dueño de la base
    Cuando el administrador corre el guion con el archivo base y con --aplicar
    Entonces el guion termina con código 0
    Y el informe dice «Aviso. La sección 412 de 450002 tiene en la base a docente.varias@example.invalid y el archivo no la trae.» (propuesta)
    Y acceso.docente_seccion conserva la asignación de la 412 de "450002" a "docente.varias@example.invalid"
    Y abet.seccion conserva la 412 de "450002"

  @US-56 @spec006 @corte1
  Escenario: Un coordinador que también dicta conserva su rol
    Dado el archivo base con la fila 3 cambiada al correo "coordinacion@example.invalid"
    Cuando el administrador corre el guion con ese archivo y con --aplicar
    Entonces el rol de "coordinacion@example.invalid" sigue en "COORDINADOR"
    Y acceso.docente_seccion asigna la 411 de "450002" a "coordinacion@example.invalid"
    Y el informe dice «Aviso. coordinacion@example.invalid es COORDINADOR y no podrá subir ni declarar en la sección 411 de 450002.» (propuesta)

  @US-56 @spec006 @corte1
  Escenario: Un profesor dado de baja no se reactiva
    Dado "docente411@example.invalid" con rol "PROFESOR" y activo falso, sembrado por el dueño de la base
    Cuando el administrador corre el guion con el archivo base y con --aplicar
    Entonces "docente411@example.invalid" sigue con activo falso
    Y acceso.docente_seccion asigna la 411 de "450002" a "docente411@example.invalid"
    Y el informe dice «Aviso. docente411@example.invalid está dado de baja y no verá la sección 411 de 450002.» (propuesta)

  @US-56 @spec006 @corte1
  Escenario: Una sección de una asignatura sin plan de medición entra con aviso
    Dado que la base no tiene plan de medición de "450010" en "2026-2"
    Y el archivo base con una fila 4 que asigna la 410 de "450010" a "docente.varias@example.invalid" sin curso de Blackboard
    Cuando el administrador corre el guion con ese archivo y con --aplicar
    Entonces abet.seccion tiene la 410 de "450010" en "2026-2" sin curso de Blackboard
    Y el informe dice «Aviso. La asignatura 450010 no tiene plan de medición en 2026-2, así que su sección 410 no podrá recibir exports.» (propuesta)

  # US-57: Un archivo con errores no deja nada a medias

  @US-57 @spec006 @corte1
  Esquema del escenario: Una fila inválida rechaza el archivo entero
    Dado el archivo base con la fila 3 cambiada a <cambio>
    Cuando el administrador corre el guion con ese archivo y con --aplicar
    Entonces el guion termina con código 1
    Y el informe dice «<mensaje>» (propuesta)
    Y el informe termina con «Archivo rechazado. Nada se escribió.» (propuesta)
    Y ninguna de las tres tablas cambia

    Ejemplos:
      | cambio                                           | mensaje                                                                                         |
      | la asignatura "999999"                           | Fila 3. La asignatura 999999 no existe en el catálogo.                                          |
      | la sección "0411"                                | Fila 3. El número de sección 0411 no es válido.                                                 |
      | el correo "docente411example.invalid"            | Fila 3. El correo docente411example.invalid no es válido.                                       |
      | el periodo "2026-1"                              | Fila 3. El periodo 2026-1 no es el de la corrida, 2026-2.                                       |
      | el correo vacío                                  | Fila 3. Falta el correo.                                                                        |
      | el curso de Blackboard "SINTETICO_20262_450002_410" | Fila 3. El curso de Blackboard SINTETICO_20262_450002_410 ya es de la sección 410 de 450002. |

  @US-57 @spec006 @corte1
  Escenario: El informe nombra todas las filas inválidas
    Dado el archivo base con la fila 2 cambiada a la asignatura "999999" y la fila 3 cambiada a la sección "0411"
    Cuando el administrador corre el guion con ese archivo y sin --aplicar
    Entonces el guion termina con código 1
    Y el informe dice «Fila 2. La asignatura 999999 no existe en el catálogo.» antes de «Fila 3. El número de sección 0411 no es válido.» (propuestas)

  @US-57 @spec006 @corte1
  Escenario: Falta una columna obligatoria
    Dado el archivo base sin la columna correo
    Cuando el administrador corre el guion con ese archivo y sin --aplicar
    Entonces el guion termina con código 1
    Y el informe dice «Falta la columna correo.» (propuesta)

  # El disparador existe solo en la base desechable del escenario y nunca en un archivo de db/.
  @US-57 @spec006 @corte1
  Escenario: Una falla de la base deshace todo
    Dado un disparador de prueba que rechaza la segunda fila que entra a acceso.docente_seccion
    Cuando el administrador corre el guion con el archivo base y con --aplicar
    Entonces el guion termina con código 3
    Y el informe dice «La base rechazó la escritura y no guardó nada.» (propuesta)
    Y ninguna de las tres tablas cambia

  @US-57 @spec006 @corte1
  Esquema del escenario: El guion no corre sin sus argumentos ni con el archivo dentro del repositorio
    Cuando el administrador corre el guion <caso>
    Entonces el guion termina con código 2 sin conectarse a la base
    Y el informe dice «<mensaje>» (propuesta)

    Ejemplos:
      | caso                                                         | mensaje                                                          |
      | sin --periodo                                                | Falta el periodo, por ejemplo --periodo 2026-2.                  |
      | con --periodo 2026-13                                        | El periodo no tiene la forma AAAA-C.                             |
      | con un archivo que no existe                                 | No se encuentra el archivo de la programación.                   |
      | con una copia del archivo base dentro de la copia de trabajo | El archivo de la programación debe estar fuera del repositorio.  |
