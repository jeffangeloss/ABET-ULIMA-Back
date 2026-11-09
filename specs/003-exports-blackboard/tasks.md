# Tasks: El export real de Blackboard en .xlsx, .csv y .xls

**Input**: spec.md, plan.md · **Estado al 2026-11-09**: Jefferson aprueba la spec en el chat; las fases 0 a 7 quedan hechas salvo T005 (D-30) y T077 (V1_10 en la rama principal antes de la versión)

Cada tarea lleva al comienzo el repositorio o el lugar donde ocurre, como en la spec 001. `[Back]` es ABET-ULIMA-Back, `[Front]` es ABET-ULIMA-Front, `[Neon]` es la base en la nube, siempre desde el Windows de Jefferson por Tailscale, y `[Jefferson]` marca lo que solo puede hacer él. Ninguna credencial pasa por un agente. Al final, cada tarea lleva las historias que habilita o audita.

## Phase 0: Descubrimiento

- [x] T001 [Back] Analizar el comportamiento actual con los exports de texto y los encabezados reales, con archivos inventados (nota de análisis del 2026-11-09 de la sesión del plan) [US-26..US-36]
- [x] T002 [Back] Escribir 15 candidatas con Gherkin en español, auditarlas con las lentes de necesidad, tamaño y verificabilidad y con el crítico de arquitectura, y dejar el resultado en `specs/003-exports-blackboard/revision-historias.md` [US-26..US-36]
- [x] T003 [Back] Redactar `spec.md`, `plan.md` y `tasks.md` de `specs/003-exports-blackboard/` [US-26..US-36]
- [x] T004 [Jefferson] Aprobar la spec y decidir J-18, J-19, J-20, D-02, D-03 y D-31 [US-26..US-36] · Aprobada en el chat el 2026-11-09 con las opciones recomendadas
- [ ] T005 [Jefferson] Llevar D-30, la escala de las columnas ABET de 100 puntos, a Stefanny Montaño o a la Oficina de Calidad [US-26] [US-29]

## Phase 1: Contrato

- [x] T010 [Back] Bloques fechados de la spec 003 en `specs/features/carga-export/carga-export.spec.md` (BR-CARGA-03, 05 a 08, 11 y 14 a 17) y en `specs/features/r17/r17.spec.md` (BR-R17-10) [US-26..US-36]
- [x] T011 [Front] Actualizar `docs/03-api/contrato.md` (sección 6, orden del trabajo, tabla de 422 y `hoja` nula), `docs/specs/api-contracts.md` y `docs/01-arquitectura/frontend.md` (P3 y P4) [US-27..US-34] · Hecha el 2026-11-09 en el Front (9467f29)
- [x] T012 [Back] Dejar definitivo `specs/003-exports-blackboard/aceptacion/exports_blackboard.feature`, que pasa el parser de Gherkin de pytest-bdd [US-26..US-36] · Hecha el 2026-11-09; 39 escenarios y 104 casos
- [x] T013 [Back] Escribir la lista común de encabezados de `tests/encabezados_de_pi.py`, que usan la prueba del lector y la prueba de paridad con la base [US-26] · Hecha el 2026-11-09; 35 casos
- [x] T014 [Back] Generar con `scripts/generar_exports_inventados.py` los cuatro exports nuevos, con los títulos reales de las actividades y números de columna de Blackboard inventados que empiezan con 9, y actualizar `tests/datos_inventados/README.md` y `tests/test_generador_exports.py` [US-26..US-30] · Hecha el 2026-11-09; 105 pruebas del generador

## Phase 2: Base

- [x] T020 [Back] Escribir `db/migration/V1_10__encabezado_pi_con_prefijo.sql`, que reemplaza `ck_carga_columna_encabezado` por la regla de J-19 y suma SIN_CALIFICACIONES a `ck_rechazo_fila_motivo` [US-26] [US-36] · Hecha el 2026-11-09
- [x] T021 [Back] Sumar a `db/pruebas/pruebas.sql` los casos que deben pasar y los que no de V1_10, y correr `db/pruebas/correr_pruebas.sh` en el clúster desechable [US-26] [US-36] · Hecha el 2026-11-09; R63 a R65, A09 y A10, y «RESULTADO: todo pasó»

## Phase 3: Backend

- [x] T030 [Back] `abet_carga/lector.py`, con `tests/test_lector.py` primero. Tipo por contenido, ruta de texto, límites, tope de 5 000 filas, patrón de encabezado de J-19 y detalle de ArchivoIlegible [US-26] [US-27] [US-28] [US-31] [US-32] · Hecha el 2026-11-09
- [x] T031 [Back] `abet_carga/validacion.py` y `abet_carga/modelos.py`, con `tests/test_validacion.py` primero. Nombre `.csv` y `.xls`, hoja nula, nivel con decimales nulos y tope de cifras, SIN_CALIFICACIONES y textos nuevos [US-29] [US-30] [US-36] · Hecha el 2026-11-09
- [x] T032 [Back] `abet_carga/carga.py`, `constancia.py`, `r17.py` y `app/rutas/cargas.py`. Hoja nula, SIN_CALIFICACIONES, «Sin hoja (export de texto)» y el detalle en el registro [US-31] [US-34] [US-36] · Hecha el 2026-11-09
- [x] T033 [Back] Actualizar los textos de la spec 001 que cambian, en `carga.feature`, sus pasos y las pruebas unitarias [US-30] [US-31] · Hecha el 2026-11-09

