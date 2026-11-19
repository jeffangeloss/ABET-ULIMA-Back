---
name: Resultados
description: Logros por resultado del estudiante (SO) y por indicador de desempeño (PI) de las secciones al alcance del usuario, leídos de abet.v_r17_por_pi con las cifras y la regla de la meta del R-17, sin datos de personas.
targets:
  - ../../../app/rutas/resultados.py
  - ../../../abet_carga/resultados.py
  - ../../../abet_carga/r17.py
  - ../../../app/permisos.py
  - ../../../db/migration/R__vista_r17_por_pi.sql
  - ../../../db/plataforma/neon/revisar_permisos_resultados.sql
---

# Resultados

> **Estado al 2026-11-18.** Reglas de la fase 1 de contrato de la spec 004 (T010), escritas antes del código en la rama `feat/004-reportes-docente`, después de la aprobación de Jefferson en el chat el 2026-11-18 («Sí, apruébala»). Los archivos de `targets` nacen o cambian en las fases 2 a 4, y la sección Verification se llena el mismo día con T060, sobre Back 0db6ee3 y Front 203d822.

Esta spec viva fija qué devuelve la ruta `GET /api/resultados` de la interfaz de programación de aplicaciones (application programming interface, API), la ruta 12 de `docs/03-api/contrato.md` del Front, con los logros por resultado del estudiante (student outcome, SO), y qué muestra con ella la pantalla P6 «Mis logros por SO» (propuesta). La ruta entrega a cada usuario el logro de cada indicador de desempeño (performance indicator, PI) de sus secciones, agrupado bajo su SO y frente a la meta, con las mismas cifras del R-17 de cada carga. Cada regla de negocio (business rule, BR) nombra su fuente en `specs/004-reportes-docente/spec.md`, sean historias de usuario (user stories, US), requisitos funcionales (functional requirements, FR), criterios de éxito (success criteria, SC), decisiones del crítico de arquitectura (AD) o decisiones de Jefferson (J). Cada regla nombra también la vista, la restricción o la consulta de control que la respalda y el escenario que la prueba, citado por su título, de `specs/004-reportes-docente/aceptacion/resultados.feature` o de `alcance_y_privacidad.feature`. Los textos entre «» son literales, y lo marcado «(propuesta)» no está fijado en las decisiones de la spec, como en los `.feature`, aunque algún escenario ya lo compruebe. Los ejemplos usan solo datos inventados.

## User Stories

| ID | Descripción | Corte |
| --- | --- | --- |
| US-37 | Ver mis logros por SO en el periodo | spec 004 |
| US-38 | El reporte solo muestra mis secciones | spec 004 |
| US-39 | Distinguir lo que todavía no tiene resultado | spec 004 |
| US-40 | Las cifras del reporte son las de mi R-17 | spec 004 (un escenario del corte 2) |
| US-41 | El reporte dice cuándo sus resultados son provisionales | spec 004 |
| US-42 | El reporte no expone a estudiantes ni a otros usuarios | spec 004 |
| US-43 | Ver cómo se reparten mis estudiantes por nivel | spec 004 |
| US-44 | El coordinador ve los resultados de todas las secciones de la carrera | spec 004 |

## Business Rules

