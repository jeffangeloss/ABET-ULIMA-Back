"""Pruebas de las rutas 14 a 16 de la spec 005 (T032), el análisis por indicador de una carga.

GET /api/cargas/{carga_id}/mejora, PUT /api/cargas/{carga_id}/mejora/borrador y POST
/api/cargas/{carga_id}/mejora/declaracion. Cada prueba nombra la regla de negocio (business rule, BR) de
specs/features/mejora/mejora.spec.md que comprueba, con lo que debe pasar y lo que no debe pasar (AGENTS.md, regla 8).
Las cargas se siembran con publicar() de tests/cargas_de_prueba.py y la conexión del dueño de una copia de la base
desechable, como en las pruebas de la ruta 13, y la API escribe con el rol de la aplicación. Las secciones 13.3 a 13.5
del contrato del Front fijan la forma de las respuestas. Todos los textos son inventados.
"""

from __future__ import annotations

import importlib.util
import sys
import unicodedata
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from app.rutas import mejora


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
C = _modulo("cargas_de_prueba")
plantilla, base, api = A.plantilla, A.base, A.api

SIN_ALCANCE = {"detail": "La sección no está a su cargo."}
VENCIDA = {"detail": "La sesión venció. Ingrese otra vez."}
CORRECTO_410 = {"5.1": [1, 3, 4, 3], "5.2": [1, 3, 4, 3], "5.3": [1, 2, 5, 3]}
VARIAS_412 = {"5.1": [1, 1, 5, 4], "5.2": [2, 3, 4, 2], "5.3": [0, 1, 4, 6]}
SIN_5_3 = {"5.1": [1, 3, 4, 3, 0], "5.2": [1, 3, 4, 3, 0], "5.3": [0, 0, 0, 0, 11]}
OM, BP = "OPORTUNIDAD_MEJORA", "BUENA_PRACTICA"
TIPOS_412 = {"5.1": BP, "5.2": OM, "5.3": BP}
TABLAS = ("mejora_borrador", "mejora_borrador_pi", "mejora_declaracion", "mejora_declaracion_pi")


# Ayudas

def _filas(repartos: dict[str, list[int]], desde: int) -> list[Any]:
    """Filas inventadas que dan en cada PI el reparto pedido, con códigos consecutivos desde «desde»."""
    columnas = []
    for reparto in repartos.values():
        niveles = [nivel for nivel, cantidad in zip((1, 2, 3, 4), reparto[:4], strict=True) for _ in range(cantidad)]
        columnas.append(niveles + [None] * (reparto[4] if len(reparto) > 4 else 0))
    assert len({len(columna) for columna in columnas}) == 1, "todos los PI deben sumar las mismas filas"
    return [C.Fila(2 + i, str(desde + i), tuple(columna[i] for columna in columnas)) for i in range(len(columnas[0]))]


def _publicar(api: Any, repartos: dict[str, list[int]] = CORRECTO_410, *, numero: str = "410",
              desde: int = 99000001, conjunto: str = C.BORRADOR, subida_por: str | None = A.DOCENTE_410,
              estado: str = "PUBLICADA") -> int:
    return C.publicar(api.dueno, asignatura="450002", numero=numero, pis=list(repartos), filas=_filas(repartos, desde),
                      nombre_archivo=f"inventado_450002_{numero}_{desde}.xlsx", conjunto=conjunto,
                      subida_por=subida_por, estado=estado)


def _la_412(api: Any) -> int:
    return _publicar(api, VARIAS_412, numero="412", desde=99100001, subida_por=A.VARIAS_CORREO)


def _registro(pi: str, tipo: str | None = OM, causa: str | None = None, accion: str | None = None) -> dict[str, Any]:
    return {"pi": pi, "tipo": tipo, "causa": causa or f"Causa inventada de {pi}.",
            "accion": accion or f"Acción inventada de {pi}."}


def _completo(tipos: dict[str, str]) -> list[dict[str, Any]]:
    return [_registro(pi, tipo) for pi, tipo in tipos.items()]


