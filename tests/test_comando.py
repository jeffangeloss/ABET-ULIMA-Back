"""Pruebas del comando python -m abet_carga (parte de T039 de specs/001-mvp-carga-r17/tasks.md).

El comando carga un export en una sección y genera el R-17 y la constancia de una carga. Antes de
cargar o de leer pregunta a app/permisos.py (BR-ACCESO-07 y BR-ACCESO-08), y cada prueba nombra la
regla de negocio (business rule, BR) que comprueba, con lo que debe pasar y lo que no debe pasar
(AGENTS.md, regla 8). Las pruebas corren main() en el mismo proceso, con SET ROLE al rol de la
aplicación por --rol, sobre bases desechables del clúster de tests/conftest.py, y una sola corre el
comando como proceso aparte para probar python -m abet_carga.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import openpyxl
import psycopg
import pytest

from abet_carga.__main__ import main

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "tests" / "datos_inventados"
CON_ERROR = DATOS / "export_inventado_410_con_error.xlsx"
EXPORT_411 = DATOS / "export_inventado_411.xlsx"
DOCENTE_410 = "docente410@example.invalid"
DOCENTE_411 = "docente411@example.invalid"
COORDINACION = "coordinacion@example.invalid"
SIN_ALCANCE = "La sección no está a su cargo."
TABLAS = ("archivo_origen", "carga", "carga_columna", "carga_fila", "estudiante", "medicion", "rechazo_fila")


@pytest.fixture
def base(base_demo: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    monkeypatch.setenv("CONJUNTO_REGLAS", "R-2026-BORRADOR")
    monkeypatch.setenv("GUARDIA_DATOS_INVENTADOS", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return base_demo


def _cargar(base: Any, archivo: Path, correo: str = DOCENTE_410, seccion: str = "410", *extra: str) -> list[str]:
    return ["cargar", str(archivo), "--asignatura", "450002", "--seccion", seccion, "--periodo", "2026-2",
            "--correo", correo, "--base", base.conexion, "--rol", base.rol_app, *extra]


def _r17(base: Any, carga_id: int, carpeta: Path, correo: str = DOCENTE_410) -> list[str]:
    return ["r17", "--carga", str(carga_id), "--correo", correo, "--carpeta", str(carpeta),
            "--base", base.conexion, "--rol", base.rol_app]


def _correr(argumentos: list[str], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    codigo = main(argumentos)
    salida = capsys.readouterr()
    return codigo, salida.out + salida.err


def _conteos(base: Any) -> dict[str, int]:
    with psycopg.connect(base.conexion) as conexion:
        return {tabla: conexion.execute(f"SELECT count(*) FROM abet.{tabla}").fetchone()[0] for tabla in TABLAS}


def _carga_id(salida: str) -> int:
    return int(next(linea for linea in salida.splitlines() if linea.startswith("Carga: ")).split()[1])


def _nombres(archivo: Path) -> set[str]:
    """Last Name y First Name del export, que el comando nunca imprime (BR-CARGA-17)."""
    libro = openpyxl.load_workbook(archivo, read_only=True)
    filas = list(libro.worksheets[0].iter_rows(values_only=True))
    libro.close()
    columnas = [filas[0].index("Last Name"), filas[0].index("First Name")]
    return {str(fila[i]) for fila in filas[1:] for i in columnas if fila[i]}


# BR-CARGA-02 a 16 por el comando, con la pregunta previa a app/permisos.py.

def test_br_carga_16_el_comando_imprime_conteos_huella_estado_y_rechazos_sin_nombres_ni_valores(
    base: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    codigo, salida = _correr(_cargar(base, CON_ERROR), capsys)
    assert codigo == 0
    lineas = salida.splitlines()
    assert f"Huella SHA-256: {hashlib.sha256(CON_ERROR.read_bytes()).hexdigest()}" in lineas
    assert "Resultado: PUBLICADA (201)" in lineas
    assert "Estado: PUBLICADA" in lineas
    assert {"Filas leídas: 11", "Filas aceptadas: 10", "Filas rechazadas: 1"} <= set(lineas)
    assert "Rechazo: fila 3, PI 5.2, NIVEL_FUERA_DE_ESCALA" in lineas
    assert "Aviso: PI 5.3, PUNTAJE_MAXIMO_DISTINTO" in lineas
    assert not [nombre for nombre in _nombres(CON_ERROR) if nombre in salida]
    assert "valor" not in salida.lower()
    assert base.conexion not in salida


def test_br_carga_09_cargar_otra_vez_el_mismo_export_no_duplica_la_carga(
    base: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    _, primera = _correr(_cargar(base, CON_ERROR), capsys)
    antes = _conteos(base)
    codigo, segunda = _correr(_cargar(base, CON_ERROR), capsys)
    assert codigo == 0
    assert "Resultado: YA_PUBLICADA (200)" in segunda.splitlines()
    assert _carga_id(segunda) == _carga_id(primera)
    assert _conteos(base) == antes


def test_br_carga_11_una_carga_rechazada_sale_con_un_codigo_distinto_de_0(
    base: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    codigo, salida = _correr(_cargar(base, EXPORT_411), capsys)
    assert codigo != 0
    assert "Estado: RECHAZADA" in salida.splitlines()
    assert "Rechazo: carga, SECCION_NO_COINCIDE" in salida.splitlines()
    assert "Mensaje: El archivo corresponde a la sección 411 y usted eligió la 410. No se publicó." in salida


@pytest.mark.parametrize("correo", [DOCENTE_411, COORDINACION, "nadie@example.invalid"])
def test_br_acceso_08_quien_no_tiene_la_seccion_a_su_cargo_no_carga_ni_escribe(
    base: Any, capsys: pytest.CaptureFixture[str], correo: str
) -> None:
    antes = _conteos(base)
    codigo, salida = _correr(_cargar(base, CON_ERROR, correo), capsys)
    assert codigo != 0
    assert salida.strip() == SIN_ALCANCE
    assert _conteos(base) == antes


def test_br_acceso_08_una_seccion_que_no_existe_responde_igual_que_una_ajena(
    base: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    codigo, salida = _correr(_cargar(base, CON_ERROR, DOCENTE_410, "499"), capsys)
    assert codigo != 0 and salida.strip() == SIN_ALCANCE


def test_br_carga_01_sin_conjunto_reglas_el_comando_no_carga(
    base: Any, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CONJUNTO_REGLAS")
    antes = _conteos(base)
    codigo, salida = _correr(_cargar(base, CON_ERROR), capsys)
    assert codigo != 0 and "CONJUNTO_REGLAS" in salida
    assert _conteos(base) == antes


def test_br_carga_01_sin_base_ni_database_url_el_comando_no_conecta(
    base: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    argumentos = _cargar(base, CON_ERROR)
    sin_base = argumentos[: argumentos.index("--base")] + argumentos[argumentos.index("--rol"):]
    codigo, salida = _correr(sin_base, capsys)
    assert codigo != 0 and "DATABASE_URL" in salida


def test_br_carga_01_la_base_sale_de_database_url_cuando_no_llega_base(
    base: Any, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DATABASE_URL", base.conexion)
    argumentos = _cargar(base, CON_ERROR)
    sin_base = argumentos[: argumentos.index("--base")] + argumentos[argumentos.index("--rol"):]
    codigo, salida = _correr(sin_base, capsys)
    assert codigo == 0 and "Estado: PUBLICADA" in salida


# BR-R17-01 a 10 por el comando, con la lectura que app/permisos.py permite.

def test_br_r17_10_el_comando_genera_el_r17_y_la_constancia_en_la_carpeta(
    base: Any, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    _, salida = _correr(_cargar(base, CON_ERROR), capsys)
    carga_id = _carga_id(salida)
    codigo, salida = _correr(_r17(base, carga_id, tmp_path), capsys)
    assert codigo == 0
    r17 = tmp_path / "R017_450002_410_2026-2_PROVISIONAL.xlsx"
    constancia = tmp_path / f"constancia_{carga_id}.json"
    assert sorted(tmp_path.iterdir()) == sorted([r17, constancia])
    assert f"R-17: {r17}" in salida.splitlines()
    assert f"Constancia: {constancia}" in salida.splitlines()
    cuerpo = json.loads(constancia.read_text(encoding="utf-8"))
    assert (cuerpo["carga_id"], cuerpo["filas_aceptadas"], cuerpo["filas_rechazadas"]) == (carga_id, 10, 1)
    hoja = openpyxl.load_workbook(r17)["Cursos de Carrera"]
    assert [hoja[f"E{fila}"].value for fila in (24, 25, 26)] == pytest.approx([0.6, 0.6, 0.7])
    assert "Logro sobre calificados: 5.1 60,0 %, 5.2 60,0 %, 5.3 70,0 %" in salida.splitlines()


def test_br_r17_10_el_coordinador_lee_y_genera_el_r17_de_cualquier_seccion(
    base: Any, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    _, salida = _correr(_cargar(base, CON_ERROR), capsys)
    codigo, _ = _correr(_r17(base, _carga_id(salida), tmp_path, COORDINACION), capsys)
    assert codigo == 0 and len(list(tmp_path.iterdir())) == 2


@pytest.mark.parametrize("correo", [DOCENTE_411, "nadie@example.invalid"])
def test_br_acceso_08_quien_no_lee_la_seccion_no_recibe_r17_ni_constancia(
    base: Any, capsys: pytest.CaptureFixture[str], tmp_path: Path, correo: str
) -> None:
    _, salida = _correr(_cargar(base, CON_ERROR), capsys)
    codigo, salida = _correr(_r17(base, _carga_id(salida), tmp_path, correo), capsys)
    assert codigo != 0 and salida.strip() == SIN_ALCANCE
    assert list(tmp_path.iterdir()) == []


def test_br_acceso_08_una_carga_que_no_existe_responde_igual_que_una_ajena(
    base: Any, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    codigo, salida = _correr(_r17(base, 2_000_000_000, tmp_path), capsys)
    assert codigo != 0 and salida.strip() == SIN_ALCANCE
    assert list(tmp_path.iterdir()) == []


def test_br_r17_01_una_carga_rechazada_deja_su_constancia_y_ningun_r17(
    base: Any, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    _, salida = _correr(_cargar(base, EXPORT_411), capsys)
    carga_id = _carga_id(salida)
    codigo, salida = _correr(_r17(base, carga_id, tmp_path), capsys)
    assert codigo != 0
    assert [ruta.name for ruta in tmp_path.iterdir()] == [f"constancia_{carga_id}.json"]
    assert "R-17: no se genera, porque la carga no está publicada." in salida.splitlines()


def test_br_acceso_08_python_m_abet_carga_corre_como_proceso_aparte(base: Any) -> None:
    entorno = {**os.environ, "CONJUNTO_REGLAS": "R-2026-BORRADOR"}
    corrida = subprocess.run(
        [sys.executable, "-m", "abet_carga", *_cargar(base, CON_ERROR, DOCENTE_411)],
        cwd=RAIZ, env=entorno, capture_output=True, text=True, check=False,
    )
    assert corrida.returncode != 0
    assert corrida.stdout.strip() == SIN_ALCANCE
