# Feature Specification: Programación docente del ciclo, cargada desde el archivo de la carrera

**Feature Branch**: `docs/005-om-bp-y-006` (PR a `develop`, junto con el cambio del 2026-11-21 de la spec 005), con la implementación en `feat/006-programacion-docente` del Back después de la aprobación
**Created**: 2026-11-21
**Status**: Aprobada por Jefferson en el chat el 2026-11-21 («Sí, apruébalas»), después de aprobar su alcance el mismo día («Sí, escríbelo»), con D-44, D-45 y J-42 en el valor que propone
**Input**: «¿El R17 podría llenar el dato de sección y docente de forma automática? Son datos maestros que cargarían al inicio del ciclo con la programación docente post-matrícula.» (Claudia León, secretaria académica de Ingeniería Ambiental, correo del 19 o 20 de noviembre de 2026). «en la semana 14 deberíamos capacitar a los profesores, para que en la 15 (máximo 16) hagan sus registros» (Claudia León, correo del 18 de noviembre de 2026)

## Épica

> **EP-06. Programación docente del ciclo (propuesta).** Desde el 2026-11-19 la universidad autoriza los datos reales en Neon (D-10), pero `develop` solo trae guiones de datos inventados (`db/datos/periodo_2026_2_inventado.sql` y `varias_secciones_2026_2_inventado.sql`). Ningún guion escribe las secciones, los profesores ni las asignaciones reales en `abet.seccion`, `acceso.usuario_autorizado` y `acceso.docente_seccion`, así que ningún profesor real encuentra su sección en la pantalla P2 «Mis secciones» cuando llegue la semana 15. Esta épica agrega un guion repetible que lee el archivo de la programación docente post-matrícula, informa lo que cambiaría en una corrida en seco y escribe todo en una sola transacción solo con `--aplicar`. Suma además una consulta informativa de las secciones con plan de medición que quedan sin profesor activo. La spec es pequeña, no agrega tablas, columnas, restricciones, vistas, roles, rutas ni pantallas, y va antes de la capacitación de la semana 14.

Convenciones de esta spec. Todos los datos de los escenarios son inventados y siguen las convenciones de las specs 001, 003, 004 y 005. Las secciones de prueba son la 410, la 411 y la 412 de 450002 «Principios de Ingeniería Sostenible» y la 410 y la 412 de 450010 «Gestión Sostenible de Residuos», en 2026-2, con los profesores `docente410@example.invalid`, `docente411@example.invalid` y `docente.varias@example.invalid` y el coordinador `coordinacion@example.invalid`. El archivo de prueba se arma en `tmp_path` y nunca entra a `tests/datos_inventados/`. El archivo real de la carrera trae correos de profesores, que son datos personales, y nunca entra a git, porque el repositorio es público (regla 6 de `AGENTS.md`). Lo que el redactor decide sin fuente va marcado «(propuesta)».

Prefijos e identificadores. La épica lleva el prefijo EP y continúa la numeración de las specs 001 a 005 (EP-06). Las historias US continúan desde US-55, porque la spec 005 usa US-45 a US-54, y su cambio del 2026-11-21 no agrega historias. Las decisiones de la carrera siguen desde D-44 y las de Jefferson desde J-42, porque el cambio del 2026-11-21 de la spec 005 usa D-39 a D-43 y J-38 a J-41. La spec no usa ningún número de consulta de control Q, porque su consulta es informativa y no entra a `db/pruebas/pruebas.sql`. Los requisitos funcionales FR (functional requirement), los criterios de éxito SC (success criterion), las decisiones técnicas AD (architecture decision) y las tareas T se numeran dentro de esta spec, así que una regla viva que cite uno de ellos nombra la spec, como «FR-004 de la spec 006». La historia candidata de la auditoría es C-C01 del cambio del 2026-11-21 de la spec 005, y su revisión está en `revision-historias.md`.

Siglas y términos. Las de las specs 001 a 005 valen aquí. CSV es el formato de valores separados por comas (comma-separated values), UTF-8 es la codificación de caracteres de 8 bits de Unicode (Unicode Transformation Format) y BOM es la marca de orden de bytes (byte order mark) que Excel antepone al guardar un CSV en UTF-8. La programación docente es la lista de secciones del ciclo con el profesor de cada una, que la carrera publica después de la matrícula. Una fila del archivo asigna un profesor a una sección, y una asignación es una fila de `acceso.docente_seccion`. El informe es el texto que el guion escribe en la salida estándar, y una corrida en seco es la que informa sin guardar nada. La fila 1 del archivo es la de los encabezados, así que la primera fila de datos es la fila 2, como en una hoja de cálculo.

Archivo base de los escenarios, `programacion_20262_inventada.csv` en `tmp_path`, con los encabezados de FR-002 (propuesta).

| Fila | periodo | asignatura | seccion | correo | curso_blackboard |
| --- | --- | --- | --- | --- | --- |
| 2 | 2026-2 | 450002 | 410 | docente410@example.invalid | SINTETICO_20262_450002_410 |
| 3 | 2026-2 | 450002 | 411 | docente411@example.invalid | SINTETICO_20262_450002_411 |

