# Implementation Plan: Del export de Blackboard al R-17 desde la base

**Branch**: `docs/plan-mvp` (PR a `develop`) | **Date**: 2026-10-28 | **Spec**: [spec.md](./spec.md)

## Summary

Hoy el profesor sube su export de Blackboard a un cuaderno de Colab que vacía las celdas inválidas sin dejar rastro, adivina la sección por el nombre de la hoja y no guarda nada, así que ningún R-17 tiene evidencia del archivo del que sale ni una base que lo respalde. El producto mínimo viable (minimum viable product, MVP) de la épica EP-01 cumple los cuatro resultados que pide Jefferson, en este orden. Primero pone la base en la nube (Neon), después recibe el export de una sección, luego guarda sus datos en la base en una sola transacción y al final genera el R-17 desde la base con la constancia de la carga. El caso de prueba es la sección 410 de 450002 en 2026-2 con códigos inventados de 99000001 a 99000011. Su export correcto da 63,6 %, 63,6 % y 72,7 % en los indicadores de desempeño (performance indicators, PI) 5.1, 5.2 y 5.3, y el export con un 5 en la fila 3 da 11 filas leídas, 10 aceptadas, 1 rechazada y 60,0 %, 60,0 % y 70,0 %. El corte 1 entrega US-01 a US-17 y el corte 2 completa el MVP con US-18 a US-21 antes del primer profesor externo.

## Technical Context

- **Backend.** Python 3.12 con FastAPI (J-01, recomendado) para la interfaz de programación de aplicaciones (application programming interface, API), con prefijo `/api` y error `{ "detail": "mensaje" }`. La biblioteca `abet_carga` usa openpyxl 3.1.5 con defusedxml 0.7.1 y Pillow para leer y escribir, sin pandas, y psycopg 3 con transacciones explícitas y `prepare_threshold=None`. La API no pasa de 1 MB por archivo, muy por debajo del tope de 4,5 MB por petición de Vercel.
- **Frontend.** React con Vite, TypeScript y Tailwind, cuatro pantallas en el corte 1 (P1 Ingreso, P2 Mis secciones, P3 Subir export y P4 Resultado de la carga) y P5 Cargas en el corte 2. `src/servicios/api.ts` es la única puerta HTTP, y `vercel.json` reescribe `/api/:path*` hacia el Back para que la cookie sea del mismo origen.
- **Base.** Neon con PostgreSQL 16 en aws-sa-east-1, esquema `abet` (V1_01 a V1_08 y las dos vistas `R__`, sin cambios) y esquema nuevo `acceso` en `V1_09__crear_acceso.sql`, que agrega también `abet.carga.subida_por` y los motivos `COLUMNA_CODIGO_AUSENTE`, `PI_REPETIDO`, `PERIODO_NO_COINCIDE` y `SECCION_SIN_DECLARAR` a `ck_rechazo_fila_motivo`. Flyway migra Neon por la conexión directa, y la integración continua (continuous integration, CI) aplica las migraciones con psql, como `correr_pruebas.sh`, sin acciones ni imágenes de Redgate.
- **Acceso.** Contraseña asignada por el administrador técnico en el corte 1 (J-03, recomendado), con hash Argon2id en `acceso.credencial`, sesión en la cookie `abet_sesion` (HttpOnly, Secure, SameSite=Lax, 12 horas) y rol leído de la base en cada petición. El código de acceso por correo (US-20) llega en el corte 2, con Resend en el piloto y un dominio propio (J-04).
- **Pruebas.** pytest para las pruebas unitarias y los criterios escritos, pytest-bdd 9 con Gherkin en español para la carga y el R-17 (behave con `lang = es` si la prueba del primer día falla), las pruebas de la base de `db/pruebas/` (38 casos de rechazo, 3 aceptaciones y Q01 a Q14) y una prueba de humo (recorrido mínimo de punta a punta que confirma que el sistema desplegado responde) con Playwright para Node. Los siete `.feature` viven solo en `specs/001-mvp-carga-r17/aceptacion/`, y los pasos de `tests/aceptacion/pasos/` los leen desde esa carpeta con `scenarios()` y la ruta relativa, sin copiarlos ni moverlos. Las pruebas de aceptación corren siempre contra un PostgreSQL 16 desechable, y en Neon solo se comprueban los criterios de despliegue que no escriben cargas, que son la migración y los controles de US-01 en la fase 2 y la región, la reescritura, la cookie, el pooler y la guardia de `despliegue.feature` en la fase 7. La prueba de humo de la fase 7 corre contra la vista previa de `develop` con su rama de Neon (J-09).
- **Despliegue.** Dos proyectos de Vercel Hobby (`abet-ulima-back` y `abet-ulima-front`) en el equipo `jeffangeloss-projects`, región `gru1` fijada en `vercel.json` porque Vercel arranca en `iad1`, entrenamiento de inteligencia artificial (IA) desactivado, Production desde `main` y Preview desde `develop` con otra rama de Neon. Jefferson pega las variables del Back (`DATABASE_URL` con pooler y usuario `abet_app`, `SESION_SECRETO`, `PERIODO_VIGENTE`, `CONJUNTO_REGLAS` y `GUARDIA_DATOS_INVENTADOS=1`).
- **Restricciones.** Solo datos inventados, solo la hoja «Cursos de Carrera» del R-17, porque 450002 es un curso de carrera y la base no guarda el tipo de curso, y una tabla de estudiantes de 142 filas como máximo (47 estudiantes con 3 PI) que el generador respeta con un mensaje claro.
- **Decisiones abiertas.** Las de Jefferson (J-01 a J-10) y las de la carrera (D-01 a D-13) están listadas en la spec con quién decide cada una, y el plan aplica sus valores provisionales sin cerrarlas.

