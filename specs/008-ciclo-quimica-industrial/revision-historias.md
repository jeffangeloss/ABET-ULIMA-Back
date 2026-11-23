# Revisión por refutación de las historias del ciclo de Química General en Ingeniería Industrial

**Fecha**: 2026-11-23
**Spec**: [spec.md](./spec.md)
**Entrada**: 37 candidatas escritas desde cuatro ángulos, el del profesor de Química General (C-01 a C-09), el de la coordinación del curso y de la carrera (C-20 a C-28), el de la base y la siembra (C-40 a C-49) y el de la capacitación, la evidencia y la privacidad (C-60 a C-68), cada una con su pantalla, sus rutas y tablas y su Gherkin en español. Salen del pedido de Jefferson del 2026-11-23 y de los hechos que Stefanny Montaño (Oficina de Calidad) verificó el mismo día sobre los datos de Química General de 2026-1
**Salida**: 24 historias (US-67 a US-90 de la spec) en 12 archivos `.feature`, con 202 escenarios y 257 casos
**Fuentes**: los informes de las tres lentes y del crítico de arquitectura que entrega el flujo de trabajo de la sesión. Los datos reales de Química General viven fuera de todo repositorio, en `ABET_SIS_MED/datos_reales/quimica_2026_1/`, y ninguna candidata ni esta revisión los copia

## Método

Cada candidata parte refutada y sobrevive solo si resiste tres lentes independientes, como en las specs 001 y 003 a 007. La lente de necesidad pregunta si la exige el pedido de Jefferson, el acuerdo con Stefanny de lograr el flujo de punta a punta o una regla vigente, y si cambia algo que `develop` no hace ya. La lente de solapamiento y tamaño aplica INVEST (independiente, negociable, valiosa, estimable, pequeña y comprobable) contra las demás candidatas y contra US-01 a US-66. La lente de verificabilidad lee el código real de `wt/back-008` y `wt/front-008` y comprueba cada texto, celda, restricción y paso contra lo que existe.

Los veredictos posibles son SOBREVIVE (S), CORREGIR (C), FUSIONAR (F), PARTIR (P), MOVER_A_DESPUES (M) y REFUTADA (R). La regla de las specs anteriores deja en la spec a una candidata que a lo sumo una lente marca R o M, así que una candidata sale cuando dos lentes o más la marcan R o M. Las candidatas que salen por MOVER_A_DESPUES van a «Fuera de alcance» de la spec con su razón, y las que salen por REFUTADA quedan solo en esta revisión. FUSIONAR, PARTIR y CORREGIR se aplican tal como los proponen las lentes, y cuando dos lentes proponen fusiones distintas, decide la que sigue el veredicto del crítico. El crítico de arquitectura ataca las decisiones técnicas con SE_SOSTIENE, CAMBIAR o DUDOSA. CAMBIAR cambia la decisión de la candidata, y DUDOSA se vuelve una decisión J-NN abierta desde J-49, con el valor provisional que propone el crítico.

## Veredictos por candidata

