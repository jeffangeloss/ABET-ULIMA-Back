# Implementation Plan: Resumen del curso para la coordinación

**Branch**: `docs/009-resumen-curso` del Back y del Front (PR a `develop`), con la implementación en `feat/009-resumen-curso` después de la aprobación | **Date**: 2026-11-24 | **Spec**: [spec.md](./spec.md)

## Summary

La coordinación ve hoy la etapa de cada sección en P7 y los logros por sección en P6, pero ninguna pantalla reúne un curso como la página «Resumen Curso» del tablero de Power BI de Stefanny Montaño. El plan suma la ruta 20, que da a la coordinación las cifras del curso y de cada sección por PI desde `abet.v_r17_por_pi`, la ruta 21 con los cursos de su alcance, la pantalla P8 con las cifras, las barras y la tabla, y la opción `--curso` del conciliador de la spec 008. No hay migraciones ni dependencias nuevas.

## Technical Context

- **Base.** PostgreSQL 18 en Neon con Flyway 13.9 desde `db/`. Sin migraciones. La consulta de la ruta 20 lee `abet.v_r17_por_pi`, `abet.carga`, `abet.seccion`, `abet.plan_medicion`, `abet.pi` y `abet.so`, que `abet_app` ya lee, en una transacción READ ONLY con REPEATABLE READ.
- **Back.** Python 3.12 con FastAPI. Un router nuevo `app/rutas/resumen_curso.py` (propuesta) para las rutas 20 y 21, la consulta y la conversión en `abet_carga/resultados.py` junto a `en_meta()`, el guardián `puede_ver_avance()` de `app/permisos.py` y la opción `--curso` de `db/herramientas/conciliar_tabla_maestra.py`.
- **Front.** React 19 con Vite, TypeScript y Tailwind 4, sin dependencias nuevas. Cambian `src/App.tsx` (P8 en el menú de la coordinación), `src/servicios/api.ts` (rutas 20 y 21), `src/pantallas/Avance.tsx` (enlace a P8) y nace `src/pantallas/ResumenCurso.tsx` (P8), con los rótulos de `MisLogros.tsx` y los componentes del sistema visual de la spec 008.
- **Contrato.** Las rutas 20 y 21 en `docs/03-api/contrato.md` del Front con su lista cerrada de claves, la sección 15.6 marcada como sustituida, `docs/specs/api-contracts.md` y ADR-010.
- **Pruebas.** pytest-bdd 9 en el Back sobre el clúster desechable, Vitest con `simularApi` en el Front para los escenarios `@delegado_a_vitest` y Playwright en `e2e/` para el de 375 px y el humo.
- **Datos.** En los repositorios, solo datos inventados. La tabla maestra real y el tablero viven fuera de todo repositorio, y la corrida real del conciliador con `--curso` imprime solo «igual» o «distinto».

## Constitution Check

| Principio | Cumplimiento |
| --- | --- |
| I · La base es la única fuente de verdad | Las cifras del curso salen de `abet.v_r17_por_pi` y se redondean en PostgreSQL, y P8 no recalcula |
| II · Privacidad por diseño y solo datos inventados | Lista cerrada de claves sin datos de personas, sin profesores y con el conciliador real fuera de git |
| III · Toda carga es atómica y trazable | La spec no escribe en la base |
| IV · Las reglas son datos versionados y lo provisional se ve | La meta y el nivel esperado salen del conjunto de reglas y P8 muestra la franja provisional |
| V · Contrato, historias auditadas y prueba antes de desplegar | 21 candidatas auditadas, contrato de las rutas 20 y 21 antes del código y pruebas primero |
| VI · Capas y privilegio mínimo | `abet_app` no gana permisos y `app/permisos.py` sigue siendo el único dueño de la visibilidad |

## Project Structure

```text
ABET-ULIMA-Back/
  app/rutas/resumen_curso.py                 rutas 20 y 21 (propuesta)
  abet_carga/resultados.py                   consulta y conversión del resumen, junto a en_meta()
  db/herramientas/conciliar_tabla_maestra.py opción --curso
  tests/aceptacion/pasos/                    pasos de resumen_del_curso.feature y conciliacion_del_curso.feature
  specs/009-resumen-del-curso/               spec, revisión, plan, tareas y .feature
ABET-ULIMA-Front/
  src/pantallas/ResumenCurso.tsx             P8
  src/servicios/api.ts                       rutas 20 y 21
  tests/spec009/                             Vitest de pantalla_resumen_del_curso.feature
  e2e/                                       375 px y humo de P8
  docs/03-api/contrato.md y docs/00-vision/adr/ADR-010-resumen-del-curso.md
```

## Phases

0. **Descubrimiento.** Candidatas, auditoría, spec y tres `.feature`, y aprobación de Jefferson del 2026-11-24.
1. **Contrato.** BR-RESULTADOS-12 a BR-RESULTADOS-15 en la spec viva `resultados`, rutas 20 y 21 en el contrato del Front, sección 15.6 sustituida, ADR-010 y cambio fechado de US-80 y FR-016 de la spec 008.
2. **Base.** Sin migraciones. Solo los datos inventados de los Antecedentes en los pasos de pytest-bdd.
3. **Back.** Rutas 20 y 21, consulta del curso y opción `--curso` del conciliador, con pytest-bdd primero.
4. **Front.** P8, el enlace desde P7 y el menú, con Vitest primero.
5. **Pruebas y humo.** Suites del Back y del Front, `preflight.sh` y el humo con Playwright contra la vista previa.
6. **Auditoría.** `audit.md`, la Verification fechada de la spec viva `resultados`, `MEMORIA.md` y `CHANGELOG.md`.
7. **Despliegue.** Solo código, porque no hay migraciones. La fusión en `develop` lleva P8 a la vista previa, y la página oficial espera la versión siguiente.

## Estimación y fecha

La estimación por tarea está en `tasks.md` y suma unas 30 horas, con el contrato y el cierre. Por J-64 la construcción empieza después del ensayo de la capacitación de la spec 008, así que con unas 9 horas diarias termina unos cuatro días después de ese ensayo, sin contar la respuesta de Stefanny a D-56.

## Riesgos

- Si D-56 dice que el tablero cuenta sobre el total o promedia porcentajes, el conciliador con `--curso` da «distinto» sin que el sistema esté mal, y la diferencia se explica a Stefanny antes de cambiar una regla.
- Si D-32 fija otro método, cambian la consulta del curso y sus escenarios, no la pantalla.
- Con un profesor por sección, la tabla por sección identifica al profesor para quien conoce la programación. D-57 lo decide la institución.
- Si la construcción se cruza con la ventana de registro del 30-11 al 12-12, la vista previa de develop está congelada (J-56 de la spec 008), así que P8 se prueba en local hasta que se descongele.
