"""Constancia de una carga, la evidencia que ata un archivo a lo que la base registra de él (T035).

armar(conexion, carga_id) devuelve el cuerpo plano de la regla de negocio (business rule, BR)
BR-R17-10 de specs/features/r17/r17.spec.md, en JavaScript Object Notation (JSON), con los campos y
los nombres del contrato de la interfaz de programación de aplicaciones (application programming
interface, API), en docs/03-api/contrato.md del Front. Lo lee de abet.carga, abet.archivo_origen,
abet.carga_columna, abet.rechazo_fila, abet.pi, abet.conjunto_reglas, abet.parametro_valor y
acceso.usuario_autorizado, con la lectura que db/plataforma/neon/crear_rol_app.sql da al rol de la
aplicación. No escribe nada y no confirma ni deshace la transacción de la conexión que recibe.

La misma función sirve a GET /api/cargas/{carga_id}, al cuerpo de la respuesta 201 o 200 de la
subida, que carga.py pide después de confirmar su transacción, y a la hoja «Constancia» del R-17
(r17.py). Así los tres dicen lo mismo de una carga PUBLICADA, y una carga RECHAZADA tiene la misma
constancia al subirse y al leerse después.

Lo que fija esta función, con lo que la spec viva o el contrato marcan como (propuesta).
1. Las horas van en la forma de la norma ISO 8601 de la Organización Internacional de Normalización
   (International Organization for Standardization, ISO), con el desfase fijo de Lima, -05:00, que
   no cambia desde 1994, así que no dependen de la base de husos horarios del sistema. Conservan los
   microsegundos, porque una carga breve empieza y termina en el mismo segundo y el fin queda
   después del inicio (BR-CARGA-02).
2. provisional repite la expresión de la columna provisional de abet.v_r17_por_pi, porque la vista
   no ve una carga RECHAZADA. parametros_pendientes lista las claves en PENDIENTE, primero las que la
   vista exige para un R-17 oficial (NIVEL_ESPERADO, META_LOGRO y TRATO_SIN_EVIDENCIA) y después
   CORTE_ROJO y CONVERSION_NIVEL_0_1, como el ejemplo del contrato.
3. columnas y avisos siguen el orden del plan, por el resultado del estudiante (student outcome, SO)
   y el número del indicador de desempeño (performance indicator, PI), con los avisos sin PI al
   final, y rechazos va por fila, con el rechazo de la carga primero. puntaje_maximo_declarado
   viaja como número, entero cuando no tiene decimales.
4. Cada rechazo y cada aviso traen su mensaje. Los de PI_DEL_PLAN_AUSENTE, PI_REPETIDO,
   ARCHIVO_SIN_FILAS, COLUMNA_CODIGO_AUSENTE, SECCION_NO_COINCIDE y NIVEL_FUERA_DE_ESCALA son los
   de los escenarios, y los demás son (propuesta). SECCION_NO_COINCIDE y PERIODO_NO_COINCIDE nombran
   lo que declara archivo_origen.hoja o, si la hoja no lo declara, archivo_origen.nombre_archivo,
   con la lectura de validacion.seccion_declarada(). SIN_CALIFICACIONES, el rechazo de una carga
   cuyas filas aceptadas no traen ningún nivel, tiene el mensaje de la spec 003 (US-36 y D-31), con
   fila y pi nulos.
5. mensaje resume el motivo de una carga RECHAZADA, que es el de su RECHAZA_CARGA o, si la carga
   rechaza todas sus filas, «Ninguna fila se pudo aceptar. La carga no se publicó.». En los demás
   estados es nulo.
6. hoja es archivo_origen.hoja tal como está, nula en un export de texto (spec 003, US-34). La
   constancia no la reemplaza por ningún texto, y es el R-17 el que muestra «Sin hoja (export de
   texto)» en su hoja «Constancia».

Ningún elemento trae un campo valor ni valor_leido, porque la base no guarda el valor leído de una
celda (BR-CARGA-17).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row

from abet_carga.validacion import seccion_declarada

HORA_DE_LIMA = timezone(timedelta(hours=-5), "America/Lima")
PARAMETROS_EN_ORDEN = ("NIVEL_ESPERADO", "META_LOGRO", "TRATO_SIN_EVIDENCIA", "CORTE_ROJO", "CONVERSION_NIVEL_0_1")
SIN_FILAS_ACEPTADAS = "Ninguna fila se pudo aceptar. La carga no se publicó."

_CARGA = """
SELECT c.carga_id, c.estado, c.seccion_id, a.codigo AS asignatura, s.numero, pe.codigo AS periodo,
       ao.nombre_archivo, ao.hoja, ao.sha256, ao.filas_de_datos, c.filas_leidas, c.filas_aceptadas,
       c.filas_rechazadas, c.conjunto_reglas_id, cr.version AS conjunto_reglas,
       cr.estado AS conjunto_reglas_estado, c.programa_version, u.correo AS subida_por,
       c.iniciada_en, c.terminada_en
