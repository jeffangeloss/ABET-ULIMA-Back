# Audit: Nombre del profesor en la base y en el R-17

**Fecha**: 2026-11-25, cierre de la construcción de la spec 010 (T050 y T060)  
**Spec**: [spec.md](./spec.md)  
**Plan**: [plan.md](./plan.md)  
**Tareas**: [tasks.md](./tasks.md)  
**Comando**: `ABET_FRONT_RAIZ=../front-010f uv run --frozen --no-build python -m pytest -q -p no:cacheprovider`, `bash db/pruebas/correr_pruebas.sh`, `bash scripts/preflight.sh` y `scripts/matriz_cumplimiento.py --front ../front-010f --comprobar` en el Back, y `npm run build`, `npx tsc --noEmit`, `npm test` y `bash scripts/preflight.sh` en el Front  
**Resultado**: corrida del 2026-11-25 sobre `feat/010-nombre-del-profesor` del Back (0692b08) y del Front (b9dd3e6), sin push. La suite completa del Back da 2772 passed y 15 skipped en 359 s, las pruebas de la base dan «RESULTADO: todo pasó» y el Front da 378 pruebas aprobadas y 1 pendiente en 26 archivos. Los 30 escenarios (42 casos) de los cuatro `.feature` tienen su prueba en pytest-bdd y pasan  
**Estado**: Spec 010 construida en local. Faltan T041 y las tareas de Jefferson (T003, T070 a T074), y la prueba de humo del Front (T040) está escrita y sin correr contra la vista previa

Esta auditoría cruza cada historia de usuario (user story, US) de la spec 010 con sus escenarios en Gherkin, la prueba que los ejecuta y su resultado del 2026-11-25. La matriz `scripts/matriz_cumplimiento.py` cubre hoy las specs 007 y 008, así que el cruce de la spec 010 se hace aquí, a mano, con cada título comprobado contra el `@scenario` de su archivo de pasos.

## Resumen

| Conjunto | Historias | Escenarios | Casos | Con prueba | Huecos |
| --- | --- | --- | --- | --- | --- |
| Spec 010 | 5 | 30 | 42 | 30 | 0 |

La matriz de las specs 007 y 008 da, con `--comprobar` y el Front de esta rama, 32 historias, 237 escenarios, 89 reglas, 10 escenarios pendientes con su razón y 0 huecos, igual que antes de la spec 010.

## Historias

| Historia | Escenarios | Pruebas | Estado | Resultado de la corrida |
| --- | --- | --- | --- | --- |
| US-95 | 7 | pytest-bdd `tests/aceptacion/pasos/test_nombre_en_la_base_feature.py`, más `db/pruebas/correr_pruebas.sh` (Q15, `probar_rol_app.sql` y roles de lectura) | Con prueba | Aprobada |
| US-96 | 7 | pytest-bdd `tests/aceptacion/pasos/test_programacion_con_nombre_feature.py`, más `tests/test_cargar_programacion.py` y `tests/test_sembrar_quimica.py` | Con prueba | Aprobada |
| US-97 | 7 | pytest-bdd `tests/aceptacion/pasos/test_profesores_en_el_r17_feature.py`, más `tests/test_r17.py` y `tests/test_r17_recuadro.py`, y Playwright `e2e/humo_quimica.spec.ts` del Front | Con prueba | Aprobada en pytest, humo del Front sin correr |
| US-98 | 4 | pytest-bdd `tests/aceptacion/pasos/test_profesores_en_el_r17_feature.py`, más `tests/test_profesores_sin_nombre.py` | Con prueba | Aprobada |
| US-99 | 5 | pytest-bdd `tests/aceptacion/pasos/test_privacidad_del_nombre_feature.py`, más `tests/test_semillas_con_nombre.py` | Con prueba | Aprobada |

## Escenarios

Cada título se comprobó contra el `@scenario` de su archivo de pasos, y los 30 tienen enlace.

