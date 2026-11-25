# Audit: Oportunidades de mejora en la carga, con semáforo, declaración y R-17 desde la base

**Fecha**: 2026-11-24, cierre de T050  
**Spec**: [spec.md](./spec.md)  
**Plan**: [plan.md](./plan.md)  
**Comando**: `ABET_FRONT_RAIZ=<Front> uv run --frozen --no-build python -m pytest -q -p no:cacheprovider` y `bash db/pruebas/correr_pruebas.sh` en el Back, `scripts/matriz_cumplimiento.py --front <Front> --comprobar`, `npm run build`, `npm test` y `npx tsc --noEmit` en el Front, y `npx playwright test e2e/humo.spec.ts` contra `bash scripts/api_local.sh --sin-https` del Back y Vite  
**Resultado**: corrida de cierre del 2026-11-24 sobre `feat/005-oportunidades-de-mejora`, con el Back en 027c5be y el Front en a579f59. La suite completa del Back da 2560 passed y 15 skipped in 873.45s (0:14:33), con los 118 casos de los cuatro `.feature` de la spec 005 aprobados, 23 de ellos delegados a Vitest; `bash db/pruebas/correr_pruebas.sh` da «RESULTADO: todo pasó»; `scripts/matriz_cumplimiento.py --comprobar` sale con 0 y da 32 historias, 237 escenarios, 87 reglas, 10 escenarios pendientes con su razón y 0 huecos; en el Front, `npm run build` y `npx tsc --noEmit` terminan sin errores y `npm test` da 26 archivos y 378 pruebas aprobadas con 1 `todo`; el humo local da 5 passed en `e2e/humo.spec.ts` y 10 passed en `e2e/visual.spec.ts`  
**Estado**: Spec 005 construida en `feat/005-oportunidades-de-mejora` del Back y del Front, sin push. Faltan T024 (migrar `develop` de Neon con V1_15), el despliegue (T060 a T062), T046 contra la vista previa de `develop` y T063 y T064 hacia `main`, que son de Jefferson. T005, T009 y T023 siguen abiertas.

Esta auditoría cruza cada historia de usuario (user story, US) de la spec 005 con sus escenarios en Gherkin, la prueba que los ejecuta y su resultado del 2026-11-24. Los escenarios con `@delegado_a_vitest` los comprueban las pruebas de `tests/spec005/` del Front, y sus pasos en el Back dejan la propiedad «delegado_a_vitest» con el nombre de la prueba. La coincidencia de cada título con una prueba que existe en el Front la comprueba `scripts/matriz_cumplimiento.py` con la misma regla de la spec 008 (título exacto, sin `it.todo` ni `skip`), aplicada a la spec 005 en una corrida puntual del generador, sin cambiar su salida, que da 85 de 85 escenarios con su prueba. Las 15 pruebas omitidas de la suite no tocan esta spec, porque son los escenarios de US-20 que esperan a T018, los de `base_neon.feature` que se comprueban en Neon y una prueba de `tests/test_cluster_desechable.py` que solo corre en la CI.

## Resumen

| Conjunto | Escenarios | Casos | Con pytest-bdd | Delegados a Vitest | Pendientes |
| --- | --- | --- | --- | --- | --- |
| Spec 005 (US-45 a US-54) | 85 | 118 | 62 | 23 | 0 |

| Historia | Escenarios | Casos | Delegados a Vitest |
| --- | --- | --- | --- |
| US-45 | 11 | 19 | 0 |
| US-46 | 6 | 8 | 6 |
| US-47 | 20 | 35 | 3 |
| US-48 | 7 | 7 | 5 |
| US-49 | 8 | 10 | 2 |
| US-50 | 8 | 8 | 0 |
| US-51 | 4 | 7 | 0 |
| US-52 | 5 | 5 | 5 |
| US-53 | 9 | 11 | 1 |
| US-54 | 7 | 8 | 1 |

## Historias

Los escenarios viven en `specs/005-oportunidades-de-mejora/aceptacion/`, en `semaforo.feature` (S), `declaracion.feature` (D), `r17_desde_la_base.feature` (R) y `navegacion.feature` (N). Sus pasos de pytest-bdd están en `tests/aceptacion/pasos/test_semaforo_feature.py`, `test_declaracion_feature.py` y `test_r17_desde_la_base_feature.py`, con los comunes en `conftest.py`. Las pruebas de Vitest están en `tests/spec005/` del Front.

