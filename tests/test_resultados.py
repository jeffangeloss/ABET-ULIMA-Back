"""Regla de la meta y conversión de cifras de la ruta 12 (T031 de la spec 004, BR-RESULTADOS-05 y BR-RESULTADOS-06).

abet_carga/resultados.py decide en una función pura si un indicador de desempeño (performance indicator, PI) está en
la meta y convierte las cifras de abet.v_r17_por_pi en números de JavaScript Object Notation (JSON). La ruta
GET /api/resultados y el plan de acción del bloque II del R-17 (_plan_de_accion de abet_carga/r17.py) usan la misma
función, así que la pantalla y la constancia nunca discrepan en la meta.
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest

from abet_carga import r17, resultados

D = Decimal


@pytest.mark.parametrize(
    ("logro", "meta", "esperado"),
    [
        (D("80.0"), D("80.0"), True),     # el 80,0 % justo llega a la meta (escenario «El 80,0 % justo queda en la meta»)
        (D("81.8"), D("80.0"), True),
        (D("79.9"), D("80.0"), False),
        (D("63.6"), D("80.0"), False),
        (D("0.0"), D("80.0"), False),     # un logro de 0,0 % es una cifra y no la falta de una
        (D("90.9"), D("70.0"), True),
        (None, D("80.0"), None),          # PI sin calificaciones o sin nivel esperado definido
        (D("63.6"), None, None),          # conjunto de reglas sin META_LOGRO definida
        (None, None, None),
    ],
)
def test_br_resultados_06_en_meta_es_llegar_a_la_meta_o_superarla(logro: Decimal | None, meta: Decimal | None,
                                                                   esperado: bool | None) -> None:
    assert resultados.en_meta(logro, meta) is esperado


@pytest.mark.parametrize(
    ("valor", "json_esperado"),
    [(D("63.6"), "63.6"), (D("80.0"), "80.0"), (D("0.0"), "0.0"), (D("100.0"), "100.0"), (D("54.5"), "54.5"),
     (None, "null")],
)
def test_br_resultados_05_cada_cifra_viaja_como_numero_json_y_el_nulo_como_null(valor: Decimal | None,
                                                                                json_esperado: str) -> None:
    convertida = resultados.cifra(valor)
    assert json.dumps(convertida) == json_esperado
    assert convertida is None or isinstance(convertida, float)


@pytest.mark.parametrize("logro", [None, D("0.0"), D("54.5"), D("69.9"), D("70.0"), D("79.9"), D("80.0"), D("90.9")])
@pytest.mark.parametrize("meta", [None, D("70.0"), D("80.0")])
def test_br_resultados_06_el_plan_de_accion_del_r17_sigue_la_misma_regla(logro: Decimal | None,
                                                                        meta: Decimal | None) -> None:
    texto = r17._plan_de_accion({"pct_logro_sobre_calificados": logro, "meta_logro_pct": meta})
    if logro is None or meta is None:
        assert texto is None
    else:
        assert texto == (r17.LOGRADO if logro >= meta else r17.NO_LOGRADO)
    assert (texto == r17.LOGRADO) is (resultados.en_meta(logro, meta) is True)


@pytest.mark.parametrize(
    ("logro", "meta", "corte", "esperado"),
    [
        (D("80.0"), D("80.0"), D("75.0"), "VERDE"),
        (D("81.8"), D("80.0"), D("75.0"), "VERDE"),
        (D("77.8"), D("80.0"), D("75.0"), "AMBAR"),
        (D("75.0"), D("80.0"), D("75.0"), "AMBAR"),
        (D("74.9"), D("80.0"), D("75.0"), "ROJO"),
        (D("72.7"), D("80.0"), D("75.0"), "ROJO"),
        (D("77.8"), D("80.0"), None, "ROJO"),
        (D("75.0"), D("80.0"), None, "ROJO"),
        (D("80.0"), D("80.0"), None, "VERDE"),
        (D("0.0"), D("80.0"), D("0.0"), "AMBAR"),
        (None, D("80.0"), D("75.0"), "SIN_DATO"),
        (D("77.8"), None, D("75.0"), "SIN_DATO"),
        (None, None, None, "SIN_DATO"),
    ],
)
def test_br_mejora_02_semaforo_por_meta_y_corte_rojo(logro, meta, corte, esperado):
    assert resultados.semaforo(logro, meta, corte) == esperado


@pytest.mark.parametrize(
    ("semaforo", "esperado"),
    [
        ("VERDE", "BUENA_PRACTICA"),
        ("AMBAR", "OPORTUNIDAD_MEJORA"),
        ("ROJO", "OPORTUNIDAD_MEJORA"),
        ("SIN_DATO", None),
    ],
)
def test_br_mejora_03_tipo_de_registro_por_semaforo(semaforo, esperado):
    assert resultados.tipo_de_registro(semaforo) == esperado


@pytest.mark.parametrize(
    ("pi", "logro", "meta", "nivel_esperado", "texto"),
    [
        ("5.1", D("63.6"), D("80.0"), 3, "5.1: 63,6 % en Satisfactorio o más, meta 80,0 %"),
        ("5.3", D("80.0"), D("80.0"), 3, "5.3: 80,0 % en Satisfactorio o más, meta 80,0 %"),
        ("5.1", D("90.9"), D("70.0"), 2, "5.1: 90,9 % en En proceso o más, meta 70,0 %"),
        ("5.2", D("0"), D("80"), 1, "5.2: 0,0 % en No satisfactorio o más, meta 80,0 %"),
        ("5.2", D("100"), D("80"), 4, "5.2: 100,0 % en Sobresaliente o más, meta 80,0 %"),
        ("5.3", None, D("80.0"), 3, "5.3: sin calificaciones en esta carga."),
        ("5.1", D("63.6"), None, 3, "5.1: el conjunto de reglas no define la meta o el nivel esperado."),
        ("5.1", D("63.6"), D("80.0"), None, "5.1: el conjunto de reglas no define la meta o el nivel esperado."),
        ("5.1", None, D("80.0"), None, "5.1: el conjunto de reglas no define la meta o el nivel esperado."),
    ],
)
def test_br_mejora_01_redactar_hallazgo_con_cifras_y_casos_sin_cifra(pi, logro, meta, nivel_esperado, texto):
    assert resultados.redactar_hallazgo(pi, logro, meta, nivel_esperado) == texto
