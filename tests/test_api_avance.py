"""Pruebas de la ruta 17 GET /api/avance fuera de los .feature (T038 de la spec 008, T033 y T035 de la spec 007).

Cada prueba nombra la regla de negocio (business rule, BR) de specs/features/avance/avance.spec.md o de
specs/features/acceso/acceso.spec.md que comprueba, con lo que debe pasar y lo que no debe pasar. La base es la copia
desechable de tests/api_de_prueba.py, con los datos de 2026-2 y los de varias secciones, en el clúster desechable y
nunca en localhost:5432. Los escenarios de avance_del_registro.feature y avance_del_curso.feature viven en
tests/aceptacion/pasos/test_avance_feature.py.
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

from abet_carga import avance


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
SIN_ALCANCE = "coordinacion.sin.alcance@example.invalid"
SOLO_COORDINACION = {"detail": "Esta página es de la Coordinación."}
VACIO = {"secciones": 0, "PUBLICADA": 0, "CON_RECHAZO": 0, "SIN_CARGA": 0, "SIN_PROFESOR": 0, "SIN_PLAN": 0}


def _avance(cliente: Any, **parametros: str) -> dict[str, Any]:
    respuesta = cliente.get("/api/avance", params=parametros or {"periodo": A.PERIODO})
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.headers["cache-control"] == "no-store"
    return respuesta.json()


def test_br_avance_04_el_conteo_trae_cada_etapa_aunque_valga_0() -> None:
    assert avance.conteo([]) == VACIO
    assert list(avance.conteo(["SIN_PLAN"])) == ["secciones", *avance.ETAPAS]
    assert avance.conteo(["PUBLICADA", "SIN_PLAN", "PUBLICADA"]) == {**VACIO, "secciones": 3, "PUBLICADA": 2,
                                                                      "SIN_PLAN": 1}


def test_br_acceso_13_una_coordinacion_sin_alcance_no_ve_ninguna_seccion(api: Any) -> None:
    api.dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES (%s, 'COORDINADOR')", (SIN_ALCANCE,))
    cliente = api.sesion(SIN_ALCANCE)
    for periodo in ("2026-2", "2026-1"):
        assert _avance(cliente, periodo=periodo) == {"periodo": periodo, "conteo": VACIO, "secciones": []}
    # La coordinación con la carrera AMB, en la misma base, sí ve las cinco secciones de 2026-2.
    assert _avance(api.sesion(A.COORDINACION))["conteo"]["secciones"] == 5


def test_br_acceso_12_el_profesor_recibe_403_antes_del_422_y_sin_secciones(api: Any) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    # El profesor sí ve su sección en la ruta 4, así que el 403 no sale de una lista vacía.
    assert [s["numero"] for s in cliente.get("/api/secciones").json()] == ["410"]
    for parametros in ({"periodo": "2026-2"}, {"periodo": "2026"}, {"periodo": "26-1"}, {}):
        respuesta = cliente.get("/api/avance", params=parametros)
        assert respuesta.status_code == 403, (parametros, respuesta.text)
        assert respuesta.json() == SOLO_COORDINACION
        assert respuesta.headers["cache-control"] == "no-store"


def test_br_acceso_06_una_coordinacion_dada_de_baja_no_lee_el_avance(api: Any) -> None:
    cliente = api.sesion(A.COORDINACION)
    assert _avance(cliente)["conteo"]["secciones"] == 5
    api.dueno.execute("UPDATE acceso.usuario_autorizado SET activo = false WHERE correo = %s", (A.COORDINACION,))
    respuesta = cliente.get("/api/avance", params={"periodo": A.PERIODO})
    assert respuesta.status_code in (401, 403), respuesta.text
    assert "secciones" not in respuesta.json()


def test_br_avance_01_la_ruta_17_figura_en_las_rutas_registradas_y_sin_cookie_responde_401(api: Any) -> None:
    cliente = api.cliente()
    assert ("GET", "/api/avance") in R.operaciones(cliente)
    assert ("GET", "/api/avance") not in R.PUBLICAS
    respuesta = R.sin_cookie(cliente, {"seccion": api.seccion("410"), "carga": 1})[("GET", "/api/avance")]
    assert respuesta.status_code == 401
    assert respuesta.json() == R.VENCIDA
    assert respuesta.headers["cache-control"] == "no-store"


def test_br_avance_03_la_lectura_no_escribe_en_ninguna_tabla(api: Any) -> None:
    antes = api.conteos()
    sesiones = api.uno("SELECT count(*) FROM acceso.sesion")
    cliente = api.sesion(A.COORDINACION)
    _avance(cliente)
    _avance(cliente, periodo="2026-1")
    assert api.conteos() == antes
    # Solo el ingreso de la coordinación suma una sesión, y la lectura no suma otra.
    assert api.uno("SELECT count(*) FROM acceso.sesion") == sesiones + 1


def test_sc_005_la_ruta_17_responde_60_secciones_en_menos_de_1_s(api: Any) -> None:
    api.dueno.execute(
        "INSERT INTO abet.seccion (periodo_id, asignatura_id, numero) SELECT pe.periodo_id, a.asignatura_id, n::text"
        " FROM abet.periodo pe, abet.asignatura a, generate_series(500, 554) AS n"
        " WHERE pe.codigo = %s AND a.codigo = '450002'", (A.PERIODO,))
    cliente = api.sesion(A.COORDINACION)
    assert _avance(cliente)["conteo"]["secciones"] == 60
    duraciones = []
    for _ in range(3):
        inicio = time.perf_counter()
        cuerpo = _avance(cliente)
        duraciones.append(time.perf_counter() - inicio)
    assert cuerpo["conteo"] == {**VACIO, "secciones": 60, "SIN_CARGA": 5, "SIN_PROFESOR": 55}
    assert sorted(duraciones)[1] < 1.0, duraciones
