# language: es
#
# Escenarios de aceptación de US-96 de la spec 010-nombre-del-profesor (épica EP-10, propuesta). El guion de la
# programación docente de la spec 006 lee una columna opcional nombre y la guarda junto al correo, sin pisar un
# nombre existente y sin escribir nombres en el informe.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid y nombres que empiezan
# por «Profesor Inventado». Un archivo real con nombres vive siempre fuera del repositorio (FR-009 de la spec 006).
#
# Vocabulario de los pasos, el de programacion_docente.feature de la spec 006.
# - «el archivo base con nombres» es programacion_20262_inventada.csv armado en tmp_path con la columna nombre y
#   estas dos filas, la 410 de 450002 con docente410@example.invalid y «Profesor Inventado Cuatrocientos Diez» y la
#   411 de 450002 con docente411@example.invalid y «Profesor Inventado Cuatrocientos Once». La fila 1 es la de los
#   encabezados, así que la primera fila de datos es la fila 2.
# - En los Ejemplos, \n es la secuencia que el paso convierte en un salto de línea dentro de la celda, y «un nombre
#   de 121 letras» es «Profesor Inventado » seguido de letras hasta sumar 121 caracteres.
# - «ningún texto del informe repite un nombre» busca en la salida estándar y en la de errores cada nombre del
#   archivo y de la base.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: La programación docente trae el nombre del profesor
  Como administrador técnico, quiero que la programación docente traiga el nombre de cada profesor,
  para no escribir nombres a mano cuando llega la programación del ciclo.

  Antecedentes:
    Dado una base desechable de partida de la spec 006, en PostgreSQL 18 con las migraciones V1_01 a V1_16, la vigencia de AMB-2026 en 2026-2 y el plan de medición de 450002 y 450010, sin secciones ni profesores
    Y el archivo base con nombres en tmp_path

  @spec010 @corte1 @US-96
  Escenario: Un profesor nuevo entra con su nombre
    Cuando el administrador corre el guion con el archivo base con nombres y --aplicar
    Entonces el guion termina con código 0
    Y acceso.usuario_autorizado trae "docente410@example.invalid" con rol "PROFESOR", activo y el nombre "Profesor Inventado Cuatrocientos Diez"
    Y el informe dice «Resumen. 2 secciones nuevas, 2 usuarios nuevos, 2 asignaciones nuevas y 0 nombres completados.» (propuesta)
    Y ningún texto del informe repite un nombre

  @spec010 @corte1 @US-96
  Escenario: Un profesor ya cargado sin nombre lo recibe y su rol y su estado no cambian
    Dado el archivo base de la spec 006, sin la columna nombre, ya aplicado con --aplicar
    Y "docente411@example.invalid" dado de baja con activo falso
    Cuando el administrador corre el guion con el archivo base con nombres y --aplicar
    Entonces "docente410@example.invalid" y "docente411@example.invalid" quedan con sus nombres del archivo
    Y "docente411@example.invalid" sigue con rol "PROFESOR" y activo falso
    Y el informe dice «Resumen. 0 secciones nuevas, 0 usuarios nuevos, 0 asignaciones nuevas y 2 nombres completados.» (propuesta)
    Y la línea final es «Cambios guardados.»

  @spec010 @corte1 @US-96
  Escenario: Un nombre que ya existe no se cambia
    Dado "docente410@example.invalid" ya cargado con el nombre "Profesor Inventado Anterior"
    Cuando el administrador corre el guion con el archivo base con nombres y --aplicar
    Entonces el nombre de "docente410@example.invalid" sigue siendo "Profesor Inventado Anterior"
    Y el informe dice «Aviso. docente410@example.invalid ya tiene otro nombre en la base y no se cambia.» (propuesta)
    Y ningún texto del informe repite un nombre

  @spec010 @corte1 @US-96
  Escenario: Un archivo sin la columna nombre responde como en la spec 006
    Dado el archivo base de la spec 006, sin la columna nombre
    Cuando el administrador corre el guion con ese archivo y --aplicar
    Entonces el informe dice «Resumen. 2 secciones nuevas, 2 usuarios nuevos y 2 asignaciones nuevas.» (propuesta)
    Y ningún usuario tiene nombre

  @spec010 @corte1 @US-96
  Escenario: Los espacios del nombre se normalizan antes de guardarlo
    Dado el archivo base con nombres con la fila 2 cambiada al nombre "  Profesor   Inventado Cuatrocientos Diez "
    Cuando el administrador corre el guion con ese archivo y --aplicar
    Entonces "docente410@example.invalid" queda con el nombre "Profesor Inventado Cuatrocientos Diez"

  @spec010 @corte1 @US-96
  Esquema del escenario: Un nombre inválido rechaza el archivo antes de conectarse
    Dado el archivo base con nombres con la fila 3 cambiada al nombre <nombre>
    Cuando el administrador corre el guion con ese archivo y --aplicar
    Entonces el informe dice «Fila 3. El nombre no es válido.» (propuesta)
    Y la línea final es «Archivo rechazado. Nada se escribió.»
    Y el guion termina con código 1 sin conectarse a la base
    Y ningún texto del informe repite el nombre de la fila 3

    Ejemplos:
      | caso           | nombre                                      |
      | arroba         | "docente411@example.invalid"                |
      | dígito         | "Profesor Inventado 411"                    |
      | salto de línea | "Profesor Inventado\nCuatrocientos Once"    |
      | 121 caracteres | un nombre de 121 letras                     |

  @spec010 @corte1 @US-96
  Escenario: Dos nombres distintos para un mismo correo rechazan el archivo
    Dado el archivo base con nombres con una fila 4 de la 410 de 450010 con "docente410@example.invalid" y el nombre "Profesor Inventado Otro"
    Cuando el administrador corre el guion con ese archivo y --aplicar
    Entonces el informe dice «Fila 4. El correo trae otro nombre en otra fila.» (propuesta)
    Y la línea final es «Archivo rechazado. Nada se escribió.»
    Y el guion termina con código 1 y ninguna de las tres tablas cambia
