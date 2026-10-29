# Tasks: Proyectos de Capstone en la base, tabla maestra en el formato nuevo y R-17 con la hoja «Cursos Capstone»

**Input**: spec.md, plan.md · **Estado al 2026-10-29**: fase 0 hecha salvo la aprobación de Jefferson (T004); las fases 2 a 7 esperan la fusión del corte 1 de la spec 001 en `develop` (T020)

Cada tarea lleva al comienzo el repositorio o el lugar donde ocurre. `[Back]` es ABET-ULIMA-Back, `[Front]` es ABET-ULIMA-Front, `[Neon]` es la base en la nube y `[Jefferson]` marca lo que solo puede hacer él, porque exige su cuenta, su decisión o sus credenciales. Ninguna credencial pasa por un agente. Al final, cada tarea lleva las historias que habilita o audita, y un rango como `[US-03..US-18]` incluye las historias intermedias. Los nombres de archivo nuevos del Back son ejemplo hasta cerrar J-11 a J-14.

## Phase 0: Descubrimiento

- [x] T001 [Back] Leer la spec 001 (`spec.md`, `revision-historias.md`, `plan.md`, `tasks.md` y `aceptacion/*.feature`), las specs vivas, la constitución, `AGENTS.md`, la base de `db/` (V1_01 a V1_09, las vistas `R__`, `db/datos` y `db/plataforma`) y el contrato `docs/03-api/contrato.md` del Front, y la estructura de los dos Excel que extrae el integrador sin abrir sus datos [US-01..US-25]
- [x] T002 [Back] Escribir 46 candidatas con Gherkin en español desde tres ángulos, auditarlas con las lentes de necesidad, tamaño y verificabilidad y con la crítica de arquitectura, y dejar el resultado en `specs/002-capstone/revision-historias.md` [US-01..US-25]
- [x] T003 [Back] Redactar `specs/002-capstone/spec.md`, `plan.md`, `tasks.md`, los cuatro `.feature` de `specs/002-capstone/aceptacion/` (83 escenarios que pasan el parser oficial de Gherkin) y la fila de la spec 002 en `specs/README.md`, en la rama `docs/002-capstone` [US-01..US-25]
- [ ] T004 [Jefferson] Revisar y fusionar la solicitud de integración (pull request, PR) de `docs/002-capstone` a `develop`, que aprueba la spec [US-01..US-25]
- [ ] T005 [Jefferson] Confirmar J-11 (una fila por estudiante), J-12 (`plan_estudios.tipo_curso`), J-13 (`rechazo_proyecto` propia), J-14 (bloque `proyectos`), J-15 (409 y Q18) y J-16 (409 en el reemplazo del export) [US-01..US-24]
- [ ] T006 [Jefferson] Llevar D-14 a D-29 a la Coordinación de Ambiental y a la Oficina de Calidad, empezando por D-14 (asignaturas Capstone), D-15 (R-18), D-16 (formato de la tabla maestra) y D-19 (RUC), y registrar cada respuesta con su fecha en `MEMORIA.md` [US-01] [US-10] [US-19] [US-21]
- [ ] T009 [Back] Auditar la fase (cada historia de la spec con su traza en `revision-historias.md`) y registrarla en `MEMORIA.md` de Back y Front [US-01..US-25]

## Phase 1: Contrato

