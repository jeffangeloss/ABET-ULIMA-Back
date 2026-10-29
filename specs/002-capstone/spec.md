# Feature Specification: Proyectos de Capstone en la base, tabla maestra en el formato nuevo y R-17 con la hoja «Cursos Capstone»

**Feature Branch**: `docs/002-capstone` (PR a `develop`)
**Created**: 2026-10-29
**Status**: Borrador, pendiente de aprobación de Jefferson
**Input**: Jefferson adjunta «Plantilla Proyectos - Copy.xlsx» y «Tabla_Maestra_PI - Capstone - Nuevo Formato.xlsx» con «Considerar estos por favor» (2026-10-28 y 2026-10-29). A la pregunta «¿Capstone va en una spec 002 aparte o lo meto en el corte 1?» responde «Spec 002 aparte», con la opción «Escribe una spec 002 de Capstone aparte, con historias auditadas desde estos dos Excel, sin frenar el corte 1».

## Épica

> **EP-02. Proyectos de Capstone desde la base.** Hoy los datos de proyecto de un curso Capstone (grupo, título, tipo de empresa, RUC, organización y línea de investigación) viven en una plantilla de Excel aparte del export de Blackboard, la tabla maestra de Capstone se arma a mano en un formato nuevo y el R-17 del MVP solo sale con la hoja «Cursos de Carrera», porque la spec 001 deja fuera la hoja «Cursos Capstone» y la marca del tipo de curso. El sprint permite que el profesor de una sección Capstone de Ingeniería Ambiental suba, después de su export, la plantilla de proyectos, que la base la guarde unida a los estudiantes del export en una sola transacción, que la tabla maestra la muestre en el formato nuevo y que el R-17 salga con la hoja «Cursos Capstone», todo desde la base. Va después del corte 1 de la spec 001 y no lo frena.

Convenciones de esta spec. Todos los datos son inventados. La sección Capstone de prueba es la 420 de la asignatura 450024 «Proyecto de Ingeniería Aplicada I» en el periodo 2026-2, con los indicadores de desempeño (performance indicators, PI) 1.1, 1.2 y 1.3 del resultado del estudiante (student outcome, SO) 1, porque `abet.asignatura_so` solo asocia a 450024 los SO 1 y 7 con el instrumento «Proyecto» y `fk_plan_medicion_asig_so` impide otros. Sus códigos de estudiante van de 99000101 a 99000111, y la sección 421 de la misma asignatura usa 99000112 a 99000122 para que la consulta de control Q08 no vea a un estudiante en dos secciones del mismo curso. La sección de carrera es la 410 de 450002 de la spec 001. Los correos de prueba son `docente420@example.invalid`, `docente421@example.invalid`, `docente410@example.invalid` y `coordinacion@example.invalid`. Los RUC (registro único de contribuyentes) inventados empiezan con 20999, cumplen el dígito verificador módulo 11 y no corresponden a ninguna organización real, y los dos RUC de rechazo (20123456781 y 10999999991) fallan ese dígito, así que tampoco pueden ser de una organización o una persona real. Lo que no existe en V1_01 a V1_09 va marcado «(V1_10)», «(script de plataforma)» o «(script de datos)». Lo que el redactor decide sin fuente va marcado «(propuesta)», y lo que depende de una decisión técnica abierta de Jefferson se escribe como ejemplo hasta cerrar su J-NN.

Prefijos e identificadores. La épica lleva el prefijo EP, cada historia de usuario US (user story), cada requisito funcional FR (functional requirement) y cada criterio de éxito SC (success criterion). Las 46 candidatas de la auditoría se nombran C-NN y las decisiones del crítico D-A1 a D-A22, y las dos tablas están en `revision-historias.md`. US-NN, FR-NNN y SC-NNN se numeran desde 01 en esta spec, y una historia de la spec 001 se cita siempre con «de la spec 001». Las decisiones abiertas siguen la numeración de la spec 001, desde D-14 para la carrera y desde J-11 para Jefferson, para que cada identificador nombre una sola decisión en el repositorio. Q## es una consulta de control y S01 una consulta de seguimiento de `db/pruebas/pruebas.sql`.

Siglas y términos. API es la interfaz de programación de aplicaciones (application programming interface), FK una clave foránea (foreign key), DNI el documento nacional de identidad, JSON el formato de datos JavaScript Object Notation y PR una solicitud de integración (pull request). Capstone es el curso de proyecto integrador de fin de carrera, el export es el archivo de calificaciones que exporta Blackboard, la plantilla de proyectos es el libro con una fila por estudiante que llena el profesor y la subida es el registro `abet.carga_proyecto` de una plantilla. Production (producción) y Preview (vista previa) son los entornos de Vercel, y la prueba de humo es el recorrido mínimo de punta a punta que confirma que el sistema desplegado responde.

Estructura de los dos Excel, extraída por el integrador sin abrir sus datos, que son reales y no entran al repositorio. La plantilla trae la hoja «Hoja1» con los encabezados CÓDIGO, ALUMNO, GRUPO, TÍTULO DEL PROYECTO, TIPO DE EMPRESA, RUC, NOMBRE DE ORGANIZACIÓN y LÍNEA DE INVESTIGACIÓN, una fila por estudiante y la lista auxiliar EMPRESA, ESTADO y ONG en K3:M5, con RUC de 8 y de 11 dígitos y GRUPO numérico. La tabla maestra de Capstone trae la hoja «Capstone» con una fila por estudiante y PI (33 filas para 11 estudiantes y 3 PI) y las columnas SO, PI, PROFESOR, CÓDIGO DEL ESTUDIANTE, SECCIÓN, CALIFICACIÓN, TÍTULO DEL PROYECTO, GRUPO, TIPO DE EMPRESA, RUC, NOMBRE DE ORGANIZACIÓN, LÍNEA DE INVESTIGACIÓN y ARCHIVO.

Cifras de prueba, recalculadas sobre la plantilla inventada de `aceptacion/carga_proyectos.feature` (11 filas en 4 grupos de 3, 3, 3 y 2 integrantes, encabezado en la fila 1 y datos en las filas 2 a 12, propuesta).

| Plantilla | Leídas / aceptadas / rechazadas | Estado | Aviso ESTUDIANTE_SIN_PROYECTO | Tabla maestra Capstone |
| --- | --- | --- | --- | --- |
| `plantilla_proyectos_inventada_420.xlsx` | 11 / 11 / 0 | PUBLICADA | ninguno | 33 filas con los seis datos de proyecto |
| Copia con 99000113 en la fila 4 | 11 / 10 / 1 | PUBLICADA | cuenta 1 | 33 filas, 3 de ellas con proyecto nulo |
| Copia sin las filas 11 y 12 | 9 / 9 / 0 | PUBLICADA | cuenta 2 | 33 filas, 6 de ellas con proyecto nulo |
| Copia con otro título en la fila 7 | 11 / 8 / 3 | PUBLICADA | cuenta 3 | 33 filas, 9 de ellas con proyecto nulo |
| Copia con «COOPERATIVA» en las 11 filas | 11 / 0 / 11 | RECHAZADA | sin subida publicada | 33 filas con proyecto nulo |
| Copia con 10000004 en la fila 4 (generada en `tmp_path`) | sin subida | 422 antes de escribir | ninguno | sin cambio |

Los escenarios Gherkin viven en un solo lugar, `specs/002-capstone/aceptacion/*.feature`, en español (`# language: es`), y los pasos de `tests/aceptacion/pasos/` los leen desde esa carpeta con `scenarios()` de pytest-bdd, como en la spec 001. Son cuatro archivos, `base_capstone.feature` (US-01, US-02 y US-24), `carga_proyectos.feature` (US-03 a US-18 y US-25), `evidencia_capstone.feature` (US-19 a US-22) y `secciones_capstone.feature` (US-23), con 83 escenarios que pasan el parser oficial de Gherkin. Cada escenario lleva `@US-NN` y `@corte1` o `@corte2`. Cuando un texto literal de la API difiere entre esta spec y un `.feature`, manda el del `.feature`, porque es la prueba. Las pruebas de aceptación corren siempre contra un PostgreSQL 16 desechable.

## User Scenarios & Testing *(mandatory)*

### US-01: Marcar las asignaturas Capstone en el plan de estudios (Priority: P1)

Como administrador técnico, quiero que la base distinga las asignaturas Capstone de las de carrera en el plan de estudios para que la subida de proyectos, la tabla maestra y el R-17 elijan su formato sin una lista escrita en el programa.

**Why this priority**: sin la marca del tipo de curso no hay zona de plantilla, ni hoja «Cursos Capstone», ni tabla maestra de Capstone, y la spec 001 deja esa marca fuera de su alcance.

**Independent Test**: tras aplicar V1_10 sobre una base con V1_01 a V1_09, `abet.plan_estudios` conserva sus 53 filas de AMB-2026 con `tipo_curso` «CARRERA», un valor «TESIS» falla por `ck_plan_estudios_tipo_curso` y Q01 a Q14 siguen en 0 filas.

