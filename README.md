# Base de datos ABET_SIS_MED

Esta carpeta es la semilla del repositorio de la base de datos del sistema de medición ABET de la Carrera de Ingeniería Ambiental. La base se construye como código, con migraciones versionadas de Flyway sobre PostgreSQL 16, en pasos pequeños que dos personas pueden revisar en una sesión. Cada cambio del esquema entra como un archivo nuevo y nunca como una edición manual de la base.

## Contenido de la carpeta

| Ruta | Para qué sirve |
| --- | --- |
| `flyway.toml` | Configuración de Flyway, con el esquema `abet`, el entorno local `dev`, el entorno `neon` y las credenciales tomadas de variables de entorno |
| `db/migration/` | Migraciones versionadas `V1_01` a `V1_08` y repetibles `R__` con las vistas |
| `db/callbacks/afterMigrate__permisos_lectura.sql` | Callback de Flyway que, al final de cada migrate, repone los permisos de los roles de lectura |
| `db/plataforma/neon/crear_roles_lectura.sql` | Script que se corre en Neon para crear los roles de solo lectura de Power BI y del respaldo |
| `referencia/ambiental_2026.json` | Datos curriculares de Ambiental (SO, PI, rúbrica, competencias y asignaturas), sin datos personales |
| `herramientas/generar_v1_03.py` | Generador determinista de `V1_03` a partir de la referencia, con la huella SHA-256 del JSON |
| `pruebas/datos_sinteticos.sql` | Datos inventados con la forma de un export real de Blackboard |
| `pruebas/pruebas.sql` | Aserciones que lanzan ERROR si algo no se cumple |
| `pruebas/correr_pruebas.sh` | Corre todas las pruebas sobre bases desechables, sin Flyway |
| `herramientas/respaldar_neon.sh` | Respaldo de la base en Neon con `pg_dump`, comprobado con `pg_restore --list` y cifrado con `gpg` |
| `.github/workflows/bd.yml` | CI propuesto con PostgreSQL 16 y Flyway Community |
| `.github/workflows/respaldo_neon.yml` | Respaldo diario de Neon a las 03:00 de Lima, guardado cifrado como artefacto durante 14 días |

## Qué crea la entrega 1

Todo vive en el esquema `abet`, que Flyway crea con `schemas = ["abet"]` en `[environments.dev]` y `createSchemas = true` en `[flyway]`. En el formato TOML, `schemas` es un ajuste del entorno y no se acepta en `[flyway]`. Las migraciones no ejecutan `CREATE SCHEMA` y califican cada objeto con `abet.`. Cada archivo contiene DDL o datos, nunca ambos, y las reglas viven en restricciones declarativas (claves primarias, UNIQUE, claves foráneas compuestas, CHECK e índices únicos parciales), sin disparadores ni funciones.

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

## Cómo correr las pruebas hoy, sin Flyway

El script crea dos bases desechables, crea en ellas el esquema `abet` (lo mismo que hace Flyway con `createSchemas`), aplica las versionadas en orden de versión con `psql -1 -v ON_ERROR_STOP=1`, cada una en su transacción, y luego las repetibles. Después compara el `pg_dump --schema-only` de ambas bases, carga los datos sintéticos en la primera, corre `pruebas/pruebas.sql` y borra las dos bases aunque algo falle. Antes de todo eso regenera `V1_03` desde la referencia y la compara con la guardada.

La conexión se toma de las variables estándar de libpq, así que el mismo script corre en la Mac y en CI.

```sh
export LC_ALL=en_US.UTF-8
PGHOST=localhost PGPORT=5432 PGUSER="$USER" \
PSQL=/opt/homebrew/opt/postgresql@16/bin/psql \
PG_DUMP=/opt/homebrew/opt/postgresql@16/bin/pg_dump \
./pruebas/correr_pruebas.sh
```

`PREFIJO_BD` cambia el prefijo de las bases desechables y `PYTHON` elige el intérprete del generador. La contraseña, si el servidor la pide, va en `PGPASSWORD` o en `~/.pgpass`, nunca en un archivo del repositorio.

