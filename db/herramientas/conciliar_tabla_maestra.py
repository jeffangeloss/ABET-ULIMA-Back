"""Conciliación de la base y los R-17 del sistema con la tabla maestra (US-83 de la spec 008, T037).

Uso, desde la raíz del repositorio, con la tabla maestra y la carpeta de los R-17 FUERA de todo repositorio y la
conexión en las variables de libpq (PGHOST, PGDATABASE, PGUSER=abet_respaldo, PGPASSWORD y las demás)
    uv run python -I db/herramientas/conciliar_tabla_maestra.py --maestra TABLA.xlsx --periodo 2026-1 \\
        --asignatura 5643 --pi 6.1 [--r17 CARPETA] [--datos-reales] [--curso]

La tabla maestra, que Stefanny Montaño verificó igual alumno por alumno a los R-17 que llenó cada profesor, es el
oráculo. El conciliador compara con ella, por sección, lo que el sistema mide y los R-17 que genera.

1. La tabla maestra es un .xlsx (su primera hoja) o un .csv con las columnas de
   scripts/generar_exports_desde_maestra.py, del que reutiliza la lectura. Lee solo AÑO, CICLO, CÓDIGO DEL CURSO, PI,
   CÓDIGO DEL ESTUDIANTE, SECCIÓN y CALIFICACIÓN, y nunca compara PROFESOR, ARCHIVO ni ESTADO DE EVIDENCIA, porque
   abet.v_tabla_maestra_pi deja PROFESOR nulo. Las filas de otro periodo o de otra asignatura se omiten. Una fila
   defectuosa (una sección que no es un número, un código que no tiene 8 cifras, una calificación que no es un entero
   de 1 a 4 o un estudiante dos veces en el mismo PI) detiene la conciliación con «Fila N. motivo», sin el valor.
2. Sin --datos-reales, cada código debe ser del rango inventado 99, y una fila con otro código se rechaza por su
   número. --datos-reales (propuesta) acepta cualquier código de 8 cifras, como los de la tabla maestra real.
3. La base se lee en una sola transacción READ ONLY, con abet_respaldo, el rol de solo lectura del respaldo (FR-018).
   Las filas salen de abet.v_tabla_maestra_pi, que lee solo las cargas PUBLICADA, y las cifras de
   abet.v_r17_por_pi. El conciliador no escribe nunca y deshace la transacción al terminar.
4. Por sección compara, en el PI de --pi, los códigos y los niveles de la tabla y del sistema, el conteo por nivel y el
   logro como cociente x de n (estudiantes con nivel 3 o 4 entre los calificados) y como porcentaje con un decimal,
   redondeado como ROUND de PostgreSQL. En los demás PI de la sección cuenta las filas de la tabla y del sistema y
   nombra la diferencia con D-48, la decisión abierta sobre el PI medido.
5. Con --r17, lee cada R-17 de la carpeta, reconoce su sección por D8, D11 e I11 y compara M24 y M25 con el conteo de
   la tabla, M26 con el cociente, E24 con el porcentaje con un decimal y la tabla desde la fila 43 con los códigos y
   niveles de la tabla maestra (plantillas/README.md).
6. El informe dice por sección «Sección N. Igual en X de X estudiantes, en el conteo por nivel y en el porcentaje.» o
   cada diferencia por su tipo, y termina con «N de M secciones iguales.». Nunca trae un código, un nombre, el valor
   de una celda ni la ruta de un archivo.
7. La tabla maestra y la carpeta de los R-17 no pueden estar dentro de un repositorio git (código 2, antes de leer
   nada y de conectarse), porque los repositorios son públicos (D-10).

8. Con --curso (US-94 de la spec 009, propuesta) compara además, en el PI de --pi, el curso y el promedio de cada sección con
   lo que da el sistema, que lee con la misma consulta de la ruta 20, abet_carga.resultados.resumen_del_curso(), en la misma
   transacción READ ONLY. Del curso compara los alumnos con el nivel esperado o más, el porcentaje, el promedio de calificación
   y las secciones en la meta, que la tabla maestra cuenta con la meta provisional de 80 % de D-56 sobre el porcentaje ya
   redondeado. El porcentaje y el promedio de la tabla se redondean como ROUND(numeric) de PostgreSQL, a uno y a dos
   decimales. Cada sección con carga publicada suma una línea «Con promedio igual.» o «Distinta en el promedio y en el
   porcentaje.», y el curso, «Curso igual en ...» o «Curso distinto en ...». El informe dice solo «igual» o «distinto», sin
   códigos, calificaciones ni cifras de promedio o de porcentaje. Sin --curso el informe es el de antes.

Códigos de salida. 0 si todas las secciones son iguales, 1 ante una diferencia o una tabla maestra que se rechaza, 2
por un argumento inválido o un archivo dentro de un repositorio, antes de leer nada, y 3 si la base no responde
(propuesta, cambio del 2026-11-23 en spec.md).
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import Counter
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
from openpyxl import load_workbook

RAIZ = Path(__file__).resolve().parent.parent.parent


def _cargar(nombre: str, ruta: Path) -> ModuleType:
    """Módulo cargado por su ruta, porque scripts/ no es un paquete."""
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, ruta)
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


M = _cargar("generar_exports_desde_maestra", RAIZ / "scripts" / "generar_exports_desde_maestra.py")
# La consulta de la ruta 20, que --curso corre en la transacción de solo lectura de la conciliación. Se carga por su ruta
# porque este guion corre con python -I y desde cualquier carpeta, y abet_carga/resultados.py solo importa psycopg.
RESULTADOS = _cargar("abet_carga_resultados", RAIZ / "abet_carga" / "resultados.py")

LOGRO_DEL_R17_A_MANO = 3
HOJA_DEL_R17 = "Cursos de Carrera"
PRIMERA_FILA_DE_LA_TABLA = 43
FILAS_DEL_BLOQUE_II = (24, 25, 26)
UN_DECIMAL = Decimal("0.1")
DOS_DECIMALES = Decimal("0.01")
# La meta provisional de la sección en la meta (D-56), con la que la tabla maestra cuenta las secciones en la meta del curso.
META_DEL_CURSO = Decimal(80)
TOLERANCIA = 1e-9

MAESTRA_EN_REPOSITORIO = "La tabla maestra está dentro de un repositorio git. Use una copia fuera de los repositorios."
R17_EN_REPOSITORIO = "La carpeta de los R-17 está dentro de un repositorio git. Use una carpeta fuera de los repositorios."
DETENIDA = "Conciliación detenida. La tabla maestra tiene filas que no se pueden comparar."
SIN_RESPUESTA = "La base no responde. Revise las variables de conexión de libpq."
NO_ES_99 = "El código del estudiante no es del rango inventado 99. Con datos reales, use --datos-reales."
REPETIDO = "El estudiante aparece dos veces en el mismo PI de la sección."
R17_ILEGIBLE = "Un archivo de la carpeta de los R-17 no se puede leer."

_FILAS_DE_LA_BASE = """
SELECT "SECCIÓN", "PI", "CÓDIGO DEL ESTUDIANTE", "CALIFICACIÓN"
FROM abet.v_tabla_maestra_pi
WHERE "AÑO" = %s AND "CICLO" = %s AND "CÓDIGO DEL CURSO" = %s
"""

_CIFRAS_DE_LA_BASE = """
SELECT seccion, carga_id, pi, n_nivel_1, n_nivel_2, n_nivel_3, n_nivel_4, n_esperado_o_superior, n_total,
       n_sin_evidencia, pct_logro_sobre_calificados