**Base**: `abet.plan_estudios.tipo_curso` varchar(8) NOT NULL DEFAULT 'CARRERA' con `ck_plan_estudios_tipo_curso` CHECK IN ('CARRERA', 'CAPSTONE') (V1_10, valor provisional de J-12), sin ninguna asignatura marcada en la migración; la marca de 450024 y 450026 como CAPSTONE solo en `db/datos/periodo_2026_2_inventado.sql` (script de datos, valor provisional de D-14); `abet.archivo_origen.tipo_fuente` ampliada a varchar(20), `ck_archivo_origen_tipo` con PLANTILLA_PROYECTOS y `uq_archivo_origen_tipo` (archivo_id, tipo_fuente) (V1_10); las tablas `abet.carga_proyecto`, `abet.proyecto_estudiante` y `abet.rechazo_proyecto` de FR-003 a FR-005 (V1_10); `abet.asignatura` (450024 y 450026), `abet.asignatura_so` (instrumento «Proyecto»); consultas Q01 a Q14.
**Pantalla**: sin pantalla (psql y Flyway).
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/base_capstone.feature`):

1. **V1_10 deja todas las asignaturas como de carrera.** 53 filas de AMB-2026, todas CARRERA, y Q01 a Q14 en 0.
2. **Solo se aceptan los dos tipos de curso (esquema).** CAPSTONE y CARRERA terminan bien y TESIS falla por `ck_plan_estudios_tipo_curso`.
3. **La semilla inventada marca 450024 y 450026 como Capstone con valor provisional.** Las secciones 420 y 421 y el plan con 1.1, 1.2 y 1.3 quedan sembrados.
4. **V1_10 amplía el tipo de fuente y crea las tablas de proyecto.** La carga de la 410 y las 33 filas de `v_tabla_maestra_pi` no cambian y «OTRO» falla por `ck_archivo_origen_tipo`.

---

### US-02: Dar a abet_app solo los permisos de la carga de proyectos (Priority: P1)

Como administrador técnico, quiero que el rol `abet_app` inserte y lea los datos de proyecto, cierre el estado de su subida y no pueda modificarlos ni borrarlos, para mantener en las tablas nuevas el privilegio mínimo de la spec 001.

**Why this priority**: la subida de proyectos no tiene borrado lógico, y sin permisos acotados un error del programa o una cadena de conexión filtrada podría cambiar los datos de proyecto que respaldan un R-17 entregado.

**Independent Test**: con una conexión `abet_app`, una subida completa de la 420 confirma sin error y todo UPDATE sobre `proyecto_estudiante`, DELETE o TRUNCATE sobre las tablas de proyecto y UPDATE sobre `plan_estudios` responde «permission denied».

**Base**: `db/plataforma/neon/crear_rol_app.sql` (script de plataforma) con INSERT y SELECT sobre `carga_proyecto`, `proyecto_estudiante` y `rechazo_proyecto`, SELECT sobre `v_tabla_maestra_capstone`, UPDATE solo de `carga_proyecto (estado, filas_leidas, filas_aceptadas, filas_rechazadas, terminada_en)`, sin privilegios sobre secuencias, porque las columnas GENERATED ALWAYS AS IDENTITY no los piden, y sin UPDATE sobre `plan_estudios`; `db/pruebas/probar_rol_app.sql` con los casos nuevos; el script se repite después de cada `migrate` que recrea una vista `R__`.
**Pantalla**: sin pantalla.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/base_capstone.feature`):

1. **abet_app publica una subida de plantilla.** La transacción confirma y las tres tablas y la vista se leen sin error.
2. **abet_app no modifica ni borra los datos de proyecto (esquema con siete órdenes).** «permission denied» y 11 filas intactas.
3. **abet_app solo actualiza el estado, los conteos y el cierre de una subida.** `has_column_privilege` es falso para `carga_id`, `archivo_id`, `subida_por` y `reemplaza_carga_proyecto_id`.
4. **Los permisos sobreviven a la recreación de las vistas.** SELECT e INSERT verdaderos y DELETE falso tras repetir `crear_rol_app.sql`.

---

### US-03: Subir la plantilla de proyectos de mi sección Capstone (Priority: P1)

Como profesor de un curso Capstone de Ingeniería Ambiental, quiero subir desde mi sección la plantilla de proyectos con el grupo, el título, el tipo de empresa, el RUC, la organización y la línea de investigación de cada estudiante, para que esos datos queden en la base junto con las notas del export y no en un Excel aparte.

**Why this priority**: es el núcleo del pedido de Jefferson y la fuente de la tabla maestra y del R-17 de Capstone.

**Independent Test**: con el export de la 420 publicado, `POST /api/secciones/{seccion_id}/proyectos` con la plantilla inventada responde 201 con 11 / 11 / 0, `abet.proyecto_estudiante` gana 11 filas en 4 grupos y Q01 a Q14 y Q16 a Q20 devuelven 0 filas.

**Base**: `abet.carga` PUBLICADA de la sección como precondición; `abet.archivo_origen` con tipo_fuente PLANTILLA_PROYECTOS, `uq_archivo_origen_sha256` y `ck_archivo_origen_nombre`; `abet.carga_proyecto` (V1_10, FR-003); `abet.proyecto_estudiante` (V1_10, FR-004, valor provisional de J-11); `abet.carga_fila` (`uq_carga_fila_estudiante`); `acceso.usuario_autorizado` para `subida_por`; ruta `POST /api/secciones/{seccion_id}/proyectos`; consultas Q01 a Q14 y Q16 a Q20.
**Pantalla**: P3 Subir export, con la zona «Plantilla de proyectos» solo en secciones Capstone (propuesta), y P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **La plantilla correcta queda publicada entera.** 201 con 11 / 11 / 0, el archivo con su huella, la subida PUBLICADA con su `carga_id`, 11 proyectos y las consultas de control en 0.
2. **El nombre del archivo se guarda sin ruta y los bytes no se conservan.** El nombre de una ruta de Windows queda sin ruta y ninguna columna de `abet` ni de `acceso` es de tipo bytea.

---

### US-04: La plantilla espera al export publicado (Priority: P1)

Como profesor de un curso Capstone, quiero que el sistema me diga que primero debo subir el export cuando intento la plantilla antes, para no perder el archivo en un rechazo sin explicación y saber qué paso sigue.

**Why this priority**: la plantilla se une a los estudiantes del export por la clave foránea hacia `carga_fila`, y sin export publicado la ruta escribiría proyectos huérfanos.

**Independent Test**: con la sección 420 sin carga PUBLICADA, la subida responde 409 con el mensaje de FR-007 y las cuatro tablas de la subida no ganan filas.

**Base**: `abet.carga` y `uq_carga_publicada_por_seccion` para hallar la carga vigente; la API responde antes de abrir la transacción.
**Pantalla**: P3 Subir export.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **Sin export publicado la plantilla no se guarda.** 409 «Suba primero el export de Blackboard de la sección 420. La plantilla de proyectos se une a los estudiantes de ese export.»
2. **Un export solo RECHAZADO no habilita la plantilla.** El mismo 409.

---

### US-05: La plantilla solo entra en secciones Capstone (Priority: P1)

Como profesor, quiero que la plantilla de proyectos solo se acepte en una sección de un curso Capstone, para no guardar datos de proyecto donde la carrera no los mide ni los reporta.

**Why this priority**: un proyecto en una sección de carrera aparecería en la tabla maestra equivocada y obligaría a una hoja del R-17 que esa sección no usa.

**Independent Test**: la subida a la 410 de 450002, de tipo CARRERA, responde 409 con «Esta sección no es de un curso Capstone. No se cargó nada.» y `abet.carga_proyecto` no gana filas.

**Base**: `abet.plan_estudios.tipo_curso` (V1_10) leído en cada petición por la versión del plan de medición de la sección, porque `abet.seccion` no tiene carrera; una sección sin plan de medición recibe el 422 de la spec 001 (propuesta); 409 antes de abrir la transacción; consulta Q18 como vigilancia en la base (valor provisional de J-15).
**Pantalla**: P3 Subir export.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **Una sección de un curso de carrera no recibe plantilla.** 409 y ninguna fila nueva.
2. **El tipo de curso se lee de la base en cada subida.** Con 450024 vuelta a CARRERA, la 420 responde el mismo 409.
3. **Una sección sin plan de medición no recibe plantilla.** 422 «La carrera aún no registra el plan de medición de esta sección.» (propuesta) y ninguna fila nueva.

---

### US-06: Solo el profesor asignado sube la plantilla y ve sus datos (Priority: P1)

Como profesor de un curso Capstone, quiero que solo yo pueda cargar los proyectos de mi sección y que un docente ajeno no lea sus títulos ni sus organizaciones, para que ningún colega cambie ni consulte los datos de mis estudiantes.

**Why this priority**: repite en las rutas nuevas la regla BR-ACCESO-07 y 08 de la spec 001, sin la cual una URL pública escribiría en secciones ajenas.

**Independent Test**: el profesor de la 420 recibe 403 al subir a la 421, el coordinador recibe 403 al subir y 200 al leer, y sin la cookie `abet_sesion` la ruta responde 401.

**Base**: `acceso.docente_seccion` (V1_09); `app/permisos.py` como dueño único de la visibilidad; rutas `POST /api/secciones/{seccion_id}/proyectos`, `GET /api/cargas/{carga_id}` y `GET /api/cargas/{carga_id}/r17.xlsx`; 403 único con «La sección no está a su cargo.».
**Pantalla**: P2 Mis secciones (la zona de proyectos solo en las secciones propias).
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **Un profesor no sube proyectos a una sección que no dicta.** 403 y ninguna fila nueva.
2. **El coordinador no sube la plantilla en este corte.** 403.
3. **Sin sesión la ruta responde 401.**
4. **La constancia y el R-17 Capstone de la 420 solo los ve quien tiene la sección a su alcance (esquema).** 403 para el profesor de la 421 y 200 para el coordinador.

---

### US-07: Un código ajeno al export o repetido deja fuera solo su fila (Priority: P1)

Como profesor de un curso Capstone, quiero que la fila de la plantilla con un código que no está en el export de mi sección, o con un código ya usado en otra fila, quede fuera sin frenar las demás, para corregir un error de digitación sin cargar proyectos de estudiantes ajenos.

**Why this priority**: guardar el proyecto de un código que no está en la medición rompe la trazabilidad del principio III y guarda datos de una persona que el export no respalda.

**Independent Test**: con 99000113 de la 421 en la fila 4, la subida responde 201 con 11 / 10 / 1 y el motivo CODIGO_FUERA_DEL_EXPORT, y un INSERT directo del mismo caso falla por `fk_proyecto_estudiante_carga_fila`.

