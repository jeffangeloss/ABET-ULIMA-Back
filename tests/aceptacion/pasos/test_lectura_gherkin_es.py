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

import ast
import re
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import scenarios
from pytest_bdd.feature import get_features
from pytest_bdd.parser import Feature
from pytest_bdd.scenario import scenario_wrapper_template_registry

RAIZ = Path(__file__).resolve().parents[3]
CARGA = "specs/001-mvp-carga-r17/aceptacion/carga.feature"
R17 = "specs/001-mvp-carga-r17/aceptacion/r17_constancia.feature"
EXPORTS = "specs/003-exports-blackboard/aceptacion/exports_blackboard.feature"
RESULTADOS = "specs/004-reportes-docente/aceptacion/resultados.feature"
ALCANCE = "specs/004-reportes-docente/aceptacion/alcance_y_privacidad.feature"
# Los cuatro archivos de la spec 005, con las historias que spec.md asigna a cada uno (T012 de su tasks.md).
HISTORIAS_DE_LA_SPEC_005 = {"semaforo": (45, 46), "declaracion": (47, 48, 49, 53, 54), "r17_desde_la_base": (50, 51),
                            "navegacion": (52,)}
SPEC_005 = tuple(f"specs/005-oportunidades-de-mejora/aceptacion/{nombre}.feature" for nombre in HISTORIAS_DE_LA_SPEC_005)
PROGRAMACION = "specs/006-programacion-docente/aceptacion/programacion_docente.feature"
SIN_DOCENTE = "specs/006-programacion-docente/aceptacion/secciones_sin_docente.feature"
SIGUIENTE_PASO = "specs/007-experiencia-por-cuenta/aceptacion/siguiente_paso.feature"
ANTES_DE_SUBIR = "specs/007-experiencia-por-cuenta/aceptacion/antes_de_subir.feature"
QUE_CORREGIR = "specs/007-experiencia-por-cuenta/aceptacion/que_corregir.feature"
ROTULOS = "specs/007-experiencia-por-cuenta/aceptacion/rotulos_por_cuenta.feature"
AVANCE = "specs/007-experiencia-por-cuenta/aceptacion/avance_del_registro.feature"
SPEC_007 = (SIGUIENTE_PASO, ANTES_DE_SUBIR, QUE_CORREGIR, ROTULOS, AVANCE)
# Los doce archivos de la spec 008, con las historias que spec.md asigna a cada uno (T013 de su tasks.md).
HISTORIAS_DE_LA_SPEC_008 = {
    "catalogo_industrial": (67, 68, 69), "alcance_coordinacion": (70, 71, 72), "periodo_elegido": (73,),
    "exports_capacitacion": (74,), "carga_quimica": (75, 76, 77), "r17_industrial": (78,),
    "avance_del_curso": (79, 80), "sistema_visual": (81, 82), "ensayo_y_conciliacion": (83, 84),
    "capacitacion_en_develop": (85, 86, 89), "guia_y_privacidad": (87, 88), "matriz_cumplimiento": (90,),
}
SPEC_008_DIR = "specs/008-ciclo-quimica-industrial/aceptacion"
SPEC_008 = tuple(f"{SPEC_008_DIR}/{nombre}.feature" for nombre in HISTORIAS_DE_LA_SPEC_008)
# Archivos sin Antecedentes (spec 007, FR-017). El esquema del lector de antes_de_subir.feature corre sin base y
# no hereda ninguna sesión, y cada escenario de rotulos_por_cuenta.feature escribe su propia sesión. En la spec 008,
# los escenarios de la siembra, la guía, la privacidad, la matriz y el sistema visual arman cada uno lo suyo.
SIN_ANTECEDENTES = frozenset({ANTES_DE_SUBIR, ROTULOS, *(ruta for ruta in SPEC_008 if any(
    nombre in ruta for nombre in ("capacitacion_en_develop", "guia_y_privacidad", "matriz_cumplimiento",
                                  "sistema_visual")))})


class _EscenariosDeCarga:
    """Funciones que scenarios() arma para carga.feature con la ruta relativa a la raíz."""

    scenarios(CARGA)


class _EscenariosDeR17:
    """Funciones que scenarios() arma para r17_constancia.feature con la ruta relativa a la raíz."""

    scenarios(R17)


class _EscenariosDeExports:
    """Funciones que scenarios() arma para exports_blackboard.feature (spec 003) con la ruta relativa a la raíz."""

    scenarios(EXPORTS)


