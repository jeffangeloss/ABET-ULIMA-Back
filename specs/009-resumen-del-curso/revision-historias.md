# Revisión por refutación de las historias del resumen del curso

**Fecha**: 2026-11-24
**Spec**: [spec.md](./spec.md)
**Entrada**: 21 candidatas escritas desde cuatro ángulos, el de la coordinación del curso o de la carrera (C-01 a C-08), el de la base, el Back y las cifras (C-20 a C-23), el del acceso, la privacidad y la evidencia (C-40 a C-44) y el de las otras páginas del tablero (C-60 y C-61), cada una con su pantalla, sus rutas y tablas y su Gherkin en español. Salen del pedido de Jefferson del 2026-11-24 de llevar al sistema la página «Resumen Curso» del tablero de Power BI de Stefanny Montaño
**Salida**: 4 historias (US-91 a US-94) en 3 archivos `.feature`
**Fuentes**: los informes de las tres lentes y del crítico de arquitectura de la sesión del 2026-11-24. El tablero es `infodata/Resumen de indicadores ABET - Cursos de Carrera.pbix`, fuera de todo repositorio, y la tabla maestra real de Química General vive en `ABET_SIS_MED/datos_reales/quimica_2026_1/`. Ninguna candidata ni esta revisión copia un dato real

## Método

Cada candidata parte refutada y sobrevive solo si resiste tres lentes independientes, como en las specs 001 y 003 a 008. La lente de necesidad pregunta si la exige el pedido, una regla vigente o la capacitación, y si cambia algo que `develop` no hace ya. La lente de solapamiento y tamaño aplica INVEST (independiente, negociable, valiosa, estimable, pequeña y verificable) y busca choques con las historias que ya existen. La lente de verificabilidad recalcula las cifras de cada escenario y comprueba sus columnas, cuentas y mensajes contra el código y la base. Un crítico de arquitectura juzga aparte las decisiones técnicas con SE_SOSTIENE, CAMBIAR o DUDOSA.

Los veredictos posibles son SOBREVIVE (S), CORREGIR (C), FUSIONAR (F), PARTIR (P), MOVER_A_DESPUES (M) y REFUTADA (R). Una candidata sale cuando dos lentes o más la marcan R o M, como en las specs anteriores.

## La página «Resumen Curso» del tablero

El tablero usa el formato PBIR (Power BI Enhanced Report), así que cada visual se lee en `Report/definition/pages/*/visuals/*/visual.json`. La página «Resumen Curso» trae segmentadores de año y ciclo, curso, PI, profesor, sección y nivel con competencia, un gráfico de columnas con el promedio de la calificación por profesor y PI, una tarjeta «% Profesores Aprobados», una tarjeta «Promedio Nota», una torta de «Secciones Aprobadas» y «Secciones No Aprobadas», una barra apilada al 100 % de «Alumnos Aprobados» y «Alumnos Desaprobados» y una tabla con sección, profesor, «Promedio Nota» y «% Alumnos 3-4». Las fórmulas DAX (Data Analysis Expressions) de esas medidas viven en el `DataModel` comprimido y no se leen sin una herramienta aparte, así que su definición exacta queda como D-56.

## Veredictos por candidata

