# Revisión por refutación de las historias del nombre del profesor

**Fecha**: 2026-11-24
**Spec**: [spec.md](./spec.md)
**Entrada**: 19 candidatas escritas desde tres ángulos, el del administrador técnico de la base (C-A01 a C-A04), el de la coordinación y el profesor que leen el R-17 (C-C01 a C-C07) y el de la privacidad y la evidencia ABET (C-P01 a C-P08), cada una con su base en el código y su Gherkin en español
**Salida**: 5 historias (US-95 a US-99) en 4 archivos `.feature`
**Fuentes**: los informes de las tres lentes y del crítico de arquitectura de la sesión del 2026-11-24, cotejados con `develop` (e9b5c7e) del Back. Ninguna candidata ni esta revisión copia un nombre real

## Pedido

Jefferson pregunta el 2026-11-24 «no tenemos campo del nombre del profesor en las tablas? porque normal si le asignas nombre a los correos de prueba». Ante la pregunta de qué va en D10 cuando la sección tiene varios profesores, responde «Sí, escribe la spec con los profesores asignados».

## Objetivo

La base guarda el nombre de cada profesor en `acceso`, fuera de `abet`, y la celda D10 del R-17 («Profesor:», combinada D10:I10, hoy vacía por BR-R17-07 y D-12) sale llena con los nombres de los profesores asignados a la sección. Los nombres reales viven solo en Neon y los de git son inventados, como pide D-10 con la Ley 29733 de protección de datos personales y su reglamento, el Decreto Supremo (DS) 016-2024-JUS.

## Método

Cada candidata parte refutada y sobrevive solo si resiste tres lentes independientes, como en las specs 001 y 003 a 009. La lente de necesidad pregunta si la exige el pedido, la plantilla del R-17 o una regla vigente. La lente de solapamiento y tamaño aplica INVEST (independiente, negociable, valiosa, estimable, pequeña y verificable) y busca choques con las historias que ya existen. La lente de verificabilidad comprueba que cada escenario se pruebe con pytest-bdd en el clúster desechable, contra el código, la plantilla y la base. Un crítico de arquitectura juzga aparte las decisiones técnicas con SE_SOSTIENE, CAMBIAR o DUDOSA.

Los veredictos posibles son SOBREVIVE (S), CORREGIR (C), FUSIONAR (F), PARTIR (P), MOVER_A_DESPUES (M) y REFUTADA (R). Una candidata sale cuando dos lentes o más la marcan R o M, como en las specs anteriores. Cuando las lentes discrepan en otro punto, la tabla de discrepancias dice qué razón decide.

## Candidatas por ángulo

Administrador técnico de la base.

- C-A01. La base guarda el nombre del profesor, opcional y normalizado.
- C-A02. La programación docente puede traer el nombre.
- C-A03. El rol de la aplicación solo lee el nombre y un control Q22 lo vigila.
- C-A04. Los datos de prueba y develop de Neon llevan solo nombres inventados.

Coordinación y profesor que leen el R-17.

- C-C01. El profesor tiene nombre en la base.
- C-C02. La carga de la programación docente trae el nombre.
- C-C03. D10 del R-17 trae los nombres de los profesores asignados.
- C-C04. Un profesor sin nombre no rompe el R-17.
- C-C05. La sección sin profesor sigue teniendo R-17.
- C-C06. El nombre del profesor no sale en ningún otro documento ni registro.
- C-C07. Las pantallas muestran el nombre.

Privacidad y evidencia ABET.

- C-P01. El nombre del profesor vive solo en `acceso`.
- C-P02. Q04 y Q15 vigilan que el nombre no salga de `acceso`.
- C-P03. Ningún nombre entra a git ni a los registros.
- C-P04. La carga de la programación completa el nombre.
- C-P05. D10 del R-17 muestra a los profesores asignados con el prefijo «Profesor: » o «Profesores: ».
- C-P06. La constancia nombra a quien sube la carga.
- C-P07. Un profesor reemplazado a mitad de ciclo no cambia la evidencia emitida.
- C-P08. La baja de un usuario no borra su nombre y su retiro es un acto aparte.

