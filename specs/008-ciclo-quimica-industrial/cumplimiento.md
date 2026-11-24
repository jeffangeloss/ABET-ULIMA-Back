# Cumplimiento de las specs 007 y 008

Traza que genera `scripts/matriz_cumplimiento.py` (US-90, T055). No se edita a mano. Liga cada historia de las specs 007 y 008 con sus escenarios y con la prueba que los cubre, y cada regla de las specs vivas con lo que nombra su línea **Prueba**. Las excepciones llevan su razón en `cumplimiento_razones.toml`. El resultado y la fecha de cada corrida quedan en el informe de la integración continua y no en este archivo.

## Tramo de la capacitación

| Tramo | Historias | Escenarios | Estado |
|---|---|---|---|
| Catálogo | US-67, US-68, US-69 | 20 | Con prueba |
| Alcance | US-70, US-71, US-72 | 30 | Con prueba |
| Periodo | US-73 | 17 | Con prueba |
| Generador | US-74 | 14 | Con prueba |
| Carga | US-75, US-76, US-77 | 19 | Con prueba |
| R-17 | US-78 | 11 | Con prueba |
| Avance | US-79, US-80 | 13 | Con prueba salvo US-80, pendiente por decisión |
| Sistema visual | US-81, US-82 | 16 | Con prueba |
| Conciliación | US-83 | 10 | Con prueba |
| Ensayo | US-84 | 4 | Con prueba |
| Siembra | US-86 | 9 | Con prueba |
| Humo | US-85 | 8 | Con prueba |
| Guía | US-87 | 9 | Con prueba |
| Privacidad | US-88 | 8 | Con prueba |
| Cierre | US-89 | 5 | Con prueba |

## Historias

| Historia | Spec | Título | Escenarios | Archivos de los escenarios | Pruebas | Razón | Estado |
|---|---|---|---|---|---|---|---|
| US-59 | 007 | P2 dice al profesor lo que falta en cada sección | 6 | siguiente_paso.feature | Vitest tests/pantallas/MisSecciones.test.tsx | Ninguna | Con prueba |
| US-60 | 007 | P3 dice antes de subir qué debe tener listo el profesor en Blackboard | 5 | antes_de_subir.feature | Vitest tests/pantallas/SubirExport.test.tsx, pytest-bdd tests/aceptacion/pasos/test_experiencia_por_cuenta_feature.py | Ninguna | Con prueba |
| US-61 | 007 | P4 de una carga rechazada dice qué corregir | 4 | que_corregir.feature | Vitest tests/pantallas/ResultadoCarga.test.tsx | Ninguna | Con prueba |
| US-62 | 007 | P4 y P3 no afirman nada falso sobre la carga publicada | 4 | que_corregir.feature | Vitest tests/pantallas/ResultadoCarga.test.tsx, Vitest tests/App.test.tsx, Vitest tests/pantallas/SubirExport.test.tsx | Ninguna | Con prueba |
| US-63 | 007 | Cada cuenta lee rótulos de su rol y sabe en qué pantalla está | 4 | rotulos_por_cuenta.feature | Vitest tests/App.test.tsx, Vitest tests/pantallas/MisSecciones.test.tsx, Vitest tests/pantallas/Cargas.test.tsx, Vitest tests/pantallas/MisLogros.test.tsx, Vitest tests/pantallas/Avance.test.tsx | Ninguna | Con prueba |
| US-64 | 007 | La ruta 17 da a la coordinación la etapa de cada sección | 4 | avance_del_registro.feature | pytest-bdd tests/aceptacion/pasos/test_avance_feature.py | Ninguna | Con prueba |
| US-65 | 007 | La coordinación entra a P7 y ve cuántas secciones faltan | 5 | avance_del_registro.feature | Vitest tests/pantallas/Avance.test.tsx | Espera a US-52 de la spec 005, la navegación por fragmento, y la spec 005 queda fuera de la spec 008 (FR-001). En el Front es un it.todo de tests/pantallas/Avance.test.tsx. | Con prueba y 1 pendiente por decisión |
| US-66 | 007 | P7 dice a quién recordar el registro | 3 | avance_del_registro.feature | Ninguna | Espera a D-47 y a D-51 de la spec 007 (FR-001 de la spec 008). | Pendiente por decisión |
| US-67 | 008 | Catálogo IND-2026 de Ingeniería Industrial desde su referencia curricular | 6 | catalogo_industrial.feature | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py | Ninguna | Con prueba |
| US-68 | 008 | Reglas de Industrial y comprobación de arranque por carrera | 6 | catalogo_industrial.feature | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py | Ninguna | Con prueba |
| US-69 | 008 | Vigencia de IND-2026 en 2026-1 y plan de medición de 5643 | 8 | catalogo_industrial.feature | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py | Ninguna | Con prueba |
| US-70 | 008 | La coordinación de una carrera ve solo su carrera | 8 | alcance_coordinacion.feature | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py | Ninguna | Con prueba |
| US-71 | 008 | La coordinación de Química General ve todas las secciones de su curso | 14 | alcance_coordinacion.feature | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py, Vitest tests/spec008/alcance_coordinacion.test.tsx | Ninguna | Con prueba |
| US-72 | 008 | Registro de la coordinación del curso con corrida en seco | 8 | alcance_coordinacion.feature | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py | Ninguna | Con prueba |
| US-73 | 008 | Cada cuenta elige el periodo que trabaja | 17 | periodo_elegido.feature | pytest-bdd tests/aceptacion/pasos/test_periodo_elegido_feature.py, Vitest tests/spec008/periodo_elegido.test.tsx | Ninguna | Con prueba |
| US-74 | 008 | Exports de capacitación generados desde la tabla maestra | 14 | exports_capacitacion.feature | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py | Ninguna | Con prueba |
| US-75 | 008 | El export de 5643 se publica entero en Ingeniería Industrial | 4 | carga_quimica.feature | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py | Ninguna | Con prueba |
| US-76 | 008 | Los errores probables de la sala se rechazan sin mostrar notas ni códigos | 9 | carga_quimica.feature | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py | Ninguna | Con prueba |
| US-77 | 008 | P4 dice qué corregir en filas rechazadas y avisos sin remitir a Blackboard | 6 | carga_quimica.feature | Vitest tests/spec008/carga_quimica.test.tsx | Ninguna | Con prueba |
| US-78 | 008 | El R-17 y P6 dicen la carrera, el SO y el PI de Industrial | 11 | r17_industrial.feature | pytest-bdd tests/aceptacion/pasos/test_r17_industrial_feature.py, Vitest tests/spec008/r17_industrial.test.tsx | Ninguna | Con prueba |
| US-79 | 008 | La ruta 17 y P7 alcanzan a la coordinación del curso | 7 | avance_del_curso.feature | pytest-bdd tests/aceptacion/pasos/test_avance_feature.py, Vitest tests/spec008/avance_del_curso.test.tsx | Ninguna | Con prueba |
| US-80 | 008 | Cumplimiento del curso con la suma de estudiantes, si D-32 se responde | 6 | avance_del_curso.feature | Ninguna | Se construye solo si D-32 se responde (J-54, T039 y T047). | Pendiente por decisión |
| US-81 | 008 | Sistema visual común, claro y accesible AA | 12 | sistema_visual.feature | Vitest tests/spec008/sistema_visual.test.tsx | Ninguna | Con prueba |
| US-82 | 008 | Uso a 375 px y con teclado | 4 | sistema_visual.feature | Playwright e2e/visual.spec.ts | Ninguna | Con prueba |
| US-83 | 008 | El conciliador compara la base y los R-17 con la tabla maestra sin mostrar códigos | 10 | ensayo_y_conciliacion.feature | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py | Ninguna | Con prueba |
| US-84 | 008 | Ensayo de punta a punta de los exports antes de la capacitación | 4 | ensayo_y_conciliacion.feature | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py | Ninguna | Con prueba |
| US-85 | 008 | Humo con Playwright de punta a punta en la vista previa | 8 | capacitacion_en_develop.feature | Playwright e2e/humo_quimica.spec.ts | Ninguna | Con prueba |
| US-86 | 008 | Siembra de Química en develop desde el Windows, en orden y sin cambiar Ambiental | 9 | capacitacion_en_develop.feature | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py | Ninguna | Con prueba |
| US-87 | 008 | Guía de la capacitación con rótulos verificados contra el Front | 9 | guia_y_privacidad.feature | Vitest tests/spec008/guia_y_privacidad.test.ts, Playwright e2e/humo_quimica.spec.ts, pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py | Ninguna | Con prueba |
| US-88 | 008 | Barrido de privacidad en los dos repositorios | 8 | guia_y_privacidad.feature | pytest-bdd tests/aceptacion/pasos/test_guia_y_privacidad_feature.py | Ninguna | Con prueba |
| US-89 | 008 | Cierre de la capacitación sin perder evidencia | 5 | capacitacion_en_develop.feature | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py | Ninguna | Con prueba |
| US-90 | 008 | Matriz de cumplimiento de las specs 007 y 008 | 9 | matriz_cumplimiento.feature | pytest-bdd tests/aceptacion/pasos/test_matriz_cumplimiento_feature.py | Ninguna | Con prueba |

