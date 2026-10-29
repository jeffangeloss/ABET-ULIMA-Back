# language: es
#
# Escenarios de aceptación de la subida de la plantilla de proyectos (spec 002, historias US-03 a US-18
# y US-25). Todos los datos son inventados. Los archivos viven en tests/datos_inventados/ (por crear con
# scripts/generar_plantillas_inventadas.py, propuesta), salvo los que traen un código o un RUC que no es
# inventado, que la prueba genera en tmp_path y nunca versiona.
#
# Plantilla inventada plantilla_proyectos_inventada_420.xlsx (propuesta). Hoja «Hoja1» con el encabezado
# en la fila 1 (CÓDIGO, ALUMNO, GRUPO, TÍTULO DEL PROYECTO, TIPO DE EMPRESA, RUC, NOMBRE DE ORGANIZACIÓN y
# LÍNEA DE INVESTIGACIÓN en A1:H1), la lista auxiliar EMPRESA, ESTADO y ONG en K3:M5 y 11 filas de datos.
# - Grupo 1, filas 2 a 4, códigos 99000101 a 99000103, "Proyecto inventado A", EMPRESA, 20999999906,
#   "Organización Inventada Uno", "Línea inventada 1".
# - Grupo 2, filas 5 a 7, códigos 99000104 a 99000106, "Proyecto inventado B", ESTADO, 20999999914,
#   "Organización Inventada Dos", "Línea inventada 2".
# - Grupo 3, filas 8 a 10, códigos 99000107 a 99000109, "Proyecto inventado C", ONG, 20999999922,
#   "Organización Inventada Tres", "Línea inventada 1".
# - Grupo 4, filas 11 y 12, códigos 99000110 y 99000111, "Proyecto inventado D", EMPRESA, 20999999931,
#   "Organización Inventada Cuatro", "Línea inventada 3".
# - ALUMNO trae "Estudiante Ficticio 01" a "Estudiante Ficticio 11".
#
# Vocabulario de los pasos.
# - «el export de la 420 publicado» es la carga PUBLICADA de sintetico_20262_450024_420.xlsx (11 filas,
#   99000101 a 99000111, PI 1.1, 1.2 y 1.3), subida por el profesor de la 420 con la ruta de la spec 001.
# - «subir X» es POST /api/secciones/{seccion_id de la 420}/proyectos con X en el campo multipart
#   «archivo» y la cookie abet_sesion de quien tiene la sesión iniciada.
# - «una copia con …» es la plantilla inventada con solo ese cambio.
# - «la respuesta» es la respuesta HTTP; los errores traen { "detail": "mensaje" }.
# - «no gana filas» compara el conteo de la tabla antes y después de la petición.
# - Una fila rechazada deja a su estudiante sin proyecto, así que suma al aviso ESTUDIANTE_SIN_PROYECTO;
#   los pasos cuentan los rechazos por su efecto.
# - La guardia de los Antecedentes solo mira los valores que ya tienen la forma válida, un código de 8
#   dígitos y un RUC que cumple ^20[0-9]{9}$ (FR-014). Una celda vacía o mal formada sigue a las reglas por
#   fila, así que los escenarios de US-08 y US-10 corren con la guardia encendida y esperan 201.
# - Desde el corte 2, «subir X» envía además el campo multipart «declaracion_sin_personas» igual a
#   «true», salvo en los escenarios de US-25, que lo omiten o lo cambian a propósito.
# - Lo marcado «(propuesta)» no está fijado y lo decide la revisión de la spec.

