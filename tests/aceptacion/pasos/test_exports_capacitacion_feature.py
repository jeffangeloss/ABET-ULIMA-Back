"""Pasos de exports_capacitacion.feature (US-74 de la spec 008) y del escenario de las tarjetas de US-87, con pytest-bdd
en español (T034).

El .feature manda. El generador scripts/generar_exports_desde_maestra.py corre como proceso aparte, como lo correría
Jefferson, sobre una tabla maestra y una programación INVENTADAS que estos pasos arman en tmp_path, con las secciones
701 a 703 de 5643 en 2026-1, códigos del rango 99 y profesores inventados. Ningún paso lee la tabla maestra real ni
escribe un export dentro del repositorio. Cada «Entonces» se comprueba con los archivos escritos, leídos con openpyxl y
con el lector y la validación de abet_carga, con el manifiesto y con la salida del proceso, sin dobles del generador.
Estos escenarios no usan base de datos.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import secrets
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from pytest_bdd import given, parsers, scenario, then, when

from abet_carga import lector, validacion
from abet_carga.modelos import ContextoSeccion, PiDelPlan, TipoColumna

Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/exports_capacitacion.feature"
FEATURE_GUIA = "specs/008-ciclo-quimica-industrial/aceptacion/guia_y_privacidad.feature"
GENERADOR = RAIZ / "scripts" / "generar_exports_desde_maestra.py"
COLUMNAS = ("AÑO", "CICLO", "CÓDIGO DEL CURSO", "CURSO", "CICLO DEL CURSO", "SO", "PI", "PROFESOR",
            "CÓDIGO DEL ESTUDIANTE", "SECCIÓN", "CALIFICACIÓN", "ARCHIVO")
PARAMETROS = {"periodo": "2026-1", "asignatura": "5643", "pi": "6.1", "fecha": "2026-07-15-00-00-00"}
OCHO_CIFRAS = re.compile(r"(?<![0-9])[0-9]{8}(?![0-9])")
# La consulta de control Q04 busca estos nombres de columna (db/plataforma/neon/controles_neon.sql).
Q04 = re.compile(r"(apellido|first_name|last_name|correo|email|telefono|dni|nombre)")
PROFESORES = {"701": "Docente Inventado Siete Cero Uno", "702": "Docente Inventado Siete Cero Dos",
              "703": "Docente Inventado Siete Cero Tres"}
# Tabla maestra inventada de los Antecedentes, con la fila del libro, la sección, el código y la calificación. La fila 5
# es de la 701, el código 99000001 es de la 702 y el 99000002 de la 701, como piden los Ejemplos de la fila defectuosa.
BASE = ((2, "701", "99000002", 3), (3, "701", "99000003", 4), (4, "701", "99000007", 2), (5, "701", "99000008", 3),
        (6, "702", "99000001", 2), (7, "702", "99000004", 1), (8, "702", "99000005", 3), (9, "702", "99000006", 4),
        (10, "703", "99000009", 4), (11, "703", "99000010", 3), (12, "703", "99000011", 1))


@dataclass
class Maestra:
    """Filas de la tabla maestra inventada, cada una con las doce columnas, en el orden del libro desde la fila 2."""

    filas: list[dict[str, object]] = field(default_factory=list)
    columnas: tuple[str, ...] = COLUMNAS

    def escribir(self, destino: Path) -> Path:
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Tabla maestra"
        hoja.append(list(self.columnas))
        for fila in self.filas:
            hoja.append([fila.get(columna) for columna in self.columnas])
        libro.save(destino)
        return destino


def _fila(seccion: str, codigo: object, calificacion: object, *, anio: object = 2026, ciclo: object = 1,
          asignatura: object = "5643", pi: object = "6.1") -> dict[str, object]:
    return {"AÑO": anio, "CICLO": ciclo, "CÓDIGO DEL CURSO": asignatura, "CURSO": "QUÍMICA GENERAL",
            "CICLO DEL CURSO": 1, "SO": str(pi).split(".")[0], "PI": pi, "PROFESOR": PROFESORES.get(seccion, "Docente"),
            "CÓDIGO DEL ESTUDIANTE": codigo, "SECCIÓN": seccion, "CALIFICACIÓN": calificacion,
            "ARCHIVO": f"R017_inventado_{seccion}.xlsx"}


def _maestra(ctx: Escenario) -> Maestra:
    return ctx.extras["maestra"]


def _carpeta(ctx: Escenario, nombre: str) -> Path:
    carpeta = ctx.request.getfixturevalue("tmp_path") / nombre
    carpeta.mkdir(exist_ok=True)
    return carpeta


def _programacion(ctx: Escenario) -> Path:
    destino = _carpeta(ctx, "entrada") / "programacion_20261_inventada.csv"
    salida = io.StringIO(newline="")
    escritor = csv.writer(salida, lineterminator="\r\n")
    escritor.writerow(("periodo", "asignatura", "seccion", "correo", "curso_blackboard"))
    for seccion, curso in ctx.extras["programacion"].items():
        escritor.writerow(("2026-1", "5643", seccion, f"docente{seccion}@example.invalid", curso))
    destino.write_bytes(salida.getvalue().encode("utf-8"))
    return destino


def correr(ctx: Escenario, *extra: str, salida: Path | None = None, **cambios: str) -> subprocess.CompletedProcess[str]:
    """Corre el generador como proceso aparte con python -I, sobre la tabla y la programación del escenario."""
    maestra = _maestra(ctx).escribir(_carpeta(ctx, "entrada") / "tabla_maestra_inventada.xlsx")
    parametros = {**PARAMETROS, **cambios}
    argumentos = ["--maestra", str(maestra), "--salida", str(salida or ctx.extras["salida"])]
    if "--ejercicio" not in extra:
        argumentos += ["--programacion", str(_programacion(ctx))]
    for clave, valor in parametros.items():
        argumentos += [f"--{clave}", valor]
    corrida = subprocess.run([sys.executable, "-I", str(GENERADOR), *argumentos, *extra], capture_output=True,
                             text=True, encoding="utf-8", check=False, cwd=ctx.request.getfixturevalue("tmp_path"))
    ctx.extras["corrida"] = corrida
    return corrida


def _exige_exito(corrida: subprocess.CompletedProcess[str]) -> None:
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr


def _exports(carpeta: Path) -> dict[str, Path]:
    """Archivos .xlsx de la carpeta por sección, leída de su nombre."""
    return {re.search(r"_5643_([0-9]+)_fullgc_", ruta.name)[1]: ruta for ruta in sorted(carpeta.glob("*.xlsx"))}


def _leer(ruta: Path) -> tuple[str, list[str], list[tuple[object, ...]]]:
    """Hoja, encabezado y filas de un export, leídos con openpyxl por su cuenta, sin el generador."""
    libro = load_workbook(ruta, read_only=True)
    try:
        hoja = libro.worksheets[0]
        filas = list(hoja.iter_rows(values_only=True))
        return hoja.title, [str(celda) for celda in filas[0]], [tuple(fila) for fila in filas[1:]]
    finally:
        libro.close()


def _leido(ruta: Path) -> Any:
    return lector.leer(ruta.read_bytes(), nombre_archivo=ruta.name)


def _manifiesto(ctx: Escenario, carpeta: Path | None = None) -> dict[str, Any]:
    return json.loads(((carpeta or ctx.extras["salida"]) / "manifiesto.json").read_text(encoding="utf-8"))


def _huellas(carpeta: Path) -> dict[str, str]:
    return {ruta.name: hashlib.sha256(ruta.read_bytes()).hexdigest() for ruta in sorted(carpeta.glob("*.xlsx"))}


def _de_la_seccion(seccion: str, maestra: Maestra) -> list[tuple[str, int]]:
    return [(str(f["CÓDIGO DEL ESTUDIANTE"]), int(f["CALIFICACIÓN"])) for f in maestra.filas
            if f["SECCIÓN"] == seccion and f["PI"] == "6.1" and f["AÑO"] == 2026 and f["CICLO"] == 1
            and f["CÓDIGO DEL CURSO"] == "5643"]


def _salida(ctx: Escenario) -> str:
    corrida = ctx.extras["corrida"]
    return corrida.stdout + corrida.stderr


# Escenarios de US-74

@scenario(FEATURE, "Cada sección da un export que el lector y la validación aceptan sin rechazos")
def test_cada_seccion_da_un_export_aceptado() -> None:
    """T034."""


@scenario(FEATURE, "La ida y vuelta por el lector da los mismos códigos y niveles que la tabla maestra")
def test_la_ida_y_vuelta_por_el_lector() -> None:
    """T034."""


@scenario(FEATURE, "El export trae solo el código y la columna del PI, sin nombres ni el profesor")
def test_el_export_sin_nombres_ni_profesor() -> None:
    """T034."""


@scenario(FEATURE, "Un código con cero a la izquierda se escribe como texto")
def test_un_codigo_con_cero_a_la_izquierda() -> None:
    """T034."""


@scenario(FEATURE, "El curso de cada archivo es el de la programación y no uno armado por el generador")
def test_el_curso_sale_de_la_programacion() -> None:
    """T034."""


@scenario(FEATURE, "Dos corridas dan los mismos archivos byte a byte")
def test_dos_corridas_byte_a_byte() -> None:
    """T034."""


@scenario(FEATURE, "El manifiesto resume cada export sin códigos")
def test_el_manifiesto_sin_codigos() -> None:
    """T034."""


@scenario(FEATURE, "Las filas de otro periodo, otra asignatura u otro PI se omiten y se cuentan")
def test_las_filas_omitidas_se_cuentan() -> None:
    """T034."""


@scenario(FEATURE, "El PI llega por parámetro para la decisión abierta D-48")
def test_el_pi_llega_por_parametro() -> None:
    """T034."""


@scenario(FEATURE, "Una fila defectuosa detiene la generación entera sin mostrar el valor")
def test_una_fila_defectuosa_detiene_todo() -> None:
    """T034, con sus siete Ejemplos."""


@scenario(FEATURE, "Sin la columna CALIFICACIÓN el generador no adivina")
def test_sin_la_columna_calificacion() -> None:
    """T034."""


@scenario(FEATURE, "La carpeta de salida dentro de un repositorio se rechaza")
def test_la_salida_dentro_de_un_repositorio() -> None:
    """T034."""


@scenario(FEATURE, "La salida del generador no muestra códigos ni nombres")
def test_la_salida_sin_codigos_ni_nombres() -> None:
    """T034."""


@scenario(FEATURE, "Un archivo de ejercicio por profesor tiene su propia huella")
def test_un_ejercicio_por_profesor() -> None:
    """T034."""


@scenario(FEATURE_GUIA, "Cada tarjeta de profesor nombra el archivo de su sección según el manifiesto")
def test_cada_tarjeta_nombra_el_archivo_de_su_seccion() -> None:
    """T034, US-87."""


# Dado

@given(parsers.re(r'una tabla maestra inventada con las filas de las secciones "701", "702" y "703" de "5643" en 2026 '
                  r'ciclo 1 con el PI "6\.1"'))
def _tabla_maestra(ctx: Escenario) -> None:
    filas = []
    for numero, (fila, seccion, codigo, calificacion) in enumerate(BASE, start=2):
        assert numero == fila
        filas.append(_fila(seccion, codigo, calificacion))
    ctx.extras["maestra"] = Maestra(filas)


@given(parsers.re(r'la programación inventada con el curso_blackboard "(?P<a>[^"]+)", "(?P<b>[^"]+)" y "(?P<c>[^"]+)"'))
def _programacion_inventada(ctx: Escenario, a: str, b: str, c: str) -> None:
    ctx.extras["programacion"] = {curso.rsplit("_", 1)[1]: curso for curso in (a, b, c)}


@given("una carpeta de salida fuera de todo repositorio git")
def _salida_fuera(ctx: Escenario) -> None:
    salida = ctx.request.getfixturevalue("tmp_path") / "salida"
    assert not any((carpeta / ".git").exists() for carpeta in (salida, *salida.parents))
    ctx.extras["salida"] = salida


@given(parsers.re(r'en la tabla maestra la 702 con "(?P<a>[0-9]+)" en (?P<na>[1-4]), "(?P<b>[0-9]+)" en (?P<nb>[1-4]) '
                  r'y "(?P<c>[0-9]+)" en (?P<nc>[1-4])'))
def _la_702_con(ctx: Escenario, a: str, na: str, b: str, nb: str, c: str, nc: str) -> None:
    maestra = _maestra(ctx)
    maestra.filas = [fila for fila in maestra.filas if fila["SECCIÓN"] != "702"]
    maestra.filas += [_fila("702", codigo, int(nivel)) for codigo, nivel in ((a, na), (b, nb), (c, nc))]


@given(parsers.re(r'en la tabla maestra la columna PROFESOR con "(?P<profesor>[^"]+)" en la 701'))
def _profesor_en_la_701(ctx: Escenario, profesor: str) -> None:
    for fila in _maestra(ctx).filas:
        if fila["SECCIÓN"] == "701":
            fila["PROFESOR"] = profesor
    ctx.extras["profesor"] = profesor


@given("una fila de la 701 con un código de ocho cifras que empieza con cero, armado por la prueba")
def _codigo_con_cero(ctx: Escenario) -> None:
    # El código no se escribe como literal en el repositorio, porque no es del rango 99, y nunca llega a una base.
    codigo = "0" + str(9900000 + 1)
    assert len(codigo) == 8
    _maestra(ctx).filas.append(_fila("701", codigo, 4))
    ctx.extras["codigo_con_cero"] = codigo


@given(parsers.re(r'la programación inventada con el curso_blackboard "(?P<curso>[^"]+)" de la (?P<seccion>[0-9]+)'))
def _curso_de_la_seccion(ctx: Escenario, curso: str, seccion: str) -> None:
    assert ctx.extras["programacion"][seccion] == curso
    ctx.extras["curso"] = (seccion, curso)


@given(parsers.re(r'(?P<periodo>[0-9]+) filas de 2025 ciclo 2, (?P<asignatura>[0-9]+) filas de la asignatura '
                  r'"450002" y (?P<pi>[0-9]+) filas del PI "6\.2" en la tabla maestra'))
def _filas_ajenas(ctx: Escenario, periodo: str, asignatura: str, pi: str) -> None:
    maestra = _maestra(ctx)
    ajenas = ([_fila("701", f"9900010{n}", 2, anio=2025, ciclo=2) for n in range(int(periodo))]
              + [_fila("701", f"9900020{n}", 3, asignatura="450002") for n in range(int(asignatura))]
              + [_fila("701", f"9900030{n}", 4, pi="6.2") for n in range(int(pi))])
    maestra.filas += ajenas
    ctx.extras["ajenas"] = [str(fila["CÓDIGO DEL ESTUDIANTE"]) for fila in ajenas]


@given(parsers.re(r'la tabla maestra con todas sus filas en el PI "(?P<pi>[0-9.]+)"'))
def _todas_en_el_pi(ctx: Escenario, pi: str) -> None:
    for fila in _maestra(ctx).filas:
        fila["PI"], fila["SO"] = pi, pi.split(".")[0]


DEFECTOS = {
    r'el código "(?P<v>[0-9]+)" de siete cifras': ("CÓDIGO DEL ESTUDIANTE", None),
    r"la calificación (?P<v>[0-9]+)": ("CALIFICACIÓN", int),
    r"la calificación (?P<v>[0-9]+,[0-9]+)": ("CALIFICACIÓN", None),
    r"la calificación vacía": ("CALIFICACIÓN", None),
    r'el código "(?P<v>[0-9]+)" que también está en la 702': ("CÓDIGO DEL ESTUDIANTE", None),
    r'el código "(?P<v>[0-9]+)" repetido en la 701': ("CÓDIGO DEL ESTUDIANTE", None),
}


@given(parsers.re(r'en la tabla maestra la fila (?P<fila>[0-9]+) con (?P<defecto>.+)'))
def _fila_defectuosa(ctx: Escenario, fila: str, defecto: str) -> None:
    for patron, (columna, tipo) in DEFECTOS.items():
        coincidencia = re.fullmatch(patron, defecto)
        if coincidencia:
            break
    else:
        raise AssertionError(f"defecto sin paso: {defecto}")
    valor = coincidencia.groupdict().get("v")
    destino = _maestra(ctx).filas[int(fila) - 2]
    destino[columna] = tipo(valor) if tipo and valor is not None else valor
    if "también está en la 702" in defecto:
        assert any(f["SECCIÓN"] == "702" and f["CÓDIGO DEL ESTUDIANTE"] == valor for f in _maestra(ctx).filas)
    if "repetido en la 701" in defecto:
        assert [f["SECCIÓN"] for f in _maestra(ctx).filas if f["CÓDIGO DEL ESTUDIANTE"] == valor] == ["701", "701"]
    ctx.extras["valor"] = valor


@given("una tabla maestra sin la columna CALIFICACIÓN")
def _sin_calificacion(ctx: Escenario) -> None:
    maestra = _maestra(ctx)
    maestra.columnas = tuple(columna for columna in maestra.columnas if columna != "CALIFICACIÓN")


@given("una carpeta de salida dentro de la copia de trabajo del Back")
def _salida_dentro(ctx: Escenario) -> None:
    salida = RAIZ / f"salida_de_prueba_{secrets.token_hex(4)}"
    assert not salida.exists()
    ctx.extras["salida"] = salida


@given("el manifiesto inventado del generador y las tarjetas inventadas en tmp_path")
def _manifiesto_y_tarjetas(ctx: Escenario) -> None:
    # guia_y_privacidad.feature no trae los Antecedentes de exports_capacitacion.feature, así que el paso arma la misma
    # tabla maestra, la misma programación y la misma carpeta de salida en tmp_path.
    _tabla_maestra(ctx)
    _programacion_inventada(ctx, *(f"SINTETICO_20261_5643_{n}" for n in ("701", "702", "703")))
    _salida_fuera(ctx)
    _exige_exito(correr(ctx))
    manifiesto = _manifiesto(ctx)
    tarjetas = [(entrada["seccion"], f"docente{entrada['seccion']}@example.invalid", entrada["archivo"],
                 "Entrega en sala por la Oficina de Calidad") for entrada in manifiesto["exports"]]
    ctx.extras["tarjetas"] = tarjetas


def _escribir_tarjetas(ctx: Escenario, tarjetas: list[tuple[str, ...]]) -> Path:
    destino = _carpeta(ctx, "tarjetas") / "tarjetas_inventadas.csv"
    salida = io.StringIO(newline="")
    escritor = csv.writer(salida, lineterminator="\r\n")
    escritor.writerow(("seccion", "correo", "archivo", "contrasena"))
    escritor.writerows(tarjetas)
    destino.write_bytes(salida.getvalue().encode("utf-8"))
    return destino


def _correr_tarjetas(ctx: Escenario, tarjetas: list[tuple[str, ...]]) -> subprocess.CompletedProcess[str]:
    ruta = _escribir_tarjetas(ctx, tarjetas)
    corrida = subprocess.run([sys.executable, "-I", str(GENERADOR), "--tarjetas", str(ruta), "--manifiesto",
                              str(ctx.extras["salida"] / "manifiesto.json")], capture_output=True, text=True,
                             encoding="utf-8", check=False, cwd=ctx.request.getfixturevalue("tmp_path"))
    ctx.extras["corrida"] = corrida
    return corrida


# Cuando

@when(parsers.re(r'el generador corre(?: con (?P<argumentos>--(?:periodo|asignatura|pi|fecha) [^ ]+(?: --[a-z]+ [^ ]+)*))?'))
def _corre(ctx: Escenario, argumentos: str | None) -> None:
    cambios = dict(re.findall(r"--([a-z]+) ([^ ]+)", argumentos or ""))
    correr(ctx, **cambios)


@when(parsers.re(r'el generador corre y el lector lee el archivo de la (?P<seccion>[0-9]+)'))
def _corre_y_lee(ctx: Escenario, seccion: str) -> None:
    _exige_exito(correr(ctx))
    ctx.extras["leido"] = _leido(_exports(ctx.extras["salida"])[seccion])


@when("el generador corre dos veces con los mismos parámetros sobre la misma tabla maestra")
def _corre_dos_veces(ctx: Escenario) -> None:
    tmp = ctx.request.getfixturevalue("tmp_path")
    for vez in ("primera", "segunda"):
        _exige_exito(correr(ctx, salida=tmp / vez))
        ctx.extras[vez] = _huellas(tmp / vez)


@when(parsers.re(r'el generador corre con --ejercicio (?P<n>[0-9]+) sobre una tabla maestra inventada de la sección '
                 r'ficticia "(?P<seccion>[0-9]+)" \(propuesta\)'))
def _corre_ejercicio(ctx: Escenario, n: str, seccion: str) -> None:
    for fila in _maestra(ctx).filas:
        fila["SECCIÓN"] = seccion
    # Una sección sola, sin repetidos, como la tabla del ejercicio que arma Jefferson.
    vistos: set[object] = set()
    _maestra(ctx).filas = [f for f in _maestra(ctx).filas
                           if not (f["CÓDIGO DEL ESTUDIANTE"] in vistos or vistos.add(f["CÓDIGO DEL ESTUDIANTE"]))]
    ctx.extras["ejercicio"] = (int(n), seccion)
    _exige_exito(correr(ctx, "--ejercicio", n))


@when(parsers.re(r'corre scripts/generar_exports_desde_maestra\.py con --tarjetas \(propuesta\)'))
def _corre_tarjetas(ctx: Escenario) -> None:
    _correr_tarjetas(ctx, ctx.extras["tarjetas"])


# Entonces

@then(parsers.re(r'la carpeta de salida tiene (?P<n>[0-9]+) archivos \.xlsx y "manifiesto\.json"'))
def _archivos(ctx: Escenario, n: str) -> None:
    _exige_exito(ctx.extras["corrida"])
    nombres = sorted(ruta.name for ruta in ctx.extras["salida"].iterdir())
    assert len([nombre for nombre in nombres if nombre.endswith(".xlsx")]) == int(n)
    assert set(nombres) - {nombre for nombre in nombres if nombre.endswith(".xlsx")} == {"manifiesto.json"}


@then(parsers.re(r'el archivo de la (?P<seccion>[0-9]+) se llama "(?P<nombre>[^"]+)" y su hoja "(?P<hoja>[^"]+)"'))
def _nombre_y_hoja(ctx: Escenario, seccion: str, nombre: str, hoja: str) -> None:
    ruta = _exports(ctx.extras["salida"])[seccion]
    assert ruta.name == nombre
    assert _leer(ruta)[0] == hoja
    ctx.extras["ruta"] = ruta


@then(parsers.re(r'el lector declara de ese archivo el periodo "(?P<periodo>[^"]+)", la asignatura "(?P<asignatura>[^"]+)" '
                 r'y la sección "(?P<seccion>[^"]+)"'))
def _declara(ctx: Escenario, periodo: str, asignatura: str, seccion: str) -> None:
    leido = _leido(ctx.extras["ruta"])
    declarada = validacion.seccion_declarada(leido.hoja, leido.nombre_archivo)
    assert (declarada.periodo, declarada.curso_codigo, declarada.seccion_codigo) == (periodo, asignatura, seccion)
    # La hoja sola también la declara, sin apoyarse en el nombre del archivo.
    assert validacion.seccion_declarada(leido.hoja, "otro_nombre.xlsx") == declarada


@then(parsers.re(r'el lector clasifica la columna "(?P<encabezado>[^"]+)" como la columna del PI (?P<pi>[0-9.]+)'))
def _clasifica(ctx: Escenario, encabezado: str, pi: str) -> None:
    columnas = _leido(ctx.extras["ruta"]).columnas_pi
    assert [(c.encabezado, c.pi_codigo, c.tipo) for c in columnas] == [(encabezado, pi, TipoColumna.PI)]


@then(parsers.re(r'validar\(\) acepta todas las filas de la (?P<seccion>[0-9]+) sin rechazos'))
def _valida(ctx: Escenario, seccion: str) -> None:
    leido = _leido(_exports(ctx.extras["salida"])[seccion])
    contexto = ContextoSeccion(periodo="2026-1", curso_codigo="5643", seccion_codigo=seccion,
                               plan=(PiDelPlan(pi_id=1, codigo="6.1"),))
    resultado = validacion.validar(leido, contexto)
    assert resultado.rechazo_de_carga is None
    assert (resultado.rechazos_de_fila, resultado.avisos) == ((), ())
    assert len(resultado.filas_aceptadas) == len(_de_la_seccion(seccion, _maestra(ctx))) == resultado.filas_de_datos


@then(parsers.re(r'lo leído trae en Username "(?P<a>[0-9]+)", "(?P<b>[0-9]+)" y "(?P<c>[0-9]+)" con los niveles '
                 r'(?P<na>[1-4]), (?P<nb>[1-4]) y (?P<nc>[1-4])'))
def _leido_trae(ctx: Escenario, a: str, b: str, c: str, na: str, nb: str, nc: str) -> None:
    leido = ctx.extras["leido"]
    assert [(fila.codigo, fila.valores_pi) for fila in leido.filas] == [
        (a, (int(na),)), (b, (int(nb),)), (c, (int(nc),))]


@then(parsers.re(r'el conteo por nivel de lo leído es igual al de la tabla maestra para la (?P<seccion>[0-9]+)'))
def _conteo_igual(ctx: Escenario, seccion: str) -> None:
    leidos = Counter(fila.valores_pi[0] for fila in ctx.extras["leido"].filas)
    assert leidos == Counter(nivel for _, nivel in _de_la_seccion(seccion, _maestra(ctx)))


@then(parsers.re(r'ningún código de la 701 ni de la 703 aparece en el archivo de la 702'))
def _sin_codigos_ajenos(ctx: Escenario) -> None:
    ajenos = {codigo for seccion in ("701", "703") for codigo, _ in _de_la_seccion(seccion, _maestra(ctx))}
    assert ajenos
    assert not ajenos & {str(fila.codigo) for fila in ctx.extras["leido"].filas}


@then(parsers.re(r'cada archivo tiene solo las columnas "(?P<a>[^"]+)" y "(?P<b>[^"]+)" \(propuesta\)'))
def _solo_dos_columnas(ctx: Escenario, a: str, b: str) -> None:
    _exige_exito(ctx.extras["corrida"])
    exports = _exports(ctx.extras["salida"])
    assert len(exports) == 3
    for ruta in exports.values():
        assert _leer(ruta)[1] == [a, b]


@then("ninguna columna se llama como las que busca la consulta de control Q04")
def _sin_columnas_q04(ctx: Escenario) -> None:
    for ruta in _exports(ctx.extras["salida"]).values():
        encabezado = [columna.lower().replace(" ", "_") for columna in _leer(ruta)[1]]
        assert not [columna for columna in encabezado if Q04.search(columna)], encabezado


@then(parsers.re(r'ninguna celda repite "(?P<profesor>[^"]+)" ni un valor de la columna ARCHIVO de la tabla maestra'))
def _sin_profesor(ctx: Escenario, profesor: str) -> None:
    prohibidos = {profesor, *(str(f["ARCHIVO"]) for f in _maestra(ctx).filas), *PROFESORES.values(), "QUÍMICA GENERAL"}
    for ruta in _exports(ctx.extras["salida"]).values():
        hoja, encabezado, filas = _leer(ruta)
        celdas = {str(celda) for fila in filas for celda in fila} | set(encabezado) | {hoja}
        assert not celdas & prohibidos
        # Ni dentro del zip, por ejemplo en las propiedades del libro.
        assert profesor.encode() not in ruta.read_bytes()


@then("la celda del código es texto y el lector lee las mismas ocho cifras, con el cero")
def _codigo_texto(ctx: Escenario) -> None:
    _exige_exito(ctx.extras["corrida"])
    codigo = ctx.extras["codigo_con_cero"]
    ruta = _exports(ctx.extras["salida"])["701"]
    libro = load_workbook(ruta)
    celdas = [fila[0] for fila in libro.worksheets[0].iter_rows(min_row=2) if fila[0].value == codigo]
    assert len(celdas) == 1 and celdas[0].data_type == "s"
    assert codigo in [fila.codigo for fila in _leido(ruta).filas]


@then(parsers.re(r'el nombre y la hoja del archivo de la (?P<seccion>[0-9]+) llevan exactamente ese curso'))
def _curso_exacto(ctx: Escenario, seccion: str) -> None:
    _exige_exito(ctx.extras["corrida"])
    assert ctx.extras["curso"][0] == seccion
    curso = ctx.extras["curso"][1]
    ruta = _exports(ctx.extras["salida"])[seccion]
    assert ruta.name == f"gc_{curso}_fullgc_{PARAMETROS['fecha']}.xlsx"
    assert _leer(ruta)[0] == f"gc_{curso}_f"


@then(parsers.re(r'una sección de la tabla maestra sin fila en la programación detiene el generador con '
                 r'«(?P<mensaje>[^»]+)» \(propuesta\)'))
def _seccion_sin_programacion(ctx: Escenario, mensaje: str) -> None:
    fila = int(re.match(r"Fila ([0-9]+)\.", mensaje)[1])
    _maestra(ctx).filas[fila - 2]["SECCIÓN"] = "704"
    assert "704" not in ctx.extras["programacion"]
    salida = ctx.request.getfixturevalue("tmp_path") / "sin_programacion"
    corrida = correr(ctx, salida=salida)
    assert corrida.returncode == 1, _salida(ctx)
    assert mensaje in corrida.stdout.splitlines()
    assert not salida.exists() or not list(salida.iterdir())


@then("cada archivo tiene la misma huella SHA-256 en las dos corridas")
def _mismas_huellas(ctx: Escenario) -> None:
    primera, segunda = ctx.extras["primera"], ctx.extras["segunda"]
    assert len(primera) == 3 and primera == segunda


@then(parsers.re(r'"manifiesto\.json" trae una entrada por sección con la sección, el nombre del archivo, su huella '
                 r'SHA-256, las filas y el conteo de los niveles 1, 2, 3 y 4'))
def _manifiesto_por_seccion(ctx: Escenario) -> None:
    _exige_exito(ctx.extras["corrida"])
    exports = _exports(ctx.extras["salida"])
    entradas = _manifiesto(ctx)["exports"]
    assert [entrada["seccion"] for entrada in entradas] == ["701", "702", "703"]
    for entrada in entradas:
        ruta = exports[entrada["seccion"]]
        de_la_tabla = _de_la_seccion(entrada["seccion"], _maestra(ctx))
        assert entrada["archivo"] == ruta.name
        assert entrada["sha256"] == hashlib.sha256(ruta.read_bytes()).hexdigest()
        assert entrada["filas"] == len(de_la_tabla)
        conteo = Counter(nivel for _, nivel in de_la_tabla)
        assert entrada["niveles"] == {str(nivel): conteo.get(nivel, 0) for nivel in (1, 2, 3, 4)}


@then(parsers.re(r'el manifiesto, sin contar el campo sha256, no trae ningún número de ocho cifras ni ningún nombre'))
def _manifiesto_sin_codigos(ctx: Escenario) -> None:
    manifiesto = _manifiesto(ctx)
    for entrada in manifiesto["exports"]:
        entrada.pop("sha256")
    texto = json.dumps(manifiesto, ensure_ascii=False)
    assert not OCHO_CIFRAS.findall(texto)
    assert not [nombre for nombre in (*PROFESORES.values(), "QUÍMICA GENERAL", "R017_inventado") if nombre in texto]
    assert "@" not in texto


@then(parsers.re(r'esas (?P<n>[0-9]+) filas no entran a ningún archivo'))
def _no_entran(ctx: Escenario, n: str) -> None:
    _exige_exito(ctx.extras["corrida"])
    ajenas = set(ctx.extras["ajenas"])
    assert len(ajenas) == int(n)
    for ruta in _exports(ctx.extras["salida"]).values():
        assert not ajenas & {str(fila.codigo) for fila in _leido(ruta).filas}


@then(parsers.re(r'el manifiesto las cuenta como (?P<p>[0-9]+) omitidas por periodo, (?P<a>[0-9]+) por asignatura y '
                 r'(?P<pi>[0-9]+) por PI \(propuesta\)'))
def _omitidas(ctx: Escenario, p: str, a: str, pi: str) -> None:
    assert _manifiesto(ctx)["omitidas"] == {"periodo": int(p), "asignatura": int(a), "pi": int(pi)}


@then(parsers.re(r'los archivos llevan la columna "(?P<columna>[^"]+)"'))
def _llevan_la_columna(ctx: Escenario, columna: str) -> None:
    _exige_exito(ctx.extras["corrida"])
    exports = _exports(ctx.extras["salida"])
    assert len(exports) == 3
    for ruta in exports.values():
        assert _leer(ruta)[1] == ["Username", columna]


@then(parsers.re(r'con --pi (?P<pi>[0-9.]+) el generador termina con código 1 y dice «(?P<mensaje>[^»]+)» \(propuesta\)'))
def _sin_filas_del_pi(ctx: Escenario, pi: str, mensaje: str) -> None:
    salida = ctx.request.getfixturevalue("tmp_path") / "otro_pi"
    corrida = correr(ctx, salida=salida, pi=pi)
    assert corrida.returncode == 1, _salida(ctx)
    assert mensaje in corrida.stdout.splitlines()
    assert not salida.exists() or not list(salida.iterdir())


@then("el generador termina con código 1 y la carpeta de salida queda sin exports")
def _detenido(ctx: Escenario) -> None:
    assert ctx.extras["corrida"].returncode == 1, _salida(ctx)
    salida = ctx.extras["salida"]
    assert not salida.exists() or not list(salida.iterdir())


@then(parsers.re(r'el informe dice «(?P<mensaje>[^»]+)» \(propuesta\)'))
def _informe_dice(ctx: Escenario, mensaje: str) -> None:
    assert mensaje in ctx.extras["corrida"].stdout.splitlines(), _salida(ctx)


@then("el informe no repite el código ni la calificación")
def _informe_sin_valores(ctx: Escenario) -> None:
    texto = re.sub(r"Fila [0-9]+\.", "Fila.", _salida(ctx))
    valor = ctx.extras["valor"]
    if valor is not None:
        assert not re.search(rf"(?<![0-9]){re.escape(valor)}(?![0-9])", texto), texto
        assert valor.replace(",", ".") not in texto
    assert not OCHO_CIFRAS.findall(texto)
    assert not re.search(r"(?<![0-9])0?[0-9]{7}(?![0-9])", texto)


@then(parsers.re(r'termina con código (?P<codigo>[0-9]+) y dice «(?P<mensaje>[^»]+)» \(propuesta\)'))
def _termina_y_dice(ctx: Escenario, codigo: str, mensaje: str) -> None:
    assert ctx.extras["corrida"].returncode == int(codigo), _salida(ctx)
    assert mensaje in ctx.extras["corrida"].stdout.splitlines()


@then(parsers.re(r'termina con código (?P<codigo>[0-9]+) sin escribir nada'))
def _sin_escribir(ctx: Escenario, codigo: str) -> None:
    assert ctx.extras["corrida"].returncode == int(codigo), _salida(ctx)
    assert not ctx.extras["salida"].exists()


@then(parsers.re(r'dice «(?P<mensaje>[^»]+)» \(propuesta\)'))
def _dice(ctx: Escenario, mensaje: str) -> None:
    assert mensaje in ctx.extras["corrida"].stdout.splitlines(), _salida(ctx)


@then("la salida dice por sección el número de filas y el conteo por nivel")
def _salida_por_seccion(ctx: Escenario) -> None:
    _exige_exito(ctx.extras["corrida"])
    lineas = ctx.extras["corrida"].stdout.splitlines()
    for seccion in ("701", "702", "703"):
        conteo = Counter(nivel for _, nivel in _de_la_seccion(seccion, _maestra(ctx)))
        esperada = (f"Sección {seccion}. {sum(conteo.values())} filas, {conteo[1]} de nivel 1, {conteo[2]} de nivel 2, "
                    f"{conteo[3]} de nivel 3 y {conteo[4]} de nivel 4.")
        assert esperada in lineas, lineas


@then("la salida no contiene ningún número de ocho cifras")
def _salida_sin_codigos(ctx: Escenario) -> None:
    texto = _salida(ctx)
    assert not OCHO_CIFRAS.findall(texto)
    assert not [nombre for nombre in (*PROFESORES.values(), "QUÍMICA GENERAL", "@") if nombre in texto]


@then(parsers.re(r'la carpeta de salida tiene (?P<n>[0-9]+) archivos de ejercicio de la (?P<seccion>[0-9]+) con códigos '
                 r'99 distintos'))
def _ejercicios(ctx: Escenario, n: str, seccion: str) -> None:
    rutas = sorted(ctx.extras["salida"].glob("*.xlsx"))
    assert len(rutas) == int(n)
    codigos_por_archivo = []
    for ruta in rutas:
        leido = _leido(ruta)
        declarada = validacion.seccion_declarada(leido.hoja, leido.nombre_archivo)
        assert (declarada.periodo, declarada.curso_codigo, declarada.seccion_codigo) == ("2026-1", "5643", seccion)
        codigos = [str(fila.codigo) for fila in leido.filas]
        assert all(re.fullmatch(r"99[0-9]{6}", codigo) for codigo in codigos)
        codigos_por_archivo.append(set(codigos))
    # Ningún código se repite entre dos archivos ni viene de la tabla maestra.
    de_la_tabla = {str(f["CÓDIGO DEL ESTUDIANTE"]) for f in _maestra(ctx).filas}
    assert sum(len(c) for c in codigos_por_archivo) == len(set().union(*codigos_por_archivo))
    assert not set().union(*codigos_por_archivo) & de_la_tabla


@then(parsers.re(r'las (?P<n>[0-9]+) huellas SHA-256 son distintas, para que uq_archivo_origen_sha256 no confunda dos '
                 r'subidas'))
def _huellas_distintas(ctx: Escenario, n: str) -> None:
    huellas = _huellas(ctx.extras["salida"])
    assert len(set(huellas.values())) == len(huellas) == int(n)


@then("cada tarjeta nombra la sección y el archivo que el manifiesto da para esa sección")
def _tarjetas_coinciden(ctx: Escenario) -> None:
    corrida = ctx.extras["corrida"]
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert corrida.stdout.splitlines()[-1] == "3 de 3 tarjetas nombran el archivo de su sección."
    assert "@" not in corrida.stdout


@then("una tarjeta con el archivo de otra sección hace fallar la comprobación y la nombra")
def _tarjeta_ajena(ctx: Escenario) -> None:
    tarjetas = list(ctx.extras["tarjetas"])
    # La tarjeta de la 702, en la fila 3 del archivo, lleva el archivo de la 701.
    assert tarjetas[1][0] == "702" and tarjetas[0][0] == "701"
    tarjetas[1] = (tarjetas[1][0], tarjetas[1][1], tarjetas[0][2], tarjetas[1][3])
    corrida = _correr_tarjetas(ctx, tarjetas)
    assert corrida.returncode == 1, corrida.stdout + corrida.stderr
    assert "Tarjeta de la fila 3. La sección 702 no lleva el archivo que el manifiesto le da." in corrida.stdout.splitlines()
    assert "@" not in corrida.stdout
