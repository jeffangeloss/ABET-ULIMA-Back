"""Pasos de periodo_elegido.feature (US-73 de la spec 008), con pytest-bdd en español (T033).

El .feature manda. Cada «Entonces» se comprueba con la respuesta de la API y con la base desechable del escenario, sin
dobles del sistema bajo prueba. Los Antecedentes arman la base de la spec 008 con el plan de 5643 en 2026-1 y los
datos de 2026-2 y de Química General, en el clúster desechable de tests/cluster_desechable.py y nunca en
localhost:5432, y arrancan la API con PERIODO_VIGENTE 2026-2, como la versión de prueba.

Aquí están los escenarios del Back, la ruta 18 GET /api/periodos, el parámetro periodo de la ruta 8 y la subida en
2026-1. Los escenarios de pantalla llevan @delegado_a_vitest y los prueba Vitest en el Front.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

from pytest_bdd import given, parsers, scenario, then, when

Escenario = Any
A = sys.modules["api_de_prueba"]
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/periodo_elegido.feature"
EXPORT_410 = "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-36-02.xlsx"


@scenario(FEATURE, "La ruta 18 lista solo los periodos con secciones al alcance de cada cuenta")
def test_la_ruta_18_lista_los_periodos_al_alcance() -> None:
    """T033."""


@scenario(FEATURE, "Con secciones en los dos periodos los recibe del más reciente al más antiguo")
def test_con_dos_periodos_del_mas_reciente_al_mas_antiguo() -> None:
    """T033."""


@scenario(FEATURE, "Sin sesión la ruta 18 responde 401 y figura en la prueba de rutas registradas")
def test_sin_sesion_la_ruta_18_responde_401() -> None:
    """T033."""


@scenario(FEATURE, "La ruta 8 con periodo lista solo las cargas de ese periodo y sin periodo sigue como hoy")
def test_la_ruta_8_con_periodo() -> None:
    """T033."""


@scenario(FEATURE, "Un periodo mal formado responde 422 en las rutas que lo aceptan")
def test_un_periodo_mal_formado_responde_422() -> None:
    """T033."""


@scenario(FEATURE, "Un periodo sin secciones del usuario da una lista vacía y no un 403")
def test_un_periodo_sin_secciones_da_una_lista_vacia() -> None:
    """T033."""


@scenario(FEATURE, "Pedir otro periodo no agrega secciones ajenas")
def test_pedir_otro_periodo_no_agrega_secciones_ajenas() -> None:
    """T033."""


@scenario(FEATURE, "La subida en una sección de 2026-1 no exige el periodo vigente")
def test_la_subida_en_2026_1_no_exige_el_vigente() -> None:
    """T033."""


@scenario(FEATURE, "Un export de otro periodo se rechaza con el texto de la API")
def test_un_export_de_otro_periodo_se_rechaza() -> None:
    """T033."""


# Ayudas

def _rutas_registradas() -> Any:
    if "rutas_registradas" not in sys.modules:
        especificacion = importlib.util.spec_from_file_location("rutas_registradas", RAIZ / "tests" / "rutas_registradas.py")
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules["rutas_registradas"] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules["rutas_registradas"]


def _lista(texto: str) -> list[str]:
    return re.findall(r'"([^"]+)"', texto)


def _subir(ctx: Escenario, correo: str, numero: str, contenido: bytes, nombre: str, asignatura: str | None = None) -> Any:
    ctx.antes = ctx.conteos()
    respuesta = A.subir(ctx.sesion(correo), ctx.seccion_de(numero, asignatura), contenido, nombre)
    ctx.respuesta = respuesta
    cuerpo = respuesta.json()
    ctx.carga_id = cuerpo.get("carga_id") if isinstance(cuerpo, dict) else None
    return respuesta


def _ids_de_cargas(respuesta: Any) -> list[int]:
    assert respuesta.status_code == 200, respuesta.text
    return [fila["carga_id"] for fila in respuesta.json()]


# Dado

@given(parsers.re(r'la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "(?P<periodo>[^"]+)"'))
def _api_con_periodo(ctx: Escenario, periodo: str) -> None:
    ctx.configurar_api(periodo, A.REGLAS, "1")
    # Crear el cliente arranca la API, con su comprobación de la base.
    ctx.api.cliente()
    assert ctx.api.ajustes.periodo_vigente == periodo
    assert ctx.api.ajustes.database_url.find(f"user={ctx.api.base.rol_app}") >= 0


@given(parsers.re(r'que acceso\.docente_seccion también asigna a "(?P<correo>[^"]+)" la (?P<numero>[0-9]+) de '
                  r'"(?P<asignatura>[0-9]+)" en "(?P<periodo>[^"]+)"'))
def _tambien_asigna(ctx: Escenario, correo: str, numero: str, asignatura: str, periodo: str) -> None:
    ctx.api.dueno.execute("INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) VALUES (%s, %s)",
                          (ctx.usuario_id(correo), ctx.seccion_de(numero, asignatura, periodo)))


@given(parsers.re(r'una petición sin la cookie abet_sesion'))
def _sin_cookie(ctx: Escenario) -> None:
    ctx.extras["con_sesion"] = None


@given(parsers.re(r'la carga PUBLICADA inventada de la 701 y una carga RECHAZADA inventada de la 411'))
def _publicada_y_rechazada(ctx: Escenario) -> None:
    contenido, nombre = ctx.export_de_quimica("701")
    respuesta = _subir(ctx, "docente701@example.invalid", "701", contenido, nombre)
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "PUBLICADA", respuesta.text
    ctx.extras["carga_701"] = ctx.carga_id
    # El export de la 410 subido a la 411 declara otra sección, así que la carga queda RECHAZADA.
    respuesta = _subir(ctx, "docente411@example.invalid", "411", ctx.de_inventados(EXPORT_410), EXPORT_410)
    assert respuesta.json()["estado"] == "RECHAZADA", respuesta.text
    ctx.extras["carga_411"] = ctx.carga_id


# Cuando

@when(parsers.re(r'(?P<correos>"[^"]+"(?:, "[^"]+")* y "[^"]+") piden GET /api/periodos'))
def _piden_periodos(ctx: Escenario, correos: str) -> None:
    ctx.extras["periodos"] = {correo: ctx.sesion(correo).get("/api/periodos") for correo in _lista(correos)}


@when(parsers.re(r'pide GET (?P<ruta>/api/\S+)'))
def _pide(ctx: Escenario, ruta: str) -> None:
    ctx.pedir(ruta)


@when(parsers.re(r'sube a la (?P<numero>70[0-9]) un export inventado (?P<texto>de texto )?cuyo curso declara '
                 r'(?P<periodo>[0-9]{5}), 5643 y (?P=numero)'))
def _sube_a_la_701(ctx: Escenario, numero: str, texto: str | None, periodo: str) -> None:
    contenido, nombre = ctx.export_de_quimica(numero, periodo=periodo, texto=texto is not None)
    _subir(ctx, ctx.extras["con_sesion"], numero, contenido, nombre)


# Entonces

@then(parsers.re(r'"(?P<correo>[^"]+)" recibe vigente "(?P<vigente>[^"]+)" y periodos (?P<periodos>\[[^\]]*\])'))
def _recibe_periodos_de(ctx: Escenario, correo: str, vigente: str, periodos: str) -> None:
    respuesta = ctx.extras["periodos"][correo]
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json() == {"vigente": vigente, "periodos": _lista(periodos)}


@then(parsers.re(r'cada respuesta lleva Cache-Control no-store, como toda /api'))
def _no_store(ctx: Escenario) -> None:
    respuestas = ctx.extras["periodos"]
    assert len(respuestas) == 3
    for respuesta in respuestas.values():
        assert respuesta.headers["cache-control"] == "no-store"


@then(parsers.re(r'recibe periodos (?P<periodos>\[[^\]]*\])'))
def _recibe_periodos(ctx: Escenario, periodos: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    assert ctx.respuesta.json() == {"vigente": "2026-2", "periodos": _lista(periodos)}


@then(parsers.re(r'recibe 401 con «(?P<mensaje>[^»]+)» y sin datos'))
def _recibe_401(ctx: Escenario, mensaje: str) -> None:
    assert ctx.respuesta.status_code == 401, ctx.respuesta.text
    assert ctx.respuesta.json() == {"detail": mensaje}


@then(parsers.re(r'la ruta figura en tests/rutas_registradas\.py'))
def _figura(ctx: Escenario) -> None:
    rutas = _rutas_registradas()
    cliente = ctx.api.cliente()
    assert ("GET", "/api/periodos") in rutas.operaciones(cliente)
    assert ("GET", "/api/periodos") not in rutas.PUBLICAS
    # El recorrido de BR-ACCESO-10 la pide sin cookie y recibe el 401 único.
    sin_cookie = rutas.sin_cookie(cliente, {"seccion": 1, "carga": 1})
    assert sin_cookie[("GET", "/api/periodos")].status_code == 401
    assert sin_cookie[("GET", "/api/periodos")].json() == rutas.VENCIDA


@then(parsers.re(r'recibe la carga de la 701 y no la de la 411'))
def _solo_la_701(ctx: Escenario) -> None:
    assert _ids_de_cargas(ctx.respuesta) == [ctx.extras["carga_701"]]


@then(parsers.re(r'GET /api/cargas sin periodo devuelve solo la carga de la 411, como hoy'))
def _sin_periodo_como_hoy(ctx: Escenario) -> None:
    assert _ids_de_cargas(ctx.pedir("/api/cargas")) == [ctx.extras["carga_411"]]


@then(parsers.re(r'recibe 422 con «(?P<mensaje>[^»]+)»'))
def _recibe_422(ctx: Escenario, mensaje: str) -> None:
    assert ctx.respuesta.status_code == 422, ctx.respuesta.text
    assert ctx.respuesta.json() == {"detail": mensaje}


@then(parsers.re(r'recibe 200 con una lista vacía(?: y no la 410 ni la 411)?'))
def _lista_vacia(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    assert ctx.respuesta.json() == []


@then(parsers.re(r'la carga queda PUBLICADA aunque PERIODO_VIGENTE sea "(?P<vigente>[^"]+)"'))
def _publicada_en_2026_1(ctx: Escenario, vigente: str) -> None:
    assert ctx.api.ajustes.periodo_vigente == vigente
    assert ctx.respuesta.status_code == 201, ctx.respuesta.text
    assert ctx.respuesta.json()["estado"] == "PUBLICADA"
    assert ctx.filas("SELECT pe.codigo, c.estado FROM abet.carga c JOIN abet.seccion s USING (seccion_id)"
                     " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id WHERE c.carga_id = %s",
                     ctx.carga_id) == [("2026-1", "PUBLICADA")]


@then(parsers.re(r'la carga queda RECHAZADA con (?P<motivo>[A-Z_]+)'))
def _rechazada_con(ctx: Escenario, motivo: str) -> None:
    assert ctx.respuesta.json()["estado"] == "RECHAZADA", ctx.respuesta.text
    assert ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", ctx.carga_id) == "RECHAZADA"
    assert ctx.cuenta("rechazo_fila", "carga_id = %s AND motivo = %s", ctx.carga_id, motivo) == 1


@then(parsers.re(r'el mensaje es «(?P<mensaje>[^»]+)»'))
def _mensaje(ctx: Escenario, mensaje: str) -> None:
    assert mensaje in ctx.respuesta.text, ctx.respuesta.text
