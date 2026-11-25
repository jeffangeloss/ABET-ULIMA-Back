# Tasks: Nombre del profesor en la base y en el R-17

**Input**: spec.md, plan.md · **Estado al 2026-11-25**: spec aprobada por Jefferson en el chat el 2026-11-24 («Apruebo la spec 010, sepáralos por coma»), con D-12 y D-58 y J-65 a J-71 en sus valores provisionales. `fix/r17-recuadros-y-filas-de-pi` ya está en `develop` del Back (PR #58, 0d92ad9) y `docs/r17-recuadros-y-filas-de-pi` en el del Front (PR #42, 3b0247e), así que la construcción puede empezar. Cada tarea lleva su estimación en horas, que suma unas 30

Cada tarea lleva al comienzo el lugar donde ocurre, como en las specs anteriores. `[Back]` es ABET-ULIMA-Back, `[Front]` es ABET-ULIMA-Front, `[Base]` es la base como código de `db/` con sus pruebas en el clúster desechable y `[Jefferson]` marca lo que solo él decide o corre desde su Windows. Toda escritura en Neon la hace Jefferson, o Claude con su permiso, desde el Windows por `en_windows.py`, con respaldo previo y sin credenciales en archivos ni argumentos. Cada tarea de código escribe primero la prueba de sus escenarios y la ve fallar.

## Fase 0 · Descubrimiento

- [x] T001 Candidatas, auditoría con tres lentes y el crítico, spec y cuatro `.feature` · 2026-11-24
- [x] T002 [Jefferson] Aprobar la spec y J-65 a J-71, con D10 separada por comas · 2026-11-24, «Apruebo la spec 010, sepáralos por coma»
- [ ] T003 [Jefferson] Llevar D-12 a la Coordinación de Ambiental y a la Oficina de Calidad y D-58 a la coordinación de cada carrera, y pedir la hoja de la programación con la columna de nombres [US-95] [US-96] [US-97] · 0,5 h
- [x] T004 [Jefferson] Fusionar `fix/r17-recuadros-y-filas-de-pi` del Back y `docs/r17-recuadros-y-filas-de-pi` del Front en `develop`, condición de FR-009 y de J-71 [US-97] · 2026-11-24, PR #58 del Back (0d92ad9) y PR #42 del Front (3b0247e)

## Fase 1 · Contrato

- [x] T010 [Back] BR-ACCESO-15 y BR-R17-14 en las specs vivas `acceso` y `r17`, con los cambios fechados de BR-ACCESO-01, BR-ACCESO-11 y BR-R17-07, y la fila de `specs/README.md` [US-95] [US-96] [US-97] [US-98] [US-99] · 2026-11-25
- [x] T011 [Front] Línea fechada «cambio del 2026-11-25 (spec 010, propuesta)» en `docs/03-api/contrato.md`, en la ruta 7 y en la sección 13.6, con AD-76 y sin ruta ni JSON nuevo [US-97] · 2026-11-25
- [x] T012 [Back] Cambio fechado de FR-002, FR-005, FR-007, FR-009 y FR-013 en `specs/006-programacion-docente/spec.md` y del valor provisional de D-12 en `specs/001-mvp-carga-r17/spec.md`, y la fila de D10 de `plantillas/README.md` [US-96] [US-97] · 2026-11-25
- [x] T013 [Back] `db/README.md` con el uso de la columna `nombre` del guion, la declaración de que el respaldo de Neon lleva nombres de profesores y entra a la Ley 29733, el orden V1_16 antes de la carga de nombres y el comando de `en_windows.py` sin ningún valor secreto [US-95] [US-96] · 2026-11-25
- [x] T014 [Back] Pasos compartidos de los Antecedentes de la spec 010 en `tests/aceptacion/pasos/conftest.py`, con la base desechable de Ambiental en 2026-2 y de Química en 2026-1 y sus nombres inventados, y el conteo de la spec 010 (30 escenarios) en `tests/aceptacion/pasos/test_lectura_gherkin_es.py` [US-95..US-99] · 2026-11-25

## Fase 2 · Base

- [ ] T020 [Base] Escribir primero los escenarios de US-95 sobre la columna y después `db/migration/V1_16__nombre_del_usuario.sql`, con `nombre varchar(120)` nulable, `ck_usuario_autorizado_nombre` (recortado, sin dobles espacios, sin caracteres de control ni de formato, sin arroba, coma ni dígitos y NFC), el `COMMENT ON SCHEMA acceso` y el comentario de la columna [US-95] · 1,5 h
- [ ] T021 [Base] Escribir primero y después ampliar Q15 de `db/pruebas/pruebas.sql` con `column_name LIKE '%nombre%'` para `acceso`, hacer que `_correr_q15` de `tests/aceptacion/pasos/test_base_neon_feature.py` corra el bloque de Q15, y sumar a `db/pruebas/probar_rol_app.sql` y a las pruebas de `crear_roles_lectura.sql` el permiso de la columna (SELECT sí, INSERT y UPDATE con 42501, roles de lectura con 42501 y `abet_respaldo` que lee), con `bash db/pruebas/correr_pruebas.sh` en «RESULTADO: todo pasó» [US-95] · 1,5 h
- [ ] T022 [Base] Escribir primero la prueba de repositorio de las semillas y después los nombres inventados de `db/datos/periodo_2026_2_inventado.sql`, `varias_secciones_2026_2_inventado.sql` y `quimica_2026_1_inventado.sql`, con `ON CONFLICT (correo) DO UPDATE SET nombre = coalesce(acceso.usuario_autorizado.nombre, EXCLUDED.nombre)` y sus comprobaciones finales sin cambio [US-99] · 1 h
- [ ] T023 [Base] Escribir primero los escenarios de la consulta y después `db/plataforma/neon/profesores_sin_nombre.sql`, con la sesión en solo lectura antes de la primera consulta, `-v periodo` obligatorio y solo dos números en la salida, sin correos, nombres ni secciones [US-98] · 1 h

## Fase 3 · Back

- [ ] T030 [Back] Escribir primero `tests/test_cargar_programacion.py` y después la lectura de la columna opcional `nombre` en `db/herramientas/cargar_programacion.py`, con la normalización NFC, la regla de FR-001 antes de conectarse, los rechazos «Fila N. El nombre no es válido.» y «Fila N. El correo trae otro nombre en otra fila.» y la adaptación de `test_las_columnas_ajenas_se_ignoran_sin_leer_sus_valores` [US-96] · 2 h
- [ ] T031 [Back] Escribir primero los pasos de `programacion_con_nombre.feature` y después `db/herramientas/cargar_programacion.sql`, con el nombre en el INSERT, el UPDATE acotado a `WHERE nombre IS NULL`, el aviso de otro nombre, el resumen de cuatro términos con la columna, «Cambios guardados.» para el archivo que solo completa nombres y ningún nombre en el informe [US-96] · 3 h
- [ ] T032 [Back] Escribir primero los escenarios de US-97 y después en `abet_carga/r17.py` la función aislada de los profesores de la sección (rol PROFESOR, nombre no nulo, sin filtro de `activo`, orden NFD sin marcas y `casefold()` con `usuario_id` de desempate, unidos con «, ») leída dentro de la transacción de `generar()` y escrita en D10 con `_escribir`, con Ambiental e Industrial [US-97] · 2 h
- [ ] T033 [Back] Escribir primero y después el ajuste de texto de D10:I10 y la función pura de cabida del alto de la fila 10 con `lineas_del_recuadro()` y el ancho de D10:I10, con tope de 409 puntos, las filas 9, 11 y 29 a 36 sin cambio, `alto_de_fila_final()` intacto y las dos aserciones de `D10` nulo de `tests/test_r17.py` al día [US-97] · 2 h
- [ ] T034 [Back] Escribir primero y después comprobar los escenarios de US-98, el profesor sin nombre, ningún profesor con nombre y la 704 sin profesor con D10 vacía, y la consulta de T023 contra una base con carga publicada [US-98] · 1 h
- [ ] T035 [Back] Escribir primero y después comprobar los escenarios de US-99 sobre el libro (nombre solo en D10, nombre del archivo y propiedades), las rutas `GET /api/cargas`, `GET /api/cargas/{carga_id}` y `GET /api/sesion`, el registro `abet.api` con `caplog` y `git ls-files` sin CSV con la columna `nombre` fuera de `tests/datos_inventados/` [US-99] · 2 h
- [ ] T036 [Back] Revisar `db/herramientas/sembrar_quimica.py` y su paso `programacion`, que acepta el archivo con la columna `nombre` sin cambiar de código mientras su paso `migraciones` siga en `-target=1.14` (V1_15 y V1_16 las aplica `migrar_neon.sh`), y dejar su docstring y `tests/test_sembrar_quimica.py` al día con el orden de V1_16 [US-96] · 0,5 h

## Fase 4 · Front

- [ ] T040 [Front] Prueba de humo con Playwright en `e2e/humo_quimica.spec.ts`, contra la vista previa de develop con la siembra inventada, que lee D10 de `r17DelProfesor` con `celdasDelLibro` y espera «Profesor Inventado Setecientos Uno», sin que ninguna ruta ni pantalla cambie [US-97] · 1 h
- [ ] T041 [Jefferson] Sumar a `herramientas_neon/revisar_r17.py`, fuera de los repositorios, la comprobación de que D10 trae solo nombres de la forma inventada y de que ninguna otra celda los repite [US-99] · 0,5 h

## Fase 5 a 7 · Pruebas, auditoría y despliegue

- [ ] T050 [Back] Suites completas del Back y del Front, `bash db/pruebas/correr_pruebas.sh`, `preflight.sh` en los dos y la matriz de cumplimiento con `--comprobar` [US-95..US-99] · 1 h
- [ ] T060 [Back] `audit.md` con el cruce de historia, escenario, prueba y resultado, las líneas Verification fechadas de las specs vivas `acceso` y `r17`, `MEMORIA.md` y `CHANGELOG.md` [US-95..US-99] · 1,5 h
- [ ] T070 [Jefferson] Autorizar empujar `feat/010-nombre-del-profesor` del Back y del Front y fusionar sus PR en `develop` [US-95..US-99] · 0,5 h
- [ ] T071 [Jefferson] Respaldar develop de Neon con `db/herramientas/respaldar_neon.sh` y aplicar V1_16 con `migrar_neon.sh develop` desde el Windows con Flyway 13.9, y correr después las semillas con nombres inventados con psql no interactivo por `en_windows.py` [US-95] [US-99] · 1 h
- [ ] T072 [Jefferson] Comprobar en develop de Neon el SC-002, con el R-17 de la 701 de 5643 con «Profesor Inventado Setecientos Uno» en D10, Q04 en 0 filas y la consulta informativa en 0 para 2026-1 [US-97] [US-98] · 0,5 h
- [ ] T073 [Jefferson] Con su permiso, respaldar la rama principal de Neon y aplicar V1_16 en ella, y cargar los nombres reales con `cargar_programacion.py` desde un archivo fuera de todo repositorio, en seco y después con `--aplicar` (J-71 y D-58) [US-95] [US-96] · 1 h
- [ ] T074 [Jefferson] Correr `profesores_sin_nombre.sql` con `abet_respaldo` y llevar a la coordinación cada sección pendiente hasta que dé 0 antes de entregar los R-17 del periodo (SC-004) [US-98] · 0,5 h
