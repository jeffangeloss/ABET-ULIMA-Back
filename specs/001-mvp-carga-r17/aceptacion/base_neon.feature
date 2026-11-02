# language: es
#
# Escenarios de aceptación de US-01 a US-04 (corte 1) de la spec 001-mvp-carga-r17.
# Parten de las candidatas C-01 a C-05 de revision-historias.md con las correcciones de la auditoría de
# verificabilidad y las fusiones de la auditoría de tamaño, según el mapa de la sección 2 de las
# decisiones de documentación del 2026-10-28 (carpeta de trabajo de la sesión, fuera del repositorio).
# Todo dato es inventado. Los correos de prueba terminan en @example.invalid y ninguna credencial
# aparece en este archivo; las claves viven solo en variables de entorno de la terminal.
# Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide quien apruebe la spec.
#
# Dónde corre cada escenario. Las pruebas de aceptación corren siempre contra un PostgreSQL 16
# desechable. Solo los escenarios de US-01 que migran y controlan la base son criterios de despliegue
# que no escriben cargas, y se comprueban en el proyecto de Neon en la región aws-sa-east-1 con
# PostgreSQL 16, con NEON_HOST, NEON_DB, NEON_DB_USER y NEON_DB_PASSWORD definidas solo en el entorno de
# la terminal del administrador técnico y NEON_HOST con el host de la conexión directa, sin «-pooler».

