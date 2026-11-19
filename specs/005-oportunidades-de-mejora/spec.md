# Feature Specification: Oportunidades de mejora en la carga, con semáforo, declaración y R-17 desde la base

**Feature Branch**: `docs/005-oportunidades-de-mejora` (PR a `develop`), con la implementación en `feat/005-oportunidades-de-mejora` del Back y del Front después de la aprobación
**Created**: 2026-11-18
**Status**: Aprobada por Jefferson en el chat el 2026-11-18 («Sí, apruébala»), con J-29 a J-37 en el valor que propone la spec
**Input**: «la descripción siempre viene de la base de datos» (Jefferson, 2026-11-18, con una captura del bloque I del R-17 de la 410). «esto no es?» y «a que tabla y atributo hace referencia entonces (?» (Jefferson, 2026-11-18, con una captura de la consola de Neon que muestra `abet.so` y su columna `descripcion`). «estos campos deben aparecer en la carga, pero como si fuera formulario. La base de datos debe guardarlos. Pero antes de hacerlo esa tabla que sale en el R17 (tercera imagen) tiene que salir hacia donde está la carga, se tiene que mostrar justo después de haber cargado para que le muestre como en forma de una figura estilo semáforo como va la sección del profesor y así mismo él declare lo que se le pregunta. Solo podrá obtener el R17 si es que el docente ha completado tmb esos dos campos. Si puedes mantener la persistencia de los datos que se escriben como borrador genial. También cuando se haga click atrás debería volver atrás (no salirse de la página).» (Jefferson, 2026-11-18, con tres capturas del R-17 y de P4)

## Épica

> **EP-05. Oportunidades de mejora en la carga (propuesta).** Después de subir el export, el profesor ve en la pantalla de resultado de la carga (P4) cómo va su sección en cada indicador de desempeño (performance indicator, PI), con la tabla de niveles del R-17 y un semáforo frente a la meta. En la misma pantalla declara, en un formulario, las causas y las acciones de los recuadros A y B del R-17, que la base guarda, también como borrador. El R-17 se descarga solo cuando la declaración está completa, y toma de la base esos dos textos y la descripción del instrumento de medición. Además, el botón atrás del navegador vuelve a la pantalla anterior de la aplicación en vez de salir de ella.

Convenciones de esta spec. Todos los datos son inventados y siguen las convenciones de las specs 001, 003 y 004. Las secciones de prueba son la 410 y la 411 de 450002 «Principios de Ingeniería Sostenible» en 2026-2, de `docente410@example.invalid` y `docente411@example.invalid`, y la 412 de 450002 y la 410 y la 412 de 450010 «Gestión Sostenible de Residuos», de `docente.varias@example.invalid`, que existe solo en las bases desechables de las pruebas. El plan de 450002 mide 5.1, 5.2 y 5.3 del SO 5 con el instrumento «Trabajo Integrador», y 22 asignaturas usan ese instrumento en `abet.asignatura_so`. El export correcto de la 410 es `tests/datos_inventados/sintetico_20262_450002_410.xlsx` (también su `.csv`), con códigos 99000001 a 99000011. Ningún export nuevo entra a `tests/datos_inventados/`, y las copias con celdas vacías se arman en `tmp_path` con `REGLAS_DE_COPIA`. Todo lo que ninguna fuente fija va marcado «(propuesta)».

Prefijos e identificadores. La épica lleva el prefijo EP y continúa la numeración de las specs 001 a 004 (EP-05). Las historias US continúan desde US-45, porque la spec 004 usa US-37 a US-44. Las decisiones de la carrera siguen desde D-35 (D-34 de la spec 004 sigue abierta) y las de Jefferson desde J-29. Las rutas nuevas son la 13 a la 16 del contrato del Front, y la spec no agrega pantalla, porque cambia P4. Las migraciones son V1_11 (descripción del instrumento) y V1_12 (borrador y declaración), separadas porque la 11 no depende de la spec 004. La spec 002 de la rama `docs/002-capstone` nombra una V1_10 propia que ya choca con la V1_10 de `develop` (spec 003), y tendrá que renumerarse cuando entre. V1_11 y V1_12 quedan reservadas en la memoria de las dos sesiones. Los requisitos funcionales FR (functional requirement), los criterios de éxito SC (success criterion) y las tareas T se numeran dentro de esta spec, así que una regla viva que cite uno de ellos nombra la spec, como «FR-005 de la spec 005». Las candidatas de la auditoría se llaman C-01 a C-15, y las decisiones técnicas del crítico, AD-01 a AD-30. Su revisión está en `revision-historias.md`. N# es una fila de `Requisitos_Sistema_Medicion.xlsx`, en la carpeta `ABET_SIS_MED`, fuera de los repositorios.

Siglas y términos. Las de las specs 001, 003 y 004 valen aquí. El resultado del estudiante (student outcome, SO), el PI y la interfaz de programación de aplicaciones (application programming interface, API) conservan el sentido de la spec 004. Lo mismo vale para el registro de decisión de arquitectura (architecture decision record, ADR), las pautas de accesibilidad para el contenido web (Web Content Accessibility Guidelines, WCAG) y el lenguaje de consultas estructurado (Structured Query Language, SQL). JSON es la notación de objetos de JavaScript (JavaScript Object Notation), NFC es la forma canónica compuesta de Unicode (Normalization Form C) y la dirección es el localizador uniforme de recursos (Uniform Resource Locator, URL). La meta es `meta_pct`, la meta de logro del conjunto de reglas de la carga. El corte rojo es el parámetro CORTE_ROJO de ese conjunto, que fija desde dónde empieza la banda ámbar. El semáforo de un PI es uno de VERDE, AMBAR, ROJO o SIN_DATO, y lo calcula el Back. La declaración es el par de textos de causas y acciones que el profesor guarda con «Guardar declaración», y el borrador es lo que escribe antes de declarar. Los recuadros A y B son B28 con B29:I31 y B33 con B34:I36 del R-17. P4 es la pantalla «Resultado de la carga».

Cifras de prueba, recalculadas por la lente de verificabilidad desde `NIVELES_410` de `scripts/generar_exports_inventados.py`. R-2026-BORRADOR tiene nivel esperado 3, meta 80,0 % y CORTE_ROJO PENDIENTE. R-PRUEBA-SEMAFORO es un conjunto de prueba nuevo, APROBADO y completo, con META_LOGRO 0,80, NIVEL_ESPERADO 3 y CORTE_ROJO 0,75, que arma un ayudante parametrizado de `tests/cargas_de_prueba.py` (hoy `conjunto_aprobado` fija 0,70, 2 y 0,50). Los niveles de 5.3 por fila de la 410 son 2 = 3, 3 = 4, 4 = 3, 5 = 3, 6 = 2, 7 = 4, 8 = 3, 9 = 1, 10 = 4, 11 = 3 y 12 = 2.

| Sección y copia | Conjunto de reglas | Estudiantes por nivel | Logro sobre calificados | Semáforo |
| --- | --- | --- | --- | --- |
| 410 de 450002, export correcto | R-2026-BORRADOR | 5.1 [1, 3, 4, 3], 5.2 [1, 3, 4, 3], 5.3 [1, 2, 5, 3] | 63,6 % (7 de 11), 63,6 % (7 de 11) y 72,7 % (8 de 11) | ROJO en los tres |
| 410 de 450002, export correcto | R-PRUEBA-SEMAFORO | Los mismos | Los mismos | 5.3 ROJO con 72,7 % |
| 412 de 450002, de `docente.varias` | R-2026-BORRADOR | No cambian | 81,8 %, 54,5 % y 90,9 % | VERDE, ROJO y VERDE |
| 410 con 5.3 vacía en la fila 9 | R-2026-BORRADOR | 5.3 [0, 2, 5, 3], 8 de 10, 1 sin evidencia | 80,0 % (72,7 % sobre el total) | VERDE, frontera de la meta |
| 410 con 5.3 vacía en las filas 2 y 6 | R-2026-BORRADOR | 5.3 [1, 1, 4, 3], 7 de 9, 2 sin evidencia | 77,8 % (63,6 % sobre el total) | ROJO |
| 410 con 5.3 vacía en las filas 2 y 6 | R-PRUEBA-SEMAFORO | Los mismos | 77,8 % | AMBAR |
| 410 con 5.3 vacía en las filas 2, 3 y 9 | R-PRUEBA-SEMAFORO | 5.3 [0, 2, 4, 2], 6 de 8, 3 sin evidencia | 75,0 % (54,5 % sobre el total) | AMBAR, frontera del corte |
| 410 con 5.3 sin ninguna nota | R-2026-BORRADOR | 5.3 sin calificados | `pct_sobre_calificados` nulo y `pct_sobre_total` 0,0 | SIN_DATO |

Las demás secciones de `docente.varias@example.invalid` dan 72,7 %, 45,5 % y 36,4 % en 2.1, 2.2 y 5.1 de la 410 de 450010, y 90,9 %, 63,6 % y 54,5 % en la 412 de 450010. La 411 tiene los niveles de la 410 en orden inverso y los mismos porcentajes. Con R-2026-BORRADOR el corte rojo está PENDIENTE, así que el piloto muestra VERDE, ROJO o SIN_DATO, y AMBAR aparece solo con un conjunto que lo defina.

Los escenarios viven en `specs/005-oportunidades-de-mejora/aceptacion/`, en español (`# language: es`), en cuatro archivos. `semaforo.feature` agrupa US-45 y US-46, `declaracion.feature` agrupa US-47, US-48, US-49, US-53 y US-54, `r17_desde_la_base.feature` agrupa US-50 y US-51, y `navegacion.feature` contiene US-52. Sus pasos van en `tests/aceptacion/pasos/` (propuesta). Cada escenario lleva `@US-NN`, `@spec005` y `@corte1`, y los de pantalla llevan además `@delegado_a_vitest`, sin «(Vitest)» en el título, porque los prueba Vitest en el Front. Cuando un texto literal de pantalla o de la API difiere, manda el del `.feature`.

## Clarifications

### Session 2026-11-18

- Jefferson pide en el chat, con las palabras del Input y con cinco capturas, que la descripción del instrumento del R-17 salga de la base y que la tabla de niveles del R-17 aparezca en la pantalla de la carga como un semáforo. Pide también que el profesor declare en un formulario las causas y las acciones de los recuadros A y B y que la base las guarde, también como borrador. Pide además que el R-17 salga solo con esos dos campos completos y que el botón atrás vuelva a la pantalla anterior.
- Primera pregunta de Jefferson, «esto no es?», con una captura de la consola de Neon que muestra `abet.so` y su columna `descripcion`. La respuesta es que esa columna es la descripción del SO, y que la columna vacía del bloque I del R-17 (G17:I19, «Descripción del instrumento de medición») pide la descripción del instrumento de cada PI, que es otro dato.
- Segunda pregunta de Jefferson, «a que tabla y atributo hace referencia entonces (?». La respuesta es que hoy a ninguna. Los únicos campos de descripción del esquema `abet` son `so.descripcion` (varchar 400), `pi.descripcion` (varchar 300), `rubrica_nivel.descriptor` (varchar 800) y `parametro.descripcion` (varchar 300), y `abet.instrumento` solo trae `nombre` (varchar 60). La propuesta es `abet.plan_medicion.descripcion_instrumento` (US-51 y J-31), que cierra J-27 de la spec 004.
- `develop` (Back 13c0c12 y Front e88d6f2) ya trae P4 con el estado, los conteos, los rechazos, los avisos, la constancia y el enlace «Descargar R-17». No trae cifras por carga, no guarda ningún texto del profesor, deja vacíos G17:I19, B29:I31 y B34:I36 del R-17, y `src/App.tsx` cambia de pantalla con `useState`, sin historial ni dirección, así que el botón atrás sale de la aplicación.
- La spec 004 (aprobada el 2026-11-18, en construcción en `feat/004-reportes-docente`) agrega la ruta 12, P6, la función de la meta en `abet_carga/resultados.py` y la regla «P2 y P4 siguen sin mostrar porcentajes» (FR-016). La spec 005 depende de ella y cambia esa regla para P4 (J-35), y su implementación sale de `develop` después de fusionar la spec 004.
- La auditoría (necesidad, solapamiento, verificabilidad y crítico de arquitectura) reduce 15 candidatas a 10 historias, y deja la descripción del SO en B15 (C-08), quién declaró en la «Constancia» (C-12) y la marca «Declaración pendiente» en P2 y P5 para después (`revision-historias.md`).
- Del requisito N6, «Al subir el archivo, el docente recibe al instante un reporte de su sección», la spec cubre el reporte inmediato de cifras y semáforo. N11, N12 y N13 quedan fuera, porque A y B son texto libre, como en el R-17.

## User Scenarios & Testing *(mandatory)*

### US-45: Las cifras del semáforo de una carga (Priority: P1)

Como profesor, quiero que el sistema entregue para mi carga publicada los conteos por nivel de cada PI, su logro frente a la meta y el color del semáforo, con las mismas cifras de mi R-17, para ver cómo va mi sección sin abrir el archivo.

**Why this priority**: N6 pide «Al subir el archivo, el docente recibe al instante un reporte de su sección», y ninguna ruta entrega hoy cifras por carga. La constancia no las trae y la ruta 12 es de P6.

**Independent Test**: con la carga PUBLICADA del export correcto de la 410 y R-2026-BORRADOR, `GET /api/cargas/{carga_id}/indicadores` responde 200 con 3 indicadores, 63.6, 63.6 y 72.7 y `semaforo` ROJO en los tres, mientras en `develop` 13c0c12 esa ruta no existe.

**Base**: `abet.v_r17_por_pi` por `carga_id`; `abet.carga` (`estado`, `conjunto_reglas_id`); `abet.parametro_valor` (CORTE_ROJO, que `abet_app` ya lee); el armado del indicador y la función de la meta de la spec 004 (`abet_carga/resultados.py`, T031 de esa spec); la función del semáforo (nueva, en el mismo módulo, propuesta); ruta 13 `GET /api/cargas/{carga_id}/indicadores` (nueva, propuesta); sin migración.
**Pantalla**: ninguna, porque la ruta alimenta a P4 (US-46).

La respuesta (propuesta) trae `carga_id`, `estado`, `provisional`, `conjunto_reglas`, `conjunto_reglas_estado`, `parametros_pendientes`, `meta_pct`, `corte_rojo_pct` (nulo si CORTE_ROJO está PENDIENTE) e `indicadores`, cada uno con las claves de FR-006 de la spec 004 más `semaforo`. Los indicadores van por `so_numero` y `pi.numero`, en una sola instantánea y con `Cache-Control: no-store`.

La regla del semáforo (J-29) es la siguiente. Es SIN_DATO si falta el logro o la meta. Es VERDE si `en_meta` es verdadero. Es AMBAR si CORTE_ROJO está DEFINIDO y el logro es mayor o igual que el corte y menor que la meta. Es ROJO en los demás casos. Así VERDE coincide siempre con «En la meta» de P6 y con el texto «¡Felicidades! …» de H24:H26 del R-17, y ROJO o AMBAR con «El indicador aún no alcanza …».

**Acceptance Scenarios** (`specs/005-oportunidades-de-mejora/aceptacion/semaforo.feature`):

1. **La 410 publicada con R-2026-BORRADOR da tres PI en rojo.** **Dado** la carga PUBLICADA del export correcto de la 410 de 450002 de `docente410@example.invalid`, **Cuando** `docente410@example.invalid` pide la ruta 13, **Entonces** recibe 200 con `meta_pct` 80.0 y `corte_rojo_pct` null. Los tres PI traen sus niveles, sus logrados y sus calificados, con 63.6, 63.6 y 72.7, y `semaforo` ROJO.
2. **La 412 de 450002 da verde, rojo y verde.** **Dado** la carga PUBLICADA de la 412 de 450002 de `docente.varias@example.invalid`, **Cuando** pide la ruta 13, **Entonces** recibe VERDE, ROJO y VERDE, con `en_meta` verdadero en los dos VERDE.
3. **La frontera de la meta es verde.** **Dado** la copia de la 410 con la columna 5.3 vacía en la fila 9, **Cuando** su profesor pide la ruta 13, **Entonces** 5.3 trae 80.0 sobre calificados, 72.7 sobre el total y `semaforo` VERDE.
4. **Con el corte rojo definido aparece la banda ámbar.** **Dado** R-PRUEBA-SEMAFORO, **Cuando** se piden las tres cargas, **Entonces** la copia de 5.3 vacía en las filas 2 y 6 trae 77.8 y AMBAR. La de las filas 2, 3 y 9 trae 75.0 y AMBAR, la 410 original trae 72.7 y ROJO, y `corte_rojo_pct` es 75.0.
5. **Con el corte rojo pendiente no hay ámbar.** **Dado** la copia de 5.3 vacía en las filas 2 y 6 con R-2026-BORRADOR, **Cuando** el profesor pide la ruta 13, **Entonces** 5.3 trae `semaforo` ROJO, porque CORTE_ROJO está PENDIENTE.
6. **Un PI sin calificaciones no se pinta.** **Dado** la copia de la 410 con la columna 5.3 sin ninguna nota, **Cuando** el profesor pide la ruta 13, **Entonces** 5.3 trae `pct_sobre_calificados` null, `pct_sobre_total` 0.0 y `semaforo` SIN_DATO, nunca ROJO.
7. **Una regla sin definir no produce un 500.** **Dado** un conjunto de reglas de prueba con NIVEL_ESPERADO o META_LOGRO sin DEFINIR, **Cuando** el profesor pide la ruta 13, **Entonces** la ruta responde 200 y cada indicador trae SIN_DATO.
8. **Las cifras coinciden con el R-17 de la misma carga.** **Dado** una carga PUBLICADA y su R-17 con la declaración hecha, **Cuando** se comparan, **Entonces** cada logro es round(100 × E, 1) de su fila del bloque II y la meta es round(100 × G, 1). Los niveles son los de L a O de K29:Q31, «7 de 11» es el de P y el porcentaje sobre el total es round(100 × Q, 1). Además, el semáforo VERDE va con el texto «¡Felicidades! …» de H, y el ROJO o el AMBAR con «El indicador aún no alcanza …». La prueba usa la 410 (ROJO), la 412 de 450002 (VERDE y ROJO) y la copia sin notas en 5.3 (SIN_DATO y H vacía).
9. **El alcance es el de la constancia.** **Dado** la carga de la 410, **Cuando** se pide la ruta 13 sin sesión, con `docente411@example.invalid`, con un `carga_id` que no existe y con `coordinacion@example.invalid`, **Entonces** recibe 401, 403 «La sección no está a su cargo.», el mismo 403 y 200, en ese orden.
10. **Solo una carga publicada tiene semáforo.** **Dado** una carga RECHAZADA o REEMPLAZADA, **Cuando** se pide la ruta 13, **Entonces** responde 409 «La carga no está publicada y no tiene semáforo.» (propuesta).

---

### US-46: Ver el semáforo en P4 al terminar la carga (Priority: P1)

Como profesor, quiero ver en P4, justo después de subir el export, la tabla de niveles de cada PI de mi sección con un semáforo frente a la meta, para saber cómo va mi sección sin abrir el R-17.

**Why this priority**: es el núcleo del pedido de Jefferson («esa tabla que sale en el R17 […] se tiene que mostrar justo después de haber cargado»). Hoy `docs/01-arquitectura/frontend.md` dice que P4 no muestra los porcentajes del R-17.

**Independent Test**: con la respuesta del escenario 1 de US-45, P4 de la 410 muestra tres filas con «7 de 11», «63,6 %» y «Debajo de la meta» en 5.1 y 5.2, y «8 de 11», «72,7 %» y «Debajo de la meta» en 5.3, mientras P4 de `develop` e88d6f2 no muestra ninguna cifra.

**Base**: ruta 13 (US-45); sin tablas nuevas.
**Pantalla**: P4, sección «Cómo va su sección» (propuesta), después de los rechazos y los avisos y antes del formulario de US-47, solo en una carga PUBLICADA. Las columnas son «PI», «Nivel 1» a «Nivel 4», «Logran / calificados» y «% sobre el total» (las del R-17), más «Logro», «Meta» y «Estado». Cada estado tiene una luz de color con `aria-hidden` y su texto, que es «En la meta» (VERDE), «Cerca de la meta» (AMBAR), «Debajo de la meta» (ROJO) y «Sin calificaciones (N sin evidencia)», «Sin meta definida» o «Sin nivel esperado definido» (SIN_DATO), todos propuestas. El Front no compara cifras.

**Acceptance Scenarios** (`specs/005-oportunidades-de-mejora/aceptacion/semaforo.feature`, todos `@delegado_a_vitest`):

1. **P4 muestra la tabla y el semáforo con texto.** **Dado** la respuesta del escenario 1 de US-45, **Cuando** `docente410@example.invalid` abre P4 de esa carga, **Entonces** ve tres filas. Las de 5.1 y 5.2 traen «7 de 11», «63,6 %» y «Debajo de la meta», la de 5.3 trae «8 de 11», «72,7 %» y «Debajo de la meta», y cada luz lleva `aria-hidden`.
2. **La leyenda sale de la respuesta.** **Dado** una respuesta con `corte_rojo_pct` null, **Cuando** P4 la muestra, **Entonces** la leyenda dice «Verde, el logro alcanza la meta de 80 %. Rojo, todavía no la alcanza.» (propuesta). **Dado** una con 75.0, **Entonces** dice «Verde, desde la meta de 80 %. Ámbar, desde 75 % hasta debajo de la meta. Rojo, debajo de 75 %.» (propuesta).
3. **Lo provisional se ve.** **Dado** una respuesta con `provisional` verdadero, **Cuando** P4 la muestra, **Entonces** aparece sobre la tabla la franja de la constancia y del R-17 con el texto de su conjunto de reglas, y no aparece nada cuando es falso.
4. **Un PI sin calificaciones no se pinta de rojo ni de cero.** **Dado** un PI SIN_DATO con 11 sin evidencia, **Cuando** P4 lo muestra, **Entonces** dice «Sin calificaciones (11 sin evidencia)» y nunca «0 %» ni una luz roja.
5. **Una carga rechazada o reemplazada no pide el semáforo.** **Dado** P4 de una carga RECHAZADA o REEMPLAZADA, **Cuando** se abre, **Entonces** no pide la ruta 13 ni muestra la sección.
6. **Un Back anterior no rompe P4.** **Dado** que la ruta 13 responde 404 (Back anterior a la spec 005), **Cuando** se abre P4, **Entonces** se comporta como hoy, sin semáforo ni formulario y con el enlace «Descargar R-17» (AD-28, propuesta).

La spec cambia FR-016 de la spec 004, el invariante 8 de ADR-008, la línea de P4 de `docs/01-arquitectura/frontend.md` («No muestra […] los porcentajes del R-17») y las pruebas de P4 sin porcentajes (J-35).

---

### US-47: Declarar las causas y las acciones en P4 (Priority: P1)

Como profesor, quiero completar en un formulario de P4 los recuadros A y B del R-17, con sus mismos enunciados, para dejar registradas en la base las causas de mi resultado y las acciones para mejorarlo.

**Why this priority**: es el pedido literal de Jefferson («estos campos deben aparecer en la carga, pero como si fuera formulario. La base de datos debe guardarlos»). N11 y N12 dan el contexto, aunque A y B, como texto libre, no cumplen N12.

**Independent Test**: con la 410 publicada, `docente410@example.invalid` guarda el borrador con los dos textos y declara la versión 1, y `GET /api/cargas/{carga_id}/mejora` devuelve la declaración con los mismos textos, mientras en `develop` ninguna de las rutas 14 a 16 existe.

**Base** (J-30): V1_12 crea `abet.mejora_borrador` (una fila por carga, `carga_id` clave primaria y FK a `abet.carga`, `causas` y `acciones` varchar(2000) nulos, `version` integer, `actualizado_en`, `actualizado_por` FK a `acceso.usuario_autorizado`) y `abet.mejora_declaracion` (solo INSERT, `declaracion_id`, `carga_id`, `causas` y `acciones` varchar(2000) no nulos y no en blanco, `version_borrador`, `declarada_en`, `declarada_por`). La declaración vigente de una carga es la última. Los nombres de las tablas, las columnas y las restricciones son propuestas. `crear_rol_app.sql` da a `abet_app` INSERT y UPDATE (columnas exactas) en el borrador e INSERT en la declaración, y actualiza sus listas exactas de comprobación.
**Pantalla**: P4, formulario «Análisis del resultado» (propuesta) con los dos enunciados literales de la plantilla, «A. Identifique las causas principales que pudieron influir en no alcanzar el indicador (por ejemplo: planificación, participación, recursos, tiempos, entre otros).» de B28 sobre las causas y «B. Proponga acciones concretas que permitan superar las causas identificadas y/o mejorar el resultado del indicador» de B33 sobre las acciones, la nota de US-53, el estado del guardado de US-48 y el botón «Guardar declaración» (propuesta). Después de declarar, P4 muestra los dos textos declarados con «Declarado el 18/11/2026 15:10» (propuesta), y el formulario sigue disponible para corregir.

Las rutas (propuestas) son tres. La ruta 14, `GET /api/cargas/{carga_id}/mejora`, responde `declaracion` (causas, acciones, declarada_en) o null, `borrador` (causas, acciones, version, actualizado_en) o null, `borrador_pendiente` (hay un borrador posterior a la última declaración), `heredado_de` (US-54) y `puede_editar`. La ruta 15 es `PUT /api/cargas/{carga_id}/mejora/borrador` con `{causas, acciones, version}`, y responde 200 con `version` y `actualizado_en`. La ruta 16 es `POST /api/cargas/{carga_id}/mejora/declaracion` con `{version}`, que declara esa versión exacta del borrador y responde 201 con `declarada_en`. Una versión de la ruta 16 distinta de la del borrador guardado responde 409 «El borrador cambió después de este guardado. Guarde otra vez antes de declarar.» (propuesta) con el `borrador`, y `version` 0 sin ningún borrador responde el 422 de la declaración incompleta. En las dos rutas, una carga que no está PUBLICADA responde 409 «La carga no está publicada y no admite causas ni acciones.» (propuesta), que manda sobre el 409 de la versión. Escribe solo el profesor asignado, con una función propia `puede_declarar()` de `app/permisos.py` (J-33 y AD-09). El coordinador lee con `puede_leer()` y nunca recibe el texto del borrador. Las respuestas siguen el orden 401, 403, 422 y 409, con el cuerpo leído a mano después del alcance y JSON obligatorio (AD-23). Las tres rutas entran en la prueba que recorre las rutas registradas (FR-003 y T030 de la spec 004).

El Back normaliza el texto a NFC, cambia `\r\n` por `\n`, rechaza los caracteres de control salvo `\n` y `\t` y cuenta puntos de código, hasta 2000 por campo (AD-10). El Front cuenta igual y no usa `maxLength`.

**Acceptance Scenarios** (`specs/005-oportunidades-de-mejora/aceptacion/declaracion.feature`):

1. **El profesor guarda y declara.** **Dado** la carga PUBLICADA de la 410 sin texto, **Cuando** `docente410@example.invalid` guarda el borrador con los dos textos (`version` 0 a 1) y declara la versión 1, **Entonces** recibe 201 con `declarada_en`, y GET devuelve la declaración con los mismos textos y `borrador_pendiente` falso.
2. **Una carga sin texto responde vacía.** **Dado** una carga sin texto, **Cuando** su profesor pide la ruta 14, **Entonces** recibe 200 con `declaracion` null, `borrador` null y `puede_editar` verdadero.
3. **Una declaración incompleta no se acepta.** **Dado** un borrador con causas o acciones vacías o de solo espacios, **Cuando** el profesor declara, **Entonces** recibe 422 «Complete las causas y las acciones.» (propuesta), y no se crea ninguna declaración.
4. **El texto tiene un largo y un contenido válidos.** **Dado** un campo de 2001 puntos de código, **Cuando** el profesor lo guarda, **Entonces** recibe 422 «Cada campo admite hasta 2000 caracteres.» (propuesta). **Dado** un carácter de control (U+0007), **Entonces** recibe 422 «El texto trae caracteres que no se pueden guardar.» (propuesta), y en ambos casos nada cambia.
5. **Solo el profesor de la sección escribe.** **Dado** la carga de la 410, **Cuando** `coordinacion@example.invalid` o `docente411@example.invalid` envía el PUT o el POST, aunque el cuerpo no sea JSON, **Entonces** recibe 403 «La sección no está a su cargo.» y nada cambia.
6. **Una carga que no está publicada no recibe declaración.** **Dado** una carga RECHAZADA o REEMPLAZADA, **Cuando** su profesor envía el PUT o el POST, **Entonces** recibe 409 «La carga no está publicada y no admite causas ni acciones.» (propuesta), y la respuesta de una REEMPLAZADA trae `reemplazada_por` (AD-27).
7. **Corregir una declaración conserva la anterior hasta declarar (D-37).** **Dado** la 410 declarada, **Cuando** `docente410@example.invalid` guarda otro borrador, **Entonces** la declaración anterior sigue vigente y el R-17 sigue saliendo con ella, y `borrador_pendiente` es verdadero. **Cuando** declara la versión nueva, **Entonces** el R-17 toma el texto nuevo y la declaración anterior queda en `abet.mejora_declaracion`.
8. **El coordinador lee la declaración sin editarla.** **Dado** la 410 declarada, **Cuando** `coordinacion@example.invalid` pide la ruta 14, **Entonces** GET responde `borrador` null y `puede_editar` falso. P4 del coordinador muestra los textos declarados sin campos ni botón (`@delegado_a_vitest`), y con solo un borrador dice «El profesor todavía no declara las causas y las acciones.» (propuesta), sin texto.
9. **P4 del profesor muestra los enunciados y el botón.** **Dado** P4 de la 410 publicada, **Cuando** `docente410@example.invalid` la abre, **Entonces** ve los enunciados de B28 y B33 sobre cada campo y el botón «Guardar declaración» deshabilitado mientras falte un campo, y después de declarar ve «Declarado el …» (`@delegado_a_vitest`).

---

### US-48: El borrador se guarda solo y no se pierde (Priority: P2)

Como profesor, quiero que lo que escribo en A y B se guarde en la base como borrador mientras escribo, para retomarlo si recargo, cierro la pestaña o vuelvo desde otro equipo.

**Why this priority**: Jefferson lo pide de forma condicional («Si puedes mantener la persistencia de los datos que se escriben como borrador genial»), y `develop` no guarda nada de la sesión en el navegador por regla, así que la base es el único lugar posible.

**Base y rutas**: la ruta 15 con `version`. Un PUT con una versión que no es la guardada responde 409 «Otra pestaña guardó un texto más reciente.» (propuesta) con el texto guardado y su versión, y P4 ofrece elegir cuál conservar (AD-19).
**Pantalla**: P4. El Front (J-30, propuesta) guarda 2,5 s después de la última tecla, con un máximo de 15 s mientras se escribe sin pausa, al salir del campo y en `pagehide` con `keepalive`, con un solo PUT en vuelo y nunca en `localStorage` ni en `sessionStorage`. Muestra «Guardando…», «Borrador guardado a las 15:10» o «No se pudo guardar el borrador. Su texto sigue en pantalla.» (propuestas). Un 401 durante el guardado no desmonta P4. P4 queda oculta bajo el ingreso con el texto en memoria y, si vuelve a ingresar el mismo usuario, reintenta con la misma versión (AD-22). Con otro usuario, o después de «Salir», el texto se descarta.

**Acceptance Scenarios** (`specs/005-oportunidades-de-mejora/aceptacion/declaracion.feature`):

1. **Un borrador parcial se acepta.** **Dado** la carga de la 410 sin texto, **Cuando** su profesor envía el PUT con solo causas y `version` 0, **Entonces** recibe 200 con `version` 1, y GET devuelve esas causas y `acciones` null.
2. **Dos pestañas no se pisan.** **Dado** el borrador en la versión 3, **Cuando** llega un PUT con `version` 2, **Entonces** responde 409 con el texto y la versión 3, y el borrador no cambia.
3. **El borrador vuelve al abrir P4** (`@delegado_a_vitest`). **Dado** un borrador guardado de la 410, **Cuando** el profesor abre P4 de esa carga, **Entonces** los dos campos traen el borrador.
4. **El guardado es automático** (`@delegado_a_vitest`). **Dado** P4 de la 410 publicada, **Cuando** el profesor escribe en A y pasan 2,5 s, **Entonces** sale un PUT y P4 dice «Borrador guardado a las …». **Cuando** sale del campo, **Entonces** sale otro PUT sin esperar.
5. **Una falla del guardado no borra el texto** (`@delegado_a_vitest`). **Dado** el PUT en 500, **Cuando** el profesor escribe, **Entonces** P4 dice «No se pudo guardar el borrador. Su texto sigue en pantalla.» y conserva lo escrito.
6. **Un 401 durante el guardado no pierde el texto** (`@delegado_a_vitest`). **Dado** un 401 en el guardado, **Cuando** P4 lo recibe, **Entonces** muestra el ingreso sin perder el texto, y tras ingresar el mismo usuario el guardado se reintenta.
7. **El navegador no guarda nada** (`@delegado_a_vitest`). **Cuando** el profesor escribe en P4, **Entonces** `localStorage` y `sessionStorage` quedan con 0 entradas.

---

### US-49: El R-17 solo con la declaración (Priority: P1)

Como coordinación, quiero que el R-17 de una carga se entregue solo cuando su profesor declaró las causas y las acciones, para que ningún R-17 llegue a la acreditación con los recuadros A y B vacíos.

**Why this priority**: es un pedido literal («Solo podrá obtener el R17 si es que el docente ha completado tmb esos dos campos»), y cambia US-15 de la spec 001 y la prueba de humo de US-17.

**Independent Test**: con la 410 publicada, la ruta 7 responde 409 «Complete las causas y las acciones en la página de la carga antes de descargar el R-17.» sin declaración, y 200 con `R017_450002_410_2026-2_PROVISIONAL.xlsx` con ella, mientras en `develop` 13c0c12 el R-17 sale siempre.

**Base**: `abet.mejora_declaracion` leída en la misma transacción `READ ONLY` y `REPEATABLE READ` de `r17.generar()` (AD-07). Una subclase nueva de `R17NoDisponible`, `DeclaracionPendiente` (propuesta), con 409 «Complete las causas y las acciones en la página de la carga antes de descargar el R-17.» (propuesta). El 409 de una carga no PUBLICADA manda sobre el de la declaración. El comando `python -m abet_carga r17` la captura (hoy solo captura `CargaNoPublicada`, `abet_carga/__main__.py:170`). La regla vale también para el coordinador (J-33). Toda carga publicada antes de V1_12, como la 410 y la 411 de la vista previa y de Production, queda en 409 hasta declarar, sin excepción por fecha (J-37).
**Pantalla**: P4, único lugar que ofrece el R-17 (J-32, propuesta). Sin declaración, P4 muestra «Descargar R-17» deshabilitado con «El R-17 se habilita cuando complete y guarde las causas y las acciones.» para el profesor y «El R-17 se habilita cuando el profesor de la sección declare las causas y las acciones.» para el coordinador (propuestas). P2 y P5 cambian «Descargar R-17» por un enlace a P4, y P6 de la spec 004 cambia su enlace al R-17 (FR-015 de esa spec) por «Ver la carga de la sección N de A» (propuesta), de modo que ningún enlace abre un 409 en JSON.

**Acceptance Scenarios** (`specs/005-oportunidades-de-mejora/aceptacion/declaracion.feature`):

1. **Sin declaración no hay R-17.** **Dado** la carga PUBLICADA de la 410 sin declaración, o con solo un borrador, **Cuando** su profesor pide la ruta 7, **Entonces** responde 409 con ese texto y ningún archivo.
2. **Con la declaración el R-17 sale.** **Dado** la misma carga con la declaración, **Cuando** pide la ruta 7, **Entonces** responde 200 con `R017_450002_410_2026-2_PROVISIONAL.xlsx`.
3. **La regla vale para el coordinador.** **Dado** la 410 sin declaración, **Cuando** `coordinacion@example.invalid` pide la ruta 7, **Entonces** recibe el mismo 409, y con la declaración recibe 200.
4. **El 409 de no publicada manda.** **Dado** una carga RECHAZADA sin declaración, **Cuando** se pide la ruta 7, **Entonces** responde «La carga no está publicada y no tiene R-17.», el 409 de siempre.
5. **El comando sigue la misma regla.** **Dado** una carga sin declaración, **Cuando** corre `python -m abet_carga r17`, **Entonces** termina con el mismo mensaje y sin escribir ningún archivo.
6. **Los enlaces llevan a P4** (`@delegado_a_vitest`). **Dado** P4 sin declaración, **Cuando** el profesor la abre, **Entonces** ve el botón deshabilitado y el texto del profesor, y después de declarar ve el enlace. P2 del coordinador y P5 no ofrecen «Descargar R-17» y llevan a P4.

La historia cambia los escenarios 1 a 4 de US-15 y la prueba de humo de US-17, que ahora declaran antes de descargar, y las 26 llamadas de prueba que generan un R-17 (ayudante `declarar()` de `tests/cargas_de_prueba.py`).

---

### US-50: El R-17 lleva las causas y las acciones desde la base (Priority: P1)

Como coordinación, quiero que el R-17 escriba en B29:I31 y B34:I36 el texto declarado que guarda la base, para que el reporte y la base digan lo mismo.

**Why this priority**: hoy `plantillas/README.md` documenta esos recuadros como «vacío y editable (BR-R17-04)», y Jefferson pide que la base los guarde y que el R-17 salga con ellos.

**Independent Test**: con la declaración de la 410 (causas «La entrega coincidió con la semana de parciales.» y acciones «Mover la entrega a la semana 10 y revisar el avance en clase.»), B29 y B34 del R-17 traen esos textos como cadenas, mientras en `develop` 13c0c12 ambos recuadros salen vacíos.

**Base**: la última fila de `abet.mejora_declaracion` de la carga. `r17.py` escribe las causas en B29 y las acciones en B34 con ajuste de texto y alineación arriba, y calcula de forma determinista el alto de las filas 31 y 36 por líneas, con un ancho conservador del rango combinado (B a I mide 208,6 unidades), sin tocar las filas 29, 30, 34 y 35. Las filas 29 a 31 llevan también la tabla K28:Q31. Cambia BR-R17-04 («vacíos y editables» pasa a «desde la base») y, por ADR-009 del Front (propuesta), el invariante 2 de ADR-005 («Ninguna celda del libro empieza por "="» pasa a «Ninguna celda del libro es una fórmula») y su frase «El profesor escribe a mano las causas, las acciones y el comentario.». El recuadro de comentario de BR-R17-04 se cierra, porque la hoja no lo tiene.
**Pantalla**: ninguna, porque el cambio vive en el archivo R-17.

**Acceptance Scenarios** (`specs/005-oportunidades-de-mejora/aceptacion/r17_desde_la_base.feature`):

1. **Los recuadros traen el texto declarado.** **Dado** la declaración de la 410 con causas «La entrega coincidió con la semana de parciales.» y acciones «Mover la entrega a la semana 10 y revisar el avance en clase.», **Cuando** se genera su R-17, **Entonces** B29 y B34 traen esos textos como cadenas.
2. **Un texto largo se lee completo.** **Dado** causas de 2000 caracteres, **Cuando** se genera el R-17, **Entonces** B29 tiene ajuste de texto, el alto de la fila 31 crece hasta mostrar el texto completo según el cálculo de `r17.py`, y K31:Q31 conserva sus valores.
3. **Un texto con aspecto de fórmula queda como texto.** **Dado** un texto que empieza con «=SUMA(1;2)», **Cuando** se genera el R-17, **Entonces** queda como cadena y ninguna celda del libro es fórmula.
4. **La declaración corregida manda.** **Dado** la declaración corregida del escenario 7 de US-47, **Cuando** se genera el R-17, **Entonces** trae el texto de la última declaración.

---

### US-51: La descripción del instrumento sale de la base (Priority: P1)

Como coordinación, quiero que la descripción del instrumento de cada PI del plan viva en la base y que el R-17 la escriba en G17:I19, para que nadie la complete a mano en el archivo.

**Why this priority**: Jefferson lo pide en sus dos primeros mensajes («la descripción siempre viene de la base de datos»), N2 lo respalda y la columna sigue vacía en el R-17 de la 410. La historia no depende de la spec 004 y puede ir primero en su propia rama.

**Independent Test**: con textos distintos para 5.1, 5.2 y 5.3 de 450002 en 2026-2, G17, G18 y G19 del R-17 traen cada uno el texto de su PI, mientras en `develop` 13c0c12 G17:I19 sale vacía porque la base no guarda ese dato.

**Base** (J-31, cierra J-27 de la spec 004): V1_11 agrega `abet.plan_medicion.descripcion_instrumento` varchar(400) nulo. La de la plantilla original mide 263 caracteres, y G:I con las filas 17 a 19 de unos 76 puntos admite unos 400. La restricción `ck_plan_medicion_descripcion` exige al menos un carácter visible y ningún blanco a los lados, con la misma definición de blanco del Back. `_PLAN` de `r17.py` la lee y `_bloques` la escribe en G de cada fila del bloque I, y deja vacía la celda de un PI sin descripción. `abet_app` no la escribe. La carga un guion de datos aparte y repetible, `db/datos/descripcion_instrumento_2026_2.sql` (propuesta), con un UPDATE por PI y textos distintos por PI marcados «Texto de prueba.», que Jefferson corre desde el Windows en `develop` y en la rama principal de Neon (AD-20). El contenido real lo decide D-34. Una consulta informativa de solo lectura en `db/plataforma/neon/` lista los PI del plan del periodo sin descripción, y no es un control de `pruebas.sql` (AD-29).
**Pantalla**: ninguna, porque el cambio vive en el archivo R-17.

**Acceptance Scenarios** (`specs/005-oportunidades-de-mejora/aceptacion/r17_desde_la_base.feature`):

1. **Cada PI trae su descripción.** **Dado** textos distintos para 5.1, 5.2 y 5.3 de 450002 en 2026-2, **Cuando** se genera el R-17 de la 410, **Entonces** G17, G18 y G19 traen cada uno el texto de su PI.
2. **Sin descripción la celda queda vacía.** **Dado** un plan sin descripción en la base, **Cuando** se genera el R-17, **Entonces** G17:I19 queda vacía y el R-17 no inventa texto.
3. **La base rechaza un texto mal formado.** **Dado** la base con V1_11, **Cuando** se intenta guardar «   », un texto con un blanco al comienzo o uno de 401 caracteres, **Entonces** la base lo rechaza con `ck_plan_medicion_descripcion` o con el largo de la columna.
4. **El guion de datos se puede repetir.** **Dado** una base con V1_11, **Cuando** el guion de datos corre dos veces, **Entonces** deja las mismas tres descripciones.

---

### US-52: El botón atrás vuelve a la pantalla anterior (Priority: P1)

Como usuario, quiero que el botón atrás del navegador me lleve a la pantalla anterior de la aplicación, para no salir de la página.

**Why this priority**: es un pedido literal («cuando se haga click atrás debería volver atrás (no salirse de la página)»). `src/App.tsx` usa `useState<Vista>` sin historial ni dirección, así que hoy el botón atrás sale de la aplicación.

**Independent Test**: desde P2, con «Cargas» (P5) y «Ver constancia» (P4), atrás dos veces lleva a P5 y a P2 sin salir de la aplicación ni pedir otra vez la sesión, mientras en `develop` e88d6f2 el primer atrás sale de la página.

**Base**: ninguna.
**Pantalla**: todas las de `src/App.tsx`. El Front (J-34) guarda cada pantalla en el fragmento de la dirección con `history.pushState` y la recupera con `popstate`, sin tocar `vercel.json` (la regla 7 del preflight del Front rechaza rutas literales fuera de `/api`). Las rutas (propuestas) son `#/secciones` (P2), `#/cargas` (P5), `#/secciones/{seccion_id}/subir` y `#/secciones/{seccion_id}/subir?reemplaza={carga_id}` (P3), `#/cargas/{carga_id}` (P4) y `#/logros` (P6). `history.state` lleva solo la ruta y una marca del ingreso, nunca la constancia ni el borrador. Cada pantalla vuelve a pedir sus datos. Después de una subida, P4 reemplaza la entrada de P3 con `replaceState` solo si la pantalla visible sigue siendo esa subida, y una carga RECHAZADA ofrece «Subir otro archivo» (propuesta). Después de «Salir», `replaceState` lleva a `#/`, y sin usuario la App muestra P1 con cualquier fragmento. Una entrada de otro ingreso o un fragmento desconocido llevan a P2, y P3 recargada cae a P2 porque necesita la sección. Recargar en P4 conserva la pantalla por el fragmento, sin escenario propio. Las pruebas del Front reinician el fragmento en `tests/preparar.ts`.

**Acceptance Scenarios** (`specs/005-oportunidades-de-mejora/aceptacion/navegacion.feature`, todos `@delegado_a_vitest`):

1. **Atrás recorre las pantallas.** **Dado** un usuario en P2 que abre «Cargas» (P5) y «Ver constancia» (P4), **Cuando** pulsa atrás dos veces, **Entonces** llega a P5 y a P2, y adelante vuelve a P5. Ninguno sale de la aplicación ni pide otra vez la sesión.
2. **Después de subir, atrás no repite el envío.** **Dado** una subida que termina en P4, **Cuando** el usuario pulsa atrás, **Entonces** llega a P2 sin repetir el POST.
3. **El modo reemplazo vive en la dirección.** **Dado** P3 en modo reemplazo, **Cuando** el usuario sube el export corregido, **Entonces** `reemplaza` queda en la dirección, y atrás desde P4 de la carga nueva vuelve a P5.
4. **Una dirección a una carga ajena muestra el 403.** **Dado** el fragmento `#/cargas/999`, **Cuando** el usuario lo abre, **Entonces** P4 muestra el 403 «La sección no está a su cargo.».
5. **Después de «Salir» atrás no muestra secciones.** **Dado** un usuario que pulsa «Salir», **Cuando** pulsa atrás, **Entonces** ve P1 y ninguna sección.

---

### US-53: La declaración no lleva datos de estudiantes (Priority: P1)

Como coordinación de la carrera, quiero que la declaración rechace códigos de estudiante y correos y que P4 recuerde no escribir nombres, para que los recuadros A y B no abran otra vía a datos personales.

**Why this priority**: las causas y las acciones son el primer texto libre que un usuario escribe en el esquema `abet`, y BR-R17-07 y la regla 6 de `AGENTS.md` piden un libro sin personas. Q04 mira nombres de columna y no vigila este texto.

**Independent Test**: unas causas con «99000004 no entregó» responden 422 «La declaración no puede llevar códigos ni correos. Describa las causas y las acciones sin datos de estudiantes.» y no se guardan ni como borrador, mientras en `develop` 13c0c12 no existe ningún campo de texto.

**Base** (AD-11): la ruta 15, la ruta 16 y dos CHECK (`ck_mejora_borrador_sin_codigos` y `ck_mejora_declaracion_sin_codigos`, propuestas) usan el mismo patrón ASCII, que es un número de exactamente 8 dígitos no rodeado de otros dígitos o un correo. La violación del CHECK sale como 422 y nunca como 500. La validación corre después del 403, y ni el error ni el registro de la aplicación repiten el texto. Las rutas 13 a 16 responden `Cache-Control: no-store`. El control nuevo Q16 de `db/pruebas/pruebas.sql` busca códigos y correos en las dos tablas y debe dar 0 filas.
**Pantalla**: P4, con la nota «No escriba nombres, códigos ni correos de estudiantes.» (propuesta) sobre el formulario.

Un nombre de estudiante escrito en el texto no se detecta. Jefferson acepta que BR-R17-07 y la regla 6 de `AGENTS.md` se cumplen en estos dos campos por aviso y no por construcción (J-36).

**Acceptance Scenarios** (`specs/005-oportunidades-de-mejora/aceptacion/declaracion.feature`):

1. **Un código se rechaza.** **Dado** la carga de la 410, **Cuando** el profesor guarda causas con «99000004 no entregó», **Entonces** recibe 422 «La declaración no puede llevar códigos ni correos. Describa las causas y las acciones sin datos de estudiantes.» (propuesta), y el texto no se guarda ni como borrador.
2. **Un correo se rechaza.** **Dado** la carga de la 410, **Cuando** el profesor guarda acciones con «escribir a alguien@example.invalid», **Entonces** recibe el mismo 422.
3. **Los falsos positivos se aceptan.** **Dado** la carga de la 410, **Cuando** el profesor guarda un número de 9 dígitos o una fecha como «18/11/2026», **Entonces** el texto se acepta.
4. **La base es la segunda defensa.** **Dado** la base con V1_12, **Cuando** un INSERT directo guarda un código en `abet.mejora_borrador`, **Entonces** falla con `ck_mejora_borrador_sin_codigos`.
5. **El autoguardado no entra en bucle** (`@delegado_a_vitest`). **Dado** un 422 durante el guardado automático, **Cuando** P4 lo recibe, **Entonces** deja el texto en pantalla con el mensaje y no reintenta en bucle.
6. **Las respuestas no filtran datos.** **Cuando** se piden las rutas 13 a 16, **Entonces** todas traen `Cache-Control: no-store` y ninguna trae códigos, nombres ni correos de estudiantes.

---

### US-54: El reemplazo trae el texto anterior como borrador (Priority: P2)

Como profesor, quiero que, al reemplazar mi carga por un export corregido, la carga nueva traiga como borrador las causas y las acciones de la anterior, para revisarlas con las cifras nuevas sin escribirlas de nuevo.

**Why this priority**: Jefferson no menciona el reemplazo, y sin esta historia el profesor reescribe el texto, que es molesto y no rompe nada. Por eso es P2.

**Base** (AD-17): la herencia ocurre al leer, sin escribir en la transacción de la subida. Si la carga nueva no tiene borrador ni declaración, la ruta 14 devuelve en `borrador` el texto de la declaración vigente de la carga que reemplaza o, si no tiene, el de su borrador, con `version` 0 y `heredado_de` igual a su `carga_id`. El texto se guarda en la carga nueva recién con el primer PUT. El R-17 de la carga nueva responde 409 hasta declarar.
**Pantalla**: P4.

**Acceptance Scenarios** (`specs/005-oportunidades-de-mejora/aceptacion/declaracion.feature`):

1. **El texto declarado pasa como borrador.** **Dado** la 410 declarada y reemplazada por el export corregido, **Cuando** el profesor pide la ruta 14 de la carga nueva, **Entonces** recibe los textos declarados como borrador con `heredado_de`, y su R-17 responde 409 hasta declarar.
2. **Sin texto previo no hay herencia.** **Dado** la carga anterior sin texto, **Cuando** se pide la ruta 14 de la nueva, **Entonces** el borrador llega vacío y `heredado_de` es null.
3. **Un borrador previo también se hereda.** **Dado** la carga anterior con solo un borrador, **Cuando** se pide la ruta 14 de la nueva, **Entonces** el borrador se hereda.
4. **El mismo archivo no cambia nada.** **Dado** el mismo archivo subido otra vez, **Cuando** la subida responde 200 sin carga nueva, **Entonces** nada cambia.
5. **El reemplazo del coordinador hereda sin que él vea el texto.** **Dado** un reemplazo hecho por `coordinacion@example.invalid`, **Cuando** se pide la ruta 14 de la carga nueva, **Entonces** el profesor recibe el texto heredado y el coordinador no lo ve.
6. **Escribir en una carga reemplazada conserva el texto.** **Dado** una carga REEMPLAZADA mientras el profesor escribe, **Cuando** envía el PUT, **Entonces** recibe 409 con `reemplazada_por`, y P4 conserva el texto y ofrece «Llevar el texto a la carga N» (propuesta, `@delegado_a_vitest`).

---

### Edge Cases

- Un PI sin calificaciones trae `pct_sobre_calificados` nulo y `pct_sobre_total` 0,0, y su semáforo es SIN_DATO. P4 dice «Sin calificaciones (N sin evidencia)» y nunca dibuja un 0 % ni una luz roja.
- Un conjunto de reglas con NIVEL_ESPERADO o META_LOGRO sin DEFINIR deja cada indicador en SIN_DATO, y la ruta 13 responde 200 y nunca 500.
- Con CORTE_ROJO PENDIENTE, como hoy en R-2026-BORRADOR, el semáforo no tiene banda ámbar, y la leyenda de P4 lo dice con la respuesta (`corte_rojo_pct` nulo).
- La plantilla del R-17 trae reglas de color fijas en E24:F26 (0,79, 0,8 y 0,75) que pintan verde un 79,2 % junto a «El indicador aún no alcanza …» y no siguen una meta distinta de 80 %. Es la plantilla oficial (D-08), así que la spec no la cambia (AD-21 queda fuera de alcance).
- Una carga RECHAZADA o REEMPLAZADA no tiene semáforo ni R-17, y su P4 no pide la ruta 13. La constancia de una REEMPLAZADA sigue disponible.
- Si el Back todavía no tiene la ruta 13 y responde 404, P4 se comporta como hoy y conserva el enlace «Descargar R-17». Por eso el Front se despliega antes que el Back (J-37).
- Toda carga PUBLICADA antes de V1_12, como la 410 y la 411 de la vista previa y de Production, recibe 409 en el R-17 hasta que su profesor declare. Es aceptable en el piloto porque los datos son inventados, y una excepción por fecha dejaría para siempre R-17 sin A ni B.
- Con el código antes de los permisos de `abet_app`, P4 recibe 500, así que el orden de despliegue es migración, `crear_rol_app.sql` sin APP_DB_CLAVE, consulta de solo lectura de los permisos y despliegue del código.
- Dos pestañas, o dos profesores de la misma sección, que escriben el mismo borrador no se pisan, porque el PUT lleva la versión y un desajuste responde 409 con el texto guardado.
- Un profesor que corrige la declaración después de descargar el R-17 (D-37) guarda un borrador nuevo. La declaración anterior sigue vigente y el R-17 siguiente la usa hasta que declare la versión nueva.
- Un reemplazo que llega mientras el profesor escribe deja el 409 con `reemplazada_por`, y el texto no se pierde.
- Una sección que alcanza la meta en todos sus PI también declara causas para obtener el R-17 (D-36), y el enunciado B ya dice «y/o mejorar el resultado del indicador».
- Un texto que empieza con «=», «+», «-» o «@» queda como cadena en el R-17, y `_escribir` cambia los caracteres de control por U+FFFD.
- Un número de 9 dígitos o una fecha no se toman por un código de estudiante, y un nombre propio no se detecta (J-36).
- Un profesor que no declara deja la sección sin R-17, y la salida es reasignar la sección en `acceso.docente_seccion` desde el Windows de Jefferson (J-33).
- Un fragmento desconocido o una entrada de otro ingreso llevan a P2, y P3 recargada cae a P2 porque necesita la sección.
- El alto de las filas 29 a 31 estira también la tabla K28:Q31, que comparte esas filas, así que el cálculo de `r17.py` acota el crecimiento a la fila 31.

## Requirements *(mandatory)*

- **FR-001** La API agrega la ruta 13, `GET /api/cargas/{carga_id}/indicadores` (propuesta), con la respuesta, el orden, la instantánea única, `Cache-Control: no-store` y los errores de US-45 (401, 403 único, 409 de una carga no publicada).
- **FR-002** Una función pura del semáforo vive junto a la función de la meta de la spec 004, con una prueba de tabla que cubre 77,8, 75,0, 74,9, 80,0, los nulos y CORTE_ROJO PENDIENTE.
- **FR-003** P4 suma la sección «Cómo va su sección» con la tabla, la leyenda, la franja provisional y el texto de lo que no se mide (US-46).
- **FR-004** V1_12 crea `abet.mejora_borrador` y `abet.mejora_declaracion`, con sus CHECK y los permisos exactos de `abet_app` en `crear_rol_app.sql` y en sus listas de comprobación.
- **FR-005** Las rutas 14, 15 y 16 usan `puede_declarar()`, el orden 401, 403, 422 y 409, el cuerpo leído después del alcance, JSON obligatorio y la normalización del texto (NFC, saltos de línea, caracteres de control y 2000 puntos de código).
- **FR-006** El formulario de P4 muestra los enunciados literales de la plantilla y guarda de forma automática según US-48, sin almacenamiento del navegador.
- **FR-007** Un 401 durante el guardado no pierde el texto (AD-22).
- **FR-008** `DeclaracionPendiente` entra en `r17.generar()` y en el comando `python -m abet_carga r17`, con el orden de los 409 de US-49.
- **FR-009** P4 es el único lugar que ofrece el R-17, y P2, P5 y P6 llevan a P4 (J-32).
- **FR-010** `r17.py` escribe B29 y B34 desde la última declaración, con ajuste de texto, alineación arriba y el alto calculado de las filas 31 y 36.
- **FR-011** V1_11 agrega `abet.plan_medicion.descripcion_instrumento`, `_PLAN` y `_bloques` la escriben en G17:I19, y un guion de datos repetible y una consulta informativa completan el cambio.
- **FR-012** `src/App.tsx` navega con el fragmento de la dirección (US-52).
- **FR-013** El patrón de códigos y correos es el mismo en la ruta y en los CHECK, en Q16 y en la nota de P4 (US-53).
- **FR-014** La herencia del texto de una carga reemplazada ocurre al leer (US-54).
- **FR-015** Antes de implementar, el Front documenta las rutas 13 a 16 en `docs/03-api/contrato.md` (sección nueva), `docs/specs/api-contracts.md`, P4 en `docs/01-arquitectura/frontend.md`, la feature en `docs/specs/feature-index.md` y ADR-009. El Back escribe las reglas en las specs vivas, que son `r17.spec.md` con BR-R17-04, BR-R17-11 y BR-R17-12 y una feature viva nueva `mejora` con BR-MEJORA-01 a BR-MEJORA-NN (propuesta).
- **FR-016** Cada escenario tiene su prueba, con pytest-bdd para la API y el R-17 y Vitest para las pantallas. La prueba de humo de `e2e/humo.spec.ts` suma el semáforo, la declaración y la descarga con A y B en la vista previa de `develop`.
- **FR-017** La infraestructura de pruebas se amplía así. La expresión de migraciones de `tests/aceptacion/pasos/conftest.py:767` admite V1_11 y V1_12. `REGLAS_DE_COPIA` suma «con la columna X.Y vacía en las filas N y M» (y tres filas). `tests/cargas_de_prueba.py` suma `declarar()` y un conjunto de reglas parametrizado para R-PRUEBA-SEMAFORO. El Front reinicia el fragmento en `tests/preparar.ts`.

## Success Criteria *(mandatory)*

- **SC-001** El 100 % de los semáforos de las pruebas coincide con el bloque II y la tabla K28:Q31 de su R-17 y con `en_meta`.
- **SC-002** Ningún R-17 generado en las pruebas sale sin una declaración, y en todos B29 y B34 traen el texto declarado.
- **SC-003** Un borrador sobrevive a la recarga y a abrir P4 desde otra sesión del mismo profesor.
- **SC-004** En los recorridos de US-52, el botón atrás nunca sale de la aplicación.
- **SC-005** Q16 da 0 filas en las pruebas y en las dos ramas de Neon.
- **SC-006** G17:I19 muestra la descripción de la base del plan de 450002 y queda vacía sin ella.
- **SC-007** En la vista previa de `develop`, la prueba de humo sube la 410, ve tres PI en rojo, declara y descarga un R-17 con A y B.

## Decisiones abiertas

De la carrera (D). Mientras no se decidan, el sistema aplica el valor provisional y P4 y el R-17 llevan la marca PROVISIONAL del conjunto de reglas.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| D-35 | Valor de CORTE_ROJO, que fija la banda ámbar del semáforo | PENDIENTE en R-2026-BORRADOR, así que el piloto muestra VERDE, ROJO o SIN_DATO. La plantilla trae 0,75 como referencia, en una regla ámbar que sus reglas rojas tapan | Coordinación de Ambiental |
| D-36 | Si una sección que alcanza la meta en todos sus PI también declara causas | Sí, como pide Jefferson para todo R-17, y el enunciado B ya dice «y/o mejorar el resultado del indicador» | Coordinación de Ambiental |
| D-37 | Si el profesor corrige la declaración después de descargar el R-17 | Sí, con una declaración nueva que reemplaza a la anterior en el R-17 siguiente, y la anterior queda guardada | Coordinación de Ambiental |
| D-34 | Quién redacta la descripción del instrumento y con qué campos (de la spec 004, sigue abierta) | Textos de prueba marcados «Texto de prueba.» en el piloto, y el contenido real espera a la Coordinación | Coordinación de Ambiental |

De Jefferson (J), con el valor que propone la spec.

| ID | Decisión | Valor provisional | Quién decide |
| --- | --- | --- | --- |
| J-29 | Quién decide el semáforo | El Back, con `en_meta` y CORTE_ROJO (AD-02 y AD-03) | Jefferson |
| J-30 | Dónde vive el borrador y cómo se guarda | Borrador con versión en `abet.mejora_borrador`, declaración de solo INSERT en `abet.mejora_declaracion` y guardado automático en la base (AD-04, AD-05, AD-06 y AD-19) | Jefferson |
| J-31 | Dónde vive la descripción del instrumento | En `abet.plan_medicion.descripcion_instrumento`, cargada desde el Windows con un guion repetible y textos de prueba en el piloto (AD-12 y AD-20). Cierra J-27 de la spec 004 | Jefferson |
| J-32 | Dónde se ofrece el R-17 | P4 es el único lugar, y P2, P5 y P6 llevan a P4 (AD-24). La alternativa es sumar el estado de la declaración a `GET /api/secciones`, `GET /api/cargas` y la ruta 12 | Jefferson |
| J-33 | A quién alcanza el 409 sin declaración | También al coordinador, que no escribe la declaración. Si el profesor no declara, la salida es reasignar la sección en `acceso.docente_seccion` (AD-08 y AD-09) | Jefferson |
| J-34 | Cómo navega el botón atrás | Con el fragmento de la dirección (AD-13 y AD-14) | Jefferson |
| J-35 | Qué reglas vigentes cambia la spec | FR-016 de la spec 004, el invariante 8 de ADR-008, la regla de P4 de `frontend.md`, ADR-005 (invariante 2 y las causas a mano) con ADR-009 y BR-R17-04 (AD-16 y AD-26) | Jefferson |
| J-36 | Qué pasa con los nombres de estudiantes en A y B | BR-R17-07 y la regla 6 de `AGENTS.md` se cumplen por aviso y no por construcción (AD-30) | Jefferson |
| J-37 | Qué pasa con las cargas publicadas antes de V1_12 | Quedan en 409 hasta declarar, sin excepción por fecha, y el Front se despliega antes que el Back (AD-28) | Jefferson |

## Fuera de alcance

- La descripción del SO en B15 del R-17 (C-08), que Jefferson no pidió.
- Quién declaró y cuándo en la hoja «Constancia» y en la constancia en JSON (C-12). La base guarda `declarada_por` y `declarada_en`, pero el R-17 no los muestra, y `constancia.armar()` no cambia (BR-R17-10, igualdad con el 201).
- La marca «Declaración pendiente» en P2 y P5 (C-14 b).
- Que `r17.py` pinte E24:F26 con la función del semáforo (AD-21). Hoy las reglas fijas de la plantilla pintan verde un 79,2 % junto a «El indicador aún no alcanza …» y no siguen una meta distinta de 80 %. Es la plantilla oficial (D-08).
- La reunión de mejora con su acta (N11), las acciones con responsable, fecha y seguimiento (N12) y la precarga del ciclo siguiente (N13). A y B son texto libre, como en el R-17.
- El resto de N6, que son los criterios de la rúbrica con más dificultades, la lista de estudiantes que necesitan apoyo y la comparación con el promedio del curso (D-33).
- La edición de la descripción del instrumento desde una pantalla (D-34).
- Que el coordinador escriba la declaración.
- Recargar en una dirección profunda como objetivo propio (C-09 parte B), que queda como efecto del fragmento y sin escenario.
