"""Pruebas de db/plataforma/neon/profesores_sin_nombre.sql (US-98 y FR-011 de la spec 010, T023).

La consulta cuenta las secciones publicadas de un periodo con algún profesor asignado sin nombre y los profesores
asignados sin nombre, y no muestra correos, nombres ni números de sección. Corre con psql 18 del clúster desechable de
tests/cluster_desechable.py y nunca en localhost:5432. La base parte de db/pruebas/datos_sinteticos.sql, que publica la
410 de 450002 en 2026-2, y de los datos inventados de 2026-2 con sus nombres.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
import pytest

RAIZ = Path(__file__).resolve().parent.parent
CONSULTA = RAIZ / "db" / "plataforma" / "neon" / "profesores_sin_nombre.sql"
ROTULOS = ["Secciones publicadas del periodo con algún profesor asignado sin nombre.",
           "Profesores asignados sin nombre a esas secciones."]


@pytest.fixture(scope="module")
def cargas() -> ModuleType:
    """tests/cargas_de_prueba.py cargado por su ruta, porque tests/ no es un paquete."""
    if "cargas_de_prueba" not in sys.modules:
        especificacion = importlib.util.spec_from_file_location("cargas_de_prueba", RAIZ / "tests" / "cargas_de_prueba.py")
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[especificacion.name] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules["cargas_de_prueba"]


@pytest.fixture
def base(crear_base_demo: Callable[..., Any], base_desechable: ModuleType, cargas: ModuleType) -> Any:
    """Base con la 410 de 450002 PUBLICADA y los usuarios de 2026-2 con sus nombres inventados."""
    return crear_base_demo(datos_2026_2=False, despues=[cargas.SINTETICOS, base_desechable.DATOS_2026_2])


def _correr(base: Any, *variables: str, rol: str | None = None) -> subprocess.CompletedProcess[str]:
    entorno = sys.modules["base_desechable"]._entorno()
    if rol is not None:
        entorno["PGUSER"] = rol
    argumentos = [valor for variable in variables for valor in ("-v", variable)]
    return subprocess.run(["psql", "-X", "-A", "-t", "-d", base.nombre, "-v", "ON_ERROR_STOP=1", *argumentos,
                           "-f", str(CONSULTA)], env=entorno, capture_output=True, text=True, encoding="utf-8",
                          check=False, timeout=60)


def _cifras(base: Any, periodo: str = "2026-2") -> tuple[int, int]:
    corrida = _correr(base, f"periodo={periodo}")
    assert corrida.returncode == 0, corrida.stderr
    salida = corrida.stdout.splitlines()
    assert salida[:2] == ["SET", "on"], salida
    assert [salida[2], salida[4]] == ROTULOS, salida
    assert len(salida) == 6, salida
    return int(salida[3]), int(salida[5])


def _sql(base: Any, sentencia: str, *parametros: object) -> None:
    with psycopg.connect(base.conexion, autocommit=True) as conexion:
        conexion.execute(sentencia, parametros or None)


def test_con_todos_los_profesores_con_nombre_la_consulta_da_cero_y_cero(base: Any) -> None:
    assert _cifras(base) == (0, 0)


def test_un_profesor_sin_nombre_en_una_seccion_publicada_cuenta_una_seccion_y_un_profesor(base: Any) -> None:
    _sql(base, "UPDATE acceso.usuario_autorizado SET nombre = NULL WHERE correo = 'docente410@example.invalid'")
    assert _cifras(base) == (1, 1)


def test_un_profesor_sin_nombre_de_una_seccion_sin_carga_publicada_no_cuenta(base: Any) -> None:
    # La 411 tiene a docente411 asignado y ninguna carga, así que su profesor sin nombre no entra.
    _sql(base, "UPDATE acceso.usuario_autorizado SET nombre = NULL WHERE correo = 'docente411@example.invalid'")
    assert _cifras(base) == (0, 0)


def test_una_carga_reemplazada_no_cuenta_aunque_su_profesor_no_tenga_nombre(base: Any) -> None:
    _sql(base, "UPDATE acceso.usuario_autorizado SET nombre = NULL WHERE correo = 'docente410@example.invalid'")
    _sql(base, "UPDATE abet.carga SET estado = 'REEMPLAZADA'")
    assert _cifras(base) == (0, 0)


def test_otro_periodo_da_cero_y_un_periodo_inexistente_tambien(base: Any) -> None:
    _sql(base, "UPDATE acceso.usuario_autorizado SET nombre = NULL WHERE correo = 'docente410@example.invalid'")
    assert _cifras(base, "2026-1") == (0, 0)
    assert _cifras(base, "2031-1") == (0, 0)


def test_un_profesor_dado_de_baja_sin_nombre_cuenta_como_en_el_r17(base: Any) -> None:
    _sql(base, "UPDATE acceso.usuario_autorizado SET nombre = NULL, activo = false WHERE correo = 'docente410@example.invalid'")
    assert _cifras(base) == (1, 1)


def test_una_cuenta_coordinador_asignada_y_sin_nombre_no_cuenta(base: Any) -> None:
    _sql(base, "INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)"
              " SELECT u.usuario_id, s.seccion_id FROM acceso.usuario_autorizado u, abet.seccion s"
              " WHERE u.correo = 'coordinacion@example.invalid' AND s.numero = '410'")
    assert _cifras(base) == (0, 0)


def test_dos_profesores_sin_nombre_en_la_misma_seccion_cuentan_una_seccion_y_dos_profesores(base: Any) -> None:
    _sql(base, "INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES ('docente743@example.invalid', 'PROFESOR')")
    _sql(base, "INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)"
              " SELECT u.usuario_id, s.seccion_id FROM acceso.usuario_autorizado u, abet.seccion s"
              " WHERE u.correo = 'docente743@example.invalid' AND s.numero = '410'")
    _sql(base, "UPDATE acceso.usuario_autorizado SET nombre = NULL WHERE correo = 'docente410@example.invalid'")
    assert _cifras(base) == (1, 2)


def test_la_salida_no_trae_correos_nombres_ni_numeros_de_seccion(base: Any) -> None:
    _sql(base, "UPDATE acceso.usuario_autorizado SET nombre = NULL WHERE correo = 'docente410@example.invalid'")
    corrida = _correr(base, "periodo=2026-2")
    texto = corrida.stdout + corrida.stderr
    assert not any(valor in texto for valor in ("@", "example", "docente", "Profesor Inventado", "410", "411", "450002"))


def test_sin_la_variable_periodo_se_detiene_antes_de_consultar(base: Any) -> None:
    corrida = _correr(base)
    assert corrida.returncode != 0
    assert not any(rotulo in corrida.stdout for rotulo in ROTULOS)


def test_la_sesion_queda_en_solo_lectura_aunque_la_corra_el_dueno(base: Any) -> None:
    texto = CONSULTA.read_text(encoding="utf-8")
    assert texto.index("SET default_transaction_read_only = on;") < texto.index("SELECT count(DISTINCT")
    escritura = subprocess.run(
        ["psql", "-X", "-A", "-t", "-d", base.nombre, "-v", "ON_ERROR_STOP=1", "-v", "periodo=2026-2", "-f", str(CONSULTA),
         "-c", "UPDATE acceso.usuario_autorizado SET activo = activo"],
        env=sys.modules["base_desechable"]._entorno(), capture_output=True, text=True, encoding="utf-8", check=False)
    assert "read-only" in escritura.stderr or "solo lectura" in escritura.stderr, escritura.stderr


def test_no_escribe_ni_nombra_ninguna_sentencia_que_escribe() -> None:
    sin_comentarios = "\n".join(linea for linea in CONSULTA.read_text(encoding="utf-8").splitlines()
                                if not linea.startswith("--"))
    for palabra in ("INSERT", "UPDATE", "DELETE", "TRUNCATE", "CREATE", "ALTER", "DROP", "GRANT"):
        assert palabra not in sin_comentarios.upper().replace("DISTINCT", ""), palabra
