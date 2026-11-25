"""Pasos compartidos de conftest.py que la spec 010 agrega (T014 de specs/010-nombre-del-profesor/tasks.md).

Los Antecedentes de los cuatro .feature de la spec 010 piden una base con V1_16, los nombres inventados de las semillas
y el archivo base de la programación con la columna nombre. Estas pruebas leen las expresiones de los pasos que
pytest-bdd registra y llaman a las ayudas del arnés sin base ni API, con lo que debe pasar y lo que no debe pasar. Los
escenarios de la spec 010 que usan esos pasos corren con sus propias tareas, de T020 en adelante.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from pytest_bdd.feature import get_features
from pytest_bdd.steps import StepFunctionContext, step_function_context_registry

RAIZ = Path(__file__).resolve().parents[3]
SPEC_010 = RAIZ / "specs" / "010-nombre-del-profesor" / "aceptacion"


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


def _coincide(nombre: str, texto: str) -> bool:
    return _paso(nombre).parser.is_matching(texto)


def _antecedentes() -> list[str]:
    pasos = []
    for feature in get_features([str(ruta) for ruta in sorted(SPEC_010.glob("*.feature"))]):
        assert feature.background is not None, feature.filename
        pasos += [paso.name for paso in feature.background.steps]
    return pasos


# Cada Antecedente de los cuatro archivos tiene su paso y solo uno

PASOS_DE_LOS_ANTECEDENTES = ("_base_migrada_hasta_v1_16", "_base_de_la_spec_010", "_base_de_partida_006_con_nombre",
                             "_archivo_base_con_nombres")


def test_cada_antecedente_de_la_spec_010_lo_reconoce_un_solo_paso() -> None:
    antecedentes = _antecedentes()
    assert len(antecedentes) == 5
    for texto in antecedentes:
        reconocidos = [nombre for nombre in PASOS_DE_LOS_ANTECEDENTES if _coincide(nombre, texto)]
        assert len(reconocidos) == 1, f"{texto!r} lo reconocen {reconocidos}"


def test_el_antecedente_de_la_spec_006_con_v1_11_sigue_con_su_paso_y_no_se_confunde_con_el_de_v1_16() -> None:
    v1_11 = ("una base desechable de partida de la spec 006, en PostgreSQL 18 con las migraciones V1_01 a V1_11, la "
             "vigencia de AMB-2026 en 2026-2 y el plan de medición de 450002 y 450010, sin secciones ni profesores")
    v1_16 = v1_11.replace("V1_11", "V1_16")
    assert _coincide("_base_de_partida_006", v1_11) and not _coincide("_base_de_partida_006_con_nombre", v1_11)
    assert _coincide("_base_de_partida_006_con_nombre", v1_16) and not _coincide("_base_de_partida_006", v1_16)


@pytest.mark.parametrize("texto", [
    "una base desechable migrada hasta V1_15", "una base desechable migrada hasta V1_17",
    "una base desechable migrada hasta V1_160", "una base migrada hasta V1_16",
])
def test_la_base_migrada_hasta_v1_16_no_admite_otra_forma(texto: str) -> None:
    assert not _coincide("_base_migrada_hasta_v1_16", texto)


@pytest.mark.parametrize("texto", [
    "una base desechable de la spec 010 con los datos inventados de Ambiental en 2026-2",
    "una base desechable de la spec 010 con los datos inventados de Ambiental en 2026-2 y de Química en 2026-1",
    "una base desechable de la spec 009 con los datos inventados de Ambiental en 2026-2 y de Química en 2026-1 y sus "
    "nombres inventados",
])
def test_la_base_de_la_spec_010_pide_las_dos_carreras_y_los_nombres(texto: str) -> None:
    assert not _coincide("_base_de_la_spec_010", texto)


# Piezas que faltan, con su tarea

def test_la_base_de_la_spec_010_nombra_la_migracion_que_falta_con_su_tarea(arnes: ModuleType, tmp_path: Path) -> None:
    assert arnes.piezas_de_la_spec_010_que_faltan(tmp_path) == ["db/migration/V1_16__*.sql (T020)"]
    (tmp_path / "db" / "migration").mkdir(parents=True)
    (tmp_path / "db" / "migration" / "V1_15__otra.sql").write_text("SELECT 1;\n", encoding="utf-8")
    assert arnes.piezas_de_la_spec_010_que_faltan(tmp_path) == ["db/migration/V1_16__*.sql (T020)"]
    (tmp_path / "db" / "migration" / "V1_16__nombre_del_usuario.sql").write_text("SELECT 1;\n", encoding="utf-8")
    assert arnes.piezas_de_la_spec_010_que_faltan(tmp_path) == []


# Nombres inventados de las semillas

class _Filas:
    """Lo que nombres_que_faltan_010 usa del escenario, con filas fijas en lugar de la base."""

    def __init__(self, filas: list[tuple[str, str | None]]) -> None:
        self._filas = filas

    def filas(self, consulta: str, *parametros: object) -> list[tuple[str, str | None]]:
        assert "nombre FROM acceso.usuario_autorizado" in consulta
        return self._filas


def test_los_nombres_inventados_de_las_convenciones_son_los_de_la_spec(arnes: ModuleType) -> None:
    assert arnes.NOMBRES_INVENTADOS_010 == {
        "docente410@example.invalid": "Profesor Inventado Cuatrocientos Diez",
        "docente411@example.invalid": "Profesor Inventado Cuatrocientos Once",
        "docente701@example.invalid": "Profesor Inventado Setecientos Uno",
        "docente702@example.invalid": "Profesor Inventado Setecientos Dos",
        "docente703@example.invalid": "Profesor Inventado Setecientos Tres",
    }
    for correo, nombre in arnes.NOMBRES_INVENTADOS_010.items():
        assert correo.endswith("@example.invalid") and nombre.startswith("Profesor Inventado ")
        assert not any(caracter.isdigit() for caracter in nombre)


def test_con_los_cinco_nombres_de_las_semillas_no_falta_ninguno(arnes: ModuleType) -> None:
    filas = list(arnes.NOMBRES_INVENTADOS_010.items())
    assert arnes.nombres_que_faltan_010(_Filas(filas)) == []


def test_un_nombre_ausente_o_distinto_se_nombra_por_su_correo_y_no_por_su_valor(arnes: ModuleType) -> None:
    filas: list[tuple[str, str | None]] = list(arnes.NOMBRES_INVENTADOS_010.items())
    filas[0] = ("docente410@example.invalid", None)
    filas[1] = ("docente411@example.invalid", "Profesor Inventado Otro")
    assert arnes.nombres_que_faltan_010(_Filas(filas)) == ["docente410@example.invalid", "docente411@example.invalid"]
    assert arnes.nombres_que_faltan_010(_Filas([])) == list(arnes.NOMBRES_INVENTADOS_010)


# Archivo base con nombres

def _ctx() -> SimpleNamespace:
    return SimpleNamespace(extras={})


def test_el_archivo_base_con_nombres_suma_la_columna_nombre_a_las_dos_filas(arnes: ModuleType) -> None:
    ctx: Any = _ctx()
    archivo = arnes.archivo_con_nombres_006(ctx)
    assert archivo.encabezados == [*arnes.ENCABEZADOS_006, "nombre"]
    assert [(fila[3], fila[5]) for fila in archivo.filas] == [
        ("docente410@example.invalid", "Profesor Inventado Cuatrocientos Diez"),
        ("docente411@example.invalid", "Profesor Inventado Cuatrocientos Once")]
    assert archivo is arnes.archivo_006(ctx)
    texto = archivo.a_bytes().decode("utf-8").splitlines()
    assert texto[0] == "periodo,asignatura,seccion,correo,curso_blackboard,nombre"
    assert texto[1].endswith(",Profesor Inventado Cuatrocientos Diez")


def test_el_archivo_base_sin_nombres_no_trae_la_columna_y_no_se_le_suma_dos_veces(arnes: ModuleType) -> None:
    ctx: Any = _ctx()
    assert "nombre" not in arnes.archivo_006(ctx).encabezados
    arnes.archivo_con_nombres_006(ctx)
    with pytest.raises(AssertionError, match="ya trae la columna nombre"):
        arnes.archivo_con_nombres_006(ctx)
