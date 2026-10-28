# Revisión por refutación de las historias del MVP del export de Blackboard al R-17

**Fecha**: 2026-10-28
**Spec**: [spec.md](./spec.md)
**Entrada**: 25 historias candidatas (C-01 a C-25), que unen 29 historias escritas desde tres ángulos (profesor, coordinador con la base, y evidencia y privacidad)
**Salida**: 21 historias del MVP (US-01 a US-21 de la spec) y 6 piezas para después
**Fuentes**: `historias/candidatas.md`, `historias/auditoria_necesidad.md`, `historias/auditoria_tamano.md`, `historias/auditoria_verificabilidad.md` e `historias/critica_arquitectura.md`, en la carpeta de trabajo de la sesión del 2026-10-28 (fuera del repositorio)

## Método

Cada candidata parte refutada y sobrevive solo si resiste tres lentes independientes. La lente de necesidad pregunta si la exige uno de los cuatro resultados del MVP (base en la nube, subir el export, datos cargados en la base, R-17 con su constancia), una frase literal del pedido o un requisito del primer lanzamiento. La lente de solapamiento y tamaño aplica INVEST (independiente, negociable, valiosa, estimable, pequeña y comprobable) y busca reglas probadas en varios lugares. La lente de verificabilidad coteja cada escenario con las migraciones V1_01 a V1_08, las vistas `R__`, `pruebas.sql`, `datos_sinteticos.sql` y el único export inventado que existe, leído celda por celda. Un crítico aparte ataca las ocho decisiones técnicas de la arquitectura.

Los veredictos posibles son SOBREVIVE, CORREGIR, FUSIONAR, PARTIR, MOVER_A_DESPUES y REFUTADA. Ninguna candidata queda refutada del todo, porque cada una que no sobrevive conserva algún escenario que otra historia necesita. Este archivo registra los veredictos y su destino; el razonamiento completo y la evidencia con línea de archivo están en cada informe.

Las candidatas se nombran C-01 a C-25, con una letra cuando la auditoría las parte (C-12a y C-12b, por ejemplo), y el prefijo US-NN queda solo para las 21 historias finales de la spec. Los demás identificadores vienen de otras fuentes. N# es una fila del Excel `Requisitos_Sistema_Medicion.xlsx`, H##, C# y P## son filas de `Entregables/Revision_Requisitos_y_Tableros.xlsx`, Q## es una consulta de control y A## o R## un caso de prueba de `bd/pruebas/pruebas.sql`. Cada informe numera además sus historias faltantes a su manera (F-01 en el de necesidad, «faltante 1» en el de tamaño y F1 en el de verificabilidad), y la tabla de faltantes conserva el número de cada informe.

## Veredictos por candidata

Abreviaturas. S es SOBREVIVE, C es CORREGIR, F es FUSIONAR, P es PARTIR y M es MOVER_A_DESPUES. «Después» indica que la pieza sale de la spec 001 y queda en «Fuera de alcance».

