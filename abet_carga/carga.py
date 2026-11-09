"""Carga del export en la base en una sola transacción (T033 de specs/001-mvp-carga-r17/tasks.md).

Aplica las reglas de negocio (business rules, BR) BR-CARGA-01 a BR-CARGA-03 y BR-CARGA-06 a
BR-CARGA-16 de specs/features/carga-export/carga-export.spec.md. cargar() es la función que
comparten el comando de carga y la ruta POST /api/secciones/{seccion_id}/cargas. Devuelve un
ResultadoCarga con el resultado, el código del protocolo de transferencia de hipertexto (Hypertext
Transfer Protocol, HTTP) que le asigna el contrato de la interfaz de programación de aplicaciones
(application programming interface, API), en docs/03-api/contrato.md del Front, el mensaje de ese
contrato y el carga_id cuando la carga existe. La biblioteca no importa FastAPI ni app/, así que la
ruta comprueba con app/permisos.py el alcance de la sección (BR-ACCESO-07 y BR-ACCESO-08) antes de
llamar a cargar(), y arma el cuerpo de la constancia con abet_carga/constancia.py (T035).

Orden de cargar(), el de BR-CARGA-03.
1. La sección elegida, su plan de medición y el conjunto de reglas de CONJUNTO_REGLAS, en una
   transacción de solo lectura. Una sección que no existe da 404 (propuesta) y una sin plan da 422,
   sin rastro. Un conjunto de reglas que la base no conoce para la carrera del plan lanza
   ConfiguracionInvalida, porque es un defecto del despliegue y no del export.
2. La huella SHA-256 (Secure Hash Algorithm de 256 bits) de los bytes recibidos, que el resultado
   lleva desde este paso para el registro de la aplicación (BR-CARGA-08).
3. El tope de 1 MB (BR-CARGA-04), la primera revisión de lector.leer().
4. La extensión, el formato por el contenido y su lectura, que es la revisión del zip y la apertura
   del libro o la decodificación y la lectura del texto, con el tope de 5 000 filas de datos
   (BR-CARGA-05 y spec 003). leer() lanza ArchivoIlegible con su motivo y su detalle, y cargar()
   responde 422 sin rastro. Un export de texto no tiene hoja, así que archivo_origen.hoja queda nula
   y su sección sale solo del nombre (BR-CARGA-11).
5. La guardia de códigos inventados, encendida salvo con GUARDIA_DATOS_INVENTADOS=0 (BR-CARGA-07). Un
   código fuera de 99000000 a 99999999 da 422 sin rastro, antes de buscar la huella en la base.
6. Ya en la transacción de la carga, la huella en abet.archivo_origen. PUBLICADA en la sección da 200
   con esa carga, y PUBLICADA en otra sección da 409 sin el carga_id ni la sección ajena (BR-CARGA-09).
7. Otra carga PUBLICADA en la sección, que da 409 con el número de la sección (BR-CARGA-10).
8. La sección que ni la hoja ni el nombre del archivo declaran, que da 422 sin rastro en el corte 1
   (BR-CARGA-11).
9. La validación en memoria de validacion.validar() y las escrituras de BR-CARGA-11 a BR-CARGA-16.

Las escrituras del paso 9 empiezan por archivo_origen, salvo que la huella ya esté registrada, y por
carga en EN_CURSO con subida_por, conjunto_reglas_id y programa_version. Siguen el rechazo de una
carga RECHAZADA entera, también la de SIN_CALIFICACIONES, que no acepta ningún nivel (spec 003,
D-31), con el pi_id del indicador de desempeño (performance indicator, PI) que falta o que se repite,
o bien las columnas del plan, los rechazos de fila, los avisos, los estudiantes,
carga_fila y medicion. Un UPDATE cierra la carga con su estado, sus tres cuentas y
terminada_en = clock_timestamp(), y la publica solo si acepta al menos una fila (BR-CARGA-16). Una
huella que solo tiene cargas RECHAZADA o REEMPLAZADA presta su archivo_id a la carga nueva, que se
coteja con el nombre que ese archivo ya tiene registrado. Así la constancia leída después nombra la
misma sección que la respuesta, porque el archivo es su huella (BR-CARGA-09). El nombre se corta en
255 caracteres, el ancho de archivo_origen.nombre_archivo, antes de cotejarlo y de guardarlo.

Cualquier error de la base, también un corte de la conexión, deshace la transacción entera y da 500
con el SQLSTATE, el código de cinco caracteres con que PostgreSQL identifica el error, y el nombre de
la restricción, nunca con el DETAIL, que repite la fila (BR-CARGA-02 y BR-CARGA-08). La subida que
llega segunda a uq_archivo_origen_sha256, uq_carga_publicada_por_seccion o uq_carga_archivo_util se
deshace y repite una sola vez los pasos 6 a 9, que ya ven lo que confirmó la otra y responden su 200
o su 409 (BR-CARGA-09 y BR-CARGA-10).

La conexión llega sin una transacción abierta, porque cargar() abre y confirma las suyas, y cargar()
le fija prepare_threshold=None, porque el agrupador de conexiones de Neon (pooler) no admite
sentencias preparadas y executemany() las prepara siempre. Puede ser la del dueño de la base o la del
rol de la aplicación de db/plataforma/neon/crear_rol_app.sql, que alcanza con sus INSERT y con el
UPDATE de estado, cuentas y terminada_en.

Ajustes a la interfaz que propone el plan de la demo. cargar() suma configuracion, que sale de
Configuracion.desde_entorno() si no llega, porque el conjunto de reglas y la guardia son del
despliegue y nunca de la petición (BR-CARGA-01 y BR-CARGA-07). ResultadoCarga suma sha256, motivo y
detalle, para el registro de un archivo detenido, y sqlstate y restriccion, para el de una falla, y
ninguno de los cinco va al cuerpo de la respuesta. mensaje_de_carga_rechazada() arma el mensaje de una carga
RECHAZADA, y la constancia puede usarlo con lo que lee de la base.

Casos que la carga no resuelve. Una carga es de una sola carrera (V1_07), así que un plan con PI de
dos carreras queda bloqueado, y sus columnas chocan con fk_carga_columna_plan y dan 500 sin rastro.
Un usuario_id que no existe choca igual con fk_carga_subida_por.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any

import psycopg
from psycopg import Connection, errors, pq
from psycopg.rows import namedtuple_row

import abet_carga
from abet_carga.lector import huella, leer
from abet_carga.modelos import (
    ArchivoIlegible,
    CodigoNoInventado,
    ColumnaDelPlan,
    ContextoSeccion,
    Efecto,
    FilaAceptada,
    LibroLeido,
    Motivo,
    PiDelPlan,
    Rechazo,
    SeccionDeclarada,
    SeccionSinDeclarar,
    Validacion,
)
from abet_carga.validacion import guardia, seccion_declarada, validar

# Ancho de archivo_origen.nombre_archivo.
LARGO_NOMBRE = 255

_SECCION = """
SELECT s.numero, s.periodo_id, s.asignatura_id, pe.codigo AS periodo, a.codigo AS asignatura
FROM abet.seccion s
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
WHERE s.seccion_id = %s
"""
_PLAN = """
SELECT pm.plan_medicion_id, pm.pi_id, p.codigo, pm.carrera_id, c.codigo AS carrera
FROM abet.plan_medicion pm
JOIN abet.pi p ON p.pi_id = pm.pi_id
JOIN abet.carrera c ON c.carrera_id = pm.carrera_id
WHERE pm.periodo_id = %s AND pm.asignatura_id = %s
ORDER BY pm.pi_id
"""
_REGLAS = "SELECT conjunto_reglas_id FROM abet.conjunto_reglas WHERE carrera_id = %s AND version = %s"
# uq_carga_archivo_util admite una sola carga PUBLICADA por archivo, así que la consulta da una fila o ninguna.
_REGISTRADO = """
SELECT ao.archivo_id, ao.nombre_archivo, c.carga_id AS publicada, c.seccion_id AS seccion_publicada
FROM abet.archivo_origen ao
LEFT JOIN abet.carga c ON c.archivo_id = ao.archivo_id AND c.estado = 'PUBLICADA'
WHERE ao.sha256 = %s
"""
_PUBLICADA_EN_LA_SECCION = "SELECT carga_id FROM abet.carga WHERE seccion_id = %s AND estado = 'PUBLICADA'"
# Índices únicos con que choca la subida que llega segunda cuando otra confirma antes (BR-CARGA-09 y BR-CARGA-10).
_CARRERAS = frozenset({"uq_archivo_origen_sha256", "uq_carga_publicada_por_seccion", "uq_carga_archivo_util"})
_ARCHIVO = """
INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)
VALUES (%s, %s, %s, %s)
RETURNING archivo_id
"""
_CARGA = """
INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version,
                        subida_por)
