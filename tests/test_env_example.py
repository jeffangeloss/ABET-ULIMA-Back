"""`.env.example` del Back (escenario «Las variables del Back están en Vercel y no en el repositorio» de US-17).

Lo que debe pasar: el archivo nombra DATABASE_URL, SESION_SECRETO, PERIODO_VIGENTE, CONJUNTO_REGLAS y
GUARDIA_DATOS_INVENTADOS, cada una sin valor, porque los valores viven en Vercel y en el `.env` local de cada
persona (constitución y regla 7 de `AGENTS.md`).
Lo que no debe pasar: que una copia tal cual del archivo arranque la API con valores que nadie eligió, ni que deje
apagada la guardia de datos inventados.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from abet_carga.carga import Configuracion
from app.main import Ajustes, ConfiguracionDeLaApi

RAIZ = Path(__file__).resolve().parent.parent
VARIABLES = ("DATABASE_URL", "SESION_SECRETO", "PERIODO_VIGENTE", "CONJUNTO_REGLAS", "GUARDIA_DATOS_INVENTADOS")


def _asignaciones() -> dict[str, str]:
    """Las líneas NOMBRE=valor de `.env.example`, sin los comentarios ni las líneas vacías."""
    asignaciones = {}
    for linea in (RAIZ / ".env.example").read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        nombre, separador, valor = linea.partition("=")
        assert separador, f"Una línea de .env.example no tiene «=» ({nombre})."
        asignaciones[nombre.strip()] = valor.strip()
    return asignaciones


@pytest.mark.parametrize("variable", VARIABLES)
def test_us17_env_example_nombra_la_variable_sin_valor(variable: str) -> None:
    assert _asignaciones()[variable] == ""


def test_us17_una_copia_tal_cual_no_arranca_la_api_aunque_traiga_los_secretos() -> None:
    entorno = _asignaciones() | {"DATABASE_URL": "host=/tmp/abet dbname=abet user=abet_app", "SESION_SECRETO": "s" * 32}
    with pytest.raises(ConfiguracionDeLaApi, match="PERIODO_VIGENTE"):
        Ajustes.desde_entorno(entorno)


def test_us17_una_copia_tal_cual_deja_la_guardia_encendida() -> None:
    entorno = _asignaciones() | {"CONJUNTO_REGLAS": "R-2026-BORRADOR"}
    assert Configuracion.desde_entorno(entorno).guardia_datos_inventados is True