La base de partida de los escenarios tiene las migraciones V1_01 a V1_11, la vigencia de AMB-2026 en 2026-2, el plan de medición de 450002 (5.1, 5.2 y 5.3) y de 450010 (2.1, 2.2 y 5.1) y el usuario `coordinacion@example.invalid` con rol COORDINADOR, y ninguna sección de 2026-2 ni ningún profesor. Con el archivo base, la primera corrida da 2 secciones nuevas, 2 usuarios nuevos y 2 asignaciones nuevas.

Los escenarios viven en `specs/006-programacion-docente/aceptacion/programacion_docente.feature` (US-55, US-56 y US-57) y en `secciones_sin_docente.feature` (US-58), en español (`# language: es`). Sus pasos van en `tests/aceptacion/pasos/test_programacion_docente_feature.py` y `test_secciones_sin_docente_feature.py` (propuesta), que reutilizan los pasos comunes de `tests/aceptacion/pasos/conftest.py`. Cada escenario lleva `@US-NN`, `@spec006` y `@corte1`. Ningún escenario lleva `@delegado_a_vitest`, porque la spec no cambia ninguna pantalla. Cuando un texto literal del informe difiere entre esta spec y un `.feature`, manda el del `.feature`.

## Clarifications

### Session 2026-11-21

- Claudia pregunta, con las palabras del Input, si el R-17 puede llenar la sección y el docente de forma automática con la programación docente post-matrícula, que la carrera cargaría al inicio del ciclo. La sección ya sale sola de la base, en D11 del R-17 desde `abet.v_r17_por_pi.seccion`. El nombre del docente en el R-17 es D-12 de la spec 001, que sigue abierta con la Oficina de Calidad, y queda fuera de esta spec.
- El correo del 18 de noviembre fija el calendario. La carrera capacita a los profesores en la semana 14, y los profesores registran en la semana 15, o a más tardar en la 16. Sin la programación cargada, ningún profesor real encuentra su sección en P2 en la semana 15, así que esta spec va antes de la capacitación.
- La auditoría del cambio del 2026-11-21 de la spec 005 revisa C-C01 con tres lentes y con el crítico de arquitectura. Las tres lentes la marcan CORREGIR y la llevan a una spec propia, y el crítico sostiene el guion en seco por omisión con `--aplicar` en una transacción, sin migración (`revision-historias.md`).
- Jefferson aprueba el alcance en el chat el 2026-11-21 («Sí, escríbelo»), con la spec 006 pequeña, sin migración y antes de la capacitación, y con D-44, D-45 y J-42 como decisiones nuevas.
- `app/permisos.py` da las secciones de `acceso.docente_seccion` solo al rol PROFESOR (`_ALCANCE`). Un coordinador asignado a una sección la lee como coordinador, pero no sube ni declara en ella (BR-ACCESO-08). La spec no cambia esa regla, y el guion lo avisa (US-56).
- Las contraseñas siguen fuera del guion. Jefferson las asigna con `ABET_SIS_MED/herramientas_neon/asignar_claves.py`, que vive fuera del repositorio, o llegan con el código por correo del corte 2 (BR-ACCESO-09), según cuál esté listo para la semana 15 (D-45).
- Se desconoce el formato del archivo real de la carrera. La spec fija un CSV mínimo provisional (D-44), que la Coordinación puede llenar a mano si el archivo no llega antes de la semana 14.

### Session 2026-11-22

La construcción en `feat/006-programacion-docente`, la revisión de AD-01 a AD-05 por el crítico (T006) y las dos revisiones del código del 2026-11-22 dejan estas dudas para la revisión de la spec. Ninguna cambia un requisito, y cada una lleva el valor que el guion aplica mientras tanto.

