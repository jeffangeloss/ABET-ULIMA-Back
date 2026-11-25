---
name: Análisis por indicador
description: Semáforo, hallazgo y tipo de registro de cada PI de una carga publicada en la ruta 13, y la causa y la acción que el profesor registra por PI como oportunidad de mejora o buena práctica, con borrador, declaración de solo INSERT, controles de privacidad y herencia en el reemplazo.
targets:
  - ../../../abet_carga/resultados.py
  - ../../../abet_carga/r17.py
  - ../../../app/permisos.py
  - ../../../app/rutas/cargas.py
  - ../../../app/rutas/mejora.py
  - ../../../db/migration/V1_15__mejora_borrador_y_declaracion.sql
  - ../../../db/plataforma/neon/crear_rol_app.sql
  - ../../../db/plataforma/neon/controles_neon.sql
  - ../../../db/pruebas/pruebas.sql
---

# Análisis por indicador

> **Estado al 2026-11-24.** Spec viva nueva de la fase 1 de contrato de la spec 005 (T010), escrita antes del código en la rama `feat/005-oportunidades-de-mejora`, con el alcance que Jefferson aprueba el 2026-11-18 («Sí, apruébala») y su cambio del 2026-11-21 («Sí, apruébalas»). La migración de esta spec es V1_15 y no V1_12, porque la spec 008 toma V1_12 a V1_14 (FR-004 de la spec 008). Las rutas 13 a 16 nacen en la fase 3 (T030 a T036), V1_15 y los permisos en la fase 2 (T021) y Q16 y Q17 con T039, y la sección Verification se llena con T050.

Esta spec viva fija qué entrega la ruta 13 de la interfaz de programación de aplicaciones (application programming interface, API), `GET /api/cargas/{carga_id}/indicadores` (propuesta), con las cifras, el semáforo, el hallazgo y el tipo de registro de cada indicador de desempeño (performance indicator, PI) de una carga publicada. Fija también cómo el profesor registra en la pantalla P4 una causa y una acción por PI con las rutas 14 a 16 (propuestas), y qué guarda la base en las cuatro tablas de V1_15. El sistema rotula cada registro como oportunidad de mejora (OM) si el PI no alcanza la meta y como buena práctica (BP) si la alcanza o la supera.

Cada regla de negocio (business rule, BR) nombra su fuente en `specs/005-oportunidades-de-mejora/spec.md`, sean historias de usuario (user stories, US), requisitos funcionales (functional requirements, FR), decisiones técnicas del crítico de arquitectura (AD) o decisiones abiertas (D de la carrera y J de Jefferson). Cada regla nombra también la tabla, la restricción o la consulta de control que la respalda y el escenario que la prueba, citado por su título, de `semaforo.feature` o de `declaracion.feature` de `specs/005-oportunidades-de-mejora/aceptacion/`. Los textos entre «» son literales, y lo marcado «(propuesta)» no está fijado en las decisiones de la spec, como en los `.feature`. Los ejemplos usan solo datos inventados, con correos del dominio reservado `example.invalid`.

El R-17 que se entrega solo con la declaración vigente completa (US-49) y sus recuadros A y B compuestos por PI (US-50) viven en `specs/features/r17/r17.spec.md`, con BR-R17-12 y el cambio fechado de BR-R17-04. La navegación con el botón atrás (US-52) vive solo en el Front, sin spec viva en el Back.

## User Stories

| ID | Descripción | Spec |
| --- | --- | --- |
| US-45 | Las cifras, el semáforo y el hallazgo de una carga | spec 005 |
| US-46 | Ver el semáforo en P4 al terminar la carga | spec 005 |
| US-47 | Registrar por indicador la oportunidad de mejora o la buena práctica en P4 | spec 005 |
| US-48 | El borrador se guarda solo y no se pierde | spec 005 |
| US-53 | El análisis por indicador no lleva datos de estudiantes | spec 005 |
| US-54 | El reemplazo trae el análisis anterior como borrador | spec 005 |

