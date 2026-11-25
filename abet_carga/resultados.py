"""Meta, cifras, semáforo y hallazgo por indicador (specs 004 y 005) y resumen del curso (spec 009).

Las reglas de la meta y de las cifras viven en specs/features/resultados/resultados.spec.md. Este módulo no conoce
FastAPI. Sus funciones, salvo resumen_del_curso() (punto 5), son puras y las usan la ruta GET /api/resultados
(app/rutas/resultados.py) y el plan de acción del bloque II del R-17 (_plan_de_accion de abet_carga/r17.py), así que la
pantalla P6 y el R-17 de una carga deciden la meta con la misma regla.

1. en_meta() dice si el logro de un indicador de desempeño (performance indicator, PI) llega a la meta. Es verdadero
   cuando el porcentaje sobre los calificados es mayor o igual que la meta, falso cuando es menor y None cuando falta
   alguno de los dos, como en un PI sin calificaciones o en un conjunto de reglas sin META_LOGRO definida.
2. cifra() convierte un Decimal de abet.v_r17_por_pi, que la vista ya redondea a un decimal con ROUND(…, 1), en el
   número de JavaScript Object Notation (JSON) que viaja por la API, y deja None como None, nunca como 0.
3. semaforo() usa en_meta() y el corte rojo. Por debajo de la meta, solo hay AMBAR si el corte está definido
   y el logro lo alcanza. tipo_de_registro() asigna el tipo de registro a cada color.
4. redactar_hallazgo() expresa el logro y la meta con un decimal y nombra el nivel esperado según la escala
   de la celda B40 del R-17. Si las reglas están incompletas, ese aviso tiene prioridad sobre la falta de calificaciones.
   Las reglas del semáforo, del registro y del hallazgo están en specs/features/mejora/mejora.spec.md.
5. resumen_del_curso() es la consulta de la ruta 20 GET /api/resumen-curso (spec 009, US-91, BR-RESULTADOS-12 a
   BR-RESULTADOS-14). Lee en la transacción que le da la ruta, sin escribir, y arma un elemento por PI del plan con la
   suma de los conteos de abet.v_r17_por_pi de las cargas PUBLICADA, nunca el promedio de los porcentajes. El porcentaje
   sale de logrados entre calificados con ROUND(numeric, 1) y el promedio de calificación de la suma de cada nivel por su
   conteo entre la suma de los conteos con ROUND(numeric, 2), los dos en PostgreSQL. en_meta() decide la meta del curso y de
   cada sección sobre el porcentaje ya redondeado. Si las cargas del PI traen metas distintas, o niveles esperados
   distintos, la meta, el nivel esperado y lo que depende de ellos del curso quedan en None.
6. cursos_con_plan() es la consulta de la ruta 21 GET /api/resumen-curso/cursos (spec 009, US-93). Da el código y el nombre
   de cada curso de las secciones dadas que tiene plan de medición en el periodo de la sección, en orden de código.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from psycopg import Connection
from psycopg.rows import dict_row

ESCALA = {1: "No satisfactorio", 2: "En proceso", 3: "Satisfactorio", 4: "Sobresaliente"}


def en_meta(logro: Decimal | None, meta: Decimal | None) -> bool | None:
    """Si el logro llega a la meta o la supera, o None si falta el logro o la meta (BR-RESULTADOS-06)."""
    if logro is None or meta is None:
        return None
    return logro >= meta


def cifra(valor: Decimal | None) -> float | None:
    """Porcentaje o meta de la vista como número JSON, 63,6 como 63.6, y el nulo como None (BR-RESULTADOS-05)."""
    return float(valor) if valor is not None else None


def semaforo(logro: Decimal | None, meta: Decimal | None, corte: Decimal | None) -> str:
    """VERDE, AMBAR, ROJO o SIN_DATO del indicador; corte None (CORTE_ROJO PENDIENTE) nunca da AMBAR (BR-MEJORA-02)."""
    if logro is None or meta is None:
        return "SIN_DATO"
    if en_meta(logro, meta):
        return "VERDE"
    if corte is not None and logro >= corte:
        return "AMBAR"
    return "ROJO"


def tipo_de_registro(semaforo: str) -> str | None:
    """BUENA_PRACTICA para VERDE, OPORTUNIDAD_MEJORA para AMBAR y ROJO, None para SIN_DATO (BR-MEJORA-03)."""
    if semaforo == "VERDE":
        return "BUENA_PRACTICA"
    if semaforo in ("AMBAR", "ROJO"):
        return "OPORTUNIDAD_MEJORA"
    return None


def redactar_hallazgo(pi: str, logro: Decimal | None, meta: Decimal | None, nivel_esperado: int | None) -> str:
    """Texto del hallazgo de un PI con coma decimal y un decimal; sin punto final solo en el caso con cifras."""
    if meta is None or nivel_esperado is None:
        return f"{pi}: el conjunto de reglas no define la meta o el nivel esperado."
    if logro is None:
        return f"{pi}: sin calificaciones en esta carga."
    logro_pct = f"{logro:.1f}".replace(".", ",")
    meta_pct = f"{meta:.1f}".replace(".", ",")
    return f"{pi}: {logro_pct} % en {ESCALA[nivel_esperado]} o más, meta {meta_pct} %"


# Resumen del curso, ruta 20 (spec 009, US-91)

# Los PI del plan de las secciones dadas, uno por SO y PI aunque dos carreras repitan el código, en orden de SO y de PI.
_PI_DEL_CURSO = """
SELECT DISTINCT p.so_numero AS so, p.numero, p.codigo AS pi
FROM abet.seccion s
JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
JOIN abet.pi p             ON p.pi_id = pm.pi_id
WHERE s.seccion_id = ANY(CAST(%(secciones)s AS int[]))
ORDER BY p.so_numero, p.numero
"""

# Las cifras de cada carga PUBLICADA de las secciones dadas y su promedio, de la vista del R-17. El promedio es la suma de
# cada nivel por su conteo entre la suma de los conteos, con numeric, y queda nulo sin calificados.
_CIFRAS_POR_SECCION = """
SELECT c.seccion_id, c.carga_id, v.so, v.pi, v.n_nivel_1, v.n_nivel_2, v.n_nivel_3, v.n_nivel_4,
       v.n_esperado_o_superior, v.n_sin_evidencia, v.n_total, v.pct_logro_sobre_calificados,
       ROUND(CAST(v.n_nivel_1 + 2 * v.n_nivel_2 + 3 * v.n_nivel_3 + 4 * v.n_nivel_4 AS numeric)
             / NULLIF(v.n_nivel_1 + v.n_nivel_2 + v.n_nivel_3 + v.n_nivel_4, 0), 2) AS promedio_nivel,
       v.meta_logro_pct
