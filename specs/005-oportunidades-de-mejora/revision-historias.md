# Revisión por refutación de las historias de las oportunidades de mejora en la carga

**Fecha**: 2026-11-18
**Spec**: [spec.md](./spec.md)
**Entrada**: 15 historias candidatas (C-01 a C-15), escritas desde el pedido literal de Jefferson del 2026-11-18. Ese pedido incluye el semáforo de la sección en P4, la declaración de causas y acciones con su borrador, el R-17 solo con esa declaración, la descripción del instrumento desde la base y el botón atrás del navegador
**Salida**: 10 historias (US-45 a US-54 de la spec), que absorben C-02, C-10, C-15, el punto (a) de C-14 y la parte A de C-09. C-08 y C-12 pasan a después, C-14 (b) pasa a después, y la parte B de C-09 queda sin escenario propio
**Fuentes**: `ABET_SIS_MED/notas_spec005/contexto_y_candidatas.md`, `auditoria_necesidad.md`, `auditoria_solapamiento.md`, `auditoria_verificabilidad.md`, `critica_arquitectura.md` y `sintesis.md`, en la carpeta de notas de la sesión del plan (fuera del repositorio)
**Cambio del 2026-11-21**: una segunda revisión, con 21 candidatas que salen de los correos de la carrera sobre las oportunidades de mejora y las buenas prácticas, está al final de este archivo, en «Revisión del cambio del 2026-11-21». Lo que sigue hasta esa sección es la revisión del 2026-11-18 sin cambios

## Método

Cada candidata parte refutada y sobrevive solo si resiste tres lentes independientes, como en las specs 001, 003 y 004. La lente de necesidad pregunta si la exige el pedido literal de Jefferson, el objetivo del sprint o un requisito de la carrera, y si cambia algo que `develop` no fija ya con prueba. La lente de solapamiento y tamaño aplica INVEST (independiente, negociable, valiosa, estimable, pequeña y comprobable) contra las demás candidatas y contra US-01 a US-44. La lente de verificabilidad coteja cada escenario con el código de los worktrees (`app/permisos.py`, `abet_carga/r17.py`, `abet_carga/carga.py`, `tests/aceptacion/pasos/conftest.py`, las migraciones V1_01 a V1_10 y la plantilla del R-17) y recalcula cada cifra desde los niveles de `scripts/generar_exports_inventados.py`.

Las lentes de necesidad y de solapamiento corren con Sonnet, y la de verificabilidad también con Sonnet. Después, el crítico de arquitectura, con el modelo de la sesión, ataca las decisiones técnicas AD-01 a AD-20 de las candidatas y agrega AD-21 a AD-30, que el código vuelve necesarias. Ningún auditor escribe en los worktrees, se conecta a una base ni corre pruebas.

Los veredictos posibles son SOBREVIVE (S), CORREGIR (C), FUSIONAR (F), PARTIR (P), MOVER_A_DESPUES (M) y REFUTADA (R). Una candidata queda en el sprint si al menos dos lentes no la sacan, es decir, si a lo sumo una la marca REFUTADA o MOVER_A_DESPUES, y las fusiones y las particiones se aplican. Este archivo registra los veredictos y su destino, y el razonamiento completo con su evidencia está en cada informe.

## Veredictos por candidata

| Candidata | Título de la candidata | Necesidad | Solapamiento y tamaño | Verificabilidad | Historia final |
| --- | --- | --- | --- | --- | --- |
| C-01 | Ver el semáforo de mi sección al terminar la carga | S, absorbe C-02 y C-15 | P, en los datos de la ruta 13 y en la tabla de P4 | P y C, mezcla pytest, Vitest y un 409 con texto prestado, y faltan la frontera de 75,0 y el caso sin corte | US-45 (datos) y US-46 (pantalla) |
| C-02 | El semáforo dice lo mismo que el R-17 | F con C-01 | F con la parte de datos de C-01 | C, solo prueba la 410 en rojo y deja sin ejercitar VERDE, AMBAR y SIN_DATO | Escenario 8 de US-45 |
| C-03 | Declarar las causas y las acciones en P4 | C, absorbe C-10, traza solo al pedido 3 | C, faltan los escenarios de pantalla, la edición posterior (D-37) y la sección en la meta (D-36) | C, faltan el orden de las validaciones y la vuelta a borrador | US-47, con C-10 |
| C-04 | El borrador de la declaración no se pierde | S | C, mueve la regla del navegador a una regla transversal y suma la falla del guardado y las dos pestañas | C, un escenario se contradice y faltan el fallo, la salida del campo, el 401 y las dos pestañas | US-48 |
| C-05 | El R-17 solo con la declaración completa | C, absorbe el punto (a) de C-14 | C, toca cinco superficies y rompe escenarios aprobados de US-15 y US-17 | C y F, rompe 26 llamadas de prueba y el comando, y su parte de P2 y P5 se fusiona con C-14 | US-49 |
| C-06 | El R-17 lleva las causas y las acciones desde la base | C, falta el escenario de legibilidad con 2000 caracteres | C, quita el escenario de «=SUMA» que ya cubre `_escribir` y suma el diseño de la celda | C, no prueba el ajuste ni el alto de fila, y las filas 29 a 31 estiran otra tabla | US-50 |
| C-07 | La descripción del instrumento sale de la base | C, sube a P1 y mueve la consulta Q15 a después | C, separa su migración de la de C-03 y suma la carga de datos desde el Windows | C, un escenario no distingue una descripción de otra y Q15 contradice el contrato de los controles | US-51 |
| C-08 | La descripción del SO en el título del bloque I | R, Jefferson no la pidió | M, sin pedido ni requisito que la sostenga | M, nadie la pidió y el texto del escenario no existe | Después, con una pregunta a Jefferson |
| C-09 | El botón atrás vuelve a la pantalla anterior | C, quita el escenario de recarga, que el pedido no nombra | P, «atrás» por un lado y «recargar conserva la pantalla» por otro | P y C, mezcla jsdom y Playwright y faltan `reemplaza` en la dirección y el enlace profundo ajeno | US-52, con la parte A |
| C-10 | El coordinador lee la declaración | F con C-03 | C, tiene reglas propias (solo lo declarado y nunca editar) | C, falta decir qué ve el coordinador en pantalla | Escenario 8 de US-47 |
| C-11 | La declaración no lleva datos de estudiantes | C, baja a P2 y quita el CHECK de la base | C, reescribe la historia a códigos y correos sin prometer cerrar la vía | C, faltan la segunda defensa en la base, el choque con el autoguardado y la definición de código | US-53 |
| C-12 | Quién declaró y cuándo, en la constancia | M, ni el pedido ni un N# lo exigen | M, cambia BR-R17-07, BR-R17-09 y BR-R17-10 para un dato que casi siempre coincide con `subida_por` | R, rompe BR-R17-10 y BR-R17-07 tal como están escritas | Después |
| C-13 | El reemplazo trae el texto anterior como borrador | M, el pedido no menciona el reemplazo | C, falta decir cuándo se copia y qué pasa si el reemplazo falla | C, el mecanismo de copia no está definido | US-54 |
| C-14 | P2 y P5 dicen qué carga espera la declaración | P, (a) a C-05 y (b) a después | M, cambia el contrato de dos rutas aprobadas sin pedido | F con C-05 | (a) en US-49 y (b) después |
| C-15 | El semáforo explica su regla | F con C-01 | F con la parte de pantalla de C-01 | F con C-01, y sus cifras salen de la ruta 13 | Escenario 2 de US-46 |

