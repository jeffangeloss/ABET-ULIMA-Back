"""Genera desde la tabla maestra un export con el formato de Blackboard por sección (US-74 de la spec 008, T034).

Uso, desde la raíz del repositorio y con la tabla maestra y la salida FUERA de todo repositorio
    uv run python -I scripts/generar_exports_desde_maestra.py --maestra TABLA.xlsx --programacion PROGRAMACION.csv \\
        --salida CARPETA --periodo 2026-1 --asignatura 5643 --pi 6.1 [--fecha 2026-07-15-00-00-00]
    uv run python -I scripts/generar_exports_desde_maestra.py --maestra TABLA.xlsx --salida CARPETA \\
        --periodo 2026-1 --asignatura 5643 --pi 6.1 --ejercicio 3
    uv run python -I scripts/generar_exports_desde_maestra.py --tarjetas TARJETAS.csv --manifiesto MANIFIESTO.json

Los profesores de Química General no calificaron en Blackboard, así que la capacitación de Ingeniería Industrial sube
un export armado desde la tabla maestra conglomerada (decisión A de Jefferson, FR-013 de la spec 008).

1. La tabla maestra es un .xlsx (su primera hoja) o un .csv con las columnas AÑO, CICLO, CÓDIGO DEL CURSO, CURSO,
   CICLO DEL CURSO, SO, PI, PROFESOR, CÓDIGO DEL ESTUDIANTE, SECCIÓN, CALIFICACIÓN y ARCHIVO, con el encabezado en la
   fila 1. El generador lee solo AÑO, CICLO, CÓDIGO DEL CURSO, PI, CÓDIGO DEL ESTUDIANTE, SECCIÓN y CALIFICACIÓN, y
   nunca copia PROFESOR, CURSO ni ARCHIVO. Sin una de esas siete columnas termina con «Falta la columna X de la tabla
   maestra.» y no adivina.
2. Las filas de otro periodo, de otra asignatura o de otro PI se omiten, en ese orden, y el manifiesto las cuenta.
   Una fila defectuosa de lo que se exporta (un código que no tiene 8 cifras, una calificación vacía o que no es un
   entero de 1 a 4, o un estudiante dos veces en la sección o en dos secciones del curso) detiene toda la generación
   con «Fila N. motivo», sin mostrar el código ni la calificación, y no se escribe ningún archivo.
3. El curso de Blackboard de cada sección sale solo del CSV de la programación de la spec 006 (columnas periodo,
   asignatura, seccion, correo y curso_blackboard), que se lee con db/herramientas/cargar_programacion.py. Una sección
   sin fila en la programación detiene el generador con «Fila N. La sección no está en la programación del curso.»,
   con la primera fila de esa sección. Los correos de la programación no se leen más allá de esa revisión ni se
   escriben en ninguna parte.
4. Cada export es un .xlsx de una sola hoja con las columnas «Username» y la del PI, como
   «ABET SO6.1 [Total Pts: 4 Score] |9000061», y nada más. El código va como texto, así que un cero a la izquierda se
   conserva. El archivo se llama gc_CURSO_fullgc_FECHA.xlsx y su hoja gc_CURSO_f, recortada a los 31 caracteres que
   admite Excel, como lo hace Blackboard. Antes de escribir, el generador comprueba con abet_carga que la hoja y el
   nombre declaren el periodo, la asignatura y la sección de la fila. La escritura es la determinista de
   scripts/generar_exports_inventados.py, así que dos corridas con los mismos parámetros dan los mismos bytes, y
   --fecha fija la fecha del nombre (sin --fecha, la del momento).
5. manifiesto.json resume cada export con la sección, el archivo, su huella SHA-256, las filas y el conteo de los
   niveles 1 a 4, más los parámetros y las filas omitidas, sin códigos ni nombres. La salida del proceso dice por
   sección las filas y el conteo por nivel, sin códigos, sin nombres y sin la ruta de la carpeta.
6. La carpeta de salida no puede estar dentro de un repositorio git (código 2, sin escribir nada), porque los
   repositorios son públicos (D-10).
7. --ejercicio N (propuesta) arma N archivos de ejercicio de la única sección de la tabla, que es una sección
   ficticia como la 799, con el curso EJERCICIO_AAAAC_ASIGNATURA_SECCION, los niveles de la tabla y códigos nuevos del
   rango 99 distintos en cada archivo, para que cada profesor suba uno con su propia huella y uq_archivo_origen_sha256
   no confunda dos subidas. No pide la programación.
8. --tarjetas (propuesta) compara el CSV de las tarjetas (columnas seccion y archivo, y las demás se ignoran) con el
   manifiesto y termina con 1 si una tarjeta nombra un archivo que no es el de su sección, con
   «Tarjeta de la fila N. La sección X no lleva el archivo que el manifiesto le da.», sin mostrar correos.

Códigos de salida. 0 si todo sale bien, 1 si la tabla, la programación o las tarjetas se rechazan, y 2 por un
argumento inválido o una carpeta de salida dentro de un repositorio, antes de leer nada.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import io
import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from types import ModuleType

from openpyxl import load_workbook

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    # python -I no pone la raíz del repositorio en sys.path, y abet_carga vive ahí.
    sys.path.insert(0, str(RAIZ))

from abet_carga.validacion import seccion_declarada  # noqa: E402


def _cargar(nombre: str, ruta: Path) -> ModuleType:
    """Módulo cargado por su ruta, porque scripts/ y db/herramientas/ no son paquetes."""
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, ruta)
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


G = _cargar("generar_exports_inventados", RAIZ / "scripts" / "generar_exports_inventados.py")
P = _cargar("cargar_programacion", RAIZ / "db" / "herramientas" / "cargar_programacion.py")

ANIO, CICLO, ASIGNATURA, PI = "AÑO", "CICLO", "CÓDIGO DEL CURSO", "PI"
CODIGO, SECCION, CALIFICACION = "CÓDIGO DEL ESTUDIANTE", "SECCIÓN", "CALIFICACIÓN"
LEIDAS = (ANIO, CICLO, ASIGNATURA, PI, CODIGO, SECCION, CALIFICACION)
LARGO_DE_HOJA = 31
MANIFIESTO = "manifiesto.json"
PERIODO = re.compile(r"[0-9]{4}-[0-9]")
ASIGNATURA_VALIDA = re.compile(r"[0-9]{4}(?:[0-9]{2})?")
PI_VALIDO = re.compile(r"[1-9][0-9]?\.[1-9]")
FECHA = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}")
OCHO_CIFRAS = re.compile(r"[0-9]{8}")

EN_REPOSITORIO = "La carpeta de salida está dentro de un repositorio git. Elija una carpeta fuera de los repositorios."
DETENIDA = "Generación detenida. No se escribió ningún archivo."
NO_SE_LEE = "La tabla maestra no se puede leer."
FUERA_DE_PROGRAMACION = "La sección no está en la programación del curso."
CODIGO_MAL = "El código del estudiante no tiene 8 cifras."
CALIFICACION_VACIA = "La calificación está vacía."
CALIFICACION_MAL = "La calificación no es un entero de 1 a 4."
DOS_VECES = "El estudiante aparece dos veces en la sección."
DOS_SECCIONES = "El estudiante aparece en dos secciones del curso."
SIN_SECCION = "La sección está vacía o no es un número."
SIN_PERIODO = "El año o el ciclo no se pueden leer."
EJERCICIO_DE_UNA_SECCION = "El ejercicio necesita las filas de una sola sección."


class Rechazo(Exception):
    """La entrada se rechaza con sus líneas de informe y el código de salida."""

    def __init__(self, *lineas: str, codigo: int = 1) -> None:
        super().__init__(*lineas)
        self.lineas, self.codigo = list(lineas), codigo


@dataclass
class Fila:
    """Fila de la tabla maestra que entra al export, con su número en el libro (la primera de datos es la 2)."""

    numero: int
    seccion: str
    codigo: str
    nivel: int


@dataclass
class Lectura:
    """Lo que entra al export, por sección en el orden de la tabla, y lo que se omite."""

    por_seccion: dict[str, list[Fila]] = field(default_factory=dict)
    omitidas: dict[str, int] = field(default_factory=lambda: {"periodo": 0, "asignatura": 0, "pi": 0})


# Lectura de la tabla maestra

def _normalizar(encabezado: object) -> str:
    return unicodedata.normalize("NFC", str(encabezado or "")).strip().upper()


def _texto(valor: object) -> str:
    """Valor de una celda como texto sin espacios a los lados. Un decimal sin fracción pasa a sus cifras."""
    if valor is None:
        return ""
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return unicodedata.normalize("NFC", str(valor)).strip()


def _registros(ruta: Path) -> list[list[object]]:
    """Encabezado y filas de la primera hoja de un .xlsx, o de un .csv en UTF-8 con coma o punto y coma."""
    try:
        if ruta.suffix.lower() == ".csv":
            texto = ruta.read_bytes().decode("utf-8-sig")
            primera = texto.split("\n", 1)[0]
            separador = ";" if primera.count(";") > primera.count(",") else ","
            return [list(registro) for registro in csv.reader(io.StringIO(texto, newline=""), delimiter=separador)]
        libro = load_workbook(ruta, read_only=True, data_only=True)
        try:
            return [list(fila) for fila in libro.worksheets[0].iter_rows(values_only=True)]
        finally:
            libro.close()
    except (OSError, UnicodeDecodeError, csv.Error, ValueError, KeyError):
        raise Rechazo(NO_SE_LEE) from None
    except Exception as falla:  # openpyxl lanza InvalidFileException y errores de zip según el archivo.
        if type(falla).__module__.startswith(("openpyxl", "zipfile")):
            raise Rechazo(NO_SE_LEE) from None
        raise


def _nivel(valor: object) -> int | str:
    """Nivel de 1 a 4 de la celda, o el motivo de su rechazo, sin el valor."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return CALIFICACION_VACIA
    if isinstance(valor, bool):
        return CALIFICACION_MAL
    if isinstance(valor, float):
        valor = int(valor) if valor.is_integer() else None
    elif isinstance(valor, str):
        valor = int(valor.strip()) if re.fullmatch(r"[0-9]+", valor.strip()) else None
    return valor if isinstance(valor, int) and 1 <= valor <= 4 else CALIFICACION_MAL