### BR-RESULTADOS-01: Una ruta por usuario y por periodo, sin identificadores
- `GET /api/resultados?periodo=2026-2` devuelve los logros de las secciones del periodo al alcance del usuario de la sesión. La ruta no recibe `seccion_id`, `carga_id` ni otro identificador (J-23), y FastAPI ignora el parámetro que la ruta no declara, así que un `seccion_id` en la consulta deja la respuesta igual.
- Sin `periodo`, la ruta usa `PERIODO_VIGENTE` (BR-PERIODO-01). Un `periodo` con otra forma que `AAAA-C` responde 422 con «El periodo no tiene la forma AAAA-C.» (propuesta), y un periodo bien formado sin secciones del usuario responde 200 con `so` y `secciones` vacíos (BR-PERIODO-04).
- Sin cookie, con la sesión vencida o con el usuario dado de baja, la ruta responde 401 con «La sesión venció. Ingrese otra vez.» (propuesta) y sin secciones (BR-ACCESO-06 y BR-ACCESO-10).
- Las respuestas 200, 401 y 422 llevan `Cache-Control: no-store`, como toda respuesta de `/api` (propuesta).
- **Fuente**: US-37, US-38, US-39, US-42, FR-001, FR-002, J-23 y J-25 de la spec 004.
- **Prueba**: «Un seccion_id en la consulta no abre otra sección», «Sin una sesión vigente no hay resultados», «Un periodo mal formado responde 422» y «Ninguna respuesta de la ruta queda en una caché» (`alcance_y_privacidad.feature`), y «Sin secciones en el periodo, la respuesta es una lista vacía y no un error» (`resultados.feature`). La ruta sin `periodo` no tiene escenario, y la comprueba `tests/test_api_resultados.py`.

### BR-RESULTADOS-02: El alcance sale de app/permisos.secciones_visibles()
- La ruta devuelve solo las secciones que `app/permisos.secciones_visibles()` da al usuario para el periodo, en su mismo orden, por código de asignatura y número de sección, sin una condición de alcance propia (BR-ACCESO-07). El profesor recibe las secciones que `acceso.docente_seccion` le asigna, y el coordinador todas las de la carrera sin filas propias.
- El alcance se lee de la base en cada petición, así que una asignación que el dueño de la base retira deja de verse en la petición siguiente con la misma cookie (BR-ACCESO-06).
- Dos profesores asignados a la misma sección la ven los dos con las mismas cifras, porque `uq_docente_seccion` admite varios usuarios por sección.
- Ninguna parte de la respuesta del profesor trae el número, el `seccion_id` ni el `carga_id` de una sección ajena.
- **Fuente**: US-38, US-44, FR-002, AD-07 y J-28.
- **Prueba**: «El reporte del profesor de varias secciones no trae las de otros profesores», «Cada profesor de una sección ve solo la suya» y «El alcance se lee de la base en cada petición» (`alcance_y_privacidad.feature`), y «El coordinador ve las cinco secciones del periodo» (`resultados.feature`). La codocencia no tiene escenario, y la comprueba `tests/test_api_resultados.py`.

### BR-RESULTADOS-03: Las cifras salen de abet.v_r17_por_pi en una sola instantánea
- Cada indicador sale de `abet.v_r17_por_pi`, filtrada solo por el `carga_id` de la carga PUBLICADA de cada sección visible (`uq_carga_publicada_por_seccion`), la misma fuente del bloque II del R-17 (BR-R17-02 e invariante 1 de ADR-008 del Front).
- La lista de `carga_id` viaja a la base como `int[]` y contiene solo los identificadores que la propia base devuelve en la misma petición, nunca un valor que llega con ella.
- La ruta lee las secciones, las cargas y las cifras en una sola transacción `READ ONLY` con `REPEATABLE READ`, así que un reemplazo del corte 2 que ocurre a mitad de la lectura no deja una sección PUBLICADA sin indicadores.
- `estudiantes_por_nivel` son `n_nivel_1` a `n_nivel_4`, `logrados` es `n_esperado_o_superior`, `calificados` es `n_total` menos `n_sin_evidencia` (BR-R17-03), `sin_evidencia` es `n_sin_evidencia` y `total` es `n_total`.
- `pct_sobre_calificados` es `pct_logro_sobre_calificados`, `pct_sobre_total` es `pct_logro_sobre_total_con_sin_evidencia`, `meta_pct` es `meta_logro_pct` y `nivel_esperado` es el de la vista.
- El filtro por `carga_id` baja dentro de la vista, por debajo de su agregación, porque la vista lleva `security_barrier` y la igualdad de enteros es a prueba de fugas (leakproof). Con 150 secciones sembradas en la base desechable, la ruta del coordinador responde en menos de 1 s, sin contar el arranque en frío de Neon (SC-005).
- Leer la ruta no escribe en ninguna tabla de `abet` ni de `acceso`, y las consultas de control Q01 a Q14 siguen en 0 filas (SC-006).
- **Fuente**: US-37, US-40, FR-004, SC-001, SC-003, SC-005, SC-006, AD-02 y J-26.
- **Prueba**: «El profesor de varias secciones ve sus logros agrupados por SO», «Los nueve indicadores coinciden con los tres R-17», «Con un estudiante sin evidencia, el segundo porcentaje también coincide con el R-17», «Leer el reporte no escribe en la base» y, del corte 2, «Una carga reemplazada sale del reporte» (`resultados.feature`). La instantánea, el plan de `EXPLAIN` y el tiempo con 150 secciones no tienen escenario, y los comprueba `tests/test_api_resultados.py` (T032 y T034).