| Candidata | Título | Necesidad | Solapamiento y tamaño | Verificabilidad | Destino |
| --- | --- | --- | --- | --- | --- |
| C-01 | El profesor elige el periodo y ve sus secciones, cargas y logros de 2026-1 | S, sin el periodo el flujo se corta en P2, porque la ruta 8 usa siempre `periodo_vigente` y el Front no manda periodo | F, absorbe C-28 y C-49, y la ruta 18 choca con el número que pide C-24 | F, la ruta 8 sin `seccion_id` usa `periodo_vigente` (`app/rutas/cargas.py`, línea 190) y el 422 coincide con `PERIODO` | US-73, con C-28, C-49 y el periodo de P6 de C-08 |
| C-02 | P2 muestra en cada sección el paso del registro | M, la línea de US-59 ya dice lo que falta | F, es rediseño de P2 y pertenece a C-09 | C, el Dado no fija `filas_aceptadas` ni `filas_leidas` y el mock no da «34 de 34» | US-81, como el bloque de P2 del sistema visual |
| C-03 | El export de 5643 se publica entero en Industrial | S, es el corazón del flujo y nadie lo prueba para Industrial | P, separa la publicación de los errores de la sala, y el archivo repetido da 200 y no 409 | C, YA_PUBLICADA responde 200, y Q01 a Q14 y «no ganan filas» no siguen los pasos existentes | US-75 (parte a) y US-76 (parte b, con la parte del Back de C-66) |
| C-04 | Cada profesor recibe un export generado desde la tabla maestra | F, repite a C-60 | F, en C-60, con el filtro por parámetro | F, `<fecha>` no es un marcador de un esquema y no nombra `scripts/generar_exports_inventados.py` | US-74, dentro de C-60 |
| C-05 | P4 de una carga publicada con filas rechazadas dice qué corregir y ofrece reemplazarla | M, los exports generados no traen filas rechazadas y el reemplazo ya vive en P5 | C, historia de pantalla de los errores de química, sin los escenarios del Back | C, `queCorregir()` cambia para la carga PUBLICADA y CODIGO_VACIO acepta también Student ID | US-77, sin el botón de reemplazo (J-53) |
| C-06 | El R-17 de 5643 dice la carrera de su carga | S, B6 dice «Carrera de Ingeniería Ambiental» y `_cabecera()` no la toca | C, se reduce a B6, la cabecera y las cifras de Industrial | C, las cifras van en M24 a M26 y E24 es 0,765, el nombre lleva siempre _PROVISIONAL y BR-R17-12 ya es de la spec 005 | US-78, con el escenario del catálogo de C-08 |
| C-07 | El R-17 del sistema se compara con el R-17 a mano | F, en C-61, porque la tabla maestra ya es el oráculo | F, en C-61 como su comparador | F, en C-61, con una sola regla de redondeo | US-83, como regla del conciliador (CAMBIAR del crítico) |
| C-08 | P6 muestra el logro del PI 6.1 frente a la meta | F, el periodo es de C-01 y lo visual de C-09 | P, el periodo a C-01, la fila a C-09 y el catálogo a una historia del Back | C, `_SO` no filtra la carrera y el caso de dos planes lo vigila un control | US-73 (periodo), US-78 (catálogo y fila de P6) y Q18 |
| C-09 | Las pantallas comparten un sistema visual claro, accesible AA y usable a 375 px | C, el pedido literal exige que se vea mejor y suma P7 y los rótulos del curso | P, sistema visual común y uso a 375 px con teclado | S, los roles, los textos y Playwright 1.64.1 existen | US-81 (parte a) y US-82 (parte b) |
| C-20 | Rol de coordinación del curso COORD_CURSO | F, con C-45 | F, con C-45, y el modelo lo decide el crítico | C, `[A-Z]+` no captura el guion bajo y la 410 en 2026-1 no se puede sembrar | US-71, con el modelo de tabla de alcance (CAMBIAR del crítico) |
| C-21 | Registrar al coordinador del curso con una corrida en seco | F, en C-45 | F, en la parte del guion de C-45 | F, choca con C-45 en el correo que ya es profesor y Q15 no vive en `controles_neon.sql` | US-72, con el correo por variable y salida 1 (CAMBIAR del crítico) |
| C-22 | La ruta 17 y P7 dan al coordinador del curso la etapa de cada sección | C, amplía US-64 y US-65 de la spec 007 sin los correos | C, solo lo que cambia frente a la spec 007, con la etapa B adelantada | C, la ruta 17 no existe y el paso de sesión no es uno de los existentes | US-79 |
| C-23 | Porcentaje de cumplimiento por sección y del curso | M, nadie lo pidió y D-32 sigue abierta | C, condicionada a D-32, absorbe el agregado de C-65 | S, las cifras se recalculan y dan 69,7 frente al promedio de 71,3 | US-80, condicionada por J-54 (DUDOSA del crítico) |
| C-24 | Descargar en un solo archivo los R-17 del curso | R, el pedido no nombra esa descarga | M, depende de P7 y de US-49 de la spec 005 | M, la comparación byte a byte falla por `properties.created` y la hoja «Constancia» trae el correo | Fuera de alcance, por mayoría de M (J-55) |
| C-25 | El coordinador del curso reemplaza la carga publicada, si se decide | R, nadie pidió ese permiso | M, depende de D-11 y de una decisión nueva | C, dos valores de una decisión no pasan en un mismo código | Fuera de alcance como historia propia. Su escenario único entra en US-71 con D-52 (CAMBIAR del crítico) |
| C-26 | La coordinación de carrera ve solo las secciones de su carrera | F, en C-44 | F, en C-44, con sus escenarios de D-50 y de la migración | F, en C-44, con un solo valor provisional | US-70, dentro de C-44 |
| C-27 | El coordinador del curso que dicta una sección sube en la suya | M, ningún dato dice que el coordinador dicte | M, es un caso borde del modelo de alcance | F, es la otra forma de C-20 y C-45 | Fuera de alcance, por mayoría de M, con J-51 (DUDOSA del crítico) |
| C-28 | La coordinación elige el periodo que revisa | F, en C-01 | F, en C-01, sin esconder el selector al profesor | F, en C-01 | US-73 |
| C-40 | Catálogo IND-2026 generado desde su referencia curricular | C, la migración toma el número V1_12 que la spec 005 reserva | C, renumerar | C, la sección 1 de `pruebas.sql` cuenta en toda la base y falla con IND-2026 | US-67 |
| C-41 | Conjunto de reglas R-2026-BORRADOR para Industrial | S, sin él la primera subida da ConfiguracionInvalida | S, absorbe el escenario sin reglas de C-03 | C, la vista da 60,0 y 80,0, y la ruta responde el 500 genérico | US-68, con Q19 |
| C-42 | Vigencia de IND-2026 en 2026-1 y plan de Química General | S, `fk_plan_medicion_vigencia` exige la vigencia antes del plan | S, con la huella de Ambiental en lugar de conteos | C, los números de migración y de consulta siguen las reservas | US-69, con Q18 |
| C-43 | Las 18 secciones con sus cuentas de profesor de ejemplo | C, falta atar el curso de Blackboard al generador | F, en C-46, porque casi todo repite la spec 006 | C, los motivos son los textos de `_forma()` y las secciones no comparten base | US-86, con el escenario de la programación de 2026-1 y Q21 |
| C-44 | El alcance del coordinador se ata a su carrera | S, con IND-2026 vigente la coordinación de Ambiental vería Química | F, base de la fusión con C-26 | C, numeración, privilegios de `abet_respaldo` y listas de `probar_rol_app.sql` | US-70, con Q20 |
| C-45 | Cuenta del coordinador de Química General con alcance de su curso | C, sin el reemplazo que nadie pidió | P, alcance, guion y reemplazo | C, el Front no distingue el curso sin un campo nuevo en la ruta 2 y `asignar_claves.py` rechaza el correo real | US-71 (alcance) y US-72 (guion). El reemplazo queda con D-52 |
| C-46 | Siembra de Química en Neon desde el Windows | C, falta el orden frente al humo y al restablecimiento | C, absorbe C-43 y fija la ventana de la capacitación | C, numeración y comparación del R-17 celda por celda | US-86 |
| C-47 | Consultas de control Q16 a Q19 | P, cada consulta vigila una historia distinta | C, los números chocan con la spec 005 | C, se renumeran desde Q18 | Q18 en US-69, Q19 en US-68, Q20 en US-70 y US-71, Q21 en US-75 y US-86 |
| C-48 | Conciliación de las cargas de Química con la tabla maestra | F, con C-65 | F, con C-65 | F, con C-65, con openpyxl en lugar de leer xlsx a mano | US-83 |
| C-49 | El periodo anterior 2026-1 al alcance sin cambiar el vigente | F, en C-01 | F, en C-01 | F, en C-01, con el texto exacto de `_OTRO_PERIODO` | US-73 |
| C-60 | Generador de los 18 exports desde la tabla maestra | S, sin él no hay nada que subir | S, absorbe C-04 | C, el PI va por parámetro y el curso sale de la programación | US-74 |
| C-61 | Ensayo completo con los 18 exports y la comparación de los R-17 | C, sin el escenario de 143 estudiantes | C, absorbe C-07 y cita los escenarios que tienen dueño | C, 60,0 en lugar de 0,6000 y el texto de NO_LOGRADO | US-84, con el conciliador de US-83 |
| C-62 | Humo con Playwright de punta a punta en la vista previa | C, el periodo y la llegada a P7 dependen de otras historias | C, corre una sola vez antes de la siembra de la capacitación | C, develop restablecida no trae Química y el R-17 se compara celda por celda | US-85 |
| C-63 | Guía de la capacitación por rol | C, sin el correo copiado | S, con los textos de P4 corregidos | C, el consejo de SECCION_NO_COINCIDE nombra la sección elegida | US-87, con el ejercicio inventado (CAMBIAR del crítico) |
| C-64 | Barrido de privacidad en cada cambio | C, el historial se barre una vez | S, absorbe la tarjeta de C-63 y las capturas de C-62 | C, la regla tabular y el límite de palabra evitan falsos positivos | US-88 |
| C-65 | Tabla maestra de ida y vuelta y controles después de la capacitación | F, en C-48 | F, en C-48, con el agregado a C-23 | F, en C-48, con la ruta 12 por sección | US-83 |
| C-66 | Errores realistas de Química en la capacitación | F, en C-03 | sin veredicto propio, la absorbe C-03 b | C, la comprobación de P4 y del registro se precisa | US-76 (Back) y US-77 (pantalla) |
| C-67 | Cierre de la capacitación y destino de los datos reales | P, la baja de cuentas es necesaria y el paso a main espera | P, cierre de la sesión y paso a main | C, el cierre necesita un guion con nombre y pruebas en tmp_path | US-89 (parte a). El paso a main queda fuera de alcance con D-55 |
| C-68 | Matriz de cumplimiento | C, la traza va al repositorio y la corrida a la integración continua | C, primero las specs 007 y 008 | C, el hueco admite una prueba nombrada en la línea **Prueba** | US-90 |

