"""Pruebas de app/permisos.py, el único dueño de BR-ACCESO-07 y BR-ACCESO-08 (parte de T037).

Cada prueba nombra la regla de negocio (business rule, BR) de specs/features/acceso/acceso.spec.md
que comprueba, con lo que debe pasar y lo que no debe pasar (AGENTS.md, regla 8). Las bases son
desechables, del clúster de tests/conftest.py, con los datos de periodo_2026_2_inventado.sql y de
varias_secciones_2026_2_inventado.sql. Cada consulta corre con la conexión del dueño de la base y
con SET ROLE al rol de la aplicación, que tiene el privilegio mínimo de Neon.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
import pytest
from psycopg import sql

from app import permisos

RAIZ = Path(__file__).resolve().parent.parent
VARIAS = RAIZ / "db" / "datos" / "varias_secciones_2026_2_inventado.sql"
DOCENTE_410 = "docente410@example.invalid"
DOCENTE_411 = "docente411@example.invalid"
VARIAS_CORREO = "docente.varias@example.invalid"
COORDINACION = "coordinacion@example.invalid"
PERIODO = "2026-2"
TODAS = {("450002", "410"), ("450002", "411"), ("450002", "412"), ("450010", "410"), ("450010", "412")}
DE_VARIAS = {("450002", "412"), ("450010", "410"), ("450010", "412")}


@pytest.fixture(scope="module")
def base(base_desechable: ModuleType) -> Iterator[Any]:
    if not VARIAS.exists():
        pytest.skip("Falta db/datos/varias_secciones_2026_2_inventado.sql, del flujo de varias secciones.")
    with base_desechable.abierta(despues=(VARIAS,)) as base:
        yield base


@pytest.fixture(params=["dueno", "rol_app"])
def conexion(request: pytest.FixtureRequest, base: Any) -> Iterator[psycopg.Connection]:
    with psycopg.connect(base.conexion, autocommit=True) as conexion:
        if request.param == "rol_app":
            conexion.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(base.rol_app)))
        yield conexion


@pytest.fixture
def dueno(base: Any) -> Iterator[psycopg.Connection]:
    with psycopg.connect(base.conexion, autocommit=True) as conexion:
        yield conexion


def _usuario(conexion: psycopg.Connection, correo: str) -> int:
    fila = conexion.execute("SELECT usuario_id FROM acceso.usuario_autorizado WHERE correo = %s", (correo,)).fetchone()
    assert fila is not None
    return int(fila[0])


def _secciones(conexion: psycopg.Connection) -> dict[tuple[str, str], int]:
    filas = conexion.execute(
        "SELECT a.codigo, s.numero, s.seccion_id FROM abet.seccion s"
        " JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id"
        " JOIN abet.periodo p ON p.periodo_id = s.periodo_id WHERE p.codigo = %s",
        (PERIODO,),
    ).fetchall()
    return {(asignatura, numero): seccion_id for asignatura, numero, seccion_id in filas}


def _vistas(conexion: psycopg.Connection, correo: str, periodo: str = PERIODO) -> set[tuple[str, str]]:
    return {(s.asignatura, s.numero) for s in permisos.secciones_visibles(conexion, _usuario(conexion, correo), periodo)}


@pytest.fixture
def inactivo(dueno: psycopg.Connection) -> Iterator[None]:
    """Da de baja a docente410 y a la coordinación mientras dura la prueba, y los repone al salir."""
    dueno.execute("UPDATE acceso.usuario_autorizado SET activo = false WHERE correo IN (%s, %s)",
                  (DOCENTE_410, COORDINACION))
    try:
        yield
    finally:
        dueno.execute("UPDATE acceso.usuario_autorizado SET activo = true WHERE correo IN (%s, %s)",
                      (DOCENTE_410, COORDINACION))


# BR-ACCESO-07: visibilidad por acceso.docente_seccion.

def test_br_acceso_07_el_profesor_ve_solo_la_seccion_que_docente_seccion_le_asigna(
    conexion: psycopg.Connection,
) -> None:
    assert _vistas(conexion, DOCENTE_410) == {("450002", "410")}
    assert _vistas(conexion, DOCENTE_411) == {("450002", "411")}


def test_br_acceso_07_el_profesor_de_varias_secciones_ve_sus_tres_y_ninguna_otra(
    conexion: psycopg.Connection,
) -> None:
    vistas = permisos.secciones_visibles(conexion, _usuario(conexion, VARIAS_CORREO), PERIODO)
    ids = _secciones(conexion)
    assert {(s.asignatura, s.numero) for s in vistas} == DE_VARIAS
    assert {s.seccion_id for s in vistas} == {ids[clave] for clave in DE_VARIAS}
    assert ids[("450002", "410")] not in {s.seccion_id for s in vistas}
    assert all(s.periodo == PERIODO for s in vistas)


def test_br_acceso_07_el_coordinador_ve_todas_las_secciones_de_la_carrera_sin_filas_propias(
    conexion: psycopg.Connection, dueno: psycopg.Connection
) -> None:
    filas = dueno.execute(
        "SELECT count(*) FROM acceso.docente_seccion d JOIN acceso.usuario_autorizado u USING (usuario_id)"
        " WHERE u.correo = %s", (COORDINACION,)
    ).fetchone()
    assert filas == (0,)
    assert _vistas(conexion, COORDINACION) == TODAS


def test_br_acceso_07_el_coordinador_no_ve_una_seccion_de_una_asignatura_fuera_del_catalogo(
    base: Any,
) -> None:
    with psycopg.connect(base.conexion) as conexion:
        conexion.execute("INSERT INTO abet.asignatura (codigo, nombre) VALUES ('9999', 'Asignatura ajena inventada')")
        conexion.execute(
            "INSERT INTO abet.seccion (periodo_id, asignatura_id, numero)"
            " SELECT p.periodo_id, a.asignatura_id, '410' FROM abet.periodo p, abet.asignatura a"
            " WHERE p.codigo = %s AND a.codigo = '9999'", (PERIODO,)
        )
        ajena = _secciones(conexion)[("9999", "410")]
        coordinacion = _usuario(conexion, COORDINACION)
        assert _vistas(conexion, COORDINACION) == TODAS
        assert not permisos.puede_leer(conexion, coordinacion, ajena)
        conexion.rollback()


def test_br_acceso_07_en_otro_periodo_nadie_ve_secciones_de_2026_2(conexion: psycopg.Connection) -> None:
    assert _vistas(conexion, VARIAS_CORREO, "2026-1") == set()
    assert _vistas(conexion, COORDINACION, "2026-1") == set()


@pytest.mark.usefixtures("inactivo")
def test_br_acceso_07_un_usuario_inactivo_no_ve_ninguna_seccion(conexion: psycopg.Connection) -> None:
    assert _vistas(conexion, DOCENTE_410) == set()
    assert _vistas(conexion, COORDINACION) == set()
    assert _vistas(conexion, DOCENTE_411) == {("450002", "411")}


def test_br_acceso_07_un_usuario_que_no_existe_no_ve_nada(conexion: psycopg.Connection) -> None:
    assert permisos.secciones_visibles(conexion, 2_000_000_000, PERIODO) == []


# BR-ACCESO-08: un solo 403 para lo que no está a cargo del usuario.

def test_br_acceso_08_el_mensaje_del_403_es_el_del_contrato() -> None:
    assert permisos.SIN_ALCANCE == "La sección no está a su cargo."


def test_br_acceso_08_el_profesor_sube_y_lee_solo_en_sus_secciones(conexion: psycopg.Connection) -> None:
    ids = _secciones(conexion)
    varias = _usuario(conexion, VARIAS_CORREO)
    for clave, seccion_id in ids.items():
        assert permisos.puede_subir(conexion, varias, seccion_id) is (clave in DE_VARIAS)
        assert permisos.puede_leer(conexion, varias, seccion_id) is (clave in DE_VARIAS)
    docente_410 = _usuario(conexion, DOCENTE_410)
    assert permisos.puede_subir(conexion, docente_410, ids[("450002", "410")])
    assert not permisos.puede_subir(conexion, docente_410, ids[("450002", "411")])
    assert not permisos.puede_leer(conexion, docente_410, ids[("450002", "412")])


def test_br_acceso_08_el_coordinador_lee_todas_y_no_sube_en_el_corte_1(conexion: psycopg.Connection) -> None:
    coordinacion = _usuario(conexion, COORDINACION)
    for seccion_id in _secciones(conexion).values():
        assert permisos.puede_leer(conexion, coordinacion, seccion_id)
        assert not permisos.puede_subir(conexion, coordinacion, seccion_id)


@pytest.mark.usefixtures("inactivo")
def test_br_acceso_08_un_usuario_inactivo_no_sube_ni_lee(conexion: psycopg.Connection) -> None:
    ids = _secciones(conexion)
    docente_410 = _usuario(conexion, DOCENTE_410)
    coordinacion = _usuario(conexion, COORDINACION)
    assert not permisos.puede_subir(conexion, docente_410, ids[("450002", "410")])
    assert not permisos.puede_leer(conexion, docente_410, ids[("450002", "410")])
    assert not permisos.puede_leer(conexion, coordinacion, ids[("450002", "410")])


def test_br_acceso_08_una_seccion_o_un_usuario_que_no_existen_no_dan_alcance(conexion: psycopg.Connection) -> None:
    ids = _secciones(conexion)
    assert not permisos.puede_subir(conexion, _usuario(conexion, DOCENTE_410), 2_000_000_000)
    assert not permisos.puede_leer(conexion, _usuario(conexion, COORDINACION), 2_000_000_000)
    assert not permisos.puede_subir(conexion, 2_000_000_000, ids[("450002", "410")])
    assert not permisos.puede_leer(conexion, 2_000_000_000, ids[("450002", "410")])


def test_br_acceso_08_las_consultas_no_dejan_una_transaccion_abierta(base: Any) -> None:
    """cargar() exige una conexión sin transacción abierta, y la ruta pregunta antes de cargar."""
    with psycopg.connect(base.conexion) as conexion:
        seccion_id = _secciones(conexion)[("450002", "410")]
        usuario_id = _usuario(conexion, DOCENTE_410)
        conexion.commit()
        assert permisos.puede_subir(conexion, usuario_id, seccion_id)
        assert conexion.info.transaction_status == psycopg.pq.TransactionStatus.IDLE
        assert permisos.puede_leer(conexion, usuario_id, seccion_id)
        assert conexion.info.transaction_status == psycopg.pq.TransactionStatus.IDLE
        assert permisos.secciones_visibles(conexion, usuario_id, PERIODO)
        assert conexion.info.transaction_status == psycopg.pq.TransactionStatus.IDLE
