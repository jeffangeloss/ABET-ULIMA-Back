# Feature Specification: Resumen del curso para la coordinación

**Feature Branch**: `docs/009-resumen-curso` del Back (PR a `develop`), con el contrato en el Front y la implementación en `feat/009-resumen-curso` después de la aprobación
**Created**: 2026-11-24
**Status**: Aprobada por Jefferson en el chat el 2026-11-24 («Sí, apruébala»), con D-32 y J-60 a J-64 en sus valores provisionales, en la rama `docs/009-resumen-curso` del Back y del Front. La construcción va en `feat/009-resumen-curso` después del ensayo de la capacitación de la spec 008 (J-64)
**Input**: «ahora empieza con la página Resumen Curso del pbix» y, antes en la misma sesión, «para el tema de los gráficos, considera usar lo que se trabajó en el pbix de steffanu»

## Épica

> **EP-09. Resumen del curso para la coordinación (propuesta).** Stefanny Montaño arma en Power BI el tablero `Resumen de indicadores ABET - Cursos de Carrera.pbix`, cuya página «Resumen Curso» resume un curso con sus secciones, sus porcentajes, sus promedios y las secciones que cumplen la meta. El sistema ya calcula esas cifras por sección en `abet.v_r17_por_pi`, pero ninguna pantalla las reúne por curso, y ADR-008 deja el agregado del curso a la espera de D-32. Esta épica lleva al sistema esa página para la coordinación, con las cifras de la base, sin Power BI y sin datos de personas, empezando por Química General (5643) de Ingeniería Industrial en 2026-1.

Convenciones de esta spec. Todos los datos de los escenarios son inventados y usan la siembra de la spec 008, con la 701 a la 704 de 5643 en 2026-1, los profesores `docente701@example.invalid` a `docente703@example.invalid`, la 704 sin profesor y la coordinación del curso `coordinador.quimica@example.invalid`, en `db/datos/quimica_2026_1_inventado.sql`. La tabla maestra real de Química General y el tablero viven fuera de todo repositorio.

Prefijos e identificadores. La épica continúa la numeración (EP-09). Las historias siguen desde US-91, porque la spec 008 termina en US-90. Las decisiones de la carrera siguen desde D-56 y las de Jefferson desde J-60. La ruta nueva es la 20, porque la 19 está reservada (J-55), y la lista de cursos de US-93 es la 21 (propuesta). La pantalla nueva es P8 y el registro de la decisión es ADR-010 del Front. Esta spec no necesita migraciones.

Siglas y términos. Las de las specs 001 a 008 valen aquí. El indicador de desempeño (performance indicator, PI) y el resultado del estudiante (student outcome, SO) conservan su sentido. «Nivel esperado o superior» nombra lo que el tablero llama «Aprobados» o «3-4», porque la vista usa el NIVEL_ESPERADO del conjunto de reglas y no un 3 fijo. Las expresiones de análisis de datos (Data Analysis Expressions, DAX) son las fórmulas de las medidas de Power BI.

Los escenarios viven en `specs/009-resumen-del-curso/aceptacion/`, en español (`# language: es`), en tres archivos. `resumen_del_curso.feature` contiene US-91 y US-93, `pantalla_resumen_del_curso.feature` US-92 y `conciliacion_del_curso.feature` US-94. La revisión por refutación está en `revision-historias.md`.

## Equivalencias con el tablero

| Visual de «Resumen Curso» | En P8 | Razón |
| --- | --- | --- |
| Segmentador de año y ciclo | Periodo de la ruta 18, como en P2 a P7 | Ya existe (US-73) |
| Segmentador de curso | Selector de curso solo para la coordinación de la carrera (US-93) | La coordinación del curso tiene uno solo |
| Segmentador de PI | Un bloque por PI del plan en la misma respuesta | Química mide un solo PI y filtrar en el Front obligaría a recalcular (BR-RESULTADOS-11) |
| Segmentador de profesor | Se omite | BR-RESULTADOS-10, H05 y D-57 |
| Segmentador de sección | Se omite, porque la tabla ya trae cada sección | BR-RESULTADOS-11 |
| Segmentador de nivel y competencia | Se omite | Pertenece a «Resumen Competencias - Nivel», fuera de alcance |
| Columnas del promedio por profesor y PI | Una barra por sección en su fila, en orden de número, con la línea de la meta | Sin profesores (BR-RESULTADOS-10) y sin biblioteca (J-24) |
| Tarjeta «% Profesores Aprobados» | Se omite | D-57 y D-51. Con un profesor por sección repite el conteo de secciones |
| Tarjeta «Promedio Nota» | «Promedio de calificación» del curso y de cada sección | US-91 |
| Torta de secciones aprobadas y no aprobadas | Conteo escrito de secciones en la meta con su barra de dos tramos | J-62 |
| Barra al 100 % de alumnos aprobados y desaprobados | Barra de dos tramos del curso, nivel esperado o superior y debajo | US-92 |
| Tabla de sección, profesor, promedio y % de alumnos con 3 y 4 | Tabla por sección con calificados, porcentaje, promedio y estado, sin profesor | US-92 |

