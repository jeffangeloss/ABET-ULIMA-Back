# Tasks: Los logros del profesor por SO, solo en sus secciones

**Input**: spec.md, plan.md · **Estado al 2026-11-18**: la fase 0 queda hecha salvo las decisiones de la carrera (T005), Jefferson aprueba la spec en el chat (T004) y la construcción, auditada en `audit.md`, entra a `develop` con el PR #31 del Back y el PR #20 del Front (T070)

Cada tarea lleva al comienzo el repositorio o el lugar donde ocurre, como en las specs 001 y 003. `[Back]` es ABET-ULIMA-Back, `[Front]` es ABET-ULIMA-Front, `[Neon]` es la base en la nube, siempre desde el Windows de Jefferson por Tailscale, y `[Jefferson]` marca lo que solo puede hacer él. Ninguna credencial pasa por un agente. Al final, cada tarea lleva las historias que habilita o audita. La estimación de cada fase llega con la aprobación, así que esta lista no promete ninguna fecha.

## Phase 0: Descubrimiento

- [x] T001 [Back] Revisar los límites de acceso que ya existen (`app/permisos.py`, BR-ACCESO-07 y BR-ACCESO-08 y sus escenarios aprobados) y los requisitos de reportes de `ABET_SIS_MED` (N6, N9, N10, N15, H05, H06, H13 y PA-04), sin copiar datos personales [US-37..US-44]
- [x] T002 [Back] Escribir 22 candidatas desde cuatro ángulos, auditarlas con las lentes de necesidad, tamaño y verificabilidad y con el crítico de arquitectura, y dejar el resultado en `specs/004-reportes-docente/revision-historias.md` [US-37..US-44]
- [x] T003 [Back] Redactar `spec.md`, `plan.md`, `tasks.md` y los dos `.feature` de `specs/004-reportes-docente/`, que el analizador de pytest-bdd lee con 37 escenarios y 45 casos [US-37..US-44]
- [x] T004 [Jefferson] Aprobar la spec, con la fusión del PR de `docs/004-reportes-docente` o con su «apruebo» en el chat, y decidir J-21 a J-28 [US-37..US-44] · Aprobada en el chat el 2026-11-18 («Sí, apruébala»), con J-21 a J-28 en el valor que propone la spec
- [ ] T005 [Jefferson] Llevar D-32, D-33 y D-34 a la Coordinación de Ambiental y recordarle D-12 y D-30, que siguen con su dueño [US-37]

## Phase 1: Contrato

- [x] T010 [Back] Escribir `specs/features/resultados/resultados.spec.md` con BR-RESULTADOS-01 a BR-RESULTADOS-NN, sumar BR-ACCESO-10 y la ruta 12 a BR-ACCESO-07 y BR-ACCESO-08, y dejar bloques fechados en BR-R17-02, BR-PERIODO-01 y BR-PERIODO-04 y la fila `resultados` en `specs/README.md` [US-37..US-44] · 2026-11-18, BR-RESULTADOS-01 a BR-RESULTADOS-11 en `feat/004-reportes-docente`
- [x] T011 [Front] Pasar a definitivos la ruta 12 en `docs/03-api/contrato.md` (tabla de rutas, su sección, la sección 3.4, la cuenta de caminos de OpenAPI y la carpeta de la spec 004 en la comprobación de mensajes de la sección 10), `docs/specs/api-contracts.md`, `docs/01-arquitectura/frontend.md`, `docs/specs/feature-index.md` y ADR-008 [US-37..US-44] · 2026-11-18, en a5d678c de `feat/004-reportes-docente` del Front
- [x] T012 [Back] Dejar definitivos los dos `.feature` con el analizador de pytest-bdd y sumar a `REGLAS_DE_COPIA` de `tests/aceptacion/pasos/conftest.py` la regla «con la columna X.Y vacía en sus N filas», con su prueba [US-39] · 2026-11-18, con `test_lectura_gherkin_es.py` y `test_reglas_de_copia.py`

## Phase 2: Base

- [x] T020 [Back] Sin migración. Comprobar en la base desechable que `abet_app` lee `abet.v_r17_por_pi`, `abet.so`, `abet.pi`, `abet.instrumento` y `abet.plan_medicion`, y dejar en `db/plataforma/neon/` la consulta de solo lectura con `has_table_privilege` para Neon [US-37] · 2026-11-18, `db/plataforma/neon/revisar_permisos_resultados.sql` y `tests/test_permisos_resultados.py`
- [x] T021 [Neon] Correr esa consulta en la rama `develop` desde el Windows de Jefferson con `ssh windows-worker`, antes de fusionar el PR del Back [US-37] · 2026-11-18, «Faltan 0 permisos de lectura de la ruta 12.» en la rama develop, con la sesión en solo lectura

## Phase 3: Backend

