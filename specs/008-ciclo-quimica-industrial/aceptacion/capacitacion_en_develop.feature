# language: es
#
# Escenarios de aceptación de US-85, US-86 y US-89 de la spec 008-ciclo-quimica-industrial (épica EP-08,
# propuesta). El humo con Playwright recorre de punta a punta la vista previa de develop con un profesor y con la
# coordinación del curso (US-85, C-62 corregida), la siembra de Química en la rama develop de Neon sale del
# Windows de Jefferson en orden, repetible y sin cambiar Ambiental (US-86, C-46 con C-43), y el cierre de la
# capacitación da de baja las cuentas de ejemplo y comprueba el respaldo sin borrar nada (US-89, la parte a de
# C-67, con el veredicto CAMBIAR del crítico).
#
# Este archivo usa solo datos inventados. El humo usa la siembra inventada (db/datos/quimica_2026_1_inventado.sql,
# 701 a 704 de 5643 en 2026-1 con docente701@example.invalid a docente703@example.invalid y la coordinación
# coordinador.quimica@example.invalid). La siembra real usa el mismo procedimiento con el CSV de la programación de
# las 18 secciones, que vive fuera del repositorio con correos de ejemplo de la forma docenteNNN@example.invalid, y
# con el correo real de la coordinación en la variable CORREO_COORDINACION, que lleva en_windows.py.
#
# Vocabulario de los pasos.
# - La ventana de la capacitación sigue el valor provisional de J-56. El humo corre una sola vez en develop con la
#   siembra inventada, después Jefferson restablece la rama develop de Neon, vuelve a sembrar desde V1_12 antes de
#   que la vista previa se use, siembra Química con los datos de la capacitación y congela develop hasta el
#   12-12-2026, sin otro restablecimiento ni otro humo que suba cargas.
# - Toda escritura en Neon sale del Windows de Jefferson con los ayudantes de herramientas_neon y
#   las claves por en_windows.py. Las contraseñas las escribe Jefferson con getpass en asignar_claves.py.
# - Los escenarios con @playwright corren en e2e/ del Front contra la vista previa de develop. Los demás corren con
#   pytest-bdd en una base desechable que imita la rama develop.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: La capacitación de Química General corre en la versión de prueba
  Como equipo del sistema y Oficina de Calidad, quiero sembrar Química en develop con orden, probar el recorrido
  completo antes de la sala y cerrar la capacitación sin perder evidencia, para que los 18 profesores registren su
  medición sin sorpresas y sin cambiar Ambiental.

  @spec008 @corte1 @US-86
  Escenario: La siembra completa deja la misma huella de Ambiental y los controles limpios
    Dado una base desechable que imita la rama develop, con V1_01 a V1_11, la 410 y la 411 de 450002 y una carga PUBLICADA inventada de la 410
    Y la huella de Ambiental tomada con db/plataforma/neon/huella_ambiental.sql
    Cuando se aplican en orden V1_12, V1_13, V1_14 con alcance_coordinacion_ambiental.sql, el plan de Química, la programación inventada y la coordinación inventada, cada paso primero en seco
    Entonces huella_ambiental.sql devuelve la misma huella que antes
    Y controles_neon.sql termina con «RESULTADO: Q01 a Q14 y Q18 a Q21 devuelven 0 filas.» (propuesta)
    Y el R-17 de la carga de la 410 sale con las mismas celdas que antes, comparadas una por una

  @spec008 @corte1 @US-86
  Escenario: El alcance de Ambiental queda antes que la vigencia de Industrial
    Dado la lista ordenada de pasos de la siembra
    Cuando se revisa el orden
    Entonces V1_14 y alcance_coordinacion_ambiental.sql corren antes del despliegue del Back con el _ALCANCE nuevo
    Y el despliegue corre antes de plan_quimica_2026_1.sql, que registra la vigencia de IND-2026 en 2026-1

  @spec008 @corte1 @US-86
  Escenario: La programación de Química acepta 2026-1 y una asignatura de cuatro cifras
    Dado el CSV inventado de la programación con la 701, la 702 y la 703 de "5643" en "2026-1" y su curso_blackboard
    Cuando cargar_programacion.py corre con --periodo 2026-1 y --aplicar
    Entonces abet.seccion gana las tres secciones con su curso_blackboard
    Y "docente701@example.invalid" recibe solo la 701 en GET /api/secciones?periodo=2026-1
    Y la consulta de control Q21 devuelve 0 filas

  @spec008 @corte1 @US-86
  Escenario: Una segunda siembra completa no suma filas
    Dado que la siembra completa ya corrió
    Cuando corre otra vez con los mismos archivos
    Entonces cada informe resume 0 filas nuevas
    Y el número de filas de cada tabla de abet y de acceso es el mismo que antes

  @spec008 @corte1 @US-86
  Escenario: Un paso que falla deja la base como estaba en ese paso y detiene los siguientes
    Dado un CSV de programación con una fila de sección "0701"
    Cuando la siembra llega a la programación con --aplicar
    Entonces la programación termina con código 1 con «Fila 2. El número de sección 0701 no es válido.»
    Y abet.seccion no gana ninguna fila
    Y la coordinación y las contraseñas no corren

  @spec008 @corte1 @US-86
  Escenario: La rama principal exige una confirmación aparte
    Cuando un paso que escribe recibe --rama principal sin --confirmo-principal
    Entonces termina con código 2 antes de conectarse

  @spec008 @corte1 @US-86
  Escenario: Ninguna salida de la siembra repite el correo de la coordinación
    Dado la variable CORREO_COORDINACION con "real.inventado@example.invalid"
    Cuando la siembra corre el registro de la coordinación con en_windows.py
    Entonces ni los informes ni la salida de en_windows.py muestran el valor de esa variable

  @spec008 @corte1 @US-86
  Escenario: La versión de prueba acepta los códigos que no empiezan con 99
    Dado la API de la versión de prueba con GUARDIA_DATOS_INVENTADOS "0", como fija D-10
    Cuando la comprobación previa de la siembra pide la configuración de la API
    Entonces informa que la guardia de datos inventados está apagada, sin mostrar ninguna otra variable
    Y con GUARDIA_DATOS_INVENTADOS "1" la comprobación se detiene antes de sembrar con «La guardia de datos inventados está encendida y rechazaría los códigos de la capacitación.» (propuesta)
    Y la comprobación informa que abet.estudiante no tiene ck_estudiante_codigo_inventado en la rama develop, y se detiene si la tiene, con «La base conserva la guardia de datos inventados.» (propuesta)

  @spec008 @corte1 @US-86
  Escenario: Después de la siembra de la capacitación, una lectura sin correos confirma el alcance
    Dado la rama develop con la siembra de la capacitación
    Cuando lectura_neon.sh corre desde el Windows la consulta de comprobación (propuesta)
    Entonces cuenta 18 secciones de 5643 en 2026-1 con plan, 18 filas de acceso.docente_seccion con 18 profesores distintos y 1 fila de alcance de 5643 en 2026-1 que cubre las 18
    Y la salida no trae correos ni códigos

  @spec008 @corte1 @US-85 @playwright
  Escenario: El profesor sube su export y descarga su R-17 en la vista previa
    Dado la vista previa de develop con la siembra inventada y la clave de omisión de la protección leída sin mostrarla
    Y el export inventado "gc_SINTETICO_20261_5643_701_fullgc_2026-07-15-00-00-00.xlsx" generado con US-74
    Cuando "docente701@example.invalid" ingresa en la vista previa
    Entonces la cabecera muestra «Periodo 2026-1» y P2 muestra solo la 701 de "5643" con «Falta subir el export de Blackboard de esta sección.»
    Cuando pulsa «Subir export» en la 701
    Entonces P3 dice «En Blackboard, una columna por PI, con el nombre ABET SO6.1.»
    Cuando sube el export inventado de la 701
    Entonces P4 muestra la carga PUBLICADA con 0 filas rechazadas y ofrece «Descargar R-17»
    Y el R-17 descargado dice «Carrera de Ingeniería Industrial» en B6

  @spec008 @corte1 @US-85 @playwright
  Escenario: El profesor no alcanza otra sección del curso
    Dado "docente702@example.invalid" sube en la vista previa el export inventado de la 702 generado con US-74
    Y la sesión de "docente701@example.invalid" en la vista previa
    Cuando pide la ruta 4 de 2026-1 y la ruta 7 de la carga de la 702
    Entonces la ruta 4 trae solo la 701
    Y la ruta 7 responde 403 con «La sección no está a su cargo.»

  @spec008 @corte1 @US-85 @playwright
  Escenario: La coordinación del curso ve las secciones del curso y el avance
    Dado la carga PUBLICADA de la 701 del primer escenario y la de la 702 del segundo
    Cuando "coordinador.quimica@example.invalid" ingresa en la vista previa
    Entonces llega a «Avance del registro del curso» y P7 dice «2 de 4 secciones con carga publicada.»
    Y la ruta 4 de 2026-1 trae 4 secciones, todas de "5643"
    Cuando pulsa «Ver la carga» en la 701
    Entonces P4 ofrece «Descargar R-17» y el R-17 tiene las mismas celdas que el que descargó el profesor

  @spec008 @corte1 @US-85 @playwright
  Escenario: Sin la etapa B, la coordinación del curso se comprueba en P2
    Dado la vista previa sin P7
    Cuando "coordinador.quimica@example.invalid" ingresa en la vista previa
    Entonces llega a «Secciones del curso» con 4 secciones de "5643" y ningún botón «Subir export»

  @spec008 @corte1 @US-85 @playwright
  Escenario: La coordinación del curso no sube en una sección ni ve otro curso
    Dado la sesión de "coordinador.quimica@example.invalid" en la vista previa
    Cuando pide la ruta 5 con el export inventado de la 703 y la ruta 4 de 2026-2
    Entonces la ruta 5 responde 403 con «La sección no está a su cargo.»
    Y la ruta 4 de 2026-2 no trae la 410 ni la 411 de "450002"
    Y lectura_neon.sh desde el Windows cuenta en abet.carga las mismas filas que antes de la ruta 5

  @spec008 @corte1 @US-85 @playwright
  Escenario: Las capturas y los resultados no guardan nada sensible
    Cuando termina la prueba de humo
    Entonces la carpeta temporal de resultados de Playwright y el archivo temporal de contraseñas ya no existen
    Y las capturas quedan fuera de los dos repositorios
    Y ninguna captura muestra un campo de contraseña con texto

  @spec008 @corte1 @US-85 @playwright
  Escenario: Una vista previa ya usada se detiene antes de subir
    Dado la 701 con una carga PUBLICADA de una corrida anterior
    Cuando empieza la prueba de humo
    Entonces se detiene antes de la ruta 5 con «La 701 ya tiene una carga publicada. Restablezca la rama develop de Neon antes de otra corrida.» (propuesta)

  @spec008 @corte1 @US-85 @playwright
  Escenario: Con la siembra de la capacitación el humo no corre
    Dado la rama develop marcada con la siembra de la capacitación (propuesta)
    Cuando empieza la prueba de humo
    Entonces se detiene antes de ingresar con «develop tiene la siembra de la capacitación y está congelada hasta el 12-12-2026 (J-56).» (propuesta)

  @spec008 @corte1 @US-89
  Escenario: Las cuentas de ejemplo se dan de baja en seco primero y pierden su sesión
    Dado una base desechable con la siembra inventada, la sesión vigente de "docente701@example.invalid" y una carga PUBLICADA de la 701
    Cuando db/herramientas/cerrar_capacitacion.py corre con el CSV de la programación sin --aplicar (propuesta)
    Entonces el informe dice que daría de baja 3 cuentas de profesor y 1 de coordinación, sin repetir los correos
    Y ninguna cuenta cambia
    Cuando corre con --aplicar
    Entonces las 4 cuentas quedan con activo falso
    Y la ruta 2 con la cookie de "docente701@example.invalid" responde 401
    Y la ruta 1 con su correo responde el mismo 401 que un correo desconocido
    Y la carga PUBLICADA de la 701 sigue PUBLICADA

  @spec008 @corte1 @US-89
  Escenario: El cierre comprueba el respaldo por huella y no borra nada
    Dado una carpeta inventada de la capacitación en tmp_path con 3 exports y su manifiesto
    Y un respaldo inventado cuyas huellas coinciden con el manifiesto
    Cuando el cierre comprueba el respaldo
    Entonces dice «3 de 3 archivos respaldados y comprobados por su huella. Se pueden borrar de la Mac.» (propuesta)
    Y los 3 exports siguen en la carpeta

  @spec008 @corte1 @US-89
  Escenario: Un respaldo incompleto se informa y no se recomienda borrar
    Dado un respaldo inventado al que le falta un export del manifiesto
    Cuando el cierre comprueba el respaldo
    Entonces dice «El respaldo no trae 1 archivo del manifiesto. No borre nada todavía.» (propuesta)
    Y termina con código 1

  @spec008 @corte1 @US-89
  Escenario: Sin decisión sobre el destino de las cargas, el cierre no toca develop ni main
    Dado D-55 sin respuesta
    Cuando el cierre corre con --aplicar
    Entonces no restablece develop ni escribe en main
    Y dice «Destino de las cargas de Química General pendiente de decisión (D-55).» (propuesta)

  @spec008 @corte1 @US-89
  Escenario: Después del cierre la conciliación de develop sigue disponible
    Dado el cierre ya corrido con --aplicar
    Cuando el conciliador de US-83 corre sobre develop con el rol abet_respaldo
    Entonces lee las cargas PUBLICADA de 5643 en 2026-1 como antes del cierre
