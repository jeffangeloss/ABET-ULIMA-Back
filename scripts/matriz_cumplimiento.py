#!/usr/bin/env python3
"""Matriz de cumplimiento de las specs 007 y 008 (US-90, T055 y FR-026 de specs/008-ciclo-quimica-industrial).

El generador liga cada historia de las specs 007 y 008 con sus escenarios y con la prueba que los cubre, y cada regla
de las specs vivas de specs/features/ con los escenarios y las pruebas que nombra su línea **Prueba**.

- Los escenarios del Back se buscan en lo que pytest-bdd liga de verdad. El generador recolecta tests/aceptacion/pasos
  del Back sin correr nada y lee la plantilla de cada prueba.
- Los escenarios @delegado_a_vitest se buscan en tests/ del Front y los @playwright en e2e/, por su título exacto. Un
  esquema admite además el título seguido de sus parámetros entre paréntesis, como «Título ($estado)». Una prueba que
  solo existe como it.todo o skip no cuenta.
- specs/008-ciclo-quimica-industrial/cumplimiento_razones.toml da la razón escrita de cada excepción, el enlace con una
  prueba de otro título o el escenario o la historia pendiente por decisión o de tarea.

La traza va a cumplimiento.md, que no cambia con cada corrida. El resultado y la fecha de cada prueba salen del reporte
JSON de Vitest (--vitest) y del de pytest --junitxml (--junit), y quedan solo en el informe (--informe), que la
integración continua deja en su resumen. La generación termina con 1 ante una historia sin escenario, un escenario sin
prueba y sin razón, una etiqueta sin historia, un enlace o una razón a algo que no existe, una regla sin prueba, una
prueba nombrada que no existe, un número de ocho cifras o un correo fuera de example.invalid en la salida, una
recolección del Back que falla o, con --comprobar, un cumplimiento.md que no está al día. Ante cualquiera de los dos
últimos casos de datos no escribe nada.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parents[1]
SPECS_DE_LA_MATRIZ = ("007-experiencia-por-cuenta", "008-ciclo-quimica-industrial")
CARPETA_008 = "008-ciclo-quimica-industrial"
# El tramo de la capacitación en el orden del flujo, con las historias de la spec 008 de cada pieza.
TRAMOS = (("Catálogo", ("US-67", "US-68", "US-69")), ("Alcance", ("US-70", "US-71", "US-72")), ("Periodo", ("US-73",)),
          ("Generador", ("US-74",)), ("Carga", ("US-75", "US-76", "US-77")), ("R-17", ("US-78",)),
          ("Avance", ("US-79", "US-80")), ("Sistema visual", ("US-81", "US-82")), ("Conciliación", ("US-83",)),
          ("Ensayo", ("US-84",)), ("Siembra", ("US-86",)), ("Humo", ("US-85",)), ("Guía", ("US-87",)),
          ("Privacidad", ("US-88",)), ("Cierre", ("US-89",)))
CON_PRUEBA = "Con prueba"
SIN_PRUEBA = "Sin prueba"
SIN_ESCENARIO = "Sin escenario"
CON_HUECOS = "Con huecos"
PENDIENTES = ("Pendiente por decisión", "Pendiente de tarea")
HISTORIA = re.compile(r"^### (US-[0-9]+): (.+?)(?: \(Priority: P[0-9]\))?\s*$", re.M)
REGLA = re.compile(r"^### (BR-[A-Z0-9]+(?:-[A-Z0-9]+)*-[0-9]+)\b", re.M)
TITULO_DE_PRUEBA = re.compile(
    r"(?:\b(?P<fn>it|test)(?P<mods>(?:\.(?:only|skip|todo|fails|concurrent|fixme|sequential))*)\s*\(|\)\s*\()\s*"
    r"(?P<q>[\"'`])(?P<titulo>(?:\\.|(?!(?P=q)).)*)(?P=q)", re.S)
MARCADOR = re.compile(r"\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_.]*|%[sdifjo#%]")
OCHO_CIFRAS = re.compile(r"(?<![0-9A-Za-z])[0-9]{8}(?![0-9A-Za-z])")
CORREO = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
PRUEBA_NOMBRADA = re.compile(r"`(test_[A-Za-z0-9_]+)`")
ARCHIVO_NOMBRADO = re.compile(r"`((?:tests|e2e)/[^`\s]+\.(?:py|tsx?))`")


class Falla(Exception):
    """Algo que impide armar la matriz, con su mensaje."""


@dataclass(frozen=True)
class Prueba:
    """Una prueba que cubre un escenario. tipo es pytest-bdd, Vitest o Playwright."""

    tipo: str
    archivo: str
    titulo: str
    mismo_titulo: bool = False

    def texto(self) -> str:
        if self.tipo == "pytest-bdd":
            return f"pytest-bdd {self.archivo}::{self.titulo}"
        return f"{self.tipo} {self.archivo}" if self.mismo_titulo else f"{self.tipo} {self.archivo} › {self.titulo}"


@dataclass
class Escenario:
    archivo: str  # relativo a specs/
    titulo: str
    historia: str
    tipo: str
    plantilla: bool
    orden: int
    pruebas: list[Prueba] = field(default_factory=list)
    estado: str = SIN_PRUEBA
    razon: str = ""


@dataclass
class Historia:
    clave: str
    spec: str
    titulo: str
    escenarios: list[Escenario] = field(default_factory=list)
    estado: str = SIN_ESCENARIO
    razon: str = ""


@dataclass
class Regla:
    clave: str
    spec_viva: str
    escenarios: int
    nombradas: list[str]
    estado: str


@dataclass(frozen=True)
class PruebaDelFront:
    tipo: str
    archivo: str
    titulo: str
    pendiente: bool


@dataclass
class Resultados:
    """Resultado de cada prueba en los reportes de una corrida, con la fecha de cada reporte."""

    vitest: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    pytest: dict[tuple[str, str], list[str]] = field(default_factory=dict)
    fecha_vitest: datetime | None = None
    fecha_pytest: datetime | None = None


# Lectura de las specs

def numero(clave: str) -> int:
    return int(clave.split("-")[1])


def historias_de(specs: Path) -> tuple[dict[str, Historia], set[str]]:
    """Historias de las specs 007 y 008, y las claves de todas las historias de specs/*/spec.md."""
    todas: set[str] = set()
    alcance: dict[str, Historia] = {}
    for spec in sorted(specs.glob("*/spec.md")):
        for marca in HISTORIA.finditer(spec.read_text(encoding="utf-8")):
            todas.add(marca.group(1))
            if spec.parent.name in SPECS_DE_LA_MATRIZ:
                alcance[marca.group(1)] = Historia(marca.group(1), spec.parent.name[:3], marca.group(2))
    return alcance, todas


