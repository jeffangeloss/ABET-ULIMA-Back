# Audit: Resumen del curso para la coordinación

**Fecha**: 2026-11-25, cierre de la construcción (T040 y T041)  
**Spec**: [spec.md](./spec.md)  
**Plan**: [plan.md](./plan.md)  
**Tareas**: [tasks.md](./tasks.md)  
**Comando**: `ABET_FRONT_RAIZ=../front-009 uv run --frozen --no-build python -m pytest -q -p no:cacheprovider --junitxml=…` y `bash scripts/preflight.sh` en el Back, `npm run build`, `npx tsc --noEmit`, `npm test` (con `npx vitest run --reporter=json` para el informe), `npx playwright test e2e/visual.spec.ts` y `bash scripts/preflight.sh` en el Front, y `scripts/matriz_cumplimiento.py --front ../front-009 --comprobar --vitest … --junit …`  
**Resultado**: corrida del 2026-11-25 sobre `feat/009-resumen-curso` del Back (7f28652) y del Front (e366633), sin push. La suite completa del Back da 2729 passed y 15 skipped en 355 s, el Front da 420 pruebas aprobadas y 1 `todo` en 28 archivos, Playwright da 12 passed en `e2e/visual.spec.ts`, ambos `preflight.sh` terminan sin fallas y la matriz da 32 historias, 237 escenarios, 87 reglas, 10 pendientes con su razón y 0 huecos.  
**Estado**: Spec 009 construida en el Back y en el Front con commits locales. Faltan T003, T042 y T043, que son de Jefferson, y la corrida de `e2e/humo_resumen.spec.ts` (T033), que necesita las contraseñas de la vista previa

Esta auditoría cruza cada historia de usuario (user story, US) de la spec 009 con sus escenarios en Gherkin, la prueba que los ejecuta y su resultado del 2026-11-25. La matriz de cumplimiento de `scripts/matriz_cumplimiento.py` lee las specs 007 y 008 por diseño, así que las 4 historias de esta spec no entran en sus 32 y se cruzan aquí, con cada prueba comprobada con grep por su `def` o por su título exacto y no de memoria. El resultado de la matriz sigue en 0 huecos porque los cambios fechados de US-80 y FR-016 de la spec 008 dejan sus seis escenarios con la razón de `cumplimiento_razones.toml`.

## Resumen

| Conjunto | Historias | Escenarios | Con prueba | Pendientes | Huecos |
| --- | --- | --- | --- | --- | --- |
| Spec 009 | 4 | 23 | 23 | 0 | 0 |

| Resultado | Escenarios |
| --- | --- |
| Aprobada en pytest-bdd | 16 |
| Aprobada en Vitest | 6 |
| Aprobada en Playwright | 1 |

El escenario de Playwright aprueba con `e2e/visual.spec.ts`, que no corre en la integración continua porque la CI no instala los navegadores. Los 16 de pytest-bdd salen en el reporte `--junitxml` con 0 fallas, y `tests/aceptacion/pasos/test_lectura_gherkin_es.py` exige que los 16 sigan atados a su prueba.

## Historias

| Historia | Escenarios | Pruebas | Estado | Resultado de la corrida |
| --- | --- | --- | --- | --- |
| US-91 | 12 | pytest-bdd `tests/aceptacion/pasos/test_resumen_del_curso_feature.py`, `tests/test_api_resumen_curso.py`, `tests/aceptacion/pasos/test_resumen_del_curso_consulta.py`, `tests/test_rutas_protegidas.py` | Con prueba | Aprobada |
| US-92 | 7 | Vitest `tests/spec009/resumen_del_curso.test.tsx` (6) y Playwright `e2e/visual.spec.ts` (1) | Con prueba | Aprobada en Vitest y en Playwright |
| US-93 | 2 | pytest-bdd `tests/aceptacion/pasos/test_resumen_del_curso_feature.py`, Vitest `tests/spec009/api_resumen.test.ts` | Con prueba | Aprobada |
| US-94 | 2 | pytest-bdd `tests/aceptacion/pasos/test_conciliacion_del_curso_feature.py`, `tests/test_conciliar_curso.py` | Con prueba | Aprobada |

## Escenarios