Cuentas por lente, con el primer veredicto de cada fila.

| Lente | S | C | F | P | M | R |
| --- | --- | --- | --- | --- | --- | --- |
| Necesidad | 2 | 6 | 3 | 1 | 2 | 1 |
| Solapamiento y tamaño | 0 | 8 | 2 | 2 | 3 | 0 |
| Verificabilidad | 0 | 9 | 2 | 2 | 1 | 1 |

Tres desacuerdos se resuelven así. C-13 queda como historia propia en P2, porque solo la lente de necesidad la mueve a después, y el crítico fija la herencia al leer (AD-17 y AD-27). C-14 se parte, porque la necesidad lleva su punto (a) a C-05 y la verificabilidad la fusiona con C-05, así que el enlace al R-17 con declaración entra en US-49 y la marca «Declaración pendiente» sale del sprint. C-12 sale, porque dos lentes la mueven a después y la tercera la refuta tal como está.

## Historias faltantes

| Faltante | La proponen | Historia o requisito final |
| --- | --- | --- |
| Corregir una declaración ya hecha (D-37) | Necesidad (F-1), solapamiento (F-4) | US-47, escenario 7, y D-37 |
| Descripción provisional del instrumento en el piloto | Necesidad (F-2) | US-51 y el guion de datos de J-31 |
| Saber si el semáforo es provisional | Solapamiento (F-1), verificabilidad (faltante 3) | US-46, escenario 3 |
| P4 y P6 no se contradicen | Solapamiento (F-2) | US-45, escenario 8, y FR-002 |
| Las respuestas nuevas no exponen a estudiantes ni a otros usuarios | Solapamiento (F-3) | US-53 y US-47 |
| Aplicar V1_11 en Neon sin romper el piloto | Solapamiento (F-5), crítico (AD-15 y AD-28) | T023 y T024 de `tasks.md`, y J-37 |
| El humo de punta a punta incluye la declaración | Solapamiento (F-6), crítico (AD-28) | FR-016, T046 y T062 |
| La frontera de 75,0 es ámbar, y el conjunto con NIVEL_ESPERADO o META_LOGRO sin definir da SIN_DATO sin un 500 | Verificabilidad (faltantes 1 y 2) | US-45, escenarios 4 y 7 |
| Una carga rechazada o reemplazada no pide el semáforo, y la ruta de una carga inexistente da el 403 único | Verificabilidad (faltantes 4 y 5) | US-45, escenarios 9 y 10, y US-46, escenario 5 |
| El comando `python -m abet_carga r17` sin declaración y el orden con el 409 de «no publicada» | Verificabilidad (faltante 10) | US-49, escenarios 4 y 5 |
| El texto de P4 para el coordinador, que no puede declarar | Verificabilidad (faltante 11) | US-49, pantalla, y US-47, escenario 8 |
| Un texto de 2000 caracteres con ajuste y alto de fila | Verificabilidad (faltante 12), crítico (AD-10) | US-50, escenario 2 |
| Los textos del R-17 que se vuelven falsos con una declaración («ninguna celda del libro empieza por "="» y «los recuadros … están vacíos») | Verificabilidad (faltante 13), crítico (AD-26) | US-50 y J-35 |
| El enlace profundo a una carga ajena, `reemplaza` en la dirección y la limpieza del fragmento al salir | Verificabilidad (faltante 15) | US-52, escenarios 3 a 5 |
| El 422 durante el autoguardado y el CHECK de la base | Verificabilidad (faltante 16) | US-53, escenarios 4 y 5 |
| Reemplazo sin declaración previa, con solo un borrador, con el mismo archivo y por el coordinador | Verificabilidad (faltante 17) | US-54, escenarios 2 a 5 |
| Infraestructura de prueba (expresión de migraciones, reglas de copia, ayudante `declarar()` y reinicio del fragmento) | Verificabilidad (faltante 19) | FR-017 y T037 |

