# Revisión por refutación de las historias de los resultados del profesor por SO

**Fecha**: 2026-11-17
**Spec**: [spec.md](./spec.md)
**Entrada**: 22 historias candidatas (C-01 a C-22), escritas desde cuatro ángulos, que son el profesor que consulta sus resultados y conserva su evidencia, la coordinación y el administrador técnico con la base, la privacidad, la seguridad y el límite de acceso, y la evidencia para la acreditación
**Salida**: 8 historias (US-37 a US-44 de la spec), que absorben C-07, C-21, el nombre del instrumento de C-08 y el escenario de la pantalla P6 de C-17. Diez candidatas o partes de candidatas pasan a después con su decisión abierta, C-17 queda refutada como historia y C-22 pasa a tarea de cierre
**Fuentes**: `spec004/contexto_y_candidatas.md`, `spec004/auditoria_necesidad.md`, `spec004/auditoria_solapamiento.md`, `spec004/auditoria_verificabilidad.md` y `spec004/critica_arquitectura.md`, en la carpeta de notas de la sesión del plan (fuera del repositorio)

## Método

Cada candidata parte refutada y sobrevive solo si resiste tres lentes independientes, como en las specs 001 y 003. La lente de necesidad pregunta si la exige el objetivo del sprint, el pedido literal de Jefferson o un requisito del lanzamiento, y si cambia algo que `develop` no fija ya con prueba. La lente de solapamiento y tamaño aplica INVEST (independiente, negociable, valiosa, estimable, pequeña y comprobable) contra las demás candidatas y contra US-01 a US-36, en especial US-06, US-15, US-16 y el corte 2 de la spec 001 (US-18 a US-21), que otra sesión implementa ahora. La lente de verificabilidad coteja cada escenario con V1_01 a V1_10, las dos vistas, `crear_rol_app.sql`, `db/pruebas/pruebas.sql`, los dos scripts de datos, `app/permisos.py`, `app/rutas/`, `abet_carga/r17.py` y los pasos de `tests/aceptacion/pasos/`, y recalcula cada cifra desde los niveles de `scripts/generar_exports_inventados.py`. Un crítico aparte ataca las catorce decisiones técnicas AD-01 a AD-14. Las candidatas llaman «ruta 11» a la ruta nueva, y la spec la numera 12, porque la spec 002 de la rama `docs/002-capstone` reserva la 11 en el contrato del Front.