VALUES (%s, %s, %s, %s, %s, %s, %s)
RETURNING carga_id
"""
_COLUMNA = """
INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id, pi_id,
                                pi_codigo, posicion, encabezado, bb_columna_id, puntaje_maximo_declarado)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
RETURNING carga_columna_id
"""
_RECHAZO = """
INSERT INTO abet.rechazo_fila (carga_id, fila_origen, carga_columna_id, motivo, efecto, pi_id)
VALUES (%s, %s, %s, %s, %s, %s)
"""
_ESTUDIANTES = "INSERT INTO abet.estudiante (codigo) SELECT unnest(%s::varchar[]) ON CONFLICT (codigo) DO NOTHING"
_IDS_DE_ESTUDIANTES = "SELECT codigo, estudiante_id FROM abet.estudiante WHERE codigo = ANY(%s)"
_FILA = "INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id) VALUES (%s, %s, %s)"
_MEDICION = """
INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original,
                           fila_origen)
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""
# now() es la hora de inicio de la transacción, la de iniciada_en, y clock_timestamp() la del cierre.
_CIERRE = """
UPDATE abet.carga
SET estado = %s, filas_leidas = %s, filas_aceptadas = %s, filas_rechazadas = %s, terminada_en = clock_timestamp()
WHERE carga_id = %s
"""


