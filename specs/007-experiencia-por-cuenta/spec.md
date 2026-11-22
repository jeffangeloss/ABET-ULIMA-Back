# Feature Specification: Lo importante para cada cuenta y en cada momento del registro

**Feature Branch**: `docs/007-experiencia-por-cuenta` del Back y del Front (PR a `develop`), con la implementación en `feat/007-experiencia-por-cuenta` después de la aprobación
**Created**: 2026-11-22
**Status**: Borrador pendiente de aprobación de Jefferson. Ninguna historia está construida, y D-46, D-47 y J-43 a J-48 siguen abiertas con el valor que propone la spec
**Input**: «también mejora la UX, creo que todo eso se elabora bajo specs usando gerkin para mostrar lo que es importante para cada cuenta y en cada momento» (Jefferson, 2026-11-22). «en la semana 14 deberíamos capacitar a los profesores, para que en la 15 (máximo 16) hagan sus registros» (Claudia León, secretaria académica de Ingeniería Ambiental, correo del 18-11-2026). «Hay que definir un nombre estándar para la evaluación que el docente crea en Blackboard, porque de eso depende la lectura automática» (Mechelle Prado, correo del 19-11-2026, según la transcripción de las notas de la sesión)

## Épica

> **EP-07. Lo importante para cada cuenta y en cada momento (propuesta).** La versión 0.2.0 deja al profesor subir el export de Blackboard, ver el resultado de la carga y descargar el R-17, y a la coordinación ver las secciones de la carrera, pero las pantallas dicen poco de lo que cada cuenta debe hacer en cada momento. El profesor cuya única carga se rechazó lee «Sin carga» en P2 «Mis secciones», P3 «Subir export» no dice qué nombre de columna lee el sistema, P4 «Resultado de la carga» de una carga rechazada no dice qué corregir en Blackboard y, tras un reemplazo rechazado, P4 afirma que la sección no tiene una carga publicada aunque la anterior sigue vigente. La coordinación entra a una pantalla titulada «Mis secciones» y no ve en ningún lugar cuántas secciones faltan ni a quién recordar el registro. Esta épica cambia esos textos y esas pantallas en dos etapas. La etapa A (US-59 a US-63) cambia el código del Front y se construye justo después de la spec 006 y antes del núcleo de la spec 005. Su mínimo antes del registro del 30-11-2026 son US-60, US-59 y US-61, y US-62 y US-63 entran como extras si caben (FR-016). La etapa B (US-64 a US-66) agrega la ruta 17 `GET /api/avance` y la pantalla P7 «Avance del registro» para la coordinación en la semana 16, si cabe, para que sirva al cierre del registro. La spec no agrega migración, tablas, columnas, restricciones, vistas ni roles, y no duplica lo que hacen o planean las specs 005 y 006.

Convenciones de esta spec. Todos los datos de los escenarios son inventados y siguen las convenciones de las specs 001 y 003 a 006. Las secciones de prueba son la 410 y la 411 de 450002 «Principios de Ingeniería Sostenible», la 412, la 413, la 415 y la 416 de 450010 «Gestión Sostenible de Residuos» y la 414 y la 417 de 450020 «Evaluación del Impacto Ambiental», una asignatura del plan de estudios vigente (V1_03) sin plan de medición en 2026-2, con los profesores `docente410@example.invalid`, `docente411@example.invalid` y `docente.baja@example.invalid` (dado de baja) y el coordinador `coordinacion@example.invalid`. Ningún export nuevo entra a `tests/datos_inventados/`. Lo que el redactor decide sin fuente va marcado «(propuesta)».

Prefijos e identificadores. La épica lleva el prefijo EP y continúa la numeración de las specs 001 a 006 (EP-07). Las historias US continúan desde US-59, porque la spec 006 usa US-55 a US-58. Las decisiones de la carrera siguen desde D-46 y las de Jefferson desde J-43, porque la spec 006 usa D-44, D-45 y J-42. La ruta nueva es la 17 del contrato del Front y la pantalla nueva es P7, dos números que AD-47 de la revisión de la spec 005 nombra para una idea fuera de alcance, la rúbrica de la sección, que recibe otros números cuando entre (J-47). Los requisitos funcionales FR (functional requirement), los criterios de éxito SC (success criterion) y las tareas T se numeran dentro de esta spec, así que una regla viva que cite uno de ellos nombra la spec, como «FR-008 de la spec 007». Las candidatas de la auditoría se llaman C-P01 a C-P06 (profesor), C-C01 a C-C06 (coordinación) y C-T01 a C-T06 (transversales), y su revisión está en `revision-historias.md`.

Siglas y términos. Las de las specs 001 a 006 valen aquí. El indicador de desempeño (performance indicator, PI), el resultado del estudiante (student outcome, SO) y la interfaz de programación de aplicaciones (application programming interface, API) conservan su sentido. La experiencia de uso (user experience, UX) es lo que el pedido de Jefferson llama UX. ARIA son los atributos de accesibilidad para aplicaciones de internet enriquecidas (Accessible Rich Internet Applications), como `aria-describedby` y `aria-current`. La etapa de una sección es su situación en el registro del periodo, que la ruta 17 nombra con SIN_PLAN, SIN_PROFESOR, CON_RECHAZO, SIN_CARGA o PUBLICADA (J-48). Una sección «que falta» es una sección cuya etapa no es PUBLICADA. La línea de lo que falta es el párrafo que P2 agrega bajo el estado de cada sección del profesor.

Los escenarios viven en `specs/007-experiencia-por-cuenta/aceptacion/`, en español (`# language: es`), en cinco archivos. `siguiente_paso.feature` contiene US-59, `antes_de_subir.feature` contiene US-60, `que_corregir.feature` agrupa US-61 y US-62, `rotulos_por_cuenta.feature` contiene US-63 y `avance_del_registro.feature` agrupa US-64, US-65 y US-66. El analizador de pytest-bdd los lee con 35 escenarios y 70 casos. Cada escenario lleva `@US-NN`, `@spec007`, `@corte1` y `@etapa_a` o `@etapa_b` (propuesta), salvo el esquema del menú de US-63, que lleva la etapa en cada bloque de Ejemplos porque su fila de P7 es de la etapa B. Los de pantalla llevan además `@delegado_a_vitest`, porque los prueba Vitest en el Front, y escriben la sesión con «una sesión de "…" con rol "…"», un texto que el paso `_sesion_iniciada` de `tests/aceptacion/pasos/conftest.py` no captura, así que no abren la base (FR-017). Sus pasos van en `tests/aceptacion/pasos/test_experiencia_por_cuenta_feature.py` y `test_avance_feature.py` (propuesta). Cuando un texto literal de pantalla o de la API difiere entre esta spec y un `.feature`, manda el del `.feature`.

## Clarifications

### Session 2026-11-22

