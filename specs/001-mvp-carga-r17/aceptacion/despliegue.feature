# language: es
#
# Escenarios de aceptación de US-17 (corte 1) de la spec 001-mvp-carga-r17.
# Cubre los faltantes de despliegue y de prueba de punta a punta de revision-historias.md con las
# decisiones de la sección 7 de las decisiones de documentación del 2026-10-28 (carpeta de trabajo de la
# sesión, fuera del repositorio) y el cambio de la crítica de arquitectura (dos proyectos de Vercel con reescritura de rutas al mismo origen desde el Front).
# Las variables del Back las pega Jefferson en Vercel, nunca un agente, y ningún valor aparece aquí.
# El piloto solo trata datos inventados. Para datos reales el camino es otro (primero Cloud Run en
# southamerica-east1 y después Vercel Pro, con la autorización de la universidad, D-10).
# Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide quien apruebe la spec.

Característica: Piloto desplegado en Vercel con Neon y probado de punta a punta

  El Back y el Front viven en dos proyectos de Vercel Hobby en la región iad1, junto a Neon (J-17), el Front reescribe
  /api hacia el Back para que el navegador vea un solo origen, la API se conecta a Neon por el pooler con
  el rol abet_app, y una prueba de humo recorre en la nube el camino del profesor desde el ingreso
  hasta el R-17.

  Antecedentes:
    Dado los proyectos de Vercel Hobby "abet-ulima-back" y "abet-ulima-front" en el equipo "jeffangeloss-projects"
    Y la base de Neon del piloto con V1_01 a V1_09, el rol abet_app, la guardia de datos inventados y los datos de periodo_2026_2_inventado.sql

  # US-17: Desplegar el piloto en Vercel con Neon y probarlo de punta a punta

  @US-17 @corte1
  Esquema del escenario: Cada proyecto fija la región iad1
    Cuando se lee el vercel.json de la rama main de <repositorio>
    Entonces su clave "regions" vale ["iad1"]
    Y "vercel inspect" del último despliegue de Production de <proyecto> muestra sus funciones en iad1

    Ejemplos:
      | repositorio      | proyecto         |
      | ABET-ULIMA-Back  | abet-ulima-back  |
      | ABET-ULIMA-Front | abet-ulima-front |

  @US-17 @corte1
  Escenario: El Front reescribe /api hacia el Back y todo queda en un solo origen
    Cuando se lee el vercel.json del Front
    Y se envía GET /api/sesion sin cookie a la URL de Production del Front
    Entonces el vercel.json del Front tiene un rewrite con source "/api/:path*" hacia la URL del Back
    Y la respuesta es 401 en JSON con la clave "detail", como la da el Back
    Y la respuesta no trae la cabecera Access-Control-Allow-Origin

  @US-17 @corte1
  Escenario: La cookie de sesión es de primera parte y nunca pasa por el almacenamiento del navegador
    Dado que "docente410@example.invalid" tiene asignada una contraseña de prueba en la base del piloto
    Cuando ingresa con Playwright en la pantalla P1 de la URL de Production del Front
    Entonces la cabecera Set-Cookie de "abet_sesion" llega desde el origen del Front, sin atributo Domain y con HttpOnly, Secure y SameSite=Lax
    Y la siguiente petición del Front a /api/sesion lleva la cookie y responde 200 con el rol "PROFESOR"
    Y localStorage y sessionStorage del origen del Front no tienen ningún valor que contenga el token de la sesión
    Y document.cookie en la página no muestra "abet_sesion"

  @US-17 @corte1
  Esquema del escenario: Las variables del Back están en Vercel y no en el repositorio
    Cuando se listan con "vercel env ls production" las variables del proyecto "abet-ulima-back"
    Entonces la lista incluye <variable>
    Y .env.example del Back nombra <variable> sin valor

    Ejemplos:
      | variable                 |
      | DATABASE_URL             |
      | SESION_SECRETO           |
      | PERIODO_VIGENTE          |
      | CONJUNTO_REGLAS          |
      | GUARDIA_DATOS_INVENTADOS |

  @US-17 @corte1
  Esquema del escenario: Los secretos del Back no quedan en ningún repositorio
    Dado el valor de <secreto> que Jefferson pega en Vercel, leído solo en la terminal de quien revisa
    Cuando se busca ese valor en los archivos que lista "git ls-files" y en la salida de "git log -p --all" de ABET-ULIMA-Back y de ABET-ULIMA-Front
    Entonces el valor no aparece en ningún archivo seguido ni en ningún commit
    Y "bash scripts/preflight.sh" termina sin fallas en los dos repositorios

    Ejemplos:
      | secreto        |
      | DATABASE_URL   |
      | SESION_SECRETO |

  @US-17 @corte1
  Escenario: La API se conecta a Neon por el pooler con el rol abet_app
    Dado DATABASE_URL de Production con un host que contiene "-pooler" y el usuario abet_app
    Cuando la prueba envía 20 peticiones seguidas a GET /api/secciones?periodo=2026-2 con la sesión de "coordinacion@example.invalid"
    Entonces las 20 respuestas son 200 con las secciones 410 y 411
    Y los registros de la función de esas peticiones no muestran ningún error "prepared statement" de psycopg
    Y pg_stat_activity de la base del piloto muestra las conexiones de la API con usename "abet_app"

  # La única carga que se escribe en Neon es la de la prueba de humo, en la rama de Preview.
  @US-17 @corte1
  Escenario: Preview trabaja sobre otra rama de Neon
    Dado un despliegue de Preview de "abet-ulima-back" construido desde develop
    Cuando se compara el host de DATABASE_URL del alcance Preview con el de Production
    Y la prueba de humo sube su export inventado desde la URL de Preview
    Entonces los dos hosts son de ramas distintas de Neon
    Y abet.carga de la rama de Production no gana ninguna fila
    Pero abet.carga de la rama de Preview gana 1 fila

  @US-17 @corte1
  Escenario: Production sale solo de main
    Cuando se revisa la configuración de Git de los dos proyectos de Vercel
    Entonces la rama de Production de cada proyecto es main
    Y un push a develop crea un despliegue de Preview y no cambia el despliegue de Production

  @US-17 @corte1
  Escenario: El equipo de Vercel no comparte el contenido para entrenar modelos
    Cuando se revisa la configuración del equipo "jeffangeloss-projects" en Vercel
    Entonces el uso del contenido del equipo para entrenar modelos de IA está desactivado

  # El registro de la aplicación solo se promete en la forma de T038, que guarda de un rechazo por la
  # guardia la huella SHA-256 (Secure Hash Algorithm de 256 bits) y la hora. Aquí se lee en los registros
  # de la función de Vercel.
  @US-17 @corte1
  Escenario: La guardia de datos inventados está encendida en el piloto
    Dado que "docente410@example.invalid" tiene la sesión iniciada en la URL de Production del Front
    Y los conteos de abet.archivo_origen, abet.carga y abet.estudiante anotados antes de empezar
    Y un export de 11 filas cuya fila 4 trae el código 10000004 en Username, que la prueba arma en memoria porque tests/datos_inventados/ solo admite códigos que empiezan con 99
    Cuando sube ese export en la sección 410
    Entonces la API responde 422 con el cuerpo {"detail": "El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada."}
    Y abet.archivo_origen, abet.carga y abet.estudiante tienen los mismos conteos que antes
    Y pg_constraint de la base del piloto tiene la restricción "ck_estudiante_codigo_inventado" en abet.estudiante
    Y el registro de la aplicación en Vercel guarda de esa petición solo la huella y la hora del rechazo, sin el código 10000004 ni ningún valor de Last Name o First Name del export

  # J-09 decide si la prueba de humo corre en la CI o contra la vista previa. Valor provisional, contra la
  # vista previa de develop antes de pasar a main, sobre su rama de Neon, que se restablece desde la rama
  # principal para que la sección 410 no tenga cargas. La prueba de humo no corre en Production.
  @US-17 @corte1 @humo
  Escenario: Prueba de humo de punta a punta con el export que trae el 5 en la fila 3
    Dado un despliegue de Preview de "abet-ulima-back" y de "abet-ulima-front" construido desde develop
    Y que la sección 410 de 450002 en 2026-2 no tiene ninguna carga en la rama de Neon de ese despliegue
    Y que "docente410@example.invalid" tiene asignada una contraseña de prueba en esa base
    Cuando Playwright para Node ingresa con ese correo en la pantalla P1 de la URL de Preview del Front
    Y abre la sección 410 en la pantalla P2 «Mis secciones»
    Y sube "tests/datos_inventados/export_inventado_410_con_error.xlsx" en la pantalla P3
    Y descarga el R-17 desde la pantalla P4
    Entonces la pantalla P4 muestra 11 filas leídas, 10 aceptadas y 1 rechazada, con el rechazo de la fila 3 en el PI 5.2
    Y el archivo descargado se llama "R017_450002_410_2026-2_PROVISIONAL.xlsx"
    Y el R-17 muestra 60,0 % (6 de 10) en el PI 5.1, 60,0 % (6 de 10) en el PI 5.2 y 70,0 % (7 de 10) en el PI 5.3, con meta 80 %
    Y la tabla de estudiantes del R-17 tiene 30 filas y ninguna del código 99000002
    Y el R-17 tiene la hoja «Constancia» con 11 leídas, 10 aceptadas y 1 rechazada
    Y abet.v_r17_por_pi de esa carga en la rama de Neon de Preview da 60,0, 60,0 y 70,0
    Y cada una de las consultas de control Q01 a Q14 devuelve 0 filas en la rama de Neon de Preview
    Pero abet.carga de la rama de Production no gana ninguna fila