- FR-007 no cuenta el `curso_blackboard` que completa el único UPDATE de FR-005. Una corrida que solo completa cursos escribe en la base, pero su resumen dice 0, 0 y 0. El guion cuenta esos UPDATE y, si hay alguno, cierra con «Cambios guardados.» y no con «Sin cambios.», sin una línea propia en el informe, así que la corrida en seco no deja ver ese UPDATE antes de guardarlo. Queda por decidir si el informe suma una línea o un conteo de cursos completados.
- FR-003 no dice si, en codocencia, una fila con `curso_blackboard` y otra de la misma sección sin él traen «dos cursos distintos». El guion aplica que una celda vacía no cuenta como un curso distinto.
- FR-008 no fija el código cuando psql no existe o no es de la 18. El guion termina con código 3, como cuando la base no responde, con «No se encuentra psql.» o «psql no es de PostgreSQL 18.» (propuestas).
- US-58 y SC-006 cuentan como cubierta una sección con un profesor activo sin contraseña, que no puede entrar en la semana 15 mientras FR-015 deja las contraseñas para el final. FR-011 no cambia, y la pregunta va a la Coordinación.
- El escenario 6 de US-55 dice que el informe «termina con» el recordatorio de las contraseñas, y el `.feature` dice que el informe lo «dice», mientras FR-007 fija la línea final. Manda el `.feature`, así que el recordatorio va antes de la línea final.
- La spec no fija el texto de algunos mensajes que el guion necesita, que quedan como propuestas, «Falta el archivo, por ejemplo --archivo RUTA.», «El periodo 2030-1 no existe en la base.», «Fila N. Falta la asignatura.» (y sus pares de periodo y sección), «Fila N. El código de asignatura 45000 no es válido.», «Fila N. El curso de Blackboard tiene más de 100 caracteres.», «Fila N. La sección 411 de 450002 trae otro curso de Blackboard en la fila M.», «El archivo no se puede leer como CSV.», «La base no responde y no se guardó nada.», «Aviso. La sección 413 de 450002 está en la base con 0 asignaciones y el archivo no la trae.», «Aviso. La asignatura 990001 no está en el plan de estudios vigente en 2026-2, así que la coordinación no verá su sección 410.» y la línea de uso de un argumento desconocido. El resumen usa el singular con una sola fila, como «1 sección nueva».
- Con el objetivo nombrado en cada INSERT (AD-03), dos corridas con `--aplicar` al mismo tiempo siguen sin duplicar filas, pero un choque de `uq_seccion_curso_bb` que la revisión de FR-004 no alcanza a ver llega como error de la base, con código 3 y sin ninguna fila nueva.
- Antes de T063, Jefferson decide si el informe de la corrida real, que trae correos de profesores, lo lee solo él en su terminal o puede pasar por un agente, y qué se hace con la 410 y la 411 inventadas de 450002 que tiene la rama principal de Neon, que una 410 o una 411 real de 450002 encontraría con su profesor inventado y su curso `SINTETICO_…` (AD-05 de `revision-historias.md` y `db/README.md`).
- FR-009 limita los datos del archivo que muestra el informe al número de fila, la asignatura, la sección y el correo, y la regla 6 de `AGENTS.md` prohíbe mostrar el valor leído de una celda en un rechazo. Los Ejemplos de «Una fila inválida rechaza el archivo entero» piden, en cambio, que el rechazo muestre la celda que lo causa, como el periodo, el curso de Blackboard, la sección o el correo inválidos. Manda el `.feature`, así que el guion muestra esa celda, y el choque entre el `.feature`, FR-009 y `AGENTS.md` queda como pregunta para la revisión de la spec.
- FR-003 solo pide el patrón de `ck_usuario_autorizado_correo` y los 100 caracteres del curso de Blackboard, y ninguno de los dos excluye los caracteres invisibles o de control de las categorías Unicode Cf y Cc. Esos caracteres llegan al copiar una celda, como el espacio de ancho cero (U+200B) de un correo copiado desde Outlook o el salto de línea de Alt+Enter en Excel. Un correo así crearía un usuario con el que el profesor no puede entrar, y un curso así nunca coincidiría con el de un export. El guion rechaza esa fila con «Fila N. El correo trae un carácter invisible o de control.» o «Fila N. El curso de Blackboard trae un carácter invisible o de control.» (propuestas), sin repetir la celda, que partiría la línea del informe.
- FR-008 no fija el código de un archivo que existe pero no se puede abrir, como el CSV que Excel tiene abierto en el Windows. El guion lo trata como un archivo rechazado, con «El archivo no se puede abrir.» (propuesta), la línea final de rechazo y código 1, sin conectarse.
- FR-008 da el código 3 cuando la base no responde, pero con `--aplicar` la conexión puede cortarse mientras viaja el COMMIT o justo después, como cuando Neon suspende el cómputo, y entonces el guion no sabe si la base guardó los cambios. Con `--aplicar`, el informe de ese caso dice «La base no responde y no se sabe si guardó los cambios. Una corrida en seco lo muestra.» (propuesta), con el mismo código 3. Como ningún INSERT duplica filas, repetir la corrida con `--aplicar` tampoco las duplica.

## User Scenarios & Testing *(mandatory)*

### US-55: Cargar la programación docente con una corrida en seco antes de escribir (Priority: P1)

Como administrador técnico de la carrera, quiero cargar al inicio del ciclo las secciones, los profesores y sus asignaciones desde el archivo de la programación docente, primero con una corrida que solo informa y después con otra que escribe, para que cada profesor encuentre su sección en P2 sin que nadie escriba SQL a mano.

**Why this priority**: sin esta carga, ningún profesor real encuentra su sección en la semana 15, y el registro de causas y acciones de la spec 005 no ocurre. Hoy solo existen guiones de datos inventados, y un SQL escrito a mano para decenas de secciones reales no deja ver qué cambia antes de guardarlo.

**Independent Test**: en la base de partida, la corrida en seco con el archivo base informa «Resumen. 2 secciones nuevas, 2 usuarios nuevos y 2 asignaciones nuevas.» y deja las tres tablas igual, y la corrida con `--aplicar` guarda esas filas, mientras en `develop` 4eb6f33 el guion no existe.

**Base**: `abet.seccion` (`uq_seccion`, `ck_seccion_numero`, `uq_seccion_curso_bb`, `fk_seccion_periodo` y `fk_seccion_asignatura`), `acceso.usuario_autorizado` (`uq_usuario_autorizado_correo`, `ck_usuario_autorizado_correo` y `ck_usuario_autorizado_rol`) y `acceso.docente_seccion` (`uq_docente_seccion`, `fk_docente_seccion_usuario` y `fk_docente_seccion_seccion`); `abet.periodo` y `abet.asignatura`, solo lectura; `acceso.credencial`, que el guion no toca; `app/permisos.secciones_visibles()` y la ruta 4, `GET /api/secciones`; guion `db/herramientas/cargar_programacion.py` con su SQL `db/herramientas/cargar_programacion.sql` (nuevos, J-42); sin migración.
**Pantalla**: ninguna. El efecto se ve en P2 Mis secciones, que no cambia.