- [ ] T010 [Back] Escribir `specs/features/proyectos-capstone/proyectos-capstone.spec.md` con `BR-PROYECTOS-NN` para la ruta, el orden de las comprobaciones, la guardia (que solo actúa sobre un código de 8 dígitos o un RUC con la forma `^20[0-9]{9}$`), la medida de `filas_de_datos` de la plantilla (FR-011), la estructura, las reglas por fila, la regla del grupo, el aviso, la huella, la transacción y el descarte de ALUMNO, cada una con su restricción de la base [US-03..US-18]
- [ ] T011 [Back] Sumar a `specs/features/r17/r17.spec.md` un bloque fechado con la elección de hoja por `tipo_curso`, la hoja «Cursos Capstone», la franja «SIN DATOS DE PROYECTO» y las dos huellas de «Constancia», y a `specs/features/periodo/periodo.spec.md` los campos nuevos de `GET /api/secciones` [US-19] [US-20] [US-23]
- [ ] T012 [Back] Sumar a `specs/features/acceso/acceso.spec.md` un bloque fechado que extiende BR-ACCESO-07 y 08 a la ruta de proyectos y al bloque `proyectos` [US-06]
- [ ] T013 [Back] Escribir `scripts/generar_plantillas_inventadas.py` (propuesta), que genera en `tests/datos_inventados/` `sintetico_20262_450024_420.xlsx`, `sintetico_20262_450024_421.xlsx`, `plantilla_proyectos_inventada_420.xlsx` y sus copias defectuosas, todas con códigos que empiezan con 99 y RUC que empiezan con 20999, y comprobar que dos corridas dan las mismas huellas [US-03..US-16]
- [ ] T014 [Front] Sumar a `docs/03-api/contrato.md`, con su índice `docs/specs/api-contracts.md`, la ruta `POST /api/secciones/{seccion_id}/proyectos` con sus códigos (`200`, `201`, `401`, `403`, `409`, `422` y `500`) y sus `detail`, el bloque `proyectos` de `GET /api/cargas/{carga_id}`, la elección de hoja y el nombre del R-17 Capstone y los cinco campos nuevos de `GET /api/secciones`, y comprobar su sección 10 sin mensajes sin escenario en los dos sentidos [US-03..US-23]
- [ ] T015 [Back] Dejar definitivos los escenarios del corte 1 en los cuatro `.feature` de `specs/002-capstone/aceptacion/` y volver a pasarlos por el parser oficial de Gherkin [US-01..US-24]
- [ ] T019 [Back] Auditar la fase (cada `BR-` con su escenario, cada ruta en el contrato y `bash scripts/preflight.sh` sin fallas) y registrarla en `MEMORIA.md` de Back y Front [US-01..US-24]

## Phase 2: Base