Característica: Subida de la plantilla de proyectos de una sección Capstone
  Como profesor de un curso Capstone de Ingeniería Ambiental, quiero subir la plantilla de proyectos de mi
  sección después del export, para que el grupo, el título, la organización y la línea de investigación
  de cada estudiante queden en la base junto con sus notas.

  Antecedentes:
    Dado una base PostgreSQL 16 desechable con las migraciones V1_01 a V1_10 y los datos de db/datos/periodo_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2" y GUARDIA_DATOS_INVENTADOS "1"
    Y la asignatura "450024" con tipo_curso "CAPSTONE" en "AMB-2026" (valor provisional de D-14)
    Y "docente420@example.invalid" tiene la sesión iniciada con rol "PROFESOR" y acceso.docente_seccion le asigna la sección 420 de "450024" en "2026-2"

  # US-03: Subir la plantilla de proyectos de mi sección Capstone

  @US-03 @corte1
  Escenario: La plantilla correcta queda publicada entera
    Dado el export de la 420 publicado
    Cuando el profesor sube "plantilla_proyectos_inventada_420.xlsx"
    Entonces la respuesta es 201 y su cuerpo trae estado "PUBLICADA", filas_leidas 11, filas_aceptadas 11 y filas_rechazadas 0
    Y abet.archivo_origen gana 1 fila con tipo_fuente "PLANTILLA_PROYECTOS", hoja "Hoja1", filas_de_datos 11 y sha256 igual a la salida de "shasum -a 256" del archivo
    Y abet.carga_proyecto gana 1 fila PUBLICADA con el carga_id del export de la 420 y subida_por igual al usuario de "docente420@example.invalid"
    Y abet.proyecto_estudiante gana 11 filas de esa subida en los grupos 1, 2, 3 y 4
    Y la fila de 99000101 trae titulo "Proyecto inventado A", tipo_empresa "EMPRESA", ruc "20999999906", organizacion "Organización Inventada Uno" y linea_investigacion "Línea inventada 1"
    Y abet.rechazo_proyecto no gana filas
    Y las consultas de control Q01 a Q14 y Q16 a Q20 devuelven 0 filas

  @US-03 @corte1
  Escenario: El nombre del archivo se guarda sin ruta y los bytes no se conservan
    Dado el export de la 420 publicado
    Cuando el navegador envía la plantilla con el nombre "C:\Users\docente\Descargas\plantilla_proyectos_inventada_420.xlsx"
    Entonces la respuesta es 201
    Y abet.archivo_origen.nombre_archivo de la subida es "plantilla_proyectos_inventada_420.xlsx"
    Y information_schema.columns no tiene ninguna columna de tipo bytea en los esquemas abet ni acceso

  # US-04: La plantilla espera al export publicado

  @US-04 @corte1
  Escenario: Sin export publicado la plantilla no se guarda
    Dado que la sección 420 no tiene ninguna carga PUBLICADA
    Cuando el profesor sube "plantilla_proyectos_inventada_420.xlsx"
    Entonces la respuesta es 409 con detail "Suba primero el export de Blackboard de la sección 420. La plantilla de proyectos se une a los estudiantes de ese export."
    Y abet.archivo_origen, abet.carga_proyecto, abet.proyecto_estudiante y abet.rechazo_proyecto no ganan filas

  @US-04 @corte1
  Escenario: Un export solo RECHAZADO no habilita la plantilla
    Dado que la sección 420 tiene solo una carga RECHAZADA del export
    Cuando el profesor sube "plantilla_proyectos_inventada_420.xlsx"
    Entonces la respuesta es 409 con detail "Suba primero el export de Blackboard de la sección 420. La plantilla de proyectos se une a los estudiantes de ese export."
    Y abet.carga_proyecto no gana filas

  # US-05: La plantilla solo entra en secciones Capstone

  @US-05 @corte1
  Escenario: Una sección de un curso de carrera no recibe plantilla
    Dado que "450002" tiene tipo_curso "CARRERA" y la sección 410 tiene PUBLICADA su carga de la spec 001
    Y que "docente410@example.invalid" tiene la sesión iniciada con la sección 410 asignada
    Cuando sube "plantilla_proyectos_inventada_420.xlsx" a POST /api/secciones/{sección 410}/proyectos
    Entonces la respuesta es 409 con detail "Esta sección no es de un curso Capstone. No se cargó nada."
    Y abet.archivo_origen, abet.carga_proyecto y abet.proyecto_estudiante no ganan filas

  @US-05 @corte1
  Escenario: El tipo de curso se lee de la base en cada subida
    Dado el export de la 420 publicado y "450024" vuelta a tipo_curso "CARRERA" por el administrador técnico
    Cuando el profesor sube "plantilla_proyectos_inventada_420.xlsx"
    Entonces la respuesta es 409 con detail "Esta sección no es de un curso Capstone. No se cargó nada."
    Y abet.carga_proyecto no gana filas

  @US-05 @corte1
  Escenario: Una sección sin plan de medición no recibe plantilla
    Dado que la sección 425 de "450026" en "2026-2" no tiene filas en abet.plan_medicion y está asignada a "docente420@example.invalid"
    Cuando el profesor sube "plantilla_proyectos_inventada_420.xlsx" a POST /api/secciones/{sección 425}/proyectos
    Entonces la respuesta es 422 con detail "La carrera aún no registra el plan de medición de esta sección." (propuesta)
    Y abet.archivo_origen, abet.carga_proyecto, abet.proyecto_estudiante y abet.rechazo_proyecto no ganan filas

  # US-06: Solo el profesor asignado sube la plantilla y ve sus datos

  @US-06 @corte1
  Escenario: Un profesor no sube proyectos a una sección que no dicta
    Dado que la sección 421 de "450024" tiene PUBLICADA la carga de "sintetico_20262_450024_421.xlsx" con los códigos 99000112 a 99000122
    Cuando el profesor de la 420 sube la plantilla a POST /api/secciones/{sección 421}/proyectos
    Entonces la respuesta es 403 con detail "La sección no está a su cargo."
    Y abet.archivo_origen, abet.carga_proyecto y abet.proyecto_estudiante no ganan filas

  @US-06 @corte1
  Escenario: El coordinador no sube la plantilla en este corte
    Dado el export de la 420 publicado
    Y que "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando envía la plantilla a POST /api/secciones/{sección 420}/proyectos
    Entonces la respuesta es 403 con detail "La sección no está a su cargo."
    Y abet.carga_proyecto no gana filas

  @US-06 @corte1
  Escenario: Sin sesión la ruta responde 401
    Dado el export de la 420 publicado
    Cuando se envía la plantilla sin la cookie abet_sesion
    Entonces la respuesta es 401
    Y abet.archivo_origen y abet.carga_proyecto no ganan filas

  @US-06 @corte1
  Esquema del escenario: La constancia y el R-17 Capstone de la 420 solo los ve quien tiene la sección a su alcance
    Dado el export de la 420 publicado y la plantilla publicada
    Y que "<usuario>" tiene la sesión iniciada con rol "<rol>"
    Cuando pide <ruta> de la carga de la 420
    Entonces la respuesta es <codigo>

    Ejemplos:
      | usuario                      | rol         | ruta                                 | codigo                                               |
      | docente421@example.invalid   | PROFESOR    | GET /api/cargas/{carga_id}           | 403 con detail "La sección no está a su cargo."      |
      | docente421@example.invalid   | PROFESOR    | GET /api/cargas/{carga_id}/r17.xlsx  | 403 con detail "La sección no está a su cargo." y sin libro |
      | coordinacion@example.invalid | COORDINADOR | GET /api/cargas/{carga_id}           | 200 con el bloque proyectos                          |
      | coordinacion@example.invalid | COORDINADOR | GET /api/cargas/{carga_id}/r17.xlsx  | 200 con la hoja "Cursos Capstone"                    |

  # US-07: Un código ajeno al export o repetido deja fuera solo su fila

  @US-07 @corte1
  Esquema del escenario: Un código que no está en el export de la sección rechaza solo su fila
    Dado el export de la 420 publicado
    Y que la sección 421 tiene PUBLICADA su carga con los códigos 99000112 a 99000122
    Cuando el profesor sube una copia con <codigo> en la celda CÓDIGO de la fila 4
    Entonces la respuesta es 201 con estado "PUBLICADA", filas_leidas 11, filas_aceptadas 10 y filas_rechazadas 1
    Y abet.rechazo_proyecto tiene 1 fila con efecto "RECHAZA_FILA", fila_origen 4, columna "CÓDIGO" y motivo "CODIGO_FUERA_DEL_EXPORT"
    Y el cuerpo trae el aviso "ESTUDIANTE_SIN_PROYECTO" con la cuenta 1
    Y ni el cuerpo de la respuesta ni abet.rechazo_proyecto contienen "<codigo>"
    Y abet.estudiante no gana filas y abet.proyecto_estudiante no tiene fila de <codigo>

    Ejemplos:
      | codigo   |
      | 99000113 |
      | 99000199 |

  @US-07 @corte1
  Escenario: La base impide un proyecto de un estudiante ajeno al export aunque el programa falle
    Dado el export de la 420 publicado, la plantilla publicada y una conexión directa con abet_app
    Cuando se inserta en abet.proyecto_estudiante una fila de esa subida con el estudiante 99000113 de la 421
    Entonces la inserción falla por fk_proyecto_estudiante_carga_fila

  @US-07 @corte1
  Escenario: Un código repetido rechaza su segunda aparición
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con 99000104 en la celda CÓDIGO de la fila 9
    Entonces la respuesta es 201 con filas_aceptadas 10 y filas_rechazadas 1
    Y abet.rechazo_proyecto tiene 1 fila con efecto "RECHAZA_FILA", fila_origen 9, columna "CÓDIGO" y motivo "CODIGO_DUPLICADO"
    Y la fila 5 queda aceptada con el grupo 2 para 99000104
    Y el cuerpo trae el aviso "ESTUDIANTE_SIN_PROYECTO" con la cuenta 1, la de 99000108

  @US-07 @corte1
  Escenario: La base no guarda dos proyectos del mismo estudiante en una subida
    Dado la plantilla publicada en la 420 y una conexión directa con abet_app
    Cuando se inserta otra fila de abet.proyecto_estudiante de esa subida para 99000101
    Entonces la inserción falla por pk_proyecto_estudiante

  # US-08: Un dato de proyecto vacío, demasiado largo o un grupo inválido rechaza la fila

  @US-08 @corte1
  Esquema del escenario: Una celda obligatoria vacía rechaza la fila completa
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con la celda <columna> de la fila 6 vacía
    Entonces la respuesta es 201 con filas_leidas 11, filas_aceptadas 10 y filas_rechazadas 1
    Y abet.rechazo_proyecto tiene 1 fila con efecto "RECHAZA_FILA", fila_origen 6, columna "<columna>" y motivo "CAMPO_VACIO"
    Y el mensaje de ese rechazo dice "Fila 6, falta el dato de <columna>. La fila completa queda fuera."
    Y abet.proyecto_estudiante no tiene fila de 99000105

    Ejemplos:
      | columna                |
      | CÓDIGO                 |
      | GRUPO                  |
      | TÍTULO DEL PROYECTO    |
      | TIPO DE EMPRESA        |
      | RUC                    |
      | NOMBRE DE ORGANIZACIÓN |
      | LÍNEA DE INVESTIGACIÓN |

  @US-08 @corte1
  Esquema del escenario: Un grupo que no es un entero positivo rechaza la fila
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con <valor> en la celda GRUPO de la fila 6
    Entonces la respuesta es 201 con filas_aceptadas 10 y filas_rechazadas 1
    Y abet.rechazo_proyecto tiene 1 fila con efecto "RECHAZA_FILA", fila_origen 6, columna "GRUPO" y motivo "GRUPO_INVALIDO"
    Y el mensaje de ese rechazo dice "Fila 6, el grupo debe ser un número entero mayor o igual que 1."

    Ejemplos:
      | valor         |
      | el número 0   |
      | el número -1  |
      | el número 1,5 |
      | el texto "A"  |

  @US-08 @corte1
  Esquema del escenario: Un texto que supera su límite rechaza la fila sin recortarlo
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con <largo> caracteres inventados en la celda <columna> de la fila 6
    Entonces la respuesta es 201 con filas_aceptadas 10 y filas_rechazadas 1
    Y abet.rechazo_proyecto tiene 1 fila con efecto "RECHAZA_FILA", fila_origen 6, columna "<columna>" y motivo "TEXTO_DEMASIADO_LARGO"
    Y ninguna fila de abet.proyecto_estudiante guarda un texto recortado de esa celda

    Ejemplos:
      | columna                | largo |
      | TÍTULO DEL PROYECTO    | 301   |
      | NOMBRE DE ORGANIZACIÓN | 201   |
      | LÍNEA DE INVESTIGACIÓN | 121   |

  # US-09: El tipo de empresa admite solo EMPRESA, ESTADO u ONG

  @US-09 @corte1
  Esquema del escenario: El tipo de empresa del grupo 4 dentro y fuera de la lista
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con <valor> en la celda TIPO DE EMPRESA de las filas 11 y 12
    Entonces <resultado>

    Ejemplos:
      | valor           | resultado                                                                                                                       |
      | "ESTADO"        | la respuesta es 201 con filas_aceptadas 11 y las filas de 99000110 y 99000111 guardan tipo_empresa "ESTADO"                     |
      | "empresa"       | la respuesta es 201 con filas_aceptadas 11 y las filas de 99000110 y 99000111 guardan tipo_empresa "EMPRESA"                    |
      | " ong "         | la respuesta es 201 con filas_aceptadas 11 y las filas de 99000110 y 99000111 guardan tipo_empresa "ONG"                        |
      | "COOPERATIVA"   | la respuesta es 201 con filas_aceptadas 9, filas_rechazadas 2 y 2 rechazos "TIPO_EMPRESA_INVALIDO" en las filas 11 y 12        |

  @US-09 @corte1
  Escenario: La forma canónica se compara antes que la consistencia del grupo
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con " ong " en TIPO DE EMPRESA de la fila 11 y "ONG" en la de la fila 12
    Entonces la respuesta es 201 con filas_aceptadas 11 y filas_rechazadas 0
    Y la consulta de control Q19 devuelve 0 filas

  @US-09 @corte1
  Escenario: El mensaje del tipo de empresa no repite la celda
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con "COOPERATIVA" en TIPO DE EMPRESA de las filas 11 y 12
    Entonces el mensaje del rechazo de la fila 11 dice "Fila 11, el tipo de empresa debe ser EMPRESA, ESTADO u ONG."
    Y ni el cuerpo de la respuesta ni abet.rechazo_proyecto contienen "COOPERATIVA"

  @US-09 @corte1
  Escenario: Una plantilla sin ninguna fila aceptada queda rechazada
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con "COOPERATIVA" en TIPO DE EMPRESA de las 11 filas
    Entonces la respuesta es 201 con estado "RECHAZADA", filas_leidas 11, filas_aceptadas 0 y filas_rechazadas 11
    Y abet.proyecto_estudiante no gana filas

  @US-09 @corte1
  Escenario: La lista auxiliar K3:M5 no se lee como estudiantes
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con solo las filas 11 y 12 y la lista EMPRESA, ESTADO y ONG en K3:M5
    Entonces la respuesta es 201 con filas_leidas 2, filas_aceptadas 2 y filas_rechazadas 0
    Y abet.archivo_origen guarda filas_de_datos 2 para esa copia, porque K3:M5 queda fuera de las ocho columnas del encabezado
    Y el cuerpo trae el aviso "ESTUDIANTE_SIN_PROYECTO" con la cuenta 9

  @US-09 @corte1
  Escenario: La base rechaza un tipo de empresa fuera de la lista aunque el programa falle
    Dado una conexión directa con abet_app y la subida de la 420 EN_CURSO
    Cuando se inserta en abet.proyecto_estudiante una fila con tipo_empresa "OTRA"
    Entonces la inserción falla por ck_proyecto_tipo_empresa

  # US-10: El RUC se acepta solo con forma de persona jurídica

  @US-10 @corte1
  Esquema del escenario: Un RUC que no tiene la forma de persona jurídica rechaza las filas del grupo
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con <ruc> en la celda RUC de las filas 11 y 12
    Entonces la respuesta es 201 con filas_aceptadas 9 y filas_rechazadas 2
    Y abet.rechazo_proyecto tiene 2 filas con efecto "RECHAZA_FILA", filas_origen 11 y 12, columna "RUC" y motivo "<motivo>"
    Y ni el cuerpo de la respuesta ni abet.rechazo_proyecto contienen <ruc>

    Ejemplos:
      | ruc            | motivo               |
      | "10999999991"  | RUC_PERSONA_NATURAL  |
      | "99999990"     | RUC_FORMATO_INVALIDO |
      | "2099999993"   | RUC_FORMATO_INVALIDO |
      | "209999999310" | RUC_FORMATO_INVALIDO |
      | "2099999993X"  | RUC_FORMATO_INVALIDO |
      | "30999999931"  | RUC_FORMATO_INVALIDO |

  @US-10 @corte1
  Esquema del escenario: Los mensajes del RUC no repiten el valor leído
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con <ruc> en RUC de las filas 11 y 12
    Entonces el mensaje del rechazo de la fila 11 dice "<mensaje>"

    Ejemplos:
      | ruc           | mensaje                                                  |
      | "10999999991" | Fila 11, RUC, no corresponde a una organización.         |
      | "99999990"    | Fila 11, el RUC debe tener 11 dígitos y empezar con 20.  |

  @US-10 @corte1
  Esquema del escenario: Un RUC que Excel entrega como número se lee como texto
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia cuya celda RUC de las filas 11 y 12 es <celda>
    Entonces la respuesta es 201 con filas_aceptadas 11
    Y abet.proyecto_estudiante guarda ruc "20999999931" como texto de 11 caracteres para 99000110 y 99000111

    Ejemplos:
      | celda                          |
      | el número entero 20999999931   |
      | el número decimal 20999999931,0 |

  @US-10 @corte1
  Escenario: La base rechaza un RUC de persona natural aunque el programa falle
    Dado una conexión directa con abet_app y la subida de la 420 EN_CURSO
    Cuando se inserta en abet.proyecto_estudiante una fila con ruc "10999999991"
    Entonces la inserción falla por ck_proyecto_ruc

  # US-11: Un grupo con datos distintos entre sus integrantes se rechaza entero

  @US-11 @corte1
  Escenario: Un integrante con otro título deja fuera a todo su grupo
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con "Proyecto inventado B2" en TÍTULO DEL PROYECTO de la fila 7
    Entonces la respuesta es 201 con estado "PUBLICADA", filas_leidas 11, filas_aceptadas 8 y filas_rechazadas 3
    Y abet.rechazo_proyecto tiene 3 filas con efecto "RECHAZA_FILA", filas_origen 5, 6 y 7, columna "TÍTULO DEL PROYECTO" y motivo "GRUPO_INCONSISTENTE"
    Y el mensaje del rechazo de la fila 5 dice "Fila 5, el grupo 2 trae datos de proyecto distintos entre sus integrantes. El grupo completo queda fuera."
    Y el cuerpo trae el aviso "ESTUDIANTE_SIN_PROYECTO" con la cuenta 3
    Y la consulta de control Q19 devuelve 0 filas

  @US-11 @corte1
  Escenario: Un grupo de dos integrantes con RUC distintos se rechaza entero
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con "20999999949" en RUC de la fila 12
    Entonces la respuesta es 201 con filas_aceptadas 9 y filas_rechazadas 2
    Y las filas 11 y 12 quedan rechazadas con motivo "GRUPO_INCONSISTENTE" y columna "RUC"
    Y abet.proyecto_estudiante no tiene filas del grupo 4

  # US-12: Un estudiante del export sin proyecto queda a la vista

  @US-12 @corte1
  Escenario: La plantilla con menos estudiantes que el export se publica con aviso
    Dado el export de la 420 publicado con 11 estudiantes
    Cuando el profesor sube una copia sin las filas 11 y 12, la de 99000110 y la de 99000111
    Entonces la respuesta es 201 con estado "PUBLICADA", filas_leidas 9, filas_aceptadas 9 y filas_rechazadas 0
    Y el cuerpo trae 1 aviso con motivo "ESTUDIANTE_SIN_PROYECTO", la cuenta 2 y el mensaje "2 estudiantes del export no tienen fila en la plantilla."
    Y abet.rechazo_proyecto tiene 1 fila con efecto "AVISO", motivo "ESTUDIANTE_SIN_PROYECTO" y fila_origen nulo
    Y la consulta de seguimiento S01 devuelve las 2 filas de 99000110 y 99000111
    Y ninguna respuesta ni ningún rechazo listan esos códigos

  # US-13: Una plantilla con la estructura equivocada se detiene

  @US-13 @corte1
  Esquema del escenario: Una estructura inválida rechaza la subida entera
    Dado el export de la 420 publicado
    Cuando el profesor sube <archivo>
    Entonces la respuesta es 201 con estado "RECHAZADA", filas_leidas 0, filas_aceptadas 0 y filas_rechazadas 0
    Y abet.rechazo_proyecto tiene 1 sola fila, con motivo "<motivo>" y efecto "RECHAZA_CARGA"
    Y abet.proyecto_estudiante no gana filas

    Ejemplos:
      | archivo                                         | motivo              |
      | una copia sin la columna RUC                    | ENCABEZADO_AUSENTE  |
      | una copia sin la columna ALUMNO                 | ENCABEZADO_AUSENTE  |
      | una copia con la columna GRUPO repetida         | ENCABEZADO_REPETIDO |
      | una copia con el encabezado y sin filas de datos | ARCHIVO_SIN_FILAS   |
      | una copia con la hoja renombrada a "Datos"      | PLANTILLA_SIN_HOJA  |

  @US-13 @corte1
  Esquema del escenario: Un archivo que no es una plantilla legible se detiene sin rastro
    Dado el export de la 420 publicado
    Cuando el profesor sube <archivo>
    Entonces la respuesta es 422 con detail "<detail>"
    Y abet.archivo_origen, abet.carga_proyecto, abet.proyecto_estudiante y abet.rechazo_proyecto no ganan filas

    Ejemplos:
      | archivo                                                  | detail                                                                  |
      | el export "sintetico_20262_450024_420.xlsx" ya publicado | El archivo ya está registrado como export de Blackboard. No se cargó nada. |
      | un archivo de texto con extensión .xlsx                  | No se pudo abrir el archivo. No se cargó nada.                          |

  # US-14: La columna ALUMNO se lee para validar y no se guarda

  @US-14 @corte1
  Escenario: Ningún nombre de la plantilla llega a la base ni a las respuestas
    Dado el export de la 420 publicado
    Cuando el profesor sube "plantilla_proyectos_inventada_420.xlsx" y obtiene 201 con estado "PUBLICADA"
    Entonces la búsqueda de "Estudiante Ficticio" en todas las columnas de texto de los esquemas abet y acceso, recorridas con information_schema.columns y query_to_xml, devuelve 0 coincidencias
    Y el cuerpo de la respuesta y el registro de la aplicación capturado en la prueba no contienen "Estudiante Ficticio"
    Y la consulta de control Q04 ampliada devuelve 0 filas

  @US-14 @corte1
  Escenario: Q04 ampliada ve una columna de nombre añadida a las tablas de proyecto
    Dado la base migrada hasta V1_10
    Cuando una transacción que se deshace agrega la columna "nombre_alumno" a abet.proyecto_estudiante y corre Q04
    Entonces Q04 devuelve 1 fila con table_name "proyecto_estudiante" y column_name "nombre_alumno"

  @US-14 @corte1
  Escenario: Un rechazo de la plantilla no repite el nombre del alumno
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia con "COOPERATIVA" en TIPO DE EMPRESA de las filas 11 y 12
    Entonces los rechazos de las filas 11 y 12 traen fila, columna, motivo, efecto y mensaje y ningún campo "valor" ni "valor_leido"
    Y ni el cuerpo de la respuesta ni abet.rechazo_proyecto contienen "Estudiante Ficticio 10" ni "Estudiante Ficticio 11"

  # US-15: La guardia de datos inventados cubre la plantilla

  @US-15 @corte1
  Escenario: Una plantilla con un código que no es inventado se detiene entera
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia generada en tmp_path con 10000004 en la celda CÓDIGO de la fila 4
    Entonces la respuesta es 422 con detail "El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada."
    Y el detail no contiene "10000004"
    Y abet.archivo_origen, abet.carga_proyecto, abet.proyecto_estudiante y abet.rechazo_proyecto no ganan filas

  @US-15 @corte1
  Escenario: Una plantilla con un RUC que no es inventado se detiene entera
    Dado el export de la 420 publicado
    Cuando el profesor sube una copia generada en tmp_path con "20123456781" en la celda RUC de las filas 11 y 12
    Entonces la respuesta es 422 con detail "El piloto solo admite RUC inventados. Revise la fila 11. No se guardó nada." (propuesta)
    Y el detail no contiene "20123456781"
    Y abet.archivo_origen, abet.carga_proyecto, abet.proyecto_estudiante y abet.rechazo_proyecto no ganan filas

  @US-15 @corte1
  Escenario: Ningún campo de la petición apaga la guardia de la plantilla
    Dado la copia con el RUC "20123456781" del escenario anterior
    Cuando el profesor la sube con el campo multipart "guardia" igual a "0" y el parámetro de consulta guardia=0
    Entonces recibe el mismo 422 y las cuatro tablas no ganan filas, como en US-08 de la spec 001

  @US-15 @corte1
  Escenario: La base de Neon rechaza un RUC que no es inventado aunque el programa falle
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_10, db/plataforma/neon/guardia_datos_inventados.sql aplicado y una conexión directa con abet_app
    Cuando se inserta en abet.proyecto_estudiante una fila con ruc "20123456781"
    Entonces la inserción falla por ck_proyecto_ruc_inventado
    Y una fila con ruc "20999999906" termina bien

  # US-16: Subir otra vez la misma plantilla no duplica nada

  @US-16 @corte1
  Escenario: El mismo archivo en la misma sección devuelve la constancia existente
    Dado el export de la 420 publicado y "plantilla_proyectos_inventada_420.xlsx" PUBLICADA en la 420
    Cuando el profesor la sube otra vez
    Entonces la respuesta es 200 con la constancia de la subida existente y el mismo carga_proyecto_id
    Y abet.archivo_origen, abet.carga_proyecto y abet.proyecto_estudiante no ganan filas

  @US-16 @corte1
  Escenario: El mismo archivo ya publicado en otra sección se detiene antes de escribir
    Dado la plantilla PUBLICADA en la 420 y la sección 421 con su export publicado
    Y que "docente421@example.invalid" tiene la sesión iniciada con la sección 421 asignada
    Cuando sube ese mismo archivo a POST /api/secciones/{sección 421}/proyectos
    Entonces la respuesta es 409 con detail "Este archivo ya está publicado en otra sección. No se cargó."
    Y la respuesta no trae ningún dato de la sección 420
    Y abet.carga_proyecto no gana filas

  @US-16 @corte1
  Escenario: Otra plantilla distinta no pisa la publicada
    Dado la plantilla PUBLICADA en la 420
    Cuando el profesor sube una copia con "Proyecto inventado A revisado" en TÍTULO DEL PROYECTO de las filas 2 a 4
    Entonces la respuesta es 409 con detail "La sección 420 ya tiene una plantilla de proyectos publicada. No se cargó el archivo."
    Y abet.carga_proyecto no gana filas

  # US-17: Un fallo a mitad de la carga de proyectos no deja nada escrito

  @US-17 @corte1
  Esquema del escenario: Un fallo en cualquier punto no deja nada escrito
    Dado el export de la 420 publicado
    Y que la prueba inyecta un fallo de conexión <punto>
    Cuando el profesor sube "plantilla_proyectos_inventada_420.xlsx"
    Entonces la respuesta es 500 con detail "La carga no se completó y no se guardó ningún dato. Intente de nuevo."
    Y abet.archivo_origen, abet.carga_proyecto, abet.proyecto_estudiante y abet.rechazo_proyecto no ganan filas
    Y ninguna subida de plantilla queda en estado "EN_CURSO"

    Ejemplos:
      | punto                                              |
      | después de insertar la fila de abet.archivo_origen |
      | después de insertar la fila de abet.carga_proyecto |
      | después de insertar la sexta fila de abet.proyecto_estudiante |
      | justo antes de cambiar el estado a PUBLICADA       |

  @US-17 @corte1
  Escenario: Una restricción violada al final deshace todo
    Dado el export de la 420 publicado
    Y que un defecto inyectado en el programa intenta guardar el RUC "2099" en el último proyecto
    Cuando el profesor sube "plantilla_proyectos_inventada_420.xlsx"
    Entonces la base rechaza la fila por ck_proyecto_ruc
    Y la respuesta es 500 con detail "La carga no se completó y no se guardó ningún dato. Intente de nuevo."
    Y las cuatro tablas no ganan filas
    Y el registro de la aplicación guarda el SQLSTATE y el nombre "ck_proyecto_ruc", y no el DETAIL de PostgreSQL

  # US-18: Recibir la constancia de la plantilla como evidencia

  @US-18 @corte1
  Escenario: La constancia de la plantilla trae huella, conteos y rechazos sin valores
    Dado el export de la 420 publicado
    Y que el profesor subió una copia con 99000113 en la celda CÓDIGO de la fila 4 y obtuvo 201
    Cuando pide GET /api/cargas/{carga_id del export de la 420}
    Entonces la respuesta es 200 con un bloque "proyectos" igual al cuerpo del 201 de la subida
    Y el bloque trae nombre_archivo, hoja "Hoja1", filas_de_datos 11, filas_leidas 11, filas_aceptadas 10, filas_rechazadas 1, estudiantes_en_export 11 y estudiantes_con_proyecto 10
    Y su sha256 tiene 64 caracteres hexadecimales en minúscula y es igual a la salida de "shasum -a 256" del archivo que conserva el profesor
    Y subida_por es "docente420@example.invalid" y terminada_en es mayor que iniciada_en, ambas con desfase "-05:00"
    Y el rechazo trae fila 4, columna "CÓDIGO" y motivo "CODIGO_FUERA_DEL_EXPORT", sin campo "valor" ni "valor_leido"
    Y ningún campo del bloque contiene un título, una organización ni un RUC de la plantilla

  @US-18 @corte1
  Escenario: La constancia de una sección sin plantilla trae el bloque vacío
    Dado el export de la 420 publicado y ninguna subida de plantilla
    Cuando el profesor pide GET /api/cargas/{carga_id del export de la 420}
    Entonces la respuesta es 200 con el bloque "proyectos" con estado "SIN_PLANTILLA", estudiantes_en_export 11 y estudiantes_con_proyecto 0 (propuesta)

  # US-25: Declarar que los textos libres no nombran personas (corte 2)

  @US-25 @corte2
  Escenario: Sin la declaración no se guarda ningún proyecto
    Dado el export de la 420 publicado
    Cuando el profesor sube "plantilla_proyectos_inventada_420.xlsx" sin el campo multipart "declaracion_sin_personas"
    Entonces la respuesta es 422 con detail "Confirme que los títulos y nombres de organización no nombran personas."
    Y abet.archivo_origen, abet.carga_proyecto y abet.proyecto_estudiante no ganan filas

  @US-25 @corte2
  Escenario: La declaración queda registrada en la subida
    Dado el export de la 420 publicado
    Cuando el profesor sube la plantilla con "declaracion_sin_personas" igual a "true"
    Entonces la respuesta es 201
    Y abet.carga_proyecto guarda declaro_sin_personas verdadero y declarado_en no nulo en hora de Lima
    Y abet.carga_proyecto no tiene ninguna columna con el texto de la declaración

  @US-25 @corte2
  Escenario: La declaración solo admite el valor true
    Dado el export de la 420 publicado
    Cuando el profesor sube la plantilla con "declaracion_sin_personas" igual a "no"
    Entonces la respuesta es 422 con detail "Confirme que los títulos y nombres de organización no nombran personas."
    Y abet.carga_proyecto no gana filas
