"""Pasos de US-45 en semaforo.feature (spec 005, BR-MEJORA-01 a BR-MEJORA-05), ejecutables con pytest-bdd en español.

El .feature manda. Ningún paso cambia un texto para que el escenario pase, y cada «Entonces» se comprueba contra la
respuesta de la ruta 13, GET /api/cargas/{carga_id}/indicadores, sin dobles del sistema bajo prueba. Este módulo enlaza
con @scenario los once escenarios del Back. «Las cifras y el semáforo coinciden con el R-17 de la misma carga» entra
en la segunda etapa de J-41 (T037), con V1_15, US-49 y el paso compartido «con su análisis declarado» de conftest.py,
que llama a declarar() de tests/cargas_de_prueba.py. Los seis de US-46 llevan @delegado_a_vitest y los prueba Vitest
en el Front.

«El dueño de la base» usa la conexión del dueño de la copia desechable, la misma de las consultas de los pasos, y nunca
toca Neon. Las subidas van por la API, así que los carga_id salen de sus respuestas y nunca se suponen.
"""

from __future__ import annotations

import io
import re
from dataclasses import replace
from typing import Any

from openpyxl import load_workbook
from pytest_bdd import given, parsers, scenario, then, when

from abet_carga import r17

Escenario = Any
FEATURE = "specs/005-oportunidades-de-mejora/aceptacion/semaforo.feature"
PIS = ("5.1", "5.2", "5.3")
ASIGNADAS = {("docente410@example.invalid", "410"), ("docente411@example.invalid", "411"),
             ("docente.varias@example.invalid", "412")}
VALORES = {"verdadero": True, "falso": False, "nulo": None, "null": None}


@scenario(FEATURE, "La 410 publicada con el conjunto borrador queda en rojo y pide tres oportunidades de mejora")
def test_la_410_con_el_borrador_queda_en_rojo() -> None:
    """US-45, la 410 con tres OM."""


@scenario(FEATURE, "La 412 de 450002 muestra verde, rojo y verde, con dos buenas prácticas")
def test_la_412_muestra_verde_rojo_y_verde() -> None:
    """US-45, la 412 con dos BP, con sus tres Ejemplos."""


@scenario(FEATURE, "El 80,0 % justo en la meta queda en verde y pide una buena práctica")
def test_el_80_justo_queda_en_verde() -> None:
    """US-45, la frontera de la meta."""


@scenario(FEATURE, "Con el corte rojo definido, la banda ámbar va desde el corte hasta debajo de la meta y pide una "
                   "oportunidad de mejora")
def test_con_corte_rojo_definido_hay_ambar() -> None:
    """US-45, la banda ámbar con R-PRUEBA-SEMAFORO, con sus tres Ejemplos."""


@scenario(FEATURE, "Con el corte rojo pendiente no hay ámbar")
def test_con_corte_rojo_pendiente_no_hay_ambar() -> None:
    """US-45, CORTE_ROJO PENDIENTE en R-2026-BORRADOR."""


@scenario(FEATURE, "Un PI sin calificaciones sale sin dato, nunca en rojo y sin tipo de registro")
def test_un_pi_sin_calificaciones_sale_sin_dato() -> None:
    """US-45, D-40."""


@scenario(FEATURE, "Un parámetro sin definir deja los indicadores sin dato y no rompe la ruta")
def test_un_parametro_sin_definir_no_rompe_la_ruta() -> None:
    """US-45, NIVEL_ESPERADO y META_LOGRO sin DEFINIR."""


@scenario(FEATURE, "Sin sesión la ruta responde 401")
def test_sin_sesion_la_ruta_responde_401() -> None:
    """US-45, BR-ACCESO-10."""


@scenario(FEATURE, "El profesor solo ve el semáforo de sus secciones")
def test_el_profesor_solo_ve_sus_secciones() -> None:
    """US-45, BR-ACCESO-08, con sus tres Ejemplos."""


@scenario(FEATURE, "Una carga que no está publicada no tiene semáforo")
def test_una_carga_no_publicada_no_tiene_semaforo() -> None:
    """US-45, BR-MEJORA-05, con sus dos Ejemplos."""


@scenario(FEATURE, "Las cifras y el semáforo coinciden con el R-17 de la misma carga")
def test_las_cifras_y_el_semaforo_coinciden_con_el_r17() -> None:
    """US-45, con las tres cargas declaradas de US-49 (T037)."""