class ConfiguracionInvalida(RuntimeError):
    """El despliegue no trae lo que la carga necesita, como un CONJUNTO_REGLAS que la base no conoce."""


@dataclass(frozen=True)
class Configuracion:
    """Configuración del despliegue, nunca de la petición (BR-CARGA-01 y BR-CARGA-07)."""

    conjunto_reglas: str
    guardia_datos_inventados: bool = True

    @classmethod
    def desde_entorno(cls, entorno: Mapping[str, str] | None = None) -> Configuracion:
        """Lee CONJUNTO_REGLAS y GUARDIA_DATOS_INVENTADOS, de os.environ si no llega otro entorno.

        La guardia queda encendida salvo con GUARDIA_DATOS_INVENTADOS=0, así que una variable que
        falta o un valor mal escrito no la apagan.
        """
        entorno = os.environ if entorno is None else entorno
        conjunto = entorno.get("CONJUNTO_REGLAS", "").strip()
        if not conjunto:
            raise ConfiguracionInvalida("Falta CONJUNTO_REGLAS, el conjunto de reglas de las cargas nuevas.")
        guardia_encendida = entorno.get("GUARDIA_DATOS_INVENTADOS", "1").strip() != "0"
        return cls(conjunto_reglas=conjunto, guardia_datos_inventados=guardia_encendida)


