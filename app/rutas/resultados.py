"""GET /api/resultados?periodo=2026-2, los logros por SO de las secciones al alcance (spec 004, T032).

Las reglas de negocio (business rules, BR) BR-RESULTADOS-01 a BR-RESULTADOS-11 viven en
specs/features/resultados/resultados.spec.md, y la forma de la respuesta en la sección 12 de docs/03-api/contrato.md
del Front. La ruta no recibe identificadores de sección ni de carga (J-23), y FastAPI ignora los parámetros que no
declara, así que un seccion_id en la consulta deja la respuesta igual.

1. El alcance sale solo de app/permisos.secciones_visibles(), sin una condición propia (BR-RESULTADOS-02), y el router
   exige la sesión (BR-ACCESO-10). Sin periodo, la ruta usa PERIODO_VIGENTE, y otra forma que AAAA-C responde 422.
2. Todo se lee en una sola transacción READ ONLY con REPEATABLE READ, que fija una instantánea desde la primera
   consulta, así que un reemplazo del corte 2 a mitad de la lectura no deja una sección PUBLICADA sin indicadores
   (BR-RESULTADOS-03).
3. Las cifras salen de abet.v_r17_por_pi, filtrada solo por el carga_id de la carga PUBLICADA de cada sección visible.
   La lista viaja como int[] y trae solo los carga_id que la base devuelve en esta misma lectura.
4. El SO, su descripción, el PI y el instrumento salen del plan de la carga por pi_id y so_id. La vista no expone
   pi_id (J-26), así que cada fila de la vista se empareja con la del plan de su carga por el código del PI, único
   dentro de ese plan porque el plan usa una sola versión de catálogo (BR-RESULTADOS-04). Los indicadores van por
   el número del SO y el número del PI.
5. Cada objeto se arma campo por campo con la lista cerrada de claves de BR-RESULTADOS-09, sin copiar filas. Las
   cifras pasan por abet_carga.resultados, que convierte cada Decimal y decide en_meta con la regla del R-17.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row

from abet_carga import constancia
from abet_carga.resultados import cifra, en_meta, redactar_hallazgo, semaforo, tipo_de_registro
from app import permisos, sesion
from app.configuracion import PERIODO, PERIODO_MAL_FORMADO, ajustes_de, conexion, error

# BR-ACCESO-10. El router exige la sesión, así que ninguna ruta suya responde sin ella aunque la olvide.
router = APIRouter(dependencies=[Depends(sesion.usuario_actual)])

SOLO_LECTURA = "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"

# Por sección visible, los PI de su plan, como GET /api/secciones, y su carga PUBLICADA con su conjunto de reglas.
_SECCIONES = """
SELECT s.seccion_id,
       coalesce((SELECT array_agg(p.codigo ORDER BY p.so_numero, p.numero)
                 FROM abet.plan_medicion pm
                 JOIN abet.pi p ON p.pi_id = pm.pi_id
                 WHERE pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id), '{}') AS pi,
       c.carga_id, cr.version AS conjunto_reglas, cr.estado AS conjunto_reglas_estado,
       (SELECT coalesce(array_agg(pv.clave), '{}')
        FROM abet.parametro_valor pv
        WHERE pv.conjunto_reglas_id = cr.conjunto_reglas_id AND pv.estado = 'PENDIENTE') AS pendientes
FROM abet.seccion s
LEFT JOIN abet.carga c            ON c.seccion_id = s.seccion_id AND c.estado = 'PUBLICADA'
LEFT JOIN abet.conjunto_reglas cr ON cr.conjunto_reglas_id = c.conjunto_reglas_id
WHERE s.seccion_id = ANY(CAST(%(secciones)s AS int[]))
"""

# Cada SO que mide el plan de alguna de las secciones, aunque no tenga carga.
_SO = """
SELECT DISTINCT so.numero, so.descripcion
FROM abet.seccion s
JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
JOIN abet.so so            ON so.so_id = pm.so_id
WHERE s.seccion_id = ANY(CAST(%(secciones)s AS int[]))
ORDER BY so.numero
"""

# Las cifras, de la vista y filtradas solo por carga_id, que baja por debajo de su agregación (SC-005).
_INDICADORES = """
SELECT v.carga_id, v.pi, v.provisional, v.nivel_esperado, v.n_nivel_1, v.n_nivel_2, v.n_nivel_3, v.n_nivel_4,
       v.n_esperado_o_superior, v.n_sin_evidencia, v.n_total, v.pct_logro_sobre_calificados,
       v.pct_logro_sobre_total_con_sin_evidencia, v.meta_logro_pct