## Business Rules

### BR-MEJORA-01: La ruta 13 entrega por PI las cifras del R-17, el semáforo, el hallazgo y el tipo (propuesta)
- `GET /api/cargas/{carga_id}/indicadores` responde con `carga_id`, `estado`, `provisional`, `conjunto_reglas`, `conjunto_reglas_estado`, `parametros_pendientes`, `meta_pct`, `corte_rojo_pct` e `indicadores`, ordenados por `so_numero` y por `pi.numero`. `corte_rojo_pct` es nulo mientras CORTE_ROJO esté PENDIENTE.
- Cada indicador trae las claves de FR-006 de la spec 004 más `semaforo`, `hallazgo` y `tipo_registro`, leídas de `abet.v_r17_por_pi` en una sola instantánea, con CORTE_ROJO leído de `abet.parametro_valor`. El Front copia el hallazgo y el tipo sin calcularlos.
- El hallazgo de `redactar_hallazgo()` de `abet_carga/resultados.py` sigue la forma «5.2: 54,5 % en Satisfactorio o más, meta 80,0 %», con el logro sobre calificados, el nombre del nivel esperado en la escala de B40 de la plantilla y la meta, ambos con un decimal y coma decimal. Un PI sin calificaciones lleva «5.3: sin calificaciones en esta carga.».
- Con R-2026-BORRADOR la 410 de 450002 da 63,6 %, 63,6 % y 72,7 %, los tres en ROJO, y la 412 de 450002 da 81,8 % VERDE, 54,5 % ROJO y 90,9 % VERDE.
- **Fuente**: US-45, FR-001, FR-002, SC-001, AD-42 y J-29 de la spec 005.
- **Prueba**: «La 410 publicada con el conjunto borrador queda en rojo y pide tres oportunidades de mejora», «La 412 de 450002 muestra verde, rojo y verde, con dos buenas prácticas» y «Las cifras y el semáforo coinciden con el R-17 de la misma carga» (`semaforo.feature`).

### BR-MEJORA-02: El Back decide el semáforo con la meta y el corte rojo (propuesta)
- El semáforo de un PI es SIN_DATO si falta el logro o la meta, VERDE si `en_meta()` de `abet_carga/resultados.py` es verdadero y AMBAR si CORTE_ROJO está DEFINIDO y el logro queda desde el corte hasta debajo de la meta. En los demás casos es ROJO.
- Así VERDE coincide con «En la meta» de P6 y con el texto «¡Felicidades! …» de la celda H del R-17, y ROJO o AMBAR coinciden con «El indicador aún no alcanza …».
- El 80,0 % justo en la meta es VERDE, el 75,0 % justo en el corte es AMBAR y, con CORTE_ROJO PENDIENTE, como en R-2026-BORRADOR, ningún PI sale AMBAR.
- Un conjunto de reglas sin NIVEL_ESPERADO o sin META_LOGRO definidos deja cada indicador en SIN_DATO y la ruta responde 200, nunca 500, con el hallazgo «5.1: el conjunto de reglas no define la meta o el nivel esperado.».
- **Fuente**: US-45, FR-002, J-29, D-35 y AD-02 y AD-03 de la spec 005.
- **Prueba**: «El 80,0 % justo en la meta queda en verde y pide una buena práctica», «Con el corte rojo definido, la banda ámbar va desde el corte hasta debajo de la meta y pide una oportunidad de mejora», «Con el corte rojo pendiente no hay ámbar» y «Un parámetro sin definir deja los indicadores sin dato y no rompe la ruta» (`semaforo.feature`).

