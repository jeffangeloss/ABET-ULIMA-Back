# language: es
#
# Escenarios de aceptación de US-79 y US-80 de la spec 008-ciclo-quimica-industrial (épica EP-08, propuesta). La
# ruta 17 y P7 de la etapa B de la spec 007 dan a la coordinación del curso la etapa de cada sección de 5643 y
# ninguna de otro curso (US-79, C-22 corregida), y la ruta 12 suma, si D-32 se responde, el cumplimiento del
# curso con la suma de estudiantes (US-80, C-23 con el escenario del agregado de C-65, condicionada por J-54).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid.
#
# Vocabulario de los pasos.
# - Estos escenarios cubren solo lo que cambia frente a avance_del_registro.feature de la spec 007, que sigue
#   vigente con la precedencia de J-48, el 403 del profesor, el filtro «Mostrar solo las secciones que faltan» y
#   el campo profesores de US-66, que espera a D-47 en Ambiental y a D-51 en Industrial.
# - La ruta 17 toma su alcance de secciones_visibles() sin una rama por rol, así que la coordinación del curso la
#   lee con el mismo puede_ver_avance() del COORDINADOR (veredicto SE_SOSTIENE del crítico).
# - La base tiene db/datos/quimica_2026_1_inventado.sql, con la 701 asignada a docente701@example.invalid, la 702
#   a docente702@example.invalid, la 703 a docente703@example.invalid y la 704 sin profesor activo, y
#   db/datos/periodo_2026_2_inventado.sql con la 410 y la 411 de 450002 en 2026-2.
# - Las cifras del agregado salen de abet.v_r17_por_pi, con calificados igual a n_total menos n_sin_evidencia, y
#   NIVEL_ESPERADO y META_LOGRO de R-2026-BORRADOR de Industrial, nunca de constantes del código.
# - Los escenarios de pantalla los prueba Vitest en el Front y llevan @delegado_a_vitest.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.
# - Cambio del 2026-11-23 (T038). Los Antecedentes suman el plan de 5643 en 2026-1, porque la carga PUBLICADA de la
#   701 lo exige y sin él las cuatro secciones serían SIN_PLAN, como en alcance_coordinacion.feature (spec.md).

