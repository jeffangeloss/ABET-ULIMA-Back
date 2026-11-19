# Feature Specification: Los logros del profesor por SO, solo en sus secciones

**Feature Branch**: `docs/004-reportes-docente` (PR a `develop`), con la implementación en `feat/004-reportes-docente` del Back y del Front después de la aprobación
**Created**: 2026-11-17
**Status**: Aprobada por Jefferson en el chat el 2026-11-18 («Sí, apruébala»), con J-21 a J-28 en el valor que propone la spec
**Input**: «los profesores suben sus export de blackboard, ellos desean como constancia su R17 y que bueno, el profesor tmb vea de forma visual con reportes como le ha ido a él frente a los SO, pero solamente debe poder consultar a él e sus secciones, no otras secciones de otros profesores. Ese debería ser el límite, tampoco él debería subir un export a secciones que no son de él.» (Jefferson, 2026-11-17, por la sesión que encarga la spec 004)

## Épica

> **EP-04. El profesor ve cómo le va en los SO de sus secciones, y solo en ellas.** Hoy el profesor sube su export y descarga el R-17 de cada carga, pero ninguna pantalla le muestra sus resultados por resultado del estudiante (student outcome, SO) ni por indicador de desempeño (performance indicator, PI). El contrato de la interfaz de programación de aplicaciones (application programming interface, API) dice que «Los porcentajes no viajan por la API, porque viven solo en el R-17.», así que un profesor con tres secciones abre tres libros para saber cómo le fue. El prototipo de Power BI muestra además a cualquier usuario la lista y el orden de los docentes (H05). Esta épica agrega una ruta y una pantalla que muestran, con barras y cifras escritas, el porcentaje de estudiantes que alcanza el nivel esperado en cada PI de las secciones del usuario, agrupado por SO y frente a la meta. Las cifras son las del R-17, y el límite es el mismo que ya rige la subida, la constancia y el R-17.

Convenciones de esta spec. Todos los datos son inventados y siguen las convenciones de las specs 001 y 003. Las secciones de prueba son la 410 y la 411 de 450002 «Principios de Ingeniería Sostenible» en 2026-2, de `docente410@example.invalid` y `docente411@example.invalid`, y la 412 de 450002 y la 410 y la 412 de 450010 «Gestión Sostenible de Residuos», de `docente.varias@example.invalid`. El plan de 450002 mide 5.1, 5.2 y 5.3 del SO 5, y el de 450010 mide 2.1 y 2.2 del SO 2 y 5.1 del SO 5, todos con el instrumento «Trabajo Integrador». Los datos de `docente.varias@example.invalid` viven en `db/datos/varias_secciones_2026_2_inventado.sql`, que corre solo en las bases desechables de las pruebas y nunca en Neon, así que el piloto conserva los valores provisionales de D-09 y D-13. Ningún export nuevo entra a `tests/datos_inventados/`, y las copias con celdas vacías se arman en `tmp_path`. La spec no agrega tablas, columnas, restricciones, vistas ni roles, y por eso no necesita migración (J-26). Lo que el redactor decide sin fuente va marcado «(propuesta)».

Prefijos e identificadores. La épica lleva el prefijo EP y continúa la numeración de las specs 001 a 003 (EP-04). Las historias US continúan desde US-37, porque la spec 003 usa US-26 a US-36 y la spec 002 de la rama `docs/002-capstone` usa US-22 a US-25, y las decisiones abiertas siguen desde D-32 y J-21 por la misma razón. Los requisitos funcionales FR (functional requirement), los criterios de éxito SC (success criterion) y las tareas T se numeran dentro de esta spec, así que una regla viva que cite uno de ellos nombra la spec, como «FR-003 de la spec 004». La ruta nueva es la 12 del contrato del Front, porque la spec 002 reserva la 11 para `POST /api/secciones/{seccion_id}/proyectos`, y la pantalla nueva es P6, porque la spec 002 no agrega pantallas y P5 es del corte 2 de la spec 001. Las candidatas de la auditoría se llaman C-01 a C-22, y su revisión está en `revision-historias.md`. N# es una fila de `Requisitos_Sistema_Medicion.xlsx`, y H## y P## son filas de las hojas Hallazgos y «Preguntas al cliente» de `Entregables/Revision_Requisitos_y_Tableros.xlsx`, en la carpeta `ABET_SIS_MED`, fuera de los repositorios.

Siglas y términos. Las de las specs 001 y 003 valen aquí. ADR es un registro de decisión de arquitectura (architecture decision record), WCAG son las pautas de accesibilidad para el contenido web (Web Content Accessibility Guidelines) y SQL es el lenguaje de consultas estructurado (Structured Query Language). HTML es el lenguaje de marcado de las páginas web (HyperText Markup Language). El logro de un PI en una sección es el porcentaje de sus estudiantes calificados que alcanza el nivel esperado o uno superior, es decir `pct_logro_sobre_calificados` de `abet.v_r17_por_pi`, el mismo número del bloque II del R-17. Un PI está en la meta cuando su logro es mayor o igual que la meta, que es la comparación del plan de acción del R-17. Un indicador es una fila de la ruta nueva por sección y PI, y P6 es la pantalla nueva «Mis logros por SO» (propuesta).

Cifras de prueba, recalculadas desde NIVELES_410, NIVELES_450002_412, NIVELES_450010_410 y NIVELES_450010_412 de `scripts/generar_exports_inventados.py`, con la meta de 80 % y el nivel esperado 3 de R-2026-BORRADOR. La columna de niveles cuenta estudiantes en los niveles 1, 2, 3 y 4.

| Sección y export | Profesor | Estudiantes por nivel | Logro por PI | En la meta |
| --- | --- | --- | --- | --- |
| 410 de 450002, `sintetico_20262_450002_410.xlsx` | docente410 | 5.1 [1, 3, 4, 3], 5.2 [1, 3, 4, 3], 5.3 [1, 2, 5, 3] | 63,6 % (7 de 11), 63,6 % (7 de 11) y 72,7 % (8 de 11) | Ninguno |
| 411 de 450002, `export_inventado_411.xlsx` | docente411 | Los de la 410, con los estudiantes en orden inverso | 63,6 %, 63,6 % y 72,7 % | Ninguno |
| 412 de 450002, `sintetico_20262_450002_412.xlsx` | docente.varias | 5.1 [1, 1, 5, 4], 5.2 [2, 3, 4, 2], 5.3 [0, 1, 4, 6] | 81,8 % (9 de 11), 54,5 % (6 de 11) y 90,9 % (10 de 11) | 5.1 y 5.3 |
| 410 de 450010, `sintetico_20262_450010_410.xlsx` | docente.varias | 2.1 [1, 2, 4, 4], 2.2 [2, 4, 3, 2], 5.1 [3, 4, 3, 1] | 72,7 % (8 de 11), 45,5 % (5 de 11) y 36,4 % (4 de 11) | Ninguno |
| 412 de 450010, `sintetico_20262_450010_412.xlsx` | docente.varias | 2.1 [0, 1, 5, 5], 2.2 [1, 3, 5, 2], 5.1 [2, 3, 3, 3] | 90,9 % (10 de 11), 63,6 % (7 de 11) y 54,5 % (6 de 11) | 2.1 |