def escenarios_de(specs: Path) -> tuple[list[Escenario], list[str], set[str]]:
    """Escenarios de las specs 007 y 008, los errores de etiquetas y los títulos de todos los escenarios de specs/."""
    from pytest_bdd.feature import get_features

    _, todas = historias_de(specs)
    escenarios: list[Escenario] = []
    errores: list[str] = []
    titulos: set[str] = set()
    for ruta in sorted(specs.glob("*/aceptacion/*.feature")):
        [feature] = get_features([str(ruta)])
        archivo = ruta.relative_to(specs).as_posix()
        for orden, escenario in enumerate(feature.scenarios.values()):
            titulos.add(escenario.name)
            historias = sorted(t for t in escenario.tags if re.fullmatch(r"US-[0-9]+", t))
            for etiqueta in historias:
                if etiqueta not in todas:
                    errores.append(f"Etiqueta sin historia @{etiqueta} en specs/{archivo}, «{escenario.name}».")
            if ruta.parent.parent.name not in SPECS_DE_LA_MATRIZ:
                continue
            if len(historias) != 1:
                errores.append(f"El escenario «{escenario.name}» de specs/{archivo} no lleva una sola etiqueta US.")
                continue
            etiquetas = set(escenario.tags)
            tipo = ("Vitest" if "delegado_a_vitest" in etiquetas else
                    "Playwright" if "playwright" in etiquetas else "pytest-bdd")
            escenarios.append(Escenario(archivo, escenario.name, historias[0], tipo, escenario.templated, orden))
    return escenarios, errores, titulos


