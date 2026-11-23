"""Alcance de cada usuario sobre las secciones, único dueño de BR-ACCESO-07 y BR-ACCESO-08 (parte de T037).

Las reglas de negocio (business rules, BR) viven en specs/features/acceso/acceso.spec.md. El
profesor ve, sube, reemplaza y lee solo en las secciones que acceso.docente_seccion le asigna. El
coordinador lee todas las secciones de la carrera sin filas propias en acceso.docente_seccion, no sube
una carga nueva y, desde el corte 2, reemplaza la carga publicada de cualquiera de ellas (valor
provisional de D-11, BR-CARGA-19). Un usuario inactivo, o que no existe, no ve ni alcanza ninguna sección.

Desde la spec 008 (BR-ACCESO-13, T030), el alcance del coordinador sale de sus filas de
acceso.coordinacion_alcance (V1_14), y una cuenta COORDINADOR sin filas no ve nada. Una fila de carrera da las
secciones del periodo cuya asignatura está en el plan de estudios del catálogo vigente de esa carrera en ese
periodo (valor provisional de J-50 para un curso compartido), y una fila de asignatura, las secciones de esa
asignatura en el periodo de la fila. _ALCANCE une las filas de la cuenta. puede_subir() no cambia, así que el
coordinador sigue sin subir una carga nueva, y puede_reemplazar() sigue el alcance de la lectura (D-52).
alcance_de() resume el alcance para GET /api/sesion y periodos_visibles() da los periodos de la ruta 18.

Las rutas de secciones, cargas, constancia y R-17 y el comando python -m abet_carga preguntan aquí
antes de leer o de escribir, y responden SIN_ALCANCE, el detail del 403 del contrato, cuando la
respuesta es no. Una sección que no existe da el mismo no que una ajena, así que conocer un
identificador ajeno no revela nada.

Cada función lee dentro de conexion.transaction(), que deja la conexión en el estado en que llegó.
Así una conexión sin transacción abierta sigue sin ella y puede pasar después a cargar(), que lo
exige. Las consultas leen solo acceso.usuario_autorizado, acceso.docente_seccion,
acceso.coordinacion_alcance y las tablas de organización y catálogo que db/plataforma/neon/crear_rol_app.sql deja leer al rol de la aplicación.
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
       AND EXISTS (SELECT 1 FROM acceso.coordinacion_alcance ca
                   WHERE ca.usuario_id = u.usuario_id
                     AND ((ca.asignatura_id = s.asignatura_id AND ca.periodo_id = s.periodo_id)
                          OR EXISTS (SELECT 1 FROM abet.catalogo_vigencia v
                                     JOIN abet.plan_estudios pl ON pl.catalogo_version_id = v.catalogo_version_id
                                     WHERE v.carrera_id = ca.carrera_id AND v.periodo_id = s.periodo_id
                                       AND pl.asignatura_id = s.asignatura_id)))))
"""

_VISIBLES = (
    "SELECT s.seccion_id, pe.codigo AS periodo, a.codigo AS asignatura, a.nombre AS asignatura_nombre, s.numero"
    + _ALCANCE
    + " AND pe.codigo = %(periodo)s ORDER BY a.codigo, s.numero"
)
_UNA = "SELECT 1" + _ALCANCE + " AND s.seccion_id = %(seccion)s"
_PERIODOS = ("SELECT pe.codigo" + _ALCANCE
             + " GROUP BY pe.codigo, pe.anio, pe.ciclo ORDER BY pe.anio DESC, pe.ciclo DESC")
# Las carreras y las asignaturas de las filas de alcance de una cuenta COORDINADOR, sin repetidos y en orden.
_ALCANCE_DE_LA_CUENTA = """
SELECT u.rol,
       coalesce(array_agg(DISTINCT c.codigo ORDER BY c.codigo) FILTER (WHERE c.codigo IS NOT NULL), '{}') AS carreras,
       coalesce(array_agg(DISTINCT a.codigo ORDER BY a.codigo) FILTER (WHERE a.codigo IS NOT NULL), '{}') AS asignaturas
FROM acceso.usuario_autorizado u
LEFT JOIN acceso.coordinacion_alcance ca ON ca.usuario_id = u.usuario_id AND u.rol = 'COORDINADOR'
LEFT JOIN abet.carrera c    ON c.carrera_id = ca.carrera_id
LEFT JOIN abet.asignatura a ON a.asignatura_id = ca.asignatura_id
WHERE u.usuario_id = %s
GROUP BY u.rol
"""


