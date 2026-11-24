# Audit: Ciclo de punta a punta de Química General en Ingeniería Industrial

**Fecha**: 2026-11-23, cierre del segundo bloque de la construcción (T050, T051 y T060)  
**Spec**: [spec.md](./spec.md)  
**Plan**: [plan.md](./plan.md)  
**Tareas**: [tasks.md](./tasks.md)  
**Traza**: [cumplimiento.md](./cumplimiento.md), que genera `scripts/matriz_cumplimiento.py` (T055)  
**Comando**: `uv run --frozen --no-build pytest -q -p no:cacheprovider --junitxml=…`, `bash db/pruebas/correr_pruebas.sh` y `bash scripts/preflight.sh` en el Back, y `npm run build`, `npm test` (con `npx vitest run --reporter=json` para el informe), `npx playwright test e2e/visual.spec.ts` y `bash scripts/preflight.sh` en el Front, con `scripts/matriz_cumplimiento.py --front ../front-feat008 --comprobar --vitest … --junit …`  
**Resultado**: corrida del 2026-11-23 entre las 20:50 y las 21:05 (Lima) sobre `feat/008-ciclo-quimica-industrial` del Back (d67a2f7 más los cambios de este cierre) y del Front (4c1f875 más la regla de la tabla maestra). La suite completa del Back da 2095 passed y 18 skipped en 318 s, las pruebas de la base dan «RESULTADO: todo pasó» y el Front da 283 pruebas aprobadas y 1 pendiente en 20 archivos. La matriz da 32 historias, 237 escenarios, 68 reglas, 11 escenarios pendientes con su razón y 0 huecos  
**Estado**: Spec 008 construida en `feat/008-ciclo-quimica-industrial` del Back y del Front, con commits locales y sin push. Faltan las tareas de Jefferson (T006, T054, T058, T059 y T069 a T072) y las de D-32 (T039 y T047)

Esta auditoría cruza cada historia de usuario (user story, US) de las specs 007 y 008 con sus escenarios en Gherkin, la prueba que los ejecuta y su resultado del 2026-11-23. La traza escenario por escenario vive en `cumplimiento.md`, que no guarda resultados ni fechas, y el informe que pone el resultado de cada prueba sale de los reportes de la corrida, fuera del repositorio. Las historias de la spec 007 entran porque la spec 008 construye su etapa B (US-64 y US-65, J-57).

## Resumen

| Conjunto | Historias | Escenarios | Con prueba | Pendientes con razón | Huecos |
| --- | --- | --- | --- | --- | --- |
| Specs 007 y 008 | 32 | 237 | 226 | 11 | 0 |

Los 11 escenarios pendientes son el de US-65 que espera a US-52 de la spec 005, los tres de US-66 que esperan a D-47 y a D-51, los seis de US-80 que esperan a D-32 (J-54) y la lectura sin correos de US-86, que solo corre en develop (T071). Cada uno lleva su razón en `cumplimiento_razones.toml`, y la matriz falla ante una razón que nombra algo que no existe.

Resultado de cada escenario en el informe de la corrida, con los reportes de pytest y de Vitest de este cierre.

| Resultado | Escenarios |
| --- | --- |
| Aprobada | 210 |
| Sin corrida | 14 |
| Sin pruebas que correr | 11 |
| Omitida | 2 |

«Sin corrida» corresponde a los 14 escenarios `@playwright` (4 de US-82, 8 de US-85 y 2 de US-87), porque el informe lee solo los reportes de pytest y de Vitest y Playwright no corre en la integración continua, y la sección «Playwright» da su resultado. «Omitida» son los dos escenarios de US-88 que nombran el Front, que la suite completa corre sin `ABET_FRONT_RAIZ` y que aprueban en la corrida con esa variable. «Sin pruebas que correr» son los 11 pendientes con razón.

## Historias