def _guardar(cliente: Any, carga: int, indicadores: list[dict[str, Any]], version: int = 0, **extra: Any) -> Any:
    return cliente.put(f"/api/cargas/{carga}/mejora/borrador", json={"version": version, "indicadores": indicadores,
                                                                       **extra})


def _declarar(cliente: Any, carga: int, version: int, **extra: Any) -> Any:
    return cliente.post(f"/api/cargas/{carga}/mejora/declaracion", json={"version": version, **extra})


def _leer(cliente: Any, carga: int) -> Any:
    return cliente.get(f"/api/cargas/{carga}/mejora")


def _conteos(api: Any) -> dict[str, int]:
    return {tabla: int(api.uno(f"SELECT count(*) FROM abet.{tabla}")) for tabla in TABLAS}


def _error(respuesta: Any, codigo: int, mensaje: str) -> None:
    assert respuesta.status_code == codigo, respuesta.text
    assert respuesta.json()["detail"] == mensaje
    assert respuesta.headers["cache-control"] == "no-store"


# BR-MEJORA-06, la ruta 14 y el borrador con una sola versión por carga

def test_br_mejora_06_una_carga_sin_texto_responde_nulos_y_el_profesor_puede_editar(api: Any) -> None:
    carga = _publicar(api)
    respuesta = _leer(api.sesion(A.DOCENTE_410), carga)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.headers["cache-control"] == "no-store"
    assert respuesta.json() == {"declaracion": None, "borrador": None, "borrador_pendiente": False,
                                "heredado_de": None, "puede_editar": True}


def test_br_mejora_06_un_borrador_parcial_se_acepta_y_la_ruta_14_lo_devuelve_por_pi(api: Any) -> None:
    carga = _la_412(api)
    cliente = api.sesion(A.VARIAS_CORREO)
    respuesta = _guardar(cliente, carga, [{"pi": "5.2", "tipo": OM, "causa": "La entrega coincidió con parciales."}])
    assert respuesta.status_code == 200, respuesta.text
    assert set(respuesta.json()) == {"version", "actualizado_en"} and respuesta.json()["version"] == 1
    assert respuesta.headers["cache-control"] == "no-store"
    cuerpo = _leer(cliente, carga).json()
    assert cuerpo["declaracion"] is None and cuerpo["borrador_pendiente"] is True
    assert cuerpo["borrador"]["version"] == 1
    assert cuerpo["borrador"]["actualizado_en"] == respuesta.json()["actualizado_en"]
    assert cuerpo["borrador"]["indicadores"] == [
        {"pi": "5.1", "tipo": BP, "causa": None, "accion": None},
        {"pi": "5.2", "tipo": OM, "causa": "La entrega coincidió con parciales.", "accion": None},
        {"pi": "5.3", "tipo": BP, "causa": None, "accion": None},
    ]


def test_br_mejora_06_un_pi_que_falta_en_el_arreglo_queda_nulo_y_la_version_sube(api: Any) -> None:
    carga = _publicar(api)
    cliente = api.sesion(A.DOCENTE_410)
    assert _guardar(cliente, carga, _completo({"5.1": OM, "5.2": OM, "5.3": OM})).json()["version"] == 1
    assert _guardar(cliente, carga, [_registro("5.2")], version=1).json()["version"] == 2
    indicadores = _leer(cliente, carga).json()["borrador"]["indicadores"]
    assert [(i["pi"], i["causa"] is None, i["accion"] is None) for i in indicadores] == [
        ("5.1", True, True), ("5.2", False, False), ("5.3", True, True)]
    assert api.uno("SELECT count(*) FROM abet.mejora_borrador_pi WHERE carga_id = %s", carga) == 3


