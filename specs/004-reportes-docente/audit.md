# Audit: Los logros del profesor por SO, solo en sus secciones

**Fecha**: 2026-11-18, cierre de T050, T051 y T060  
**Spec**: [spec.md](./spec.md)  
**Plan**: [plan.md](./plan.md)  
**Comando**: `uv run --frozen --no-build pytest -q -p no:cacheprovider` en el Back, `bash db/pruebas/correr_pruebas.sh` sobre el clúster desechable de `db/pruebas/cluster_desechable.sh` y `bash scripts/preflight.sh --pr origin/develop` en el Back y en el Front, `npm test` y `npm run build` en el Front, y `npx playwright test e2e/humo.spec.ts` contra `bash scripts/api_local.sh --sin-https` del Back y Vite  
**Resultado**: corrida de cierre del 2026-11-18 sobre `feat/004-reportes-docente`, con el código del Back de 0db6ee3 y la siembra final de las 150 secciones, y el del Front de 203d822. La suite completa del Back da 1440 passed y 15 skipped in 156.81s (0:02:36), con los 45 casos de los dos `.feature` de la spec 004 aprobados; las pruebas de la base dan «RESULTADO: todo pasó», con Q01 a Q14 en 0 filas y Q15 aprobada; la revisión previa no da fallas en los dos repositorios; Vitest da 11 archivos y 164 pruebas aprobadas, y la compilación termina sin errores; el humo local da 5 passed, 2 de ellos de P6  
**Estado**: Spec 004 construida en `feat/004-reportes-docente` del Back (55a66b6 y 0db6ee3) y del Front (a5d678c, 203d822 y b856515) y fusionada en `develop` el 2026-11-18 con el permiso de Jefferson, con el PR #31 en f403d52 y el PR #20 del Front en 778ae23 (T070). Quedan T005 (D-32 a D-34 con la Coordinación de Ambiental), T071 (el humo de P6 contra la vista previa de `develop`) y T072 (la versión hacia `main`).

Esta auditoría cruza cada historia de usuario (user story, US) de la spec 004 con sus escenarios en Gherkin, la prueba que los ejecuta y su resultado del 2026-11-18. Las 15 pruebas omitidas de la suite no tocan esta spec, porque son los escenarios de US-20 que esperan a T018, los de `base_neon.feature` que se comprueban en Neon y una prueba de `tests/test_cluster_desechable.py` que solo corre en la CI, como antes de la spec 004. Los escenarios con `@delegado_a_vitest` los comprueban las pruebas de Vitest del Front, y sus pasos dejan la propiedad «delegado_a_vitest» con el nombre de la prueba que los cubre, que el resumen de pytest lista.

## Resumen

| Conjunto | Escenarios | Casos | Aprobados | Omitidos | Pendientes |
| --- | --- | --- | --- | --- | --- |
| Spec 004 (US-37 a US-44) | 37 | 45 | 45 | 0 | 0 |

De los 45 casos, pytest comprueba 33 contra la ruta 12, la base y el R-17 de la misma carga, y delega 12 en Vitest del Front. Los 30 casos de `tests/pantallas/MisLogros.test.tsx` y de `tests/App.test.tsx` dan 30 de 30 con `npx vitest run --reporter=verbose`, y cada nombre que anotan los pasos del Back coincide con el de una prueba aprobada. El paso que delega en Vitest anota la prueba que lo cubre sin comprobar que exista, así que esta coincidencia se revisa a mano en cada cierre.

## Historias

Los escenarios viven en `specs/004-reportes-docente/aceptacion/resultados.feature` (R) y `alcance_y_privacidad.feature` (A), y sus pasos en `tests/aceptacion/pasos/test_resultados_feature.py` y `test_alcance_resultados_feature.py`, con los comunes en `tests/aceptacion/pasos/conftest.py`.