Característica: Base del MVP en Neon con el rol de la aplicación y los datos inventados de 2026-2

  La carrera de Ingeniería Ambiental tiene su base en la nube con el mismo esquema que prueban las
  bases desechables, un rol de aplicación que no borra ni cambia reglas, el periodo 2026-2 sembrado
  con datos inventados y los usuarios autorizados en un esquema acceso aparte de abet.

  # US-01: Migrar y verificar la base en Neon

  @US-01 @corte1
  Escenario: Primera migración en una base vacía
    Dado que la base de Neon no tiene el esquema abet
    Cuando el administrador técnico ejecuta "flyway -environment=neon migrate"
    Entonces "flyway -environment=neon info" muestra las versiones 1.01 a 1.08 en estado "Success"
    Y muestra las migraciones repetibles "vista r17 por pi" y "vista tabla maestra pi" en estado "Success"
    Y abet.so tiene 7 filas, abet.pi tiene 17 y abet.rubrica_nivel tiene 102
    Y abet.asignatura tiene 53 filas, abet.asignatura_so tiene 61 y abet.instrumento tiene 7
    Y abet.conjunto_reglas tiene el conjunto "R-2026-BORRADOR" en estado "BORRADOR"
    Y pg_class.reloptions de abet.v_r17_por_pi y de abet.v_tabla_maestra_pi contiene "security_barrier=true"

  @US-01 @corte1
  Escenario: Repetir la migración no aplica nada nuevo
    Dado que la base de Neon ya tiene aplicadas las versiones 1.01 a 1.08
    Cuando el administrador técnico ejecuta otra vez "flyway -environment=neon migrate"
    Entonces Flyway informa 0 migraciones aplicadas
    Y abet.pi sigue con 17 filas

  @US-01 @corte1
  Escenario: Clean prohibido en la base compartida
    Dado que la base de Neon ya tiene aplicadas las versiones 1.01 a 1.08
    Cuando el administrador técnico ejecuta "flyway -environment=neon clean"
    Entonces Flyway termina con un código de salida distinto de 0 y un mensaje que nombra cleanDisabled
    Y abet.pi sigue con 17 filas

  @US-01 @corte1
  Escenario: Ninguna credencial queda en lo que sigue git
    Dado que el administrador técnico guarda la conexión de Neon solo en un archivo local .env.neon
    Cuando se busca el valor de NEON_DB_PASSWORD en los archivos que lista "git ls-files" y en la salida de "git log -p --all" del repositorio que guarda las migraciones
    Entonces el valor no aparece en ningún archivo seguido ni en ningún commit, incluido flyway.toml
    Y "git check-ignore -v .env.neon" responde con la regla ".env.*" de .gitignore
    Y "bash scripts/preflight.sh" termina sin fallas de la regla 3 ni de la regla 4

  @US-01 @corte1
  Escenario: Las consultas de control pasan en la base recién preparada
    Dado la base de Neon con las migraciones aplicadas y los datos inventados del periodo 2026-2 de US-03
    Y una conexión con el usuario abet_respaldo
    Cuando el administrador técnico corre controles_neon.sql, copia de las consultas Q01 a Q14 de pruebas.sql como consultas sueltas
    Entonces cada una de las consultas Q01 a Q14 devuelve 0 filas

  @US-01 @corte1
  Escenario: Las consultas de control no escriben en la base
    Dado la base de Neon con las migraciones aplicadas y una conexión con el usuario abet_respaldo
    Y el número de filas de abet.carga anotado antes de empezar
    Cuando el administrador técnico corre controles_neon.sql
    Entonces "SHOW default_transaction_read_only" devuelve "on" en esa sesión
    Y abet.carga tiene el mismo número de filas que antes de correr el script

  @US-01 @corte1
  Escenario: La CI del Back reproduce la base desde cero sin Redgate
    Dado el contenido de bd/ trasladado a db/ del Back con su historia de git
    Cuando la CI del Back corre correr_pruebas.sh con psql contra un PostgreSQL 16 desechable
    Entonces la salida del paso termina con "RESULTADO: todo pasó" y el código de salida es 0
    Y ningún archivo de .github/workflows/ del Back nombra una imagen o una acción de Redgate o de Flyway
    Y "git log --follow -m" del archivo V1_07__crear_registro_cargas.sql en el Back muestra los commits que tenía en ABET_ULIMA

  # US-02: Crear el rol de la aplicación con privilegio mínimo
  # (propuesta) La clave de abet_app se lee de la variable APP_DB_CLAVE, como POWERBI_CLAVE en
  # crear_roles_lectura.sql. Un solo rol en el MVP, por la decisión J-02.

  @US-02 @corte1
  Escenario: El script crea abet_app sin atributos de administración
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09
    Y la variable APP_DB_CLAVE definida solo en el entorno de la terminal
    Cuando el administrador técnico corre db/plataforma/neon/crear_rol_app.sql con psql
    Entonces pg_roles muestra abet_app con rolcanlogin verdadero
    Y rolsuper, rolbypassrls, rolcreaterole, rolcreatedb y rolreplication de abet_app son falsos
    Y la salida del script no muestra el valor de APP_DB_CLAVE

  @US-02 @corte1
  Escenario: abet_app publica una carga válida en una sola transacción
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09, el rol de crear_rol_app.sql y los datos de periodo_2026_2_inventado.sql
    Y una conexión con el usuario abet_app
    Y la sección 411 de 450002 en 2026-2 sin ninguna carga
    Cuando la aplicación inserta en una sola transacción el archivo_origen, la carga, 3 carga_columna, 11 estudiante con los códigos 99000012 a 99000022, 11 carga_fila y 33 medicion de la sección 411
    Y actualiza esa carga a estado "PUBLICADA" con filas_leidas 11, filas_aceptadas 11, filas_rechazadas 0 y terminada_en no nulo
    Entonces la transacción confirma sin errores
    Y la consulta de control Q08 devuelve 0 filas

  @US-02 @corte1
  Escenario: abet_app lee las vistas del R-17
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09, el rol de crear_rol_app.sql y los datos de periodo_2026_2_inventado.sql
    Y una conexión con el usuario abet_app
    Cuando consulta "SELECT count(*) FROM abet.v_r17_por_pi" y "SELECT count(*) FROM abet.v_tabla_maestra_pi"
    Entonces las dos consultas responden sin error de permisos

  @US-02 @corte1
  Esquema del escenario: abet_app no puede borrar ni vaciar tablas de abet
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09, el rol de crear_rol_app.sql y los datos de periodo_2026_2_inventado.sql
    Y una conexión con el usuario abet_app
    Y una carga PUBLICADA de la sección 410 con 33 mediciones
    Cuando ejecuta "<orden> abet.<tabla>"
    Entonces PostgreSQL responde "permission denied for table <tabla>"
    Y abet.medicion sigue con las 33 filas de la carga de la sección 410

    Ejemplos:
      | orden       | tabla          |
      | DELETE FROM | medicion       |
      | DELETE FROM | carga_fila     |
      | DELETE FROM | carga          |
      | DELETE FROM | archivo_origen |
      | DELETE FROM | rechazo_fila   |
      | DELETE FROM | estudiante     |
      | TRUNCATE    | medicion       |
      | TRUNCATE    | carga          |

  @US-02 @corte1
  Esquema del escenario: abet_app solo actualiza el estado y los conteos de una carga
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09, el rol de crear_rol_app.sql y los datos de periodo_2026_2_inventado.sql
    Y una conexión con el usuario abet_app
    Y una carga PUBLICADA de la sección 410 hecha con "R-2026-BORRADOR"
    Cuando ejecuta un UPDATE de la columna <columna> de esa fila de abet.carga
    Entonces PostgreSQL responde "permission denied for table carga"
    Y la carga conserva su valor anterior en <columna>

    Ejemplos:
      | columna            |
      | conjunto_reglas_id |
      | subida_por         |
      | archivo_id         |
      | seccion_id         |
      | reemplaza_carga_id |

  @US-02 @corte1
  Esquema del escenario: abet_app no escribe reglas, catálogo ni datos del periodo
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09, el rol de crear_rol_app.sql y los datos de periodo_2026_2_inventado.sql
    Y una conexión con el usuario abet_app
    Cuando ejecuta un <orden> sobre abet.<tabla>
    Entonces PostgreSQL responde "permission denied for table <tabla>"

    Ejemplos:
      | orden  | tabla             |
      | UPDATE | conjunto_reglas   |
      | INSERT | conjunto_reglas   |
      | UPDATE | parametro_valor   |
      | UPDATE | catalogo_version  |
      | INSERT | catalogo_vigencia |
      | INSERT | plan_medicion     |
      | UPDATE | seccion           |

  # (propuesta) En acceso, abet_app lee usuarios, credenciales, asignaciones, sesiones e intentos
  # fallidos. En el corte 1 solo inserta sesiones (usuario_id y hash_token) e intentos fallidos
  # (hash_cuenta), con las fechas que pone la base, y no actualiza credencial. Los códigos de acceso
  # llegan en el corte 2 (US-20). El cierre de sesión vence la fila con un UPDATE que fija expira_en en
  # least(expira_en, clock_timestamp()), porque el rol no borra.
  @US-02 @corte1
  Esquema del escenario: abet_app no borra ni da de alta usuarios en acceso
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09, el rol de crear_rol_app.sql y los datos de periodo_2026_2_inventado.sql
    Y una conexión con el usuario abet_app
    Cuando ejecuta <orden> sobre acceso.<tabla>
    Entonces PostgreSQL responde "permission denied for table <tabla>"

    Ejemplos:
      | orden                                         | tabla              |
      | un DELETE                                     | usuario_autorizado |
      | un DELETE                                     | sesion             |
      | un DELETE                                     | credencial         |
      | un DELETE                                     | docente_seccion    |
      | un INSERT de un usuario nuevo                 | usuario_autorizado |
      | un UPDATE que cambia el rol a "COORDINADOR"   | usuario_autorizado |
      | un INSERT que asigna la sección 411 al usuario de "docente410@example.invalid" | docente_seccion |

  # (propuesta) El callback afterMigrate repone también los permisos de abet_app. La prueba aplica con
  # psql una migración de prueba y después el callback, como hace Flyway al terminar cada migrate.
  @US-02 @corte1
  Escenario: Los permisos de abet_app sobreviven a una nueva migración
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09 y abet_app creado con crear_rol_app.sql
    Cuando la prueba aplica con psql una migración de prueba y después db/callbacks/afterMigrate__permisos_lectura.sql
    Entonces has_table_privilege('abet_app', 'abet.medicion', 'INSERT') devuelve verdadero
    Y has_table_privilege('abet_app', 'abet.medicion', 'DELETE') devuelve falso
    Y has_table_privilege('abet_app', 'abet.v_r17_por_pi', 'SELECT') devuelve verdadero

  # US-03: Preparar el periodo 2026-2 con datos inventados

  @US-03 @corte1
  Escenario: Sembrar la vigencia, las secciones 410 y 411 y el plan de 450002
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09 y sin datos operativos de 2026-2
    Cuando el administrador técnico ejecuta db/datos/periodo_2026_2_inventado.sql con los valores que entrega el coordinador
    Entonces abet.catalogo_vigencia tiene 1 fila de Ambiental en 2026-2 con la versión "AMB-2026"
    Y abet.seccion tiene las secciones 410 y 411 de 450002 en 2026-2 con curso_blackboard "SINTETICO_20262_450002_410" y "SINTETICO_20262_450002_411"
    Y abet.plan_medicion tiene 3 filas de 450002 en 2026-2, con los PI 5.1, 5.2 y 5.3 del SO 5
    Y la consulta de control Q05 devuelve 0 filas
    Y abet.estudiante, abet.carga y abet.medicion siguen con 0 filas

  # (propuesta) El script se puede repetir sin duplicar nada.
  @US-03 @corte1
  Escenario: Repetir el script de datos no duplica filas
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09 y periodo_2026_2_inventado.sql ya aplicado
    Cuando el administrador técnico lo ejecuta otra vez
    Entonces abet.catalogo_vigencia, abet.seccion y abet.plan_medicion tienen el mismo número de filas que después de la primera ejecución
    Y acceso.usuario_autorizado y acceso.docente_seccion tienen el mismo número de filas que después de la primera ejecución

  @US-03 @corte1
  Escenario: El número de sección no admite ceros a la izquierda
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09 y los datos de periodo_2026_2_inventado.sql
    Cuando el administrador técnico inserta la sección "0410" de 450002 en 2026-2
    Entonces la base rechaza la fila por la restricción "ck_seccion_numero"

  @US-03 @corte1
  Escenario: El script de datos solo trae datos inventados
    Cuando se buscan en periodo_2026_2_inventado.sql los números de 8 dígitos y los correos
    Entonces todo número de 8 dígitos empieza con 99
    Y todo correo termina en "@example.invalid"

  # (propuesta) La API valida su configuración al arrancar, porque la base no marca un periodo ni
  # un conjunto de reglas como vigente (faltante del periodo vigente en revision-historias.md).
  @US-03 @corte1
  Esquema del escenario: La API no arranca con un periodo o un conjunto de reglas que la base no conoce
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09 y los datos de periodo_2026_2_inventado.sql
    Y la API configurada con PERIODO_VIGENTE "<periodo>" y CONJUNTO_REGLAS "<conjunto>"
    Cuando la API arranca contra esa base
    Entonces el arranque se detiene con el mensaje "<mensaje>"
    Y abet.carga no gana ninguna fila

    Ejemplos:
      | periodo | conjunto        | mensaje                                             |
      | 2027-1  | R-2026-BORRADOR | PERIODO_VIGENTE 2027-1 no existe en abet.periodo     |
      | 2026-2  | R-NO-EXISTE     | CONJUNTO_REGLAS R-NO-EXISTE no existe para Ambiental |

  # US-04: Registrar usuarios autorizados y docentes por sección
  # (propuesta) Los nombres ck_usuario_autorizado_rol, ck_usuario_autorizado_correo,
  # uq_usuario_autorizado_correo y fk_docente_seccion_seccion se fijan al escribir V1_09.

  @US-04 @corte1
  Escenario: V1_09 crea el esquema acceso y los motivos nuevos
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_08
    Y db/flyway.toml con schemas ["abet", "acceso"] en sus entornos
    Cuando la prueba aplica V1_09__crear_acceso.sql con psql, como correr_pruebas.sh
    Entonces psql termina con código de salida 0
    Y el esquema acceso tiene las tablas usuario_autorizado, credencial, sesion, intento_fallido, docente_seccion y codigo_acceso
    Y abet.carga tiene la columna subida_por, que admite nulo y tiene una FK hacia acceso.usuario_autorizado
    Y ck_rechazo_fila_motivo admite "COLUMNA_CODIGO_AUSENTE", "PI_REPETIDO", "PERIODO_NO_COINCIDE" y "SECCION_SIN_DECLARAR" además de los 10 motivos de V1_07
    Y cada una de las consultas de control Q01 a Q14 sigue en 0 filas

  @US-04 @corte1
  Escenario: Las cargas anteriores a V1_09 conservan subida_por nulo
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_08 y la carga PUBLICADA de la sección 410 de db/pruebas/datos_sinteticos.sql
    Cuando la prueba aplica V1_09__crear_acceso.sql con psql
    Entonces esa carga sigue en estado "PUBLICADA" con subida_por nulo
    Y cada una de las consultas de control Q01 a Q14 sigue en 0 filas

  @US-04 @corte1
  Escenario: El script de datos registra a los usuarios de prueba y sus secciones
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09
    Cuando el administrador técnico ejecuta db/datos/periodo_2026_2_inventado.sql
    Entonces acceso.usuario_autorizado tiene estos usuarios activos
      | correo                       | rol         |
      | coordinacion@example.invalid | COORDINADOR |
      | docente410@example.invalid   | PROFESOR    |
      | docente411@example.invalid   | PROFESOR    |
    Y acceso.docente_seccion asigna la sección 410 de 450002 en 2026-2 a "docente410@example.invalid" y la sección 411 a "docente411@example.invalid"
    Y acceso.docente_seccion no tiene filas de "coordinacion@example.invalid"
    Y acceso.credencial no tiene filas, porque la contraseña se asigna aparte con el comando de US-05

  @US-04 @corte1
  Esquema del escenario: La base rechaza un registro de acceso inválido
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09 y los usuarios de prueba registrados por periodo_2026_2_inventado.sql
    Cuando el administrador técnico <acción>
    Entonces la base rechaza la fila por la restricción "<restricción>"

    Ejemplos:
      | acción                                                                     | restricción                  |
      | inserta el usuario "otro@example.invalid" con rol "ADMIN"                   | ck_usuario_autorizado_rol    |
      | inserta otra vez el usuario "docente410@example.invalid" con rol "PROFESOR" | uq_usuario_autorizado_correo |
      | inserta el usuario " Docente412@EXAMPLE.invalid " sin normalizar             | ck_usuario_autorizado_correo |
      | asigna otra vez la sección 410 a "docente410@example.invalid"               | uq_docente_seccion           |
      | asigna a "docente410@example.invalid" una seccion_id que no existe          | fk_docente_seccion_seccion   |

  @US-04 @corte1
  Escenario: Los correos solo viven en acceso.usuario_autorizado
    Dado una base PostgreSQL 16 desechable con V1_01 a V1_09 y los usuarios de prueba registrados por periodo_2026_2_inventado.sql
    Cuando el administrador técnico corre la consulta de control Q04
    Y corre la consulta Q15, nueva en pruebas.sql, que aplica el filtro de columnas de Q04 al esquema acceso
    Entonces Q04 devuelve 0 filas
    Y Q15 devuelve solo la columna de correo de acceso.usuario_autorizado
