"""Cierre de la capacitación sin perder evidencia (spec 008, US-89, FR-025, T056).

Uso, desde la raíz del repositorio, con el CSV de la programación, la carpeta de la capacitación y la del respaldo
FUERA de todo repositorio, y la conexión a la base en las variables de libpq (PGHOST, PGDATABASE, PGUSER, PGPASSWORD,
PGSSLMODE y las demás)
    python -I db/herramientas/cerrar_capacitacion.py [--programacion CSV --periodo 2026-1]
        [--capacitacion CARPETA --respaldo CARPETA] [--aplicar]

El cierre tiene dos partes, y cada corrida pide al menos una.

1. La baja de las cuentas, con --programacion y --periodo. Lee el CSV de la programación con la lectura y las
   revisiones de forma de cargar_programacion.py, sin repetir sus correos en el informe. Da de baja, con activo
   falso en acceso.usuario_autorizado, las cuentas PROFESOR de los correos del CSV y las cuentas COORDINADOR con
   alcance en una asignatura del CSV en el periodo (la coordinación del curso), y cierra sus sesiones vigentes con
   least(expira_en, clock_timestamp()), como el cierre de sesión de la API. Una cuenta que dicta una sección fuera de
   las asignaturas del CSV en el periodo, o que tiene otro alcance, queda activa y el informe la cuenta. Nunca borra
   una fila, nunca cambia un rol y no toca acceso.credencial ni ninguna tabla de abet, así que las cargas, sus R-17
   y la conciliación de US-83 siguen como antes. Sin --aplicar corre en seco y termina con ROLLBACK, así que la
   corrida en seco informa exactamente lo que la corrida real haría. Con --aplicar escribe en una sola transacción, y
   una segunda corrida informa 0 cuentas nuevas dadas de baja.
2. La comprobación del respaldo, con --capacitacion y --respaldo. --capacitacion es la carpeta de la capacitación
   con el manifiesto.json de scripts/generar_exports_desde_maestra.py. --respaldo es una copia restaurada del
   respaldo de esa carpeta, por ejemplo la que restaura la skill respaldar-en-windows en una carpeta temporal,
   porque su respaldo es un tar.gz cifrado y no guarda la huella de cada archivo. El cierre comprueba que cada
   export del manifiesto tenga en las dos carpetas la huella SHA-256 del manifiesto y que el respaldo traiga el mismo
   manifiesto, e informa qué se puede borrar de la Mac. Nunca borra, mueve ni escribe un archivo.

El cierre no restablece la rama develop de Neon, no escribe en main, no despliega y no decide el destino de las
cargas de Química General, que espera a D-55, así que toda corrida termina con esa línea.

El guion usa solo la biblioteca estándar, para que corra con el Python 3.14 del Windows sin instalar paquetes, y
psql, que PSQL nombra cuando no está en el PATH. Los correos viajan a psql por su entrada estándar y no por
argumentos.

Códigos de salida. 0 cuando todo sale bien, en seco o con --aplicar, 1 cuando el respaldo no está completo o no
coincide, cuando el manifiesto no se lee o cuando el CSV se rechaza, 2 por un argumento inválido o una ruta dentro de
un repositorio git, antes de leer nada y de conectarse, y 3 cuando psql falta o la base no responde o rechaza la
escritura. La comprobación del respaldo corre antes que la baja, y el código final es el mayor de las dos partes.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType

USO = ("Uso: python -I db/herramientas/cerrar_capacitacion.py [--programacion CSV --periodo 2026-1] "
       "[--capacitacion CARPETA --respaldo CARPETA] [--aplicar]")
NADA = "No se guardó nada."
NO_BORRE = "No borre nada todavía."
MANIFIESTO = "manifiesto.json"
D_55 = "Destino de las cargas de Química General pendiente de decisión (D-55)."
SIN_RAMAS = "El cierre no restablece develop ni escribe en main."
SIN_BORRAR = "El cierre no borra ningún archivo."
HEX64 = re.compile(r"[0-9a-f]{64}")


def _programacion() -> ModuleType:
    """cargar_programacion.py, cargado por su ruta porque db/herramientas/ no es un paquete."""
    nombre = "cargar_programacion"
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, Path(__file__).with_name(f"{nombre}.py"))
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


P = _programacion()


class Rechazo(Exception):
    """El cierre se detiene con su mensaje, que va a stderr, y el código de salida."""

    def __init__(self, mensaje: str, codigo: int) -> None:
        super().__init__(mensaje)
        self.mensaje, self.codigo = mensaje, codigo


def _cantidad(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


# Argumentos

def dentro_de_un_repositorio(ruta: Path) -> bool:
    """Si la ruta o alguna carpeta que la contiene tiene .git, como carpeta en un clon o como archivo en un worktree."""
    resuelta = ruta.resolve()
    return any((carpeta / ".git").exists() for carpeta in (resuelta, *resuelta.parents))


class _Argumentos(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # noqa: ARG002, el mensaje de argparse no se muestra en inglés
        raise Rechazo(USO, 2)


def argumentos_de(argv: list[str] | None) -> argparse.Namespace:
    # Sin abreviaturas, porque --aplicar es la única llave entre la corrida en seco y la escritura.
    analizador = _Argumentos(add_help=False, allow_abbrev=False)
    for opcion in ("--programacion", "--periodo", "--capacitacion", "--respaldo"):
        analizador.add_argument(opcion)
    analizador.add_argument("--aplicar", action="store_true")
    leidos = analizador.parse_args(argv)
    baja = leidos.programacion is not None or leidos.periodo is not None
    respaldo = leidos.capacitacion is not None or leidos.respaldo is not None
    if not (baja or respaldo):
        raise Rechazo(USO, 2)
    if baja and not (leidos.programacion and leidos.periodo):
        raise Rechazo(USO, 2)
    if respaldo and not (leidos.capacitacion and leidos.respaldo):
        raise Rechazo(USO, 2)
    if leidos.aplicar and not baja:
        raise Rechazo(USO, 2)
    if baja and not P.PERIODO.fullmatch(leidos.periodo):
        raise Rechazo("El periodo no tiene la forma AAAA-C.", 2)
    for ruta, que in ((leidos.programacion, "El CSV de la programación"),
                      (leidos.capacitacion, "La carpeta de la capacitación"), (leidos.respaldo, "El respaldo")):
        if ruta and dentro_de_un_repositorio(Path(ruta)):
            raise Rechazo(f"{que} está dentro de un repositorio git. Use una ruta fuera de los repositorios.", 2)
    if baja and not Path(leidos.programacion).is_file():
        raise Rechazo("No se encuentra el CSV de la programación.", 2)
    return leidos


# Respaldo

def _huella(ruta: Path) -> str | None:
    try:
        return hashlib.sha256(ruta.read_bytes()).hexdigest() if ruta.is_file() else None
    except OSError:
        return None


def _manifiesto(carpeta: Path) -> tuple[bytes, list[tuple[str, str]]]:
    """Bytes del manifiesto y archivo y huella de cada export, o Rechazo si no describe sus archivos."""
    ilegible = Rechazo(f"El manifiesto de la carpeta de la capacitación no se puede leer. {NO_BORRE}", 1)
    try:
        crudo = (carpeta / MANIFIESTO).read_bytes()
        entradas = [(str(e["archivo"]), str(e["sha256"])) for e in json.loads(crudo.decode("utf-8"))["exports"]]
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError):
        raise ilegible from None
    if not entradas or len({archivo for archivo, _ in entradas}) != len(entradas):
        raise ilegible
    for archivo, huella in entradas:
        if Path(archivo).name != archivo or archivo in ("", ".", "..", MANIFIESTO) or not HEX64.fullmatch(huella):
            raise ilegible
    return crudo, entradas


def comprobar_respaldo(capacitacion: Path, respaldo: Path) -> tuple[int, list[str]]:
    """Código y líneas de la comprobación del respaldo. Solo lee, nunca borra ni escribe."""
    try:
        crudo, entradas = _manifiesto(capacitacion)
    except Rechazo as rechazo:
        return rechazo.codigo, [rechazo.mensaje]
    cambiados = sum(1 for archivo, huella in entradas if _huella(capacitacion / archivo) not in (None, huella))
    faltan = sum(1 for archivo, _ in entradas if _huella(respaldo / archivo) is None)
    otros = sum(1 for archivo, huella in entradas if _huella(respaldo / archivo) not in (None, huella))
    try:
        mismo_manifiesto = (respaldo / MANIFIESTO).read_bytes() == crudo
    except OSError:
        mismo_manifiesto = False
    lineas = []
    if cambiados:
        lineas.append(f"La carpeta de la capacitación trae {_cantidad(cambiados, 'archivo', 'archivos')} con otra "
                      f"huella que la del manifiesto. {NO_BORRE}")
    if faltan:
        lineas.append(f"El respaldo no trae {_cantidad(faltan, 'archivo', 'archivos')} del manifiesto. {NO_BORRE}")
    if otros:
        lineas.append(f"El respaldo trae {_cantidad(otros, 'archivo', 'archivos')} con otra huella que la del "
                      f"manifiesto. {NO_BORRE}")
    if not mismo_manifiesto:
        lineas.append(f"El respaldo no trae el manifiesto igual al de la carpeta. {NO_BORRE}")
    if lineas:
        return 1, lineas
    n = len(entradas)
    return 0, [f"{n} de {n} archivos respaldados y comprobados por su huella. Se pueden borrar de la Mac."]


# Baja de las cuentas

def _literal(texto: str) -> str:
    """Literal de SQL de un valor que ya pasó la forma de cargar_programacion.py."""
    return "'" + "''".join(texto.split("'")) + "'"


def _sql_de_la_baja(correos: list[str], asignaturas: list[str], aplicar: bool) -> str:
    valores_correo = ", ".join(f"({_literal(c)})" for c in correos)
    valores_asignatura = ", ".join(f"({_literal(a)})" for a in asignaturas)
    final = "COMMIT;" if aplicar else "ROLLBACK;"
    return rf"""
