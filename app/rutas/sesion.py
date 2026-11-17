"""POST, GET y DELETE /api/sesion (T036, BR-ACCESO-03 a BR-ACCESO-06).

POST valida el correo y la contraseña con app/sesion.py y fija la cookie abet_sesion. Un fallo
responde 401 con «Correo o contraseña incorrectos.» sin la cabecera Set-Cookie, y el sexto intento
de una serie de fallos responde 429. GET devuelve el correo y el rol de la sesión vigente, o 401.
DELETE vence la sesión y devuelve la cookie con Max-Age 0, y responde 204 también sin sesión
(propuesta). El cuerpo IngresoEntrada limita el correo a 254 caracteres, el ancho de la columna, y
la contraseña a 1024, para que un cuerpo enorme no cueste un hash Argon2id (propuesta).
"""

from __future__ import annotations

from typing import Any

import psycopg
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app import sesion
from app.configuracion import ajustes_de, conexion, error

router = APIRouter()


class IngresoEntrada(BaseModel):
    """Cuerpo de POST /api/sesion (propuesta)."""

    correo: str = Field(max_length=254)
    contrasena: str = Field(max_length=1024)


class UsuarioSalida(BaseModel):
    """Correo y rol del usuario de la sesión."""

    correo: str
    rol: str


@router.post("/sesion", response_model=UsuarioSalida)
def iniciar(entrada: IngresoEntrada, request: Request, abierta: psycopg.Connection[Any] = Depends(conexion)) -> Response:
    try:
        usuario, token = sesion.ingresar(abierta, entrada.correo, entrada.contrasena, ajustes_de(request).sesion_secreto)
    except sesion.DemasiadosIntentos:
        return error(429, sesion.DEMASIADOS)
    except sesion.IngresoFallido:
        return error(401, sesion.INCORRECTOS)
    respuesta = JSONResponse({"correo": usuario.correo, "rol": usuario.rol})
    respuesta.headers["Cache-Control"] = "no-store"
    sesion.fijar_cookie(request, respuesta, token)
    return respuesta


@router.get("/sesion", response_model=UsuarioSalida)
def actual(usuario: sesion.Usuario = Depends(sesion.usuario_actual)) -> UsuarioSalida:
    return UsuarioSalida(correo=usuario.correo, rol=usuario.rol)


@router.delete("/sesion", status_code=204, response_class=Response)
def cerrar(request: Request, abierta: psycopg.Connection[Any] = Depends(conexion)) -> Response:
    sesion.cerrar(abierta, request.cookies.get(sesion.COOKIE))
    respuesta = Response(status_code=204)
    sesion.fijar_cookie(request, respuesta, "", vigencia=0)
    return respuesta
