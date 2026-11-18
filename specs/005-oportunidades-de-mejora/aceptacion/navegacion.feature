# language: es
#
# Escenarios de aceptación de la navegación con el botón atrás, de la historia de usuario (user story, US)
# US-52 de la spec 005-oportunidades-de-mejora (épica EP-05, propuesta). Jefferson pide el 2026-11-18 que el
# botón atrás del navegador lleve a la pantalla anterior de la aplicación y no saque al usuario de la página
# (C-09, parte A, de la síntesis de la auditoría).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid. Ninguna
# contraseña aparece escrita aquí, porque la prueba inicia las sesiones con una contraseña generada al azar,
# sin guardarla en el repositorio.
#
# Vocabulario de los pasos, el de las pantallas del Front de la spec 001 (P1 a P5) y el de la spec 004 (P6).
# - P1 es el ingreso, P2 «Mis secciones», P3 la subida, P4 el resultado de una carga («Ver constancia»), P5
#   «Cargas» y P6 «Mis logros por SO».
# - (J-34, propuesta) src/App.tsx guarda cada pantalla en el fragmento de la dirección con history.pushState y
#   la recupera con popstate, sin tocar vercel.json. Las rutas son #/secciones (P2), #/cargas (P5),
#   #/secciones/{seccion_id}/subir y #/secciones/{seccion_id}/subir?reemplaza={carga_id} (P3),
#   #/cargas/{carga_id} (P4) y #/logros (P6).
# - history.state lleva solo la ruta y una marca del ingreso, nunca la constancia ni el borrador. Cada pantalla
#   vuelve a pedir sus datos. Una entrada de otro ingreso o un fragmento desconocido llevan a P2, y P3
#   recargada cae a P2 porque necesita la sección. Sin usuario la App muestra P1 con cualquier fragmento.
# - Las pruebas del Front reinician el fragmento en tests/preparar.ts.
# - Los cinco escenarios se prueban con Vitest en el Front y aquí quedan como criterio escrito. Todos llevan
#   @delegado_a_vitest.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: El botón atrás del navegador vuelve a la pantalla anterior de la aplicación
  Como usuario, quiero que el botón atrás del navegador me lleve a la pantalla anterior de la aplicación,
  para no salir de la página.

  Antecedentes:
    Dado que "docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR" y acceso.docente_seccion le asigna la sección 410 de "450002" en "2026-2"
    Y la aplicación abierta en P2 «Mis secciones» con el fragmento #/secciones

  @US-52 @spec005 @corte1 @delegado_a_vitest
  Escenario: Atrás recorre las pantallas visitadas y adelante las recupera
    Cuando el usuario abre P5 «Cargas», después «Ver constancia» (P4) de una carga, y pulsa atrás dos veces
    Entonces la primera vez la aplicación muestra P5 y la segunda muestra P2
    Y al pulsar adelante la aplicación vuelve a mostrar P5
    Y ninguna de las pulsaciones sale de la aplicación ni pide otra vez la sesión

  @US-52 @spec005 @corte1 @delegado_a_vitest
  Escenario: Después de una subida, atrás lleva a P2 sin repetir el POST
    Dado que el usuario abre P3 de la sección 410 y sube "sintetico_20262_450002_410.xlsx" con respuesta 201
    Cuando la subida termina en P4 y el usuario pulsa atrás
    Entonces la aplicación muestra P2
    Y el navegador no envía otra vez POST /api/secciones/{sección 410}/cargas
    Y P4 reemplazó la entrada de P3 en el historial solo porque la pantalla visible seguía siendo esa subida

  @US-52 @spec005 @corte1 @delegado_a_vitest
  Escenario: La subida en modo reemplazo guarda la carga que reemplaza en la dirección
    Dado que el usuario abre P5 y elige reemplazar la carga A
    Cuando la aplicación muestra P3 en modo reemplazo
    Entonces la dirección trae #/secciones/{seccion_id}/subir?reemplaza={A}
    Cuando la subida termina en P4 de la carga nueva y el usuario pulsa atrás
    Entonces la aplicación vuelve a P5

  @US-52 @spec005 @corte1 @delegado_a_vitest
  Escenario: Un fragmento a una carga ajena muestra el 403 de P4
    Cuando el usuario escribe en la dirección el fragmento #/cargas/999
    Entonces P4 muestra «La sección no está a su cargo.»

  @US-52 @spec005 @corte1 @delegado_a_vitest
  Escenario: Después de salir, atrás muestra el ingreso y ninguna sección
    Dado que el usuario recorrió P2 y P5
    Cuando pulsa «Salir» y después atrás
    Entonces la aplicación muestra P1
    Y la aplicación no muestra ninguna sección
    Y la dirección de P1 es #/ tras el replaceState de la salida