Las pruebas cubren los conteos del catálogo y los números del R-17 de la sección 410 de 450002 en 2026-2 con 11 estudiantes inventados (63,6 % en 5.1, 63,6 % en 5.2 y 72,7 % en 5.3). Repiten ese R-17 con un NIVEL_ESPERADO PENDIENTE, que debe dar porcentajes NULL, y con TRATO_SIN_EVIDENCIA DEFINIDO en un conjunto en BORRADOR, que debe seguir provisional. Revisan además las columnas de la tabla maestra, 38 casos que la base debe rechazar con la restricción exacta que los rechaza, tres casos que debe aceptar y catorce consultas de control que deben devolver 0 filas, entre ellas la conciliación de mediciones con filas aceptadas, las filas del archivo que no existen y la ausencia de columnas con nombres de personas. Los casos aceptados son la sección 301 en dos asignaturas, el reemplazo de una carga publicada con otro archivo y el reemplazo con el mismo archivo y un conjunto de reglas aprobado. Cada consulta de control que vigila un caso que la base no puede impedir (Q06 a Q14) se prueba además sobre ese caso, en una transacción que se deshace.

## Cómo instalar Flyway en la Mac

Flyway 13 requiere Java 21 o posterior. La fórmula `flyway` de Homebrew depende de `openjdk`, que hoy instala openjdk 27. Redgate fija Java 21 como mínimo y el equipo usa la 21 LTS para no depender de la 27. Hay dos caminos recomendados.

El primero instala `openjdk@21` junto a la fórmula y fija `JAVA_HOME` en esa versión antes de llamar a Flyway.

```sh
brew install openjdk@21 flyway
export JAVA_HOME="$(brew --prefix openjdk@21)/libexec/openjdk.jdk/Contents/Home"
flyway --version
```

El lanzador que instala Homebrew respeta `JAVA_HOME`, así que basta exportarlo en la terminal donde se usa Flyway, sin cambiar el Java del sistema ni crear enlaces con `sudo`. La fórmula instala Flyway OSS Edition, la edición de código abierto con licencia Apache 2.0, que trae los comandos `info`, `migrate` y `validate` que usa el proyecto. El CI propuesto usa la edición Community de Redgate, también gratuita.

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

En CI el orden es `info`, `migrate` y `validate`, con la versión de Flyway fija en el flujo. `flyway clean` está deshabilitado en `[flyway]`, pero `dev` es el entorno por defecto y el único definido, y lo permite para reconstruir la base local desde cero. En la práctica, toda ejecución sin `-environment`, incluido el CI, corre con `clean` permitido, lo que se acepta porque ambas bases son desechables. Un entorno compartido entra con su propio bloque `[environments.<nombre>]`, sin ese override, y se llama con `-environment=<nombre>`, como `neon`. El repositorio está en GitHub con GitHub Actions apagado, porque la acción `red-gate/setup-flyway` de `.github/workflows/bd.yml` pide aceptar la licencia de uso de Redgate, que el equipo revisa antes de activarla.

## Estado de la base local

La base `abet_sis_med_dev` de la Mac de Jefferson está en la versión 1.08. El 22/10/2026, Flyway OSS 13.10.3 con openjdk 21.0.12 aplica las ocho versionadas y las dos repetibles en 0,25 segundos, `flyway validate` pasa con 11 migraciones y un segundo `flyway migrate` responde que el esquema está al día. El `pg_dump --schema-only` de esa base, sin la tabla `flyway_schema_history`, coincide línea por línea con el de una base armada con `psql` como en las pruebas, y los datos de referencia coinciden tabla por tabla. La base no tiene estudiantes ni mediciones, porque los datos sintéticos solo se cargan en las bases desechables de las pruebas.

En Windows, que usa Stefanny, el camino equivalente es PostgreSQL 16 con el instalador oficial para Windows y la descarga de línea de comandos de Flyway para Windows, que trae su propio JRE. `pruebas/correr_pruebas.sh` necesita una terminal bash, como Git Bash o WSL.

## Base en Neon

