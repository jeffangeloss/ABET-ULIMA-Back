# Audit: Del export de Blackboard al R-17 desde la base (cortes 1 y 2)

**Fecha**: 2026-10-30 (corte 1) y 2026-11-17 (corte 2)  
**Spec**: [spec.md](./spec.md)  
**Plan**: [plan.md](./plan.md)  
**Comando**: `uv run --frozen pytest -q tests/aceptacion -rA` en el Back, `uv run --frozen pytest -q tests -rA` en el Back para las pruebas unitarias y `npm test` en el Front  
**Resultado**: aceptación, 170 passed, 19 skipped in 116.97s (0:01:56); suite completa del Back, 852 passed, 20 skipped in 241.50s (0:04:01); Vitest del Front, 8 archivos y 76 pruebas aprobadas; corte 2 (2026-11-17), aceptación, 300 passed y 14 skipped, y suite completa del Back, 1289 passed y 15 skipped in 141.47s (0:02:21); Vitest del Front, 10 archivos y 139 pruebas aprobadas; prueba de humo local `e2e/humo.spec.ts`, 3 passed  
**Estado**: Corte 1 verificado en local el 2026-10-30 y publicado en Production con la versión 0.1.0 el 2026-11-17 (sección «Despliegue»). El corte 2 queda verificado en local el 2026-11-17 en la rama `feat/001-corte-2` para US-18, US-19 y US-21 (sección «Corte 2»), y US-20 espera a T018. Quedan abiertos tres escenarios de US-17, la verificación a mano de T062, US-20 y la prueba de humo del corte 2 contra la vista previa de `develop`.

Esta auditoría cruza cada historia de usuario (user story, US) con sus escenarios en Gherkin, la prueba que los ejecuta y su resultado de hoy. Después cruza los requisitos funcionales (functional requirements, FR) y los criterios de éxito (success criteria, SC) de la spec con la evidencia, y lista lo que el corte 1 deja abierto. Las reglas de negocio (business rules, BR) son las de `specs/features/`. El resultado de cada escenario sale de una corrida real, no de una nota a mano, y los tres estados posibles son los siguientes.

- **aprobado**, la prueba corrió y pasó.
- **omitido (razón)**, la prueba existe y pytest la omite con esa razón.
- **pendiente (razón)**, la prueba todavía no existe.

## Cómo se armó esta traza

El script `traza.py` (guardado fuera del repositorio, en la carpeta temporal de la fase 6) lee los siete `.feature` de `aceptacion/`, arma para cada escenario el nombre de la función de pytest-bdd con la misma regla que `pytest_bdd.scenario.make_python_name` y lo busca entre las pruebas que pytest recolecta. Luego toma el resultado de la salida de `pytest -rA` y el de `npm test`. Se detiene si un escenario no tiene prueba, si una prueba no tiene escenario, si una prueba falla o si los omitidos por razón no suman lo que informa pytest. La corrida de aceptación recolectó 189 pruebas, que son 170 aprobadas y 19 omitidas, y la suite completa suma 682 pruebas unitarias y de plataforma aprobadas además de las de aceptación. Las 12 pruebas de `test_lectura_gherkin_es.py` (T010) comprueban la lectura del Gherkin en español y no pertenecen a ningún escenario. La traza del corte 2, del 2026-11-17, sigue la misma regla sobre la salida de `pytest tests/aceptacion -rA` de la rama `feat/001-corte-2`, que recolecta 314 pruebas, 300 aprobadas y 14 omitidas. De ellas, 193 son de escenarios de la spec 001, con 179 aprobadas y 14 omitidas, 104 son de la spec 003 y 17 de `test_lectura_gherkin_es.py`.

## Resumen

| Conjunto | Escenarios | Aprobados | Omitidos | Pendientes |
| --- | --- | --- | --- | --- |
| Corte 1 (US-01 a US-17) | 107 | 98 | 6 | 3 |
| Corte 2 (US-18 a US-21) | 25 | 20 | 5 | 0 |
| Total | 132 | 117 | 11 | 4 |

Un esquema de escenario (Esquema del escenario) cuenta una vez aunque corra varios ejemplos. En pruebas de pytest, las 193 de escenarios del 2026-11-17 dan 179 aprobadas y 14 omitidas, que son las 9 de US-20 y las 5 que se comprueban en Neon. El corte 1 pierde el escenario «Un export que no declara su sección se detiene sin dejar rastro» de US-13, que se retira con T084 porque el primero de US-21 lo reemplaza. Los siete escenarios aprobados de US-17 salen de las comprobaciones del 2026-11-17 contra Vercel y Neon, que describe la sección «Despliegue», y no de los pasos de pytest-bdd. El de las variables suma además `tests/test_env_example.py`, que revisa `.env.example` en cada corrida de la suite.

## Historias

### US-01: Migrar y verificar la base en Neon (P1, corte 1)

7 escenarios, 2 aprobados, 5 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| Primera migración en una base vacía | `test_base_neon_feature.py::test_primera_migración_en_una_base_vacía` | omitido (se comprueban en Neon con T021 y T027) |
| Repetir la migración no aplica nada nuevo | `test_base_neon_feature.py::test_repetir_la_migración_no_aplica_nada_nuevo` | omitido (se comprueban en Neon con T021 y T027) |
| Clean prohibido en la base compartida | `test_base_neon_feature.py::test_clean_prohibido_en_la_base_compartida` | omitido (se comprueban en Neon con T021 y T027) |
| Ninguna credencial queda en lo que sigue git | `test_base_neon_feature.py::test_ninguna_credencial_queda_en_lo_que_sigue_git` | aprobado |
| Las consultas de control pasan en la base recién preparada | `test_base_neon_feature.py::test_las_consultas_de_control_pasan_en_la_base_recién_preparada` | omitido (se comprueban en Neon con T021 y T027) |
| Las consultas de control no escriben en la base | `test_base_neon_feature.py::test_las_consultas_de_control_no_escriben_en_la_base` | omitido (se comprueban en Neon con T021 y T027) |
| La CI del Back reproduce la base desde cero sin Redgate | `test_base_neon_feature.py::test_la_ci_del_back_reproduce_la_base_desde_cero_sin_redgate` | aprobado |

### US-02: Crear el rol de la aplicación con privilegio mínimo (P1, corte 1)

8 escenarios, 7 aprobados, 1 omitido y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| El script crea abet_app sin atributos de administración | `test_base_neon_feature.py::test_el_script_crea_abet_app_sin_atributos_de_administración` | aprobado |
| abet_app publica una carga válida en una sola transacción | `test_base_neon_feature.py::test_abet_app_publica_una_carga_válida_en_una_sola_transacción` | aprobado |
| abet_app lee las vistas del R-17 | `test_base_neon_feature.py::test_abet_app_lee_las_vistas_del_r17` | aprobado |
| abet_app no puede borrar ni vaciar tablas de abet | `test_base_neon_feature.py::test_abet_app_no_puede_borrar_ni_vaciar_tablas_de_abet` (8 ejemplos) | aprobado (8 de 8 ejemplos) |
| abet_app solo actualiza el estado y los conteos de una carga | `test_base_neon_feature.py::test_abet_app_solo_actualiza_el_estado_y_los_conteos_de_una_carga` (5 ejemplos) | aprobado (5 de 5 ejemplos) |
| abet_app no escribe reglas, catálogo ni datos del periodo | `test_base_neon_feature.py::test_abet_app_no_escribe_reglas_catálogo_ni_datos_del_periodo` (7 ejemplos) | aprobado (7 de 7 ejemplos) |
| abet_app no borra ni da de alta usuarios en acceso | `test_base_neon_feature.py::test_abet_app_no_borra_ni_da_de_alta_usuarios_en_acceso` (7 ejemplos) | aprobado (7 de 7 ejemplos) |
| Los permisos de abet_app sobreviven a una nueva migración | `test_base_neon_feature.py::test_los_permisos_de_abet_app_sobreviven_a_una_nueva_migración` | omitido (db/callbacks/afterMigrate__permisos_lectura.sql llega con el git subtree pull de preparacion-neon (T022 y T027)) |

### US-03: Preparar el periodo 2026-2 con datos inventados (P1, corte 1)

5 escenarios, 5 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| Sembrar la vigencia, las secciones 410 y 411 y el plan de 450002 | `test_base_neon_feature.py::test_sembrar_la_vigencia_las_secciones_410_y_411_y_el_plan_de_450002` | aprobado |
| Repetir el script de datos no duplica filas | `test_base_neon_feature.py::test_repetir_el_script_de_datos_no_duplica_filas` | aprobado |
| El número de sección no admite ceros a la izquierda | `test_base_neon_feature.py::test_el_número_de_sección_no_admite_ceros_a_la_izquierda` | aprobado |
| El script de datos solo trae datos inventados | `test_base_neon_feature.py::test_el_script_de_datos_solo_trae_datos_inventados` | aprobado |
| La API no arranca con un periodo o un conjunto de reglas que la base no conoce | `test_base_neon_feature.py::test_la_api_no_arranca_con_un_periodo_o_un_conjunto_de_reglas_que_la_base_no_conoce` (2 ejemplos) | aprobado (2 de 2 ejemplos) |

### US-04: Registrar usuarios autorizados y docentes por sección (P1, corte 1)

5 escenarios, 5 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| V1_09 crea el esquema acceso y los motivos nuevos | `test_base_neon_feature.py::test_v1_09_crea_el_esquema_acceso_y_los_motivos_nuevos` | aprobado |
| Las cargas anteriores a V1_09 conservan subida_por nulo | `test_base_neon_feature.py::test_las_cargas_anteriores_a_v1_09_conservan_subida_por_nulo` | aprobado |
| El script de datos registra a los usuarios de prueba y sus secciones | `test_base_neon_feature.py::test_el_script_de_datos_registra_a_los_usuarios_de_prueba_y_sus_secciones` | aprobado |
| La base rechaza un registro de acceso inválido | `test_base_neon_feature.py::test_la_base_rechaza_un_registro_de_acceso_inválido` (5 ejemplos) | aprobado (5 de 5 ejemplos) |
| Los correos solo viven en acceso.usuario_autorizado | `test_base_neon_feature.py::test_los_correos_solo_viven_en_accesousuario_autorizado` | aprobado |

