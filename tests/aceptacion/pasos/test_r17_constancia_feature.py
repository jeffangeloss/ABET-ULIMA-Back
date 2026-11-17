"""Pasos de r17_constancia.feature (US-15 y US-16), ejecutables con pytest-bdd en español (T050).

El .feature manda. Ningún paso cambia una cifra, un mensaje ni un título para que el escenario pase.
El R-17 que descarga el profesor se abre con openpyxl en modo de solo lectura y con los valores
guardados, sin recalcular fórmulas, y cada celda que nombra un escenario se compara con la vista
abet.v_r17_por_pi, con las tablas de la base o con la respuesta de la subida. Los pasos que repiten
otros .feature (Antecedentes, subidas, sesiones, consultas de control) viven en el conftest.py de
esta carpeta.

Mapa de celdas de «Cursos de Carrera», el de plantillas/README.md.
- Cabecera. D8 asignatura, D11 sección, I11 periodo y B7 la franja PROVISIONAL.
- Bloque I. B15 el SO y B17 a B19 los PI.
- Bloque II. B24 a B26 los PI, E24 a E26 el porcentaje, G24 a G26 la meta y, en K29 a Q31, la
  frecuencia por nivel (L a O), «logran de calificados» (P) y el porcentaje sobre el total (Q).
- Recuadros de causas y de acciones. B29:I31 y B34:I36.
- Tabla de estudiantes. Desde la fila 43, con SO en B, PI en C, código en E y calificación en F.
La hoja «Constancia» tiene el rótulo en la columna A y el valor en la B.
"""

from __future__ import annotations

import io
import re
import subprocess
import zipfile
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from pytest_bdd import given, parsers, scenarios, then, when

RAIZ = Path(__file__).resolve().parents[3]
Escenario = Any
scenarios("specs/001-mvp-carga-r17/aceptacion/r17_constancia.feature")

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
HOJA = "Cursos de Carrera"
CONSTANCIA = "Constancia"
PRIMERA_FILA_DE_LA_TABLA = 43
FILAS_DEL_BLOQUE_II = {"5.1": 24, "5.2": 25, "5.3": 26}
FILAS_DE_FRECUENCIAS = {"5.1": 29, "5.2": 30, "5.3": 31}
SIN_CARGA = "el escenario todavía no descargó ningún libro"


def _conftest(ctx: Escenario) -> Any:
    """Módulo conftest.py de esta carpeta, que pytest registra como plugin, para reutilizar sus ayudas."""
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        ruta = getattr(plugin, "__file__", "") or ""
        if ruta.endswith("aceptacion/pasos/conftest.py"):
            return plugin
    raise AssertionError("no se encontró el conftest.py del arnés de aceptación")


# El libro descargado

def _libro(ctx: Escenario) -> dict[str, dict[str, Any]]:
    """Celdas con valor de cada hoja del libro de la respuesta, leído en solo lectura y con los valores guardados."""
    if "libro" not in ctx.extras:
        assert ctx.respuesta is not None, SIN_CARGA
        libro = load_workbook(io.BytesIO(ctx.respuesta.content), read_only=True, data_only=True)
        ctx.extras["libro"] = {
            hoja.title: {celda.coordinate: celda.value for fila in hoja.iter_rows() for celda in fila
                         if getattr(celda, "value", None) is not None}
            for hoja in libro.worksheets
        }
        ctx.extras["propiedades"] = libro.properties
        ctx.extras["hojas"] = list(libro.sheetnames)
        libro.close()
    return ctx.extras["libro"]


def _celdas(ctx: Escenario, hoja: str = HOJA) -> dict[str, Any]:
    libro = _libro(ctx)
    assert hoja in libro, f"el libro no tiene la hoja {hoja!r}, tiene {list(libro)}"
    return libro[hoja]


def _numero(texto: str) -> Decimal:
    return Decimal(texto.replace(",", "."))


def _filas_de_constancia(ctx: Escenario) -> list[tuple[Any, Any]]:
    celdas = _celdas(ctx, CONSTANCIA)
    ultima = max(int(re.sub(r"[A-Z]+", "", ref)) for ref in celdas)
    return [(celdas.get(f"A{n}"), celdas.get(f"B{n}")) for n in range(1, ultima + 1)]


def _valor_de_constancia(ctx: Escenario, rotulo: str) -> Any:
    valores = [valor for nombre, valor in _filas_de_constancia(ctx) if nombre == rotulo]
    assert len(valores) == 1, f"la hoja Constancia trae {len(valores)} filas con el rótulo {rotulo!r}"
    return valores[0]


def _textos(ctx: Escenario, hoja: str | None = None) -> list[str]:
    libro = _libro(ctx)
    hojas = [hoja] if hoja else list(libro)
    return [str(valor) for nombre in hojas for valor in libro[nombre].values()]


def _tabla_de_estudiantes(ctx: Escenario) -> list[tuple[Any, Any, Any, Any]]:
    celdas = _celdas(ctx)
    filas = []
    numero = PRIMERA_FILA_DE_LA_TABLA
    while any(f"{columna}{numero}" in celdas for columna in "BCEF"):
        filas.append(tuple(celdas.get(f"{columna}{numero}") for columna in "BCEF"))
        numero += 1
    return filas


def _cabecera(ctx: Escenario) -> str:
    return ctx.respuesta.headers.get("content-disposition", "")


# Antecedentes propios

@given(parsers.re(r'el conjunto de reglas "(?P<version>[^"]+)" en estado "(?P<estado>[A-Z]+)" con META_LOGRO (?P<meta>[0-9,]+) '
                  r'y NIVEL_ESPERADO (?P<nivel>[0-9]) DEFINIDOS'))