class _EscenariosDeResultados:
    """Funciones que scenarios() arma para resultados.feature (spec 004) con la ruta relativa a la raíz."""

    scenarios(RESULTADOS)


class _EscenariosDeAlcance:
    """Funciones que scenarios() arma para alcance_y_privacidad.feature (spec 004) con la ruta relativa a la raíz."""

    scenarios(ALCANCE)


class _EscenariosDelSemaforo:
    """Funciones que scenarios() arma para semaforo.feature (spec 005) con la ruta relativa a la raíz."""

    scenarios(SPEC_005[0])


class _EscenariosDeLaDeclaracion:
    """Funciones que scenarios() arma para declaracion.feature (spec 005) con la ruta relativa a la raíz."""

    scenarios(SPEC_005[1])


class _EscenariosDelR17DesdeLaBase:
    """Funciones que scenarios() arma para r17_desde_la_base.feature (spec 005) con la ruta relativa a la raíz."""

    scenarios(SPEC_005[2])


class _EscenariosDeLaNavegacion:
    """Funciones que scenarios() arma para navegacion.feature (spec 005) con la ruta relativa a la raíz."""

    scenarios(SPEC_005[3])


class _EscenariosDeProgramacion:
    """Funciones que scenarios() arma para programacion_docente.feature (spec 006) con la ruta relativa a la raíz."""

    scenarios(PROGRAMACION)


class _EscenariosSinDocente:
    """Funciones que scenarios() arma para secciones_sin_docente.feature (spec 006) con la ruta relativa a la raíz."""

    scenarios(SIN_DOCENTE)


class _EscenariosDelSiguientePaso:
    """Funciones que scenarios() arma para siguiente_paso.feature (spec 007) con la ruta relativa a la raíz."""

    scenarios(SIGUIENTE_PASO)


class _EscenariosDeAntesDeSubir:
    """Funciones que scenarios() arma para antes_de_subir.feature (spec 007) con la ruta relativa a la raíz."""

    scenarios(ANTES_DE_SUBIR)


class _EscenariosDeQueCorregir:
    """Funciones que scenarios() arma para que_corregir.feature (spec 007) con la ruta relativa a la raíz."""

    scenarios(QUE_CORREGIR)


class _EscenariosDeRotulos:
    """Funciones que scenarios() arma para rotulos_por_cuenta.feature (spec 007) con la ruta relativa a la raíz."""

    scenarios(ROTULOS)


class _EscenariosDelAvance:
    """Funciones que scenarios() arma para avance_del_registro.feature (spec 007) con la ruta relativa a la raíz."""

    scenarios(AVANCE)


class _EscenariosDeCatalogoIndustrial:
    """Funciones que scenarios() arma para catalogo_industrial.feature (spec 008) con la ruta relativa a la raíz."""

    scenarios(f"{SPEC_008_DIR}/catalogo_industrial.feature")


class _EscenariosDeAlcanceCoordinacion:
    """Funciones que scenarios() arma para alcance_coordinacion.feature (spec 008) con la ruta relativa a la raíz."""

    scenarios(f"{SPEC_008_DIR}/alcance_coordinacion.feature")


class _EscenariosDePeriodoElegido:
    """Funciones que scenarios() arma para periodo_elegido.feature (spec 008) con la ruta relativa a la raíz."""

    scenarios(f"{SPEC_008_DIR}/periodo_elegido.feature")


class _EscenariosDeExportsCapacitacion:
    """Funciones que scenarios() arma para exports_capacitacion.feature (spec 008) con la ruta relativa a la raíz."""

    scenarios(f"{SPEC_008_DIR}/exports_capacitacion.feature")


class _EscenariosDeCargaQuimica:
    """Funciones que scenarios() arma para carga_quimica.feature (spec 008) con la ruta relativa a la raíz."""

    scenarios(f"{SPEC_008_DIR}/carga_quimica.feature")


class _EscenariosDeR17Industrial:
    """Funciones que scenarios() arma para r17_industrial.feature (spec 008) con la ruta relativa a la raíz."""

    scenarios(f"{SPEC_008_DIR}/r17_industrial.feature")


class _EscenariosDeAvanceDelCurso:
    """Funciones que scenarios() arma para avance_del_curso.feature (spec 008) con la ruta relativa a la raíz."""

    scenarios(f"{SPEC_008_DIR}/avance_del_curso.feature")


class _EscenariosDeSistemaVisual:
    """Funciones que scenarios() arma para sistema_visual.feature (spec 008) con la ruta relativa a la raíz."""

    scenarios(f"{SPEC_008_DIR}/sistema_visual.feature")


