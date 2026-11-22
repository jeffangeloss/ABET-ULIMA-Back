"""Pasos de secciones_sin_docente.feature (US-58 de la spec 006), con pytest-bdd en español (T020).

El .feature manda. La consulta db/plataforma/neon/secciones_sin_docente.sql corre con psql 18 del clúster
desechable, con -X -v ON_ERROR_STOP=1 y la salida sin alinear, por el usuario dueño de la copia del escenario,
nunca en localhost:5432. Los Antecedentes, que siembran la base de partida y corren el guion de la
programación docente con el archivo base, viven en el conftest.py de esta carpeta.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

Escenario = Any
scenarios("specs/006-programacion-docente/aceptacion/secciones_sin_docente.feature")

CP = sys.modules["cargas_de_prueba"]
RAIZ = Path(__file__).resolve().parents[3]
CONSULTA = RAIZ / "db" / "plataforma" / "neon" / "secciones_sin_docente.sql"
FILA = re.compile(r"(?P<asignatura>[0-9]{4}(?:[0-9]{2})?)\|(?P<numero>[1-9][0-9]{0,4})")


def _conteos(ctx: Escenario) -> dict[str, int]:
    """Número de filas de cada tabla de los esquemas abet y acceso."""
    tablas = ctx.filas("SELECT table_schema, table_name FROM information_schema.tables"
                       " WHERE table_schema IN ('abet', 'acceso') AND table_type = 'BASE TABLE'"
                       " ORDER BY table_schema, table_name")
    return {f"{esquema}.{tabla}": int(ctx.uno(f'SELECT count(*) FROM "{esquema}"."{tabla}"')) for esquema, tabla in tablas}


def _salida(ctx: Escenario) -> list[str]:
    corrida = ctx.extras.get("consulta_006")
    assert corrida is not None, "el escenario todavía no corrió la consulta"
    return corrida.stdout.splitlines()


@given(parsers.re(r'la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" en "(?P<periodo>[^"]+)" '
                  r'(?P<asignacion>sin ninguna asignación|asignada solo a "(?P<correo>[^"]+)"'
                  r'(?P<baja>, con rol "PROFESOR" y activo falso)?), sembrada por el dueño de la base'))
def _seccion_sembrada(ctx: Escenario, numero: str, asignatura: str, periodo: str, asignacion: str,
                      correo: str | None, baja: str | None) -> None:
    dueno = ctx.api.dueno
    dueno.execute("INSERT INTO abet.seccion (periodo_id, asignatura_id, numero) SELECT pe.periodo_id, a.asignatura_id, %s"
                  " FROM abet.periodo pe, abet.asignatura a WHERE pe.codigo = %s AND a.codigo = %s",
                  (numero, periodo, asignatura))
    # Sin esta comprobación, un INSERT que no encuentra la asignatura no insertaría nada y la cantidad final de 0
    # saldría igual, por una razón equivocada.
    assert ctx.uno("SELECT count(*) FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                   " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
                   " WHERE s.numero = %s AND a.codigo = %s AND pe.codigo = %s", numero, asignatura, periodo) == 1
    if correo is None:
        return
    if baja is not None:
        dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol, activo) VALUES (%s, 'PROFESOR', false)",
                      (correo,))
    dueno.execute(
        "INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) SELECT u.usuario_id, s.seccion_id"
        " FROM acceso.usuario_autorizado u, abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
        " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
        " WHERE u.correo = %s AND s.numero = %s AND a.codigo = %s AND pe.codigo = %s",
        (correo, numero, asignatura, periodo))
    asignados = ctx.filas("SELECT u.correo, u.rol, u.activo FROM acceso.docente_seccion d"
                          " JOIN acceso.usuario_autorizado u USING (usuario_id) JOIN abet.seccion s USING (seccion_id)"
                          " JOIN abet.asignatura a USING (asignatura_id) WHERE s.numero = %s AND a.codigo = %s",
                          numero, asignatura)
    esperado = ("PROFESOR", False) if baja else ("COORDINADOR", True)
    assert asignados == [(correo, *esperado)], asignados


@given(parsers.re(r'que la base no tiene plan de medición de "(?P<asignatura>[0-9]+)" en "(?P<periodo>[^"]+)"'))
def _sin_plan(ctx: Escenario, asignatura: str, periodo: str) -> None:
    # La base de partida no trae el plan de 450020, así que aquí el paso solo lo comprueba.
    assert ctx.uno("SELECT count(*) FROM abet.plan_medicion pm JOIN abet.asignatura a USING (asignatura_id)"
                   " JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id WHERE a.codigo = %s AND pe.codigo = %s",
                   asignatura, periodo) == 0


@when(parsers.re(r'corre la consulta (?:con -v periodo=(?P<periodo>[0-9]{4}-[0-9])|(?P<sin>sin -v periodo))'))
def _corre_la_consulta(ctx: Escenario, periodo: str | None, sin: str | None) -> None:
    ctx.extras["conteos_006"] = _conteos(ctx)
    orden = ["psql", "-X", "-A", "-t", "-F", "|", "-v", "ON_ERROR_STOP=1"]
    if periodo is not None:
        orden += ["-v", f"periodo={periodo}"]
    entorno = CP.entorno_de_programacion(ctx.api.base.nombre)
    ctx.extras["consulta_006"] = subprocess.run([*orden, "-f", str(CONSULTA)], env=entorno, capture_output=True,
                                                text=True, encoding="utf-8", check=False, timeout=60)


@then(parsers.re(r'la consulta lista la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" y ninguna sección de '
                 r'"(?P<otra>[0-9]+)"'))
def _lista(ctx: Escenario, numero: str, asignatura: str, otra: str) -> None:
    corrida = ctx.extras["consulta_006"]
    assert corrida.returncode == 0, corrida.stderr
    filas = [(m["asignatura"], m["numero"]) for linea in _salida(ctx) if (m := FILA.fullmatch(linea))]
    assert filas == [(asignatura, numero)], filas
    assert all(a != otra for a, _ in filas)


@then(parsers.re(r'la cantidad final es (?P<n>[0-9]+)'))
def _cantidad(ctx: Escenario, n: str) -> None:
    corrida = ctx.extras["consulta_006"]
    assert corrida.returncode == 0, corrida.stderr
    assert _salida(ctx)[-1] == n, _salida(ctx)


@then(parsers.re(r'la sesión de la consulta queda en solo lectura antes de la primera consulta'))
def _solo_lectura(ctx: Escenario) -> None:
    corrida = ctx.extras["consulta_006"]
    assert corrida.returncode == 0, corrida.stderr
    # Lo primero que escribe psql es el SET y el SHOW de default_transaction_read_only, antes de cualquier SELECT.
    assert _salida(ctx)[:2] == ["SET", "on"], _salida(ctx)
    # El único SELECT anterior es el del periodo que falta, sangrado dentro de su \if, que corta la corrida.
    texto = CONSULTA.read_text(encoding="utf-8")
    primera = re.search(r"^(?:SELECT|WITH)\b", texto, flags=re.MULTILINE)
    assert primera is not None
    assert 0 <= texto.index("\nSET default_transaction_read_only = on;\n") < primera.start()


@then(parsers.re(r'ninguna tabla de los esquemas abet y acceso cambia su número de filas'))
def _sin_filas_nuevas(ctx: Escenario) -> None:
    assert _conteos(ctx) == ctx.extras["conteos_006"]


@then(parsers.re(r'psql termina con un error antes de consultar'))
def _termina_con_error(ctx: Escenario) -> None:
    corrida = ctx.extras["consulta_006"]
    assert corrida.returncode != 0
    assert not any("Secciones del periodo" in linea for linea in _salida(ctx)), _salida(ctx)


@then(parsers.re(r'la salida dice «(?P<linea>[^»]+)»'))
def _salida_dice(ctx: Escenario, linea: str) -> None:
    assert linea in _salida(ctx), _salida(ctx)
