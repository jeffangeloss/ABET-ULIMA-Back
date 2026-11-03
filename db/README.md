# Base de datos ABET_SIS_MED

Esta carpeta es la semilla del repositorio de la base de datos del sistema de medición ABET de la Carrera de Ingeniería Ambiental. La base se construye como código, con migraciones versionadas de Flyway sobre PostgreSQL 18, en pasos pequeños que dos personas pueden revisar en una sesión. Cada cambio del esquema entra como un archivo nuevo y nunca como una edición manual de la base.

## Contenido de la carpeta

| Ruta | Para qué sirve |
| --- | --- |
| `flyway.toml` | Configuración de Flyway, con los esquemas `abet` y `acceso`, el entorno local `dev`, el entorno `neon` y las credenciales tomadas de variables de entorno |
| `migration/` | Migraciones versionadas `V1_01` a `V1_09` y repetibles `R__` con las vistas |
| `callbacks/afterMigrate__permisos_lectura.sql` | Callback de Flyway que, al final de cada migrate, repone los permisos de los roles de lectura y del respaldo y el SELECT de las dos vistas de `abet_app` |
| `plataforma/neon/crear_roles_lectura.sql` | Script que se corre en Neon para crear los roles de solo lectura de Power BI y del respaldo |
| `referencia/ambiental_2026.json` | Datos curriculares de Ambiental, con los resultados del estudiante (student outcomes, SO), los indicadores de desempeño (performance indicators, PI), la rúbrica, las competencias y las asignaturas, sin datos personales |
| `herramientas/generar_v1_03.py` | Generador determinista de `V1_03` a partir de la referencia, con la huella SHA-256 del JSON |
| `plataforma/neon/crear_rol_app.sql` | Rol de la aplicación con privilegio mínimo, `abet_app` por defecto |
| `plataforma/neon/guardia_datos_inventados.sql` | Guardia `ck_estudiante_codigo_inventado`, solo para Neon, con la sentencia que la retira |
| `plataforma/neon/controles_neon.sql` | Consultas de control Q01 a Q14 en solo lectura, para Neon |
| `plataforma/neon/marcar_entorno.sql` | Marca de entorno de Vercel de cada rama (`abet.entorno`), production en la principal y preview en `develop` (T077) |
| `datos/periodo_2026_2_inventado.sql` | Datos inventados del periodo 2026-2, con la vigencia, las secciones 410 y 411, el plan y los usuarios de prueba |
| `datos/varias_secciones_2026_2_inventado.sql` | Datos inventados del profesor con varias secciones en 2026-2, con el plan de 450010, la 412 de 450002, la 410 y la 412 de 450010 y sus asignaciones |
| `pruebas/datos_sinteticos.sql` | Datos inventados con la forma de un export real de Blackboard |
| `pruebas/pruebas.sql` | Aserciones que lanzan ERROR si algo no se cumple |
| `pruebas/probar_rol_app.sql` | Lo que el rol de la aplicación puede y no puede hacer |
| `pruebas/probar_guardia.sql` | La guardia de datos inventados en una base aparte |
| `pruebas/correr_pruebas.sh` | Corre todas las pruebas sobre bases desechables, sin Flyway |
| `pruebas/cluster_desechable.sh` | Arranca y apaga el clúster de PostgreSQL desechable donde `correr_pruebas.sh` crea sus bases fuera de la CI |
| `../.github/workflows/ci.yml` | Job `pruebas` de la integración continua (continuous integration, CI), que corre `pruebas/correr_pruebas.sh` con `psql` sobre un PostgreSQL 18 desechable, sin Flyway ni Redgate |
| `herramientas/respaldar_neon.sh` | Respaldo de la base en Neon con `pg_dump` 18, comprobado con `pg_restore --list` y cifrado con `gpg` |
| `../.github/workflows/respaldo_neon.yml` | Respaldo de Neon a mano desde la pestaña Actions, guardado cifrado como artefacto durante 14 días |

## Qué crea la entrega 1

Todo vive en el esquema `abet`, el primero de `schemas = ["abet", "acceso"]` en `[environments.dev]`, que Flyway crea con `createSchemas = true` en `[flyway]`. En el formato TOML, `schemas` es un ajuste del entorno y no se acepta en `[flyway]`. Las migraciones de la entrega 1 no ejecutan `CREATE SCHEMA` y califican cada objeto con `abet.`; V1_09 es la excepción que explica la sección siguiente. Cada archivo contiene DDL o datos, nunca ambos, y las reglas viven en restricciones declarativas (claves primarias, UNIQUE, claves foráneas compuestas, CHECK e índices únicos parciales), sin disparadores ni funciones.

| Migración | Tipo | Qué hace |
| --- | --- | --- |
| `V1_01__crear_organizacion.sql` | DDL | Facultad, carrera, periodo (código «2026-2»), asignatura (código de 4 o 6 dígitos como texto) y sección (periodo + asignatura + número, sin ceros a la izquierda) |
| `V1_02__crear_catalogo_curricular.sql` | DDL | Versión de catálogo con huella SHA-256 y aprobación por cargo, vigencia de una sola versión por carrera y periodo y, colgando de la versión, SO, PI (código de texto «5.1»), rúbrica, instrumentos, plan de estudios, asignatura por SO, competencias, competencia por SO y asignatura por competencia con estadío |
| `V1_03__cargar_referencia_ambiental.sql` | Datos | Catálogo AMB-2026 en BORRADOR, generado por `herramientas/generar_v1_03.py`; termina con una aserción que detiene la migración si un conteo no coincide |
| `V1_04__crear_plan_medicion.sql` | DDL | Plan de medición por periodo, asignatura y PI, solo con la versión vigente de la carrera y solo para PI de un SO que la asignatura tributa |
| `V1_05__crear_reglas_versionadas.sql` | DDL | Conjunto de reglas, parámetros de lista cerrada, valores DEFINIDO o PENDIENTE con dominio por clave y tabla de conversión de niveles |
| `V1_06__cargar_reglas_borrador.sql` | Datos | Conjunto R-2026-BORRADOR con META_LOGRO 0,80 y NIVEL_ESPERADO 3; el resto queda PENDIENTE |
| `V1_07__crear_registro_cargas.sql` | DDL | Archivo de origen (huella única, filas de datos y tipo de fuente), carga (carrera, estados, reemplazo y conteos conciliados con el archivo), columnas reconocidas por el código exacto del PI y rechazos sin valores leídos |
| `V1_08__crear_mediciones.sql` | DDL | Estudiante (solo el código de 8 dígitos) y medición (nivel 1 a 4 o SIN_EVIDENCIA) |
| `R__vista_r17_por_pi.sql` | Vista | Números del R-17 por carga PUBLICADA y PI, con el conteo por nivel 1 a 4, el nivel esperado y la meta del conjunto de reglas de la carga |
| `R__vista_tabla_maestra_pi.sql` | Vista | Tabla_Maestra_PI con las columnas que Power BI espera hoy, más ESTADO DE EVIDENCIA |

El bloque `DO` del final de `V1_03` es la única excepción a la regla de no usar plpgsql dentro de las migraciones. Fuera de ellas, el callback de permisos y el script de roles de Neon usan bloques `DO` para no fallar cuando un rol todavía no existe. Funciona como aserción de carga (7 SO, 17 PI, 102 descriptores de rúbrica, 11 competencias, 7 pares competencia y SO, 53 asignaturas, 53 filas de plan de estudios, 61 pares asignatura y SO, 95 pares asignatura y competencia, además de 7 instrumentos) y en T-SQL se traduce a `IF ... THROW`.

La vista del R-17 muestra dos porcentajes con nombres explícitos, uno sobre los calificados y otro sobre el total que incluye SIN_EVIDENCIA, porque la carrera todavía no fija el trato del estudiante sin evidencia (H08). La columna `pct_logro_segun_regla` toma uno u otro según TRATO_SIN_EVIDENCIA y sale NULL mientras ese parámetro siga PENDIENTE. La columna `provisional` vale verdadero mientras el conjunto de reglas de la carga no esté APROBADO o le falte DEFINIR NIVEL_ESPERADO, META_LOGRO o TRATO_SIN_EVIDENCIA. Si el conjunto de reglas de la carga no tiene NIVEL_ESPERADO DEFINIDO, los conteos contra el esperado y los dos porcentajes salen NULL y nunca 0, mientras el conteo por nivel 1 a 4 sigue disponible. En la vista de la tabla maestra, PROFESOR queda NULL porque docentes, roles y ámbitos entran en la entrega 2, y el SO y el ciclo del curso salen del catálogo, nunca del número de sección.

