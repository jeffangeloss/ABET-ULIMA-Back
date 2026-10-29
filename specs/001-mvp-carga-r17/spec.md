# Feature Specification: Del export de Blackboard al R-17 desde la base

**Feature Branch**: `docs/plan-mvp` (PR a `develop`)
**Created**: 2026-10-28
**Status**: Borrador, pendiente de aprobación de Jefferson
**Input**: «Debemos desarrollar un sistema completo para poder subir el export de blackboard y este mismo que permita generar el excel (R17) para el profesor como evidencia de que se subió correctamente el export con sus datos. Y así mismo de que se pudo subir a la base de datos. La base de datos ya es manejada por los entes superiores, es decir los coordinadores de la carrera. En este caso ambiental que probaremos un primer lanzamiento.» (Jefferson, 2026-10-28). Y después «este será algo rápido, es un MVP, quiero que el sistema sea capaz de tener una base de datos en la nube, que se pueda subir el export, que se genere el r17 y que esos datos se carguen en la base de datos».

## Épica

> **EP-01. Del export de Blackboard al R-17 desde la base.** Hoy el profesor sube su export al Colab, que vacía celdas inválidas sin dejar rastro, adivina la sección por el nombre de hoja y no guarda nada. Con eso no hay evidencia de qué archivo da origen a un R-17 ni una base que lo respalde. El producto mínimo viable (minimum viable product, MVP) deja la base de Ambiental en Neon (PostgreSQL 16, región aws-sa-east-1), recibe el export en una aplicación con acceso por usuario, carga sus datos en una sola transacción y genera el R-17 desde la base con una hoja «Constancia» que ata el informe al archivo y a la carga.

Convenciones de esta spec. Todos los datos son inventados. La sección de prueba es la 410 de la asignatura 450002 «Principios de Ingeniería Sostenible» en el periodo 2026-2, con los indicadores de desempeño (performance indicators, PI) 5.1, 5.2 y 5.3 del resultado del estudiante (student outcome, SO) 5, y la sección 411 de la misma asignatura. Los códigos de estudiante van de 99000001 a 99000011 en la 410 y de 99000012 a 99000022 en la 411, para que la consulta de control Q08 no los vea en dos secciones. El profesor de varias secciones, `docente.varias@example.invalid`, dicta la 412 de 450002 y la 410 y la 412 de 450010 «Gestión Sostenible de Residuos», cuyo plan mide los PI 2.1, 2.2 y 5.1. Los datos de este profesor viven en `db/datos/varias_secciones_2026_2_inventado.sql` (script de datos), que corre solo en las bases desechables de las pruebas y nunca en Neon, así que el piloto conserva los valores provisionales de D-09 y D-13. Los exports de sus tres secciones traen los códigos 99000023 a 99000033, 99000034 a 99000044 y 99000045 a 99000055. Los correos de prueba son `docente410@example.invalid`, `docente411@example.invalid`, `coordinacion@example.invalid` y `docente.varias@example.invalid`, y ningún ejemplo usa un dominio real. Lo que no existe en las migraciones V1_01 a V1_08 va marcado «(V1_09)», «(script de plataforma)» o «(script de datos)». Lo que el redactor decide sin fuente va marcado «(propuesta)».

Prefijos e identificadores. La épica lleva el prefijo EP, cada historia de usuario US (user story), cada requisito funcional FR (functional requirement) y cada criterio de éxito SC (success criterion). Las 25 historias candidatas de la auditoría se nombran C-01 a C-25 (con letra cuando se parten, como C-19b), y US-NN queda solo para las 21 historias finales. N# es una fila del Excel `Requisitos_Sistema_Medicion.xlsx`; H##, C# y P## son filas de `Entregables/Revision_Requisitos_y_Tableros.xlsx`; Q## es una consulta de control y A## o R## un caso de prueba de `db/pruebas/pruebas.sql`; F-NN y los demás números de faltantes remiten a los informes de auditoría resumidos en `revision-historias.md`.

Siglas y términos. API es la interfaz de programación de aplicaciones (application programming interface), CI la integración continua (continuous integration), FK una clave foránea (foreign key), JSON el formato de datos JavaScript Object Notation, URL la dirección web (uniform resource locator), CORS el uso compartido de recursos entre orígenes (cross-origin resource sharing), DNS el sistema de nombres de dominio (Domain Name System), IA la inteligencia artificial y PR una solicitud de integración (pull request). SPF, DKIM y DMARC son los registros de autenticación del correo de un dominio, y SES es el servicio de correo Amazon Simple Email Service. Los anglicismos fijos se conservan con este sentido. Una spec es una especificación, el export es el archivo de calificaciones que exporta Blackboard, una feature es una funcionalidad, el merge es la fusión de un PR, el pooler es el agrupador de conexiones de Neon y el preflight es la revisión previa de `scripts/preflight.sh`. Production (producción) y Preview (vista previa) son los entornos de Vercel. La prueba de humo es el recorrido mínimo de punta a punta que confirma que el sistema desplegado responde.

Cifras de prueba, comprobadas contra `db/pruebas/datos_sinteticos.sql`.

| Archivo | Filas de datos / leídas / aceptadas / rechazadas | Mediciones | R-17 (5.1, 5.2, 5.3) | Filas en `rechazo_fila` |
| --- | --- | --- | --- | --- |
| `tests/datos_inventados/sintetico_20262_450002_410.xlsx` (por crear) | 11 / 11 / 11 / 0 | 33 | 63,6 % (7 de 11), 63,6 % (7 de 11), 72,7 % (8 de 11), meta 80 %, provisional | 1, AVISO `PUNTAJE_MAXIMO_DISTINTO` en 5.3 |
| `tests/datos_inventados/export_inventado_410_con_error.xlsx` (copia de `ejemplos_inventados/`) | 11 / 11 / 10 / 1 | 30 | 60,0 % (6 de 10), 60,0 % (6 de 10), 70,0 % (7 de 10) | 2, `NIVEL_FUERA_DE_ESCALA` con `RECHAZA_FILA` en la fila 3 (99000002, un 5 en 5.2) y el AVISO de 5.3 |
| Export con 10000004 en la fila 4 de Username | sin carga | 0 | sin R-17 | 0, respuesta 422 antes de escribir |

Los escenarios Gherkin viven en un solo lugar, `specs/001-mvp-carga-r17/aceptacion/*.feature`, en español (`# language: es`). Los pasos viven en `tests/aceptacion/pasos/` y leen los `.feature` desde esa carpeta con `scenarios()` de pytest-bdd y la ruta relativa, así que nadie los copia ni los mueve a `tests/`. Son siete archivos, `base_neon.feature` (US-01 a US-04), `acceso.feature` (US-05, US-06 y US-20), `carga.feature` (US-07 a US-14 y US-21), `r17_constancia.feature` (US-15 y US-16), `despliegue.feature` (US-17), `reemplazo_y_cargas.feature` (US-18 y US-19) y `varias_secciones.feature`. Este último reúne los seis escenarios del profesor que dicta varias secciones (US-06, US-07, US-09 y US-13). Cada escenario lleva `@US-NN` y `@corte1` o `@corte2`. Cada historia de abajo lista sus escenarios con el título y su Dado, Cuando y Entonces en una línea, y nombra el archivo `.feature` que los contiene. Cuando un texto literal de pantalla o de la API difiere, manda el del `.feature`, porque es la prueba. Las pruebas de aceptación corren siempre contra un PostgreSQL 16 desechable, y en Neon solo se comprueban los criterios de despliegue que no escriben cargas, que son la migración y los controles de US-01 y los escenarios de `despliegue.feature` de región, reescritura, cookie, pooler y guardia, además de la prueba de humo contra Preview (J-09).

## Clarifications

### Session 2026-10-28

- Jefferson pide en el chat, con estas palabras, «se espera lo siguiente / un profesor está dictando muchos cursos de muchas secciones / él solo puede cargar el export de su sección que le corresponde en el lugar donde le corresponde». Después responde «Sí, agrégalos» a la pregunta «¿Agrego a la spec los seis escenarios del profesor con varias secciones?».
- Las reglas de negocio (business rules, BR) de las specs vivas ya sostienen el pedido. BR-ACCESO-07 y BR-ACCESO-08 de `specs/features/acceso/acceso.spec.md` dejan al profesor solo con las secciones que le asigna `acceso.docente_seccion` y responden 403 con «La sección no está a su cargo.» en cualquier otra. BR-CARGA-09 de `specs/features/carga-export/carga-export.spec.md` detiene un archivo ya publicado en otra sección, y BR-CARGA-11 y BR-CARGA-12 exigen que el archivo declare la asignatura, la sección y el periodo de la sección elegida.
- Los datos de `db/datos/periodo_2026_2_inventado.sql` tienen un profesor por sección y una sola asignatura, así que `specs/001-mvp-carga-r17/aceptacion/varias_secciones.feature` suma los seis escenarios con `docente.varias@example.invalid`. Según `db/datos/varias_secciones_2026_2_inventado.sql`, este profesor dicta la 412 de 450002 y la 410 y la 412 de 450010 en 2026-2. Los escenarios figuran en US-06 (7 y 8), US-07 (8), US-09 (7) y US-13 (6 y 7).

## User Scenarios & Testing *(mandatory)*

### US-01: Migrar y verificar la base en Neon (Priority: P1)

Como administrador técnico, quiero aplicar con Flyway las migraciones del esquema `abet` en Neon y comprobarlas con las consultas de control para que la carrera tenga su base en la nube con las mismas garantías que las bases desechables de prueba.

**Why this priority**: es el resultado (1) del MVP, «tener una base de datos en la nube», y ninguna otra historia funciona sin él.

**Independent Test**: sobre un proyecto de Neon vacío, `flyway -environment=neon migrate` seguido de `controles_neon.sql` con el usuario `abet_respaldo` deja las versiones 1.01 a 1.08 en «Success» y Q01 a Q14 en 0 filas.

**Base**: `flyway_schema_history`; `V1_01__crear_organizacion` a `V1_08__crear_mediciones`; `R__vista_r17_por_pi` y `R__vista_tabla_maestra_pi` (`v_r17_por_pi` y `v_tabla_maestra_pi` con `security_barrier`); callback `afterMigrate__permisos_lectura.sql`; `flyway.toml`, entorno `neon`, que hereda `cleanDisabled = true`; semilla de V1_03 (7 filas en `so`, 17 en `pi`, 102 en `rubrica_nivel`, 53 en `asignatura`, 61 en `asignatura_so` y 7 en `instrumento`) y de V1_06 (`conjunto_reglas` R-2026-BORRADOR); consultas Q01 a Q14 de `db/pruebas/pruebas.sql` copiadas como consultas sueltas en `controles_neon.sql` (script de plataforma, solo lectura); `abet_respaldo` con `default_transaction_read_only`.
**Pantalla**: sin pantalla (Flyway con conexión directa, sin «-pooler»).
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/base_neon.feature`):

1. **Primera migración en Neon.** **Dado** un proyecto de Neon en aws-sa-east-1 con la base vacía, **Cuando** el administrador técnico ejecuta `flyway -environment=neon migrate`, **Entonces** `flyway info` muestra 1.01 a 1.08 y las dos vistas repetibles en «Success», `abet.so` tiene 7 filas, `abet.pi` 17, `abet.rubrica_nivel` 102, `abet.asignatura` 53, `abet.asignatura_so` 61, `abet.instrumento` 7, `conjunto_reglas` trae R-2026-BORRADOR en BORRADOR y `pg_class.reloptions` de `v_r17_por_pi` y de `v_tabla_maestra_pi` contiene `security_barrier=true`.
2. **Repetir la migración no cambia nada.** **Dado** la base con 1.01 a 1.08 aplicadas, **Cuando** se ejecuta otra vez `migrate`, **Entonces** Flyway informa 0 migraciones aplicadas y `abet.pi` sigue con 17 filas.
3. **Clean prohibido en la base compartida.** **Dado** el entorno `neon`, **Cuando** se ejecuta `flyway -environment=neon clean`, **Entonces** Flyway rechaza la orden porque `cleanDisabled` vale true y `abet.pi` sigue con 17 filas.
4. **Base recién preparada sin anomalías.** **Dado** la base migrada y una conexión con `abet_respaldo`, **Cuando** el administrador técnico corre `controles_neon.sql`, **Entonces** Q01 a Q14 devuelven 0 filas cada una.
5. **Los controles no escriben.** **Dado** una conexión con `abet_respaldo`, **Cuando** corre `controles_neon.sql`, **Entonces** la sesión trabaja con `default_transaction_read_only` activo y el número de filas de `abet.carga` es el mismo antes y después.
6. **Ninguna credencial en los archivos que versiona git.** **Dado** la conexión de Neon guardada solo en un archivo local `.env.neon`, **Cuando** se busca el valor de `NEON_DB_PASSWORD` en los archivos de `git ls-files` y en `git log -p --all`, **Entonces** no aparece en ningún archivo versionado ni en ningún commit, `git check-ignore -v .env.neon` responde con la regla `.env.*` de `.gitignore` y `bash scripts/preflight.sh` termina sin fallas de las reglas 3 y 4.
7. **La CI del Back reproduce la base desde cero sin Redgate.** **Dado** el contenido de `bd/` trasladado a `db/` del Back con su historia de git, **Cuando** la CI corre `correr_pruebas.sh` con psql contra un PostgreSQL 16 desechable, **Entonces** la salida termina con «RESULTADO: todo pasó» y código 0, ningún archivo de `.github/workflows/` nombra una imagen o una acción de Redgate o de Flyway y `git log --follow` de `V1_07__crear_registro_cargas.sql` muestra los commits que tenía en `ABET_ULIMA`.

---

### US-02: Crear el rol de la aplicación con privilegio mínimo (Priority: P1)

Como administrador técnico, quiero un único rol de base `abet_app` para la API que solo inserte las filas de una carga, actualice su estado y sus conteos y lea lo necesario para que ni un error del programa ni una cadena de conexión filtrada puedan borrar mediciones ni cambiar las reglas de una carga publicada.

**Why this priority**: la regla «nunca editar `carga.conjunto_reglas_id` de una carga publicada» no tiene restricción en la base y solo la sostienen los permisos; sin este rol la API se conecta con el usuario dueño.

**Independent Test**: con una conexión `abet_app`, una carga completa de la sección 411 confirma sin error y todo DELETE, TRUNCATE o UPDATE fuera de las columnas permitidas responde «permission denied».

**Base**: rol `abet_app` (script de plataforma `db/plataforma/neon/crear_rol_app.sql`); INSERT en `archivo_origen`, `carga`, `carga_columna`, `carga_fila`, `estudiante`, `medicion` y `rechazo_fila`; UPDATE solo de `carga (estado, filas_leidas, filas_aceptadas, filas_rechazadas, terminada_en)`; SELECT sobre organización, catálogo, `plan_medicion`, `conjunto_reglas`, `parametro_valor`, registro y las vistas `v_r17_por_pi` y `v_tabla_maestra_pi`; en `acceso`, SELECT, INSERT y UPDATE donde haga falta (V1_09); sin DELETE ni TRUNCATE en `abet`; sin escritura en `conjunto_reglas`, `parametro_valor`, `catalogo_*`, `plan_medicion` ni `seccion`; `fk_carga_reglas`; consulta Q08; `afterMigrate__permisos_lectura.sql` repone también los permisos de `abet_app` sobre tablas nuevas (propuesta).
**Pantalla**: sin pantalla.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/base_neon.feature`):

