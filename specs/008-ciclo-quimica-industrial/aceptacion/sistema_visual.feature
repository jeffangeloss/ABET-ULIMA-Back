# language: es
#
# Escenarios de aceptación de US-81 y US-82 de la spec 008-ciclo-quimica-industrial (épica EP-08, propuesta).
# Las pantallas comparten un sistema visual claro y accesible con contraste AA, con P2 que muestra el camino de
# cada sección y su paso actual (US-81, la parte a de C-09 con C-02 y la fila de P6 de C-08), y se usan a 375 px
# y con teclado (US-82, la parte b de C-09, que retoma C-T06 de la spec 007 sin axe-core).
#
# Este archivo usa solo datos inventados, con correos del dominio reservado example.invalid.
#
# Vocabulario de los pasos.
# - La dirección visual sale de la skill frontend-design. Los tokens de color, tipografía y espaciado viven como
#   valores literales en el bloque @theme de src/index.css, con Tailwind 4 y sin dependencias nuevas, para que una
#   función propia calcule el contraste sin navegador (veredicto SE_SOSTIENE del crítico). La tipografía usa
#   fuentes del sistema (J-59, valor provisional).
# - AA es el nivel de conformidad de las pautas de accesibilidad para el contenido web (Web Content Accessibility
#   Guidelines, WCAG) 2.2 que pide 4,5 a 1 en el texto normal y 3 a 1 en los componentes y gráficos.
# - Los rótulos que citan los .feature de las specs 001 a 007 no cambian (FR-003 de la spec 007), y las pruebas de
#   Vitest de la spec 007 pasan sin cambios, salvo las que nombra FR-019 de esta spec.
# - Los escenarios con @delegado_a_vitest los prueba Vitest en el Front, y los que llevan @playwright los prueba
#   Playwright 1.64.1 en e2e/ del Front, con la API simulada.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.
# - Cambio del 2026-11-23 (cierre de la construcción). La ruta 17 responde 403 al profesor (BR-ACCESO-12), así que la
#   fila de P7 del esquema «Cada estado de una pantalla usa su componente y su rol» la abre la coordinación del curso.
#   El esquema suma las columnas cuenta y rol_de_la_cuenta, sin cambiar sus seis filas ni el título de la prueba.
# - Cambio del 2026-11-23 (cierre del segundo bloque, T048). «Antes de subir» es una sección sin controles, y volverla
#   enfocable sería un defecto de accesibilidad, así que el escenario del foco de P3 la lee entre el periodo y el archivo
#   sin que tome el foco. El orden real empieza en «Salir», que encabeza la página antes del menú.