# Ayudas

def _cuerpo(ctx: Escenario) -> dict[str, Any]:
    assert ctx.respuesta is not None and ctx.respuesta.status_code == 200, ctx.respuesta.text
    return ctx.respuesta.json()


def _indicador(ctx: Escenario, pi: str) -> dict[str, Any]:
    [indicador] = [i for i in _cuerpo(ctx)["indicadores"] if i["pi"] == pi]
    ctx.extras["indicador"] = indicador
    return indicador


def _valor(texto: str) -> Any:
    """Valor de una frase: una lista [1, 3, 4, 3], un texto entre comillas, nulo, verdadero, falso o un número."""
    if texto.startswith("["):
        return [int(n) for n in re.findall(r"-?[0-9]+", texto)]
    if texto.startswith('"'):
        return texto.strip('"')
    if texto in VALORES:
        return VALORES[texto]
    return float(texto) if "." in texto else int(texto)


def _comprobar(indicador: dict[str, Any], texto: str) -> None:
    """Cada «clave valor» de la frase contra el indicador, y el hallazgo entre comillas angulares si la frase lo trae."""
    if (hallazgo := re.search(r"el hallazgo «([^»]+)»", texto)) is not None:
        assert indicador["hallazgo"] == hallazgo[1], indicador["hallazgo"]
        texto = texto[:hallazgo.start()]
    pares = re.findall(r'([a-z_]+) (\[[^\]]*\]|"[^"]*"|nulo|verdadero|falso|-?[0-9]+(?:\.[0-9]+)?)', texto)
    assert pares, f"la frase {texto!r} no trae ningún campo"
    for clave, valor in pares:
        assert indicador[clave] == _valor(valor), (indicador["pi"], clave, indicador[clave])


# Antecedentes propios de este archivo

@given('acceso.docente_seccion asigna la sección 410 de "450002" a "docente410@example.invalid", la 411 de "450002" a '
       '"docente411@example.invalid" y la 412 de "450002" a "docente.varias@example.invalid"')
def _asignaciones(ctx: Escenario) -> None:
    filas = set(ctx.filas("SELECT u.correo, s.numero FROM acceso.docente_seccion d"
                          " JOIN acceso.usuario_autorizado u USING (usuario_id) JOIN abet.seccion s USING (seccion_id)"
                          " JOIN abet.asignatura a USING (asignatura_id) WHERE a.codigo = '450002'"))
    assert ASIGNADAS <= filas, filas
    for _, numero in ASIGNADAS:
        assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion WHERE seccion_id = %s",
                       ctx.seccion_id(numero)) == 1, numero


@given("ninguna sección de 2026-2 tiene cargas")
def _sin_cargas(ctx: Escenario) -> None:
    assert ctx.uno("SELECT count(*) FROM abet.carga c JOIN abet.seccion s USING (seccion_id)"
                   " JOIN abet.periodo p USING (periodo_id) WHERE p.codigo = '2026-2'") == 0


# Dado, los conjuntos de reglas de prueba y las cargas que no están publicadas

def _usar_conjunto(ctx: Escenario, version: str) -> None:
    ctx.reiniciar_api(carga=replace(ctx.api.ajustes.carga, conjunto_reglas=version))
    assert ctx.api.ajustes.carga.conjunto_reglas == version


@given(parsers.re(r'que la base tiene el conjunto "(?P<version>[^"]+)" de Ambiental en estado "APROBADO" con META_LOGRO '
                  r'(?P<meta>0,[0-9]+), NIVEL_ESPERADO (?P<nivel>[1-4]) y CORTE_ROJO (?P<corte>0,[0-9]+), y la API '
                  r'configurada con ese CONJUNTO_REGLAS'))
def _conjunto_con_corte(ctx: Escenario, version: str, meta: str, nivel: str, corte: str) -> None:
    _cargas(ctx).conjunto_aprobado(ctx.api.dueno, version, meta_logro=float(meta.replace(",", ".")),
                                   nivel_esperado=int(nivel), corte_rojo=float(corte.replace(",", ".")))
    _usar_conjunto(ctx, version)


@given(parsers.re(r'que la base tiene un conjunto de reglas de prueba de Ambiental con (?P<parametro>NIVEL_ESPERADO|'
                  r'META_LOGRO) sin DEFINIR, y la API configurada con ese CONJUNTO_REGLAS'))
