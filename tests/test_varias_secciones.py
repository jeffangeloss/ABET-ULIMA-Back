"""Profesor de varias secciones, los seis escenarios de varias_secciones.feature (corte 1).

Pedido de Jefferson del 2026-10-28, «él solo puede cargar el export de su sección que le
corresponde en el lugar donde le corresponde». Cada prueba nombra el escenario y las reglas de
negocio (business rules, BR) BR-ACCESO-07, BR-ACCESO-08, BR-CARGA-09 o BR-CARGA-11 que comprueba,
con lo que debe pasar y lo que no debe pasar (AGENTS.md, regla 8). Las pruebas quedan al nivel de
app/permisos.py, de abet_carga y del comando python -m abet_carga, porque las rutas de la interfaz
llegan con T036 a T038. Cada una corre en una base desechable con periodo_2026_2_inventado.sql y
varias_secciones_2026_2_inventado.sql, y la carga va con SET ROLE al rol de la aplicación.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import psycopg
import pytest
from psycopg import sql

from abet_carga import constancia
from abet_carga.__main__ import main
from abet_carga.carga import Configuracion, Resultado, cargar
from app import permisos

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "tests" / "datos_inventados"
VARIAS_SQL = RAIZ / "db" / "datos" / "varias_secciones_2026_2_inventado.sql"
EXPORTS = {
    ("450002", "412"): "sintetico_20262_450002_412.xlsx",
    ("450010", "410"): "sintetico_20262_450010_410.xlsx",
    ("450010", "412"): "sintetico_20262_450010_412.xlsx",
}
VARIAS = "docente.varias@example.invalid"
CONFIGURACION = Configuracion(conjunto_reglas="R-2026-BORRADOR")
TABLAS = ("archivo_origen", "carga", "rechazo_fila", "estudiante")
FALTA = [ruta for ruta in [VARIAS_SQL, *(DATOS / nombre for nombre in EXPORTS.values())] if not ruta.exists()]
pytestmark = pytest.mark.skipif(bool(FALTA), reason=f"Faltan los datos del flujo de varias secciones: {FALTA}")


@pytest.fixture
def base(crear_base_demo: Callable[..., Any]) -> Any:
    return crear_base_demo(despues=(VARIAS_SQL,))


@pytest.fixture
def conexion(base: Any) -> Iterator[psycopg.Connection]:
    with psycopg.connect(base.conexion, autocommit=True) as conexion:
        conexion.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(base.rol_app)))
        yield conexion


def _seccion(conexion: psycopg.Connection, asignatura: str, numero: str) -> int:
    fila = conexion.execute(
        "SELECT s.seccion_id FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
        " JOIN abet.periodo p USING (periodo_id) WHERE a.codigo = %s AND s.numero = %s AND p.codigo = '2026-2'",
        (asignatura, numero),
    ).fetchone()
    assert fila is not None
    return int(fila[0])


def _usuario(conexion: psycopg.Connection, correo: str = VARIAS) -> int:
    fila = conexion.execute("SELECT usuario_id FROM acceso.usuario_autorizado WHERE correo = %s", (correo,)).fetchone()
    assert fila is not None
    return int(fila[0])


def _subir(conexion: psycopg.Connection, nombre: str, asignatura: str, numero: str, correo: str = VARIAS) -> Any:
    seccion_id, usuario_id = _seccion(conexion, asignatura, numero), _usuario(conexion, correo)
    assert permisos.puede_subir(conexion, usuario_id, seccion_id)
    return cargar(conexion, (DATOS / nombre).read_bytes(), nombre_archivo=nombre, seccion_id=seccion_id,
                  usuario_id=usuario_id, configuracion=CONFIGURACION)


def _cargas(conexion: psycopg.Connection, asignatura: str, numero: str) -> list[str]:
    filas = conexion.execute("SELECT estado FROM abet.carga WHERE seccion_id = %s ORDER BY carga_id",
                             (_seccion(conexion, asignatura, numero),)).fetchall()
    return [estado for (estado,) in filas]


def _conteos(conexion: psycopg.Connection) -> dict[str, int]:
    return {t: conexion.execute(f"SELECT count(*) FROM abet.{t}").fetchone()[0] for t in TABLAS}


def _codigos(conexion: psycopg.Connection) -> set[str]:
    return {codigo for (codigo,) in conexion.execute("SELECT codigo FROM abet.estudiante").fetchall()}


def _rango(desde: int, hasta: int) -> set[str]:
    return {str(codigo) for codigo in range(desde, hasta + 1)}


# Escenario 1. El profesor de varias secciones ve sus tres secciones y ninguna otra (BR-ACCESO-07).

def test_br_acceso_07_el_profesor_de_varias_secciones_ve_sus_tres_secciones_y_ninguna_otra(
    conexion: psycopg.Connection,
) -> None:
    vistas = permisos.secciones_visibles(conexion, _usuario(conexion), "2026-2")
    assert sorted((s.asignatura, s.numero, s.asignatura_nombre) for s in vistas) == [
        ("450002", "412", "Principios de Ingeniería Sostenible"),
        ("450010", "410", "Gestión Sostenible de Residuos"),
        ("450010", "412", "Gestión Sostenible de Residuos"),
    ]
    ids = {s.seccion_id for s in vistas}
    assert len(ids) == 3
    assert _seccion(conexion, "450002", "412") != _seccion(conexion, "450010", "412")
    assert ids.isdisjoint({_seccion(conexion, "450002", "410"), _seccion(conexion, "450002", "411")})


# Escenario 2. Cada export del profesor se publica solo en su sección (BR-CARGA-03 y BR-CARGA-11).

@pytest.mark.parametrize(
    ("asignatura", "numero", "pis", "desde", "hasta"),
    [("450002", "412", ["5.1", "5.2", "5.3"], 99000023, 99000033),
     ("450010", "410", ["2.1", "2.2", "5.1"], 99000034, 99000044),
     ("450010", "412", ["2.1", "2.2", "5.1"], 99000045, 99000055)],
)
def test_br_carga_11_cada_export_del_profesor_de_varias_secciones_se_publica_solo_en_su_seccion(
    conexion: psycopg.Connection, asignatura: str, numero: str, pis: list[str], desde: int, hasta: int
) -> None:
    nombre = EXPORTS[(asignatura, numero)]
    resultado = _subir(conexion, nombre, asignatura, numero)
    assert (resultado.resultado, resultado.codigo_http) == (Resultado.PUBLICADA, 201)
    cuerpo = constancia.armar(conexion, resultado.carga_id)
    assert (cuerpo["filas_leidas"], cuerpo["filas_aceptadas"], cuerpo["filas_rechazadas"]) == (11, 11, 0)
    assert (cuerpo["nombre_archivo"], cuerpo["hoja"], cuerpo["filas_de_datos"]) == (
        nombre, f"gc_SINTETICO_20262_{asignatura}_{numero}_f", 11)
    assert cuerpo["subida_por"] == VARIAS
    assert [columna["pi"] for columna in cuerpo["columnas"]] == pis
    medidas = conexion.execute("SELECT count(*) FROM abet.medicion WHERE carga_id = %s", (resultado.carga_id,))
    assert medidas.fetchone() == (33,)
    assert _codigos(conexion) == _rango(desde, hasta)
    assert _cargas(conexion, asignatura, numero) == ["PUBLICADA"]
    otras = [clave for clave in [*EXPORTS, ("450002", "410"), ("450002", "411")] if clave != (asignatura, numero)]
    assert all(_cargas(conexion, *clave) == [] for clave in otras)
    visibles = permisos.secciones_visibles(conexion, _usuario(conexion), "2026-2")
    assert len(visibles) == 3


# Escenario 3. El export de una sección no entra en otra sección de la misma asignatura (BR-CARGA-11).

def test_br_carga_11_el_export_de_la_410_de_450010_se_rechaza_en_la_412_de_450010(
    conexion: psycopg.Connection,
) -> None:
    resultado = _subir(conexion, EXPORTS[("450010", "410")], "450010", "412")
    assert (resultado.resultado, resultado.codigo_http) == (Resultado.RECHAZADA, 201)
    assert resultado.mensaje == "El archivo corresponde a la sección 410 y usted eligió la 412. No se publicó."
    cuerpo = constancia.armar(conexion, resultado.carga_id)
    assert (cuerpo["hoja"], cuerpo["filas_leidas"], cuerpo["filas_aceptadas"]) == (
        "gc_SINTETICO_20262_450010_410_f", 0, 0)
    assert [(r["motivo"], r["efecto"], r["fila"]) for r in cuerpo["rechazos"]] == [
        ("SECCION_NO_COINCIDE", "RECHAZA_CARGA", None)]
    assert cuerpo["columnas"] == []
    assert _cargas(conexion, "450010", "412") == ["RECHAZADA"]
    assert _cargas(conexion, "450010", "410") == []
    assert _codigos(conexion).isdisjoint(_rango(99000034, 99000044))


# Escenario 4. El mismo número de sección en otra asignatura no basta (BR-CARGA-11).

def test_br_carga_11_el_export_de_la_412_de_450010_se_rechaza_en_la_412_de_450002_por_la_asignatura(
    conexion: psycopg.Connection,
) -> None:
    resultado = _subir(conexion, EXPORTS[("450010", "412")], "450002", "412")
    assert (resultado.resultado, resultado.codigo_http) == (Resultado.RECHAZADA, 201)
    assert resultado.mensaje == ("El archivo corresponde a la asignatura 450010 y usted eligió la 450002. "
                                 "No se publicó.")
    cuerpo = constancia.armar(conexion, resultado.carga_id)
    assert cuerpo["hoja"] == "gc_SINTETICO_20262_450010_412_f"
    assert [(r["motivo"], r["efecto"], r["fila"]) for r in cuerpo["rechazos"]] == [
        ("SECCION_NO_COINCIDE", "RECHAZA_CARGA", None)]
    assert _cargas(conexion, "450002", "412") == ["RECHAZADA"]
    assert _cargas(conexion, "450010", "412") == []
    assert _codigos(conexion).isdisjoint(_rango(99000045, 99000055))


# Escenario 5. El profesor no alcanza una sección que no dicta (BR-ACCESO-08).

def test_br_acceso_08_el_profesor_de_varias_secciones_no_alcanza_la_410_de_450002(
    base: Any, conexion: psycopg.Connection, capsys: pytest.CaptureFixture[str], tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CONJUNTO_REGLAS", "R-2026-BORRADOR")
    ajena = _subir(conexion, "sintetico_20262_450002_410.xlsx", "450002", "410", "docente410@example.invalid")
    assert ajena.resultado is Resultado.PUBLICADA
    seccion_410 = _seccion(conexion, "450002", "410")
    assert not permisos.puede_subir(conexion, _usuario(conexion), seccion_410)
    assert not permisos.puede_leer(conexion, _usuario(conexion), seccion_410)
    antes = _conteos(conexion)
    comun = ["--correo", VARIAS, "--base", base.conexion, "--rol", base.rol_app]
    intentos = [
        ["cargar", str(DATOS / EXPORTS[("450002", "412")]), "--asignatura", "450002", "--seccion", "410",
         "--periodo", "2026-2", *comun],
        ["cargar", str(DATOS / "sintetico_20262_450002_410.xlsx"), "--asignatura", "450002", "--seccion", "410",
         "--periodo", "2026-2", *comun],
        ["r17", "--carga", str(ajena.carga_id), "--carpeta", str(tmp_path), *comun],
    ]
    for intento in intentos:
        assert main(intento) != 0
        salida = capsys.readouterr()
        assert (salida.out + salida.err).strip() == permisos.SIN_ALCANCE
    assert _conteos(conexion) == antes
    assert list(tmp_path.iterdir()) == []


# Escenario 6. Un archivo publicado en una sección del profesor se detiene en otra (BR-CARGA-09).

def test_br_carga_09_el_export_publicado_en_la_412_de_450002_se_detiene_en_la_410_de_450010(
    conexion: psycopg.Connection,
) -> None:
    nombre = EXPORTS[("450002", "412")]
    publicada = _subir(conexion, nombre, "450002", "412")
    assert publicada.resultado is Resultado.PUBLICADA
    antes = _conteos(conexion)
    otra = _subir(conexion, nombre, "450010", "410")
    assert (otra.resultado, otra.codigo_http, otra.carga_id) == (Resultado.EN_OTRA_SECCION, 409, None)
    assert otra.mensaje == "Este archivo ya está publicado en otra sección. No se cargó."
    huella = hashlib.sha256((DATOS / nombre).read_bytes()).hexdigest()
    assert not any(dato in otra.mensaje for dato in (str(publicada.carga_id), huella, "412", "450002"))
    assert _conteos(conexion) == antes
    assert _cargas(conexion, "450010", "410") == []
    assert _cargas(conexion, "450002", "412") == ["PUBLICADA"]
    medidas = conexion.execute("SELECT count(*) FROM abet.medicion WHERE carga_id = %s", (publicada.carga_id,))
    assert medidas.fetchone() == (33,)
