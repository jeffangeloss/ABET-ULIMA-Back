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

import importlib.util
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


# El nombre del profesor en la programación (spec 010, US-96, T036)

def _siembra() -> object:
    especificacion = importlib.util.spec_from_file_location("sembrar_quimica_010", SEMBRAR)
    assert especificacion is not None and especificacion.loader is not None
    modulo = importlib.util.module_from_spec(especificacion)
    sys.modules[especificacion.name] = modulo
    especificacion.loader.exec_module(modulo)
    return modulo


def test_el_paso_programacion_no_cambia_con_la_columna_nombre_y_las_migraciones_siguen_en_la_1_14() -> None:
    pasos = {paso.nombre: paso for paso in _siembra().PASOS}
    programacion = pasos["programacion"]
    assert programacion.aplicado == ("{python}", "-I", "db/herramientas/cargar_programacion.py", "--periodo", "2026-1",
                                     "--archivo", "{programacion}", "--aplicar")
    assert programacion.en_seco == programacion.aplicado[:-1]
    assert "-target=1.14" in pasos["migraciones"].aplicado and "-target=1.16" not in pasos["migraciones"].aplicado
    assert not any("nombre" in argumento for paso in pasos.values() for argumento in (paso.aplicado or ()))


def test_el_docstring_dice_que_v1_16_la_aplica_migrar_neon_antes_de_la_siembra() -> None:
    doc = _siembra().__doc__
    assert "V1_16" in doc and "migrar_neon.sh" in doc and "columna opcional nombre" in doc


def test_ninguna_salida_de_la_siembra_oculta_ni_repite_un_nombre_de_profesor() -> None:
    texto = SEMBRAR.read_text(encoding="utf-8")
    assert "nombre" not in {n.lower() for n in _siembra().OCULTAS}
    assert "Profesor Inventado" not in texto