## Qué agrega V1_09 (corte 1 del MVP)

`V1_09__crear_acceso.sql` prepara la base para la aplicación del producto mínimo viable (minimum viable product, MVP) de `specs/001-mvp-carga-r17/`. Crea el esquema `acceso` con los usuarios autorizados, porque la consulta de control Q04 falla si `abet` tiene nombres o datos de contacto, agrega a `abet.carga` la columna `subida_por` y amplía la lista de motivos de `abet.rechazo_fila` sin editar V1_07. A `abet.rechazo_fila` le suma también la columna `pi_id`, con el PI del plan que falta en el export o que el export repite.

| Objeto | Qué guarda |
| --- | --- |
| `acceso.usuario_autorizado` | Correo normalizado y único (`ck_usuario_autorizado_correo` y `uq_usuario_autorizado_correo`), rol PROFESOR o COORDINADOR (`ck_usuario_autorizado_rol`) y `activo`, que da de baja sin borrar |
| `acceso.credencial` | Hash Argon2id de la contraseña asignada (`ck_credencial_hash`) y la hora de su asignación |
| `acceso.sesion` | Hash SHA-256 del token de la cookie `abet_sesion` (`uq_sesion_token`) y su vencimiento, de 12 horas como máximo (`ck_sesion_vigencia`). El cierre de sesión fija `expira_en = least(expira_en, clock_timestamp())` y no borra la fila, porque sin `least()` el cierre de una sesión ya vencida pasa ese tope y la base lo rechaza |
| `acceso.intento_fallido` | Un intento fallido de ingreso por fila, con el código de autenticación de mensajes basado en hash (hash-based message authentication code, HMAC) del correo normalizado (`ck_intento_fallido_hash`) y su hora, exista o no ese correo en `usuario_autorizado`. El límite de 5 intentos en 15 minutos de US-05 vive en la base porque Vercel no guarda memoria entre peticiones, y cuenta igual un correo desconocido y uno autorizado, así que la respuesta no revela cuál está autorizado |
| `acceso.docente_seccion` | Sección que dicta cada profesor (`uq_docente_seccion` y `fk_docente_seccion_seccion`), fuente de la regla de visibilidad, con más de un docente por sección si hace falta |
| `acceso.codigo_acceso` | Hash del código de 6 dígitos del corte 2 (US-20), con vencimiento de 10 minutos y hasta 5 intentos |
| `abet.carga.subida_por` | Usuario que sube la carga (`fk_carga_subida_por`), nulo en las cargas anteriores a V1_09 |
| `ck_rechazo_fila_motivo` | Los 10 motivos de V1_07 más COLUMNA_CODIGO_AUSENTE, PI_REPETIDO, PERIODO_NO_COINCIDE y SECCION_SIN_DECLARAR |
| `abet.rechazo_fila.pi_id` | PI del plan que falta en el export (PI_DEL_PLAN_AUSENTE) o que el export repite (PI_REPETIDO), con `fk_rechazo_fila_pi` hacia `abet.pi`, para que la constancia leída después nombre el mismo PI que la respuesta de la subida. `ck_rechazo_fila_pi` lo admite solo con esos dos motivos, y queda nulo en los demás motivos y en los rechazos anteriores a V1_09 |

Con `createSchemas = true`, Flyway crea en cada `migrate` el esquema de la lista `schemas` que falte, aunque la base ya tenga su historial, y lo anota en `flyway_schema_history` como «<< Flyway Schema Creation >>». En una base con V1_01 a V1_08 cuyo entorno lista `acceso`, como `abet_sis_med_dev` con el entorno `dev`, el siguiente `migrate` crea así el esquema antes de V1_09, y el `CREATE SCHEMA IF NOT EXISTS` de V1_09, la única migración que crea un esquema, solo avisa que ya existe. Esa sentencia queda para los caminos con `psql`, como el ensayo de Neon de las pruebas, y para un entorno que no liste `acceso`. Ninguna tabla guarda en claro una contraseña, un token, un código ni el correo escrito en un intento fallido, y el correo de `acceso.usuario_autorizado` es el único dato de contacto de la base. La consulta Q15 de `pruebas/pruebas.sql` aplica el filtro de Q04 al esquema `acceso` y solo encuentra esa columna.

## Scripts de plataforma y de datos

Lo que depende del alojamiento o del periodo queda fuera de `migration/`, porque una migración corre igual en la CI, en la Mac y en Neon y no se edita después de aplicarse. Estos scripts se corren a mano con `psql`, cada uno abre y cierra su propia transacción y todos se pueden repetir sin efecto nuevo.

| Archivo | Qué hace | Dónde corre |
| --- | --- | --- |
| `plataforma/neon/crear_rol_app.sql` | Crea el rol de la aplicación, `abet_app` o el que fije `-v rol_app=<nombre>`, y deja sus permisos exactamente como los declara su cabecera, con una comprobación final que deshace todo si algo no cuadra. La contraseña sale de la variable de entorno `APP_DB_CLAVE` con `\getenv`, como en `crear_roles_lectura.sql` | Neon y las bases de ensayo de las pruebas |
| `plataforma/neon/guardia_datos_inventados.sql` | Agrega `ck_estudiante_codigo_inventado CHECK (codigo LIKE '99%')` a `abet.estudiante`, que con `ck_estudiante_codigo` solo admite 99000000 a 99999999, y trae escrita la sentencia que la retira cuando la universidad autorice los datos reales (D-10) | Solo Neon y la base de la prueba de la guardia |
| `plataforma/neon/controles_neon.sql` | Copia literal de Q01 a Q14 de `pruebas/pruebas.sql` como consultas sueltas, en una sesión de solo lectura, que termina con error si alguna devuelve filas | Neon con `abet_respaldo` y las bases de ensayo |
| `plataforma/neon/marcar_entorno.sql` | Deja el comentario de la base en `abet.entorno=production` o `abet.entorno=preview` (`COMMENT ON DATABASE`), a partir de `-v entorno=production` o `-v entorno=preview`, y `comprobar_base` de `app/configuracion.py` lo compara con `VERCEL_ENV` al arrancar en Vercel (T077). Lo corre el dueño de la base, que en Neon no es superusuario |
| `datos/periodo_2026_2_inventado.sql` | Siembra la vigencia AMB-2026 en 2026-2, las secciones 410 y 411 de 450002, su plan con 5.1, 5.2 y 5.3, un coordinador y dos profesores con correos `@example.invalid` y la sección de cada profesor, sin contraseñas. Usa `ON CONFLICT DO NOTHING` y se detiene si una fila existente no es la esperada | Neon, las pruebas y, cuando haga falta, `abet_sis_med_dev` |
| `datos/varias_secciones_2026_2_inventado.sql` | Completa los datos de 2026-2 con `docente.varias@example.invalid`, un profesor activo y sin contraseña que dicta la 412 de 450002 y la 410 y la 412 de 450010, cada una con su curso de Blackboard, y con su asignación en `acceso.docente_seccion`. Siembra además el plan de 450010, con 2.1 y 2.2 del SO 2 y 5.1 del SO 5 y el instrumento Trabajo Integrador, en tres PI porque los bloques I y II del R-17 tienen tres filas fijas. Se aplica después de `periodo_2026_2_inventado.sql`, no cambia ninguna de sus filas, usa `ON CONFLICT DO NOTHING` y se detiene si faltan esos datos o si un dato no queda como dice su cabecera | Las pruebas, entre ellas las bases desechables de `varias_secciones.feature`, y, cuando haga falta, `abet_sis_med_dev`. No entra en Neon (T027) |

El rol de la aplicación hace INSERT en las siete tablas de una carga, UPDATE solo de `estado`, `filas_leidas`, `filas_aceptadas`, `filas_rechazadas` y `terminada_en` de `abet.carga` y SELECT sobre el resto de `abet` y las dos vistas, salvo `flyway_schema_history`. En `acceso` lee usuarios, credenciales, asignaciones, sesiones e intentos fallidos, inserta solo `usuario_id` y `hash_token` de una sesión y `hash_cuenta` de un intento, y actualiza solo `sesion.expira_en`. Así las fechas de una sesión y de un intento salen siempre de la base, y el tope de 12 horas corre desde la hora real de la sesión. No tiene DELETE ni TRUNCATE en ninguna tabla, no escribe reglas, catálogo, plan, secciones, usuarios ni credenciales y no toca `acceso.codigo_acceso` hasta el corte 2. Convive con `abet_lectura`, `powerbi_lectura` y `abet_respaldo`, que siguen de solo lectura.

## Orden en Neon (T027)

