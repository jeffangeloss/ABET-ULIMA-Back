"""Pruebas de la ayuda de bases desechables (tests/base_desechable.py).

crear() y borrar() corren de verdad solo en el clúster desechable que arma la fixture cluster_postgres
de tests/conftest.py, nunca en el clúster de la Mac (localhost:5432), y en la integración continua
(continuous integration, CI) en el servicio postgres:18 del job, con las variables PGHOST, PGPORT y
PGUSER de libpq y sin contraseñas. Cada base y cada rol de esas pruebas llevan el prefijo abet_demo_.
Las guardias de nombres de borrar() y de crear() se prueban sin servidor, con una ejecución falsa de
subprocess.run y las variables de libpq apuntando a una carpeta vacía, así que ni un mutante sin la
guardia alcanza una base con abet_sis_med_dev u otro nombre real. Cada prueba comprueba lo que debe
pasar y lo que no debe pasar (AGENTS.md, regla 8). Toda prueba que pide una base lleva el marcador
base, que tests/conftest.py pone solo, así que pytest -m "not base" las deja fuera.
"""

from __future__ import annotations

import os
import re
import secrets
import subprocess
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, NoReturn

import psycopg
import pytest
from psycopg import errors, sql

from abet_carga.modelos import Efecto, Motivo


