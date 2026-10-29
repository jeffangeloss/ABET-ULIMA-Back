# Revisión por refutación de las historias de Capstone

**Fecha**: 2026-10-29
**Spec**: [spec.md](./spec.md)
**Entrada**: 46 historias candidatas (C-01 a C-32 y C-40 a C-53), escritas desde tres ángulos (el profesor de la sección Capstone, el coordinador y el administrador técnico con la base, y la evidencia con la privacidad), 44 preguntas abiertas, tres lentes de auditoría y una crítica de arquitectura con 22 decisiones (D-A1 a D-A22)
**Salida**: 25 historias de la spec (US-01 a US-25, 24 del corte 1 y 1 del corte 2), 3 piezas para después y 2 candidatas refutadas
**Fuentes**: los veredictos de las tres lentes y de la crítica, en la carpeta de trabajo del flujo del 2026-10-29 (fuera del repositorio)

## Método

Cada candidata parte refutada y entra al sprint solo si las lentes no la refutan ni la mueven. La lente de necesidad pregunta si la exige el objetivo del sprint (la plantilla de proyectos en la base, la tabla maestra en el formato nuevo y el R-17 con la hoja «Cursos Capstone»), el pedido literal de Jefferson o un principio de la constitución. La lente de solapamiento y tamaño aplica INVEST (independiente, negociable, valiosa, estimable, pequeña y comprobable) y busca reglas repetidas entre candidatas. La lente de verificabilidad coteja cada escenario con las migraciones V1_01 a V1_09, las vistas `R__`, `db/pruebas/pruebas.sql`, `db/datos/periodo_2026_2_inventado.sql` y el contrato `docs/03-api/contrato.md` del Front. Un crítico aparte ataca las decisiones técnicas con los veredictos SE_SOSTIENE, CAMBIAR y DUDOSA.

Las lentes usan SOBREVIVE (S), CORREGIR (C), FUSIONAR (F), PARTIR (P), MOVER_A_DESPUES (M) y REFUTADA (R). La síntesis aplica la regla de `auditoria-historias.md` de la skill del método. Una candidata queda en el sprint si al menos dos lentes no la sacan, y FUSIONAR, PARTIR y CORREGIR se aplican sobre la historia que la recibe. Cuando dos lentes eligen anfitriones distintos para una fusión, manda el anfitrión que eligen dos lentes. Cuando dos correcciones se contradicen en un nombre o un valor, manda el que proponen dos lentes, y si cada lente propone otro, manda el que respalda la crítica de arquitectura. Ninguna pieza que dos lentes sacan del sprint entra a la spec, aunque una tercera la mantenga.

Las candidatas se nombran C-NN, con letra cuando la auditoría las parte (C-07a, C-45b), y el prefijo US-NN queda solo para las 25 historias de `spec.md`. Las decisiones del crítico conservan su número D-A1 a D-A22 de su informe, que no es una decisión abierta. Las decisiones abiertas de esta spec siguen la numeración de la spec 001, desde D-14 para la carrera y desde J-11 para Jefferson, para que «D-08» o «D-11» nombren siempre la misma decisión en el repositorio.

## Veredictos por candidata

Abreviaturas. N es la lente de necesidad, T la de solapamiento y tamaño y V la de verificabilidad. «Después» indica que la pieza sale de la spec 002 y queda en «Fuera de alcance».