| Candidata | Título de la candidata | Necesidad | Solapamiento y tamaño | Verificabilidad | Historia final |
| --- | --- | --- | --- | --- | --- |
| C-01 | Aplicar las migraciones del esquema abet en Neon con Flyway | S | S | C, el escenario de credenciales falla con `bd/.env.neon` ignorado; se reescribe sobre `git ls-files` y `git log -p --all` | US-01 |
| C-02 | Crear el rol de escritura del programa de carga sin permisos de borrar | C, la traza a N15 no la sostiene y el rol no cubre el esquema `acceso` | C, faltan SELECT sobre las vistas del R-17 y el rol del esquema `acceso` | C, la carga de la 411 sin códigos propios dispara Q08 | US-02, con el rol único `abet_app` |
| C-03 | Preparar el periodo 2026-2 con vigencia del catálogo, secciones y plan de medición | C, el actor es el administrador técnico y no el coordinador | C, mismo actor; el escenario del PI fuera del plan es de la carga | C, el PI 5.4 no existe en el catálogo | US-03; el PI fuera del plan pasa a US-10 con 4.1 |
| C-04 | Autorizar correos con su rol y asignar docentes a secciones | C, sobran la auditoría de altas, el rol admin y la pantalla | C, la baja de un correo es un escenario del ingreso | C, Q04 se cumple por construcción y no vigila `acceso` | US-04 (con V1_09 y Q15); la baja pasa a US-05; la auditoría de altas, después |
| C-05 | Verificar la base en Neon con las consultas de control | F, es un criterio de terminado | F, con C-01, C-08 y C-10 | S | US-01; los controles posteriores a la carga, a US-17 |
| C-06 | Iniciar sesión con el código que llega al correo | S, le falta el envío del correo | S, el rol es «usuario autorizado» | S, depende del proveedor de correo | US-05 con contraseña asignada (J-03) y US-20 con el código, corte 2 |
| C-07 | Ver solo mis secciones del periodo | S | S, única dueña de la regla de visibilidad | C, la sección sin plan contradice sus Antecedentes y «periodo vigente» no existe en la base | US-06, con `PERIODO_VIGENTE` |
| C-08 | Subir el export de Blackboard de una sección | S | S, absorbe C-09, C-16 y la huella de C-11 | S | US-07 |
| C-09 | Escribir cada carga en una sola transacción | F, es una regla y no una historia | F, un escenario duplica C-13 | S | US-07 |
| C-10 | Rechazar exports con códigos fuera del rango inventado | S, la traza a H04 es débil | S, un escenario no se puede comprobar como está escrito | C, el ejemplo 9900001 deja inalcanzable CODIGO_INVALIDO sin decirlo | US-08, con la segunda barrera en la base |
| C-11 | Calcular la huella SHA-256 del export y evitar que el mismo archivo se cargue dos veces | C, sobra la promesa de historial | C, la huella ya está en C-08 | C, el escenario del byte distinto choca con el reemplazo | US-09 (archivo repetido); la huella pasa a US-07 |
| C-12 | Revisar la validación con filas leídas, aceptadas, rechazadas y avisos conciliadas con el archivo | S | P, en reglas por fila (C-12a) y pantalla de resultado (C-12b) | C, escenario de fila perdida impreciso y falta la celda vacía SIN_EVIDENCIA | US-10 (C-12a); la pantalla mínima de C-12b pasa a US-07 |
| C-13 | Recibir un motivo claro cuando el archivo no se puede leer o la carga se rechaza | C, de los motivos nuevos solo COLUMNA_CODIGO_AUSENTE se justifica | P, en archivo ilegible (C-13a) y rechazo por estructura (C-13b) | C, conteo ambiguo con el AVISO de 5.3 y un motivo que hoy viola `ck_rechazo_fila_motivo` | US-11 (C-13a) y US-12 (C-13b) |
| C-14 | Detener un export que pertenece a otra sección | P, el cotejo entra y la confirmación manual sale | P, en cotejo (C-14a) y confirmación (C-14b) | C, escenario con dos Cuando y una migración sin etiqueta | US-13 (C-14a) y US-21, prioridad P3, corte 2 (C-14b) |
| C-15 | Descartar nombres y valores leídos del export | S | C, el escenario del R-17 pertenece al R-17 | C, escenarios sin Cuando y un mensaje distinto del de C-12 | US-14; el escenario del R-17 pasa a US-15 |
| C-16 | Registrar quién sube cada export y cuándo | S | F, llenar `subida_por` es un criterio de la subida | C, `now()` hace iguales inicio y fin | US-07 (`subida_por`), US-16 (constancia con `clock_timestamp()`) y US-02 (sin UPDATE de `subida_por`) |
| C-17 | Descargar el R-17 de mi sección generado desde la base | S, absorbe C-18 y C-21 | S, la historia más grande | S, cifras recalculadas | US-15 |
| C-18 | Marcar el R-17 como provisional mientras las reglas no estén aprobadas | F, la franja es una propiedad del archivo | F, con C-17 | C, R-PRUEBA-APROBADO solo existe en `pruebas.sql` (caso A03) y no fija cifras del export de 450002 | US-15, con la franja y con el escenario de reglas aprobadas, que fija 90,9 % (10 de 11) con nivel esperado 2 y meta 70 %, cifras comprobadas contra los niveles de `datos_sinteticos.sql` |
| C-19 | Emitir la constancia que ata el R-17 a un archivo y una carga | P, la hoja entra y la pantalla «Verificar carga» sale | P, en hoja «Constancia» (C-19a) y verificación (C-19b) | S | US-16 (C-19a); C-19b, después |
| C-20 | Ver todas las cargas de la carrera con su estado | C, N9 no la sostiene; sobrevive reducida y sin filtro por estado | S, absorbe C-24 | S | US-19, corte 2 |
| C-21 | Descargar el R-17 de cualquier sección de la carrera | F, es el mismo R-17 con otra regla de permiso | F, con C-17 | S | US-15 (esquema de quién descarga) |
| C-22 | Reemplazar mi propia carga con un export corregido sin borrar la anterior | C, la fecha de cierre sale | P, en reemplazo (C-22a) y cierre por fecha (C-22b) | C, la carga A tiene 2 filas de `rechazo_fila` y el reemplazo fallido pide un UPDATE que el rol no da | US-18, corte 2 (C-22a); C-22b, después |
| C-23 | Reemplazar como coordinador la carga publicada de una sección | M, sin fecha de cierre el profesor siempre puede reemplazar | F, es una fila de permiso de C-22a | S | US-18 (esquema de quién reemplaza) |
| C-24 | Ver el historial de cargas de mi sección | M, el MVP funciona sin esta pantalla | F, misma consulta que C-20 | S | US-19 |
| C-25 | Aprobar un conjunto de reglas y reprocesar las cargas de la carrera | M | P, en aprobar (C-25a) y reprocesar (C-25b) | S, la nota sobre los bytes contradice el caso A03 de `pruebas.sql` | Después (C-25a y C-25b) |

