# Feature Specification: Nombre del profesor en la base y en el R-17

**Feature Branch**: `docs/010-nombre-del-profesor` del Back (PR a `develop`), con la implementación en `feat/010-nombre-del-profesor` después de la aprobación y de la fusión de `fix/r17-recuadros-y-filas-de-pi`
**Created**: 2026-11-24
**Status**: Borrador para aprobación de Jefferson
**Input**: «no tenemos campo del nombre del profesor en las tablas? porque normal si le asignas nombre a los correos de prueba» y, ante la pregunta de qué va en D10 cuando la sección tiene varios profesores, «Sí, escribe la spec con los profesores asignados»

## Épica

> **EP-10. Nombre del profesor (propuesta).** La plantilla del R-17 trae el rótulo «Profesor:» en B10:C10 y su valor en D10:I10, que hoy sale vacío porque la base no guarda nombres (BR-R17-07 y valor provisional de D-12) y la plantilla base de la carrera lo deja para llenarse a mano. Esta épica guarda el nombre de cada profesor en `acceso.usuario_autorizado`, fuera del esquema `abet`, lo carga con la programación docente de la spec 006 y llena D10 con los nombres de los profesores asignados a la sección. Los nombres reales viven solo en Neon, y git lleva solo nombres inventados.

Convenciones de esta spec. Todos los datos de los escenarios son inventados. Los nombres inventados se escriben con letras y empiezan por «Profesor Inventado», porque la base rechaza los dígitos en un nombre (J-66). La correspondencia fija de las semillas es «Profesor Inventado Cuatrocientos Diez» para `docente410@example.invalid`, «Profesor Inventado Cuatrocientos Once» para `docente411@example.invalid`, «Profesor Inventado Varias» para `docente.varias@example.invalid` y «Profesor Inventado Setecientos Uno», «Profesor Inventado Setecientos Dos» y «Profesor Inventado Setecientos Tres» para `docente701@example.invalid` a `docente703@example.invalid`. Las cuentas COORDINADOR quedan sin nombre. Un profesor extra de un escenario, como `docente721@example.invalid`, se siembra en el paso Dado y no en `db/datos/`.

Prefijos e identificadores. La épica continúa la numeración (EP-10). Las historias siguen desde US-95, porque la spec 009 termina en US-94. Las decisiones de la carrera siguen desde D-58 y las de Jefferson desde J-65. La migración nueva es `V1_16__nombre_del_usuario.sql` (propuesta), porque la última es V1_15. Las reglas nuevas de las specs vivas son BR-ACCESO-15 y BR-R17-14 (propuestas). Esta spec no agrega rutas ni pantallas.

Siglas y términos. Las de las specs 001 a 009 valen aquí. La forma de normalización canónica compuesta de Unicode (Normalization Form C, NFC) es la forma en que el guion y la base guardan el nombre, y la descomposición canónica (Normalization Form D, NFD) es la que separa las tildes para ordenar. La categoría Unicode Cf agrupa los caracteres de formato invisibles, como U+200B. El valor separado por comas (comma-separated values, CSV) es el formato del archivo de la programación docente. La Ley 29733 es la Ley de Protección de Datos Personales del Perú y el Decreto Supremo (DS) 016-2024-JUS es su reglamento.

Los escenarios viven en `specs/010-nombre-del-profesor/aceptacion/`, en español (`# language: es`), en cuatro archivos. `nombre_en_la_base.feature` contiene US-95, `programacion_con_nombre.feature` US-96, `profesores_en_el_r17.feature` US-97 y US-98, y `privacidad_del_nombre.feature` US-99. La revisión por refutación está en `revision-historias.md`.

## Qué cambia y qué no

| Objeto | Cambia | No cambia |
| --- | --- | --- |
| `acceso.usuario_autorizado` | Columna `nombre`, nulable, con su restricción y su comentario | `correo`, `rol`, `activo` y el comentario de baja «nunca se borra» |
| Esquema `abet` | Nada | Q04 sigue en 0 filas |
| Q15 de `db/pruebas/pruebas.sql` | Su filtro suma `nombre` para `acceso` y espera correo y nombre | Q01 a Q14 y Q16 a Q21 |
| `crear_rol_app.sql` | Nada, porque el SELECT de tabla ya cubre la columna | `abet_app` sigue sin INSERT ni UPDATE |
| `cargar_programacion.py` y `.sql` | Columna opcional `nombre` | Un CSV sin esa columna responde como en la spec 006 |
| R-17, hoja «Cursos de Carrera» | D10 y el alto de la fila 10 | B10:C10, las demás celdas de la cabecera, las 45 celdas combinadas y los recuadros A y B |
| R-17, hoja «Constancia», JSON y rutas | Nada | `subida_por` sigue siendo el correo (D-12) |