def _conjunto_de_reglas(ctx: Escenario, version: str, estado: str, meta: str, nivel: str) -> None:
    filas = ctx.filas("SELECT cr.estado, pv.clave, pv.estado, pv.valor_numero FROM abet.conjunto_reglas cr"
                      " JOIN abet.parametro_valor pv USING (conjunto_reglas_id) WHERE cr.version = %s"
                      " AND pv.clave IN ('META_LOGRO', 'NIVEL_ESPERADO') ORDER BY pv.clave", version)
    assert filas == [(estado, "META_LOGRO", "DEFINIDO", _numero(meta)),
                     (estado, "NIVEL_ESPERADO", "DEFINIDO", Decimal(nivel))], filas


APROBAR = """
INSERT INTO abet.conjunto_reglas (carrera_id, version, estado, aprobado_por, aprobado_en)
SELECT carrera_id, %(version)s, 'APROBADO', 'Comité de prueba', DATE '2026-10-01'
FROM abet.carrera WHERE codigo = 'AMB'
"""
PARAMETROS = """
INSERT INTO abet.parametro_valor (conjunto_reglas_id, clave, estado, valor_numero, valor_texto)
SELECT cr.conjunto_reglas_id, v.clave, 'DEFINIDO', v.numero, v.texto
FROM (VALUES ('META_LOGRO',           CAST(0.70 AS numeric(9, 4)), CAST(NULL AS varchar(40))),
             ('NIVEL_ESPERADO',       2,    NULL),
             ('CORTE_ROJO',           0.50, NULL),
             ('CONVERSION_NIVEL_0_1', NULL, NULL),
             ('TRATO_SIN_EVIDENCIA',  NULL, 'SE_EXCLUYE_DEL_DENOMINADOR')) AS v (clave, numero, texto)
JOIN abet.conjunto_reglas cr ON cr.version = %(version)s
"""
CONVERSION = """
INSERT INTO abet.conversion_nivel_0_1 (conjunto_reglas_id, nivel_original, valor_0_1)
SELECT cr.conjunto_reglas_id, v.nivel, v.valor
FROM (VALUES (1, 0.0), (2, 0.3333), (3, 0.6667), (4, 1.0)) AS v (nivel, valor)
JOIN abet.conjunto_reglas cr ON cr.version = %(version)s
"""


@given(parsers.re(r'que la base tiene el conjunto "(?P<version>[^"]+)" de Ambiental en estado "APROBADO" con META_LOGRO 0,70, '
                  r'NIVEL_ESPERADO 2, CORTE_ROJO 0,50, TRATO_SIN_EVIDENCIA "SE_EXCLUYE_DEL_DENOMINADOR" y la conversión '
                  r'de sus 4 niveles, como en el caso A03 de pruebas\.sql'))
def _reglas_aprobadas_de_prueba(ctx: Escenario, version: str) -> None:
    """Inserta, con la conexión del dueño de la copia, las mismas filas que el caso A03 de db/pruebas/pruebas.sql."""
    for sentencia in (APROBAR, PARAMETROS, CONVERSION):
        ctx.api.dueno.execute(sentencia, {"version": version})
    assert ctx.filas("SELECT estado FROM abet.conjunto_reglas WHERE version = %s", version) == [("APROBADO",)]
    assert ctx.cuenta("conversion_nivel_0_1", "conjunto_reglas_id = (SELECT conjunto_reglas_id"
                      " FROM abet.conjunto_reglas WHERE version = %s)", version) == 4


@given(parsers.re(r'la API configurada con CONJUNTO_REGLAS "(?P<version>[^"]+)"'))
def _api_con_otro_conjunto(ctx: Escenario, version: str) -> None:
    ctx.reiniciar_api(carga=replace(ctx.api.ajustes.carga, conjunto_reglas=version))
    assert ctx.api.ajustes.carga.conjunto_reglas == version


@given(parsers.re(r'la consulta de control (?P<nombre>Q[0-9]{2}) devuelve 0 filas'))
def _control_previo(ctx: Escenario, nombre: str) -> None:
    assert ctx.filas(_conftest(ctx).consultas_de_control()[nombre]) == [], f"{nombre} devuelve filas"


@given(parsers.re(r'que una copia de "(?P<base>[^"]+)" (?P<cambio>sin la columna [0-9]\.[0-9]) está subida a la sección '
                  r'(?P<numero>[0-9]+) con respuesta 201, estado "(?P<estado>[A-Z]+)" y su carga_id'))
def _copia_subida_con_estado(ctx: Escenario, base: str, cambio: str, numero: str, estado: str) -> None:
    contenido, nombre = ctx.copia_de(f'una copia de "{base}" {cambio}')
    respuesta = ctx.subir(ctx.profesor, contenido, nombre, numero)
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["estado"] == estado
    assert ctx.carga_id is not None
    ctx.carga_previa = ctx.carga_id
    ctx.antes = ctx.api.conteos()


# Cuando, el R-17 y la constancia

def _pedir(ctx: Escenario, quien: str, ruta: str) -> None:
    """GET de la ruta con la sesión de quien, que deja la respuesta nueva y descarta el libro de la anterior."""
    correo = ctx.profesor if quien == "el profesor" else quien.strip('"')
    assert correo is not None and ctx.carga_id is not None
    ctx.extras.setdefault("subida", ctx.respuesta)
    for clave in ("libro", "propiedades", "hojas"):
        ctx.extras.pop(clave, None)
    ctx.respuesta = ctx.sesion(correo).get(ruta.format(carga_id=ctx.carga_id))


