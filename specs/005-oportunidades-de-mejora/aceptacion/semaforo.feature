# language: es
#
# Escenarios de aceptación del semáforo de una carga, de las historias de usuario (user stories, US) US-45 y
# US-46 de la spec 005-oportunidades-de-mejora (épica EP-05, propuesta). Jefferson pide el 2026-11-18 que el
# profesor vea cómo va su sección al terminar la carga, sin abrir el R-17. N6 pide «Al subir el archivo, el
# docente recibe al instante un reporte de su sección», y ninguna ruta entrega hoy cifras por carga (la
# constancia no las trae y la ruta 12 es de la pantalla P6).
#
# Cambio del 2026-11-21 (borrador, pendiente de la reaprobación de Jefferson). Cada indicador de la ruta 13
# suma hallazgo y tipo_registro, porque el profesor registra por PI una oportunidad de mejora (OM) o una buena
# práctica (BP) que fija el semáforo, como pide Claudia León («incluso cuando se supera el valor de
# referencia, deberíamos hacer el análisis de causas hasta llegar a la BP»). La 412 de 450002 es el ejemplo
# con PI sobre la meta.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid y los códigos de
# estudiante 99000001 a 99000011. Ninguna contraseña aparece escrita aquí, porque la prueba asigna al azar la
# contraseña con que abre cada sesión, sin guardarla en el repositorio.
# - Los exports viven en tests/datos_inventados/ y sus cifras salen de NIVELES_410 y NIVELES_450002_412 de
#   scripts/generar_exports_inventados.py. Con R-2026-BORRADOR (nivel esperado 3, meta 0,80 y CORTE_ROJO
#   PENDIENTE), la 410 da 5.1 [1, 3, 4, 3] 7 de 11 63,6 %, 5.2 [1, 3, 4, 3] 7 de 11 63,6 % y 5.3 [1, 2, 5, 3]
#   8 de 11 72,7 %, los tres ROJO. La 412 de 450002 da 5.1 [1, 1, 5, 4] 9 de 11 81,8 % VERDE, 5.2
#   [2, 3, 4, 2] 6 de 11 54,5 % ROJO y 5.3 [0, 1, 4, 6] 10 de 11 90,9 % VERDE.
# - Las copias con celdas vacías se arman en tmp_path con REGLAS_DE_COPIA de
#   tests/aceptacion/pasos/conftest.py. 5.3 por fila de la 410: 2 = 3, 3 = 4, 4 = 3, 5 = 3, 6 = 2, 7 = 4,
#   8 = 3, 9 = 1, 10 = 4, 11 = 3, 12 = 2. La regla «con la columna X.Y vacía en la fila N» existe. La regla
#   «en las filas N y M» (y la de tres filas) es nueva y llega con FR-017.
# - R-PRUEBA-SEMAFORO es un conjunto de reglas de prueba nuevo, APROBADO y completo, con META_LOGRO 0,80,
#   NIVEL_ESPERADO 3 y CORTE_ROJO 0,75, que arma un ayudante parametrizado de tests/cargas_de_prueba.py (hoy
#   conjunto_aprobado fija 0,70, 2 y 0,50). Con él, la 410 original da 5.3 72,7 % ROJO.
#
# Vocabulario de los pasos, el de resultados.feature de la spec 004 y el de acceso.feature de la spec 001.
# - «se envía GET /api/cargas/{carga_id}/indicadores» es la petición a la ruta 13 (propuesta) con la cookie
#   abet_sesion de quien tiene la sesión iniciada.
# - Un indicador es una fila de la respuesta por PI, con las claves de FR-006 de la spec 004
#   (estudiantes_por_nivel, logrados, calificados, sin_evidencia, total, pct_sobre_calificados,
#   pct_sobre_total, meta_pct, nivel_esperado y en_meta) más semaforo, hallazgo y tipo_registro.
# - Regla del semáforo (J-29). SIN_DATO si falta el logro o la meta. VERDE si en_meta es verdadero. AMBAR si
#   CORTE_ROJO está DEFINIDO y el logro es mayor o igual que el corte y menor que la meta. ROJO en los demás
#   casos. Mientras CORTE_ROJO siga PENDIENTE en R-2026-BORRADOR, el piloto muestra VERDE, ROJO o SIN_DATO.
# - Regla del tipo de registro (D-39), la de tipo_de_registro() de abet_carga/resultados.py. VERDE da
#   BUENA_PRACTICA, AMBAR y ROJO dan OPORTUNIDAD_MEJORA, y SIN_DATO da nulo, porque un PI sin calificaciones
#   no lleva registro (D-40).
# - (propuesta) El hallazgo, de redactar_hallazgo(), sigue la forma «5.2: 63,6 % en Satisfactorio o más, meta
#   80,0 %», con el logro sobre calificados, el nombre del nivel esperado en la escala base y la meta, ambos
#   con un decimal y coma decimal. Un PI sin calificaciones lleva «5.3: sin calificaciones en esta carga.» y
#   un conjunto sin META_LOGRO o sin NIVEL_ESPERADO definido lleva «5.1: el conjunto de reglas no define la
#   meta o el nivel esperado.». El Front copia la frase y el tipo sin calcularlos.
# - «7 de 11» es logrados 7 con calificados 11. Una cifra «63,6 %» viaja como el número 63.6.
# - Cada escenario corre en una base desechable propia, así que los carga_id y los seccion_id salen de la
#   API o de la base y nunca se suponen.
# - @delegado_a_vitest marca un escenario de la pantalla P4 que prueba Vitest en el Front, como en la spec
#   004, y aquí queda como criterio escrito.
# - «con su análisis declarado» llama a declarar() de tests/cargas_de_prueba.py, que registra y declara la
#   causa y la acción de prueba de cada PI con calificados (FR-017), porque desde US-49 el R-17 sale solo con
#   la declaración vigente completa.
# - Los Antecedentes nombran V1_11, porque J-41 construye primero la ruta 13 y P4 (US-45 y US-46) y V1_12
#   todavía no existe. US-47 los lleva a V1_12 en el mismo cambio que crea esa migración (T021 y T012). El
#   escenario «Las cifras y el semáforo coinciden con el R-17 de la misma carga» necesita V1_12, las rutas 14
#   a 16 y US-49, así que su prueba se escribe en la segunda etapa de J-41, junto con declarar() (T037).
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec. D-35
#   (valor de CORTE_ROJO), D-39 y D-40 siguen abiertas con la Coordinación.