**Acceptance Scenarios** (`specs/006-programacion-docente/aceptacion/programacion_docente.feature`):

1. **La corrida en seco informa y no escribe.** **Dado** la base de partida y el archivo base, **Cuando** el administrador corre el guion con `--periodo 2026-2` y sin `--aplicar`, **Entonces** termina con código 0, el informe dice «Resumen. 2 secciones nuevas, 2 usuarios nuevos y 2 asignaciones nuevas.» y «Corrida en seco. Nada se escribió.» (propuestas), y `abet.seccion`, `acceso.usuario_autorizado` y `acceso.docente_seccion` conservan sus filas.
2. **La corrida con `--aplicar` escribe y se puede repetir.** **Dado** la base de partida y el archivo base, **Cuando** el administrador corre el guion con `--aplicar` dos veces, **Entonces** la primera termina con código 0, crea la 410 y la 411 de 450002 con su curso de Blackboard, los 2 usuarios con rol PROFESOR, activos, y las 2 asignaciones, y dice «Cambios guardados.» (propuesta). La segunda dice «Resumen. 0 secciones nuevas, 0 usuarios nuevos y 0 asignaciones nuevas.» y «Sin cambios.» (propuestas) y deja las mismas filas.
3. **El profesor cargado recibe solo su sección en `GET /api/secciones`.** **Dado** el archivo base aplicado y `docente410@example.invalid` con una contraseña de prueba asignada por el paso común de la spec 001, **Cuando** pide `GET /api/secciones?periodo=2026-2`, **Entonces** recibe 200 con la 410 de 450002 y sin la 411.
4. **Un correo con mayúsculas o espacios se normaliza.** **Dado** el archivo base con « Docente410@EXAMPLE.invalid » en la fila 2 y `docente410@example.invalid` ya creado por una corrida anterior, **Cuando** el administrador corre el guion con `--aplicar`, **Entonces** el informe cuenta 0 usuarios nuevos y `acceso.usuario_autorizado` sigue con una sola fila de ese correo.
5. **Dos profesores en la misma sección dan dos asignaciones.** **Dado** el archivo base con una fila 4 que asigna también la 411 de 450002 a `docente.varias@example.invalid`, **Cuando** el administrador corre el guion con `--aplicar`, **Entonces** el informe cuenta 3 usuarios nuevos y 3 asignaciones nuevas, y la 411 queda con sus dos profesores.
6. **El guion no asigna contraseñas.** **Dado** el archivo base, **Cuando** el administrador corre el guion con `--aplicar`, **Entonces** `acceso.credencial` no gana ninguna fila y el informe termina con «Los usuarios nuevos no tienen contraseña. Asígnela con asignar_claves.py o con el código por correo.» (propuesta).

---

### US-56: Lo que ya está en la base no se borra ni cambia sin aviso (Priority: P1)

Como administrador técnico, quiero que la carga nunca borre una asignación, nunca cambie el rol ni el estado de un usuario y me avise de lo que el archivo no trae, para que un archivo incompleto o un coordinador que también dicta no dejen sin acceso a nadie.

**Why this priority**: el guion corre con datos reales y con el usuario dueño de la base, que sí puede borrar y actualizar. Un archivo parcial que borrara lo ausente quitaría a un profesor su sección en plena semana 15, y un cambio de rol silencioso daría a un profesor la vista de toda la carrera.

**Independent Test**: con `docente.varias@example.invalid` asignado a la 412 de 450002 y el archivo base, la corrida con `--aplicar` conserva esa asignación, el informe la nombra, y ningún rol ni ningún `activo` cambia.

**Base**: `acceso.docente_seccion`, `acceso.usuario_autorizado` (`rol` y `activo`) y `abet.seccion`; `_ALCANCE` de `app/permisos.py` y BR-ACCESO-08, que no cambian; `abet.plan_medicion` y `abet.catalogo_vigencia` con `abet.plan_estudios`, solo lectura, para los avisos; guion de US-55.
**Pantalla**: ninguna.

**Acceptance Scenarios** (`specs/006-programacion-docente/aceptacion/programacion_docente.feature`):

1. **Una asignación que el archivo no trae se informa y no se borra.** **Dado** la 412 de 450002 asignada a `docente.varias@example.invalid` y el archivo base, que no la trae, **Cuando** el administrador corre el guion con `--aplicar`, **Entonces** el informe dice «Aviso. La sección 412 de 450002 tiene en la base a docente.varias@example.invalid y el archivo no la trae.» (propuesta), y `acceso.docente_seccion` y `abet.seccion` conservan esas filas.
2. **Un coordinador que también dicta conserva su rol.** **Dado** el archivo base con la fila 3 cambiada a `coordinacion@example.invalid`, **Cuando** el administrador corre el guion con `--aplicar`, **Entonces** el rol de `coordinacion@example.invalid` sigue en COORDINADOR, la asignación de la 411 se crea y el informe dice «Aviso. coordinacion@example.invalid es COORDINADOR y no podrá subir ni declarar en la sección 411 de 450002.» (propuesta).
3. **Un profesor dado de baja no se reactiva.** **Dado** `docente411@example.invalid` con rol PROFESOR y `activo` falso, **Cuando** el administrador corre el guion con `--aplicar` y el archivo base, **Entonces** `activo` sigue falso, la asignación de la 411 se crea y el informe dice «Aviso. docente411@example.invalid está dado de baja y no verá la sección 411 de 450002.» (propuesta).
4. **Una sección de una asignatura sin plan de medición entra con aviso.** **Dado** una base de partida sin el plan de medición de 450010 y el archivo base con una fila 4 de la 410 de 450010 para `docente.varias@example.invalid`, **Cuando** el administrador corre el guion con `--aplicar`, **Entonces** la sección se crea y el informe dice «Aviso. La asignatura 450010 no tiene plan de medición en 2026-2, así que su sección 410 no podrá recibir exports.» (propuesta).