def test_br_mejora_06_una_version_vieja_responde_409_con_el_borrador_guardado_y_no_cambia_nada(api: Any) -> None:
    carga = _publicar(api)
    cliente = api.sesion(A.DOCENTE_410)
    for version in range(3):
        assert _guardar(cliente, carga, [_registro("5.1", causa=f"Texto {version}.")], version).status_code == 200
    antes = api.dueno.execute("SELECT version, actualizado_en FROM abet.mejora_borrador").fetchall()
    respuesta = _guardar(cliente, carga, [_registro("5.1", causa="Otro texto.")], version=2)
    _error(respuesta, 409, "Otra pestaña guardó un texto más reciente.")
    borrador = respuesta.json()["borrador"]
    assert borrador["version"] == 3 and borrador["indicadores"][0]["causa"] == "Texto 2."
    assert api.dueno.execute("SELECT version, actualizado_en FROM abet.mejora_borrador").fetchall() == antes
    # Una versión 0 contra un borrador que ya existe también es vieja.
    _error(_guardar(cliente, carga, [_registro("5.1")], version=0), 409, "Otra pestaña guardó un texto más reciente.")


def test_br_mejora_06_el_coordinador_lee_sin_borrador_y_sin_poder_editar(api: Any) -> None:
    carga = _publicar(api)
    assert _guardar(api.sesion(A.DOCENTE_410), carga, [_registro("5.1")]).status_code == 200
    cuerpo = _leer(api.sesion(A.COORDINACION), carga).json()
    assert cuerpo == {"declaracion": None, "borrador": None, "borrador_pendiente": True, "heredado_de": None,
                      "puede_editar": False}
    assert "Causa inventada" not in _leer(api.sesion(A.COORDINACION), carga).text


# BR-MEJORA-05, el alcance y el orden 401, 403, 422 y 409

@pytest.mark.parametrize("metodo", ["GET", "PUT", "POST"])
def test_br_mejora_05_sin_sesion_cada_ruta_responde_401(api: Any, metodo: str) -> None:
    carga = _publicar(api)
    camino = {"GET": "mejora", "PUT": "mejora/borrador", "POST": "mejora/declaracion"}[metodo]
    respuesta = api.cliente().request(metodo, f"/api/cargas/{carga}/{camino}", content=b"no es json")
    assert (respuesta.status_code, respuesta.json()) == (401, VENCIDA)


@pytest.mark.parametrize("correo", [A.COORDINACION, A.DOCENTE_411])
@pytest.mark.parametrize("camino", ["mejora/borrador", "mejora/declaracion"])
def test_br_mejora_05_solo_el_profesor_asignado_escribe_aunque_el_cuerpo_no_sea_json(
        api: Any, correo: str, camino: str) -> None:
    carga = _publicar(api)
    metodo = "PUT" if camino.endswith("borrador") else "POST"
    respuesta = api.sesion(correo).request(metodo, f"/api/cargas/{carga}/{camino}", content=b"{no es json",
                                           headers={"content-type": "text/plain"})
    assert (respuesta.status_code, respuesta.json()) == (403, SIN_ALCANCE)
    assert _conteos(api) == dict.fromkeys(TABLAS, 0)


def test_br_mejora_05_una_carga_que_no_existe_recibe_el_mismo_403_en_las_tres_rutas(api: Any) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    for respuesta in (_leer(cliente, 999999), _guardar(cliente, 999999, []), _declarar(cliente, 999999, 1)):
        assert (respuesta.status_code, respuesta.json()) == (403, SIN_ALCANCE)


@pytest.mark.parametrize("camino", ["mejora/borrador", "mejora/declaracion"])
@pytest.mark.parametrize("contenido", [b"{no es json", b"[]", b'"texto"', b"", b'{"version": "1", "indicadores": []}',
                                       b'{"version": true, "indicadores": []}', b'{"version": -1, "indicadores": []}'])