### BR-MEJORA-03: El semáforo fija el tipo de registro, en la ruta y en la base (propuesta)
- `tipo_de_registro()` de `abet_carga/resultados.py` da BUENA_PRACTICA con VERDE, OPORTUNIDAD_MEJORA con AMBAR o ROJO y nulo con SIN_DATO. El profesor no elige el tipo, y cada PI lleva un solo registro (valor provisional de D-39).
- La ruta 15 responde 422 con «El tipo de registro de cada indicador lo fija su semáforo.» cuando el `tipo` del cuerpo no es el que devuelve la ruta 13, y no guarda nada.
- En la base, `ck_mejora_declaracion_pi_tipo` admite solo OPORTUNIDAD_MEJORA y BUENA_PRACTICA, `ck_mejora_declaracion_pi_semaforo` admite solo VERDE, AMBAR y ROJO y `ck_mejora_declaracion_pi_coherencia` exige, con el semáforo presente, BUENA_PRACTICA solo con VERDE y OPORTUNIDAD_MEJORA con AMBAR o ROJO.
- Una sección con todos sus PI en la meta también registra, con una BP por PI (valor provisional de D-36).
- **Fuente**: US-45, US-47, D-36, D-39, AD-34 y AD-35 de la spec 005.
- **Prueba**: «El tipo de registro lo fija el semáforo, en la ruta y en la base» (`declaracion.feature`) y «La 412 de 450002 muestra verde, rojo y verde, con dos buenas prácticas» (`semaforo.feature`).

### BR-MEJORA-04: Un PI sin calificaciones no lleva registro (propuesta)
- Un PI sin ninguna medición CALIFICADO trae `pct_sobre_calificados` nulo, `pct_sobre_total` 0,0, `semaforo` SIN_DATO y `tipo_registro` nulo, y nunca sale ROJO.
- La declaración no exige su registro, la ruta 15 rechaza uno con 422 y «El indicador 5.3 no lleva registro porque su semáforo no tiene dato.», y P4 muestra solo su hallazgo, sin campos (valor provisional de D-40).
- Una carga cuyos PI son todos SIN_DATO se declara con un borrador de arreglo `indicadores` vacío, porque la ruta 16 no acepta la versión 0 sin borrador.
- **Fuente**: US-45, US-47, D-40 y AD-35 de la spec 005.
- **Prueba**: «Un PI sin calificaciones sale sin dato, nunca en rojo y sin tipo de registro» (`semaforo.feature`), «Un PI sin calificaciones no exige registro y no lo admite» y «Un PI sin calificaciones muestra su hallazgo sin campos» (`declaracion.feature`).

### BR-MEJORA-05: Las rutas 13 a 16 siguen el alcance de la constancia y escribe solo el profesor de la sección (propuesta)
- Las cuatro rutas responden 401 sin sesión y 403 con «La sección no está a su cargo.» a una carga ajena o inexistente, con el mismo texto para no revelar cuáles existen. El coordinador lee con `puede_leer()` de `app/permisos.py`.
- Solo el profesor asignado escribe en las rutas 15 y 16, con `puede_declarar()` de `app/permisos.py`, y el 403 llega antes de leer el cuerpo, aunque el cuerpo no sea JSON. El coordinador lee la declaración vigente y nunca recibe el texto del borrador.
- Una carga RECHAZADA o REEMPLAZADA responde 409 con «La carga no está publicada y no tiene semáforo.» en la ruta 13 y con «La carga no está publicada y no admite causas ni acciones.» en las rutas 15 y 16, y la respuesta de una REEMPLAZADA trae `reemplazada_por`.
- Las respuestas siguen el orden 401, 403, 422 y 409, salvo el 409 de la carga no publicada y el de la regla sin definir de BR-MEJORA-09, que mandan.
- **Fuente**: US-45, US-47, FR-001, FR-005, J-33, AD-09, AD-23 y AD-27 de la spec 005.
- **Prueba**: «Sin sesión la ruta responde 401», «El profesor solo ve el semáforo de sus secciones» y «Una carga que no está publicada no tiene semáforo» (`semaforo.feature`), y «Solo el profesor asignado escribe, aunque el cuerpo no sea JSON», «Una carga que no está publicada responde 409 al guardar y al declarar» y «El coordinador lee la declaración sin editarla ni ver el borrador» (`declaracion.feature`).