| Historia | Spec | Escenarios | Pruebas | Estado | Resultado de la corrida |
| --- | --- | --- | --- | --- | --- |
| US-59 | 007 | 6 | Vitest tests/pantallas/MisSecciones.test.tsx | Con prueba | Aprobada |
| US-60 | 007 | 5 | Vitest tests/pantallas/SubirExport.test.tsx, pytest-bdd tests/aceptacion/pasos/test_experiencia_por_cuenta_feature.py | Con prueba | Aprobada |
| US-61 | 007 | 4 | Vitest tests/pantallas/ResultadoCarga.test.tsx | Con prueba | Aprobada |
| US-62 | 007 | 4 | Vitest tests/pantallas/ResultadoCarga.test.tsx, Vitest tests/App.test.tsx, Vitest tests/pantallas/SubirExport.test.tsx | Con prueba | Aprobada |
| US-63 | 007 | 4 | Vitest tests/App.test.tsx, Vitest tests/pantallas/MisSecciones.test.tsx, Vitest tests/pantallas/Cargas.test.tsx, Vitest tests/pantallas/MisLogros.test.tsx, Vitest tests/pantallas/Avance.test.tsx | Con prueba | Aprobada |
| US-64 | 007 | 4 | pytest-bdd tests/aceptacion/pasos/test_avance_feature.py | Con prueba | Aprobada |
| US-65 | 007 | 5 | Vitest tests/pantallas/Avance.test.tsx | Con prueba y 1 pendiente por decisión | Aprobada |
| US-66 | 007 | 3 | Ninguna | Pendiente por decisión | Sin pruebas que correr |
| US-67 | 008 | 6 | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py | Con prueba | Aprobada |
| US-68 | 008 | 6 | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py | Con prueba | Aprobada |
| US-69 | 008 | 8 | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py | Con prueba | Aprobada |
| US-70 | 008 | 8 | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py | Con prueba | Aprobada |
| US-71 | 008 | 14 | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py, Vitest tests/spec008/alcance_coordinacion.test.tsx | Con prueba | Aprobada |
| US-72 | 008 | 8 | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py | Con prueba | Aprobada |
| US-73 | 008 | 17 | pytest-bdd tests/aceptacion/pasos/test_periodo_elegido_feature.py, Vitest tests/spec008/periodo_elegido.test.tsx | Con prueba | Aprobada |
| US-74 | 008 | 14 | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py | Con prueba | Aprobada |
| US-75 | 008 | 4 | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py | Con prueba | Aprobada |
| US-76 | 008 | 9 | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py | Con prueba | Aprobada |
| US-77 | 008 | 6 | Vitest tests/spec008/carga_quimica.test.tsx | Con prueba | Aprobada |
| US-78 | 008 | 11 | pytest-bdd tests/aceptacion/pasos/test_r17_industrial_feature.py, Vitest tests/spec008/r17_industrial.test.tsx | Con prueba | Aprobada |
| US-79 | 008 | 7 | pytest-bdd tests/aceptacion/pasos/test_avance_feature.py, Vitest tests/spec008/avance_del_curso.test.tsx | Con prueba | Aprobada |
| US-80 | 008 | 6 | Ninguna | Pendiente por decisión | Sin pruebas que correr |
| US-81 | 008 | 12 | Vitest tests/spec008/sistema_visual.test.tsx | Con prueba | Aprobada |
| US-82 | 008 | 4 | Playwright e2e/visual.spec.ts | Con prueba | Sin corrida (Playwright fuera de la CI, ver la sección de Playwright) |
| US-83 | 008 | 10 | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py | Con prueba | Aprobada |
| US-84 | 008 | 4 | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py | Con prueba | Aprobada |
| US-85 | 008 | 8 | Playwright e2e/humo_quimica.spec.ts | Con prueba | Sin corrida (Playwright fuera de la CI, ver la sección de Playwright) |
| US-86 | 008 | 9 | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py | Con prueba y 1 pendiente de tarea | Aprobada |
| US-87 | 008 | 9 | Vitest tests/spec008/guia_y_privacidad.test.ts, Playwright e2e/humo_quimica.spec.ts, pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py | Con prueba | Sin corrida en 2 de 9 pruebas (Playwright fuera de la CI, ver la sección de Playwright) |
| US-88 | 008 | 8 | pytest-bdd tests/aceptacion/pasos/test_guia_y_privacidad_feature.py | Con prueba | 6 aprobadas y 2 omitidas sin `ABET_FRONT_RAIZ`, que aprueban con la variable |
| US-89 | 008 | 5 | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py | Con prueba | Aprobada |
| US-90 | 008 | 9 | pytest-bdd tests/aceptacion/pasos/test_matriz_cumplimiento_feature.py | Con prueba | Aprobada |