- Jefferson pide, con las palabras del Input, mejorar la UX con specs en Gherkin que muestren lo importante para cada cuenta y en cada momento. El calendario de Claudia fija los momentos. La capacitación de los profesores ocurre en la semana 14 (23 al 28-11-2026) y el registro en la semana 15 (30-11 al 5-12) o, a más tardar, en la 16 (7 al 12-12). Lo útil antes del registro es prioritario.
- Las cuentas son las dos de `app/permisos.py`, PROFESOR y COORDINADOR. Los momentos que cubre la spec son la preparación del export en Blackboard, la subida, el rechazo, el reemplazo y el seguimiento del registro por la coordinación. La reunión de mejora, posterior al registro, queda fuera.
- La auditoría revisa 18 candidatas con tres lentes y con el crítico de arquitectura (`revision-historias.md`). Ocho historias sobreviven en dos etapas. C-P04, C-T03 y C-T05 pasan la regla de las specs anteriores, que admite a lo sumo una lente en REFUTADA o MOVER_A_DESPUES, pero el crítico las deja para después por capacidad, porque tocan P4 mientras la spec 005 la reescribe o cambian cuatro pantallas sin un pedido. Quedan en «Fuera de alcance» con sus correcciones, y Jefferson puede subirlas al aprobar la spec.
- El orden del crítico (spec 006, núcleo de la spec 005, etapa A y etapa B) no deja llegar la etapa A antes del registro del 30-11, porque el núcleo de la spec 005 (US-45 a US-49, V1_12, las rutas 13 a 16 y la reescritura de P4) no tiene código. La spec adelanta la etapa A al núcleo de la spec 005, con un mínimo de US-60, US-59 y US-61, y deja la etapa B para la semana 16, si cabe (FR-016).
- La spec no duplica la spec 005. El semáforo, el registro de las oportunidades de mejora (OM) y de las buenas prácticas (BP) por indicador en P4, el R-17 con la declaración, la marca «Declaración pendiente» (C-14 b) y el botón «Subir otro archivo» de US-52 siguen en ella. US-61 y US-62 tocan solo la rama de P4 de una carga que no está PUBLICADA, que la spec 005 no cambia salvo ese botón, y no tocan «Cómo va su sección» ni «Análisis por indicador».
- La spec no duplica la spec 006. La consulta `secciones_sin_docente.sql` de US-58 sigue informando a Jefferson fuera de línea, y la ruta 17 usa la misma condición de sección sin profesor para la coordinación, sin repetirla en otra regla.
- El correo de Mechelle del 19-11 dice que el nombre de la actividad de Blackboard es hoy «ABET-SO-PI», una forma con guiones que el lector no acepta (`_ENCABEZADO_DE_PI` de `abet_carga/lector.py`, spec 005, Clarification sobre D-43). US-60 muestra en P3 la forma de D-43, «ABET SO5.1», y su escenario del Back comprueba que el lector la reconoce y que rechaza la forma con guiones.
- La spec 005 (US-49) deja el R-17 de una carga PUBLICADA en 409 hasta la declaración, cuando se construya. Por eso la línea de US-59 de una carga publicada dice «completar lo que falte y descargar el R-17» y la etapa PUBLICADA de P7 se rotula «Publicada», sin presentarse como sección terminada. La división entre la carga publicada sin declarar y la declarada (C-C06) espera a V1_12 y a US-49.
- Una sección con una carga publicada y sin profesor activo, por ejemplo cuando el profesor se da de baja después de publicar, queda en PUBLICADA, porque su registro está hecho, y cuenta en «N de M secciones con carga publicada» (valor provisional de J-48). La alternativa de J-48 la deja en SIN_PROFESOR con su `carga_id`, para que la coordinación vea que no tiene profesor. En los dos casos, `secciones_sin_docente.sql` de la spec 006 sigue informando esa sección a Jefferson.
- Los botones «Volver a mis secciones» de P3 y P4 y «Volver» de P6 conservan su texto y su destino P2 también para el coordinador, porque los buscan las pruebas de Vitest y ninguna candidata los cambia. El texto choca con el fin de US-63, y `alVolver` de `App.tsx` lleva al coordinador a P2 y no a P7, así que los dos quedan como deuda en «Fuera de alcance». Con la etapa B y US-52 de la spec 005, el botón atrás del navegador sí vuelve de P4 a P7 (US-65).

## User Scenarios & Testing *(mandatory)*

### US-59: P2 dice al profesor lo que falta en cada sección (Priority: P1)

Como profesor, quiero ver en cada sección de P2 lo que falta hacer, para registrar la medición en la semana 15 sin abrir cada pantalla ni volver al material de la capacitación.

**Why this priority**: P2 es la primera pantalla del profesor en cada ingreso de las semanas 15 y 16. Hoy una sección cuya única carga está RECHAZADA dice «Sin carga» y no ofrece «Ver resultado» (`estadoDeCarga()` de `src/pantallas/MisSecciones.tsx` y docstring de `app/rutas/secciones.py`), así que el profesor que vuelve a P2 después de un rechazo cree que no subió nada. La lista vacía tampoco dice a quién acudir si la programación docente de la spec 006 lo deja fuera.

**Independent Test**: con la ruta 4 que da la 410 en SIN_CARGA y la ruta 8 que da una carga RECHAZADA de la 410, P2 conserva «Sin carga», dice debajo «La última carga se rechazó y no se publicó. Falta subir un export corregido.» y ofrece «Ver por qué se rechazó», que abre P4 de esa carga, mientras en `develop` 7aa1f02 del Front la fila dice solo «Sin carga».

**Base**: ninguna tabla nueva. Ruta 4 `GET /api/secciones` (`estado`, `tiene_plan`, `carga_id`, `filas_leidas` y `filas_aceptadas`) y ruta 8 `GET /api/cargas` sin `seccion_id` (`seccion.seccion_id`, `estado` y `carga_id`, de la más reciente a la más antigua por `constancia.resumenes`), sin cambios en el contrato; `app/permisos.py` fija el alcance de las dos.
**Pantalla**: P2 Mis secciones (`src/pantallas/MisSecciones.tsx`), solo para el rol PROFESOR, con una función nueva de `src/servicios/` que combina las rutas 4 y 8 (J-45). La línea va en un párrafo propio bajo el estado, y el botón «Subir export» la anuncia con `aria-describedby`.

**Acceptance Scenarios** (`specs/007-experiencia-por-cuenta/aceptacion/siguiente_paso.feature`, todos `@delegado_a_vitest`):