| Candidata | Título | Necesidad | Solapamiento y tamaño | Verificabilidad | Destino |
| --- | --- | --- | --- | --- | --- |
| C-01 | La coordinación ve las cifras del curso | C, repite US-80 de la spec 008 y solo suma el promedio | F con C-20, unas 4 h | C, la vista no expone `n_calificados`, que es `n_total` menos `n_sin_evidencia`, y el promedio pide los conteos por nivel | US-91, con C-20, C-21, C-23, C-40 y C-41 |
| C-02 | Una fila por sección con promedio y porcentaje | F con C-01, porque P6 ya da la fila por sección | C, decir qué suma P8 a P6, unas 3 h | S, «Sin carga publicada» existe en `MisLogros.tsx` y el orden es `a.codigo, s.numero` | US-92, con C-03, C-04, C-42 y C-43 |
| C-03 | Gráfico de barras por sección con la meta | R, P6 ya dibuja una barra por sección y PI sin biblioteca | M, la tabla cubre la meta, unas 4 h | C, los rótulos de P6 son «En la meta» y «Debajo de la meta» | Sale por dos lentes. Su barra por fila entra a US-92 como corrección de C-02 |
| C-04 | Reparto del curso entre 1 y 2 y entre 3 y 4 | M, el 23 de 33 ya sale de C-01 | M, unas 2,5 h | S, 10 de 33 es 30,3 % y suma 100,0 con 69,7 | Sale por dos lentes. La barra de dos tramos del curso entra a US-92 como forma de mostrar la cifra de US-91 (CAMBIAR del crítico) |
| C-05 | Torta de secciones en la meta | R, repite «1 de 3 en la meta» | R, una torta de dos porciones no aporta | S, 1 en la meta y 2 debajo | REFUTADA. La reemplaza el conteo escrito con su barra (J-62) |
| C-06 | La coordinación elige el curso y el PI | M, el arranque es 5643 | P, separa el selector de curso del de PI | C, la ruta 18 da periodos y no cursos, y 5643 tiene un solo PI | US-93, solo el selector de curso de la coordinación de la carrera. El PI va como lista en la respuesta |
| C-07 | Porcentaje de profesores que cumplen | R, choca con J-28, H05 y BR-RESULTADOS-10 | R, ranking encubierto | R, `PROFESOR` es nulo en la vista de la tabla maestra | REFUTADA hasta D-57 |
| C-08 | Descarga del resumen en Excel | M, nadie lo pidió y el R-17 ya es la evidencia | M, la ruta 19 está reservada (J-55) | C, el Gherkin no nombra hoja ni celdas | Sale por dos lentes, a «Fuera de alcance» |
| C-20 | Una sola ruta con lista cerrada de claves | C, el campo `agregados` de la ruta 12 ya existe como propuesta | F con C-01, ruta 12 y no ruta nueva | C, elegir una sola ruta y sumar el promedio y los conteos a la lista cerrada | US-91. El crítico sostiene la ruta 20 (J-61) |
| C-21 | La regla de la meta es la del R-17 | R, BR-RESULTADOS-06 ya lo exige | C, es criterio de C-01 | C, un 79,9 exacto necesita 107 de 134, así que el escenario usa 4 de 5 | Escenario de US-91 |
| C-22 | El resumen coincide con la tabla maestra | S, es la prueba ante Stefanny | S, unas 3 h | C, el mensaje no existe y el ensayo inventado tiene 3 secciones publicadas, no 18 | US-94 |
| C-23 | Un curso sin cargas no inventa cifras | F con C-01 | F con C-01 | S, coincide con la sección 15.6 del contrato | Escenario de US-91 |
| C-40 | El profesor no ve el resumen | F con C-01 | F con C-20 | C, el 403 vale solo para una ruta nueva y el menú se condiciona por rol en `App.tsx` | Escenarios de US-91 y US-92 |
| C-41 | Cada coordinación ve solo su alcance | R, BR-ACCESO-13 ya lo prueba | F con C-20 | C, decidir 403 o lista vacía, y las rutas 12 y 17 dan 200 con lista vacía | Escenario de US-91, con 200 y lista vacía |
| C-42 | Sin ranking de docentes | R, es BR-RESULTADOS-10 | F con C-02 | S | Escenario de US-92 |
| C-43 | Teclado, lector de pantalla y 375 px | R, US-81 y US-82 valen para toda pantalla | F con C-02 | C, P8 entra a la lista `PANTALLAS` de `visual.spec.ts` | Escenario de US-92 |
| C-44 | Humo de Playwright en P8 | F con C-01 como tarea | F con C-02, es tarea y no historia | C, el humo publica 701 a 703 con 5 estudiantes, así que las cifras son las de su generador | Tarea `[Front]` del humo |
| C-60 | Histórico por periodo | M, la página no se pidió | M, sin Gherkin y con un solo periodo | P | Sale, a «Fuera de alcance» |
| C-61 | Resumen por competencia y nivel | M, otra página | M, espera a D-50 y a la «Base cursos - Nivel» de Industrial | P | Sale, a «Fuera de alcance» |