Las pruebas arman tres copias de `sintetico_20262_450002_410.xlsx` en `tmp_path`. Sin la nota de 5.3 de la fila 9, 5.3 da 80,0 % (8 de 10) y queda en la meta. Sin la nota de 5.2 de la fila 3, 5.2 da 60,0 % (6 de 10) sobre los calificados y 54,5 % (6 de 11) sobre el total. Sin ninguna nota en 5.3, la carga se publica igual, porque 5.1 y 5.2 traen niveles, y 5.3 queda sin logro y con 0,0 % sobre el total.

Los escenarios viven en `specs/004-reportes-docente/aceptacion/resultados.feature` (US-37, US-39, US-40, US-41, US-43 y US-44) y en `alcance_y_privacidad.feature` (US-38 y US-42), en español (`# language: es`). Sus pasos van en `tests/aceptacion/pasos/test_resultados_feature.py` y `test_alcance_resultados_feature.py` (propuesta), que reutilizan los pasos comunes de `tests/aceptacion/pasos/conftest.py`. Cada escenario lleva `@US-NN`, `@corte1` o `@corte2` y `@spec004`, y los escenarios de la pantalla llevan además `@delegado_a_vitest`, como en la spec 003, porque los prueba Vitest en el Front. Cuando un texto literal de pantalla o de la API difiere, manda el del `.feature`.

## Clarifications

### Session 2026-11-17

- Jefferson pide en el chat, con las palabras del Input, que los profesores suban sus exports y conserven su R-17 como constancia, que vean de forma visual cómo les va frente a los SO y que solo consulten sus secciones, sin subir exports a secciones ajenas.
- Tres partes del pedido ya existen en `develop` con escenarios aprobados. La subida es US-07 (spec 001) y US-26 a US-36 (spec 003), y el R-17 con su hoja «Constancia» es US-15 y US-16. El límite de subida y de lectura lo fijan BR-ACCESO-07 y BR-ACCESO-08 de `specs/features/acceso/acceso.spec.md`, que `app/permisos.py` aplica con un solo 403, «La sección no está a su cargo.». Lo prueban «El profesor no alcanza una sección ajena escribiendo la ruta» (`acceso.feature`), «Un profesor no sube a una sección que no tiene asignada» y «El coordinador no sube en el corte 1» (`carga.feature`) y «El profesor de varias secciones no alcanza una sección que no dicta» (`varias_secciones.feature`). La spec 004 no cambia esas reglas y las extiende a la ruta nueva (US-38).
- La sesión que encarga la spec nombra otras candidatas de la conversación, y la auditoría las decide. La descripción del instrumento de medición en el catálogo del curso, el nombre del profesor en el R-17 (D-12) y la conversión de escalas de rúbrica, ligada a D-30, quedan para después con su decisión abierta. Reportes dentro del sistema frente a Power BI es J-21, que el crítico de arquitectura sostiene a favor del sistema (`revision-historias.md`).
- El corte 2 de la spec 001 (US-18 a US-21 y la pantalla P5 «Cargas») lo implementa otra sesión. La spec 004 no usa P5, y su único escenario del corte 2, «Una carga reemplazada sale del reporte», espera a US-18.

## User Scenarios & Testing *(mandatory)*

### US-37: Ver mis logros por SO en el periodo (Priority: P1)

Como profesor, quiero ver en una pantalla, con barras y cifras escritas, el porcentaje de mis estudiantes que alcanza el nivel esperado en cada PI de mis secciones, agrupado por SO y frente a la meta, para saber cómo me va en los SO que mide mi curso sin abrir cada R-17.

**Why this priority**: es la única parte del pedido que `develop` no tiene. Ninguna ruta entrega cifras por SO o por PI, y el profesor de varias secciones solo las ve si abre un R-17 por sección.

**Independent Test**: con las tres cargas de `docente.varias@example.invalid` publicadas, `GET /api/resultados?periodo=2026-2` responde 200 con 3 secciones y 9 indicadores, 3 en la meta y 6 debajo, con las cifras de la tabla de esta spec, mientras en `develop` e981a31 esa ruta no existe.

**Base**: `abet.v_r17_por_pi` (`carga_id`, `so`, `pi`, `nivel_esperado`, `n_nivel_1` a `n_nivel_4`, `n_esperado_o_superior`, `n_sin_evidencia`, `n_total`, `pct_logro_sobre_calificados`, `pct_logro_sobre_total_con_sin_evidencia`, `meta_logro_pct`, `provisional` y `conjunto_reglas`), unida solo por `carga_id`. Además, `abet.carga` (`estado`, `uq_carga_publicada_por_seccion`); `abet.seccion`, `abet.asignatura` y `abet.plan_medicion` (`pi_id`, `so_id`, `instrumento_id`, `uq_plan_medicion`); `abet.pi` (`codigo`, `numero`, `so_numero`), `abet.so` (`numero`, `descripcion`) y `abet.instrumento` (`nombre`); `app/permisos.secciones_visibles()`; la función pura de la meta que comparten la ruta y `abet_carga/r17.py` (nueva); ruta 12 (nueva); sin migración.
**Pantalla**: P6 Mis logros por SO (nueva), que se abre con «Ver mis logros por SO» (propuesta) desde la cabecera y desde P4.

**Acceptance Scenarios** (`specs/004-reportes-docente/aceptacion/resultados.feature`):