def leer_maestra(ruta: Path, periodo: str, asignatura: str, pi: str) -> Lectura:
    """Filas de la tabla maestra que entran al export, o Rechazo con todas las filas defectuosas, sin sus valores."""
    registros = _registros(ruta)
    encabezado = [_normalizar(celda) for celda in registros[0]] if registros else []
    faltan = [columna for columna in LEIDAS if columna not in encabezado]
    if faltan:
        raise Rechazo(*(f"Falta la columna {columna} de la tabla maestra." for columna in faltan))
    posicion = {columna: encabezado.index(columna) for columna in LEIDAS}
    lectura, errores = Lectura(), []
    vistos: dict[str, tuple[str, int]] = {}
    for numero, registro in enumerate(registros[1:], start=2):
        celdas = {columna: (registro[i] if i < len(registro) else None) for columna, i in posicion.items()}
        if all(_texto(valor) == "" for valor in celdas.values()):
            continue
        anio, ciclo = _texto(celdas[ANIO]), _texto(celdas[CICLO])
        if not (anio.isdigit() and ciclo.isdigit()):
            errores.append(f"Fila {numero}. {SIN_PERIODO}")
            continue
        if f"{int(anio)}-{int(ciclo)}" != periodo:
            lectura.omitidas["periodo"] += 1
            continue
        if _texto(celdas[ASIGNATURA]) != asignatura:
            lectura.omitidas["asignatura"] += 1
            continue
        if _texto(celdas[PI]) != pi:
            lectura.omitidas["pi"] += 1
            continue
        seccion, codigo, nivel = _texto(celdas[SECCION]), _texto(celdas[CODIGO]), _nivel(celdas[CALIFICACION])
        if not seccion.isdigit() or int(seccion) == 0:
            errores.append(f"Fila {numero}. {SIN_SECCION}")
            continue
        seccion = str(int(seccion))
        if not OCHO_CIFRAS.fullmatch(codigo):
            errores.append(f"Fila {numero}. {CODIGO_MAL}")
            continue
        if isinstance(nivel, str):
            errores.append(f"Fila {numero}. {nivel}")
            continue
        if codigo in vistos:
            otra_seccion, otra_fila = vistos[codigo]
            motivo = DOS_VECES if otra_seccion == seccion else DOS_SECCIONES
            # Las dos filas se nombran, la primera aparición y esta, sin el código.
            errores += [f"Fila {otra_fila}. {motivo}", f"Fila {numero}. {motivo}"]
            continue
        vistos[codigo] = (seccion, numero)
        lectura.por_seccion.setdefault(seccion, []).append(Fila(numero, seccion, codigo, nivel))
    if errores:
        raise Rechazo(*sorted(dict.fromkeys(errores), key=lambda linea: int(linea.split(".")[0].split()[1])))
    if not lectura.por_seccion:
        raise Rechazo(_ninguna(lectura, periodo, asignatura, pi))
    return lectura


