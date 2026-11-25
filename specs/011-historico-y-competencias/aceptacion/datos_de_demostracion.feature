# language: es
#
# Escenarios de aceptación de US-105 a US-108 de la spec 011-historico-y-competencias (épica EP-11, propuesta). Las
# semillas, las tablas maestras inventadas, el generador, el ensayo y la siembra dan a la base los periodos y las
# mediciones que P9 y P10 necesitan para verse de punta a punta, con el flujo normal de carga y sin INSERT directos en
# abet.medicion.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid, estudiantes del rango
# 99500000 a 99599999 y profesores «Profesor Inventado» seguidos de palabras con letras.
#
# Vocabulario de los pasos.
# - «La semilla histórica» es db/datos/historico_quimica_inventado.sql y «la semilla de Ambiental» es
#   db/datos/competencias_ambiental_inventado.sql, las dos propuestas, que corren en seco salvo con -v aplicar=1.
# - «Las tablas maestras inventadas» viven en tests/datos_inventados/maestras_011/ (propuesta), una por periodo y
#   asignatura, y sus cifras son las del oráculo escrito a mano tests/datos_inventados/oraculo_011.md (propuesta).
# - «La siembra de la demostración» es db/herramientas/sembrar_demostracion.py (propuesta), que corre el respaldo, la
#   huella, la comprobación del rango de códigos, las semillas, el ensayo por periodo y asignatura y los controles, y
#   nunca carga 5643 en 2026-1. Sus escenarios corren en el clúster desechable de las pruebas, y la corrida real en la
#   rama demo-011 de Neon es la tarea T052 (J-72).
# - «Los manifiestos de la demostración» son los de los exports de 5643 en 2025-1 y 2025-2, de 450002 en 2024-2 y de
#   450002, 6511 y 5674 en 2026-2. Los de 5643 en 2026-1 los carga scripts/api_local.sh con el ensayo (T025) y no la
#   siembra.
# - La comprobación del rango vive en la siembra y no en ensayar_capacitacion.py. El rango está en uso si
#   abet.estudiante tiene un código de 99500000 a 99599999 sin mediciones o con alguna medición de una carga cuyo
#   archivo no tiene la huella SHA-256 de un export de los manifiestos.
# - La huella es db/plataforma/neon/huella_ambiental.sql, y sus partes 1 a 6 son el catálogo, los SO y PI, las
#   rúbricas, el plan de estudios, las asignaturas con su SO y las competencias.