class Resultado(StrEnum):
    """Resultado de cargar(), con el código HTTP que le asigna el contrato en ResultadoCarga.codigo_http.

    PUBLICADA y RECHAZADA son cargas nuevas (201), y YA_PUBLICADA es la carga del mismo archivo en la
    sección (200). EN_OTRA_SECCION y SECCION_CON_CARGA son los 409 de BR-CARGA-09 y BR-CARGA-10, y
    SECCION_INEXISTENTE es el 404 (propuesta). SIN_PLAN, ILEGIBLE, GUARDIA y SECCION_SIN_DECLARAR son
    los 422 sin rastro, y FALLA es el 500 con la transacción deshecha.
    """

    PUBLICADA = "PUBLICADA"
    RECHAZADA = "RECHAZADA"
    YA_PUBLICADA = "YA_PUBLICADA"
    EN_OTRA_SECCION = "EN_OTRA_SECCION"
    SECCION_CON_CARGA = "SECCION_CON_CARGA"
    SECCION_INEXISTENTE = "SECCION_INEXISTENTE"
    SIN_PLAN = "SIN_PLAN"
    ILEGIBLE = "ILEGIBLE"
    GUARDIA = "GUARDIA"
    SECCION_SIN_DECLARAR = "SECCION_SIN_DECLARAR"
    FALLA = "FALLA"


_CODIGO_HTTP = {
    Resultado.PUBLICADA: 201,
    Resultado.RECHAZADA: 201,
    Resultado.YA_PUBLICADA: 200,
    Resultado.EN_OTRA_SECCION: 409,
    Resultado.SECCION_CON_CARGA: 409,
    Resultado.SECCION_INEXISTENTE: 404,
    Resultado.SIN_PLAN: 422,
    Resultado.ILEGIBLE: 422,
    Resultado.GUARDIA: 422,
    Resultado.SECCION_SIN_DECLARAR: 422,
    Resultado.FALLA: 500,
}

# Mensajes literales del contrato. Los de 404, 422 sin plan y ninguna fila aceptada son (propuesta).
_FALLA = "La carga no se completó y no se guardó ningún dato. Intente de nuevo."
_EN_OTRA_SECCION = "Este archivo ya está publicado en otra sección. No se cargó."
_SECCION_CON_CARGA = "La sección {seccion} ya tiene una carga publicada. No se cargó el archivo."
_SECCION_INEXISTENTE = "La sección no existe."
_SIN_PLAN = "La carrera aún no registra el plan de medición de esta sección."
_NINGUNA_FILA_ACEPTADA = "Ninguna fila se pudo aceptar. La carga no se publicó."
_MENSAJES_DE_ESTRUCTURA = {
    Motivo.ARCHIVO_SIN_FILAS: "El archivo no trae filas de estudiantes.",
    Motivo.COLUMNA_CODIGO_AUSENTE: "El archivo no tiene la columna Username ni Student ID.",
    Motivo.PI_DEL_PLAN_AUSENTE: "Falta la columna del PI {pi} que el plan de medición pide para esta sección.",
    Motivo.PI_REPETIDO: "El PI {pi} aparece en dos columnas del archivo.",
    Motivo.SIN_CALIFICACIONES: (
        "El archivo no trae ningún nivel en las columnas de los PI del plan. La carga no se publicó."
    ),
}
_OTRA_ASIGNATURA = "El archivo corresponde a la asignatura {declarada} y usted eligió la {elegida}. No se publicó."
_OTRA_SECCION = "El archivo corresponde a la sección {declarada} y usted eligió la {elegida}. No se publicó."
_OTRO_PERIODO = "El archivo corresponde al periodo {declarado} y la sección elegida es de {elegido}. No se publicó."


@dataclass(frozen=True)
class ResultadoCarga:
    """Resultado de cargar(), con el mensaje del contrato y el carga_id cuando la carga existe.

    mensaje es el detail de un error o el mensaje de una carga RECHAZADA, y queda en None en una carga
    PUBLICADA o YA_PUBLICADA. sha256, motivo, el nombre del MotivoIlegible, y detalle, el nombre del
    DetalleIlegible o None (spec 003), van al registro de un archivo detenido, y sqlstate y restriccion
    al de una falla (BR-CARGA-08). Ninguno de esos cinco va al cuerpo de la respuesta, y ninguno trae el
    DETAIL de PostgreSQL ni un valor leído.
    """

    resultado: Resultado
    mensaje: str | None = None
    carga_id: int | None = None
    sha256: str | None = None
    motivo: str | None = None
    detalle: str | None = None
    sqlstate: str | None = None
    restriccion: str | None = None

    @property
    def codigo_http(self) -> int:
        """Código HTTP que el contrato asigna al resultado."""
        return _CODIGO_HTTP[self.resultado]


