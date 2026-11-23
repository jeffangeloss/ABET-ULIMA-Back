# Tasks: Lo importante para cada cuenta y en cada momento del registro

**Input**: spec.md, plan.md · **Estado al 2026-11-22**: spec aprobada por Jefferson en el chat el 2026-11-22 («Sí, apruébala»), con la auditoría, la spec, el plan y los cinco `.feature` en `docs/007-experiencia-por-cuenta` del Back y del Front, sin commit. Ninguna tarea tiene estimación todavía, así que el plan no promete fechas

Cada tarea lleva al comienzo el repositorio o el lugar donde ocurre, como en las specs 001 y 003 a 006. `[Back]` es ABET-ULIMA-Back, `[Front]` es ABET-ULIMA-Front, `[Carrera]` es la Coordinación de Ambiental y `[Jefferson]` marca lo que solo él decide o autoriza. Ninguna tarea escribe en Neon ni en Vercel. Las tareas de la etapa A llevan [A] y las de la etapa B llevan [B].

## Phase 0: Descubrimiento

- [x] T001 [Back] Escribir 18 candidatas desde el profesor, la coordinación y la experiencia de uso, con su pantalla, sus rutas y tablas y su Gherkin, sobre el código de `wt/back-007` y `wt/front-007` [US-59..US-66] · 2026-11-22
- [x] T002 [Back] Auditar las candidatas con las lentes de necesidad, tamaño y verificabilidad y con el crítico de arquitectura, y dejar el resultado en `specs/007-experiencia-por-cuenta/revision-historias.md` [US-59..US-66] · 2026-11-22
- [x] T003 [Back] Redactar `spec.md`, `plan.md`, `tasks.md` y los cinco `.feature`, que el analizador de pytest-bdd lee con 35 escenarios y 70 casos tras la revisión, y sumar la línea de la spec a `specs/README.md` [US-59..US-66] · 2026-11-22
- [x] T004 [Front] Anotar la propuesta en `docs/01-arquitectura/frontend.md` (sección 11), `docs/specs/feature-index.md` y la ruta 17 en `docs/03-api/contrato.md` (sección 14) [US-59..US-66] · 2026-11-22
- [x] T005 [Jefferson] Aprobar la spec, con la fusión de los PR de `docs/007-experiencia-por-cuenta` o con su «apruebo» en el chat, y decidir J-43 a J-48, también si C-P04, C-T03 o C-T05 suben a la spec [US-59..US-66] · Hecha el 2026-11-22 («Sí, apruébala»)
- [ ] T006 [Carrera] Pedir a la Coordinación de Ambiental, esta semana y durante la capacitación, primero D-43 de la spec 005, porque P3 muestra el nombre de la actividad de Blackboard. Después, el texto de contacto del profesor sin secciones (D-46) y si la coordinación ve los correos de los profesores en P7 (D-47) [US-59] [US-60] [US-66]

## Phase 1: Contrato

- [ ] T010 [Front] [A] Escribir en `frontend.md` los textos definitivos de la etapa A, con su marca «(propuesta)» hasta la revisión, y la lista de pruebas de Vitest que cambian (FR-006 y SC-002). Al aprobar, cambian también la sección 3 («con sesión muestra P2», que pasa a la página de llegada de J-46 en la etapa B) y la sección 4 («No hay una carga publicada para esta sección», que pasa a «Esta carga no tiene R-17.») [US-59..US-63]
- [ ] T011 [Back] [B] Abrir la spec viva `specs/features/avance/avance.spec.md` con BR-AVANCE-01 a BR-AVANCE-NN y sus `targets`, sumar BR-ACCESO-12 a `acceso` y su fila a `specs/README.md` [US-64..US-66]
- [ ] T012 [Front] [B] Dejar definitiva la sección 14 del contrato con la ruta 17, sumar su camino a la sección 10 y su fila a `docs/specs/api-contracts.md` [US-64..US-66]
- [x] T013 [Back] Dejar definitivos los cinco `.feature` con el analizador de pytest-bdd y fijar en `test_lectura_gherkin_es.py` el conteo de 35 escenarios y 70 casos, con `@spec007`, `@corte1`, una etapa por escenario o por bloque de Ejemplos y `@delegado_a_vitest` en los de pantalla. En `test_experiencia_por_cuenta_feature.py`, el paso `_pantalla_dada` atiende «una sesión de "…" con rol "…"» y «la cuenta "…" con rol "…"» y solo llama a `_delegar()`, sin abrir la base, y la prueba comprueba que ninguno de esos pasos coincide con la expresión `_sesion_iniciada` de `conftest.py` [US-59..US-66] · Hecha el 2026-11-22

## Phase 2: Base

- [ ] T020 [Back] [B] Sin migración. Sumar a `tests/cargas_de_prueba.py` el ayudante de las secciones 410 a 417 con sus profesores y sus cargas PUBLICADA, RECHAZADA, EN_CURSO y REEMPLAZADA, con su prueba, y el paso «una base desechable del avance de la spec 007, …» que no choca con la expresión de `conftest.py` [US-64..US-66]

## Phase 3: Back

