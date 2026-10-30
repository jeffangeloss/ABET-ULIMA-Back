# Implementation Plan: Proyectos de Capstone en la base, tabla maestra en el formato nuevo y R-17 con la hoja «Cursos Capstone»

**Branch**: `docs/002-capstone` (PR a `develop`) | **Date**: 2026-10-29 | **Spec**: [spec.md](./spec.md)

## Summary

Hoy la spec 001 lleva el export de Blackboard de una sección a la base y genera el R-17 con la hoja «Cursos de Carrera», pero los datos de proyecto de un curso Capstone siguen en una plantilla de Excel aparte, la tabla maestra de Capstone se arma a mano y el R-17 no tiene la hoja «Cursos Capstone». La épica EP-02 suma a la base la marca del tipo de curso, una segunda subida por sección para la plantilla de proyectos, unida a los estudiantes del export publicado en una sola transacción, la vista de la tabla maestra en el formato nuevo y la elección de hoja del R-17. El caso de prueba es la sección 420 de 450024 en 2026-2 con los códigos inventados 99000101 a 99000111, los indicadores de desempeño (performance indicators, PI) 1.1, 1.2 y 1.3 y una plantilla inventada de 11 filas en 4 grupos. Su plantilla correcta da 11 / 11 / 0 y 33 filas en la tabla maestra de Capstone, y la copia con un código ajeno en la fila 4 da 11 / 10 / 1 con el aviso de un estudiante sin proyecto. El corte 1 entrega US-01 a US-24 y el corte 2 la declaración de US-25.

## Technical Context

- **Dependencia.** La spec 002 se apoya en el corte 1 de la spec 001 (US-01 a US-17), que se implementa en otra rama. Las fases 0 y 1 corren en paralelo y no tocan su código. Las fases 2 a 7 empiezan cuando el corte 1 de la spec 001 está fusionado en `develop`, porque necesitan V1_09 aplicada, el rol `abet_app`, `abet_carga` con su lector, su transacción y su R-17, la sesión, `app/permisos.py`, `GET /api/secciones` y P2 a P4 del Front. Nada de esta spec cambia el comportamiento del corte 1, salvo el 409 de J-16 sobre el reemplazo del export, que es del corte 2 de la spec 001.
- **Backend.** Python 3.12 con FastAPI (J-01 de la spec 001). `abet_carga` suma un lector, una validación y una carga de la plantilla (los nombres de archivo son ejemplo hasta cerrar J-11 y J-13) con openpyxl 3.1.5 en solo lectura, defusedxml y psycopg 3 con transacciones explícitas y `prepare_threshold=None`. `abet_carga/r17.py` elige la hoja por `tipo_curso` y `app/rutas/proyectos.py` agrega `POST /api/secciones/{seccion_id}/proyectos`.
- **Frontend.** React con Vite, TypeScript y Tailwind, como en la spec 001. P3 suma la zona «Plantilla de proyectos», P4 el resultado de la subida y P2 el estado de proyectos, todo detrás de `src/servicios/api.ts`.
- **Base.** PostgreSQL 16 en Neon (aws-sa-east-1). V1_10 agrega `plan_estudios.tipo_curso` y marca CAPSTONE 450025, 450024 y 450026, amplía `archivo_origen.tipo_fuente` y crea `carga_proyecto`, `proyecto_estudiante` y `rechazo_proyecto`. `R__vista_tabla_maestra_capstone.sql` crea la vista nueva y `R__vista_r17_por_pi.sql` suma `tipo_curso` al final. Los scripts de plataforma suman permisos, la guardia del RUC y Q16 a Q20.
- **Pruebas.** pytest-bdd 9 lee los cuatro `.feature` de `specs/002-capstone/aceptacion/`, pytest cubre los criterios escritos contra un PostgreSQL 16 desechable armado con `db/pruebas/cluster_desechable.sh`, nunca contra el clúster de la Mac, y el humo de Playwright del Front recorre el flujo de Capstone.
- **Restricciones.** Solo datos inventados. Los dos Excel que adjunta Jefferson traen datos reales y no entran al repositorio ni a una prueba; la plantilla inventada se genera con un script. El RUC no se guarda con prefijo 10 ni con 8 dígitos. Ninguna migración aplicada se edita.