### US-05: Iniciar sesión con contraseña asignada (P1, corte 1)

9 escenarios, 9 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| El administrador técnico asigna una contraseña por comando | `test_acceso_feature.py::test_el_administrador_técnico_asigna_una_contraseña_por_comando` | aprobado |
| Un usuario autorizado entra con su contraseña | `test_acceso_feature.py::test_un_usuario_autorizado_entra_con_su_contraseña` | aprobado |
| El correo se compara sin espacios ni mayúsculas | `test_acceso_feature.py::test_el_correo_se_compara_sin_espacios_ni_mayúsculas` | aprobado |
| Un intento fallido no revela si el correo está autorizado | `test_acceso_feature.py::test_un_intento_fallido_no_revela_si_el_correo_está_autorizado` (3 ejemplos) | aprobado (3 de 3 ejemplos) |
| Cinco intentos fallidos bloquean el correo por 15 minutos | `test_acceso_feature.py::test_cinco_intentos_fallidos_bloquean_el_correo_por_15_minutos` | aprobado |
| Cerrar la sesión vence la cookie y la fila | `test_acceso_feature.py::test_cerrar_la_sesión_vence_la_cookie_y_la_fila` | aprobado |
| Una sesión vencida no da acceso | `test_acceso_feature.py::test_una_sesión_vencida_no_da_acceso` | aprobado |
| Un usuario dado de baja deja de entrar | `test_acceso_feature.py::test_un_usuario_dado_de_baja_deja_de_entrar` | aprobado |
| Sin sesión ninguna ruta de datos responde | `test_acceso_feature.py::test_sin_sesión_ninguna_ruta_de_datos_responde` (4 ejemplos) | aprobado (4 de 4 ejemplos) |

### US-06: Ver solo mis secciones del periodo (P1, corte 1)

8 escenarios, 8 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| El profesor ve únicamente su sección | `test_acceso_feature.py::test_el_profesor_ve_únicamente_su_sección`; Vitest `tests/pantallas/MisSecciones.test.tsx`, «lista todas las secciones del profesor, una fila por sección, con su estado de carga» | aprobado; Vitest aprobado |
| El coordinador ve todas las secciones de la carrera | `test_acceso_feature.py::test_el_coordinador_ve_todas_las_secciones_de_la_carrera` | aprobado |
| El estado refleja la carga publicada | `test_acceso_feature.py::test_el_estado_refleja_la_carga_publicada`; Vitest `tests/pantallas/MisSecciones.test.tsx`, «lista todas las secciones del profesor, una fila por sección, con su estado de carga» | aprobado; Vitest aprobado |
| El profesor no alcanza una sección ajena escribiendo la ruta | `test_acceso_feature.py::test_el_profesor_no_alcanza_una_sección_ajena_escribiendo_la_ruta` (3 ejemplos) | aprobado (3 de 3 ejemplos) |
| Sin sesión no hay lista | `test_acceso_feature.py::test_sin_sesión_no_hay_lista` | aprobado |
| Sección de una asignatura sin plan de medición | `test_acceso_feature.py::test_sección_de_una_asignatura_sin_plan_de_medición`; Vitest `tests/pantallas/MisSecciones.test.tsx`, «una sección sin plan de medición lo dice y deja Subir export desactivado» | aprobado; Vitest aprobado |
| El profesor de varias secciones ve sus tres secciones y ninguna otra | `test_varias_secciones_feature.py::test_el_profesor_de_varias_secciones_ve_sus_tres_secciones_y_ninguna_otra`; Vitest `tests/pantallas/MisSecciones.test.tsx`, «lista todas las secciones del profesor, una fila por sección, con su estado de carga»; Vitest `tests/pantallas/MisSecciones.test.tsx`, «dos secciones de una misma asignatura aparecen como filas distintas»; Vitest `tests/pantallas/MisSecciones.test.tsx`, «Subir export abre P3 con la sección de esa fila» | aprobado; Vitest aprobado; Vitest aprobado; Vitest aprobado |
| El profesor de varias secciones no alcanza una sección que no dicta | `test_varias_secciones_feature.py::test_el_profesor_de_varias_secciones_no_alcanza_una_sección_que_no_dicta` (4 ejemplos) | aprobado (4 de 4 ejemplos) |

### US-07: Subir el export y cargarlo en una sola transacción (P1, corte 1)

8 escenarios, 8 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| El export correcto queda publicado entero | `test_carga_feature.py::test_el_export_correcto_queda_publicado_entero` | aprobado |
| Un fallo en cualquier punto de la transacción no deja nada escrito | `test_carga_feature.py::test_un_fallo_en_cualquier_punto_de_la_transacción_no_deja_nada_escrito` (4 ejemplos) | aprobado (4 de 4 ejemplos) |
| Una restricción violada al final deshace la carga entera | `test_carga_feature.py::test_una_restricción_violada_al_final_deshace_la_carga_entera` | aprobado |
| Otro archivo no entra en una sección que ya tiene carga publicada | `test_carga_feature.py::test_otro_archivo_no_entra_en_una_sección_que_ya_tiene_carga_publicada` | aprobado |
| Un profesor no sube a una sección que no tiene asignada | `test_carga_feature.py::test_un_profesor_no_sube_a_una_sección_que_no_tiene_asignada` | aprobado |
| El coordinador no sube en el corte 1 | `test_carga_feature.py::test_el_coordinador_no_sube_en_el_corte_1` | aprobado |
| Dos subidas a la vez dejan una sola publicada | `test_carga_feature.py::test_dos_subidas_a_la_vez_dejan_una_sola_publicada` | aprobado |
| Cada export del profesor de varias secciones se publica solo en su sección | `test_varias_secciones_feature.py::test_cada_export_del_profesor_de_varias_secciones_se_publica_solo_en_su_sección` (3 ejemplos) | aprobado (3 de 3 ejemplos) |

### US-08: Rechazar exports con códigos que no son inventados (P1, corte 1)

4 escenarios, 4 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| Un solo código que no es inventado rechaza el archivo entero sin dejar rastro | `test_carga_feature.py::test_un_solo_código_que_no_es_inventado_rechaza_el_archivo_entero_sin_dejar_rastro` (3 ejemplos) | aprobado (3 de 3 ejemplos) |
| Los extremos del rango inventado pasan la guardia | `test_carga_feature.py::test_los_extremos_del_rango_inventado_pasan_la_guardia` (2 ejemplos) | aprobado (2 de 2 ejemplos) |
| Ningún campo de la petición apaga la guardia | `test_carga_feature.py::test_ningún_campo_de_la_petición_apaga_la_guardia` | aprobado |
| La guardia de la base rechaza un código que no es inventado aunque el programa falle | `test_carga_feature.py::test_la_guardia_de_la_base_rechaza_un_código_que_no_es_inventado_aunque_el_programa_falle` | aprobado |

### US-09: Reconocer un export ya cargado (P1, corte 1)

7 escenarios, 7 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| Subir otra vez el export publicado devuelve su constancia y no cambia nada | `test_carga_feature.py::test_subir_otra_vez_el_export_publicado_devuelve_su_constancia_y_no_cambia_nada` | aprobado |
| El mismo contenido con otro nombre se reconoce por la huella | `test_carga_feature.py::test_el_mismo_contenido_con_otro_nombre_se_reconoce_por_la_huella` | aprobado |
| Un archivo rechazado en una sección se publica después en la suya | `test_carga_feature.py::test_un_archivo_rechazado_en_una_sección_se_publica_después_en_la_suya` | aprobado |
| La base impide registrar dos veces la misma huella | `test_carga_feature.py::test_la_base_impide_registrar_dos_veces_la_misma_huella` | aprobado |
| Un export abierto y guardado de nuevo es otro archivo | `test_carga_feature.py::test_un_export_abierto_y_guardado_de_nuevo_es_otro_archivo` | aprobado |
| Un archivo publicado en otra sección se detiene sin datos de esa sección | `test_carga_feature.py::test_un_archivo_publicado_en_otra_sección_se_detiene_sin_datos_de_esa_sección` | aprobado |
| Un archivo publicado en una sección del profesor se detiene en otra de sus secciones | `test_varias_secciones_feature.py::test_un_archivo_publicado_en_una_sección_del_profesor_se_detiene_en_otra_de_sus_secciones` | aprobado |

### US-10: Rechazar filas inválidas y avisar de columnas dudosas (P1, corte 1)

8 escenarios, 8 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| El 5 de la fila 3 rechaza esa fila completa | `test_carga_feature.py::test_el_5_de_la_fila_3_rechaza_esa_fila_completa` | aprobado |
| Una celda de PI inválida en la fila 3 rechaza esa fila | `test_carga_feature.py::test_una_celda_de_pi_inválida_en_la_fila_3_rechaza_esa_fila` (7 ejemplos) | aprobado (7 de 7 ejemplos) |
| Una celda de PI vacía se carga como SIN_EVIDENCIA y no rechaza la fila | `test_carga_feature.py::test_una_celda_de_pi_vacía_se_carga_como_sin_evidencia_y_no_rechaza_la_fila` | aprobado |
| Un código vacío o repetido rechaza su fila | `test_carga_feature.py::test_un_código_vacío_o_repetido_rechaza_su_fila` (2 ejemplos) | aprobado (2 de 2 ejemplos) |
| Una columna de PI que no está en el plan se ignora con aviso | `test_carga_feature.py::test_una_columna_de_pi_que_no_está_en_el_plan_se_ignora_con_aviso` | aprobado |
| Si todas las filas se rechazan, la carga no se publica | `test_carga_feature.py::test_si_todas_las_filas_se_rechazan_la_carga_no_se_publica` | aprobado |
| Con la guardia apagada, un código mal formado rechaza solo su fila | `test_carga_feature.py::test_con_la_guardia_apagada_un_código_mal_formado_rechaza_solo_su_fila` | aprobado |
| La base no deja publicar cuentas que no cuadran | `test_carga_feature.py::test_la_base_no_deja_publicar_cuentas_que_no_cuadran` (2 ejemplos) | aprobado (2 de 2 ejemplos) |

### US-11: Detener un archivo ilegible sin dejar rastro (P1, corte 1)

