# Implementation Plan: Ciclo de punta a punta de Química General en Ingeniería Industrial

**Branch**: `docs/008-ciclo-quimica-industrial` del Back y del Front (PR a `develop`), con la implementación en `feat/008-ciclo-quimica-industrial` después de la aprobación | **Date**: 2026-11-23 | **Spec**: [spec.md](./spec.md)

## Summary

La capacitación usa Química General (5643) de Ingeniería Industrial en 2026-1 con los datos reales que entrega la Oficina de Calidad, y hoy el sistema no puede recorrer ese ciclo. El plan carga en la base el catálogo IND-2026, el conjunto de reglas de Industrial y el plan de 5643 con el PI 6.1 (US-67 a US-69), ata la coordinación de cada carrera a su carrera y crea la coordinación de un curso con una tabla de alcance y un guion de registro (US-70 a US-72), deja a cada cuenta elegir el periodo (US-73), genera desde la tabla maestra un export por sección con el formato de Blackboard (US-74), prueba la publicación de 5643 en Industrial, sus errores probables y los consejos de P4 (US-75 a US-77), corrige la carrera del R-17 y el catálogo de P6 (US-78), construye la etapa B de la spec 007 con el alcance del curso (US-79) y, si D-32 se responde, el agregado del curso (US-80). Rediseña las pantallas con un sistema visual común y accesible (US-81 y US-82), concilia la base y los R-17 con la tabla maestra en un ensayo previo y después de la sala (US-83 y US-84), prueba el despliegue con un humo de Playwright (US-85), siembra develop desde el Windows (US-86), escribe la guía (US-87), blinda los repositorios públicos (US-88), cierra la capacitación (US-89) y genera la matriz de cumplimiento (US-90).

## Technical Context

- **Base.** PostgreSQL 18 en Neon con Flyway 13.9 desde `db/`. Tres migraciones nuevas, V1_12 (catálogo IND-2026, solo datos y generada), V1_13 (reglas de Industrial, solo datos) y V1_14 (`acceso.coordinacion_alcance`, solo DDL con su GRANT de lectura). La V1_12 de la spec 005 pasa a V1_15 (FR-004). Guiones de datos nuevos en `db/datos/` (`plan_quimica_2026_1.sql`, `alcance_coordinacion_ambiental.sql` y `quimica_2026_1_inventado.sql`), la consulta de solo lectura `db/plataforma/neon/huella_ambiental.sql` y las consultas Q18 a Q21 en `db/pruebas/pruebas.sql` y `controles_neon.sql`.
- **Back.** Python 3.12 con FastAPI. Cambian `app/permisos.py` (`_ALCANCE` por la tabla de alcance), `app/sesion.py` y la ruta 2 (campo `alcance`), `app/rutas/cargas.py` (parámetro `periodo` de la ruta 8), `app/configuracion.py` (comprobación por carrera) y `abet_carga/r17.py` (B6). Son nuevos `app/rutas/periodos.py` (ruta 18), `app/rutas/avance.py` y `abet_carga/avance.py` (ruta 17 de la spec 007), y los guiones `db/herramientas/generar_v1_12.py`, `registrar_coordinacion.py`, `conciliar_tabla_maestra.py`, `ensayar_capacitacion.py`, `sembrar_quimica.py` y `cerrar_capacitacion.py` y `scripts/generar_exports_desde_maestra.py` y `scripts/matriz_cumplimiento.py`, todos propuestas.
- **Front.** React 19 con Vite, TypeScript y Tailwind 4, sin dependencias nuevas. Cambian `src/index.css` (tokens en `@theme`), `src/componentes/`, `src/App.tsx` (periodo, rótulos por alcance, P7 y `pantallaDeLlegada()`), `src/servicios/api.ts`, `tipos.ts`, `rotulos.ts`, `ayudas.ts` y `secciones_del_profesor.ts`, y las pantallas P1 a P6. Es nueva `src/pantallas/Avance.tsx` (P7), como fija la spec 007. La dirección visual sale de la skill frontend-design.
- **Contrato.** La sección 15 nueva de `docs/03-api/contrato.md` del Front con la ruta 18, el campo `alcance` de la ruta 2, el periodo de las rutas 4, 8, 12 y 17, el alcance del curso de la ruta 17, el campo condicional `agregados` de la ruta 12 y la reserva de la ruta 19, y su fila en `docs/specs/api-contracts.md` y `docs/specs/feature-index.md`.
- **Pruebas.** pytest-bdd 9 con gherkin-official en el Back, en el clúster desechable de `tests/cluster_desechable.py`. Vitest y Testing Library en el Front para los escenarios `@delegado_a_vitest`, con `simularApi`. Playwright 1.64.1 en `e2e/` para los `@playwright`. Cada historia se construye con su prueba primero (TDD), sus escenarios en Gherkin (BDD) y la corrida de los `.feature` como aceptación (ATDD), en cada commit y en la integración continua.
- **Datos.** En los repositorios, solo datos inventados con correos de example.invalid y códigos de 99000000 a 99999999. Los datos reales viven en `ABET_SIS_MED/datos_reales/quimica_2026_1/`, en Neon y en Vercel (D-10). El generador y el conciliador corren sobre ellos solo desde una carpeta fuera de git.
- **Restricciones.** Una sola línea de trabajo, en una sola sesión. Toda escritura en Neon sale del Windows de Jefferson con `ssh windows-worker` y `en_windows.py`, y las contraseñas las escribe Jefferson con getpass. Codex CLI (plan Plus) se usa solo para piezas chicas sin datos reales, como la función de contraste o el esquema de un ayudante, y se pregunta antes de una tarea de más de 50 000 tokens. No hay clave de la API de OpenAI, así que la optimización de costos se logra con subagentes de Claude de menor costo en lo mecánico. Ningún commit ni push sin el permiso de Jefferson, y los commits van solo a su nombre.