## Veredictos por candidata

| Candidata | Necesidad | Solapamiento y tamaño | Verificabilidad | Destino |
| --- | --- | --- | --- | --- |
| C-A01 | F con C-C01 y C-P01 y C, quitar «sin dígitos» | F con C-C01, quitar «sin dígitos» y conservar el `COMMENT ON SCHEMA acceso` | C, «sin dígitos» rechaza «Docente Inventado 410» y PostgreSQL no tiene clase para la categoría Unicode Cf | US-95. Conserva la regla sin dígitos y cambia los nombres inventados a letras (ver discrepancia 1) |
| C-A02 | F con C-C02 y C-P04 y C | F con C-C02 y C-P04, reescribir FR-002, FR-005 y FR-007 de la spec 006 | C, la línea «Resumen.» de tres términos está fijada, y fijar si un usuario nuevo cuenta como nombre completado | US-96 |
| C-A02, mayúsculas (D-59 de la candidata) | M | M | C, la regla estropea «Del Río» | Sale por dos lentes. El nombre se guarda como llega (AD-62) |
| C-A02, herramienta de corrección (D-60 de la candidata) | R | M, fuera de la spec | sin veredicto | Sale por dos lentes. El procedimiento de corrección queda en J-70 |
| C-A03 | C, reducir a dos escenarios y R para Q22 | F con C-C01 y R para Q22 | P, sobreviven los permisos, `abet_respaldo` sí lee `acceso` y Q22 queda R | Escenarios de US-95. Q22 sale por las tres lentes |
| C-A04 | S fusionada y C, la guardia de git a M | F con C-C06 y C-P03 | C, `docente412` no existe, la sección con dos profesores se siembra en el paso Dado y las semillas con `DO NOTHING` no llenan develop de Neon | US-99 y FR-013, con la prueba de repositorio (ver discrepancia 3) |
| C-C01 | F con C-A01 y C-P01 | S, base de la fusión | F con C-A01, el filtro de Q15 no casa `nombre` y hay que ampliarlo | US-95 |
| C-C02 | F con C-A02 y C-P04 | F, sin el escenario del COORDINADOR | F con C-A02, los nombres inventados no cumplen la guardia y el aviso no lleva la fila | US-96, sin el nombre de la coordinación (AD-64) |
| C-C03 | S, F con C-P05 y C, solo PROFESOR y sin filtro de `activo` | S, cubrir Ambiental e Industrial y construir después de `fix/r17-recuadros-y-filas-de-pi` | C, cada Dado necesita la declaración vigente, D10:I10 necesita su propia cabida y `casefold` no quita tildes | US-97 |
| C-C04 | S, como escenarios de la historia de D10 | S, historia propia con C-C05 | C, la hoja «Constancia» sí trae el correo de quien sube | US-98 (ver discrepancia 2) |
| C-C05 | F con C-C04 | F con C-C04 | F con C-C04, con una carga de la 704 subida por la coordinación en el corte 2 | Escenario de US-98 |
| C-C06 | F en la historia de D10 y C, suma el registro `abet.api` | S fusionada, absorbe C-A04 y C-P03 | P, el libro con openpyxl y las rutas sobreviven, la lista de nombres pasa a C-A04 | US-99 (ver discrepancia 3) |
| C-C07 | M | M | M | Sale por las tres lentes, a «Fuera de alcance» |
| C-P01 | F con C-A01 y C-C01 | F con C-C01 | F con C-A01 | US-95 |
| C-P02 | F con la historia de la columna, R para la lista blanca de Q04 | F con C-C01, R para la lista blanca | C, `controles_neon.sql` no trae Q15 y ninguna prueba corre contra producción | Escenarios de Q04 y Q15 en US-95. La lista blanca sale |
| C-P03 | P, el registro y el informe quedan, la guardia de git a M | F con C-C06 | P, el registro con `caplog` queda y `GUARDIA_DATOS_INVENTADOS` es otra cosa | US-99, con una prueba de repositorio y sin variable de entorno |
| C-P04 | F con C-A02 y C-C02 | F con C-A02 | F con C-A02, el rechazo ocurre antes de conectarse y no en ROLLBACK | US-96 |
| C-P05 | F con C-C03 y C | F con C-C03, R para el prefijo, el filtro de `activo` y el aviso | F con C-C03, el prefijo repite el rótulo de B10:C10 | US-97, sin prefijo, sin filtro de `activo` y sin aviso en «Constancia» |
| C-P06 | M | M | M | Sale por las tres lentes, a «Fuera de alcance» |
| C-P07 | R | R, la variante `desasignado_en` a M | F con C-C03, reducida al profesor dado de baja | Sale por dos lentes. El profesor dado de baja entra como escenario de US-97 y el corte temporal queda en J-67 |
| C-P08 | M | R como historia | R | Sale por las tres lentes. El retiro del nombre queda como procedimiento en J-70 |

