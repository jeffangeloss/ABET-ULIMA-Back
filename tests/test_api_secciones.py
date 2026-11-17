"""Pruebas de GET /api/secciones (T037), con los escenarios de US-06 de acceso.feature y varias_secciones.feature.

Cada prueba nombra la regla de negocio (business rule, BR) que comprueba, de
specs/features/acceso/acceso.spec.md o de specs/features/periodo/periodo.spec.md, con lo que debe
pasar y lo que no debe pasar. La regla de visibilidad vive en app/permisos.py, y estas pruebas
comprueban que la ruta la usa y arma el cuerpo del contrato.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


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
plantilla, base, api = A.plantilla, A.base, A.api
TODAS = {("450002", "410"), ("450002", "411"), ("450002", "412"), ("450010", "410"), ("450010", "412")}


def _secciones(cliente: object, **parametros: str) -> list[dict]:
    respuesta = cliente.get("/api/secciones", params=parametros or {"periodo": A.PERIODO})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def test_br_acceso_07_el_profesor_ve_unicamente_su_seccion_sin_carga(api: object) -> None:
    secciones = _secciones(api.sesion(A.DOCENTE_410))
    assert secciones == [{
        "seccion_id": api.seccion("410"),
        "asignatura": {"codigo": "450002", "nombre": "Principios de Ingeniería Sostenible"},
        "numero": "410",
        "periodo": "2026-2",
        "pi": ["5.1", "5.2", "5.3"],
        "tiene_plan": True,
        "estado": "SIN_CARGA",
        "carga_id": None,
        "filas_leidas": None,
        "filas_aceptadas": None,
    }]


def test_br_acceso_07_el_coordinador_ve_todas_las_secciones_sin_filas_propias(api: object) -> None:
    secciones = _secciones(api.sesion(A.COORDINACION))
    assert {(s["asignatura"]["codigo"], s["numero"]) for s in secciones} == TODAS
    assert api.uno("SELECT count(*) FROM acceso.docente_seccion d JOIN acceso.usuario_autorizado u"
                   " USING (usuario_id) WHERE u.correo = %s", A.COORDINACION) == 0


def test_br_acceso_07_el_profesor_de_varias_secciones_ve_sus_tres_y_ninguna_otra(api: object) -> None:
    secciones = _secciones(api.sesion(A.VARIAS_CORREO))
    assert [(s["asignatura"]["codigo"], s["numero"]) for s in secciones] == [
        ("450002", "412"), ("450010", "410"), ("450010", "412")]
    assert {tuple(s["pi"]) for s in secciones} == {("5.1", "5.2", "5.3"), ("2.1", "2.2", "5.1")}


def test_br_periodo_01_el_estado_refleja_la_carga_publicada(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    subida = A.subir(cliente, api.seccion("410"), A.archivo(A.CORRECTO), A.CORRECTO)
    assert subida.status_code == 201
    [seccion] = _secciones(cliente)
    assert (seccion["estado"], seccion["carga_id"], seccion["filas_leidas"], seccion["filas_aceptadas"]) == (
        "PUBLICADA", subida.json()["carga_id"], 11, 11)


def test_br_periodo_01_una_seccion_con_solo_cargas_rechazadas_sigue_sin_carga(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    subida = A.subir(cliente, api.seccion("410"), A.archivo("sin_5_2_410.xlsx"), "sin_5_2_410.xlsx")
    assert subida.status_code == 201 and subida.json()["estado"] == "RECHAZADA"
    [seccion] = _secciones(cliente)
    assert seccion["estado"] == "SIN_CARGA" and seccion["carga_id"] is None


def test_br_periodo_04_una_seccion_sin_plan_sale_con_tiene_plan_falso_y_sin_pi(api: object) -> None:
    api.dueno.execute("DELETE FROM abet.plan_medicion pm USING abet.asignatura a"
                      " WHERE a.asignatura_id = pm.asignatura_id AND a.codigo = '450010'")
    secciones = {(s["asignatura"]["codigo"], s["numero"]): s for s in _secciones(api.sesion(A.VARIAS_CORREO))}
    assert (secciones[("450010", "410")]["tiene_plan"], secciones[("450010", "410")]["pi"]) == (False, [])
    assert secciones[("450002", "412")]["tiene_plan"] is True


def test_br_periodo_01_sin_periodo_la_api_usa_el_periodo_vigente(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    assert cliente.get("/api/secciones").json() == _secciones(cliente)


def test_br_periodo_01_un_periodo_sin_secciones_da_una_lista_vacia(api: object) -> None:
    assert _secciones(api.sesion(A.DOCENTE_410), periodo="2025-1") == []


@pytest.mark.parametrize("periodo", ["2026-3", "2026", "26-2", "2026-2; DROP"])
def test_br_periodo_01_un_periodo_mal_formado_responde_422(api: object, periodo: str) -> None:
    respuesta = api.sesion(A.DOCENTE_410).get("/api/secciones", params={"periodo": periodo})
    assert respuesta.status_code == 422
    assert respuesta.json() == {"detail": "El periodo no tiene la forma AAAA-C."}


def test_br_acceso_06_sin_sesion_no_hay_lista(api: object) -> None:
    respuesta = api.cliente().get("/api/secciones", params={"periodo": A.PERIODO})
    assert respuesta.status_code == 401 and "seccion_id" not in respuesta.text