def _sin_servidor(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list[object]:
    """Deja a base_desechable sin servidor al que llegar y devuelve la lista de órdenes que intenta correr.

    subprocess.run pasa a una ejecución falsa que anota la orden y falla, y las variables de libpq
    apuntan a una carpeta de tmp_path sin servidor y sin ABET_CLUSTER_DESECHABLE, así que ni la guardia
    de nombres ni la de _entorno() ni la ejecución falsa dejan llegar una sentencia a una base.
    """
    ordenes: list[object] = []

    def ejecucion_falsa(orden: object, *_argumentos: object, **_opciones: object) -> NoReturn:
        ordenes.append(orden)
        raise AssertionError("base_desechable intenta correr una orden que la guardia debía detener")

    monkeypatch.setattr(subprocess, "run", ejecucion_falsa)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("ABET_CLUSTER_DESECHABLE", raising=False)
    monkeypatch.setenv("PGHOST", str(tmp_path / "sin_servidor"))
    monkeypatch.setenv("PGPORT", "1")
    return ordenes


def _quedan(modulo: ModuleType) -> tuple[set[str], set[str]]:
    bases, roles = modulo.restos()
    return set(bases), set(roles)


def _uno(conexion: psycopg.Connection, consulta: str) -> object:
    fila = conexion.execute(consulta).fetchone()
    assert fila is not None
    return fila[0]


def test_crea_la_base_con_migraciones_rol_y_datos_y_la_borra_al_salir(base_desechable: ModuleType) -> None:
    with base_desechable.abierta() as base:
        sufijo = base.nombre.removeprefix("abet_demo_")
        assert re.fullmatch(r"[0-9]+_[0-9a-f]{8}", sufijo)
        assert base.rol_app == f"abet_demo_app_{sufijo}"
        assert "password" not in base.conexion and "password" not in (base.conexion_app or "")
        bases, roles = _quedan(base_desechable)
        assert base.nombre in bases and base.rol_app in roles
        with psycopg.connect(base.conexion) as conexion:
            # V1_09 aplicada, con el PI de los rechazos de estructura y el autor de cada carga.
            nuevas = (
                "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'abet' "
                "AND (table_name, column_name) IN (('rechazo_fila', 'pi_id'), ('carga', 'subida_por'))"
            )
            assert _uno(conexion, nuevas) == 2
            # Las repetibles R__ aplicadas, con la vista del R-17 vacía.
            assert _uno(conexion, "SELECT count(*) FROM abet.v_r17_por_pi") == 0
            secciones = conexion.execute(
                "SELECT s.numero, s.curso_blackboard FROM abet.seccion s JOIN abet.periodo p USING (periodo_id) "
                "WHERE p.codigo = '2026-2' ORDER BY s.numero"
            ).fetchall()
            assert secciones == [("410", "SINTETICO_20262_450002_410"), ("411", "SINTETICO_20262_450002_411")]
            plan = conexion.execute(
                "SELECT pi.codigo FROM abet.plan_medicion pm JOIN abet.pi pi USING (pi_id) "
                "JOIN abet.asignatura a USING (asignatura_id) WHERE a.codigo = '450002' ORDER BY pi.codigo"
            ).fetchall()
            assert plan == [("5.1",), ("5.2",), ("5.3",)]
            usuarios = conexion.execute("SELECT correo, rol FROM acceso.usuario_autorizado ORDER BY correo").fetchall()
            assert usuarios == [
                ("coordinacion@example.invalid", "COORDINADOR"),
                ("docente410@example.invalid", "PROFESOR"),
                ("docente411@example.invalid", "PROFESOR"),
            ]
            # Sin guardia=True la base no lleva ck_estudiante_codigo_inventado.
            guardias = "SELECT count(*) FROM pg_constraint WHERE conname = 'ck_estudiante_codigo_inventado'"
            assert _uno(conexion, guardias) == 0
        assert base.conexion_app is not None
        with psycopg.connect(base.conexion_app) as aplicacion:
            assert _uno(aplicacion, "SELECT current_user") == base.rol_app
            assert _uno(aplicacion, "SELECT count(*) FROM abet.seccion") == 2
            with pytest.raises(errors.InsufficientPrivilege):
                aplicacion.execute("DELETE FROM abet.carga")
    bases, roles = _quedan(base_desechable)
    assert base.nombre not in bases
    assert base.rol_app not in roles


def test_la_base_y_el_rol_se_borran_aunque_la_prueba_falle(base_desechable: ModuleType) -> None:
    with pytest.raises(RuntimeError, match="falla a propósito"):
        with base_desechable.abierta() as base:
            nombre, rol = base.nombre, base.rol_app
            raise RuntimeError("falla a propósito")
    bases, roles = _quedan(base_desechable)
    assert nombre not in bases
    assert rol not in roles


def test_si_un_paso_de_la_creacion_falla_no_queda_ni_la_base_ni_el_rol(
    base_desechable: ModuleType, tmp_path: Path
) -> None:
    roto = tmp_path / "roto.sql"
    roto.write_text("SELECT 1 / 0;\n", encoding="utf-8")
    sufijo = f"falla_{os.getpid()}_{secrets.token_hex(3)}"
    with pytest.raises(base_desechable.ErrorDeBase) as error:
        base_desechable.crear(sufijo, despues=(roto,))
    assert "roto.sql" in str(error.value)
    bases, roles = _quedan(base_desechable)
    assert f"abet_demo_{sufijo}" not in bases
    assert f"abet_demo_app_{sufijo}" not in roles


def test_una_creacion_que_choca_con_una_base_viva_no_la_borra(base_desechable: ModuleType) -> None:
    with base_desechable.abierta() as base:
        sufijo = base.nombre.removeprefix("abet_demo_")
        with pytest.raises(base_desechable.ErrorDeBase):
            base_desechable.crear(sufijo)
        bases, roles = _quedan(base_desechable)
        assert base.nombre in bases and base.rol_app in roles
        with psycopg.connect(base.conexion) as conexion:
            assert _uno(conexion, "SELECT count(*) FROM abet.seccion") == 2


def test_un_rol_que_ya_existe_no_se_toma_ni_se_borra(base_desechable: ModuleType) -> None:
    sufijo = f"rol_{os.getpid()}_{secrets.token_hex(3)}"
    rol = f"abet_demo_app_{sufijo}"
    with base_desechable.abierta(rol_app=False) as base, psycopg.connect(base.conexion, autocommit=True) as conexion:
        conexion.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(rol)))
        try:
            with pytest.raises(base_desechable.ErrorDeBase, match="ya existe"):
                base_desechable.crear(sufijo)
            bases, roles = _quedan(base_desechable)
            # La base que alcanzó a crear la llamada se borra, y el rol que ya existía se queda.
            assert f"abet_demo_{sufijo}" not in bases
            assert rol in roles
        finally:
            conexion.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(rol)))
    assert rol not in _quedan(base_desechable)[1]


