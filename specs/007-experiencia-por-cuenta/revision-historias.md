# Revisión por refutación de las historias de la experiencia por cuenta

**Fecha**: 2026-11-22
**Spec**: [spec.md](./spec.md)
**Entrada**: 18 candidatas escritas desde tres ángulos, el del profesor (C-P01 a C-P06), el de la coordinación (C-C01 a C-C06) y el transversal de la experiencia de uso (C-T01 a C-T06), cada una con su pantalla, sus rutas y tablas y su Gherkin en español. Salen del pedido de Jefferson del 2026-11-22 y de los correos de Claudia León y Mechelle Prado del 18 al 20-11-2026
**Salida**: 8 historias (US-59 a US-66 de la spec), en dos etapas. La etapa A (US-59 a US-63) cambia el código del Front, con un mínimo de US-60, US-59 y US-61 antes del registro del 30-11-2026. La etapa B (US-64 a US-66) agrega la ruta 17 y la pantalla P7 en la semana 16, si cabe
**Fuentes**: los informes de las tres lentes y del crítico de arquitectura que entrega el flujo de trabajo de la sesión, e `insumos_spec005_2026-11-21.md` (correos y estado del sistema), en la carpeta de notas de la sesión, fuera del repositorio

## Método

Cada candidata parte refutada y sobrevive solo si resiste tres lentes independientes, como en las specs 001 y 003 a 006. La lente de necesidad pregunta si la exige el pedido, un correo de la carrera o el calendario de las semanas 14 a 16, y si cambia algo que `develop` no hace ya. La lente de solapamiento y tamaño aplica INVEST (independiente, negociable, valiosa, estimable, pequeña y comprobable) contra las demás candidatas y contra US-01 a US-58, sobre todo contra las specs 005 y 006. La lente de verificabilidad lee el código real de `wt/back-007` y `wt/front-007` y busca cada texto, campo, ruta y prueba que la candidata nombra.

Los veredictos posibles son SOBREVIVE (S), CORREGIR (C), FUSIONAR (F), PARTIR (P), MOVER_A_DESPUES (M) y REFUTADA (R). La regla de las specs anteriores deja en la spec a una candidata que a lo sumo una lente marca R o M. Esta revisión suma un segundo filtro, porque el proyecto trabaja en una sola línea y la spec 007 no debe retrasar a la 006 ni al núcleo de la 005. El crítico de arquitectura fija el alcance por capacidad, y una candidata que pasa la regla pero que el crítico deja para después queda en «Fuera de alcance» con sus correcciones anotadas, para que no se pierdan. Tres candidatas están en ese caso (C-P04, C-T03 y C-T05), y la spec lo dice en sus Clarifications.

## Veredictos por candidata