| Archivo `.feature` | Historia | Escenarios | Archivo de pasos |
| --- | --- | --- | --- |
| `nombre_en_la_base.feature` | US-95 | «Un usuario sin nombre sigue siendo válido»; «La base acepta un nombre normalizado con tildes y eñes»; «La base rechaza un nombre que no está normalizado o que no parece un nombre»; «Q15 encuentra en acceso solo el correo y el nombre del usuario»; «Ninguna tabla de abet gana una columna de nombre»; «La aplicación lee el nombre y no lo escribe»; «Los roles de lectura no alcanzan el nombre y el rol de respaldo sí lo lee» | `test_nombre_en_la_base_feature.py` |
| `programacion_con_nombre.feature` | US-96 | «Un profesor nuevo entra con su nombre»; «Un profesor ya cargado sin nombre lo recibe y su rol y su estado no cambian»; «Un nombre que ya existe no se cambia»; «Un archivo sin la columna nombre responde como en la spec 006»; «Los espacios del nombre se normalizan antes de guardarlo»; «Un nombre inválido rechaza el archivo antes de conectarse»; «Dos nombres distintos para un mismo correo rechazan el archivo» | `test_programacion_con_nombre_feature.py` |
| `profesores_en_el_r17.feature` | US-97 | «Una sección con un profesor trae su nombre en D10»; «Varios profesores salen en orden alfabético sin tildes ni mayúsculas, separados por coma, y el orden es estable»; «Un profesor dado de baja sigue en D10 de su sección»; «Solo los profesores de la sección salen en D10»; «Un nombre que parece fórmula queda como texto»; «Tres nombres caben en D10:I10 y la fila 10 crece sin mover el resto de la cabecera»; «Fuera de D10 y de la fila 10 la plantilla no cambia» | `test_profesores_en_el_r17_feature.py` |
| `profesores_en_el_r17.feature` | US-98 | «Un profesor sin nombre no sale y el otro sí»; «Si ningún profesor tiene nombre, D10 queda vacía como hoy»; «La sección sin profesor tiene R-17 con D10 vacía»; «La consulta informativa cuenta las secciones publicadas con un profesor sin nombre» | `test_profesores_en_el_r17_feature.py` |
| `privacidad_del_nombre.feature` | US-99 | «Fuera de D10 el libro no repite el nombre»; «Las rutas de cargas y de sesión no traen el nombre»; «El registro de la aplicación no trae el nombre»; «Las semillas solo traen nombres inventados con correos de example.invalid»; «Git no rastrea un archivo de programación con la columna nombre fuera de los datos inventados» | `test_privacidad_del_nombre_feature.py` |

## Suites completas (T050)

| Repositorio | Comando | Resultado |
| --- | --- | --- |
| Back | `ABET_FRONT_RAIZ=../front-010f uv run --frozen --no-build python -m pytest -q -p no:cacheprovider` | 2772 passed y 15 skipped en 359.79 s |
| Back | `bash db/pruebas/correr_pruebas.sh` | «RESULTADO: todo pasó» |
| Back | `bash scripts/preflight.sh` | Sin fallas |
| Back | `scripts/matriz_cumplimiento.py --front ../front-010f --comprobar` | 0 huecos y 10 pendientes con su razón |
| Front | `npm run build` y `npx tsc --noEmit` | Sin errores |
| Front | `npm test` | 26 archivos, 378 pruebas aprobadas y 1 pendiente |
| Front | `bash scripts/preflight.sh` | Sin fallas |
| Front | `npx playwright test e2e/humo_quimica.spec.ts --list` | Lista 11 pruebas con la de D10. No corre contra la vista previa porque necesita las contraseñas de Jefferson y el despliegue de V1_16 |

## Requisitos y criterios de éxito

| Criterio | Estado al 2026-11-25 | Evidencia o razón |
| --- | --- | --- |
| SC-001 | Cumplido | Los 30 escenarios tienen prueba en pytest-bdd y pasan, y `correr_pruebas.sh` termina con «RESULTADO: todo pasó» |
| SC-002 | Pendiente de Jefferson | Se comprueba en develop de Neon después de V1_16 y de las semillas (T071 y T072). El humo de T040 lo verifica en la vista previa |
| SC-003 | Cumplido | Los escenarios de privacidad de US-99 y `tests/test_semillas_con_nombre.py` pasan, y el 2026-11-25 la revisión cambia un nombre de apariencia real de dos pruebas por «Docente Sin Forma Inventada» |
| SC-004 | Pendiente de Jefferson | Lo mide `profesores_sin_nombre.sql` sobre la rama de Neon con la programación real (T073 y T074) |

| Requisito | Historia | Prueba |
| --- | --- | --- |
| FR-001 a FR-003 | US-95 | `nombre_en_la_base.feature`, con los casos de la restricción ampliados el 2026-11-25 |
| FR-004 a FR-007 | US-96 | `programacion_con_nombre.feature` y `tests/test_cargar_programacion.py` |
| FR-008 a FR-010 | US-97 y US-98 | `profesores_en_el_r17.feature`, `tests/test_r17.py` y `tests/test_r17_recuadro.py` |
| FR-011 | US-98 | `tests/test_profesores_sin_nombre.py` y el último escenario de US-98 |
| FR-012 y FR-013 | US-99 | `privacidad_del_nombre.feature` y `tests/test_semillas_con_nombre.py` |
| FR-014 | Jefferson | T071 y T073, sin código |
| FR-015 y FR-016 | US-95 a US-99 | Líneas Verification de las specs vivas `acceso` y `r17`, y esta auditoría |

## Pendientes y riesgos

- Las dos ramas `feat` salen de antes de que `origin/docs/010` integrara la spec 009, así que al fusionar chocan en `MEMORIA.md` (Back y Front) y en `tests/aceptacion/pasos/test_lectura_gherkin_es.py` (Back), y después hay que volver a correr la suite con la spec 009 sobre V1_16.
- La coma de ancho completo U+FF0C, los dígitos que no son ASCII y U+3000 siguen entrando al nombre, porque FR-001 no los nombra. Lo decide Jefferson.
- V1_16 no está aplicada en ninguna rama de Neon, y T041 y T070 a T074 son de Jefferson.