2 escenarios, 2 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| Un archivo que no se puede leer se detiene antes de registrar nada | `test_carga_feature.py::test_un_archivo_que_no_se_puede_leer_se_detiene_antes_de_registrar_nada` (7 ejemplos) | aprobado (7 de 7 ejemplos) |
| Un libro que se infla al descomprimirse se rechaza | `test_carga_feature.py::test_un_libro_que_se_infla_al_descomprimirse_se_rechaza` | aprobado |

### US-12: Rechazar la carga por su estructura (P1, corte 1)

3 escenarios, 3 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| Un defecto de estructura rechaza la carga entera y deja su motivo | `test_carga_feature.py::test_un_defecto_de_estructura_rechaza_la_carga_entera_y_deja_su_motivo` (4 ejemplos) | aprobado (4 de 4 ejemplos) |
| La base no acepta un motivo que no existe | `test_carga_feature.py::test_la_base_no_acepta_un_motivo_que_no_existe` | aprobado |
| Después de un rechazo, un archivo distinto es otro archivo y se publica | `test_carga_feature.py::test_después_de_un_rechazo_un_archivo_distinto_es_otro_archivo_y_se_publica` | aprobado |

### US-13: Rechazar el export de otra sección o periodo (P1, corte 1)

6 escenarios, 6 aprobados, 0 omitidos y 0 pendientes. El escenario «Un export que no declara su sección se detiene sin dejar rastro» se retira el 2026-11-17 con T084, como anunciaba su comentario, porque el primero de US-21 lo reemplaza con las mismas comprobaciones de la base.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| El export de la 411 subido en la 410 se rechaza | `test_carga_feature.py::test_el_export_de_la_411_subido_en_la_410_se_rechaza` | aprobado |
| Un curso o un periodo distinto en el nombre de hoja rechaza la carga | `test_carga_feature.py::test_un_curso_o_un_periodo_distinto_en_el_nombre_de_hoja_rechaza_la_carga` (2 ejemplos) | aprobado (2 de 2 ejemplos) |
| Si la hoja no declara la sección, se coteja el nombre del archivo | `test_carga_feature.py::test_si_la_hoja_no_declara_la_sección_se_coteja_el_nombre_del_archivo` | aprobado |
| Una hoja truncada a 31 caracteres se coteja igual | `test_carga_feature.py::test_una_hoja_truncada_a_31_caracteres_se_coteja_igual` | aprobado |
| El export de una sección del profesor no entra en otra de sus secciones de la misma asignatura | `test_varias_secciones_feature.py::test_el_export_de_una_sección_del_profesor_no_entra_en_otra_de_sus_secciones_de_la_misma_asignatura` | aprobado |
| El mismo número de sección en otra asignatura no basta para cargar el export | `test_varias_secciones_feature.py::test_el_mismo_número_de_sección_en_otra_asignatura_no_basta_para_cargar_el_export` | aprobado |

### US-14: Descartar nombres y valores leídos (P1, corte 1)

4 escenarios, 4 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| Los nombres del export no llegan a ninguna tabla | `test_carga_feature.py::test_los_nombres_del_export_no_llegan_a_ninguna_tabla` | aprobado |
| El rechazo dice fila, PI y motivo, nunca el valor leído | `test_carga_feature.py::test_el_rechazo_dice_fila_pi_y_motivo_nunca_el_valor_leído` | aprobado |
| Las columnas que no son PI del plan se descartan | `test_carga_feature.py::test_las_columnas_que_no_son_pi_del_plan_se_descartan` | aprobado |
| El nombre del archivo se guarda sin ruta | `test_carga_feature.py::test_el_nombre_del_archivo_se_guarda_sin_ruta` | aprobado |

### US-15: Descargar el R-17 generado desde la base (P1, corte 1)

7 escenarios, 7 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| R-17 del export correcto | `test_r17_constancia_feature.py::test_r17_del_export_correcto` | aprobado |
| R-17 del export con el 5 en la fila 3 | `test_r17_constancia_feature.py::test_r17_del_export_con_el_5_en_la_fila_3` | aprobado |
| Con reglas en borrador el R-17 sale provisional | `test_r17_constancia_feature.py::test_con_reglas_en_borrador_el_r17_sale_provisional` | aprobado |
| Con reglas aprobadas el R-17 sale sin franja | `test_r17_constancia_feature.py::test_con_reglas_aprobadas_el_r17_sale_sin_franja` | aprobado |
| El R-17 no lleva nombres de personas | `test_r17_constancia_feature.py::test_el_r17_no_lleva_nombres_de_personas` | aprobado |
| El R-17 de la 410 según quién lo pide | `test_r17_constancia_feature.py::test_el_r17_de_la_410_según_quién_lo_pide` (3 ejemplos) | aprobado (3 de 3 ejemplos) |
| Una carga rechazada no tiene R-17 | `test_r17_constancia_feature.py::test_una_carga_rechazada_no_tiene_r17` | aprobado |

### US-16: Recibir la constancia de la carga (P1, corte 1)

5 escenarios, 5 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| Constancia del export correcto en el R-17 | `test_r17_constancia_feature.py::test_constancia_del_export_correcto_en_el_r17` | aprobado |
| La constancia en JSON dice lo mismo que la hoja | `test_r17_constancia_feature.py::test_la_constancia_en_json_dice_lo_mismo_que_la_hoja` | aprobado |
| Constancia del export con el 5 en la fila 3 | `test_r17_constancia_feature.py::test_constancia_del_export_con_el_5_en_la_fila_3` | aprobado |
| Una carga rechazada también tiene constancia | `test_r17_constancia_feature.py::test_una_carga_rechazada_también_tiene_constancia` | aprobado |
| La constancia de la 410 según quién la pide | `test_r17_constancia_feature.py::test_la_constancia_de_la_410_según_quién_la_pide` (2 ejemplos) | aprobado (2 de 2 ejemplos) |

### US-17: Desplegar el piloto en Vercel con Neon y probarlo de punta a punta (P1, corte 1)

11 escenarios, 8 aprobados, 0 omitidos y 3 pendientes. Las pruebas de esta historia corren el 2026-11-17 y el 2026-11-18 contra Vercel y Neon, fuera de pytest, y su evidencia está en la sección «Despliegue». La mitad de `.env.example` del escenario de las variables corre además en pytest, con `tests/test_env_example.py`.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| Cada proyecto fija la región iad1 | `vercel.json` de `main` y `vercel api /v13/deployments` del despliegue de Production de cada proyecto | aprobado |
| El Front reescribe /api hacia el Back y todo queda en un solo origen | `vercel.json` del Front en `main` y `GET /api/sesion` sin cookie a la URL de Production del Front, con curl y con `herramientas_neon/e2e_version/produccion.spec.ts` | aprobado |
| La cookie de sesión es de primera parte y nunca pasa por el almacenamiento del navegador | `herramientas_neon/e2e_version/produccion.spec.ts`, con docente410 en P1 de Production | aprobado |
| Las variables del Back están en Vercel y no en el repositorio | `vercel env ls production --project abet-ulima-back` y `tests/test_env_example.py` | aprobado (2026-11-17, las cinco variables están en Production, de tipo Secret, y `.env.example` las nombra sin valor desde `fix/001-env-example-sin-valores`) |
| Los secretos del Back no quedan en ningún repositorio | búsqueda de las claves de `bd/.env.neon` en `git log -p --all` de los dos repositorios y `scripts/preflight.sh` | pendiente (con `DATABASE_URL` pasa, porque la clave de `abet_app` aparece 0 veces; el valor de `SESION_SECRETO` no está en la Mac, y la búsqueda no lo incluye) |
| La API se conecta a Neon por el pooler con el rol abet_app | 20 `GET /api/secciones?periodo=2026-2` con coordinacion en `produccion.spec.ts`, `vercel logs` de esa corrida y `pg_stat_activity` de la rama principal | aprobado |
| Preview trabaja sobre otra rama de Neon | conteos de las dos ramas del 2026-11-17 (la principal sin cargas y `develop` con las 2 de la prueba del 2026-11-09), T073 y T075 (2026-11-02) y T076 de la spec 003 | aprobado |
| Production sale solo de main | `vercel api /v9/projects` de los dos proyectos y los despliegues del push a `develop` del 2026-11-17 | aprobado |
| El equipo de Vercel no comparte el contenido para entrenar modelos | `vercel api /v2/teams/jeffangeloss-projects` | pendiente (`dataSharingConsent` está en `granted` por los términos de servicio; lo apaga Jefferson en Team Settings, Data Preferences, T070) |
| La guardia de datos inventados está encendida en el piloto | consulta de solo lectura de `pg_constraint` en la rama principal y `vercel env ls production` | pendiente (la restricción y la variable están, pero la subida que la guardia rechaza no corre en Production, porque la versión 0.1.0 no sube nada allí) |
| Prueba de humo de punta a punta con el export que trae el 5 en la fila 3 | `ABET_SIS_MED/herramientas_neon/humo_preview_con_error.sh` el 2026-11-18, con las dos pruebas de US-17 de `e2e/humo.spec.ts` del Front (f10fdc3) contra la vista previa de `develop` (Back 7da9aa4), después de restablecer la rama `develop` de Neon desde la principal, y `revisar_r17.py` sobre el R-17 descargado | aprobado |

### US-18: Reemplazar la carga publicada de una sección (P2, corte 2)

