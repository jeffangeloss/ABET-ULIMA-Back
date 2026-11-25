# language: es
#
# Escenarios de aceptación de los resultados del profesor por resultado del estudiante (student outcome,
# SO), de las historias de usuario (user stories, US) US-37, US-39, US-40, US-41, US-43 y US-44 de la spec
# 004-reportes-docente. Jefferson pide el 2026-11-17 que el profesor vea «de forma visual con reportes como
# le ha ido a él frente a los SO», solo en sus secciones (spec.md, Input). El límite de acceso y la
# privacidad de la ruta nueva viven en alcance_y_privacidad.feature (US-38 y US-42).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid. Ninguna
# contraseña aparece escrita aquí, porque los scripts de datos no crean credenciales y la prueba asigna al
# azar la contraseña con que abre cada sesión, sin guardarla en el repositorio.
# - db/datos/varias_secciones_2026_2_inventado.sql corre después de periodo_2026_2_inventado.sql, solo en
#   las bases desechables de estas pruebas y nunca en Neon, donde D-09 y D-13 fijan los datos del piloto.
# - Los exports viven en tests/datos_inventados/ y sus cifras salen de NIVELES_410, NIVELES_450002_412,
#   NIVELES_450010_410 y NIVELES_450010_412 de scripts/generar_exports_inventados.py, que
#   tests/datos_inventados/README.md resume por sección y por indicador de desempeño (performance
#   indicator, PI).
# - Las copias con celdas vacías se arman en tmp_path con REGLAS_DE_COPIA de
#   tests/aceptacion/pasos/conftest.py. La regla «con la columna X.Y vacía en sus N filas» llega con la
#   tarea T012.
#
# Vocabulario de los pasos, el de acceso.feature y varias_secciones.feature.
# - «se envía GET /api/resultados?periodo=2026-2» es la petición a la ruta 12 (J-23) con la cookie
#   abet_sesion de quien tiene la sesión iniciada.
# - «que "docente.varias@example.invalid" tiene publicadas sus tres secciones» sube por la ruta 5, con la
#   sesión de ese profesor, sintetico_20262_450002_412.xlsx a la sección 412 de 450002,
#   sintetico_20262_450010_410.xlsx a la 410 de 450010 y sintetico_20262_450010_412.xlsx a la 412 de
#   450010, cada uno con respuesta 201 y estado PUBLICADA.
# - Un indicador es una fila de la respuesta por sección y PI. Sus campos estudiantes_por_nivel, logrados,
#   calificados, sin_evidencia, total, pct_sobre_calificados, pct_sobre_total, meta_pct y nivel_esperado
#   corresponden a n_nivel_1 a n_nivel_4, n_esperado_o_superior, n_total - n_sin_evidencia,
#   n_sin_evidencia, n_total, pct_logro_sobre_calificados, pct_logro_sobre_total_con_sin_evidencia,
#   meta_logro_pct y nivel_esperado de abet.v_r17_por_pi. en_meta es verdadero si pct_sobre_calificados es
#   mayor o igual que meta_pct, falso si es menor y nulo si falta alguno de los dos.
# - «81,8 % (9 de 11)» es pct_sobre_calificados 81.8 con logrados 9 y calificados 11.
# - Una sección se nombra con su número y su asignatura, porque la 412 existe en 450002 y en 450010. «la
#   sección 410» sin asignatura es la de 450002, como en carga.feature.
# - Cada escenario corre en una base desechable propia, así que los carga_id y los seccion_id salen de la
#   API o de la base y nunca se suponen.
# - @delegado_a_vitest marca un escenario de la pantalla P6 que prueba Vitest en el Front, como en la spec
#   003, y aquí queda como criterio escrito.
# - Lo marcado «(propuesta)» no lo fija ninguna decisión de la spec, que Jefferson aprueba el 2026-11-18 con
#   J-21 a J-28, y lo confirma la revisión del contrato.

