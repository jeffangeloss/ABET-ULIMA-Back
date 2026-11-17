"""Pruebas de la sesión de la API, del arranque y de scripts/asignar_clave.py (T036).

Cada prueba nombra la regla de negocio (business rule, BR) de specs/features/acceso/acceso.spec.md
que comprueba, con lo que debe pasar y lo que no debe pasar, y sigue los escenarios de US-05 de
acceso.feature. Las contraseñas y el secreto de la sesión se generan al azar en cada prueba.
"""

from __future__ import annotations

import hashlib
import importlib.util
import logging
import os
import re
import secrets
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from types import ModuleType

import pytest
from psycopg import sql

from app import sesion as modulo_sesion
from app.main import Ajustes, ConfiguracionDeLaApi, crear_app


def _modulo(nombre: str) -> ModuleType:
    """Módulo de tests/ cargado por su ruta, porque tests/ no es un paquete."""
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, Path(__file__).with_name(f"{nombre}.py"))
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


A = _modulo("api_de_prueba")
TestClient = A.TestClient
plantilla, base, api = A.plantilla, A.base, A.api
RAIZ = Path(__file__).resolve().parent.parent
ASIGNAR = RAIZ / "scripts" / "asignar_clave.py"
INCORRECTOS = {"detail": "Correo o contraseña incorrectos."}
DEMASIADOS = {"detail": "Demasiados intentos. Espere 15 minutos."}
VENCIDA = {"detail": "La sesión venció. Ingrese otra vez."}


def _ingresar(cliente: TestClient, correo: str, clave: str) -> object:
    return cliente.post("/api/sesion", json={"correo": correo, "contrasena": clave})


def _sesiones(api: object, correo: str) -> int:
    return int(api.uno("SELECT count(*) FROM acceso.sesion s JOIN acceso.usuario_autorizado u USING (usuario_id)"
                       " WHERE u.correo = %s", correo))


def _cookie(respuesta: object) -> str:
    return respuesta.headers["set-cookie"]


# BR-ACCESO-03: ingreso y cookie abet_sesion