### BR-MEJORA-06: El borrador tiene una sola versión por carga (propuesta)
- `abet.mejora_borrador` guarda una fila por carga con su `version`, y `abet.mejora_borrador_pi` un registro por PI con `causa` y `accion` nulas. La ruta 15 reemplaza el conjunto de registros de la carga en la misma transacción que sube la versión, así que un PI ausente del arreglo queda con los dos campos nulos por UPDATE.
- Un borrador parcial se acepta. Un PUT con una versión distinta de la guardada responde 409 con «Otra pestaña guardó un texto más reciente.», los registros guardados y su versión, y el borrador no cambia.
- La ruta 14 responde `declaracion`, `borrador`, `borrador_pendiente`, `heredado_de` y `puede_editar`, y una carga sin texto trae `declaracion` y `borrador` nulos.
- **Fuente**: US-47, US-48, J-30, AD-19 y AD-38 de la spec 005.
- **Prueba**: «Un borrador parcial se acepta», «Dos pestañas no se pisan el borrador» y «Una carga sin texto responde con la declaración y el borrador nulos» (`declaracion.feature`).

### BR-MEJORA-07: El cuerpo de las rutas 15 y 16 es cerrado y no lleva responsable, plazo ni estado (propuesta)
- Las rutas 15 y 16 exigen JSON y responden 422 con «El cuerpo trae claves que esta ruta no admite.» a un cuerpo con claves fuera del contrato, como `responsable`, `plazo` o `estado`, y con «Cada indicador va una sola vez en el cuerpo.» a un PI repetido, sin cambiar nada.
- Un PI que la carga no mide responde 422 con «El indicador 2.1 no pertenece a esta carga.», y la base lo rechaza también por la clave foránea (foreign key, FK) (`carga_id`, `pi_id`) de las tablas por PI hacia `abet.carga_columna`, sostenida por `uq_carga_columna_pi`.
- La ruta 14 deriva el estado PROPUESTA de cada indicador declarado sin guardarlo, y ninguna tabla de V1_15 tiene columnas de estado, responsable ni plazo (D-42).
- **Fuente**: US-47, FR-004, FR-005, D-42, AD-43 y AD-44 de la spec 005.
- **Prueba**: «El profesor no fija responsable, plazo ni estado», «Un PI repetido en el cuerpo se rechaza», «Un PI que la carga no mide se rechaza en la ruta y en la base» y «Las tablas de V1_15 no tienen estado, responsable ni plazo, y abet_app no corrige una declaración» (`declaracion.feature`).

### BR-MEJORA-08: Cada causa y cada acción se normalizan y admiten hasta 800 puntos de código (propuesta)
- El Back normaliza cada campo a la forma canónica compuesta de Unicode (Normalization Form C, NFC), cambia `\r\n` por `\n`, rechaza los caracteres de control salvo `\n` y `\t` y cuenta puntos de código, hasta 800 por campo (J-39).
- Un campo de 801 puntos de código responde 422 con «Cada campo admite hasta 800 caracteres.» y uno con U+0007 responde 422 con «El texto trae caracteres que no se pueden guardar.», y en los dos casos nada cambia. Las columnas `causa` y `accion` de las tablas por PI son varchar(800).
- **Fuente**: US-47, FR-005, J-39, AD-10 y AD-39 de la spec 005.
- **Prueba**: «Un texto demasiado largo o con caracteres de control se rechaza y nada cambia» y «Una causa de 800 puntos de código se acepta» (`declaracion.feature`).

