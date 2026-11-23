"""Negativas y comprobación del respaldo de db/herramientas/cerrar_capacitacion.py sin base (spec 008, US-89, T056).

El cierre da de baja las cuentas de la capacitación y comprueba el respaldo por huella, sin borrar nada. Estas pruebas
corren el guion como proceso aparte con python -I y con PGHOST en una carpeta que no existe, así un intento de conexión
terminaría con el código 3 y no tocaría ningún PostgreSQL de la Mac. Cubren los argumentos inválidos, las rutas dentro
de un repositorio git, que es público (D-10), el manifiesto que no se lee, el respaldo con otra huella o sin el
manifiesto, la carpeta con otra huella, el CSV que se rechaza sin repetir sus correos, psql que falta y la base que no
responde. La baja en el clúster desechable vive en tests/aceptacion/pasos/test_capacitacion_en_develop_feature.py.

Todo es inventado y vive en tmp_path. Cada prueba nombra lo que debe pasar y lo que no debe pasar (AGENTS.md, regla 8).
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
CIERRE = RAIZ / "db" / "herramientas" / "cerrar_capacitacion.py"
OCHO_CIFRAS = re.compile(r"(?<![0-9])[0-9]{8}(?![0-9])")
D_55 = "Destino de las cargas de Química General pendiente de decisión (D-55)."
SECCIONES = ("701", "702", "703")


def _correr(tmp_path: Path, *argumentos: str, psql: str | None = None) -> subprocess.CompletedProcess[str]:
    assert CIERRE.exists(), "falta db/herramientas/cerrar_capacitacion.py (T056)"
    entorno = {"PATH": "/usr/bin:/bin", "PGHOST": str(tmp_path / "sin_servidor"), "PGDATABASE": "ninguna",
               "PGCONNECT_TIMEOUT": "2"}
    if psql is not None:
        entorno["PSQL"] = psql
    corrida = subprocess.run([sys.executable, "-I", str(CIERRE), *argumentos], env=entorno, capture_output=True,
                             text=True, encoding="utf-8", check=False, cwd=tmp_path)
    salida = corrida.stdout + corrida.stderr
    assert "@" not in salida, "la salida repite un correo"
    assert not OCHO_CIFRAS.search(salida), "la salida trae un número de ocho cifras"
    assert "Traceback" not in salida, salida
    return corrida


def _capacitacion(tmp_path: Path) -> Path:
    """Tres exports inventados, con bytes distintos, y su manifiesto, con la forma que escribe el generador."""
    carpeta = tmp_path / "capacitacion"
    carpeta.mkdir()
    entradas = []
    for seccion in SECCIONES:
        nombre = f"gc_SINTETICO_20261_5643_{seccion}_fullgc_2026-07-15-00-00-00.xlsx"
        contenido = f"export inventado de la {seccion}".encode()
        (carpeta / nombre).write_bytes(contenido)
        entradas.append({"seccion": seccion, "archivo": nombre, "sha256": hashlib.sha256(contenido).hexdigest(),
                         "filas": 4})
    manifiesto = {"periodo": "2026-1", "asignatura": "5643", "pi": "6.1", "exports": entradas}
    (carpeta / "manifiesto.json").write_text(json.dumps(manifiesto, indent=2) + "\n", encoding="utf-8")
    return carpeta


def _huellas(carpeta: Path) -> dict[str, str]:
    return {ruta.name: hashlib.sha256(ruta.read_bytes()).hexdigest() for ruta in sorted(carpeta.iterdir())}


def _respaldo(tmp_path: Path, carpeta: Path) -> Path:
    respaldo = tmp_path / "respaldo"
    shutil.copytree(carpeta, respaldo)
    return respaldo


def _exports(carpeta: Path) -> list[Path]:
    return sorted(ruta for ruta in carpeta.iterdir() if ruta.suffix == ".xlsx")


def _programacion(tmp_path: Path, filas: str | None = None) -> Path:
    ruta = tmp_path / "programacion_inventada.csv"
    cuerpo = filas if filas is not None else "".join(
        f"2026-1,5643,{s},docente{s}@example.invalid,SINTETICO_20261_5643_{s}\n" for s in SECCIONES)
    ruta.write_text("periodo,asignatura,seccion,correo,curso_blackboard\n" + cuerpo, encoding="utf-8")
    return ruta


# Argumentos

@pytest.mark.parametrize("argumentos", [
    (),
    ("--aplicar",),
    ("--capacitacion", "x"),
    ("--respaldo", "x"),
    ("--programacion", "x.csv"),
    ("--rama", "principal"),
    ("--destino", "main"),
    ("--programacion", "x.csv", "--periodo", "2026-1", "--apl"),
], ids=["sin_nada", "solo_aplicar", "sin_respaldo", "sin_capacitacion", "sin_periodo", "rama", "destino",
        "abreviatura"])
def test_un_argumento_invalido_termina_con_2_sin_leer(tmp_path: Path, argumentos: tuple[str, ...]) -> None:
    corrida = _correr(tmp_path, *argumentos)
    assert corrida.returncode == 2, corrida.stdout + corrida.stderr
    assert "Uso:" in corrida.stderr
    assert corrida.stdout == ""


def test_un_periodo_sin_forma_termina_con_2(tmp_path: Path) -> None:
    corrida = _correr(tmp_path, "--programacion", str(_programacion(tmp_path)), "--periodo", "2026")
    assert corrida.returncode == 2 and "El periodo no tiene la forma AAAA-C." in corrida.stderr


@pytest.mark.parametrize("cual", ["capacitacion", "respaldo", "programacion"])
def test_una_ruta_dentro_de_un_repositorio_termina_con_2_sin_leer(tmp_path: Path, cual: str) -> None:
    carpeta = _capacitacion(tmp_path)
    respaldo = _respaldo(tmp_path, carpeta)
    dentro = RAIZ / "tests" / "datos_inventados"
    rutas = {"capacitacion": carpeta, "respaldo": respaldo, "programacion": _programacion(tmp_path)}
    rutas[cual] = dentro / "programacion.csv" if cual == "programacion" else dentro
    argumentos = ["--capacitacion", str(rutas["capacitacion"]), "--respaldo", str(rutas["respaldo"])]
    if cual == "programacion":
        argumentos = ["--programacion", str(rutas["programacion"]), "--periodo", "2026-1"]
    corrida = _correr(tmp_path, *argumentos)
    assert corrida.returncode == 2, corrida.stdout + corrida.stderr
    assert "dentro de un repositorio git" in corrida.stderr
    assert "respaldados" not in corrida.stdout and "baja" not in corrida.stdout


# Respaldo

def test_el_respaldo_completo_da_0_y_no_borra_ni_escribe(tmp_path: Path) -> None:
    carpeta = _capacitacion(tmp_path)
    respaldo = _respaldo(tmp_path, carpeta)
    antes = (_huellas(carpeta), _huellas(respaldo), sorted(p.name for p in tmp_path.iterdir()))
    corrida = _correr(tmp_path, "--capacitacion", str(carpeta), "--respaldo", str(respaldo))
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    lineas = corrida.stdout.splitlines()
    assert "3 de 3 archivos respaldados y comprobados por su huella. Se pueden borrar de la Mac." in lineas
    assert lineas[-1] == D_55
    assert "El cierre no borra ningún archivo." in lineas
    assert (_huellas(carpeta), _huellas(respaldo), sorted(p.name for p in tmp_path.iterdir())) == antes


@pytest.mark.parametrize("faltan", [1, 2, 3])
def test_el_respaldo_incompleto_cuenta_lo_que_falta(tmp_path: Path, faltan: int) -> None:
    carpeta = _capacitacion(tmp_path)
    respaldo = _respaldo(tmp_path, carpeta)
    for ruta in _exports(respaldo)[:faltan]:
        ruta.unlink()
    corrida = _correr(tmp_path, "--capacitacion", str(carpeta), "--respaldo", str(respaldo))
    assert corrida.returncode == 1
    archivos = "1 archivo" if faltan == 1 else f"{faltan} archivos"
    assert f"El respaldo no trae {archivos} del manifiesto. No borre nada todavía." in corrida.stdout.splitlines()
    assert "Se pueden borrar" not in corrida.stdout
    assert len(_exports(carpeta)) == 3


def test_un_respaldo_con_otra_huella_no_se_da_por_bueno(tmp_path: Path) -> None:
    carpeta = _capacitacion(tmp_path)
    respaldo = _respaldo(tmp_path, carpeta)
    _exports(respaldo)[0].write_bytes(b"otro contenido")
    corrida = _correr(tmp_path, "--capacitacion", str(carpeta), "--respaldo", str(respaldo))
    assert corrida.returncode == 1
    assert ("El respaldo trae 1 archivo con otra huella que la del manifiesto. No borre nada todavía."
            in corrida.stdout.splitlines())
    assert "Se pueden borrar" not in corrida.stdout


def test_una_carpeta_con_otra_huella_no_se_da_por_buena(tmp_path: Path) -> None:
    carpeta = _capacitacion(tmp_path)
    respaldo = _respaldo(tmp_path, carpeta)
    _exports(carpeta)[1].write_bytes(b"cambiado despues del generador")
    corrida = _correr(tmp_path, "--capacitacion", str(carpeta), "--respaldo", str(respaldo))
    assert corrida.returncode == 1
    assert ("La carpeta de la capacitación trae 1 archivo con otra huella que la del manifiesto. No borre nada "
            "todavía." in corrida.stdout.splitlines())
    assert "Se pueden borrar" not in corrida.stdout


def test_un_respaldo_sin_el_manifiesto_no_se_da_por_bueno(tmp_path: Path) -> None:
    carpeta = _capacitacion(tmp_path)
    respaldo = _respaldo(tmp_path, carpeta)
    (respaldo / "manifiesto.json").unlink()
    corrida = _correr(tmp_path, "--capacitacion", str(carpeta), "--respaldo", str(respaldo))
    assert corrida.returncode == 1
    assert "El respaldo no trae el manifiesto igual al de la carpeta. No borre nada todavía." in corrida.stdout
    assert "Se pueden borrar" not in corrida.stdout


@pytest.mark.parametrize("contenido", ["no es json", '{"exports": []}', '{"exports": [{"seccion": "701"}]}',
                                       '{"exports": [{"seccion": "701", "archivo": "../fuera.xlsx", "sha256": "0"}]}'],
                         ids=["texto", "vacio", "sin_campos", "fuera_de_la_carpeta"])
def test_un_manifiesto_que_no_se_lee_termina_con_1(tmp_path: Path, contenido: str) -> None:
    carpeta = _capacitacion(tmp_path)
    respaldo = _respaldo(tmp_path, carpeta)
    (carpeta / "manifiesto.json").write_text(contenido, encoding="utf-8")
    corrida = _correr(tmp_path, "--capacitacion", str(carpeta), "--respaldo", str(respaldo))
    assert corrida.returncode == 1
    assert "El manifiesto de la carpeta de la capacitación no se puede leer. No borre nada todavía." in corrida.stdout
    assert "Se pueden borrar" not in corrida.stdout


# Baja sin base

def test_un_csv_que_se_rechaza_no_repite_sus_correos_ni_se_conecta(tmp_path: Path) -> None:
    csv = _programacion(tmp_path, "2026-1,5643,701,docente701@example.invalid,X\n2026-1,5643,702,no-es-correo,Y\n")
    corrida = _correr(tmp_path, "--programacion", str(csv), "--periodo", "2026-1", "--aplicar")
    assert corrida.returncode == 1, corrida.stdout + corrida.stderr
    assert ("La programación trae 1 fila sin la forma de cargar_programacion.py. Revísela en seco con ese guion. "
            "No se guardó nada." in corrida.stderr)
    assert "no-es-correo" not in corrida.stdout + corrida.stderr


def test_sin_psql_termina_con_3(tmp_path: Path) -> None:
    corrida = _correr(tmp_path, "--programacion", str(_programacion(tmp_path)), "--periodo", "2026-1",
                      psql=str(tmp_path / "no_existe" / "psql"))
    assert corrida.returncode == 3
    assert "No se encontró psql. PSQL nombra su ruta completa. No se guardó nada." in corrida.stderr


def test_una_base_que_no_responde_termina_con_3(tmp_path: Path) -> None:
    psql = shutil.which("psql")
    if psql is None:
        pytest.skip("psql no está en el PATH")
    corrida = _correr(tmp_path, "--programacion", str(_programacion(tmp_path)), "--periodo", "2026-1", "--aplicar",
                      psql=psql)
    assert corrida.returncode == 3
    assert "La base no respondió. No se guardó nada." in corrida.stderr
    assert "Dio de baja" not in corrida.stdout


def test_el_respaldo_se_comprueba_aunque_la_base_no_responda(tmp_path: Path) -> None:
    psql = shutil.which("psql")
    if psql is None:
        pytest.skip("psql no está en el PATH")
    carpeta = _capacitacion(tmp_path)
    respaldo = _respaldo(tmp_path, carpeta)
    corrida = _correr(tmp_path, "--programacion", str(_programacion(tmp_path)), "--periodo", "2026-1",
                      "--capacitacion", str(carpeta), "--respaldo", str(respaldo), psql=psql)
    assert corrida.returncode == 3
    assert "3 de 3 archivos respaldados y comprobados por su huella. Se pueden borrar de la Mac." in corrida.stdout


def test_el_guion_no_tiene_como_borrar_ni_escribir_archivos() -> None:
    """Una prueba del código fuente, además de las corridas, porque nunca borrar es la promesa central del cierre."""
    assert CIERRE.exists(), "falta db/herramientas/cerrar_capacitacion.py (T056)"
    codigo = CIERRE.read_text(encoding="utf-8")
    for prohibido in ("unlink", "rmtree", "rmdir", "os.remove", ".rename(", ".replace(", "write_text", "write_bytes",
                      "shutil", "neonctl", "flyway", '"git"'):
        assert prohibido not in codigo, f"el cierre usa {prohibido}"
    assert not re.search(r"open\([^)]*['\"][wax+]", codigo), "el cierre abre un archivo para escribir"


def test_una_carpeta_que_es_la_raiz_de_un_clon_termina_con_2(tmp_path: Path) -> None:
    """La carpeta misma con .git cuenta como dentro de un repositorio, como en el generador de US-74."""
    carpeta = _capacitacion(tmp_path)
    respaldo = _respaldo(tmp_path, carpeta)
    (respaldo / ".git").mkdir()
    corrida = _correr(tmp_path, "--capacitacion", str(carpeta), "--respaldo", str(respaldo))
    assert corrida.returncode == 2 and "El respaldo está dentro de un repositorio git." in corrida.stderr
    assert corrida.stdout == ""