T027 parte del `git subtree pull` de `preparacion-neon` (T023), que trae a `db/` el entorno `neon` de `flyway.toml` con `schemas = ["abet", "acceso"]`, `callbacks/afterMigrate__permisos_lectura.sql`, `plataforma/neon/crear_roles_lectura.sql` y las dos R__ con `security_barrier` que T021 aplica en Neon. Como esas R__ son las mismas que Neon ya tiene, un `migrate` desde este `db/` no las vuelve a aplicar ni les quita los permisos.

T027 aplica lo nuevo primero en la rama `develop` de Neon y después en la principal, siempre con la conexión directa, sin «-pooler», y con el usuario dueño del proyecto, salvo el paso de las consultas de control, que usa `abet_respaldo`. Los comandos corren desde `db/`, y las claves llegan desde el gestor de claves de Jefferson por variables de entorno, como `PGPASSWORD` o `~/.pgpass`, nunca por un archivo del repositorio. El usuario `abet_respaldo` existe desde que `plataforma/neon/crear_roles_lectura.sql` prepara los roles de lectura. En el proyecto ABET-ULIMA ese script corre al comienzo de T027, con `POWERBI_CLAVE` y `RESPALDO_DB_CLAVE` en la terminal (apartado «Roles de solo lectura»).

1. `flyway -environment=neon info` y `flyway -environment=neon migrate`, que crea `acceso` y aplica V1_09. Después, `flyway info` muestra una segunda fila «<< Flyway Schema Creation >>», la de `acceso`, antes de la versión 1.09.
2. `crear_rol_app.sql`, con `APP_DB_CLAVE` definida en la terminal. Sin esa variable el rol queda sin contraseña y T028 la asigna después. Después de un `migrate` que vuelve a aplicar una R__, el callback repone el SELECT de las dos vistas del rol, y en los caminos con psql este paso se repite.
3. `guardia_datos_inventados.sql`.
4. `periodo_2026_2_inventado.sql`.
5. `controles_neon.sql` con `abet_respaldo`, que debe terminar con «RESULTADO: Q01 a Q14 devuelven 0 filas.».
6. La consulta de `security_barrier` de la comprobación final de `crear_roles_lectura.sql`, que debe devolver 0 filas.

Desde T077, cada rama lleva además su marca de entorno, con `marcar_entorno.sql` y `-v entorno=production` en la principal o `-v entorno=preview` en `develop`. La marca es el comentario de la base, que solo su dueño puede cambiar. Neon la copia al crear o restablecer una rama desde otra, así que esa rama nace con la marca `production`. Hasta volver a marcarla con `preview`, la API de Preview no arranca contra ella, y la de Production arrancaría si su `DATABASE_URL` apuntara por error a esa rama. Por eso volver a marcar es el primer paso después de crear o restablecer `develop`, antes de cualquier despliegue.

`varias_secciones_2026_2_inventado.sql` no entra en este orden. Sus datos sirven a los escenarios de `varias_secciones.feature`, que corren en bases desechables como toda prueba de aceptación (Principio V de la constitución), y en el piloto D-09 y D-13 fijan el plan de 450002 y un coordinador con dos profesores de prueba. Si Jefferson decide llevar al piloto el profesor con varias secciones, el archivo va entre los pasos 4 y 5, y cambian con él D-09, D-13, T027 y el escenario del pooler de `despliegue.feature`, que espera las secciones 410 y 411.

```sh
CONEXION="host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=verify-full sslrootcert=system"
flyway -environment=neon info && flyway -environment=neon migrate
export APP_DB_CLAVE="$(openssl rand -hex 32)"    # se guarda en el gestor de claves
psql "$CONEXION" -v ON_ERROR_STOP=1 -f plataforma/neon/crear_rol_app.sql
psql "$CONEXION" -v ON_ERROR_STOP=1 -f plataforma/neon/guardia_datos_inventados.sql
psql "$CONEXION" -v ON_ERROR_STOP=1 -f datos/periodo_2026_2_inventado.sql
psql "host=$NEON_HOST dbname=$NEON_DB user=abet_respaldo sslmode=verify-full sslrootcert=system" \
     -f plataforma/neon/controles_neon.sql
psql "$CONEXION" -c "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'abet' AND c.relname IN ('v_tabla_maestra_pi', 'v_r17_por_pi')
       AND NOT coalesce(c.reloptions @> ARRAY['security_barrier=true'], false)"
```

La clave del rol va en hexadecimal porque la aplicación la usa dentro de `DATABASE_URL`, donde una «/» de base64 corta la cadena de conexión si no va codificada en porcentaje.

Con V1_09, `fk_carga_subida_por` ata `abet.carga` a `acceso.usuario_autorizado`, así que un volcado solo de `abet` ya no se restaura en una base vacía. Por eso el respaldo suma `acceso` sin los datos de `credencial`, `sesion`, `intento_fallido` ni `codigo_acceso` (J-10), como describe el apartado «Respaldo diario», y T027 lo prueba con una restauración real.

## Cómo correr las pruebas hoy, sin Flyway

El script regenera primero `V1_03` desde la referencia y la compara con la guardada. Después arma cuatro bases desechables y un rol de prueba, todos con el prefijo `abet_prueba` y el número del proceso en el nombre, aplica cada versionada con `psql -1 -v ON_ERROR_STOP=1`, en su transacción y en orden de versión, y luego las repetibles. Al terminar borra las bases y después el rol, aunque algo falle, porque los roles son del clúster y no de una base.

| Base | Qué prueba |
| --- | --- |
| `abet_prueba_a_<pid>` | Las migraciones en una base vacía con `abet` y `acceso` ya creados, como hace Flyway con `createSchemas`, los datos sintéticos, dos corridas de `datos/periodo_2026_2_inventado.sql`, dos de `datos/varias_secciones_2026_2_inventado.sql` y `pruebas/pruebas.sql` |
| `abet_prueba_b_<pid>` | Las mismas migraciones, para comparar el `pg_dump --schema-only` de las dos bases, y después el script de datos con un usuario de prueba de otro rol, que debe detenerse y deshacer todo. En esa base, el script de varias secciones debe detenerse sin los datos de 2026-2, sin una asignación, con una sección sin curso de Blackboard, con una asignación de más y con un segundo profesor de prueba en una de sus secciones, y después pasa dos veces sin duplicar filas, en una base sin los datos sintéticos |
| `abet_prueba_neon_<pid>` | El camino de Neon. V1_01 a V1_08 y las vistas, los datos sintéticos, `crear_rol_app.sql` antes de V1_09, que debe rechazar `abet_respaldo` y fallar sin dejar el rol, y después V1_09, que debe dejar el mismo esquema que una base nueva. Luego los scripts del orden de T027, las consultas de control, `pruebas/probar_rol_app.sql`, las R__ otra vez y las consultas de control con una carga REEMPLAZADA sin reemplazo, que deben terminar con error |
| `abet_prueba_guardia_<pid>` | La guardia, con `pruebas/probar_guardia.sql`, en una base sin cargas que recibe dos veces la guardia y los datos de 2026-2, y después la marca de entorno de `plataforma/neon/marcar_entorno.sql`, que un dueño sin superusuario pasa de preview a production, que el rol de la aplicación lee y no puede cambiar, y que rechaza otro valor o la falta de `-v entorno` sin cambiar la marca |

En la Mac, el script arranca su propio clúster de PostgreSQL desechable con `pruebas/cluster_desechable.sh` (initdb en una carpeta temporal y un socket propio, sin TCP), crea ahí todas sus bases y lo borra al terminar, así que nunca toca el clúster de `localhost:5432`, donde vive `abet_sis_med_dev`. El 2026-10-28 una prueba de mutación borró esa base, y desde entonces ninguna prueba crea ni borra bases en ese clúster. Para eso usa `initdb`, `pg_ctl`, `psql` y `pg_dump` de PostgreSQL 18, la versión de Neon (J-17): los de `PG_BIN`, si está definida, o los de Homebrew (`postgresql@18`), y se detiene si `initdb` es de otra versión. En la CI usa las variables estándar de libpq del job, con un `PGUSER` que puede crear bases y roles, como `postgres`. El rol de prueba nunca recibe contraseña, aunque la terminal tenga `APP_DB_CLAVE`.

```sh
export LC_ALL=en_US.UTF-8
PSQL=/opt/homebrew/opt/postgresql@18/bin/psql \
PG_DUMP=/opt/homebrew/opt/postgresql@18/bin/pg_dump \
./pruebas/correr_pruebas.sh
```