| Candidata | Título | Necesidad | Solapamiento y tamaño | Verificabilidad | Destino |
| --- | --- | --- | --- | --- | --- |
| C-P01 | P2 dice el estado y el siguiente paso de cada sección | S, la sección cuya única carga está RECHAZADA dice «Sin carga» y no ofrece «Ver resultado», y absorbe C-T02 y la lista vacía de C-T03 | F, con C-T02 como base, porque las dos cambian la misma fila y C-P01 reescribe «Sin carga», que cita la spec 001 | F, el defecto se confirma en `estadoDeCarga()` y en el docstring de `app/rutas/secciones.py`, pero sus textos chocan con acceso.feature y varias_secciones.feature | US-59 (etapa A) |
| C-P02 | P3 dice antes de subir qué debe tener listo en Blackboard | S, el correo de Mechelle del 19-11 dice que la lectura depende del nombre de la actividad, y D-43 es urgente antes de la capacitación | F, con C-T04, la misma ayuda en otro lugar y con otra forma | F, los datos existen (`Seccion.pi` y `_ENCABEZADO_DE_PI`), y la línea del nombre del archivo es exacta solo en parte | US-60 (etapa A) |
| C-P03 | P4 de una carga rechazada dice qué corregir y pliega la constancia | C, «Qué corregir» cubre el tropiezo más probable de la semana 15, y el pliegue de la constancia no lo pide nadie | F, con C-P05 en la misma rama de `ResultadoCarga.tsx`, y el pliegue choca con el de C-T05 | C, `_rechazo_por_columnas()` informa solo el primer PI ausente, SECCION_NO_COINCIDE cubre también otra asignatura y `ResultadoCarga.test.tsx` (línea 87) espera la línea de conteos | US-61 (etapa A), sin el pliegue |
| C-P04 | P4 publicada con filas rechazadas dice qué pierde el R-17 y ofrece reemplazar | C, el texto sirve durante el registro y el botón es otro camino a «Reemplazar carga» de P5 | P, el texto va con C-T05 y el botón espera a US-52 de la spec 005 | S, todos los campos existen y BR-CARGA-15 confirma que la fila sale de todos los PI | Fuera de alcance, por capacidad (crítico) |
| C-P05 | Un reemplazo rechazado dice que la carga publicada sigue vigente | S, «No hay una carga publicada para esta sección» es falso en un reemplazo rechazado, y su prioridad sube a P1 | F, con C-P03 en la misma rama de P4 | S, el defecto se confirma en `ResultadoCarga.tsx` (línea 97) y en BR-CARGA-19 | US-62 (etapa A), en la versión mínima del crítico |
| C-P06 | P6 sin cargas publicadas dice una sola vez el siguiente paso | M, ningún correo ni el calendario lo piden | M, después de la primera entrega | S, la condición sale de `SeccionConLogros.estado`, aunque «Volver» ya lleva a P2 | Fuera de alcance |
| C-C01 | Avance del registro de la carrera en P7, con la etapa de cada sección | S, el registro de las semanas 15 y 16 pide saber cuántas secciones faltan y por qué, y la ruta 4 no distingue el rechazo ni la sección sin profesor | P, la ruta 17 y P7 no caben antes del 30-11 junto con la 005 y la 006, y van a un segundo corte | C, coherente con el código, pero el 422 no dice quién lo pide, no fija el orden de los errores y P7 y la ruta 17 ya figuran en AD-47 de la spec 005 | US-64 y US-65 (etapa B) |
| C-C02 | A quién recordar, con los correos de los profesores de las secciones que faltan | C, quedan el campo `profesores` y el correo en la fila, y el portapapeles no lo pide nadie | M, depende por completo de la ruta 17 | S, `acceso.usuario_autorizado` y `acceso.docente_seccion` los lee `abet_app`, y el ejemplo del portapapeles es exacto | US-66 (etapa B), con D-47 antes de construir |
| C-C03 | Cada cuenta entra a su página y lee rótulos de su rol | P, la entrada a P7 va con C-C01 y los textos vacíos pasan a después | F, con C-T01, que cambia el mismo título y el mismo botón | C, la entrada a P7 choca con la regla de US-52 de la spec 005 que lleva todo fragmento desconocido a P2 | US-63 (etapa A) para los rótulos y US-65 (etapa B) para la entrada a P7 |
| C-C04 | Lo que espera a la Coordinación, al comienzo de P7 | R, ningún correo lo pide, y los pendientes ya salen en la constancia y en las decisiones de las specs | M, su momento es la semana 14, antes de que la ruta 17 exista | C, `en_orden()` da otro orden y los efectos del ámbar y del 409 de la ruta 16 son de la spec 005 sin construir | Fuera de alcance. La línea de secciones sin plan queda en US-65 |
| C-C05 | Resumen y filtro de los indicadores debajo de la meta en P6 de la carrera | M, la reunión de mejora es después del registro | M, va con la reunión de mejora (N11) | C, el orden esperado no es el de `flatMap()` y `frontend.md` (sección 9.2) prohíbe el filtro en P6 | Fuera de alcance |
| C-C06 | El avance distingue la carga publicada sin declarar de la declarada | S, con US-49 de la spec 005 una carga publicada aún no tiene R-17 | M, depende de V1_12, de US-49 y de la ruta 17 | M, V1_12 no existe en el repositorio ni en Neon | Fuera de alcance, con V1_12 y US-49 |
| C-T01 | La coordinación llega a las secciones de la carrera con su avance | F, con C-C01, porque la ruta 4 cubre solo una parte de la necesidad | F, base del primer corte con C-C03 y la parte CON_RECHAZO de C-C01 | F, la ruta 4 no distingue CON_RECHAZO ni SIN_PROFESOR | Absorbida por C-C01 (crítico) |
| C-T02 | Cada sección del profesor dice qué le falta | F, con C-P01 | F, base de la historia de P2 del profesor | F, su forma conserva los textos de la spec 001 y une la línea al botón con aria-describedby | US-59 (etapa A) |
| C-T03 | Las pantallas vacías y los errores dicen qué hacer | R, con US-52 de la spec 005 recargar repite la lectura, y distinguir la red caída no cambia lo que hace el profesor | P, la lista vacía va a C-T02 y el reintento queda como historia propia | C, el mensaje del status 0 alcanza también a P1 y P3, y resultados.feature cita el texto del 502 | Fuera de alcance, por capacidad (crítico). La lista vacía de P2 queda en US-59 |
| C-T04 | P3 explica cómo preparar el export de la sección elegida | F, con C-P02, y los pasos de descarga esperan un texto sin dueño | F, base de la ayuda de P3 | F, su escenario del Back respondería 422, porque no fija la hoja ni el nombre del archivo | US-60 (etapa A), sin los pasos de descarga |
| C-T05 | Los estados y la constancia se leen en el lenguaje del profesor | M, las etiquetas se entienden solas y la capacitación explica los PI y los SO | F, recibe el pliegue de C-P03 y el texto de filas rechazadas de C-P04 | C, EN_CURSO no lo ve otro lector, y el pliegue choca con el de C-P03 | Fuera de alcance, por capacidad (crítico) |
| C-T06 | La aplicación se usa con teclado, lector de pantalla y celular | M, el pedido no habla de accesibilidad y subir el export es tarea de computador | M, axe-core pide una dependencia nueva con la espera de 14 días | C, la cabecera tiene cuatro botones y el correo, y `playwright.config.ts` sirve hoy al humo contra la API real | El menú con aria-current entra en US-63 (crítico). El resto queda fuera de alcance |

