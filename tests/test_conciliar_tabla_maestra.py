"""Salida 3 de db/herramientas/conciliar_tabla_maestra.py cuando la base no responde (spec 008, US-83, FR-018).

El conciliador lee la tabla maestra antes de conectarse, así que una tabla válida en tmp_path llega hasta la conexión.
La prueba corre el guion como proceso aparte con python -I y con PGHOST en una carpeta que no existe, así la conexión
no llega nunca a un PostgreSQL de la Mac. La corrida completa, en el clúster desechable, vive en
tests/aceptacion/pasos/test_ensayo_y_conciliacion_feature.py.

Todo es inventado y vive en tmp_path. La prueba nombra lo que debe pasar y lo que no debe pasar (AGENTS.md, regla 8).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from openpyxl import Workbook

RAIZ = Path(__file__).resolve().parent.parent
CONCILIADOR = RAIZ / "db" / "herramientas" / "conciliar_tabla_maestra.py"
COLUMNAS = ("AÑO", "CICLO", "CÓDIGO DEL CURSO", "CURSO", "CICLO DEL CURSO", "SO", "PI", "PROFESOR",
            "CÓDIGO DEL ESTUDIANTE", "SECCIÓN", "CALIFICACIÓN", "ARCHIVO")
OCHO_CIFRAS = re.compile(r"(?<![0-9])[0-9]{8}(?![0-9])")
SIN_RESPUESTA = "La base no responde. Revise las variables de conexión de libpq."


def _maestra(carpeta: Path) -> Path:
    """Tabla maestra inventada con las secciones 701 y 702 y códigos del rango 99."""
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


def test_una_base_que_no_responde_termina_con_3(tmp_path: Path) -> None:
    """Con la tabla maestra válida y fuera de un repositorio, debe terminar con 3 y solo el aviso de la conexión. No
    debe mostrar las variables de conexión, un código de ocho cifras ni una línea de conciliación."""
    entorno = {"PATH": os.environ["PATH"], "PGHOST": "/nonexistent/abet_sin_servidor", "PGPORT": "1",
               "PGDATABASE": "abet_demo_no_existe", "PGUSER": "abet_respaldo", "PGCONNECT_TIMEOUT": "2"}
    corrida = subprocess.run([sys.executable, "-I", str(CONCILIADOR), "--maestra", str(_maestra(tmp_path / "entrada")),
                              "--periodo", "2026-1", "--asignatura", "5643", "--pi", "6.1"],
                             env=entorno, capture_output=True, text=True, encoding="utf-8", check=False, cwd=tmp_path)
    salida = corrida.stdout + corrida.stderr
    assert corrida.returncode == 3, salida
    assert corrida.stdout.splitlines() == [SIN_RESPUESTA], salida
    assert "nonexistent" not in salida and "abet_demo_no_existe" not in salida
    assert not OCHO_CIFRAS.findall(salida)