1. **El profesor de varias secciones ve sus logros agrupados por SO.** **Dado** las tres cargas PUBLICADAS de `docente.varias@example.invalid`, **Cuando** pide `GET /api/resultados?periodo=2026-2`, **Entonces** recibe 200 con 3 secciones y 9 indicadores con meta 80,0 e instrumento «Trabajo Integrador». El SO 2 trae 72,7 % y 45,5 % de la 410 de 450010 y 90,9 % y 63,6 % de la 412 de 450010. El SO 5 trae 81,8 %, 54,5 % y 90,9 % de la 412 de 450002 y 36,4 % y 54,5 % en el 5.1 de las dos de 450010. `en_meta` es verdadero en 3 indicadores, y cada sección 412 trae su propio `carga_id`.
2. **Las cifras viajan como números de un decimal.** **Dado** las mismas cargas, **Cuando** se lee el 5.1 de la 412 de 450002, **Entonces** trae `estudiantes_por_nivel` [1, 1, 5, 4], `logrados` 9, `calificados` 11, `pct_sobre_calificados` 81.8 y `meta_pct` 80.0 como números JSON, y `en_meta` verdadero.
3. **El 80,0 % justo queda en la meta.** **Dado** la copia de la 410 sin la nota de 5.3 de la fila 9, **Cuando** `docente410@example.invalid` pide la ruta, **Entonces** 5.3 trae 8 de 10, 80.0 y `en_meta` verdadero, y 5.1 y 5.2 traen 63,6 % y `en_meta` falso.
4. **P6 agrupa los PI por SO y escribe cada cifra** (Vitest). **Dado** la respuesta del escenario 1, **Cuando** el profesor abre P6, **Entonces** ve los grupos «SO 2» y «SO 5» con su descripción y una fila por PI y sección con su texto completo, como «5.1 · Sección 412 de 450002 · 81,8 % (9 de 11) · En la meta» (propuesta). Ve además 3 filas «En la meta» y 6 «Debajo de la meta», y cada barra con `aria-hidden` y la meta marcada con una línea y con texto.
5. **P6 se abre desde P2 y desde P4 sin confundirse con «Ver resultado»** (Vitest). **Dado** `docente410@example.invalid` en P2 con la 410 publicada, **Entonces** la cabecera muestra una sola vez «Ver mis logros por SO», la fila de la 410 conserva «Subir export» y «Ver resultado», P4 ofrece el mismo enlace y P6 vuelve a P2 con «Volver».
6. **P6 ofrece el R-17 de cada sección publicada** (Vitest). **Dado** la 412 de 450002 publicada y las dos de 450010 sin carga, **Entonces** solo la 412 de 450002 ofrece «Descargar R-17 de la sección 412 de 450002» (propuesta), con destino `/api/cargas/{carga_id}/r17.xlsx`.

---

### US-38: El reporte solo muestra mis secciones (Priority: P1)

Como profesor, quiero que el reporte muestre solo mis secciones y que ninguna petición me deje ver la de otro profesor para que el límite de acceso valga también en los resultados.

**Why this priority**: es el límite literal del pedido («Ese debería ser el límite»), y la ruta es nueva, así que su caso del límite tiene que probarse aunque la regla exista. Hoy cada ruta pide la sesión por su cuenta y ninguna prueba recorre las rutas registradas, de modo que una ruta nueva que olvide esa dependencia respondería 200 sin sesión.

**Independent Test**: con las cinco cargas publicadas, `docente.varias@example.invalid` recibe solo sus 3 secciones y `docente411@example.invalid` solo la 411, sin el número ni el `carga_id` de las ajenas, y una prueba que recorre todas las rutas registradas recibe 401 sin cookie en cada ruta que no es pública.

**Base**: `app/permisos.py` (`secciones_visibles` y `_ALCANCE`), `acceso.docente_seccion` (`uq_docente_seccion`, `fk_docente_seccion_seccion`), `acceso.usuario_autorizado` (`activo`, `ck_usuario_autorizado_rol`) y `acceso.sesion` (BR-ACCESO-06); `app/sesion.usuario_actual`; la dependencia de sesión de cada router con datos y su prueba sobre las rutas registradas (nuevas, J-25 y BR-ACCESO-10); ruta 12.
**Pantalla**: P6.

**Acceptance Scenarios** (`specs/004-reportes-docente/aceptacion/alcance_y_privacidad.feature`):

1. **El reporte del profesor de varias secciones no trae las de otros profesores.** **Dado** la 410 y la 411 de 450002 publicadas por sus profesores y las tres de `docente.varias@example.invalid`, **Cuando** él pide la ruta, **Entonces** recibe 200 con sus 3 secciones y ningún dato de la 410 ni de la 411.
2. **Cada profesor de una sección ve solo la suya (esquema).** **Dado** la 410 y la 411 publicadas, **Cuando** la pide `docente410@example.invalid` o `docente411@example.invalid`, **Entonces** cada uno recibe 1 sección, la suya, con el `carga_id` de su carga y sin la otra.
3. **Un `seccion_id` en la consulta no abre otra sección.** **Dado** la 410 publicada, **Cuando** `docente411@example.invalid` pide la ruta con `seccion_id` de la 410, **Entonces** recibe el mismo cuerpo que sin el parámetro, solo con la 411.
4. **El alcance se lee de la base en cada petición.** **Dado** `docente410@example.invalid` con sesión y su 410 en la respuesta, **Cuando** el dueño de la base desechable retira su fila de `acceso.docente_seccion` y él repite la petición con la misma cookie, **Entonces** recibe 200 con 0 secciones.
5. **Sin una sesión vigente no hay resultados (esquema).** **Dado** una petición sin cookie, con la sesión vencida o con el usuario dado de baja, **Cuando** pide la ruta, **Entonces** recibe 401 con «La sesión venció. Ingrese otra vez.» (propuesta) y sin secciones.
6. **Un periodo mal formado responde 422.** **Dado** `docente410@example.invalid` con sesión, **Cuando** pide `?periodo=2026-13`, **Entonces** recibe 422 con «El periodo no tiene la forma AAAA-C.» (propuesta).
7. **Ninguna ruta con datos responde sin sesión.** **Dado** la lista cerrada de rutas públicas (`POST /api/sesion`, `DELETE /api/sesion`, `POST /api/sesion/codigo` cuando exista y `GET /api/openapi.json`), **Cuando** una prueba recorre las rutas registradas sin cookie, **Entonces** cada ruta fuera de la lista responde 401, también la ruta 12, y cada ruta con `seccion_id` o `carga_id` responde 403 con uno de la 410 pedido por `docente411@example.invalid`.
8. **P6 no ofrece subir exports** (Vitest). **Dado** P6 del profesor o del coordinador, **Entonces** no tiene ningún botón «Subir export», que sigue solo en P2.

