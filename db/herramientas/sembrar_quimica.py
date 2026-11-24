"""Siembra de Química General en una rama de Neon, en el orden de FR-020 (spec 008, US-86, T027).

Corre en orden los pasos de la siembra, cada uno con su propio guion, y se detiene en el primer paso que termina
con un código distinto de 0. Sin --aplicar corre cada paso en seco, con el modo en seco de su guion, así el informe
dice lo que haría cada uno sin escribir nada. El orden importa, porque la vigencia de IND-2026 antes del alcance
nuevo dejaría a la coordinación de Ambiental ver las secciones de Química.

En seco, el paso migraciones solo corre flyway info, así que en una rama sin V1_12 a V1_14, como develop o main antes
de la siembra, los pasos que leen o escriben lo que esas migraciones crean (alcance_ambiental, plan_quimica,
programacion, coordinacion y controles) solo se anuncian. La siembra lo sabe porque acceso.coordinacion_alcance, que
crea V1_14, todavía no existe, y con Flyway outOfOrder en false V1_14 llega después de V1_12 y V1_13.

El paso migraciones deja también al rol de la API leyendo acceso.coordinacion_alcance, porque el callback
db/callbacks/afterMigrate__permisos_lectura.sql le da ese SELECT al final de cada migrate (corrección del 2026-11-23).
Sin él, el Back con el _ALCANCE nuevo respondería 500 a cada cuenta, porque PostgreSQL revisa el permiso de toda tabla
de la consulta, también la de una rama OR que no se evalúa.

La siembra con --aplicar se detiene en el despliegue y se reanuda con --desde plan_quimica --back-desplegado. Ese
segundo tramo no corre huella_antes, así que recibe la huella de Ambiental de antes con --huella-antes, el valor que
el primer tramo escribe en su orden para reanudar. Una corrida en la que huella_despues corre sin huella_antes y sin
--huella-antes termina con 2 antes de conectarse, así la comparación nunca se pierde en silencio.

    python -I db/herramientas/sembrar_quimica.py --rama develop [--aplicar] [--programacion RUTA] [--desde PASO]
                                                 [--back-desplegado] [--huella-antes HUELLA]
                                                 [--respaldo-en CARPETA] [--pi 6.1]
    python -I db/herramientas/sembrar_quimica.py --rama develop --solo-comprobar

Pasos. respaldo (respaldar_neon.sh, solo con --aplicar), huella_antes (huella_ambiental.sql), migraciones (Flyway
con el entorno neon hasta la versión 1.14, V1_12 a V1_14), alcance_ambiental (alcance_coordinacion_ambiental.sql),
despliegue (el Back con el _ALCANCE nuevo, que Jefferson despliega y confirma con --back-desplegado), plan_quimica
(plan_quimica_2026_1.sql), programacion (cargar_programacion.py con --periodo 2026-1), coordinacion
(registrar_coordinacion.py, T032), contrasenas (herramientas_neon/asignar_claves.py con getpass, que la siembra
nunca corre), huella_despues (la misma huella de Ambiental que antes) y controles (controles_neon.sql).

Comprobación previa, antes de cualquier paso. Con --rama principal y --aplicar exige --confirmo-principal y, sin
él, termina con 2 antes de conectarse. Lee GUARDIA_DATOS_INVENTADOS, el valor de la API de la rama que llega por
en_windows.py, y se detiene si está en 1, porque la guardia rechazaría los códigos reales de la capacitación (D-10).
Después consulta en pg_constraint si abet.estudiante conserva ck_estudiante_codigo_inventado
(guardia_datos_inventados.sql) y se detiene si la conserva. El informe nombra solo esa variable.

La conexión llega por las variables de libpq (PGHOST, PGDATABASE, PGUSER, PGPASSWORD y las demás) y, para Flyway y el
respaldo, por las NEON_* de flyway.toml, nunca por argumentos. Desde el Windows las pasa en_windows.py. PSQL y
FLYWAY nombran los programas cuando no están en el PATH. Ninguna salida repite el valor de CORREO_COORDINACION,
DESCRIPCION_INSTRUMENTO, PGPASSWORD, NEON_DB_PASSWORD ni RESPALDO_CLAVE, que se ocultan aunque un guion los muestre.
Usa solo la biblioteca estándar, para que corra con el Python 3.14 del Windows sin instalar paquetes.

Códigos de salida. 0 cuando todos los pasos terminan bien, 1 cuando un paso falla, el despliegue espera su
confirmación o la guardia sigue encendida, 2 por un argumento inválido o una variable que falta, antes de conectarse,
y 3 cuando la base no responde a la comprobación previa.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PERIODO = "2026-1"
ASIGNATURA = "5643"
OCULTAS = ("CORREO_COORDINACION", "DESCRIPCION_INSTRUMENTO", "PGPASSWORD", "NEON_DB_PASSWORD", "RESPALDO_CLAVE")
GUARDIA = "ck_estudiante_codigo_inventado"
USO = ("Uso: python -I db/herramientas/sembrar_quimica.py --rama develop|principal [--confirmo-principal] [--aplicar] "
       "[--programacion RUTA] [--desde PASO] [--back-desplegado] [--huella-antes HUELLA] [--respaldo-en CARPETA] "
       "[--pi 6.1] [--solo-comprobar]")
# La huella completa de la fila «HUELLA DE AMBIENTAL», un SHA-256 en hexadecimal.
HUELLA = re.compile(r"[0-9a-f]{64}")
# Tabla que crea V1_14, la última migración de la siembra. Sin ella, V1_12 a V1_14 siguen pendientes.
DE_V1_14 = "SELECT to_regclass('acceso.coordinacion_alcance') IS NOT NULL"


@dataclass(frozen=True)
class Paso:
    """Un paso de la siembra. en_seco y aplicado son su orden, o None si el paso solo se anuncia en ese modo.
    tras_migraciones marca el paso que necesita V1_12 a V1_14 y que en seco solo se anuncia si siguen pendientes."""

    nombre: str
    descripcion: str
    en_seco: tuple[str, ...] | None
    aplicado: tuple[str, ...] | None
    carpeta: str = "."
    tras_migraciones: bool = False


PSQL = ("{psql}", "-X", "-q", "-v", "ON_ERROR_STOP=1")
FLYWAY = ("{flyway}", "-configFiles=flyway.toml", "-environment=neon")
PASOS = (
    Paso("respaldo", "respaldo cifrado de la rama con respaldar_neon.sh", None,
         ("bash", "db/herramientas/respaldar_neon.sh", "{respaldo}")),
    Paso("huella_antes", "huella de Ambiental antes de sembrar", (*PSQL, "-f", "db/plataforma/neon/huella_ambiental.sql"),
         (*PSQL, "-f", "db/plataforma/neon/huella_ambiental.sql")),
    Paso("migraciones", "V1_12 a V1_14 con Flyway", (*FLYWAY, "info"), (*FLYWAY, "migrate", "-target=1.14"), "db"),
    Paso("alcance_ambiental", "alcance de la carrera AMB para las coordinaciones de hoy",
         (*PSQL, "-f", "db/datos/alcance_coordinacion_ambiental.sql"),
         (*PSQL, "-v", "aplicar=1", "-f", "db/datos/alcance_coordinacion_ambiental.sql"), tras_migraciones=True),
    Paso("despliegue", "despliegue del Back con el _ALCANCE nuevo, que hace Jefferson", None, None),
    Paso("plan_quimica", "vigencia de IND-2026 en 2026-1 y plan de 5643",
         (*PSQL, "-v", "pi={pi}", "-f", "db/datos/plan_quimica_2026_1.sql"),
         (*PSQL, "-v", "aplicar=1", "-v", "pi={pi}", "-f", "db/datos/plan_quimica_2026_1.sql"), tras_migraciones=True),
    Paso("programacion", "programación de las secciones de 5643 en 2026-1",
         ("{python}", "-I", "db/herramientas/cargar_programacion.py", "--periodo", PERIODO, "--archivo", "{programacion}"),
         ("{python}", "-I", "db/herramientas/cargar_programacion.py", "--periodo", PERIODO, "--archivo", "{programacion}",
          "--aplicar"), tras_migraciones=True),
    Paso("coordinacion", "cuenta y alcance de la coordinación del curso",
         ("{python}", "-I", "db/herramientas/registrar_coordinacion.py", "--asignatura", ASIGNATURA, "--periodo", PERIODO),
         ("{python}", "-I", "db/herramientas/registrar_coordinacion.py", "--asignatura", ASIGNATURA, "--periodo", PERIODO,
          "--aplicar"), tras_migraciones=True),
    Paso("contrasenas", "contraseñas, que Jefferson asigna con asignar_claves.py y getpass", None, None),
    Paso("huella_despues", "huella de Ambiental después de sembrar",
         (*PSQL, "-f", "db/plataforma/neon/huella_ambiental.sql"), (*PSQL, "-f", "db/plataforma/neon/huella_ambiental.sql")),
    Paso("controles", "consultas de control Q01 a Q14 y Q18 a Q21", (*PSQL, "-f", "db/plataforma/neon/controles_neon.sql"),
         (*PSQL, "-f", "db/plataforma/neon/controles_neon.sql"), tras_migraciones=True),
)
NOMBRES = tuple(paso.nombre for paso in PASOS)


class _Argumentos(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # noqa: ARG002, el mensaje de argparse no se muestra
        raise SystemExit(_falla(USO, 2))


def _falla(mensaje: str, codigo: int) -> int:
    sys.stderr.write(_ocultar(mensaje) + "\n")
    return codigo


def _ocultar(texto: str) -> str:
    """El texto sin el valor de ninguna variable que no debe aparecer en un informe."""
    for nombre in OCULTAS:
        valor = os.environ.get(nombre, "")
        if len(valor) >= 4:
            texto = texto.replace(valor, f"[{nombre} oculto]")
    return texto


def _argumentos(argv: list[str]) -> argparse.Namespace:
    analizador = _Argumentos(add_help=False, allow_abbrev=False)
    analizador.add_argument("--rama", choices=("develop", "principal"), required=True)
    analizador.add_argument("--confirmo-principal", action="store_true")
    analizador.add_argument("--aplicar", action="store_true")
    analizador.add_argument("--programacion")
    analizador.add_argument("--desde", choices=NOMBRES, default=NOMBRES[0])
    analizador.add_argument("--back-desplegado", action="store_true")
    analizador.add_argument("--huella-antes")
    analizador.add_argument("--respaldo-en")
    analizador.add_argument("--pi", default="6.1")
    analizador.add_argument("--solo-comprobar", action="store_true")
    return analizador.parse_args(argv)


def _orden(paso: Paso, aplicar: bool, valores: dict[str, str]) -> list[str] | None:
    plantilla = paso.aplicado if aplicar else paso.en_seco
    return None if plantilla is None else [parte.format(**valores) for parte in plantilla]


def _huella(salida: str) -> str | None:
    """La huella completa de la última línea de huella_ambiental.sql, o None si esa línea no la trae."""
    lineas = salida.strip().splitlines()
    encontrada = HUELLA.search(lineas[-1]) if lineas else None
    return encontrada[0] if encontrada else None


def _migraciones_pendientes(psql: str) -> bool:
    """True si la base todavía no tiene acceso.coordinacion_alcance, que crea V1_14."""
    corrida = subprocess.run([psql, "-X", "-q", "-At", "-v", "ON_ERROR_STOP=1", "-c", DE_V1_14], env=os.environ.copy(),
                             capture_output=True, text=True, check=False)
    return corrida.stdout.strip() != "t"


def _correr(orden: list[str], carpeta: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(orden, cwd=RAIZ / carpeta, env=os.environ.copy(), capture_output=True, text=True, check=False)


def _comprobar(argumentos: argparse.Namespace, psql: str) -> int:
    """Comprobación previa de la guardia en la API y en la base. Devuelve 0 si la siembra puede seguir."""
    guardia = os.environ.get("GUARDIA_DATOS_INVENTADOS")
    if guardia is None:
        return _falla("Falta GUARDIA_DATOS_INVENTADOS, el valor de la API de la rama, que llega por en_windows.py.", 2)
    if guardia.strip() == "1":
        return _falla("La guardia de datos inventados está encendida y rechazaría los códigos de la capacitación.", 1)
    if guardia.strip() != "0":
        return _falla("GUARDIA_DATOS_INVENTADOS debe valer 0 o 1.", 2)
    print("La guardia de datos inventados está apagada en la API (GUARDIA_DATOS_INVENTADOS en 0).")
    consulta = f"SELECT count(*) FROM pg_constraint WHERE conname = '{GUARDIA}'"
    try:
        corrida = subprocess.run([psql, "-X", "-q", "-At", "-v", "ON_ERROR_STOP=1", "-c", consulta], env=os.environ.copy(),
                                 capture_output=True, text=True, check=False)
    except OSError:
        return _falla("No se encontró psql. PSQL nombra su ruta completa.", 3)
    if corrida.returncode != 0 or not corrida.stdout.strip().isdigit():
        return _falla("La base no respondió a la comprobación previa. No se sembró nada.", 3)
    if int(corrida.stdout.strip()) > 0:
        return _falla("La base conserva la guardia de datos inventados.", 1)
    print(f"abet.estudiante no tiene {GUARDIA}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    argumentos = _argumentos(sys.argv[1:] if argv is None else argv)
    if argumentos.rama == "principal" and argumentos.aplicar and not argumentos.confirmo_principal:
        return _falla("La rama principal pide también --confirmo-principal. No se conectó ni escribió nada.", 2)
    pendientes = PASOS[NOMBRES.index(argumentos.desde):]
    if not argumentos.solo_comprobar:
        if any(p.nombre == "programacion" for p in pendientes) and not argumentos.programacion:
            return _falla("Falta --programacion con la ruta del CSV de la programación, fuera del repositorio.", 2)
        if argumentos.aplicar and pendientes[0].nombre == "respaldo" and not argumentos.respaldo_en:
            return _falla("Falta --respaldo-en con la carpeta del respaldo cifrado, fuera del repositorio.", 2)
        nombres = {paso.nombre for paso in pendientes}
        if "huella_despues" in nombres and "huella_antes" not in nombres and argumentos.huella_antes is None:
            return _falla("Falta --huella-antes con la huella de Ambiental que dio el paso «huella_antes» del primer "
                          "tramo. No se conectó ni escribió nada.", 2)
    if argumentos.huella_antes is not None and not HUELLA.fullmatch(argumentos.huella_antes):
        return _falla("--huella-antes lleva las 64 cifras hexadecimales de la huella de Ambiental. No se conectó ni "
                      "escribió nada.", 2)
    psql = os.environ.get("PSQL", "psql")
    codigo = _comprobar(argumentos, psql)
    if codigo or argumentos.solo_comprobar:
        return codigo

    valores = {"psql": psql, "flyway": os.environ.get("FLYWAY", "flyway"), "python": sys.executable,
               "programacion": argumentos.programacion or "", "respaldo": argumentos.respaldo_en or "",
               "pi": argumentos.pi}
    modo = "con --aplicar" if argumentos.aplicar else "en seco"
    print(f"Siembra de Química General en la rama {argumentos.rama}, {modo}, desde el paso «{pendientes[0].nombre}».")
    huella_antes = argumentos.huella_antes
    pendientes_en_seco: bool | None = None
    for paso in pendientes:
        print(f"\n== Paso {paso.nombre} ({paso.descripcion})")
        if paso.nombre == "despliegue":
            if argumentos.aplicar and not argumentos.back_desplegado:
                reanudar = "--desde plan_quimica --back-desplegado"
                if huella_antes is not None:
                    reanudar += f" --huella-antes {huella_antes}"
                print("El paso «despliegue» espera el Back con el _ALCANCE nuevo. Despliéguelo y vuelva a correr con "
                      f"{reanudar}. Los pasos siguientes no corren.")
                return 1
            print("El Back con el _ALCANCE nuevo va desplegado antes del plan de Química.")
            continue
        if paso.nombre == "contrasenas":
            print("Las contraseñas las asigna Jefferson con herramientas_neon/asignar_claves.py desde el Windows, con "
                  "getpass. La siembra no las escribe.")
            continue
        if paso.tras_migraciones and not argumentos.aplicar:
            if pendientes_en_seco is None:
                pendientes_en_seco = _migraciones_pendientes(psql)
            if pendientes_en_seco:
                print(f"El paso «{paso.nombre}» necesita V1_12 a V1_14, que siguen pendientes en esta base, así que en "
                      "seco solo se anuncia.")
                continue
        orden = _orden(paso, argumentos.aplicar, valores)
        if orden is None:
            print(f"El paso «{paso.nombre}» corre solo con --aplicar.")
            continue
        try:
            corrida = _correr(orden, paso.carpeta)
        except OSError:
            print(f"El paso «{paso.nombre}» no encontró su programa. Los pasos siguientes no corren.")
            return 1
        print(_ocultar(corrida.stdout.rstrip()))
        if corrida.stderr.strip():
            print(_ocultar(corrida.stderr.rstrip()))
        if corrida.returncode != 0:
            print(f"El paso «{paso.nombre}» terminó con el código {corrida.returncode}. Los pasos siguientes no corren.")
            return 1
        if paso.nombre in ("huella_antes", "huella_despues") and _huella(corrida.stdout) is None:
            print(f"El paso «{paso.nombre}» no terminó con la huella de Ambiental. Los pasos siguientes no corren.")
            return 1
        if paso.nombre == "huella_antes":
            huella_antes = _huella(corrida.stdout)
            print(f"Huella de Ambiental de antes {huella_antes}.")
        if paso.nombre == "huella_despues":
            if huella_antes is None:
                print("No hay huella de Ambiental de antes para comparar. Los pasos siguientes no corren.")
                return 1
            if _huella(corrida.stdout) != huella_antes:
                print("La huella de Ambiental cambió con la siembra. Los pasos siguientes no corren.")
                return 1
            print("La huella de Ambiental es la misma antes y después de la siembra.")
    print("\nSiembra terminada" + (" con --aplicar." if argumentos.aplicar else " en seco. No se guardó nada."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
