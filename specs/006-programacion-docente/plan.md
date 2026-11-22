# Implementation Plan: Programación docente del ciclo, cargada desde el archivo de la carrera

**Branch**: `docs/005-om-bp-y-006` (PR a `develop`), con la implementación en `feat/006-programacion-docente` del Back después de la aprobación | **Date**: 2026-11-21 | **Spec**: [spec.md](./spec.md)

## Summary

Con D-10 la universidad autoriza los datos reales en Neon, pero ningún guion carga las secciones, los profesores ni las asignaciones reales, así que ningún profesor encuentra su sección en P2 en la semana 15. El plan agrega `db/herramientas/cargar_programacion.py`, que lee el CSV de la programación docente, revisa la forma de cada fila antes de conectarse y entrega las filas a psql 18. Un solo SQL, `db/herramientas/cargar_programacion.sql`, cruza el archivo con la base, escribe solo con INSERT en `abet.seccion`, `acceso.usuario_autorizado` y `acceso.docente_seccion` y arma el informe dentro de una transacción, que termina con ROLLBACK en seco y con COMMIT con `--aplicar`. La consulta informativa `db/plataforma/neon/secciones_sin_docente.sql` lista después las secciones con plan de medición sin profesor activo. La prueba de cierre es la corrida en seco en la rama principal de Neon con el archivo real, desde el Windows de Jefferson, y la corrida con `--aplicar` con su permiso.

## Technical Context

- **Guion.** Python 3.12 con la biblioteca estándar (`argparse`, `csv`, `json`, `pathlib` y `subprocess`), sin dependencias nuevas, para que corra en el Windows con Python 3.14 sin instalar paquetes (AD-01). Lee el CSV con `encoding="utf-8-sig"`, que acepta la BOM, normaliza cada correo con `strip()` y `lower()`, como `app.sesion.normalizar_correo()` y `ck_usuario_autorizado_correo`, y revisa la forma de FR-003 antes de conectarse, con un motivo por fila y un orden fijo de revisiones. Si falla el archivo entero (falta una columna, no es UTF-8 o no trae filas), informa y termina con código 1 sin conectarse. Si fallan filas, igual entrega todas las filas a psql, cada una con su número y la marca de su falla de forma, para que el informe junte en el orden de las filas los motivos de forma y los de FR-004 (cambio del 2026-11-22, T006). Al comenzar fija la salida en UTF-8, porque con `python -I` el Windows escribiría en cp1252 hacia una tubería, y entrega las filas a psql como bytes UTF-8.
- **SQL.** `db/herramientas/cargar_programacion.sql` corre con `psql -X -q -A -t -v ON_ERROR_STOP=1 -v periodo=… -v aplicar=0|1`, exige las dos variables con `\if :{?periodo}` y `\if :{?aplicar}`, con el molde de `pi_sin_descripcion_instrumento.sql`, y recibe las filas por la entrada estándar con `\copy programacion_archivo FROM pstdin WITH (FORMAT csv)` a una tabla temporal `ON COMMIT DROP`. Dentro de un solo `BEGIN`, sin `psql -1`, revisa FR-004 solo en las filas sin falla de forma. Con cualquier falla, de forma o de la base, escribe los motivos y cierra con ROLLBACK antes de los INSERT. Sin fallas, completa los `curso_blackboard` nulos, inserta con `ON CONFLICT (periodo_id, asignatura_id, numero) DO NOTHING`, `ON CONFLICT (correo) DO NOTHING` y `ON CONFLICT (usuario_id, seccion_id) DO NOTHING`, cuenta lo nuevo, arma los avisos de FR-007 y cierra con `\if :aplicar` COMMIT o ROLLBACK (AD-02 y AD-03). El SQL no lanza un error para el código 1. Escribe cada resultado como un arreglo JSON y termina con una línea centinela, RECHAZADO, SECO o GUARDADO, que el guion lee y convierte en el informe. Sin la línea centinela, o con psql terminando con un código distinto de 0, el guion da código 3 sin reenviar el error de psql, porque su DETAIL repetiría los valores de la fila, y escribe en la salida de errores solo el SQLSTATE, que `\set VERBOSITY sqlstate` deja sin texto. Corre psql con `LC_MESSAGES=C` y `PGCLIENTENCODING=UTF8` (cambio del 2026-11-22, T006).
- **Conexión.** Las variables de libpq (`PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` y `PGSSLMODE`), que psql lee solo, sin argumentos con secretos. En Neon, `~/.claude/scripts/en_windows.py` pasa los valores de `bd/.env.neon` por la entrada estándar de SSH y el comando los asigna a esas variables en el Windows, con el usuario dueño de la base y la conexión directa, sin el repartidor de conexiones, como los guiones de `db/datos/`. Desde el Windows, `db/README.md` asigna cada `NEON_*` a su variable de libpq y suma `PGSSLMODE=require`, `PGCHANNELBINDING=require`, `PGCLIENTENCODING=UTF8` y `PSQL` con la ruta completa de psql 18, como los ayudantes que ya corren allí (cambio del 2026-11-22, T006).
- **Base.** Sin migración y sin cambios en `crear_rol_app.sql`. `abet_app` sigue sin escribir `abet.seccion`, `acceso.usuario_autorizado` ni `acceso.docente_seccion`, y el guion corre con el dueño (FR-010). Q01 a Q15 no cambian.
- **Consulta.** `db/plataforma/neon/secciones_sin_docente.sql`, con el molde de `pi_sin_descripcion_instrumento.sql`. Exige `-v periodo`, fija `default_transaction_read_only`, lista asignatura y sección y termina con la cantidad. En Neon la corre `abet_respaldo`, que lee `abet` y `acceso` desde V1_09.
- **Pruebas.** pytest-bdd 9 con los dos `.feature` de `specs/006-programacion-docente/aceptacion/`, pruebas unitarias de la lectura y de la forma en `tests/test_cargar_programacion.py` y un ayudante de `tests/cargas_de_prueba.py` que siembra la base de partida (propuesta). Todo corre en el clúster desechable de `tests/cluster_desechable.py`, con psql 18 del mismo clúster, y nunca en localhost:5432. El paso que corre el guion le arma un entorno propio con PGHOST, PGPORT y PGUSER del clúster y PGDATABASE de la copia del escenario, y `cluster_desechable.exigir()` lo revisa antes del subproceso. La variante «programacion» de `tests/aceptacion/pasos/conftest.py` parte sin los datos de 2026-2 y siembra la base de partida en su plantilla. El caso del archivo dentro de la copia de trabajo arma un repositorio falso en `tmp_path`, con `.git` como archivo, y nunca escribe en el repositorio real (cambio del 2026-11-22, T006).
- **Datos.** Solo datos inventados en el repositorio, con correos de `@example.invalid` y archivos armados en `tmp_path`. El archivo real de la carrera vive fuera de todo repositorio, llega al Windows con `scp` a una carpeta propia y se borra al terminar (AD-05 y J-42). `.gitignore` suma `programacion_*.csv`.
- **Restricciones.** La spec 005 cambia en paralelo, en la misma rama de documentación, y su construcción toca `abet_carga/`, `app/` y V1_12. La spec 006 no toca esos archivos, así que las dos construcciones no chocan salvo en `MEMORIA.md`, `CHANGELOG.md`, `specs/README.md` y `acceso.spec.md`. Una sola línea de trabajo construye primero la spec 006, porque la capacitación de la semana 14 la necesita (Clarification «Session 2026-11-21» de la spec).

