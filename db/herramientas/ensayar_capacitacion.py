"""Ensayo de punta a punta de los exports antes de la capacitación (US-84 de la spec 008, T057, FR-030).

Uso, desde la raíz del repositorio, con los exports, la tabla maestra y la carpeta de los R-17 FUERA de todo
repositorio, y la conexión a la base del ensayo en las variables de libpq (PGHOST, PGDATABASE, PGUSER con un rol que
puede cargar, PGPASSWORD y las demás)
    uv run python -I db/herramientas/ensayar_capacitacion.py --exports CARPETA --maestra TABLA.xlsx \\
        --r17 CARPETA_NUEVA --base-del-ensayo HOST/BASE [--reglas R-2026-BORRADOR] [--rol-lectura abet_respaldo] \\
        [--datos-reales]

El ensayo prueba a la vez el generador, el lector, la regla de la meta, el R-17 y el conciliador antes de la sala.

1. --exports es la carpeta que escribe scripts/generar_exports_desde_maestra.py, con su manifiesto.json. Antes de
   conectarse, el ensayo comprueba que el manifiesto no es de un ejercicio, que cada archivo que nombra está en la
   carpeta y que sus bytes tienen la huella SHA-256 del manifiesto. El periodo, la asignatura y el PI salen del
   manifiesto.
2. La base es aparte (J-52), porque uq_archivo_origen_sha256 haría que la subida en la sala devolviera la constancia
   de una carga del ensayo. --base-del-ensayo nombra esa base como HOST/BASE, con el host y el nombre de la base a
   los que llega la conexión, y el ensayo se niega a subir si la conexión llega a otra, porque las variables de
   libpq pueden seguir apuntando a develop, que después de la siembra tiene las secciones y los profesores y ninguna
   carga. También se niega si la base ya tiene cargas de la asignatura en el periodo, y si una sección del
   manifiesto no existe o no tiene un profesor asignado en acceso.docente_seccion. En esos casos no sube ningún
   archivo.
3. Cada export sube con cargar() de la biblioteca abet_carga, como el profesor de su sección (el primero por
   usuario_id si hay más de uno), con el conjunto de reglas de --reglas o de CONJUNTO_REGLAS. La guardia de datos
   inventados queda encendida salvo con --datos-reales. Cada carga PUBLICADA sin filas rechazadas deja su R-17 en
   --r17 con abet_carga.r17.generar().
4. Después corre db/herramientas/conciliar_tabla_maestra.py como proceso aparte, con la tabla maestra, la carpeta de
   los R-17 y el rol de solo lectura de --rol-lectura (abet_respaldo por omisión), con PGPASSWORD_LECTURA como su
   contraseña si existe. Sus líneas van tal cual en el informe del ensayo.
5. El informe dice por sección «Sección N. Carga PUBLICADA con X filas aceptadas y Y rechazadas, y su R-17
   descargado.» o el resultado de la carga, las líneas del conciliador y, al final, «Ensayo sin diferencias. Las N
   secciones salen iguales a la tabla maestra.» o «Ensayo con diferencias. No se da por bueno hasta resolverlas.».
   Nunca trae un código de estudiante, un nombre, un correo ni la ruta de un archivo.
6. La tabla maestra, la carpeta de los exports y la de los R-17 no pueden estar dentro de un repositorio git (código
   2, antes de leer nada y de conectarse), porque los repositorios son públicos (D-10). La carpeta de los R-17 debe
   ser nueva o estar vacía.

Códigos de salida. 0 solo si todas las cargas quedan PUBLICADA sin rechazos y el conciliador dice que todas las
secciones son iguales, 1 ante un manifiesto que se rechaza, una conexión que no llega a la base de
--base-del-ensayo, una base que no sirve para el ensayo, una carga que no
queda limpia o una diferencia, 2 por un argumento inválido, una ruta dentro de un repositorio o una carpeta de R-17
con archivos, antes de leer nada, y 3 si la base no responde. Un código 2 o 3 del conciliador pasa tal cual.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import psycopg

RAIZ = Path(__file__).resolve().parent.parent.parent
if str(RAIZ) not in sys.path:
    # python -I no pone la raíz del repositorio en sys.path, y abet_carga vive ahí.
    sys.path.insert(0, str(RAIZ))

from abet_carga import constancia, r17  # noqa: E402
from abet_carga.carga import Configuracion, ConfiguracionInvalida, Resultado, cargar  # noqa: E402

CONCILIADOR = RAIZ / "db" / "herramientas" / "conciliar_tabla_maestra.py"


def _cargar(nombre: str, ruta: Path) -> ModuleType:
    """Módulo cargado por su ruta, porque scripts/ no es un paquete."""
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, ruta)
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


M = _cargar("generar_exports_desde_maestra", RAIZ / "scripts" / "generar_exports_desde_maestra.py")

ARGUMENTOS_INVALIDOS = "Argumentos inválidos. Lea el uso al comienzo de db/herramientas/ensayar_capacitacion.py."
MAESTRA_EN_REPOSITORIO = "La tabla maestra está dentro de un repositorio git. Use una copia fuera de los repositorios."
EXPORTS_EN_REPOSITORIO = ("La carpeta de los exports está dentro de un repositorio git. Use una copia fuera de los "
                          "repositorios.")
R17_EN_REPOSITORIO = "La carpeta de los R-17 está dentro de un repositorio git. Elija una carpeta fuera de los repositorios."
R17_CON_ARCHIVOS = "La carpeta de los R-17 ya tiene archivos. Elija una carpeta nueva o vacía."
MANIFIESTO_ILEGIBLE = "El manifiesto de los exports no se puede leer."
MANIFIESTO_DE_EJERCICIO = "El manifiesto es de un ejercicio. El ensayo sube los exports por sección."
FUERA_DE_LA_CARPETA = "El manifiesto nombra un archivo fuera de la carpeta de los exports."
FALTA_EL_ARCHIVO = "Falta el archivo que el manifiesto nombra."
OTRA_HUELLA = "El archivo no tiene la huella SHA-256 del manifiesto."
OTRA_BASE = ("La conexión no llega a la base que nombra --base-del-ensayo. Revise PGHOST y PGDATABASE antes de subir "
             "(J-52).")
SIN_SECCION = "La sección no existe en la base del ensayo."
SIN_PROFESOR = "No tiene un profesor asignado en la base del ensayo."
CON_CARGAS = "La base ya tiene cargas de {asignatura} en {periodo}. El ensayo corre en una base aparte, sin cargas del curso (J-52)."
SIN_REGLAS = "El conjunto de reglas {reglas} no existe para la carrera del plan. Revise --reglas."
R17_NO_DISPONIBLE = "La carga quedó PUBLICADA y su R-17 no se pudo generar."
DETENIDO = "Ensayo detenido antes de subir. No se cargó ningún archivo."
SIN_RESPUESTA = "La base no responde. Revise las variables de conexión de libpq."
SIN_DIFERENCIAS = "Ensayo sin diferencias. Las {n} secciones salen iguales a la tabla maestra."
CON_DIFERENCIAS = "Ensayo con diferencias. No se da por bueno hasta resolverlas."

_SECCION = """
SELECT s.seccion_id,
       (SELECT min(d.usuario_id) FROM acceso.docente_seccion d
        JOIN acceso.usuario_autorizado u ON u.usuario_id = d.usuario_id
        WHERE d.seccion_id = s.seccion_id AND u.activo AND u.rol = 'PROFESOR') AS profesor