---

### US-57: Un archivo con errores no deja nada a medias (Priority: P1)

Como administrador técnico, quiero que una sola fila inválida o una falla de la base rechacen el archivo entero, con todas las filas inválidas nombradas, para corregir el archivo una vez y no dejar la programación cargada a medias.

**Why this priority**: el Principio III de la constitución exige que toda carga sea atómica, y una programación a medias deja a unos profesores con su sección y a otros sin ella, sin que nadie sepa cuáles. Además, el archivo real puede traer códigos con ceros a la izquierda o correos mal escritos, que `ck_seccion_numero` y `ck_usuario_autorizado_correo` rechazan.

**Independent Test**: con el archivo base y la asignatura 999999 en la fila 3, el guion con `--aplicar` termina con código 1, nombra la fila 3 y deja las tres tablas igual.

**Base**: las restricciones de US-55; `abet.periodo` (`uq_periodo_codigo`); la transacción única del guion (FR-006); los códigos de salida (FR-008).
**Pantalla**: ninguna.

**Acceptance Scenarios** (`specs/006-programacion-docente/aceptacion/programacion_docente.feature`):

1. **Una fila inválida rechaza el archivo entero (esquema).** **Dado** el archivo base con un valor inválido en una columna de la fila 3, **Cuando** el administrador corre el guion con `--aplicar`, **Entonces** termina con código 1, el informe trae el mensaje de esa fila y «Archivo rechazado. Nada se escribió.» (propuesta), y ninguna de las tres tablas cambia. Los casos son la asignatura 999999, que no existe, la sección «0411», el correo sin arroba, el periodo 2026-1, una celda de correo vacía y el curso de Blackboard de la fila 2 repetido en la fila 3.
2. **El informe nombra todas las filas inválidas.** **Dado** el archivo base con la asignatura 999999 en la fila 2 y la sección «0411» en la fila 3, **Cuando** el administrador corre el guion, **Entonces** el informe trae los dos mensajes, en el orden de las filas.
3. **Falta una columna obligatoria.** **Dado** el archivo base sin la columna `correo`, **Cuando** el administrador corre el guion, **Entonces** termina con código 1 y el informe dice «Falta la columna correo.» (propuesta).
4. **Una falla de la base deshace todo.** **Dado** un disparador de prueba en la base desechable que rechaza la segunda fila que entra a `acceso.docente_seccion`, **Cuando** el administrador corre el guion con `--aplicar`, **Entonces** termina con código 3, el informe dice «La base rechazó la escritura y no guardó nada.» (propuesta), y la 410 y su profesor tampoco quedan guardados.
5. **El guion no corre sin sus argumentos ni con el archivo dentro del repositorio (esquema).** **Dado** una corrida sin `--periodo`, con `--periodo 2026-13`, con un archivo que no existe o con un archivo dentro de la copia de trabajo del repositorio, **Cuando** el administrador corre el guion, **Entonces** termina con código 2 antes de conectarse a la base y dice el mensaje del caso (propuestas).

---

### US-58: Saber qué secciones quedan sin profesor antes de la semana 15 (Priority: P1)

Como coordinación de la carrera, quiero listar las secciones del periodo con plan de medición que no tienen ningún profesor activo para pedir la asignación que falta antes de que los profesores registren.

**Why this priority**: una sección con plan y sin profesor activo no recibe ningún export, y su R-17 falta en la acreditación sin que ninguna pantalla lo diga. Después de cargar la programación, esta consulta es la prueba de que la carga quedó completa.

**Independent Test**: con el archivo base aplicado y la 412 de 450010 creada sin profesor, la consulta lista solo la 412 de 450010 y cuenta 1.

**Base**: `abet.seccion`, `abet.plan_medicion`, `acceso.docente_seccion` y `acceso.usuario_autorizado` (`rol` y `activo`), solo lectura; consulta informativa `db/plataforma/neon/secciones_sin_docente.sql` (nueva, propuesta), con el molde de `pi_sin_descripcion_instrumento.sql` (AD-29 de la spec 005); `abet_respaldo`, de solo lectura, que lee `abet` y `acceso` desde V1_09.
**Pantalla**: ninguna.

**Acceptance Scenarios** (`specs/006-programacion-docente/aceptacion/secciones_sin_docente.feature`):