1. **La línea de lo que falta sale del estado de la sección (esquema).** **Dado** la 410 con o sin plan, en SIN_CARGA o PUBLICADA y con o sin una carga RECHAZADA, **Cuando** el profesor abre P2, **Entonces** la fila conserva su texto de hoy y dice debajo «Falta subir el export de Blackboard de esta sección.», «La última carga se rechazó y no se publicó. Falta subir un export corregido.», «Revise el resultado de la carga para completar lo que falte y descargar el R-17.» o «Por ahora no hay nada que hacer. La Coordinación de la carrera registra el plan de medición.» (propuestas).
2. **El botón anuncia lo que falta y, desactivado, su motivo.** **Entonces** «Subir export» de la sección con plan tiene `aria-describedby` hacia su línea, y el botón desactivado de la sección sin plan lo tiene hacia «La carrera aún no registra el plan de medición de esta sección».
3. **«Ver por qué se rechazó» abre P4 de la carga rechazada más reciente.** **Dado** las cargas 9 y 8 RECHAZADA de la 410, con la 9 primero en la ruta 8, **Cuando** el profesor pulsa «Ver por qué se rechazó» (propuesta), **Entonces** P4 muestra la constancia de la carga 9, y la fila conserva «Subir export» activo.
4. **Si la ruta 8 falla, P2 sigue con la ruta 4.** **Dado** la ruta 8 en 500, **Entonces** la fila dice «Falta subir el export de Blackboard de esta sección.», sin mensaje de error y sin «Ver por qué se rechazó».
5. **Sin secciones, P2 dice a quién acudir.** **Dado** la ruta 4 vacía, **Entonces** P2 conserva «No tiene secciones asignadas en este periodo.», dice debajo «Si dicta una sección con medición ABET en este periodo, escriba a la Coordinación de la carrera.» (propuesta, D-46) y no pide la ruta 8.
6. **La coordinación no recibe las líneas del profesor.** **Dado** una sesión COORDINADOR, **Entonces** ninguna fila dice «Falta subir el export de Blackboard de esta sección.» y P2 no pide la ruta 8.

---

### US-60: P3 dice antes de subir qué debe tener listo el profesor en Blackboard (Priority: P1)

Como profesor, quiero ver en P3 qué columnas y qué notas espera el sistema para mi sección, para preparar Blackboard y subir el export una sola vez.

**Why this priority**: la lectura automática depende del nombre de la actividad de Blackboard (correo de Mechelle del 19-11), el nombre de hoy lleva guiones que el lector no acepta y la revisión de la spec 005 deja fuera el aviso de una columna mal nombrada (C-C04 de la spec 005) confiando en el nombre estándar de D-43. El profesor registra una o dos semanas después de la capacitación, así que recordar en P3 los nombres de columna de su sección evita el rechazo PI_DEL_PLAN_AUSENTE sin tocar el lector.

**Independent Test**: con la 410 y sus PI 5.1, 5.2 y 5.3, P3 muestra antes del campo de archivo el apartado «Antes de subir» con «En Blackboard, una columna por PI, con el nombre ABET SO5.1, ABET SO5.2 y ABET SO5.3.», y el lector clasifica «ABET SO5.1 [Total Pts: 4 Score] |9000051» como columna del PI 5.1, mientras en `develop` 7aa1f02 P3 solo dice «Export de Blackboard (.xlsx, .csv o .xls, hasta 1 MB)».

