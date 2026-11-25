"""Pasos compartidos de conftest.py que la spec 009 usa en sus Antecedentes (T014 de specs/009-resumen-del-curso/tasks.md).

Los Antecedentes de resumen_del_curso.feature piden la base de la spec 009 con el plan de 5643 en 2026-1 y los datos
inventados de Química, y sus escenarios publican la carga de una sección con «los niveles [a, b, c, d]», que son los
alumnos calificados en los niveles 1, 2, 3 y 4, y a veces con un alumno sin evidencia. Estas pruebas leen las
expresiones que pytest-bdd registra y llaman a las ayudas del arnés, con lo que debe pasar y lo que no debe pasar. Dos
de ellas publican de verdad en una base desechable del clúster de tests/cluster_desechable.py y comprueban lo que lee
abet.v_r17_por_pi.
"""

from __future__ import annotations

import re
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from pytest_bdd.steps import StepFunctionContext, step_function_context_registry

RAIZ = Path(__file__).resolve().parents[3]
ANTECEDENTE = "una base desechable de la spec 009 con el plan de 5643 en 2026-1 y los datos inventados de Química"


@pytest.fixture
def arnes(request: pytest.FixtureRequest) -> ModuleType:
    """Módulo conftest.py de esta carpeta, que pytest registra como plugin."""
    for plugin in request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            return plugin
    raise AssertionError("no se encontró el conftest.py del arnés de aceptación")


def _paso(nombre: str) -> StepFunctionContext:
    contextos = [c for c in list(step_function_context_registry.values())
                 if c.step_func.__name__ == nombre and c.step_func.__code__.co_filename.endswith("pasos/conftest.py")]
    assert len(contextos) == 1, f"conftest.py define {len(contextos)} pasos {nombre}"
    return contextos[0]


def _argumentos(nombre: str, texto: str) -> dict[str, Any] | None:
    parser = _paso(nombre).parser
    return parser.parse_arguments(texto) if parser.is_matching(texto) else None


# La base de la spec 009

def test_la_base_de_la_spec_009_con_el_plan_y_los_datos_de_quimica_se_reconoce() -> None:
    assert _argumentos("_base_de_la_spec_009", ANTECEDENTE)["resto"] == (
        "con el plan de 5643 en 2026-1 y los datos inventados de Química")


@pytest.mark.parametrize("texto", [
    "una base desechable de la spec 009",
    "una base desechable de la spec 009 sin el plan",
    "una base desechable de la spec 008 con el plan de 5643 en 2026-1 y los datos inventados de Química",
    "una base desechable de la spec 010 con el plan de 5643 en 2026-1 y los datos inventados de Química",
])
def test_la_base_de_la_spec_009_no_reconoce_otra_spec_ni_una_base_sin_forma(texto: str) -> None:
    assert _argumentos("_base_de_la_spec_009", texto) is None


def test_la_forma_de_la_base_dice_su_variante_y_una_forma_desconocida_no_adivina(arnes: ModuleType) -> None:
    variante, piezas = arnes.forma_de_la_base_009("con el plan de 5643 en 2026-1 y los datos inventados de Química")
    assert variante == "resumen_curso"
    assert ("db/datos/plan_quimica_2026_1.sql", "T022") in piezas
    with pytest.raises(AssertionError, match="la base de la spec 009 «con otra cosa» no tiene variante"):
        arnes.forma_de_la_base_009("con otra cosa")


def test_la_variante_del_resumen_siembra_quimica_con_su_plan_y_el_plan_de_450010(arnes: ModuleType) -> None:
    assert arnes.SIEMBRAS["resumen_curso"] is arnes.sembrar_resumen_curso
    assert arnes.VARIANTES["resumen_curso"] == {}