1. **La consulta encuentra la sección sin profesor activo (esquema).** **Dado** el archivo base aplicado y la 412 de 450010 sin asignación, asignada solo a un profesor dado de baja o asignada solo a `coordinacion@example.invalid`, **Cuando** corre la consulta con `-v periodo=2026-2`, **Entonces** lista la 412 de 450010 y ninguna sección de 450002, y cuenta 1.
2. **Una sección sin plan de medición no aparece.** **Dado** el archivo base aplicado y una sección 413 de una asignatura sin plan de medición en 2026-2, **Cuando** corre la consulta, **Entonces** cuenta 0.
3. **La consulta no escribe.** **Dado** la consulta corrida por el usuario dueño de la base desechable, **Entonces** la sesión queda en solo lectura antes de la primera consulta y ninguna tabla de `abet` ni de `acceso` cambia su número de filas.
4. **La consulta pide el periodo.** **Dado** una corrida sin `-v periodo`, **Entonces** se detiene antes de consultar con «Falta el periodo, por ejemplo -v periodo=2026-2.», el texto de `pi_sin_descripcion_instrumento.sql`.

---

### Edge Cases

- Una fila repetida, con la misma sección y el mismo correo, cuenta una sola vez y no crea otra asignación, porque `uq_docente_seccion` y `ON CONFLICT DO NOTHING` la absorben.
- Dos filas de la misma sección con cursos de Blackboard distintos rechazan el archivo, con el mensaje de la segunda fila (propuesta).
- Una sección que ya existe sin curso de Blackboard lo recibe del archivo, y una que ya tiene otro curso rechaza la fila con «Fila N. La sección 410 de 450002 ya tiene otro curso de Blackboard en la base.» (propuesta). Un archivo sin la columna `curso_blackboard` deja el curso como está, porque la validación del export lee la sección del nombre del curso y no de esta columna (`abet_carga/validacion.py`).
- Una asignatura que existe en `abet.asignatura` pero no en el plan de estudios vigente de la carrera entra con aviso, porque el coordinador no la verá en P2 (`_ALCANCE` con `abet.catalogo_vigencia` y `abet.plan_estudios`) (propuesta).
- Una sección que la base tiene en el periodo y que el archivo no trae se informa con su número de asignaciones y no se borra.
- Un archivo con BOM de UTF-8 se lee igual que sin ella, y un archivo en otra codificación que no se puede leer como UTF-8 se rechaza con «El archivo no está en UTF-8.» (propuesta) y código 1.
- Un archivo sin filas de datos termina con código 1 y «El archivo no trae filas.» (propuesta).
- Dos corridas con `--aplicar` al mismo tiempo no duplican filas, porque cada INSERT usa `ON CONFLICT DO NOTHING` sobre las restricciones únicas, y la segunda informa lo que ya encuentra.
- El guion corre en el Windows de Jefferson con Python 3.14 y psql 18 y en las pruebas con Python 3.12, así que solo usa la biblioteca estándar de Python 3.12.
- Un correo de otro dominio que el institucional pasa el patrón de `ck_usuario_autorizado_correo`. El dominio que acepta el guion es parte de D-44, y mientras no se decida no se filtra (propuesta).

## Requirements *(mandatory)*