## Discrepancias entre las lentes y cómo se deciden

1. **Dígitos en el nombre.** Necesidad y solapamiento quitan «sin dígitos» de la restricción, porque choca con «Docente Inventado 701». El crítico conserva la regla (AD-61) y escribe los nombres inventados con letras. Decide la razón del crítico, porque la regla frena un código de estudiante de ocho dígitos pegado en la columna, mientras que la razón de las lentes solo nace de la forma de los nombres inventados, que cambia sin costo. Los nombres inventados de la spec son «Profesor Inventado Setecientos Uno» y parecidos.
2. **Historia propia para el profesor sin nombre.** Necesidad lo pone como escenarios de la historia de D10, y solapamiento y verificabilidad lo dejan como historia propia. Queda como US-98, porque todos los usuarios actuales tienen el nombre nulo, así que es el caso de partida en Neon, y porque decide algo propio (sin correo de relleno ni aviso).
3. **Guardia de los datos inventados.** Necesidad mueve la guardia de git a después, y solapamiento, verificabilidad y el crítico (AD-82) la conservan como prueba de repositorio. Queda en US-99 como prueba de repositorio, porque el repositorio es público, el pedido trae nombres a los datos de prueba por primera vez y la prueba solo lee las semillas y `git ls-files`.
4. **Filtro de rol en D10.** Necesidad pide `rol = 'PROFESOR'`, como `abet_carga/avance.py`, y el crítico (AD-68) y solapamiento lo ven sobrante porque Q20 ya impide una coordinación activa con secciones. Queda el filtro de rol, porque Q20 no cubre una cuenta COORDINADOR inactiva con secciones, el rótulo dice «Profesor:» y `avance.py` ya define así al profesor de una sección. El filtro de `activo` sale, como piden las tres lentes.
5. **Cambio de Q15.** Necesidad, solapamiento y el crítico (AD-78) amplían el filtro de Q15 con `nombre` para `acceso`. Verificabilidad prefiere dejar Q15 y agregar un bloque aparte, porque el paso `_correr_q15` de `tests/aceptacion/pasos/test_base_neon_feature.py` simula Q15 con el texto de Q04. Se amplía Q15 y el paso pasa a correr el bloque de Q15 de `db/pruebas/pruebas.sql`, porque un segundo bloque repetiría el mismo filtro con otro nombre.
6. **Control en Neon.** El crítico sostiene un Q22 en `controles_neon.sql` con el filtro de Q15 (AD-80) y un control que cuente profesores sin nombre (AD-73). Las tres lentes refutan Q22. Q22 sale, porque Flyway aplica a Neon las mismas migraciones que `correr_pruebas.sh` prueba con Q15, y porque un control nuevo cambia `CONTROLES_ADMITIDOS` y el texto RESULTADO sin cubrir nada que Q15 no cubra. El conteo de AD-73 entra como consulta informativa y no como control, porque hoy todos los profesores de Neon tienen el nombre nulo y un control fallaría desde el primer día.

## Veredicto del crítico de arquitectura