FROM abet.carga c
JOIN abet.v_r17_por_pi v ON v.carga_id = c.carga_id
WHERE c.seccion_id = ANY(CAST(%(secciones)s AS int[])) AND c.estado = 'PUBLICADA'
"""

# La suma de los conteos de esas cargas por PI. Los logrados, el nivel esperado y la meta quedan nulos si las cargas no
# coinciden, porque dos escalas o dos metas no se suman ni se comparan.
_CIFRAS_DEL_CURSO = """
SELECT v.so, v.pi,
       SUM(v.n_nivel_1) AS n_nivel_1, SUM(v.n_nivel_2) AS n_nivel_2, SUM(v.n_nivel_3) AS n_nivel_3,
       SUM(v.n_nivel_4) AS n_nivel_4,
       CASE WHEN COUNT(v.n_esperado_o_superior) = COUNT(*) AND COUNT(DISTINCT v.nivel_esperado) = 1
            THEN SUM(v.n_esperado_o_superior) END AS logrados,
       SUM(v.n_sin_evidencia) AS sin_evidencia, SUM(v.n_total) AS total,
       SUM(v.n_total - v.n_sin_evidencia) AS calificados,
       CASE WHEN COUNT(v.n_esperado_o_superior) = COUNT(*) AND COUNT(DISTINCT v.nivel_esperado) = 1
            THEN ROUND(100.0 * SUM(v.n_esperado_o_superior) / NULLIF(SUM(v.n_total - v.n_sin_evidencia), 0), 1)
       END AS pct_sobre_calificados,
       ROUND(CAST(SUM(v.n_nivel_1 + 2 * v.n_nivel_2 + 3 * v.n_nivel_3 + 4 * v.n_nivel_4) AS numeric)
             / NULLIF(SUM(v.n_nivel_1 + v.n_nivel_2 + v.n_nivel_3 + v.n_nivel_4), 0), 2) AS promedio_nivel,
       bool_or(v.provisional) AS provisional,
       CASE WHEN COUNT(v.nivel_esperado) = COUNT(*) AND COUNT(DISTINCT v.nivel_esperado) = 1
            THEN MAX(v.nivel_esperado) END AS nivel_esperado,
       CASE WHEN COUNT(v.meta_logro_pct) = COUNT(*) AND COUNT(DISTINCT v.meta_logro_pct) = 1
            THEN MAX(v.meta_logro_pct) END AS meta_logro_pct
