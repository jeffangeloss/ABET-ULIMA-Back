# Audit: Programación docente del ciclo, cargada desde el archivo de la carrera

**Fecha**: 2026-11-22, cierre de T010 a T012, T020, T021, T030 a T034 y T040, y la parte de `audit.md` de T050  
**Spec**: [spec.md](./spec.md)  
**Plan**: [plan.md](./plan.md)  
**Comando**: `uv run --frozen --offline --no-build pytest -q -p no:cacheprovider` en el Back, `bash scripts/preflight.sh` y `bash db/pruebas/correr_pruebas.sh` sobre el clúster desechable de `db/pruebas/cluster_desechable.sh`  
**Resultado**: corrida del 2026-11-22 sobre `feat/006-programacion-docente`, que sale de `develop` 7fc19a9, sin commit. La suite completa del Back da 1686 passed y 15 skipped in 163.27s (0:02:43), después de los arreglos de las dos revisiones del código, con los 29 casos de los dos `.feature` de la spec 006 aprobados. Las pruebas de la base dan «RESULTADO: todo pasó», con Q01 a Q14 en 0 filas y Q15 aprobada. La revisión previa da «Revisión previa sin fallas (todo).»  
**Estado**: Spec 006 construida en la copia de trabajo `wt/back-006`, sin commit ni push. Faltan `MEMORIA.md` y `CHANGELOG.md` de T050, la integración continua del PR y la corrida real de la fase 6 (T060 a T066), que espera a Jefferson

Esta auditoría cruza cada historia de usuario (user story, US) de la spec 006 con sus escenarios en Gherkin, la prueba que los ejecuta y su resultado del 2026-11-22. Las 15 pruebas omitidas de la suite no tocan esta spec, porque son los escenarios de US-20 que esperan a T018, los de `base_neon.feature` que se comprueban en Neon y una prueba de `tests/test_cluster_desechable.py` que solo corre en la CI, como antes de la spec 006. Ningún escenario de la spec lleva `@delegado_a_vitest`, porque la spec no cambia ninguna pantalla, y `tests/aceptacion/pasos/test_lectura_gherkin_es.py` lo comprueba.

## Resumen

| Conjunto | Escenarios | Casos | Aprobados | Omitidos | Pendientes |
| --- | --- | --- | --- | --- | --- |
| Spec 006 (US-55 a US-58) | 19 | 29 | 29 | 0 | 0 |

Todo caso se comprueba contra el informe del guion, la base de la copia del escenario o la respuesta de la API, sin dobles del sistema bajo prueba. El guion corre como proceso aparte con `python -I`, como en el Windows de Jefferson, y recibe las variables de libpq que arma `tests/cargas_de_prueba.entorno_de_programacion()`, que exige el clúster desechable con `cluster_desechable.exigir()` antes de cada corrida. Ninguna prueba alcanza localhost:5432, Neon ni el Windows.

## Historias

Los escenarios viven en `specs/006-programacion-docente/aceptacion/programacion_docente.feature` (P) y `secciones_sin_docente.feature` (S), y sus pasos en `tests/aceptacion/pasos/test_programacion_docente_feature.py` y `test_secciones_sin_docente_feature.py`, con los comunes en `tests/aceptacion/pasos/conftest.py`.

| Historia | Escenario | Archivo | Casos | Resultado |
| --- | --- | --- | --- | --- |
| US-55 | La corrida en seco informa y no escribe | P | 1 | aprobado |
| US-55 | La corrida con --aplicar escribe y se puede repetir | P | 1 | aprobado |
| US-55 | El profesor cargado recibe solo su sección en GET /api/secciones | P | 1 | aprobado, con la API conectada con el rol de la aplicación |
| US-55 | Un correo con mayúsculas o espacios se normaliza | P | 1 | aprobado |
| US-55 | Dos profesores en la misma sección dan dos asignaciones | P | 1 | aprobado |
| US-55 | El guion no asigna contraseñas | P | 1 | aprobado |
| US-56 | Una asignación que el archivo no trae se informa y no se borra | P | 1 | aprobado |
| US-56 | Un coordinador que también dicta conserva su rol | P | 1 | aprobado |
| US-56 | Un profesor dado de baja no se reactiva | P | 1 | aprobado |
| US-56 | Una sección de una asignatura sin plan de medición entra con aviso | P | 1 | aprobado, con el plan de 450010 retirado en la copia del escenario |
| US-57 | Una fila inválida rechaza el archivo entero | P | 6 | aprobado |
| US-57 | El informe nombra todas las filas inválidas | P | 1 | aprobado, con una falla de la base y una de forma en el mismo informe |
| US-57 | Falta una columna obligatoria | P | 1 | aprobado |
| US-57 | Una falla de la base deshace todo | P | 1 | aprobado, con un disparador creado solo en la copia del escenario |
| US-57 | El guion no corre sin sus argumentos ni con el archivo dentro del repositorio | P | 4 | aprobado, con PGHOST en una carpeta sin socket y PSQL en un programa que no existe |
| US-58 | La consulta encuentra la sección sin profesor activo | S | 3 | aprobado |
| US-58 | Una sección de una asignatura sin plan de medición no aparece | S | 1 | aprobado |
| US-58 | La consulta no escribe | S | 1 | aprobado |
| US-58 | La consulta pide el periodo | S | 1 | aprobado |