- [ ] T020 [Jefferson] Confirmar que el corte 1 de la spec 001 está fusionado en `develop` y que V1_09, `crear_rol_app.sql` y `periodo_2026_2_inventado.sql` están aplicados en las dos ramas de Neon, antes de empezar esta fase [US-01..US-24]
- [ ] T021 [Back] Escribir la migración `db/migration/V1_10__crear_proyectos_capstone.sql` (propuesta de nombre) como cambio nuevo, sin editar V1_01 a V1_09, con `plan_estudios.tipo_curso` y `ck_plan_estudios_tipo_curso` sin marcar ninguna asignatura, `archivo_origen.tipo_fuente` varchar(20) con PLANTILLA_PROYECTOS y `uq_archivo_origen_tipo`, y las tablas `carga_proyecto`, `proyecto_estudiante` y `rechazo_proyecto` con las restricciones de FR-003 a FR-005 (entre ellas la FK de `filas_de_datos` hacia `uq_archivo_origen_filas` y `uq_carga_proyecto_carga`), y sumar a `db/pruebas/pruebas.sql` un caso que debe pasar y uno que no por cada restricción nueva [US-01] [US-07..US-11] [US-16]
- [ ] T022 [Back] Escribir `db/migration/R__vista_tabla_maestra_capstone.sql` sobre las tablas base con `security_barrier`, y sumar `tipo_curso` al final de `db/migration/R__vista_r17_por_pi.sql`, ambas sobre las versiones con `security_barrier` que trae el subtree de `preparacion-neon`, y hacer en `db/pruebas/correr_pruebas.sh` la foto de `v_tabla_maestra_pi` en el ensayo por etapas, después de aplicar `EN_NEON` y antes de V1_10, para compararla con EXCEPT en los dos sentidos después de `NUEVAS`, porque `pruebas.sql` corre con todas las migraciones ya aplicadas [US-19] [US-21] [US-22]
- [ ] T023 [Back] Ampliar `db/plataforma/neon/crear_rol_app.sql` con los permisos de FR-020 y `db/pruebas/probar_rol_app.sql` con los casos de US-02, incluido el que repite el script después de recrear las vistas [US-02]
- [ ] T024 [Back] Ampliar `db/plataforma/neon/guardia_datos_inventados.sql` con `ck_proyecto_ruc_inventado` y `db/pruebas/probar_guardia.sql` con el RUC 20123456781 que falla y el 20999999906 que pasa [US-15]
- [ ] T025 [Back] Ampliar `db/datos/periodo_2026_2_inventado.sql` con las secciones 420 y 421 de 450024 (`curso_blackboard` «SINTETICO_20262_450024_420» y «SINTETICO_20262_450024_421»), su plan con 1.1, 1.2 y 1.3 e instrumento «Proyecto», la marca CAPSTONE de 450024 y 450026 con el comentario «valor provisional de D-14» y los usuarios `docente420@example.invalid` y `docente421@example.invalid` con sus `docente_seccion`, repetible sin duplicar, y `db/pruebas/datos_sinteticos.sql` con la sección 420 coherente (11 estudiantes 99000101 a 99000111 y 4 grupos). Como `correr_pruebas.sh` carga `datos_sinteticos.sql` antes de la semilla y, en el ensayo de Neon, con solo V1_01 a V1_08, ese archivo crea él mismo la 420, su plan y sus usuarios, como ya hace con la 410, y la subida y los proyectos van en `db/pruebas/datos_sinteticos_capstone.sql` (propuesta), que `correr_pruebas.sh` aplica después de V1_10. La aserción A05 de `pruebas.sql` pasa a las cifras nuevas de usuarios, asignaciones y filas de `plan_medicion` [US-01] [US-03] [US-24]
- [ ] T026 [Back] Ampliar Q04 en `pruebas.sql` y `controles_neon.sql` con «alumno» y las tres tablas de proyecto, escribir Q16 a Q20 con su sondeo en una transacción que se deshace, S01 como consulta de seguimiento y la prueba de paridad de `controles_neon.sql` con Q01 a Q14 y Q16 a Q20, y cambiar la línea fija «RESULTADO: Q01 a Q14 devuelven 0 filas.» en `controles_neon.sql` y en la función `controles` de `correr_pruebas.sh` por la que nombra Q01 a Q14 y Q16 a Q20 [US-14] [US-24]
- [ ] T027 [Neon] Aplicar V1_10 y las dos vistas con `flyway migrate`, repetir `crear_rol_app.sql` y `crear_roles_lectura.sql` con el cambio de T028, aplicar la guardia ampliada y la semilla, primero en la rama `develop` y después en la principal, y correr `controles_neon.sql` con `abet_respaldo` hasta ver Q01 a Q14 y Q16 a Q20 en cero [US-01] [US-02] [US-15] [US-24]
- [ ] T028 [Back] Sumar `abet.v_tabla_maestra_capstone` a `db/plataforma/neon/crear_roles_lectura.sql` (SELECT de `abet_lectura` y comprobación de `security_barrier`) y a `db/callbacks/afterMigrate__permisos_lectura.sql`, en el repositorio de origen del subtree o como cambio local de `db/` con su nota de divergencia en `db/README.md`, con un caso que compruebe `has_table_privilege('abet_lectura', 'abet.v_tabla_maestra_capstone', 'SELECT')` y el mismo para `powerbi_lectura` después del `migrate` [US-21]
- [ ] T029 [Back] Auditar la fase (`bash db/pruebas/correr_pruebas.sh` aprobado en un clúster desechable con los casos nuevos y la integración continua aprobada) y registrarla en `MEMORIA.md` [US-01] [US-02] [US-22] [US-24]

## Phase 3: Backend

