# Audit: El export real de Blackboard en .xlsx, .csv y .xls

**Fecha**: 2026-11-17, cierre de T053, T060 y T061 (la corrida de la implementación es del 2026-11-09)  
**Spec**: [spec.md](./spec.md)  
**Plan**: [plan.md](./plan.md)  
**Comando**: `uv run --frozen --no-build pytest -q` en el Back, `bash db/pruebas/correr_pruebas.sh` sobre el clúster desechable de `db/pruebas/cluster_desechable.sh`, `bash scripts/probar_preflight.sh` y `bash scripts/preflight.sh` en el Back y en el Front, y `npm test` y `npm run build` en el Front  
**Resultado**: corrida de cierre del 2026-11-17 sobre `develop` (Back e981a31, Front 7f6c72b). La suite completa del Back da 1187 passed y 19 skipped in 131.41s (0:02:11), con los 104 casos de `exports_blackboard.feature` aprobados; las pruebas de la base dan «ok 65/65 casos de rechazo» y «RESULTADO: todo pasó»; la revisión previa da 46 casos bien y 0 mal en el Back y 28 bien y 0 mal en el Front; Vitest da 9 archivos y 85 pruebas aprobadas, y la compilación termina sin errores. La CI de `develop` termina en verde en los dos commits, con gitleaks (Back, corrida 44227900984; Front, corrida 44209561524)  
**Estado**: Spec 003 cerrada el 2026-11-17, salvo T005 (D-30, en «Decisiones abiertas»). Está en `develop` y en Production con la versión 0.1.0 (Back 7325231 y Front 0d693b9 en `main`), y V1_10 está en la rama `develop` de Neon desde T074 (2026-11-09) y en la principal desde T077 (2026-11-17), antes de la versión.

Esta auditoría cruza cada historia de usuario (user story, US) de la spec 003 con sus escenarios en Gherkin, la prueba que los ejecuta y su resultado del 2026-11-17. Las 19 pruebas omitidas de la suite no tocan esta spec, porque 13 son escenarios del corte 2 de la spec 001 (@corte2), 5 son escenarios de `base_neon.feature` que se comprueban en Neon (T021 y T027) y 1 es una prueba de `tests/test_cluster_desechable.py` que solo corre en la CI. Los escenarios de US-33 los comprueban las pruebas de Vitest del Front (`tests/pantallas/SubirExport.test.tsx`), y el de US-35, los casos de `scripts/probar_preflight.sh`, que la integración continua corre antes de pytest. Los pasos de esos escenarios dejan la propiedad «delegado_a_vitest» o «delegado_a_preflight» con el nombre de la prueba que los cubre, y el resumen de pytest los lista.

## Resumen

| Conjunto | Escenarios | Casos | Aprobados | Omitidos | Pendientes |
| --- | --- | --- | --- | --- | --- |
| Spec 003 (US-26 a US-36) | 39 | 104 | 104 | 0 | 0 |

De los 104 casos, pytest comprueba 100 y delega 4. Los 3 de US-33 van a Vitest del Front, donde `tests/pantallas/SubirExport.test.tsx` da 18 de 18 el 2026-11-17 con `--reporter=verbose`, y el de US-35 va a `scripts/probar_preflight.sh`. El paso que delega en Vitest anota la prueba que lo cubre sin comprobar que exista, a diferencia del paso que delega en la revisión previa, que busca cada caso en el guion.

## Historias

Los escenarios viven en `specs/003-exports-blackboard/aceptacion/exports_blackboard.feature` y sus pasos en `tests/aceptacion/pasos/test_exports_blackboard_feature.py`, con los comunes en `tests/aceptacion/pasos/conftest.py`.

