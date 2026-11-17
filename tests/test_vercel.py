"""Configuración de Vercel del Back (T071, con la región de J-17).

Lo que debe pasar: vercel.json fija la región iad1, junto a Neon en us-east-1, y la función de FastAPI
(app.main:app) deja fuera del paquete las pruebas, las specs, la documentación, la base y los guiones.
Lo que no debe pasar: que el paquete pierda la API, la biblioteca o las plantillas que el R-17 necesita, ni que
Vercel construya una vista previa de una rama que no es develop, porque el Back no tiene la protección de Vercel.
"""

from __future__ import annotations

import json
import os
import subprocess
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


def _construye(entorno: str, rama: str) -> bool:
    """Corre ignoreCommand como lo corre Vercel, donde 1 sigue con el build y 0 lo omite."""
    entorno_del_build = {"PATH": os.environ["PATH"], "VERCEL_ENV": entorno, "VERCEL_GIT_COMMIT_REF": rama}
    resultado = subprocess.run(["sh", "-c", _vercel()["ignoreCommand"]], env=entorno_del_build, check=False)
    assert resultado.returncode in (0, 1)
    return resultado.returncode == 1


def test_t071_vercel_solo_construye_production_y_la_rama_develop() -> None:
    # Vercel Authentication está apagada en el Back (sección 2.4 de entornos-y-despliegue.md del Front), así
    # que la vista previa de otra rama quedaría pública con la base de develop.
    assert _construye("production", "main")
    assert _construye("preview", "develop")
    for rama in ("feat/001-despliegue-vercel", "dependabot/pip/fastapi-1.0", "develop-copia", ""):
        assert not _construye("preview", rama)
