# Tasks: Oportunidades de mejora en la carga, con semáforo, declaración y R-17 desde la base

**Input**: spec.md, plan.md · **Estado al 2026-11-18**: la fase 0 queda hecha salvo las decisiones de la carrera (T005), y Jefferson aprueba la spec en el chat (T004), así que la fase 1 puede empezar. La implementación espera la fusión de la spec 004, salvo US-51 y V1_11

Cada tarea lleva al comienzo el repositorio o el lugar donde ocurre, como en las specs 001, 003 y 004. `[Back]` es ABET-ULIMA-Back, `[Front]` es ABET-ULIMA-Front, `[Neon]` es la base en la nube, siempre desde el Windows de Jefferson por Tailscale, y `[Jefferson]` marca lo que solo puede hacer él. Ninguna credencial pasa por un agente. Al final, cada tarea lleva las historias que habilita o audita. La estimación de cada fase llega con la aprobación, así que esta lista no promete ninguna fecha. La implementación sale de `develop` después de fusionar la spec 004.

## Phase 0: Descubrimiento

- [x] T001 [Back] Revisar los requisitos de la carrera (N2, N6, N11, N12, N13 y N15), el código de P4, de `App.tsx`, de `abet_carga/r17.py` y de `app/permisos.py`, y la base de Neon en solo lectura, sin copiar datos personales [US-45..US-54]
- [x] T002 [Back] Escribir 15 candidatas desde el pedido de Jefferson, auditarlas con las lentes de necesidad, solapamiento y verificabilidad y con el crítico de arquitectura, y dejar el resultado en `specs/005-oportunidades-de-mejora/revision-historias.md` [US-45..US-54]
- [x] T003 [Back] Redactar `spec.md`, `plan.md`, `tasks.md` y los cuatro `.feature` de `specs/005-oportunidades-de-mejora/` en la rama `docs/005-oportunidades-de-mejora`, que el analizador de pytest-bdd lee con 65 escenarios y 90 casos [US-45..US-54]
- [x] T004 [Jefferson] Aprobar la spec, con la fusión del PR de `docs/005-oportunidades-de-mejora` o con su «apruebo» en el chat, y decidir J-29 a J-37 [US-45..US-54] · Aprobada en el chat el 2026-11-18 («Sí, apruébala»), con J-29 a J-37 en el valor que propone la spec
- [ ] T005 [Jefferson] Llevar D-34 a D-37 a la Coordinación de Ambiental [US-45..US-51]

## Phase 1: Contrato

- [ ] T010 [Back] Escribir las specs vivas, que son `specs/features/r17/r17.spec.md` con BR-R17-04 (de «vacíos y editables» a «desde la base»), BR-R17-11 y BR-R17-12 y la feature `specs/features/mejora/mejora.spec.md` con BR-MEJORA-01 a BR-MEJORA-NN (propuesta), y sumar la fila `mejora` en `specs/README.md` [US-47..US-51] · BR-R17-11 escrita el 2026-11-18 con US-51; BR-R17-04, BR-R17-12 y `mejora` siguen pendientes
- [ ] T011 [Front] Pasar a definitivos el contrato de las rutas 13 a 16 en `docs/03-api/contrato.md` (sección nueva), `docs/specs/api-contracts.md`, P4 en `docs/01-arquitectura/frontend.md`, `docs/specs/feature-index.md` y ADR-009, con el cambio de FR-016 de la spec 004 y del invariante 8 de ADR-008 [US-45..US-54]
- [ ] T012 [Back] Dejar definitivos los cuatro `.feature` con el analizador de pytest-bdd y cumplir FR-017, que amplía la expresión de migraciones de `tests/aceptacion/pasos/conftest.py:767` a V1_11 y V1_12 y suma la regla de copia «con la columna X.Y vacía en las filas N y M» [US-45..US-54] · Los escenarios de US-51 quedan definitivos y la expresión admite V1_11 el 2026-11-18; V1_12, la regla de copia y los demás `.feature` siguen pendientes

## Phase 2: Base

- [x] T020 [Back] V1_11 con `abet.plan_medicion.descripcion_instrumento` y `ck_plan_medicion_descripcion`, probada en el clúster desechable con los casos del escenario 3 de US-51 [US-51] · Hecha el 2026-11-18 en `feat/005-us51-descripcion-instrumento`
- [ ] T021 [Back] V1_12 con `abet.mejora_borrador`, `abet.mejora_declaracion` y sus CHECK, y los permisos exactos de `abet_app` en `db/plataforma/neon/crear_rol_app.sql` con sus listas de comprobación [US-47..US-49] [US-53]
- [x] T022 [Back] Guion de datos `db/datos/descripcion_instrumento_2026_2.sql` con un UPDATE repetible y textos «Texto de prueba.» por PI, y la consulta informativa de solo lectura de los PI sin descripción en `db/plataforma/neon/pi_sin_descripcion_instrumento.sql` [US-51] · Hecha el 2026-11-18 en `feat/005-us51-descripcion-instrumento`
- [ ] T023 [Neon] Consulta de solo lectura de las cargas publicadas sin declaración y de los permisos de `abet_app`, desde el Windows de Jefferson con `ssh windows-worker` [US-49]
- [ ] T024 [Neon] Migrar la rama `develop` desde el Windows con V1_11, V1_12, los permisos sin APP_DB_CLAVE y la comprobación con `has_table_privilege` y `has_column_privilege` [US-47..US-51] · V1_11 aplicada en la rama `develop` el 2026-11-19 con `migrar_neon.sh develop 8d51852`; V1_12 y los permisos siguen con T021
- [x] T025 [Jefferson] Correr el guion de la descripción en la rama `develop` desde el Windows [US-51] · Hecha el 2026-11-19 en la rama `develop` de Neon por Claude Code, con el permiso de Jefferson («Sí, prepárala») y la huella md5 de los tres textos comprobada

