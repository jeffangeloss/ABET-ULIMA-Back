"""Pasos de r17_industrial.feature (US-78 de la spec 008), con pytest-bdd en español (T036).

El .feature manda. Cada «Entonces» se comprueba con el libro que descarga la ruta 7, con la respuesta de la ruta 12 o
con la base desechable del escenario, sin dobles del sistema bajo prueba. Los Antecedentes arman la base de la spec 008
con el plan de 5643 en 2026-1 para IND, el PI 6.1, el «Portafolio 3» y la descripción de prueba, en el clúster
desechable de tests/cluster_desechable.py y nunca en localhost:5432, y publican la carga inventada de la 701 con 34
filas por la ruta 5.

Aquí están los escenarios del Back de BR-R17-13, B6 con la carrera de la carga, y los que fijan que lo demás del R-17
no cambia con Industrial. Los escenarios de P6 llevan @delegado_a_vitest y los prueba Vitest en el Front.
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from pytest_bdd import given, parsers, scenario, then, when

Escenario = Any
A = sys.modules["api_de_prueba"]
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/r17_industrial.feature"
HOJA = "Cursos de Carrera"
EXPORT_410 = "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-36-02.xlsx"
NO_LOGRADO = "El indicador aún no alcanza lo esperado, pero es una buena oportunidad para mejorar"
# Textos inventados del PI 6.1 y del SO 6 en cada catálogo, para que la ruta 12 muestre de cuál los toma.
TEXTOS = {"AMB-2026": ("Texto inventado del PI 6.1 de AMB-2026.", "Texto inventado del SO 6 de AMB-2026."),
          "IND-2026": ("Texto inventado del PI 6.1 de IND-2026.", "Texto inventado del SO 6 de IND-2026.")}


@scenario(FEATURE, "El encabezado dice la carrera de la carga")
def test_el_encabezado_dice_la_carrera_de_la_carga() -> None:
    """T036, con sus dos Ejemplos."""


@scenario(FEATURE, "Ninguna otra celda de la plantilla nombra a Ambiental")
def test_ninguna_otra_celda_nombra_a_ambiental() -> None:
    """T036."""


@scenario(FEATURE, "La cabecera y el bloque I traen la sección, el periodo y el instrumento")
def test_la_cabecera_y_el_bloque_i() -> None:
    """T036."""


@scenario(FEATURE, "Las cifras del R-17 siguen la regla de la meta de Industrial")
def test_las_cifras_siguen_la_regla_de_la_meta() -> None:
    """T036."""


@scenario(FEATURE, "La franja provisional nombra el conjunto de Industrial")
def test_la_franja_provisional_nombra_el_conjunto() -> None:
    """T036."""


@scenario(FEATURE, "La tabla de estudiantes trae SO, PI, código y nivel, sin nombres ni el profesor")
def test_la_tabla_de_estudiantes_sin_nombres() -> None:
    """T036."""


@scenario(FEATURE, "Un PI sin descriptores de rúbrica no cambia el R-17")
def test_un_pi_sin_descriptores_no_cambia_el_r17() -> None:
    """T036."""


@scenario(FEATURE, "Otro profesor del curso no descarga el R-17 de la 701")
def test_otro_profesor_no_descarga_el_r17() -> None:
    """T036."""


@scenario(FEATURE, "El SO y el PI de la ruta 12 salen del catálogo de Industrial y no del de Ambiental")
def test_la_ruta_12_usa_el_catalogo_de_industrial() -> None:
    """T036."""


# Ayudas

def _publicar(ctx: Escenario, quien: str, numero: str, contenido: bytes, nombre: str,
              asignatura: str | None = None) -> int:
    respuesta = A.subir(ctx.sesion(quien), ctx.seccion_de(numero, asignatura), contenido, nombre)
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "PUBLICADA", respuesta.text
    return int(respuesta.json()["carga_id"])


def _descargar(ctx: Escenario, quien: str, carga_id: int) -> Any:
    ctx.respuesta = ctx.sesion(quien).get(f"/api/cargas/{carga_id}/r17.xlsx")
    return ctx.respuesta


def _libro(ctx: Escenario, contenido: bytes | None = None) -> Any:
    if contenido is None:
        assert ctx.respuesta.status_code == 200, ctx.respuesta.text[:300]
        contenido = ctx.respuesta.content
    return load_workbook(io.BytesIO(contenido))


def _hoja(ctx: Escenario) -> Any:
    if "hoja" not in ctx.extras:
        ctx.extras["hoja"] = _libro(ctx)[HOJA]
    return ctx.extras["hoja"]


def _celdas(libro: Any) -> dict[tuple[str, str], Any]:
    """Valor y formato de cada celda con valor de cada hoja, para comparar dos libros sin la fecha de creación."""
    return {(hoja.title, celda.coordinate): (celda.value, celda.number_format)
            for hoja in libro.worksheets for fila in hoja.iter_rows() for celda in fila if celda.value is not None}


def _carrera_de(ctx: Escenario, carga_id: int) -> str:
    return ctx.uno("SELECT c.codigo FROM abet.carga cg JOIN abet.carrera c USING (carrera_id) WHERE cg.carga_id = %s",
                   carga_id)


# Dado

@given(parsers.re(r'la carga PUBLICADA inventada de la (?P<numero>70[0-9]) con (?P<n1>[0-9]+) de nivel 1, '
                  r'(?P<n2>[0-9]+) de nivel 2, (?P<n3>[0-9]+) de nivel 3 y (?P<n4>[0-9]+) de nivel 4'))
def _carga_de_quimica(ctx: Escenario, numero: str, n1: str, n2: str, n3: str, n4: str) -> None:
    niveles = (1,) * int(n1) + (2,) * int(n2) + (3,) * int(n3) + (4,) * int(n4)
    contenido, nombre = ctx.export_de_quimica(numero, niveles)
    quien = f"docente{numero}@example.invalid"
    ctx.carga_id = _publicar(ctx, quien, numero, contenido, nombre)
    ctx.extras["701"] = (quien, ctx.carga_id)


@given(parsers.re(r'una carga PUBLICADA inventada de (?P<asignatura>[0-9]+) cuyo plan es de (?P<carrera>[A-Z]+)'))
def _carga_de_la_carrera(ctx: Escenario, asignatura: str, carrera: str) -> None:
    if asignatura == "5643":
        # La de los Antecedentes, porque la 701 ya tiene su carga PUBLICADA.
        quien, carga_id = ctx.extras["701"]
    else:
        quien = "docente410@example.invalid"
        carga_id = _publicar(ctx, quien, "410", ctx.de_inventados(EXPORT_410), EXPORT_410, asignatura)
    assert _carrera_de(ctx, carga_id) == carrera
    ctx.extras["de_la_carrera"] = (quien, carga_id)


@given(parsers.re(r'que IND-2026 tiene 0 filas en abet\.rubrica_nivel'))
def _sin_descriptores(ctx: Escenario) -> None:
    assert ctx.uno("SELECT count(*) FROM abet.rubrica_nivel r JOIN abet.pi p USING (pi_id)"
                   " JOIN abet.catalogo_version cv USING (catalogo_version_id) WHERE cv.codigo = 'IND-2026'") == 0


@given(parsers.re(r'el PI 6\.1 y el SO 6 en AMB-2026 y en IND-2026 con textos inventados distintos en cada catálogo'))
def _textos_por_catalogo(ctx: Escenario) -> None:
    for catalogo, (texto_pi, texto_so) in TEXTOS.items():
        cambiados = ctx.api.dueno.execute(
            "UPDATE abet.pi p SET descripcion = %s FROM abet.catalogo_version cv"
            " WHERE cv.catalogo_version_id = p.catalogo_version_id AND cv.codigo = %s AND p.codigo = '6.1'",
            (texto_pi, catalogo)).rowcount
        assert cambiados == 1, f"{catalogo} no tiene el PI 6.1"
        cambiados = ctx.api.dueno.execute(
            "UPDATE abet.so s SET descripcion = %s FROM abet.catalogo_version cv"
            " WHERE cv.catalogo_version_id = s.catalogo_version_id AND cv.codigo = %s AND s.numero = 6",
            (texto_so, catalogo)).rowcount
        assert cambiados == 1, f"{catalogo} no tiene el SO 6"


# Cuando

@when("se descarga su R-17")
def _descarga_su_r17(ctx: Escenario) -> None:
    _descargar(ctx, *ctx.extras["de_la_carrera"])


@when(parsers.re(r'(?:el profesor descarga el R-17 de la carga de la 701'
                 r'|se recorren todas las celdas de todas las hojas del R-17 de la 701)'))
def _descarga_la_701(ctx: Escenario) -> None:
    _descargar(ctx, *ctx.extras["701"])


@when(parsers.re(r'pide GET /api/cargas/\{carga\}/r17\.xlsx de la carga de la 701'))
def _otro_pide(ctx: Escenario) -> None:
    _descargar(ctx, ctx.extras["con_sesion"], ctx.extras["701"][1])


@when(parsers.re(r'el profesor pide GET /api/resultados\?periodo=(?P<periodo>[0-9]{4}-[0-9])'))
def _pide_resultados(ctx: Escenario, periodo: str) -> None:
    ctx.respuesta = ctx.sesion(ctx.profesor).get("/api/resultados", params={"periodo": periodo})


# Entonces

@then(parsers.re(r'la celda B6 dice «(?P<texto>[^»]+)»'))
def _b6(ctx: Escenario, texto: str) -> None:
    assert _hoja(ctx)["B6"].value == texto


@then("ninguna celda dice «Ambiental»")
def _sin_ambiental(ctx: Escenario) -> None:
    libro = _libro(ctx)
    con_ambiental = [f"{hoja}!{celda}" for (hoja, celda), (valor, _) in _celdas(libro).items()
                     if isinstance(valor, str) and "ambiental" in valor.lower()]
    assert not con_ambiental, con_ambiental
    assert "ambiental" not in (libro.properties.title or "").lower()


@then(parsers.re(r'el archivo se llama "(?P<nombre>[^"]+)"'))
def _nombre(ctx: Escenario, nombre: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text[:300]
    assert ctx.respuesta.headers["content-disposition"] == f'attachment; filename="{nombre}"'


@then(parsers.re(r'D8 dice "(?P<d8>[^"]+)", D11 dice "(?P<d11>[^"]+)" e I11 dice "(?P<i11>[^"]+)"'))
def _cabecera(ctx: Escenario, d8: str, d11: str, i11: str) -> None:
    hoja = _hoja(ctx)
    assert (hoja["D8"].value, hoja["D11"].value, hoja["I11"].value) == (d8, d11, i11)


@then(parsers.re(r'B15 dice «(?P<texto>[^»]+)»'))
def _b15(ctx: Escenario, texto: str) -> None:
    assert _hoja(ctx)["B15"].value == texto


@then(parsers.re(r'E17 dice «(?P<e17>[^»]+)» y G17 dice "(?P<g17>[^"]+)"'))
def _bloque_i(ctx: Escenario, e17: str, g17: str) -> None:
    hoja = _hoja(ctx)
    assert (hoja["E17"].value, hoja["G17"].value) == (e17, g17)


@then(parsers.re(r'M24 vale (?P<m24>[0-9]+), M25 vale (?P<m25>[0-9]+) y M26 vale (?P<a>[0-9]+) / (?P<b>[0-9]+)'))
def _frecuencias(ctx: Escenario, m24: str, m25: str, a: str, b: str) -> None:
    hoja = _hoja(ctx)
    assert (hoja["M24"].value, hoja["M25"].value) == (int(m24), int(m25))
    assert hoja["M26"].value == int(a) / int(b)


@then(parsers.re(r'E24 vale (?P<e24>[0-9]+,[0-9]+) con el formato (?P<formato>\S+ %) y G24 vale (?P<g24>[0-9]+,[0-9]+)'))
def _bloque_ii(ctx: Escenario, e24: str, formato: str, g24: str) -> None:
    hoja = _hoja(ctx)
    assert hoja["E24"].value == float(e24.replace(",", "."))
    # El .feature escribe el formato con un espacio antes de «%», como lo muestra Excel en español; la celda lo guarda
    # sin el espacio.
    assert hoja["E24"].number_format == formato.replace(" ", "")
    assert hoja["G24"].value == float(g24.replace(",", "."))


@then(parsers.re(r'H24 trae el texto de NO_LOGRADO, «(?P<texto>[^»]+)»'))
def _h24(ctx: Escenario, texto: str) -> None:
    assert texto == NO_LOGRADO
    assert _hoja(ctx)["H24"].value == texto


@then(parsers.re(r'B7 dice «(?P<texto>[^»]+)»'))
def _franja(ctx: Escenario, texto: str) -> None:
    assert _hoja(ctx)["B7"].value == texto


@then(parsers.re(r'las filas (?P<desde>[0-9]+) a (?P<hasta>[0-9]+) traen en B, C, E y F el SO (?P<so>[0-9]+), el PI '
                 r'(?P<pi>[0-9.]+), el código y el nivel de cada estudiante'))
def _tabla(ctx: Escenario, desde: str, hasta: str, so: str, pi: str) -> None:
    hoja = _hoja(ctx)
    esperadas = ctx.filas(
        "SELECT e.codigo, m.nivel_original FROM abet.medicion m JOIN abet.estudiante e USING (estudiante_id)"
        " WHERE m.carga_id = %s ORDER BY m.fila_origen", ctx.extras["701"][1])
    filas = range(int(desde), int(hasta) + 1)
    assert len(esperadas) == len(filas)
    leidas = [(hoja[f"B{n}"].value, hoja[f"C{n}"].value, hoja[f"E{n}"].value, hoja[f"F{n}"].value) for n in filas]
    assert leidas == [(int(so), pi, codigo, nivel) for codigo, nivel in esperadas]
    assert hoja[f"B{int(hasta) + 1}"].value is None


@then(parsers.re(r'la columna D y la celda D10 quedan vacías, como fija BR-R17-07'))
def _sin_nombres(ctx: Escenario) -> None:
    hoja = _hoja(ctx)
    assert hoja["D10"].value is None
    assert [hoja[f"D{n}"].value for n in range(43, 43 + 142)] == [None] * 142


@then("ninguna celda contiene una fórmula")
def _sin_formulas(ctx: Escenario) -> None:
    libro = _libro(ctx)
    formulas = [f"{hoja.title}!{celda.coordinate}" for hoja in libro.worksheets for fila in hoja.iter_rows()
                for celda in fila if celda.data_type == "f"]
    assert not formulas, formulas


@then(parsers.re(r'la ruta 7 responde 200 con el mismo libro que con descriptores, porque abet_carga/r17\.py no lee '
                 r'abet\.rubrica_nivel'))
def _mismo_libro(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text[:300]
    sin_descriptores = _celdas(_libro(ctx))
    ctx.api.dueno.execute(
        "INSERT INTO abet.rubrica_nivel (pi_id, nivel, descriptor)"
        " SELECT p.pi_id, n.nivel, 'Descriptor inventado del nivel ' || n.nivel FROM abet.pi p"
        " JOIN abet.catalogo_version cv USING (catalogo_version_id), (VALUES (1), (2), (3), (4)) AS n (nivel)"
        " WHERE cv.codigo = 'IND-2026' AND p.codigo = '6.1'")
    assert _descargar(ctx, *ctx.extras["701"]).status_code == 200
    assert _celdas(_libro(ctx)) == sin_descriptores
    assert "rubrica_nivel" not in (RAIZ / "abet_carga" / "r17.py").read_text(encoding="utf-8")


@then(parsers.re(r'recibe 403 con «(?P<mensaje>[^»]+)»'))
def _recibe_403(ctx: Escenario, mensaje: str) -> None:
    assert ctx.respuesta.status_code == 403, ctx.respuesta.text
    assert ctx.respuesta.json() == {"detail": mensaje}


@then(parsers.re(r'el PI 6\.1 trae el instrumento «(?P<instrumento>[^»]+)» del plan de IND-2026 y la respuesta no '
                 r'repite ningún texto inventado de AMB-2026'))
def _pi_de_industrial(ctx: Escenario, instrumento: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    cuerpo = ctx.respuesta.json()
    [seccion] = [s for s in cuerpo["secciones"] if s["numero"] == "701"]
    [indicador] = [i for i in seccion["indicadores"] if i["pi"] == "6.1"]
    assert indicador["instrumento"] == instrumento
    texto = json.dumps(cuerpo, ensure_ascii=False)
    assert not [ajeno for ajeno in TEXTOS["AMB-2026"] if ajeno in texto]


@then(parsers.re(r'el SO 6 trae el texto inventado de IND-2026'))
def _so_de_industrial(ctx: Escenario) -> None:
    so = {fila["numero"]: fila["descripcion"] for fila in ctx.respuesta.json()["so"]}
    assert so == {6: TEXTOS["IND-2026"][1]}


@then(parsers.re(r'la 701 trae logrados (?P<logrados>[0-9]+), calificados (?P<calificados>[0-9]+), '
                 r'pct_sobre_calificados (?P<pct>[0-9.]+), meta_pct (?P<meta>[0-9.]+) y en_meta (?P<en_meta>falso|verdadero)'))
def _cifras_de_la_701(ctx: Escenario, logrados: str, calificados: str, pct: str, meta: str, en_meta: str) -> None:
    [seccion] = [s for s in ctx.respuesta.json()["secciones"] if s["numero"] == "701"]
    [indicador] = seccion["indicadores"]
    assert (indicador["logrados"], indicador["calificados"]) == (int(logrados), int(calificados))
    assert (indicador["pct_sobre_calificados"], indicador["meta_pct"]) == (float(pct), float(meta))
    assert indicador["en_meta"] is (en_meta == "verdadero")
    assert re.fullmatch(r"[0-9]+", str(seccion["carga_id"]))


# Fuera del .feature

def test_ninguna_celda_fuera_de_b6_nombra_una_carrera(ctx: Escenario) -> None:
    """Cambio del 2026-11-24 (FR-015). El escenario busca solo «Ambiental», y FR-015 pide que ninguna celda fuera de B6
    nombre una carrera. En el R-17 de la 701 de Industrial y en el de la 410 de Ambiental, B6 debe decir «Carrera de»
    más el nombre de la carrera de la carga. No debe haber otra celda de ninguna hoja con «Carrera de» ni con el nombre
    de una fila de abet.carrera, salvo las que copian tal cual una descripción del catálogo. La descripción del PI 6.1
    de IND-2026 en C17 dice «ingeniería industrial», y es un texto del catálogo de la carrera, no de la plantilla."""
    ctx.crear_base("quimica_plan")
    nombres = {codigo: nombre for codigo, nombre in ctx.filas("SELECT codigo, nombre FROM abet.carrera")}
    assert {"IND", "AMB"} <= set(nombres), nombres
    del_catalogo = {texto for (texto,) in ctx.filas("SELECT descripcion FROM abet.pi WHERE descripcion IS NOT NULL"
                                                    " UNION SELECT descripcion FROM abet.so WHERE descripcion IS NOT NULL")}
    contenido, nombre_701 = ctx.export_de_quimica("701", (1, 2, 3, 4))
    cargas = (("docente701@example.invalid", _publicar(ctx, "docente701@example.invalid", "701", contenido, nombre_701),
               "IND"),
              ("docente410@example.invalid", _publicar(ctx, "docente410@example.invalid", "410",
                                                      ctx.de_inventados(EXPORT_410), EXPORT_410, "450002"), "AMB"))
    for quien, carga_id, carrera in cargas:
        assert _carrera_de(ctx, carga_id) == carrera
        _descargar(ctx, quien, carga_id)
        libro = _libro(ctx)
        assert libro[HOJA]["B6"].value == f"Carrera de {nombres[carrera]}"
        otras = [f"{hoja}!{celda}" for (hoja, celda), (valor, _) in _celdas(libro).items()
                 if (hoja, celda) != (HOJA, "B6") and isinstance(valor, str) and valor not in del_catalogo
                 and ("carrera de" in valor.lower() or any(n.lower() in valor.lower() for n in nombres.values()))]
        assert not otras, (carrera, otras)