def reglas_de(specs: Path, titulos: set[str], raiz: Path, front: Path) -> tuple[list[Regla], list[str]]:
    """Reglas de specs/features/*/*.spec.md con los escenarios y las pruebas que nombra su línea **Prueba**."""
    definidas = {m.group(1) for ruta in (raiz / "tests").rglob("*.py")
                 for m in re.finditer(r"^\s*def (test_[A-Za-z0-9_]+)\(", ruta.read_text(encoding="utf-8"), re.M)}
    reglas: list[Regla] = []
    errores: list[str] = []
    for spec in sorted(specs.glob("features/*/*.spec.md")):
        texto = spec.read_text(encoding="utf-8").split("\n## Verification", 1)[0]
        marcas = list(REGLA.finditer(texto))
        for i, marca in enumerate(marcas):
            bloque = texto[marca.start():marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)]
            lineas = [linea for linea in bloque.splitlines() if "**Prueba**" in linea]
            escenarios = {t for linea in lineas for t in re.findall(r"«([^»]+)»", linea) if t in titulos}
            nombradas: list[str] = []
            faltan: list[str] = []
            for linea in lineas:
                for prueba in PRUEBA_NOMBRADA.findall(linea):
                    nombradas.append(prueba)
                    if prueba not in definidas:
                        faltan.append(prueba)
                for archivo in ARCHIVO_NOMBRADO.findall(linea):
                    nombradas.append(archivo)
                    base = raiz if archivo.endswith(".py") else front
                    if not (base / archivo).is_file():
                        faltan.append(archivo)
            nombradas = list(dict.fromkeys(nombradas))
            if faltan:
                estado = "Prueba nombrada que no existe"
                errores.append(f"{marca.group(1)} nombra pruebas que no existen, {', '.join(dict.fromkeys(faltan))}.")
            elif escenarios:
                estado = "Con escenario"
            elif nombradas:
                estado = "Con prueba nombrada"
            else:
                estado = SIN_PRUEBA
                errores.append(f"{marca.group(1)} no tiene escenario ni prueba nombrada en su línea **Prueba**.")
            reglas.append(Regla(marca.group(1), spec.parent.name, len(escenarios), nombradas, estado))
    return reglas, errores


# Pruebas del Back y del Front

def ligaduras_del_back(raiz: Path) -> dict[tuple[str, str], set[tuple[str, str]]]:
    """Archivo de la prueba y función de cada escenario que pytest-bdd liga en tests/aceptacion/pasos, sin correrlo."""
    import pytest
    from pytest_bdd.scenario import scenario_wrapper_template_registry

    raiz = raiz.resolve()

    class Recolector:
        def __init__(self) -> None:
            self.ligas: dict[tuple[str, str], set[tuple[str, str]]] = {}

        def pytest_collection_finish(self, session: Any) -> None:
            for item in session.items:
                plantilla = scenario_wrapper_template_registry.get(getattr(item, "function", None))
                if plantilla is None:
                    continue
                with contextlib.suppress(ValueError):
                    feature = Path(plantilla.feature.filename).resolve().relative_to(raiz).as_posix()
                    archivo, _, resto = item.nodeid.partition("::")
                    self.ligas.setdefault((feature, plantilla.name), set()).add((archivo, resto.split("[")[0]))

    # La corrida de la CI pone --junitxml en PYTEST_ADDOPTS, y la recolección no debe pisar ese reporte.
    os.environ.pop("PYTEST_ADDOPTS", None)
    recolector = Recolector()
    salida = io.StringIO()
    previo = Path.cwd()
    os.chdir(raiz)
    try:
        with contextlib.redirect_stdout(salida):
            codigo = pytest.main(["--collect-only", "-q", "-p", "no:cacheprovider", "--rootdir", str(raiz),
                                  str(raiz / "tests" / "aceptacion" / "pasos")], plugins=[recolector])
    finally:
        os.chdir(previo)
    if codigo not in (0, 5):
        cola = "\n".join(salida.getvalue().splitlines()[-15:])
        raise Falla(f"La recolección de tests/aceptacion/pasos termina con {int(codigo)}.\n{cola}")
    return recolector.ligas


def _sin_escapes(literal: str) -> str:
    return re.sub(r"\\(.)", r"\1", literal)