La base compartida se propone en Neon, un servicio de PostgreSQL 16 en la nube, sin pasar por la unidad de informática de la universidad. Al principio solo lleva datos inventados. Los datos reales de estudiantes entran después de la autorización escrita que gestiona la carrera, la revisión del Oficial de Datos Personales, la decisión de la universidad sobre el consentimiento, el contrato con el proveedor y la comunicación del envío a la Autoridad Nacional de Protección de Datos Personales, porque guardar datos personales fuera del Perú es un flujo transfronterizo según la Ley 29733. El documento `Entregables/Arquitectura_BD_explicada.docx`, en su capítulo 10, explica el porqué.

### Crear el proyecto

El proyecto se crea a mano en la consola de Neon, dentro de una organización con un segundo administrador, por ejemplo un docente de la carrera, para que la base no dependa de una sola cuenta. La región es AWS São Paulo (`aws-sa-east-1`), que no se puede cambiar después, y la versión es PostgreSQL 16. De la consola se copian el host de la conexión directa, que no lleva `-pooler`, el nombre de la base y el usuario dueño.

### Migrar con Flyway

El entorno `neon` de `flyway.toml` arma la URL con `sslmode=verify-full`, que cifra la conexión y comprueba el certificado, y con `DefaultJavaSSLFactory`, que lo valida con los certificados raíz de Java. Usa la conexión directa, porque Flyway toma bloqueos de asesoría que el repartidor de conexiones de Neon no garantiza en modo transacción. No lleva el override de `cleanDisabled`, así que `flyway clean` queda prohibido en Neon. Como `dev` sigue siendo el entorno por defecto, cada orden contra Neon lleva `-environment=neon`.

```sh
export JAVA_HOME="$(brew --prefix openjdk@21)/libexec/openjdk.jdk/Contents/Home"
export NEON_HOST=ep-xxxx.sa-east-1.aws.neon.tech   # host de la conexión directa, sin -pooler
export NEON_DB=neondb NEON_DB_USER=neondb_owner
read -rs NEON_DB_PASSWORD && export NEON_DB_PASSWORD   # se escribe sin que quede en el historial
flyway info -environment=neon
flyway migrate -environment=neon
flyway validate -environment=neon
```

Al final de cada `migrate`, haya o no migraciones pendientes, Flyway corre `db/callbacks/afterMigrate__permisos_lectura.sql`. Ese callback repone los permisos de los roles de lectura, porque las repetibles borran y recrean las vistas, y con eso PostgreSQL borra sus permisos, y porque una migración nueva puede crear tablas nuevas. Si los roles no existen, como en la base local y en el CI, no hace nada. El callback no entra en `flyway_schema_history` ni cambia ningún checksum.

Las dos vistas se crean con `security_barrier`. Sin esa opción, quien consulta puede escribir una función que PostgreSQL evalúa antes del filtro de la vista, y con ella ver filas que la vista oculta, como las de cargas que no están PUBLICADAS. Como las repetibles cambian, la base local de cada persona necesita un `flyway migrate` para recrear las vistas con la opción, y hasta entonces `flyway validate` las marca como pendientes.

### Roles de solo lectura

`db/plataforma/neon/crear_roles_lectura.sql` se corre con el usuario dueño después del primer `migrate`, y se puede repetir sin romper nada. Crea tres roles.

- `abet_lectura`, un rol de grupo sin inicio de sesión, con uso del esquema `abet` y SELECT solo sobre las dos vistas.
- `powerbi_lectura`, el usuario de Power BI, miembro de `abet_lectura`, con un máximo de 5 conexiones.
- `abet_respaldo`, el usuario del respaldo diario, con SELECT sobre todas las tablas y secuencias de `abet` y de `acceso` (desde V1_09), que `pg_dump` necesita. Así el secreto que guarda GitHub sirve para leer y no para cambiar ni borrar la base.

El script quita además a PUBLIC el permiso de crear tablas y funciones temporales en la base, que es la vía para intentar saltar el filtro de una vista, y evita que las funciones de migraciones futuras queden ejecutables por cualquiera. Las sesiones de los dos usuarios empiezan en solo lectura, pero eso es un valor por defecto que el propio usuario puede apagar, así que solo es una defensa adicional. El control real son los permisos. El script termina con una comprobación que se detiene si algún rol tiene un atributo de administración o pertenece a otro rol, si `powerbi_lectura` puede leer una tabla, crear objetos temporales o entrar al esquema `acceso`, o si una vista no tiene `security_barrier`. También se detiene si `abet_respaldo` no puede leer alguna tabla o secuencia de `abet` o `acceso`, porque sin este permiso el respaldo falla.