## Defectos transversales de verificabilidad

| Defecto | Resolución en la spec |
| --- | --- |
| Escenarios que mezclan lo que prueba pytest con lo que prueba Vitest, con «(Vitest)» en el título | Cada escenario de pantalla va aparte con `@delegado_a_vitest` y sin «(Vitest)» en el título |
| Las copias «en las filas 2 y 6» y «con la columna X.Y vacía en sus N filas» no existen en `REGLAS_DE_COPIA` | FR-017 las suma, y la segunda la crea T012 de la spec 004 |
| Los pasos de fondo solo admiten V1_09 y V1_10 (`conftest.py:756`) | FR-017 amplía la expresión a V1_11 y V1_12 |
| El Front lanza «Ruta no simulada» ante una ruta que no simula | Todo test de P4 simula las rutas 13 y 14, y el costo queda en T040 a T042 |
| 24 llamadas a `generar(` en `tests/test_r17.py`, 2 en `tests/test_demo_punta_a_punta.py` y `r17_constancia.feature` generan un R-17 sin declaración | El ayudante `declarar()` de `tests/cargas_de_prueba.py` y T037 |
| Los anchos de B a I del contexto no coinciden con la plantilla, que suma 208,6 unidades | US-50 usa 208,6 y el cálculo conservador de `r17.py` |
| Las filas 29 a 31 se comparten con la tabla K28:Q31 | US-50 crece solo las filas 31 y 36, y conserva K31:Q31 |

## Veredicto del crítico de arquitectura

| N.º | Decisión | Veredicto | Lo que adopta la spec |
| --- | --- | --- | --- |
| AD-01 | Ruta 13 `GET /api/cargas/{carga_id}/indicadores` para P4 | SE_SOSTIENE | US-45. Cada indicador sale de la función que arma los de la ruta 12, y ADR-008 admite la ruta por carga solo para P4 |
| AD-02 | El Back calcula `semaforo` y el Front lo pinta | SE_SOSTIENE | J-29. El Front solo traduce el valor a texto y color |
| AD-03 | Banda ámbar desde la meta menos 5 puntos | CAMBIAR | La banda sale de CORTE_ROJO, que la base ya modela, y D-35 es el valor que fija la Coordinación |
| AD-04 | Tabla nueva `abet.carga_mejora`, una fila por carga | CAMBIAR | J-30. Dos tablas, `abet.mejora_borrador` con versión y `abet.mejora_declaracion` de solo INSERT |
| AD-05 | Borrador en la base y guardado cada 1,5 s | CAMBIAR | US-48. Espera de 2,5 s con máximo de 15 s, guardado al salir del campo y en `pagehide` con `keepalive`, y un solo PUT en vuelo |
| AD-06 | Un solo PUT con `declarar` | CAMBIAR | Rutas 15 y 16 separadas, y la declaración recibe la versión del borrador |
| AD-07 | La regla del R-17 vive en `r17.generar()` | SE_SOSTIENE | US-49. Lectura en una transacción `READ ONLY` con `REPEATABLE READ` y `DeclaracionPendiente` capturada por el comando |
| AD-08 | El 409 sin declaración vale también para el coordinador | DUDOSA | J-33, con la salida de reasignar la sección en `acceso.docente_seccion` |
| AD-09 | Escribe solo el profesor asignado | SE_SOSTIENE | Una función propia `puede_declarar()` con prueba propia |
| AD-10 | Tope de 2000 caracteres, ajuste de texto y alto de fila calculado | DUDOSA | US-47 y US-50. Normalización a NFC, conteo en puntos de código y alto determinista de las filas 31 y 36 |
| AD-11 | Rechazo de códigos y correos en la ruta y CHECK en la base | SE_SOSTIENE | US-53. El mismo patrón ASCII en la ruta y en la base, y la violación sale como 422 |
| AD-12 | `abet.plan_medicion.descripcion_instrumento` | SE_SOSTIENE | US-51 y J-31 |
| AD-13 | Navegación con el fragmento, `pushState` y `popstate` | SE_SOSTIENE | US-52 y J-34, sin tocar `vercel.json` |
| AD-14 | P4 reemplaza la entrada de P3 con `replaceState` | SE_SOSTIENE | US-52, solo si la pantalla visible sigue siendo esa subida, y «Subir otro archivo» en una carga rechazada |
| AD-15 | Una sola migración V1_11 y los permisos en `crear_rol_app.sql` | SE_SOSTIENE | V1_11 y V1_12 separadas, con los permisos y los datos en pasos aparte y en orden (T020 a T025) |
| AD-16 | La 005 se implementa después de la fase de la 004 y cambia FR-016 | CAMBIAR | La implementación sale de `develop` después de fusionar la spec 004, y J-35 cubre FR-016, el invariante 8 de ADR-008 y `frontend.md` |
| AD-17 | La declaración es de la carga y el reemplazo la copia como borrador | CAMBIAR | US-54. La herencia ocurre al leer, sin escribir en la transacción de la subida |
| AD-18 | El coordinador ve solo lo declarado | SE_SOSTIENE | US-47, escenario 8, y la ruta 14 sin el texto del borrador |
| AD-19 | Dos pestañas, gana la última escritura | CAMBIAR | US-48. Versión en el borrador y 409 con el texto guardado |
| AD-20 | Descripción inventada en `periodo_2026_2_inventado.sql` hasta D-34 | CAMBIAR | US-51. Guion de datos aparte y repetible, que Jefferson corre desde el Windows |
| AD-21 | Colores de E24:F26 del R-17 | Decisión agregada por el crítico | Fuera de alcance, porque es la plantilla oficial (D-08) |
| AD-22 | Un 401 mientras el profesor escribe | Decisión agregada por el crítico | US-48, escenario 6, y FR-007 |
| AD-23 | Orden de las respuestas y lectura del cuerpo en las rutas nuevas | Decisión agregada por el crítico | US-47 y FR-005. Orden 401, 403, 422 y 409, con el cuerpo leído después del alcance |
| AD-24 | Enlaces del R-17 que pueden recibir 409 | Decisión agregada por el crítico | US-49 y J-32. P4 es el único lugar que ofrece el R-17 |
| AD-25 | Constancia y declaración | Decisión agregada por el crítico | `constancia.armar()` no cambia (BR-R17-10), y la hoja «Constancia» queda fuera de alcance (C-12) |
| AD-26 | ADR y reglas que la 005 cambia sin nombrarlos | Decisión agregada por el crítico | J-35. ADR-009 enmienda ADR-005 y ADR-008, y BR-R17-04 pasa a «desde la base» |
| AD-27 | Reemplazo mientras el profesor escribe | Decisión agregada por el crítico | US-47, escenario 6, y US-54, escenario 6 |
| AD-28 | Activación y cargas publicadas antes de la migración | Decisión agregada por el crítico | J-37. Toda carga publicada antes de V1_12 queda en 409 hasta declarar, y el Front se despliega primero |
| AD-29 | Consultas de control | Decisión agregada por el crítico | US-51 y US-53. La consulta de los PI sin descripción es informativa, y Q16 busca códigos y correos |
| AD-30 | Aceptación del riesgo de nombres en el texto libre | Decisión agregada por el crítico | J-36 y US-53. La regla se cumple por aviso y no por construcción |

