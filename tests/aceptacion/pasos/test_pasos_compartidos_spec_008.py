"""Pasos compartidos de conftest.py que la spec 008 amplía (T013 de specs/008-ciclo-quimica-industrial/tasks.md).

FR-004 y FR-027 de la spec 008 piden que conftest.py admita las migraciones V1_12 a V1_15, el rol en mayúsculas con
guion bajo, las tablas del esquema acceso en las listas de «no ganan ninguna fila», los rangos de consultas de control
como «Q01 a Q14 y Q18 a Q21», la base desechable de la spec 008 y el registro de la prueba de e2e/ de cada escenario
@playwright. Estas pruebas leen las expresiones de los pasos que pytest-bdd registra y llaman a las ayudas del arnés
sin base ni API, con lo que debe pasar y lo que no debe pasar. Los escenarios de la spec 008 que usan esos pasos
corren con sus propias tareas, de T020 en adelante.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from pytest_bdd.feature import get_features
from pytest_bdd.steps import StepFunctionContext, step_function_context_registry

RAIZ = Path(__file__).resolve().parents[3]
SPEC_008 = RAIZ / "specs" / "008-ciclo-quimica-industrial" / "aceptacion"


@pytest.fixture
def arnes(request: pytest.FixtureRequest) -> ModuleType:
    """Módulo conftest.py de esta carpeta, que pytest registra como plugin."""
    for plugin in request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            return plugin
    raise AssertionError("no se encontró el conftest.py del arnés de aceptación")


def _paso(nombre: str) -> StepFunctionContext:
    """Paso de pytest-bdd de conftest.py con ese nombre de función."""
    contextos = [c for c in list(step_function_context_registry.values())
                 if c.step_func.__name__ == nombre and c.step_func.__code__.co_filename.endswith("pasos/conftest.py")]
    assert len(contextos) == 1, f"conftest.py define {len(contextos)} pasos {nombre}"
    return contextos[0]


def _argumentos(nombre: str, texto: str) -> dict[str, Any] | None:
    parser = _paso(nombre).parser
    return parser.parse_arguments(texto) if parser.is_matching(texto) else None


# Migraciones de V1_09 a V1_15 (FR-004 de la spec 008)

ANTECEDENTE = "una base PostgreSQL 18 desechable con las migraciones V1_01 a V1_{} y los datos de prueba"


@pytest.mark.parametrize("ultima", ["09", "10", "11", "12", "13", "14", "15"])
def test_la_expresion_de_migraciones_admite_de_v1_09_a_v1_15(ultima: str) -> None:
    assert _argumentos("_base_desechable", ANTECEDENTE.format(ultima))["ultima"] == ultima


@pytest.mark.parametrize("ultima", ["08", "16", "1", "120"])
def test_la_expresion_de_migraciones_no_admite_otra_version(ultima: str) -> None:
    assert _argumentos("_base_desechable", ANTECEDENTE.format(ultima)) is None


def test_una_migracion_de_v1_12_a_v1_15_que_no_existe_se_nombra_con_su_tarea(arnes: ModuleType, tmp_path: Path) -> None:
    for version in ("01", "11", "12", "13"):
        (tmp_path / f"V1_{version}__inventada.sql").write_text("SELECT 1;\n", encoding="utf-8")
    assert arnes.migraciones_que_faltan("11", tmp_path) == []
    assert arnes.migraciones_que_faltan("13", tmp_path) == []
    assert arnes.migraciones_que_faltan("15", tmp_path) == [
        "falta la migración V1_14 (T023 de la spec 008)", "falta la migración V1_15 (T021 de la spec 005)"]


# Rol en mayúsculas con guion bajo

def test_el_rol_de_la_sesion_admite_el_guion_bajo() -> None:
    texto = '"coordinador.quimica@example.invalid" tiene la sesión iniciada con rol "COORDINADOR_CURSO"'
    assert _argumentos("_sesion_iniciada", texto)["rol"] == "COORDINADOR_CURSO"
    assert _argumentos("_sesion_iniciada", texto.replace("_CURSO", ""))["rol"] == "COORDINADOR"


@pytest.mark.parametrize("rol", ["coordinador", "Coordinador", "COORDINADOR-CURSO", "COORDINADOR CURSO", ""])
def test_el_rol_de_la_sesion_no_admite_minusculas_guiones_ni_espacios(rol: str) -> None:
    assert _argumentos("_sesion_iniciada", f'"docente701@example.invalid" tiene la sesión iniciada con rol "{rol}"') is None


# Tablas de acceso en las listas de «no ganan ninguna fila»

@pytest.mark.parametrize(("texto", "paso", "tablas"), [
    ("acceso.usuario_autorizado y acceso.coordinacion_alcance no ganan ninguna fila", "_no_ganan",
     [("acceso", "usuario_autorizado"), ("acceso", "coordinacion_alcance")]),
    ("abet.carga, abet.medicion y acceso.sesion no ganan ninguna fila", "_no_ganan",
     [("abet", "carga"), ("abet", "medicion"), ("acceso", "sesion")]),
    ("acceso.credencial no gana ninguna fila", "_no_gana", [("acceso", "credencial")]),
    ("abet.archivo_origen, abet.carga y abet.estudiante no ganan ninguna fila", "_no_ganan",
     [("abet", "archivo_origen"), ("abet", "carga"), ("abet", "estudiante")]),
])
def test_la_lista_admite_tablas_de_abet_y_de_acceso(arnes: ModuleType, texto: str, paso: str,
                                                    tablas: list[tuple[str, str]]) -> None:
    assert arnes.tablas_de(_argumentos(paso, texto)["lista"]) == tablas


@pytest.mark.parametrize("texto", ["public.carga no gana ninguna fila", "acceso no gana ninguna fila",
                                   "pg_catalog.pg_class no gana ninguna fila"])
def test_la_lista_no_admite_otro_esquema(texto: str) -> None:
    assert _argumentos("_no_gana", texto) is None


class _Conteos:
    """Lo que _no_ganan usa del escenario, con conteos fijos en lugar de la base."""

    def __init__(self, antes: dict[str, int], ahora: dict[str, int]) -> None:
        self.antes, self._ahora = antes, ahora

    def conteos(self) -> dict[str, int]:
        return self._ahora


def test_una_tabla_de_acceso_que_no_cambia_pasa_y_una_que_gana_filas_falla(arnes: ModuleType) -> None:
    antes = {"carga": 3, "acceso.sesion": 2, "acceso.coordinacion_alcance": 1}
    arnes._no_ganan(_Conteos(antes, dict(antes)), "abet.carga y acceso.sesion")
    with pytest.raises(AssertionError, match=r"acceso\.coordinacion_alcance cambió de 1 a 2 filas"):
        arnes._no_ganan(_Conteos(antes, {**antes, "acceso.coordinacion_alcance": 2}), "acceso.coordinacion_alcance")


def test_una_tabla_de_acceso_sin_conteo_previo_no_pasa_en_silencio(arnes: ModuleType) -> None:
    with pytest.raises(AssertionError, match=r"no tomó el conteo previo de acceso\.credencial"):
        arnes._no_ganan(_Conteos({"carga": 3}, {"carga": 3, "acceso.credencial": 0}), "acceso.credencial")


# Rangos de consultas de control

@pytest.mark.parametrize(("lista", "nombres"), [
    ("Q01 a Q14 y Q18 a Q21", [f"Q{n:02d}" for n in (*range(1, 15), *range(18, 22))]),
    ("Q21", ["Q21"]),
    ("Q05 y Q18", ["Q05", "Q18"]),
    ("Q01, Q02, Q03, Q04, Q06, Q07, Q08, Q10, Q12, Q13, Q14, Q18, Q19, Q20 y Q21",
     ["Q01", "Q02", "Q03", "Q04", "Q06", "Q07", "Q08", "Q10", "Q12", "Q13", "Q14", "Q18", "Q19", "Q20", "Q21"]),
    ("Q06 a Q07", ["Q06", "Q07"]),
])
def test_la_lista_de_controles_admite_rangos(arnes: ModuleType, lista: str, nombres: list[str]) -> None:
    texto = f"las consultas de control {lista} devuelven 0 filas" if " " in lista else f"la consulta de control {lista} devuelve 0 filas"
    assert arnes.controles_de(_argumentos("_controles_en_cero", texto)["lista"]) == nombres


@pytest.mark.parametrize("lista", ["Q14 a Q01", "Q03 a Q03"])
def test_un_rango_al_reves_o_de_una_sola_consulta_no_se_admite(arnes: ModuleType, lista: str) -> None:
    with pytest.raises(AssertionError, match="rango"):
        arnes.controles_de(lista)


def test_las_consultas_nuevas_se_exigen_solo_cuando_un_escenario_las_pide(arnes: ModuleType) -> None:
    de_hoy = {f"Q{n:02d}": "SELECT 1" for n in range(1, 15)}
    arnes.exigir_controles(de_hoy, ["Q01", "Q14"])
    arnes.exigir_controles({**de_hoy, "Q18": "SELECT 1", "Q21": "SELECT 1"}, ["Q18", "Q21"])
    with pytest.raises(AssertionError, match=r"Q19 no está en controles_neon\.sql"):
        arnes.exigir_controles(de_hoy, ["Q01", "Q19"])
    with pytest.raises(AssertionError, match=r"faltan Q13 y Q14"):
        arnes.exigir_controles({f"Q{n:02d}": "SELECT 1" for n in range(1, 13)}, ["Q01"])
    with pytest.raises(AssertionError, match=r"Q15 no es una consulta de controles_neon\.sql"):
        arnes.exigir_controles({**de_hoy, "Q15": "SELECT 1"}, ["Q01"])


def test_controles_neon_sql_de_hoy_cumple_la_regla(arnes: ModuleType) -> None:
    arnes.exigir_controles(arnes.consultas_de_control(), [f"Q{n:02d}" for n in range(1, 15)])


# Base desechable de la spec 008

def _antecedentes_de_la_spec_008() -> list[str]:
    pasos = []
    for feature in get_features([str(ruta) for ruta in sorted(SPEC_008.glob("*.feature"))]):
        if feature.background is not None:
            pasos += [paso.name for paso in feature.background.steps]
    return pasos


def test_cada_cuenta_con_alcance_de_los_antecedentes_tiene_su_paso() -> None:
    lineas = [paso for paso in _antecedentes_de_la_spec_008() if "activo y con alcance de" in paso]
    assert len(lineas) == 3
    argumentos = [_argumentos("_con_alcance", linea) for linea in lineas]
    assert {(a["correo"], a["rol"], a["carrera"], a["asignatura"], a["periodo"]) for a in argumentos} == {
        ("coordinacion@example.invalid", "COORDINADOR", "AMB", None, None),
        ("coordinador.quimica@example.invalid", "COORDINADOR", None, "5643", "2026-1")}
    assert _argumentos("_con_alcance", '"x@example.invalid" con rol "COORDINADOR", activo y con alcance de la asignatura'
                       ' "5643"') is None


def test_cada_forma_de_la_base_de_la_spec_008_tiene_su_variante(arnes: ModuleType) -> None:
    formas = [paso for paso in _antecedentes_de_la_spec_008() if paso.startswith("una base desechable de la spec 008")]
    assert len(formas) == 7
    variantes = {arnes.forma_de_la_base_008(_argumentos("_base_de_la_spec_008", paso)["resto"])[0] for paso in formas}
    assert variantes == {"quimica", "quimica_plan", "catalogo_industrial"}


@pytest.mark.parametrize("resto", [
    "con los datos de periodo_2026_2_inventado.sql",
    "con el plan de 5643 en 2026-2 y los datos de quimica_2026_1_inventado.sql",
    "con las migraciones V1_01 a V1_11 y la referencia db/referencia/industrial_2026.json de 7 SO, 21 PI y 53 "
    "asignaturas, 10 de ellas también en AMB-2026",
    'con el plan de 5643 en 2026-1 para "IND" con el PI 6.1, el instrumento «Portafolio 3» y la descripción "Otro texto"',
])
def test_una_forma_que_no_es_de_la_spec_008_no_adivina_su_base(arnes: ModuleType, resto: str) -> None:
    with pytest.raises(AssertionError, match="no tiene variante"):
        arnes.forma_de_la_base_008(resto)


def test_la_base_de_la_spec_008_nombra_cada_pieza_que_falta_con_su_tarea(arnes: ModuleType, tmp_path: Path) -> None:
    resto = "con los datos de periodo_2026_2_inventado.sql y quimica_2026_1_inventado.sql"
    _, piezas = arnes.forma_de_la_base_008(resto)
    assert arnes.piezas_que_faltan(piezas, tmp_path) == [
        "db/migration/V1_12__*.sql (T020)", "db/migration/V1_13__*.sql (T021)", "db/migration/V1_14__*.sql (T023)",
        "db/datos/alcance_coordinacion_ambiental.sql (T023)", "db/datos/quimica_2026_1_inventado.sql (T024)"]
    for patron in ("db/migration/V1_12__x.sql", "db/migration/V1_13__x.sql", "db/migration/V1_14__x.sql",
                   "db/datos/alcance_coordinacion_ambiental.sql", "db/datos/quimica_2026_1_inventado.sql"):
        (tmp_path / patron).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / patron).write_text("SELECT 1;\n", encoding="utf-8")
    assert arnes.piezas_que_faltan(piezas, tmp_path) == []


def test_la_forma_del_catalogo_pide_la_referencia_y_su_generador(arnes: ModuleType) -> None:
    resto = ("con las migraciones V1_01 a V1_11 y la referencia db/referencia/industrial_2026.json de 7 SO, 21 PI y 53 "
             "asignaturas, 15 de ellas también en AMB-2026")
    variante, piezas = arnes.forma_de_la_base_008(resto)
    assert variante == "catalogo_industrial"
    # La referencia ya está en el repositorio (T026), y el generador llega con T020.
    assert arnes.piezas_que_faltan(piezas) == ["db/herramientas/generar_v1_12.py (T020)"]


def test_la_variante_del_catalogo_aplica_solo_hasta_v1_11(modulo_base_desechable: ModuleType, arnes: ModuleType) -> None:
    hasta_11 = modulo_base_desechable.migraciones(hasta=(1, 11))
    assert [ruta.name.split("__")[0] for ruta in hasta_11 if ruta.name.startswith("V")][-1] == "V1_11"
    assert all(not ruta.name.startswith("V") or modulo_base_desechable._version(ruta) <= (1, 11) for ruta in hasta_11)
    # Las vistas repetibles van igual al final, y sin límite la lista es la de siempre.
    assert [ruta.name for ruta in hasta_11 if ruta.name.startswith("R__")] == [
        "R__vista_r17_por_pi.sql", "R__vista_tabla_maestra_pi.sql"]
    assert modulo_base_desechable.migraciones() == modulo_base_desechable.migraciones(hasta=None)
    assert arnes.VARIANTES["catalogo_industrial"] == {"hasta": (1, 11)}


# Escenarios @playwright

def _nodo(etiquetas: set[str]) -> SimpleNamespace:
    return SimpleNamespace(user_properties=[], etiquetas=etiquetas)


def test_un_paso_playwright_registra_su_prueba_de_e2e(arnes: ModuleType) -> None:
    nodo = _nodo({"spec008", "playwright"})
    cubiertos = {"El profesor sube su export": ["e2e/humo_quimica.spec.ts › el profesor sube su export"]}
    arnes.registrar_playwright(nodo, "El profesor sube su export", nodo.etiquetas, cubiertos, "la vista previa")
    assert nodo.user_properties == [
        ("delegado_a_playwright", "la vista previa → e2e/humo_quimica.spec.ts › el profesor sube su export")]
    assert "delegado_a_playwright" in arnes.PROPIEDADES_A_LA_VISTA


@pytest.mark.parametrize(("etiquetas", "cubiertos", "error"), [
    ({"spec008"}, {"E": ["e2e/a.spec.ts › e"]}, "no lleva @playwright"),
    ({"spec008", "playwright"}, {}, "no tiene pruebas de e2e/ anotadas"),
    ({"spec008", "playwright"}, {"E": ["src/App.test.tsx › e"]}, "fuera de e2e/"),
])
def test_un_paso_playwright_sin_su_prueba_no_pasa(arnes: ModuleType, etiquetas: set[str],
                                                 cubiertos: dict[str, list[str]], error: str) -> None:
    nodo = _nodo(etiquetas)
    with pytest.raises(AssertionError, match=error):
        arnes.registrar_playwright(nodo, "E", etiquetas, cubiertos, "texto")
    assert nodo.user_properties == []
