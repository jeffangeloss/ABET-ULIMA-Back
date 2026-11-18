# Implementation Plan: Oportunidades de mejora en la carga, con semáforo, declaración y R-17 desde la base

**Branch**: `docs/005-oportunidades-de-mejora` (PR a `develop`), con la implementación en `feat/005-oportunidades-de-mejora` del Back y del Front después de la aprobación | **Date**: 2026-11-18 | **Spec**: [spec.md](./spec.md)

## Summary

El profesor sube su export y ve la constancia en P4, pero ninguna pantalla le dice cómo va su sección en cada indicador de desempeño (performance indicator, PI), el R-17 sale con los recuadros A y B y con la descripción del instrumento vacíos, y el botón atrás sale de la aplicación. El plan agrega la ruta 13, que entrega por carga los conteos por nivel, el logro, la meta y el semáforo, y cambia P4 para mostrar esa tabla, un formulario de causas y acciones con guardado automático y el R-17 solo con la declaración hecha. Las rutas 14 a 16 leen, guardan el borrador con versión y declaran, y la base guarda el borrador y cada declaración. El R-17 escribe desde la base las causas, las acciones y la descripción del instrumento. `App.tsx` navega con el fragmento de la dirección. La prueba de cierre es la 410 en la vista previa de `develop`, con tres PI en rojo, una declaración y un R-17 con A y B.

## Technical Context

- **Backend.** Python 3.12 con FastAPI y psycopg 3, sin dependencias nuevas. La ruta 13 y las rutas 14 a 16 viven en `app/rutas/` (propuesta), cada una con la dependencia de sesión del router. La función pura del semáforo vive en `abet_carga/resultados.py`, junto a la función de la meta de la spec 004, y `abet_carga/r17.py` suma `DeclaracionPendiente`, la lectura de la última declaración, el alto calculado de las filas 31 y 36 y la descripción del instrumento en `_PLAN` y `_bloques`. `app/permisos.py` suma `puede_declarar()`. El comando `python -m abet_carga r17` captura la subclase nueva.
- **Frontend.** React 19 con Vite, TypeScript y Tailwind, sin biblioteca de gráficos. P4 (`src/pantallas/ResultadoCarga.tsx`) suma la sección del semáforo y el formulario. `src/servicios/api.ts` suma `obtenerIndicadores`, `obtenerMejora`, `guardarBorrador` y `declarar`, con sus tipos en `tipos.ts`. `src/App.tsx` guarda cada pantalla en el fragmento de la dirección. P2, P5 y P6 cambian su enlace «Descargar R-17» por un enlace a P4.
- **Base.** Dos migraciones (J-30 y J-31). V1_11 agrega `abet.plan_medicion.descripcion_instrumento` con `ck_plan_medicion_descripcion`. V1_12 crea `abet.mejora_borrador` y `abet.mejora_declaracion` con sus CHECK. `crear_rol_app.sql` da a `abet_app` los permisos exactos y actualiza sus listas de comprobación. Un guion de datos repetible carga la descripción de prueba, y una consulta informativa de solo lectura lista los PI sin descripción. El control Q16 de `db/pruebas/pruebas.sql` busca códigos y correos en las dos tablas.
- **Pruebas.** pytest-bdd 9 con los cuatro `.feature` de `specs/005-oportunidades-de-mejora/aceptacion/`, pruebas unitarias de las rutas, de la función del semáforo y del alto de fila, la prueba que recorre las rutas registradas, Vitest con Testing Library para P4 y la navegación, y Playwright para la prueba de humo. Las pruebas que crean o borran bases corren en el clúster desechable de `tests/cluster_desechable.py`, nunca en localhost:5432.
- **Despliegue.** Production del Back sale de `main` y la vista previa de `develop` usa la rama `develop` de Neon. El orden es el Front primero, tolerante al 404 de la ruta 13, y después la migración, `crear_rol_app.sql` sin APP_DB_CLAVE, la consulta de solo lectura de los permisos y el código del Back (J-37). Toda modificación y toda consulta a Neon corren desde el Windows de Jefferson por Tailscale con `~/.claude/scripts/en_windows.py`.
- **Restricciones.** Solo datos inventados. La implementación sale de `develop` después de fusionar los PR de la spec 004, porque las dos specs tocan `r17.py`, `ResultadoCarga.tsx`, `App.tsx`, `api.ts`, `tipos.ts`, `conftest.py`, `r17.spec.md`, `contrato.md`, `frontend.md` y `e2e/humo.spec.ts`. La documentación de la spec 005 puede avanzar antes. US-51 y V1_11 no dependen de la spec 004 y pueden ir primero en su propia rama si Jefferson lo pide. La spec 002 nombra una V1_10 propia que ya choca con la de `develop`, y V1_11 y V1_12 quedan reservadas en la memoria de las dos sesiones.

