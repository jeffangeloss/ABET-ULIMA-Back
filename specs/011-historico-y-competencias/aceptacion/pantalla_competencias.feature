# language: es
#
# Escenarios de aceptación de US-103 y US-104 de la spec 011-historico-y-competencias (épica EP-11, propuesta). P10
# «Competencias por estadío» dibuja lo que traen las rutas 23 y 24, con una matriz de competencia por estadío, el
# detalle de cada celda y la evolución de una competencia, sin profesores, sin radar y sin biblioteca de gráficos (J-24
# de la spec 004 y ADR-011, propuesta).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid.
#
# Vocabulario de los pasos.
# - Los escenarios de pantalla los prueba Vitest en el Front con la respuesta simulada del primer escenario de
#   competencias_por_estadio.feature y llevan @delegado_a_vitest, y los de Playwright llevan @playwright.
# - P10 escribe lo que trae la API y no recalcula ninguna cifra (BR-RESULTADOS-11). Su unidad es la medición de un
#   estudiante en un PI, y nunca escribe «alumnos».

Característica: Pantalla de las competencias por estadío
  Como coordinación de Ambiental, quiero ver una matriz de competencia por estadío con la cifra escrita en cada celda,
  para llevar al comité el logro de la carrera a lo largo de la malla.

  @spec011 @corte1 @US-103 @delegado_a_vitest
  Escenario: P10 escribe la matriz de G4 con una cifra por estadío
    Dado la respuesta de la ruta 23 de AMB en 2026-2
    Cuando la coordinación abre P10 en 2026-2
    Entonces la fila G4 dice en INICIAL «3 de 5 mediciones en el nivel esperado o superior (60,0 %)» y «Debajo de la meta»
    Y dice en REFUERZO «12 de 15 mediciones en el nivel esperado o superior (80,0 %)» y «En la meta»
    Y dice en LOGRADO «9 de 10 mediciones en el nivel esperado o superior (90,0 %)» y «En la meta»
    Y cada barra marca «Meta 80 %» y lleva aria-hidden, con su cifra escrita en la celda

  @spec011 @corte1 @US-103 @delegado_a_vitest
  Escenario: La fila de cada competencia dice su SO y sus PI medidos
    Dado la respuesta de la ruta 23 de AMB en 2026-2
    Cuando la coordinación abre P10 en 2026-2
    Entonces la fila G4 dice «G4 · SO 5 · PI 5.1, 5.2 y 5.3»

  @spec011 @corte1 @US-103 @delegado_a_vitest
  Escenario: El detalle de una celda trae sus asignaturas, secciones y PI sin profesores
    Dado la respuesta de la ruta 23 de AMB en 2026-2
    Cuando la coordinación despliega G4 en REFUERZO
    Entonces ve «450002, sección 413, 12 de 15 mediciones (80,0 %)»
    Y ve la 410, la 411 y la 412 de 450002 y la 410 y la 412 de 450010 con «Sin carga publicada» y sin barra de 0 %
    Y ve «PI 5.1, 4 de 5 (80,0 %)», «PI 5.2, 4 de 5 (80,0 %)» y «PI 5.3, 4 de 5 (80,0 %)»
    Y ve «Promedio de calificación 3,07 de 4», «1 de 1 sección publicada en la meta» y «5 secciones sin carga publicada»
    Y ninguna celda trae un correo ni el texto «Profesor Inventado»

  @spec011 @corte1 @US-103 @delegado_a_vitest
  Escenario: Una celda sin medición no dibuja una barra de 0 %
    Dado la respuesta de la ruta 23 de AMB en 2026-2
    Cuando la coordinación abre P10 en 2026-2
    Entonces G3 en REFUERZO y en LOGRADO dice «Sin medición en el periodo» y no dibuja barra ni porcentaje

  @spec011 @corte1 @US-103 @delegado_a_vitest
  Escenario: Las competencias sin SO lo dicen en la fila
    Dado la respuesta de la ruta 23 de AMB en 2026-2
    Cuando la coordinación abre P10 en 2026-2
    Entonces las filas G1, G2, G5 y G7 dicen «Sin SO asociado» y no traen celdas con cifra

  @spec011 @corte1 @US-103 @delegado_a_vitest
  Escenario: P10 rotula mediciones y marca las cifras provisionales
    Dado la respuesta de la ruta 23 de AMB en 2026-2 con provisional verdadero
    Cuando la coordinación abre P10 en 2026-2
    Entonces P10 muestra la franja «Cifras provisionales.» sobre la matriz
    Y dice «Cada medición es el nivel de un estudiante en un PI.»
    Y ninguna celda dice «alumnos»

  @spec011 @corte1 @US-103 @delegado_a_vitest
  Escenario: Una carrera sin el mapeo de competencias lo dice con texto
    Dado una cuenta COORDINADOR con alcance de la carrera IND y la respuesta de la ruta 23 de IND en 2026-1 con competencias vacía
    Cuando abre P10 en 2026-1
    Entonces lee «La carrera aún no tiene el mapeo de competencias por estadío.»
    Y no ve ninguna celda con porcentaje

  @spec011 @corte1 @US-103 @delegado_a_vitest
  Escenario: La coordinación de un curso lee que la página es de la carrera
    Dado coordinador.quimica@example.invalid con alcance CURSO
    Cuando abre la dirección «#/competencias»
    Entonces lee «Las competencias son de la coordinación de la carrera.»
    Y no ve ninguna celda con porcentaje

  @spec011 @corte1 @US-103 @delegado_a_vitest
  Escenario: P10 no ordena por resultado
    Dado la respuesta de la ruta 23 de AMB en 2026-2
    Cuando la coordinación abre P10 en 2026-2
    Entonces las filas siguen el orden de la respuesta, de G1 a G8 y de E1 a E3
    Y las columnas van INICIAL, REFUERZO y LOGRADO
    Y ningún control ordena por porcentaje

  @spec011 @corte1 @US-103 @delegado_a_vitest
  Escenario: Solo la coordinación de la carrera ve las competencias en el menú
    Dado una sesión de coordinacion@example.invalid, otra de coordinador.quimica@example.invalid y otra de docente413@example.invalid
    Cuando cada una abre el menú
    Entonces solo la coordinación de la carrera ve «Competencias por estadío»
    Y la dirección «#/competencias» lleva al profesor a su pantalla de llegada

  @spec011 @corte1 @US-104 @delegado_a_vitest
  Escenario: P10 escribe la evolución de G4 con una fila por periodo
    Dado la respuesta de la ruta 24 de G4 con 2024-2 y 2026-2
    Cuando la coordinación elige «G4» en el selector «Competencia» de P10
    Entonces ve las filas 2024-2 y 2026-2 en ese orden
    Y la fila de 2024-2 dice en REFUERZO «9 de 15 mediciones en el nivel esperado o superior (60,0 %)» y en INICIAL «Sin medición en el periodo»
    Y la fila de 2026-2 dice en REFUERZO «12 de 15 mediciones en el nivel esperado o superior (80,0 %)»

  @spec011 @corte1 @US-103 @playwright
  Escenario: P10 a 375 px solo desplaza a lo ancho la matriz y se recorre con teclado
    Dado la coordinación de la carrera en P10 con la API simulada a 375 px de ancho
    Entonces la página no se desplaza a lo ancho y solo la región «Matriz de competencias» se desplaza a lo ancho
    Y cada celda tiene su cifra en texto y el foco recorre las filas en orden
