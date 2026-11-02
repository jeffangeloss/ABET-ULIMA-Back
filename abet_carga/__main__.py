"""Comando python -m abet_carga, que carga un export y genera el R-17 y la constancia (parte de T039).

Subcomandos.
- cargar ARCHIVO --asignatura --seccion --periodo --correo carga el export en la sección con
  abet_carga.carga.cargar(). Imprime los conteos, la huella SHA-256 (Secure Hash Algorithm de 256
  bits), el estado y cada rechazo y aviso con su fila, su indicador de desempeño (performance
  indicator, PI) y su motivo, leídos de la constancia que guarda la base. Nunca imprime un nombre,
  un acceso ni el valor leído de una celda (BR-CARGA-17).
- r17 --carga --correo --carpeta escribe en la carpeta constancia_<carga_id>.json, el cuerpo de
  BR-R17-10, y el R-17 de una carga PUBLICADA (BR-R17-01 a BR-R17-09).

Los dos preguntan antes a app/permisos.py, el único dueño de BR-ACCESO-07 y BR-ACCESO-08. Si el
usuario no tiene la sección a su cargo, o si el usuario, la sección o la carga no existen, el
comando imprime «La sección no está a su cargo.», no escribe nada y sale con 3. Así un
identificador ajeno no revela nada, igual que el 403 de la interfaz.

La base sale de --base o, si no llega, de DATABASE_URL, y el comando nunca imprime esa cadena,
que en Neon trae la contraseña. --rol hace SET ROLE a ese rol después de conectar, como la demo
del corte 1 con el rol de db/plataforma/neon/crear_rol_app.sql. CONJUNTO_REGLAS y
GUARDIA_DATOS_INVENTADOS salen del entorno, como en el despliegue (BR-CARGA-01 y BR-CARGA-07).

Códigos de salida. 0 si la carga queda PUBLICADA (también YA_PUBLICADA) o si el R-17 se genera, 1 si
la carga no se publica o la carga no tiene R-17, 2 si falta la configuración o la base no responde
y 3 si la sección no está a cargo del usuario.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import openpyxl
import psycopg
from psycopg import sql

from abet_carga import constancia, r17
from abet_carga.carga import ConfiguracionInvalida, Configuracion, Resultado, cargar
from app import permisos

PUBLICADA, NO_PUBLICADA, SIN_CONFIGURACION, SIN_ALCANCE = 0, 1, 2, 3
_PUBLICADAS = {Resultado.PUBLICADA, Resultado.YA_PUBLICADA}
_SECCION = """
SELECT s.seccion_id
FROM abet.seccion s
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
JOIN abet.periodo pe   ON pe.periodo_id = s.periodo_id
WHERE a.codigo = %s AND s.numero = %s AND pe.codigo = %s
"""
_USUARIO = "SELECT usuario_id FROM acceso.usuario_autorizado WHERE correo = lower(btrim(%s))"
_SECCION_DE_LA_CARGA = "SELECT seccion_id FROM abet.carga WHERE carga_id = %s"


class _SinAlcance(Exception):
    """El usuario, la sección o la carga no existen, o la sección no está a cargo del usuario."""


class _SinConfiguracion(Exception):
    """Falta la base, CONJUNTO_REGLAS u otra pieza del despliegue."""


def main(argumentos: Sequence[str] | None = None) -> int:
    """Corre el subcomando y devuelve el código de salida."""
    opciones = _analizador().parse_args(argumentos)
    try:
        with _conectar(opciones.base, opciones.rol) as conexion:
            return int(opciones.correr(conexion, opciones))
    except _SinAlcance:
        print(permisos.SIN_ALCANCE)
        return SIN_ALCANCE
    except (_SinConfiguracion, ConfiguracionInvalida) as error:
        print(error)
        return SIN_CONFIGURACION


def _analizador() -> argparse.ArgumentParser:
    analizador = argparse.ArgumentParser(prog="python -m abet_carga", description=__doc__.splitlines()[0])
    subcomandos = analizador.add_subparsers(required=True)
    subir = subcomandos.add_parser("cargar", help="Carga un export en una sección.")
    subir.add_argument("archivo", type=Path)
    subir.add_argument("--asignatura", required=True)
    subir.add_argument("--seccion", required=True)
    subir.add_argument("--periodo", required=True)
    subir.set_defaults(correr=_subcomando_cargar)
    reporte = subcomandos.add_parser("r17", help="Genera el R-17 y la constancia de una carga.")
    reporte.add_argument("--carga", required=True, type=int)
    reporte.add_argument("--carpeta", required=True, type=Path)
    reporte.set_defaults(correr=_subcomando_r17)
    for subcomando in (subir, reporte):
        subcomando.add_argument("--correo", required=True)
        subcomando.add_argument("--base", default=None, help="Cadena de conexión; sin ella, DATABASE_URL.")
        subcomando.add_argument("--rol", default=None, help="Rol al que la conexión hace SET ROLE.")
    return analizador


def _conectar(base: str | None, rol: str | None) -> psycopg.Connection[Any]:
    base = base or os.environ.get("DATABASE_URL")
    if not base:
        raise _SinConfiguracion("Falta la base. Use --base o DATABASE_URL.")
    try:
        conexion = psycopg.connect(base, autocommit=True)
    except psycopg.OperationalError:
        # El mensaje de libpq puede repetir el servidor o el usuario, así que no se imprime.
        raise _SinConfiguracion("No se pudo conectar con la base.") from None
    if rol:
        conexion.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(rol)))
    return conexion


def _uno(conexion: psycopg.Connection[Any], consulta: str, *parametros: object) -> int:
    fila = conexion.execute(consulta, parametros).fetchone()
    if fila is None:
        raise _SinAlcance()
    return int(fila[0])


def _subcomando_cargar(conexion: psycopg.Connection[Any], opciones: argparse.Namespace) -> int:
    configuracion = Configuracion.desde_entorno()
    seccion_id = _uno(conexion, _SECCION, opciones.asignatura, opciones.seccion, opciones.periodo)
    usuario_id = _uno(conexion, _USUARIO, opciones.correo)
    if not permisos.puede_subir(conexion, usuario_id, seccion_id):
        raise _SinAlcance()
    contenido = opciones.archivo.read_bytes()
    resultado = cargar(conexion, contenido, nombre_archivo=opciones.archivo.name, seccion_id=seccion_id,
                       usuario_id=usuario_id, configuracion=configuracion)
    print(f"Archivo: {opciones.archivo.name}")
    print(f"Huella SHA-256: {hashlib.sha256(contenido).hexdigest()}")
    print(f"Resultado: {resultado.resultado} ({resultado.codigo_http})")
    if resultado.carga_id is not None:
        _imprimir_constancia(constancia.armar(conexion, resultado.carga_id))
    elif resultado.mensaje:
        print(f"Mensaje: {resultado.mensaje}")
    return PUBLICADA if resultado.resultado in _PUBLICADAS else NO_PUBLICADA


def _imprimir_constancia(cuerpo: dict[str, Any]) -> None:
    print(f"Carga: {cuerpo['carga_id']}")
    print(f"Estado: {cuerpo['estado']}")
    print(f"Filas leídas: {cuerpo['filas_leidas']}")
    print(f"Filas aceptadas: {cuerpo['filas_aceptadas']}")
    print(f"Filas rechazadas: {cuerpo['filas_rechazadas']}")
    for rechazo in cuerpo["rechazos"]:
        donde = "carga" if rechazo["fila"] is None else f"fila {rechazo['fila']}"
        pi = "" if rechazo["pi"] is None else f", PI {rechazo['pi']}"
        print(f"Rechazo: {donde}{pi}, {rechazo['motivo']}")
    for aviso in cuerpo["avisos"]:
        pi = "carga" if aviso["pi"] is None else f"PI {aviso['pi']}"
        print(f"Aviso: {pi}, {aviso['motivo']}")
    if cuerpo["mensaje"]:
        print(f"Mensaje: {cuerpo['mensaje']}")


def _subcomando_r17(conexion: psycopg.Connection[Any], opciones: argparse.Namespace) -> int:
    seccion_id = _uno(conexion, _SECCION_DE_LA_CARGA, opciones.carga)
    usuario_id = _uno(conexion, _USUARIO, opciones.correo)
    if not permisos.puede_leer(conexion, usuario_id, seccion_id):
        raise _SinAlcance()
    opciones.carpeta.mkdir(parents=True, exist_ok=True)
    cuerpo = constancia.armar(conexion, opciones.carga)
    ruta_constancia = opciones.carpeta / f"constancia_{opciones.carga}.json"
    ruta_constancia.write_text(json.dumps(cuerpo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Constancia: {ruta_constancia}")
    try:
        ruta = r17.generar(conexion, opciones.carga, opciones.carpeta)
    except r17.CargaNoPublicada:
        print("R-17: no se genera, porque la carga no está publicada.")
        return NO_PUBLICADA
    except r17.SeccionSuperaPlantilla:
        print("R-17: no se genera, porque la sección no cabe en la plantilla.")
        return NO_PUBLICADA
    print(f"R-17: {ruta}")
    print(f"Logro sobre calificados: {_logros(ruta)}")
    return PUBLICADA


def _logros(ruta: Path) -> str:
    """Porcentaje de cada PI tal como lo escribe el R-17, en las filas 24 a 26 de su hoja."""
    libro = openpyxl.load_workbook(ruta, read_only=True)
    try:
        hoja = libro[r17.HOJA]
        pares = [(hoja[f"B{fila}"].value, hoja[f"E{fila}"].value) for fila in r17.FILAS_DEL_BLOQUE_II]
    finally:
        libro.close()
    return ", ".join(f"{pi} {_porcentaje(valor)}" for pi, valor in pares if pi is not None)


def _porcentaje(valor: object) -> str:
    if not isinstance(valor, int | float):
        return "sin dato"
    return f"{valor * 100:.1f} %".replace(".", ",")


if __name__ == "__main__":
    sys.exit(main())