**Base**: ninguna tabla. Campo `pi` del objeto `Seccion` de la ruta 4, que P3 ya recibe en la prop `seccion` (`src/servicios/tipos.ts`), sin petición nueva; regla `_ENCABEZADO_DE_PI` de `abet_carga/lector.py`, la misma de `ck_carga_columna_encabezado` en V1_10 (J-19), que acepta «ABET SO5.1 [», «ABET PI5.1 [» y «5.1 [» y lee «6.10» como el PI 6.10; D-43 de la spec 005, D-03, D-04 y D-06; `_NOMBRE_DE_BLACKBOARD` de `abet_carga/validacion.py` y la confirmación de US-21.
**Pantalla**: P3 Subir export (`src/pantallas/SubirExport.tsx`), con el apartado «Antes de subir» (propuesta) antes del campo de archivo, armado desde una constante del Front (J-44), también en el modo reemplazo.

**Acceptance Scenarios** (`specs/007-experiencia-por-cuenta/aceptacion/antes_de_subir.feature`, los cuatro primeros `@delegado_a_vitest`):

1. **P3 lista lo que el profesor debe tener listo.** **Cuando** el profesor pulsa «Subir export» en la 410, **Entonces** P3 muestra antes del campo de archivo, en este orden, «En Blackboard, una columna por PI, con el nombre ABET SO5.1, ABET SO5.2 y ABET SO5.3.», «En cada columna, un nivel entero de 1 a 4 por estudiante. El puntaje máximo de la columna es 4, y otro puntaje máximo solo deja un aviso.», «Conserve la columna Username y no cambie el nombre de las columnas.» y «Suba el export completo del Centro de calificaciones sin cambiarle el nombre, porque la hoja o el nombre que le pone Blackboard indican la sección.» (propuestas).
2. **La primera línea nombra los PI de la sección elegida (esquema).** **Dado** una sección con el PI 5.1, o con los PI 6.1 y 6.10, **Entonces** la línea nombra «ABET SO5.1», o «ABET SO6.1 y ABET SO6.10».
3. **El apartado no lee el archivo.** **Cuando** el profesor elige un archivo, **Entonces** el apartado no cambia y P3 no hace ninguna petición hasta «Subir».
4. **El modo reemplazo muestra el mismo apartado.** **Cuando** el profesor abre P3 desde «Reemplazar carga» de P5, **Entonces** ve las mismas cuatro líneas.
5. **El lector reconoce el nombre que propone P3 y no el que lleva guiones (esquema).** **Dado** los encabezados «ABET SO5.1 [Total Pts: 4 Score] |9000051», «ABET SO6.10 [Total Pts: 4 Score] |9000610» y «ABET-SO5-PI5.1 [Total Pts: 4 Score] |9000051», **Cuando** el lector los clasifica, **Entonces** los dos primeros son columnas de los PI 5.1 y 6.10, y el tercero es una columna que no es de un PI.

---

### US-61: P4 de una carga rechazada dice qué corregir (Priority: P1)

Como profesor, quiero que P4 de una carga rechazada me diga qué corregir en Blackboard, para subir un export válido sin adivinar.

**Why this priority**: el rechazo de toda la carga es el tropiezo más probable de la semana 15, porque cualquier nombre de columna distinto de D-43 da PI_DEL_PLAN_AUSENTE. El mensaje de la API dice qué falta («Falta la columna del PI 5.2 que el plan de medición pide para esta sección.», contrato, sección 6), pero no qué hacer en Blackboard.

**Independent Test**: con la carga 8 RECHAZADA por PI_DEL_PLAN_AUSENTE en el PI 5.2, P4 muestra el mensaje de la API sin cambios y debajo «Qué corregir. Revise en Blackboard que cada PI del plan de esta sección tenga su columna, y cree o renombre la del PI 5.2 como ABET SO5.2. Después exporte otra vez y suba el archivo nuevo.», mientras en `develop` 7aa1f02 P4 muestra solo el mensaje.

**Base**: ninguna tabla. Ruta 6 `GET /api/cargas/{carga_id}` (`estado`, `filas_leidas`, `rechazos[].motivo`, `rechazos[].pi`, `rechazos[].efecto`, `seccion` y `mensaje`), sin cambios en el contrato; motivos RECHAZA_CARGA de BR-CARGA-11 a BR-CARGA-13 y BR-CARGA-16 (PI_DEL_PLAN_AUSENTE, PI_REPETIDO, COLUMNA_CODIGO_AUSENTE, ARCHIVO_SIN_FILAS, SIN_CALIFICACIONES, SECCION_NO_COINCIDE y PERIODO_NO_COINCIDE) y la carga sin filas aceptadas (`SIN_FILAS_ACEPTADAS` de `abet_carga/constancia.py`).
**Pantalla**: P4 Resultado de la carga (`src/pantallas/ResultadoCarga.tsx`), con el párrafo «Qué corregir» bajo el mensaje de la API, desde una tabla del Front por motivo en `src/servicios/` (J-43). El coordinador que abre la carga ve el mismo texto, salvo en SECCION_NO_COINCIDE, donde el consejo lo remite al profesor de la sección, porque `permisos.puede_subir()` no le deja una carga nueva.

**Acceptance Scenarios** (`specs/007-experiencia-por-cuenta/aceptacion/que_corregir.feature`, todos `@delegado_a_vitest`):

1. **Cada motivo trae su forma de corregir (esquema).** **Dado** la carga 8 RECHAZADA con un RECHAZA_CARGA de cada uno de los siete motivos, **Entonces** P4 muestra el mensaje de la API sin cambios, debajo «Qué corregir. …» con el texto de su fila de Ejemplos (propuesta, J-43) y conserva «0 filas leídas, 0 aceptadas y 0 rechazadas». El consejo de SECCION_NO_COINCIDE nombra «450002, sección 410» de la constancia, sin remitir a una pantalla, y el de PERIODO_NO_COINCIDE nombra «2026-2». El coordinador lee en SECCION_NO_COINCIDE «El archivo no es de 450002, sección 410. Pida al profesor de esa sección que exporte su Centro de calificaciones y lo suba otra vez.» (propuesta).
2. **Si ninguna fila se acepta, P4 remite a la tabla de rechazos.** **Dado** 11 filas rechazadas por NIVEL_FUERA_DE_ESCALA y ningún RECHAZA_CARGA, **Entonces** P4 conserva «11 filas leídas, 0 aceptadas y 11 rechazadas» y dice «Qué corregir. Corrija en Blackboard cada fila de la tabla de rechazos, exporte otra vez y suba el archivo nuevo.» (propuesta).
3. **Un motivo desconocido no muestra consejo.** **Dado** el motivo «MOTIVO_NUEVO», **Entonces** P4 muestra solo el mensaje de la API y ningún texto que empieza con «Qué corregir».
4. **Una carga publicada no muestra «Qué corregir».** **Dado** la carga 7 PUBLICADA con una fila rechazada, **Entonces** P4 no muestra ningún texto que empieza con «Qué corregir».

---

### US-62: P4 y P3 no afirman nada falso sobre la carga publicada (Priority: P1)

Como profesor, quiero que un reemplazo rechazado no me diga que la sección quedó sin carga publicada, para no creer que perdí el R-17 en plena semana 15 o 16.

**Why this priority**: P4 escribe «No hay una carga publicada para esta sección» en toda carga que no está PUBLICADA ni REEMPLAZADA con sucesora (`ResultadoCarga.tsx`, línea 97). Tras un reemplazo rechazado el texto es falso, porque la carga anterior sigue PUBLICADA y la nueva trae `reemplaza_carga_id` nulo (BR-CARGA-19). El reemplazo es el camino que el profesor sigue durante el registro.

**Independent Test**: con la carga 12 RECHAZADA que devuelve la ruta 9 con `reemplaza` 7, P4 dice «Esta carga no tiene R-17.» y no «No hay una carga publicada para esta sección», mientras en `develop` 7aa1f02 dice lo segundo.

**Base**: ninguna tabla. Ruta 6 (`estado`, `reemplaza_carga_id` y `reemplazada_por`) y ruta 9 `POST /api/secciones/{seccion_id}/cargas?reemplaza={carga_id}`, con el 201 RECHAZADA que deja la anterior PUBLICADA (`uq_carga_reemplaza` y `uq_carga_publicada_por_seccion`), sin cambios.
**Pantalla**: P4 (`src/pantallas/ResultadoCarga.tsx`), en el párrafo final de una carga que no está PUBLICADA, y P3 en modo reemplazo (`src/pantallas/SubirExport.tsx`), con una frase en un párrafo propio. P4 no pide la ruta 4, así que no nombra la carga que sigue publicada (Fuera de alcance).

**Acceptance Scenarios** (`specs/007-experiencia-por-cuenta/aceptacion/que_corregir.feature`, todos `@delegado_a_vitest`):

1. **Una carga sin R-17 lo dice sin afirmar nada sobre la sección (esquema).** **Dado** la carga 12 RECHAZADA, EN_CURSO o REEMPLAZADA sin sucesora conocida, **Entonces** P4 dice «Esta carga no tiene R-17.» (propuesta), no dice «No hay una carga publicada para esta sección» y no ofrece «Descargar R-17».
2. **Un reemplazo rechazado no dice que la sección quedó sin carga publicada.** **Dado** la carga 7 PUBLICADA y la ruta 9 con `reemplaza` 7 que da la carga 12 RECHAZADA, **Cuando** P3 pasa a P4, **Entonces** P4 dice «Esta carga no tiene R-17.».
3. **Una carga reemplazada con sucesora conocida conserva su texto.** **Dado** la carga 7 REEMPLAZADA con `reemplazada_por` 11, **Entonces** P4 dice «La carga 11 la reemplaza, así que esta carga no tiene R-17.».
4. **P3 en modo reemplazo dice que la carga publicada no se pierde.** **Cuando** el profesor abre P3 desde «Reemplazar carga» de la carga 7, **Entonces** P3 conserva «Reemplaza a la carga 7, la publicada de esta sección.» y dice en un párrafo propio «Si la carga nueva queda rechazada, la carga 7 sigue publicada.» (propuesta).

---

### US-63: Cada cuenta lee rótulos de su rol y sabe en qué pantalla está (Priority: P2)

Como coordinación de la carrera, quiero leer rótulos que hablan de la carrera y no de secciones propias, para que la capacitación de la semana 14 y el seguimiento del registro no muestren textos de otra cuenta.

**Why this priority**: `src/App.tsx` titula P2 y su botón «Mis secciones» para las dos cuentas, y P2, P5 y P6 dicen «No tiene secciones asignadas en este periodo.» también al coordinador. Solo el enlace a P6 cambia hoy según el rol (`rotuloDeLogros()`). El cambio es pequeño y toca las mismas líneas de la cabecera que el menú con `aria-current`, que `frontend.md` (sección 7, punto 3) deja como deuda.

**Independent Test**: con una sesión COORDINADOR, la cabecera dice «Secciones de la carrera», «Cargas» y «Ver los logros por SO de la carrera», P2 se titula «Secciones de la carrera» y la cabecera es un nav con `aria-current="page"` en el botón de la pantalla actual, mientras en `develop` 7aa1f02 dice «Mis secciones» y no es un nav.

**Base**: ninguna. El rol sale de la ruta 2 `GET /api/sesion` (`Usuario.rol`).
**Pantalla**: cabecera de `src/App.tsx`, P2 (`MisSecciones.tsx`), P5 (`Cargas.tsx`) y P6 (`MisLogros.tsx`). Los textos del profesor no cambian.

**Acceptance Scenarios** (`specs/007-experiencia-por-cuenta/aceptacion/rotulos_por_cuenta.feature`, todos `@delegado_a_vitest`):

1. **La cabecera nombra lo que ve cada cuenta (esquema).** **Entonces** el profesor ve «Mis secciones», «Cargas» y «Ver mis logros por SO», y el coordinador «Secciones de la carrera», «Cargas» y «Ver los logros por SO de la carrera», y P2 lleva el mismo título que su botón.
2. **Una lista vacía se explica según la cuenta (esquema).** **Entonces** P2, P5 y P6 dicen al profesor «No tiene secciones asignadas en este periodo.» y al coordinador «La carrera no tiene secciones en este periodo.» (propuesta).
3. **El aviso de espera de P6 habla de la cuenta (esquema).** **Entonces** P6 dice al profesor «Cargando sus logros…» y al coordinador «Cargando los logros de la carrera…» (propuesta).
4. **El menú marca la pantalla actual (esquema).** **Entonces** la cabecera es un nav con aria-label «Menú principal» (propuesta), solo el botón de P2, P5 o P6 lleva `aria-current="page"` cuando esa pantalla está a la vista, también «Secciones de la carrera» del coordinador en P2 y, desde la etapa B, «Avance del registro» en P7, y ningún botón lo lleva en P3 ni en P4.

---

### US-64: La ruta 17 da a la coordinación la etapa de cada sección (Priority: P1)

Como coordinación de la carrera, quiero saber la etapa de cada sección del periodo y cuántas hay en cada una, para saber durante las semanas 15 y 16 cuántas faltan y cuáles piden una acción de la Coordinación.

**Why this priority**: Claudia fija el registro en la semana 15, con la 16 como máximo (correo del 18-11). La ruta 4 da SIN_CARGA también a la sección con todas sus cargas RECHAZADA y no ve la sección sin profesor activo, que US-58 de la spec 006 informa solo a Jefferson fuera de línea. Ninguna de esas dos etapas sale de la ruta 4, así que la necesidad pide el dato del Back.

**Independent Test**: con las cinco secciones de los Antecedentes, `GET /api/avance?periodo=2026-2` del coordinador responde 200 con las etapas PUBLICADA, CON_RECHAZO, SIN_CARGA, SIN_PROFESOR y SIN_PLAN en el orden de asignatura y número, y el profesor recibe 403, mientras en `develop` ec33606 la ruta no existe.

**Base**: `abet.seccion`, `abet.plan_medicion`, `abet.carga` (`estado`), `acceso.docente_seccion` y `acceso.usuario_autorizado` (`rol` y `activo`), solo lectura, que `abet_app` ya lee según `crear_rol_app.sql`; `app/permisos.secciones_visibles()` con rol COORDINADOR y una función nueva `puede_ver_avance()` en `app/permisos.py` (propuesta); ruta nueva `app/rutas/avance.py` con su consulta en `abet_carga/avance.py` (propuestas, J-47 y J-48); sin migración.
**Pantalla**: ninguna en esta historia. P7 es de US-65.

**Acceptance Scenarios** (`specs/007-experiencia-por-cuenta/aceptacion/avance_del_registro.feature`):

1. **La ruta da la etapa de cada sección en el orden de asignatura y número.** **Cuando** el coordinador pide la ruta 17, **Entonces** recibe 200 con `Cache-Control: no-store`, la 410 PUBLICADA con su `carga_id`, la 411 CON_RECHAZO, la 412 SIN_CARGA, la 413 SIN_PROFESOR y la 414 SIN_PLAN, el conteo 5, 1, 1, 1, 1 y 1, y ningún porcentaje de logro, nivel ni dato de estudiantes.
2. **La precedencia de J-48 decide la etapa de cada sección (esquema).** **Dado** la 417 de 450020 sin plan y sin profesor, o la 415 con un profesor dado de baja, asignada solo al coordinador, con una carga PUBLICADA y su único profesor dado de baja después, con una carga EN_CURSO, con una RECHAZADA y después una PUBLICADA, o con una REEMPLAZADA y su sucesora PUBLICADA, **Entonces** trae SIN_PLAN, SIN_PROFESOR, SIN_PROFESOR, PUBLICADA, SIN_CARGA, PUBLICADA y PUBLICADA.
3. **Solo la coordinación lee el avance, en el orden 401, 403 y 422.** **Entonces** el profesor recibe 403 con «Esta página es de la Coordinación.» (propuesta), también con el periodo «2026», la ruta sin sesión responde 401 y el coordinador con el periodo «2026» recibe 422 con «El periodo no tiene la forma AAAA-C.».
4. **Sin periodo, la ruta usa el periodo vigente.** **Dado** `PERIODO_VIGENTE` «2026-2», **Entonces** la ruta sin periodo responde las mismas 5 secciones.

---

### US-65: La coordinación entra a P7 y ve cuántas secciones faltan (Priority: P1)

Como coordinación de la carrera, quiero entrar a una página que diga cuántas secciones tienen su carga publicada, en qué etapa está cada una y cuáles faltan, para seguir el registro sin abrir sección por sección.

**Why this priority**: la ruta 17 sirve solo si la coordinación llega a ella al ingresar. Hoy `App.tsx` abre P2 para las dos cuentas, y ninguna pantalla cuenta el avance.

**Independent Test**: con la respuesta del primer escenario de US-64, el coordinador ingresa, llega a P7 «Avance del registro» y ve «1 de 5 secciones con carga publicada.», y el filtro «Mostrar solo las secciones que faltan» deja la 411 a la 414, mientras en `develop` 7aa1f02 llega a P2.

**Base**: ruta 17 de US-64. Ruta 2 para el rol.
**Pantalla**: P7 Avance del registro (`src/pantallas/Avance.tsx`, nueva, propuesta), solo para el rol COORDINADOR, con la vista «avance» y el fragmento `#/avance` (propuesta) en `src/App.tsx`, el tipo en `src/servicios/tipos.ts`, la función de `src/servicios/api.ts` y el botón «Avance del registro» en la cabecera, antes de «Secciones de la carrera». Las filas van agrupadas por asignatura en el orden de la API (J-28 de la spec 004, sin orden por resultado), y cada etapa lleva texto además de cualquier color. «Ver la carga» abre P4, el único lugar del R-17 según J-32 de la spec 005.

**Acceptance Scenarios** (`specs/007-experiencia-por-cuenta/aceptacion/avance_del_registro.feature`, todos `@delegado_a_vitest`):

1. **P7 muestra el avance con texto, agrupado por asignatura.** **Entonces** P7 dice con `role="status"` «1 de 5 secciones con carga publicada.», dice «1 sección sin plan de medición, en la que su profesor no puede subir el export.», muestra «410 · Publicada», «411 · La última carga se rechazó», «412 · Sin carga», «413 · Sin profesor asignado» y «414 · Sin plan de medición» bajo su asignatura (propuestas) y ofrece en la 410 «Ver la carga», que abre P4.
2. **El filtro deja solo las secciones que faltan.** **Cuando** la coordinación marca «Mostrar solo las secciones que faltan» (propuesta), **Entonces** ve la 411 a la 414 en el mismo orden, el resumen no cambia y el navegador no guarda nada.
3. **Cada cuenta entra a su página (esquema).** **Entonces** el profesor llega a «Mis secciones» sin el botón «Avance del registro», y el coordinador llega a «Avance del registro», con ese botón antes de «Secciones de la carrera».
4. **Atrás desde P4 abierta con «Ver la carga» vuelve a P7.** **Dado** la navegación por fragmento de US-52 de la spec 005, **Cuando** la coordinación pulsa «Ver la carga» en la 410 y después el botón atrás del navegador, **Entonces** la dirección termina en `#/avance`, P7 vuelve a pedir la ruta 17 y una recarga en `#/avance` la deja en P7.
5. **P7 sin secciones lo dice con el texto de la carrera.** **Dado** la ruta 17 sin secciones, **Entonces** P7 dice «La carrera no tiene secciones en este periodo.» y no muestra el resumen ni el filtro.

---

### US-66: P7 dice a quién recordar el registro (Priority: P1)

Como coordinación de la carrera, quiero ver el correo del profesor activo de cada sección que falta y copiar esos correos sin repetirlos, para recordarles el registro desde el correo institucional durante las semanas 15 y 16.

**Why this priority**: recordar el registro a quien falta es la acción que sigue al avance en las semanas 15 y 16. Hoy ninguna ruta entrega al coordinador el profesor de una sección sin carga, porque P5 muestra `subida_por` solo de una carga ya subida. La historia espera a D-47, y si la Coordinación responde que no, sale sin tocar US-64 ni US-65.

**Independent Test**: con la 416 asignada a `docente411@example.invalid` y a un profesor dado de baja, la ruta 17 trae en la 416 solo `["docente411@example.invalid"]`, y P7 copia «docente410@example.invalid; docente411@example.invalid», mientras en `develop` ec33606 no hay ruta.

**Base**: `acceso.usuario_autorizado` (`correo`, `rol` y `activo`) y `acceso.docente_seccion`, solo lectura, sin nombres ni datos de `acceso.credencial`; campo `profesores` de la ruta 17.
**Pantalla**: P7, con el correo en la fila de cada sección CON_RECHAZO o SIN_CARGA y el botón «Copiar los correos de los profesores que faltan» (propuesta), con `navigator.clipboard.writeText` y un cuadro de solo lectura si el navegador rechaza el portapapeles. La aplicación no envía correos y no guarda la lista en el navegador.

**Acceptance Scenarios** (`specs/007-experiencia-por-cuenta/aceptacion/avance_del_registro.feature`):

1. **La ruta trae solo los correos de los profesores activos de las secciones que faltan.** **Entonces** la 411 trae `["docente411@example.invalid"]`, la 412 `["docente410@example.invalid"]`, la 416 `["docente411@example.invalid"]` sin el dado de baja, y la 410, la 413 y la 414 traen `[]`, sin nombres, contraseñas ni datos de `acceso.credencial`.
2. **P7 muestra los correos y los copia sin repetirlos** (`@delegado_a_vitest`). **Cuando** la coordinación pulsa el botón, **Entonces** las filas de la 411, la 412 y la 416 muestran su correo, la 410 no muestra ninguno, el portapapeles recibe «docente410@example.invalid; docente411@example.invalid», en orden alfabético y separados por «; », y P7 dice «Se copiaron 2 correos.» (propuesta).
3. **Sin portapapeles, los correos quedan seleccionables** (`@delegado_a_vitest`). **Dado** un navegador que rechaza el portapapeles, **Entonces** P7 muestra los mismos correos en un cuadro de texto de solo lectura y seleccionado, y el navegador no guarda nada.

---

### Edge Cases

- Una sección SIN_CARGA para la ruta 4 sin ninguna carga RECHAZADA en la ruta 8, pero con una EN_CURSO, recibe «Falta subir el export de Blackboard de esta sección.», porque ningún otro lector ve una carga EN_CURSO (`abet_carga/carga.py` la cierra en la misma transacción).
- Una sección sin plan con cargas RECHAZADA de antes de perder el plan recibe la línea de la sección sin plan, porque el botón «Subir export» sigue desactivado (BR-PERIODO-04).
- Un PI con más de un dígito tras el punto, como 6.10, conserva su número completo en P3 y en «Qué corregir», porque el lector lee «6.10 [» como el PI 6.10.
- Un rechazo RECHAZA_CARGA con `pi` nulo en PI_DEL_PLAN_AUSENTE o PI_REPETIDO, que el contrato no prevé, no muestra consejo, como un motivo desconocido.
- Un coordinador inactivo no ve nada en la ruta 17, porque `secciones_visibles()` exige `activo`, y recibe el 401 de la sesión o el 403 de `puede_ver_avance()`.
- Un usuario COORDINADOR asignado en `acceso.docente_seccion` no cuenta como profesor de esa sección, porque `_ALCANCE` da `acceso.docente_seccion` solo al rol PROFESOR (BR-ACCESO-08 y US-56 de la spec 006). Un mismo correo no tiene los dos roles, porque `acceso.usuario_autorizado` guarda un solo rol por correo (`uq_usuario_autorizado_correo` y `ck_usuario_autorizado_rol`).
- Un correo que aparece en varias secciones que faltan se copia una sola vez, y un profesor con una sección publicada y otra sin carga entra al recordatorio por la segunda.
- Una sección con una carga publicada y sin profesor activo queda en PUBLICADA, trae su `carga_id` y cuenta en «N de M secciones con carga publicada» (valor provisional de J-48).
- Con una sola sección en una etapa, P7 usa el singular, como «1 de 1 sección con carga publicada.» y «1 sección sin plan de medición, en la que su profesor no puede subir el export.», y sin secciones SIN_PLAN no muestra esa línea (propuesta).
- La ruta 17 sigue el orden de `secciones_visibles()`, por código de asignatura y número de sección como texto, el mismo de la ruta 4.

## Requirements *(mandatory)*

- **FR-001** La spec se construye en dos etapas. La etapa A (US-59 a US-63) cambia solo el código del Front, sin rutas ni contrato nuevos, y suma en el Back solo el paso del esquema del lector de US-60 (T030), sin cambiar código del Back. La etapa B (US-64 a US-66) agrega la ruta 17, la pantalla P7 y la entrada del coordinador a P7. US-66 espera a D-47.
- **FR-002** P2 del profesor combina la ruta 4 y una sola petición a la ruta 8 sin `seccion_id` en una función de `src/servicios/` (J-45). Una sección es «con la última carga rechazada» cuando la ruta 4 la da en SIN_CARGA y la ruta 8 trae al menos una carga RECHAZADA suya, y «Ver por qué se rechazó» abre la primera de esas cargas en el orden de la ruta 8. P2 no pide la ruta 8 al coordinador ni con la lista vacía, y una falla de la ruta 8 deja P2 como si no hubiera cargas rechazadas, sin mensaje.
- **FR-003** Los textos de hoy que citan los `.feature` de las specs 001, 003 y 004 no cambian, entre ellos «Sin carga», «Publicada, N de M filas aceptadas», «La carrera aún no registra el plan de medición de esta sección», «No tiene secciones asignadas en este periodo.», «Cargando sus logros…», «PI del plan: 5.1, 5.2, 5.3» y «Reemplaza a la carga 7, la publicada de esta sección.». Cada texto nuevo va en un elemento propio.
- **FR-004** Las líneas de «Antes de subir» viven en una constante del Front (J-44) que sigue el valor provisional de D-43, se arman solo con `Seccion.pi` y une los nombres con comas y «y». P3 no hace ninguna petición nueva.
- **FR-005** El texto «Qué corregir» vive en una tabla del Front por motivo RECHAZA_CARGA, en `src/servicios/` (J-43), con un caso para la carga sin filas aceptadas. Un motivo desconocido no muestra consejo. Una prueba de Vitest recorre los siete motivos RECHAZA_CARGA de la sección 6 del contrato y exige un consejo para cada uno, de modo que un motivo nuevo del contrato rompe la prueba hasta que tenga su texto.
- **FR-006** P4 reemplaza «No hay una carga publicada para esta sección» por «Esta carga no tiene R-17.» (propuesta) en toda carga que no está PUBLICADA ni REEMPLAZADA con sucesora conocida. Cambian `ResultadoCarga.test.tsx` (líneas 91, 178 y 184) y `App.test.tsx` (línea 217). P3 suma en modo reemplazo el párrafo «Si la carga nueva queda rechazada, la carga N sigue publicada.» (propuesta).
- **FR-007** La cabecera de `App.tsx` es un nav con aria-label «Menú principal» (propuesta) y `aria-current="page"` en el botón de P2, P5, P6 o P7 cuando esa pantalla está a la vista. Para el COORDINADOR, el botón y el título de P2 dicen «Secciones de la carrera», la lista vacía de P2, P5, P6 y P7 dice «La carrera no tiene secciones en este periodo.» y la espera de P6 dice «Cargando los logros de la carrera…» (propuestas).
- **FR-008** La ruta 17 `GET /api/avance?periodo=2026-2` exige la sesión, responde en el orden 401, 403 y 422, admite solo a un usuario activo con rol COORDINADOR por `puede_ver_avance()` de `app/permisos.py`, con el 403 «Esta página es de la Coordinación.» (propuesta), valida el periodo como la ruta 4, con el 422 «El periodo no tiene la forma AAAA-C.», y usa `PERIODO_VIGENTE` sin periodo. Su alcance sale de `secciones_visibles()`, lleva `Cache-Control: no-store` como toda `/api` y entra en la prueba que recorre las rutas registradas (`tests/rutas_registradas.py`, FR-003 de la spec 004).
- **FR-009** La ruta 17 responde `periodo`, `conteo` (`secciones` y una cifra por etapa) y `secciones`, cada una con `seccion_id`, `asignatura` (`codigo` y `nombre`), `numero`, `etapa` y `carga_id` de su carga PUBLICADA o `null`. El campo `profesores` (US-66) depende de D-47 y no existe si la Coordinación responde que no. La etapa se deriva en cada lectura con la precedencia de J-48 en una sola consulta del Back y no se guarda en ninguna tabla.
- **FR-010** La ruta 17 no trae porcentajes, niveles, cifras del R-17, códigos ni nombres de estudiantes, nombres de profesores ni datos de `acceso.credencial`. `profesores` trae, en orden alfabético, los correos de los usuarios activos con rol PROFESOR de `acceso.docente_seccion` solo en las secciones CON_RECHAZO y SIN_CARGA, y `[]` en las demás (D-47).
- **FR-011** P7 vive en `src/pantallas/Avance.tsx` con la vista «avance» de `App.tsx` y el fragmento `#/avance` (propuesta), que la tabla de la sección 10.3 de `frontend.md` recibe cuando entre US-52 de la spec 005. Una función `pantallaDeLlegada(usuario)` de `App.tsx` lleva al COORDINADOR a P7 y al PROFESOR a P2 al ingresar y al salir de un 401 (J-46), y US-52 la reutiliza para el fragmento vacío o desconocido, lo que enmienda su regla de llevar todo fragmento desconocido a P2. Con US-52, atrás desde P4 abierta con «Ver la carga» vuelve a P7, y una recarga en `#/avance` deja al coordinador en P7.
- **FR-012** P7 y P2 guardan el filtro y la lista de correos solo en el estado de React, sin `localStorage` ni `sessionStorage`, como exige `frontend.md`. La copia usa `navigator.clipboard.writeText` y, si el navegador la rechaza, un cuadro de texto de solo lectura y seleccionado.
- **FR-013** `frontend.md` fija que los correos de P7 son una regla distinta de la de P6 (sección 9.2), que no muestra correos de profesores, y que solo la cuenta COORDINADOR los recibe.
- **FR-014** La etapa A no agrega reglas `BR-`, porque cambia textos del Front, y sus textos quedan en `frontend.md`. La etapa B abre la spec viva `avance` con BR-AVANCE-01 a BR-AVANCE-NN (propuesta) y suma BR-ACCESO-12 «Lectura del avance solo para la coordinación» (propuesta) en `acceso`, antes de escribir código.
- **FR-015** La spec no agrega migración, no cambia `crear_rol_app.sql` ni las consultas Q01 a Q15, no toca las secciones «Cómo va su sección» ni «Análisis por indicador» de P4 de la spec 005 y no cambia la ruta 4 ni la ruta 8.
- **FR-016** La construcción ajusta el orden del crítico a la spec 006, la etapa A, el núcleo de la spec 005 y la etapa B, porque el núcleo de la spec 005 no tiene código y no cabe antes del registro del 30-11-2026. La etapa A se construye justo después de la spec 006, con un mínimo para antes del 30-11 de US-60, US-59 y US-61, en ese orden, y con US-62 y US-63 como extras si caben. US-59, US-60 y US-63 no tocan `ResultadoCarga.tsx`. US-61 y US-62 cambian solo la rama de P4 de una carga que no está PUBLICADA y entran sobre `develop` si la primera etapa de J-41 de la spec 005 no está fusionada, para reconciliarse al fusionarla. La etapa B va en la semana 16, si cabe.
- **FR-017** Cada escenario `@delegado_a_vitest` tiene su prueba de Vitest en el Front, y su paso del Back registra la propiedad «delegado_a_vitest» con el nombre de esa prueba, como `tests/aceptacion/pasos/test_resultados_feature.py`. Esos escenarios escriben la sesión con «una sesión de "…" con rol "…"», que el paso `_sesion_iniciada` de `conftest.py` no captura, y su paso de sesión solo llama a `_delegar()`, sin abrir la base. Los escenarios del Back corren con pytest-bdd en el clúster desechable de `tests/cluster_desechable.py`, nunca en localhost:5432, y el esquema del lector de US-60, en un archivo sin Antecedentes, corre sin base.

## Success Criteria *(mandatory)*

- **SC-001** Los 35 escenarios y 70 casos de los cinco `.feature` tienen su prueba, en pytest-bdd o en Vitest, y pasan.
- **SC-002** Ningún texto que citan los `.feature` de las specs 001 a 006 cambia, y las pruebas de Vitest que cambian son solo las que nombra FR-006, las de los rótulos del coordinador y, en la etapa B, las de `App.test.tsx` que esperan el título «Mis secciones» después del ingreso del coordinador (J-46).
- **SC-003** Con la ruta 8 en 500, P2 del profesor muestra las mismas secciones y botones que con la ruta 8 vacía.
- **SC-004** Ningún escenario de la ruta 17 entrega un correo de profesor a una cuenta PROFESOR, y P7 deja `localStorage` y `sessionStorage` con 0 entradas.
- **SC-005** Con 60 secciones inventadas en el clúster desechable, la ruta 17 responde en menos de 1 s (propuesta).
- **SC-006** La prueba de humo con Playwright recorre P2 y P3 del profesor con la línea de lo que falta y el apartado «Antes de subir» y, desde la etapa B, la llegada del coordinador a P7.
- **SC-007** `bash scripts/preflight.sh` del Back y del Front sigue sin fallas, y ningún dato real ni ninguna credencial entra a git.

## Decisiones abiertas

De la carrera (D). Mientras no se decidan, el sistema aplica el valor provisional.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| D-46 | A quién remite P2 al profesor sin secciones | «la Coordinación de la carrera», para un caso poco frecuente desde que la spec 006 carga la programación docente | Coordinación de Ambiental |
| D-47 | Si la coordinación ve en P7 el correo del profesor de cada sección que falta | Sí, solo la cuenta COORDINADOR, en las secciones CON_RECHAZO y SIN_CARGA, sin nombres y sin envío desde la aplicación. Se decide antes de construir US-66 | Coordinación de Ambiental |
| D-43 | Nombre estándar de la actividad de Blackboard (de la spec 005, sigue abierta) | Una actividad por PI, como «ABET SO4.1». US-60 y US-61 lo muestran y cambian con la constante de J-44 si la carrera lo cierra con otro nombre | Coordinación de Ambiental |

De Jefferson (J), con el valor que propone la spec.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| J-43 | Dónde vive el texto «Qué corregir» | En una tabla del Front por motivo RECHAZA_CARGA, en `src/servicios/`, con una prueba que recorre los motivos del contrato y sin consejo para un motivo desconocido | Jefferson |
| J-44 | Dónde viven las líneas de «Antes de subir» | En una constante del Front que sigue D-43, armada con `Seccion.pi` | Jefferson |
| J-45 | Quién decide que la última carga de una sección se rechazó para el profesor | En esta spec, el Front, con la ruta 4 y una sola petición a la ruta 8, sin cambiar la ruta 4 (FR-015). Después de la ruta 17, una spec posterior pasa la consulta de la etapa a una función del Back compartida y suma a la ruta 4 el campo aditivo `ultima_rechazada_id`, con lo que P2 deja de pedir la ruta 8 (veredicto DUDOSA del crítico y «Fuera de alcance») | Jefferson |
| J-46 | Página de llegada por rol | P7 para el COORDINADOR y P2 para el PROFESOR, con `pantallaDeLlegada(usuario)`, que entra en el mismo commit que P7 y que US-52 de la spec 005 reutiliza para el fragmento vacío o desconocido. P7 lleva el fragmento `#/avance` (propuesta) en la navegación de US-52 | Jefferson |
| J-47 | Forma de la ruta 17 y sus números | `GET /api/avance` solo para COORDINADOR, con secciones, etapa, `carga_id`, `profesores` y conteo. El bloque de reglas (C-C04) y la división POR_DECLARAR y DECLARADA (C-C06) llegan después como campos aditivos. P7 y la ruta 17 toman los números que AD-47 de la spec 005 nombra, y esa idea recibe otros. Al aprobar esta spec, `specs/005-oportunidades-de-mejora/revision-historias.md` suma junto a AD-47 una nota fechada que remite a J-47 de la spec 007 | Jefferson |
| J-48 | Cómo se decide la etapa | En cada lectura, en una sola consulta del Back y sin guardarla. Primero SIN_PLAN, después PUBLICADA con una carga PUBLICADA, para que una sección publicada sin profesor activo cuente como publicada, después SIN_PROFESOR, después CON_RECHAZO con una carga RECHAZADA y, en otro caso, SIN_CARGA. Una alternativa pone SIN_PROFESOR antes de PUBLICADA, para que la coordinación vea la sección sin profesor. Otra cuenta en el resumen de P7 solo las secciones con plan, porque en una sección SIN_PLAN nadie puede registrar | Jefferson |

## Fuera de alcance

- El bloque de reglas y parámetros pendientes al comienzo de P7 (C-C04). La lista de pendientes con su efecto va al acta de la reunión con Claudia antes de la semana 15, y el bloque entra en la ruta 17 después de US-45 a US-49 de la spec 005.
- La división de la etapa PUBLICADA en POR_DECLARAR y DECLARADA (C-C06), después de V1_12 y de US-49 de la spec 005, con la regla de completitud de `DeclaracionPendiente` y el control Q17 sin redefinirlos.
- El texto sobre las filas rechazadas de una carga publicada y el botón «Reemplazar con un export corregido» en P4 (C-P04), después de que la spec 005 cierre P4 y de US-52, con el fragmento `#/secciones/{seccion_id}/subir?reemplaza={carga_id}`.
- Nombrar en P4 la carga que sigue publicada tras un reemplazo rechazado y el botón «Ver la carga publicada» (resto de C-P05), que piden la ruta 4 desde P4.
- El pliegue de la constancia en un details y la supresión de la línea «0 filas leídas, 0 aceptadas y 0 rechazadas» (C-P03 y C-T05), con un solo details para todos los estados.
- Las explicaciones de cada estado en P4 y P5 y las glosas de PI y SO en pantalla (C-T05).
- El mensaje sin conexión distinto del servicio caído y el botón «Intentar de nuevo» (C-T03), salvo que la capacitación de la semana 14 muestre fallas de red reales.
- P6 sin cargas publicadas con un solo mensaje (C-P06).
- El resumen y el filtro de los indicadores debajo de la meta en P6 de la carrera (C-C05), que cambia J-28 de la spec 004 y la sección 9.2 de `frontend.md` y va con la reunión de mejora (N11) y la spec del R-18.
- La tabla desplazable con `role="region"`, la prueba a 375 px y la revisión con axe-core (C-T06), después de US-46 de la spec 005, con axe-core como dependencia nueva que pide la aprobación de Jefferson y la espera de 14 días de Dependabot.
- La variante de P2 del coordinador con resumen y filtro (C-T01), absorbida por P7.
- Los pasos de descarga del export en Blackboard dentro de P3 (C-T04), que esperan un texto de la Coordinación sin dueño ni fecha.
- El campo `ultima_rechazada_id` de la ruta 4 y la consulta compartida del Back (J-45), que llegan en una spec posterior a la ruta 17.
- El rótulo de «Volver a mis secciones» de P3 y P4 para el coordinador y su destino, que `alVolver` de `App.tsx` fija en P2 y que debería ser `pantallaDeLlegada(usuario)`. La deuda choca con el fin de US-63, pero cambiarla mueve el texto que buscan las pruebas de Vitest, y con US-52 el botón atrás del navegador ya vuelve de P4 a P7.
- El envío de correos desde la aplicación. La coordinación copia la lista y escribe desde su propio correo.
- El aviso que nombra la columna mal nombrada (C-C04 de la spec 005) y la marca «Declaración pendiente» en P2 y P5 (C-14 b de la spec 005).