def test_br_mejora_07_un_cuerpo_sin_la_forma_esperada_responde_422(api: Any, camino: str, contenido: bytes) -> None:
    carga = _publicar(api)
    metodo = "PUT" if camino.endswith("borrador") else "POST"
    if metodo == "POST":
        # La ruta 16 admite solo version, así que su cuerpo de otra forma no trae indicadores.
        contenido = contenido.replace(b', "indicadores": []', b"")
    respuesta = api.sesion(A.DOCENTE_410).request(metodo, f"/api/cargas/{carga}/{camino}", content=contenido,
                                                  headers={"content-type": "application/json"})
    _error(respuesta, 422, "La petición no tiene la forma esperada.")
    assert _conteos(api) == dict.fromkeys(TABLAS, 0)


@pytest.mark.parametrize("cuerpo", [
    {"version": 0},
    {"indicadores": []},
    {"version": 0, "indicadores": {}},
    {"version": 0, "indicadores": ["5.1"]},
    {"version": 0, "indicadores": [{"tipo": OM, "causa": "Algo."}]},
    {"version": 0, "indicadores": [{"pi": 5.1, "tipo": OM}]},
    {"version": 0, "indicadores": [{"pi": "5.1", "tipo": OM, "causa": 7}]},
])
def test_br_mejora_07_un_borrador_con_campos_de_otro_tipo_responde_422(api: Any, cuerpo: dict[str, Any]) -> None:
    carga = _publicar(api)
    respuesta = api.sesion(A.DOCENTE_410).put(f"/api/cargas/{carga}/mejora/borrador", json=cuerpo)
    _error(respuesta, 422, "La petición no tiene la forma esperada.")


@pytest.mark.parametrize("clave", ["responsable", "plazo", "estado", "otra"])
def test_br_mejora_07_una_clave_fuera_del_contrato_responde_422_en_la_raiz_y_en_el_indicador(
        api: Any, clave: str) -> None:
    carga = _publicar(api)
    cliente = api.sesion(A.DOCENTE_410)
    mensaje = "El cuerpo trae claves que esta ruta no admite."
    _error(_guardar(cliente, carga, [_registro("5.1")], **{clave: "x"}), 422, mensaje)
    _error(_guardar(cliente, carga, [{**_registro("5.1"), clave: "x"}]), 422, mensaje)
    _error(_declarar(cliente, carga, 0, **{clave: "x"}), 422, mensaje)
    _error(_declarar(cliente, carga, 0, indicadores=[]), 422, mensaje)
    assert _conteos(api) == dict.fromkeys(TABLAS, 0)


def test_br_mejora_07_un_pi_repetido_o_ajeno_responde_422_y_no_guarda_nada(api: Any) -> None:
    carga = _publicar(api)
    cliente = api.sesion(A.DOCENTE_410)
    _error(_guardar(cliente, carga, [_registro("5.1"), _registro("5.1")]), 422,
           "Cada indicador va una sola vez en el cuerpo.")
    _error(_guardar(cliente, carga, [_registro("5.1"), _registro("2.1")]), 422,
           "El indicador 2.1 no pertenece a esta carga.")
    assert _conteos(api) == dict.fromkeys(TABLAS, 0)


def test_br_mejora_04_un_pi_sin_dato_no_admite_registro(api: Any) -> None:
    carga = _publicar(api, SIN_5_3)
    _error(_guardar(api.sesion(A.DOCENTE_410), carga, [_registro("5.1"), _registro("5.3", None)]), 422,
           "El indicador 5.3 no lleva registro porque su semáforo no tiene dato.")
    assert _conteos(api) == dict.fromkeys(TABLAS, 0)


@pytest.mark.parametrize(("pi", "tipo"), [("5.2", BP), ("5.1", OM), ("5.1", None), ("5.2", "OTRO")])
def test_br_mejora_03_el_tipo_lo_fija_el_semaforo(api: Any, pi: str, tipo: str | None) -> None:
    carga = _la_412(api)
    _error(_guardar(api.sesion(A.VARIAS_CORREO), carga, [_registro(pi, tipo)]), 422,
           "El tipo de registro de cada indicador lo fija su semáforo.")
    assert _conteos(api) == dict.fromkeys(TABLAS, 0)