## Constitution Check

| Principio | Cumplimiento |
| --- | --- |
| I · La base es la única fuente de verdad | La tabla maestra de Capstone y el R-17 salen de `v_tabla_maestra_capstone`, `v_r17_por_pi` y `proyecto_estudiante`, y todo cambio de la base entra en V1_10 o en una vista `R__` (fases 2 y 3) |
| II · Privacidad por diseño y solo datos inventados | La columna ALUMNO se descarta, Q04 suma «alumno» y las tablas de proyecto, el RUC de persona natural no se guarda, la guardia cubre código y RUC en la API y en Neon, y ningún rechazo guarda el valor leído (fases 2 y 3) |
| III · Toda carga es atómica y trazable | La plantilla se escribe en una transacción con su huella SHA-256, `subida_por` y sus rechazos por fila, columna y motivo, y se ata a la carga publicada del export por clave foránea compuesta (fase 3) |
| IV · Las reglas son datos versionados y lo provisional se ve | El tipo de curso vive en `plan_estudios`, la marca de 450025, 450024 y 450026 la fija D-14 (2026-10-29) y la pone V1_10, el R-17 conserva la franja PROVISIONAL y suma la de «SIN DATOS DE PROYECTO» (fases 2 y 3) |
| V · Contrato, historias auditadas y prueba antes de desplegar | 46 candidatas auditadas en la fase 0, contrato y specs vivas en la fase 1, `.feature` con 85 escenarios, pruebas en la fase 5 y `audit.md` en la fase 6, con `MEMORIA.md` en cada commit |
| VI · Capas y privilegio mínimo | `abet_carga` sin FastAPI, `app/permisos.py` como dueño de la visibilidad y `abet_app` sin DELETE ni TRUNCATE y con UPDATE solo de las columnas de cierre de `carga_proyecto` |

## Project Structure

```text
ABET-ULIMA-Back/
  db/
    migration/V1_10__crear_proyectos_capstone.sql   # (nuevo, propuesta de nombre) tipo_curso con la marca de 450025, 450024 y 450026, tipo_fuente y tres tablas
    migration/R__vista_tabla_maestra_capstone.sql   # (nuevo) vista del formato nuevo sobre las tablas base
    migration/R__vista_r17_por_pi.sql               # + tipo_curso al final
    plataforma/neon/crear_rol_app.sql               # + permisos de las tablas de proyecto y de la vista
    plataforma/neon/guardia_datos_inventados.sql    # + ck_proyecto_ruc_inventado
    plataforma/neon/controles_neon.sql              # + Q04 ampliada y Q16 a Q20
    datos/periodo_2026_2_inventado.sql              # + secciones 420 y 421 de 450024, plan 1.1 a 1.3 y docentes
    pruebas/pruebas.sql                             # + casos de V1_10, Q04 ampliada, Q16 a Q20, S01 y paridad
    pruebas/datos_sinteticos.sql                    # + sección 420 coherente
    pruebas/probar_rol_app.sql, probar_guardia.sql  # + casos nuevos
    pruebas/datos_sinteticos_capstone.sql           # (nuevo, propuesta) subida y proyectos de la 420, después de V1_10
    pruebas/correr_pruebas.sh                       # + foto de v_tabla_maestra_pi antes de V1_10, archivo Capstone y línea RESULTADO
    plataforma/neon/crear_roles_lectura.sql         # + SELECT de abet_lectura sobre v_tabla_maestra_capstone (subtree)
    callbacks/afterMigrate__permisos_lectura.sql    # + la vista nueva (subtree)
  abet_carga/
    lector_proyectos.py                             # (nuevo, ejemplo hasta J-11) lectura por encabezado y descarte de ALUMNO
    validacion_proyectos.py                         # (nuevo, ejemplo) guardia, estructura, filas y grupo
    carga_proyectos.py                              # (nuevo, ejemplo) cargar_proyectos(bytes, seccion_id, usuario_id)
    r17.py, constancia.py                           # + hoja «Cursos Capstone», franja y bloque proyectos
  app/rutas/proyectos.py                            # (nuevo) POST /api/secciones/{seccion_id}/proyectos
  app/rutas/secciones.py, app/rutas/cargas.py       # + campos de proyectos y bloque proyectos
  plantillas/R017_ambiental_capstone.xlsx           # (nuevo) copia vaciada de la hoja «Cursos Capstone»
  scripts/generar_plantillas_inventadas.py          # (nuevo, propuesta) plantilla inventada y sus copias
  tests/datos_inventados/                           # + exports de la 420 y la 421, plantilla y copias
  specs/002-capstone/aceptacion/                    # base_capstone, carga_proyectos, evidencia_capstone y secciones_capstone
  specs/features/proyectos-capstone/                # (nuevo) spec viva con BR-PROYECTOS-NN

ABET-ULIMA-Front/
  docs/03-api/contrato.md                           # + ruta de proyectos, bloque proyectos y campos de secciones
  src/pantallas/SubirExport.tsx                     # + zona «Plantilla de proyectos» en secciones Capstone
  src/pantallas/ResultadoCarga.tsx                  # + resultado de la plantilla y descarga del R-17 Capstone
  src/pantallas/MisSecciones.tsx                    # + estado de proyectos
  e2e/humo-capstone.spec.ts                         # (nuevo, propuesta) humo con Playwright
```