Las tres lentes coinciden en que el flujo de punta a punta necesita el catálogo, las reglas y el plan de Industrial, el alcance de las dos coordinaciones, el periodo elegido, el generador, la carga, el R-17 con la carrera, el ensayo, el humo, la siembra, la guía y la privacidad. Discrepan en C-02, que la necesidad mueve y el tamaño fusiona en el sistema visual, y en C-23, que la necesidad mueve, el tamaño condiciona y la verificabilidad sostiene, y que el crítico deja como J-54 abierta. C-24, C-25 y C-27 salen porque dos lentes las marcan R o M.

## Correcciones que la spec adopta

| Corrección | La propone | Dónde queda |
| --- | --- | --- |
| Un solo juego de secciones inventadas de 5643 en 2026-1, la 701 a la 704, con `docente701@example.invalid` a `docente703@example.invalid`, la 704 sin profesor y el curso `SINTETICO_20261_5643_70N`, en `db/datos/quimica_2026_1_inventado.sql` | Crítico y verificabilidad | Todos los `.feature` y FR-002 |
| El mismo archivo subido otra vez en la misma sección responde 200 con la constancia existente (BR-CARGA-09) | Crítico, solapamiento y verificabilidad | US-76, escenario 7 |
| Las cifras del R-17 se comprueban en M24 a M26, E24 vale 0,765 con el formato 0.0 % y el nombre lleva siempre _PROVISIONAL con R-2026-BORRADOR | Verificabilidad | US-78 |
| La vista da `pct_logro_sobre_calificados` 60,0 y `meta_logro_pct` 80,0 en escala de 0 a 100 | Verificabilidad | US-68, escenario 2 |
| La falta del conjunto de reglas de Industrial se prueba en `cargar()` y, por la ruta 5, como el 500 genérico, y la comprobación de arranque revisa cada carrera con plan | Verificabilidad y crítico | US-68 y FR-007 |
| La sección 1 de `db/pruebas/pruebas.sql` cuenta por catálogo y `abet.asignatura` queda con 96 filas | Verificabilidad | US-67, escenario 3 |
| El generador filtra por `--periodo`, `--asignatura` y `--pi`, cuenta lo omitido en el manifiesto y toma el curso de Blackboard del CSV de la programación | Solapamiento, verificabilidad y crítico | US-74 |
| El código con cero a la izquierda se arma en la prueba y no se escribe en el `.feature`, porque una cifra de ocho dígitos que no empieza con 99 haría fallar el barrido de US-88 | Redacción, por la regla de US-88 | US-74, escenario 4 |
| El consejo de CODIGO_VACIO y CODIGO_INVALIDO nombra Username o Student ID, y el de la carga sin filas aceptadas deja de decir «Corrija en Blackboard» | Verificabilidad, necesidad y crítico | US-77 y FR-012 |
| El ejercicio de error de la guía usa un archivo inventado de la sección ficticia 799 por profesor, con su propia huella | Crítico | US-74, escenario 14, y US-87 |
| Las consultas nuevas empiezan en Q18 y la sección sin carga no es un control de 0 filas | Crítico y solapamiento | FR-021 |
| El humo corre una sola vez con la siembra inventada, antes de restablecer develop y sembrar la capacitación | Necesidad, solapamiento y crítico | US-85, US-86 y J-56 |
| El R-17 de la 410 se compara celda por celda y no por bytes, porque `_propiedades()` escribe la fecha de generación | Verificabilidad | US-86, escenario 1 |
| El porcentaje se compara como cociente x de n y con un decimal, y PROFESOR, ARCHIVO y ESTADO DE EVIDENCIA no se comparan | Solapamiento y verificabilidad | US-83 |
| La regla de ocho cifras usa límite de palabra, excluye el rango 99 y las huellas de 64 caracteres, y la regla de la tabla maestra mira solo archivos tabulares | Verificabilidad | US-88 |
| El hueco de la matriz es una regla sin escenario y sin prueba nombrada en su línea **Prueba** | Verificabilidad | US-90 |
| El cierre informa qué se puede borrar y no borra | Crítico | US-89 |

