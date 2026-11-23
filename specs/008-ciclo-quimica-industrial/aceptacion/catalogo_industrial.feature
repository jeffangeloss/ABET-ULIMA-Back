# language: es
#
# Escenarios de aceptación de US-67, US-68 y US-69 de la spec 008-ciclo-quimica-industrial (épica EP-08,
# propuesta). La base recibe el catálogo IND-2026 de Ingeniería Industrial desde su referencia curricular
# (US-67, candidata C-40 corregida), el conjunto de reglas R-2026-BORRADOR de Industrial con la comprobación de
# arranque por carrera (US-68, C-41 con el escenario sin reglas de C-03 y la consulta Q19 de C-47) y la vigencia
# de IND-2026 en 2026-1 con el plan de medición de 5643 (US-69, C-42 con la consulta Q18 de C-47).
#
# Este archivo usa solo datos inventados. La referencia db/referencia/industrial_2026.json trae solo datos
# curriculares (SO, PI, asignaturas y niveles), sin datos de personas, y la descripción del instrumento de las
# pruebas es un texto inventado.
#
# Vocabulario de los pasos.
# - Las migraciones de la spec 008 son V1_12 (catálogo IND-2026), V1_13 (reglas de Industrial) y V1_14
#   (acceso.coordinacion_alcance), y la V1_12 de la spec 005 pasa a V1_15 con un cambio fechado en esa spec
#   (veredicto CAMBIAR del crítico de arquitectura).
# - Las consultas de control nuevas empiezan en Q18, porque Q15 vive en db/pruebas/pruebas.sql y la spec 005
#   reserva Q16 y Q17. Q18 detecta un curso con plan de dos carreras en el mismo periodo y Q19 una carrera con
#   plan de medición sin conjunto de reglas.
# - Las bases de estos escenarios son clústeres PostgreSQL 18 desechables de tests/cluster_desechable.py, nunca
#   localhost:5432.
# - Lo marcado «(propuesta)» no está fijado en las decisiones y lo decide la revisión de la spec.