## Playwright

Los escenarios `@playwright` corren en el Front fuera de la integración continua, porque la CI no instala los navegadores.

| Prueba | Historias | Corrida | Resultado |
| --- | --- | --- | --- |
| `e2e/visual.spec.ts` | US-82 | 2026-11-23 en este cierre, con la API simulada de `e2e/api_simulada.ts` y su propio Vite en el puerto 5199 | 10 de 10 aprobadas, a 375 y a 1100 px |
| `e2e/humo_quimica.spec.ts` | US-85 y US-87 | 2026-11-23 en T053 (ffb9ef2 del Front), en local, con la API del Back sobre un clúster desechable con la siembra inventada | 10 de 10 aprobadas con `bash scripts/humo_quimica.sh`. La corrida en la vista previa de develop es de T071 |

El humo no corre en este cierre, porque exige la API local sobre un clúster desechable sembrado, el archivo de contraseñas de `ABET_CLAVES_ARCHIVO` y los exports del generador, y el código del humo no cambia desde ffb9ef2 salvo la corrección de la revisión del segundo bloque (4c1f875), que no toca `e2e/humo_quimica.spec.ts`.

## Suites completas (T050 y T051)

| Repositorio | Comando | Resultado |
| --- | --- | --- |
| Back | `uv run --frozen --no-build pytest -q -p no:cacheprovider` | 2095 passed y 18 skipped en 318 s. Los 18 omitidos son 9 de US-20, que esperan a T018, 5 de `base_neon.feature`, que se comprueban en Neon, 2 de US-88 y 1 de la matriz, que piden `ABET_FRONT_RAIZ`, y 1 de `tests/test_cluster_desechable.py`, que en la Mac nunca toma una CI |
| Back | `ABET_FRONT_RAIZ=../front-feat008 uv run --frozen --no-build pytest -q -p no:cacheprovider tests/aceptacion/pasos/test_guia_y_privacidad_feature.py tests/aceptacion/pasos/test_matriz_cumplimiento_feature.py` | 28 passed, con los dos escenarios de US-88 que nombran el Front y la comparación de `cumplimiento.md` con el Front real |
| Back | `bash db/pruebas/correr_pruebas.sh` | «RESULTADO: todo pasó», con 302 comprobaciones ok, Q01 a Q15 y Q18 a Q21 en 0 y `controles_neon.sql` con «Q01 a Q14 y Q18 a Q21 devuelven 0 filas.» |
| Back | `bash scripts/preflight.sh` y `bash scripts/probar_preflight.sh` | Sin fallas, y 73 bien y 0 mal |
| Back | `scripts/matriz_cumplimiento.py --front ../front-feat008 --comprobar` | 0 huecos y 11 pendientes, con `cumplimiento.md` al día |
| Front | `npm run build` y `npm test` | El build termina sin errores, y Vitest da 20 archivos con 283 pruebas aprobadas y 1 pendiente, «Atrás desde P4 abierta con «Ver la carga» vuelve a P7» |
| Front | `npx playwright test e2e/visual.spec.ts` | 10 passed |
| Front | `bash scripts/preflight.sh` y `bash scripts/probar_preflight.sh` | Sin fallas, y 55 bien y 0 mal con los tres casos nuevos de la regla de la tabla maestra, que dan 2 mal antes del cambio del guion |

