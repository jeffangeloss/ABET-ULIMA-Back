# Tasks: Resumen del curso para la coordinación

**Input**: spec.md, plan.md · **Estado al 2026-11-24**: spec aprobada por Jefferson en el chat el 2026-11-24 («Sí, apruébala»), con D-32 y J-60 a J-64 en sus valores provisionales. La construcción empieza después del ensayo de la capacitación de la spec 008 (J-64). Cada tarea lleva su estimación en horas, que suma unas 30

Cada tarea lleva al comienzo el lugar donde ocurre, como en las specs anteriores. `[Back]` es ABET-ULIMA-Back, `[Front]` es ABET-ULIMA-Front, `[Base]` es la base como código de `db/` con sus pruebas en el clúster desechable y `[Jefferson]` marca lo que solo él decide o corre desde su Windows. Ninguna tarea escribe en Neon. Cada tarea de código escribe primero la prueba de sus escenarios y la ve fallar.

## Fase 0 · Descubrimiento

- [x] T001 Candidatas, auditoría con tres lentes y el crítico, spec y tres `.feature` · 2026-11-24
- [x] T002 [Jefferson] Aprobar la spec y J-60 a J-64 · 2026-11-24, «Sí, apruébala»
- [ ] T003 [Jefferson] Pedir a Stefanny las fórmulas DAX de «Alumnos Aprobados», «Secciones Aprobadas», «Promedio Nota» y «% Alumnos 3-4» (D-56), y llevar D-57 y D-32 a la coordinación y a la Oficina de Calidad [US-91] [US-94] · 0,5 h

## Fase 1 · Contrato

- [x] T010 [Back] BR-RESULTADOS-12 a BR-RESULTADOS-15 en `specs/features/resultados/resultados.spec.md`, con el cambio fechado de BR-RESULTADOS-10 [US-91] [US-92] · 2026-11-24
- [ ] T011 [Front] Rutas 20 y 21 en `docs/03-api/contrato.md` con su lista cerrada de claves y el ejemplo inventado, la sección 15.6 marcada como sustituida, `docs/specs/api-contracts.md` y `docs/specs/feature-index.md` [US-91] [US-93] · 1,5 h
- [ ] T012 [Front] ADR-010 «Resumen del curso para la coordinación en el sistema», con ADR-008 vigente y modificada en parte [US-91] [US-92] · 1 h
- [x] T013 [Back] Cambio fechado de US-80 y FR-016 en `specs/008-ciclo-quimica-industrial/spec.md` y de T039 y T047 en su `tasks.md`, sustituidos por esta spec, con la razón de los seis escenarios de US-80 en `cumplimiento_razones.toml` [US-91] · 1 h · 2026-11-25, `spec.md` de la spec 008 marca US-80, FR-016, SC-001 y J-54 como sustituidos por la spec 009 (J-61), `tasks.md` anota T039 y T047 como sustituidas por T020, T021, T030 y T031, y `cumplimiento_razones.toml` da a cada uno de los seis escenarios de US-80 su razón con los escenarios de la spec 009 que lo cubren. `cumplimiento.md` se regenera con 10 pendientes y 0 huecos
- [x] T014 [Back] Pasos compartidos de los Antecedentes de la spec 009 en `tests/aceptacion/pasos/conftest.py`, con la carga de una sección con «los niveles [a, b, c, d]» y un alumno sin evidencia, y el conteo de la spec 009 en `test_lectura_gherkin_es.py` [US-91] [US-94] · 2 h · 2026-11-25, la variante `resumen_curso` de `conftest.py` (Química con su plan y el plan de 450010), el paso de la base de la spec 009, `publicar_seccion_de_quimica()` con los pasos de «la 70N publicada con los niveles [a, b, c, d]», con o sin un alumno sin evidencia, y de las tres secciones del primer escenario, `filas_por_nivel()` y las opciones `periodo`, `carrera` y `reemplaza` de `cargas_de_prueba.publicar()`. `test_pasos_compartidos_spec_009.py` suma 32 pruebas que fallan sin ellos, y `test_lectura_gherkin_es.py` lee los tres `.feature` con 23 escenarios, 6 a Vitest y 1 a Playwright

## Fase 3 · Back

- [ ] T020 [Back] Escribir primero los escenarios de US-91 y después la consulta del resumen en `abet_carga/resultados.py`, con la suma de conteos, `ROUND(numeric, 1)` y `ROUND(numeric, 2)` en PostgreSQL, `en_meta()`, el conteo de secciones, los nulos, la marca provisional y la meta nula con metas distintas [US-91] · 4 h
- [ ] T021 [Back] Escribir primero los escenarios de acceso de US-91 y después la ruta 20 en `app/rutas/resumen_curso.py`, con el guardián de la ruta 17, el 422 de los parámetros, la lista cerrada de claves y la ruta en la prueba de rutas con sesión de J-25 [US-91] · 2,5 h
- [ ] T022 [Back] Escribir primero los escenarios de US-93 y después la ruta 21 con los cursos del alcance [US-93] · 2 h
- [ ] T023 [Back] Escribir primero los escenarios de US-94 y después la opción `--curso` del conciliador, que compara el curso y el promedio de cada sección y escribe solo «igual» o «distinto» [US-94] · 3 h

## Fase 4 · Front

- [ ] T030 [Front] Escribir primero los Vitest de los escenarios `@delegado_a_vitest` de US-92 y después P8 en `src/pantallas/ResumenCurso.tsx`, con las cifras del curso, la barra de dos tramos, la tabla con su barra por fila y la línea de la meta, la franja provisional y el curso sin cargas [US-92] · 4 h
- [ ] T031 [Front] El menú de la coordinación con «Resumen del curso», el enlace desde cada curso de P7, el selector de curso de US-93 y las rutas 20 y 21 en `src/servicios/api.ts` [US-92] [US-93] · 2 h
- [ ] T032 [Front] P8 en la lista `PANTALLAS` de `e2e/visual.spec.ts` con su caso de `api_simulada.ts`, a 375 px y con teclado [US-92] · 1 h
- [ ] T033 [Front] Prueba de humo con Playwright de P8 en `e2e/`, contra la vista previa de develop con la siembra inventada, en la que `coordinador.quimica@example.invalid` abre «Resumen del curso» y ve las cifras del curso y una fila por sección con las cifras del generador del humo de la spec 008 [US-92] · 1,5 h

## Fase 5 a 7 · Pruebas, auditoría y despliegue

- [ ] T040 [Back] Suites completas del Back y del Front, `preflight.sh` en los dos y la matriz de cumplimiento [US-91..US-94] · 1 h
- [ ] T041 [Back] `audit.md` con el cruce de historia, escenario, prueba y resultado y la Verification fechada de la spec viva `resultados` [US-91..US-94] · 1,5 h
- [ ] T042 [Jefferson] Correr fuera de todo repositorio el conciliador con `--curso` sobre la tabla maestra real de Química General y mostrar P8 a Stefanny junto a su página «Resumen Curso» (SC-002 y SC-003) [US-94] · 1 h
- [ ] T043 [Jefferson] Autorizar empujar `feat/009-resumen-curso` del Back y del Front y fusionar sus PR en `develop`, fuera de la ventana congelada de la capacitación [US-91..US-94] · 0,5 h
