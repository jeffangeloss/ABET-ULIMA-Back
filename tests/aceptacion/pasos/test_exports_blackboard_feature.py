"""Pasos de exports_blackboard.feature (spec 003, US-26 a US-36), ejecutables con pytest-bdd en español.

El .feature manda. Ningún paso cambia una cifra, un mensaje ni un título para que el escenario pase, y cada
«Entonces» se comprueba contra la base, la respuesta de la API, el registro de la API (logger abet.api, con
caplog) o el archivo descargado, sin dobles del sistema bajo prueba. Los pasos que repiten otros .feature
(Antecedentes, subidas, conteos, consultas de control y las copias «una copia de X con ...») viven en el
conftest.py de esta carpeta, y aquí quedan los propios del export real de Blackboard.

Las copias de un .csv o de un .xls las arma el conftest.py con las funciones del generador
(leer_export_texto y a_texto), en memoria y en el formato de su archivo base, y nunca se versionan.

Dos grupos de escenarios se comprueban en otra suite y aquí solo dejan su rastro.
- Los de US-33 (@delegado_a_vitest) los cubre front/tests/pantallas/SubirExport.test.tsx, y cada paso registra
  la propiedad «delegado_a_vitest» con el nombre exacto de la prueba de Vitest, como test_acceso_feature.py.
- El de US-35 (@delegado_a_preflight) lo cubre scripts/probar_preflight.sh, que corre en la CI antes de pytest.
  Este módulo no corre ese guion, comprueba que los casos que lo cubren siguen en él y registra la propiedad
  «delegado_a_preflight» con sus nombres.
"""

from __future__ import annotations

import io
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
from openpyxl import load_workbook
from psycopg import sql
from pytest_bdd import given, parsers, scenarios, then, when

from abet_carga.lector import leer
from abet_carga.modelos import TipoColumna

Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
scenarios("specs/003-exports-blackboard/aceptacion/exports_blackboard.feature")

CSV_410 = "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-59.csv"
XLS_410 = "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-35-54.xls"
TABLAS_DE_LA_CARGA = ("archivo_origen", "carga", "carga_columna", "carga_fila", "estudiante", "medicion",
                      "rechazo_fila")
SUBIDA = "abet.api"


def _encabezados_de_pi() -> tuple[tuple[str, str | None], ...]:
    """Lista común de tests/encabezados_de_pi.py, cargada por su ruta porque tests/ no es un paquete."""
    if "encabezados_de_pi" not in sys.modules:
        import importlib.util

        especificacion = importlib.util.spec_from_file_location("encabezados_de_pi",
                                                                RAIZ / "tests" / "encabezados_de_pi.py")
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules["encabezados_de_pi"] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules["encabezados_de_pi"].ENCABEZADOS_DE_PI


# El lector, con un .xls de texto de dos columnas

def _clasificado(ctx: Escenario, encabezado: str) -> Any:
    """Columna que el lector arma con el encabezado, en un .xls de texto con Username y un nivel."""
    g = ctx.generador
    export = g.Export("", ("Username", encabezado), (("99000001", "4"),))
    contenido = g.a_texto(export, separador="\t", codificacion="utf-16")
    columna = leer(contenido, nombre_archivo=XLS_410).columnas[1]
    # El encabezado que va a la base es el que el lector clasificó, sin espacios a los lados y cortado a 200.
    assert columna.encabezado == encabezado.strip()[:200]
    return columna


@given(parsers.re(r'el encabezado "(?P<encabezado>.*)"$'))
def _el_encabezado(ctx: Escenario, encabezado: str) -> None:
    ctx.extras["encabezado"] = encabezado


@then(parsers.re(r'el lector lo clasifica como (?P<tipo>PI|OTRA) con el código "(?P<pi>[0-9.]*)"'))
def _clasifica(ctx: Escenario, tipo: str, pi: str) -> None:
    columna = _clasificado(ctx, ctx.extras["encabezado"])
    assert (columna.tipo, columna.pi_codigo) == (TipoColumna(tipo), pi or None), (columna.tipo, columna.pi_codigo)


# La base y el encabezado de la columna del PI

@when(parsers.re(r'el dueño de la base cambia el encabezado de la columna del PI (?P<pi>[0-9]\.[0-9]+) de esa carga '
                 r'a "(?P<encabezado>.*)"$'))
