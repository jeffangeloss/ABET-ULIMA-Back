"""Pasos de alcance_y_privacidad.feature de la spec 004 (US-38 y US-42), ejecutables con pytest-bdd (T033).

El .feature manda. Ningún paso cambia una cifra, un mensaje ni un título para que el escenario pase, y cada
«Entonces» se comprueba contra la respuesta de GET /api/resultados o contra la base, sin dobles del sistema bajo
prueba. El recorrido de las rutas registradas es el de tests/rutas_registradas.py, el mismo de
tests/test_rutas_protegidas.py (BR-ACCESO-10). Los pasos que repite resultados.feature viven en el conftest.py de esta
carpeta.

Los dos escenarios de la pantalla P6 llevan @delegado_a_vitest y registran la propiedad «delegado_a_vitest» con la
prueba de Vitest del Front que los comprueba, como test_resultados_feature.py.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when
from pytest_bdd.scenario import scenario_wrapper_template_registry

A = sys.modules["api_de_prueba"]
Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]

scenarios("specs/004-reportes-docente/aceptacion/alcance_y_privacidad.feature")


def _rutas_registradas() -> Any:
    if "rutas_registradas" not in sys.modules:
        especificacion = importlib.util.spec_from_file_location("rutas_registradas", RAIZ / "tests" / "rutas_registradas.py")
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules["rutas_registradas"] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules["rutas_registradas"]


def _conftest(ctx: Escenario) -> Any:
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            return plugin
    raise AssertionError("no se encontró el conftest.py del arnés de aceptación")


def _cuerpo(ctx: Escenario) -> dict[str, Any]:
    assert ctx.respuesta is not None and ctx.respuesta.status_code == 200, ctx.respuesta.text
    return ctx.respuesta.json()


def _secciones(ctx: Escenario) -> list[tuple[str, str]]:
    return [(s["asignatura"]["codigo"], s["numero"]) for s in _cuerpo(ctx)["secciones"]]


def _lista(texto: str) -> list[str]:
    """Elementos de una enumeración en español, con «y» o con «e» antes de «i», como en «provisional e indicadores»."""
    return [parte.strip() for parte in re.split(r", | y | e ", texto) if parte.strip()]


def _sin_la_seccion(ctx: Escenario, numero: str, asignatura: str) -> None:
    """Falla si la respuesta trae la sección, su seccion_id o el carga_id de alguna de sus cargas."""
    seccion = ctx.seccion_id(numero, asignatura)
    cargas = {int(fila[0]) for fila in ctx.filas("SELECT carga_id FROM abet.carga WHERE seccion_id = %s", seccion)}
    assert cargas, f"la sección {numero} de {asignatura} no tiene cargas, así que la prueba no revisaría nada"
    assert (asignatura, numero) not in _secciones(ctx)

    def recorrer(valor: Any) -> None:
        if isinstance(valor, dict):
            assert valor.get("seccion_id") != seccion, "la respuesta trae el seccion_id de la sección ajena"
            assert valor.get("carga_id") not in cargas, "la respuesta trae un carga_id de la sección ajena"
            for hijo in valor.values():
                recorrer(hijo)
        elif isinstance(valor, list):
            for hijo in valor:
                recorrer(hijo)
    recorrer(_cuerpo(ctx))


# Pantalla P6, delegada a Vitest

VITEST_P6 = "front/tests/pantallas/MisLogros.test.tsx › P6 Mis logros por SO › "
CUBIERTO_POR_VITEST = {
    "P6 no ofrece subir exports": [VITEST_P6 + "no ofrece Subir export al profesor ni al coordinador"],
    "P6 no guarda nada en el navegador": [VITEST_P6 + "no guarda nada en localStorage ni en sessionStorage"],
}


def _delegar(ctx: Escenario, texto: str) -> None:
    escenario = scenario_wrapper_template_registry[ctx.request.node.function].name
    pruebas = CUBIERTO_POR_VITEST.get(escenario)
    assert pruebas, f"el escenario de pantalla «{escenario}» no tiene pruebas de Vitest anotadas"
    ctx.request.node.user_properties.append(("delegado_a_vitest", f"{texto} → {'; '.join(pruebas)}"))


@given(parsers.re(r'(?P<texto>P6 abierta por .+)'))
def _p6_abierta(ctx: Escenario, texto: str) -> None:
    _delegar(ctx, texto)


@then(parsers.re(r'(?P<texto>P6 no tiene .+|window\.localStorage .+)'))
def _p6_muestra(ctx: Escenario, texto: str) -> None:
    _delegar(ctx, texto)


# Dado, las sesiones que no valen

@given("una petición sin la cookie abet_sesion")
def _sin_cookie(ctx: Escenario) -> None:
    ctx.extras["sin_cookie"] = True


@given(parsers.re(r'que la sesión de "(?P<correo>[^"]+)" está vencida'))
def _sesion_vencida(ctx: Escenario, correo: str) -> None:
    ctx.sesion(correo)
    ctx.extras["con_sesion"] = correo
    filas = ctx.filas("UPDATE acceso.sesion s SET creada_en = now() - interval '13 hours',"
                      " expira_en = now() - interval '1 hour' FROM acceso.usuario_autorizado u"
                      " WHERE u.usuario_id = s.usuario_id AND u.correo = %s RETURNING s.sesion_id", correo)
    assert len(filas) == 1


@given(parsers.re(r'que "(?P<correo>[^"]+)" tiene la sesión iniciada y después su usuario pasa a activo falso'))
def _usuario_dado_de_baja(ctx: Escenario, correo: str) -> None:
    ctx.sesion(correo)
    ctx.extras["con_sesion"] = correo
    assert len(ctx.filas("UPDATE acceso.usuario_autorizado SET activo = false WHERE correo = %s RETURNING usuario_id",
                         correo)) == 1


@given(parsers.re(r'que GET /api/resultados\?periodo=(?P<periodo>[0-9]+-[0-9]+) le responde 200 con la sección '
                  r'(?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)"'))
def _primera_respuesta(ctx: Escenario, periodo: str, numero: str, asignatura: str) -> None:
    _conftest(ctx).pedir_resultados(ctx, periodo)
    assert _secciones(ctx) == [(asignatura, numero)]


# Cuando

@when(parsers.re(r'el dueño de la base retira la fila de acceso\.docente_seccion que asigna la (?P<numero>[0-9]+) a '
                 r'"(?P<correo>[^"]+)"'))
def _retira_la_asignacion(ctx: Escenario, numero: str, correo: str) -> None:
    filas = ctx.filas("DELETE FROM acceso.docente_seccion d USING acceso.usuario_autorizado u"
                      " WHERE u.usuario_id = d.usuario_id AND u.correo = %s AND d.seccion_id = %s RETURNING d.seccion_id",
                      correo, ctx.seccion_id(numero))
    assert len(filas) == 1


@when(parsers.re(r'se envía otra vez GET /api/resultados\?periodo=(?P<periodo>[0-9]+-[0-9]+) con la misma cookie'))
def _otra_vez(ctx: Escenario, periodo: str) -> None:
    _conftest(ctx).pedir_resultados(ctx, periodo)


@when(parsers.re(r'se envía GET /api/resultados\?periodo=(?P<periodo>[0-9]+-[0-9]+)&seccion_id=\{seccion_id de la '
                 r'sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)"\}'))
def _con_seccion_id(ctx: Escenario, periodo: str, numero: str, asignatura: str) -> None:
    arnes = _conftest(ctx)
    ctx.extras["sin_parametro"] = arnes.pedir_resultados(ctx, periodo).json()
    arnes.pedir_resultados(ctx, periodo, seccion_id=ctx.seccion_id(numero, asignatura))


@given("la lista cerrada de rutas públicas, que son POST /api/sesion, DELETE /api/sesion, POST /api/sesion/codigo "
       "cuando exista y GET /api/openapi.json")
def _lista_publica(ctx: Escenario) -> None:
    assert _rutas_registradas().PUBLICAS == {("POST", "/api/sesion"), ("DELETE", "/api/sesion"),
                                             ("POST", "/api/sesion/codigo"), ("GET", "/api/openapi.json")}


@when("una prueba recorre todas las rutas registradas en la aplicación y llama a cada una sin la cookie abet_sesion")
def _recorre_sin_cookie(ctx: Escenario) -> None:
    respuesta = ctx.subir(A.DOCENTE_410, ctx.de_inventados(A.CORRECTO), A.CORRECTO, "410")
    assert respuesta.status_code == 201, respuesta.text
    ctx.extras["ids_410"] = {"seccion": ctx.seccion_id("410"), "carga": respuesta.json()["carga_id"]}
    ctx.extras["sin_cookie"] = _rutas_registradas().sin_cookie(ctx.api.cliente(), ctx.extras["ids_410"])


# Entonces, el alcance

@then('la API responde 200 con 3 secciones, la 412 de "450002" y la 410 y la 412 de "450010"')
def _tres_secciones_propias(ctx: Escenario) -> None:
    assert _secciones(ctx) == [("450002", "412"), ("450010", "410"), ("450010", "412")]


@then(parsers.re(r'la API responde 200 con 1 sección, la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)", con el carga_id '
                 r'de su propia carga'))
def _una_seccion_propia(ctx: Escenario, numero: str, asignatura: str) -> None:
    [seccion] = _cuerpo(ctx)["secciones"]
    assert (seccion["asignatura"]["codigo"], seccion["numero"]) == (asignatura, numero)
    assert seccion["carga_id"] == ctx.extras["cargas_de"][(asignatura, numero)]


@then(parsers.re(r'la API responde 200 con (?P<n>[0-9]+) secciones'))
def _n_secciones(ctx: Escenario, n: str) -> None:
    assert len(_cuerpo(ctx)["secciones"]) == int(n)


@then(parsers.re(r'la API responde 200 con el mismo cuerpo que sin el parámetro seccion_id, solo con la sección '
                 r'(?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)"'))
def _mismo_cuerpo(ctx: Escenario, numero: str, asignatura: str) -> None:
    assert _cuerpo(ctx) == ctx.extras["sin_parametro"]
    assert _secciones(ctx) == [(asignatura, numero)]


@then(parsers.re(r'la respuesta no trae la sección (?P<a>[0-9]+) de "(?P<asignatura_a>[0-9]+)"'
                 r'(?: ni la (?P<b>[0-9]+) de "(?P<asignatura_b>[0-9]+)")?'))
def _no_trae(ctx: Escenario, a: str, asignatura_a: str, b: str | None, asignatura_b: str | None) -> None:
    _sin_la_seccion(ctx, a, asignatura_a)
    if b is not None:
        _sin_la_seccion(ctx, b, asignatura_b)


@then(parsers.re(r'la API responde (?P<codigo>401|422) con el cuerpo (?P<cuerpo>\{.*\}) y sin secciones'))
def _error_sin_secciones(ctx: Escenario, codigo: str, cuerpo: str) -> None:
    assert ctx.respuesta.status_code == int(codigo), ctx.respuesta.text
    assert ctx.respuesta.json() == json.loads(cuerpo)
    assert "secciones" not in ctx.respuesta.text and "seccion_id" not in ctx.respuesta.text


# Entonces, las rutas registradas

@then("cada ruta fuera de esa lista responde 401, también GET /api/resultados")
def _todas_responden_401(ctx: Escenario) -> None:
    respuestas = ctx.extras["sin_cookie"]
    assert ("GET", "/api/resultados") in respuestas
    for (metodo, camino), respuesta in respuestas.items():
        assert respuesta.status_code == 401, f"{metodo} {camino} responde {respuesta.status_code} sin sesión"


@then(parsers.re(r'cada ruta que recibe un seccion_id o un carga_id responde 403 con el cuerpo (?P<cuerpo>\{.*\}) cuando '
                 r'"(?P<correo>[^"]+)" le pasa uno de la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)"'))
def _todas_responden_403(ctx: Escenario, cuerpo: str, correo: str, numero: str, asignatura: str) -> None:
    ids = ctx.extras["ids_410"]
    assert ids["seccion"] == ctx.seccion_id(numero, asignatura)
    respuestas = _rutas_registradas().con_identificador_ajeno(ctx.sesion(correo), ids)
    assert len(respuestas) >= 4, sorted(respuestas)
    for (metodo, camino), respuesta in respuestas.items():
        assert respuesta.status_code == 403, f"{metodo} {camino} responde {respuesta.status_code}"
        assert respuesta.json() == json.loads(cuerpo), f"{metodo} {camino}"


# Entonces, la privacidad del cuerpo

@then('el cuerpo trae solo periodo, so y secciones, y cada elemento de so trae solo numero y descripcion')
def _claves_del_cuerpo(ctx: Escenario) -> None:
    cuerpo = _cuerpo(ctx)
    assert set(cuerpo) == {"periodo", "so", "secciones"}
    assert cuerpo["so"] and all(set(so) == {"numero", "descripcion"} for so in cuerpo["so"])


@then(parsers.re(r'cada sección trae solo (?P<lista>.+)'))
def _claves_de_cada_seccion(ctx: Escenario, lista: str) -> None:
    secciones = _cuerpo(ctx)["secciones"]
    assert secciones and all(set(s) == set(_lista(lista)) for s in secciones), [sorted(s) for s in secciones]
    assert all(set(s["asignatura"]) == {"codigo", "nombre"} for s in secciones)


@then(parsers.re(r'cada indicador trae solo (?P<lista>.+)'))
def _claves_de_cada_indicador(ctx: Escenario, lista: str) -> None:
    indicadores = [i for s in _cuerpo(ctx)["secciones"] for i in s["indicadores"]]
    assert indicadores and all(set(i) == set(_lista(lista)) for i in indicadores)


@then(parsers.re(r'ninguna parte del cuerpo trae (?P<lista>.+)'))
def _sin_claves_prohibidas(ctx: Escenario, lista: str) -> None:
    def claves(valor: Any) -> set[str]:
        if isinstance(valor, dict):
            return set(valor) | {c for hijo in valor.values() for c in claves(hijo)}
        if isinstance(valor, list):
            return {c for hijo in valor for c in claves(hijo)}
        return set()
    presentes = claves(_cuerpo(ctx))
    for prohibida in re.split(r", | ni ", lista):
        assert prohibida not in presentes and prohibida not in ctx.respuesta.text, prohibida


@then('el cuerpo no trae ningún número de 8 dígitos, ningún «@» ni el texto «Inventado» de la columna Last Name de los '
      'exports')
def _sin_personas(ctx: Escenario) -> None:
    texto = ctx.respuesta.text
    assert _cuerpo(ctx)["secciones"]
    assert not re.search(r"(?<![0-9])[0-9]{8}(?![0-9])", texto)
    assert "@" not in texto and "Inventado" not in texto


@then(parsers.re(r'la API responde (?P<codigo>[0-9]+) con la cabecera Cache-Control "(?P<valor>[^"]+)"'))
def _sin_cache(ctx: Escenario, codigo: str, valor: str) -> None:
    assert ctx.respuesta.status_code == int(codigo), ctx.respuesta.text
    assert ctx.respuesta.headers["cache-control"] == valor