## Constitution Check

| Principio | Cumplimiento |
| --- | --- |
| I · La base es la única fuente de verdad | El catálogo, las reglas, el plan y el alcance viven en la base, el R-17 toma la carrera de `abet.carga.carrera_id` y las cifras salen de `abet.v_r17_por_pi`, también en el conciliador y en el agregado |
| II · Privacidad por diseño y solo datos inventados | Ningún dato real entra a git, el correo real llega solo por variable, el generador no copia nombres, ninguna salida trae un código de ocho cifras y `preflight.sh` detecta el correo real por su huella |
| III · Toda carga es atómica y trazable | La carga de 5643 usa la misma transacción de `cargar()`, el reemplazo de la coordinación deja `subida_por`, y el ensayo corre en una base aparte para no tocar `uq_archivo_origen_sha256` de develop |
| IV · Las reglas son datos versionados y lo provisional se ve | R-2026-BORRADOR de IND entra por migración, el R-17 sale PROVISIONAL (D-54), IND-2026 queda en BORRADOR (D-50) y el PI llega por parámetro (D-48) |
| V · Contrato, historias auditadas y prueba antes de desplegar | 37 candidatas auditadas con tres lentes y el crítico, contrato de las rutas 18 y 17 y del campo `alcance` antes del código, reglas BR nuevas, pruebas primero y humo con Playwright |
| VI · Capas y privilegio mínimo | `abet_app` solo lee `acceso.coordinacion_alcance`, `app/permisos.py` sigue siendo el único dueño de la visibilidad y el conciliador lee con `abet_respaldo` en READ ONLY |

## Project Structure