@dataclass(frozen=True)
class _Seccion:
    """Sección elegida con lo que la carga escribe de ella y el contexto con que se valida el export."""

    seccion_id: int
    periodo_id: int
    asignatura_id: int
    carrera_id: int
    conjunto_reglas_id: int
    contexto: ContextoSeccion
    plan_medicion: Mapping[str, int]


def cargar(
    conexion: Connection[Any],
    contenido: bytes,
    *,
    nombre_archivo: str,
    seccion_id: int,
    usuario_id: int,
    configuracion: Configuracion | None = None,
) -> ResultadoCarga:
    """Carga el export en la sección elegida en una sola transacción y devuelve su resultado.

    contenido son los bytes recibidos, nombre_archivo el nombre que envía el navegador, con o sin
    ruta, y usuario_id quien sube, que queda en carga.subida_por. Lanza ValueError si la conexión trae
    una transacción abierta y ConfiguracionInvalida si el conjunto de reglas no existe. Los demás
    casos, también una falla de la base, vuelven como ResultadoCarga.
    """
    configuracion = Configuracion.desde_entorno() if configuracion is None else configuracion
    if conexion.info.transaction_status != pq.TransactionStatus.IDLE:
        raise ValueError("cargar() necesita una conexión sin una transacción abierta, porque abre y confirma la suya.")
    conexion.prepare_threshold = None
    try:
        return _cargar(conexion, contenido, nombre_archivo, seccion_id, usuario_id, configuracion)
    except psycopg.Error as error:
        return ResultadoCarga(Resultado.FALLA, _FALLA, sqlstate=error.sqlstate, restriccion=error.diag.constraint_name)


def mensaje_de_carga_rechazada(
    rechazo: Rechazo | None, contexto: ContextoSeccion, declarada: SeccionDeclarada | None
) -> str:
    """Mensaje del contrato para una carga RECHAZADA (BR-CARGA-11 a BR-CARGA-13 y BR-CARGA-16).

    rechazo es el RECHAZA_CARGA de la carga, o None si la carga queda RECHAZADA porque no acepta
    ninguna fila. La sección, la asignatura y el periodo del archivo salen de lo que declaran su hoja o
    su nombre, y los elegidos, del contexto de la sección.
    """
    if rechazo is None:
        return _NINGUNA_FILA_ACEPTADA
    if rechazo.motivo in _MENSAJES_DE_ESTRUCTURA:
        return _MENSAJES_DE_ESTRUCTURA[rechazo.motivo].format(pi=rechazo.pi_codigo)
    if declarada is None:
        raise ValueError(f"El mensaje de {rechazo.motivo} necesita la sección que declara el archivo.")
    if rechazo.motivo is Motivo.PERIODO_NO_COINCIDE:
        return _OTRO_PERIODO.format(declarado=declarada.periodo, elegido=contexto.periodo)
    if declarada.curso_codigo != contexto.curso_codigo:
        return _OTRA_ASIGNATURA.format(declarada=declarada.curso_codigo, elegida=contexto.curso_codigo)
    return _OTRA_SECCION.format(declarada=declarada.seccion_codigo, elegida=contexto.seccion_codigo)


