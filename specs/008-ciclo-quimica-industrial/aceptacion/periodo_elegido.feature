# language: es
#
# Escenarios de aceptación de US-73 de la spec 008-ciclo-quimica-industrial (épica EP-08, propuesta). Cada cuenta
# elige el periodo que trabaja, sin cambiar PERIODO_VIGENTE (C-01 con C-28, C-49 y el periodo de P6 de C-08). La
# ruta 18 GET /api/periodos es nueva y la ruta 8 GET /api/cargas suma el parámetro aditivo periodo.
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid.
#
# Vocabulario de los pasos.
# - La API de los escenarios del Back corre con PERIODO_VIGENTE "2026-2", como la versión de prueba, y la base
#   tiene db/datos/periodo_2026_2_inventado.sql (410 y 411 de 450002 en 2026-2) y
#   db/datos/quimica_2026_1_inventado.sql (701 a 704 de 5643 en 2026-1).
# - La ruta 18 responde vigente y la lista de periodos con al menos una sección al alcance del usuario, del más
#   reciente al más antiguo (propuesta). Sin periodo, las rutas 4, 8, 12 y 17 usan PERIODO_VIGENTE, como hoy.
# - El selector aparece en la cabecera solo con dos periodos o más, y el periodo elegido vive en el estado de
#   App.tsx, sin localStorage ni sessionStorage (veredicto SE_SOSTIENE del crítico).
# - Los escenarios de pantalla los prueba Vitest en el Front y llevan @delegado_a_vitest.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Cada cuenta elige el periodo que trabaja
  Como profesor o coordinación de Química General, quiero trabajar en 2026-1 aunque el periodo vigente sea
  2026-2, para registrar y revisar la medición de un ciclo ya cerrado sin cambiar la configuración de la carrera.

  Antecedentes:
    Dado una base desechable de la spec 008 con los datos de periodo_2026_2_inventado.sql y quimica_2026_1_inventado.sql
    Y la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "2026-2"

  @spec008 @US-73
  Escenario: La ruta 18 lista solo los periodos con secciones al alcance de cada cuenta
    Cuando "docente701@example.invalid", "docente410@example.invalid" y "coordinador.quimica@example.invalid" piden GET /api/periodos
    Entonces "docente701@example.invalid" recibe vigente "2026-2" y periodos ["2026-1"]
    Y "docente410@example.invalid" recibe vigente "2026-2" y periodos ["2026-2"]
    Y "coordinador.quimica@example.invalid" recibe vigente "2026-2" y periodos ["2026-1"]
    Y cada respuesta lleva Cache-Control no-store, como toda /api

  @spec008 @US-73
  Escenario: Con secciones en los dos periodos los recibe del más reciente al más antiguo
    Dado que acceso.docente_seccion también asigna a "docente701@example.invalid" la 411 de "450002" en "2026-2"
    Y "docente701@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando pide GET /api/periodos
    Entonces recibe periodos ["2026-2", "2026-1"]

  @spec008 @US-73
  Escenario: Sin sesión la ruta 18 responde 401 y figura en la prueba de rutas registradas
    Dado una petición sin la cookie abet_sesion
    Cuando pide GET /api/periodos
    Entonces recibe 401 con «La sesión venció. Ingrese otra vez.» y sin datos
    Y la ruta figura en tests/rutas_registradas.py

  @spec008 @US-73
  Escenario: La ruta 8 con periodo lista solo las cargas de ese periodo y sin periodo sigue como hoy
    Dado que acceso.docente_seccion también asigna a "docente701@example.invalid" la 411 de "450002" en "2026-2"
    Y la carga PUBLICADA inventada de la 701 y una carga RECHAZADA inventada de la 411
    Y "docente701@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando pide GET /api/cargas?periodo=2026-1
    Entonces recibe la carga de la 701 y no la de la 411
    Y GET /api/cargas sin periodo devuelve solo la carga de la 411, como hoy

  @spec008 @US-73
  Esquema del escenario: Un periodo mal formado responde 422 en las rutas que lo aceptan
    Dado "docente701@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando pide <ruta>?periodo=<periodo>
    Entonces recibe 422 con «El periodo no tiene la forma AAAA-C.»

    Ejemplos:
      | ruta             | periodo |
      | GET /api/cargas  | 2026-3  |
      | GET /api/cargas  | 2026    |
      | GET /api/cargas  | 26-1    |
      | GET /api/secciones | 2026-3 |

  @spec008 @US-73
  Escenario: Un periodo sin secciones del usuario da una lista vacía y no un 403
    Dado "docente701@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando pide GET /api/cargas?periodo=2025-2
    Entonces recibe 200 con una lista vacía

  @spec008 @US-73
  Escenario: Pedir otro periodo no agrega secciones ajenas
    Dado "docente701@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando pide GET /api/secciones?periodo=2026-2
    Entonces recibe 200 con una lista vacía y no la 410 ni la 411

  @spec008 @US-73
  Escenario: La subida en una sección de 2026-1 no exige el periodo vigente
    Dado "docente701@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando sube a la 701 un export inventado cuyo curso declara 20261, 5643 y 701
    Entonces la carga queda PUBLICADA aunque PERIODO_VIGENTE sea "2026-2"

  @spec008 @US-73
  Escenario: Un export de otro periodo se rechaza con el texto de la API
    Dado "docente701@example.invalid" tiene la sesión iniciada con rol "PROFESOR"
    Cuando sube a la 701 un export inventado de texto cuyo curso declara 20262, 5643 y 701
    Entonces la carga queda RECHAZADA con PERIODO_NO_COINCIDE
    Y el mensaje es «El archivo corresponde al periodo 2026-2 y la sección elegida es de 2026-1. No se publicó.»

  @spec008 @US-73 @delegado_a_vitest
  Escenario: Sin secciones en el periodo vigente, P2 abre en el periodo más reciente con secciones
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR"
    Y que la ruta 18 responde vigente "2026-2" y periodos ["2026-1"]
    Cuando el profesor ingresa
    Entonces la cabecera muestra «Periodo 2026-1» sin selector (propuesta)
    Y P2 pide la ruta 4 con periodo=2026-1
    Y la fila dice «5643 Química General, sección 701, 2026-1»

  @spec008 @US-73 @delegado_a_vitest
  Escenario: Con dos periodos la cabecera ofrece el selector y abre en el vigente
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR"
    Y que la ruta 18 responde vigente "2026-2" y periodos ["2026-2", "2026-1"]
    Cuando el profesor ingresa
    Entonces la cabecera muestra un selector con la etiqueta «Periodo» y el valor "2026-2" (propuesta)
    Y P2 pide la ruta 4 con periodo=2026-2

  @spec008 @US-73 @delegado_a_vitest
  Escenario: Cambiar el periodo vuelve a pedir P2, P5 y P6 con el periodo elegido
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR"
    Y que la ruta 18 responde vigente "2026-2" y periodos ["2026-2", "2026-1"]
    Cuando el profesor elige "2026-1" en el selector «Periodo»
    Entonces P2 pide la ruta 4 y la ruta 8 con periodo=2026-1
    Y al abrir «Cargas» se piden la ruta 4 y la ruta 8 con periodo=2026-1
    Y al abrir «Mis logros por SO» se pide la ruta 12 con periodo=2026-1 y se ve «Cargando sus logros…» mientras espera

  @spec008 @US-73 @delegado_a_vitest
  Escenario: La marca de la última carga rechazada de P2 sale del periodo elegido
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" con "2026-1" elegido
    Y que la ruta 4 responde la 701 en SIN_CARGA y la ruta 8 con periodo=2026-1 responde una carga RECHAZADA de la 701
    Cuando abre P2
    Entonces la fila dice «La última carga se rechazó y no se publicó. Falta subir un export corregido.»

  @spec008 @US-73 @delegado_a_vitest
  Escenario: El periodo elegido se conserva en el recorrido y no se guarda en el navegador
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" con "2026-1" elegido
    Cuando sube un export en la 701, ve el resultado y pulsa «Volver a mis secciones»
    Entonces P2 sigue en "2026-1"
    Y localStorage y sessionStorage quedan con 0 entradas

  @spec008 @US-73 @delegado_a_vitest
  Escenario: Si la ruta 18 falla, P2 usa el periodo vigente como hoy y no muestra error
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR"
    Y que la ruta 18 responde 500
    Cuando el profesor ingresa
    Entonces P2 pide la ruta 4 sin periodo
    Y P2 no muestra ningún mensaje de error de la ruta 18

  @spec008 @US-73 @delegado_a_vitest
  Escenario: En un periodo sin secciones, P2 remite al selector
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" con "2026-2" elegido
    Y que la ruta 4 responde una lista vacía
    Cuando abre P2
    Entonces ve «No tiene secciones asignadas en este periodo.»
    Y debajo ve «Elija otro periodo en la cabecera si dictó una sección con medición ABET en otro ciclo.» (propuesta)

  @spec008 @US-73 @delegado_a_vitest
  Escenario: La coordinación del curso trabaja 2026-1 en P2, P5, P6 y P7
    Dado una sesión de "coordinador.quimica@example.invalid" con rol "COORDINADOR" y alcance "CURSO"
    Y que la ruta 18 responde vigente "2026-2" y periodos ["2026-1"]
    Cuando ingresa y recorre P7, P2, P5 y P6
    Entonces la ruta 17, la ruta 4, la ruta 8 y la ruta 12 se piden con periodo=2026-1
    Y el navegador no guarda el periodo elegido