```
ABET-ULIMA-Back/
  specs/008-ciclo-quimica-industrial/        revisión, spec, plan, tareas, aceptación y cumplimiento.md (nuevo)
  specs/features/acceso/acceso.spec.md       BR-ACCESO-13 y BR-ACCESO-14, cambios fechados en BR-ACCESO-07 y 08
  specs/features/periodo/periodo.spec.md     BR-PERIODO-05 y BR-PERIODO-06
  specs/features/carga-export/carga-export.spec.md   cambio fechado en BR-CARGA-20
  specs/features/r17/r17.spec.md             BR-R17-13
  specs/features/avance/avance.spec.md       BR-AVANCE de la spec 007 con el alcance nuevo
  db/referencia/industrial_2026.json         referencia curricular de Industrial, sin personas
  db/herramientas/generar_v1_12.py, registrar_coordinacion.py, conciliar_tabla_maestra.py, ensayar_capacitacion.py,
                                             sembrar_quimica.py, cerrar_capacitacion.py
  db/migration/V1_12__cargar_referencia_industrial.sql, V1_13__cargar_reglas_industrial.sql, V1_14__crear_coordinacion_alcance.sql
  db/datos/plan_quimica_2026_1.sql, alcance_coordinacion_ambiental.sql, quimica_2026_1_inventado.sql
  db/plataforma/neon/huella_ambiental.sql, controles_neon.sql, crear_rol_app.sql
  db/pruebas/pruebas.sql, probar_rol_app.sql, correr_pruebas.sh
  app/permisos.py, app/sesion.py, app/configuracion.py, app/rutas/cargas.py, app/rutas/periodos.py, app/rutas/avance.py
  abet_carga/r17.py, abet_carga/avance.py
  scripts/generar_exports_desde_maestra.py, scripts/matriz_cumplimiento.py, scripts/preflight.sh
  tests/aceptacion/pasos/ (pasos de los doce .feature y conftest.py ampliado), tests/rutas_registradas.py

ABET-ULIMA-Front/
  src/index.css, src/componentes/*        tokens y componentes del sistema visual
  src/App.tsx                             periodo, rótulos por alcance, P7 y pantallaDeLlegada()
  src/pantallas/*.tsx, src/pantallas/Avance.tsx
  src/servicios/api.ts, tipos.ts, rotulos.ts, ayudas.ts, secciones_del_profesor.ts
  tests/                                  pruebas de Vitest de cada escenario @delegado_a_vitest y de la guía
  e2e/humo_quimica.spec.ts, e2e/visual.spec.ts   humo y uso a 375 px y con teclado
  docs/capacitacion/guia_quimica.md       guía por rol, con correos de ejemplo
  docs/03-api/contrato.md, docs/specs/api-contracts.md, docs/specs/feature-index.md
  docs/01-arquitectura/frontend.md        sección 12, textos y estado de App.tsx de la spec 008
  scripts/preflight.sh
```

## Phases

0. **Descubrimiento.** Candidatas desde cuatro ángulos, auditoría con tres lentes y el crítico (`revision-historias.md`), spec y doce `.feature` leídos por el analizador de pytest-bdd, contrato propuesto en el Front y aprobación de Jefferson con J-49 a J-59. Pedido de D-48 a D-55 a Stefanny y de la fecha de la capacitación.
1. **Contrato.** Reglas BR nuevas y cambios fechados en las specs vivas, sección 15 definitiva del contrato y sus índices, cambio fechado de la spec 005 (V1_15) y de la spec 007 (textos de FR-019), conteo de la spec 008 en `test_lectura_gherkin_es.py` y pasos compartidos de `conftest.py`.
2. **Base.** V1_12 con su generador y la sección 1 de `pruebas.sql`, V1_13, el guion del plan, V1_14 con sus privilegios, el guion de alcance de Ambiental, los datos inventados de Química, la huella de Ambiental, Q18 a Q21 y el guion que siembra en orden, cada uno con su prueba primero.
3. **Back.** Alcance por carrera y por curso, campo `alcance`, guion de registro, ruta 18 y periodo de la ruta 8, comprobación de arranque, generador, B6 del R-17, conciliador, ruta 17 con el alcance, agregado si D-32 se responde, cierre y matriz, cada uno con su prueba primero.
4. **Front.** Sistema visual, P2 con el camino de cada sección, periodo en la cabecera, rótulos por alcance, consejos de P4, fila de P6, P7, agregado en P6 si entra, guía con su cotejo, y uso a 375 px y con teclado, con Vitest y Playwright primero.
5. **Pruebas y humo.** Suites del Back y del Front, `preflight.sh` con las reglas nuevas en los dos, el barrido del historial, el humo con Playwright contra la vista previa con la siembra inventada, el guion del ensayo, la programación de la capacitación, el modo de J-58 y el ensayo con los datos reales en una rama hija de develop (J-52).
6. **Auditoría.** `audit.md` con el cruce de historia, escenario, prueba y resultado, la matriz de cumplimiento, la Verification fechada en las specs vivas, `MEMORIA.md` y `CHANGELOG.md`.
7. **Despliegue.** V1_12 a V1_14 y el alcance de Ambiental en develop antes de la fusión de `feat/008-ciclo-quimica-industrial` con el permiso de Jefferson, siembra de develop desde el Windows en el orden de FR-020, capacitación con develop congelada (J-56), conciliación posterior y cierre. Production solo con una decisión aparte de Jefferson y D-55.

