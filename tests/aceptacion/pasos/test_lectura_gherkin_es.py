"""T010. pytest-bdd 9 lee en español los escenarios de los .feature de specs/, sin copiarlos ni moverlos.

Resultado de la prueba de tasks.md. pytest-bdd 9.0.0, con el analizador oficial de Gherkin
(gherkin-official 42), reconoce `# language: es` con Característica, Antecedentes, Escenario,
Esquema del escenario, Ejemplos y los pasos Dado, Cuando, Entonces, Y y Pero, así que behave con
lang = es no hace falta.

Los pasos ejecutables llegan con T050. Hasta entonces, scenarios() arma sus funciones de prueba
dentro de clases que pytest no recoge (su nombre no empieza con Test). Así se comprueba que la ruta
relativa y la lectura funcionan sin dejar la suite en rojo por pasos sin definir y sin escenarios
que pasan con pasos vacíos. Los conteos de referencia salen del texto del archivo con expresiones
regulares, sin el analizador de Gherkin, de modo que un cambio válido del .feature (otro título,
otro paso en Antecedentes u otra tabla de Ejemplos) mueve el texto y lo leído por igual. Los
nombres exactos de los pasos quedan para T050.

La prueba lee lo que arma el analizador con tres objetos de pytest-bdd que no están en su
`__all__` (get_features, Feature y scenario_wrapper_template_registry). Por eso pyproject.toml
admite solo parches de pytest-bdd (~=9.0.0), y una versión nueva entra solo si esta prueba pasa con
ella.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pytest_bdd import scenarios
from pytest_bdd.feature import get_features
from pytest_bdd.parser import Feature
from pytest_bdd.scenario import scenario_wrapper_template_registry

RAIZ = Path(__file__).resolve().parents[3]
CARGA = "specs/001-mvp-carga-r17/aceptacion/carga.feature"
R17 = "specs/001-mvp-carga-r17/aceptacion/r17_constancia.feature"
EXPORTS = "specs/003-exports-blackboard/aceptacion/exports_blackboard.feature"


class _EscenariosDeCarga:
    """Funciones que scenarios() arma para carga.feature con la ruta relativa a la raíz."""

    scenarios(CARGA)


class _EscenariosDeR17:
    """Funciones que scenarios() arma para r17_constancia.feature con la ruta relativa a la raíz."""

    scenarios(R17)


class _EscenariosDeExports:
    """Funciones que scenarios() arma para exports_blackboard.feature (spec 003) con la ruta relativa a la raíz."""

    scenarios(EXPORTS)


_ARMADAS = {CARGA: _EscenariosDeCarga, R17: _EscenariosDeR17, EXPORTS: _EscenariosDeExports}
_POR_ARCHIVO = pytest.mark.parametrize("ruta", [CARGA, R17, EXPORTS], ids=["carga", "r17_constancia", "exports_blackboard"])
_ENCABEZADO = re.compile(r"^[ \t]*(Escenario|Esquema del escenario):[ \t]*(.+?)[ \t]*$", re.MULTILINE)
_CARACTERISTICA = re.compile(r"^[ \t]*Característica:[ \t]*(.+?)[ \t]*$", re.MULTILINE)
# Palabras de paso del español de Gherkin (gherkin-languages.json), sin el asterisco. Y, E y Pero
# toman el tipo del paso anterior.
_TIPO_DE = {"Dado": "given", "Dada": "given", "Dados": "given", "Dadas": "given", "Cuando": "when", "Entonces": "then"}
_CONTINUAN = ("Y", "E", "Pero")
_PASO = re.compile(r"^[ \t]*(Dado|Dada|Dados|Dadas|Cuando|Entonces|Y|E|Pero)[ \t]")


def _texto(ruta: str) -> str:
    return (RAIZ / ruta).read_text(encoding="utf-8")


def _encabezados(ruta: str) -> list[tuple[str, str]]:
    """Palabra clave y nombre de cada escenario, leídos del texto sin analizador de Gherkin."""
    return _ENCABEZADO.findall(_texto(ruta))


def _titulo(ruta: str) -> str:
    """Nombre de la Característica, leído del texto."""
    [titulo] = _CARACTERISTICA.findall(_texto(ruta))
    return titulo


def _pasos_de_antecedentes(ruta: str) -> list[tuple[str, str | None]]:
    """Palabra clave y tipo de cada paso de Antecedentes, leídos del texto."""
    pasos: list[tuple[str, str | None]] = []
    dentro, anterior = False, None
    for linea in _texto(ruta).splitlines():
        limpia = linea.strip()
        if limpia.startswith("Antecedentes:"):
            dentro = True
        elif dentro and (limpia.startswith(("@", "Regla:")) or _ENCABEZADO.match(linea)):
            break
        elif dentro and (paso := _PASO.match(linea)):
            palabra = paso.group(1)
            anterior = _TIPO_DE.get(palabra, anterior)
            pasos.append((palabra, anterior))
    return pasos


def _tablas_de_ejemplos(ruta: str) -> dict[str, list[tuple[str, int]]]:
    """Nombre y filas de datos de cada tabla de Ejemplos, por esquema, leídos del texto."""
    tablas: dict[str, list[list]] = {}
    esquema, en_tabla, con_encabezado = None, False, False
    for linea in _texto(ruta).splitlines():
        limpia = linea.strip()
        if encabezado := _ENCABEZADO.match(linea):
            palabra, nombre = encabezado.groups()
            esquema = nombre if palabra == "Esquema del escenario" else None
            if esquema is not None:
                tablas[esquema] = []
            en_tabla = False
        elif esquema is not None and limpia.startswith("Ejemplos:"):
            tablas[esquema].append([limpia.removeprefix("Ejemplos:").strip(), 0])
            en_tabla, con_encabezado = True, False
        elif en_tabla and limpia.startswith("|"):
            if con_encabezado:
                tablas[esquema][-1][1] += 1
            con_encabezado = True
        elif en_tabla and limpia and not limpia.startswith("#"):
            en_tabla = False
    return {nombre: [(tabla, filas) for tabla, filas in lista] for nombre, lista in tablas.items()}


def _filas_de_ejemplos(ruta: str) -> int:
    """Filas de datos de las tablas de Ejemplos, sin contar la fila de encabezado de cada tabla."""
    filas, en_tabla, con_encabezado = 0, False, False
    for linea in _texto(ruta).splitlines():
        limpia = linea.strip()
        if limpia.startswith("Ejemplos:"):
            en_tabla, con_encabezado = True, False
        elif en_tabla and limpia.startswith("|"):
            filas += 1 if con_encabezado else 0
            con_encabezado = True
        elif en_tabla and limpia and not limpia.startswith("#"):
            en_tabla = False
    return filas


def _feature(ruta: str) -> Feature:
    [feature] = get_features([str(RAIZ / ruta)])
    return feature


@_POR_ARCHIVO
def test_scenarios_arma_una_funcion_por_escenario_desde_specs(ruta: str) -> None:
    funciones = [f for nombre, f in vars(_ARMADAS[ruta]).items() if nombre.startswith("test_")]
    plantillas = [scenario_wrapper_template_registry[f] for f in funciones]
    encabezados = _encabezados(ruta)

    assert len(encabezados) > 0
    assert len(funciones) == len(encabezados)
    assert sorted(p.name for p in plantillas) == sorted(nombre for _, nombre in encabezados)
    # La ruta relativa se resuelve desde la raíz (bdd_features_base_dir = "."), sin copias en tests/.
    assert {Path(p.feature.filename) for p in plantillas} == {RAIZ / ruta}
    assert not list((RAIZ / "tests").rglob("*.feature"))


@_POR_ARCHIVO
def test_cada_esquema_trae_todas_las_filas_de_sus_ejemplos(ruta: str) -> None:
    feature = _feature(ruta)
    esquemas = [e for e in feature.scenarios.values() if e.templated]
    lineas = _texto(ruta).splitlines()

    assert len(esquemas) == sum(1 for palabra, _ in _encabezados(ruta) if palabra == "Esquema del escenario")
    assert sum(len(t.examples) for e in esquemas for t in e.examples) == _filas_de_ejemplos(ruta)
    # Cada esquema trae las mismas tablas que el texto, con su nombre (vacío en «Ejemplos:» sin nombre)
    # y su número de filas.
    leidas = {e.name: [(t.name or "", len(t.examples)) for t in e.examples] for e in esquemas}
    assert leidas == _tablas_de_ejemplos(ruta)
    for esquema in esquemas:
        assert esquema.examples, esquema.name
        texto_de_pasos = " ".join(paso.name for paso in esquema.steps)
        for tabla in esquema.examples:
            assert lineas[tabla.line_number - 1].strip().startswith("Ejemplos:")
            assert tabla.examples, f"{esquema.name}: una tabla de Ejemplos sin filas"
            for parametro in tabla.example_params:
                assert f"<{parametro}>" in texto_de_pasos, f"{esquema.name}: <{parametro}> no aparece en los pasos"
    for escenario in feature.scenarios.values():
        if not escenario.templated:
            assert not escenario.examples, escenario.name


@_POR_ARCHIVO
def test_la_caracteristica_y_sus_antecedentes_se_leen_como_en_el_texto(ruta: str) -> None:
    feature = _feature(ruta)
    pasos = _pasos_de_antecedentes(ruta)

    assert feature.keyword == "Característica"
    assert feature.name == _titulo(ruta)
    assert feature.background is not None and pasos
    assert _texto(ruta).splitlines()[feature.background.line_number - 1].strip() == "Antecedentes:"
    assert [(p.keyword.strip(), p.type) for p in feature.background.steps] == pasos


def test_el_analizador_reconoce_las_palabras_clave_en_espanol() -> None:
    feature = _feature(CARGA)

    assert feature.language == "es"
    assert {e.keyword for e in feature.scenarios.values()} == {"Escenario", "Esquema del escenario"}

    palabras = {p.keyword.strip() for e in feature.scenarios.values() for p in e.steps}
    assert {"Dado", "Cuando", "Entonces", "Y", "Pero"} <= palabras


def test_cada_paso_toma_el_tipo_de_su_palabra_clave() -> None:
    feature = _feature(CARGA)
    for escenario in feature.scenarios.values():
        anterior = None
        for paso in escenario.steps:
            palabra = paso.keyword.strip()
            if palabra in _CONTINUAN:
                assert anterior is not None, f"{escenario.name}: «{palabra}» abre la lista de pasos"
                assert paso.type == anterior, f"{escenario.name}: «{palabra} {paso.name}»"
            else:
                assert paso.type == _TIPO_DE[palabra], f"{escenario.name}: «{palabra} {paso.name}»"
            anterior = paso.type
    assert [p for e in feature.scenarios.values() for p in e.steps if p.keyword.strip() == "Pero"]


@_POR_ARCHIVO
def test_ningun_escenario_queda_vacio(ruta: str) -> None:
    for escenario in _feature(ruta).scenarios.values():
        propios = [p for p in escenario.steps if p.background is None]
        assert propios, f"{escenario.name}: sin pasos"
        assert any(p.type == "then" for p in propios), f"{escenario.name}: sin un Entonces que compruebe algo"


@_POR_ARCHIVO
def test_cada_escenario_lleva_su_historia_y_su_corte(ruta: str) -> None:
    # Constitución, principio V. Cada escenario lleva @US-NN y @corte1 o @corte2.
    for escenario in _feature(ruta).scenarios.values():
        historias = [t for t in escenario.tags if re.fullmatch(r"US-\d{2}", t)]
        cortes = [t for t in escenario.tags if t in ("corte1", "corte2")]
        assert len(historias) == 1, f"{escenario.name}: {sorted(escenario.tags)}"
        assert len(cortes) == 1, f"{escenario.name}: {sorted(escenario.tags)}"