`PREFIJO_BD` cambia el prefijo de las bases y del rol desechables y `PYTHON` elige el intérprete del generador. La contraseña, si el servidor la pide, va en `PGPASSWORD` o en `~/.pgpass`, nunca en un archivo del repositorio.

Las pruebas cubren los conteos del catálogo y los números del R-17 de la sección 410 de 450002 en 2026-2 con 11 estudiantes inventados (63,6 % en 5.1, 63,6 % en 5.2 y 72,7 % en 5.3). Repiten ese R-17 con un NIVEL_ESPERADO PENDIENTE, que debe dar porcentajes NULL, y con TRATO_SIN_EVIDENCIA DEFINIDO en un conjunto en BORRADOR, que debe seguir provisional. La sección 7 de `pruebas/pruebas.sql` arma la carga del export con error, que trae un 5 en el PI 5.2 de la fila 3, como reemplazo de la del export correcto. Esa carga lee 11 filas, acepta 10, rechaza 1 por NIVEL_FUERA_DE_ESCALA y guarda 30 mediciones sin ese estudiante, con 60,0 %, 60,0 % y 70,0 % en el R-17 y Q01 a Q14 en cero dentro de su transacción. Las pruebas revisan también las columnas de la tabla maestra, 62 casos que la base debe rechazar con la restricción exacta que los rechaza (24 de ellos de V1_09) y ocho casos que debe aceptar. Las catorce consultas de control deben devolver 0 filas, entre ellas la conciliación de mediciones con filas aceptadas, las filas del archivo que no existen y la ausencia de columnas con nombres de personas. Los casos aceptados de la entrega 1 son la sección 301 en dos asignaturas, el reemplazo de una carga publicada con otro archivo y el reemplazo con el mismo archivo y un conjunto de reglas aprobado. Los de V1_09 son el esquema `acceso`, los datos de 2026-2 aplicados dos veces sobre los sintéticos, una fila válida de cada tabla de `acceso` con los 14 motivos de rechazo y dos cargas RECHAZADAS de la 410 con su PI en `pi_id`. Esas dos cargas guardan el PI 5.2 de PI_DEL_PLAN_AUSENTE y el 5.1 de PI_REPETIDO, ambos del plan de la sección. El octavo caso, A08, revisa los datos de varias secciones aplicados dos veces, con el plan 2.1, 2.2 y 5.1 de 450010, las cinco secciones con curso de Blackboard una sola vez y las tres secciones de `docente.varias@example.invalid`, y solo esas, cada una con los PI de su plan y sin carga. Entre los rechazos de V1_09, `ck_rechazo_fila_pi` rechaza un `pi_id` en un CODIGO_VACIO y `fk_rechazo_fila_pi` un `pi_id` que no existe en `abet.pi`. Cada consulta de control que vigila un caso que la base no puede impedir (Q06 a Q14) se prueba además sobre ese caso, en una transacción que se deshace. El archivo `controles_neon.sql` debe traer las mismas catorce consultas, salvo espacios, cada una sola entre su `\echo` y su `\set qNN :ROW_COUNT`, y su cierre debe sumarlas todas. Sus únicas órdenes de `psql` que fijan variables son `\set ON_ERROR_STOP 1`, esos catorce `\set` y el `\gset` del cierre, sin repetirse, así que una condición agregada, un `\set qNN` de más, un `\set` que no lee `:ROW_COUNT` o un control que falta rompen la prueba. La sección 8 publica además la carga de `export_inventado_411.xlsx`, con los códigos 99000012 a 99000022, junto a la de la 410, en una transacción que se deshace, con 63,6 %, 63,6 % y 72,7 % en la 411 y Q01 a Q14 en cero, Q08 entre ellas. La sección 9 publica a la vez, en otra transacción que se deshace, las cargas de los tres exports de `docente.varias@example.invalid`, una en cada una de sus secciones. Cada sección da en el R-17 sus cifras propias, que `tests/datos_inventados/README.md` anota, la 412 de 450002 no se mezcla con la 412 de 450010, la 410 de 450002 conserva sus cifras y Q01 a Q14 siguen en cero. La 410 y la 411 del caso de Q08 se buscan con su asignatura y no solo por su número, porque 450010 también tiene una 410.

La prueba del rol, `pruebas/probar_rol_app.sql`, actúa como el rol de prueba con `SET ROLE`, que aplica sus permisos igual que una conexión propia. Comprueba lo que el rol debe poder hacer, que es leer las vistas del R-17, publicar en una transacción la carga completa de la 411 con los códigos 99000012 a 99000022 y los niveles de `export_inventado_411.xlsx` y reconocer un estudiante existente. El rol registra además 5 intentos fallidos de un correo autorizado y 5 de uno desconocido, que suman lo mismo, y abre una sesión que cierra con `least()` sin borrarla. En dos cargas RECHAZADAS de la 410 guarda en `pi_id` el PI 5.2 de PI_DEL_PLAN_AUSENTE y el 5.1 de PI_REPETIDO, y la base le rechaza un `pi_id` en un CODIGO_VACIO. La prueba revisa también 43 sentencias que el rol debe recibir denegadas, entre ellas DELETE y TRUNCATE en `abet.carga`, el UPDATE de `carga.conjunto_reglas_id`, el INSERT y el UPDATE en `abet.parametro_valor`, una sesión o un intento con fechas que elige el rol y el cambio del `pi_id` de un rechazo, con la base sin cambios después. Antes, el ensayo de Neon de `correr_pruebas.sh` corre `crear_rol_app.sql` dos veces, con un permiso de más puesto a mano entre las dos corridas, para probar que el archivo deja el rol como lo declara. Después de esas pruebas aplica otra vez las R__, comprueba que el rol pierde el SELECT de las dos vistas y que una nueva corrida de `crear_rol_app.sql` se lo repone, como pide el orden de T027.

Los casos que deben fallar exigen la salida 3 de `psql` y su mensaje. El script de datos se detiene y deshace todo cuando un usuario de prueba ya existe con otro rol, `crear_rol_app.sql` rechaza `abet_respaldo` y falla sin dejar el rol en una base sin V1_09, y `controles_neon.sql` termina con error ante una carga REEMPLAZADA sin reemplazo, armada en una transacción que no se confirma. Ese último caso corre el archivo sin `-v ON_ERROR_STOP=1`, como el paso 5 del orden de T027, así que su salida 3 depende del `\set ON_ERROR_STOP 1` del propio archivo. El script de varias secciones se detiene y deshace todo sin los datos de 2026-2 y en una copia del archivo sin la asignación de la 410 de 450010. También se detiene con la 412 de 450010 ya registrada sin curso de Blackboard, con `docente.varias@example.invalid` asignado también a la 410 de 450002 y con `docente410@example.invalid` asignado también a la 410 de 450010, tres casos que se arman en una transacción que no se confirma. El último prueba el bloque de la comprobación final que deja un solo profesor de prueba en cada sección, porque en él `docente.varias@example.invalid` dicta exactamente sus tres secciones. La prueba de la guardia, `pruebas/probar_guardia.sql`, comprueba que 99000001 entra, que 10000004 y 98999999 se rechazan por `ck_estudiante_codigo_inventado`, que el rol de la aplicación no puede retirar la guardia y que la sentencia de retiro la quita en una transacción que se deshace.

## Cómo instalar Flyway en la Mac

Flyway 13 requiere Java 21 o posterior. La fórmula `flyway` de Homebrew depende de `openjdk`, que hoy instala openjdk 27. Redgate fija Java 21 como mínimo y el equipo usa la 21 LTS para no depender de la 27. Hay dos caminos recomendados.

El primero instala `openjdk@21` junto a la fórmula y fija `JAVA_HOME` en esa versión antes de llamar a Flyway.

```sh
brew install openjdk@21 flyway
export JAVA_HOME="$(brew --prefix openjdk@21)/libexec/openjdk.jdk/Contents/Home"
flyway --version
```

El lanzador que instala Homebrew respeta `JAVA_HOME`, así que basta exportarlo en la terminal donde se usa Flyway, sin cambiar el Java del sistema ni crear enlaces con `sudo`. La fórmula instala Flyway OSS Edition, la edición de código abierto con licencia Apache 2.0, que trae los comandos `info`, `migrate` y `validate` que el proyecto usa en la Mac y en Neon.

El segundo descarga el tarball de línea de comandos para macOS arm64 desde la página de descargas de Redgate, que trae su propio JRE, lo descomprime fuera del repositorio y agrega su carpeta al `PATH`. Los dos caminos pesan distinto. El tarball de macOS arm64 con JRE supera los 380 MB en GitHub y ronda los 570 MB en el sitio de descargas de Redgate, mientras que la fórmula de Homebrew baja el tarball sin JRE, de unos 324 MB, y le suma `openjdk` y `openjdk@21`. En cualquier caso conviene revisar antes el espacio libre en disco.