class _EscenariosDeEnsayoYConciliacion:
    """Funciones que scenarios() arma para ensayo_y_conciliacion.feature (spec 008) con la ruta relativa a la raíz."""

    scenarios(f"{SPEC_008_DIR}/ensayo_y_conciliacion.feature")


class _EscenariosDeCapacitacionEnDevelop:
    """Funciones que scenarios() arma para capacitacion_en_develop.feature (spec 008) con la ruta relativa a la raíz."""

    scenarios(f"{SPEC_008_DIR}/capacitacion_en_develop.feature")


class _EscenariosDeGuiaYPrivacidad:
    """Funciones que scenarios() arma para guia_y_privacidad.feature (spec 008) con la ruta relativa a la raíz."""

    scenarios(f"{SPEC_008_DIR}/guia_y_privacidad.feature")


class _EscenariosDeMatrizCumplimiento:
    """Funciones que scenarios() arma para matriz_cumplimiento.feature (spec 008) con la ruta relativa a la raíz."""

    scenarios(f"{SPEC_008_DIR}/matriz_cumplimiento.feature")


_ARMADAS = {CARGA: _EscenariosDeCarga, R17: _EscenariosDeR17, EXPORTS: _EscenariosDeExports,
            RESULTADOS: _EscenariosDeResultados, ALCANCE: _EscenariosDeAlcance,
            **dict(zip(SPEC_005, (_EscenariosDelSemaforo, _EscenariosDeLaDeclaracion, _EscenariosDelR17DesdeLaBase,
                                  _EscenariosDeLaNavegacion), strict=True)),
            PROGRAMACION: _EscenariosDeProgramacion, SIN_DOCENTE: _EscenariosSinDocente,
            SIGUIENTE_PASO: _EscenariosDelSiguientePaso, ANTES_DE_SUBIR: _EscenariosDeAntesDeSubir,
            QUE_CORREGIR: _EscenariosDeQueCorregir, ROTULOS: _EscenariosDeRotulos, AVANCE: _EscenariosDelAvance,
            **{ruta: clase for ruta, clase in zip(SPEC_008, (_EscenariosDeCatalogoIndustrial, _EscenariosDeAlcanceCoordinacion, _EscenariosDePeriodoElegido, _EscenariosDeExportsCapacitacion, _EscenariosDeCargaQuimica, _EscenariosDeR17Industrial, _EscenariosDeAvanceDelCurso, _EscenariosDeSistemaVisual, _EscenariosDeEnsayoYConciliacion, _EscenariosDeCapacitacionEnDevelop, _EscenariosDeGuiaYPrivacidad, _EscenariosDeMatrizCumplimiento), strict=True)}}
_POR_ARCHIVO = pytest.mark.parametrize("ruta", list(_ARMADAS),
                                       ids=["carga", "r17_constancia", "exports_blackboard", "resultados",
                                            "alcance_y_privacidad", *HISTORIAS_DE_LA_SPEC_005, "programacion_docente", "secciones_sin_docente",
                                            "siguiente_paso", "antes_de_subir", "que_corregir", "rotulos_por_cuenta",
                                            "avance_del_registro", *HISTORIAS_DE_LA_SPEC_008])
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
    if ruta in SIN_ANTECEDENTES:
        assert feature.background is None and not pasos
        assert "Antecedentes:" not in [linea.strip() for linea in _texto(ruta).splitlines()]
        return
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


@pytest.mark.parametrize("ruta", [RESULTADOS, ALCANCE], ids=["resultados", "alcance_y_privacidad"])
def test_cada_escenario_de_la_spec_004_lleva_su_etiqueta_y_la_pantalla_va_a_vitest(ruta: str) -> None:
    # spec.md de la spec 004. Cada escenario lleva @spec004, y uno que abre o nombra la pantalla P6 lleva además
    # @delegado_a_vitest, porque lo prueba Vitest en el Front y no pytest-bdd.
    for escenario in _feature(ruta).scenarios.values():
        assert "spec004" in escenario.tags, f"{escenario.name}: {sorted(escenario.tags)}"
        pantalla = escenario.name.startswith("P6 ") or any("P6" in paso.name for paso in escenario.steps)
        assert pantalla == ("delegado_a_vitest" in escenario.tags), f"{escenario.name}: {sorted(escenario.tags)}"