## Phases

Los días son de trabajo sin interrupciones, con Claude a cargo del código y Jefferson de la revisión. Las fases 3 y 4 se solapan, porque el Front trabaja contra el contrato de la fase 1.

0. **Descubrimiento** (hecho el 2026-10-29). En el Back, lectura de la spec 001, de la base y del contrato, 46 candidatas desde tres ángulos, tres lentes y una crítica de arquitectura que dejan 25 historias. En el Front y en Neon, nada. Artefactos `revision-historias.md`, `spec.md`, este plan, `tasks.md` y los cuatro `.feature`, en revisión por PR a `develop`. No cierra historias y prepara EP-02.
1. **Contrato** (1 día). En el Back, la spec viva `proyectos-capstone` con sus reglas `BR-PROYECTOS-NN`, los bloques nuevos de `r17` y `periodo`, la versión definitiva de los `.feature` y el generador de la plantilla inventada. En el Front, el contrato de la ruta de proyectos, del bloque `proyectos` y de los campos nuevos de `GET /api/secciones`. En Neon, nada. Jefferson lleva D-15 a D-29 a la carrera, porque D-14 ya está decidida. No cierra historias y habilita US-03 a US-23.
2. **Base** (1 a 1,5 días, después del corte 1 de la spec 001). En el Back, V1_10, las dos vistas `R__`, los permisos, la guardia, Q04 ampliada, Q16 a Q20, S01, la semilla y los datos sintéticos, todo probado con `correr_pruebas.sh` en un clúster desechable. Después se aplican en Neon, primero en la rama `develop` y luego en la principal. Cierra US-01, US-02, US-22 y US-24.
3. **Backend** (2,5 a 3,5 días). En el Back, el lector, la validación y la carga de la plantilla, la ruta de proyectos, el bloque `proyectos`, los campos de secciones, la plantilla vaciada de «Cursos Capstone» con su mapa de celdas y la elección de hoja del R-17. Artefacto, la API local que publica la plantilla inventada con 11 / 11 / 0 y descarga el R-17 con la hoja Capstone. Cierra en la API US-03 a US-21 y US-23.
4. **Frontend** (1 día). En el Front, la zona de la plantilla en P3, su resultado en P4 y el estado de proyectos en P2. Cierra en pantalla US-03, US-12, US-13, US-14, US-15, US-18, US-19 y US-23.
5. **Pruebas** (1 día). En el Back, los pasos de `carga_proyectos.feature` y `evidencia_capstone.feature`, pytest para `base_capstone.feature` y `secciones_capstone.feature` y los casos negativos con archivos generados en `tmp_path`. En el Front, Vitest y el humo con Playwright. Cierra la aceptación del corte 1.
6. **Auditoría** (0,5 días). `audit.md` cruza historia, escenario, prueba y resultado, y las specs vivas reciben su `Verification` fechada.
7. **Despliegue** (0,5 días). V1_10, las vistas y los scripts de plataforma en Neon, `crear_rol_app.sql` repetido después del `migrate`, `controles_neon.sql` en cero en las dos ramas y el humo contra la vista previa de `develop` antes de pasar a `main` (J-09 de la spec 001).