\set ON_ERROR_STOP 1
\set VERBOSITY terse
BEGIN;
CREATE TEMP TABLE cierre_correo (correo text PRIMARY KEY) ON COMMIT DROP;
INSERT INTO cierre_correo VALUES {valores_correo} ON CONFLICT DO NOTHING;
CREATE TEMP TABLE cierre_asignatura (codigo text PRIMARY KEY) ON COMMIT DROP;
INSERT INTO cierre_asignatura VALUES {valores_asignatura} ON CONFLICT DO NOTHING;
CREATE TEMP TABLE cierre_seccion ON COMMIT DROP AS
SELECT s.seccion_id
FROM abet.seccion s
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
WHERE pe.codigo = :'periodo' AND a.codigo IN (SELECT codigo FROM cierre_asignatura);
CREATE TEMP TABLE cierre_cuenta ON COMMIT DROP AS
SELECT u.usuario_id, u.rol, u.activo,
       CASE WHEN u.rol = 'PROFESOR' THEN EXISTS (
                SELECT 1 FROM acceso.docente_seccion d
                WHERE d.usuario_id = u.usuario_id AND d.seccion_id NOT IN (SELECT seccion_id FROM cierre_seccion))
            ELSE EXISTS (
                SELECT 1 FROM acceso.coordinacion_alcance ca
                LEFT JOIN abet.asignatura a ON a.asignatura_id = ca.asignatura_id
                LEFT JOIN abet.periodo pe ON pe.periodo_id = ca.periodo_id
                WHERE ca.usuario_id = u.usuario_id
                  AND (ca.carrera_id IS NOT NULL OR pe.codigo IS DISTINCT FROM :'periodo'
                       OR a.codigo NOT IN (SELECT codigo FROM cierre_asignatura)))
       END AS fuera