def test_la_base_del_resumen_trae_450010_con_plan_y_una_seccion_y_5643_con_sus_cuatro(ctx: Any) -> None:
    ctx.crear_base("resumen_curso")
    secciones = ctx.filas("SELECT a.codigo, pe.codigo, count(*), (SELECT count(*) FROM abet.plan_medicion pm"
                          " WHERE pm.asignatura_id = a.asignatura_id AND pm.periodo_id = pe.periodo_id)"
                          " FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                          " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
                          " WHERE a.codigo IN ('450010', '450020', '5643') GROUP BY 1, 2, pe.periodo_id, a.asignatura_id"
                          " ORDER BY 1, 2")
    assert secciones == [("450010", "2026-2", 1, 3), ("5643", "2026-1", 4, 1)]


# La carga de una sección con «los niveles [a, b, c, d]»

@pytest.mark.parametrize(("texto", "numero", "niveles", "sin"), [
    ("la 701 publicada con los niveles [1, 2, 4, 3]", "701", "1, 2, 4, 3", None),
    ("la 702 publicada con los niveles [0, 1, 5, 4]", "702", "0, 1, 5, 4", None),
    ("la 703 publicada con los niveles [2, 4, 4, 3] y un alumno sin evidencia", "703", "2, 4, 4, 3",
     " y un alumno sin evidencia"),
])
def test_la_carga_con_niveles_se_reconoce_con_o_sin_un_alumno_sin_evidencia(texto: str, numero: str, niveles: str,
                                                                          sin: str | None) -> None:
    argumentos = _argumentos("_publicada_con_niveles", texto)
    assert (argumentos["numero"], argumentos["niveles"], argumentos["sin"]) == (numero, niveles, sin)


@pytest.mark.parametrize("texto", [
    "la 701 publicada con los niveles [1, 2, 4]",
    "la 701 publicada con los niveles [1, 2, 4, 3, 5]",
    "la 701 publicada con los niveles [1, 2, x, 3]",
    "la 701 publicada con los niveles [1, 2, -4, 3]",
    "la 701 publicada con los niveles 1, 2, 4, 3",
    "la 705 publicada con los niveles [1, 2, 4, 3]",
    "la 701 publicada con los niveles [1, 2, 4, 3] y dos alumnos sin evidencia",
    "la 701 con los niveles [1, 2, 4, 3]",
])
def test_la_carga_con_niveles_no_admite_otra_forma(texto: str) -> None:
    assert _argumentos("_publicada_con_niveles", texto) is None


@pytest.mark.parametrize("texto", [
    "la 701, la 702 y la 703 publicadas con los niveles del primer escenario y la 704 sin carga",
    "la 701, la 702 y la 703 publicadas con los niveles del escenario anterior y la 704 sin carga",
])
def test_las_tres_cargas_de_los_niveles_del_primer_escenario_se_reconocen(texto: str) -> None:
    assert _argumentos("_tres_publicadas_del_primer_escenario", texto) is not None


@pytest.mark.parametrize("texto", [
    "la 701, la 702 y la 703 publicadas con los niveles del tercer escenario y la 704 sin carga",
    "la 701, la 702 y la 703 publicadas con los niveles del primer escenario",
    "la 701 y la 702 publicadas con los niveles del primer escenario y la 704 sin carga",
])
def test_las_tres_cargas_no_admiten_otra_referencia(texto: str) -> None:
    assert _argumentos("_tres_publicadas_del_primer_escenario", texto) is None


# Las filas que arma la ayuda

def test_las_filas_por_nivel_cuentan_cada_nivel_y_el_alumno_sin_evidencia() -> None:
    c = _cargas_de_prueba()
    filas = c.filas_por_nivel((1, 2, 4, 3), desde=99200000)
    assert len(filas) == 10
    assert [sum(1 for f in filas if f.niveles == (nivel,)) for nivel in (1, 2, 3, 4)] == [1, 2, 4, 3]
    con_uno = c.filas_por_nivel((2, 4, 4, 3), desde=99200000, sin_evidencia=1)
    assert len(con_uno) == 14
    assert [f.niveles for f in con_uno if f.niveles == (None,)] == [(None,)]
    assert c.filas_por_nivel((0, 0, 0, 0), desde=99200000) == []