### BR-MEJORA-09: La declaración es completa, de solo INSERT y guarda la foto del semáforo (propuesta)
- La ruta 16 declara en una sola transacción la versión exacta del borrador. Exige causa y acción no en blanco en cada PI con calificados y escribe la cabecera en `abet.mejora_declaracion` y una fila por PI en `abet.mejora_declaracion_pi`, con el tipo y la foto de `logro_pct`, `meta_pct` y `semaforo` de `abet.v_r17_por_pi` (J-40).
- Un registro incompleto, una acción de solo espacios o la versión 0 sin borrador responden 422 con «Complete la causa y la acción de cada indicador.», y un PI con calificados que queda SIN_DATO por una regla sin definir responde 409 con «El conjunto de reglas no define la meta o el nivel esperado. La declaración espera a la Coordinación.». En ningún caso nace una declaración.
- La declaración vigente de una carga es la de mayor `declaracion_id`. Corregirla guarda un borrador nuevo con `borrador_pendiente` verdadero, y la anterior sigue vigente y guardada hasta declarar la versión nueva (valor provisional de D-37).
- `ck_mejora_declaracion_pi_texto` exige en `causa` y `accion` al menos un carácter visible, con la definición de blanco de `ck_plan_medicion_descripcion` (BR-R17-11), y la FK (`declaracion_id`, `carga_id`) obliga a cada fila a repetir la carga de su cabecera.
- **Fuente**: US-47, FR-004, FR-005, D-37, J-38, J-40, AD-33 y AD-36 de la spec 005.
- **Prueba**: «El profesor registra y declara los tres PI de la 412, con dos buenas prácticas y una oportunidad de mejora», «Declarar con un registro incompleto no crea ninguna declaración», «Declarar la versión 0 sin ningún borrador no crea ninguna declaración», «Una regla sin definir detiene la declaración» y «Corregir una declaración deja la anterior guardada y vigente hasta declarar la nueva» (`declaracion.feature`).

### BR-MEJORA-10: El análisis no lleva códigos ni correos de estudiantes (propuesta)
- Las rutas 15 y 16 y los CHECK `ck_mejora_borrador_pi_sin_codigos` y `ck_mejora_declaracion_pi_sin_codigos` usan el mismo patrón ASCII, que es un número de exactamente 8 dígitos no rodeado de otros dígitos o un correo. Ante un código o un correo, la ruta responde 422 con «La declaración no puede llevar códigos ni correos. Describa las causas y las acciones sin datos de estudiantes.» y no guarda nada, ni como borrador.
- Un número de 9 dígitos o una fecha como «18/11/2026» se aceptan. La violación de un CHECK sale como 422 y nunca como 500, y ni el error ni el registro de la aplicación repiten el texto.
- Las rutas 13 a 16 responden `Cache-Control: no-store` y ningún cuerpo trae códigos, nombres ni correos de estudiantes. Un nombre propio escrito en el texto no se detecta, y BR-R17-07 se cumple en estos campos por aviso y no por construcción (J-36).
- **Fuente**: US-53, FR-013, J-36, AD-11 y AD-30 de la spec 005.
- **Prueba**: «Un código o un correo de estudiante se rechaza y no se guarda ni como borrador», «Un número de 9 dígitos o una fecha no son un código de estudiante», «La base rechaza un código en el borrador aunque la API se salte la validación», «La base rechaza un correo en la declaración» y «Las rutas 13 a 16 no se guardan en caché y no traen datos de estudiantes» (`declaracion.feature`).

