# Revisión por refutación de las historias de las oportunidades de mejora en la carga

**Fecha**: 2026-11-18
**Spec**: [spec.md](./spec.md)
**Entrada**: 15 historias candidatas (C-01 a C-15), escritas desde el pedido literal de Jefferson del 2026-11-18. Ese pedido incluye el semáforo de la sección en P4, la declaración de causas y acciones con su borrador, el R-17 solo con esa declaración, la descripción del instrumento desde la base y el botón atrás del navegador
**Salida**: 10 historias (US-45 a US-54 de la spec), que absorben C-02, C-10, C-15, el punto (a) de C-14 y la parte A de C-09. C-08 y C-12 pasan a después, C-14 (b) pasa a después, y la parte B de C-09 queda sin escenario propio
**Fuentes**: `ABET_SIS_MED/notas_spec005/contexto_y_candidatas.md`, `auditoria_necesidad.md`, `auditoria_solapamiento.md`, `auditoria_verificabilidad.md`, `critica_arquitectura.md` y `sintesis.md`, en la carpeta de notas de la sesión del plan (fuera del repositorio)

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
