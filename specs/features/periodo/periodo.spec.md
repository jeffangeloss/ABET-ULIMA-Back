---
name: Periodo y secciones
description: Periodo vigente y conjunto de reglas de una carga nueva desde la configuración de la API, datos inventados del periodo 2026-2 y lista de secciones al alcance del usuario.
targets:
  - ../../../app/main.py
  - ../../../app/rutas/secciones.py
  - ../../../db/datos/periodo_2026_2_inventado.sql
---

# Periodo y secciones

> **Estado al 2026-10-30.** Reglas de la fase 1 de contrato (T014), escritas antes del código. Los archivos de `targets` nacen en las fases 2 y 3, y la sección Verification se llenó el 2026-10-30 con la corrida del corte 1 (T061); las reglas del corte 2 la reciben con T088.

Esta spec viva fija de dónde toma la interfaz de programación de aplicaciones (application programming interface, API) el periodo vigente y el conjunto de reglas de una carga nueva, qué datos del periodo 2026-2 siembra el script de datos y qué devuelve la lista de secciones. Cada regla de negocio (business rule, BR) nombra su fuente en `specs/001-mvp-carga-r17/spec.md`, sean historias de usuario (user stories, US), requisitos funcionales (functional requirements, FR) o decisiones abiertas (D). Cada regla nombra también la restricción o la consulta de control de la base que la respalda y el escenario que la prueba, citado por su título. Los textos entre «» son literales, y lo marcado «(propuesta)» no está fijado en las decisiones de la spec, como en los `.feature`, aunque algún escenario ya lo compruebe. Los ejemplos usan solo datos inventados.

## User Stories

| ID | Descripción | Corte |
| --- | --- | --- |
| US-03 | Preparar el periodo 2026-2 con datos inventados | 1 |
| US-06 | Ver solo las secciones propias del periodo (la lista de secciones) | 1 |

## Business Rules

### BR-PERIODO-01: Periodo vigente desde la configuración
- La base no marca un periodo como vigente, así que la API lo toma de la variable `PERIODO_VIGENTE`, que en el piloto vale `2026-2`.
- Al arrancar, la API comprueba que `abet.periodo` tenga ese `codigo` (`uq_periodo_codigo`). Si no lo tiene, el arranque se detiene con «PERIODO_VIGENTE 2027-1 no existe en abet.periodo» (propuesta), con el valor configurado, y `abet.carga` no gana filas.
- `GET /api/secciones` sin el parámetro `periodo` usa `PERIODO_VIGENTE`.
- **Fuente**: FR-007, US-03 (escenario 4), Principio I de la constitución y `uq_periodo_codigo`.
- **Prueba**: «La API no arranca con un periodo o un conjunto de reglas que la base no conoce» (`base_neon.feature`).

### BR-PERIODO-02: Conjunto de reglas de una carga nueva
- La base tampoco marca un conjunto de reglas como vigente, así que cada carga nueva toma el de la variable `CONJUNTO_REGLAS`, que en el piloto vale `R-2026-BORRADOR`, y lo guarda en `carga.conjunto_reglas_id`. La clave foránea `fk_carga_reglas` exige que el conjunto sea de la carrera de la carga.
- Al arrancar, la API comprueba que `abet.conjunto_reglas` tenga esa `version` para Ambiental (`uq_conjunto_reglas`). Si no la tiene, el arranque se detiene con «CONJUNTO_REGLAS R-NO-EXISTE no existe para Ambiental» (propuesta), con el valor configurado.
- `carga.conjunto_reglas_id` no se edita en una carga publicada, porque `abet_app` no tiene UPDATE sobre esa columna (US-02). Un cambio de reglas entra por una carga nueva que reemplaza a la anterior en el corte 2 (BR-CARGA-19).
- Los parámetros de la medición viven en `abet.conjunto_reglas` y `abet.parametro_valor`, nunca en constantes del código. R-2026-BORRADOR define META_LOGRO en 0,80 y NIVEL_ESPERADO en 3 y deja CORTE_ROJO, CONVERSION_NIVEL_0_1 y TRATO_SIN_EVIDENCIA en PENDIENTE (V1_06).
- **Fuente**: FR-007, US-03 (escenario 4), Principios I y IV de la constitución, `fk_carga_reglas`, `uq_conjunto_reglas` y V1_06.
- **Prueba**: «La API no arranca con un periodo o un conjunto de reglas que la base no conoce» y «abet_app solo actualiza el estado y los conteos de una carga» (`base_neon.feature`), «El export correcto queda publicado entero» (`carga.feature`) y «Con reglas aprobadas el R-17 sale sin franja» (`r17_constancia.feature`).