Las tres lentes coinciden en lo esencial de la etapa A. Discrepan en C-C01, que la necesidad sostiene y el tamaño parte, y el crítico resuelve con P7 y la ruta 17 en una etapa B propia. Discrepan también en C-C02, que la necesidad corrige y el tamaño mueve, y el crítico la deja en la etapa B con la decisión de la Coordinación antes de construir.

## Correcciones que la spec adopta

| Corrección | La propone | Dónde queda |
| --- | --- | --- |
| Conservar «Sin carga», «Publicada, N de M filas aceptadas» y «La carrera aún no registra el plan de medición de esta sección», y poner lo que falta en una línea aparte unida por aria-describedby al botón, también al desactivado | Las tres lentes y el crítico | US-59, escenarios 1 y 2 |
| La combinación de las rutas 4 y 8 no tiene precedente en P5. `Cargas.tsx` pide las dos rutas y filtra las cargas por sección, pero no busca la carga RECHAZADA más reciente | Crítico | US-59 y J-45, sin la frase «como ya hace P5» |
| Un solo texto para la lista vacía del profesor, con a quién acudir, y un solo número de decisión | Tamaño y verificabilidad | US-59, escenario 5, y D-46 |
| La línea de una carga PUBLICADA no promete el R-17 inmediato, para seguir siendo cierta con US-49 de la spec 005 | Tamaño | US-59, escenario 1 |
| Un solo lugar para la ayuda de P3, visible antes del campo de archivo, con la columna Username, el nivel de 1 a 4 con el puntaje máximo que solo avisa y la hoja o el nombre del archivo que indican la sección | Las tres lentes y el crítico | US-60, escenario 1 |
| El escenario del Back de C-T04 no sube un export, que respondería 422 sin la hoja ni el nombre de Blackboard, y comprueba en cambio que el lector reconoce el nombre que propone P3 y no el que lleva guiones | Verificabilidad y crítico | US-60, escenario 5 |
| El consejo de PI_DEL_PLAN_AUSENTE pide revisar todas las columnas del plan, porque `_rechazo_por_columnas()` informa solo el primer PI ausente, y cubre la columna que existe con otro nombre | Necesidad y verificabilidad | US-61, escenario 1 |
| El consejo de SECCION_NO_COINCIDE nombra la asignatura y la sección de la constancia, porque el motivo cubre también otra asignatura | Verificabilidad | US-61, escenario 1 |
| La línea «0 filas leídas, 0 aceptadas y 0 rechazadas» y la constancia completa no cambian, así que `ResultadoCarga.test.tsx` (línea 87) sigue igual | Necesidad y verificabilidad | US-61, escenario 1, y Fuera de alcance |
| Una prueba de Vitest recorre los siete motivos RECHAZA_CARGA del contrato y exige un consejo por motivo | Crítico | FR-005 |
| «No hay una carga publicada para esta sección» se cambia por «Esta carga no tiene R-17.», siempre cierto, sin pedir la ruta 4 desde P4 | Crítico | US-62 |
| La frase nueva de P3 va en un párrafo propio, porque `SubirExport.test.tsx` (línea 219) y `App.test.tsx` (línea 124) buscan el texto exacto actual | Verificabilidad | US-62, escenario 4 |
| El nav con aria-label y aria-current entra con los rótulos, y P3 y P4 no marcan ningún botón, porque «Mis secciones» no es la pantalla actual mientras se ve P3 | Crítico y verificabilidad | US-63, escenario 4 |
| El 422 de la ruta 17 lo pide la coordinación, y la ruta responde en el orden 401, 403 y 422 | Verificabilidad | US-64, escenario 3, y FR-008 |
| P7 y la ruta 17 toman los números que AD-47 de la spec 005 nombra para una idea fuera de alcance, que recibe otro número cuando entre | Verificabilidad y crítico | J-47 |
| La llegada a P7 enmienda la regla de US-52 de la spec 005, de modo que el fragmento vacío o desconocido lleve al coordinador a P7 | Verificabilidad y crítico | J-46 y FR-011 |
| La regla de `frontend.md` (sección 9.2) que prohíbe correos de profesores vale para P6, y P7 lleva su propia regla escrita | Verificabilidad y crítico | US-66 y FR-013 |
| La etapa PUBLICADA se rotula «Publicada» y el resumen no la presenta como sección terminada, porque con US-49 de la spec 005 una carga publicada aún no tiene R-17 | Necesidad | US-65, escenario 1 |