- [ ] T030 [Back] Escribir `abet_carga/lector_proyectos.py` (ejemplo), que revisa el zip como el lector de la spec 001, busca la hoja «Hoja1» y la fila de los ocho encabezados, toma las columnas por su encabezado, lee el RUC como texto, ignora K3:M5 y descarta ALUMNO sin guardarlo [US-09] [US-10] [US-13] [US-14]
- [ ] T031 [Back] Escribir `abet_carga/validacion_proyectos.py` (ejemplo) con la guardia de código y RUC, la estructura, las reglas por fila de FR-009, la normalización del tipo de empresa, la regla del grupo de FR-010 y el aviso ESTUDIANTE_SIN_PROYECTO, con los mensajes de los `.feature` y sin ningún valor leído [US-07..US-12] [US-15]
- [ ] T032 [Back] Escribir `abet_carga/carga_proyectos.py` (ejemplo) con `cargar_proyectos(bytes, seccion_id, usuario_id)` en una sola transacción, la huella SHA-256 buscada antes de escribir (200, 409 o 422), el cierre con `clock_timestamp()` y el registro que guarda solo el SQLSTATE y el nombre de la restricción, probado con la plantilla inventada (11 / 11 / 0) y con la copia de la fila 4 (11 / 10 / 1) [US-03] [US-16] [US-17]
- [ ] T033 [Back] Crear `plantillas/R017_ambiental_capstone.xlsx` desde la hoja «Cursos Capstone» de «Plantilla Base - Final.xlsx», vaciada, sin `#REF!`, sin autor y con el logotipo, escribir su mapa de celdas (cabecera, bloque II, rótulos B48:L48 y filas de la tabla) con el número de filas que admite, y sumar su excepción a `.gitignore` y a la regla 1 de `scripts/preflight.sh` limitada a esa ruta y probada en `scripts/probar_preflight.sh` (propuesta) [US-19] [US-20]
- [ ] T034 [Back] Ampliar `abet_carga/r17.py` y `abet_carga/constancia.py` con la elección de hoja por `v_r17_por_pi.tipo_curso`, la tabla de «Cursos Capstone» con los seis datos de proyecto, la franja y el sufijo de US-20 y la hoja «Constancia» con las dos huellas y «N de M estudiantes con datos de proyecto», probados con 33 filas, con 0 de 11 y con 9 de 11 [US-19] [US-20]
- [ ] T035 [Back] Escribir `app/rutas/proyectos.py` con `POST /api/secciones/{seccion_id}/proyectos`, el tope de 1 MB y el orden de comprobaciones de los Edge Cases de la spec (401, 403, 409 de tipo de curso o 422 sin plan de medición, 409 sin export, 422, 200, 409 y 201), con el permiso de `app/permisos.py` [US-03..US-17]
- [ ] T036 [Back] Ampliar `app/rutas/cargas.py` con el bloque `proyectos` de `GET /api/cargas/{carga_id}` y `app/rutas/secciones.py` con los campos de FR-023 [US-18] [US-23]
- [ ] T037 [Back] Escribir una prueba que falle si existe la ruta de reemplazo del export de la spec 001 (su US-18) y no responde el 409 de J-16 en una sección con plantilla PUBLICADA, y que pase mientras esa ruta no exista; si US-18 ya está implementado, sumar el 409 a esa ruta. La dependencia queda anotada en `MEMORIA.md` para quien implemente el corte 2 de la spec 001 [US-24]
- [ ] T039 [Back] Auditar la fase (cada `BR-PROYECTOS-` con su prueba unitaria y el comando de `abet_carga` contra la base desechable) y registrarla en `MEMORIA.md` [US-03..US-23]

## Phase 4: Frontend

- [ ] T040 [Front] Sumar a P3 Subir export la zona «Plantilla de proyectos», visible solo cuando `tipo_curso` es CAPSTONE, con los rótulos «Solo plantillas con códigos y RUC inventados» y «La columna ALUMNO no se guarda» y los mensajes del `409`, el `422` y el `403` [US-03] [US-04] [US-05] [US-13] [US-14] [US-15]
- [ ] T041 [Front] Sumar a P4 Resultado de la carga el resultado de la plantilla (conteos, aviso y rechazos por fila, columna y motivo sin valor leído) y la descarga del R-17 con su hoja [US-12] [US-18] [US-19] [US-20]
- [ ] T042 [Front] Sumar a P2 Mis secciones el estado de proyectos de cada sección y «9 de 11 con proyecto» (propuesta) [US-23]
- [ ] T043 [Front] Probar P2 a P4 con Vitest y Testing Library usando respuestas del contrato solo dentro de las pruebas [US-03] [US-12] [US-18] [US-23]
- [ ] T049 [Front] Auditar la fase (compilación sin errores, pruebas aprobadas y cada pantalla con su historia) y registrarla en `MEMORIA.md` [US-03..US-23]

## Phase 5: Pruebas

