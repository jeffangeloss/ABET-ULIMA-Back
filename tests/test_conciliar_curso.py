"""Cifras del curso del conciliador, opción --curso (T023 de la spec 009, US-94, FR-011).

Pruebas sin base ni proceso aparte sobre las funciones puras de db/herramientas/conciliar_tabla_maestra.py que arman lo
que la tabla maestra dice del curso (alumnos con el nivel esperado o más, porcentaje, promedio y secciones en la meta,
valores provisionales de D-56) y las líneas del informe. La corrida completa, con la base desechable, vive en
tests/aceptacion/pasos/test_conciliacion_del_curso_feature.py.

Todo es inventado. Cada prueba nombra lo que debe pasar y lo que no debe pasar (AGENTS.md, regla 8). Los redondeos son
como los de ROUND(numeric) de PostgreSQL, que se aleja del cero en la mitad, y no como el round() de Python.
"""

from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest

RAIZ = Path(__file__).resolve().parent.parent


def _conciliador() -> ModuleType:
    if "conciliar_tabla_maestra" not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(
            "conciliar_tabla_maestra", RAIZ / "db" / "herramientas" / "conciliar_tabla_maestra.py")
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules["conciliar_tabla_maestra"] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules["conciliar_tabla_maestra"]


K = _conciliador()


def _tabla(**secciones: tuple[int, ...]) -> dict[str, dict[str, dict[str, int]]]:
    """Niveles inventados por sección, con códigos del rango 99 distintos, en el PI 6.1."""
    return {numero[1:]: {"6.1": {f"99{numero[1:]}{n:03d}": nivel for n, nivel in enumerate(niveles, start=1)}}
            for numero, niveles in secciones.items()}


# Lo que la tabla maestra dice del curso

def test_el_curso_de_la_tabla_suma_alumnos_y_no_promedia_porcentajes() -> None:
    # Las tres secciones de la spec 009, con [1, 2, 4, 3], [0, 1, 5, 4] y [2, 4, 4, 3] alumnos en los niveles 1 a 4.
    niveles = {"s701": (1, 2, 2, 3, 3, 3, 3, 4, 4, 4), "s702": (2, *(3,) * 5, *(4,) * 4),
               "s703": (1, 1, *(2,) * 4, *(3,) * 4, *(4,) * 3)}
    curso = K.curso_de_la_tabla(_tabla(**niveles), "6.1")
    assert (curso.logrados, curso.calificados) == (23, 33)
    assert curso.porcentaje == Decimal("69.7") and curso.promedio == Decimal("2.91")
    # Los porcentajes de sección son 70,0, 90,0 y 53,8, y su promedio, 71,3, no es el del curso.
    assert [curso.por_seccion[s][0] for s in ("701", "702", "703")] == [Decimal("70.0"), Decimal("90.0"), Decimal("53.8")]
    assert curso.porcentaje != Decimal("71.3")
    assert [curso.por_seccion[s][1] for s in ("701", "702", "703")] == [Decimal("2.90"), Decimal("3.30"), Decimal("2.62")]
    assert curso.en_la_meta == 1


def test_el_porcentaje_y_el_promedio_se_redondean_lejos_del_cero_como_postgresql() -> None:
    # 1 de 16 es 6,25 y el redondeo de PostgreSQL da 6,3, y 21 entre 8 es 2,625 y da 2,63. round() daría 6,2 y 2,62.
    curso = K.curso_de_la_tabla(_tabla(s701=(3, *(1,) * 15)), "6.1")
    assert curso.porcentaje == Decimal("6.3") and curso.promedio == Decimal("1.13")
    curso = K.curso_de_la_tabla(_tabla(s701=(3, 3, 3, 3, 3, 3, 1, 2)), "6.1")
    assert curso.promedio == Decimal("2.63")
    assert round(21 / 8, 2) == 2.62


def test_la_meta_se_compara_con_el_porcentaje_ya_redondeado() -> None:
    # 799 de 999 son 79,98 y se redondean a 80,0, que llega a la meta de 80 %. 107 de 134 son 79,85 y dan 79,9.
    curso = K.curso_de_la_tabla(_tabla(s701=(*(3,) * 799, *(1,) * 200), s702=(*(3,) * 107, *(1,) * 27)), "6.1")
    assert curso.por_seccion["701"][0] == Decimal("80.0") and curso.por_seccion["702"][0] == Decimal("79.9")
    assert curso.en_la_meta == 1
    assert K.META_DEL_CURSO == Decimal(80)


