# Implementation Plan: Nombre del profesor en la base y en el R-17

**Branch**: `docs/010-nombre-del-profesor` del Back y del Front (PR a `develop`), con la implementación en `feat/010-nombre-del-profesor` después de la aprobación y de la fusión de `fix/r17-recuadros-y-filas-de-pi` | **Date**: 2026-11-25 | **Spec**: [spec.md](./spec.md)

## Summary

La casilla «Profesor:» del R-17 (D10:I10 de la hoja «Cursos de Carrera») sale vacía porque la base no guarda nombres. El plan suma la columna opcional `acceso.usuario_autorizado.nombre` con la migración V1_16 (propuesta), la vigila con Q15, la carga con una columna opcional de la programación docente de la spec 006 y llena D10 con los nombres de los profesores asignados a la sección, en orden alfabético sin tildes ni mayúsculas y separados por «, ». No hay rutas, pantallas ni dependencias nuevas, y el contrato del Front solo gana una línea fechada porque ninguna ruta ni JSON cambia (AD-76).

## Technical Context

- **Base.** PostgreSQL 18 en Neon con Flyway 13.9 desde `db/`. Una migración nueva, `V1_16__nombre_del_usuario.sql` (propuesta, solo DDL), con la columna, `ck_usuario_autorizado_nombre` y los comentarios. Q15 de `db/pruebas/pruebas.sql` amplía su filtro, `probar_rol_app.sql` y las pruebas de `crear_roles_lectura.sql` suman el permiso de la columna, y `crear_rol_app.sql` y `controles_neon.sql` no cambian. Nace `db/plataforma/neon/profesores_sin_nombre.sql` (propuesta), informativa y de solo lectura.
- **Back.** Python 3.12 con FastAPI. Cambian `db/herramientas/cargar_programacion.py` y `.sql` (columna opcional `nombre`, UPDATE acotado a `nombre IS NULL`, resumen de cuatro términos con la columna) y `abet_carga/r17.py` (función aislada de los profesores de la sección, escritura de D10 en `_cabecera()` y función pura de cabida para el alto de la fila 10, junto a `lineas_del_recuadro()`). Las semillas `db/datos/*_inventado.sql` ganan los nombres inventados con `ON CONFLICT (correo) DO UPDATE SET nombre = coalesce(...)`.
- **Front.** Sin código. `docs/03-api/contrato.md` suma la línea fechada del cambio del 2026-11-25 en la ruta 7 y en la sección 13.6, y la prueba de humo `e2e/humo_quimica.spec.ts` suma la lectura de D10 del R-17 descargado.
- **Pruebas.** pytest-bdd 9 sobre el clúster desechable de `tests/cluster_desechable.py`, nunca en localhost:5432 ni en Neon, `db/pruebas/correr_pruebas.sh` para Q15 y `probar_rol_app.sql`, pruebas unitarias en `tests/test_cargar_programacion.py` y `tests/test_r17.py`, y Playwright en `e2e/` del Front para el humo.
- **Datos.** En los repositorios, solo nombres inventados que empiezan por «Profesor Inventado», con letras, y correos `@example.invalid`. Los nombres reales viven solo en Neon y entran solo por `cargar_programacion.py` desde el Windows de Jefferson, con un archivo fuera de todo repositorio.

## Constitution Check

| Principio | Cumplimiento |
| --- | --- |
| I · La base es la única fuente de verdad | D10 sale de `acceso.docente_seccion` y `acceso.usuario_autorizado` dentro de la misma transacción de `generar()` (BR-R17-12), y el Front no recalcula nada |
| II · Privacidad por diseño y solo datos inventados | El nombre vive solo en `acceso`, sale solo en D10, ningún registro ni informe lo repite y git lleva solo nombres inventados, con una prueba de repositorio sobre las semillas y `git ls-files` |
| III · Toda carga es atómica y trazable | La programación con nombre corre en la misma transacción de la spec 006, con corrida en seco y ROLLBACK, y un archivo inválido se rechaza antes de conectarse |
| IV · Las reglas son datos versionados y lo provisional se ve | D-12 sigue abierta y su valor provisional vive en una función aislada que se revierte sin tocar la cabecera |
| V · Contrato, historias auditadas y prueba antes de desplegar | 19 candidatas auditadas, reglas y contrato antes del código y pruebas primero |
| VI · Capas y privilegio mínimo | `abet_app` solo lee la columna con el SELECT que ya tiene, los roles de lectura no la alcanzan y `abet_respaldo` la lee y entra al tratamiento de la Ley 29733 |

## Project Structure