## Constitution Check

| Principio | Cumplimiento |
| --- | --- |
| I · La base es la única fuente de verdad | Cada cifra del semáforo sale de `abet.v_r17_por_pi`, la misma fuente del R-17, y el borrador, la declaración y la descripción del instrumento viven en la base. El Front no calcula porcentajes ni decide el color |
| II · Privacidad por diseño y solo datos inventados | La declaración rechaza códigos y correos con el mismo patrón en la ruta y en la base, las respuestas llevan `no-store`, y P4 no escribe en `localStorage` ni en `sessionStorage`. Un nombre de estudiante no se detecta, y Jefferson acepta ese riesgo por aviso (J-36) |
| III · Toda carga es atómica y trazable | La subida no escribe el borrador, porque la herencia ocurre al leer. La declaración es de solo INSERT con quien declaró y cuándo, y el R-17 lee la última en una instantánea |
| IV · Las reglas son datos versionados y lo provisional se ve | El corte rojo sale de `abet.parametro_valor`, la franja provisional se ve sobre la tabla de P4, y D-35 a D-37 quedan con su valor provisional |
| V · Contrato, historias auditadas y prueba antes de desplegar | Historias auditadas en la fase 0, reglas, contrato y ADR-009 en la fase 1, pruebas antes del código y la prueba de humo en la vista previa antes de `main` |
| VI · Capas y privilegio mínimo | `puede_declarar()` tiene un solo dueño en `app/permisos.py`, `abet_app` recibe INSERT y UPDATE por columnas exactas en el borrador e INSERT en la declaración, y no escribe la descripción del instrumento |

## Project Structure

```
ABET-ULIMA-Back/
  db/migration/V1_11__descripcion_instrumento.sql           columna y CHECK en abet.plan_medicion (nuevo, propuesta)
  db/migration/V1_12__mejora_borrador_y_declaracion.sql     dos tablas y sus CHECK (nuevo, propuesta)
  db/plataforma/neon/crear_rol_app.sql                      permisos y listas exactas (cambia)
  db/datos/descripcion_instrumento_2026_2.sql               UPDATE repetible con textos de prueba (nuevo, propuesta)
  db/plataforma/neon/                                       consulta informativa de PI sin descripción (nuevo)
  db/pruebas/pruebas.sql                                    Q16, códigos y correos en las dos tablas (cambia)
  abet_carga/resultados.py                                  función pura del semáforo (cambia, de la spec 004)
  abet_carga/r17.py                                         DeclaracionPendiente, B29, B34, alto de fila y G17:I19 (cambia)
  abet_carga/__main__.py                                    el comando captura la subclase nueva (cambia)
  app/permisos.py                                           puede_declarar() (cambia)
  app/rutas/                                                rutas 13 a 16 (nuevo)
  tests/                                                    pruebas unitarias, pasos de pytest-bdd, declarar(), reglas de copia (nuevo y cambia)
  specs/005-oportunidades-de-mejora/                        revisión, spec, plan, tareas y aceptación (nuevo)
  specs/features/mejora/mejora.spec.md                      BR-MEJORA-NN (nuevo, propuesta)
  specs/features/r17/r17.spec.md                            BR-R17-04, BR-R17-11 y BR-R17-12 (cambia)
ABET-ULIMA-Front/
  src/pantallas/ResultadoCarga.tsx                          semáforo, formulario y R-17 solo con declaración (cambia)
  src/pantallas/MisSecciones.tsx, Cargas.tsx, MisLogros.tsx enlaces a P4 en lugar de «Descargar R-17» (cambian)
  src/App.tsx                                               navegación con el fragmento de la dirección (cambia)
  src/servicios/api.ts, tipos.ts                            llamadas a las rutas 13 a 16 y sus tipos (cambian)
  tests/                                                    pruebas de P4 y de la navegación, y reinicio del fragmento en preparar.ts (cambian)
  e2e/humo.spec.ts                                          semáforo, declaración y descarga en la vista previa (cambia)
  docs/03-api/contrato.md, docs/specs/api-contracts.md, docs/01-arquitectura/frontend.md, docs/specs/feature-index.md   (cambian)
  docs/00-vision/adr/ADR-009-declaracion-en-el-sistema.md   (nuevo, propuesta)
```