El crítico extrae 26 decisiones técnicas (AD-57 a AD-82) y juzga aparte la decisión D-12, que no es técnica. Resultan 13 SE_SOSTIENE, 12 CAMBIAR y 1 DUDOSA, más D-12 como DUDOSA.

| ID | Decisión | Veredicto | Razón | Alternativa que adopta la spec |
| --- | --- | --- | --- | --- |
| AD-57 | El nombre vive en `acceso.usuario_autorizado.nombre` y en ninguna tabla de `abet` | SE_SOSTIENE | Q04 prohíbe `%nombre%` en cinco tablas de `abet` y `usuario_id` ya une `carga.subida_por` y `docente_seccion` | La de la candidata (US-95) |
| AD-58 | Una sola columna `nombre` | SE_SOSTIENE | D10 es texto libre y `apellido` está en la expresión de Q04 y Q15 | Una columna (J-65) |
| AD-59 | La columna admite nulo | SE_SOSTIENE | Los usuarios cargados y las coordinaciones no traen nombre | Nulo, y el faltante se cuenta con la consulta informativa de US-98 |
| AD-60 | `varchar(120)` con la normalización Unicode NFC (forma de normalización canónica compuesta) solo en el guion | CAMBIAR | El dueño también escribe por SQL, y un nombre en NFD o con un carácter de formato se ve igual y ordena distinto | La restricción suma `nombre IS NFC NORMALIZED` y una clase explícita de caracteres de formato, y el guion aplica la misma regla antes de conectarse (FR-001 y FR-004) |
| AD-61 | La restricción rechaza dígitos | CAMBIAR | Rechaza los nombres inventados con número | Se conserva la regla y los nombres inventados van en letras (J-66) |
| AD-62 | El guion pasa a mayúscula inicial un nombre que llega en mayúsculas | CAMBIAR | Altera apellidos como McDonald o De la Puente | El nombre se guarda como llega, recortado, con espacios colapsados y en NFC |
| AD-63 | Columna opcional `nombre` en el CSV (valores separados por comas) de `cargar_programacion.py` | SE_SOSTIENE | Reúsa la guardia de archivo dentro de git, la transacción y el informe sin valores | US-96, con los cambios fechados de FR-002, FR-005, FR-007 y FR-009 de la spec 006 |
| AD-64 | La coordinación recibe su nombre por una fila del CSV | CAMBIAR | Cada fila crea una asignación y Q20 marca una coordinación activa con secciones | La coordinación queda sin nombre en la spec 010 |
| AD-65 | Un nombre se corrige con un UPDATE manual y el retiro es un procedimiento escrito | CAMBIAR | Un literal escrito en una sesión interactiva de psql queda en su historial en el Windows | Corrección y retiro con psql no interactivo desde la Mac por `en_windows.py`, con el valor por la entrada estándar, sin herramienta nueva (J-70). Las banderas `--corregir-nombres` y `--retirar-nombres` del crítico quedan como alternativa, porque dos lentes sacan la herramienta |
| AD-66 | D10 empieza por «Profesor: » o «Profesores: » | CAMBIAR | La plantilla ya trae el rótulo en B10:C10 | D10 lleva solo los nombres y B10 no cambia |
| AD-67 | Separador «; » y orden alfabético sin mayúsculas ni tildes, con `usuario_id` de desempate | SE_SOSTIENE | El orden es estable entre generaciones | Orden en Python, sin diacríticos por la descomposición NFD más `casefold()`, y no con `ORDER BY` del cotejo de cada base (J-68) |
| AD-68 | D10 lista solo a los PROFESOR activos | CAMBIAR | La baja borraría al profesor de todos sus R-17 | Sin filtro de `activo`. El filtro de rol se conserva (discrepancia 4) |
| AD-69 | La evidencia emitida no cambia cuando cambia el equipo | DUDOSA | El libro se genera en cada descarga, y `desasignado_en` es una migración que nadie pide | J-67 deja el valor provisional sin corte temporal y anota el filtro `asignado_en <= carga.terminada_en` del crítico como alternativa |
| AD-70 | Un profesor sin nombre se omite y su correo no lo reemplaza | SE_SOSTIENE | BR-R17-07 deja el correo solo en la hoja «Constancia» | US-98 |
| AD-71 | Una sección sin profesor responde 200 con D10 vacía | SE_SOSTIENE | Un 409 nuevo bloquea una entrega que hoy funciona | US-98 |
| AD-72 | La hoja «Constancia» avisa «Sin nombre registrado del profesor» | CAMBIAR | BR-R17-09 y BR-R17-10 fijan el cuerpo de la constancia | Sin aviso en el libro |
| AD-73 | Ningún control cuenta los profesores asignados sin nombre | CAMBIAR | D10 puede quedar vacía en silencio en todo un periodo | Consulta informativa `db/plataforma/neon/profesores_sin_nombre.sql`, que solo cuenta, en lugar del control Q23 (discrepancia 6) |
| AD-74 | D10 ajusta el texto y calcula el alto de la fila 10, sin tope ni 422 | SE_SOSTIENE | Truncar un nombre es peor que una fila alta | Construir después de fusionar `fix/r17-recuadros-y-filas-de-pi`, con `lineas_del_recuadro()` y el ancho de D10:I10 |
| AD-75 | El nombre se lee en la transacción de `generar()` y se escribe con `_escribir` | SE_SOSTIENE | La constancia, las cifras y D10 salen de la misma foto (BR-R17-12) | La de la candidata |
| AD-76 | La interfaz de programación de aplicaciones (application programming interface, API) expone el nombre en `subida_por` o en `/api/sesion` | CAMBIAR | Cambia el contrato del Front y amplía la exposición | La spec no cambia la API, la sesión ni la constancia, y US-99 lo prueba |
| AD-77 | `abet_app` lee la columna y no la escribe, y ningún rol de lectura la alcanza | SE_SOSTIENE | `abet_respaldo` sí lee todo `acceso`, así que el nombre viaja al respaldo del Windows | `probar_rol_app.sql` prueba el 42501, y la spec declara el respaldo dentro del tratamiento de la Ley 29733 |
| AD-78 | Q04 y Q15 no cambian de texto | CAMBIAR | Q15 no ve una columna `nombre` en `acceso` | Q15 amplía su filtro y espera `usuario_autorizado.correo` y `usuario_autorizado.nombre` |
| AD-79 | Q04 se amplía con una lista blanca | SE_SOSTIENE no ampliarlo | La lista blanca se rompe con cada tabla nueva | Q04 no cambia |
| AD-80 | Un control hermano de Q04 en Neon | SE_SOSTIENE con otro alcance | Neon no corre Q15 | Sale. Ver discrepancia 6 |
| AD-81 | `V1_16` solo con definición de datos (data definition language, DDL), primero en develop de Neon desde el Windows con respaldo | SE_SOSTIENE | La última migración es V1_15 y el comentario del esquema dice que el correo es el único dato de contacto | J-71 |
| AD-82 | Nombres «Docente Inventado NNN» y una guardia que reúsa `GUARDIA_DATOS_INVENTADOS` | CAMBIAR | Los dígitos chocan con AD-61 y esa variable es la guardia de códigos 99 que D-10 retiró | Prueba de repositorio con la forma «Profesor Inventado» seguida de palabras con letras, sobre las semillas cargadas, y `git ls-files` sin CSV con la columna `nombre` |
| D-12 | Nombre del profesor en el R-17 | DUDOSA | Pertenece a la Coordinación de Ambiental y a la Oficina de Calidad, y su valor provisional sostiene BR-R17-07 | El valor provisional de D-12 pasa a «D10 con los profesores asignados» por el pedido de Jefferson, D-12 sigue abierta y el llenado de D10 vive en una función aislada que se revierte sin tocar el resto de la cabecera |