| Historia | Escenario | Archivo | Casos | Prueba | Resultado |
| --- | --- | --- | --- | --- | --- |
| US-45 | La 410 publicada con el conjunto borrador queda en rojo y pide tres oportunidades de mejora | S | 1 | `test_semaforo_feature.py::test_la_410_con_el_borrador_queda_en_rojo` | aprobado |
| US-45 | La 412 de 450002 muestra verde, rojo y verde, con dos buenas prácticas | S | 3 | `test_semaforo_feature.py::test_la_412_muestra_verde_rojo_y_verde` | aprobado |
| US-45 | El 80,0 % justo en la meta queda en verde y pide una buena práctica | S | 1 | `test_semaforo_feature.py::test_el_80_justo_queda_en_verde` | aprobado |
| US-45 | Con el corte rojo definido, la banda ámbar va desde el corte hasta debajo de la meta y pide una oportunidad de mejora | S | 3 | `test_semaforo_feature.py::test_con_corte_rojo_definido_hay_ambar` | aprobado |
| US-45 | Con el corte rojo pendiente no hay ámbar | S | 1 | `test_semaforo_feature.py::test_con_corte_rojo_pendiente_no_hay_ambar` | aprobado |
| US-45 | Un PI sin calificaciones sale sin dato, nunca en rojo y sin tipo de registro | S | 1 | `test_semaforo_feature.py::test_un_pi_sin_calificaciones_sale_sin_dato` | aprobado |
| US-45 | Un parámetro sin definir deja los indicadores sin dato y no rompe la ruta | S | 2 | `test_semaforo_feature.py::test_un_parametro_sin_definir_no_rompe_la_ruta` | aprobado |
| US-45 | Las cifras y el semáforo coinciden con el R-17 de la misma carga | S | 1 | `test_semaforo_feature.py::test_las_cifras_y_el_semaforo_coinciden_con_el_r17` | aprobado |
| US-45 | Sin sesión la ruta responde 401 | S | 1 | `test_semaforo_feature.py::test_sin_sesion_la_ruta_responde_401` | aprobado |
| US-45 | El profesor solo ve el semáforo de sus secciones | S | 3 | `test_semaforo_feature.py::test_el_profesor_solo_ve_sus_secciones` | aprobado |
| US-45 | Una carga que no está publicada no tiene semáforo | S | 2 | `test_semaforo_feature.py::test_una_carga_no_publicada_no_tiene_semaforo` | aprobado |
| US-46 | P4 muestra la tabla de niveles con un estado por PI | S | 1 | Vitest `tests/spec005/semaforo.test.tsx` › «P4 muestra la tabla de niveles con un estado por PI» | aprobado, delegado a Vitest del Front |
| US-46 | La leyenda sale de la respuesta | S | 2 | Vitest `tests/spec005/semaforo.test.tsx` › «La leyenda sale de la respuesta ($corte)» | aprobado, delegado a Vitest del Front |
| US-46 | La franja provisional depende de la respuesta | S | 2 | Vitest `tests/spec005/semaforo.test.tsx` › «La franja provisional depende de la respuesta ($valor)» | aprobado, delegado a Vitest del Front |
| US-46 | Un PI sin dato no se pinta como 0 % ni en rojo | S | 1 | Vitest `tests/spec005/semaforo.test.tsx` › «Un PI sin dato no se pinta como 0 % ni en rojo» | aprobado, delegado a Vitest del Front |
| US-46 | P4 de una carga no publicada no pide el semáforo | S | 1 | Vitest `tests/spec005/semaforo.test.tsx` › «P4 de una carga no publicada no pide el semáforo» | aprobado, delegado a Vitest del Front |
| US-46 | Con un Back anterior, P4 se comporta como hoy | S | 1 | Vitest `tests/spec005/semaforo.test.tsx` › «Con un Back anterior, P4 se comporta como hoy» | aprobado, delegado a Vitest del Front |
| US-47 | El profesor registra y declara los tres PI de la 412, con dos buenas prácticas y una oportunidad de mejora | D | 3 | `test_declaracion_feature.py::test_registra_y_declara_la_412` | aprobado |
| US-47 | Una carga sin texto responde con la declaración y el borrador nulos | D | 1 | `test_declaracion_feature.py::test_una_carga_sin_texto` | aprobado |
| US-47 | Declarar con un registro incompleto no crea ninguna declaración | D | 4 | `test_declaracion_feature.py::test_declaracion_incompleta` | aprobado |
| US-47 | Declarar la versión 0 sin ningún borrador no crea ninguna declaración | D | 1 | `test_declaracion_feature.py::test_version_0_sin_borrador` | aprobado |
| US-47 | Un PI sin calificaciones no exige registro y no lo admite | D | 1 | `test_declaracion_feature.py::test_pi_sin_calificaciones` | aprobado |
| US-47 | Un PI que la carga no mide se rechaza en la ruta y en la base | D | 1 | `test_declaracion_feature.py::test_pi_ajeno` | aprobado |
| US-47 | El tipo de registro lo fija el semáforo, en la ruta y en la base | D | 1 | `test_declaracion_feature.py::test_tipo_del_semaforo` | aprobado |
| US-47 | Un texto demasiado largo o con caracteres de control se rechaza y nada cambia | D | 2 | `test_declaracion_feature.py::test_texto_invalido` | aprobado |
| US-47 | Una causa de 800 puntos de código se acepta | D | 1 | `test_declaracion_feature.py::test_800_puntos_de_codigo` | aprobado |
| US-47 | El profesor no fija responsable, plazo ni estado | D | 3 | `test_declaracion_feature.py::test_sin_responsable_plazo_ni_estado` | aprobado |
| US-47 | Un PI repetido en el cuerpo se rechaza | D | 1 | `test_declaracion_feature.py::test_pi_repetido` | aprobado |
| US-47 | Las tablas de V1_15 no tienen estado, responsable ni plazo, y abet_app no corrige una declaración | D | 1 | `test_declaracion_feature.py::test_tablas_sin_estado_y_permisos` | aprobado |
| US-47 | Solo el profesor asignado escribe, aunque el cuerpo no sea JSON | D | 4 | `test_declaracion_feature.py::test_solo_el_profesor_asignado` | aprobado |
| US-47 | Una carga que no está publicada responde 409 al guardar y al declarar | D | 4 | `test_declaracion_feature.py::test_carga_no_publicada` | aprobado |
| US-47 | Una regla sin definir detiene la declaración | D | 1 | `test_declaracion_feature.py::test_regla_sin_definir` | aprobado |
| US-47 | Corregir una declaración deja la anterior guardada y vigente hasta declarar la nueva | D | 1 | `test_declaracion_feature.py::test_corregir_una_declaracion` | aprobado |
| US-47 | El coordinador lee la declaración sin editarla ni ver el borrador | D | 1 | `test_declaracion_feature.py::test_coordinador_lee` | aprobado |
| US-47 | P4 del coordinador muestra lo declarado sin campos ni botón | D | 2 | Vitest `tests/spec005/declaracion.test.tsx` › «P4 del coordinador muestra lo declarado sin campos ni botón ($respuesta)» | aprobado, delegado a Vitest del Front |
| US-47 | P4 del profesor muestra un bloque por PI con los rótulos de su tipo | D | 1 | Vitest `tests/spec005/declaracion.test.tsx` › «P4 del profesor muestra un bloque por PI con los rótulos de su tipo» | aprobado, delegado a Vitest del Front |
| US-47 | Un PI sin calificaciones muestra su hallazgo sin campos | D | 1 | Vitest `tests/spec005/declaracion.test.tsx` › «Un PI sin calificaciones muestra su hallazgo sin campos» | aprobado, delegado a Vitest del Front |
| US-48 | Un borrador parcial se acepta | D | 1 | `test_declaracion_feature.py::test_borrador_parcial` | aprobado |
| US-48 | Dos pestañas no se pisan el borrador | D | 1 | `test_declaracion_feature.py::test_dos_pestanas` | aprobado |
| US-48 | El borrador vuelve al abrir P4 | D | 1 | Vitest `tests/spec005/declaracion.test.tsx` › «El borrador vuelve al abrir P4» | aprobado, delegado a Vitest del Front |
| US-48 | El guardado automático sale 2,5 segundos después de escribir y al salir de un campo | D | 1 | Vitest `tests/spec005/declaracion.test.tsx` › «El guardado automático sale 2,5 segundos después de escribir y al salir de un campo» | aprobado, delegado a Vitest del Front |
| US-48 | Si el guardado falla, el texto sigue en pantalla | D | 1 | Vitest `tests/spec005/declaracion.test.tsx` › «Si el guardado falla, el texto sigue en pantalla» | aprobado, delegado a Vitest del Front |
| US-48 | Un 401 durante el guardado no pierde el texto | D | 1 | Vitest `tests/spec005/app.test.tsx` › «Un 401 durante el guardado no pierde el texto» | aprobado, delegado a Vitest del Front |
| US-48 | El navegador no guarda el texto | D | 1 | Vitest `tests/spec005/declaracion.test.tsx` › «El navegador no guarda el texto» | aprobado, delegado a Vitest del Front |
| US-49 | Sin declaración el R-17 no se entrega | D | 2 | `test_declaracion_feature.py::test_sin_declaracion_no_hay_r17` | aprobado |
| US-49 | Con la declaración el R-17 se entrega | D | 1 | `test_declaracion_feature.py::test_con_declaracion_hay_r17` | aprobado |
| US-49 | El coordinador recibe el mismo 409 sin declaración y el archivo con ella | D | 2 | `test_declaracion_feature.py::test_coordinador_y_r17` | aprobado |
| US-49 | Una sección con todos sus PI en la meta también registra sus buenas prácticas | D | 1 | `test_declaracion_feature.py::test_todos_en_la_meta_declaran_bp` | aprobado |
| US-49 | El 409 de una carga rechazada manda sobre el de la declaración | D | 1 | `test_declaracion_feature.py::test_rechazada_manda` | aprobado |
| US-49 | El comando r17 de una carga sin declaración termina sin escribir ningún archivo | D | 1 | `test_declaracion_feature.py::test_comando_sin_declaracion` | aprobado |
| US-49 | P4 deshabilita el R-17 hasta que la carga tiene declaración | D | 1 | Vitest `tests/spec005/declaracion.test.tsx` › «P4 deshabilita el R-17 hasta que la carga tiene declaración» | aprobado, delegado a Vitest del Front |
| US-49 | P2, P5 y P6 no ofrecen el R-17 y llevan a P4 | D | 1 | Vitest `tests/spec005/app.test.tsx` › «P2, P5 y P6 no ofrecen el R-17 y llevan a P4» | aprobado, delegado a Vitest del Front |
| US-50 | B29 y B34 traen un párrafo por PI de la 410, en el orden del plan | R | 1 | `test_r17_desde_la_base_feature.py::test_b29_y_b34_traen_un_parrafo_por_pi` | aprobado |
| US-50 | Una buena práctica y dos oportunidades de mejora conviven en los recuadros | R | 1 | `test_r17_desde_la_base_feature.py::test_una_bp_y_dos_om_conviven` | aprobado |
| US-50 | Un PI sin calificaciones se nombra sin análisis | R | 1 | `test_r17_desde_la_base_feature.py::test_un_pi_sin_calificaciones_se_nombra_sin_analisis` | aprobado |
| US-50 | La plantilla oficial no cambia con los párrafos por PI | R | 1 | `test_r17_desde_la_base_feature.py::test_la_plantilla_oficial_no_cambia` | aprobado |
| US-50 | Tres PI con causas y acciones de 800 caracteres caben y no tapan la tabla de frecuencias | R | 1 | `test_r17_desde_la_base_feature.py::test_tres_pi_de_800_caracteres_caben` | aprobado |
| US-50 | Una declaración cuyo recuadro no cabe en el R-17 se rechaza | R | 1 | `test_r17_desde_la_base_feature.py::test_una_declaracion_que_no_cabe_se_rechaza` | aprobado |
| US-50 | Un texto que parece fórmula queda como cadena | R | 1 | `test_r17_desde_la_base_feature.py::test_un_texto_que_parece_formula_queda_como_cadena` | aprobado |
| US-50 | El R-17 trae el texto de la última declaración | R | 1 | `test_r17_desde_la_base_feature.py::test_el_r17_trae_la_ultima_declaracion` | aprobado |
| US-51 | G17, G18 y G19 traen la descripción de cada PI | R | 1 | `test_r17_desde_la_base_feature.py::test_g17_g18_y_g19_traen_la_descripcion_de_cada_pi` | aprobado |
| US-51 | Sin descripción en la base, G17:I19 queda vacía | R | 1 | `test_r17_desde_la_base_feature.py::test_sin_descripcion_en_la_base_g17_i19_queda_vacia` | aprobado |
| US-51 | La base rechaza una descripción en blanco, con blancos a los lados o demasiado larga | R | 4 | `test_r17_desde_la_base_feature.py::test_la_base_rechaza_una_descripcion_mal_formada` | aprobado |
| US-51 | El guion de datos se corre dos veces y deja las mismas tres descripciones | R | 1 | `test_r17_desde_la_base_feature.py::test_el_guion_de_datos_se_corre_dos_veces` | aprobado |
| US-52 | Atrás recorre las pantallas visitadas y adelante las recupera | N | 1 | Vitest `tests/spec005/navegacion.test.tsx` › «Atrás recorre las pantallas visitadas y adelante las recupera» | aprobado, delegado a Vitest del Front |
| US-52 | Después de una subida, atrás lleva a P2 sin repetir el POST | N | 1 | Vitest `tests/spec005/navegacion.test.tsx` › «Después de una subida, atrás lleva a P2 sin repetir el POST» | aprobado, delegado a Vitest del Front |
| US-52 | La subida en modo reemplazo guarda la carga que reemplaza en la dirección | N | 1 | Vitest `tests/spec005/navegacion.test.tsx` › «La subida en modo reemplazo guarda la carga que reemplaza en la dirección» | aprobado, delegado a Vitest del Front |
| US-52 | Un fragmento a una carga ajena muestra el 403 de P4 | N | 1 | Vitest `tests/spec005/navegacion.test.tsx` › «Un fragmento a una carga ajena muestra el 403 de P4» | aprobado, delegado a Vitest del Front |
| US-52 | Después de salir, atrás muestra el ingreso y ninguna sección | N | 1 | Vitest `tests/spec005/navegacion.test.tsx` › «Después de salir, atrás muestra el ingreso y ninguna sección» | aprobado, delegado a Vitest del Front |
| US-53 | Un código o un correo de estudiante se rechaza y no se guarda ni como borrador | D | 2 | `test_declaracion_feature.py::test_codigo_o_correo` | aprobado |
| US-53 | Un número de 9 dígitos o una fecha no son un código de estudiante | D | 2 | `test_declaracion_feature.py::test_falsos_positivos` | aprobado |
| US-53 | La base rechaza un código en el borrador aunque la API se salte la validación | D | 1 | `test_declaracion_feature.py::test_base_rechaza_codigo_en_el_borrador` | aprobado |
| US-53 | La base rechaza un correo en la declaración | D | 1 | `test_declaracion_feature.py::test_base_rechaza_correo_en_la_declaracion` | aprobado |
| US-53 | Un 422 durante el guardado automático deja el texto y no reintenta en bucle | D | 1 | Vitest `tests/spec005/declaracion.test.tsx` › «Un 422 durante el guardado automático deja el texto y no reintenta en bucle» | aprobado, delegado a Vitest del Front |
| US-53 | Las rutas 13 a 16 no se guardan en caché y no traen datos de estudiantes | D | 1 | `test_declaracion_feature.py::test_sin_cache` | aprobado |
| US-53 | Q16 y Q17 dan 0 filas con declaraciones sanas | D | 1 | `test_declaracion_feature.py::test_q16_y_q17_en_cero` | aprobado |
| US-53 | Q17 ve un PI con calificados sin su registro en la declaración vigente | D | 1 | `test_declaracion_feature.py::test_q17_ve_el_pi_que_falta` | aprobado |
| US-53 | Neon corre los mismos controles | D | 1 | `test_declaracion_feature.py::test_neon_corre_los_mismos_controles` | aprobado |
| US-54 | La carga nueva hereda el análisis declarado con el tipo de sus cifras | D | 1 | `test_declaracion_feature.py::test_hereda_lo_declarado` | aprobado |
| US-54 | Un PI que queda sin calificaciones en la carga nueva no se hereda | D | 1 | `test_declaracion_feature.py::test_sin_calificaciones_no_se_hereda` | aprobado |
| US-54 | Sin texto declarado se hereda lo que haya, o nada | D | 2 | `test_declaracion_feature.py::test_hereda_lo_que_haya` | aprobado |
| US-54 | Subir el mismo archivo no cambia nada | D | 1 | `test_declaracion_feature.py::test_mismo_archivo` | aprobado |
| US-54 | Un reemplazo hecho por coordinación hereda igual y coordinación no ve el texto heredado | D | 1 | `test_declaracion_feature.py::test_reemplazo_de_coordinacion` | aprobado |
| US-54 | Un PUT a la carga reemplazada responde 409 con la carga nueva | D | 1 | `test_declaracion_feature.py::test_put_a_la_reemplazada` | aprobado |
| US-54 | P4 de la carga reemplazada conserva el texto y lo lleva a la nueva | D | 1 | Vitest `tests/spec005/declaracion.test.tsx` › «P4 de la carga reemplazada conserva el texto y lo lleva a la nueva» | aprobado, delegado a Vitest del Front |