Característica: Catálogo, reglas y plan de medición de Ingeniería Industrial
  Como administrador técnico, quiero cargar el catálogo de Ingeniería Industrial, su conjunto de reglas y el
  plan de medición de Química General en 2026-1, para que las secciones de 5643 midan el PI 6.1 de su carrera sin
  tocar Ingeniería Ambiental.

  Antecedentes:
    Dado una base desechable de la spec 008 con las migraciones V1_01 a V1_11 y la referencia db/referencia/industrial_2026.json de 7 SO, 21 PI y 53 asignaturas, 10 de ellas también en AMB-2026

  @spec008 @US-67
  Escenario: La migración V1_12 carga el catálogo IND-2026 con sus conteos
    Cuando Flyway aplica V1_12__cargar_referencia_industrial.sql
    Entonces abet.carrera tiene la carrera "IND" con el nombre "Ingeniería Industrial" en la facultad "FI"
    Y abet.catalogo_version tiene "IND-2026" en estado "BORRADOR" con la huella SHA-256 de la referencia
    Y IND-2026 tiene 7 filas en abet.so, 21 en abet.pi, 53 en abet.plan_estudios y 0 en abet.rubrica_nivel
    Y el PI "6.1" de IND-2026 pertenece al SO 6 y el par 5643 y SO 6 está en abet.asignatura_so
    Y abet.instrumento tiene «Portafolio 3» en IND-2026

  @spec008 @US-67
  Escenario: Una asignatura compartida se reutiliza sin tocar Ambiental
    Dado que abet.asignatura ya tiene "5643" con el nombre "Química General" desde V1_03
    Cuando Flyway aplica V1_12__cargar_referencia_industrial.sql
    Entonces abet.asignatura sigue con una sola fila de código "5643" y el mismo nombre
    Y abet.asignatura gana 43 filas y queda con 96
    Y "5643" está en el plan de estudios de AMB-2026 y en el de IND-2026
    Y las filas de AMB-2026 en abet.so, abet.pi, abet.rubrica_nivel, abet.plan_estudios y abet.asignatura_so no cambian

  @spec008 @US-67
  Escenario: La sección 1 de pruebas.sql cuenta por catálogo y no en toda la base
    Dado la base con V1_12 aplicada
    Cuando corre db/pruebas/correr_pruebas.sh
    Entonces las aserciones de AMB-2026 cuentan solo las filas del catálogo AMB-2026
    Y una aserción nueva cuenta las filas de IND-2026
    Y la corrida termina sin ninguna línea «FALLA»

  @spec008 @US-67
  Escenario: El generador de V1_12 es determinista
    Cuando db/herramientas/generar_v1_12.py corre dos veces con la misma referencia
    Entonces los dos archivos salen iguales byte a byte
    Y la prueba regenera V1_12 y no encuentra diferencias con el archivo guardado

  @spec008 @US-67
  Esquema del escenario: El generador rechaza una referencia mal formada antes de escribir
    Dado una referencia inventada con <defecto>
    Cuando corre db/herramientas/generar_v1_12.py
    Entonces termina con código 1
    Y el mensaje nombra <motivo>
    Y no escribe el archivo de salida

    Ejemplos:
      | defecto                                                 | motivo                               |
      | un PI "8.1" de un SO 8 que no existe                    | el SO del PI                         |
      | dos PI con el código "2.3"                              | el PI repetido                       |
      | la asignatura "56430" de 5 dígitos                      | el código de la asignatura           |
      | la asignatura "5643" con el nombre "Quimica general"    | el nombre distinto del ya registrado |
      | una descripción de PI de 301 caracteres                 | el largo de la descripción del PI    |
      | una asignatura de nivel 13                              | el ciclo de malla                    |
      | una asignatura sin nivel                                | el ciclo de malla                    |

  @spec008 @US-67
  Escenario: La aserción final detiene la migración si un conteo no coincide
    Dado una copia de V1_12 sin una de sus 21 filas de PI
    Cuando Flyway la aplica en una transacción en una base desechable
    Entonces la migración falla con el conteo de abet.pi
    Y ninguna fila de IND-2026 queda en la base

  @spec008 @US-68
  Escenario: La migración V1_13 siembra el conjunto de reglas de Industrial
    Dado la base con V1_12 aplicada
    Cuando Flyway aplica V1_13__cargar_reglas_industrial.sql
    Entonces abet.conjunto_reglas tiene "R-2026-BORRADOR" en "BORRADOR" para "IND" y otro para "AMB"
    Y el de "IND" define META_LOGRO en 0,80 y NIVEL_ESPERADO en 3
    Y deja CORTE_ROJO, CONVERSION_NIVEL_0_1 y TRATO_SIN_EVIDENCIA en PENDIENTE, como el de "AMB"

  @spec008 @US-68
  Escenario: Una carga de 5643 toma las reglas de Industrial y la vista da la regla de la meta
    Dado la base con V1_12 y V1_13 aplicadas y los datos de db/datos/quimica_2026_1_inventado.sql
    Cuando "docente701@example.invalid" sube a la 701 un export inventado con 10 estudiantes de niveles 1, 2, 2, 3, 3, 3, 4, 4, 1 y 3 en el PI "6.1"
    Entonces la carga queda PUBLICADA con la carrera "IND" y el conjunto R-2026-BORRADOR de "IND"
    Y abet.v_r17_por_pi da para el PI "6.1" n_esperado_o_superior 6 de 10 calificados
    Y pct_logro_sobre_calificados es 60,0, meta_logro_pct es 80,0 y provisional es verdadero

  @spec008 @US-68
  Escenario: Una carga de 450002 sigue con las reglas de Ambiental
    Dado la base con V1_12 y V1_13 aplicadas y la sección inventada 410 de 450002 en 2026-2
    Cuando "docente410@example.invalid" sube a la 410 un export inventado válido
    Entonces la carga queda PUBLICADA con la carrera "AMB" y el conjunto R-2026-BORRADOR de "AMB"

  @spec008 @US-68
  Escenario: Sin el conjunto de Industrial la biblioteca no guarda nada y la ruta responde el error interno
    Dado la base con V1_12 y sin V1_13 y los datos de db/datos/quimica_2026_1_inventado.sql
    Cuando la biblioteca carga en la 701 un export inventado válido
    Entonces cargar() lanza ConfiguracionInvalida con «CONJUNTO_REGLAS R-2026-BORRADOR no existe para la carrera IND.»
    Y abet.archivo_origen y abet.carga no ganan ninguna fila
    Y por la ruta 5 el profesor recibe 500 con «Ocurrió un error interno. Intente de nuevo.» y sin el nombre de la variable

  @spec008 @US-68
  Escenario: El arranque de la API revisa el conjunto de reglas de cada carrera con plan
    Dado la base con V1_12 y sin V1_13 y el plan de 5643 en 2026-1
    Cuando la API arranca con CONJUNTO_REGLAS "R-2026-BORRADOR"
    Entonces la API no arranca y el mensaje nombra la carrera "IND" sin la palabra «Ambiental» (propuesta)
    Y con V1_13 aplicada la API arranca

  @spec008 @US-68
  Escenario: Q19 lista una carrera con plan de medición sin conjunto de reglas
    Dado la base con V1_12 y sin V1_13 y el plan de 5643 en 2026-1
    Cuando corre la consulta de control Q19
    Entonces devuelve 1 fila que nombra la carrera "IND" y el periodo "2026-1"
    Y con V1_13 aplicada devuelve 0 filas

  @spec008 @US-69
  Escenario: La corrida en seco del plan de Química informa y no escribe
    Dado la base con V1_12 y V1_13 aplicadas y la variable DESCRIPCION_INSTRUMENTO con "Texto de prueba del Portafolio 3"
    Cuando psql corre db/datos/plan_quimica_2026_1.sql sin la variable aplicar
    Entonces el informe dice que registraría 1 vigencia y 1 fila de plan de medición
    Y abet.catalogo_vigencia y abet.plan_medicion no ganan ninguna fila

  @spec008 @US-69
  Escenario: Con aplicar quedan la vigencia y el plan de 5643 con el PI 6.1
    Dado la base con V1_12 y V1_13 aplicadas y la variable DESCRIPCION_INSTRUMENTO con "Texto de prueba del Portafolio 3"
    Cuando psql corre db/datos/plan_quimica_2026_1.sql con -v aplicar=1 y -v pi=6.1
    Entonces abet.catalogo_vigencia tiene IND-2026 para "IND" en "2026-1"
    Y abet.plan_medicion tiene para 5643 en "2026-1" solo el PI "6.1" del SO 6 de "IND"
    Y su instrumento es «Portafolio 3» y su descripción es "Texto de prueba del Portafolio 3"

  @spec008 @US-69
  Escenario: Repetir el guion del plan no duplica ni cambia filas
    Dado que db/datos/plan_quimica_2026_1.sql ya corrió con -v aplicar=1
    Cuando corre otra vez con -v aplicar=1 y la misma descripción
    Entonces abet.catalogo_vigencia y abet.plan_medicion tienen las mismas filas que antes

  @spec008 @US-69
  Escenario: Una fila de plan distinta detiene todo
    Dado que abet.plan_medicion ya tiene 5643 en "2026-1" con el PI "6.1" y el instrumento "Proyecto"
    Cuando el guion del plan corre con -v aplicar=1
    Entonces el guion se detiene con un error que nombra la fila de 5643 en "2026-1"
    Y abet.catalogo_vigencia y abet.plan_medicion no ganan ninguna fila

  @spec008 @US-69
  Esquema del escenario: Una descripción del instrumento inválida no entra
    Dado la variable DESCRIPCION_INSTRUMENTO <estado>
    Cuando el guion del plan corre con -v aplicar=1
    Entonces el guion se detiene con <causa>
    Y abet.plan_medicion no gana ninguna fila

    Ejemplos:
      | estado                    | causa                                                                                    |
      | ausente                   | «Falta la descripción del instrumento, por ejemplo con \getenv DESCRIPCION_INSTRUMENTO.» |
      | con un espacio al final   | ck_plan_medicion_descripcion                                                             |
      | con 401 caracteres        | el SQLSTATE 22001 del largo                                                              |

  @spec008 @US-69
  Escenario: Sin el par 5643 y SO 6 en el catálogo el plan no entra
    Dado una base cuyo IND-2026 no tiene el par 5643 y SO 6 en abet.asignatura_so
    Cuando el guion del plan corre con -v aplicar=1
    Entonces el guion se detiene con fk_plan_medicion_asig_so
    Y abet.catalogo_vigencia no gana ninguna fila

  @spec008 @US-69
  Escenario: Ambiental en 2026-2 queda igual tras el plan de Química
    Dado la vigencia de AMB-2026 en 2026-2 y el plan de 450002 con los PI 5.1, 5.2 y 5.3
    Y la huella de Ambiental tomada con db/plataforma/neon/huella_ambiental.sql
    Cuando el guion del plan corre con -v aplicar=1
    Entonces huella_ambiental.sql devuelve la misma huella que antes
    Y las consultas de control Q05 y Q18 devuelven 0 filas

  @spec008 @US-69
  Escenario: Q18 detecta un curso con plan de dos carreras en el mismo periodo
    Dado el plan de 5643 en "2026-1" con el PI "6.1" de IND-2026 y otra fila con un PI de AMB-2026 sembrada por error
    Cuando corre la consulta de control Q18
    Entonces devuelve 1 fila que nombra la asignatura 5643 y el periodo "2026-1"
    Y la fila no trae correos ni códigos de estudiante