Cuentas por lente, tomadas de las tablas de cada informe.

| Lente | S | C | F | P | M |
| --- | --- | --- | --- | --- | --- |
| Necesidad | 9 | 7 | 4 | 2 | 3 |
| Solapamiento y tamaño | 7 | 5 | 7 | 6 | 0 |
| Verificabilidad | 11 | 14 | 0 | 0 | 0 |

El resumen en prosa del informe de necesidad dice 8 que sobreviven y 8 que se corrigen, pero su propia tabla da 9 y 7; aquí manda la tabla. Sumadas las tres lentes, 15 candidatas reciben al menos un CORREGIR (C-01, C-02, C-03, C-04, C-07, C-10, C-11, C-12, C-13, C-14, C-15, C-16, C-18, C-20 y C-22). En la lista final 7 candidatas se parten (C-11, C-12, C-13, C-14, C-19, C-22 y C-25) y 8 piezas se fusionan en otra historia (C-05, C-09, C-16, C-18, C-21, C-23, C-24 y la pantalla de C-12b).

## Historias faltantes

| Faltante | Lo propone | Historia o requisito final |
| --- | --- | --- |
| Migración V1_09 con el esquema `acceso`, `carga.subida_por` y los motivos nuevos | Necesidad (F-01) | US-04 y FR-003 |
| Rol de la API para el esquema `acceso` y para leer las vistas del R-17 | Necesidad (C-02), tamaño (faltante 4) | US-02, con un solo rol `abet_app` (J-02) |
| Envío del código de acceso por correo desde un dominio propio | Necesidad (F-02), verificabilidad (F4) | US-20, corte 2; la semana 1 entra con contraseña asignada (US-05) |
| Despliegue de la API y del Front en Vercel conectados a Neon | Necesidad (F-03), tamaño (faltante 3), verificabilidad (F1) | US-17 |
| Prueba de punta a punta del MVP en Neon | Necesidad (F-04) | US-17, escenario 1 |
| Juego de exports inventados y casos nuevos en `pruebas.sql` | Necesidad (F-05), verificabilidad (F2) | FR-030; no es una historia porque ningún rol la pide |
| Rechazo de filas con código vacío, inválido o repetido | Tamaño (faltante 1), verificabilidad (F3) | US-10, escenarios 5, 6 y 10 |
| Columna de PI fuera del plan ignorada con aviso | Tamaño (faltante 2), verificabilidad (C-03) | US-10, escenario 7 |
| Periodo vigente y conjunto de reglas de una carga nueva | Verificabilidad (F5) | US-03, escenario 4, y FR-007, con `PERIODO_VIGENTE` y `CONJUNTO_REGLAS` |
| Estudiante medido en dos secciones del mismo curso (Q08) | Tamaño (faltante 5), verificabilidad (defecto 1) | Después como regla; en el MVP, la 411 usa los códigos 99000012 a 99000022 (US-02 y FR-030) |
| Columna de código ausente, PI repetido y periodo distinto como motivos propios | Decisión de documentación sobre los motivos de necesidad y tamaño | US-12 y US-13, con COLUMNA_CODIGO_AUSENTE, PI_REPETIDO y PERIODO_NO_COINCIDE en V1_09 |