## Choques de numeración y renumeración

Las candidatas usan J-49 a J-51 con varios significados, D-49 y D-50 sin pedido, la ruta 18 dos veces, V1_12 que la spec 005 reserva y Q16 a Q19 que chocan con la spec 005. La spec asigna un número por decisión y una tabla de reserva.

| Número de la spec | Qué es | Números de las candidatas |
| --- | --- | --- |
| V1_12, V1_13 y V1_14 | Catálogo IND-2026, reglas de Industrial y `acceso.coordinacion_alcance` | V1_12, V1_13 y V1_14 de C-40, C-41 y C-44. La V1_12 de la spec 005 pasa a V1_15 |
| Q18 | Curso con plan de dos carreras en el mismo periodo | Q16 de C-42 y C-47 |
| Q19 | Carrera con plan de medición sin conjunto de reglas | Q17 de C-41 y C-47 |
| Q20 | Coordinación sin alcance o con secciones propias | Q18 de C-44, C-45 y C-47 |
| Q21 | Sección cuyo curso de Blackboard declara otra sección | Q19 de C-43 y C-47 |
| Ruta 18 | `GET /api/periodos` | Ruta 18 de C-01, C-28 y C-49 |
| Ruta 19 | Reservada para el archivo de los R-17 del curso, fuera de alcance | Ruta 18 de C-24 |
| BR-R17-13 | Encabezado con la carrera de la carga | BR-R17-12 de C-06, que la spec 005 reserva |
| BR-ACCESO-13 y BR-ACCESO-14 | Alcance de la coordinación y su registro | BR-ACCESO-12 de C-20, que la spec 007 reserva para la ruta 17 |
| BR-PERIODO-05 y BR-PERIODO-06 | Periodo elegido y comprobación de arranque por carrera | BR-PERIODO-05 de C-01 |
| D-48 a D-55 | Decisiones de la Oficina de Calidad y de la carrera | D-48 de C-22, D-49 de C-25 y D-50 de C-26 |
| J-49 a J-59 | Decisiones de Jefferson | J-49 de C-20, J-50 de C-26 y J-51 de C-28 |

