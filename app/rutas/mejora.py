"""Rutas 14 a 16 de la spec 005, el análisis por indicador de una carga (T032, BR-MEJORA-04 a BR-MEJORA-10).

GET /api/cargas/{carga_id}/mejora responde la declaración vigente y el borrador, con un elemento por PI, y si quien
pide puede editar. PUT /api/cargas/{carga_id}/mejora/borrador guarda el borrador con una sola versión por carga, y
POST /api/cargas/{carga_id}/mejora/declaracion declara una versión exacta del borrador. Las reglas viven en
specs/features/mejora/mejora.spec.md y la forma de cada respuesta en las secciones 13.3 a 13.5 de
docs/03-api/contrato.md del Front.

1. El alcance sale solo de app/permisos.py. La lectura usa puede_leer() y la escritura puede_declarar(), que admite
   solo al profesor asignado (BR-MEJORA-05). Una carga que no existe recibe el mismo 403 que una ajena, y el router
   exige la sesión (BR-ACCESO-10).
2. Las rutas 15 y 16 leen el cuerpo a mano después del alcance, así que un usuario sin permiso recibe 403 aunque su
   cuerpo no sea JSON (AD-23). El orden es 401, 403, los 422 del cuerpo (que no es JSON, claves fuera del contrato,
   campos de otro tipo y PI repetido), el 409 de la carga que no está PUBLICADA, que manda sobre los demás 409 y no
   necesita mirar el semáforo, los 422 de los PI y del texto y, al final, el 409 de la versión. En la ruta 16, el 409
   de la regla sin definir va antes que los 422 de la declaración, porque ningún texto del profesor lo resuelve.
3. Cada causa y cada acción pasa por normalizar(): NFC, \\r\\n como \\n, ningún carácter de control salvo \\n y \\t,
   hasta 800 puntos de código y sin el patrón de códigos y correos de los CHECK de V1_15 (BR-MEJORA-08 y
   BR-MEJORA-10). Un texto vacío se guarda nulo. Ni la respuesta ni el registro repiten el texto, y la violación de un
   CHECK sale como 422 y nunca como 500.
4. El tipo de cada PI lo fija el semáforo de la ruta 13, que app/rutas/resultados.indicadores_de_la_carga() calcula
   en la misma transacción (BR-MEJORA-03). La ruta 16 guarda esa foto (J-40) y comprueba con las funciones de
   abet_carga/r17.py que los recuadros A y B compuestos quepan en el R-17 (BR-R17-04).
5. El estado PROPUESTA de cada indicador declarado lo deriva la ruta 14 y la base no lo guarda (D-42). La herencia
   de US-54 (heredado_de) llega con T036, y hasta entonces heredado_de es nulo.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response
from psycopg.rows import dict_row

from abet_carga import r17
from abet_carga.constancia import HORA_DE_LIMA
from app import permisos, sesion
from app.configuracion import FORMA_INESPERADA, conexion, error, registrar_falla
from app.rutas import resultados

# BR-ACCESO-10. El router exige la sesión, así que ninguna ruta suya responde sin ella aunque la olvide.
router = APIRouter(dependencies=[Depends(sesion.usuario_actual)])

CLAVES_AJENAS = "El cuerpo trae claves que esta ruta no admite."
PI_REPETIDO = "Cada indicador va una sola vez en el cuerpo."
NO_PUBLICADA = "La carga no está publicada y no admite causas ni acciones."
OTRA_PESTANA = "Otra pestaña guardó un texto más reciente."
BORRADOR_CAMBIO = "El borrador cambió después de este guardado. Guarde otra vez antes de declarar."
REGLA_SIN_DEFINIR = "El conjunto de reglas no define la meta o el nivel esperado. La declaración espera a la Coordinación."
INCOMPLETA = "Complete la causa y la acción de cada indicador."
NO_CABE = "El análisis no cabe en el R-17. Acorte la causa o la acción de algún indicador."
TIPO_DEL_SEMAFORO = "El tipo de registro de cada indicador lo fija su semáforo."
DEMASIADO_LARGO = "Cada campo admite hasta 800 caracteres."
CON_CONTROL = "El texto trae caracteres que no se pueden guardar."
CON_CODIGOS = ("La declaración no puede llevar códigos ni correos. Describa las causas y las acciones sin datos de "
               "estudiantes.")
TOPE_DE_CARACTERES = 800
# El mismo patrón ASCII de ck_mejora_borrador_pi_sin_codigos, ck_mejora_declaracion_pi_sin_codigos y Q16 (FR-013):
# un número de exactamente 8 dígitos no rodeado de otros dígitos, o un correo.
CODIGO_O_CORREO = re.compile(r"(^|[^0-9])[0-9]{8}([^0-9]|$)|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+")
# Excel no admite filas de más de 409 puntos, y alto_de_fila_final() de r17.py se detiene en ese tope.
ALTO_MAXIMO = 409.0
_CLAVES_DEL_BORRADOR = frozenset({"version", "indicadores"})
_CLAVES_DEL_INDICADOR = frozenset({"pi", "tipo", "causa", "accion"})
_CLAVES_DE_LA_DECLARACION = frozenset({"version"})
SOLO_LECTURA = resultados.SOLO_LECTURA
ESCRITURA = "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ"

_SECCION_DE_LA_CARGA = "SELECT seccion_id FROM abet.carga WHERE carga_id = %s"
_ESTADO = """
SELECT c.estado, (SELECT r.carga_id FROM abet.carga r WHERE r.reemplaza_carga_id = c.carga_id) AS reemplazada_por
FROM abet.carga c WHERE c.carga_id = %s
"""
_COLUMNAS = "SELECT pi_codigo, pi_id FROM abet.carga_columna WHERE carga_id = %s"
_CABECERA_DEL_BORRADOR = "SELECT version, actualizado_en FROM abet.mejora_borrador WHERE carga_id = %s"
_REGISTROS_DEL_BORRADOR = """
SELECT cc.pi_codigo AS pi, b.causa, b.accion
FROM abet.mejora_borrador_pi b
JOIN abet.carga_columna cc ON cc.carga_id = b.carga_id AND cc.pi_id = b.pi_id
JOIN abet.pi p             ON p.pi_id = b.pi_id
WHERE b.carga_id = %s
ORDER BY p.so_numero, p.numero
"""
_VIGENTE = """
SELECT declaracion_id, version_borrador, declarada_en
FROM abet.mejora_declaracion WHERE carga_id = %s ORDER BY declaracion_id DESC LIMIT 1
"""
_REGISTROS_DECLARADOS = """
SELECT p.codigo AS pi, d.tipo, d.causa, d.accion
FROM abet.mejora_declaracion_pi d
JOIN abet.pi p ON p.pi_id = d.pi_id
WHERE d.declaracion_id = %s
ORDER BY p.so_numero, p.numero
"""
_PRIMER_BORRADOR = """
INSERT INTO abet.mejora_borrador (carga_id, version, actualizado_por) VALUES (%s, 1, %s)
ON CONFLICT (carga_id) DO NOTHING RETURNING version, actualizado_en
"""
_SIGUIENTE_BORRADOR = """
UPDATE abet.mejora_borrador SET version = version + 1, actualizado_en = now(), actualizado_por = %s
WHERE carga_id = %s AND version = %s RETURNING version, actualizado_en
"""
_GUARDAR_REGISTRO = """
INSERT INTO abet.mejora_borrador_pi (carga_id, pi_id, causa, accion) VALUES (%s, %s, %s, %s)
ON CONFLICT (carga_id, pi_id) DO UPDATE SET causa = EXCLUDED.causa, accion = EXCLUDED.accion
"""
_VACIAR_LOS_DEMAS = """
UPDATE abet.mejora_borrador_pi SET causa = NULL, accion = NULL
WHERE carga_id = %s AND NOT (pi_id = ANY(CAST(%s AS smallint[])))
"""
_BORRADOR_PARA_DECLARAR = "SELECT version FROM abet.mejora_borrador WHERE carga_id = %s FOR UPDATE"
_DECLARAR = """
INSERT INTO abet.mejora_declaracion (carga_id, version_borrador, declarada_por) VALUES (%s, %s, %s)
RETURNING declaracion_id, declarada_en
"""
_DECLARAR_PI = """
INSERT INTO abet.mejora_declaracion_pi (declaracion_id, pi_id, carga_id, tipo, causa, accion, logro_pct, meta_pct,
                                        semaforo)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