---

### US-39: Distinguir lo que todavía no tiene resultado (Priority: P1)

Como profesor, quiero que el reporte distinga una sección sin carga publicada, un PI sin calificaciones y un estudiante sin evidencia de un resultado bajo para no leer como fracaso lo que todavía no se mide.

**Why this priority**: la ruta es nueva y define sus estados vacíos. La vista ya deja nulo, y nunca en 0, el logro de un PI sin calificaciones (H80), y una barra de 0 % contradiría esa decisión ante el profesor.

**Independent Test**: con la copia de la 410 sin ninguna nota en 5.3, el indicador 5.3 llega con `pct_sobre_calificados` nulo y `en_meta` nulo, y P6 dice «Sin calificaciones (11 sin evidencia)» (propuesta) sin barra.

**Base**: `abet.carga` (`estado`, `uq_carga_publicada_por_seccion`), `abet.plan_medicion` (`uq_plan_medicion`), `abet.v_r17_por_pi` (el `NULLIF` de `pct_logro_sobre_calificados`, `n_sin_evidencia` y `pct_logro_sobre_total_con_sin_evidencia`); ruta 12 (`estado`, `pi` e `indicadores` de cada sección).
**Pantalla**: P6.

**Acceptance Scenarios** (`specs/004-reportes-docente/aceptacion/resultados.feature`):

1. **Una sección sin carga publicada no trae cifras.** **Dado** solo la 412 de 450002 publicada, **Cuando** `docente.varias@example.invalid` pide la ruta, **Entonces** la 410 y la 412 de 450010 llegan con `estado` «SIN_CARGA», `carga_id` nulo, `pi` [«2.1», «2.2», «5.1»] e indicadores vacíos, y `so` trae los SO 2 y 5.
2. **Una carga rechazada no cuenta como resultado.** **Dado** la copia de la 410 sin la columna del PI 5.2, RECHAZADA con PI_DEL_PLAN_AUSENTE, **Cuando** `docente410@example.invalid` pide la ruta, **Entonces** la 410 llega en «SIN_CARGA» y sin indicadores.
3. **Un PI sin calificaciones no sale como 0 %.** **Dado** la copia de la 410 sin ninguna nota en 5.3, **Cuando** se pide la ruta, **Entonces** 5.3 trae `calificados` 0, `sin_evidencia` 11, `pct_sobre_calificados` nulo, `pct_sobre_total` 0.0 y `en_meta` nulo, y 5.1 y 5.2 traen 63,6 %.
4. **Un estudiante sin evidencia deja dos porcentajes.** **Dado** la copia de la 410 sin la nota de 5.2 de la fila 3, **Cuando** se pide la ruta, **Entonces** 5.2 trae `estudiantes_por_nivel` [1, 3, 3, 3], 60.0 sobre 10 calificados, 54.5 sobre 11 y `en_meta` falso.
5. **Sin secciones en el periodo, la respuesta es una lista vacía y no un error (esquema).** **Dado** un profesor activo sin secciones o `docente410@example.invalid` con `periodo=2026-1`, **Cuando** pide la ruta, **Entonces** recibe 200 con `so` y `secciones` vacíos.
6. **P6 no pinta lo que no se mide** (Vitest). **Entonces** la sección sin carga dice «Sin carga publicada», el 5.3 sin calificaciones dice «Sin calificaciones (11 sin evidencia)» sin ningún «0 %», y el 5.2 dice «60,0 % de los calificados (6 de 10) y 54,5 % del total (6 de 11), 1 sin evidencia» (propuestas).
7. **P6 muestra la espera, el error y la lista vacía** (Vitest). **Entonces** P6 dice «Cargando sus logros…» mientras espera, vuelve a P1 con un 401, dice «El servicio no respondió. Intente de nuevo.» sin respuesta y «No tiene secciones asignadas en este periodo.» con la lista vacía (propuestas).

---

### US-40: Las cifras del reporte son las de mi R-17 (Priority: P1)

Como profesor, quiero que cada cifra del reporte sea la misma del R-17 de esa carga para no ver un número en la pantalla y otro en mi constancia.

**Why this priority**: el R-17 es la constancia que el profesor conserva, y H13 muestra que la misma sección sale en verde en una página del tablero y en rojo en otra. El invariante 1 de ADR-005 del Front exige que cada porcentaje sea el de la vista, y esta historia lo extiende a la ruta 12.

**Independent Test**: en los 9 indicadores de `docente.varias@example.invalid`, el logro es igual a la celda E de su fila del bloque II del R-17 multiplicada por 100 y redondeada a un decimal, y `en_meta` es verdadero si y solo si la celda H trae el texto de logro.

**Base**: `abet.v_r17_por_pi`; `abet_carga/r17.py` (bloque II en las celdas E24 a E26, G24 a G26 y H24 a H26, frecuencias en Q29 a Q31, `_fraccion` y `_plan_de_accion`); la función pura de la meta (nueva); consultas de control Q01 a Q14; `acceso.sesion` y `acceso.intento_fallido`.
**Pantalla**: P6.

**Acceptance Scenarios** (`specs/004-reportes-docente/aceptacion/resultados.feature`):

1. **Los nueve indicadores coinciden con los tres R-17.** **Dado** las tres cargas de `docente.varias@example.invalid`, **Cuando** se comparan la ruta, el R-17 de cada carga y la vista, **Entonces** cada logro es igual a `round(100 × E, 1)` de su fila y a `pct_logro_sobre_calificados`, la meta a `round(100 × G, 1)`, el porcentaje sobre el total a `round(100 × Q, 1)` de su fila de frecuencias, y `en_meta` sigue a la celda H.
2. **Con un estudiante sin evidencia, el segundo porcentaje también coincide con el R-17.** **Dado** la copia de la 410 sin la nota de 5.2 de la fila 3, **Entonces** 5.2 trae 60.0, igual a E25, y 54.5, igual a Q30.
3. **Leer el reporte no escribe en la base.** **Dado** las tres cargas, **Cuando** se pide la ruta cinco veces, **Entonces** `abet.archivo_origen`, `abet.carga`, `abet.medicion`, `abet.rechazo_fila`, `acceso.sesion` y `acceso.intento_fallido` conservan sus filas, y Q01 a Q14 devuelven 0 filas.
4. **Una carga reemplazada sale del reporte** (corte 2, depende de US-18). **Dado** la carga A del export con el 5 en la fila 3 reemplazada por la B de `sintetico_20262_450002_410.xlsx`, **Entonces** la 410 trae el `carga_id` de B con 63,6 %, 63,6 % y 72,7 %, y ninguna cifra de A.

