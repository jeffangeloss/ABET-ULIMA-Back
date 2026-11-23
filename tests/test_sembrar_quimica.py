"""Pruebas de la huella de referencia de db/herramientas/sembrar_quimica.py (spec 008, US-86, corrección del 2026-11-23
a T027).

La siembra real corre en dos tramos, porque se detiene en el despliegue del Back y se reanuda con --desde plan_quimica.
El segundo tramo no corre huella_antes, así que recibe la huella de Ambiental de antes con --huella-antes, y sin ella
termina con el código 2 antes de conectarse, en vez de saltar la comparación en silencio. Estas pruebas corren el
guion como proceso aparte con python -I y sin variables de libpq ni psql, así que un intento de conexión daría otro
código y otro mensaje. La corrida completa en los dos tramos, con la huella que da el primero, vive en
tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py.

Cada prueba nombra lo que debe pasar y lo que no debe pasar (AGENTS.md, regla 8).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SEMBRAR = RAIZ / "db" / "herramientas" / "sembrar_quimica.py"
HUELLA = "0123456789abcdef" * 4


def sembrar(*argumentos: str) -> subprocess.CompletedProcess[str]:
    entorno = {"PATH": os.environ["PATH"], "GUARDIA_DATOS_INVENTADOS": "0", "PSQL": "/nonexistent/psql"}
    return subprocess.run([sys.executable, "-I", str(SEMBRAR), *argumentos], env=entorno, capture_output=True,
                          text=True, check=False)


@pytest.mark.parametrize("desde", ["migraciones", "plan_quimica", "programacion", "coordinacion", "huella_despues"])
def test_un_tramo_sin_huella_antes_termina_con_2_antes_de_conectarse(desde: str, tmp_path: Path) -> None:
    """Debe pedir --huella-antes cuando huella_despues corre sin huella_antes. No debe conectarse ni correr un paso."""
    corrida = sembrar("--rama", "develop", "--aplicar", "--back-desplegado", "--desde", desde, "--programacion",
                      str(tmp_path / "programacion.csv"))
    assert corrida.returncode == 2, corrida.stdout + corrida.stderr
    assert "Falta --huella-antes" in corrida.stderr
    assert "== Paso" not in corrida.stdout and "guardia" not in corrida.stdout


@pytest.mark.parametrize("valor", ["", "abc", HUELLA.upper(), HUELLA + "0", "HUELLA DE AMBIENTAL|1|" + HUELLA])
def test_una_huella_antes_sin_forma_de_sha_256_termina_con_2(valor: str) -> None:
    """Debe aceptar solo 64 cifras hexadecimales en minúscula. No debe conectarse."""
    corrida = sembrar("--rama", "develop", "--desde", "controles", "--huella-antes", valor)
    assert corrida.returncode == 2, corrida.stdout + corrida.stderr
    assert "== Paso" not in corrida.stdout


def test_un_tramo_que_corre_huella_antes_o_no_llega_a_huella_despues_no_la_pide(tmp_path: Path) -> None:
    """No debe pedir --huella-antes si huella_antes corre o huella_despues no corre. Debe llegar a la comprobación
    previa, que sin psql termina con el código 3."""
    for argumentos in (("--desde", "huella_antes", "--programacion", str(tmp_path / "p.csv")),
                       ("--desde", "controles")):
        corrida = sembrar("--rama", "develop", "--aplicar", *argumentos)
        assert corrida.returncode == 3, corrida.stdout + corrida.stderr
        assert "Falta --huella-antes" not in corrida.stderr