## Requerimientos funcionales

| FR | Estado | Evidencia |
| --- | --- | --- |
| FR-001 | Cumplido | US-45, escenarios de la ruta 13 (401, 403 único, 409 de una carga no publicada, `no-store` y una sola instantánea) en `tests/test_api_indicadores.py` y `test_semaforo_feature.py` |
| FR-002 | Cumplido | las pruebas de tabla de `semaforo()`, `tipo_de_registro()` y `redactar_hallazgo()` en `tests/test_resultados.py` (T030) |
| FR-003 | Cumplido | US-46, seis escenarios en `tests/spec005/semaforo.test.tsx` del Front |
| FR-004 | Cumplido | V1_15 en lugar de V1_12 por FR-004 de la spec 008; `tests/test_mejora_base.py` (123 casos en el clúster desechable), N10 de `probar_rol_app.sql` y los permisos de `crear_rol_app.sql`; la rama `develop` de Neon sigue en V1_14 (T024) |
| FR-005 | Cumplido | US-47, escenarios de las rutas 14 a 16 (orden 401, 403, 422 y 409, JSON obligatorio, claves fuera del contrato, 800 puntos de código y recuadro que no cabe) en `test_declaracion_feature.py` y `tests/test_api_mejora.py`, y las tres pruebas de mutación del 2026-11-24 |
| FR-006 | Cumplido | US-47 y US-48, escenarios delegados a Vitest en `tests/spec005/declaracion.test.tsx` |
| FR-007 | Cumplido | US-48, «Un 401 durante el guardado no pierde el texto» en `tests/spec005/app.test.tsx` |
| FR-008 | Cumplido | US-49, `DeclaracionPendiente` en `r17.generar()`, la ruta 7 con su 409 y el comando, en `test_declaracion_feature.py` y `tests/test_r17.py` |
| FR-009 | Cumplido | US-49, «P2, P5 y P6 no ofrecen el R-17 y llevan a P4» en `tests/spec005/app.test.tsx` |
| FR-010 | Cumplido | US-50, ocho escenarios de `r17_desde_la_base.feature` y `tests/test_r17_recuadro.py` (tres PI en el tope, 45 celdas combinadas iguales a la plantilla y K31:Q31 sin cambios) |
| FR-011 | Cumplido | US-51, cuatro escenarios de `r17_desde_la_base.feature`, `tests/test_descripcion_instrumento.py` y T020 a T022, hechas el 2026-11-18 |
| FR-012 | Cumplido | US-52, cinco escenarios en `tests/spec005/navegacion.test.tsx` |
| FR-013 | Cumplido | US-53, `test_declaracion_feature.py` (rutas), `tests/test_mejora_base.py` (CHECK de las tablas) y Q16 en el clúster desechable |
| FR-014 | Cumplido | US-54, seis escenarios del Back en `test_declaracion_feature.py` y uno de Vitest |
| FR-015 | Cumplido | T011 en el Front (sección 13 de `docs/03-api/contrato.md` y ADR-009), T010 en el Back (`mejora`, `r17` y la fila de `specs/README.md`) |
| FR-016 | Cumplido en local, pendiente en la vista previa | una prueba por escenario, 85 de 85; el humo local se corre el 2026-11-24 y T046 contra la vista previa de `develop` espera el despliegue (T062) |
| FR-017 | Cumplido | T012 y T037: la expresión de migraciones admite V1_15, `REGLAS_DE_COPIA` suma la columna vacía, `declarar()` y `conjunto_semaforo()` en `tests/cargas_de_prueba.py` |
| FR-018 | Cumplido | T039: Q16 y Q17 iguales en `pruebas.sql` y `controles_neon.sql` con su prueba de paridad |
| FR-019 | Cumplido | el orden de J-41 se siguió: ruta 13 y P4 por indicador, rutas 14 a 16 con US-49 y US-50, y al final US-54 |