11 escenarios, 11 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| El export corregido reemplaza a la carga con el error | `test_reemplazo_y_cargas_feature.py::test_el_export_corregido_reemplaza_a_la_carga_con_el_error` (2 ejemplos) | aprobado (2 de 2 ejemplos) |
| Subir sin pedir el reemplazo no pisa la carga publicada | `test_reemplazo_y_cargas_feature.py::test_subir_sin_pedir_el_reemplazo_no_pisa_la_carga_publicada`; Vitest `tests/pantallas/SubirExport.test.tsx`, «un 409 de la sección con carga publicada pregunta si se reemplaza y reenvía el archivo con reemplaza» | aprobado |
| Un reemplazo con un archivo ilegible no cambia nada | `test_reemplazo_y_cargas_feature.py::test_un_reemplazo_con_un_archivo_ilegible_no_cambia_nada`; Vitest `tests/pantallas/SubirExport.test.tsx`, «en el reemplazo, el 422 del archivo que no abre muestra que la carga publicada no cambió» | aprobado |
| Un reemplazo que rechaza todas las filas no quita la carga vigente | `test_reemplazo_y_cargas_feature.py::test_un_reemplazo_que_rechaza_todas_las_filas_no_quita_la_carga_vigente` | aprobado |
| Un reemplazo fallido no bloquea el siguiente | `test_reemplazo_y_cargas_feature.py::test_un_reemplazo_fallido_no_bloquea_el_siguiente` | aprobado |
| El mismo archivo de la carga publicada no la reemplaza | `test_reemplazo_y_cargas_feature.py::test_el_mismo_archivo_de_la_carga_publicada_no_la_reemplaza` | aprobado |
| Volver al export anterior reutiliza su archivo | `test_reemplazo_y_cargas_feature.py::test_volver_al_export_anterior_reutiliza_su_archivo` | aprobado |
| No se reemplaza una carga que ya no es la vigente | `test_reemplazo_y_cargas_feature.py::test_no_se_reemplaza_una_carga_que_ya_no_es_la_vigente` | aprobado |
| El profesor no reemplaza la carga de otra sección | `test_reemplazo_y_cargas_feature.py::test_el_profesor_no_reemplaza_la_carga_de_otra_sección` | aprobado |
| La base impide dos cargas publicadas en la misma sección | `test_reemplazo_y_cargas_feature.py::test_la_base_impide_dos_cargas_publicadas_en_la_misma_sección` | aprobado |
| La base no deja que una carga reemplace a otra de otra sección | `test_reemplazo_y_cargas_feature.py::test_la_base_no_deja_que_una_carga_reemplace_a_otra_de_otra_sección` | aprobado |

### US-19: Ver las cargas a mi alcance (P2, corte 2)

5 escenarios, 5 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| El coordinador ve las cargas de todas las secciones | `test_reemplazo_y_cargas_feature.py::test_el_coordinador_ve_las_cargas_de_todas_las_secciones` | aprobado |
| El coordinador filtra por sección | `test_reemplazo_y_cargas_feature.py::test_el_coordinador_filtra_por_sección` | aprobado |
| El profesor ve solo las cargas de su sección | `test_reemplazo_y_cargas_feature.py::test_el_profesor_ve_solo_las_cargas_de_su_sección` | aprobado |
| La constancia de una carga reemplazada sigue disponible | `test_reemplazo_y_cargas_feature.py::test_la_constancia_de_una_carga_reemplazada_sigue_disponible` | aprobado |
| La lista no expone datos que la base no guarda | `test_reemplazo_y_cargas_feature.py::test_la_lista_no_expone_datos_que_la_base_no_guarda`; Vitest `tests/pantallas/Cargas.test.tsx`, «no muestra nombres de estudiantes, valores leídos ni rutas locales» | aprobado |

### US-20: Recibir el código de acceso en el correo institucional (P2, corte 2)

5 escenarios, 0 aprobados, 5 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| Un usuario autorizado recibe su código | `test_acceso_feature.py::test_un_usuario_autorizado_recibe_su_código` | omitido (Escenario de US-20 (corte 2), pendiente de T018, el dominio y la cuenta de Resend de Jefferson, y de T083 y T086.) |
| La respuesta es la misma exista o no el correo | `test_acceso_feature.py::test_la_respuesta_es_la_misma_exista_o_no_el_correo` (3 ejemplos) | omitido (Escenario de US-20 (corte 2), pendiente de T018, el dominio y la cuenta de Resend de Jefferson, y de T083 y T086.) |
| El código vigente abre la sesión | `test_acceso_feature.py::test_el_código_vigente_abre_la_sesión` | omitido (Escenario de US-20 (corte 2), pendiente de T018, el dominio y la cuenta de Resend de Jefferson, y de T083 y T086.) |
| Un código que ya no sirve no abre sesión | `test_acceso_feature.py::test_un_código_que_ya_no_sirve_no_abre_sesión` (3 ejemplos) | omitido (Escenario de US-20 (corte 2), pendiente de T018, el dominio y la cuenta de Resend de Jefferson, y de T083 y T086.) |
| Pedir códigos en ráfaga no llena el buzón | `test_acceso_feature.py::test_pedir_códigos_en_ráfaga_no_llena_el_buzón` | omitido (Escenario de US-20 (corte 2), pendiente de T018, el dominio y la cuenta de Resend de Jefferson, y de T083 y T086.) |

### US-21: Confirmar la sección cuando el archivo no la declara (P3, corte 2)

4 escenarios, 4 aprobados, 0 omitidos y 0 pendientes.

| Escenario | Prueba | Resultado |
| --- | --- | --- |
| Un export que no declara su sección espera la confirmación sin escribir nada | `test_carga_feature.py::test_un_export_que_no_declara_su_sección_espera_la_confirmación_sin_escribir_nada` | aprobado |
| La sección confirmada publica la carga y la constancia lo dice | `test_carga_feature.py::test_la_sección_confirmada_publica_la_carga_y_la_constancia_lo_dice` | aprobado |
| La confirmación no vale si nombra otra sección | `test_carga_feature.py::test_la_confirmación_no_vale_si_nombra_otra_sección` | aprobado |
| La confirmación no pasa por encima de una sección declarada distinta | `test_carga_feature.py::test_la_confirmación_no_pasa_por_encima_de_una_sección_declarada_distinta` | aprobado |

## Pantallas en Vitest

Los pasos de pantalla de los `.feature` los comprueba Vitest con Testing Library (T045 y T085). Los escenarios con un paso de pantalla traen su prueba de Vitest en la tabla de su historia, y esta tabla suma todas las del Front con la corrida del 2026-11-17 de `npx vitest run` en la rama `feat/001-corte-2` del Front.

| Grupo de pruebas | Archivo | Historias que la spec le asigna | Pruebas | Resultado |
| --- | --- | --- | --- | --- |
| P1 Ingreso | `Ingreso.test.tsx` | US-05, US-17, US-20 | 7 | aprobado (7 de 7) |
| P2 Mis secciones | `MisSecciones.test.tsx` | US-06 | 10 | aprobado (10 de 10) |
| P3 Subir export | `SubirExport.test.tsx` | US-07, US-08, US-09, US-11, US-12, US-13, US-18, US-21 | 32 | aprobado (32 de 32) |
| P4 Resultado de la carga | `ResultadoCarga.test.tsx` | US-07, US-10, US-12, US-13, US-14, US-15, US-16, US-17, US-18 | 19 | aprobado (19 de 19) |
| P5 Cargas | `Cargas.test.tsx` | US-18, US-19 | 17 | aprobado (17 de 17) |
| App | `App.test.tsx` | transversal | 10 | aprobado (10 de 10) |
| AvisosCarga | `componentes.test.tsx` | transversal | 2 | aprobado (2 de 2) |
| Mensaje | `componentes.test.tsx` | transversal | 2 | aprobado (2 de 2) |
| TablaRechazos | `componentes.test.tsx` | transversal | 1 | aprobado (1 de 1) |
| api.ts | `api.test.ts` | transversal | 27 | aprobado (27 de 27) |
| horaDeLima | `formato.test.ts` | transversal | 4 | aprobado (4 de 4) |
| resumenFilas | `formato.test.ts` | transversal | 2 | aprobado (2 de 2) |
| vercel.json del Front | `vercel.test.ts` | US-17 | 6 | aprobado (6 de 6) |

Total del Front, 10 archivos y 139 pruebas aprobadas, frente a 9 archivos y 85 en `develop` (7f6c72b). La prueba de humo `e2e/humo.spec.ts` (Playwright para Node, T053 y T087) recorre P1 a P5, con el reemplazo en P5, contra el Back y el Front locales, y no corre con `npm test`. Su corrida contra la vista previa de `develop` espera la fusión de las dos ramas (sección «Corte 2»).

## Verificación manual (T062)

T062 queda para Jefferson, porque exige un navegador y el recorrido de un humano. La tabla muestra qué comprobar, y la evidencia queda en blanco hasta que la anote.

| Flujo | Cómo | Evidencia |
| --- | --- | --- |
| El profesor de la 410 sube el export con el 5 en la fila 3 | P1, P2, P3 con `export_inventado_410_con_error.xlsx` | pendiente |
| La constancia dice 11 leídas, 10 aceptadas, 1 rechazada, con el rechazo de la fila 3 en el PI 5.2 | P4 | pendiente |
| El R-17 se descarga con el nombre `R017_450002_410_2026-2_PROVISIONAL.xlsx` y la huella de la constancia es la de `shasum -a 256` del archivo | P4 y terminal | pendiente |
| Subir otra vez el mismo archivo dice que ya se cargó, y subir otro archivo a la 410 responde el 409 | P3 | pendiente |
| El coordinador ve las secciones 410 y 411, no ve el botón Subir export y descarga el R-17 | P2 y P4 | pendiente |
| El profesor de varias secciones ve sus tres secciones y ninguna otra | P2 | pendiente |

### Guía para hacerla

La prueba usa un clúster de PostgreSQL desechable que arma el propio guion y no toca `abet_sis_med_dev`, porque las pruebas ya no escriben en esa base.