FROM acceso.usuario_autorizado u
WHERE (u.rol = 'PROFESOR' AND u.correo IN (SELECT correo FROM cierre_correo))
   OR (u.rol = 'COORDINADOR' AND EXISTS (
        SELECT 1 FROM acceso.coordinacion_alcance ca
        JOIN abet.asignatura a ON a.asignatura_id = ca.asignatura_id
        JOIN abet.periodo pe ON pe.periodo_id = ca.periodo_id
        WHERE ca.usuario_id = u.usuario_id AND pe.codigo = :'periodo'
          AND a.codigo IN (SELECT codigo FROM cierre_asignatura)));
WITH baja AS (
    UPDATE acceso.usuario_autorizado u SET activo = false
    FROM cierre_cuenta c
    WHERE u.usuario_id = c.usuario_id AND c.activo AND NOT c.fuera
    RETURNING u.usuario_id, u.rol
), cerradas AS (
    UPDATE acceso.sesion s SET expira_en = least(s.expira_en, clock_timestamp())
    WHERE s.usuario_id IN (SELECT usuario_id FROM baja) AND s.expira_en > clock_timestamp()
    RETURNING 1
)
SELECT 'RESULTADO',
       (SELECT count(*) FROM baja WHERE rol = 'PROFESOR'),
       (SELECT count(*) FROM baja WHERE rol = 'COORDINADOR'),
       (SELECT count(*) FROM cerradas),
       (SELECT count(*) FROM cierre_cuenta WHERE NOT activo),
       (SELECT count(*) FROM cierre_cuenta WHERE activo AND fuera),
       (SELECT count(*) FROM cierre_correo c WHERE NOT EXISTS (
            SELECT 1 FROM acceso.usuario_autorizado u WHERE u.correo = c.correo AND u.rol = 'PROFESOR'));
{final}
"""


def _correos_y_asignaturas(ruta: Path, periodo: str) -> tuple[list[str], list[str]]:
    """Correos y asignaturas del CSV, o Rechazo sin repetir ningún valor del archivo."""
    try:
        filas = P.leer(ruta.read_bytes())
    except OSError:
        raise Rechazo(f"El CSV de la programación no se puede leer. {NADA}", 1) from None
    except P.ArchivoRechazado:
        raise Rechazo(f"El CSV de la programación no tiene la forma de cargar_programacion.py. {NADA}", 1) from None
    errores = P.revisar(filas, periodo)
    if errores:
        raise Rechazo(f"La programación trae {_cantidad(len(errores), 'fila', 'filas')} sin la forma de "
                      f"cargar_programacion.py. Revísela en seco con ese guion. {NADA}", 1)
    return sorted({f.correo for f in filas}), sorted({f.asignatura for f in filas})


def dar_de_baja(ruta: Path, periodo: str, aplicar: bool) -> list[str]:
    """Líneas del informe de la baja, o Rechazo. Sin aplicar, la transacción termina con ROLLBACK."""
    correos, asignaturas = _correos_y_asignaturas(ruta, periodo)
    orden = [os.environ.get("PSQL") or "psql", "-X", "-q", "-At", "-F", "|", "-v", f"periodo={periodo}", "-f", "-"]
    try:
        corrida = subprocess.run(orden, input=_sql_de_la_baja(correos, asignaturas, aplicar), capture_output=True,
                                 text=True, encoding="utf-8", check=False)
    except OSError:
        raise Rechazo(f"No se encontró psql. PSQL nombra su ruta completa. {NADA}", 3) from None
    resultado = re.search(r"^RESULTADO\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|(\d+)$", corrida.stdout, flags=re.M)
    if corrida.returncode == 3:
        raise Rechazo(f"La base rechazó la baja. {NADA}", 3)
    if corrida.returncode != 0 or resultado is None:
        raise Rechazo(f"La base no respondió. {NADA}", 3)
    profesores, coordinaciones, sesiones, ya, fuera, sin_cuenta = (int(v) for v in resultado.groups())
    nombre = " y ".join(asignaturas)
    if aplicar:
        lineas = [f"Dio de baja {_cantidad(profesores, 'cuenta', 'cuentas')} de profesor y {coordinaciones} de "
                  f"coordinación, y cerró {_cantidad(sesiones, 'sesión vigente', 'sesiones vigentes')}."]
    else:
        lineas = [f"Daría de baja {_cantidad(profesores, 'cuenta', 'cuentas')} de profesor y {coordinaciones} de "
                  f"coordinación, y cerraría {_cantidad(sesiones, 'sesión vigente', 'sesiones vigentes')}. "
                  "No se guardó nada, y --aplicar lo guarda."]
    if ya:
        lineas.append(f"{_cantidad(ya, 'cuenta ya estaba dada', 'cuentas ya estaban dadas')} de baja.")
    if fuera:
        lineas.append(f"{_cantidad(fuera, 'cuenta tiene', 'cuentas tienen')} secciones o alcance fuera de {nombre} "
                      f"en {periodo} y {'queda activa' if fuera == 1 else 'quedan activas'}.")
    if sin_cuenta:
        lineas.append(f"{_cantidad(sin_cuenta, 'correo', 'correos')} de la programación no "
                      f"{'tiene' if sin_cuenta == 1 else 'tienen'} una cuenta de profesor.")
    lineas.append("Las cargas, sus R-17 y las contraseñas no cambian.")
    return lineas


# Principal

def principal(argv: list[str] | None = None) -> tuple[int, list[str], list[str]]:
    """Código de salida, líneas del informe y líneas de error."""
    try:
        argumentos = argumentos_de(argv)
    except Rechazo as rechazo:
        return rechazo.codigo, [], [rechazo.mensaje]
    codigo, lineas, errores = 0, [], []
    if argumentos.capacitacion:
        codigo, lineas = comprobar_respaldo(Path(argumentos.capacitacion), Path(argumentos.respaldo))
    if argumentos.programacion:
        modo = "con --aplicar" if argumentos.aplicar else "en seco"
        lineas.append(f"Baja de las cuentas de la capacitación en {argumentos.periodo}, {modo}.")
        try:
            lineas += dar_de_baja(Path(argumentos.programacion), argumentos.periodo, argumentos.aplicar)
        except Rechazo as rechazo:
            codigo, errores = max(codigo, rechazo.codigo), [rechazo.mensaje]
    return codigo, [*lineas, SIN_BORRAR, SIN_RAMAS, D_55], errores


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    codigo, lineas, errores = principal(sys.argv[1:] if argv is None else argv)
    for linea in lineas:
        print(linea)
    for error in errores:
        sys.stderr.write(error + "\n")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