1. **La API publica una carga válida.** **Dado** una conexión `abet_app` y la sección 411 sin cargas, **Cuando** inserta en una sola transacción el archivo, la carga, 3 `carga_columna`, 11 `estudiante` con los códigos 99000012 a 99000022, 11 `carga_fila` y 33 `medicion`, y deja la carga PUBLICADA con 11 / 11 / 0 y `terminada_en` no nulo, **Entonces** la transacción confirma y Q08 devuelve 0 filas.
2. **El rol no borra ni vacía tablas (esquema con DELETE en `medicion`, `carga_fila`, `carga`, `archivo_origen`, `rechazo_fila` y `estudiante`, y TRUNCATE en `medicion` y `carga`).** **Dado** una carga PUBLICADA de la 410 con 33 mediciones, **Cuando** `abet_app` ejecuta `<orden> abet.<tabla>`, **Entonces** PostgreSQL responde «permission denied for table <tabla>» y `medicion` sigue con las 33 filas de la 410.
3. **El rol solo actualiza el estado y los conteos de una carga (esquema con las columnas `conjunto_reglas_id`, `subida_por`, `archivo_id`, `seccion_id` y `reemplaza_carga_id`).** **Dado** la carga PUBLICADA de la 410 con R-2026-BORRADOR, **Cuando** `abet_app` ejecuta un UPDATE de esa columna de `abet.carga`, **Entonces** PostgreSQL responde «permission denied for table carga» y la carga conserva su valor anterior en esa columna.
4. **El rol no escribe reglas, catálogo ni datos del periodo (esquema con UPDATE de `conjunto_reglas`, `parametro_valor`, `catalogo_version` y `seccion`, e INSERT en `conjunto_reglas`, `catalogo_vigencia` y `plan_medicion`).** **Dado** una conexión `abet_app`, **Cuando** ejecuta esa orden sobre `abet.<tabla>`, **Entonces** PostgreSQL responde «permission denied for table <tabla>».
5. **El rol lee las vistas del R-17.** **Dado** una conexión `abet_app` y los datos de `periodo_2026_2_inventado.sql`, **Cuando** consulta `v_r17_por_pi` y `v_tabla_maestra_pi`, **Entonces** ambas responden sin error de permisos.
6. **El script crea `abet_app` sin atributos de administración.** **Dado** una base PostgreSQL 16 desechable con V1_01 a V1_09 y `APP_DB_CLAVE` definida solo en el entorno de la terminal, **Cuando** el administrador técnico corre `crear_rol_app.sql` con psql, **Entonces** `pg_roles` muestra `abet_app` con `rolcanlogin` verdadero y `rolsuper`, `rolbypassrls`, `rolcreaterole`, `rolcreatedb` y `rolreplication` falsos, y la salida del script no muestra la clave.
7. **El rol no borra ni da de alta usuarios en `acceso` (esquema con un DELETE en `usuario_autorizado`, `sesion`, `credencial` y `docente_seccion`, un INSERT de un usuario nuevo, un UPDATE que cambia el rol a COORDINADOR y un INSERT que asigna la 411 al profesor de la 410).** **Dado** una conexión `abet_app`, **Cuando** ejecuta esa orden sobre `acceso.<tabla>`, **Entonces** PostgreSQL responde «permission denied for table <tabla>» (propuesta).
8. **Los permisos de `abet_app` sobreviven a una nueva migración.** **Dado** `abet_app` creado con `crear_rol_app.sql`, **Cuando** la prueba aplica con psql una migración de prueba y después `afterMigrate__permisos_lectura.sql`, **Entonces** `has_table_privilege` da verdadero para INSERT en `abet.medicion` y SELECT en `abet.v_r17_por_pi` y falso para DELETE en `abet.medicion` (propuesta).

---

### US-03: Preparar el periodo 2026-2 con datos inventados (Priority: P1)

Como administrador técnico, quiero sembrar en Neon la vigencia del catálogo, las secciones 410 y 411 y el plan de medición de 450002 en 2026-2 con datos inventados para que la base acepte las columnas de PI del export, mientras la carrera entrega los datos reales.

**Why this priority**: sin `catalogo_vigencia` y `plan_medicion` la base rechaza toda columna de PI por `fk_carga_columna_plan`, así que el resultado (3) no ocurre.

**Independent Test**: tras `psql -f db/datos/periodo_2026_2_inventado.sql`, `abet.plan_medicion` tiene 3 filas para 450002 en 2026-2 y Q05 devuelve 0 filas.

**Base**: `catalogo_vigencia` (`pk_catalogo_vigencia`, `fk_catalogo_vigencia_version`); `seccion` (`uq_seccion`, `ck_seccion_numero`, `uq_seccion_curso_bb`); `plan_medicion` (`uq_plan_medicion`, `fk_plan_medicion_vigencia`, `fk_plan_medicion_asig_so`, `fk_plan_medicion_pi`); consulta Q05; script `db/datos/periodo_2026_2_inventado.sql` (script de datos, no migración), que siembra además los usuarios de US-04; configuración de la API `PERIODO_VIGENTE=2026-2` y `CONJUNTO_REGLAS=R-2026-BORRADOR`, porque la base no marca un periodo ni un conjunto como vigente.
**Pantalla**: sin pantalla en el MVP.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/base_neon.feature`):

1. **Registrar la vigencia, las secciones y el plan.** **Dado** la base con la semilla AMB-2026 de V1_03, **Cuando** el administrador técnico ejecuta `periodo_2026_2_inventado.sql`, **Entonces** `catalogo_vigencia` tiene 1 fila de Ambiental en 2026-2 con AMB-2026, `seccion` tiene la 410 y la 411 de 450002 con `curso_blackboard` «SINTETICO_20262_450002_410» y «SINTETICO_20262_450002_411», `plan_medicion` tiene 3 filas (5.1, 5.2 y 5.3) y Q05 devuelve 0 filas.
2. **El script se puede repetir sin duplicar.** **Dado** el script ya aplicado, **Cuando** se ejecuta otra vez, **Entonces** termina sin error y los conteos de `seccion` y `plan_medicion` no cambian (propuesta, el script usa `ON CONFLICT DO NOTHING`).
3. **El número de sección no admite ceros a la izquierda.** **Dado** una base PostgreSQL 16 desechable con V1_01 a V1_09 y los datos de `periodo_2026_2_inventado.sql`, **Cuando** el administrador técnico inserta la sección «0410» de 450002 en 2026-2, **Entonces** la base la rechaza por `ck_seccion_numero` (los casos de `pk_catalogo_vigencia`, `uq_seccion` y `fk_plan_medicion_vigencia` ya están en `pruebas.sql`).
4. **La API no arranca con un periodo o un conjunto de reglas que la base no conoce (esquema con `PERIODO_VIGENTE=2027-1` y con `CONJUNTO_REGLAS=R-NO-EXISTE`).** **Dado** la API configurada con ese valor, **Cuando** arranca contra la base, **Entonces** el arranque se detiene con «PERIODO_VIGENTE 2027-1 no existe en abet.periodo» o «CONJUNTO_REGLAS R-NO-EXISTE no existe para Ambiental» y `abet.carga` no gana filas (propuesta, porque la base no marca un periodo ni un conjunto como vigente).
5. **El script de datos solo trae datos inventados.** **Dado** `periodo_2026_2_inventado.sql`, **Cuando** se buscan en él los números de 8 dígitos y los correos, **Entonces** todo número de 8 dígitos empieza con 99 y todo correo termina en «@example.invalid».

---

### US-04: Registrar usuarios autorizados y docentes por sección (Priority: P1)

Como administrador técnico, quiero aplicar la migración V1_09 con el esquema `acceso` y registrar por script los correos autorizados con su rol y las secciones de cada profesor para que la aplicación sepa quién entra y qué ve cada uno.

**Why this priority**: la regla «los de arriba pueden ver hacia abajo, pero no los de abajo hacia arriba» necesita saber qué profesor dicta qué sección, y el registro de quién sube cada carga necesita `carga.subida_por`.

**Independent Test**: tras `flyway migrate` con V1_09 y el script de datos, `acceso.usuario_autorizado` tiene 3 filas, `acceso.docente_seccion` 2 filas y Q04 sigue en 0 filas.

**Base**: `V1_09__crear_acceso.sql` (V1_09) con `acceso.usuario_autorizado` (correo normalizado único, rol PROFESOR o COORDINADOR, `activo`, `creado_en`, `ck_usuario_autorizado_correo` (propuesta, exige minúsculas sin espacios)), `acceso.credencial` (hash Argon2id, `actualizado_en`), `acceso.sesion` (hash del token, usuario, `expira_en`, `creada_en`), `acceso.intento_fallido` (`hash_cuenta`, el hash del correo normalizado con el secreto de la aplicación, e `intentado_en`, sin FK, para el límite de intentos de US-05), `acceso.docente_seccion` (usuario y `seccion_id` con FK a `abet.seccion`, `uq_docente_seccion` (propuesta)), `acceso.codigo_acceso` (para US-20); columna `abet.carga.subida_por` con FK a `acceso.usuario_autorizado`, nula en cargas anteriores; columna `abet.rechazo_fila.pi_id` con el PI de PI_DEL_PLAN_AUSENTE o de PI_REPETIDO (`fk_rechazo_fila_pi` y `ck_rechazo_fila_pi`), nula en los demás motivos y en los rechazos anteriores; motivos nuevos en `ck_rechazo_fila_motivo` (`COLUMNA_CODIGO_AUSENTE`, `PI_REPETIDO`, `PERIODO_NO_COINCIDE` y `SECCION_SIN_DECLARAR`); `flyway.toml` con `schemas = ["abet", "acceso"]`; consulta Q04 y una consulta Q15 (propuesta) que aplica el filtro de Q04 al esquema `acceso`.
**Pantalla**: sin pantalla en el MVP.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/base_neon.feature`):

1. **El script de datos registra a los usuarios de prueba y sus secciones.** **Dado** una base PostgreSQL 16 desechable con V1_01 a V1_09, **Cuando** el administrador técnico ejecuta `db/datos/periodo_2026_2_inventado.sql`, **Entonces** `acceso.usuario_autorizado` tiene activos a `coordinacion@example.invalid` con rol COORDINADOR y a `docente410@example.invalid` y `docente411@example.invalid` con rol PROFESOR, `acceso.docente_seccion` asigna la 410 de 450002 en 2026-2 a `docente410@example.invalid` y la 411 a `docente411@example.invalid`, pero no tiene filas de `coordinacion@example.invalid`, y `acceso.credencial` no tiene filas, porque la contraseña se asigna aparte con el comando de US-05.
2. **La base no guarda un correo sin normalizar.** **Dado** una base PostgreSQL 16 desechable con V1_01 a V1_09 y los usuarios de prueba registrados por el script de datos, **Cuando** el administrador técnico inserta directamente el usuario « Docente412@EXAMPLE.invalid » sin normalizar, **Entonces** la base rechaza la fila por `ck_usuario_autorizado_correo`.
3. **La base rechaza un registro de acceso inválido (esquema con cinco casos).** **Dado** una base PostgreSQL 16 desechable con V1_01 a V1_09 y los usuarios de prueba registrados por el script de datos, **Cuando** el administrador técnico inserta el usuario `otro@example.invalid` con rol «ADMIN», inserta otra vez a `docente410@example.invalid` con rol PROFESOR, inserta « Docente412@EXAMPLE.invalid » sin normalizar, asigna otra vez la 410 a `docente410@example.invalid` o le asigna una `seccion_id` que no existe, **Entonces** la base rechaza cada fila, en ese orden, por `ck_usuario_autorizado_rol`, `uq_usuario_autorizado_correo`, `ck_usuario_autorizado_correo`, `uq_docente_seccion` y `fk_docente_seccion_seccion` (propuesta, los nombres de las restricciones se fijan al escribir V1_09).
4. **Los correos no entran a `abet`.** **Dado** V1_09 aplicada, **Cuando** el administrador técnico corre Q04 y Q15, **Entonces** Q04 devuelve 0 filas y Q15 solo devuelve la columna del correo normalizado de `acceso.usuario_autorizado`.
5. **Las cargas anteriores conservan `subida_por` nulo.** **Dado** una base PostgreSQL 16 desechable con V1_01 a V1_08 y la carga PUBLICADA de la 410 de `db/pruebas/datos_sinteticos.sql`, **Cuando** se aplica V1_09 con psql, **Entonces** esa carga sigue PUBLICADA con `subida_por` nulo y Q01 a Q14 siguen en 0 filas.
6. **V1_09 crea el esquema acceso y los motivos nuevos.** **Dado** una base PostgreSQL 16 desechable con V1_01 a V1_08 y `db/flyway.toml` con `schemas = ["abet", "acceso"]` en sus entornos, **Cuando** la prueba aplica `V1_09__crear_acceso.sql` con psql, como `correr_pruebas.sh`, **Entonces** psql termina con código 0, `acceso` tiene las tablas `usuario_autorizado`, `credencial`, `sesion`, `intento_fallido`, `docente_seccion` y `codigo_acceso`, `abet.carga` tiene la columna `subida_por`, que admite nulo y tiene una FK hacia `acceso.usuario_autorizado`, `ck_rechazo_fila_motivo` admite `COLUMNA_CODIGO_AUSENTE`, `PI_REPETIDO`, `PERIODO_NO_COINCIDE` y `SECCION_SIN_DECLARAR` además de los 10 motivos de V1_07, y Q01 a Q14 siguen en 0 filas.

---

### US-05: Iniciar sesión con contraseña asignada (Priority: P1)

Como usuario autorizado, quiero entrar con mi correo y la contraseña que me asigna el administrador técnico para usar el sistema la primera semana sin depender de un proveedor de correo.

**Why this priority**: una URL pública que escribe en Neon no puede recibir archivos de cualquiera, y la contraseña asignada evita que el piloto espere la configuración del correo saliente (decisión J-03).

**Independent Test**: `POST /api/sesion` con las credenciales de prueba devuelve 200 y la cookie `abet_sesion`, y `GET /api/sesion` devuelve el correo y el rol.