Característica: Avance y cumplimiento del curso para su coordinación
  Como coordinación de Química General, quiero ver la etapa de cada sección de mi curso y, cuando se decida, el
  cumplimiento del curso frente a la meta, para cerrar el registro a tiempo y saber si el curso cumple el PI.

  Antecedentes:
    Dado una base desechable de la spec 008 con el plan de 5643 en 2026-1 y los datos de periodo_2026_2_inventado.sql y quimica_2026_1_inventado.sql
    Y "coordinador.quimica@example.invalid" con rol "COORDINADOR", activo y con alcance de la asignatura "5643" en "2026-1"

  @spec008 @corte1 @US-79
  Escenario: La ruta 17 da la etapa de cada sección del curso y ninguna de otro curso
    Dado la 701 con una carga PUBLICADA inventada, la 702 con una sola carga RECHAZADA y la 703 sin cargas
    Y "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/avance?periodo=2026-1
    Entonces recibe 200 con Cache-Control no-store
    Y la 701 viene PUBLICADA con su carga_id, la 702 CON_RECHAZO, la 703 SIN_CARGA y la 704 SIN_PROFESOR, en ese orden
    Y el conteo dice 4 secciones, 1 PUBLICADA, 1 CON_RECHAZO, 1 SIN_CARGA, 1 SIN_PROFESOR y 0 SIN_PLAN
    Y la respuesta no trae la 410 ni la 411 de "450002" ni ningún porcentaje, nivel o código de estudiante

  @spec008 @corte1 @US-79
  Escenario: Un periodo sin secciones del curso responde vacío
    Dado "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/avance?periodo=2026-2
    Entonces recibe 200 con secciones vacías y el conteo en 0

  @spec008 @corte1 @US-79
  Escenario: El profesor del curso no lee el avance
    Dado "docente701@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando pide GET /api/avance?periodo=2026-1
    Entonces recibe 403 con «Esta página es de la Coordinación.»

  @spec008 @corte1 @US-79
  Escenario: La coordinación de Ambiental no ve el avance de Química
    Dado "coordinacion@example.invalid" con rol "COORDINADOR", activo y con alcance de la carrera "AMB"
    Y "coordinacion@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/avance?periodo=2026-1
    Entonces recibe 200 con secciones vacías

  @spec008 @corte1 @US-79 @delegado_a_vitest
  Escenario: P7 lleva el título del curso y es la llegada de su coordinación
    Dado una sesión de "coordinador.quimica@example.invalid" con rol "COORDINADOR" y alcance "CURSO"
    Y que la ruta 17 responde la 701 PUBLICADA, la 702 CON_RECHAZO, la 703 SIN_CARGA y la 704 SIN_PROFESOR de "5643" en "2026-1"
    Cuando ingresa
    Entonces llega a «Avance del registro del curso» (propuesta)
    Y P7 dice con role="status" «1 de 4 secciones con carga publicada.»
    Y muestra «701 · Publicada», «702 · La última carga se rechazó», «703 · Sin carga» y «704 · Sin profesor asignado» bajo «5643 Química General»

  @spec008 @corte1 @US-79 @delegado_a_vitest
  Escenario: Desde P7 la coordinación abre la carga publicada de una sección
    Dado una sesión de "coordinador.quimica@example.invalid" con rol "COORDINADOR" y alcance "CURSO" en P7
    Cuando pulsa «Ver la carga» en la 701
    Entonces P4 muestra la constancia de la carga de la 701 y ofrece «Descargar R-17»

  @spec008 @corte1 @US-79 @delegado_a_vitest
  Escenario: Sin la etapa B, la coordinación del curso sigue el avance en P2
    Dado una sesión de "coordinador.quimica@example.invalid" con rol "COORDINADOR" y alcance "CURSO"
    Y que la versión del Front no tiene P7
    Cuando llega a P2 «Secciones del curso»
    Entonces cada fila dice el estado de su sección con «Sin carga» o «Publicada, N de M filas aceptadas»

  @spec008 @corte1 @US-80
  Escenario: Cada sección trae su porcentaje como en su R-17
    Dado cargas PUBLICADA inventadas con estos niveles por sección
      | seccion | nivel_1 | nivel_2 | nivel_3 | nivel_4 |
      | 701     | 1       | 2       | 5       | 2       |
      | 702     | 0       | 1       | 6       | 3       |
      | 703     | 2       | 4       | 5       | 2       |
    Y "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/resultados?periodo=2026-1
    Entonces la 701 trae logrados 7, calificados 10 y pct_sobre_calificados 70.0 con en_meta falso
    Y la 702 trae logrados 9, calificados 10 y pct_sobre_calificados 90.0 con en_meta verdadero
    Y la 703 trae logrados 7, calificados 13 y pct_sobre_calificados 53.8 con en_meta falso
    Y la 704 viene SIN_CARGA con indicadores vacío

  @spec008 @corte1 @US-80
  Escenario: El agregado del curso suma estudiantes y no promedia porcentajes
    Dado las cargas PUBLICADA inventadas de la 701, la 702 y la 703 del escenario anterior
    Y D-32 respondida con la suma de estudiantes por PI y curso
    Y "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/resultados?periodo=2026-1
    Entonces agregados trae para "5643" y el PI 6.1 logrados 23, calificados 33, pct_sobre_calificados 69.7, meta_pct 80.0 y en_meta falso
    Y secciones_publicadas 3 de secciones 4
    Y el agregado no vale 71.3, el promedio de los tres porcentajes

  @spec008 @corte1 @US-80
  Escenario: Un curso sin cargas publicadas no inventa un porcentaje
    Dado ninguna carga PUBLICADA en "5643" en 2026-1
    Y "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/resultados?periodo=2026-1
    Entonces el agregado de "5643" trae calificados 0, pct_sobre_calificados null y en_meta null, nunca 0

  @spec008 @corte1 @US-80
  Escenario: El profesor no recibe el agregado del curso
    Dado las cargas PUBLICADA inventadas de la 701, la 702 y la 703
    Y "docente701@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando pide GET /api/resultados?periodo=2026-1
    Entonces recibe solo la 701 y la respuesta no trae el campo agregados, como fija D-33

  @spec008 @corte1 @US-80
  Escenario: Ninguna cifra del agregado revela a un estudiante
    Dado las cargas PUBLICADA inventadas de la 701, la 702 y la 703
    Y "coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR"
    Cuando pide GET /api/resultados?periodo=2026-1
    Entonces la respuesta no trae códigos de estudiante, nombres, correos, subida_por ni nombre_archivo

  @spec008 @corte1 @US-80 @delegado_a_vitest
  Escenario: P6 muestra el curso antes de las secciones
    Dado una sesión de "coordinador.quimica@example.invalid" con rol "COORDINADOR" y alcance "CURSO"
    Y que la ruta 12 responde el agregado de "5643" con 23 de 33, 69,7 %, meta 80 % y 3 de 4 secciones publicadas
    Cuando abre «Ver los logros por SO del curso»
    Entonces P6 dice «Curso 5643, 3 de 4 secciones publicadas» con «69,7 %» y «Debajo de la meta de 80 %» en texto además del color (propuesta)
    Y las filas 701, 702 y 703 siguen en el orden de número de sección, nunca por resultado
