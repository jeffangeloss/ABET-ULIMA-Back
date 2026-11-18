"""Permisos de lectura que usa GET /api/resultados, sin migración (T020 de la spec 004, FR-020 y J-26).

db/plataforma/neon/revisar_permisos_resultados.sql comprueba en solo lectura que el rol de la aplicación lee cada
tabla y vista que usa la ruta 12, la regla de alcance de app/permisos.py y la sesión. Jefferson lo corre en la rama
develop de Neon desde su Windows antes de fusionar el PR del Back (T021), y estas pruebas lo corren con psql contra
una copia de la base desechable de tests/api_de_prueba.py, con el rol de la aplicación de esa base.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import psycopg
from psycopg import sql

RAIZ = Path(__file__).resolve().parent.parent
GUION = RAIZ / "db" / "plataforma" / "neon" / "revisar_permisos_resultados.sql"
# Lo que lee la ruta 12, la sesión (app/sesion.py) y la regla de alcance (app/permisos.py).
LEE_LA_RUTA = (
    "abet.asignatura", "abet.carga", "abet.catalogo_vigencia", "abet.conjunto_reglas", "abet.instrumento",
    "abet.parametro_valor", "abet.periodo", "abet.pi", "abet.plan_estudios", "abet.plan_medicion", "abet.seccion",
    "abet.so", "abet.v_r17_por_pi", "acceso.docente_seccion", "acceso.sesion", "acceso.usuario_autorizado",
)


def _modulo(nombre: str) -> ModuleType:
    """Módulo de tests/ cargado por su ruta, porque tests/ no es un paquete."""
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, Path(__file__).with_name(f"{nombre}.py"))
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


A = _modulo("api_de_prueba")
plantilla, base, api = A.plantilla, A.base, A.api


def _revisar(base: object, **entorno: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [os.environ.get("PSQL", "psql"), "-X", "-q", "-v", "ON_ERROR_STOP=1", "-v", f"rol_app={base.rol_app}",
         "-d", base.conexion, "-f", str(GUION)],
        capture_output=True, text=True, check=False, env={**os.environ, **entorno},
    )


def test_fr_020_el_rol_de_la_aplicacion_lee_todo_lo_que_usa_la_ruta_12(base: object) -> None:
    corrida = _revisar(base)
    assert corrida.returncode == 0, corrida.stderr
    for objeto in LEE_LA_RUTA:
        assert f"{objeto}|t" in corrida.stdout, objeto
    assert "|f" not in corrida.stdout
    assert "Faltan 0 permisos de lectura de la ruta 12." in corrida.stdout


def test_fr_020_un_permiso_que_falta_detiene_la_revision_y_nombra_la_tabla(base: object) -> None:
    with psycopg.connect(base.conexion, autocommit=True) as dueno:
        dueno.execute(sql.SQL("REVOKE SELECT ON abet.instrumento FROM {}").format(sql.Identifier(base.rol_app)))
    corrida = _revisar(base)
    assert corrida.returncode != 0
    assert "abet.instrumento|f" in corrida.stdout
    assert "abet.instrumento" in corrida.stderr


def test_fr_020_la_revision_corre_en_una_sesion_de_solo_lectura(base: object) -> None:
    # Con default_transaction_read_only, cualquier escritura del guion fallaría con el SQLSTATE 25006.
    corrida = _revisar(base, PGOPTIONS="-c default_transaction_read_only=on")
    assert corrida.returncode == 0, corrida.stderr
    assert "Faltan 0 permisos de lectura de la ruta 12." in corrida.stdout