**Base**: `acceso.usuario_autorizado` (`activo`), `acceso.credencial` (hash Argon2id), `acceso.sesion` (hash del token, `expira_en`), `acceso.intento_fallido` (hash del correo de cada intento fallido, exista o no el usuario) (V1_09); comando de asignación de contraseña en `scripts/` (propuesta, la contraseña se pide por la terminal y nunca se escribe en un archivo); rutas `POST`, `GET` y `DELETE /api/sesion`.
**Pantalla**: P1 Ingreso.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/acceso.feature`):

1. **El profesor autorizado entra.** **Dado** `docente410@example.invalid` activo con su contraseña asignada, **Cuando** envía correo y contraseña a `POST /api/sesion`, **Entonces** recibe 200, la cookie `abet_sesion` HttpOnly, Secure, SameSite=Lax y de 12 horas, `acceso.sesion` gana 1 fila con el hash del token y no con el token, y la pantalla pasa a P2.
2. **Correo desconocido y contraseña errada reciben la misma respuesta (esquema).** **Dado** `desconocido@example.invalid` sin registro y `docente410@example.invalid` con otra contraseña, **Cuando** cada uno intenta entrar, **Entonces** ambos reciben 401 con el mismo `{ "detail": "Correo o contraseña incorrectos." }` (propuesta) y no se crea ninguna sesión.
3. **Un usuario inactivo no entra.** **Dado** un usuario con `activo` falso y una sesión abierta, **Cuando** intenta entrar o usa su sesión previa, **Entonces** el ingreso responde 401 y la sesión previa responde 401 en cualquier ruta.
4. **El límite de intentos frena la adivinanza.** **Dado** `docente410@example.invalid`, **Cuando** falla 5 veces seguidas en 15 minutos (propuesta), **Entonces** el sexto intento responde 429 con «Demasiados intentos. Espere 15 minutos.» aunque la contraseña sea correcta.
5. **La sesión vence y se cierra.** **Dado** una sesión con `expira_en` vencido, **Cuando** llama a `GET /api/sesion`, **Entonces** recibe 401; y **Dado** una sesión vigente, **Cuando** llama a `DELETE /api/sesion`, **Entonces** la API responde 204, la cookie vuelve con Max-Age 0 y la fila de `acceso.sesion` queda vencida sin borrarse, porque `abet_app` no borra.
6. **Sin sesión ninguna ruta de datos responde (esquema con `GET /api/sesion`, `POST /api/secciones/{id de la 410}/cargas`, la constancia `GET /api/cargas/{carga_id}` y el R-17 `GET /api/cargas/{carga_id}/r17.xlsx`).** **Dado** una petición sin la cookie `abet_sesion`, **Cuando** llama a cada una de esas rutas, **Entonces** la API responde 401 y `archivo_origen` y `carga` no ganan filas.
7. **El administrador técnico asigna una contraseña por comando.** **Dado** `docente410@example.invalid` registrado, **Cuando** el administrador técnico corre el comando de asignar contraseña con una contraseña de prueba generada al azar, **Entonces** `acceso.credencial` tiene 1 fila de ese usuario con un hash que empieza por «$argon2id$», el texto de la contraseña no aparece en ninguna fila de `acceso` y la salida del comando no lo muestra.
8. **El correo se compara sin espacios ni mayúsculas.** **Dado** `docente410@example.invalid` con su contraseña asignada, **Cuando** envía « Docente410@EXAMPLE.invalid » y esa contraseña a `POST /api/sesion`, **Entonces** la API responde 200 con el correo `docente410@example.invalid`.

---

### US-06: Ver solo mis secciones del periodo (Priority: P1)

Como profesor, quiero ver solo las secciones que dicto en el periodo vigente, con el estado de su carga, para subir el export en la sección correcta sin ver datos de otros docentes (el coordinador ve todas las de la carrera).

**Why this priority**: el profesor elige la sección (D-02), y esa elección necesita una lista que cumpla la regla de visibilidad. Esta historia es la única dueña de esa regla; las demás solo repiten el caso de su propia ruta.

**Independent Test**: `GET /api/secciones?periodo=2026-2` devuelve 1 sección al profesor de la 410 y 2 al coordinador.

**Base**: `periodo` (`uq_periodo_codigo`), `asignatura`, `seccion` (`uq_seccion`), `carga` (`uq_carga_publicada_por_seccion`), `plan_medicion` (`uq_plan_medicion`); `acceso.docente_seccion` y `acceso.usuario_autorizado` (V1_09); `PERIODO_VIGENTE`.
**Pantalla**: P2 Mis secciones.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/acceso.feature`; los escenarios 7 y 8, en `varias_secciones.feature`):

1. **El profesor ve únicamente su sección.** **Dado** la 410 asignada a `docente410@example.invalid` y la 411 a `docente411@example.invalid`, **Cuando** el profesor de la 410 abre P2, **Entonces** la lista muestra 1 fila, «450002 Principios de Ingeniería Sostenible, sección 410, 2026-2» (propuesta), con los PI «5.1, 5.2, 5.3» y el estado «Sin carga», y no muestra la 411.
2. **El coordinador ve todas.** **Dado** `coordinacion@example.invalid` con rol COORDINADOR y sin secciones asignadas, **Cuando** abre P2, **Entonces** la lista muestra la 410 y la 411.
3. **El estado refleja la carga publicada.** **Dado** la 410 con una carga PUBLICADA de 11 aceptadas, **Cuando** su profesor abre P2, **Entonces** la fila muestra «Publicada, 11 de 11 filas aceptadas».
4. **El profesor no sube en una sección ajena.** **Dado** el profesor de la 410 con sesión y la 411 con la carga PUBLICADA de `export_inventado_411.xlsx`, **Cuando** envía ese mismo archivo a `POST /api/secciones/{id de la 411}/cargas`, **Entonces** la API responde 403 con «La sección no está a su cargo.», la respuesta no trae datos de la 411 y `abet.carga` no gana filas.
5. **Sección de una asignatura sin plan.** **Dado** una sección de prueba de otra asignatura sin filas en `plan_medicion` en 2026-2, asignada al profesor de la 410, **Cuando** abre P2, **Entonces** esa fila muestra «La carrera aún no registra el plan de medición de esta sección» y su botón «Subir export» está desactivado.
6. **Sin sesión no hay lista.** **Dado** una petición sin cookie, **Cuando** llama a `GET /api/secciones?periodo=2026-2`, **Entonces** recibe 401.
7. **El profesor de varias secciones ve sus tres secciones y ninguna otra.** **Dado** `docente.varias@example.invalid` con la 412 de 450002 y la 410 y la 412 de 450010 en `acceso.docente_seccion`, **Cuando** pide `GET /api/secciones?periodo=2026-2` y abre P2, **Entonces** recibe 200 con esas 3 secciones, todas con el estado «SIN_CARGA» (propuesta) y las dos 412 con `seccion_id` distintos. La de 450002 trae los PI 5.1, 5.2 y 5.3 y las de 450010 traen 2.1, 2.2 y 5.1, sin ningún dato de la 410 ni de la 411 de 450002. En P2, el botón «Subir export» de cada fila abre P3 con esa sección, y P3 sube el archivo al `seccion_id` de esa fila, también en las dos 412.
8. **El profesor de varias secciones no alcanza una sección que no dicta (esquema).** **Dado** la carga PUBLICADA de `sintetico_20262_450002_410.xlsx` en la 410 de 450002, **Cuando** `docente.varias@example.invalid` envía a esa sección su export de la 412 de 450002 o el archivo ya publicado, o pide la constancia o el R-17 de esa carga, **Entonces** la API responde 403. El cuerpo trae «La sección no está a su cargo.» y ningún dato de esa sección ni de la carga de `docente410@example.invalid`, y `archivo_origen`, `carga` y `estudiante` no ganan filas.

---

### US-07: Subir el export y cargarlo en una sola transacción (Priority: P1)

Como profesor, quiero subir el export de Blackboard de mi sección y que sus datos queden cargados en la base de una vez o no queden para que el R-17 nunca salga de una carga a medias.

**Why this priority**: cubre los resultados (2) y (3), «que se pueda subir el export» y «que esos datos se carguen en la base de datos».

**Independent Test**: subir `sintetico_20262_450002_410.xlsx` en la 410 deja una carga PUBLICADA con 11 / 11 / 0, 33 mediciones y Q01, Q02, Q03, Q06, Q12 y Q13 en 0 filas.

**Base**: `archivo_origen` (`uq_archivo_origen_sha256`, `ck_archivo_origen_sha256`, `ck_archivo_origen_nombre`, `ck_archivo_origen_filas`, `ck_archivo_origen_tipo`); `carga` (`ck_carga_estado`, `ck_carga_filas`, `ck_carga_publicable`, `ck_carga_conciliada`, `ck_carga_terminada`, `fk_carga_archivo`, `fk_carga_reglas`, los índices únicos parciales `uq_carga_publicada_por_seccion` y `uq_carga_archivo_util`, `subida_por` (V1_09)); `acceso.docente_seccion` (V1_09), porque en el corte 1 solo sube el profesor asignado a la sección y el coordinador no sube; `carga_columna` (`ck_carga_columna_encabezado`, `fk_carga_columna_plan`, `uq_carga_columna_pi`, `ck_carga_columna_bb`); `estudiante` (`ck_estudiante_codigo`, `uq_estudiante_codigo`); `carga_fila` (`uq_carga_fila_estudiante`, `ck_carga_fila_fila`); `medicion` (`ck_medicion_nivel`, `ck_medicion_estado_nivel`, `uq_medicion`); consultas Q01, Q02, Q03, Q06, Q12 y Q13; ruta `POST /api/secciones/{seccion_id}/cargas` (multipart `archivo`).
**Pantalla**: P3 Subir export y P4 Resultado de la carga (versión mínima con los conteos).
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/carga.feature`; el escenario 8, en `varias_secciones.feature`):

1. **El export correcto queda publicado entero.** **Dado** la 410 sin cargas y su profesor con sesión, **Cuando** sube `sintetico_20262_450002_410.xlsx`, **Entonces** la API responde 201 con la constancia, `archivo_origen` registra el nombre sin ruta, la hoja `gc_SINTETICO_20262_450002_410_f`, `filas_de_datos` 11, `tipo_fuente` BLACKBOARD_EXPORT y una huella `sha256` de 64 caracteres hexadecimales en minúscula, igual a la salida de `shasum -a 256` del archivo, la carga queda PUBLICADA con 11 / 11 / 0, R-2026-BORRADOR y `subida_por` igual al usuario, `carga_columna` tiene 5.1, 5.2 y 5.3, `carga_fila` las filas 2 a 12, `medicion` 33 filas CALIFICADO con nivel 1 a 4, Q01, Q02, Q03, Q06, Q12 y Q13 dan 0 filas y ninguna carga queda EN_CURSO.
2. **Un fallo en cualquier punto no deja nada (esquema con el fallo tras `archivo_origen`, tras las 3 `carga_columna`, tras la medición 30 y antes de PUBLICADA).** **Dado** la prueba que inyecta un fallo de conexión en ese punto, **Cuando** el profesor sube el archivo, **Entonces** la API responde 500 con «La carga no se completó y no se guardó ningún dato. Intente de nuevo.» y `archivo_origen`, `carga`, `carga_columna`, `carga_fila`, `medicion`, `rechazo_fila` y `estudiante` no ganan filas.
3. **Una restricción violada al final deshace todo.** **Dado** un defecto inyectado que guarda un nivel 5 en la última medición, **Cuando** el profesor sube el archivo, **Entonces** la base lo rechaza por `ck_medicion_nivel`, `abet.carga` no tiene filas de la 410 y ninguna carga queda EN_CURSO.
4. **Otra carga publicada en la sección detiene la subida.** **Dado** la 410 con la carga PUBLICADA de `sintetico_20262_450002_410.xlsx`, **Cuando** el profesor sube `export_inventado_410_con_error.xlsx` sin pedir reemplazo, **Entonces** la API responde 409 con «La sección 410 ya tiene una carga publicada. No se cargó el archivo.» y `archivo_origen` y `carga` no ganan filas.
5. **Dos subidas a la vez dejan una sola publicada.** **Dado** dos envíos simultáneos de archivos distintos a la 410 vacía, **Cuando** ambos llegan a publicar, **Entonces** uno confirma y el otro termina en 409 por el índice único parcial `uq_carga_publicada_por_seccion`, sin carga EN_CURSO.
6. **El coordinador no sube en el corte 1.** **Dado** `coordinacion@example.invalid` con sesión y la 410 sin cargas, **Cuando** envía `sintetico_20262_450002_410.xlsx` a `POST /api/secciones/{id de la 410}/cargas`, **Entonces** la API responde 403 con «La sección no está a su cargo.» y `archivo_origen` y `carga` no ganan filas (el corte 2 le permite reemplazar, US-18).
7. **Un profesor no sube a una sección que no tiene asignada.** **Dado** el profesor de la 410 con sesión, **Cuando** sube `export_inventado_411.xlsx` a la sección 411, **Entonces** la API responde 403 con «La sección no está a su cargo.» y `archivo_origen`, `carga` y `estudiante` no ganan filas.
8. **Cada export del profesor de varias secciones se publica solo en su sección (esquema).** **Dado** `docente.varias@example.invalid` con sus tres secciones sin cargas, **Cuando** sube el export de una de ellas en esa misma sección, **Entonces** la API responde 201 con estado PUBLICADA, 11 / 11 / 0 y 33 mediciones. Esa sección queda con 1 sola carga PUBLICADA, `estudiante` gana solo los 11 códigos del export y las otras dos secciones siguen sin cargas.

---

### US-08: Rechazar exports con códigos que no son inventados (Priority: P1)

Como sistema, quiero rechazar antes de escribir nada todo export que traiga un código fuera de 99000000 a 99999999, y que la base de Neon lo impida también, para que ningún código real de estudiante llegue a la base mientras la universidad no autorice datos reales.

**Why this priority**: la regla «solo datos inventados en Neon, en Vercel y en los repositorios» no tiene otra barrera, y el único export real conocido es de 2026-2.

**Independent Test**: un export con 10000004 en la fila 4 recibe 422 y ninguna tabla gana filas; un INSERT directo de 10000004 en `abet.estudiante` falla por `ck_estudiante_codigo_inventado`.

**Base**: variable `GUARDIA_DATOS_INVENTADOS=1` del Back; script de plataforma `db/plataforma/neon/guardia_datos_inventados.sql` con `ck_estudiante_codigo_inventado CHECK (codigo LIKE '99%')` en `abet.estudiante`, solo en Neon; `archivo_origen`, `carga`, `rechazo_fila` y `estudiante` sin cambios ante un rechazo; `ck_estudiante_codigo`.
**Pantalla**: P3 Subir export.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/carga.feature`):

1. **Un export con códigos inventados pasa la guardia.** **Dado** la guardia encendida, **Cuando** el profesor sube `sintetico_20262_450002_410.xlsx`, **Entonces** la carga sigue la validación normal y queda PUBLICADA con 11 aceptadas (lo cubre US-07, escenario 1, con la guardia encendida en los Antecedentes de `carga.feature`).
2. **Un código real rechaza el archivo entero.** **Dado** un export de la 410 con 11 filas y 10000004 en Username de la fila 4, **Cuando** el profesor lo sube, **Entonces** la API responde 422 con «El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada.», la respuesta no contiene el código y `archivo_origen`, `carga`, `carga_columna`, `carga_fila`, `medicion`, `rechazo_fila` y `estudiante` no ganan filas.
3. **Otros códigos fuera del rango (esquema con 98999999 y 9900001).** **Dado** un export con ese valor en Username de la fila 4, **Cuando** el profesor lo sube, **Entonces** recibe el mismo 422, la respuesta no contiene el código y el registro de la aplicación guarda de ese rechazo solo la huella y la hora (prueba unitaria de app/rutas/cargas.py, fuera del .feature).
4. **Los extremos del rango se aceptan (esquema con 99000000 y 99999999).** **Dado** un export con ese código en Username de la fila 4, **Cuando** el profesor lo sube, **Entonces** la API responde 201, la carga queda PUBLICADA con 11 / 11 / 0 y `abet.estudiante` tiene ese código.
5. **La base rechaza un código real aunque el programa falle.** **Dado** una base desechable con el script de la guardia de Neon aplicado y una conexión directa con `abet_app`, **Cuando** se inserta 10000004 en `abet.estudiante`, **Entonces** la inserción falla por `ck_estudiante_codigo_inventado`.
6. **Ningún campo de la petición apaga la guardia.** **Dado** el export con 10000004 en la fila 4, **Cuando** el profesor lo sube con el campo multipart `guardia` igual a «0» y el parámetro de consulta `guardia=0`, **Entonces** recibe el mismo 422 y `archivo_origen`, `carga` y `estudiante` no ganan filas, porque la guardia solo cambia con la variable del despliegue y un cambio revisado.