def _ninguna(lectura: Lectura, periodo: str, asignatura: str, pi: str) -> str:
    """Por qué ninguna fila entra al export, con el primer filtro que las dejó todas fuera."""
    omitidas = lectura.omitidas
    if omitidas["asignatura"] == 0 and omitidas["pi"] == 0:
        return f"Ninguna fila es del periodo {periodo}."
    if omitidas["pi"] == 0:
        return f"Ninguna fila es de la asignatura {asignatura}."
    return f"Ninguna fila es del PI {pi}."


# Programación, exports y manifiesto

def cursos_de_la_programacion(ruta: Path, periodo: str, asignatura: str) -> dict[str, str]:
    """Curso de Blackboard de cada sección del periodo y la asignatura, leído del CSV de la programación."""
    try:
        filas = P.leer(ruta.read_bytes())
    except P.ArchivoRechazado as rechazo:
        raise Rechazo(*(f"Programación. {mensaje}" for mensaje in rechazo.mensajes)) from None
    except OSError:
        raise Rechazo("Programación. El archivo no se puede leer.") from None
    return {str(int(fila.seccion)): fila.curso_blackboard for fila in filas
            if fila.periodo == periodo and fila.asignatura == asignatura and fila.seccion.isdigit()
            and fila.curso_blackboard}