## Defectos transversales de verificabilidad

| Defecto | Resolución en la spec |
| --- | --- |
| Q08 se dispara si la 411 repite los códigos de la 410 | Códigos 99000012 a 99000022 en la 411 (US-02 y Edge Cases) |
| Solo existe el export con error | FR-030, con los archivos en `tests/datos_inventados/` |
| `now()` deja iguales inicio y fin de una carga | `clock_timestamp()` al cerrar (US-16, escenario 3, y FR-021) |
| Escenarios que ejecuta el coordinador sin pantalla | Los ejecuta el administrador técnico con scripts (US-03 y US-04) |
| La base no marca periodo ni conjunto de reglas vigentes | Configuración de la API (FR-007) |
| Los identificadores de carga se consumen al deshacer | Las pruebas capturan el `carga_id` devuelto (Edge Cases) |

## Veredicto del crítico de arquitectura

| N.º | Decisión | Veredicto | Lo que adopta la spec |
| --- | --- | --- | --- |
| 1 | Backend en Python con FastAPI y `abet_carga` como biblioteca | SE_SOSTIENE | openpyxl directo y sin pandas, revisión previa del zip, prueba que exige defusedxml y biblioteca que no importa FastAPI (FR-008 y FR-013, US-11) |
| 2 | Frontend en React con Vite, TypeScript y Tailwind | SE_SOSTIENE | Cuatro pantallas en el corte 1, sin token en `localStorage` y sin acceso del Front a la base (FR-022 y FR-023) |
| 3 | Vercel Hobby en gru1 con API y Front en un mismo proyecto | CAMBIAR | Dos proyectos con reescritura de rutas al mismo origen desde el Front, entrenamiento de inteligencia artificial desactivado y Preview contra otra rama de Neon (US-17 y FR-024); para datos reales, primero Cloud Run en southamerica-east1 |
| 4 | Código de 6 dígitos propio frente a Neon Auth | DUDOSA | Se descarta Neon Auth; la semana 1 entra con contraseña asignada y el código por correo pasa al corte 2 (US-05, US-20 y J-03) |
| 5 | Guardia de datos inventados por rango de código | CAMBIAR | Guardia doble, en la API y como `ck_estudiante_codigo_inventado` en Neon, respuesta 422 sin rastro y rótulo en la pantalla de subida (US-08, FR-005 y Edge Cases) |
| 6 | Gherkin en español con pytest-bdd o behave y Playwright | DUDOSA | Prueba de 30 minutos el día 1, Gherkin ejecutable solo en la carga y el R-17 y una prueba de humo con Playwright (FR-028 y FR-029) |
| 7 | `bd/` pasa al Back como `db/` después del despliegue en Neon | SE_SOSTIENE con ajuste de momento | Traslado después del primer `migrate` y antes de V1_09, con historia preservada y CI con psql sin Redgate (FR-002, FR-031 y J-06) |
| 8 | R-17 con openpyxl desde la plantilla vaciada | SE_SOSTIENE | Pillow obligatorio, `#REF!` limpiados, filas fijas, propiedades sin personas, solo la hoja «Cursos de Carrera» y la hoja «Constancia» al final (US-15, US-16 y FR-019) |

El crítico deja sin verificar que `vercel.app` figure en la Public Suffix List y que la reescritura de rutas conserve la cookie de primera parte, el arranque en frío de FastAPI en Vercel, el comportamiento real de pytest-bdd y behave con `# language: es` y el autor guardado en las propiedades de la plantilla. La spec los cubre con US-17 (escenario 2), FR-028 y US-15 (escenario 6), que fallan si la suposición no se cumple.

## Estimaciones de los informes

Los tres informes estiman el plazo sin medición del equipo y con supuestos distintos. Necesidad da de 15 a 21 días hábiles con el código por correo desde el inicio. Tamaño da de 31 a 37 días de trabajo sin interrupciones de una persona para sus 21 historias, o de 24 a 30 si se limita a los cuatro resultados. El crítico da cerca de 7 días hábiles con contraseña en la semana 1, solo la hoja «Cursos de Carrera» y Gherkin ejecutable en la carga. La spec adopta el corte del crítico como corte 1 (unos 7 días hábiles) y deja el código por correo, el reemplazo, la lista de cargas y la confirmación de sección para el corte 2 (unos 3 a 4 días más).
