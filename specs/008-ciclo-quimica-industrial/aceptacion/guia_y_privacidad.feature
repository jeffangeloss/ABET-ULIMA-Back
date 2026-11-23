# language: es
#
# Escenarios de aceptación de US-87 y US-88 de la spec 008-ciclo-quimica-industrial (épica EP-08, propuesta). La
# guía de la capacitación por rol cita los rótulos exactos del Front, con una prueba que la coteja con src y un
# ejercicio de error con un export inventado (US-87, C-63 corregida con el veredicto CAMBIAR del crítico), y cada
# cambio de los dos repositorios se detiene si trae un dato real, el correo real de la coordinación o una captura
# (US-88, C-64 corregida, con la tarjeta de C-63 y las capturas de C-62).
#
# Este archivo usa solo datos inventados. El correo real de la coordinación nunca se escribe en el repositorio ni
# en la prueba, y la prueba usa la huella SHA-256 del correo inventado real.inventado@example.invalid, leída de una
# variable de entorno. Ningún código de estudiante fuera del rango 99 aparece escrito aquí, porque la prueba los
# arma en tmp_path, salvo 10000004, que está en la lista cerrada CODIGOS_DE_PRUEBA de las pruebas de la guardia
# de la spec 001.
#
# Vocabulario de los pasos.
# - La guía vive en docs/capacitacion/guia_quimica.md del Front (propuesta), con solo correos de ejemplo, y la
#   tarjeta de cada profesor (sección, correo de ejemplo, nombre del archivo de su export y el camino para recibir
#   la contraseña) vive fuera de los repositorios. La correspondencia entre cada correo de ejemplo y la persona
#   que lo usa tampoco entra a git.
# - La prueba de cotejo de la guía corre con Vitest en el Front y lleva @delegado_a_vitest. Los escenarios del
#   barrido corren scripts/preflight.sh del Back y del Front sobre una copia de prueba en tmp_path.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Guía de la capacitación y barrido de privacidad
  Como Oficina de Calidad, quiero una guía por rol que hable con los rótulos que ven los profesores y unos
  repositorios que rechacen todo dato real, para que nadie se pierda en la sala y la capacitación no deje rastros
  en git.

  @spec008 @US-87 @delegado_a_vitest
  Escenario: Cada rótulo citado en la guía existe en el Front
    Dado la guía con rótulos entre comillas latinas como «Subir export», «Antes de subir», «Descargar R-17», «Reemplazar carga» y «Avance del registro del curso»
    Cuando corre la prueba que coteja la guía con src
    Entonces cada rótulo citado aparece en src/pantallas o en src/servicios

  @spec008 @US-87 @delegado_a_vitest
  Escenario: Un rótulo cambiado en el Front hace fallar la guía
    Dado un cambio del Front que reemplaza «Descargar R-17» por «Bajar R-17»
    Cuando corre la prueba que coteja la guía con src
    Entonces la prueba falla y nombra «Descargar R-17» y la línea de la guía que lo cita

  @spec008 @US-87 @delegado_a_vitest
  Escenario: La guía no trae datos que no debe
    Cuando corre la prueba que coteja la guía con src
    Entonces la guía no trae ningún correo fuera de example.invalid
    Y no trae ningún número de ocho cifras
    Y no trae ninguna contraseña

  @spec008 @US-87 @delegado_a_vitest
  Escenario: Una fecha sin confirmar se dice como tal
    Dado J-56 abierta, con la fecha de la capacitación sin confirmar
    Cuando corre la prueba que coteja la guía con src
    Entonces la portada de la guía dice «Fecha por confirmar» y «Versión de prueba (develop)»

  @spec008 @US-87 @delegado_a_vitest
  Escenario: La guía del profesor sigue el flujo en el orden de las pantallas
    Cuando corre la prueba que coteja la guía con src
    Entonces la sección del profesor nombra, en este orden, «Ingresar», «Mis secciones», «Subir export», «Antes de subir», «Resultado de la carga», «Descargar R-17» y «Mis logros por SO»

  @spec008 @US-87 @playwright
  Escenario: El profesor sigue la guía de su rol de punta a punta en la vista previa
    Dado la tarjeta inventada de "docente701@example.invalid" con la 701 y el archivo "gc_SINTETICO_20261_5643_701_fullgc_2026-07-15-00-00-00.xlsx"
    Cuando el profesor sigue los pasos de su rol en la vista previa con la siembra inventada
    Entonces ingresa, elige la 701 en P2, lee «Antes de subir» en P3, sube su archivo, ve la carga publicada en P4 y descarga el R-17

  @spec008 @US-87 @playwright
  Escenario: El ejercicio de error usa un export inventado y enseña a leer «Qué corregir»
    Dado el archivo de ejercicio inventado de la sección ficticia 799 de "5643" en 2026-1, generado con --ejercicio
    Cuando "docente701@example.invalid" lo sube en la 701
    Entonces P4 muestra «El archivo corresponde a la sección 799 y usted eligió la 701. No se publicó.»
    Y debajo «Qué corregir. Exporte el Centro de calificaciones de 5643, sección 701, o suba este archivo en la sección que le corresponde.»
    Y la guía dice a continuación «Suba ahora el archivo de su sección.»
    Y la 701 conserva «Subir export» activo y abet.medicion no gana filas de la 701

  @spec008 @US-87 @delegado_a_vitest
  Escenario: La guía de la coordinación del curso no promete correos sin D-51
    Dado D-51 sin respuesta
    Cuando corre la prueba que coteja la guía con src
    Entonces la sección de la coordinación dice cómo leer «N de M secciones con carga publicada.» y cómo abrir «Ver la carga»
    Y no describe la copia de los correos de los profesores

  @spec008 @US-87
  Escenario: Cada tarjeta de profesor nombra el archivo de su sección según el manifiesto
    Dado el manifiesto inventado del generador y las tarjetas inventadas en tmp_path
    Cuando corre scripts/generar_exports_desde_maestra.py con --tarjetas (propuesta)
    Entonces cada tarjeta nombra la sección y el archivo que el manifiesto da para esa sección
    Y una tarjeta con el archivo de otra sección hace fallar la comprobación y la nombra

  @spec008 @US-88
  Escenario: El correo prohibido se detecta por su huella sin imprimirlo
    Dado la variable HUELLAS_CORREOS_PROHIBIDOS con la huella SHA-256 del correo normalizado "real.inventado@example.invalid"
    Y un cambio preparado que agrega "Real.Inventado@Example.invalid" a un archivo de specs
    Cuando corre scripts/preflight.sh --staged
    Entonces el control falla y nombra el archivo y su línea
    Y la salida no repite el correo

  @spec008 @US-88
  Escenario: Sin la variable de huellas el control avisa y no falla
    Dado HUELLAS_CORREOS_PROHIBIDOS sin definir
    Cuando corre scripts/preflight.sh
    Entonces la salida dice «Sin huellas de correos prohibidos. La regla del correo real no se revisó.» (propuesta)

  @spec008 @US-88
  Esquema del escenario: Un código de ocho cifras fuera del rango inventado detiene el cambio en specs, pruebas, e2e y docs
    Dado un cambio preparado que agrega <texto> a <archivo>
    Cuando corre scripts/preflight.sh --staged
    Entonces el control <resultado>

    Ejemplos:
      | texto                                                          | archivo                                      | resultado                 |
      | un código de ocho cifras que empieza con 20, armado por la prueba | specs/008-ciclo-quimica-industrial/aceptacion/prueba.feature | falla y nombra el archivo |
      | un código de ocho cifras que empieza con 20, armado por la prueba | e2e/humo_quimica.spec.ts                     | falla y nombra el archivo |
      | "99000001"                                                     | specs/008-ciclo-quimica-industrial/aceptacion/prueba.feature | pasa                      |
      | una huella SHA-256 de 64 caracteres con ocho cifras seguidas   | specs/008-ciclo-quimica-industrial/aceptacion/prueba.feature | pasa                      |
      | "2026-11-23"                                                   | MEMORIA.md                                   | pasa                      |
      | "9000061" de siete cifras                                      | specs/008-ciclo-quimica-industrial/aceptacion/prueba.feature | pasa                      |
      | "10000004"                                                     | specs/001-mvp-carga-r17/aceptacion/carga.feature | pasa                      |
      | una línea sin cifras, junto a un color de ocho cifras ya versionado, | tests/test_plantilla_r17.py                  | pasa                      |

  @spec008 @US-88
  Escenario: Una captura o un resultado de Playwright no se versionan
    Dado un cambio preparado que agrega e2e/capturas/P4_701.png o test-results/trace.zip
    Cuando corre scripts/preflight.sh --staged
    Entonces el control falla y nombra el archivo

  @spec008 @US-88
  Escenario: La tabla maestra no entra por otro nombre y los archivos legítimos pasan
    Dado un cambio preparado que agrega docs/maestra.csv cuya primera línea trae «CÓDIGO DEL ESTUDIANTE» y «CALIFICACIÓN»
    Cuando corre scripts/preflight.sh --staged
    Entonces el control falla y nombra docs/maestra.csv
    Y db/migration/R__vista_tabla_maestra_pi.sql y los .feature que nombran esas columnas pasan

  @spec008 @US-88
  Escenario: Una tarjeta de profesor dentro del repositorio se rechaza
    Dado un cambio preparado que agrega docs/capacitacion/tarjeta_701.md
    Cuando corre scripts/preflight.sh --staged
    Entonces el control falla y nombra la tarjeta

  @spec008 @US-88
  Escenario: La regla nueva no da falsos positivos en el contenido actual
    Cuando scripts/preflight.sh corre sobre todo el contenido actual del Back y del Front y con --pr origin/develop sobre el cambio de la spec 008
    Entonces no encuentra ningún correo prohibido ni ninguna captura
    Y la regla de ocho cifras no marca los valores de CODIGOS_DE_PRUEBA ni los colores y decimales que ya estaban versionados

  @spec008 @US-88
  Escenario: El historial publicado no trae el correo prohibido
    Cuando corre una vez el barrido del historial de los dos repositorios antes de publicar la spec 008
    Entonces ningún commit de develop ni de main trae un correo con la huella prohibida