| Candidata | Título | N | T | V | Historia final | Razón de la decisión |
| --- | --- | --- | --- | --- | --- | --- |
| C-01 | Subir la plantilla de proyectos de mi sección Capstone | C | P | C | US-03 | Las tres lentes la mantienen. Fija el modelo único (subida `carga_proyecto` atada a `carga_id` y `proyecto_estudiante` con clave foránea compuesta hacia `carga_fila`), amplía `archivo_origen.tipo_fuente` de varchar(17) a varchar(20) porque PLANTILLA_PROYECTOS tiene 19 caracteres, deja Q15 en manos de la spec 001 y absorbe de C-47 el nombre sin ruta y la ausencia de columnas bytea |
| C-02 | La plantilla que llega antes que el export espera al export | S | F | S | US-04 | Dos lentes la conservan como historia propia y absorben el segundo escenario de C-49 con el texto de C-02, que explica el paso siguiente. El campo `proyectos_estado` pasa a US-23 |
| C-03 | Un código que no es de mi sección deja fuera solo su fila | C | F | C | US-07 | Dos lentes la eligen como anfitriona de C-49. Motivo único CODIGO_FUERA_DEL_EXPORT, respaldo en la clave foránea compuesta en lugar de Q15, el escenario de la guardia pasa a US-15 y el CODIGO_DUPLICADO de C-07 entra aquí |
| C-04 | Un dato de proyecto faltante rechaza la fila | C | S | C | US-08 | CAMPO_VACIO cubre también TIPO DE EMPRESA y RUC, porque así lo piden necesidad y verificabilidad frente a tamaño. Suma GRUPO_INVALIDO (verificabilidad) y TEXTO_DEMASIADO_LARGO de C-45, sin recortar el texto |
| C-05 | El tipo de empresa solo admite la lista de la carrera | C | F | F | US-09 | Las tres lentes la unen con C-46. CHECK `ck_proyecto_tipo_empresa` sin tabla catálogo y motivo TIPO_EMPRESA_INVALIDO, el nombre que eligen las tres lentes |
| C-06 | El RUC debe ser un RUC de 11 dígitos válido | F | F | C | US-10 | Las tres lentes la unen con C-44. El dígito verificador módulo 11 sale del sprint porque necesidad y tamaño lo sacan (D-19), y todos los RUC de aceptación lo cumplen igual para que la regla pueda entrar después sin cambiar ejemplos |
| C-07 | Un grupo con datos distintos no se parte en silencio | P | P | C | US-11 y US-07 | Tamaño y verificabilidad mantienen la consistencia del grupo y necesidad la saca, así que entra. Se aplica la regla sin mayoría que piden tamaño, verificabilidad y la crítica (D-A18), con el grupo rechazado entero. El código repetido (C-07b) pasa a US-07 |
| C-08 | Un estudiante del export sin proyecto queda a la vista | C | S | C | US-12 | El aviso ESTUDIANTE_SIN_PROYECTO se guarda una vez, sin fila, y la cuenta sale en la respuesta. Q17 no lo vigila, porque un estudiante sin proyecto es un estado válido, y la consulta de seguimiento S01 lo lista. El conteo de P2 pasa a US-23 |
| C-09 | Una plantilla con la estructura equivocada se detiene | S | S | C | US-13 | Verificabilidad prueba que subir el export como plantilla choca con `uq_archivo_origen_sha256`, así que ese caso responde 422 antes de escribir. PLANTILLA_SIN_HOJA se prueba con la hoja renombrada |
| C-10 | La columna ALUMNO se lee para validar y no se guarda | C | F | C | US-14 | Absorbe C-26 y C-43. Q04 suma «alumno» a su patrón y las tres tablas de proyecto a su filtro de `%nombre%`, y la columna se llama `organizacion` para no necesitar excepción |
| C-11 | Solo el profesor asignado sube la plantilla | C | F | C | US-06 | Absorbe C-53 con 403 y «La sección no está a su cargo.», como BR-ACCESO-07 y 08 de la spec 001 y la sección 6 del contrato. El 404 de C-53 se descarta |
| C-12 | La plantilla solo aplica a secciones Capstone | C | F | C | US-05 | Absorbe C-52 y C-24 con 409 antes de abrir la transacción, que eligen necesidad, verificabilidad y la crítica (D-A15). El tipo se lee de `plan_estudios.tipo_curso` y NO_APLICA pasa a US-23 |
| C-13 | Subir otra vez la misma plantilla no duplica nada | C | F | C | US-16 | Absorbe el segundo escenario de C-47 con la regla de FR-012 de la spec 001, que da 200 en la misma sección y 409 en otra. El 409 de otra plantilla publicada informa sin ofrecer reemplazo |
| C-14 | Reemplazar la plantilla sin borrar la anterior | M | M | S | Después | Necesidad y tamaño la mueven, porque depende de US-18 de la spec 001 (corte 2) y de D-11. V1_10 deja ya el estado REEMPLAZADA y `reemplaza_carga_proyecto_id` nula en `carga_proyecto` para no migrar otra vez |
| C-15 | Un fallo a mitad de la carga no deja nada escrito | C | S | S | US-17 | La restricción del fallo inyectado se llama `ck_proyecto_ruc` y el texto del 500 es el de la sección 6 del contrato |
| C-16 | Recibir la constancia de la plantilla | F | F | C | US-18 | Necesidad y tamaño reutilizan `GET /api/cargas/{carga_id}` con un bloque `proyectos` en lugar de una ruta nueva, y verificabilidad pide la ruta propia. Gana el bloque y la alternativa queda en J-14 |
| C-17 | El R-17 Capstone sale con la hoja «Cursos Capstone» | F | F | F | US-19 | Las tres lentes la unen con C-40. Su 409 sin plantilla se descarta a favor de C-41 |
| C-18 | La tabla maestra muestra los proyectos en el formato nuevo | F | F | F | US-21 | Las tres lentes la unen con C-28. La pantalla de vista previa sale, porque ningún contrato la pide |
| C-19 | Ver el estado de proyectos de mis secciones | S | S | C | US-23 | Suma la fila NO_APLICA de la 410 y los campos `estudiantes_con_proyecto` y `estudiantes_en_export` |
| C-20 | Marcar qué asignaturas del plan son Capstone | C | C | C | US-01 | Necesidad, verificabilidad y la crítica (D-A6) sostienen `plan_estudios.tipo_curso`, y tamaño propone `asignatura.tipo_curso`, que queda como alternativa de J-12. Sin `uq_plan_estudios_tipo`, ninguna asignatura marcada en la migración (hasta que D-14 se decide el 2026-10-29 y V1_10 marca 450025, 450024 y 450026) y el tercer escenario reemplazado por Q18 |
| C-21 | Guardar el proyecto de cada grupo en la base | R | R | R | Ninguna | Las tres lentes refutan la tabla por grupo, porque la plantilla trae una fila por estudiante y la tabla maestra repite los datos en cada fila. La crítica (D-A1) pide lo contrario y su alternativa queda en J-11 |
| C-22 | Ligar a cada estudiante con su grupo | R | R | R | Ninguna | Depende de C-21. La clave primaria (carga_proyecto_id, estudiante_id) ya da un grupo por estudiante |
| C-23 | Rechazar tipo de organización y RUC inválidos | F | F | F | US-09 y US-10 | Sus escenarios de base pasan a las dos historias sobre `proyecto_estudiante`. Los prefijos 10, 15 y 17 no se aceptan (D-19) |
| C-24 | Aceptar proyectos solo en secciones Capstone | F | R | F | US-05 y US-24 | La clave foránea compuesta hacia el plan se cambia por el 409 de la ruta y la consulta Q18 |
| C-25 | Vigilar los datos de proyecto con consultas nuevas | C | C | C | US-24 | Reescrita sobre el modelo único y numerada desde Q16, porque Q15 es de la spec 001. Una sección sin plantilla y un estudiante sin proyecto no son anomalías |
| C-26 | No guardar el nombre del estudiante | F | F | F | US-14 | Misma regla que C-10, con su escenario de la columna añadida en una transacción que se deshace |
| C-27 | Dar a abet_app solo los permisos de la carga de proyectos | C | C | C | US-02 | Necesidad y verificabilidad la mantienen como historia, igual que US-02 de la spec 001. Suma UPDATE por columnas de `carga_proyecto`, quita el USAGE de secuencias y recibe el DELETE denegado de C-53 |
| C-28 | Obtener la tabla maestra de Capstone desde la base | C | F | C | US-21 | Anfitriona de C-18 y C-50 para necesidad y verificabilidad. Usa los PI 1.1, 1.2 y 1.3, porque `asignatura_so` solo asocia a 450024 los SO 1 y 7 y `fk_plan_medicion_asig_so` impide los PI 5.x, y filtra la subida PUBLICADA para no duplicar filas |
| C-29 | Mantener la tabla maestra tradicional sin cambios | F | S | C | US-22 | Tamaño y verificabilidad la conservan como historia propia. La vista tradicional ya incluye las secciones Capstone y sigue así, y su tercer escenario se escribe sin condición |
| C-30 | Exponer el tipo de curso a la vista del R-17 | F | F | C | US-19 y US-22 | Dos lentes la unen con C-40. La columna `tipo_curso` al final de `v_r17_por_pi` es una nota de base de US-19 y el orden de columnas una prueba de US-22. El tercer escenario se retira por contradictorio |
| C-31 | Cargar proyectos inventados y bloquear los reales | F | F | C | US-15 y T025 | Dos lentes la sacan como historia. La semilla pasa a `tasks.md` y la guardia del RUC a US-15 |
| C-32 | Corregir los datos reemplazando | F | F | F | Después | Las tres lentes la unen con C-14, que sale del sprint |
| C-40 | R-17 Capstone con la hoja «Cursos Capstone» | C | S | C | US-19 | Anfitriona de C-17 y C-30. Toma la sección 420, el tipo desde `plan_estudios`, las dos huellas en «Constancia» y el logotipo conservado |
| C-41 | R-17 Capstone sin datos de proyecto | C | S | C | US-20 | El sufijo `_SIN_PROYECTOS` lo quita necesidad y lo conservan tamaño y verificabilidad, así que queda como propuesta de D-24. Suma el caso de 9 de 11 estudiantes |
| C-42 | Constancia con el conteo de proyectos y sin valores | C | F | F | US-18 y US-19 | Los conteos y los rechazos van al bloque `proyectos` de US-18 y la línea «10 de 11 estudiantes con datos de proyecto» a la hoja «Constancia» de US-19 |
| C-43 | La columna ALUMNO nunca se guarda | F | F | F | US-14 | Repite C-10 y aporta el escenario del rechazo que no repite el nombre |
| C-44 | El RUC de persona natural no se guarda | C | S | F | US-10 | Anfitriona para necesidad y tamaño. Motivos RUC_FORMATO_INVALIDO y RUC_PERSONA_NATURAL, el primero con el nombre que eligen dos lentes y la crítica |
| C-45 | Títulos y nombres que traen datos personales | M | P | C | US-08 y US-25 | El límite de longitud pasa a US-08. La declaración (C-45b) la conservan tamaño y verificabilidad y entra como US-25 del corte 2, en una columna de `carga_proyecto` y sin tabla nueva. Los patrones de DNI, correo y teléfono solo los conserva verificabilidad y quedan en D-28 |
| C-46 | Tipo de empresa de lista cerrada | F | S | C | US-09 | Unida con C-05. Su celda vacía va a CAMPO_VACIO y su escenario de la lista auxiliar K3:M5 queda en US-09 |
| C-47 | Registro del archivo de proyectos sin conservar sus bytes | F | S | F | US-03 y US-16 | Necesidad y verificabilidad la reparten. `carga.archivo_proyectos_id` se descarta, porque la plantilla tiene su propia subida |
| C-48 | Guardia de datos inventados en la plantilla | C | S | C | US-15 | Usa el mensaje literal de la spec 001 para el código y un patrón único de RUC inventado, `^20999[0-9]{6}$` |
| C-49 | Filas de estudiantes que no están en el export | F | S | F | US-07 y US-04 | Dos lentes la reparten entre C-03 y C-02 |
| C-50 | Vista de la tabla maestra Capstone sin datos personales | F | F | F | US-21 | Aporta las columnas exactas, la exclusión de la carga reemplazada y del curso de carrera, sin el privilegio a un rol de Power BI |
| C-51 | Reemplazar la carga retira los datos de proyecto | M | F | C | Después | Necesidad la mueve y tamaño la une al reemplazo, que también sale. La interacción con US-18 de la spec 001 queda en J-16 |
| C-52 | La plantilla solo entra en secciones Capstone | F | S | F | US-05 | Unida con C-12 con 409 |
| C-53 | Solo el profesor de la sección sube y descarga | F | S | F | US-06 y US-02 | Unida con C-11 con 403. El DELETE denegado pasa a US-02 |