El crítico anota además que los anchos de B a I que da el contexto no coinciden con la plantilla, y que el cálculo del alto de fila debe usar 208,6 unidades. También advierte que la 005 rompe pruebas de la spec 004 (el R-17 pasa a dar 409 y P4 muestra porcentajes), que actualiza en su propio PR.

## Decisiones que salen de la revisión

- De la carrera, D-35 (valor de CORTE_ROJO), D-36 (declaración de una sección que alcanza la meta) y D-37 (corrección de la declaración después de descargar), con su valor provisional en la spec. D-34 de la spec 004 sigue abierta con su dueño.
- De Jefferson, J-29 a J-37, con el valor que propone la spec.

## Revisión del cambio del 2026-11-21

**Fecha**: 2026-11-21
**Entrada**: 21 candidatas, escritas desde tres ángulos por tres proponentes. C-P01 a C-P07 miran al profesor, C-C01 a C-C07 a la coordinación y C-B01 a C-B07 a la base. Las tres parten de tres correos de la carrera. Claudia León, secretaria académica de Ingeniería Ambiental, pide que el profesor registre en la plataforma las oportunidades de mejora (OM) y las buenas prácticas (BP), que el estado de cada acción nazca como «Propuesta» y que el responsable y el plazo queden para la coordinación y quizás para el R-18. Pide además «incluso cuando se supera el valor de referencia, deberíamos hacer el análisis de causas hasta llegar a la BP». Mechelle Prado resume la reunión del 18-11, en la que el docente completa las OM y las BP como paso previo para habilitar la descarga, y pide un nombre estándar para la actividad de Blackboard. Claudia recuerda también que la capacitación de los profesores es en la semana 14 y su registro en la semana 15, o en la 16 como máximo
**Salida**: ninguna historia nueva en la spec 005. Cambian en su lugar US-45 a US-50 y US-52 a US-54 donde corresponde, y US-51 queda igual. C-C01 pasa a la spec 006 nueva (`specs/006-programacion-docente/`), desde US-55. Diez candidatas quedan fuera de alcance con su destino, y las otras diez se fusionan en las historias que cambian
**Alcance**: el que Jefferson aprueba en el chat el 2026-11-21 («Sí, escríbelo»), que toma el alcance que recomienda el crítico de arquitectura con los cambios que registra la columna «Cómo queda». El cambio queda en borrador hasta que Jefferson lo reapruebe (T008 de `tasks.md`)
**Fuentes**: `historias_spec005_om_bp_2026-11-21.json` (candidatas, veredictos de las tres lentes y crítico de arquitectura) e `insumos_spec005_2026-11-21.md` (transcripción de los correos, estructura de la propuesta de R-17 de Mechelle sin datos personales y estado del sistema), en la carpeta de notas de la sesión del plan (fuera del repositorio). Ningún código, nombre ni curso de la propuesta de Mechelle entra a este archivo

### Método

