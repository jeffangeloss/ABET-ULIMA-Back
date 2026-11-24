"""Etapa del registro de cada sección, para la ruta 17 GET /api/avance (spec 007, US-64, J-48; spec 008, US-79).

Las reglas de negocio (business rules, BR) BR-AVANCE-01 a BR-AVANCE-05 viven en specs/features/avance/avance.spec.md.
Este módulo no conoce FastAPI ni decide qué secciones ve una cuenta, que es asunto de app/permisos.secciones_visibles().
Recibe los seccion_id ya visibles y deriva la etapa de cada una en una sola consulta, sin guardarla en ninguna tabla
(BR-AVANCE-03), con la precedencia de J-48 de la spec 007, valor provisional.

1. SIN_PLAN, cuando abet.plan_medicion no tiene filas de su asignatura en el periodo, la condición de tiene_plan de la
   ruta 4.
2. PUBLICADA, con una carga PUBLICADA, aunque su profesor ya no esté activo. Una carga REEMPLAZADA con su sucesora
   PUBLICADA deja la sección en PUBLICADA.
3. SIN_PROFESOR, sin un usuario activo con rol PROFESOR en acceso.docente_seccion, la condición de
   secciones_sin_docente.sql de la spec 006. Una cuenta COORDINADOR asignada a la sección no cuenta como profesor.
4. CON_RECHAZO, con al menos una carga RECHAZADA.
5. SIN_CARGA en otro caso, también con una carga EN_CURSO.

carga_id es el de la carga PUBLICADA de la sección, o None sin ella. La consulta no lee mediciones, estudiantes ni
credenciales, así que nada de lo que devuelve trae cifras del R-17 ni datos de personas (BR-AVANCE-04).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from psycopg import Connection

# Las etapas en el orden del conteo de la respuesta (contrato del Front, sección 14.2).
ETAPAS = ("PUBLICADA", "CON_RECHAZO", "SIN_CARGA", "SIN_PROFESOR", "SIN_PLAN")

_ETAPAS = """
SELECT s.seccion_id,
       CASE
         WHEN NOT EXISTS (SELECT 1 FROM abet.plan_medicion pm
                          WHERE pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id) THEN 'SIN_PLAN'
         WHEN publicada.carga_id IS NOT NULL THEN 'PUBLICADA'
         WHEN NOT EXISTS (SELECT 1 FROM acceso.docente_seccion d
                          JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
                          WHERE d.seccion_id = s.seccion_id AND u.activo AND u.rol = 'PROFESOR') THEN 'SIN_PROFESOR'
         WHEN EXISTS (SELECT 1 FROM abet.carga c
                      WHERE c.seccion_id = s.seccion_id AND c.estado = 'RECHAZADA') THEN 'CON_RECHAZO'
         ELSE 'SIN_CARGA'
       END AS etapa,
       publicada.carga_id
FROM abet.seccion s
LEFT JOIN abet.carga publicada ON publicada.seccion_id = s.seccion_id AND publicada.estado = 'PUBLICADA'
WHERE s.seccion_id = ANY(CAST(%(secciones)s AS int[]))
"""


@dataclass(frozen=True)
class Etapa:
    """Etapa de una sección y el carga_id de su carga PUBLICADA, o None."""

    etapa: str
    carga_id: int | None


def etapas(conexion: Connection[Any], secciones: list[int]) -> dict[int, Etapa]:
    """Etapa de cada sección dada, por seccion_id, en una sola consulta y sin escribir nada (BR-AVANCE-03)."""
    filas = conexion.execute(_ETAPAS, {"secciones": secciones}).fetchall()
    return {int(seccion_id): Etapa(etapa, carga_id) for seccion_id, etapa, carga_id in filas}


def conteo(etapas_de_las_secciones: list[str]) -> dict[str, int]:
    """Conteo de la respuesta, con el total de secciones y una cifra por etapa, también las que valen 0."""
    return {"secciones": len(etapas_de_las_secciones),
            **{etapa: etapas_de_las_secciones.count(etapa) for etapa in ETAPAS}}