## Clarifications

### Session 2026-11-24

- Q: ¿Por qué una ruta nueva y no el campo `agregados` de la ruta 12 que propone US-80? → A: La ruta 12 es una por usuario, no recibe identificadores y también la usa el profesor, y con `agregados` la coordinación de la carrera recibiría unas 150 secciones para ver un curso. El crítico de arquitectura sostiene la ruta 20 y esta spec sustituye la sección 15.6 del contrato, US-80 y FR-016 de la spec 008 (J-61).
- Q: ¿El tablero responde D-32? → A: No por sí solo, porque D-32 es de la coordinación de Ambiental y de la Oficina de Calidad. La suma de estudiantes por PI y curso del tablero es el valor provisional de D-32 que esta spec construye con la franja provisional (J-60).
- Q: ¿Por qué no hay profesores en P8? → A: La base no guarda nombres (`PROFESOR` es nulo en `abet.v_tabla_maestra_pi`), BR-RESULTADOS-10 prohíbe un orden de docentes y D-47 y D-51 siguen abiertas. D-57 pregunta si la coordinación debe ver vistas por profesor.

### Session 2026-11-25

- Q: ¿Qué fórmulas usa el tablero de Stefanny? → A: El modelo del archivo `Resumen de indicadores ABET - Cursos de Carrera.pbix` se lee con la biblioteca `pbixray` sin abrir Power BI, fuera del repositorio y sin leer sus filas. Sus medidas en expresiones de análisis de datos (Data Analysis Expressions, DAX) son las siguientes. «Promedio Nota» es `AVERAGE('Maestra'[CALIFICACIÓN])`. «% Alumnos 3-4» divide las filas con `CALIFICACIÓN >= 3` entre `COUNTROWS('Maestra')`. «Sección Aprobada» vale 1 cuando ese porcentaje llega a 0,8, y «Secciones Aprobadas» la suma sobre `VALUES('Maestra'[SECCIÓN])`. «Alumnos Aprobados» y «Alumnos Desaprobados» cuentan las filas con 3 o más y con menos de 3, y «% Profesores Aprobados» divide las secciones aprobadas entre las secciones distintas, así que cuenta secciones y no profesores.
- Q: ¿Cierra D-56? → A: Sí, sin cambiar el valor provisional. El tablero divide entre todas las filas de la tabla maestra y el sistema entre los calificados, y en Química General las dos cifras coinciden, porque `scripts/generar_exports_desde_maestra.py` rechaza la tabla maestra con una calificación vacía y armó los exports de las 18 secciones. El tablero suma alumnos y no promedia porcentajes, igual que BR-RESULTADOS-13, y compara el porcentaje sin redondear con 0,8, mientras BR-RESULTADOS-14 compara el porcentaje redondeado a un decimal. Esa diferencia solo cambia el estado de una sección con más de 400 estudiantes, porque con menos el logro más cercano por debajo de 80 % queda bajo 79,95 %.
- Q: ¿Dónde puede diferir el tablero en otros cursos? → A: En dos casos que se le explican a Stefanny antes de cambiar una regla. Una fila con la calificación vacía cuenta como desaprobada en el tablero, porque DAX compara el vacío como 0, mientras el sistema la deja sin evidencia y fuera de los calificados. El tablero agrupa además las secciones solo por número, así que con varios cursos a la vez junta secciones de cursos distintos, y P8 las separa por curso (H32). SC-003 sigue abierto hasta que Stefanny compare las dos pantallas.

## User Scenarios & Testing *(mandatory)*

### US-91: La coordinación recibe las cifras del curso en la ruta 20 (Priority: P1)

Como coordinación de un curso o de una carrera, quiero recibir de una sola vez las cifras del curso y de cada sección por PI, con el promedio de calificación y las secciones en la meta, para saber si el curso cumple el PI sin abrir un R-17 por sección.