Los roles se crean por SQL y no desde la consola de Neon, porque Neon da a los roles de la consola el rol `neon_superuser`, con atributos de administración que un usuario de lectura no necesita. Las contraseñas se leen de las variables de entorno `POWERBI_CLAVE` y `RESPALDO_DB_CLAVE`, así que no pasan por la línea de comandos ni por el historial. Neon pide recibirlas en texto plano para revisar que sean robustas, por eso el script no usa `\password`, que las manda ya cifradas.

```sh
export POWERBI_CLAVE="$(openssl rand -base64 24)"       # se guarda en el gestor de contraseñas
export RESPALDO_DB_CLAVE="$(openssl rand -base64 24)"   # se guarda en el gestor y en los secretos de GitHub
psql -q "host=$NEON_HOST dbname=$NEON_DB user=$NEON_DB_USER sslmode=verify-full sslrootcert=system" \
     -v ON_ERROR_STOP=1 -f db/plataforma/neon/crear_roles_lectura.sql
unset POWERBI_CLAVE RESPALDO_DB_CLAVE
```

En Power BI Desktop, el conector PostgreSQL usa como servidor el host de la conexión directa, la base de `NEON_DB` y el usuario `powerbi_lectura`, y lee solo las dos vistas del esquema `abet`. Si Power BI responde que falta el endpoint ID, Neon documenta poner `endpoint=<id del endpoint>$<contraseña>` en el campo de contraseña. La conexión sigue cifrada, pero la autenticación baja de SCRAM a contraseña simple.

Cuando la entrega 2 agregue políticas de seguridad por fila, las vistas que lee Power BI no las aplicarán solas, porque consultan las tablas con los permisos de su dueño, y en Neon el dueño salta esas políticas. En ese momento las vistas pasan a `security_invoker` con SELECT sobre las tablas bajo las políticas, o a un dueño sin BYPASSRLS que no sea dueño de las tablas. El usuario del respaldo necesitará entonces leer todas las filas, porque `pg_dump` se detiene ante una tabla con políticas que filtran.

### Respaldo diario

El plan gratuito de Neon solo deja volver la base a las últimas 6 horas. `herramientas/respaldar_neon.sh` vuelca los esquemas `abet` y `acceso` con `pg_dump` en formato custom, comprueba con `pg_restore --list` que el archivo se lee y que trae el historial de Flyway, lo cifra con `gpg` en AES-256 con una derivación de clave lenta y fija, y escribe su huella SHA-256. La copia sin cifrar nunca sale de una carpeta temporal privada que se borra al terminar, y la frase de cifrado no pasa por la línea de comandos ni queda guardada en `gpg-agent`. El script exige que `pg_dump` y `pg_restore` sean de la versión mayor 16 (`PG_MAYOR`), la misma del servidor y del `pg_restore` con que se restaura, porque un `pg_restore` más viejo no lee el archivo de un `pg_dump` más nuevo.

El esquema `acceso` entra al respaldo desde V1_09, la migración del Back que agrega `abet.carga.subida_por` con una clave foránea hacia `acceso.usuario_autorizado`, porque desde entonces un volcado solo de `abet` no se restaura en una base vacía. El archivo trae los usuarios y sus secciones, mientras que de `credencial`, `sesion`, `intento_fallido` y `codigo_acceso` guarda solo la definición, sin ninguna fila. La comprobación del script se detiene antes de cifrar si alguna de estas cuatro tablas falta en el archivo o llega con filas, así que, si una cambia de nombre, sus filas no entran al respaldo sin aviso. Antes de V1_09 el volcado trae solo `abet`, porque `pg_dump` ignora un `--schema` que no encuentra mientras otro coincida. Como `pg_dump` bloquea cada tabla que vuelca, también las que vuelca sin filas, `abet_respaldo` necesita leer estas cuatro tablas. En ellas no hay contraseñas, tokens ni códigos en claro, solo sus hashes, y el secreto de GitHub sigue sin servir para cambiar ni borrar la base.