## Constitution Check

| Principio | Cumplimiento |
| --- | --- |
| I · La base es la única fuente de verdad | El R-17 sale de `v_r17_por_pi` y de la carga publicada (fase 3), el Front no habla con la base y las migraciones aplicadas no se editan, porque todo cambio entra en V1_09 |
| II · Privacidad por diseño y solo datos inventados | Guardia doble en `abet_carga/validacion.py` y en `ck_estudiante_codigo_inventado` (fases 2 y 3), descarte de nombres y valores leídos en el lector, esquema `acceso` aparte y secretos pegados solo por Jefferson (fase 7) |
| III · Toda carga es atómica y trazable | `cargar()` escribe las siete tablas en una transacción, guarda la huella SHA-256 y `carga.subida_por`, y la constancia muestra filas, avisos y rechazos por motivo y fila (fase 3) |
| IV · Las reglas son datos versionados y lo provisional se ve | El programa lee `R-2026-BORRADOR` de la base, el R-17 lleva la franja PROVISIONAL y `abet_app` no escribe en reglas, catálogo, plan ni secciones (fases 2 y 3) |
| V · Contrato, historias auditadas y prueba antes de desplegar | Historias auditadas en la fase 0, specs vivas, contrato y `.feature` en la fase 1, pruebas en la fase 5 y `audit.md` en la fase 6, todo antes de la fase 7, con `MEMORIA.md` en cada commit |
| VI · Capas y privilegio mínimo | `abet_carga` sin FastAPI, `app/permisos.py` como dueño de la visibilidad, rol `abet_app` sin DELETE ni TRUNCATE y dos proyectos de Vercel con reescritura de rutas al mismo origen |

## Project Structure