def test_los_codigos_de_las_filas_son_unicos_de_ocho_cifras_y_del_rango_99() -> None:
    c = _cargas_de_prueba()
    filas = c.filas_por_nivel((2, 4, 4, 3), desde=99200000, sin_evidencia=1)
    codigos = [f.codigo for f in filas]
    assert len(set(codigos)) == len(codigos)
    assert all(re.fullmatch(r"99[0-9]{6}", codigo) for codigo in codigos), codigos
    assert [f.fila_origen for f in filas] == list(range(2, 2 + len(filas)))


@pytest.mark.parametrize("niveles", [(1, 2, 4), (1, 2, 4, 3, 1), (1, -2, 4, 3)])
def test_las_filas_por_nivel_no_aceptan_un_conteo_que_no_sea_de_cuatro_niveles_no_negativos(niveles: tuple[int, ...]) -> None:
    with pytest.raises(AssertionError, match="cuatro conteos"):
        _cargas_de_prueba().filas_por_nivel(niveles, desde=99200000)


def test_el_codigo_no_se_sale_del_rango_99_con_demasiados_alumnos() -> None:
    with pytest.raises(AssertionError, match="rango 99"):
        _cargas_de_prueba().filas_por_nivel((2_000_000, 0, 0, 0), desde=99900000)


def _cargas_de_prueba() -> ModuleType:
    import sys

    return sys.modules["cargas_de_prueba"]


# La carga en una base desechable

def test_la_carga_de_una_seccion_de_5643_queda_en_la_vista_con_sus_niveles(ctx: Any, arnes: ModuleType) -> None:
    ctx.crear_base("resumen_curso")
    carga = arnes.publicar_seccion_de_quimica(ctx, "701", (1, 2, 4, 3))
    fila = ctx.filas("SELECT pi, n_nivel_1, n_nivel_2, n_nivel_3, n_nivel_4, n_sin_evidencia, n_total, nivel_esperado,"
                     " meta_logro_pct, provisional FROM abet.v_r17_por_pi WHERE carga_id = %s", carga)
    assert fila == [("6.1", 1, 2, 4, 3, 0, 10, 3, 80.0, True)]
    assert ctx.filas("SELECT s.numero, pe.codigo, a.codigo FROM abet.carga c JOIN abet.seccion s USING (seccion_id)"
                     " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
                     " JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id WHERE c.carga_id = %s",
                     carga) == [("701", "2026-1", "5643")]
    # No nace ninguna sección nueva ni en 2026-2 ni en otro número.
    assert ctx.uno("SELECT count(*) FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                   " WHERE a.codigo = '5643'") == 4


def test_un_alumno_sin_evidencia_cuenta_en_el_total_y_no_entre_los_calificados(ctx: Any, arnes: ModuleType) -> None:
    ctx.crear_base("resumen_curso")
    carga = arnes.publicar_seccion_de_quimica(ctx, "703", (2, 4, 4, 3), sin_evidencia=1)
    assert ctx.filas("SELECT n_nivel_1, n_nivel_2, n_nivel_3, n_nivel_4, n_sin_evidencia, n_total"
                     " FROM abet.v_r17_por_pi WHERE carga_id = %s", carga) == [(2, 4, 4, 3, 1, 14)]


def test_una_seccion_que_no_existe_o_una_publicada_dos_veces_no_se_publica(ctx: Any, arnes: ModuleType) -> None:
    ctx.crear_base("resumen_curso")
    with pytest.raises(AssertionError):
        arnes.publicar_seccion_de_quimica(ctx, "799", (1, 2, 4, 3))
    arnes.publicar_seccion_de_quimica(ctx, "701", (1, 2, 4, 3))
    with pytest.raises(AssertionError, match="ya tiene una carga PUBLICADA"):
        arnes.publicar_seccion_de_quimica(ctx, "701", (0, 1, 3, 1))
    assert ctx.uno("SELECT count(*) FROM abet.carga WHERE estado = 'PUBLICADA'") == 1