### BR-PERIODO-03: Datos del periodo por script y solo inventados
- La vigencia del catálogo, las secciones y el plan de medición son datos operativos de `db/datos/periodo_2026_2_inventado.sql` y nunca entran en una migración.
- El script registra AMB-2026 como catálogo vigente de Ambiental en 2026-2 (`pk_catalogo_vigencia`) y las secciones 410 y 411 de 450002 con `curso_blackboard` «SINTETICO_20262_450002_410» y «SINTETICO_20262_450002_411» (`uq_seccion` y `uq_seccion_curso_bb`).
- Registra también el plan con los indicadores de desempeño (performance indicators, PI) 5.1, 5.2 y 5.3 del resultado del estudiante (student outcome, SO) 5 (`uq_plan_medicion` y `fk_plan_medicion_vigencia`) y los usuarios de BR-ACCESO-01, y la consulta de control Q05 devuelve 0 filas.
- El script se puede repetir sin duplicar filas (propuesta, con `ON CONFLICT DO NOTHING`).
- Todo número de 8 dígitos del script empieza con 99 y todo correo termina en «@example.invalid». El número de sección no admite ceros a la izquierda, y `ck_seccion_numero` rechaza «0410».
- El plan de 2026-2 es el valor provisional de D-09, y `abet_app` no escribe en `seccion`, `plan_medicion`, `catalogo_*` ni en las reglas (US-02).
- **Fuente**: US-03, FR-006, D-09, Principio IV de la constitución, `ck_seccion_numero` y la consulta de control Q05.
- **Prueba** (`base_neon.feature`): «Sembrar la vigencia, las secciones 410 y 411 y el plan de 450002», «Repetir el script de datos no duplica filas», «El número de sección no admite ceros a la izquierda» y «El script de datos solo trae datos inventados».

### BR-PERIODO-04: Lista de secciones del periodo
- `GET /api/secciones?periodo=2026-2` devuelve las secciones del periodo al alcance del usuario (BR-ACCESO-07), cada una con `seccion_id`, la asignatura con su `codigo` y su `nombre`, `numero`, `periodo`, los PI de su plan (`pi`), `tiene_plan` y el estado de su carga.
- `estado` vale «PUBLICADA» cuando la sección tiene una carga en ese estado, con su `carga_id`, `filas_leidas` y `filas_aceptadas`, y «SIN_CARGA» en otro caso, con esos tres campos nulos (propuesta, el valor «SIN_CARGA»). Una sección cuyas cargas están todas RECHAZADA o REEMPLAZADA sale «SIN_CARGA» (propuesta). `uq_carga_publicada_por_seccion` garantiza una sola carga PUBLICADA por sección.
- `tiene_plan` es falso cuando `abet.plan_medicion` no tiene filas de esa asignatura y ese periodo. Entonces `pi` viene vacío, la pantalla P2 desactiva «Subir export» y la subida responde 422 (BR-CARGA-01).
- La respuesta del profesor no trae datos de secciones ajenas, y sin sesión la ruta responde 401 sin secciones (BR-ACCESO-06).
- Un `periodo` con otra forma que `AAAA-C`, la de `ck_periodo_codigo`, responde 422 (propuesta).
- Con la conexión por el pooler de Neon, su agrupador de conexiones, y psycopg 3 con `prepare_threshold=None`, 20 peticiones seguidas del coordinador responden 200 con la 410 y la 411 (US-17).
- **Fuente**: FR-011, US-06 (escenarios 1, 2, 3, 5 y 6), `uq_carga_publicada_por_seccion` y `ck_periodo_codigo`.
- **Prueba** (`acceso.feature`): «El profesor ve únicamente su sección», «El coordinador ve todas las secciones de la carrera», «El estado refleja la carga publicada», «Sin sesión no hay lista» y «Sección de una asignatura sin plan de medición»; en el piloto, «La API se conecta a Neon por el pooler con el rol abet_app» (`despliegue.feature`).

## Verification

Corrida del 2026-10-30 en el Back, rama `feat/001-mvp-carga-r17`, sobre un PostgreSQL 16 desechable que arma la propia suite. La más reciente va primero y cada línea lleva la fecha, el comando, el archivo de prueba y las reglas que cubre.

```text
- 2026-10-30 · uv run --frozen pytest -q tests/aceptacion -rA · test_acceso_feature.py, test_base_neon_feature.py, test_carga_feature.py, test_r17_constancia_feature.py → BR-PERIODO-01 a BR-PERIODO-04
- 2026-10-30 · uv run --frozen pytest -q tests -rA · test_api_cargas.py, test_api_secciones.py → BR-PERIODO-01, BR-PERIODO-04
```

Resultado: aceptación, 170 passed, 19 skipped in 116.97s (0:01:56); suite completa, 852 passed, 20 skipped in 241.50s (0:04:01). Las pantallas P1 a P4 tienen sus pruebas en el Front (`npm test`, 8 archivos y 76 pruebas aprobadas), que `audit.md` lista por grupo.

### Resultado por regla

Las columnas de escenarios cuentan los del corte 1 que la regla cita en su **Prueba**. Un escenario omitido o pendiente se nombra en `audit.md`, que lista su razón.

| Regla | Escenarios (aprobados, omitidos, pendientes) | Pruebas unitarias aprobadas | Resultado |
| --- | --- | --- | --- |
| BR-PERIODO-01 | 1, 0, 0 | 8 | Aprobada |
| BR-PERIODO-02 | 4, 0, 0 | 0 | Aprobada |
| BR-PERIODO-03 | 4, 0, 0 | 0 | Aprobada |
| BR-PERIODO-04 | 5, 0, 1 | 2 | Aprobada en local; 1 pendiente (ver audit.md) |
