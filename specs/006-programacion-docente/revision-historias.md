# Revisión por refutación de la historia de la programación docente del ciclo

**Fecha**: 2026-11-21
**Spec**: [spec.md](./spec.md)
**Entrada**: la candidata C-C01 «Cargar la programación docente del ciclo desde el archivo post-matrícula», una de las 21 candidatas que la auditoría del cambio del 2026-11-21 de la spec 005 escribe desde los correos de Claudia León y Mechelle Prado, y C-C02 «Nombre del docente en el R-17», que la revisión de la spec 005 deja fuera de alcance con D-12 y que esta revisión vuelve a mirar porque depende de C-C01
**Salida**: 4 historias (US-55 a US-58 de la spec), que salen de C-C01 con las correcciones de las tres lentes y la partición del redactor (propuesta). C-C02 queda fuera de alcance, con D-12
**Fuentes**: `historias_spec005_om_bp_2026-11-21.json` (candidatas, veredictos de las tres lentes y crítico de arquitectura) e `insumos_spec005_2026-11-21.md` (correos y estado del sistema), en la carpeta de notas de la sesión del plan, fuera del repositorio

## Método

La candidata parte refutada y sobrevive solo si resiste tres lentes independientes, como en las specs 001, 003, 004 y 005. La lente de necesidad pregunta si la exige el pedido de la carrera, el calendario de la semana 14 o un requisito del lanzamiento, y si cambia algo que `develop` no fija ya con prueba. La lente de solapamiento y tamaño aplica INVEST (independiente, negociable, valiosa, estimable, pequeña y comprobable) contra las demás candidatas y contra US-01 a US-54. La lente de verificabilidad coteja cada escenario con las migraciones V1_01, V1_02, V1_07 y V1_09, `app/permisos.py`, `db/datos/`, `db/pruebas/pruebas.sql` y `crear_rol_app.sql`. Después, el crítico de arquitectura ataca la decisión técnica de la candidata. Ningún auditor escribe en las copias de trabajo, se conecta a una base ni corre pruebas.

Los veredictos posibles son SOBREVIVE (S), CORREGIR (C), FUSIONAR (F), PARTIR (P), MOVER_A_DESPUES (M) y REFUTADA (R). Una candidata queda en el sprint si a lo sumo una lente la marca REFUTADA o MOVER_A_DESPUES. Este archivo registra los veredictos, su destino y las correcciones que la spec adopta, y el razonamiento completo está en el informe de cada lente.

## Veredictos por candidata

| Candidata | Título de la candidata | Necesidad | Solapamiento y tamaño | Verificabilidad | Historia final |
| --- | --- | --- | --- | --- | --- |
| C-C01 | Cargar la programación docente del ciclo desde el archivo post-matrícula | C, bloquea la semana 15 porque con D-10 no hay guion que cargue profesores reales, y no pertenece a la spec 005 | C, no se repite con ninguna historia y cabe en una, pero va a una spec propia, y un título contradice su escenario | C, cuatro fallas (el coordinador asignado no sube, el título del correo, el control no cabe en `control_cero` y `asignar_claves.py` vive fuera del repositorio) | US-55 a US-58 de la spec 006 |
| C-C02 | Nombre del docente en el R-17 | M, es D-12 y no hace falta para registrar en la semana 15 | M, depende de C-C01 y de D-12, y cambia Q15 y BR-R17-07 | M, `acceso.usuario_autorizado.nombre` no pasa el filtro de Q04, así que Q15 no lo vigilaría | Fuera de alcance, con D-12 |

Las tres lentes coinciden en C-C01, así que no hay desacuerdo que resolver. La lente de tamaño cuenta siete escenarios y la deja en una historia. Con las correcciones de las tres lentes y los faltantes de abajo, el conjunto llega a 19 escenarios con 29 casos, y el redactor la parte en cuatro historias (propuesta). US-55 es la carga en seco y con `--aplicar`, US-56 lo que ya existe en la base, US-57 los rechazos y la atomicidad, y US-58 la consulta, que es otro archivo, corre con otro usuario y se prueba sola. Esta partición no la vota ninguna lente, y la revisión de Jefferson la puede deshacer.

## Correcciones que la spec adopta