---

### US-09: Reconocer un export ya cargado (Priority: P1)

Como profesor, quiero que el sistema reconozca un archivo que ya está en la base para que el mismo export nunca sume filas dos veces y yo reciba la constancia que ya existe.

**Why this priority**: el caso C9 de `Entregables/Revision_Requisitos_y_Tableros.xlsx` muestra que cargar el mismo archivo dos veces suma filas, y `uq_archivo_origen_sha256` haría fallar la transacción sin un mensaje claro.

**Independent Test**: subir dos veces `sintetico_20262_450002_410.xlsx` en la 410 devuelve 200 la segunda vez con la misma constancia y `archivo_origen` sigue con 1 fila para esa huella.

**Base**: `archivo_origen` (`sha256`, `nombre_archivo`, `recibido_en`, `uq_archivo_origen_sha256`); `carga` (índices únicos parciales `uq_carga_archivo_util` y `uq_carga_publicada_por_seccion`, caso R34 de `pruebas.sql`); `medicion` (`uq_medicion`); vista `v_tabla_maestra_pi`.
**Pantalla**: P3 Subir export.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/carga.feature`; el escenario 7, en `varias_secciones.feature`):

1. **Subir otra vez el export publicado no cambia nada.** **Dado** la 410 con la carga PUBLICADA de `sintetico_20262_450002_410.xlsx`, **Cuando** el profesor sube el mismo archivo, **Entonces** la API responde 200 con la constancia existente, `archivo_origen` sigue con 1 fila para esa huella, `carga` no gana filas y `v_tabla_maestra_pi` sigue con 33 filas de la 410.
2. **El mismo contenido con otro nombre se reconoce.** **Dado** la misma carga publicada, **Cuando** el profesor sube los mismos bytes como «copia de notas 410.xlsx», **Entonces** recibe la misma respuesta 200 y `nombre_archivo` sigue siendo `sintetico_20262_450002_410.xlsx`.
3. **Un archivo rechazado puede usarse en su sección correcta.** **Dado** `export_inventado_411.xlsx` rechazado en la 410 con SECCION_NO_COINCIDE (US-13), **Cuando** el profesor de la 411 lo sube en la 411, **Entonces** la carga nueva reutiliza el `archivo_id` de esa huella, queda PUBLICADA y `archivo_origen` sigue con 1 fila para esa huella.
4. **La base impide registrar dos veces la misma huella.** **Dado** una huella registrada, **Cuando** el programa intenta insertar otra fila con ella, **Entonces** la base la rechaza por `uq_archivo_origen_sha256`.
5. **Un export abierto y guardado de nuevo es otro archivo.** **Dado** la carga publicada de `sintetico_20262_450002_410.xlsx`, **Cuando** el profesor sube una copia vuelta a guardar en Excel, **Entonces** la huella difiere y la API responde 409 como en US-07, escenario 4.
6. **Un archivo publicado en otra sección no se carga.** **Dado** `sintetico_20262_450002_410.xlsx` PUBLICADO en la 410 y `docente411@example.invalid` con sesión, **Cuando** sube los mismos bytes con el nombre «notas 411.xlsx» en la 411, **Entonces** la API responde 409 con «Este archivo ya está publicado en otra sección. No se cargó.» antes de escribir, la respuesta no trae el `carga_id`, la huella ni el número de la 410, `archivo_origen`, `carga`, `rechazo_fila` y `estudiante` no ganan filas y la 411 sigue sin cargas, porque la base lo impediría con el índice único parcial `uq_carga_archivo_util`.
7. **Un archivo publicado en una sección del profesor se detiene en otra de sus secciones.** **Dado** `sintetico_20262_450002_412.xlsx` PUBLICADO en la 412 de 450002, **Cuando** `docente.varias@example.invalid` lo sube otra vez en la 410 de 450010, que también dicta, **Entonces** la API responde 409 con «Este archivo ya está publicado en otra sección. No se cargó.» antes de cotejar la hoja y sin datos de la 412. `archivo_origen`, `carga`, `rechazo_fila` y `estudiante` no ganan filas.

---

### US-10: Rechazar filas inválidas y avisar de columnas dudosas (Priority: P1)

Como sistema, quiero rechazar la fila completa que trae un nivel o un código inválido, guardar como sin evidencia la celda vacía y avisar de las columnas dudosas sin detener la carga para que el profesor sepa exactamente qué queda fuera y por qué.

**Why this priority**: sin estas reglas un código repetido llega a `uq_carga_fila_estudiante` y deshace la carga entera, y el profesor no tiene evidencia de que el export «se subió correctamente con sus datos».

**Independent Test**: `export_inventado_410_con_error.xlsx` deja 11 / 10 / 1, 30 mediciones y 2 filas en `rechazo_fila`, el rechazo de la fila 3 y el aviso de 5.3.

**Base**: `rechazo_fila` (`ck_rechazo_fila_motivo` con NIVEL_FUERA_DE_ESCALA, NIVEL_NO_NUMERICO, CODIGO_VACIO, CODIGO_INVALIDO, CODIGO_DUPLICADO, COLUMNA_PI_FUERA_DEL_PLAN y PUNTAJE_MAXIMO_DISTINTO; `ck_rechazo_fila_efecto`; `ck_rechazo_fila_con_fila`; `ck_rechazo_fila_fila`; `fk_rechazo_fila_columna`); `carga` (`ck_carga_filas`, `ck_carga_conciliada`, `ck_carga_publicable`); `carga_columna` (`puntaje_maximo_declarado`, `ck_carga_columna_puntaje`, `fk_carga_columna_plan`); `carga_fila`; `medicion` (`ck_medicion_estado_nivel`, estado SIN_EVIDENCIA); vista `v_r17_por_pi`; consultas Q01, Q02, Q03, Q12 y Q13.
**Pantalla**: P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/carga.feature`):

1. **El 5 de la fila 3 rechaza esa fila completa.** **Dado** la 410 sin cargas, **Cuando** el profesor sube `export_inventado_410_con_error.xlsx`, **Entonces** la carga queda PUBLICADA con 11 / 10 / 1 y 30 mediciones, `rechazo_fila` registra NIVEL_FUERA_DE_ESCALA con RECHAZA_FILA, `fila_origen` 3 y la columna de 5.2, 99000002 no tiene mediciones en 5.1, 5.2 ni 5.3 y `v_r17_por_pi` da 60,0 / 60,0 / 70,0.
2. **El Total Pts de 20 en 5.3 es un aviso.** **Dado** el mismo envío, **Cuando** termina la carga, **Entonces** `rechazo_fila` registra PUNTAJE_MAXIMO_DISTINTO con AVISO, `fila_origen` nulo y la columna de 5.3, y `carga_columna` de 5.3 guarda `puntaje_maximo_declarado` 20.
3. **Celdas de PI inválidas (esquema con 5, 0 y -1 para NIVEL_FUERA_DE_ESCALA, valor provisional de D-06, y 3,5, «Needs Grading», «-» y «NP» para NIVEL_NO_NUMERICO, valor provisional de D-03).** **Dado** un export cuya 5.2 de la fila 3 trae ese valor, **Cuando** el profesor lo sube, **Entonces** la fila 3 queda con ese motivo y RECHAZA_FILA y la carga con 11 / 10 / 1.
4. **Una celda de PI vacía es SIN_EVIDENCIA y no rechaza la fila.** **Dado** el export correcto con la 5.2 de la fila 3 vacía, **Cuando** el profesor lo sube, **Entonces** la carga queda con 11 / 11 / 0 y 33 mediciones, la de 99000002 en 5.2 con SIN_EVIDENCIA y `nivel_original` nulo, y `v_r17_por_pi` da en 5.2 `n_sin_evidencia` 1, `pct_logro_sobre_calificados` 60,0 y `pct_logro_sobre_total_con_sin_evidencia` 54,5, con 5.1 y 5.3 en 63,6 y 72,7.
5. **Un código vacío rechaza su fila.** **Dado** el export correcto con Username vacío en la fila 3, **Cuando** el profesor lo sube, **Entonces** la fila 3 queda con CODIGO_VACIO y RECHAZA_FILA, la carga con 11 / 10 / 1 y el R-17 con 60,0 / 60,0 / 70,0.
6. **Un código repetido rechaza su segunda aparición.** **Dado** el export correcto con 99000001 también en la fila 12, **Cuando** el profesor lo sube, **Entonces** la fila 12 queda con CODIGO_DUPLICADO y RECHAZA_FILA, la carga con 11 / 10 / 1 y el R-17 con 70,0 / 70,0 / 80,0.
7. **Una columna de PI fuera del plan se ignora con aviso.** **Dado** el export correcto con una columna más «4.1 [Total Pts: 4 Score] |9000041», **Cuando** el profesor lo sube, **Entonces** la carga queda PUBLICADA con 11 / 11 / 0, `carga_columna` solo tiene 5.1, 5.2 y 5.3 y `rechazo_fila` registra COLUMNA_PI_FUERA_DEL_PLAN con AVISO, `fila_origen` nulo y `carga_columna_id` nulo.
8. **Si todas las filas se rechazan, la carga no se publica.** **Dado** un export con un 5 en la 5.2 de las 11 filas, **Cuando** el profesor lo sube, **Entonces** la API responde 201 con el mensaje «Ninguna fila se pudo aceptar. La carga no se publicó.» (propuesta), la carga queda RECHAZADA con 11 / 0 / 11 y `medicion` no tiene filas de ella.
9. **La base no deja publicar cuentas que no cuadran.** **Dado** un defecto que deja `filas_leidas` 10, `filas_aceptadas` 10 y `filas_rechazadas` 0 en un archivo de 11 filas, **Cuando** intenta pasar a PUBLICADA, **Entonces** la base lo rechaza por `ck_carga_conciliada`; y un intento de guardar 11 / 10 / 0 lo rechaza `ck_carga_filas`.
10. **Con la guardia apagada, un código mal formado rechaza solo su fila.** **Dado** una base desechable sin el script de la guardia y la API con `GUARDIA_DATOS_INVENTADOS=0`, **Cuando** el profesor sube el export correcto con 9900001 en Username de la fila 4, **Entonces** la fila 4 queda con CODIGO_INVALIDO y RECHAZA_FILA, la carga con 11 / 10 / 1 y el R-17 con 70,0 / 60,0 / 70,0.

---

### US-11: Detener un archivo ilegible sin dejar rastro (Priority: P1)

Como profesor, quiero saber de inmediato si mi archivo no se puede leer, con un motivo claro, para volver a descargarlo de Blackboard sin que quede nada a medias en la base.

**Why this priority**: sin esta historia la API responde con un error genérico al primer archivo mal formado, y leer archivos de terceros es la pieza más expuesta del sistema.

**Independent Test**: los siete archivos de prueba defectuosos reciben 422 con su mensaje y `archivo_origen`, `carga` y `rechazo_fila` no ganan filas.

**Base**: `archivo_origen`, `carga` y `rechazo_fila` sin escritura, porque `archivo_origen.filas_de_datos` es obligatorio y no se puede medir; lector `abet_carga/lector.py` con openpyxl en solo lectura, sin pandas, con defusedxml activo y revisión previa del zip (tamaño descomprimido, sin `vbaProject.bin` ni `externalLinks`).
**Pantalla**: P3 Subir export.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/carga.feature`):

1. **El archivo ilegible se detiene antes de registrar nada (esquema).** **Dado** el profesor de la 410 con sesión, **Cuando** sube cada archivo, **Entonces** recibe 422 con su mensaje y `archivo_origen`, `carga` y `rechazo_fila` no ganan filas. Los ejemplos son una copia del export cortada a la mitad de sus bytes («No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard.»), una copia protegida con contraseña («El archivo está protegido con contraseña. Guárdelo sin contraseña y súbalo.»), un PDF inventado llamado `export_410.pdf` («Solo se admiten exports de Blackboard en formato .xlsx.»), el mismo PDF llamado `export_410.xlsx` («El contenido del archivo no es un libro de Excel aunque su nombre termine en .xlsx.»), una copia con la parte `xl/vbaProject.bin` o con `xl/externalLinks/` («El archivo trae macros o vínculos externos y no se admite.») y un .xlsx inventado de 1,2 MB («El archivo supera el máximo de 1 MB.»).
2. **Un libro que se infla al descomprimirse se rechaza.** **Dado** un .xlsx inventado de menos de 1 MB cuyo contenido descomprimido supera el límite fijado en `lector.py` (propuesta, 20 MB), **Cuando** el profesor lo sube, **Entonces** recibe 422 con «El contenido del archivo supera el tamaño admitido al descomprimirse.» (propuesta) y `archivo_origen`, `carga`, `rechazo_fila` y `estudiante` no ganan filas, porque la revisión del zip lo detiene antes de abrir el libro.
3. **El lector no arranca sin defusedxml.** **Dado** el entorno de pruebas, **Cuando** corre la prueba unitaria del lector, **Entonces** falla si `openpyxl.xml.DEFUSEDXML` es `False` (prueba unitaria de lector.py, fuera del .feature).
4. **El registro guarda el intento sin el contenido.** **Dado** cualquiera de los envíos del escenario 1, **Cuando** se revisa el registro de la aplicación, **Entonces** trae la huella, la hora y el motivo, y ningún nombre de hoja, celda ni código (prueba unitaria de app/rutas/cargas.py, fuera del .feature).

---

### US-12: Rechazar la carga por su estructura (Priority: P1)

Como profesor, quiero que el sistema rechace la carga entera cuando al export le falta lo que el plan pide, y que el intento quede registrado sin tocar el R-17, para corregir el export y subirlo otra vez.

**Why this priority**: un export sin la columna de un PI del plan o sin códigos no puede alimentar el R-17, y la constancia del intento es la evidencia de por qué no se publica.

**Independent Test**: un export sin la columna 5.2 deja una carga RECHAZADA con `filas_leidas` 0 y exactamente 1 fila de `rechazo_fila` con PI_DEL_PLAN_AUSENTE y RECHAZA_CARGA.

**Base**: `carga` (`ck_carga_estado`, `ck_carga_terminada`); `rechazo_fila` (`ck_rechazo_fila_motivo` con ARCHIVO_SIN_FILAS y PI_DEL_PLAN_AUSENTE de V1_07 y COLUMNA_CODIGO_AUSENTE y PI_REPETIDO de V1_09; efecto RECHAZA_CARGA); `carga_columna` sin filas en una carga rechazada por estructura; vista `v_r17_por_pi` (solo cargas en estado PUBLICADA); consulta Q03.
**Pantalla**: P3 Subir export y P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/carga.feature`):

