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


# Regla «con la columna X.Y vacía en las filas N y M» y su forma de tres filas (T012 y FR-017 de la spec 005).
# Las filas son las del export, desde la 2, como en la regla de una sola fila. Los niveles de 5.3 de la 410 son
# 2 = 3, 3 = 4, 4 = 3, 5 = 3, 6 = 2, 7 = 4, 8 = 3, 9 = 1, 10 = 4, 11 = 3 y 12 = 2.
NIVELES_5_3 = [3, 4, 3, 3, 2, 4, 3, 1, 4, 3, 2]


@pytest.mark.parametrize(("filas", "vacias"), [("las filas 2 y 6", (2, 6)), ("las filas 2, 3 y 9", (2, 3, 9))])
def test_la_columna_queda_vacia_solo_en_las_filas_nombradas(arnes: ModuleType, generador: ModuleType, filas: str,
                                                          vacias: tuple[int, ...]) -> None:
    escenario = _Escenario(generador)
    contenido, nombre = arnes.armar_archivo(escenario, f'una copia de "{CORRECTO}" con la columna 5.3 vacía en {filas}')

    copia = generador.leer_export(contenido)
    original = generador.leer_export(escenario.de_inventados(CORRECTO))
    assert nombre == CORRECTO
    assert _columna(original, "5.3") == NIVELES_5_3
    assert _columna(copia, "5.3") == [None if fila in vacias else nivel for fila, nivel in zip(FILAS, NIVELES_5_3)]
    for pi in ("5.1", "5.2", "Username"):
        assert _columna(copia, pi) == _columna(original, pi)


def test_las_filas_2_y_6_dan_7_de_9_y_las_2_3_y_9_dan_6_de_8_en_el_lector(arnes: ModuleType,
                                                                          generador: ModuleType) -> None:
    # Las cifras de la tabla de la spec 005, con nivel esperado 3, antes de que la base cuente nada.
    for cambio, esperado in (("las filas 2 y 6", (7, 9)), ("las filas 2, 3 y 9", (6, 8))):
        contenido, nombre = arnes.armar_archivo(_Escenario(generador),
                                                f'una copia de "{CORRECTO}" con la columna 5.3 vacía en {cambio}')
        leido = leer(contenido, nombre_archivo=nombre)
        posicion = [c.pi_codigo for c in leido.columnas_pi].index("5.3")
        niveles = [fila.valores_pi[posicion] for fila in leido.filas]
        calificados = [n for n in niveles if n is not None]
        assert (sum(1 for n in calificados if n >= 3), len(calificados)) == esperado


@pytest.mark.parametrize("cambio", ["con la columna 5.3 vacía en las filas 2 y 13", "con la columna 5.3 vacía en las filas 6 y 6",
                                    "con la columna 5.3 vacía en las filas 1, 3 y 9"])
def test_una_fila_fuera_del_export_o_repetida_detiene_la_copia(arnes: ModuleType, generador: ModuleType,
                                                               cambio: str) -> None:
    with pytest.raises(AssertionError, match="fuera de las filas de datos|se repite"):
        arnes.armar_archivo(_Escenario(generador), f'una copia de "{CORRECTO}" {cambio}')
