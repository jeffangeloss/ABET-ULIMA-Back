# Implementation Plan: El export real de Blackboard en .xlsx, .csv y .xls

**Branch**: `docs/003-exports-blackboard` (PR a `develop`), con la implementación en `feat/003-exports-blackboard` | **Date**: 2026-11-09 | **Spec**: [spec.md](./spec.md)

## Summary

El export real de la sección 410 de 450002 llega en tres formatos y con columnas «ABET SO5.1 [Total Pts: 100 Score] |1629477», y hoy no se carga en ninguno. El `.csv` y el `.xls` de texto se detienen por su extensión, el `.xlsx` queda RECHAZADO con PI_DEL_PLAN_AUSENTE porque el lector solo reconoce «5.1 [», y la base rechazaría ese encabezado con `ck_carga_columna_encabezado` aunque el lector lo aceptara. El plan agrega al lector una ruta de texto que entrega las mismas filas que el libro, amplía el reconocimiento del encabezado en el lector y en la base con la misma regla (V1_10), acepta el nivel escrito «3.00», toma la sección del nombre del export de texto y cierra la revisión previa para los textos UTF-16. La prueba de cierre es la carga del `.csv` y del `.xls` inventados en la vista previa de `develop` contra la rama `develop` de Neon, con 11 de 11 filas aceptadas y 63,6 / 63,6 / 72,7 %.

## Technical Context

- **Backend.** Python 3.12, la biblioteca `abet_carga` y FastAPI, sin dependencias nuevas. La ruta de texto usa `codecs` y `csv` de la biblioteca estándar, sin pandas ni `csv.Sniffer`, y conserva el orden de BR-CARGA-03 y el tope de 1 MB. `csv` de Python 3.12 acepta el byte nulo, así que el lector lo rechaza antes de leer.
- **Frontend.** P3 (`src/pantallas/SubirExport.tsx`) cambia su `accept`, su etiqueta y su aviso, y P4 (`src/pantallas/ResultadoCarga.tsx`) muestra la hoja nula de un export de texto. `src/servicios/tipos.ts` declara `hoja: string | null`.
- **Base.** `V1_10` reemplaza `ck_carga_columna_encabezado` por la regla de J-19 con clases de letras explícitas y espacios ASCII, para que PostgreSQL y Python acepten exactamente lo mismo. La regla C6 de V1_07 se conserva y el caso R26 de `db/pruebas/pruebas.sql` sigue fallando. Si D-31 rechaza el export sin niveles, V1_10 suma su motivo a `ck_rechazo_fila_motivo`.
- **Pruebas.** pytest con las pruebas unitarias del lector y de la validación, pytest-bdd 9 con `specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`, los casos nuevos de `db/pruebas/pruebas.sql`, los de `scripts/probar_preflight.sh` y Vitest en el Front. Las pruebas que crean o borran bases corren en el clúster desechable de `tests/cluster_desechable.py`, nunca en localhost:5432.
- **Despliegue.** Production del Back sale de `main` y la vista previa de `develop` usa la rama `develop` de Neon (comprobado con la CLI de Vercel el 2026-11-09). Toda escritura en Neon corre desde el Windows de Jefferson por Tailscale, con `~/.claude/scripts/en_windows.py`, y los ayudantes de la marca, de las contraseñas y de la prueba de humo viven en `ABET_SIS_MED/herramientas_neon/`, fuera de `/tmp`.
- **Restricciones.** Solo datos inventados. De los exports reales de `~/Downloads` se usa solo su forma, descrita en la nota de análisis, y nadie los abre ni los copia.

## Constitution Check

| Principio | Cumplimiento |
| --- | --- |
| I · La base es la única fuente de verdad | El lector y `ck_carga_columna_encabezado` aplican la misma regla, y V1_10 entra como migración nueva sin editar V1_07 |
| II · Privacidad por diseño y solo datos inventados | La ruta de texto descarta las mismas columnas que el libro, la revisión previa lee el UTF-16 y los datos nuevos son inventados |
| III · Toda carga es atómica y trazable | La ruta de texto no cambia la transacción, la huella se calcula sobre los bytes con su BOM y `archivo_origen.hoja` queda nulo |
| IV · Las reglas son datos versionados y lo provisional se ve | D-02, D-03, D-30 y D-31 quedan con su valor provisional y el R-17 sigue con la franja |
| V · Contrato, historias auditadas y prueba antes de desplegar | Historias auditadas en la fase 0, reglas y contrato en la fase 1, pruebas antes del código y prueba en la vista previa antes de `main` |
| VI · Capas y privilegio mínimo | `abet_carga` sigue sin FastAPI, y `abet_app` no gana permisos |

## Project Structure

```
ABET-ULIMA-Back/
  abet_carga/lector.py              tipo por contenido, ruta de texto y encabezado de PI (cambia)
  abet_carga/validacion.py          sección por el nombre del texto y nivel «3.00» (cambia)
  abet_carga/modelos.py             textos de MotivoIlegible y hoja opcional (cambia)
  abet_carga/carga.py, constancia.py, r17.py   hoja nula (cambian)
  db/migration/V1_10__encabezado_pi_con_prefijo.sql   (nuevo)
  db/pruebas/pruebas.sql            casos de V1_10 (cambia)
  scripts/preflight.sh, probar_preflight.sh   regla 2 con UTF-16 (cambian)
  scripts/generar_exports_inventados.py   exports de texto con los encabezados reales (cambia)
  tests/datos_inventados/           cuatro exports nuevos (nuevo)
  tests/aceptacion/pasos/test_exports_blackboard_feature.py   (nuevo)
  specs/003-exports-blackboard/     spec, revisión, plan, tareas, aceptación y auditoría (nuevo)
ABET-ULIMA-Front/
  src/pantallas/SubirExport.tsx, ResultadoCarga.tsx, src/servicios/tipos.ts   (cambian)
  docs/03-api/contrato.md, docs/specs/api-contracts.md, docs/01-arquitectura/frontend.md   (cambian)
```

## Phases

0. **Descubrimiento.** Nota de análisis del 2026-11-09, candidatas, auditoría con tres lentes y el crítico de arquitectura, spec y aprobación de Jefferson con sus decisiones.
1. **Contrato.** Bloques fechados en las specs vivas de la carga y del R-17, contrato del Front, `.feature` definitivo y los cuatro exports inventados con el generador.
2. **Base.** V1_10 con sus casos en `pruebas.sql`, probada en el clúster desechable.
3. **Backend.** Lector, validación, constancia y R-17, con las pruebas unitarias primero.
4. **Frontend.** P3, P4 y sus pruebas.
5. **Pruebas.** Pasos de `exports_blackboard.feature`, escenarios de la spec 001 con sus textos nuevos, revisión previa y suite completa.
6. **Auditoría.** `audit.md`, Verification fechada en las specs vivas, `MEMORIA.md` y `CHANGELOG.md`.
7. **Despliegue.** PR del Back y del Front con la integración continua en verde, fusión por Jefferson, rama `develop` de Neon restablecida, migrada a 1.10, marcada con preview y con contraseñas, y prueba en la vista previa con el `.csv` y el `.xls`. V1_10 en la rama principal queda para la versión hacia `main`.