**Base**: `abet.proyecto_estudiante` con `fk_proyecto_estudiante_carga_fila` (carga_id, estudiante_id) hacia `uq_carga_fila_estudiante` y `pk_proyecto_estudiante` (carga_proyecto_id, estudiante_id) (V1_10); `abet.rechazo_proyecto` con los motivos CODIGO_FUERA_DEL_EXPORT y CODIGO_DUPLICADO y efecto RECHAZA_FILA; `abet.estudiante` sin filas nuevas, porque la plantilla nunca crea estudiantes.
**Pantalla**: P4 Resultado de la carga, tabla de rechazos con fila, columna y motivo.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **Un código que no está en el export de la sección rechaza solo su fila (esquema con 99000113 y 99000199).** 201 con 11 / 10 / 1, el aviso con la cuenta 1 y ningún código repetido en la respuesta.
2. **La base impide un proyecto de un estudiante ajeno al export aunque el programa falle.** Falla por `fk_proyecto_estudiante_carga_fila`.
3. **Un código repetido rechaza su segunda aparición.** La fila 9 queda fuera con CODIGO_DUPLICADO y la fila 5 queda aceptada.
4. **La base no guarda dos proyectos del mismo estudiante en una subida.** Falla por `pk_proyecto_estudiante`.

---

### US-08: Un dato de proyecto vacío, demasiado largo o un grupo inválido rechaza la fila (Priority: P1)

Como profesor de un curso Capstone, quiero que el sistema me indique qué dato falta o no sirve en qué fila, para completar la plantilla y no publicar proyectos a medias.

**Why this priority**: un proyecto sin título, sin organización o con un grupo inválido deja la tabla maestra y el R-17 con celdas que nadie puede interpretar.

**Independent Test**: con la celda RUC de la fila 6 vacía, la subida responde 201 con 11 / 10 / 1 y un rechazo CAMPO_VACIO con la columna RUC y sin el valor de ninguna celda.

**Base**: `abet.proyecto_estudiante` con columnas NOT NULL, `ck_proyecto_grupo` (grupo >= 1), `ck_proyecto_titulo`, `ck_proyecto_organizacion` y `ck_proyecto_linea` (texto sin espacios sobrantes y no vacío) y largos de 300, 200 y 120 caracteres (V1_10, valor provisional de D-21); `abet.rechazo_proyecto` con CAMPO_VACIO, GRUPO_INVALIDO y TEXTO_DEMASIADO_LARGO, efecto RECHAZA_FILA, que guardan el nombre del encabezado y nunca el valor (valor provisional de D-18).
**Pantalla**: P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **Una celda obligatoria vacía rechaza la fila completa (esquema con las siete columnas obligatorias).** CAMPO_VACIO y «Fila 6, falta el dato de <columna>. La fila completa queda fuera.»
2. **Un grupo que no es un entero positivo rechaza la fila (esquema con 0, -1, 1,5 y «A»).** GRUPO_INVALIDO y «Fila 6, el grupo debe ser un número entero mayor o igual que 1.»
3. **Un texto que supera su límite rechaza la fila sin recortarlo (esquema con 301, 201 y 121 caracteres).** TEXTO_DEMASIADO_LARGO.

---

### US-09: El tipo de empresa admite solo EMPRESA, ESTADO u ONG (Priority: P1)

Como coordinador, quiero que TIPO DE EMPRESA solo admita EMPRESA, ESTADO u ONG, la lista auxiliar de la plantilla, para que la tabla maestra agrupe los proyectos por un valor que la base controla y no por texto libre.

**Why this priority**: el formato nuevo de la tabla maestra agrupa por tipo de empresa, y una variante de escritura parte un mismo tipo en dos.

**Independent Test**: con «COOPERATIVA» en las dos filas del grupo 4 la subida responde 201 con 11 / 9 / 2 y TIPO_EMPRESA_INVALIDO, y con « ong » guarda «ONG».

**Base**: `abet.proyecto_estudiante.tipo_empresa` varchar(7) con `ck_proyecto_tipo_empresa` CHECK IN ('EMPRESA', 'ESTADO', 'ONG') (V1_10, valor provisional de D-20), sin tabla catálogo; la comparación ignora mayúsculas y espacios y guarda la forma canónica (propuesta); `ck_carga_proyecto_publicable`, que deja RECHAZADA una subida sin filas aceptadas; la lista K3:M5 no se lee como dato, porque el lector toma las columnas por su encabezado.
**Pantalla**: P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **El tipo de empresa del grupo 4 dentro y fuera de la lista (esquema).** ESTADO, «empresa» y « ong » se aceptan en su forma canónica y «COOPERATIVA» rechaza las dos filas.
2. **La forma canónica se compara antes que la consistencia del grupo.** « ong » y «ONG» en un mismo grupo no lo parten.
3. **El mensaje del tipo de empresa no repite la celda.** «Fila 11, el tipo de empresa debe ser EMPRESA, ESTADO u ONG.»
4. **Una plantilla sin ninguna fila aceptada queda rechazada.** 201 con estado RECHAZADA y 11 / 0 / 11.
5. **La lista auxiliar K3:M5 no se lee como estudiantes.** Una copia con dos filas da 2 leídas y el aviso con la cuenta 9.
6. **La base rechaza un tipo de empresa fuera de la lista aunque el programa falle.** Falla por `ck_proyecto_tipo_empresa`.

---

### US-10: El RUC se acepta solo con forma de persona jurídica (Priority: P1)

Como profesor de un curso Capstone, quiero saber qué filas traen un RUC que no tiene 11 dígitos con el prefijo 20, o que es de una persona natural, para corregirlo antes de que la organización quede mal registrada, sin que la base guarde un RUC que contiene un DNI.

**Why this priority**: la copia de la plantilla trae RUC de 8 dígitos, que tienen la forma de un DNI, y un RUC de prefijo 10 contiene el DNI de una persona natural, así que el principio II exige no guardarlos.

**Independent Test**: con «10999999991» en las filas 11 y 12 la subida responde 201 con RUC_PERSONA_NATURAL en las dos filas sin repetir el valor, y un INSERT directo del mismo RUC falla por `ck_proyecto_ruc`.

**Base**: `abet.proyecto_estudiante.ruc` varchar(11) con `ck_proyecto_ruc` CHECK (ruc ~ '^20[0-9]{9}$') (V1_10, valor provisional de D-19); motivos RUC_FORMATO_INVALIDO y RUC_PERSONA_NATURAL con efecto RECHAZA_FILA; el lector toma la celda como texto aunque Excel la entregue como número, sin perder ceros ni recibir notación científica; sin dígito verificador en este sprint (D-19), con todos los RUC de aceptación que lo cumplen.
**Pantalla**: P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **Un RUC que no tiene la forma de persona jurídica rechaza las filas del grupo (esquema con seis valores).** RUC_PERSONA_NATURAL para el prefijo 10 y RUC_FORMATO_INVALIDO para los demás.
2. **Los mensajes del RUC no repiten el valor leído (esquema).** «Fila 11, RUC, no corresponde a una organización.» y «Fila 11, el RUC debe tener 11 dígitos y empezar con 20.»
3. **Un RUC que Excel entrega como número se lee como texto (esquema con entero y decimal).** Se guarda «20999999931».
4. **La base rechaza un RUC de persona natural aunque el programa falle.** Falla por `ck_proyecto_ruc`.

---

### US-11: Un grupo con datos distintos entre sus integrantes se rechaza entero (Priority: P2)

Como profesor de un curso Capstone, quiero que el sistema me avise cuando integrantes de un mismo grupo traen título, tipo de empresa, RUC, organización o línea de investigación distintos, para que un proyecto no aparezca en la tabla maestra con dos identidades.

**Base**: regla del lector sobre las filas que pasan las comprobaciones por fila, con el grupo entero rechazado y sin regla de mayoría (valor provisional de D-22); motivo GRUPO_INCONSISTENTE con efecto RECHAZA_FILA en cada fila del grupo y la columna del primer campo que difiere; consulta de control Q19 como respaldo en la base (valor provisional de J-11).
**Pantalla**: P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **Un integrante con otro título deja fuera a todo su grupo.** 201 con 11 / 8 / 3, las filas 5, 6 y 7 con GRUPO_INCONSISTENTE, el mensaje «Fila 5, el grupo 2 trae datos de proyecto distintos entre sus integrantes. El grupo completo queda fuera.» y Q19 en 0.
2. **Un grupo de dos integrantes con RUC distintos se rechaza entero.** 11 / 9 / 2 y ninguna fila del grupo 4.

---

### US-12: Un estudiante del export sin proyecto queda a la vista (Priority: P2)

Como profesor de un curso Capstone, quiero ver cuántos estudiantes del export no aparecen en la plantilla, para completarla antes de que la tabla maestra y el R-17 salgan con datos de proyecto en blanco.

**Base**: `abet.carga_fila` frente a `abet.proyecto_estudiante`; un solo aviso ESTUDIANTE_SIN_PROYECTO con efecto AVISO y `fila_origen` nulo en `abet.rechazo_proyecto`, con la cuenta calculada en la respuesta; consulta de seguimiento S01 (no es de control) que lista por código a los estudiantes de la carga sin fila en la subida PUBLICADA; la plantilla incompleta se publica (valor provisional de D-23).
**Pantalla**: P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **La plantilla con menos estudiantes que el export se publica con aviso.** 201 con 9 / 9 / 0, el aviso con la cuenta 2 y el mensaje «2 estudiantes del export no tienen fila en la plantilla.», y S01 con 2 filas, sin códigos en la respuesta.

---

### US-13: Una plantilla con la estructura equivocada se detiene (Priority: P1)

Como profesor de un curso Capstone, quiero que el sistema detenga un archivo que no es la plantilla de proyectos (falta la hoja, falta o se repite un encabezado, no trae filas o es el export de Blackboard) y me diga qué encontró, para no cargar datos corridos de columna.