FROM abet.carga c
JOIN abet.v_r17_por_pi v ON v.carga_id = c.carga_id
WHERE c.seccion_id = ANY(CAST(%(secciones)s AS int[])) AND c.estado = 'PUBLICADA'
GROUP BY v.so, v.pi
"""


def _entero(valor: Any) -> int | None:
    """Conteo de PostgreSQL, que SUM entrega como numeric, como int, y el nulo como None."""
    return int(valor) if valor is not None else None


def _seccion_del_resumen(seccion_id: int, numero: str, fila: dict[str, Any] | None) -> dict[str, Any]:
    """Una sección del resumen, con la lista cerrada de claves de la ruta 20 y nulos sin carga publicada."""
    if fila is None:
        return {"seccion_id": seccion_id, "numero": numero, "estado": "SIN_CARGA", "carga_id": None, "logrados": None,
                "calificados": None, "sin_evidencia": None, "pct_sobre_calificados": None, "promedio_nivel": None,
                "en_meta": None}
    logro = fila["pct_logro_sobre_calificados"]
    return {"seccion_id": seccion_id, "numero": numero, "estado": "PUBLICADA", "carga_id": fila["carga_id"],
            "logrados": fila["n_esperado_o_superior"], "calificados": fila["n_total"] - fila["n_sin_evidencia"],
            "sin_evidencia": fila["n_sin_evidencia"], "pct_sobre_calificados": cifra(logro),
            "promedio_nivel": cifra(fila["promedio_nivel"]), "en_meta": en_meta(logro, fila["meta_logro_pct"])}


def _conteo_de_secciones(secciones: list[dict[str, Any]]) -> dict[str, int]:
    """Secciones en la meta y debajo de ella solo entre las publicadas, y sin_dato con las que no dan un veredicto."""
    publicadas = [s for s in secciones if s["estado"] == "PUBLICADA"]
    en = sum(1 for s in publicadas if s["en_meta"] is True)
    debajo = sum(1 for s in publicadas if s["en_meta"] is False)
    return {"total": len(secciones), "publicadas": len(publicadas), "en_meta": en, "debajo_de_la_meta": debajo,
            "sin_dato": len(secciones) - en - debajo}


def _curso_del_resumen(fila: dict[str, Any] | None) -> dict[str, Any]:
    """Cifras del curso en un PI. Sin cargas publicadas, los conteos valen 0 y el porcentaje, el promedio y en_meta, None."""
    if fila is None:
        return {"estudiantes_por_nivel": [0, 0, 0, 0], "logrados": 0, "calificados": 0, "sin_evidencia": 0, "total": 0,
                "pct_sobre_calificados": None, "promedio_nivel": None, "en_meta": None}
    logro = fila["pct_sobre_calificados"]
    return {"estudiantes_por_nivel": [int(fila[f"n_nivel_{n}"]) for n in (1, 2, 3, 4)],
            "logrados": _entero(fila["logrados"]), "calificados": int(fila["calificados"]),
            "sin_evidencia": int(fila["sin_evidencia"]), "total": int(fila["total"]),
            "pct_sobre_calificados": cifra(logro), "promedio_nivel": cifra(fila["promedio_nivel"]),
            "en_meta": en_meta(logro, fila["meta_logro_pct"])}


def resumen_del_curso(conexion: Connection[Any], secciones: Sequence[tuple[int, str]]) -> list[dict[str, Any]]:
    """Indicadores de la ruta 20 de las secciones dadas, que son las que la cuenta ve de un curso en un periodo.

    secciones trae el seccion_id y el número de cada una, en el orden en que salen en la respuesta. Se llama dentro de la
    transacción READ ONLY y REPEATABLE READ de la ruta, así que el plan, las cifras de cada sección y las del curso salen de
    la misma instantánea (BR-RESULTADOS-13). Trae un elemento por PI del plan en orden de SO y PI, también sin cargas
    publicadas, y una lista vacía si las secciones no tienen plan.
    """
    ids = [seccion_id for seccion_id, _ in secciones]
    with conexion.cursor(row_factory=dict_row) as cursor:
        plan = cursor.execute(_PI_DEL_CURSO, {"secciones": ids}).fetchall()
        por_seccion = {(f["seccion_id"], f["so"], f["pi"]): f
                       for f in cursor.execute(_CIFRAS_POR_SECCION, {"secciones": ids}).fetchall()}
        del_curso = {(f["so"], f["pi"]): f for f in cursor.execute(_CIFRAS_DEL_CURSO, {"secciones": ids}).fetchall()}
    indicadores = []
    for pi in plan:
        curso = del_curso.get((pi["so"], pi["pi"]))
        del_pi = [_seccion_del_resumen(seccion_id, numero, por_seccion.get((seccion_id, pi["so"], pi["pi"])))
                  for seccion_id, numero in secciones]
        meta = curso["meta_logro_pct"] if curso is not None else None
        indicadores.append({
            "so": pi["so"], "pi": pi["pi"],
            "nivel_esperado": curso["nivel_esperado"] if curso is not None else None,
            "meta_pct": cifra(meta), "provisional": bool(curso["provisional"]) if curso is not None else False,
            "curso": _curso_del_resumen(curso), "conteo_secciones": _conteo_de_secciones(del_pi), "secciones": del_pi})
    return indicadores


# Cursos del alcance con plan de medición, ruta 21 (spec 009, US-93)

_CURSOS_CON_PLAN = """
SELECT a.codigo, a.nombre
FROM abet.asignatura a
WHERE a.asignatura_id IN (
    SELECT s.asignatura_id
    FROM abet.seccion s
    WHERE s.seccion_id = ANY(CAST(%(secciones)s AS int[]))
      AND EXISTS (SELECT 1 FROM abet.plan_medicion pm
                  WHERE pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id))
ORDER BY a.codigo
"""


def cursos_con_plan(conexion: Connection[Any], secciones: Sequence[int]) -> list[dict[str, str]]:
    """Cursos de las secciones dadas con plan de medición en su periodo, en orden de código (BR-RESULTADOS-12).

    secciones son las que la cuenta ve en el periodo, de app/permisos.secciones_visibles(), así que la lista no trae un
    curso fuera de su alcance. Se llama dentro de la transacción READ ONLY de la ruta.
    """
    with conexion.cursor(row_factory=dict_row) as cursor:
        return [{"codigo": f["codigo"], "nombre": f["nombre"]}
                for f in cursor.execute(_CURSOS_CON_PLAN, {"secciones": list(secciones)}).fetchall()]