## Cortes

| Corte | Historias | Fases | Duración | Resultado |
| --- | --- | --- | --- | --- |
| Primer corte demostrable | US-01, US-03, US-07, US-17, US-19 y US-21 | 2 y 3 reducidas, sin pantallas | 2 días | El comando de `abet_carga` publica la plantilla inventada de la 420 en la Mac y produce la tabla maestra de 33 filas y el R-17 con la hoja «Cursos Capstone» |
| Corte 1 | US-01 a US-24 | 1 a 7 | unos 6 a 7 días hábiles después del corte 1 de la spec 001 | Plantilla en la base, tabla maestra en el formato nuevo y R-17 Capstone en Vercel con Neon |
| Corte 2 | US-25 | 1, 3, 4, 5 y 6, breves (tareas T080 a T089) | 1 día | Declaración de que los textos libres no nombran personas, antes de pedir datos reales |

## Complexity Tracking

| Desviación | Por qué hace falta | Alternativa más simple descartada |
| --- | --- | --- |
| Segunda subida por sección (`carga_proyecto`) en lugar de colgar la plantilla de `abet.carga` | Los contadores de `carga` están atados al export por `ck_carga_filas`, `ck_carga_conciliada` y `fk_carga_archivo`, y una carga publicada no admite UPDATE de sus columnas | Un `carga.archivo_proyectos_id` con UPDATE sobre una carga PUBLICADA (C-47), que rompe esas restricciones y el privilegio mínimo |
| Datos de proyecto repetidos en cada integrante (J-11) | La plantilla y la tabla maestra del formato nuevo son por estudiante, y la clave hacia `carga_fila` impide proyectos de estudiantes ajenos | Una tabla por grupo con integrantes, que suma dos tablas y una identidad sin cambiar ningún escenario de aceptación |
| `rechazo_proyecto` aparte de `rechazo_fila` | `rechazo_fila` exige una carga y nombra la columna con `carga_columna_id`, que solo existe para los PI | Ampliar `rechazo_fila`, que debilita sus claves para todo el corte 1 |
| Vista Capstone sobre las tablas base y no sobre `v_tabla_maestra_pi` | El DROP VIEW ... CASCADE de una `R__` borraría la vista dependiente sin que Flyway la recree | Reusar la vista tradicional, más corta pero frágil a cada cambio de la tradicional |
| Plantilla `.xlsx` de «Cursos Capstone» versionada fuera de `tests/datos_inventados/` (propuesta) | El R-17 Capstone se llena desde `plantillas/R017_ambiental_capstone.xlsx`, y la regla 1 de `scripts/preflight.sh` rechaza todo `.xlsx` fuera de esa carpeta | Generar la hoja desde cero, que conviene solo si la Oficina de Calidad aprueba un formato distinto de la hoja «Cursos Capstone», que D-25 fija el 2026-10-30 |
| Copias de la plantilla con un código o un RUC no inventados generadas en la prueba (propuesta) | La regla 2 de `scripts/preflight.sh` rechaza en `tests/datos_inventados/` un número de 8 dígitos que no empieza con 99 | Versionar esos archivos con una excepción, que abre un hueco en la regla de datos inventados |