El método es el de la revisión del 2026-11-18. Cada candidata parte refutada, pasa por las lentes de necesidad, de solapamiento y tamaño y de verificabilidad, y queda en el sprint si a lo sumo una lente la marca REFUTADA o MOVER_A_DESPUES. Los tres proponentes y los cuatro auditores corren con Opus 5.5. La lente de verificabilidad coteja cada escenario con `develop` del Back (migraciones V1_01 a V1_11, `R__vista_r17_por_pi.sql`, `abet_carga/r17.py`, `resultados.py` y `lector.py`, `app/permisos.py`, `db/pruebas/pruebas.sql`, `crear_rol_app.sql`, `controles_neon.sql`, `plantillas/README.md` y `tests/aceptacion/pasos/conftest.py`) y con el contrato y `frontend.md` del Front. Ningún auditor escribe en los worktrees, abre una base, corre pruebas ni lee la propuesta de Mechelle. El crítico de arquitectura ataca 26 decisiones técnicas, que este archivo numera AD-31 a AD-56 para seguir la numeración de la primera revisión.

### Veredictos por candidata

| Candidata | Título de la candidata | Necesidad | Solapamiento y tamaño | Verificabilidad | Cómo queda |
| --- | --- | --- | --- | --- | --- |
| C-P01 | Registrar por indicador la OM o la BP en P4 | C | C | F con C-B01 | US-47 reescrita, con una causa y una acción por PI, el tipo fijado por el semáforo y la sección «Análisis por indicador» de P4. US-48 guarda los campos de cada PI con una sola versión por carga, y US-53 lleva sus CHECK a las tablas por PI. Absorbe C-B01, el tipo de C-P02, C-P03, el cuerpo cerrado de C-C03, la Q16 de C-B03 y C-B06 |
| C-P02 | El hallazgo y el tipo de registro de cada PI salen del semáforo, también cuando supera la meta | F con C-P01 | F con C-P01 | C | US-45, con `hallazgo` y `tipo_registro` por PI en la ruta 13 y `tipo_de_registro()` en `abet_carga/resultados.py`, y US-47, con el hallazgo al comienzo del bloque de cada PI. D-39 fija el tipo y D-36 se propone cerrar con la frase de Claudia |
| C-P03 | La descarga del R-17 se habilita solo con todos los PI registrados | F con C-P01 | F con C-P01 | F con C-B01 | US-49 conserva su regla, porque la ruta 16 acepta solo una declaración completa, y cambia sus textos a «cada indicador». La ruta 16 responde 422 «Complete la causa y la acción de cada indicador.» (propuesta), y Q17 vigila la completitud. El 422 que nombra los PI faltantes y el contador de avance no entran |
| C-P06 | El R-17 escribe la OM o la BP de cada PI desde la base | C | F con C-B02 | F con C-B02 | Se fusiona con C-B02 en US-50. La hoja «Acciones por indicador» queda fuera (D-41) |
| C-P04 | Ver la ficha del R-17 en P4 antes de descargarlo | M | M | C | Fuera de alcance, después de la semana 16. P4 mostrará los resultados por PI con el semáforo cuando se construya US-46 |
| C-P05 | Ver la rúbrica de mi sección según su estadio | R | M | M | Fuera de alcance, después de la semana 16, con D-06 y D-38 |
| C-P07 | Cada registro nace con estado Propuesta y sin responsable ni plazo | F con C-C03 | M | F con C-C03 | Se fusiona con C-C03. V1_12 no lleva columna de estado (AD-43) |
| C-C01 | Cargar la programación docente del ciclo desde el archivo post-matrícula | C | C | C | Spec 006 nueva, desde US-55, sin migración y antes de la semana 14. Su escenario del correo se retitula «Un correo con mayúsculas o espacios se normaliza», y la contraseña sigue fuera del guion (D-45 de la spec 006) |
| C-C02 | El R-17 lleva el nombre del docente de la sección desde la base | M | M | M | Fuera de alcance, con D-12 de la spec 001. La sección ya sale de la base en D11 del R-17 |
| C-C03 | La acción declarada queda en estado Propuesta, sin responsable ni plazo en P4 | C | F con C-P01 | C | US-47. La ruta 14 deriva `estado` PROPUESTA en cada indicador declarado sin guardarlo, y las rutas 15 y 16 rechazan con 422 un cuerpo con `responsable`, `plazo` o `estado` |
| C-C04 | Un aviso nombra la columna ABET que el lector no reconoce y el nombre estándar que espera | C | P | C | La regla de las lentes la deja en el sprint, pero el alcance aprobado la saca. El aviso de columna mal nombrada va después de la semana 16, y D-43 fija en su lugar el nombre estándar provisional «ABET SO4.1», que el lector ya acepta |
| C-C05 | Coordinador de curso y coordinador de área como asignaciones con alcance propio | M | M | M | Fuera de alcance, en la spec del R-18 (D-42) |
| C-C06 | El coordinador de curso incorpora la acción al R-18 con responsable y plazo y la deja Revisada | M | M | M | Fuera de alcance, en la spec del R-18, y absorbe C-B07 |
| C-C07 | El coordinador de área aprueba o ajusta la acción y el R-18 de la asignatura sale con su estado | M | M | M | Fuera de alcance, en la spec del R-18, que espera la plantilla oficial |
| C-B01 | V1_12 guarda un registro por PI con su tipo OM o BP en lugar de un texto por carga | F con C-P01 | F con C-P01 | C | Se fusiona con C-P01. V1_12 se rediseña con cuatro tablas (J-38), con los permisos exactos de `abet_app` sin DELETE y el escenario del INSERT directo con un PI ajeno |
| C-B02 | El R-17 compone los recuadros A y B desde los registros por PI sin tocar la plantilla oficial | F con C-P06 | C | C | US-50 reescrita, con un párrafo por PI y un prefijo sin cifras en B29:I31 y B34:I36, la plantilla intacta y el tope de alto de fila validado en la ruta 16 (J-39) |
| C-B03 | Consultas de control de la declaración por PI (Q16 ampliada, Q17 y Q18) | F con C-P01 | P | C | Q16 ampliada a las tablas por PI en US-53, y Q17 nueva de completitud en US-53, que US-49 cita. La comparación de la foto con la vista y Q18 no entran (AD-37) |
| C-B04 | La muestra para el archivo ABET (Bajo, Medio y Alto) queda en la base sin texto | R | M | M | Fuera de alcance, después de la semana 16 |
| C-B05 | La base no guarda texto libre por estudiante mientras la carrera no decida la observación del evaluador | R | R | C | Fuera de alcance. La observación por alumno no entra a la base, y Q19 no entra (AD-54) |
| C-B06 | El reemplazo hereda el análisis por PI y recalcula su tipo con las cifras nuevas | F con C-P01 | M | C | US-54 reescrita por `pi_id`, solo para los PI que la carga nueva reconoce, con el tipo recalculado por su semáforo. El aviso del tipo anterior no entra, y la historia se construye al final (J-41) |
| C-B07 | El estado de la acción de mejora (Propuesta, Revisada, Aprobada) se registra como eventos | F con C-C06 | F con C-C06 | F con C-C06 | Fuera de alcance, fusionada con C-C06 en la spec del R-18 |