def test_el_rol_de_la_aplicacion_no_recibe_contrasena_aunque_la_terminal_tenga_app_db_clave(
    base_desechable: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Una terminal preparada para Neon puede traer APP_DB_CLAVE, y el rol desechable nunca la toma.
    monkeypatch.setenv("APP_DB_CLAVE", "no-debe-llegar")
    with base_desechable.abierta(datos_2026_2=False) as base, psycopg.connect(base.conexion) as conexion:
        consulta = "SELECT rolpassword IS NULL FROM pg_authid WHERE rolname = %s"
        fila = conexion.execute(consulta, (base.rol_app,)).fetchone()
    assert fila == (True,)


def test_la_guardia_de_la_base_rechaza_un_codigo_que_no_es_inventado(crear_base_demo: Callable[..., Any]) -> None:
    base = crear_base_demo(guardia=True)
    with psycopg.connect(base.conexion_app) as aplicacion:
        with pytest.raises(errors.CheckViolation) as error:
            aplicacion.execute("INSERT INTO abet.estudiante (codigo) VALUES (%s)", ("10000004",))
        assert error.value.diag.constraint_name == "ck_estudiante_codigo_inventado"
        aplicacion.rollback()
        aplicacion.execute("INSERT INTO abet.estudiante (codigo) VALUES (%s)", ("99000001",))
        aplicacion.rollback()


def test_sin_rol_ni_datos_la_base_trae_solo_las_migraciones(crear_base_demo: Callable[..., Any]) -> None:
    base = crear_base_demo(rol_app=False, datos_2026_2=False)
    assert (base.rol_app, base.conexion_app) == (None, None)
    with psycopg.connect(base.conexion) as conexion:
        assert _uno(conexion, "SELECT count(*) FROM abet.pi") == 17
        assert _uno(conexion, "SELECT count(*) FROM abet.seccion WHERE curso_blackboard LIKE 'SINTETICO_20262_%'") == 0
        assert _uno(conexion, "SELECT count(*) FROM acceso.usuario_autorizado") == 0


@pytest.mark.parametrize(
    ("nombre", "rol_app"),
    [
        ("abet_sis_med_dev", None),
        ("abet_prueba_a_1", None),
        ("postgres", None),
        ("template1", None),
        ("abet_demo_Mayus", None),
        ("abet_demo_x WITH (FORCE); DROP DATABASE abet_sis_med_dev", None),
        ("abet_demo_x", "abet_app"),
        ("abet_demo_x", "postgres"),
    ],
    ids=[
        "base_de_la_mac",
        "base_de_correr_pruebas",
        "postgres",
        "template1",
        "mayusculas",
        "sentencia_escondida",
        "rol_de_la_aplicacion",
        "rol_postgres",
    ],
)
def test_borrar_no_toca_un_nombre_que_no_es_desechable(
    modulo_base_desechable: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    nombre: str,
    rol_app: str | None,
) -> None:
    ordenes = _sin_servidor(monkeypatch, tmp_path)
    ajena = modulo_base_desechable.BaseDesechable(nombre=nombre, conexion="", rol_app=rol_app, conexion_app=None)
    with pytest.raises(ValueError, match="abet_demo_"):
        modulo_base_desechable.borrar(ajena)
    assert ordenes == []


@pytest.mark.parametrize(
    "sufijo",
    ["Mayus", "con espacio", "otra;base", "", "x" * 41, "x TEMPLATE abet_sis_med_dev"],
    ids=["mayusculas", "espacio", "punto_y_coma", "vacio", "41_caracteres", "sentencia_escondida"],
)
def test_crear_no_acepta_un_sufijo_que_no_es_un_identificador_simple(
    modulo_base_desechable: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sufijo: str
) -> None:
    ordenes = _sin_servidor(monkeypatch, tmp_path)
    with pytest.raises(ValueError, match="sufijo"):
        modulo_base_desechable.crear(sufijo)
    assert ordenes == []


def test_sin_un_cluster_desechable_borrar_no_corre_ninguna_orden(
    modulo_base_desechable: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Un nombre desechable pasa la guardia de nombres, pero las variables de libpq no nombran el
    # clúster desechable, así que _entorno() lo detiene antes de la ejecución falsa.
    ordenes = _sin_servidor(monkeypatch, tmp_path)
    desechable = modulo_base_desechable.BaseDesechable(
        nombre="abet_demo_x", conexion="", rol_app="abet_demo_app_x", conexion_app=None
    )
    with pytest.raises(RuntimeError, match="clúster desechable"):
        modulo_base_desechable.borrar(desechable)
    assert ordenes == []


def test_migraciones_sigue_el_orden_de_version_y_despues_las_repetibles(
    modulo_base_desechable: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # El orden de sort -t_ -k1,1V -k2,2n de db/pruebas/correr_pruebas.sh, en el que V1_9 va antes que
    # V1_10, y las repetibles en orden alfabético después de todas las versionadas.
    for nombre in ("V1_10__d.sql", "R__z.sql", "V1_9__c.sql", "V2_01__e.sql", "R__a.sql", "V1_01__a.sql", "notas.sql"):
        (tmp_path / nombre).write_text("SELECT 1;\n", encoding="utf-8")
    monkeypatch.setattr(modulo_base_desechable, "MIGRACIONES", tmp_path)
    assert [ruta.name for ruta in modulo_base_desechable.migraciones()] == [
        "V1_01__a.sql",
        "V1_9__c.sql",
        "V1_10__d.sql",
        "V2_01__e.sql",
        "R__a.sql",
        "R__z.sql",
    ]


def test_exigir_sin_restos_falla_mientras_queda_una_base_o_un_rol_desechable(base_desechable: ModuleType) -> None:
    # La fixture base_desechable de tests/conftest.py llama a exigir_sin_restos() al cerrar la sesión.
    rol = f"abet_demo_app_resto_{os.getpid()}_{secrets.token_hex(3)}"
    with base_desechable.abierta(rol_app=False, datos_2026_2=False) as base:
        with pytest.raises(base_desechable.ErrorDeBase, match=base.nombre):
            base_desechable.exigir_sin_restos()
        with psycopg.connect(base.conexion, autocommit=True) as conexion:
            conexion.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(rol)))
    try:
        # La base ya no existe, y el rol suelto basta para que falle.
        with pytest.raises(base_desechable.ErrorDeBase, match=rol):
            base_desechable.exigir_sin_restos()
    finally:
        base_desechable.borrar(base_desechable.BaseDesechable(base.nombre, "", rol, None))
    base_desechable.exigir_sin_restos()


def test_los_motivos_y_efectos_de_la_base_son_los_de_modelos(base_demo: Any) -> None:
    with psycopg.connect(base_demo.conexion) as conexion:
        definiciones = dict(
            conexion.execute(
                "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                "WHERE conname IN ('ck_rechazo_fila_motivo', 'ck_rechazo_fila_efecto')"
            ).fetchall()
        )
    assert set(re.findall(r"'([A-Z_]+)'", definiciones["ck_rechazo_fila_motivo"])) == {m.value for m in Motivo}
    assert set(re.findall(r"'([A-Z_]+)'", definiciones["ck_rechazo_fila_efecto"])) == {e.value for e in Efecto}


def test_una_prueba_que_pide_una_base_lleva_el_marcador_base(request: pytest.FixtureRequest, base_demo: Any) -> None:
    assert request.node.get_closest_marker("base") is not None


def test_una_prueba_que_no_pide_una_base_no_lleva_el_marcador(request: pytest.FixtureRequest) -> None:
    assert request.node.get_closest_marker("base") is None