### BR-RESULTADOS-04: El catálogo de cada indicador sale del plan de su carga
- El SO, su descripción, el PI y el instrumento de cada indicador salen del plan de medición de la carga, que es `abet.plan_medicion` con `abet.pi` por `pi_id`, `abet.so` por `so_id` y `abet.instrumento` por `instrumento_id`, nunca de un código o un número buscados en todo el catálogo.
- La vista no expone `pi_id` (J-26), así que cada fila de la vista se empareja con la fila del plan de su carga por el código del PI. Este código es único dentro del plan, porque el plan usa la versión de catálogo vigente del periodo (`fk_plan_medicion_vigencia`) y `uq_pi_codigo` no repite un código en una versión, de modo que una segunda versión de catálogo en la base no duplica ningún indicador.
- Un PI sin instrumento en el plan, con `plan_medicion.instrumento_id` nulo porque la fuente del catálogo trae «-», llega con `instrumento` nulo.
- Las secciones van en el orden de BR-RESULTADOS-02, y los indicadores de cada sección por el número de su SO y el número de su PI, así que el 5.10 va después del 5.2.
- `pi` de cada sección trae los PI de su plan con la misma lectura y el mismo orden de `GET /api/secciones` (BR-PERIODO-04).
- `so` trae una vez cada SO que mide el plan de alguna sección de la respuesta, por número y con su `numero` y su `descripcion`, aunque la sección no tenga carga.
- **Fuente**: US-37, US-39, FR-005, AD-02 y AD-04.
- **Prueba**: «El profesor de varias secciones ve sus logros agrupados por SO» y «Una sección sin carga publicada no trae cifras» (`resultados.feature`). El PI sin instrumento, la segunda versión de catálogo y el PI 5.10 no tienen escenario, porque ningún dato inventado los trae, y los comprueba `tests/test_api_resultados.py` (T035).

### BR-RESULTADOS-05: Números de un decimal y nulos que nunca valen 0
- Los porcentajes y la meta viajan como números de JavaScript Object Notation (JSON) con el decimal de `ROUND(…, 1)` de la vista, como `81.8` y `80.0`, y nunca como textos (J-22). El Back convierte cada `Decimal` con `abet_carga.resultados.cifra()` antes de responder.
- Un nulo de la vista viaja como `null`, nunca como 0. Un PI sin calificaciones trae `pct_sobre_calificados` nulo y `en_meta` nulo, mientras `pct_sobre_total` vale 0.0. La vista divide con `NULLIF` y deja sin logro al PI sin mediciones calificadas (H80).
- Un conjunto de reglas sin NIVEL_ESPERADO DEFINIDO deja nulos `nivel_esperado`, `logrados`, los dos porcentajes y `en_meta`, y uno sin META_LOGRO DEFINIDA deja nulos `meta_pct` y `en_meta`, como la vista.
- **Fuente**: US-37, US-39, FR-007, FR-013, J-22 y AD-03.
- **Prueba**: «Las cifras viajan como números de un decimal», «Un PI sin calificaciones no sale como 0 %» y «Un estudiante sin evidencia deja dos porcentajes» (`resultados.feature`). La conversión de 63,6 en `63.6` y los nulos de un conjunto sin nivel esperado o sin meta no tienen escenario, y los comprueban `tests/test_resultados.py` y `tests/test_api_resultados.py`.