- [ ] T050 [Back] Escribir los pasos de `tests/aceptacion/pasos/`, que leen con `scenarios()` `carga_proyectos.feature` y `evidencia_capstone.feature` desde `specs/002-capstone/aceptacion/`, con cada «Entonces» comprobado en la base, y sumarlos al job `pruebas` [US-03..US-22]
- [ ] T051 [Back] Probar con pytest los criterios escritos de `base_capstone.feature` y `secciones_capstone.feature` contra un PostgreSQL 16 desechable armado con `db/pruebas/cluster_desechable.sh` [US-01] [US-02] [US-23] [US-24]
- [ ] T052 [Back] Probar los casos que no deben pasar con las copias generadas en `tmp_path` y nunca versionadas (código 10000004 y RUC 20123456781, `422` y conteos sin cambio), el profesor que sube a una sección ajena (`403`) y la sección de carrera (`409`) [US-05] [US-06] [US-15]
- [ ] T053 [Front] Escribir `e2e/humo-capstone.spec.ts` (propuesta) con Playwright contra el Back y el Front locales como prueba de humo, el recorrido mínimo de punta a punta que confirma que el sistema responde (ingresar como `docente420@example.invalid`, subir el export de la 420, subir la plantilla inventada, ver 11 / 11 / 0 y descargar el R-17 con la hoja «Cursos Capstone») [US-03] [US-18] [US-19] [US-23]
- [ ] T059 [Back] Auditar la fase (salida resumida de cada comando y la verificación `pruebas` aprobada en los dos repositorios) y registrarla en `MEMORIA.md` de Back y Front [US-01..US-24]

## Phase 6: Auditoría

- [ ] T060 [Back] Escribir `specs/002-capstone/audit.md` con las tablas historia, escenario, prueba y resultado, requisitos funcionales y criterios de éxito [US-01..US-24]
- [ ] T061 [Back] Agregar la sección `Verification` fechada a `proyectos-capstone.spec.md` y a los bloques nuevos de `r17.spec.md`, `periodo.spec.md` y `acceso.spec.md` [US-03..US-23]
- [ ] T062 [Back] Verificar a mano en el navegador local el flujo del profesor de la 420 y del coordinador, y anotar la evidencia (ID de la carga y de la subida, conteos y hoja del R-17) en `audit.md` [US-03..US-23]
- [ ] T063 [Front] Actualizar la documentación del Front con la zona de la plantilla en P3, su resultado en P4 y el estado de proyectos en P2 [US-03..US-23]
- [ ] T069 [Back] Auditar la fase (`audit.md` sin escenarios sin prueba) y registrarla en `MEMORIA.md` de Back y Front [US-01..US-24]

## Phase 7: Despliegue

- [ ] T070 [Neon] Confirmar Q01 a Q14 y Q16 a Q20 en cero en las dos ramas después de T027 y de la primera subida de prueba [US-24]
- [ ] T071 [Back] Correr el humo de T053 contra la vista previa de `develop` y su rama de Neon (J-09 de la spec 001) y anotar el resultado en `audit.md` [US-03] [US-19]
- [ ] T072 [Jefferson] Aprobar el paso de `develop` a `main` en los dos repositorios, el Back primero, con la versión que fije `docs/devops.md` [US-01..US-24]
- [ ] T079 [Back] Auditar la fase (sección «Despliegue» de `audit.md` con la migración, el commit y el humo) y registrarla en `MEMORIA.md` de Back y Front [US-01..US-24]

## Corte 2

- [ ] T080 [Back] Exigir el campo `declaracion_sin_personas` en `app/rutas/proyectos.py` y guardar `declaro_sin_personas` y `declarado_en` en la subida, con el contrato del Front actualizado antes [US-25]
- [ ] T081 [Front] Sumar a P3 la casilla de declaración y el mensaje del `422` [US-25]
- [ ] T082 [Back] Escribir los pasos de los escenarios `@corte2` de `carga_proyectos.feature` y enviar la declaración en los pasos de las demás subidas [US-25]
- [ ] T089 [Back] Auditar el corte (escenarios `@corte2` aprobados y `audit.md` actualizado) y registrarlo en `MEMORIA.md` de Back y Front [US-25]
