"""Configuración, arranque y conexión de la API, que comparten app/main.py y las rutas.

Este módulo existe aparte de app/main.py para que app/sesion.py y app/rutas/ lean la conexión y
los ajustes sin importar la aplicación, que app/main.py crea al importarse. La descripción de cada
variable de entorno está en el docstring de app/main.py.
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

import psycopg
from fastapi import Request
from fastapi.responses import JSONResponse
from psycopg.conninfo import conninfo_to_dict

from abet_carga.carga import Configuracion, ConfiguracionInvalida

REGISTRO = logging.getLogger("abet.api")
PERIODO = re.compile(r"[0-9]{4}-[0-2]")
LARGO_MINIMO_DEL_SECRETO = 32
FORMA_INESPERADA = "La petición no tiene la forma esperada."
ERROR_INTERNO = "Ocurrió un error interno. Intente de nuevo."
_HOSTS_LOCALES = frozenset({"localhost", "127.0.0.1", "::1"})

_PERIODO_EXISTE = "SELECT 1 FROM abet.periodo WHERE codigo = %s"
_REGLAS_EXISTEN = "SELECT 1 FROM abet.conjunto_reglas WHERE version = %s"
_ROL = """
SELECT rolsuper OR rolcreaterole OR rolcreatedb OR rolbypassrls OR rolreplication
FROM pg_roles WHERE rolname = current_user
"""


class ConfiguracionDeLaApi(RuntimeError):
    """El despliegue no trae lo que la API necesita para arrancar."""


@dataclass(frozen=True)
class Ajustes:
    """Configuración de la API, que sale del entorno y nunca de la petición.

    La representación omite DATABASE_URL, que en Neon trae la contraseña del rol, y SESION_SECRETO,
    para que una traza o un registro no los repita.
    """

    database_url: str = field(repr=False)
    sesion_secreto: str = field(repr=False)
    periodo_vigente: str
    carga: Configuracion
    cookie_segura: bool = True

    @classmethod
    def desde_entorno(cls, entorno: Mapping[str, str] | None = None) -> Ajustes:
        """Lee la configuración de os.environ, o del entorno que llega, y se niega a seguir si falta algo."""
        entorno = os.environ if entorno is None else entorno
        valores = {}
        for variable in ("DATABASE_URL", "SESION_SECRETO", "PERIODO_VIGENTE"):
            valores[variable] = entorno.get(variable, "").strip()
            if not valores[variable]:
                raise ConfiguracionDeLaApi(f"Falta {variable}.")
        if len(valores["SESION_SECRETO"]) < LARGO_MINIMO_DEL_SECRETO:
            raise ConfiguracionDeLaApi(f"SESION_SECRETO necesita al menos {LARGO_MINIMO_DEL_SECRETO} caracteres.")
        if not PERIODO.fullmatch(valores["PERIODO_VIGENTE"]):
            raise ConfiguracionDeLaApi("PERIODO_VIGENTE no tiene la forma AAAA-C.")
        try:
            carga = Configuracion.desde_entorno(entorno)
        except ConfiguracionInvalida as error:
            raise ConfiguracionDeLaApi(str(error)) from None
        sin_secure = entorno.get("ABET_COOKIE_SIN_SECURE", "").strip() == "1"
        if sin_secure and (entorno.get("VERCEL") or not _base_local(valores["DATABASE_URL"])):
            raise ConfiguracionDeLaApi("ABET_COOKIE_SIN_SECURE solo se admite con una base local y fuera de Vercel.")
        return cls(
            database_url=valores["DATABASE_URL"],
            sesion_secreto=valores["SESION_SECRETO"],
            periodo_vigente=valores["PERIODO_VIGENTE"],
            carga=carga,
            cookie_segura=not sin_secure,
        )


def _base_local(database_url: str) -> bool:
    try:
        host = conninfo_to_dict(database_url).get("host") or ""
    except psycopg.ProgrammingError:
        return False
    hosts = [parte.strip() for parte in str(host).split(",")]
    return all(parte.startswith("/") or parte in _HOSTS_LOCALES for parte in hosts)


def conectar(ajustes: Ajustes) -> psycopg.Connection[Any]:
    """Conexión con confirmación automática y sin sentencias preparadas, que el agrupador de Neon no admite."""
    return psycopg.connect(ajustes.database_url, autocommit=True, prepare_threshold=None)


def comprobar_base(ajustes: Ajustes) -> None:
    """Comprueba el periodo, el conjunto de reglas y el rol de la conexión, o detiene el arranque."""
    try:
        conexion = conectar(ajustes)
    except psycopg.OperationalError:
        # El mensaje de libpq puede repetir el servidor o el usuario, así que no se repite.
        raise ConfiguracionDeLaApi("No se pudo conectar con la base de DATABASE_URL.") from None
    with conexion:
        administra = conexion.execute(_ROL).fetchone()
        if administra is None or administra[0]:
            raise ConfiguracionDeLaApi(
                "DATABASE_URL entra con un rol de administración, y la API necesita el rol de la aplicación.")
        if conexion.execute(_PERIODO_EXISTE, (ajustes.periodo_vigente,)).fetchone() is None:
            raise ConfiguracionDeLaApi(f"PERIODO_VIGENTE {ajustes.periodo_vigente} no existe en abet.periodo")
        if conexion.execute(_REGLAS_EXISTEN, (ajustes.carga.conjunto_reglas,)).fetchone() is None:
            raise ConfiguracionDeLaApi(f"CONJUNTO_REGLAS {ajustes.carga.conjunto_reglas} no existe para Ambiental")


def ajustes_de(request: Request) -> Ajustes:
    """Ajustes con que arrancó la aplicación."""
    return request.app.state.ajustes  # type: ignore[no-any-return]


def conexion(request: Request) -> Iterator[psycopg.Connection[Any]]:
    """Conexión de la petición, que se cierra al responder."""
    with conectar(ajustes_de(request)) as abierta:
        yield abierta


def error(codigo: int, mensaje: str) -> JSONResponse:
    """Respuesta de error del contrato, con un solo campo detail."""
    return JSONResponse({"detail": mensaje}, status_code=codigo)


def registrar_falla(evento: str, falla: BaseException) -> None:
    """Deja en el registro el tipo de la falla y, de PostgreSQL, solo el SQLSTATE y la restricción."""
    partes = [f"evento={evento}", f"tipo={type(falla).__name__}"]
    if isinstance(falla, psycopg.Error):
        partes += [f"sqlstate={falla.sqlstate}", f"restriccion={falla.diag.constraint_name}"]
    REGISTRO.error(" ".join(partes))