**Why this priority**: sin estas cifras P8 no tiene qué mostrar, y hoy ninguna ruta da el curso ni el promedio. La regla de la meta y el alcance ya existen, así que la historia reutiliza `secciones_visibles()`, la vista y `en_meta()`.

**Independent Test**: en una base desechable con la siembra de Química y tres cargas publicadas, `GET /api/resumen-curso?periodo=2026-1&asignatura=5643` da al curso 23 de 33, 69,7 % y promedio 2,91, y 1 de 3 secciones publicadas en la meta.

**Base**: `abet.v_r17_por_pi` (`n_nivel_1` a `n_nivel_4`, `n_sin_evidencia`, `n_total`, `n_esperado_o_superior`, `pct_logro_sobre_calificados`, `meta_logro_pct`, `nivel_esperado`, `provisional`), `abet.seccion`, `abet.carga` (la PUBLICADA de cada sección), `abet.plan_medicion`, `abet.pi` y `abet.so`, `acceso.coordinacion_alcance` y `acceso.usuario_autorizado` por `app/permisos.secciones_visibles()` y `puede_ver_avance()`. Sin migración.
**Pantalla**: ninguna propia. P8 la consume (US-92).

**Acceptance Scenarios** (`specs/009-resumen-del-curso/aceptacion/resumen_del_curso.feature`):

1. **El curso suma alumnos de las secciones publicadas y no promedia porcentajes**, con 23 de 33, 69,7 %, promedio 2,91 y un alumno sin evidencia aparte.
2. **Cada sección trae sus cifras en orden de número** y la sección sin carga trae nulos.
3. **El conteo de secciones cuenta la meta solo sobre las publicadas**, con 4, 3, 1, 2 y 1.
4. **Cada porcentaje de sección es el de su R-17.**
5. **El curso cumple con el 80,0 justo y no cumple con 75,0**, con la misma función del R-17.
6. **Un curso sin cargas publicadas trae nulos y no ceros.**
7. **Con un conjunto de reglas provisional el curso sale provisional.**
8. **La respuesta trae solo las claves de su lista cerrada.**
9. **El profesor recibe 403**, sin sesión responde 401 y un periodo o una asignatura mal formados responden 422.
10. **La coordinación de Ambiental recibe el resumen de 5643 sin indicadores**, con 200, como las rutas 12 y 17 fuera del alcance.

---

### US-92: P8 muestra el resumen del curso (Priority: P1)

Como coordinación de Química General, quiero ver en una página las cifras del curso con su barra, una barra por sección con la línea de la meta y la tabla de secciones, para ubicar qué secciones necesitan un plan de acción, como en la página «Resumen Curso» del tablero de Stefanny.

**Why this priority**: es lo que pide Jefferson y lo que la coordinación verá en la capacitación. Sin P8 la ruta 20 no llega a nadie.

**Independent Test**: con la respuesta simulada de la ruta 20, Vitest encuentra en P8 «23 de 33 alumnos en el nivel esperado o superior (69,7 %)», «Promedio de calificación 2,91 de 4», cuatro filas en orden de número y ninguna celda con un profesor.

**Base**: ninguna directa. P8 escribe lo que trae la ruta 20 (BR-RESULTADOS-11).
**Pantalla**: P8 «Resumen del curso» (propuesta), solo en el menú de la cuenta COORDINADOR (`src/App.tsx`) y enlazada desde cada curso de P7, con los rótulos de P6 (`src/pantallas/MisLogros.tsx`) y el sistema visual de la spec 008.

**Acceptance Scenarios** (`specs/009-resumen-del-curso/aceptacion/pantalla_resumen_del_curso.feature`):

1. **P8 escribe las cifras del curso con su barra de dos tramos.**
2. **P8 trae una fila por sección con su barra y la línea de la meta**, y la sección sin carga no dibuja una barra de 0 %.
3. **P8 no muestra profesores ni ordena por resultado**, y no trae torta ni tarjeta de profesores.
4. **P8 marca las cifras provisionales.**
5. **P8 de un curso sin cargas no dibuja barras de 0 %.**
6. **Solo la coordinación ve el enlace al resumen del curso en el menú.**
7. **P8 a 375 px no se desplaza a lo ancho y se recorre con teclado** (Playwright).

---

### US-93: La coordinación de la carrera elige el curso (Priority: P2)

Como coordinación de una carrera, quiero elegir en P8 uno de los cursos con plan en el periodo, porque la carrera mide varios cursos y la coordinación del curso tiene uno solo.

