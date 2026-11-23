"""Registra la cuenta de la coordinación de un curso con su asignatura y su periodo (spec 008, US-72, FR-010, T032).

Lee el correo solo de la variable CORREO_COORDINACION, que desde el Windows de Jefferson llega por en_windows.py, lo
normaliza sin espacios a los lados y en minúscula, como acceso.usuario_autorizado, y nunca lo repite en el informe.
Sin --aplicar corre en seco, lee la base y dice qué registraría sin escribir. Con --aplicar escribe en una sola
transacción la cuenta COORDINADOR en acceso.usuario_autorizado y la fila de la asignatura y el periodo en
acceso.coordinacion_alcance, con INSERT y ON CONFLICT DO NOTHING, así que una segunda corrida informa 0 filas nuevas.
Nunca hace UPDATE de rol ni de activo y no toca acceso.credencial, porque la clave de ingreso la asigna Jefferson
aparte con asignar_claves.py y getpass (BR-ACCESO-14).

    python -I db/herramientas/registrar_coordinacion.py --asignatura 5643 --periodo 2026-1 [--aplicar]

Una asignatura sin plan de medición en el periodo entra con un aviso, porque la coordinación puede registrarse antes
que el plan. La conexión llega por las variables de libpq que psql lee solo (PGHOST, PGDATABASE, PGUSER, PGPASSWORD,
PGSSLMODE y las demás), nunca por argumentos, y PSQL nombra el programa psql cuando no está en el PATH, como en el
Windows. El correo viaja a psql por su entorno y psql lo lee con \\getenv, así que tampoco queda en un argumento. El
guion usa solo la biblioteca estándar, para que corra con el Python 3.14 del Windows sin instalar paquetes.

Códigos de salida. 0 cuando la corrida en seco o la escritura salen bien, 1 cuando la cuenta ya existe con otro rol o
está dada de baja, o la asignatura, el periodo o el correo no son válidos, 2 sin la variable o con un argumento que
falta, antes de conectarse, y 3 cuando psql falta, la base no responde o rechaza la escritura.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

VARIABLE = "CORREO_COORDINACION"
USO = "Uso: python -I db/herramientas/registrar_coordinacion.py --asignatura 5643 --periodo 2026-1 [--aplicar]"
# Las formas de ck_asignatura_codigo, ck_periodo_codigo con ck_periodo_ciclo y ck_usuario_autorizado_correo.
ASIGNATURA = re.compile(r"[0-9]{4}(?:[0-9]{2})?")
PERIODO = re.compile(r"[0-9]{4}-[0-2]")
CORREO = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
LARGO_CORREO = 254
NADA = "No se guardó nada."

# La lectura, que no escribe. Devuelve una sola fila separada por «|».
LECTURA = r"""
\set ON_ERROR_STOP 1
\set VERBOSITY terse
\getenv correo CORREO_COORDINACION
SELECT (SELECT count(*) FROM abet.asignatura WHERE codigo = :'asignatura'),
       (SELECT count(*) FROM abet.periodo WHERE codigo = :'periodo'),
       coalesce((SELECT rol FROM acceso.usuario_autorizado WHERE correo = :'correo'), '-'),
       coalesce((SELECT CASE WHEN activo THEN 'activo' ELSE 'baja' END
                 FROM acceso.usuario_autorizado WHERE correo = :'correo'), '-'),
       (SELECT count(*) FROM abet.plan_medicion pm
        JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id
        JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id
        WHERE a.codigo = :'asignatura' AND pe.codigo = :'periodo'),
       (SELECT count(*) FROM acceso.coordinacion_alcance ca
        JOIN acceso.usuario_autorizado u ON u.usuario_id = ca.usuario_id
        JOIN abet.asignatura a ON a.asignatura_id = ca.asignatura_id
        JOIN abet.periodo pe ON pe.periodo_id = ca.periodo_id
        WHERE u.correo = :'correo' AND a.codigo = :'asignatura' AND pe.codigo = :'periodo');
