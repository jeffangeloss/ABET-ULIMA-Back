# Implementation Plan: Los logros del profesor por SO, solo en sus secciones

**Branch**: `docs/004-reportes-docente` (PR a `develop`), con la implementación en `feat/004-reportes-docente` del Back y del Front después de la aprobación | **Date**: 2026-11-17 | **Spec**: [spec.md](./spec.md)

## Summary

El profesor sube su export y descarga el R-17 de cada carga, pero no ve en ninguna pantalla cómo le va frente a los resultados del estudiante (student outcomes, SO). El plan agrega la ruta 12, `GET /api/resultados?periodo=2026-2`, que lee `abet.v_r17_por_pi` por el `carga_id` de la carga PUBLICADA de cada sección que devuelve `app/permisos.secciones_visibles()`, y la pantalla P6 «Mis logros por SO», que agrupa cada indicador de desempeño (performance indicator, PI) bajo su SO con una barra y su cifra escrita frente a la meta. La ruta no recibe identificadores, lleva los porcentajes con el decimal de la vista y decide la meta con la misma función que el R-17. Antes de la ruta, cada router con datos pasa a exigir la sesión, y una prueba recorre las rutas registradas para que ninguna responda sin ella. La prueba de cierre es P6 en la vista previa de `develop`, con las mismas cifras del R-17 de la 410 y sin la 410 en la P6 de `docente411@example.invalid`.

## Technical Context

- **Backend.** Python 3.12 con FastAPI y psycopg 3, sin dependencias nuevas. La ruta vive en `app/rutas/resultados.py` (propuesta), lee en una sola sentencia o en una transacción `READ ONLY` con `REPEATABLE READ` y convierte cada `Decimal` antes de `JSONResponse`. La función pura de la meta y la conversión de cifras viven en `abet_carga/resultados.py` (propuesta), que `abet_carga/r17.py` usa en `_plan_de_accion`. Cada router con datos declara `APIRouter(dependencies=[Depends(sesion.usuario_actual)])`.
- **Frontend.** React 19 con Vite, TypeScript y Tailwind, sin biblioteca de gráficos. P6 vive en `src/pantallas/MisLogros.tsx` (propuesta), con la vista `logros` de `src/App.tsx`, `obtenerResultados` en `src/servicios/api.ts` y su tipo en `src/servicios/tipos.ts`. P2 y P4 suman el enlace «Ver mis logros por SO» (propuesta) y siguen sin porcentajes.
- **Base.** Sin migración (J-26). `abet_app` ya lee `abet.v_r17_por_pi`, `abet.so`, `abet.pi`, `abet.instrumento` y `abet.plan_medicion` (`db/plataforma/neon/crear_rol_app.sql`). El filtro por `carga_id` baja dentro de la vista con `security_barrier` porque su operador es a prueba de fugas, y una tarea lo comprueba con `EXPLAIN`.
- **Pruebas.** pytest-bdd 9 con los dos `.feature` de `specs/004-reportes-docente/aceptacion/`, pruebas unitarias de la ruta y de la función de la meta, la prueba que recorre las rutas registradas, Vitest con Testing Library para P6 y Playwright para la prueba de humo. Las pruebas que crean o borran bases corren en el clúster desechable de `tests/cluster_desechable.py`, nunca en localhost:5432.
- **Despliegue.** Production del Back sale de `main` y la vista previa de `develop` usa la rama `develop` de Neon. Como no hay migración, el despliegue lleva solo código. Toda consulta a Neon, también la de solo lectura de los permisos, corre desde el Windows de Jefferson por Tailscale con `~/.claude/scripts/en_windows.py`.
- **Restricciones.** Solo datos inventados, y `docente.varias@example.invalid` existe solo en las bases desechables. El corte 2 de la spec 001 edita en otra sesión las rutas de carga, `app/permisos.py`, al que suma `puede_reemplazar`, y `docs/01-arquitectura/frontend.md`, así que `feat/004-reportes-docente` sale de `develop` y se rebasa sobre él antes de integrar. La spec 004 no cambia `app/permisos.py`, y si la barra de navegación de `App.tsx` del corte 2 llega antes, el enlace a P6 va en ella.

## Constitution Check

