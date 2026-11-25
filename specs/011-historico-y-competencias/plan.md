# Implementation Plan: Evolución del curso y competencias por estadío

**Branch**: `docs/011-historico-y-competencias` del Back y del Front (PR a `develop`), con la implementación en `feat/011-historico-y-competencias` después de la aprobación | **Date**: 2026-11-25 | **Spec**: [spec.md](./spec.md)

## Summary

La coordinación ve hoy un curso en un solo periodo en P8, y ninguna pantalla muestra cómo evoluciona entre ciclos ni cómo progresa una competencia a lo largo de la malla, que son las páginas «Histórico por Profesor» y «Resumen Competencias - Nivel» del tablero de Power BI de Stefanny Montaño. El plan suma la ruta 22 con la evolución del curso, que llama a `resumen_del_curso()` de la spec 009 en cada periodo visible, la pantalla P9, las rutas 23 y 24 con el logro por competencia y estadío desde una consulta nueva en `abet_carga/resultados.py` y la pantalla P10. Como la base tiene un solo periodo con cargas y Ambiental no tiene mediciones, el plan genera los datos inventados que faltan, con dos semillas, tablas maestras inventadas que pasan por el generador y el ensayo de la spec 008 y una siembra desde el Windows en una rama de Neon aparte (J-72). No hay migraciones ni dependencias nuevas.

## Technical Context

- **Base.** PostgreSQL 18 en Neon con Flyway 13.9 desde `db/`. Sin migraciones ni vistas nuevas (J-74). Las consultas leen `abet.v_r17_por_pi`, `abet.carga`, `abet.seccion`, `abet.plan_medicion`, `abet.pi`, `abet.so`, `abet.periodo`, `abet.competencia`, `abet.competencia_so` y `abet.asignatura_competencia`, que `abet_app` ya lee (`crear_rol_app.sql:82-91`), en una transacción READ ONLY con REPEATABLE READ. Las semillas nuevas viven en `db/datos/` y corren en seco salvo con `-v aplicar=1`.
- **Back.** Python 3.12 con FastAPI. La ruta 22 se suma a `app/rutas/resumen_curso.py` y las rutas 23 y 24 viven en un router nuevo `app/rutas/resumen_carrera.py` (propuesta), con el guardián `puede_ver_avance()`, `alcance_de()`, `periodos_visibles()` y `secciones_visibles()` de `app/permisos.py`. La consulta de competencias y su conversión viven en `abet_carga/resultados.py` junto a `resumen_del_curso()` y `en_meta()`, con las secciones de cada celda tomadas del plan de estudios, del estadío y del plan de medición, y las que no tienen carga PUBLICADA contadas como sin dato, igual que en la ruta 20 (FR-005). Cambian `scripts/generar_exports_desde_maestra.py` (`--pi` como lista) y `db/herramientas/ensayar_capacitacion.py` (manifiesto de varios PI y conciliador por PI), y nace `db/herramientas/sembrar_demostracion.py` (propuesta) con el molde de `sembrar_quimica.py`, que comprueba el rango de códigos una sola vez antes de la primera carga sobre todos los manifiestos juntos.
- **Front.** React 19 con Vite, TypeScript y Tailwind 4, sin dependencias nuevas. Cambian `src/App.tsx` (vistas `evolucion` y `competencias`, menú y fragmentos), `src/servicios/api.ts` y `src/servicios/tipos.ts` (rutas 22, 23 y 24), `src/pantallas/ResumenCurso.tsx` (exporta `BarraDelCurso`, `LineaDeMeta`, `TablaDeSecciones`, `Franja` y `SelectorDeCurso` y enlaza P9) y `src/pantallas/Avance.tsx` (enlace a P9), y nacen `src/pantallas/EvolucionCurso.tsx` (P9) y `src/pantallas/CompetenciasEstadio.tsx` (P10), propuestos.
- **Contrato.** La §17 de `docs/03-api/contrato.md` del Front con las rutas 22, 23 y 24, su lista cerrada de claves y un ejemplo inventado, la tabla general, `docs/specs/api-contracts.md`, `docs/specs/feature-index.md`, ADR-011 y la sección 14 de `docs/01-arquitectura/frontend.md` con P9 y P10.
- **Pruebas.** pytest-bdd 9 en el Back sobre el clúster desechable, Vitest con `simularApi` en el Front para los escenarios `@delegado_a_vitest` y Playwright en `e2e/` para los de 375 px y los humos de P9 y P10, que corren contra `scripts/api_local.sh` con las semillas y las cargas de la demostración, nunca contra el clúster compartido de localhost:5432.
- **Datos.** En los repositorios, solo datos inventados, con estudiantes del rango 99500000 a 99599999. Las tablas maestras inventadas y el oráculo viven en `tests/datos_inventados/`, los exports se escriben fuera de todo repositorio y la siembra real va en la rama `demo-011` de Neon desde el Windows de Jefferson con `en_windows.py`. La siembra excluye 5643 en 2026-1, que develop ya tiene, y `demo-011` hereda de develop los datos reales de 2026-1 que D-10 autoriza en Neon. Las cuentas inventadas de la vista previa ya los ven hoy en develop, y ninguna captura ni humo de Playwright los registra, por el preflight de la spec 008 (FR-022 de esa spec).