## Veredicto del crítico de arquitectura

| Decisión | Veredicto | Razón | Alternativa |
| --- | --- | --- | --- |
| Modelo del coordinador de curso con un rol nuevo COORD_CURSO en `ck_usuario_autorizado_rol` (C-20) | CAMBIAR | La columna mide 11 caracteres y cada función de `app/permisos.py`, el tipo Rol y los ternarios del Front ganan una tercera rama, cuando el curso es un alcance y no un permiso distinto | Conservar PROFESOR y COORDINADOR y dar el alcance por `acceso.coordinacion_alcance` (C-44 y C-45), sin cambiar `ck_usuario_autorizado_rol`, Q04 ni Q15 |
| Una sola tabla de alcance con `carrera_id` o `asignatura_id` (C-44) frente a dos tablas o una columna en `usuario_autorizado` | SE_SOSTIENE | Una sola subconsulta EXISTS en `_ALCANCE`, una sola regla de control y ningún correo en la tabla | Dos tablas, a costa de duplicar la condición |
| Si la fila de alcance por asignatura lleva `periodo_id` | DUDOSA | La coordinación de un curso suele rotar entre ciclos, y sin periodo una cuenta de 2026-1 vería 5643 de los ciclos siguientes | J-49, con el periodo obligatorio en la fila de asignatura y nulo en la de carrera |
| Atar el COORDINADOR de carrera a su carrera antes de sumar Industrial (C-26 y C-44) | SE_SOSTIENE | `_ALCANCE` no mira la carrera, y con IND-2026 vigente en 2026-1 la coordinación de Ambiental vería las 18 secciones de 5643 | V1_14 y el guion que da AMB a las coordinaciones existentes corren antes del código nuevo y antes de la vigencia de IND-2026 |
| Regla del curso compartido 5643 para la coordinación de carrera (D-50 de C-26) | DUDOSA | Solo importa con las dos carreras vigentes en el mismo periodo, que no pasa en 2026-1 | J-50, con la regla actual filtrada por la carrera de la fila de alcance |
| Rótulos del Front para la coordinación de curso con `usuario.rol === 'COORDINADOR'` | CAMBIAR | La coordinación de Química leería «Secciones de la carrera» | `GET /api/sesion` suma el campo aditivo `alcance` y `rotulos.ts` elige por su tipo |
| Reemplazo por la coordinación de curso con escenarios para dos valores de D-49 (C-25) frente a heredar D-11 (C-45) | CAMBIAR | `puede_reemplazar()` ya usa el mismo alcance que `puede_leer()`, y dos valores obligan a un interruptor que nadie pidió | Valor provisional de D-11 y un solo escenario, con D-52 como confirmación de Stefanny |
| Profesor que además coordina el curso con una sola cuenta (C-27) | DUDOSA | Un solo rol por correo y la rama PROFESOR no mira la tabla de alcance | J-51, con cuentas separadas para la capacitación |
| Registro de la cuenta de coordinación por CSV con aviso (C-21) o por variable con salida 1 (C-45) | CAMBIAR | Un CSV con el correo real es un archivo más que limpiar, y un aviso que deja seguir oculta un error | `db/herramientas/registrar_coordinacion.py` con el correo en `CORREO_COORDINACION` por `en_windows.py` y salida 1 ante otro rol o una baja |
| Selector con la ruta 18 frente a `PERIODO_VIGENTE=2026-1` en develop, y si el profesor ve el selector | SE_SOSTIENE | Las rutas 4 y 12 ya aceptan periodo y cambiar la variable esconde 450002 de 2026-2 | Un solo diseño para los dos roles, el selector solo con dos periodos o más y el estado en `App.tsx` |
| Parámetro `periodo` aditivo en la ruta 8 sin `seccion_id` | SE_SOSTIENE | Sin él, P5 y la marca de rechazo de P2 quedan vacías en 2026-1 | Validar con `PERIODO` y `PERIODO_MAL_FORMADO`, con un cambio fechado en BR-CARGA-20 |
| Número de las rutas nuevas, la 18 para periodos y también para el archivo de los R-17 | CAMBIAR | Dos candidatas piden el mismo número | La 18 para `GET /api/periodos` y la 19 para el archivo, solo si entra |
| Numeración de las migraciones con V1_12 reservada por la spec 005 | CAMBIAR | `outOfOrder = false` deja sin aplicar una V1_12 posterior a una V1_13, y una versión intermedia se ordena antes de V1_11 | La spec 008 toma V1_12 a V1_14 y la spec 005 pasa a V1_15 con un cambio fechado |
| El catálogo IND-2026 como migración generada desde su referencia (C-40) | SE_SOSTIENE | Sigue el camino de AMB-2026 con `generar_v1_03.py`, y 5643 se reutiliza con `uq_asignatura_codigo` | Confirmar que el nivel de la hoja cabe en `ck_plan_estudios_ciclo` |
| El conjunto de reglas de Industrial en migración y cómo se avisa su falta (C-41) | SE_SOSTIENE | La subida da 500 sin él y la comprobación de arranque pasa con el conjunto de Ambiental | La comprobación de arranque revisa cada carrera con plan y Q19 lista la carrera sin conjunto |
| Vigencia y plan por un guion de `db/datos/` con la descripción por `\getenv` (C-42) | SE_SOSTIENE | Es la forma de BR-PERIODO-03 y la descripción no entra al repositorio | El PI como parámetro del guion |
| Secciones y profesores con `cargar_programacion.py --periodo 2026-1` y la fuente del curso de Blackboard (C-43) | SE_SOSTIENE | `uq_seccion_curso_bb` y `_CURSO` exigen el mismo curso en la base y en el export | El CSV de la programación es la única fuente del curso y el generador lo lee |
| Dónde vive el generador de exports (C-04 y C-60) | SE_SOSTIENE | Fuera del repositorio quedaría sin integración continua la pieza que más puede fallar | `scripts/generar_exports_desde_maestra.py` en el Back, con pruebas de datos inventados |
| Oráculo de la comparación de punta a punta con cuatro comparadores (C-07, C-48, C-61 y C-65) | CAMBIAR | La tabla maestra coincide alumno por alumno con los 18 R-17 a mano, así que leer esos libros suma fragilidad sin evidencia | Un solo `db/herramientas/conciliar_tabla_maestra.py`, antes y después de la sala, y la revisión visual de una sección en la guía |
| Base del ensayo con los datos reales, un clúster desechable del Windows (C-61) | DUDOSA | D-10 autoriza datos reales en Neon y en Vercel, no en un clúster local | J-52, con una rama hija de develop en Neon |
| Encabezado del R-17 desde `abet.carrera.nombre` con la misma plantilla (C-06) | SE_SOSTIENE | B6 es la única cadena de Ambiental de la plantilla y `abet.carga.carrera_id` lleva a la carrera | Ninguna |
| Respuesta al mismo export subido dos veces (C-03) | CAMBIAR | `carga.py` responde 200 con la carga existente en la misma sección | El escenario dice 200 y `abet.carga` sin filas nuevas |
| Numeración de las consultas de control nuevas | CAMBIAR | Q15 existe y la spec 005 reserva Q16 y Q17 | Desde Q18, y la sección sin carga va al avance |
| Control de un curso con plan de dos carreras (Q16 de C-47) | SE_SOSTIENE | `carga.py` toma `plan[0].carrera_id` y la ruta 4 repetiría «6.1» | El control, sin cambiar `_DETALLE` |
| Rediseño con tokens de Tailwind 4 y fuentes del sistema, sin dependencias (C-09 con C-02) | SE_SOSTIENE | Las pruebas buscan por rol y texto, y no sumar axe-core ni fuentes externas evita la espera de Dependabot | Tokens literales en `@theme` y la prueba de 375 px en Playwright |
| Consejos de P4 por motivo de fila y el texto «Corrija en Blackboard» (C-05 y C-66) | SE_SOSTIENE | `QUE_CORREGIR` cubre solo RECHAZA_CARGA y el consejo genérico no sirve a un export generado | Un consejo por motivo RECHAZA_FILA y el texto neutro con un cambio fechado |
| Botón de reemplazo en P4 antes de la spec 005 (C-05) | DUDOSA | Contradice el orden aprobado de la spec 007 | J-53, con el reemplazo desde P5 enseñado en la guía |
| Ejercicio de error con el archivo real de otra sección (C-63) | CAMBIAR | Entregaría códigos y niveles ajenos y dependería del orden de la sala | Un export inventado con códigos 99 de una sección ficticia |
| Agregado del curso en la ruta 12 (C-23) | DUDOSA | D-32 sigue abierta y la sección 12.3 del contrato deja el agregado fuera | J-54, fuera del mínimo y dentro de la spec si D-32 se responde |
| Archivo con los R-17 del curso (C-24) | DUDOSA | No hace falta para el flujo y suma una ruta | J-55, después de la capacitación como ruta 19 |
| Avance del curso con la ruta 17 y P7 de la spec 007 (C-22) | SE_SOSTIENE | Duplicar la precedencia de J-48 sería peor, y la etapa B se construye dentro de este trabajo | La etapa B con el alcance de `secciones_visibles()`, sin una rama por rol |
| Capacitación en develop junto a un humo que exige restablecer develop (C-62 y C-67) | DUDOSA | Un humo durante la ventana de registro borraría las cargas reales | J-56, con el humo una sola vez antes de la siembra y develop congelada |
| Cierre que borra los archivos reales de la Mac (C-67) | CAMBIAR | Borrar para siempre exige la confirmación de Jefferson cada vez | El cierre comprueba huellas, da de baja las cuentas e informa, sin borrar |
| Barrido de privacidad con el correo real por su huella (C-64) | SE_SOSTIENE | `preflight.sh` no conoce el correo real ni las capturas | Cuidar los falsos positivos de fechas y huellas |
| Matriz de cumplimiento generada (C-68) | SE_SOSTIENE | Es la forma repetible de comprobar que nada se olvida | Etiquetas con los IDs reales desde US-67 y fallo ante una etiqueta sin historia |
| Juego de secciones inventadas de las pruebas | CAMBIAR | Tres juegos distintos para el mismo curso multiplican pasos y datos | Un solo juego, la 701 a la 704 |