## Clarifications

### Session 2026-11-24

- Q: ¿Por qué el nombre va en `acceso` y no en `abet`? → A: Q04 prohíbe columnas de nombre en `estudiante`, `medicion`, `carga`, `rechazo_fila` y `carga_columna`, y los roles de lectura `abet_lectura` y `powerbi_lectura` no tienen acceso a `acceso`. El usuario ya vive en `acceso` por esa razón (V1_09).
- Q: ¿Qué va en D10 con varios profesores? → A: Los nombres de todos los profesores asignados a la sección en `acceso.docente_seccion`, en orden alfabético sin tildes ni mayúsculas y separados por «; », como pidió Jefferson. El rótulo «Profesor:» de B10:C10 no cambia.
- Q: ¿Y si un profesor no tiene nombre? → A: Se omite de D10 y su correo no lo reemplaza, porque el R-17 sale de la carrera hacia los revisores de ABET y BR-R17-07 deja el correo solo en la hoja «Constancia».
- Q: ¿D-12 queda resuelta? → A: No. El pedido de Jefferson cambia su valor provisional, y la decisión sigue con la Coordinación de Ambiental y la Oficina de Calidad. El llenado de D10 vive en una función aislada para revertirlo sin tocar el resto de la cabecera.

## User Scenarios & Testing *(mandatory)*

### US-95: La base guarda el nombre del profesor en `acceso` (Priority: P1)

Como administrador técnico de la base, quiero una columna opcional `nombre` en `acceso.usuario_autorizado`, normalizada por la base y vigilada por Q15, para que el R-17 escriba al profesor sin guardar nombres en `abet` ni romper a los usuarios que ya existen.

**Why this priority**: es el pedido literal («campo del nombre del profesor en las tablas») y las specs 004 y 006 ya anuncian que el nombre en el R-17 pide una migración propia y el cambio de Q15. Sin la columna no hay nada que cargar ni que escribir en D10.

**Independent Test**: en una base desechable migrada hasta V1_16, un usuario sin nombre entra, un nombre con dos espacios seguidos se rechaza por `ck_usuario_autorizado_nombre`, Q15 encuentra en `acceso` exactamente `usuario_autorizado.correo` y `usuario_autorizado.nombre`, Q04 da 0 filas y `abet_app` recibe 42501 al cambiar un nombre.

**Base**: `db/migration/V1_16__nombre_del_usuario.sql` (nueva, solo DDL), `acceso.usuario_autorizado`, `db/pruebas/pruebas.sql` (Q04 y Q15), `db/plataforma/neon/crear_rol_app.sql` y `db/pruebas/probar_rol_app.sql`, `db/plataforma/neon/crear_roles_lectura.sql`.
**Pantalla**: ninguna.

**Acceptance Scenarios** (`specs/010-nombre-del-profesor/aceptacion/nombre_en_la_base.feature`):

1. **Un usuario sin nombre sigue siendo válido.**
2. **La base acepta un nombre normalizado con tildes y eñes.**
3. **La base rechaza un nombre que no está normalizado o que no parece un nombre**, con espacios a los lados, dos espacios seguidos, vacío, un salto de línea, U+200B, una arroba, un dígito o la forma NFD.
4. **Q15 encuentra en `acceso` solo el correo y el nombre del usuario**, y una columna de nombre en otra tabla de `acceso` la hace fallar.
5. **Ninguna tabla de `abet` gana una columna de nombre**, con Q04 en 0 filas.
6. **La aplicación lee el nombre y no lo escribe.**
7. **Los roles de lectura no alcanzan el nombre y el rol de respaldo sí lo lee.**

---

### US-96: La programación docente trae el nombre del profesor (Priority: P1)

