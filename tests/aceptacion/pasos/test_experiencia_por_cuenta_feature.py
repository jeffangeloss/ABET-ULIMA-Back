"""Pasos de la etapa A de la spec 007-experiencia-por-cuenta (US-59 a US-63), con pytest-bdd (T013 y T030).

El .feature manda. Ningún paso cambia un nombre de columna ni un resultado para que el escenario pase.

- El esquema del lector de antes_de_subir.feature (US-60, T030) corre en el Back sin base. Arma en memoria un .xls
  de texto con Username y la columna del encabezado, como test_exports_blackboard_feature.py, y lo lee con
  abet_carga/lector.py sin cambios. Ningún paso pide la fixture ctx de conftest.py, así que la prueba no arranca el
  clúster desechable ni lleva el marcador base.
- Los escenarios de pantalla llevan @delegado_a_vitest y escriben la sesión con «una sesión de "…" con rol "…"» o «la
  cuenta "…" con rol "…"», un texto que la expresión _sesion_iniciada de conftest.py no captura. Su paso
  _pantalla_dada solo llama a _delegar(), sin abrir la base, y registra la propiedad «delegado_a_vitest» con las
  pruebas de Vitest del Front anotadas en CUBIERTO_POR_VITEST (FR-017). Esas pruebas llegan con T040 a T044, y
  cada escenario de pantalla se enlaza aquí junto con su prueba. Hasta entonces un escenario de pantalla sin sus
  pruebas anotadas hace fallar sus pasos.
"""

from __future__ import annotations

import re
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from pytest_bdd.feature import get_features
from pytest_bdd.scenario import scenario_wrapper_template_registry
from pytest_bdd.steps import StepFunctionContext, step_function_context_registry

from abet_carga.lector import leer
from abet_carga.modelos import ColumnaLeida, TipoColumna

RAIZ = Path(__file__).resolve().parents[3]
ACEPTACION = "specs/007-experiencia-por-cuenta/aceptacion"
ANTES_DE_SUBIR = f"{ACEPTACION}/antes_de_subir.feature"
# Archivos de la spec 007 con escenarios de pantalla. avance_del_registro.feature es de la etapa B.
CON_PANTALLA = tuple(f"{ACEPTACION}/{nombre}.feature" for nombre in
                     ("siguiente_paso", "antes_de_subir", "que_corregir", "rotulos_por_cuenta", "avance_del_registro"))
XLS_410 = "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls"


@scenario(ANTES_DE_SUBIR, "El lector de exports reconoce el nombre que propone P3 y no el que lleva guiones")
def test_el_lector_reconoce_el_nombre_que_propone_p3() -> None:
    """US-60, T030. El lector acepta «ABET SO5.1 [» y «ABET SO6.10 [», y no la forma con guiones de hoy."""


# El lector, con un .xls de texto de dos columnas y sin base

def _clasificado(generador: ModuleType, encabezado: str) -> ColumnaLeida:
    """Columna que el lector arma con el encabezado, en un .xls de texto con Username y un nivel."""
    export = generador.Export("", ("Username", encabezado), (("99000001", "4"),))
    contenido = generador.a_texto(export, separador="\t", codificacion="utf-16")
    libro = leer(contenido, nombre_archivo=XLS_410)
    assert [c.tipo for c in libro.columnas][0] is TipoColumna.CODIGO
    return libro.columnas[1]


@given(parsers.re(r"el encabezado de Blackboard «(?P<encabezado>[^»]+)»"), target_fixture="encabezado")
def _el_encabezado(encabezado: str) -> str:
    return encabezado


@when("el lector de exports de abet_carga/lector.py clasifica la columna", target_fixture="columna")
def _clasifica(generador: ModuleType, encabezado: str) -> ColumnaLeida:
    return _clasificado(generador, encabezado)


@then(parsers.re(r"la columna queda como columna del PI (?P<pi>[0-9]+\.[0-9]+)"))
def _columna_del_pi(columna: ColumnaLeida, encabezado: str, pi: str) -> None:
    assert (columna.tipo, columna.pi_codigo) == (TipoColumna.PI, pi), (columna.tipo, columna.pi_codigo)
    # El encabezado que va a la base es el que el lector clasificó, y el número de Blackboard sale tras «|».
    assert columna.encabezado == encabezado
    assert columna.bb_columna_id == encabezado.rsplit("|", 1)[1]


@then("la columna queda como columna que no es de un PI")
def _columna_que_no_es_de_un_pi(columna: ColumnaLeida) -> None:
    assert (columna.tipo, columna.pi_codigo) == (TipoColumna.OTRA, None), (columna.tipo, columna.pi_codigo)


# Pantallas de la etapa A, delegadas a Vitest

# Escenario de pantalla y pruebas de Vitest del Front que lo comprueban, con el nombre que da Vitest. T040 a T044
# suman cada entrada junto con su prueba y el enlace de su escenario.
CUBIERTO_POR_VITEST: dict[str, list[str]] = {}


