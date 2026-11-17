"""Clúster de PostgreSQL 18 desechable para las pruebas de Python que crean o borran bases.

Fuera de la integración continua (continuous integration, CI), ninguna prueba usa el clúster de la
Mac (localhost:5432), donde viven abet_sis_med_dev y las bases de otros proyectos. El 2026-10-28 una
mutación de tests/base_desechable.py apagó su guardia de borrado y una prueba borró abet_sis_med_dev,
y desde entonces las bases desechables viven en un clúster que también es desechable.

iniciar() corre initdb en una carpeta temporal y pg_ctl arranca el servidor escuchando solo en un
socket de Unix de esa carpeta, sin TCP, así que nada fuera de las pruebas lo alcanza. Devuelve las
variables de libpq que lo apuntan, y detener() lo apaga y borra la carpeta. En la CI no hace falta,
porque el servicio postgres:18 del job ya es desechable. La CI se reconoce por GITHUB_ACTIONS=true,
por RUNNER_TEMP no vacío (GitHub Actions lo define en cada job) y por una plataforma distinta de
macOS, así que exportar solo GITHUB_ACTIONS=true en la Mac no abre el clúster local.

El clúster es de PostgreSQL 18, la versión de Neon (J-17). iniciar() toma los binarios de PG_BIN, si
está definida, o los de Homebrew (postgresql@18), deja esa carpeta al frente del PATH de la sesión para
que psql también sea de la 18, y se niega a seguir si initdb es de otra versión.

exigir() es la guardia que tests/base_desechable.py corre antes de cada sentencia. Se niega a seguir
si las variables de libpq no apuntan al clúster que nombra ABET_CLUSTER_DESECHABLE, y comprueba con
SHOW data_directory que el servidor que responde es ese clúster y no otro. db/pruebas/cluster_desechable.sh
hace lo mismo para db/pruebas/correr_pruebas.sh y scripts/demo_corte1.sh.
"""

from __future__ import annotations

import functools
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

PUERTO = 54329
VARIABLE = "ABET_CLUSTER_DESECHABLE"
# Versión mayor de Neon (J-17); el clúster de la Mac debe ser de la misma.
MAYOR = "18"
# Un socket de Unix admite rutas de hasta 103 bytes en macOS, y la carpeta del socket más
# «/.s.PGSQL.54329» debe caber, así que una carpeta temporal larga se reemplaza por /tmp.
_LARGO_MAXIMO = 60


class ClusterAjeno(RuntimeError):
    """Las variables de libpq apuntan a un servidor que no es el clúster desechable de las pruebas."""


@dataclass(frozen=True)
class Cluster:
    """Clúster desechable con su carpeta y las variables de libpq que lo alcanzan."""

    carpeta: Path
    entorno: dict[str, str]


def en_ci(entorno: Mapping[str, str] | None = None, plataforma: str | None = None) -> bool:
    """True en GitHub Actions, donde el servicio postgres:18 del job ya es desechable.

    Exige GITHUB_ACTIONS=true, RUNNER_TEMP no vacío y una plataforma distinta de macOS, porque la
    primera variable sola la puede exportar cualquiera en la Mac. plataforma toma sys.platform por
    omisión, y las pruebas la pasan para comprobar la regla en cualquier máquina.
    """
    variables = os.environ if entorno is None else entorno
    plataforma = sys.platform if plataforma is None else plataforma
    return (
        variables.get("GITHUB_ACTIONS") == "true"
        and bool(variables.get("RUNNER_TEMP"))
        and plataforma != "darwin"
    )


def _ruta_con_binarios() -> str:
    """PATH con los binarios de PostgreSQL 18 al frente: los de PG_BIN, si está definida, o los de Homebrew."""
    homebrew = (f"/opt/homebrew/opt/postgresql@{MAYOR}/bin", f"/usr/local/opt/postgresql@{MAYOR}/bin")
    carpeta = os.environ.get("PG_BIN") or next((c for c in homebrew if Path(c, "initdb").exists()), "")
    ruta = os.environ.get("PATH", "")
    return f"{carpeta}{os.pathsep}{ruta}" if carpeta else ruta