_CUERPO_DEL_BORRADOR = {"requestBody": {"required": True, "content": {"application/json": {"schema": {
    "type": "object", "required": ["version", "indicadores"], "additionalProperties": False,
    "properties": {"version": {"type": "integer", "minimum": 0}, "indicadores": {"type": "array", "items": {
        "type": "object", "required": ["pi", "tipo"], "additionalProperties": False,
        "properties": {"pi": {"type": "string"}, "tipo": {"type": ["string", "null"]},
                       "causa": {"type": ["string", "null"], "maxLength": TOPE_DE_CARACTERES},
                       "accion": {"type": ["string", "null"], "maxLength": TOPE_DE_CARACTERES}}}}}}}}}}
_CUERPO_DE_LA_DECLARACION = {"requestBody": {"required": True, "content": {"application/json": {"schema": {
    "type": "object", "required": ["version"], "additionalProperties": False,
    "properties": {"version": {"type": "integer", "minimum": 0}}}}}}}


class Rechazo(Exception):
    """Respuesta de error que corta la ruta, con su código, su detail y los campos que el contrato le suma."""

    def __init__(self, codigo: int, mensaje: str, **extra: Any) -> None:
        super().__init__(mensaje)
        self.codigo, self.mensaje, self.extra = codigo, mensaje, extra

    def respuesta(self) -> JSONResponse:
        return JSONResponse({"detail": self.mensaje, **self.extra}, status_code=self.codigo)