## Veredicto del crítico de arquitectura

| Decisión | Veredicto | Razón | Alternativa que adopta la spec |
| --- | --- | --- | --- |
| Ruta 20 frente al campo `agregados` de la ruta 12 | SE_SOSTIENE | La ruta 12 es una por usuario, no recibe identificadores (J-23, BR-RESULTADOS-01) y también la usa el profesor, y con `agregados` la coordinación de la carrera recibe unas 150 secciones para ver un curso | Ruta 20 solo para COORDINADOR, con el 403 `SOLO_COORDINACION` de la ruta 17 y la asignatura filtrada dentro de `secciones_visibles()`. La sección 15.6 del contrato, US-80 y FR-016 de la spec 008 pasan a sustituidas (J-61) |
| Construir el agregado con D-32 abierta | CAMBIAR | D-32 es de la coordinación de Ambiental y de la Oficina de Calidad, y el tablero de Stefanny no la responde solo | La spec construye la suma de estudiantes por PI y curso como valor provisional de D-32, con la franja provisional en P8, y Jefferson decide en J-60 si eso basta para construir |
| Promedio desde `n_nivel_1` a `n_nivel_4` sin migración | SE_SOSTIENE | `ck_medicion_nivel` limita el nivel de 1 a 4, así que la suma de cada nivel por su conteo entre la suma de los conteos da el promedio exacto | `ROUND(numeric, 2)` en la consulta de la ruta, nunca en float, con la suma de los conteos como denominador |
| Gráficos con HTML, CSS y SVG propios | SE_SOSTIENE | J-24 y el invariante 7 de ADR-008, y `package.json` del Front solo trae react y react-dom | Barras con Tailwind y el ancho en `style`, con `aria-hidden` y la cifra escrita |
| Torta de secciones | CAMBIAR | Con 18 secciones el conteo escrito dice más que dos porciones, y el ángulo se lee peor que la longitud | Conteo escrito con la barra de dos tramos (J-62) |
| Eje por número de sección y sin profesores | SE_SOSTIENE | BR-RESULTADOS-10, H05 y el invariante 5 de ADR-008 | Filas y barras por número de sección, sin segmentador de profesor (D-57) |
| Tarjeta «% Profesores Aprobados» | CAMBIAR | Necesita D-51 y con un profesor por sección repite el porcentaje de secciones | Se omite y P8 muestra «secciones en la meta» |
| Pantalla P8 nueva | SE_SOSTIENE | P6 la ve también el profesor y P7 muestra etapas, no cifras | P8 «Resumen del curso», solo en el menú de la coordinación y enlazada desde cada curso de P7 (J-63) |
| ADR-010 que cambia ADR-008 en parte | SE_SOSTIENE | ADR-008 deja Power BI para la coordinación y no suma secciones mientras D-32 siga abierta | ADR-010 «Resumen del curso para la coordinación en el sistema», con ADR-008 vigente y modificada en parte |
| Igualdad con el tablero sin datos reales en git | DUDOSA | Las fórmulas DAX no se leyeron y el oráculo descansa en supuestos | Datos inventados con cifras calculadas a mano en el repositorio, el conciliador fuera de git con «igual» o «distinto» y D-56 a Stefanny |
| Parámetro `pi` en la consulta | CAMBIAR | Química mide un solo PI y el promedio del tablero sin filtro mezclaría PI | Sin `pi`. La respuesta trae un elemento por PI del plan, en orden de SO y PI |
| Segmentadores de sección y nivel | CAMBIAR | Filtrar en el Front obliga a recalcular, lo que prohíbe BR-RESULTADOS-11 | Sin segmentadores de sección ni de nivel |
| Redondeo y regla de la meta del curso | CAMBIAR, para precisarlo | `en_meta()` compara la cifra ya redondeada a un decimal | Suma de logrados entre suma de calificados con `ROUND(…, 1)` en SQL y `en_meta()` sobre ese valor, como el R-17 |
| Qué cuenta como «aprobado» | CAMBIAR | La vista usa el `nivel_esperado` del conjunto de reglas y no un 3 fijo | Rótulo «nivel esperado o superior» y la marca provisional del curso si alguna sección la tiene |
| Curso de dos carreras con metas distintas | DUDOSA | El plan se une por la carrera de la carga y la meta del curso podría no ser única | `meta_pct` y `en_meta` del curso en `null` si las metas de sus secciones difieren, con su prueba |
| Denominador de las secciones | SE_SOSTIENE | Una sección sin carga no tiene cifras (BR-RESULTADOS-07) | «En la meta» y «debajo de la meta» se cuentan sobre las publicadas, y «sin dato» va aparte |

