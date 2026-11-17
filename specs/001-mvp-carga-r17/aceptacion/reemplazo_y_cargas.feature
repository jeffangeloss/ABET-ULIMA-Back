# language: es
#
# Escenarios de aceptación de US-18 y US-19 (corte 2) de la spec 001-mvp-carga-r17.
# US-18 parte de las candidatas C-22 y C-23 con la partición y la fusión de la auditoría de tamaño
# (el cierre por fecha queda después del MVP) y con las correcciones de la auditoría de
# verificabilidad (dos filas de rechazo en la carga con error, reemplazo fallido con
# reemplaza_carga_id nulo desde el INSERT). US-19 une las candidatas C-20 y C-24.
# Los identificadores de carga se capturan de la respuesta de la API y se nombran A, B, C y D,
# porque una transacción deshecha también consume números de la secuencia.
# El export inventado de la 411 usa los códigos 99000012 a 99000022, para que Q08 siga en 0 filas.
# Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide quien apruebe la spec.

Característica: Reemplazo de cargas publicadas y lista de cargas al alcance del usuario

  Una carga publicada con un error se corrige con otra carga que la reemplaza en la misma sección,
  sin borrar nada, y cada usuario ve las cargas que su rol alcanza con su estado, sus filas y quién
  las sube.

  Antecedentes:
    Dado la base con los datos inventados de 2026-2 de periodo_2026_2_inventado.sql
    Y "coordinacion@example.invalid" activo con rol "COORDINADOR" y sin secciones en acceso.docente_seccion
    Y "docente410@example.invalid" activo con rol "PROFESOR" y la sección 410 de 450002 en 2026-2
    Y "docente411@example.invalid" activo con rol "PROFESOR" y la sección 411 de 450002 en 2026-2
    Y la API configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y los exports de prueba en tests/datos_inventados/

  # US-18: Reemplazar la carga publicada de una sección
  # El reemplazo va en una sola transacción. La carga nueva entra EN_CURSO, la anterior pasa a
  # REEMPLAZADA y la nueva pasa a PUBLICADA. El rol abet_app no borra filas.

  @US-18 @corte2
  Esquema del escenario: El export corregido reemplaza a la carga con el error
    Dado la carga A PUBLICADA de "export_inventado_410_con_error.xlsx" en la sección 410 con 11 filas leídas, 10 aceptadas, 1 rechazada y 30 mediciones
    Y que "<usuario>" tiene la sesión iniciada
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={A} con el archivo "sintetico_20262_450002_410.xlsx"
    Entonces la API responde 201 con la constancia de una carga B en estado "PUBLICADA"
    Y la carga A queda en estado "REEMPLAZADA" y conserva sus 30 mediciones y sus 2 filas de abet.rechazo_fila, NIVEL_FUERA_DE_ESCALA en la fila 3 del PI 5.2 y PUNTAJE_MAXIMO_DISTINTO en el PI 5.3
    Y la carga B tiene filas_leidas 11, filas_aceptadas 11, filas_rechazadas 0, 33 mediciones y reemplaza_carga_id igual a A
    Y la carga B tiene subida_por igual al usuario_id de "<usuario>"
    Y la sección 410 tiene 1 sola carga en estado "PUBLICADA"
    Y abet.v_r17_por_pi devuelve solo filas de la carga B, con 63,6 en el PI 5.1, 63,6 en el PI 5.2 y 72,7 en el PI 5.3
    Y cada una de las consultas de control Q06, Q07, Q10 y Q14 devuelve 0 filas

    Ejemplos:
      | usuario                      |
      | docente410@example.invalid   |
      | coordinacion@example.invalid |

  @US-18 @corte2
  Escenario: Subir sin pedir el reemplazo no pisa la carga publicada
    Dado la carga A PUBLICADA de "export_inventado_410_con_error.xlsx" en la sección 410
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía POST /api/secciones/{sección 410}/cargas sin el parámetro reemplaza, con el archivo "sintetico_20262_450002_410.xlsx"
    Entonces la API responde 409
    Y abet.archivo_origen y abet.carga no ganan ninguna fila
    Y la carga A sigue en estado "PUBLICADA"
    Y la pantalla P3 pregunta "La sección 410 ya tiene una carga publicada. ¿Desea reemplazarla?"

  @US-18 @corte2
  Escenario: Un reemplazo con un archivo ilegible no cambia nada
    Dado la carga A PUBLICADA de "export_inventado_410_con_error.xlsx" en la sección 410
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={A} con un archivo .xlsx dañado que no abre como zip
    Entonces la API responde 422
    Y abet.archivo_origen y abet.carga no ganan ninguna fila
    Y la carga A sigue en estado "PUBLICADA"
    Y la pantalla P3 muestra "No se pudo abrir el archivo. La carga publicada no cambió."

  @US-18 @corte2
  Escenario: Un reemplazo que rechaza todas las filas no quita la carga vigente
    Dado la carga A PUBLICADA de "sintetico_20262_450002_410.xlsx" en la sección 410
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={A} con un export de la 410 que trae un 5 en la columna 5.2 de las 11 filas
    Entonces la API responde 201 con la constancia de una carga en estado "RECHAZADA"
    Y esa carga tiene filas_leidas 11, filas_aceptadas 0 y filas_rechazadas 11
    Y su reemplaza_carga_id es nulo desde el INSERT, sin ningún UPDATE de esa columna
    Y la carga A sigue en estado "PUBLICADA"

  @US-18 @corte2
  Escenario: Un reemplazo fallido no bloquea el siguiente
    Dado la carga A PUBLICADA de "export_inventado_410_con_error.xlsx" en la sección 410
    Y una carga RECHAZADA de un reemplazo fallido de A, con reemplaza_carga_id nulo
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={A} con el archivo "sintetico_20262_450002_410.xlsx"
    Entonces la API responde 201 con una carga en estado "PUBLICADA" y reemplaza_carga_id igual a A
    Y la base no rechaza esa carga por "uq_carga_reemplaza"
    Y las consultas de control Q07 y Q14 devuelven 0 filas

  # (propuesta) El texto del aviso. El mismo archivo de la carga vigente no abre otra carga.
  @US-18 @corte2
  Escenario: El mismo archivo de la carga publicada no la reemplaza
    Dado la carga A PUBLICADA de "sintetico_20262_450002_410.xlsx" en la sección 410
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={A} con el archivo "sintetico_20262_450002_410.xlsx"
    Entonces la API responde 200 con la constancia de la carga A
    Y el cuerpo trae el aviso "Es el mismo archivo de la carga publicada. No se reemplazó."
    Y abet.archivo_origen y abet.carga no ganan ninguna fila
    Y la carga A sigue en estado "PUBLICADA"

  @US-18 @corte2
  Escenario: Volver al export anterior reutiliza su archivo
    Dado la carga A REEMPLAZADA de "sintetico_20262_450002_410.xlsx" y la carga B PUBLICADA de "export_inventado_410_con_error.xlsx" que la reemplaza en la sección 410
    Y que "coordinacion@example.invalid" tiene la sesión iniciada
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={B} con el archivo "sintetico_20262_450002_410.xlsx"
    Entonces la API responde 201 con una carga C en estado "PUBLICADA", el mismo archivo_id de la carga A y reemplaza_carga_id igual a B
    Y abet.archivo_origen sigue con 1 sola fila para la huella de "sintetico_20262_450002_410.xlsx"
    Y la carga A sigue en estado "REEMPLAZADA" y la carga B pasa a "REEMPLAZADA"

  # (propuesta) El reemplazo apunta siempre a la carga PUBLICADA vigente de la sección.
  @US-18 @corte2
  Escenario: No se reemplaza una carga que ya no es la vigente
    Dado la carga A REEMPLAZADA y la carga B PUBLICADA que la reemplaza en la sección 410
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía POST /api/secciones/{sección 410}/cargas?reemplaza={A} con el archivo "sintetico_20262_450002_410.xlsx"
    Entonces la API responde 409
    Y abet.carga no gana ninguna fila
    Y la carga B sigue en estado "PUBLICADA"

  @US-18 @corte2
  Escenario: El profesor no reemplaza la carga de otra sección
    Dado la carga D PUBLICADA del export inventado de la 411 en la sección 411, subida por "docente411@example.invalid"
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía POST /api/secciones/{sección 411}/cargas?reemplaza={D} con un export de la 411
    Entonces la API responde 403
    Y abet.carga no gana ninguna fila
    Y la carga D sigue en estado "PUBLICADA"

  @US-18 @corte2
  Escenario: La base impide dos cargas publicadas en la misma sección
    Dado la carga A PUBLICADA en la sección 410
    Y una transacción abierta que inserta una carga B EN_CURSO de la misma sección con reemplaza_carga_id igual a A
    Cuando un programa defectuoso intenta pasar B a "PUBLICADA" en esa transacción sin marcar antes A como "REEMPLAZADA"
    Entonces la base rechaza el cambio por "uq_carga_publicada_por_seccion"
    Y la transacción completa se deshace, así que B no existe y A sigue "PUBLICADA"

  @US-18 @corte2
  Escenario: La base no deja que una carga reemplace a otra de otra sección
    Dado la carga D PUBLICADA de la sección 411 de 450002 en 2026-2
    Cuando la aplicación intenta registrar una carga de la sección 410 con reemplaza_carga_id igual a D
    Entonces la base rechaza la fila por la restricción "fk_carga_reemplaza"

  # US-19: Ver las cargas a mi alcance
  # (propuesta) GET /api/cargas sin seccion_id devuelve las cargas al alcance del usuario del periodo vigente,
  # de la más reciente a la más antigua, con las horas en America/Lima (UTC-05:00), y el R-17 de una
  # carga que no está PUBLICADA responde 409.

  @US-19 @corte2
  Escenario: El coordinador ve las cargas de todas las secciones
    Dado que la sección 410 tiene estas cargas, subidas por "docente410@example.invalid" en este orden
      | carga | archivo                             | estado      | leídas | aceptadas | rechazadas |
      | A     | export_inventado_411.xlsx           | RECHAZADA   | 0      | 0         | 0          |
      | B     | export_inventado_410_con_error.xlsx | REEMPLAZADA | 11     | 10        | 1          |
      | C     | sintetico_20262_450002_410.xlsx     | PUBLICADA   | 11     | 11        | 0          |
    Y que la sección 411 tiene la carga D PUBLICADA del export inventado de la 411, subida por "docente411@example.invalid" después de C
    Y que "coordinacion@example.invalid" tiene la sesión iniciada
    Cuando se envía GET /api/cargas
    Entonces la API responde 200 con 4 cargas en el orden D, C, B y A
    Y cada carga trae su sección, su estado, filas_leidas, filas_aceptadas, filas_rechazadas, el nombre del archivo, los primeros 12 caracteres de la huella y el correo de quien la sube
    Y la carga A trae el motivo "SECCION_NO_COINCIDE"
    Y la carga C indica que reemplaza a la carga B
    Y iniciada_en y terminada_en de cada carga vienen con el desfase "-05:00"

  @US-19 @corte2
  Escenario: El coordinador filtra por sección
    Dado las cargas A, B y C de la sección 410 y la carga D de la sección 411
    Y que "coordinacion@example.invalid" tiene la sesión iniciada
    Cuando se envía GET /api/cargas?seccion_id={sección 411}
    Entonces la API responde 200 con solo la carga D

  @US-19 @corte2
  Escenario: El profesor ve solo las cargas de su sección
    Dado las cargas A, B y C de la sección 410 y la carga D de la sección 411
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía GET /api/cargas
    Entonces la API responde 200 con las cargas C, B y A
    Y la respuesta no trae la carga D ni ningún dato de la sección 411
    Pero GET /api/cargas?seccion_id={sección 411} responde 403

  @US-19 @corte2
  Escenario: La constancia de una carga reemplazada sigue disponible
    Dado las cargas A, B y C de la sección 410
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía GET /api/cargas/{B}
    Entonces la API responde 200 con el estado "REEMPLAZADA", filas_leidas 11, filas_aceptadas 10 y filas_rechazadas 1
    Y la constancia lista el rechazo de la fila 3 en el PI 5.2 con el motivo "NIVEL_FUERA_DE_ESCALA" y el efecto "RECHAZA_FILA"
    Y la constancia indica que la carga C reemplaza a la carga B
    Pero GET /api/cargas/{B}/r17.xlsx responde 409 y no entrega ningún archivo

  @US-19 @corte2
  Escenario: La lista no expone datos que la base no guarda
    Dado las cargas A, B y C de la sección 410
    Y que "docente410@example.invalid" tiene la sesión iniciada
    Cuando se envía GET /api/cargas y se abre la pantalla P5 «Cargas»
    Entonces ningún valor de las columnas Last Name ni First Name de los exports de prueba aparece en la respuesta ni en la pantalla
    Y ningún nombre de archivo de la respuesta contiene "/" ni "\"
    Y la respuesta no trae ningún valor leído de una celda de PI
