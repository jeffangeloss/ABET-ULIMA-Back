# language: es
#
# Escenarios de aceptación del R-17 Capstone y de la tabla maestra en el formato nuevo (spec 002,
# historias US-19 a US-22). Todos los datos son inventados, con la plantilla y el export de la 420 que
# describe carga_proyectos.feature.
#
# Vocabulario de los pasos.
# - «el export de la 420 publicado» y «la plantilla publicada» son las subidas de carga_proyectos.feature,
#   con respuestas 201 y sus identificadores capturados de esas respuestas.
# - «descargar el R-17 de esa carga» es GET /api/cargas/{carga_id del export}/r17.xlsx.
# - «el libro» es el .xlsx de la respuesta, leído con openpyxl en modo de solo lectura y con los valores
#   guardados, sin recalcular fórmulas.
# - «antes de V1_10» es una base con V1_01 a V1_09 y los datos de la spec 001, donde la prueba guarda la
#   salida de la vista en una tabla temporal antes de aplicar V1_10.
# - La fila de la tabla de estudiantes de «Cursos Capstone» es una por medición (estudiante y PI), valor
#   provisional de D-25.
# - Lo marcado «(propuesta)» no está fijado y lo decide la revisión de la spec.

Característica: R-17 Capstone y tabla maestra en el formato nuevo generados desde la base
  Como profesor de un curso Capstone, quiero descargar el R-17 con la hoja «Cursos Capstone» y que la
  tabla maestra muestre mis proyectos en el formato nuevo, para entregar la evidencia de mi sección en el
  formato de mi tipo de curso sin armar ningún Excel a mano.

  Antecedentes:
    Dado una base PostgreSQL 16 desechable con las migraciones V1_01 a V1_10 y los datos de db/datos/periodo_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y la asignatura "450024" con tipo_curso "CAPSTONE" en "AMB-2026" (marca de V1_10, D-14)
    Y "docente420@example.invalid" tiene la sesión iniciada con rol "PROFESOR" y acceso.docente_seccion le asigna la sección 420 de "450024" en "2026-2"

  # US-19: Descargar el R-17 de una sección Capstone con la hoja «Cursos Capstone»

  @US-19 @corte1
  Escenario: El R-17 de una sección Capstone usa la hoja Capstone con los datos de proyecto
    Dado el export de la 420 publicado y la plantilla publicada con 11 proyectos
    Cuando el profesor descarga el R-17 de esa carga
    Entonces la respuesta es 200 y su Content-Disposition nombra el archivo "R017_450024_420_2026-2_PROVISIONAL.xlsx"
    Y el libro tiene las hojas "Cursos Capstone" y "Constancia", en ese orden, y no tiene la hoja "Cursos de Carrera"
    Y la cabecera de "Cursos Capstone" muestra la asignatura "450024", la sección "420" y el periodo "2026-2"
    Y los rótulos de B48:L48 son SO, PI, PROFESOR, CÓDIGO DEL ESTUDIANTE, CALIFICACIÓN, TÍTULO DEL PROYECTO, GRUPO, TIPO DE EMPRESA, RUC, NOMBRE DE ORGANIZACIÓN y LÍNEA DE INVESTIGACIÓN
    Y la tabla de estudiantes tiene 33 filas, una por cada fila de abet.medicion de esa carga
    Y en cada fila el GRUPO, el TÍTULO DEL PROYECTO, el TIPO DE EMPRESA, el RUC, el NOMBRE DE ORGANIZACIÓN y la LÍNEA DE INVESTIGACIÓN son iguales a los de abet.proyecto_estudiante para ese estudiante
    Y cada porcentaje del bloque II es igual al de abet.v_r17_por_pi para esa carga y su PI
    Y ninguna celda del libro empieza por "=" ni contiene "#REF!"
    Y ninguna hoja contiene "Estudiante Ficticio"
    Y el libro conserva el logotipo de la plantilla

  @US-19 @corte1
  Escenario: La hoja Constancia lleva las dos huellas y el conteo de proyectos sin valores
    Dado el export de la 420 publicado
    Y que el profesor subió una copia de la plantilla con 99000113 en la celda CÓDIGO de la fila 4 y obtuvo 201
    Cuando el profesor descarga el R-17 de esa carga
    Entonces la hoja "Constancia" muestra el sha256 del export y el sha256 de la plantilla, cada uno con su nombre de archivo
    Y la hoja "Constancia" dice "10 de 11 estudiantes con datos de proyecto"
    Y ninguna celda de "Constancia" contiene un título de proyecto, un nombre de organización ni un RUC de la plantilla

  @US-19 @corte1
  Escenario: Un curso de carrera sigue saliendo con su hoja de siempre
    Dado que "450002" tiene tipo_curso "CARRERA" y la sección 410 tiene PUBLICADA la carga de "sintetico_20262_450002_410.xlsx"
    Y que "docente410@example.invalid" tiene la sesión iniciada con la sección 410 asignada
    Cuando descarga el R-17 de esa carga
    Entonces el libro tiene las hojas "Cursos de Carrera" y "Constancia" y no tiene "Cursos Capstone"
    Y el bloque II muestra 63,6 %, 63,6 % y 72,7 %, como en US-15 de la spec 001

  @US-19 @corte1
  Escenario: La vista del R-17 distingue la sección de carrera de la Capstone
    Dado la 410 de "450002" y la 420 de "450024", ambas con carga PUBLICADA
    Cuando se consulta abet.v_r17_por_pi
    Entonces las filas de la 410 traen tipo_curso "CARRERA" y las de la 420 traen tipo_curso "CAPSTONE"

  # US-20: El R-17 Capstone sin plantilla sale con aviso

  @US-20 @corte1
  Escenario: El R-17 Capstone sin plantilla de proyectos sale con aviso
    Dado el export de la 420 publicado y ninguna plantilla publicada
    Cuando el profesor descarga el R-17 de esa carga
    Entonces la respuesta es 200 y su Content-Disposition nombra el archivo "R017_450024_420_2026-2_PROVISIONAL_SIN_PROYECTOS.xlsx" (propuesta)
    Y la hoja "Cursos Capstone" muestra bajo el título una franja que contiene "SIN DATOS DE PROYECTO"
    Y las columnas TÍTULO DEL PROYECTO, GRUPO, TIPO DE EMPRESA, RUC, NOMBRE DE ORGANIZACIÓN y LÍNEA DE INVESTIGACIÓN están vacías en las 33 filas
    Y el bloque II sigue mostrando los porcentajes de abet.v_r17_por_pi para esa carga
    Y la hoja "Constancia" dice "0 de 11 estudiantes con datos de proyecto" y muestra solo la huella del export

  @US-20 @corte1
  Escenario: El R-17 con una plantilla incompleta avisa cuántos faltan
    Dado el export de la 420 publicado y una plantilla publicada sin las filas de 99000110 y 99000111
    Cuando el profesor descarga el R-17 de esa carga
    Entonces la franja de "Cursos Capstone" contiene "SIN DATOS DE PROYECTO PARA 2 DE 11 ESTUDIANTES" (propuesta)
    Y las 6 filas de 99000110 y 99000111 traen vacías las seis columnas de proyecto
    Y su Content-Disposition nombra el archivo "R017_450024_420_2026-2_PROVISIONAL.xlsx", sin el sufijo "_SIN_PROYECTOS"

  # US-21: Obtener la tabla maestra de Capstone en el formato nuevo

  @US-21 @corte1
  Escenario: La tabla maestra Capstone trae una fila por estudiante y PI con su proyecto
    Dado el export de la 420 publicado con los PI 1.1, 1.2 y 1.3 y la plantilla publicada con 11 proyectos
    Cuando se consulta abet.v_tabla_maestra_capstone con el rol abet_app
    Entonces la vista devuelve 33 filas de la sección 420, tres por cada uno de los 11 estudiantes
    Y sus columnas, en el orden de information_schema.columns.ordinal_position, son SO, PI, PROFESOR, CÓDIGO DEL ESTUDIANTE, SECCIÓN, CALIFICACIÓN, TÍTULO DEL PROYECTO, GRUPO, TIPO DE EMPRESA, RUC, NOMBRE DE ORGANIZACIÓN, LÍNEA DE INVESTIGACIÓN y ARCHIVO
    Y las 3 filas de 99000101 traen GRUPO 1, TÍTULO DEL PROYECTO "Proyecto inventado A" y la CALIFICACIÓN de abet.medicion para cada PI
    Y las tres filas de cada estudiante repiten los mismos seis datos de proyecto
    Y PROFESOR es nulo en las 33 filas (valor provisional de D-17)
    Y ARCHIVO es "sintetico_20262_450024_420.xlsx" en las 33 filas (valor provisional de D-16)
    Y todo RUC devuelto empieza por "20" (valor provisional de D-19)

  @US-21 @corte1
  Escenario: Un estudiante sin proyecto sale con las seis columnas vacías y no desaparece
    Dado el export de la 420 publicado y una plantilla publicada sin las filas de 99000110 y 99000111
    Cuando se consulta abet.v_tabla_maestra_capstone
    Entonces la vista devuelve 33 filas
    Y las 3 filas de 99000111 traen TÍTULO DEL PROYECTO, GRUPO, TIPO DE EMPRESA, RUC, NOMBRE DE ORGANIZACIÓN y LÍNEA DE INVESTIGACIÓN nulos

  @US-21 @corte1
  Esquema del escenario: Lo que no está vigente no duplica filas
    Dado la sección 420 con <situacion>, armada en una transacción que se deshace
    Cuando se consulta abet.v_tabla_maestra_capstone para la sección 420
    Entonces la vista devuelve 33 filas y ninguna proviene de <excluida>

    Ejemplos:
      | situacion                                                                                 | excluida                     |
      | la carga A del export REEMPLAZADA con su subida REEMPLAZADA y la carga B PUBLICADA con su subida PUBLICADA | la carga A                   |
      | el export publicado, la subida de plantilla A REEMPLAZADA y la subida B PUBLICADA sobre la misma carga      | la subida A                  |

  @US-21 @corte1
  Escenario: Un curso de carrera no entra en la vista Capstone
    Dado la carga PUBLICADA de la sección 410 de "450002" con tipo_curso "CARRERA" y la carga PUBLICADA de la 420
    Cuando se consulta abet.v_tabla_maestra_capstone
    Entonces no hay filas de "450002"

  @US-21 @corte1
  Escenario: La vista Capstone no expone columnas de nombre de persona
    Dado la base migrada hasta V1_10
    Cuando se leen las columnas de abet.v_tabla_maestra_capstone y de las tablas de las que lee
    Entonces ninguna se llama alumno, nombre_estudiante, nombres ni apellidos
    Y pg_class.reloptions de abet.v_tabla_maestra_capstone contiene "security_barrier=true"

  # US-22: La tabla maestra tradicional y la vista del R-17 no cambian

  @US-22 @corte1
  Escenario: Las columnas de la vista tradicional no cambian
    Dado la base migrada hasta V1_10
    Cuando se leen el orden y el nombre de las columnas de abet.v_tabla_maestra_pi
    Entonces son AÑO, CICLO, CÓDIGO DEL CURSO, CURSO, CICLO DEL CURSO, SO, PI, PROFESOR, CÓDIGO DEL ESTUDIANTE, SECCIÓN, CALIFICACIÓN, ARCHIVO y ESTADO DE EVIDENCIA

  @US-22 @corte1
  Escenario: Las filas de la 410 no cambian con V1_10
    Dado la carga PUBLICADA de la 410 con 33 mediciones antes de V1_10 y su salida de abet.v_tabla_maestra_pi guardada
    Cuando se aplica V1_10 y se compara la vista con la salida guardada con EXCEPT en los dos sentidos
    Entonces las dos comparaciones devuelven 0 filas

  @US-22 @corte1
  Escenario: Un estudiante Capstone aparece en las dos vistas con la misma calificación
    Dado el export de la 420 publicado, con nivel 3 de 99000101 en el PI 1.1, y la plantilla publicada
    Cuando se consulta 99000101 y el PI "1.1" en abet.v_tabla_maestra_pi y en abet.v_tabla_maestra_capstone
    Entonces ambas devuelven 1 fila con CALIFICACIÓN 3

  @US-22 @corte1
  Escenario: La vista del R-17 conserva sus columnas y suma el tipo de curso al final
    Dado la base migrada hasta V1_10
    Cuando se comparan las columnas de abet.v_r17_por_pi con las de la spec 001 por information_schema.columns.ordinal_position
    Entonces las columnas de la spec 001 siguen en sus posiciones con sus tipos
    Y tipo_curso es la última columna