---

### US-41: El reporte dice cuándo sus resultados son provisionales (Priority: P1)

Como profesor, quiero que el reporte lleve la misma marca PROVISIONAL de mi R-17 mientras las reglas de la carrera no estén aprobadas para no usarlo como evidencia oficial.

**Why this priority**: el Principio IV de la constitución exige que lo provisional se vea en toda cifra de medición, y BR-R17-05 lo cumple en el R-17. Con R-2026-BORRADOR toda cifra del piloto es provisional, y la Oficina de Calidad no debe recibir un reporte sin esa marca.

**Independent Test**: con R-2026-BORRADOR, la 410 llega con `provisional` verdadero y `conjunto_reglas_estado` «BORRADOR», y P6 muestra la franja; con el conjunto de prueba R-PRUEBA-APROBADO, llega con `provisional` falso y P6 no la muestra.

**Base**: `abet.v_r17_por_pi` (`provisional`, `conjunto_reglas`, `nivel_esperado` y `meta_logro_pct`), `abet.conjunto_reglas` (`estado`, `ck_conjunto_reglas_aprobado`), `abet.parametro_valor` (`estado`) y Q11; los campos `conjunto_reglas_estado` y `parametros_pendientes` de la constancia (BR-R17-10), por sección; el texto de la franja de `abet_carga/r17.py` (`_franja`).
**Pantalla**: P6.

**Acceptance Scenarios** (`specs/004-reportes-docente/aceptacion/resultados.feature`):

1. **Con R-2026-BORRADOR los resultados son provisionales.** **Dado** la 410 publicada, **Entonces** trae `provisional` verdadero, «R-2026-BORRADOR» en estado «BORRADOR» y CONVERSION_NIVEL_0_1, CORTE_ROJO y TRATO_SIN_EVIDENCIA pendientes.
2. **Con reglas aprobadas los resultados salen sin la marca.** **Dado** solo en la base de pruebas R-PRUEBA-APROBADO, como el caso A03, **Entonces** la 410 trae `provisional` falso y 90,9 % (10 de 11) con nivel esperado 2 y meta 70,0 en los tres PI.
3. **Un conjunto aprobado que no define todos sus parámetros sigue provisional.** **Dado** solo en la base de pruebas un conjunto APROBADO con TRATO_SIN_EVIDENCIA PENDIENTE, el caso que señala Q11, **Entonces** la 410 trae `provisional` verdadero y estado «APROBADO», con las cifras de R-2026-BORRADOR.
4. **P6 escribe la marca provisional de cada sección** (Vitest, esquema). **Entonces** P6 muestra «Resultados provisionales. Las reglas de la carrera (conjunto R-2026-BORRADOR) aún no están aprobadas. No usar como evidencia oficial.» o el texto del conjunto aprobado e incompleto (propuestas), y nada cuando `provisional` es falso.

---

### US-42: El reporte no expone a estudiantes ni a otros usuarios (Priority: P1)

Como profesor, quiero que el reporte me entregue solo conteos, porcentajes y nombres del catálogo, sin códigos ni nombres de estudiantes ni correos, para que ver mis resultados no abra otra vía a datos personales.

**Why this priority**: `abet_app` lee `abet.estudiante`, `abet.medicion` y `abet.archivo_origen`, así que la minimización depende solo del código de la ruta (Principio II). El nombre del archivo puede traer nombres de personas (H106), y la tabla maestra de Power BI ya expone el código de cada estudiante.

**Independent Test**: el cuerpo de la ruta con las tres cargas de `docente.varias@example.invalid` trae solo las claves de la lista cerrada y ningún número de 8 dígitos, ningún «@» ni el texto «Inventado» de los exports.

**Base**: ruta 12 con su lista cerrada de claves (FR-006); `abet.estudiante`, `abet.medicion` y `abet.archivo_origen` (`nombre_archivo` y `sha256`), que la ruta no lee o no devuelve; Q04 y Q15; el filtro de `Cache-Control` de `app/main.py`.
**Pantalla**: P6.

**Acceptance Scenarios** (`specs/004-reportes-docente/aceptacion/alcance_y_privacidad.feature`):

1. **La respuesta trae solo las claves de la lista cerrada.** **Entonces** el cuerpo trae solo `periodo`, `so` y `secciones`, con las claves de FR-006, y ninguna parte trae `subida_por`, `nombre_archivo`, `sha256`, `trato_sin_evidencia` ni `pct_logro_segun_regla`.
2. **La respuesta no trae códigos, nombres ni correos.** **Entonces** el cuerpo no trae ningún número de 8 dígitos, ningún «@» ni «Inventado».
3. **Ninguna respuesta de la ruta queda en una caché (esquema).** **Entonces** las respuestas 200, 401 y 422 de la ruta llevan `Cache-Control: no-store`.
4. **P6 no guarda nada en el navegador** (Vitest). **Entonces** `localStorage` y `sessionStorage` quedan con 0 entradas después de abrir P6.

---

### US-43: Ver cómo se reparten mis estudiantes por nivel (Priority: P2)

Como profesor, quiero ver cuántos de mis estudiantes quedan en cada nivel de 1 a 4 en cada PI para saber si un resultado bajo se explica por el nivel 2 o por el nivel 1.

**Base**: `abet.v_r17_por_pi` (`n_nivel_1` a `n_nivel_4`); ruta 12 (`estudiantes_por_nivel`).
**Pantalla**: P6.

**Acceptance Scenarios** (`specs/004-reportes-docente/aceptacion/resultados.feature`):

1. **El reparto por nivel suma los calificados.** **Dado** la 410 publicada, **Entonces** 5.1 trae [1, 3, 4, 3], 5.2 trae [1, 3, 4, 3] y 5.3 trae [1, 2, 5, 3], cada reparto suma 11 calificados y sus dos últimos valores suman los logrados, 7, 7 y 8.
2. **P6 escribe el reparto por nivel** (Vitest). **Entonces** la barra apilada de 5.3 dice «Nivel 1: 1, Nivel 2: 2, Nivel 3: 5, Nivel 4: 3» (propuesta), con cada tramo en texto.

---

### US-44: El coordinador ve los resultados de todas las secciones de la carrera (Priority: P2)

