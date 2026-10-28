# Tasks: Del export de Blackboard al R-17 desde la base

**Input**: spec.md, plan.md · **Estado al 2026-10-28**: fase 0 hecha; las fases 1 a 7 esperan la aprobación de la spec

Cada tarea lleva al comienzo el repositorio o el lugar donde ocurre. `[Back]` es ABET-ULIMA-Back, `[Front]` es ABET-ULIMA-Front, `[Neon]` es la base en la nube y `[Jefferson]` marca lo que solo puede hacer él, porque exige su cuenta, su pago o sus credenciales. Ninguna credencial pasa por un agente. Al final, cada tarea lleva las historias que habilita o audita, y un rango como `[US-05..US-16]` incluye las historias intermedias.

## Phase 0: Descubrimiento

- [x] T001 [Back] Leer la base de `jeffangeloss/ABET_ULIMA` (V1_01 a V1_08, `R__vista_r17_por_pi.sql`, `R__vista_tabla_maestra_pi.sql`, `pruebas/pruebas.sql` y `pruebas/datos_sinteticos.sql`), el export `export_inventado_410_con_error.xlsx` y la plantilla del R-17 de Ambiental [US-01..US-21]
- [x] T002 [Back] Escribir 25 historias candidatas con Gherkin en español, auditarlas con las lentes de necesidad, tamaño y verificabilidad y con la crítica de arquitectura, y dejar el resultado en `specs/001-mvp-carga-r17/revision-historias.md` [US-01..US-21]
- [x] T003 [Back] Redactar `specs/001-mvp-carga-r17/spec.md`, `plan.md`, `tasks.md`, `.specify/memory/constitution.md` y `specs/README.md` en la rama `docs/plan-mvp` [US-01..US-21]
- [ ] T004 [Jefferson] Revisar y fusionar la solicitud de integración (pull request, PR) de `docs/plan-mvp` a `develop`, que aprueba la spec, y ratificar la constitución con su fecha [US-01..US-21]
- [ ] T005 [Jefferson] Confirmar J-01 (Python con FastAPI), J-02 (un solo rol de aplicación), J-03 (contraseña asignada en el corte 1) y J-07 (Vercel Hobby para el piloto) [US-02] [US-05..US-17]
- [ ] T009 [Back] Auditar la fase (cada historia de la spec con su traza en `revision-historias.md`) y registrarla en `MEMORIA.md` de Back y Front [US-01..US-21]

## Phase 1: Contrato