Cuentas por lente, tomadas de la tabla.

| Lente | S | C | F | P | M | R |
| --- | --- | --- | --- | --- | --- | --- |
| Necesidad | 3 | 19 | 18 | 1 | 3 | 2 |
| Solapamiento y tamaño | 15 | 3 | 21 | 3 | 1 | 3 |
| Verificabilidad | 3 | 26 | 15 | 0 | 0 | 2 |

## Discrepancias entre lentes y cómo se resuelven

| Punto | Lo que dicen las lentes | Lo que adopta la spec | Razón |
| --- | --- | --- | --- |
| Nombre del motivo de código ajeno | N, T y V eligen CODIGO_FUERA_DEL_EXPORT frente a CODIGO_FUERA_DE_SECCION | CODIGO_FUERA_DEL_EXPORT | Tres lentes y un término por concepto |
| Celda vacía de RUC y de TIPO DE EMPRESA | N y V usan CAMPO_VACIO; T usa los motivos propios de cada columna | CAMPO_VACIO para las siete columnas obligatorias | Dos lentes |
| Dígito verificador del RUC | N y T lo sacan; V lo mantiene | Fuera del sprint, en D-19 | Dos lentes lo sacan |
| Prefijos de RUC | N y T rechazan solo el 10 como persona natural; V suma 15 y 17 | Prefijo 20 aceptado, 10 con RUC_PERSONA_NATURAL y los demás con RUC_FORMATO_INVALIDO | Dos lentes y la crítica (D-A9) |
| Nombre del motivo de forma del RUC | N, T y la crítica dicen RUC_FORMATO_INVALIDO; V dice RUC_FORMA_INVALIDA | RUC_FORMATO_INVALIDO | Dos lentes |
| Nombre del motivo de longitud | N y la crítica dicen TEXTO_DEMASIADO_LARGO; V dice CAMPO_LARGO | TEXTO_DEMASIADO_LARGO | Desempata la crítica |
| Límites de longitud | N y la crítica dan 300, 200 y 120; V da 300, 200 y 200 | 300, 200 y 120 como valor provisional de D-21 | Desempata la crítica |
| Ruta de la constancia | N y T amplían `GET /api/cargas/{carga_id}`; V pide `GET /api/cargas-proyecto/{id}` | Bloque `proyectos` en la ruta existente | Dos lentes, con J-14 abierta |
| Código de la sección que no es Capstone | N, V y la crítica dan 409; C-12 daba 422 | 409 antes de abrir la transacción | Tres votos |
| Respuesta a un profesor ajeno | N, T y V dan 403; C-53 daba 404 | 403 con «La sección no está a su cargo.» | Tres lentes y la spec 001 |
| Sufijo `_SIN_PROYECTOS` | N lo quita; T y V lo mantienen | Se mantiene como (propuesta) de D-24 | Dos lentes |
| Declaración sin personas (C-45b) | N la mueve; T y V la mantienen | US-25 en el corte 2 | Dos lentes, y el corte 2 recoge la razón de necesidad (sin objeto con datos inventados) |
| Grupo inconsistente (C-07a) | N la mueve; T y V la mantienen sin mayoría | US-11, con el grupo rechazado entero | Dos lentes y la crítica (D-A18) |
| Tipo de curso | N, V y la crítica dicen `plan_estudios`; T dice `asignatura` | `plan_estudios.tipo_curso`, con J-12 abierta | Dos lentes y la crítica |
| Nombre de la columna de organización | V y la crítica dicen `organizacion`; N dice `nombre_organizacion` | `organizacion` | Evita la excepción de Q04 |
| Nombre de la columna de tipo | N y V dicen `tipo_empresa`; la crítica dice `tipo_organizacion` | `tipo_empresa` | Dos lentes y el rótulo de la plantilla |

