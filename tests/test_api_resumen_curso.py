"""Pruebas de la ruta 20 GET /api/resumen-curso fuera de los .feature (T021 de la spec 009, US-91).

Cada prueba nombra la regla de negocio (business rule, BR) de specs/features/resultados/resultados.spec.md o de
specs/features/acceso/acceso.spec.md que comprueba, con lo que debe pasar y lo que no debe pasar. La base es la copia
desechable de tests/api_de_prueba.py, con los datos de 2026-2, en el clúster desechable y nunca en localhost:5432. Los
escenarios de resumen_del_curso.feature, con las cifras de Química General, viven en
tests/aceptacion/pasos/test_resumen_del_curso_feature.py.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from abet_carga import resultados
from app import permisos


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
R = _modulo("rutas_registradas")
plantilla, base, api = A.plantilla, A.base, A.api
RUTA = "/api/resumen-curso"
SOLO_COORDINACION = {"detail": "Esta página es de la Coordinación."}
PERIODO_MAL = {"detail": "El periodo no tiene la forma AAAA-C."}
ASIGNATURA_MAL = {"detail": "La asignatura no tiene la forma de un código de 4 o 6 cifras."}


def _pedir(cliente: Any, **parametros: str) -> Any:
    return cliente.get(RUTA, params=parametros)


# Las rutas registradas y el 401

def test_br_acceso_10_la_ruta_20_figura_en_las_rutas_registradas_y_sin_cookie_responde_401(api: Any) -> None:
    cliente = api.cliente()
    assert ("GET", RUTA) in R.operaciones(cliente)
    assert ("GET", RUTA) not in R.PUBLICAS
    respuestas = R.sin_cookie(cliente, {"seccion": api.seccion("410"), "carga": 1})
    assert respuestas[("GET", RUTA)].status_code == 401
    assert respuestas[("GET", RUTA)].json() == R.VENCIDA
    assert respuestas[("GET", RUTA)].headers["cache-control"] == "no-store"
    # Con parámetros válidos también, porque la sesión se exige antes de leerlos.
    sin_sesion = _pedir(cliente, periodo=A.PERIODO, asignatura="450002")
    assert (sin_sesion.status_code, sin_sesion.json()) == (401, R.VENCIDA)
    # Y la ruta no recibe identificadores de sección ni de carga, así que la prueba del 403 único no la recorre.
    assert ("GET", RUTA) not in R.con_identificador_ajeno(api.sesion(A.DOCENTE_411), {"seccion": 1, "carga": 1})


def test_br_acceso_12_el_profesor_recibe_403_antes_del_422_y_con_cualquier_parametro(api: Any) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    for parametros in ({"periodo": A.PERIODO, "asignatura": "450002"}, {"periodo": "2026", "asignatura": "450002"},
                       {"periodo": A.PERIODO, "asignatura": "Q43"}, {"periodo": "2026", "asignatura": "Q43"}, {}):
        respuesta = _pedir(cliente, **parametros)
        assert (respuesta.status_code, respuesta.json()) == (403, SOLO_COORDINACION), parametros
        assert respuesta.headers["cache-control"] == "no-store"
        assert "indicadores" not in respuesta.text


def test_br_acceso_06_una_coordinacion_dada_de_baja_no_lee_el_resumen(api: Any) -> None:
    cliente = api.sesion(A.COORDINACION)
    assert _pedir(cliente, periodo=A.PERIODO, asignatura="450002").status_code == 200
    api.dueno.execute("UPDATE acceso.usuario_autorizado SET activo = false WHERE correo = %s", (A.COORDINACION,))
    respuesta = _pedir(cliente, periodo=A.PERIODO, asignatura="450002")
    assert respuesta.status_code in (401, 403), respuesta.text
    assert "indicadores" not in respuesta.json()


# El 422 sin leer secciones ni cifras

@pytest.mark.parametrize("periodo", ["2026", "26-1", "2026-3", "2026-12", "2026-", "20261", "abcd-1", "2026-1 "])
def test_br_resultados_12_un_periodo_mal_formado_responde_422_con_su_mensaje(api: Any, periodo: str) -> None:
    respuesta = _pedir(api.sesion(A.COORDINACION), periodo=periodo, asignatura="450002")
    assert (respuesta.status_code, respuesta.json()) == (422, PERIODO_MAL)
    assert respuesta.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("asignatura", ["Q43", "123", "12345", "1234567", "45000A", "4500 2", "-45002", ""])
def test_br_resultados_12_una_asignatura_mal_formada_responde_422_con_su_mensaje(api: Any, asignatura: str) -> None:
    respuesta = _pedir(api.sesion(A.COORDINACION), periodo=A.PERIODO, asignatura=asignatura)
    assert (respuesta.status_code, respuesta.json()) == (422, ASIGNATURA_MAL)


def test_br_resultados_12_sin_asignatura_responde_422_y_el_periodo_mal_formado_se_dice_primero(api: Any) -> None:
    cliente = api.sesion(A.COORDINACION)
    assert (lambda r: (r.status_code, r.json()))(_pedir(cliente, periodo=A.PERIODO)) == (422, ASIGNATURA_MAL)
    assert (lambda r: (r.status_code, r.json()))(_pedir(cliente, periodo="2026", asignatura="Q43")) == (422, PERIODO_MAL)


@pytest.mark.parametrize("asignatura", ["4500", "450002", "5643"])
def test_br_resultados_12_una_asignatura_de_cuatro_o_seis_cifras_pasa_la_validacion(api: Any, asignatura: str) -> None:
    assert _pedir(api.sesion(A.COORDINACION), periodo=A.PERIODO, asignatura=asignatura).status_code == 200


def test_br_resultados_12_el_422_no_lee_secciones_ni_cifras(api: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    cliente = api.sesion(A.COORDINACION)

    def no_debe_leer(*_: object, **__: object) -> None:
        raise AssertionError("la ruta leyó secciones o cifras con una petición mal formada")

    monkeypatch.setattr(permisos, "secciones_visibles", no_debe_leer)
    monkeypatch.setattr(resultados, "resumen_del_curso", no_debe_leer)
    for parametros in ({"periodo": "2026", "asignatura": "450002"}, {"periodo": A.PERIODO, "asignatura": "Q43"},
                       {"periodo": A.PERIODO}):
        assert _pedir(cliente, **parametros).status_code == 422, parametros
    # Con una petición bien formada, en cambio, sí las lee, así que la prueba no pasa por no mirar nada.
    assert _pedir(cliente, periodo=A.PERIODO, asignatura="450002").status_code == 500


# Lo que lee y cómo lo lee

def test_br_resultados_13_la_ruta_lee_en_una_transaccion_de_solo_lectura_con_repeatable_read(
        api: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    visto: dict[str, str] = {}
    real = resultados.resumen_del_curso

    def espia(conexion: Any, secciones: Any) -> Any:
        visto["solo_lectura"] = conexion.execute("SHOW transaction_read_only").fetchone()[0]
        visto["aislamiento"] = conexion.execute("SHOW transaction_isolation").fetchone()[0]
        return real(conexion, secciones)

    monkeypatch.setattr(resultados, "resumen_del_curso", espia)
    assert _pedir(api.sesion(A.COORDINACION), periodo=A.PERIODO, asignatura="450002").status_code == 200
    assert visto == {"solo_lectura": "on", "aislamiento": "repeatable read"}


def test_br_resultados_12_la_coordinacion_recibe_el_curso_con_su_plan_y_sus_secciones_sin_cargas(api: Any) -> None:
    respuesta = _pedir(api.sesion(A.COORDINACION), periodo=A.PERIODO, asignatura="450002")
    assert respuesta.status_code == 200 and respuesta.headers["cache-control"] == "no-store"
    cuerpo = respuesta.json()
    assert list(cuerpo) == ["periodo", "asignatura", "indicadores"]
    assert cuerpo["periodo"] == A.PERIODO
    assert cuerpo["asignatura"]["codigo"] == "450002" and cuerpo["asignatura"]["nombre"]
    assert [(i["so"], i["pi"]) for i in cuerpo["indicadores"]] == [(5, "5.1"), (5, "5.2"), (5, "5.3")]
    numeros = [s["numero"] for s in cuerpo["indicadores"][0]["secciones"]]
    assert numeros == sorted(numeros) and "410" in numeros
    # Ninguna sección de 450002 tiene carga publicada en la base de partida, así que ningún porcentaje es 0.
    for indicador in cuerpo["indicadores"]:
        assert indicador["curso"]["pct_sobre_calificados"] is None and indicador["curso"]["calificados"] == 0
        assert indicador["conteo_secciones"]["publicadas"] == 0


def test_br_resultados_12_con_una_carga_publicada_la_ruta_trae_las_cifras_de_su_pi(api: Any) -> None:
    cliente = api.sesion(A.COORDINACION)
    carga = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), A.archivo(A.CORRECTO), A.CORRECTO)
    assert carga.status_code == 201, carga.text
    cuerpo = _pedir(cliente, periodo=A.PERIODO, asignatura="450002").json()
    for indicador in cuerpo["indicadores"]:
        [de_la_410] = [s for s in indicador["secciones"] if s["numero"] == "410"]
        assert de_la_410["estado"] == "PUBLICADA" and de_la_410["carga_id"] == carga.json()["carga_id"]
        assert de_la_410["calificados"] > 0 and de_la_410["pct_sobre_calificados"] is not None
        assert indicador["conteo_secciones"]["publicadas"] == 1
        # Con una sola sección publicada, el curso es esa sección.
        assert indicador["curso"]["pct_sobre_calificados"] == de_la_410["pct_sobre_calificados"]
        assert indicador["curso"]["calificados"] == de_la_410["calificados"]


def test_br_resultados_12_otro_periodo_u_otro_curso_no_trae_indicadores_y_no_dice_si_existe(api: Any) -> None:
    cliente = api.sesion(A.COORDINACION)
    for parametros in ({"periodo": "2026-1", "asignatura": "450002"}, {"periodo": A.PERIODO, "asignatura": "5643"},
                       {"periodo": A.PERIODO, "asignatura": "999999"}):
        respuesta = _pedir(cliente, **parametros)
        assert respuesta.status_code == 200, respuesta.text
        assert respuesta.json() == {"periodo": parametros["periodo"],
                                    "asignatura": {"codigo": parametros["asignatura"], "nombre": None},
                                    "indicadores": []}


def test_br_resultados_12_otros_parametros_de_la_consulta_no_cambian_la_respuesta(api: Any) -> None:
    cliente = api.sesion(A.COORDINACION)
    sola = _pedir(cliente, periodo=A.PERIODO, asignatura="450002").json()
    assert _pedir(cliente, periodo=A.PERIODO, asignatura="450002", seccion_id=str(api.seccion("410"))).json() == sola
    assert _pedir(cliente, periodo=A.PERIODO, asignatura="450002", profesor="docente410@example.invalid").json() == sola


def test_br_resultados_12_sin_periodo_la_ruta_usa_el_periodo_vigente(api: Any) -> None:
    cliente = api.sesion(A.COORDINACION)
    sin_periodo = _pedir(cliente, asignatura="450002")
    assert sin_periodo.status_code == 200 and sin_periodo.json()["periodo"] == api.ajustes.periodo_vigente == A.PERIODO
    assert sin_periodo.json() == _pedir(cliente, periodo=A.PERIODO, asignatura="450002").json()


def test_br_resultados_13_la_lectura_no_escribe_en_ninguna_tabla(api: Any) -> None:
    antes = api.conteos()
    sesiones = api.uno("SELECT count(*) FROM acceso.sesion")
    cliente = api.sesion(A.COORDINACION)
    for asignatura in ("450002", "450010", "5643"):
        assert _pedir(cliente, periodo=A.PERIODO, asignatura=asignatura).status_code == 200
    assert api.conteos() == antes
    assert api.uno("SELECT count(*) FROM acceso.sesion") == sesiones + 1
