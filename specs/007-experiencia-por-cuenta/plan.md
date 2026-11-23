# Implementation Plan: Lo importante para cada cuenta y en cada momento del registro

**Branch**: `docs/007-experiencia-por-cuenta` del Back y del Front (PR a `develop`), con la implementación en `feat/007-experiencia-por-cuenta` después de la aprobación | **Date**: 2026-11-22 | **Spec**: [spec.md](./spec.md)

## Summary

El profesor y la coordinación ven hoy las mismas pantallas con los mismos textos, y ninguna dice lo que falta en cada momento del registro. El plan cambia en una etapa A, en el código del Front, la fila de cada sección de P2 del profesor, que suma una línea con lo que falta y el caso de la última carga rechazada (US-59), el apartado «Antes de subir» de P3 con los nombres de columna de D-43 (US-60), el párrafo «Qué corregir» de P4 de una carga rechazada (US-61), el texto falso de P4 tras un reemplazo rechazado (US-62) y los rótulos por rol de la cabecera con el menú que marca la pantalla actual (US-63). En una etapa B agrega la ruta 17 `GET /api/avance` para la coordinación, con la etapa de cada sección derivada en cada lectura (US-64), la pantalla P7 «Avance del registro» como página de entrada del coordinador (US-65) y los correos de los profesores de las secciones que faltan, con su copia al portapapeles (US-66, que espera a D-47). No hay migración.

## Technical Context

- **Front.** React con Vite, TypeScript y Tailwind, la pila de la versión 0.2.0. La etapa A toca `src/pantallas/MisSecciones.tsx`, `SubirExport.tsx`, `ResultadoCarga.tsx`, `Cargas.tsx` y `MisLogros.tsx`, `src/App.tsx` y dos módulos nuevos de `src/servicios/`, uno con la combinación de las rutas 4 y 8 (J-45) y otro con los textos de «Antes de subir» y de «Qué corregir» (J-43 y J-44). La etapa B agrega `src/pantallas/Avance.tsx`, la vista «avance», `pantallaDeLlegada(usuario)` (J-46), el tipo de la ruta 17 en `src/servicios/tipos.ts` y su función en `src/servicios/api.ts`, la única puerta a la API.
- **Back.** Solo en la etapa B. Python 3.12 con FastAPI. `app/rutas/avance.py` (nueva) con el router que exige la sesión, como `app/rutas/secciones.py`, `puede_ver_avance()` en `app/permisos.py` y la consulta de la etapa en `abet_carga/avance.py` (nueva, propuesta), que parte de `secciones_visibles()` y lee `abet.plan_medicion`, `abet.carga`, `acceso.docente_seccion` y `acceso.usuario_autorizado` con la precedencia de J-48. La ruta se registra en `app/main.py` y en la lista de `tests/rutas_registradas.py`.
- **Base.** Sin migración, sin cambios en `crear_rol_app.sql` y con Q01 a Q15 sin cambios. `abet_app` ya lee todas las tablas que usa la ruta 17.
- **Contrato.** La sección 14 nueva de `docs/03-api/contrato.md` del Front describe la ruta 17 (propuesta) y la sección 10 suma su camino a la cuenta de la comprobación con OpenAPI cuando llegue la etapa B. El índice `docs/specs/api-contracts.md` suma la ruta en la misma fase.
- **Pruebas.** Vitest y Testing Library en el Front para los 29 escenarios `@delegado_a_vitest`, con `simularApi` de `tests/respuestas.ts` y el portapapeles simulado. pytest-bdd 9 en el Back para los escenarios de la ruta 17, en el clúster desechable de `tests/cluster_desechable.py`, con un ayudante nuevo de `tests/cargas_de_prueba.py` que siembra las secciones 410 a 417 con sus cargas (propuesta), y para el esquema del lector de US-60, sin base, en `antes_de_subir.feature`, que no tiene Antecedentes. Los escenarios `@delegado_a_vitest` escriben la sesión con «una sesión de "…" con rol "…"» (o «la cuenta "…" con rol "…"»), un texto que la expresión `_sesion_iniciada` de `tests/aceptacion/pasos/conftest.py` no captura. Ese paso lo atiende `_pantalla_dada` de `test_experiencia_por_cuenta_feature.py`, que solo llama a `_delegar()`, como `test_resultados_feature.py`, así que ningún paso de esos escenarios abre la base, inicia una sesión ni pide la API. Una prueba de `tests/aceptacion/pasos/test_lectura_gherkin_es.py` fija los 35 escenarios y 70 casos de la spec, como la de la spec 006.
- **Humo.** Playwright para Node en `e2e/`, contra Vite y la API local, con las contraseñas del archivo de `ABET_CLAVES_ARCHIVO`. La etapa A suma a `e2e/humo.spec.ts` la línea de P2 y el apartado «Antes de subir» de P3 del profesor. La etapa B suma la llegada del coordinador a P7, que necesita su contraseña en ese archivo y cambia `ingresar()` de `e2e/comun.ts`, que hoy espera siempre «Mis secciones».
- **Datos.** Solo datos inventados, con correos de `@example.invalid` y códigos de 99000000 a 99999999. Ningún export nuevo entra a `tests/datos_inventados/`.
- **Restricciones.** Una sola línea de trabajo, en el orden spec 006, etapa A, núcleo de la spec 005 y etapa B (FR-016). La spec 006 está construida, sin commit y a la espera de su corrida en Neon, y el núcleo de la spec 005 no tiene código. La spec 005 reescribe `ResultadoCarga.tsx` con US-45 a US-49 y `App.tsx` con US-52, así que US-61 y US-62 tocan solo la rama de una carga que no está PUBLICADA, y J-46 deja `pantallaDeLlegada()` lista para que US-52 la reutilice.

