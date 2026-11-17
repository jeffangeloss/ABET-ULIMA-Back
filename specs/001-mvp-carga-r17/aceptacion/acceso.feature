# language: es
#
# Escenarios de aceptación de US-05 y US-06 (corte 1) y US-20 (corte 2) de la spec 001-mvp-carga-r17.
# Parten de las candidatas C-06, C-07 y la baja de C-04 de revision-historias.md, con las correcciones
# de la auditoría de verificabilidad, la fusión de la regla de visibilidad en US-06 que pide la auditoría
# de tamaño y el faltante del envío del código de revision-historias.md, según las secciones 2, 4, 5 y 7
# de las decisiones de documentación del 2026-10-28 (carpeta de trabajo de la sesión, fuera del
# repositorio).
# La identidad de la semana 1 es una contraseña asignada (J-03); el código por correo llega en el
# corte 2. Ninguna contraseña aparece escrita aquí; cada prueba genera la suya al azar y no la
# guarda en el repositorio.
# Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide quien apruebe la spec.
# Este archivo es criterio escrito. Los pasos de pantalla, que nombran P2, sus filas o sus botones, los
# comprueban las pruebas de Vitest del Front (T045), y los demás, pytest contra un PostgreSQL 18
# desechable (T051).

Característica: Acceso al sistema y visibilidad de las secciones

  Cada usuario autorizado entra con su correo y su contraseña asignada, recibe una sesión en la
  cookie HttpOnly abet_sesion y ve solo lo que su rol alcanza. El profesor ve sus secciones y el
  coordinador ve todas las de la carrera, porque los de arriba ven hacia abajo y no al revés.

  Antecedentes:
    Dado la base con los datos inventados de 2026-2 de periodo_2026_2_inventado.sql
    Y "coordinacion@example.invalid" activo con rol "COORDINADOR" y sin secciones en acceso.docente_seccion
    Y "docente410@example.invalid" activo con rol "PROFESOR" y la sección 410 de 450002 en 2026-2
    Y "docente411@example.invalid" activo con rol "PROFESOR" y la sección 411 de 450002 en 2026-2
    Y la API configurada con PERIODO_VIGENTE "2026-2" y CONJUNTO_REGLAS "R-2026-BORRADOR"

  # US-05: Iniciar sesión con contraseña asignada
  # (propuesta) El comando de asignar contraseña corre con la conexión directa del dueño de la base,
  # no con abet_app, y lee la contraseña de la entrada estándar sin mostrarla.
  # (propuesta) El mensaje único de 401, el límite de 5 intentos fallidos por correo en 15 minutos
  # y la respuesta 204 del cierre de sesión.

  @US-05 @corte1
  Escenario: El administrador técnico asigna una contraseña por comando
    Cuando el administrador técnico corre el comando de asignar contraseña para "docente410@example.invalid" con una contraseña de prueba generada al azar
    Entonces acceso.credencial tiene 1 fila de ese usuario cuyo hash empieza por "$argon2id$"
    Y el texto de la contraseña no aparece en ninguna fila del esquema acceso
    Y la salida del comando no muestra la contraseña

  @US-05 @corte1
  Escenario: Un usuario autorizado entra con su contraseña
    Dado que "docente410@example.invalid" tiene asignada una contraseña de prueba
    Cuando se envía POST /api/sesion con ese correo y esa contraseña
    Entonces la API responde 200 con el correo "docente410@example.invalid" y el rol "PROFESOR"
    Y la respuesta fija la cookie "abet_sesion" con HttpOnly, Secure, SameSite=Lax y Max-Age 43200
    Y acceso.sesion tiene 1 fila nueva de ese usuario con expira_en 12 horas después de creada_en
    Y esa fila guarda el hash del token y no el valor de la cookie
    Y GET /api/sesion con esa cookie responde 200 con el correo "docente410@example.invalid" y el rol "PROFESOR"
    Y los registros de la API de esas peticiones no contienen la contraseña ni el valor de la cookie

  @US-05 @corte1
  Escenario: El correo se compara sin espacios ni mayúsculas
    Dado que "docente410@example.invalid" tiene asignada una contraseña de prueba
    Cuando se envía POST /api/sesion con el correo " Docente410@EXAMPLE.invalid " y esa contraseña
    Entonces la API responde 200 con el correo "docente410@example.invalid"

  @US-05 @corte1
  Esquema del escenario: Un intento fallido no revela si el correo está autorizado
    Dado que "docente410@example.invalid" tiene asignada una contraseña de prueba y "docente411@example.invalid" no tiene ninguna
    Cuando se envía POST /api/sesion con el correo "<correo>" y <contraseña>
    Entonces la API responde 401 con el cuerpo {"detail": "Correo o contraseña incorrectos."}
    Y la respuesta no trae la cabecera Set-Cookie
    Y acceso.sesion no gana ninguna fila

    Ejemplos:
      | correo                      | contraseña                                       |
      | desconocido@example.invalid | una contraseña cualquiera                        |
      | docente410@example.invalid  | la contraseña asignada con un carácter cambiado  |
      | docente411@example.invalid  | una contraseña cualquiera                        |

  @US-05 @corte1
  Escenario: Cinco intentos fallidos bloquean el correo por 15 minutos
    Dado que "docente410@example.invalid" y "docente411@example.invalid" tienen asignada una contraseña de prueba
    Cuando se envía 5 veces POST /api/sesion con el correo "docente410@example.invalid" y una contraseña distinta dentro de 15 minutos
    Y se envía una sexta vez con la contraseña correcta
    Entonces la sexta respuesta es 429 con el cuerpo {"detail": "Demasiados intentos. Espere 15 minutos."}
    Y acceso.sesion no gana ninguna fila de ese usuario
    Pero POST /api/sesion de "docente411@example.invalid" con su contraseña correcta responde 200

  @US-05 @corte1
  Escenario: Cerrar la sesión vence la cookie y la fila
    Dado que "docente410@example.invalid" tiene la sesión iniciada y la cookie "abet_sesion"
    Cuando se envía DELETE /api/sesion con esa cookie
    Entonces la API responde 204 y la cookie "abet_sesion" vuelve con Max-Age 0
    Y la fila de acceso.sesion de esa cookie sigue en la tabla con expira_en menor o igual que la hora del cierre
    Y GET /api/sesion con la cookie anterior responde 401

  @US-05 @corte1
  Escenario: Una sesión vencida no da acceso
    Dado que "docente410@example.invalid" tiene una sesión cuyo expira_en es de hace 1 minuto
    Cuando se envía GET /api/secciones?periodo=2026-2 con esa cookie
    Entonces la API responde 401
    Y la respuesta no trae ninguna sección

  @US-05 @corte1
  Escenario: Un usuario dado de baja deja de entrar
    Dado que "docente410@example.invalid" tiene la sesión iniciada y la cookie "abet_sesion"
    Cuando el administrador técnico marca a ese usuario como inactivo en acceso.usuario_autorizado
    Entonces GET /api/sesion con la cookie anterior responde 401
    Y GET /api/secciones?periodo=2026-2 con la cookie anterior responde 401
    Y POST /api/sesion con su contraseña correcta responde 401 con el mismo cuerpo que da a un correo desconocido

  @US-05 @corte1
  Esquema del escenario: Sin sesión ninguna ruta de datos responde
    Dado una petición sin la cookie "abet_sesion"
    Cuando se envía <método> <ruta>
    Entonces la API responde 401
    Y abet.archivo_origen y abet.carga no ganan ninguna fila

    Ejemplos:
      | método | ruta                                         |
      | GET    | /api/sesion                                  |
      | POST   | /api/secciones/{sección 410}/cargas          |
      | GET    | /api/cargas/{carga publicada de la 410}      |
      | GET    | /api/cargas/{carga publicada de la 410}/r17.xlsx |

  # US-06: Ver solo mis secciones del periodo
  # Esta historia es la dueña única de la regla de visibilidad; las demás solo repiten el caso de
  # su propia ruta. (propuesta) El valor "SIN_CARGA" del estado y el texto del 403.

  @US-06 @corte1
  Escenario: El profesor ve únicamente su sección
    Dado que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía GET /api/secciones?periodo=2026-2
    Entonces la API responde 200 con 1 sección
    Y esa sección es la 410 de 450002 "Principios de Ingeniería Sostenible" en 2026-2, con los PI 5.1, 5.2 y 5.3 y el estado de carga "SIN_CARGA"
    Y la respuesta no trae ningún dato de la sección 411
    Y la pantalla P2 «Mis secciones» muestra 1 fila con el estado "Sin carga"

  @US-06 @corte1
  Escenario: El coordinador ve todas las secciones de la carrera
    Dado que "coordinacion@example.invalid" tiene la sesión iniciada
    Cuando se envía GET /api/secciones?periodo=2026-2
    Entonces la API responde 200 con las secciones 410 y 411 de 450002 en 2026-2
    Pero acceso.docente_seccion sigue sin filas de "coordinacion@example.invalid"

  @US-06 @corte1
  Escenario: El estado refleja la carga publicada
    Dado que la sección 410 tiene una carga en estado "PUBLICADA" con 11 filas leídas y 11 aceptadas
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía GET /api/secciones?periodo=2026-2
    Entonces la sección 410 trae el estado de carga "PUBLICADA" con filas_leidas 11 y filas_aceptadas 11
    Y la pantalla P2 muestra en la sección 410 "Publicada, 11 de 11 filas aceptadas"

  # La fila del POST manda el mismo export que la 411 tiene publicado, porque una ruta que busca la huella
  # antes que el alcance responde 200 con la constancia de esa carga. El orden lo fijan las reglas de negocio
  # (business rules, BR) BR-CARGA-03, en sus pasos 1 y 6, y BR-CARGA-09.
  @US-06 @corte1
  Esquema del escenario: El profesor no alcanza una sección ajena escribiendo la ruta
    Dado que la sección 411 tiene una carga PUBLICADA del export inventado de la 411, con los códigos 99000012 a 99000022
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía <método> <ruta> <cuerpo>
    Entonces la API responde 403 con el cuerpo {"detail": "La sección no está a su cargo."}
    Y la respuesta no trae ningún dato de la sección 411 ni de su carga
    Y abet.archivo_origen y abet.carga no ganan ninguna fila

    Ejemplos:
      | método | ruta                                       | cuerpo                                                          |
      | POST   | /api/secciones/{sección 411}/cargas        | con "export_inventado_411.xlsx" en el campo multipart «archivo» |
      | GET    | /api/cargas/{carga de la 411}              | sin cuerpo                                                      |
      | GET    | /api/cargas/{carga de la 411}/r17.xlsx     | sin cuerpo                                                      |

  @US-06 @corte1
  Escenario: Sin sesión no hay lista
    Dado una petición sin la cookie "abet_sesion"
    Cuando se envía GET /api/secciones?periodo=2026-2
    Entonces la API responde 401
    Y la respuesta no trae ninguna sección

  @US-06 @corte1
  Escenario: Sección de una asignatura sin plan de medición
    Dado la sección 410 de la asignatura "450010" en 2026-2, sin curso_blackboard, asignada también a "docente410@example.invalid"
    Y que abet.plan_medicion no tiene filas de 450010 en 2026-2
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía GET /api/secciones?periodo=2026-2
    Y se abre la pantalla P2 «Mis secciones»
    Entonces la API responde 200 con la sección 410 de 450010 con tiene_plan falso y sin PI, y la sección 410 de 450002 con tiene_plan verdadero
    Y la fila de 450010, sección 410, muestra "La carrera aún no registra el plan de medición de esta sección"
    Y el botón "Subir export" de esa fila está desactivado
    Pero la fila de 450002, sección 410, conserva el botón "Subir export" activo

  # US-20: Recibir el código de acceso en el correo institucional
  # Corte 2. El proveedor de correo queda abierto (J-04); las pruebas usan su modo de prueba, que
  # guarda los mensajes en un buzón de prueba sin enviarlos.
  # (propuesta) La respuesta 202, la verificación del código en POST /api/sesion con correo y código,
  # los textos de error y el límite de 3 pedidos por correo en 15 minutos. El código tiene 6 dígitos,
  # vence a los 10 minutos, sirve una sola vez y admite 5 intentos, como en las candidatas.

  @US-20 @corte2
  Escenario: Un usuario autorizado recibe su código
    Cuando se envía POST /api/sesion/codigo con el correo "docente410@example.invalid"
    Entonces la API responde 202 con el cuerpo {"detail": "Si el correo está autorizado, recibirá un código en unos minutos."}
    Y el buzón de prueba tiene 1 mensaje para "docente410@example.invalid" con un código de 6 dígitos
    Y acceso.codigo_acceso tiene 1 fila de ese usuario con el hash del código, no el código, y una vigencia de 10 minutos

  @US-20 @corte2
  Esquema del escenario: La respuesta es la misma exista o no el correo
    Dado que "<correo>" <situación>
    Cuando se envía POST /api/sesion/codigo con el correo "<correo>"
    Entonces la API responde 202 con el mismo cuerpo que recibe un correo autorizado
    Y el buzón de prueba no gana ningún mensaje
    Y acceso.codigo_acceso no gana ninguna fila

    Ejemplos:
      | correo                      | situación                                    |
      | desconocido@example.invalid | no figura en acceso.usuario_autorizado       |
      | docente411@example.invalid  | figura con activo falso                      |
      | sin-arroba.example.invalid  | no tiene la forma de un correo               |

  @US-20 @corte2
  Escenario: El código vigente abre la sesión
    Dado que "docente410@example.invalid" tiene un código pedido hace 2 minutos
    Cuando se envía POST /api/sesion con ese correo y el código del buzón de prueba
    Entonces la API responde 200 y fija la cookie "abet_sesion" con HttpOnly, Secure, SameSite=Lax y Max-Age 43200
    Y acceso.sesion tiene 1 fila nueva de ese usuario

  @US-20 @corte2
  Esquema del escenario: Un código que ya no sirve no abre sesión
    Dado que "docente410@example.invalid" <situación>
    Cuando se envía POST /api/sesion con ese correo y <código>
    Entonces la API responde 401 con el cuerpo {"detail": "<mensaje>"}
    Y acceso.sesion no gana ninguna fila

    Ejemplos:
      | situación                                              | código                    | mensaje                                   |
      | tiene un código pedido hace 11 minutos                 | ese código                | El código venció. Pida uno nuevo.          |
      | ya tiene usado el código de su último pedido           | el mismo código           | El código ya se usó. Pida uno nuevo.       |
      | tiene 5 intentos con códigos distintos del suyo        | el código correcto        | El código ya no es válido. Pida uno nuevo. |

  @US-20 @corte2
  Escenario: Pedir códigos en ráfaga no llena el buzón
    Dado que "docente410@example.invalid" tiene 3 códigos pedidos en los últimos 15 minutos
    Cuando se envía otra vez POST /api/sesion/codigo con ese correo
    Entonces la API responde 202 con el mismo cuerpo de siempre
    Y el buzón de prueba no gana un cuarto mensaje para ese correo