En el escenario de los argumentos, la prueba del archivo dentro de la copia de trabajo arma un repositorio falso en `tmp_path`, con `.git` como archivo, como en un worktree, y con su propia copia del guion y de su SQL, así que ningún archivo de prueba entra al repositorio real. En los cuatro casos el código 2 prueba además que el guion no se conectó, porque un psql invocado no existe y habría dado el código 3.

## Pruebas unitarias y de integración

`tests/test_cargar_programacion.py` suma 90 pruebas aprobadas, que cubren lo que los escenarios no recorren.

| Grupo | Pruebas | Lo que debe pasar y lo que no debe pasar |
| --- | --- | --- |
| Lectura y forma, sin base (T030) | 48 | La normalización del correo es la de `app.sesion.normalizar_correo()`, el guion importa solo la biblioteca estándar, la BOM no cambia lo leído, las columnas ajenas no se guardan, una línea vacía conserva la numeración, cada falla de forma da su mensaje con un solo motivo por fila y en un orden fijo, una celda de curso vacía no cuenta como otro curso en codocencia, un correo o un curso con un carácter invisible o de control (U+200B, U+FEFF, U+2060, U+00AD, BEL, salto de línea o retorno de carro) se rechaza sin repetir la celda, las letras acentuadas siguen siendo válidas y un archivo ilegible da código 1 sin invocar psql |
| Argumentos y repositorio (T030) | 19 | Cada argumento inválido da código 2 sin invocar psql, un argumento desconocido o abreviado, como `--ap` o `--per`, da la línea de uso, un archivo que no se puede abrir da código 1 sin invocar psql, un archivo dentro de un repositorio con `.git` como carpeta o como archivo no se lee, el guion corre con `python -I` y escribe su informe en UTF-8, sin psql o con un psql de otra versión el código es 3, y psql recibe `-w`, así que nunca pide la contraseña, con un informe que no afirma que nada se guardó cuando la conexión se corta con `--aplicar` |
| Base de partida (T021) | 1 | `tests/cargas_de_prueba.base_de_partida_006()` siembra la vigencia, los dos planes y el coordinador, sin secciones ni profesores, y se puede repetir sin filas nuevas |
| Corridas contra la base (T031) | 17 | Una fila repetida cuenta una vez, el resumen usa el singular con una fila, el curso nulo se completa y la corrida no cierra con «Sin cambios.», otro curso en la base o un curso de otra sección rechazan la fila, un periodo que no existe rechaza el archivo sin informar como de otra sección el curso de una sección de 2026-2, las fallas de forma y de la base salen juntas por fila, los avisos de la sección ausente y de la asignatura fuera del plan de estudios salen en su orden, el SQL sin `-v aplicar` se detiene sin escribir, los tres INSERT nombran su restricción y no hay DELETE, una base que no responde da código 3, con su informe propio con `--aplicar`, una abreviatura de `--aplicar` no escribe y un correo con un espacio de ancho cero no crea un usuario |
| Dueño sin superusuario | 1 | Con un rol `abet_demo_dueno_…` dueño de la copia, sin superusuario y con TEMP retirado a PUBLIC, como `neondb_owner` en Neon, el guion escribe y cierra con «Cambios guardados.». El rol se borra al terminar |
| Tiempo (T034, SC-005) | 1 | La corrida en seco de un archivo inventado de 300 filas termina en 0,07 s en el clúster desechable, por debajo de los 10 s de SC-005, y no deja filas |
| `.gitignore` (T033) | 3 | `git check-ignore --no-index` ignora `programacion_*.csv` en la raíz, en `db/herramientas/` y dentro de `tests/datos_inventados/`, porque la línea va después de las negaciones de esa carpeta |

`tests/aceptacion/pasos/test_lectura_gherkin_es.py` suma los dos `.feature` de la spec al analizador de pytest-bdd (T011), con 12 pruebas parametrizadas nuevas y una que exige 19 escenarios, 29 casos, `@spec006` y `@corte1` en cada escenario y ningún `@delegado_a_vitest`. Las 40 pruebas del archivo pasan.

## Requisitos y criterios de éxito