## Constitution Check

| Principio | Cumplimiento |
| --- | --- |
| I · La base es la única fuente de verdad | Las cifras salen de `abet.v_r17_por_pi` y se redondean en PostgreSQL, y P9 y P10 no recalculan |
| II · Privacidad por diseño y solo datos inventados | Listas cerradas de claves sin datos de personas ni profesores, estudiantes del rango 99, barrido de las semillas y ninguna fila del tablero en git |
| III · Toda carga es atómica y trazable | Las cargas de la demostración pasan por `cargar()` con su constancia, su R-17 y su huella, sin INSERT directos |
| IV · Las reglas son datos versionados y lo provisional se ve | La meta y el nivel esperado salen del conjunto de reglas, P9 y P10 muestran la franja provisional y P10 rotula la unidad «mediciones» mientras D-32 siga abierta |
| V · Contrato, historias auditadas y prueba antes de desplegar | 58 candidatas auditadas, contrato de las rutas 22 a 24 antes del código y pruebas primero |
| VI · Capas y privilegio mínimo | `abet_app` no gana permisos, no nace vista ni GRANT y `app/permisos.py` sigue siendo el único dueño de la visibilidad |

## Project Structure

```text
ABET-ULIMA-Back/
  app/rutas/resumen_curso.py                 ruta 22, junto a las rutas 20 y 21
  app/rutas/resumen_carrera.py               rutas 23 y 24 (propuesta)
  abet_carga/resultados.py                   evolución por periodo y consulta de competencias
  db/datos/historico_quimica_inventado.sql   5643 en 2025-1 y 2025-2 (propuesta)
  db/datos/competencias_ambiental_inventado.sql  6511, 450002 y 5674 en 2026-2 y 450002 en 2024-2 (propuesta)
  db/herramientas/sembrar_demostracion.py    siembra de la demostración desde el Windows (propuesta)
  db/herramientas/ensayar_capacitacion.py    manifiesto de varios PI y conciliador por PI
  scripts/generar_exports_desde_maestra.py   --pi como lista
  scripts/api_local.sh                       suma las semillas y las cargas de la demostración
  tests/datos_inventados/maestras_011/       tablas maestras inventadas (propuesta)
  tests/datos_inventados/oraculo_011.md      cifras escritas a mano (propuesta)
  tests/aceptacion/pasos/                    pasos de los cinco .feature
  specs/011-historico-y-competencias/        spec, revisión, plan, tareas y .feature
ABET-ULIMA-Front/
  src/pantallas/EvolucionCurso.tsx           P9 (propuesta)
  src/pantallas/CompetenciasEstadio.tsx      P10 (propuesta)
  src/servicios/api.ts y tipos.ts            rutas 22, 23 y 24
  tests/spec011/                             Vitest de las dos pantallas
  e2e/humo_evolucion.spec.ts y humo_competencias.spec.ts
  docs/03-api/contrato.md y docs/00-vision/adr/ADR-011-evolucion-y-competencias.md
```