## Hechos del código que corrigen supuestos de las candidatas

- El filtro de Q15 (`db/pruebas/pruebas.sql`, línea 1384) busca `apellido|first_name|last_name|correo|email|telefono|dni` y busca `%nombre%` solo en cinco tablas de `abet`, así que una columna `acceso.usuario_autorizado.nombre` pasa sin que Q15 la vea. `controles_neon.sql` trae Q04 y no Q15.
- `crear_rol_app.sql` da a `abet_app` SELECT de tabla completa sobre `acceso.usuario_autorizado` y ningún INSERT ni UPDATE. `abet_lectura` y `powerbi_lectura` no tienen USAGE sobre `acceso`, y `abet_respaldo` lee todo `acceso`.
- `_cabecera()` de `abet_carga/r17.py` escribe B6, D8, D9, D11, I11 y B15. El rótulo «Profesor:» está en B10:C10 y la plantilla no trae ajuste de texto ni alto en la fila 10. `lineas_del_recuadro()` ya existe en `develop` con el ancho de B a I (208,6) como valor por defecto, y `alto_de_fila_final()` sirve solo para las filas 31 y 36.
- `tests/test_r17.py` afirma `D10` nulo en dos pruebas (BR-R17-02 y BR-R17-07), y la fila D10 de `plantillas/README.md` dice «Vacía, porque el R-17 no lleva el nombre del profesor».
- `abet_carga/avance.py` define el profesor de una sección con `u.activo AND u.rol = 'PROFESOR'` para el estado SIN_PROFESOR.
- Todo R-17 exige la declaración vigente completa (BR-R17-12), así que cada escenario que genera el libro trae la declaración en su Dado.
- Las semillas `db/datos/*.sql` insertan usuarios con `ON CONFLICT DO NOTHING` y sus comprobaciones finales fijan usuarios y asignaciones exactos. Los profesores de prueba son docente410, docente411, docente.varias y docente701 a docente703, y la 704 de 5643 no tiene profesor.
- La línea «Resumen.» del guion de la spec 006 tiene tres términos y la fijan sus escenarios. FR-002 de esa spec dice que el guion ignora el nombre del profesor sin leerlo.
- La última historia es US-94 (US-999 es una etiqueta de prueba de la spec 008), la última D es D-57, la última J es J-64, la última épica es EP-09, la última regla de `acceso` es BR-ACCESO-14 y la del R-17 es BR-R17-13.