def test_la_spec_005_trae_85_escenarios_con_118_casos_y_23_van_a_vitest() -> None:
    # T003 y T012 de specs/005-oportunidades-de-mejora/tasks.md, con los cuatro .feature definitivos del 2026-11-24.
    # Cada escenario lleva @spec005, @corte1 y una sola historia de las que spec.md asigna a su archivo. Un escenario
    # que nombra una pantalla, de P1 a P7, lleva @delegado_a_vitest y ninguno más, porque lo prueba Vitest en el Front.
    # Los Antecedentes de los tres archivos con base piden V1_15, la migración de la spec (FR-004 de la spec 008).
    escenarios, casos, delegados, historias = 0, 0, 0, set()
    for nombre, ruta in zip(HISTORIAS_DE_LA_SPEC_005, SPEC_005, strict=True):
        propias = {f"US-{n}" for n in HISTORIAS_DE_LA_SPEC_005[nombre]}
        feature = _feature(ruta)
        for escenario in feature.scenarios.values():
            escenarios += 1
            casos += sum(len(t.examples) for t in escenario.examples) if escenario.templated else 1
            assert {"spec005", "corte1"} <= set(escenario.tags), f"{escenario.name}: {sorted(escenario.tags)}"
            [historia] = [t for t in escenario.tags if re.fullmatch(r"US-\d{2}", t)]
            assert historia in propias, f"{nombre}: «{escenario.name}» lleva {historia}"
            historias.add(historia)
            pantalla = bool(_PANTALLA.search(escenario.name)) or any(_PANTALLA.search(p.name) for p in escenario.steps)
            assert pantalla == ("delegado_a_vitest" in escenario.tags), f"{escenario.name}: {sorted(escenario.tags)}"
            delegados += pantalla
        if nombre != "navegacion":
            [base] = [p.name for p in feature.background.steps if p.name.startswith("una base PostgreSQL 18")]
            assert "con las migraciones V1_01 a V1_15" in base, f"{nombre}: {base}"
        assert "V1_12" not in " ".join(e.name for e in feature.scenarios.values()), nombre
    assert (escenarios, casos, delegados) == (85, 118, 23)
    assert historias == {f"US-{n}" for n in range(45, 55)}


def _titulos_enlazados() -> set[str]:
    """Títulos que algún módulo de pasos enlaza con @scenario(FEATURE, «título»), leídos del código sin importarlo."""
    titulos = set()
    for modulo in (RAIZ / "tests" / "aceptacion" / "pasos").glob("test_*.py"):
        for nodo in ast.walk(ast.parse(modulo.read_text(encoding="utf-8"))):
            if (isinstance(nodo, ast.Call) and getattr(nodo.func, "id", None) == "scenario" and len(nodo.args) >= 2
                    and isinstance(nodo.args[1], ast.Constant)):
                titulos.add(nodo.args[1].value)
    return titulos


def test_cada_escenario_de_la_spec_005_sin_vitest_tiene_su_paso_de_pytest_bdd() -> None:
    # T038 de specs/005-oportunidades-de-mejora/tasks.md. Un escenario sin @delegado_a_vitest que ningún módulo enlaza
    # con @scenario no corre en ninguna parte, así que esta prueba lo nombra antes de que quede sin probar.
    enlazados = _titulos_enlazados()
    sin_enlace = [f"{ruta.rsplit('/', 1)[1]}: {escenario.name}" for ruta in SPEC_005
                  for escenario in _feature(ruta).scenarios.values()
                  if "delegado_a_vitest" not in escenario.tags and escenario.name not in enlazados]
    assert sin_enlace == []


def test_la_spec_006_trae_19_escenarios_con_29_casos_y_ninguno_va_a_vitest() -> None:
    # T003 y T011 de specs/006-programacion-docente/tasks.md. Cada escenario lleva @spec006, y ninguno lleva
    # @delegado_a_vitest, porque la spec no cambia ninguna pantalla.
    escenarios = casos = 0
    for ruta in (PROGRAMACION, SIN_DOCENTE):
        for escenario in _feature(ruta).scenarios.values():
            escenarios += 1
            casos += sum(len(t.examples) for t in escenario.examples) if escenario.templated else 1
            assert {"spec006", "corte1"} <= set(escenario.tags), f"{escenario.name}: {sorted(escenario.tags)}"
            assert "delegado_a_vitest" not in escenario.tags, escenario.name
    assert (escenarios, casos) == (19, 29)


_PANTALLA = re.compile(r"\bP[1-7]\b")
_ETAPAS = ("etapa_a", "etapa_b")