def test_br_acceso_03_un_usuario_autorizado_entra_con_su_contrasena(api: object, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    clave = api.asignar(A.DOCENTE_410)
    cliente = api.cliente()
    respuesta = _ingresar(cliente, A.DOCENTE_410, clave)
    assert respuesta.status_code == 200
    assert respuesta.json() == {"correo": A.DOCENTE_410, "rol": "PROFESOR"}
    cookie = _cookie(respuesta)
    token = re.match(r"abet_sesion=([^;]+)", cookie).group(1)
    atributos = {parte.strip().lower() for parte in cookie.split(";")[1:]}
    assert {"httponly", "secure", "samesite=lax", "max-age=43200", "path=/"} <= atributos
    assert not any(atributo.startswith("domain") for atributo in atributos)
    fila = api.dueno.execute(
        "SELECT hash_token, expira_en - creada_en FROM acceso.sesion s JOIN acceso.usuario_autorizado u"
        " USING (usuario_id) WHERE u.correo = %s", (A.DOCENTE_410,)).fetchall()
    assert len(fila) == 1
    assert fila[0][0] == hashlib.sha256(token.encode()).hexdigest() != token
    assert fila[0][1].total_seconds() == 12 * 3600
    actual = cliente.get("/api/sesion")
    assert actual.status_code == 200 and actual.json() == {"correo": A.DOCENTE_410, "rol": "PROFESOR"}
    assert token not in respuesta.text and clave not in respuesta.text
    assert clave not in caplog.text and token not in caplog.text


def test_br_acceso_03_el_correo_se_compara_sin_espacios_ni_mayusculas(api: object) -> None:
    clave = api.asignar(A.DOCENTE_410)
    respuesta = _ingresar(api.cliente(), " Docente410@EXAMPLE.invalid ", clave)
    assert respuesta.status_code == 200 and respuesta.json()["correo"] == A.DOCENTE_410


def test_br_acceso_03_sin_https_local_la_cookie_va_sin_secure(api: object) -> None:
    clave = api.asignar(A.DOCENTE_410)
    cliente = api.cliente(replace(api.ajustes, cookie_segura=False))
    cookie = _cookie(_ingresar(cliente, A.DOCENTE_410, clave)).lower()
    assert "httponly" in cookie and "secure" not in cookie


# BR-ACCESO-04: un solo 401 para todo intento fallido

@pytest.mark.parametrize("caso", ["desconocido", "contrasena_errada", "sin_contrasena", "inactivo"])
def test_br_acceso_04_un_intento_fallido_no_revela_si_el_correo_esta_autorizado(api: object, caso: str) -> None:
    clave = api.asignar(A.DOCENTE_410)
    correo, intento = {
        "desconocido": ("desconocido@example.invalid", secrets.token_urlsafe(12)),
        "contrasena_errada": (A.DOCENTE_410, clave[:-1] + ("a" if clave[-1] != "a" else "b")),
        "sin_contrasena": (A.DOCENTE_411, secrets.token_urlsafe(12)),
        "inactivo": (A.DOCENTE_410, clave),
    }[caso]
    if caso == "inactivo":
        api.dueno.execute("UPDATE acceso.usuario_autorizado SET activo = false WHERE correo = %s", (A.DOCENTE_410,))
    respuesta = _ingresar(api.cliente(), correo, intento)
    assert respuesta.status_code == 401 and respuesta.json() == INCORRECTOS
    assert "set-cookie" not in respuesta.headers
    assert api.uno("SELECT count(*) FROM acceso.sesion") == 0
    assert api.uno("SELECT count(*) FROM acceso.intento_fallido") == 1


def test_br_acceso_04_un_cuerpo_mal_formado_responde_422_con_un_texto(api: object) -> None:
    respuesta = api.cliente().post("/api/sesion", json={"correo": A.DOCENTE_410})
    assert respuesta.status_code == 422
    assert respuesta.json() == {"detail": "La petición no tiene la forma esperada."}


# BR-ACCESO-05: límite de intentos de ingreso

def test_br_acceso_05_cinco_fallos_bloquean_el_correo_autorizado_y_no_a_otro(api: object) -> None:
    clave_410, clave_411 = api.asignar(A.DOCENTE_410), api.asignar(A.DOCENTE_411)
    cliente = api.cliente()
    for _ in range(5):
        assert _ingresar(cliente, A.DOCENTE_410, secrets.token_urlsafe(12)).status_code == 401
    sexta = _ingresar(cliente, A.DOCENTE_410, clave_410)
    assert sexta.status_code == 429 and sexta.json() == DEMASIADOS
    assert "set-cookie" not in sexta.headers
    assert _sesiones(api, A.DOCENTE_410) == 0
    assert _ingresar(cliente, A.DOCENTE_411, clave_411).status_code == 200


def test_br_acceso_05_un_correo_desconocido_recibe_el_mismo_429(api: object) -> None:
    cliente = api.cliente()
    for _ in range(5):
        assert _ingresar(cliente, "desconocido@example.invalid", secrets.token_urlsafe(12)).status_code == 401
    sexta = _ingresar(cliente, " DESCONOCIDO@example.invalid", secrets.token_urlsafe(12))
    assert sexta.status_code == 429 and sexta.json() == DEMASIADOS


def test_br_acceso_05_la_tabla_guarda_el_hmac_del_correo_y_nunca_el_correo(api: object) -> None:
    cliente = api.cliente()
    _ingresar(cliente, A.DOCENTE_410, secrets.token_urlsafe(12))
    guardado = api.uno("SELECT hash_cuenta FROM acceso.intento_fallido")
    esperado = modulo_sesion.hash_cuenta(api.ajustes.sesion_secreto, A.DOCENTE_410)
    assert guardado == esperado
    assert esperado != hashlib.sha256(A.DOCENTE_410.encode()).hexdigest()
    assert esperado != modulo_sesion.hash_cuenta(secrets.token_hex(32), A.DOCENTE_410)


def test_br_acceso_05_los_fallos_de_hace_mas_de_15_minutos_no_cuentan(api: object) -> None:
    clave = api.asignar(A.DOCENTE_410)
    cuenta = modulo_sesion.hash_cuenta(api.ajustes.sesion_secreto, A.DOCENTE_410)
    api.dueno.execute("INSERT INTO acceso.intento_fallido (hash_cuenta, intentado_en)"
                      " SELECT %s, now() - interval '16 minutes' FROM generate_series(1, 5)", (cuenta,))
    assert _ingresar(api.cliente(), A.DOCENTE_410, clave).status_code == 200


def test_br_acceso_05_un_ingreso_correcto_reinicia_la_serie_sin_borrar_filas(api: object) -> None:
    clave = api.asignar(A.DOCENTE_410)
    cliente = api.cliente()
    for _ in range(4):
        _ingresar(cliente, A.DOCENTE_410, secrets.token_urlsafe(12))
    assert _ingresar(cliente, A.DOCENTE_410, clave).status_code == 200
    for _ in range(4):
        _ingresar(cliente, A.DOCENTE_410, secrets.token_urlsafe(12))
    assert _ingresar(cliente, A.DOCENTE_410, clave).status_code == 200
    assert api.uno("SELECT count(*) FROM acceso.intento_fallido") == 8



def _rafaga(api: object, correo: str, intentos: int) -> list[int]:
    """Códigos de intentos fallidos simultáneos, cada uno con su cliente, soltados a la vez por una barrera."""
    clientes = [api.cliente() for _ in range(intentos)]
    barrera = threading.Barrier(intentos)

    def intentar(cliente: TestClient) -> int:
        barrera.wait()
        return _ingresar(cliente, correo, secrets.token_urlsafe(12)).status_code

    with ThreadPoolExecutor(max_workers=intentos) as hilos:
        return list(hilos.map(intentar, clientes))


@pytest.mark.parametrize("correo", [A.DOCENTE_410, "desconocido@example.invalid"])
def test_br_acceso_05_una_rafaga_simultanea_evalua_a_lo_sumo_cinco_contrasenas(api: object, correo: str) -> None:
    api.asignar(A.DOCENTE_410)
    codigos = _rafaga(api, correo, 12)
    assert sorted(codigos) == [401] * 5 + [429] * 7
    assert api.uno("SELECT count(*) FROM acceso.intento_fallido") == 5


def test_br_acceso_05_en_serie_el_sexto_intento_recibe_429(api: object) -> None:
    cliente = api.cliente()
    codigos = [_ingresar(cliente, A.DOCENTE_410, secrets.token_urlsafe(12)).status_code for _ in range(6)]
    assert codigos == [401] * 5 + [429]

# BR-ACCESO-06: sesión vigente leída de la base en cada petición

def test_br_acceso_06_cerrar_la_sesion_vence_la_cookie_y_la_fila(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    token = cliente.cookies.get("abet_sesion")
    cierre = cliente.delete("/api/sesion")
    assert cierre.status_code == 204 and cierre.content == b""
    assert "max-age=0" in _cookie(cierre).lower()
    fila = api.dueno.execute("SELECT expira_en <= clock_timestamp() FROM acceso.sesion WHERE hash_token = %s",
                             (hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
    assert fila == (True,)
    respuesta = api.cliente().get("/api/sesion", headers={"cookie": f"abet_sesion={token}"})
    assert respuesta.status_code == 401 and respuesta.json() == VENCIDA


def test_br_acceso_06_cerrar_sin_sesion_o_con_una_vencida_responde_204(api: object) -> None:
    assert api.cliente().delete("/api/sesion").status_code == 204
    cliente = api.sesion(A.DOCENTE_410)
    api.dueno.execute("UPDATE acceso.sesion SET creada_en = now() - interval '13 hours',"
                      " expira_en = now() - interval '1 hour'")
    assert cliente.delete("/api/sesion").status_code == 204


def test_br_acceso_06_una_sesion_vencida_no_da_acceso(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    api.dueno.execute("UPDATE acceso.sesion SET creada_en = now() - interval '2 hours',"
                      " expira_en = now() - interval '1 minute'")
    respuesta = cliente.get("/api/secciones", params={"periodo": A.PERIODO})
    assert respuesta.status_code == 401 and respuesta.json() == VENCIDA


def test_br_acceso_06_un_usuario_dado_de_baja_deja_de_entrar(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    api.dueno.execute("UPDATE acceso.usuario_autorizado SET activo = false WHERE correo = %s", (A.DOCENTE_410,))
    assert cliente.get("/api/sesion").status_code == 401
    assert cliente.get("/api/secciones", params={"periodo": A.PERIODO}).status_code == 401
    otra = _ingresar(api.cliente(), A.DOCENTE_410, api.claves[A.DOCENTE_410])
    assert otra.status_code == 401 and otra.json() == INCORRECTOS


@pytest.mark.parametrize("ruta", ["/api/sesion", "/api/secciones", "/api/cargas/1", "/api/cargas/1/r17.xlsx"])
def test_br_acceso_06_sin_sesion_ninguna_ruta_de_datos_responde(api: object, ruta: str) -> None:
    respuesta = api.cliente().get(ruta)
    assert respuesta.status_code == 401 and respuesta.json() == VENCIDA


def test_br_acceso_06_una_cookie_inventada_no_da_acceso(api: object) -> None:
    cabecera = {"cookie": f"abet_sesion={secrets.token_urlsafe(32)}"}
    assert api.cliente().get("/api/sesion", headers=cabecera).status_code == 401


# Arranque y configuración (sección 1 del contrato)

def _entorno(**valores: str) -> dict[str, str]:
    entorno = {"DATABASE_URL": "host=/tmp/abet dbname=abet user=abet_app", "SESION_SECRETO": secrets.token_hex(32),
               "PERIODO_VIGENTE": "2026-2", "CONJUNTO_REGLAS": "R-2026-BORRADOR"}
    entorno.update(valores)
    return {clave: valor for clave, valor in entorno.items() if valor != ""}



def test_la_representacion_de_los_ajustes_no_muestra_el_secreto_ni_la_base() -> None:
    secreto, clave_base = secrets.token_hex(32), secrets.token_hex(12)
    ajustes = Ajustes.desde_entorno(_entorno(SESION_SECRETO=secreto,
                                             DATABASE_URL=f"host=/tmp/abet dbname=abet user=abet_app password={clave_base}"))
    assert secreto not in repr(ajustes) and clave_base not in repr(ajustes)
    assert "periodo_vigente='2026-2'" in repr(ajustes)


def test_la_representacion_de_la_api_de_prueba_no_muestra_las_contrasenas(api: object) -> None:
    clave = api.asignar(A.DOCENTE_410)
    assert clave not in repr(api) and api.ajustes.sesion_secreto not in repr(api)

def test_la_configuracion_sale_del_entorno_con_la_guardia_encendida_si_falta() -> None:
    ajustes = Ajustes.desde_entorno(_entorno())
    assert ajustes.periodo_vigente == "2026-2" and ajustes.carga.conjunto_reglas == "R-2026-BORRADOR"
    assert ajustes.carga.guardia_datos_inventados is True and ajustes.cookie_segura is True
    assert Ajustes.desde_entorno(_entorno(GUARDIA_DATOS_INVENTADOS="no")).carga.guardia_datos_inventados is True
    assert Ajustes.desde_entorno(_entorno(GUARDIA_DATOS_INVENTADOS="0")).carga.guardia_datos_inventados is False


@pytest.mark.parametrize("variable", ["DATABASE_URL", "SESION_SECRETO", "PERIODO_VIGENTE", "CONJUNTO_REGLAS"])
def test_sin_una_variable_obligatoria_la_api_no_arranca(variable: str) -> None:
    with pytest.raises(ConfiguracionDeLaApi, match=variable):
        Ajustes.desde_entorno(_entorno(**{variable: ""}))


def test_un_secreto_corto_no_arranca() -> None:
    with pytest.raises(ConfiguracionDeLaApi, match="SESION_SECRETO"):
        Ajustes.desde_entorno(_entorno(SESION_SECRETO=secrets.token_hex(8)))


def test_la_cookie_sin_secure_solo_se_admite_con_una_base_local_fuera_de_vercel() -> None:
    assert Ajustes.desde_entorno(_entorno(ABET_COOKIE_SIN_SECURE="1")).cookie_segura is False
    with pytest.raises(ConfiguracionDeLaApi, match="ABET_COOKIE_SIN_SECURE"):
        Ajustes.desde_entorno(_entorno(ABET_COOKIE_SIN_SECURE="1", VERCEL="1"))
    with pytest.raises(ConfiguracionDeLaApi, match="ABET_COOKIE_SIN_SECURE"):
        Ajustes.desde_entorno(_entorno(ABET_COOKIE_SIN_SECURE="1",
                                       DATABASE_URL="host=ep-ejemplo.neon.tech dbname=abet user=abet_app"))


@pytest.mark.parametrize(("cambio", "mensaje"), [
    ({"periodo_vigente": "2027-1"}, "PERIODO_VIGENTE 2027-1 no existe en abet.periodo"),
    ({"carga": A.Configuracion(conjunto_reglas="R-NO-EXISTE")}, "CONJUNTO_REGLAS R-NO-EXISTE no existe para Ambiental"),
])
def test_la_api_se_detiene_si_la_base_no_tiene_el_periodo_o_las_reglas(api: object, cambio: dict, mensaje: str) -> None:
    with pytest.raises(ConfiguracionDeLaApi, match=mensaje), TestClient(crear_app(replace(api.ajustes, **cambio))):
        pass


def test_la_api_no_arranca_con_un_rol_de_administracion(api: object) -> None:
    ajustes = replace(api.ajustes, database_url=api.base.conexion)
    with pytest.raises(ConfiguracionDeLaApi, match="rol de la aplicación"), TestClient(crear_app(ajustes)):
        pass


def test_vercel_env_dice_de_que_entorno_es_el_despliegue() -> None:
    assert Ajustes.desde_entorno(_entorno()).entorno_vercel is None
    assert Ajustes.desde_entorno(_entorno(VERCEL="1", VERCEL_ENV="preview")).entorno_vercel == "preview"
    with pytest.raises(ConfiguracionDeLaApi, match="VERCEL_ENV"):
        Ajustes.desde_entorno(_entorno(VERCEL="1"))
    with pytest.raises(ConfiguracionDeLaApi, match="VERCEL_ENV"):
        Ajustes.desde_entorno(_entorno(VERCEL_ENV="staging"))


def _comentar(api: object, comentario: str | None) -> None:
    """Deja el comentario de la base de la prueba, donde db/plataforma/neon/marcar_entorno.sql guarda la marca."""
    valor = sql.NULL if comentario is None else sql.Literal(comentario)
    api.dueno.execute(sql.SQL("COMMENT ON DATABASE {} IS {}").format(sql.Identifier(api.dueno.info.dbname), valor))


@pytest.mark.parametrize(("comentario", "entorno"), [
    ("abet.entorno=preview", "preview"), ("abet.entorno=production", "production"), (None, "development"),
    (None, None)])
def test_la_api_arranca_si_la_base_esta_marcada_para_su_entorno_de_vercel(
        api: object, comentario: str | None, entorno: str | None) -> None:
    _comentar(api, comentario)
    with TestClient(crear_app(replace(api.ajustes, entorno_vercel=entorno))) as cliente:
        assert cliente.get("/api/sesion").status_code == 401


@pytest.mark.parametrize(("comentario", "entorno"), [
    ("abet.entorno=production", "preview"), ("abet.entorno=preview", "production"), (None, "preview"),
    (None, "production"), ("Base del piloto", "production"), ("abet.entorno=preview ", "preview")])
def test_la_api_no_arranca_contra_la_base_de_otro_entorno_de_vercel(
        api: object, comentario: str | None, entorno: str) -> None:
    _comentar(api, comentario)
    with pytest.raises(ConfiguracionDeLaApi, match=f"el despliegue es de {entorno}"), \
            TestClient(crear_app(replace(api.ajustes, entorno_vercel=entorno))):
        pass


def test_una_ruta_que_no_existe_responde_con_un_texto_en_espanol(api: object) -> None:
    respuesta = api.cliente().get("/api/no-existe")
    assert respuesta.status_code == 404 and respuesta.json() == {"detail": "La ruta no existe."}


# BR-ACCESO-02: contraseña asignada con hash Argon2id

def test_br_acceso_02_el_comando_guarda_solo_el_hash_argon2id(api: object) -> None:
    clave = secrets.token_urlsafe(18)
    entorno = {**os.environ, "DATABASE_URL": api.base.conexion}
    corrida = subprocess.run([sys.executable, str(ASIGNAR), "--correo", A.DOCENTE_410], input=clave + "\n",
                             env=entorno, capture_output=True, text=True, check=False)
    assert corrida.returncode == 0, corrida.stderr
    assert clave not in corrida.stdout + corrida.stderr
    hash_clave = api.uno("SELECT hash_clave FROM acceso.credencial c JOIN acceso.usuario_autorizado u"
                         " USING (usuario_id) WHERE u.correo = %s", A.DOCENTE_410)
    assert hash_clave.startswith("$argon2id$")
    volcado = api.dueno.execute(
        "SELECT string_agg(t::text, ' ') FROM (SELECT row_to_json(x)::text AS t FROM acceso.credencial x"
        " UNION ALL SELECT row_to_json(x)::text FROM acceso.usuario_autorizado x) filas").fetchone()[0]
    assert clave not in volcado
    assert _ingresar(api.cliente(), A.DOCENTE_410, clave).status_code == 200


def test_br_acceso_02_el_comando_no_asigna_a_un_correo_desconocido(api: object) -> None:
    entorno = {**os.environ, "DATABASE_URL": api.base.conexion}
    corrida = subprocess.run([sys.executable, str(ASIGNAR), "--correo", "desconocido@example.invalid"],
                             input=secrets.token_urlsafe(18) + "\n", env=entorno, capture_output=True, text=True,
                             check=False)
    assert corrida.returncode == 1
    assert api.uno("SELECT count(*) FROM acceso.credencial") == 0


def test_br_acceso_02_el_comando_rechaza_una_contrasena_vacia(api: object) -> None:
    entorno = {**os.environ, "DATABASE_URL": api.base.conexion}
    corrida = subprocess.run([sys.executable, str(ASIGNAR), "--correo", A.DOCENTE_410], input="\n", env=entorno,
                             capture_output=True, text=True, check=False)
    assert corrida.returncode == 2
    assert api.uno("SELECT count(*) FROM acceso.credencial") == 0