def _conjunto_sin_un_parametro(ctx: Escenario, parametro: str) -> None:
    version = f"R-PRUEBA-SIN-{parametro.replace('_', '-')}"
    valores = {"meta_logro": 0.80, "nivel_esperado": 3, "corte_rojo": 0.75, parametro.lower(): None}
    _cargas(ctx).conjunto_aprobado(ctx.api.dueno, version, **valores)
    assert ctx.uno("SELECT pv.estado FROM abet.parametro_valor pv JOIN abet.conjunto_reglas cr USING (conjunto_reglas_id)"
                   " WHERE cr.version = %s AND pv.clave = %s", version, parametro) == "PENDIENTE"
    _usar_conjunto(ctx, version)


def _cargas(ctx: Escenario) -> Any:
    """tests/cargas_de_prueba.py, el mismo módulo que carga el conftest del arnés."""
    import sys

    return sys.modules["cargas_de_prueba"]


@given(parsers.re(r'que la carga A REEMPLAZADA de "(?P<a>[^"]+)" y la carga B PUBLICADA de "(?P<b>[^"]+)" que la '
                  r'reemplaza en la sección (?P<numero>[0-9]+), y se pide la de A'))
def _a_reemplazada_por_b(ctx: Escenario, a: str, b: str, numero: str) -> None:
    primera = ctx.subir(ctx.profesor, ctx.de_inventados(a), a, numero)
    assert primera.status_code == 201 and primera.json()["estado"] == "PUBLICADA", primera.text
    anterior = primera.json()["carga_id"]
    segunda = ctx.subir(ctx.profesor, ctx.de_inventados(b), b, numero, params={"reemplaza": str(anterior)})
    assert segunda.status_code == 201 and segunda.json()["estado"] == "PUBLICADA", segunda.text
    assert ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", anterior) == "REEMPLAZADA"
    ctx.extras["cargas"] = {"A": anterior, "B": segunda.json()["carga_id"]}
    ctx.carga_id = anterior


@given('una petición sin la cookie "abet_sesion"')
def _sin_cookie(ctx: Escenario) -> None:
    ctx.extras["con_sesion"] = None


# Cuando

@when(parsers.re(r'se envía GET /api/cargas/(?P<carga>\{carga_id\}|\{carga_id de la 410\}|[0-9]+)/indicadores'))
def _pide_indicadores(ctx: Escenario, carga: str) -> None:
    if carga.startswith("{"):
        assert ctx.carga_id is not None, "el escenario no tiene carga_id"
        carga = str(ctx.carga_id)
    ctx.pedir(f"/api/cargas/{carga}/indicadores")


# Entonces

@then(parsers.re(r'la API responde 200 con (?:meta_pct (?P<meta>[0-9.]+) y )?corte_rojo_pct (?P<corte>nulo|[0-9.]+)'))
def _meta_y_corte(ctx: Escenario, meta: str | None, corte: str) -> None:
    cuerpo = _cuerpo(ctx)
    assert ctx.respuesta.headers["cache-control"] == "no-store"
    assert cuerpo["estado"] == "PUBLICADA" and cuerpo["carga_id"] == ctx.carga_id
    if meta is not None:
        assert cuerpo["meta_pct"] == float(meta)
    assert cuerpo["corte_rojo_pct"] == _valor(corte)


@then(parsers.re(r'los tres PI 5\.1, 5\.2 y 5\.3 traen estudiantes_por_nivel (?P<a>\[[^\]]+\]), (?P<b>\[[^\]]+\]) y '
                 r'(?P<c>\[[^\]]+\]), logrados (?P<l1>[0-9]+), (?P<l2>[0-9]+) y (?P<l3>[0-9]+), calificados '
                 r'(?P<calificados>[0-9]+) y pct_sobre_total (?P<p1>[0-9.]+), (?P<p2>[0-9.]+) y (?P<p3>[0-9.]+)'))
def _tres_pi(ctx: Escenario, a: str, b: str, c: str, l1: str, l2: str, l3: str, calificados: str,
             p1: str, p2: str, p3: str) -> None:
    indicadores = _cuerpo(ctx)["indicadores"]
    assert [i["pi"] for i in indicadores] == list(PIS)
    assert [i["estudiantes_por_nivel"] for i in indicadores] == [_valor(a), _valor(b), _valor(c)]
    assert [i["logrados"] for i in indicadores] == [int(l1), int(l2), int(l3)]
    assert {i["calificados"] for i in indicadores} == {int(calificados)}
    assert [i["pct_sobre_total"] for i in indicadores] == [float(p1), float(p2), float(p3)]


