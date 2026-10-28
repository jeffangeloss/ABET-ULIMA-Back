"""Esqueleto de Python del Back (T030). Versión, capas, dependencias fijadas y requirements.txt."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tomllib
from importlib.metadata import version
from pathlib import Path

import openpyxl.xml
import pytest

import abet_carga

RAIZ = Path(__file__).resolve().parent.parent
PYPROJECT = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
LOCK = tomllib.loads((RAIZ / "uv.lock").read_text(encoding="utf-8"))
REQUISITOS = (RAIZ / "requirements.txt").read_text(encoding="utf-8")
EXPORTAR = ["export", "--frozen", "--offline", "--no-dev", "--no-emit-project", "--format", "requirements-txt"]


def _nombre(requisito: str) -> str:
    return re.split(r"[\[<>=~!; ]", requisito, maxsplit=1)[0].lower()


def test_la_version_sigue_a_version() -> None:
    esperada = (RAIZ / "VERSION").read_text(encoding="utf-8").strip()
    assert PYPROJECT["project"]["version"] == esperada
    assert abet_carga.__version__ == esperada
    assert version("abet-ulima-back") == esperada


def test_abet_carga_no_importa_fastapi(tmp_path: Path) -> None:
    # Constitución, principio VI. La biblioteca no importa FastAPI ni Starlette, y app/ sí puede.
    codigo = "import sys, abet_carga; print(sorted(m for m in ('fastapi', 'starlette') if m in sys.modules))"
    salida = subprocess.run(
        [sys.executable, "-I", "-c", codigo], cwd=tmp_path, capture_output=True, text=True, check=True
    )
    assert salida.stdout.strip() == "[]"


def test_las_versiones_del_plan_van_exactas_y_las_demas_con_rango() -> None:
    dependencias = PYPROJECT["project"]["dependencies"] + PYPROJECT["dependency-groups"]["dev"]
    exactas = {d for d in dependencias if "==" in d}
    assert exactas == {"openpyxl==3.1.5", "defusedxml==0.7.1"}
    for requisito in set(dependencias) - exactas:
        # Rango compatible, con límite superior, nunca abierto.
        assert "~=" in requisito or re.search(r">=[^,]+,<", requisito), requisito
    assert version("openpyxl") == "3.1.5"
    assert version("defusedxml") == "0.7.1"
    assert version("pytest-bdd").startswith("9.")


def test_openpyxl_lee_el_xml_con_defusedxml() -> None:
    # openpyxl usa defusedxml solo si está instalado. Sin él leería el XML del export sin protección.
    assert openpyxl.xml.DEFUSEDXML is True


def test_requirements_txt_trae_solo_las_dependencias_de_la_aplicacion_con_hash() -> None:
    lineas = REQUISITOS.splitlines()
    fijadas = {}
    for numero, linea in enumerate(lineas):
        coincidencia = re.match(r"([a-z0-9][a-z0-9._-]*)==([^\s;\\]+)", linea)
        if coincidencia:
            fijadas[coincidencia[1]] = coincidencia[2]
            assert "--hash=sha256:" in lineas[numero + 1], linea
    del_lock = {p["name"]: p.get("version") for p in LOCK["package"]}
    assert fijadas
    assert {n: del_lock.get(n) for n in fijadas} == fijadas
    assert {_nombre(d) for d in PYPROJECT["project"]["dependencies"]} <= set(fijadas)
    assert not {_nombre(d) for d in PYPROJECT["dependency-groups"]["dev"]} & set(fijadas)
    assert PYPROJECT["project"]["name"] not in fijadas
    assert not any(linea.startswith("-e ") for linea in lineas)


@pytest.mark.skipif(not (os.environ.get("UV") or shutil.which("uv")), reason="uv no está disponible")
def test_uv_lock_y_requirements_txt_estan_al_dia() -> None:
    uv = os.environ.get("UV") or shutil.which("uv")
    assert uv is not None
    revision = subprocess.run(
        [uv, "lock", "--check", "--offline"], cwd=RAIZ, capture_output=True, text=True, check=False
    )
    assert revision.returncode == 0, revision.stderr
    exportado = subprocess.run([uv, *EXPORTAR], cwd=RAIZ, capture_output=True, text=True, check=True).stdout
    # Las dos primeras líneas son la cabecera con el comando, que en el archivo lleva -o requirements.txt.
    assert exportado.splitlines()[2:] == REQUISITOS.splitlines()[2:]
    assert "uv export --frozen --no-dev --no-emit-project --format requirements-txt -o requirements.txt" in REQUISITOS