## Choques de numeración y renumeración

Las candidatas usan J-43, J-44 y D-46 con tres significados cada una, y J-45 con uno. La spec 006 termina en D-45 y en J-42, así que el punto de partida es correcto. La spec asigna un número por decisión, en el orden en que aparecen las historias.

| Número de la spec | Decisión | Números de las candidatas |
| --- | --- | --- |
| D-46 | Texto de contacto del profesor sin secciones | D-46 de C-P01 |
| D-47 | Si la coordinación ve en P7 el correo del profesor de cada sección que falta | D-46 de C-C02 |
| J-43 | La tabla «Qué corregir» por motivo vive en el Front | J-43 de C-P03 |
| J-44 | Las líneas de «Antes de subir» viven en una constante del Front | J-44 de C-P02 |
| J-45 | P2 del profesor combina las rutas 4 y 8 en el Front | J-45 de C-P01 y J-43 de C-T01 |
| J-46 | Página de llegada por rol | J-44 de C-C03 |
| J-47 | Forma de la ruta 17 y números de P7 y de la ruta 17 | Ninguno |
| J-48 | La etapa se deriva en cada lectura con una precedencia del Back | J-43 de C-C01 |

D-46 de C-T04 (los pasos de descarga de Blackboard) y J-44 de C-T06 (axe-core) no reciben número, porque sus partes quedan fuera de alcance.

## Veredicto del crítico de arquitectura