**Why this priority**: un encabezado ausente o repetido corre los datos de columna, y una fila con el título en la columna del RUC pasaría como dato válido de otra columna.

**Independent Test**: una copia sin la columna RUC responde 201 con estado RECHAZADA, 0 filas leídas y un solo rechazo ENCABEZADO_AUSENTE con efecto RECHAZA_CARGA.

**Base**: lector de la plantilla en `abet_carga` con la lista fija de los ocho encabezados y la hoja «Hoja1» (propuesta, D-26); motivos PLANTILLA_SIN_HOJA, ENCABEZADO_AUSENTE, ENCABEZADO_REPETIDO y ARCHIVO_SIN_FILAS con efecto RECHAZA_CARGA; 422 sin rastro para un archivo ilegible y para una huella ya registrada como export, como US-11 de la spec 001.
**Pantalla**: P3 Subir export, zona «Plantilla de proyectos», y P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **Una estructura inválida rechaza la subida entera (esquema con cinco archivos).** 201 RECHAZADA con 0 / 0 / 0 y un solo rechazo RECHAZA_CARGA.
2. **Un archivo que no es una plantilla legible se detiene sin rastro (esquema).** 422 con «El archivo ya está registrado como export de Blackboard. No se cargó nada.» o «No se pudo abrir el archivo. No se cargó nada.»

---

### US-14: La columna ALUMNO se lee para validar y no se guarda (Priority: P1)

Como coordinador, quiero que la columna ALUMNO de la plantilla no llegue a ninguna tabla, respuesta ni registro, para que la base solo tenga códigos de estudiante, como con Last Name y First Name del export.

**Why this priority**: la plantilla real trae nombres de estudiantes, y el principio II y FR-018 de la spec 001 prohíben guardarlos.

**Independent Test**: tras subir la plantilla inventada, la búsqueda de «Estudiante Ficticio» en las columnas de texto de `abet` y `acceso` devuelve 0 coincidencias y Q04 ampliada devuelve 0 filas.

**Base**: el lector comprueba que el encabezado ALUMNO existe y descarta la columna; `abet.proyecto_estudiante` sin columna de nombre y con `organizacion` en lugar de `nombre_organizacion`; consulta Q04 de `pruebas.sql` y de `controles_neon.sql` con «alumno» en su patrón y `carga_proyecto`, `proyecto_estudiante` y `rechazo_proyecto` en su filtro de `%nombre%`; búsqueda de contenido con `information_schema.columns` y `query_to_xml`.
**Pantalla**: P3 Subir export, con el rótulo «La columna ALUMNO no se guarda» (propuesta).
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **Ningún nombre de la plantilla llega a la base ni a las respuestas.** 0 coincidencias en la base, en la respuesta y en el registro.
2. **Q04 ampliada ve una columna de nombre añadida a las tablas de proyecto.** 1 fila con `proyecto_estudiante` y `nombre_alumno`.
3. **Un rechazo de la plantilla no repite el nombre del alumno.** Sin campos «valor» ni «valor_leido».

---

### US-15: La guardia de datos inventados cubre la plantilla (Priority: P1)

Como Jefferson, responsable del piloto, quiero que la guardia de datos inventados rechace toda plantilla con un código de estudiante o un RUC que no sea inventado, para que la plantilla real, que trae códigos y nombres reales, no llegue nunca a Neon durante el piloto.

**Why this priority**: la copia de la plantilla que entrega la carrera trae datos que parecen reales, y la guardia de la spec 001 solo mira el export.

**Independent Test**: con `GUARDIA_DATOS_INVENTADOS=1`, una copia con 10000004 en la fila 4 responde 422 con el mensaje de la spec 001 sin el código, y las cuatro tablas de la subida no ganan filas.

**Base**: `GUARDIA_DATOS_INVENTADOS` del Back, evaluada antes de escribir y sin campo de la petición que la apague, solo sobre los valores que ya tienen la forma válida (un código de 8 dígitos y un RUC que cumple `^20[0-9]{9}$`), de modo que una celda vacía o mal formada sigue a las reglas por fila de US-08 y US-10 aunque la guardia esté encendida; `db/plataforma/neon/guardia_datos_inventados.sql` con `ck_proyecto_ruc_inventado` CHECK (ruc ~ '^20999[0-9]{6}$') solo en Neon (script de plataforma), probado con `db/pruebas/probar_guardia.sql`; el código no inventado tampoco entra a la base por `fk_proyecto_estudiante_carga_fila`, porque `ck_estudiante_codigo_inventado` ya protege `abet.estudiante`. La guardia no reconoce un título ni una organización reales, así que el control del RUC es adicional y no una garantía.
**Pantalla**: P3 Subir export, con el rótulo «Solo plantillas con códigos y RUC inventados» (propuesta).
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **Una plantilla con un código que no es inventado se detiene entera.** 422 «El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada.»
2. **Una plantilla con un RUC que no es inventado se detiene entera.** 422 «El piloto solo admite RUC inventados. Revise la fila 11. No se guardó nada.» (propuesta).
3. **Ningún campo de la petición apaga la guardia de la plantilla.** Mismo 422, como US-08 de la spec 001.
4. **La base de Neon rechaza un RUC que no es inventado aunque el programa falle.** Falla por `ck_proyecto_ruc_inventado`.

---

### US-16: Subir otra vez la misma plantilla no duplica nada (Priority: P2)

Como profesor de un curso Capstone, quiero que subir dos veces la misma plantilla me devuelva la constancia ya existente, para que un reintento o un doble clic no genere dos subidas ni un error 500.

**Base**: `uq_archivo_origen_sha256`, que es global y haría fallar un reintento; índice único parcial `uq_carga_proyecto_publicada_por_carga` sobre `carga_proyecto (carga_id)` WHERE estado = 'PUBLICADA' (V1_10); la API busca la huella antes de escribir, con la regla de FR-012 de la spec 001; una huella con solo subidas RECHAZADA reutiliza su `archivo_id`.
**Pantalla**: P3 Subir export y P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **El mismo archivo en la misma sección devuelve la constancia existente.** 200 sin filas nuevas.
2. **El mismo archivo ya publicado en otra sección se detiene antes de escribir.** 409 «Este archivo ya está publicado en otra sección. No se cargó.»
3. **Otra plantilla distinta no pisa la publicada.** 409 «La sección 420 ya tiene una plantilla de proyectos publicada. No se cargó el archivo.»

---

### US-17: Un fallo a mitad de la carga de proyectos no deja nada escrito (Priority: P1)

Como profesor de un curso Capstone, quiero que un error de conexión o de la base durante la carga de la plantilla no deje proyectos a medias, para que la tabla maestra y el R-17 nunca muestren una sección con la mitad de sus proyectos.

**Why this priority**: es el principio III de la constitución aplicado a la segunda subida de la sección.

**Independent Test**: con un fallo inyectado después de la sexta fila de `proyecto_estudiante`, la API responde 500 con el texto de la sección 6 del contrato y las cuatro tablas no ganan filas.

**Base**: una sola transacción de psycopg 3 con `prepare_threshold=None`, como FR-012 de la spec 001; `archivo_origen`, `carga_proyecto`, `proyecto_estudiante` y `rechazo_proyecto`; `ck_proyecto_ruc` como causa del fallo inyectado; el registro guarda el SQLSTATE y el nombre de la restricción, nunca el DETAIL.
**Pantalla**: P4 Resultado de la carga (mensaje de error).
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **Un fallo en cualquier punto no deja nada escrito (esquema con cuatro puntos).** 500 «La carga no se completó y no se guardó ningún dato. Intente de nuevo.» y ninguna subida EN_CURSO.
2. **Una restricción violada al final deshace todo.** `ck_proyecto_ruc`, 500 y el registro sin el DETAIL.

---

### US-18: Recibir la constancia de la plantilla como evidencia (Priority: P1)

Como profesor de un curso Capstone, quiero recibir la constancia de la plantilla con su huella, sus conteos y sus rechazos por fila, columna y motivo, para demostrar que mis datos de proyecto se subieron y quedaron en la base sin que la constancia repita ningún título, organización ni RUC.

**Why this priority**: es la evidencia que Jefferson pide para el export en la spec 001, extendida a la segunda subida.

**Independent Test**: tras subir la copia con 99000113 en la fila 4, `GET /api/cargas/{carga_id}` trae el bloque `proyectos` con 11 / 10 / 1, la huella igual a `shasum -a 256` y el rechazo sin valor.

**Base**: `abet.carga_proyecto`, `abet.archivo_origen` y `abet.rechazo_proyecto`; `acceso.usuario_autorizado` para el correo de `subida_por`; bloque `proyectos` en la respuesta de `GET /api/cargas/{carga_id}`, igual al cuerpo del 201 de la subida (valor provisional de J-14); horas con `clock_timestamp()` y en hora de Lima.
**Pantalla**: P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **La constancia de la plantilla trae huella, conteos y rechazos sin valores.** Bloque con 11 / 10 / 1, `estudiantes_con_proyecto` 10 y horas con «-05:00».
2. **La constancia de una sección sin plantilla trae el bloque vacío.** Estado SIN_PLANTILLA (propuesta).

---

### US-19: Descargar el R-17 de una sección Capstone con la hoja «Cursos Capstone» (Priority: P1)

Como profesor de una sección Capstone de Ingeniería Ambiental, quiero descargar el R-17 con la hoja «Cursos Capstone» de la plantilla institucional llena desde la base, para entregar la evidencia de mi sección en el formato de mi tipo de curso, con los datos de proyecto de cada estudiante junto con sus niveles por PI.

**Why this priority**: es el tercer resultado del objetivo del sprint y la pieza que la spec 001 deja fuera de su alcance.

**Independent Test**: con el export y la plantilla de la 420 publicados, `GET /api/cargas/{carga_id}/r17.xlsx` devuelve un libro con «Cursos Capstone» y «Constancia», sin «Cursos de Carrera», con 33 filas cuyos datos de proyecto son iguales a los de la base.

