"""Carga la programación docente del ciclo desde el archivo de la carrera (spec 006, US-55 a US-57, J-42).

Lee el CSV de la programación docente post-matrícula, revisa la forma de cada fila antes de conectarse (FR-003) y
entrega todas las filas a psql 18, que corre cargar_programacion.sql en una sola transacción. El SQL revisa lo
que solo sabe la base (FR-004), escribe con INSERT y ON CONFLICT DO NOTHING en abet.seccion,
acceso.usuario_autorizado y acceso.docente_seccion, completa un curso de Blackboard nulo y arma los avisos. Sin
--aplicar termina con ROLLBACK, así que la corrida en seco informa exactamente lo que la corrida real escribiría
(FR-006). Nunca borra, nunca cambia rol ni activo y no toca acceso.credencial (FR-005).

    python -I db/herramientas/cargar_programacion.py --periodo 2026-2 --archivo RUTA [--aplicar]

La conexión llega por las variables de libpq que psql lee solo (PGHOST, PGDATABASE, PGUSER, PGPASSWORD,
PGSSLMODE y las demás), nunca por argumentos (FR-010). PSQL nombra el programa psql cuando no está en el PATH,
como en el Windows de Jefferson. El guion usa solo la biblioteca estándar de Python 3.12, para que corra con el
Python 3.14 del Windows sin instalar paquetes (FR-001 y AD-01).

Desde la spec 010 (US-96), el archivo admite una columna opcional nombre con el nombre del profesor. El guion lo
normaliza a NFC, sin espacios a los lados ni dobles, y le exige la forma de ck_usuario_autorizado_nombre antes de
conectarse (FR-004 de la spec 010). El SQL lo guarda junto al correo nuevo y completa solo el nombre nulo de un
profesor que ya existe, sin cambiar uno guardado, su rol ni su estado, y nunca lo escribe en el informe (FR-005 y FR-006).

Códigos de salida (FR-008). 0 cuando la corrida en seco o la escritura salen bien, 1 cuando el archivo se
rechaza, 2 por un argumento inválido, antes de leer el archivo y de conectarse, y 3 cuando psql falta o no es de
la 18, cuando la base no responde o cuando rechaza la escritura.

El archivo real trae correos de profesores y, desde la spec 010, sus nombres, que son datos personales. El guion se
niega a leer un archivo dentro de un repositorio de git (FR-009), lee solo las columnas de FR-002 y el nombre y no
copia el archivo ni lo escribe en ningún registro. El informe solo muestra el número de fila, la asignatura, la sección, el correo y, en un
rechazo, el valor de la celda que lo causa, y el error de psql nunca se reenvía tal cual, porque su DETAIL
repetiría los valores de la fila.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

SQL = Path(__file__).with_name("cargar_programacion.sql")
USO = "Uso: python -I db/herramientas/cargar_programacion.py --periodo 2026-2 --archivo RUTA [--aplicar]"
OBLIGATORIAS = ("periodo", "asignatura", "seccion", "correo")
CURSO = "curso_blackboard"
NOMBRE = "nombre"
# Las formas de FR-003, con las restricciones de la base que copian.
PERIODO = re.compile(r"[0-9]{4}-[0-9]")
ASIGNATURA = re.compile(r"[0-9]{4}(?:[0-9]{2})?")  # ck_asignatura_codigo
SECCION = re.compile(r"[1-9][0-9]{0,4}")  # ck_seccion_numero
CORREO = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")  # ck_usuario_autorizado_correo
LARGO_CORREO = 254  # acceso.usuario_autorizado.correo varchar(254)
LARGO_CURSO = 100  # abet.seccion.curso_blackboard varchar(100)
LARGO_NOMBRE = 120  # acceso.usuario_autorizado.nombre varchar(120)
# Lo que ck_usuario_autorizado_nombre no admite, además de los caracteres invisibles y de control: la arroba, la coma
# (que separa a los profesores en D10 del R-17) y los dígitos ASCII.
NOMBRE_PROHIBIDO = re.compile(r"[@,0-9]")
NOMBRE_INVALIDO = "El nombre no es válido."
NOMBRE_DISTINTO = "El correo trae otro nombre en otra fila."
FALTA = {"periodo": "Falta el periodo.", "asignatura": "Falta la asignatura.", "seccion": "Falta la sección.",
         "correo": "Falta el correo."}

RECHAZADO = "Archivo rechazado. Nada se escribió."
EN_SECO = "Corrida en seco. Nada se escribió."
GUARDADO = "Cambios guardados."
SIN_CAMBIOS = "Sin cambios."
CONTRASENA = "Los usuarios nuevos no tienen contraseña. Asígnela con asignar_claves.py o con el código por correo."
BASE_RECHAZA = "La base rechazó la escritura y no guardó nada."
BASE_NO_RESPONDE = "La base no responde y no se guardó nada."
# Con --aplicar, la conexión pudo cortarse mientras viajaba el COMMIT o justo después, antes de FIN GUARDADO.
BASE_NO_RESPONDE_AL_APLICAR = "La base no responde y no se sabe si guardó los cambios. Una corrida en seco lo muestra."
# Las categorías Unicode de los caracteres que no se ven, como U+200B, U+FEFF, U+2060 y U+00AD (Cf), y de los
# de control, como el salto de línea de Alt+Enter en Excel (Cc). Llegan al copiar una celda desde Outlook o una
# web y pasan el patrón de ck_usuario_autorizado_correo, así que el correo no sería el que escribe el profesor.
INVISIBLES = ("Cc", "Cf")


class ArchivoRechazado(Exception):
    """El archivo entero no se puede leer, con sus mensajes. El guion termina con código 1 sin conectarse."""

    def __init__(self, *mensajes: str) -> None:
        super().__init__(*mensajes)
        self.mensajes = list(mensajes)


class ArgumentoInvalido(Exception):
    """Un argumento inválido, con su mensaje. El guion termina con código 2 sin leer el archivo."""


@dataclass(frozen=True)
class FilaLeida:
    """Una fila de datos del archivo, con sus celdas sin espacios a los lados y el correo normalizado."""

    fila: int
    periodo: str
    asignatura: str
    seccion: str
    correo: str
    curso_blackboard: str | None
    nombre: str | None = None


class Lectura(list):
    """Filas leídas del archivo, y si el archivo trae la columna nombre aunque todas sus celdas estén vacías."""

    con_nombre: bool = False


def normalizar_nombre(celda: str) -> str | None:
    """Nombre en NFC, sin espacios a los lados y con un solo espacio entre palabras, o None si la celda no trae nombre.

    Solo se tocan los espacios, así que un salto de línea o un tabulador sobrevive y la revisión de forma rechaza el
    nombre en lugar de esconder el error (FR-004 de la spec 010).
    """
    nombre = re.sub(" +", " ", unicodedata.normalize("NFC", celda)).strip(" ")
    return nombre or None


def nombre_valido(nombre: str) -> bool:
    """Si el nombre normalizado cumple lo que exige ck_usuario_autorizado_nombre (FR-001 de la spec 010)."""
    return (len(nombre) <= LARGO_NOMBRE and not _con_invisibles(nombre) and not NOMBRE_PROHIBIDO.search(nombre)
            and nombre == normalizar_nombre(nombre))


def normalizar_correo(correo: str) -> str:
    """Correo sin espacios a los lados y en minúscula, igual que app.sesion.normalizar_correo()."""
    return correo.strip().lower()


def leer(datos: bytes) -> Lectura:
    """Filas de datos del CSV, con BOM de UTF-8 o sin ella. Lanza ArchivoRechazado si el archivo no se puede leer.

    La fila 1 es la de los encabezados, así que la primera fila de datos es la 2, y una línea vacía cuenta su
    número aunque se salte, como en una hoja de cálculo. Solo se leen las columnas de FR-002 y, desde la spec 010, la
    columna opcional nombre, y las demás se descartan sin guardar sus valores. La celda del nombre se lee sin quitar los
    saltos de línea de sus extremos, para que la revisión de forma los vea.
    """
    try:
        texto = datos.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ArchivoRechazado("El archivo no está en UTF-8.") from None
    try:
        registros = list(csv.reader(io.StringIO(texto, newline="")))
    except csv.Error:
        raise ArchivoRechazado("El archivo no se puede leer como CSV.") from None
    encabezados = [celda.strip().lower() for celda in registros[0]] if registros else []
    faltan = [columna for columna in OBLIGATORIAS if columna not in encabezados]
    if faltan:
        raise ArchivoRechazado(*(f"Falta la columna {columna}." for columna in faltan))
    posicion = {columna: encabezados.index(columna) for columna in (*OBLIGATORIAS, CURSO) if columna in encabezados}
    columna_nombre = encabezados.index(NOMBRE) if NOMBRE in encabezados else None
    filas = Lectura()
    filas.con_nombre = columna_nombre is not None
    for numero, registro in enumerate(registros[1:], start=2):
        celdas = {columna: (registro[i].strip() if i < len(registro) else "") for columna, i in posicion.items()}
        crudo = registro[columna_nombre] if columna_nombre is not None and columna_nombre < len(registro) else ""
        if not any(celdas.values()) and not crudo.strip():
            continue
        filas.append(FilaLeida(numero, celdas["periodo"], celdas["asignatura"], celdas["seccion"],
                               normalizar_correo(celdas["correo"]), celdas.get(CURSO) or None, normalizar_nombre(crudo)))
    if not filas:
        raise ArchivoRechazado("El archivo no trae filas.")
    return filas


def _con_invisibles(texto: str) -> bool:
    return any(unicodedata.category(caracter) in INVISIBLES for caracter in texto)


def _forma(fila: FilaLeida, periodo: str) -> str | None:
    """Primer motivo de forma de la fila o None si la fila tiene la forma de FR-003.

    Las columnas se revisan en el orden de FR-002, periodo, asignatura, sección, correo y curso, y en cada una
    primero la celda vacía y después su forma, así que el motivo de una fila no depende del orden de las columnas
    del archivo. Un correo o un curso con un carácter invisible o de control se rechaza sin repetir la celda, que
    partiría la línea del informe o mostraría un valor que parece válido (propuesta de la Clarification «Session
    2026-11-22» de spec.md).
    """
    correo_invisible = _con_invisibles(fila.correo)
    revisiones = (
        ("periodo", fila.periodo == periodo, f"El periodo {fila.periodo} no es el de la corrida, {periodo}."),
        ("asignatura", ASIGNATURA.fullmatch(fila.asignatura), f"El código de asignatura {fila.asignatura} no es válido."),
        ("seccion", SECCION.fullmatch(fila.seccion), f"El número de sección {fila.seccion} no es válido."),
        ("correo", not correo_invisible and len(fila.correo) <= LARGO_CORREO and CORREO.fullmatch(fila.correo),
         "El correo trae un carácter invisible o de control." if correo_invisible
         else f"El correo {fila.correo} no es válido."),
    )
    for columna, valida, motivo in revisiones:
        if not getattr(fila, columna):
            return FALTA[columna]
        if not valida:
            return motivo
    if fila.curso_blackboard is not None and _con_invisibles(fila.curso_blackboard):
        return "El curso de Blackboard trae un carácter invisible o de control."
    if fila.curso_blackboard is not None and len(fila.curso_blackboard) > LARGO_CURSO:
        return f"El curso de Blackboard tiene más de {LARGO_CURSO} caracteres."
    if fila.nombre is not None and not nombre_valido(fila.nombre):
        return NOMBRE_INVALIDO
    return None


def revisar(filas: list[FilaLeida], periodo: str) -> dict[int, str]:
    """Mensaje de cada fila que falla la forma de FR-003, por número de fila, con un solo motivo por fila.

    Las revisiones entre filas solo miran las filas sin falla propia. Un curso de Blackboard no pertenece a dos
    secciones, y una sección no trae dos cursos distintos. Una celda de curso vacía no cuenta como un curso
    distinto, así que dos profesores de la misma sección pueden traer el curso en una sola de sus filas. Desde la
    spec 010, un correo tampoco trae dos nombres distintos, y una celda de nombre vacía no cuenta como otro nombre.
    """
    errores: dict[int, str] = {}
    duenos: dict[str, tuple[str, str]] = {}
    cursos: dict[tuple[str, str], tuple[str, int]] = {}
    nombres: dict[str, str] = {}
    for fila in filas:
        motivo = _forma(fila, periodo)
        seccion = (fila.asignatura, fila.seccion)
        curso = fila.curso_blackboard
        if motivo is None and curso is not None:
            otra = duenos.get(curso)
            propio = cursos.get(seccion)
            if otra is not None and otra != seccion:
                motivo = f"El curso de Blackboard {curso} ya es de la sección {otra[1]} de {otra[0]}."
            elif propio is not None and propio[0] != curso:
                motivo = f"La sección {fila.seccion} de {fila.asignatura} trae otro curso de Blackboard en la fila {propio[1]}."
            else:
                duenos.setdefault(curso, seccion)
                cursos.setdefault(seccion, (curso, fila.fila))
        if motivo is None and fila.nombre is not None:
            if nombres.setdefault(fila.correo, fila.nombre) != fila.nombre:
                motivo = NOMBRE_DISTINTO
        if motivo is not None:
            errores[fila.fila] = f"Fila {fila.fila}. {motivo}"
    return errores


def dentro_de_un_repositorio(ruta: Path) -> bool:
    """Si alguna carpeta que contiene la ruta tiene .git, como carpeta en un clon o como archivo en un worktree."""
    return any((carpeta / ".git").exists() for carpeta in ruta.resolve().parents)


class _Argumentos(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # noqa: ARG002, el mensaje de argparse no se muestra
        raise ArgumentoInvalido(USO)


def _argumentos(argv: list[str] | None) -> tuple[str, Path, bool]:
    # Sin abreviaturas, porque --aplicar es la única llave entre la corrida en seco y la escritura, y argparse
    # aceptaría --ap o --apli como --aplicar.
    analizador = _Argumentos(add_help=False, allow_abbrev=False)
    analizador.add_argument("--periodo")
    analizador.add_argument("--archivo")
    analizador.add_argument("--aplicar", action="store_true")
    leidos = analizador.parse_args(argv)
    if not leidos.periodo:
        raise ArgumentoInvalido("Falta el periodo, por ejemplo --periodo 2026-2.")
    if not PERIODO.fullmatch(leidos.periodo):
        raise ArgumentoInvalido("El periodo no tiene la forma AAAA-C.")
    if not leidos.archivo:
        raise ArgumentoInvalido("Falta el archivo, por ejemplo --archivo RUTA.")
    archivo = Path(leidos.archivo)
    if not archivo.is_file():
        raise ArgumentoInvalido("No se encuentra el archivo de la programación.")
    if dentro_de_un_repositorio(archivo):
        raise ArgumentoInvalido("El archivo de la programación debe estar fuera del repositorio.")
    return leidos.periodo, archivo, leidos.aplicar


def _para_psql(filas: list[FilaLeida], errores: dict[int, str]) -> bytes:
    """Filas en CSV para \\copy, con su número y la marca de falla de forma. Una fila con falla va sin sus valores."""
    salida = io.StringIO(newline="")
    escritor = csv.writer(salida, lineterminator="\n")
    for fila in filas:
        if fila.fila in errores:
            escritor.writerow([fila.fila, "t", "", "", "", "", ""])
        else:
            escritor.writerow([fila.fila, "f", fila.asignatura, fila.seccion, fila.correo, fila.curso_blackboard or "",
                               fila.nombre or ""])
    return salida.getvalue().encode("utf-8")


def _psql() -> str:
    return os.environ.get("PSQL") or "psql"


def _comprobar_psql() -> str | None:
    """Mensaje si psql falta o no es de PostgreSQL 18, la versión de Neon (FR-001), o None si sirve."""
    try:
        version = subprocess.run([_psql(), "--version"], capture_output=True, check=False, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return "No se encuentra psql."
    if not re.search(rb"\s18\.[0-9]", version.stdout):
        return "psql no es de PostgreSQL 18."
    return None


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _aviso(registro: list[object]) -> str:
    tipo, *v = registro[1:]
    plantillas = {
        "COORDINADOR": "Aviso. {0} es COORDINADOR y no podrá subir ni declarar en la sección {1} de {2}.",
        "BAJA": "Aviso. {0} está dado de baja y no verá la sección {1} de {2}.",
        "SIN_PLAN": "Aviso. La asignatura {0} no tiene plan de medición en {1}, así que su sección {2} no podrá recibir exports.",
        "FUERA_DEL_PLAN": ("Aviso. La asignatura {0} no está en el plan de estudios vigente en {1}, así que la"
                           " coordinación no verá su sección {2}."),
        "ASIGNACION_AUSENTE": "Aviso. La sección {0} de {1} tiene en la base a {2} y el archivo no la trae.",
        "OTRO_NOMBRE": "Aviso. {0} ya tiene otro nombre en la base y no se cambia.",
    }
    if tipo == "SECCION_AUSENTE":
        numero, asignatura, asignaciones = v
        cuantas = _plural(int(asignaciones), "asignación", "asignaciones")
        return f"Aviso. La sección {numero} de {asignatura} está en la base con {cuantas} y el archivo no la trae."
    return plantillas[str(tipo)].format(*v)


def _error_de_la_base(registro: list[object]) -> tuple[int, str]:
    fila, tipo, *v = registro[1:]
    mensajes = {
        "ASIGNATURA": "La asignatura {0} no existe en el catálogo.",
        "CURSO_DE_OTRA": "El curso de Blackboard {0} ya es de la sección {1} de {2}.",
        "OTRO_CURSO": "La sección {0} de {1} ya tiene otro curso de Blackboard en la base.",
    }
    return int(fila), f"Fila {fila}. {mensajes[str(tipo)].format(*v)}"


def _sqlstate(stderr: bytes) -> str | None:
    """SQLSTATE del error de psql, que \\set VERBOSITY sqlstate deja sin el texto ni el DETAIL con valores."""
    coincide = re.search(rb"ERROR:\s+([0-9A-Z]{5})\b", stderr)
    return coincide.group(1).decode("ascii") if coincide else None


def _correr(periodo: str, aplicar: bool, filas: list[FilaLeida], errores: dict[int, str],
            con_nombre: bool = False) -> tuple[int, list[str]]:
    falla = _comprobar_psql()
    if falla is not None:
        return 3, [falla]
    # Con -w, psql nunca pide la contraseña. Sin terminal, la tomaría de la primera línea del CSV que le llega
    # por la entrada estándar, así que un PGPASSWORD ausente falla de inmediato con el código 2 de psql.
    orden = [_psql(), "-X", "-w", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1", "-v", f"periodo={periodo}",
             "-v", f"aplicar={1 if aplicar else 0}", "-v", f"con_nombre={1 if con_nombre else 0}", "-f", str(SQL)]
    # Los mensajes de psql en inglés y el texto en UTF-8 en cualquier sistema, también en el Windows de Jefferson.
    entorno = {**os.environ, "PGCLIENTENCODING": "UTF8", "LC_MESSAGES": "C", "PGAPPNAME": "cargar_programacion"}
    try:
        corrida = subprocess.run(orden, input=_para_psql(filas, errores), capture_output=True, env=entorno,
                                 check=False)
    except OSError:
        return 3, ["No se encuentra psql."]
    registros = []
    for linea in corrida.stdout.decode("utf-8", errors="replace").splitlines():
        if linea.startswith("["):
            registros.append(json.loads(linea))
    fin = next((r[1] for r in registros if r[0] == "FIN"), None)
    if corrida.returncode != 0 or fin is None:
        estado = _sqlstate(corrida.stderr)
        if estado is not None:
            print(f"SQLSTATE {estado}", file=sys.stderr)
        # psql termina con 2 cuando no alcanza la base o la conexión se corta (EXIT_BADCONN). Con --aplicar el
        # corte pudo llegar después del COMMIT, así que el informe no afirma que nada se guardó.
        if corrida.returncode == 2:
            return 3, [BASE_NO_RESPONDE_AL_APLICAR if aplicar else BASE_NO_RESPONDE]
        return 3, [BASE_RECHAZA]
    if fin == "RECHAZADO":
        de_la_base = dict(_error_de_la_base(r) for r in registros if r[0] == "E")
        todos = {**de_la_base, **errores}
        lineas = [f"El periodo {r[1]} no existe en la base." for r in registros if r[0] == "P"]
        return 1, [*lineas, *(todos[fila] for fila in sorted(todos)), RECHAZADO]
    [resumen] = [r for r in registros if r[0] == "R"]
    secciones, usuarios, asignaciones, cursos, nombres = (int(n) for n in resumen[1:6])
    # Con la columna nombre, el resumen suma un cuarto término. Sin ella, es el de la spec 006 (FR-006 de la spec 010).
    if con_nombre:
        del_archivo = (
            f"Resumen. {_plural(secciones, 'sección nueva', 'secciones nuevas')}, "
            f"{_plural(usuarios, 'usuario nuevo', 'usuarios nuevos')}, "
            f"{_plural(asignaciones, 'asignación nueva', 'asignaciones nuevas')} y "
            f"{_plural(nombres, 'nombre completado', 'nombres completados')}.")
    else:
        del_archivo = (
            f"Resumen. {_plural(secciones, 'sección nueva', 'secciones nuevas')}, "
            f"{_plural(usuarios, 'usuario nuevo', 'usuarios nuevos')} y "
            f"{_plural(asignaciones, 'asignación nueva', 'asignaciones nuevas')}.")
    lineas = [del_archivo, *(_aviso(r) for r in registros if r[0] == "A")]
    if usuarios:
        lineas.append(CONTRASENA)
    if fin == "SECO":
        lineas.append(EN_SECO)
    else:
        # El UPDATE del curso nulo también escribe, así que con cursos completados la corrida no cierra con
        # «Sin cambios.» aunque las tres cifras del resumen sean 0 (duda de FR-007 en la Clarification «Session
        # 2026-11-22» de spec.md).
        lineas.append(GUARDADO if secciones or usuarios or asignaciones or cursos or nombres else SIN_CAMBIOS)
    return 0, lineas


def main(argv: list[str] | None = None) -> int:
    try:
        periodo, archivo, aplicar = _argumentos(argv)
    except ArgumentoInvalido as error:
        print(error)
        return 2
    try:
        try:
            datos = archivo.read_bytes()
        except OSError:
            # Por ejemplo, el PermissionError del Windows cuando Excel tiene abierto el CSV.
            raise ArchivoRechazado("El archivo no se puede abrir.") from None
        filas = leer(datos)
    except ArchivoRechazado as rechazo:
        for mensaje in [*rechazo.mensajes, RECHAZADO]:
            print(mensaje)
        return 1
    errores = revisar(filas, periodo)
    # Un nombre inválido o distinto rechaza el archivo antes de conectarse (FR-004 de la spec 010). Los demás errores de
    # forma siguen viajando a la base, que suma los que solo ella ve.
    if any(mensaje.endswith((NOMBRE_INVALIDO, NOMBRE_DISTINTO)) for mensaje in errores.values()):
        for fila in sorted(errores):
            print(errores[fila])
        print(RECHAZADO)
        return 1
    codigo, lineas = _correr(periodo, aplicar, filas, errores, filas.con_nombre)
    for linea in lineas:
        print(linea)
    return codigo


if __name__ == "__main__":
    # Con python -I, Python no lee PYTHONUTF8, y en el Windows escribiría en cp1252 hacia una tubería.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