## Piezas que agrega la auditoría

| Pieza | Lo propone | Historia o requisito final |
| --- | --- | --- |
| Motivo GRUPO_INVALIDO para un grupo 0, negativo, decimal o no numérico | V (C-04) | US-08 y FR-009 |
| Consulta de seguimiento S01, que lista a los estudiantes del export sin proyecto y no es control | V (C-08) | US-12 y FR-012 |
| Consultas de control Q16 a Q20 con la prueba de paridad de `controles_neon.sql` ampliada | N, T, V y la crítica (D-A16) | US-24 y FR-021 |
| `tipo_fuente` de `archivo_origen` ampliada a varchar(20) y clave compuesta (archivo_id, tipo_fuente) | V (C-01) y la crítica (D-A4) | US-01 y FR-002 |
| Clave foránea compuesta de `carga_proyecto` hacia `uq_carga_seccion` | La crítica (D-A3) | US-03 y FR-003 |
| Semilla Capstone inventada (secciones 420 y 421 de 450024, PI 1.1 a 1.3, sin marca de tipo, que pasa a V1_10 con D-14) | N, T y V (C-31) | T025 y FR-024 |
| Reemplazo del export de la spec 001 en una sección con plantilla publicada | V (C-51) | J-16 |
| Mapa de celdas de la hoja «Cursos Capstone» como tarea con su prueba sin fórmulas ni `#REF!` | La crítica (D-A19) | T033 y D-25 |

