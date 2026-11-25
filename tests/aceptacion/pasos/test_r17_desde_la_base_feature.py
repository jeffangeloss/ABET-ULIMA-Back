"""Pasos de r17_desde_la_base.feature (spec 005, US-50 y US-51, BR-R17-04, BR-R17-11 y BR-R17-12), con pytest-bdd.

El .feature manda. Ningún paso cambia un texto para que el escenario pase, y cada «Entonces» se comprueba contra
la base o contra el libro descargado por la API, sin dobles del sistema bajo prueba. Este módulo enlaza con @scenario
los ocho escenarios de US-50 y los cuatro de US-51. Desde US-49 el R-17 sale solo con la declaración vigente completa,
así que «tiene declarados …» llama a declarar() de tests/cargas_de_prueba.py con los textos del escenario, y
«con su análisis declarado» es el paso compartido de conftest.py (T037). La declaración que no cabe y la corrección
pasan por las rutas 15 y 16, como en declaracion.feature.

«El dueño de la base» usa la conexión del dueño de la copia desechable, la misma de las consultas de los pasos,
y nunca toca Neon. En Neon, la descripción la carga Jefferson desde el Windows con el guion (AD-20).
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path
from typing import Any

import psycopg
from openpyxl import load_workbook
from pytest_bdd import given, parsers, scenario, then, when

from abet_carga import r17

Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/005-oportunidades-de-mejora/aceptacion/r17_desde_la_base.feature"
GUION = RAIZ / "db" / "datos" / "descripcion_instrumento_2026_2.sql"
HOJA = "Cursos de Carrera"
PIS = ("5.1", "5.2", "5.3")
CELDAS = {"5.1": "G17", "5.2": "G18", "5.3": "G19"}
DEL_PLAN = (
    "FROM abet.plan_medicion pm JOIN abet.pi p ON p.pi_id = pm.pi_id"
    " JOIN abet.asignatura a ON a.asignatura_id = pm.asignatura_id JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id"
    " WHERE a.codigo = %s AND pe.codigo = %s"
)
FIJAR = ("UPDATE abet.plan_medicion pm SET descripcion_instrumento = %s FROM abet.pi p, abet.asignatura a,"
         " abet.periodo pe WHERE p.pi_id = pm.pi_id AND a.asignatura_id = pm.asignatura_id"
         " AND pe.periodo_id = pm.periodo_id AND p.codigo = %s AND a.codigo = %s AND pe.codigo = %s")
PLANTILLA = RAIZ / "plantillas" / "R017_ambiental_general.xlsx"
OM, BP, SIN_CALIFICACIONES = "Oportunidad de mejora.", "Buena práctica.", "Sin calificaciones en esta carga."
CORRECCION_410 = ("La entrega coincidió con la semana de parciales y de feriado.",
                  "Mover la entrega a la semana 10 y revisar el avance en tutoría.")
TEXTOS = {
    '"   "': "   ",
    '" Texto de prueba." (blanco al comienzo)': " Texto de prueba.",
    '"Texto de prueba. " (blanco al final)': "Texto de prueba. ",
    "un texto de 401 caracteres": "x" * 401,
}


@scenario(FEATURE, "B29 y B34 traen un párrafo por PI de la 410, en el orden del plan")
def test_b29_y_b34_traen_un_parrafo_por_pi() -> None:
    """US-50, escenario 1."""


@scenario(FEATURE, "Una buena práctica y dos oportunidades de mejora conviven en los recuadros")
def test_una_bp_y_dos_om_conviven() -> None:
    """US-50, escenario 2."""


@scenario(FEATURE, "Un PI sin calificaciones se nombra sin análisis")
def test_un_pi_sin_calificaciones_se_nombra_sin_analisis() -> None:
    """US-50, escenario 3, D-40."""


@scenario(FEATURE, "La plantilla oficial no cambia con los párrafos por PI")
def test_la_plantilla_oficial_no_cambia() -> None:
    """US-50, escenario 4, D-08 y D-41."""


@scenario(FEATURE, "Tres PI con causas y acciones de 800 caracteres caben y no tapan la tabla de frecuencias")
def test_tres_pi_de_800_caracteres_caben() -> None:
    """US-50, escenario 5, J-39."""


@scenario(FEATURE, "Una declaración cuyo recuadro no cabe en el R-17 se rechaza")
def test_una_declaracion_que_no_cabe_se_rechaza() -> None:
    """US-50, escenario 6, J-39."""


@scenario(FEATURE, "Un texto que parece fórmula queda como cadena")
def test_un_texto_que_parece_formula_queda_como_cadena() -> None:
    """US-50, escenario 7, BR-R17-04."""


@scenario(FEATURE, "El R-17 trae el texto de la última declaración")
def test_el_r17_trae_la_ultima_declaracion() -> None:
    """US-50, escenario 8, D-37."""


@scenario(FEATURE, "G17, G18 y G19 traen la descripción de cada PI")
def test_g17_g18_y_g19_traen_la_descripcion_de_cada_pi() -> None:
    """US-51, escenario 1."""


@scenario(FEATURE, "Sin descripción en la base, G17:I19 queda vacía")
def test_sin_descripcion_en_la_base_g17_i19_queda_vacia() -> None:
    """US-51, escenario 2."""


@scenario(FEATURE, "La base rechaza una descripción en blanco, con blancos a los lados o demasiado larga")
def test_la_base_rechaza_una_descripcion_mal_formada() -> None:
    """US-51, escenario 3, con sus cuatro Ejemplos."""


@scenario(FEATURE, "El guion de datos se corre dos veces y deja las mismas tres descripciones")
def test_el_guion_de_datos_se_corre_dos_veces() -> None:
    """US-51, escenario 4."""


# Ayudas

def _descripciones(ctx: Escenario, asignatura: str = "450002",
                   periodo: str = "2026-2") -> dict[str, str | None]:
    return dict(ctx.filas(f"SELECT p.codigo, pm.descripcion_instrumento {DEL_PLAN} ORDER BY p.numero",
                          asignatura, periodo))


def _hoja(ctx: Escenario) -> Any:
    if "hoja_r17" not in ctx.extras:
        assert ctx.respuesta.status_code == 200, ctx.respuesta.text[:300]
        ctx.extras["hoja_r17"] = load_workbook(io.BytesIO(ctx.respuesta.content))[HOJA]
    return ctx.extras["hoja_r17"]


def _cargas() -> Any:
    """tests/cargas_de_prueba.py, el mismo módulo que carga el conftest del arnés."""
    return sys.modules["cargas_de_prueba"]


def _registros() -> dict[str, tuple[str, str]]:
    return dict(_cargas().REGISTROS_DE_PRUEBA["410"])


def _parrafos(ctx: Escenario, celda: str) -> list[str]:
    hoja = _hoja(ctx)
    assert hoja[celda].data_type == "s", hoja[celda].data_type
    return hoja[celda].value.split("\n")


def _tabla_de_frecuencias(ctx: Escenario) -> list[list[Any]]:
    """K28:Q31 como debe quedar, armada desde la ruta 13 de la misma carga y no desde el libro."""
    respuesta = ctx.sesion(ctx.profesor).get(f"/api/cargas/{ctx.carga_id}/indicadores")
    assert respuesta.status_code == 200, respuesta.text
    filas: list[list[Any]] = [list(r17.ENCABEZADOS_DE_FRECUENCIAS)]
    for i in respuesta.json()["indicadores"]:
        logran = f"{i['logrados']} de {i['calificados']}" if i["logrados"] is not None else None
        filas.append([i["pi"], *i["estudiantes_por_nivel"], logran, i["pct_sobre_total"]])
    return filas


def _frecuencias_del_libro(ctx: Escenario, desde: int = 28) -> list[list[Any]]:
    hoja = _hoja(ctx)
    filas = [[hoja[f"{columna}{fila}"].value for columna in "KLMNOPQ"] for fila in range(desde, 32)]
    for fila in filas[(1 if desde == 28 else 0):]:
        fila[6] = round(100 * fila[6], 1) if fila[6] is not None else None
    return filas


def _plantilla() -> Any:
    return load_workbook(PLANTILLA)[HOJA]


def _put(ctx: Escenario, correo: str, registros: dict[str, tuple[str, str]], version: int) -> Any:
    tipos = {i["pi"]: i["tipo_registro"] for i in ctx.sesion(correo).get(
        f"/api/cargas/{ctx.carga_id}/indicadores").json()["indicadores"]}
    cuerpo = {"version": version, "indicadores": [{"pi": pi, "tipo": tipos[pi], "causa": causa, "accion": accion}
                                                  for pi, (causa, accion) in registros.items()]}
    ctx.respuesta = ctx.sesion(correo).put(f"/api/cargas/{ctx.carga_id}/mejora/borrador", json=cuerpo)
    return ctx.respuesta


# Antecedentes propios de este archivo

@given(parsers.re(r'acceso\.docente_seccion asigna la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" a '
                  r'"(?P<correo>[^"]+)"'))
def _asigna(ctx: Escenario, numero: str, asignatura: str, correo: str) -> None:
    assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion WHERE usuario_id = %s AND seccion_id = %s",
                   ctx.usuario_id(correo), ctx.seccion_id(numero, asignatura)) == 1


@given(parsers.re(r'"(?P<correo>[^"]+)" activo con rol "(?P<rol>[A-Z]+)" y sin secciones en acceso\.docente_seccion'))
def _sin_secciones(ctx: Escenario, correo: str, rol: str) -> None:
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, True)]
    assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion WHERE usuario_id = %s", ctx.usuario_id(correo)) == 0


@given(parsers.re(r'ninguna sección de (?P<periodo>[0-9]{4}-[0-2]) tiene cargas'))
def _sin_cargas(ctx: Escenario, periodo: str) -> None:
    assert ctx.uno("SELECT count(*) FROM abet.carga c JOIN abet.seccion s ON s.seccion_id = c.seccion_id"
                   " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id WHERE pe.codigo = %s", periodo) == 0


# Dado, la descripción en la base

@given(parsers.re(r'que el dueño de la base fija en abet\.plan_medicion de "(?P<asignatura>[0-9]+)" en '
                  r'"(?P<periodo>[^"]+)" una descripción distinta para 5\.1, 5\.2 y 5\.3, cada una «Texto de prueba\.» '
                  r'seguido del número de su PI'))
def _fija_descripciones(ctx: Escenario, asignatura: str, periodo: str) -> None:
    for pi in PIS:
        cambiadas = ctx.api.dueno.execute(FIJAR, (f"Texto de prueba. {pi}", pi, asignatura, periodo)).rowcount
        assert cambiadas == 1, pi
    ctx.extras["descripciones"] = _descripciones(ctx, asignatura, periodo)


@given(parsers.re(r'que abet\.plan_medicion de "(?P<asignatura>[0-9]+)" en "(?P<periodo>[^"]+)" no tiene '
                  r'descripcion_instrumento en ningún PI'))
def _sin_descripciones(ctx: Escenario, asignatura: str, periodo: str) -> None:
    assert _descripciones(ctx, asignatura, periodo) == {pi: None for pi in PIS}


@given(parsers.re(r'una conexión directa del dueño de la base'))
def _conexion_del_dueno(ctx: Escenario) -> None:
    ctx.directa = ctx.pila.enter_context(psycopg.connect(ctx.api.base.conexion, autocommit=True))
    assert ctx.directa.execute("SELECT current_user").fetchone()[0] != ctx.api.base.rol_app


# Dado, la declaración de US-50

@given(parsers.re(r'que la carga tiene declarados los registros de prueba de la 410(?P<resto>.*)'))
def _declarados(ctx: Escenario, resto: str) -> None:
    registros = _registros()
    if resto == " en 5.1 y 5.2":
        registros.pop("5.3")
    elif (bp := re.fullmatch(r' en 5\.1 y 5\.2, y en 5\.3 la causa «(?P<causa>[^»]+)» y la acción «(?P<accion>[^»]+)»',
                             resto)):
        registros["5.3"] = (bp["causa"], bp["accion"])
    elif (formula := re.fullmatch(r', con la causa de 5\.1 cambiada por «(?P<causa>[^»]+)»', resto)):
        registros["5.1"] = (formula["causa"], registros["5.1"][1])
    else:
        assert resto == "", f"la frase «{resto}» no tiene paso en este módulo"
    ctx.extras["registros"] = registros
    _cargas().declarar(ctx.api.dueno, ctx.carga_id, registros, correo=ctx.profesor)


@given("que la carga tiene declaradas, en 5.1, 5.2 y 5.3, causas y acciones de 800 caracteres sin saltos de línea")
def _declaradas_de_800(ctx: Escenario) -> None:
    registros = {pi: (chr(ord("p") + i) * 800, chr(ord("a") + i) * 800) for i, pi in enumerate(PIS)}
    ctx.extras["registros"] = registros
    _cargas().declarar(ctx.api.dueno, ctx.carga_id, registros, correo=ctx.profesor)


@given(parsers.re(r'que "(?P<correo>[^"]+)" guardó en la versión 1 los registros de prueba de la 410, con la causa de '
                  r'5\.1 cambiada por un texto de (?P<n>[0-9]+) caracteres con (?P<saltos>[0-9]+) saltos de línea'))
def _guardo_sin_cabida(ctx: Escenario, correo: str, n: str, saltos: str) -> None:
    causa = ("\n" * int(saltos) + "x" * int(n))[:int(n)]
    assert len(causa) == int(n) and causa.count("\n") == int(saltos)
    registros = _registros()
    registros["5.1"] = (causa, registros["5.1"][1])
    assert _put(ctx, correo, registros, 0).json()["version"] == 1, ctx.respuesta.text
    ctx.antes = ctx.conteos()


@given(parsers.re(r'que "(?P<correo>[^"]+)" corrigió la declaración con la corrección de la 410'))
def _corrigio(ctx: Escenario, correo: str) -> None:
    ctx.extras["anterior"] = ctx.uno("SELECT max(declaracion_id) FROM abet.mejora_declaracion WHERE carga_id = %s",
                                     ctx.carga_id)
    registros = _registros()
    registros["5.1"] = CORRECCION_410
    version = ctx.uno("SELECT version FROM abet.mejora_borrador WHERE carga_id = %s", ctx.carga_id)
    assert _put(ctx, correo, registros, version).status_code == 200, ctx.respuesta.text
    declarada = ctx.sesion(correo).post(f"/api/cargas/{ctx.carga_id}/mejora/declaracion", json={"version": version + 1})
    assert declarada.status_code == 201, declarada.text


# Cuando

@when(parsers.re(r'(?P<quien>"[^"]+") descarga el R-17 de esa carga'))
def _descarga_r17(ctx: Escenario, quien: str) -> None:
    assert ctx.carga_id is not None
    ctx.extras.pop("hoja_r17", None)
    ctx.respuesta = ctx.sesion(quien.strip('"')).get(f"/api/cargas/{ctx.carga_id}/r17.xlsx")


@when(parsers.re(r'"(?P<correo>[^"]+)" declara la versión (?P<version>[0-9]+)'))
def _declara(ctx: Escenario, correo: str, version: str) -> None:
    ctx.respuesta = ctx.sesion(correo).post(f"/api/cargas/{ctx.carga_id}/mejora/declaracion",
                                            json={"version": int(version)})


@when(parsers.re(r'esa conexión fija en abet\.plan_medicion la descripcion_instrumento (?P<texto>.+)'))
def _fija_mal_formada(ctx: Escenario, texto: str) -> None:
    assert texto in TEXTOS, f"el texto «{texto}» no tiene valor en este módulo"
    ctx.extras["anterior"] = _descripciones(ctx)["5.1"]
    ctx.intentar(FIJAR, TEXTOS[texto], "5.1", "450002", "2026-2")


@when(parsers.re(r'esa conexión corre dos veces db/datos/descripcion_instrumento_2026_2\.sql'))
def _corre_dos_veces(ctx: Escenario) -> None:
    corridas = []
    for _ in range(2):
        ctx.plantillas.base_desechable._psql(ctx.api.base.nombre, "-f", str(GUION))
        corridas.append(_descripciones(ctx))
    ctx.extras["corridas"] = corridas


# Entonces

@then(parsers.re(r'G17 trae el texto del PI 5\.1, G18 el del PI 5\.2 y G19 el del PI 5\.3'))
def _g_trae_cada_texto(ctx: Escenario) -> None:
    hoja, esperadas = _hoja(ctx), ctx.extras["descripciones"]
    assert [hoja[f"B{celda[1:]}"].value for celda in CELDAS.values()] == list(PIS)
    assert {pi: hoja[celda].value for pi, celda in CELDAS.items()} == esperadas
    assert all(hoja[celda].data_type == "s" for celda in CELDAS.values())


@then(parsers.re(r'los tres textos son distintos entre sí'))
def _distintos(ctx: Escenario) -> None:
    hoja = _hoja(ctx)
    textos = [hoja[celda].value for celda in CELDAS.values()]
    assert all(textos) and len(set(textos)) == 3


@then(parsers.re(r'G17, G18 y G19 están vacías'))
def _g_vacias(ctx: Escenario) -> None:
    hoja = _hoja(ctx)
    assert [hoja[f"{columna}{fila}"].value for fila in (17, 18, 19) for columna in "GHI"] == [None] * 9


@then(parsers.re(r'el R-17 no inventa ningún texto de descripción'))
def _no_inventa(ctx: Escenario) -> None:
    hoja = _hoja(ctx)
    textos = [str(celda.value) for fila in hoja.iter_rows() for celda in fila if celda.value is not None]
    assert not [texto for texto in textos if texto.startswith("Texto de prueba")]
    # El nombre del instrumento sigue en E y no se copia a G.
    assert [hoja[f"E{fila}"].value for fila in (17, 18, 19)] == ["Trabajo Integrador"] * 3


@then(parsers.re(r'la base rechaza el cambio por el largo de la columna'))
def _rechaza_por_largo(ctx: Escenario) -> None:
    assert ctx.error_directo is not None, "la base aceptó la sentencia"
    assert isinstance(ctx.error_directo, psycopg.errors.StringDataRightTruncation), type(ctx.error_directo)


@then(parsers.re(r'abet\.plan_medicion conserva su descripción anterior'))
def _conserva(ctx: Escenario) -> None:
    assert _descripciones(ctx)["5.1"] == ctx.extras["anterior"]


@then(parsers.re(r'abet\.plan_medicion de "(?P<asignatura>[0-9]+)" en "(?P<periodo>[^"]+)" tiene las mismas '
                 r'(?P<n>[0-9]+) descripciones tras la primera y tras la segunda corrida'))
def _mismas(ctx: Escenario, asignatura: str, periodo: str, n: str) -> None:
    primera, segunda = ctx.extras["corridas"]
    assert primera == segunda == _descripciones(ctx, asignatura, periodo)
    assert len([texto for texto in primera.values() if texto]) == int(n)
    assert all(texto.startswith("Texto de prueba.") for texto in primera.values())


@then(parsers.re(r'ninguna de las tres descripciones está repetida en otro PI'))
def _no_repetidas(ctx: Escenario) -> None:
    textos = list(ctx.extras["corridas"][-1].values())
    assert len(set(textos)) == 3
    assert ctx.uno("SELECT count(*) FROM abet.plan_medicion WHERE descripcion_instrumento IS NOT NULL") == 3


# Entonces, US-50

@then(parsers.re(r'(?P<celda>B29|B34) trae como cadena tres párrafos separados por un salto de línea, en este orden'))
def _tres_parrafos(ctx: Escenario, celda: str, datatable: list[list[str]]) -> None:
    assert datatable[0] == ["párrafo"]
    assert _parrafos(ctx, celda) == [fila[0] for fila in datatable[1:]]


@then("ningún párrafo trae una cifra de logro ni de meta")
def _sin_cifras(ctx: Escenario) -> None:
    for celda in ("B29", "B34"):
        for parrafo in _parrafos(ctx, celda):
            resto = re.sub(r"^[0-9]+\.[0-9]+ · ", "", parrafo)
            assert "%" not in resto and not re.search(r"[0-9]+[,.][0-9]", resto), parrafo


@then(parsers.re(r'el (?P<orden>primer|tercer) párrafo de (?P<celda>B29|B34) es (?:la cadena )?«(?P<texto>[^»]+)»'))
def _parrafo(ctx: Escenario, orden: str, celda: str, texto: str) -> None:
    assert _parrafos(ctx, celda)[0 if orden == "primer" else 2] == texto


@then(parsers.re(r'los párrafos de 5\.1 y 5\.2 empiezan con «(?P<a>[^»]+)» y «(?P<b>[^»]+)»'))
def _empiezan(ctx: Escenario, a: str, b: str) -> None:
    for celda in ("B29", "B34"):
        primero, segundo, _ = _parrafos(ctx, celda)
        assert primero.startswith(a + " ") and segundo.startswith(b + " "), (primero, segundo)


@then(parsers.re(r'el tercer párrafo de B29 y el de B34 son «(?P<texto>[^»]+)»(?: \(propuesta\))?'))
def _tercero_en_los_dos(ctx: Escenario, texto: str) -> None:
    assert _parrafos(ctx, "B29")[2] == _parrafos(ctx, "B34")[2] == texto


@then("ningún recuadro trae texto del profesor para 5.3")
def _sin_texto_de_5_3(ctx: Escenario) -> None:
    causa, accion = _cargas().REGISTROS_DE_PRUEBA["410"]["5.3"]
    for celda in ("B29", "B34"):
        texto = _hoja(ctx)[celda].value
        assert causa not in texto and accion not in texto
        assert [p for p in texto.split("\n") if p.startswith("5.3")] == [f"5.3 · {SIN_CALIFICACIONES}"]
    assert ctx.cuenta("mejora_declaracion_pi", "carga_id = %s AND pi_id = (SELECT pi_id FROM abet.carga_columna"
                      " WHERE carga_id = %s AND pi_codigo = '5.3')", ctx.carga_id, ctx.carga_id) == 0


@then("B28 y B33 traen los enunciados literales de plantillas/R017_ambiental_general.xlsx")
def _enunciados(ctx: Escenario) -> None:
    hoja, plantilla = _hoja(ctx), _plantilla()
    for celda in ("B28", "B33"):
        assert hoja[celda].value == plantilla[celda].value and plantilla[celda].value


@then("las 45 celdas combinadas del libro, B29:I31 y B34:I36 entre ellas, son las de la plantilla")
def _combinadas(ctx: Escenario) -> None:
    de_la_plantilla = {str(rango) for rango in _plantilla().merged_cells.ranges}
    del_libro = {str(rango) for rango in _hoja(ctx).merged_cells.ranges}
    assert len(de_la_plantilla) == 45 and {"B29:I31", "B34:I36"} <= de_la_plantilla
    # La franja PROVISIONAL de BR-R17-05 combina además B7:I7, la única celda que el R-17 suma a la plantilla.
    assert del_libro - {"B7:I7"} == de_la_plantilla


@then("K28:Q31 conserva sus valores")
def _k28_q31(ctx: Escenario) -> None:
    assert _frecuencias_del_libro(ctx) == _tabla_de_frecuencias(ctx)


@then("B29 y B34 tienen ajuste de texto y alineación arriba")
def _ajuste(ctx: Escenario) -> None:
    for celda in ("B29", "B34"):
        alineacion = _hoja(ctx)[celda].alignment
        assert alineacion.wrap_text is True and alineacion.vertical == "top", celda


@then("el alto de las filas 31 y 36 crece hasta mostrar el texto completo, según el cálculo de r17.py, sin pasar de "
      "409 puntos")
def _alto(ctx: Escenario) -> None:
    hoja = _hoja(ctx)
    for celda, fila, indice in (("B29", 31, 0), ("B34", 36, 1)):
        texto = hoja[celda].value
        assert [p.split(f"{OM} ", 1)[1] for p in texto.split("\n")] == [
            ctx.extras["registros"][pi][indice] for pi in PIS]
        alto = hoja.row_dimensions[fila].height
        assert alto == r17.alto_de_fila_final(r17.lineas_del_recuadro(texto))
        assert 15.0 < alto <= 409.0, alto


@then("K31:Q31 conserva sus valores")
def _k31_q31(ctx: Escenario) -> None:
    assert _frecuencias_del_libro(ctx, desde=31) == _tabla_de_frecuencias(ctx)[-1:]


@then("las filas 29, 30, 34 y 35 conservan su alto")
def _altos_de_la_plantilla(ctx: Escenario) -> None:
    hoja, plantilla = _hoja(ctx), _plantilla()
    for fila in (29, 30, 34, 35):
        assert hoja.row_dimensions[fila].height == plantilla.row_dimensions[fila].height, fila


@then(parsers.re(r'la API responde 422 con el mensaje "(?P<mensaje>[^"]+)"(?: \(propuesta\))?'))
def _422(ctx: Escenario, mensaje: str) -> None:
    assert ctx.respuesta.status_code == 422, ctx.respuesta.text
    assert ctx.respuesta.json() == {"detail": mensaje}


@then("ninguna celda del libro es una fórmula")
def _sin_formulas(ctx: Escenario) -> None:
    libro = load_workbook(io.BytesIO(ctx.respuesta.content))
    assert not [celda.coordinate for hoja in libro.worksheets for fila in hoja.iter_rows() for celda in fila
                if celda.data_type == "f"]


@then("los párrafos de 5.2 y 5.3 no cambian")
def _no_cambian(ctx: Escenario) -> None:
    registros = _registros()
    for celda, indice in (("B29", 0), ("B34", 1)):
        assert _parrafos(ctx, celda)[1:] == [f"{pi} · {OM} {registros[pi][indice]}" for pi in ("5.2", "5.3")]


@then("abet.mejora_declaracion conserva la declaración anterior con sus filas de abet.mejora_declaracion_pi")
def _conserva_la_anterior(ctx: Escenario) -> None:
    anterior = ctx.extras["anterior"]
    assert ctx.cuenta("mejora_declaracion", "carga_id = %s", ctx.carga_id) == 2
    filas = ctx.filas("SELECT cc.pi_codigo, d.causa, d.accion FROM abet.mejora_declaracion_pi d"
                      " JOIN abet.carga_columna cc ON cc.carga_id = d.carga_id AND cc.pi_id = d.pi_id"
                      " WHERE d.declaracion_id = %s ORDER BY cc.pi_codigo", anterior)
    assert filas == [(pi, *_registros()[pi]) for pi in PIS]
