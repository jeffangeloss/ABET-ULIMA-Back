"""Pruebas de GET /api/cargas/{carga_id}/indicadores, la ruta 13 de la spec 005 (T031).

Cada prueba nombra la regla de negocio (business rule, BR) de specs/features/mejora/mejora.spec.md que comprueba, con
lo que debe pasar y lo que no debe pasar (AGENTS.md, regla 8). Las cargas se siembran con publicar() de
tests/cargas_de_prueba.py y la conexión del dueño de una copia de la base desechable, como en las pruebas de la ruta 12,
así que ningún export nuevo entra a tests/datos_inventados/. Cada porcentaje esperado sale a mano de su reparto por
nivel, con el redondeo a un decimal de la vista. La sección 13.2 del contrato del Front fija la forma de la respuesta.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
import pytest

from abet_carga import constancia
from app import permisos
from app.rutas import resultados as lectura


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

INSTRUMENTO = "Trabajo Integrador"
SEMAFORO = "R-PRUEBA-SEMAFORO"
NO_PUBLICADA = {"detail": "La carga no está publicada y no tiene semáforo."}
SIN_ALCANCE = {"detail": "La sección no está a su cargo."}
VENCIDA = {"detail": "La sesión venció. Ingrese otra vez."}
CLAVES = {"carga_id", "estado", "provisional", "conjunto_reglas", "conjunto_reglas_estado", "parametros_pendientes",
          "meta_pct", "corte_rojo_pct", "indicadores"}
CLAVES_INDICADOR = {"so", "pi", "instrumento", "nivel_esperado", "estudiantes_por_nivel", "logrados", "calificados",
                    "sin_evidencia", "total", "pct_sobre_calificados", "pct_sobre_total", "meta_pct", "en_meta",
                    "semaforo", "hallazgo", "tipo_registro"}
# Repartos por nivel (niveles 1 a 4 y, si lo hay, un quinto valor con los estudiantes sin evidencia).
CORRECTO_410 = {"5.1": [1, 3, 4, 3], "5.2": [1, 3, 4, 3], "5.3": [1, 2, 5, 3]}
VARIAS_412 = {"5.1": [1, 1, 5, 4], "5.2": [2, 3, 4, 2], "5.3": [0, 1, 4, 6]}
OTROS = {"5.1": [1, 3, 4, 3, 0], "5.2": [1, 3, 4, 3, 0]}


# Ayudas

def _filas(repartos: dict[str, list[int]], desde: int) -> list[Any]:
    """Filas inventadas que dan en cada PI el reparto pedido, con códigos consecutivos desde «desde»."""
    columnas = []
    for reparto in repartos.values():
        niveles = [nivel for nivel, cantidad in zip((1, 2, 3, 4), reparto[:4], strict=True) for _ in range(cantidad)]
        columnas.append(niveles + [None] * (reparto[4] if len(reparto) > 4 else 0))
    assert len({len(columna) for columna in columnas}) == 1, "todos los PI deben sumar las mismas filas"
    return [C.Fila(2 + i, str(desde + i), tuple(columna[i] for columna in columnas)) for i in range(len(columnas[0]))]


def _publicar(api: Any, repartos: dict[str, list[int]], *, numero: str = "410", desde: int = 99000001,
              conjunto: str = C.BORRADOR, subida_por: str | None = A.DOCENTE_410, estado: str = "PUBLICADA") -> int:
    return C.publicar(api.dueno, asignatura="450002", numero=numero, pis=list(repartos), filas=_filas(repartos, desde),
                      nombre_archivo=f"inventado_450002_{numero}_{desde}.xlsx", conjunto=conjunto,
                      subida_por=subida_por, estado=estado)


def _pedir(cliente: Any, carga_id: int | str) -> Any:
    return cliente.get(f"/api/cargas/{carga_id}/indicadores")


def _cuerpo(cliente: Any, carga_id: int) -> dict[str, Any]:
    respuesta = _pedir(cliente, carga_id)
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def _indicador(cuerpo: dict[str, Any], pi: str) -> dict[str, Any]:
    [indicador] = [i for i in cuerpo["indicadores"] if i["pi"] == pi]
    return indicador


def _estado(cuerpo: dict[str, Any]) -> list[tuple[str, Any, str, Any]]:
    return [(i["pi"], i["pct_sobre_calificados"], i["semaforo"], i["tipo_registro"]) for i in cuerpo["indicadores"]]


def _esperado(pi: str, reparto: list[int], pct: float, semaforo: str, tipo: str) -> dict[str, Any]:
    calificados = sum(reparto[:4])
    texto = f"{pct:.1f}".replace(".", ",")
    return {"so": 5, "pi": pi, "instrumento": INSTRUMENTO, "nivel_esperado": 3, "estudiantes_por_nivel": reparto[:4],
            "logrados": sum(reparto[2:4]), "calificados": calificados, "sin_evidencia": 0, "total": calificados,
            "pct_sobre_calificados": pct, "pct_sobre_total": pct, "meta_pct": 80.0, "en_meta": semaforo == "VERDE",
            "semaforo": semaforo, "hallazgo": f"{pi}: {texto} % en Satisfactorio o más, meta 80,0 %",
            "tipo_registro": tipo}


def _semaforo(api: Any, *, corte: float | None = 0.75) -> None:
    """R-PRUEBA-SEMAFORO, APROBADO y completo, con META_LOGRO 0,80, NIVEL_ESPERADO 3 y el corte pedido."""
    C.conjunto_aprobado(api.dueno, SEMAFORO, meta_logro=0.80, nivel_esperado=3, corte_rojo=corte)


# BR-MEJORA-01, la forma de la respuesta con las cifras de la vista

def test_br_mejora_01_la_410_con_el_borrador_trae_tres_rojos_con_oportunidad_de_mejora(api: Any) -> None:
    carga = _publicar(api, CORRECTO_410)
    respuesta = _pedir(api.sesion(A.DOCENTE_410), carga)
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.headers["cache-control"] == "no-store"
    assert respuesta.json() == {
        "carga_id": carga,
        "estado": "PUBLICADA",
        "provisional": True,
        "conjunto_reglas": "R-2026-BORRADOR",
        "conjunto_reglas_estado": "BORRADOR",
        "parametros_pendientes": constancia.armar(api.dueno, carga)["parametros_pendientes"],
        "meta_pct": 80.0,
        "corte_rojo_pct": None,
        "indicadores": [
            _esperado("5.1", [1, 3, 4, 3], 63.6, "ROJO", "OPORTUNIDAD_MEJORA"),
            _esperado("5.2", [1, 3, 4, 3], 63.6, "ROJO", "OPORTUNIDAD_MEJORA"),
            _esperado("5.3", [1, 2, 5, 3], 72.7, "ROJO", "OPORTUNIDAD_MEJORA"),
        ],
    }


def test_br_mejora_01_la_412_de_450002_trae_verde_rojo_y_verde_con_dos_buenas_practicas(api: Any) -> None:
    carga = _publicar(api, VARIAS_412, numero="412", desde=99100001, subida_por=A.VARIAS_CORREO)
    cuerpo = _cuerpo(api.sesion(A.VARIAS_CORREO), carga)
    assert cuerpo["indicadores"] == [
        _esperado("5.1", [1, 1, 5, 4], 81.8, "VERDE", "BUENA_PRACTICA"),
        _esperado("5.2", [2, 3, 4, 2], 54.5, "ROJO", "OPORTUNIDAD_MEJORA"),
        _esperado("5.3", [0, 1, 4, 6], 90.9, "VERDE", "BUENA_PRACTICA"),
    ]


def test_br_mejora_01_cada_objeto_trae_solo_las_claves_de_la_lista_cerrada_y_ningun_dato_de_estudiante(api: Any) -> None:
    carga = _publicar(api, CORRECTO_410)
    respuesta = _pedir(api.sesion(A.DOCENTE_410), carga)
    cuerpo = respuesta.json()
    assert set(cuerpo) == CLAVES
    assert all(set(indicador) == CLAVES_INDICADOR for indicador in cuerpo["indicadores"])
    for prohibido in ("subida_por", "nombre_archivo", "sha256", "inventado_", "99000", "@", "trato_sin_evidencia"):
        assert prohibido not in respuesta.text, prohibido


def test_br_mejora_01_los_porcentajes_viajan_como_numeros_json(api: Any) -> None:
    carga = _publicar(api, CORRECTO_410)
    cuerpo = _cuerpo(api.sesion(A.DOCENTE_410), carga)
    assert isinstance(cuerpo["meta_pct"], float)
    for indicador in cuerpo["indicadores"]:
        for clave in ("pct_sobre_calificados", "pct_sobre_total", "meta_pct"):
            assert isinstance(indicador[clave], float), (indicador["pi"], clave)


def test_br_mejora_01_los_indicadores_van_por_numero_de_pi_y_el_5_10_queda_despues_del_5_2(api: Any) -> None:
    api.dueno.execute(
        "INSERT INTO abet.pi (catalogo_version_id, so_id, so_numero, numero, codigo, descripcion)"
        " SELECT so.catalogo_version_id, so.so_id, 5, 10, '5.10', 'PI inventado de prueba'"
        " FROM abet.so so JOIN abet.catalogo_version cv USING (catalogo_version_id)"
        " WHERE cv.codigo = 'AMB-2026' AND so.numero = 5")
    C.plan(api.dueno, "450002", ["5.10"])
    carga = _publicar(api, {**CORRECTO_410, "5.10": [0, 0, 5, 6]})
    cuerpo = _cuerpo(api.sesion(A.DOCENTE_410), carga)
    assert [i["pi"] for i in cuerpo["indicadores"]] == ["5.1", "5.2", "5.3", "5.10"]
    assert _estado(cuerpo)[-1] == ("5.10", 100.0, "VERDE", "BUENA_PRACTICA")


# BR-MEJORA-02, el semáforo con el corte rojo de abet.parametro_valor

def test_br_mejora_02_el_80_justo_en_la_meta_queda_en_verde_con_buena_practica(api: Any) -> None:
    carga = _publicar(api, {**OTROS, "5.3": [0, 2, 5, 3, 1]})
    indicador = _indicador(_cuerpo(api.sesion(A.DOCENTE_410), carga), "5.3")
    assert (indicador["estudiantes_por_nivel"], indicador["logrados"], indicador["calificados"],
            indicador["sin_evidencia"], indicador["pct_sobre_calificados"], indicador["pct_sobre_total"]) == (
        [0, 2, 5, 3], 8, 10, 1, 80.0, 72.7)
    assert (indicador["en_meta"], indicador["semaforo"], indicador["tipo_registro"]) == (True, "VERDE", "BUENA_PRACTICA")
    assert indicador["hallazgo"] == "5.3: 80,0 % en Satisfactorio o más, meta 80,0 %"


@pytest.mark.parametrize(("reparto", "logro", "semaforo"), [
    ([1, 1, 4, 3, 2], 77.8, "AMBAR"),
    ([0, 2, 4, 2, 3], 75.0, "AMBAR"),
    ([1, 2, 5, 3, 0], 72.7, "ROJO"),
])
def test_br_mejora_02_con_corte_rojo_definido_la_banda_ambar_va_del_corte_a_debajo_de_la_meta(
        api: Any, reparto: list[int], logro: float, semaforo: str) -> None:
    _semaforo(api)
    carga = _publicar(api, {**OTROS, "5.3": reparto}, conjunto=SEMAFORO)
    cuerpo = _cuerpo(api.sesion(A.DOCENTE_410), carga)
    assert (cuerpo["meta_pct"], cuerpo["corte_rojo_pct"], cuerpo["provisional"]) == (80.0, 75.0, False)
    assert cuerpo["parametros_pendientes"] == []
    indicador = _indicador(cuerpo, "5.3")
    assert (indicador["pct_sobre_calificados"], indicador["semaforo"], indicador["tipo_registro"]) == (
        logro, semaforo, "OPORTUNIDAD_MEJORA")


def test_br_mejora_02_el_corte_rojo_sale_de_parametro_valor_en_porcentaje(api: Any) -> None:
    _semaforo(api, corte=0.78)
    carga = _publicar(api, {**OTROS, "5.3": [1, 1, 4, 3, 2]}, conjunto=SEMAFORO)
    cliente = api.sesion(A.DOCENTE_410)
    cuerpo = _cuerpo(cliente, carga)
    assert (cuerpo["corte_rojo_pct"], _indicador(cuerpo, "5.3")["semaforo"]) == (78.0, "ROJO")
    api.dueno.execute("UPDATE abet.parametro_valor pv SET valor_numero = 0.775 FROM abet.conjunto_reglas cr"
                      " WHERE cr.conjunto_reglas_id = pv.conjunto_reglas_id AND cr.version = %s"
                      " AND pv.clave = 'CORTE_ROJO'", (SEMAFORO,))
    cuerpo = _cuerpo(cliente, carga)
    assert (cuerpo["corte_rojo_pct"], _indicador(cuerpo, "5.3")["semaforo"]) == (77.5, "AMBAR")


def test_br_mejora_02_con_corte_rojo_pendiente_no_hay_ambar(api: Any) -> None:
    carga = _publicar(api, {**OTROS, "5.3": [1, 1, 4, 3, 2]})
    cuerpo = _cuerpo(api.sesion(A.DOCENTE_410), carga)
    assert cuerpo["corte_rojo_pct"] is None
    indicador = _indicador(cuerpo, "5.3")
    assert (indicador["estudiantes_por_nivel"], indicador["logrados"], indicador["calificados"],
            indicador["sin_evidencia"], indicador["pct_sobre_calificados"], indicador["pct_sobre_total"]) == (
        [1, 1, 4, 3], 7, 9, 2, 77.8, 63.6)
    assert indicador["semaforo"] == "ROJO"


def test_br_mejora_02_con_corte_rojo_pendiente_en_un_conjunto_aprobado_tampoco_hay_ambar(api: Any) -> None:
    _semaforo(api, corte=None)
    carga = _publicar(api, {**OTROS, "5.3": [1, 1, 4, 3, 2]}, conjunto=SEMAFORO)
    cuerpo = _cuerpo(api.sesion(A.DOCENTE_410), carga)
    assert (cuerpo["corte_rojo_pct"], cuerpo["parametros_pendientes"]) == (None, ["CORTE_ROJO"])
    assert _indicador(cuerpo, "5.3")["semaforo"] == "ROJO"


# BR-MEJORA-03, SIN_DATO y el tipo de registro nulo

def test_br_mejora_03_un_pi_sin_calificaciones_sale_sin_dato_y_sin_tipo_de_registro(api: Any) -> None:
    carga = _publicar(api, {**OTROS, "5.3": [0, 0, 0, 0, 11]})
    cuerpo = _cuerpo(api.sesion(A.DOCENTE_410), carga)
    indicador = _indicador(cuerpo, "5.3")
    assert (indicador["pct_sobre_calificados"], indicador["pct_sobre_total"], indicador["sin_evidencia"],
            indicador["en_meta"], indicador["semaforo"], indicador["tipo_registro"]) == (
        None, 0.0, 11, None, "SIN_DATO", None)
    assert indicador["hallazgo"] == "5.3: sin calificaciones en esta carga."
    assert _estado(cuerpo)[:2] == [("5.1", 63.6, "ROJO", "OPORTUNIDAD_MEJORA"),
                                   ("5.2", 63.6, "ROJO", "OPORTUNIDAD_MEJORA")]


@pytest.mark.parametrize(("parametro", "cambios"), [
    ("NIVEL_ESPERADO", {"nivel_esperado": None}),
    ("META_LOGRO", {"meta_logro": None}),
])
def test_br_mejora_03_un_parametro_sin_definir_deja_sin_dato_y_responde_200(
        api: Any, parametro: str, cambios: dict[str, Any]) -> None:
    version = f"R-PRUEBA-SIN-{parametro}"
    C.conjunto_aprobado(api.dueno, version, **{"meta_logro": 0.80, "nivel_esperado": 3, "corte_rojo": 0.75, **cambios})
    carga = _publicar(api, CORRECTO_410, conjunto=version)
    cuerpo = _cuerpo(api.sesion(A.DOCENTE_410), carga)
    assert parametro in cuerpo["parametros_pendientes"] and cuerpo["provisional"] is True
    assert [(i["semaforo"], i["tipo_registro"]) for i in cuerpo["indicadores"]] == [("SIN_DATO", None)] * 3
    assert [i["hallazgo"] for i in cuerpo["indicadores"]] == [
        f"{pi}: el conjunto de reglas no define la meta o el nivel esperado." for pi in ("5.1", "5.2", "5.3")]
    assert cuerpo["meta_pct"] == (None if parametro == "META_LOGRO" else 80.0)


def test_br_mejora_03_un_conjunto_con_todo_pendiente_responde_200_sin_dato(api: Any) -> None:
    C.conjunto_pendiente(api.dueno, "R-PRUEBA-PENDIENTE")
    carga = _publicar(api, CORRECTO_410, conjunto="R-PRUEBA-PENDIENTE")
    cuerpo = _cuerpo(api.sesion(A.DOCENTE_410), carga)
    assert (cuerpo["meta_pct"], cuerpo["corte_rojo_pct"]) == (None, None)
    assert {i["semaforo"] for i in cuerpo["indicadores"]} == {"SIN_DATO"}


# BR-MEJORA-05 y BR-ACCESO-08, el orden 401, 403 y 409

def test_br_mejora_05_sin_sesion_responde_401_aunque_la_carga_no_este_publicada(api: Any) -> None:
    carga = C.rechazar(api.dueno, motivo="PI_DEL_PLAN_AUSENTE", nombre_archivo="sin_5_2_410.xlsx", pi="5.2")
    for pedida in (carga, _publicar(api, CORRECTO_410), 999999):
        respuesta = _pedir(api.cliente(), pedida)
        assert (respuesta.status_code, respuesta.json()) == (401, VENCIDA)
        assert respuesta.headers["cache-control"] == "no-store"


def test_br_acceso_08_una_carga_ajena_y_una_inexistente_reciben_el_mismo_403(api: Any) -> None:
    carga = _publicar(api, CORRECTO_410)
    ajena = _pedir(api.sesion(A.DOCENTE_411), carga)
    inexistente = _pedir(api.sesion(A.DOCENTE_410), 999999)
    assert (ajena.status_code, ajena.json()) == (403, SIN_ALCANCE)
    assert (inexistente.status_code, inexistente.json()) == (403, SIN_ALCANCE)
    assert ajena.headers["cache-control"] == inexistente.headers["cache-control"] == "no-store"


def test_br_acceso_08_el_coordinador_lee_la_410_sin_tenerla_asignada(api: Any) -> None:
    carga = _publicar(api, CORRECTO_410)
    cuerpo = _cuerpo(api.sesion(A.COORDINACION), carga)
    assert _estado(cuerpo) == [("5.1", 63.6, "ROJO", "OPORTUNIDAD_MEJORA"), ("5.2", 63.6, "ROJO", "OPORTUNIDAD_MEJORA"),
                               ("5.3", 72.7, "ROJO", "OPORTUNIDAD_MEJORA")]


def test_br_mejora_05_una_carga_rechazada_responde_409_y_el_403_manda_sobre_el_409(api: Any) -> None:
    carga = C.rechazar(api.dueno, motivo="PI_DEL_PLAN_AUSENTE", nombre_archivo="sin_5_2_410.xlsx", pi="5.2")
    propia = _pedir(api.sesion(A.DOCENTE_410), carga)
    assert (propia.status_code, propia.json()) == (409, NO_PUBLICADA)
    assert propia.headers["cache-control"] == "no-store"
    ajena = _pedir(api.sesion(A.DOCENTE_411), carga)
    assert (ajena.status_code, ajena.json()) == (403, SIN_ALCANCE)


def test_br_mejora_05_una_carga_reemplazada_responde_409_y_la_que_la_reemplaza_200(api: Any) -> None:
    anterior = _publicar(api, CORRECTO_410)
    nueva = C.con_error(api.dueno, anterior)
    cliente = api.sesion(A.DOCENTE_410)
    respuesta = _pedir(cliente, anterior)
    assert (respuesta.status_code, respuesta.json()) == (409, NO_PUBLICADA)
    cuerpo = _cuerpo(cliente, nueva)
    assert (cuerpo["carga_id"], cuerpo["estado"], len(cuerpo["indicadores"])) == (nueva, "PUBLICADA", 3)


# BR-MEJORA-01, una sola instantánea de solo lectura

def test_br_mejora_01_la_ruta_lee_el_alcance_y_las_cifras_en_una_transaccion_read_only_repeatable_read(
        api: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    carga = _publicar(api, CORRECTO_410)
    vistas = []

    def espia(nombre: str, original: Any) -> Any:
        def envuelta(conexion: psycopg.Connection, *argumentos: Any) -> Any:
            vistas.append((nombre, conexion.execute("SHOW transaction_isolation").fetchone()[0],
                           conexion.execute("SHOW transaction_read_only").fetchone()[0],
                           conexion.execute("SELECT txid_current_if_assigned() IS NULL").fetchone()[0],
                           conexion.info.transaction_status.name))
            return original(conexion, *argumentos)
        return envuelta

    monkeypatch.setattr(permisos, "puede_leer", espia("alcance", permisos.puede_leer))
    monkeypatch.setattr(lectura, "_indicadores", espia("cifras", lectura._indicadores))
    assert len(_cuerpo(api.sesion(A.DOCENTE_410), carga)["indicadores"]) == 3
    assert [v[:3] for v in vistas] == [("alcance", "repeatable read", "on"), ("cifras", "repeatable read", "on")]


def test_br_mejora_01_un_reemplazo_a_mitad_de_la_lectura_no_cambia_la_respuesta(
        api: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    anterior = _publicar(api, CORRECTO_410)
    original = lectura._indicadores
    reemplazos = []

    def con_reemplazo(conexion: psycopg.Connection, cargas: list[int], *argumentos: Any) -> Any:
        # Otra conexión reemplaza la carga y confirma después de que la ruta ya leyó que está PUBLICADA.
        reemplazos.append(C.con_error(api.dueno, anterior))
        return original(conexion, cargas, *argumentos)

    monkeypatch.setattr(lectura, "_indicadores", con_reemplazo)
    cuerpo = _cuerpo(api.sesion(A.DOCENTE_410), anterior)
    assert len(reemplazos) == 1
    assert (cuerpo["estado"], [i["pct_sobre_calificados"] for i in cuerpo["indicadores"]]) == (
        "PUBLICADA", [63.6, 63.6, 72.7])


# Contrato, sección 10: la ruta figura en el esquema OpenAPI

def test_la_ruta_13_figura_en_el_esquema_openapi_sin_parametros_de_consulta(api: Any) -> None:
    esquema = api.cliente().get("/api/openapi.json").json()
    operacion = esquema["paths"]["/api/cargas/{carga_id}/indicadores"]["get"]
    assert [p["name"] for p in operacion.get("parameters", [])] == ["carga_id"]
    assert "requestBody" not in operacion
