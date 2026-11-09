"""Subida del export, constancia y R-17 (T038, BR-CARGA-01 a BR-CARGA-17, BR-R17-01 a BR-R17-10).

POST /api/secciones/{seccion_id}/cargas sigue el orden fijo de BR-CARGA-03.
1. La sesión y el alcance, con app/permisos.puede_subir(). En el corte 1 solo sube el profesor
   asignado, así que el coordinador recibe el mismo 403 que un profesor ajeno (BR-ACCESO-08).
2. Recién entonces lee el cuerpo multipart. Sin el campo archivo responde 422 con «La petición no
   tiene la forma esperada.». Los demás campos y los parámetros de consulta no se leen, así que
   ninguno apaga la guardia (BR-CARGA-07).
3. abet_carga.carga.cargar() comprueba el plan de la sección, calcula la huella SHA-256 (Secure
   Hash Algorithm de 256 bits) de todo el contenido recibido antes del tope de 1 MB, revisa el
   archivo, aplica la guardia de datos inventados antes de buscar la huella en la base o de escribir
   nada, y escribe la carga en una sola transacción. La ruta responde el código HTTP que el
   resultado trae, con la constancia de abet_carga.constancia si la carga existe o con su mensaje
   en detail si no.

El registro de la aplicación (logger abet.api) guarda de un archivo detenido por tamaño o por ser
ilegible la huella, la hora, el motivo y el detalle de la lista cerrada de la spec 003, con «-» si
no tiene, en la forma evento=archivo_detenido hora=… sha256=… motivo=… detalle=…, de uno detenido
por la guardia solo la huella y la hora, y
de una falla de la base solo el SQLSTATE y el nombre de la restricción (BR-CARGA-08). Nunca guarda
el nombre del archivo, de la hoja, un código, un valor leído, el DETAIL de PostgreSQL ni la cookie.

GET /api/cargas/{carga_id} responde la constancia, con el mensaje de cada rechazo y de cada aviso, y
GET /api/cargas/{carga_id}/r17.xlsx el libro del R-17 de una carga PUBLICADA, con las cabeceras del
contrato. Las dos leen con app/permisos.puede_leer(), así que el coordinador alcanza cualquier
sección. Una sección o una carga que no existe responde el mismo 403 que una ajena, porque un 404
distinto revelaría qué identificadores existen (sección 9 del contrato, propuesta).
"""

from __future__ import annotations

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
from app.configuracion import FORMA_INESPERADA, REGISTRO, ajustes_de, conexion, error

router = APIRouter()
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_SECCION_DE_LA_CARGA = "SELECT seccion_id FROM abet.carga WHERE carga_id = %s"
_MULTIPART = {
    "requestBody": {
        "required": True,
        "content": {"multipart/form-data": {"schema": {
            "type": "object", "required": ["archivo"],
            "properties": {"archivo": {"type": "string", "format": "binary"}},
        }}},
    }
}


def _ajena() -> JSONResponse:
    return error(403, permisos.SIN_ALCANCE)


@router.post("/secciones/{seccion_id}/cargas", openapi_extra=_MULTIPART)
async def subir(
    seccion_id: int,
    request: Request,
    usuario: sesion.Usuario = Depends(sesion.usuario_actual),
    abierta: psycopg.Connection[Any] = Depends(conexion),
) -> Response:
    if not await run_in_threadpool(permisos.puede_subir, abierta, usuario.usuario_id, seccion_id):
        return _ajena()
    try:
        async with request.form() as formulario:
            archivo = formulario.get("archivo")
            if not isinstance(archivo, UploadFile):
                return error(422, FORMA_INESPERADA)
            contenido = await archivo.read()
            nombre = archivo.filename or ""
    except Exception:  # noqa: BLE001 - un multipart mal formado es un cuerpo con otra forma
        return error(422, FORMA_INESPERADA)
    return await run_in_threadpool(_cargar, abierta, request, contenido, nombre, seccion_id, usuario.usuario_id)


def _cargar(abierta: psycopg.Connection[Any], request: Request, contenido: bytes, nombre: str, seccion_id: int,
            usuario_id: int) -> Response:
    resultado = cargar(abierta, contenido, nombre_archivo=nombre, seccion_id=seccion_id, usuario_id=usuario_id,
                       configuracion=ajustes_de(request).carga)
    _registrar(resultado)
    if resultado.carga_id is None:
        return error(resultado.codigo_http, resultado.mensaje or FORMA_INESPERADA)
    return JSONResponse(constancia.armar(abierta, resultado.carga_id), status_code=resultado.codigo_http)


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
