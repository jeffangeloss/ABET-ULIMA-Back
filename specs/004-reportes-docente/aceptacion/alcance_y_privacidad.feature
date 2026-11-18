# language: es
#
# Escenarios de aceptación del límite de acceso y de la privacidad de los resultados por resultado del
# estudiante (student outcome, SO), de las historias de usuario (user stories, US) US-38 y US-42 de la spec
# 004-reportes-docente. Jefferson pide el 2026-11-17 que el profesor «solamente debe poder consultar a él e
# sus secciones, no otras secciones de otros profesores. Ese debería ser el límite» (spec.md, Input). Las
# reglas de negocio (business rules, BR) que prueba son BR-ACCESO-06, BR-ACCESO-07 y BR-ACCESO-08 de
# acceso.spec.md, con la regla nueva BR-ACCESO-10 (propuesta, tarea T010).
#
# El límite de subida que pide la misma frase («tampoco él debería subir un export a secciones que no son de
# él») ya lo prueban escenarios aprobados de la spec 001, que este archivo no repite. Son «El profesor no
# alcanza una sección ajena escribiendo la ruta» (acceso.feature), «Un profesor no sube a una sección que no
# tiene asignada» y «El coordinador no sube en el corte 1» (carga.feature) y «El profesor de varias secciones
# no alcanza una sección que no dicta» (varias_secciones.feature).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid. Ninguna
# contraseña aparece escrita aquí. db/datos/varias_secciones_2026_2_inventado.sql corre solo en las bases
# desechables de estas pruebas y nunca en Neon.
#
# Vocabulario de los pasos, el de resultados.feature.
# - «se envía GET /api/resultados?periodo=2026-2» es la petición a la ruta 12 (propuesta) con la cookie
#   abet_sesion de quien tiene la sesión iniciada.
# - «que "docente.varias@example.invalid" tiene publicadas sus tres secciones» sube sus tres exports
#   inventados a la 412 de 450002 y a la 410 y la 412 de 450010, cada uno con respuesta 201 y PUBLICADA.
# - «no trae la sección N de A» quiere decir que ninguna sección de la respuesta tiene ese número con esa
#   asignatura, y que el cuerpo no contiene su seccion_id ni el carga_id de sus cargas.
# - Cada escenario corre en una base desechable propia, así que los carga_id y los seccion_id salen de la
#   API o de la base y nunca se suponen.
# - @delegado_a_vitest marca un escenario de la pantalla P6 que prueba Vitest en el Front.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Los resultados por SO respetan el límite de cada profesor y no exponen personas
  Un profesor ve en sus resultados solo las secciones que acceso.docente_seccion le asigna, el coordinador
  ve todas las de la carrera y nadie ve resultados sin una sesión vigente. La respuesta trae solo conteos,
  porcentajes y nombres del catálogo, sin estudiantes ni correos.

  Antecedentes:
    Dado una base PostgreSQL 18 desechable con las migraciones V1_01 a V1_10, los datos de db/datos/periodo_2026_2_inventado.sql y, después, los de db/datos/varias_secciones_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y acceso.docente_seccion asigna la sección 410 de "450002" a "docente410@example.invalid", la 411 de "450002" a "docente411@example.invalid" y la 412 de "450002" y las secciones 410 y 412 de "450010" a "docente.varias@example.invalid", y no tiene filas de "coordinacion@example.invalid"
    Y ninguna de las cinco secciones de 2026-2 tiene cargas

  # US-38: El reporte solo muestra mis secciones
  # El alcance sale solo de app/permisos.secciones_visibles(), el único dueño de la regla de visibilidad
  # (BR-ACCESO-07). La ruta 12 no recibe identificadores de sección ni de carga (J-23), así que no tiene un
  # caso 403 propio, y FastAPI ignora los parámetros que la ruta no declara.

  @US-38 @corte1 @spec004
  Escenario: El reporte del profesor de varias secciones no trae las de otros profesores
    Dado que la sección 410 de "450002" tiene una carga PUBLICADA de "sintetico_20262_450002_410.xlsx", subida por "docente410@example.invalid"
    Y que la sección 411 de "450002" tiene una carga PUBLICADA de "export_inventado_411.xlsx", subida por "docente411@example.invalid"
    Y que "docente.varias@example.invalid" tiene publicadas sus tres secciones
    Y que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces la API responde 200 con 3 secciones, la 412 de "450002" y la 410 y la 412 de "450010"
    Pero la respuesta no trae la sección 410 de "450002" ni la 411 de "450002"

  @US-38 @corte1 @spec004
  Esquema del escenario: Cada profesor de una sección ve solo la suya
    Dado que la sección 410 de "450002" tiene una carga PUBLICADA de "sintetico_20262_450002_410.xlsx", subida por "docente410@example.invalid"
    Y que la sección 411 de "450002" tiene una carga PUBLICADA de "export_inventado_411.xlsx", subida por "docente411@example.invalid"
    Y que "<correo>" tiene la sesión iniciada con rol "PROFESOR"
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces la API responde 200 con 1 sección, la <propia> de "450002", con el carga_id de su propia carga
    Pero la respuesta no trae la sección <ajena> de "450002"

    Ejemplos:
      | correo                     | propia | ajena |
      | docente410@example.invalid | 410    | 411   |
      | docente411@example.invalid | 411    | 410   |

  @US-38 @corte1 @spec004
  Escenario: Un seccion_id en la consulta no abre otra sección
    Dado que la sección 410 de "450002" tiene una carga PUBLICADA de "sintetico_20262_450002_410.xlsx", subida por "docente410@example.invalid"
    Y que "docente411@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando se envía GET /api/resultados?periodo=2026-2&seccion_id={seccion_id de la sección 410 de "450002"}
    Entonces la API responde 200 con el mismo cuerpo que sin el parámetro seccion_id, solo con la sección 411 de "450002"
    Pero la respuesta no trae la sección 410 de "450002"

  # BR-ACCESO-06. La API lee de la base en cada petición el usuario, su rol y sus secciones. El dueño de la
  # base retira la asignación solo en esta base desechable, porque abet_app no borra filas.
  @US-38 @corte1 @spec004
  Escenario: El alcance se lee de la base en cada petición
    Dado que la sección 410 de "450002" tiene una carga PUBLICADA de "sintetico_20262_450002_410.xlsx", subida por "docente410@example.invalid"
    Y que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que GET /api/resultados?periodo=2026-2 le responde 200 con la sección 410 de "450002"
    Cuando el dueño de la base retira la fila de acceso.docente_seccion que asigna la 410 a "docente410@example.invalid"
    Y se envía otra vez GET /api/resultados?periodo=2026-2 con la misma cookie
    Entonces la API responde 200 con 0 secciones

  # (propuesta) El texto del 401, el de BR-ACCESO-06.
  @US-38 @corte1 @spec004
  Esquema del escenario: Sin una sesión vigente no hay resultados
    Dado <caso>
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces la API responde 401 con el cuerpo {"detail": "La sesión venció. Ingrese otra vez."} y sin secciones

    Ejemplos:
      | caso                                                                                        |
      | una petición sin la cookie abet_sesion                                                      |
      | que la sesión de "docente410@example.invalid" está vencida                                  |
      | que "docente410@example.invalid" tiene la sesión iniciada y después su usuario pasa a activo falso |

  # (propuesta) El texto del 422, el de BR-PERIODO-04.
  @US-38 @corte1 @spec004
  Escenario: Un periodo mal formado responde 422
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando se envía GET /api/resultados?periodo=2026-13
    Entonces la API responde 422 con el cuerpo {"detail": "El periodo no tiene la forma AAAA-C."} y sin secciones

  # (propuesta) La guardia de sesión por router y su lista cerrada de rutas públicas (J-25 y BR-ACCESO-10).
  # La API no publica /docs ni /redoc (docs_url y redoc_url en None, app/main.py). El 403 de un identificador
  # que no existe sigue siendo una propuesta de BR-ACCESO-08.
  @US-38 @corte1 @spec004
  Escenario: Ninguna ruta con datos responde sin sesión
    Dado la lista cerrada de rutas públicas, que son POST /api/sesion, DELETE /api/sesion, POST /api/sesion/codigo cuando exista y GET /api/openapi.json
    Cuando una prueba recorre todas las rutas registradas en la aplicación y llama a cada una sin la cookie abet_sesion
    Entonces cada ruta fuera de esa lista responde 401, también GET /api/resultados
    Y cada ruta que recibe un seccion_id o un carga_id responde 403 con el cuerpo {"detail": "La sección no está a su cargo."} cuando "docente411@example.invalid" le pasa uno de la sección 410 de "450002"

  @US-38 @corte1 @spec004 @delegado_a_vitest
  Escenario: P6 no ofrece subir exports
    Dado P6 abierta por "docente.varias@example.invalid" y, en otra prueba, por "coordinacion@example.invalid"
    Entonces P6 no tiene ningún botón «Subir export», que sigue solo en P2, en cada sección del profesor con plan de medición

  # US-42: El reporte no expone a estudiantes ni a otros usuarios
  # La ruta arma cada objeto campo por campo contra una lista cerrada, sin SELECT * (AD-14 de la revisión).

  @US-42 @corte1 @spec004
  Escenario: La respuesta trae solo las claves de la lista cerrada
    Dado que "docente.varias@example.invalid" tiene publicadas sus tres secciones
    Y que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces el cuerpo trae solo periodo, so y secciones, y cada elemento de so trae solo numero y descripcion
    Y cada sección trae solo seccion_id, asignatura, numero, estado, carga_id, pi, conjunto_reglas, conjunto_reglas_estado, parametros_pendientes, provisional e indicadores
    Y cada indicador trae solo so, pi, instrumento, nivel_esperado, estudiantes_por_nivel, logrados, calificados, sin_evidencia, total, pct_sobre_calificados, pct_sobre_total, meta_pct y en_meta
    Pero ninguna parte del cuerpo trae subida_por, nombre_archivo, sha256, trato_sin_evidencia ni pct_logro_segun_regla

  @US-42 @corte1 @spec004
  Escenario: La respuesta no trae códigos, nombres ni correos
    Dado que "docente.varias@example.invalid" tiene publicadas sus tres secciones
    Y que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces el cuerpo no trae ningún número de 8 dígitos, ningún «@» ni el texto «Inventado» de la columna Last Name de los exports

  @US-42 @corte1 @spec004
  Esquema del escenario: Ninguna respuesta de la ruta queda en una caché
    Dado <caso>
    Cuando se envía GET /api/resultados?periodo=<periodo>
    Entonces la API responde <estado> con la cabecera Cache-Control "no-store"

    Ejemplos:
      | caso                                                                         | periodo | estado |
      | que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR" | 2026-2  | 200    |
      | una petición sin la cookie abet_sesion                                       | 2026-2  | 401    |
      | que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR" | 2026-13 | 422    |

  @US-42 @corte1 @spec004 @delegado_a_vitest
  Escenario: P6 no guarda nada en el navegador
    Dado P6 abierta por "docente.varias@example.invalid" con la respuesta de sus tres secciones
    Entonces window.localStorage y window.sessionStorage quedan con 0 entradas, como comprueba tests/App.test.tsx con P1 a P4