Como administrador técnico, quiero que `cargar_programacion.py` lea una columna opcional `nombre` del archivo de la carrera y la guarde junto al correo, para no escribir nombres a mano en el Windows cuando llega la programación del ciclo.

**Why this priority**: sin esta vía, los nombres reales solo entran con SQL a mano, y un literal escrito en una sesión interactiva de psql queda en su historial (AD-65). La spec 006 ya prevé que la programación traiga el nombre después.

**Independent Test**: con el archivo base de la spec 006 más la columna `nombre`, la corrida con `--aplicar` deja a `docente410@example.invalid` con «Profesor Inventado Cuatrocientos Diez», y ningún texto del informe repite ese nombre.

**Base**: `db/herramientas/cargar_programacion.py` y `cargar_programacion.sql` (spec 006, con cambios fechados de FR-002, FR-005, FR-007, FR-009 y FR-013), `tests/test_cargar_programacion.py` y los pasos de `tests/aceptacion/pasos/test_programacion_docente_feature.py`.
**Pantalla**: ninguna.

**Acceptance Scenarios** (`specs/010-nombre-del-profesor/aceptacion/programacion_con_nombre.feature`):

1. **Un profesor nuevo entra con su nombre.**
2. **Un profesor ya cargado sin nombre lo recibe y su rol y su estado no cambian**, y el informe cierra con «Cambios guardados.».
3. **Un nombre que ya existe no se cambia**, con un aviso que lleva el correo y ninguno de los dos nombres.
4. **Un archivo sin la columna `nombre` responde como en la spec 006.**
5. **Los espacios del nombre se normalizan antes de guardarlo.**
6. **Un nombre inválido rechaza el archivo antes de conectarse.**
7. **Dos nombres distintos para un mismo correo rechazan el archivo.**

---

### US-97: D10 del R-17 trae los profesores asignados (Priority: P1)

Como profesor o coordinación que entrega el R-17 a la carrera, quiero que el valor de «Profesor:» salga con los nombres de quienes dictan la sección, para no completar la celda a mano en cada libro.

**Why this priority**: es el segundo pedido literal de Jefferson y el único cambio visible de la spec. La plantilla base de la carrera trae la celda y hoy se llena a mano.

**Independent Test**: con la 701 de 5643 publicada y su análisis declarado, el R-17 trae en D10 «Profesor Inventado Setecientos Uno», y con tres profesores asignados trae «Profesor Inventado Ángel; Profesor Inventado Beto; Profesor Inventado Setecientos Uno» en dos generaciones seguidas.

**Base**: `abet_carga/r17.py` (`generar()`, `_cabecera()` y una función nueva y aislada que lee los profesores de la sección, propuesta), `abet.carga.seccion_id`, `acceso.docente_seccion` y `acceso.usuario_autorizado`, `lineas_del_recuadro()`, `plantillas/README.md` (fila de D10), `tests/test_r17.py` y `specs/features/r17/r17.spec.md` (BR-R17-07 y BR-R17-14).
**Pantalla**: ninguna. El libro se descarga por la ruta 7.

**Acceptance Scenarios** (`specs/010-nombre-del-profesor/aceptacion/profesores_en_el_r17.feature`):

1. **Una sección con un profesor trae su nombre en D10**, en Ambiental y en Industrial, con B10 igual a «Profesor:».
2. **Varios profesores salen en orden alfabético sin tildes ni mayúsculas, separados por «; », y el orden es estable.**
3. **Un profesor dado de baja sigue en D10 de su sección.**
4. **Solo los profesores de la sección salen en D10**, sin los de otra sección ni una cuenta COORDINADOR asignada.
5. **Un nombre que parece fórmula queda como texto.**
6. **Tres nombres caben en D10:I10 y la fila 10 crece sin mover el resto de la cabecera.**
7. **Fuera de D10 y de la fila 10 la plantilla no cambia.**

---

### US-98: Un profesor sin nombre o una sección sin profesor no rompen el R-17 (Priority: P1)

Como coordinación, quiero que el R-17 se genere aunque a un profesor le falte el nombre o la sección no tenga profesor, para no bloquear la entrega por un dato que todavía no se cargó.

