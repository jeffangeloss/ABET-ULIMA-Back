"""Recorrido de las rutas registradas en la aplicación (BR-ACCESO-10, spec 004), sin pruebas propias.

Lo usan tests/test_rutas_protegidas.py y el escenario «Ninguna ruta con datos responde sin sesión» de
specs/004-reportes-docente/aceptacion/alcance_y_privacidad.feature. iter_route_contexts() es el recorrido con que
FastAPI abre los routers incluidos, que app.routes guarda sin expandir, así que la lista trae también una ruta que no
figura en el esquema OpenAPI.
"""

from __future__ import annotations

import re
from typing import Any

from fastapi.routing import iter_route_contexts

# La lista cerrada de BR-ACCESO-10. POST /api/sesion/codigo entra cuando exista (US-20, T018).
PUBLICAS = frozenset({("POST", "/api/sesion"), ("DELETE", "/api/sesion"), ("POST", "/api/sesion/codigo"),
                      ("GET", "/api/openapi.json")})
SIN_ALCANCE = {"detail": "La sección no está a su cargo."}
VENCIDA = {"detail": "La sesión venció. Ingrese otra vez."}
# Qué clase de identificador recibe cada parámetro. reemplaza es el carga_id de la carga que se reemplaza (BR-CARGA-19).
IDENTIFICADORES = {"seccion_id": "seccion", "carga_id": "carga", "reemplaza": "carga"}
PARAMETRO_DE_CAMINO = re.compile(r"\{([^}]+)\}")


def operaciones(cliente: Any) -> list[tuple[str, str]]:
    """Método y camino de cada ruta registrada en la aplicación del cliente, sin HEAD."""
    return sorted((metodo, ruta.path) for ruta in iter_route_contexts(cliente.app.routes)
                  for metodo in (ruta.methods or ()) if metodo != "HEAD")


def parametros_de_consulta(cliente: Any, metodo: str, camino: str) -> list[dict[str, Any]]:
    """Parámetros de consulta que la ruta declara en el esquema OpenAPI, también los de openapi_extra."""
    operacion = cliente.app.openapi()["paths"].get(camino, {}).get(metodo.lower(), {})
    return [p for p in operacion.get("parameters", []) if p.get("in") == "query"]


def url(camino: str, ids: dict[str, int], consulta: list[dict[str, Any]]) -> tuple[str, dict[str, int]]:
    """URL con los identificadores dados en el camino y en la consulta, o la falla si no sabe armarla."""
    def cambio(coincidencia: re.Match[str]) -> str:
        nombre = coincidencia.group(1)
        assert nombre in IDENTIFICADORES, f"{camino}: la prueba no sabe armar el parámetro {nombre}"
        return str(ids[IDENTIFICADORES[nombre]])
    parametros = {}
    for parametro in consulta:
        nombre = parametro["name"]
        if nombre in IDENTIFICADORES:
            parametros[nombre] = ids[IDENTIFICADORES[nombre]]
        else:
            assert not parametro.get("required"), f"{camino}: la prueba no sabe armar el parámetro {nombre}"
    return PARAMETRO_DE_CAMINO.sub(cambio, camino), parametros


def sin_cookie(cliente: Any, ids: dict[str, int]) -> dict[tuple[str, str], Any]:
    """Respuesta sin cookie de cada ruta fuera de la lista pública, con los identificadores dados."""
    respuestas = {}
    for metodo, camino in operaciones(cliente):
        if (metodo, camino) in PUBLICAS:
            continue
        direccion, consulta = url(camino, ids, parametros_de_consulta(cliente, metodo, camino))
        respuestas[(metodo, camino)] = cliente.request(metodo, direccion, params=consulta)
    return respuestas


def con_identificador_ajeno(cliente: Any, ids: dict[str, int]) -> dict[tuple[str, str], Any]:
    """Respuesta de cada ruta que recibe un seccion_id o un carga_id, pedida con los identificadores dados.

    Una ruta con seccion_id en el camino recibe solo ese identificador, y una ruta sin él lo recibe por la consulta.
    """
    respuestas = {}
    for metodo, camino in operaciones(cliente):
        consulta = parametros_de_consulta(cliente, metodo, camino)
        en_camino = set(PARAMETRO_DE_CAMINO.findall(camino))
        if (metodo, camino) in PUBLICAS or not (en_camino | {p["name"] for p in consulta}) & {"seccion_id", "carga_id"}:
            continue
        direccion, parametros = url(camino, ids, consulta)
        if "seccion_id" in en_camino:
            parametros = {}
        else:
            parametros = {nombre: valor for nombre, valor in parametros.items() if nombre in ("seccion_id", "carga_id")}
        respuestas[(metodo, camino)] = cliente.request(metodo, direccion, params=parametros)
    return respuestas