**Why this priority**: Química tiene una coordinación de curso y no la necesita para la capacitación, pero Ambiental mide 450002 y 450010 en 2026-2 y su coordinación no llegaría a P8 sin elegir.

**Independent Test**: `coordinacion@example.invalid` recibe 450002 y 450010 en la ruta 21 para 2026-2, y `coordinador.quimica@example.invalid` recibe solo 5643 en 2026-1.

**Base**: `abet.plan_medicion` y `abet.asignatura` filtradas por `secciones_visibles()`.
**Pantalla**: el selector de curso de P8, que no aparece si la respuesta trae un solo curso.

**Acceptance Scenarios** (`specs/009-resumen-del-curso/aceptacion/resumen_del_curso.feature`):

1. **La coordinación de la carrera recibe la lista de sus cursos con plan en el periodo.**
2. **La coordinación del curso recibe solo su curso.**

---

### US-94: El conciliador compara el curso y sus secciones con la tabla maestra (Priority: P2)

Como dueño técnico, quiero que el conciliador de la spec 008 compare también las cifras del curso y el promedio de cada sección con la tabla maestra, para mostrar a Stefanny que P8 da lo mismo que su tablero.

**Why this priority**: es la única prueba de igualdad con el tablero, pero depende de US-91 y la capacitación no la necesita para funcionar.

**Independent Test**: con el ensayo inventado de la spec 008, `conciliar_tabla_maestra.py --curso` termina en 0 con «Curso igual…», y con una calificación cambiada termina en 1 sin mostrar el código ni la calificación.

**Base**: la tabla maestra que lee `db/herramientas/conciliar_tabla_maestra.py` y la consulta de la ruta 20 en una sesión de solo lectura.
**Pantalla**: ninguna.

**Acceptance Scenarios** (`specs/009-resumen-del-curso/aceptacion/conciliacion_del_curso.feature`):

1. **El conciliador dice que el curso es igual a la tabla maestra.**
2. **Una calificación cambiada en la tabla maestra hace distinto al curso**, sin mostrar datos del estudiante.

### Edge Cases

- Un curso de dos carreras con metas distintas trae `meta_pct` y `en_meta` del curso en `null`, y cada sección conserva los suyos.
- Una sección con carga RECHAZADA o REEMPLAZADA sin otra PUBLICADA cuenta como sin dato.
- Un alumno sin evidencia no cuenta en los calificados ni en el promedio, y el curso lo informa en `sin_evidencia`.

## Requirements *(mandatory)*

- **FR-001** La ruta 20, `GET /api/resumen-curso?periodo=AAAA-C&asignatura=CODIGO`, atiende solo a la cuenta COORDINADOR con el guardián de la ruta 17 y responde 403 `SOLO_COORDINACION` al PROFESOR, 401 sin sesión y 422 con un periodo o una asignatura mal formados, sin leer la base.
- **FR-002** La ruta 20 toma las secciones de la asignatura y del periodo dentro de `secciones_visibles()`, así que fuera del alcance responde 200 con `indicadores` vacío y no revela si el curso existe.
- **FR-003** La respuesta trae un elemento por PI del plan en orden de SO y PI, con `so`, `pi`, `nivel_esperado`, `meta_pct`, `provisional`, `curso`, `conteo_secciones` y `secciones`, y nada más (lista cerrada, propuesta). `curso` trae `estudiantes_por_nivel`, `logrados`, `calificados`, `sin_evidencia`, `total`, `pct_sobre_calificados`, `promedio_nivel` y `en_meta`. Cada sección trae `seccion_id`, `numero`, `estado`, `carga_id`, `logrados`, `calificados`, `sin_evidencia`, `pct_sobre_calificados`, `promedio_nivel` y `en_meta`.
- **FR-004** Las cifras del curso suman los conteos de las cargas PUBLICADA de `abet.v_r17_por_pi` y nunca promedian porcentajes. El porcentaje es la suma de logrados entre la suma de calificados con `ROUND(numeric, 1)` y el promedio es la suma de cada nivel por su conteo entre la suma de los conteos con `ROUND(numeric, 2)`, ambos en PostgreSQL y en una sola transacción READ ONLY con REPEATABLE READ.
- **FR-005** `en_meta` del curso y de cada sección sale de la misma función que el plan de acción del R-17, sobre el porcentaje ya redondeado (BR-RESULTADOS-06).
- **FR-006** `conteo_secciones` cuenta `en_meta` y `debajo_de_la_meta` solo sobre las secciones publicadas, y `sin_dato` aparte.
- **FR-007** Un curso sin cargas publicadas trae `calificados` 0 y el porcentaje, el promedio y `en_meta` en `null`. `provisional` es verdadero si alguna sección lo es.
- **FR-008** La respuesta no trae correos, nombres, códigos de estudiantes, `subida_por`, `nombre_archivo` ni `sha256`, y la ruta 20 entra a la lista de rutas con sesión de la prueba de J-25.
- **FR-009** P8 escribe las cifras de la ruta 20 sin recalcularlas, dibuja las barras con HTML y Tailwind, con el ancho en `style` y `aria-hidden`, sin biblioteca de gráficos, y usa los rótulos de P6.
- **FR-010** La ruta 21, `GET /api/resumen-curso/cursos?periodo=AAAA-C` (propuesta), da a la coordinación los cursos con plan en el periodo dentro de su alcance, en orden de código, con código y nombre.
- **FR-011** `conciliar_tabla_maestra.py --curso` (propuesta) compara el curso y el promedio de cada sección con la tabla maestra y escribe solo «igual» o «distinto».
- **FR-012** La sección 15.6 del contrato, US-80 y FR-016 de la spec 008 quedan sustituidas por esta spec con un cambio fechado, y ADR-010 del Front modifica en parte ADR-008.