def test_el_curso_sin_estudiantes_en_el_pi_no_inventa_cifras() -> None:
    curso = K.curso_de_la_tabla({"701": {"6.2": {"99701001": 3}}}, "6.1")
    assert (curso.logrados, curso.calificados, curso.porcentaje, curso.promedio, curso.en_la_meta) == (0, 0, None, None, 0)
    assert curso.por_seccion == {}


def test_solo_cuenta_el_pi_pedido() -> None:
    tabla = _tabla(s701=(3, 3, 1))
    tabla["701"]["6.2"] = {"99701101": 1, "99701102": 1}
    curso = K.curso_de_la_tabla(tabla, "6.1")
    assert (curso.logrados, curso.calificados) == (2, 3)


# El informe del curso

def _curso(logrados: int, calificados: int, pct: str | None, promedio: str | None, en_la_meta: int,
           por_seccion: dict[str, tuple[str | None, str | None]] | None = None) -> object:
    return K.Curso(logrados, calificados, Decimal(pct) if pct else None, Decimal(promedio) if promedio else None,
                   en_la_meta, {s: (Decimal(a) if a else None, Decimal(b) if b else None)
                                for s, (a, b) in (por_seccion or {}).items()})


def test_un_curso_igual_dice_igual_en_las_cuatro_cifras_y_no_trae_diferencias() -> None:
    curso = _curso(23, 33, "69.7", "2.91", 1)
    lineas, distinto = K.lineas_del_curso(curso, curso)
    assert lineas == ["Curso igual en alumnos en el nivel esperado o superior, en el porcentaje, en el promedio y en las "
                      "secciones en la meta."]
    assert distinto is False


@pytest.mark.parametrize(("sistema", "esperado"), [
    (_curso(23, 33, "69.7", "2.92", 1), ["Curso distinto en el promedio.",
                                          "Curso igual en alumnos en el nivel esperado o superior, en el porcentaje y en "
                                          "las secciones en la meta."]),
    (_curso(22, 33, "66.7", "2.91", 1), ["Curso distinto en alumnos en el nivel esperado o superior y en el porcentaje.",
                                          "Curso igual en el promedio y en las secciones en la meta."]),
    (_curso(23, 33, "69.7", "2.91", 2), ["Curso distinto en las secciones en la meta.",
                                          "Curso igual en alumnos en el nivel esperado o superior, en el porcentaje y en "
                                          "el promedio."]),
    (_curso(22, 32, "68.8", "2.50", 2), ["Curso distinto en alumnos en el nivel esperado o superior, en el porcentaje, en "
                                          "el promedio y en las secciones en la meta."]),
])
def test_cada_cifra_distinta_se_nombra_y_las_demas_salen_como_iguales(sistema: object, esperado: list[str]) -> None:
    lineas, distinto = K.lineas_del_curso(_curso(23, 33, "69.7", "2.91", 1), sistema)
    assert lineas == esperado and distinto is True


def test_un_sistema_sin_el_pi_hace_distinto_al_curso_en_todo() -> None:
    lineas, distinto = K.lineas_del_curso(_curso(23, 33, "69.7", "2.91", 1), None)
    assert lineas == ["Curso distinto en alumnos en el nivel esperado o superior, en el porcentaje, en el promedio y en las "
                      "secciones en la meta."]
    assert distinto is True


def test_el_porcentaje_nulo_del_sistema_no_es_igual_a_uno_de_la_tabla_y_dos_nulos_si() -> None:
    lineas, distinto = K.lineas_del_curso(_curso(0, 0, None, None, 0), _curso(0, 0, None, None, 0))
    assert distinto is False and lineas[0].startswith("Curso igual")
    lineas, distinto = K.lineas_del_curso(_curso(23, 33, "69.7", "2.91", 1), _curso(0, 0, None, None, 0))
    assert distinto is True and "el porcentaje" in lineas[0] and "el promedio" in lineas[0]


def test_las_lineas_del_curso_no_traen_cifras_ni_codigos() -> None:
    lineas, _ = K.lineas_del_curso(_curso(23, 33, "69.7", "2.91", 1), _curso(22, 32, "68.8", "2.50", 2))
    assert not any(caracter.isdigit() for linea in lineas for caracter in linea)


# El informe de cada sección