FROM abet.carga c
JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id
JOIN abet.seccion s         ON s.seccion_id = c.seccion_id
JOIN abet.asignatura a      ON a.asignatura_id = s.asignatura_id
JOIN abet.periodo pe        ON pe.periodo_id = s.periodo_id
JOIN abet.conjunto_reglas cr ON cr.conjunto_reglas_id = c.conjunto_reglas_id
LEFT JOIN acceso.usuario_autorizado u ON u.usuario_id = c.subida_por
WHERE c.carga_id = %s
"""

# La expresión de la columna provisional de abet.v_r17_por_pi (R__vista_r17_por_pi.sql).
_REGLAS = """
SELECT cr.estado <> 'APROBADO'
       OR COUNT(CASE WHEN pv.clave IN ('NIVEL_ESPERADO', 'META_LOGRO', 'TRATO_SIN_EVIDENCIA')
                      AND pv.estado = 'DEFINIDO' THEN 1 END) < 3 AS provisional,
       COALESCE(array_agg(pv.clave) FILTER (WHERE pv.estado = 'PENDIENTE'), '{}') AS pendientes
FROM abet.conjunto_reglas cr
LEFT JOIN abet.parametro_valor pv ON pv.conjunto_reglas_id = cr.conjunto_reglas_id
WHERE cr.conjunto_reglas_id = %s
GROUP BY cr.estado
"""

_COLUMNAS = """
SELECT cc.pi_codigo, cc.puntaje_maximo_declarado
FROM abet.carga_columna cc
JOIN abet.pi p ON p.pi_id = cc.pi_id
WHERE cc.carga_id = %s
ORDER BY p.so_numero, p.numero
"""

# El PI de un rechazo de nivel o de un aviso sale de su columna, y el de PI_DEL_PLAN_AUSENTE o
# PI_REPETIDO, de rechazo_fila.pi_id (V1_09).
_RECHAZOS = """
SELECT rf.fila_origen, rf.motivo, rf.efecto, coalesce(cc.pi_codigo, p.codigo) AS pi,
       cc.puntaje_maximo_declarado
FROM abet.rechazo_fila rf
LEFT JOIN abet.carga_columna cc ON cc.carga_columna_id = rf.carga_columna_id
LEFT JOIN abet.pi pc            ON pc.pi_id = cc.pi_id
LEFT JOIN abet.pi p             ON p.pi_id = rf.pi_id
WHERE rf.carga_id = %s
ORDER BY rf.fila_origen NULLS FIRST, coalesce(pc.so_numero, p.so_numero) NULLS LAST,
         coalesce(pc.numero, p.numero) NULLS LAST, rf.rechazo_id