def _cambia_encabezado(ctx: Escenario, pi: str, encabezado: str) -> None:
    assert ctx.uno("SELECT current_user = (SELECT pg_get_userbyid(datdba) FROM pg_database"
                   " WHERE datname = current_database())") is True
    ctx.directa = ctx.api.dueno
    ctx.extras["columna"], ctx.extras["encabezado"] = ctx.columna_id(ctx.carga_id, pi), encabezado
    ctx.intentar("UPDATE abet.carga_columna SET encabezado = %s WHERE carga_columna_id = %s",
                 encabezado, ctx.extras["columna"])


@then(parsers.re(r'la base acepta el cambio'))
def _base_acepta(ctx: Escenario) -> None:
    assert ctx.error_directo is None, ctx.error_directo
    assert ctx.uno("SELECT encabezado FROM abet.carga_columna WHERE carga_columna_id = %s",
                   ctx.extras["columna"]) == ctx.extras["encabezado"]


@when(parsers.re(r'cada encabezado de la lista común de tests/encabezados_de_pi\.py se prueba en la columna del PI '
                 r'(?P<pi>[0-9]\.[0-9]+) de esa carga, dentro de una transacción que se deshace'))
def _prueba_la_lista(ctx: Escenario, pi: str) -> None:
    columna = ctx.columna_id(ctx.carga_id, pi)
    original = ctx.uno("SELECT encabezado FROM abet.carga_columna WHERE carga_columna_id = %s", columna)
    resultados = []
    dueno = ctx.api.dueno
    for encabezado, esperado in _encabezados_de_pi():
        leida = _clasificado(ctx, encabezado)
        error = None
        try:
            with dueno.transaction(force_rollback=True):
                dueno.execute("UPDATE abet.carga_columna SET encabezado = %s WHERE carga_columna_id = %s",
                              (leida.encabezado, columna))
        except psycopg.Error as falla:
            error = falla
        resultados.append((encabezado, esperado, leida, error))
    assert ctx.uno("SELECT encabezado FROM abet.carga_columna WHERE carga_columna_id = %s", columna) == original
    ctx.extras["paridad"] = resultados


@then(parsers.re(r'la base acepta cada encabezado que el lector clasifica como el PI (?P<pi>[0-9]\.[0-9]+) y rechaza '
                 r'todos los demás'))
def _paridad(ctx: Escenario, pi: str) -> None:
    resultados = ctx.extras["paridad"]
    assert len(resultados) == len(_encabezados_de_pi()) > 0
    distintos = []
    # Se compara lo que clasifica el lector con lo que acepta la base. Lo que dice la lista del lector lo prueba
    # tests/test_lector.py.
    for encabezado, _, leida, error in resultados:
        es_del_pi = leida.tipo is TipoColumna.PI and leida.pi_codigo == pi
        if es_del_pi and error is not None:
            distintos.append(f"la base rechaza {encabezado!r}, que el lector clasifica como {pi}: {error.sqlstate}")
        if not es_del_pi and (error is None or error.sqlstate != "23514"
                              or error.diag.constraint_name != "ck_carga_columna_encabezado"):
            distintos.append(f"la base no rechaza con ck_carga_columna_encabezado {encabezado!r}, que el lector "
                             f"clasifica como {leida.tipo} {leida.pi_codigo}: {error and error.sqlstate}")
    assert distintos == []
    # La lista tiene casos de los dos lados, así que la comparación no es vacía.
    assert any(leida.pi_codigo == pi for _, _, leida, _ in resultados)
    assert any(leida.pi_codigo != pi for _, _, leida, _ in resultados)


# La carga y sus tablas hijas

@then(parsers.re(r'abet\.medicion tiene (?P<n>[0-9]+) filas de esa carga(?:, (?P<c>[0-9]+) con estado_evidencia '
                 r'"(?P<e1>[A-Z_]+)" y (?P<s>[0-9]+) con "(?P<e2>[A-Z_]+)")?$'))
def _mediciones(ctx: Escenario, n: str, c: str | None, e1: str | None, s: str | None, e2: str | None) -> None:
    assert ctx.cuenta("medicion", "carga_id = %s", ctx.carga_id) == int(n)
    if c is not None:
        assert ctx.cuenta("medicion", "carga_id = %s AND estado_evidencia = %s", ctx.carga_id, e1) == int(c)
        assert ctx.cuenta("medicion", "carga_id = %s AND estado_evidencia = %s", ctx.carga_id, e2) == int(s)


