"""Ninguna ruta con datos responde sin sesión (BR-ACCESO-10, T030 de la spec 004 y J-25).

La prueba recorre las rutas que la aplicación registra de verdad (tests/rutas_registradas.py), así que una ruta nueva
entra sola al recorrido. Cada ruta fuera de la lista cerrada de rutas públicas debe responder 401 sin la cookie
abet_sesion, y cada ruta que recibe un seccion_id o un carga_id, por el camino o por la consulta, debe responder el 403
único de BR-ACCESO-08 cuando docente411@example.invalid le pasa uno de la sección 410 de 450002. Una ruta con otro
identificador que la prueba no sabe armar la hace fallar, para que nadie sume una ruta sin decidir su caso 403.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from app import sesion


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


def _ids_de_la_410(api: Any) -> dict[str, int]:
    respuesta = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), A.archivo(A.CORRECTO), A.CORRECTO)
    assert respuesta.status_code == 201, respuesta.text
    return {"seccion": api.seccion("410"), "carga": respuesta.json()["carga_id"]}


def test_br_acceso_10_cada_ruta_fuera_de_la_lista_publica_responde_401_sin_cookie(api: Any) -> None:
    respuestas = R.sin_cookie(api.cliente(), _ids_de_la_410(api))
    # La ruta 20 de la spec 009 entra al recorrido sin cambiar la prueba, y esta línea exige que no salga de él.
    assert {("GET", "/api/resultados"), ("GET", "/api/cargas/{carga_id}/indicadores"),
            ("GET", "/api/cargas/{carga_id}/mejora"), ("PUT", "/api/cargas/{carga_id}/mejora/borrador"),
            ("POST", "/api/cargas/{carga_id}/mejora/declaracion"), ("GET", "/api/resumen-curso"),
            ("GET", "/api/resumen-curso/cursos")} <= set(respuestas)
    assert len(respuestas) >= 8, sorted(respuestas)
    for (metodo, camino), respuesta in respuestas.items():
        assert respuesta.status_code == 401, f"{metodo} {camino} responde {respuesta.status_code} sin sesión"
        assert respuesta.json() == R.VENCIDA, f"{metodo} {camino}"
        assert respuesta.headers["cache-control"] == "no-store", f"{metodo} {camino}"


def test_br_acceso_10_las_rutas_publicas_no_piden_la_sesion(api: Any) -> None:
    cliente = api.cliente()
    publicas = [(m, c) for m, c in R.operaciones(cliente) if (m, c) in R.PUBLICAS]
    assert {("POST", "/api/sesion"), ("DELETE", "/api/sesion"), ("GET", "/api/openapi.json")} <= set(publicas)
    for metodo, camino in publicas:
        assert cliente.request(metodo, camino).status_code != 401, f"{metodo} {camino}"


def test_br_acceso_10_cada_ruta_con_un_identificador_ajeno_responde_el_403_unico(api: Any) -> None:
    respuestas = R.con_identificador_ajeno(api.sesion(A.DOCENTE_411), _ids_de_la_410(api))
    for (metodo, camino), respuesta in respuestas.items():
        assert respuesta.status_code == 403, f"{metodo} {camino} responde {respuesta.status_code}"
        assert respuesta.json() == R.SIN_ALCANCE, f"{metodo} {camino}"
    assert {("POST", "/api/secciones/{seccion_id}/cargas"), ("GET", "/api/cargas"), ("GET", "/api/cargas/{carga_id}"),
            ("GET", "/api/cargas/{carga_id}/r17.xlsx"), ("GET", "/api/cargas/{carga_id}/indicadores"),
            ("GET", "/api/cargas/{carga_id}/mejora"), ("PUT", "/api/cargas/{carga_id}/mejora/borrador"),
            ("POST", "/api/cargas/{carga_id}/mejora/declaracion")} <= set(respuestas), sorted(respuestas)
    assert ("GET", "/api/resultados") not in respuestas
    # Las rutas 20 y 21 reciben el periodo y la asignatura y ningún identificador de sección ni de carga, así que no entra a esta lista.
    assert {("GET", "/api/resumen-curso"), ("GET", "/api/resumen-curso/cursos")}.isdisjoint(respuestas)


def test_br_acceso_10_una_ruta_con_un_parametro_desconocido_detiene_el_recorrido() -> None:
    with pytest.raises(AssertionError, match="no sabe armar el parámetro codigo"):
        R.url("/api/estudiantes/{codigo}", {"seccion": 1, "carga": 1}, [])


@pytest.mark.parametrize("modulo", ["secciones", "cargas", "resultados", "mejora"])
def test_br_acceso_10_cada_router_con_datos_declara_la_dependencia_de_sesion(modulo: str) -> None:
    # J-25 fija la dependencia en el router y no ruta por ruta, para que una ruta nueva del router no pueda olvidarla.
    router = importlib.import_module(f"app.rutas.{modulo}").router
    assert any(dependencia.dependency is sesion.usuario_actual for dependencia in router.dependencies), modulo