1. **Un defecto de estructura rechaza la carga entera (esquema).** **Dado** el profesor de la 410 con sesión, **Cuando** sube un export con el defecto, **Entonces** la API responde 201 con estado RECHAZADA y el mensaje, la carga queda RECHAZADA con `filas_leidas` 0 y `terminada_en` no nulo, `rechazo_fila` tiene exactamente 1 fila con el motivo y RECHAZA_CARGA, `carga_columna`, `carga_fila` y `medicion` no tienen filas de ella y `v_r17_por_pi` no la ve. Los ejemplos son el encabezado sin filas de datos (ARCHIVO_SIN_FILAS, «El archivo no trae filas de estudiantes.»), la falta de la columna «5.2 [Total Pts: 4 Score]» (PI_DEL_PLAN_AUSENTE, «Falta la columna del PI 5.2 que el plan de medición pide para esta sección.»), la falta de Username y Student ID (COLUMNA_CODIGO_AUSENTE, «El archivo no tiene la columna Username ni Student ID.») y dos columnas de 5.1 (PI_REPETIDO, «El PI 5.1 aparece en dos columnas del archivo.»).
2. **Una carga rechazada por estructura no registra avisos.** **Dado** el export sin la columna 5.2, que conserva el 5.3 de 20 puntos, **Cuando** el profesor lo sube, **Entonces** `rechazo_fila` no registra el AVISO PUNTAJE_MAXIMO_DISTINTO.
3. **Después de un rechazo se puede volver a subir.** **Dado** una carga RECHAZADA de la 410 por PI_DEL_PLAN_AUSENTE, **Cuando** el profesor sube `sintetico_20262_450002_410.xlsx`, **Entonces** la 410 tiene 1 carga RECHAZADA con su fila de `rechazo_fila` y 1 carga PUBLICADA.
4. **La base no acepta un motivo que no existe.** **Dado** una conexión directa con `abet_app` y una carga EN_CURSO de la 410, **Cuando** inserta un rechazo con motivo «CODIGO_RARO» y efecto RECHAZA_CARGA, **Entonces** la base lo rechaza por `ck_rechazo_fila_motivo`.

---

### US-13: Rechazar el export de otra sección o periodo (Priority: P1)

Como profesor, quiero que el sistema rechace un export cuyo nombre de hoja indica otra sección, curso o periodo para no publicar por error notas ajenas en mi sección.

**Why this priority**: el profesor elige la sección y el sistema la coteja con la hoja y, si la hoja no la declara, con el nombre del archivo; sin el cotejo un error de elección publica datos en la sección equivocada.

**Independent Test**: `export_inventado_411.xlsx` subido en la 410 deja una carga RECHAZADA con SECCION_NO_COINCIDE y la 410 sin carga publicada.

**Base**: `seccion` (`numero`, `curso_blackboard`, `uq_seccion_curso_bb`); `archivo_origen` (`hoja`); `carga`; `rechazo_fila` (SECCION_NO_COINCIDE de V1_07 y PERIODO_NO_COINCIDE de V1_09, efecto RECHAZA_CARGA).
**Pantalla**: P3 Subir export y P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/carga.feature`; los escenarios 6 y 7, en `varias_secciones.feature`):

1. **El export de la 411 subido en la 410 se rechaza.** **Dado** la 410 sin cargas, **Cuando** su profesor sube `export_inventado_411.xlsx`, cuya hoja es `gc_SINTETICO_20262_450002_411_f`, **Entonces** la API responde 201 con el mensaje «El archivo corresponde a la sección 411 y usted eligió la 410. No se publicó.», la carga queda RECHAZADA con `filas_leidas` 0, `rechazo_fila` registra SECCION_NO_COINCIDE con RECHAZA_CARGA y la 410 sigue sin carga publicada.
2. **Curso o periodo distinto en la hoja (esquema).** **Dado** un export con la hoja `gc_SINTETICO_20261_450002_410_f` o `gc_SINTETICO_20262_450010_410_f`, **Cuando** el profesor lo sube en la 410, **Entonces** la carga queda RECHAZADA con PERIODO_NO_COINCIDE en el primer caso y SECCION_NO_COINCIDE en el segundo.
3. **Una hoja truncada a 31 caracteres se coteja igual.** **Dado** un export correcto de la 410 cuya hoja termina cortada antes de «_f», como `gc_SINTETICO_20262_450002_410`, **Cuando** el profesor lo sube en la 410, **Entonces** la API responde 201 y la carga queda PUBLICADA con 11 / 11 / 0.
4. **Un archivo que no declara su sección no se carga en el corte 1.** **Dado** un export correcto cuya hoja se llama «Hoja1» y cuyo archivo se llama «notas.xlsx», **Cuando** el profesor lo sube en la 410 durante el corte 1, **Entonces** la API responde 422 con «El archivo no indica su sección. Sube el export de Blackboard sin cambiar el nombre de su hoja.» y `archivo_origen`, `carga` y `estudiante` no ganan filas (valor provisional de D-02; el corte 2 agrega la confirmación de US-21).
5. **Si la hoja no declara la sección, se coteja el nombre del archivo.** **Dado** un export correcto con la hoja «Hoja1» y el nombre `gc_SINTETICO_20262_450002_411_fullgc_2026-10-20.xlsx`, **Cuando** el profesor lo sube en la 410, **Entonces** la carga queda RECHAZADA con SECCION_NO_COINCIDE y RECHAZA_CARGA.
6. **El export de una sección del profesor no entra en otra de sus secciones de la misma asignatura.** **Dado** la 410 y la 412 de 450010 a cargo de `docente.varias@example.invalid`, **Cuando** sube `sintetico_20262_450010_410.xlsx` en la 412, **Entonces** la API responde 201 con «El archivo corresponde a la sección 410 y usted eligió la 412. No se publicó.» (propuesta), y la carga queda RECHAZADA en la 412 con SECCION_NO_COINCIDE y RECHAZA_CARGA. Ninguna de las dos secciones gana una carga PUBLICADA, y `estudiante` no gana los códigos 99000034 a 99000044.
7. **El mismo número de sección en otra asignatura no basta para cargar el export.** **Dado** la 412 de 450002 y la 412 de 450010 a cargo del mismo profesor, **Cuando** sube `sintetico_20262_450010_412.xlsx` en la 412 de 450002, **Entonces** la carga queda RECHAZADA con SECCION_NO_COINCIDE, RECHAZA_CARGA y el mensaje «El archivo corresponde a la asignatura 450010 y usted eligió la 450002. No se publicó.» (propuesta). `estudiante` no gana los códigos 99000045 a 99000055.

---

### US-14: Descartar nombres y valores leídos (Priority: P1)

Como sistema, quiero quedarme solo con el código de 8 dígitos y las celdas de los PI del plan, y descartar nombres, último acceso, disponibilidad, actividades y valores leídos, para que la base y los registros no guarden datos personales.

**Why this priority**: la regla «nunca se guardan ni se muestran nombres de estudiantes, ni el valor leído de una celda, ni la ruta local del archivo» no se puede romper, y Q04 solo vigila nombres de columna, no contenido.

**Independent Test**: tras subir `export_inventado_410_con_error.xlsx`, Q04 devuelve 0 filas y la búsqueda de cada nombre inventado del archivo en las columnas de texto de `abet` y `acceso` devuelve 0 coincidencias.

**Base**: consulta Q04; `estudiante` (`ck_estudiante_codigo`); `rechazo_fila` (sin columna de valor); `archivo_origen` (`ck_archivo_origen_nombre`); `carga_columna` (solo PI reconocidos, `fk_carga_columna_plan`); registro de la aplicación del Back y de Vercel.
**Pantalla**: P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/carga.feature`):

1. **Los nombres no llegan a ninguna tabla.** **Dado** el export con error, cuyas columnas Last Name y First Name traen nombres inventados, **Cuando** su profesor lo sube en la 410, **Entonces** Q04 devuelve 0 filas, la búsqueda de cada nombre en las columnas de texto de `abet` y `acceso` devuelve 0 coincidencias y `estudiante` solo tiene códigos que cumplen `ck_estudiante_codigo`.
2. **El rechazo dice motivo, fila y columna, nunca el valor.** **Dado** el mismo envío, **Cuando** termina la carga, **Entonces** el rechazo de la respuesta trae el mensaje «Fila 3, PI 5.2, nivel fuera de la escala 1 a 4. La fila completa queda fuera, también de 5.1 y 5.3.» sin un campo `valor` ni `valor_leido`, la fila de `rechazo_fila` solo tiene `rechazo_id`, `carga_id`, `fila_origen`, `carga_columna_id`, `motivo`, `efecto` y `pi_id`, y el registro de la aplicación no trae el valor leído (el registro, prueba unitaria de app/rutas/cargas.py, fuera del .feature).
3. **Las columnas que no son PI del plan se descartan.** **Dado** el mismo envío, **Cuando** termina la carga, **Entonces** `carga_columna` solo tiene 5.1, 5.2 y 5.3 y ninguna tabla guarda Last Access, Availability ni las columnas «Actividad 01» a «Actividad 18».
4. **El nombre del archivo se guarda sin ruta.** **Dado** un navegador que envía «C:\Users\docente\Descargas\export_inventado_410_con_error.xlsx», **Cuando** se registra el archivo, **Entonces** `nombre_archivo` es `export_inventado_410_con_error.xlsx`, y un intento de guardar un nombre con «/» o «\» lo rechaza `ck_archivo_origen_nombre`.
5. **Los bytes del export no se conservan.** **Dado** una carga terminada, **Cuando** se revisan Neon y el almacenamiento de Vercel, **Entonces** ninguna tabla de `abet` ni de `acceso` tiene una columna de tipo bytea, no hay copia del archivo y solo queda su huella (propuesta, configurable).

---

### US-15: Descargar el R-17 generado desde la base (Priority: P1)

Como profesor (y el coordinador para cualquier sección de la carrera), quiero descargar el R-17 de mi sección con los porcentajes calculados en la base para tener la evidencia de que mi export está en la base con esos datos.

**Why this priority**: es el resultado (4) y la frase literal del pedido, «generar el excel (R17) para el profesor como evidencia».

**Independent Test**: con la carga del export con error publicada, `GET /api/cargas/{carga_id}/r17.xlsx` entrega `R017_450002_410_2026-2_PROVISIONAL.xlsx` con 60,0 / 60,0 / 70,0 y 30 filas de estudiantes.

**Base**: vista `v_r17_por_pi` (`provisional`, `conjunto_reglas`, `nivel_esperado`, `n_nivel_1` a `n_nivel_4`, `pct_logro_sobre_calificados`, `pct_logro_sobre_total_con_sin_evidencia`, `pct_logro_segun_regla`, `meta_logro_pct`, `n_esperado_o_superior`, `n_total` y `n_sin_evidencia`; solo cargas en estado PUBLICADA). La vista no expone `n_calificados`, así que `r17.py` calcula el denominador de calificados como `n_total - n_sin_evidencia`. Además, vista `v_tabla_maestra_pi`; `carga`, `archivo_origen`, `conjunto_reglas`, `parametro_valor` (META_LOGRO, NIVEL_ESPERADO, TRATO_SIN_EVIDENCIA); `acceso.usuario_autorizado` y `acceso.docente_seccion` (V1_09) para el permiso; plantilla `plantillas/R017_ambiental_general.xlsx` (copia vaciada de «Plantilla Base - Final.xlsx», hoja «Cursos de Carrera», sin `#REF!`); `abet_carga/r17.py` con openpyxl y Pillow.
**Pantalla**: P4 Resultado de la carga (botón «Descargar R-17»).
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/r17_constancia.feature`):

1. **R-17 del export correcto.** **Dado** la carga PUBLICADA de `sintetico_20262_450002_410.xlsx`, **Cuando** el profesor descarga el R-17 de esa carga, **Entonces** recibe `R017_450002_410_2026-2_PROVISIONAL.xlsx` con la cabecera «450002», «sección 410» y «2026-2», el bloque II con 63,6 % (7 de 11) en 5.1, 63,6 % (7 de 11) en 5.2 y 72,7 % (8 de 11) en 5.3 y meta 80 %, cada porcentaje igual a `pct_logro_sobre_calificados` de `v_r17_por_pi`, la tabla de estudiantes con 33 filas de 99000001 a 99000011, ninguna celda que empiece por «=» y los recuadros de causas, acciones y comentario vacíos y editables.
2. **R-17 del export con el 5 en la fila 3.** **Dado** la carga PUBLICADA de `export_inventado_410_con_error.xlsx`, **Cuando** el profesor lo descarga, **Entonces** el bloque II muestra 60,0 % (6 de 10), 60,0 % (6 de 10) y 70,0 % (7 de 10) y la tabla de estudiantes tiene 30 filas sin 99000002.
3. **Con reglas en borrador el R-17 sale provisional.** **Dado** la carga con R-2026-BORRADOR, **Cuando** se descarga el R-17, **Entonces** `v_r17_por_pi` da `provisional` verdadero y `pct_logro_segun_regla` nulo, la hoja «Cursos de Carrera» muestra bajo el título la franja «R-17 PROVISIONAL. Las reglas de la carrera (conjunto R-2026-BORRADOR) aún no están aprobadas. No usar como evidencia oficial.» (propuesta), que contiene «PROVISIONAL» y «R-2026-BORRADOR», el título de las propiedades del libro contiene «PROVISIONAL» y el nombre termina en «_PROVISIONAL.xlsx».
4. **Quién descarga (esquema).** **Dado** la carga PUBLICADA de la 410, **Cuando** la pide el profesor de la 410, el coordinador sin secciones asignadas o el profesor de la 411, **Entonces** los dos primeros reciben el mismo archivo con las mismas cifras y el tercero recibe 403 sin archivo.
5. **Una carga no publicada no tiene R-17.** **Dado** la única carga de la 410 en RECHAZADA, **Cuando** el profesor pide el R-17 de esa carga, **Entonces** la API responde 409 con «La carga no está publicada y no tiene R-17.» sin archivo y `v_r17_por_pi` no devuelve filas de ella.
6. **El R-17 no lleva nombres de personas.** **Dado** la carga del export con error, **Cuando** se descarga el R-17, **Entonces** las propiedades autor y último autor están vacías o dicen «ABET_SIS_MED», la tabla de estudiantes solo muestra SO, PI, código y calificación y ninguna hoja contiene nombres.
7. **El logotipo de la plantilla se conserva.** **Dado** la plantilla vaciada con su logotipo, **Cuando** se genera el R-17, **Entonces** el libro conserva la imagen, y la prueba falla si Pillow no está instalado (prueba unitaria de r17.py, fuera del .feature).
8. **Con reglas aprobadas el R-17 sale sin franja.** **Dado** solo en la base de pruebas el conjunto inventado R-PRUEBA-APROBADO en APROBADO con META_LOGRO 0,70, NIVEL_ESPERADO 2, CORTE_ROJO 0,50, TRATO_SIN_EVIDENCIA «SE_EXCLUYE_DEL_DENOMINADOR» y la conversión de sus 4 niveles, como el caso A03 de `pruebas.sql`, la API con `CONJUNTO_REGLAS=R-PRUEBA-APROBADO` y la carga PUBLICADA de `sintetico_20262_450002_410.xlsx`, **Cuando** el profesor descarga el R-17, **Entonces** `v_r17_por_pi` da `provisional` falso, `meta_logro_pct` 70,0 y `pct_logro_segun_regla` 90,9 en los 3 PI, el bloque II muestra 90,9 % (10 de 11) en 5.1, 5.2 y 5.3 con meta 70 %, ninguna hoja lleva la franja y el archivo se llama `R017_450002_410_2026-2.xlsx`. La cifra sale de los niveles de `datos_sinteticos.sql`, donde cada PI tiene un solo estudiante en el nivel 1. En Neon ningún conjunto se aprueba dentro del MVP.

---

### US-16: Recibir la constancia de la carga (Priority: P1)

Como profesor, quiero que el R-17 traiga una hoja «Constancia» y que la API me devuelva la misma constancia para demostrar qué archivo subo, cuándo, quién lo sube y qué queda en la base.

**Why this priority**: es la parte más literal del pedido, «Y así mismo de que se pudo subir a la base de datos», y une el R-17 con un archivo y una carga concretos.

**Independent Test**: la hoja «Constancia» del R-17 del export correcto muestra «11 / 11 / 11 / 0», la huella completa igual a `archivo_origen.sha256` y 1 aviso en 5.3.

**Base**: `archivo_origen` (`sha256`, `nombre_archivo`, `hoja`, `filas_de_datos`, `recibido_en`); `carga` (`carga_id`, `estado`, `programa_version`, `filas_leidas`, `filas_aceptadas`, `filas_rechazadas`, `iniciada_en`, `terminada_en`, `conjunto_reglas_id`, `reemplaza_carga_id`, `subida_por` (V1_09)); `rechazo_fila`; `acceso.usuario_autorizado` (V1_09, correo de quien sube la carga, valor provisional de D-12); `abet_carga/constancia.py`; rutas `GET /api/cargas/{carga_id}` y `GET /api/cargas/{carga_id}/r17.xlsx`.
**Pantalla**: P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/r17_constancia.feature`):