def _pis(texto: str) -> list[str]:
    return sorted(re.findall(r"[0-9]+\.[0-9]+", texto))


@then(parsers.re(r'abet\.carga_columna tiene (?P<n>[0-9]+) filas de esa carga, de los PI (?P<pis>.+)'))
def _columnas_de_la_carga(ctx: Escenario, n: str, pis: str) -> None:
    filas = [f[0] for f in ctx.filas("SELECT pi_codigo FROM abet.carga_columna WHERE carga_id = %s ORDER BY 1",
                                     ctx.carga_id)]
    assert len(filas) == int(n) and filas == _pis(pis), filas


@then(parsers.re(r'abet\.carga_columna de esa carga solo tiene los PI (?P<pis>.+)'))
def _solo_esos_pi(ctx: Escenario, pis: str) -> None:
    assert [f[0] for f in ctx.filas("SELECT pi_codigo FROM abet.carga_columna WHERE carga_id = %s ORDER BY 1",
                                    ctx.carga_id)] == _pis(pis)


@then(parsers.re(r'la columna del PI (?P<pi>[0-9]\.[0-9]+) guarda el encabezado "(?P<encabezado>[^"]+)"'
                 r'(?:, bb_columna_id "(?P<bb>[0-9]+)" y puntaje_maximo_declarado (?P<puntaje>[0-9.]+))?'))
def _columna_guarda(ctx: Escenario, pi: str, encabezado: str, bb: str | None, puntaje: str | None) -> None:
    filas = ctx.filas("SELECT encabezado, bb_columna_id, puntaje_maximo_declarado FROM abet.carga_columna"
                      " WHERE carga_id = %s AND pi_codigo = %s", ctx.carga_id, pi)
    assert len(filas) == 1 and filas[0][0] == encabezado, filas
    if bb is not None:
        assert (filas[0][1], filas[0][2]) == (bb, Decimal(puntaje)), filas


@then(parsers.re(r'la carga queda en estado "(?P<estado>[A-Z]+)" con filas_leidas (?P<leidas>[0-9]+), filas_aceptadas '
                 r'(?P<aceptadas>[0-9]+), filas_rechazadas (?P<rechazadas>[0-9]+) y terminada_en no nulo'))
def _carga_en_estado(ctx: Escenario, estado: str, leidas: str, aceptadas: str, rechazadas: str) -> None:
    assert ctx.carga_id is not None
    assert ctx.filas("SELECT estado, filas_leidas, filas_aceptadas, filas_rechazadas, terminada_en IS NOT NULL"
                     " FROM abet.carga WHERE carga_id = %s", ctx.carga_id) == [
        (estado, int(leidas), int(aceptadas), int(rechazadas), True)]


@then(parsers.re(r'abet\.carga_fila tiene (?P<n>[0-9]+) filas de esa carga y ninguna con fila_origen (?P<sin>[0-9]+)'))
def _filas_de_la_carga(ctx: Escenario, n: str, sin: str) -> None:
    origenes = [f[0] for f in ctx.filas("SELECT fila_origen FROM abet.carga_fila WHERE carga_id = %s", ctx.carga_id)]
    assert len(origenes) == int(n) and int(sin) not in origenes, origenes


@then(parsers.re(r'la medición de (?P<codigo>[0-9]+) en el PI (?P<pi>[0-9]\.[0-9]+) tiene estado_evidencia '
                 r'"(?P<estado>[A-Z_]+)" y nivel_original (?P<nivel>[0-9]+)'))
def _medicion_con_nivel(ctx: Escenario, codigo: str, pi: str, estado: str, nivel: str) -> None:
    assert ctx.filas("SELECT m.estado_evidencia, m.nivel_original FROM abet.medicion m JOIN abet.estudiante e"
                     " USING (estudiante_id) JOIN abet.carga_columna cc USING (carga_columna_id)"
                     " WHERE m.carga_id = %s AND e.codigo = %s AND cc.pi_codigo = %s",
                     ctx.carga_id, codigo, pi) == [(estado, int(nivel))]


def _numero(texto: str) -> Decimal:
    return Decimal(texto.replace(",", "."))


