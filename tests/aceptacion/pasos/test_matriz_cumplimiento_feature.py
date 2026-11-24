"""Pasos de los escenarios de US-90 de matriz_cumplimiento.feature (spec 008), con pytest-bdd en español (T055).

El .feature manda. Cada escenario corre scripts/matriz_cumplimiento.py como proceso aparte, como lo corre la integración
continua, sobre las specs del Back o sobre una copia en tmp_path, y con un Front espejo armado en tmp_path. El espejo
trae, por cada escenario @delegado_a_vitest o @playwright de las specs 007 y 008, una prueba con su título exacto, o con
el título que nombra su enlace en cumplimiento_razones.toml, y deja fuera los escenarios que ese archivo marca pendientes.
Así la prueba no depende de la copia de trabajo del Front, y la corrida contra el Front real queda para la integración
continua y para la regeneración de cumplimiento.md. Los reportes de Vitest y de pytest de cada escenario son inventados y
nombran solo pruebas del espejo y del Back.

Sin la variable ABET_FRONT_RAIZ, la prueba final que compara cumplimiento.md con el Front real se omite con su razón.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from pytest_bdd.feature import get_features

RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/matriz_cumplimiento.feature"
GENERADOR = RAIZ / "scripts" / "matriz_cumplimiento.py"
CARPETA_008 = "008-ciclo-quimica-industrial"
RAZONES = RAIZ / "specs" / CARPETA_008 / "cumplimiento_razones.toml"
CUMPLIMIENTO = RAIZ / "specs" / CARPETA_008 / "cumplimiento.md"
CI = RAIZ / ".github" / "workflows" / "ci.yml"
SPECS_DE_LA_MATRIZ = ("007-experiencia-por-cuenta", CARPETA_008)
TRAMOS = ("Catálogo", "Alcance", "Periodo", "Generador", "Carga", "R-17", "Avance", "Sistema visual", "Conciliación",
          "Ensayo", "Siembra", "Humo", "Guía", "Privacidad", "Cierre")
ESTADOS = ("Con prueba", "Pendiente por decisión", "Pendiente de tarea", "Sin prueba", "Sin escenario", "Con huecos")
PRUEBA_DEL_TOPE = "test_br_r17_08_142_mediciones_llenan_la_tabla_hasta_la_fila_184"
OCHO_CIFRAS = re.compile(r"(?<![0-9A-Za-z])[0-9]{8}(?![0-9A-Za-z])")
CORREO = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
# Fechas inventadas de dos corridas, en milisegundos desde 1970 como las escribe Vitest.
CORRIDA_A = datetime(2026, 11, 23, 14, 5, tzinfo=UTC)
CORRIDA_B = datetime(2026, 11, 24, 9, 30, tzinfo=UTC)


def fecha(corrida: datetime) -> str:
    return corrida.strftime("%Y-%m-%d %H:%M UTC")


@scenario(FEATURE, "Cada historia del flujo tiene escenario, prueba y corrida")
def test_cada_historia_tiene_escenario_prueba_y_corrida() -> None:
    """T055."""


@scenario(FEATURE, "Una historia de la spec 008 sin escenario hace fallar la generación")
def test_una_historia_sin_escenario_hace_fallar_la_generacion() -> None:
    """T055."""


@scenario(FEATURE, "Una regla con prueba nombrada no es un hueco aunque no tenga escenario")
def test_una_regla_con_prueba_nombrada_no_es_un_hueco() -> None:
    """T055."""


@scenario(FEATURE, "Un escenario delegado a Vitest se busca en el Front por su título exacto")
def test_un_escenario_delegado_se_busca_por_su_titulo_exacto() -> None:
    """T055."""


@scenario(FEATURE, "Lo pendiente por decisión se distingue de lo olvidado")
def test_lo_pendiente_por_decision_se_distingue_de_lo_olvidado() -> None:
    """T055."""


@scenario(FEATURE, "Una etiqueta que no liga con ninguna historia hace fallar la generación")
def test_una_etiqueta_sin_historia_hace_fallar_la_generacion() -> None:
    """T055."""


@scenario(FEATURE, "El tramo de la capacitación queda en una sola vista")
def test_el_tramo_de_la_capacitacion_queda_en_una_sola_vista() -> None:
    """T055."""


@scenario(FEATURE, "La integración continua corre la matriz y el archivo versionado no cambia con cada corrida")
def test_la_integracion_continua_corre_la_matriz() -> None:
    """T055."""


@scenario(FEATURE, "La matriz no trae datos reales")
def test_la_matriz_no_trae_datos_reales() -> None:
    """T055."""


# Front espejo y reportes inventados

@dataclass
class Prueba:
    archivo: str
    titulo: str


@dataclass
class Matriz:
    """Estado del escenario, con las specs que lee el generador, el Front espejo y las salidas de cada corrida."""

    tmp: Path
    specs: Path = RAIZ / "specs"
    front: Path | None = None
    pruebas: list[Prueba] = field(default_factory=list)
    vitest: Path | None = None
    junit: Path | None = None
    corridas: list[dict[str, Any]] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)

    def copiar_specs(self) -> Path:
        if self.specs == RAIZ / "specs":
            destino = self.tmp / "specs"
            shutil.copytree(RAIZ / "specs", destino)
            self.specs = destino
        return self.specs

    @property
    def ultima(self) -> dict[str, Any]:
        assert self.corridas, "el escenario no generó la matriz"
        return self.corridas[-1]


def _razones() -> dict[str, Any]:
    return tomllib.loads(RAZONES.read_text(encoding="utf-8"))


def _escenarios_del_front(specs: Path) -> list[tuple[str, str, set[str]]]:
    """Archivo relativo a specs/, título y etiquetas de cada escenario de pantalla o de navegador de las specs 007 y 008."""
    escenarios = []
    for carpeta in SPECS_DE_LA_MATRIZ:
        for ruta in sorted((specs / carpeta / "aceptacion").glob("*.feature")):
            [feature] = get_features([str(ruta)])
            for escenario in feature.scenarios.values():
                etiquetas = set(escenario.tags)
                if etiquetas & {"delegado_a_vitest", "playwright"}:
                    escenarios.append((ruta.relative_to(specs).as_posix(), escenario.name, etiquetas))
    return escenarios


def armar_espejo(destino: Path, specs: Path) -> list[Prueba]:
    """Front en tmp_path con una prueba por escenario de pantalla o de navegador, con el título que busca la matriz."""
    razones = _razones()
    pendientes_por_historia = {historia for historia, razon in razones.get("historias", {}).items() if "estado" in razon}
    enlaces: dict[tuple[str, str], list[Prueba]] = {}
    pendientes: set[tuple[str, str]] = set()
    for entrada in razones.get("escenarios", []):
        clave = (entrada["archivo"], entrada["escenario"])
        if "pruebas" in entrada:
            enlaces[clave] = [Prueba(p["archivo"], p["titulo"]) for p in entrada["pruebas"]]
        else:
            pendientes.add(clave)
    pruebas: list[Prueba] = []
    for archivo, titulo, etiquetas in _escenarios_del_front(specs):
        historias = {etiqueta for etiqueta in etiquetas if etiqueta.startswith("US-")}
        if (archivo, titulo) in pendientes or historias & pendientes_por_historia:
            continue
        defecto = "e2e/espejo.spec.ts" if "playwright" in etiquetas else "tests/espejo.test.tsx"
        pruebas += enlaces.get((archivo, titulo), [Prueba(defecto, titulo)])
    for prueba in pruebas:
        ruta = destino / prueba.archivo
        ruta.parent.mkdir(parents=True, exist_ok=True)
        llamada = "test" if prueba.archivo.startswith("e2e/") else "it"
        with ruta.open("a", encoding="utf-8") as salida:
            salida.write(f"{llamada}({json.dumps(prueba.titulo, ensure_ascii=False)}, () => {{}});\n")
    # Los archivos del Front que nombran las líneas **Prueba** de las specs vivas, vacíos.
    for spec_viva in (specs / "features").glob("*/*.spec.md"):
        for linea in spec_viva.read_text(encoding="utf-8").splitlines():
            if "**Prueba**" in linea:
                for nombre in re.findall(r"`((?:tests|e2e)/[^`]+\.tsx?)`", linea):
                    (destino / nombre).parent.mkdir(parents=True, exist_ok=True)
                    (destino / nombre).touch()
    return pruebas


def reporte_vitest(ruta: Path, front: Path, pruebas: list[Prueba], corrida: datetime,
                   fallidas: frozenset[str] = frozenset()) -> Path:
    """Reporte JSON con la forma del reporter json de Vitest, con cada prueba del espejo y su resultado."""
    por_archivo: dict[str, list[dict[str, Any]]] = {}
    for prueba in pruebas:
        if prueba.archivo.startswith("e2e/"):
            continue
        estado = "failed" if prueba.titulo in fallidas else "passed"
        por_archivo.setdefault(prueba.archivo, []).append(
            {"ancestorTitles": [], "fullName": prueba.titulo, "title": prueba.titulo, "status": estado})
    ruta.write_text(json.dumps({
        "startTime": int(corrida.timestamp() * 1000),
        "success": not fallidas,
        "testResults": [{"name": str(front / archivo), "assertionResults": resultados}
                        for archivo, resultados in sorted(por_archivo.items())],
    }, ensure_ascii=False), encoding="utf-8")
    return ruta


def generar(ctx: Matriz, *extra: str, nombre: str = "corrida") -> dict[str, Any]:
    """Corre el generador como proceso aparte y guarda su código, su salida, cumplimiento.md y el informe."""
    assert ctx.front is not None, "el escenario no armó el Front"
    carpeta = ctx.tmp / f"{nombre}_{len(ctx.corridas)}"
    carpeta.mkdir()
    salida, informe = carpeta / "cumplimiento.md", carpeta / "informe.md"
    argumentos = [sys.executable, str(GENERADOR), "--specs", str(ctx.specs), "--front", str(ctx.front),
                  "--salida", str(salida), "--informe", str(informe)]
    if ctx.vitest is not None:
        argumentos += ["--vitest", str(ctx.vitest)]
    if ctx.junit is not None:
        argumentos += ["--junit", str(ctx.junit)]
    entorno = {k: v for k, v in os.environ.items() if k != "PYTEST_ADDOPTS"}
    proceso = subprocess.run([*argumentos, *extra], cwd=ctx.tmp, capture_output=True, text=True, env=entorno,
                             timeout=300, check=False)
    corrida = {"codigo": proceso.returncode, "stdout": proceso.stdout, "stderr": proceso.stderr,
               "matriz": salida.read_text(encoding="utf-8") if salida.exists() else None,
               "informe": informe.read_text(encoding="utf-8") if informe.exists() else None}
    ctx.corridas.append(corrida)
    return corrida


def fila(texto: str | None, primera_celda: str) -> list[str]:
    """Celdas de la fila de una tabla Markdown cuya primera celda es primera_celda."""
    assert texto is not None, "la corrida no escribió la matriz"
    for linea in texto.splitlines():
        if linea.startswith("|"):
            celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
            if celdas and celdas[0] == primera_celda:
                return celdas
    raise AssertionError(f"la matriz no tiene la fila {primera_celda}")


def primera_tabla(texto: str) -> list[list[str]]:
    filas: list[list[str]] = []
    for linea in texto.splitlines():
        if linea.startswith("|"):
            filas.append([c.strip() for c in linea.strip().strip("|").split("|")])
        elif filas:
            break
    return filas


@pytest.fixture
def ctx(tmp_path: Path) -> Matriz:
    matriz = Matriz(tmp_path)
    matriz.front = tmp_path / "front"
    matriz.front.mkdir()
    return matriz


def _con_espejo(ctx: Matriz) -> None:
    assert ctx.front is not None
    if not ctx.pruebas:
        ctx.pruebas = armar_espejo(ctx.front, ctx.specs)


# Dado

@given(parsers.re(r"US-59 con su escenario en (?P<archivo>\S+) y su prueba aprobada en el reporte de Vitest"))
def _us_59_aprobada(ctx: Matriz, archivo: str) -> None:
    assert (RAIZ / archivo).is_file(), archivo
    _con_espejo(ctx)
    ctx.vitest = reporte_vitest(ctx.tmp / "vitest.json", ctx.front, ctx.pruebas, CORRIDA_A)
    ctx.extras["archivo"] = Path(archivo).name


@given("una historia US de prueba en una copia de spec.md sin ningún escenario con su etiqueta")
def _historia_sin_escenario(ctx: Matriz) -> None:
    specs = ctx.copiar_specs()
    spec = specs / CARPETA_008 / "spec.md"
    texto = spec.read_text(encoding="utf-8")
    nueva = "### US-998: Historia de prueba sin escenario (Priority: P3)\n\nComo nadie, quiero nada.\n\n---\n\n"
    spec.write_text(texto.replace("### US-90:", nueva + "### US-90:", 1), encoding="utf-8")
    assert "### US-998:" in spec.read_text(encoding="utf-8")
    ctx.extras["historia"] = "US-998"
    _con_espejo(ctx)


@given(parsers.re(r"BR-R17-08 en una copia de r17\.spec\.md cuya línea \*\*Prueba\*\* nombra solo "
                  r"(?P<prueba>test_[a-z0-9_]+) de (?P<archivo>tests/\S+\.py) y ningún escenario"))
def _regla_con_prueba_nombrada(ctx: Matriz, prueba: str, archivo: str) -> None:
    assert f"def {prueba}(" in (RAIZ / archivo).read_text(encoding="utf-8"), f"{archivo} no define {prueba}"
    specs = ctx.copiar_specs()
    spec = specs / "features" / "r17" / "r17.spec.md"
    texto = spec.read_text(encoding="utf-8")
    bloque = re.search(r"### BR-R17-08:.*?(?=\n### )", texto, re.S)
    assert bloque is not None
    linea = re.search(r"^- \*\*Prueba\*\*.*$", bloque.group(0), re.M)
    assert linea is not None and "«" in linea.group(0), "la línea **Prueba** de BR-R17-08 ya no nombra escenarios"
    nueva = f"- **Prueba**: `{prueba}` de `{archivo}`."
    spec.write_text(texto.replace(bloque.group(0), bloque.group(0).replace(linea.group(0), nueva)), encoding="utf-8")
    ctx.extras.update(regla="BR-R17-08", prueba=prueba)
    _con_espejo(ctx)


@given("un escenario con la etiqueta @delegado_a_vitest")
def _escenario_delegado(ctx: Matriz) -> None:
    _con_espejo(ctx)
    archivo, titulo, _ = next((a, t, e) for a, t, e in _escenarios_del_front(ctx.specs)
                               if a.startswith(CARPETA_008) and "delegado_a_vitest" in e
                               and any(p.titulo == t for p in ctx.pruebas))
    ctx.extras.update(archivo=archivo, titulo=titulo)


@given(parsers.re(r"(?P<historia>US-66), que espera a D-47 y a D-51"))
def _us_66(ctx: Matriz, historia: str) -> None:
    razon = _razones()["historias"][historia]
    assert razon["estado"] == "Pendiente por decisión" and "D-47" in razon["razon"] and "D-51" in razon["razon"], razon
    ctx.extras["historia"] = historia
    _con_espejo(ctx)


@given(parsers.re(r"un escenario de prueba con la etiqueta (?P<etiqueta>@US-[0-9]+)"))
def _etiqueta_sin_historia(ctx: Matriz, etiqueta: str) -> None:
    specs = ctx.copiar_specs()
    (specs / CARPETA_008 / "aceptacion" / "prueba_etiqueta.feature").write_text(
        "# language: es\nCaracterística: Etiqueta de prueba\n\n"
        f"  {etiqueta} @spec008 @corte1\n  Escenario: Un escenario con una etiqueta sin historia\n"
        "    Cuando se genera la matriz\n    Entonces no pasa nada\n", encoding="utf-8")
    ctx.extras["etiqueta"] = etiqueta
    _con_espejo(ctx)


# Cuando

@when("se genera la matriz")
def _se_genera(ctx: Matriz) -> None:
    _con_espejo(ctx)
    generar(ctx)


@when("se genera la matriz con la ruta del Front")
def _se_genera_con_el_front(ctx: Matriz) -> None:
    _con_espejo(ctx)
    generar(ctx)
    # El mismo Front con el título del escenario cambiado en una sola letra, la primera en minúscula.
    titulo = ctx.extras["titulo"]
    for ruta in ctx.front.rglob("*.test.tsx"):
        texto = ruta.read_text(encoding="utf-8")
        literal = json.dumps(titulo, ensure_ascii=False)
        if literal in texto:
            ruta.write_text(texto.replace(literal, json.dumps(titulo[0].lower() + titulo[1:], ensure_ascii=False)),
                            encoding="utf-8")
    generar(ctx, nombre="sin_titulo")


@when("la integración continua genera la matriz dos veces con resultados de corrida distintos")
def _dos_corridas(ctx: Matriz) -> None:
    _con_espejo(ctx)
    vitest_pruebas = [p for p in ctx.pruebas if not p.archivo.startswith("e2e/")]
    fallida = vitest_pruebas[0].titulo
    ctx.vitest = reporte_vitest(ctx.tmp / "vitest_a.json", ctx.front, ctx.pruebas, CORRIDA_A)
    generar(ctx, nombre="a")
    ctx.vitest = reporte_vitest(ctx.tmp / "vitest_b.json", ctx.front, ctx.pruebas, CORRIDA_B, frozenset({fallida}))
    generar(ctx, nombre="b")
    ctx.extras["fallida"] = fallida


# Entonces

@then(parsers.re(r"la fila de US-59 dice el archivo del escenario, la prueba y «(?P<resultado>Aprobada)» con la fecha "
                 r"de la corrida del reporte"))
def _fila_us_59(ctx: Matriz, resultado: str) -> None:
    corrida = ctx.ultima
    assert corrida["codigo"] == 0, corrida["stdout"] + corrida["stderr"]
    celdas = fila(corrida["informe"], "US-59")
    texto = " | ".join(celdas)
    pruebas_us_59 = {p.archivo for p in ctx.pruebas if p.archivo == "tests/pantallas/MisSecciones.test.tsx"}
    assert ctx.extras["archivo"] in texto, texto
    assert pruebas_us_59 and all(archivo in texto for archivo in pruebas_us_59), texto
    assert f"{resultado} el {fecha(CORRIDA_A)}" in celdas[-1], celdas
    # La traza versionada dice el archivo y la prueba, pero no el resultado ni la fecha de la corrida.
    traza = " | ".join(fila(corrida["matriz"], "US-59"))
    assert ctx.extras["archivo"] in traza and "tests/pantallas/MisSecciones.test.tsx" in traza, traza
    assert resultado not in traza and fecha(CORRIDA_A) not in corrida["matriz"]


@then(parsers.re(r"la fila de esa historia dice «(?P<estado>Sin escenario)»"))
def _fila_sin_escenario(ctx: Matriz, estado: str) -> None:
    assert fila(ctx.ultima["matriz"], ctx.extras["historia"])[-1] == estado


@then(parsers.re(r"la generación termina con código (?P<codigo>[0-9]+)$"))
def _termina_con(ctx: Matriz, codigo: str) -> None:
    corrida = ctx.ultima
    assert corrida["codigo"] == int(codigo), corrida["stdout"] + corrida["stderr"]
    if "historia" in ctx.extras:
        assert ctx.extras["historia"] in corrida["stderr"], corrida["stderr"]


@then("su fila dice la prueba nombrada y no cuenta como hueco")
def _regla_sin_hueco(ctx: Matriz) -> None:
    corrida = ctx.ultima
    assert corrida["codigo"] == 0, corrida["stdout"] + corrida["stderr"]
    celdas = fila(corrida["matriz"], ctx.extras["regla"])
    assert ctx.extras["prueba"] in " | ".join(celdas), celdas
    assert celdas[-1] == "Con prueba nombrada", celdas
    assert "0 huecos" in corrida["stdout"], corrida["stdout"]


@then("la matriz lo busca en las pruebas de Vitest por su título exacto")
def _busca_por_titulo(ctx: Matriz) -> None:
    corrida = ctx.corridas[0]
    assert corrida["codigo"] == 0, corrida["stdout"] + corrida["stderr"]
    filas = [linea for linea in corrida["matriz"].splitlines() if f"| {ctx.extras['titulo']} |" in linea]
    assert len(filas) == 1 and "Vitest tests/espejo.test.tsx" in filas[0] and filas[0].endswith("| Con prueba |"), filas


@then("un título que no existe en el Front hace fallar la generación y nombra el escenario")
def _titulo_inexistente(ctx: Matriz) -> None:
    corrida = ctx.ultima
    assert corrida["codigo"] == 1, corrida["stdout"] + corrida["stderr"]
    assert f"«{ctx.extras['titulo']}»" in corrida["stderr"], corrida["stderr"]
    filas = [linea for linea in corrida["matriz"].splitlines() if f"| {ctx.extras['titulo']} |" in linea]
    assert len(filas) == 1 and filas[0].endswith("| Sin prueba |"), filas


@then(parsers.re(r"su fila dice «(?P<estado>Pendiente por decisión)» y no cuenta como hueco"))
def _pendiente_por_decision(ctx: Matriz, estado: str) -> None:
    corrida = ctx.ultima
    assert corrida["codigo"] == 0, corrida["stdout"] + corrida["stderr"]
    celdas = fila(corrida["matriz"], ctx.extras["historia"])
    assert celdas[-1] == estado, celdas
    assert "D-47" in " ".join(celdas) and "D-51" in " ".join(celdas), celdas
    assert "0 huecos" in corrida["stdout"], corrida["stdout"]


@then(parsers.re(r"la generación termina con código (?P<codigo>[0-9]+) y nombra la etiqueta"))
def _termina_y_nombra(ctx: Matriz, codigo: str) -> None:
    corrida = ctx.ultima
    assert corrida["codigo"] == int(codigo), corrida["stdout"] + corrida["stderr"]
    assert re.search(rf"{re.escape(ctx.extras['etiqueta'])}(?![0-9])", corrida["stderr"]), corrida["stderr"]


@then(parsers.re(r"su primera tabla lista, en el orden del flujo, .+, con el estado de cada uno"))
def _primera_tabla(ctx: Matriz) -> None:
    corrida = ctx.ultima
    assert corrida["codigo"] == 0, corrida["stdout"] + corrida["stderr"]
    tabla = primera_tabla(corrida["matriz"])
    assert tabla[0][0] == "Tramo" and tabla[0][-1] == "Estado", tabla[0]
    filas = tabla[2:]
    assert tuple(f[0] for f in filas) == TRAMOS, [f[0] for f in filas]
    for celdas in filas:
        assert celdas[-1].startswith(ESTADOS), celdas
        assert re.search(r"US-[0-9]+", celdas[1]), celdas
    # El avance espera a D-32 por US-80, y la matriz lo dice en vez de darlo por cumplido. El humo tiene su prueba desde
    # T053 del Front (cambio del 2026-11-23 del cierre de la spec 008).
    assert fila(corrida["matriz"], "Humo")[-1] == "Con prueba"
    assert "US-80" in fila(corrida["matriz"], "Avance")[-1]


@then("cumplimiento.md sale igual las dos veces")
def _igual_dos_veces(ctx: Matriz) -> None:
    a, b = ctx.corridas
    assert a["codigo"] == b["codigo"] == 0, a["stderr"] + b["stderr"]
    assert a["matriz"] == b["matriz"]
    assert a["informe"] != b["informe"]


@then("la fecha y el resultado de cada corrida quedan solo en el informe de la integración continua")
def _solo_en_el_informe(ctx: Matriz) -> None:
    a, b = ctx.corridas
    assert fecha(CORRIDA_A) in a["informe"] and fecha(CORRIDA_B) in b["informe"]
    assert "Fallida" not in a["informe"] and "Fallida" in b["informe"]
    for texto in (fecha(CORRIDA_A), fecha(CORRIDA_B), "Aprobada", "Fallida", "Sin corrida"):
        assert texto not in a["matriz"], texto
    # La integración continua corre el generador contra el Front, compara la traza y deja el informe en su resumen.
    flujo = CI.read_text(encoding="utf-8")
    assert re.search(r"scripts/matriz_cumplimiento\.py[^\n]*--comprobar", flujo), "la CI no compara cumplimiento.md"
    assert re.search(r"--informe \"\$GITHUB_STEP_SUMMARY\"", flujo), "la CI no deja el informe en su resumen"


@then("la matriz no trae ningún número de ocho cifras ni ningún correo fuera de example.invalid")
def _sin_datos_reales(ctx: Matriz) -> None:
    corrida = ctx.ultima
    assert corrida["codigo"] == 0, corrida["stdout"] + corrida["stderr"]
    for texto in (corrida["matriz"], corrida["informe"], corrida["stdout"]):
        assert not OCHO_CIFRAS.search(texto), OCHO_CIFRAS.search(texto)
        assert all(c.endswith("@example.invalid") for c in CORREO.findall(texto)), CORREO.findall(texto)
    # Lo que no debe pasar. Un título con un código fuera del rango inventado detiene la generación sin escribirla.
    specs = ctx.copiar_specs()
    codigo = "2" + "0" * 6 + "4"
    feature = specs / CARPETA_008 / "aceptacion" / "periodo_elegido.feature"
    texto = feature.read_text(encoding="utf-8")
    feature.write_text(texto.replace("Escenario: Pedir otro periodo no agrega secciones ajenas",
                                     f"Escenario: Pedir otro periodo no agrega secciones ajenas {codigo}", 1),
                       encoding="utf-8")
    con_codigo = generar(ctx, nombre="con_codigo")
    assert con_codigo["codigo"] == 1, con_codigo["stdout"] + con_codigo["stderr"]
    assert con_codigo["matriz"] is None and con_codigo["informe"] is None
    assert codigo not in con_codigo["stdout"] + con_codigo["stderr"]


# Fuera de los escenarios

@pytest.mark.skipif(not os.environ.get("ABET_FRONT_RAIZ"),
                    reason="Sin ABET_FRONT_RAIZ la comparación con el Front real queda en la integración continua (T055).")
def test_cumplimiento_md_esta_al_dia_con_el_front_real(tmp_path: Path) -> None:
    proceso = subprocess.run([sys.executable, str(GENERADOR), "--front", os.environ["ABET_FRONT_RAIZ"], "--comprobar"],
                             cwd=RAIZ, capture_output=True, text=True, timeout=300, check=False,
                             env={k: v for k, v in os.environ.items() if k != "PYTEST_ADDOPTS"})
    assert proceso.returncode == 0, proceso.stdout + proceso.stderr
    assert CUMPLIMIENTO.is_file()


def _pasos_del_job_de_pruebas() -> list[str]:
    """Los pasos del job «pruebas» de ci.yml, cada uno con su texto, en el orden en que corren. Se leen por su sangría,
    porque PyYAML no está entre las dependencias del Back."""
    flujo = CI.read_text(encoding="utf-8")
    job = flujo.split("\n  pruebas:\n", 1)[1]
    job = re.split(r"\n  [a-z]+:\n", job, maxsplit=1)[0]
    pasos = job.split("\n    steps:\n", 1)[1]
    return re.split(r"\n(?=      - )", pasos)


def test_la_ci_clona_el_front_antes_de_pytest_y_le_pasa_su_raiz() -> None:
    # Corrección del 2026-11-23 (traza de los requerimientos). Sin el Front clonado antes de pytest y sin
    # ABET_FRONT_RAIZ, los dos escenarios de US-88 que nombran el Front y la comparación de cumplimiento.md con el Front
    # real terminan en skip en la CI (FR-022 y FR-026).
    pasos = _pasos_del_job_de_pruebas()
    [clon] = [i for i, paso in enumerate(pasos) if "git clone" in paso and "../front_ci" in paso]
    [pytest_paso] = [i for i, paso in enumerate(pasos) if re.search(r"uv run [^\n]*pytest -q", paso)]
    assert clon < pytest_paso, "la CI clona el Front después de pytest"
    assert "--branch \"$RAMA\"" in pasos[clon] and "--branch develop" in pasos[clon], "el clon perdió su respaldo"
    raiz = re.search(r"\n\s+ABET_FRONT_RAIZ: ([^\n]+)", pasos[pytest_paso])
    assert raiz, "el paso de pytest no fija ABET_FRONT_RAIZ"
    assert raiz.group(1) == "${{ github.workspace }}/../front_ci", raiz.group(1)


# Una orden de shell que baja un paquete en el momento: npx, bunx, pnpm dlx o yarn dlx, npm exec o npm x con cualquier
# opción o espacio entre npm y la suborden, y npm install, npm i o npm add con un paquete, que no lee el package-lock.json.
_OPCIONES_DE_NPM = r"(\s+-\S+(\s+[^-\s]\S*)?)*"
INSTALA_A_PEDIDO = re.compile(r"(^|[\s;&|(])((npx|bunx|(pnpm|yarn)\s+dlx|npm" + _OPCIONES_DE_NPM + r"\s+(exec|x))(?=\s|$)"
                              r"|npm" + _OPCIONES_DE_NPM + r"\s+(i|in|install|add)(\s+-\S+)*\s+[^-\s])")


def test_la_ci_corre_vitest_con_el_binario_que_instala_npm_ci_y_sin_npx() -> None:
    # Corrección del 2026-11-24 (SonarCloud, githubactions:S6505 y S8543 en el PR #54). npx y npm exec pueden bajar en
    # el momento un paquete sin versión fija y correr sus scripts de instalación. La CI usa solo lo que fija el
    # package-lock.json del Front, instalado con npm ci --ignore-scripts.
    instrucciones = [linea.split("#", 1)[0] for linea in CI.read_text(encoding="utf-8").splitlines()
                     if not linea.lstrip().startswith("#")]
    a_pedido = [linea.strip() for linea in instrucciones if INSTALA_A_PEDIDO.search(linea)]
    assert not a_pedido, f"ci.yml instala paquetes a pedido: {a_pedido}"
    pasos = _pasos_del_job_de_pruebas()
    [vitest] = [paso for paso in pasos if "vitest" in paso and "working-directory: ../front_ci" in paso]
    assert "npm ci --ignore-scripts" in vitest, "el paso de Vitest perdió --ignore-scripts"
    assert "./node_modules/.bin/vitest run --reporter=json --outputFile=../informes_ci/vitest.json" in vitest, vitest


@pytest.mark.parametrize("orden", [
    "npx vitest run", "cd ../front_ci && npx vitest run", "bunx vitest", "pnpm dlx vitest", "yarn  dlx vitest",
    "npm exec vitest", "npm  exec vitest", "npm --yes exec -- vitest --version", "npm -y x vitest",
    "npm --prefix ../front_ci exec vitest", "npm\texec vitest", "npm install --no-save vitest", "npm i vitest",
    "npm add vitest@3", "npm install -D vitest",
])
def test_el_patron_de_la_ci_detecta_cada_forma_de_bajar_un_paquete_en_el_momento(orden: str) -> None:
    # Corrección del 2026-11-24 (verificadores del PR #54). El patrón de antes pedía «npm exec» con un solo espacio, así
    # que «npm --yes exec» y «npm  exec» pasaban, y no veía «npm install» con un paquete sin versión fija.
    assert INSTALA_A_PEDIDO.search(orden), orden


@pytest.mark.parametrize("orden", [
    "npm ci --ignore-scripts", "npm run build", "npm ci", "npm install", "npm install --ignore-scripts",
    "./node_modules/.bin/vitest run --reporter=json --outputFile=../informes_ci/vitest.json", "npm run exec-tareas",
    "npm run x", "uv run --frozen --no-build pytest -q", "echo npxx", "pnpm exec vitest",
])
def test_el_patron_de_la_ci_no_marca_lo_que_usa_el_package_lock(orden: str) -> None:
    assert not INSTALA_A_PEDIDO.search(orden), orden


def _espejo_sin_correr(tmp_path: Path) -> Matriz:
    matriz = Matriz(tmp_path)
    matriz.front = tmp_path / "front"
    matriz.front.mkdir()
    _con_espejo(matriz)
    return matriz


def test_una_prueba_que_solo_es_it_todo_no_cubre_su_escenario(tmp_path: Path) -> None:
    # FR-026. Un it.todo o un skip con el título del escenario no es su prueba, y el escenario queda como hueco.
    matriz = _espejo_sin_correr(tmp_path)
    titulo = next(p.titulo for p in matriz.pruebas if p.archivo == "tests/espejo.test.tsx")
    literal = json.dumps(titulo, ensure_ascii=False)
    for variante in ("it.todo", "it.skip"):
        ruta = matriz.front / "tests" / "espejo.test.tsx"
        texto = ruta.read_text(encoding="utf-8").replace(f"it({literal}, () => {{}});", f"{variante}({literal});")
        ruta.write_text(texto, encoding="utf-8")
        corrida = generar(matriz, nombre=variante.replace(".", "_"))
        assert corrida["codigo"] == 1, corrida["stdout"] + corrida["stderr"]
        assert f"«{titulo}»" in corrida["stderr"] and "solo como it.todo o skip" in corrida["stderr"], corrida["stderr"]
        armar_de_nuevo = ruta.read_text(encoding="utf-8").replace(f"{variante}({literal});", f"it({literal}, () => {{}});")
        ruta.write_text(armar_de_nuevo, encoding="utf-8")
    assert generar(matriz, nombre="de_vuelta")["codigo"] == 0


def test_un_enlace_o_una_razon_a_algo_que_no_existe_hace_fallar_la_generacion(tmp_path: Path) -> None:
    # Cada excepción del archivo de razones apunta a algo real. Un enlace a una prueba que el Front no tiene, una razón a
    # un escenario que no existe y una historia fuera de las specs 007 y 008 hacen fallar la generación.
    matriz = _espejo_sin_correr(tmp_path)
    razones = RAZONES.read_text(encoding="utf-8")
    casos = {
        "enlace": (razones.replace('titulo = "sin secciones muestra un texto y no una lista vacía"',
                                   'titulo = "una prueba que no existe en el Front"', 1),
                   "«una prueba que no existe en el Front», que no está en tests/pantallas/MisSecciones.test.tsx"),
        "escenario": (razones + '\n[[escenarios]]\narchivo = "008-ciclo-quimica-industrial/aceptacion/'
                      'guia_y_privacidad.feature"\nescenario = "Un escenario que no existe"\nestado = "Pendiente de '
                      'tarea"\nrazon = "Ninguna."\n', "«Un escenario que no existe» nombra un escenario que no está"),
        "historia": (razones + '\n[historias.US-20]\nestado = "Pendiente de tarea"\nrazon = "Ninguna."\n',
                     "US-20 nombra una historia que no está en las specs 007 y 008"),
    }
    for nombre, (texto, mensaje) in casos.items():
        ruta = tmp_path / f"razones_{nombre}.toml"
        ruta.write_text(texto, encoding="utf-8")
        corrida = generar(matriz, "--razones", str(ruta), nombre=nombre)
        assert corrida["codigo"] == 1 and mensaje in corrida["stderr"], (nombre, corrida["stderr"])


def test_comprobar_no_escribe_y_falla_si_la_traza_cambio(tmp_path: Path) -> None:
    # --comprobar es lo que corre la CI. No escribe cumplimiento.md, pasa si está al día y falla si no.
    matriz = _espejo_sin_correr(tmp_path)
    primera = generar(matriz, nombre="primera")
    assert primera["codigo"] == 0, primera["stderr"]
    vigente = tmp_path / "vigente.md"
    vigente.write_text(primera["matriz"], encoding="utf-8")
    al_dia = generar(matriz, "--comprobar", "--salida", str(vigente), nombre="al_dia")
    assert al_dia["codigo"] == 0, al_dia["stderr"]
    vigente.write_text(primera["matriz"].replace("| Con prueba |", "| Sin prueba |", 1), encoding="utf-8")
    atrasada = generar(matriz, "--comprobar", "--salida", str(vigente), nombre="atrasada")
    assert atrasada["codigo"] == 1 and "vigente.md no está al día" in atrasada["stderr"], atrasada["stderr"]
    assert "| Sin prueba |" in vigente.read_text(encoding="utf-8")