FROM abet.v_r17_por_pi
WHERE periodo = %s AND codigo_asignatura = %s
"""


class Rechazo(Exception):
    """La entrada se rechaza con sus líneas de informe y el código de salida."""

    def __init__(self, *lineas: str, codigo: int = 1) -> None:
        super().__init__(*lineas)
        self.lineas, self.codigo = list(lineas), codigo


# Niveles de un lado de la comparación, por sección y PI

Niveles = dict[str, dict[str, dict[str, Any]]]


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _porcentaje(x: int, n: int) -> Decimal | None:
    """Porcentaje de x sobre n con un decimal, redondeado lejos del cero como ROUND de PostgreSQL."""
    return (Decimal(100) * x / n).quantize(UN_DECIMAL, rounding=ROUND_HALF_UP) if n else None


def _promedio(suma: int, n: int) -> Decimal | None:
    """Promedio de n niveles con dos decimales, redondeado lejos del cero como ROUND de PostgreSQL."""
    return (Decimal(suma) / n).quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP) if n else None


@dataclass
class Logro:
    """Conteo por nivel y logro de una sección y un PI según la tabla maestra."""

    niveles: dict[str, int]

    @property
    def conteo(self) -> tuple[int, int, int, int]:
        cuenta = Counter(self.niveles.values())
        return cuenta[1], cuenta[2], cuenta[3], cuenta[4]

    @property
    def cociente(self) -> tuple[int, int]:
        return sum(1 for nivel in self.niveles.values() if nivel >= LOGRO_DEL_R17_A_MANO), len(self.niveles)


# El curso, de la tabla maestra y del sistema (spec 009, US-94)

@dataclass
class Curso:
    """Cifras del curso en un PI. por_seccion trae, por número de sección con estudiantes o con carga publicada, su porcentaje
    y su promedio. en_la_meta cuenta las secciones cuyo porcentaje llega a la meta."""

    logrados: int | None
    calificados: int
    porcentaje: Decimal | None
    promedio: Decimal | None
    en_la_meta: int
    por_seccion: dict[str, tuple[Decimal | None, Decimal | None]]


def curso_de_la_tabla(tabla: Niveles, pi: str) -> Curso:
    """Lo que la tabla maestra dice del curso en el PI. Suma estudiantes de todas las secciones y no promedia porcentajes."""
    por_seccion: dict[str, tuple[Decimal | None, Decimal | None]] = {}
    logrados = calificados = suma = en_la_meta = 0
    for seccion, pis in tabla.items():
        niveles = pis.get(pi, {})
        if not niveles:
            continue
        x, n = Logro(niveles).cociente
        porcentaje = _porcentaje(x, n)
        por_seccion[seccion] = (porcentaje, _promedio(sum(niveles.values()), n))
        logrados, calificados, suma = logrados + x, calificados + n, suma + sum(niveles.values())
        en_la_meta += porcentaje is not None and porcentaje >= META_DEL_CURSO
    return Curso(logrados, calificados, _porcentaje(logrados, calificados), _promedio(suma, calificados), en_la_meta,
                 por_seccion)


_SECCIONES_DEL_CURSO = """
SELECT s.seccion_id, s.numero
FROM abet.seccion s
JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id
JOIN abet.periodo pe   ON pe.periodo_id = s.periodo_id
WHERE pe.codigo = %s AND a.codigo = %s
"""


def _decimal(valor: float | None, cuantos: Decimal) -> Decimal | None:
    return Decimal(repr(valor)).quantize(cuantos) if valor is not None else None


def curso_del_sistema(conexion: psycopg.Connection, periodo: str, asignatura: str, pi: str) -> Curso | None:
    """Lo que la consulta de la ruta 20 da del curso en el PI, o None si el curso no tiene secciones o el plan no mide el PI."""
    secciones = [(int(seccion_id), str(int(numero)))
                 for seccion_id, numero in conexion.execute(_SECCIONES_DEL_CURSO, (periodo, asignatura)).fetchall()]
    secciones.sort(key=lambda par: int(par[1]))
    indicadores = [i for i in RESULTADOS.resumen_del_curso(conexion, secciones) if i["pi"] == pi]
    if not indicadores:
        return None
    [indicador] = indicadores
    curso = indicador["curso"]
    return Curso(curso["logrados"], curso["calificados"], _decimal(curso["pct_sobre_calificados"], UN_DECIMAL),
                 _decimal(curso["promedio_nivel"], DOS_DECIMALES), indicador["conteo_secciones"]["en_meta"],
                 {s["numero"]: (_decimal(s["pct_sobre_calificados"], UN_DECIMAL), _decimal(s["promedio_nivel"], DOS_DECIMALES))
                  for s in indicador["secciones"] if s["estado"] == "PUBLICADA"})


def _enumerar(partes: list[str]) -> str:
    """«en a», «en a y en b» o «en a, en b y en c», con cada parte precedida por «en»."""
    if len(partes) == 1:
        return f"en {partes[0]}"
    return f"en {', en '.join(partes[:-1])} y en {partes[-1]}"


ASPECTOS_DEL_CURSO = ("alumnos en el nivel esperado o superior", "el porcentaje", "el promedio", "las secciones en la meta")


def lineas_del_curso(tabla: Curso, sistema: Curso | None) -> tuple[list[str], bool]:
    """Líneas del informe del curso y si es distinto. Primero lo distinto y después lo igual, sin cifras ni códigos."""
    if sistema is None:
        iguales = [False] * len(ASPECTOS_DEL_CURSO)
    else:
        iguales = [tabla.logrados == sistema.logrados and tabla.calificados == sistema.calificados,
                   tabla.porcentaje == sistema.porcentaje, tabla.promedio == sistema.promedio,
                   tabla.en_la_meta == sistema.en_la_meta]
    distintos = [aspecto for aspecto, igual in zip(ASPECTOS_DEL_CURSO, iguales, strict=True) if not igual]
    parecidos = [aspecto for aspecto, igual in zip(ASPECTOS_DEL_CURSO, iguales, strict=True) if igual]
    lineas = []
    if distintos:
        lineas.append(f"Curso distinto {_enumerar(distintos)}.")
    if parecidos:
        lineas.append(f"Curso igual {_enumerar(parecidos)}.")
    return lineas, bool(distintos)


def lineas_del_promedio(seccion: str, tabla: Curso | None, sistema: Curso | None) -> tuple[list[str], bool]:
    """Líneas de la sección sobre su promedio y su porcentaje, y si es distinta. Sin carga publicada no trae líneas."""
    if tabla is None or sistema is None or seccion not in tabla.por_seccion or seccion not in sistema.por_seccion:
        return [], False
    (porcentaje_t, promedio_t), (porcentaje_s, promedio_s) = tabla.por_seccion[seccion], sistema.por_seccion[seccion]
    distintos = [nombre for nombre, igual in (("el promedio", promedio_t == promedio_s),
                                              ("el porcentaje", porcentaje_t == porcentaje_s)) if not igual]
    if not distintos:
        return [f"Sección {seccion}. Con promedio igual."], False
    lineas = [f"Sección {seccion}. Distinta en {' y en '.join(distintos)}."]
    if promedio_t == promedio_s:
        lineas.append(f"Sección {seccion}. Con promedio igual.")
    return lineas, True


# Tabla maestra

def leer_maestra(ruta: Path, periodo: str, asignatura: str, datos_reales: bool) -> Niveles:
    """Nivel de cada código por sección y PI, o Rechazo con todas las filas defectuosas, sin sus valores."""
    registros = M._registros(ruta)
    encabezado = [M._normalizar(celda) for celda in registros[0]] if registros else []
    faltan = [columna for columna in M.LEIDAS if columna not in encabezado]
    if faltan:
        raise Rechazo(*(f"Falta la columna {columna} de la tabla maestra." for columna in faltan), DETENIDA)
    posicion = {columna: encabezado.index(columna) for columna in M.LEIDAS}
    tabla: Niveles = {}
    errores: list[tuple[int, str]] = []
    vistas: dict[tuple[str, str, str], int] = {}
    for numero, registro in enumerate(registros[1:], start=2):
        celdas = {columna: (registro[i] if i < len(registro) else None) for columna, i in posicion.items()}
        if all(M._texto(valor) == "" for valor in celdas.values()):
            continue
        anio, ciclo = M._texto(celdas[M.ANIO]), M._texto(celdas[M.CICLO])
        if not (anio.isdigit() and ciclo.isdigit()):
            errores.append((numero, M.SIN_PERIODO))
            continue
        if f"{int(anio)}-{int(ciclo)}" != periodo or M._texto(celdas[M.ASIGNATURA]) != asignatura:
            continue
        seccion, pi = M._texto(celdas[M.SECCION]), M._texto(celdas[M.PI])
        codigo, nivel = M._texto(celdas[M.CODIGO]), M._nivel(celdas[M.CALIFICACION])
        if not seccion.isdigit() or int(seccion) == 0:
            errores.append((numero, M.SIN_SECCION))
        elif not M.OCHO_CIFRAS.fullmatch(codigo):
            errores.append((numero, M.CODIGO_MAL))
        elif not datos_reales and not codigo.startswith("99"):
            errores.append((numero, NO_ES_99))
        elif isinstance(nivel, str):
            errores.append((numero, nivel))
        elif (str(int(seccion)), pi, codigo) in vistas:
            errores += [(vistas[(str(int(seccion)), pi, codigo)], REPETIDO), (numero, REPETIDO)]
        else:
            vistas[(str(int(seccion)), pi, codigo)] = numero
            tabla.setdefault(str(int(seccion)), {}).setdefault(pi, {})[codigo] = nivel
    if errores:
        raise Rechazo(*(f"Fila {numero}. {motivo}" for numero, motivo in sorted(set(errores))), DETENIDA)
    return tabla


# Base

def abrir(conninfo: str = "") -> psycopg.Connection:
    """Conexión cuyas transacciones son READ ONLY, así un INSERT falla con el SQLSTATE 25006 aunque el rol pudiera
    escribir. Sin conninfo usa las variables de libpq."""
    conexion = psycopg.connect(conninfo, autocommit=False)
    conexion.read_only = True
    return conexion


@dataclass
class Base:
    """Lo que el sistema mide del periodo y la asignatura, leído en una transacción READ ONLY."""

    filas: Niveles = field(default_factory=dict)
    repetidos: Counter = field(default_factory=Counter)
    cifras: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)
    cargas: dict[str, set[int]] = field(default_factory=dict)
    curso: Curso | None = None


def leer_base(conexion: psycopg.Connection, periodo: str, asignatura: str, curso_del_pi: str | None = None) -> Base:
    """Lo que el sistema mide, y con curso_del_pi también el curso de ese PI, todo en la misma transacción READ ONLY."""
    anio, ciclo = (int(parte) for parte in periodo.split("-"))
    base = Base()
    try:
        with conexion.cursor() as cursor:
            for seccion, pi, codigo, nivel in cursor.execute(_FILAS_DE_LA_BASE, (anio, ciclo, asignatura)):
                niveles = base.filas.setdefault(str(int(seccion)), {}).setdefault(pi, {})
                if codigo in niveles:
                    base.repetidos[str(int(seccion))] += 1
                niveles[codigo] = nivel
            for fila in cursor.execute(_CIFRAS_DE_LA_BASE, (periodo, asignatura)):
                seccion, carga_id, pi = str(int(fila[0])), fila[1], fila[2]
                base.cargas.setdefault(seccion, set()).add(carga_id)
                base.cifras.setdefault(seccion, {})[pi] = dict(zip(
                    ("n1", "n2", "n3", "n4", "x", "total", "sin_evidencia", "pct"), fila[3:], strict=True))
            if curso_del_pi is not None:
                base.curso = curso_del_sistema(conexion, periodo, asignatura, curso_del_pi)
    finally:
        conexion.rollback()
    return base


# R-17

@dataclass
class R17:
    """Celdas de un R-17 del sistema que la conciliación compara."""

    bajos: object
    altos: object
    cociente: object
    porcentajes: dict[str, object]
    tabla: dict[str, dict[str, object]]
    repetidos: int = 0


def _celda(filas: list[tuple[object, ...]], referencia: str) -> object:
    columna, fila = ord(referencia[0]) - ord("A"), int(referencia[1:])
    valores = filas[fila - 1] if fila <= len(filas) else ()
    return valores[columna] if columna < len(valores) else None


def leer_r17(carpeta: Path, periodo: str, asignatura: str) -> tuple[dict[str, list[R17]], bool]:
    """R-17 de la carpeta por sección, solo los del periodo y la asignatura, y si algún archivo no se pudo leer."""
    por_seccion: dict[str, list[R17]] = {}
    ilegible = False
    for ruta in sorted(carpeta.glob("*.xlsx")):
        try:
            libro = load_workbook(ruta, read_only=True, data_only=True)
            try:
                filas = [tuple(fila) for fila in libro[HOJA_DEL_R17].iter_rows(max_col=17, values_only=True)]
            finally:
                libro.close()
        except Exception:  # noqa: BLE001 (openpyxl, zipfile y KeyError según el archivo, sin mostrar cuál)
            ilegible = True
            continue
        cabecera = tuple(M._texto(_celda(filas, referencia)) for referencia in ("D8", "D11", "I11"))
        if cabecera[0] != asignatura or cabecera[2] != periodo or not cabecera[1].isdigit():
            continue
        tabla: dict[str, dict[str, object]] = {}
        repetidos = 0
        for numero in range(PRIMERA_FILA_DE_LA_TABLA, len(filas) + 1):
            pi, codigo = M._texto(_celda(filas, f"C{numero}")), M._texto(_celda(filas, f"E{numero}"))
            if not pi and not codigo:
                break
            repetidos += codigo in tabla.get(pi, {})
            tabla.setdefault(pi, {})[codigo] = _celda(filas, f"F{numero}")
        porcentajes = {M._texto(_celda(filas, f"B{fila}")): _celda(filas, f"E{fila}") for fila in FILAS_DEL_BLOQUE_II
                       if M._texto(_celda(filas, f"B{fila}"))}
        por_seccion.setdefault(str(int(cabecera[1])), []).append(
            R17(_celda(filas, "M24"), _celda(filas, "M25"), _celda(filas, "M26"), porcentajes, tabla, repetidos))
    return por_seccion, ilegible


def _es_entero(valor: object, esperado: int) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool) and valor == esperado


def diferencias_del_r17(seccion: str, r17: R17, tabla: dict[str, dict[str, int]], pi: str) -> list[str]:
    """Diferencias del R-17 de la sección con la tabla maestra, en los PI que trae el R-17."""
    lineas = []
    pis = [p for p in r17.porcentajes if p in tabla] or [pi]
    niveles = [nivel for p in pis for nivel in tabla.get(p, {}).values()]
    bajos = sum(1 for nivel in niveles if nivel < LOGRO_DEL_R17_A_MANO)
    altos = len(niveles) - bajos
    if r17.tabla != {p: dict(tabla.get(p, {})) for p in r17.tabla} or set(r17.tabla) != set(pis) or r17.repetidos:
        lineas.append(f"Sección {seccion}. La tabla de estudiantes del R-17 no es la de la tabla maestra.")
    if not (_es_entero(r17.bajos, bajos) and _es_entero(r17.altos, altos)):
        lineas.append(f"Sección {seccion}. El conteo del R-17 no es el de la tabla maestra.")
    cociente_igual = (isinstance(r17.cociente, (int, float)) and niveles
                      and abs(float(r17.cociente) - altos / len(niveles)) < TOLERANCIA)
    x, n = Logro(tabla.get(pi, {})).cociente
    esperado = _porcentaje(x, n)
    mostrado = r17.porcentajes.get(pi)
    porcentaje_igual = (isinstance(mostrado, (int, float)) and esperado is not None
                        and (Decimal(repr(float(mostrado))) * 100).quantize(UN_DECIMAL, rounding=ROUND_HALF_UP)
                        == esperado)
    if not (cociente_igual and porcentaje_igual):
        lineas.append(f"Sección {seccion}. El porcentaje del R-17 no es el de la tabla maestra.")
    return lineas


# Comparación

def diferencias_de_la_seccion(seccion: str, tabla: dict[str, dict[str, int]], base: Base, pi: str,
                              r17: list[R17] | None) -> list[str]:
    """Líneas de las diferencias de la sección, vacía si la sección es igual."""
    if seccion not in base.cargas:
        return [f"Sección {seccion}. Sin carga publicada."]
    lineas = []
    if len(base.cargas[seccion]) > 1:
        lineas.append(f"Sección {seccion}. Más de una carga publicada.")
    maestra, sistema = tabla.get(pi, {}), base.filas.get(seccion, {}).get(pi, {})
    solo_en_la_tabla = len(maestra.keys() - sistema.keys())
    solo_en_el_sistema = len(sistema.keys() - maestra.keys())
    distintos = sum(1 for codigo in maestra.keys() & sistema.keys() if maestra[codigo] != sistema[codigo])
    if solo_en_la_tabla:
        lineas.append(f"Sección {seccion}. {_plural(solo_en_la_tabla, 'estudiante', 'estudiantes')} en la tabla "
                      "maestra que el sistema no mide.")
    if solo_en_el_sistema:
        medidos = "medido por el sistema que no está" if solo_en_el_sistema == 1 else "medidos por el sistema que no están"
        lineas.append(f"Sección {seccion}. {solo_en_el_sistema} "
                      f"{'estudiante' if solo_en_el_sistema == 1 else 'estudiantes'} {medidos} en la tabla.")
    if distintos:
        lineas.append(f"Sección {seccion}. {_plural(distintos, 'estudiante', 'estudiantes')} con nivel distinto.")
    if base.repetidos[seccion]:
        lineas.append(f"Sección {seccion}. {_plural(base.repetidos[seccion], 'estudiante', 'estudiantes')} con más de "
                      "una fila en el sistema.")
    lineas += _diferencias_de_las_cifras(seccion, Logro(maestra), base.cifras.get(seccion, {}).get(pi), pi)
    otros = sorted((set(tabla) | set(base.filas.get(seccion, {}))) - {pi})
    for otro in otros:
        en_la_tabla, en_el_sistema = len(tabla.get(otro, {})), len(base.filas.get(seccion, {}).get(otro, {}))
        if en_la_tabla != en_el_sistema:
            lineas.append(f"Sección {seccion}. {_plural(en_la_tabla, 'fila', 'filas')} del PI {otro} en la tabla "
                          f"maestra y {en_el_sistema} en el sistema (D-48).")
    if r17 is not None:
        if not r17:
            lineas.append(f"Sección {seccion}. Sin R-17 en la carpeta.")
        elif len(r17) > 1:
            lineas.append(f"Sección {seccion}. Más de un R-17 en la carpeta.")
        else:
            lineas += diferencias_del_r17(seccion, r17[0], tabla, pi)
    return lineas


def _diferencias_de_las_cifras(seccion: str, logro: Logro, cifras: dict[str, Any] | None, pi: str) -> list[str]:
    """Conteo por nivel y logro de abet.v_r17_por_pi frente a la tabla maestra."""
    if cifras is None:
        return [f"Sección {seccion}. El plan del sistema no mide el PI {pi}."]
    lineas = []
    if (cifras["n1"], cifras["n2"], cifras["n3"], cifras["n4"]) != logro.conteo:
        lineas.append(f"Sección {seccion}. El conteo por nivel del sistema no es el de la tabla maestra.")
    x = cifras["x"] if cifras["x"] is not None else cifras["n3"] + cifras["n4"]
    n = cifras["total"] - cifras["sin_evidencia"]
    pct = cifras["pct"]
    if (x, n) != logro.cociente or pct is None or Decimal(pct).quantize(UN_DECIMAL) != _porcentaje(*logro.cociente):
        lineas.append(f"Sección {seccion}. El porcentaje del sistema no es el de la tabla maestra.")
    return lineas


def conciliar(maestra: Niveles, base: Base, pi: str, r17: dict[str, list[R17]] | None,
              con_curso: bool = False) -> tuple[int, list[str]]:
    """Informe de la conciliación. Con con_curso suma por sección la línea del promedio y, antes del total, la del curso."""
    secciones = sorted(set(maestra) | set(base.cargas), key=int)
    de_la_tabla = curso_de_la_tabla(maestra, pi) if con_curso else None
    lineas, iguales = [], 0
    for seccion in secciones:
        diferencias = diferencias_de_la_seccion(seccion, maestra.get(seccion, {}), base, pi,
                                                None if r17 is None else r17.get(seccion, []))
        del_promedio, promedio_distinto = lineas_del_promedio(seccion, de_la_tabla, base.curso)
        if diferencias:
            lineas += diferencias
        elif not promedio_distinto:
            iguales += 1
            n = len(maestra.get(seccion, {}).get(pi, {}))
            lineas.append(f"Sección {seccion}. Igual en {n} de {n} estudiantes, en el conteo por nivel y en el "
                          "porcentaje.")
        lineas += del_promedio
    curso_distinto = False
    if de_la_tabla is not None:
        del_curso, curso_distinto = lineas_del_curso(de_la_tabla, base.curso)
        lineas += del_curso
    lineas.append(f"{iguales} de {len(secciones)} secciones iguales.")
    return (0 if secciones and iguales == len(secciones) and not curso_distinto else 1), lineas


# Argumentos y principal

class _Argumentos(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # noqa: ARG002 (el mensaje de argparse no se muestra en inglés)
        raise Rechazo("Argumentos inválidos. Lea el uso al comienzo de db/herramientas/conciliar_tabla_maestra.py.",
                      codigo=2)


def argumentos_de(argv: list[str] | None) -> argparse.Namespace:
    analizador = _Argumentos(add_help=False)
    for opcion in ("--maestra", "--periodo", "--asignatura", "--pi", "--r17"):
        analizador.add_argument(opcion)
    analizador.add_argument("--datos-reales", action="store_true")
    analizador.add_argument("--curso", action="store_true")
    argumentos = analizador.parse_args(argv)
    validos = (argumentos.maestra and M.PERIODO.fullmatch(argumentos.periodo or "")
               and M.ASIGNATURA_VALIDA.fullmatch(argumentos.asignatura or "") and M.PI_VALIDO.fullmatch(argumentos.pi or ""))
    if not validos:
        analizador.error("")
    return argumentos


def principal(argv: list[str] | None = None) -> tuple[int, list[str]]:
    try:
        argumentos = argumentos_de(argv)
        maestra_ruta = Path(argumentos.maestra)
        carpeta = Path(argumentos.r17) if argumentos.r17 else None
        # Antes de leer nada y de conectarse, porque los repositorios son públicos (D-10).
        if M.dentro_de_un_repositorio(maestra_ruta):
            raise Rechazo(MAESTRA_EN_REPOSITORIO, codigo=2)
        if carpeta is not None and M.dentro_de_un_repositorio(carpeta):
            raise Rechazo(R17_EN_REPOSITORIO, codigo=2)
        try:
            maestra = leer_maestra(maestra_ruta, argumentos.periodo, argumentos.asignatura, argumentos.datos_reales)
        except M.Rechazo as rechazo:
            raise Rechazo(*rechazo.lineas, DETENIDA) from None
        r17, ilegible = leer_r17(carpeta, argumentos.periodo, argumentos.asignatura) if carpeta else (None, False)
        try:
            with abrir() as conexion:
                base = leer_base(conexion, argumentos.periodo, argumentos.asignatura,
                                 argumentos.pi if argumentos.curso else None)
        except psycopg.OperationalError:
            raise Rechazo(SIN_RESPUESTA, codigo=3) from None
        codigo, lineas = conciliar(maestra, base, argumentos.pi, r17, argumentos.curso)
        if ilegible:
            lineas.insert(0, R17_ILEGIBLE)
            codigo = 1
        encabezado = f"Conciliación de {argumentos.asignatura} en {argumentos.periodo}, PI {argumentos.pi}."
        return codigo, [encabezado, *lineas]
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