| Decisión | Veredicto | Razón | Alternativa |
| --- | --- | --- | --- |
| Pantalla de llegada por rol (C-C03). El COORDINADOR entra a P7 y el PROFESOR sigue entrando a P2 | SE_SOSTIENE | `App.tsx` arranca siempre en P2 y el botón dice «Mis secciones» también al coordinador, mientras `rotuloDeLogros()` ya cambia un rótulo según el rol. La navegación por fragmento de US-52 no está construida | Mientras P7 no exista, el coordinador llega a P2 con los rótulos de la carrera, y la llegada a P7 entra en el mismo commit que P7, con `pantallaDeLlegada(usuario)` que US-52 reutiliza |
| P7 nueva (C-C01) frente a la variante de P2 con resumen y filtro (C-T01) | SE_SOSTIENE | La ruta 4 da SIN_CARGA también con todas las cargas RECHAZADA y no trae al profesor, y meter esos datos en la ruta 4 mezclaría el contrato del profesor con el de la carrera | Entra P7 con la ruta 17 y C-T01 queda absorbida por C-C01 |
| Ruta 17 `GET /api/avance` solo para COORDINADOR, con etapa, conteo, correos (C-C02) y bloque de reglas (C-C04) | CAMBIAR | El bloque de reglas describe efectos de la spec 005 que no existen, y la ruta debe entrar en la prueba de rutas registradas | Primer corte con secciones, etapa, `carga_id`, `profesores` y conteo. El bloque de reglas y la división POR_DECLARAR y DECLARADA llegan después como campos aditivos |
| Estado derivado en la lectura frente a un estado guardado | SE_SOSTIENE | Un estado guardado obliga a mantenerlo en la carga, el reemplazo, la asignación y la baja, y una carrera tiene decenas de secciones | La spec fija que la etapa no se guarda y que su precedencia vive en una sola consulta del Back (J-48) |
| Quién decide la última carga rechazada, el Back en la ruta 17 y el Front con las rutas 4 y 8 en P2 (J-45) | DUDOSA | La misma regla queda escrita dos veces y puede divergir, y el precedente de P5 que cita C-P01 no existe | Antes de la semana 15, la combinación en el Front con una sola petición a la ruta 8 y tolerancia a su falla. Con la ruta 17, la consulta pasa a una función del Back y la ruta 4 suma un campo aditivo `ultima_rechazada_id` |
| Ayudas solo en el Front, «Antes de subir» (C-P02 y C-T04) y «Qué corregir» (C-P03) | SE_SOSTIENE | Los nombres salen de `Seccion.pi` y del lector, y los motivos están cerrados en la sección 6 del contrato | Una sola ayuda de P3 antes del campo de archivo, y una prueba de Vitest que recorre los motivos RECHAZA_CARGA del contrato |
| Cambios a P2 del profesor (C-P01, C-T02 y la lista vacía de C-T03) | CAMBIAR | Las tres cambian la misma fila con redacciones distintas, y C-P01 reescribe un literal de la spec 001 | Una sola historia con la línea aparte de C-T02, el caso rechazado y la falla de la ruta 8 de C-P01 y un solo texto de lista vacía |
| Cambios a P4 (C-P03, C-P04, C-P05 y el pliegue de C-P03 y C-T05) | CAMBIAR | La spec 005 reescribe `ResultadoCarga.tsx` con US-45 a US-49, y C-P05 pide la ruta 4 desde P4 | Antes de la semana 15, solo «Qué corregir» en la rama RECHAZADA y el texto siempre cierto de C-P05 con la frase de P3. El resto va después de que la spec 005 cierre P4 |
| Cambios a P5 y P6 (C-T05 en P5, C-P06 y C-C05 en P6) | DUDOSA | Ninguno bloquea el registro, y C-C05 cambia J-28 de la spec 004 y la regla de `frontend.md` que prohíbe el filtro | Los tres van después de la semana 16, y C-C05 como cambio explícito de J-28 |
| Correos de los profesores en P7, con copia al portapapeles (C-C02) | SE_SOSTIENE | El coordinador ya ve `subida_por` en P5, el correo sale solo a la cuenta COORDINADOR y la aplicación no envía correos ni guarda la lista | En el mismo corte que la ruta 17, con la decisión de la Coordinación antes de construir y la regla de P7 escrita en `frontend.md` |
| Pendientes de reglas y plan al comienzo de P7 (C-C04) | DUDOSA | Se resuelven una vez y sus textos de efecto describen pantallas de la spec 005 que no existen | Solo la línea de secciones sin plan en P7, y el bloque de reglas después de US-45 a US-49 |
| Numeración de decisiones de las candidatas | CAMBIAR | J-43, J-44 y D-46 tienen tres usos cada una | Renumeración de la tabla anterior, una decisión por número |
| Reintento y mensaje de falta de conexión (C-T03) | DUDOSA | Cambia `MSG_NO_RESPONDE`, sus pruebas y cuatro pantallas, y el texto del 502 lo cita la spec 004 | Después de la semana 15, salvo que la capacitación muestre fallas de red reales |
| Accesibilidad, nav con aria-current y prueba a 375 px con axe-core (C-T06) | SE_SOSTIENE | La cabecera no es un nav ni marca la pantalla actual, y axe-core suma una dependencia con la espera de 14 días | El nav con aria-current entra con los rótulos de US-63, y la tabla desplazable, la prueba de ancho y axe-core van después de la semana 16 |