## Reglas de las specs vivas

| Regla | Spec viva | Escenarios | Pruebas nombradas | Estado |
|---|---|---|---|---|
| BR-ACCESO-01 | acceso | 5 | Ninguna | Con escenario |
| BR-ACCESO-02 | acceso | 1 | Ninguna | Con escenario |
| BR-ACCESO-03 | acceso | 3 | Ninguna | Con escenario |
| BR-ACCESO-04 | acceso | 2 | Ninguna | Con escenario |
| BR-ACCESO-05 | acceso | 1 | Ninguna | Con escenario |
| BR-ACCESO-06 | acceso | 5 | Ninguna | Con escenario |
| BR-ACCESO-07 | acceso | 11 | Ninguna | Con escenario |
| BR-ACCESO-08 | acceso | 15 | Ninguna | Con escenario |
| BR-ACCESO-09 | acceso | 5 | Ninguna | Con escenario |
| BR-ACCESO-10 | acceso | 1 | tests/test_rutas_protegidas.py | Con escenario |
| BR-ACCESO-11 | acceso | 19 | tests/test_cargar_programacion.py | Con escenario |
| BR-ACCESO-12 | acceso | 2 | Ninguna | Con escenario |
| BR-ACCESO-13 | acceso | 11 | Ninguna | Con escenario |
| BR-ACCESO-14 | acceso | 8 | Ninguna | Con escenario |
| BR-AVANCE-01 | avance | 3 | Ninguna | Con escenario |
| BR-AVANCE-02 | avance | 4 | Ninguna | Con escenario |
| BR-AVANCE-03 | avance | 2 | Ninguna | Con escenario |
| BR-AVANCE-04 | avance | 2 | Ninguna | Con escenario |
| BR-AVANCE-05 | avance | 1 | Ninguna | Con escenario |
| BR-CARGA-01 | carga-export | 3 | Ninguna | Con escenario |
| BR-CARGA-02 | carga-export | 3 | Ninguna | Con escenario |
| BR-CARGA-03 | carga-export | 8 | Ninguna | Con escenario |
| BR-CARGA-04 | carga-export | 1 | Ninguna | Con escenario |
| BR-CARGA-05 | carga-export | 5 | Ninguna | Con escenario |
| BR-CARGA-06 | carga-export | 4 | Ninguna | Con escenario |
| BR-CARGA-07 | carga-export | 7 | Ninguna | Con escenario |
| BR-CARGA-08 | carga-export | 2 | Ninguna | Con escenario |
| BR-CARGA-09 | carga-export | 6 | Ninguna | Con escenario |
| BR-CARGA-10 | carga-export | 4 | Ninguna | Con escenario |
| BR-CARGA-11 | carga-export | 9 | Ninguna | Con escenario |
| BR-CARGA-12 | carga-export | 1 | Ninguna | Con escenario |
| BR-CARGA-13 | carga-export | 3 | Ninguna | Con escenario |
| BR-CARGA-14 | carga-export | 9 | Ninguna | Con escenario |
| BR-CARGA-15 | carga-export | 9 | Ninguna | Con escenario |
| BR-CARGA-16 | carga-export | 6 | Ninguna | Con escenario |
| BR-CARGA-17 | carga-export | 5 | Ninguna | Con escenario |
| BR-CARGA-18 | carga-export | 6 | Ninguna | Con escenario |
| BR-CARGA-19 | carga-export | 11 | Ninguna | Con escenario |
| BR-CARGA-20 | carga-export | 8 | Ninguna | Con escenario |
| BR-PERIODO-01 | periodo | 1 | tests/test_api_resultados.py | Con escenario |
| BR-PERIODO-02 | periodo | 6 | Ninguna | Con escenario |
| BR-PERIODO-03 | periodo | 4 | Ninguna | Con escenario |
| BR-PERIODO-04 | periodo | 9 | Ninguna | Con escenario |
| BR-PERIODO-05 | periodo | 8 | Ninguna | Con escenario |
| BR-PERIODO-06 | periodo | 7 | Ninguna | Con escenario |
| BR-R17-01 | r17 | 3 | Ninguna | Con escenario |
| BR-R17-02 | r17 | 5 | test_br_r17_02_m24_a_m26_siguen_el_corte_fijo_con_reglas_aprobadas, tests/test_r17.py | Con escenario |
| BR-R17-03 | r17 | 3 | Ninguna | Con escenario |
| BR-R17-04 | r17 | 1 | Ninguna | Con escenario |
| BR-R17-05 | r17 | 2 | Ninguna | Con escenario |
| BR-R17-06 | r17 | 3 | test_br_r17_06_el_r17_no_deja_que_el_navegador_adivine_su_tipo, tests/test_api_cargas.py | Con escenario |
| BR-R17-07 | r17 | 2 | Ninguna | Con escenario |
| BR-R17-08 | r17 | 2 | Ninguna | Con escenario |
| BR-R17-09 | r17 | 2 | Ninguna | Con escenario |
| BR-R17-10 | r17 | 7 | Ninguna | Con escenario |
| BR-R17-11 | r17 | 4 | tests/test_r17.py, tests/test_descripcion_instrumento.py | Con escenario |
| BR-R17-13 | r17 | 8 | Ninguna | Con escenario |
| BR-RESULTADOS-01 | resultados | 5 | tests/test_api_resultados.py | Con escenario |
| BR-RESULTADOS-02 | resultados | 4 | tests/test_api_resultados.py | Con escenario |
| BR-RESULTADOS-03 | resultados | 5 | tests/test_api_resultados.py | Con escenario |
| BR-RESULTADOS-04 | resultados | 2 | tests/test_api_resultados.py | Con escenario |
| BR-RESULTADOS-05 | resultados | 3 | tests/test_resultados.py, tests/test_api_resultados.py | Con escenario |
| BR-RESULTADOS-06 | resultados | 2 | tests/test_resultados.py | Con escenario |
| BR-RESULTADOS-07 | resultados | 6 | Ninguna | Con escenario |
| BR-RESULTADOS-08 | resultados | 3 | Ninguna | Con escenario |
| BR-RESULTADOS-09 | resultados | 3 | Ninguna | Con escenario |
| BR-RESULTADOS-10 | resultados | 2 | Ninguna | Con escenario |
| BR-RESULTADOS-11 | resultados | 0 | tests/pantallas/MisLogros.test.tsx, tests/App.test.tsx, e2e/humo.spec.ts | Con prueba nombrada |

## Escenarios