1. En una terminal del Back, ejecutar `bash scripts/api_local.sh --sin-https`. El guion arma el clúster, aplica las migraciones y los datos inventados, asigna una contraseña al azar a `docente410@example.invalid`, `docente.varias@example.invalid` y `coordinacion@example.invalid`, imprime la ruta de un archivo temporal con esas contraseñas y deja la API en `http://127.0.0.1:8000/api`. La opción `--sin-https` quita el atributo Secure de la cookie, solo en este servidor local.
2. En otra terminal, leer ese archivo con `cat <ruta impresa>`. Las contraseñas no se pegan en el chat ni en `audit.md`.
3. En una terminal del Front, ejecutar `npm run dev` y abrir la dirección que imprime Vite, por omisión `http://localhost:5173`. El proxy de Vite reenvía `/api` a la API local.
4. Ingresar como `docente410@example.invalid`, abrir la 410 de 450002 y subir `tests/datos_inventados/export_inventado_410_con_error.xlsx` del Back. Anotar el identificador de la carga, que aparece en la dirección de P4, los conteos 11, 10 y 1, la fila 3 con el PI 5.2 y el aviso del PI 5.3.
5. Descargar el R-17 y comprobar que el nombre termina en `_PROVISIONAL.xlsx`. Calcular `shasum -a 256` del export y compararlo con la huella de la constancia.
6. Subir de nuevo el mismo archivo y comprobar que P3 avisa que ya se cargó. Subir `tests/datos_inventados/sintetico_20262_450002_410.xlsx` y comprobar el 409 con «La sección 410 ya tiene una carga publicada. No se cargó el archivo.».
7. Cerrar sesión e ingresar como `coordinacion@example.invalid`. Comprobar que P2 lista las secciones 410 y 411, que no ofrece Subir export y que ofrece el resultado y el R-17 de la 410.
8. Cerrar sesión e ingresar como `docente.varias@example.invalid`. Comprobar las tres secciones, la 412 de 450002 y la 410 y la 412 de 450010.
9. Cortar el guion del Back con Ctrl+C, que apaga y borra el clúster y el archivo de contraseñas, y copiar la evidencia a la tabla de arriba.

## Requisitos funcionales

Cada requisito toma sus escenarios de las reglas BR que lo citan como fuente y de las historias que se declaran en el script. Las pruebas unitarias salen de los nombres `test_br_*` de la suite completa. El estado es **Cubierto** si todos sus escenarios del corte 1 están aprobados y **Parcial** si alguno está omitido o pendiente.

| FR | Historias y reglas | Escenarios del corte 1 | Pruebas unitarias o de pantalla | Estado |
| --- | --- | --- | --- | --- |
| FR-001 | US-01; sin regla BR | 2 aprobados, 5 omitidos y 0 pendientes | Flyway sobre Neon: lo comprueban T021 y T027, no el Back local | Parcial |
| FR-002 | US-01; sin regla BR | 1 aprobado, 0 omitidos y 0 pendientes | Traslado de bd/ a db/ con git subtree, verificado por el escenario de la CI | Cubierto |
| FR-003 | US-04; BR-ACCESO-01 | 5 aprobados, 0 omitidos y 0 pendientes | solo escenarios | Cubierto |
| FR-004 | US-02; sin regla BR | 7 aprobados, 1 omitido y 0 pendientes | solo escenarios | Parcial |
| FR-005 | US-08, US-17; BR-CARGA-07 | 4 aprobados, 0 omitidos y 1 pendiente | `test_api_cargas.py` (3), `test_carga.py` (22), `test_validacion.py` (17) | Parcial |
| FR-006 | US-03, US-04; BR-ACCESO-01, BR-PERIODO-03 | 10 aprobados, 0 omitidos y 0 pendientes | solo escenarios | Cubierto |
| FR-007 | US-02, US-03, US-07, US-15; BR-PERIODO-01, BR-PERIODO-02 | 8 aprobados, 0 omitidos y 0 pendientes | `test_api_secciones.py` (8) | Cubierto |
| FR-008 | US-07; BR-CARGA-01 | 3 aprobados, 0 omitidos y 0 pendientes | `test_carga.py` (12), `test_comando.py` (3), `test_esqueleto.py` (6), `test_validacion.py` (1) | Cubierto |
| FR-009 | US-05, US-06, US-17; BR-ACCESO-02, BR-ACCESO-03, BR-ACCESO-04, BR-ACCESO-05, BR-ACCESO-06 | 11 aprobados, 0 omitidos y 0 pendientes (el de la cookie de US-17, aprobado el 2026-11-17) | `test_api_secciones.py` (1), `test_api_sesion.py` (28) | Cubierto |
| FR-010 | US-05, US-06, US-07, US-15, US-16; BR-ACCESO-06, BR-ACCESO-07, BR-ACCESO-08, BR-CARGA-01 | 15 aprobados, 0 omitidos y 0 pendientes | `test_api_cargas.py` (4), `test_api_secciones.py` (4), `test_api_sesion.py` (9), `test_carga.py` (12), `test_comando.py` (11), `test_permisos.py` (23), `test_validacion.py` (1), `test_varias_secciones.py` (2) | Cubierto |
| FR-011 | US-06, US-17; BR-PERIODO-04 | 9 aprobados, 0 omitidos y 0 pendientes (el del pooler de US-17, aprobado el 2026-11-17) | `test_api_cargas.py` (1), `test_api_secciones.py` (13); Vitest, grupos «P2 Mis secciones» (10) | Cubierto |
| FR-012 | US-06, US-07, US-08, US-09, US-11, US-13; BR-CARGA-01, BR-CARGA-02, BR-CARGA-03, BR-CARGA-04, BR-CARGA-09, BR-CARGA-10, BR-CARGA-11 | 25 aprobados, 0 omitidos y 0 pendientes | `test_api_cargas.py` (8), `test_carga.py` (78), `test_comando.py` (5), `test_demo_punta_a_punta.py` (2), `test_lector.py` (8), `test_validacion.py` (28), `test_varias_secciones.py` (6) | Cubierto |
| FR-013 | US-06, US-08, US-09, US-11, US-13; BR-CARGA-03, BR-CARGA-05 | 9 aprobados, 0 omitidos y 0 pendientes | `test_api_cargas.py` (4), `test_carga.py` (16), `test_lector.py` (39), `test_validacion.py` (1) | Cubierto |
| FR-014 | US-06, US-07, US-08, US-09, US-11, US-13; BR-CARGA-03, BR-CARGA-06, BR-CARGA-09 | 14 aprobados, 0 omitidos y 0 pendientes | `test_api_cargas.py` (3), `test_carga.py` (28), `test_comando.py` (1), `test_demo_punta_a_punta.py` (1), `test_lector.py` (3), `test_validacion.py` (1), `test_varias_secciones.py` (1) | Cubierto |
| FR-015 | US-07, US-10, US-14; BR-CARGA-14, BR-CARGA-15 | 8 aprobados, 0 omitidos y 0 pendientes | `test_api_cargas.py` (1), `test_carga.py` (12), `test_lector.py` (20), `test_validacion.py` (54) | Cubierto |
| FR-016 | US-07, US-12, US-13; BR-CARGA-11, BR-CARGA-12, BR-CARGA-13 | 11 aprobados, 0 omitidos y 0 pendientes | `test_api_cargas.py` (3), `test_carga.py` (28), `test_comando.py` (1), `test_lector.py` (6), `test_validacion.py` (43), `test_varias_secciones.py` (5) | Cubierto |
| FR-017 | US-07, US-10; BR-CARGA-16 | 3 aprobados, 0 omitidos y 0 pendientes | `test_carga.py` (5), `test_comando.py` (1), `test_lector.py` (3), `test_validacion.py` (4) | Cubierto |
| FR-018 | US-14, US-15, US-16, US-17; BR-CARGA-08, BR-CARGA-17, BR-R17-07 | 6 aprobados, 0 omitidos y 1 pendiente | `test_api_cargas.py` (1), `test_carga.py` (8), `test_demo_punta_a_punta.py` (1), `test_lector.py` (7), `test_plantilla_r17.py` (10), `test_r17.py` (3), `test_validacion.py` (2) | Parcial |
| FR-019 | US-10, US-15, US-16; BR-R17-02, BR-R17-03, BR-R17-04, BR-R17-05, BR-R17-06, BR-R17-07, BR-R17-08 | 7 aprobados, 0 omitidos y 0 pendientes | `test_api_cargas.py` (2), `test_plantilla_r17.py` (23), `test_r17.py` (32) | Cubierto |
| FR-020 | US-15, US-16; BR-R17-01, BR-R17-09 | 4 aprobados, 0 omitidos y 0 pendientes | `test_api_cargas.py` (1), `test_comando.py` (1), `test_demo_punta_a_punta.py` (2), `test_r17.py` (9) | Cubierto |
| FR-021 | US-16; BR-R17-09, BR-R17-10 | 5 aprobados, 0 omitidos y 0 pendientes | `test_api_cargas.py` (1), `test_comando.py` (2), `test_constancia.py` (22), `test_r17.py` (5) | Cubierto |
| FR-022 | US-05, US-06, US-07; sin regla BR | 25 aprobados, 0 omitidos y 0 pendientes | Vitest, grupos «P1 Ingreso» (7); Vitest, grupos «P2 Mis secciones» (10); Vitest, grupos «P3 Subir export» (17); Vitest, grupos «P4 Resultado de la carga» (13); Vitest, grupos «App» (5) | Cubierto |
| FR-023 | US-05, US-17; BR-ACCESO-03 | 11 aprobados, 0 omitidos y 0 pendientes (los de la cookie y la reescritura de US-17, aprobados el 2026-11-17) | `test_api_sesion.py` (3); Vitest, grupos «api.ts» (15) | Cubierto |
| FR-024 | US-17; sin regla BR | 8 aprobados, 0 omitidos y 3 pendientes | comprobaciones del 2026-11-17 y del 2026-11-18 contra Vercel y Neon (sección «Despliegue») y `test_env_example.py` (7) | Parcial |
| FR-025 | US-18; BR-CARGA-19 | 11 aprobados, 0 omitidos y 0 pendientes (corte 2) | `test_api_cargas.py` (13), `test_carga.py` (30); Vitest, grupos «P3 Subir export» (32) y «P5 Cargas» (17) | Cubierto |
| FR-026 | US-19; BR-CARGA-20 | 5 aprobados, 0 omitidos y 0 pendientes (corte 2) | `test_api_cargas.py` (9), `test_constancia.py` (2); Vitest, grupo «P5 Cargas» (17) | Cubierto |
| FR-027 | US-20; BR-ACCESO-09 | 0 aprobados, 5 omitidos y 0 pendientes (corte 2) | ninguna, porque espera a T018 | Corte 2, pendiente de T018 |
| FR-028 | ninguna; sin regla BR | ninguno | `test_lectura_gherkin_es.py` (12) | Cubierto |
| FR-029 | US-07, US-08, US-09, US-10, US-11, US-12, US-13, US-14, US-15, US-16; sin regla BR | 55 aprobados, 0 omitidos y 0 pendientes | solo escenarios | Cubierto |
| FR-030 | ninguna; sin regla BR | ninguno | `test_generador_exports.py` (73) | Cubierto |
| FR-031 | US-01; sin regla BR | 1 aprobado, 0 omitidos y 0 pendientes | La CI aplica las migraciones con psql, probado en local por el escenario de la CI | Cubierto |
| FR-032 | ninguna; sin regla BR | ninguno | bash scripts/preflight.sh y la entrada de MEMORIA.md se verifican en la etapa de commit | Parcial |