### BR-RESULTADOS-06: Una sola regla de la meta para la ruta y el R-17
- `en_meta` es verdadero cuando `pct_sobre_calificados` es mayor o igual que `meta_pct`, falso cuando es menor y nulo cuando falta alguno de los dos, así que el 80,0 % justo queda en la meta.
- La decide `abet_carga.resultados.en_meta()`, una función pura que usan la ruta y `_plan_de_accion` de `abet_carga/r17.py`. Así, `en_meta` es verdadero si y solo si la celda H de la fila del PI en el bloque II del R-17 trae el texto de logro (invariante 2 de ADR-008).
- El Front no compara cifras, y P6 escribe el estado que trae la API.
- **Fuente**: US-37, US-40, FR-008 y AD-03.
- **Prueba**: «El 80,0 % justo queda en la meta» y «Los nueve indicadores coinciden con los tres R-17» (`resultados.feature`), y las pruebas de la función en `tests/test_resultados.py`.

### BR-RESULTADOS-07: Lo que todavía no tiene resultado no se cuenta como resultado
- Una sección sin carga PUBLICADA llega con `estado` «SIN_CARGA», `carga_id` nulo, los PI de su plan en `pi` e `indicadores` vacío, también cuando todas sus cargas están RECHAZADAS, igual que en `GET /api/secciones` (BR-PERIODO-04). Una sección sin plan de medición llega además con `pi` vacío.
- Una carga RECHAZADA o REEMPLAZADA no da indicadores, porque la vista filtra `estado = 'PUBLICADA'` (BR-R17-01). El 409 de un segundo archivo en una sección con carga publicada no crea ninguna carga, así que la ruta sigue mostrando la misma carga PUBLICADA.
- Un estudiante sin evidencia cuenta en `sin_evidencia` y en `total` y no en `calificados`, de modo que el indicador trae los dos porcentajes que pide el valor provisional de D-05 de la spec 001, sobre los calificados y sobre el total.
- **Fuente**: US-39, US-40, FR-009, FR-013 y D-05 de la spec 001.
- **Prueba**: «Una sección sin carga publicada no trae cifras», «Una carga rechazada no cuenta como resultado», «Un PI sin calificaciones no sale como 0 %», «Un estudiante sin evidencia deja dos porcentajes» y «Sin secciones en el periodo, la respuesta es una lista vacía y no un error» (`resultados.feature`). Del corte 2, la prueba es «Una carga reemplazada sale del reporte».

### BR-RESULTADOS-08: La marca provisional va por sección
- Cada sección con carga trae `provisional` de la vista y `conjunto_reglas`, `conjunto_reglas_estado` y `parametros_pendientes` del conjunto de reglas de su carga (`carga.conjunto_reglas_id`), con los valores y el orden de la constancia (BR-R17-10). Una sección sin carga trae los cuatro campos nulos.
- Con R-2026-BORRADOR, `provisional` es verdadero y `parametros_pendientes` trae TRATO_SIN_EVIDENCIA, CORTE_ROJO y CONVERSION_NIVEL_0_1. Un conjunto APROBADO con un parámetro de la vista en PENDIENTE sigue provisional, el caso que vigila la consulta de control Q11, y solo un conjunto APROBADO con NIVEL_ESPERADO, META_LOGRO y TRATO_SIN_EVIDENCIA DEFINIDOS da `provisional` falso (BR-R17-05).
- En Neon ningún conjunto se aprueba dentro del producto mínimo viable (minimum viable product, MVP), así que el piloto muestra siempre resultados provisionales.
- **Fuente**: US-41, FR-010 y Principio IV de la constitución.
- **Prueba**: «Con R-2026-BORRADOR los resultados son provisionales», «Con reglas aprobadas los resultados salen sin la marca» y «Un conjunto aprobado que no define todos sus parámetros sigue provisional» (`resultados.feature`).