def _exigir_version(entorno: Mapping[str, str]) -> None:
    """Se niega a crear el clúster si initdb no es de la versión mayor de Neon."""
    try:
        version = subprocess.run(["initdb", "--version"], env=dict(entorno), capture_output=True, text=True, check=False).stdout
    except FileNotFoundError:
        version = ""
    if f" {MAYOR}." not in version:
        raise RuntimeError(
            f"initdb no es de PostgreSQL {MAYOR}, la versión de Neon (J-17). "
            f"Instala postgresql@{MAYOR} con Homebrew o define PG_BIN con la carpeta de sus binarios."
        )


def iniciar() -> Cluster:
    """Crea y arranca un clúster nuevo de PostgreSQL 18, vacío y con autenticación trust solo por su socket."""
    ruta = _ruta_con_binarios()
    _exigir_version({**os.environ, "PATH": ruta})
    base = tempfile.gettempdir()
    if len(base) > _LARGO_MAXIMO:
        base = "/tmp"
    carpeta = Path(tempfile.mkdtemp(prefix="abet_pg_", dir=base))
    datos = carpeta / "datos"
    entorno = {**os.environ, "LC_ALL": "en_US.UTF-8", "PATH": ruta}
    opciones = (
        f"-p {PUERTO} -k {carpeta} -c listen_addresses='' "
        "-c fsync=off -c full_page_writes=off -c synchronous_commit=off"
    )
    try:
        _correr(["initdb", "-D", str(datos), "-U", "postgres", "-A", "trust", "-E", "UTF8", "--locale=en_US.UTF-8"], entorno)
        _correr(["pg_ctl", "-D", str(datos), "-l", str(carpeta / "servidor.log"), "-w", "-o", opciones, "start"], entorno)
    except BaseException:
        shutil.rmtree(carpeta, ignore_errors=True)
        raise
    variables = {
        "PGHOST": str(carpeta),
        "PGPORT": str(PUERTO),
        "PGUSER": "postgres",
        "PGDATABASE": "postgres",
        "PATH": ruta,
        VARIABLE: str(datos),
    }
    return Cluster(carpeta=carpeta, entorno=variables)


def detener(cluster: Cluster) -> None:
    """Apaga el clúster sin esperar a que las conexiones cierren y borra su carpeta."""
    subprocess.run(
        ["pg_ctl", "-D", cluster.entorno[VARIABLE], "-m", "immediate", "-w", "stop"],
        env={**os.environ, "PATH": cluster.entorno.get("PATH", os.environ.get("PATH", ""))},
        capture_output=True,
        check=False,
    )
    shutil.rmtree(cluster.carpeta, ignore_errors=True)


def exigir(entorno: Mapping[str, str], plataforma: str | None = None) -> None:
    """Se niega a seguir si entorno no apunta al clúster desechable de las pruebas."""
    if en_ci(entorno, plataforma):
        return
    datos = entorno.get(VARIABLE, "")
    host = entorno.get("PGHOST", "")
    if not datos or not host or Path(host).resolve() != Path(datos).parent.resolve():
        raise ClusterAjeno(
            "Las bases desechables solo se crean y se borran en el clúster desechable de las pruebas "
            f"(tests/cluster_desechable.py), nunca en el clúster de la Mac. PGHOST={host or '(vacío)'} "
            f"y {VARIABLE}={datos or '(vacía)'} no lo nombran."
        )
    _comprobar_servidor(host, entorno.get("PGPORT", ""), datos)


@functools.lru_cache(maxsize=8)
def _comprobar_servidor(host: str, puerto: str, datos: str) -> None:
    # Una sola consulta por clúster y proceso, porque base_desechable llama a exigir() antes de cada psql.
    corrida = subprocess.run(
        ["psql", "-X", "-At", "-h", host, "-p", puerto, "-U", "postgres", "-d", "postgres", "-c", "SHOW data_directory"],
        capture_output=True,
        text=True,
        check=False,
    )
    respuesta = corrida.stdout.strip()
    if corrida.returncode != 0 or Path(respuesta).resolve() != Path(datos).resolve():
        raise ClusterAjeno(
            f"El servidor de PGHOST={host} y PGPORT={puerto} no es el clúster desechable de {VARIABLE}."
        )


def _correr(orden: list[str], entorno: Mapping[str, str]) -> None:
    corrida = subprocess.run(orden, env=dict(entorno), capture_output=True, text=True, check=False)
    if corrida.returncode != 0:
        raise RuntimeError(f"{orden[0]} sale con el código {corrida.returncode}.\n{corrida.stderr.strip()}")