Cuentas por lente.

| Lente | S | C | F | P | M | R |
| --- | --- | --- | --- | --- | --- | --- |
| Necesidad | 0 | 5 | 8 | 0 | 5 | 3 |
| Solapamiento y tamaño | 0 | 3 | 6 | 2 | 9 | 1 |
| Verificabilidad | 0 | 10 | 5 | 0 | 6 | 0 |

Tres desacuerdos se resuelven con el alcance aprobado. El hallazgo de C-P02 entra, aunque las lentes de necesidad y de solapamiento lo sacan por repetir la tabla de P4, porque el crítico lo sostiene (AD-42) y la hoja «Acciones» de la propuesta de Mechelle trae un hallazgo automático por PI. La parte A de C-C04, que solo cambia el mensaje de PI_DEL_PLAN_AUSENTE, no entra, y el riesgo del nombre de la actividad lo cubre D-43 antes de la capacitación. C-B06 queda dentro de US-54, aunque la lente de solapamiento la mueve a después, porque la herencia por `pi_id` es la forma de US-54 con V1_12 rediseñada.

### Choques de numeración y de diseño entre las candidatas

| Choque | Lo reportan | Resolución |
| --- | --- | --- |
| Dos listas de decisiones con los mismos números y otro sentido (D-39 a D-45 y J-38 a J-42) | Solapamiento y verificabilidad | Una sola lista, en la tabla de renumeración de abajo |
| Q17 en C-P03 y en C-B03 con reglas distintas, y Q18 a Q20 repartidas sin reservar | Solapamiento y verificabilidad | Q17 es solo la completitud (AD-37). Q18 a Q20 no se usan. La rama `docs/002-capstone`, sin fusionar, usa Q16 a Q20 con otro sentido y tendrá que renumerar al entrar, como su V1_10 |
| P7 nombra a la vez la rúbrica y la revisión del coordinador | Solapamiento y verificabilidad | El cambio no agrega pantallas, y las dos quedan fuera de alcance |
| SIN_DATO como OM obligatoria (C-P01, C-P02 y C-P03) frente a sin registro (C-B01 y C-B02) | Las tres lentes y el crítico | Sin registro obligatorio, y el R-17 escribe «5.3 · Sin calificaciones en esta carga.» (propuesta, D-40), con el número de cada PI |
| Estado como columna con DEFAULT (C-P07) frente a estado derivado (C-C03 y C-B07) | Solapamiento, verificabilidad y crítico | Derivado en la ruta 14 y sin columna (AD-43) |
| OM y BP frente a OPORTUNIDAD_MEJORA y BUENA_PRACTICA, causas frente a causa, y 700 frente a 800 | Necesidad y solapamiento | OPORTUNIDAD_MEJORA y BUENA_PRACTICA, `causa` y `accion` en singular, y 800 puntos de código (J-39) |
| Foto del logro y la meta, que solo hace falta si el prefijo lleva cifras | Necesidad y solapamiento | El prefijo va sin cifras y la foto se guarda igual como evidencia del ciclo (J-40) |

### Renumeración de las decisiones propuestas

| En el JSON de la revisión | Sentido | Número final |
| --- | --- | --- |
| D-39 de las dos listas | Qué registra el profesor por PI y quién fija el tipo | D-39 |
| D-43 de la primera lista y D-40 de la segunda | Si un PI SIN_DATO exige registro | D-40 |
| D-41 de la primera lista | Dónde van las OM y las BP en el R-17 oficial | D-41 |
| D-42 de la primera lista | Responsable, plazo y estados Revisado y Aprobado | D-42 |
| D-45 de la primera lista y la pregunta sobre el nombre de la actividad | Nombre estándar de la actividad de Blackboard | D-43 |
| D-36, ya abierta | Si la sección en la meta registra | D-36, que se propone cerrar |
| D-08 de la spec 001, ya abierta | Los enunciados de B28 y B33 hablan de «no alcanzar el indicador» | D-08, sin cambio de la plantilla |
| La pregunta sobre el archivo de la programación | Formato, dueño y fecha del archivo | D-44 de la spec 006 |
| La pregunta sobre la cuenta del profesor | Si el guion crea la cuenta | D-45 de la spec 006 |
| J-38 de las dos listas | Forma de V1_12 | J-38 |
| J-39 de las dos listas | Tope por campo | J-39, con 800 |
| J-40 de la segunda lista | Foto de logro, meta y semáforo | J-40 |
| J-41 de la primera lista y J-42 de la segunda | Orden de construcción | J-41 |
| D-40 y D-44 de la primera lista, D-41 y D-42 de la segunda, y J-40 y J-41 de la primera y la segunda | Rúbrica por estadio, ficha de la propuesta, muestra, observación por alumno, pantalla P7 y columnas reservadas | Sin número, porque quedan fuera de alcance |