- **FR-001** El guion vive en `db/herramientas/cargar_programacion.py` (J-42) y se corre con `python -I db/herramientas/cargar_programacion.py --periodo 2026-2 --archivo RUTA [--aplicar]`. Usa solo la biblioteca estándar de Python 3.12 y llama a psql 18 con `-X -v ON_ERROR_STOP=1`, de modo que el Windows no necesita instalar paquetes de Python.
- **FR-002** El archivo es un CSV en UTF-8, con BOM o sin ella, separado por comas, con una fila de encabezados y una fila por cada par de sección y profesor (D-44). Las columnas obligatorias son `periodo`, `asignatura`, `seccion` y `correo`, y `curso_blackboard` es opcional en el archivo y en cada fila (propuesta). El guion ignora otras columnas sin leer sus valores, así que un archivo real con el nombre del profesor no lleva ese nombre a la base. **Cambio del 2026-11-25 (spec 010, FR-004, propuesta).** El archivo admite una columna opcional `nombre`, en el archivo y en cada fila. El guion la lee, normaliza el nombre y lo guarda junto al correo. Las demás columnas ajenas siguen ignoradas sin leer sus valores.
- **FR-003** Antes de conectarse, el guion revisa la forma de cada fila. El periodo tiene la forma `AAAA-C` y es el de `--periodo`. La asignatura tiene 4 o 6 dígitos (`ck_asignatura_codigo`). La sección cumple `^[1-9][0-9]{0,4}$` (`ck_seccion_numero`). El correo, después de quitarle los espacios a los lados y pasarlo a minúscula, cumple el patrón de `ck_usuario_autorizado_correo`. El curso de Blackboard tiene a lo sumo 100 caracteres, y una sección no trae dos cursos distintos ni un curso pertenece a dos secciones. Una celda obligatoria vacía también invalida la fila.
- **FR-004** Dentro de la transacción, el guion revisa que el periodo exista en `abet.periodo`, que cada asignatura exista en `abet.asignatura` y que ningún curso de Blackboard del archivo pertenezca en la base a otra sección (`uq_seccion_curso_bb`). Una fila que falla cualquier revisión de FR-003 o FR-004 rechaza el archivo entero, y el informe nombra cada fila inválida con su número y su motivo, en el orden de las filas.
- **FR-005** El guion escribe solo con INSERT y `ON CONFLICT DO NOTHING` en `abet.seccion` (`periodo_id`, `asignatura_id`, `numero` y `curso_blackboard`), en `acceso.usuario_autorizado` (`correo` y rol PROFESOR, solo para un correo nuevo) y en `acceso.docente_seccion` (`usuario_id` y `seccion_id`). La única actualización completa un `curso_blackboard` nulo de una sección existente. El guion nunca borra, nunca cambia `rol` ni `activo` y no toca `acceso.credencial`, `abet.plan_medicion` ni ninguna tabla de cargas. **Cambio del 2026-11-25 (spec 010, FR-005, propuesta).** El INSERT de un correo nuevo suma el nombre, y una segunda actualización completa el `nombre` nulo de un usuario existente con `WHERE nombre IS NULL`. Un nombre que ya existe no cambia, y el guion nunca asigna nombre a una cuenta COORDINADOR.
- **FR-006** La corrida en seco y la corrida con `--aplicar` ejecutan el mismo SQL, `db/herramientas/cargar_programacion.sql`, en una sola transacción. La corrida en seco termina con ROLLBACK y la otra con COMMIT, así que el informe en seco cuenta exactamente lo que la corrida real escribiría. Cualquier error de la base deshace la transacción entera.
- **FR-007** El informe trae una línea de resumen, «Resumen. N secciones nuevas, N usuarios nuevos y N asignaciones nuevas.», las líneas «Aviso. …» y una línea final, que es «Corrida en seco. Nada se escribió.», «Cambios guardados.», «Sin cambios.» o «Archivo rechazado. Nada se escribió.» (propuestas). Los avisos cubren la asignación o la sección de la base que el archivo no trae, el usuario dado de baja, el coordinador con una sección asignada, la asignatura sin plan de medición en el periodo y la asignatura fuera del plan de estudios vigente. Con usuarios nuevos, el informe recuerda que no tienen contraseña. **Cambio del 2026-11-25 (spec 010, FR-006, propuesta).** Con la columna `nombre` en el archivo, la línea de resumen es «Resumen. N secciones nuevas, N usuarios nuevos, N asignaciones nuevas y N nombres completados.», y un archivo que solo completa nombres cierra con «Cambios guardados.». Un nombre que ya existe produce «Aviso. <correo> ya tiene otro nombre en la base y no se cambia.». Sin la columna, el informe es el de esta spec.
- **FR-008** El guion termina con código 0 cuando la corrida en seco o la escritura salen bien, con 1 cuando rechaza el archivo, con 2 por un argumento inválido, antes de conectarse, y con 3 cuando la base no responde o rechaza la escritura, como `asignar_claves.py`.
- **FR-009** El guion se niega a leer un archivo dentro de la copia de trabajo del repositorio, con «El archivo de la programación debe estar fuera del repositorio.» (propuesta) y código 2. No copia el archivo, no lo escribe en ningún registro y no muestra en el informe más datos del archivo que el número de fila, la asignatura, la sección y el correo de cada aviso o rechazo. `.gitignore` suma `programacion_*.csv` como segunda barrera (propuesta). **Cambio del 2026-11-25 (spec 010, FR-012, propuesta).** El informe nunca escribe un nombre, ni el del archivo ni el de la base. Un nombre inválido se rechaza con «Fila N. El nombre no es válido.» sin repetir el valor.
- **FR-010** La conexión llega por las variables de entorno de libpq que psql lee solo (`PGHOST`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` y `PGSSLMODE`), nunca por argumentos ni por archivos. En Neon el guion corre desde el Windows de Jefferson con `~/.claude/scripts/en_windows.py`, que pasa los secretos de `bd/.env.neon` por la entrada estándar de SSH, y con el usuario dueño de la base, porque `abet_app` no escribe `abet.seccion`, `acceso.usuario_autorizado` ni `acceso.docente_seccion` y `crear_rol_app.sql` no cambia.
- **FR-011** La consulta informativa `db/plataforma/neon/secciones_sin_docente.sql` recibe `-v periodo`, pasa la sesión a solo lectura antes de la primera consulta y lista por asignatura y número cada sección del periodo cuya asignatura tiene plan de medición en ese periodo y que no tiene en `acceso.docente_seccion` ningún usuario activo con rol PROFESOR. Termina con la cantidad. No es un control de `db/pruebas/pruebas.sql`, porque la base de `db/pruebas/pruebas.sql` tiene a propósito dos secciones 301 sin profesor, que usan los casos de Q06 y Q07.
- **FR-012** Cada escenario tiene su prueba con pytest-bdd, y el guion tiene además pruebas unitarias de la lectura y de las revisiones de forma en `tests/test_cargar_programacion.py` (propuesta). Las pruebas corren en el clúster desechable de `tests/cluster_desechable.py`, nunca en localhost:5432, con archivos armados en `tmp_path` y correos de `@example.invalid`. La base de partida la siembra un ayudante nuevo de `tests/cargas_de_prueba.py` con la vigencia y los dos planes, sin secciones ni profesores (propuesta). Su paso de Antecedentes empieza con «una base desechable de partida de la spec 006», y no con «una base PostgreSQL 18 desechable con las migraciones V1_01 a V1_», para que la expresión de `tests/aceptacion/pasos/conftest.py:766`, que crea la base «periodo» con `db/datos/periodo_2026_2_inventado.sql` y sus secciones 410 y 411, no lo capture.
- **FR-013** La spec no agrega migración, no cambia permisos, rutas, pantallas, `app/permisos.py`, el contrato del Front ni las consultas Q01 a Q15. Q15 sigue encontrando en `acceso` solo `usuario_autorizado.correo`, porque el guion no agrega columnas. **Cambio del 2026-11-25 (spec 010, FR-001, propuesta).** La migración V1_16 de la spec 010 agrega la columna `acceso.usuario_autorizado.nombre`, y Q15 pasa a encontrar en `acceso` exactamente `usuario_autorizado.correo` y `usuario_autorizado.nombre`. Esta spec no agrega ninguna columna más.
- **FR-014** La regla vive en la spec viva `acceso` como BR-ACCESO-11 «Programación docente desde el archivo de la carrera» (propuesta), con `db/herramientas/cargar_programacion.py` en sus `targets`. `db/README.md` suma el uso del guion y de la consulta, con el orden de FR-015.
- **FR-015** En Neon, el primer paso es actualizar la copia del Back del Windows al commit fusionado de `develop` que trae el guion. Después siguen un respaldo con `db/herramientas/respaldar_neon.sh`, la corrida en seco en la rama principal, la lectura del informe por Jefferson, la corrida con `--aplicar` con su permiso, la consulta de US-58 y, al final, las contraseñas de los usuarios nuevos (propuesta, J-42).

## Success Criteria *(mandatory)*

- **SC-001** Con el archivo base, la corrida en seco y la corrida con `--aplicar` informan las mismas cifras, 2 secciones, 2 usuarios y 2 asignaciones nuevas, y solo la segunda las guarda.
- **SC-002** Una segunda corrida con `--aplicar` del mismo archivo informa 0 secciones, 0 usuarios y 0 asignaciones nuevas y no cambia ninguna fila.
- **SC-003** En las pruebas, ningún archivo rechazado y ninguna falla de la base dejan una fila nueva en `abet.seccion`, `acceso.usuario_autorizado` ni `acceso.docente_seccion`.
- **SC-004** Ninguna corrida borra una fila ni cambia `rol` o `activo` de un usuario, también cuando el archivo omite secciones o asignaciones de la base.
- **SC-005** Con un archivo inventado de 300 filas en el clúster desechable, la corrida en seco termina en menos de 10 s (propuesta).
- **SC-006** Antes de la capacitación de la semana 14, la consulta de US-58 devuelve 0 secciones en la rama principal de Neon, o la Coordinación conoce cada sección que devuelve.
- **SC-007** Ningún archivo con correos fuera de `@example.invalid` entra a git, y `bash scripts/preflight.sh` sigue sin fallas.

## Decisiones abiertas

De la carrera (D). Mientras no se decidan, el guion aplica el valor provisional.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| D-44 | Formato, dueño y fecha de entrega del archivo de la programación docente post-matrícula (columnas, si trae el correo institucional y el curso de Blackboard, el dominio del correo y si trae solo las asignaturas de Ambiental) | CSV mínimo con `periodo`, `asignatura`, `seccion`, `correo` y `curso_blackboard` opcional, que la Coordinación llena a mano si el archivo de la carrera no llega antes de la semana 14. Urgente, porque sin el formato real el CSV de prueba puede no ser fiel | Coordinación de Ambiental |
| D-45 | Si el guion crea la cuenta del profesor | Sí, con rol PROFESOR, activa y sin contraseña. La contraseña sigue con `asignar_claves.py` y la pone Jefferson, o llega con el código por correo del corte 2 si está listo para la semana 15 | Coordinación de Ambiental, con Jefferson |
| D-12 | Nombre del profesor en el R-17 (spec 001, sigue abierta) | Sin nombre. La programación cargada aquí podría traerlo después, en una migración propia | Coordinación de Ambiental y Oficina de Calidad |

De Jefferson (J), con el valor que propone la spec.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| J-42 | Dónde vive el guion y cómo se prueba | En `db/herramientas/cargar_programacion.py` del Back, con la biblioteca estándar y psql 18, y su SQL al lado. Se prueba con pytest-bdd en el clúster desechable con archivos inventados en `tmp_path`. El archivo real vive fuera de todo repositorio, llega al Windows con `scp` a una carpeta propia y se borra al terminar, y la corrida real va desde el Windows con el permiso de Jefferson en cada `--aplicar` (AD-01 a AD-05) | Jefferson |

## Fuera de alcance

- El nombre del profesor en el R-17 (C-C02), que espera a D-12 con la Oficina de Calidad, cambia Q15 y BR-R17-07 y pide una migración propia (V1_13 o posterior), nunca V1_12.
- Que un coordinador que también dicta suba y declare en su sección. Cambia `_ALCANCE` y BR-ACCESO-08, y lo decide la carrera.
- Dar de baja a los profesores o retirar las asignaciones que el archivo no trae. Lo hace el dueño de la base a mano, después de leer el aviso.
- La lectura directa de un archivo `.xlsx` de la carrera, que espera a D-44 y sumaría openpyxl al Windows.
- Las contraseñas y el código por correo del corte 2 (BR-ACCESO-09), que siguen en sus propios pasos.
- Una pantalla para que la Coordinación suba el archivo. El guion es del administrador técnico, y una pantalla exige rutas y un rol nuevos.
- Los roles de coordinador de curso y de área, que van con el R-18, fuera de esta spec y de la spec 005.
- Cargar el plan de medición o los cursos de otras carreras.