Como coordinador de la carrera, quiero ver los mismos resultados por SO de todas las secciones de la carrera, sin un orden por resultado, para seguir el periodo sin descargar cada R-17.

**Base**: `_ALCANCE` de `app/permisos.py` con rol COORDINADOR (`abet.catalogo_vigencia` y `abet.plan_estudios`), sin filas en `acceso.docente_seccion`; `abet.v_r17_por_pi`; ruta 12.
**Pantalla**: P6, que el coordinador abre con «Ver los logros por SO de la carrera» (propuesta) desde la cabecera.

**Acceptance Scenarios** (`specs/004-reportes-docente/aceptacion/resultados.feature`):

1. **El coordinador ve las cinco secciones del periodo.** **Dado** las cinco cargas publicadas por sus tres profesores, **Cuando** `coordinacion@example.invalid` pide la ruta, **Entonces** recibe 200 con 5 secciones en el orden 410, 411 y 412 de 450002 y 410 y 412 de 450010, 15 indicadores (11 del SO 5 y 4 del SO 2) y ningún correo.
2. **P6 del coordinador agrupa por asignatura y no ordena por resultado** (Vitest). **Entonces** P6 agrupa las secciones por asignatura, cada una en el orden de su número y nunca por su porcentaje, sin correos ni nombres de profesores.

---

### Edge Cases

- Un PI del plan sin instrumento (`plan_medicion.instrumento_id` nulo, donde la fuente del catálogo trae «-») llega con `instrumento` nulo, y P6 no muestra la línea del instrumento. Ningún dato inventado tiene hoy ese caso, así que lo cubre la prueba unitaria de la ruta.
- Un conjunto de reglas con NIVEL_ESPERADO o META_LOGRO sin DEFINIR deja nulos `logrados`, los dos porcentajes, `meta_pct` y `en_meta`, como la vista. P6 dice «Sin nivel esperado definido» o «Sin meta definida» (propuestas) y nunca una barra.
- Una sección sin plan de medición llega con `pi` vacío y en «SIN_CARGA», y P6 dice «La carrera aún no registra el plan de medición de esta sección», el texto de P2.
- Un segundo archivo que recibe 409 en una sección con carga publicada no crea ninguna carga, así que la ruta sigue mostrando la misma carga PUBLICADA (`uq_carga_publicada_por_seccion`).
- Un reemplazo del corte 2 que ocurre entre dos lecturas de la ruta no deja una sección PUBLICADA sin indicadores, porque la ruta lee las cargas y las cifras en una sola instantánea (FR-004).
- Un PI 5.10 va después del 5.2, porque los indicadores se ordenan por el número del SO y el número del PI, y no por el texto del código.
- Con una segunda versión de catálogo en la base, los indicadores no se duplican, porque el SO, el PI y el instrumento salen del plan de la carga por `pi_id` y `so_id`.
- Dos profesores asignados a la misma sección (codocencia, H36) ven los dos esa sección y sus cifras, porque `uq_docente_seccion` admite varios usuarios por sección.
- La descripción del SO 2 en AMB-2026 termina en coma (`V1_03__cargar_referencia_ambiental.sql:138`). P6 la muestra tal como la trae el catálogo, en BORRADOR, y ningún escenario compara ese texto.
- El primer pedido después de un reposo de Neon tarda más por el arranque en frío, que queda fuera de la medida de SC-005.

## Requirements *(mandatory)*

