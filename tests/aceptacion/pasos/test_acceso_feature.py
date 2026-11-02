"""Pasos de acceso.feature (US-05 y US-06), ejecutables con pytest-bdd en español (T051).

El .feature manda. Ningún paso cambia una cifra, un mensaje ni un título para que el escenario pase, y cada
«Entonces» se comprueba contra la respuesta de la API o contra la base, sin dobles del sistema bajo prueba.
Las contraseñas y el secreto de la sesión salen de tests/api_de_prueba.py, que los genera al vuelo.

Los pasos que nombran la pantalla P2 o P3 los comprueban las pruebas de Vitest del Front (T045), como dice el
encabezado de los .feature. Aquí quedan registrados con la propiedad «delegado_a_vitest» y no comprueban nada,
así que el informe de cada escenario separa lo que verifica este módulo de lo que verifica el Front.

Los dos escenarios de US-06 de varias_secciones.feature los ejecuta test_varias_secciones_feature.py. Los escenarios de US-20 llevan la etiqueta @corte2 y el conftest.py los omite con su razón.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import secrets
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

A = sys.modules["api_de_prueba"]
Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
FEATURES = "specs/001-mvp-carga-r17/aceptacion"
ASIGNAR = RAIZ / "scripts" / "asignar_clave.py"
ASIGNATURA = "450002"
COOKIE = "abet_sesion"
CUERPO = r"(?P<cuerpo>\{.*\})"

scenarios(f"{FEATURES}/acceso.feature")


# Ayudas

def _token(cliente: Any) -> str:
    valor = cliente.cookies.get(COOKIE)
    assert valor, "el cliente no tiene la cookie abet_sesion"
    return valor


def _atributos(respuesta: Any) -> set[str]:
    """Atributos de la cabecera Set-Cookie en minúscula, sin el par nombre y valor."""
    return {parte.strip().lower() for parte in respuesta.headers["set-cookie"].split(";")[1:]}


# Cada paso de pantalla y la prueba de Vitest del Front que lo cubre, en tests/pantallas/MisSecciones.test.tsx
# (describe «P2 Mis secciones», T045). La clave es el comienzo del texto del paso.
VITEST = "front/tests/pantallas/MisSecciones.test.tsx › P2 Mis secciones › "
CUBIERTO_POR_VITEST = {
    "se abre la pantalla P2": "lista todas las secciones del profesor, una fila por sección, con su estado de carga",
    "la pantalla P2 «Mis secciones» muestra 1 fila": (
        "lista todas las secciones del profesor, una fila por sección, con su estado de carga"),
    "la pantalla P2 muestra en la sección 410 \"Publicada": (
        "lista todas las secciones del profesor, una fila por sección, con su estado de carga"),
    "la fila de 450010, sección 410, muestra": "una sección sin plan de medición lo dice y deja Subir export desactivado",
    "el botón \"Subir export\" de esa fila está desactivado": (
        "una sección sin plan de medición lo dice y deja Subir export desactivado"),
    "la fila de 450002, sección 410, conserva": "Subir export abre P3 con la sección de esa fila",
}


def _delegar(ctx: Escenario, texto: str) -> None:
    """Deja constancia de un paso de pantalla y de la prueba de Vitest que lo comprueba en el Front.

    Un paso de pantalla sin una prueba de Vitest anotada en CUBIERTO_POR_VITEST hace fallar el escenario, para
    que ninguna delegación quede sin rastro.
    """
    pruebas = [prueba for inicio, prueba in CUBIERTO_POR_VITEST.items() if texto.startswith(inicio)]
    assert len(pruebas) == 1, f"el paso de pantalla «{texto}» no tiene una prueba de Vitest anotada"
    ctx.request.node.user_properties.append(("delegado_a_vitest", f"{texto} → {VITEST}{pruebas[0]}"))


def _sesiones(ctx: Escenario, correo: str | None = None) -> int:
    if correo is None:
        return int(ctx.uno("SELECT count(*) FROM acceso.sesion"))
    return int(ctx.uno("SELECT count(*) FROM acceso.sesion s JOIN acceso.usuario_autorizado u USING (usuario_id)"
                       " WHERE u.correo = %s", correo))


def _anotar_sesiones(ctx: Escenario, correo: str | None = None) -> None:
    """Guarda, solo la primera vez del escenario, cuántas sesiones había antes de la primera petición."""
    ctx.extras.setdefault("sesiones_antes", _sesiones(ctx))
    if correo is not None:
        ctx.extras.setdefault("sesiones_antes_de", {}).setdefault(correo, _sesiones(ctx, correo))


def _registro(ctx: Escenario) -> pytest.LogCaptureFixture:
    caplog = ctx.request.getfixturevalue("caplog")
    caplog.set_level(logging.DEBUG)
    return caplog


def _lista(ctx: Escenario) -> list[dict[str, Any]]:
    cuerpo = ctx.cuerpo()
    assert isinstance(cuerpo, list), cuerpo
    return cuerpo


def _clave_de(ctx: Escenario, correo: str, cambiada: bool = False) -> str:
    clave = ctx.api.claves[correo]
    if cambiada:
        return clave[:-1] + ("A" if clave[-1] != "A" else "B")
    return clave


def _ingresar(ctx: Escenario, correo: str, clave: str) -> Any:
    cliente = ctx.api.cliente()
    ctx.extras["cliente"] = cliente
    ctx.extras["correo_enviado"] = correo
    ctx.respuesta = cliente.post("/api/sesion", json={"correo": correo, "contrasena": clave})
    return ctx.respuesta


def _carga_publicada(ctx: Escenario, numero: str, asignatura: str, publicar: bool) -> int:
    """carga_id de la carga PUBLICADA de la sección, que sube docente410 si el escenario pide una y no hay."""
    seccion = ctx.seccion_id(numero, asignatura)
    filas = ctx.filas("SELECT carga_id FROM abet.carga WHERE seccion_id = %s AND estado = 'PUBLICADA'"
                      " ORDER BY carga_id DESC", seccion)
    if not filas and publicar:
        respuesta = ctx.subir(A.DOCENTE_410, A.archivo(A.CORRECTO), A.CORRECTO, numero, asignatura)
        assert respuesta.status_code == 201, respuesta.text
        return int(respuesta.json()["carga_id"])
    assert filas, f"la sección {numero} de {asignatura} no tiene ninguna carga PUBLICADA"
    return int(filas[0][0])


def _resolver(ctx: Escenario, ruta: str) -> str:
    """Cambia los marcadores {sección ...} y {carga ...} de la ruta por los identificadores de la base."""
    def cambio(coincidencia: re.Match[str]) -> str:
        texto = coincidencia.group(1)
        if (seccion := re.fullmatch(r"sección (\d+)(?: de (\d+))?", texto)):
            return str(ctx.seccion_id(seccion[1], seccion[2] or ASIGNATURA))
        carga = re.fullmatch(r"carga (publicada )?de la (\d+)(?: de (\d+))?", texto)
        assert carga is not None, f"no se reconoce el marcador {{{texto}}}"
        return str(_carga_publicada(ctx, carga[2], carga[3] or ASIGNATURA, publicar=bool(carga[1])))
    return re.sub(r"\{([^}]+)\}", cambio, ruta)


def _datos_ajenos(ctx: Escenario, numero: str, asignatura: str) -> None:
    """Falla si la respuesta lleva algún dato de la sección o de sus cargas.

    Los carga_id de la sección se buscan siempre, también cuando el paso no nombra la carga, porque ninguna
    respuesta debe traer una carga de una sección ajena.
    """
    seccion = ctx.seccion_id(numero, asignatura)
    cargas = {int(f[0]) for f in ctx.filas("SELECT carga_id FROM abet.carga WHERE seccion_id = %s", seccion)}
    curso = ctx.uno("SELECT coalesce(curso_blackboard, '') FROM abet.seccion WHERE seccion_id = %s", seccion)
    texto = ctx.respuesta.text
    assert not curso or curso not in texto, "la respuesta nombra el curso de Blackboard de la sección"

    def recorrer(valor: Any) -> None:
        if isinstance(valor, dict):
            assert valor.get("seccion_id") != seccion, "la respuesta trae el seccion_id de la sección"
            if "carga_id" in valor:
                assert valor["carga_id"] not in cargas, "la respuesta trae un carga_id ajeno"
            if valor.get("numero") == numero and isinstance(valor.get("asignatura"), dict):
                assert valor["asignatura"].get("codigo") != asignatura, "la respuesta trae la sección"
            for hijo in valor.values():
                recorrer(hijo)
        elif isinstance(valor, list):
            for hijo in valor:
                recorrer(hijo)
    if ctx.respuesta.headers.get("content-type", "").startswith("application/json"):
        recorrer(ctx.respuesta.json())


def _es_seccion(item: dict[str, Any], numero: str, asignatura: str, nombre: str | None, pis: list[str],
                periodo: str = "2026-2") -> None:
    assert item["numero"] == numero and item["asignatura"]["codigo"] == asignatura, item
    if nombre is not None:
        assert item["asignatura"]["nombre"] == nombre, item
    assert item["periodo"] == periodo, item
    assert item["pi"] == pis, item


def _pis(texto: str) -> list[str]:
    return re.findall(r"[0-9]+\.[0-9]+", texto)


# Antecedentes de acceso.feature

@given("la base con los datos inventados de 2026-2 de periodo_2026_2_inventado.sql")
def _base_del_periodo(ctx: Escenario) -> None:
    ctx.crear_base("periodo")
    assert ctx.uno("SELECT count(*) FROM abet.periodo WHERE codigo = '2026-2'") == 1
    assert ctx.uno("SELECT count(*) FROM abet.seccion s JOIN abet.periodo p USING (periodo_id)"
                   " WHERE p.codigo = '2026-2'") == 2


@given(parsers.re(r'"(?P<correo>[^"]+)" activo con rol "(?P<rol>[A-Z]+)"'
                  r'(?: y sin secciones en acceso\.docente_seccion'
                  r'| y la sección (?P<numero>[0-9]+) de (?P<asignatura>[0-9]+) en (?P<periodo>[0-9-]+))'))
def _usuario_activo(ctx: Escenario, correo: str, rol: str, numero: str | None, asignatura: str | None,
                    periodo: str | None) -> None:
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, True)]
    asignadas = ctx.filas("SELECT s.numero, a.codigo FROM acceso.docente_seccion d JOIN abet.seccion s USING (seccion_id)"
                          " JOIN abet.asignatura a USING (asignatura_id) WHERE d.usuario_id = %s",
                          ctx.usuario_id(correo))
    assert asignadas == ([(numero, asignatura)] if numero else [])


@given(parsers.re(r'la API configurada con PERIODO_VIGENTE "(?P<periodo>[^"]+)" y CONJUNTO_REGLAS "(?P<reglas>[^"]+)"'))
def _api_configurada(ctx: Escenario, periodo: str, reglas: str) -> None:
    """Arranca la API con el periodo y las reglas del paso y con GUARDIA_DATOS_INVENTADOS encendida.

    El Antecedente no nombra la guardia. Queda encendida porque es el valor del piloto y porque la base de
    estas pruebas solo trae códigos inventados, así que la guardia no cambia ninguna respuesta de acceso.feature.
    """
    ctx.configurar_api(periodo, reglas, "1")
    ctx.api.cliente()  # El arranque de la API valida la configuración contra la base.


# Contraseñas y sesiones

@given(parsers.re(r'(?:que )?(?P<lista>"[^"]+"(?: y "[^"]+")?) tienen? asignada una contraseña de prueba'
                  r'(?: y "(?P<sin>[^"]+)" no tiene ninguna)?'))
def _contrasena_asignada(ctx: Escenario, lista: str, sin: str | None) -> None:
    correos = re.findall(r'"([^"]+)"', lista)
    for correo in correos:
        ctx.api.asignar(correo)
    ctx.extras["correo"] = correos[0]
    if sin is not None:
        assert ctx.uno("SELECT count(*) FROM acceso.credencial c JOIN acceso.usuario_autorizado u USING (usuario_id)"
                       " WHERE u.correo = %s", sin) == 0


@given(parsers.re(r'(?:que )?"(?P<correo>[^"]+)" tiene la sesión iniciada(?P<cookie> y la cookie "abet_sesion")?'))
def _sesion_del_usuario(ctx: Escenario, correo: str, cookie: str | None) -> None:
    _iniciar(ctx, correo)
    if cookie:
        assert ctx.uno("SELECT count(*) FROM acceso.sesion WHERE hash_token = %s",
                       hashlib.sha256(ctx.extras["token"].encode()).hexdigest()) == 1


def _iniciar(ctx: Escenario, correo: str) -> None:
    cliente = ctx.sesion(correo)
    ctx.extras.update(cliente=cliente, correo=correo, token=_token(cliente))
    if ctx.profesor is None and ctx.filas("SELECT rol FROM acceso.usuario_autorizado WHERE correo = %s",
                                          correo) == [("PROFESOR",)]:
        ctx.profesor = correo


@given(parsers.re(r'(?:que )?"(?P<correo>[^"]+)" tiene una sesión cuyo expira_en es de hace 1 minuto'))
def _sesion_vencida(ctx: Escenario, correo: str) -> None:
    _iniciar(ctx, correo)
    filas = ctx.filas("UPDATE acceso.sesion SET creada_en = now() - interval '2 minutes',"
                      " expira_en = now() - interval '1 minute' WHERE usuario_id = %s RETURNING sesion_id",
                      ctx.usuario_id(correo))
    assert len(filas) == 1


@given('una petición sin la cookie "abet_sesion"')
def _sin_cookie(ctx: Escenario) -> None:
    ctx.extras.update(cliente=ctx.api.cliente(), token=None)


@when(parsers.re(
    r'el administrador técnico corre el comando de asignar contraseña para "(?P<correo>[^"]+)" '
    r'con una contraseña de prueba generada al azar'))
def _asignar_por_comando(ctx: Escenario, correo: str) -> None:
    clave = secrets.token_urlsafe(18)
    corrida = subprocess.run([sys.executable, str(ASIGNAR), "--correo", correo], input=clave + "\n",
                             env={**os.environ, "DATABASE_URL": ctx.api.base.conexion}, capture_output=True,
                             text=True, check=False)
    assert corrida.returncode == 0, corrida.stderr
    ctx.extras.update(correo=correo, clave_del_comando=clave, salida=corrida.stdout + corrida.stderr)


@then(parsers.re(r'acceso\.credencial tiene 1 fila de ese usuario cuyo hash empieza por "(?P<inicio>[^"]+)"'))
def _credencial(ctx: Escenario, inicio: str) -> None:
    filas = ctx.filas("SELECT hash_clave FROM acceso.credencial WHERE usuario_id = %s",
                      ctx.usuario_id(ctx.extras["correo"]))
    assert len(filas) == 1 and filas[0][0].startswith(inicio)


@then("el texto de la contraseña no aparece en ninguna fila del esquema acceso")
def _clave_fuera_de_acceso(ctx: Escenario) -> None:
    tablas = [f[0] for f in ctx.filas("SELECT table_name FROM information_schema.tables"
                                      " WHERE table_schema = 'acceso' AND table_type = 'BASE TABLE'")]
    assert tablas, "el esquema acceso no tiene tablas"
    for tabla in tablas:
        volcado = ctx.uno(f'SELECT coalesce(string_agg(t::text, \' \'), \'\') FROM acceso."{tabla}" t')
        assert ctx.extras["clave_del_comando"] not in volcado, f"la contraseña aparece en acceso.{tabla}"


@then("la salida del comando no muestra la contraseña")
def _salida_sin_clave(ctx: Escenario) -> None:
    assert ctx.extras["clave_del_comando"] not in ctx.extras["salida"]


@when(parsers.re(r'se envía POST /api/sesion con (?:ese correo|el correo "(?P<correo>[^"]*)") y '
                 r'(?P<clave>esa contraseña|una contraseña cualquiera|la contraseña asignada con un carácter cambiado)'))
def _post_sesion(ctx: Escenario, correo: str | None, clave: str) -> None:
    correo = correo if correo is not None else ctx.extras["correo"]
    normalizado = correo.strip().lower()
    _registro(ctx)
    _anotar_sesiones(ctx, normalizado)
    if clave == "esa contraseña":
        texto = _clave_de(ctx, normalizado)
    elif clave == "una contraseña cualquiera":
        texto = secrets.token_urlsafe(18)
    else:
        texto = _clave_de(ctx, normalizado, cambiada=True)
    _ingresar(ctx, correo, texto)
    ctx.extras["correo"] = normalizado
    ctx.extras["texto_clave"] = texto


@when(parsers.re(r'se envía 5 veces POST /api/sesion con el correo "(?P<correo>[^"]+)" y una contraseña distinta '
                 r'dentro de 15 minutos'))
def _cinco_fallos(ctx: Escenario, correo: str) -> None:
    _anotar_sesiones(ctx, correo)
    ctx.extras["correo"] = correo
    for _ in range(5):
        assert _ingresar(ctx, correo, secrets.token_urlsafe(18)).status_code == 401


@when("se envía una sexta vez con la contraseña correcta")
def _sexta(ctx: Escenario) -> None:
    correo = ctx.extras["correo"]
    _ingresar(ctx, correo, _clave_de(ctx, correo))


@then(parsers.re(r'la API responde 200 con el correo "(?P<correo>[^"]+)"(?: y el rol "(?P<rol>[A-Z]+)")?'))
def _responde_200_con_usuario(ctx: Escenario, correo: str, rol: str | None) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    cuerpo = ctx.respuesta.json()
    assert cuerpo["correo"] == correo
    if rol is not None:
        assert cuerpo == {"correo": correo, "rol": rol}


@then(parsers.re(r'(?:la API responde|la sexta respuesta es) (?P<codigo>[0-9]+)(?: con el cuerpo ' + CUERPO + ")?"))
def _responde_con_codigo(ctx: Escenario, codigo: str, cuerpo: str | None) -> None:
    assert ctx.respuesta.status_code == int(codigo), ctx.respuesta.text
    if cuerpo is not None:
        assert ctx.respuesta.json() == json.loads(cuerpo)


@then(parsers.re(r'la respuesta fija la cookie "abet_sesion" con HttpOnly, Secure, SameSite=Lax y Max-Age 43200'))
def _cookie_fijada(ctx: Escenario) -> None:
    assert ctx.respuesta.headers["set-cookie"].startswith(f"{COOKIE}=")
    assert {"httponly", "secure", "samesite=lax", "max-age=43200"} <= _atributos(ctx.respuesta)


@then("la respuesta no trae la cabecera Set-Cookie")
def _sin_set_cookie(ctx: Escenario) -> None:
    assert "set-cookie" not in ctx.respuesta.headers


@then(parsers.re(r'acceso\.sesion tiene 1 fila nueva de ese usuario con expira_en 12 horas después de creada_en'))
def _fila_de_sesion(ctx: Escenario) -> None:
    correo = ctx.extras["correo"]
    assert _sesiones(ctx, correo) - ctx.extras["sesiones_antes_de"][correo] == 1
    filas = ctx.filas("SELECT expira_en - creada_en FROM acceso.sesion s JOIN acceso.usuario_autorizado u"
                      " USING (usuario_id) WHERE u.correo = %s", correo)
    assert [f[0].total_seconds() for f in filas] == [12 * 3600]


@then("esa fila guarda el hash del token y no el valor de la cookie")
def _hash_del_token(ctx: Escenario) -> None:
    token = re.match(rf"{COOKIE}=([^;]+)", ctx.respuesta.headers["set-cookie"])[1]
    esperado = hashlib.sha256(token.encode()).hexdigest()
    assert ctx.uno("SELECT hash_token FROM acceso.sesion s JOIN acceso.usuario_autorizado u USING (usuario_id)"
                   " WHERE u.correo = %s", ctx.extras["correo"]) == esperado != token
    assert token not in ctx.uno("SELECT coalesce(string_agg(s::text, ' '), '') FROM acceso.sesion s")
    ctx.extras["token"] = token


@then(parsers.re(r'(?:GET|POST) /api/(?P<ruta>sesion|secciones\?periodo=2026-2) con (?:esa|la) cookie(?: anterior)? '
                 r'responde (?P<codigo>[0-9]+)(?: con el correo "(?P<correo>[^"]+)" y el rol "(?P<rol>[A-Z]+)")?'))
def _get_con_cookie(ctx: Escenario, ruta: str, codigo: str, correo: str | None, rol: str | None) -> None:
    respuesta = ctx.api.cliente().get(f"/api/{ruta}", headers={"Cookie": f"{COOKIE}={ctx.extras['token']}"})
    assert respuesta.status_code == int(codigo), respuesta.text
    if correo is not None:
        assert respuesta.json() == {"correo": correo, "rol": rol}


@then("los registros de la API de esas peticiones no contienen la contraseña ni el valor de la cookie")
def _registros_limpios(ctx: Escenario) -> None:
    texto = ctx.request.getfixturevalue("caplog").text
    assert ctx.extras["texto_clave"] not in texto and ctx.extras["token"] not in texto


@then(parsers.re(r'acceso\.sesion no gana ninguna fila(?P<de_ese> de ese usuario)?'))
def _sesion_sin_filas(ctx: Escenario, de_ese: str | None) -> None:
    if de_ese:
        correo = ctx.extras["correo"]
        assert _sesiones(ctx, correo) == ctx.extras["sesiones_antes_de"][correo]
    else:
        assert _sesiones(ctx) == ctx.extras["sesiones_antes"]


@then(parsers.re(r'POST /api/sesion de "(?P<correo>[^"]+)" con su contraseña correcta responde 200'))
def _otro_usuario_entra(ctx: Escenario, correo: str) -> None:
    assert _ingresar(ctx, correo, _clave_de(ctx, correo)).status_code == 200


# Cierre, vencimiento y baja

@when(parsers.re(r'el administrador técnico marca a ese usuario como inactivo en acceso\.usuario_autorizado'))
def _dar_de_baja(ctx: Escenario) -> None:
    filas = ctx.filas("UPDATE acceso.usuario_autorizado SET activo = false WHERE correo = %s RETURNING usuario_id",
                      ctx.extras["correo"])
    assert len(filas) == 1


@then("POST /api/sesion con su contraseña correcta responde 401 con el mismo cuerpo que da a un correo desconocido")
def _baja_no_entra(ctx: Escenario) -> None:
    correo = ctx.extras["correo"]
    propio = _ingresar(ctx, correo, _clave_de(ctx, correo))
    desconocido = _ingresar(ctx, "desconocido@example.invalid", secrets.token_urlsafe(18))
    assert propio.status_code == desconocido.status_code == 401
    assert propio.json() == desconocido.json()
    assert "set-cookie" not in propio.headers


@then(parsers.re(r'la API responde 204 y la cookie "abet_sesion" vuelve con Max-Age 0'))
def _cookie_vencida(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 204, ctx.respuesta.text
    assert ctx.respuesta.headers["set-cookie"].startswith(f"{COOKIE}=")
    assert "max-age=0" in _atributos(ctx.respuesta)


@then("la fila de acceso.sesion de esa cookie sigue en la tabla con expira_en menor o igual que la hora del cierre")
def _fila_cerrada(ctx: Escenario) -> None:
    fila = ctx.filas("SELECT expira_en <= clock_timestamp(), expira_en < creada_en + interval '12 hours'"
                     " FROM acceso.sesion WHERE hash_token = %s",
                     hashlib.sha256(ctx.extras["token"].encode()).hexdigest())
    assert fila == [(True, True)]


@then("la respuesta no trae ninguna sección")
def _sin_secciones(ctx: Escenario) -> None:
    cuerpo = ctx.respuesta.json()
    assert not isinstance(cuerpo, list) and "seccion_id" not in ctx.respuesta.text


# Peticiones a las rutas de datos

RUTA = (r"/api/(?:sesion|secciones\?periodo=[0-9-]+|secciones/\{[^}]+\}/cargas"
        r"|cargas/\{[^}]+\}(?:/r17\.xlsx)?)")


@when(parsers.re(rf'se envía (?P<metodo>GET|POST|DELETE) (?P<ruta>{RUTA})'
                 r'(?: (?:sin cuerpo|(?P<cookie>con esa cookie)|con "(?P<archivo>[^"]+)" en el campo multipart «archivo»))?'))
def _enviar(ctx: Escenario, metodo: str, ruta: str, cookie: str | None, archivo: str | None) -> None:
    _registro(ctx)
    ruta = _resolver(ctx, ruta)
    if cookie:
        cliente, cabeceras = ctx.api.cliente(), {"Cookie": f"{COOKIE}={ctx.extras['token']}"}
    else:
        cliente, cabeceras = ctx.extras["cliente"], {}
    ctx.antes = ctx.api.conteos()
    _anotar_sesiones(ctx)
    opciones: dict[str, Any] = {"headers": cabeceras}
    if metodo == "POST":
        nombre = archivo or A.CORRECTO
        opciones["files"] = {"archivo": (nombre, A.archivo(nombre), A.XLSX)}
    ctx.respuesta = cliente.request(metodo, ruta, **opciones)


@then(parsers.re(r'la API responde 200 con (?P<n>[0-9]+) (?:sección|secciones)'))
def _responde_n_secciones(ctx: Escenario, n: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    assert len(_lista(ctx)) == int(n)


@then(parsers.re(r'esa sección es la (?P<numero>[0-9]+) de (?P<asignatura>[0-9]+) "(?P<nombre>[^"]+)" en (?P<periodo>[0-9-]+), '
                 r'con los PI (?P<pis>[0-9., y]+) y el estado de carga "(?P<estado>[A-Z_]+)"'))
def _esa_seccion(ctx: Escenario, numero: str, asignatura: str, nombre: str, periodo: str, pis: str, estado: str) -> None:
    (item,) = _lista(ctx)
    _es_seccion(item, numero, asignatura, nombre, _pis(pis), periodo)
    assert item["estado"] == estado and item["tiene_plan"] is True


@then(parsers.re(r'la respuesta no trae ningún dato de la sección (?P<numero>[0-9]+)(?: de "(?P<asignatura>[0-9]+)")?'
                 r'(?P<carga> ni de su carga)?'))
def _sin_datos_de_la_seccion(ctx: Escenario, numero: str, asignatura: str | None) -> None:
    _datos_ajenos(ctx, numero, asignatura or ASIGNATURA)


@then(parsers.re(r'la API responde 200 con las secciones (?P<a>[0-9]+) y (?P<b>[0-9]+) de (?P<asignatura>[0-9]+) '
                 r'en (?P<periodo>[0-9-]+)'))
def _responde_las_secciones(ctx: Escenario, a: str, b: str, asignatura: str, periodo: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    esperadas = sorted([(a, asignatura, periodo), (b, asignatura, periodo)])
    recibidas = sorted((s["numero"], s["asignatura"]["codigo"], s["periodo"]) for s in _lista(ctx))
    assert recibidas == esperadas


@then(parsers.re(r'acceso\.docente_seccion sigue sin filas de "(?P<correo>[^"]+)"'))
def _sin_asignaciones(ctx: Escenario, correo: str) -> None:
    assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion WHERE usuario_id = %s", ctx.usuario_id(correo)) == 0


@given(parsers.re(r'(?:que )?la sección 410 tiene una carga en estado "PUBLICADA" con 11 filas leídas y 11 aceptadas'))
def _carga_publicada_de_la_410(ctx: Escenario) -> None:
    respuesta = ctx.subir(A.DOCENTE_410, A.archivo(A.CORRECTO), A.CORRECTO, "410")
    assert respuesta.status_code == 201, respuesta.text
    assert ctx.filas("SELECT estado, filas_leidas, filas_aceptadas FROM abet.carga WHERE carga_id = %s",
                     respuesta.json()["carga_id"]) == [("PUBLICADA", 11, 11)]


@then(parsers.re(r'la sección (?P<numero>[0-9]+) trae el estado de carga "(?P<estado>[A-Z_]+)" con filas_leidas '
                 r'(?P<leidas>[0-9]+) y filas_aceptadas (?P<aceptadas>[0-9]+)'))
def _estado_de_la_seccion(ctx: Escenario, numero: str, estado: str, leidas: str, aceptadas: str) -> None:
    (item,) = [s for s in _lista(ctx) if s["numero"] == numero]
    assert (item["estado"], item["filas_leidas"], item["filas_aceptadas"]) == (estado, int(leidas), int(aceptadas))
    assert item["carga_id"] == ctx.uno("SELECT carga_id FROM abet.carga WHERE seccion_id = %s AND estado = 'PUBLICADA'",
                                       item["seccion_id"])


@given(parsers.re(r'(?:que )?la sección 411 tiene una carga PUBLICADA del export inventado de la 411, con los códigos '
                  r'99000012 a 99000022'))
def _carga_publicada_de_la_411(ctx: Escenario) -> None:
    respuesta = ctx.subir(A.DOCENTE_411, A.archivo(A.EXPORT_411), A.EXPORT_411, "411")
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "PUBLICADA", respuesta.text
    codigos = [f[0] for f in ctx.filas("SELECT e.codigo FROM abet.estudiante e JOIN abet.carga_fila f USING (estudiante_id)"
                                       " WHERE f.carga_id = %s ORDER BY e.codigo", respuesta.json()["carga_id"])]
    assert codigos == [str(n) for n in range(99000012, 99000023)]


@given(parsers.re(r'la sección 410 de la asignatura "450010" en 2026-2, sin curso_blackboard, asignada también a '
                  r'"(?P<correo>[^"]+)"'))
def _seccion_sin_plan(ctx: Escenario, correo: str) -> None:
    sembrada = ctx.filas(
        "INSERT INTO abet.seccion (periodo_id, asignatura_id, numero, curso_blackboard)"
        " SELECT p.periodo_id, a.asignatura_id, '410', NULL FROM abet.periodo p, abet.asignatura a"
        " WHERE p.codigo = '2026-2' AND a.codigo = '450010' RETURNING seccion_id")
    assert len(sembrada) == 1
    ctx.filas("INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) VALUES (%s, %s) RETURNING 1",
              ctx.usuario_id(correo), sembrada[0][0])


@given(parsers.re(r'(?:que )?abet\.plan_medicion no tiene filas de 450010 en 2026-2'))
def _sin_plan(ctx: Escenario) -> None:
    assert ctx.uno("SELECT count(*) FROM abet.plan_medicion pm JOIN abet.asignatura a USING (asignatura_id)"
                   " JOIN abet.periodo p USING (periodo_id) WHERE a.codigo = '450010' AND p.codigo = '2026-2'") == 0


@then(parsers.re(r'la API responde 200 con la sección 410 de 450010 con tiene_plan falso y sin PI, y la sección 410 '
                 r'de 450002 con tiene_plan verdadero'))
def _una_sin_plan_y_otra_con_plan(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    por_asignatura = {s["asignatura"]["codigo"]: s for s in _lista(ctx) if s["numero"] == "410"}
    assert set(por_asignatura) == {"450010", "450002"}
    assert por_asignatura["450010"]["tiene_plan"] is False and por_asignatura["450010"]["pi"] == []
    assert por_asignatura["450002"]["tiene_plan"] is True and por_asignatura["450002"]["pi"] == ["5.1", "5.2", "5.3"]


# Pasos de pantalla, que comprueba Vitest en el Front (T045)

@when("se abre la pantalla P2 «Mis secciones»")
def _abrir_p2(ctx: Escenario) -> None:
    _delegar(ctx, "se abre la pantalla P2 «Mis secciones»")


@then(parsers.re(r'(?P<texto>la pantalla P2 .+|en P2 .+|la fila de [0-9]+, sección [0-9]+, .+'
                 r'|el botón "Subir export" de esa fila está desactivado)'))
def _pantalla(ctx: Escenario, texto: str) -> None:
    _delegar(ctx, texto)