```text
ABET-ULIMA-Back/
  .specify/memory/constitution.md
  db/                                      # traslado de bd/ con git subtree (fase 2)
    flyway.toml                            # schemas = ["abet", "acceso"] en dev y neon
    migration/V1_09__crear_acceso.sql      # (nuevo) esquema acceso, carga.subida_por y cuatro motivos
    plataforma/neon/crear_rol_app.sql      # (nuevo) rol abet_app con privilegio mínimo
    plataforma/neon/guardia_datos_inventados.sql  # (nuevo) ck_estudiante_codigo_inventado, solo en Neon
    plataforma/neon/controles_neon.sql     # (nuevo) Q01 a Q14 en solo lectura
    datos/periodo_2026_2_inventado.sql     # (nuevo) vigencia, secciones 410 y 411, plan y usuarios de prueba
    datos/varias_secciones_2026_2_inventado.sql   # (nuevo) profesor con tres secciones de 450002 y 450010, solo en las pruebas
    pruebas/pruebas.sql                    # + casos de V1_09 y caso 60,0 / 60,0 / 70,0
  abet_carga/                              # (nuevo) lector, validacion, carga, r17 y constancia
  app/                                     # (nuevo) main, sesion, permisos y rutas/
    rutas/sesion.py                        # + POST, GET y DELETE /api/sesion
    rutas/secciones.py                     # + GET /api/secciones?periodo=2026-2
    rutas/cargas.py                        # + POST /api/secciones/{seccion_id}/cargas, GET /api/cargas/{carga_id} y su r17.xlsx
  plantillas/R017_ambiental_general.xlsx   # (nuevo) copia vaciada y limpia de la plantilla de Ambiental
  tests/unit/                              # (nuevo) pytest
  tests/aceptacion/pasos/                  # (nuevo) pasos de pytest-bdd que leen los .feature con scenarios()
  tests/datos_inventados/                  # (nuevo) exports con códigos 99
  specs/001-mvp-carga-r17/aceptacion/      # los siete .feature en español, único lugar donde viven
  specs/features/{carga-export,r17,acceso,periodo}/   # (nuevo) specs vivas
  pyproject.toml, requirements.txt, .env.example, vercel.json   # (nuevo, propuesta)

ABET-ULIMA-Front/
  docs/03-api/contrato.md                  # contrato de la API, con su índice docs/specs/api-contracts.md
  src/servicios/api.ts                     # (nuevo) única puerta HTTP, cookie y nunca localStorage
  src/servicios/tipos.ts                   # (nuevo, propuesta) tipos del contrato
  src/pantallas/Ingreso.tsx                # (nuevo, propuesta) P1
  src/pantallas/MisSecciones.tsx           # (nuevo, propuesta) P2
  src/pantallas/SubirExport.tsx            # (nuevo, propuesta) P3 con el rótulo «Solo exports con códigos inventados (99000000 a 99999999)»
  src/pantallas/ResultadoCarga.tsx         # (nuevo, propuesta) P4 con constancia y descarga del R-17
  src/pantallas/Cargas.tsx                 # (nuevo, propuesta) P5, corte 2
  tests/                                   # (nuevo) Vitest y Testing Library
  vite.config.ts                           # (nuevo) proxy de /api hacia el Back local
  vercel.json                              # (nuevo) reescritura de /api/:path* hacia el Back
```

## Phases

Los días son de trabajo sin interrupciones, con Claude a cargo del código y Jefferson de la revisión. Las fases 3 y 4 se solapan, porque el Front trabaja contra el contrato de la fase 1.