@then(parsers.re(r'abet\.v_r17_por_pi de esa carga da pct_logro_sobre_calificados (?P<pares>[0-9,]+ en [0-9]\.[0-9]+'
                 r'(?:(?:, | y )[0-9,]+ en [0-9]\.[0-9]+)*)'))
def _porcentajes(ctx: Escenario, pares: str) -> None:
    esperados = re.findall(r"([0-9,]+) en ([0-9]\.[0-9]+)", pares)
    assert len(esperados) == 3
    for valor, pi in esperados:
        assert ctx.uno("SELECT pct_logro_sobre_calificados FROM abet.v_r17_por_pi WHERE carga_id = %s AND pi = %s",
                       ctx.carga_id, pi) == _numero(valor), pi


# Rechazos y avisos

def _rechazos(ctx: Escenario) -> list[tuple[Any, ...]]:
    """Filas de rechazo_fila de esa carga, con motivo, efecto, fila, columna y el PI de su pi_id y de su columna."""
    return ctx.filas(
        "SELECT rf.motivo, rf.efecto, rf.fila_origen, rf.carga_columna_id, p.codigo, cc.pi_codigo"
        " FROM abet.rechazo_fila rf LEFT JOIN abet.pi p ON p.pi_id = rf.pi_id"
        " LEFT JOIN abet.carga_columna cc ON cc.carga_columna_id = rf.carga_columna_id"
        " WHERE rf.carga_id = %s ORDER BY rf.rechazo_id", ctx.carga_id)


@then(parsers.re(r'abet\.rechazo_fila tiene los 5 avisos de esa carga y ningún rechazo de fila'))
def _cinco_avisos(ctx: Escenario) -> None:
    filas = _rechazos(ctx)
    assert len(filas) == 5 and all(efecto == "AVISO" for _, efecto, *_ in filas), filas
    puntajes = sorted(columna_pi for motivo, _, fila, _, _, columna_pi in filas
                      if motivo == "PUNTAJE_MAXIMO_DISTINTO" and fila is None)
    assert puntajes == ["5.1", "5.2", "5.3"], filas
    for pi in puntajes:
        assert ctx.uno("SELECT puntaje_maximo_declarado FROM abet.carga_columna WHERE carga_id = %s AND pi_codigo = %s",
                       ctx.carga_id, pi) == Decimal(100)
    fuera = [f for f in filas if f[0] == "COLUMNA_PI_FUERA_DEL_PLAN"]
    assert len(fuera) == 2 and all(f[2:5] == (None, None, None) for f in fuera), filas


@then(parsers.re(r'abet\.rechazo_fila tiene exactamente (?P<n>[0-9]+) filas? de esa carga, con motivo "(?P<motivo>[A-Z_]+)", '
                 r'efecto "(?P<efecto>[A-Z_]+)", fila_origen nulo y carga_columna_id nulo'))
def _rechazo_de_la_carga(ctx: Escenario, n: str, motivo: str, efecto: str) -> None:
    filas = _rechazos(ctx)
    assert len(filas) == int(n), filas
    assert all(f[:4] == (motivo, efecto, None, None) for f in filas), filas


@then(parsers.re(r'esa fila guarda en pi_id el PI (?P<pi>[0-9]\.[0-9]+)'))
def _rechazo_con_pi(ctx: Escenario, pi: str) -> None:
    filas = _rechazos(ctx)
    assert len(filas) == 1 and filas[0][4] == pi, filas


@then(parsers.re(r'abet\.rechazo_fila tiene (?P<n>[0-9]+) filas (?P<motivo>[A-Z_]+) de esa carga, con efecto '
                 r'"(?P<efecto>[A-Z_]+)" y fila_origen, carga_columna_id y pi_id nulos'))
def _avisos_sin_columna(ctx: Escenario, n: str, motivo: str, efecto: str) -> None:
    filas = [f for f in _rechazos(ctx) if f[0] == motivo]
    assert len(filas) == int(n) and all(f[1:5] == (efecto, None, None, None) for f in filas), filas


# El archivo de origen y su huella

def _sha_de_la_carga(ctx: Escenario, carga_id: int | None) -> str:
    assert carga_id is not None
    return ctx.uno("SELECT sha256 FROM abet.archivo_origen WHERE archivo_id = (SELECT archivo_id FROM abet.carga"
                   " WHERE carga_id = %s)", carga_id)