## Datos de prueba unificados

Todas las candidatas se reescriben con los mismos datos inventados, tomados de las correcciones de necesidad y verificabilidad. La sección Capstone es la 420 de 450024 «Proyecto de Ingeniería Aplicada I» en 2026-2, con los PI 1.1, 1.2 y 1.3 y los códigos 99000101 a 99000111, y la 421 de la misma asignatura usa 99000112 a 99000122 para que Q08 no vea a un estudiante en dos secciones del mismo curso. La sección de carrera es la 410 de 450002 de la spec 001. La plantilla inventada tiene 11 filas en 4 grupos (3, 3, 3 y 2 integrantes). Los RUC inventados empiezan con 20999 y cumplen el dígito verificador módulo 11 (20999999906, 20999999914, 20999999922, 20999999931 y 20999999949), comprobado con los pesos 5, 4, 3, 2, 7, 6, 5, 4, 3 y 2, y ninguno corresponde a una organización real. Los RUC de rechazo de la guardia (20123456781) y de persona natural (10999999991) fallan ese dígito, así que tampoco pueden ser el RUC de una organización o una persona real.

## Veredicto del crítico de arquitectura

| Decisión | Veredicto | Razón | Alternativa | Lo que adopta la spec |
| --- | --- | --- | --- | --- |
| D-A1. Una fila por estudiante (`proyecto_estudiante`) frente a una fila por grupo con integrantes | CAMBIAR | La fila por estudiante copia título, RUC y organización en cada integrante, y la base puede guardar dos identidades para un grupo | `carga_proyecto`, `proyecto` por grupo y `proyecto_integrante` | Se mantiene `proyecto_estudiante`, porque las tres lentes refutan C-21 y C-22, la plantilla y la tabla maestra son por estudiante y el lector rechaza el grupo inconsistente antes de escribir (US-11) con Q19 de respaldo. La alternativa queda en J-11 |
| D-A2. Subida propia de la plantilla frente a colgarla de `abet.carga` | CAMBIAR | Los contadores de `carga` están atados al export por `ck_carga_filas`, `ck_carga_conciliada` y `fk_carga_archivo` | `carga_proyecto` con sus conteos y las mismas restricciones que `carga` | Adoptada. C-42 y C-47 dejan de tocar `abet.carga` |
| D-A3. Atar la subida a la carga del export con clave foránea hacia `carga_fila` | SE_SOSTIENE | La clave compuesta vuelve imposible un proyecto de un estudiante que no está en el export | `carga_proyecto.carga_id` NOT NULL con clave compuesta hacia `uq_carga_seccion` | Adoptada, y el estado PUBLICADA de la carga lo comprueban la API (409) y Q16 |
| D-A4. Reusar `archivo_origen` con PLANTILLA_PROYECTOS | CAMBIAR | `tipo_fuente` es varchar(17), PLANTILLA_PROYECTOS mide 19 y nada impide que una subida apunte a un export | varchar(20), `uq (archivo_id, tipo_fuente)` y clave compuesta desde `carga_proyecto` | Adoptada. La misma protección para `abet.carga` queda como deuda, porque toca el corte 1 de la spec 001 |
| D-A5. Rechazos en tabla propia frente a ampliar `rechazo_fila` | CAMBIAR | `rechazo_fila` tiene clave hacia `carga` y nombra la columna con `carga_columna_id`, y las candidatas dan dos nombres a un motivo | `rechazo_proyecto` propia con lista única de motivos | Adoptada con la lista de FR-008, y J-13 la deja abierta solo para el nombre |
| D-A6. Tipo de curso en `plan_estudios` frente a `asignatura` | SE_SOSTIENE | `asignatura` no tiene carrera y `plan_estudios` ya es la asignatura en una versión de catálogo | `plan_estudios.tipo_curso` NOT NULL DEFAULT 'CARRERA' sin marcar ninguna en la migración | Adoptada (US-01), con J-12 |
| D-A7. Impedir en la base proyectos en secciones de carrera | DUDOSA | Cuatro columnas redundantes en cada grupo y la marca congelada para siempre | La garantía una sola vez en `carga_proyecto` con clave compuesta hacia el plan | Se adopta el 409 de la ruta y Q18 (US-05 y US-24), con la clave en la base como alternativa de J-15 |
| D-A8. Tipo de organización como tabla catálogo o CHECK | CAMBIAR | Tres valores fijos no justifican una tabla, una semilla y un permiso | CHECK con la forma canónica guardada | Adoptado el CHECK `ck_proyecto_tipo_empresa`. La columna se llama `tipo_empresa`, como el rótulo, por las dos lentes |
| D-A9. Reglas del RUC | CAMBIAR | Las tres reglas de las candidatas se contradicen y un RUC 10 contiene un DNI (documento nacional de identidad) | `ck_proyecto_ruc` con `^20[0-9]{9}$`, lectura como texto y módulo 11 en el lector | Adoptado salvo el módulo 11, que sale del sprint (D-19). Todos los ejemplos de aceptación cumplen el dígito |
| D-A10. Patrón de la guardia del RUC | CAMBIAR | Dos patrones para la misma guardia dan pruebas contradictorias | Un único CHECK solo en Neon | Adoptado `ck_proyecto_ruc_inventado` con `^20999[0-9]{6}$` (US-15) |
| D-A11. Vista nueva `v_tabla_maestra_capstone` | SE_SOSTIENE | El formato nuevo tiene otras columnas y Power BI ya consume la tradicional | Construirla sobre las tablas base y no sobre otra vista, por el DROP VIEW ... CASCADE de Flyway | Adoptada (US-21 y FR-018) |
| D-A12. Tradicional sin cambios y `tipo_curso` en `v_r17_por_pi` | CAMBIAR | El DROP VIEW de una `R__` borra los privilegios y `v_r17_por_pi` une `plan_medicion` y no `plan_estudios` | `tipo_curso` al final de `v_r17_por_pi` con JOIN a `plan_estudios` y `crear_rol_app.sql` repetido tras el migrate | Adoptada (US-19, US-22 y T021). `v_tabla_maestra_pi` no gana `tipo_curso` en este sprint |
| D-A13. Reemplazo por subida frente a reemplazo por grupo | CAMBIAR | El reemplazo por grupo mezcla archivos y exige UPDATE sobre los proyectos | Reemplazo de la subida entera, como `abet.carga` | Adoptado en el diseño de `carga_proyecto`, con el reemplazo fuera del sprint |
| D-A14. Permisos de `abet_app` | CAMBIAR | Sin UPDATE la API no cierra la subida, y las columnas de identidad no piden permisos de secuencia | INSERT, UPDATE por columnas de `carga_proyecto` y SELECT, sin secuencias | Adoptada (US-02) |
| D-A15. Códigos HTTP y mensajes | CAMBIAR | Tres pares de candidatas se contradicen sobre la misma ruta | 403 para el ajeno, 409 para la sección no Capstone y 200 o 409 para el archivo repetido, fijados en el contrato | Adoptada (US-05, US-06 y US-16, T014) |
| D-A16. Numeración de las consultas de control | CAMBIAR | Q15 ya existe y cada candidata da otro significado a Q16 a Q20 | Numerar una vez desde Q16 y ampliar la prueba de paridad | Adoptada con Q16 a Q20 (US-24). Q21 de la crítica no entra, porque necesidad y tamaño retiran la comparación con `medicion` |
| D-A17. Q04 y la columna ALUMNO | CAMBIAR | Una excepción por nombre de columna debilita Q04 | Columna `organizacion` y tablas de proyecto en Q04 sin excepciones | Adoptada (US-14) |
| D-A18. Plantilla incompleta y grupo por mayoría | CAMBIAR | La mayoría decide sin saber cuál título es el correcto | Publicar con aviso y rechazar el grupo entero sin mayoría | Adoptada (US-11 y US-12) |
| D-A19. R-17 Capstone sin plantilla | DUDOSA | Bloquear o no es decisión de la carrera y la hoja exige su propio mapa de celdas | 200 con franja como valor provisional y el mapa de celdas como tarea | Adoptada (US-20, D-24, D-25 y T033) |
| D-A20. Declaración y patrones de datos personales | DUDOSA | Una tabla aparte es más de lo necesario y los patrones dan falsos positivos | Columnas en `carga_proyecto` y patrones limitados | Declaración en columnas de `carga_proyecto` (US-25, corte 2). Los patrones quedan fuera (D-28) |
| D-A21. La plantilla solo después del export publicado | SE_SOSTIENE | Es la condición de la clave hacia `carga_fila` | Campos nuevos de `GET /api/secciones` como opcionales | Adoptada (US-04 y US-23) |
| D-A22. Atomicidad y constancia propia | SE_SOSTIENE | Repite FR-012 y FR-021 de la spec 001 | Mantenerla | Adoptada (US-17 y US-18) |

