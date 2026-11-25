"""Subida del export, constancia y R-17 (T038, BR-CARGA-01 a BR-CARGA-17, BR-R17-01 a BR-R17-10).

POST /api/secciones/{seccion_id}/cargas sigue el orden fijo de BR-CARGA-03.
1. La sesión y el alcance, con app/permisos.puede_subir() o, si la petición trae el parámetro
   reemplaza, con app/permisos.puede_reemplazar() (corte 2, BR-CARGA-19). Solo sube una carga nueva el
   profesor asignado, así que el coordinador recibe el mismo 403 que un profesor ajeno, y reemplaza
   la carga publicada en cualquier sección de la carrera (BR-ACCESO-08 y D-11).
2. La forma de reemplaza, un solo entero positivo, y recién entonces el cuerpo multipart. Sin el campo
   archivo, o con un reemplaza mal formado, responde 422 con «La petición no tiene la forma
   esperada.». El campo confirmar_seccion solo admite un único «true», y otro valor responde 422 con
   «La sección confirmada no es la sección elegida. No se guardó nada.» (BR-CARGA-18). Los demás
   campos y parámetros no se leen, así que ninguno apaga la guardia (BR-CARGA-07).
3. abet_carga.carga.cargar() comprueba el plan de la sección, calcula la huella SHA-256 (Secure
   Hash Algorithm de 256 bits) de todo el contenido recibido antes del tope de 1 MB, revisa el
   archivo, aplica la guardia de datos inventados antes de buscar la huella en la base o de escribir
   nada, y escribe la carga en una sola transacción. La ruta responde el código HTTP que el
   resultado trae, con la constancia de abet_carga.constancia si la carga existe o con su mensaje
   en detail si no. Dos errores del corte 2 suman un campo para la pantalla (contrato, sección 3.1),
   requiere_confirmacion en el 422 de la sección sin declarar y carga_publicada en el 409 de la
   sección con otra carga publicada, y el 200 del mismo archivo en un reemplazo suma aviso.

El registro de la aplicación (logger abet.api) guarda de un archivo detenido por tamaño o por ser
ilegible la huella, la hora, el motivo y el detalle de la lista cerrada de la spec 003, con «-» si
no tiene, en la forma evento=archivo_detenido hora=… sha256=… motivo=… detalle=…, de uno detenido
por la guardia solo la huella y la hora, y
de una falla de la base solo el SQLSTATE y el nombre de la restricción (BR-CARGA-08). Nunca guarda
el nombre del archivo, de la hoja, un código, un valor leído, el DETAIL de PostgreSQL ni la cookie.

GET /api/cargas?seccion_id= (corte 2, BR-CARGA-20) responde la lista resumida de las cargas al
alcance del usuario, de la más reciente a la más antigua. Sin seccion_id lista las de las secciones que
app/permisos.secciones_visibles() da en el periodo del parámetro aditivo periodo o, sin él, en PERIODO_VIGENTE
(cambio fechado de BR-CARGA-20, spec 008, T033). Un periodo con otra forma que AAAA-C responde el 422 de la ruta 4,
y uno bien formado sin secciones del usuario, una lista vacía. Con seccion_id el periodo no se usa, porque la
sección ya lo fija. Con seccion_id, las de esa sección si
app/permisos.puede_leer() la alcanza, o el 403 único si no, también para un entero que no es el de
ninguna sección, como 0. Un seccion_id que no es un entero responde 422 con el texto de la forma
inesperada.

GET /api/cargas/{carga_id} responde la constancia, con el mensaje de cada rechazo y de cada aviso, y
GET /api/cargas/{carga_id}/r17.xlsx el libro del R-17 de una carga PUBLICADA, con las cabeceras del
contrato. Las dos leen con app/permisos.puede_leer(), así que el coordinador alcanza cualquier
sección. Una sección o una carga que no existe responde el mismo 403 que una ajena, porque un 404
distinto revelaría qué identificadores existen (sección 9 del contrato, propuesta). La ruta del R-17 responde
con el código y el mensaje de cada abet_carga.r17.R17NoDisponible: 409 para una carga que no está PUBLICADA, que
manda, 409 «Complete la causa y la acción de cada indicador en la página de la carga antes de descargar el R-17.»
para una carga PUBLICADA sin su declaración vigente completa, también para el coordinador (DeclaracionPendiente,
BR-R17-12, sección 13.6 del contrato), y 422 para una sección que no cabe en la plantilla. r17.generar() lee la
constancia, las cifras y la declaración en una sola transacción READ ONLY y REPEATABLE READ.

GET /api/cargas/{carga_id}/indicadores (ruta 13 de la spec 005, T031, BR-MEJORA-01 a BR-MEJORA-05) responde las
cifras de cada PI de una carga PUBLICADA con su semáforo, su hallazgo y su tipo de registro, armadas por
app/rutas/resultados.indicadores_de_la_carga() con las funciones puras de abet_carga/resultados.py. Lee el alcance,
el estado, CORTE_ROJO de abet.parametro_valor y la vista en una sola transacción READ ONLY con REPEATABLE READ, y
responde en el orden 401, 403 (el único, también para una carga que no existe) y 409 para una carga RECHAZADA o
REEMPLAZADA. No tiene cuerpo ni parámetros de consulta, así que no responde 422 por la forma.
"""