Antes de escribir las candidatas, un subagente de búsqueda (Sonnet) revisa en solo lectura el material de `ABET_SIS_MED` fuera de los repositorios (los requisitos N#, los hallazgos H## y las preguntas P## de `Entregables/Revision_Requisitos_y_Tableros.xlsx`, el prototipo de Power BI y los R-17 de `Archivo/`) sin copiar ningún nombre, código ni nota. Las lentes de necesidad y de solapamiento corren con Sonnet y esfuerzo medio, la de verificabilidad con Sonnet y esfuerzo alto, porque recalcula cifras y nombres, y el crítico con el modelo de la sesión y esfuerzo alto, porque varias decisiones tocan el límite de acceso.

Los veredictos posibles son SOBREVIVE, CORREGIR, FUSIONAR, PARTIR, MOVER_A_DESPUES y REFUTADA. Una candidata queda en el sprint si al menos dos lentes no la sacan, es decir, si a lo sumo una la marca REFUTADA o MOVER_A_DESPUES, y las fusiones y particiones se aplican. Cuando dos lentes fusionan una candidata en historias distintas, la síntesis elige la que conserva el objetivo y lleva el resto como escenario de la otra. Este archivo registra los veredictos y su destino, y el razonamiento completo con su evidencia está en cada informe.

## Veredictos por candidata

Abreviaturas. S es SOBREVIVE, C es CORREGIR, F es FUSIONAR, P es PARTIR, M es MOVER_A_DESPUES y R es REFUTADA.

| Candidata | Título de la candidata | Necesidad | Solapamiento y tamaño | Verificabilidad | Historia final |
| --- | --- | --- | --- | --- | --- |
| C-01 | Ver mis resultados por SO en el periodo | S, sin la traza a N10, que pide una alerta automática | S con C, absorbe C-07, C-20 y el nombre del instrumento de C-08 y pierde los escenarios de alcance | C, `niveles` se lee como niveles cuando son conteos, falta la regla de «En la meta» y el escenario de la pantalla mezcla pytest y Vitest | US-37, con C-07, el nombre del instrumento de C-08 y los faltantes de accesibilidad, navegación, frontera del 80 % y números JSON |
| C-02 | Ver cómo se reparten mis estudiantes por nivel | S como P2, sin repetir el fixture de C-01 | C, solo la barra apilada y la suma de niveles igual a calificados | C, cifras exactas, fusionable en C-01 | US-43 |
| C-03 | Ver el consolidado de mis secciones por PI y por SO | M, D-32 abierta | M, D-32 y el doble conteo de Q08 | M, suma dos cursos distintos y la causa del escenario omite 5.2 | Después, sujeta a D-32 |
| C-04 | Comparar mis resultados con periodos anteriores | M, solo hay datos de 2026-2 | M | M, exige datos nuevos que AD-12 descarta | Después |
| C-05 | Ver mi resultado frente al de mi curso | M, choca con el límite literal y con D-33 | R, el agregado del curso menos la sección propia revela otras secciones | M, D-33 y H68 | Después, sujeta a D-33 |
| C-06 | Saber qué todavía no tiene resultado | S, recibe a C-21 | C, el estado SIN_CARGA ya existe en la ruta 4 | C, la frase de copia «en las 11 filas» no existe como paso | US-39, con C-21 y los faltantes de pantalla vacía y de profesor sin secciones |
| C-07 | Descargar el R-17 desde el reporte | F con C-01 | F con C-01 | F con C-01, partida en API y pantalla | Escenario de US-37 |
| C-08 | Ver el instrumento con que se mide cada PI | M, la descripción depende de C-12 y D-34 | P, el nombre a C-01 y la descripción a después | F con C-01 y M de la descripción | El nombre en US-37; la descripción, después con C-12 |
| C-09 | Ver qué estudiantes quedan debajo del nivel esperado | M, contradice a C-18 y a AD-14 | M | M | Después |
| C-10 | El coordinador ve los resultados de todas las secciones | S reducida, sin N9 | F con C-16 | C, cifras exactas | US-44 |
| C-11 | Ver los resultados de mi asignatura como coordinador de asignatura | M, rol nuevo y migración | M | M, `ck_usuario_autorizado_rol` | Después |
| C-12 | Registrar la descripción del instrumento de cada curso | M, D-34 y V1_11 | M | M | Después, sujeta a D-34 y J-27 |
| C-13 | Registrar el nombre del profesor y llevarlo al R-17 | M, D-12 abierta | M | M, Q15 no ve una columna `nombre` | Después, sujeta a D-12 |
| C-14 | Convertir a niveles 1 a 4 una rúbrica con otra escala | R, es de la carga y de D-30 | M | M, el escenario inventa una conversión | Después, en una spec de la carga, sujeta a D-30 |
| C-15 | Ver los resultados en Power BI con el filtro de cada profesor | M, fuera de alcance en la spec 001 | M | M, no se comprueba con pytest ni Vitest | Después, sujeta a J-21 |
| C-16 | El reporte nunca muestra una sección ajena | S con C | S con C, absorbe C-10, C-18 y el escenario de P6 de C-17 | C, el escenario de otro periodo no prueba aislamiento | US-38, con el escenario de P6 de C-17 y los faltantes de alcance leído en cada petición, guardia de sesión y 401 o 422 con `no-store` |
| C-17 | El profesor no sube un export a una sección ajena | R, cuatro escenarios aprobados ya lo cubren | R, repite US-06 y `varias_secciones.feature` | F con C-16 | Refutada; su escenario de P6 pasa a US-38 |
| C-18 | El reporte no expone estudiantes ni a otros usuarios | S reducida | F con C-16 | P, pytest por un lado y Vitest por otro | US-42 |
| C-19 | Las cifras del reporte son las del R-17 | S con C, con el profesor como rol | S con C, absorbe C-21 | C, falta decir cómo se compara la fracción del libro con el número de la API | US-40, con la parte de C-21 que compara el segundo porcentaje |
| C-20 | El reporte dice que es provisional | S | F con C-01 | C, falta el conjunto APROBADO que no define todos sus parámetros | US-41 |
| C-21 | El reporte muestra los dos porcentajes con estudiantes sin evidencia | F con C-06 | F con C-19 | S | Escenario de US-39 y escenario de US-40 |
| C-22 | Probar el reporte en la vista previa de develop | R, es tarea | R, es tarea | R, es tarea con estado inicial definido | T043 y T071 de `tasks.md` |

Cuentas por lente, tomadas de las tablas de cada informe. Una candidata marcada «SOBREVIVE (con CORREGIR)» cuenta como S, como en la spec 003.

| Lente | S | C | F | P | M | R |
| --- | --- | --- | --- | --- | --- | --- |
| Necesidad | 8 | 0 | 2 | 0 | 9 | 3 |
| Solapamiento y tamaño | 3 | 2 | 5 | 1 | 8 | 3 |
| Verificabilidad | 1 | 7 | 3 | 1 | 9 | 1 |

Tres desacuerdos se resuelven así. C-10 queda como historia propia, porque la necesidad y la verificabilidad la conservan y la ruta tiene que fijar qué responde al coordinador. C-21 se parte, porque la necesidad la lleva a C-06 y el solapamiento a C-19, así que su escenario de pantalla va en US-39 y su comparación con el R-17 en US-40. El nombre del instrumento de C-08 viaja en US-37, porque dos lentes lo ponen en C-01 y la tercera lo saca solo por la descripción.

## Historias faltantes

| Faltante | La proponen | Historia o requisito final |
| --- | --- | --- |
| La frontera del 80 %. Sin un caso de 80,0 % justo, nada fija si «En la meta» es llegar a la meta o superarla | Verificabilidad (F-01) | US-37, escenario «El 80,0 % justo queda en la meta», con la copia de la 410 sin nota de 5.3 en la fila 9 (8 de 10) |
| Leer el reporte sin depender del color y con teclado | Solapamiento (F-01), verificabilidad (F-10), crítico (AD-06) | US-37, escenario de P6, y FR-012 |
| Llegar a P6 desde P2 y desde P4 sin confundirla con «Ver resultado» | Necesidad (F-01 y F-05), solapamiento (F-02), crítico (AD-11) | US-37 y US-44, escenarios de navegación, y FR-011 |
| El contrato dice «Los porcentajes no viajan por la API, porque viven solo en el R-17.» y la ruta 12 los lleva | Necesidad (F-02), solapamiento (F-03), verificabilidad (F-08), crítico (AD-03) | ADR-008 del Front, FR-017 y T011 |
| El profesor sin secciones y la pantalla P6 en espera, en error o vacía | Necesidad (F-03), verificabilidad (F-03 y F-09) | US-39, escenarios de la lista vacía y de los estados de P6 |
| El prototipo de Power BI no se comparte con profesores mientras no tenga seguridad por filas | Necesidad (F-04) | «Fuera de alcance» y J-21 |
| La ruta nueva responde 401 y 422 con `Cache-Control: no-store` | Verificabilidad (F-02) | US-38 y US-42 |
| El alcance se lee en cada petición, no al iniciar la sesión | Verificabilidad (F-04) | US-38, escenario «El alcance se lee en cada petición» |
| Las dos secciones 412 de asignaturas distintas no se mezclan | Verificabilidad (F-05) | US-37, escenario 1 |
| Leer el reporte no escribe en la base y Q01 a Q15 siguen en 0 | Verificabilidad (F-06) | US-40, escenario «Leer el reporte no escribe en la base» |
| Un `seccion_id` de otro periodo frente al `periodo` pedido | Verificabilidad (F-07) | Desaparece con J-23, porque la ruta no recibe `seccion_id`; US-38 prueba que un `seccion_id` en la consulta no cambia la respuesta |
| La franja de un conjunto APROBADO que no define todos sus parámetros | Verificabilidad (F-11) | US-41, escenario 3 |
| Un PI sin instrumento en el plan | Verificabilidad (F-12) | Edge Cases y prueba unitaria de la ruta, porque ningún dato inventado tiene ese caso |
| Un archivo que recibe 409 no cambia la carga que muestra el reporte | Verificabilidad (F-13) | Edge Cases |
| Los porcentajes viajan como número JSON y no como texto | Verificabilidad (F-14), crítico (riesgo 4) | US-37, escenario «Las cifras viajan como números de un decimal», y FR-007 |
| Ninguna ruta con datos responde sin sesión | Crítico (riesgo 1) | US-38, escenario de las rutas registradas, FR-003, J-25 y BR-ACCESO-10 |
| Tres lecturas en instantáneas distintas pueden dejar una sección PUBLICADA sin indicadores | Crítico (riesgo 2) | FR-004 y Edge Cases |
| El filtro por `carga_id` baja dentro de la vista con `security_barrier` | Crítico (riesgo 3) | SC-005 y T034 |
| Una sola regla de «en la meta» para la ruta y el R-17 | Crítico (riesgo 5) | FR-008 y US-40, escenario 1 |
| Los nulos de la regla (sin nivel esperado o sin meta definidos) | Crítico (riesgo 6) | Edge Cases y FR-013 |
| La unión por catálogo y el orden de los PI con un 5.10 | Crítico (riesgos 7 y 8) | FR-005 y T035 |
| El volumen del coordinador, del orden de 150 secciones | Crítico (AD-09 y riesgo 12) | US-44, SC-005 y T034 |

## Defectos transversales de verificabilidad

| Defecto | Resolución en la spec |
| --- | --- |
| Escenarios que mezclan lo que prueba pytest con lo que prueba Vitest | Cada escenario de pantalla va aparte con `@delegado_a_vitest`, como en la spec 003 |
| Las frases de copia «en las filas 3, 6 y 10» y «con la columna 5.3 vacía en las 11 filas» no existen en `REGLAS_DE_COPIA` (`tests/aceptacion/pasos/conftest.py:636-690`) | C-03 sale del sprint, y la regla «con la columna X.Y vacía en sus N filas» entra con T012 |
| Los pasos no reutilizaban el vocabulario existente | Los `.feature` usan «tiene la sesión iniciada con rol», «Cuando se envía GET» y «la API responde» de `acceso.feature` y `varias_secciones.feature` |
| Faltaban los Antecedentes | Base desechable con V1_01 a V1_10 y los dos scripts de datos, el segundo solo en bases desechables, y la API con R-2026-BORRADOR |
| El JSON propuesto traía `niveles` ambiguo, `pi_del_plan` distinto de `pi`, `Decimal` sin convertir y sin `conjunto_reglas_estado` | La forma de la ruta 12 usa `estudiantes_por_nivel`, `pi`, números JSON y los campos del conjunto de reglas de la constancia (FR-006) |
| El 403 de un identificador inexistente sigue como «(propuesta)» | La ruta 12 no recibe identificadores (J-23), y la prueba de las rutas registradas hereda la nota de BR-ACCESO-08 |
| Q15 no vigila una columna `nombre` en `acceso` | Queda anotado con C-13, que sale del sprint |
| La descripción del SO 2 de AMB-2026 termina en coma (`V1_03__cargar_referencia_ambiental.sql:138`) | Ningún escenario compara la descripción del SO, y el dato del catálogo en BORRADOR queda para su revisión |
| El humo de la vista previa admite una sola corrida por restablecimiento de `develop` | C-22 pasa a tareas con su estado inicial definido (T043 y T071) |
| El corte 2 edita en otra sesión las rutas de carga, `app/permisos.py` (suma `puede_reemplazar`) y `docs/01-arquitectura/frontend.md` del Front | La spec 004 no cambia `app/permisos.py`, documenta P6 en una sección propia de `frontend.md` y pide rebasar `feat/004-reportes-docente` sobre `develop` antes de integrar |

## Veredicto del crítico de arquitectura

| N.º | Decisión | Veredicto | Lo que adopta la spec |
| --- | --- | --- | --- |
| AD-01 | El reporte del profesor vive en el sistema y no en Power BI | SE_SOSTIENE | J-21. Power BI no sabe hoy quién es el profesor, porque `powerbi_lectura` no entra al esquema `acceso` y la tabla maestra trae PROFESOR nulo, y esa tabla expone además el código de cada estudiante. Las licencias siguen sin confirmar. Power BI queda para la coordinación en una spec aparte |
| AD-02 | Las cifras salen de `abet.v_r17_por_pi`, sin vista nueva | SE_SOSTIENE con condiciones | La vista se une solo por `carga_id`, y el SO, el PI y el instrumento salen del plan de la carga por `pi_id` y `so_id`, nunca por código suelto (FR-004 y FR-005). Ampliar la vista queda para después (J-26) |
| AD-03 | Los porcentajes viajan por la API con un decimal | SE_SOSTIENE con condiciones | J-22 y ADR-008. El Back convierte `Decimal` antes de responder y calcula `en_meta` con una función pura que comparte con `r17.py` (FR-007 y FR-008) |
| AD-04 | Una ruta por usuario con `seccion_id` opcional | CAMBIAR | J-23. `GET /api/resultados?periodo=2026-2` sin `seccion_id`, para que la ruta no reciba ningún identificador ajeno, y los PI del plan en la clave `pi`, como la ruta 4 |
| AD-05 | Sin consolidado ni cifra de SO mientras D-32 siga abierta | SE_SOSTIENE | D-32. Los PI se agrupan bajo su SO y P6 no repite el agregado de M24 a M26 del R-17 |
| AD-06 | Barras en HTML y Tailwind sin biblioteca de gráficos | SE_SOSTIENE con condiciones | J-24. El ancho va en `style`, porque Tailwind 4 no genera clases armadas en ejecución, cada fila lleva su texto completo y la barra lleva `aria-hidden` (FR-012) |
| AD-07 | La ruta usa `secciones_visibles()` sin SQL de alcance propio | SE_SOSTIENE con condiciones | J-25. Los routers con datos declaran la dependencia de sesión y una prueba recorre las rutas registradas (FR-003 y BR-ACCESO-10) |
| AD-08 | El periodo vigente por omisión y `periodo` admitido, sin selector en P6 | SE_SOSTIENE | FR-001 |
| AD-09 | El coordinador usa la misma ruta y la misma P6 | SE_SOSTIENE con condiciones | J-28. Orden por asignatura y sección, nunca por resultado, agrupación por asignatura y marca PROVISIONAL por sección (US-44) |
| AD-10 | La descripción del instrumento en `abet.asignatura_so` | CAMBIAR | J-27. Si C-12 entra, la descripción va en `abet.plan_medicion.descripcion_instrumento` (V1_11), por periodo y PI. Mientras D-34 siga abierta, queda fuera |
| AD-11 | P6 se abre desde P2 sin reemplazarla | SE_SOSTIENE con condiciones | El botón dice «Ver mis logros por SO» (propuesta), porque «Ver resultado» ya abre P4, y la vista de `App.tsx` se llama `logros` (FR-011) |
| AD-12 | Datos y exports ya versionados | SE_SOSTIENE con condiciones | Las pruebas de la ruta siembran con `publicar()` y `filas_inventadas()` de `tests/cargas_de_prueba.py`, y el humo compara P6 con el R-17 de la carga que ya existe en la vista previa (FR-019 y FR-021) |
| AD-13 | Sin migración en Neon | SE_SOSTIENE con condiciones | Antes de fusionar, una consulta de solo lectura desde el Windows de Jefferson comprueba los permisos de `abet_app` en la rama `develop` (FR-020, T020 y T021) |
| AD-14 | La respuesta no trae `subida_por`, códigos ni nombres | SE_SOSTIENE con condiciones | La ruta arma cada objeto campo por campo contra una lista cerrada, sin `nombre_archivo`, `sha256`, `trato_sin_evidencia` ni `pct_logro_segun_regla` (US-42 y FR-006) |

El crítico anota además que M24 a M26 del R-17 cuentan los niveles de todos los PI con un corte fijo y no con `nivel_esperado` (`abet_carga/r17.py:299-303`), y lo propone como un defecto que la spec 004 no corrige. Con R-PRUEBA-APROBADO (nivel esperado 2) estas celdas se apartan del bloque II, mientras que con R-2026-BORRADOR coinciden, porque su nivel esperado es 3. El 2026-11-18, una revisión de la plantilla descarta el defecto, ya que sus rótulos definen las tres celdas con el mismo corte fijo (K24 «Número de alumnos que obtuvieron 1 y 2» y K25 «Número de alumnos que obtuvieron 3 y 4»), y `plantillas/README.md` las documenta igual. Qué deben mostrar con otro nivel esperado lo deciden la Coordinación de Ambiental y la Oficina de Calidad (D-08), y la spec anota la regla en «Fuera de alcance» para la spec viva del R-17.

## Decisiones que salen de la revisión

- De la carrera, D-32 (resumen de un PI en varias secciones y de un SO en sus PI), D-33 (agregado del curso o de la carrera para el profesor) y D-34 (descripción del instrumento de medición), con su valor provisional en la spec. D-12 (nombre del profesor en el R-17) y D-30 (escala de las columnas ABET de 100 puntos) siguen abiertas con su dueño y su valor.
- De Jefferson, J-21 a J-28, con el valor que propone el crítico.