Si PostgreSQL de Homebrew no arranca por un error de configuración regional al iniciarlo a mano con `pg_ctl` o `initdb`, se exporta `LC_ALL=en_US.UTF-8` en la misma terminal. `brew services` ya fija esa variable por su cuenta.

## Comandos de Flyway

Las credenciales se leen de `ABET_DB_USER` y `ABET_DB_PASSWORD`, y el entorno `dev` apunta a `abet_sis_med_dev` en `localhost:5432`.

```sh
export ABET_DB_USER=...        # usuario de la base local
export ABET_DB_PASSWORD=...    # se escribe en la terminal o en un gestor de secretos, nunca en el repositorio
flyway info       # estado de cada migración
flyway migrate    # aplica las versionadas pendientes y luego las repetibles cambiadas
flyway validate   # comprueba que los archivos coinciden con lo aplicado (checksum)
```

Con el PostgreSQL de Homebrew, que autentica por `trust` en `localhost`, el usuario es el de macOS y la contraseña queda vacía. La base se crea una sola vez y Flyway hace el resto.

```sh
createdb -h localhost -p 5432 abet_sis_med_dev
export JAVA_HOME="$(brew --prefix openjdk@21)/libexec/openjdk.jdk/Contents/Home"
export ABET_DB_USER="$USER" ABET_DB_PASSWORD=""
flyway info && flyway migrate && flyway validate
```

Flyway corre en la Mac, con el orden `info`, `migrate` y `validate`, y en Neon, con el orden de T027. `flyway clean` está deshabilitado en `[flyway]`, pero `dev` es el entorno por defecto y el único definido, y lo permite para reconstruir la base local desde cero. En la práctica, toda ejecución sin `-environment` corre con `clean` permitido, lo que se acepta porque `abet_sis_med_dev` es desechable. Un entorno compartido, como el `neon` que usa T027, entra con su propio bloque `[environments.<nombre>]`, sin ese override, y se llama con `-environment=<nombre>`. La CI no corre Flyway ni usa Redgate. Su job `pruebas`, en `../.github/workflows/ci.yml`, aplica las migraciones con `psql` sobre un PostgreSQL 18 desechable, por medio de `pruebas/correr_pruebas.sh`.

## Estado de la base local

La base `abet_sis_med_dev` de la Mac de Jefferson está en la versión 1.08. El 22/10/2026, Flyway OSS 13.10.3 con openjdk 21.0.12 aplica las ocho versionadas y las dos repetibles en 0,25 segundos, `flyway validate` pasa con 11 migraciones y un segundo `flyway migrate` responde que el esquema está al día. El `pg_dump --schema-only` de esa base, sin la tabla `flyway_schema_history`, coincide línea por línea con el de una base armada con `psql` como en las pruebas, y los datos de referencia coinciden tabla por tabla. La base no tiene estudiantes ni mediciones, porque los datos sintéticos solo se cargan en las bases desechables de las pruebas. V1_09 todavía no está aplicada en esa base. El próximo `flyway migrate` crea antes `acceso`, porque el entorno `dev` lo lista en `schemas`, y después aplica V1_09.

En Windows, que usa Stefanny, el camino equivalente es PostgreSQL 18 con el instalador oficial para Windows y la descarga de línea de comandos de Flyway para Windows, que trae su propio JRE. `pruebas/correr_pruebas.sh` necesita una terminal bash, como Git Bash o WSL.

## Base en Neon

La base compartida vive en Neon, un servicio de PostgreSQL en la nube, sin pasar por la unidad de informática de la universidad. Es el proyecto ABET-ULIMA, con PostgreSQL 18 en us-east-1 (J-17). Al principio solo lleva datos inventados. Los datos reales de estudiantes entran después de la autorización escrita que gestiona la carrera, la revisión del Oficial de Datos Personales, la decisión de la universidad sobre el consentimiento, el contrato con el proveedor y la comunicación del envío a la Autoridad Nacional de Protección de Datos Personales, porque guardar datos personales fuera del Perú es un flujo transfronterizo según la Ley 29733. El documento `Entregables/Arquitectura_BD_explicada.docx`, en su capítulo 10, explica el porqué.

### Crear el proyecto

Jefferson crea el proyecto ABET-ULIMA con la integración Neon × Vercel, en us-east-1 y con PostgreSQL 18.6, y el 2026-11-02 decide usarlo para el piloto con datos inventados (J-17). Conviene sumar un segundo administrador, por ejemplo un docente de la carrera, para que la base no dependa de una sola cuenta. La región y la versión no cambian después de crear el proyecto. De la consola se copian el host de la conexión directa, que no lleva `-pooler`, el nombre de la base y el usuario dueño.

### Migrar con Flyway

El entorno `neon` de `flyway.toml` arma la URL con `sslmode=verify-full`, que cifra la conexión y comprueba el certificado, y con `DefaultJavaSSLFactory`, que lo valida con los certificados raíz de Java. Usa la conexión directa, porque Flyway toma bloqueos de asesoría que el repartidor de conexiones de Neon no garantiza en modo transacción. No lleva el override de `cleanDisabled`, así que `flyway clean` queda prohibido en Neon. Como `dev` sigue siendo el entorno por defecto, cada orden contra Neon lleva `-environment=neon`.

```sh
export JAVA_HOME="$(brew --prefix openjdk@21)/libexec/openjdk.jdk/Contents/Home"
export NEON_HOST=ep-xxxx.us-east-1.aws.neon.tech   # host de la conexión directa, sin -pooler
export NEON_DB=neondb NEON_DB_USER=neondb_owner
read -rs NEON_DB_PASSWORD && export NEON_DB_PASSWORD   # se escribe sin que quede en el historial
flyway info -environment=neon
flyway migrate -environment=neon
flyway validate -environment=neon
```

Al final de cada `migrate`, haya o no migraciones pendientes, Flyway corre `callbacks/afterMigrate__permisos_lectura.sql`. Ese callback repone los permisos de los roles de lectura y del respaldo y el SELECT de las dos vistas de `abet_app`, porque las repetibles borran y recrean las vistas, y con eso PostgreSQL borra sus permisos, y porque una migración nueva puede crear tablas nuevas. Si los roles no existen, como en la base local y en el CI, no hace nada. El callback no entra en `flyway_schema_history` ni cambia ningún checksum.

Las dos vistas se crean con `security_barrier`. Sin esa opción, quien consulta puede escribir una función que PostgreSQL evalúa antes del filtro de la vista, y con ella ver filas que la vista oculta, como las de cargas que no están PUBLICADAS. Como las repetibles cambian, la base local de cada persona necesita un `flyway migrate` para recrear las vistas con la opción, y hasta entonces `flyway validate` las marca como pendientes.

### Roles de solo lectura

`plataforma/neon/crear_roles_lectura.sql` se corre con el usuario dueño después del primer `migrate`, y se puede repetir sin romper nada. Crea tres roles.

- `abet_lectura`, un rol de grupo sin inicio de sesión, con uso del esquema `abet` y SELECT solo sobre las dos vistas.
- `powerbi_lectura`, el usuario de Power BI, miembro de `abet_lectura`, con un máximo de 5 conexiones.
- `abet_respaldo`, el usuario del respaldo diario, con SELECT sobre todas las tablas y secuencias de `abet` y de `acceso` (desde V1_09), que `pg_dump` necesita. Así el secreto que guarda GitHub sirve para leer y no para cambiar ni borrar la base.

El script quita además a PUBLIC el permiso de crear tablas y funciones temporales en la base, que es la vía para intentar saltar el filtro de una vista, y evita que las funciones de migraciones futuras queden ejecutables por cualquiera. Las sesiones de los dos usuarios empiezan en solo lectura, pero eso es un valor por defecto que el propio usuario puede apagar, así que solo es una defensa adicional. El control real son los permisos. El script termina con una comprobación que se detiene si algún rol tiene un atributo de administración o pertenece a otro rol, si `powerbi_lectura` puede leer una tabla, crear objetos temporales o entrar al esquema `acceso`, o si una vista no tiene `security_barrier`. También se detiene si `abet_respaldo` no puede leer alguna tabla o secuencia de `abet` o `acceso`, porque sin este permiso el respaldo falla.

Los roles se crean por SQL y no desde la consola de Neon, porque Neon da a los roles de la consola el rol `neon_superuser`, con atributos de administración que un usuario de lectura no necesita. Las contraseñas se leen de las variables de entorno `POWERBI_CLAVE` y `RESPALDO_DB_CLAVE`, así que no pasan por la línea de comandos ni por el historial. Neon pide recibirlas en texto plano para revisar que sean robustas, por eso el script no usa `\password`, que las manda ya cifradas.