# Funciones puras del texto y de la cabida

def normalizar(texto: str | None) -> str | None:
    """Causa o acción en NFC, con \\n como salto de línea, o None si viene vacía; Rechazo 422 si no se puede guardar.

    El orden de los 422 es el del contrato: el largo en puntos de código después de normalizar, los caracteres de
    control salvo \\n y \\t, y los códigos o correos (BR-MEJORA-08 y BR-MEJORA-10). Un texto de solo espacios se guarda
    tal cual en el borrador, y la ruta 16 lo trata como vacío.
    """
    if texto is None or texto == "":
        return None
    limpio = unicodedata.normalize("NFC", texto).replace("\r\n", "\n")
    if len(limpio) > TOPE_DE_CARACTERES:
        raise Rechazo(422, DEMASIADO_LARGO)
    if any(unicodedata.category(caracter) == "Cc" and caracter not in "\n\t" for caracter in limpio):
        raise Rechazo(422, CON_CONTROL)
    if CODIGO_O_CORREO.search(limpio):
        raise Rechazo(422, CON_CODIGOS)
    return limpio


def cabe_en_el_r17(texto: str) -> bool:
    """Si un recuadro compuesto cabe en el alto de fila que r17.py le daría (BR-R17-04 y J-39).

    alto_de_fila_final() da 15 puntos por línea menos los 30 de las dos primeras filas y se detiene en 409, el máximo
    de Excel. Como 15 × n − 30 nunca vale 409 para un n entero, el texto cabe si su alto queda debajo del tope y no
    cabe si el cálculo lo recorta en él.
    """
    return r17.alto_de_fila_final(r17.lineas_del_recuadro(texto)) < ALTO_MAXIMO


def _en_blanco(texto: str | None) -> bool:
    return texto is None or texto.strip() == ""


def _hora(valor: datetime) -> str:
    return valor.astimezone(HORA_DE_LIMA).isoformat()


# Lectura del cuerpo