`.github/workflows/respaldo_neon.yml` corre ese script cada día a las 08:00 UTC, que son las 03:00 en Lima, y también a mano desde la pestaña Actions. Se conecta con el usuario `abet_respaldo` y guarda el archivo cifrado como artefacto del repositorio durante 14 días. La copia diaria deja además actividad en la base. El flujo no usa Flyway ni acciones de Redgate.

El flujo necesita cinco secretos del repositorio, `NEON_HOST`, `NEON_DB`, `NEON_RESPALDO_USER` (con el valor `abet_respaldo`), `NEON_RESPALDO_PASSWORD` y `RESPALDO_CLAVE`. La frase `RESPALDO_CLAVE` se genera al azar, por ejemplo con `openssl rand -base64 32`, y se guarda también fuera de GitHub, en un gestor de contraseñas, porque sin ella ningún respaldo se puede abrir. Mientras la base tenga datos reales, cada artefacto es una copia más de datos personales fuera del Perú, aunque vaya cifrada, y entra en la misma autorización que la base.

Para correr solo este flujo, el orden importa, porque `bd.yml` se dispara con cada push a `main` y acepta la licencia de Redgate. Primero, con Actions todavía apagado, se sube todo lo pendiente. Después se enciende Actions en Settings > Actions con la opción «Allow select actions», con solo `actions/checkout` y `actions/upload-artifact` en la lista, y enseguida se apaga el flujo `bd` con `gh workflow disable bd.yml`. Con esa lista, la acción de Redgate queda bloqueada aunque `bd.yml` llegue a dispararse.

Desde la Mac, el mismo respaldo se corre con las variables de Neon exportadas.

