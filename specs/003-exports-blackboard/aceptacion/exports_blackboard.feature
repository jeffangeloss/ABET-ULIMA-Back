# language: es
#
# Escenarios de aceptación del export real de Blackboard en .xlsx, .csv y .xls (spec 003, US-26 a US-36).
# Todos los datos son inventados. Los cuatro exports nuevos viven en tests/datos_inventados/ y los genera
# scripts/generar_exports_inventados.py con los 31 encabezados del export real, los títulos reales de las
# actividades y números de columna de Blackboard inventados que empiezan con 9. Las cifras salen de
# db/pruebas/datos_sinteticos.sql, como en la spec 001.
#
# Vocabulario de los pasos, además del de specs/001-mvp-carga-r17/aceptacion/carga.feature.
# - «el .csv inventado de la 410» es gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv, en
#   UTF-8 con BOM, separado por comas, con comillas dobles en todos los campos, saltos LF y niveles «N.00».
# - «el .xls inventado de la 410» es gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls, el
#   mismo contenido en UTF-16 LE con BOM, separado por tabuladores, y «el .xls inventado de la 411» es
#   gc_SINTETICO_20262_450002_411_fullgc_2026-11-04-14-40-10.xls, con los códigos 99000012 a 99000022.
# - «el .xlsx inventado con los encabezados reales» es gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-36-02.xlsx,
#   con la hoja gc_SINTETICO_20262_450002_410_f y los niveles como números.
# - «una copia de X con ...» arma la copia en tmp_path con las funciones del generador y cambia solo lo
#   que dice la frase. Cada escenario, y cada fila de un esquema, corre en su propia base desechable, así
#   que dos copias con los mismos bytes no comparten huella entre escenarios.
# - «el registro» es el logger abet.api de la API, que la prueba lee con caplog.
# - «los 5 avisos» son PUNTAJE_MAXIMO_DISTINTO en 5.1, 5.2 y 5.3, que declaran 100 puntos, y dos
#   COLUMNA_PI_FUERA_DEL_PLAN, de «ABET SO 4.1» y «ABET SO4.2», con pi_id y carga_columna_id nulos,
#   porque ck_rechazo_fila_pi no guarda el PI de ese motivo.

