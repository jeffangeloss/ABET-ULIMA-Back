# Tasks: Evolución del curso y competencias por estadío

**Input**: spec.md, plan.md · **Estado al 2026-11-25**: borrador, espera la aprobación de Jefferson, con D-32, D-38, D-57, D-59, D-60 y J-72 a J-77 en sus valores provisionales, D-50 en la spec 008 y D-56 cerrada el 2026-11-25 en la spec 009. La construcción empieza después de construir la spec 010 (J-77). Cada tarea lleva su estimación en horas, que suma unas 62,5

Cada tarea lleva al comienzo el lugar donde ocurre, como en las specs anteriores. `[Back]` es ABET-ULIMA-Back, `[Front]` es ABET-ULIMA-Front, `[Base]` es la base como código de `db/` con sus pruebas en el clúster desechable o su corrida en Neon desde el Windows, y `[Jefferson]` marca lo que solo él decide, autoriza o corre. Mientras J-72 conserve su valor provisional, ninguna tarea escribe en develop ni en la rama principal de Neon. Cada tarea de código escribe primero la prueba de sus escenarios y la ve fallar.

## Fase 0 · Descubrimiento

- [x] T001 Candidatas, auditoría con tres lentes y el crítico, spec y cinco `.feature` · 2026-11-25
- [ ] T002 [Jefferson] Aprobar la spec y J-72 a J-77 · 0,5 h
- [ ] T003 [Jefferson] Llevar D-59 a Claudia León y a la coordinación, recordar D-32, D-38 y D-57 a la coordinación de Ambiental y a la Oficina de Calidad y llevar D-60 a la coordinación de Industrial [US-100] [US-102] [US-103] · 0,5 h

## Fase 1 · Contrato

- [ ] T010 [Back] BR-RESULTADOS-16 a BR-RESULTADOS-19 (propuestas) en `specs/features/resultados/resultados.spec.md`, con la ruta 22, las rutas 23 y 24, la unidad «mediciones» y P9 y P10 sin profesores ni orden por resultado, y el cambio fechado de BR-RESULTADOS-10 [US-100] [US-102] [US-104] · 1,5 h
- [ ] T011 [Front] §17 de `docs/03-api/contrato.md` con las rutas 22, 23 y 24, su lista cerrada de claves y un ejemplo inventado, la tabla general con la ruta 19 reservada, `docs/specs/api-contracts.md` y `docs/specs/feature-index.md` [US-100] [US-102] [US-104] · 2 h
- [ ] T012 [Front] ADR-011 «Evolución del curso y competencias por estadío», que enmienda ADR-010 y la §16.4 del contrato, y la sección 14 de `docs/01-arquitectura/frontend.md` con P9 y P10 [US-101] [US-103] · 1,5 h

## Fase 2 · Base y datos

- [ ] T020 [Base] Escribir primero los escenarios de US-105 y después `db/datos/historico_quimica_inventado.sql`, en seco salvo con `-v aplicar=1`, idempotente, con la ficción de IND-2026 declarada, en `SEMILLAS` de `tests/semillas_inventadas.py` y con las partes 1 a 6 de la huella iguales [US-105] · 3 h
- [ ] T021 [Base] Escribir primero los escenarios de US-106 y después `db/datos/competencias_ambiental_inventado.sql`, con el periodo 2024-2, la ficción de AMB-2026 declarada, los planes de 6511, 450002 y 5674, la 413 y las dos 401 y un profesor inventado por sección, en `SEMILLAS` [US-106] · 3 h
- [ ] T022 [Back] Tablas maestras inventadas en `tests/datos_inventados/maestras_011/`, el oráculo `tests/datos_inventados/oraculo_011.md` calculado a mano y `--pi` como lista en `scripts/generar_exports_desde_maestra.py`, con los escenarios del generador, de los bytes fijos y de las huellas distintas primero [US-107] · 4 h
- [ ] T023 [Back] Escribir primero los escenarios del estudiante en dos periodos, del flujo normal y de la segunda corrida, y después el manifiesto de varios PI y el conciliador por PI en `db/herramientas/ensayar_capacitacion.py`, sin comprobación del rango. La segunda corrida termina con 1 por CON_CARGAS, como hoy, sin subir ningún archivo [US-107] · 2,5 h
- [ ] T024 [Back] Escribir primero los escenarios de US-108 y después `db/herramientas/sembrar_demostracion.py` (propuesta), con respaldo, huella, la comprobación única del rango antes de la primera carga sobre todos los manifiestos juntos, semillas, ensayo por periodo y asignatura sin 5643 en 2026-1, controles, `--rama demo|develop|principal`, `--confirmo-principal`, la negativa ante secciones sin SINTETICO_, el aviso y la omisión de una asignatura con cargas que no son de la demostración y sus comandos con la salida esperada en `db/README.md` [US-108] · 4,5 h
- [ ] T025 [Back] `scripts/api_local.sh` suma al clúster desechable `quimica_2026_1_inventado.sql`, `plan_quimica_2026_1.sql`, las dos semillas y las cargas de la demostración, también las de 5643 en 2026-1 con el ensayo, sin `db/pruebas/datos_sinteticos.sql`, y suma `coordinador.quimica@example.invalid` a las cuentas a las que asigna contraseña, para los pasos de pytest-bdd y los humos. Corre `sembrar_demostracion.py` antes del ensayo de 5643 en 2026-1 y pasa a `plan_quimica_2026_1.sql` una `DESCRIPCION_INSTRUMENTO` inventada [US-105] [US-106] [US-107] · 1,5 h