- [x] T030 [Back] Declarar la dependencia de sesión en cada router con datos y escribir primero `tests/test_rutas_protegidas.py`, que recorre `app.routes` con la lista cerrada de rutas públicas y exige 401 sin cookie y 403 con un `seccion_id` o un `carga_id` ajeno [US-38] · 2026-11-18, routers de `secciones`, `cargas` y `resultados`
- [x] T031 [Back] Escribir primero las pruebas unitarias y después `abet_carga/resultados.py`, con la función pura de la meta y la conversión de `Decimal`, y hacer que `_plan_de_accion` de `abet_carga/r17.py` la use (63,6 sale como `63.6`, el nulo como `null` y 80,0 frente a 80,0 da verdadero) [US-37] [US-40] · 2026-11-18, `tests/test_resultados.py`
- [x] T032 [Back] Escribir primero `tests/test_api_resultados.py` y después `app/rutas/resultados.py`, con una sola instantánea, la lista cerrada de claves, la unión por `pi_id` y `so_id` y el orden de FR-005, sembrando cargas con `publicar()` y `filas_inventadas()` [US-37..US-44] · 2026-11-18, `tests/test_api_resultados.py`
- [x] T033 [Back] Pasos de pytest-bdd en `tests/aceptacion/pasos/test_resultados_feature.py` y `test_alcance_resultados_feature.py` para los escenarios sin `@delegado_a_vitest` [US-37..US-44] · 2026-11-18, 27 escenarios y 33 casos de la API, y 10 escenarios y 12 casos delegados a Vitest
- [x] T034 [Back] Sembrar 150 secciones en la base desechable, revisar con `EXPLAIN` que el filtro por `carga_id` baja por debajo de la agregación de la vista y medir la ruta del coordinador en menos de 1 s (SC-005) [US-44] · 2026-11-18, en `tests/test_api_resultados.py`
- [x] T035 [Back] Prueba con una segunda versión de catálogo inventada y un PI 5.10 en la base desechable, sin indicadores duplicados y con el 5.10 después del 5.2 [US-37] · 2026-11-18, en `tests/test_api_resultados.py`

## Phase 4: Frontend

- [x] T040 [Front] `obtenerResultados` en `src/servicios/api.ts` y su tipo en `src/servicios/tipos.ts`, con su prueba [US-37] · 2026-11-18, en 203d822 del Front
- [x] T041 [Front] Escribir primero `tests/pantallas/MisLogros.test.tsx` y después `src/pantallas/MisLogros.tsx` (P6), con las barras de texto completo, `aria-hidden`, los grupos por SO, la marca provisional, los nulos, la lista vacía, los enlaces al R-17, sin «Subir export» y sin almacenamiento del navegador [US-37] [US-38] [US-39] [US-41] [US-42] [US-43] · 2026-11-18, en 203d822 del Front, con 15 pruebas de P6
- [x] T042 [Front] La vista `logros` en `src/App.tsx` y los enlaces de P2 («Ver mis logros por SO» y, para el coordinador, «Ver los logros por SO de la carrera») y de P4, con sus pruebas [US-37] [US-44] · 2026-11-18, en 203d822 del Front, con 5 pruebas en `tests/App.test.tsx`
- [x] T043 [Front] Prueba de humo con Playwright en `e2e/humo.spec.ts`. Después de la subida de la 410 en la vista previa de `develop`, abre P6, compara sus cifras con el R-17 descargado de esa misma carga y comprueba que `docente411@example.invalid` no ve la 410 en su P6. Corre una vez por restablecimiento de la rama `develop` de Neon y nunca con `docente.varias@example.invalid`, que no existe en Neon [US-37] [US-38] [US-40] · 2026-11-18, los dos casos de P6 en 203d822 del Front pasan en local contra `api_local.sh`, y su corrida en la vista previa es T071

## Phase 5: Pruebas

- [x] T050 [Back] Suite completa con `uv run --frozen --no-build pytest -q`, `bash scripts/preflight.sh` y `bash db/pruebas/correr_pruebas.sh` con Q01 a Q15 en 0 [US-37..US-44] · 2026-11-18, 1440 passed y 15 skipped, revisión previa sin fallas y «RESULTADO: todo pasó» con Q01 a Q15
- [x] T051 [Front] `npm test`, `npm run build` y la comprobación de mensajes de la sección 10 del contrato con la carpeta de la spec 004 [US-37..US-44] · 2026-11-18, 164 pruebas aprobadas, compilación sin errores y 0 mensajes de los escenarios sin contrato

## Phase 6: Auditoría

- [x] T060 [Back] `specs/004-reportes-docente/audit.md` con el cruce de historia, escenario, prueba y resultado, la línea Verification fechada en `resultados`, `acceso`, `r17` y `periodo`, y `MEMORIA.md` y `CHANGELOG.md` de los dos repositorios [US-37..US-44] · 2026-11-18, `audit.md` y las líneas Verification del 2026-11-18

## Phase 7: Despliegue

- [x] T070 [Jefferson] Autorizar empujar las ramas `feat/004-reportes-docente` y fusionar sus PR con la integración continua en verde [US-37..US-44] · empuje autorizado el 2026-11-18 («Sí, empuja y abre»), con jeffangeloss/ABET-ULIMA-Back#31 y jeffangeloss/ABET-ULIMA-Front#20, y fusión autorizada el mismo día («Sí, fusiónalos»), con el #31 en f403d52 y el #20 en 778ae23
- [ ] T071 [Front] Correr T043 contra la vista previa de `develop`, con la rama `develop` de Neon restablecida con `ABET_SIS_MED/herramientas_neon/humo_preview.sh`, que corre Jefferson [US-37] [US-38] [US-40]
- [ ] T072 [Jefferson] Llevar la versión hacia `main` y Production, sin migración en Neon [US-37..US-44]