- [ ] T010 [Back] Probar durante 30 minutos pytest-bdd 9 con un paso de `tests/aceptacion/pasos/` que lee con `scenarios()` y la ruta relativa `specs/001-mvp-carga-r17/aceptacion/carga.feature` (`# language: es`, Característica, Antecedentes, Esquema del escenario y Ejemplos) y, si no lo lee, behave con `lang = es` en `behave.ini` [US-07..US-14]
- [ ] T011 [Back] Escribir `specs/features/carga-export/carga-export.spec.md` con `BR-CARGA-NN` para la transacción, la huella, la guardia, el rechazo de filas (D-01, D-03, D-04 y D-06), la estructura, la sección, el periodo y el descarte de nombres [US-07] [US-08] [US-09] [US-10] [US-11] [US-12] [US-13] [US-14]
- [ ] T012 [Back] Escribir `specs/features/r17/r17.spec.md` con `BR-R17-NN` para `v_r17_por_pi`, la franja PROVISIONAL, el nombre `R017_450002_410_2026-2_PROVISIONAL.xlsx`, las propiedades sin personas y la hoja «Constancia» [US-15] [US-16]
- [ ] T013 [Back] Escribir `specs/features/acceso/acceso.spec.md` con `BR-ACCESO-NN` para la cookie `abet_sesion`, Argon2id, el `401` único, el límite de intentos y la visibilidad por `acceso.docente_seccion` [US-04] [US-05] [US-06]
- [ ] T014 [Back] Escribir `specs/features/periodo/periodo.spec.md` con `BR-PERIODO-NN` para `PERIODO_VIGENTE`, `CONJUNTO_REGLAS` y `GET /api/secciones?periodo=2026-2` [US-03] [US-06]
- [ ] T015 [Back] Escribir `docs/specs/api-contracts.md`, el contrato de la interfaz de programación de aplicaciones (application programming interface, API), con los siete endpoints del corte 1, sus cuerpos con la forma que comprueban los `.feature`, sus códigos (`200`, `201`, `204`, `401`, `403`, `409`, `422`, `429` y `500`) y la forma `{ "detail": "mensaje" }` [US-05..US-16]
- [ ] T016 [Back] Dejar definitivos los escenarios del corte 1 en los `.feature` de `specs/001-mvp-carga-r17/aceptacion/`, el único lugar donde viven (`carga.feature` y `r17_constancia.feature` ejecutables; `base_neon.feature`, `acceso.feature` y `despliegue.feature` como criterio escrito), con datos de la sección 410 de 450002 en 2026-2 [US-01..US-17]
- [ ] T017 [Back] Generar con `scripts/generar_exports_inventados.py` (propuesta) los exports de `tests/datos_inventados/` (`sintetico_20262_450002_410.xlsx` con 11 filas y la columna 5.3 de 20 puntos, la copia de `export_inventado_410_con_error.xlsx` y los de la 411, dañado, protegido, PDF renombrado, vacío, sin 5.2, sin Username y con la hoja «Hoja1»), todos con códigos que empiezan con 99 [US-07] [US-10] [US-11] [US-12] [US-13]
- [ ] T018 [Jefferson] Comprar el dominio y abrir la cuenta de Resend (J-04) para que el registro del dominio se propague antes del corte 2 [US-20]
- [ ] T019 [Back] Auditar la fase (cada `BR-` con su escenario, cada endpoint en el contrato y `bash scripts/preflight.sh` sin fallas) y registrarla en `MEMORIA.md` de Back y Front [US-03..US-16]

## Phase 2: Base

- [ ] T020 [Jefferson] Crear el proyecto de Neon con PostgreSQL 16 en aws-sa-east-1, con la rama `develop` para Preview, y guardar sus cadenas directa y con pooler en su gestor de claves [US-01]
- [ ] T021 [Neon] Aplicar V1_01 a V1_08 y las dos vistas con `flyway -environment=neon migrate` desde `ABET_ULIMA` y comprobar la semilla (7 resultados del estudiante o student outcomes, SO; 17 indicadores de desempeño o performance indicators, PI; 102 descriptores, 53 asignaturas y 61 pares) y `security_barrier` en `v_r17_por_pi` [US-01]
- [ ] T022 [Jefferson] Fusionar `preparacion-neon` (4ff1952) en `main` de `ABET_ULIMA`, aprobar el traslado y archivar el repositorio en solo lectura cuando termine T023 [US-01]
- [ ] T023 [Back] Trasladar `bd/` a `db/` con `git subtree` y su historia, aplanar `db/db/` en `db/migration/`, `db/callbacks/` y `db/plataforma/` con las `locations` de `db/flyway.toml` ajustadas (propuesta) y sumar `db/pruebas/correr_pruebas.sh` al job `pruebas` de `.github/workflows/ci.yml` con PostgreSQL 16 desechable [US-01]
- [ ] T024 [Back] Escribir `db/migration/V1_09__crear_acceso.sql` (esquema `acceso`, `abet.carga.subida_por` y los motivos `COLUMNA_CODIGO_AUSENTE`, `PI_REPETIDO`, `PERIODO_NO_COINCIDE` y `SECCION_SIN_DECLARAR`), poner `schemas = ["abet", "acceso"]` en `db/flyway.toml` y agregar a `db/pruebas/pruebas.sql` los rechazos de `ck_usuario_autorizado_correo` y `uq_docente_seccion` y el caso 60,0 / 60,0 / 70,0 [US-04] [US-12] [US-13] [US-21]
- [ ] T025 [Back] Escribir `db/plataforma/neon/crear_rol_app.sql` y `db/plataforma/neon/controles_neon.sql`, con pruebas de que `abet_app` no puede hacer DELETE en `abet.carga` ni UPDATE de `carga.conjunto_reglas_id` ni escribir en `abet.parametro_valor` [US-01] [US-02]
- [ ] T026 [Back] Escribir `db/plataforma/neon/guardia_datos_inventados.sql` (`ck_estudiante_codigo_inventado`) y `db/datos/periodo_2026_2_inventado.sql` (vigencia AMB-2026, secciones 410 y 411 de 450002, plan con 5.1, 5.2 y 5.3, un coordinador y dos profesores con correos `@example.invalid` y sus `docente_seccion`) [US-03] [US-04] [US-08]
- [ ] T027 [Neon] Aplicar V1_09, `crear_rol_app.sql`, `guardia_datos_inventados.sql` y `periodo_2026_2_inventado.sql`, primero en la rama `develop` y después en la principal, y correr `controles_neon.sql` con `abet_respaldo` hasta ver Q01 a Q14 en cero [US-01] [US-02] [US-03] [US-04]
- [ ] T028 [Jefferson] Asignar la clave de `abet_app` en la consola de Neon de cada rama y guardarla en su gestor de claves [US-02]
- [ ] T029 [Back] Auditar la fase (`bash db/pruebas/correr_pruebas.sh` aprobado con los casos nuevos y la integración continua, CI, aprobada) y registrarla en `MEMORIA.md` [US-01..US-04]