## Hechos del código que corrigen supuestos de las candidatas

- `abet.v_r17_por_pi` no expone `n_calificados`, `pi_id` ni un promedio. Los calificados son `n_total` menos `n_sin_evidencia`, como en `_indicador` de `abet_carga/resultados.py` y `_logran` de `abet_carga/r17.py`.
- `en_meta` compara el logro ya redondeado a un decimal con la meta (`abet_carga/resultados.py`), y `_plan_de_accion` del R-17 usa la misma función.
- La siembra inventada de Química es la 701 a la 704 de 5643 en 2026-1, con docente701 a docente703, la 704 sin profesor y `coordinador.quimica@example.invalid` con alcance de la asignatura 5643 (`db/datos/quimica_2026_1_inventado.sql`), sin cargas sembradas y con un solo PI, el 6.1.
- `alcance_de` da el tipo CURSO a la coordinación de Química y CARRERA a `coordinacion@example.invalid` (`app/permisos.py`). La ruta 18 da periodos y no cursos.
- `PROFESOR` es nulo en `abet.v_tabla_maestra_pi`, así que la base no puede dar las vistas por profesor del tablero.
- P6 ya escribe «En la meta», «Debajo de la meta», «Sin carga publicada» y «Meta 80 %» (`src/pantallas/MisLogros.tsx`), y la navegación por rol vive en `src/App.tsx` con los rótulos por alcance en `src/servicios/rotulos.ts`.
- El humo de la spec 008 publica la 701, la 702 y la 703 con cinco estudiantes cada una, así que el humo de P8 compara con las cifras de ese generador.

## Faltantes que la spec cubre

- Una tabla de equivalencias entre los visuales del tablero y P8, con lo que se omite y por qué (sección «Equivalencias con el tablero» de la spec).
- La marca provisional del curso, que vale si alguna sección es provisional (BR-RESULTADOS-08).
- Los estudiantes sin evidencia del curso, que no cuentan como calificados y se informan aparte.
- El promedio de calificación como cifra propia del curso y de cada sección.
- La meta del curso en nulo si sus secciones traen metas distintas.

## Lista final del sprint

| Historia | Prioridad | Candidatas | Estimación |
| --- | --- | --- | --- |
| US-91 La coordinación recibe las cifras del curso en la ruta 20 | P1 | C-01, C-20, C-21, C-23, C-40 y C-41 | 6 h |
| US-92 P8 muestra el resumen del curso | P1 | C-02, C-03 y C-04 como corrección, C-42 y C-43 | 7 h |
| US-93 La coordinación de la carrera elige el curso | P2 | C-06 en parte | 2 h |
| US-94 El conciliador compara el curso y sus secciones con la tabla maestra | P2 | C-22 | 3 h |

El humo de P8 (C-44) es una tarea `[Front]`. La estimación suma unas 18 h más el contrato y el cierre.

## Decisiones que salen de la revisión

- D-56 a Stefanny Montaño, las fórmulas DAX de las medidas del tablero. Cerrada el 2026-11-25 con las fórmulas leídas del archivo, sin cambio del valor provisional (`spec.md`, Clarifications).
- D-57 a la coordinación y a la Oficina de Calidad, si la coordinación ve vistas por profesor.
- J-60 a J-64 a Jefferson, que la spec lista con su valor provisional.