- [x] T030 [Back] [A] Escribir primero el paso del esquema del lector de `antes_de_subir.feature`, sin base, y comprobar que pasa con `abet_carga/lector.py` sin cambios [US-60] · Hecha el 2026-11-22
- [ ] T031 [Back] [B] Escribir primero los pasos de los escenarios de la ruta 17 y después `puede_ver_avance()` en `app/permisos.py`, con el 403 «Esta página es de la Coordinación.» y el orden 401, 403 y 422 [US-64]
- [ ] T032 [Back] [B] Escribir primero el esquema de la precedencia y después `abet_carga/avance.py` con la consulta de la etapa de J-48, sin guardar nada, y `app/rutas/avance.py` con el conteo, `carga_id` y `PERIODO_VIGENTE` [US-64]
- [ ] T033 [Back] [B] Sumar la ruta 17 a `tests/rutas_registradas.py` y comprobar `Cache-Control: no-store` y el 401 sin sesión [US-64]
- [ ] T034 [Back] [B] Escribir primero el escenario del campo `profesores` y después su lectura, solo en CON_RECHAZO y SIN_CARGA, con los correos activos en orden alfabético y sin nombres, solo si D-47 dice que sí [US-66]
- [ ] T035 [Back] [B] Medir la ruta 17 con 60 secciones inventadas en el clúster desechable, en menos de 1 s (SC-005) [US-64]

## Phase 4: Front

- [ ] T040 [Front] [A] Escribir primero las pruebas de Vitest de `siguiente_paso.feature` y después la función de `src/servicios/` que combina las rutas 4 y 8 y la línea de P2 con `aria-describedby` [US-59]
- [ ] T041 [Front] [A] Escribir primero las pruebas de Vitest de `antes_de_subir.feature` y después la constante de J-44 y el apartado «Antes de subir» de P3 [US-60]
- [ ] T042 [Front] [A] Escribir primero las pruebas de Vitest de `rotulos_por_cuenta.feature` y después el nav, `aria-current` y los rótulos por rol de `App.tsx`, P2, P5 y P6 [US-63]
- [ ] T043 [Front] [A] Escribir primero las pruebas de Vitest de US-61, con la que recorre los siete motivos RECHAZA_CARGA del contrato, y después la tabla de J-43 y el párrafo «Qué corregir» de P4 [US-61]
- [ ] T044 [Front] [A] Escribir primero las pruebas de Vitest de US-62, cambiar las de FR-006 y después «Esta carga no tiene R-17.» en P4 y el párrafo nuevo del modo reemplazo de P3 [US-62]
- [ ] T045 [Front] [B] Escribir primero las pruebas de Vitest de US-65 y después P7 en `src/pantallas/Avance.tsx`, la vista «avance», el botón «Avance del registro» y `pantallaDeLlegada(usuario)` de J-46 [US-65]
- [ ] T046 [Front] [B] Escribir primero las pruebas de Vitest de US-66, con el portapapeles simulado y su rechazo, y después los correos de las filas que faltan y el botón de copia, solo si D-47 dice que sí [US-66]

## Phase 5: Pruebas y humo

- [ ] T050 [Back] Suite completa con `uv run --frozen --no-build pytest -q`, `bash scripts/preflight.sh` y `bash db/pruebas/correr_pruebas.sh` con Q01 a Q15 en 0 [US-59..US-66]
- [ ] T051 [Front] Suite de Vitest, `npm run build` y `bash scripts/preflight.sh` del Front [US-59..US-66]
- [ ] T052 [Front] [A] Prueba de humo con Playwright en `e2e/humo.spec.ts`, contra Vite y la API local, en la que `docente410@example.invalid` ve en P2 la línea de lo que falta y en P3 el apartado «Antes de subir» con los nombres de columna de la 410, y sube después el export inventado como hoy [US-59] [US-60]
- [ ] T053 [Front] [B] Sumar al humo con Playwright el ingreso de `coordinacion@example.invalid`, que llega a P7 «Avance del registro» y ve el resumen, con `ingresar()` de `e2e/comun.ts` que espera la página de llegada de cada rol y la contraseña del coordinador en el archivo de `ABET_CLAVES_ARCHIVO` [US-65]

## Phase 6: Auditoría

- [ ] T060 [Back] `specs/007-experiencia-por-cuenta/audit.md` con el cruce de historia, escenario, prueba y resultado, la línea Verification fechada en `avance` y `acceso`, y `MEMORIA.md` y `CHANGELOG.md` de los dos repositorios [US-59..US-66]

## Phase 7: Despliegue

- [ ] T070 [Jefferson] Autorizar empujar las ramas `feat/007-experiencia-por-cuenta` y fusionar sus PR con la integración continua en verde, primero la etapa A y después la etapa B [US-59..US-66] · Etapa A hecha el 2026-11-22 («Sí, júntala»), con el PR #44 del Back en 1c28f50 y jeffangeloss/ABET-ULIMA-Front#29 en bee0adc; falta la etapa B
- [ ] T071 [Front] Correr el humo con Playwright contra la vista previa de `develop` de cada etapa, con `URL_FRONT` y sin escribir contraseñas en el repositorio [US-59] [US-60] [US-65] · Etapa A el 2026-11-22 con `ABET_SIS_MED/herramientas_neon/comprobar_version_020.sh`, 14 de 14 en ok, que ingresa con las tres cuentas y espera la página de llegada de cada rol; las aserciones propias de P2 y P3 esperan a T052, y falta la etapa B
- [ ] T072 [Jefferson] Autorizar la publicación en Production de cada etapa, la A antes del registro del 30-11-2026 con al menos el mínimo de US-60, US-59 y US-61 (FR-016), si la estimación de las fases 3 a 5 lo sostiene, y la B en la semana 16, si cabe [US-59..US-66] · Etapa A publicada el 2026-11-22 con la versión 0.3.0 (PR #46), antes del registro del 30-11 y sin migración en Neon; falta la etapa B