```sh
export POWERBI_CLAVE="$(openssl rand -base64 24)"       # se guarda en el gestor de contraseñas
export RESPALDO_DB_CLAVE="$(openssl rand -base64 24)"   # se guarda en el gestor y en los secretos de GitHub
psql -q "host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=verify-full sslrootcert=system" \
     -v ON_ERROR_STOP=1 -f plataforma/neon/crear_roles_lectura.sql
unset POWERBI_CLAVE RESPALDO_DB_CLAVE
```

En Power BI Desktop, el conector PostgreSQL usa como servidor el host de la conexión directa, la base de `NEON_DB` y el usuario `powerbi_lectura`, y lee solo las dos vistas del esquema `abet`. Si Power BI responde que falta el endpoint ID, Neon documenta poner `endpoint=<id del endpoint>$<contraseña>` en el campo de contraseña. La conexión sigue cifrada, pero la autenticación baja de SCRAM a contraseña simple.

Cuando la entrega 2 agregue políticas de seguridad por fila, las vistas que lee Power BI no las aplicarán solas, porque consultan las tablas con los permisos de su dueño, y en Neon el dueño salta esas políticas. En ese momento las vistas pasan a `security_invoker` con SELECT sobre las tablas bajo las políticas, o a un dueño sin BYPASSRLS que no sea dueño de las tablas. El usuario del respaldo necesitará entonces leer todas las filas, porque `pg_dump` se detiene ante una tabla con políticas que filtran.

### Respaldo diario

El plan gratuito de Neon solo deja volver la base a las últimas 6 horas. `herramientas/respaldar_neon.sh` vuelca los esquemas `abet` y `acceso` con `pg_dump` en formato custom, comprueba con `pg_restore --list` que el archivo se lee y que trae el historial de Flyway, lo cifra con `gpg` en AES-256 con una derivación de clave lenta y fija, y escribe su huella SHA-256. La copia sin cifrar nunca sale de una carpeta temporal privada que se borra al terminar, y la frase de cifrado no pasa por la línea de comandos ni queda guardada en `gpg-agent`. El script exige que `pg_dump` y `pg_restore` sean de la versión mayor 18 (`PG_MAYOR`), la de Neon (J-17), la misma del servidor y del `pg_restore` con que se restaura, porque un `pg_restore` más viejo no lee el archivo de un `pg_dump` más nuevo.

El esquema `acceso` entra al respaldo desde V1_09, la migración del Back que agrega `abet.carga.subida_por` con una clave foránea hacia `acceso.usuario_autorizado`, porque desde entonces un volcado solo de `abet` no se restaura en una base vacía. El archivo trae los usuarios y sus secciones, mientras que de `credencial`, `sesion`, `intento_fallido` y `codigo_acceso` guarda solo la definición, sin ninguna fila. La comprobación del script se detiene antes de cifrar si alguna de estas cuatro tablas falta en el archivo o llega con filas, así que, si una cambia de nombre, sus filas no entran al respaldo sin aviso. Antes de V1_09 el volcado trae solo `abet`, porque `pg_dump` ignora un `--schema` que no encuentra mientras otro coincida. Como `pg_dump` bloquea cada tabla que vuelca, también las que vuelca sin filas, `abet_respaldo` necesita leer estas cuatro tablas. En ellas no hay contraseñas, tokens ni códigos en claro, solo sus hashes, y el secreto de GitHub sigue sin servir para cambiar ni borrar la base.

`../.github/workflows/respaldo_neon.yml` corre ese script a mano desde la pestaña Actions, con el cliente de PostgreSQL 18, y se conecta con el usuario `abet_respaldo`. Guarda el archivo cifrado como artefacto del repositorio durante 14 días. El horario diario de las 08:00 UTC, que son las 03:00 en Lima, se suma cuando una corrida a mano termine bien con los cinco secretos cargados (T027), y entonces la copia diaria deja además actividad en la base. El flujo no usa Flyway ni acciones de Redgate.

El flujo necesita cinco secretos del repositorio, `NEON_HOST`, `NEON_DB`, `NEON_RESPALDO_USER` (con el valor `abet_respaldo`), `NEON_RESPALDO_PASSWORD` y `RESPALDO_CLAVE`. La frase `RESPALDO_CLAVE` se genera al azar, por ejemplo con `openssl rand -base64 32`, y se guarda también fuera de GitHub, en un gestor de contraseñas, porque sin ella ningún respaldo se puede abrir. Mientras la base tenga datos reales, cada artefacto es una copia más de datos personales fuera del Perú, aunque vaya cifrada, y entra en la misma autorización que la base.

En el Back, Actions ya está encendido y el flujo usa solo acciones fijadas por SHA, así que no pide ningún cambio en Settings.

Desde la Mac, el mismo respaldo se corre con las variables de Neon exportadas.

```sh
read -rs RESPALDO_CLAVE && export RESPALDO_CLAVE
PATH="/opt/homebrew/opt/postgresql@18/bin:$PATH" ./herramientas/respaldar_neon.sh respaldo
```

### Restaurar un respaldo

Si el error cae dentro de las últimas 6 horas, lo más directo es restablecer la rama de Neon a un momento anterior desde su consola. Pasada esa ventana, se usa el respaldo diario. Se comprueba la huella y se descifra directo hacia `pg_restore`, sin dejar un archivo sin cifrar en el disco, dentro de una base vacía creada para eso, que puede estar en una rama aparte de Neon pero nunca es la base en uso. `--single-transaction` hace que un error no deje la restauración a medias.

```sh
shasum -a 256 -c abet_neondb_<fecha>.dump.gpg.sha256
psql "host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=verify-full sslrootcert=system" -c "CREATE DATABASE abet_restaurada"
gpg --decrypt abet_neondb_<fecha>.dump.gpg | pg_restore --no-owner --exit-on-error --single-transaction \
    -d "host=$NEON_HOST dbname=abet_restaurada user=$NEON_DB_USER sslmode=verify-full sslrootcert=system"
NEON_DB=abet_restaurada flyway validate -environment=neon
```

El respaldo no guarda roles ni permisos, así que en la base restaurada se corre después `crear_roles_lectura.sql`. Tampoco guarda la marca de entorno, así que la base restaurada recibe `marcar_entorno.sql` antes de que la API la use. Desde V1_09 se corre además `crear_rol_app.sql` del Back, que repone los permisos del rol de la aplicación. Si la configuración de Flyway no incluye V1_09, como la de `ABET_ULIMA`, `flyway validate` la marca como futura (Future) y pasa igual. La copia trae los usuarios autorizados y sus secciones, pero no sus credenciales, sesiones, intentos fallidos ni códigos de acceso, de modo que cada usuario necesita una contraseña nueva antes de volver a entrar a la aplicación. Las sesiones abiertas antes del respaldo tampoco sirven en la copia.

### Qué está probado

El 26/10/2026 todo esto se prueba en un clúster desechable de PostgreSQL 16.14 que imita a Neon. Ese clúster tiene un dueño sin superusuario con CREATEROLE, la base `neondb` y SSL con un certificado firmado por una autoridad de prueba. Sin esa autoridad entre los certificados de confianza de Java, Flyway rechaza la conexión, lo que confirma que el certificado se verifica. Con ella, `migrate` aplica las diez migraciones y corre el callback, `validate` pasa con 11 y `clean` queda bloqueado.

El script de roles corre dos veces sin errores, la primera con las contraseñas tomadas de las variables y la segunda avisando que faltan. `powerbi_lectura` lee las dos vistas y recibe «permission denied» en las tablas y al crear tablas o funciones temporales, aun después de apagar el modo de solo lectura. `abet_respaldo` lee las tablas y recibe «permission denied» al intentar borrar.

Para probar `security_barrier`, se devuelve por un momento el permiso temporal a `powerbi_lectura` y se agrega un estudiante sin mediciones publicadas. Con una función temporal que avisa cada código que ve, una vista de control sin la opción deja ver a ese estudiante, mientras que la vista de control con la opción y `v_tabla_maestra_pi` muestran solo sus 33 filas. Tras quitar los permisos de las vistas, un `migrate` sin pendientes los repone.

El respaldo hecho con `abet_respaldo` pesa unos 29 KB cifrado, usa AES-256 con S2K iterado y SHA-512, y no deja ningún archivo sin cifrar. Restaurado por tubería en una base vacía, da los mismos conteos que el origen (33 mediciones, 12 estudiantes, 17 PI, 11 filas de historial y 3 filas del R-17), con las vistas protegidas, y `flyway validate` pasa sobre la copia. Las pruebas de `pruebas/correr_pruebas.sh` siguen pasando.