def _cargar(
    conexion: Connection[Any],
    contenido: bytes,
    nombre_archivo: str,
    seccion_id: int,
    usuario_id: int,
    configuracion: Configuracion,
) -> ResultadoCarga:
    """Pasos 1 a 9 de BR-CARGA-03, con una segunda vuelta para la subida que llega segunda."""
    with conexion.transaction():
        seccion = _seccion(conexion, seccion_id, configuracion.conjunto_reglas)
    if isinstance(seccion, ResultadoCarga):
        return seccion
    sha256 = huella(contenido)
    try:
        libro = leer(contenido, nombre_archivo=nombre_archivo)
        if configuracion.guardia_datos_inventados:
            guardia(libro)
    except ArchivoIlegible as error:
        detalle = error.detalle.name if error.detalle is not None else None
        return ResultadoCarga(
            Resultado.ILEGIBLE, error.mensaje, sha256=sha256, motivo=error.motivo.name, detalle=detalle
        )
    except CodigoNoInventado as error:
        return ResultadoCarga(Resultado.GUARDIA, error.mensaje, sha256=sha256)
    # La validación coteja el mismo nombre que se guarda, así que la constancia dice lo mismo después.
    libro = replace(libro, nombre_archivo=libro.nombre_archivo[:LARGO_NOMBRE])
    try:
        with conexion.transaction():
            return _registrar(conexion, libro, sha256, seccion, usuario_id)
    except errors.UniqueViolation as error:
        if error.diag.constraint_name not in _CARRERAS:
            raise
    # Otra subida confirmó primero, y la segunda vuelta ve lo que dejó y responde como si llegara después.
    with conexion.transaction():
        return _registrar(conexion, libro, sha256, seccion, usuario_id)


def _seccion(conexion: Connection[Any], seccion_id: int, conjunto_reglas: str) -> _Seccion | ResultadoCarga:
    """Sección elegida con su plan y su conjunto de reglas, o el 404 o el 422 sin rastro (BR-CARGA-01)."""
    with conexion.cursor(row_factory=namedtuple_row) as cursor:
        seccion = cursor.execute(_SECCION, (seccion_id,)).fetchone()
        if seccion is None:
            return ResultadoCarga(Resultado.SECCION_INEXISTENTE, _SECCION_INEXISTENTE)
        plan = cursor.execute(_PLAN, (seccion.periodo_id, seccion.asignatura_id)).fetchall()
    if not plan:
        return ResultadoCarga(Resultado.SIN_PLAN, _SIN_PLAN)
    carrera_id = plan[0].carrera_id
    reglas = conexion.execute(_REGLAS, (carrera_id, conjunto_reglas)).fetchone()
    if reglas is None:
        raise ConfiguracionInvalida(f"CONJUNTO_REGLAS {conjunto_reglas} no existe para la carrera {plan[0].carrera}.")
    contexto = ContextoSeccion(
        periodo=seccion.periodo,
        curso_codigo=seccion.asignatura,
        seccion_codigo=seccion.numero,
        plan=tuple(PiDelPlan(pi.pi_id, pi.codigo) for pi in plan),
    )
    return _Seccion(
        seccion_id=seccion_id,
        periodo_id=seccion.periodo_id,
        asignatura_id=seccion.asignatura_id,
        carrera_id=carrera_id,
        conjunto_reglas_id=reglas[0],
        contexto=contexto,
        plan_medicion={pi.codigo: pi.plan_medicion_id for pi in plan},
    )


def _registrar(
    conexion: Connection[Any], libro: LibroLeido, sha256: str, seccion: _Seccion, usuario_id: int
) -> ResultadoCarga:
    """Pasos 6 a 9 de BR-CARGA-03, dentro de la transacción de la carga."""
    with conexion.cursor(row_factory=namedtuple_row) as cursor:
        registrado = cursor.execute(_REGISTRADO, (sha256,)).fetchone()
    if registrado is not None and registrado.publicada is not None:
        if registrado.seccion_publicada == seccion.seccion_id:
            return ResultadoCarga(Resultado.YA_PUBLICADA, carga_id=registrado.publicada, sha256=sha256)
        return ResultadoCarga(Resultado.EN_OTRA_SECCION, _EN_OTRA_SECCION, sha256=sha256)
    if conexion.execute(_PUBLICADA_EN_LA_SECCION, (seccion.seccion_id,)).fetchone() is not None:
        mensaje = _SECCION_CON_CARGA.format(seccion=seccion.contexto.seccion_codigo)
        return ResultadoCarga(Resultado.SECCION_CON_CARGA, mensaje, sha256=sha256)
    if registrado is not None:
        libro = replace(libro, nombre_archivo=registrado.nombre_archivo)
    try:
        validacion = validar(libro, seccion.contexto)
    except SeccionSinDeclarar as error:
        return ResultadoCarga(Resultado.SECCION_SIN_DECLARAR, error.mensaje, sha256=sha256)
    archivo_id = registrado.archivo_id if registrado is not None else _insertar_archivo(conexion, sha256, libro)
    return _escribir(conexion, libro, archivo_id, seccion, usuario_id, validacion)


