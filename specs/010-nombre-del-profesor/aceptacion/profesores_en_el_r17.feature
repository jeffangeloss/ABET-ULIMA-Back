# language: es
#
# Escenarios de aceptación de US-97 y US-98 de la spec 010-nombre-del-profesor (épica EP-10, propuesta). La celda
# D10 del R-17, valor del rótulo «Profesor:» de B10:C10, sale con los nombres de los profesores asignados a la
# sección, y un profesor sin nombre o una sección sin profesor no rompen el libro.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid y los nombres
# inventados de las convenciones de spec.md.
#
# Vocabulario de los pasos, el de r17_constancia.feature de la spec 001 y el de r17_desde_la_base.feature de la
# spec 005.
# - La base tiene db/datos/periodo_2026_2_inventado.sql y db/datos/quimica_2026_1_inventado.sql con los nombres
#   inventados de FR-013, así que docente410@example.invalid se llama «Profesor Inventado Cuatrocientos Diez» y
#   docente701@example.invalid a docente703@example.invalid se llaman «Profesor Inventado Setecientos Uno», «Dos»
#   y «Tres». La 704 de 5643 no tiene profesor.
# - «publicada con su análisis declarado» sube el export de prueba de la sección, lo deja PUBLICADA y llama a
#   declarar() de tests/cargas_de_prueba.py, porque el R-17 solo sale con la declaración vigente completa
#   (BR-R17-12).
# - «se genera el R-17» es GET /api/cargas/{carga_id}/r17.xlsx (ruta 7) con la sesión del profesor de la sección o
#   de la coordinación, y el libro se lee con openpyxl. «La hoja» es «Cursos de Carrera».
# - Un profesor extra, como docente721@example.invalid, se siembra en el paso Dado con rol PROFESOR y su asignación
#   en acceso.docente_seccion, y no en db/datos.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: El R-17 nombra a los profesores de la sección
  Como profesor o coordinación que entrega el R-17 a la carrera, quiero que «Profesor:» venga llena con quienes
  dictan la sección, para no completar la celda a mano en cada libro.

  Antecedentes:
    Dado una base desechable de la spec 010 con los datos inventados de Ambiental en 2026-2 y de Química en 2026-1 y sus nombres inventados

  # US-97: D10 del R-17 trae los profesores asignados

  @spec010 @corte1 @US-97
  Esquema del escenario: Una sección con un profesor trae su nombre en D10
    Dado la <seccion> de <asignatura> en <periodo> publicada con su análisis declarado
    Cuando se genera el R-17 de esa carga
    Entonces D10 de la hoja vale "<nombre>"
    Y B10 de la hoja sigue diciendo "Profesor:"
    Y B6 de la hoja dice "<carrera>"

    Ejemplos:
      | seccion | asignatura | periodo | nombre                                | carrera                          |
      | 410     | 450002     | 2026-2  | Profesor Inventado Cuatrocientos Diez | Carrera de Ingeniería Ambiental  |
      | 701     | 5643       | 2026-1  | Profesor Inventado Setecientos Uno    | Carrera de Ingeniería Industrial |

  @spec010 @corte1 @US-97
  Escenario: Varios profesores salen en orden alfabético sin tildes ni mayúsculas, separados por punto y coma, y el orden es estable
    Dado "docente721@example.invalid" con el nombre "Profesor Inventado Beto" asignado a la 701 de 5643
    Y "docente722@example.invalid" con el nombre "Profesor Inventado Ángel" asignado a la 701 de 5643
    Y la 701 de 5643 publicada con su análisis declarado
    Cuando se genera el R-17 de esa carga dos veces
    Entonces D10 vale "Profesor Inventado Ángel; Profesor Inventado Beto; Profesor Inventado Setecientos Uno" las dos veces

  @spec010 @corte1 @US-97
  Escenario: Un profesor dado de baja sigue en D10 de su sección
    Dado "docente722@example.invalid" con el nombre "Profesor Inventado Ángel" asignado a la 701 de 5643
    Y la 701 de 5643 publicada con su análisis declarado
    Y "docente722@example.invalid" dado de baja con activo falso
    Cuando coordinador.quimica@example.invalid genera el R-17 de esa carga
    Entonces D10 vale "Profesor Inventado Ángel; Profesor Inventado Setecientos Uno"

  @spec010 @corte1 @US-97
  Escenario: Solo los profesores de la sección salen en D10
    Dado la 701 de 5643 publicada con su análisis declarado
    Y una cuenta COORDINADOR inactiva "coordinador.anterior@example.invalid" con el nombre "Profesor Inventado Coordinador" asignada a la 701 de 5643
    Cuando se genera el R-17 de esa carga
    Entonces D10 vale "Profesor Inventado Setecientos Uno"
    Y D10 no contiene "Profesor Inventado Setecientos Dos", que dicta solo la 702
    Y D10 no contiene "Profesor Inventado Coordinador"

  @spec010 @corte1 @US-97
  Escenario: Un nombre que parece fórmula queda como texto
    Dado "docente723@example.invalid" con el nombre "=Profesor Inventado Fórmula" asignado a la 702 de 5643
    Y la 702 de 5643 publicada con su análisis declarado
    Cuando se genera el R-17 de esa carga
    Entonces D10 es una cadena que empieza por "=Profesor Inventado Fórmula"
    Y ninguna celda del libro es una fórmula

  @spec010 @corte1 @US-97
  Escenario: Tres nombres caben en D10:I10 y la fila 10 crece sin mover el resto de la cabecera
    Dado "docente721@example.invalid" con el nombre "Profesor Inventado Bartolomé Cuatrecasas Villanueva" asignado a la 703 de 5643
    Y "docente722@example.invalid" con el nombre "Profesor Inventado Ángel Echeverría Santisteban" asignado a la 703 de 5643
    Y la 703 de 5643 publicada con su análisis declarado
    Cuando se genera el R-17 de esa carga
    Entonces D10 trae los tres nombres completos
    Y D10 tiene ajuste de texto y la fila 10 es más alta que en la plantilla, sin pasar de 409 puntos (propuesta)
    Y las filas 9 y 11 y las filas 29 a 36 tienen el mismo alto que con un solo profesor

  @spec010 @corte1 @US-97
  Escenario: Fuera de D10 y de la fila 10 la plantilla no cambia
    Dado la 410 de 450002 en 2026-2 publicada con su análisis declarado
    Cuando se genera el R-17 de esa carga
    Entonces B6, D8, D9, D11, I11 y B15 de la hoja valen lo mismo que antes de la spec 010
    Y las 45 celdas combinadas de la plantilla siguen combinadas
    Y los recuadros A y B traen lo mismo que antes de la spec 010

  # US-98: Un profesor sin nombre o una sección sin profesor no rompen el R-17

  @spec010 @corte1 @US-98
  Escenario: Un profesor sin nombre no sale y el otro sí
    Dado "docente701@example.invalid" con el nombre nulo
    Y "docente721@example.invalid" con el nombre "Profesor Inventado Beto" asignado a la 701 de 5643
    Y la 701 de 5643 publicada por docente701@example.invalid con su análisis declarado
    Cuando se genera el R-17 de esa carga
    Entonces D10 vale "Profesor Inventado Beto"
    Y la hoja «Cursos de Carrera» no contiene "docente701" en ninguna celda
    Y la hoja «Constancia» sigue diciendo «Subido por docente701@example.invalid»

  @spec010 @corte1 @US-98
  Escenario: Si ningún profesor tiene nombre, D10 queda vacía como hoy
    Dado "docente702@example.invalid" con el nombre nulo
    Y la 702 de 5643 publicada con su análisis declarado
    Cuando se genera el R-17 de esa carga
    Entonces la respuesta es 200
    Y D10 está vacía y B10 sigue diciendo "Profesor:"

  @spec010 @corte1 @US-98
  Escenario: La sección sin profesor tiene R-17 con D10 vacía
    Dado la 704 de 5643 sin filas en acceso.docente_seccion
    Y la 704 publicada por coordinador.quimica@example.invalid en el corte 2 con su análisis declarado
    Cuando coordinador.quimica@example.invalid genera el R-17 de esa carga
    Entonces la respuesta es 200
    Y D10 está vacía y el resto de la cabecera es igual que antes de la spec 010

  @spec010 @corte1 @US-98
  Escenario: La consulta informativa cuenta las secciones publicadas con un profesor sin nombre
    Dado "docente701@example.invalid" con el nombre nulo
    Y la 701 y la 702 de 5643 publicadas con su análisis declarado
    Cuando corre db/plataforma/neon/profesores_sin_nombre.sql con -v periodo=2026-1 (propuesta)
    Entonces la salida dice 1 sección publicada con un profesor sin nombre y 1 profesor asignado sin nombre
    Y la salida no contiene correos, nombres ni números de sección
    Y la sesión queda en solo lectura antes de la primera consulta