El 28/10/2026 se prueba el esquema `acceso` en el respaldo, otra vez en un clúster desechable propio de PostgreSQL 16.14 con un dueño sin superusuario y la base `neondb`, sin SSL y sin tocar el clúster de `localhost:5432`. Sobre las migraciones de bd/, Flyway aplica una copia de la V1_09 del Back (rama `feat/001-mvp-carga-r17`, commit 55c6588), y después se cargan los datos sintéticos y dos usuarios inventados con credenciales, sesiones, intentos y códigos de prueba. Con el script anterior, el respaldo solo de `abet` no se restaura en una base vacía, porque la clave foránea de `abet.carga.subida_por` pide `acceso.usuario_autorizado`. Con el script nuevo pero sin los permisos de `acceso`, `pg_dump` responde «permission denied for schema acceso» y no deja ningún archivo.

Con el callback nuevo, el archivo trae los datos de `usuario_autorizado` y `docente_seccion` y solo la definición de las cuatro tablas sensibles, y ninguno de sus ocho hashes de prueba aparece en el archivo descifrado. En la copia restaurada por tubería en una base vacía, las 29 tablas de `abet` y las dos de `acceso` con datos coinciden con el origen en filas y huella MD5, las cuatro sin datos llegan vacías y el R-17 da 63,6 %, 63,6 % y 72,7 %. La copia conserva las cinco claves foráneas de `acceso` y la de `subida_por`, y `flyway validate` pasa con V1_09 entre las ubicaciones y sin ella. Los esquemas de origen y copia coinciden, salvo 34 líneas de restricciones CHECK con listas IN sobre varchar, que PostgreSQL reescribe al restaurar en una forma equivalente, y una segunda vuelta ya no cambia nada. Antes de V1_09, el script nuevo vuelca solo `abet`, igual que el anterior.

La copia llega sin permisos, y el script de roles anterior deja a `abet_respaldo` fuera de `acceso`. El script nuevo le devuelve la lectura de este esquema, con lo que la copia se puede respaldar, y su comprobación final se detiene si `powerbi_lectura` entra en `acceso` o si `abet_respaldo` no puede leer alguna tabla o secuencia. Además, `pg_dump` se detiene si a `abet_respaldo` le falta SELECT sobre `acceso.credencial`, cuyos datos excluye, o sobre las secuencias de `acceso`. En cuanto a los usuarios, `powerbi_lectura` recibe «permission denied for schema acceso», mientras que `abet_respaldo` lee las tablas de `acceso` y recibe «permission denied» al intentar borrar, cambiar o crear.

Falta probar contra Neon de verdad, en GitHub Actions y desde Power BI, en especial la actualización programada de Power BI Service sin puerta de enlace.

Estas pruebas son de PostgreSQL 16.14. Desde J-17, Neon corre la 18.6, y la corrida del respaldo con `pg_dump` 18 llega con T027.

## Cómo agregar una migración

1. Se elige el siguiente número libre de la entrega en curso con dos dígitos, por ejemplo `V2_01__crear_docentes.sql`. Flyway lee `V1_01` como versión 1.01 y ordena numéricamente. Flyway trata `V1_01` y `V1_1` como la misma versión y rechaza una versión repetida, así que los dos dígitos son una convención del equipo para que los nombres se ordenen igual en cualquier listado.
2. El nombre sigue el patrón `V<entrega>_<paso>__<verbo>_<objeto>.sql` y el archivo contiene DDL o datos, no ambos.
3. Cada objeto lleva el prefijo de su esquema, `abet.` o `acceso.`, y un comentario breve en español que dice qué hallazgos o historias cubre.
4. Las vistas van en repetibles `R__` con `DROP VIEW IF EXISTS ... CASCADE;` seguido de `CREATE VIEW`, porque `CREATE OR REPLACE VIEW` falla al quitar o renombrar columnas.
5. Si la migración nace de la referencia curricular, se genera con un script determinista y la prueba compara la salida regenerada con el archivo guardado.
6. Antes de abrir la solicitud de cambios se corre `./pruebas/correr_pruebas.sh` y se agregan las aserciones que prueban la regla nueva, incluido el caso que debe fallar.
7. Si la migración agrega una tabla o una columna que la aplicación lee o escribe, `plataforma/neon/crear_rol_app.sql` suma el permiso justo y `pruebas/probar_rol_app.sql` lo prueba, porque el rol no recibe permisos por defecto. Si cambia una R__, el `migrate` borra y recrea la vista y el rol pierde su SELECT, así que `crear_rol_app.sql` corre otra vez después, hasta que `afterMigrate__permisos_lectura.sql` reponga también los permisos de `abet_app`.

Una migración aplicada en una base compartida nunca se edita. El error se corrige con otra migración hacia adelante, y `flyway validate` detecta cualquier edición por su checksum.

## Reglas de trabajo entre dos personas

Cada migración nueva entra en su propia rama y en su propia solicitud de cambios, revisada por la otra persona. El número de versión se fija al fusionar. Si dos ramas toman el mismo número, la segunda en fusionarse renumera su archivo antes de hacerlo, y como `outOfOrder = false`, nadie aplica en una base compartida una versión menor que la última aplicada. La base local de cada persona se reconstruye con `flyway clean` y `flyway migrate` cuando su historial difiere del de la rama principal. Los exports de Blackboard, las planillas y las credenciales nunca entran al repositorio, y `.gitignore` excluye `*.csv`, `*.xlsx` y `flyway.user.toml`.

## Supuestos del modelo y lo que vigila el programa de carga

Algunas reglas dependen de decisiones abiertas o no caben en restricciones declarativas, y quedan escritas aquí para revisarlas antes de la primera carga real.

- El grano de la carga es un archivo por sección con todos los SO medidos, porque `uq_carga_publicada_por_seccion` admite una sola carga PUBLICADA por sección. H51 sigue abierto y 450002 tributa SO4 y SO5, así que antes de la primera carga real se confirma con un export real de una asignatura que mida dos SO. Si Blackboard entrega un archivo por SO, la carga recibe un alcance por SO y el índice cambia antes de publicar datos reales.
- La carga lleva su carrera, sus reglas son de esa carrera y sus columnas solo toman PI del plan de esa carrera. `uq_carga_publicada_por_seccion` y `uq_carga_archivo_util` no incluyen la carrera, así que una sección de un curso compartido cuyo export traiga PI de dos carreras no se puede publicar. Esto es un bloqueo explícito y no un descuido. Antes de cargar el primer curso compartido, la carrera decide cómo se reparten entre dos carreras las columnas de un mismo export, cuyos códigos de PI pueden coincidir (H02). Después, una migración nueva cambia el grano de ambos índices a la sección y la carrera o lleva las reglas a una tabla por carga y carrera.
- Las reglas de una carga publicada cambian solo por reemplazo, nunca con un UPDATE de `carga.conjunto_reglas_id`. Cuando la carrera aprueba un conjunto de reglas o se corrige el programa de carga, el mismo archivo se procesa en una carga nueva que queda EN_CURSO mientras la anterior sigue PUBLICADA. En una sola transacción la anterior pasa a REEMPLAZADA y la nueva a PUBLICADA, y la anterior conserva el conjunto con que se publicó (H57). `uq_carga_archivo_util` admite por eso una sola carga PUBLICADA por archivo y deja reutilizar el archivo de una carga REEMPLAZADA o RECHAZADA. La base no impide el UPDATE sin disparadores, así que lo evita el programa de carga y, en el alojamiento, los permisos por columna. Q14 detecta una carga REEMPLAZADA sin ninguna carga que la reemplace.
- El conjunto de reglas no está atado al periodo. Dos secciones del mismo curso y periodo pueden publicarse con conjuntos distintos, por ejemplo mientras dura el reemplazo que aplica un conjunto recién aprobado, y Q10 lo detecta. Una tabla `reglas_vigencia` por periodo y carrera, análoga a `catalogo_vigencia`, queda como decisión abierta, porque con una clave foránea desde la carga impediría el paso de un conjunto a otro dentro del mismo periodo. Se resuelve antes de la regla R-018 por curso de la fase 2.
- Un conjunto de reglas puede pasar a APROBADO con parámetros PENDIENTE, porque exigirlo pide comparar filas de dos tablas. Q11 detecta ese caso y la vista del R-17 lo sigue marcando como provisional mientras le falte NIVEL_ESPERADO, META_LOGRO o TRATO_SIN_EVIDENCIA.
- La rúbrica guarda descriptores para los niveles -1 y 1 a 5, mientras `medicion.nivel_original` solo acepta la escala 1 a 4 de Blackboard. La correspondencia entre los niveles -1 y 5 de la rúbrica y esa escala la decide la carrera. Mientras tanto, el programa de carga rechaza un -1 o un 5 con NIVEL_FUERA_DE_ESCALA, y esa fila completa queda fuera de la carga.
- El nombre de la asignatura sale depurado de `herramientas/generar_v1_03.py`, que junta los espacios repetidos y pasa a minúscula los conectores que no abren el nombre (H23). Así 450025 llega a Power BI como «Formulación y Evaluación de Proyectos Sostenibles» y 5674 como «Gestión de Proyectos». El JSON de referencia conserva el texto de la fuente.
- La versión de catálogo de cada periodo se registra en `catalogo_vigencia` antes del plan de medición, y el plan solo acepta esa versión. `vigente_desde_periodo_id` queda como dato informativo de la versión.
- La base exige que una carga publicada lea todas las filas de datos del archivo. Que cada columna tenga tantas mediciones como filas aceptadas no se puede declarar sin disparadores, así que lo asegura el programa de carga y lo revisa Q02 en las pruebas y en la CI. Un nivel fuera de escala rechaza la fila completa, y `rechazo_fila.carga_columna_id` solo indica qué celda causa el rechazo. Cada fila aceptada queda en `carga_fila` con su estudiante, de modo que una fila no mezcla dos estudiantes ni un estudiante ocupa dos filas de la misma carga, y Q12 y Q13 vigilan que las filas existan en el archivo y coincidan con las filas aceptadas.
- `nivel_original` es entero. El programa de carga rechaza con NIVEL_NO_NUMERICO un valor no entero, como 3,5, antes de insertarlo, porque la base lo redondearía al convertirlo.
- `estudiante.carrera_id` no guarda historia. Cuando llegue la fuente oficial de matrícula (H28), la carrera pasa a una tabla `estudiante_carrera` con su periodo de inicio, en lugar de actualizar la columna y reasignar mediciones pasadas. Q08 vigila que un estudiante no aparezca con el mismo PI en dos secciones del mismo curso y periodo.
- `archivo_origen.tipo_fuente` distingue el export de Blackboard del R-17 histórico. La migración de los R-17 de 2025-1 (H34) entra en una fase posterior y define entonces cómo registra columnas que no traen el encabezado de Blackboard.