## Constitution Check

| Principio | Cumplimiento |
| --- | --- |
| I · La base es la única fuente de verdad | La etapa de cada sección se deriva de `abet.carga`, `abet.plan_medicion` y `acceso.docente_seccion` en cada lectura y no se guarda (J-48). El Front no decide la etapa de P7 ni el `en_meta` de ninguna pantalla |
| II · Privacidad por diseño y solo datos inventados | La ruta 17 no trae datos de estudiantes ni nombres, y los correos de profesores llegan solo a la cuenta COORDINADOR y solo en las secciones que faltan (D-47). P7 no guarda nada en el navegador y la aplicación no envía correos |
| III · Toda carga es atómica y trazable | La spec no cambia la carga, el reemplazo ni la constancia, y P4 sigue mostrando todos sus campos (US-16) |
| IV · Las reglas son datos versionados y lo provisional se ve | Los nombres de columna siguen el valor provisional de D-43 en una constante (J-44), y los textos nuevos llevan «(propuesta)» hasta su aprobación |
| V · Contrato, historias auditadas y prueba antes de desplegar | 18 candidatas auditadas con tres lentes y el crítico, contrato de la ruta 17 y reglas BR-AVANCE y BR-ACCESO-12 antes del código, pruebas primero y humo con Playwright |
| VI · Capas y privilegio mínimo | `abet_app` no gana permisos. `puede_ver_avance()` vive en `app/permisos.py`, el único dueño de la visibilidad, y el Front habla con la API solo por `src/servicios/api.ts` |

## Project Structure