### Veredicto del crítico de arquitectura

| N.º | Decisión | Veredicto | Lo que adopta el cambio |
| --- | --- | --- | --- |
| AD-31 | Un registro por PI, con cabecera por carga y una tabla hija por PI, en lugar de un par A y B por carga | SE_SOSTIENE | J-38 y US-47. Una columna jsonb perdería los CHECK por columna y la FK a `abet.carga_columna` |
| AD-32 | Rediseñar V1_12 antes de construirla y dejarla solo con las tablas de mejora | SE_SOSTIENE | V1_12 no existe en el repositorio ni en Neon, así que se rediseña sin migración correctiva. Toda definición de datos ajena a la mejora va en V1_13 o después, y Jefferson reaprueba el cambio antes de construir (T008) |
| AD-33 | Claves de `abet.mejora_declaracion_pi` y sus FK compuestas | SE_SOSTIENE | Clave primaria (`declaracion_id`, `pi_id`), `carga_id` no nulo, FK a la cabecera por (`declaracion_id`, `carga_id`) y FK (`carga_id`, `pi_id`) a `abet.carga_columna` por `uq_carga_columna_pi`. Los tipos usan los códigos largos OPORTUNIDAD_MEJORA y BUENA_PRACTICA |
| AD-34 | El Back fija el tipo, y el CHECK de tipo lo ata a `logro_pct >= meta_pct` | CAMBIAR | `tipo_de_registro()` en `abet_carga/resultados.py` con el semáforo, la foto de semáforo, logro y meta con columnas nulas y un CHECK de coherencia entre tipo y semáforo. Si D-39 admite una OM en un PI VERDE, basta con quitar ese CHECK |
| AD-35 | Qué PI cubre la declaración que habilita el R-17 | CAMBIAR | D-40. La declaración cubre cada PI de la carga con al menos una medición calificada, y un PI SIN_DATO no exige registro |
| AD-36 | Foto del logro, la meta y el semáforo en cada fila de la declaración | SE_SOSTIENE | J-40. La foto conserva lo que vio el profesor, y un cambio posterior de la meta del conjunto BORRADOR no obliga a declarar otra vez. El hallazgo no se guarda, porque una función pura lo vuelve a armar |
| AD-37 | Q17 que compara la foto con `abet.v_r17_por_pi` (C-B03) y Q17 de completitud (C-P03) | CAMBIAR | Q17 es solo la completitud, de 0 filas, igual en `pruebas.sql` y en `controles_neon.sql`. La comparación de la foto no es control, porque un cambio legítimo de la meta la pondría en rojo, y con J-40 tampoco pide una declaración nueva |
| AD-38 | Una sola versión del borrador por carga en la cabecera `abet.mejora_borrador` | SE_SOSTIENE | US-48. Las rutas 15 y 16 llevan el arreglo `indicadores` y el PUT reemplaza el conjunto de los PI en la misma transacción que sube la versión |
| AD-39 | Tope fijo de 700 u 800 puntos de código por campo | CAMBIAR | J-39. 800 puntos de código por campo, y la ruta 16 rechaza con 422 una declaración cuyos recuadros A o B compuestos no caben en el alto de fila, con la misma función de `r17.py` que fija el alto de las filas 31 y 36 |
| AD-40 | A y B compuestos con un párrafo por PI y su prefijo de tipo, sin tocar la plantilla ni B28 ni B33 | SE_SOSTIENE | US-50 y D-41. El prefijo va sin cifras, como «5.2 · Oportunidad de mejora. …» (propuesta), porque las cifras ya salen en el bloque II |
| AD-41 | Hoja nueva «Acciones por indicador» en el R-17 | DUDOSA | No entra. D-41 deja la hoja aparte para después |
| AD-42 | Hallazgo automático y tipo de registro por indicador en la ruta 13 | SE_SOSTIENE | US-45. El hallazgo usa el logro sobre calificados y la meta, como «5.2: 63,6 % en Satisfactorio o más, meta 80,0 %» (propuesta), y el Front lo copia sin calcularlo. El promedio de nivel no entra |
| AD-43 | Columna `estado` con DEFAULT 'PROPUESTA' y un CHECK con REVISADO y APROBADO | CAMBIAR | Sin columna de estado. La ruta 14 deriva PROPUESTA en cada indicador declarado, y la revisión futura irá en una tabla de eventos propia (D-42) |
| AD-44 | Las rutas 15 y 16 rechazan con 422 un cuerpo con claves fuera del contrato | SE_SOSTIENE | US-47. Responsable, plazo y «Cómo sabremos que mejoró» tampoco entran como columnas nulas en V1_12 |
| AD-45 | Roles nuevos de coordinador de curso y de área frente a asignaciones con alcance | CAMBIAR | Fuera de alcance, en la spec del R-18. La alternativa de asignaciones por periodo y asignatura queda como insumo de esa spec |
| AD-46 | Registro en P4 con un bloque por PI frente a una pantalla nueva | SE_SOSTIENE | US-47. La sección «Análisis por indicador» va debajo de «Cómo va su sección», sin pantalla ni dirección nuevas, y lleva la nota de US-53 |
| AD-47 | Pantalla P7 con la ruta 17 para la rúbrica de la sección | DUDOSA | Fuera de alcance |
| AD-48 | Ficha del R-17 en la ruta 13, con estadio, meta y estudiantes evaluados | DUDOSA | Fuera de alcance. La ruta 13 no suma la descripción del PI ni el instrumento en este cambio |
| AD-49 | Guion repetible de la programación docente, en seco por omisión y con `--aplicar` en una transacción | SE_SOSTIENE | Spec 006, sin migración, con la consulta de control de secciones sin docente |
| AD-50 | Nombre del docente en `acceso.usuario_autorizado.nombre` | DUDOSA | Fuera de alcance, con D-12 de la spec 001 y nunca en V1_12 |
| AD-51 | Motivo nuevo COLUMNA_ABET_NO_RECONOCIDA de tipo AVISO | CAMBIAR | Fuera de alcance. D-43 fija el nombre estándar antes de la capacitación |
| AD-52 | Revisión del coordinador de curso, aprobación del área y R-18 | DUDOSA | Fuera de alcance, en la spec del R-18, con eventos de solo INSERT por (`declaracion_id`, `pi_id`) |
| AD-53 | Muestra Bajo, Medio y Alto con DELETE para `abet_app` | CAMBIAR | Fuera de alcance |
| AD-54 | Q19, que ninguna tabla de `abet` unida a un estudiante tenga texto libre | SE_SOSTIENE | No entra, porque el cambio no agrega texto por estudiante y la observación por alumno no entra a la base. Vuelve con la spec que agregue una tabla unida a estudiantes |
| AD-55 | Herencia del análisis por `pi_id` en el reemplazo, con el tipo recalculado | SE_SOSTIENE | US-54 con prioridad P2, al final del orden de J-41, sin el aviso del tipo anterior |
| AD-56 | Q16 ampliada, CHECK sin códigos ni correos por columna y permisos exactos | SE_SOSTIENE | US-53. `abet_app` recibe INSERT y UPDATE de columnas exactas en las dos tablas del borrador e INSERT en las dos de la declaración, sin DELETE. Un PI vaciado en el borrador queda con `causa` y `accion` nulas por UPDATE |