**Why this priority**: todos los usuarios de Neon tienen hoy el nombre nulo, así que este es el caso de partida el día de la migración. La 704 de 5643 no tiene profesor y la coordinación sube por ella en el corte 2 (BR-ACCESO-09).

**Independent Test**: con la 701 publicada y un solo profesor sin nombre, la ruta 7 responde 200, D10 está vacía y la hoja «Cursos de Carrera» no contiene «docente701». La consulta informativa cuenta 1 sección publicada con un profesor sin nombre.

**Base**: `abet_carga/r17.py`, `acceso.docente_seccion`, `db/plataforma/neon/profesores_sin_nombre.sql` (nueva, informativa, propuesta).
**Pantalla**: ninguna.

**Acceptance Scenarios** (`specs/010-nombre-del-profesor/aceptacion/profesores_en_el_r17.feature`):

1. **Un profesor sin nombre no sale y el otro sí**, y el correo del primero no aparece en la hoja «Cursos de Carrera».
2. **Si ningún profesor tiene nombre, D10 queda vacía como hoy.**
3. **La sección sin profesor tiene R-17 con D10 vacía.**
4. **La consulta informativa cuenta las secciones publicadas con un profesor sin nombre sin mostrar correos ni nombres.**

---

### US-99: El nombre sale solo en D10 y git solo lleva nombres inventados (Priority: P2)

Como dueño técnico del repositorio público, quiero pruebas que fijen que el nombre del profesor aparece solo en D10 del R-17 y que las semillas y los archivos de git llevan solo nombres inventados, para cumplir la Ley 29733 y el DS 016-2024-JUS con la mínima exposición.

**Why this priority**: vigila lo que US-97 abre, pero el R-17 funciona sin ella. Sin esta historia, un nombre podría colarse en el registro de la aplicación o en una semilla sin que nada lo detecte.

**Independent Test**: un R-17 de la 701 con «Profesor Inventado Setecientos Uno» no trae ese nombre en ninguna celda fuera de D10, en las propiedades del libro ni en el nombre del archivo, el registro `abet.api` no lo contiene y la prueba de repositorio pasa sobre las semillas cargadas.

**Base**: `tests/test_r17.py` (molde de BR-R17-07), `app/configuracion.py` (`REGISTRO`), las rutas `GET /api/cargas`, `GET /api/cargas/{carga_id}` y `GET /api/sesion`, `db/datos/*.sql`, `tests/datos_inventados/` y una prueba de repositorio nueva (propuesta).
**Pantalla**: ninguna.

**Acceptance Scenarios** (`specs/010-nombre-del-profesor/aceptacion/privacidad_del_nombre.feature`):

1. **Fuera de D10 el libro no repite el nombre.**
2. **Las rutas de cargas y de sesión no traen el nombre.**
3. **El registro de la aplicación no trae el nombre.**
4. **Las semillas solo traen nombres inventados con correos de example.invalid.**
5. **Git no rastrea un archivo de programación con la columna `nombre` fuera de los datos inventados.**

### Edge Cases

- Un nombre con tildes, eñes, diéresis, apóstrofo o guion, como «Profesor Inventado D'Ángelo-Núñez», es válido. Uno que llega en mayúsculas se guarda y sale en mayúsculas, porque la spec no cambia la capitalización.
- Dos profesores homónimos de una sección salen los dos, en el orden de su `usuario_id`.
- Un nombre de 120 caracteres es válido y uno de 121 se rechaza en el guion con el número de fila y en la base por el largo de la columna.
- Un profesor asignado a la sección después de publicar la carga aparece en el R-17 de esa carga, porque el libro se genera en cada descarga y la spec no aplica corte temporal (J-67).
- Un nombre retirado a pedido de su titular (derecho de cancelación de la Ley 29733) queda nulo, y el R-17 lo omite como a cualquier profesor sin nombre (US-98).
- El respaldo diario de Neon con `abet_respaldo` copia el nombre al Windows y a Google Drive cifrado, así que ese respaldo entra al tratamiento de datos personales.

## Requirements *(mandatory)*

