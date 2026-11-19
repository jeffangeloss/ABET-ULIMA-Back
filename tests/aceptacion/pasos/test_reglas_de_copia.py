"""Regla de copia «con la columna X.Y vacía en sus N filas» de REGLAS_DE_COPIA (T012 de la spec 004).

El escenario «Un PI sin calificaciones no sale como 0 %» de specs/004-reportes-docente/aceptacion/resultados.feature
sube una copia del export correcto de la 410 sin ninguna nota en la columna de un indicador de desempeño
(performance indicator, PI). conftest.py la arma en memoria con el generador de exports inventados, y estas pruebas
la leen con el mismo generador y con abet_carga.lector, sin base ni API, para comprobar lo que debe cambiar y lo que
no debe cambiar.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import pytest

from abet_carga.lector import leer

RAIZ = Path(__file__).resolve().parents[3]
INVENTADOS = RAIZ / "tests" / "datos_inventados"
CORRECTO = "sintetico_20262_450002_410.xlsx"
CSV_410 = "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv"
FILAS = range(2, 13)


@dataclass
class _Escenario:
    """Lo que armar_archivo() de conftest.py usa del escenario, sin base ni API."""

    generador: ModuleType

    def de_inventados(self, nombre: str) -> bytes:
        return (INVENTADOS / nombre).read_bytes()


@pytest.fixture
def arnes(request: pytest.FixtureRequest) -> ModuleType:
    """Módulo conftest.py de esta carpeta, que pytest registra como plugin."""
    for plugin in request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            return plugin
    raise AssertionError("no se encontró el conftest.py del arnés de aceptación")


def _columna(export: object, pi: str) -> list[object]:
    return [export.valor(fila, pi) for fila in FILAS]


def test_la_columna_5_3_queda_vacia_en_las_11_filas_y_las_demas_no_cambian(arnes: ModuleType, generador: ModuleType) -> None:
    escenario = _Escenario(generador)
    contenido, nombre = arnes.armar_archivo(escenario, f'una copia de "{CORRECTO}" con la columna 5.3 vacía en sus 11 filas')

    original = generador.leer_export(escenario.de_inventados(CORRECTO))
    copia = generador.leer_export(contenido)
    assert nombre == CORRECTO
    assert _columna(copia, "5.3") == [None] * 11
    # Los niveles de NIVELES_410 en 5.1 y 5.2, y los once códigos, siguen como en el export correcto.
    assert _columna(copia, "5.1") == [3, 4, 2, 3, 1, 4, 3, 2, 4, 3, 2] == _columna(original, "5.1")
    assert _columna(copia, "5.2") == [4, 3, 3, 2, 2, 3, 4, 1, 3, 4, 2] == _columna(original, "5.2")
    assert _columna(copia, "Username") == list(range(99000001, 99000012))
    assert copia.encabezado == original.encabezado and copia.hoja == original.hoja


def test_el_lector_ve_la_columna_5_3_sin_ningun_nivel(arnes: ModuleType, generador: ModuleType) -> None:
    contenido, nombre = arnes.armar_archivo(_Escenario(generador),
                                            f'una copia de "{CORRECTO}" con la columna 5.3 vacía en sus 11 filas')
    leido = leer(contenido, nombre_archivo=nombre)
    posiciones = {columna.pi_codigo: i for i, columna in enumerate(leido.columnas_pi)}
    assert sorted(posiciones) == ["5.1", "5.2", "5.3"]
    assert [fila.valores_pi[posiciones["5.3"]] for fila in leido.filas] == [None] * 11
    assert all(fila.valores_pi[posiciones["5.1"]] is not None for fila in leido.filas)


def test_en_un_export_de_texto_la_columna_queda_con_celdas_vacias(arnes: ModuleType, generador: ModuleType) -> None:
    escenario = _Escenario(generador)
    contenido, _ = arnes.armar_archivo(escenario, f'una copia de "{CSV_410}" con la columna 5.2 vacía en sus 11 filas')

    copia = generador.leer_export_texto(contenido)
    original = generador.leer_export_texto(escenario.de_inventados(CSV_410))
    assert _columna(copia, "5.2") == [""] * 11
    assert _columna(copia, "5.1") == _columna(original, "5.1") != [""] * 11


def test_un_numero_de_filas_que_no_es_el_del_export_detiene_la_copia(arnes: ModuleType, generador: ModuleType) -> None:
    with pytest.raises(AssertionError, match="trae 11 filas de datos y no 12"):
        arnes.armar_archivo(_Escenario(generador), f'una copia de "{CORRECTO}" con la columna 5.3 vacía en sus 12 filas')