| Historia | Escenario | Prueba | Resultado |
| --- | --- | --- | --- |
| US-91 | El curso suma alumnos de las secciones publicadas y no promedia porcentajes | `test_el_curso_suma_alumnos_y_no_promedia_porcentajes` | Aprobada |
| US-91 | Cada sección trae sus cifras en orden de número y la sección sin carga no inventa un porcentaje | `test_cada_seccion_trae_sus_cifras_en_orden` | Aprobada |
| US-91 | El conteo de secciones cuenta la meta solo sobre las publicadas | `test_el_conteo_de_secciones_cuenta_la_meta_solo_sobre_las_publicadas` | Aprobada |
| US-91 | Cada porcentaje de sección es el de su R-17 | `test_cada_porcentaje_de_seccion_es_el_de_su_r17` | Aprobada |
| US-91 | El curso cumple con el 80,0 justo y no cumple con 75,0, igual que el R-17 | `test_el_curso_cumple_con_el_80_justo_y_no_con_75` | Aprobada |
| US-91 | Un curso sin cargas publicadas trae nulos y no ceros | `test_un_curso_sin_cargas_publicadas_trae_nulos` | Aprobada |
| US-91 | Con un conjunto de reglas provisional el curso sale provisional | `test_con_un_conjunto_provisional_el_curso_sale_provisional` | Aprobada |
| US-91 | La respuesta del resumen trae solo las claves de su lista cerrada | `test_la_respuesta_trae_solo_las_claves_de_su_lista_cerrada` | Aprobada |
| US-91 | El profesor recibe 403 en el resumen del curso | `test_el_profesor_recibe_403` | Aprobada |
| US-91 | La coordinación de Ambiental recibe el resumen de 5643 sin indicadores | `test_la_coordinacion_de_ambiental_recibe_el_resumen_sin_indicadores` | Aprobada |
| US-91 | Sin sesión el resumen responde 401 | `test_sin_sesion_el_resumen_responde_401` | Aprobada |
| US-91 | Un periodo o una asignatura mal formados responden 422 sin leer la base | `test_un_periodo_o_una_asignatura_mal_formados_responden_422` | Aprobada |
| US-93 | La coordinación de la carrera recibe la lista de sus cursos con plan en el periodo | `test_la_coordinacion_de_la_carrera_recibe_la_lista_de_sus_cursos` | Aprobada |
| US-93 | La coordinación del curso recibe solo su curso | `test_la_coordinacion_del_curso_recibe_solo_su_curso` | Aprobada |
| US-94 | El conciliador dice que el curso es igual a la tabla maestra | `test_el_conciliador_dice_que_el_curso_es_igual` | Aprobada |
| US-94 | Una calificación cambiada en la tabla maestra hace distinto al curso | `test_una_calificacion_cambiada_hace_distinto_al_curso` | Aprobada |
| US-92 | P8 escribe las cifras del curso con su barra de dos tramos | Vitest `tests/spec009/resumen_del_curso.test.tsx` | Aprobada |
| US-92 | P8 trae una fila por sección con su barra y la línea de la meta | Vitest `tests/spec009/resumen_del_curso.test.tsx` | Aprobada |
| US-92 | P8 no muestra profesores ni ordena por resultado | Vitest `tests/spec009/resumen_del_curso.test.tsx` | Aprobada |
| US-92 | P8 marca las cifras provisionales | Vitest `tests/spec009/resumen_del_curso.test.tsx` | Aprobada |
| US-92 | P8 de un curso sin cargas no dibuja barras de 0 % | Vitest `tests/spec009/resumen_del_curso.test.tsx` | Aprobada |
| US-92 | Solo la coordinación ve el enlace al resumen del curso en el menú | Vitest `tests/spec009/resumen_del_curso.test.tsx` | Aprobada |
| US-92 | P8 a 375 px no se desplaza a lo ancho y se recorre con teclado | Playwright `e2e/visual.spec.ts` | Aprobada, 12 de 12 en el archivo |

## Suites completas (T040)

| Repositorio | Comando | Resultado |
| --- | --- | --- |
| Back | `ABET_FRONT_RAIZ=../front-009 uv run --frozen --no-build python -m pytest -q -p no:cacheprovider` | 2729 passed y 15 skipped en 355 s. Los 15 omitidos son 9 de US-20, que esperan a T018, y 5 de `base_neon.feature`, que se comprueban en Neon, y 1 de `test_cluster_desechable`, que no corre en la Mac como CI |
| Back | `bash scripts/preflight.sh` | Sin fallas |
| Back | `scripts/matriz_cumplimiento.py --front ../front-009 --comprobar` | 32 historias, 237 escenarios, 87 reglas, 10 pendientes con su razón y 0 huecos, salida 0 |
| Front | `npm run build` y `npx tsc --noEmit` | Terminan sin errores |
| Front | `npm test` | 28 archivos, 420 pruebas aprobadas y 1 `todo` |
| Front | `npx playwright test e2e/visual.spec.ts` | 12 passed, con P8 a 375 y a 1100 px |
| Front | `bash scripts/preflight.sh` | Sin fallas |

## Requisitos y criterios de éxito

