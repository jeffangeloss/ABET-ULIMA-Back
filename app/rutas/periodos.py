"""GET /api/periodos, la ruta 18 del contrato (spec 008, US-73, BR-PERIODO-05, T033).

Responde vigente, con el valor de PERIODO_VIGENTE, y periodos, con los códigos de los periodos que tienen al menos
una sección al alcance del usuario según app/permisos.periodos_visibles(), que usa la misma condición de
secciones_visibles(), del más reciente al más antiguo. Las claves son cerradas y la ruta no dice cuántas secciones
hay en cada periodo ni de qué asignatura (contrato, sección 15.2). Sin sesión responde el 401 único, porque el router
exige la sesión (BR-ACCESO-10), y la respuesta lleva Cache-Control: no-store, como toda /api.
"""

from __future__ import annotations

from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app import permisos, sesion
from app.configuracion import ajustes_de, conexion

# BR-ACCESO-10. El router exige la sesión, así que ninguna ruta suya responde sin ella aunque la olvide.
router = APIRouter(dependencies=[Depends(sesion.usuario_actual)])


@router.get("/periodos")
def listar(
    request: Request,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> JSONResponse:
    periodos = permisos.periodos_visibles(abierta, usuario.usuario_id)
    return JSONResponse({"vigente": ajustes_de(request).periodo_vigente, "periodos": periodos})