Resumen de requisitos, Corte 2, pendiente de T018 1, Cubierto 25, Parcial 6.

## Criterios de éxito

| SC | Estado | Evidencia |
| --- | --- | --- |
| SC-001 | Parcial | 98 de 107 escenarios del corte 1 aprobados, 6 omitidos y 3 pendientes. Ocho de US-17 se aprueban contra Vercel y Neon, siete el 2026-11-17 y uno el 2026-11-18, y el resto sale de la corrida local del 2026-10-30. |
| SC-002 | Parcial | 7 escenarios, 2 aprobados, 5 omitidos y 0 pendientes. Q01 a Q14 en Neon llegan con T021 y T027. |
| SC-003 | Cumplido en local | 3 escenarios, 3 aprobados, 0 omitidos y 0 pendientes; pruebas unitarias `test_demo_punta_a_punta.py` (5), `test_plantilla_r17.py` (4), `test_r17.py` (10) |
| SC-004 | Cumplido en local | 3 escenarios, 3 aprobados, 0 omitidos y 0 pendientes; pruebas unitarias `test_plantilla_r17.py` (9), `test_r17.py` (16) |
| SC-005 | Parcial | 10 escenarios, 9 aprobados, 0 omitidos y 1 pendiente; pruebas unitarias `test_api_cargas.py` (7), `test_carga.py` (38), `test_demo_punta_a_punta.py` (1), `test_lector.py` (38), `test_validacion.py` (17) |
| SC-006 | Parcial | 7 escenarios, 6 aprobados, 0 omitidos y 1 pendiente; pruebas unitarias `test_api_cargas.py` (1), `test_carga.py` (8), `test_demo_punta_a_punta.py` (1), `test_lector.py` (7), `test_plantilla_r17.py` (10), `test_r17.py` (3), `test_validacion.py` (2) |
| SC-007 | Parcial | 5 escenarios, 4 aprobados, 0 omitidos y 1 pendiente; pruebas unitarias `test_api_cargas.py` (3), `test_carga.py` (22), `test_validacion.py` (17). El conteo de abet.estudiante en Neon llega con T027. |
| SC-008 | Parcial | 8 escenarios, 7 aprobados, 1 omitido y 0 pendientes. El rol abet_app de Neon llega con T027 y T028. |
| SC-009 | Cumplido en local | 9 escenarios, 9 aprobados, 0 omitidos y 0 pendientes; pruebas unitarias `test_api_cargas.py` (4), `test_api_secciones.py` (3), `test_comando.py` (8), `test_permisos.py` (23), `test_varias_secciones.py` (2) |
| SC-010 | Cumplido en local | 2 escenarios, 2 aprobados, 0 omitidos y 0 pendientes; pruebas unitarias `test_r17.py` (5) |
| SC-011 | Parcial | 11 escenarios, 8 aprobados, 0 omitidos y 3 pendientes, comprobados el 2026-11-17 y el 2026-11-18 contra Production y la vista previa (sección «Despliegue»). |
| SC-012 | Pendiente | sin escenario propio. bash scripts/preflight.sh y la verificación de autoría corren en la etapa de commit y en cada PR. |

## Reglas de negocio

Cada regla de las cuatro specs vivas con sus escenarios y sus pruebas unitarias. Es la tabla que pide la auditoría de la fase 3 (T039).

| Regla | Escenarios (aprobados, omitidos, pendientes) | Pruebas unitarias | Estado |
| --- | --- | --- | --- |
| BR-ACCESO-01 | 5, 0, 0 | ninguna | Aprobada |
| BR-ACCESO-02 | 1, 0, 0 | `test_api_sesion.py` (3) | Aprobada |
| BR-ACCESO-03 | 2, 0, 1 | `test_api_sesion.py` (3) | Aprobada en local; queda abierto lo omitido o pendiente |
| BR-ACCESO-04 | 2, 0, 0 | `test_api_sesion.py` (5) | Aprobada |
| BR-ACCESO-05 | 1, 0, 0 | `test_api_sesion.py` (8) | Aprobada |
| BR-ACCESO-06 | 5, 0, 0 | `test_api_secciones.py` (1), `test_api_sesion.py` (9) | Aprobada |
| BR-ACCESO-07 | 3, 0, 0 | `test_api_secciones.py` (3), `test_permisos.py` (13), `test_varias_secciones.py` (1) | Aprobada |
| BR-ACCESO-08 | 6, 0, 0 | `test_api_cargas.py` (4), `test_comando.py` (8), `test_permisos.py` (10), `test_varias_secciones.py` (1) | Aprobada |
| BR-ACCESO-09 | 0, 5, 0 | ninguna | Corte 2, pendiente de T018 |
| BR-CARGA-01 | 3, 0, 0 | `test_carga.py` (12), `test_comando.py` (3), `test_validacion.py` (1) | Aprobada |
| BR-CARGA-02 | 3, 0, 0 | `test_api_cargas.py` (1), `test_carga.py` (16), `test_demo_punta_a_punta.py` (1) | Aprobada |
| BR-CARGA-03 | 8, 0, 0 | `test_api_cargas.py` (1), `test_carga.py` (16), `test_lector.py` (1), `test_validacion.py` (1) | Aprobada |
| BR-CARGA-04 | 1, 0, 0 | `test_api_cargas.py` (1), `test_lector.py` (3) | Aprobada |
| BR-CARGA-05 | 2, 0, 0 | `test_api_cargas.py` (3), `test_lector.py` (38) | Aprobada |
| BR-CARGA-06 | 3, 0, 0 | `test_lector.py` (2) | Aprobada |
| BR-CARGA-07 | 4, 0, 1 | `test_api_cargas.py` (3), `test_carga.py` (22), `test_validacion.py` (17) | Aprobada en local; queda abierto lo omitido o pendiente |
| BR-CARGA-08 | 0, 0, 1 | `test_api_cargas.py` (1) | Parcial, solo prueba unitaria; 1 pendiente |
| BR-CARGA-09 | 5, 0, 0 | `test_api_cargas.py` (2), `test_carga.py` (12), `test_comando.py` (1), `test_demo_punta_a_punta.py` (1), `test_varias_secciones.py` (1) | Aprobada |
| BR-CARGA-10 | 3, 0, 0 | `test_api_cargas.py` (1), `test_carga.py` (4) | Aprobada |
| BR-CARGA-11 | 8, 0, 0 | `test_api_cargas.py` (2), `test_carga.py` (18), `test_comando.py` (1), `test_lector.py` (4), `test_validacion.py` (26), `test_varias_secciones.py` (5) | Aprobada |
| BR-CARGA-12 | 1, 0, 0 | `test_validacion.py` (3) | Aprobada |
| BR-CARGA-13 | 3, 0, 0 | `test_api_cargas.py` (1), `test_carga.py` (10), `test_lector.py` (2), `test_validacion.py` (14) | Aprobada |
| BR-CARGA-14 | 3, 0, 0 | `test_carga.py` (2), `test_lector.py` (18), `test_validacion.py` (11) | Aprobada |
| BR-CARGA-15 | 6, 0, 0 | `test_api_cargas.py` (1), `test_carga.py` (10), `test_lector.py` (2), `test_validacion.py` (43) | Aprobada |
| BR-CARGA-16 | 3, 0, 0 | `test_carga.py` (5), `test_comando.py` (1), `test_lector.py` (3), `test_validacion.py` (4) | Aprobada |
| BR-CARGA-17 | 4, 0, 0 | `test_carga.py` (8), `test_demo_punta_a_punta.py` (1), `test_lector.py` (7), `test_validacion.py` (2) | Aprobada |
| BR-CARGA-18 | 6, 0, 0 | `test_api_cargas.py` (9), `test_carga.py` (4), `test_validacion.py` (7) | Aprobada (corte 2) |
| BR-CARGA-19 | 11, 0, 0 | `test_api_cargas.py` (13), `test_carga.py` (30) | Aprobada (corte 2) |
| BR-CARGA-20 | 5, 0, 0 | `test_api_cargas.py` (9), `test_constancia.py` (2) | Aprobada (corte 2) |
| BR-PERIODO-01 | 1, 0, 0 | `test_api_secciones.py` (8) | Aprobada |
| BR-PERIODO-02 | 4, 0, 0 | ninguna | Aprobada |
| BR-PERIODO-03 | 4, 0, 0 | ninguna | Aprobada |
| BR-PERIODO-04 | 5, 0, 1 | `test_api_cargas.py` (1), `test_api_secciones.py` (1) | Aprobada en local; queda abierto lo omitido o pendiente |
| BR-R17-01 | 2, 0, 0 | `test_api_cargas.py` (1), `test_comando.py` (1), `test_demo_punta_a_punta.py` (2), `test_r17.py` (4) | Aprobada |
| BR-R17-02 | 3, 0, 0 | `test_plantilla_r17.py` (4), `test_r17.py` (10) | Aprobada |
| BR-R17-03 | 3, 0, 0 | `test_r17.py` (2) | Aprobada |
| BR-R17-04 | 1, 0, 0 | `test_plantilla_r17.py` (5), `test_r17.py` (6) | Aprobada |
| BR-R17-05 | 2, 0, 0 | `test_plantilla_r17.py` (2), `test_r17.py` (3) | Aprobada |
| BR-R17-06 | 3, 0, 0 | `test_api_cargas.py` (2), `test_r17.py` (2) | Aprobada |
| BR-R17-07 | 2, 0, 0 | `test_plantilla_r17.py` (10), `test_r17.py` (3) | Aprobada |
| BR-R17-08 | 2, 0, 0 | `test_plantilla_r17.py` (2), `test_r17.py` (6) | Aprobada |
| BR-R17-09 | 2, 0, 0 | `test_r17.py` (5) | Aprobada |
| BR-R17-10 | 3, 0, 0 | `test_api_cargas.py` (1), `test_comando.py` (2), `test_constancia.py` (22) | Aprobada |