@then(parsers.re(r'archivo_origen\.filas_de_datos es (?P<n>[0-9]+)'))
def _filas_de_datos(ctx: Escenario, n: str) -> None:
    assert ctx.uno("SELECT filas_de_datos FROM abet.archivo_origen WHERE archivo_id = (SELECT archivo_id"
                   " FROM abet.carga WHERE carga_id = %s)", ctx.carga_id) == int(n)


@then(parsers.re(r'archivo_origen\.sha256 cumple "(?P<patron>[^"]+)" y es igual a la salida de "shasum -a 256" '
                 r'sobre (?P<ruta>tests/datos_inventados/\S+)'))
def _sha256_igual_a_shasum(ctx: Escenario, patron: str, ruta: str) -> None:
    sha = _sha_de_la_carga(ctx, ctx.carga_id)
    assert re.fullmatch(patron, sha)
    salida = subprocess.run(["shasum", "-a", "256", str(RAIZ / ruta)], capture_output=True, text=True, check=True)
    assert salida.stdout.split()[0] == sha


@then(parsers.re(r'la huella de la copia sin BOM es distinta de archivo_origen\.sha256 de la carga publicada'))
def _huella_sin_bom(ctx: Escenario) -> None:
    contenido, nombre = ctx.ultimo
    assert contenido.startswith(b"\xef\xbb\xbf")
    copia, _ = ctx.copia_de(f'una copia de "{nombre}" sin BOM')
    assert copia == contenido[3:]
    assert ctx.cuenta("carga", "carga_id = %s AND estado = 'PUBLICADA'", ctx.carga_id) == 1
    assert ctx.huella(copia) != _sha_de_la_carga(ctx, ctx.carga_id)


@then(parsers.re(r'archivo_origen\.sha256 es distinta de la huella de "(?P<nombre>[^"]+)"'))
def _huella_distinta_de(ctx: Escenario, nombre: str) -> None:
    sha = _sha_de_la_carga(ctx, ctx.carga_id)
    assert sha == ctx.huella(ctx.ultimo[0]) and sha != ctx.huella(ctx.de_inventados(nombre))


@then(parsers.re(r'abet\.archivo_origen sigue con 1 fila para esa huella'))
def _una_fila_por_huella(ctx: Escenario) -> None:
    assert ctx.cuenta("archivo_origen", "sha256 = %s", ctx.huella(ctx.ultimo[0])) == 1


@then(parsers.re(r'archivo_origen\.nombre_archivo sigue siendo "(?P<nombre>[^"]+)"'))
def _nombre_guardado(ctx: Escenario, nombre: str) -> None:
    assert [f[0] for f in ctx.filas("SELECT nombre_archivo FROM abet.archivo_origen")] == [nombre]


@then(parsers.re(r'el cuerpo de la respuesta no contiene ese carga_id, la huella del archivo ni el número de la sección 410'))
def _cuerpo_sin_datos_ajenos(ctx: Escenario) -> None:
    texto = ctx.respuesta.text
    assert ctx.carga_previa is not None
    assert str(ctx.carga_previa) not in texto and ctx.huella(ctx.ultimo[0]) not in texto and "410" not in texto


# Lo que la carga descarta del .xls

def _columnas_de_texto(ctx: Escenario) -> list[tuple[str, str, str]]:
    """Columnas de texto de las tablas de abet que escribe la carga y de todas las tablas de acceso."""
    return ctx.filas(
        "SELECT c.table_schema, c.table_name, c.column_name FROM information_schema.columns c"
        " JOIN information_schema.tables t USING (table_schema, table_name)"
        " WHERE t.table_type = 'BASE TABLE'"
        " AND ((c.table_schema = 'abet' AND c.table_name = ANY(%s)) OR c.table_schema = 'acceso')"
        " AND c.data_type IN ('text', 'character varying', 'character', 'name', 'json', 'jsonb', 'USER-DEFINED')"
        " ORDER BY 1, 2, 3", list(TABLAS_DE_LA_CARGA))


def _textos_buscados(lista: str) -> list[str]:
    textos = []
    for parte in re.findall(r'"[^"]+"(?: a "[^"]+")?', lista):
        rango = re.fullmatch(r'"(.+?) ([0-9]+)" a "\1 ([0-9]+)"', parte)
        if rango:
            ancho = len(rango[2])
            textos += [f"{rango[1]} {n:0{ancho}d}" for n in range(int(rango[2]), int(rango[3]) + 1)]
        else:
            textos.append(parte.strip('"'))
    return textos