def pruebas_del_front(front: Path) -> list[PruebaDelFront]:
    """Título de cada prueba de Vitest de tests/ y de Playwright de e2e/ del Front, leído del código fuente."""
    pruebas: list[PruebaDelFront] = []
    fuentes = [("Vitest", r) for patron in ("*.test.ts", "*.test.tsx") for r in (front / "tests").rglob(patron)]
    fuentes += [("Playwright", r) for r in (front / "e2e").rglob("*.spec.ts")]
    for tipo, ruta in sorted(fuentes, key=lambda par: par[1]):
        if "node_modules" in ruta.parts:
            continue
        texto = ruta.read_text(encoding="utf-8")
        for marca in TITULO_DE_PRUEBA.finditer(texto):
            mods = marca.group("mods") or ""
            pendiente = any(m in mods for m in (".todo", ".skip", ".fixme"))
            pruebas.append(PruebaDelFront(tipo, ruta.relative_to(front).as_posix(), _sin_escapes(marca.group("titulo")),
                                          pendiente))
    return pruebas


def coincide(titulo_de_prueba: str, escenario: Escenario) -> bool:
    """Título exacto, o en un esquema el título seguido de sus parámetros entre paréntesis."""
    if titulo_de_prueba == escenario.titulo:
        return True
    return escenario.plantilla and titulo_de_prueba.startswith(f"{escenario.titulo} (") and titulo_de_prueba.endswith(")")


def patron_de(titulo: str) -> re.Pattern[str]:
    """Expresión que reconoce en un reporte los títulos que Vitest arma con los marcadores $x, %s o ${x}."""
    partes = MARCADOR.split(titulo)
    return re.compile(".+?".join(re.escape(parte) for parte in partes), re.S)


# Razones