# BR-MEJORA-08 y BR-MEJORA-10, el texto

@pytest.mark.parametrize(("texto", "mensaje"), [
    ("a" * 801, "Cada campo admite hasta 800 caracteres."),
    ("Entrega tardía\u0007", "El texto trae caracteres que no se pueden guardar."),
    ("Entrega\rtardía", "El texto trae caracteres que no se pueden guardar."),
    ("99000004 no entregó", "La declaración no puede llevar códigos ni correos. Describa las causas y las acciones "
                            "sin datos de estudiantes."),
    ("escribir a alguien@example.invalid", "La declaración no puede llevar códigos ni correos. Describa las causas y "
                                           "las acciones sin datos de estudiantes."),
    ("código:99000004.", "La declaración no puede llevar códigos ni correos. Describa las causas y las acciones sin "
                         "datos de estudiantes."),
])
@pytest.mark.parametrize("campo", ["causa", "accion"])
def test_br_mejora_08_y_10_un_texto_invalido_responde_422_sin_repetirlo_y_no_guarda_nada(
        api: Any, texto: str, mensaje: str, campo: str, caplog: pytest.LogCaptureFixture) -> None:
    carga = _publicar(api)
    registro = {**_registro("5.1"), campo: texto}
    respuesta = _guardar(api.sesion(A.DOCENTE_410), carga, [registro, _registro("5.2")])
    _error(respuesta, 422, mensaje)
    assert texto not in respuesta.text and texto not in caplog.text
    assert _conteos(api) == dict.fromkeys(TABLAS, 0)


@pytest.mark.parametrize("texto", ["Resolución 990000041 del periodo", "Entrega del 18/11/2026 en parciales",
                                   "a" * 800, "Dos\tcolumnas\ny dos líneas", "Fecha 2026-11-18 y hora 15:10"])
def test_br_mejora_08_y_10_un_texto_valido_se_guarda(api: Any, texto: str) -> None:
    carga = _publicar(api)
    respuesta = _guardar(api.sesion(A.DOCENTE_410), carga, [_registro("5.1", causa=texto)])
    assert respuesta.status_code == 200, respuesta.text
    assert api.uno("SELECT causa FROM abet.mejora_borrador_pi WHERE carga_id = %s", carga) == texto


def test_br_mejora_08_el_texto_se_normaliza_a_nfc_con_saltos_de_linea_n_y_cuenta_puntos_de_codigo(api: Any) -> None:
    carga = _publicar(api)
    descompuesto = unicodedata.normalize("NFD", "Revisión") + "\r\nsegunda línea"
    assert descompuesto != unicodedata.normalize("NFC", descompuesto)
    # 800 puntos de código en NFC son más de 800 en NFD, y el tope se cuenta después de normalizar.
    largo = unicodedata.normalize("NFD", "á" * 800)
    assert len(largo) == 1600
    respuesta = _guardar(api.sesion(A.DOCENTE_410), carga, [_registro("5.1", causa=descompuesto, accion=largo)])
    assert respuesta.status_code == 200, respuesta.text
    causa, accion = api.dueno.execute("SELECT causa, accion FROM abet.mejora_borrador_pi").fetchone()
    assert causa == "Revisión\nsegunda línea" and unicodedata.is_normalized("NFC", causa)
    assert accion == "á" * 800


def test_br_mejora_06_un_texto_vacio_se_guarda_como_nulo(api: Any) -> None:
    carga = _publicar(api)
    cliente = api.sesion(A.DOCENTE_410)
    assert _guardar(cliente, carga, [_registro("5.1", causa="", accion="   ") | {"causa": ""}]).status_code == 200
    causa, accion = api.dueno.execute("SELECT causa, accion FROM abet.mejora_borrador_pi").fetchone()
    assert (causa, accion) == (None, "   ")


# BR-MEJORA-05, las cargas que no están publicadas