Reglas sin prueba, ninguna.

## Lo que el corte 1 deja abierto

### Escenarios omitidos del corte 1

| Escenario | Historia | Razón |
| --- | --- | --- |
| Primera migración en una base vacía | US-01 | se comprueban en Neon con T021 y T027 |
| Repetir la migración no aplica nada nuevo | US-01 | se comprueban en Neon con T021 y T027 |
| Clean prohibido en la base compartida | US-01 | se comprueban en Neon con T021 y T027 |
| Las consultas de control pasan en la base recién preparada | US-01 | se comprueban en Neon con T021 y T027 |
| Las consultas de control no escriben en la base | US-01 | se comprueban en Neon con T021 y T027 |
| Los permisos de abet_app sobreviven a una nueva migración | US-02 | db/callbacks/afterMigrate__permisos_lectura.sql llega con el git subtree pull de preparacion-neon (T022 y T027) |

### Escenarios pendientes del corte 1

| Escenario | Historia | Razón |
| --- | --- | --- |
| Los secretos del Back no quedan en ningún repositorio | US-17 | falta buscar `SESION_SECRETO`, cuyo valor no está en la Mac |
| El equipo de Vercel no comparte el contenido para entrenar modelos | US-17 | el equipo tiene `dataSharingConsent` en `granted` (T070) |
| La guardia de datos inventados está encendida en el piloto | US-17 | la subida del export con el código 10000004 no corre en Production en la versión 0.1.0 |

### Escenarios del corte 2

Desde el 2026-11-17, 20 de los 25 escenarios de US-18 a US-21 están aprobados (sección «Corte 2»). Los 5 de US-20, que son 9 pruebas de pytest, siguen omitidos con la razón «Escenario de US-20 (corte 2), pendiente de T018, el dominio y la cuenta de Resend de Jefferson, y de T083 y T086.».

### Decisiones abiertas

La spec aplica un valor provisional a cada una, y el R-17 sale con la franja PROVISIONAL mientras la carrera no decida.

| ID | Decisión | Quién decide | Estado |
| --- | --- | --- | --- |
| D-01 | Trato de una celda de PI inválida | Coordinación de Ambiental | abierta, con valor provisional |
| D-02 | Sección cuando el archivo no la declara | Coordinación de Ambiental | abierta, con valor provisional |
| D-03 | Celdas con «-» o «NP» | Coordinación de Ambiental | abierta, con valor provisional |
| D-04 | Total Pts distinto de 4 | Coordinación de Ambiental | abierta, con valor provisional |
| D-05 | Trato del estudiante sin evidencia (fila H08 de la revisión de requisitos) | Coordinación de Ambiental | abierta, con valor provisional |
| D-06 | Niveles -1 y 5 de la rúbrica frente a la escala 1 a 4 | Coordinación de Ambiental | abierta, con valor provisional |
| D-07 | Un archivo por sección o uno por SO (fila H51 de la revisión de requisitos) | Coordinación de Ambiental | abierta, con valor provisional |
| D-08 | Plantilla oficial del R-17 | Coordinación de Ambiental y Oficina de Calidad | abierta, con valor provisional |
| D-09 | Plan de medición de 2026-2 | Coordinación de Ambiental | abierta, con valor provisional |
| D-10 | Autorización de datos reales (Ley 29733 y DS 016-2024-JUS) | Universidad de Lima | abierta, con valor provisional |
| D-11 | Quién reemplaza una carga publicada y hasta cuándo | Coordinación de Ambiental | abierta, con valor provisional |
| D-12 | Nombre del profesor en el R-17 y firma frente a validación en el sistema | Coordinación de Ambiental y Oficina de Calidad | abierta, con valor provisional |
| D-13 | Usuarios del piloto | Coordinación de Ambiental | abierta, con valor provisional |
| D-38 | Nivel esperado según el estadio del curso en la malla | Coordinación de Ambiental | abierta, con valor provisional (desde el 2026-11-18) |
| J-01 | Lenguaje del Back | Jefferson | decidida |
| J-02 | Uno o dos roles de aplicación en la base | Jefferson | decidida |
| J-03 | Identidad de la semana 1 | Jefferson | decidida |
| J-04 | Dominio propio y proveedor de correo | Jefferson | abierta, con valor provisional |
| J-05 | Organización de SonarQube Cloud | Jefferson | abierta, con valor provisional |
| J-06 | Traslado de `bd/` al Back y archivo de `ABET_ULIMA` | Jefferson | decidida |
| J-07 | Plan de Vercel para el piloto | Jefferson | decidida |
| J-08 | Controles de la CI | Jefferson | abierta, con valor provisional |
| J-09 | La prueba de humo corre en la CI o contra la vista previa | Jefferson | abierta, con valor provisional |
| J-10 | Respaldo diario del esquema `acceso` | Jefferson | decidida |

### Tareas abiertas de Neon, despliegue y de Jefferson

Salen de `tasks.md` del 2026-11-18 y se acortan a una línea. T062 es la verificación a mano de la sección anterior.

| Tarea | Dónde | Descripción |
| --- | --- | --- |
| T004 | Jefferson | Revisar y fusionar la solicitud de integración (pull request, PR) de `docs/plan-mvp` a `develop`, que aprueba la spec, y ratificar la constitución con su fecha |
| T018 | Jefferson | Comprar el dominio y abrir la cuenta de Resend (J-04) para que el registro del dominio se propague antes del corte 2; de ella dependen T083, T086 y los escenarios de US-20 |
| T022 | Jefferson | Fusionar `preparacion-neon` (4ff1952) en `main` de `ABET_ULIMA`, aprobar el traslado y archivar el repositorio en solo lectura cuando termine T023 |
| T070 | Jefferson | Apagar el entrenamiento de IA del equipo de Vercel, que sigue con `dataSharingConsent` en `granted`, y enviar la consulta a soporte de J-07 |

### Despliegue

La versión 0.1.0 llega a Production el 2026-11-17 en los dos proyectos de Vercel (T076), después de V1_10 en la rama principal de Neon (T077 de la spec 003). Esta sección reúne cada paso con su comando o prueba, su código HTTP cuando lo hay y su evidencia (T079). En Production corren solo los pasos que no escriben cargas, porque una carga del piloto no se puede borrar, y la prueba con cargas corre en la vista previa de `develop`, sobre su propia rama de Neon. Las comprobaciones con contraseña las corre Jefferson con `ABET_SIS_MED/herramientas_neon/comprobar_version.sh`, fuera de los repositorios, que antes pasa en local contra `scripts/api_local.sh`, y sus evidencias quedan sin contraseñas ni tokens en `ABET_SIS_MED/demo_version_010/`.

