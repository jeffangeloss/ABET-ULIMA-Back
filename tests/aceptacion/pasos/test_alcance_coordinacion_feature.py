"""Pasos de alcance_coordinacion.feature (US-70 a US-72 de la spec 008), con pytest-bdd en español (T023 y T024).

El .feature manda. Cada «Entonces» se comprueba contra la base desechable del escenario, sin dobles del sistema bajo
prueba. Los Antecedentes arman la base de la spec 008 con los datos de 2026-2 y los de Química General
(db/datos/quimica_2026_1_inventado.sql), en el clúster desechable de tests/cluster_desechable.py y nunca en
localhost:5432.

Cada escenario se ata con @scenario y el nombre de su tarea. Aquí están los de la base (T023 y T024). Los que piden
la API con el alcance nuevo, la sesión con el campo alcance o el guion de registro llegan con T030 a T032, y los de
pantalla los prueba Vitest en el Front.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import psycopg
from psycopg.conninfo import make_conninfo
from pytest_bdd import given, parsers, scenario, then, when

Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/alcance_coordinacion.feature"
PROBAR_ROL_APP = RAIZ / "db" / "pruebas" / "probar_rol_app.sql"
PRIVILEGIOS = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")


@scenario(FEATURE, "La base exige un solo alcance por fila")
def test_la_base_exige_un_solo_alcance_por_fila() -> None:
    """T023."""


@scenario(FEATURE, "El rol de la aplicación solo lee el alcance")
def test_el_rol_de_la_aplicacion_solo_lee_el_alcance() -> None:
    """T023."""


@scenario(FEATURE, "Q20 lista una coordinación de curso con una sección propia en acceso.docente_seccion")
def test_q20_lista_una_coordinacion_de_curso_con_una_seccion_propia() -> None:
    """T023."""


# Ayudas

def _id(ctx: Escenario, consulta: str, *parametros: object) -> int:
    return int(ctx.uno(consulta, *parametros))


def _ids(ctx: Escenario) -> dict[str, int]:
    return {
        "usuario": _id(ctx, "SELECT usuario_id FROM acceso.usuario_autorizado WHERE correo = 'coordinacion@example.invalid'"),
        "carrera": _id(ctx, "SELECT carrera_id FROM abet.carrera WHERE codigo = 'AMB'"),
        "asignatura": _id(ctx, "SELECT asignatura_id FROM abet.asignatura WHERE codigo = '5643'"),
        "periodo": _id(ctx, "SELECT periodo_id FROM abet.periodo WHERE codigo = '2026-1'"),
    }


# Cuando

@when(parsers.re(r'el dueño de la base inserta en acceso\.coordinacion_alcance una fila con (?P<valores>.+)'))
def _inserta_fila(ctx: Escenario, valores: str) -> None:
    i = _ids(ctx)
    filas = {
        'la carrera "AMB" y la asignatura 5643 a la vez': (i["usuario"], i["carrera"], i["asignatura"], i["periodo"]),
        "ni carrera ni asignatura": (i["usuario"], None, None, None),
        "la asignatura 5643 sin periodo": (i["usuario"], None, i["asignatura"], None),
        # La fila de AMB de coordinacion@example.invalid ya está desde los Antecedentes.
        'la carrera "AMB" repetida para el mismo usuario': (i["usuario"], i["carrera"], None, None),
    }
    assert valores in filas, f"valores sin regla: {valores}"
    ctx.antes = ctx.conteos()
    ctx.error_directo = None
    try:
        ctx.api.dueno.execute("INSERT INTO acceso.coordinacion_alcance (usuario_id, carrera_id, asignatura_id, periodo_id)"
                              " VALUES (%s, %s, %s, %s)", filas[valores])
    except psycopg.Error as falla:
        ctx.error_directo = falla


@when(parsers.re(r'abet_app inserta una fila en acceso\.coordinacion_alcance'))
def _rol_app_inserta(ctx: Escenario) -> None:
    conexion = make_conninfo(ctx.api.base.conexion, user=ctx.api.base.rol_app)
    ctx.directa = ctx.pila.enter_context(psycopg.connect(conexion, autocommit=True))
    assert ctx.directa.execute("SELECT current_user").fetchone()[0] == ctx.api.base.rol_app
    ctx.antes = ctx.conteos()
    usuario = _id(ctx, "SELECT usuario_id FROM acceso.usuario_autorizado WHERE correo = 'docente701@example.invalid'")
    ctx.intentar("INSERT INTO acceso.coordinacion_alcance (usuario_id, carrera_id)"
                 " SELECT %s, carrera_id FROM abet.carrera WHERE codigo = 'IND'", usuario)


@given(parsers.re(r'"(?P<correo>[^"]+)" asignado también a la (?P<numero>[0-9]+) en acceso\.docente_seccion'))
def _asignado_tambien(ctx: Escenario, correo: str, numero: str) -> None:
    ctx.api.dueno.execute(
        "INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)"
        " SELECT u.usuario_id, s.seccion_id FROM acceso.usuario_autorizado u, abet.seccion s"
        " JOIN abet.asignatura a USING (asignatura_id) JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
        " WHERE u.correo = %s AND s.numero = %s AND a.codigo = '5643' AND pe.codigo = '2026-1'", (correo, numero))


# Entonces

@then(parsers.re(r'PostgreSQL la rechaza con (?P<restriccion>[a-z_]+)'))
def _rechaza(ctx: Escenario, restriccion: str) -> None:
    assert ctx.error_directo is not None, "la base aceptó la fila"
    assert ctx.error_directo.diag.constraint_name == restriccion, ctx.error_directo.diag.message_primary
    ahora = ctx.conteos()
    assert ahora["acceso.coordinacion_alcance"] == ctx.antes["acceso.coordinacion_alcance"]


@then(parsers.re(r'PostgreSQL responde el SQLSTATE (?P<estado>[0-9A-Z]{5})'))
def _sqlstate(ctx: Escenario, estado: str) -> None:
    assert ctx.error_directo is not None, "el rol de la aplicación pudo insertar"
    assert ctx.error_directo.sqlstate == estado
    assert ctx.conteos()["acceso.coordinacion_alcance"] == ctx.antes["acceso.coordinacion_alcance"]


@then(parsers.re(r'db/pruebas/probar_rol_app\.sql lista SELECT como único privilegio de abet_app en esa tabla'))
def _solo_select(ctx: Escenario) -> None:
    rol = ctx.api.base.rol_app
    tiene = {privilegio for privilegio in PRIVILEGIOS if ctx.uno(
        "SELECT has_table_privilege(%s, 'acceso.coordinacion_alcance', %s)", rol, privilegio)}
    assert tiene == {"SELECT"}
    texto = PROBAR_ROL_APP.read_text(encoding="utf-8")
    assert "ok N09 el rol solo lee acceso.coordinacion_alcance" in texto
    # La lista de sentencias denegadas suma la escritura de la tabla de alcance.
    for sentencia in ("INSERT INTO acceso.coordinacion_alcance", "UPDATE acceso.coordinacion_alcance",
                      "DELETE FROM acceso.coordinacion_alcance", "TRUNCATE acceso.coordinacion_alcance"):
        assert sentencia in texto, sentencia


@then(parsers.re(r'devuelve 1 fila con su usuario_id y su rol, sin el correo'))
def _q20_una_fila(ctx: Escenario) -> None:
    usuario = _id(ctx, "SELECT usuario_id FROM acceso.usuario_autorizado"
                       " WHERE correo = 'coordinador.quimica@example.invalid'")
    filas = ctx.extras["control"]
    assert [tuple(fila) for fila in filas] == [(usuario, "COORDINADOR")]
    assert "@" not in repr(filas)
