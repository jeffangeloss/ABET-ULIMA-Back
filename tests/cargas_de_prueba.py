"""Cargas de prueba para las pruebas del R-17 y de la constancia (T035).

La carga real la escribe abet_carga/carga.py (T033), así que estas ayudas preparan la base sin ella,
con la conexión del dueño de una base desechable de tests/base_desechable.py y siempre con
parámetros de psycopg. Parten de db/pruebas/datos_sinteticos.sql, que publica la 410 de 450002 con
63,6 / 63,6 / 72,7 y 33 mediciones, y de db/datos/periodo_2026_2_inventado.sql, que registra la 411
y los usuarios de prueba.

preparar_410() deja la carga de los datos sintéticos como la deja la subida del export correcto, con
la hoja de Blackboard, la huella SHA-256 (Secure Hash Algorithm de 256 bits) del archivo de
tests/datos_inventados/ y docente410 como autor. con_error() la reemplaza por la carga del export
con el 5 en la fila 3, sin las mediciones de 99000002 y con su rechazo NIVEL_FUERA_DE_ESCALA, que da
60,0 / 60,0 / 70,0 y 30 mediciones, como la sección 7 de db/pruebas/pruebas.sql. aprobar() la
reemplaza con el conjunto inventado R-PRUEBA-APROBADO del caso A03 de pruebas.sql. publicar() y
rechazar() registran cargas nuevas de cualquier asignatura y sección del plan. Los códigos son
inventados, de 99000000 a 99999999, y los correos terminan en @example.invalid.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import psycopg

RAIZ = Path(__file__).resolve().parent.parent
SINTETICOS = RAIZ / "db" / "pruebas" / "datos_sinteticos.sql"
INVENTADOS = RAIZ / "tests" / "datos_inventados"
DOCENTE_410 = "docente410@example.invalid"
HOJA_410 = "gc_SINTETICO_20262_450002_410_f"
PERIODO = "2026-2"
BORRADOR = "R-2026-BORRADOR"
APROBADO = "R-PRUEBA-APROBADO"


@dataclass(frozen=True)
class Fila:
    """Fila aceptada de una carga de prueba, con un nivel por columna de PI (None es SIN_EVIDENCIA)."""

    fila_origen: int
    codigo: str
    niveles: tuple[int | None, ...]


def huella_de(nombre: str) -> str:
    """Huella del archivo de tests/datos_inventados/ con ese nombre, o la del nombre si el archivo no existe."""
    ruta = INVENTADOS / nombre
    datos = ruta.read_bytes() if ruta.is_file() else nombre.encode()
    return hashlib.sha256(datos).hexdigest()


def uno(conexion: psycopg.Connection, consulta: str, parametros: Sequence[object] = ()) -> object:
    fila = conexion.execute(consulta, parametros).fetchone()
    assert fila is not None, consulta
    return fila[0]


def usuario(conexion: psycopg.Connection, correo: str) -> int:
    return int(uno(conexion, "SELECT usuario_id FROM acceso.usuario_autorizado WHERE correo = %s", (correo,)))


def seccion(conexion: psycopg.Connection, asignatura: str, numero: str) -> int:
    """seccion_id de la sección de 2026-2, que se registra si todavía no existe."""
    conexion.execute(
        "INSERT INTO abet.seccion (periodo_id, asignatura_id, numero) "
        "SELECT pe.periodo_id, a.asignatura_id, %s FROM abet.periodo pe, abet.asignatura a "
        "WHERE pe.codigo = %s AND a.codigo = %s ON CONFLICT DO NOTHING",
        (numero, PERIODO, asignatura),
    )
    return int(uno(
        conexion,
        "SELECT s.seccion_id FROM abet.seccion s JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id "
        "JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id "
        "WHERE pe.codigo = %s AND a.codigo = %s AND s.numero = %s",
        (PERIODO, asignatura, numero),
    ))


def plan(conexion: psycopg.Connection, asignatura: str, pis: Sequence[str]) -> None:
    """Plan de medición de la asignatura en 2026-2 con esos PI, con el instrumento del par asignatura y SO."""
    conexion.execute(
        "INSERT INTO abet.plan_medicion (periodo_id, asignatura_id, carrera_id, catalogo_version_id, so_id, pi_id, "
        "instrumento_id) "
        "SELECT pe.periodo_id, a.asignatura_id, cv.carrera_id, cv.catalogo_version_id, p.so_id, p.pi_id, "
        "aso.instrumento_id "
        "FROM abet.periodo pe JOIN abet.catalogo_version cv ON cv.codigo = 'AMB-2026' "
        "JOIN abet.asignatura a ON a.codigo = %s "
        "JOIN abet.pi p ON p.catalogo_version_id = cv.catalogo_version_id AND p.codigo = ANY(%s) "
        "JOIN abet.asignatura_so aso ON aso.catalogo_version_id = cv.catalogo_version_id "
        "AND aso.asignatura_id = a.asignatura_id AND aso.so_id = p.so_id "
        "WHERE pe.codigo = %s ON CONFLICT DO NOTHING",
        (asignatura, list(pis), PERIODO),
    )
    registrados = int(uno(
        conexion,
        "SELECT count(*) FROM abet.plan_medicion pm JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id "
        "JOIN abet.pi p ON p.pi_id = pm.pi_id WHERE a.codigo = %s AND p.codigo = ANY(%s)",
        (asignatura, list(pis)),
    ))
    assert registrados == len(pis), f"el catálogo no admite el plan {pis} para {asignatura}"


def carga_de(conexion: psycopg.Connection, nombre_archivo: str, estado: str = "PUBLICADA") -> int:
    return int(uno(
        conexion,
        "SELECT c.carga_id FROM abet.carga c JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id "
        "WHERE ao.nombre_archivo = %s AND c.estado = %s",
        (nombre_archivo, estado),
    ))


def preparar_410(conexion: psycopg.Connection) -> int:
    """Carga de datos_sinteticos.sql con la hoja, la huella y el autor que deja la subida del export correcto."""
    carga_id = carga_de(conexion, "sintetico_20262_450002_410.xlsx")
    conexion.execute(
        "UPDATE abet.archivo_origen ao SET hoja = %s, sha256 = %s FROM abet.carga c "
        "WHERE c.archivo_id = ao.archivo_id AND c.carga_id = %s",
        (HOJA_410, huella_de("sintetico_20262_450002_410.xlsx"), carga_id),
    )
    conexion.execute(
        "UPDATE abet.carga SET subida_por = %s WHERE carga_id = %s", (usuario(conexion, DOCENTE_410), carga_id)
    )
    return carga_id


def conjunto_aprobado(
    conexion: psycopg.Connection, version: str = APROBADO, *, completo: bool = True, aprobado: bool = True,
) -> None:
    """Conjunto de reglas inventado con los valores del caso A03 de db/pruebas/pruebas.sql.

    Con completo falso deja TRATO_SIN_EVIDENCIA en PENDIENTE, así que el R-17 sigue provisional
    aunque el conjunto esté aprobado. Con aprobado falso el conjunto queda en BORRADOR con los cinco
    parámetros DEFINIDOS, y el R-17 también sigue provisional.
    """
    estado, por, fecha = ("APROBADO", "Comité de prueba", "2026-10-01") if aprobado else ("BORRADOR", None, None)
    conexion.execute(
        "INSERT INTO abet.conjunto_reglas (carrera_id, version, estado, aprobado_por, aprobado_en) "
        "SELECT carrera_id, %s, %s, %s, CAST(%s AS date) FROM abet.carrera WHERE codigo = 'AMB'",
        (version, estado, por, fecha),
    )
    trato = ("DEFINIDO", None, "SE_EXCLUYE_DEL_DENOMINADOR") if completo else ("PENDIENTE", None, None)
    valores = [
        ("META_LOGRO", "DEFINIDO", 0.70, None),
        ("NIVEL_ESPERADO", "DEFINIDO", 2, None),
        ("CORTE_ROJO", "DEFINIDO", 0.50, None),
        ("CONVERSION_NIVEL_0_1", "DEFINIDO", None, None),
        ("TRATO_SIN_EVIDENCIA", *trato),
    ]
    for clave, estado, numero, texto in valores:
        conexion.execute(
            "INSERT INTO abet.parametro_valor (conjunto_reglas_id, clave, estado, valor_numero, valor_texto) "
            "SELECT conjunto_reglas_id, %s, %s, %s, %s FROM abet.conjunto_reglas WHERE version = %s",
            (clave, estado, numero, texto, version),
        )
    for nivel, valor in ((1, 0.0), (2, 0.3333), (3, 0.6667), (4, 1.0)):
        conexion.execute(
            "INSERT INTO abet.conversion_nivel_0_1 (conjunto_reglas_id, nivel_original, valor_0_1) "
            "SELECT conjunto_reglas_id, %s, %s FROM abet.conjunto_reglas WHERE version = %s",
            (nivel, valor, version),
        )


def conjunto_pendiente(conexion: psycopg.Connection, version: str) -> None:
    """Conjunto de reglas inventado en BORRADOR con sus cinco parámetros en PENDIENTE, sin nivel esperado ni meta."""
    conexion.execute(
        "INSERT INTO abet.conjunto_reglas (carrera_id, version) "
        "SELECT carrera_id, %s FROM abet.carrera WHERE codigo = 'AMB'",
        (version,),
    )
    conexion.execute(
        "INSERT INTO abet.parametro_valor (conjunto_reglas_id, clave, estado) "
        "SELECT cr.conjunto_reglas_id, p.clave, 'PENDIENTE' FROM abet.conjunto_reglas cr, abet.parametro p "
        "WHERE cr.version = %s",
        (version,),
    )


def reemplazar(
    conexion: psycopg.Connection,
    anterior: int,
    *,
    nombre_archivo: str | None = None,
    hoja: str = HOJA_410,
    sin_fila: int | None = None,
    rechazo: tuple[int, str, str] | None = None,
    conjunto: str | None = None,
) -> int:
    """Carga nueva que copia las columnas, los avisos, las filas y las mediciones de la anterior y la reemplaza.

    Con nombre_archivo registra otro archivo, y sin él reutiliza el de la anterior. sin_fila deja fuera
    las mediciones de esa fila, y rechazo es la fila, el PI y el motivo de su RECHAZA_FILA.
    """
    archivo_id = uno(conexion, "SELECT archivo_id FROM abet.carga WHERE carga_id = %s", (anterior,))
    if nombre_archivo is not None:
        archivo_id = uno(
            conexion,
            "INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos) "
            "SELECT %s, %s, %s, filas_de_datos FROM abet.carga WHERE carga_id = %s RETURNING archivo_id",
            (huella_de(nombre_archivo), nombre_archivo, hoja, anterior),
        )
    nueva = int(uno(
        conexion,
        "INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, "
        "programa_version, reemplaza_carga_id, subida_por) "
        "SELECT c.seccion_id, %s, c.filas_de_datos, c.carrera_id, "
        "coalesce((SELECT conjunto_reglas_id FROM abet.conjunto_reglas WHERE version = %s), c.conjunto_reglas_id), "
        "'v0.0.0-prueba', c.carga_id, c.subida_por FROM abet.carga c WHERE c.carga_id = %s RETURNING carga_id",
        (archivo_id, conjunto, anterior),
    ))
    conexion.execute(
        "INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, "
        "plan_medicion_id, pi_id, pi_codigo, posicion, encabezado, bb_columna_id, puntaje_maximo_declarado) "
        "SELECT %s, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id, pi_id, pi_codigo, posicion, "
        "encabezado, bb_columna_id, puntaje_maximo_declarado FROM abet.carga_columna WHERE carga_id = %s",
        (nueva, anterior),
    )
    conexion.execute(
        "INSERT INTO abet.rechazo_fila (carga_id, fila_origen, carga_columna_id, motivo, efecto) "
        "SELECT %s, NULL, nc.carga_columna_id, r.motivo, r.efecto FROM abet.rechazo_fila r "
        "JOIN abet.carga_columna ac ON ac.carga_columna_id = r.carga_columna_id "
        "JOIN abet.carga_columna nc ON nc.carga_id = %s AND nc.pi_id = ac.pi_id "
        "WHERE r.carga_id = %s AND r.efecto = 'AVISO'",
        (nueva, nueva, anterior),
    )
    excluida = -1 if sin_fila is None else sin_fila
    conexion.execute(
        "INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id) "
        "SELECT %s, fila_origen, estudiante_id FROM abet.carga_fila WHERE carga_id = %s AND fila_origen <> %s",
        (nueva, anterior, excluida),
    )
    conexion.execute(
        "INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, "
        "nivel_original, fila_origen) "
        "SELECT %s, nc.carga_columna_id, m.pi_id, m.estudiante_id, m.estado_evidencia, m.nivel_original, m.fila_origen "
        "FROM abet.medicion m JOIN abet.carga_columna nc ON nc.carga_id = %s AND nc.pi_id = m.pi_id "
        "WHERE m.carga_id = %s AND m.fila_origen <> %s",
        (nueva, nueva, anterior, excluida),
    )
    rechazadas = 0
    if rechazo is not None:
        fila, pi, motivo = rechazo
        conexion.execute(
            "INSERT INTO abet.rechazo_fila (carga_id, fila_origen, carga_columna_id, motivo, efecto) "
            "SELECT %s, %s, carga_columna_id, %s, 'RECHAZA_FILA' FROM abet.carga_columna "
            "WHERE carga_id = %s AND pi_codigo = %s",
            (nueva, fila, motivo, nueva, pi),
        )
        rechazadas = 1
    conexion.execute("UPDATE abet.carga SET estado = 'REEMPLAZADA' WHERE carga_id = %s", (anterior,))
    conexion.execute(
        "UPDATE abet.carga SET estado = 'PUBLICADA', filas_leidas = filas_de_datos, "
        "filas_aceptadas = filas_de_datos - %s, filas_rechazadas = %s, terminada_en = clock_timestamp() "
        "WHERE carga_id = %s",
        (rechazadas, rechazadas, nueva),
    )
    return nueva


def con_error(conexion: psycopg.Connection, anterior: int) -> int:
    """Reemplaza la carga correcta de la 410 por la del export con el 5 en el PI 5.2 de la fila 3."""
    return reemplazar(
        conexion, anterior, nombre_archivo="export_inventado_410_con_error.xlsx", sin_fila=3,
        rechazo=(3, "5.2", "NIVEL_FUERA_DE_ESCALA"),
    )


def aprobar(conexion: psycopg.Connection, anterior: int) -> int:
    """Reemplaza la carga con el mismo archivo y el conjunto R-PRUEBA-APROBADO, como el caso A03."""
    conjunto_aprobado(conexion)
    return reemplazar(conexion, anterior, conjunto=APROBADO)


def publicar(
    conexion: psycopg.Connection,
    *,
    asignatura: str,
    numero: str,
    pis: Sequence[str],
    filas: Sequence[Fila],
    nombre_archivo: str,
    hoja: str | None = None,
    conjunto: str = BORRADOR,
    subida_por: str | None = DOCENTE_410,
    rechazos_de_fila: Sequence[tuple[int, str | None, str]] = (),
    avisos: Sequence[tuple[str | None, str]] = (),
    puntajes: dict[str, float | None] | None = None,
    estado: str = "PUBLICADA",
) -> int:
    """Carga de una sección del plan con sus columnas, filas, mediciones, rechazos de fila y avisos.

    Cada rechazo de fila es (fila, PI o None, motivo) y cada aviso es (PI o None, motivo). Las filas
    rechazadas cuentan como filas de datos, y la carga queda en el estado pedido.
    """
    seccion_id = seccion(conexion, asignatura, numero)
    filas_de_datos = len(filas) + len(rechazos_de_fila)
    archivo_id = uno(
        conexion,
        "INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos) "
        "VALUES (%s, %s, %s, %s) RETURNING archivo_id",
        (huella_de(nombre_archivo), nombre_archivo, hoja, filas_de_datos),
    )
    autor = usuario(conexion, subida_por) if subida_por else None
    carga_id = int(uno(
        conexion,
        "INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, "
        "programa_version, subida_por) "
        "SELECT %s, %s, %s, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba', %s "
        "FROM abet.conjunto_reglas cr WHERE cr.version = %s RETURNING carga_id",
        (seccion_id, archivo_id, filas_de_datos, autor, conjunto),
    ))
    columnas = _columnas(conexion, carga_id, seccion_id, pis, puntajes or {})
    for fila in filas:
        _fila(conexion, carga_id, fila, pis, columnas)
    for fila_origen, pi, motivo in rechazos_de_fila:
        conexion.execute(
            "INSERT INTO abet.rechazo_fila (carga_id, fila_origen, carga_columna_id, motivo, efecto) "
            "VALUES (%s, %s, %s, %s, 'RECHAZA_FILA')",
            (carga_id, fila_origen, columnas.get(pi or ""), motivo),
        )
    for pi, motivo in avisos:
        conexion.execute(
            "INSERT INTO abet.rechazo_fila (carga_id, fila_origen, carga_columna_id, motivo, efecto) "
            "VALUES (%s, NULL, %s, %s, 'AVISO')",
            (carga_id, columnas.get(pi or ""), motivo),
        )
    conexion.execute(
        "UPDATE abet.carga SET estado = %s, filas_leidas = %s, filas_aceptadas = %s, filas_rechazadas = %s, "
        "terminada_en = clock_timestamp() WHERE carga_id = %s",
        (estado, filas_de_datos, len(filas), len(rechazos_de_fila), carga_id),
    )
    return carga_id


def rechazar(
    conexion: psycopg.Connection,
    *,
    motivo: str,
    nombre_archivo: str,
    hoja: str | None = HOJA_410,
    pi: str | None = None,
    asignatura: str = "450002",
    numero: str = "410",
    conjunto: str = BORRADOR,
    filas_de_datos: int = 11,
) -> int:
    """Carga RECHAZADA por estructura, sección o periodo, con su único RECHAZA_CARGA (BR-CARGA-13).

    pi es el PI que falta (PI_DEL_PLAN_AUSENTE) o que se repite (PI_REPETIDO), que la carga guarda en
    rechazo_fila.pi_id.
    """
    seccion_id = seccion(conexion, asignatura, numero)
    archivo_id = uno(
        conexion,
        "INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos) "
        "VALUES (%s, %s, %s, %s) RETURNING archivo_id",
        (huella_de(nombre_archivo), nombre_archivo, hoja, filas_de_datos),
    )
    carga_id = int(uno(
        conexion,
        "INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, "
        "programa_version, subida_por) "
        "SELECT %s, %s, %s, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba', %s "
        "FROM abet.conjunto_reglas cr WHERE cr.version = %s RETURNING carga_id",
        (seccion_id, archivo_id, filas_de_datos, usuario(conexion, DOCENTE_410), conjunto),
    ))
    conexion.execute(
        "INSERT INTO abet.rechazo_fila (carga_id, fila_origen, carga_columna_id, motivo, efecto, pi_id) "
        "VALUES (%s, NULL, NULL, %s, 'RECHAZA_CARGA', "
        "(SELECT p.pi_id FROM abet.pi p "
        "JOIN abet.catalogo_version cv ON cv.catalogo_version_id = p.catalogo_version_id "
        "WHERE cv.codigo = 'AMB-2026' AND p.codigo = %s))",
        (carga_id, motivo, pi),
    )
    conexion.execute(
        "UPDATE abet.carga SET estado = 'RECHAZADA', terminada_en = clock_timestamp() WHERE carga_id = %s",
        (carga_id,),
    )
    return carga_id


def _columnas(
    conexion: psycopg.Connection,
    carga_id: int,
    seccion_id: int,
    pis: Sequence[str],
    puntajes: dict[str, float | None],
) -> dict[str, int]:
    columnas: dict[str, int] = {}
    for posicion, pi in enumerate(pis, start=5):
        puntaje = puntajes.get(pi, 4)
        encabezado = f"{pi} [Total Pts: {puntaje if puntaje is not None else 0} Score] |{90000 + posicion}"
        columnas[pi] = int(uno(
            conexion,
            "INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, "
            "plan_medicion_id, pi_id, pi_codigo, posicion, encabezado, bb_columna_id, puntaje_maximo_declarado) "
            "SELECT c.carga_id, s.seccion_id, c.carrera_id, s.periodo_id, s.asignatura_id, pm.plan_medicion_id, "
            "pm.pi_id, p.codigo, %s, %s, %s, %s "
            "FROM abet.carga c JOIN abet.seccion s ON s.seccion_id = %s "
            "JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id "
            "AND pm.carrera_id = c.carrera_id "
            "JOIN abet.pi p ON p.pi_id = pm.pi_id AND p.codigo = %s WHERE c.carga_id = %s "
            "RETURNING carga_columna_id",
            (posicion, encabezado, str(90000 + posicion), puntaje, seccion_id, pi, carga_id),
        ))
    return columnas


def _fila(
    conexion: psycopg.Connection, carga_id: int, fila: Fila, pis: Sequence[str], columnas: dict[str, int],
) -> None:
    conexion.execute("INSERT INTO abet.estudiante (codigo) VALUES (%s) ON CONFLICT DO NOTHING", (fila.codigo,))
    estudiante_id = uno(conexion, "SELECT estudiante_id FROM abet.estudiante WHERE codigo = %s", (fila.codigo,))
    conexion.execute(
        "INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id) VALUES (%s, %s, %s)",
        (carga_id, fila.fila_origen, estudiante_id),
    )
    for pi, nivel in zip(pis, fila.niveles, strict=True):
        conexion.execute(
            "INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, "
            "nivel_original, fila_origen) "
            "SELECT %s, carga_columna_id, pi_id, %s, %s, %s, %s FROM abet.carga_columna WHERE carga_columna_id = %s",
            (carga_id, estudiante_id, "CALIFICADO" if nivel is not None else "SIN_EVIDENCIA", nivel,
             fila.fila_origen, columnas[pi]),
        )


def filas_inventadas(cantidad: int, *, desde: int, niveles: Sequence[int | None]) -> list[Fila]:
    """cantidad filas desde la fila 2, con códigos inventados consecutivos y los mismos niveles en cada una."""
    return [Fila(2 + i, str(desde + i), tuple(niveles)) for i in range(cantidad)]