def _escribir(
    conexion: Connection[Any],
    libro: LibroLeido,
    archivo_id: int,
    seccion: _Seccion,
    usuario_id: int,
    validacion: Validacion,
) -> ResultadoCarga:
    """Escribe la carga, sus columnas, rechazos, estudiantes, filas y mediciones, y la cierra (BR-CARGA-16)."""
    carga_id = _insertar_carga(conexion, seccion, archivo_id, validacion.filas_de_datos, usuario_id)
    rechazo = validacion.rechazo_de_carga
    if rechazo is not None:
        _insertar_rechazos(conexion, carga_id, (rechazo,), {}, seccion)
        _cerrar(conexion, carga_id, Resultado.RECHAZADA, validacion)
        declarada = seccion_declarada(libro.hoja, libro.nombre_archivo)
        mensaje = mensaje_de_carga_rechazada(rechazo, seccion.contexto, declarada)
        return ResultadoCarga(Resultado.RECHAZADA, mensaje, carga_id)
    columnas = _insertar_columnas(conexion, carga_id, seccion, validacion.columnas)
    _insertar_rechazos(conexion, carga_id, (*validacion.rechazos_de_fila, *validacion.avisos), columnas, seccion)
    if not validacion.publicable:
        _cerrar(conexion, carga_id, Resultado.RECHAZADA, validacion)
        return ResultadoCarga(Resultado.RECHAZADA, mensaje_de_carga_rechazada(None, seccion.contexto, None), carga_id)
    _insertar_filas(conexion, carga_id, validacion.filas_aceptadas, columnas)
    _cerrar(conexion, carga_id, Resultado.PUBLICADA, validacion)
    return ResultadoCarga(Resultado.PUBLICADA, carga_id=carga_id)


def _insertar(conexion: Connection[Any], consulta: str, parametros: Sequence[object]) -> int:
    """Corre un INSERT con RETURNING y devuelve el identificador que asigna la base."""
    fila = conexion.execute(consulta, parametros).fetchone()
    assert fila is not None, "un INSERT con RETURNING devuelve siempre su fila"
    return int(fila[0])


def _insertar_archivo(conexion: Connection[Any], sha256: str, libro: LibroLeido) -> int:
    return _insertar(conexion, _ARCHIVO, (sha256, libro.nombre_archivo, libro.hoja, libro.filas_de_datos))


def _insertar_carga(
    conexion: Connection[Any], seccion: _Seccion, archivo_id: int, filas_de_datos: int, usuario_id: int
) -> int:
    parametros = (
        seccion.seccion_id,
        archivo_id,
        filas_de_datos,
        seccion.carrera_id,
        seccion.conjunto_reglas_id,
        abet_carga.__version__,
        usuario_id,
    )
    return _insertar(conexion, _CARGA, parametros)