async def _cuerpo_json(request: Request) -> Any:
    try:
        return json.loads((await request.body()).decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise Rechazo(422, FORMA_INESPERADA) from None


def _version(cuerpo: dict[str, Any]) -> int:
    version = cuerpo.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 0:
        raise Rechazo(422, FORMA_INESPERADA)
    return version


def _pedido_de_borrador(cuerpo: Any) -> tuple[int, list[dict[str, Any]]]:
    """Versión e indicadores de un PUT, con la forma revisada y sin PI repetidos, todavía sin mirar la carga."""
    if not isinstance(cuerpo, dict):
        raise Rechazo(422, FORMA_INESPERADA)
    indicadores = cuerpo.get("indicadores")
    elementos = indicadores if isinstance(indicadores, list) else []
    if set(cuerpo) - _CLAVES_DEL_BORRADOR or any(
            isinstance(elemento, dict) and set(elemento) - _CLAVES_DEL_INDICADOR for elemento in elementos):
        raise Rechazo(422, CLAVES_AJENAS)
    version = _version(cuerpo)
    if not isinstance(indicadores, list):
        raise Rechazo(422, FORMA_INESPERADA)
    for elemento in elementos:
        if (not isinstance(elemento, dict) or not isinstance(elemento.get("pi"), str) or "tipo" not in elemento
                or not all(isinstance(elemento.get(clave), (str, type(None))) for clave in ("tipo", "causa", "accion"))):
            raise Rechazo(422, FORMA_INESPERADA)
    pis = [elemento["pi"] for elemento in elementos]
    if len(set(pis)) != len(pis):
        raise Rechazo(422, PI_REPETIDO)
    return version, elementos


def _pedido_de_declaracion(cuerpo: Any) -> int:
    if not isinstance(cuerpo, dict):
        raise Rechazo(422, FORMA_INESPERADA)
    if set(cuerpo) - _CLAVES_DE_LA_DECLARACION:
        raise Rechazo(422, CLAVES_AJENAS)
    return _version(cuerpo)


# Lecturas comunes

def _filas(abierta: psycopg.Connection[Any], consulta: str, *parametros: object) -> list[dict[str, Any]]:
    with abierta.cursor(row_factory=dict_row) as cursor:
        return cursor.execute(consulta, parametros).fetchall()


def _seccion(abierta: psycopg.Connection[Any], carga_id: int) -> int | None:
    fila = abierta.execute(_SECCION_DE_LA_CARGA, (carga_id,)).fetchone()
    return int(fila[0]) if fila is not None else None


def _publicada(abierta: psycopg.Connection[Any], carga_id: int) -> None:
    """Rechazo 409 si la carga no está PUBLICADA, con reemplazada_por en una REEMPLAZADA (AD-27)."""
    [fila] = _filas(abierta, _ESTADO, carga_id)
    if fila["estado"] == "PUBLICADA":
        return
    extra = {"reemplazada_por": fila["reemplazada_por"]} if fila["reemplazada_por"] is not None else {}
    raise Rechazo(409, NO_PUBLICADA, **extra)


def _indicadores(abierta: psycopg.Connection[Any], carga_id: int) -> list[dict[str, Any]]:
    cuerpo = resultados.indicadores_de_la_carga(abierta, carga_id)
    return cuerpo["indicadores"] if cuerpo is not None else []


def _borrador(abierta: psycopg.Connection[Any], carga_id: int,
              indicadores: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    """Borrador de la carga con la forma de la ruta 14, o None si no tiene.

    En una carga PUBLICADA trae un elemento por cada PI que lleva registro, con el tipo que fija hoy el semáforo. En una
    que ya no lo está, que no tiene semáforo, trae solo los registros con texto y su tipo nulo.
    """
    [cabecera] = _filas(abierta, _CABECERA_DEL_BORRADOR, carga_id) or [None]
    if cabecera is None:
        return None
    textos = {fila["pi"]: fila for fila in _filas(abierta, _REGISTROS_DEL_BORRADOR, carga_id)}
    [estado] = _filas(abierta, _ESTADO, carga_id)
    if estado["estado"] == "PUBLICADA":
        indicadores = _indicadores(abierta, carga_id) if indicadores is None else indicadores
        elementos = [{"pi": i["pi"], "tipo": i["tipo_registro"],
                      "causa": textos.get(i["pi"], {}).get("causa"), "accion": textos.get(i["pi"], {}).get("accion")}
                     for i in indicadores if i["tipo_registro"] is not None]
    else:
        elementos = [{"pi": pi, "tipo": None, "causa": fila["causa"], "accion": fila["accion"]}
                     for pi, fila in textos.items() if fila["causa"] is not None or fila["accion"] is not None]
    return {"version": cabecera["version"], "actualizado_en": _hora(cabecera["actualizado_en"]),
            "indicadores": elementos}


def _declaracion(abierta: psycopg.Connection[Any], carga_id: int) -> tuple[dict[str, Any] | None, int | None]:
    """Declaración vigente con la forma de la ruta 14 y la versión del borrador que declaró, o (None, None)."""
    [vigente] = _filas(abierta, _VIGENTE, carga_id) or [None]
    if vigente is None:
        return None, None
    indicadores = [{**fila, "estado": "PROPUESTA"} for fila in
                   _filas(abierta, _REGISTROS_DECLARADOS, vigente["declaracion_id"])]
    return {"declarada_en": _hora(vigente["declarada_en"]), "indicadores": indicadores}, vigente["version_borrador"]


# Ruta 14

@router.get("/cargas/{carga_id}/mejora")
def leer_mejora(
    carga_id: int,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> Response:
    # Una sola instantánea de solo lectura para el alcance, la declaración, el borrador y el semáforo.
    with abierta.transaction():
        abierta.execute(SOLO_LECTURA)
        seccion = _seccion(abierta, carga_id)
        if seccion is None or not permisos.puede_leer(abierta, usuario.usuario_id, seccion):
            return error(403, permisos.SIN_ALCANCE)
        puede_editar = permisos.puede_declarar(abierta, usuario.usuario_id, seccion)
        declaracion, declarada = _declaracion(abierta, carga_id)
        [cabecera] = _filas(abierta, _CABECERA_DEL_BORRADOR, carga_id) or [None]
        # El coordinador nunca recibe el texto del borrador (BR-MEJORA-05).
        borrador = _borrador(abierta, carga_id) if puede_editar else None
    pendiente = cabecera is not None and (declarada is None or cabecera["version"] > declarada)
    return JSONResponse({"declaracion": declaracion, "borrador": borrador, "borrador_pendiente": pendiente,
                         "heredado_de": None, "puede_editar": puede_editar})


def _violacion(falla: psycopg.errors.CheckViolation) -> JSONResponse:
    """422 de un CHECK de V1_15, nunca un 500: el patrón de códigos o, en la declaración, el texto en blanco."""
    restriccion = falla.diag.constraint_name or ""
    if restriccion.endswith("_sin_codigos"):
        return error(422, CON_CODIGOS)
    if restriccion == "ck_mejora_declaracion_pi_texto":
        return error(422, INCOMPLETA)
    raise falla


# Rutas 15 y 16, con el alcance antes del cuerpo

def _puede_escribir(abierta: psycopg.Connection[Any], usuario_id: int, carga_id: int) -> bool:
    with abierta.transaction():
        seccion = _seccion(abierta, carga_id)
        return seccion is not None and permisos.puede_declarar(abierta, usuario_id, seccion)


@router.put("/cargas/{carga_id}/mejora/borrador", openapi_extra=_CUERPO_DEL_BORRADOR)
async def guardar_borrador(
    carga_id: int,
    request: Request,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> Response:
    if not await run_in_threadpool(_puede_escribir, abierta, usuario.usuario_id, carga_id):
        return error(403, permisos.SIN_ALCANCE)
    try:
        version, elementos = _pedido_de_borrador(await _cuerpo_json(request))
        return await run_in_threadpool(_guardar, abierta, usuario.usuario_id, carga_id, version, elementos)
    except Rechazo as rechazo:
        return rechazo.respuesta()


def _guardar(abierta: psycopg.Connection[Any], usuario_id: int, carga_id: int, version: int,
             elementos: list[dict[str, Any]]) -> Response:
    try:
        with abierta.transaction():
            abierta.execute(ESCRITURA)
            _publicada(abierta, carga_id)
            columnas = {fila["pi_codigo"]: fila["pi_id"] for fila in _filas(abierta, _COLUMNAS, carga_id)}
            indicadores = _indicadores(abierta, carga_id)
            tipos = {i["pi"]: i["tipo_registro"] for i in indicadores}
            for elemento in elementos:
                if elemento["pi"] not in columnas:
                    raise Rechazo(422, f"El indicador {elemento['pi']} no pertenece a esta carga.")
            for elemento in elementos:
                if tipos.get(elemento["pi"]) is None:
                    raise Rechazo(422, f"El indicador {elemento['pi']} no lleva registro porque su semáforo no "
                                       "tiene dato.")
            if any(elemento["tipo"] != tipos[elemento["pi"]] for elemento in elementos):
                raise Rechazo(422, TIPO_DEL_SEMAFORO)
            textos = [(columnas[e["pi"]], normalizar(e.get("causa")), normalizar(e.get("accion"))) for e in elementos]
            consulta, parametros = ((_PRIMER_BORRADOR, (carga_id, usuario_id)) if version == 0
                                    else (_SIGUIENTE_BORRADOR, (usuario_id, carga_id, version)))
            guardado = abierta.execute(consulta, parametros).fetchone()
            if guardado is None:
                raise Rechazo(409, OTRA_PESTANA, borrador=_borrador(abierta, carga_id, indicadores))
            for pi_id, causa, accion in textos:
                abierta.execute(_GUARDAR_REGISTRO, (carga_id, pi_id, causa, accion))
            abierta.execute(_VACIAR_LOS_DEMAS, (carga_id, [pi_id for pi_id, _, _ in textos]))
    except psycopg.errors.CheckViolation as falla:
        # La segunda defensa de la base (BR-MEJORA-10). El registro guarda solo el SQLSTATE y la restricción.
        registrar_falla("borrador_rechazado", falla)
        return _violacion(falla)
    return JSONResponse({"version": guardado[0], "actualizado_en": _hora(guardado[1])})


@router.post("/cargas/{carga_id}/mejora/declaracion", status_code=201, openapi_extra=_CUERPO_DE_LA_DECLARACION)
async def declarar(
    carga_id: int,
    request: Request,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> Response:
    if not await run_in_threadpool(_puede_escribir, abierta, usuario.usuario_id, carga_id):
        return error(403, permisos.SIN_ALCANCE)
    try:
        version = _pedido_de_declaracion(await _cuerpo_json(request))
        return await run_in_threadpool(_declarar, abierta, usuario.usuario_id, carga_id, version)
    except Rechazo as rechazo:
        return rechazo.respuesta()


def _declarar(abierta: psycopg.Connection[Any], usuario_id: int, carga_id: int, version: int) -> Response:
    try:
        with abierta.transaction():
            abierta.execute(ESCRITURA)
            _publicada(abierta, carga_id)
            indicadores = _indicadores(abierta, carga_id)
            calificados = [i for i in indicadores if i["calificados"] > 0]
            if any(i["semaforo"] == "SIN_DATO" for i in calificados):
                raise Rechazo(409, REGLA_SIN_DEFINIR)
            guardada = abierta.execute(_BORRADOR_PARA_DECLARAR, (carga_id,)).fetchone()
            if guardada is None:
                raise Rechazo(422, INCOMPLETA)
            if guardada[0] != version:
                raise Rechazo(409, BORRADOR_CAMBIO, borrador=_borrador(abierta, carga_id, indicadores))
            textos = {fila["pi"]: fila for fila in _filas(abierta, _REGISTROS_DEL_BORRADOR, carga_id)}
            registros = [(i, textos.get(i["pi"], {}).get("causa"), textos.get(i["pi"], {}).get("accion"))
                         for i in calificados]
            if any(_en_blanco(causa) or _en_blanco(accion) for _, causa, accion in registros):
                raise Rechazo(422, INCOMPLETA)
            for _, causa, accion in registros:
                normalizar(causa), normalizar(accion)
            texto_a, texto_b = r17.componer_recuadros([
                (i["pi"], i["tipo_registro"] if i["calificados"] > 0 else None,
                 textos.get(i["pi"], {}).get("causa") or "", textos.get(i["pi"], {}).get("accion") or "")
                for i in indicadores])
            if not (cabe_en_el_r17(texto_a) and cabe_en_el_r17(texto_b)):
                raise Rechazo(422, NO_CABE)
            declaracion_id, declarada_en = abierta.execute(_DECLARAR, (carga_id, version, usuario_id)).fetchone()
            columnas = {fila["pi_codigo"]: fila["pi_id"] for fila in _filas(abierta, _COLUMNAS, carga_id)}
            for indicador, causa, accion in registros:
                abierta.execute(_DECLARAR_PI, (declaracion_id, columnas[indicador["pi"]], carga_id,
                                               indicador["tipo_registro"], causa, accion,
                                               indicador["pct_sobre_calificados"], indicador["meta_pct"],
                                               indicador["semaforo"]))
    except psycopg.errors.CheckViolation as falla:
        registrar_falla("declaracion_rechazada", falla)
        return _violacion(falla)
    cuerpo = {"declarada_en": _hora(declarada_en),
              "indicadores": [{"pi": i["pi"], "tipo": i["tipo_registro"], "causa": causa, "accion": accion,
                               "estado": "PROPUESTA"} for i, causa, accion in registros]}
    return JSONResponse(cuerpo, status_code=201)
