# ABET Backend Specs

Esta carpeta es la fuente de verdad del comportamiento de ABET-ULIMA-Back y sigue el mismo flujo de desarrollo guiado por especificaciones (Spec Driven Development) de IQBF-ULIMA_Back, donde cada spec es una especificación escrita antes del código. Una épica abre una carpeta numerada (`specs/NNN-slug/`) con sus historias auditadas, su `spec.md`, su `plan.md`, su `tasks.md` y, al cerrar, su `audit.md`. El comportamiento estable de cada módulo vive en una spec viva (`specs/features/<feature>/<feature>.spec.md`) con reglas numeradas, que cada iniciativa amplía y que recibe una línea `Verification` fechada cuando sus pruebas pasan. El orden no cambia con la prisa. Primero se auditan las historias, después se aprueba la spec por PR a `develop`, luego se escriben las reglas y el contrato de la API, y solo entonces se escribe código con sus pruebas primero. La constitución del proyecto está en `.specify/memory/constitution.md` y prevalece sobre todo lo que dice esta carpeta.

## Contexto actual

- Estado al 2026-10-28. No hay código de producto. La spec `001-mvp-carga-r17` está en revisión en la rama `docs/plan-mvp`, y nada se implementa hasta la fusión (merge) de su PR en `develop`.
- Solo datos inventados (códigos de estudiante de 99000000 a 99999999) en este repositorio, en Neon y en Vercel, hasta que la universidad autorice los reales (D-10). Ningún nombre de estudiante se guarda ni se muestra, y ningún rechazo guarda el valor leído de una celda.
- La base vive todavía en el repositorio privado `jeffangeloss/ABET_ULIMA` (carpeta local `bd/`). Pasa a `db/` de este repositorio con su historia después del primer `flyway migrate` en Neon y antes de escribir `V1_09__crear_acceso.sql`.
- Ninguna tabla, columna, restricción ni rol nace sin una spec aprobada. Todo cambio de la base entra como migración nueva en `db/migration/` o como script de plataforma en `db/plataforma/neon/`, y nunca edita una migración aplicada.
- El proyecto de Neon (PostgreSQL 16, aws-sa-east-1) todavía no existe y lo crea Jefferson. Las pruebas de aceptación corren siempre contra un PostgreSQL 16 desechable. En Neon solo se comprueban los criterios de despliegue que no escriben cargas, que son la migración y los controles de US-01 en `base_neon.feature` y la región, la reescritura, la cookie, el pooler y la guardia de `despliegue.feature`, y además corre la prueba de humo contra Preview (J-09).
- El backend en Python 3.12 con FastAPI es la opción recomendada y espera la confirmación de Jefferson (J-01). Las decisiones abiertas de la carrera (D-01 a D-13) se aplican con valores provisionales y configurables que las specs nombran con su identificador.
- El Front (ABET-ULIMA-Front) no habla con la base y consume solo el contrato de `docs/specs/api-contracts.md`.

## Convenciones

- Una carpeta numerada por épica, `NNN-slug-en-minusculas` (`001-mvp-carga-r17`), con nombres fijos y sin prefijo (`revision-historias.md`, `spec.md`, `plan.md`, `tasks.md` y `audit.md`).
- Una carpeta por feature (funcionalidad) en `specs/features/`; los archivos terminan en `.spec.md` y la carpeta lleva el mismo nombre que el archivo.
- Frontmatter YAML con `name`, `description` y `targets`, que apunta a archivos reales o globs del backend con rutas relativas desde la carpeta de la feature (`../../../abet_carga/carga.py`).
- Reglas de negocio numeradas `BR-<FEATURE>-NN`, con un título de una frase nominal, viñetas con rutas HTTP, códigos de respuesta, mensajes literales entre «» y el nombre de la restricción de la base que la respalda.
- La forma de error es siempre `{ "detail": "mensaje" }`. Los códigos del MVP son `200`, `201`, `202` y `204` en las respuestas correctas y `401`, `403`, `409`, `422`, `429` y `500` en los errores. El `403` es único para las rutas de sección y de carga, con «La sección no está a su cargo.».
- Un solo prefijo de historia final en todo el repositorio, `US-NN`. Las candidatas de la auditoría se nombran `C-NN` (con letra cuando se parten, como `C-12a`) y nunca usan `US-NN`. Las specs vivas citan las historias de la carpeta numerada que las originan y no abren otra numeración.
- Las historias se auditan antes de la spec. Tres lentes intentan refutarlas (necesidad, tamaño y verificabilidad) y una crítica ataca las decisiones técnicas, con el resultado en `revision-historias.md`.
- Los escenarios de aceptación van en Gherkin en español (`# language: es`, con Característica, Antecedentes, Escenario, Esquema del escenario y Ejemplos) en un solo lugar, la carpeta `aceptacion/` de la carpeta numerada (`specs/001-mvp-carga-r17/aceptacion/*.feature`). Los pasos viven en `tests/aceptacion/pasos/` y leen los `.feature` desde esa carpeta con `scenarios()` de pytest-bdd y la ruta relativa, y nadie los copia ni los mueve a `tests/`. Cada escenario lleva `@US-NN` y `@corte1` o `@corte2`, y la spec lista por historia sus escenarios y el archivo `.feature` donde viven.
- Las secciones `Verification` de una spec viva llevan fecha ISO y el archivo de prueba, y la más reciente va primero.
- Una decisión pendiente se marca con su identificador (`D-NN` para la carrera, `J-NN` para Jefferson) o con «(propuesta)» si la propone el redactor.
- El contrato de la API se actualiza en `docs/specs/api-contracts.md` antes de implementar cada ruta.

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
      aceptacion/                   base_neon, acceso, carga, r17_constancia, despliegue y reemplazo_y_cargas (.feature)
    features/<feature>/<feature>.spec.md
  docs/
    devops.md
    specs/api-contracts.md          contrato de la API
```

## Features

La épica EP-01 vive en `001-mvp-carga-r17/` (spec, plan y tasks en revisión). Las specs vivas que su fase 1 de contrato debe crear son estas.

| Feature | Estado |
| --- | --- |
| `carga-export` | por escribir en la fase 1 (`BR-CARGA-NN`, propuesta; US-07 a US-14, US-18, US-19 y US-21; `abet_carga/lector.py`, `validacion.py`, `carga.py` y `app/rutas/cargas.py`) |
| `r17` | por escribir en la fase 1 (`BR-R17-NN`, propuesta; US-15 y US-16; `abet_carga/r17.py`, `constancia.py`, `plantillas/R017_ambiental_general.xlsx` y `db/migration/R__vista_r17_por_pi.sql`) |
| `acceso` | por escribir en la fase 1 (`BR-ACCESO-NN`, propuesta; US-04, US-05, US-06 y US-20; `app/sesion.py`, `app/permisos.py` y `db/migration/V1_09__crear_acceso.sql`) |
| `periodo` | por escribir en la fase 1 (`BR-PERIODO-NN`, propuesta; US-03 y el listado de US-06; `app/rutas/secciones.py` y `db/datos/periodo_2026_2_inventado.sql`) |

US-01, US-02 y US-17 son de plataforma (migración en Neon, rol `abet_app` y despliegue en Vercel), no abren una spec viva y se verifican en `001-mvp-carga-r17/audit.md`.