## Faltantes que la spec cubre

| Faltante | Lo señala | Dónde queda |
| --- | --- | --- |
| Qué alcanza el pedido de que todas las historias se cumplan, y que el R-17 del sistema queda sin las hojas III y IV mientras la spec 005 no se construya | Necesidad | J-57, FR-001 y «Fuera de alcance» |
| La entrega segura de las contraseñas y de los exports a cada profesor, sin dejar en un repositorio la correspondencia entre correo de ejemplo y persona | Necesidad y solapamiento | US-87, escenario 9, US-88, escenario 6, y T054 |
| Las decisiones de Stefanny con su valor provisional, que son el PI 6.1 frente al 6.2, el estadio «Inicial» y la plantilla base de Industrial | Necesidad y verificabilidad | D-48 a D-50 |
| La revisión de las demás hojas de la plantilla del R-17 | Necesidad y solapamiento | US-78, escenario 2 |
| La reserva de números de migraciones, consultas, rutas e identificadores | Las tres lentes | «Choques de numeración» y FR-021 |
| El entorno, la fecha y la ventana de la capacitación | Necesidad y solapamiento | J-56 |
| La etapa B de la spec 007 antes de la capacitación, o la alternativa de seguir el avance en P2 | Solapamiento | US-79 y FR-014 |
| Los pasos compartidos de `conftest.py` (base de la spec 008, rol con guion bajo, LISTA con tablas de `acceso` y rangos de consultas) | Verificabilidad | T013 |
| La sección 1 de `pruebas.sql` con conteos globales | Verificabilidad | US-67, escenario 3 |
| GUARDIA_DATOS_INVENTADOS en la vista previa | Verificabilidad | US-86, escenario 8 |
| La contraseña de la cuenta real de la coordinación, que `asignar_claves.py` rechaza | Verificabilidad | J-58 |
| Si el R-17 de la capacitación puede salir OFICIAL | Verificabilidad | D-54 |
| Los textos de P3 y P4 que remiten a Blackboard | Solapamiento y verificabilidad | US-77 y FR-012. P3 conserva «Antes de subir», porque el export generado sigue el formato de Blackboard |
| El comportamiento de un PI sin descriptores de rúbrica | Solapamiento | US-78, escenario 7 |
| Los privilegios de `abet_respaldo` y las listas de `probar_rol_app.sql` con la tabla nueva | Verificabilidad | US-70, escenario 8, y T023 |