### Hechos del código que corrigen supuestos de las candidatas

- `abet.v_r17_por_pi` expone el código del PI y el número del SO, no `pi_id`, y no trae `n_calificados` ni CORTE_ROJO, que la ruta 13 lee aparte de `abet.parametro_valor`.
- `uq_carga_columna_pi` es UNIQUE (`carga_id`, `pi_id`) en V1_07, así que sostiene la FK de las tablas por PI.
- `crear_rol_app.sql` prohíbe DELETE en todas las tablas y fija listas exactas de INSERT por tabla y por columna.
- `_franja()` de `r17.py` suma B7:I7 a las 45 celdas combinadas de la plantilla cuando la carga es provisional, y las filas 29 a 31 se comparten con la tabla K28:Q31.
- El alto de fila de Excel llega a 409 puntos, así que un tope de 2000 por campo con saltos libres ya puede pasarlo, y 13 de las 47 asignaturas de `abet.asignatura_so` (61 filas en V1_03) tributan a más de un SO, con planes que pueden pasar de 3 PI.
- `_ENCABEZADO_DE_PI` de `abet_carga/lector.py` exige el código N.M, así que no acepta «ABET-SO-PI» con guiones ni «ABET SO4 [» sin PI.
- `_ALCANCE` de `app/permisos.py` da la sección por `acceso.docente_seccion` solo al rol PROFESOR, y `asignar_claves.py` vive en `ABET_SIS_MED/herramientas_neon`, fuera del repositorio.
- La 412 de 450002 y `docente.varias@example.invalid` están en `db/datos/varias_secciones_2026_2_inventado.sql`, y sus cifras de 81,8 %, 54,5 % y 90,9 % coinciden con `semaforo.feature`. Con D-39, esa carga da BP, OM y BP, y es el ejemplo de un PI sobre el 80 % que pide Claudia.
- Q16 y `puede_declarar()` todavía no existen, porque T039 y T032 siguen abiertas.

### Respuestas para la carrera que son hechos y no historias

- La sección ya sale sola de la base en D11 del R-17, y el nombre del docente espera D-12.
- Las rúbricas maestras están en `abet.rubrica_nivel`, una por PI con niveles -1 a 5 y sin estadio.
- La columna de la muestra para el archivo ABET de la propuesta es manual, y el sistema no elige muestras.

### Decisiones que salen de la revisión del 2026-11-21

- De la carrera, D-39 (tipo de registro fijado por el semáforo, con un registro por PI), D-40 (un PI SIN_DATO no exige registro), D-41 (dónde van las OM y las BP en el R-17 oficial), D-42 (responsable, plazo y estados Revisado y Aprobado, fuera de esta spec) y D-43 (nombre estándar de la actividad de Blackboard, urgente antes de la capacitación de la semana 14), con su valor provisional en la spec. D-36 se propone cerrar con la frase de Claudia, y D-08 sigue abierta con los enunciados de B28 y B33.
- De Jefferson, J-38 (cuatro tablas en V1_12), J-39 (tope de 800), J-40 (foto de logro, meta y semáforo) y J-41 (orden de construcción), con el valor que propone la spec.
- De la spec 006, D-44, D-45 y J-42.
