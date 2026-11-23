# language: es
#
# Escenarios de aceptación de US-83 y US-84 de la spec 008-ciclo-quimica-industrial (épica EP-08, propuesta). Un
# solo conciliador de solo lectura, db/herramientas/conciliar_tabla_maestra.py (propuesta), compara la base y los
# R-17 del sistema con la tabla maestra por sección, por estudiante y por nivel, sin mostrar códigos (US-83,
# C-48 con C-65 y el comparador de C-07, veredicto CAMBIAR del crítico), y un ensayo sube los exports en una base
# aparte y pasa el conciliador antes de la capacitación (US-84, C-61 corregida).
#
# Este archivo usa solo datos inventados. Las pruebas usan la tabla maestra inventada de exports_capacitacion.feature
# (701, 702 y 703 de 5643 en 2026-1, códigos del rango 99). La corrida con los 18 exports reales y la tabla
# maestra real se hace fuera del repositorio, en una rama hija de develop en Neon desde el Windows de Jefferson
# (J-52, valor provisional), y su informe queda fuera del repositorio.
#
# Vocabulario de los pasos.
# - El oráculo es la tabla maestra, que Stefanny verificó igual alumno por alumno a los 18 R-17 llenados a mano.
#   Por eso «el R-17 del sistema es igual al del profesor» significa que el conciliador encuentra, en la sección,
#   los mismos códigos con los mismos niveles, el mismo conteo por nivel y el mismo porcentaje en la base, en
#   abet.v_r17_por_pi y en las celdas del R-17 descargado (M24 a M26, E24 y la tabla desde la fila 43).
# - El porcentaje se compara como el cociente x de n y, cuando se muestra, con la precisión de un decimal del
#   R-17. Las columnas PROFESOR, ARCHIVO y ESTADO DE EVIDENCIA no se comparan, porque abet.v_tabla_maestra_pi deja
#   PROFESOR nulo.
# - El conciliador lee la base con el rol abet_respaldo, en una transacción READ ONLY, lee .xlsx con openpyxl o
#   .csv y se niega a leer un archivo que está dentro de un repositorio git. Acepta códigos que no empiezan con
#   99 y exige 8 cifras, y su informe nunca trae un número de ocho cifras.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Conciliación con la tabla maestra y ensayo de punta a punta
  Como Oficina de Calidad, quiero comparar lo que el sistema mide y los R-17 que genera con la tabla maestra,
  para saber antes y después de la capacitación que el sistema reproduce el R-17 de cada profesor.

  Antecedentes:
    Dado una base desechable de la spec 008 con el plan de 5643 en 2026-1 y los datos de quimica_2026_1_inventado.sql
    Y una tabla maestra inventada en tmp_path con 5 estudiantes por sección en la 701, la 702 y la 703, códigos del rango 99 y calificaciones de 1 a 4

  @spec008 @US-83
  Escenario: Todo coincide en la base, en la vista y en los R-17
    Dado las cargas PUBLICADA de la 701, la 702 y la 703 con los mismos niveles de la tabla
    Y sus R-17 descargados en una carpeta de tmp_path
    Cuando el conciliador corre con --periodo 2026-1 --asignatura 5643 --pi 6.1, la tabla y la carpeta de los R-17
    Entonces termina con código 0
    Y por cada sección dice «Sección 701. Igual en 5 de 5 estudiantes, en el conteo por nivel y en el porcentaje.» (propuesta)
    Y el resumen dice «3 de 3 secciones iguales.» (propuesta)

  @spec008 @US-83
  Escenario: Una calificación distinta se informa sin el código
    Dado las cargas PUBLICADA de las tres secciones y la tabla con la calificación de un estudiante de la 702 cambiada de 3 a 2
    Cuando el conciliador corre
    Entonces termina con código 1
    Y dice «Sección 702. 1 estudiante con nivel distinto.» y «2 de 3 secciones iguales.» (propuesta)
    Y ninguna línea del informe trae un número de ocho cifras

  @spec008 @US-83
  Esquema del escenario: Cada diferencia se cuenta por su tipo y por sección
    Dado las cargas PUBLICADA de las tres secciones y la tabla con <diferencia>
    Cuando el conciliador corre
    Entonces dice «<informe>» (propuesta)

    Ejemplos:
      | diferencia                                              | informe                                                                      |
      | una fila más en la 701 que la base no tiene             | Sección 701. 1 estudiante en la tabla maestra que el sistema no mide.        |
      | una fila menos en la 703                                | Sección 703. 1 estudiante medido por el sistema que no está en la tabla.     |
      | las filas de la 702 en el PI 6.2                        | Sección 702. 5 filas del PI 6.2 en la tabla maestra y 0 en el sistema (D-48). |
      | un R-17 descargado de la 701 con M25 cambiado           | Sección 701. El conteo del R-17 no es el de la tabla maestra.                |

  @spec008 @US-83
  Escenario: Una sección sin carga publicada se nombra
    Dado la carga PUBLICADA de la 701 y la 702 y la 703 sin carga PUBLICADA
    Cuando el conciliador corre
    Entonces dice «Sección 703. Sin carga publicada.» (propuesta)

  @spec008 @US-83
  Escenario: El mismo cociente con otro redondeo cuenta como igual
    Dado la 701 con 2 de 3 estudiantes con nivel 3 o 4 en la base y en la tabla
    Cuando el conciliador corre
    Entonces la 701 es igual, porque compara el cociente 2 de 3 y el porcentaje con un decimal

  @spec008 @US-83
  Escenario: Una carga reemplazada no duplica filas
    Dado la 703 con una carga REEMPLAZADA y su sucesora PUBLICADA con los mismos niveles
    Cuando el conciliador corre
    Entonces la 703 trae 5 estudiantes y es igual, porque abet.v_tabla_maestra_pi lee solo la carga PUBLICADA

  @spec008 @US-83
  Escenario: El orden de las filas y la columna PROFESOR no cuentan como diferencia
    Dado la tabla con las filas en otro orden y la columna PROFESOR llena
    Cuando el conciliador corre
    Entonces las tres secciones son iguales

  @spec008 @US-83
  Escenario: Los códigos que no empiezan con 99 se aceptan con 8 cifras
    Dado una tabla y una base inventadas con códigos de ocho cifras que no empiezan con 99, armados por la prueba en tmp_path
    Cuando el conciliador corre con la opción de datos reales (propuesta)
    Entonces compara las secciones y su informe no trae ningún número de ocho cifras

  @spec008 @US-83
  Escenario: El conciliador no lee un archivo dentro de un repositorio
    Dado la tabla inventada copiada dentro de una carpeta con .git
    Cuando el conciliador corre con esa ruta
    Entonces termina con código 2 antes de leer el archivo

  @spec008 @US-83
  Escenario: La conciliación no escribe en la base
    Cuando el conciliador corre con el rol abet_respaldo
    Entonces abet.carga, abet.medicion y acceso.sesion no ganan ninguna fila
    Y un INSERT del conciliador fallaría con el SQLSTATE 25006 de la transacción READ ONLY

  @spec008 @US-84
  Escenario: El ensayo sube los exports generados y deja las secciones iguales
    Dado los exports de la 701, la 702 y la 703 que el generador de US-74 arma desde la tabla inventada, con su manifiesto
    Cuando el ensayo sube cada export con la biblioteca abet_carga y descarga su R-17
    Entonces cada carga queda PUBLICADA con 0 filas rechazadas
    Y el conciliador dice «3 de 3 secciones iguales.» y termina con código 0
    Y las consultas de control Q01, Q02, Q03, Q04, Q06, Q07, Q08, Q10, Q12, Q13, Q14, Q18, Q19, Q20 y Q21 devuelven 0 filas

  @spec008 @US-84
  Escenario: El manifiesto del generador y lo publicado coinciden por huella y por conteo
    Dado los exports generados con su manifiesto
    Cuando el ensayo termina
    Entonces cada abet.archivo_origen tiene la huella SHA-256 que el manifiesto da para su sección
    Y el conteo por nivel de cada sección en abet.v_r17_por_pi es el del manifiesto

  @spec008 @US-84
  Escenario: Un nivel distinto en el ensayo se nombra sin el código y detiene la conclusión
    Dado el export de la 702 con el nivel de un estudiante cambiado de 3 a 2 frente a la tabla
    Cuando el ensayo sube los exports y corre el conciliador
    Entonces el conciliador dice «Sección 702. 1 estudiante con nivel distinto.» y «2 de 3 secciones iguales.»
    Y el ensayo termina con código 1

  @spec008 @US-84
  Escenario: El ensayo corre en una base aparte y no deja huellas en la de la capacitación
    Dado una base para el ensayo y otra para la capacitación
    Cuando el ensayo sube los exports en la base del ensayo
    Entonces la base de la capacitación no gana ninguna fila en abet.archivo_origen
    Y la misma subida en la base de la capacitación crea cargas nuevas y no devuelve la constancia de una carga del ensayo
