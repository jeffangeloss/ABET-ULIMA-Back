"""Alcance de cada usuario sobre las secciones, único dueño de BR-ACCESO-07 y BR-ACCESO-08 (parte de T037).

Las reglas de negocio (business rules, BR) viven en specs/features/acceso/acceso.spec.md. El
profesor ve, sube y lee solo en las secciones que acceso.docente_seccion le asigna. El coordinador
lee todas las secciones de la carrera sin filas propias en acceso.docente_seccion y no sube en el
corte 1. Un usuario inactivo, o que no existe, no ve ni alcanza ninguna sección. En el producto
mínimo viable (minimum viable product, MVP), con una sola carrera, las secciones de la carrera son
las del periodo cuya asignatura está en el plan de estudios del catálogo vigente de ese periodo
(propuesta de BR-ACCESO-07).

Las rutas de secciones, cargas, constancia y R-17 y el comando python -m abet_carga preguntan aquí
antes de leer o de escribir, y responden SIN_ALCANCE, el detail del 403 del contrato, cuando la
respuesta es no. Una sección que no existe da el mismo no que una ajena, así que conocer un
identificador ajeno no revela nada.

Cada función lee dentro de conexion.transaction(), que deja la conexión en el estado en que llegó.
Así una conexión sin transacción abierta sigue sin ella y puede pasar después a cargar(), que lo
exige. Las consultas leen solo acceso.usuario_autorizado, acceso.docente_seccion y las tablas de
organización y catálogo que db/plataforma/neon/crear_rol_app.sql deja leer al rol de la aplicación.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from psycopg import Connection
from psycopg.rows import class_row

SIN_ALCANCE = "La sección no está a su cargo."


@dataclass(frozen=True)
class SeccionVisible:
    """Sección que el usuario alcanza, con su asignatura y su número, sin datos de sus cargas."""

    seccion_id: int
    periodo: str
    asignatura: str
    asignatura_nombre: str
    numero: str


# Una sola condición de alcance para las tres funciones. %(usuario)s y %(rol)s son parámetros de psycopg.
_ALCANCE = """
FROM abet.seccion s
JOIN abet.periodo pe     ON pe.periodo_id = s.periodo_id
JOIN abet.asignatura a   ON a.asignatura_id = s.asignatura_id
JOIN acceso.usuario_autorizado u ON u.usuario_id = %(usuario)s AND u.activo
WHERE ((u.rol = 'PROFESOR'
       AND EXISTS (SELECT 1 FROM acceso.docente_seccion d
                   WHERE d.usuario_id = u.usuario_id AND d.seccion_id = s.seccion_id))
   OR (u.rol = 'COORDINADOR' AND %(coordinador_alcanza)s
       AND EXISTS (SELECT 1 FROM abet.catalogo_vigencia v
                   JOIN abet.plan_estudios pl ON pl.catalogo_version_id = v.catalogo_version_id
                   WHERE v.periodo_id = s.periodo_id AND pl.asignatura_id = s.asignatura_id)))
"""

_VISIBLES = (
    "SELECT s.seccion_id, pe.codigo AS periodo, a.codigo AS asignatura, a.nombre AS asignatura_nombre, s.numero"
    + _ALCANCE
    + " AND pe.codigo = %(periodo)s ORDER BY a.codigo, s.numero"
)
_UNA = "SELECT 1" + _ALCANCE + " AND s.seccion_id = %(seccion)s"


def secciones_visibles(conexion: Connection[Any], usuario_id: int, periodo: str) -> list[SeccionVisible]:
    """Secciones del periodo que el usuario ve, por asignatura y número (BR-ACCESO-07)."""
    parametros = {"usuario": usuario_id, "periodo": periodo, "coordinador_alcanza": True}
    with conexion.transaction(), conexion.cursor(row_factory=class_row(SeccionVisible)) as cursor:
        return cursor.execute(_VISIBLES, parametros).fetchall()


def puede_subir(conexion: Connection[Any], usuario_id: int, seccion_id: int) -> bool:
    """Si el usuario sube un export en la sección. En el corte 1 solo sube el profesor asignado (BR-ACCESO-08)."""
    return _alcanza(conexion, usuario_id, seccion_id, coordinador_alcanza=False)


def puede_leer(conexion: Connection[Any], usuario_id: int, seccion_id: int) -> bool:
    """Si el usuario lee la sección, sus cargas, su constancia y su R-17 (BR-ACCESO-07 y BR-ACCESO-08)."""
    return _alcanza(conexion, usuario_id, seccion_id, coordinador_alcanza=True)


def _alcanza(conexion: Connection[Any], usuario_id: int, seccion_id: int, *, coordinador_alcanza: bool) -> bool:
    parametros = {"usuario": usuario_id, "seccion": seccion_id, "coordinador_alcanza": coordinador_alcanza}
    with conexion.transaction():
        return conexion.execute(_UNA, parametros).fetchone() is not None