| Corrección | La propone | Dónde queda |
| --- | --- | --- |
| Llevar la historia a una spec 006 pequeña, sin migración y antes de la semana 14, en la única línea de trabajo | Las tres lentes y el crítico | La spec entera, con el orden de la Clarification «Session 2026-11-21» de esta spec y de J-41 de la spec 005 |
| Retitular «Un correo mal escrito se rechaza antes de la base», porque su cuerpo normaliza el correo y no lo rechaza | Tamaño y verificabilidad | US-55, «Un correo con mayúsculas o espacios se normaliza» |
| El coordinador asignado a una sección no sube ni declara, porque `_ALCANCE` da `acceso.docente_seccion` solo al rol PROFESOR. El escenario pasaba con un resultado que no sirve | Necesidad y verificabilidad | US-56, con el aviso «… es COORDINADOR y no podrá subir ni declarar …», y el cambio de `_ALCANCE` fuera de alcance |
| La consulta de secciones sin docente no cabe en `control_cero` de `db/pruebas/pruebas.sql`, porque esa base tiene a propósito dos secciones 301 sin profesor | Verificabilidad | US-58, consulta informativa en `db/plataforma/neon/`, con el molde de `pi_sin_descripcion_instrumento.sql` (AD-29 de la spec 005) |
| El conflicto de `uq_seccion_curso_bb` es una fila inválida | Verificabilidad | US-57, esquema de filas inválidas |
| La contraseña sale de la historia y sigue en `asignar_claves.py`, que vive en `ABET_SIS_MED/herramientas_neon/` y no en el Back | Tamaño y verificabilidad | US-55, escenario «El guion no asigna contraseñas», y D-45 |
| El formato real del archivo bloquea un CSV de prueba fiel. Si no llega antes de la semana 14, la Coordinación llena un CSV mínimo | Necesidad, tamaño, verificabilidad y crítico | D-44, con el CSV mínimo de FR-002 |
| Plan alterno si el formato no llega a tiempo, con un SQL de datos repetible desde el Windows | Necesidad | La spec sigue la alternativa del crítico, el CSV mínimo con el mismo guion, porque un SQL a mano no tiene corrida en seco (propuesta) |

## Historias faltantes

| Faltante | La propone | Historia o requisito final |
| --- | --- | --- |
| Un profesor dado de baja que vuelve en el archivo. Sin un caso, nada fija si el guion lo reactiva | Redactor (propuesta) | US-56, «Un profesor dado de baja no se reactiva» |
| Una asignatura sin plan de medición en el periodo. Su sección entra, pero P2 responde «La carrera aún no registra el plan de medición de esta sección.» al subir | Redactor (propuesta) | US-56, con aviso |
| Una falla de la base a mitad de la escritura. Sin ella, nada prueba que la transacción es una sola | Redactor (propuesta), por el Principio III | US-57, con un disparador de prueba |
| Todas las filas inválidas en un solo informe, para corregir el archivo una vez | Redactor (propuesta) | US-57 |
| El archivo real dentro de la copia de trabajo del repositorio, que es público | Redactor (propuesta), por la regla 6 de `AGENTS.md` | US-57 y FR-009 |
| Codocencia, con dos profesores en la misma sección | Redactor (propuesta), por `uq_docente_seccion`, que admite varios usuarios por sección | US-55 |
| La consulta en solo lectura y sin periodo | Redactor (propuesta), con el molde de `pi_sin_descripcion_instrumento.sql` | US-58 |

## Veredicto del crítico de arquitectura

| N.º | Decisión | Veredicto | Lo que adopta la spec |
| --- | --- | --- | --- |
| C-C01 (AD-49 de la spec 005) | Guion repetible de la programación docente post-matrícula, en seco por omisión y con `--aplicar` en una transacción | SE_SOSTIENE | Spec 006 pequeña, sin migración, con la consulta de secciones con plan y sin docente. El guion acepta un CSV mínimo si el archivo no llega, las contraseñas siguen aparte y la corrida real va desde el Windows con el permiso de Jefferson |
| C-C02 (AD-50 de la spec 005) | Nombre del docente en `acceso.usuario_autorizado.nombre` para llenar D10 del R-17 | DUDOSA | Fuera de alcance. Si entra, va en V1_13 o después, nunca en V1_12, con la regla para dos docentes que decida la carrera |

El crítico revisa la decisión de conjunto, y el redactor la baja a cinco decisiones técnicas (propuestas), que el crítico ataca una por una en T006 de `tasks.md`, con el resultado del apartado siguiente.