| Historia | Escenario | Archivo | Casos | Resultado |
| --- | --- | --- | --- | --- |
| US-37 | El profesor de varias secciones ve sus logros agrupados por SO | R | 1 | aprobado |
| US-37 | Las cifras viajan como números de un decimal | R | 1 | aprobado |
| US-37 | El 80,0 % justo queda en la meta | R | 1 | aprobado |
| US-37 | P6 agrupa los PI por SO y escribe cada cifra | R | 1 | aprobado, delegado a Vitest del Front |
| US-37 | P6 se abre desde P2 y desde P4 sin confundirse con «Ver resultado» | R | 1 | aprobado, delegado a Vitest del Front |
| US-37 | P6 ofrece el R-17 de cada sección publicada | R | 1 | aprobado, delegado a Vitest del Front |
| US-38 | El reporte del profesor de varias secciones no trae las de otros profesores | A | 1 | aprobado |
| US-38 | Cada profesor de una sección ve solo la suya | A | 2 | aprobado |
| US-38 | Un seccion_id en la consulta no abre otra sección | A | 1 | aprobado |
| US-38 | El alcance se lee de la base en cada petición | A | 1 | aprobado |
| US-38 | Sin una sesión vigente no hay resultados | A | 3 | aprobado |
| US-38 | Un periodo mal formado responde 422 | A | 1 | aprobado |
| US-38 | Ninguna ruta con datos responde sin sesión | A | 1 | aprobado |
| US-38 | P6 no ofrece subir exports | A | 1 | aprobado, delegado a Vitest del Front |
| US-39 | Una sección sin carga publicada no trae cifras | R | 1 | aprobado |
| US-39 | Una carga rechazada no cuenta como resultado | R | 1 | aprobado |
| US-39 | Un PI sin calificaciones no sale como 0 % | R | 1 | aprobado |
| US-39 | Un estudiante sin evidencia deja dos porcentajes | R | 1 | aprobado |
| US-39 | Sin secciones en el periodo, la respuesta es una lista vacía y no un error | R | 2 | aprobado |
| US-39 | P6 no pinta lo que no se mide | R | 1 | aprobado, delegado a Vitest del Front |
| US-39 | P6 muestra la espera, el error y la lista vacía | R | 1 | aprobado, delegado a Vitest del Front |
| US-40 | Los nueve indicadores coinciden con los tres R-17 | R | 1 | aprobado |
| US-40 | Con un estudiante sin evidencia, el segundo porcentaje también coincide con el R-17 | R | 1 | aprobado |
| US-40 | Leer el reporte no escribe en la base | R | 1 | aprobado |
| US-40 | Una carga reemplazada sale del reporte | R | 1 | aprobado, del corte 2, con US-18 en `develop` desde el PR #28 |
| US-41 | Con R-2026-BORRADOR los resultados son provisionales | R | 1 | aprobado |
| US-41 | Con reglas aprobadas los resultados salen sin la marca | R | 1 | aprobado |
| US-41 | Un conjunto aprobado que no define todos sus parámetros sigue provisional | R | 1 | aprobado, con Q11 en 1 fila en esa base |
| US-41 | P6 escribe la marca provisional de cada sección | R | 3 | aprobado, delegado a Vitest del Front |
| US-42 | La respuesta trae solo las claves de la lista cerrada | A | 1 | aprobado |
| US-42 | La respuesta no trae códigos, nombres ni correos | A | 1 | aprobado |
| US-42 | Ninguna respuesta de la ruta queda en una caché | A | 3 | aprobado |
| US-42 | P6 no guarda nada en el navegador | A | 1 | aprobado, delegado a Vitest del Front |
| US-43 | El reparto por nivel suma los calificados | R | 1 | aprobado |
| US-43 | P6 escribe el reparto por nivel | R | 1 | aprobado, delegado a Vitest del Front |
| US-44 | El coordinador ve las cinco secciones del periodo | R | 1 | aprobado |
| US-44 | P6 del coordinador agrupa por asignatura y no ordena por resultado | R | 1 | aprobado, delegado a Vitest del Front |

## Escenarios delegados a Vitest del Front