"""

# La escritura, en una sola transacción. Vuelve a revisar el rol y el estado de la cuenta antes del alcance, y si la
# cuenta no es una COORDINADOR activa deshace todo.
ESCRITURA = r"""
\set ON_ERROR_STOP 1
\set VERBOSITY terse
\getenv correo CORREO_COORDINACION
BEGIN;
WITH nueva AS (
    INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES (:'correo', 'COORDINADOR')
    ON CONFLICT DO NOTHING
    RETURNING 1
)
SELECT count(*) AS cuentas FROM nueva \gset
SELECT CASE WHEN rol = 'COORDINADOR' AND activo THEN 'true' ELSE 'false' END AS valida
FROM acceso.usuario_autorizado WHERE correo = :'correo' \gset
\if :valida
WITH nuevo AS (
    INSERT INTO acceso.coordinacion_alcance (usuario_id, asignatura_id, periodo_id)
    SELECT u.usuario_id, a.asignatura_id, pe.periodo_id
    FROM acceso.usuario_autorizado u, abet.asignatura a, abet.periodo pe
    WHERE u.correo = :'correo' AND a.codigo = :'asignatura' AND pe.codigo = :'periodo'
    ON CONFLICT DO NOTHING
    RETURNING 1
)
SELECT count(*) AS alcances FROM nuevo \gset
COMMIT;
\echo RESULTADO :cuentas :alcances
\else
ROLLBACK;
\echo RESULTADO cuenta_invalida
\endif
"""


class _Argumentos(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # noqa: ARG002, el mensaje de argparse no se muestra
        raise SystemExit(_falla(USO, 2))


def _ocultar(texto: str) -> str:
    """El texto sin el correo de la variable, tal como llega y normalizado."""
    valor = os.environ.get(VARIABLE, "")
    for forma in {valor, valor.strip(), valor.strip().lower()}:
        if len(forma) >= 4:
            texto = texto.replace(forma, f"[{VARIABLE} oculto]")
    return texto


def _falla(mensaje: str, codigo: int) -> int:
    sys.stderr.write(_ocultar(mensaje) + "\n")
    return codigo


def _filas(n: int) -> str:
    return "1 fila nueva" if n == 1 else f"{n} filas nuevas"


def _psql(sql: str, asignatura: str, periodo: str, correo: str) -> subprocess.CompletedProcess[str] | None:
    entorno = {**os.environ, VARIABLE: correo}
    orden = [os.environ.get("PSQL", "psql"), "-X", "-q", "-At", "-F", "|", "-v", f"asignatura={asignatura}",
             "-v", f"periodo={periodo}", "-f", "-"]
    try:
        return subprocess.run(orden, input=sql, env=entorno, capture_output=True, text=True, encoding="utf-8",
                              check=False)
    except OSError:
        return None


def main(argv: list[str] | None = None) -> int:
    analizador = _Argumentos(add_help=False, allow_abbrev=False)
    analizador.add_argument("--asignatura", required=True)
    analizador.add_argument("--periodo", required=True)
    analizador.add_argument("--aplicar", action="store_true")
    argumentos = analizador.parse_args(sys.argv[1:] if argv is None else argv)
    asignatura, periodo = argumentos.asignatura, argumentos.periodo

    crudo = os.environ.get(VARIABLE)
    if crudo is None or not crudo.strip():
        return _falla(f"Falta la variable {VARIABLE}.", 2)
    correo = crudo.strip().lower()
    if len(correo) > LARGO_CORREO or not CORREO.fullmatch(correo):
        return _falla(f"El valor de {VARIABLE} no tiene la forma de un correo. {NADA}", 1)
    if not ASIGNATURA.fullmatch(asignatura):
        return _falla(f"La asignatura {asignatura} no tiene la forma de un código de asignatura. {NADA}", 1)
    if not PERIODO.fullmatch(periodo):
        return _falla(f"El periodo {periodo} no tiene la forma AAAA-C. {NADA}", 1)

    modo = "con --aplicar" if argumentos.aplicar else "en seco"
    print(f"Registro de la coordinación de {asignatura} en {periodo}, {modo}.")
    lectura = _psql(LECTURA, asignatura, periodo, correo)
    if lectura is None:
        return _falla(f"No se encontró psql. PSQL nombra su ruta completa. {NADA}", 3)
    partes = lectura.stdout.strip().split("|")
    if lectura.returncode != 0 or len(partes) != 6:
        return _falla(f"La base no respondió a la lectura. {NADA}", 3)
    hay_asignatura, hay_periodo, rol, estado, filas_plan, alcances_previos = partes
    if hay_asignatura == "0":
        return _falla(f"La asignatura {asignatura} no existe en abet.asignatura. {NADA}", 1)
    if hay_periodo == "0":
        return _falla(f"El periodo {periodo} no existe en abet.periodo. {NADA}", 1)
    if rol not in ("-", "COORDINADOR"):
        return _falla(f"La cuenta ya existe con otro rol y el guion no lo cambia. {NADA}", 1)
    if estado == "baja":
        return _falla(f"La cuenta está dada de baja y el guion no la reactiva. {NADA}", 1)
    if filas_plan == "0":
        print(f"Aviso. La asignatura {asignatura} no tiene plan de medición en {periodo}, así que la coordinación verá "
              "sus secciones sin indicadores hasta que la carrera registre el plan.")

    cuenta_nueva, alcance_nuevo = rol == "-", alcances_previos == "0"
    if not argumentos.aplicar:
        print(f"{_frase('Registraría', cuenta_nueva, alcance_nuevo, asignatura, periodo)} "
              f"Son {_filas(int(cuenta_nueva) + int(alcance_nuevo))}. No se guardó nada, y --aplicar lo guarda.")
        print("La cuenta no recibe una clave de ingreso. Jefferson la asigna aparte con asignar_claves.py.")
        return 0

    escritura = _psql(ESCRITURA, asignatura, periodo, correo)
    if escritura is None:
        return _falla(f"No se encontró psql. PSQL nombra su ruta completa. {NADA}", 3)
    resultado = re.search(r"^RESULTADO (\S+)(?: (\d+))?$", escritura.stdout, flags=re.M)
    if escritura.returncode != 0 or resultado is None:
        return _falla(f"La base rechazó la escritura. {NADA}", 3)
    if resultado[1] == "cuenta_invalida":
        return _falla(f"La cuenta cambió durante el registro y ya no es una coordinación activa. {NADA}", 1)
    cuentas, alcances = int(resultado[1]), int(resultado[2])
    print(f"{_frase('Registró', cuentas == 1, alcances == 1, asignatura, periodo)} Registró {_filas(cuentas + alcances)}.")
    print("La cuenta no recibe una clave de ingreso. Jefferson la asigna aparte con asignar_claves.py.")
    return 0


def _frase(verbo: str, cuenta_nueva: bool, alcance_nuevo: bool, asignatura: str, periodo: str) -> str:
    alcance = f"el alcance de {asignatura} en {periodo}"
    if cuenta_nueva:
        return f"{verbo} 1 cuenta de coordinación nueva con {alcance}."
    if alcance_nuevo:
        return f"{verbo} {alcance} para la cuenta de coordinación que ya existe."
    return f"La cuenta de coordinación ya existe y ya tiene {alcance}."


if __name__ == "__main__":
    raise SystemExit(main())