**Base**: `abet.v_r17_por_pi` con `tipo_curso` al final desde `abet.plan_estudios` (R__, J-12); `abet.medicion`, `abet.proyecto_estudiante` de la subida PUBLICADA y `abet.carga_proyecto`; plantilla vaciada `plantillas/R017_ambiental_capstone.xlsx` desde la hoja «Cursos Capstone» de «Plantilla Base - Final.xlsx» (B5:P272, 43 rangos combinados, logotipo y rótulos del bloque III en B48:L48), con el mapa de celdas de D-25 y D-08 de la spec 001; la ruta existente `GET /api/cargas/{carga_id}/r17.xlsx` elige la hoja por `tipo_curso`; la hoja «Constancia» lleva la huella del export y la de la plantilla; el Back no escribe en celdas de rótulos.
**Pantalla**: P4 Resultado de la carga, botón «Descargar R-17».
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/evidencia_capstone.feature`):

1. **El R-17 de una sección Capstone usa la hoja Capstone con los datos de proyecto.** 33 filas iguales a la base, bloque II igual a `v_r17_por_pi`, sin «=», sin `#REF!`, sin nombres y con el logotipo.
2. **La hoja Constancia lleva las dos huellas y el conteo de proyectos sin valores.** «10 de 11 estudiantes con datos de proyecto».
3. **Un curso de carrera sigue saliendo con su hoja de siempre.** La 410 sale con «Cursos de Carrera» y 63,6 %, 63,6 % y 72,7 %.
4. **La vista del R-17 distingue la sección de carrera de la Capstone.** `tipo_curso` CARRERA en la 410 y CAPSTONE en la 420.

---

### US-20: El R-17 Capstone sin plantilla sale con aviso (Priority: P2)

Como profesor de una sección Capstone, quiero que el R-17 salga con las columnas de proyecto vacías y un aviso cuando todavía no subo la plantilla o cuando le faltan estudiantes, para no bloquear la evidencia de los niveles y para que nadie confunda un campo vacío con un dato omitido en la base.

**Base**: `abet.carga_proyecto` sin subida PUBLICADA o con estudiantes de `carga_fila` sin fila en `proyecto_estudiante`; franja bajo el título de «Cursos Capstone» con «SIN DATOS DE PROYECTO» o «SIN DATOS DE PROYECTO PARA 2 DE 11 ESTUDIANTES» y sufijo `_SIN_PROYECTOS` solo sin plantilla (propuesta, valor provisional de D-24).
**Pantalla**: P4 Resultado de la carga.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/evidencia_capstone.feature`):

1. **El R-17 Capstone sin plantilla de proyectos sale con aviso.** 200, franja, seis columnas vacías en 33 filas y «0 de 11 estudiantes con datos de proyecto».
2. **El R-17 con una plantilla incompleta avisa cuántos faltan.** Franja con «PARA 2 DE 11 ESTUDIANTES» y nombre sin el sufijo.

---

### US-21: Obtener la tabla maestra de Capstone en el formato nuevo (Priority: P1)

Como coordinador, quiero que la base entregue la tabla maestra de Capstone con las columnas del formato nuevo, para alimentar Power BI y revisar los proyectos de cada sección sin armar el Excel a mano.

**Why this priority**: la tabla maestra en el formato nuevo es el segundo resultado del objetivo del sprint y viene del segundo Excel del pedido.

**Independent Test**: con el export y la plantilla de la 420 publicados, `abet.v_tabla_maestra_capstone` devuelve 33 filas con las 13 columnas del formato nuevo en su orden y los datos de proyecto repetidos en las tres filas de cada estudiante.

**Base**: `abet.v_tabla_maestra_capstone` (migración repetible `R__vista_tabla_maestra_capstone.sql`, con `security_barrier`) sobre las tablas base `medicion`, `carga_columna`, `carga`, `seccion`, `plan_medicion`, `plan_estudios`, `pi`, `estudiante` y `archivo_origen`, sin depender de otra vista; LEFT JOIN a `proyecto_estudiante` de la subida PUBLICADA de la carga; solo cargas PUBLICADAS de asignaturas CAPSTONE; PROFESOR nulo como en `v_tabla_maestra_pi` (D-17); ARCHIVO con el nombre del export (D-16); AÑO, CICLO, CÓDIGO DEL CURSO, CURSO, CICLO DEL CURSO y ESTADO DE EVIDENCIA fuera del formato de la muestra (D-16); GRANT SELECT a `abet_app` y a los roles de lectura del callback.
**Pantalla**: sin pantalla (psql y Power BI).
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/evidencia_capstone.feature`):

1. **La tabla maestra Capstone trae una fila por estudiante y PI con su proyecto.** 33 filas, columnas en su orden, PROFESOR nulo y todo RUC con prefijo 20.
2. **Un estudiante sin proyecto sale con las seis columnas vacías y no desaparece.**
3. **Lo que no está vigente no duplica filas (esquema con la carga y la subida reemplazadas).** 33 filas y no 66.
4. **Un curso de carrera no entra en la vista Capstone.**
5. **La vista Capstone no expone columnas de nombre de persona.** Y lleva `security_barrier=true`.

---

### US-22: La tabla maestra tradicional y la vista del R-17 no cambian (Priority: P2)

Como analista de Power BI, quiero que `abet.v_tabla_maestra_pi` conserve sus columnas, sus filas y su significado, y que `abet.v_r17_por_pi` solo sume una columna al final, para que el reporte tradicional no se rompa cuando entren los cursos Capstone.

**Base**: `abet.v_tabla_maestra_pi` (`R__vista_tabla_maestra_pi.sql`) sin cambios, que ya incluye las secciones Capstone porque solo filtra cargas PUBLICADAS (valor provisional de D-16); `abet.v_r17_por_pi` con `tipo_curso` como última columna; las dos son `R__`, así que Flyway las recrea con DROP VIEW ... CASCADE y `crear_rol_app.sql` se repite después.
**Pantalla**: sin pantalla.
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/evidencia_capstone.feature`):

1. **Las columnas de la vista tradicional no cambian.** Las 13 columnas en su orden.
2. **Las filas de la 410 no cambian con V1_10.** EXCEPT en los dos sentidos da 0 filas.
3. **Un estudiante Capstone aparece en las dos vistas con la misma calificación.** CALIFICACIÓN 3 en ambas.
4. **La vista del R-17 conserva sus columnas y suma el tipo de curso al final.**

---

### US-23: Ver el estado de proyectos de mis secciones (Priority: P2)

Como profesor de varias secciones Capstone, quiero ver en mi lista de secciones si cada una tiene su export, su plantilla y cuántos estudiantes tienen proyecto, para saber qué me falta subir.

**Base**: `GET /api/secciones` (existente) con los campos nuevos `tipo_curso`, `proyectos_estado` (NO_APLICA, SIN_EXPORT, PENDIENTE y PUBLICADA), `carga_proyecto_id`, `estudiantes_con_proyecto` y `estudiantes_en_export`, que se suman sin quitar ninguno del contrato de la spec 001; una sección con export y con subidas solo RECHAZADA sale PENDIENTE; `acceso.docente_seccion` como filtro de visibilidad.
**Pantalla**: P2 Mis secciones, con «9 de 11 con proyecto» (propuesta).
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/secciones_capstone.feature`):

1. **El estado de proyectos refleja la situación de cada sección (esquema con cinco secciones).** PUBLICADA, PENDIENTE, SIN_EXPORT, PENDIENTE y NO_APLICA.
2. **La sección con plantilla completa trae sus conteos.** 11 y 11, con los campos de la spec 001 intactos.
3. **La sección con plantilla incompleta muestra cuántos faltan.** 9 y 11.
4. **Las secciones sin datos de proyecto traen los conteos nulos.**
5. **El coordinador ve el estado de proyectos de toda la carrera.**
6. **Una sección sin plan de medición no tiene tipo de curso.** `tipo_curso` nulo y `proyectos_estado` NO_APLICA (propuesta).

---

### US-24: Vigilar los datos de proyecto con consultas de control (Priority: P1)

Como administrador técnico, quiero consultas de control que encuentren subidas y proyectos incoherentes, para detectar un fallo de carga antes de entregar la tabla maestra y el R-17 de Capstone.

**Why this priority**: el proyecto vigila sus invariantes con Q01 a Q14, y las reglas que no tienen restricción en la base (estado de la carga del export, consistencia del grupo y tipo de curso) solo las ve una consulta.

**Independent Test**: con la 420 coherente, Q01 a Q14 y Q16 a Q20 devuelven 0 filas, y cada anomalía armada en una transacción que se deshace la ve solo su consulta.