FROM abet.v_r17_por_pi v
WHERE v.carga_id = ANY(CAST(%(cargas)s AS int[]))
"""

# El catálogo de cada carga, del plan de su sección y su carrera por pi_id y so_id, en el orden de los indicadores.
_PLAN = """
SELECT c.carga_id, p.codigo AS pi, so.numero AS so, i.nombre AS instrumento
FROM abet.carga c
JOIN abet.seccion s          ON s.seccion_id = c.seccion_id
JOIN abet.plan_medicion pm   ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
                            AND pm.carrera_id = c.carrera_id
JOIN abet.pi p               ON p.pi_id = pm.pi_id
JOIN abet.so so              ON so.so_id = pm.so_id
LEFT JOIN abet.instrumento i ON i.instrumento_id = pm.instrumento_id
WHERE c.carga_id = ANY(CAST(%(cargas)s AS int[]))
ORDER BY c.carga_id, p.so_numero, p.numero
"""


@dataclass
class _Carga:
    """Indicadores de una carga PUBLICADA y su marca provisional, la de la vista."""

    provisional: bool = False
    indicadores: list[dict[str, Any]] = field(default_factory=list)


@router.get("/resultados")
def listar(
    request: Request,
    periodo: str | None = None,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> JSONResponse:
    periodo = ajustes_de(request).periodo_vigente if periodo is None else periodo
    if not PERIODO.fullmatch(periodo):
        return error(422, PERIODO_MAL_FORMADO)
    return JSONResponse(leer(abierta, usuario.usuario_id, periodo))


def leer(conexion: psycopg.Connection[Any], usuario_id: int, periodo: str) -> dict[str, Any]:
    """Cuerpo de la ruta 12 para el usuario y el periodo, leído en una sola instantánea de solo lectura."""
    with conexion.transaction():
        conexion.execute(SOLO_LECTURA)
        visibles = permisos.secciones_visibles(conexion, usuario_id, periodo)
        ids = [visible.seccion_id for visible in visibles]
        detalle = {fila["seccion_id"]: fila for fila in _filas(conexion, _SECCIONES, secciones=ids)}
        so = _filas(conexion, _SO, secciones=ids)
        cargas = [fila["carga_id"] for fila in detalle.values() if fila["carga_id"] is not None]
        indicadores = _indicadores(conexion, cargas)
    return {
        "periodo": periodo,
        "so": [{"numero": fila["numero"], "descripcion": fila["descripcion"]} for fila in so],
        "secciones": [_seccion(visible, detalle[visible.seccion_id], indicadores) for visible in visibles],
    }


def _filas(conexion: psycopg.Connection[Any], consulta: str, **parametros: object) -> list[dict[str, Any]]:
    with conexion.cursor(row_factory=dict_row) as cursor:
        return cursor.execute(consulta, parametros).fetchall()


def _indicadores(conexion: psycopg.Connection[Any], cargas: list[int],
                 armar: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] | None = None) -> dict[int, _Carga]:
    """Indicadores de cada carga, con las cifras de la vista y el catálogo del plan, en el orden del SO y del PI.

    armar arma cada objeto desde la fila del plan y la de la vista, y sin él vale _indicador(), el de la ruta 12.
    """
    armar = armar or _indicador
    if not cargas:
        return {}
    cifras = {(fila["carga_id"], fila["pi"]): fila for fila in _filas(conexion, _INDICADORES, cargas=cargas)}
    por_carga: dict[int, _Carga] = defaultdict(_Carga)
    for plan in _filas(conexion, _PLAN, cargas=cargas):
        fila = cifras.pop((plan["carga_id"], plan["pi"]), None)
        if fila is None:
            raise RuntimeError(f"La vista no trae el PI {plan['pi']} del plan de la carga {plan['carga_id']}.")
        carga = por_carga[plan["carga_id"]]
        carga.provisional = carga.provisional or bool(fila["provisional"])
        carga.indicadores.append(armar(plan, fila))
    # La vista y el plan se leen en la misma instantánea y con las mismas uniones, así que coinciden fila por fila.
    if cifras:
        raise RuntimeError(f"Filas de la vista sin su PI en el plan de la carga: {sorted(cifras)}")
    return dict(por_carga)


def _indicador(plan: dict[str, Any], fila: dict[str, Any]) -> dict[str, Any]:
    logro, meta = fila["pct_logro_sobre_calificados"], fila["meta_logro_pct"]
    return {
        "so": plan["so"],
        "pi": plan["pi"],
        "instrumento": plan["instrumento"],
        "nivel_esperado": fila["nivel_esperado"],
        "estudiantes_por_nivel": [fila["n_nivel_1"], fila["n_nivel_2"], fila["n_nivel_3"], fila["n_nivel_4"]],
        "logrados": fila["n_esperado_o_superior"],
        "calificados": fila["n_total"] - fila["n_sin_evidencia"],
        "sin_evidencia": fila["n_sin_evidencia"],
        "total": fila["n_total"],
        "pct_sobre_calificados": cifra(logro),
        "pct_sobre_total": cifra(fila["pct_logro_sobre_total_con_sin_evidencia"]),
        "meta_pct": cifra(meta),
        "en_meta": en_meta(logro, meta),
    }


def _seccion(visible: permisos.SeccionVisible, detalle: dict[str, Any], indicadores: dict[int, _Carga]) -> dict[str, Any]:
    carga_id = detalle["carga_id"]
    con_carga = carga_id is not None
    carga = indicadores.get(carga_id) if con_carga else None
    return {
        "seccion_id": visible.seccion_id,
        "asignatura": {"codigo": visible.asignatura, "nombre": visible.asignatura_nombre},
        "numero": visible.numero,
        "estado": "PUBLICADA" if con_carga else "SIN_CARGA",
        "carga_id": carga_id,
        "pi": list(detalle["pi"]),
        "conjunto_reglas": detalle["conjunto_reglas"] if con_carga else None,
        "conjunto_reglas_estado": detalle["conjunto_reglas_estado"] if con_carga else None,
        "parametros_pendientes": constancia.en_orden(detalle["pendientes"]) if con_carga else None,
        # provisional es el de la vista, igual en todas las filas de la carga porque depende de su conjunto de reglas.
        "provisional": carga.provisional if carga is not None else None,
        "indicadores": carga.indicadores if carga is not None else [],
    }


# Ruta 13 de la spec 005 (BR-MEJORA-01 a BR-MEJORA-05), que la ruta de app/rutas/cargas.py lee dentro de la misma
# instantánea en que comprueba el alcance.

# El estado de la carga, su conjunto de reglas con sus claves en PENDIENTE, la marca provisional con la expresión de la
# vista y la meta y el corte rojo DEFINIDOS de abet.parametro_valor, en porcentaje como meta_logro_pct de la vista.
_CABECERA = """
SELECT c.estado, cr.version AS conjunto_reglas, cr.estado AS conjunto_reglas_estado,
       COALESCE(array_agg(pv.clave) FILTER (WHERE pv.estado = 'PENDIENTE'), '{}') AS pendientes,
       cr.estado <> 'APROBADO'
       OR COUNT(CASE WHEN pv.clave IN ('NIVEL_ESPERADO', 'META_LOGRO', 'TRATO_SIN_EVIDENCIA')
                      AND pv.estado = 'DEFINIDO' THEN 1 END) < 3 AS provisional,
       ROUND(100.0 * MAX(pv.valor_numero) FILTER (WHERE pv.clave = 'META_LOGRO' AND pv.estado = 'DEFINIDO'), 1)
           AS meta_pct,
       ROUND(100.0 * MAX(pv.valor_numero) FILTER (WHERE pv.clave = 'CORTE_ROJO' AND pv.estado = 'DEFINIDO'), 1)
           AS corte_rojo_pct