| Escenario | Prueba de Vitest | Resultado |
| --- | --- | --- |
| P6 agrupa los PI por SO y escribe cada cifra | `MisLogros.test.tsx` › «agrupa los PI bajo su SO y cada fila escribe su PI, su sección, su porcentaje, su fracción y su estado» y «cada barra lleva aria-hidden, su ancho es el porcentaje y la meta va marcada con una línea y con texto» | aprobado |
| P6 se abre desde P2 y desde P4 sin confundirse con «Ver resultado» | `App.test.tsx` › «la cabecera ofrece una sola vez «Ver mis logros por SO», que abre P6, y P6 vuelve a P2 con «Volver»» y «P4 de una carga publicada ofrece también el enlace a P6» | aprobado |
| P6 ofrece el R-17 de cada sección publicada | `MisLogros.test.tsx` › «ofrece el R-17 solo de cada sección publicada, con el carga_id de su carga» | aprobado el 2026-11-22. Cambia el 2026-11-24 (spec 005, J-32): P6 ya no ofrece el R-17 y la prueba, con el título «ofrece Ver la carga solo de cada sección publicada, con el carga_id de su carga, y ningún enlace al R-17», comprueba que lleva a P4 |
| P6 no ofrece subir exports | `MisLogros.test.tsx` › «no ofrece Subir export al profesor ni al coordinador» | aprobado |
| P6 no pinta lo que no se mide | `MisLogros.test.tsx` › «escribe lo que no se mide y no dibuja ninguna barra de 0 %» | aprobado |
| P6 muestra la espera, el error y la lista vacía | `MisLogros.test.tsx` › «dice que espera mientras la API responde, el error del servicio y la lista vacía» y `App.test.tsx` › «un 401 en P6 vuelve a P1 con el aviso de sesión vencida» | aprobado |
| P6 escribe la marca provisional de cada sección | `MisLogros.test.tsx` › «escribe la marca provisional de una sección según su conjunto de reglas», con sus tres casos | aprobado |
| P6 no guarda nada en el navegador | `MisLogros.test.tsx` › «no guarda nada en localStorage ni en sessionStorage» | aprobado |
| P6 escribe el reparto por nivel | `MisLogros.test.tsx` › «escribe el reparto por nivel de cada PI, con el conteo de cada tramo» | aprobado |
| P6 del coordinador agrupa por asignatura y no ordena por resultado | `MisLogros.test.tsx` › «el coordinador ve las secciones agrupadas por asignatura y en el orden de su número, nunca por su porcentaje» y `App.test.tsx` › «el coordinador abre P6 con «Ver los logros por SO de la carrera»» | aprobado |

Tres pruebas de P6 van más allá de los escenarios. La prueba «escribe la falta de nivel esperado, de meta, de instrumento y de plan sin dibujar barras» cubre los Edge Cases que ningún dato inventado trae. La prueba «escribe el estado que decide la API, sin comparar el porcentaje con la meta» da a P6 un `en_meta` contrario a las cifras y exige el de la API, y «P4 de una carga que no está publicada no ofrece el enlace a P6» cubre el límite de FR-011.

## Pruebas unitarias, de la base y de humo