## Phase 3: Backend

- [ ] T030 [Back] Crear `pyproject.toml` (FastAPI, psycopg 3, openpyxl 3.1.5, defusedxml, Pillow, argon2-cffi, pytest y pytest-bdd), exportar `requirements.txt` para Snyk, escribir `.env.example` con `DATABASE_URL`, `SESION_SECRETO`, `PERIODO_VIGENTE`, `CONJUNTO_REGLAS` y `GUARDIA_DATOS_INVENTADOS` sin valores y sumar pytest al job `pruebas` [US-05..US-16]
- [ ] T031 [Back] Escribir `abet_carga/lector.py` con la revisión del zip, `load_workbook(read_only=True, data_only=True)` y el descarte de nombres, accesos y valores leídos, más una prueba que falla si `openpyxl.xml.DEFUSEDXML` es `False` [US-11] [US-14]
- [ ] T032 [Back] Escribir `abet_carga/validacion.py` con la guardia de códigos 99, la estructura (`ARCHIVO_SIN_FILAS`, `PI_DEL_PLAN_AUSENTE`, `COLUMNA_CODIGO_AUSENTE` y `PI_REPETIDO`), la sección y el periodo (`SECCION_NO_COINCIDE`, `PERIODO_NO_COINCIDE` y el 422 sin rastro del export que no declara su sección), las filas (`CODIGO_VACIO`, `CODIGO_INVALIDO`, `CODIGO_DUPLICADO`, `NIVEL_FUERA_DE_ESCALA`, con -1, 0 y 5 por D-06, y `NIVEL_NO_NUMERICO`, con «-» y «NP» por D-03) y los avisos `PUNTAJE_MAXIMO_DISTINTO` y `COLUMNA_PI_FUERA_DEL_PLAN` [US-08] [US-10] [US-12] [US-13]
- [ ] T033 [Back] Escribir `abet_carga/carga.py` con `cargar(bytes, seccion_id, usuario_id)` en una sola transacción, la huella SHA-256, la carga existente (200 con su constancia si la huella está PUBLICADA en esa sección, 409 sin datos ajenos si lo está en otra y el mismo `archivo_id` si solo tiene cargas RECHAZADA o REEMPLAZADA), probado con el export con error (11 leídas, 10 aceptadas, 1 rechazada) y Q01 a Q14 en cero [US-07] [US-09] [US-10]
- [ ] T034 [Back] Crear `plantillas/R017_ambiental_general.xlsx` desde la hoja «Cursos de Carrera» vaciada, sin `#REF!` y sin autor, con su excepción en `.gitignore` y en la regla 1 de `scripts/preflight.sh` limitada a esa ruta y probada en `scripts/probar_preflight.sh` (propuesta) [US-15]
- [ ] T035 [Back] Escribir `abet_carga/r17.py` y `abet_carga/constancia.py` desde `v_r17_por_pi`, con Pillow, la franja PROVISIONAL y el tope de 142 filas, probados con 63,6 / 63,6 / 72,7 y 33 filas, con 60,0 / 60,0 / 70,0 y 30 filas, y con una prueba que falla si la salida pierde el logotipo [US-15] [US-16]
- [ ] T036 [Back] Escribir `app/main.py`, `app/sesion.py` y `app/rutas/sesion.py` (`POST`, `GET` y `DELETE /api/sesion`) y `scripts/asignar_clave.py` (propuesta), que lee la contraseña por la entrada estándar y guarda solo su hash Argon2id [US-05]
- [ ] T037 [Back] Escribir `app/permisos.py` y `app/rutas/secciones.py` (`GET /api/secciones?periodo=2026-2`), con el `403` para una sección ajena [US-06]
- [ ] T038 [Back] Escribir `app/rutas/cargas.py` (`POST /api/secciones/{seccion_id}/cargas` con 1 MB como tope y respuestas `201`, `200`, `409`, `422`, `403` y `500`, `GET /api/cargas/{carga_id}` y `GET /api/cargas/{carga_id}/r17.xlsx`), con un registro que guarda solo la huella y la hora de un rechazo por la guardia [US-07] [US-08] [US-09] [US-11] [US-12] [US-13] [US-15] [US-16]
- [ ] T039 [Back] Auditar la fase (cada `BR-` de las specs vivas con su prueba unitaria y el comando de `abet_carga` contra `abet_sis_med_dev`) y registrarla en `MEMORIA.md` [US-05..US-16]