**Base**: consultas Q16 a Q20 de FR-021 en `db/pruebas/pruebas.sql` (`control_cero`) y en `db/plataforma/neon/controles_neon.sql`, cada una con su sondeo en una transacción que se deshace; la prueba de paridad de `pruebas.sql` pasa de Q01 a Q14 a Q01 a Q14 y Q16 a Q20; Q15 sigue siendo la de la spec 001; S01 es de seguimiento y no de control.
**Pantalla**: sin pantalla (salida de `controles_neon.sql` en solo lectura con `abet_respaldo`).
**Corte**: 1.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/base_capstone.feature`):

1. **Una base Capstone coherente deja las consultas de control en cero.**
2. **Cada anomalía la ve su consulta (esquema con Q16 a Q20).**
3. **Un estudiante del export sin proyecto no es una anomalía.** Q16 a Q20 en 0 y S01 con 2 filas.
4. **Los controles de Neon traen las consultas nuevas iguales a las de las pruebas.**

---

### US-25: Declarar que los textos libres no nombran personas (Priority: P3)

Como coordinador, quiero que el profesor declare en cada subida que los títulos y los nombres de organización no nombran personas, para dejar constancia de un control que ninguna regla automática puede cumplir del todo antes de autorizar datos reales.

**Base**: columnas `carga_proyecto.declaro_sin_personas` boolean y `carga_proyecto.declarado_en` (V1_10, nulas en el corte 1 y exigidas por la API desde el corte 2) con `ck_carga_proyecto_declaracion` (propuesta); campo multipart `declaracion_sin_personas`, que solo admite «true»; sin tabla nueva y sin texto de la declaración en la base; si la declaración basta lo decide D-28.
**Pantalla**: P3 Subir export, casilla de declaración.
**Corte**: 2.

**Acceptance Scenarios** (`specs/002-capstone/aceptacion/carga_proyectos.feature`):

1. **Sin la declaración no se guarda ningún proyecto.** 422 «Confirme que los títulos y nombres de organización no nombran personas.»
2. **La declaración queda registrada en la subida.**
3. **La declaración solo admite el valor true.**

### Edge Cases

- Toda respuesta de error usa `{ "detail": "mensaje" }`. Sin sesión la API responde 401; con sesión y sin permiso sobre la sección o la carga, 403 con «La sección no está a su cargo.», y la respuesta no trae datos de esa sección.
- La API comprueba, en este orden y hasta el primero que falla, la sesión (401), el permiso (403), el tipo de curso (409, o 422 si la sección no tiene plan de medición), el export publicado (409), el tamaño y la legibilidad del archivo (422), la huella ya registrada (200, 409 o 422), la plantilla ya publicada (409), la guardia (422, solo sobre los códigos de 8 dígitos y los RUC con la forma `^20[0-9]{9}$`), la estructura (201 RECHAZADA) y, al final, las reglas por fila y la regla del grupo (FR-009 y FR-010).
- Toda fila rechazada deja a su estudiante sin proyecto, así que también suma al aviso ESTUDIANTE_SIN_PROYECTO.
- Un archivo de más de 1 MB recibe 422 antes de leerse, como en la spec 001.
- Los identificadores GENERATED ALWAYS AS IDENTITY se consumen aunque la transacción se deshaga, así que las pruebas capturan el `carga_proyecto_id` devuelto.
- La plantilla real puede traer el encabezado en otra fila que la 1. El lector busca la fila de los ocho encabezados en las primeras 10 filas de «Hoja1» (propuesta) y numera `fila_origen` con la fila de Excel.
- Un RUC de 8 dígitos de la copia puede ser un DNI, un RUC truncado o un error, y en todos los casos da RUC_FORMATO_INVALIDO sin repetir el valor hasta que D-19 decida otro motivo.
- Una celda numérica de RUC que Excel guarda en notación científica pierde dígitos antes de llegar al lector. El lector la rechaza con RUC_FORMATO_INVALIDO cuando el número no tiene 11 dígitos enteros (propuesta).
- La hoja «Cursos Capstone» tiene filas fijas para la tabla de estudiantes. Una sección que no cabe recibe 422 al pedir el R-17 con «La sección supera las filas de la plantilla del R-17.», como en la spec 001, en lugar de truncar la tabla (el número de filas sale del mapa de T033).
- El reemplazo del export de la spec 001 (US-18, corte 2) en una sección con plantilla PUBLICADA dejaría la subida colgada de una carga REEMPLAZADA, que Q16 marca. Mientras el reemplazo de la plantilla no exista, ese reemplazo responde 409 (valor provisional de J-16).
- La guardia rechaza la plantilla después de recibirla, así que no evita que un archivo real llegue a la función de Vercel. P3 lleva el rótulo de US-15 mientras no exista un lector en el navegador.

## Requirements *(mandatory)*

- **FR-001** `V1_10__crear_proyectos_capstone.sql` (propuesta de nombre) agrega `abet.plan_estudios.tipo_curso` varchar(8) NOT NULL DEFAULT 'CARRERA' con `ck_plan_estudios_tipo_curso`, sin marcar ninguna asignatura, y `pruebas.sql` gana un caso que debe pasar y uno que no por cada restricción nueva.
- **FR-002** V1_10 amplía `abet.archivo_origen.tipo_fuente` a varchar(20), agrega PLANTILLA_PROYECTOS a `ck_archivo_origen_tipo` y crea `uq_archivo_origen_tipo` (archivo_id, tipo_fuente).
- **FR-003** V1_10 crea `abet.carga_proyecto` con `carga_proyecto_id` de identidad, `carga_id`, `seccion_id` y `carrera_id` con FK compuesta hacia `uq_carga_seccion`, `archivo_id` y `tipo_fuente` con CHECK = 'PLANTILLA_PROYECTOS' y FK compuesta hacia `uq_archivo_origen_tipo`, `filas_de_datos` con FK compuesta (archivo_id, filas_de_datos) hacia `uq_archivo_origen_filas`, como `fk_carga_archivo`, `filas_leidas`, `filas_aceptadas`, `filas_rechazadas`, `estado` (EN_CURSO, RECHAZADA, PUBLICADA y REEMPLAZADA), `reemplaza_carga_proyecto_id` nula, `subida_por` hacia `acceso.usuario_autorizado`, `iniciada_en`, `terminada_en`, `declaro_sin_personas` y `declarado_en`, con las restricciones análogas a las de `abet.carga` (`ck_carga_proyecto_filas`, `ck_carga_proyecto_conciliada`, `ck_carga_proyecto_publicable`, `ck_carga_proyecto_terminada`, `ck_carga_proyecto_reemplaza` y `uq_carga_proyecto_reemplaza`) la clave única `uq_carga_proyecto_carga` (carga_proyecto_id, carga_id), que sostiene la FK compuesta de FR-004, y el índice único parcial `uq_carga_proyecto_publicada_por_carga`.
- **FR-004** V1_10 crea `abet.proyecto_estudiante` con `carga_proyecto_id`, `carga_id`, `estudiante_id`, `fila_origen`, `grupo`, `titulo`, `tipo_empresa`, `ruc`, `organizacion` y `linea_investigacion`, `pk_proyecto_estudiante` (carga_proyecto_id, estudiante_id), FK compuesta (carga_proyecto_id, carga_id) hacia la subida, `fk_proyecto_estudiante_carga_fila` (carga_id, estudiante_id) hacia `uq_carga_fila_estudiante` y los CHECK `ck_proyecto_grupo`, `ck_proyecto_titulo`, `ck_proyecto_organizacion`, `ck_proyecto_linea`, `ck_proyecto_tipo_empresa` y `ck_proyecto_ruc`, sin ninguna columna de nombre de persona (valor provisional de J-11).
- **FR-005** V1_10 crea `abet.rechazo_proyecto` con `carga_proyecto_id`, `fila_origen`, `columna` (CHECK sobre los ocho encabezados de la plantilla, nula en el AVISO y en PLANTILLA_SIN_HOJA y ARCHIVO_SIN_FILAS, con el encabezado afectado en ENCABEZADO_AUSENTE y ENCABEZADO_REPETIDO y con un CHECK análogo a `ck_rechazo_fila_con_fila` que la exige en RECHAZA_FILA), `motivo` varchar(30), `efecto` (RECHAZA_FILA, RECHAZA_CARGA y AVISO) y los CHECK análogos a `ck_rechazo_fila_efecto` y `ck_rechazo_fila_con_fila`, sin columna de valor leído (valor provisional de J-13).
- **FR-006** `POST /api/secciones/{seccion_id}/proyectos` recibe la plantilla en el campo multipart `archivo` y escribe archivo, subida, proyectos y rechazos en una sola transacción de psycopg 3 con `prepare_threshold=None`, responde 201 con la constancia de la subida y cierra la subida con `clock_timestamp()`.
- **FR-007** La ruta responde, antes de abrir la transacción, 409 con «Esta sección no es de un curso Capstone. No se cargó nada.» si `plan_estudios.tipo_curso` no es CAPSTONE, 422 con «La carrera aún no registra el plan de medición de esta sección.», el texto de la spec 001, si la sección no tiene filas en `plan_medicion` y el tipo de curso no se puede resolver (propuesta), y 409 con «Suba primero el export de Blackboard de la sección {numero}. La plantilla de proyectos se une a los estudiantes de ese export.» si la sección no tiene carga PUBLICADA.
- **FR-008** La lista única de motivos de `rechazo_proyecto` es CODIGO_FUERA_DEL_EXPORT, CODIGO_DUPLICADO, CAMPO_VACIO, GRUPO_INVALIDO, TEXTO_DEMASIADO_LARGO, TIPO_EMPRESA_INVALIDO, RUC_FORMATO_INVALIDO, RUC_PERSONA_NATURAL y GRUPO_INCONSISTENTE con RECHAZA_FILA; PLANTILLA_SIN_HOJA, ENCABEZADO_AUSENTE, ENCABEZADO_REPETIDO y ARCHIVO_SIN_FILAS con RECHAZA_CARGA; y ESTUDIANTE_SIN_PROYECTO con AVISO.
- **FR-009** La validación por fila rechaza la fila completa ante un código ajeno al export, un código repetido (la segunda aparición), una de las siete celdas obligatorias vacía, un grupo que no es entero mayor o igual que 1, un texto más largo que 300, 200 o 120 caracteres, un tipo de empresa fuera de la lista o un RUC sin la forma `^20[0-9]{9}$`, con los valores provisionales de D-18, D-19, D-20 y D-21.
- **FR-010** Sobre las filas que pasan FR-009, el lector agrupa por GRUPO y rechaza todas las filas de un grupo cuyos integrantes difieren en título, tipo de empresa, RUC, organización o línea de investigación, ya normalizados, con GRUPO_INCONSISTENTE (valor provisional de D-22).
- **FR-011** La subida se publica cuando termina con al menos una fila aceptada y queda RECHAZADA si no acepta ninguna; una estructura inválida deja `filas_leidas` 0 y un solo rechazo RECHAZA_CARGA. `archivo_origen.filas_de_datos` de la plantilla es el número de filas de «Hoja1» bajo la fila del encabezado con algún valor en las ocho columnas que el encabezado ubica, sin mirar otras columnas como K:M, y vale 0 cuando la hoja o el encabezado faltan (propuesta).
- **FR-012** La subida guarda un solo aviso ESTUDIANTE_SIN_PROYECTO cuando algún estudiante de `carga_fila` no tiene fila aceptada, y la respuesta trae su cuenta; la consulta de seguimiento S01 los lista por código y no forma parte de los controles (valor provisional de D-23).
- **FR-013** La columna ALUMNO se comprueba como encabezado y se descarta, y ni la base, ni los registros, ni las respuestas, ni el R-17 guardan o muestran un nombre de estudiante, el valor leído de una celda o la ruta local del archivo, como FR-018 de la spec 001.
- **FR-014** Con `GUARDIA_DATOS_INVENTADOS=1`, la API rechaza con 422 y sin escribir toda plantilla con un código de 8 dígitos que no empieza con 99 o con un RUC que cumple `^20[0-9]{9}$` y no `^20999[0-9]{6}$`. La guardia mira la forma antes de decidir, así que una celda vacía o mal formada no la dispara y recibe el motivo por fila de FR-009 (CAMPO_VACIO, RUC_FORMATO_INVALIDO, RUC_PERSONA_NATURAL o CODIGO_FUERA_DEL_EXPORT), y `guardia_datos_inventados.sql` agrega `ck_proyecto_ruc_inventado` solo en Neon.
- **FR-015** La API busca la huella antes de escribir y responde 200 con la constancia existente si la plantilla está PUBLICADA en la misma sección, 409 si lo está en otra, 422 si la huella es la de un export y 409 si la sección ya tiene otra plantilla PUBLICADA.
- **FR-016** `GET /api/cargas/{carga_id}` suma un bloque `proyectos` con el nombre del archivo, la hoja, las filas de datos, leídas, aceptadas y rechazadas, la huella completa, el estado, `estudiantes_en_export`, `estudiantes_con_proyecto`, los avisos y los rechazos por fila, columna y motivo, el correo de quien sube y las horas en hora de Lima, igual al cuerpo del 201 de FR-006 (valor provisional de J-14).
- **FR-017** `GET /api/cargas/{carga_id}/r17.xlsx` elige la hoja por `v_r17_por_pi.tipo_curso`, llena «Cursos Capstone» desde `plantillas/R017_ambiental_capstone.xlsx` con valores y sin fórmulas, una fila por medición con los seis datos de proyecto de la subida PUBLICADA, la franja y el nombre de US-20 cuando falta la plantilla o algún estudiante, y la hoja «Constancia» con las dos huellas y la línea «N de M estudiantes con datos de proyecto».
- **FR-018** `R__vista_tabla_maestra_capstone.sql` crea `abet.v_tabla_maestra_capstone` con `security_barrier`, como las versiones de `v_tabla_maestra_pi` y `v_r17_por_pi` que llegan a Neon por el subtree de `preparacion-neon` y que `crear_roles_lectura.sql` exige para las vistas de Power BI (`db/README.md`, condiciones de T027), sobre las tablas base, sin depender de otra vista, con las 13 columnas del formato nuevo en su orden y solo cargas PUBLICADAS de asignaturas CAPSTONE, con un LEFT JOIN a la subida PUBLICADA.
- **FR-019** `R__vista_r17_por_pi.sql` suma `tipo_curso` como última columna con un JOIN a `plan_estudios` por la versión de catálogo del plan de medición, y `v_tabla_maestra_pi` no cambia. Las dos `R__` se escriben sobre las versiones del subtree, con `security_barrier`.
- **FR-020** `crear_rol_app.sql` da a `abet_app` INSERT y SELECT sobre las tres tablas de proyecto, SELECT sobre `v_tabla_maestra_capstone` y UPDATE solo de `carga_proyecto (estado, filas_leidas, filas_aceptadas, filas_rechazadas, terminada_en)`, sin DELETE, TRUNCATE ni privilegios de secuencias, y se repite después de cada `migrate` que recrea una vista `R__`. `crear_roles_lectura.sql` y el callback `afterMigrate__permisos_lectura.sql` suman `abet.v_tabla_maestra_capstone` al SELECT de `abet_lectura`, que hereda `powerbi_lectura`, y a la comprobación de `security_barrier`.
- **FR-021** `pruebas.sql` y `controles_neon.sql` suman Q16 (subida PUBLICADA cuya carga no está PUBLICADA), Q17 (subida PUBLICADA o REEMPLAZADA con `filas_aceptadas` distinto de sus filas de `proyecto_estudiante`), Q18 (subida PUBLICADA o REEMPLAZADA en una asignatura que `plan_estudios` no marca CAPSTONE), Q19 (grupo de una subida PUBLICADA con más de un valor en título, tipo de empresa, RUC, organización o línea de investigación) y Q20 (subida REEMPLAZADA sin ninguna que la reemplace), cada una con su sondeo, y la prueba de paridad las incluye.
- **FR-022** Q04 suma «alumno» a su patrón y `carga_proyecto`, `proyecto_estudiante` y `rechazo_proyecto` a su filtro de `%nombre%`, en `pruebas.sql` y en `controles_neon.sql`.
- **FR-023** `GET /api/secciones` suma `tipo_curso`, `proyectos_estado`, `carga_proyecto_id`, `estudiantes_con_proyecto` y `estudiantes_en_export` sin quitar ningún campo del contrato de la spec 001. El tipo de curso se resuelve por `plan_medicion` de la sección, y una sección sin plan trae `tipo_curso` nulo y `proyectos_estado` NO_APLICA (propuesta).
- **FR-024** `db/datos/periodo_2026_2_inventado.sql` siembra las secciones 420 y 421 de 450024, su plan con 1.1, 1.2 y 1.3, la marca CAPSTONE de 450024 y 450026 con el comentario «valor provisional de D-14» y los usuarios `docente420@example.invalid` y `docente421@example.invalid` con sus `docente_seccion`, y se puede repetir sin duplicar; `db/pruebas/datos_sinteticos.sql` arma la sección 420 coherente.
- **FR-025** Los archivos de prueba viven en `tests/datos_inventados/` (el export de la 420 y de la 421, la plantilla inventada y sus copias defectuosas), con códigos que empiezan con 99 y RUC que empiezan con 20999; las copias con un código o un RUC que no es inventado se generan en `tmp_path` y nunca se versionan.
- **FR-026** El contrato `docs/03-api/contrato.md` del Front documenta, antes de implementar, la ruta de la plantilla, el bloque `proyectos`, la elección de hoja del R-17 y los campos nuevos de `GET /api/secciones`, con los textos de esta spec.
- **FR-027** El Front muestra la zona «Plantilla de proyectos» en P3 solo cuando `tipo_curso` es CAPSTONE, el resultado de la subida en P4 y el estado de proyectos en P2, sin mostrar nada que ninguna historia pida.
- **FR-028** Desde el corte 2, la ruta exige el campo `declaracion_sin_personas` igual a «true» y guarda `declaro_sin_personas` y `declarado_en` en la subida.
- **FR-029** Cada cambio de esta funcionalidad actualiza `MEMORIA.md` en el mismo commit y pasa `bash scripts/preflight.sh`.

## Success Criteria *(mandatory)*

- **SC-001** El 100 % de los escenarios del corte 1 de esta spec tiene una prueba que pasa en la integración continua, y cada prueba cubre lo que debe pasar y lo que no.
- **SC-002** Con la plantilla inventada, la subida queda con 11 / 11 / 0 y 11 proyectos, y con la copia con 99000113 en la fila 4, con 11 / 10 / 1 y el aviso con la cuenta 1, sin ninguna diferencia.
- **SC-003** `abet.v_tabla_maestra_capstone` devuelve exactamente 3 filas por estudiante del export de una sección con 3 PI, con o sin plantilla, y `v_tabla_maestra_pi` devuelve las mismas filas antes y después de V1_10.
- **SC-004** En el R-17 Capstone, cada dato de proyecto es igual al de `proyecto_estudiante`, cada porcentaje del bloque II es igual al de `v_r17_por_pi` y ninguna celda empieza por «=» ni contiene `#REF!`.
- **SC-005** En los escenarios de fallo inyectado, de archivo ilegible, de guardia y de 409, el conteo de `archivo_origen`, `carga_proyecto`, `proyecto_estudiante` y `rechazo_proyecto` es el mismo antes y después del envío.
- **SC-006** La búsqueda de los nombres inventados de la columna ALUMNO en las columnas de texto de `abet` y `acceso`, en las respuestas, en el registro y en todas las hojas del R-17 devuelve 0 coincidencias, y Q04 ampliada devuelve 0 filas.
- **SC-007** Ningún mensaje, respuesta ni rechazo repite un código, un RUC, un título, una organización ni un nombre leídos de la plantilla.
- **SC-008** En Neon, `abet.proyecto_estudiante` tiene 0 RUC fuera de `^20999[0-9]{6}$` y un INSERT directo de 20123456781 falla por `ck_proyecto_ruc_inventado`.
- **SC-009** Con el rol `abet_app`, el 100 % de los intentos de UPDATE sobre `proyecto_estudiante`, de DELETE o TRUNCATE sobre las tablas de proyecto y de UPDATE fuera de las columnas permitidas de `carga_proyecto` responde «permission denied».
- **SC-010** Un profesor recibe 403 en el 100 % de las rutas de proyecto, constancia y R-17 de una sección que no dicta, y el coordinador recibe 200 en las de lectura y 403 al subir.
- **SC-011** Q01 a Q14 y Q16 a Q20 devuelven 0 filas en Neon después de V1_10, después de la primera subida de plantilla y después de la prueba de humo.
- **SC-012** La huella de la plantilla en la respuesta y en la hoja «Constancia» es igual a `shasum -a 256` del archivo en el 100 % de las subidas de prueba.
- **SC-013** `bash scripts/preflight.sh` termina sin fallas en cada PR de esta feature, y ningún commit trae `Co-Authored-By` ni firmas de herramientas.