def columna_del_pi(pi: str) -> str:
    so, numero = pi.split(".")
    return f"ABET SO{so}.{numero} [Total Pts: 4 Score] |{G.id_de_blackboard(pi)}"


def _hoja(curso: str) -> str:
    return f"gc_{curso}_f"[:LARGO_DE_HOJA]


def _nombre(curso: str, fecha: str, sufijo: str = "") -> str:
    return f"gc_{curso}_fullgc_{fecha}{sufijo}.xlsx"


def _comprobar_declaracion(curso: str, nombre: str, periodo: str, asignatura: str, seccion: str) -> None:
    """La hoja y el nombre declaran lo mismo que la fila, con la regla del lector de abet_carga."""
    esperada = (periodo, asignatura, seccion)
    for hoja, archivo in ((_hoja(curso), "sin_nombre.xlsx"), (None, nombre)):
        declarada = seccion_declarada(hoja, archivo)
        if declarada is None or (declarada.periodo, declarada.curso_codigo, declarada.seccion_codigo) != esperada:
            raise Rechazo(f"El curso de la sección {seccion} no declara su periodo, su asignatura y su sección.")


@dataclass(frozen=True)
class Export:
    seccion: str
    archivo: str
    contenido: bytes
    niveles: Counter

    def entrada(self, **extra: object) -> dict[str, object]:
        return {"seccion": self.seccion, **extra, "archivo": self.archivo,
                "sha256": hashlib.sha256(self.contenido).hexdigest(), "filas": sum(self.niveles.values()),
                "niveles": {str(nivel): self.niveles.get(nivel, 0) for nivel in (1, 2, 3, 4)}}


def armar(curso: str, nombre: str, pi: str, filas: list[tuple[str, int]], seccion: str) -> Export:
    export = G.Export(_hoja(curso), ("Username", columna_del_pi(pi)), tuple((codigo, nivel) for codigo, nivel in filas))
    return Export(seccion, nombre, bytes(G.a_bytes(export)), Counter(nivel for _, nivel in filas))


