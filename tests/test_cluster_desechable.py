"""Guardia del clúster desechable (tests/cluster_desechable.py y _entorno() de tests/base_desechable.py).

Lo que debe pasar: la sesión de pruebas crea sus bases en un clúster propio, cuyo data_directory es
el que nombra ABET_CLUSTER_DESECHABLE. Lo que no debe pasar: ninguna variable de libpq que apunte a
localhost:5432, el clúster de la Mac, llega a correr una sentencia, ni siquiera con el nombre de una
base desechable.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

RAIZ = Path(__file__).resolve().parent.parent


def _modulo() -> ModuleType:
    nombre = "cluster_desechable"
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, RAIZ / "tests" / "cluster_desechable.py")
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


@pytest.mark.skipif(os.environ.get("GITHUB_ACTIONS") == "true", reason="la CI usa el servicio postgres:16 del job")
def test_la_sesion_corre_en_el_cluster_desechable(cluster_postgres: dict[str, str]) -> None:
    datos = cluster_postgres[_modulo().VARIABLE]
    respuesta = subprocess.run(
        ["psql", "-X", "-At", "-d", "postgres", "-c", "SHOW data_directory"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert Path(respuesta).resolve() == Path(datos).resolve()
    assert os.environ["PGHOST"] == cluster_postgres["PGHOST"] != "localhost"
    assert os.environ["PGPORT"] == "54329"


@pytest.mark.parametrize(
    "variables",
    [
        {},
        {"PGHOST": "localhost", "PGPORT": "5432"},
        {"PGHOST": "/tmp", "PGPORT": "5432"},
        {"PGHOST": "localhost", "PGPORT": "5432", "ABET_CLUSTER_DESECHABLE": "/tmp/abet_pg_otro/datos"},
    ],
)
def test_exigir_rechaza_lo_que_no_es_el_cluster_desechable(variables: dict[str, str]) -> None:
    with pytest.raises(_modulo().ClusterAjeno):
        _modulo().exigir(variables)


def test_exigir_acepta_el_servicio_de_la_ci() -> None:
    _modulo().exigir(
        {"GITHUB_ACTIONS": "true", "RUNNER_TEMP": "/home/runner/work/_temp", "PGHOST": "localhost", "PGPORT": "5432"},
        plataforma="linux",
    )


@pytest.mark.parametrize(
    ("variables", "plataforma"),
    [
        # GITHUB_ACTIONS=true exportada en la Mac no vuelve a la Mac una CI.
        ({"GITHUB_ACTIONS": "true", "RUNNER_TEMP": "/Users/x/tmp", "PGHOST": "localhost", "PGPORT": "5432"}, "darwin"),
        ({"GITHUB_ACTIONS": "true", "PGHOST": "localhost", "PGPORT": "5432"}, "darwin"),
        # Sin RUNNER_TEMP, que GitHub Actions define en cada job, tampoco basta en Linux.
        ({"GITHUB_ACTIONS": "true", "PGHOST": "localhost", "PGPORT": "5432"}, "linux"),
        ({"GITHUB_ACTIONS": "true", "RUNNER_TEMP": "", "PGHOST": "localhost", "PGPORT": "5432"}, "linux"),
    ],
)
def test_exigir_rechaza_github_actions_sin_la_ci_real(variables: dict[str, str], plataforma: str) -> None:
    assert _modulo().en_ci(variables, plataforma) is False
    with pytest.raises(_modulo().ClusterAjeno):
        _modulo().exigir(variables, plataforma=plataforma)


def _iniciar_con_initdb_falso(tmp_path: Path, variables: dict[str, str]) -> bool:
    """Corre iniciar_cluster_desechable con un initdb falso y dice si llegó a llamarlo."""
    falsos = tmp_path / "bin"
    falsos.mkdir()
    marca = tmp_path / "initdb_llamado"
    initdb = falsos / "initdb"
    initdb.write_text(f"#!/bin/sh\ntouch '{marca}'\nexit 1\n", encoding="utf-8")
    initdb.chmod(0o755)
    entorno = {"PATH": f"{falsos}:{os.environ['PATH']}", "TMPDIR": str(tmp_path), **variables}
    subprocess.run(
        ["bash", "-c", 'source "$0"; iniciar_cluster_desechable', str(RAIZ / "db" / "pruebas" / "cluster_desechable.sh")],
        env=entorno, capture_output=True, text=True, check=False,
    )
    return marca.exists()


@pytest.mark.parametrize(
    "variables",
    [{"GITHUB_ACTIONS": "true"}, {"GITHUB_ACTIONS": "true", "RUNNER_TEMP": ""}],
)
def test_el_guion_no_toma_github_actions_solo_como_prueba_de_la_ci(tmp_path: Path, variables: dict[str, str]) -> None:
    assert _iniciar_con_initdb_falso(tmp_path, variables) is True


@pytest.mark.skipif(sys.platform == "darwin", reason="en la Mac nunca se toma una CI")
def test_el_guion_reconoce_el_servicio_de_la_ci_en_linux(tmp_path: Path) -> None:
    assert _iniciar_con_initdb_falso(tmp_path, {"GITHUB_ACTIONS": "true", "RUNNER_TEMP": str(tmp_path)}) is False


@pytest.mark.skipif(sys.platform != "darwin", reason="solo la Mac es el caso que se rechaza")
def test_el_guion_rechaza_github_actions_en_la_mac(tmp_path: Path) -> None:
    variables = {"GITHUB_ACTIONS": "true", "RUNNER_TEMP": str(tmp_path)}
    assert _iniciar_con_initdb_falso(tmp_path, variables) is True


def test_base_desechable_no_corre_nada_contra_el_cluster_de_la_mac(
    base_desechable: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("ABET_CLUSTER_DESECHABLE", raising=False)
    monkeypatch.setenv("PGHOST", "localhost")
    monkeypatch.setenv("PGPORT", "5432")

    def sin_ejecutar(*_argumentos: object, **_opciones: object) -> None:
        raise AssertionError("base_desechable corre una sentencia fuera del clúster desechable")

    monkeypatch.setattr(base_desechable.subprocess, "run", sin_ejecutar)
    ajena = base_desechable.BaseDesechable(nombre="abet_demo_x", conexion="", rol_app=None, conexion_app=None)
    with pytest.raises(_modulo().ClusterAjeno):
        base_desechable.borrar(ajena)
    with pytest.raises(_modulo().ClusterAjeno):
        base_desechable.restos()
