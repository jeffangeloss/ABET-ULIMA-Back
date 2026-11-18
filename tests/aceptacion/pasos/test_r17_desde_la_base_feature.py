"""Pasos de US-51 en r17_desde_la_base.feature (spec 005, BR-R17-11), ejecutables con pytest-bdd en español.

El .feature manda. Ningún paso cambia un texto para que el escenario pase, y cada «Entonces» se comprueba contra
la base o contra el libro descargado por la API, sin dobles del sistema bajo prueba. Este módulo enlaza solo los
cuatro escenarios de US-51 con @scenario, porque los de US-50 necesitan V1_12 y la declaración de US-49, que
llegan después (T037 y T038). Cuando lleguen, el módulo pasa a scenarios() sobre el archivo entero.

«El dueño de la base» usa la conexión del dueño de la copia desechable, la misma de las consultas de los pasos,
y nunca toca Neon. En Neon, la descripción la carga Jefferson desde el Windows con el guion (AD-20).
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import psycopg
from openpyxl import load_workbook
from pytest_bdd import given, parsers, scenario, then, when

Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/005-oportunidades-de-mejora/aceptacion/r17_desde_la_base.feature"
GUION = RAIZ / "db" / "datos" / "descripcion_instrumento_2026_2.sql"
HOJA = "Cursos de Carrera"
PIS = ("5.1", "5.2", "5.3")
CELDAS = {"5.1": "G17", "5.2": "G18", "5.3": "G19"}
DEL_PLAN = (
    "FROM abet.plan_medicion pm JOIN abet.pi p ON p.pi_id = pm.pi_id"
    " JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id"
    " WHERE a.codigo = %s AND pe.codigo = %s"
)
FIJAR = ("UPDATE abet.plan_medicion pm SET descripcion_instrumento = %s FROM abet.pi p, abet.asignatura a,"
         " abet.periodo pe WHERE p.pi_id = pm.pi_id AND a.asignatura_id = pm.asignatura_id"
         " AND pe.periodo_id = pm.periodo_id AND p.codigo = %s AND a.codigo = %s AND pe.codigo = %s")
TEXTOS = {
    '"   "': "   ",
    '" Texto de prueba." (blanco al comienzo)': " Texto de prueba.",
    '"Texto de prueba. " (blanco al final)': "Texto de prueba. ",
    "un texto de 401 caracteres": "x" * 401,
}


@scenario(FEATURE, "G17, G18 y G19 traen la descripción de cada PI")
def test_g17_g18_y_g19_traen_la_descripcion_de_cada_pi() -> None:
    """US-51, escenario 1."""


@scenario(FEATURE, "Sin descripción en la base, G17:I19 queda vacía")
def test_sin_descripcion_en_la_base_g17_i19_queda_vacia() -> None:
    """US-51, escenario 2."""


@scenario(FEATURE, "La base rechaza una descripción en blanco, con blancos a los lados o demasiado larga")
def test_la_base_rechaza_una_descripcion_mal_formada() -> None:
    """US-51, escenario 3, con sus cuatro Ejemplos."""


@scenario(FEATURE, "El guion de datos se corre dos veces y deja las mismas tres descripciones")
def test_el_guion_de_datos_se_corre_dos_veces() -> None:
    """US-51, escenario 4."""


# Ayudas

def _descripciones(ctx: Escenario, asignatura: str = "450002",
                   periodo: str = "2026-2") -> dict[str, str | None]:
    return dict(ctx.filas(f"SELECT p.codigo, pm.descripcion_instrumento {DEL_PLAN} ORDER BY p.numero",
                          asignatura, periodo))


def _hoja(ctx: Escenario) -> Any:
    if "hoja_r17" not in ctx.extras:
        assert ctx.respuesta.status_code == 200, ctx.respuesta.text[:300]
        ctx.extras["hoja_r17"] = load_workbook(io.BytesIO(ctx.respuesta.content))[HOJA]
    return ctx.extras["hoja_r17"]


# Antecedentes propios de este archivo

@given(parsers.re(r'acceso\.docente_seccion asigna la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" a '
                  r'"(?P<correo>[^"]+)"'))
def _asigna(ctx: Escenario, numero: str, asignatura: str, correo: str) -> None:
    assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion WHERE usuario_id = %s AND seccion_id = %s",
                   ctx.usuario_id(correo), ctx.seccion_id(numero, asignatura)) == 1


@given(parsers.re(r'"(?P<correo>[^"]+)" activo con rol "(?P<rol>[A-Z]+)" y sin secciones en acceso\.docente_seccion'))
def _sin_secciones(ctx: Escenario, correo: str, rol: str) -> None:
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, True)]
    assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion WHERE usuario_id = %s", ctx.usuario_id(correo)) == 0


@given(parsers.re(r'ninguna sección de (?P<periodo>[0-9]{4}-[0-2]) tiene cargas'))
def _sin_cargas(ctx: Escenario, periodo: str) -> None:
    assert ctx.uno("SELECT count(*) FROM abet.carga c JOIN abet.seccion s ON s.seccion_id = c.seccion_id"
                   " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id WHERE pe.codigo = %s", periodo) == 0


# Dado, la descripción en la base

@given(parsers.re(r'que el dueño de la base fija en abet\.plan_medicion de "(?P<asignatura>[0-9]+)" en '
                  r'"(?P<periodo>[^"]+)" una descripción distinta para 5\.1, 5\.2 y 5\.3, cada una «Texto de prueba\.» '
                  r'seguido del número de su PI'))
def _fija_descripciones(ctx: Escenario, asignatura: str, periodo: str) -> None:
    for pi in PIS:
        cambiadas = ctx.api.dueno.execute(FIJAR, (f"Texto de prueba. {pi}", pi, asignatura, periodo)).rowcount
        assert cambiadas == 1, pi
    ctx.extras["descripciones"] = _descripciones(ctx, asignatura, periodo)


@given(parsers.re(r'que abet\.plan_medicion de "(?P<asignatura>[0-9]+)" en "(?P<periodo>[^"]+)" no tiene '
                  r'descripcion_instrumento en ningún PI'))
def _sin_descripciones(ctx: Escenario, asignatura: str, periodo: str) -> None:
    assert _descripciones(ctx, asignatura, periodo) == {pi: None for pi in PIS}


@given(parsers.re(r'una conexión directa del dueño de la base'))
def _conexion_del_dueno(ctx: Escenario) -> None:
    ctx.directa = ctx.pila.enter_context(psycopg.connect(ctx.api.base.conexion, autocommit=True))
    assert ctx.directa.execute("SELECT current_user").fetchone()[0] != ctx.api.base.rol_app


# Cuando

@when(parsers.re(r'(?P<quien>"[^"]+") descarga el R-17 de esa carga'))
def _descarga_r17(ctx: Escenario, quien: str) -> None:
    assert ctx.carga_id is not None
    ctx.extras.pop("hoja_r17", None)
    ctx.respuesta = ctx.sesion(quien.strip('"')).get(f"/api/cargas/{ctx.carga_id}/r17.xlsx")


@when(parsers.re(r'esa conexión fija en abet\.plan_medicion la descripcion_instrumento (?P<texto>.+)'))
def _fija_mal_formada(ctx: Escenario, texto: str) -> None:
    assert texto in TEXTOS, f"el texto «{texto}» no tiene valor en este módulo"
    ctx.extras["anterior"] = _descripciones(ctx)["5.1"]
    ctx.intentar(FIJAR, TEXTOS[texto], "5.1", "450002", "2026-2")


@when(parsers.re(r'esa conexión corre dos veces db/datos/descripcion_instrumento_2026_2\.sql'))
def _corre_dos_veces(ctx: Escenario) -> None:
    corridas = []
    for _ in range(2):
        ctx.plantillas.base_desechable._psql(ctx.api.base.nombre, "-f", str(GUION))
        corridas.append(_descripciones(ctx))
    ctx.extras["corridas"] = corridas


# Entonces

@then(parsers.re(r'G17 trae el texto del PI 5\.1, G18 el del PI 5\.2 y G19 el del PI 5\.3'))
def _g_trae_cada_texto(ctx: Escenario) -> None:
    hoja, esperadas = _hoja(ctx), ctx.extras["descripciones"]
    assert [hoja[f"B{celda[1:]}"].value for celda in CELDAS.values()] == list(PIS)
    assert {pi: hoja[celda].value for pi, celda in CELDAS.items()} == esperadas
    assert all(hoja[celda].data_type == "s" for celda in CELDAS.values())


@then(parsers.re(r'los tres textos son distintos entre sí'))
def _distintos(ctx: Escenario) -> None:
    hoja = _hoja(ctx)
    textos = [hoja[celda].value for celda in CELDAS.values()]
    assert all(textos) and len(set(textos)) == 3


@then(parsers.re(r'G17, G18 y G19 están vacías'))
def _g_vacias(ctx: Escenario) -> None:
    hoja = _hoja(ctx)
    assert [hoja[f"{columna}{fila}"].value for fila in (17, 18, 19) for columna in "GHI"] == [None] * 9


@then(parsers.re(r'el R-17 no inventa ningún texto de descripción'))
def _no_inventa(ctx: Escenario) -> None:
    hoja = _hoja(ctx)
    textos = [str(celda.value) for fila in hoja.iter_rows() for celda in fila if celda.value is not None]
    assert not [texto for texto in textos if texto.startswith("Texto de prueba")]
    # El nombre del instrumento sigue en E y no se copia a G.
    assert [hoja[f"E{fila}"].value for fila in (17, 18, 19)] == ["Trabajo Integrador"] * 3


@then(parsers.re(r'la base rechaza el cambio por el largo de la columna'))
def _rechaza_por_largo(ctx: Escenario) -> None:
    assert ctx.error_directo is not None, "la base aceptó la sentencia"
    assert isinstance(ctx.error_directo, psycopg.errors.StringDataRightTruncation), type(ctx.error_directo)


@then(parsers.re(r'abet\.plan_medicion conserva su descripción anterior'))
def _conserva(ctx: Escenario) -> None:
    assert _descripciones(ctx)["5.1"] == ctx.extras["anterior"]


@then(parsers.re(r'abet\.plan_medicion de "(?P<asignatura>[0-9]+)" en "(?P<periodo>[^"]+)" tiene las mismas '
                 r'(?P<n>[0-9]+) descripciones tras la primera y tras la segunda corrida'))
def _mismas(ctx: Escenario, asignatura: str, periodo: str, n: str) -> None:
    primera, segunda = ctx.extras["corridas"]
    assert primera == segunda == _descripciones(ctx, asignatura, periodo)
    assert len([texto for texto in primera.values() if texto]) == int(n)
    assert all(texto.startswith("Texto de prueba.") for texto in primera.values())


@then(parsers.re(r'ninguna de las tres descripciones está repetida en otro PI'))
def _no_repetidas(ctx: Escenario) -> None:
    textos = list(ctx.extras["corridas"][-1].values())
    assert len(set(textos)) == 3
    assert ctx.uno("SELECT count(*) FROM abet.plan_medicion WHERE descripcion_instrumento IS NOT NULL") == 3