El crítico fija además el orden de prioridad de la línea de trabajo, que es la spec 006, el núcleo de la 005, la etapa 007-A y la etapa 007-B. La revisión de la spec del 2026-11-22 ajusta ese orden a la spec 006, la etapa 007-A, el núcleo de la 005 y la etapa 007-B, porque el núcleo de la spec 005 no tiene código y no deja llegar la etapa A antes del registro del 30-11. La etapa A fija un mínimo de US-60, US-59 y US-61 y deja US-62 y US-63 como extras si caben, y la etapa B pasa a la semana 16, si cabe (FR-016 de la spec 007).

## Hechos del código que corrigen supuestos de las candidatas

- `src/pantallas/Cargas.tsx` pide las rutas 4 y 8 con `Promise.all` y filtra las cargas por `seccion.seccion_id`, pero no busca la carga RECHAZADA más reciente de una sección en SIN_CARGA.
- La ruta 8 sin `seccion_id` lista las cargas del periodo vigente de la más reciente a la más antigua (`constancia.resumenes`, `ORDER BY c.iniciada_en DESC, c.carga_id DESC`), el mismo periodo que usa `listarSecciones()` sin argumento.
- La cabecera de `src/App.tsx` tiene cuatro botones («Mis secciones», «Cargas», el enlace a P6 y «Salir») y el correo, sin nav ni aria-current.
- `abet_carga/lector.py` clasifica «ABET SO6.10 [Total Pts: 4 Score] |9000610» como columna del PI 6.10 y «ABET-SO5-PI5.1 [Total Pts: 4 Score] |9000051» como una columna que no es de un PI. El correo de Mechelle del 19-11 dice que el nombre de hoy es «ABET-SO-PI», una forma con guiones que el lector no acepta.
- «No hay una carga publicada para esta sección» aparece en `ResultadoCarga.tsx` (línea 97) para toda carga que no está PUBLICADA ni REEMPLAZADA con sucesora, y lo buscan `ResultadoCarga.test.tsx` (líneas 91, 178 y 184) y `App.test.tsx` (línea 217). Ningún `.feature` de las specs 001 a 006 lo cita.
- `app/main.py` ya pone `Cache-Control: no-store` en toda respuesta de `/api`, y `crear_rol_app.sql` ya deja leer a `abet_app` las tablas que usa la ruta 17.
- `db/plataforma/neon/secciones_sin_docente.sql` cuenta solo las secciones con plan de medición, la misma precedencia de SIN_PLAN sobre SIN_PROFESOR que fija J-48.

## Decisiones que salen de la revisión

D-46 y D-47 de la carrera, y J-43 a J-48 de Jefferson, con el valor que propone la spec (`spec.md`, «Decisiones abiertas»). D-47 se decide antes de construir US-66, y si la Coordinación responde que no, US-66 sale sin tocar US-64 ni US-65.