- **FR-001** La migración `V1_16__nombre_del_usuario.sql` (propuesta, solo DDL) agrega `acceso.usuario_autorizado.nombre varchar(120) NULL` y la restricción `ck_usuario_autorizado_nombre`. La restricción exige que el nombre sea igual a su versión recortada, no esté vacío, no tenga dos espacios seguidos, no tenga caracteres de control (`[[:cntrl:]]`) ni los de formato U+00AD, U+200B a U+200F, U+202A a U+202E, U+2060 a U+2064 y U+FEFF, no tenga arroba ni dígitos y cumpla `nombre IS NFC NORMALIZED`. La migración actualiza el `COMMENT ON SCHEMA acceso`, que hoy dice que el correo es el único dato de contacto, y comenta la columna como dato personal de la Ley 29733 y el DS 016-2024-JUS.
- **FR-002** Q15 de `db/pruebas/pruebas.sql` suma al filtro de `acceso` la condición `column_name LIKE '%nombre%'` y espera exactamente `usuario_autorizado.correo,usuario_autorizado.nombre`, con el mensaje «FALLA Q15: en acceso solo usuario_autorizado.correo y usuario_autorizado.nombre deben pasar el filtro» (propuesta). El paso `_correr_q15` de `tests/aceptacion/pasos/test_base_neon_feature.py` corre el bloque de Q15 del archivo y no el texto de Q04. Q04 y `controles_neon.sql` no cambian.
- **FR-003** `crear_rol_app.sql` no cambia. `probar_rol_app.sql` suma que `abet_app` lee `nombre` y recibe 42501 en un INSERT o un UPDATE de `acceso.usuario_autorizado`. Las pruebas de `crear_roles_lectura.sql` suman que `abet_lectura` y `powerbi_lectura` reciben 42501 sobre esa tabla y que `abet_respaldo` la lee. `db/README.md` declara que el respaldo de Neon lleva nombres de profesores y entra al tratamiento de la Ley 29733.
- **FR-004** `cargar_programacion.py` acepta una columna opcional `nombre`, en el archivo y en cada fila. Antes de conectarse, normaliza el nombre a NFC, quita los espacios a los lados y colapsa los internos a uno, y aplica la misma regla de FR-001. Una celda vacía significa sin nombre. Un nombre inválido rechaza el archivo con «Fila N. El nombre no es válido.» (propuesta) y dos nombres distintos para un mismo correo lo rechazan con «Fila N. El correo trae otro nombre en otra fila.» (propuesta), sin repetir ningún valor.
- **FR-005** `cargar_programacion.sql` guarda el nombre de un correo nuevo en el INSERT que ya existe y completa el de un correo existente con un UPDATE acotado a `WHERE nombre IS NULL`, que pasa a ser la segunda actualización permitida. Un correo existente con otro nombre no cambia y el informe dice «Aviso. <correo> ya tiene otro nombre en la base y no se cambia.» (propuesta). El guion nunca cambia `rol` ni `activo` y nunca asigna nombre a una cuenta COORDINADOR.
- **FR-006** Con la columna `nombre` en el archivo, la línea de resumen es «Resumen. N secciones nuevas, N usuarios nuevos, N asignaciones nuevas y N nombres completados.» (propuesta), donde «nombres completados» cuenta solo usuarios que ya existían con el nombre nulo. Un archivo que solo completa nombres cierra con «Cambios guardados.». Sin la columna, el informe es el de la spec 006. Ningún informe, registro ni mensaje de error escribe un nombre.
- **FR-007** La spec 010 cambia con fecha FR-002, FR-005, FR-007, FR-009 y FR-013 de la spec 006 y BR-ACCESO-11, y adapta `test_las_columnas_ajenas_se_ignoran_sin_leer_sus_valores` para que las columnas distintas de `nombre` sigan ignoradas sin leer sus valores.
- **FR-008** `generar()` de `abet_carga/r17.py` lee, dentro de su transacción READ ONLY con REPEATABLE READ (BR-R17-12), los usuarios de `acceso.docente_seccion` de `abet.carga.seccion_id` con `rol = 'PROFESOR'`, sin filtrar por `activo` y con `nombre` no nulo. Una función aislada (propuesta) los ordena en Python por la clave del nombre en NFD sin marcas diacríticas y con `casefold()`, con `usuario_id` de desempate, los une con «; » y devuelve el texto que `_cabecera()` escribe en D10 con `_escribir`. Sin nombres, D10 queda vacía.
- **FR-009** D10:I10 lleva ajuste de texto, y una función pura de cabida calcula el alto de la fila 10 por líneas con `lineas_del_recuadro()` y el ancho de D10:I10, sin pasar de 409 puntos. Las filas 9 y 11 y las filas 29 a 36 no cambian, y no hay tope de caracteres ni respuesta 422 por la cabida de D10. La implementación se construye después de fusionar `fix/r17-recuadros-y-filas-de-pi` y no modifica `alto_de_fila_final()`.
- **FR-010** Un profesor sin nombre se omite de D10 y su correo no lo reemplaza. Una sección sin profesores con nombre responde 200 con D10 vacía, y `generar()` no suma ningún error nuevo. La hoja «Constancia», el JSON de la constancia y BR-R17-09 y BR-R17-10 no cambian.
- **FR-011** La consulta informativa `db/plataforma/neon/profesores_sin_nombre.sql` (propuesta) recibe `-v periodo`, pasa la sesión a solo lectura antes de la primera consulta y devuelve solo dos números, las secciones del periodo con carga PUBLICADA que tienen algún PROFESOR asignado sin nombre y los profesores asignados sin nombre, sin correos, nombres ni números de sección. No es un control de `pruebas.sql` ni de `controles_neon.sql`.
- **FR-012** El nombre del profesor aparece solo en D10 de la hoja «Cursos de Carrera». No entra al nombre del archivo, a las propiedades del libro, a la hoja «Constancia», a las respuestas de `GET /api/cargas`, `GET /api/cargas/{carga_id}` ni `GET /api/sesion`, al registro `abet.api` ni a los informes de las herramientas.
- **FR-013** Las semillas `db/datos/periodo_2026_2_inventado.sql`, `varias_secciones_2026_2_inventado.sql` y `quimica_2026_1_inventado.sql` asignan a sus profesores los nombres inventados de las convenciones con `ON CONFLICT (correo) DO UPDATE SET nombre = coalesce(acceso.usuario_autorizado.nombre, EXCLUDED.nombre)`, para que develop de Neon los reciba sin pisar un nombre existente. Sus comprobaciones finales de usuarios y asignaciones no cambian. Una prueba de repositorio (propuesta) carga las semillas en una base desechable y exige que cada nombre no nulo empiece por «Profesor Inventado» y siga con palabras de solo letras, y que cada correo sea de `@example.invalid`, y revisa con `git ls-files` que ningún CSV rastreado fuera de `tests/datos_inventados/` tenga la columna `nombre`. Sus mensajes nombran el archivo y nunca el valor.
- **FR-014** V1_16 se aplica primero en develop de Neon desde el Windows de Jefferson con Flyway 13.9, después de un respaldo con `db/herramientas/respaldar_neon.sh`, y llega a la rama principal solo con el permiso de Jefferson (J-71). Los nombres reales entran solo por `cargar_programacion.py`, con un archivo fuera del repositorio, desde el Windows y con la conexión del dueño de la base.
- **FR-015** Las specs vivas suman BR-ACCESO-15 «Nombre del usuario autorizado» (propuesta) y BR-R17-14 «Profesores de la sección en D10» (propuesta), y cambian con fecha BR-R17-07, cuya regla pasa a decir que el libro lleva solo el nombre de los profesores de la sección en D10 y ningún nombre de estudiante. La fila de D10 de `plantillas/README.md`, las dos aserciones de `D10` nulo de `tests/test_r17.py` y el valor provisional de D-12 en la spec 001 cambian con la misma fecha.
- **FR-016** Cada escenario tiene su prueba con pytest-bdd en el clúster desechable de `tests/cluster_desechable.py`, nunca en localhost:5432 ni en Neon, y los cambios de Q15 y de `probar_rol_app.sql` pasan además por `db/pruebas/correr_pruebas.sh`.