## Phase 4: Frontend

- [ ] T040 [Front] Crear el proyecto con React, Vite, TypeScript y Tailwind, `src/servicios/api.ts` como única puerta HTTP, `src/servicios/tipos.ts` con los tipos del contrato (propuesta) y el proxy de `/api` en `vite.config.ts` hacia el Back local [US-05..US-16]
- [ ] T041 [Front] Construir P1 Ingreso con el mensaje único del `401` y sin guardar la sesión en `localStorage` [US-05]
- [ ] T042 [Front] Construir P2 Mis secciones con el estado de la carga de cada sección [US-06]
- [ ] T043 [Front] Construir P3 Subir export con el rótulo «Solo exports con códigos inventados (99000000 a 99999999)» y los mensajes del `422`, el `409` y el `403` [US-07] [US-08] [US-09] [US-11] [US-12] [US-13]
- [ ] T044 [Front] Construir P4 Resultado de la carga con la constancia (11 leídas, 10 aceptadas, 1 rechazada), los rechazos por motivo y fila sin el valor leído y la descarga del R-17 [US-10] [US-14] [US-15] [US-16]
- [ ] T045 [Front] Probar P1 a P4 con Vitest y Testing Library usando respuestas del contrato solo dentro de las pruebas, y sumar a `scripts/preflight.sh` del Front una regla que falla si un archivo de `src/` usa `localStorage` o llama a una URL que no sea `/api` [US-05]
- [ ] T049 [Front] Auditar la fase (compilación sin errores, pruebas aprobadas y cada pantalla con su historia) y registrarla en `MEMORIA.md` [US-05..US-16]