def _delegar(request: pytest.FixtureRequest, texto: str) -> None:
    """Deja constancia de un paso de pantalla y de las pruebas de Vitest del Front que comprueban su escenario."""
    escenario = scenario_wrapper_template_registry[request.node.function].name
    pruebas = CUBIERTO_POR_VITEST.get(escenario)
    assert pruebas, f"el escenario de pantalla «{escenario}» no tiene pruebas de Vitest anotadas"
    request.node.user_properties.append(("delegado_a_vitest", f"{texto} → {'; '.join(pruebas)}"))


@given(parsers.re(r'(?P<texto>una sesión (?:de "[^"]+" )?con rol "[A-Z]+".*|la cuenta "[^"]+" con rol "[A-Z]+".*)'))
def _pantalla_dada(request: pytest.FixtureRequest, texto: str) -> None:
    _delegar(request, texto)


# Comprobaciones de los pasos, fuera de los escenarios

def _contexto(nombre: str, archivo: str) -> StepFunctionContext:
    """Paso de pytest-bdd con ese nombre de función, definido en el archivo de esta carpeta que termina en archivo."""
    contextos = [c for c in list(step_function_context_registry.values())
                 if c.step_func.__name__ == nombre and c.step_func.__code__.co_filename.endswith(archivo)]
    assert len(contextos) == 1, f"{archivo} define {len(contextos)} pasos {nombre}"
    return contextos[0]


def _pasos_de_sesion_de_pantalla() -> list[tuple[str, str]]:
    """Escenario y texto de cada paso de sesión de un escenario @delegado_a_vitest, con cada fila de Ejemplos escrita."""
    pasos = []
    for ruta in CON_PANTALLA:
        [feature] = get_features([str(RAIZ / ruta)])
        for escenario in feature.scenarios.values():
            if "delegado_a_vitest" not in escenario.tags:
                continue
            filas = [fila for tabla in escenario.examples for fila in tabla.as_contexts()] if escenario.templated else [{}]
            for fila in filas:
                pasos += [(escenario.name, paso.name) for paso in escenario.render(fila).steps
                          if paso.name.startswith(("una sesión ", "la cuenta "))]
    return pasos


def test_la_sesion_de_un_escenario_de_pantalla_va_a_pantalla_dada_y_no_a_sesion_iniciada() -> None:
    # T013 y FR-017. Cada paso de sesión de un escenario de pantalla lo atiende _pantalla_dada, que no abre la base,
    # y ninguno coincide con _sesion_iniciada de conftest.py, que exige la base y pide la API.
    pantalla_dada = _contexto("_pantalla_dada", "test_experiencia_por_cuenta_feature.py")
    sesion_iniciada = _contexto("_sesion_iniciada", "aceptacion/pasos/conftest.py")
    pasos = _pasos_de_sesion_de_pantalla()

    assert {texto.split('"', 1)[0] for _, texto in pasos} == {"una sesión de ", "una sesión con rol ", "la cuenta "}
    for escenario, texto in pasos:
        assert pantalla_dada.type == sesion_iniciada.type == "given"
        assert pantalla_dada.parser.is_matching(texto), f"{escenario}: «{texto}»"
        assert not sesion_iniciada.parser.is_matching(texto), f"{escenario}: «{texto}»"
    # Lo que no debe pasar. La frase de la sesión con base sigue en _sesion_iniciada y no en _pantalla_dada.
    con_base = '"docente410@example.invalid" tiene la sesión iniciada con rol "PROFESOR"'
    assert sesion_iniciada.parser.is_matching(con_base)
    assert not pantalla_dada.parser.is_matching(con_base)


def _nombres_que_propone_p3() -> list[str]:
    """Nombres de columna de las líneas «En Blackboard, una columna por PI, …» de antes_de_subir.feature."""
    lineas = [linea for linea in (RAIZ / ANTES_DE_SUBIR).read_text(encoding="utf-8").splitlines()
              if "En Blackboard, una columna por PI, con el nombre " in linea]
    return sorted({nombre for linea in lineas for nombre in re.findall(r"ABET SO[0-9]+\.[0-9]+", linea)})


def test_cada_nombre_que_propone_p3_lo_lee_el_lector_como_su_pi(generador: ModuleType) -> None:
    # T030 y FR-001. Los nombres de las líneas de P3 son los de la constante del Front (J-44), y el lector los acepta
    # con el «[Total Pts: …]» que Blackboard pone detrás. Sin ese corchete, la columna no es de un PI.
    nombres = _nombres_que_propone_p3()

    assert nombres == ["ABET SO5.1", "ABET SO5.2", "ABET SO5.3", "ABET SO6.1", "ABET SO6.10"]
    for nombre in nombres:
        columna = _clasificado(generador, f"{nombre} [Total Pts: 4 Score] |9000051")
        assert (columna.tipo, columna.pi_codigo) == (TipoColumna.PI, nombre.removeprefix("ABET SO")), nombre
        assert _clasificado(generador, nombre).tipo is TipoColumna.OTRA, nombre