- **FR-001** La API agrega la ruta 12, `GET /api/resultados?periodo=2026-2` (propuesta, J-23), sin `seccion_id` ni otro identificador, que FastAPI ignora si llega. Sin `periodo`, la ruta usa `PERIODO_VIGENTE`. Un periodo con otra forma que `AAAA-C` responde 422 con «El periodo no tiene la forma AAAA-C.» (propuesta), y un periodo sin secciones del usuario responde 200 con `so` y `secciones` vacíos (BR-PERIODO-01 y BR-PERIODO-04).
- **FR-002** La ruta devuelve solo las secciones que devuelve `app/permisos.secciones_visibles()` para el usuario y el periodo, sin SQL de alcance propio. El profesor recibe las de `acceso.docente_seccion` y el coordinador todas las de la carrera (BR-ACCESO-07). Sin cookie, con la sesión vencida o con el usuario inactivo responde 401 (BR-ACCESO-06).
- **FR-003** Todo router de la API con datos declara la dependencia de sesión en `APIRouter(dependencies=[…])`, y una prueba recorre las rutas registradas en la aplicación. Esa prueba exige 401 sin cookie en cada ruta fuera de la lista cerrada de rutas públicas y 403 con «La sección no está a su cargo.» en cada ruta que recibe un `seccion_id` o un `carga_id` ajeno (BR-ACCESO-10, propuesta, J-25).
- **FR-004** Las cifras salen de `abet.v_r17_por_pi`, filtrada por el `carga_id` de la carga PUBLICADA de cada sección visible, en una sola sentencia o en una transacción `READ ONLY` con `REPEATABLE READ`. La lista de identificadores viaja como `int[]` y contiene solo los que lee la propia base, nunca un valor de la petición.
- **FR-005** El SO, su descripción, el PI y el instrumento salen del plan de la carga por `pi_id` y `so_id`, nunca por un código o un número sueltos. Las secciones van por código de asignatura y número de sección, los indicadores por `so_numero` y `pi.numero` del PI, y `so` trae, por número, cada SO que mide el plan de alguna sección de la respuesta.
- **FR-006** La respuesta trae solo `periodo`, `so` (con `numero` y `descripcion`) y `secciones`. Cada sección trae solo `seccion_id`, `asignatura` (con `codigo` y `nombre`), `numero`, `estado` (PUBLICADA o SIN_CARGA), `carga_id`, `pi`, `conjunto_reglas`, `conjunto_reglas_estado`, `parametros_pendientes`, `provisional` e `indicadores`. Cada indicador trae solo `so`, `pi`, `instrumento`, `nivel_esperado`, `estudiantes_por_nivel`, `logrados`, `calificados`, `sin_evidencia`, `total`, `pct_sobre_calificados`, `pct_sobre_total`, `meta_pct` y `en_meta`, y la ruta arma cada objeto campo por campo, sin `SELECT *` ni copias de filas enteras.
- **FR-007** Los porcentajes y la meta viajan como números JSON con un decimal, los mismos de `ROUND(…, 1)` de la vista, y un nulo de la vista viaja como `null`, nunca como 0. El Back convierte cada `Decimal` antes de responder, y una prueba unitaria fija que 63,6 sale como `63.6` (J-22).
- **FR-008** `en_meta` es verdadero cuando `pct_sobre_calificados` es mayor o igual que `meta_pct`, falso cuando es menor y nulo cuando falta alguno. La decide una función pura de `abet_carga` que usan la ruta y `_plan_de_accion` de `abet_carga/r17.py`, y el Front no compara cifras.
- **FR-009** Una sección sin carga PUBLICADA llega con `estado` «SIN_CARGA», `carga_id` nulo, los PI de su plan en `pi` e `indicadores` vacío, también cuando todas sus cargas están RECHAZADAS.
- **FR-010** Cada sección con carga trae `provisional` de la vista y `conjunto_reglas`, `conjunto_reglas_estado` y `parametros_pendientes` de su conjunto de reglas, con la regla de la constancia (BR-R17-10). Una sección sin carga los trae nulos.
- **FR-011** El Front agrega P6 «Mis logros por SO» (propuesta) en `src/pantallas/MisLogros.tsx`, con la vista `logros` de `src/App.tsx` y la llamada `obtenerResultados` de `src/servicios/api.ts` (propuestas). P6 se abre con «Ver mis logros por SO» desde la cabecera y desde P4 de una carga PUBLICADA, y esa cabecera es la de `App.tsx` si el corte 2 ya trae su barra de navegación o la de P2 si no. Además, el coordinador la abre con «Ver los logros por SO de la carrera», y P6 vuelve a P2 con «Volver» (propuestas). Su estado vive en la pantalla, sin almacén global.
- **FR-012** P6 dibuja cada barra con HTML y Tailwind, con el ancho en `style`, sin biblioteca de gráficos (J-24). Cada fila escribe su PI, su sección, su porcentaje, su fracción y su estado. La barra lleva `aria-hidden` y la meta se marca con una línea y con texto, de modo que ningún estado depende solo del color (WCAG 1.4.1) y el contraste de lo que no es texto llega a 3 a 1 (WCAG 1.4.11).
- **FR-013** P6 escribe con texto lo que no se mide, que es la sección sin carga, el PI sin calificaciones, los estudiantes sin evidencia, el nivel esperado o la meta sin definir, el PI sin instrumento, la sección sin plan y la lista vacía, y nunca dibuja una barra de 0 % para un nulo.
- **FR-014** P6 muestra por sección la franja provisional con el texto que corresponde a `conjunto_reglas_estado`, como `_franja` de `abet_carga/r17.py`, y no muestra ninguna cuando `provisional` es falso.
- **FR-015** P6 ofrece en cada sección PUBLICADA el enlace «Descargar R-17 de la sección N de A» (propuesta) hacia la ruta 7, y ninguno en una sección sin carga.
- **FR-016** P6 no ofrece «Subir export», no muestra correos ni nombres de profesores y no escribe en `localStorage` ni en `sessionStorage`. P2 y P4 siguen sin mostrar porcentajes, como dice hoy `docs/01-arquitectura/frontend.md`.
- **FR-017** Antes de implementar, el Front documenta la ruta 12 en `docs/03-api/contrato.md` (tabla de rutas, sección propia, sección 3.4 con ADR-008 y la cuenta de caminos de OpenAPI de la sección 10, que suma `/api/resultados`), en `docs/specs/api-contracts.md`, en `docs/01-arquitectura/frontend.md` (P6) y en `docs/specs/feature-index.md` (`resultados`). La comprobación de mensajes de la sección 10 suma la carpeta de la spec 004.
- **FR-018** Las reglas viven en la spec viva nueva `specs/features/resultados/resultados.spec.md` (BR-RESULTADOS-NN). `acceso.spec.md` suma BR-ACCESO-10 y la ruta 12 en BR-ACCESO-07 y BR-ACCESO-08, `r17.spec.md` suma un bloque fechado en BR-R17-02 con la misma vista y la misma regla de la meta, y `periodo.spec.md` suma la ruta 12 en BR-PERIODO-01 y BR-PERIODO-04.
- **FR-019** Cada escenario tiene su prueba, con pytest-bdd para la API y Vitest para P6. `REGLAS_DE_COPIA` de `tests/aceptacion/pasos/conftest.py` suma «con la columna X.Y vacía en sus N filas». Las pruebas unitarias de la ruta siembran cargas con `publicar()` y `filas_inventadas()` de `tests/cargas_de_prueba.py`, y nada nuevo entra a `tests/datos_inventados/`.
- **FR-020** La ruta solo lee y usa permisos que `abet_app` ya tiene sobre `abet.v_r17_por_pi`, `abet.so`, `abet.pi`, `abet.instrumento` y `abet.plan_medicion`, así que no hay migración (J-26). Antes de fusionar, una consulta de solo lectura con `has_table_privilege` lo comprueba en la rama `develop` de Neon desde el Windows de Jefferson.
- **FR-021** La prueba de humo con Playwright (`e2e/humo.spec.ts`) suma P6 en la vista previa de `develop`. Después de la subida de la 410, abre P6, compara sus cifras con el R-17 descargado de esa misma carga y comprueba que `docente411@example.invalid` no ve la 410 en su P6.

## Success Criteria *(mandatory)*

- **SC-001** Con las tres cargas de `docente.varias@example.invalid`, la ruta 12 responde los 9 indicadores con las cifras de la tabla de esta spec, 3 en la meta y 6 debajo.
- **SC-002** En las pruebas, ninguna respuesta de la ruta 12 a `docente410@example.invalid`, `docente411@example.invalid` o `docente.varias@example.invalid` trae una sección ajena, y toda ruta que no es pública responde 401 sin cookie.
- **SC-003** El 100 % de los indicadores de las pruebas coincide con el bloque II y las frecuencias de su R-17 en el logro, la meta, el porcentaje sobre el total y `en_meta`.
- **SC-004** Ningún indicador sin calificaciones aparece en P6 como 0 %.
- **SC-005** Con 150 secciones sembradas en la base desechable, la ruta 12 del coordinador responde en menos de 1 s, sin contar el arranque en frío, y el plan de `EXPLAIN` muestra el filtro por `carga_id` por debajo de la agregación de la vista.
- **SC-006** Después de leer el reporte, ninguna tabla de `abet` ni de `acceso` cambia su número de filas y Q01 a Q14 siguen en 0.
- **SC-007** Cada fila de P6 se entiende sin color, y sus pruebas la buscan por rol y por texto.
- **SC-008** En la vista previa de `develop`, P6 muestra las mismas cifras del R-17 de la carga de la 410 que sube la prueba de humo.