## Phase 3: Backend

- [ ] T030 [Back] Escribir primero la prueba de tabla y después la función pura del semáforo en `abet_carga/resultados.py`, con 77,8, 75,0, 74,9, 80,0, los nulos y CORTE_ROJO PENDIENTE [US-45]
- [ ] T031 [Back] Ruta 13 `GET /api/cargas/{carga_id}/indicadores`, con una sola instantánea, `no-store`, el orden 401, 403 y 409 y la lectura de CORTE_ROJO de `abet.parametro_valor`, y las pruebas primero [US-45]
- [ ] T032 [Back] Rutas 14 a 16 con `puede_declarar()`, el orden 401, 403, 422 y 409, el cuerpo leído después del alcance, JSON obligatorio, la normalización del texto y el patrón de códigos y correos, y su entrada en la prueba que recorre las rutas registradas [US-47] [US-48] [US-53]
- [ ] T033 [Back] `DeclaracionPendiente` en `r17.generar()` con la lectura en la misma transacción `READ ONLY` y `REPEATABLE READ`, y su captura en `python -m abet_carga r17` [US-49]
- [ ] T034 [Back] B29 y B34 desde la última declaración, con ajuste de texto, alineación arriba y el alto calculado de las filas 31 y 36 con prueba unitaria, y la edición de `plantillas/README.md` [US-50]
- [x] T035 [Back] G17:I19 desde `abet.plan_medicion.descripcion_instrumento` en `_PLAN` y `_bloques` [US-51] · Hecha el 2026-11-18 en `feat/005-us51-descripcion-instrumento`
- [ ] T036 [Back] Herencia del texto al leer en la ruta 14, con `heredado_de` y el 409 con `reemplazada_por` [US-54]
- [ ] T037 [Back] Ayudante `declarar()` y conjunto de reglas parametrizado R-PRUEBA-SEMAFORO en `tests/cargas_de_prueba.py`, y ajuste de las 26 llamadas de prueba que generan un R-17 [US-49] [US-45]
- [ ] T038 [Back] Pasos de pytest-bdd para los escenarios sin `@delegado_a_vitest` [US-45..US-54]
- [ ] T039 [Back] Control Q16 en `db/pruebas/pruebas.sql`, que busca códigos y correos en las dos tablas y da 0 filas [US-53]

## Phase 4: Frontend

- [ ] T040 [Front] `obtenerIndicadores`, `obtenerMejora`, `guardarBorrador` y `declarar` en `src/servicios/api.ts` y sus tipos en `tipos.ts`, con la simulación de las rutas en `tests/ayudas.ts` [US-45..US-48]
- [ ] T041 [Front] Escribir primero las pruebas y después la sección «Cómo va su sección» de P4, con la leyenda, la franja provisional, los estados en texto, `aria-hidden` y la tolerancia al 404 de la ruta 13 [US-46]
- [ ] T042 [Front] Formulario «Análisis del resultado» de P4 con los enunciados de B28 y B33 y la nota de US-53. Suma el guardado automático (2,5 s, máximo de 15 s, salida del campo y `pagehide` con `keepalive`), el 409 de dos pestañas y la vista del coordinador, sin almacenamiento del navegador [US-47] [US-48] [US-53] [US-54]
- [ ] T043 [Front] R-17 solo desde P4, con el botón deshabilitado y su texto, y los cambios de P2, P5 y P6 para llevar a P4 [US-49]
- [ ] T044 [Front] Navegación con el fragmento de la dirección en `src/App.tsx`, con `pushState`, `popstate` y `replaceState`, y el reinicio del fragmento en `tests/preparar.ts` [US-52]
- [ ] T045 [Front] 401 durante el guardado sin perder el texto, con P4 oculta bajo el ingreso y el reintento con la misma versión [US-48]
- [ ] T046 [Front] Prueba de humo con Playwright en `e2e/humo.spec.ts`, que sube la 410, ve tres PI en rojo, declara y descarga un R-17 con A y B en la vista previa de `develop` [US-45..US-52]

## Phase 5: Auditoría

- [ ] T050 [Back] `specs/005-oportunidades-de-mejora/audit.md` con el cruce de historia, escenario, prueba y resultado, la línea Verification fechada en `r17` y `mejora`, y `MEMORIA.md` y `CHANGELOG.md` de los dos repositorios [US-45..US-54]

## Phase 6: Despliegue

- [ ] T060 [Front] Desplegar primero el Front, tolerante al 404 de la ruta 13, con el PR y la integración continua en verde [US-46] [US-49] [US-52]
- [ ] T061 [Back] Desplegar el Back en la vista previa con la migración y los permisos ya aplicados en la rama `develop` de Neon [US-45..US-51]
- [ ] T062 [Front] Correr T046 contra la vista previa de `develop` con la rama `develop` de Neon restablecida con `ABET_SIS_MED/herramientas_neon/humo_preview.sh`, que corre Jefferson [US-45..US-52]
- [ ] T063 [Neon] Migrar la rama principal desde el Windows de Jefferson con V1_11, V1_12, los permisos sin APP_DB_CLAVE y la comprobación [US-47..US-51]
- [ ] T064 [Jefferson] Correr el guion de la descripción en la rama principal y llevar la versión hacia `main` y Production [US-51] [US-45..US-54]
