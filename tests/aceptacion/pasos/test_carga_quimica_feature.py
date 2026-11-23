"""Pasos de carga_quimica.feature (US-75 a US-77 de la spec 008), con pytest-bdd en español (T024).

El .feature manda. Los Antecedentes arman la base de la spec 008 con el plan de 5643 en 2026-1 y los datos inventados
de Química General, en el clúster desechable de tests/cluster_desechable.py y nunca en localhost:5432. Aquí está Q21,
la consulta de control que llega con los datos inventados (T024). Los escenarios de la subida, de los errores
probables y de los consejos de P4 llegan con T034, T035 y T044.
"""

from __future__ import annotations

from typing import Any

from pytest_bdd import given, parsers, scenario, then

Escenario = Any
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/carga_quimica.feature"


@scenario(FEATURE, "Q21 detecta una sección cuyo curso de Blackboard declara otra sección")
def test_q21_detecta_una_seccion_cuyo_curso_declara_otra() -> None:
    """T024."""


@given(parsers.re(r'la sección (?P<numero>[0-9]+) de (?P<asignatura>[0-9]+) en (?P<periodo>[0-9]{4}-[0-9]) con el '
                  r'curso_blackboard "(?P<curso>[^"]+)"'))
def _curso_de_otra_seccion(ctx: Escenario, numero: str, asignatura: str, periodo: str, curso: str) -> None:
    # El curso es único (uq_seccion_curso_bb), así que la sección dueña del curso queda sin él antes del cambio.
    ctx.api.dueno.execute("UPDATE abet.seccion SET curso_blackboard = NULL WHERE curso_blackboard = %s", (curso,))
    cambiadas = ctx.api.dueno.execute(
        "UPDATE abet.seccion s SET curso_blackboard = %s FROM abet.asignatura a, abet.periodo pe"
        " WHERE a.asignatura_id = s.asignatura_id AND pe.periodo_id = s.periodo_id AND s.numero = %s"
        " AND a.codigo = %s AND pe.codigo = %s", (curso, numero, asignatura, periodo)).rowcount
    assert cambiadas == 1


@then(parsers.re(r'devuelve 1 fila que nombra la sección (?P<numero>[0-9]+) de (?P<asignatura>[0-9]+) en '
                 r'(?P<periodo>[0-9]{4}-[0-9])'))
def _q21_una_fila(ctx: Escenario, numero: str, asignatura: str, periodo: str) -> None:
    filas = ctx.extras["control"]
    assert [tuple(fila[1:]) for fila in filas] == [(numero, asignatura, periodo)]
    assert "@" not in repr(filas)