## Phase 5: Pruebas

- [ ] T050 [Back] Escribir los pasos de `tests/aceptacion/pasos/`, que leen con `scenarios()` `carga.feature` y `r17_constancia.feature` desde `specs/001-mvp-carga-r17/aceptacion/`, con cada «Entonces» comprobado en la base, y sumarlos al job `pruebas` [US-07] [US-08] [US-09] [US-10] [US-11] [US-12] [US-13] [US-14] [US-15] [US-16]
- [ ] T051 [Back] Probar con pytest los criterios escritos de `base_neon.feature` y `acceso.feature` contra un PostgreSQL 16 desechable, salvo los de migración y controles de US-01, que se comprueban en Neon con T021 y T027 [US-01] [US-02] [US-03] [US-04] [US-05] [US-06]
- [ ] T052 [Back] Probar los casos que no deben pasar, entre ellos el export con el código 10000004 en la fila 4 generado en `tmp_path` y nunca versionado (`422` y conteos de `archivo_origen`, `carga` y `estudiante` sin cambio), el profesor que sube a una sección ajena (`403`) y la contraseña errada (`401`) [US-05] [US-06] [US-08]
- [ ] T053 [Back] Escribir `tests/humo/test_flujo_profesor.py` con Playwright para Python contra el Back y el Front locales como prueba de humo, el recorrido mínimo de punta a punta que confirma que el sistema responde (ingresar, subir el export con el 5 en la fila 3, ver 11 / 10 / 1 y descargar el R-17 con 60,0 %, 60,0 % y 70,0 %) [US-05] [US-07] [US-10] [US-15] [US-16]
- [ ] T059 [Back] Auditar la fase (salida resumida de cada comando y la verificación `pruebas` aprobada en los dos repositorios) y registrarla en `MEMORIA.md` de Back y Front [US-01..US-16]

## Phase 6: Auditoría

- [ ] T060 [Back] Escribir `specs/001-mvp-carga-r17/audit.md` con las tablas historia, escenario, prueba y resultado, requisitos funcionales y criterios de éxito [US-01..US-16]
- [ ] T061 [Back] Agregar la sección `Verification` fechada a `carga-export.spec.md`, `r17.spec.md`, `acceso.spec.md` y `periodo.spec.md` [US-03..US-16]
- [ ] T062 [Back] Verificar a mano en el navegador local, con `abet_sis_med_dev`, el flujo del profesor y del coordinador, y anotar la evidencia (ID de la carga, conteos y porcentajes) en `audit.md` [US-05..US-16]
- [ ] T063 [Front] Actualizar la documentación del Front con las pantallas P1 a P4 y el enlace al contrato del Back [US-05..US-16]
- [ ] T069 [Back] Auditar la fase (`audit.md` sin escenarios sin prueba) y registrarla en `MEMORIA.md` de Back y Front [US-01..US-16]

## Phase 7: Despliegue

