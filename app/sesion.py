"""Sesión con contraseña asignada y cookie abet_sesion (T036, BR-ACCESO-02 a BR-ACCESO-06).

Las reglas de negocio (business rules, BR) viven en specs/features/acceso/acceso.spec.md.

1. El correo se normaliza sin espacios a los lados y en minúscula, como lo guarda
   acceso.usuario_autorizado (BR-ACCESO-03).
2. La contraseña se compara con el hash Argon2id de acceso.credencial con argon2-cffi. Un correo
   desconocido, un usuario sin contraseña o inactivo y una contraseña errada reciben la misma
   IngresoFallido, y los tres primeros casos verifican también un hash de relleno, así que el
   tiempo de la respuesta no distingue un correo registrado (BR-ACCESO-02 y BR-ACCESO-04).
3. Cada fallo suma una fila a acceso.intento_fallido con el HMAC-SHA-256 del correo normalizado,
   el código de autenticación de mensajes basado en hash (hash-based message authentication code)
   con el algoritmo de hash seguro de 256 bits (Secure Hash Algorithm). La clave del HMAC es el HMAC
   de la etiqueta «acceso.intento_fallido» con SESION_SECRETO (propuesta). Con 5 fallos del mismo
   hash en los últimos 15 minutos, posteriores al último ingreso correcto del usuario de ese correo,
   el intento siguiente recibe DemasiadosIntentos, aunque traiga la contraseña correcta, y no suma
   otra fila (BR-ACCESO-05). Un candado consultivo de la transacción, pg_advisory_xact_lock sobre el
   hash de la cuenta, serializa el conteo, la verificación y la escritura de una misma cuenta, así
   que una ráfaga de intentos simultáneos tampoco evalúa más de 5 contraseñas.
4. Un ingreso correcto crea un token aleatorio de 32 bytes, que viaja solo en la cookie, y guarda en
   acceso.sesion solo usuario_id y el SHA-256 del token en hexadecimal. La base pone creada_en y
   expira_en, 12 horas después (BR-ACCESO-03).
5. Cada petición busca la sesión por el hash del token, vigente y de un usuario activo, y lee el
   rol desde la base (BR-ACCESO-06). El cierre fija expira_en en least(expira_en, clock_timestamp())
   sin borrar la fila.

Ninguna función escribe en el registro de la aplicación una contraseña, un token ni el correo de un
intento fallido.
"""

from __future__ import annotations

import functools
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Any

import psycopg
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends, HTTPException, Request
from psycopg.rows import class_row

from app.configuracion import ajustes_de, conexion

COOKIE = "abet_sesion"
DURACION = 12 * 60 * 60
MAXIMO_DE_FALLOS = 5
ETIQUETA_DE_INTENTOS = b"acceso.intento_fallido"
LARGO_MAXIMO_DEL_TOKEN = 128
INCORRECTOS = "Correo o contraseña incorrectos."
DEMASIADOS = "Demasiados intentos. Espere 15 minutos."
VENCIDA = "La sesión venció. Ingrese otra vez."

_CREDENCIAL = """
SELECT u.usuario_id, u.correo, u.rol, u.activo, c.hash_clave
FROM acceso.usuario_autorizado u
LEFT JOIN acceso.credencial c ON c.usuario_id = u.usuario_id
WHERE u.correo = %s
"""
# Los fallos de los últimos 15 minutos posteriores al último ingreso correcto del usuario de ese correo.
_FALLOS = """
SELECT count(*)
FROM acceso.intento_fallido i
WHERE i.hash_cuenta = %(cuenta)s
  AND i.intentado_en > now() - interval '15 minutes'
  AND i.intentado_en > coalesce((SELECT max(s.creada_en)
                                 FROM acceso.sesion s
                                 JOIN acceso.usuario_autorizado u ON u.usuario_id = s.usuario_id
                                 WHERE u.correo = %(correo)s), '-infinity')
"""
_CANDADO = "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))"
_FALLO = "INSERT INTO acceso.intento_fallido (hash_cuenta) VALUES (%s)"
_SESION_NUEVA = "INSERT INTO acceso.sesion (usuario_id, hash_token) VALUES (%s, %s)"
_SESION_VIGENTE = """
SELECT u.usuario_id, u.correo, u.rol
FROM acceso.sesion s
JOIN acceso.usuario_autorizado u ON u.usuario_id = s.usuario_id
WHERE s.hash_token = %s AND s.expira_en > now() AND u.activo
"""
_CIERRE = "UPDATE acceso.sesion SET expira_en = least(expira_en, clock_timestamp()) WHERE hash_token = %s"


class IngresoFallido(Exception):
    """Correo o contraseña que no coinciden, el 401 único de BR-ACCESO-04."""