## Lista final del sprint

| Historia | Título | Prioridad | Candidatas | Archivo |
| --- | --- | --- | --- | --- |
| US-67 | Catálogo IND-2026 de Ingeniería Industrial desde su referencia curricular | P1 | C-40 | `catalogo_industrial.feature` |
| US-68 | Reglas de Industrial y comprobación de arranque por carrera | P1 | C-41, C-03 (sin reglas), C-47 (Q19) | `catalogo_industrial.feature` |
| US-69 | Vigencia de IND-2026 en 2026-1 y plan de medición de 5643 | P1 | C-42, C-47 (Q18) | `catalogo_industrial.feature` |
| US-70 | La coordinación de una carrera ve solo su carrera | P1 | C-44, C-26, C-47 (Q20) | `alcance_coordinacion.feature` |
| US-71 | La coordinación de Química General ve todas las secciones de su curso | P1 | C-20, C-45 (alcance), C-25 (un escenario) | `alcance_coordinacion.feature` |
| US-72 | Registro de la coordinación del curso con corrida en seco | P1 | C-21, C-45 (guion) | `alcance_coordinacion.feature` |
| US-73 | Cada cuenta elige el periodo que trabaja | P1 | C-01, C-28, C-49, C-08 (periodo) | `periodo_elegido.feature` |
| US-74 | Exports de capacitación generados desde la tabla maestra | P1 | C-60, C-04 | `exports_capacitacion.feature` |
| US-75 | El export de 5643 se publica entero en Ingeniería Industrial | P1 | C-03 a, C-43 (programación), C-47 (Q21) | `carga_quimica.feature` |
| US-76 | Los errores probables de la sala se rechazan sin mostrar notas ni códigos | P2 | C-03 b, C-66 (Back), C-49 (otro periodo) | `carga_quimica.feature` |
| US-77 | P4 dice qué corregir en filas rechazadas y avisos sin remitir a Blackboard | P2 | C-05, C-66 (pantalla) | `carga_quimica.feature` |
| US-78 | El R-17 y P6 dicen la carrera, el SO y el PI de Industrial | P1 | C-06, C-08 (catálogo y fila) | `r17_industrial.feature` |
| US-79 | La ruta 17 y P7 alcanzan a la coordinación del curso | P2 | C-22 | `avance_del_curso.feature` |
| US-80 | Cumplimiento del curso con la suma de estudiantes, si D-32 se responde | P3 | C-23, C-65 (agregado) | `avance_del_curso.feature` |
| US-81 | Sistema visual común, claro y accesible AA | P1 | C-09 a, C-02, C-08 (fila de P6) | `sistema_visual.feature` |
| US-82 | Uso a 375 px y con teclado | P2 | C-09 b | `sistema_visual.feature` |
| US-83 | El conciliador compara la base y los R-17 con la tabla maestra sin mostrar códigos | P1 | C-48, C-65, C-07 | `ensayo_y_conciliacion.feature` |
| US-84 | Ensayo de punta a punta de los exports antes de la capacitación | P1 | C-61 | `ensayo_y_conciliacion.feature` |
| US-85 | Humo con Playwright de punta a punta en la vista previa | P1 | C-62 | `capacitacion_en_develop.feature` |
| US-86 | Siembra de Química en develop desde el Windows, en orden y sin cambiar Ambiental | P1 | C-46, C-43 | `capacitacion_en_develop.feature` |
| US-87 | Guía de la capacitación con rótulos verificados contra el Front | P1 | C-63 | `guia_y_privacidad.feature` |
| US-88 | Barrido de privacidad en los dos repositorios | P1 | C-64 | `guia_y_privacidad.feature` |
| US-89 | Cierre de la capacitación sin perder evidencia | P2 | C-67 a | `capacitacion_en_develop.feature` |
| US-90 | Matriz de cumplimiento de las specs 007 y 008 | P2 | C-68 | `matriz_cumplimiento.feature` |

