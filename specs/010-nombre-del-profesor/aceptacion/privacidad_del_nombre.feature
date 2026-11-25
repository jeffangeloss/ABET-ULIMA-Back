# language: es
#
# Escenarios de aceptación de US-99 de la spec 010-nombre-del-profesor (épica EP-10, propuesta). El nombre del
# profesor aparece solo en D10 del R-17, y las semillas y los archivos de git llevan solo nombres inventados, como
# pide D-10 con la Ley 29733 y el DS 016-2024-JUS.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid y los nombres
# inventados de las convenciones de spec.md.
#
# Vocabulario de los pasos.
# - La base es la de profesores_en_el_r17.feature, con la 701 de 5643 en 2026-1 y docente701@example.invalid
#   llamado «Profesor Inventado Setecientos Uno».
# - «las celdas fuera de D10» se leen con openpyxl en cada hoja del libro. Las partes xl/sharedStrings.xml y la de
#   la hoja «Cursos de Carrera» traen el nombre por diseño, así que la búsqueda por partes del zip se limita a
#   docProps y a las demás hojas.
# - «el registro abet.api» se captura con caplog en el nivel INFO, como tests/test_api_mejora.py.
# - «la forma inventada» es «Profesor Inventado» seguida de una o más palabras con mayúscula inicial y solo letras.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: El nombre del profesor sale solo en D10
  Como dueño técnico del repositorio público, quiero pruebas que fijen dónde aparece el nombre del profesor,
  para cumplir la Ley 29733 con la mínima exposición.

  Antecedentes:
    Dado una base desechable de la spec 010 con los datos inventados de Ambiental en 2026-2 y de Química en 2026-1 y sus nombres inventados

  @spec010 @corte1 @US-99
  Escenario: Fuera de D10 el libro no repite el nombre
    Dado la 701 de 5643 publicada por docente701@example.invalid con su análisis declarado
    Cuando se genera el R-17 de esa carga
    Entonces ninguna celda fuera de D10 de la hoja «Cursos de Carrera» trae "Profesor Inventado Setecientos Uno"
    Y la hoja «Constancia» no trae "Profesor Inventado Setecientos Uno"
    Y ni el nombre del archivo ni docProps traen "Profesor Inventado Setecientos Uno"

  @spec010 @corte1 @US-99
  Escenario: Las rutas de cargas y de sesión no traen el nombre
    Dado la 701 de 5643 publicada por docente701@example.invalid con su análisis declarado
    Cuando docente701@example.invalid pide GET /api/sesion, GET /api/cargas y GET /api/cargas/{carga_id}
    Entonces ninguna respuesta trae "Profesor Inventado Setecientos Uno"
    Y subida_por sigue siendo "docente701@example.invalid"

  @spec010 @corte1 @US-99
  Escenario: El registro de la aplicación no trae el nombre
    Dado el registro abet.api capturado en el nivel INFO
    Cuando docente701@example.invalid inicia sesión, sube el export de la 701, declara su análisis y genera el R-17
    Entonces ninguna línea del registro abet.api contiene "Profesor Inventado Setecientos Uno"

  @spec010 @corte1 @US-99
  Escenario: Las semillas solo traen nombres inventados con correos de example.invalid
    Cuando la prueba de repositorio carga db/datos/periodo_2026_2_inventado.sql, varias_secciones_2026_2_inventado.sql y quimica_2026_1_inventado.sql en una base desechable (propuesta)
    Entonces cada nombre no nulo de acceso.usuario_autorizado tiene la forma inventada
    Y cada correo es del dominio example.invalid
    Pero con una semilla que asigna un nombre fuera de la forma inventada la prueba falla nombrando el archivo y sin repetir el nombre

  @spec010 @corte1 @US-99
  Escenario: Git no rastrea un archivo de programación con la columna nombre fuera de los datos inventados
    Cuando la prueba de repositorio lista los CSV rastreados con git ls-files (propuesta)
    Entonces ningún CSV fuera de tests/datos_inventados trae la columna nombre en su encabezado
    Pero con un CSV con la columna nombre agregado al índice en una copia temporal la prueba falla nombrando el archivo