def exports_por_seccion(lectura: Lectura, cursos: dict[str, str], argumentos: argparse.Namespace) -> list[Export]:
    faltan = [filas[0].numero for seccion, filas in lectura.por_seccion.items() if seccion not in cursos]
    if faltan:
        raise Rechazo(*(f"Fila {numero}. {FUERA_DE_PROGRAMACION}" for numero in sorted(faltan)))
    exports = []
    for seccion in sorted(lectura.por_seccion, key=int):
        curso, filas = cursos[seccion], lectura.por_seccion[seccion]
        nombre = _nombre(curso, argumentos.fecha)
        _comprobar_declaracion(curso, nombre, argumentos.periodo, argumentos.asignatura, seccion)
        exports.append(armar(curso, nombre, argumentos.pi, [(f.codigo, f.nivel) for f in filas], seccion))
    return exports


def exports_de_ejercicio(lectura: Lectura, argumentos: argparse.Namespace) -> list[Export]:
    if len(lectura.por_seccion) != 1:
        raise Rechazo(EJERCICIO_DE_UNA_SECCION)
    [(seccion, filas)] = lectura.por_seccion.items()
    if len(filas) > 999 or argumentos.ejercicio > 99:
        raise Rechazo("El ejercicio admite hasta 99 archivos de hasta 999 filas.")
    curso = f"EJERCICIO_{argumentos.periodo.replace('-', '')}_{argumentos.asignatura}_{seccion}"
    exports = []
    for numero in range(1, argumentos.ejercicio + 1):
        nombre = _nombre(curso, argumentos.fecha, f"_ejercicio{numero:02d}")
        _comprobar_declaracion(curso, nombre, argumentos.periodo, argumentos.asignatura, seccion)
        # Códigos nuevos del rango 99, 999 + el archivo en dos cifras + la fila en tres, distintos en cada archivo.
        codigos = [f"999{numero:02d}{posicion:03d}" for posicion in range(1, len(filas) + 1)]
        exports.append(armar(curso, nombre, argumentos.pi, list(zip(codigos, (f.nivel for f in filas), strict=True)),
                             seccion))
    return exports


def escribir(salida: Path, exports: list[Export], lectura: Lectura, argumentos: argparse.Namespace) -> None:
    """Escribe los exports y el manifiesto. Todo se armó y se comprobó antes, así que nada queda a medias por datos."""
    salida.mkdir(parents=True, exist_ok=True)
    for export in exports:
        (salida / export.archivo).write_bytes(export.contenido)
    entradas = [export.entrada(**({"ejercicio": i} if argumentos.ejercicio else {}))
                for i, export in enumerate(exports, start=1)]
    manifiesto = {"periodo": argumentos.periodo, "asignatura": argumentos.asignatura, "pi": argumentos.pi,
                  "fecha": argumentos.fecha, "omitidas": lectura.omitidas, "exports": entradas}
    (salida / MANIFIESTO).write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def informe(exports: list[Export], lectura: Lectura) -> list[str]:
    lineas = []
    for export in exports:
        n = export.niveles
        lineas.append(f"Sección {export.seccion}. {sum(n.values())} filas, {n[1]} de nivel 1, {n[2]} de nivel 2, "
                      f"{n[3]} de nivel 3 y {n[4]} de nivel 4.")
    o = lectura.omitidas
    lineas.append(f"Filas omitidas. {o['periodo']} de otro periodo, {o['asignatura']} de otra asignatura y {o['pi']} "
                  "de otro PI.")
    lineas.append(f"{len(exports)} archivos y {MANIFIESTO} escritos.")
    return lineas


# Tarjetas