Característica: Sistema visual claro, accesible y usable en cualquier pantalla
  Como profesor o coordinación que usa el sistema una o dos veces por ciclo, quiero pantallas con jerarquía
  clara, estados reconocibles, foco visible y buen contraste también en el celular, para completar el registro
  sin perderme.

  @spec008 @corte1 @US-81 @delegado_a_vitest
  Escenario: Los pares de color de texto y fondo cumplen el contraste AA
    Dado los tokens de color de src/index.css
    Cuando una prueba calcula la razón de contraste de cada par de texto y fondo que usan las pantallas
    Entonces cada par de texto normal tiene al menos 4,5 a 1
    Y el borde de los campos, el anillo de foco y la marca de la meta tienen al menos 3 a 1 contra su fondo

  @spec008 @corte1 @US-81 @delegado_a_vitest
  Esquema del escenario: Cada estado de una pantalla usa su componente y su rol
    Dado una sesión de "<cuenta>" con rol "<rol_de_la_cuenta>"
    Y que la ruta de <pantalla> está <estado>
    Cuando esa cuenta abre <pantalla>
    Entonces ve el componente de <estado> con el rol "<rol>"

    Ejemplos:
      | pantalla | estado    | rol    | cuenta                              | rol_de_la_cuenta |
      | P2       | esperando | status | docente701@example.invalid          | PROFESOR         |
      | P2       | en 500    | alert  | docente701@example.invalid          | PROFESOR         |
      | P4       | esperando | status | docente701@example.invalid          | PROFESOR         |
      | P5       | esperando | status | docente701@example.invalid          | PROFESOR         |
      | P6       | en 500    | alert  | docente701@example.invalid          | PROFESOR         |
      | P7       | esperando | status | coordinador.quimica@example.invalid | COORDINADOR      |

  @spec008 @corte1 @US-81 @delegado_a_vitest
  Escenario: Los rótulos fijados no cambian con el rediseño
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR"
    Cuando se recorren Ingreso, P2, P3, P4, P5 y P6
    Entonces siguen los textos «ABET ULIMA, carga del R-17», «Mis secciones», «Subir export», «Antes de subir», «Resultado de la carga», «Volver a mis secciones», «Sin carga», «Descargar R-17» y «Mis logros por SO»
    Y las pruebas de Vitest de la spec 007 pasan sin cambios, salvo las que nombra FR-019

  @spec008 @corte1 @US-81 @delegado_a_vitest
  Esquema del escenario: La tarjeta de P2 muestra el camino de la sección y su paso actual
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" y la sección 701 de "5643" en "2026-1"
    Y que la ruta 4 responde la 701 con tiene_plan true, estado "<estado>", filas_aceptadas <aceptadas> y filas_leidas <leidas>
    Y que la ruta 8 responde para la 701 las cargas en estado "<cargas>"
    Cuando el profesor abre P2
    Entonces la tarjeta lista «1. Subir el export» con la marca «<paso1>» y «2. Revisar el resultado y descargar el R-17» con la marca «<paso2>» (propuesta)
    Y el paso actual lleva aria-current="step"
    Y la tarjeta conserva el texto «<texto_actual>» y la línea «<lo_que_falta>» de US-59

    Ejemplos:
      | estado    | aceptadas | leidas | cargas    | paso1    | paso2     | texto_actual                        | lo_que_falta                                                                     |
      | SIN_CARGA |           |        | ninguna   | Ahora    | Pendiente | Sin carga                           | Falta subir el export de Blackboard de esta sección.                             |
      | SIN_CARGA |           |        | RECHAZADA | Corregir | Pendiente | Sin carga                           | La última carga se rechazó y no se publicó. Falta subir un export corregido.     |
      | PUBLICADA | 34        | 34     | PUBLICADA | Hecho    | Ahora     | Publicada, 34 de 34 filas aceptadas | Revise el resultado de la carga para completar lo que falte y descargar el R-17. |

  @spec008 @corte1 @US-81 @delegado_a_vitest
  Escenario: El botón principal de la tarjeta es el del paso actual
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" y la sección 701 de "5643" en "2026-1"
    Y que la ruta 4 responde la 701 en estado "PUBLICADA" con su carga_id
    Cuando el profesor abre P2
    Entonces «Ver resultado» tiene el estilo del botón principal
    Y «Subir export» queda como botón secundario y sigue activo

  @spec008 @corte1 @US-81 @delegado_a_vitest
  Escenario: Una sección sin plan no muestra pasos y conserva su texto
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" y la sección 701 de "5643" en "2026-1"
    Y que la ruta 4 responde la 701 con tiene_plan false
    Cuando el profesor abre P2
    Entonces la tarjeta no lista pasos y dice «La carrera aún no registra el plan de medición de esta sección»
    Y el botón «Subir export» sigue desactivado con aria-describedby hacia ese texto

  @spec008 @corte1 @US-81 @delegado_a_vitest
  Escenario: La marca del paso no depende solo del color
    Dado una sesión de "docente701@example.invalid" con rol "PROFESOR" y la sección 701 de "5643" en "2026-1"
    Y que la ruta 4 responde la 701 en estado "SIN_CARGA"
    Cuando el profesor abre P2
    Entonces cada paso tiene su marca escrita «Ahora», «Hecho», «Corregir» o «Pendiente»
    Y un lector de pantalla anuncia «Paso 1 de 2, ahora» (propuesta)

  @spec008 @corte1 @US-81 @delegado_a_vitest
  Escenario: La coordinación no recibe los pasos del profesor
    Dado una sesión de "coordinador.quimica@example.invalid" con rol "COORDINADOR" y alcance "CURSO"
    Y que la ruta 4 responde la 701 en estado "SIN_CARGA"
    Cuando abre P2
    Entonces ninguna tarjeta lista pasos
    Y P2 no pide la ruta 8

  @spec008 @corte1 @US-81 @delegado_a_vitest
  Escenario: Ingreso dice el error junto al formulario y conserva el correo
    Dado que la ruta 1 responde 401 con «Correo o contraseña incorrectos.»
    Cuando el profesor ingresa "docente701@example.invalid" con una contraseña errada
    Entonces el mensaje aparece con role="alert" sobre el botón «Ingresar»
    Y el campo del correo conserva "docente701@example.invalid" y el de la contraseña queda vacío (propuesta)

  @spec008 @corte1 @US-81 @delegado_a_vitest
  Escenario: El bloqueo por intentos se muestra sin ocultar el formulario
    Dado que la ruta 1 responde 429 con «Demasiados intentos. Espere 15 minutos.»
    Cuando el profesor intenta ingresar
    Entonces ve ese texto con role="alert"
    Y el formulario sigue a la vista

  @spec008 @corte1 @US-81 @delegado_a_vitest
  Escenario: Con movimiento reducido no hay animaciones
    Dado que el navegador pide prefers-reduced-motion
    Cuando el profesor abre P2 en espera
    Entonces el indicador de carga no anima y sigue diciendo «Cargando secciones»

  @spec008 @corte1 @US-81 @delegado_a_vitest
  Escenario: El rediseño no carga recursos de terceros ni dependencias nuevas
    Cuando se construye el Front con npm run build
    Entonces el index.html y el CSS no piden fuentes ni hojas de estilo de otro dominio
    Y package.json y package-lock.json no ganan dependencias

  @spec008 @corte1 @US-82 @playwright
  Esquema del escenario: A 375 px de ancho ninguna pantalla se desplaza de lado
    Dado el navegador de Playwright a 375 por 812 px con la API simulada
    Cuando el profesor abre <pantalla> con la sección «5643 Química General, sección 701, 2026-1»
    Entonces el ancho del documento no supera el de la ventana
    Y cada botón mide al menos 24 por 24 px

    Ejemplos:
      | pantalla |
      | Ingreso  |
      | P2       |
      | P3       |
      | P4       |
      | P5       |
      | P6       |
      | P7       |

  @spec008 @corte1 @US-82 @playwright
  Escenario: La tabla de rechazos de P4 se desplaza dentro de su región y no la página
    Dado el navegador de Playwright a 375 px con una carga de 12 rechazos de fila
    Cuando el profesor abre P4
    Entonces la tabla vive en una región con role="region", nombre accesible y tabindex 0
    Y la página no se desplaza de lado

  @spec008 @corte1 @US-82 @playwright
  Escenario: El foco se ve en cada control de P3 y sigue el orden de lectura
    Dado el navegador de Playwright en P3 de la sección 701
    Cuando el profesor recorre la pantalla con la tecla Tab
    Entonces cada control enfocado muestra el anillo de foco
    Y el orden pasa por «Salir», el menú, el selector de periodo si existe, el archivo, «Subir» y «Volver a mis secciones», y «Antes de subir» se lee entre el periodo y el archivo sin tomar el foco

  @spec008 @corte1 @US-82 @playwright
  Escenario: El menú principal se usa solo con el teclado
    Dado el navegador de Playwright en P2 de una sesión de "docente701@example.invalid"
    Cuando el profesor llega con Tab a «Cargas» y pulsa Enter
    Entonces P5 queda a la vista y su botón del menú lleva aria-current="page"
