"""Asigna la contraseña de un usuario autorizado y guarda solo su hash Argon2id (T036, BR-ACCESO-02).

Uso, con la conexión directa del dueño de la base en DATABASE_URL (propuesta).

    python scripts/asignar_clave.py --correo docente410@example.invalid < archivo_con_la_contrasena

La contraseña llega por la entrada estándar. En una terminal se pide con getpass, que no la
muestra, y en una tubería se lee la primera línea sin su salto de línea. El comando guarda en
acceso.credencial el hash Argon2id de argon2-cffi, que empieza por «$argon2id$», y reemplaza el
anterior si existe. Nunca escribe la contraseña ni DATABASE_URL en la salida, en un archivo o en la
línea de comandos.

Códigos de salida. 0 si guarda el hash, 1 si el correo no está en acceso.usuario_autorizado, 2 si
la contraseña llega vacía o falta DATABASE_URL y 3 si la base no responde.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from collections.abc import Sequence

import psycopg
from argon2 import PasswordHasher

GUARDADA, SIN_USUARIO, SIN_DATOS, SIN_BASE = 0, 1, 2, 3
_ASIGNAR = """
INSERT INTO acceso.credencial (usuario_id, hash_clave)
SELECT usuario_id, %s FROM acceso.usuario_autorizado WHERE correo = %s
ON CONFLICT (usuario_id) DO UPDATE SET hash_clave = EXCLUDED.hash_clave, actualizado_en = now()
RETURNING usuario_id
"""


def _leer_contrasena() -> str:
    if sys.stdin.isatty():
        return getpass.getpass("Contraseña: ")
    return sys.stdin.readline().rstrip("\r\n")


def main(argumentos: Sequence[str] | None = None) -> int:
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--correo", required=True)
    opciones = analizador.parse_args(argumentos)
    correo = opciones.correo.strip().lower()
    base = os.environ.get("DATABASE_URL", "")
    if not base:
        print("Falta DATABASE_URL, la conexión del dueño de la base.", file=sys.stderr)
        return SIN_DATOS
    contrasena = _leer_contrasena()
    if not contrasena:
        print("La contraseña llegó vacía y no se guardó nada.", file=sys.stderr)
        return SIN_DATOS
    hash_clave = PasswordHasher().hash(contrasena)
    try:
        with psycopg.connect(base, autocommit=True) as conexion:
            fila = conexion.execute(_ASIGNAR, (hash_clave, correo)).fetchone()
    except psycopg.OperationalError:
        # El mensaje de libpq puede repetir el servidor o el usuario, así que no se imprime.
        print("No se pudo conectar con la base.", file=sys.stderr)
        return SIN_BASE
    if fila is None:
        print(f"{correo} no está en acceso.usuario_autorizado y no se guardó nada.", file=sys.stderr)
        return SIN_USUARIO
    print(f"Contraseña asignada a {correo}. acceso.credencial guarda solo su hash Argon2id.")
    return GUARDADA


if __name__ == "__main__":
    sys.exit(main())
