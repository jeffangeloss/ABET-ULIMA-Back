"""Ayudas comunes de las pruebas de la interfaz HTTP (T036 a T038), sin pruebas propias.

La interfaz de programación de aplicaciones (application programming interface, API) corre en el
TestClient de FastAPI contra una copia propia de una base desechable del clúster de
tests/conftest.py, con las migraciones, el rol de la aplicación, los datos de 2026-2 y los de
varias_secciones_2026_2_inventado.sql. La API se conecta con el rol de la aplicación, como en
Neon, y la revisión de lo escrito usa la conexión del dueño de la base.

Cada contraseña de prueba y el secreto de la sesión se generan al azar en cada prueba y no se
escriben en ningún archivo. El cliente usa https://testserver, porque httpx no devuelve una cookie
Secure por http.
"""

from __future__ import annotations

import secrets
import warnings
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import psycopg
import pytest
from argon2 import PasswordHasher
from psycopg import sql
from starlette.exceptions import StarletteDeprecationWarning
from psycopg.conninfo import make_conninfo

from abet_carga.carga import Configuracion
from app.main import Ajustes, crear_app

# Starlette 1.8 avisa al importar su TestClient que prefiere httpx2. El proyecto prueba con httpx, que
# pyproject.toml ya trae, y no suma httpx2, así que el aviso se silencia solo en esta importación y
# -W error sigue en pie para todo lo demás.
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", "Using `httpx` with `starlette.testclient`", StarletteDeprecationWarning)
    from fastapi.testclient import TestClient

RAIZ = Path(__file__).resolve().parent.parent
INVENTADOS = RAIZ / "tests" / "datos_inventados"
VARIAS = RAIZ / "db" / "datos" / "varias_secciones_2026_2_inventado.sql"
DOCENTE_410 = "docente410@example.invalid"
DOCENTE_411 = "docente411@example.invalid"
VARIAS_CORREO = "docente.varias@example.invalid"
COORDINACION = "coordinacion@example.invalid"
PERIODO = "2026-2"
REGLAS = "R-2026-BORRADOR"
CORRECTO = "sintetico_20262_450002_410.xlsx"
CON_ERROR = "export_inventado_410_con_error.xlsx"
EXPORT_411 = "export_inventado_411.xlsx"
TABLAS = ("archivo_origen", "carga", "carga_columna", "carga_fila", "estudiante", "medicion", "rechazo_fila")
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@dataclass
class Api:
    """API de una prueba, con su base, la conexión del dueño y un cliente por usuario."""

    base: Any
    dueno: psycopg.Connection
    ajustes: Ajustes = field(repr=False)
    pila: ExitStack
    # Las contraseñas generadas quedan fuera de la representación que pytest imprime en una falla.
    claves: dict[str, str] = field(default_factory=dict, repr=False)

    def cliente(self, ajustes: Ajustes | None = None) -> TestClient:
        """Cliente nuevo, sin cookies, de la aplicación con estos ajustes o con los de la prueba."""
        aplicacion = crear_app(ajustes or self.ajustes)
        return self.pila.enter_context(TestClient(aplicacion, base_url="https://testserver"))

    def asignar(self, correo: str) -> str:
        """Asigna a correo una contraseña generada al azar y la devuelve, sin escribirla en ningún archivo."""
        clave = secrets.token_urlsafe(18)
        hash_clave = PasswordHasher().hash(clave)
        self.dueno.execute(
            "INSERT INTO acceso.credencial (usuario_id, hash_clave)"
            " SELECT usuario_id, %s FROM acceso.usuario_autorizado WHERE correo = %s"
            " ON CONFLICT (usuario_id) DO UPDATE SET hash_clave = EXCLUDED.hash_clave",
            (hash_clave, correo),
        )
        self.claves[correo] = clave
        return clave

    def sesion(self, correo: str) -> TestClient:
        """Cliente con la sesión de correo iniciada, con una contraseña asignada si no tiene una."""
        clave = self.claves.get(correo) or self.asignar(correo)
        cliente = self.cliente()
        respuesta = cliente.post("/api/sesion", json={"correo": correo, "contrasena": clave})
        assert respuesta.status_code == 200, respuesta.text
        return cliente

    def uno(self, consulta: str, *parametros: object) -> Any:
        fila = self.dueno.execute(consulta, parametros or None).fetchone()
        assert fila is not None
        return fila[0]

    def seccion(self, numero: str = "410", asignatura: str = "450002") -> int:
        return int(self.uno(
            "SELECT s.seccion_id FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
            " JOIN abet.periodo p USING (periodo_id) WHERE a.codigo = %s AND s.numero = %s AND p.codigo = %s",
            asignatura, numero, PERIODO,
        ))

    def conteos(self) -> dict[str, int]:
        return {tabla: int(self.uno(sql.SQL("SELECT count(*) FROM abet.{}").format(sql.Identifier(tabla))))
                for tabla in TABLAS}


def archivo(nombre: str) -> bytes:
    return (INVENTADOS / nombre).read_bytes()


def subir(cliente: TestClient, seccion_id: int, contenido: bytes, nombre: str, **opciones: Any) -> Any:
    """POST del export en el campo multipart «archivo»."""
    return cliente.post(f"/api/secciones/{seccion_id}/cargas", files={"archivo": (nombre, contenido, XLSX)},
                        **opciones)


def ajustes_de(base: Any, **cambios: Any) -> Ajustes:
    """Ajustes de la API contra la base, con el rol de la aplicación y un secreto nuevo."""
    ajustes = Ajustes(
        database_url=make_conninfo(base.conexion, user=base.rol_app),
        sesion_secreto=secrets.token_hex(32),
        periodo_vigente=PERIODO,
        carga=Configuracion(conjunto_reglas=REGLAS),
        cookie_segura=True,
    )
    return replace(ajustes, **cambios)


@pytest.fixture(scope="module")
def plantilla(base_desechable: Any) -> Iterator[Any]:
    """Base con las migraciones, el rol de la aplicación y los datos de 2026-2, que cada prueba copia."""
    with base_desechable.abierta(despues=(VARIAS,)) as base:
        yield base


@pytest.fixture
def base(base_desechable: Any, plantilla: Any) -> Iterator[Any]:
    """Copia propia de la plantilla, con el mismo rol de la aplicación, que se borra al terminar."""
    nombre = f"{plantilla.nombre}_{secrets.token_hex(3)}"
    with psycopg.connect(make_conninfo(plantilla.conexion, dbname="postgres"), autocommit=True) as servidor:
        servidor.execute(sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(sql.Identifier(nombre),
                                                                          sql.Identifier(plantilla.nombre)))
    copia = base_desechable.BaseDesechable(nombre, make_conninfo(plantilla.conexion, dbname=nombre), None, None)
    try:
        yield replace(copia, rol_app=plantilla.rol_app)
    finally:
        base_desechable.borrar(copia)


@pytest.fixture
def api(base: Any) -> Iterator[Api]:
    with ExitStack() as pila, psycopg.connect(base.conexion, autocommit=True) as dueno:
        yield Api(base=base, dueno=dueno, ajustes=ajustes_de(base), pila=pila)


@pytest.fixture
def con_sesion(api: Api) -> Callable[[str], TestClient]:
    return api.sesion
