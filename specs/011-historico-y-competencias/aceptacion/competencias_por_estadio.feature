# language: es
#
# Escenarios de aceptación de US-102 y US-104 de la spec 011-historico-y-competencias (épica EP-11, propuesta). La ruta
# 23 da a la coordinación de una carrera, para un periodo, las mediciones con nivel esperado o superior de cada
# competencia en cada estadío, y la ruta 24 da la misma cifra de una competencia en cada periodo visible, como la página
# «Resumen Competencias - Nivel» del tablero de Stefanny Montaño, con las cifras de la base y sin Power BI.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid y estudiantes del rango
# 99500000 a 99599999.
#
# Vocabulario de los pasos.
# - La base es la de scripts/api_local.sh con lo que suma T025, y no carga db/pruebas/datos_sinteticos.sql. Trae
#   db/datos/periodo_2026_2_inventado.sql, con coordinacion@example.invalid, su fila de la carrera AMB y la 410 y la
#   411 de 450002 sin carga, db/datos/varias_secciones_2026_2_inventado.sql, con la 412 de 450002 y la 410 y la 412 de
#   450010 sin carga, y la semilla db/datos/competencias_ambiental_inventado.sql de US-106 (propuesta), con 6511 (401),
#   450002 (413) y 5674 (401) en 2026-2 y 450002 (413) en el periodo nuevo 2024-2, cada sección con un profesor
#   inventado. Esas son todas las secciones de Ambiental de 2024-2 y 2026-2.
# - Las secciones de una celda son las de las asignaturas del plan de estudios de AMB-2026 que tienen ese estadío para
#   esa competencia en abet.asignatura_competencia y un plan_medicion de un PI de un SO de esa competencia en el
#   periodo. Las que tienen carga PUBLICADA suman sus mediciones, y las demás cuentan en conteo_secciones.sin_dato,
#   igual que en la ruta 20 (FR-005).
# - «Las cargas del oráculo» son las de tests/datos_inventados/oraculo_011.md (propuesta), con 5 estudiantes por
#   sección, publicadas con R-2026-BORRADOR de Ambiental.
# - Una medición es el nivel de un estudiante en un PI de una carga PUBLICADA (uq_medicion), y es la unidad de cada
#   celda. En AMB-2026 G4 sale del SO 5, G3 del SO 3, G8 del SO 4 y E2 del SO 2, y G1, G2, G5 y G7 no tienen SO.
# - Las cifras son las de las tablas de Ambiental de la sección «Datos inventados de la demostración» de spec.md, con
#   su cuenta.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Logro por competencia y estadío para la coordinación de la carrera
  Como coordinación de Ambiental, quiero recibir las mediciones de cada competencia en cada estadío, con sus
  asignaturas, sus secciones y sus PI, para saber si la carrera progresa a lo largo de la malla.

  Antecedentes:
    Dado una base desechable de la spec 011 con periodo_2026_2_inventado.sql, varias_secciones_2026_2_inventado.sql y la semilla de Ambiental en 2024-2 y 2026-2
    Y la base no carga db/pruebas/datos_sinteticos.sql

  @spec011 @corte1 @US-102
  Escenario: G4 trae una celda por estadío con sus mediciones
    Dado las cargas del oráculo de Ambiental en 2026-2
    Cuando coordinacion@example.invalid pide GET /api/resumen-carrera/competencias?periodo=2026-2 (propuesta)
    Entonces la respuesta es 200 con la carrera AMB
    Y G4 trae en INICIAL logrados 3, calificados 5, pct_sobre_calificados 60.0 y en_meta falso
    Y G4 trae en REFUERZO logrados 12, calificados 15, pct_sobre_calificados 80.0 y en_meta verdadero
    Y G4 trae en LOGRADO logrados 9, calificados 10, pct_sobre_calificados 90.0 y en_meta verdadero

  @spec011 @corte1 @US-102
  Escenario: Cada celda trae sus asignaturas, sus secciones y su desglose por PI
    Dado las cargas del oráculo de Ambiental en 2026-2
    Cuando coordinacion@example.invalid pide las competencias de 2026-2
    Entonces G4 trae so 5 y pis 5.1, 5.2 y 5.3
    Y G4 en REFUERZO trae asignaturas 450002 y 450010 en ese orden
    Y 450002 trae las secciones 410, 411, 412 y 413 en ese orden, con la 413 en estado PUBLICADA, logrados 12, calificados 15 y pct_sobre_calificados 80.0
    Y la 410, la 411 y la 412 de 450002 y la 410 y la 412 de 450010 traen estado SIN_CARGA con logrados, calificados, pct_sobre_calificados y en_meta en null
    Y G4 en REFUERZO trae pis 5.1, 5.2 y 5.3 con 4 de 5 y pct_sobre_calificados 80.0 cada uno
    Y G4 en REFUERZO trae conteo_secciones con total 6, publicadas 1, en_meta 1, debajo_de_la_meta 0 y sin_dato 5

  @spec011 @corte1 @US-102
  Escenario: La 450002 suma a G4 por el SO 5 y no a G8
    Dado el plan de 450002 en 2026-2 con los PI 5.1, 5.2 y 5.3 del SO 5 y sin PI del SO 4
    Y el par de 450002 con G8 en REFUERZO en asignatura_competencia
    Y las cargas del oráculo de Ambiental en 2026-2
    Cuando coordinacion@example.invalid pide las competencias de 2026-2
    Entonces las 15 mediciones de la 413 suman a G4 en REFUERZO
    Y G8 en REFUERZO trae calificados 0, conteo_secciones con total 0 y asignaturas vacía

  @spec011 @corte1 @US-102
  Escenario: La unidad de la celda es la medición de un estudiante en un PI
    Dado la 413 de 450002 en 2026-2 con 5 estudiantes medidos en 5.1, 5.2 y 5.3
    Cuando coordinacion@example.invalid pide las competencias de 2026-2
    Entonces G4 en REFUERZO trae calificados 15 y no 5
    Y la respuesta no trae una clave que cuente estudiantes distintos

  @spec011 @corte1 @US-102
  Escenario: Una celda sin mediciones trae nulos y no ceros
    Dado las cargas del oráculo de Ambiental en 2026-2
    Cuando coordinacion@example.invalid pide las competencias de 2026-2
    Entonces G3 trae en INICIAL logrados 2, calificados 5, pct_sobre_calificados 40.0 y conteo_secciones con total 1 y debajo_de_la_meta 1
    Y G3 trae en REFUERZO y en LOGRADO calificados 0, conteo_secciones con total 0 y pct_sobre_calificados, promedio_nivel y en_meta en null

  @spec011 @corte1 @US-102
  Escenario: Una sección sin carga publicada cuenta como sin dato en su celda
    Dado las cargas del oráculo de Ambiental en 2026-2
    Y una carga RECHAZADA de la 410 de 450010 en 2026-2 creada en la prueba con un export inventado que el lector rechaza
    Cuando coordinacion@example.invalid pide las competencias de 2026-2
    Entonces E2 trae so 2 y pis 2.1 y 2.2
    Y E2 en REFUERZO trae calificados 0, conteo_secciones con total 2, publicadas 0 y sin_dato 2, y pct_sobre_calificados, promedio_nivel y en_meta en null
    Y E2 en REFUERZO trae la 410 y la 412 de 450010 con estado SIN_CARGA
    Y G4 en REFUERZO sigue con logrados 12, calificados 15 y conteo_secciones con sin_dato 5

  @spec011 @corte1 @US-102
  Escenario: Las competencias sin SO vienen sin celdas
    Dado las cargas del oráculo de Ambiental en 2026-2
    Cuando coordinacion@example.invalid pide las competencias de 2026-2
    Entonces G1, G2, G5 y G7 traen so en null y estadios vacío

  @spec011 @corte1 @US-102
  Escenario: El plan de Industrial de 5643 no suma a E3 de Ambiental
    Dado la vigencia de AMB-2026 en 2026-1 creada en la prueba
    Y la 701 de 5643 en 2026-1 publicada con el plan de IND-2026 y los niveles [0, 0, 3, 2] del oráculo
    Cuando coordinacion@example.invalid pide las competencias de 2026-1
    Entonces E3 en INICIAL trae calificados 0 y conteo_secciones con total 0
    Y ninguna celda suma una medición ni una sección de 5643

  @spec011 @corte1 @US-102
  Escenario: Todos los estadíos cuentan con el mismo nivel esperado
    Dado R-2026-BORRADOR de Ambiental con NIVEL_ESPERADO 3
    Y las cargas del oráculo de Ambiental en 2026-2
    Cuando coordinacion@example.invalid pide las competencias de 2026-2
    Entonces G4 en INICIAL, en REFUERZO y en LOGRADO trae nivel_esperado 3
    Y cada celda cuenta como logradas solo las mediciones con nivel 3 o 4

  @spec011 @corte1 @US-102
  Escenario: Las competencias y los estadíos van en un orden fijo
    Dado las cargas del oráculo de Ambiental en 2026-2
    Cuando coordinacion@example.invalid pide las competencias de 2026-2
    Entonces competencias trae G1 a G8 y después E1 a E3, cada grupo en orden de número
    Y cada competencia con SO trae los estadios INICIAL, REFUERZO y LOGRADO en ese orden
    Y las asignaturas de cada celda van en orden de código y sus secciones en orden de número

  @spec011 @corte1 @US-102
  Escenario: Cada celda trae sus mediciones por nivel y su promedio
    Dado las cargas del oráculo de Ambiental en 2026-2
    Cuando coordinacion@example.invalid pide las competencias de 2026-2
    Entonces G4 en INICIAL trae mediciones_por_nivel [0, 2, 2, 1] y promedio_nivel 2.8
    Y G4 en REFUERZO trae mediciones_por_nivel [1, 2, 7, 5] y promedio_nivel 3.07
    Y G4 en LOGRADO trae mediciones_por_nivel [0, 1, 5, 4] y promedio_nivel 3.3
    Y G3 en INICIAL trae mediciones_por_nivel [1, 2, 1, 1] y promedio_nivel 2.4

  @spec011 @corte1 @US-102
  Escenario: Con un conjunto de reglas provisional las celdas salen provisionales
    Dado las cargas del oráculo publicadas con R-2026-BORRADOR de Ambiental, que tiene parámetros PENDIENTE
    Cuando coordinacion@example.invalid pide las competencias de 2026-2
    Entonces cada celda de G4 trae provisional verdadero

  @spec011 @corte1 @US-102
  Escenario: La respuesta de las competencias trae solo las claves de su lista cerrada
    Dado las cargas del oráculo de Ambiental en 2026-2
    Cuando coordinacion@example.invalid pide las competencias de 2026-2
    Entonces la respuesta trae solo las claves de la lista cerrada de la ruta 23 del contrato
    Y no trae correos, nombres de personas, usuario_id, subida_por, nombre_archivo ni sha256
    Y ni el texto «Profesor Inventado» ni un número de 8 cifras aparecen en el cuerpo de la respuesta

  @spec011 @corte1 @US-102
  Escenario: La coordinación de un curso recibe la lista de competencias vacía
    Dado coordinador.quimica@example.invalid con alcance solo de la asignatura 5643
    Cuando pide GET /api/resumen-carrera/competencias?periodo=2026-2
    Entonces la respuesta es 200 con competencias vacía

  @spec011 @corte1 @US-102
  Escenario: Una carrera sin el mapeo de competencias recibe la lista vacía
    Dado una cuenta COORDINADOR creada en la prueba con la fila de la carrera IND
    Y el catálogo IND-2026 vigente en 2026-1, con 0 filas en asignatura_competencia
    Cuando pide GET /api/resumen-carrera/competencias?periodo=2026-1
    Entonces la respuesta es 200 con la carrera IND y competencias vacía

  @spec011 @corte1 @US-102
  Escenario: El profesor recibe 403 en las competencias y sin sesión la ruta responde 401
    Dado docente413@example.invalid con sesión
    Cuando pide GET /api/resumen-carrera/competencias?periodo=2026-2
    Entonces la respuesta es 403 con «Esta página es de la Coordinación.»
    Y la misma petición sin sesión responde 401

  @spec011 @corte1 @US-102
  Escenario: Un periodo o una carrera mal formados responden 422 sin leer la base
    Cuando coordinacion@example.invalid pide GET /api/resumen-carrera/competencias?periodo=2026/2
    Entonces la respuesta es 422 con «El periodo no tiene la forma AAAA-C.»
    Y con periodo=2026-2&carrera=amb la respuesta es 422 con «La carrera no tiene la forma de un código de 2 a 10 letras mayúsculas.» (propuesta)

  @spec011 @corte1 @US-102
  Escenario: Una carrera fuera del alcance responde 200 con la lista vacía
    Dado coordinacion@example.invalid con la fila de la carrera AMB y sin la de IND
    Cuando pide GET /api/resumen-carrera/competencias?periodo=2026-1&carrera=IND
    Entonces la respuesta es 200 con competencias vacía
    Y la respuesta no dice si IND tiene secciones en 2026-1

  @spec011 @corte1 @US-104
  Escenario: La evolución de G4 trae los periodos visibles en orden cronológico
    Dado las cargas del oráculo de Ambiental en 2024-2 y 2026-2
    Cuando coordinacion@example.invalid pide GET /api/resumen-carrera/competencias/evolucion?competencia=G4 (propuesta)
    Entonces la respuesta trae los periodos 2024-2 y 2026-2 en ese orden
    Y 2024-2 trae REFUERZO con logrados 9, calificados 15, pct_sobre_calificados 60.0, promedio_nivel 2.73 y conteo_secciones con total 1, e INICIAL y LOGRADO con calificados 0 y conteo_secciones con total 0
    Y 2026-2 trae INICIAL con 60.0, REFUERZO con 80.0 y conteo_secciones con total 6 y sin_dato 5, y LOGRADO con 90.0
    Y ningún periodo trae la clave asignaturas

  @spec011 @corte1 @US-104
  Escenario: Un periodo sin la vigencia de la carrera no aparece en la evolución
    Dado la semilla histórica de Química con secciones de 5643 en 2025-1 y 2025-2 y sin vigencia de AMB en esos periodos
    Y las cargas del oráculo de Ambiental en 2024-2 y 2026-2
    Cuando coordinacion@example.invalid pide la evolución de G4
    Entonces la respuesta no trae 2025-1, 2025-2 ni 2026-1

  @spec011 @corte1 @US-104
  Escenario: Una competencia mal formada responde 422 y el profesor recibe 403
    Cuando coordinacion@example.invalid pide GET /api/resumen-carrera/competencias/evolucion?competencia=X4
    Entonces la respuesta es 422 con «La competencia no tiene la forma de una letra G o E seguida de su número.» (propuesta)
    Y docente413@example.invalid recibe 403 con «Esta página es de la Coordinación.» en la misma ruta

  @spec011 @corte1 @US-104
  Escenario: La evolución de las competencias trata el alcance y la carrera como la ruta 23
    Dado las cargas del oráculo de Ambiental en 2024-2 y 2026-2
    Cuando coordinador.quimica@example.invalid, con alcance solo de la asignatura 5643, pide GET /api/resumen-carrera/competencias/evolucion?competencia=G4
    Entonces la respuesta es 200 con periodos vacía
    Y coordinacion@example.invalid con competencia=G4&carrera=IND recibe 200 con periodos vacía
    Y coordinacion@example.invalid con competencia=G4&carrera=AMB recibe los periodos 2024-2 y 2026-2
    Y con competencia=G4&carrera=amb la respuesta es 422 con «La carrera no tiene la forma de un código de 2 a 10 letras mayúsculas.» (propuesta)