| Archivo | Lo que cubre | Resultado |
| --- | --- | --- |
| `tests/test_resultados.py` | `en_meta()` en la frontera del 80,0 % y con nulos, `cifra()` como número JSON y `_plan_de_accion` del R-17 con la misma regla en 24 combinaciones | 39 aprobadas |
| `tests/test_api_resultados.py` | la sección 412 de 450002 campo por campo, el orden, los nulos de la regla, la sección sin plan, la codocencia, el periodo, la sesión, la transacción `READ ONLY` con `REPEATABLE READ`, un reemplazo a mitad de la lectura, la lectura sin escrituras, el PI 5.10, una segunda versión de catálogo, el `EXPLAIN` y 150 secciones | 39 aprobadas |
| `tests/test_rutas_protegidas.py` y `tests/rutas_registradas.py` | el recorrido de las rutas registradas con `fastapi.routing.iter_route_contexts()`, el 401 sin cookie, el 403 único con un identificador de la 410 pedido por docente411 y la dependencia de sesión de cada router con datos | 7 aprobadas |
| `tests/test_permisos_resultados.py` | `db/plataforma/neon/revisar_permisos_resultados.sql`, con los 16 objetos que lee la ruta, el permiso revocado que lo detiene y la sesión en solo lectura | 3 aprobadas |
| `tests/aceptacion/pasos/test_reglas_de_copia.py` | la regla «con la columna X.Y vacía en sus N filas» en un `.xlsx` y en un `.csv`, y su detención con otro número de filas | 4 aprobadas |
| `tests/aceptacion/pasos/test_lectura_gherkin_es.py` | los dos `.feature` de la spec 004 con el analizador de pytest-bdd, sus esquemas, sus Antecedentes, sus etiquetas y `@delegado_a_vitest` en los escenarios de P6 | 29 aprobadas, 12 de ellas de la spec 004 |
| `tests/test_r17.py` | el R-17 con `_plan_de_accion` sobre la regla compartida, sin cambios en sus expectativas | 42 aprobadas |
| `db/pruebas/correr_pruebas.sh` | las migraciones, los datos, las pruebas A y R de `pruebas.sql`, Q01 a Q15 y el camino de Neon | «RESULTADO: todo pasó» |
| `tests/servicios/api.test.ts` y `formato.test.ts` del Front | `obtenerResultados()` y las cifras con coma decimal | 38 aprobadas en los dos archivos |
| `e2e/humo.spec.ts` del Front | P6 de docente410 con las cifras de las celdas B, E, G y H del bloque II del R-17 de la misma carga de la 410, y el profesor ajeno sin la 410 en P6 ni en `GET /api/resultados` | 5 passed en local, contra la API del clúster desechable de `api_local.sh` |

En la rama `develop` de Neon, `revisar_permisos_resultados.sql` corre desde el Windows de Jefferson con `herramientas_neon/lectura_neon.sh`, en una sesión de solo lectura, y da `t` en los 16 objetos y «Faltan 0 permisos de lectura de la ruta 12.» (T021). Con 150 secciones sembradas con `publicar()` y `filas_inventadas()`, el plan de `EXPLAIN` deja el filtro por `carga_id` bajo la agregación de la vista, y la mediana de tres peticiones del coordinador es 0,024 s.

## Requisitos funcionales

| FR | Estado | Evidencia |
| --- | --- | --- |
| FR-001 | Cumplido | US-38, escenarios 3, 5 y 6, y US-39, escenario 5; la ruta sin `periodo` en `tests/test_api_resultados.py` |
| FR-002 | Cumplido | US-38, escenarios 1, 2 y 4, y US-44, escenario 1 |
| FR-003 | Cumplido | US-38, escenario 7, y `tests/test_rutas_protegidas.py` |
| FR-004 | Cumplido | la transacción y el reemplazo a mitad de la lectura en `tests/test_api_resultados.py`; la lista de `carga_id` viaja como `int[]` y sale de la misma lectura |
| FR-005 | Cumplido | US-37, escenario 1, y el PI 5.10 y la segunda versión de catálogo de T035 |
| FR-006 | Cumplido | US-42, escenario 1, y la sección 412 de 450002 campo por campo |
| FR-007 | Cumplido | US-37, escenario 2, y `cifra()` en `tests/test_resultados.py` |
| FR-008 | Cumplido | US-37, escenario 3, US-40, escenario 1, y `tests/test_resultados.py` |
| FR-009 | Cumplido | US-39, escenarios 1 y 2 |
| FR-010 | Cumplido | US-41, escenarios 1 a 3, y la comparación con la constancia en `tests/test_api_resultados.py` |
| FR-011 | Cumplido | US-37, escenario 5, y US-44, escenario 2, en `App.test.tsx` |
| FR-012 | Cumplido | US-37, escenario 4, con el ancho, `aria-hidden`, la línea de la meta y el contraste de 3 a 1 que mide la prueba |
| FR-013 | Cumplido | US-39, escenario 6, y la prueba de los nulos de la regla, del instrumento y del plan |
| FR-014 | Cumplido | US-41, escenario 4 |
| FR-015 | Cumplido | US-37, escenario 6 |
| FR-016 | Cumplido | US-38, escenario 8, US-42, escenario 4, y US-44, escenario 2; P2 conserva su prueba sin porcentajes y P4 suma la suya |
| FR-017 | Cumplido | a5d678c del Front; la comprobación de la sección 10 da «0 mensajes de los escenarios sin contrato» con la carpeta de la spec 004, y OpenAPI publica los 7 caminos que cuenta el contrato |
| FR-018 | Cumplido | 55a66b6 del Back |
| FR-019 | Cumplido | una prueba por escenario, la regla de copia nueva y las cargas sembradas con `publicar()` y `filas_inventadas()`, sin exports nuevos en `tests/datos_inventados/` |
| FR-020 | Cumplido | T020 en la base desechable y T021 en la rama `develop` de Neon |
| FR-021 | Cumplido en local, pendiente en la vista previa | el humo local da 5 passed; la corrida contra la vista previa de `develop` espera las dos fusiones (T071), porque la vista previa del Front reescribe `/api` hacia la de `develop` del Back |