```text
ABET-ULIMA-Back/
  db/migration/V1_16__nombre_del_usuario.sql         columna, restricción y comentarios (propuesta)
  db/pruebas/pruebas.sql                             Q15 con el filtro ampliado
  db/pruebas/probar_rol_app.sql                      lee nombre y recibe 42501 al escribir
  db/plataforma/neon/profesores_sin_nombre.sql       consulta informativa (propuesta)
  db/herramientas/cargar_programacion.py y .sql      columna opcional nombre
  db/datos/*_inventado.sql                           nombres inventados de las semillas
  abet_carga/r17.py                                  profesores de la sección y D10
  tests/aceptacion/pasos/                            pasos de los cuatro .feature de la spec 010
  tests/test_cargar_programacion.py, tests/test_r17.py y la prueba de repositorio de las semillas
  specs/010-nombre-del-profesor/                     spec, revisión, plan, tareas y .feature
ABET-ULIMA-Front/
  docs/03-api/contrato.md                            línea fechada, sin ruta nueva
  e2e/humo_quimica.spec.ts                           lectura de D10 del R-17 descargado
```

## Phases

0. **Descubrimiento.** Candidatas, auditoría con tres lentes y el crítico, spec y cuatro `.feature`, y aprobación de Jefferson del 2026-11-24 con D10 separada por comas.
1. **Contrato.** BR-ACCESO-15 y BR-R17-14 con los cambios fechados de BR-ACCESO-01, BR-ACCESO-11 y BR-R17-07, la línea fechada del contrato del Front, el cambio fechado de la spec 006 y de D-12 de la spec 001 y los pasos compartidos de los Antecedentes.
2. **Base.** V1_16, Q15, los permisos de la columna, la consulta informativa y las semillas con nombres inventados, con pytest-bdd y `correr_pruebas.sh` primero.
3. **Back.** La columna `nombre` en `cargar_programacion.py` y su SQL, y los profesores de la sección en D10 con su cabida, con pytest-bdd primero. Empieza después de fusionar `fix/r17-recuadros-y-filas-de-pi`, porque toca `abet_carga/r17.py`, `tests/test_r17.py` y la spec viva `r17`.
4. **Front.** Solo la prueba de humo de D10. La API no cambia, pero el R-17 descargado se revisa.
5. **Pruebas y humo.** Suites del Back y del Front, `bash db/pruebas/correr_pruebas.sh`, `preflight.sh` y la matriz de cumplimiento, y el humo con Playwright contra la vista previa de develop.
6. **Auditoría.** `audit.md`, las líneas Verification fechadas de las specs vivas `acceso` y `r17`, `MEMORIA.md` y `CHANGELOG.md`.
7. **Despliegue.** V1_16 primero en develop de Neon, con respaldo previo y desde el Windows de Jefferson, y después el código por la fusión en `develop`. La rama principal de Neon y la carga de los nombres reales esperan el permiso de Jefferson (J-71).

## Estimación y fecha

La estimación por tarea está en `tasks.md` y suma unas 30 horas, de las cuales unas 17 son de construcción de las cinco historias (US-95 con 3 h, US-96 con 5 h, US-97 con 4 h, US-98 con 2 h y US-99 con 3 h) y el resto es contrato, cierre y despliegue. Con unas 9 horas diarias la construcción cubre tres días, y empieza solo cuando `fix/r17-recuadros-y-filas-de-pi` está fusionada en `develop`. La carga de los nombres reales no tiene fecha propia, porque depende de que la coordinación de cada carrera entregue la hoja con la columna de nombres (D-58).

## Riesgos

- Si V1_16 no está en la rama de Neon, un archivo de programación con la columna `nombre` falla en la base. El orden es V1_16 primero y la carga de nombres después, y la prueba de humo de develop lo confirma antes de tocar la rama principal.
- Todos los usuarios actuales de Neon tienen el nombre nulo, así que D10 sigue vacía hasta cargar los nombres. La consulta informativa cuenta las secciones publicadas con un profesor sin nombre y debe dar 0 antes de entregar los R-17 del periodo (SC-004).
- Si la Coordinación de Ambiental o la Oficina de Calidad deciden en D-12 que el R-17 no lleva el nombre, la función aislada de D10 se revierte sin tocar el resto de la cabecera ni la base.
- Si J-67 cambia al corte temporal de la alternativa del crítico, D10 queda vacía cuando la programación se carga después de publicar, y cambian la consulta y sus escenarios, no la migración.
- El respaldo diario con `abet_respaldo` copia el nombre al Windows y a Google Drive cifrado, así que ese respaldo entra al tratamiento de datos personales y `db/README.md` lo declara.
- Un nombre con una coma de la carrera, como «Apellido, Nombre», lo rechaza la base y el guion. La hoja de la carrera se normaliza antes de cargarla, sin que el guion adivine el orden.
