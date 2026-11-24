# language: es
#
# Escenarios de aceptación de US-90 de la spec 008-ciclo-quimica-industrial (épica EP-08, propuesta). Una matriz
# generada desde los repositorios liga cada historia y cada regla de las specs 007 y 008 con su escenario, su
# prueba y el resultado de su última corrida, para que el «no olvides nada» del pedido sea una comprobación
# repetible (C-68 corregida).
#
# Este archivo usa solo datos inventados.
#
# Vocabulario de los pasos.
# - El generador scripts/matriz_cumplimiento.py (propuesta) vive en el Back, lee specs/*/spec.md, las specs vivas de
#   specs/features/ y los .feature, y recibe la ruta del Front para buscar los escenarios @delegado_a_vitest.
# - Un hueco es una historia o una regla sin escenario y sin prueba nombrada en su línea **Prueba**. Lo que una
#   spec marca pendiente por decisión no cuenta como hueco.
# - El archivo versionado specs/008-ciclo-quimica-industrial/cumplimiento.md guarda solo la traza. El resultado y la
#   fecha de cada corrida salen de pytest --junitxml y del reporte JSON de Vitest, y quedan en el informe de la
#   integración continua, fuera del repositorio.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Matriz de cumplimiento de punta a punta
  Como Oficina de Calidad, quiero ver qué historias y reglas tienen escenario, prueba y corrida aprobada, para que
  nada del flujo de la capacitación quede olvidado.

  @spec008 @corte1 @US-90
  Escenario: Cada historia del flujo tiene escenario, prueba y corrida
    Dado US-59 con su escenario en specs/007-experiencia-por-cuenta/aceptacion/siguiente_paso.feature y su prueba aprobada en el reporte de Vitest
    Cuando se genera la matriz
    Entonces la fila de US-59 dice el archivo del escenario, la prueba y «Aprobada» con la fecha de la corrida del reporte

  @spec008 @corte1 @US-90
  Escenario: Una historia de la spec 008 sin escenario hace fallar la generación
    Dado una historia US de prueba en una copia de spec.md sin ningún escenario con su etiqueta
    Cuando se genera la matriz
    Entonces la fila de esa historia dice «Sin escenario»
    Y la generación termina con código 1

  @spec008 @corte1 @US-90
  Escenario: Una regla con prueba nombrada no es un hueco aunque no tenga escenario
    Dado BR-R17-08 en una copia de r17.spec.md cuya línea **Prueba** nombra solo test_br_r17_08_142_mediciones_llenan_la_tabla_hasta_la_fila_184 de tests/test_r17.py y ningún escenario
    Cuando se genera la matriz
    Entonces su fila dice la prueba nombrada y no cuenta como hueco

  @spec008 @corte1 @US-90
  Escenario: Un escenario delegado a Vitest se busca en el Front por su título exacto
    Dado un escenario con la etiqueta @delegado_a_vitest
    Cuando se genera la matriz con la ruta del Front
    Entonces la matriz lo busca en las pruebas de Vitest por su título exacto
    Y un título que no existe en el Front hace fallar la generación y nombra el escenario

  @spec008 @corte1 @US-90
  Escenario: Lo pendiente por decisión se distingue de lo olvidado
    Dado US-66, que espera a D-47 y a D-51
    Cuando se genera la matriz
    Entonces su fila dice «Pendiente por decisión» y no cuenta como hueco

  @spec008 @corte1 @US-90
  Escenario: Una etiqueta que no liga con ninguna historia hace fallar la generación
    Dado un escenario de prueba con la etiqueta @US-999
    Cuando se genera la matriz
    Entonces la generación termina con código 1 y nombra la etiqueta

  @spec008 @corte1 @US-90
  Escenario: El tramo de la capacitación queda en una sola vista
    Cuando se genera la matriz
    Entonces su primera tabla lista, en el orden del flujo, el catálogo, el alcance, el periodo, el generador, la carga, el R-17, el avance, el sistema visual, la conciliación, el ensayo, la siembra, el humo, la guía, la privacidad y el cierre, con el estado de cada uno

  @spec008 @corte1 @US-90
  Escenario: La integración continua corre la matriz y el archivo versionado no cambia con cada corrida
    Cuando la integración continua genera la matriz dos veces con resultados de corrida distintos
    Entonces cumplimiento.md sale igual las dos veces
    Y la fecha y el resultado de cada corrida quedan solo en el informe de la integración continua

  @spec008 @corte1 @US-90
  Escenario: La matriz no trae datos reales
    Cuando se genera la matriz
    Entonces la matriz no trae ningún número de ocho cifras ni ningún correo fuera de example.invalid