- [ ] T070 [Jefferson] Crear en el equipo `jeffangeloss-projects` los proyectos de Vercel Hobby `abet-ulima-back` y `abet-ulima-front`, enlazados a sus repositorios con Production desde `main` y Preview desde `develop`, desactivar el entrenamiento de inteligencia artificial (IA) del equipo y enviar la consulta a soporte por la cláusula de uso no comercial (J-07) [US-17]
- [ ] T071 [Back] Escribir `vercel.json` del Back con `regions: ["gru1"]` y la función de FastAPI, y confirmar `prepare_threshold=None` en la conexión con pooler [US-17]
- [ ] T072 [Front] Escribir `vercel.json` del Front con la reescritura de `/api/:path*` hacia la URL del Back que corresponde a Production y a Preview [US-17]
- [ ] T073 [Jefferson] Pegar en Vercel las variables del Back, separadas por Production y Preview (`DATABASE_URL` con pooler y usuario `abet_app` de la rama principal o de `develop`, `SESION_SECRETO`, `PERIODO_VIGENTE`, `CONJUNTO_REGLAS` y `GUARDIA_DATOS_INVENTADOS=1`) [US-17]
- [ ] T074 [Jefferson] Asignar con `scripts/asignar_clave.py` las contraseñas de los tres usuarios de prueba en cada rama de Neon, sin pasarlas por un agente [US-05] [US-17]
- [ ] T075 [Neon] Correr la prueba de humo de T053 contra la vista previa de `develop` y su rama de Neon, restablecida desde la principal (valor provisional de J-09), nunca contra Production, comprobar que la cookie `abet_sesion` viaja por la reescritura y ver `controles_neon.sql` en cero en las dos ramas [US-17]
- [ ] T076 [Jefferson] Publicar la versión 0.1.0 por PR de `develop` a `main`, primero en el Back y después en el Front [US-17]
- [ ] T079 [Back] Auditar la fase (sección «Despliegue» de `audit.md` con cada paso de la prueba de humo y su código HTTP) y registrarla en `MEMORIA.md` de Back y Front [US-17]

## Corte 2: Fases 1, 3, 4, 5, 6 y 7 para US-18 a US-21

- [ ] T080 [Back] Ampliar `carga-export.spec.md`, `acceso.spec.md` y `docs/specs/api-contracts.md` con el reemplazo, la lista de cargas, el código por correo y la confirmación de la sección (D-02 y D-11), y dejar definitivos sus escenarios en `reemplazo_y_cargas.feature` (US-18 y US-19), `acceso.feature` (US-20) y `carga.feature` (US-21) [US-18] [US-19] [US-20] [US-21]
- [ ] T081 [Back] Agregar a `abet_carga/carga.py` y a `app/rutas/cargas.py` el reemplazo con `POST /api/secciones/{seccion_id}/cargas?reemplaza={carga_id}`, que deja la anterior en `REEMPLAZADA` antes de publicar la nueva, con Q07 y Q14 en cero [US-18]
- [ ] T082 [Back] Agregar `GET /api/cargas?seccion_id=` con la visibilidad de `app/permisos.py` [US-19]
- [ ] T083 [Back] Agregar `POST /api/sesion/codigo` con `acceso.codigo_acceso` y Resend, con la misma respuesta exista o no el correo [US-20]
- [ ] T084 [Back] Agregar la confirmación explícita de la sección cuando el archivo no la declara (D-02), con el campo multipart `confirmar_seccion=true` y el AVISO `SECCION_SIN_DECLARAR` en `abet.rechazo_fila`, y retirar el 422 del corte 1 para ese caso [US-21]
- [ ] T085 [Front] Construir P5 Cargas con el reemplazo, P1 con el código por correo y P3 con la confirmación de la sección [US-18] [US-19] [US-20] [US-21]
- [ ] T086 [Jefferson] Configurar los registros de autenticación del correo SPF, DKIM y DMARC del dominio, pegar la clave de Resend en Vercel y probar la entrega a su propia cuenta institucional [US-20]
- [ ] T087 [Back] Probar los escenarios del corte 2, lo que debe pasar y lo que no, y extender la prueba de humo con el reemplazo de la carga con error por el export correcto (63,6 %, 63,6 % y 72,7 % con 33 filas) [US-18] [US-19] [US-20] [US-21]
- [ ] T088 [Back] Agregar al `audit.md` y a las `Verification` de las specs vivas la evidencia del corte 2 [US-18..US-21]
- [ ] T089 [Jefferson] Publicar la versión 0.2.0 por PR de `develop` a `main`, primero en el Back y después en el Front [US-18..US-21]
- [ ] T099 [Back] Auditar el corte (cada historia de US-18 a US-21 con su prueba y su prueba de humo contra la vista previa) y registrarlo en `MEMORIA.md` de Back y Front [US-18..US-21]
