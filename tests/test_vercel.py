"""Configuración de Vercel del Back (T071, con la región de J-17).

Lo que debe pasar: vercel.json fija la región iad1, junto a Neon en us-east-1, y la función de FastAPI
(app.main:app) deja fuera del paquete las pruebas, las specs, la documentación, la base y los guiones.
Lo que no debe pasar: que el paquete pierda la API, la biblioteca o las plantillas que el R-17 necesita.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _vercel() -> dict:
    return json.loads((RAIZ / "vercel.json").read_text(encoding="utf-8"))


def test_t071_vercel_fija_la_region_iad1_junto_a_neon() -> None:
    assert _vercel()["regions"] == ["iad1"]


def test_t071_la_funcion_de_vercel_es_la_app_de_fastapi() -> None:
    pyproject = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["tool"]["vercel"]["entrypoint"] == "app.main:app"
    assert "app/main.py" in _vercel()["functions"]


def test_t071_el_paquete_deja_fuera_lo_que_no_corre_en_vercel() -> None:
    patron = _vercel()["functions"]["app/main.py"]["excludeFiles"]
    for carpeta in ("tests/**", "specs/**", "docs/**", "db/**", "scripts/**"):
        assert carpeta in patron
    for necesaria in ("app/", "abet_carga/", "plantillas/"):
        assert necesaria not in patron