## Phase 4: Frontend

- [x] T040 [Front] `src/pantallas/SubirExport.tsx` con `accept`, etiqueta y aviso nuevos, y su prueba [US-33] · Hecha el 2026-11-09 (9467f29)
- [x] T041 [Front] `src/pantallas/ResultadoCarga.tsx` y `src/servicios/tipos.ts` con la hoja nula, y su prueba [US-34] · Hecha el 2026-11-09 (9467f29)
- [x] T042 [Front] Prueba de humo con Playwright (`e2e/`) que sube el `.csv` inventado de la 410 por P3, ve P4 y descarga el R-17, local y contra la vista previa de `develop` [US-27] [US-33] · Escrita el 2026-11-09 (9467f29); corre en T076

## Phase 5: Pruebas

- [x] T050 [Back] Pasos de `exports_blackboard.feature` en `tests/aceptacion/pasos/test_exports_blackboard_feature.py` [US-26..US-36] · Hecha el 2026-11-09; 104 casos aprobados
- [x] T051 [Back] Regla 2 de `scripts/preflight.sh` por contenido y sus casos en `scripts/probar_preflight.sh` [US-35] · Hecha el 2026-11-09; 46 casos de `probar_preflight.sh`, con los nombres que no son ASCII de la revisión de seguridad
- [x] T052 [Back] Revisión de seguridad del lector de texto con un subagente con el modelo de la sesión y esfuerzo alto, y corrección de lo que confirme [US-31] [US-32] · Hecha el 2026-11-09; 11 hallazgos, cuatro corregidos en el lector y uno en la revisión previa, y los demás anotados en `docs/devops.md` o aceptados
- [ ] T053 [Back] [Front] Suite completa del Back y del Front, `correr_pruebas.sh` y la revisión previa [US-26..US-36]

## Phase 6: Auditoría

- [ ] T060 [Back] `specs/003-exports-blackboard/audit.md` y la Verification fechada de `carga-export.spec.md` y `r17.spec.md` [US-26..US-36]
- [ ] T061 [Back] [Front] `MEMORIA.md` y `CHANGELOG.md` de cada repositorio, también en cada commit de las fases anteriores [US-26..US-36]

## Phase 7: Despliegue

- [x] T070 [Jefferson] Dar permiso para empujar `feat/003-exports-blackboard` en los dos repositorios y abrir sus PR [US-26..US-36] · Hecha el 2026-11-09 («Sí, empuja y abre los PR»)
- [x] T071 [Back] [Front] Abrir los PR a `develop` y dejar la integración continua en verde [US-26..US-36] · PR jeffangeloss/ABET-ULIMA-Back#17 y jeffangeloss/ABET-ULIMA-Front#10 con la CI requerida en verde
- [x] T072 [Jefferson] Fusionar los PR en `develop` [US-26..US-36] · Hecha el 2026-11-09 por Claude Code con el permiso de Jefferson: PR #17 en e56fb8a y PR #10 del Front en c2f3523, con merge commit
- [x] T073 [Neon] [Jefferson] Restablecer la rama `develop` de Neon desde la principal [US-26..US-36] · Hecha el 2026-11-09 de otro modo: la rama `develop` se había borrado el 2026-11-05, y Claude Code crea con la CLI de Neon una rama `develop` nueva desde la principal (br-dark-block-b7avl02u), con el permiso de Jefferson; Jefferson cambia el host de la DATABASE_URL de Preview (develop) en Vercel
- [x] T074 [Neon] Contar antes de migrar, con una consulta de solo lectura, las filas de `carga_columna` que no cumplirían la restricción nueva (debe dar 0), aplicar V1_10 con `flyway migrate` y volver a marcar la rama con preview (`db/plataforma/neon/marcar_entorno.sql`) [US-26] [US-36] · Hecha el 2026-11-09 desde el Windows con `ABET_SIS_MED/herramientas_neon/migrar_neon.sh`: 0 filas por revisar, Flyway en 1.10, marca preview y Q01 a Q14 en 0; la rama principal sigue en 1.09
- [x] T075 [Jefferson] Asignar las contraseñas de docente410 y docente411 en la rama `develop` con `ABET_SIS_MED/herramientas_neon/asignar_claves.py` [US-27] [US-28] · Hecha el 2026-11-09 por Jefferson con `humo_preview.sh`; la rama `develop` queda con 2 credenciales
- [x] T076 [Front] Probar en la vista previa de `develop` el `.csv` inventado en la 410 y el `.xls` inventado en la 411, con R-17 de 63,6 / 63,6 / 72,7 %, Q01 a Q14 en 0 y la rama principal de Neon sin cambios [US-27] [US-28] · Hecha el 2026-11-09: Playwright da 2 passed contra la vista previa; en Neon `develop`, la 410 (.csv) y la 411 (.xls) quedan PUBLICADA con 11 / 11 / 0, hoja nula, 33 mediciones, 5 avisos y R-17 de 63,6 / 63,6 / 72,7 %, Q01 a Q14 en 0, y la principal sigue en 1.09 sin cargas
- [ ] T077 [Neon] [Jefferson] Aplicar V1_10 en la rama principal de Neon antes de llevar la versión a `main` (T076 de la spec 001) [US-26] [US-36]