| Historia | Escenario | Casos | Resultado |
| --- | --- | --- | --- |
| US-26 | El .xlsx con los encabezados reales queda publicado | 1 | aprobado, con la línea de `abet.v_r17_por_pi` desde el 2026-11-17 |
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
| FR-006 | Cumplido con el valor provisional de D-30 | US-29 |
| FR-007 | Cumplido | US-27, escenario 1, y US-30 |
| FR-008 | Cumplido | US-34 y las pruebas de P4 del Front |
| FR-009 | Cumplido | US-33 y `tests/pantallas/SubirExport.test.tsx` del Front |
| FR-010 | Cumplido | US-35 y `scripts/probar_preflight.sh` |
| FR-011 | Cumplido con el valor provisional de D-30 | `tests/test_generador_exports.py` |
| FR-012 | Cumplido | bloques fechados de `carga-export.spec.md` (BR-CARGA-03, BR-CARGA-05 a BR-CARGA-08, BR-CARGA-11 y BR-CARGA-14 a BR-CARGA-17) y de `r17.spec.md` (BR-R17-10), y el contrato del Front (9467f29). Los bloques suman BR-CARGA-06 a BR-CARGA-08, que FR-012 no nombra |
| FR-013 | Cumplido para US-08, US-11, US-13 y US-21 | `carga.feature` cambia los textos del tipo no admitido, del contenido que no es un libro y del archivo sin sección, y la suite completa pasa. El escenario 1 de US-21 conserva su texto y pytest lo omite por @corte2, así que su texto se revisa con T084 del corte 2. Desde el corte 2 (T084, 2026-11-18), el escenario corre y pasa con el mismo texto, porque su pregunta no nombra la hoja y vale para los tres formatos, y `tests/test_carga.py` suma un `.csv` sin sección confirmado |
| FR-014 | Cumplido | T074 (2026-11-09, rama `develop`) y T077 (2026-11-17, rama principal) aplican V1_10 con `migrar_neon.sh` desde el Windows, la primera con el permiso de Jefferson en el chat («Sí, desde el Windows») y la segunda dentro de su pedido de publicar la versión 0.1.0. La rama `develop` de T074 la crea Claude Code el mismo día desde la principal con la CLI de Neon, con su permiso («Sí, créala desde la principal»), porque la anterior se había borrado. Back 7325231 y Front 0d693b9 llegan a `main` después de T077 (spec 001, `audit.md`, sección «Despliegue») |
| FR-015 | Cumplido para `MEMORIA.md`, con una excepción en `CHANGELOG.md` | `MEMORIA.md` está en los 15 commits de la spec 003 y de su salida a `develop` (9 del Back y 6 del Front), con las ocho líneas de su plantilla. `CHANGELOG.md` está en 10 de los 15, y le faltan los commits sin cambio visible 5adf3e4, 510c325 y d6637b5 del Back y b75de56 y 706139d del Front. La línea de US-30 que faltaba en `[0.1.0]` del Back se agrega el 2026-11-17, y la revisión previa no da fallas |

## Criterios de éxito

| SC | Estado | Evidencia |
| --- | --- | --- |
| SC-001 | Cumplido con el valor provisional de D-30 | Los escenarios 1 de US-26, US-27 y US-28 comprueban en el `.xlsx`, el `.csv` y el `.xls` las mismas cifras fijas, 11 filas aceptadas de 11, 33 mediciones, 63,6 / 63,6 / 72,7 % en `abet.v_r17_por_pi` y 5 avisos, así que los formatos no difieren entre sí. El del `.xlsx` suma la línea de `abet.v_r17_por_pi` el 2026-11-17. En la vista previa, la 410 (.csv) y la 411 (.xls) quedan con esas cifras (T076), y el R-17 de la 410 cargada con el `.csv` se abre el 2026-11-17 (spec 001, `audit.md`, sección «Despliegue») |
| SC-002 | Cumplido | 104 de 104 casos de la spec 003 y la suite completa sin fallas, en local y en la CI de `develop` (corrida 44227900984 sobre e981a31) |
| SC-003 | Cumplido | US-31 y US-32 y los casos de la revisión de seguridad en `tests/test_lector.py`, en local y en la CI de `develop` |
| SC-004 | Cumplido con el valor provisional de D-30 | T076: Playwright da 2 passed, y Neon `develop` tiene la 410 (.csv) y la 411 (.xls) PUBLICADA con 11 de 11 y 63,6 / 63,6 / 72,7 %, con Q01 a Q14 en 0 |
| SC-005 | Cumplido | `tests/test_generador_exports.py` y la regla 2 de la revisión previa, en local y en la CI de `develop` |

Production no tiene ninguna carga a propósito, porque una carga del piloto no se puede borrar, así que ningún criterio se comprueba con datos en Production.

## Revisión de seguridad

Un subagente con el modelo de la sesión y esfuerzo alto revisa el lector de texto, la validación, el registro, V1_10 y la regla 2 con pruebas en memoria. Su informe (`spec003/revision_seguridad.md`) queda en la carpeta de notas de la sesión, fuera del repositorio, así que la tabla siguiente resume sus once hallazgos, lo que se hace con cada uno y la prueba de cada corrección. El crítico de arquitectura y la revisión coinciden en que el patrón del encabezado del lector y `ck_carga_columna_encabezado` aceptan lo mismo, y el escenario de paridad de US-26 lo comprueba contra PostgreSQL 18.

