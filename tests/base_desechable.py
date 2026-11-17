"""Bases PostgreSQL 18 desechables para las pruebas que escriben en la base (T033 a T035, T050 y T052).

crear() arma una base abet_demo_<sufijo> como db/pruebas/correr_pruebas.sh arma las suyas. Crea la
base desde template0 con la codificación UTF8 y los esquemas abet y acceso, aplica cada migración
versionada en su transacción y en orden de versión, desde V1_01 hasta la última, y después las
repetibles R__ en orden alfabético. Luego corre, en el orden de T027,
db/plataforma/neon/crear_rol_app.sql con el rol abet_demo_app_<sufijo>,
db/plataforma/neon/guardia_datos_inventados.sql solo si se pide, db/datos/periodo_2026_2_inventado.sql
y, al final, los scripts de despues. Las rutas salen de la raíz del repositorio y no de la carpeta
desde la que corre pytest.

La conexión sale de las variables de libpq (PGHOST, PGPORT y PGUSER) que deja la fixture
cluster_postgres de tests/conftest.py. Fuera de la integración continua (continuous integration, CI)
apuntan al clúster desechable de tests/cluster_desechable.py, y en ella, al servicio postgres:18 del
job. Sin esas variables,
_entorno() se niega a seguir, así que ninguna base se crea ni se borra en el clúster de la Mac. El rol de la
aplicación nunca recibe contraseña, porque crear_rol_app.sql corre sin APP_DB_CLAVE, y ninguna cadena
de conexión de BaseDesechable lleva contraseña.

borrar() quita la base con DROP DATABASE ... WITH (FORCE), que cierra las conexiones que queden, y
después el rol, y se niega a tocar un nombre sin el prefijo abet_demo_, así que nunca alcanza a
abet_sis_med_dev ni a las bases abet_prueba_ de correr_pruebas.sh. abierta() borra todo al salir,
también si la prueba falla, y crear() borra lo que alcanzó a crear si un paso falla, sin tocar una
base o un rol que ya existían con ese nombre. Las fixtures base_demo y crear_base_demo de
tests/conftest.py usan abierta(). exigir_sin_restos() falla si queda alguna base o algún rol
abet_demo_, y la fixture base_desechable la llama al cerrar la sesión de pruebas.
"""

from __future__ import annotations

import importlib.util
import os
import re
import secrets
import subprocess
import sys
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from psycopg.conninfo import make_conninfo

PREFIJO = "abet_demo_"
RAIZ = Path(__file__).resolve().parent.parent
MIGRACIONES = RAIZ / "db" / "migration"
ROL_APP = RAIZ / "db" / "plataforma" / "neon" / "crear_rol_app.sql"
GUARDIA = RAIZ / "db" / "plataforma" / "neon" / "guardia_datos_inventados.sql"
DATOS_2026_2 = RAIZ / "db" / "datos" / "periodo_2026_2_inventado.sql"

# Hasta 40 caracteres, así que abet_demo_app_<sufijo> queda por debajo de los 63 de un identificador.
_SUFIJO = re.compile(r"[a-z0-9_]{1,40}")
_DESECHABLE = re.compile(PREFIJO + r"[a-z0-9_]{1,44}")


class ErrorDeBase(RuntimeError):
    """Paso de psql que falla al crear o al borrar una base desechable, con lo que psql informa."""


@dataclass(frozen=True)
class BaseDesechable:
    """Base desechable con la cadena de conexión de su dueño y, si existe, la del rol de la aplicación."""

    nombre: str
    conexion: str
    rol_app: str | None
    conexion_app: str | None


def migraciones() -> list[Path]:
    """Migraciones versionadas en orden de versión y repetibles en orden alfabético, como correr_pruebas.sh."""
    versionadas = sorted(MIGRACIONES.glob("V*__*.sql"), key=_version)
    repetibles = sorted(MIGRACIONES.glob("R__*.sql"), key=lambda ruta: ruta.name.encode())
    return [*versionadas, *repetibles]


def crear(
    sufijo: str | None = None,
    *,
    guardia: bool = False,
    rol_app: bool = True,
    datos_2026_2: bool = True,
    despues: Sequence[Path] = (),
) -> BaseDesechable:
    """Crea la base abet_demo_<sufijo> con sus migraciones y sus scripts, o no deja nada si un paso falla."""
    sufijo = _sufijo_nuevo() if sufijo is None else sufijo
    if not _SUFIJO.fullmatch(sufijo):
        raise ValueError(
            "El sufijo de una base desechable lleva solo minúsculas, cifras y «_», hasta 40 caracteres."
        )
    nombre = PREFIJO + sufijo
    rol = f"{PREFIJO}app_{sufijo}" if rol_app else None
    creada = rol_propio = False
    try:
        _psql("postgres", "-c", f"CREATE DATABASE {nombre} TEMPLATE template0 ENCODING 'UTF8'")
        creada = True
        _psql(nombre, "-c", "CREATE SCHEMA abet", "-c", "CREATE SCHEMA acceso")
        for migracion in migraciones():
            _psql(nombre, "-1", "-f", str(migracion), opciones="-c client_min_messages=warning")
        if rol is not None:
            if rol in restos()[1]:
                raise ErrorDeBase(f"El rol {rol} ya existe y no es de esta base.")
            rol_propio = True
            _psql(nombre, "-v", f"rol_app={rol}", "-f", str(ROL_APP))
        for script in ([GUARDIA] if guardia else []) + ([DATOS_2026_2] if datos_2026_2 else []) + list(despues):
            _psql(nombre, "-f", str(script))
    except BaseException:
        _borrar(nombre if creada else None, rol if rol_propio else None)
        raise
    return BaseDesechable(nombre, _conexion(nombre), rol, _conexion(nombre, rol) if rol else None)