La crítica deja tres decisiones con DUDOSA (D-A7, D-A19 y D-A20), cinco con SE_SOSTIENE y catorce con CAMBIAR. Quedan sin verificar el mapa real de celdas de «Cursos Capstone» (B5:P272, 43 rangos combinados y un logotipo), que el integrador describe sin abrir el libro, y la fila del encabezado de la plantilla real de proyectos. La spec los cubre con T033 y con una plantilla inventada que fija su encabezado en la fila 1 (propuesta).

## Revisión de la spec (2026-10-29)

Tres revisores leen la spec escrita y dejan diez hallazgos. La corrección no cambia ningún veredicto de las lentes ni del crítico, y solo suma dos escenarios (83 en total).

| Hallazgo | Severidad | Corrección |
|---|---|---|
| La guardia encendida en los Antecedentes contradice los ejemplos de RUC mal formado y de celda vacía | Alta | FR-014, US-15, el orden de los Edge Cases, el contrato y una nota del `.feature` dicen que la guardia solo mira un código de 8 dígitos o un RUC con la forma `^20[0-9]{9}$`, y lo demás sigue a las reglas por fila |
| `filas_de_datos` de la plantilla sin definir y sin atar al archivo | Media | FR-003 suma la FK (archivo_id, filas_de_datos) hacia `uq_archivo_origen_filas`, FR-011 define la medida, y el escenario de K3:M5 comprueba `filas_de_datos` 2 |
| Las tareas de base rompen `correr_pruebas.sh` y A05 | Media | T022, T025 y T026 cubren la foto previa a V1_10, el archivo sintético aparte, A05 y la línea RESULTADO, y `plan.md` nombra los archivos |
| Power BI sin SELECT sobre la vista nueva | Media | FR-020 y la tarea nueva T028 suman la vista a `crear_roles_lectura.sql` y al callback, con su prueba de `has_table_privilege` |
| Cinco mensajes de los `.feature` ausentes del contrato | Media | El contrato suma la tabla de mensajes por fila (siete textos), y `spec.md` suma los de GRUPO_INVALIDO, GRUPO_INCONSISTENTE y el aviso |
| Tipo de curso de una sección sin plan de medición | Baja | FR-007 responde el 422 de la spec 001, FR-023 da `tipo_curso` nulo y NO_APLICA, con un escenario nuevo en cada `.feature` (propuesta) |
| Piezas menores de FR-003 a FR-007 | Baja | `uq_carga_proyecto_carga`, `columna` nula según el motivo y el texto del 409 con `{numero}` |
| T037 condicional | Baja | T037 pasa a una prueba que falla mientras el reemplazo del export exista sin el 409 de J-16 |
| `security_barrier` sin justificar | Baja, parcialmente falsa | Las vistas `R__` de este `db/` no lo usan, pero sus versiones del subtree de `preparacion-neon` sí, y `crear_roles_lectura.sql` lo exige (líneas 128 a 130). FR-018 lo dice en lugar de quitarlo |
| La hoja «Hoja1» remite a una decisión equivocada | Baja, falsa | D-26 ya pregunta «¿Se identifica la hoja por el nombre «Hoja1» o se toma la primera?», así que la remisión queda |