Característica: Datos inventados de la demostración de punta a punta
  Como dueño técnico, quiero sembrar y cargar con el flujo normal los periodos y las mediciones inventadas que faltan,
  para que la coordinación vea la evolución del curso y las competencias por estadío funcionando de punta a punta.

  Antecedentes:
    Dado un clúster desechable migrado con Flyway hasta la última versión, con quimica_2026_1_inventado.sql, plan_quimica_2026_1.sql, periodo_2026_2_inventado.sql y varias_secciones_2026_2_inventado.sql
    Y el clúster no carga db/pruebas/datos_sinteticos.sql

  @spec011 @corte1 @US-105
  Escenario: La semilla histórica corre en seco salvo con aplicar
    Cuando se corre la semilla histórica sin -v aplicar=1
    Entonces informa las filas que escribiría en 2025-1 y 2025-2
    Y la base queda igual, con 5643 solo en 2026-1

  @spec011 @corte1 @US-105
  Escenario: Con aplicar 5643 queda con plan, secciones, profesores y alcance en 2025-1 y 2025-2
    Cuando se corre la semilla histórica con -v aplicar=1
    Entonces la vigencia de IND-2026 existe en 2025-1 y 2025-2 y la semilla la declara como ficción del catálogo
    Y 5643 tiene plan con el PI 6.1 en 2025-1, 2025-2 y 2026-1
    Y 2025-1 tiene las secciones SINTETICO_20251_5643_701 y SINTETICO_20251_5643_702, y 2025-2 las SINTETICO_20252_5643_701 a SINTETICO_20252_5643_703
    Y docente701@example.invalid a docente703@example.invalid quedan asignados a la sección de su número en cada periodo
    Y coordinador.quimica@example.invalid tiene una fila de alcance de 5643 en 2025-1, en 2025-2 y en 2026-1

  @spec011 @corte1 @US-105
  Escenario: La ruta 18 ofrece los tres periodos a la coordinación del curso
    Dado la semilla histórica aplicada
    Cuando coordinador.quimica@example.invalid pide GET /api/periodos
    Entonces la respuesta trae 2026-1, 2025-2 y 2025-1 en ese orden

  @spec011 @corte1 @US-105
  Escenario: Las semillas de la demostración no cambian el catálogo
    Dado la huella de la base antes de las semillas
    Cuando se aplican la semilla histórica y la de Ambiental
    Entonces las partes 1 a 6 de la huella dan las mismas filas
    Y IND-2026 sigue con 0 filas en rubrica_nivel, competencia y asignatura_competencia
    Y tests/semillas_inventadas.py revisa las dos semillas entre sus SEMILLAS sin encontrar correos fuera de example.invalid ni nombres fuera de «Profesor Inventado»

  @spec011 @corte1 @US-105
  Escenario: Una segunda corrida de las semillas no duplica filas
    Dado la semilla histórica y la de Ambiental aplicadas
    Cuando se aplican otra vez con -v aplicar=1
    Entonces informan 0 filas nuevas y la base queda igual

  @spec011 @corte1 @US-106
  Escenario: La semilla de Ambiental respeta el SO de cada asignatura
    Cuando se corre la semilla de Ambiental con -v aplicar=1
    Entonces en 2026-2 el plan de 6511 tiene 3.1 y 5.1, el de 450002 tiene 5.1, 5.2 y 5.3 y el de 5674 tiene 5.1 y 5.2
    Y en 2024-2 el plan de 450002 tiene 5.1, 5.2 y 5.3
    Y ningún plan usa un SO que su asignatura no tributa en abet.asignatura_so

  @spec011 @corte1 @US-106
  Escenario: La semilla crea 2024-2 sin abrir Química a la coordinación de Ambiental
    Dado la semilla histórica y la de Ambiental aplicadas
    Cuando coordinacion@example.invalid pide GET /api/periodos y las secciones de cada periodo que recibe
    Entonces la respuesta de periodos trae 2026-2 y 2024-2 en ese orden
    Y 2024-2 trae solo la 413 de 450002 con el curso SINTETICO_20242_450002_413
    Y ninguna sección de 5643 aparece en lo que recibe

  @spec011 @corte1 @US-106
  Escenario: Cada sección nueva de Ambiental tiene un profesor inventado
    Cuando se corre la semilla de Ambiental con -v aplicar=1
    Entonces la 401 de 6511 tiene a docente.lenguaje401@example.invalid, «Profesor Inventado Lenguaje Cuatrocientos Uno»
    Y la 413 de 450002 tiene a docente413@example.invalid, «Profesor Inventado Cuatrocientos Trece», en 2024-2 y en 2026-2
    Y la 401 de 5674 tiene a docente.proyectos401@example.invalid, «Profesor Inventado Proyectos Cuatrocientos Uno»
    Y la semilla no crea otra cuenta de coordinación

  @spec011 @corte1 @US-107
  Escenario: El generador arma un export por sección con todos sus PI
    Dado la tabla maestra inventada de 450002 en 2026-2
    Cuando se corre generar_exports_desde_maestra.py con --pi 5.1 --pi 5.2 --pi 5.3 y una salida fuera del repositorio
    Entonces el export de la 413 trae las columnas «5.1 [», «5.2 [» y «5.3 [»
    Y su carga crea tres filas en abet.carga_columna

  @spec011 @corte1 @US-107
  Escenario: Dos corridas del generador dan los mismos bytes
    Dado las tablas maestras inventadas de la demostración
    Cuando se corre el generador dos veces en carpetas distintas
    Entonces cada export tiene la misma huella SHA-256 en las dos corridas

  @spec011 @corte1 @US-107
  Escenario: Ningún export de la demostración repite la huella de otro
    Dado los exports de 5643 en 2025-1, 2025-2 y 2026-1 y los de Ambiental en 2024-2 y 2026-2
    Cuando se comparan sus huellas
    Entonces todas son distintas, así que uq_archivo_origen_sha256 no devuelve la constancia de otra carga

  @spec011 @corte1 @US-107
  Escenario: Un mismo estudiante inventado aparece en dos periodos con un solo registro
    Dado el estudiante 99500010 en la 702 de 2025-1 y en la 702 de 2025-2 de las tablas maestras inventadas
    Cuando se corren con ensayar_capacitacion.py los ensayos de 2025-1 y de 2025-2 en ese orden
    Entonces las dos cargas quedan publicadas
    Y abet.estudiante tiene un solo registro con el código 99500010
    Y ningún informe del ensayo menciona el rango de códigos de la demostración

  @spec011 @corte1 @US-107
  Escenario: Cada export sube por el flujo normal y queda publicado con su R-17
    Dado las semillas aplicadas y los exports de 5643 en 2025-1
    Cuando se corre el ensayo de 5643 en 2025-1
    Entonces la 701 y la 702 quedan con su carga PUBLICADA, subida por su profesor y con tipo_fuente BLACKBOARD_EXPORT
    Y ninguna carga queda con tipo_fuente R17_HISTORICO
    Y cada carga deja su R-17 en la carpeta de salida y el informe termina con «Ensayo sin diferencias.»

  @spec011 @corte1 @US-107
  Escenario: Una segunda corrida del ensayo no sube nada
    Dado la demostración ya cargada en 2025-1
    Cuando se corre otra vez el ensayo de 5643 en 2025-1
    Entonces no sube ningún archivo y lo dice
    Y la evolución de 5643 sigue con 6 de 10 en 2025-1

  @spec011 @corte1 @US-107
  Escenario: El oráculo escrito a mano coincide con las tablas maestras y con las rutas
    Dado el oráculo con 6 de 10, 8 de 12 y 12 de 15 para 5643, con 3 de 5, 12 de 15 y 9 de 10 para G4 en 2026-2 y con 9 de 15 para G4 en REFUERZO de 2024-2
    Cuando la prueba cuenta los niveles de las tablas maestras inventadas y pide las rutas 22, 23 y 24 sobre la base cargada
    Entonces los conteos de las tablas maestras y de las rutas 22, 23 y 24 coinciden con el oráculo
    Y el conteo de secciones de cada celda coincide con el del oráculo, con 6 secciones y 5 sin dato en G4 en REFUERZO de 2026-2

  @spec011 @corte1 @US-108
  Escenario: Sin --aplicar la siembra de la demostración no escribe y no toca 5643 en 2026-1
    Cuando se corre la siembra de la demostración con --rama demo y sin --aplicar
    Entonces informa el respaldo que haría, la huella, la comprobación del rango y las filas que escribiría cada paso
    Y la lista de ensayos trae 5643 en 2025-1 y 2025-2, 450002 en 2024-2 y 450002, 6511 y 5674 en 2026-2, y no trae 5643 en 2026-1
    Y ningún paso escribe en 2026-1
    Y termina con «Siembra terminada en seco. No se guardó nada.» y la base queda igual

  @spec011 @corte1 @US-108
  Escenario: La rama principal pide --confirmo-principal y termina antes de conectarse
    Cuando se corre la siembra de la demostración con --rama principal --aplicar y sin --confirmo-principal
    Entonces termina con el código 2 y «La rama principal pide también --confirmo-principal. No se conectó ni escribió nada.»

  @spec011 @corte1 @US-108
  Escenario: La siembra comprueba el rango de códigos una sola vez antes de la primera carga
    Dado una base sin estudiantes del rango 99500000 a 99599999
    Cuando se corre la siembra de la demostración con --rama demo y --aplicar
    Entonces el informe trae una sola vez «Rango de códigos de la demostración libre.» (propuesta), antes de la primera semilla
    Y los ensayos de 5643 en 2025-1 y en 2025-2 cargan al mismo estudiante 99500010 sin detenerse por el rango

  @spec011 @corte1 @US-108
  Escenario: Un estudiante del rango en la base detiene la siembra antes de escribir
    Dado un estudiante de código 99500001 creado en la prueba, sin mediciones
    Cuando se corre la siembra de la demostración con --rama demo y --aplicar
    Entonces termina con el código 1 y «El rango de códigos de la demostración ya está en uso.» (propuesta)
    Y no corre ninguna semilla ni sube ningún archivo, y la base queda igual

  @spec011 @corte1 @US-108
  Escenario: Un export con un código fuera del rango detiene la siembra antes de conectarse
    Dado los exports de 5643 en 2025-1 generados desde una copia de su tabla maestra inventada en la que la 701 trae el código 99000001
    Cuando se corre la siembra de la demostración con --rama demo y --aplicar
    Entonces termina con el código 1 antes de conectarse y «Un export de la demostración trae códigos fuera del rango 99500000 a 99599999.» (propuesta)
    Y el mensaje nombra 2025-1, 5643 y la sección 701 y no trae el código

  @spec011 @corte1 @US-108
  Escenario: La siembra se detiene ante cargas de secciones sin el prefijo SINTETICO_
    Dado una carga publicada de 5643 en 2025-1 creada en la prueba en una sección cuyo curso_blackboard no empieza con SINTETICO_, con códigos 99 fuera del rango de la demostración
    Cuando se corre la siembra de la demostración con --rama demo y --aplicar
    Entonces se detiene antes de subir, nombra el periodo 2025-1 y la asignatura 5643 y no escribe nada

  @spec011 @corte1 @US-108
  Escenario: La siembra informa y omite una asignatura con cargas que no son de la demostración
    Dado una carga publicada de la 410 de 450002 en 2026-2 creada en la prueba, con códigos 99 fuera del rango de la demostración
    Cuando se corre la siembra de la demostración con --rama demo y --aplicar
    Entonces informa «450002 en 2026-2 ya tiene cargas que no son de la demostración. Se omite su ensayo.» (propuesta)
    Y no sube el export de la 413 de 450002 en 2026-2
    Y carga los exports de 6511 y 5674 en 2026-2 y los de los demás periodos

  @spec011 @corte1 @US-108
  Escenario: Una segunda corrida de la siembra no sube nada
    Dado la siembra de la demostración ya aplicada con --rama demo
    Cuando se corre otra vez con --rama demo y --aplicar
    Entonces el informe trae «Rango de códigos de la demostración libre.», porque los estudiantes del rango solo tienen mediciones de las cargas de la demostración
    Y informa cada export como ya cargado por su huella y no sube ningún archivo
    Y las semillas informan 0 filas nuevas

  @spec011 @corte1 @US-108
  Escenario: Las consultas de control no dan filas después de la siembra
    Cuando se corre la siembra de la demostración con --rama demo y --aplicar
    Entonces controles_neon.sql no devuelve filas en ninguna de sus consultas
    Y las partes 1 a 6 de la huella quedan iguales a las de antes de la siembra