"""

_QUEDA_FUERA = "La fila completa queda fuera"
_DE_FILA = {
    "CODIGO_VACIO": "Fila {fila}, sin código de estudiante. " + _QUEDA_FUERA + ".",
    "CODIGO_INVALIDO": "Fila {fila}, el código de estudiante no tiene 8 cifras. " + _QUEDA_FUERA + ".",
    "CODIGO_DUPLICADO": "Fila {fila}, el código de estudiante ya aparece en una fila anterior. " + _QUEDA_FUERA + ".",
    "NIVEL_FUERA_DE_ESCALA": "Fila {fila}, PI {pi}, nivel fuera de la escala 1 a 4. " + _QUEDA_FUERA + "{tambien}.",
    "NIVEL_NO_NUMERICO": "Fila {fila}, PI {pi}, valor que no es un nivel de 1 a 4. " + _QUEDA_FUERA + "{tambien}.",
}
_FIJOS = {
    "ARCHIVO_SIN_FILAS": "El archivo no trae filas de estudiantes.",
    "COLUMNA_CODIGO_AUSENTE": "El archivo no tiene la columna Username ni Student ID.",
    "PI_DEL_PLAN_AUSENTE": "Falta la columna del PI {pi} que el plan de medición pide para esta sección.",
    "PI_REPETIDO": "El PI {pi} aparece en dos columnas del archivo.",
    "COLUMNA_PI_FUERA_DEL_PLAN": "El archivo trae la columna de un PI que no está en el plan de medición de esta "
                                 "sección. Se ignoró.",
    "SECCION_SIN_DECLARAR": "El archivo no indica su sección. Quien lo subió confirmó la sección elegida.",
    "SIN_CALIFICACIONES": "El archivo no trae ningún nivel en las columnas de los PI del plan. "
                          "La carga no se publicó.",
}


class CargaInexistente(LookupError):
    """La carga pedida no existe, que la API responde con 404 y «La carga no existe.» (propuesta)."""

    mensaje = "La carga no existe."
    codigo_http = 404

    def __init__(self) -> None:
        super().__init__(self.mensaje)


def armar(conexion: psycopg.Connection, carga_id: int) -> dict[str, Any]:
    """Cuerpo de la constancia de BR-R17-10 para cualquier estado de la carga, o CargaInexistente."""
    with conexion.cursor(row_factory=dict_row) as cursor:
        carga = cursor.execute(_CARGA, (carga_id,)).fetchone()
        if carga is None:
            raise CargaInexistente()
        reglas = cursor.execute(_REGLAS, (carga["conjunto_reglas_id"],)).fetchone()
        columnas = cursor.execute(_COLUMNAS, (carga_id,)).fetchall()
        filas = cursor.execute(_RECHAZOS, (carga_id,)).fetchall()
    assert reglas is not None, "fk_carga_reglas garantiza el conjunto de reglas de la carga"
    pis = [columna["pi_codigo"] for columna in columnas]
    elementos = [_elemento(fila, carga, pis) for fila in filas]
    rechazos = [elemento for elemento in elementos if elemento["efecto"] != "AVISO"]
    # Un aviso no es de una fila, así que el contrato lo trae sin el campo fila.
    avisos = [{clave: valor for clave, valor in elemento.items() if clave != "fila"}
              for elemento in elementos if elemento["efecto"] == "AVISO"]
    return {
        "carga_id": carga["carga_id"],
        "estado": carga["estado"],
        "seccion": {"seccion_id": carga["seccion_id"], "asignatura": carga["asignatura"], "numero": carga["numero"],
                    "periodo": carga["periodo"]},
        "nombre_archivo": carga["nombre_archivo"],
        "hoja": carga["hoja"],
        "sha256": carga["sha256"],
        "filas_de_datos": carga["filas_de_datos"],
        "filas_leidas": carga["filas_leidas"],
        "filas_aceptadas": carga["filas_aceptadas"],
        "filas_rechazadas": carga["filas_rechazadas"],
        "mensaje": _mensaje_de_la_carga(carga["estado"], rechazos),
        "columnas": [{"pi": c["pi_codigo"], "puntaje_maximo_declarado": _numero(c["puntaje_maximo_declarado"])}
                     for c in columnas],
        "rechazos": rechazos,
        "avisos": avisos,
        "conjunto_reglas": carga["conjunto_reglas"],
        "conjunto_reglas_estado": carga["conjunto_reglas_estado"],
        "parametros_pendientes": _en_orden(reglas["pendientes"]),
        "provisional": reglas["provisional"],
        "programa_version": carga["programa_version"],
        "subida_por": carga["subida_por"],
        "iniciada_en": _hora(carga["iniciada_en"]),
        "terminada_en": _hora(carga["terminada_en"]),
    }


def lista(elementos: Sequence[str]) -> str:
    """Elementos unidos como en una enumeración en español, «5.1, 5.2 y 5.3»."""
    if len(elementos) <= 1:
        return "".join(elementos)
    return f"{', '.join(elementos[:-1])} y {elementos[-1]}"


def _elemento(fila: dict[str, Any], carga: dict[str, Any], pis: Sequence[str]) -> dict[str, Any]:
    return {
        "fila": fila["fila_origen"],
        "pi": fila["pi"],
        "motivo": fila["motivo"],
        "efecto": fila["efecto"],
        "mensaje": _mensaje(fila, carga, pis),
    }


def _mensaje(fila: dict[str, Any], carga: dict[str, Any], pis: Sequence[str]) -> str:
    motivo, pi = fila["motivo"], fila["pi"]
    if motivo in _DE_FILA:
        otros = [codigo for codigo in pis if codigo != pi]
        tambien = f", también de {lista(otros)}" if otros else ""
        return _DE_FILA[motivo].format(fila=fila["fila_origen"], pi=pi, tambien=tambien)
    if motivo == "PUNTAJE_MAXIMO_DISTINTO":
        return _aviso_de_puntaje(pi, fila["puntaje_maximo_declarado"])
    if motivo == "SECCION_NO_COINCIDE":
        return _otra_seccion(carga)
    if motivo == "PERIODO_NO_COINCIDE":
        return _otro_periodo(carga)
    return _FIJOS[motivo].format(pi=pi)


def _aviso_de_puntaje(pi: str | None, puntaje: Decimal | None) -> str:
    # Un Total Pts de 0 o mayor que numeric(6, 2) entra sin puntaje (D-04), y el aviso no inventa la cifra.
    if puntaje is None:
        declara = "un puntaje máximo que la base no admite,"
    else:
        declara = f"{_cifra(puntaje)} puntos"
    return f"PI {pi}. La columna declara {declara} y sus notas están entre 1 y 4. Se cargó igual."


def _otra_seccion(carga: dict[str, Any]) -> str:
    declarada = seccion_declarada(carga["hoja"], carga["nombre_archivo"])
    if declarada is None:
        return "El archivo corresponde a otra sección. No se publicó."
    if declarada.curso_codigo != carga["asignatura"]:
        return (f"El archivo corresponde a la asignatura {declarada.curso_codigo} "
                f"y usted eligió la {carga['asignatura']}. No se publicó.")
    return (f"El archivo corresponde a la sección {declarada.seccion_codigo} "
            f"y usted eligió la {carga['numero']}. No se publicó.")


def _otro_periodo(carga: dict[str, Any]) -> str:
    declarada = seccion_declarada(carga["hoja"], carga["nombre_archivo"])
    periodo = f"al periodo {declarada.periodo}" if declarada is not None else "a otro periodo"
    return f"El archivo corresponde {periodo} y la sección elegida es de {carga['periodo']}. No se publicó."


def _mensaje_de_la_carga(estado: str, rechazos: Sequence[dict[str, Any]]) -> str | None:
    if estado != "RECHAZADA":
        return None
    de_carga = next((rechazo for rechazo in rechazos if rechazo["efecto"] == "RECHAZA_CARGA"), None)
    return de_carga["mensaje"] if de_carga is not None else SIN_FILAS_ACEPTADAS


def _en_orden(claves: Sequence[str]) -> list[str]:
    def posicion(clave: str) -> tuple[int, str]:
        return (PARAMETROS_EN_ORDEN.index(clave) if clave in PARAMETROS_EN_ORDEN else len(PARAMETROS_EN_ORDEN), clave)

    return sorted(claves, key=posicion)


def _numero(valor: Decimal | None) -> int | float | None:
    if valor is None:
        return None
    return int(valor) if valor == valor.to_integral_value() else float(valor)


def _cifra(valor: Decimal) -> str:
    """Cifra con coma decimal y sin ceros de más, «20» o «4,5»."""
    return format(valor.normalize(), "f").replace(".", ",")


def _hora(valor: datetime | None) -> str | None:
    return valor.astimezone(HORA_DE_LIMA).isoformat() if valor is not None else None
