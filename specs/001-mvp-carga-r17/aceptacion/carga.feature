# language: es
#
# Escenarios de aceptación de la carga del export (spec 001, historias US-07 a US-14 y US-21).
# Todos los datos son inventados. Los archivos viven en tests/datos_inventados/ y los correos usan el
# dominio reservado example.invalid. Las cifras salen de bd/pruebas/datos_sinteticos.sql.
#
# Vocabulario de los pasos.
# - «subir X a la sección N» es POST /api/secciones/{seccion_id de N}/cargas con X en el campo
#   multipart «archivo», con la cookie abet_sesion de quien tiene la sesión iniciada.
# - «la respuesta» es la respuesta HTTP de esa petición; los errores traen { "detail": "mensaje" }.
# - «no gana ninguna fila» compara el conteo de la tabla antes y después de la petición.
# - «una copia de X con ...» es un libro que la prueba arma desde X y cambia solo lo que se dice.
# - Cada escenario corre en una base desechable propia, así que los carga_id se capturan de la respuesta
#   y nunca se suponen.
# - El export correcto sintetico_20262_450002_410.xlsx (por crear) es una copia de
#   export_inventado_410_con_error.xlsx con un 3 en la columna 5.2 de la fila 3, el nivel de 99000002.
# - export_inventado_411.xlsx (por crear) tiene la hoja gc_SINTETICO_20262_450002_411_f y los códigos
#   99000012 a 99000022, para que la consulta de control Q08 no vea a un estudiante en dos secciones.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Carga del export de Blackboard en la base
  Como profesor de Ingeniería Ambiental, quiero subir el export de Blackboard de mi sección para que sus
  mediciones queden en la base en una sola transacción, con cada rechazo explicado y sin datos personales.

  Antecedentes:
    Dado una base PostgreSQL 16 desechable con las migraciones V1_01 a V1_09 y los datos de db/datos/periodo_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y plan_medicion registra los PI 5.1, 5.2 y 5.3 para la asignatura "450002" en "2026-2"
    Y "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR" y acceso.docente_seccion le asigna la sección 410 de "450002" en "2026-2"
    Y la sección 410 no tiene ninguna carga

  # US-07: Subir el export y cargarlo en una sola transacción

  @US-07 @corte1
  Escenario: El export correcto queda publicado entero
    Cuando el profesor sube "sintetico_20262_450002_410.xlsx" a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y abet.archivo_origen tiene 1 fila con nombre_archivo "sintetico_20262_450002_410.xlsx", hoja "gc_SINTETICO_20262_450002_410_f", filas_de_datos 11 y tipo_fuente "BLACKBOARD_EXPORT"
    Y archivo_origen.sha256 cumple "^[0-9a-f]{64}$" y es igual a la salida de "shasum -a 256" sobre tests/datos_inventados/sintetico_20262_450002_410.xlsx
    Y abet.carga tiene 1 fila de la sección 410 en estado "PUBLICADA" con filas_leidas 11, filas_aceptadas 11, filas_rechazadas 0 y el conjunto de reglas "R-2026-BORRADOR"
    Y carga.subida_por apunta a la fila de acceso.usuario_autorizado de "docente410@example.invalid"
    Y carga.terminada_en, que el programa fija con clock_timestamp() al cerrar la carga, es mayor que carga.iniciada_en
    Y abet.carga_columna tiene 3 filas de esa carga, con pi_codigo "5.1", "5.2" y "5.3" y puntaje_maximo_declarado 4, 4 y 20
    Y el encabezado guardado del PI 5.1 empieza por "5.1 [Total Pts: 4 Score]"
    Y abet.carga_fila tiene 11 filas de esa carga, de la fila_origen 2 a la 12
    Y abet.medicion tiene 33 filas de esa carga, todas con estado_evidencia "CALIFICADO" y nivel_original entre 1 y 4
    Y las consultas de control Q01, Q02, Q03, Q06, Q12 y Q13 devuelven 0 filas
    Y ninguna carga queda en estado "EN_CURSO"

  @US-07 @corte1 @inyeccion_de_fallos
  Esquema del escenario: Un fallo en cualquier punto de la transacción no deja nada escrito
    Dado que la prueba inyecta un fallo de conexión <punto>
    Cuando el profesor sube "sintetico_20262_450002_410.xlsx" a la sección 410
    Entonces la respuesta es 500 con detail "La carga no se completó y no se guardó ningún dato. Intente de nuevo."
    Y abet.archivo_origen, abet.carga, abet.carga_columna, abet.carga_fila, abet.medicion y abet.rechazo_fila no ganan ninguna fila
    Y abet.estudiante no gana ninguna fila
    Y ninguna carga queda en estado "EN_CURSO"

    Ejemplos:
      | punto                                              |
      | después de insertar la fila de abet.archivo_origen |
      | después de insertar las 3 filas de carga_columna   |
      | después de insertar la medición número 30          |
      | justo antes de cambiar el estado a PUBLICADA       |

  @US-07 @corte1 @inyeccion_de_fallos
  Escenario: Una restricción violada al final deshace la carga entera
    Dado que un defecto inyectado del programa intenta guardar el nivel 5 en la última medición
    Cuando el profesor sube "sintetico_20262_450002_410.xlsx" a la sección 410
    Entonces la base rechaza esa medición por la restricción "ck_medicion_nivel"
    Y la respuesta es 500 con detail "La carga no se completó y no se guardó ningún dato. Intente de nuevo."
    Y abet.carga no tiene ninguna fila de la sección 410
    Y abet.archivo_origen y abet.estudiante no ganan ninguna fila

  # El 409 se responde antes de escribir, y el corte 2 agrega el reemplazo (US-18). Que no se escriba
  # archivo_origen antes del 409 es una (propuesta).
  @US-07 @corte1
  Escenario: Otro archivo no entra en una sección que ya tiene carga publicada
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201
    Cuando el profesor sube "export_inventado_410_con_error.xlsx" a la sección 410
    Entonces la respuesta es 409 con detail "La sección 410 ya tiene una carga publicada. No se cargó el archivo."
    Y abet.archivo_origen y abet.carga no ganan ninguna fila
    Y la sección 410 sigue con 1 carga "PUBLICADA", la de "sintetico_20262_450002_410.xlsx", y sus 33 mediciones

  @US-07 @corte1
  Escenario: Un profesor no sube a una sección que no tiene asignada
    Cuando el profesor sube "export_inventado_411.xlsx" a la sección 411
    Entonces la respuesta es 403 con detail "La sección no está a su cargo."
    Y abet.archivo_origen, abet.carga y abet.estudiante no ganan ninguna fila

  # En el corte 1 solo sube el profesor asignado a la sección. El corte 2 deja al coordinador
  # reemplazar la carga de cualquier sección (US-18).
  @US-07 @corte1
  Escenario: El coordinador no sube en el corte 1
    Dado que "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando "coordinacion@example.invalid" sube "sintetico_20262_450002_410.xlsx" a la sección 410
    Entonces la respuesta es 403 con detail "La sección no está a su cargo."
    Y abet.archivo_origen, abet.carga y abet.estudiante no ganan ninguna fila

  # La transacción que llega segunda a publicar choca con el índice único parcial
  # uq_carga_publicada_por_seccion y se deshace entera.
  @US-07 @corte1
  Escenario: Dos subidas a la vez dejan una sola publicada
    Cuando el profesor envía a la vez a la sección 410 "sintetico_20262_450002_410.xlsx" y "export_inventado_410_con_error.xlsx"
    Entonces una de las respuestas es 201 con estado "PUBLICADA"
    Y la otra es 409 con detail "La sección 410 ya tiene una carga publicada. No se cargó el archivo."
    Y la sección 410 tiene 1 carga "PUBLICADA"
    Y abet.archivo_origen gana 1 sola fila
    Y ninguna carga queda en estado "EN_CURSO"

  # US-08: Rechazar exports con códigos que no son inventados

  # Con la guardia encendida, todo Username no vacío fuera de 99000000 a 99999999, incluido uno mal
  # formado como 9900001, detiene el archivo antes de calcular la huella o escribir. Por eso CODIGO_INVALIDO
  # solo se alcanza con la guardia apagada (escenario de US-10 con la etiqueta @guardia_apagada).
  @US-08 @corte1
  Esquema del escenario: Un solo código que no es inventado rechaza el archivo entero sin dejar rastro
    Dado una copia de "sintetico_20262_450002_410.xlsx" con el Username <codigo> en la fila 4
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 422 con detail "El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada."
    Pero el cuerpo de la respuesta no contiene el texto "<codigo>"
    Y abet.archivo_origen, abet.carga, abet.carga_columna, abet.carga_fila, abet.medicion, abet.rechazo_fila y abet.estudiante no ganan ninguna fila

    Ejemplos:
      | codigo   |
      | 10000004 |
      | 98999999 |
      | 9900001  |

  @US-08 @corte1
  Esquema del escenario: Los extremos del rango inventado pasan la guardia
    Dado una copia de "sintetico_20262_450002_410.xlsx" con el Username <codigo> en la fila 4
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y abet.estudiante tiene el código "<codigo>"

    Ejemplos:
      | codigo   |
      | 99000000 |
      | 99999999 |

  @US-08 @corte1
  Escenario: Ningún campo de la petición apaga la guardia
    Dado una copia de "sintetico_20262_450002_410.xlsx" con el Username 10000004 en la fila 4
    Cuando el profesor sube esa copia a la sección 410 con el campo multipart "guardia" igual a "0" y el parámetro de consulta "guardia=0"
    Entonces la respuesta es 422 con detail "El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada."
    Y abet.archivo_origen, abet.carga y abet.estudiante no ganan ninguna fila

  # Segunda barrera. El CHECK vive en el script de plataforma de Neon y la prueba lo aplica a su base
  # desechable.
  @US-08 @corte1 @guardia_en_base
  Escenario: La guardia de la base rechaza un código que no es inventado aunque el programa falle
    Dado que la base tiene aplicado db/plataforma/neon/guardia_datos_inventados.sql
    Y una conexión directa con el rol abet_app
    Cuando esa conexión inserta en abet.estudiante el código "10000004"
    Entonces la base rechaza la inserción por la restricción "ck_estudiante_codigo_inventado"
    Y abet.estudiante no tiene el código "10000004"

  # US-09: Reconocer un export ya cargado

  @US-09 @corte1
  Escenario: Subir otra vez el export publicado devuelve su constancia y no cambia nada
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el profesor sube otra vez "sintetico_20262_450002_410.xlsx" a la sección 410
    Entonces la respuesta es 200 y su cuerpo es la constancia de ese mismo carga_id, en estado "PUBLICADA"
    Y abet.archivo_origen sigue con 1 fila para esa huella
    Y abet.carga no gana ninguna fila
    Y abet.medicion y abet.v_tabla_maestra_pi siguen con 33 filas de la sección 410

  @US-09 @corte1
  Escenario: El mismo contenido con otro nombre se reconoce por la huella
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando el profesor sube los mismos bytes con el nombre "copia de notas 410.xlsx" a la sección 410
    Entonces la respuesta es 200 y su cuerpo es la constancia de ese mismo carga_id
    Y abet.archivo_origen no gana ninguna fila
    Y archivo_origen.nombre_archivo sigue siendo "sintetico_20262_450002_410.xlsx"

  # Depende del cotejo de sección de US-13. Una huella que solo tiene cargas RECHAZADA o REEMPLAZADA
  # reutiliza su archivo_id, lo que uq_carga_archivo_util permite porque solo limita las PUBLICADA.
  @US-09 @corte1
  Escenario: Un archivo rechazado en una sección se publica después en la suya
    Dado que "export_inventado_411.xlsx" está subido por "docente410@example.invalid" a la sección 410 y su carga está "RECHAZADA" con SECCION_NO_COINCIDE
    Y que "docente411@example.invalid" tiene la sesión iniciada con rol "PROFESOR" y acceso.docente_seccion le asigna la sección 411
    Cuando "docente411@example.invalid" sube "export_inventado_411.xlsx" a la sección 411
    Entonces la respuesta es 201 con estado "PUBLICADA"
    Y la carga nueva de la sección 411 usa el mismo archivo_id que la carga rechazada en la 410
    Y abet.archivo_origen sigue con 1 fila para esa huella
    Y la consulta de control Q08 devuelve 0 filas

  @US-09 @corte1
  Escenario: La base impide registrar dos veces la misma huella
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201
    Y una conexión directa con el rol abet_app
    Cuando esa conexión inserta en abet.archivo_origen otra fila con la misma sha256
    Entonces la base rechaza la inserción por la restricción "uq_archivo_origen_sha256"

  # La prueba abre la copia con openpyxl y la guarda otra vez, lo que cambia sus bytes como lo hace Excel.
  @US-09 @corte1
  Escenario: Un export abierto y guardado de nuevo es otro archivo
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201
    Y una copia de "sintetico_20262_450002_410.xlsx" abierta y guardada otra vez, con las mismas celdas y otros bytes
    Cuando el profesor sube esa copia a la sección 410
    Entonces la huella de la copia es distinta de archivo_origen.sha256 de la carga publicada
    Y la respuesta es 409 con detail "La sección 410 ya tiene una carga publicada. No se cargó el archivo."
    Y abet.archivo_origen y abet.carga no ganan ninguna fila

  # La huella se revisa antes que el cotejo de sección. Si ya tiene una carga PUBLICADA en otra sección,
  # la API responde 409 antes de escribir, porque el índice único parcial uq_carga_archivo_util impediría
  # publicar la carga nueva, y no entrega la constancia ni ningún dato de esa otra sección.
  @US-09 @corte1
  Escenario: Un archivo publicado en otra sección se detiene sin datos de esa sección
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que "docente411@example.invalid" tiene la sesión iniciada con rol "PROFESOR" y acceso.docente_seccion le asigna la sección 411
    Cuando "docente411@example.invalid" sube los mismos bytes con el nombre "notas 411.xlsx" a la sección 411
    Entonces la respuesta es 409 con detail "Este archivo ya está publicado en otra sección. No se cargó."
    Pero el cuerpo de la respuesta no contiene ese carga_id, la huella del archivo ni el número de la sección 410
    Y abet.archivo_origen, abet.carga, abet.rechazo_fila y abet.estudiante no ganan ninguna fila
    Y la sección 411 no tiene ninguna carga
    Y la sección 410 sigue con 1 carga "PUBLICADA" y sus 33 mediciones

  # US-10: Rechazar filas inválidas y avisar de columnas dudosas

  # Valor provisional de D-01. Una celda inválida rechaza la fila completa, así que el estudiante sale de
  # los tres PI. Valor provisional de D-04. Un Total Pts distinto de 4 deja un AVISO y la carga sigue.
  @US-10 @corte1
  Escenario: El 5 de la fila 3 rechaza esa fila completa
    Cuando el profesor sube "export_inventado_410_con_error.xlsx" a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 10 y filas_rechazadas 1
    Y archivo_origen.filas_de_datos es 11
    Y abet.rechazo_fila tiene exactamente 2 filas de esa carga
    Y una de ellas tiene motivo "NIVEL_FUERA_DE_ESCALA", efecto "RECHAZA_FILA", fila_origen 3 y la carga_columna_id del PI 5.2
    Y la otra tiene motivo "PUNTAJE_MAXIMO_DISTINTO", efecto "AVISO", fila_origen nulo y la carga_columna_id del PI 5.3
    Y abet.carga_fila tiene 10 filas de esa carga y ninguna con fila_origen 3
    Y abet.medicion tiene 30 filas de esa carga
    Y abet.estudiante no tiene el código "99000002"
    Y abet.v_r17_por_pi de esa carga da pct_logro_sobre_calificados 60,0 en 5.1, 60,0 en 5.2 y 70,0 en 5.3
    Y las consultas de control Q01, Q02, Q03, Q12 y Q13 devuelven 0 filas

  # Valor provisional de D-06. Los niveles -1, 0 y 5 dan NIVEL_FUERA_DE_ESCALA. Valor provisional de D-03.
  # Las marcas «-» y «NP» dan NIVEL_NO_NUMERICO, como cualquier texto que no es un nivel.
  @US-10 @corte1
  Esquema del escenario: Una celda de PI inválida en la fila 3 rechaza esa fila
    Dado una copia de "sintetico_20262_450002_410.xlsx" cuya columna 5.2 trae "<valor>" en la fila 3
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 10 y filas_rechazadas 1
    Y abet.rechazo_fila tiene 1 fila de esa carga con motivo "<motivo>", efecto "RECHAZA_FILA", fila_origen 3 y la carga_columna_id del PI 5.2
    Y abet.medicion tiene 30 filas de esa carga y ninguna de la fila_origen 3
    Y abet.v_r17_por_pi de esa carga da pct_logro_sobre_calificados 60,0 en 5.1, 60,0 en 5.2 y 70,0 en 5.3

    Ejemplos:
      | valor         | motivo                |
      | 5             | NIVEL_FUERA_DE_ESCALA |
      | 0             | NIVEL_FUERA_DE_ESCALA |
      | -1            | NIVEL_FUERA_DE_ESCALA |
      | 3,5           | NIVEL_NO_NUMERICO     |
      | Needs Grading | NIVEL_NO_NUMERICO     |
      | -             | NIVEL_NO_NUMERICO     |
      | NP            | NIVEL_NO_NUMERICO     |

  @US-10 @corte1
  Escenario: Una celda de PI vacía se carga como SIN_EVIDENCIA y no rechaza la fila
    Dado una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.2 vacía en la fila 3
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y abet.medicion tiene 33 filas de esa carga
    Y la medición de 99000002 en el PI 5.2 tiene estado_evidencia "SIN_EVIDENCIA" y nivel_original nulo
    Y abet.v_r17_por_pi del PI 5.2 da n_sin_evidencia 1, n_total 11, n_esperado_o_superior 6, pct_logro_sobre_calificados 60,0 y pct_logro_sobre_total_con_sin_evidencia 54,5
    Y abet.v_r17_por_pi da pct_logro_sobre_calificados 63,6 en 5.1 y 72,7 en 5.3
    Y pct_logro_segun_regla es nulo en los 3 PI, porque TRATO_SIN_EVIDENCIA sigue PENDIENTE

  # En un código repetido se rechaza la segunda aparición y se conserva la primera (propuesta).
  @US-10 @corte1
  Esquema del escenario: Un código vacío o repetido rechaza su fila
    Dado una copia de "sintetico_20262_450002_410.xlsx" <cambio>
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 10 y filas_rechazadas 1
    Y abet.rechazo_fila tiene 1 fila de esa carga con motivo "<motivo>", efecto "RECHAZA_FILA" y fila_origen <fila>
    Y abet.v_r17_por_pi de esa carga da pct_logro_sobre_calificados <pct_51> en 5.1, <pct_52> en 5.2 y <pct_53> en 5.3

    Ejemplos:
      | cambio                                 | motivo           | fila | pct_51 | pct_52 | pct_53 |
      | con el Username vacío en la fila 3     | CODIGO_VACIO     | 3    | 60,0   | 60,0   | 70,0   |
      | con el Username 99000001 en la fila 12 | CODIGO_DUPLICADO | 12   | 70,0   | 70,0   | 80,0   |

  @US-10 @corte1
  Escenario: Una columna de PI que no está en el plan se ignora con aviso
    Dado una copia de "sintetico_20262_450002_410.xlsx" con una columna más "4.1 [Total Pts: 4 Score] |9000041"
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y abet.rechazo_fila tiene 1 fila de esa carga con motivo "COLUMNA_PI_FUERA_DEL_PLAN", efecto "AVISO", fila_origen nulo y carga_columna_id nulo
    Pero abet.carga_columna de esa carga solo tiene los PI 5.1, 5.2 y 5.3
    Y abet.medicion tiene 33 filas de esa carga

  @US-10 @corte1
  Escenario: Si todas las filas se rechazan, la carga no se publica
    Dado una copia de "sintetico_20262_450002_410.xlsx" con un 5 en la columna 5.2 de las 11 filas de datos
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "RECHAZADA", filas_leidas 11, filas_aceptadas 0 y filas_rechazadas 11
    Y abet.rechazo_fila tiene 11 filas de esa carga con motivo "NIVEL_FUERA_DE_ESCALA" y efecto "RECHAZA_FILA", de la fila_origen 2 a la 12
    Y abet.carga_fila y abet.medicion no tienen filas de esa carga
    Y abet.v_r17_por_pi no devuelve filas de esa carga

  # Solo en una base desechable sin el script de guardia y con la guardia del programa apagada.
  @US-10 @corte1 @guardia_apagada
  Escenario: Con la guardia apagada, un código mal formado rechaza solo su fila
    Dado la API reiniciada con GUARDIA_DATOS_INVENTADOS "0"
    Y una copia de "sintetico_20262_450002_410.xlsx" con el Username 9900001 en la fila 4
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 10 y filas_rechazadas 1
    Y abet.rechazo_fila tiene 1 fila de esa carga con motivo "CODIGO_INVALIDO", efecto "RECHAZA_FILA" y fila_origen 4
    Y abet.v_r17_por_pi de esa carga da pct_logro_sobre_calificados 70,0 en 5.1, 60,0 en 5.2 y 70,0 en 5.3

  @US-10 @corte1
  Esquema del escenario: La base no deja publicar cuentas que no cuadran
    Dado una conexión directa con el rol abet_app y una carga EN_CURSO de la sección 410 con un archivo de filas_de_datos 11
    Cuando esa conexión cambia la carga a estado "PUBLICADA" con filas_leidas <leidas>, filas_aceptadas <aceptadas> y filas_rechazadas <rechazadas>
    Entonces la base rechaza el cambio por la restricción "<restriccion>"

    Ejemplos:
      | leidas | aceptadas | rechazadas | restriccion         |
      | 10     | 10        | 0          | ck_carga_conciliada |
      | 11     | 10        | 0          | ck_carga_filas      |

  # US-11: Detener un archivo ilegible sin dejar rastro

  # El tipo se comprueba por los primeros bytes y el zip se revisa antes de abrir el libro. Sin un archivo
  # medible no hay filas_de_datos, y sin archivo_origen no hay carga ni rechazo_fila.
  @US-11 @corte1
  Esquema del escenario: Un archivo que no se puede leer se detiene antes de registrar nada
    Dado <archivo>
    Cuando el profesor sube ese archivo a la sección 410
    Entonces la respuesta es 422 con detail "<mensaje>"
    Y abet.archivo_origen, abet.carga, abet.rechazo_fila y abet.estudiante no ganan ninguna fila
    Y ninguna carga queda en estado "EN_CURSO"

    Ejemplos:
      | archivo                                                                        | mensaje                                                                             |
      | una copia de "sintetico_20262_450002_410.xlsx" cortada a la mitad de sus bytes | No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard.                 |
      | una copia de "sintetico_20262_450002_410.xlsx" protegida con contraseña        | El archivo está protegido con contraseña. Guárdelo sin contraseña y súbalo.         |
      | un PDF inventado de una página con el nombre "export_410.pdf"                  | Solo se admiten exports de Blackboard en formato .xlsx.                             |
      | el mismo PDF con el nombre "export_410.xlsx"                                   | El contenido del archivo no es un libro de Excel aunque su nombre termine en .xlsx. |
      | una copia de "sintetico_20262_450002_410.xlsx" con la parte xl/vbaProject.bin  | El archivo trae macros o vínculos externos y no se admite.                          |
      | una copia de "sintetico_20262_450002_410.xlsx" con una parte xl/externalLinks/ | El archivo trae macros o vínculos externos y no se admite.                          |
      | un .xlsx inventado de 1,2 MB con códigos 99000001 a 99000011                   | El archivo supera el máximo de 1 MB.                                                |

  # (propuesta) El límite de 20 MB descomprimidos que fija lector.py y el texto del 422. La revisión del zip
  # lo detiene antes de abrir el libro. Que el lector no arranque sin defusedxml y que el registro no
  # guarde el contenido son pruebas unitarias y quedan en la spec, fuera de este archivo.
  @US-11 @corte1
  Escenario: Un libro que se infla al descomprimirse se rechaza
    Dado un .xlsx inventado de menos de 1 MB cuyo contenido descomprimido supera los 20 MB
    Cuando el profesor sube ese archivo a la sección 410
    Entonces la respuesta es 422 con detail "El contenido del archivo supera el tamaño admitido al descomprimirse."
    Y abet.archivo_origen, abet.carga, abet.rechazo_fila y abet.estudiante no ganan ninguna fila
    Y ninguna carga queda en estado "EN_CURSO"

  # US-12: Rechazar la carga por su estructura

  # Valor provisional que vuelve comprobable el conteo. Una carga rechazada por su estructura no registra
  # columnas ni avisos, solo su rechazo, y queda con filas_leidas 0 porque no llega a interpretar filas.
  @US-12 @corte1
  Esquema del escenario: Un defecto de estructura rechaza la carga entera y deja su motivo
    Dado una copia de "sintetico_20262_450002_410.xlsx" <defecto>
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "RECHAZADA" y el mensaje "<mensaje>"
    Y la carga queda en estado "RECHAZADA" con filas_leidas 0, filas_aceptadas 0, filas_rechazadas 0 y terminada_en no nulo
    Y carga.subida_por apunta a la fila de acceso.usuario_autorizado de "docente410@example.invalid"
    Y abet.rechazo_fila tiene exactamente 1 fila de esa carga, con motivo "<motivo>", efecto "RECHAZA_CARGA", fila_origen nulo y carga_columna_id nulo
    Y abet.carga_columna, abet.carga_fila y abet.medicion no tienen filas de esa carga
    Y abet.v_r17_por_pi no devuelve filas de esa carga

    Ejemplos: Motivos de V1_07
      | defecto                                   | motivo              | mensaje                                                                     |
      | con el encabezado y ninguna fila de datos | ARCHIVO_SIN_FILAS   | El archivo no trae filas de estudiantes.                                    |
      | sin la columna del PI 5.2                 | PI_DEL_PLAN_AUSENTE | Falta la columna del PI 5.2 que el plan de medición pide para esta sección. |

    Ejemplos: Motivos que agrega V1_09
      | defecto                                            | motivo                 | mensaje                                                |
      | sin las columnas Username ni Student ID            | COLUMNA_CODIGO_AUSENTE | El archivo no tiene la columna Username ni Student ID. |
      | con una segunda columna "5.1 [Total Pts: 4 Score]" | PI_REPETIDO            | El PI 5.1 aparece en dos columnas del archivo.         |

  @US-12 @corte1
  Escenario: La base no acepta un motivo que no existe
    Dado una conexión directa con el rol abet_app y una carga EN_CURSO de la sección 410
    Cuando esa conexión inserta un rechazo de esa carga con motivo "CODIGO_RARO" y efecto "RECHAZA_CARGA"
    Entonces la base rechaza la inserción por la restricción "ck_rechazo_fila_motivo"

  @US-12 @corte1
  Escenario: Después de un rechazo, un archivo distinto es otro archivo y se publica
    Dado que una copia de "sintetico_20262_450002_410.xlsx" sin la columna 5.2 está subida a la sección 410 y su carga está "RECHAZADA" con PI_DEL_PLAN_AUSENTE
    Cuando el profesor sube "sintetico_20262_450002_410.xlsx" a la sección 410
    Entonces la respuesta es 201 con estado "PUBLICADA"
    Y abet.archivo_origen tiene 2 filas con huellas distintas
    Y la sección 410 tiene 1 carga "RECHAZADA" y 1 carga "PUBLICADA"
    Y la carga RECHAZADA conserva su fila de abet.rechazo_fila

  # US-13: Rechazar el export de otra sección o periodo

  # La sección la elige el profesor y el sistema la coteja con el nombre de hoja y, si la hoja no la
  # declara, con el nombre del archivo. El curso distinto usa SECCION_NO_COINCIDE y el periodo distinto
  # usa PERIODO_NO_COINCIDE, que agrega V1_09. Si ni la hoja ni el nombre del archivo declaran la sección,
  # el corte 1 responde 422 sin rastro (valor provisional de D-02) y el corte 2 pide la confirmación de US-21.
  @US-13 @corte1
  Escenario: El export de la 411 subido en la 410 se rechaza
    Cuando el profesor sube "export_inventado_411.xlsx" a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "RECHAZADA" y el mensaje "El archivo corresponde a la sección 411 y usted eligió la 410. No se publicó."
    Y abet.archivo_origen tiene 1 fila con hoja "gc_SINTETICO_20262_450002_411_f"
    Y abet.rechazo_fila tiene exactamente 1 fila de esa carga, con motivo "SECCION_NO_COINCIDE", efecto "RECHAZA_CARGA" y fila_origen nulo
    Y abet.carga_fila y abet.medicion no tienen filas de esa carga
    Y la sección 410 no tiene ninguna carga "PUBLICADA"
    Y abet.estudiante no tiene ninguno de los códigos 99000012 a 99000022

  @US-13 @corte1
  Esquema del escenario: Un curso o un periodo distinto en el nombre de hoja rechaza la carga
    Dado una copia de "sintetico_20262_450002_410.xlsx" con la hoja renombrada "<hoja>"
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "RECHAZADA"
    Y abet.rechazo_fila tiene exactamente 1 fila de esa carga, con motivo "<motivo>" y efecto "RECHAZA_CARGA"
    Y abet.medicion no tiene filas de esa carga

    Ejemplos:
      | hoja                            | motivo              |
      | gc_SINTETICO_20262_450010_410_f | SECCION_NO_COINCIDE |
      | gc_SINTETICO_20261_450002_410_f | PERIODO_NO_COINCIDE |

  @US-13 @corte1
  Escenario: Si la hoja no declara la sección, se coteja el nombre del archivo
    Dado una copia de "sintetico_20262_450002_410.xlsx" con la hoja renombrada "Hoja1" y el nombre "gc_SINTETICO_20262_450002_411_fullgc_2026-10-20.xlsx"
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "RECHAZADA"
    Y abet.rechazo_fila tiene exactamente 1 fila de esa carga, con motivo "SECCION_NO_COINCIDE" y efecto "RECHAZA_CARGA"

  # Blackboard corta el nombre de hoja a 31 caracteres, así que el sufijo puede faltar.
  @US-13 @corte1
  Escenario: Una hoja truncada a 31 caracteres se coteja igual
    Dado una copia de "sintetico_20262_450002_410.xlsx" con la hoja renombrada "gc_SINTETICO_20262_450002_410"
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0

  # Rige solo en el corte 1. Al entrar US-21, el primer escenario de US-21 reemplaza a este.
  @US-13 @corte1
  Escenario: Un export que no declara su sección se detiene sin dejar rastro
    Dado una copia de "sintetico_20262_450002_410.xlsx" con la hoja renombrada "Hoja1" y el nombre "notas.xlsx"
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 422 con detail "El archivo no indica su sección. Sube el export de Blackboard sin cambiar el nombre de su hoja."
    Y abet.archivo_origen, abet.carga, abet.rechazo_fila y abet.estudiante no ganan ninguna fila
    Y ninguna carga queda en estado "EN_CURSO"

  # US-14: Descartar nombres y valores leídos

  @US-14 @corte1
  Escenario: Los nombres del export no llegan a ninguna tabla
    Cuando el profesor sube "export_inventado_410_con_error.xlsx" a la sección 410
    Entonces la consulta de control Q04 devuelve 0 filas
    Y una búsqueda de cada apellido y nombre inventado de las columnas Last Name y First Name del archivo en todas las columnas de texto de los esquemas abet y acceso devuelve 0 coincidencias
    Y todos los códigos de abet.estudiante cumplen "^99[0-9]{6}$"

  @US-14 @corte1
  Escenario: El rechazo dice fila, PI y motivo, nunca el valor leído
    Cuando el profesor sube "export_inventado_410_con_error.xlsx" a la sección 410
    Entonces el cuerpo de la respuesta trae el rechazo con fila 3, PI "5.2", motivo "NIVEL_FUERA_DE_ESCALA" y el mensaje "Fila 3, PI 5.2, nivel fuera de la escala 1 a 4. La fila completa queda fuera, también de 5.1 y 5.3."
    Pero ningún rechazo del cuerpo de la respuesta tiene un campo "valor" ni "valor_leido"
    Y information_schema.columns da para abet.rechazo_fila solo las columnas rechazo_id, carga_id, fila_origen, carga_columna_id, motivo y efecto

  @US-14 @corte1
  Escenario: Las columnas que no son PI del plan se descartan
    Cuando el profesor sube "export_inventado_410_con_error.xlsx" a la sección 410
    Entonces abet.carga_columna de esa carga solo tiene los PI 5.1, 5.2 y 5.3
    Y una búsqueda de "Last Access", "Availability" y de "Actividad 01" a "Actividad 18" en todas las columnas de texto de los esquemas abet y acceso devuelve 0 coincidencias
    Y ninguna tabla de los esquemas abet y acceso tiene una columna de tipo bytea, así que los bytes del export no se guardan

  @US-14 @corte1
  Escenario: El nombre del archivo se guarda sin ruta
    Cuando el profesor sube "export_inventado_410_con_error.xlsx" a la sección 410 con el nombre de archivo multipart "C:\Users\docente\Descargas\export_inventado_410_con_error.xlsx"
    Entonces archivo_origen.nombre_archivo es "export_inventado_410_con_error.xlsx"
    Y una inserción directa con el rol abet_app de un nombre_archivo con "/" la rechaza la restricción "ck_archivo_origen_nombre"

  # US-21: Confirmar la sección cuando el archivo no la declara

  # Corte 2, prioridad P3, valor provisional de D-02. El profesor confirma con el campo multipart
  # «confirmar_seccion» igual a "true", y la carga registra en abet.rechazo_fila un AVISO con el motivo
  # SECCION_SIN_DECLARAR, que V1_09 agrega junto con COLUMNA_CODIGO_AUSENTE, PI_REPETIDO y
  # PERIODO_NO_COINCIDE. carga.subida_por dice quién confirma. La respuesta 422 a la espera de la
  # confirmación y el campo requiere_confirmacion son (propuesta).
  @US-21 @corte2
  Escenario: Un export que no declara su sección espera la confirmación sin escribir nada
    Dado una copia de "sintetico_20262_450002_410.xlsx" con la hoja renombrada "Hoja1" y el nombre "notas.xlsx"
    Cuando el profesor sube esa copia a la sección 410
    Entonces la respuesta es 422 con detail "El archivo no indica su sección. ¿Confirma que es de la sección 410 de 450002 en 2026-2?"
    Y el cuerpo de la respuesta trae requiere_confirmacion verdadero
    Y abet.archivo_origen, abet.carga y abet.estudiante no ganan ninguna fila

  @US-21 @corte2
  Escenario: La sección confirmada publica la carga y la constancia lo dice
    Dado una copia de "sintetico_20262_450002_410.xlsx" con la hoja renombrada "Hoja1" y el nombre "notas.xlsx"
    Cuando el profesor sube esa copia a la sección 410 con el campo multipart "confirmar_seccion" igual a "true"
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y el cuerpo trae 1 aviso con motivo "SECCION_SIN_DECLARAR"
    Y abet.rechazo_fila tiene 1 fila de esa carga con motivo "SECCION_SIN_DECLARAR", efecto "AVISO", fila_origen nulo y carga_columna_id nulo
    Y abet.archivo_origen tiene 1 fila con nombre_archivo "notas.xlsx" y hoja "Hoja1"
    Y carga.subida_por apunta a la fila de acceso.usuario_autorizado de "docente410@example.invalid"
    Y abet.medicion tiene 33 filas de esa carga

  # El campo «confirmar_seccion» solo admite "true". Un número de sección distinto no confirma nada.
  @US-21 @corte2
  Escenario: La confirmación no vale si nombra otra sección
    Dado una copia de "sintetico_20262_450002_410.xlsx" con la hoja renombrada "Hoja1" y el nombre "notas.xlsx"
    Cuando el profesor sube esa copia a la sección 410 con el campo multipart "confirmar_seccion" igual a "411"
    Entonces la respuesta es 422 con detail "La sección confirmada no es la sección elegida. No se guardó nada."
    Y abet.archivo_origen, abet.carga y abet.estudiante no ganan ninguna fila

  @US-21 @corte2
  Escenario: La confirmación no pasa por encima de una sección declarada distinta
    Cuando el profesor sube "export_inventado_411.xlsx" a la sección 410 con el campo multipart "confirmar_seccion" igual a "true"
    Entonces la respuesta es 201 y su cuerpo trae estado "RECHAZADA"
    Y abet.rechazo_fila tiene exactamente 1 fila de esa carga, con motivo "SECCION_NO_COINCIDE" y efecto "RECHAZA_CARGA"