@then(parsers.re(r'el semáforo de los tres PI es "(?P<semaforo>[A-Z_]+)" y su tipo_registro es "(?P<tipo>[A-Z_]+)"'))
def _semaforo_de_los_tres(ctx: Escenario, semaforo: str, tipo: str) -> None:
    assert [(i["semaforo"], i["tipo_registro"]) for i in _cuerpo(ctx)["indicadores"]] == [(semaforo, tipo)] * 3


@then(parsers.re(r'el hallazgo de (?P<pi>[0-9]\.[0-9]+) es «(?P<hallazgo>[^»]+)» \(propuesta\)'))
def _hallazgo_de(ctx: Escenario, pi: str, hallazgo: str) -> None:
    assert _indicador(ctx, pi)["hallazgo"] == hallazgo


@then(parsers.re(r'el indicador (?P<pi>[0-9]\.[0-9]+) trae (?P<campos>.+?)(?: \(propuesta\))?'))
def _indicador_trae(ctx: Escenario, pi: str, campos: str) -> None:
    _comprobar(_indicador(ctx, pi), campos)


@then(parsers.re(r'su (?P<resto>(?:semáforo|en_meta|tipo_registro|hallazgo) .+?)(?: \(propuesta\))?'))
def _su(ctx: Escenario, resto: str) -> None:
    indicador = ctx.extras["indicador"]
    if (hallazgo := re.fullmatch(r"hallazgo es «([^»]+)»", resto)) is not None:
        assert indicador["hallazgo"] == hallazgo[1], indicador["hallazgo"]
        return
    pares = re.findall(r'(semáforo|en_meta|tipo_registro) es ("[^"]*"|verdadero|falso|nulo)', resto)
    assert pares, resto
    for clave, valor in pares:
        assert indicador["semaforo" if clave == "semáforo" else clave] == _valor(valor), (clave, indicador)
    for distinto in re.findall(r' y no "([^"]+)"', resto):
        assert indicador["semaforo"] != distinto


@then(parsers.re(r'los indicadores (?P<pis>[0-9]\.[0-9]+ y [0-9]\.[0-9]+) traen (?P<campos>.+)'))
def _indicadores_traen(ctx: Escenario, pis: str, campos: str) -> None:
    for pi in re.findall(r"[0-9]\.[0-9]+", pis):
        _comprobar(_indicador(ctx, pi), campos)