## Requisitos y criterios de éxito

| Criterio | Estado al 2026-11-23 | Evidencia o razón |
| --- | --- | --- |
| SC-001 | Cumplido salvo los pendientes con razón | 237 escenarios en la matriz y 226 con prueba. En el informe de este cierre 210 aprueban, 2 de US-88 aprueban con `ABET_FRONT_RAIZ` y 14 de Playwright aprueban fuera del informe. Los 11 pendientes son 6 de US-80, como prevé el criterio, y 5 que esperan a la spec 005, a D-47 y a D-51 o a T071 |
| SC-002 | Pendiente de Jefferson | El ensayo con los datos reales es de T054, con «18 de 18 secciones iguales.». La herramienta pasa sus escenarios con datos inventados (US-84) |
| SC-003 | Pendiente de Jefferson | El conciliador sobre develop corre después de la capacitación (T072) |
| SC-004 | Pendiente de la capacitación | Lo mide la sala (T072). Los exports inventados se publican con 0 rechazos en US-75 y en el humo |
| SC-005 | Pendiente de Jefferson | La huella de Ambiental en develop es de T069 y T071. En el clúster desechable la huella es la misma antes y después de la siembra (US-69 y US-86) |
| SC-006 | Cumplido en el clúster desechable, pendiente en develop | Los escenarios de 403 y de alcance de US-70, US-71 y US-79 pasan. La lectura sin correos de develop es de T071 |
| SC-007 | Cumplido en el clúster desechable, pendiente en develop | `correr_pruebas.sh` deja Q01 a Q15 y Q18 a Q21 en 0. En develop lo comprueban T069 a T072 |
| SC-008 | Cumplido en local, pendiente en la vista previa | El humo da 10 de 10 en local (T053). La corrida en la vista previa es de T071 |
| SC-009 | Cumplido | La prueba de contraste exige 0 clases sin token, `e2e/visual.spec.ts` da 10 de 10 a 375 px y las pruebas de la spec 007 cambian solo las que nombra FR-019 |
| SC-010 | Cumplido con una huella inventada, pendiente con la real | `preflight.sh` pasa en los dos repositorios. El barrido del historial con la huella del correo real es de Jefferson |
| SC-011 | Cumplido | La matriz da 0 huecos con `--comprobar` |

## Verificación de las specs vivas

Cada spec viva que toca la spec 008 suma su línea Verification del 2026-11-23, con el comando, las pruebas y las reglas que cubre. Son `specs/features/acceso/acceso.spec.md` (BR-ACCESO-12 a 14), `periodo/periodo.spec.md` (BR-PERIODO-05 y 06), `carga-export/carga-export.spec.md` (BR-CARGA-20), `r17/r17.spec.md` (BR-R17-13), `resultados/resultados.spec.md` (la ruta 12 de Industrial y BR-RESULTADOS-11 en P6) y `avance/avance.spec.md` (BR-AVANCE-01 a 04, con BR-AVANCE-05 en espera de D-47 y de D-51). Las 68 reglas de las seis specs vivas tienen escenario o prueba nombrada en la matriz.

## Cambios fechados del cierre

Los informes del segundo bloque del Front piden fechar lecturas de escenarios que contradicen el código real o que no se pueden reproducir tal como están escritos. El cierre las fecha en «Lecturas del segundo bloque del Front» de `spec.md`, y tres pasos cambian en los `.feature`, con su nota en el encabezado de cada archivo y sin cambiar ningún título ni los conteos de 202 escenarios y 258 casos.