## Key Entities

- **Usuario autorizado** (`acceso.usuario_autorizado`). Suma `nombre`, nulable, normalizado por la base y de solo lectura para `abet_app`. Es el único sitio de la base con el nombre de una persona.
- **Asignación docente** (`acceso.docente_seccion`). No cambia. Define quiénes son los profesores de una sección, sin vigencia.
- **Carga** (`abet.carga`). No cambia. Su `seccion_id` une el R-17 con los profesores de la sección.
- **Archivo de la programación docente**. CSV de la spec 006 con la columna opcional `nombre`, siempre fuera del repositorio cuando trae datos reales.
- **R-17**. Libro de la ruta 7, cuya hoja «Cursos de Carrera» lleva los nombres en D10:I10.

## Success Criteria *(mandatory)*

- **SC-001** Los escenarios de los cuatro `.feature` tienen su prueba en pytest-bdd y pasan, y `bash db/pruebas/correr_pruebas.sh` termina con «RESULTADO: todo pasó».
- **SC-002** En develop de Neon, después de V1_16 y de las semillas, el R-17 de la 701 de 5643 trae «Profesor Inventado Setecientos Uno» en D10, Q04 devuelve 0 filas y la consulta informativa devuelve 0 secciones con un profesor sin nombre para 2026-1.
- **SC-003** La prueba de repositorio pasa y ningún archivo rastreado por git trae un nombre de profesor que no tenga la forma inventada.
- **SC-004** Con la programación real cargada en la rama de Neon que Jefferson decida, la consulta informativa devuelve 0 secciones publicadas con un profesor sin nombre antes de entregar los R-17 del periodo.

