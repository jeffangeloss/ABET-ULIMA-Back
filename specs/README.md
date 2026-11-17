# ABET Backend Specs

Esta carpeta es la fuente de verdad del comportamiento de ABET-ULIMA-Back y sigue el mismo flujo de desarrollo guiado por especificaciones (Spec Driven Development) de IQBF-ULIMA_Back, donde cada spec es una especificación escrita antes del código. Una épica abre una carpeta numerada (`specs/NNN-slug/`) con sus historias auditadas, su `spec.md`, su `plan.md`, su `tasks.md` y, al cerrar, su `audit.md`. El comportamiento estable de cada módulo vive en una spec viva (`specs/features/<feature>/<feature>.spec.md`) con reglas numeradas, que cada iniciativa amplía y que recibe una línea `Verification` fechada cuando sus pruebas pasan. El orden no cambia con la prisa. Primero se auditan las historias, después se aprueba la spec por una solicitud de integración (pull request, PR) a `develop`, luego se escriben las reglas y el contrato de la interfaz de programación de aplicaciones (application programming interface, API), y solo entonces se escribe código con sus pruebas primero. La constitución del proyecto está en `.specify/memory/constitution.md` y prevalece sobre todo lo que dice esta carpeta.

## Contexto actual

- Estado al 2026-11-09. La spec `003-exports-blackboard` (EP-03, US-26 a US-36) amplía la carga a los tres formatos del export real de Blackboard, `.xlsx`, `.csv` y `.xls` de texto, y a los encabezados «ABET SO5.1 [», con la migración nueva V1_10. Jefferson la aprueba en el chat el mismo día, y su implementación avanza en la rama `feat/003-exports-blackboard` del Back y del Front.
- Estado al 2026-10-28. `develop` no tiene código de producto. Jefferson aprueba la spec `001-mvp-carga-r17` en el chat el mismo día, y `MEMORIA.md` registra la aprobación. La aprobación formal que pide el Principio V de la constitución es la fusión (merge) en `develop` del PR de la spec desde la rama `docs/plan-mvp` (T004), que espera el permiso de Jefferson. Mientras tanto, el corte 1 avanza en local en la rama `feat/001-mvp-carga-r17`.
- Solo datos inventados (códigos de estudiante de 99000000 a 99999999) en este repositorio, en Neon y en Vercel, hasta que la universidad autorice los reales (D-10). Ningún nombre de estudiante se guarda ni se muestra, y ningún rechazo guarda el valor leído de una celda.
- La base vive todavía en el repositorio privado `jeffangeloss/ABET_ULIMA` (carpeta local `bd/`). Pasa a `db/` de este repositorio con su historia, y Jefferson aprueba el 2026-10-28 adelantar ese traslado en local, antes del primer `flyway migrate` en Neon y de `V1_09__crear_acceso.sql` (J-06). Los commits de `preparacion-neon` entran después con `git subtree pull --prefix=db`, y `ABET_ULIMA` se archiva cuando termina T022.
- Ninguna tabla, columna, restricción ni rol nace sin una spec aprobada. Todo cambio de la base entra como migración nueva en `db/migration/` o como script de plataforma en `db/plataforma/neon/`, y nunca edita una migración aplicada.
- El proyecto de Neon es ABET-ULIMA (PostgreSQL 18, us-east-1, J-17), que Jefferson crea con la integración de Vercel y que ya tiene V1_01 a V1_08. Las pruebas de aceptación corren siempre contra un PostgreSQL 18 desechable. En Neon solo se comprueban los criterios de despliegue que no escriben cargas, que son la migración y los controles de la historia de usuario (user story, US) US-01 en `base_neon.feature` y la región, la reescritura, la cookie, el pooler y la guardia de `despliegue.feature`. Allí corre además la prueba de humo contra Preview (J-09).
- El backend es Python 3.12 con FastAPI, el valor de J-01 que Jefferson confirma con la aprobación del plan el 2026-10-28. Las decisiones abiertas de la carrera (D-01 a D-13) se aplican con valores provisionales y configurables que las specs nombran con su identificador.
- El Front (ABET-ULIMA-Front) no habla con la base y consume solo el contrato de la API, que vive en el propio Front, en `docs/03-api/contrato.md`, con su índice corto en `docs/specs/api-contracts.md`.

## Convenciones

- Una carpeta numerada por épica, `NNN-slug-en-minusculas` (`001-mvp-carga-r17`), con nombres fijos y sin prefijo (`revision-historias.md`, `spec.md`, `plan.md`, `tasks.md` y `audit.md`).
- Una carpeta por feature (funcionalidad) en `specs/features/`; los archivos terminan en `.spec.md` y la carpeta lleva el mismo nombre que el archivo.
- Frontmatter YAML con `name`, `description` y `targets`, que apunta a archivos reales o globs del backend con rutas relativas desde la carpeta de la feature (`../../../abet_carga/carga.py`).
- Reglas de negocio (business rules, BR) numeradas `BR-<FEATURE>-NN`, con un título de una frase nominal, viñetas con las rutas de la API, sus códigos de respuesta, mensajes literales entre «» y el nombre de la restricción de la base que la respalda.
- La forma de error es siempre `{ "detail": "mensaje" }`. Los códigos del producto mínimo viable (minimum viable product, MVP) son `200`, `201`, `202` y `204` en las respuestas correctas y `401`, `403`, `409`, `422`, `429` y `500` en los errores. El `403` es único para las rutas de sección y de carga, con «La sección no está a su cargo.».
- Un solo prefijo de historia final en todo el repositorio, `US-NN`. Las candidatas de la auditoría se nombran `C-NN` (con letra cuando se parten, como `C-12a`) y nunca usan `US-NN`. Las specs vivas citan las historias de la carpeta numerada que las originan y no abren otra numeración.
- Las historias se auditan antes de la spec. Tres lentes intentan refutarlas (necesidad, tamaño y verificabilidad) y una crítica ataca las decisiones técnicas, con el resultado en `revision-historias.md`.
- Los escenarios de aceptación van en Gherkin en español (`# language: es`, con Característica, Antecedentes, Escenario, Esquema del escenario y Ejemplos) en un solo lugar, la carpeta `aceptacion/` de la carpeta numerada (`specs/001-mvp-carga-r17/aceptacion/*.feature`). Los pasos viven en `tests/aceptacion/pasos/` y leen los `.feature` desde esa carpeta con `scenarios()` de pytest-bdd y la ruta relativa, y nadie los copia ni los mueve a `tests/`. Cada escenario lleva `@US-NN` y `@corte1` o `@corte2`, y la spec lista por historia sus escenarios y el archivo `.feature` donde viven.
- Las secciones `Verification` de una spec viva llevan la fecha en la forma AAAA-MM-DD y el archivo de prueba, y la más reciente va primero.
- Una decisión pendiente se marca con su identificador (`D-NN` para la carrera, `J-NN` para Jefferson) o con «(propuesta)» si la propone el redactor.
- El contrato de la API vive en ABET-ULIMA-Front, en `docs/03-api/contrato.md` con su índice `docs/specs/api-contracts.md`, y se actualiza antes de implementar cada ruta, en un PR del Front que cita el PR de la spec viva del Back que cambia la ruta.

## Arquitectura objetivo

```text
ABET-ULIMA-Back/
  .specify/memory/constitution.md   constitución (seis principios)
  db/                               base como código (traslado de bd/ con su historia)
    flyway.toml                     entornos dev y neon; schemas abet y acceso
    migration/                      V1_01 a V1_08, V1_09__crear_acceso.sql, R__vista_r17_por_pi, R__vista_tabla_maestra_pi
    callbacks/                      afterMigrate__permisos_lectura.sql
    plataforma/neon/                crear_roles_lectura.sql, crear_rol_app.sql, guardia_datos_inventados.sql, controles_neon.sql
    datos/                          periodo_2026_2_inventado.sql (vigencia, secciones 410 y 411, plan y usuarios de prueba)
                                    varias_secciones_2026_2_inventado.sql (profesor con tres secciones de 450002 y 450010, solo en las pruebas)
    pruebas/                        correr_pruebas.sh, pruebas.sql (Q01 a Q14), datos_sinteticos.sql
  abet_carga/                       biblioteca de carga, sin FastAPI
    lector.py                       revisión del zip y lectura con openpyxl en solo lectura, sin pandas
    validacion.py                   guardia, estructura, sección, periodo y filas
    carga.py                        cargar(bytes, seccion_id, ...) en una sola transacción
    r17.py                          R-17 desde v_r17_por_pi con valores calculados
    constancia.py                   constancia en JSON y hoja «Constancia»
  app/                              API FastAPI con prefijo /api
    main.py
    sesion.py                       cookie abet_sesion, Argon2id, límite de intentos
    permisos.py                     dueño único de la regla de visibilidad
    rutas/                          sesion, secciones y cargas
  plantillas/R017_ambiental_general.xlsx   copia vaciada de la hoja «Cursos de Carrera», sin #REF!
  tests/
    unit/
    aceptacion/pasos/               pasos de pytest-bdd que leen specs/001-mvp-carga-r17/aceptacion/*.feature
    datos_inventados/               exports inventados con códigos que empiezan con 99
  scripts/                          preflight.sh, probar_preflight.sh, hooks/
  specs/
    README.md
    001-mvp-carga-r17/              revision-historias, spec, plan, tasks y audit
    003-exports-blackboard/         export real en .xlsx, .csv y .xls, encabezados ABET SO y V1_10 (spec 003)
      aceptacion/                   base_neon, acceso, carga, r17_constancia, despliegue, reemplazo_y_cargas y varias_secciones (.feature)
    features/<feature>/<feature>.spec.md
  docs/
    devops.md
```

## Features

La épica EP-01 vive en `001-mvp-carga-r17/`, y su fase 1 de contrato ya escribe las cuatro specs vivas con sus reglas numeradas. Las cuatro siguen «en revisión» en la escala de `docs/specs/feature-index.md` del Front, porque esperan la auditoría de la fase (T019), la revisión de Jefferson en su PR y la fusión del PR de la spec 001 en `develop` (T004).

| Feature | Reglas | Historias | Archivos de `targets` | Estado |
| --- | --- | --- | --- | --- |
| `carga-export` | BR-CARGA-01 a BR-CARGA-20, con los bloques de la spec 003 en BR-CARGA-03, 05 a 08, 11 y 14 a 17 | US-07 a US-14, US-18, US-19, US-21 y US-26 a US-36 | `abet_carga/lector.py`, `validacion.py`, `carga.py` y `app/rutas/cargas.py` | en revisión |
| `r17` | BR-R17-01 a BR-R17-10 | US-15 y US-16 | `abet_carga/r17.py`, `constancia.py`, `app/rutas/cargas.py`, `plantillas/R017_ambiental_general.xlsx` y `db/migration/R__vista_r17_por_pi.sql` | en revisión |
| `acceso` | BR-ACCESO-01 a BR-ACCESO-09 | US-04, US-05, US-06 y US-20 | `app/sesion.py`, `app/permisos.py`, `app/rutas/sesion.py`, `scripts/asignar_clave.py` y `db/migration/V1_09__crear_acceso.sql` | en revisión |
| `periodo` | BR-PERIODO-01 a BR-PERIODO-04 | US-03 y el listado de US-06 | `app/main.py`, `app/rutas/secciones.py` y `db/datos/periodo_2026_2_inventado.sql` | en revisión |

US-01, US-02 y US-17 son de plataforma (migración en Neon, rol `abet_app` y despliegue en Vercel), no abren una spec viva y se verifican en `001-mvp-carga-r17/audit.md`.