FROM abet.seccion s
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
WHERE pe.codigo = %s AND a.codigo = %s AND s.numero ~ '^[0-9]+$' AND s.numero::integer = %s
"""

_CARGAS_DEL_CURSO = """
SELECT count(*)
FROM abet.carga c
JOIN abet.seccion s ON s.seccion_id = c.seccion_id
JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
WHERE pe.codigo = %s AND a.codigo = %s
"""


class Rechazo(Exception):
    """El ensayo se detiene con sus líneas de informe y el código de salida."""

    def __init__(self, *lineas: str, codigo: int = 1) -> None:
        super().__init__(*lineas)
        self.lineas, self.codigo = list(lineas), codigo


@dataclass(frozen=True)
class Export:
    """Export del manifiesto con sus bytes, ya comprobados contra su huella."""

    seccion: str
    archivo: str
    contenido: bytes


@dataclass(frozen=True)
class Manifiesto:
    periodo: str
    asignatura: str
    pi: str
    exports: list[Export]


# Manifiesto

def leer_manifiesto(carpeta: Path) -> Manifiesto:
    """Manifiesto del generador con los bytes de cada export, o Rechazo con cada sección que no coincide."""
    try:
        datos = json.loads((carpeta / M.MANIFIESTO).read_text(encoding="utf-8"))
        periodo, asignatura, pi = str(datos["periodo"]), str(datos["asignatura"]), str(datos["pi"])
        entradas = [(str(e["seccion"]), str(e["archivo"]), str(e["sha256"]), "ejercicio" in e) for e in datos["exports"]]
    except (OSError, UnicodeDecodeError, ValueError, KeyError, TypeError):
        raise Rechazo(MANIFIESTO_ILEGIBLE) from None
    validos = (M.PERIODO.fullmatch(periodo) and M.ASIGNATURA_VALIDA.fullmatch(asignatura) and M.PI_VALIDO.fullmatch(pi)
               and entradas and all(seccion.isdigit() for seccion, *_ in entradas)
               and len({seccion for seccion, *_ in entradas}) == len(entradas))
    if not validos:
        raise Rechazo(MANIFIESTO_ILEGIBLE)
    if any(ejercicio for *_, ejercicio in entradas):
        raise Rechazo(MANIFIESTO_DE_EJERCICIO)
    exports, errores = [], []
    for seccion, archivo, sha256, _ in entradas:
        ruta = carpeta / archivo
        if Path(archivo).name != archivo or archivo in ("", ".", ".."):
            errores.append(f"Sección {seccion}. {FUERA_DE_LA_CARPETA}")
        elif not ruta.is_file():
            errores.append(f"Sección {seccion}. {FALTA_EL_ARCHIVO}")
        else:
            contenido = ruta.read_bytes()
            if hashlib.sha256(contenido).hexdigest() != sha256:
                errores.append(f"Sección {seccion}. {OTRA_HUELLA}")
            else:
                exports.append(Export(seccion, archivo, contenido))
    if errores:
        raise Rechazo(*errores)
    return Manifiesto(periodo, asignatura, pi, exports)


# Base del ensayo

def comprobar_destino(conexion: psycopg.Connection, base_del_ensayo: str) -> None:
    """Rechazo si la conexión no llega al HOST/BASE que nombra --base-del-ensayo, sin mostrar ninguno de los dos.

    El nombre de la base no basta, porque una rama hija de Neon conserva el de develop, y el host no basta en un
    clúster con varias bases, así que se comparan los dos (cambio del 2026-11-23 del cierre de la spec 008)."""
    if f"{conexion.info.host}/{conexion.info.dbname}" != base_del_ensayo:
        raise Rechazo(OTRA_BASE)


def destinos(conexion: psycopg.Connection, manifiesto: Manifiesto) -> dict[str, tuple[int, int]]:
    """Sección y profesor de cada export, o Rechazo si la base no sirve para el ensayo. No escribe nada."""
    with conexion.transaction():
        [previas] = conexion.execute(_CARGAS_DEL_CURSO, (manifiesto.periodo, manifiesto.asignatura)).fetchone()
        if previas:
            raise Rechazo(CON_CARGAS.format(asignatura=manifiesto.asignatura, periodo=manifiesto.periodo))
        resultado, errores = {}, []
        for export in manifiesto.exports:
            fila = conexion.execute(_SECCION, (manifiesto.periodo, manifiesto.asignatura, int(export.seccion))).fetchone()
            if fila is None:
                errores.append(f"Sección {export.seccion}. {SIN_SECCION}")
            elif fila[1] is None:
                errores.append(f"Sección {export.seccion}. {SIN_PROFESOR}")
            else:
                resultado[export.seccion] = (fila[0], fila[1])
    if errores:
        raise Rechazo(*errores)
    return resultado


def subir(conexion: psycopg.Connection, manifiesto: Manifiesto, configuracion: Configuracion,
          carpeta_r17: Path) -> tuple[list[str], bool]:
    """Sube cada export como el profesor de su sección y descarga el R-17 de cada carga limpia."""
    lugares = destinos(conexion, manifiesto)
    carpeta_r17.mkdir(parents=True, exist_ok=True)
    lineas, limpias = [], True
    for export in manifiesto.exports:
        seccion_id, profesor = lugares[export.seccion]
        try:
            resultado = cargar(conexion, export.contenido, nombre_archivo=export.archivo, seccion_id=seccion_id,
                               usuario_id=profesor, configuracion=configuracion)
        except ConfiguracionInvalida:
            raise Rechazo(SIN_REGLAS.format(reglas=configuracion.conjunto_reglas)) from None
        if resultado.carga_id is None or resultado.resultado is not Resultado.PUBLICADA:
            lineas.append(f"Sección {export.seccion}. La carga no quedó PUBLICADA ({resultado.resultado.value}).")
            limpias = False
            continue
        cuerpo = constancia.armar(conexion, resultado.carga_id)
        aceptadas, rechazadas = cuerpo["filas_aceptadas"], cuerpo["filas_rechazadas"]
        if rechazadas:
            lineas.append(f"Sección {export.seccion}. Carga PUBLICADA con {aceptadas} filas aceptadas y {rechazadas} "
                          "rechazadas.")
            limpias = False
        try:
            r17.generar(conexion, resultado.carga_id, carpeta_r17)
        except r17.R17NoDisponible:
            lineas.append(f"Sección {export.seccion}. {R17_NO_DISPONIBLE}")
            limpias = False
            continue
        if not rechazadas:
            lineas.append(f"Sección {export.seccion}. Carga PUBLICADA con {aceptadas} filas aceptadas y 0 rechazadas, "
                          "y su R-17 descargado.")
    return lineas, limpias


# Conciliador

def conciliar(maestra: Path, carpeta_r17: Path, manifiesto: Manifiesto, rol_lectura: str,
              datos_reales: bool) -> subprocess.CompletedProcess[str]:
    """El conciliador de US-83 como proceso aparte, con el rol de solo lectura y su propia contraseña."""
    entorno = {clave: valor for clave, valor in os.environ.items()
               if clave not in ("PGPASSWORD", "PGPASSWORD_LECTURA", "PGSERVICE")}
    entorno["PGUSER"] = rol_lectura
    if os.environ.get("PGPASSWORD_LECTURA"):
        entorno["PGPASSWORD"] = os.environ["PGPASSWORD_LECTURA"]
    argumentos = ["--maestra", str(maestra), "--periodo", manifiesto.periodo, "--asignatura", manifiesto.asignatura,
                  "--pi", manifiesto.pi, "--r17", str(carpeta_r17), *(["--datos-reales"] if datos_reales else [])]
    return subprocess.run([sys.executable, "-I", str(CONCILIADOR), *argumentos], env=entorno, capture_output=True,
                          text=True, encoding="utf-8", check=False)


# Argumentos y principal

class _Argumentos(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # noqa: ARG002 (el mensaje de argparse no se muestra en inglés)
        raise Rechazo(ARGUMENTOS_INVALIDOS, codigo=2)


def argumentos_de(argv: list[str] | None) -> argparse.Namespace:
    analizador = _Argumentos(add_help=False)
    for opcion in ("--exports", "--maestra", "--r17", "--reglas", "--base-del-ensayo"):
        analizador.add_argument(opcion)
    analizador.add_argument("--rol-lectura", default="abet_respaldo")
    analizador.add_argument("--datos-reales", action="store_true")
    argumentos = analizador.parse_args(argv)
    argumentos.reglas = (argumentos.reglas or os.environ.get("CONJUNTO_REGLAS", "")).strip()
    if not (argumentos.exports and argumentos.maestra and argumentos.r17 and argumentos.reglas
            and argumentos.rol_lectura and argumentos.base_del_ensayo):
        analizador.error("")
    return argumentos


def _antes_de_leer(maestra: Path, exports: Path, carpeta_r17: Path) -> None:
    """Las negativas que no leen nada ni se conectan (D-10)."""
    for ruta, mensaje in ((maestra, MAESTRA_EN_REPOSITORIO), (exports, EXPORTS_EN_REPOSITORIO),
                          (carpeta_r17, R17_EN_REPOSITORIO)):
        if M.dentro_de_un_repositorio(ruta):
            raise Rechazo(mensaje, codigo=2)
    if carpeta_r17.exists() and (not carpeta_r17.is_dir() or any(carpeta_r17.iterdir())):
        raise Rechazo(R17_CON_ARCHIVOS, codigo=2)


def principal(argv: list[str] | None = None) -> tuple[int, list[str]]:
    lineas: list[str] = []
    try:
        argumentos = argumentos_de(argv)
        maestra, exports, carpeta_r17 = Path(argumentos.maestra), Path(argumentos.exports), Path(argumentos.r17)
        _antes_de_leer(maestra, exports, carpeta_r17)
        try:
            manifiesto = leer_manifiesto(exports)
        except Rechazo as rechazo:
            raise Rechazo(*rechazo.lineas, DETENIDO) from None
        configuracion = Configuracion(argumentos.reglas, guardia_datos_inventados=not argumentos.datos_reales)
        try:
            with psycopg.connect("", autocommit=True) as conexion:
                try:
                    comprobar_destino(conexion, argumentos.base_del_ensayo)
                    lineas, limpias = subir(conexion, manifiesto, configuracion, carpeta_r17)
                except Rechazo as rechazo:
                    detenido = [] if rechazo.lineas[0].startswith("El conjunto") else [DETENIDO]
                    raise Rechazo(*rechazo.lineas, *detenido) from None
        except psycopg.OperationalError:
            raise Rechazo(*lineas, SIN_RESPUESTA, codigo=3) from None
        corrida = conciliar(maestra, carpeta_r17, manifiesto, argumentos.rol_lectura, argumentos.datos_reales)
        lineas += corrida.stdout.splitlines()
        if corrida.returncode in (2, 3):
            return corrida.returncode, lineas
        if corrida.returncode == 0 and limpias:
            return 0, [*lineas, SIN_DIFERENCIAS.format(n=len(manifiesto.exports))]
        return 1, [*lineas, CON_DIFERENCIAS]
    except Rechazo as rechazo:
        return rechazo.codigo, rechazo.lineas


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    codigo, lineas = principal(argv)
    for linea in lineas:
        print(linea)
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
