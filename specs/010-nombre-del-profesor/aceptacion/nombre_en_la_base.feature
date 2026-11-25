# language: es
#
# Escenarios de aceptación de US-95 de la spec 010-nombre-del-profesor (épica EP-10, propuesta). La base guarda el
# nombre del profesor en acceso.usuario_autorizado, opcional y normalizado, fuera del esquema abet, y Q15 lo vigila.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid y nombres que empiezan
# por «Profesor Inventado» y se escriben con letras.
#
# Vocabulario de los pasos.
# - «una base desechable migrada hasta V1_16» es una base del clúster de tests/cluster_desechable.py con las
#   migraciones V1_01 a V1_16, nunca localhost:5432 ni Neon.
# - «la base rechaza la fila por ck_usuario_autorizado_nombre» es el paso de test_base_neon_feature.py que espera el
#   SQLSTATE 23514 con el nombre de la restricción, sin repetir el valor.
# - En los Ejemplos, \n y \uXXXX son secuencias que el paso convierte en el salto de línea y en el punto de código
#   Unicode que nombran, antes de insertar.
# - «corre Q15» ejecuta el bloque de Q15 de db/pruebas/pruebas.sql sobre la base (FR-002).
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Nombre del profesor en la base
  Como administrador técnico de la base, quiero una columna opcional nombre en acceso.usuario_autorizado,
  para que el R-17 escriba al profesor sin guardar nombres en abet.

  Antecedentes:
    Dado una base desechable migrada hasta V1_16

  @spec010 @corte1 @US-95
  Escenario: Un usuario sin nombre sigue siendo válido
    Cuando el dueño de la base inserta "docente730@example.invalid" con rol "PROFESOR" y sin nombre
    Entonces la fila queda con nombre nulo
    Y acceso.usuario_autorizado tiene la columna nombre de hasta 120 caracteres que admite nulo

  @spec010 @corte1 @US-95
  Escenario: La base acepta un nombre normalizado con tildes y eñes
    Cuando el dueño de la base inserta "docente731@example.invalid" con el nombre "Profesor Inventado Ángel Muñoz"
    Entonces la fila queda con ese nombre

  @spec010 @corte1 @US-95
  Esquema del escenario: La base rechaza un nombre que no está normalizado o que no parece un nombre
    Cuando el dueño de la base inserta "docente732@example.invalid" con el nombre <nombre>
    Entonces la base rechaza la fila por ck_usuario_autorizado_nombre

    Ejemplos:
      | caso                     | nombre                                    |
      | espacio al comienzo      | " Profesor Inventado Uno"                 |
      | dos espacios seguidos    | "Profesor  Inventado Uno"                 |
      | vacío                    | ""                                        |
      | salto de línea           | "Profesor Inventado\nUno"                 |
      | espacio de ancho cero    | "Profesor Inventado​Uno"             |
      | arroba                   | "docente732@example.invalid"              |
      | dígito                   | "Profesor Inventado 732"                  |
      | coma                     | "Inventado, Profesor"                     |
      | forma NFD                | "Profesor Inventado Ángel"          |

  @spec010 @corte1 @US-95
  Escenario: Q15 encuentra en acceso solo el correo y el nombre del usuario
    Cuando corre Q15
    Entonces el filtro sobre acceso encuentra exactamente usuario_autorizado.correo y usuario_autorizado.nombre
    Pero con una columna nombre_contacto agregada a acceso.credencial Q15 falla con «FALLA Q15: en acceso solo usuario_autorizado.correo y usuario_autorizado.nombre deben pasar el filtro» (propuesta)

  @spec010 @corte1 @US-95
  Escenario: Ninguna tabla de abet gana una columna de nombre
    Cuando corre la consulta de control Q04
    Entonces devuelve 0 filas

  @spec010 @corte1 @US-95
  Escenario: La aplicación lee el nombre y no lo escribe
    Dado el rol abet_app creado con crear_rol_app.sql
    Cuando abet_app consulta el nombre de acceso.usuario_autorizado
    Entonces la consulta responde sin error
    Pero un UPDATE de nombre de abet_app responde con el SQLSTATE 42501
    Y un INSERT con nombre de abet_app responde con el SQLSTATE 42501

  @spec010 @corte1 @US-95
  Escenario: Los roles de lectura no alcanzan el nombre y el rol de respaldo sí lo lee
    Dado los roles de crear_roles_lectura.sql creados en la copia
    Cuando abet_lectura y powerbi_lectura consultan acceso.usuario_autorizado
    Entonces ambos reciben el SQLSTATE 42501
    Y abet_respaldo lee la columna nombre sin error
