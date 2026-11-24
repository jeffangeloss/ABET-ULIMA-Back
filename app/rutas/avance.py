"""GET /api/avance?periodo=2026-1, la ruta 17 del contrato (spec 007, US-64; spec 008, US-79, T038).

Las reglas de negocio (business rules, BR) BR-AVANCE-01 a BR-AVANCE-05 viven en specs/features/avance/avance.spec.md,
y la forma de la respuesta en las secciones 14 y 15.5 de docs/03-api/contrato.md del Front.

1. Responde en el orden 401, 403 y 422. El router exige la sesión (BR-ACCESO-10), app/permisos.puede_ver_avance()
   deja pasar solo a una cuenta activa con rol COORDINADOR, y el profesor recibe 403 con «Esta página es de la
   Coordinación.» también con un periodo mal formado (BR-ACCESO-12). Después, un periodo con otra forma que AAAA-C
   responde 422, y sin periodo la ruta usa PERIODO_VIGENTE.
2. Las secciones salen solo de app/permisos.secciones_visibles(), sin una rama por rol ni una condición de alcance
   propia, así que la coordinación de una carrera recibe su carrera y la de un curso, su curso en el periodo de su
   fila (BR-AVANCE-02). Un periodo sin secciones al alcance responde 200 con secciones vacía y el conteo en 0.
3. La etapa de cada sección la deriva abet_carga.avance en cada lectura, sin guardarla (BR-AVANCE-03). Las dos
   consultas van en una sola transacción READ ONLY con REPEATABLE READ, así la etapa y la lista de secciones salen de
   la misma instantánea.
4. Cada sección se arma con la lista cerrada de claves de BR-AVANCE-04, en el orden de código de asignatura y número,
   sin porcentajes, niveles, datos de estudiantes ni de profesores. El campo profesores de US-66 espera a D-47 y a
   D-51 (BR-AVANCE-05) y no existe.
"""

from __future__ import annotations

from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from abet_carga import avance
from app import permisos, sesion
from app.configuracion import PERIODO, PERIODO_MAL_FORMADO, ajustes_de, conexion, error

# BR-ACCESO-10. El router exige la sesión, así que ninguna ruta suya responde sin ella aunque la olvide.
router = APIRouter(dependencies=[Depends(sesion.usuario_actual)])

_SOLO_LECTURA = "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"


@router.get("/avance")
def leer(
    request: Request,
    periodo: str | None = None,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> JSONResponse:
    if not permisos.puede_ver_avance(abierta, usuario.usuario_id):
        return error(403, permisos.SOLO_COORDINACION)
    periodo = ajustes_de(request).periodo_vigente if periodo is None else periodo
    if not PERIODO.fullmatch(periodo):
        return error(422, PERIODO_MAL_FORMADO)
    with abierta.transaction():
        abierta.execute(_SOLO_LECTURA)
        visibles = permisos.secciones_visibles(abierta, usuario.usuario_id, periodo)
        etapas = avance.etapas(abierta, [visible.seccion_id for visible in visibles])
    secciones = [_seccion(visible, etapas[visible.seccion_id]) for visible in visibles]
    return JSONResponse({"periodo": periodo,
                         "conteo": avance.conteo([seccion["etapa"] for seccion in secciones]),
                         "secciones": secciones})


def _seccion(visible: permisos.SeccionVisible, etapa: avance.Etapa) -> dict[str, Any]:
    return {
        "seccion_id": visible.seccion_id,
        "asignatura": {"codigo": visible.asignatura, "nombre": visible.asignatura_nombre},
        "numero": visible.numero,
        "etapa": etapa.etapa,
        "carga_id": etapa.carga_id,
    }