def test_br_mejora_05_una_carga_rechazada_responde_409_sin_reemplazada_por(api: Any) -> None:
    carga = C.rechazar(api.dueno, motivo="PI_DEL_PLAN_AUSENTE", nombre_archivo="sin_5_2_410.xlsx", pi="5.2")
    cliente = api.sesion(A.DOCENTE_410)
    for respuesta in (_guardar(cliente, carga, [_registro("5.1")]), _declarar(cliente, carga, 1)):
        _error(respuesta, 409, "La carga no está publicada y no admite causas ni acciones.")
        assert set(respuesta.json()) == {"detail"}
    assert _leer(cliente, carga).status_code == 200


def test_br_mejora_05_una_carga_reemplazada_responde_409_con_reemplazada_por(api: Any) -> None:
    anterior = _publicar(api)
    nueva = C.con_error(api.dueno, anterior)
    cliente = api.sesion(A.DOCENTE_410)
    for respuesta in (_guardar(cliente, anterior, [_registro("5.1")]), _declarar(cliente, anterior, 1)):
        _error(respuesta, 409, "La carga no está publicada y no admite causas ni acciones.")
        assert respuesta.json() == {"detail": "La carga no está publicada y no admite causas ni acciones.",
                                    "reemplazada_por": nueva}
    assert _conteos(api) == dict.fromkeys(TABLAS, 0)


# BR-MEJORA-09, la declaración

def test_br_mejora_09_la_412_se_declara_con_dos_buenas_practicas_una_oportunidad_y_la_foto(api: Any) -> None:
    carga = _la_412(api)
    cliente = api.sesion(A.VARIAS_CORREO)
    assert _guardar(cliente, carga, _completo(TIPOS_412)).status_code == 200
    respuesta = _declarar(cliente, carga, 1)
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.headers["cache-control"] == "no-store"
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"declarada_en", "indicadores"}
    assert cuerpo["indicadores"] == [
        {"pi": pi, "tipo": tipo, "causa": f"Causa inventada de {pi}.", "accion": f"Acción inventada de {pi}.",
         "estado": "PROPUESTA"} for pi, tipo in TIPOS_412.items()]
    filas = api.dueno.execute(
        "SELECT p.codigo, d.tipo, d.logro_pct, d.meta_pct, d.semaforo FROM abet.mejora_declaracion_pi d"
        " JOIN abet.pi p USING (pi_id) ORDER BY p.numero").fetchall()
    assert [(pi, tipo, float(logro), float(meta), semaforo) for pi, tipo, logro, meta, semaforo in filas] == [
        ("5.1", BP, 81.8, 80.0, "VERDE"), ("5.2", OM, 54.5, 80.0, "ROJO"), ("5.3", BP, 90.9, 80.0, "VERDE")]
    cabecera = api.dueno.execute("SELECT carga_id, version_borrador, declarada_por FROM abet.mejora_declaracion")
    assert cabecera.fetchall() == [(carga, 1, C.usuario(api.dueno, A.VARIAS_CORREO))]
    leida = _leer(cliente, carga).json()
    assert leida["declaracion"] == cuerpo and leida["borrador_pendiente"] is False
    assert leida["borrador"]["version"] == 1


def test_br_mejora_09_corregir_deja_la_anterior_vigente_hasta_declarar_la_nueva(api: Any) -> None:
    carga = _publicar(api)
    cliente = api.sesion(A.DOCENTE_410)
    tipos = {"5.1": OM, "5.2": OM, "5.3": OM}
    _guardar(cliente, carga, _completo(tipos))
    assert _declarar(cliente, carga, 1).status_code == 201
    corregido = [_registro("5.1", causa="Causa corregida.")] + _completo(tipos)[1:]
    assert _guardar(cliente, carga, corregido, version=1).status_code == 200
    leida = _leer(cliente, carga).json()
    assert leida["borrador_pendiente"] is True
    assert leida["declaracion"]["indicadores"][0]["causa"] == "Causa inventada de 5.1."
    assert _declarar(cliente, carga, 2).status_code == 201
    leida = _leer(cliente, carga).json()
    assert leida["borrador_pendiente"] is False
    assert leida["declaracion"]["indicadores"][0]["causa"] == "Causa corregida."
    assert {i["estado"] for i in leida["declaracion"]["indicadores"]} == {"PROPUESTA"}
    assert api.uno("SELECT count(*) FROM abet.mejora_declaracion WHERE carga_id = %s", carga) == 2
    assert api.uno("SELECT count(*) FROM abet.mejora_declaracion_pi WHERE carga_id = %s", carga) == 6