## Estimación y fecha

La estimación por tarea está en `tasks.md` y suma unas 130 horas. Con una sola línea de trabajo, la cuenta usa unas 9 horas diarias desde el 24-11-2026, sin contar el tiempo de respuesta de Stefanny ni las aprobaciones de Jefferson.

- **Antes del 30-11 (unas 52 h, del 24 al 29-11).** Las decisiones de arranque (T005 y T006), el contrato y los pasos compartidos (T010 a T013), la base de T020 a T026, el alcance, la sesión, el registro, el periodo, el generador, la carga y el R-17 en el Back (T030 a T036) y el periodo y los rótulos del curso en el Front (T042 y T043). Con eso US-67 a US-75 y US-78 quedan construidas y probadas en local, sin despliegue. Nada de la capacitación de punta a punta cabe antes del 30-11.
- **Semana del 30-11 (unas 57 h).** El conciliador (T037), la siembra ordenada (T027), el guion del ensayo (T057), la programación de la capacitación (T059), la ruta 17 y P7 (T038 y T046), los tokens y P2 del sistema visual (T040 y T041), los consejos de P4 (T044), la guía (T049), la privacidad (T052), las suites (T050 y T051), el humo (T053), el ensayo (T054), el modo de J-58 (T058) y las migraciones, la fusión y la siembra (T069 a T071). La capacitación de punta a punta completa cabe hacia el 6-12-2026, dentro del registro del 30-11 al 12-12, si Jefferson aprueba la spec el 23 o el 24-11.
- **Después de la capacitación (unas 20 h).** El resto del rediseño y P6 (T045), el uso a 375 px y con teclado (T048), el agregado si D-32 se responde (T039 y T047), el cierre (T056 y T072), la matriz (T055) y la auditoría (T060).

Si la capacitación debe ocurrir antes, el mínimo que la sostiene es US-67 a US-75, US-78, US-83, US-84, US-85, US-86 y US-87 con los tokens del sistema visual (unas 88 h), que termina hacia el 3-12-2026, con la coordinación del curso siguiendo el avance en P2. J-56 fija la fecha con esta estimación.

## Riesgos

- La spec 005 aprobada pierde el número V1_12. Si se construyera antes que esta spec, el orden de FR-004 se invierte con otro cambio fechado.
- Si la tabla maestra trae un estudiante en dos secciones, una calificación fuera de 1 a 4 o una sección que no está en la programación, el generador se detiene y la Oficina de Calidad corrige la tabla antes del ensayo.
- Si Stefanny responde 6.2 a D-48, cambian el parámetro del plan y del generador, sin código.
- Un restablecimiento de develop durante la ventana de registro borra las cargas reales. J-56 congela develop y el humo se niega a correr sobre la siembra de la capacitación.
- La etapa B de la spec 007 es la parte más grande de la semana del 30-11. Si no llega, la coordinación del curso sigue el avance en P2 (FR-014).
- Las fuentes del sistema dependen del equipo de cada profesor. El contraste se calcula sobre los colores, que no dependen de la fuente.
- La estimación no cuenta el tiempo de respuesta de Stefanny ni las aprobaciones de Jefferson, que pueden mover la fecha de la capacitación.