Característica: Resultados del profesor por SO, calculados desde la base
  Como profesor de Ingeniería Ambiental, quiero ver en el sistema cómo le va a cada PI de mis secciones
  frente a la meta, agrupado por SO, para saber cómo me va en los SO que mide mi curso, con las mismas
  cifras de mi R-17.

  Antecedentes:
    Dado una base PostgreSQL 18 desechable con las migraciones V1_01 a V1_10, los datos de db/datos/periodo_2026_2_inventado.sql y, después, los de db/datos/varias_secciones_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y plan_medicion registra los PI 5.1, 5.2 y 5.3 para la asignatura "450002" en "2026-2" y los PI 2.1, 2.2 y 5.1 para "450010", con el instrumento "Trabajo Integrador"
    Y acceso.docente_seccion asigna la sección 410 de "450002" a "docente410@example.invalid", la 411 de "450002" a "docente411@example.invalid" y la 412 de "450002" y las secciones 410 y 412 de "450010" a "docente.varias@example.invalid", y no tiene filas de "coordinacion@example.invalid"
    Y ninguna de las cinco secciones de 2026-2 tiene cargas

  # US-37: Ver mis logros por SO en el periodo
  # La ruta 12 y la forma de su respuesta las fijan J-22 y J-23 de spec.md. Las secciones van por código
  # de asignatura y número de sección, y los indicadores por número de SO y número de PI.

  @US-37 @corte1 @spec004
  Escenario: El profesor de varias secciones ve sus logros agrupados por SO
    Dado que "docente.varias@example.invalid" tiene publicadas sus tres secciones
    Y que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces la API responde 200 con 3 secciones y 9 indicadores, cada uno con meta_pct 80.0 e instrumento "Trabajo Integrador"
    Y las secciones llegan en el orden 412 de "450002", 410 de "450010" y 412 de "450010"
    Y "so" trae los SO 2 y 5, en ese orden, cada uno con su descripción de abet.so
    Y el SO 2 reúne 2.1 y 2.2 de la sección 410 de "450010", con 72,7 % (8 de 11) y 45,5 % (5 de 11), y de la sección 412 de "450010", con 90,9 % (10 de 11) y 63,6 % (7 de 11)
    Y el SO 5 reúne 5.1, 5.2 y 5.3 de la sección 412 de "450002", con 81,8 % (9 de 11), 54,5 % (6 de 11) y 90,9 % (10 de 11), y 5.1 de las secciones 410 y 412 de "450010", con 36,4 % (4 de 11) y 54,5 % (6 de 11)
    Y en_meta es verdadero en 3 indicadores, 5.1 y 5.3 de la sección 412 de "450002" y 2.1 de la sección 412 de "450010", y falso en los otros 6
    Y la sección 412 de "450002" y la sección 412 de "450010" traen seccion_id y carga_id distintos, cada una con su propio 5.1

  @US-37 @corte1 @spec004
  Escenario: Las cifras viajan como números de un decimal
    Dado que "docente.varias@example.invalid" tiene publicadas sus tres secciones
    Y que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces el indicador 5.1 de la sección 412 de "450002" trae estudiantes_por_nivel [1, 1, 5, 4], logrados 9, calificados 11, sin_evidencia 0, total 11, nivel_esperado 3, pct_sobre_calificados 81.8, pct_sobre_total 81.8, meta_pct 80.0 y en_meta verdadero
    Y pct_sobre_calificados, pct_sobre_total y meta_pct llegan como números JSON y no como textos

  # La frontera de la meta. «En la meta» es llegar a la meta o superarla, la misma comparación del plan de
  # acción del bloque II del R-17 (abet_carga/r17.py, _plan_de_accion). Sin la nota de la fila 9
  # (99000008, el único estudiante con nivel 1 en 5.3), 5.3 queda en 8 de 10.
  @US-37 @corte1 @spec004
  Escenario: El 80,0 % justo queda en la meta
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en la fila 9 está subida a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces el indicador 5.3 de la sección 410 de "450002" trae logrados 8, calificados 10, sin_evidencia 1, pct_sobre_calificados 80.0 y en_meta verdadero
    Y los indicadores 5.1 y 5.2 traen 63,6 % (7 de 11) y en_meta falso

  @US-37 @corte1 @spec004 @delegado_a_vitest
  Escenario: P6 agrupa los PI por SO y escribe cada cifra
    Dado la respuesta del escenario «El profesor de varias secciones ve sus logros agrupados por SO»
    Cuando "docente.varias@example.invalid" abre la pantalla P6 «Mis logros por SO» (propuesta)
    Entonces P6 muestra un grupo «SO 2» y un grupo «SO 5», cada uno con la descripción del SO, y dentro de cada grupo una fila por PI y sección
    Y cada fila escribe su PI, su sección, su porcentaje, su fracción y su estado, como «5.1 · Sección 412 de 450002 · 81,8 % (9 de 11) · En la meta» (propuesta)
    Y 3 filas dicen «En la meta» (propuesta) y 6 dicen «Debajo de la meta» (propuesta)
    Y la barra de cada fila lleva aria-hidden, su ancho es el porcentaje y la meta se marca con una línea y con el texto «Meta 80 %» (propuesta), de modo que ningún estado depende solo del color

  @US-37 @corte1 @spec004 @delegado_a_vitest
  Escenario: P6 se abre desde P2 y desde P4 sin confundirse con «Ver resultado»
    Dado "docente410@example.invalid" en la pantalla P2 «Mis secciones» con la sección 410 de "450002" PUBLICADA
    Entonces la cabecera muestra una sola vez «Ver mis logros por SO» (propuesta), que abre P6
    Y la fila de la 410 conserva sus botones «Subir export» y «Ver resultado» (propuesta), que abre P4
    Y P4 de la carga de la 410 ofrece también «Ver mis logros por SO» (propuesta)
    Y P6 vuelve a P2 con «Volver» (propuesta)

  # Cambio del 2026-11-24 (spec 005, J-32 y FR-009). El R-17 solo sale con la declaración vigente completa, así que P6
  # ya no lo ofrece y lleva a P4, el único lugar que lo ofrece. El título del escenario no cambia, porque es la clave de
  # las referencias de la spec viva `resultados`, de `test_resultados_feature.py` y de `audit.md`. Su primer «Entonces»
  # decía, hasta el 2026-11-23, «la sección 412 de "450002" ofrece el enlace «Descargar R-17 de la sección 412 de
  # 450002» (propuesta), que apunta a /api/cargas/{carga_id de esa sección}/r17.xlsx». La prueba del Front pasa a
  # llamarse «ofrece Ver la carga solo de cada sección publicada, con el carga_id de su carga, y ningún enlace al R-17».
  @US-37 @corte1 @spec004 @delegado_a_vitest
  Escenario: P6 ofrece el R-17 de cada sección publicada
    Dado una respuesta de GET /api/resultados con la sección 412 de "450002" PUBLICADA y las secciones 410 y 412 de "450010" en "SIN_CARGA"
    Cuando "docente.varias@example.invalid" abre P6
    Entonces la sección 412 de "450002" ofrece el enlace «Ver la carga de la sección 412 de 450002» (propuesta), que abre P4 con el carga_id de esa sección y no ofrece «Descargar R-17»
    Y las secciones 410 y 412 de "450010" no ofrecen ningún enlace de R-17

  # US-39: Distinguir lo que todavía no tiene resultado
  # abet.v_r17_por_pi solo ve cargas PUBLICADAS y deja nulo, y nunca en 0, el porcentaje sobre calificados
  # de un PI sin calificaciones (NULLIF). "so" trae todo SO que mide el plan de alguna sección de la
  # respuesta, aunque esa sección no tenga carga.

  @US-39 @corte1 @spec004
  Escenario: Una sección sin carga publicada no trae cifras
    Dado que "sintetico_20262_450002_412.xlsx" está subido por "docente.varias@example.invalid" a la sección 412 de "450002" con respuesta 201 y su carga_id
    Y que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces la API responde 200 con 3 secciones y 3 indicadores, los de la sección 412 de "450002"
    Y las secciones 410 y 412 de "450010" traen estado "SIN_CARGA", carga_id nulo, pi ["2.1", "2.2", "5.1"] e indicadores vacíos, como el estado de GET /api/secciones
    Y "so" trae los SO 2 y 5, porque el plan de 450010 mide el SO 2 aunque sus secciones no tengan carga

  @US-39 @corte1 @spec004
  Escenario: Una carga rechazada no cuenta como resultado
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que una copia de "sintetico_20262_450002_410.xlsx" sin la columna del PI 5.2 está subida a la sección 410 y su carga está "RECHAZADA" con PI_DEL_PLAN_AUSENTE
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces la API responde 200 con 1 sección, la 410 de "450002", con estado "SIN_CARGA", carga_id nulo e indicadores vacíos

  @US-39 @corte1 @spec004
  Escenario: Un PI sin calificaciones no sale como 0 %
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en sus 11 filas está subida a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces el indicador 5.3 de la sección 410 de "450002" trae estudiantes_por_nivel [0, 0, 0, 0], logrados 0, calificados 0, sin_evidencia 11, total 11, pct_sobre_calificados nulo, pct_sobre_total 0.0 y en_meta nulo
    Y los indicadores 5.1 y 5.2 traen 63,6 % (7 de 11)

  @US-39 @corte1 @spec004
  Escenario: Un estudiante sin evidencia deja dos porcentajes
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.2 vacía en la fila 3 está subida a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces el indicador 5.2 de la sección 410 de "450002" trae estudiantes_por_nivel [1, 3, 3, 3], logrados 6, calificados 10, sin_evidencia 1, total 11, pct_sobre_calificados 60.0, pct_sobre_total 54.5 y en_meta falso
    Y los indicadores 5.1 y 5.3 traen el mismo número en pct_sobre_calificados y en pct_sobre_total, 63.6 y 72.7

  # El profesor de prueba sin secciones lo crea el dueño de la base solo en la base desechable, como un
  # usuario activo de acceso.usuario_autorizado con rol PROFESOR y sin filas en acceso.docente_seccion. El
  # periodo 2026-1 existe en abet.periodo (V1_03) y no tiene secciones.
  @US-39 @corte1 @spec004
  Esquema del escenario: Sin secciones en el periodo, la respuesta es una lista vacía y no un error
    Dado <quien>
    Cuando se envía GET /api/resultados?periodo=<periodo>
    Entonces la API responde 200 con "so" vacío y "secciones" vacío

    Ejemplos:
      | quien                                                                                                                                | periodo |
      | que "docente.sinseccion@example.invalid", activo, con rol "PROFESOR" y sin filas en acceso.docente_seccion, tiene la sesión iniciada | 2026-2  |
      | que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"                                                         | 2026-1  |

  @US-39 @corte1 @spec004 @delegado_a_vitest
  Escenario: P6 no pinta lo que no se mide
    Dado respuestas de GET /api/resultados con una sección en "SIN_CARGA", el 5.3 del escenario «Un PI sin calificaciones no sale como 0 %» y el 5.2 del escenario «Un estudiante sin evidencia deja dos porcentajes»
    Cuando el profesor abre P6
    Entonces la sección en "SIN_CARGA" dice «Sin carga publicada» (propuesta), con los PI de su plan y sin barras
    Y el 5.3 dice «Sin calificaciones (11 sin evidencia)» (propuesta), sin barra y sin ningún «0 %» ni «0,0 %»
    Y el 5.2 dice «60,0 % de los calificados (6 de 10) y 54,5 % del total (6 de 11), 1 sin evidencia» (propuesta)

  @US-39 @corte1 @spec004 @delegado_a_vitest
  Escenario: P6 muestra la espera, el error y la lista vacía
    Dado el profesor con la sesión iniciada que abre P6
    Entonces mientras la API responde, P6 dice «Cargando sus logros…» (propuesta)
    Y con un 401 vuelve a P1 con «La sesión venció. Ingrese otra vez.» (propuesta), como las demás pantallas
    Y sin respuesta del servicio dice «El servicio no respondió. Intente de nuevo.» (propuesta), como el contrato para un 502 o un 504
    Y con "secciones" vacío dice «No tiene secciones asignadas en este periodo.» (propuesta), el mismo texto de P2

  # US-40: Las cifras del reporte son las de mi R-17
  # El bloque II del R-17 escribe el porcentaje y la meta como fracción, 0,818 para 81,8 % (abet_carga/r17.py,
  # _fraccion), así que la comparación multiplica la celda por 100 y la redondea a un decimal. Las filas del
  # bloque II son la 24, la 25 y la 26, y las de las frecuencias la 29, la 30 y la 31, en el orden de los PI.

  @US-40 @corte1 @spec004
  Escenario: Los nueve indicadores coinciden con los tres R-17
    Dado que "docente.varias@example.invalid" tiene publicadas sus tres secciones
    Y que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando se envía GET /api/resultados?periodo=2026-2 y se descarga el R-17 de cada una de las tres cargas
    Entonces en cada indicador pct_sobre_calificados es igual a round(100 × la celda E de su fila del bloque II, 1) y a pct_logro_sobre_calificados de abet.v_r17_por_pi para esa carga y ese PI
    Y meta_pct es igual a round(100 × la celda G de esa fila, 1) y pct_sobre_total es igual a round(100 × la celda Q de su fila de las frecuencias, 1)
    Y en_meta es verdadero si y solo si la celda H de esa fila trae el texto de logro del plan de acción del R-17

  @US-40 @corte1 @spec004
  Escenario: Con un estudiante sin evidencia, el segundo porcentaje también coincide con el R-17
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.2 vacía en la fila 3 está subida a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/resultados?periodo=2026-2 y se descarga el R-17 de esa carga
    Entonces el indicador 5.2 trae pct_sobre_calificados 60.0, igual a round(100 × E25, 1), y pct_sobre_total 54.5, igual a round(100 × Q30, 1)

  @US-40 @corte1 @spec004
  Escenario: Leer el reporte no escribe en la base
    Dado que "docente.varias@example.invalid" tiene publicadas sus tres secciones
    Y que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando se envía GET /api/resultados?periodo=2026-2 cinco veces
    Entonces abet.archivo_origen, abet.carga, abet.medicion, abet.rechazo_fila, acceso.sesion y acceso.intento_fallido conservan su número de filas
    Y las consultas de control Q01 a Q14 devuelven 0 filas

  # Depende de US-18 (reemplazo de la carga publicada) del corte 2 de la spec 001, que está en develop desde
  # el PR #28 del Back, así que el escenario corre con los demás.
  @US-40 @corte2 @spec004
  Escenario: Una carga reemplazada sale del reporte
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "export_inventado_410_con_error.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que esa carga A se reemplaza con "sintetico_20262_450002_410.xlsx" en la carga B, como en US-18
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces la sección 410 de "450002" trae el carga_id de B con 63,6 % (7 de 11), 63,6 % (7 de 11) y 72,7 % (8 de 11)
    Y ningún indicador trae 60,0 % (6 de 10) ni 70,0 % (7 de 10), las cifras de A

  # US-41: El reporte dice cuándo sus resultados son provisionales
  # La marca va por sección, porque cada carga guarda su conjunto de reglas (carga.conjunto_reglas_id), y sus
  # campos son los de la constancia (BR-R17-10). Los conjuntos R-PRUEBA-APROBADO y R-PRUEBA-INCOMPLETO son
  # inventados y solo existen en la base de pruebas. En Neon ningún conjunto se aprueba dentro del MVP.

  @US-41 @corte1 @spec004
  Escenario: Con R-2026-BORRADOR los resultados son provisionales
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces la sección 410 de "450002" trae provisional verdadero, conjunto_reglas "R-2026-BORRADOR", conjunto_reglas_estado "BORRADOR" y parametros_pendientes con CONVERSION_NIVEL_0_1, CORTE_ROJO y TRATO_SIN_EVIDENCIA
    Y sus tres indicadores traen meta_pct 80.0 y nivel_esperado 3

  @US-41 @corte1 @spec004 @reglas_aprobadas_de_prueba
  Escenario: Con reglas aprobadas los resultados salen sin la marca
    Dado que la base tiene el conjunto "R-PRUEBA-APROBADO" de Ambiental en estado "APROBADO" con META_LOGRO 0,70, NIVEL_ESPERADO 2, CORTE_ROJO 0,50, TRATO_SIN_EVIDENCIA "SE_EXCLUYE_DEL_DENOMINADOR" y la conversión de sus 4 niveles, como en el caso A03 de pruebas.sql
    Y la API configurada con CONJUNTO_REGLAS "R-PRUEBA-APROBADO"
    Y que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces la sección 410 de "450002" trae provisional falso y conjunto_reglas_estado "APROBADO"
    Y 5.1, 5.2 y 5.3 traen nivel_esperado 2, logrados 10, calificados 11, pct_sobre_calificados 90.9, meta_pct 70.0 y en_meta verdadero

  # El conjunto aprobado con un parámetro que usa la vista en PENDIENTE es el caso que vigila la consulta de
  # control Q11, que en esta base devuelve 1 fila. El R-17 tiene para él su propio texto de franja
  # (abet_carga/r17.py, _franja).
  @US-41 @corte1 @spec004 @reglas_aprobadas_de_prueba
  Escenario: Un conjunto aprobado que no define todos sus parámetros sigue provisional
    Dado que la base tiene el conjunto "R-PRUEBA-INCOMPLETO" de Ambiental en estado "APROBADO" con META_LOGRO 0,80 y NIVEL_ESPERADO 3 en DEFINIDO y TRATO_SIN_EVIDENCIA en PENDIENTE
    Y la API configurada con CONJUNTO_REGLAS "R-PRUEBA-INCOMPLETO"
    Y que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces la sección 410 de "450002" trae provisional verdadero, conjunto_reglas_estado "APROBADO" y parametros_pendientes con TRATO_SIN_EVIDENCIA
    Y 5.1, 5.2 y 5.3 traen 63,6 % (7 de 11), 63,6 % (7 de 11) y 72,7 % (8 de 11)

  @US-41 @corte1 @spec004 @delegado_a_vitest
  Esquema del escenario: P6 escribe la marca provisional de cada sección
    Dado una sección de GET /api/resultados con provisional <provisional>, conjunto_reglas "<conjunto>" y conjunto_reglas_estado "<estado>"
    Cuando el profesor abre P6
    Entonces esa sección <marca>

    Ejemplos:
      | provisional | conjunto            | estado   | marca                                                                                                                                                                                                  |
      | verdadero   | R-2026-BORRADOR     | BORRADOR | muestra «Resultados provisionales. Las reglas de la carrera (conjunto R-2026-BORRADOR) aún no están aprobadas. No usar como evidencia oficial.» (propuesta)                                             |
      | verdadero   | R-PRUEBA-INCOMPLETO | APROBADO | muestra «Resultados provisionales. El conjunto de reglas R-PRUEBA-INCOMPLETO está aprobado, pero no define todos los parámetros que usan estos resultados. No usar como evidencia oficial.» (propuesta) |
      | falso       | R-PRUEBA-APROBADO   | APROBADO | no muestra ninguna marca provisional                                                                                                                                                                   |

  # US-43: Ver cómo se reparten mis estudiantes por nivel
  # Con R-2026-BORRADOR el nivel esperado es 3, así que logrados suma los niveles 3 y 4.

  @US-43 @corte1 @spec004
  Escenario: El reparto por nivel suma los calificados
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces el indicador 5.1 trae estudiantes_por_nivel [1, 3, 4, 3], el 5.2 trae [1, 3, 4, 3] y el 5.3 trae [1, 2, 5, 3]
    Y en cada indicador la suma de estudiantes_por_nivel es igual a calificados, 11, y la suma de sus dos últimos valores es igual a logrados, 7, 7 y 8

  @US-43 @corte1 @spec004 @delegado_a_vitest
  Escenario: P6 escribe el reparto por nivel
    Dado la respuesta del escenario «El reparto por nivel suma los calificados»
    Cuando "docente410@example.invalid" abre P6
    Entonces la barra apilada de 5.3 dice «Nivel 1: 1, Nivel 2: 2, Nivel 3: 5, Nivel 4: 3» (propuesta) y cada tramo lleva su conteo en texto

  # US-44: El coordinador ve los resultados de todas las secciones de la carrera
  # El coordinador alcanza las secciones del periodo cuya asignatura está en el plan de estudios del
  # catálogo vigente, sin filas propias en acceso.docente_seccion (BR-ACCESO-07). 450002 y 450010 están en
  # abet.plan_estudios de AMB-2026.

  @US-44 @corte1 @spec004
  Escenario: El coordinador ve las cinco secciones del periodo
    Dado que la sección 410 de "450002" tiene una carga PUBLICADA de "sintetico_20262_450002_410.xlsx", subida por "docente410@example.invalid"
    Y que la sección 411 de "450002" tiene una carga PUBLICADA de "export_inventado_411.xlsx", subida por "docente411@example.invalid"
    Y que "docente.varias@example.invalid" tiene publicadas sus tres secciones
    Y que "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando se envía GET /api/resultados?periodo=2026-2
    Entonces la API responde 200 con 5 secciones, en el orden 410, 411 y 412 de "450002" y 410 y 412 de "450010", y 15 indicadores, 11 del SO 5 y 4 del SO 2
    Y la respuesta no trae ningún correo ni el campo subida_por
    Pero acceso.docente_seccion sigue sin filas de "coordinacion@example.invalid"

  @US-44 @corte1 @spec004 @delegado_a_vitest
  Escenario: P6 del coordinador agrupa por asignatura y no ordena por resultado
    Dado la respuesta del escenario «El coordinador ve las cinco secciones del periodo»
    Cuando "coordinacion@example.invalid" abre P6 con «Ver los logros por SO de la carrera» (propuesta) desde la cabecera
    Entonces P6 agrupa las secciones por asignatura, 450002 y después 450010, con las secciones de cada una en el orden de su número y nunca por su porcentaje
    Y P6 no muestra ningún correo ni nombre de profesor