## Constitution Check

| Principio | Cumplimiento |
| --- | --- |
| I · La base es la única fuente de verdad | Las secciones, los profesores y las asignaciones viven en las tablas que ya existen, y el archivo de la carrera es solo la entrada de una corrida |
| II · Privacidad por diseño y solo datos inventados | El repositorio solo trae correos de `@example.invalid`. El guion lee solo cinco columnas, ignora las demás sin leer sus valores, se niega a leer un archivo dentro del repositorio y no copia el archivo real |
| III · Toda carga es atómica y trazable | Una sola transacción, con ROLLBACK ante cualquier error y una corrida en seco con el mismo SQL. `creado_en` y `asignado_en` fechan cada usuario y cada asignación nuevos |
| IV · Las reglas son datos versionados y lo provisional se ve | D-44 y D-45 quedan con su valor provisional, y el formato del CSV es provisional hasta que la carrera lo fije |
| V · Contrato, historias auditadas y prueba antes de desplegar | Historia auditada en la fase 0, regla viva BR-ACCESO-11 en la fase 1, pruebas antes del código y corrida en seco en Neon antes de escribir |
| VI · Capas y privilegio mínimo | `abet_app` no gana permisos. El guion corre con el dueño solo desde el Windows, y la consulta con `abet_respaldo`, de solo lectura |

## Project Structure

```
ABET-ULIMA-Back/
  db/herramientas/cargar_programacion.py    lectura, forma, llamada a psql e informe (nuevo)
  db/herramientas/cargar_programacion.sql   cruce con la base, INSERT y avisos en una transacción (nuevo)
  db/plataforma/neon/secciones_sin_docente.sql   consulta informativa de solo lectura (nuevo)
  db/README.md                              uso del guion y de la consulta, con el orden de FR-015 (cambia)
  .gitignore                                programacion_*.csv (cambia)
  tests/test_cargar_programacion.py         pruebas unitarias de la lectura y de la forma (nuevo)
  tests/cargas_de_prueba.py                 ayudante de la base de partida sin secciones ni profesores (cambia)
  tests/aceptacion/pasos/test_programacion_docente_feature.py, test_secciones_sin_docente_feature.py   (nuevos)
  specs/006-programacion-docente/           revisión, spec, plan, tareas, aceptación y auditoría (nuevo)
  specs/features/acceso/acceso.spec.md      BR-ACCESO-11 y el guion en targets (cambia)
```

El Front no cambia, porque la spec no agrega rutas ni pantallas.

## Phases

0. **Descubrimiento.** C-C01 auditada con tres lentes y el crítico en el cambio del 2026-11-21 de la spec 005, spec, revisión de AD-01 a AD-05 por el crítico, pedido del formato del archivo a la carrera (D-44) y aprobación de Jefferson con J-42.
1. **Contrato.** BR-ACCESO-11 en la spec viva `acceso`, los dos `.feature` definitivos con el analizador de pytest-bdd y el uso del guion en `db/README.md`.
2. **Base.** Sin migración. La consulta informativa y su prueba en el clúster desechable.
3. **Guion.** Pruebas primero. Lectura y forma con sus pruebas unitarias, el SQL con sus casos de aceptación, el informe y los códigos de salida.
4. **Pruebas.** Suite completa del Back, `bash scripts/preflight.sh` y `bash db/pruebas/correr_pruebas.sh` con Q01 a Q15 en 0.
5. **Auditoría.** `audit.md`, Verification fechada en `acceso`, `MEMORIA.md` y `CHANGELOG.md`.
6. **Corrida real.** PR del Back con la integración continua en verde y fusión por Jefferson. Después, respaldo de Neon, corrida en seco en la rama principal desde el Windows, lectura del informe, `--aplicar` con el permiso de Jefferson, la consulta de US-58 y las contraseñas de los usuarios nuevos, todo antes de la capacitación de la semana 14.