@then(parsers.re(r'una búsqueda con igualdad exacta de (?P<lista>.+) en las columnas de texto de las tablas de abet '
                 r'que escribe la carga y de acceso devuelve 0 coincidencias'))
def _sin_textos_del_archivo(ctx: Escenario, lista: str) -> None:
    textos = _textos_buscados(lista)
    assert len(textos) == 16 and "Inventado 11" in textos and "19.00" in textos, textos
    columnas = _columnas_de_texto(ctx)
    tablas_de_abet = {tabla for esquema, tabla, _ in columnas if esquema == "abet"}
    assert tablas_de_abet and tablas_de_abet <= set(TABLAS_DE_LA_CARGA), tablas_de_abet
    assert any(esquema == "acceso" for esquema, _, _ in columnas)
    halladas = []
    for esquema, tabla, columna in columnas:
        consulta = sql.SQL("SELECT count(*) FROM {}.{} WHERE {}::text = ANY(%s)").format(
            sql.Identifier(esquema), sql.Identifier(tabla), sql.Identifier(columna))
        if ctx.api.dueno.execute(consulta, (textos,)).fetchone()[0]:
            halladas.append(f"{esquema}.{tabla}.{columna}")
    assert halladas == []


# El registro de la API

@then(parsers.re(r'el registro trae "evento=archivo_detenido" con la huella, "motivo=(?P<motivo>[A-Z_]+)" y '
                 r'"detalle=(?P<detalle>[A-Z_]+|-)", sin el nombre del archivo'))
def _registro(ctx: Escenario, motivo: str, detalle: str) -> None:
    contenido, nombre = ctx.ultimo
    caplog = ctx.request.getfixturevalue("caplog")
    lineas = [r.getMessage() for r in caplog.records if r.name == SUBIDA and "evento=archivo_detenido" in r.getMessage()]
    assert len(lineas) == 1, lineas
    assert re.fullmatch(rf"evento=archivo_detenido hora=\S+ sha256={ctx.huella(contenido)} motivo={motivo}"
                        rf" detalle={re.escape(detalle)}", lineas[0]), lineas[0]
    assert nombre not in caplog.text and nombre.rsplit(".", 1)[0] not in caplog.text


# La constancia y el R-17 de un export de texto

@when(parsers.re(r'el profesor pide la constancia de esa carga y descarga su R-17'))
def _constancia_y_r17(ctx: Escenario) -> None:
    cliente = ctx.sesion(ctx.profesor)
    constancia = cliente.get(f"/api/cargas/{ctx.carga_id}")
    r17 = cliente.get(f"/api/cargas/{ctx.carga_id}/r17.xlsx")
    assert constancia.status_code == 200, constancia.text
    assert r17.status_code == 200, r17.text[:300]
    ctx.extras["constancia"], ctx.extras["r17"] = constancia.json(), r17.content


@then(parsers.re(r'el cuerpo de la constancia trae hoja (?:nula|"(?P<hoja>[^"]+)")(?: y nombre_archivo "(?P<nombre>[^"]+)")?'))
def _cuerpo_de_la_constancia(ctx: Escenario, hoja: str | None, nombre: str | None) -> None:
    cuerpo = ctx.extras["constancia"]
    assert "hoja" in cuerpo and cuerpo["hoja"] == hoja, cuerpo.get("hoja")
    if nombre is not None:
        assert cuerpo["nombre_archivo"] == nombre


@then(parsers.re(r'la hoja "(?P<hoja>[^"]+)" del R-17 muestra en la fila "(?P<rotulo>[^"]+)" el texto "(?P<texto>[^"]+)"'))
def _fila_del_r17(ctx: Escenario, hoja: str, rotulo: str, texto: str) -> None:
    libro = load_workbook(io.BytesIO(ctx.extras["r17"]), read_only=True, data_only=True)
    try:
        valores = [fila[1] for fila in libro[hoja].iter_rows(min_col=1, max_col=2, values_only=True) if fila[0] == rotulo]
    finally:
        libro.close()
    assert valores == [texto], valores


# US-33, delegado a Vitest