def borrar(base: BaseDesechable) -> None:
    """Borra la base y su rol, y se niega a tocar un nombre sin el prefijo abet_demo_."""
    for nombre in (base.nombre, base.rol_app):
        if nombre is not None and not _DESECHABLE.fullmatch(nombre):
            raise ValueError("Solo se borran bases y roles desechables con el prefijo abet_demo_.")
    _borrar(base.nombre, base.rol_app)


@contextmanager
def abierta(
    sufijo: str | None = None,
    *,
    guardia: bool = False,
    rol_app: bool = True,
    datos_2026_2: bool = True,
    despues: Sequence[Path] = (),
) -> Iterator[BaseDesechable]:
    """Base desechable que se borra al salir del bloque, también si el bloque falla."""
    base = crear(sufijo, guardia=guardia, rol_app=rol_app, datos_2026_2=datos_2026_2, despues=despues)
    try:
        yield base
    finally:
        borrar(base)


def restos() -> tuple[list[str], list[str]]:
    """Bases y roles con el prefijo abet_demo_ que siguen en el servidor."""
    bases = _psql("postgres", "-At", "-c", f"SELECT datname FROM pg_database WHERE starts_with(datname, '{PREFIJO}')")
    roles = _psql("postgres", "-At", "-c", f"SELECT rolname FROM pg_roles WHERE starts_with(rolname, '{PREFIJO}')")
    return sorted(bases.split()), sorted(roles.split())


def exigir_sin_restos() -> None:
    """Lanza ErrorDeBase con los nombres de las bases y los roles abet_demo_ que siguen en el servidor."""
    bases, roles = restos()
    if bases or roles:
        quedan = ", ".join(bases + roles)
        raise ErrorDeBase(f"Quedan sin borrar {quedan}, y una prueba no debe dejar bases ni roles abet_demo_.")


def _version(ruta: Path) -> tuple[int, ...]:
    """Versión de V1_09__crear_acceso.sql como (1, 9), el orden de sort -t_ -k1,1V -k2,2n."""
    return tuple(int(parte) for parte in ruta.name[1:].split("__", 1)[0].split("_"))


def _sufijo_nuevo() -> str:
    return f"{os.getpid()}_{secrets.token_hex(4)}"


def _borrar(nombre: str | None, rol: str | None) -> None:
    sentencias = []
    if nombre is not None:
        sentencias.append(f"DROP DATABASE IF EXISTS {nombre} WITH (FORCE)")
    if rol is not None:
        # Después de la base, que guarda los permisos del rol, como en correr_pruebas.sh.
        sentencias.append(f"DROP ROLE IF EXISTS {rol}")
    fallas = []
    for sentencia in sentencias:
        try:
            _psql("postgres", "-c", sentencia)
        except ErrorDeBase as error:
            fallas.append(str(error))
    if fallas:
        aviso = "No se pudo borrar todo lo desechable, así que hay que borrarlo a mano."
        raise ErrorDeBase("\n".join([aviso, *fallas]))


def _entorno() -> dict[str, str]:
    """Variables de libpq sin APP_DB_CLAVE, solo si apuntan al clúster desechable de las pruebas.

    Sin APP_DB_CLAVE el rol de prueba nunca recibe contraseña. Fuera de la CI no hay valores por
    omisión, así que un PGHOST que falta nunca cae en localhost:5432, el clúster de la Mac, y
    cluster_desechable.exigir() detiene todo antes de la primera sentencia.
    """
    entorno = {clave: valor for clave, valor in os.environ.items() if clave != "APP_DB_CLAVE"}
    cluster = _cluster()
    if cluster.en_ci(entorno):
        entorno.setdefault("PGHOST", "localhost")
        entorno.setdefault("PGPORT", "5432")
    cluster.exigir(entorno)
    entorno["PGCLIENTENCODING"] = "UTF8"
    return entorno


def _cluster() -> ModuleType:
    """tests/cluster_desechable.py, cargado por su ruta porque tests/ no es un paquete."""
    nombre = "cluster_desechable"
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, Path(__file__).with_name("cluster_desechable.py"))
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


def _conexion(base: str, usuario: str | None = None) -> str:
    entorno = _entorno()
    datos = {"host": entorno["PGHOST"], "port": entorno["PGPORT"], "dbname": base}
    usuario = usuario or entorno.get("PGUSER")
    if usuario:
        datos["user"] = usuario
    return make_conninfo(**datos)


def _psql(base: str, *argumentos: str, opciones: str | None = None) -> str:
    entorno = _entorno()
    if opciones is not None:
        entorno["PGOPTIONS"] = opciones
    corrida = subprocess.run(
        [entorno.get("PSQL", "psql"), "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", base, *argumentos],
        env=entorno,
        capture_output=True,
        text=True,
        check=False,
    )
    if corrida.returncode != 0:
        detalle = corrida.stderr.strip() or corrida.stdout.strip()
        paso = " ".join(argumentos)
        raise ErrorDeBase(f"psql sale con el código {corrida.returncode} en {base} ({paso}).\n{detalle}")
    return corrida.stdout