FROM abet.carga c
JOIN abet.conjunto_reglas cr      ON cr.conjunto_reglas_id = c.conjunto_reglas_id
LEFT JOIN abet.parametro_valor pv ON pv.conjunto_reglas_id = cr.conjunto_reglas_id
WHERE c.carga_id = %(carga)s
GROUP BY c.estado, cr.version, cr.estado
"""


def indicadores_de_la_carga(conexion: psycopg.Connection[Any], carga_id: int) -> dict[str, Any] | None:
    """Cuerpo de la ruta 13 de una carga PUBLICADA, o None si la carga no existe o no está PUBLICADA.

    Se llama dentro de la transacción READ ONLY y REPEATABLE READ de la ruta, así que la cabecera, las cifras de la
    vista y el plan salen de la misma instantánea (BR-MEJORA-01).
    """
    [cabecera] = _filas(conexion, _CABECERA, carga=carga_id) or [None]
    if cabecera is None or cabecera["estado"] != "PUBLICADA":
        return None
    corte: Decimal | None = cabecera["corte_rojo_pct"]

    def armar(plan: dict[str, Any], fila: dict[str, Any]) -> dict[str, Any]:
        logro, meta = fila["pct_logro_sobre_calificados"], fila["meta_logro_pct"]
        color = semaforo(logro, meta, corte)
        return {**_indicador(plan, fila), "semaforo": color,
                "hallazgo": redactar_hallazgo(plan["pi"], logro, meta, fila["nivel_esperado"]),
                "tipo_registro": tipo_de_registro(color)}

    carga = _indicadores(conexion, [carga_id], armar).get(carga_id, _Carga())
    return {
        "carga_id": carga_id,
        "estado": cabecera["estado"],
        "provisional": bool(cabecera["provisional"]),
        "conjunto_reglas": cabecera["conjunto_reglas"],
        "conjunto_reglas_estado": cabecera["conjunto_reglas_estado"],
        "parametros_pendientes": constancia.en_orden(cabecera["pendientes"]),
        "meta_pct": cifra(cabecera["meta_pct"]),
        "corte_rojo_pct": cifra(corte),
        "indicadores": carga.indicadores,
    }