## Criterios de éxito

| SC | Estado | Evidencia |
| --- | --- | --- |
| SC-001 | Cumplido | US-37, escenario 1, con 9 indicadores, 3 en la meta y 6 debajo |
| SC-002 | Cumplido | US-38 y `tests/test_rutas_protegidas.py` |
| SC-003 | Cumplido | US-40, escenarios 1 y 2, con los 9 indicadores de docente.varias y el 5.2 con un estudiante sin evidencia |
| SC-004 | Cumplido | US-39, escenario 6 |
| SC-005 | Cumplido | 150 secciones, el filtro bajo la agregación en el plan de `EXPLAIN` y una mediana de 0,024 s |
| SC-006 | Cumplido | US-40, escenario 3, que compara todas las tablas de `abet` y de `acceso`, y Q01 a Q14 en 0 filas |
| SC-007 | Cumplido | cada fila escribe su estado, y las pruebas de P6 buscan por rol y por texto |
| SC-008 | Pendiente de T071 | el humo local ya compara P6 con el R-17 de la misma carga de la 410, y la corrida en la vista previa de `develop` llega después de las fusiones |

## Decisiones abiertas

D-32 (resumen de un PI en varias secciones y de un SO en sus PI), D-33 (agregado del curso o de la carrera para el profesor) y D-34 (descripción del instrumento) siguen con la Coordinación de Ambiental en T005. Mientras tanto rige su valor provisional, así que la ruta no suma secciones ni resume un SO, P6 no muestra un agregado y la línea del instrumento trae solo su nombre. D-12 y D-30 siguen con su dueño y su valor, y si alguna de estas decisiones cambia, sus escenarios se reescriben antes que el código.

## Pendiente

1. T005, D-32 a D-34 con la Coordinación de Ambiental, y el recordatorio de D-12 y D-30.
2. T070 queda hecha el 2026-11-18. Jefferson autoriza en el chat empujar y abrir los PR («Sí, empuja y abre») y fusionarlos («Sí, fusiónalos»), y el PR #31 entra a `develop` en f403d52 y el PR #20 del Front en 778ae23.
3. T071, el humo de P6 contra la vista previa de `develop` después de las dos fusiones, con la rama `develop` de Neon restablecida y las contraseñas que asigna Jefferson con `herramientas_neon/humo_preview.sh`. En la vista previa el profesor ajeno es docente411, porque docente.varias no existe en Neon.
4. T072, la versión hacia `main` y Production, sin migración en Neon.
5. El PR #29 del Back, que documenta la regla fija de M24 a M26 en BR-R17-02, también agrega un bloque a la misma regla, así que el PR #29, que se fusiona después de la spec 004, resuelve un conflicto de inserción.