## Phases

0. **Descubrimiento.** Candidatas, auditoría, spec y cinco `.feature`, y aprobación de Jefferson.
1. **Contrato.** BR-RESULTADOS-16 a BR-RESULTADOS-19 en la spec viva `resultados`, con el cambio fechado de BR-RESULTADOS-10, la §17 del contrato del Front, ADR-011 y la sección 14 de `frontend.md`.
2. **Base y datos.** Las dos semillas, las tablas maestras inventadas, el oráculo, el generador con varios PI, el ensayo con varios PI, la siembra de la demostración y `api_local.sh` con los datos de la demostración, con pytest-bdd primero.
3. **Back.** Rutas 22, 23 y 24 y la consulta de competencias, con pytest-bdd primero.
4. **Front.** P9, P10, el menú, los enlaces desde P7 y P8 y los fragmentos, con Vitest primero.
5. **Pruebas y humo.** Suites del Back y del Front, `preflight.sh`, la matriz de cumplimiento y los humos con Playwright en el clúster desechable y en la vista previa de la demostración.
6. **Auditoría.** `audit.md`, la Verification fechada de la spec viva `resultados`, `MEMORIA.md` y `CHANGELOG.md`.
7. **Despliegue.** Solo código, porque no hay migraciones. La rama `demo-011` de Neon se crea desde develop y se siembra desde el Windows con el permiso de Jefferson, sin 5643 en 2026-1, la vista previa de la rama de git de la demostración apunta a ella y la fusión en `develop` lleva P9 y P10 a la vista previa de develop, donde se ven con los datos que develop tenga.

## Estimación y fecha

La estimación por tarea está en `tasks.md` y suma unas 62,5 horas, con el contrato, el humo, la carga en Neon y el cierre. Por J-77 la construcción empieza después de construir la spec 010 y fuera de la ventana congelada de la capacitación, así que con unas 9 horas diarias termina unos siete días después de empezar, sin contar la respuesta a D-59.

## Riesgos

- Si D-59 dice que la «evolución histórica» debe ser por profesor, P9 no cambia hasta que D-57 lo permita, y la diferencia se explica a Claudia León.
- Si D-32 fija otro método para una competencia medida por varios PI, cambian la consulta de US-102 y sus escenarios, no las pantallas.
- Si D-38 da un nivel esperado por estadío, cambian el conjunto de reglas y las celdas de P10.
- Las ficciones del catálogo (IND-2026 en 2025 y AMB-2026 en 2024-2) ocupan el par carrera y periodo que después necesita el catálogo real cuando lleguen los R-17 antiguos (H34), así que viven solo en la rama de la demostración y en el clúster desechable (J-75).
- La rama `demo-011` hereda de develop los datos reales de 2026-1 (D-10) y las cargas de 2026-2 que develop tenga. La siembra excluye 5643 en 2026-1, así que la fila de 2026-1 de P9 muestra lo que develop tenga y su oráculo vale solo en el clúster desechable. Si develop tiene cargas de 450002, 6511 o 5674 en 2026-2, la siembra las informa y omite el ensayo de esa asignatura, y SC-003 no compara sus celdas. El conteo de secciones sin dato de 2026-2 depende además de las secciones que develop tenga, porque `varias_secciones_2026_2_inventado.sql` no entra en Neon, así que SC-003 no lo compara.
- Los datos reales de 2026-1 que hereda `demo-011` ya los ven hoy en develop las cuentas inventadas de la vista previa. El humo contra la vista previa de la demostración no afirma la fila de 2026-1 ni guarda capturas, y el preflight de la spec 008 impide versionar capturas y resultados de Playwright.
- Si la construcción se cruza con la ventana de registro del 30-11 al 12-12, la vista previa de develop está congelada (J-56 de la spec 008), así que P9 y P10 se prueban en local y en la vista previa de la demostración.
