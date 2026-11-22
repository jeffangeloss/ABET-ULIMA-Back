# Tasks: Programación docente del ciclo, cargada desde el archivo de la carrera

**Input**: spec.md, plan.md · **Estado al 2026-11-21**: spec aprobada por Jefferson en el chat el 2026-11-21 («Sí, apruébalas», T004). Nada está construido

Cada tarea lleva al comienzo el repositorio o el lugar donde ocurre, como en las specs 001, 003, 004 y 005. `[Back]` es ABET-ULIMA-Back, `[Neon]` es la base en la nube, siempre desde el Windows de Jefferson por Tailscale, `[Carrera]` es la Coordinación de Ambiental y `[Jefferson]` marca lo que solo puede hacer él. Ninguna credencial ni ningún archivo real pasan por un agente. Al final, cada tarea lleva las historias que habilita o audita. La estimación de cada fase llega con la aprobación, así que esta lista no promete ninguna fecha, salvo el límite de la capacitación de la semana 14.

## Phase 0: Descubrimiento

- [x] T001 [Back] Revisar las tablas `abet.seccion`, `acceso.usuario_autorizado` y `acceso.docente_seccion` con sus restricciones, `_ALCANCE` de `app/permisos.py`, `db/datos/`, `crear_rol_app.sql` y `asignar_claves.py`, sin abrir ninguna base [US-55..US-58]
- [x] T002 [Back] Auditar C-C01 con las lentes de necesidad, tamaño y verificabilidad y con el crítico de arquitectura, dentro de la auditoría del cambio del 2026-11-21 de la spec 005, y dejar el resultado en `specs/006-programacion-docente/revision-historias.md` [US-55..US-58]
- [x] T003 [Back] Redactar `spec.md`, `plan.md`, `tasks.md` y los dos `.feature` de `specs/006-programacion-docente/`, que el analizador de pytest-bdd lee con 19 escenarios y 29 casos [US-55..US-58] · 2026-11-21
- [x] T004 [Jefferson] Aprobar la spec, con la fusión del PR de `docs/005-om-bp-y-006` o con su «apruebo» en el chat, y decidir J-42 [US-55..US-58] · Hecha el 2026-11-21 («Sí, apruébalas»)
- [ ] T005 [Carrera] Pedir hoy a la Coordinación de Ambiental el formato, el dueño y la fecha del archivo de la programación docente (D-44), y si la cuenta del profesor la crea el guion (D-45). Si el archivo no llega antes de la semana 14, acordar que la Coordinación llene el CSV mínimo de FR-002 [US-55]
- [ ] T006 [Back] Pasar AD-01 a AD-05 por el crítico de arquitectura antes de construir, y ajustar la spec con lo que no se sostenga [US-55..US-58]

## Phase 1: Contrato

- [ ] T010 [Back] Escribir BR-ACCESO-11 «Programación docente desde el archivo de la carrera» en `specs/features/acceso/acceso.spec.md`, con `db/herramientas/cargar_programacion.py` en sus `targets`, y actualizar la fila `acceso` de `specs/README.md` [US-55..US-57]
- [ ] T011 [Back] Dejar definitivos los dos `.feature` con el analizador de pytest-bdd y ajustarlos al formato real si D-44 llega antes de construir [US-55..US-58]
- [ ] T012 [Back] Escribir en `db/README.md` el uso del guion y de la consulta, con el orden de FR-015 y el comando de `en_windows.py` sin ningún valor secreto [US-55] [US-58]

## Phase 2: Base

- [ ] T020 [Back] Sin migración. Escribir primero `tests/aceptacion/pasos/test_secciones_sin_docente_feature.py` y después `db/plataforma/neon/secciones_sin_docente.sql`, con la sesión en solo lectura y el periodo obligatorio [US-58]
- [ ] T021 [Back] Sumar a `tests/cargas_de_prueba.py` el ayudante de la base de partida, con la vigencia de AMB-2026 en 2026-2 y los planes de 450002 y 450010, sin secciones ni profesores, con su prueba, y el paso «una base desechable de partida de la spec 006, …» que lo llama sin chocar con la expresión de migraciones de `tests/aceptacion/pasos/conftest.py:766` (FR-012) [US-55..US-58]

## Phase 3: Guion

- [ ] T030 [Back] Escribir primero `tests/test_cargar_programacion.py` y después la lectura y la forma de `db/herramientas/cargar_programacion.py`, con la BOM, la normalización del correo, todas las filas inválidas en un solo informe, los argumentos y el archivo dentro del repositorio (códigos 1 y 2) [US-55] [US-57]
- [ ] T031 [Back] Escribir primero `tests/aceptacion/pasos/test_programacion_docente_feature.py` y después `db/herramientas/cargar_programacion.sql`, con la tabla temporal, las revisiones contra la base, los INSERT con `ON CONFLICT DO NOTHING`, los avisos y el cierre con COMMIT o ROLLBACK [US-55..US-57]
- [ ] T032 [Back] Prueba de la falla de la base con un disparador creado solo en la base desechable del escenario, con código 3 y ninguna fila nueva [US-57]
- [ ] T033 [Back] Sumar `programacion_*.csv` a `.gitignore` y comprobar con `git check-ignore` que un archivo con ese nombre queda fuera [US-57]
- [ ] T034 [Back] Medir la corrida en seco con un archivo inventado de 300 filas en el clúster desechable, en menos de 10 s (SC-005) [US-55]

## Phase 4: Pruebas

- [ ] T040 [Back] Suite completa con `uv run --frozen --no-build pytest -q`, `bash scripts/preflight.sh` y `bash db/pruebas/correr_pruebas.sh` con Q01 a Q15 en 0 [US-55..US-58]

## Phase 5: Auditoría

- [ ] T050 [Back] `specs/006-programacion-docente/audit.md` con el cruce de historia, escenario, prueba y resultado, la línea Verification fechada en `acceso`, y `MEMORIA.md` y `CHANGELOG.md` [US-55..US-58]

## Phase 6: Corrida real

- [ ] T060 [Jefferson] Autorizar empujar la rama `feat/006-programacion-docente` y fusionar su PR con la integración continua en verde [US-55..US-58]
- [ ] T061 [Neon] Respaldar la rama principal con `db/herramientas/respaldar_neon.sh` antes de la primera escritura [US-55]
- [ ] T062 [Jefferson] Copiar el archivo real al Windows con `scp`, a una carpeta fuera de todo repositorio, sin que pase por un agente [US-55]
- [ ] T063 [Neon] Antes de la primera corrida, actualizar en el Windows la copia del Back al commit fusionado de `develop` y comprobar que trae `db/herramientas/cargar_programacion.py` y su SQL. Después, correr el guion en seco en la rama principal desde el Windows con `en_windows.py`, con el dueño de la base, y entregar el informe a Jefferson [US-55..US-57]
- [ ] T064 [Jefferson] Leer el informe y autorizar la corrida con `--aplicar`, que corre igual que T063 [US-55]
- [ ] T065 [Neon] Correr `secciones_sin_docente.sql` con `abet_respaldo` y llevar a la Coordinación cada sección que devuelva [US-58]
- [ ] T066 [Jefferson] Asignar las contraseñas de los usuarios nuevos con `asignar_claves.py`, o activar el código por correo si el corte 2 está listo (D-45), y borrar del Windows el archivo real [US-55]