@then("la API responde 200 y no 500")
def _sin_500(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    assert len(_cuerpo(ctx)["indicadores"]) == 3


@then(parsers.re(r'cada indicador trae (?P<campos>.+)'))
def _cada_indicador(ctx: Escenario, campos: str) -> None:
    indicadores = _cuerpo(ctx)["indicadores"]
    assert indicadores
    for indicador in indicadores:
        _comprobar(indicador, campos)


@then(parsers.re(r'la API responde (?P<codigo>40[139])(?: con el mensaje "(?P<mensaje>[^"]+)"(?: \(propuesta\))?)?'))
def _error(ctx: Escenario, codigo: str, mensaje: str | None) -> None:
    respuesta = ctx.respuesta
    assert respuesta.status_code == int(codigo), respuesta.text
    assert respuesta.headers["cache-control"] == "no-store"
    assert set(respuesta.json()) == {"detail"}
    if mensaje is not None:
        assert respuesta.json()["detail"] == mensaje


@then("la API responde 200 con los tres PI de la 410")
def _tres_pi_de_la_410(ctx: Escenario) -> None:
    cuerpo = _cuerpo(ctx)
    assert cuerpo["carga_id"] == ctx.carga_id
    assert [(i["pi"], i["pct_sobre_calificados"], i["semaforo"]) for i in cuerpo["indicadores"]] == [
        ("5.1", 63.6, "ROJO"), ("5.2", 63.6, "ROJO"), ("5.3", 72.7, "ROJO")]


# Cuando y Entonces, las cifras contra el R-17 de la misma carga

def _fila(hoja: Any, filas: tuple[int, ...], columna: str, pi: str) -> int:
    [fila] = [fila for fila in filas if hoja[f"{columna}{fila}"].value == pi]
    return fila


def _con_su_r17(ctx: Escenario) -> list[tuple[str, dict[str, Any], Any]]:
    """(carga, indicador, hoja) de cada indicador de las tres cargas."""
    return [(carga, indicador, hoja) for carga, (indicadores, hoja) in ctx.extras["con_r17"].items()
            for indicador in indicadores]


@when("se envía GET /api/cargas/{carga_id}/indicadores y se descarga el R-17 de cada una de las tres cargas")
def _indicadores_y_r17(ctx: Escenario) -> None:
    cliente = ctx.sesion(ctx.extras["con_sesion"])
    cargas = ctx.extras["declaradas"]
    assert len(cargas) == 3, cargas
    leidas = {}
    for carga_id in cargas:
        indicadores = cliente.get(f"/api/cargas/{carga_id}/indicadores")
        descarga = cliente.get(f"/api/cargas/{carga_id}/r17.xlsx")
        assert indicadores.status_code == 200 and descarga.status_code == 200, (indicadores.text, descarga.text)
        leidas[carga_id] = (indicadores.json()["indicadores"],
                            load_workbook(io.BytesIO(descarga.content), data_only=True)[r17.HOJA])
    ctx.extras["con_r17"] = leidas


@then("en cada indicador el logro es igual a round(100 × la celda E de su fila del bloque II, 1) y la meta a "
      "round(100 × la celda G de esa fila, 1)")
def _logro_y_meta(ctx: Escenario) -> None:
    revisados = 0
    for _, indicador, hoja in _con_su_r17(ctx):
        fila = _fila(hoja, r17.FILAS_DEL_BLOQUE_II, "B", indicador["pi"])
        logro, meta = hoja[f"E{fila}"].value, hoja[f"G{fila}"].value
        assert indicador["pct_sobre_calificados"] == (round(100 * logro, 1) if logro is not None else None)
        assert indicador["meta_pct"] == round(100 * meta, 1)
        revisados += 1
    assert revisados == 9


@then("los conteos por nivel son los de las celdas L a O de K29:Q31, «7 de 11» es el de la celda P y pct_sobre_total "
      "es round(100 × la celda Q, 1)")
def _conteos(ctx: Escenario) -> None:
    for _, indicador, hoja in _con_su_r17(ctx):
        fila = _fila(hoja, r17.FILAS_DE_FRECUENCIAS, "K", indicador["pi"])
        assert indicador["estudiantes_por_nivel"] == [hoja[f"{columna}{fila}"].value for columna in "LMNO"]
        logran = f"{indicador['logrados']} de {indicador['calificados']}" if indicador["logrados"] is not None else None
        assert hoja[f"P{fila}"].value == logran
        total = hoja[f"Q{fila}"].value
        assert indicador["pct_sobre_total"] == (round(100 * total, 1) if total is not None else None)


def _celda_h(hoja: Any, pi: str) -> Any:
    return hoja[f"H{_fila(hoja, r17.FILAS_DEL_BLOQUE_II, 'B', pi)}"].value


@then(parsers.re(r'el semáforo "VERDE" va con el texto «¡Felicidades! …» de la celda H de su fila'))
def _verde(ctx: Escenario) -> None:
    verdes = [(i, hoja) for _, i, hoja in _con_su_r17(ctx) if i["semaforo"] == "VERDE"]
    assert verdes and all(_celda_h(hoja, i["pi"]) == r17.LOGRADO for i, hoja in verdes)


@then(parsers.re(r'el semáforo "ROJO" o "AMBAR" va con el texto «El indicador aún no alcanza …» de la celda H de su fila'))
def _rojo_o_ambar(ctx: Escenario) -> None:
    abajo = [(i, hoja) for _, i, hoja in _con_su_r17(ctx) if i["semaforo"] in ("ROJO", "AMBAR")]
    assert abajo and all(_celda_h(hoja, i["pi"]) == r17.NO_LOGRADO for i, hoja in abajo)


@then(parsers.re(r'el indicador "SIN_DATO" de la copia sin notas en 5\.3 va con la celda H vacía'))
def _sin_dato(ctx: Escenario) -> None:
    sin_dato = [(i, hoja) for _, i, hoja in _con_su_r17(ctx) if i["semaforo"] == "SIN_DATO"]
    assert [i["pi"] for i, _ in sin_dato] == ["5.3"]
    assert all(_celda_h(hoja, i["pi"]) is None for i, hoja in sin_dato)