## Decisiones abiertas

De la carrera y de la Oficina de Calidad (D). Mientras no se decidan, el sistema aplica el valor provisional.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| D-12 | Nombre del profesor en el R-17 (spec 001) | D10 lleva los nombres de los profesores asignados a la sección, y la constancia sigue con el correo de quien sube la carga | Coordinación de Ambiental y Oficina de Calidad |
| D-58 | De dónde salen los nombres reales, la hoja de programación de la carrera o una lista aparte | La columna `nombre` del mismo archivo de la programación docente, y una lista aparte pasa por el mismo guion | Coordinación de cada carrera |

De Jefferson (J).

| ID | Decisión | Valor provisional |
| --- | --- | --- |
| J-65 | Un campo `nombre` o dos campos, `nombres` y `apellidos` | Un campo de 120 caracteres, tal como lo escribe la carrera |
| J-66 | Dígitos en el nombre | La base los rechaza y los nombres inventados van en letras |
| J-67 | Quiénes salen en D10 | Todo PROFESOR de `acceso.docente_seccion` con nombre, activo o dado de baja, sin corte temporal. La alternativa del crítico filtra `asignado_en <= carga.terminada_en` y deja D10 vacía si la programación se carga después de publicar |
| J-68 | Orden, separador y largo de D10 | Alfabético sin tildes ni mayúsculas en Python, con `usuario_id` de desempate, separador «; », sin tope y con el alto de la fila 10 calculado |
| J-69 | Profesor sin nombre | Se omite de D10, sin el correo de relleno y sin aviso en la hoja «Constancia» |
| J-70 | Corrección de un nombre mal escrito y retiro a pedido del titular | El dueño de la base corre desde la Mac un psql no interactivo en el Windows por `en_windows.py`, con el correo y el nombre por la entrada estándar, nunca en una sesión interactiva. La alternativa del crítico son las banderas `--corregir-nombres` y `--retirar-nombres` de `cargar_programacion.py` |
| J-71 | Cuándo y dónde se aplica | V1_16 primero en develop de Neon con respaldo previo y en la rama principal con el permiso de Jefferson, y el código después de fusionar `fix/r17-recuadros-y-filas-de-pi`, con unas 17 h más el cierre |

## Fuera de alcance

- Las pantallas con el nombre del usuario y el nombre en `/api/sesion` (C-C07), sacadas por las tres lentes.
- El nombre en la hoja «Constancia» o en `subida_por` (C-P06), que cambia el contrato del Front y espera D-12.
- La conversión de mayúsculas a mayúscula inicial, que estropea apellidos compuestos.
- Una herramienta propia de corrección o de retiro de nombres, mientras J-70 siga con su valor provisional.
- La vigencia de una asignación con `desasignado_en` (C-P07), que nadie pide.
- El nombre de las cuentas COORDINADOR (AD-64).
- Un control nuevo en `controles_neon.sql` para el esquema `acceso` (Q22) y la lista blanca de Q04.