def _insertar_columnas(
    conexion: Connection[Any], carga_id: int, seccion: _Seccion, columnas: Sequence[ColumnaDelPlan]
) -> dict[str, tuple[int, int]]:
    """Registra las columnas del plan y devuelve, por código de PI, su carga_columna_id y su pi_id."""
    registradas = {}
    for columna in columnas:
        parametros = (
            carga_id,
            seccion.seccion_id,
            seccion.carrera_id,
            seccion.periodo_id,
            seccion.asignatura_id,
            seccion.plan_medicion[columna.pi_codigo],
            columna.pi_id,
            columna.pi_codigo,
            columna.posicion,
            columna.encabezado,
            columna.bb_columna_id,
            columna.puntaje_maximo_declarado,
        )
        registradas[columna.pi_codigo] = (_insertar(conexion, _COLUMNA, parametros), columna.pi_id)
    return registradas


def _insertar_rechazos(
    conexion: Connection[Any],
    carga_id: int,
    rechazos: Sequence[Rechazo],
    columnas: Mapping[str, tuple[int, int]],
    seccion: _Seccion,
) -> None:
    """Registra rechazos y avisos sin el valor leído, que rechazo_fila no tiene dónde guardar (BR-CARGA-17)."""
    plan = {pi.codigo: pi.pi_id for pi in seccion.contexto.plan}
    filas = []
    for rechazo in rechazos:
        carga_columna_id, pi_id = _referencias(rechazo, columnas, plan)
        filas.append((carga_id, rechazo.fila_origen, carga_columna_id, rechazo.motivo, rechazo.efecto, pi_id))
    with conexion.cursor() as cursor:
        cursor.executemany(_RECHAZO, filas)


def _referencias(
    rechazo: Rechazo, columnas: Mapping[str, tuple[int, int]], plan: Mapping[str, int]
) -> tuple[int | None, int | None]:
    """carga_columna_id y pi_id de un rechazo o de un aviso.

    El PI de una columna registrada va como carga_columna_id, en un rechazo de nivel o en
    PUNTAJE_MAXIMO_DISTINTO, y el PI del plan de un RECHAZA_CARGA, en PI_DEL_PLAN_AUSENTE o
    PI_REPETIDO, va como pi_id. El de COLUMNA_PI_FUERA_DEL_PLAN no va, porque su columna no entra a
    carga_columna y ck_rechazo_fila_pi no lo admite.
    """
    if rechazo.pi_codigo is None:
        return None, None
    if rechazo.efecto is Efecto.RECHAZA_CARGA:
        return None, plan[rechazo.pi_codigo]
    columna = columnas.get(rechazo.pi_codigo)
    return (columna[0] if columna is not None else None), None


def _insertar_filas(
    conexion: Connection[Any], carga_id: int, aceptadas: Sequence[FilaAceptada], columnas: Mapping[str, tuple[int, int]]
) -> None:
    """Registra los estudiantes que faltan, una fila de carga_fila por fila aceptada y sus mediciones.

    Los códigos van ordenados, así que dos cargas a la vez con estudiantes en común toman los candados
    de uq_estudiante_codigo en el mismo orden y no se bloquean entre sí.
    """
    codigos = sorted(fila.codigo for fila in aceptadas)
    conexion.execute(_ESTUDIANTES, (codigos,))
    estudiantes = dict(conexion.execute(_IDS_DE_ESTUDIANTES, (codigos,)).fetchall())
    mediciones = [
        (
            carga_id,
            *columnas[medicion.pi_codigo],
            estudiantes[fila.codigo],
            medicion.estado_evidencia,
            medicion.nivel,
            fila.fila_origen,
        )
        for fila in aceptadas
        for medicion in fila.mediciones
    ]
    with conexion.cursor() as cursor:
        cursor.executemany(_FILA, [(carga_id, fila.fila_origen, estudiantes[fila.codigo]) for fila in aceptadas])
        cursor.executemany(_MEDICION, mediciones)


def _cerrar(conexion: Connection[Any], carga_id: int, estado: Resultado, validacion: Validacion) -> None:
    """Cierra la carga con su estado y sus cuentas, que suman filas_leidas (ck_carga_filas)."""
    parametros = (
        estado.value,
        validacion.filas_leidas,
        len(validacion.filas_aceptadas),
        validacion.filas_rechazadas,
        carga_id,
    )
    conexion.execute(_CIERRE, parametros)