def test_br_mejora_09_el_coordinador_lee_la_declaracion_vigente_sin_el_borrador(api: Any) -> None:
    carga = _publicar(api)
    cliente = api.sesion(A.DOCENTE_410)
    _guardar(cliente, carga, _completo({"5.1": OM, "5.2": OM, "5.3": OM}))
    _declarar(cliente, carga, 1)
    _guardar(cliente, carga, [_registro("5.1", causa="Borrador posterior.")], version=1)
    cuerpo = _leer(api.sesion(A.COORDINACION), carga).json()
    assert cuerpo["borrador"] is None and cuerpo["puede_editar"] is False and cuerpo["borrador_pendiente"] is True
    assert [i["causa"] for i in cuerpo["declaracion"]["indicadores"]][0] == "Causa inventada de 5.1."
    assert "Borrador posterior" not in _leer(api.sesion(A.COORDINACION), carga).text


@pytest.mark.parametrize("cambio", [
    {"accion": None}, {"causa": None}, {"accion": "   "}, {"causa": "　\n\t"}, "sin registro"])
def test_br_mejora_09_una_declaracion_incompleta_responde_422_y_no_crea_filas(api: Any, cambio: Any) -> None:
    carga = _la_412(api)
    cliente = api.sesion(A.VARIAS_CORREO)
    registros = _completo(TIPOS_412)
    registros = registros[:2] if cambio == "sin registro" else registros[:2] + [{**registros[2], **cambio}]
    assert _guardar(cliente, carga, registros).status_code == 200
    _error(_declarar(cliente, carga, 1), 422, "Complete la causa y la acción de cada indicador.")
    assert api.uno("SELECT count(*) FROM abet.mejora_declaracion") == 0


def test_br_mejora_09_la_version_0_sin_borrador_responde_422(api: Any) -> None:
    carga = _publicar(api)
    _error(_declarar(api.sesion(A.DOCENTE_410), carga, 0), 422, "Complete la causa y la acción de cada indicador.")
    assert api.uno("SELECT count(*) FROM abet.mejora_declaracion") == 0


def test_br_mejora_09_una_version_distinta_de_la_guardada_responde_409_con_el_borrador(api: Any) -> None:
    carga = _publicar(api)
    cliente = api.sesion(A.DOCENTE_410)
    _guardar(cliente, carga, _completo({"5.1": OM, "5.2": OM, "5.3": OM}))
    respuesta = _declarar(cliente, carga, 2)
    _error(respuesta, 409, "El borrador cambió después de este guardado. Guarde otra vez antes de declarar.")
    assert respuesta.json()["borrador"]["version"] == 1
    assert api.uno("SELECT count(*) FROM abet.mejora_declaracion") == 0


def test_br_mejora_09_una_regla_sin_definir_responde_409_que_manda_sobre_el_422(api: Any) -> None:
    C.conjunto_aprobado(api.dueno, "R-PRUEBA-SIN-META", meta_logro=None, nivel_esperado=3, corte_rojo=0.75)
    carga = _publicar(api, conjunto="R-PRUEBA-SIN-META")
    cliente = api.sesion(A.DOCENTE_410)
    for version in (0, 1):
        _error(_declarar(cliente, carga, version), 409,
               "El conjunto de reglas no define la meta o el nivel esperado. La declaración espera a la Coordinación.")
    assert api.uno("SELECT count(*) FROM abet.mejora_declaracion") == 0


