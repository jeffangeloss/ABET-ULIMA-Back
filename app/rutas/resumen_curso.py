"""GET /api/resumen-curso?periodo=2026-1&asignatura=5643, la ruta 20 del contrato (spec 009, US-91, T021).

Las reglas de negocio (business rules, BR) BR-RESULTADOS-12 a BR-RESULTADOS-14 viven en
specs/features/resultados/resultados.spec.md, y la forma de la respuesta en la sección 16 de docs/03-api/contrato.md del
Front.

1. Responde en el orden 401, 403 y 422, como la ruta 17. El router exige la sesión (BR-ACCESO-10),
   app/permisos.puede_ver_avance() deja pasar solo a una cuenta activa con rol COORDINADOR, y el profesor recibe 403 con
   «Esta página es de la Coordinación.» también con un periodo o una asignatura mal formados (BR-ACCESO-12). Después, un
   periodo con otra forma que AAAA-C responde 422, y sin periodo la ruta usa PERIODO_VIGENTE. Una asignatura que no es un
   código de 4 o 6 cifras, o que falta, responde 422 con su propio mensaje (propuesta). Ningún 422 lee secciones ni cifras.
2. Las secciones salen solo de app/permisos.secciones_visibles(), filtradas por la asignatura pedida, sin una rama por
   rol ni una condición de alcance propia (BR-RESULTADOS-12). Una asignatura sin secciones al alcance, exista o no, responde
   200 con indicadores vacío y el nombre en null, así que la respuesta no revela si el curso existe.
3. Las cifras las arma abet_carga.resultados.resumen_del_curso() desde abet.v_r17_por_pi (BR-RESULTADOS-13 y
   BR-RESULTADOS-14). Las secciones, el plan y las cifras se leen en una sola transacción READ ONLY con REPEATABLE READ, así
   que salen de la misma instantánea, y la ruta no escribe nada.
4. La respuesta trae solo las claves de la lista cerrada de la sección 16.2 del contrato, sin correos, nombres, códigos de
   estudiantes, subida_por, nombre_archivo ni sha256.
"""

from __future__ import annotations

from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from abet_carga import resultados
from app import permisos, sesion
from app.configuracion import (
    ASIGNATURA,
    ASIGNATURA_MAL_FORMADA,
    PERIODO,
    PERIODO_MAL_FORMADO,
    ajustes_de,
    conexion,
    error,
)

# BR-ACCESO-10. El router exige la sesión, así que ninguna ruta suya responde sin ella aunque la olvide.
router = APIRouter(dependencies=[Depends(sesion.usuario_actual)])

_SOLO_LECTURA = "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"


@router.get("/resumen-curso")
def leer(
    request: Request,
    periodo: str | None = None,
    asignatura: str | None = None,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> JSONResponse:
    if not permisos.puede_ver_avance(abierta, usuario.usuario_id):
        return error(403, permisos.SOLO_COORDINACION)
    periodo = ajustes_de(request).periodo_vigente if periodo is None else periodo
    if not PERIODO.fullmatch(periodo):
        return error(422, PERIODO_MAL_FORMADO)
    if asignatura is None or not ASIGNATURA.fullmatch(asignatura):
        return error(422, ASIGNATURA_MAL_FORMADA)
    with abierta.transaction():
        abierta.execute(_SOLO_LECTURA)
        visibles = [v for v in permisos.secciones_visibles(abierta, usuario.usuario_id, periodo)
                    if v.asignatura == asignatura]
        indicadores = resultados.resumen_del_curso(abierta, [(v.seccion_id, v.numero) for v in visibles])
    nombre = visibles[0].asignatura_nombre if visibles else None
    return JSONResponse({"periodo": periodo, "asignatura": {"codigo": asignatura, "nombre": nombre},
                         "indicadores": indicadores})
