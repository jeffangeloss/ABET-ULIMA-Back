"""Lista común de encabezados de columna con el PI que nombran, o None si no son de un PI (spec 003, J-19).

La regla del encabezado de un indicador de desempeño (performance indicator, PI) vive dos veces: en
_ENCABEZADO_DE_PI de abet_carga/lector.py y en ck_carga_columna_encabezado de
db/migration/V1_10__encabezado_pi_con_prefijo.sql. Esta lista es la única fuente de casos para las
dos, así que tests/test_lector.py comprueba con ella el lector y una prueba de paridad con la base
puede comprobar que la restricción acepta exactamente los mismos encabezados con su pi_codigo. Cada
caso es (encabezado, pi_codigo o None) y el encabezado va tal como llega al lector, antes de
quitarle los espacios de los lados y de cortarlo a 200 caracteres. Trae los ejemplos del esquema
«Qué encabezados son de un PI» de specs/003-exports-blackboard/aceptacion/exports_blackboard.feature
y los bordes de la regla: el espacio duro U+00A0, la «ſ» que una comparación sin re.ASCII tomaría
por «s», cuatro espacios entre las partes, el corte a 200 caracteres y «6.10 [», que nunca es 6.1.
Ningún encabezado trae datos de estudiantes.
"""

from __future__ import annotations

ENCABEZADOS_DE_PI: tuple[tuple[str, str | None], ...] = (
    # Ejemplos del esquema «Qué encabezados son de un PI» del .feature.
    ("ABET SO5.1 [Total Pts: 100 Score] |9000051", "5.1"),
    ("ABET SO 5.3 [Total Pts: 100 Score] |9000053", "5.3"),
    ("abet so 5.2 [Total Pts: 100 Score] |9000052", "5.2"),
    ("SO 5.1 [Total Pts: 4 Score] |9000051", "5.1"),
    ("PI 5.1 [Total Pts: 4 Score] |9000051", "5.1"),
    ("5.1 [Total Pts: 4 Score] |9000051", "5.1"),
    ("5.1[Total Pts: 4 Score] |9000051", "5.1"),
    ("ABET SO 5.10 [Total Pts: 100 Score] |9000051", "5.10"),
    ("ABET SO 5.1", None),
    ("ABET SO5 [Total Pts: 100 Score] |9000051", None),
    ("ABET    SO 5.1 [Total Pts: 100 Score] |9000051", None),
    ("Actividad 5.1 [Total Pts: 4 Score] |9000051", None),
    ("9. Casos de Circularidad [Total Pts: 100 Score] |9000099", None),
    ("7. Ejercicio en clase: Conceptos y Métricas LCA (10 ejercicios) [Total Pts: 20 Score] |9000098", None),
    # Bordes de la regla.
    ("ABET SO5.1 [Total Pts: 100 Score] |9000051", None),
    ("ABET SO 5.1 [Total Pts: 100 Score] |9000051", None),
    ("5.1 [Total Pts: 4 Score] |9000051", None),
    ("ABET ſO5.1 [Total Pts: 100 Score] |9000051", None),
    ("ABET SO    5.1 [Total Pts: 100 Score] |9000051", None),
    ("5.1    [Total Pts: 4 Score] |9000051", None),
    ("5.1  [Total Pts: 4 Score] |9000051", "5.1"),
    ("ABET   SO   5.1   [Total Pts: 100 Score] |9000051", "5.1"),
    ("Abet So5.1 [Total Pts: 100 Score] |9000051", "5.1"),
    ("ABETSO5.1 [Total Pts: 100 Score] |9000051", "5.1"),
    ("ABET5.1 [Total Pts: 100 Score] |9000051", "5.1"),
    ("ABET SO 5.1 sin corchete", None),
    ("5.1 [Total Pts: 4 Score] " + "x" * 225, "5.1"),
    ("ABET SO 5." + "1" * 200 + " [Total Pts: 4 Score]", None),
    ("6.10 [Total Pts: 4 Score] |9000610", "6.10"),
    ("ABET SO 4.1 [Total Pts: 100 Score] |9000041", "4.1"),
    ("  ABET SO5.1 [Total Pts: 100 Score] |9000051  ", "5.1"),
    ("Nota 5.1 [Total Pts: 4 Score] |9000051", None),
    ("5 [Total Pts: 4 Score] |9000005", None),
    ("SOPI 5.1 [Total Pts: 4 Score] |9000051", None),
    ("ABET SO ５.1 [Total Pts: 100 Score] |9000051", None),
)