@when(parsers.re(r'(?P<quien>el profesor|"[^"]+") descarga el R-17 de esa carga'))
def _descarga_r17(ctx: Escenario, quien: str) -> None:
    _pedir(ctx, quien, "/api/cargas/{carga_id}/r17.xlsx")


@when(parsers.re(r'(?P<quien>el profesor|"[^"]+") pide la constancia de esa carga'))
def _pide_constancia(ctx: Escenario, quien: str) -> None:
    _pedir(ctx, quien, "/api/cargas/{carga_id}")


# Entonces, la respuesta

@then(parsers.re(r'la respuesta es (?P<codigo>[0-9]+)'))
def _respuesta_es(ctx: Escenario, codigo: str) -> None:
    assert ctx.respuesta.status_code == int(codigo), ctx.respuesta.text[:300]


@then(parsers.re(r'la respuesta es 200 con Content-Type "(?P<tipo>[^"]+)"'))
def _respuesta_con_tipo(ctx: Escenario, tipo: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text[:300]
    assert ctx.respuesta.headers["content-type"] == tipo


@then(parsers.re(r'su Content-Disposition nombra el archivo "(?P<nombre>[^"]+)"'))
def _nombre_del_archivo(ctx: Escenario, nombre: str) -> None:
    assert _cabecera(ctx) == f'attachment; filename="{nombre}"'


@then(parsers.re(r'el nombre del archivo termina en "(?P<final>[^"]+)"'))
def _nombre_termina_en(ctx: Escenario, final: str) -> None:
    nombre = re.fullmatch(r'attachment; filename="([^"]+)"', _cabecera(ctx))
    assert nombre is not None and nombre[1].endswith(final), _cabecera(ctx)


@then(parsers.re(r'el cuerpo de la respuesta no es un libro de Excel'))
def _no_es_un_libro(ctx: Escenario) -> None:
    assert ctx.respuesta.headers["content-type"] != XLSX
    assert not zipfile.is_zipfile(io.BytesIO(ctx.respuesta.content))
    assert "content-disposition" not in ctx.respuesta.headers


# Entonces, la hoja «Cursos de Carrera»

@then(parsers.re(r'el libro tiene las hojas "(?P<primera>[^"]+)" y "(?P<segunda>[^"]+)"'))
def _hojas(ctx: Escenario, primera: str, segunda: str) -> None:
    _libro(ctx)
    assert ctx.extras["hojas"] == [primera, segunda]


@then(parsers.re(r'la cabecera de "Cursos de Carrera" muestra la asignatura "(?P<asignatura>[0-9]+)", la sección '
                 r'"(?P<seccion>[0-9]+)" y el periodo "(?P<periodo>[^"]+)"'))
def _cabecera_de_la_hoja(ctx: Escenario, asignatura: str, seccion: str, periodo: str) -> None:
    celdas = _celdas(ctx)
    assert (str(celdas["D8"]), str(celdas["D11"]), str(celdas["I11"])) == (asignatura, seccion, periodo)


@then(parsers.re(r'el bloque I muestra el SO 5 con los PI 5\.1, 5\.2 y 5\.3'))
def _bloque_i(ctx: Escenario) -> None:
    celdas = _celdas(ctx)
    assert celdas["B15"] == "Student Outcome (SO) 5"
    assert [celdas.get(f"B{n}") for n in (17, 18, 19)] == ["5.1", "5.2", "5.3"]


def _pares_del_bloque_ii(texto: str) -> list[tuple[str, int | None, int | None, str]]:
    """Porcentaje, logran, calificados y PI de cada «63,6 % (7 de 11) en 5.1» de una frase del .feature."""
    pares = []
    for m in re.finditer(r'([0-9]+,[0-9]) % (?:\(([0-9]+) de ([0-9]+)\) )?en ((?:[0-9]\.[0-9](?:, | y )?)+)', texto):
        for pi in re.findall(r'[0-9]\.[0-9]', m[4]):
            pares.append((m[1], int(m[2]) if m[2] else None, int(m[3]) if m[3] else None, pi))
    return pares


@then(parsers.re(r'el bloque II muestra (?P<texto>[0-9]+,[0-9] % .+?)(?:, con meta (?P<meta>[0-9]+) %)?'))
def _bloque_ii_porcentajes(ctx: Escenario, texto: str, meta: str | None) -> None:
    celdas = _celdas(ctx)
    pares = _pares_del_bloque_ii(texto)
    assert pares, f"no se leyó ningún porcentaje en {texto!r}"
    for pct, logran, calificados, pi in pares:
        fila, frecuencia = FILAS_DEL_BLOQUE_II[pi], FILAS_DE_FRECUENCIAS[pi]
        assert celdas[f"B{fila}"] == pi
        assert abs(Decimal(str(celdas[f"E{fila}"])) * 100 - _numero(pct)) < Decimal("0.05"), (pi, celdas[f"E{fila}"])
        if logran is not None:
            assert celdas[f"P{frecuencia}"] == f"{logran} de {calificados}", pi
        if meta is not None:
            assert Decimal(str(celdas[f"G{fila}"])) * 100 == Decimal(meta), pi


@then(parsers.re(r'el bloque II muestra por nivel (?P<texto>.+)'))
def _bloque_ii_niveles(ctx: Escenario, texto: str) -> None:
    celdas = _celdas(ctx)
    esperado = {}
    for niveles, pi in re.findall(r'([0-9](?:, [0-9]){2} y [0-9])(?: estudiantes)? en ([0-9]\.[0-9])', texto):
        esperado[pi] = [int(n) for n in re.findall(r'[0-9]', niveles)]
    assert sorted(esperado) == ["5.1", "5.2", "5.3"], esperado
    for pi, niveles in esperado.items():
        assert [celdas[f"{columna}{FILAS_DE_FRECUENCIAS[pi]}"] for columna in "LMNO"] == niveles, pi
        assert celdas[f"K{FILAS_DE_FRECUENCIAS[pi]}"] == pi


@then(parsers.re(r'cada porcentaje es igual a pct_logro_sobre_calificados de abet\.v_r17_por_pi para ese carga_id y ese PI'))
def _porcentaje_igual_a_la_vista(ctx: Escenario) -> None:
    celdas = _celdas(ctx)
    vista = ctx.filas("SELECT pi, pct_logro_sobre_calificados FROM abet.v_r17_por_pi WHERE carga_id = %s ORDER BY pi",
                      ctx.carga_id)
    assert [pi for pi, _ in vista] == ["5.1", "5.2", "5.3"]
    for pi, porcentaje in vista:
        celda = Decimal(str(celdas[f"E{FILAS_DEL_BLOQUE_II[pi]}"]))
        assert abs(celda * 100 - porcentaje) < Decimal("0.05"), (pi, celda, porcentaje)


@then(parsers.re(r'cada conteo por nivel es igual a n_nivel_1, n_nivel_2, n_nivel_3 y n_nivel_4 de abet\.v_r17_por_pi '
                 r'para ese carga_id y ese PI'))
def _conteos_iguales_a_la_vista(ctx: Escenario) -> None:
    celdas = _celdas(ctx)
    vista = ctx.filas("SELECT pi, n_nivel_1, n_nivel_2, n_nivel_3, n_nivel_4 FROM abet.v_r17_por_pi"
                      " WHERE carga_id = %s ORDER BY pi", ctx.carga_id)
    assert len(vista) == 3
    for pi, *niveles in vista:
        assert [celdas[f"{columna}{FILAS_DE_FRECUENCIAS[pi]}"] for columna in "LMNO"] == niveles, pi


@then(parsers.re(r'la tabla de estudiantes tiene (?P<n>[0-9]+) filas con SO, PI, código y calificación, ordenadas por PI y '
                 r'fila de origen, con los códigos (?P<desde>[0-9]+) a (?P<hasta>[0-9]+)'))
def _tabla_completa(ctx: Escenario, n: str, desde: str, hasta: str) -> None:
    tabla = _tabla_de_estudiantes(ctx)
    assert len(tabla) == int(n)
    base = ctx.filas(
        "SELECT p.so_numero, p.codigo, e.codigo, m.nivel_original FROM abet.medicion m"
        " JOIN abet.pi p ON p.pi_id = m.pi_id JOIN abet.estudiante e USING (estudiante_id)"
        " WHERE m.carga_id = %s ORDER BY p.so_numero, p.numero, m.fila_origen", ctx.carga_id)
    assert [(int(so), pi, str(codigo), int(nivel)) for so, pi, codigo, nivel in tabla] == [
        (so, pi, str(codigo), nivel) for so, pi, codigo, nivel in base]
    assert {str(codigo) for _, _, codigo, _ in tabla} == {str(c) for c in range(int(desde), int(hasta) + 1)}
    assert [pi for _, pi, _, _ in tabla] == sorted(pi for _, pi, _, _ in tabla)


@then(parsers.re(r'la tabla de estudiantes tiene (?P<n>[0-9]+) filas y ninguna con el código (?P<codigo>[0-9]+)'))
def _tabla_sin_codigo(ctx: Escenario, n: str, codigo: str) -> None:
    tabla = _tabla_de_estudiantes(ctx)
    assert len(tabla) == int(n)
    assert codigo not in {str(c) for _, _, c, _ in tabla}


@then(parsers.re(r'ninguna celda del libro empieza por "=" ni contiene "#REF!"'))
def _sin_formulas(ctx: Escenario) -> None:
    for hoja in _libro(ctx):
        for ref, valor in _celdas(ctx, hoja).items():
            assert not str(valor).startswith("="), f"{hoja}!{ref} empieza por «=»"
            assert "#REF!" not in str(valor), f"{hoja}!{ref} contiene #REF!"
    with zipfile.ZipFile(io.BytesIO(ctx.respuesta.content)) as libro:
        for parte in libro.namelist():
            if parte.startswith("xl/worksheets/") and parte.endswith(".xml"):
                assert not re.search(rb"<f[ >/]", libro.read(parte)), f"{parte} trae una fórmula"


@then(parsers.re(r'los recuadros de causas, acciones y comentario están vacíos'))
def _recuadros_vacios(ctx: Escenario) -> None:
    celdas = _celdas(ctx)
    causas = [f"{columna}{fila}" for columna in "BCDEFGHI" for fila in (29, 30, 31)]
    acciones = [f"{columna}{fila}" for columna in "BCDEFGHI" for fila in (34, 35, 36)]
    assert [ref for ref in causas + acciones if ref in celdas] == []
    # La plantilla no tiene un recuadro de comentario. Se exige que ninguna celda del libro lo nombre con texto propio.
    assert [ref for ref, valor in celdas.items() if "omentario" in str(valor)] == []


@then(parsers.re(r'abet\.v_r17_por_pi devuelve 3 filas de ese carga_id con provisional verdadero, conjunto_reglas '
                 r'"(?P<reglas>[^"]+)" y pct_logro_segun_regla nulo'))
def _vista_provisional(ctx: Escenario, reglas: str) -> None:
    assert ctx.filas("SELECT provisional, conjunto_reglas, pct_logro_segun_regla FROM abet.v_r17_por_pi"
                     " WHERE carga_id = %s", ctx.carga_id) == [(True, reglas, None)] * 3


@then(parsers.re(r'abet\.v_r17_por_pi devuelve 3 filas de ese carga_id con provisional falso, nivel_esperado '
                 r'(?P<nivel>[0-9]), meta_logro_pct (?P<meta>[0-9,]+) y pct_logro_segun_regla (?P<pct>[0-9,]+)'))
def _vista_oficial(ctx: Escenario, nivel: str, meta: str, pct: str) -> None:
    assert ctx.filas("SELECT provisional, nivel_esperado, meta_logro_pct, pct_logro_segun_regla"
                     " FROM abet.v_r17_por_pi WHERE carga_id = %s", ctx.carga_id) == [
        (False, int(nivel), _numero(meta), _numero(pct))] * 3


@then(parsers.re(r'abet\.v_r17_por_pi no devuelve filas de ese carga_id'))
def _sin_vista(ctx: Escenario) -> None:
    assert ctx.cuenta("v_r17_por_pi", "carga_id = %s", ctx.carga_id) == 0


@then(parsers.re(r'la hoja "Cursos de Carrera" muestra bajo el título una franja que contiene "(?P<a>[^"]+)" y "(?P<b>[^"]+)"'))
def _franja(ctx: Escenario, a: str, b: str) -> None:
    celdas = _celdas(ctx)
    assert "E6" in celdas, "el título de la hoja no está en E6"
    franja = str(celdas["B7"])
    assert a in franja and b in franja, franja


@then(parsers.re(r'ninguna hoja del libro contiene la franja "(?P<texto>[^"]+)"'))
def _sin_franja(ctx: Escenario, texto: str) -> None:
    assert [t for t in _textos(ctx) if texto in t] == []


@then(parsers.re(r'el título de las propiedades del libro contiene "(?P<texto>[^"]+)"'))
def _titulo_de_propiedades(ctx: Escenario, texto: str) -> None:
    _libro(ctx)
    assert texto in (ctx.extras["propiedades"].title or "")


@then(parsers.re(r'las propiedades creator y lastModifiedBy del libro están vacías o dicen "(?P<autor>[^"]+)"'))
def _autores(ctx: Escenario, autor: str) -> None:
    _libro(ctx)
    propiedades = ctx.extras["propiedades"]
    assert propiedades.creator in (None, "", autor)
    assert propiedades.lastModifiedBy in (None, "", autor)


def _nombres_del_export(ctx: Escenario) -> tuple[set[str], set[str]]:
    contenido, _ = ctx.ultimo
    hoja = load_workbook(io.BytesIO(contenido), read_only=True).active
    filas = list(hoja.iter_rows(values_only=True))
    encabezado = list(filas[0])
    apellidos = {str(f[encabezado.index("Last Name")]) for f in filas[1:] if f[encabezado.index("Last Name")]}
    nombres = {str(f[encabezado.index("First Name")]) for f in filas[1:] if f[encabezado.index("First Name")]}
    assert apellidos and nombres
    return apellidos, nombres


def _sin_nombres_en(ctx: Escenario, textos: list[str]) -> None:
    """Ningún apellido aparece en los textos, y un nombre de pila solo aparece si ya está en la plantilla vacía.

    El nombre de pila inventado del export es la palabra genérica «Estudiante», que ya forma parte de la
    plantilla del R-17. Por eso se compara con la plantilla sin datos y el libro no puede sumar ninguna
    aparición. Los apellidos («Inventado 01» a «Inventado 11») no están en la plantilla, así que para
    ellos se exige 0 coincidencias.
    """
    apellidos, nombres = _nombres_del_export(ctx)
    junto = "\n".join(textos).lower()
    for apellido in sorted(apellidos):
        assert apellido.lower() not in junto, f"el apellido {apellido!r} aparece en el libro"
    plantilla = load_workbook(RAIZ / "plantillas" / "R017_ambiental_general.xlsx")
    de_plantilla = "\n".join(str(c.value) for hoja in plantilla.worksheets for fila in hoja.iter_rows()
                             for c in fila if c.value is not None).lower()
    for nombre in sorted(nombres):
        if de_plantilla.count(nombre.lower()):
            # El paso pide 0 coincidencias y la plantilla vacía ya trae el nombre, así que solo se exige que el libro
            # no sume apariciones. La propiedad lo deja a la vista en el resumen del informe.
            ctx.request.node.user_properties.append(
                ("criterio_relajado", f"el nombre de pila {nombre!r} ya está en la plantilla del R-17, y se exige que"
                                      " el libro no sume apariciones"))
        assert junto.count(nombre.lower()) <= de_plantilla.count(nombre.lower()), f"el nombre {nombre!r} suma una aparición"


@then(parsers.re(r'ninguna hoja del libro contiene un apellido ni un nombre de las columnas Last Name y First Name del export'))
def _libro_sin_nombres(ctx: Escenario) -> None:
    _sin_nombres_en(ctx, _textos(ctx))


@then(parsers.re(r'la hoja "Constancia" no contiene ningún apellido ni nombre de las columnas Last Name y First Name del export'))
def _constancia_sin_nombres(ctx: Escenario) -> None:
    textos = _textos(ctx, CONSTANCIA)
    apellidos, nombres = _nombres_del_export(ctx)
    junto = "\n".join(textos).lower()
    assert [x for x in sorted(apellidos | nombres) if x.lower() in junto] == []


@then(parsers.re(r'el nombre del archivo no contiene ningún correo ni nombre de persona'))
def _nombre_sin_personas(ctx: Escenario) -> None:
    nombre = re.fullmatch(r'attachment; filename="([^"]+)"', _cabecera(ctx))[1]
    apellidos, nombres = _nombres_del_export(ctx)
    assert "@" not in nombre and "example.invalid" not in nombre
    assert re.fullmatch(r"R017_[0-9]+_[0-9]+_[0-9]{4}-[0-9](_PROVISIONAL)?\.xlsx", nombre), nombre
    assert [x for x in sorted(apellidos | nombres) if x.lower() in nombre.lower()] == []


# Entonces, la hoja «Constancia»

def _dato_de_la_carga(ctx: Escenario, columna: str) -> Any:
    return ctx.uno(f"SELECT {columna} FROM abet.carga c JOIN abet.archivo_origen ao USING (archivo_id)"
                   " WHERE c.carga_id = %s", ctx.carga_id)


@then(parsers.re(r'la hoja "Constancia" muestra ese carga_id, el archivo "(?P<archivo>[^"]+)" y la hoja "(?P<hoja>[^"]+)"'))
def _constancia_identifica(ctx: Escenario, archivo: str, hoja: str) -> None:
    assert _valor_de_constancia(ctx, "Carga") == ctx.carga_id
    assert _valor_de_constancia(ctx, "Archivo") == archivo == _dato_de_la_carga(ctx, "ao.nombre_archivo")
    assert _valor_de_constancia(ctx, "Hoja") == hoja == _dato_de_la_carga(ctx, "ao.hoja")


@then(parsers.re(r'la hoja "Constancia" muestra ese carga_id, que es el carga_id de las filas de abet\.v_r17_por_pi con que '
                 r'se llenó el bloque II'))
def _constancia_y_bloque(ctx: Escenario) -> None:
    assert _valor_de_constancia(ctx, "Carga") == ctx.carga_id
    assert ctx.filas("SELECT DISTINCT carga_id FROM abet.v_r17_por_pi WHERE carga_id = %s", ctx.carga_id) == [
        (ctx.carga_id,)]
    assert _porcentaje_igual_a_la_vista(ctx) is None


@then(parsers.re(r'muestra el archivo "(?P<archivo>[^"]+)", la hoja "(?P<hoja>[^"]+)" y la huella igual a archivo_origen\.sha256'))
def _constancia_archivo_y_huella(ctx: Escenario, archivo: str, hoja: str) -> None:
    assert _valor_de_constancia(ctx, "Archivo") == archivo == _dato_de_la_carga(ctx, "ao.nombre_archivo")
    assert _valor_de_constancia(ctx, "Hoja") == hoja == _dato_de_la_carga(ctx, "ao.hoja")
    assert _valor_de_constancia(ctx, "Huella SHA-256") == _dato_de_la_carga(ctx, "ao.sha256")


@then(parsers.re(r'muestra filas de datos, leídas, aceptadas y rechazadas "(?P<cifras>[0-9]+(?: / [0-9]+){3})"'))
def _constancia_cifras(ctx: Escenario, cifras: str) -> None:
    assert _valor_de_constancia(ctx, "Filas de datos / leídas / aceptadas / rechazadas") == cifras
    de_la_base = ctx.filas("SELECT filas_de_datos, filas_leidas, filas_aceptadas, filas_rechazadas FROM abet.carga"
                           " WHERE carga_id = %s", ctx.carga_id)[0]
    assert " / ".join(str(n) for n in de_la_base) == cifras


@then(parsers.re(r'muestra "(?P<cifras>[0-9]+(?: / [0-9]+){3})"'))
def _constancia_cifras_sueltas(ctx: Escenario, cifras: str) -> None:
    _constancia_cifras(ctx, cifras)


@then(parsers.re(r'muestra la huella SHA-256 completa, igual a archivo_origen\.sha256 y a la salida de "shasum -a 256" sobre '
                 r'(?P<ruta>tests/datos_inventados/\S+)'))
def _constancia_huella(ctx: Escenario, ruta: str) -> None:
    huella = _valor_de_constancia(ctx, "Huella SHA-256")
    assert re.fullmatch(r"[0-9a-f]{64}", huella)
    assert huella == _dato_de_la_carga(ctx, "ao.sha256")
    salida = subprocess.run(["shasum", "-a", "256", str(RAIZ / ruta)], capture_output=True, text=True, check=True)
    assert salida.stdout.split()[0] == huella


@then(parsers.re(r'muestra el estado "(?P<estado>[A-Z]+)" y la versión del programa igual a carga\.programa_version'))
def _constancia_estado(ctx: Escenario, estado: str) -> None:
    assert _valor_de_constancia(ctx, "Estado") == estado == _dato_de_la_carga(ctx, "c.estado")
    version = _dato_de_la_carga(ctx, "c.programa_version")
    assert version and _valor_de_constancia(ctx, "Versión del programa") == version


@then(parsers.re(r'muestra el conjunto "(?P<conjunto>[^"]+)" con (?P<lista>[A-Z_0-9]+(?:, [A-Z_0-9]+)* y [A-Z_0-9]+) como pendientes'))
def _constancia_conjunto(ctx: Escenario, conjunto: str, lista: str) -> None:
    assert _valor_de_constancia(ctx, "Conjunto de reglas") == conjunto
    dichos = set(re.findall(r"[A-Z][A-Z_0-9]+", lista))
    en_la_base = {clave for (clave,) in ctx.filas(
        "SELECT pv.clave FROM abet.carga c JOIN abet.parametro_valor pv USING (conjunto_reglas_id)"
        " WHERE c.carga_id = %s AND pv.estado = 'PENDIENTE'", ctx.carga_id)}
    assert dichos == en_la_base
    assert set(re.findall(r"[A-Z][A-Z_0-9]+", str(_valor_de_constancia(ctx, "Parámetros pendientes")))) == dichos


def _lineas_tras(ctx: Escenario, rotulo: str, cuantas: int) -> list[Any]:
    filas = _filas_de_constancia(ctx)
    indice = next(i for i, (nombre, _) in enumerate(filas) if nombre == rotulo)
    return [nombre for nombre, _ in filas[indice + 1:indice + 1 + cuantas]]


@then(parsers.re(r'muestra 1 aviso "(?P<aviso>[^"]+)" y 0 rechazos de fila'))
def _constancia_un_aviso(ctx: Escenario, aviso: str) -> None:
    assert _valor_de_constancia(ctx, "Avisos") == 1
    assert _lineas_tras(ctx, "Avisos", 1) == [aviso]
    assert _valor_de_constancia(ctx, "Rechazos de fila") == 0
    assert ctx.cuenta("rechazo_fila", "carga_id = %s AND efecto = 'AVISO'", ctx.carga_id) == 1
    assert ctx.cuenta("rechazo_fila", "carga_id = %s AND efecto <> 'AVISO'", ctx.carga_id) == 0


@then(parsers.re(r'muestra el rechazo "(?P<rechazo>[^"]+)" y el aviso "(?P<aviso>[^"]+)"'))
def _constancia_rechazo_y_aviso(ctx: Escenario, rechazo: str, aviso: str) -> None:
    assert _valor_de_constancia(ctx, "Avisos") == 1 and _valor_de_constancia(ctx, "Rechazos de fila") == 1
    assert _lineas_tras(ctx, "Avisos", 1) == [aviso]
    assert _lineas_tras(ctx, "Rechazos de fila", 1) == [rechazo]
    assert ctx.cuenta("rechazo_fila", "carga_id = %s AND efecto = 'AVISO'", ctx.carga_id) == 1
    # La fila y el PI salen del texto del rechazo que da el paso, y la base debe guardar ese mismo rechazo.
    fila, pi = _fila_y_pi(rechazo)
    ctx.extras["rechazo"] = (fila, pi)
    assert ctx.cuenta("rechazo_fila", "carga_id = %s AND efecto = 'RECHAZA_FILA' AND fila_origen = %s"
                      " AND carga_columna_id = %s", ctx.carga_id, fila, ctx.columna_id(ctx.carga_id, pi)) == 1


def _fila_y_pi(rechazo: str) -> tuple[int, str]:
    """Fila de origen y código del PI de un rechazo escrito como «Fila N, PI X.Y, ...»."""
    partes = re.match(r"Fila ([0-9]+), PI ([0-9]+\.[0-9]+),", rechazo)
    assert partes is not None, f"el rechazo «{rechazo}» no empieza con «Fila N, PI X.Y,»"
    return int(partes[1]), partes[2]


def _valor_leido(ctx: Escenario, fila: int, pi: str) -> Any:
    """Valor de la celda del PI en la fila de origen del export subido, leído con openpyxl."""
    contenido, _ = ctx.ultimo
    hoja = load_workbook(io.BytesIO(contenido), read_only=True).active
    filas = list(hoja.iter_rows(values_only=True))
    (columna,) = [i for i, titulo in enumerate(filas[0]) if str(titulo or "").startswith(f"{pi} [")]
    return filas[fila - 1][columna]


@then(parsers.re(r'la fila del rechazo no muestra el valor leído de la celda'))
def _rechazo_sin_valor(ctx: Escenario) -> None:
    celdas = _celdas(ctx, CONSTANCIA)
    fila_origen, pi = ctx.extras["rechazo"]
    filas = [n for n in range(1, 200) if str(celdas.get(f"A{n}", "")).startswith(f"Fila {fila_origen}, PI {pi},")]
    assert len(filas) == 1
    fila = filas[0]
    assert [ref for ref in celdas if re.fullmatch(rf"[C-Z]+{fila}", ref)] == [], "la fila trae más de dos celdas"
    # El valor leído sale de la celda del export subido y no puede aparecer como número suelto en la fila.
    leido = _valor_leido(ctx, fila_origen, pi)
    assert leido is not None, f"la celda del PI {pi} en la fila {fila_origen} del export está vacía"
    texto = str(int(leido)) if isinstance(leido, float) and leido.is_integer() else str(leido)
    for columna in "AB":
        celda = str(celdas.get(f"{columna}{fila}", ""))
        assert not re.search(rf"(?<![0-9.,]){re.escape(texto)}(?![0-9.,])", celda), (columna, celda)


@then(parsers.re(r'muestra el inicio y el fin en hora de Lima, iguales a carga\.iniciada_en y carga\.terminada_en, con el fin '
                 r'posterior al inicio'))
def _constancia_horas(ctx: Escenario) -> None:
    inicio = datetime.fromisoformat(_valor_de_constancia(ctx, "Inicio (hora de Lima)"))
    fin = datetime.fromisoformat(_valor_de_constancia(ctx, "Fin (hora de Lima)"))
    assert inicio.utcoffset().total_seconds() == -5 * 3600 and fin.utcoffset().total_seconds() == -5 * 3600
    iniciada, terminada = ctx.filas("SELECT iniciada_en, terminada_en FROM abet.carga WHERE carga_id = %s",
                                    ctx.carga_id)[0]
    assert (inicio, fin) == (iniciada, terminada)
    assert fin > inicio


@then(parsers.re(r'muestra "Subido por (?P<correo>[^"]+)"'))
def _constancia_subido_por(ctx: Escenario, correo: str) -> None:
    assert f"Subido por {correo}" in [nombre for nombre, _ in _filas_de_constancia(ctx)]
    assert ctx.uno("SELECT u.correo FROM abet.carga c JOIN acceso.usuario_autorizado u ON u.usuario_id = c.subida_por"
                   " WHERE c.carga_id = %s", ctx.carga_id) == correo


@then(parsers.re(r'muestra la frase fija "(?P<frase>[^"]+)"'))
def _constancia_frase(ctx: Escenario, frase: str) -> None:
    assert frase in [nombre for nombre, _ in _filas_de_constancia(ctx)]


# Entonces, la constancia en JSON

def _archivo_de_la_carga(ctx: Escenario) -> str:
    return _dato_de_la_carga(ctx, "ao.sha256")


@then(parsers.re(r'la respuesta es 200 y su cuerpo es igual al cuerpo de la respuesta 201 de la subida'))
def _constancia_igual_a_la_subida(ctx: Escenario) -> None:
    subida = ctx.extras["subida"]
    assert subida.status_code == 201 and ctx.respuesta.status_code == 200, ctx.respuesta.text
    assert ctx.respuesta.json() == subida.json()


@then(parsers.re(r'el cuerpo trae carga_id, estado "(?P<estado>[A-Z]+)", nombre_archivo "(?P<archivo>[^"]+)", hoja '
                 r'"(?P<hoja>[^"]+)", sha256 igual a archivo_origen\.sha256, filas_de_datos (?P<datos>[0-9]+), filas_leidas '
                 r'(?P<leidas>[0-9]+), filas_aceptadas (?P<aceptadas>[0-9]+) y filas_rechazadas (?P<rechazadas>[0-9]+)'))
def _cuerpo_de_la_constancia(ctx: Escenario, estado: str, archivo: str, hoja: str, datos: str, leidas: str,
                             aceptadas: str, rechazadas: str) -> None:
    cuerpo = ctx.respuesta.json()
    assert cuerpo["carga_id"] == ctx.carga_id
    assert (cuerpo["estado"], cuerpo["nombre_archivo"], cuerpo["hoja"]) == (estado, archivo, hoja)
    assert cuerpo["sha256"] == _archivo_de_la_carga(ctx)
    assert (cuerpo["filas_de_datos"], cuerpo["filas_leidas"], cuerpo["filas_aceptadas"], cuerpo["filas_rechazadas"]) == (
        int(datos), int(leidas), int(aceptadas), int(rechazadas))
    assert ctx.filas("SELECT estado, filas_de_datos, filas_leidas, filas_aceptadas, filas_rechazadas FROM abet.carga"
                     " WHERE carga_id = %s", ctx.carga_id) == [
        (estado, int(datos), int(leidas), int(aceptadas), int(rechazadas))]


@then(parsers.re(r'el cuerpo trae conjunto_reglas "(?P<reglas>[^"]+)", provisional verdadero y 1 aviso con motivo '
                 r'"(?P<motivo>[A-Z_]+)" y PI "(?P<pi>[0-9]\.[0-9])"'))
def _cuerpo_con_aviso(ctx: Escenario, reglas: str, motivo: str, pi: str) -> None:
    cuerpo = ctx.respuesta.json()
    assert cuerpo["conjunto_reglas"] == reglas and cuerpo["provisional"] is True
    assert [(a["motivo"], a["pi"]) for a in cuerpo["avisos"]] == [(motivo, pi)]
    assert ctx.cuenta("rechazo_fila", "carga_id = %s AND efecto = 'AVISO' AND motivo = %s", ctx.carga_id, motivo) == 1


@then(parsers.re(r'la respuesta es 200 y su cuerpo trae estado "(?P<estado>[A-Z]+)", filas_de_datos (?P<datos>[0-9]+), '
                 r'filas_leidas (?P<leidas>[0-9]+), filas_aceptadas (?P<aceptadas>[0-9]+) y filas_rechazadas '
                 r'(?P<rechazadas>[0-9]+)'))
def _cuerpo_rechazada(ctx: Escenario, estado: str, datos: str, leidas: str, aceptadas: str, rechazadas: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    cuerpo = ctx.respuesta.json()
    assert cuerpo["estado"] == estado
    assert (cuerpo["filas_de_datos"], cuerpo["filas_leidas"], cuerpo["filas_aceptadas"], cuerpo["filas_rechazadas"]) == (
        int(datos), int(leidas), int(aceptadas), int(rechazadas))
    assert ctx.filas("SELECT estado, filas_de_datos, filas_leidas, filas_aceptadas, filas_rechazadas FROM abet.carga"
                     " WHERE carga_id = %s", ctx.carga_id) == [
        (estado, int(datos), int(leidas), int(aceptadas), int(rechazadas))]


@then(parsers.re(r'el cuerpo trae 1 rechazo con motivo "(?P<motivo>[A-Z_]+)", efecto "(?P<efecto>[A-Z_]+)" y PI '
                 r'"(?P<pi>[0-9]\.[0-9])"'))
def _cuerpo_con_rechazo(ctx: Escenario, motivo: str, efecto: str, pi: str) -> None:
    rechazos = ctx.respuesta.json()["rechazos"]
    assert [(r["motivo"], r["efecto"], r["pi"]) for r in rechazos] == [(motivo, efecto, pi)]
    assert ctx.cuenta("rechazo_fila", "carga_id = %s AND motivo = %s AND efecto = %s", ctx.carga_id, motivo, efecto) == 1


@then(parsers.re(r'el cuerpo trae el mensaje "(?P<mensaje>[^"]*)", igual al de la respuesta 201 de la subida'))
def _cuerpo_con_mensaje(ctx: Escenario, mensaje: str) -> None:
    assert ctx.respuesta.json()["mensaje"] == mensaje == ctx.extras["subida"].json()["mensaje"]


@then(parsers.re(r'el sha256 del cuerpo es igual a archivo_origen\.sha256 de esa carga'))
def _sha256_del_cuerpo(ctx: Escenario) -> None:
    assert ctx.respuesta.json()["sha256"] == _archivo_de_la_carga(ctx)