| Paso | Cómo | Evidencia |
| --- | --- | --- |
| Migración en Neon | `flyway -environment=neon migrate` desde el Windows, con V1_01 a V1_09 en las dos ramas (T021 y T027, 2026-11-02), V1_10 en `develop` (2026-11-09) y V1_10 en la principal con `herramientas_neon/migrar_neon.sh principal 12c6207 --confirmo-principal` (2026-11-17) | La principal queda en la versión 1.10, sin migraciones fallidas, con la marca production, los cuatro roles sin atributos de administración, `abet_app` con los permisos de `crear_rol_app.sql`, Q01 a Q14 en 0 y 0 cargas |
| Versión en `main` | PR «Versión 0.1.0» de `develop` a `main`, con `pruebas` y `flujo` en verde y merge commit | Back #22 en 7325231 y Front #14 en 0d693b9, cada uno con el mismo árbol que su `develop`; `release.yml` crea el tag `v0.1.0` y el Release «Versión 0.1.0» en los dos repositorios |
| Despliegue de Production | `vercel api /v9/projects` y `/v13/deployments` de cada proyecto | Back `dpl_8eDNfqHA62QB4AADYuRktHRaAT8M` desde `main` 7325231, en lugar del Redeploy de `develop` f8057d7 del 2026-11-02; Front `dpl_EjScFgZmaZ8AugUs458zYHfeA92v` desde `main` 0d693b9, en lugar del despliegue de la importación (`develop` f26f4a1). Los dos quedan READY, en la región iad1, con los alias `abet-ulima-back-gray.vercel.app` y `abet-ulima-front.vercel.app` |
| Push a `develop` | Fusión de los PR #21 del Back y #13 del Front en `develop`, a las 17:25 de Lima | Vistas previas READY de 4341bc9 y 35a4266, y Production sin cambios hasta la fusión en `main`; la vista previa del Back de `chore/version-0.1.0` queda cancelada por `ignoreCommand` |
| API de Production | `GET /api/sesion` sin cookie a `https://abet-ulima-back-gray.vercel.app` | 401, `application/json`, `Cache-Control: no-store` y `{"detail": "La sesión venció. Ingrese otra vez."}`, con iad1 en `x-vercel-id`. La API arranca solo si la marca de la base es production (`comprobar_base` de `app/configuracion.py`, al iniciar), así que su `DATABASE_URL` es la de la rama principal, que muestra después 2 conexiones de `abet_app` desde `pgbouncer` |
| Reescritura del Front | `GET /api/sesion` sin cookie a `https://abet-ulima-front.vercel.app` | El mismo 401 en JSON del Back, sin `Access-Control-Allow-Origin`, por la regla con `has` del dominio de Production; antes de la versión respondía 404 NOT_FOUND. `GET /` responde 200 sin la protección de Vercel |
| Variables de Production | `vercel env ls production --project abet-ulima-back` | `DATABASE_URL`, `SESION_SECRETO`, `PERIODO_VIGENTE`, `CONJUNTO_REGLAS` y `GUARDIA_DATOS_INVENTADOS`, de tipo Secret |
| `.env.example` sin valores | `tests/test_env_example.py` en `fix/001-env-example-sin-valores` y otra vez `vercel env ls production --project abet-ulima-back`, a las 21:12 de Lima | `.env.example` nombra las cinco variables sin valor y deja el valor del piloto de las tres que no son secretas en su comentario. Una copia tal cual no arranca la API, porque le falta `PERIODO_VIGENTE`, y deja la guardia encendida, ya que solo el valor 0 la apaga. Las cinco siguen en Production, de tipo Secret y ocultas |
| Secretos fuera de los repositorios | Búsqueda en `git log -p --all` de las cinco claves de `bd/.env.neon` y de la clave de `abet_app` codificada como en `DATABASE_URL` | 0 apariciones en los 63 commits del Back y en los 48 del Front, y `scripts/preflight.sh` sin fallas en los dos |
| Contraseñas de T074 | `herramientas_neon/asignar_claves.py`, que pide cada contraseña en la terminal de Jefferson y manda al Windows solo el hash | La principal guarda las credenciales de docente410, docente411 y coordinacion, con hash Argon2id, del 2026-11-17 a las 17:36; `develop` guarda las de docente410 y docente411, y desde el 2026-11-18 también la de coordinacion |
| Ingreso en Production | `herramientas_neon/e2e_version/produccion.spec.ts` contra `https://abet-ulima-front.vercel.app`, sin la clave de omisión, con docente410 en P1 | `POST /api/sesion` 200 desde el origen del Front, con `abet_sesion` HttpOnly, Secure, SameSite=Lax, Path=/ y Max-Age 43200, sin Domain y guardada solo para `abet-ulima-front.vercel.app`. `GET /api/sesion` da 200 con el rol PROFESOR, localStorage y sessionStorage no tienen ningún valor y `document.cookie` no muestra `abet_sesion`. P2 muestra la 410 sin carga, sin subir nada, y «Salir» da 204 y después 401 |
| Pooler y rol `abet_app` | 20 `GET /api/secciones?periodo=2026-2` seguidas con la sesión de coordinacion, en la misma prueba | 20 respuestas 200 con la 410 y la 411. Los 30 registros de la función de esa corrida, entre las 22:35 y las 22:38 UTC, son de nivel info, sin ningún «prepared statement» ni una subida, y `pg_stat_activity` de la rama principal muestra la conexión de `abet_app` desde `pgbouncer` |
| Rama de Neon de cada entorno | Consultas de solo lectura desde el Windows, después de la prueba de Production | La principal gana solo las 2 sesiones de la prueba, de docente410 y coordinacion, ya cerradas, y sigue con 0 cargas y 0 archivos; `develop` gana solo la sesión de la vista previa |
| Prueba con cargas en Preview | `e2e/humo.spec.ts` (T075, 2026-11-02) y `e2e/humo_csv.spec.ts` (T076 de la spec 003, 2026-11-09) contra la vista previa de `develop` | 2 passed en cada corrida, y la rama principal no gana ninguna carga |
| Humo con el 5 en la fila 3 | `herramientas_neon/humo_preview_con_error.sh` el 2026-11-18 a las 12:44 de Lima, después de restablecer la rama `develop` de Neon desde la principal, con las dos pruebas de US-17 de `e2e/humo.spec.ts` del Front (f10fdc3) contra la vista previa de `develop` (Back 7da9aa4), y después `herramientas_neon/e2e_version/vista_previa_r17.spec.ts` y `herramientas_neon/revisar_r17.py` | Antes de empezar, la 410 de `develop` no tiene cargas y la base tiene la marca preview. P1 a P4 da 11 filas leídas, 10 aceptadas y 1 rechazada, con la fila 3 fuera por el 5 del PI 5.2. `GET /api/cargas/1/r17.xlsx` responde 200 con `R017_450002_410_2026-2_PROVISIONAL.xlsx`, que trae 6 de 10, 6 de 10 y 7 de 10 (60,0 %, 60,0 % y 70,0 %) con meta 80 % y formato 0,0 %, una tabla de 30 filas sin 99000002 y la constancia 11 / 11 / 10 / 1. `abet.v_r17_por_pi` da los mismos 60,0, 60,0 y 70,0, Q01 a Q14 devuelven 0 filas y la principal sigue sin cargas antes y después. Las evidencias, sin contraseñas ni nombres, quedan en `ABET_SIS_MED/demo_us17/` |
| R-17 descargado en Preview | `herramientas_neon/e2e_version/vista_previa_r17.spec.ts`, en el que docente410 abre P4 de la 410 y pulsa «Descargar R-17», y `herramientas_neon/revisar_r17.py` | `GET /api/cargas/1/r17.xlsx` 200, con `nosniff`, entrega `R017_450002_410_2026-2_PROVISIONAL.xlsx`. Es el R-17 de la 410 cargada con el `.csv` el 2026-11-09, porque la carga del export con el 5 en la fila 3 ya no existe en `develop` |
| Tabla de estudiantes del R-17 | Lectura del libro con openpyxl en `revisar_r17.py` | 33 filas, de la 43 a la 75, con 11 estudiantes por 3 PI, solo códigos inventados y niveles de 1 a 4. Los 7, 7 y 8 de 11 de la tabla (63,6 %, 63,6 % y 72,7 %) coinciden con los bloques E24:E26 y P29:Q31, y ninguna celda trae una fórmula ni repite uno de los 12 nombres del export |
| Hoja «Constancia» del R-17 | La misma lectura | «Sin hoja (export de texto)», 11 / 11 / 11 / 0 filas, la huella SHA-256 del `.csv`, PUBLICADA, PROVISIONAL, subida por docente410, 5 avisos de dos tipos, 0 rechazos y la frase final. Su versión del programa es 0.0.0, porque `abet.carga` la guarda al cargar y esa carga es del 2026-11-09, antes de la 0.1.0 |

## Corte 2

El corte 2 se implementa el 2026-11-17 en las ramas `feat/001-corte-2` del Back (desde e981a31 de `develop`) y del Front (desde 7f6c72b), con las tareas T080 a T082, T084, T085 sin P1, T087 sin US-20 y T088. US-20 (T083 y T086) espera a T018, el dominio y la cuenta de Resend de Jefferson, y la versión 0.2.0 (T089) es de Jefferson. Todas las pruebas que escriben corren en un clúster desechable de PostgreSQL 18, nunca en localhost:5432, y solo con datos inventados.

| Paso | Cómo | Evidencia |
| --- | --- | --- |
| Contrato antes del código | Sección 10 de `docs/03-api/contrato.md` del Front contra los `.feature` de la rama | 0 mensajes de los escenarios sin contrato. El único mensaje del contrato sin escenario es el de la marca de entorno de T077, que ya falta en `develop` |
| Esquema OpenAPI | `app.openapi()` del Back | 6 caminos, como pide la sección 10 del contrato sin US-20, con `seccion_id` en `GET /api/cargas` y `reemplaza` en la subida |
| Aceptación del Back | `uv run --frozen --no-build pytest -q -p no:cacheprovider tests/aceptacion -rA` | 300 passed y 14 skipped, con los 20 escenarios de US-18, US-19 y US-21 aprobados y los 5 de US-20 omitidos |
| Suite completa del Back | `uv run --frozen --no-build pytest -q -p no:cacheprovider` | 1289 passed y 15 skipped in 141.47s (0:02:21), frente a 1187 passed y 19 skipped de `develop` en e981a31 |
| Front | `npx vitest run`, `npx tsc --noEmit`, `npm run build` y `bash scripts/preflight.sh` | 10 archivos y 139 pruebas aprobadas, la compilación sin errores y la revisión previa sin fallas |
| Prueba de humo local | `bash scripts/api_local.sh --sin-https` del Back, Vite en el puerto 5173 y `bash scripts/e2e.sh e2e/humo.spec.ts` del Front con `EXPORT_CON_ERROR` y `EXPORT_CORRECTO` | 3 passed. docente410 sube el export con el error (11 / 10 / 1), docente.varias recibe 403 en la 410 y docente410 reemplaza en P5 esa carga por el export correcto, con P4 en 11 / 11 / 0 y P5 con «Vigente, reemplaza a la carga 1» y «Reemplazada por la carga 2» |
| R-17 de la carga que reemplaza | `herramientas_neon/revisar_r17.py` sobre el `R017_450002_410_2026-2_PROVISIONAL.xlsx` que descarga la prueba de humo, contra `sintetico_20262_450002_410.xlsx` | 0 fallas, 33 filas desde la 43, 7, 7 y 8 de 11 (63,6 %, 63,6 % y 72,7 %), ninguna fórmula ni nombre y la hoja «Constancia» con 11 / 11 / 11 / 0, la huella del export y PUBLICADA. La evidencia, sin contraseñas, queda en `ABET_SIS_MED/demo_corte2/` |
| Revisión independiente | Un subagente con el modelo de la sesión y esfuerzo alto revisa en solo lectura el diff de los dos repositorios | Ningún hallazgo de severidad alta ni media. De los tres de severidad baja, dos se resuelven con su prueba (un `seccion_id` entero que no es de ninguna sección recibe el 403 único, y el 200 del mismo archivo manda aunque `reemplaza` nombre otra carga) y uno se acepta (P3 no vuelve a ofrecer el reemplazo si otra persona reemplaza la carga mientras pregunta) |
| Escenario 1 de US-21 y FR-013 de la spec 003 | Cotejo de su texto con BR-CARGA-11 y con US-30 de la spec 003, que saca la sección de un `.csv` o un `.xls` solo del nombre, y `test_carga.py` con un `.csv` sin sección confirmado | La pregunta no nombra la hoja, así que vale para los tres formatos y su texto no cambia. El `.csv` «notas 410.csv» recibe la misma pregunta y, al confirmarla, se publica con la hoja nula y el AVISO SECCION_SIN_DECLARAR. Los textos del corte 1 que `spec.md` conservaba con la forma anterior a la spec 003 pasan a la forma vigente |
| Prueba de humo contra la vista previa | `e2e/humo.spec.ts` contra la vista previa de `develop` y su rama de Neon | Pendiente (T099), porque exige empujar y fusionar las dos ramas con el permiso de Jefferson |
| US-20 | Escenarios de `acceso.feature` | Pendiente de T018, T083 y T086 |

El corte 2 no cambia la base. El reemplazo usa `reemplaza_carga_id`, `uq_carga_reemplaza`, `fk_carga_reemplaza` y el estado REEMPLAZADA de V1_07, el aviso SECCION_SIN_DECLARAR de V1_09 y el UPDATE de `estado` que `crear_rol_app.sql` ya da a `abet_app`, así que Neon no necesita ninguna migración para esta versión.
