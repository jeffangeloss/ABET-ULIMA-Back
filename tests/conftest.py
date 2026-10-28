"""Configuración común de las pruebas del Back."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

RAIZ = Path(__file__).resolve().parent.parent
GENERADOR = RAIZ / "scripts" / "generar_exports_inventados.py"


def etiquetas_de_gherkin() -> set[str]:
    """Etiquetas de los .feature de specs/, que pytest-bdd convierte en marcas de pytest."""
    etiquetas: set[str] = set()
    for feature in sorted(RAIZ.glob("specs/*/aceptacion/*.feature")):
        for linea in feature.read_text(encoding="utf-8").splitlines():
            limpia = linea.split("#", 1)[0].strip()
            if limpia.startswith("@"):
                etiquetas.update(palabra[1:] for palabra in limpia.split() if palabra.startswith("@"))
    return etiquetas


def pytest_configure(config: pytest.Config) -> None:
    # Cada etiqueta de Gherkin (@US-07, @corte1...) queda registrada como marca, así que pytest-bdd
    # no avisa de marcas desconocidas al aplicar las etiquetas de cada escenario.
    for etiqueta in sorted(etiquetas_de_gherkin()):
        config.addinivalue_line("markers", f"{etiqueta}: etiqueta de Gherkin de specs/")


def cargar_generador() -> ModuleType:
    """Carga scripts/generar_exports_inventados.py por su ruta, porque scripts/ no es un paquete."""
    especificacion = importlib.util.spec_from_file_location("generar_exports_inventados", GENERADOR)
    assert especificacion is not None and especificacion.loader is not None
    modulo = importlib.util.module_from_spec(especificacion)
    # dataclasses busca el módulo en sys.modules mientras se define la clase Export.
    sys.modules[especificacion.name] = modulo
    especificacion.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="session")
def generador() -> ModuleType:
    return cargar_generador()