class DemasiadosIntentos(Exception):
    """Cinco fallos seguidos del mismo correo en 15 minutos, el 429 de BR-ACCESO-05."""


@dataclass(frozen=True)
class Usuario:
    """Usuario de la sesión, con el rol que la base dice en esta petición."""

    usuario_id: int
    correo: str
    rol: str


def normalizar_correo(correo: str) -> str:
    """Correo sin espacios a los lados y en minúscula, como lo guarda acceso.usuario_autorizado."""
    return correo.strip().lower()


def hash_cuenta(sesion_secreto: str, correo: str) -> str:
    """HMAC-SHA-256 del correo normalizado con la clave derivada de SESION_SECRETO, en hexadecimal minúscula."""
    clave = hmac.new(sesion_secreto.encode(), ETIQUETA_DE_INTENTOS, hashlib.sha256).digest()
    return hmac.new(clave, normalizar_correo(correo).encode(), hashlib.sha256).hexdigest()


def hash_token(token: str) -> str:
    """SHA-256 del token de la cookie en hexadecimal, lo único que guarda acceso.sesion."""
    return hashlib.sha256(token.encode()).hexdigest()


@functools.cache
def _hash_de_relleno() -> str:
    # Un hash de una contraseña al azar que nadie conoce, para que todo fallo cueste lo mismo.
    return PasswordHasher().hash(secrets.token_urlsafe(32))


def _coincide(hash_clave: str | None, contrasena: str) -> bool:
    try:
        return PasswordHasher().verify(hash_clave or _hash_de_relleno(), contrasena) and hash_clave is not None
    except (VerificationError, InvalidHashError):
        return False


def ingresar(conexion: psycopg.Connection[Any], correo: str, contrasena: str, sesion_secreto: str) -> tuple[Usuario, str]:
    """Abre una sesión y devuelve el usuario y el token de la cookie, o lanza IngresoFallido o DemasiadosIntentos."""
    correo = normalizar_correo(correo)
    cuenta = hash_cuenta(sesion_secreto, correo)
    fallido = False
    # El candado de la transacción serializa los intentos de una misma cuenta desde el conteo hasta
    # la fila del fallo o la sesión nueva, así que una ráfaga simultánea no evalúa más de 5 contraseñas.
    with conexion.transaction():
        conexion.execute(_CANDADO, (cuenta,))
        fallos = conexion.execute(_FALLOS, {"cuenta": cuenta, "correo": correo}).fetchone()
        if fallos is not None and fallos[0] >= MAXIMO_DE_FALLOS:
            raise DemasiadosIntentos()
        fila = conexion.execute(_CREDENCIAL, (correo,)).fetchone()
        vigente = fila is not None and fila[3]
        hash_clave = fila[4] if vigente else None
        if _coincide(hash_clave, contrasena):
            assert fila is not None
            token = secrets.token_urlsafe(32)
            conexion.execute(_SESION_NUEVA, (fila[0], hash_token(token)))
        else:
            # La fila del fallo se confirma con la transacción, que una excepción desharía.
            conexion.execute(_FALLO, (cuenta,))
            fallido = True
    if fallido:
        raise IngresoFallido()
    assert fila is not None
    return Usuario(fila[0], fila[1], fila[2]), token


def usuario_del_token(conexion: psycopg.Connection[Any], token: str | None) -> Usuario | None:
    """Usuario de una sesión vigente de un usuario activo, o None."""
    if not token or len(token) > LARGO_MAXIMO_DEL_TOKEN:
        return None
    with conexion.cursor(row_factory=class_row(Usuario)) as cursor:
        return cursor.execute(_SESION_VIGENTE, (hash_token(token),)).fetchone()


def cerrar(conexion: psycopg.Connection[Any], token: str | None) -> None:
    """Vence la sesión del token sin borrar su fila. Sin token, o con uno desconocido, no hace nada."""
    if token and len(token) <= LARGO_MAXIMO_DEL_TOKEN:
        conexion.execute(_CIERRE, (hash_token(token),))


def usuario_actual(request: Request, abierta: psycopg.Connection[Any] = Depends(conexion)) -> Usuario:
    """Dependencia de las rutas con sesión, que responde 401 sin una sesión vigente (BR-ACCESO-06)."""
    usuario = usuario_del_token(abierta, request.cookies.get(COOKIE))
    if usuario is None:
        raise HTTPException(status_code=401, detail=VENCIDA)
    return usuario


def fijar_cookie(request: Request, respuesta: Any, token: str, *, vigencia: int = DURACION) -> None:
    """Cookie abet_sesion de primera parte, HttpOnly, Secure salvo en local, SameSite=Lax y Path=/."""
    respuesta.set_cookie(COOKIE, token, max_age=vigencia, httponly=True, secure=ajustes_de(request).cookie_segura,
                         samesite="lax", path="/")
