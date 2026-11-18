---
name: Acceso
description: Usuarios autorizados en el esquema acceso, sesión con contraseña asignada en la cookie abet_sesion, límite de intentos y visibilidad por acceso.docente_seccion.
targets:
  - ../../../app/sesion.py
  - ../../../app/permisos.py
  - ../../../app/rutas/*.py
  - ../../../scripts/asignar_clave.py
  - ../../../db/migration/V1_09__crear_acceso.sql
---

# Acceso

> **Estado al 2026-11-18.** BR-ACCESO-10 y los cambios fechados de BR-ACCESO-07 y BR-ACCESO-08 llegan con la fase 1 de la spec 004 (T010), escritos antes de su código. **Estado al 2026-11-17.** BR-ACCESO-07 y BR-ACCESO-08 suman el reemplazo y la lista de cargas del corte 2 (T080), escritos antes de su código, y BR-ACCESO-09 espera a T018. **Estado al 2026-10-30.** Reglas de la fase 1 de contrato (T013), escritas antes del código. Los archivos de `targets` nacen en las fases 2 y 3, y los nombres de tablas, columnas y restricciones de `acceso` salen de `V1_09__crear_acceso.sql` (T024) y los permisos de `abet_app`, de `db/plataforma/neon/crear_rol_app.sql` (T025). La sección Verification se llenó el 2026-10-30 con la corrida del corte 1 (T061); las reglas del corte 2 la reciben con T088.

Esta spec viva fija quién entra al sistema, cómo viaja su sesión y qué secciones alcanza cada rol en la interfaz de programación de aplicaciones (application programming interface, API). Cada regla de negocio (business rule, BR) nombra su fuente en `specs/001-mvp-carga-r17/spec.md`, sean historias de usuario (user stories, US), requisitos funcionales (functional requirements, FR), criterios de éxito (success criteria, SC) o decisiones abiertas (D de la carrera y J de Jefferson). Cada regla nombra también la restricción de la base que la respalda y el escenario que la prueba, citado por su título, casi siempre de `specs/001-mvp-carga-r17/aceptacion/acceso.feature`. Los textos entre «» son literales, y lo marcado «(propuesta)» no está fijado en las decisiones de la spec, como en los `.feature`, aunque algún escenario ya lo compruebe. Las reglas del corte 2 llevan esa marca en su título. Todos los correos de los ejemplos son de prueba, con el dominio reservado `example.invalid`.

## User Stories

| ID | Descripción | Corte |
| --- | --- | --- |
| US-04 | Registrar usuarios autorizados y docentes por sección | 1 |
| US-05 | Iniciar sesión con contraseña asignada | 1 |
| US-06 | Ver solo las secciones propias del periodo (la regla de visibilidad) | 1 |
| US-20 | Recibir el código de acceso en el correo institucional | 2 |
| US-38 | El reporte solo muestra mis secciones (spec 004) | spec 004 |

## Business Rules

### BR-ACCESO-01: Usuarios autorizados en un esquema aparte
- `V1_09__crear_acceso.sql` crea el esquema `acceso` aparte de `abet`, porque la consulta de control Q04 falla si `abet` tiene columnas con nombres o datos de contacto y los usuarios tienen correo.
- `acceso.usuario_autorizado` guarda el correo normalizado, en minúscula y sin espacios, una sola vez (`uq_usuario_autorizado_correo` y `ck_usuario_autorizado_correo`), el rol PROFESOR o COORDINADOR (`ck_usuario_autorizado_rol`), `activo` y `creado_en`. Un usuario se da de baja con `activo` falso y nunca se borra.
- `acceso.docente_seccion` asigna una sección a un profesor una sola vez (`uq_docente_seccion`) y solo con una sección que existe en `abet.seccion` (`fk_docente_seccion_seccion`).
- `acceso.credencial` guarda el hash Argon2id de la contraseña, `acceso.sesion` el hash del token, el usuario, `creada_en` y `expira_en`, y `acceso.codigo_acceso` el hash del código del corte 2 (BR-ACCESO-09). `acceso.intento_fallido` guarda de cada intento fallido `hash_cuenta`, el hash del correo normalizado con el secreto de la aplicación, y nunca el correo. Ese hash es un código de autenticación de mensajes basado en hash (hash-based message authentication code, HMAC), como fija BR-ACCESO-05. Ninguna tabla guarda una contraseña, un token ni un código en claro.
- `abet.carga.subida_por` apunta a `acceso.usuario_autorizado` (`fk_carga_subida_por`) y queda nulo en las cargas anteriores a V1_09.
- `db/datos/periodo_2026_2_inventado.sql` registra activos a `coordinacion@example.invalid` con el rol COORDINADOR y a `docente410@example.invalid` y `docente411@example.invalid` con el rol PROFESOR (valor provisional de D-13). Asigna la 410 de 450002 en 2026-2 a `docente410@example.invalid` y la 411 a `docente411@example.invalid`, no asigna secciones al coordinador y no crea credenciales.
- Q04 devuelve 0 filas, y la consulta Q15 (propuesta), que aplica el filtro de Q04 al esquema `acceso`, devuelve solo la columna del correo de `acceso.usuario_autorizado`.
- **Fuente**: US-04, FR-003, FR-006, D-13, Principio II de la constitución y plan.md (Complexity Tracking).
- **Prueba** (`base_neon.feature`): «V1_09 crea el esquema acceso y los motivos nuevos», «Las cargas anteriores a V1_09 conservan subida_por nulo», «El script de datos registra a los usuarios de prueba y sus secciones», «La base rechaza un registro de acceso inválido» y «Los correos solo viven en acceso.usuario_autorizado».

### BR-ACCESO-02: Contraseña asignada con hash Argon2id
- En el corte 1 el usuario entra con la contraseña que le asigna el administrador técnico (J-03). El comando `scripts/asignar_clave.py` (propuesta) lee la contraseña por la entrada estándar sin mostrarla y guarda en `acceso.credencial` solo su hash Argon2id, que empieza por «$argon2id$» (`ck_credencial_hash`).
- El comando corre con la conexión directa del dueño de la base y no con `abet_app` (propuesta), y el texto de la contraseña no aparece en ninguna fila de `acceso`, en la salida del comando ni en un archivo del repositorio.
- **Fuente**: US-05 (escenario 7), FR-009, J-03 y T036.
- **Prueba**: «El administrador técnico asigna una contraseña por comando».

### BR-ACCESO-03: Ingreso y cookie abet_sesion
- `POST /api/sesion` recibe un cuerpo JSON (JavaScript Object Notation) con `correo` y `contrasena`, normaliza el correo sin espacios y en minúscula y compara la contraseña con el hash Argon2id de `acceso.credencial`. Así, « Docente410@EXAMPLE.invalid » entra como `docente410@example.invalid`.
- Con credenciales correctas responde 200 con el correo normalizado y el rol, como `{ "correo": "docente410@example.invalid", "rol": "PROFESOR" }`, y fija la cookie `abet_sesion` con HttpOnly, Secure, SameSite=Lax y Max-Age 43200, que son 12 horas, sin atributo Domain. `Path=/` es (propuesta).
- El valor de la cookie es un token aleatorio. `acceso.sesion` gana 1 fila con el SHA-256 (Secure Hash Algorithm de 256 bits) del token en hexadecimal (`ck_sesion_token` y `uq_sesion_token`), nunca con el token. `abet_app` inserta solo `usuario_id` y `hash_token`, y la base pone `creada_en` y `expira_en`, que queda 12 horas después (`ck_sesion_vigencia`).
- El cuerpo de ninguna respuesta trae el token, y el registro de la aplicación no guarda la contraseña ni el valor de la cookie, porque ninguna credencial entra a los registros (Principio II de la constitución).
- La sesión viaja solo en la cookie y nunca en `localStorage`. La cookie es de primera parte porque el `vercel.json` del Front reescribe `/api/:path*` hacia el Back.
- **Fuente**: US-05, FR-009, FR-023, Principios II y VI de la constitución y ADR-004 del Front.
- **Prueba**: «Un usuario autorizado entra con su contraseña» y «El correo se compara sin espacios ni mayúsculas»; en el piloto, «La cookie de sesión es de primera parte y nunca pasa por el almacenamiento del navegador» (`despliegue.feature`).

### BR-ACCESO-04: Un solo 401 para todo intento fallido
- Un correo desconocido, un usuario sin contraseña, un usuario inactivo y una contraseña errada reciben el mismo 401 con `{ "detail": "Correo o contraseña incorrectos." }`, sin la cabecera Set-Cookie y sin fila nueva en `acceso.sesion`, para no revelar quién está autorizado.
- **Fuente**: US-05 (escenarios 2 y 3), FR-009 y Principio VI de la constitución.
- **Prueba**: «Un intento fallido no revela si el correo está autorizado» y «Un usuario dado de baja deja de entrar».

### BR-ACCESO-05: Límite de intentos de ingreso
- Cinco intentos fallidos seguidos de un mismo correo en 15 minutos hacen que el sexto responda 429 con `{ "detail": "Demasiados intentos. Espere 15 minutos." }` aunque traiga la contraseña correcta, sin crear sesión, y el límite no bloquea a otro correo (valores provisionales, propuesta).
- La cuenta vive en la base, porque las funciones de Vercel no comparten memoria entre peticiones. Cada intento fallido suma una fila a `acceso.intento_fallido` con `hash_cuenta`, el hash del correo normalizado con el secreto de la aplicación, y la base pone `intentado_en`. Este hash es el HMAC con SHA-256 del correo normalizado como en BR-ACCESO-03, en hexadecimal minúscula (`ck_intento_fallido_hash`). `abet_app` lee la tabla e inserta solo `hash_cuenta`, y el índice `ix_intento_fallido_cuenta` sostiene el conteo por hash y hora.
- La cuenta no depende de que el correo esté registrado, porque la tabla no tiene clave foránea hacia `acceso.usuario_autorizado`. Un correo desconocido, un usuario sin contraseña, un usuario inactivo y una contraseña errada suman un intento fallido, y con 5 intentos fallidos del mismo hash en los últimos 15 minutos la API responde este 429 a cualquiera de ellos. Así, el sexto intento tampoco distingue un correo registrado de uno que no lo está (BR-ACCESO-04).
- Para un usuario que existe, los intentos fallidos anteriores a su último ingreso correcto, que es su `acceso.sesion.creada_en` más reciente, no cuentan. De este modo la serie de intentos fallidos seguidos vuelve a empezar sin UPDATE ni DELETE, porque `abet_app` no actualiza `acceso.credencial` ni borra filas (US-02), y el dueño de la base retira las filas viejas cuando haga falta.
- La clave del HMAC se deriva de `SESION_SECRETO` con la etiqueta «acceso.intento_fallido» (propuesta), y la tabla nunca guarda el correo tecleado.
- **Fuente**: US-05 (escenario 4), FR-009, ADR-004 del Front (invariante 5), `ck_intento_fallido_hash` e `ix_intento_fallido_cuenta`.
- **Prueba**: «Cinco intentos fallidos bloquean el correo por 15 minutos».

### BR-ACCESO-06: Sesión vigente leída de la base en cada petición
- Toda ruta salvo `POST /api/sesion`, `DELETE /api/sesion` y, en el corte 2, `POST /api/sesion/codigo` lee la cookie, busca en `acceso.sesion` una fila vigente de un usuario activo y lee su rol y sus secciones desde la base. Sin cookie, con la sesión vencida o con el usuario inactivo responde 401, sin datos y sin escribir en `archivo_origen` ni en `carga`.
- `GET /api/sesion` responde 200 con el correo y el rol del usuario.
- `DELETE /api/sesion` con la cookie de una sesión vigente responde 204, devuelve la cookie con Max-Age 0 y adelanta el vencimiento de la fila a la hora del cierre, sin borrarla, porque `abet_app` no borra (US-02). El cierre es un UPDATE que fija `expira_en` en `least(expira_en, clock_timestamp())`, el único que el rol puede hacer en `acceso`. El `least()` deja igual una sesión ya vencida, porque una hora posterior a `creada_en` más 12 horas viola `ck_sesion_vigencia`. Después, la cookie anterior recibe 401. Sin sesión también responde 204, para que cerrar sesión nunca falle (propuesta).
- El 401 de una ruta con la sesión vencida trae «La sesión venció. Ingrese otra vez.» (propuesta).
- **Fuente**: US-05 (escenarios 3, 5 y 6), US-06 (escenario 6), FR-009, FR-010 y Principio VI de la constitución.
- **Prueba**: «Cerrar la sesión vence la cookie y la fila», «Una sesión vencida no da acceso», «Un usuario dado de baja deja de entrar», «Sin sesión ninguna ruta de datos responde» y «Sin sesión no hay lista».

### BR-ACCESO-07: Visibilidad por acceso.docente_seccion
- Los de arriba ven hacia abajo y los de abajo no ven hacia arriba. El profesor ve solo las secciones que `acceso.docente_seccion` le asigna, y el coordinador ve todas las de la carrera sin filas propias en `acceso.docente_seccion`.
- La regla tiene un solo dueño, `app/permisos.py`, que usan las rutas de secciones, cargas, constancia y R-17, el reporte de medición de la sección, y en el corte 2 la lista de cargas, que parte de las mismas secciones visibles (BR-CARGA-20). Las demás specs vivas solo repiten el caso de su propia ruta.
- En el producto mínimo viable (minimum viable product, MVP), con una sola carrera, las secciones de la carrera son las del periodo cuyas asignaturas están en el catálogo vigente de Ambiental (propuesta).
- **Fuente**: US-06, FR-010, J-02 y Principio VI de la constitución.
- **Prueba**: «El profesor ve únicamente su sección» y «El coordinador ve todas las secciones de la carrera»; con un profesor que dicta tres secciones de dos asignaturas, «El profesor de varias secciones ve sus tres secciones y ninguna otra» (`varias_secciones.feature`).
- **Cambio del 2026-11-18 (spec 004, US-38 y US-44).** `GET /api/resultados`, la ruta 12 del contrato, aplica esta misma regla con `secciones_visibles()` y sin una condición de alcance propia. El profesor ve los logros solo de sus secciones y el coordinador los de todas las de la carrera, sin filas propias en `acceso.docente_seccion` (BR-RESULTADOS-02 y BR-RESULTADOS-10). **Prueba**: «El reporte del profesor de varias secciones no trae las de otros profesores», «Cada profesor de una sección ve solo la suya» y «El alcance se lee de la base en cada petición» (`specs/004-reportes-docente/aceptacion/alcance_y_privacidad.feature`), y «El coordinador ve las cinco secciones del periodo» (`specs/004-reportes-docente/aceptacion/resultados.feature`).

### BR-ACCESO-08: Un solo 403 para lo que no está a cargo del usuario
- Una ruta de sección, de carga, de constancia o del R-17 fuera del alcance del usuario responde 403 con `{ "detail": "La sección no está a su cargo." }`, sin datos de esa sección ni de su carga y sin escribir en `archivo_origen`, `carga` ni `estudiante`.
- En el corte 1 solo sube el profesor asignado, así que el coordinador recibe ese 403 al subir un export, aunque recibe 200 en las rutas de lectura (secciones, constancia y R-17) de cualquier sección de la carrera. En el corte 2 la subida de una carga nueva sigue igual, y `app/permisos.puede_reemplazar()` deja reemplazar al profesor en sus secciones y al coordinador en cualquiera de la carrera (valor provisional de D-11, BR-CARGA-19). Un profesor que pide el reemplazo en una sección ajena recibe ese mismo 403, y la lista de cargas con el `seccion_id` de una sección ajena también (BR-CARGA-20).
- Conocer un identificador ajeno solo produce 403, porque la API comprueba el alcance en cada petición. Una sección o una carga que no existe recibe el mismo 403 (propuesta), y la decisión sigue abierta en la sección 9 de `docs/03-api/contrato.md` del Front.
- **Fuente**: US-06 (escenarios 4 y 8), US-07 (escenarios 6 y 7), US-15 (escenario 4), US-16 (escenario 6), FR-010, SC-009 y D-11.
- **Prueba**: «El profesor no alcanza una sección ajena escribiendo la ruta» (`acceso.feature`), «Un profesor no sube a una sección que no tiene asignada» y «El coordinador no sube en el corte 1» (`carga.feature`), «El R-17 de la 410 según quién lo pide» y «La constancia de la 410 según quién la pide» (`r17_constancia.feature`) y «El profesor de varias secciones no alcanza una sección que no dicta» (`varias_secciones.feature`); en el corte 2, «El profesor no reemplaza la carga de otra sección», el ejemplo del coordinador de «El export corregido reemplaza a la carga con el error» y «El profesor ve solo las cargas de su sección» (`reemplazo_y_cargas.feature`).
- **Cambio del 2026-11-18 (spec 004, US-38).** La ruta 12 no recibe identificadores de sección ni de carga (J-23), así que no tiene un 403 propio, y un `seccion_id` en su consulta deja la respuesta igual (BR-RESULTADOS-01). BR-ACCESO-10 exige este mismo 403 en cada ruta que recibe un identificador, con una prueba que las recorre todas. **Prueba**: «Un seccion_id en la consulta no abre otra sección» y «Ninguna ruta con datos responde sin sesión» (`specs/004-reportes-docente/aceptacion/alcance_y_privacidad.feature`).

### BR-ACCESO-09: Código de acceso por correo (corte 2)
- `POST /api/sesion/codigo` responde 202 con `{ "detail": "Si el correo está autorizado, recibirá un código en unos minutos." }` exista o no el correo, esté activo o no y aunque no tenga la forma de un correo, y solo envía el código a un usuario autorizado y activo.
- El código tiene 6 dígitos, vale 10 minutos, sirve una sola vez y admite 5 intentos (`ck_codigo_acceso_vigencia` y `ck_codigo_acceso_intentos`), y `acceso.codigo_acceso` guarda solo su hash (valores provisionales).
- El código se verifica en `POST /api/sesion` con el correo y el código (propuesta) y abre la sesión de BR-ACCESO-03. Un código vencido, usado o con 5 intentos fallidos responde 401 con «El código venció. Pida uno nuevo.», «El código ya se usó. Pida uno nuevo.» o «El código ya no es válido. Pida uno nuevo.».
- Más de 3 pedidos de un correo en 15 minutos reciben la misma respuesta 202 y no envían otro mensaje (propuesta).
- El proveedor de correo es Resend en el piloto, con dominio propio y los registros de autenticación del correo SPF, DKIM y DMARC (J-04), y las pruebas usan su modo de prueba, que guarda los mensajes en un buzón de prueba sin enviarlos (propuesta).
- **Fuente**: US-20, FR-027 y J-04.
- **Prueba**: «Un usuario autorizado recibe su código», «La respuesta es la misma exista o no el correo», «El código vigente abre la sesión», «Un código que ya no sirve no abre sesión» y «Pedir códigos en ráfaga no llena el buzón».

### BR-ACCESO-10: Ninguna ruta con datos responde sin sesión (spec 004)
- Todo router de `app/rutas/` con datos declara la dependencia de sesión en `APIRouter(dependencies=[Depends(sesion.usuario_actual)])`, así que una ruta nueva de ese router no puede olvidarla. Hoy son los routers de `secciones`, `cargas` y `resultados`. El de `sesion` la declara ruta por ruta, porque sirve también las rutas públicas.
- La lista cerrada de rutas públicas es `POST /api/sesion`, `DELETE /api/sesion`, `POST /api/sesion/codigo` cuando exista y `GET /api/openapi.json`. La API no publica `/docs` ni `/redoc`, porque `app/main.py` deja `docs_url` y `redoc_url` en `None`.
- `tests/test_rutas_protegidas.py` recorre las rutas registradas en la aplicación y exige 401 sin cookie en cada una fuera de esa lista, también en `GET /api/resultados`. En cada ruta que recibe un `seccion_id` o un `carga_id` por el camino o por la consulta, exige además el 403 de BR-ACCESO-08 con «La sección no está a su cargo.» cuando `docente411@example.invalid` le pasa uno de la sección 410 de 450002.
- Una ruta nueva con un identificador que la prueba no sabe armar la hace fallar, de modo que nadie suma una ruta sin decidir su caso 403. El 403 de un identificador que no existe sigue siendo la propuesta de BR-ACCESO-08.
- **Fuente**: US-38 de la spec 004, FR-003, J-25 y el riesgo 1 del crítico de arquitectura (`specs/004-reportes-docente/revision-historias.md`).
- **Prueba**: «Ninguna ruta con datos responde sin sesión» (`specs/004-reportes-docente/aceptacion/alcance_y_privacidad.feature`), y en `tests/test_rutas_protegidas.py` la comprobación de que cada router con datos declara la dependencia.

## Verification

Corrida del 2026-10-30 en el Back, rama `feat/001-mvp-carga-r17`, sobre un PostgreSQL 16 desechable que arma la propia suite. La más reciente va primero y cada línea lleva la fecha, el comando, el archivo de prueba y las reglas que cubre.

```text
- 2026-11-18 · uv run --frozen --no-build pytest -q -p no:cacheprovider · test_alcance_resultados_feature.py, test_resultados_feature.py, test_rutas_protegidas.py, test_api_resultados.py → BR-ACCESO-07, BR-ACCESO-08 y BR-ACCESO-10 con la ruta 12 (spec 004)
- 2026-11-17 · uv run --frozen --no-build pytest -q -p no:cacheprovider · test_reemplazo_y_cargas_feature.py, test_permisos.py, test_api_cargas.py → BR-ACCESO-07 y BR-ACCESO-08 en el corte 2 (reemplazo y lista de cargas)
- 2026-10-30 · uv run --frozen pytest -q tests/aceptacion -rA · test_acceso_feature.py, test_base_neon_feature.py, test_carga_feature.py, test_r17_constancia_feature.py, test_varias_secciones_feature.py → BR-ACCESO-01 a BR-ACCESO-08
- 2026-10-30 · uv run --frozen pytest -q tests -rA · test_api_cargas.py, test_api_secciones.py, test_api_sesion.py, test_comando.py, test_permisos.py, test_varias_secciones.py → BR-ACCESO-02 a BR-ACCESO-08
```

Resultado del 2026-11-18 (spec 004, rama `feat/004-reportes-docente`, PostgreSQL 18 desechable): suite completa, 1440 passed y 15 skipped in 156.81s (0:02:36); BR-ACCESO-10 y los cambios de BR-ACCESO-07 y BR-ACCESO-08 con sus escenarios aprobados, y el detalle por historia en `specs/004-reportes-docente/audit.md`.

Resultado del 2026-11-17 (corte 2, rama `feat/001-corte-2`, PostgreSQL 18 desechable): suite completa, 1289 passed y 15 skipped in 141.47s (0:02:21); aceptación, 300 passed y 14 skipped, con los 9 casos de US-20 omitidos por T018; el detalle por historia está en la sección «Corte 2» de `specs/001-mvp-carga-r17/audit.md`.

Resultado: aceptación, 170 passed, 19 skipped in 116.97s (0:01:56); suite completa, 852 passed, 20 skipped in 241.50s (0:04:01). Las pantallas P1 a P4 tienen sus pruebas en el Front (`npm test`, 8 archivos y 76 pruebas aprobadas), que `audit.md` lista por grupo.

### Resultado por regla

Las columnas de escenarios cuentan los del corte 1 que la regla cita en su **Prueba**. Un escenario omitido o pendiente se nombra en `audit.md`, que lista su razón.

| Regla | Escenarios (aprobados, omitidos, pendientes) | Pruebas unitarias aprobadas | Resultado |
| --- | --- | --- | --- |
| BR-ACCESO-01 | 5, 0, 0 | 0 | Aprobada |
| BR-ACCESO-02 | 1, 0, 0 | 3 | Aprobada |
| BR-ACCESO-03 | 2, 0, 1 | 3 | Aprobada en local; 1 pendiente (ver audit.md) |
| BR-ACCESO-04 | 2, 0, 0 | 5 | Aprobada |
| BR-ACCESO-05 | 1, 0, 0 | 8 | Aprobada |
| BR-ACCESO-06 | 5, 0, 0 | 10 | Aprobada |
| BR-ACCESO-07 | 3, 0, 0 | 17 | Aprobada |
| BR-ACCESO-08 | 6, 0, 0 | 23 | Aprobada |
| BR-ACCESO-09 | 0, 5, 0 | 0 | Corte 2, pendiente de T018, T083 y T086 |
| BR-ACCESO-10 | 1, 0, 0 | 7 | Aprobada el 2026-11-18 (spec 004) |

Con la spec 004, BR-ACCESO-07 suma «El reporte del profesor de varias secciones no trae las de otros profesores», «Cada profesor de una sección ve solo la suya», «El alcance se lee de la base en cada petición» y «El coordinador ve las cinco secciones del periodo», y BR-ACCESO-08 suma «Un seccion_id en la consulta no abre otra sección» y «Ninguna ruta con datos responde sin sesión», todos aprobados el 2026-11-18.

En el corte 2, BR-ACCESO-07 y BR-ACCESO-08 suman los escenarios «El profesor no reemplaza la carga de otra sección», «El export corregido reemplaza a la carga con el error» (ejemplo del coordinador) y «El profesor ve solo las cargas de su sección», aprobados el 2026-11-17, y las pruebas de `puede_reemplazar()` de `test_permisos.py` (8), también aprobadas.