def leer_razones(ruta: Path) -> dict[str, Any]:
    if not ruta.is_file():
        raise Falla(f"No se encuentra el archivo de razones {ruta.name}.")
    try:
        return tomllib.loads(ruta.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise Falla(f"{ruta.name} no es TOML válido ({error}).") from None


# Armado de la matriz

def armar(specs: Path, front: Path, raiz: Path, razones: dict[str, Any]) -> tuple[
        list[Historia], list[Escenario], list[Regla], list[str], list[str]]:
    historias, _ = historias_de(specs)
    escenarios, errores, titulos = escenarios_de(specs)
    avisos: list[str] = []
    ligas = ligaduras_del_back(raiz)
    del_front = pruebas_del_front(front)
    reglas, errores_de_reglas = reglas_de(specs, titulos, raiz, front)

    por_clave = {(e.archivo, e.titulo): e for e in escenarios}
    razon_de_historia = razones.get("historias", {})
    for clave, razon in razon_de_historia.items():
        if clave not in historias:
            errores.append(f"La razón de {clave} nombra una historia que no está en las specs 007 y 008.")
        elif razon.get("estado") not in PENDIENTES or not razon.get("razon"):
            errores.append(f"La razón de {clave} necesita un estado de {' o '.join(PENDIENTES)} y su razón.")
    enlaces: dict[tuple[str, str], dict[str, Any]] = {}
    for entrada in razones.get("escenarios", []):
        clave = (entrada.get("archivo", ""), entrada.get("escenario", ""))
        if clave not in por_clave:
            errores.append(f"La razón de «{clave[1]}» nombra un escenario que no está en specs/{clave[0]}.")
        elif not entrada.get("razon") or ("pruebas" in entrada) == ("estado" in entrada):
            errores.append(f"La razón de «{clave[1]}» necesita su razón y, o bien sus pruebas, o bien su estado.")
        elif "estado" in entrada and entrada["estado"] not in PENDIENTES:
            errores.append(f"La razón de «{clave[1]}» tiene un estado que no es {' ni '.join(PENDIENTES)}.")
        else:
            enlaces[clave] = entrada

    for escenario in escenarios:
        entrada = enlaces.get((escenario.archivo, escenario.titulo), {})
        if escenario.tipo == "pytest-bdd":
            ligadas = ligas.get((f"specs/{escenario.archivo}", escenario.titulo), set())
            escenario.pruebas = [Prueba("pytest-bdd", archivo, funcion) for archivo, funcion in sorted(ligadas)]
        elif "pruebas" in entrada:
            for nombrada in entrada["pruebas"]:
                existe = any(p.tipo == escenario.tipo and not p.pendiente and p.archivo == nombrada["archivo"]
                             and p.titulo == nombrada["titulo"] for p in del_front)
                if existe:
                    escenario.pruebas.append(Prueba(escenario.tipo, nombrada["archivo"], nombrada["titulo"]))
                else:
                    errores.append(f"El enlace de «{escenario.titulo}» nombra «{nombrada['titulo']}», que no está en "
                                   f"{nombrada['archivo']} del Front.")
        else:
            encontradas = [p for p in del_front if p.tipo == escenario.tipo and coincide(p.titulo, escenario)]
            escenario.pruebas = [Prueba(p.tipo, p.archivo, p.titulo, p.titulo == escenario.titulo)
                                 for p in encontradas if not p.pendiente]
            if encontradas and not escenario.pruebas:
                escenario.razon = "solo como it.todo o skip"
        pendiente = entrada if "estado" in entrada else razon_de_historia.get(escenario.historia, {})
        if escenario.pruebas:
            escenario.estado = CON_PRUEBA
            if "estado" in entrada:
                avisos.append(f"La razón de «{escenario.titulo}» sobra, porque el escenario ya tiene prueba.")
        elif pendiente.get("estado") in PENDIENTES:
            escenario.estado, escenario.razon = pendiente["estado"], pendiente["razon"]
        else:
            escenario.estado = SIN_PRUEBA
            lugar = {"Vitest": "en tests/ del Front", "Playwright": "en e2e/ del Front",
                     "pytest-bdd": "ligada en tests/aceptacion/pasos"}[escenario.tipo]
            extra = f" ({escenario.razon})" if escenario.razon else ""
            errores.append(f"Sin prueba {lugar} para «{escenario.titulo}» de specs/{escenario.archivo}{extra}.")
        if escenario.historia in historias:
            historias[escenario.historia].escenarios.append(escenario)

    for historia in historias.values():
        razon = razon_de_historia.get(historia.clave, {})
        estados = [e.estado for e in historia.escenarios]
        if not estados:
            historia.estado, historia.razon = razon.get("estado", SIN_ESCENARIO), razon.get("razon", "")
            if historia.estado == SIN_ESCENARIO:
                errores.append(f"{historia.clave} no tiene ningún escenario con su etiqueta.")
        elif SIN_PRUEBA in estados:
            historia.estado = CON_HUECOS
        elif all(estado == CON_PRUEBA for estado in estados):
            historia.estado = CON_PRUEBA
            if razon:
                avisos.append(f"La razón de {historia.clave} sobra, porque todos sus escenarios tienen prueba.")
        elif razon.get("estado") in PENDIENTES:
            historia.estado, historia.razon = razon["estado"], razon["razon"]
        elif CON_PRUEBA not in estados and len(set(estados)) == 1:
            historia.estado = estados[0]
            historia.razon = " ".join(dict.fromkeys(e.razon for e in historia.escenarios))
        else:
            partes = [f"{estados.count(p)} {_en_plural(p, estados.count(p))}" for p in PENDIENTES if p in estados]
            historia.estado = f"{CON_PRUEBA} y {' y '.join(partes)}"
            historia.razon = " ".join(dict.fromkeys(e.razon for e in historia.escenarios if e.razon))

    ordenadas = sorted(historias.values(), key=lambda h: numero(h.clave))
    escenarios.sort(key=lambda e: (numero(e.historia), e.archivo, e.orden))
    return ordenadas, escenarios, reglas, errores + errores_de_reglas, avisos


def _en_plural(estado: str, cuantos: int) -> str:
    texto = estado.lower()
    return texto.replace("pendiente", "pendientes", 1) if cuantos != 1 else texto


def estado_del_tramo(historias: list[Historia]) -> str:
    estados = [h.estado for h in historias]
    if all(e == CON_PRUEBA for e in estados) or len(set(estados)) == 1:
        return estados[0]
    if any(e in (CON_HUECOS, SIN_ESCENARIO) for e in estados):
        return CON_HUECOS
    otras = [f"{h.clave}, {h.estado[0].lower()}{h.estado[1:]}" for h in historias if h.estado != CON_PRUEBA]
    return f"{CON_PRUEBA} salvo {'; '.join(otras)}"


# Resultados de una corrida

def _relativa(nombre: str, front: Path) -> str:
    ruta = Path(nombre)
    with contextlib.suppress(ValueError):
        return ruta.resolve().relative_to(front.resolve()).as_posix()
    for raiz in ("tests/", "e2e/"):
        if f"/{raiz}" in nombre:
            return raiz + nombre.rsplit(f"/{raiz}", 1)[1]
    return nombre


def leer_resultados(vitest: Path | None, junit: Path | None, front: Path) -> Resultados:
    resultados = Resultados()
    if vitest is not None:
        try:
            reporte = json.loads(vitest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise Falla(f"El reporte de Vitest no se puede leer ({type(error).__name__}).") from None
        if reporte.get("startTime"):
            resultados.fecha_vitest = datetime.fromtimestamp(reporte["startTime"] / 1000, tz=UTC)
        for archivo in reporte.get("testResults", []):
            relativa = _relativa(archivo.get("name", ""), front)
            for prueba in archivo.get("assertionResults", []):
                resultados.vitest.setdefault(relativa, []).append((prueba.get("title", ""), prueba.get("status", "")))
    if junit is not None:
        try:
            arbol = ET.parse(junit)
        except (OSError, ET.ParseError) as error:
            raise Falla(f"El reporte de pytest no se puede leer ({type(error).__name__}).") from None
        for suite in arbol.getroot().iter("testsuite"):
            if suite.get("timestamp") and resultados.fecha_pytest is None:
                momento = datetime.fromisoformat(suite.get("timestamp", ""))
                resultados.fecha_pytest = (momento if momento.tzinfo else momento.replace(tzinfo=UTC)).astimezone(UTC)
            for caso in suite.iter("testcase"):
                archivo = caso.get("classname", "").replace(".", "/") + ".py"
                funcion = caso.get("name", "").split("[")[0]
                if caso.find("failure") is not None or caso.find("error") is not None:
                    estado = "Fallida"
                elif caso.find("skipped") is not None:
                    estado = "Omitida"
                else:
                    estado = "Aprobada"
                resultados.pytest.setdefault((archivo, funcion), []).append(estado)
    return resultados


VITEST = {"passed": "Aprobada", "failed": "Fallida", "skipped": "Omitida", "pending": "Omitida", "todo": "Omitida"}


def resultado_de_prueba(prueba: Prueba, resultados: Resultados) -> tuple[str, datetime | None]:
    if prueba.tipo == "pytest-bdd":
        estados = resultados.pytest.get((prueba.archivo, prueba.titulo), [])
        fecha = resultados.fecha_pytest
    elif prueba.tipo == "Vitest":
        patron = patron_de(prueba.titulo)
        estados = [VITEST.get(estado, "Omitida") for titulo, estado in resultados.vitest.get(prueba.archivo, [])
                   if patron.fullmatch(titulo)]
        fecha = resultados.fecha_vitest
    else:
        estados, fecha = [], None
    if not estados:
        return "Sin corrida", None
    for estado in ("Fallida", "Omitida"):
        if estado in estados:
            return estado, fecha
    return "Aprobada", fecha


def combinar(pares: Iterable[tuple[str, datetime | None]]) -> str:
    pares = list(pares)
    if not pares:
        return "Sin pruebas que correr"
    estados = [estado for estado, _ in pares]
    for estado in ("Fallida", "Omitida"):
        if estado in estados:
            return estado
    fechas = [fecha for estado, fecha in pares if estado == "Aprobada" and fecha is not None]
    if "Sin corrida" in estados:
        aprobadas = estados.count("Aprobada")
        return f"Sin corrida en {len(estados) - aprobadas} de {len(estados)} pruebas" if aprobadas else "Sin corrida"
    return f"Aprobada el {fecha_legible(max(fechas))}"


def fecha_legible(momento: datetime) -> str:
    return momento.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")


# Salidas

def celda(texto: str) -> str:
    return texto.replace("|", "\\|").replace("\n", " ").strip() or "Ninguna"


def tabla(encabezados: list[str], filas: Iterable[list[str]]) -> list[str]:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "|".join("---" for _ in encabezados) + "|"]
    lineas += ["| " + " | ".join(celda(c) for c in fila) + " |" for fila in filas]
    return lineas


def _archivos(historia: Historia) -> str:
    return ", ".join(dict.fromkeys(Path(e.archivo).name for e in historia.escenarios))


def _pruebas(historia: Historia) -> str:
    return ", ".join(dict.fromkeys(f"{p.tipo} {p.archivo}" for e in historia.escenarios for p in e.pruebas))


def escribir(historias: list[Historia], escenarios: list[Escenario], reglas: list[Regla],
             resultados: Resultados | None) -> str:
    """cumplimiento.md sin resultados, o el informe con el resultado de cada prueba si se pasan los reportes."""
    por_clave = {h.clave: h for h in historias}
    con = resultados is not None
    res: Resultados = resultados or Resultados()

    def de_escenario(escenario: Escenario) -> list[tuple[str, datetime | None]]:
        return [resultado_de_prueba(p, res) for p in escenario.pruebas] if escenario.estado == CON_PRUEBA else []

    def de_historia(historia: Historia) -> str:
        return combinar(par for e in historia.escenarios for par in de_escenario(e))

    lineas: list[str] = []
    if con:
        lineas += ["# Informe de la matriz de cumplimiento de las specs 007 y 008", ""]
        lineas += [f"- Reporte de Vitest del {fecha_legible(res.fecha_vitest)}." if res.fecha_vitest else
                   "- Sin reporte de Vitest.",
                   f"- Reporte de pytest del {fecha_legible(res.fecha_pytest)}." if res.fecha_pytest else
                   "- Sin reporte de pytest.",
                   "- Las pruebas de Playwright no corren en la integración continua y salen sin corrida.", ""]
    else:
        lineas += ["# Cumplimiento de las specs 007 y 008", "",
                   "Traza que genera `scripts/matriz_cumplimiento.py` (US-90, T055). No se edita a mano. Liga cada "
                   "historia de las specs 007 y 008 con sus escenarios y con la prueba que los cubre, y cada regla de "
                   "las specs vivas con lo que nombra su línea **Prueba**. Las excepciones llevan su razón en "
                   "`cumplimiento_razones.toml`. El resultado y la fecha de cada corrida quedan en el informe de la "
                   "integración continua y no en este archivo.", ""]
    lineas += ["## Tramo de la capacitación", ""]
    filas = []
    for nombre, claves in TRAMOS:
        del_tramo = [por_clave[c] for c in claves if c in por_clave]
        fila = [nombre, ", ".join(claves), str(sum(len(h.escenarios) for h in del_tramo)),
                estado_del_tramo(del_tramo) if del_tramo else SIN_ESCENARIO]
        if con:
            fila.append(combinar(par for h in del_tramo for e in h.escenarios for par in de_escenario(e)))
        filas.append(fila)
    lineas += tabla(["Tramo", "Historias", "Escenarios", "Estado"] + (["Resultado"] if con else []), filas)
    lineas += ["", "## Historias", ""]
    lineas += tabla(["Historia", "Spec", "Título", "Escenarios", "Archivos de los escenarios", "Pruebas", "Razón",
                     "Estado"] + (["Resultado"] if con else []),
                    ([h.clave, h.spec, h.titulo, str(len(h.escenarios)), _archivos(h), _pruebas(h), h.razon, h.estado]
                     + ([de_historia(h)] if con else []) for h in historias))
    lineas += ["", "## Reglas de las specs vivas", ""]
    lineas += tabla(["Regla", "Spec viva", "Escenarios", "Pruebas nombradas", "Estado"],
                    ([r.clave, r.spec_viva, str(r.escenarios), ", ".join(r.nombradas), r.estado] for r in reglas))
    lineas += ["", "## Escenarios", ""]
    lineas += tabla(["Historia", "Archivo", "Escenario", "Prueba", "Estado"] + (["Resultado"] if con else []),
                    ([e.historia, Path(e.archivo).name, e.titulo, "; ".join(p.texto() for p in e.pruebas), e.estado]
                     + ([combinar(de_escenario(e))] if con else []) for e in escenarios))
    return "\n".join(lineas) + "\n"


def datos_reales(texto: str, nombre: str) -> list[str]:
    """Motivos por los que un texto no puede salir, sin repetir el valor encontrado."""
    motivos = []
    for numero_de_linea, linea in enumerate(texto.splitlines(), start=1):
        if OCHO_CIFRAS.search(linea):
            motivos.append(f"{nombre} trae un número de ocho cifras en la línea {numero_de_linea}.")
        if any(not correo.lower().endswith("@example.invalid") for correo in CORREO.findall(linea)):
            motivos.append(f"{nombre} trae un correo fuera de example.invalid en la línea {numero_de_linea}.")
    return motivos


def main(argv: list[str] | None = None) -> int:
    lector = argparse.ArgumentParser(description="Matriz de cumplimiento de las specs 007 y 008 (US-90).")
    lector.add_argument("--front", required=True, type=Path, help="raíz del Front, con tests/ y e2e/")
    lector.add_argument("--specs", type=Path, default=RAIZ / "specs", help="carpeta specs/ que se lee")
    lector.add_argument("--raiz", type=Path, default=RAIZ, help="raíz del Back cuyas pruebas se recolectan")
    lector.add_argument("--razones", type=Path, help="archivo de razones (por omisión, el de la spec 008)")
    lector.add_argument("--salida", type=Path, help="cumplimiento.md que se escribe (por omisión, el de la spec 008)")
    lector.add_argument("--comprobar", action="store_true", help="compara la traza con --salida sin escribirla")
    lector.add_argument("--informe", type=Path, help="informe con el resultado y la fecha de cada prueba")
    lector.add_argument("--vitest", type=Path, help="reporte JSON de Vitest")
    lector.add_argument("--junit", type=Path, help="reporte de pytest --junitxml")
    argumentos = lector.parse_args(argv)
    specs, front = argumentos.specs.resolve(), argumentos.front.resolve()
    razones_ruta = argumentos.razones or specs / CARPETA_008 / "cumplimiento_razones.toml"
    salida = argumentos.salida or specs / CARPETA_008 / "cumplimiento.md"
    if not (front / "tests").is_dir():
        print(f"El Front {front.name} no tiene la carpeta tests/.", file=sys.stderr)
        return 1
    try:
        razones = leer_razones(razones_ruta)
        historias, escenarios, reglas, errores, avisos = armar(specs, front, argumentos.raiz.resolve(), razones)
        resultados = leer_resultados(argumentos.vitest, argumentos.junit, front)
    except Falla as falla:
        print(str(falla), file=sys.stderr)
        return 1
    traza = escribir(historias, escenarios, reglas, None)
    informe = escribir(historias, escenarios, reglas, resultados)
    if avisos:
        informe += "\n## Avisos\n\n" + "\n".join(f"- {aviso}" for aviso in avisos) + "\n"
    motivos = datos_reales(traza, "La matriz") + datos_reales(informe, "El informe")
    if motivos:
        print("\n".join(dict.fromkeys(motivos)) + "\nNo se escribió nada.", file=sys.stderr)
        return 1
    if argumentos.comprobar:
        vigente = salida.read_text(encoding="utf-8") if salida.is_file() else ""
        if vigente != traza:
            errores.append(f"{salida.name} no está al día. Se regenera con scripts/matriz_cumplimiento.py --front "
                           "y se versiona en el mismo cambio.")
    else:
        salida.write_text(traza, encoding="utf-8")
    if argumentos.informe is not None:
        with argumentos.informe.open("a", encoding="utf-8") as destino:
            destino.write(informe)
    huecos = sum(1 for e in escenarios if e.estado == SIN_PRUEBA)
    huecos += sum(1 for h in historias if h.estado == SIN_ESCENARIO)
    huecos += sum(1 for r in reglas if r.estado in (SIN_PRUEBA, "Prueba nombrada que no existe"))
    pendientes = sum(1 for e in escenarios if e.estado in PENDIENTES)
    for aviso in avisos:
        print(f"Aviso. {aviso}", file=sys.stderr)
    for error in errores:
        print(error, file=sys.stderr)
    print(f"Matriz de cumplimiento de las specs 007 y 008. {len(historias)} historias, {len(escenarios)} escenarios, "
          f"{len(reglas)} reglas, {pendientes} escenarios pendientes con su razón, {huecos} "
          f"{'hueco' if huecos == 1 else 'huecos'}.")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