## Faltantes que la spec cubre

- La forma de los nombres inventados, en letras y reconocible, para las semillas, las pruebas y develop de Neon.
- La cabida de D10:I10 con tres nombres o más, con su propia medida y sin tocar las filas 29 a 36.
- La lectura del nombre por `abet_respaldo` y su viaje al respaldo cifrado del Windows.
- El cambio fechado de FR-013 de la spec 006, que hoy dice que Q15 sigue encontrando solo el correo.
- El orden de construcción después de `fix/r17-recuadros-y-filas-de-pi`, que toca `r17.py`, `tests/test_r17.py` y `r17.spec.md`.

## Lista final del sprint

| Historia | Prioridad | Candidatas | Estimación |
| --- | --- | --- | --- |
| US-95 La base guarda el nombre del profesor en `acceso` | P1 | C-A01, C-C01, C-P01, C-A03 en parte y C-P02 en parte | 3 h |
| US-96 La programación docente trae el nombre del profesor | P1 | C-A02, C-C02 y C-P04 | 5 h |
| US-97 D10 del R-17 trae los profesores asignados | P1 | C-C03, C-P05 y C-P07 en parte | 4 h |
| US-98 Un profesor sin nombre o una sección sin profesor no rompen el R-17 | P1 | C-C04 y C-C05, con la consulta de AD-73 | 2 h |
| US-99 El nombre sale solo en D10 y git solo lleva nombres inventados | P2 | C-C06, C-A04 y C-P03 | 3 h |

La estimación suma unas 17 h más el cierre de las specs vivas.

## Decisiones que salen de la revisión

- D-12 sigue abierta con la Coordinación de Ambiental y la Oficina de Calidad, con el valor provisional nuevo.
- D-58 a la coordinación de cada carrera, de dónde salen los nombres reales.
- J-65 a J-71 a Jefferson, que la spec lista con su valor provisional.
