# Audit: El export real de Blackboard en .xlsx, .csv y .xls

**Fecha**: 2026-11-09  
**Spec**: [spec.md](./spec.md)  
**Plan**: [plan.md](./plan.md)  
**Comando**: `uv run --frozen --no-build pytest -q` en el Back, `bash db/pruebas/correr_pruebas.sh` sobre el clúster desechable de `db/pruebas/cluster_desechable.sh`, `bash scripts/probar_preflight.sh` y `bash scripts/preflight.sh` en el Back, y `npm test` y `npm run build` en el Front  
**Resultado**: suite completa del Back, 1180 passed y 19 skipped in 124.87s (0:02:04), con los 104 casos de `exports_blackboard.feature` aprobados; pruebas de la base, «ok 65/65 casos de rechazo» y «RESULTADO: todo pasó»; revisión previa, 46 casos bien y 0 mal; Vitest del Front, 9 archivos y 85 pruebas aprobadas, y la compilación sin errores  
**Estado**: Spec 003 fusionada en `develop` (Back e56fb8a, Front c2f3523) y probada en la vista previa de `develop` contra la rama `develop` de Neon, en V1_10. Falta V1_10 en la rama principal antes de la versión hacia `main` (T077).

Esta auditoría cruza cada historia de usuario (user story, US) de la spec 003 con sus escenarios en Gherkin, la prueba que los ejecuta y su resultado del 2026-11-09. Las 19 pruebas omitidas de la suite son los escenarios del corte 2 de la spec 001 y no tocan esta spec. Los escenarios de US-33 los comprueban las pruebas de Vitest del Front (`tests/pantallas/SubirExport.test.tsx`), y el de US-35, los casos de `scripts/probar_preflight.sh`, que la integración continua corre antes de pytest. Los pasos de esos escenarios dejan la propiedad «delegado_a_vitest» o «delegado_a_preflight» con el nombre de la prueba que los cubre, y el resumen de pytest los lista.

## Resumen

| Conjunto | Escenarios | Casos | Aprobados | Omitidos | Pendientes |
| --- | --- | --- | --- | --- | --- |
| Spec 003 (US-26 a US-36) | 39 | 104 | 104 | 0 | 0 |

## Historias

Los escenarios viven en `specs/003-exports-blackboard/aceptacion/exports_blackboard.feature` y sus pasos en `tests/aceptacion/pasos/test_exports_blackboard_feature.py`, con los comunes en `tests/aceptacion/pasos/conftest.py`.

| Historia | Escenario | Casos | Resultado |
| --- | --- | --- | --- |
| US-26 | El .xlsx con los encabezados reales queda publicado | 1 | aprobado |
| US-26 | Los exports de la spec 001 dan las mismas cifras con el lector nuevo | 2 | aprobado |
| US-26 | Qué encabezados son de un PI | 14 | aprobado |
| US-26 | La base acepta o rechaza el encabezado de la columna del PI 5.1 | 8 | aprobado |
| US-26 | El lector y la base aceptan los mismos encabezados | 1 | aprobado |
| US-26 | Dos columnas del mismo PI con distinta escritura rechazan la carga | 1 | aprobado |
| US-26 | Las columnas del SO 4 se ignoran con aviso y sin leer sus valores | 1 | aprobado |
| US-27 | El .csv inventado de la 410 queda publicado entero | 1 | aprobado |
| US-27 | Las variantes del texto del .csv se leen igual | 7 | aprobado |
| US-27 | Una línea vacía entre filas con datos cuenta como fila | 1 | aprobado |
| US-27 | Un salto de línea dentro de comillas no cambia la numeración | 1 | aprobado |
| US-27 | Un defecto de estructura en el .csv rechaza la carga entera | 3 | aprobado |
| US-27 | Un código que no es inventado en el .csv detiene el archivo | 1 | aprobado |
| US-27 | La huella del .csv incluye su BOM | 1 | aprobado |
| US-27 | El mismo .csv otra vez devuelve su constancia | 1 | aprobado |
| US-27 | El mismo .csv publicado en la 410 no entra en la 411 | 1 | aprobado |
| US-28 | El .xls de texto inventado de la 410 queda publicado entero | 1 | aprobado |
| US-28 | Las variantes del .xls se leen igual | 4 | aprobado |
| US-28 | El .xls con las mismas notas que el .csv es otro archivo | 1 | aprobado |
| US-28 | Un código que no es inventado en el .xls detiene el archivo | 1 | aprobado |
| US-28 | Los nombres y las actividades del .xls no llegan a ninguna tabla | 1 | aprobado |
| US-29 | El texto de un nivel en el PI 5.2 de la fila 3 | 9 | aprobado |
| US-29 | El texto de un nivel dentro de un .xlsx | 3 | aprobado |
| US-29 | Un nivel con miles de cifras no deja la carga en 500 | 1 | aprobado |
| US-30 | La sección sale del nombre del archivo de texto | 6 | aprobado |
| US-30 | Un .xlsx sin sección en la hoja ni en el nombre recibe el texto nuevo | 1 | aprobado |
| US-31 | Un archivo que no es un export admitido se detiene sin rastro | 7 | aprobado |
| US-32 | Un texto dañado o armado a mano se detiene sin rastro | 12 | aprobado |
| US-32 | El orden de BR-CARGA-03 se mantiene con un export de texto | 2 | aprobado |
| US-32 | La guardia va antes que la carga publicada de la sección | 1 | aprobado |
| US-33 | El selector de P3 admite los tres formatos | 1 | aprobado, delegado a Vitest del Front |
| US-33 | Sin archivo, P3 pide el export en los tres formatos | 1 | aprobado, delegado a Vitest del Front |
| US-33 | P3 envía el archivo tal cual y la API decide | 1 | aprobado, delegado a Vitest del Front |
| US-34 | La constancia del .csv no inventa una hoja | 1 | aprobado |
| US-34 | La constancia del .xlsx sigue mostrando su hoja | 1 | aprobado |
| US-35 | La revisión previa lee el contenido antes de contar los códigos | 1 | aprobado, delegado a `scripts/probar_preflight.sh` |
| US-36 | Un export sin ningún nivel en los PI del plan no se publica | 1 | aprobado |
| US-36 | Un solo nivel basta para publicar | 1 | aprobado |
| US-36 | La sección queda libre para el export con niveles | 1 | aprobado |

