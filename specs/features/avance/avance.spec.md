---
name: Avance del registro
description: Etapa de cada sección al alcance de la coordinación, por carrera o por curso, y su conteo, en la ruta 17 GET /api/avance, sin cifras del R-17 ni datos de personas.
targets:
  - ../../../app/rutas/avance.py
  - ../../../abet_carga/avance.py
  - ../../../app/permisos.py
---

# Avance del registro

> **Estado al 2026-11-23 (T038).** Los archivos de `targets` existen y BR-AVANCE-01 a 04 tienen su prueba en verde. BR-AVANCE-05 sigue sin código, porque el campo `profesores` espera a D-47 y a D-51. **Estado al 2026-11-23.** Spec viva abierta con la etapa B de la spec 007 (US-64 y US-65, FR-014 de esa spec), que la spec 008 construye con el alcance de la coordinación por carrera o por curso (J-57 y T010 de la spec 008). Las reglas se escriben antes del código, los archivos de `targets` nacen con T038 de la spec 008 y la sección Verification se llena con su T060.

Esta spec viva fija qué devuelve la ruta `GET /api/avance` de la interfaz de programación de aplicaciones (application programming interface, API), la ruta 17 de `docs/03-api/contrato.md` del Front, con la que la coordinación sigue el registro de los profesores sin abrir sección por sección, y qué lee de ella la pantalla P7 «Avance del registro» (propuesta). Cada regla de negocio (business rule, BR) nombra su fuente en `specs/007-experiencia-por-cuenta/spec.md` o en `specs/008-ciclo-quimica-industrial/spec.md`, sean historias de usuario (user stories, US), requisitos funcionales (functional requirements, FR) o decisiones abiertas (D de la carrera y J de Jefferson), con la spec que la fija. Cada regla nombra también las tablas que lee y el escenario que la prueba, citado por su título, de `specs/007-experiencia-por-cuenta/aceptacion/avance_del_registro.feature` o de `specs/008-ciclo-quimica-industrial/aceptacion/avance_del_curso.feature`. Los textos entre «» son literales, y lo marcado «(propuesta)» no está fijado en las decisiones de la spec, como en los `.feature`, aunque algún escenario ya lo compruebe. Los ejemplos usan solo datos inventados, con correos del dominio reservado `example.invalid`.

## User Stories

| ID | Descripción | Spec |
| --- | --- | --- |
| US-64 | La ruta 17 da a la coordinación la etapa de cada sección | spec 007 |
| US-65 | La coordinación entra a P7 y ve cuántas secciones faltan | spec 007 |
| US-66 | P7 dice a quién recordar el registro, que espera a D-47 y a D-51 de la spec 008 | spec 007 |
| US-79 | La ruta 17 y P7 alcanzan a la coordinación del curso | spec 008 |

## Business Rules

### BR-AVANCE-01: Solo la coordinación lee el avance, en el orden 401, 403 y 422
- `GET /api/avance` exige la sesión y admite solo a un usuario activo con rol COORDINADOR, por `puede_ver_avance()` de `app/permisos.py` (BR-ACCESO-12). Sin sesión responde 401, el profesor recibe 403 con «Esta página es de la Coordinación.» (propuesta) también con un periodo mal formado, y la coordinación con un periodo de otra forma que `AAAA-C` recibe 422 con «El periodo no tiene la forma AAAA-C.».
- Sin `periodo`, la ruta usa `PERIODO_VIGENTE`, como la lista de secciones (BR-PERIODO-01), y con `periodo` sigue el periodo elegido (BR-PERIODO-05). Lleva `Cache-Control: no-store`, como toda `/api`, y entra en la prueba que recorre las rutas registradas (`tests/rutas_registradas.py`).
- **Fuente**: US-64 y FR-008 de la spec 007, y US-79 de la spec 008.
- **Prueba**: «Solo la coordinación lee el avance, en el orden 401, 403 y 422» y «Sin periodo, la ruta 17 usa el periodo vigente» (`avance_del_registro.feature`), y «El profesor del curso no lee el avance» (`avance_del_curso.feature`).

### BR-AVANCE-02: Las secciones del avance salen de secciones_visibles()
- La ruta devuelve solo las secciones que `app/permisos.secciones_visibles()` da a la cuenta en el periodo, sin una rama por rol ni una condición de alcance propia (BR-ACCESO-07 y BR-ACCESO-13). La coordinación de Ambiental, con la carrera AMB, recibe las secciones de su carrera, y la coordinación de Química General, con 5643 en 2026-1, recibe la 701 a la 704 y ninguna de 450002.
- Un periodo sin secciones al alcance responde 200 con `secciones` vacía y el conteo en 0, así que la coordinación de Ambiental recibe el avance de 2026-1 vacío y la del curso el de 2026-2 vacío.
- **Fuente**: FR-008 de la spec 007, y US-79, FR-008 y FR-014 de la spec 008.
- **Prueba**: «La ruta 17 da la etapa de cada sección en el orden de asignatura y número» (`avance_del_registro.feature`), y «La ruta 17 da la etapa de cada sección del curso y ninguna de otro curso», «Un periodo sin secciones del curso responde vacío» y «La coordinación de Ambiental no ve el avance de Química» (`avance_del_curso.feature`).

