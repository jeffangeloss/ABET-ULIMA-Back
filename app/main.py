"""Aplicación FastAPI de ABET-ULIMA-Back, con prefijo /api (T036 a T038).

La interfaz de programación de aplicaciones (application programming interface, API) traduce a
abet_carga y a app/permisos.py las peticiones del protocolo de transferencia de hipertexto
(Hypertext Transfer Protocol, HTTP) que describe docs/03-api/contrato.md del Front. Este módulo
reúne la configuración, el arranque, la conexión con la base y los manejadores de errores.

Configuración, siempre del despliegue y nunca de la petición.
- DATABASE_URL, la cadena de conexión con el rol de la aplicación (abet_app en Neon, por el
  agrupador de conexiones). La API nunca la imprime, porque en Neon trae la contraseña.
- SESION_SECRETO, de al menos 32 caracteres, del que sale la clave del código de autenticación de
  mensajes basado en hash (hash-based message authentication code, HMAC) de los intentos fallidos.
- PERIODO_VIGENTE y CONJUNTO_REGLAS, que la base no marca como vigentes (BR-PERIODO-01 y 02).
- GUARDIA_DATOS_INVENTADOS, encendida salvo con el valor 0, así que una variable que falta no la
  apaga (BR-CARGA-07).
- ABET_COOKIE_SIN_SECURE=1 deja la cookie sin el atributo Secure para el servidor local por http
  de scripts/api_local.sh. Solo se admite con una base local, por socket de Unix, localhost o
  127.0.0.1, y fuera de Vercel, que define VERCEL en sus funciones (propuesta).

Al arrancar, la API comprueba que el periodo y el conjunto de reglas existen y que DATABASE_URL no
entra con un rol de administración (superusuario, creación de roles o de bases, o sin seguridad por
filas), porque la aplicación trabaja solo con el privilegio mínimo del rol de
db/plataforma/neon/crear_rol_app.sql (propuesta). Si algo falla, se detiene con su mensaje.

Cada petición abre su propia conexión en modo de confirmación automática y sin sentencias
preparadas, porque el agrupador de Neon no las admite, y la cierra al responder.

Todo error responde {"detail": "mensaje"} en español, sin trazas. El 422 de un cuerpo mal formado
dice «La petición no tiene la forma esperada.», y un error no previsto responde 500 con «Ocurrió un
error interno. Intente de nuevo.» (propuesta). El registro de la aplicación guarda de ese error
solo su tipo y, si viene de PostgreSQL, el SQLSTATE y el nombre de la restricción, nunca el
mensaje ni el DETAIL, que repiten los valores de la fila (BR-CARGA-08).

Toda respuesta de /api, de éxito o de error, lleva Cache-Control: no-store, para que ni una caché
intermedia ni el historial de un equipo compartido retengan datos de una sesión (propuesta).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.configuracion import (
    ERROR_INTERNO,
    FORMA_INESPERADA,
    Ajustes,
    ConfiguracionDeLaApi,
    comprobar_base,
    error,
    registrar_falla,
)
from app.rutas import cargas, secciones, sesion

__all__ = ["Ajustes", "ConfiguracionDeLaApi", "app", "crear_app"]
_GENERICOS = {404: "La ruta no existe.", 405: "El método no se admite en esta ruta."}


async def _http(_: Request, excepcion: Exception) -> Response:
    assert isinstance(excepcion, StarletteHTTPException)
    detalle = excepcion.detail
    if not isinstance(detalle, str) or detalle == HTTPStatus(excepcion.status_code).phrase:
        detalle = _GENERICOS.get(excepcion.status_code, FORMA_INESPERADA)
    return JSONResponse({"detail": detalle}, status_code=excepcion.status_code, headers=excepcion.headers)


async def _validacion(_: Request, __: Exception) -> Response:
    return error(422, FORMA_INESPERADA)


async def _sin_trazas(request: Request, siguiente: Callable[[Request], Awaitable[Response]]) -> Response:
    try:
        respuesta = await siguiente(request)
    except Exception as falla:  # noqa: BLE001 - toda falla no prevista responde el mismo 500 sin trazas
        registrar_falla("error_interno", falla)
        respuesta = error(500, ERROR_INTERNO)
    # (propuesta) Ninguna respuesta de /api queda en una caché ni en el historial de un equipo compartido.
    if request.url.path.startswith("/api/"):
        respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


def crear_app(ajustes: Ajustes | None = None) -> FastAPI:
    """Aplicación con sus rutas. Los ajustes salen del entorno al arrancar si no llegan."""
    @asynccontextmanager
    async def ciclo(aplicacion: FastAPI) -> AsyncIterator[None]:
        vigentes = ajustes if ajustes is not None else Ajustes.desde_entorno()
        comprobar_base(vigentes)
        aplicacion.state.ajustes = vigentes
        yield

    aplicacion = FastAPI(title="ABET-ULIMA-Back", lifespan=ciclo, openapi_url="/api/openapi.json",
                         docs_url=None, redoc_url=None)
    aplicacion.add_exception_handler(StarletteHTTPException, _http)
    aplicacion.add_exception_handler(RequestValidationError, _validacion)
    aplicacion.middleware("http")(_sin_trazas)
    for modulo in (sesion, secciones, cargas):
        aplicacion.include_router(modulo.router, prefix="/api")
    return aplicacion


app = crear_app()