0. **Descubrimiento** (hecho el 2026-10-28). En ABET-ULIMA-Back, lectura de la base, del export inventado y de la plantilla del R-17, 25 historias candidatas con Gherkin, tres auditorías y una crítica de arquitectura que dejan 21 historias. En ABET-ULIMA-Front y en Neon, nada. Artefactos `revision-historias.md`, `spec.md`, este plan, `tasks.md`, la constitución, `specs/README.md` y los seis `.feature` de `specs/001-mvp-carga-r17/aceptacion/`, en revisión por solicitud de integración (pull request, PR) a `develop`. No cierra ninguna historia y prepara EP-01.
1. **Contrato** (1 día). En el Back, las specs vivas `carga-export`, `r17`, `acceso` y `periodo` con sus reglas `BR-`, la versión definitiva de los siete `.feature` de `specs/001-mvp-carga-r17/aceptacion/`, la prueba de 30 minutos de pytest-bdd 9 en español sobre `carga.feature` y los exports inventados de `tests/datos_inventados/`. En el Front, nada de código y el contrato de la API en `docs/03-api/contrato.md`, con su índice `docs/specs/api-contracts.md` y los siete endpoints del corte 1. En Neon, nada, y Jefferson compra el dominio para que su registro se propague antes del corte 2. Artefacto, el contrato aprobado. No cierra historias y habilita US-03 a US-16.
2. **Base** (1 a 1,5 días). En Neon, Jefferson crea el proyecto en aws-sa-east-1 con la rama `develop`, y `flyway migrate` aplica V1_01 a V1_08 con `controles_neon.sql` en cero. En el Back, el traslado de `bd/` a `db/`, `V1_09__crear_acceso.sql`, `crear_rol_app.sql`, `guardia_datos_inventados.sql`, `periodo_2026_2_inventado.sql` y la CI con las pruebas de la base. Después se aplican en Neon, primero en `develop` y luego en la rama principal. En el Front, nada. Artefacto, Neon migrado con los datos inventados de 2026-2. Cierra US-01, US-02, US-03 y US-04.
3. **Backend** (3 a 4 días). En el Back, `abet_carga` (lector, validación, carga, R-17 y constancia), la plantilla vaciada y la API de sesión, secciones y cargas. En el Front y en Neon, nada. Artefacto, la API local que carga el export con error en `abet_sis_med_dev` con 11 / 10 / 1 y descarga su R-17 con 60,0 %, 60,0 % y 70,0 %. Cierra en la API US-05 a US-16.
4. **Frontend** (1,5 a 2 días). En el Front, P1 a P4 contra el contrato, con el proxy de Vite hacia el Back local. En el Back y en Neon, nada. Artefacto, el flujo del profesor completo en la Mac. Cierra en pantalla US-05, US-06, US-07 y US-09 a US-16, y deja US-08 con su rótulo en P3.
5. **Pruebas** (1 día). En el Back, los pasos de `tests/aceptacion/pasos/` para `carga.feature` y `r17_constancia.feature`, pytest para los criterios escritos de `base_neon.feature` y `acceso.feature` contra un PostgreSQL 16 desechable, salvo los de migración y controles de US-01, que se comprueban en Neon en la fase 2, los casos negativos y la prueba de humo con Playwright para Node contra el Back y el Front locales. Los escenarios de `varias_secciones.feature` siguen ese reparto, los de US-07, US-09 y US-13 con los pasos de pytest-bdd de `carga.feature` (T050) y los de US-06 con los criterios escritos de `acceso.feature` (T051). En el Front, Vitest y Testing Library para P3 y P4. En Neon, nada. Artefacto, la verificación `pruebas` aprobada en los dos repositorios. Cierra la aceptación de US-01 a US-16.
6. **Auditoría** (0,5 días). En el Back, `audit.md` cruza historia, escenario, prueba y resultado, y las cuatro specs vivas reciben su `Verification` fechada. En el Front, su documentación de pantallas y contrato. En Neon, nada. Artefacto, `audit.md`. No cierra historias y certifica las de las fases 2 a 5.
7. **Despliegue** (0,5 a 1 día). Jefferson crea los dos proyectos de Vercel y pega las variables, el Back y el Front fijan `gru1` y la reescritura de rutas en su `vercel.json`, la prueba de humo con datos inventados corre contra la vista previa de `develop` y su rama de Neon (valor provisional de J-09), y después la versión 0.1.0 pasa de `develop` a `main` en los dos repositorios, el Back primero. La prueba de humo no corre en Production, y los demás criterios escritos de `despliegue.feature` se comprueban con la configuración de los dos proyectos. En Neon, `controles_neon.sql` en cero en las dos ramas. Artefacto, el piloto en línea y la sección «Despliegue» de `audit.md`. Cierra US-17.

## Cortes