## Criterios de éxito

| SC | Estado | Evidencia |
| --- | --- | --- |
| SC-001 | Cumplido | US-45, «Las cifras y el semáforo coinciden con el R-17 de la misma carga» y la prueba de tabla de `tipo_de_registro()` |
| SC-002 | Cumplido | US-49 y US-50, con `declarar()` en las llamadas de prueba que generan un R-17 (T037) y un párrafo por PI en B29 y B34 |
| SC-003 | Cumplido | «El borrador vuelve al abrir P4» en Vitest y el borrador de una versión por carga, guardado en la base, en `test_declaracion_feature.py` y `tests/test_api_mejora.py` |
| SC-004 | Cumplido en Vitest | US-52, cinco escenarios en `navegacion.test.tsx` |
| SC-005 | Cumplido en el clúster desechable, pendiente en Neon | Q16 y Q17 en 0 filas en `correr_pruebas.sh`; en las dos ramas de Neon, T024 y T063 |
| SC-006 | Cumplido | US-51, G17:I19 con la descripción del plan de 450002 y vacía sin ella |
| SC-007 | Cumplido en local, pendiente en la vista previa | el humo local del 2026-11-24 da 5 passed: sube la 410 con el rechazo, deja el R-17 deshabilitado y con 409, reemplaza con el export correcto, escribe y declara el análisis por indicador y descarga el R-17; T046 contra la vista previa de `develop` espera el despliegue (T062) |
| SC-008 | Cumplido | las CHECK de coherencia entre tipo y semáforo de `tests/test_mejora_base.py` y la ausencia de columnas de estado, responsable y plazo |