from __future__ import annotations

import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile

from abet_carga import constancia, r17
from abet_carga.carga import Resultado, ResultadoCarga, cargar
from abet_carga.constancia import HORA_DE_LIMA
from app import permisos, sesion
from app.rutas import resultados
from app.configuracion import FORMA_INESPERADA, PERIODO, PERIODO_MAL_FORMADO, REGISTRO, ajustes_de, conexion, error

# BR-ACCESO-10. El router exige la sesión, así que ninguna ruta suya responde sin ella aunque la olvide.
router = APIRouter(dependencies=[Depends(sesion.usuario_actual)])
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
CONFIRMACION_INVALIDA = "La sección confirmada no es la sección elegida. No se guardó nada."
# reemplaza es un carga_id, un entero positivo sin signo, ceros a la izquierda ni decimales. seccion_id de la lista
# admite cualquier entero, como el seccion_id de la ruta de subida, y uno que no existe recibe el 403 único.
_ENTERO_POSITIVO = re.compile(r"[1-9][0-9]{0,17}")
_ENTERO = re.compile(r"[+-]?[0-9]{1,18}")
SIN_SEMAFORO = "La carga no está publicada y no tiene semáforo."
_SECCION_DE_LA_CARGA = "SELECT seccion_id FROM abet.carga WHERE carga_id = %s"
# reemplaza y seccion_id se declaran solo en el esquema OpenAPI. Las rutas los leen después de comprobar el alcance,
# como pide el orden de BR-CARGA-03, y no con la conversión de FastAPI, que respondería su 422 antes que el 403.
_REEMPLAZA = {"name": "reemplaza", "in": "query", "required": False,
              "schema": {"type": "integer", "minimum": 1}, "description": "Carga PUBLICADA que la nueva reemplaza."}
_SECCION_ID = {"name": "seccion_id", "in": "query", "required": False, "schema": {"type": "integer"}}
_PERIODO = {"name": "periodo", "in": "query", "required": False, "schema": {"type": "string", "pattern": "^[0-9]{4}-[0-2]$"},
            "description": "Periodo de la lista sin seccion_id. Sin él, PERIODO_VIGENTE."}
_MULTIPART = {
    "parameters": [_REEMPLAZA],
    "requestBody": {
        "required": True,
        "content": {"multipart/form-data": {"schema": {
            "type": "object", "required": ["archivo"],
            "properties": {"archivo": {"type": "string", "format": "binary"},
                           "confirmar_seccion": {"type": "string", "enum": ["true"]}},
        }}},
    }
}


def _ajena() -> JSONResponse:
    return error(403, permisos.SIN_ALCANCE)


def _entero(valores: list[str], forma: re.Pattern[str] = _ENTERO_POSITIVO) -> int | None:
    """El único valor de un parámetro como entero de esa forma, o None si falta, se repite o tiene otra forma."""
    if len(valores) != 1 or not forma.fullmatch(valores[0]):
        return None
    return int(valores[0])