@dataclass(frozen=True)
class Alcance:
    """Alcance de una cuenta para GET /api/sesion (BR-ACCESO-13), sin datos de personas.

    tipo es SECCIONES para el PROFESOR, CARRERA para una cuenta COORDINADOR con al menos una fila de carrera o sin
    filas, y CURSO para una cuenta COORDINADOR con solo filas de asignatura.
    """

    tipo: str
    carreras: tuple[str, ...]
    asignaturas: tuple[str, ...]


def secciones_visibles(conexion: Connection[Any], usuario_id: int, periodo: str) -> list[SeccionVisible]:
    """Secciones del periodo que el usuario ve, por asignatura y número (BR-ACCESO-07)."""
    parametros = {"usuario": usuario_id, "periodo": periodo, "coordinador_alcanza": True}
    with conexion.transaction(), conexion.cursor(row_factory=class_row(SeccionVisible)) as cursor:
        return cursor.execute(_VISIBLES, parametros).fetchall()


def periodos_visibles(conexion: Connection[Any], usuario_id: int) -> list[str]:
    """Periodos con al menos una sección que el usuario ve, del más reciente al más antiguo (BR-PERIODO-05)."""
    parametros = {"usuario": usuario_id, "coordinador_alcanza": True}
    with conexion.transaction():
        return [fila[0] for fila in conexion.execute(_PERIODOS, parametros).fetchall()]


def alcance_de(conexion: Connection[Any], usuario_id: int) -> Alcance:
    """Tipo de alcance de la cuenta y los códigos de carrera y de asignatura de sus filas (BR-ACCESO-13)."""
    with conexion.transaction():
        fila = conexion.execute(_ALCANCE_DE_LA_CUENTA, (usuario_id,)).fetchone()
    if fila is None or fila[0] != "COORDINADOR":
        return Alcance("SECCIONES", (), ())
    carreras, asignaturas = tuple(fila[1]), tuple(fila[2])
    return Alcance("CURSO" if asignaturas and not carreras else "CARRERA", carreras, asignaturas)


def puede_subir(conexion: Connection[Any], usuario_id: int, seccion_id: int) -> bool:
    """Si el usuario sube un export en la sección. En el corte 1 solo sube el profesor asignado (BR-ACCESO-08)."""
    return _alcanza(conexion, usuario_id, seccion_id, coordinador_alcanza=False)


def puede_reemplazar(conexion: Connection[Any], usuario_id: int, seccion_id: int) -> bool:
    """Si el usuario reemplaza la carga publicada de la sección (corte 2, BR-ACCESO-08, BR-CARGA-19 y D-11).

    El profesor reemplaza en sus secciones y el coordinador en cualquiera de su alcance, también la coordinación de un
    curso en su curso (valor provisional de D-52), así que el alcance es el de la lectura. Vive aparte de puede_leer() porque D-11 sigue abierta y puede fijar otro alcance o un plazo.
    """
    return _alcanza(conexion, usuario_id, seccion_id, coordinador_alcanza=True)


def puede_leer(conexion: Connection[Any], usuario_id: int, seccion_id: int) -> bool:
    """Si el usuario lee la sección, sus cargas, su constancia y su R-17 (BR-ACCESO-07 y BR-ACCESO-08)."""
    return _alcanza(conexion, usuario_id, seccion_id, coordinador_alcanza=True)


def _alcanza(conexion: Connection[Any], usuario_id: int, seccion_id: int, *, coordinador_alcanza: bool) -> bool:
    parametros = {"usuario": usuario_id, "seccion": seccion_id, "coordinador_alcanza": coordinador_alcanza}
    with conexion.transaction():
        return conexion.execute(_UNA, parametros).fetchone() is not None