VITEST = "front/tests/pantallas/SubirExport.test.tsx › P3 Subir export › "
CUBIERTO_POR_VITEST = {
    "que el profesor abre P3 de la sección 410": (
        "muestra la sección elegida fija, el campo de .xlsx, .csv y .xls, el botón Subir y el rótulo del piloto"),
    'el campo "archivo" tiene accept': (
        "muestra la sección elegida fija, el campo de .xlsx, .csv y .xls, el botón Subir y el rótulo del piloto"),
    'pulsa "Subir" sin elegir un archivo': "sin archivo no sale ninguna petición y pide elegirlo",
    'P3 muestra "Elija el archivo del export': "sin archivo no sale ninguna petición y pide elegirlo",
    'elige "export_410.pdf" sin el filtro del diálogo': (
        "envía tal cual un archivo de otro tipo, sin aviso propio, y muestra el detail del 422"),
    "P3 envía ese archivo una vez con su nombre": (
        "envía tal cual un archivo de otro tipo, sin aviso propio, y muestra el detail del 422"),
}


def _delegar(ctx: Escenario, texto: str) -> None:
    """Deja constancia de un paso de pantalla y de la prueba de Vitest que lo comprueba en el Front."""
    pruebas = [prueba for inicio, prueba in CUBIERTO_POR_VITEST.items() if texto.startswith(inicio)]
    assert len(pruebas) == 1, f"el paso de pantalla «{texto}» no tiene una prueba de Vitest anotada"
    ctx.request.node.user_properties.append(("delegado_a_vitest", f"{texto} → {VITEST}{pruebas[0]}"))


@given(parsers.re(r'(?P<texto>que el profesor abre P3 de la sección 410)'))
def _abre_p3(ctx: Escenario, texto: str) -> None:
    _delegar(ctx, texto)


@when(parsers.re(r'(?P<texto>pulsa "Subir" sin elegir un archivo|elige "export_410\.pdf" sin el filtro del diálogo y '
                 r'pulsa "Subir")'))
def _accion_en_p3(ctx: Escenario, texto: str) -> None:
    _delegar(ctx, texto)


@then(parsers.re(r'(?P<texto>el campo "archivo" tiene accept .+|P3 muestra .+|P3 envía ese archivo .+)'))
def _p3_muestra(ctx: Escenario, texto: str) -> None:
    _delegar(ctx, texto)


# US-35, delegado a scripts/probar_preflight.sh

PREFLIGHT = "scripts/probar_preflight.sh"
CUBIERTO_POR_PREFLIGHT = (
    ".xls UTF-16 con 20231234 falla",
    ".csv UTF-16 con 20231234 falla",
    ".csv UTF-8 con BOM y 20231234 falla",
    "texto Windows-1252 con 20231234 falla",
    ".txt con 20231234 en la carpeta falla",
    ".xls OLE inventado falla",
    ".xls UTF-16 con BOM y 99000001,99000002 pasa",
)


def _delegar_a_preflight(ctx: Escenario, texto: str) -> None:
    """Deja constancia del paso y de los casos de probar_preflight.sh que lo cubren, que siguen en el guion."""
    guion = (RAIZ / PREFLIGHT).read_text(encoding="utf-8")
    for caso in CUBIERTO_POR_PREFLIGHT:
        assert re.search(rf'^caso(?:_por)? "{re.escape(caso)}" ', guion, flags=re.M), f"{PREFLIGHT} ya no trae «{caso}»"
    ctx.request.node.user_properties.append(
        ("delegado_a_preflight", f"{texto} → {PREFLIGHT}: " + "; ".join(CUBIERTO_POR_PREFLIGHT)))


@given(parsers.re(r'(?P<texto>en tests/datos_inventados/ un \.xls UTF-16 con BOM, .+)'))
def _archivos_de_preflight(ctx: Escenario, texto: str) -> None:
    _delegar_a_preflight(ctx, texto)


@when(parsers.re(r'(?P<texto>corre "bash scripts/preflight\.sh --staged" con cada uno)'))
def _corre_preflight(ctx: Escenario, texto: str) -> None:
    _delegar_a_preflight(ctx, texto)


@then(parsers.re(r'(?P<texto>cada corrida falla por la regla 2 sin mostrar el código, .+)'))
def _preflight_falla(ctx: Escenario, texto: str) -> None:
    _delegar_a_preflight(ctx, texto)