Característica: El semáforo de una carga publicada, calculado en el Back y mostrado en P4
  Como profesor de Ingeniería Ambiental, quiero ver en P4, justo después de subir el export, la tabla de
  niveles de cada PI de mi sección con un semáforo frente a la meta, un hallazgo y el tipo de registro que
  corresponde, con las mismas cifras de mi R-17, para saber cómo va mi sección sin abrir el archivo y qué
  analizar en cada indicador.

  Antecedentes:
    Dado una base PostgreSQL 18 desechable con las migraciones V1_01 a V1_11, los datos de db/datos/periodo_2026_2_inventado.sql y, después, los de db/datos/varias_secciones_2026_2_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2", CONJUNTO_REGLAS "R-2026-BORRADOR" y GUARDIA_DATOS_INVENTADOS "1"
    Y plan_medicion registra los PI 5.1, 5.2 y 5.3 para la asignatura "450002" en "2026-2"
    Y acceso.docente_seccion asigna la sección 410 de "450002" a "docente410@example.invalid", la 411 de "450002" a "docente411@example.invalid" y la 412 de "450002" a "docente.varias@example.invalid"
    Y ninguna sección de 2026-2 tiene cargas

  # US-45: Las cifras, el semáforo y el hallazgo de una carga
  # (propuesta) La ruta 13 y la forma de su respuesta. Trae carga_id, estado, provisional, conjunto_reglas,
  # conjunto_reglas_estado, parametros_pendientes, meta_pct, corte_rojo_pct (nulo si CORTE_ROJO está
  # PENDIENTE) e indicadores, ordenados por so_numero y pi.numero, en una sola instantánea con
  # Cache-Control: no-store. Cada indicador trae además semaforo, hallazgo y tipo_registro.

  @US-45 @spec005 @corte1
  Escenario: La 410 publicada con el conjunto borrador queda en rojo y pide tres oportunidades de mejora
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/cargas/{carga_id}/indicadores
    Entonces la API responde 200 con meta_pct 80.0 y corte_rojo_pct nulo
    Y los tres PI 5.1, 5.2 y 5.3 traen estudiantes_por_nivel [1, 3, 4, 3], [1, 3, 4, 3] y [1, 2, 5, 3], logrados 7, 7 y 8, calificados 11 y pct_sobre_total 63.6, 63.6 y 72.7
    Y el semáforo de los tres PI es "ROJO" y su tipo_registro es "OPORTUNIDAD_MEJORA"
    Y el hallazgo de 5.1 es «5.1: 63,6 % en Satisfactorio o más, meta 80,0 %» (propuesta)

  # El ejemplo que pide Claudia León, con PI que superan el 80 % y que también llevan análisis, como BP.
  @US-45 @spec005 @corte1
  Esquema del escenario: La 412 de 450002 muestra verde, rojo y verde, con dos buenas prácticas
    Dado que "docente.varias@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_412.xlsx" está subido a la sección 412 con respuesta 201 y su carga_id
    Cuando se envía GET /api/cargas/{carga_id}/indicadores
    Entonces el indicador <pi> trae estudiantes_por_nivel <niveles>, logrados <logrados>, calificados 11 y pct_sobre_calificados <logro>
    Y su semáforo es "<semaforo>", su en_meta es <en_meta> y su tipo_registro es "<tipo>"
    Y su hallazgo es «<hallazgo>» (propuesta)

    Ejemplos:
      | pi  | niveles      | logrados | logro | semaforo | en_meta   | tipo               | hallazgo                                          |
      | 5.1 | [1, 1, 5, 4] | 9        | 81.8  | VERDE    | verdadero | BUENA_PRACTICA     | 5.1: 81,8 % en Satisfactorio o más, meta 80,0 %   |
      | 5.2 | [2, 3, 4, 2] | 6        | 54.5  | ROJO     | falso     | OPORTUNIDAD_MEJORA | 5.2: 54,5 % en Satisfactorio o más, meta 80,0 %   |
      | 5.3 | [0, 1, 4, 6] | 10       | 90.9  | VERDE    | verdadero | BUENA_PRACTICA     | 5.3: 90,9 % en Satisfactorio o más, meta 80,0 %   |

  # La frontera de la meta. «En la meta» es llegar a la meta o superarla. Sin la nota de la fila 9 (99000008,
  # el único estudiante con nivel 1 en 5.3), 5.3 queda en 8 de 10.
  @US-45 @spec005 @corte1
  Escenario: El 80,0 % justo en la meta queda en verde y pide una buena práctica
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en la fila 9 está subida a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/cargas/{carga_id}/indicadores
    Entonces el indicador 5.3 trae estudiantes_por_nivel [0, 2, 5, 3], logrados 8, calificados 10, sin_evidencia 1, pct_sobre_calificados 80.0 y pct_sobre_total 72.7
    Y su en_meta es verdadero, su semáforo es "VERDE" y su tipo_registro es "BUENA_PRACTICA"
    Y su hallazgo es «5.3: 80,0 % en Satisfactorio o más, meta 80,0 %» (propuesta)

  # CORTE_ROJO 0,75 define la banda ámbar. Con R-PRUEBA-SEMAFORO, la copia de las filas 2 y 6 da [1, 1, 4, 3],
  # 7 de 9, 77,8 sobre calificados y 63,6 sobre el total, y la de las filas 2, 3 y 9 da [0, 2, 4, 2], 6 de 8,
  # 75,0 sobre calificados y 54,5 sobre el total (frontera del corte).
  @US-45 @spec005 @corte1
  Esquema del escenario: Con el corte rojo definido, la banda ámbar va desde el corte hasta debajo de la meta y pide una oportunidad de mejora
    Dado que la base tiene el conjunto "R-PRUEBA-SEMAFORO" de Ambiental en estado "APROBADO" con META_LOGRO 0,80, NIVEL_ESPERADO 3 y CORTE_ROJO 0,75, y la API configurada con ese CONJUNTO_REGLAS
    Y que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que <archivo> está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/cargas/{carga_id}/indicadores
    Entonces la API responde 200 con meta_pct 80.0 y corte_rojo_pct 75.0
    Y el indicador 5.3 trae pct_sobre_calificados <logro>, semaforo "<semaforo>" y tipo_registro "OPORTUNIDAD_MEJORA"

    Ejemplos:
      | archivo                                                                                          | logro | semaforo |
      | una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en las filas 2 y 6       | 77.8  | AMBAR    |
      | una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en las filas 2, 3 y 9    | 75.0  | AMBAR    |
      | "sintetico_20262_450002_410.xlsx"                                                                | 72.7  | ROJO     |

  # Con CORTE_ROJO PENDIENTE no hay banda ámbar, así que el 77,8 % de la misma copia queda en ROJO.
  @US-45 @spec005 @corte1
  Escenario: Con el corte rojo pendiente no hay ámbar
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en las filas 2 y 6 está subida a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/cargas/{carga_id}/indicadores
    Entonces la API responde 200 con corte_rojo_pct nulo
    Y el indicador 5.3 trae estudiantes_por_nivel [1, 1, 4, 3], logrados 7, calificados 9, sin_evidencia 2, pct_sobre_calificados 77.8 y pct_sobre_total 63.6
    Y su semáforo es "ROJO" y no "AMBAR"

  # D-40 (valor provisional). Un PI sin calificaciones no lleva registro.
  @US-45 @spec005 @corte1
  Escenario: Un PI sin calificaciones sale sin dato, nunca en rojo y sin tipo de registro
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en sus 11 filas está subida a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/cargas/{carga_id}/indicadores
    Entonces el indicador 5.3 trae pct_sobre_calificados nulo, pct_sobre_total 0.0, sin_evidencia 11 y semaforo "SIN_DATO"
    Y el indicador 5.3 trae tipo_registro nulo y el hallazgo «5.3: sin calificaciones en esta carga.» (propuesta)
    Y los indicadores 5.1 y 5.2 traen semaforo "ROJO" y tipo_registro "OPORTUNIDAD_MEJORA"

  # El dueño de la base deja el parámetro sin DEFINIR solo en la base desechable.
  @US-45 @spec005 @corte1
  Esquema del escenario: Un parámetro sin definir deja los indicadores sin dato y no rompe la ruta
    Dado que la base tiene un conjunto de reglas de prueba de Ambiental con <parametro> sin DEFINIR, y la API configurada con ese CONJUNTO_REGLAS
    Y que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Cuando se envía GET /api/cargas/{carga_id}/indicadores
    Entonces la API responde 200 y no 500
    Y cada indicador trae semaforo "SIN_DATO" y tipo_registro nulo
    Y el hallazgo de 5.1 es «5.1: el conjunto de reglas no define la meta o el nivel esperado.» (propuesta)

    Ejemplos:
      | parametro    |
      | NIVEL_ESPERADO |
      | META_LOGRO   |

  # Las cifras son las del R-17 de la misma carga. El bloque II escribe el porcentaje y la meta como fracción
  # (0,818 para 81,8 %), así que la comparación multiplica la celda por 100 y la redondea a un decimal. El
  # R-17 solo se entrega con la declaración vigente completa de US-49, que el paso «con su análisis declarado»
  # cubre antes de descargar. «El indicador aún no alcanza …» y «¡Felicidades! …» son los textos de H24:H26.
  # Cada profesor sube y declara la carga de su sección, y el coordinador, que lee todas (BR-ACCESO-08),
  # pide la ruta 13 y descarga el R-17 de las tres. Este escenario entra en la segunda etapa de J-41.
  @US-45 @spec005 @corte1
  Escenario: Las cifras y el semáforo coinciden con el R-17 de la misma carga
    Dado que "docente410@example.invalid" tiene subido "sintetico_20262_450002_410.xlsx" a la sección 410 con respuesta 201 y su carga_id, con su análisis declarado
    Y que "docente.varias@example.invalid" tiene subido "sintetico_20262_450002_412.xlsx" a la sección 412 con respuesta 201 y su carga_id, con su análisis declarado
    Y que "docente411@example.invalid" tiene subida una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en sus 11 filas a la sección 411 con respuesta 201 y su carga_id, con su análisis declarado
    Y que "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando se envía GET /api/cargas/{carga_id}/indicadores y se descarga el R-17 de cada una de las tres cargas
    Entonces en cada indicador el logro es igual a round(100 × la celda E de su fila del bloque II, 1) y la meta a round(100 × la celda G de esa fila, 1)
    Y los conteos por nivel son los de las celdas L a O de K29:Q31, «7 de 11» es el de la celda P y pct_sobre_total es round(100 × la celda Q, 1)
    Y el semáforo "VERDE" va con el texto «¡Felicidades! …» de la celda H de su fila
    Y el semáforo "ROJO" o "AMBAR" va con el texto «El indicador aún no alcanza …» de la celda H de su fila
    Y el indicador "SIN_DATO" de la copia sin notas en 5.3 va con la celda H vacía

  @US-45 @spec005 @corte1
  Escenario: Sin sesión la ruta responde 401
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y una petición sin la cookie "abet_sesion"
    Cuando se envía GET /api/cargas/{carga_id}/indicadores
    Entonces la API responde 401

  # La misma respuesta 403 para una carga ajena y para una que no existe, para no revelar cuáles existen.
  @US-45 @spec005 @corte1
  Esquema del escenario: El profesor solo ve el semáforo de sus secciones
    Dado que "sintetico_20262_450002_410.xlsx" está subido a la sección 410 con respuesta 201 y su carga_id
    Y que "<correo>" tiene la sesión iniciada con rol "<rol>"
    Cuando se envía GET /api/cargas/<carga>/indicadores
    Entonces la API responde <respuesta>

    Ejemplos:
      | correo                       | rol         | carga                | respuesta                                       |
      | docente411@example.invalid   | PROFESOR    | {carga_id de la 410} | 403 con el mensaje "La sección no está a su cargo." |
      | docente410@example.invalid   | PROFESOR    | 999999               | 403 con el mensaje "La sección no está a su cargo." |
      | coordinacion@example.invalid | COORDINADOR | {carga_id de la 410} | 200 con los tres PI de la 410                   |

  # (propuesta) El estado de la carga manda, porque solo una carga PUBLICADA tiene semáforo.
  @US-45 @spec005 @corte1
  Esquema del escenario: Una carga que no está publicada no tiene semáforo
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Y que <carga>
    Cuando se envía GET /api/cargas/{carga_id}/indicadores
    Entonces la API responde 409 con el mensaje "La carga no está publicada y no tiene semáforo." (propuesta)

    Ejemplos:
      | carga                                                                                                                                                                                  |
      | una copia de "sintetico_20262_450002_410.xlsx" sin la columna del PI 5.2 está subida a la sección 410 y su carga está "RECHAZADA" con PI_DEL_PLAN_AUSENTE                                 |
      | la carga A REEMPLAZADA de "sintetico_20262_450002_410.xlsx" y la carga B PUBLICADA de "export_inventado_410_con_error.xlsx" que la reemplaza en la sección 410, y se pide la de A          |

  # US-46: Ver el semáforo en P4 al terminar la carga
  # (propuesta) P4, sección «Cómo va su sección», después de los rechazos y los avisos y antes de la sección
  # «Análisis por indicador» de US-47, solo en una carga PUBLICADA. El hallazgo y el tipo de cada PI encabezan
  # su bloque en US-47, no la tabla. Columnas «PI», «Nivel 1» a «Nivel 4», «Logran / calificados» y «% sobre
  # el total», más «Logro», «Meta» y «Estado». El Front no compara cifras. Cada estado tiene luz de color con
  # aria-hidden y texto, de modo que ningún estado depende solo del color. Cambia FR-016 de la spec 004, el
  # invariante 8 de ADR-008, la línea de P4 de docs/01-arquitectura/frontend.md y las pruebas de P4 sin
  # porcentajes (J-35).

  @US-46 @spec005 @corte1 @delegado_a_vitest
  Escenario: P4 muestra la tabla de niveles con un estado por PI
    Dado la respuesta del escenario «La 410 publicada con el conjunto borrador queda en rojo y pide tres oportunidades de mejora»
    Cuando "docente410@example.invalid" abre la pantalla P4 de esa carga
    Entonces P4 muestra tres filas, con «7 de 11», «63,6 %» y «Debajo de la meta» (propuesta) en 5.1 y 5.2, y «8 de 11», «72,7 %» y «Debajo de la meta» (propuesta) en 5.3
    Y cada luz de color lleva aria-hidden

  @US-46 @spec005 @corte1 @delegado_a_vitest
  Esquema del escenario: La leyenda sale de la respuesta
    Dado una respuesta de la ruta 13 con meta_pct 80.0 y corte_rojo_pct <corte>
    Cuando "docente410@example.invalid" abre la pantalla P4 de esa carga
    Entonces la leyenda dice «<leyenda>» (propuesta)

    Ejemplos:
      | corte | leyenda                                                                                       |
      | null  | Verde, el logro alcanza la meta de 80 %. Rojo, todavía no la alcanza.                         |
      | 75.0  | Verde, desde la meta de 80 %. Ámbar, desde 75 % hasta debajo de la meta. Rojo, debajo de 75 %. |

  @US-46 @spec005 @corte1 @delegado_a_vitest
  Esquema del escenario: La franja provisional depende de la respuesta
    Dado una respuesta de la ruta 13 con provisional <valor>
    Cuando "docente410@example.invalid" abre la pantalla P4 de esa carga
    Entonces P4 <resultado>

    Ejemplos:
      | valor     | resultado                                                                                                                       |
      | verdadero | muestra sobre la tabla la franja de la constancia y del R-17, con el texto de su conjunto de reglas                             |
      | falso     | no muestra la franja                                                                                                            |

  @US-46 @spec005 @corte1 @delegado_a_vitest
  Escenario: Un PI sin dato no se pinta como 0 % ni en rojo
    Dado la respuesta del escenario «Un PI sin calificaciones sale sin dato, nunca en rojo y sin tipo de registro»
    Cuando "docente410@example.invalid" abre la pantalla P4 de esa carga
    Entonces el 5.3 dice «Sin calificaciones (11 sin evidencia)» (propuesta)
    Pero el 5.3 no dice «0 %» ni «0,0 %» y su luz no es roja

  @US-46 @spec005 @corte1 @delegado_a_vitest
  Escenario: P4 de una carga no publicada no pide el semáforo
    Dado una carga "RECHAZADA" y una carga "REEMPLAZADA" de la sección 410
    Cuando "docente410@example.invalid" abre la pantalla P4 de cada una
    Entonces P4 no pide la ruta 13 y no muestra la sección «Cómo va su sección»

  # (propuesta, AD-28) El Front se despliega antes que el Back, así que tolera el 404 de un Back anterior a la
  # spec 005.
  @US-46 @spec005 @corte1 @delegado_a_vitest
  Escenario: Con un Back anterior, P4 se comporta como hoy
    Dado que la ruta 13 responde 404
    Cuando "docente410@example.invalid" abre la pantalla P4 de su carga PUBLICADA
    Entonces P4 no muestra el semáforo ni la sección «Análisis por indicador»
    Y P4 conserva el enlace «Descargar R-17»