@router.post("/secciones/{seccion_id}/cargas", openapi_extra=_MULTIPART)
async def subir(
    seccion_id: int,
    request: Request,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> Response:
    pide_reemplazo = "reemplaza" in request.query_params
    alcance = permisos.puede_reemplazar if pide_reemplazo else permisos.puede_subir
    if not await run_in_threadpool(alcance, abierta, usuario.usuario_id, seccion_id):
        return _ajena()
    reemplazada = _entero(request.query_params.getlist("reemplaza")) if pide_reemplazo else None
    if pide_reemplazo and reemplazada is None:
        return error(422, FORMA_INESPERADA)
    try:
        async with request.form() as formulario:
            archivo = formulario.get("archivo")
            if not isinstance(archivo, UploadFile):
                return error(422, FORMA_INESPERADA)
            confirmaciones = formulario.getlist("confirmar_seccion")
            if confirmaciones and confirmaciones != ["true"]:
                return error(422, CONFIRMACION_INVALIDA)
            contenido = await archivo.read()
            nombre = archivo.filename or ""
    except Exception:  # noqa: BLE001 - un multipart mal formado es un cuerpo con otra forma
        return error(422, FORMA_INESPERADA)
    pedido = _Pedido(seccion_id, usuario.usuario_id, reemplazada, confirmar_seccion=bool(confirmaciones))
    return await run_in_threadpool(_cargar, abierta, request, contenido, nombre, pedido)


class _Pedido:
    """Sección, usuario y lo que pide la subida en el corte 2, ya revisados por la ruta."""

    def __init__(self, seccion_id: int, usuario_id: int, reemplaza: int | None, *, confirmar_seccion: bool) -> None:
        self.seccion_id, self.usuario_id = seccion_id, usuario_id
        self.reemplaza, self.confirmar_seccion = reemplaza, confirmar_seccion


def _cargar(abierta: psycopg.Connection[Any], request: Request, contenido: bytes, nombre: str,
            pedido: _Pedido) -> Response:
    resultado = cargar(abierta, contenido, nombre_archivo=nombre, seccion_id=pedido.seccion_id,
                       usuario_id=pedido.usuario_id, configuracion=ajustes_de(request).carga,
                       reemplaza=pedido.reemplaza, confirmar_seccion=pedido.confirmar_seccion)
    _registrar(resultado)
    if resultado.carga_id is None:
        cuerpo: dict[str, Any] = {"detail": resultado.mensaje or FORMA_INESPERADA}
        if resultado.requiere_confirmacion:
            cuerpo["requiere_confirmacion"] = True
        if resultado.carga_publicada is not None:
            cuerpo["carga_publicada"] = resultado.carga_publicada
        return JSONResponse(cuerpo, status_code=resultado.codigo_http)
    cuerpo = constancia.armar(abierta, resultado.carga_id)
    if resultado.aviso is not None:
        cuerpo["aviso"] = resultado.aviso
    return JSONResponse(cuerpo, status_code=resultado.codigo_http)


def _registrar(resultado: ResultadoCarga) -> None:
    """Registro de BR-CARGA-08, sin nombres, códigos, valores leídos ni el DETAIL de PostgreSQL."""
    hora = datetime.now(HORA_DE_LIMA).isoformat()
    if resultado.resultado is Resultado.ILEGIBLE:
        REGISTRO.warning(f"evento=archivo_detenido hora={hora} sha256={resultado.sha256} motivo={resultado.motivo}"
                         f" detalle={resultado.detalle or '-'}")
    elif resultado.resultado is Resultado.GUARDIA:
        REGISTRO.warning(f"evento=guardia_datos_inventados hora={hora} sha256={resultado.sha256}")
    elif resultado.resultado is Resultado.FALLA:
        REGISTRO.error(f"evento=carga_fallida hora={hora} sqlstate={resultado.sqlstate}"
                       f" restriccion={resultado.restriccion}")


def _seccion_legible(abierta: psycopg.Connection[Any], usuario: sesion.Usuario, carga_id: int) -> bool:
    fila = abierta.execute(_SECCION_DE_LA_CARGA, (carga_id,)).fetchone()
    return fila is not None and permisos.puede_leer(abierta, usuario.usuario_id, int(fila[0]))


@router.get("/cargas", openapi_extra={"parameters": [_SECCION_ID, _PERIODO]})
def listar_cargas(
    request: Request,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> Response:
    if "seccion_id" in request.query_params:
        pedida = _entero(request.query_params.getlist("seccion_id"), _ENTERO)
        if pedida is None:
            return error(422, FORMA_INESPERADA)
        if not permisos.puede_leer(abierta, usuario.usuario_id, pedida):
            return _ajena()
        secciones = [pedida]
    else:
        pedidos = request.query_params.getlist("periodo")
        if len(pedidos) > 1 or (pedidos and not PERIODO.fullmatch(pedidos[0])):
            return error(422, PERIODO_MAL_FORMADO)
        periodo = pedidos[0] if pedidos else ajustes_de(request).periodo_vigente
        visibles = permisos.secciones_visibles(abierta, usuario.usuario_id, periodo)
        secciones = [visible.seccion_id for visible in visibles]
    return JSONResponse(constancia.resumenes(abierta, secciones))


@router.get("/cargas/{carga_id}")
def leer_constancia(
    carga_id: int,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> Response:
    if not _seccion_legible(abierta, usuario, carga_id):
        return _ajena()
    return JSONResponse(constancia.armar(abierta, carga_id))


@router.get("/cargas/{carga_id}/r17.xlsx", response_class=Response,
            responses={200: {"content": {XLSX: {}}}})
def descargar_r17(
    carga_id: int,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> Response:
    if not _seccion_legible(abierta, usuario, carga_id):
        return _ajena()
    with tempfile.TemporaryDirectory(prefix="abet_r17_") as carpeta:
        try:
            ruta = r17.generar(abierta, carga_id, Path(carpeta))
        except r17.R17NoDisponible as motivo:
            return error(motivo.codigo_http, motivo.mensaje)
        contenido = ruta.read_bytes()
    cabeceras = {
        "Content-Disposition": f'attachment; filename="{ruta.name}"',
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    }
    return Response(contenido, media_type=XLSX, headers=cabeceras)


@router.get("/cargas/{carga_id}/indicadores")
def leer_indicadores(
    carga_id: int,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> Response:
    # Una sola transacción READ ONLY con REPEATABLE READ, que fija la instantánea desde la primera consulta, así que el
    # alcance, el estado de la carga, el corte rojo y las cifras salen de la misma foto (BR-MEJORA-01). El 403 va antes
    # que el 409, y una carga que no existe recibe el mismo 403 que una ajena (BR-MEJORA-05 y BR-ACCESO-08).
    with abierta.transaction():
        abierta.execute(resultados.SOLO_LECTURA)
        if not _seccion_legible(abierta, usuario, carga_id):
            return _ajena()
        cuerpo = resultados.indicadores_de_la_carga(abierta, carga_id)
    if cuerpo is None:
        return error(409, SIN_SEMAFORO)
    return JSONResponse(cuerpo)