### BR-RESULTADOS-09: Lista cerrada de claves y ningún dato de personas
- La respuesta trae solo `periodo`, `so` y `secciones`, y cada elemento de `so` trae solo `numero` y `descripcion`.
- Cada sección trae solo `seccion_id`, `asignatura` (con `codigo` y `nombre`), `numero`, `estado`, `carga_id`, `pi`, `conjunto_reglas`, `conjunto_reglas_estado`, `parametros_pendientes`, `provisional` e `indicadores`.
- Cada indicador trae solo `so`, `pi`, `instrumento`, `nivel_esperado`, `estudiantes_por_nivel`, `logrados`, `calificados`, `sin_evidencia`, `total`, `pct_sobre_calificados`, `pct_sobre_total`, `meta_pct` y `en_meta`. La ruta arma cada objeto campo por campo, sin `SELECT *` ni copias de filas enteras (AD-14).
- Ninguna parte trae `subida_por`, `nombre_archivo`, `sha256`, `trato_sin_evidencia`, `pct_logro_segun_regla`, un correo ni el código o el nombre de un estudiante. La ruta no consulta `abet.estudiante` ni `abet.archivo_origen`, y de `abet.medicion` recibe solo los conteos que agrega la vista, aunque `abet_app` puede leer las tres tablas (Principio II de la constitución).
- **Fuente**: US-42, FR-006 y AD-14.
- **Prueba**: «La respuesta trae solo las claves de la lista cerrada» y «La respuesta no trae códigos, nombres ni correos» (`alcance_y_privacidad.feature`), y «El coordinador ve las cinco secciones del periodo» (`resultados.feature`).

### BR-RESULTADOS-10: El coordinador ve la carrera sin un orden por resultado
- El coordinador recibe con la misma ruta todas las secciones de la carrera en el periodo, las que `_ALCANCE` de `app/permisos.py` da al rol COORDINADOR sin filas en `acceso.docente_seccion` (BR-ACCESO-07), con las mismas cifras que ve el profesor de cada sección.
- Las secciones van por código de asignatura y número de sección, nunca por su porcentaje, y la respuesta no trae correos ni nombres de profesores, para que P6 no arme un ranking de docentes (H05 y J-28).
- La comparación entre secciones de N9, el consolidado por PI y la cifra por SO (D-32) y el agregado del curso o de la carrera (D-33) quedan fuera de esta ruta.
- **Fuente**: US-44, AD-09 y J-28.
- **Prueba**: «El coordinador ve las cinco secciones del periodo» y «P6 del coordinador agrupa por asignatura y no ordena por resultado» (`resultados.feature`).

### BR-RESULTADOS-11: P6 escribe lo que trae la API y no lo recalcula
- La pantalla P6 «Mis logros por SO» (propuesta) del Front consume solo esta ruta. Agrupa los indicadores bajo su SO con la descripción que trae `so`, y cada fila escribe su PI, su sección, su porcentaje, su fracción y su estado, «En la meta» o «Debajo de la meta» (propuestas).
- La barra de cada fila es de lenguaje de marcado de hipertexto (HyperText Markup Language, HTML) y Tailwind, con el ancho en `style` y sin biblioteca de gráficos (J-24). Lleva `aria-hidden`, y la meta se marca con una línea y con texto, de modo que ningún estado depende solo del color (criterios 1.4.1 y 1.4.11 de las pautas de accesibilidad para el contenido web, Web Content Accessibility Guidelines, WCAG).
- P6 escribe con texto lo que no se mide, que es la sección sin carga, el PI sin calificaciones, los estudiantes sin evidencia, el nivel esperado o la meta sin definir, el PI sin instrumento, la sección sin plan y la lista vacía, y nunca dibuja una barra de 0 % para un nulo (SC-004).
- P6 muestra la franja provisional de cada sección con el texto que corresponde a `conjunto_reglas_estado`, como `_franja` de `abet_carga/r17.py`, y ofrece el R-17 de cada sección PUBLICADA por la ruta del R-17 de su carga.
- P6 no ofrece «Subir export», no muestra correos ni nombres de profesores y no escribe en `localStorage` ni en `sessionStorage`. P2 y P4 siguen sin porcentajes (invariante 8 de ADR-008).
- **Fuente**: US-37 a US-44, FR-011 a FR-016, SC-004, SC-007, J-24 y la sección 9 de `docs/01-arquitectura/frontend.md` del Front.
- **Prueba**: los diez escenarios con `@delegado_a_vitest` de los dos `.feature`, que comprueban `tests/pantallas/MisLogros.test.tsx` y `tests/App.test.tsx` del Front, y la prueba de humo de `e2e/humo.spec.ts` del Front contra la vista previa de `develop` (T043 y T071).

