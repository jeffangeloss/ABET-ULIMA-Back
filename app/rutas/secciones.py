"""GET /api/secciones?periodo=2026-2 (T037, BR-ACCESO-07, BR-PERIODO-01 y BR-PERIODO-04).

Las secciones que el usuario ve salen solo de app/permisos.secciones_visibles(), el único dueño de
la regla de visibilidad. Esta ruta suma a cada una los indicadores de desempeño (performance
indicators, PI) de su plan de medición, en el orden del resultado del estudiante y del número del
PI, y el estado de su carga. estado vale PUBLICADA, con carga_id, filas_leidas y filas_aceptadas,
cuando la sección tiene una carga en ese estado, y SIN_CARGA en otro caso, con esos tres campos en
null, también si sus cargas están todas RECHAZADA o REEMPLAZADA (propuesta). tiene_plan es falso, y
pi viene vacío, cuando abet.plan_medicion no tiene filas de la asignatura en el periodo.

Sin periodo, la ruta usa PERIODO_VIGENTE. Un periodo con otra forma que AAAA-C responde 422 con «El
periodo no tiene la forma AAAA-C.» (propuesta), y uno bien formado sin secciones da una lista vacía.
"""

from __future__ import annotations

from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row

from app import permisos, sesion
from app.configuracion import PERIODO, ajustes_de, conexion, error

router = APIRouter()
PERIODO_MAL_FORMADO = "El periodo no tiene la forma AAAA-C."

_DETALLE = """
SELECT s.seccion_id,
       coalesce(array_agg(p.codigo ORDER BY p.so_numero, p.numero) FILTER (WHERE p.codigo IS NOT NULL), '{}') AS pi,
       c.carga_id, c.filas_leidas, c.filas_aceptadas
FROM abet.seccion s
LEFT JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
LEFT JOIN abet.pi p             ON p.pi_id = pm.pi_id
LEFT JOIN abet.carga c          ON c.seccion_id = s.seccion_id AND c.estado = 'PUBLICADA'
WHERE s.seccion_id = ANY(%s)
GROUP BY s.seccion_id, c.carga_id, c.filas_leidas, c.filas_aceptadas
"""


@router.get("/secciones")
def listar(
    request: Request,
    periodo: str | None = None,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> JSONResponse:
    periodo = ajustes_de(request).periodo_vigente if periodo is None else periodo
    if not PERIODO.fullmatch(periodo):
        return error(422, PERIODO_MAL_FORMADO)
    visibles = permisos.secciones_visibles(abierta, usuario.usuario_id, periodo)
    with abierta.cursor(row_factory=dict_row) as cursor:
        filas = cursor.execute(_DETALLE, ([s.seccion_id for s in visibles],)).fetchall()
    detalle = {fila["seccion_id"]: fila for fila in filas}
    return JSONResponse([_seccion(visible, detalle[visible.seccion_id]) for visible in visibles])


def _seccion(visible: permisos.SeccionVisible, detalle: dict[str, Any]) -> dict[str, Any]:
    publicada = detalle["carga_id"] is not None
    return {
        "seccion_id": visible.seccion_id,
        "asignatura": {"codigo": visible.asignatura, "nombre": visible.asignatura_nombre},
        "numero": visible.numero,
        "periodo": visible.periodo,
        "pi": list(detalle["pi"]),
        "tiene_plan": bool(detalle["pi"]),
        "estado": "PUBLICADA" if publicada else "SIN_CARGA",
        "carga_id": detalle["carga_id"],
        "filas_leidas": detalle["filas_leidas"],
        "filas_aceptadas": detalle["filas_aceptadas"],
    }