## Decisiones abiertas

De la carrera y de Jefferson como cliente (D). Mientras no se decidan, el sistema aplica el valor provisional, el R-17 conserva la franja PROVISIONAL de la spec 001 y cada valor provisional se nombra con su identificador en el código y en las pruebas.

| ID | Decisión y pregunta abierta | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| D-14 | Qué asignaturas son Capstone. V1_03 trae 450024 «Proyecto de Ingeniería Aplicada I» y 450026 «Proyecto de Ingeniería Aplicada II» sin marca de tipo. ¿Son las dos, solo una u otras más? | Ninguna marcada en la migración; 450024 y 450026 marcadas solo en la semilla inventada | Coordinación de Ambiental |
| D-15 | Qué es el R-18, quién lo emite, qué contiene y si entra en esta spec | Fuera de alcance; el sistema no genera nada del R-18 | Coordinación de Ambiental y Oficina de Calidad |
| D-16 | Si la tabla maestra de 13 columnas omite AÑO, CICLO, CÓDIGO DEL CURSO, CURSO, CICLO DEL CURSO y ESTADO DE EVIDENCIA por recorte de la muestra o por diseño, si reemplaza a la tradicional en Capstone o convive con ella, si la tradicional sigue incluyendo las secciones Capstone, si Power BI necesita esas columnas y si ARCHIVO nombra el export o la plantilla | Vista nueva de 13 columnas que convive con la tradicional; la tradicional sigue incluyendo Capstone; ARCHIVO con el nombre del export | Coordinación de Ambiental |
| D-17 | Si PROFESOR lleva el nombre o el correo del profesor, o el del asesor de cada proyecto, y si Power BI puede mostrarlo (D-12 de la spec 001) | Nulo, como en `v_tabla_maestra_pi` | Coordinación de Ambiental y Oficina de Calidad |
| D-18 | Campos obligatorios de la plantilla. ¿Se rechaza, se acepta con aviso o se admite según el tipo de empresa una fila sin RUC, por ejemplo de un proyecto sin organización externa? | Las siete columnas son obligatorias y una celda vacía da CAMPO_VACIO | Coordinación de Ambiental |
| D-19 | Reglas del RUC. ¿Los RUC de 8 dígitos de la copia son DNI, RUC truncados por Excel o errores? ¿ESTADO y ONG pueden traer otros prefijos legítimos? ¿Se acepta una organización con RUC de persona natural (prefijo 10)? ¿Se verifica el dígito módulo 11? ¿Para qué se guarda el RUC? | Solo 11 dígitos con prefijo 20; el prefijo 10 da RUC_PERSONA_NATURAL y lo demás RUC_FORMATO_INVALIDO; sin dígito verificador, con ejemplos que lo cumplen | Coordinación de Ambiental, con Jefferson por la privacidad |
| D-20 | Si la lista de TIPO DE EMPRESA (EMPRESA, ESTADO y ONG) es cerrada y estable, si admite persona natural, universidad o gremio y quién la mantiene | Lista cerrada por CHECK; ampliarla exige una migración | Coordinación de Ambiental |
| D-21 | Si LÍNEA DE INVESTIGACIÓN es texto libre o un catálogo de la carrera, quién lo mantiene, y los largos máximos de título, organización y línea | Texto libre; 300, 200 y 120 caracteres, sin recortar | Coordinación de Ambiental |
| D-22 | Reglas de GRUPO. ¿Los integrantes de un grupo comparten siempre título, tipo, RUC, organización y línea? ¿El grupo es de la sección o del curso, y puede tener integrantes de dos secciones? ¿Un estudiante puede estar en dos grupos? | Grupo por subida de la sección; un grupo inconsistente se rechaza entero sin mayoría; la segunda aparición de un código da CODIGO_DUPLICADO | Coordinación de Ambiental |
| D-23 | Si un estudiante del export sin fila en la plantilla es un aviso o rechaza la plantilla entera, y si una fila con un código ajeno al export solo rechaza su fila o impide publicar | Aviso ESTUDIANTE_SIN_PROYECTO y la plantilla se publica; el código ajeno rechaza solo su fila | Coordinación de Ambiental |
| D-24 | Si el R-17 Capstone se descarga sin datos de proyecto, con franja, o se bloquea hasta que la plantilla esté cargada | 200 con franja «SIN DATOS DE PROYECTO» y sufijo `_SIN_PROYECTOS` (propuesta) solo sin plantilla | Coordinación de Ambiental y Oficina de Calidad |
| D-25 | Hoja y celdas de «Cursos Capstone». ¿Qué columnas hasta P llena el sistema y cuáles otro proceso (D-08 de la spec 001)? ¿La tabla lleva una fila por estudiante o por estudiante y PI? ¿Se imprime el instrumento «Documento Técnico de Capstone - Capítulo 3» de la hoja o el «Proyecto» de `asignatura_so`? ¿La celda G104 con «A» es un resto de edición? ¿El logotipo se reutiliza tal cual? ¿El R-17 Capstone incluye también «Cursos de Carrera»? | Una fila por medición, las seis columnas de proyecto desde la base, el instrumento de `asignatura_so`, el logotipo conservado, G104 vaciada y solo la hoja «Cursos Capstone» con «Constancia» | Coordinación de Ambiental y Oficina de Calidad |
| D-26 | Forma de llegada de la plantilla. Jefferson decide la plantilla aparte, pero ¿la carrera acepta dos subidas por sección? ¿Puede llegar antes que el export en el futuro? ¿Se sube por tramos o entera? ¿Se identifica la hoja por el nombre «Hoja1» o se toma la primera? | Plantilla aparte, después del export publicado, entera, una PUBLICADA por carga y la hoja «Hoja1» | Coordinación de Ambiental y Jefferson |
| D-27 | Hasta cuándo se reemplaza la plantilla, quién la reemplaza (profesor, coordinador o ambos), depende de D-11 de la spec 001, y cuánto tiempo se conservan los datos de una subida reemplazada | Fuera del sprint; nadie reemplaza la plantilla y nada se borra | Coordinación de Ambiental |
| D-28 | Datos de proyecto reales. ¿Un título o una organización pueden identificar a un estudiante? ¿Requieren la autorización de D-10 de la spec 001? ¿Basta la declaración del profesor de US-25 o hace falta una revisión humana? ¿Se buscan patrones de DNI, correo o teléfono en los textos? ¿La carrera pide conservar la columna ALUMNO, que choca con FR-018 de la spec 001? | Solo datos inventados; ALUMNO se descarta; la declaración llega en el corte 2; ningún patrón en este sprint | Universidad de Lima, Coordinación de Ambiental y Jefferson |
| D-29 | Cuántos PI mide Capstone por curso y si son los mismos en 450024 y 450026 | 450024 mide 1.1, 1.2 y 1.3 con datos inventados; 450026 sin plan | Coordinación de Ambiental |

