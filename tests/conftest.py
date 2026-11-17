"""Configuración común de las pruebas del Back."""

from __future__ import annotations

import importlib.util
import os
import sys
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

RAIZ = Path(__file__).resolve().parent.parent
GENERADOR = RAIZ / "scripts" / "generar_exports_inventados.py"
BASE_DESECHABLE = RAIZ / "tests" / "base_desechable.py"
CLUSTER_DESECHABLE = RAIZ / "tests" / "cluster_desechable.py"

# Toda prueba que pide una de estas fixtures usa una base PostgreSQL 18 desechable y lleva el
# marcador base, declarado en pyproject.toml, aunque no lo escriba.
FIXTURES_DE_BASE = frozenset({"cluster_postgres", "base_desechable", "base_demo", "crear_base_demo"})


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


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    # Con el marcador puesto aquí, pytest -m "not base" deja fuera toda prueba que pide una base.
    for item in items:
        if FIXTURES_DE_BASE & set(getattr(item, "fixturenames", ())):
            item.add_marker(pytest.mark.base)


def cargar_modulo(nombre: str, ruta: Path) -> ModuleType:
    """Carga un módulo por su ruta, porque scripts/ y tests/ no son paquetes y pytest usa --import-mode=importlib."""
    especificacion = importlib.util.spec_from_file_location(nombre, ruta)
    assert especificacion is not None and especificacion.loader is not None
    modulo = importlib.util.module_from_spec(especificacion)
    # dataclasses busca el módulo en sys.modules mientras define sus clases.
    sys.modules[especificacion.name] = modulo
    especificacion.loader.exec_module(modulo)
    return modulo


def cargar_generador() -> ModuleType:
    """Carga scripts/generar_exports_inventados.py por su ruta, porque scripts/ no es un paquete."""
    return cargar_modulo("generar_exports_inventados", GENERADOR)


@pytest.fixture(scope="session")
def generador() -> ModuleType:
    return cargar_generador()


@pytest.fixture(scope="session")
def cluster_postgres() -> Iterator[dict[str, str]]:
    """Clúster de PostgreSQL desechable de la sesión de pruebas, con sus variables de libpq en os.environ.

    En la CI no arranca nada, porque el servicio postgres:18 del job ya es desechable. En la Mac, el
    clúster vive solo lo que dura la sesión de pytest, y ninguna prueba alcanza el de localhost:5432.
    """
    cluster_desechable = cargar_modulo("cluster_desechable", CLUSTER_DESECHABLE)
    if cluster_desechable.en_ci():
        yield {}
        return
    cluster = cluster_desechable.iniciar()
    anteriores = {clave: os.environ.get(clave) for clave in cluster.entorno}
    os.environ.update(cluster.entorno)
    try:
        yield cluster.entorno
    finally:
        for clave, valor in anteriores.items():
            if valor is None:
                os.environ.pop(clave, None)
            else:
                os.environ[clave] = valor
        cluster_desechable.detener(cluster)


@pytest.fixture(scope="session")
def modulo_base_desechable() -> ModuleType:
    """Módulo tests/base_desechable.py sin arrancar ningún clúster, para probar sus guardias sin servidor."""
    return cargar_modulo("base_desechable", BASE_DESECHABLE)


@pytest.fixture(scope="session")
def base_desechable(cluster_postgres: dict[str, str], modulo_base_desechable: ModuleType) -> Iterator[ModuleType]:
    """Módulo tests/base_desechable.py con el clúster desechable de la sesión ya arrancado.

    Al cerrar la sesión exige que no quede ninguna base ni rol abet_demo_, y una que quede hace fallar
    la sesión en lugar de borrarse en silencio.
    """
    yield modulo_base_desechable
    modulo_base_desechable.exigir_sin_restos()


@pytest.fixture
def crear_base_demo(base_desechable: ModuleType) -> Iterator[Callable[..., Any]]:
    """Crea bases desechables con las opciones de base_desechable.crear() y las borra al terminar, pase o falle."""
    with ExitStack() as pila:
        yield lambda **opciones: pila.enter_context(base_desechable.abierta(**opciones))


@pytest.fixture
def base_demo(crear_base_demo: Callable[..., Any]) -> Any:
    """Base desechable con las migraciones, el rol de la aplicación y los datos de 2026-2, sin la guardia de Neon."""
    return crear_base_demo()