### BR-MEJORA-11: Q16 y Q17 vigilan el texto y la completitud de la declaración vigente (propuesta)
- La consulta de control Q16 busca códigos y correos, con el patrón de BR-MEJORA-10, en `causa` y `accion` de `abet.mejora_borrador_pi` y de `abet.mejora_declaracion_pi`.
- Q17 lista cada declaración vigente de una carga PUBLICADA a la que le falta la fila de un PI de `abet.carga_columna` con al menos una medición CALIFICADO, con la carga y el PI y sin ningún texto del profesor. Es la misma regla de `DeclaracionPendiente` de BR-R17-12.
- Las dos devuelven 0 filas, tienen su caso en la transacción que se deshace de `db/pruebas/pruebas.sql` y se repiten iguales en `db/plataforma/neon/controles_neon.sql`, cada una con su `\set qNN :ROW_COUNT`. Ningún control de 0 filas compara la foto de la declaración con `abet.v_r17_por_pi`, porque un cambio legítimo de la meta de un conjunto BORRADOR no es un dato corrupto (J-40).
- **Fuente**: US-53, FR-018, SC-005, AD-37 y AD-56 de la spec 005.
- **Prueba**: «Q16 y Q17 dan 0 filas con declaraciones sanas», «Q17 ve un PI con calificados sin su registro en la declaración vigente» y «Neon corre los mismos controles» (`declaracion.feature`).

### BR-MEJORA-12: abet_app escribe el borrador por columnas exactas y solo inserta la declaración (propuesta)
- `db/plataforma/neon/crear_rol_app.sql` da a `abet_app` el SELECT de las cuatro tablas de V1_15. En `abet.mejora_borrador` le da el INSERT de `carga_id`, `version` y `actualizado_por` y el UPDATE de `version`, `actualizado_en` y `actualizado_por`, y en `abet.mejora_borrador_pi`, el INSERT de `carga_id`, `pi_id`, `causa` y `accion` y el UPDATE de `causa` y `accion`.
- En `abet.mejora_declaracion` y en `abet.mejora_declaracion_pi`, el rol recibe solo el INSERT de tabla completa, así que no corrige ni borra una declaración. Ninguna de las cuatro tablas le da DELETE, TRUNCATE ni UPDATE de tabla completa.
- La comprobación final del archivo lista con `has_table_privilege` y `has_column_privilege` los permisos exactos del rol y se detiene, sin dejar ningún cambio, si sobra o falta uno. En una base anterior a V1_15 el archivo no da estos permisos y sus listas quedan como antes.
- **Fuente**: US-47, FR-004, J-38, AD-56 y el Principio VI de la constitución.
- **Prueba**: «Las tablas de V1_15 no tienen estado, responsable ni plazo, y abet_app no corrige una declaración» (`declaracion.feature`).

### BR-MEJORA-13: La carga que reemplaza a otra hereda el análisis al leer, por PI y con el tipo nuevo (propuesta)
- Si la carga nueva no tiene borrador ni declaración, la ruta 14 devuelve en `borrador` los registros de la declaración vigente de la carga que reemplaza o, sin ella, los de su borrador. El borrador heredado llega con `version` 0 y `heredado_de` igual al `carga_id` de la carga anterior, y la subida no escribe nada de la herencia.
- La herencia va por `pi_id`, copia solo los PI que la carga nueva mide y que en ella llevan registro, y cada uno llega con el tipo que fija el semáforo de la carga nueva. El texto se guarda en la carga nueva recién con el primer PUT, y su R-17 responde 409 hasta declarar.
- El coordinador que reemplaza no ve el texto heredado, y un PUT a la carga reemplazada responde 409 con `reemplazada_por`.
- **Fuente**: US-54, FR-014, AD-17 y AD-55 de la spec 005.
- **Prueba**: «La carga nueva hereda el análisis declarado con el tipo de sus cifras», «Un PI que queda sin calificaciones en la carga nueva no se hereda», «Sin texto declarado se hereda lo que haya, o nada», «Subir el mismo archivo no cambia nada», «Un reemplazo hecho por coordinación hereda igual y coordinación no ve el texto heredado» y «Un PUT a la carga reemplazada responde 409 con la carga nueva» (`declaracion.feature`).