## Phases

0. **Descubrimiento.** Revisión de los límites que ya existen y de los requisitos de la carrera, 15 candidatas, auditoría con tres lentes y el crítico de arquitectura, y spec, plan y tareas del borrador. Queda la aprobación de Jefferson con sus decisiones J-29 a J-37 y la consulta a la Coordinación de D-34 a D-37.
1. **Contrato.** Specs vivas `r17` (BR-R17-04, BR-R17-11 y BR-R17-12) y `mejora` (BR-MEJORA-NN), contrato definitivo de las rutas 13 a 16 y ADR-009 en el Front, y los `.feature` definitivos con la infraestructura de prueba de FR-017.
2. **Base.** V1_11 con pruebas en el clúster desechable, V1_12 con `crear_rol_app.sql`, el guion de la descripción y la consulta informativa. Después, desde el Windows de Jefferson, la consulta de solo lectura de las cargas publicadas sin declaración, la migración de `develop` y el guion de la descripción.
3. **Backend.** Función del semáforo, ruta 13, rutas 14 a 16 con `puede_declarar()`, `DeclaracionPendiente`, B29 y B34 con el alto calculado, G17:I19, herencia al leer, ayudante `declarar()`, pasos de pytest-bdd y Q16, con las pruebas primero.
4. **Frontend.** Llamadas y tipos, semáforo en P4, formulario con guardado automático, R-17 solo desde P4, navegación con el fragmento, 401 sin perder el texto y prueba de humo, con las pruebas de Vitest primero.
5. **Auditoría.** `audit.md` con el cruce de historia, escenario, prueba y resultado, y la línea Verification fechada en las specs vivas.
6. **Despliegue.** El Front primero, el Back en la vista previa, la prueba de humo, la migración de la rama principal de Neon y el guion de la descripción, y la versión hacia `main`.

## Riesgos

- **Choque con la spec 004.** Las dos specs tocan los mismos archivos y la 005 cambia FR-016, el invariante 8 de ADR-008 y las pruebas de P4 sin porcentajes. Se mitiga con la implementación después de la fusión de la spec 004 y con el cambio escrito en J-35.
- **R-17 con 409 para toda carga anterior.** La 410 y la 411 de la vista previa y de Production quedan sin R-17 hasta declarar. Se mitiga con el Front primero, la consulta de solo lectura de las cargas afectadas y la declaración previa a cada descarga de `e2e/humo.spec.ts` (J-37).
- **Permisos antes que el código.** Con el código del Back antes de los permisos de `abet_app`, P4 recibe 500. Se mitiga con el orden migración, `crear_rol_app.sql`, comprobación y código.
- **Texto largo en celdas combinadas.** Excel no ajusta el alto de las celdas combinadas, y las filas 29 a 31 comparten la tabla K28:Q31. Se mitiga con el alto calculado de forma determinista de las filas 31 y 36 y con una prueba que conserva K31:Q31.
- **Datos personales en texto libre.** Un nombre de estudiante no se detecta. Se mitiga con la nota de P4, el rechazo de códigos y correos, el control Q16 y la aceptación explícita de Jefferson (J-36) antes de los datos reales.
- **Pérdida del texto del profesor.** Dos pestañas, un reemplazo o un 401 pueden descartar lo escrito. Se mitigan con la versión del borrador, el 409 con el texto guardado y `reemplazada_por`, y la pantalla que sigue montada bajo el ingreso (AD-19, AD-22 y AD-27).
- **Colisión de migraciones.** La spec 002 nombra una V1_10 que ya existe en `develop`. Se mitiga reservando V1_11 y V1_12 en la memoria de las dos sesiones.
- **Pruebas que se rompen.** El R-17 con declaración obligatoria cambia 26 llamadas de prueba y los escenarios 1 a 4 de US-15. Se mitiga con el ayudante `declarar()` y con el cambio escrito en US-49.