1. **Constancia del export correcto.** **Dado** la carga PUBLICADA de `sintetico_20262_450002_410.xlsx`, **Cuando** el profesor abre la hoja «Constancia» del R-17, **Entonces** la hoja muestra el `carga_id` de las filas de `v_r17_por_pi`, el archivo y la hoja `gc_SINTETICO_20262_450002_410_f`, «11 / 11 / 11 / 0», la huella SHA-256 completa, el estado PUBLICADA, la versión del programa, «R-2026-BORRADOR (BORRADOR)», 1 aviso «PUNTAJE_MAXIMO_DISTINTO en el PI 5.3», «Subido por docente410@example.invalid», las horas de inicio y fin en hora de Lima y la frase fija «Los números de este R-17 los calcula el sistema desde la carga registrada en la base, no desde fórmulas.».
2. **Constancia del export con el 5 en la fila 3.** **Dado** la carga PUBLICADA de `export_inventado_410_con_error.xlsx`, **Cuando** el profesor abre la hoja, **Entonces** muestra «11 / 11 / 10 / 1», el rechazo «Fila 3, PI 5.2, NIVEL_FUERA_DE_ESCALA, RECHAZA_FILA», el aviso de 5.3 y no muestra el valor leído.
3. **La hora de fin es posterior a la de inicio.** **Dado** cualquier carga terminada, **Cuando** se lee la constancia, **Entonces** `terminada_en`, que el programa fija con `clock_timestamp()` y no con `now()`, es mayor que `iniciada_en`.
4. **La API devuelve la misma constancia.** **Dado** la carga del export con error, **Cuando** el profesor llama a `GET /api/cargas/{carga_id}`, **Entonces** el JSON trae los mismos conteos, huella, estado, conjunto, avisos y rechazos que la hoja.
5. **Una carga rechazada tiene constancia y no R-17.** **Dado** una carga RECHAZADA por PI_DEL_PLAN_AUSENTE, **Cuando** el profesor pide su constancia, **Entonces** `GET /api/cargas/{carga_id}` devuelve el estado RECHAZADA con su motivo y `subida_por`, y la ruta del R-17 responde como en US-15, escenario 5.
6. **La constancia de otra sección no se entrega.** **Dado** la carga de la 410, **Cuando** el profesor de la 411 pide `GET /api/cargas/{carga_id}`, **Entonces** recibe 403.

---

### US-17: Desplegar el piloto en Vercel con Neon y probarlo de punta a punta (Priority: P1)

Como administrador técnico, quiero desplegar el Back y el Front en Vercel conectados a Neon y correr una prueba de humo desde la URL del piloto para demostrar que los cuatro resultados del MVP se cumplen juntos en la nube.

**Why this priority**: el resultado (2) exige una aplicación en línea, y ninguna otra historia la despliega ni prueba los cuatro resultados juntos.

**Independent Test**: la prueba de humo con Playwright para Python contra la URL de Preview desde `develop` ingresa, sube el export con el 5 en la fila 3, ve 11 / 10 / 1 y descarga el R-17 con 60,0 / 60,0 / 70,0.

**Base**: Neon con V1_01 a V1_09, el rol `abet_app`, la guardia y los datos inventados; consultas Q01 a Q14; variables del Back que pega Jefferson en Vercel (`DATABASE_URL` con pooler y usuario `abet_app`, `SESION_SECRETO`, `PERIODO_VIGENTE`, `CONJUNTO_REGLAS`, `GUARDIA_DATOS_INVENTADOS=1`); psycopg 3 con `prepare_threshold=None`; proyectos `abet-ulima-back` y `abet-ulima-front` en el equipo `jeffangeloss-projects`, región `gru1` en `vercel.json`; `vercel.json` del Front con la reescritura de rutas de `/api/:path*` hacia el Back; Production desde `main` y Preview desde `develop` con otra rama de Neon.
**Pantalla**: sin pantalla propia; la prueba de humo recorre P1 a P4.
**Corte**: 1.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/despliegue.feature`):

1. **Prueba de humo de punta a punta en la nube.** **Dado** el despliegue Preview desde `develop` y la 410 sin cargas en su rama de Neon, **Cuando** Playwright ingresa como `docente410@example.invalid`, sube `export_inventado_410_con_error.xlsx` y descarga el R-17, **Entonces** P4 muestra «11 filas leídas, 10 aceptadas y 1 rechazada», el archivo se llama `R017_450002_410_2026-2_PROVISIONAL.xlsx`, el R-17 trae 60,0 / 60,0 / 70,0 con 30 filas y Q01 a Q14 devuelven 0 filas en esa rama de Neon. La prueba de humo no corre en Production (J-09).
2. **Todo viaja por el mismo origen.** **Dado** el Front en su dominio de Vercel, **Cuando** el navegador llama a `/api/sesion`, **Entonces** la petición pasa por la reescritura de rutas, la respuesta no trae la cabecera Access-Control-Allow-Origin, la cookie `abet_sesion` es de primera parte y el Back no necesita CORS.
3. **Las funciones corren en São Paulo.** **Dado** los dos proyectos, **Cuando** se lee la configuración desplegada, **Entonces** la región de las funciones es `gru1` y no `iad1`.
4. **Preview no escribe en la base de Production.** **Dado** un despliegue Preview desde `develop`, **Cuando** se lee su `DATABASE_URL` de alcance Preview, **Entonces** apunta a otra rama de Neon.
5. **Los secretos del Back no quedan en ningún repositorio (esquema con `DATABASE_URL` y `SESION_SECRETO`).** **Dado** el valor del secreto que Jefferson pega en Vercel, leído solo en la terminal de quien revisa, **Cuando** se busca ese valor en los archivos de `git ls-files` y en `git log -p --all` de `ABET-ULIMA-Back` y de `ABET-ULIMA-Front`, **Entonces** el valor no aparece en ningún archivo ni en ningún commit y `bash scripts/preflight.sh` termina sin fallas en los dos repositorios.
6. **El entrenamiento de inteligencia artificial está desactivado.** **Dado** el equipo `jeffangeloss-projects`, **Cuando** se revisa su configuración, **Entonces** la opción de uso de contenido para entrenamiento figura desactivada (comprobación manual de Jefferson).
7. **La cookie de sesión es de primera parte y nunca pasa por el almacenamiento del navegador.** **Dado** `docente410@example.invalid` con una contraseña de prueba asignada en la base del piloto, **Cuando** ingresa con Playwright en P1 de la URL de Production del Front, **Entonces** la cookie `abet_sesion` llega desde el origen del Front, sin atributo Domain y con HttpOnly, Secure y SameSite=Lax, la siguiente petición del Front a `/api/sesion` lleva la cookie y responde 200 con el rol PROFESOR, `localStorage` y `sessionStorage` no guardan ningún valor con el token de la sesión y `document.cookie` no muestra `abet_sesion`.
8. **Las variables del Back están en Vercel y no en el repositorio (esquema con `DATABASE_URL`, `SESION_SECRETO`, `PERIODO_VIGENTE`, `CONJUNTO_REGLAS` y `GUARDIA_DATOS_INVENTADOS`).** **Dado** el proyecto `abet-ulima-back`, **Cuando** se listan sus variables con `vercel env ls production`, **Entonces** la lista incluye esa variable y `.env.example` del Back la nombra sin valor.
9. **La API se conecta a Neon por el pooler con el rol abet_app.** **Dado** `DATABASE_URL` de Production con un host que contiene «-pooler» y el usuario `abet_app`, **Cuando** la prueba envía 20 peticiones seguidas a `GET /api/secciones?periodo=2026-2` con la sesión de `coordinacion@example.invalid`, **Entonces** las 20 respuestas son 200 con las secciones 410 y 411, los registros de la función no muestran ningún error «prepared statement» de psycopg y `pg_stat_activity` muestra las conexiones de la API con `usename` igual a `abet_app`.
10. **Production sale solo de main.** **Dado** los dos proyectos de Vercel, **Cuando** se revisa su configuración de Git, **Entonces** la rama de Production de cada uno es `main`, y empujar un cambio a `develop` crea un despliegue de Preview sin cambiar el de Production.
11. **La guardia de datos inventados está encendida en el piloto.** **Dado** `docente410@example.invalid` con sesión en la URL de Production del Front, los conteos de `archivo_origen`, `carga` y `estudiante` anotados y un export de 11 filas con 10000004 en Username de la fila 4, que la prueba arma en memoria porque `tests/datos_inventados/` solo admite códigos que empiezan con 99, **Cuando** lo sube en la 410, **Entonces** la API responde 422 con «El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada.», los tres conteos no cambian, `pg_constraint` tiene `ck_estudiante_codigo_inventado` en `abet.estudiante` y el registro de la aplicación en Vercel guarda de ese rechazo solo la huella y la hora, sin 10000004 ni ningún valor de Last Name o First Name del export.

---

### US-18: Reemplazar la carga publicada de una sección (Priority: P2)

Como profesor (en mi sección) o coordinador (en cualquiera de la carrera), quiero reemplazar la carga publicada por un export corregido para que el R-17 refleje las notas correctas sin borrar la carga anterior.

**Base**: `carga` (`reemplaza_carga_id`, `uq_carga_reemplaza`, `ck_carga_reemplaza`, `fk_carga_reemplaza` y los índices únicos parciales `uq_carga_publicada_por_seccion` y `uq_carga_archivo_util`); `archivo_origen`; `medicion`; `rechazo_fila`; vista `v_r17_por_pi`; consultas Q06, Q07, Q10 y Q14; `acceso.docente_seccion` (V1_09); ruta `POST /api/secciones/{seccion_id}/cargas?reemplaza={carga_id}`; rol `abet_app` sin DELETE y sin UPDATE de `reemplaza_carga_id`.
**Pantalla**: P5 Cargas (acción «Reemplazar carga») y P3 Subir export.
**Corte**: 2.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/reemplazo_y_cargas.feature`):

1. **El export corregido reemplaza a la carga con el error.** **Dado** la carga A PUBLICADA de `export_inventado_410_con_error.xlsx`, **Cuando** el profesor de la 410 la reemplaza con `sintetico_20262_450002_410.xlsx`, **Entonces** A queda REEMPLAZADA con sus 30 mediciones y sus 2 filas de `rechazo_fila`, B queda PUBLICADA con 11 aceptadas, 33 mediciones y `reemplaza_carga_id` igual a A, `v_r17_por_pi` solo ve B con 63,6 / 63,6 / 72,7 y Q06, Q07, Q10 y Q14 devuelven 0 filas.
2. **Si el reemplazo falla, la carga anterior sigue publicada.** **Dado** la carga A publicada, **Cuando** el profesor la reemplaza con un archivo .xlsx dañado que no abre como zip, **Entonces** recibe 422 con «No se pudo abrir el archivo. La carga publicada no cambió.» y A sigue PUBLICADA.
3. **Un reemplazo que rechaza todas las filas no quita la vigente.** **Dado** la carga A publicada, **Cuando** el profesor la reemplaza con un export que trae un 5 en la 5.2 de las 11 filas, **Entonces** la carga nueva queda RECHAZADA con 11 / 0 / 11 y `reemplaza_carga_id` nulo desde el INSERT, sin UPDATE de esa columna, y A sigue PUBLICADA.
4. **Un reemplazo fallido no bloquea el siguiente.** **Dado** A publicada y una carga RECHAZADA de un reemplazo fallido, **Cuando** el profesor reemplaza A con `sintetico_20262_450002_410.xlsx`, **Entonces** la nueva queda PUBLICADA con `reemplaza_carga_id` igual a A, la base no la rechaza por `uq_carga_reemplaza` y Q07 y Q14 dan 0 filas.
5. **La base impide dos cargas publicadas en la misma sección.** **Dado** un defecto que publica B sin marcar antes A como REEMPLAZADA, **Cuando** ejecuta el UPDATE que pasa B a PUBLICADA, **Entonces** la base lo rechaza en esa misma sentencia por el índice único parcial `uq_carga_publicada_por_seccion`, la transacción se deshace y A sigue PUBLICADA.
6. **El profesor no reemplaza la carga de otra sección.** **Dado** la carga D PUBLICADA de la 411, subida por `docente411@example.invalid`, **Cuando** el profesor de la 410 intenta reemplazarla, **Entonces** la API responde 403, `carga` no gana filas y D sigue PUBLICADA, mientras el coordinador reemplaza en la 410 como en el escenario 1.
7. **Volver al export anterior reutiliza su archivo.** **Dado** B, que reemplaza a A, **Cuando** el coordinador reemplaza B con el archivo de A, **Entonces** la carga C queda PUBLICADA con el `archivo_id` de A y `reemplaza_carga_id` igual a B, y `archivo_origen` sigue con 1 fila para esa huella.
8. **El mismo archivo de la carga publicada no la reemplaza.** **Dado** A publicada con `sintetico_20262_450002_410.xlsx`, **Cuando** alguien intenta reemplazarla con ese mismo archivo, **Entonces** recibe 200 con la constancia de A y el aviso «Es el mismo archivo de la carga publicada. No se reemplazó.» (propuesta), y `carga` no gana filas.
9. **Una carga no reemplaza a otra de otra sección.** **Dado** la carga D PUBLICADA de la 411, **Cuando** el programa registra una carga de la 410 con `reemplaza_carga_id` igual a D, **Entonces** la base la rechaza por `fk_carga_reemplaza`.
10. **Subir sin pedir el reemplazo no pisa la carga publicada.** **Dado** A publicada en la 410, **Cuando** el profesor sube `sintetico_20262_450002_410.xlsx` sin el parámetro `reemplaza`, **Entonces** la API responde 409, `archivo_origen` y `carga` no ganan filas y P3 pregunta «La sección 410 ya tiene una carga publicada. ¿Desea reemplazarla?».
11. **No se reemplaza una carga que ya no es la vigente.** **Dado** B PUBLICADA, que reemplaza a A, **Cuando** el profesor pide el reemplazo de A, **Entonces** la API responde 409, `carga` no gana filas y B sigue PUBLICADA (propuesta).