def comprobar_tarjetas(ruta_tarjetas: Path, ruta_manifiesto: Path) -> list[str]:
    """Líneas del informe de las tarjetas, o Rechazo con cada tarjeta que no nombra el archivo de su sección."""
    try:
        manifiesto = json.loads(ruta_manifiesto.read_text(encoding="utf-8"))
        texto = ruta_tarjetas.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError, ValueError):
        raise Rechazo("Las tarjetas o el manifiesto no se pueden leer.") from None
    archivos = {entrada["seccion"]: entrada["archivo"] for entrada in manifiesto.get("exports", [])}
    registros = list(csv.reader(io.StringIO(texto, newline="")))
    encabezado = [celda.strip().lower() for celda in registros[0]] if registros else []
    if "seccion" not in encabezado or "archivo" not in encabezado:
        raise Rechazo("Las tarjetas necesitan las columnas seccion y archivo.")
    i_seccion, i_archivo = encabezado.index("seccion"), encabezado.index("archivo")
    errores, revisadas = [], 0
    for numero, registro in enumerate(registros[1:], start=2):
        if not any(celda.strip() for celda in registro):
            continue
        revisadas += 1
        seccion = registro[i_seccion].strip() if i_seccion < len(registro) else ""
        archivo = registro[i_archivo].strip() if i_archivo < len(registro) else ""
        if seccion not in archivos:
            errores.append(f"Tarjeta de la fila {numero}. La sección {seccion} no está en el manifiesto.")
        elif archivo != archivos[seccion]:
            errores.append(f"Tarjeta de la fila {numero}. La sección {seccion} no lleva el archivo que el manifiesto le da.")
    if errores:
        raise Rechazo(*errores)
    return [f"{revisadas} de {revisadas} tarjetas nombran el archivo de su sección."]


# Argumentos y principal

def dentro_de_un_repositorio(ruta: Path) -> bool:
    """Si la carpeta o alguna que la contiene tiene .git, como carpeta en un clon o como archivo en un worktree."""
    resuelta = ruta.resolve()
    return any((carpeta / ".git").exists() for carpeta in (resuelta, *resuelta.parents))


class _Argumentos(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # noqa: ARG002 (el mensaje de argparse no se muestra en inglés)
        raise Rechazo("Argumentos inválidos. Lea el uso al comienzo de scripts/generar_exports_desde_maestra.py.",
                      codigo=2)


def argumentos_de(argv: list[str] | None) -> argparse.Namespace:
    analizador = _Argumentos(add_help=False)
    for opcion in ("--maestra", "--programacion", "--salida", "--periodo", "--asignatura", "--pi", "--fecha",
                   "--tarjetas", "--manifiesto"):
        analizador.add_argument(opcion)
    analizador.add_argument("--ejercicio", type=int, default=0)
    argumentos = analizador.parse_args(argv)
    if argumentos.tarjetas is not None:
        if argumentos.manifiesto is None:
            analizador.error("")
        return argumentos
    argumentos.fecha = argumentos.fecha or datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    validos = (argumentos.maestra and argumentos.salida
               and (argumentos.programacion or argumentos.ejercicio > 0) and argumentos.ejercicio >= 0
               and PERIODO.fullmatch(argumentos.periodo or "") and ASIGNATURA_VALIDA.fullmatch(argumentos.asignatura or "")
               and PI_VALIDO.fullmatch(argumentos.pi or "") and FECHA.fullmatch(argumentos.fecha))
    if not validos:
        analizador.error("")
    return argumentos


def principal(argv: list[str] | None = None) -> tuple[int, list[str]]:
    try:
        argumentos = argumentos_de(argv)
        if argumentos.tarjetas is not None:
            return 0, comprobar_tarjetas(Path(argumentos.tarjetas), Path(argumentos.manifiesto))
        salida = Path(argumentos.salida)
        if dentro_de_un_repositorio(salida):
            raise Rechazo(EN_REPOSITORIO, codigo=2)
        lectura = leer_maestra(Path(argumentos.maestra), argumentos.periodo, argumentos.asignatura, argumentos.pi)
        if argumentos.ejercicio:
            exports = exports_de_ejercicio(lectura, argumentos)
        else:
            cursos = cursos_de_la_programacion(Path(argumentos.programacion), argumentos.periodo, argumentos.asignatura)
            exports = exports_por_seccion(lectura, cursos, argumentos)
        escribir(salida, exports, lectura, argumentos)
        return 0, informe(exports, lectura)
    except Rechazo as rechazo:
        cierre = [] if rechazo.codigo == 2 or "tarjetas" in " ".join(rechazo.lineas).lower() else [DETENIDA]
        return rechazo.codigo, [*rechazo.lineas, *cierre]


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    codigo, lineas = principal(argv)
    for linea in lineas:
        print(linea)
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