| Requisito | Escenarios | Pruebas | Resultado |
| --- | --- | --- | --- |
| FR-001 | «El profesor recibe 403…», «Sin sesión el resumen responde 401», «Un periodo o una asignatura mal formados responden 422…» | `tests/test_api_resumen_curso.py`, `tests/test_rutas_protegidas.py` | Aprobada |
| FR-002 | «La coordinación de Ambiental recibe el resumen de 5643 sin indicadores» | `tests/test_api_resumen_curso.py` | Aprobada |
| FR-003 | «La respuesta del resumen trae solo las claves de su lista cerrada», «Cada sección trae sus cifras en orden de número…» | `test_resumen_del_curso_feature.py` | Aprobada |
| FR-004 | «El curso suma alumnos de las secciones publicadas…», «Cada porcentaje de sección es el de su R-17» | `test_resumen_del_curso_feature.py`, `test_resumen_del_curso_consulta.py` | Aprobada |
| FR-005 | «El curso cumple con el 80,0 justo y no cumple con 75,0…» | `test_resumen_del_curso_feature.py` | Aprobada |
| FR-006 | «El conteo de secciones cuenta la meta solo sobre las publicadas» | `test_resumen_del_curso_feature.py` | Aprobada |
| FR-007 | «Un curso sin cargas publicadas trae nulos y no ceros», «Con un conjunto de reglas provisional el curso sale provisional» | `test_resumen_del_curso_feature.py` | Aprobada |
| FR-008 | «La respuesta del resumen trae solo las claves de su lista cerrada» | `test_resumen_del_curso_feature.py`, `tests/test_rutas_protegidas.py` | Aprobada |
| FR-009 | Los seis escenarios de P8 | Vitest `tests/spec009/resumen_del_curso.test.tsx` | Aprobada |
| FR-010 | Los dos escenarios de US-93 | `test_resumen_del_curso_feature.py`, Vitest `tests/spec009/api_resumen.test.ts` | Aprobada |
| FR-011 | Los dos escenarios de US-94 | `test_conciliacion_del_curso_feature.py`, `tests/test_conciliar_curso.py` | Aprobada |
| FR-012 | Sin escenario propio | La nota «Sustituida el 2026-11-25 por la spec 009 (J-61)» de US-80 y FR-016 en la spec 008, ADR-010 del Front y la matriz con 0 huecos | Aprobada |

| Criterio | Estado al 2026-11-25 | Evidencia o razón |
| --- | --- | --- |
| SC-001 | Cumplido | 23 de 23 escenarios con prueba y aprobados, con los 6 de P8 en Vitest y el de 375 px en Playwright |
| SC-002 | Pendiente de Jefferson | La corrida de `--curso` con la tabla maestra real de Química General va fuera de todo repositorio (T042) |
| SC-003 | Pendiente de Jefferson | P8 de 5643 en la vista previa junto a «Resumen Curso» de Stefanny (T042), con `e2e/humo_resumen.spec.ts` sin correr (T033) |
| SC-004 | Cumplido | El escenario de la lista cerrada y el barrido de privacidad de `preflight.sh` en los dos repositorios pasan |

## Pendientes y riesgos

- **Valores provisionales**, anotados en `MEMORIA.md`. La ruta 20 usa `PERIODO_VIGENTE` si falta el periodo, una asignatura ausente o inválida da 422, la meta de sección del conciliador es 80 % (D-56) y la franja de P8 dice «Cifras provisionales.» con texto general porque la ruta 20 no trae el conjunto de reglas.
- **BR-RESULTADOS-15, tramo de la barra.** Resuelto el 2026-11-25 en el Front (6357e84). P8 calcula el tramo «Debajo del nivel esperado» desde los conteos con `porcentajeDeConteos()`, que redondea como ROUND(numeric, 1) de PostgreSQL, y con 1 de 80 calificados escribe 98,8 %. La prueba es «El tramo debajo del nivel esperado sale de los conteos con el redondeo de PostgreSQL, no de restar a 100» de `tests/spec009/resumen_del_curso.test.tsx`.
- **Selector de P8.** Resuelto el 2026-11-25 en el Front (6357e84). El curso que llega desde P7 y no figura en la ruta 21 encabeza el selector, y elegir otro curso cambia el fragmento, así que recargar conserva la elección. La prueba es «Un curso que llega desde P7 y no está en la ruta 21 queda elegido en el selector, y otra elección cambia de curso».
- **Orden de secciones.** `secciones_visibles()` ordena `s.numero` como texto, y el orden numérico se rompería con números de largo distinto. En Química todas tienen 3 cifras. El riesgo viene de antes de esta rama.
- **Orden de corrida de los pasos.** Correr a mano archivos de `tests/aceptacion/pasos` mezclados con archivos de `tests/` en el orden «pasos, tests, pasos» pierde la fixture `ctx`, como con archivos anteriores, y no ocurre al correr la carpeta completa como hace la CI.
- **Mutaciones equivalentes.** Tres mutaciones del código no hacen fallar ninguna prueba, y las tres son equivalentes. Dos quitan un filtro `PUBLICADA` que la vista ya aplica y la otra pasa el PI a la lectura sin pedir `--curso`.
- **De Jefferson.** T003 (fórmulas DAX de Stefanny, D-57 y D-32), T042 (corrida real y P8 junto a «Resumen Curso») y T043 (el push y los PR, fuera de la ventana congelada de la capacitación).