## Pruebas unitarias y de la base

| Archivo | Lo que cubre | Resultado |
| --- | --- | --- |
| `tests/test_lector.py` | precedencia de firmas, cada detalle de la lista cerrada, saltos y comillas, topes de filas, columnas, campos y celdas, la lista común de `tests/encabezados_de_pi.py` y el corte a 200 caracteres | aprobado |
| `tests/test_validacion.py` | nombre `.csv` y `.xls`, hoja nula, nivel con decimales nulos y tope de cifras, SIN_CALIFICACIONES | aprobado |
| `tests/test_carga.py`, `tests/test_api_cargas.py`, `tests/test_constancia.py` y `tests/test_r17.py` | hoja nula, el detalle en el registro, el nombre con un carácter de control, SIN_CALIFICACIONES y «Sin hoja (export de texto)» | aprobado |
| `tests/test_generador_exports.py` | los cuatro exports nuevos, sus 31 columnas, sus cifras y que solo traen códigos 99 y números de columna inventados | aprobado |
| `tests/test_base_desechable.py` y `db/pruebas/pruebas.sql` | V1_10, con R63 a R65 que deben fallar y A09 y A10 que deben pasar, y R26 y R60 sin cambio | aprobado |
| `scripts/probar_preflight.sh` | la regla 2 por contenido, los contenedores OLE, los textos UTF-16 y Windows-1252 y los nombres que no son ASCII | 46 bien, 0 mal |

## Requisitos funcionales

| FR | Estado | Evidencia |
| --- | --- | --- |
| FR-001 | Cumplido | US-27, US-28 y US-31 en `exports_blackboard.feature`; `tests/test_lector.py` |
| FR-002 | Cumplido | US-27, escenarios 2 a 4, y US-32; `tests/test_lector.py` |
| FR-003 | Cumplido | US-32, escenario 1, y los topes de `tests/test_lector.py`, con el de celdas de la revisión de seguridad |
| FR-004 | Cumplido | US-26, escenarios 3 y 5 |
| FR-005 | Cumplido | US-26, escenarios 4 y 5; R63 a R65 y A09 de `pruebas.sql` |
| FR-006 | Cumplido | US-29 |
| FR-007 | Cumplido | US-27, escenario 1, y US-30 |
| FR-008 | Cumplido | US-34 y las pruebas de P4 del Front |
| FR-009 | Cumplido | US-33 y `tests/pantallas/SubirExport.test.tsx` del Front |
| FR-010 | Cumplido | US-35 y `scripts/probar_preflight.sh` |
| FR-011 | Cumplido | `tests/test_generador_exports.py` |
| FR-012 | Cumplido | bloques fechados de `carga-export.spec.md` y `r17.spec.md` y el contrato del Front (9467f29) |
| FR-013 | Cumplido | `carga.feature` con los textos nuevos; la suite completa en verde |
| FR-014 | Cumplido en `develop` | T073 y T074; la rama principal queda para T077 |
| FR-015 | Cumplido | `MEMORIA.md` y `CHANGELOG.md` en cada commit; la revisión previa sin fallas |

## Criterios de éxito

| SC | Estado | Evidencia |
| --- | --- | --- |
| SC-001 | Cumplido en local | US-26, escenario 1; US-27, escenario 1; US-28, escenario 1 |
| SC-002 | Cumplido en local | 104 de 104 casos de la spec 003 y la suite completa sin fallas |
| SC-003 | Cumplido en local | US-31 y US-32 y los casos de la revisión de seguridad en `tests/test_lector.py` |
| SC-004 | Cumplido | T076: Playwright da 2 passed, y Neon `develop` tiene la 410 (.csv) y la 411 (.xls) PUBLICADA con 11 de 11 y 63,6 / 63,6 / 72,7 %, con Q01 a Q14 en 0 |
| SC-005 | Cumplido en local | `tests/test_generador_exports.py` y la regla 2 de la revisión previa |

## Revisión de seguridad

Un subagente con el modelo de la sesión y esfuerzo alto revisa el lector de texto, la validación, el registro, V1_10 y la regla 2 con pruebas en memoria (`spec003/revision_seguridad.md`, en la carpeta de notas de la sesión, fuera del repositorio). De sus once hallazgos se corrigen cinco con prueba primero, que son el `[Content_Types].xml` dañado que daba 500 (S-01), las rutas que no son ASCII que la revisión previa no veía (S-02), el libro con miles de filas vacías hasta la columna XFD (S-03, con el tope de 1 000 000 de celdas), la excepción original encadenada (S-08) y el nombre con un carácter de control (S-09). Cuatro límites de la revisión previa que ya existían (S-04 a S-07) quedan anotados como riesgo residual en `docs/devops.md`, y S-10 (los espacios Unicode alrededor de un nivel) cumple la spec. El crítico de arquitectura y la revisión coinciden en que el patrón del encabezado del lector y `ck_carga_columna_encabezado` aceptan lo mismo, y el escenario de paridad de US-26 lo comprueba contra PostgreSQL 18.