## Ajuste con los R-17 reales de Capstone (2026-10-29)

Jefferson adjunta ocho R-17 reales de 560073 «Proyecto de Ingeniería Aplicada II» de Ingeniería Industrial del periodo 2025-1, y el integrador los resume sin copiar ningún dato personal. El ajuste no cambia ningún veredicto de las lentes ni del crítico, conserva la numeración de historias, decisiones y escenarios y suma dos escenarios al final de `evidencia_capstone.feature` (85 en total).

| Hecho observado | Efecto en la spec |
|---|---|
| Los ocho R-17 usan el formato de siempre y ninguno trae la hoja «Cursos Capstone» | D-25 pregunta si la Oficina de Calidad adopta esa hoja, y el valor provisional la conserva |
| Los ocho miden solo el PI 2.3 del SO 2, que el catálogo de Ambiental no tiene, y la hoja «Base de Cursos - SO» coincide con `asignatura_so` de V1_03 | D-29 deja los PI en `plan_medicion` por curso y periodo, sin PI fijo en el código |
| Cada fila trae solo el CÓDIGO y la nota, sin datos de proyecto ni SO, PI o PROFESOR | D-16 deja como obligatorias solo CÓDIGO DEL ESTUDIANTE y CALIFICACIÓN |
| El profesor es un dato de la sección, con nombres y firma en origen | D-17 deja vacíos la cabecera y la columna PROFESOR y pregunta a Jefferson, y el escenario nuevo de US-19 lo prueba |
| Las fórmulas de los conteos y la fecha tienen rangos desplazados en 4 de 8 archivos | FR-017 escribe también los conteos y la fecha como valores, y T034 lo prueba |
| La plantilla base admite 224 filas, de la 49 a la 272, y la sección real más grande tiene 36 estudiantes | El caso límite del R-17 fija las 224 filas, y el esquema nuevo de US-19 prueba 222 y 225 mediciones |
| Las tolerancias de lectura y la norma de privacidad de un importador de R-17 históricos | Quedan en Fuera de alcance, porque la spec 002 genera el R-17 y no lo importa |