## Decisiones abiertas

D-35 (CORTE_ROJO), D-36, D-37, D-34, D-39 a D-43 y la nota de D-08 siguen con la Coordinación de Ambiental y la Oficina de Calidad (T005 y T009), y rigen sus valores provisionales: CORTE_ROJO PENDIENTE y sin ámbar, una BP por PI en el semáforo verde, una declaración nueva que reemplaza a la anterior, un solo registro por PI con el tipo del semáforo y un párrafo por PI en los recuadros A y B. J-29 a J-41 las aprueba Jefferson en el chat el 2026-11-18 y el 2026-11-21, y J-37 y J-41 siguen en los valores que propone la spec.

## Pendiente

1. T005 y T009, las decisiones de la carrera, y T023, la consulta de solo lectura de las cargas publicadas sin declaración en Neon, desde el Windows de Jefferson.
2. T024, migrar `develop` de Neon con V1_15 y sus permisos sin APP_DB_CLAVE, desde el Windows de Jefferson, y T063 con la rama principal.
3. El permiso de Jefferson para empujar las ramas del Back y del Front y abrir los PR. Hasta entonces no hay push.
4. T060 a T062, con el Front desplegado antes que el Back y T046 contra la vista previa de `develop`, con la rama `develop` de Neon restablecida con `humo_preview.sh`.
5. T064, la versión hacia `main` y Production.