def _casos_por_etapa(escenario: Any) -> list[tuple[str, list[str]]]:
    """Etapa y pasos de cada caso del escenario, con los Antecedentes, y cada fila de Ejemplos ya escrita en ellos."""
    propias = [t for t in escenario.tags if t in _ETAPAS]
    if not escenario.templated:
        [etapa] = propias
        return [(etapa, [paso.name for paso in escenario.steps])]
    casos = []
    for tabla in escenario.examples:
        [etapa] = propias or [t for t in tabla.tags if t in _ETAPAS]
        casos += [(etapa, [paso.name for paso in escenario.render(fila).steps]) for fila in tabla.as_contexts()]
    return casos


def test_la_spec_007_trae_35_escenarios_con_70_casos_y_29_van_a_vitest() -> None:
    # T003 y T013 de specs/007-experiencia-por-cuenta/tasks.md. Cada escenario lleva @spec007 y @corte1, y una sola
    # etapa, en el escenario o, si no la lleva, en cada bloque de Ejemplos, como el esquema del menú de US-63, cuya
    # fila de P7 es de la etapa B. Un escenario que nombra una pantalla, de P1 a P7, lleva @delegado_a_vitest y
    # ninguno más, y en la etapa A el Back prueba solo el esquema del lector de US-60 (FR-001).
    escenarios, casos, delegados = 0, {"etapa_a": 0, "etapa_b": 0}, 0
    del_back_en_la_etapa_a = []
    for ruta in SPEC_007:
        for escenario in _feature(ruta).scenarios.values():
            escenarios += 1
            assert {"spec007", "corte1"} <= set(escenario.tags), f"{escenario.name}: {sorted(escenario.tags)}"
            assert len([t for t in escenario.tags if t in _ETAPAS]) <= 1, f"{escenario.name}: {sorted(escenario.tags)}"
            de_cada_caso = _casos_por_etapa(escenario)
            for etapa, _ in de_cada_caso:
                casos[etapa] += 1
            pantalla = any(_PANTALLA.search(paso) for _, pasos in de_cada_caso for paso in pasos)
            assert pantalla == ("delegado_a_vitest" in escenario.tags), f"{escenario.name}: {sorted(escenario.tags)}"
            delegados += pantalla
            if not pantalla and any(etapa == "etapa_a" for etapa, _ in de_cada_caso):
                del_back_en_la_etapa_a.append((ruta, escenario.name))
    assert (escenarios, sum(casos.values())) == (35, 70)
    assert casos == {"etapa_a": 50, "etapa_b": 20}
    assert delegados == 29
    assert del_back_en_la_etapa_a == [
        (ANTES_DE_SUBIR, "El lector de exports reconoce el nombre que propone P3 y no el que lleva guiones")]


def test_la_spec_008_trae_202_escenarios_con_258_casos_41_van_a_vitest_y_14_a_playwright() -> None:
    # T003 y T013 de specs/008-ciclo-quimica-industrial/tasks.md. Cada escenario lleva @spec008, @corte1 y una sola
    # historia de las que spec.md asigna a su archivo, y ninguno va a la vez a Vitest y a Playwright. Las 24 historias,
    # de US-67 a US-90, tienen al menos un escenario.
    escenarios, casos, delegados, del_navegador, historias = 0, 0, 0, 0, set()
    for nombre, ruta in zip(HISTORIAS_DE_LA_SPEC_008, SPEC_008, strict=True):
        propias = {f"US-{n}" for n in HISTORIAS_DE_LA_SPEC_008[nombre]}
        for escenario in _feature(ruta).scenarios.values():
            escenarios += 1
            casos += sum(len(t.examples) for t in escenario.examples) if escenario.templated else 1
            assert {"spec008", "corte1"} <= set(escenario.tags), f"{escenario.name}: {sorted(escenario.tags)}"
            [historia] = [t for t in escenario.tags if re.fullmatch(r"US-\d{2}", t)]
            assert historia in propias, f"{nombre}: «{escenario.name}» lleva {historia}"
            historias.add(historia)
            a_vitest, a_playwright = "delegado_a_vitest" in escenario.tags, "playwright" in escenario.tags
            assert not (a_vitest and a_playwright), f"{escenario.name}: {sorted(escenario.tags)}"
            delegados += a_vitest
            del_navegador += a_playwright
    # 258 casos desde el cambio del 2026-11-23 del cierre, que suma al esquema de US-83 la fila 43 del R-17 cambiada.
    assert (escenarios, casos) == (202, 258)
    assert (delegados, del_navegador) == (41, 14)
    assert historias == {f"US-{n}" for n in range(67, 91)}