De Jefferson como dueño técnico (J).

| ID | Decisión | Valor provisional | Alternativa |
| --- | --- | --- | --- |
| J-11 | Granularidad del proyecto | `abet.proyecto_estudiante`, una fila por estudiante como la plantilla, con el grupo inconsistente rechazado en el lector y vigilado por Q19 | Tabla `proyecto` por grupo más `proyecto_integrante`, que la crítica propone (D-A1) y las tres lentes refutan (C-21 y C-22) |
| J-12 | Lugar del tipo de curso | `abet.plan_estudios.tipo_curso`, porque `asignatura` no tiene carrera ni versión | `abet.asignatura.tipo_curso`, como lo nombra la spec 001 |
| J-13 | Tabla de rechazos de la plantilla | `abet.rechazo_proyecto` propia, porque `rechazo_fila` depende de `carga` y de `carga_columna` | Ampliar `abet.rechazo_fila` con una columna de subida |
| J-14 | Ruta de la constancia de la plantilla | Bloque `proyectos` en `GET /api/cargas/{carga_id}` | Ruta propia `GET /api/cargas-proyecto/{id}` |
| J-15 | Garantía de «solo Capstone» en la base | 409 de la ruta y la consulta Q18 | FK compuesta de `carga_proyecto` hacia `plan_estudios` con `tipo_curso` = 'CAPSTONE', que congela la marca (D-A7) |
| J-16 | Reemplazo del export (US-18 de la spec 001) en una sección con plantilla PUBLICADA | 409 «La sección tiene una plantilla de proyectos publicada. Su reemplazo todavía no está disponible.» (propuesta) hasta que exista el reemplazo de la plantilla | La misma transacción del reemplazo del export pasa la subida a REEMPLAZADA y el profesor sube otra vez la plantilla (C-51) |

## Fuera de alcance

Estos temas quedan para después del sprint, y cada uno abre su propia spec o un corte posterior cuando se apruebe. Los nombres de tablas, columnas y motivos de esta lista no existen en V1_01 a V1_10 y son (propuesta).

- Reemplazar la plantilla publicada por una corregida sin borrar la anterior (candidatas C-14 y C-32), que depende de US-18 de la spec 001 y de D-11 y D-27. V1_10 ya trae el estado REEMPLAZADA, `reemplaza_carga_proyecto_id` y `uq_carga_proyecto_reemplaza` para no migrar otra vez.
- Retirar los datos de proyecto al reemplazar el export (candidata C-51), con J-16.
- El R-18 (D-15).
- Detectar en los textos libres patrones de DNI, correo o teléfono (parte de la candidata C-45, D-28).
- El dígito verificador módulo 11 del RUC (D-19).
- Una pantalla de vista previa de la tabla maestra y un rol de lectura propio para Power BI.
- Subir la plantilla junto con el export en una sola petición, antes que el export o por tramos (D-26).
- Que el coordinador suba o corrija la plantilla de una sección.
- Datos reales de estudiantes y de proyectos, que exigen D-10 de la spec 001 y D-28.