## Fase 3 · Back

- [ ] T030 [Back] Escribir primero los escenarios de US-100 y después la ruta 22 en `app/rutas/resumen_curso.py`, que recorre `periodos_visibles()` y llama a `resumen_del_curso()` por periodo en una transacción READ ONLY con REPEATABLE READ, con el guardián, el orden 401, 403 y 422, la lista cerrada de claves y la ruta en `test_rutas_protegidas.py` y `tests/rutas_registradas.py` [US-100] · 4 h
- [ ] T031 [Back] Escribir primero los escenarios de US-102 y después la consulta de competencias en `abet_carga/resultados.py` y la ruta 23 en `app/rutas/resumen_carrera.py` (propuesta), con la carrera de `alcance_de()`, las secciones de cada celda de FR-005 con las que no tienen carga PUBLICADA en `sin_dato`, el `estado` de cada sección, el 422 de la carrera, la lista vacía para el alcance CURSO, la lista cerrada de claves y la aserción de 0 mediciones sin estadío [US-102] · 6 h
- [ ] T032 [Back] Escribir primero los escenarios de US-104 y después la ruta 24, con la consulta de T031 por periodo visible, el parámetro opcional `carrera`, la lista vacía para el alcance CURSO y el 422 de la competencia y de la carrera [US-104] · 2,5 h

## Fase 4 · Front

- [ ] T040 [Front] Escribir primero los Vitest de los escenarios `@delegado_a_vitest` de US-101 y después P9 en `src/pantallas/EvolucionCurso.tsx`, con una fila por periodo, su barra de dos tramos, su promedio, su conteo de secciones, el detalle por sección, la franja provisional y el periodo sin cargas, y las piezas exportadas de `ResumenCurso.tsx` [US-101] · 5 h
- [ ] T041 [Front] La vista `evolucion` en `src/App.tsx` con `#/evolucion?asignatura=`, el menú de la coordinación, el enlace desde P7 y P8, el selector de curso con la ruta 21 del periodo de la cabecera y la ruta 22 en `src/servicios/api.ts` y `tipos.ts` [US-101] · 2 h
- [ ] T042 [Front] Escribir primero los Vitest de los escenarios `@delegado_a_vitest` de US-103 y después P10 en `src/pantallas/CompetenciasEstadio.tsx`, con la matriz en la región «Matriz de competencias», el detalle de cada celda, la unidad «mediciones», «Sin SO asociado», «Sin medición en el periodo», los estados vacíos de Industrial y de la coordinación de un curso, la vista `competencias` y el menú solo para el alcance CARRERA [US-103] · 6 h
- [ ] T043 [Front] Escribir primero el Vitest del escenario de US-104 y después el selector «Competencia» de P10 con la tabla de periodos por estadío, y las rutas 23 y 24 en `src/servicios/api.ts` y `tipos.ts` [US-104] · 2,5 h
- [ ] T044 [Front] P9 y P10 en la lista `PANTALLAS` de `e2e/visual.spec.ts` con su caso de `api_simulada.ts`, a 375 px y con teclado [US-101] [US-103] · 1,5 h
- [ ] T045 [Front] Pruebas de humo con Playwright `e2e/humo_evolucion.spec.ts` y `e2e/humo_competencias.spec.ts`, primero contra `scripts/api_local.sh` con los datos de la demostración, donde `coordinador.quimica@example.invalid` ve en P9 60,0 %, 66,7 % y 80,0 % en ese orden y `coordinacion@example.invalid` ve en P10 60,0 %, 80,0 % y 90,0 % para G4, y después contra la vista previa de la demostración, donde solo afirma 2025-1 y 2025-2 en P9 y 2024-2 en P10, y 2026-2 solo si la siembra no omitió esas asignaturas (SC-003), sin afirmar la fila de 2026-1 ni guardar capturas [US-101] [US-103] · 2,5 h

## Fase 5 a 7 · Pruebas, auditoría y despliegue

- [ ] T050 [Back] Suites completas del Back y del Front, `preflight.sh` en los dos y la matriz de cumplimiento con los cinco `.feature` [US-100..US-108] · 1 h
- [ ] T051 [Back] `audit.md` con el cruce de historia, escenario, prueba y resultado y la Verification fechada de la spec viva `resultados` [US-100..US-108] · 1,5 h
- [ ] T052 [Base] Con el permiso de Jefferson, crear la rama `demo-011` de Neon desde develop y cargar en ella los datos inventados desde DESKTOP-FKQ5ENS con `python3 -I ~/.claude/scripts/en_windows.py`, primero en seco y después con `--aplicar`, con el respaldo de `respaldar_neon.sh`, el ensayo por periodo y asignatura sin 5643 en 2026-1, que develop ya tiene, y los controles de `controles_neon.sql`, y comprobar con la huella que develop no cambió (SC-005). Si Jefferson elige develop en J-72, la misma corrida va solo a los periodos sin cargas reales [US-108] · 2 h
- [ ] T053 [Jefferson] Poner en Vercel las variables de vista previa limitadas a la rama de git de la demostración del Back, apuntando a `demo-011`, asignar las contraseñas de las cuentas inventadas y mostrar P9 y P10 a Stefanny Montaño y a Claudia León (SC-003) [US-101] [US-103] · 1 h
- [ ] T054 [Jefferson] Autorizar empujar `feat/011-historico-y-competencias` del Back y del Front y fusionar sus PR en `develop`, fuera de la ventana congelada de la capacitación, y borrar la rama `demo-011` cuando la demostración ya no haga falta [US-100..US-108] · 0,5 h