```
ABET-ULIMA-Back/
  specs/007-experiencia-por-cuenta/        revisión, spec, plan, tareas y aceptación (nuevo)
  specs/features/avance/avance.spec.md      BR-AVANCE-01 a BR-AVANCE-NN (nuevo, etapa B, propuesta)
  specs/features/acceso/acceso.spec.md      BR-ACCESO-12 (cambia, etapa B)
  app/rutas/avance.py                       ruta 17 (nuevo, etapa B)
  app/permisos.py                           puede_ver_avance() (cambia, etapa B)
  abet_carga/avance.py                      consulta de la etapa con la precedencia de J-48 (nuevo, etapa B)
  app/main.py                               registro del router (cambia, etapa B)
  tests/rutas_registradas.py                ruta 17 en la lista (cambia, etapa B)
  tests/cargas_de_prueba.py                 ayudante de las secciones 410 a 417 con sus cargas (cambia, etapa B)
  tests/aceptacion/pasos/test_experiencia_por_cuenta_feature.py, test_avance_feature.py   (nuevos)
  tests/aceptacion/pasos/test_lectura_gherkin_es.py   conteo de la spec 007 (cambia)

ABET-ULIMA-Front/
  src/servicios/secciones_del_profesor.ts   combinación de las rutas 4 y 8 (nuevo, etapa A, propuesta)
  src/servicios/ayudas.ts                   «Antes de subir» y «Qué corregir» (nuevo, etapa A, propuesta)
  src/pantallas/MisSecciones.tsx, SubirExport.tsx, ResultadoCarga.tsx, Cargas.tsx, MisLogros.tsx   (cambian, etapa A)
  src/App.tsx                               nav, aria-current, rótulos por rol y, en la etapa B, P7 y pantallaDeLlegada()
  src/pantallas/Avance.tsx                  P7 (nuevo, etapa B)
  src/servicios/api.ts, tipos.ts            ruta 17 (cambian, etapa B)
  tests/                                    pruebas de Vitest de cada escenario @delegado_a_vitest
  e2e/humo.spec.ts, e2e/comun.ts            humo de la etapa A y de la etapa B
  docs/01-arquitectura/frontend.md          sección 11 de la spec 007 (propuesta)
  docs/03-api/contrato.md, docs/specs/api-contracts.md   ruta 17 (propuesta)
  docs/specs/feature-index.md               fila de la feature avance (propuesta)
```

## Phases

0. **Descubrimiento.** Candidatas desde tres ángulos, auditoría con tres lentes y el crítico (`revision-historias.md`), spec y `.feature` leídos por el analizador de pytest-bdd, y aprobación de Jefferson con J-43 a J-48. Pedido de D-46 y D-47 a la Coordinación.
1. **Contrato.** Etapa A sin reglas `BR-`, con sus textos en `frontend.md`. Etapa B con la spec viva `avance`, BR-ACCESO-12, la sección 14 del contrato y su índice, y los `.feature` definitivos.
2. **Base.** Sin migración. El ayudante de las secciones de prueba de la etapa B.
3. **Back.** Solo en la etapa B. Pruebas primero, `puede_ver_avance()`, la consulta de la etapa, la ruta 17 y el campo `profesores`.
4. **Front.** Pruebas de Vitest primero. La etapa A va justo después de la spec 006 y antes del núcleo de la spec 005, con el mínimo de antes del registro del 30-11-2026 en el orden US-60, US-59 y US-61, y con US-62 y US-63 como extras si caben. US-61 y US-62 entran sobre `develop` si la primera etapa de J-41 de la spec 005 no está fusionada. La etapa B, con P7, la llegada y los correos, va en la semana 16, si cabe.
5. **Pruebas y humo.** Suite completa del Back y del Front, `bash scripts/preflight.sh` en los dos y el humo con Playwright de cada etapa.
6. **Auditoría.** `audit.md` con el cruce de historia, escenario, prueba y resultado, Verification fechada en las specs vivas, `MEMORIA.md` y `CHANGELOG.md`.
7. **Despliegue.** Vista previa con el humo, y Production solo con el permiso de Jefferson. La etapa A puede salir sola, antes de la etapa B, con al menos el mínimo de US-60, US-59 y US-61.

## Riesgos

- La spec 005 reescribe P4 en la misma línea de trabajo. US-61 y US-62 se limitan a la rama de una carga que no está PUBLICADA, y si la primera etapa de J-41 no se fusiona antes, se construyen sobre `develop` y se reconcilian al fusionar.
- La ruta 8 sin `seccion_id` trae todas las cargas visibles del periodo en una sola petición. Para un profesor con pocas secciones el tamaño es pequeño, y la ruta 17 lo reemplaza con `ultima_rechazada_id` (J-45).
- Si la carrera cierra D-43 con otro nombre antes del registro, US-60 y US-61 cambian solo la constante de J-44.
- Si la Coordinación responde que no a D-47, US-66 sale de la etapa B sin tocar US-64 ni US-65.
- La spec no tiene todavía una estimación por tarea, así que no promete fechas. Antes de Production faltan la aprobación de la spec, las pruebas de Vitest del mínimo y el permiso de Jefferson, y quedan ocho días hasta el 30-11-2026. Por eso la etapa A no espera al núcleo de la spec 005, el mínimo se limita a US-60, US-59 y US-61, y la etapa B queda para la semana 16, si cabe.