## Qué falta (entrega 2 y siguientes)

La entrega 1 deja fuera, a propósito, lo que todavía depende de decisiones abiertas.

- Docentes identificados por su cuenta institucional, que también llenan la columna PROFESOR de la tabla maestra. V1_09 trae solo lo que pide el MVP, los usuarios autorizados por correo y `acceso.docente_seccion`, que ya admite co-docencia.
- Roles y ámbitos de acceso, con el principio de que nadie ve hacia arriba (Dirección y Secretaría Académica ven la carrera, el coordinador de acreditación su SO, el coordinador de área su área, el coordinador de curso su curso y el profesor su sección).
- Seudónimos para el código de estudiante, guardados fuera del modelo que lee Power BI.
- Equipos de Capstone unidos por código de estudiante.
- La regla R-018 y las competencias en los tableros.
- Lo específico del alojamiento que todavía no tiene destino (Microsoft Entra ID, pgaudit y políticas de seguridad por fila), que va en `db/plataforma/<destino>`. Neon ya tiene la suya, `plataforma/neon/`, con el rol de la aplicación, la guardia y las consultas de control.
- La aprobación de las reglas pendientes (corte rojo del semáforo, conversión de 1 a 4 a la escala de 0 a 1 y trato del estudiante sin evidencia) en un conjunto de reglas nuevo, sin editar R-2026-BORRADOR, que llega a las cargas publicadas por reemplazo.

## Por qué PostgreSQL

PostgreSQL 18 corre nativo en la Mac con Apple Silicon (Homebrew, `postgresql@18`), mientras que SQL Server no tiene una imagen de contenedor soportada para arm64 y en la Mac no hay Docker. Neon corre la misma versión mayor (J-17), así que el motor de desarrollo coincide con el de producción (paridad entre desarrollo y producción). Flyway funciona igual con PostgreSQL, SQL Server y Azure SQL; lo que cambia entre ellos es el dialecto de cada archivo.

Si algún día el alojamiento pasa a SQL Server o Azure SQL, el esquema se traduce a una ubicación propia (`migration/sqlserver`) antes del primer despliegue compartido y ambas secuencias se prueban con los mismos datos sintéticos. Estas son las diferencias que hay que reescribir.

- `GENERATED ALWAYS AS IDENTITY` pasa a `IDENTITY(1,1)`.
- Los CHECK con expresiones regulares (`~` y `!~`) no existen en T-SQL y se reescriben con `LEN` y `LIKE`, por ejemplo `LEN(codigo) = 8 AND codigo NOT LIKE '%[^0-9]%'`; la huella usa además una intercalación binaria para distinguir mayúsculas.
- Un UNIQUE sobre una columna que admite NULL acepta un solo NULL en SQL Server, así que `uq_seccion_curso_bb` y `uq_carga_reemplaza` pasan a índices únicos filtrados con `WHERE columna IS NOT NULL`.
- Los índices únicos parciales (`uq_carga_publicada_por_seccion` y `uq_carga_archivo_util`, ambos con `WHERE estado = 'PUBLICADA'`) pasan a índices filtrados con el mismo filtro.
- T-SQL no admite una expresión booleana en la lista del SELECT, así que la columna `provisional` de la vista del R-17 pasa a `CASE WHEN ... THEN 1 ELSE 0 END` con tipo `bit`.
- `timestamptz` y `now()` pasan a `datetimeoffset` y `SYSDATETIMEOFFSET()`.
- El texto con tildes pasa a `nvarchar` con literales `N'...'`, o a `varchar` con una intercalación UTF-8.
- La intercalación por defecto de SQL Server no distingue mayúsculas, de modo que `G1` y `g1` chocan; los CHECK de formato lo evitan, pero hay que tenerlo presente al comparar códigos.
- `COMMENT ON` pasa a `sp_addextendedproperty` con `MS_Description`.
- El operador `||` pasa a `+` o `CONCAT`, `btrim` a `TRIM`, `encode(sha256(...))` a `HASHBYTES`, y los casts con `::` a `CAST`.
- `DROP VIEW IF EXISTS` más `CREATE VIEW` pasa a `CREATE OR ALTER VIEW`, que debe ir sola en su lote, separada con `GO`.
- El bloque `DO` de `V1_03` y los de las pruebas pasan a lotes con `IF ... THROW`.
- `string_agg(x, ',' ORDER BY y)` pasa a `STRING_AGG(x, ',') WITHIN GROUP (ORDER BY y)` y `ALTER TABLE ... ADD COLUMN` pierde la palabra `COLUMN`.
- Un CHECK que compare dos expresiones booleanas no es válido en T-SQL; por eso las reglas de este esquema se escriben con `AND` y `OR`, que se trasladan sin cambios, igual que las claves foráneas compuestas, que no usan `ON DELETE CASCADE`.

## Privacidad

Ningún archivo contiene códigos de estudiante reales, nombres de docentes ni ids de columnas de Blackboard reales. Los datos de prueba son inventados, con los códigos 99000001 a 99000011 en la sección 410, 99000012 a 99000022 en la 411, 99000023 a 99000055 en las tres secciones de `docente.varias@example.invalid` y correos que terminan en `@example.invalid`. Los únicos códigos que no empiezan con 99 son 10000004 y 98999999, los valores de prueba de la guardia en `pruebas/probar_guardia.sql`, que la base rechaza sin guardarlos. La base guarda del estudiante solo su código, `rechazo_fila` registra el motivo sin el valor leído y `archivo_origen` guarda el nombre del archivo sin la ruta local de quien lo carga. Los correos de los usuarios viven solo en `acceso.usuario_autorizado`, el esquema `acceso` guarda el hash de cada contraseña, token, código y correo de un intento fallido, nunca su texto, y en Neon `ck_estudiante_codigo_inventado` impide además guardar un código que no empiece con 99. Cuando una restricción rechaza una fila, PostgreSQL repite esa fila en el DETAIL del error, código del estudiante incluido, así que la interfaz de programación de aplicaciones (application programming interface, API) registra y responde de un error de integridad solo el SQLSTATE y el nombre de la restricción, nunca su DETAIL (FR-018 y SC-006).