Salen del sprint C-24 (archivo con los R-17 del curso), C-25 como historia propia (reemplazo con dos valores de una decisión), C-27 (profesor que coordina con una sola cuenta) y el paso de las cargas a main de C-67 (parte b), todos en «Fuera de alcance» de la spec. Ninguna candidata queda REFUTADA por mayoría, así que ninguna se descarta sin destino.

## Hechos del código que corrigen supuestos de las candidatas

- `plantillas/R017_ambiental_general.xlsx` tiene en B6 «Carrera de Ingeniería Ambiental», y `_cabecera()` de `abet_carga/r17.py` escribe D8, D9, D11, I11 y B15 sin tocar B6.
- `_frecuencias()` escribe M24 (niveles 1 y 2), M25 (niveles 3 y 4) y M26 (la fracción), y el bloque II escribe E24 con `_fraccion()` y el formato 0.0 % y G24 con la meta. K24 y K25 son rótulos.
- `_nombre()` arma `R017_{asignatura}_{seccion}_{periodo}` con el sufijo _PROVISIONAL, y con R-2026-BORRADOR en BORRADOR `abet.v_r17_por_pi` marca provisional siempre.
- `abet_carga/r17.py` y `app/` no leen `abet.rubrica_nivel`, así que un catálogo sin rúbricas no cambia el R-17.
- `carga.py` lanza ConfiguracionInvalida con «CONJUNTO_REGLAS {conjunto} no existe para la carrera {carrera}.», y `app/configuracion.py` detiene el arranque con «… no existe para Ambiental».
- `carga.py` tiene los textos `_OTRA_SECCION`, `_OTRO_PERIODO` y `_NO_ES_LA_PUBLICADA` que citan los escenarios, y `constancia.py` el de la carga sin filas aceptadas.
- `src/servicios/ayudas.ts` dice «Corrija en Blackboard…» en `CORREGIR_SIN_FILAS_ACEPTADAS` y arma «En Blackboard, una columna por PI, con el nombre …» en «Antes de subir».
- `db/plataforma/neon/controles_neon.sql` termina con «RESULTADO: Q01 a Q14 devuelven 0 filas.» y Q15 vive solo en `db/pruebas/pruebas.sql`.
- `db/migration/` llega hasta V1_11, y `flyway.toml` fija `outOfOrder = false`.

## Decisiones que salen de la revisión

D-48 a D-55 de la Oficina de Calidad y de la carrera, y J-49 a J-59 de Jefferson, con el valor que propone la spec (`spec.md`, «Decisiones abiertas»). Los veredictos CAMBIAR del crítico quedan como decisiones de la spec y no abren una J, y aprobar la spec aprueba también el cambio fechado de V1_12 a V1_15 en la spec 005.
