"""Pruebas de V1_11, del guion de la descripción del instrumento y de su consulta informativa (BR-R17-11).

V1_11 agrega abet.plan_medicion.descripcion_instrumento varchar(400) nula con ck_plan_medicion_descripcion,
que exige al menos un carácter visible y ningún blanco a los lados. Blanco es todo carácter para el que
str.isspace() de Python es verdadero, la misma definición de str.strip() en el Back, así que la lista de
blancos de estas pruebas sale de Python y no se copia de la migración. abet_app lee la columna y no la escribe.

db/datos/descripcion_instrumento_2026_2.sql carga un texto de prueba distinto en cada PI de 450002 en 2026-2 y
se puede correr dos veces con el mismo resultado. db/plataforma/neon/pi_sin_descripcion_instrumento.sql lista
en solo lectura los PI del plan de un periodo sin descripción. Las bases son desechables (tests/base_desechable.py)
en el clúster desechable de tests/cluster_desechable.py, nunca en localhost:5432.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
import pytest
from psycopg import errors

RAIZ = Path(__file__).resolve().parent.parent
GUION = RAIZ / "db" / "datos" / "descripcion_instrumento_2026_2.sql"
CONSULTA = RAIZ / "db" / "plataforma" / "neon" / "pi_sin_descripcion_instrumento.sql"
BLANCOS = [chr(punto) for punto in range(0x110000) if chr(punto).isspace()]
PIS = ("5.1", "5.2", "5.3")
FIJAR = (
    "UPDATE abet.plan_medicion pm SET descripcion_instrumento = %s FROM abet.pi p, abet.asignatura a, abet.periodo pe "
    "WHERE p.pi_id = pm.pi_id AND a.asignatura_id = pm.asignatura_id AND pe.periodo_id = pm.periodo_id "
    "AND p.codigo = %s AND a.codigo = '450002' AND pe.codigo = '2026-2'"
)
DESCRIPCIONES = (
    "SELECT p.codigo, pm.descripcion_instrumento FROM abet.plan_medicion pm JOIN abet.pi p ON p.pi_id = pm.pi_id "
    "JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id "
    "WHERE a.codigo = '450002' AND pe.codigo = '2026-2' ORDER BY p.numero"
)


@pytest.fixture(scope="module")
def base(base_desechable: ModuleType) -> Iterator[Any]:
    with base_desechable.abierta() as base:
        yield base


@pytest.fixture
def dueno(base: Any) -> Iterator[psycopg.Connection]:
    """Conexión del dueño en una transacción que se deshace al terminar, así que ninguna prueba deja filas."""
    with psycopg.connect(base.conexion) as conexion:
        yield conexion
        conexion.rollback()


def _fijar(conexion: psycopg.Connection, texto: str | None, pi: str = "5.1") -> None:
    with conexion.transaction():
        cambiadas = conexion.execute(FIJAR, (texto, pi)).rowcount
    assert cambiadas == 1


def _psql(base_desechable: ModuleType, base: Any, archivo: Path, *argumentos: str) -> str:
    return base_desechable._psql(base.nombre, *argumentos, "-f", str(archivo))


# V1_11 y ck_plan_medicion_descripcion

def test_br_r17_11_la_definicion_de_blanco_de_python_tiene_29_caracteres() -> None:
    assert len(BLANCOS) == 29
    assert "".join(BLANCOS).strip() == ""


def test_br_r17_11_la_columna_es_varchar_400_nula(base: Any) -> None:
    with psycopg.connect(base.conexion) as conexion:
        fila = conexion.execute(
            "SELECT data_type, character_maximum_length, is_nullable FROM information_schema.columns "
            "WHERE table_schema = 'abet' AND table_name = 'plan_medicion' AND column_name = 'descripcion_instrumento'"
        ).fetchone()
    assert fila == ("character varying", 400, "YES")


def test_br_r17_11_los_datos_inventados_dejan_la_descripcion_nula(base: Any) -> None:
    with psycopg.connect(base.conexion) as conexion:
        assert conexion.execute(DESCRIPCIONES).fetchall() == [(pi, None) for pi in PIS]


@pytest.mark.parametrize("texto", ["Texto de prueba. Informe.", "a", "Texto de prueba.\nCon dos líneas.",
                                   "Texto  de prueba.", "x" * 400, None])
def test_br_r17_11_la_base_acepta_una_descripcion_bien_formada_o_nula(dueno: psycopg.Connection,
                                                                      texto: str | None) -> None:
    _fijar(dueno, texto)
    assert dict(dueno.execute(DESCRIPCIONES).fetchall())["5.1"] == texto


@pytest.mark.parametrize("texto", ["", "   ", "\t\n"], ids=["vacia", "tres_espacios", "tab_y_salto"])
def test_br_r17_11_la_base_rechaza_una_descripcion_sin_caracteres_visibles(dueno: psycopg.Connection,
                                                                           texto: str) -> None:
    with pytest.raises(errors.CheckViolation) as falla:
        _fijar(dueno, texto)
    assert falla.value.diag.constraint_name == "ck_plan_medicion_descripcion"


@pytest.mark.parametrize("blanco", BLANCOS, ids=[f"U+{ord(b):04X}" for b in BLANCOS])
@pytest.mark.parametrize("lado", ["comienzo", "final"])
def test_br_r17_11_la_base_rechaza_cada_blanco_del_back_a_los_lados(dueno: psycopg.Connection, blanco: str,
                                                                    lado: str) -> None:
    texto = blanco + "Texto de prueba." if lado == "comienzo" else "Texto de prueba." + blanco
    with pytest.raises(errors.CheckViolation) as falla:
        _fijar(dueno, texto)
    assert falla.value.diag.constraint_name == "ck_plan_medicion_descripcion"


@pytest.mark.parametrize("blanco", BLANCOS, ids=[f"U+{ord(b):04X}" for b in BLANCOS])
def test_br_r17_11_la_base_acepta_cada_blanco_del_back_entre_palabras(dueno: psycopg.Connection,
                                                                      blanco: str) -> None:
    _fijar(dueno, f"Texto{blanco}de prueba.")


def test_br_r17_11_la_base_rechaza_401_caracteres_por_el_largo_de_la_columna(dueno: psycopg.Connection) -> None:
    with pytest.raises(errors.StringDataRightTruncation):
        _fijar(dueno, "x" * 401)


def test_br_r17_11_abet_app_lee_la_columna_y_no_la_escribe(base: Any) -> None:
    with psycopg.connect(base.conexion) as conexion:
        lee, escribe = conexion.execute(
            "SELECT has_column_privilege(%s, 'abet.plan_medicion', 'descripcion_instrumento', 'SELECT'), "
            "has_column_privilege(%s, 'abet.plan_medicion', 'descripcion_instrumento', 'UPDATE')",
            (base.rol_app, base.rol_app)).fetchone()
    assert (lee, escribe) == (True, False)
    with psycopg.connect(base.conexion_app) as app, pytest.raises(errors.InsufficientPrivilege):
        app.execute(FIJAR, ("Texto de prueba. Desde la aplicación.", "5.1"))


# Guion de datos y consulta informativa

def test_br_r17_11_el_guion_deja_tres_textos_de_prueba_distintos_y_se_puede_repetir(
    base_desechable: ModuleType, crear_base_demo: Any,
) -> None:
    base = crear_base_demo()
    _psql(base_desechable, base, GUION)
    with psycopg.connect(base.conexion) as conexion:
        primera = conexion.execute(DESCRIPCIONES).fetchall()
    _psql(base_desechable, base, GUION)
    with psycopg.connect(base.conexion) as conexion:
        segunda = conexion.execute(DESCRIPCIONES).fetchall()
        otras = conexion.execute(
            "SELECT count(*) FROM abet.plan_medicion WHERE descripcion_instrumento IS NOT NULL").fetchone()[0]
    assert primera == segunda
    assert [pi for pi, _ in primera] == list(PIS)
    textos = [texto for _, texto in primera]
    assert all(texto.startswith("Texto de prueba.") and len(texto) <= 400 for texto in textos)
    assert len(set(textos)) == 3
    assert otras == 3


def test_br_r17_11_el_guion_no_escribe_nada_si_falta_un_pi_del_plan(
    base_desechable: ModuleType, crear_base_demo: Any,
) -> None:
    base = crear_base_demo()
    with psycopg.connect(base.conexion) as conexion:
        conexion.execute(
            "DELETE FROM abet.plan_medicion pm USING abet.pi p WHERE p.pi_id = pm.pi_id AND p.codigo = '5.3'")
    with pytest.raises(base_desechable.ErrorDeBase, match=r"no tiene los PI 5\.1, 5\.2 y 5\.3 .*\(2 de 3\)"):
        _psql(base_desechable, base, GUION)
    with psycopg.connect(base.conexion) as conexion:
        assert conexion.execute(
            "SELECT count(*) FROM abet.plan_medicion WHERE descripcion_instrumento IS NOT NULL").fetchone()[0] == 0


def test_br_r17_11_la_consulta_lista_los_pi_sin_descripcion_y_no_escribe(
    base_desechable: ModuleType, crear_base_demo: Any,
) -> None:
    base = crear_base_demo()
    antes = _psql(base_desechable, base, CONSULTA, "-v", "periodo=2026-2", "-A", "-t", "-F", "|")
    assert [linea for linea in antes.splitlines() if linea.startswith("450002|")] == [
        f"450002|{pi}|Trabajo Integrador" for pi in PIS]
    _psql(base_desechable, base, GUION)
    despues = _psql(base_desechable, base, CONSULTA, "-v", "periodo=2026-2", "-A", "-t", "-F", "|")
    assert not [linea for linea in despues.splitlines() if linea.startswith("450002|")]
    # La sesión pasa a solo lectura antes de la primera consulta, como revisar_antes_de_v1_10.sql.
    assert "SET default_transaction_read_only = on;" in CONSULTA.read_text()
    assert "on" in despues.splitlines()


def test_br_r17_11_la_consulta_exige_el_periodo(base_desechable: ModuleType, base: Any) -> None:
    with pytest.raises(base_desechable.ErrorDeBase, match="(?i)falta el periodo"):
        _psql(base_desechable, base, CONSULTA)