- `sistema_visual.feature`, «El foco se ve en cada control de P3 y sigue el orden de lectura». «Antes de subir» se lee entre el periodo y el archivo sin tomar el foco, y el orden empieza en «Salir» (T048).
- `guia_y_privacidad.feature`, «Cada rótulo citado en la guía existe en el Front». El cotejo busca en todo `src/` y en los mensajes del contrato que terminan en punto o en signo de pregunta (T049).
- `guia_y_privacidad.feature`, «El profesor sigue la guía de su rol de punta a punta en la vista previa» y «El ejercicio de error usa un export inventado y enseña a leer «Qué corregir»». El recorrido recibe el archivo ya publicado en la misma corrida y abre P4 con «Ver resultado», y el ejercicio corre en la 703 con `docente703@example.invalid` (T053).

`spec.md` fecha además la lectura de FR-012 (el consejo del aviso con role="status", T044), la barra de P6 con role="img" que cumple US-41 de la spec 004 y US-78 (T045), los escenarios de US-79 y de US-65 que no se pueden reproducir tal como están (T046) y la medida de 24 por 24 px sobre cada control visible (T048). Las marcas de T048 y T053 en `tasks.md` siguen los informes del Front, con la marca de T048 escrita sin dos puntos y con el commit al comienzo, como las demás.

## Pendiente y de quién

| Pendiente | De quién | Razón |
| --- | --- | --- |
| T006, las decisiones D-48 a D-55, la «Plantilla Base - Final» y la «Base cursos - Nivel» de Industrial, J-51 y J-56 | Jefferson con Stefanny Montaño | Solo la Oficina de Calidad y la carrera las deciden, y la spec aplica el valor provisional mientras tanto |
| T039 y T047, el agregado del curso de US-80 | Jefferson, si D-32 se responde (J-54) | Sin D-32 no hay regla del agregado que construir |
| T059, el CSV de la programación de 2026-1 con correos de ejemplo | Jefferson | Nace de la programación real, fuera del repositorio |
| T054, el ensayo con los datos reales en una rama hija de develop | Jefferson, desde su Windows | La regla global exige que toda escritura en una base salga del Windows, y los datos reales no entran a la Mac del repositorio |
| T058, el modo de J-58 de `asignar_claves.py` | Jefferson | `herramientas_neon` vive fuera de los repositorios |
| T069 a T072, la migración, el empuje y la fusión, la siembra, el humo en la vista previa, la capacitación y el cierre | Jefferson, desde su Windows y con su permiso | Escriben en Neon o en Vercel, o empujan ramas |
| El barrido del historial con la huella del correo real (US-88) | Jefferson | La huella vive en su entorno y en los secretos de GitHub de los dos repositorios |
| US-66 de la spec 007 y el campo `profesores` de la ruta 17 (BR-AVANCE-05) | La Oficina de Calidad y la coordinación de Industrial, con D-47 y D-51 | La spec no promete correos sin esa respuesta |
| «Atrás desde P4 abierta con «Ver la carga» vuelve a P7» de US-65 | La spec 005, con US-52 | Espera la navegación por fragmento |

## Orden de publicación

La CI del Back clona la rama del Front del mismo nombre o, si no existe, develop, donde todavía no están las pruebas de la spec 008, así que la rama del Front se empuja antes que la del Back (T070). Cada cambio del Front que toca un título de prueba de un escenario regenera `cumplimiento.md` con `scripts/matriz_cumplimiento.py --front` en el Back, porque `--comprobar` falla con una traza atrasada.

## Lo que esta auditoría no prueba

- Ninguna corrida toca Neon, Vercel ni datos reales. El ensayo, la siembra, el humo en la vista previa, la capacitación y el cierre real son de Jefferson.
- El humo de Playwright no corre en este cierre ni en la CI, y su resultado es el de T053 en local.
- La regla de ocho cifras del preflight revisa solo las líneas que agrega un cambio, así que un código real que un commit anterior agregó no lo detiene ninguna regla (`docs/devops.md`).
- La revisión con axe-core queda fuera de alcance, porque pide una dependencia nueva, y un texto que hereda el fondo de su elemento padre sigue fuera de la prueba de contraste.