## Success Criteria *(mandatory)*

- **SC-001** Los escenarios de los tres `.feature` tienen su prueba en pytest-bdd, en Vitest o en Playwright, y pasan.
- **SC-002** Con la tabla maestra real de Química General, fuera de todo repositorio, el conciliador con `--curso` dice «Curso igual…» para 5643 en 2026-1.
- **SC-003** Stefanny revisa P8 de 5643 en la vista previa de develop junto a su página «Resumen Curso» y no encuentra diferencias en las cifras que ambas muestran, o las diferencias se explican por los dos casos de la sesión del 2026-11-25.
- **SC-004** Ninguna respuesta ni pantalla de esta spec trae un dato de personas, como comprueban el escenario de la lista cerrada y el barrido de privacidad de la spec 008.

## Decisiones abiertas

De la carrera, de la Oficina de Calidad y de Stefanny (D). Mientras no se decidan, el sistema aplica el valor provisional.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| D-32 | Cómo se resume un PI medido en varias secciones (spec 004) | Suma de estudiantes por PI y curso, como el tablero, con la franja provisional | Coordinación de Ambiental y Oficina de Calidad |
| D-56 | Fórmulas DAX de «Alumnos Aprobados», «Secciones Aprobadas», «Promedio Nota» y «% Alumnos 3-4», y si cuentan sobre los calificados o sobre el total | Cerrada el 2026-11-25 con las fórmulas del tablero, sin cambio. Nivel esperado o superior sobre los calificados, sección en la meta con 80 % o más y promedio de 1 a 4 de los calificados (Clarifications, sesión del 2026-11-25) | Stefanny Montaño |
| D-57 | Si la coordinación ve vistas por profesor (segmentador, columnas y porcentaje de profesores) | No las ve | Coordinación de la carrera y Oficina de Calidad |

De Jefferson (J).

| ID | Decisión | Valor provisional |
| --- | --- | --- |
| J-60 | Construir el agregado del curso con D-32 abierta | Sí, con la franja provisional, y reabre J-54 de la spec 008 |
| J-61 | Ruta 20 propia en lugar del campo `agregados` de la ruta 12 | Ruta 20, que sustituye la sección 15.6, US-80 y FR-016 |
| J-62 | Torta de secciones del tablero | Conteo escrito con barra de dos tramos |
| J-63 | P8 nueva en lugar de sumar el resumen a P6 o a P7 | P8, enlazada desde P7 |
| J-64 | Cuándo se construye | Después del ensayo de la capacitación de la spec 008, con unas 18 h más el contrato y el cierre |

## Fuera de alcance

- La torta de secciones (C-05) y la tarjeta de porcentaje de profesores (C-07), refutadas por las tres lentes.
- Las vistas por profesor del tablero, hasta D-57.
- La descarga del resumen en Excel (C-08), que choca con la ruta 19 reservada.
- Las páginas «Histórico por Profesor» (C-60) y «Resumen Competencias - Nivel» (C-61), que esperan otro periodo con datos y la «Base cursos - Nivel» de Industrial.
- El reparto del curso por cada nivel de 1 a 4 en una gráfica propia (C-04). La respuesta trae `estudiantes_por_nivel` y P8 muestra la barra de dos tramos.