| N.º | Decisión | Origen | Lo que adopta la spec |
| --- | --- | --- | --- |
| AD-01 | Guion en Python con la biblioteca estándar, que llama a psql 18 | Redactor (propuesta) | FR-001 y J-42. El Windows tiene Python 3.14 y psql 18 y no necesita instalar psycopg, y las pruebas lo corren con Python 3.12 |
| AD-02 | La corrida en seco ejecuta el mismo SQL y termina con ROLLBACK | Redactor (propuesta) | FR-006. El informe en seco cuenta lo que escribiría la corrida real, sin una segunda lógica que pueda divergir |
| AD-03 | INSERT con `ON CONFLICT DO NOTHING` y un solo UPDATE, el del `curso_blackboard` nulo, sin DELETE ni cambios de `rol` o `activo` (título del 2026-11-22, T006) | Redactor (propuesta), con la corrección de la necesidad sobre lo que el archivo no trae y la del crítico de T006 | FR-005 y US-56. Cada INSERT nombra su objetivo, `(periodo_id, asignatura_id, numero)`, `(correo)` y `(usuario_id, seccion_id)` |
| AD-04 | Consulta informativa en `db/plataforma/neon/` y no un control Q | Lente de verificabilidad | FR-011 y US-58 |
| AD-05 | Archivo real fuera de todo repositorio, enviado al Windows con `scp` y borrado al terminar, y conexión por las variables de libpq | Redactor (propuesta), por la regla 6 de `AGENTS.md` y las instrucciones de Jefferson sobre el Windows | FR-009, FR-010 y J-42 |

## Revisión de AD-01 a AD-05 por el crítico (T006, 2026-11-22)

El crítico de arquitectura ataca las cinco decisiones antes de construir, contra el código de `develop` 7fc19a9 y con ensayos de psql en un clúster desechable, sin tocar localhost:5432, Neon ni el Windows. La construcción adopta lo que el crítico marca CAMBIAR o corregir con una razón que el código o un `.feature` sostiene, y deja como duda lo que la spec no fija.

| N.º | Veredicto | Lo que cambia o queda como duda |
| --- | --- | --- |
| AD-01 | SE_SOSTIENE | El guion fija su salida en UTF-8, porque con `python -I` el Windows escribe en cp1252 hacia una tubería, entrega las filas a psql como bytes UTF-8 y normaliza el correo con la misma expresión de `app.sesion.normalizar_correo()`, con una prueba que compara las dos. Con `-I` no entra la carpeta del guion en `sys.path`, así que el guion no importa `abet_carga` ni `app` |
| AD-02 | SE_SOSTIENE | Cambia el flujo de la forma. El escenario «El informe nombra todas las filas inválidas» junta una falla de la base (fila 2) y una de forma (fila 3), así que el guion entrega todas las filas a psql con su marca de forma y solo un archivo entero ilegible termina sin conectarse (plan.md, viñeta Guion). El código 1 se separa del 3 con una línea centinela y no con el texto de un error de psql, que cambia con el idioma |
| AD-03 | CAMBIAR | Nuevo título, «INSERT con ON CONFLICT DO NOTHING y un solo UPDATE, el del curso_blackboard nulo, sin DELETE ni cambios de rol o activo», porque FR-005 completa con UPDATE el curso nulo de una sección. En el clúster desechable, un `ON CONFLICT DO NOTHING` sin objetivo se salta en silencio el choque de `uq_seccion_curso_bb`, así que cada INSERT nombra su objetivo y ese choque llega como error de la base, con código 3 |
| AD-04 | SE_SOSTIENE | Sin cambios. `db/pruebas/pruebas.sql` tiene a propósito las secciones 301 sin profesor, y `abet_respaldo` lee `abet` y `acceso` en solo lectura |
| AD-05 | DUDOSA | `db/README.md` asigna las variables `NEON_*` a las de libpq con `PGSSLMODE=require`, `PGCHANNELBINDING=require`, `PGCLIENTENCODING=UTF8` y la ruta completa de psql, y el guion busca `.git` como carpeta o como archivo en cada carpeta que contiene el archivo, porque en un worktree `.git` es un archivo. Quedan dos dudas para Jefferson antes de T063, si el informe real, con correos, puede pasar por un agente, y qué se hace con la 410 y la 411 inventadas de 450002 que tiene la rama principal de Neon |

Las dudas que la spec no fija quedan en la Clarification «Session 2026-11-22» de `spec.md`, con el valor que la construcción aplica mientras tanto.

## Decisiones que salen de la revisión

- De la carrera, D-44 (formato, dueño y fecha del archivo de la programación) y D-45 (si el guion crea la cuenta del profesor), con su valor provisional en la spec. D-12 de la spec 001 sigue abierta con su dueño.
- De Jefferson, J-42 (dónde vive el guion y cómo se prueba con datos inventados), con el valor que propone la spec.
- Para la carrera, la pregunta de si un coordinador que también dicta debe subir y declarar en su sección, que cambiaría `_ALCANCE` y BR-ACCESO-08 y queda fuera de esta spec.