## Verification

Corrida del 2026-11-18 en el Back y en el Front, rama `feat/004-reportes-docente`, sobre un PostgreSQL 18 desechable que arma la propia suite. La más reciente va primero y cada línea lleva la fecha, el comando, el archivo de prueba y las reglas que cubre.

```text
- 2026-11-18 · uv run --frozen --no-build pytest -q -p no:cacheprovider · test_resultados_feature.py, test_alcance_resultados_feature.py, test_api_resultados.py, test_resultados.py, test_rutas_protegidas.py, test_permisos_resultados.py → BR-RESULTADOS-01 a BR-RESULTADOS-10
- 2026-11-18 · npx vitest run (Front) · tests/pantallas/MisLogros.test.tsx, tests/App.test.tsx, tests/servicios/api.test.ts, tests/servicios/formato.test.ts → BR-RESULTADOS-11
- 2026-11-18 · npx playwright test e2e/humo.spec.ts (Front) contra scripts/api_local.sh del Back · los dos casos de P6 → BR-RESULTADOS-03 y BR-RESULTADOS-11 en local
- 2026-11-18 · revisar_permisos_resultados.sql en la rama develop de Neon, desde el Windows de Jefferson y en solo lectura → BR-RESULTADOS-03 (sin migración)
```

Resultado: suite completa del Back, 1440 passed y 15 skipped in 156.81s (0:02:36), con los 45 casos de los dos `.feature` de la spec 004 aprobados, 12 de ellos delegados a Vitest; Vitest del Front, 11 archivos y 164 pruebas aprobadas; humo local, 5 passed; Neon `develop`, «Faltan 0 permisos de lectura de la ruta 12.». El detalle por historia está en `specs/004-reportes-docente/audit.md`, y la corrida del humo contra la vista previa de `develop` queda para T071, después de las dos fusiones.

### Resultado por regla

Las columnas de escenarios cuentan los que la regla cita en su **Prueba**, y un caso delegado a Vitest cuenta como aprobado cuando su prueba del Front pasa.

| Regla | Escenarios (aprobados, omitidos, pendientes) | Casos | Pruebas unitarias aprobadas | Resultado |
| --- | --- | --- | --- | --- |
| BR-RESULTADOS-01 | 5, 0, 0 | 10 | 12 | Aprobada |
| BR-RESULTADOS-02 | 4, 0, 0 | 5 | 2 | Aprobada |
| BR-RESULTADOS-03 | 5, 0, 0 | 5 | 7 | Aprobada, con el `EXPLAIN` y 150 secciones (SC-005) |
| BR-RESULTADOS-04 | 2, 0, 0 | 2 | 3 | Aprobada |
| BR-RESULTADOS-05 | 3, 0, 0 | 3 | 10 | Aprobada |
| BR-RESULTADOS-06 | 2, 0, 0 | 2 | 34 | Aprobada |
| BR-RESULTADOS-07 | 6, 0, 0 | 7 | 5 | Aprobada |
| BR-RESULTADOS-08 | 3, 0, 0 | 3 | 3 | Aprobada |
| BR-RESULTADOS-09 | 3, 0, 0 | 3 | 1 | Aprobada |
| BR-RESULTADOS-10 | 2, 0, 0 | 2 | 1 | Aprobada, con un escenario delegado a Vitest |
| BR-RESULTADOS-11 | 10, 0, 0 | 12 | 20 en Vitest | Aprobada en Vitest y en el humo local; la vista previa queda para T071 |