### BR-MEJORA-14: P4 escribe lo que trae la API y guarda el borrador en la base (propuesta)
- P4 suma «Cómo va su sección», con una fila por PI, una luz de color con `aria-hidden` y el estado en texto, la leyenda armada con `meta_pct` y `corte_rojo_pct` y la franja provisional cuando `provisional` es verdadero. Un PI SIN_DATO nunca se dibuja como 0 % ni en rojo, y una carga que no está publicada no pide la ruta 13.
- Debajo va «Análisis por indicador», con un bloque por PI que empieza con su hallazgo copiado y el rótulo de su tipo, «Causa probable» y «Acción de mejora» en una OM y «Causa del logro» y «Buena práctica que conviene mantener o compartir» en una BP, sin campos de responsable, plazo ni estado.
- P4 guarda el borrador 2,5 s después de la última tecla, con un máximo de 15 s, al salir de un campo y en `pagehide`, nunca en `localStorage` ni en `sessionStorage`, y un 401 o un 500 no borran el texto. Con un Back anterior que responde 404 en la ruta 13, P4 se comporta como antes.
- **Fuente**: US-46, US-47, US-48, US-53, FR-003, FR-006, FR-007, J-35, AD-22 y AD-28 de la spec 005.
- **Prueba**: los escenarios con `@delegado_a_vitest`, que prueba el Front, entre ellos «P4 muestra la tabla de niveles con un estado por PI», «La leyenda sale de la respuesta», «Un PI sin dato no se pinta como 0 % ni en rojo», «Con un Back anterior, P4 se comporta como hoy» (`semaforo.feature`), «P4 del profesor muestra un bloque por PI con los rótulos de su tipo», «El guardado automático sale 2,5 segundos después de escribir y al salir de un campo», «Un 401 durante el guardado no pierde el texto» y «El navegador no guarda el texto» (`declaracion.feature`).

## Verification

Corrida del 2026-11-24 en el Back y en el Front, rama `feat/005-oportunidades-de-mejora` (Back 027c5be, Front a579f59), sobre un PostgreSQL 18 desechable que arma la propia suite. La más reciente va primero y cada línea lleva la fecha, el comando, el archivo de prueba y las reglas que cubre.

```text
- 2026-11-24 · ABET_FRONT_RAIZ=<Front> uv run --frozen --no-build python -m pytest -q -p no:cacheprovider (2560 passed y 15 skipped) · test_semaforo_feature.py, test_declaracion_feature.py, tests/test_api_indicadores.py, tests/test_api_mejora.py, tests/test_resultados.py → BR-MEJORA-01 a BR-MEJORA-13
- 2026-11-24 · tests/test_mejora_base.py en el mismo comando (37 pruebas) y bash db/pruebas/correr_pruebas.sh («RESULTADO: todo pasó») → BR-MEJORA-07, BR-MEJORA-10, BR-MEJORA-11 y BR-MEJORA-12 (V1_15, los CHECK, los permisos de abet_app y Q16 y Q17)
- 2026-11-24 · npm test del Front (26 archivos y 378 aprobadas), con tests/spec005/semaforo.test.tsx, declaracion.test.tsx, app.test.tsx y navegacion.test.tsx → BR-MEJORA-14 y los 23 escenarios con @delegado_a_vitest
- 2026-11-24 · npx playwright test e2e/humo.spec.ts (Front) contra scripts/api_local.sh del Back (5 passed) → BR-MEJORA-01, BR-MEJORA-05, BR-MEJORA-09 y BR-MEJORA-14 en local
```

Resultado: suite completa del Back, 2560 passed y 15 skipped in 873.45s (0:14:33), con los 118 casos de los cuatro `.feature` de la spec 005 aprobados, 23 de ellos delegados a Vitest; Vitest del Front, 26 archivos y 378 pruebas aprobadas con 1 `todo`; humo local, 5 passed. Q16 y Q17 en `controles_neon.sql` corren contra Neon con T024 y T063, y el humo contra la vista previa de `develop` con T062. El detalle por historia está en `specs/005-oportunidades-de-mejora/audit.md`.