```sh
read -rs RESPALDO_CLAVE && export RESPALDO_CLAVE
PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH" ./herramientas/respaldar_neon.sh respaldo
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

El respaldo no guarda roles ni permisos, así que en la base restaurada se corre después `crear_roles_lectura.sql`. Desde V1_09 se corre además `crear_rol_app.sql` del Back, que repone los permisos del rol de la aplicación. Si la configuración de Flyway no incluye V1_09, como la de bd/, `flyway validate` la marca como futura (Future) y pasa igual. La copia trae los usuarios autorizados y sus secciones, pero no sus credenciales, sesiones, intentos fallidos ni códigos de acceso, de modo que cada usuario necesita una contraseña nueva antes de volver a entrar a la aplicación. Las sesiones abiertas antes del respaldo tampoco sirven en la copia.

### Qué está probado

El 26/10/2026 todo esto se prueba en un clúster desechable de PostgreSQL 16.14 que imita a Neon. Ese clúster tiene un dueño sin superusuario con CREATEROLE, la base `neondb` y SSL con un certificado firmado por una autoridad de prueba. Sin esa autoridad entre los certificados de confianza de Java, Flyway rechaza la conexión, lo que confirma que el certificado se verifica. Con ella, `migrate` aplica las diez migraciones y corre el callback, `validate` pasa con 11 y `clean` queda bloqueado.

El script de roles corre dos veces sin errores, la primera con las contraseñas tomadas de las variables y la segunda avisando que faltan. `powerbi_lectura` lee las dos vistas y recibe «permission denied» en las tablas y al crear tablas o funciones temporales, aun después de apagar el modo de solo lectura. `abet_respaldo` lee las tablas y recibe «permission denied» al intentar borrar.

Para probar `security_barrier`, se devuelve por un momento el permiso temporal a `powerbi_lectura` y se agrega un estudiante sin mediciones publicadas. Con una función temporal que avisa cada código que ve, una vista de control sin la opción deja ver a ese estudiante, mientras que la vista de control con la opción y `v_tabla_maestra_pi` muestran solo sus 33 filas. Tras quitar los permisos de las vistas, un `migrate` sin pendientes los repone.

El respaldo hecho con `abet_respaldo` pesa unos 29 KB cifrado, usa AES-256 con S2K iterado y SHA-512, y no deja ningún archivo sin cifrar. Restaurado por tubería en una base vacía, da los mismos conteos que el origen (33 mediciones, 12 estudiantes, 17 PI, 11 filas de historial y 3 filas del R-17), con las vistas protegidas, y `flyway validate` pasa sobre la copia. Las pruebas de `pruebas/correr_pruebas.sh` siguen pasando.

El 28/10/2026 se prueba el esquema `acceso` en el respaldo, otra vez en un clúster desechable propio de PostgreSQL 16.14 con un dueño sin superusuario y la base `neondb`, sin SSL y sin tocar el clúster de `localhost:5432`. Sobre las migraciones de bd/, Flyway aplica una copia de la V1_09 del Back (rama `feat/001-mvp-carga-r17`, commit 55c6588), y después se cargan los datos sintéticos y dos usuarios inventados con credenciales, sesiones, intentos y códigos de prueba. Con el script anterior, el respaldo solo de `abet` no se restaura en una base vacía, porque la clave foránea de `abet.carga.subida_por` pide `acceso.usuario_autorizado`. Con el script nuevo pero sin los permisos de `acceso`, `pg_dump` responde «permission denied for schema acceso» y no deja ningún archivo.

Con el callback nuevo, el archivo trae los datos de `usuario_autorizado` y `docente_seccion` y solo la definición de las cuatro tablas sensibles, y ninguno de sus ocho hashes de prueba aparece en el archivo descifrado. En la copia restaurada por tubería en una base vacía, las 29 tablas de `abet` y las dos de `acceso` con datos coinciden con el origen en filas y huella MD5, las cuatro sin datos llegan vacías y el R-17 da 63,6 %, 63,6 % y 72,7 %. La copia conserva las cinco claves foráneas de `acceso` y la de `subida_por`, y `flyway validate` pasa con V1_09 entre las ubicaciones y sin ella. Los esquemas de origen y copia coinciden, salvo 34 líneas de restricciones CHECK con listas IN sobre varchar, que PostgreSQL reescribe al restaurar en una forma equivalente, y una segunda vuelta ya no cambia nada. Antes de V1_09, el script nuevo vuelca solo `abet`, igual que el anterior.

La copia llega sin permisos, y el script de roles anterior deja a `abet_respaldo` fuera de `acceso`. El script nuevo le devuelve la lectura de este esquema, con lo que la copia se puede respaldar, y su comprobación final se detiene si `powerbi_lectura` entra en `acceso` o si `abet_respaldo` no puede leer alguna tabla o secuencia. Además, `pg_dump` se detiene si a `abet_respaldo` le falta SELECT sobre `acceso.credencial`, cuyos datos excluye, o sobre las secuencias de `acceso`. En cuanto a los usuarios, `powerbi_lectura` recibe «permission denied for schema acceso», mientras que `abet_respaldo` lee las tablas de `acceso` y recibe «permission denied» al intentar borrar, cambiar o crear.

Falta probar contra Neon de verdad, en GitHub Actions y desde Power BI, en especial la actualización programada de Power BI Service sin puerta de enlace.

## Cómo agregar una migración

1. Se elige el siguiente número libre de la entrega en curso con dos dígitos, por ejemplo `V2_01__crear_docentes.sql`. Flyway lee `V1_01` como versión 1.01 y ordena numéricamente. Flyway trata `V1_01` y `V1_1` como la misma versión y rechaza una versión repetida, así que los dos dígitos son una convención del equipo para que los nombres se ordenen igual en cualquier listado.
2. El nombre sigue el patrón `V<entrega>_<paso>__<verbo>_<objeto>.sql` y el archivo contiene DDL o datos, no ambos.
3. Cada objeto lleva el prefijo `abet.` y un comentario breve en español que dice qué hallazgos cubre.
4. Las vistas van en repetibles `R__` con `DROP VIEW IF EXISTS ... CASCADE;` seguido de `CREATE VIEW`, porque `CREATE OR REPLACE VIEW` falla al quitar o renombrar columnas.
5. Si la migración nace de la referencia curricular, se genera con un script determinista y la prueba compara la salida regenerada con el archivo guardado.
6. Antes de abrir la solicitud de cambios se corre `./pruebas/correr_pruebas.sh` y se agregan las aserciones que prueban la regla nueva, incluido el caso que debe fallar.

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
- La base exige que una carga publicada lea todas las filas de datos del archivo. Que cada columna tenga tantas mediciones como filas aceptadas no se puede declarar sin disparadores, así que lo asegura el programa de carga y lo revisa Q02 en las pruebas y en CI. Un nivel fuera de escala rechaza la fila completa, y `rechazo_fila.carga_columna_id` solo indica qué celda causa el rechazo. Cada fila aceptada queda en `carga_fila` con su estudiante, de modo que una fila no mezcla dos estudiantes ni un estudiante ocupa dos filas de la misma carga, y Q12 y Q13 vigilan que las filas existan en el archivo y coincidan con las filas aceptadas.
- `nivel_original` es entero. El programa de carga rechaza con NIVEL_NO_NUMERICO un valor no entero, como 3,5, antes de insertarlo, porque la base lo redondearía al convertirlo.
- `estudiante.carrera_id` no guarda historia. Cuando llegue la fuente oficial de matrícula (H28), la carrera pasa a una tabla `estudiante_carrera` con su periodo de inicio, en lugar de actualizar la columna y reasignar mediciones pasadas. Q08 vigila que un estudiante no aparezca con el mismo PI en dos secciones del mismo curso y periodo.
- `archivo_origen.tipo_fuente` distingue el export de Blackboard del R-17 histórico. La migración de los R-17 de 2025-1 (H34) entra en una fase posterior y define entonces cómo registra columnas que no traen el encabezado de Blackboard.

## Qué falta (entrega 2 y siguientes)

La entrega 1 deja fuera, a propósito, lo que todavía depende de decisiones abiertas.

- Personas y docentes identificados por su cuenta institucional, con co-docencia por sección, que también llenan la columna PROFESOR de la tabla maestra.
- Roles y ámbitos de acceso, con el principio de que nadie ve hacia arriba (Dirección y Secretaría Académica ven la carrera, el coordinador de acreditación su SO, el coordinador de área su área, el coordinador de curso su curso y el profesor su sección).
- Seudónimos para el código de estudiante, guardados fuera del modelo que lee Power BI.
- Equipos de Capstone unidos por código de estudiante.
- La regla R-018 y las competencias en los tableros.
- Lo específico del alojamiento que falta, como los roles de escritura del programa de carga, el registro de accesos y las políticas de seguridad por fila, en `db/plataforma/neon/` junto al script de roles de lectura.
- La aprobación de las reglas pendientes (corte rojo del semáforo, conversión de 1 a 4 a la escala de 0 a 1 y trato del estudiante sin evidencia) en un conjunto de reglas nuevo, sin editar R-2026-BORRADOR, que llega a las cargas publicadas por reemplazo.

## Por qué PostgreSQL

PostgreSQL 16 corre nativo en la Mac con Apple Silicon y ya está instalado, mientras que SQL Server no tiene una imagen de contenedor soportada para arm64 y en la Mac no hay Docker. Neon, el alojamiento propuesto, ofrece la versión 16, así que el motor de desarrollo coincide con el de la base compartida (paridad entre desarrollo y producción). Flyway funciona igual con PostgreSQL, SQL Server y Azure SQL; lo que cambia entre ellos es el dialecto de cada archivo.

Si algún día el alojamiento pasa a SQL Server o Azure SQL, el esquema se traduce a una ubicación propia (`db/migration/sqlserver`) antes del primer despliegue compartido y ambas secuencias se prueban con los mismos datos sintéticos. Estas son las diferencias que hay que reescribir.

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

Ningún archivo contiene códigos de estudiante reales, nombres de docentes ni ids de columnas de Blackboard reales. Los datos de prueba son inventados (códigos 99000001 a 99000011). La base guarda del estudiante solo su código, `rechazo_fila` registra el motivo sin el valor leído y `archivo_origen` guarda el nombre del archivo sin la ruta local de quien lo carga.