| Historia | Archivo | Escenario | Prueba | Estado |
|---|---|---|---|---|
| US-59 | siguiente_paso.feature | La línea de lo que falta sale del estado de la sección | Vitest tests/pantallas/MisSecciones.test.tsx › la sección $caso conserva su texto y dice debajo lo que falta | Con prueba |
| US-59 | siguiente_paso.feature | El botón de la fila anuncia lo que falta y, desactivado, su motivo | Vitest tests/pantallas/MisSecciones.test.tsx › el botón anuncia el siguiente paso de su propia sección o el motivo de su desactivación | Con prueba |
| US-59 | siguiente_paso.feature | «Ver por qué se rechazó» abre P4 de la carga rechazada más reciente | Vitest tests/pantallas/MisSecciones.test.tsx › abre P4 de la primera rechazada de esa sección en el orden de la ruta 8 | Con prueba |
| US-59 | siguiente_paso.feature | Si la ruta 8 falla, P2 sigue con la ruta 4 y no muestra error | Vitest tests/pantallas/MisSecciones.test.tsx › conserva las secciones y permite subir si la ruta 8 da 500 | Con prueba |
| US-59 | siguiente_paso.feature | Sin secciones asignadas, P2 dice a quién acudir y no pide la ruta 8 | Vitest tests/pantallas/MisSecciones.test.tsx › sin secciones muestra un texto y no una lista vacía | Con prueba |
| US-59 | siguiente_paso.feature | La coordinación no recibe las líneas del profesor | Vitest tests/pantallas/MisSecciones.test.tsx › el coordinador no ve Subir export y sí el resultado y la descarga del R-17 publicada | Con prueba |
| US-60 | antes_de_subir.feature | P3 lista antes del campo de archivo lo que el profesor debe tener listo | Vitest tests/pantallas/SubirExport.test.tsx › US-60: en $modo, Antes de subir presenta las cuatro líneas en orden antes del campo de archivo | Con prueba |
| US-60 | antes_de_subir.feature | La primera línea nombra los PI de la sección elegida | Vitest tests/pantallas/SubirExport.test.tsx › US-60: la primera línea usa los PI de la sección y dice $nombres | Con prueba |
| US-60 | antes_de_subir.feature | El apartado sale solo del plan y no lee el archivo | Vitest tests/pantallas/SubirExport.test.tsx › US-60: elegir un archivo conserva el apartado del plan y no envía peticiones hasta Subir | Con prueba |
| US-60 | antes_de_subir.feature | El modo reemplazo muestra el mismo apartado | Vitest tests/pantallas/SubirExport.test.tsx › US-60: en $modo, Antes de subir presenta las cuatro líneas en orden antes del campo de archivo | Con prueba |
| US-60 | antes_de_subir.feature | El lector de exports reconoce el nombre que propone P3 y no el que lleva guiones | pytest-bdd tests/aceptacion/pasos/test_experiencia_por_cuenta_feature.py::test_el_lector_reconoce_el_nombre_que_propone_p3 | Con prueba |
| US-61 | que_corregir.feature | Cada motivo de rechazo de toda la carga trae su forma de corregir | Vitest tests/pantallas/ResultadoCarga.test.tsx › la tabla de J-43 tiene un consejo para cada uno de los siete motivos RECHAZA_CARGA del contrato; Vitest tests/pantallas/ResultadoCarga.test.tsx › %s con %s conserva el mensaje de la API, muestra debajo qué corregir y los conteos | Con prueba |
| US-61 | que_corregir.feature | Si ninguna fila se acepta, P4 remite a la tabla de rechazos y conserva los conteos | Vitest tests/pantallas/ResultadoCarga.test.tsx › sin filas aceptadas muestra el mensaje de la API junto con la tabla de rechazos | Con prueba |
| US-61 | que_corregir.feature | Un motivo que el Front no conoce muestra solo el mensaje de la API | Vitest tests/pantallas/ResultadoCarga.test.tsx › un motivo que el Front no conoce muestra solo el mensaje de la API, también con PI | Con prueba |
| US-61 | que_corregir.feature | Una carga publicada sin rechazos ni avisos no muestra «Qué corregir» | Vitest tests/pantallas/ResultadoCarga.test.tsx › una carga publicada sin rechazos ni avisos no muestra «Qué corregir» | Con prueba |
| US-62 | que_corregir.feature | Una carga sin R-17 lo dice sin afirmar nada sobre la sección | Vitest tests/pantallas/ResultadoCarga.test.tsx › la carga 12 %s sin sucesora lo dice sin afirmar nada sobre la sección | Con prueba |
| US-62 | que_corregir.feature | Un reemplazo rechazado no dice que la sección quedó sin carga publicada | Vitest tests/App.test.tsx › US-62 muestra el resultado del reemplazo rechazado de la carga 7 sin afirmar que la sección perdió su publicación | Con prueba |
| US-62 | que_corregir.feature | Una carga reemplazada con sucesora conocida conserva su texto de hoy | Vitest tests/pantallas/ResultadoCarga.test.tsx › una carga REEMPLAZADA nombra a su sucesora como la publicada y no ofrece el R-17 | Con prueba |
| US-62 | que_corregir.feature | P3 en modo reemplazo dice que la carga publicada no se pierde | Vitest tests/pantallas/SubirExport.test.tsx › en modo reemplazo dice qué carga reemplaza y envía reemplaza desde la primera subida | Con prueba |
| US-63 | rotulos_por_cuenta.feature | La cabecera nombra lo que ve cada cuenta | Vitest tests/App.test.tsx › con el rol $usuario.rol la cabecera dice «$secciones», «Cargas» y «$logros», y P2 lleva el título de su botón | Con prueba |
| US-63 | rotulos_por_cuenta.feature | Una lista vacía se explica según la cuenta | Vitest tests/pantallas/MisSecciones.test.tsx › sin secciones muestra un texto y no una lista vacía; Vitest tests/pantallas/MisSecciones.test.tsx › al coordinador sin secciones le habla de la carrera, sin la línea del profesor ni la ruta 8; Vitest tests/pantallas/Cargas.test.tsx › sin secciones dice que no tiene secciones asignadas; Vitest tests/pantallas/Cargas.test.tsx › al coordinador sin secciones le dice que la carrera no tiene secciones; Vitest tests/pantallas/MisLogros.test.tsx › con el rol $usuario.rol espera con «$espera» y sin secciones dice «$vacia» | Con prueba |
| US-63 | rotulos_por_cuenta.feature | El aviso de espera de P6 habla de la cuenta que lo lee | Vitest tests/pantallas/MisLogros.test.tsx › con el rol $usuario.rol espera con «$espera» y sin secciones dice «$vacia» | Con prueba |
| US-63 | rotulos_por_cuenta.feature | El menú marca la pantalla actual | Vitest tests/App.test.tsx › US-63 marca solo la pantalla abierta en el menú del profesor, incluso al entrar y salir de P3 y P4; Vitest tests/pantallas/Avance.test.tsx › El menú marca la pantalla actual (P7 «Avance del registro») | Con prueba |
| US-64 | avance_del_registro.feature | La ruta 17 da la etapa de cada sección en el orden de asignatura y número | pytest-bdd tests/aceptacion/pasos/test_avance_feature.py::test_la_ruta_17_da_la_etapa_de_cada_seccion | Con prueba |
| US-64 | avance_del_registro.feature | La precedencia de J-48 decide la etapa de cada sección | pytest-bdd tests/aceptacion/pasos/test_avance_feature.py::test_la_precedencia_de_j_48_decide_la_etapa | Con prueba |
| US-64 | avance_del_registro.feature | Solo la coordinación lee el avance, en el orden 401, 403 y 422 | pytest-bdd tests/aceptacion/pasos/test_avance_feature.py::test_solo_la_coordinacion_lee_el_avance | Con prueba |
| US-64 | avance_del_registro.feature | Sin periodo, la ruta 17 usa el periodo vigente | pytest-bdd tests/aceptacion/pasos/test_avance_feature.py::test_sin_periodo_la_ruta_17_usa_el_vigente | Con prueba |
| US-65 | avance_del_registro.feature | P7 muestra el avance con texto, agrupado por asignatura | Vitest tests/pantallas/Avance.test.tsx | Con prueba |
| US-65 | avance_del_registro.feature | El filtro deja solo las secciones que faltan | Vitest tests/pantallas/Avance.test.tsx | Con prueba |
| US-65 | avance_del_registro.feature | Cada cuenta entra a su página | Vitest tests/pantallas/Avance.test.tsx › Cada cuenta entra a su página ($rol) | Con prueba |
| US-65 | avance_del_registro.feature | Atrás desde P4 abierta con «Ver la carga» vuelve a P7 | Ninguna | Pendiente por decisión |
| US-65 | avance_del_registro.feature | P7 sin secciones lo dice con el texto de la carrera | Vitest tests/pantallas/Avance.test.tsx | Con prueba |
| US-66 | avance_del_registro.feature | La ruta 17 trae solo los correos de los profesores activos de las secciones que faltan | Ninguna | Pendiente por decisión |
| US-66 | avance_del_registro.feature | P7 muestra los correos en las filas que faltan y los copia sin repetirlos | Ninguna | Pendiente por decisión |
| US-66 | avance_del_registro.feature | Sin portapapeles, los correos quedan seleccionables y no se guardan | Ninguna | Pendiente por decisión |
| US-67 | catalogo_industrial.feature | La migración V1_12 carga el catálogo IND-2026 con sus conteos | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_v1_12_carga_ind_2026_con_sus_conteos | Con prueba |
| US-67 | catalogo_industrial.feature | Una asignatura compartida se reutiliza sin tocar Ambiental | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_una_asignatura_compartida_se_reutiliza_sin_tocar_ambiental | Con prueba |
| US-67 | catalogo_industrial.feature | La sección 1 de pruebas.sql cuenta por catálogo y no en toda la base | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_la_seccion_1_de_pruebas_sql_cuenta_por_catalogo | Con prueba |
| US-67 | catalogo_industrial.feature | El generador de V1_12 es determinista | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_el_generador_de_v1_12_es_determinista | Con prueba |
| US-67 | catalogo_industrial.feature | El generador rechaza una referencia mal formada antes de escribir | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_el_generador_rechaza_una_referencia_mal_formada | Con prueba |
| US-67 | catalogo_industrial.feature | La aserción final detiene la migración si un conteo no coincide | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_la_asercion_final_detiene_la_migracion | Con prueba |
| US-68 | catalogo_industrial.feature | La migración V1_13 siembra el conjunto de reglas de Industrial | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_v1_13_siembra_el_conjunto_de_industrial | Con prueba |
| US-68 | catalogo_industrial.feature | Una carga de 5643 toma las reglas de Industrial y la vista da la regla de la meta | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_una_carga_de_5643_toma_las_reglas_de_industrial | Con prueba |
| US-68 | catalogo_industrial.feature | Una carga de 450002 sigue con las reglas de Ambiental | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_una_carga_de_450002_sigue_con_las_reglas_de_ambiental | Con prueba |
| US-68 | catalogo_industrial.feature | Sin el conjunto de Industrial la biblioteca no guarda nada y la ruta responde el error interno | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_sin_el_conjunto_de_industrial_la_biblioteca_no_guarda_nada | Con prueba |
| US-68 | catalogo_industrial.feature | El arranque de la API revisa el conjunto de reglas de cada carrera con plan | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_el_arranque_revisa_el_conjunto_de_cada_carrera | Con prueba |
| US-68 | catalogo_industrial.feature | Q19 lista una carrera con plan de medición sin conjunto de reglas | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_q19_lista_una_carrera_con_plan_sin_conjunto_de_reglas | Con prueba |
| US-69 | catalogo_industrial.feature | La corrida en seco del plan de Química informa y no escribe | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_la_corrida_en_seco_del_plan_informa_y_no_escribe | Con prueba |
| US-69 | catalogo_industrial.feature | Con aplicar quedan la vigencia y el plan de 5643 con el PI 6.1 | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_con_aplicar_quedan_la_vigencia_y_el_plan | Con prueba |
| US-69 | catalogo_industrial.feature | Repetir el guion del plan no duplica ni cambia filas | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_repetir_el_guion_del_plan_no_duplica | Con prueba |
| US-69 | catalogo_industrial.feature | Una fila de plan distinta detiene todo | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_una_fila_de_plan_distinta_detiene_todo | Con prueba |
| US-69 | catalogo_industrial.feature | Una descripción del instrumento inválida no entra | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_una_descripcion_del_instrumento_invalida_no_entra | Con prueba |
| US-69 | catalogo_industrial.feature | Sin el par 5643 y SO 6 en el catálogo el plan no entra | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_sin_el_par_5643_y_so_6_el_plan_no_entra | Con prueba |
| US-69 | catalogo_industrial.feature | Ambiental en 2026-2 queda igual tras el plan de Química | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_ambiental_en_2026_2_queda_igual_tras_el_plan | Con prueba |
| US-69 | catalogo_industrial.feature | Q18 detecta un curso con plan de dos carreras en el mismo periodo | pytest-bdd tests/aceptacion/pasos/test_catalogo_industrial_feature.py::test_q18_detecta_un_curso_con_plan_de_dos_carreras | Con prueba |
| US-70 | alcance_coordinacion.feature | La coordinación de Ambiental no ve las secciones de Química General | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_la_coordinacion_de_ambiental_no_ve_quimica | Con prueba |
| US-70 | alcance_coordinacion.feature | La coordinación de Ambiental conserva lo que ya veía | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_la_coordinacion_de_ambiental_conserva_lo_que_veia | Con prueba |
| US-70 | alcance_coordinacion.feature | Una sección o una carga de Química pedida por la coordinación de Ambiental responde el 403 de siempre | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_quimica_pedida_por_ambiental_responde_403 | Con prueba |
| US-70 | alcance_coordinacion.feature | Un coordinador sin alcance no ve ninguna sección y Q20 lo lista | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_un_coordinador_sin_alcance_no_ve_nada | Con prueba |
| US-70 | alcance_coordinacion.feature | Con las dos carreras vigentes en el mismo periodo, el curso compartido sigue el valor provisional de J-50 | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_el_curso_compartido_sigue_j_50 | Con prueba |
| US-70 | alcance_coordinacion.feature | El guion de alcance de Ambiental corre antes del código nuevo y no deja a la coordinación sin alcance | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_el_guion_de_alcance_de_ambiental_corre_antes | Con prueba |
| US-70 | alcance_coordinacion.feature | La base exige un solo alcance por fila | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_la_base_exige_un_solo_alcance_por_fila | Con prueba |
| US-70 | alcance_coordinacion.feature | El rol de la aplicación solo lee el alcance | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_el_rol_de_la_aplicacion_solo_lee_el_alcance | Con prueba |
| US-71 | alcance_coordinacion.feature | La coordinación del curso ve las secciones de 5643 en orden y ninguna otra | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_la_coordinacion_del_curso_ve_sus_secciones | Con prueba |
| US-71 | alcance_coordinacion.feature | La sesión dice el alcance del curso sin un rol nuevo | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_la_sesion_dice_el_alcance | Con prueba |
| US-71 | alcance_coordinacion.feature | Una cuenta con alcance de carrera y de curso recibe el tipo más amplio | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_carrera_y_curso_recibe_el_tipo_mas_amplio | Con prueba |
| US-71 | alcance_coordinacion.feature | La asignación vale solo en su periodo | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_la_asignacion_vale_solo_en_su_periodo | Con prueba |
| US-71 | alcance_coordinacion.feature | Lee la constancia y el R-17 de una sección de su curso | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_lee_la_constancia_y_el_r17_de_su_curso | Con prueba |
| US-71 | alcance_coordinacion.feature | La coordinación del curso no alcanza otro curso | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_la_coordinacion_del_curso_no_alcanza_otro_curso | Con prueba |
| US-71 | alcance_coordinacion.feature | La coordinación del curso no sube una carga nueva | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_la_coordinacion_del_curso_no_sube | Con prueba |
| US-71 | alcance_coordinacion.feature | La coordinación del curso reemplaza en su curso con el valor provisional de D-52 | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_la_coordinacion_del_curso_reemplaza | Con prueba |
| US-71 | alcance_coordinacion.feature | Una cuenta de coordinación dada de baja no alcanza nada | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_una_coordinacion_dada_de_baja_no_alcanza_nada | Con prueba |
| US-71 | alcance_coordinacion.feature | El profesor del curso sigue viendo solo su sección | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_el_profesor_del_curso_sigue_viendo_su_seccion | Con prueba |
| US-71 | alcance_coordinacion.feature | Q20 lista una coordinación de curso con una sección propia en acceso.docente_seccion | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_q20_lista_una_coordinacion_de_curso_con_una_seccion_propia | Con prueba |
| US-71 | alcance_coordinacion.feature | P2 rotula el curso y no ofrece subir | Vitest tests/spec008/alcance_coordinacion.test.tsx | Con prueba |
| US-71 | alcance_coordinacion.feature | La coordinación de la carrera conserva sus rótulos | Vitest tests/spec008/alcance_coordinacion.test.tsx | Con prueba |
| US-71 | alcance_coordinacion.feature | El consejo de una sección cruzada remite al profesor también para la coordinación del curso | Vitest tests/spec008/alcance_coordinacion.test.tsx | Con prueba |
| US-72 | alcance_coordinacion.feature | La corrida en seco del registro de la coordinación informa sin repetir el correo | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_registro_en_seco | Con prueba |
| US-72 | alcance_coordinacion.feature | Con --aplicar escribe una vez y se puede repetir | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_registro_aplicado_dos_veces | Con prueba |
| US-72 | alcance_coordinacion.feature | Un correo que ya es profesor detiene el guion sin cambiar su rol | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_registro_de_un_profesor | Con prueba |
| US-72 | alcance_coordinacion.feature | Una cuenta dada de baja no se reactiva | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_registro_de_una_baja | Con prueba |
| US-72 | alcance_coordinacion.feature | Un argumento inválido se rechaza antes de escribir | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_registro_con_un_argumento_invalido | Con prueba |
| US-72 | alcance_coordinacion.feature | Sin la variable del correo el guion no adivina | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_registro_sin_la_variable | Con prueba |
| US-72 | alcance_coordinacion.feature | Una asignatura sin plan de medición entra con aviso | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_registro_de_una_asignatura_sin_plan | Con prueba |
| US-72 | alcance_coordinacion.feature | El guion no escribe contraseñas ni las muestra | pytest-bdd tests/aceptacion/pasos/test_alcance_coordinacion_feature.py::test_registro_sin_contrasenas | Con prueba |
| US-73 | periodo_elegido.feature | La ruta 18 lista solo los periodos con secciones al alcance de cada cuenta | pytest-bdd tests/aceptacion/pasos/test_periodo_elegido_feature.py::test_la_ruta_18_lista_los_periodos_al_alcance | Con prueba |
| US-73 | periodo_elegido.feature | Con secciones en los dos periodos los recibe del más reciente al más antiguo | pytest-bdd tests/aceptacion/pasos/test_periodo_elegido_feature.py::test_con_dos_periodos_del_mas_reciente_al_mas_antiguo | Con prueba |
| US-73 | periodo_elegido.feature | Sin sesión la ruta 18 responde 401 y figura en la prueba de rutas registradas | pytest-bdd tests/aceptacion/pasos/test_periodo_elegido_feature.py::test_sin_sesion_la_ruta_18_responde_401 | Con prueba |
| US-73 | periodo_elegido.feature | La ruta 8 con periodo lista solo las cargas de ese periodo y sin periodo sigue como hoy | pytest-bdd tests/aceptacion/pasos/test_periodo_elegido_feature.py::test_la_ruta_8_con_periodo | Con prueba |
| US-73 | periodo_elegido.feature | Un periodo mal formado responde 422 en las rutas que lo aceptan | pytest-bdd tests/aceptacion/pasos/test_periodo_elegido_feature.py::test_un_periodo_mal_formado_responde_422 | Con prueba |
| US-73 | periodo_elegido.feature | Un periodo sin secciones del usuario da una lista vacía y no un 403 | pytest-bdd tests/aceptacion/pasos/test_periodo_elegido_feature.py::test_un_periodo_sin_secciones_da_una_lista_vacia | Con prueba |
| US-73 | periodo_elegido.feature | Pedir otro periodo no agrega secciones ajenas | pytest-bdd tests/aceptacion/pasos/test_periodo_elegido_feature.py::test_pedir_otro_periodo_no_agrega_secciones_ajenas | Con prueba |
| US-73 | periodo_elegido.feature | La subida en una sección de 2026-1 no exige el periodo vigente | pytest-bdd tests/aceptacion/pasos/test_periodo_elegido_feature.py::test_la_subida_en_2026_1_no_exige_el_vigente | Con prueba |
| US-73 | periodo_elegido.feature | Un export de otro periodo se rechaza con el texto de la API | pytest-bdd tests/aceptacion/pasos/test_periodo_elegido_feature.py::test_un_export_de_otro_periodo_se_rechaza | Con prueba |
| US-73 | periodo_elegido.feature | Sin secciones en el periodo vigente, P2 abre en el periodo más reciente con secciones | Vitest tests/spec008/periodo_elegido.test.tsx | Con prueba |
| US-73 | periodo_elegido.feature | Con dos periodos la cabecera ofrece el selector y abre en el vigente | Vitest tests/spec008/periodo_elegido.test.tsx | Con prueba |
| US-73 | periodo_elegido.feature | Cambiar el periodo vuelve a pedir P2, P5 y P6 con el periodo elegido | Vitest tests/spec008/periodo_elegido.test.tsx | Con prueba |
| US-73 | periodo_elegido.feature | La marca de la última carga rechazada de P2 sale del periodo elegido | Vitest tests/spec008/periodo_elegido.test.tsx | Con prueba |
| US-73 | periodo_elegido.feature | El periodo elegido se conserva en el recorrido y no se guarda en el navegador | Vitest tests/spec008/periodo_elegido.test.tsx | Con prueba |
| US-73 | periodo_elegido.feature | Si la ruta 18 falla, P2 usa el periodo vigente como hoy y no muestra error | Vitest tests/spec008/periodo_elegido.test.tsx | Con prueba |
| US-73 | periodo_elegido.feature | En un periodo sin secciones, P2 remite al selector | Vitest tests/spec008/periodo_elegido.test.tsx | Con prueba |
| US-73 | periodo_elegido.feature | La coordinación del curso trabaja 2026-1 en P2, P5, P6 y P7 | Vitest tests/spec008/periodo_elegido.test.tsx | Con prueba |
| US-74 | exports_capacitacion.feature | Cada sección da un export que el lector y la validación aceptan sin rechazos | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_cada_seccion_da_un_export_aceptado | Con prueba |
| US-74 | exports_capacitacion.feature | La ida y vuelta por el lector da los mismos códigos y niveles que la tabla maestra | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_la_ida_y_vuelta_por_el_lector | Con prueba |
| US-74 | exports_capacitacion.feature | El export trae solo el código y la columna del PI, sin nombres ni el profesor | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_el_export_sin_nombres_ni_profesor | Con prueba |
| US-74 | exports_capacitacion.feature | Un código con cero a la izquierda se escribe como texto | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_un_codigo_con_cero_a_la_izquierda | Con prueba |
| US-74 | exports_capacitacion.feature | El curso de cada archivo es el de la programación y no uno armado por el generador | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_el_curso_sale_de_la_programacion | Con prueba |
| US-74 | exports_capacitacion.feature | Dos corridas dan los mismos archivos byte a byte | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_dos_corridas_byte_a_byte | Con prueba |
| US-74 | exports_capacitacion.feature | El manifiesto resume cada export sin códigos | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_el_manifiesto_sin_codigos | Con prueba |
| US-74 | exports_capacitacion.feature | Las filas de otro periodo, otra asignatura u otro PI se omiten y se cuentan | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_las_filas_omitidas_se_cuentan | Con prueba |
| US-74 | exports_capacitacion.feature | El PI llega por parámetro para la decisión abierta D-48 | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_el_pi_llega_por_parametro | Con prueba |
| US-74 | exports_capacitacion.feature | Una fila defectuosa detiene la generación entera sin mostrar el valor | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_una_fila_defectuosa_detiene_todo | Con prueba |
| US-74 | exports_capacitacion.feature | Sin la columna CALIFICACIÓN el generador no adivina | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_sin_la_columna_calificacion | Con prueba |
| US-74 | exports_capacitacion.feature | La carpeta de salida dentro de un repositorio se rechaza | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_la_salida_dentro_de_un_repositorio | Con prueba |
| US-74 | exports_capacitacion.feature | La salida del generador no muestra códigos ni nombres | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_la_salida_sin_codigos_ni_nombres | Con prueba |
| US-74 | exports_capacitacion.feature | Un archivo de ejercicio por profesor tiene su propia huella | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_un_ejercicio_por_profesor | Con prueba |
| US-75 | carga_quimica.feature | Un export de 34 filas con niveles de 1 a 4 queda PUBLICADA entero en Industrial | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_un_export_de_34_filas_queda_publicada_en_industrial | Con prueba |
| US-75 | carga_quimica.feature | La asignatura de cuatro cifras se lee también en el nombre de un export de texto | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_la_asignatura_de_cuatro_cifras_en_un_export_de_texto | Con prueba |
| US-75 | carga_quimica.feature | El export que arma el generador con la programación de la sección se publica sin rechazos | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_el_export_del_generador_se_publica_sin_rechazos | Con prueba |
| US-75 | carga_quimica.feature | Q21 detecta una sección cuyo curso de Blackboard declara otra sección | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_q21_detecta_una_seccion_cuyo_curso_declara_otra | Con prueba |
| US-76 | carga_quimica.feature | El export de otra sección del curso se rechaza con el número de las dos | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_el_export_de_otra_seccion_se_rechaza | Con prueba |
| US-76 | carga_quimica.feature | Un nombre de columna que el lector no reconoce deja la carga sin el PI 6.1 | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_una_columna_que_el_lector_no_reconoce | Con prueba |
| US-76 | carga_quimica.feature | La nota sobre 20 entre otras filas válidas publica solo los niveles | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_la_nota_sobre_20_entre_filas_validas | Con prueba |
| US-76 | carga_quimica.feature | Un Excel con todas las notas sobre 20 queda RECHAZADA sin repetir las notas | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_todas_las_notas_sobre_20 | Con prueba |
| US-76 | carga_quimica.feature | Un nivel con medio punto se rechaza como no numérico | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_un_nivel_con_medio_punto | Con prueba |
| US-76 | carga_quimica.feature | Un libro sin Username ni Student ID se rechaza entero | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_un_libro_sin_username_ni_student_id | Con prueba |
| US-76 | carga_quimica.feature | El mismo export subido dos veces en la misma sección devuelve la constancia existente | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_el_mismo_export_dos_veces | Con prueba |
| US-76 | carga_quimica.feature | Los nombres de un libro con Last Name y First Name no llegan a la base | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_los_nombres_no_llegan_a_la_base | Con prueba |
| US-76 | carga_quimica.feature | El registro de la aplicación no trae códigos ni notas fuera de la huella del archivo | pytest-bdd tests/aceptacion/pasos/test_carga_quimica_feature.py::test_el_registro_no_trae_codigos_ni_notas | Con prueba |
| US-77 | carga_quimica.feature | El consejo sigue al motivo de las filas rechazadas de una carga publicada | Vitest tests/spec008/carga_quimica.test.tsx › El consejo sigue al motivo de las filas rechazadas de una carga publicada ($motivo) | Con prueba |
| US-77 | carga_quimica.feature | El aviso del puntaje máximo se muestra antes de la constancia | Vitest tests/spec008/carga_quimica.test.tsx | Con prueba |
| US-77 | carga_quimica.feature | Una carga rechazada sin filas aceptadas remite a la tabla sin nombrar Blackboard | Vitest tests/spec008/carga_quimica.test.tsx | Con prueba |
| US-77 | carga_quimica.feature | Una carga publicada sin rechazos ni avisos no muestra consejo | Vitest tests/spec008/carga_quimica.test.tsx | Con prueba |
| US-77 | carga_quimica.feature | Un motivo de fila desconocido no muestra consejo y la prueba recorre los motivos del contrato | Vitest tests/spec008/carga_quimica.test.tsx | Con prueba |
| US-77 | carga_quimica.feature | P4 de una carga publicada remite al reemplazo de P5 | Vitest tests/spec008/carga_quimica.test.tsx | Con prueba |
| US-78 | r17_industrial.feature | El encabezado dice la carrera de la carga | pytest-bdd tests/aceptacion/pasos/test_r17_industrial_feature.py::test_el_encabezado_dice_la_carrera_de_la_carga | Con prueba |
| US-78 | r17_industrial.feature | Ninguna otra celda de la plantilla nombra a Ambiental | pytest-bdd tests/aceptacion/pasos/test_r17_industrial_feature.py::test_ninguna_otra_celda_nombra_a_ambiental | Con prueba |
| US-78 | r17_industrial.feature | La cabecera y el bloque I traen la sección, el periodo y el instrumento | pytest-bdd tests/aceptacion/pasos/test_r17_industrial_feature.py::test_la_cabecera_y_el_bloque_i | Con prueba |
| US-78 | r17_industrial.feature | Las cifras del R-17 siguen la regla de la meta de Industrial | pytest-bdd tests/aceptacion/pasos/test_r17_industrial_feature.py::test_las_cifras_siguen_la_regla_de_la_meta | Con prueba |
| US-78 | r17_industrial.feature | La franja provisional nombra el conjunto de Industrial | pytest-bdd tests/aceptacion/pasos/test_r17_industrial_feature.py::test_la_franja_provisional_nombra_el_conjunto | Con prueba |
| US-78 | r17_industrial.feature | La tabla de estudiantes trae SO, PI, código y nivel, sin nombres ni el profesor | pytest-bdd tests/aceptacion/pasos/test_r17_industrial_feature.py::test_la_tabla_de_estudiantes_sin_nombres | Con prueba |
| US-78 | r17_industrial.feature | Un PI sin descriptores de rúbrica no cambia el R-17 | pytest-bdd tests/aceptacion/pasos/test_r17_industrial_feature.py::test_un_pi_sin_descriptores_no_cambia_el_r17 | Con prueba |
| US-78 | r17_industrial.feature | Otro profesor del curso no descarga el R-17 de la 701 | pytest-bdd tests/aceptacion/pasos/test_r17_industrial_feature.py::test_otro_profesor_no_descarga_el_r17 | Con prueba |
| US-78 | r17_industrial.feature | El SO y el PI de la ruta 12 salen del catálogo de Industrial y no del de Ambiental | pytest-bdd tests/aceptacion/pasos/test_r17_industrial_feature.py::test_la_ruta_12_usa_el_catalogo_de_industrial | Con prueba |
| US-78 | r17_industrial.feature | La fila de P6 dice la cifra, la meta y el resultado con palabras | Vitest tests/spec008/r17_industrial.test.tsx | Con prueba |
| US-78 | r17_industrial.feature | Una sección que llega a la meta lo dice con palabras | Vitest tests/spec008/r17_industrial.test.tsx | Con prueba |
| US-79 | avance_del_curso.feature | La ruta 17 da la etapa de cada sección del curso y ninguna de otro curso | pytest-bdd tests/aceptacion/pasos/test_avance_feature.py::test_la_ruta_17_da_la_etapa_del_curso | Con prueba |
| US-79 | avance_del_curso.feature | Un periodo sin secciones del curso responde vacío | pytest-bdd tests/aceptacion/pasos/test_avance_feature.py::test_un_periodo_sin_secciones_del_curso_responde_vacio | Con prueba |
| US-79 | avance_del_curso.feature | El profesor del curso no lee el avance | pytest-bdd tests/aceptacion/pasos/test_avance_feature.py::test_el_profesor_del_curso_no_lee_el_avance | Con prueba |
| US-79 | avance_del_curso.feature | La coordinación de Ambiental no ve el avance de Química | pytest-bdd tests/aceptacion/pasos/test_avance_feature.py::test_la_coordinacion_de_ambiental_no_ve_el_avance_de_quimica | Con prueba |
| US-79 | avance_del_curso.feature | P7 lleva el título del curso y es la llegada de su coordinación | Vitest tests/spec008/avance_del_curso.test.tsx | Con prueba |
| US-79 | avance_del_curso.feature | Desde P7 la coordinación abre la carga publicada de una sección | Vitest tests/spec008/avance_del_curso.test.tsx | Con prueba |
| US-79 | avance_del_curso.feature | Sin la etapa B, la coordinación del curso sigue el avance en P2 | Vitest tests/spec008/avance_del_curso.test.tsx | Con prueba |
| US-80 | avance_del_curso.feature | Cada sección trae su porcentaje como en su R-17 | Ninguna | Pendiente por decisión |
| US-80 | avance_del_curso.feature | El agregado del curso suma estudiantes y no promedia porcentajes | Ninguna | Pendiente por decisión |
| US-80 | avance_del_curso.feature | Un curso sin cargas publicadas no inventa un porcentaje | Ninguna | Pendiente por decisión |
| US-80 | avance_del_curso.feature | El profesor no recibe el agregado del curso | Ninguna | Pendiente por decisión |
| US-80 | avance_del_curso.feature | Ninguna cifra del agregado revela a un estudiante | Ninguna | Pendiente por decisión |
| US-80 | avance_del_curso.feature | P6 muestra el curso antes de las secciones | Ninguna | Pendiente por decisión |
| US-81 | sistema_visual.feature | Los pares de color de texto y fondo cumplen el contraste AA | Vitest tests/spec008/sistema_visual.test.tsx | Con prueba |
| US-81 | sistema_visual.feature | Cada estado de una pantalla usa su componente y su rol | Vitest tests/spec008/sistema_visual.test.tsx › Cada estado de una pantalla usa su componente y su rol ($pantalla $estado) | Con prueba |
| US-81 | sistema_visual.feature | Los rótulos fijados no cambian con el rediseño | Vitest tests/spec008/sistema_visual.test.tsx | Con prueba |
| US-81 | sistema_visual.feature | La tarjeta de P2 muestra el camino de la sección y su paso actual | Vitest tests/spec008/sistema_visual.test.tsx › La tarjeta de P2 muestra el camino de la sección y su paso actual ($estado, $paso1, $paso2) | Con prueba |
| US-81 | sistema_visual.feature | El botón principal de la tarjeta es el del paso actual | Vitest tests/spec008/sistema_visual.test.tsx | Con prueba |
| US-81 | sistema_visual.feature | Una sección sin plan no muestra pasos y conserva su texto | Vitest tests/spec008/sistema_visual.test.tsx | Con prueba |
| US-81 | sistema_visual.feature | La marca del paso no depende solo del color | Vitest tests/spec008/sistema_visual.test.tsx | Con prueba |
| US-81 | sistema_visual.feature | La coordinación no recibe los pasos del profesor | Vitest tests/spec008/sistema_visual.test.tsx | Con prueba |
| US-81 | sistema_visual.feature | Ingreso dice el error junto al formulario y conserva el correo | Vitest tests/spec008/sistema_visual.test.tsx | Con prueba |
| US-81 | sistema_visual.feature | El bloqueo por intentos se muestra sin ocultar el formulario | Vitest tests/spec008/sistema_visual.test.tsx | Con prueba |
| US-81 | sistema_visual.feature | Con movimiento reducido no hay animaciones | Vitest tests/spec008/sistema_visual.test.tsx | Con prueba |
| US-81 | sistema_visual.feature | El rediseño no carga recursos de terceros ni dependencias nuevas | Vitest tests/spec008/sistema_visual.test.tsx | Con prueba |
| US-82 | sistema_visual.feature | A 375 px de ancho ninguna pantalla se desplaza de lado | Playwright e2e/visual.spec.ts › A 375 px de ancho ninguna pantalla se desplaza de lado (${pantalla}) | Con prueba |
| US-82 | sistema_visual.feature | La tabla de rechazos de P4 se desplaza dentro de su región y no la página | Playwright e2e/visual.spec.ts | Con prueba |
| US-82 | sistema_visual.feature | El foco se ve en cada control de P3 y sigue el orden de lectura | Playwright e2e/visual.spec.ts | Con prueba |
| US-82 | sistema_visual.feature | El menú principal se usa solo con el teclado | Playwright e2e/visual.spec.ts | Con prueba |
| US-83 | ensayo_y_conciliacion.feature | Todo coincide en la base, en la vista y en los R-17 | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_todo_coincide | Con prueba |
| US-83 | ensayo_y_conciliacion.feature | Una calificación distinta se informa sin el código | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_una_calificacion_distinta | Con prueba |
| US-83 | ensayo_y_conciliacion.feature | Cada diferencia se cuenta por su tipo y por sección | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_cada_diferencia_por_su_tipo | Con prueba |
| US-83 | ensayo_y_conciliacion.feature | Una sección sin carga publicada se nombra | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_una_seccion_sin_carga_publicada | Con prueba |
| US-83 | ensayo_y_conciliacion.feature | El mismo cociente con otro redondeo cuenta como igual | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_el_mismo_cociente_con_otro_redondeo | Con prueba |
| US-83 | ensayo_y_conciliacion.feature | Una carga reemplazada no duplica filas | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_una_carga_reemplazada_no_duplica | Con prueba |
| US-83 | ensayo_y_conciliacion.feature | El orden de las filas y la columna PROFESOR no cuentan como diferencia | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_el_orden_y_profesor_no_cuentan | Con prueba |
| US-83 | ensayo_y_conciliacion.feature | Los códigos que no empiezan con 99 se aceptan con 8 cifras | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_los_codigos_sin_99 | Con prueba |
| US-83 | ensayo_y_conciliacion.feature | El conciliador no lee un archivo dentro de un repositorio | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_no_lee_dentro_de_un_repositorio | Con prueba |
| US-83 | ensayo_y_conciliacion.feature | La conciliación no escribe en la base | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_la_conciliacion_no_escribe | Con prueba |
| US-84 | ensayo_y_conciliacion.feature | El ensayo sube los exports generados y deja las secciones iguales | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_el_ensayo_deja_las_secciones_iguales | Con prueba |
| US-84 | ensayo_y_conciliacion.feature | El manifiesto del generador y lo publicado coinciden por huella y por conteo | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_el_manifiesto_y_lo_publicado_coinciden | Con prueba |
| US-84 | ensayo_y_conciliacion.feature | Un nivel distinto en el ensayo se nombra sin el código y detiene la conclusión | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_un_nivel_distinto_detiene_la_conclusion | Con prueba |
| US-84 | ensayo_y_conciliacion.feature | El ensayo corre en una base aparte y no deja huellas en la de la capacitación | pytest-bdd tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py::test_el_ensayo_corre_en_una_base_aparte | Con prueba |
| US-85 | capacitacion_en_develop.feature | El profesor sube su export y descarga su R-17 en la vista previa | Playwright e2e/humo_quimica.spec.ts | Con prueba |
| US-85 | capacitacion_en_develop.feature | El profesor no alcanza otra sección del curso | Playwright e2e/humo_quimica.spec.ts | Con prueba |
| US-85 | capacitacion_en_develop.feature | La coordinación del curso ve las secciones del curso y el avance | Playwright e2e/humo_quimica.spec.ts | Con prueba |
| US-85 | capacitacion_en_develop.feature | Sin la etapa B, la coordinación del curso se comprueba en P2 | Playwright e2e/humo_quimica.spec.ts | Con prueba |
| US-85 | capacitacion_en_develop.feature | La coordinación del curso no sube en una sección ni ve otro curso | Playwright e2e/humo_quimica.spec.ts | Con prueba |
| US-85 | capacitacion_en_develop.feature | Las capturas y los resultados no guardan nada sensible | Playwright e2e/humo_quimica.spec.ts | Con prueba |
| US-85 | capacitacion_en_develop.feature | Una vista previa ya usada se detiene antes de subir | Playwright e2e/humo_quimica.spec.ts | Con prueba |
| US-85 | capacitacion_en_develop.feature | Con la siembra de la capacitación el humo no corre | Playwright e2e/humo_quimica.spec.ts | Con prueba |
| US-86 | capacitacion_en_develop.feature | La siembra completa deja la misma huella de Ambiental y los controles limpios | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_la_siembra_completa_deja_la_misma_huella | Con prueba |
| US-86 | capacitacion_en_develop.feature | El alcance de Ambiental queda antes que la vigencia de Industrial | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_el_alcance_de_ambiental_queda_antes_que_la_vigencia | Con prueba |
| US-86 | capacitacion_en_develop.feature | La programación de Química acepta 2026-1 y una asignatura de cuatro cifras | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_la_programacion_de_quimica_acepta_2026_1 | Con prueba |
| US-86 | capacitacion_en_develop.feature | Una segunda siembra completa no suma filas | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_una_segunda_siembra_completa_no_suma_filas | Con prueba |
| US-86 | capacitacion_en_develop.feature | Un paso que falla deja la base como estaba en ese paso y detiene los siguientes | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_un_paso_que_falla_detiene_los_siguientes | Con prueba |
| US-86 | capacitacion_en_develop.feature | La rama principal exige una confirmación aparte | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_la_rama_principal_exige_una_confirmacion_aparte | Con prueba |
| US-86 | capacitacion_en_develop.feature | Ninguna salida de la siembra repite el correo de la coordinación | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_ninguna_salida_repite_el_correo_de_la_coordinacion | Con prueba |
| US-86 | capacitacion_en_develop.feature | La versión de prueba acepta los códigos que no empiezan con 99 | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_la_version_de_prueba_acepta_los_codigos | Con prueba |
| US-86 | capacitacion_en_develop.feature | Después de la siembra de la capacitación, una lectura sin correos confirma el alcance | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_una_lectura_sin_correos_confirma_el_alcance | Con prueba |
| US-87 | guia_y_privacidad.feature | Cada rótulo citado en la guía existe en el Front | Vitest tests/spec008/guia_y_privacidad.test.ts | Con prueba |
| US-87 | guia_y_privacidad.feature | Un rótulo cambiado en el Front hace fallar la guía | Vitest tests/spec008/guia_y_privacidad.test.ts | Con prueba |
| US-87 | guia_y_privacidad.feature | La guía no trae datos que no debe | Vitest tests/spec008/guia_y_privacidad.test.ts | Con prueba |
| US-87 | guia_y_privacidad.feature | Una fecha sin confirmar se dice como tal | Vitest tests/spec008/guia_y_privacidad.test.ts | Con prueba |
| US-87 | guia_y_privacidad.feature | La guía del profesor sigue el flujo en el orden de las pantallas | Vitest tests/spec008/guia_y_privacidad.test.ts | Con prueba |
| US-87 | guia_y_privacidad.feature | El profesor sigue la guía de su rol de punta a punta en la vista previa | Playwright e2e/humo_quimica.spec.ts | Con prueba |
| US-87 | guia_y_privacidad.feature | El ejercicio de error usa un export inventado y enseña a leer «Qué corregir» | Playwright e2e/humo_quimica.spec.ts | Con prueba |
| US-87 | guia_y_privacidad.feature | La guía de la coordinación del curso no promete correos sin D-51 | Vitest tests/spec008/guia_y_privacidad.test.ts | Con prueba |
| US-87 | guia_y_privacidad.feature | Cada tarjeta de profesor nombra el archivo de su sección según el manifiesto | pytest-bdd tests/aceptacion/pasos/test_exports_capacitacion_feature.py::test_cada_tarjeta_nombra_el_archivo_de_su_seccion | Con prueba |
| US-88 | guia_y_privacidad.feature | El correo prohibido se detecta por su huella sin imprimirlo | pytest-bdd tests/aceptacion/pasos/test_guia_y_privacidad_feature.py::test_el_correo_prohibido_se_detecta_por_su_huella | Con prueba |
| US-88 | guia_y_privacidad.feature | Sin la variable de huellas el control avisa y no falla | pytest-bdd tests/aceptacion/pasos/test_guia_y_privacidad_feature.py::test_sin_la_variable_de_huellas_el_control_avisa | Con prueba |
| US-88 | guia_y_privacidad.feature | Un código de ocho cifras fuera del rango inventado detiene el cambio en specs, pruebas, e2e y docs | pytest-bdd tests/aceptacion/pasos/test_guia_y_privacidad_feature.py::test_un_codigo_de_ocho_cifras_fuera_del_rango_detiene_el_cambio | Con prueba |
| US-88 | guia_y_privacidad.feature | Una captura o un resultado de Playwright no se versionan | pytest-bdd tests/aceptacion/pasos/test_guia_y_privacidad_feature.py::test_una_captura_o_un_resultado_de_playwright_no_se_versionan | Con prueba |
| US-88 | guia_y_privacidad.feature | La tabla maestra no entra por otro nombre y los archivos legítimos pasan | pytest-bdd tests/aceptacion/pasos/test_guia_y_privacidad_feature.py::test_la_tabla_maestra_no_entra_por_otro_nombre | Con prueba |
| US-88 | guia_y_privacidad.feature | Una tarjeta de profesor dentro del repositorio se rechaza | pytest-bdd tests/aceptacion/pasos/test_guia_y_privacidad_feature.py::test_una_tarjeta_de_profesor_dentro_del_repositorio_se_rechaza | Con prueba |
| US-88 | guia_y_privacidad.feature | La regla nueva no da falsos positivos en el contenido actual | pytest-bdd tests/aceptacion/pasos/test_guia_y_privacidad_feature.py::test_la_regla_nueva_no_da_falsos_positivos_en_el_contenido_actual | Con prueba |
| US-88 | guia_y_privacidad.feature | El historial publicado no trae el correo prohibido | pytest-bdd tests/aceptacion/pasos/test_guia_y_privacidad_feature.py::test_el_historial_publicado_no_trae_el_correo_prohibido | Con prueba |
| US-89 | capacitacion_en_develop.feature | Las cuentas de ejemplo se dan de baja en seco primero y pierden su sesión | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_las_cuentas_de_ejemplo_se_dan_de_baja | Con prueba |
| US-89 | capacitacion_en_develop.feature | El cierre comprueba el respaldo por huella y no borra nada | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_el_cierre_comprueba_el_respaldo | Con prueba |
| US-89 | capacitacion_en_develop.feature | Un respaldo incompleto se informa y no se recomienda borrar | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_un_respaldo_incompleto_se_informa | Con prueba |
| US-89 | capacitacion_en_develop.feature | Sin decisión sobre el destino de las cargas, el cierre no toca develop ni main | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_sin_d_55_el_cierre_no_toca_develop_ni_main | Con prueba |
| US-89 | capacitacion_en_develop.feature | Después del cierre la conciliación de develop sigue disponible | pytest-bdd tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py::test_despues_del_cierre_la_conciliacion_sigue | Con prueba |
| US-90 | matriz_cumplimiento.feature | Cada historia del flujo tiene escenario, prueba y corrida | pytest-bdd tests/aceptacion/pasos/test_matriz_cumplimiento_feature.py::test_cada_historia_tiene_escenario_prueba_y_corrida | Con prueba |
| US-90 | matriz_cumplimiento.feature | Una historia de la spec 008 sin escenario hace fallar la generación | pytest-bdd tests/aceptacion/pasos/test_matriz_cumplimiento_feature.py::test_una_historia_sin_escenario_hace_fallar_la_generacion | Con prueba |
| US-90 | matriz_cumplimiento.feature | Una regla con prueba nombrada no es un hueco aunque no tenga escenario | pytest-bdd tests/aceptacion/pasos/test_matriz_cumplimiento_feature.py::test_una_regla_con_prueba_nombrada_no_es_un_hueco | Con prueba |
| US-90 | matriz_cumplimiento.feature | Un escenario delegado a Vitest se busca en el Front por su título exacto | pytest-bdd tests/aceptacion/pasos/test_matriz_cumplimiento_feature.py::test_un_escenario_delegado_se_busca_por_su_titulo_exacto | Con prueba |
| US-90 | matriz_cumplimiento.feature | Lo pendiente por decisión se distingue de lo olvidado | pytest-bdd tests/aceptacion/pasos/test_matriz_cumplimiento_feature.py::test_lo_pendiente_por_decision_se_distingue_de_lo_olvidado | Con prueba |
| US-90 | matriz_cumplimiento.feature | Una etiqueta que no liga con ninguna historia hace fallar la generación | pytest-bdd tests/aceptacion/pasos/test_matriz_cumplimiento_feature.py::test_una_etiqueta_sin_historia_hace_fallar_la_generacion | Con prueba |
| US-90 | matriz_cumplimiento.feature | El tramo de la capacitación queda en una sola vista | pytest-bdd tests/aceptacion/pasos/test_matriz_cumplimiento_feature.py::test_el_tramo_de_la_capacitacion_queda_en_una_sola_vista | Con prueba |
| US-90 | matriz_cumplimiento.feature | La integración continua corre la matriz y el archivo versionado no cambia con cada corrida | pytest-bdd tests/aceptacion/pasos/test_matriz_cumplimiento_feature.py::test_la_integracion_continua_corre_la_matriz | Con prueba |
| US-90 | matriz_cumplimiento.feature | La matriz no trae datos reales | pytest-bdd tests/aceptacion/pasos/test_matriz_cumplimiento_feature.py::test_la_matriz_no_trae_datos_reales | Con prueba |