| Principio | Cumplimiento |
| --- | --- |
| I · La base es la única fuente de verdad | Las cifras salen de `abet.v_r17_por_pi`, la misma fuente del R-17, y el Front no calcula porcentajes ni decide la meta |
| II · Privacidad por diseño y solo datos inventados | La ruta trae solo conteos, porcentajes y nombres del catálogo, sin códigos, nombres, correos ni nombres de archivo, y P6 no escribe en el navegador |
| III · Toda carga es atómica y trazable | La ruta solo lee, y una prueba fija que leerla no cambia ninguna tabla |
| IV · Las reglas son datos versionados y lo provisional se ve | P6 lleva la marca PROVISIONAL de cada sección con los textos del R-17, y D-32 a D-34 quedan con su valor provisional |
| V · Contrato, historias auditadas y prueba antes de desplegar | Historias auditadas en la fase 0, reglas, contrato y ADR-008 en la fase 1, pruebas antes del código y P6 en la vista previa antes de `main` |
| VI · Capas y privilegio mínimo | La regla de alcance sigue con un solo dueño, `app/permisos.py`, `abet_app` no gana permisos y cada router con datos exige la sesión |

## Project Structure

```
ABET-ULIMA-Back/
  abet_carga/resultados.py          función pura de la meta y conversión de cifras (nuevo)
  abet_carga/r17.py                 _plan_de_accion usa la función de la meta (cambia)
  app/rutas/resultados.py           GET /api/resultados (nuevo)
  app/rutas/secciones.py, cargas.py, sesion.py   dependencia de sesión por router (cambian)
  app/main.py                       registro del router nuevo (cambia)
  tests/test_api_resultados.py      pruebas unitarias de la ruta (nuevo)
  tests/test_rutas_protegidas.py    recorrido de las rutas registradas (nuevo)
  tests/aceptacion/pasos/test_resultados_feature.py, test_alcance_resultados_feature.py   (nuevos)
  tests/aceptacion/pasos/conftest.py   regla de copia «con la columna X.Y vacía en sus N filas» (cambia)
  specs/004-reportes-docente/       revisión, spec, plan, tareas, aceptación y auditoría (nuevo)
  specs/features/resultados/resultados.spec.md   BR-RESULTADOS-NN (nuevo)
  specs/features/acceso/acceso.spec.md, r17/r17.spec.md, periodo/periodo.spec.md   bloques fechados (cambian)
ABET-ULIMA-Front/
  src/pantallas/MisLogros.tsx       P6 (nuevo)
  src/App.tsx, src/pantallas/MisSecciones.tsx, ResultadoCarga.tsx   vista logros y enlaces (cambian)
  src/servicios/api.ts, tipos.ts    obtenerResultados y su tipo (cambian)
  tests/pantallas/MisLogros.test.tsx   pruebas de P6 (nuevo)
  e2e/humo.spec.ts                  P6 en la vista previa (cambia)
  docs/03-api/contrato.md, docs/specs/api-contracts.md, docs/01-arquitectura/frontend.md, docs/specs/feature-index.md   (cambian)
  docs/00-vision/adr/ADR-008-logros-por-pi-en-el-sistema.md   (nuevo)
```

## Phases

0. **Descubrimiento.** Revisión de los límites que ya existen y de los requisitos de reportes, 22 candidatas desde cuatro ángulos, auditoría con tres lentes y el crítico de arquitectura, spec y aprobación de Jefferson con sus decisiones J-21 a J-28.
1. **Contrato.** Spec viva `resultados` con BR-RESULTADOS-NN, BR-ACCESO-10 y los bloques fechados de `acceso`, `r17` y `periodo`, el contrato definitivo de la ruta 12 en el Front con ADR-008, y los `.feature` definitivos con la regla de copia nueva.
2. **Base.** Sin migración. Comprobación de los permisos de `abet_app` en la base desechable y en la rama `develop` de Neon, en solo lectura.
3. **Backend.** Guardia de sesión por router con su prueba, función de la meta, ruta 12 y pasos de pytest-bdd, con las pruebas primero.
4. **Frontend.** P6, los enlaces de P2 y P4 y sus pruebas de Vitest primero, y la prueba de humo con Playwright.
5. **Pruebas.** Suite completa del Back y del Front, `EXPLAIN` con 150 secciones, revisión previa y comprobación de los mensajes del contrato.
6. **Auditoría.** `audit.md`, Verification fechada en las specs vivas, `MEMORIA.md` y `CHANGELOG.md`.
7. **Despliegue.** PR del Back y del Front con la integración continua en verde, fusión por Jefferson, prueba de humo con P6 en la vista previa de `develop` con la rama `develop` de Neon restablecida y, después, la versión hacia `main`, sin migración.