---

### US-19: Ver las cargas a mi alcance (Priority: P2)

Como profesor (mis secciones) o coordinador (todas las de la carrera), quiero ver la lista de cargas con su estado, sus conteos y quién las sube para saber qué secciones ya tienen evidencia publicada, cuáles faltan y cuál carga está vigente.

**Base**: `carga` (`estado`, `filas_leidas`, `filas_aceptadas`, `filas_rechazadas`, `iniciada_en`, `terminada_en`, `reemplaza_carga_id`, `subida_por` (V1_09), `ck_carga_estado`); `archivo_origen` (`nombre_archivo`, `sha256`); `seccion`, `asignatura`, `periodo`; `rechazo_fila` (conteo por `motivo` y `efecto`); `acceso.usuario_autorizado` y `acceso.docente_seccion` (V1_09); rutas `GET /api/cargas?seccion_id=` y `GET /api/cargas/{carga_id}`.
**Pantalla**: P5 Cargas.
**Corte**: 2.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/reemplazo_y_cargas.feature`):

1. **El coordinador ve las cargas de todas las secciones.** **Dado** en la 410 la carga A RECHAZADA de `export_inventado_411.xlsx` con 0 / 0 / 0, la B REEMPLAZADA de `export_inventado_410_con_error.xlsx` con 11 / 10 / 1 y la C PUBLICADA de `sintetico_20262_450002_410.xlsx` con 11 / 11 / 0, subidas en ese orden por `docente410@example.invalid`, y en la 411 la carga D PUBLICADA del export inventado de la 411, subida después de C por `docente411@example.invalid`, **Cuando** el coordinador llama a `GET /api/cargas`, **Entonces** recibe las 4 cargas en el orden D, C, B y A, cada una con su sección, su estado, sus conteos, el nombre del archivo, los primeros 12 caracteres de la huella y el correo de quien la sube, A con el motivo SECCION_NO_COINCIDE, C con la indicación de que reemplaza a B y las horas con el desfase «-05:00».
2. **El profesor ve solo las de su sección.** **Dado** las mismas cargas, **Cuando** el profesor de la 410 llama a `GET /api/cargas`, **Entonces** recibe C, B y A sin la D ni ningún dato de la 411, y `GET /api/cargas?seccion_id={sección 411}` responde 403.
3. **Una carga reemplazada sigue visible con su sucesora.** **Dado** las mismas cargas de la 410, **Cuando** el profesor de la 410 pide `GET /api/cargas/{B}`, **Entonces** recibe 200 con B en REEMPLAZADA, 11 / 10 / 1, el rechazo de la fila 3 en 5.2 y la indicación de que C reemplaza a B, `GET /api/cargas/{B}/r17.xlsx` responde 409 sin archivo y P5 muestra C con la marca «Vigente, reemplaza a la carga B» (propuesta).
4. **La lista no expone lo que la base no guarda.** **Dado** cualquier carga, **Cuando** se abre P5, **Entonces** ninguna fila muestra la ruta local del archivo, valores leídos ni nombres de estudiantes, y la huella aparece con sus primeros 12 caracteres.
5. **El coordinador filtra por sección.** **Dado** las mismas cargas A, B, C y D, **Cuando** el coordinador llama a `GET /api/cargas?seccion_id={sección 411}`, **Entonces** recibe 200 con solo la carga D.

---

### US-20: Recibir el código de acceso en el correo institucional (Priority: P2)

Como usuario autorizado, quiero entrar con un código de 6 dígitos que llega a mi correo para no depender de una contraseña asignada cuando el piloto reciba al primer profesor externo.

**Base**: `acceso.codigo_acceso` con el hash del código, vigencia e intentos (V1_09); `acceso.usuario_autorizado`; `acceso.sesion`; ruta `POST /api/sesion/codigo`; proveedor de correo Resend con dominio propio y sus registros de autenticación del correo SPF, DKIM y DMARC (J-04); modo de prueba que captura los correos sin enviarlos (propuesta).
**Pantalla**: P1 Ingreso.
**Corte**: 2.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/acceso.feature`):

1. **El usuario autorizado entra con el código vigente.** **Dado** `docente410@example.invalid` activo y el modo de prueba del correo, **Cuando** pide un código y lo escribe dentro de 10 minutos, **Entonces** recibe la cookie `abet_sesion` como en US-05 y `codigo_acceso` guarda el hash del código y no el código.
2. **El correo no autorizado recibe la misma respuesta (esquema con un correo desconocido y uno inactivo).** **Dado** ese correo, **Cuando** pide un código, **Entonces** la API responde 202 con «Si el correo está autorizado, recibirá un código en unos minutos.», P1 lo muestra, no se envía correo y no se crea sesión.
3. **El código vencido o usado no abre sesión.** **Dado** un código de hace 11 minutos o uno ya usado, **Cuando** el usuario lo escribe, **Entonces** P1 muestra «El código venció. Pida uno nuevo.» o «El código ya se usó. Pida uno nuevo.» y no se crea sesión.
4. **Cinco intentos fallidos invalidan el código.** **Dado** un código vigente, **Cuando** el usuario escribe 5 veces otro código, **Entonces** el sexto intento con el correcto muestra «El código ya no es válido. Pida uno nuevo.».
5. **Los pedidos tienen límite.** **Dado** un correo, **Cuando** pide más de 3 códigos en 15 minutos (propuesta), **Entonces** el cuarto pedido recibe la misma respuesta de pantalla y no se envía correo.

---

### US-21: Confirmar la sección cuando el archivo no la declara (Priority: P3)

Como profesor, quiero que el sistema me pida confirmar la sección cuando el export no la declara en su hoja ni en su nombre para que un archivo renombrado no se cargue en la sección equivocada sin que yo lo decida.

**Base**: `archivo_origen` (`hoja`, `nombre_archivo`); `carga` (`subida_por` (V1_09), que dice quién confirma); `rechazo_fila` con el motivo `SECCION_SIN_DECLARAR` y efecto AVISO, que V1_09 agrega a `ck_rechazo_fila_motivo` junto con COLUMNA_CODIGO_AUSENTE, PI_REPETIDO y PERIODO_NO_COINCIDE; campo multipart `confirmar_seccion`; valor provisional de D-02.
**Pantalla**: P3 Subir export.
**Corte**: 2.

**Acceptance Scenarios** (`specs/001-mvp-carga-r17/aceptacion/carga.feature`):

1. **Un export sin sección declarada espera confirmación.** **Dado** un export correcto cuya hoja se llama «Hoja1» y cuyo archivo se llama «notas.xlsx», **Cuando** el profesor lo sube en la 410, **Entonces** la API responde 422 con «El archivo no indica su sección. ¿Confirma que es de la sección 410 de 450002 en 2026-2?» y `requiere_confirmacion` verdadero (propuesta), P3 muestra esa pregunta y `archivo_origen`, `carga` y `estudiante` no ganan filas.
2. **La confirmación queda registrada en la carga.** **Dado** el pedido de confirmación anterior, **Cuando** el profesor sube el mismo archivo con `confirmar_seccion=true`, **Entonces** la API responde 201, la carga queda PUBLICADA con 11 / 11 / 0 y 33 mediciones, `subida_por` es el profesor y `rechazo_fila` registra SECCION_SIN_DECLARAR con AVISO, `fila_origen` nulo y `carga_columna_id` nulo.
3. **La confirmación no pasa por encima de una sección declarada distinta.** **Dado** `export_inventado_411.xlsx`, cuya hoja declara la 411, **Cuando** el profesor lo sube en la 410 con `confirmar_seccion=true`, **Entonces** la carga queda RECHAZADA con SECCION_NO_COINCIDE y RECHAZA_CARGA.
4. **La confirmación no vale si nombra otra sección.** **Dado** el export «notas.xlsx» con la hoja «Hoja1», **Cuando** el profesor lo sube en la 410 con `confirmar_seccion` igual a «411», **Entonces** la API responde 422 con «La sección confirmada no es la sección elegida. No se guardó nada.» y `archivo_origen`, `carga` y `estudiante` no ganan filas, porque el campo solo admite «true».

### Edge Cases

- Toda respuesta de error de la API usa `{ "detail": "mensaje" }`. Sin sesión la API responde 401; con sesión y sin permiso sobre la sección o la carga, un 403 único con «La sección no está a su cargo.», y la respuesta no trae datos de esa sección.
- Un archivo de más de 1 MB recibe 422 antes de leerse, por debajo del tope de 4,5 MB por petición de Vercel.
- Ninguna carga queda EN_CURSO al terminar una petición, aunque la conexión con Neon se corte, porque la transacción se deshace entera.
- Los identificadores `GENERATED ALWAYS AS IDENTITY` se consumen aunque la transacción se deshaga, así que las pruebas capturan el `carga_id` devuelto y nunca suponen 1, 2 o 3.
- `now()` devuelve la hora de inicio de la transacción; el programa cierra cada carga con `clock_timestamp()` para que inicio y fin difieran.
- El export de la 411 usa los códigos 99000012 a 99000022, porque con los de la 410 Q08 vería al mismo estudiante en dos secciones del mismo curso.
- Student ID viene vacío en el export conocido; el código sale de Username, y una celda vacía de Username es CODIGO_VACIO.
- La hoja «Cursos de Carrera» tiene 142 filas para la tabla de estudiantes (de la 43 a la 184). Con 3 PI, una sección de más de 47 estudiantes no cabe, y el MVP responde 422 al pedir el R-17 con «La sección supera las filas de la plantilla del R-17.» (propuesta) en lugar de truncar la tabla.
- Un export abierto y guardado otra vez en Excel cambia sus bytes y cuenta como archivo distinto.
- El nombre de hoja de Blackboard tiene un máximo de 31 caracteres y puede venir truncado; el cotejo tolera el sufijo cortado.
- Con la guardia encendida, un Username mal formado como 9900001 detiene el archivo entero, así que CODIGO_INVALIDO solo se alcanza con la guardia apagada en la base desechable de `correr_pruebas.sh`.
- Dos subidas simultáneas en la misma sección dejan una sola carga PUBLICADA por el índice único parcial `uq_carga_publicada_por_seccion`; la otra recibe 409.
- Un archivo cuya huella ya está PUBLICADA en otra sección recibe 409 con «Este archivo ya está publicado en otra sección. No se cargó.» antes de escribir, porque el índice único parcial `uq_carga_archivo_util` lo impediría (caso R34 de `pruebas.sql`).
- Dos subdominios de `vercel.app` son sitios distintos para el navegador, así que la cookie solo viaja porque el Front reescribe las rutas `/api/:path*` hacia el Back.
- La guardia rechaza el archivo después de recibirlo, así que no evita que un archivo real llegue a la función de Vercel; P3 lleva el rótulo «Solo exports con códigos inventados (99000000 a 99999999)» mientras no exista un lector en el navegador.

## Requirements *(mandatory)*