### BR-AVANCE-03: La etapa se deriva en cada lectura con la precedencia de J-48
- Cada sección recibe una sola etapa, derivada en cada lectura en una sola consulta del Back y sin guardarse en ninguna tabla. Primero SIN_PLAN, cuando `abet.plan_medicion` no tiene filas de su asignatura en el periodo, después PUBLICADA, con una carga PUBLICADA en `abet.carga`, después SIN_PROFESOR, sin un usuario activo con rol PROFESOR en `acceso.docente_seccion`, después CON_RECHAZO, con al menos una carga RECHAZADA, y en otro caso SIN_CARGA.
- Una sección con una carga PUBLICADA y su único profesor dado de baja después queda PUBLICADA, una carga EN_CURSO no cuenta como carga y una carga REEMPLAZADA con su sucesora PUBLICADA deja la sección en PUBLICADA (valor provisional de J-48 de la spec 007). La 704 de Química General, sin profesor, queda en SIN_PROFESOR, como en `secciones_sin_docente.sql` de la spec 006.
- **Fuente**: US-64, FR-009 y J-48 de la spec 007.
- **Prueba**: «La precedencia de J-48 decide la etapa de cada sección» (`avance_del_registro.feature`) y «La ruta 17 da la etapa de cada sección del curso y ninguna de otro curso» (`avance_del_curso.feature`).

### BR-AVANCE-04: Respuesta, orden y conteo sin cifras del R-17 ni datos de personas
- La ruta responde `periodo`, `conteo`, con `secciones` y una cifra por etapa, y `secciones`, cada una con `seccion_id`, `asignatura` (`codigo` y `nombre`), `numero`, `etapa` y el `carga_id` de su carga PUBLICADA o `null`, en el orden de código de asignatura y número de sección (J-47 de la spec 007).
- La respuesta no trae porcentajes, niveles, cifras del R-17, códigos ni nombres de estudiantes, nombres de profesores ni datos de `acceso.credencial`. El bloque de reglas y la división de la carga publicada entre declarada y por declarar llegan después como campos aditivos.
- P7 escribe lo que trae la ruta, con «N de M secciones con carga publicada.» y cada etapa con texto además de cualquier color, y su título para la coordinación de un curso es «Avance del registro del curso» (propuesta, FR-014 de la spec 008). Sus textos viven en `docs/01-arquitectura/frontend.md` del Front y los prueba Vitest.
- **Fuente**: US-64, US-65, FR-009, FR-010 y J-47 de la spec 007, y FR-014 de la spec 008.
- **Prueba**: «La ruta 17 da la etapa de cada sección en el orden de asignatura y número» (`avance_del_registro.feature`) y «La ruta 17 da la etapa de cada sección del curso y ninguna de otro curso» (`avance_del_curso.feature`). Los escenarios de P7 los prueba Vitest en el Front.

### BR-AVANCE-05: Los correos de los profesores esperan a D-47 y a D-51
- El campo `profesores` de US-66 no existe mientras D-47 no se responda en Ambiental ni D-51 en Industrial. Si la respuesta es sí, trae solo a la cuenta COORDINADOR, en orden alfabético, los correos de los usuarios activos con rol PROFESOR de `acceso.docente_seccion` en las secciones CON_RECHAZO y SIN_CARGA, y `[]` en las demás, sin nombres y sin envío desde la aplicación.
- La ruta 17 de Industrial sale sin el campo `profesores`, y la guía de la capacitación no lo promete (US-87 de la spec 008).
- **Fuente**: US-66, FR-010 y D-47 de la spec 007, y D-51 de la spec 008.
- **Prueba**: «La ruta 17 trae solo los correos de los profesores activos de las secciones que faltan» (`avance_del_registro.feature`), que espera a D-47 con los demás escenarios de US-66.

## Verification

- 2026-11-23 (T038 de la spec 008). `uv run --frozen --no-build pytest -q -p no:cacheprovider tests/aceptacion/pasos/test_avance_feature.py tests/test_api_avance.py` da 21 passed. Cubre BR-AVANCE-01 (el orden 401, 403 y 422, el periodo vigente y las rutas registradas), BR-AVANCE-02 (la carrera, el curso, Ambiental sin Química, el periodo vacío y la coordinación sin alcance), BR-AVANCE-03 (el esquema de J-48 con siete casos y la lectura sin escritura) y BR-AVANCE-04 (las claves cerradas, el orden, el conteo y SC-005 con 60 secciones). BR-AVANCE-05 espera a D-47 y a D-51. La línea de T060 llega con la auditoría.