## Decisiones abiertas

De la carrera (D). Mientras no se decidan, el sistema aplica el valor provisional y P6 lleva la marca PROVISIONAL del conjunto de reglas.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| D-32 | Cómo se resume un PI medido en varias secciones y un SO a partir de sus PI (H06 y P14) | El reporte no suma secciones ni resume un SO en una cifra, y muestra cada PI de cada sección frente a la meta, agrupado bajo su SO. La propuesta del equipo sería sumar estudiantes por PI y curso (Σx/Σn, PA-04, H73 y H74) y dar el SO en la meta solo si todos sus PI medidos lo están (PA-13) | Coordinación de Ambiental y Oficina de Calidad |
| D-33 | Si el profesor ve el agregado de su curso o de la carrera junto al suyo, y con cuántas secciones como mínimo (N6 y H68) | No lo ve, porque el pedido limita la consulta a sus secciones y, con pocas secciones, el agregado menos la propia revela a las otras | Coordinación de Ambiental |
| D-34 | Descripción del instrumento de medición de cada curso y PI, quién la redacta y con qué campos (N2, con la evidencia y la semana de aplicación) | Sin descripción. La descripción de G17 a I19 del R-17 sigue vacía y editable, y P6 muestra solo el nombre del instrumento | Coordinación de Ambiental |
| D-12 | Nombre del profesor en el R-17 y firma frente a validación en el sistema (spec 001) | Sigue sin nombre, y la constancia muestra el correo de quien sube | Coordinación de Ambiental y Oficina de Calidad |
| D-30 | Escala de las columnas ABET de 100 puntos (spec 003), de la que depende convertir otras escalas, como la de 20 puntos | Sigue sin conversión | Stefanny Montaño o la Oficina de Calidad, con la Coordinación de Ambiental |

De Jefferson (J), con el valor que sostiene el crítico de arquitectura.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| J-21 | Dónde ve el profesor sus resultados | En el sistema, con la ruta 12 y P6. Power BI queda para la coordinación en una spec aparte, después de confirmar las licencias, la región de su inquilino, la conexión hacia Neon y una vista sin códigos de estudiante | Jefferson |
| J-22 | Si los porcentajes viajan por la API | Sí, como número JSON con el decimal de la vista, junto a los conteos y a `en_meta`, que calcula el Back con la función del R-17. ADR-008 del Front cambia la sección 3.4 del contrato | Jefferson |
| J-23 | Forma de la ruta 12 | `GET /api/resultados?periodo=2026-2`, una por usuario y sin `seccion_id` | Jefferson |
| J-24 | Biblioteca de gráficos | Ninguna. Barras en HTML y Tailwind con el ancho en `style` y el texto completo en cada fila | Jefferson |
| J-25 | Guardia de sesión de las rutas | Dependencia de sesión en cada router con datos y prueba que recorre las rutas registradas con la lista cerrada de rutas públicas, en este sprint | Jefferson |
| J-26 | Ampliar `abet.v_r17_por_pi` con `seccion_id`, `pi_id`, `so_id` y `n_calificados` | No en este sprint, para desplegar solo código. Se reabre con la spec de la coordinación o con la descripción del instrumento | Jefferson |
| J-27 | Dónde se guarda la descripción del instrumento, si entra | En `abet.plan_medicion.descripcion_instrumento` (V1_11), por periodo y PI, cargada por el script de datos desde el Windows. Mientras D-34 siga abierta, queda fuera | Jefferson |
| J-28 | Qué ve el coordinador en P6 | Las mismas cifras de todas las secciones, ordenadas por asignatura y sección y agrupadas por asignatura, sin correos ni un orden por resultado. La comparación entre secciones de N9 queda para la spec de la coordinación | Jefferson |

## Fuera de alcance

- El consolidado por PI de varias secciones y una cifra por SO (C-03), que esperan a D-32.
- La comparación entre periodos y el selector de periodo de P6 (C-04), porque los datos solo traen 2026-2 y no hay R-17 históricos cargados.
- El agregado del curso o de la carrera junto al resultado del profesor (C-05), que espera a D-33.
- La descripción del instrumento en el catálogo, en las celdas G17 a I19 del R-17 y en P6 (C-08 y C-12), que esperan a D-34 y a J-27.
- La lista de códigos de los estudiantes debajo del nivel esperado (C-09), que N6 pide como «la lista de estudiantes con apoyo» y que necesita una decisión de privacidad propia antes de los datos reales (D-10).
- Los roles de coordinador de asignatura y de área de N15 (C-11), que exigen un rol nuevo en `ck_usuario_autorizado_rol`.
- El nombre del profesor en el R-17 (C-13), que espera a D-12 y que exige cambiar Q15, porque hoy no vigila una columna `nombre` en `acceso`.
- La conversión de escalas de rúbrica, como 20 puntos en Química o 100 en las columnas ABET (C-14), que es de una spec de la carga y espera a D-30.
- Power BI para la coordinación con seguridad por filas (C-15), con J-21. Mientras el prototipo actual no la tenga, no se comparte con profesores, porque muestra a cualquier usuario la lista y el orden de los docentes (H05).
- La alerta automática de N10, la reunión de mejora de N11 y la comparación entre secciones de N9.
- Ampliar `abet.v_r17_por_pi` (J-26).
- La regla de M24 a M26 del R-17. M24 suma los niveles 1 y 2 y M25 los niveles 3 y 4 de todos los PI, y M26 es M25 / (M24 + M25). Las tres celdas siguen el corte fijo de los rótulos de K24 y K25 de la plantilla y no `nivel_esperado` (`abet_carga/r17.py:302-306`). Coinciden con el bloque II cuando el conjunto de reglas es R-2026-BORRADOR (nivel esperado 3) y se apartan de él con R-PRUEBA-APROBADO (nivel esperado 2), por diseño de la plantilla y no por un defecto del código. Qué deben mostrar con otro nivel esperado lo deciden la Coordinación de Ambiental y la Oficina de Calidad con la plantilla oficial (D-08), y P6 no repite este agregado, cuya regla fija está en el cambio del 2026-11-18 de BR-R17-02, en la spec viva del R-17.
- Una herramienta automática de accesibilidad como axe, que suma una dependencia de desarrollo al Front.