- **FR-001** El esquema `abet` se aplica en Neon con Flyway desde el entorno `neon` con `cleanDisabled = true`, y `controles_neon.sql` corre Q01 a Q14 con `abet_respaldo` en solo lectura.
- **FR-002** El contenido de `bd/` pasa a `db/` de este repositorio con su historia (git subtree) después del primer `flyway migrate` en Neon y de fusionar `preparacion-neon`, y antes de escribir V1_09; después `ABET_ULIMA` se archiva.
- **FR-003** `V1_09__crear_acceso.sql` crea el esquema `acceso` con `usuario_autorizado`, `credencial`, `sesion`, `intento_fallido`, `docente_seccion` y `codigo_acceso`, las columnas `abet.carga.subida_por` y `abet.rechazo_fila.pi_id` y los motivos COLUMNA_CODIGO_AUSENTE, PI_REPETIDO, PERIODO_NO_COINCIDE y SECCION_SIN_DECLARAR, y `pruebas.sql` gana un caso que debe pasar y uno que no por cada restricción nueva.
- **FR-004** La API se conecta con el rol `abet_app` de `db/plataforma/neon/crear_rol_app.sql`, que no tiene DELETE ni TRUNCATE en `abet` y solo actualiza `estado`, `filas_leidas`, `filas_aceptadas`, `filas_rechazadas` y `terminada_en` de `carga`.
- **FR-005** `db/plataforma/neon/guardia_datos_inventados.sql` agrega `ck_estudiante_codigo_inventado` solo en Neon, y la API, con `GUARDIA_DATOS_INVENTADOS=1`, rechaza con 422 y sin escribir todo export con un código fuera de 99000000 a 99999999.
- **FR-006** `db/datos/periodo_2026_2_inventado.sql` siembra la vigencia AMB-2026 en 2026-2, las secciones 410 y 411 de 450002, el plan con 5.1, 5.2 y 5.3, un coordinador y dos profesores con correos `@example.invalid` y sus `docente_seccion`, y se puede repetir sin duplicar.
- **FR-007** La API toma el periodo vigente de `PERIODO_VIGENTE` y el conjunto de reglas de una carga nueva de `CONJUNTO_REGLAS`.
- **FR-008** El Back usa Python 3.12 con FastAPI bajo el prefijo `/api` y separa la biblioteca `abet_carga/` (`lector.py`, `validacion.py`, `carga.py`, `r17.py`, `constancia.py`), que no importa FastAPI, de la aplicación `app/` (`main.py`, `sesion.py`, `permisos.py`, `rutas/`).
- **FR-009** `POST /api/sesion` valida la contraseña contra un hash Argon2id, responde 401 con el mismo mensaje para un correo desconocido y una contraseña errada, limita los intentos y fija la cookie `abet_sesion` HttpOnly, Secure, SameSite=Lax y de 12 horas; `acceso.sesion` guarda solo el hash del token, y `GET` y `DELETE /api/sesion` devuelven y cierran la sesión.
- **FR-010** Cada ruta lee el rol y las secciones del usuario desde la base en cada petición. El profesor solo actúa sobre las secciones de `acceso.docente_seccion`. El coordinador ve todas las secciones de la carrera y descarga cualquier constancia o R-17, pero en el corte 1 no sube, porque solo sube el profesor asignado a la sección; en el corte 2 puede reemplazar la carga de cualquier sección (US-18).
- **FR-011** `GET /api/secciones?periodo=2026-2` devuelve las secciones al alcance del usuario con el campo `estado` de su carga y sus PI del plan.
- **FR-012** `POST /api/secciones/{seccion_id}/cargas` escribe archivo, carga, columnas, filas, estudiantes, mediciones y rechazos en una sola transacción de psycopg 3 con `prepare_threshold=None`, y responde 201 con la constancia; 200 con la constancia existente si el mismo archivo ya está publicado en esa misma sección; 409 con «Este archivo ya está publicado en otra sección. No se cargó.», antes de escribir y sin datos de esa sección, si la huella está publicada en otra sección, porque la base lo impediría con el índice único parcial `uq_carga_archivo_util`; 409 si la sección tiene otra carga publicada; 422 sin rastro para un archivo ilegible, de tipo no admitido, de más de 1 MB, con códigos que no son inventados o que no declara su sección en el corte 1; y 403 con «La sección no está a su cargo.» si el usuario no es el profesor asignado a la sección.
- **FR-013** El lector abre el export con openpyxl en solo lectura, sin pandas y con defusedxml activo, después de revisar el zip (tamaño descomprimido, sin `vbaProject.bin` ni `externalLinks`) y de comprobar el tipo por sus primeros bytes.
- **FR-014** La huella SHA-256 se calcula sobre los bytes recibidos antes de cualquier transformación y se guarda en minúscula; una huella con solo cargas en estado RECHAZADA o REEMPLAZADA reutiliza su `archivo_id`.
- **FR-015** La validación rechaza la fila completa con RECHAZA_FILA ante NIVEL_FUERA_DE_ESCALA, NIVEL_NO_NUMERICO, CODIGO_VACIO, CODIGO_INVALIDO o CODIGO_DUPLICADO (la segunda aparición), guarda la celda de PI vacía como SIN_EVIDENCIA y registra como AVISO PUNTAJE_MAXIMO_DISTINTO y COLUMNA_PI_FUERA_DEL_PLAN, con los valores provisionales de D-01, D-03, D-04 y D-06.
- **FR-016** La validación rechaza la carga entera con RECHAZA_CARGA ante ARCHIVO_SIN_FILAS, PI_DEL_PLAN_AUSENTE, COLUMNA_CODIGO_AUSENTE, PI_REPETIDO, SECCION_NO_COINCIDE y PERIODO_NO_COINCIDE, con `filas_leidas` 0, una sola fila de `rechazo_fila` y sin avisos ni columnas.
- **FR-017** La carga se publica sola cuando termina con al menos una fila aceptada, y queda RECHAZADA si no acepta ninguna.
- **FR-018** Ni la base, ni los registros, ni las respuestas, ni el R-17 guardan o muestran nombres de estudiantes, el valor leído de una celda o la ruta local del archivo, y el MVP no conserva los bytes del export después de la transacción.
- **FR-019** El R-17 sale de `v_r17_por_pi`, `v_tabla_maestra_pi` y las tablas, nunca de recalcular el archivo, y se genera con openpyxl y Pillow sobre `plantillas/R017_ambiental_general.xlsx`, con valores y sin fórmulas, filas fijas, franja PROVISIONAL y sufijo `_PROVISIONAL` si y solo si `v_r17_por_pi.provisional` es verdadero (conjunto no APROBADO o sin NIVEL_ESPERADO, META_LOGRO o TRATO_SIN_EVIDENCIA DEFINIDOS), los dos porcentajes de D-05, propiedades sin personas, con autor «ABET_SIS_MED» o vacías, y el nombre `R017_<asignatura>_<sección>_<periodo>_PROVISIONAL.xlsx`. El denominador de calificados es `n_total - n_sin_evidencia`, que calcula `r17.py`, porque la vista no expone `n_calificados`.
- **FR-020** `GET /api/cargas/{carga_id}/r17.xlsx` entrega el R-17 solo de una carga en estado PUBLICADA, con la hoja «Constancia» al final del libro, y responde 409 con «La carga no está publicada y no tiene R-17.» para las demás.
- **FR-021** La hoja «Constancia» y `GET /api/cargas/{carga_id}` muestran archivo, hoja, filas de datos, leídas, aceptadas y rechazadas, huella completa, estado, versión del programa, conjunto de reglas con su estado, avisos y rechazos por motivo y fila, el correo de quien sube la carga y las horas de inicio y fin en hora de Lima, y la carga se cierra con `clock_timestamp()`.
- **FR-022** El Front usa React con Vite, TypeScript y Tailwind, con las pantallas P1 a P4 en el corte 1 y P5 en el corte 2, y no muestra nada que ninguna historia pida.
- **FR-023** `src/servicios/api.ts` es la única puerta HTTP del Front, la sesión viaja solo en la cookie y nunca en `localStorage`, y `vercel.json` del Front reescribe `/api/:path*` hacia la URL del Back.
- **FR-024** El Back y el Front se despliegan como dos proyectos de Vercel Hobby (`abet-ulima-back` y `abet-ulima-front`) en `gru1`, con Production desde `main` y Preview desde `develop` contra otra rama de Neon, y las variables del Back las pega Jefferson en Vercel, nunca un agente.
- **FR-025** El reemplazo (corte 2) marca la carga anterior REEMPLAZADA y publica la nueva en una sola transacción, fija `reemplaza_carga_id` en el INSERT solo si la carga nueva se publica y nunca borra la anterior.
- **FR-026** `GET /api/cargas?seccion_id=` (corte 2) devuelve las cargas al alcance del usuario, de la más reciente a la más antigua.
- **FR-027** `POST /api/sesion/codigo` (corte 2) envía un código de 6 dígitos de un solo uso, vigente 10 minutos y con 5 intentos, guarda solo su hash y responde lo mismo exista o no el correo.
- **FR-028** Los escenarios de esta spec viven en un solo lugar, `specs/001-mvp-carga-r17/aceptacion/*.feature`, en español, y cada uno lleva `@US-NN` y `@corte1` o `@corte2`. Los pasos viven en `tests/aceptacion/pasos/` y leen los `.feature` desde esa carpeta con `scenarios()` de pytest-bdd y la ruta relativa; nadie los copia ni los mueve a `tests/`. El día 1 de la fase de contrato una prueba de 30 minutos confirma pytest-bdd 9 con el Gherkin en español, y si falla el respaldo es behave con `lang = es`.
- **FR-029** El Gherkin ejecutable cubre la carga (US-07 a US-14) y el R-17 con su constancia (US-15 y US-16); el resto de los escenarios se prueba con pytest como criterio escrito, y una prueba de humo con Playwright para Python cubre US-17.
- **FR-030** Los archivos de prueba viven en `tests/datos_inventados/` (el export correcto, el export con error, el de la 411 con los códigos 99000012 a 99000022 y los defectuosos de US-10 a US-13), y `pruebas.sql` gana los casos 60,0 / 60,0 / 70,0 y Q08 con la 410 y la 411 publicadas.
- **FR-031** La CI del Back aplica las migraciones con psql, como `correr_pruebas.sh`, sin acciones ni imágenes de Redgate, y corre las pruebas de la base, las de pytest y las de aceptación contra un PostgreSQL 16 desechable.
- **FR-032** Cada cambio de esta funcionalidad actualiza `MEMORIA.md` en el mismo commit y pasa `bash scripts/preflight.sh`.

## Success Criteria *(mandatory)*

- **SC-001** El 100 % de los escenarios de las historias del corte 1 tiene una prueba que pasa en la CI, y cada prueba cubre lo que debe pasar y lo que no.
- **SC-002** En Neon, Q01 a Q14 devuelven 0 filas después de la migración, después de la primera carga y después de la prueba de humo de US-17.
- **SC-003** Con `sintetico_20262_450002_410.xlsx`, la carga queda con 11 / 11 / 0, 33 mediciones y R-17 de 63,6 / 63,6 / 72,7, y con `export_inventado_410_con_error.xlsx`, con 11 / 10 / 1, 30 mediciones, 2 filas de `rechazo_fila` y R-17 de 60,0 / 60,0 / 70,0, sin ninguna diferencia, ni siquiera de una décima.
- **SC-004** Cada porcentaje del bloque II del R-17 es igual al `pct_logro_sobre_calificados` de `v_r17_por_pi` para su carga y su PI, y ninguna celda del libro empieza por «=».
- **SC-005** En los escenarios de fallo inyectado, de archivo ilegible y de guardia, el conteo de filas de `archivo_origen`, `carga`, `carga_fila`, `medicion` y `estudiante` es el mismo antes y después del envío.
- **SC-006** La búsqueda de los nombres inventados del export en las columnas de texto de `abet` y `acceso` y en todas las hojas del R-17 devuelve 0 coincidencias, Q04 devuelve 0 filas y el registro de la aplicación guarda de un rechazo por la guardia solo la huella y la hora.
- **SC-007** `abet.estudiante` en Neon tiene 0 códigos fuera de 99000000 a 99999999, y un INSERT directo de 10000004 falla por `ck_estudiante_codigo_inventado`.
- **SC-008** Con el rol `abet_app`, el 100 % de los intentos de DELETE, TRUNCATE y UPDATE fuera de las columnas permitidas responde «permission denied».
- **SC-009** Un profesor recibe 403 en el 100 % de las rutas de sección, carga, constancia y R-17 de una sección que no dicta, y el coordinador recibe 200 en el 100 % de las rutas de lectura (secciones, constancia y R-17) de las secciones de su carrera y 403 al subir un export en el corte 1.
- **SC-010** La huella de la hoja «Constancia» es igual a `shasum -a 256` del archivo que conserva el profesor en el 100 % de las cargas de prueba.
- **SC-011** La prueba de humo de US-17 termina en menos de 2 minutos contra la URL de Preview (propuesta) y deja la constancia 11 / 11 / 10 / 1.
- **SC-012** `bash scripts/preflight.sh` termina sin fallas en cada PR de esta feature, y ningún commit trae `Co-Authored-By` ni firmas de herramientas.

## Decisiones abiertas

De la carrera (D). Mientras no se decidan, el sistema aplica el valor provisional y el R-17 sale con la franja PROVISIONAL.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| D-01 | Trato de una celda de PI inválida | Rechazar la fila completa con RECHAZA_FILA | Coordinación de Ambiental |
| D-02 | Sección cuando el archivo no la declara | En el corte 1, 422 sin rastro con «El archivo no indica su sección. Sube el export de Blackboard sin cambiar el nombre de su hoja.» (US-13); en el corte 2, el profesor confirma con `confirmar_seccion=true` y la carga registra el AVISO SECCION_SIN_DECLARAR de V1_09 (US-21) | Coordinación de Ambiental |
| D-03 | Celdas con «-» o «NP» | NIVEL_NO_NUMERICO, que rechaza la fila | Coordinación de Ambiental |
| D-04 | Total Pts distinto de 4 | AVISO PUNTAJE_MAXIMO_DISTINTO y la carga sigue | Coordinación de Ambiental |
| D-05 | Trato del estudiante sin evidencia (fila H08 de la revisión de requisitos) | El R-17 muestra los dos porcentajes, sobre calificados y sobre el total | Coordinación de Ambiental |
| D-06 | Niveles -1 y 5 de la rúbrica frente a la escala 1 a 4 | NIVEL_FUERA_DE_ESCALA | Coordinación de Ambiental |
| D-07 | Un archivo por sección o uno por SO (fila H51 de la revisión de requisitos) | Un archivo por sección con todos los PI de su plan (propuesta) | Coordinación de Ambiental |
| D-08 | Plantilla oficial del R-17 | Copia vaciada de «Plantilla Base - Final.xlsx», hoja «Cursos de Carrera», llenada celda por celda | Coordinación de Ambiental y Oficina de Calidad |
| D-09 | Plan de medición de 2026-2 | 450002 mide 5.1, 5.2 y 5.3 con datos inventados | Coordinación de Ambiental |
| D-10 | Autorización de datos reales (Ley 29733 y DS 016-2024-JUS) | Solo datos inventados, con la guardia doble encendida | Universidad de Lima |
| D-11 | Quién reemplaza una carga publicada y hasta cuándo | En el corte 2, el profesor en su sección y el coordinador en cualquiera, sin fecha de cierre en el MVP; en el corte 1 solo sube el profesor asignado y nadie reemplaza | Coordinación de Ambiental |
| D-12 | Nombre del profesor en el R-17 y firma frente a validación en el sistema | Sin nombre del profesor; la constancia muestra el correo de quien sube la carga | Coordinación de Ambiental y Oficina de Calidad |
| D-13 | Usuarios del piloto | Un coordinador y dos profesores de prueba con correos `@example.invalid` | Coordinación de Ambiental |

De Jefferson (J).

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| J-01 | Lenguaje del Back | Python 3.12 con FastAPI (recomendado) frente a TypeScript con Hono | Jefferson |
| J-02 | Uno o dos roles de aplicación en la base | Un solo rol `abet_app` | Jefferson |
| J-03 | Identidad de la semana 1 | Contraseña asignada (recomendado); el código por correo llega en el corte 2 | Jefferson |
| J-04 | Dominio propio y proveedor de correo | Resend en el piloto y Amazon SES en la región sa-east-1 de AWS para datos reales; el dominio se compra el primer día para que su registro en el DNS se propague antes del corte 2 | Jefferson |
| J-05 | Organización de SonarQube Cloud | Una organización aparte de IQBF (propuesta) | Jefferson |
| J-06 | Traslado de `bd/` al Back y archivo de `ABET_ULIMA` | Después del primer `flyway migrate` y antes de V1_09, con git subtree | Jefferson |
| J-07 | Plan de Vercel para el piloto | Vercel Hobby, con la consulta a soporte por la cláusula de uso no comercial | Jefferson |
| J-08 | Controles de la CI | `secretos` como verificación (check) requerida, acciones fijadas por SHA y alertas de Dependabot (propuesta, los tres) | Jefferson |
| J-09 | La prueba de humo corre en la CI o contra la vista previa | Contra la vista previa (Preview) de `develop` antes de pasar a `main`; la prueba de humo no corre en Production | Jefferson |

## Fuera de alcance

Estos temas quedan para después del MVP, y cada uno abre su propia spec cuando se apruebe. Los nombres de tablas, columnas y motivos de esta lista no existen en V1_01 a V1_09 y son (propuesta) para specs futuras.

- Verificar un export o un R-17 contra la base desde una pantalla del coordinador, con la huella calculada en el navegador y la tabla `r17_emitido` (candidata C-19b).
- Cerrar las cargas del periodo en una fecha, con `periodo.fecha_cierre_cargas` (candidata C-22b, depende de D-11).
- Aprobar un conjunto de reglas de la carrera (candidata C-25a) y reprocesar las cargas publicadas con él a partir de `carga_fila` y `medicion` (candidata C-25b), con el R-17 sin franja en Neon.
- Detectar a un estudiante medido en dos secciones del mismo curso (Q08) como regla de la carga.
- Pantallas de administración para coordinadores (periodo, plan, usuarios y secciones, auditoría de altas) en lugar de scripts.
- Inicio de sesión con cuenta Microsoft de la universidad.
- Power BI leyendo Neon.
- R-18 y la hoja «Cursos Capstone» del R-17, que necesita `asignatura.tipo_curso`.
- Los motivos STUDENT_ID_DISTINTO y PI_TIPO_NO_SCORE.
- Datos reales de estudiantes, que exigen D-10 y pasar primero a Cloud Run en southamerica-east1 y después a Vercel Pro con la autorización de la universidad.
