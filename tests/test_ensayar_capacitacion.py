"""Negativas de db/herramientas/ensayar_capacitacion.py antes de conectarse (spec 008, US-84, T057).

El ensayo sube exports a una base, así que se niega antes de leer la tabla y de conectarse cuando un argumento falta,
cuando la tabla maestra, la carpeta de los exports o la de los R-17 están dentro de un repositorio git, que es
público (D-10), o cuando la carpeta de los R-17 ya trae archivos. Un manifiesto que no describe sus archivos se
rechaza antes de conectarse. Cada prueba corre el guion como proceso aparte con python -I y con PGHOST en una carpeta
que no existe, así un intento de conexión terminaría con el código 3 y no tocaría ningún PostgreSQL de la Mac. La
corrida completa, en el clúster desechable, vive en tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py.

Todo es inventado y vive en tmp_path. Cada prueba nombra lo que debe pasar y lo que no debe pasar (AGENTS.md, regla 8).
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from openpyxl import Workbook

RAIZ = Path(__file__).resolve().parent.parent
ENSAYO = RAIZ / "db" / "herramientas" / "ensayar_capacitacion.py"
GENERADOR = RAIZ / "scripts" / "generar_exports_desde_maestra.py"
COLUMNAS = ("AÑO", "CICLO", "CÓDIGO DEL CURSO", "CURSO", "CICLO DEL CURSO", "SO", "PI", "PROFESOR",
            "CÓDIGO DEL ESTUDIANTE", "SECCIÓN", "CALIFICACIÓN", "ARCHIVO")
OCHO_CIFRAS = re.compile(r"(?<![0-9])[0-9]{8}(?![0-9])")
ARGUMENTOS_INVALIDOS = "Argumentos inválidos. Lea el uso al comienzo de db/herramientas/ensayar_capacitacion.py."


def _maestra(carpeta: Path) -> Path:
    libro = Workbook()
    hoja = libro.active
    hoja.append(list(COLUMNAS))
    for seccion in ("701", "702"):
        for n, nivel in enumerate((3, 4, 2), start=1):
            hoja.append([2026, 1, "5643", "QUÍMICA GENERAL", 1, "6", "6.1", "Docente Inventado", f"99{seccion}{n:03d}",
                         seccion, nivel, "R017_inventado.xlsx"])
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "tabla_maestra_inventada.xlsx"
    libro.save(ruta)
    return ruta


def _exports(tmp_path: Path, maestra: Path) -> Path:
    """Exports y manifiesto del generador de US-74 sobre la tabla inventada, sin base."""
    programacion = tmp_path / "entrada" / "programacion.csv"
    texto = io.StringIO(newline="")
    escritor = csv.writer(texto, lineterminator="\r\n")
    escritor.writerow(("periodo", "asignatura", "seccion", "correo", "curso_blackboard"))
    for seccion in ("701", "702"):
        escritor.writerow(("2026-1", "5643", seccion, f"docente{seccion}@example.invalid", f"SINTETICO_20261_5643_{seccion}"))
    programacion.write_text(texto.getvalue(), encoding="utf-8")
    salida = tmp_path / "exports"
    corrida = subprocess.run([sys.executable, "-I", str(GENERADOR), "--maestra", str(maestra), "--programacion",
                              str(programacion), "--salida", str(salida), "--periodo", "2026-1", "--asignatura", "5643",
                              "--pi", "6.1", "--fecha", "2026-07-15-00-00-00"], capture_output=True, text=True,
                             encoding="utf-8", check=False)
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    return salida


@pytest.fixture
def entrada(tmp_path: Path) -> dict[str, Path]:
    maestra = _maestra(tmp_path / "entrada")
    return {"maestra": maestra, "exports": _exports(tmp_path, maestra), "r17": tmp_path / "r17"}


def ensayar(rutas: dict[str, Path], *extra: str, sin: str | None = None) -> subprocess.CompletedProcess[str]:
    # PGHOST en una carpeta que no existe, así una conexión no llega nunca a un PostgreSQL de la Mac.
    entorno = {"PATH": os.environ["PATH"], "PGHOST": "/nonexistent/abet_sin_servidor", "PGPORT": "1",
               "PGDATABASE": "abet_demo_no_existe", "PGCONNECT_TIMEOUT": "2"}
    argumentos = []
    for opcion in ("exports", "maestra", "r17"):
        if opcion != sin:
            argumentos += [f"--{opcion}", str(rutas[opcion])]
    if sin != "base-del-ensayo":
        argumentos += ["--base-del-ensayo", "/nonexistent/abet_sin_servidor/abet_demo_no_existe"]
    return subprocess.run([sys.executable, "-I", str(ENSAYO), *argumentos, "--reglas", "R-2026-BORRADOR", *extra],
                          env=entorno, capture_output=True, text=True, encoding="utf-8", check=False)


def _en_un_repositorio(tmp_path: Path) -> Path:
    repositorio = tmp_path / "repositorio"
    (repositorio / ".git").mkdir(parents=True, exist_ok=True)
    return repositorio


def _lineas(corrida: subprocess.CompletedProcess[str]) -> list[str]:
    return corrida.stdout.splitlines()


@pytest.mark.parametrize("sin", ["exports", "maestra", "r17", "base-del-ensayo"])
def test_sin_una_opcion_termina_con_2(entrada: dict[str, Path], sin: str) -> None:
    """Debe terminar con 2 y el mensaje de los argumentos. No debe conectarse, porque eso daría 3."""
    corrida = ensayar(entrada, sin=sin)
    assert corrida.returncode == 2, corrida.stdout + corrida.stderr
    assert _lineas(corrida) == [ARGUMENTOS_INVALIDOS]


def test_sin_conjunto_de_reglas_termina_con_2(entrada: dict[str, Path]) -> None:
    """Debe pedir --reglas o CONJUNTO_REGLAS. No debe adivinar el conjunto ni conectarse."""
    corrida = subprocess.run([sys.executable, "-I", str(ENSAYO), "--exports", str(entrada["exports"]), "--maestra",
                              str(entrada["maestra"]), "--r17", str(entrada["r17"])],
                             env={"PATH": os.environ["PATH"], "PGHOST": "/nonexistent/abet_sin_servidor"},
                             capture_output=True, text=True, encoding="utf-8", check=False)
    assert corrida.returncode == 2, corrida.stdout + corrida.stderr
    assert _lineas(corrida) == [ARGUMENTOS_INVALIDOS]


@pytest.mark.parametrize(("cual", "mensaje"), [
    ("maestra", "La tabla maestra está dentro de un repositorio git. Use una copia fuera de los repositorios."),
    ("exports", "La carpeta de los exports está dentro de un repositorio git. Use una copia fuera de los repositorios."),
    ("r17", "La carpeta de los R-17 está dentro de un repositorio git. Elija una carpeta fuera de los repositorios."),
])
def test_dentro_de_un_repositorio_termina_con_2_sin_escribir(entrada: dict[str, Path], tmp_path: Path, cual: str,
                                                             mensaje: str) -> None:
    """Debe negarse con 2 cuando una de las tres rutas está dentro de un repositorio git. No debe leer, conectarse ni
    crear la carpeta de los R-17."""
    repositorio = _en_un_repositorio(tmp_path)
    rutas = dict(entrada)
    rutas[cual] = repositorio / ("r17" if cual == "r17" else entrada[cual].name)
    if cual == "maestra":
        rutas["maestra"].write_bytes(entrada["maestra"].read_bytes())
        # Sin permiso de lectura, un ensayo que la abriera antes de la negativa terminaría con otro código.
        rutas["maestra"].chmod(0)
    elif cual == "exports":
        rutas["exports"].mkdir()
    corrida = ensayar(rutas)
    if cual == "maestra":
        rutas["maestra"].chmod(0o600)
    assert corrida.returncode == 2, corrida.stdout + corrida.stderr
    assert _lineas(corrida) == [mensaje]
    assert not (repositorio / "r17").exists()


def test_una_carpeta_de_r17_con_archivos_termina_con_2(entrada: dict[str, Path]) -> None:
    """Debe pedir una carpeta nueva o vacía para los R-17. No debe borrar ni tocar lo que ya trae."""
    entrada["r17"].mkdir()
    previo = entrada["r17"] / "R017_5643_701_2026-1.xlsx"
    previo.write_bytes(b"otro")
    corrida = ensayar(entrada)
    assert corrida.returncode == 2, corrida.stdout + corrida.stderr
    assert _lineas(corrida) == ["La carpeta de los R-17 ya tiene archivos. Elija una carpeta nueva o vacía."]
    assert previo.read_bytes() == b"otro"


def test_un_export_con_otra_huella_detiene_el_ensayo_antes_de_conectarse(entrada: dict[str, Path]) -> None:
    """Debe nombrar la sección cuyo archivo no tiene la huella del manifiesto y terminar con 1. No debe conectarse
    (eso daría 3) ni mostrar un número de ocho cifras."""
    manifiesto = json.loads((entrada["exports"] / "manifiesto.json").read_text(encoding="utf-8"))
    [segunda] = [e for e in manifiesto["exports"] if e["seccion"] == "702"]
    archivo = entrada["exports"] / segunda["archivo"]
    archivo.write_bytes(archivo.read_bytes() + b"\0")
    corrida = ensayar(entrada)
    assert corrida.returncode == 1, corrida.stdout + corrida.stderr
    assert _lineas(corrida) == ["Sección 702. El archivo no tiene la huella SHA-256 del manifiesto.",
                                "Ensayo detenido antes de subir. No se cargó ningún archivo."]
    assert not OCHO_CIFRAS.findall(corrida.stdout + corrida.stderr)


@pytest.mark.parametrize(("cambio", "mensaje"), [
    ("sin_manifiesto", "El manifiesto de los exports no se puede leer."),
    ("ejercicio", "El manifiesto es de un ejercicio. El ensayo sube los exports por sección."),
    ("ruta", "Sección 701. El manifiesto nombra un archivo fuera de la carpeta de los exports."),
    ("falta", "Sección 701. Falta el archivo que el manifiesto nombra."),
])
def test_un_manifiesto_que_no_describe_sus_archivos_se_rechaza(entrada: dict[str, Path], cambio: str,
                                                               mensaje: str) -> None:
    """Debe rechazar el manifiesto con 1 y su motivo. No debe conectarse ni subir nada."""
    ruta = entrada["exports"] / "manifiesto.json"
    manifiesto = json.loads(ruta.read_text(encoding="utf-8"))
    primera = manifiesto["exports"][0]
    if cambio == "sin_manifiesto":
        ruta.unlink()
    elif cambio == "ejercicio":
        primera["ejercicio"] = 1
    elif cambio == "ruta":
        primera["archivo"] = "../" + primera["archivo"]
    else:
        (entrada["exports"] / primera["archivo"]).unlink()
    if cambio != "sin_manifiesto":
        ruta.write_text(json.dumps(manifiesto), encoding="utf-8")
    corrida = ensayar(entrada)
    assert corrida.returncode == 1, corrida.stdout + corrida.stderr
    assert _lineas(corrida) == [mensaje, "Ensayo detenido antes de subir. No se cargó ningún archivo."]


def test_una_base_que_no_responde_termina_con_3(entrada: dict[str, Path]) -> None:
    """Con todo lo demás en orden, debe terminar con 3 y el aviso de la conexión. No debe crear la carpeta de los
    R-17 ni mostrar las variables de conexión."""
    corrida = ensayar(entrada)
    assert corrida.returncode == 3, corrida.stdout + corrida.stderr
    assert _lineas(corrida) == ["La base no responde. Revise las variables de conexión de libpq."]
    assert "nonexistent" not in corrida.stdout + corrida.stderr
    assert not entrada["r17"].exists()


# Cargas que no quedan limpias, sin base (cambio del 2026-11-23 del cierre de la spec 008)

def _modulo() -> ModuleType:
    """El guion cargado por su ruta, como lo carga el ensayo con scripts/, para cambiar sus piezas en una prueba."""
    especificacion = importlib.util.spec_from_file_location("ensayar_capacitacion_en_prueba", ENSAYO)
    modulo = importlib.util.module_from_spec(especificacion)
    # dataclasses busca el módulo de cada clase en sys.modules.
    sys.modules[especificacion.name] = modulo
    especificacion.loader.exec_module(modulo)
    return modulo


class _ConexionFalsa:
    """Una conexión que no llega a ningún PostgreSQL. El ensayo solo la pasa a las piezas que la prueba cambia."""

    info = SimpleNamespace(host="/nonexistent/abet_sin_servidor", dbname="abet_demo_no_existe")

    def __enter__(self) -> _ConexionFalsa:
        return self

    def __exit__(self, *_: object) -> None:
        return None


def _subir_con(modulo: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
               cuerpos: dict[int, tuple[int, int]], sin_r17: set[int]) -> tuple[list[str], bool]:
    """subir() con destinos, cargar(), la constancia y el R-17 cambiados. Cada sección 70N es la carga N."""
    exports = [modulo.Export(seccion, f"{seccion}.xls", b"inventado") for seccion in ("701", "702", "703")]
    manifiesto = modulo.Manifiesto("2026-1", "5643", "6.1", exports)
    monkeypatch.setattr(modulo, "destinos", lambda _c, _m: {e.seccion: (int(e.seccion), 99) for e in exports})
    monkeypatch.setattr(modulo, "cargar", lambda _c, _b, *, seccion_id, **_k: SimpleNamespace(
        carga_id=seccion_id - 700, resultado=modulo.Resultado.PUBLICADA))
    monkeypatch.setattr(modulo.constancia, "armar", lambda _c, carga_id: {
        "filas_aceptadas": cuerpos[carga_id][0], "filas_rechazadas": cuerpos[carga_id][1]})

    def generar(_c: object, carga_id: int, carpeta: Path) -> Path:
        if carga_id in sin_r17:
            raise modulo.r17.R17NoDisponible
        return carpeta / f"R017_{carga_id}.xlsx"

    monkeypatch.setattr(modulo.r17, "generar", generar)
    return modulo.subir(_ConexionFalsa(), manifiesto, None, tmp_path / "r17")


def test_una_carga_publicada_con_rechazos_o_sin_r17_no_queda_limpia(monkeypatch: pytest.MonkeyPatch,
                                                                    tmp_path: Path) -> None:
    """Debe decir las filas rechazadas de la 702 y que el R-17 de la 703 no se pudo generar, y no dar las cargas por
    limpias. No debe decir que la 702 o la 703 tienen su R-17 descargado."""
    modulo = _modulo()
    lineas, limpias = _subir_con(modulo, monkeypatch, tmp_path, {1: (5, 0), 2: (4, 1), 3: (5, 0)}, sin_r17={3})
    assert lineas == ["Sección 701. Carga PUBLICADA con 5 filas aceptadas y 0 rechazadas, y su R-17 descargado.",
                      "Sección 702. Carga PUBLICADA con 4 filas aceptadas y 1 rechazadas.",
                      "Sección 703. La carga quedó PUBLICADA y su R-17 no se pudo generar."]
    assert limpias is False
    # Cada causa basta sola para que las cargas no queden limpias.
    assert _subir_con(modulo, monkeypatch, tmp_path, {1: (5, 0), 2: (4, 1), 3: (5, 0)}, sin_r17=set())[1] is False
    assert _subir_con(modulo, monkeypatch, tmp_path, {1: (5, 0), 2: (5, 0), 3: (5, 0)}, sin_r17={3})[1] is False
    lineas, limpias = _subir_con(modulo, monkeypatch, tmp_path, {1: (5, 0), 2: (5, 0), 3: (5, 0)}, sin_r17=set())
    assert limpias is True and all(linea.endswith("y su R-17 descargado.") for linea in lineas)


def test_una_carga_que_no_queda_limpia_no_da_el_ensayo_por_bueno(entrada: dict[str, Path],
                                                                monkeypatch: pytest.MonkeyPatch) -> None:
    """Con el conciliador en 0 y una carga con filas rechazadas, debe terminar con 1 y «Ensayo con diferencias». No debe
    decir «Ensayo sin diferencias», porque el 0 exige además todas las cargas limpias."""
    modulo = _modulo()
    linea = "Sección 702. Carga PUBLICADA con 2 filas aceptadas y 1 rechazadas."
    monkeypatch.setattr(modulo.psycopg, "connect", lambda *_a, **_k: _ConexionFalsa())
    monkeypatch.setattr(modulo, "subir", lambda *_a: ([linea], False))
    monkeypatch.setattr(modulo, "conciliar",
                        lambda *_a: subprocess.CompletedProcess([], 0, "2 de 2 secciones iguales.\n", ""))
    argumentos = ["--exports", str(entrada["exports"]), "--maestra", str(entrada["maestra"]), "--r17",
                  str(entrada["r17"]), "--reglas", "R-2026-BORRADOR", "--base-del-ensayo",
                  "/nonexistent/abet_sin_servidor/abet_demo_no_existe"]
    codigo, lineas = modulo.principal(argumentos)
    assert codigo == 1
    assert lineas == [linea, "2 de 2 secciones iguales.",
                      "Ensayo con diferencias. No se da por bueno hasta resolverlas."]
    monkeypatch.setattr(modulo, "subir", lambda *_a: ([], True))
    assert modulo.principal(argumentos) == (0, [
        "2 de 2 secciones iguales.", "Ensayo sin diferencias. Las 2 secciones salen iguales a la tabla maestra."])
