"""Pasos de resumen_del_curso.feature, la ruta 20 GET /api/resumen-curso y la 21 (T021 y T022 de la spec 009, US-91 y US-93).

El .feature manda. Los Antecedentes arman la base de la spec 009 con el plan de 5643 en 2026-1 y los datos inventados de
Química General (conftest.py), y cada sección del escenario nace en su paso Dado con los alumnos de «los niveles
[a, b, c, d]». Cada «Entonces» se comprueba con la respuesta de la API y con la base desechable del escenario, sin dobles
del sistema bajo prueba, en el clúster desechable de tests/cluster_desechable.py y nunca en localhost:5432.

La lista cerrada de claves de la ruta 20 se compara con la que fija la sección 16.2 de docs/03-api/contrato.md del Front
cuando ABET_FRONT_RAIZ la señala, y siempre con la lista que este módulo escribe a mano. Los porcentajes de cada sección
se comparan con la vista del R-17 y con la celda E del bloque II del R-17 que genera abet_carga.r17 para la misma carga.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from pytest_bdd import given, parsers, scenario, then, when

from abet_carga import r17

Escenario = Any
C = sys.modules["cargas_de_prueba"]
FEATURE = "specs/009-resumen-del-curso/aceptacion/resumen_del_curso.feature"
CORREO = r"[a-z0-9.]+@example\.invalid"
COORDINACION_DEL_CURSO = "coordinador.quimica@example.invalid"
CLAVES = {"periodo", "asignatura", "indicadores"}
CLAVES_DE_UN_INDICADOR = ["so", "pi", "nivel_esperado", "meta_pct", "provisional", "curso", "conteo_secciones", "secciones"]
CLAVES_DEL_CURSO = ["estudiantes_por_nivel", "logrados", "calificados", "sin_evidencia", "total",
                    "pct_sobre_calificados", "promedio_nivel", "en_meta"]
CLAVES_DE_UNA_SECCION = ["seccion_id", "numero", "estado", "carga_id", "logrados", "calificados", "sin_evidencia",
                         "pct_sobre_calificados", "promedio_nivel", "en_meta"]
CLAVES_DEL_CONTEO = ["total", "publicadas", "en_meta", "debajo_de_la_meta", "sin_dato"]
FILAS_DEL_BLOQUE_II = (24, 25, 26)
OCHO_CIFRAS = re.compile(r"(?<![0-9])[0-9]{8}(?![0-9])")
RUTA = "/api/resumen-curso"


# Escenarios de US-91

@scenario(FEATURE, "El curso suma alumnos de las secciones publicadas y no promedia porcentajes")
def test_el_curso_suma_alumnos_y_no_promedia_porcentajes() -> None:
    """T021."""


@scenario(FEATURE, "Cada sección trae sus cifras en orden de número y la sección sin carga no inventa un porcentaje")
def test_cada_seccion_trae_sus_cifras_en_orden() -> None:
    """T021."""


@scenario(FEATURE, "El conteo de secciones cuenta la meta solo sobre las publicadas")
def test_el_conteo_de_secciones_cuenta_la_meta_solo_sobre_las_publicadas() -> None:
    """T021."""


@scenario(FEATURE, "Cada porcentaje de sección es el de su R-17")
def test_cada_porcentaje_de_seccion_es_el_de_su_r17() -> None:
    """T021."""


@scenario(FEATURE, "El curso cumple con el 80,0 justo y no cumple con 75,0, igual que el R-17")
def test_el_curso_cumple_con_el_80_justo_y_no_con_75() -> None:
    """T021."""


@scenario(FEATURE, "Un curso sin cargas publicadas trae nulos y no ceros")
def test_un_curso_sin_cargas_publicadas_trae_nulos() -> None:
    """T021."""


@scenario(FEATURE, "Con un conjunto de reglas provisional el curso sale provisional")
def test_con_un_conjunto_provisional_el_curso_sale_provisional() -> None:
    """T021."""


@scenario(FEATURE, "La respuesta del resumen trae solo las claves de su lista cerrada")
def test_la_respuesta_trae_solo_las_claves_de_su_lista_cerrada() -> None:
    """T021."""


@scenario(FEATURE, "El profesor recibe 403 en el resumen del curso")
def test_el_profesor_recibe_403() -> None:
    """T021."""


@scenario(FEATURE, "La coordinación de Ambiental recibe el resumen de 5643 sin indicadores")
def test_la_coordinacion_de_ambiental_recibe_el_resumen_sin_indicadores() -> None:
    """T021."""


@scenario(FEATURE, "Sin sesión el resumen responde 401")
def test_sin_sesion_el_resumen_responde_401() -> None:
    """T021."""


@scenario(FEATURE, "Un periodo o una asignatura mal formados responden 422 sin leer la base")
def test_un_periodo_o_una_asignatura_mal_formados_responden_422() -> None:
    """T021."""


# Escenarios de US-93

@scenario(FEATURE, "La coordinación de la carrera recibe la lista de sus cursos con plan en el periodo")
def test_la_coordinacion_de_la_carrera_recibe_la_lista_de_sus_cursos() -> None:
    """T022."""


@scenario(FEATURE, "La coordinación del curso recibe solo su curso")
def test_la_coordinacion_del_curso_recibe_solo_su_curso() -> None:
    """T022."""


# Ayudas

def _cuerpo(ctx: Escenario, codigo: int = 200) -> Any:
    assert ctx.respuesta is not None, "el escenario todavía no pidió nada"
    assert ctx.respuesta.status_code == codigo, ctx.respuesta.text
    assert ctx.respuesta.headers["cache-control"] == "no-store"
    return ctx.respuesta.json()


def _indicador(ctx: Escenario, pi: str) -> dict[str, Any]:
    [indicador] = [i for i in _cuerpo(ctx)["indicadores"] if i["pi"] == pi]
    return indicador


def _seccion(ctx: Escenario, numero: str, pi: str = "6.1") -> dict[str, Any]:
    [seccion] = [s for s in _indicador(ctx, pi)["secciones"] if s["numero"] == numero]
    return seccion


def _valor(texto: str) -> Any:
    """Valor de una cifra del .feature, como 69.7, 4, «SIN_CARGA», verdadero, falso, null o [3, 7, 13, 10]."""
    if texto == "verdadero":
        return True
    if texto == "falso":
        return False
    if texto == "null":
        return None
    if texto.startswith("["):
        return [int(n) for n in re.findall(r"[0-9]+", texto)]
    if texto.startswith('"'):
        return texto.strip('"')
    return float(texto) if "." in texto else int(texto)


_PAR = re.compile(r'(?P<clave>[a-z_]+)(?: (?P<valor>"[^"]*"|\[[^\]]*\]|[0-9]+(?:\.[0-9]+)?|verdadero|falso|null))?'
                  r'(?:, | y |$)')


def _pares(texto: str) -> dict[str, Any]:
    """Pares «clave valor» de una frase del .feature. Una clave sin valor, antes de «en null», vale None."""
    pares: dict[str, Any] = {}
    for tramo in texto.split(" con "):
        con_nulos = tramo.endswith(" en null")
        resto = tramo.removesuffix(" en null")
        posicion = 0
        while posicion < len(resto):
            par = _PAR.match(resto, posicion)
            assert par is not None and par.end() > posicion, f"no se entiende «{resto[posicion:]}» de «{texto}»"
            if par["valor"] is None:
                assert con_nulos, f"«{par['clave']}» no trae su valor en «{texto}»"
                pares[par["clave"]] = None
            else:
                pares[par["clave"]] = _valor(par["valor"])
            posicion = par.end()
    return pares


def _comprobar(obtenido: dict[str, Any], esperado: dict[str, Any], donde: str) -> None:
    for clave, valor in esperado.items():
        assert clave in obtenido, f"{donde} no trae «{clave}»"
        assert obtenido[clave] == valor and type(obtenido[clave]) is type(valor), \
            f"{donde}: {clave} es {obtenido[clave]!r} y el escenario dice {valor!r}"


def _pedir(ctx: Escenario, correo: str | None, ruta: str) -> None:
    ctx.extras["ruta"] = ruta
    if correo is not None:
        ctx.extras["con_sesion"] = correo
    cliente = ctx.sesion(correo) if correo is not None else ctx.api.cliente()
    ctx.respuesta = cliente.get(ruta)


def _ruta_del_resumen(asignatura: str, periodo: str) -> str:
    return f"{RUTA}?periodo={periodo}&asignatura={asignatura}"


def _contrato_del_front() -> dict[str, Any] | None:
    """Respuesta de ejemplo de la sección 16.2 del contrato del Front, o None sin ABET_FRONT_RAIZ."""
    raiz = os.environ.get("ABET_FRONT_RAIZ")
    contrato = Path(raiz) / "docs" / "03-api" / "contrato.md" if raiz else None
    if contrato is None or not contrato.is_file():
        return None
    texto = contrato.read_text(encoding="utf-8")
    seccion = texto.split("### 16.2", 1)[1].split("```jsonc", 1)[1].split("```", 1)[0]
    return json.loads("\n".join(linea for linea in seccion.splitlines() if not linea.lstrip().startswith("//")))


def _forma(valor: Any) -> Any:
    """Claves de un objeto, con la forma de sus objetos anidados y de los de sus listas, sin los valores."""
    if isinstance(valor, dict):
        return {clave: _forma(hijo) for clave, hijo in valor.items()}
    if isinstance(valor, list) and valor and isinstance(valor[0], dict):
        return [_forma(valor[0])]
    return None


# Dado

@given(parsers.re(rf'(?P<correo>{CORREO}) con sesión'))
def _con_sesion(ctx: Escenario, correo: str) -> None:
    assert ctx.filas("SELECT activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(True,)]
    ctx.sesion(correo)
    ctx.extras["con_sesion"] = correo


@given(parsers.re(rf'(?P<correo>{CORREO}) con alcance de la carrera (?P<carrera>[A-Z]+)'))
def _con_alcance_de_carrera(ctx: Escenario, correo: str, carrera: str) -> None:
    assert ctx.uno("SELECT count(*) FROM acceso.coordinacion_alcance ca JOIN acceso.usuario_autorizado u USING (usuario_id)"
                   " JOIN abet.carrera c USING (carrera_id) WHERE u.correo = %s AND c.codigo = %s", correo, carrera) == 1
    ctx.sesion(correo)
    ctx.extras["con_sesion"] = correo


@given(parsers.re(rf'(?P<correo>{CORREO}) con alcance de la asignatura (?P<asignatura>[0-9]+) en (?P<periodo>[0-9]{{4}}-[0-9])'))
def _con_alcance_de_asignatura(ctx: Escenario, correo: str, asignatura: str, periodo: str) -> None:
    assert ctx.uno("SELECT count(*) FROM acceso.coordinacion_alcance ca JOIN acceso.usuario_autorizado u USING (usuario_id)"
                   " JOIN abet.asignatura a USING (asignatura_id) JOIN abet.periodo pe ON pe.periodo_id = ca.periodo_id"
                   " WHERE u.correo = %s AND a.codigo = %s AND pe.codigo = %s", correo, asignatura, periodo) == 1
    ctx.sesion(correo)
    ctx.extras["con_sesion"] = correo


@given(parsers.re(r'ninguna carga publicada de (?P<asignatura>[0-9]+) en (?P<periodo>[0-9]{4}-[0-9])'))
def _ninguna_carga_publicada(ctx: Escenario, asignatura: str, periodo: str) -> None:
    assert ctx.uno("SELECT count(*) FROM abet.carga c JOIN abet.seccion s USING (seccion_id)"
                   " JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id"
                   " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
                   " WHERE a.codigo = %s AND pe.codigo = %s AND c.estado = 'PUBLICADA'", asignatura, periodo) == 0


@given("la 701 publicada con R-2026-BORRADOR de Industrial, que tiene parámetros PENDIENTE")
def _publicada_con_el_borrador(ctx: Escenario) -> None:
    pendientes = ctx.uno("SELECT count(*) FROM abet.parametro_valor pv JOIN abet.conjunto_reglas cr USING (conjunto_reglas_id)"
                         " JOIN abet.carrera c USING (carrera_id) WHERE cr.version = 'R-2026-BORRADOR' AND c.codigo = 'IND'"
                         " AND pv.estado = 'PENDIENTE'")
    assert pendientes > 0, "R-2026-BORRADOR de Industrial no tiene parámetros PENDIENTE"
    ctx.publicar_seccion_de_quimica("701", (1, 2, 4, 3), conjunto="R-2026-BORRADOR")


# Cuando

@when(parsers.re(rf'(?P<correo>{CORREO}) pide GET (?P<ruta>/api/\S+)'))
def _pide_con_sesion(ctx: Escenario, correo: str, ruta: str) -> None:
    _pedir(ctx, correo, ruta)


@when(parsers.re(rf'(?P<correo>{CORREO}) pide el resumen de (?P<asignatura>[0-9]+) en (?P<periodo>[0-9]{{4}}-[0-9])'))
def _pide_el_resumen(ctx: Escenario, correo: str, asignatura: str, periodo: str) -> None:
    _pedir(ctx, correo, _ruta_del_resumen(asignatura, periodo))


@when(parsers.re(r'pide GET (?P<ruta>/api/\S+?)(?: \(propuesta\))?'))
def _pide(ctx: Escenario, ruta: str) -> None:
    _pedir(ctx, ctx.extras.get("con_sesion"), ruta)


@when(parsers.re(r'alguien sin sesión pide GET (?P<ruta>/api/\S+)'))
def _pide_sin_sesion(ctx: Escenario, ruta: str) -> None:
    _pedir(ctx, None, ruta)


# Entonces, el código y el cuerpo

@then(parsers.re(r'la respuesta es (?P<codigo>[0-9]{3})'))
def _la_respuesta_es(ctx: Escenario, codigo: str) -> None:
    assert ctx.respuesta is not None and ctx.respuesta.status_code == int(codigo), ctx.respuesta.text
    assert ctx.respuesta.headers["cache-control"] == "no-store"


@then('la respuesta es 403 con el código "SOLO_COORDINACION"')
def _403_solo_coordinacion(ctx: Escenario) -> None:
    from app import permisos

    assert _cuerpo(ctx, 403) == {"detail": permisos.SOLO_COORDINACION} == {"detail": "Esta página es de la Coordinación."}


@then("la respuesta es 200 con indicadores vacío")
def _200_sin_indicadores(ctx: Escenario) -> None:
    cuerpo = _cuerpo(ctx)
    assert set(cuerpo) == CLAVES and cuerpo["indicadores"] == []


@then(parsers.re(r'con asignatura=(?P<valor>\S+) la respuesta también es 422'))
def _tambien_422(ctx: Escenario, valor: str) -> None:
    respuesta = ctx.sesion(ctx.extras["con_sesion"]).get(f"{RUTA}?periodo=2026-1&asignatura={valor}")
    assert respuesta.status_code == 422, respuesta.text
    assert respuesta.json() == {"detail": "La asignatura no tiene la forma de un código de 4 o 6 cifras."}
    # El periodo mal formado de la primera petición dice su propio mensaje, y la asignatura no lo tapa.
    assert ctx.respuesta.json() == {"detail": "El periodo no tiene la forma AAAA-C."}


@then(parsers.re(r'el PI (?P<pi>[0-9]+\.[0-9]+) trae en curso (?P<resto>.+)'))
def _el_pi_trae_en_curso(ctx: Escenario, pi: str, resto: str) -> None:
    _comprobar(_indicador(ctx, pi)["curso"], _pares(resto), f"el curso del PI {pi}")


@then(parsers.re(r'el PI (?P<pi>[0-9]+\.[0-9]+) trae (?P<resto>(?!en curso).+)'))
def _el_pi_trae(ctx: Escenario, pi: str, resto: str) -> None:
    _comprobar(_indicador(ctx, pi), _pares(resto), f"el PI {pi}")


@then(parsers.re(r'conteo_secciones trae (?P<resto>.+)'))
def _conteo_de_secciones(ctx: Escenario, resto: str) -> None:
    conteo = _indicador(ctx, "6.1")["conteo_secciones"]
    assert list(conteo) == CLAVES_DEL_CONTEO
    _comprobar(conteo, _pares(resto), "conteo_secciones")
    secciones = _indicador(ctx, "6.1")["secciones"]
    # El conteo es el de las secciones de la respuesta, no otro.
    assert conteo["total"] == len(secciones)
    assert conteo["publicadas"] == sum(1 for s in secciones if s["estado"] == "PUBLICADA")
    assert conteo["en_meta"] + conteo["debajo_de_la_meta"] + conteo["sin_dato"] == conteo["total"]


@then(parsers.re(r'secciones trae la 701, la 702, la 703 y la 704 en ese orden'))
def _secciones_en_orden(ctx: Escenario) -> None:
    secciones = _indicador(ctx, "6.1")["secciones"]
    assert [s["numero"] for s in secciones] == ["701", "702", "703", "704"]
    assert [s["seccion_id"] for s in secciones] == [ctx.seccion_de(n) for n in ("701", "702", "703", "704")]


@then(parsers.re(r'la (?P<numero>70[1-4]) trae (?P<resto>.+)'))
def _la_seccion_trae(ctx: Escenario, numero: str, resto: str) -> None:
    _comprobar(_seccion(ctx, numero), _pares(resto), f"la sección {numero}")


@then("pct_sobre_calificados de la 701 es igual a pct_logro_sobre_calificados de abet.v_r17_por_pi para su carga")
def _pct_igual_a_la_vista(ctx: Escenario) -> None:
    seccion = _seccion(ctx, "701")
    assert seccion["carga_id"] == ctx.extras["cargas"]["701"]
    vista = ctx.uno("SELECT pct_logro_sobre_calificados FROM abet.v_r17_por_pi WHERE carga_id = %s AND pi = '6.1'",
                    seccion["carga_id"])
    assert seccion["pct_sobre_calificados"] == float(vista) == 70.0
    assert _indicador(ctx, "6.1")["curso"]["pct_sobre_calificados"] == float(vista)


@then("es igual al porcentaje del bloque II del R-17 de esa carga")
def _pct_igual_al_r17(ctx: Escenario) -> None:
    carga = _seccion(ctx, "701")["carga_id"]
    with tempfile.TemporaryDirectory() as carpeta:
        # La base de la spec 009 no tiene la declaración de la spec 005, así que el R-17 sale como en el ensayo.
        ruta = r17.generar(ctx.api.dueno, carga, Path(carpeta), exigir_declaracion=False)
        hoja = load_workbook(ruta, data_only=True)[r17.HOJA]
    [fila] = [f for f in FILAS_DEL_BLOQUE_II if hoja[f"B{f}"].value == "6.1"]
    assert _seccion(ctx, "701")["pct_sobre_calificados"] == round(100 * hoja[f"E{fila}"].value, 1) == 70.0


@then(parsers.re(r'con la 701 publicada con los niveles \[(?P<niveles>[0-9]+(?:, [0-9]+){3})\] el curso trae '
                 r'(?P<pct>[0-9.]+) y en_meta (?P<en_meta>verdadero|falso)'))
def _con_otra_701_el_curso_trae(ctx: Escenario, niveles: str, pct: str, en_meta: str) -> None:
    anterior = ctx.extras["cargas"]["701"]
    assert ctx.extras["ruta"].startswith(RUTA)
    ctx.publicar_seccion_de_quimica("701", tuple(int(n) for n in niveles.split(", ")), reemplaza=anterior)
    assert ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", anterior) == "REEMPLAZADA"
    _pedir(ctx, ctx.extras.get("con_sesion"), ctx.extras["ruta"])
    curso = _indicador(ctx, "6.1")["curso"]
    assert (curso["pct_sobre_calificados"], curso["en_meta"]) == (float(pct), en_meta == "verdadero")


@then("la respuesta trae solo las claves de la lista cerrada de la ruta 20 del contrato")
def _lista_cerrada(ctx: Escenario) -> None:
    cuerpo = _cuerpo(ctx)
    assert set(cuerpo) == CLAVES
    assert set(cuerpo["asignatura"]) == {"codigo", "nombre"}
    assert [list(i) for i in cuerpo["indicadores"]] == [CLAVES_DE_UN_INDICADOR]
    [indicador] = cuerpo["indicadores"]
    assert list(indicador["curso"]) == CLAVES_DEL_CURSO
    assert list(indicador["conteo_secciones"]) == CLAVES_DEL_CONTEO
    assert [list(s) for s in indicador["secciones"]] == [CLAVES_DE_UNA_SECCION] * 4
    ejemplo = _contrato_del_front()
    if ejemplo is None:
        ctx.request.node.user_properties.append(("criterio_relajado", "sin ABET_FRONT_RAIZ no se compara con el contrato"))
    else:
        assert _forma(cuerpo) == _forma(ejemplo), "las claves de la ruta 20 no son las de la sección 16.2 del contrato"


@then("no trae correos, nombres, códigos de estudiantes, subida_por, nombre_archivo ni sha256")
def _sin_datos_de_personas(ctx: Escenario) -> None:
    texto = ctx.respuesta.text
    assert ctx.cuenta("medicion") > 0, "la base no tiene mediciones, así que la prueba no revisaría nada"
    assert not OCHO_CIFRAS.search(texto), "la respuesta trae un número de ocho cifras"
    for prohibido in ("@", "example.invalid", "subida_por", "nombre_archivo", "sha256", "profesor", "docente", "correo"):
        assert prohibido not in texto, f"la respuesta trae «{prohibido}»"
    # Los 8 códigos de los alumnos de la 701 no salen en ninguna parte.
    codigos = [fila[0] for fila in ctx.filas("SELECT codigo FROM abet.estudiante")]
    assert codigos and not any(codigo in texto for codigo in codigos)


@then("la respuesta no dice si 5643 tiene secciones en 2026-1")
def _no_revela_si_el_curso_existe(ctx: Escenario) -> None:
    cuerpo = _cuerpo(ctx)
    # La misma petición por un curso que no existe da la misma respuesta, salvo el código que se pidió.
    otra = ctx.sesion(ctx.extras["con_sesion"]).get(_ruta_del_resumen("999999", "2026-1"))
    assert otra.status_code == 200, otra.text
    assert {**otra.json(), "asignatura": cuerpo["asignatura"]} == cuerpo
    assert cuerpo["asignatura"] == {"codigo": "5643", "nombre": None}
    assert otra.json()["asignatura"] == {"codigo": "999999", "nombre": None}
    # Y 5643 sí tiene sus cuatro secciones en 2026-1, que la coordinación de Química sí recibe.
    assert ctx.uno("SELECT count(*) FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                   " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id WHERE a.codigo = '5643'"
                   " AND pe.codigo = '2026-1'") == 4


# Entonces, la ruta 21

def _cursos(ctx: Escenario) -> list[dict[str, str]]:
    cuerpo = _cuerpo(ctx)
    assert list(cuerpo) == ["periodo", "cursos"]
    assert all(list(curso) == ["codigo", "nombre"] for curso in cuerpo["cursos"])
    return cuerpo["cursos"]


@then("la respuesta trae 450002 y 450010 en orden de código, con su nombre")
def _trae_450002_y_450010(ctx: Escenario) -> None:
    cursos = _cursos(ctx)
    assert [curso["codigo"] for curso in cursos] == ["450002", "450010"]
    for curso in cursos:
        assert curso["nombre"] and curso["nombre"] == ctx.uno("SELECT nombre FROM abet.asignatura WHERE codigo = %s",
                                                              curso["codigo"])
    assert _cuerpo(ctx)["periodo"] == "2026-2"


@then("no trae cursos de otra carrera")
def _sin_cursos_de_otra_carrera(ctx: Escenario) -> None:
    codigos = [curso["codigo"] for curso in _cursos(ctx)]
    # 5643 es de Industrial, y 450020 de Ambiental no tiene plan en 2026-2, y ninguno de los dos sale.
    assert ctx.uno("SELECT count(*) FROM abet.plan_medicion pm JOIN abet.asignatura a USING (asignatura_id)"
                   " WHERE a.codigo = '5643'") > 0
    assert "5643" not in codigos and "450020" not in codigos
    # La misma coordinación no ve el curso de Industrial ni en 2026-1, donde sí tiene plan y sus cuatro secciones.
    otro = ctx.sesion(ctx.extras["con_sesion"]).get(f"{RUTA}/cursos?periodo=2026-1")
    assert otro.status_code == 200 and otro.json() == {"periodo": "2026-1", "cursos": []}


@then("la respuesta trae solo 5643")
def _trae_solo_5643(ctx: Escenario) -> None:
    cursos = _cursos(ctx)
    assert [curso["codigo"] for curso in cursos] == ["5643"]
    assert cursos[0]["nombre"] == ctx.uno("SELECT nombre FROM abet.asignatura WHERE codigo = '5643'")
    assert _cuerpo(ctx)["periodo"] == "2026-1"