| Corte | Historias | Fases | Duración | Resultado |
| --- | --- | --- | --- | --- |
| Primer corte demostrable | US-01, US-03, US-07, US-10, US-15 y US-16 | 2 y 3 reducidas, sin acceso ni pantallas | 2 a 3 días | El comando de `abet_carga` carga el export con error en la Mac y después en la rama `develop` de Neon, y produce el R-17 con 60,0 %, 60,0 % y 70,0 % y su constancia 11 / 10 / 1 |
| Corte 1 | US-01 a US-17 | 1 a 7 | unos 7 días hábiles | Piloto en Vercel con Neon, con los cuatro resultados del pedido y la prueba de humo de punta a punta contra la vista previa |
| Corte 2 | US-18 a US-21 | 1, 3, 4, 5, 6 y 7 de nuevo, más breves (tareas T080 a T099) | unos 3 a 4 días hábiles | Reemplazo de una carga publicada, lista de cargas, código de acceso por correo y confirmación de la sección, antes del primer profesor externo |

En total el MVP toma unas dos semanas hábiles. El correo del corte 2 depende además de la propagación del sistema de nombres de dominio (Domain Name System, DNS) y de la pasarela de correo de la universidad, que no se aceleran con más horas.

## Complexity Tracking

| Desviación | Por qué hace falta | Alternativa más simple descartada |
| --- | --- | --- |
| Esquema `acceso` aparte de `abet` | La consulta de control Q04 falla si `abet` tiene columnas con nombres o datos de contacto, y los usuarios tienen correo | Tablas de usuarios dentro de `abet`, que rompen Q04 y mezclan la medición con la identidad |
| Guardia en la base como script de plataforma y no como migración | La guardia vale solo mientras no haya autorización y solo en Neon, y se retira con un cambio explícito | Una migración con el CHECK, que también correría en la CI y en local y obligaría a otra migración para retirarlo |
| Dos proyectos de Vercel con reescritura de rutas al mismo origen | Un proyecto se enlaza a un repositorio, y dos subdominios de `vercel.app` son sitios distintos para la cookie SameSite=Lax | Un solo proyecto con API y Front, que contradice los dos repositorios, o el uso compartido de recursos entre orígenes (cross-origin resource sharing, CORS) con un token en `localStorage`, que la constitución prohíbe |
| Contraseña asignada en el corte 1 y código por correo en el corte 2 | El correo depende de un dominio, de su DNS y de la pasarela de la universidad, plazos que Jefferson no controla | El código por correo desde el primer día, que puede dejar el piloto sin nadie que entre |
| Gherkin ejecutable solo en la carga y el R-17 | Enlazar cada paso en español cuesta tiempo en cada historia, y la carga es donde cada «Entonces» se comprueba en la base | Gherkin ejecutable en las 21 historias, que alarga el corte 1 sin cubrir más riesgo |
| CI con psql en lugar de Flyway | La licencia de Redgate está en revisión, y `correr_pruebas.sh` ya aplica las migraciones con psql | La imagen de Flyway en la CI, que queda para cuando se aclare la licencia |
| `db/` aplanado tras el `git subtree` (propuesta) | `bd/` trae su propio `db/`, y copiarlo sin aplanar deja `db/db/migration` | Llevar `bd/` a la raíz del Back, que mezcla `pruebas/`, `herramientas/` y `referencia/` con el código de la API |
| Plantilla `.xlsx` versionada fuera de `tests/datos_inventados/` (propuesta) | El R-17 se llena desde `plantillas/R017_ambiental_general.xlsx`, y `scripts/preflight.sh` (regla 1) y `.gitignore` rechazan hoy todo `.xlsx` fuera de esa carpeta | Generar el libro desde cero con estilos en código, que conviene solo si la Oficina de Calidad aprueba un formato nuevo (D-08) |
| Export de la guardia generado en la prueba y no versionado (propuesta) | El caso del código 10000004 en la fila 4 trae un código que no empieza con 99, y `scripts/preflight.sh` (regla 2) lo rechazaría en `tests/datos_inventados/` | Versionar ese export con una excepción en la revisión previa, que abre un hueco en la regla de datos inventados |