Característica: El export real de Blackboard en .xlsx, .csv y .xls
  Como profesor de Ingeniería Ambiental, quiero subir el export de mi sección tal como lo descarga
  Blackboard, en .xlsx, .csv o .xls, para que sus niveles lleguen a la base sin abrirlo ni convertirlo.

  Antecedentes:
    Dado una base PostgreSQL 18 desechable con las migraciones V1_01 a V1_10 y los datos de db/datos/periodo_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y plan_medicion registra los PI 5.1, 5.2 y 5.3 para la asignatura "450002" en "2026-2"
    Y "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR" y acceso.docente_seccion le asigna la sección 410 de "450002" en "2026-2"
    Y la sección 410 no tiene ninguna carga

  # US-26: Reconocer las columnas de PI con sus encabezados reales, en el lector y en la base

  @US-26 @corte1 @spec003
  Escenario: El .xlsx con los encabezados reales queda publicado
    Cuando el profesor sube "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-36-02.xlsx" a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y abet.medicion tiene 33 filas de esa carga
    Y abet.carga_columna tiene 3 filas de esa carga, de los PI 5.1, 5.2 y 5.3
    Y la columna del PI 5.1 guarda el encabezado "ABET SO5.1 [Total Pts: 100 Score] |9000051", bb_columna_id "9000051" y puntaje_maximo_declarado 100.00
    Y la columna del PI 5.3 guarda el encabezado "ABET SO 5.3 [Total Pts: 100 Score] |9000053"
    Y abet.rechazo_fila tiene los 5 avisos de esa carga y ningún rechazo de fila

  @US-26 @corte1 @spec003
  Esquema del escenario: Los exports de la spec 001 dan las mismas cifras con el lector nuevo
    Cuando el profesor sube "<archivo>" a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas <aceptadas> y filas_rechazadas <rechazadas>
    Y abet.v_r17_por_pi de esa carga da pct_logro_sobre_calificados <porcentajes>

    Ejemplos:
      | archivo                              | aceptadas | rechazadas | porcentajes                         |
      | sintetico_20262_450002_410.xlsx      | 11        | 0          | 63,6 en 5.1, 63,6 en 5.2 y 72,7 en 5.3 |
      | export_inventado_410_con_error.xlsx  | 10        | 1          | 60,0 en 5.1, 60,0 en 5.2 y 70,0 en 5.3 |

  @US-26 @corte1 @spec003
  Esquema del escenario: Qué encabezados son de un PI
    Dado el encabezado "<encabezado>"
    Entonces el lector lo clasifica como <tipo> con el código "<pi>"

    Ejemplos:
      | encabezado                                                                               | tipo | pi   |
      | ABET SO5.1 [Total Pts: 100 Score] \|9000051                                              | PI   | 5.1  |
      | ABET SO 5.3 [Total Pts: 100 Score] \|9000053                                             | PI   | 5.3  |
      | abet so 5.2 [Total Pts: 100 Score] \|9000052                                             | PI   | 5.2  |
      | SO 5.1 [Total Pts: 4 Score] \|9000051                                                    | PI   | 5.1  |
      | PI 5.1 [Total Pts: 4 Score] \|9000051                                                    | PI   | 5.1  |
      | 5.1 [Total Pts: 4 Score] \|9000051                                                       | PI   | 5.1  |
      | 5.1[Total Pts: 4 Score] \|9000051                                                        | PI   | 5.1  |
      | ABET SO 5.10 [Total Pts: 100 Score] \|9000051                                            | PI   | 5.10 |
      | ABET SO 5.1                                                                              | OTRA |      |
      | ABET SO5 [Total Pts: 100 Score] \|9000051                                                | OTRA |      |
      | ABET    SO 5.1 [Total Pts: 100 Score] \|9000051                                          | OTRA |      |
      | Actividad 5.1 [Total Pts: 4 Score] \|9000051                                             | OTRA |      |
      | 9. Casos de Circularidad [Total Pts: 100 Score] \|9000099                                | OTRA |      |
      | 7. Ejercicio en clase: Conceptos y Métricas LCA (10 ejercicios) [Total Pts: 20 Score] \|9000098 | OTRA |      |

  @US-26 @corte1 @spec003
  Esquema del escenario: La base acepta o rechaza el encabezado de la columna del PI 5.1
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201
    Cuando el dueño de la base cambia el encabezado de la columna del PI 5.1 de esa carga a "<encabezado>"
    Entonces <resultado>

    Ejemplos:
      | encabezado                                     | resultado                                                              |
      | ABET SO5.1 [Total Pts: 100 Score] \|9000051    | la base acepta el cambio                                               |
      | ABET SO 5.1 [Total Pts: 100 Score] \|9000051   | la base acepta el cambio                                               |
      | abet so 5.1 [Total Pts: 100 Score] \|9000051   | la base acepta el cambio                                               |
      | PI 5.1 [Total Pts: 4 Score] \|9000051          | la base acepta el cambio                                               |
      | 5.1[Total Pts: 4 Score] \|9000051              | la base acepta el cambio                                               |
      | ABET SO 5.10 [Total Pts: 100 Score] \|9000051  | la base rechaza el cambio por la restricción "ck_carga_columna_encabezado" |
      | 5.10 [Total Pts: 4 Score] \|9000051            | la base rechaza el cambio por la restricción "ck_carga_columna_encabezado" |
      | Actividad 5.1 [Total Pts: 4 Score] \|9000051   | la base rechaza el cambio por la restricción "ck_carga_columna_encabezado" |

  @US-26 @corte1 @spec003
  Escenario: El lector y la base aceptan los mismos encabezados
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201
    Cuando cada encabezado de la lista común de tests/encabezados_de_pi.py se prueba en la columna del PI 5.1 de esa carga, dentro de una transacción que se deshace
    Entonces la base acepta cada encabezado que el lector clasifica como el PI 5.1 y rechaza todos los demás

  @US-26 @corte1 @spec003
  Escenario: Dos columnas del mismo PI con distinta escritura rechazan la carga
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" con una segunda columna "ABET SO 5.1 [Total Pts: 100 Score] |9000061"
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "RECHAZADA" y el mensaje "El PI 5.1 aparece en dos columnas del archivo."
    Y la carga queda en estado "RECHAZADA" con filas_leidas 0, filas_aceptadas 0, filas_rechazadas 0 y terminada_en no nulo
    Y abet.rechazo_fila tiene exactamente 1 fila de esa carga, con motivo "PI_REPETIDO", efecto "RECHAZA_CARGA", fila_origen nulo y carga_columna_id nulo
    Y esa fila guarda en pi_id el PI 5.1
    Y abet.carga_columna, abet.carga_fila y abet.medicion no tienen filas de esa carga

  @US-26 @corte1 @spec003
  Escenario: Las columnas del SO 4 se ignoran con aviso y sin leer sus valores
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" con "75" en la columna "ABET SO 4.1" y "Needs Grading" en la columna "ABET SO4.2" de la fila 3
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y abet.rechazo_fila tiene 2 filas COLUMNA_PI_FUERA_DEL_PLAN de esa carga, con efecto "AVISO" y fila_origen, carga_columna_id y pi_id nulos
    Y abet.carga_columna de esa carga solo tiene los PI 5.1, 5.2 y 5.3

  # US-27: Cargar el .csv de Blackboard tal como se descarga

  @US-27 @corte1 @spec003
  Escenario: El .csv inventado de la 410 queda publicado entero
    Cuando el profesor sube "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y abet.archivo_origen tiene 1 fila con nombre_archivo "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv", hoja nula, filas_de_datos 11 y tipo_fuente "BLACKBOARD_EXPORT"
    Y abet.carga_columna tiene 3 filas de esa carga, de los PI 5.1, 5.2 y 5.3
    Y abet.medicion tiene 33 filas de esa carga
    Y abet.v_r17_por_pi de esa carga da pct_logro_sobre_calificados 63,6 en 5.1, 63,6 en 5.2 y 72,7 en 5.3
    Y abet.rechazo_fila tiene los 5 avisos de esa carga y ningún rechazo de fila
    Y las consultas de control Q01, Q02, Q03, Q04, Q05, Q06, Q07, Q08, Q09, Q10, Q11, Q12, Q13 y Q14 devuelven 0 filas

  @US-27 @corte1 @spec003
  Esquema del escenario: Las variantes del texto del .csv se leen igual
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" <variante>
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y abet.medicion tiene 33 filas de esa carga

    Ejemplos:
      | variante                                          |
      | con saltos de línea CRLF                          |
      | sin BOM                                           |
      | con dos líneas vacías al final                    |
      | sin comillas en ningún campo                      |
      | con tabuladores en lugar de comas                 |
      | con la columna Username primero                   |
      | con el nombre "GC_SINTETICO_20262_450002_410_FULLGC_2026-11-04-14-35-59.CSV" |

  @US-27 @corte1 @spec003
  Escenario: Una línea vacía entre filas con datos cuenta como fila
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" con una línea vacía después de la línea 4 del archivo
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 12, filas_aceptadas 11 y filas_rechazadas 1
    Y archivo_origen.filas_de_datos es 12
    Y el cuerpo de la respuesta trae el rechazo con fila 5, PI "", motivo "CODIGO_VACIO"
    Y abet.carga_fila tiene 11 filas de esa carga y ninguna con fila_origen 5

  @US-27 @corte1 @spec003
  Escenario: Un salto de línea dentro de comillas no cambia la numeración
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" con un salto de línea dentro de las comillas de Last Name en la fila 3 y "3.50" en la columna 5.2 de la fila 4
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 10 y filas_rechazadas 1
    Y el cuerpo de la respuesta trae el rechazo con fila 4, PI "5.2", motivo "NIVEL_NO_NUMERICO"

  @US-27 @corte1 @spec003
  Esquema del escenario: Un defecto de estructura en el .csv rechaza la carga entera
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" <defecto>
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "RECHAZADA" y el mensaje "<mensaje>"
    Y la carga queda en estado "RECHAZADA" con filas_leidas 0, filas_aceptadas 0, filas_rechazadas 0 y terminada_en no nulo
    Y abet.rechazo_fila tiene exactamente 1 fila de esa carga, con motivo "<motivo>", efecto "RECHAZA_CARGA", fila_origen nulo y carga_columna_id nulo

    Ejemplos:
      | defecto                                  | motivo                 | mensaje                                                                     |
      | con el encabezado y ninguna fila de datos | ARCHIVO_SIN_FILAS      | El archivo no trae filas de estudiantes.                                    |
      | sin las columnas Username ni Student ID  | COLUMNA_CODIGO_AUSENTE | El archivo no tiene la columna Username ni Student ID.                      |
      | sin la columna del PI 5.2                | PI_DEL_PLAN_AUSENTE    | Falta la columna del PI 5.2 que el plan de medición pide para esta sección. |

  @US-27 @corte1 @spec003
  Escenario: Un código que no es inventado en el .csv detiene el archivo
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" con el Username 10000004 en la fila 4
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 422 con detail "El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada."
    Y abet.archivo_origen, abet.carga, abet.carga_columna, abet.carga_fila, abet.medicion, abet.rechazo_fila y abet.estudiante no ganan ninguna fila
    Y el cuerpo de la respuesta no contiene el texto "10000004"

  @US-27 @corte1 @spec003
  Escenario: La huella del .csv incluye su BOM
    Cuando el profesor sube "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" a la sección 410
    Entonces archivo_origen.sha256 cumple "^[0-9a-f]{64}$" y es igual a la salida de "shasum -a 256" sobre tests/datos_inventados/gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv
    Y la huella de la copia sin BOM es distinta de archivo_origen.sha256 de la carga publicada

  @US-27 @corte1 @spec003
  Escenario: El mismo .csv otra vez devuelve su constancia
    Dado que "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el profesor sube los mismos bytes con el nombre "copia de notas 410.csv" a la sección 410
    Entonces la respuesta es 200 y su cuerpo es la constancia de ese mismo carga_id, en estado "PUBLICADA"
    Y abet.archivo_origen sigue con 1 fila para esa huella
    Y archivo_origen.nombre_archivo sigue siendo "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv"

  @US-27 @corte1 @spec003
  Escenario: El mismo .csv publicado en la 410 no entra en la 411
    Dado que "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que "docente411@example.invalid" tiene la sesión iniciada con rol "PROFESOR" y acceso.docente_seccion le asigna la sección 411 de "450002" en "2026-2"
    Cuando "docente411@example.invalid" sube los mismos bytes con el nombre "gc_SINTETICO_20262_450002_411_fullgc_2026-11-04-14-35-59.csv" a la sección 411
    Entonces la respuesta es 409 con detail "Este archivo ya está publicado en otra sección. No se cargó."
    Y el cuerpo de la respuesta no contiene ese carga_id, la huella del archivo ni el número de la sección 410

  # US-28: Cargar el .xls de texto de Blackboard

  @US-28 @corte1 @spec003
  Escenario: El .xls de texto inventado de la 410 queda publicado entero
    Cuando el profesor sube "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls" a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y abet.archivo_origen tiene 1 fila con nombre_archivo "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls", hoja nula, filas_de_datos 11 y tipo_fuente "BLACKBOARD_EXPORT"
    Y abet.medicion tiene 33 filas de esa carga
    Y abet.v_r17_por_pi de esa carga da pct_logro_sobre_calificados 63,6 en 5.1, 63,6 en 5.2 y 72,7 en 5.3
    Y abet.rechazo_fila tiene los 5 avisos de esa carga y ningún rechazo de fila
    Y archivo_origen.sha256 es distinta de la huella de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv"

  @US-28 @corte1 @spec003
  Esquema del escenario: Las variantes del .xls se leen igual
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls" <variante>
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0

    Ejemplos:
      | variante                                                                       |
      | con saltos de línea CRLF                                                       |
      | con comas en lugar de tabuladores                                              |
      | con el nombre "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.XLS"   |
      | con el nombre "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xlsx"  |

  @US-28 @corte1 @spec003
  Escenario: El .xls con las mismas notas que el .csv es otro archivo
    Dado que "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" está subido a la sección 410 con respuesta 201
    Cuando el profesor sube "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls" a la sección 410
    Entonces la respuesta es 409 con detail "La sección 410 ya tiene una carga publicada. No se cargó el archivo."
    Y abet.archivo_origen no gana ninguna fila

  @US-28 @corte1 @spec003
  Escenario: Un código que no es inventado en el .xls detiene el archivo
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls" con el Username 10000004 en la fila 4
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 422 con detail "El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada."
    Y abet.archivo_origen, abet.carga, abet.carga_columna, abet.carga_fila, abet.medicion, abet.rechazo_fila y abet.estudiante no ganan ninguna fila

  @US-28 @corte1 @spec003
  Escenario: Los nombres y las actividades del .xls no llegan a ninguna tabla
    Dado que "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls" está subido a la sección 410 con respuesta 201
    Entonces la consulta de control Q04 devuelve 0 filas
    Y una búsqueda con igualdad exacta de "Estudiante", "Inventado 01" a "Inventado 11", "Complete", "Incomplete", "Needs Grading" y "19.00" en las columnas de texto de las tablas de abet que escribe la carga y de acceso devuelve 0 coincidencias

  # US-29: Leer el nivel que Blackboard escribe con decimales nulos

  @US-29 @corte1 @spec003
  Esquema del escenario: El texto de un nivel en el PI 5.2 de la fila 3
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" cuya columna 5.2 trae "<valor>" entre comillas en la fila 3
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas <aceptadas> y filas_rechazadas <rechazadas>
    Y abet.medicion tiene <mediciones> filas de esa carga
    Y abet.v_r17_por_pi de esa carga da pct_logro_sobre_calificados <porcentajes>
    Y <resultado>

    Ejemplos:
      | valor         | aceptadas | rechazadas | mediciones | porcentajes                            | resultado                                                                                  |
      | 3.00          | 11        | 0          | 33         | 63,6 en 5.1, 63,6 en 5.2 y 72,7 en 5.3 | la medición de 99000002 en el PI 5.2 tiene estado_evidencia "CALIFICADO" y nivel_original 3 |
      | 3,00          | 11        | 0          | 33         | 63,6 en 5.1, 63,6 en 5.2 y 72,7 en 5.3 | la medición de 99000002 en el PI 5.2 tiene estado_evidencia "CALIFICADO" y nivel_original 3 |
      | 4.0           | 11        | 0          | 33         | 63,6 en 5.1, 63,6 en 5.2 y 72,7 en 5.3 | la medición de 99000002 en el PI 5.2 tiene estado_evidencia "CALIFICADO" y nivel_original 4 |
      | 3.50          | 10        | 1          | 30         | 60,0 en 5.1, 60,0 en 5.2 y 70,0 en 5.3 | el cuerpo de la respuesta trae el rechazo con fila 3, PI "5.2", motivo "NIVEL_NO_NUMERICO"     |
      | 1,000         | 10        | 1          | 30         | 60,0 en 5.1, 60,0 en 5.2 y 70,0 en 5.3 | el cuerpo de la respuesta trae el rechazo con fila 3, PI "5.2", motivo "NIVEL_NO_NUMERICO"     |
      | Needs Grading | 10        | 1          | 30         | 60,0 en 5.1, 60,0 en 5.2 y 70,0 en 5.3 | el cuerpo de la respuesta trae el rechazo con fila 3, PI "5.2", motivo "NIVEL_NO_NUMERICO"     |
      | 0.00          | 10        | 1          | 30         | 60,0 en 5.1, 60,0 en 5.2 y 70,0 en 5.3 | el cuerpo de la respuesta trae el rechazo con fila 3, PI "5.2", motivo "NIVEL_FUERA_DE_ESCALA" |
      | 19.00         | 10        | 1          | 30         | 60,0 en 5.1, 60,0 en 5.2 y 70,0 en 5.3 | el cuerpo de la respuesta trae el rechazo con fila 3, PI "5.2", motivo "NIVEL_FUERA_DE_ESCALA" |
      | 75            | 10        | 1          | 30         | 60,0 en 5.1, 60,0 en 5.2 y 70,0 en 5.3 | el cuerpo de la respuesta trae el rechazo con fila 3, PI "5.2", motivo "NIVEL_FUERA_DE_ESCALA" |

  @US-29 @corte1 @spec003
  Esquema del escenario: El texto de un nivel dentro de un .xlsx
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-36-02.xlsx" cuya columna 5.2 trae el texto "<valor>" en la fila 3
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas <aceptadas> y filas_rechazadas <rechazadas>

    Ejemplos:
      | valor | aceptadas | rechazadas |
      | 3.00  | 11        | 0          |
      | 3,00  | 11        | 0          |
      | 3.50  | 10        | 1          |

  @US-29 @corte1 @spec003
  Escenario: Un nivel con miles de cifras no deja la carga en 500
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" cuya columna 5.2 trae un texto de 5000 cifras en la fila 3
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 10 y filas_rechazadas 1
    Y el cuerpo de la respuesta trae el rechazo con fila 3, PI "5.2", motivo "NIVEL_FUERA_DE_ESCALA"

  # US-30: Cotejar la sección con el nombre del export de texto

  @US-30 @corte1 @spec003
  Esquema del escenario: La sección sale del nombre del archivo de texto
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" con el nombre "<nombre>"
    Cuando el profesor sube esa copia a la sección 410
    Entonces <resultado>

    Ejemplos:
      | nombre                                                             | resultado                                                                                                                                                   |
      | gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59 (1).csv   | la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0                                         |
      | gc_OTRO_PREFIJO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv    | la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0                                         |
      | gc_SINTETICO_20262_450002_411_fullgc_2026-11-04-14-35-59.csv       | la respuesta es 201 y su cuerpo trae estado "RECHAZADA" y el mensaje "El archivo corresponde a la sección 411 y usted eligió la 410. No se publicó."       |
      | gc_SINTETICO_20261_450002_410_fullgc_2026-11-04-14-35-59.csv       | la respuesta es 201 y su cuerpo trae estado "RECHAZADA" y el mensaje "El archivo corresponde al periodo 2026-1 y la sección elegida es de 2026-2. No se publicó." |
      | gc_SINTETICO_20262_450010_410_fullgc_2026-11-04-14-35-59.csv       | la respuesta es 201 y su cuerpo trae estado "RECHAZADA" y el mensaje "El archivo corresponde a la asignatura 450010 y usted eligió la 450002. No se publicó." |
      | notas 410.csv                                                      | la respuesta es 422 con detail "El archivo no indica su sección. Suba el export de Blackboard sin cambiar el nombre del archivo ni el de su hoja."          |

  @US-30 @corte1 @spec003
  Escenario: Un .xlsx sin sección en la hoja ni en el nombre recibe el texto nuevo
    Dado una copia de "sintetico_20262_450002_410.xlsx" con la hoja renombrada "Hoja1" y el nombre "notas.xlsx"
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 422 con detail "El archivo no indica su sección. Suba el export de Blackboard sin cambiar el nombre del archivo ni el de su hoja."
    Y abet.archivo_origen, abet.carga, abet.rechazo_fila y abet.estudiante no ganan ninguna fila

  # US-31: Saber por qué no se admite un archivo

  @US-31 @corte1 @spec003
  Esquema del escenario: Un archivo que no es un export admitido se detiene sin rastro
    Dado <archivo>
    Cuando el profesor sube ese archivo a la sección 410
    Entonces la respuesta es 422 con detail "<mensaje>"
    Y abet.archivo_origen, abet.carga, abet.rechazo_fila y abet.estudiante no ganan ninguna fila
    Y ninguna carga queda en estado "EN_CURSO"
    Y el registro trae "evento=archivo_detenido" con la huella, "motivo=<motivo>" y "detalle=<detalle>", sin el nombre del archivo

    Ejemplos:
      | archivo                                                                   | motivo                   | detalle      | mensaje                                                                                              |
      | un PDF inventado de una página con el nombre "export_410.pdf"             | TIPO_NO_ADMITIDO         | -            | Solo se admiten exports de Blackboard en formato .xlsx, .csv o .xls.                                 |
      | el mismo PDF con el nombre "export_410.xlsx"                              | CONTENIDO_NO_ES_LIBRO    | -            | El contenido del archivo no es un export de Blackboard aunque su nombre termine en .xlsx, .csv o .xls. |
      | el mismo PDF con el nombre "export_410.csv"                               | NO_SE_PUDO_ABRIR         | CODIFICACION | No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard.                                  |
      | un contenedor OLE inventado sin cifrado con el nombre "export_410.xls"    | CONTENIDO_NO_ES_LIBRO    | -            | El contenido del archivo no es un export de Blackboard aunque su nombre termine en .xlsx, .csv o .xls. |
      | una copia de "protegido_410.xlsx" con el nombre "export_410.xls"          | PROTEGIDO_CON_CONTRASENA | -            | El archivo está protegido con contraseña. Guárdelo sin contraseña y súbalo.                          |
      | un zip inventado que no es un libro con el nombre "export_410.csv"        | CONTENIDO_NO_ES_LIBRO    | -            | El contenido del archivo no es un export de Blackboard aunque su nombre termine en .xlsx, .csv o .xls. |
      | un archivo vacío con el nombre "export_410.csv"                           | NO_SE_PUDO_ABRIR         | VACIO        | No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard.                                  |

  # US-32: Detener un export de texto dañado sin dejar rastro

  @US-32 @corte1 @spec003
  Esquema del escenario: Un texto dañado o armado a mano se detiene sin rastro
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" <defecto>
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 422 con detail "No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard."
    Y abet.archivo_origen, abet.carga, abet.rechazo_fila y abet.estudiante no ganan ninguna fila
    Y el registro trae "evento=archivo_detenido" con la huella, "motivo=NO_SE_PUDO_ABRIR" y "detalle=<detalle>", sin el nombre del archivo

    Ejemplos:
      | defecto                                              | detalle       |
      | en Windows-1252                                      | CODIFICACION  |
      | en UTF-16 BE con BOM                                 | CODIFICACION  |
      | con dos BOM al comienzo                              | CODIFICACION  |
      | en UTF-16 LE sin BOM                                 | CARACTER_NULO |
      | con un carácter U+0000 en el Last Name de la fila 3  | CARACTER_NULO |
      | con solo el BOM                                      | VACIO         |
      | con una primera línea sin coma ni tabulador          | SEPARADOR     |
      | separada por punto y coma                            | SEPARADOR     |
      | sin la última comilla del archivo                    | COMILLAS      |
      | con un campo de 131073 caracteres en la fila 3       | CAMPO_LARGO   |
      | con una fila 1 de 16385 columnas                     | COLUMNAS      |
      | con 5001 filas de datos                              | FILAS         |

  @US-32 @corte1 @spec003
  Esquema del escenario: El orden de BR-CARGA-03 se mantiene con un export de texto
    Dado <archivo>
    Cuando el profesor sube ese archivo a la sección 410
    Entonces la respuesta es 422 con detail "<mensaje>"
    Y abet.archivo_origen, abet.carga, abet.rechazo_fila y abet.estudiante no ganan ninguna fila

    Ejemplos:
      | archivo                                                                                                                                  | mensaje                                                                                          |
      | una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" de 1,2 MB sin la última comilla del archivo                 | El archivo supera el máximo de 1 MB.                                                             |
      | una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" con el Username 10000004 en la fila 4 y sin la última comilla del archivo | No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard.                    |

  @US-32 @corte1 @spec003
  Escenario: La guardia va antes que la carga publicada de la sección
    Dado que "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls" está subido a la sección 410 con respuesta 201
    Y una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" con el Username 10000004 en la fila 4
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 422 con detail "El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada."

  # US-33: Elegir el .csv o el .xls en la pantalla de subida
  # Se prueba en el Front, en tests/pantallas/SubirExport.test.tsx; aquí queda como criterio escrito.

  @US-33 @corte1 @spec003 @delegado_a_vitest
  Escenario: El selector de P3 admite los tres formatos
    Dado que el profesor abre P3 de la sección 410
    Entonces el campo "archivo" tiene accept ".xlsx,.csv,.xls" y la etiqueta "Export de Blackboard (.xlsx, .csv o .xls, hasta 1 MB)"

  @US-33 @corte1 @spec003 @delegado_a_vitest
  Escenario: Sin archivo, P3 pide el export en los tres formatos
    Dado que el profesor abre P3 de la sección 410
    Cuando pulsa "Subir" sin elegir un archivo
    Entonces P3 muestra "Elija el archivo del export (.xlsx, .csv o .xls)." y no llama a la API

  @US-33 @corte1 @spec003 @delegado_a_vitest
  Escenario: P3 envía el archivo tal cual y la API decide
    Dado que el profesor abre P3 de la sección 410
    Cuando elige "export_410.pdf" sin el filtro del diálogo y pulsa "Subir"
    Entonces P3 envía ese archivo una vez con su nombre y muestra el detail del 422 de la API

  # US-34: Ver la constancia de un export sin hoja

  @US-34 @corte1 @spec003
  Escenario: La constancia del .csv no inventa una hoja
    Dado que "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el profesor pide la constancia de esa carga y descarga su R-17
    Entonces el cuerpo de la constancia trae hoja nula y nombre_archivo "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv"
    Y la hoja "Constancia" del R-17 muestra en la fila "Hoja" el texto "Sin hoja (export de texto)"

  @US-34 @corte1 @spec003
  Escenario: La constancia del .xlsx sigue mostrando su hoja
    Dado que "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-36-02.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el profesor pide la constancia de esa carga y descarga su R-17
    Entonces el cuerpo de la constancia trae hoja "gc_SINTETICO_20262_450002_410_f"
    Y la hoja "Constancia" del R-17 muestra en la fila "Hoja" el texto "gc_SINTETICO_20262_450002_410_f"

  # US-35: Revisar por contenido los datos inventados antes de versionarlos
  # Se prueba en scripts/probar_preflight.sh, que corre en la CI antes de pytest; aquí queda como criterio escrito.

  @US-35 @corte1 @spec003 @delegado_a_preflight
  Escenario: La revisión previa lee el contenido antes de contar los códigos
    Dado en tests/datos_inventados/ un .xls UTF-16 con BOM, un .csv UTF-16, un .csv UTF-8, un texto en Windows-1252 y un .txt, cada uno con el código 20231234, y un .xls que es un contenedor OLE
    Cuando corre "bash scripts/preflight.sh --staged" con cada uno
    Entonces cada corrida falla por la regla 2 sin mostrar el código, y el mismo .xls UTF-16 con los códigos 99000001 y 99000002 pasa

  # US-36: No publicar un export sin ningún nivel en los PI del plan

  @US-36 @corte1 @spec003
  Escenario: Un export sin ningún nivel en los PI del plan no se publica
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" con las columnas 5.1, 5.2 y 5.3 vacías en sus 11 filas
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "RECHAZADA" y el mensaje "El archivo no trae ningún nivel en las columnas de los PI del plan. La carga no se publicó."
    Y la carga queda en estado "RECHAZADA" con filas_leidas 0, filas_aceptadas 0, filas_rechazadas 0 y terminada_en no nulo
    Y abet.rechazo_fila tiene exactamente 1 fila de esa carga, con motivo "SIN_CALIFICACIONES", efecto "RECHAZA_CARGA", fila_origen nulo y carga_columna_id nulo
    Y abet.carga_columna, abet.carga_fila y abet.medicion no tienen filas de esa carga
    Y la sección 410 no tiene ninguna carga "PUBLICADA"

  @US-36 @corte1 @spec003
  Escenario: Un solo nivel basta para publicar
    Dado una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" con las columnas 5.1, 5.2 y 5.3 vacías en sus 11 filas salvo "3.00" en la columna 5.1 de la fila 2
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y abet.medicion tiene 33 filas de esa carga, 1 con estado_evidencia "CALIFICADO" y 32 con "SIN_EVIDENCIA"

  @US-36 @corte1 @spec003
  Escenario: La sección queda libre para el export con niveles
    Dado que una copia de "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" con las columnas 5.1, 5.2 y 5.3 vacías en sus 11 filas está subida a la sección 410 y su carga está "RECHAZADA" con SIN_CALIFICACIONES
    Cuando el profesor sube "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv" a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
