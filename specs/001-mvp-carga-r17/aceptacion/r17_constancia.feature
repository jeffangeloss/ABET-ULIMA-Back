# language: es
#
# Escenarios de aceptación del R-17 y de la constancia de la carga (spec 001, historias US-15 y US-16).
# Todos los datos son inventados. Los archivos viven en tests/datos_inventados/ y los correos usan el
# dominio reservado example.invalid. Las cifras salen de bd/pruebas/datos_sinteticos.sql y de la
# sección 3 de bd/pruebas/pruebas.sql.
#
# Vocabulario de los pasos.
# - «subir X a la sección N» es POST /api/secciones/{seccion_id de N}/cargas con X en el campo
#   multipart «archivo», con la cookie abet_sesion de quien tiene la sesión iniciada.
# - «descargar el R-17 de esa carga» es GET /api/cargas/{carga_id}/r17.xlsx, y «pedir la constancia de
#   esa carga» es GET /api/cargas/{carga_id}.
# - «la respuesta» es la respuesta HTTP de esa petición; los errores traen { "detail": "mensaje" }.
# - «el libro» es el .xlsx de la respuesta, leído con openpyxl en modo de solo lectura y con los
#   valores guardados, sin recalcular fórmulas.
# - Cada escenario corre en una base desechable propia, así que los carga_id se capturan de la respuesta
#   de la subida y nunca se suponen.
# - El R-17 sale de abet.v_r17_por_pi y de las tablas, nunca de volver a leer el export.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: R-17 y constancia de la carga generados desde la base
  Como profesor de Ingeniería Ambiental, quiero descargar el R-17 de mi sección calculado desde la base,
  con una hoja «Constancia», para tener la evidencia de que mi export está en la base con esos datos.

  Antecedentes:
    Dado una base PostgreSQL 16 desechable con las migraciones V1_01 a V1_09 y los datos de db/datos/periodo_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y el conjunto de reglas "R-2026-BORRADOR" en estado "BORRADOR" con META_LOGRO 0,80 y NIVEL_ESPERADO 3 DEFINIDOS
    Y "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR" y acceso.docente_seccion le asigna la sección 410 de "450002" en "2026-2"

  # US-15: Descargar el R-17 generado desde la base

  @US-15 @corte1
  Escenario: R-17 del export correcto
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el profesor descarga el R-17 de esa carga
    Entonces la respuesta es 200 con Content-Type "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    Y su Content-Disposition nombra el archivo "R017_450002_410_2026-2_PROVISIONAL.xlsx"
    Y el libro tiene las hojas "Cursos de Carrera" y "Constancia"
    Y la cabecera de "Cursos de Carrera" muestra la asignatura "450002", la sección "410" y el periodo "2026-2"
    Y el bloque I muestra el SO 5 con los PI 5.1, 5.2 y 5.3
    Y el bloque II muestra 63,6 % (7 de 11) en 5.1, 63,6 % (7 de 11) en 5.2 y 72,7 % (8 de 11) en 5.3, con meta 80 %
    Y el bloque II muestra por nivel 1, 3, 4 y 3 estudiantes en 5.1, 1, 3, 4 y 3 en 5.2 y 1, 2, 5 y 3 en 5.3
    Y cada porcentaje es igual a pct_logro_sobre_calificados de abet.v_r17_por_pi para ese carga_id y ese PI
    Y cada conteo por nivel es igual a n_nivel_1, n_nivel_2, n_nivel_3 y n_nivel_4 de abet.v_r17_por_pi para ese carga_id y ese PI
    Y la tabla de estudiantes tiene 33 filas con SO, PI, código y calificación, ordenadas por PI y fila de origen, con los códigos 99000001 a 99000011
    Y ninguna celda del libro empieza por "=" ni contiene "#REF!"
    Y los recuadros de causas, acciones y comentario están vacíos

  @US-15 @corte1
  Escenario: R-17 del export con el 5 en la fila 3
    Dado que "export_inventado_410_con_error.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el profesor descarga el R-17 de esa carga
    Entonces la respuesta es 200
    Y el bloque II muestra 60,0 % (6 de 10) en 5.1, 60,0 % (6 de 10) en 5.2 y 70,0 % (7 de 10) en 5.3, con meta 80 %
    Y cada porcentaje es igual a pct_logro_sobre_calificados de abet.v_r17_por_pi para ese carga_id y ese PI
    Y la tabla de estudiantes tiene 30 filas y ninguna con el código 99000002

  @US-15 @corte1
  Escenario: Con reglas en borrador el R-17 sale provisional
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el profesor descarga el R-17 de esa carga
    Entonces abet.v_r17_por_pi devuelve 3 filas de ese carga_id con provisional verdadero, conjunto_reglas "R-2026-BORRADOR" y pct_logro_segun_regla nulo
    Y la hoja "Cursos de Carrera" muestra bajo el título una franja que contiene "PROVISIONAL" y "R-2026-BORRADOR"
    Y el nombre del archivo termina en "_PROVISIONAL.xlsx"
    Y el título de las propiedades del libro contiene "PROVISIONAL"

  # El conjunto R-PRUEBA-APROBADO es inventado y solo existe en la base de pruebas, como el caso A03 de
  # bd/pruebas/pruebas.sql. En Neon ningún conjunto se aprueba antes de las historias de después del MVP.
  # La cifra 90,9 % sale de recalcular los niveles de la 410 de bd/pruebas/datos_sinteticos.sql con el
  # NIVEL_ESPERADO 2 de A03. En cada PI, 10 de los 11 estudiantes tienen nivel 2 o más, y como no hay
  # SIN_EVIDENCIA el porcentaje sobre calificados y el que fija SE_EXCLUYE_DEL_DENOMINADOR coinciden.
  @US-15 @corte1 @reglas_aprobadas_de_prueba
  Escenario: Con reglas aprobadas el R-17 sale sin franja
    Dado que la base tiene el conjunto "R-PRUEBA-APROBADO" de Ambiental en estado "APROBADO" con META_LOGRO 0,70, NIVEL_ESPERADO 2, CORTE_ROJO 0,50, TRATO_SIN_EVIDENCIA "SE_EXCLUYE_DEL_DENOMINADOR" y la conversión de sus 4 niveles, como en el caso A03 de pruebas.sql
    Y la API configurada con CONJUNTO_REGLAS "R-PRUEBA-APROBADO"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y la consulta de control Q11 devuelve 0 filas
    Cuando el profesor descarga el R-17 de esa carga
    Entonces abet.v_r17_por_pi devuelve 3 filas de ese carga_id con provisional falso, nivel_esperado 2, meta_logro_pct 70,0 y pct_logro_segun_regla 90,9
    Y el bloque II muestra 90,9 % (10 de 11) en 5.1, 5.2 y 5.3, con meta 70 %
    Y ninguna hoja del libro contiene la franja "PROVISIONAL"
    Y su Content-Disposition nombra el archivo "R017_450002_410_2026-2.xlsx"

  @US-15 @corte1
  Escenario: El R-17 no lleva nombres de personas
    Dado que "export_inventado_410_con_error.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el profesor descarga el R-17 de esa carga
    Entonces las propiedades creator y lastModifiedBy del libro están vacías o dicen "ABET_SIS_MED"
    Y ninguna hoja del libro contiene un apellido ni un nombre de las columnas Last Name y First Name del export
    Y el nombre del archivo no contiene ningún correo ni nombre de persona

  # La regla de visibilidad la prueba US-06; aquí solo se repite el caso de esta ruta.
  @US-15 @corte1
  Esquema del escenario: El R-17 de la 410 según quién lo pide
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que "<correo>" tiene la sesión iniciada con rol "<rol>"
    Cuando "<correo>" descarga el R-17 de esa carga
    Entonces la respuesta es <estado>
    Y <resultado>

    Ejemplos:
      | correo                       | rol         | estado | resultado                                                         |
      | docente410@example.invalid   | PROFESOR    | 200    | el bloque II muestra 63,6 % en 5.1, 63,6 % en 5.2 y 72,7 % en 5.3 |
      | coordinacion@example.invalid | COORDINADOR | 200    | el bloque II muestra 63,6 % en 5.1, 63,6 % en 5.2 y 72,7 % en 5.3 |
      | docente411@example.invalid   | PROFESOR    | 403    | el cuerpo de la respuesta no es un libro de Excel                 |

  # El código 409 para una carga que no está publicada es una (propuesta).
  @US-15 @corte1
  Escenario: Una carga rechazada no tiene R-17
    Dado que una copia de "sintetico_20262_450002_410.xlsx" sin la columna 5.2 está subida a la sección 410 con respuesta 201, estado "RECHAZADA" y su carga_id
    Cuando el profesor descarga el R-17 de esa carga
    Entonces la respuesta es 409 con detail "La carga no está publicada y no tiene R-17."
    Y abet.v_r17_por_pi no devuelve filas de ese carga_id

  # US-16: Recibir la constancia de la carga

  # Valor provisional de D-12. La hoja «Constancia» muestra el correo de quien sube el archivo, y ni el
  # nombre del archivo ni las propiedades del libro lo llevan.
  @US-16 @corte1
  Escenario: Constancia del export correcto en el R-17
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el profesor descarga el R-17 de esa carga
    Entonces la hoja "Constancia" muestra ese carga_id, el archivo "sintetico_20262_450002_410.xlsx" y la hoja "gc_SINTETICO_20262_450002_410_f"
    Y muestra filas de datos, leídas, aceptadas y rechazadas "11 / 11 / 11 / 0"
    Y muestra la huella SHA-256 completa, igual a archivo_origen.sha256 y a la salida de "shasum -a 256" sobre tests/datos_inventados/sintetico_20262_450002_410.xlsx
    Y muestra el estado "PUBLICADA" y la versión del programa igual a carga.programa_version
    Y muestra el conjunto "R-2026-BORRADOR (BORRADOR)" con TRATO_SIN_EVIDENCIA, CORTE_ROJO y CONVERSION_NIVEL_0_1 como pendientes
    Y muestra 1 aviso "PUNTAJE_MAXIMO_DISTINTO en el PI 5.3" y 0 rechazos de fila
    Y muestra el inicio y el fin en hora de Lima, iguales a carga.iniciada_en y carga.terminada_en, con el fin posterior al inicio
    Y muestra "Subido por docente410@example.invalid"
    Y muestra la frase fija "Los números de este R-17 los calcula el sistema desde la carga registrada en la base, no desde fórmulas."

  @US-16 @corte1
  Escenario: La constancia en JSON dice lo mismo que la hoja
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el profesor pide la constancia de esa carga
    Entonces la respuesta es 200 y su cuerpo es igual al cuerpo de la respuesta 201 de la subida
    Y el cuerpo trae carga_id, estado "PUBLICADA", nombre_archivo "sintetico_20262_450002_410.xlsx", hoja "gc_SINTETICO_20262_450002_410_f", sha256 igual a archivo_origen.sha256, filas_de_datos 11, filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y el cuerpo trae conjunto_reglas "R-2026-BORRADOR", provisional verdadero y 1 aviso con motivo "PUNTAJE_MAXIMO_DISTINTO" y PI "5.3"

  @US-16 @corte1
  Escenario: Constancia del export con el 5 en la fila 3
    Dado que "export_inventado_410_con_error.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el profesor descarga el R-17 de esa carga
    Entonces la hoja "Constancia" muestra ese carga_id, que es el carga_id de las filas de abet.v_r17_por_pi con que se llenó el bloque II
    Y muestra el archivo "export_inventado_410_con_error.xlsx", la hoja "gc_SINTETICO_20262_450002_410_f" y la huella igual a archivo_origen.sha256
    Y muestra "11 / 11 / 10 / 1"
    Y muestra el rechazo "Fila 3, PI 5.2, NIVEL_FUERA_DE_ESCALA, RECHAZA_FILA" y el aviso "PUNTAJE_MAXIMO_DISTINTO en el PI 5.3"
    Pero la fila del rechazo no muestra el valor leído de la celda
    Y la hoja "Constancia" no contiene ningún apellido ni nombre de las columnas Last Name y First Name del export

  # La constancia de una carga RECHAZADA se arma de abet.carga, abet.archivo_origen y abet.rechazo_fila.
  @US-16 @corte1
  Escenario: Una carga rechazada también tiene constancia
    Dado que una copia de "sintetico_20262_450002_410.xlsx" sin la columna 5.2 está subida a la sección 410 con respuesta 201, estado "RECHAZADA" y su carga_id
    Cuando el profesor pide la constancia de esa carga
    Entonces la respuesta es 200 y su cuerpo trae estado "RECHAZADA", filas_de_datos 11, filas_leidas 0, filas_aceptadas 0 y filas_rechazadas 0
    Y el cuerpo trae 1 rechazo con motivo "PI_DEL_PLAN_AUSENTE" y efecto "RECHAZA_CARGA"
    Y el sha256 del cuerpo es igual a archivo_origen.sha256 de esa carga

  @US-16 @corte1
  Esquema del escenario: La constancia de la 410 según quién la pide
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que "<correo>" tiene la sesión iniciada con rol "<rol>"
    Cuando "<correo>" pide la constancia de esa carga
    Entonces la respuesta es <estado>

    Ejemplos:
      | correo                       | rol         | estado |
      | coordinacion@example.invalid | COORDINADOR | 200    |
      | docente411@example.invalid   | PROFESOR    | 403    |