| Hallazgo | Severidad | Lo que encuentra | Resultado | Prueba |
| --- | --- | --- | --- | --- |
| S-01 | Alta | un zip con una parte dañada, cifrada o con un método de compresión no admitido deja la subida en 500 | corregido | `test_br_carga_05_spec003_una_parte_del_zip_que_no_se_descomprime_no_abre` en `tests/test_lector.py` |
| S-02 | Alta | las rutas con tilde o eñe escapan de las reglas 1 y 2 de la revisión previa | corregido | casos «csv con tilde en el nombre y 20231234 falla» y «xlsx con tilde en el nombre fuera de datos_inventados falla» de `scripts/probar_preflight.sh` |
| S-03 | Media | las filas vacías del final no tienen tope, y la lectura de un `.xlsx` puede pasar de un minuto | corregido con el tope de 1 000 000 de celdas | `test_br_carga_05_spec003_las_filas_vacias_hasta_xfd_se_detienen_por_las_celdas_recorridas` y dos pruebas más del tope en `tests/test_lector.py` |
| S-04 | Media | con `--staged`, la regla 2 lee el árbol de trabajo y no el índice | riesgo residual en `docs/devops.md` | no aplica |
| S-05 | Media | con `--pr`, la regla 2 revisa solo el árbol final y no la historia del PR | riesgo residual en `docs/devops.md` | no aplica |
| S-06 | Media | en un zip, la regla 2 lee solo las hojas y las cadenas compartidas | riesgo residual en `docs/devops.md` | no aplica |
| S-07 | Baja | la regla 2 da por revisado el contenido que no puede leer | riesgo residual en `docs/devops.md` | no aplica |
| S-08 | Baja | `raise … from None` conserva en `__context__` la excepción original, que puede traer el valor de una celda | corregido | `test_br_carga_05_spec003_un_libro_ilegible_no_encadena_la_excepcion_original` en `tests/test_lector.py` |
| S-09 | Baja | un nombre de archivo con U+0000 deja la carga en 500 | corregido | `test_br_carga_05_spec003_un_nombre_con_caracteres_de_control_no_se_admite` en `tests/test_lector.py` y `test_br_carga_05_spec003_un_nombre_con_un_caracter_de_control_responde_422_sin_rastro` en `tests/test_carga.py` |
| S-10 | Baja | `str.strip()` quita los espacios Unicode alrededor de un nivel | aceptado, porque cumple la spec | no aplica |
| S-11 | Informativo | los cuatro exports nuevos estaban sin seguimiento de git, así que la revisión previa no los leía | resuelto al versionarlos, porque la revisión previa los lee desde el commit | `bash scripts/preflight.sh` sin fallas el 2026-11-17 |

## Decisiones abiertas

D-30, la escala de las columnas ABET de 100 puntos, sigue abierta en T005, y la deciden Stefanny Montaño o la Oficina de Calidad con la Coordinación de Ambiental. Mientras tanto rige su valor provisional de `spec.md`, en el que el profesor escribe niveles de 1 a 4 sin conversión, un 75 rechaza su fila con NIVEL_FUERA_DE_ESCALA y cada columna de 100 puntos deja el aviso PUNTAJE_MAXIMO_DISTINTO. Con ese valor quedan cumplidos FR-006, FR-011, SC-001 y SC-004, y aprobados los escenarios 1 de US-26, US-27 y US-28 y los de US-29 con 0.00, 19.00, 75 y miles de cifras. Si D-30 cambia, cambian esos avisos, el motivo del 75 y las cifras del R-17, y los escenarios se reescriben antes que el código.

## Cierre del 2026-11-17

T053 vuelve a correr la suite completa sobre `develop` después de la versión 0.1.0 y de los saltos de Dependabot, con los resultados del encabezado, y la lista de las 19 bases del PostgreSQL local de la Mac (localhost:5432) queda igual antes y después de la corrida. Los 7 casos aprobados de más frente al 2026-11-09 son de `tests/test_env_example.py`, de la spec 001. Tres verificadores (Sonnet, esfuerzo medio) intentan refutar esta auditoría contra el JUnit de esa corrida, el Gherkin, las specs vivas y el historial de los dos repositorios. Sus hallazgos cambian el desglose de las omitidas, la evidencia de FR-012 a FR-015 y de los criterios de éxito, la tabla de la revisión de seguridad y la sección de D-30. El escenario «El .xlsx con los encabezados reales queda publicado» suma la línea de `abet.v_r17_por_pi`, que falla con 63,7 en el PI 5.1 y pasa con 63,6, porque SC-001 promete esas cifras en los tres formatos.