def test_br_mejora_04_un_pi_sin_calificaciones_no_exige_registro_y_no_tiene_fila(api: Any) -> None:
    carga = _publicar(api, SIN_5_3)
    cliente = api.sesion(A.DOCENTE_410)
    _guardar(cliente, carga, _completo({"5.1": OM, "5.2": OM}))
    respuesta = _declarar(cliente, carga, 1)
    assert respuesta.status_code == 201, respuesta.text
    assert [i["pi"] for i in respuesta.json()["indicadores"]] == ["5.1", "5.2"]
    assert api.uno("SELECT count(*) FROM abet.mejora_declaracion_pi") == 2


def test_br_mejora_04_una_carga_sin_ningun_calificado_se_declara_con_el_arreglo_vacio(api: Any) -> None:
    carga = _publicar(api, {pi: [0, 0, 0, 0, 11] for pi in ("5.1", "5.2", "5.3")})
    cliente = api.sesion(A.DOCENTE_410)
    assert _guardar(cliente, carga, []).json()["version"] == 1
    respuesta = _declarar(cliente, carga, 1)
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["indicadores"] == []
    assert _leer(cliente, carga).json()["borrador"]["indicadores"] == []


def test_br_mejora_09_un_analisis_que_no_cabe_en_el_r17_responde_422(api: Any) -> None:
    carga = _publicar(api)
    cliente = api.sesion(A.DOCENTE_410)
    registros = _completo({"5.1": OM, "5.2": OM, "5.3": OM})
    registros[0]["causa"] = ("x\n" * 300)[:800]
    assert _guardar(cliente, carga, registros).status_code == 200
    _error(_declarar(cliente, carga, 1), 422,
           "El análisis no cabe en el R-17. Acorte la causa o la acción de algún indicador.")
    assert api.uno("SELECT count(*) FROM abet.mejora_declaracion") == 0


def test_br_mejora_09_tres_pi_en_el_tope_de_800_sin_saltos_caben(api: Any) -> None:
    carga = _publicar(api)
    cliente = api.sesion(A.DOCENTE_410)
    registros = [_registro(pi, OM, "c" * 800, "a" * 800) for pi in ("5.1", "5.2", "5.3")]
    assert _guardar(cliente, carga, registros).status_code == 200
    assert _declarar(cliente, carga, 1).status_code == 201


# La cabida usa las funciones de abet_carga/r17.py

def test_br_mejora_09_la_cabida_usa_el_alto_que_calcula_r17() -> None:
    assert mejora.cabe_en_el_r17("linea\n" * 28 + "linea")
    assert not mejora.cabe_en_el_r17("linea\n" * 29 + "linea")


# BR-MEJORA-10, ninguna respuesta trae datos de estudiantes

def test_br_mejora_10_las_respuestas_no_traen_codigos_ni_correos_de_estudiantes(api: Any) -> None:
    carga = _publicar(api)
    cliente = api.sesion(A.DOCENTE_410)
    respuestas = [_leer(cliente, carga), _guardar(cliente, carga, _completo({"5.1": OM, "5.2": OM, "5.3": OM})),
                  _declarar(cliente, carga, 1), _leer(cliente, carga)]
    for respuesta in respuestas:
        assert respuesta.status_code in (200, 201), respuesta.text
        assert respuesta.headers["cache-control"] == "no-store"
        assert "99000" not in respuesta.text and "@" not in respuesta.text


def test_las_rutas_14_a_16_figuran_en_el_esquema_openapi(api: Any) -> None:
    caminos = api.cliente().get("/api/openapi.json").json()["paths"]
    assert "get" in caminos["/api/cargas/{carga_id}/mejora"]
    assert "put" in caminos["/api/cargas/{carga_id}/mejora/borrador"]
    assert "post" in caminos["/api/cargas/{carga_id}/mejora/declaracion"]