| Requisito | Dónde se comprueba |
| --- | --- |
| FR-001, FR-002 y FR-003 | Escenarios de US-55 y US-57, y los grupos de lectura, forma y argumentos de `tests/test_cargar_programacion.py`, con la propuesta de los caracteres invisibles o de control |
| FR-004 y FR-006 | «Una fila inválida rechaza el archivo entero», «El informe nombra todas las filas inválidas», «Una falla de la base deshace todo» y las corridas contra la base |
| FR-005 y SC-004 | Los escenarios de US-56, «El guion no asigna contraseñas» y la prueba de los INSERT sin DELETE |
| FR-007 | Los escenarios de US-55 y US-56 y las pruebas de los avisos, con la duda de los cursos completados |
| FR-008 | Las pruebas de los códigos 0 a 3, con el código 1 de un archivo que no se puede abrir, el código 2 de una opción abreviada y el código 3 sin psql, con un psql de otra versión, con una base que no responde, en seco y con `--aplicar`, y con el disparador |
| FR-009 y SC-007 | «El guion no corre sin sus argumentos ni con el archivo dentro del repositorio», la prueba del repositorio con `.git` como carpeta o como archivo, las pruebas de `.gitignore` y la revisión previa. Como piden los Ejemplos del `.feature`, el rechazo muestra la celda que lo causa, aunque FR-009 nombra solo la fila, la asignatura, la sección y el correo y la regla 6 de `AGENTS.md` prohíbe el valor leído en un rechazo, choque que queda como pregunta en la Clarification «Session 2026-11-22» de `spec.md` |
| FR-010 | La prueba del dueño sin superusuario y `db/README.md`. La conexión real desde el Windows queda para T063 |
| FR-011 | Los escenarios de US-58 |
| FR-012 | La variante «programacion» del conftest, el paso de la base de partida y la prueba del ayudante |
| FR-013 | Sin migración ni cambios en `app/`, `crear_rol_app.sql` ni `db/pruebas/pruebas.sql`, con Q01 a Q15 en 0 en `correr_pruebas.sh` |
| FR-014 | BR-ACCESO-11 en `specs/features/acceso/acceso.spec.md` y el apartado «Programación docente del ciclo (spec 006)» de `db/README.md` |
| FR-015 y SC-006 | Quedan para la fase 6, porque piden Neon y el permiso de Jefferson |
| SC-001, SC-002, SC-003 y SC-005 | «La corrida en seco informa y no escribe», «La corrida con --aplicar escribe y se puede repetir», los escenarios de US-57 y la prueba de 300 filas |

## Cambios de la revisión de T006

La construcción sigue la crítica de AD-01 a AD-05 y deja su resultado en `revision-historias.md`, en el apartado «Revisión de AD-01 a AD-05 por el crítico (T006, 2026-11-22)». `plan.md` cambia sus viñetas Guion, SQL, Conexión y Pruebas, con la marca «cambio del 2026-11-22, T006». AD-03 cambia de título y cada INSERT nombra su objetivo. Las dudas que la spec no fija quedan en la Clarification «Session 2026-11-22» de `spec.md`, con el valor que el guion aplica mientras tanto.

## Cambios de las dos revisiones del código

Las dos revisiones del código del 2026-11-22 dejan estos arreglos en el guion, su SQL y las pruebas, y cada cambio de comportamiento tiene su prueba, escrita antes del cambio. argparse ya no acepta abreviaturas, así que `--ap` o `--apli` no abren la escritura. Un correo o un curso con un carácter de las categorías Unicode Cf o Cc rechaza la fila, y un archivo que no se puede abrir termina con código 1 y la línea final de rechazo, sin traceback. psql corre con `-w`, también en el comando de `secciones_sin_docente.sql` de `db/README.md`, y con `--aplicar` un corte de la conexión ya no afirma que nada se guardó. Un periodo que no existe deja de sumar un `CURSO_DE_OTRA` engañoso, y el paso de la sección sin asignación comprueba que la sección quedó en la base. Las dudas que estos arreglos abren quedan en la Clarification «Session 2026-11-22» de `spec.md`, y los comentarios del guion y de las pruebas remiten a ella.

## Lo que esta auditoría no prueba

- El guion no corrió con Python 3.14 ni con el psql 18 del Windows, ni a través de `en_windows.py`. La prueba con `python -I` y la salida en UTF-8 lo acercan, y T063 lo comprueba con la corrida en seco real.
- La conexión con `PGSSLMODE=require` y `PGCHANNELBINDING=require` contra Neon, el respaldo desde el Windows con `gpg` y la consulta con `abet_respaldo` quedan para T061, T063 y T065.
- El dueño de las tablas en Neon es `neondb_owner`. La prueba del dueño sin superusuario recibe sus permisos por GRANT y no por ser dueño de cada tabla, así que la corrida en seco de T063 es la prueba real de esos permisos.
- La integración continua no corrió, porque la rama no tiene commit ni push.
- Un choque de `uq_seccion_curso_bb` entre dos corridas que coinciden en el tiempo no se reproduce. La prueba comprueba que cada INSERT nombra su restricción, así que ese choque llegaría como error de la base, con código 3.