def test_la_seccion_con_el_promedio_y_el_porcentaje_iguales_dice_promedio_igual() -> None:
    tabla = _curso(7, 10, "70.0", "2.90", 0, {"701": ("70.0", "2.90")})
    sistema = _curso(7, 10, "70.0", "2.90", 0, {"701": ("70.0", "2.90")})
    assert K.lineas_del_promedio("701", tabla, sistema) == (["Sección 701. Con promedio igual."], False)


@pytest.mark.parametrize(("sistema", "esperadas"), [
    (("70.0", "2.80"), ["Sección 701. Distinta en el promedio."]),
    (("60.0", "2.90"), ["Sección 701. Distinta en el porcentaje.", "Sección 701. Con promedio igual."]),
    (("60.0", "2.80"), ["Sección 701. Distinta en el promedio y en el porcentaje."]),
    ((None, None), ["Sección 701. Distinta en el promedio y en el porcentaje."]),
])
def test_la_seccion_nombra_lo_que_la_distingue(sistema: tuple[str | None, str | None], esperadas: list[str]) -> None:
    tabla = _curso(7, 10, "70.0", "2.90", 0, {"701": ("70.0", "2.90")})
    lineas, distinta = K.lineas_del_promedio("701", tabla, _curso(7, 10, "70.0", "2.90", 0, {"701": sistema}))
    assert lineas == esperadas and distinta is True


def test_una_seccion_que_el_sistema_no_publica_no_trae_linea_de_promedio() -> None:
    tabla = _curso(7, 10, "70.0", "2.90", 0, {"701": ("70.0", "2.90")})
    assert K.lineas_del_promedio("701", tabla, _curso(0, 0, None, None, 0)) == ([], False)
    assert K.lineas_del_promedio("701", tabla, None) == ([], False)


# La conciliación completa con el curso

def _base_de_una_seccion(promedio: str) -> object:
    """Una sección de 5643, con los mismos dos niveles en la tabla y en el sistema, y un promedio dado para el sistema."""
    cifras = {"n1": 1, "n2": 0, "n3": 1, "n4": 0, "x": 1, "total": 2, "sin_evidencia": 0, "pct": Decimal("50.0")}
    base = K.Base(filas={"701": {"6.1": {"99701001": 3, "99701002": 1}}}, cifras={"701": {"6.1": cifras}},
                  cargas={"701": {1}})
    base.curso = _curso(1, 2, "50.0", promedio, 0, {"701": ("50.0", promedio)})
    return base


TABLA = {"701": {"6.1": {"99701001": 3, "99701002": 1}}}


def test_una_seccion_igual_en_todo_y_con_el_curso_igual_termina_en_0() -> None:
    codigo, lineas = K.conciliar(TABLA, _base_de_una_seccion("2.00"), "6.1", None, con_curso=True)
    assert codigo == 0
    assert lineas == ["Sección 701. Igual en 2 de 2 estudiantes, en el conteo por nivel y en el porcentaje.",
                      "Sección 701. Con promedio igual.",
                      "Curso igual en alumnos en el nivel esperado o superior, en el porcentaje, en el promedio y en las "
                      "secciones en la meta.",
                      "1 de 1 secciones iguales."]


def test_un_promedio_distinto_hace_distinta_a_la_seccion_aunque_todo_lo_demas_sea_igual() -> None:
    codigo, lineas = K.conciliar(TABLA, _base_de_una_seccion("2.10"), "6.1", None, con_curso=True)
    assert codigo == 1
    assert "Sección 701. Distinta en el promedio." in lineas
    assert not any(linea.startswith("Sección 701. Igual") for linea in lineas)
    assert lineas[-1] == "0 de 1 secciones iguales."


def test_sin_con_curso_el_informe_no_trae_lineas_del_promedio_ni_del_curso() -> None:
    codigo, lineas = K.conciliar(TABLA, _base_de_una_seccion("2.10"), "6.1", None)
    assert codigo == 0
    assert lineas == ["Sección 701. Igual en 2 de 2 estudiantes, en el conteo por nivel y en el porcentaje.",
                      "1 de 1 secciones iguales."]


def test_un_curso_distinto_solo_en_las_secciones_en_la_meta_termina_en_1_con_las_secciones_iguales() -> None:
    base = _base_de_una_seccion("2.00")
    base.curso = _curso(1, 2, "50.0", "2.00", 1, {"701": ("50.0", "2.00")})
    codigo, lineas = K.conciliar(TABLA, base, "6.1", None, con_curso=True)
    assert codigo == 1
    assert "Curso distinto en las secciones en la meta." in lineas
    assert lineas[-1] == "1 de 1 secciones iguales."
