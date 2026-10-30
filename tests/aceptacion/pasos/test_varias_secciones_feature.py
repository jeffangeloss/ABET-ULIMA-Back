"""Pasos de varias_secciones.feature (US-06, US-07, US-09 y US-13), ejecutables con pytest-bdd en español (T050).

El .feature manda. Ningún paso cambia una cifra, un mensaje ni un título para que el escenario pase,
y cada «Entonces» se comprueba contra la base, la respuesta de la API o el archivo, sin dobles del
sistema bajo prueba. Los Antecedentes que repiten otros .feature (la base, la API, las consultas de
control, los conteos antes y después) viven en el conftest.py de esta carpeta.

Una sección se nombra siempre con su número y su asignatura, porque la 412 existe en 450002 y en
450010. Los pasos que sirven a cada sección usan ctx.seccion_id(numero, asignatura).

La pantalla P2 «Mis secciones» y la P3 pertenecen al Front, y sus pruebas de Vitest (T045, en
tests/pantallas/MisSecciones.test.tsx del Front) comprueban lo que dibujan. Aquí se comprueba lo que la
API entrega a esas pantallas, que es la fila de cada sección con su asignatura, su número, sus PI, su
estado y el seccion_id al que la pantalla P3 sube el archivo.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

Escenario = Any
scenarios("specs/001-mvp-carga-r17/aceptacion/varias_secciones.feature")

PERIODO = "2026-2"
VARIAS = "docente.varias@example.invalid"
DOCENTE_410 = "docente410@example.invalid"
DOCENTE_411 = "docente411@example.invalid"
COORDINACION = "coordinacion@example.invalid"
CONTROLADAS = (("450002", "410"), ("450002", "411"))


def _conftest(ctx: Escenario) -> Any:
    """Módulo conftest.py de esta carpeta, que pytest registra como plugin, para reutilizar sus ayudas."""
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        ruta = getattr(plugin, "__file__", "") or ""
        if ruta.endswith("aceptacion/pasos/conftest.py"):
            return plugin
    raise AssertionError("no se encontró el conftest.py del arnés de aceptación")


def _pis(texto: str) -> list[str]:
    return re.findall(r"[0-9]\.[0-9]", texto)


def _secciones_visibles(ctx: Escenario) -> list[dict[str, Any]]:
    """Cuerpo de la última respuesta, que es la lista de GET /api/secciones."""
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    return ctx.respuesta.json()


def _fila_de(lista: list[dict[str, Any]], numero: str, asignatura: str) -> dict[str, Any]:
    filas = [s for s in lista if s["numero"] == numero and s["asignatura"]["codigo"] == asignatura]
    assert len(filas) == 1, f"la lista trae {len(filas)} filas de la sección {numero} de {asignatura}"
    return filas[0]


# Antecedentes propios

@given(parsers.re(r'abet\.seccion registra en "(?P<periodo>[^"]+)" la sección 412 de "450002" y las secciones 410 y 412 de '
                  r'"450010" con curso_blackboard "(?P<a>[^"]+)", "(?P<b>[^"]+)" y "(?P<c>[^"]+)"'))
def _secciones_registradas(ctx: Escenario, periodo: str, a: str, b: str, c: str) -> None:
    filas = ctx.filas(
        "SELECT a.codigo, s.numero, s.curso_blackboard FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
        " JOIN abet.periodo p USING (periodo_id) WHERE p.codigo = %s AND (a.codigo, s.numero) IN"
        " (('450002', '412'), ('450010', '410'), ('450010', '412')) ORDER BY a.codigo, s.numero", periodo)
    assert filas == [("450002", "412", a), ("450010", "410", b), ("450010", "412", c)]


@given(parsers.re(r'plan_medicion registra los PI (?P<primeros>[0-9.]+(?:, [0-9.]+)* y [0-9.]+) para la asignatura '
                  r'"(?P<uno>[0-9]+)" en "(?P<periodo>[^"]+)" y los PI (?P<segundos>[0-9.]+(?:, [0-9.]+)* y [0-9.]+) '
                  r'para "(?P<otro>[0-9]+)", con el instrumento "(?P<instrumento>[^"]+)" que asignatura_so le asigna '
                  r'en los SO (?P<sos>[0-9]+ y [0-9]+)'))
def _plan_de_dos_asignaturas(ctx: Escenario, primeros: str, uno: str, periodo: str, segundos: str, otro: str,
                             instrumento: str, sos: str) -> None:
    consulta = ("SELECT p.codigo, i.nombre, p.so_numero FROM abet.plan_medicion pm JOIN abet.pi p USING (pi_id)"
                " JOIN abet.asignatura a USING (asignatura_id) JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id"
                " LEFT JOIN abet.instrumento i ON i.instrumento_id = pm.instrumento_id"
                " WHERE a.codigo = %s AND pe.codigo = %s ORDER BY p.codigo")
    primero = ctx.filas(consulta, uno, periodo)
    segundo = ctx.filas(consulta, otro, periodo)
    assert [fila[0] for fila in primero] == sorted(_pis(primeros))
    assert [fila[0] for fila in segundo] == sorted(_pis(segundos))
    # asignatura_so asigna a 450010 el instrumento solo en los SO que el plan mide, el 2 y el 5.
    esperados = sorted(int(n) for n in re.findall(r"[0-9]+", sos))
    asignados = ctx.filas(
        "SELECT so.numero, i.nombre FROM abet.asignatura_so aso JOIN abet.asignatura a USING (asignatura_id)"
        " JOIN abet.so so USING (so_id) JOIN abet.instrumento i ON i.instrumento_id = aso.instrumento_id"
        " WHERE a.codigo = %s AND so.numero = ANY(%s) ORDER BY so.numero", otro, esperados)
    assert asignados == [(n, instrumento) for n in esperados]
    assert {fila[1] for fila in segundo} == {instrumento}
    assert sorted({fila[2] for fila in segundo}) == esperados


@given(parsers.re(r'"(?P<correo>[^"]+)" figura activo con rol "(?P<rol>[A-Z]+)" y acceso\.docente_seccion le asigna la '
                  r'sección 412 de "450002" y las secciones 410 y 412 de "450010" en "(?P<periodo>[^"]+)", y ninguna otra'))
def _profesor_con_tres_secciones(ctx: Escenario, correo: str, rol: str, periodo: str) -> None:
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, True)]
    asignadas = ctx.filas(
        "SELECT a.codigo, s.numero, p.codigo FROM acceso.docente_seccion d JOIN abet.seccion s USING (seccion_id)"
        " JOIN abet.asignatura a USING (asignatura_id) JOIN abet.periodo p USING (periodo_id)"
        " WHERE d.usuario_id = %s ORDER BY a.codigo, s.numero", ctx.usuario_id(correo))
    assert asignadas == [("450002", "412", periodo), ("450010", "410", periodo), ("450010", "412", periodo)]


@given(parsers.re(r'acceso\.docente_seccion asigna la sección 410 de "450002" solo a "(?P<d410>[^"]+)" y la 411 solo a '
                  r'"(?P<d411>[^"]+)", y no tiene filas de "(?P<coordinacion>[^"]+)"'))
def _secciones_de_los_otros(ctx: Escenario, d410: str, d411: str, coordinacion: str) -> None:
    for numero, correo in (("410", d410), ("411", d411)):
        dueños = ctx.filas("SELECT u.correo FROM acceso.docente_seccion d JOIN acceso.usuario_autorizado u"
                           " USING (usuario_id) WHERE d.seccion_id = %s", ctx.seccion_id(numero, "450002"))
        assert dueños == [(correo,)], (numero, dueños)
    assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion WHERE usuario_id = %s",
                   ctx.usuario_id(coordinacion)) == 0


@given(parsers.re(r'"(?P<correo>[^"]+)" tiene la sesión iniciada'))
def _sesion_del_profesor(ctx: Escenario, correo: str) -> None:
    ctx.sesion(correo)
    ctx.profesor = correo


@given(parsers.re(r'ninguna de las cinco secciones de 2026-2 tiene cargas'))
def _sin_cargas(ctx: Escenario) -> None:
    assert ctx.uno("SELECT count(*) FROM abet.seccion s JOIN abet.periodo p USING (periodo_id) WHERE p.codigo = %s",
                   PERIODO) == 5
    assert ctx.cuenta("carga") == 0


# Dado, cargas previas

@given(parsers.re(r'que "(?P<export>[^"]+)" está subido a la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" con '
                  r'respuesta 201 y su carga_id'))
def _subido_a_una_seccion(ctx: Escenario, export: str, numero: str, asignatura: str) -> None:
    respuesta = ctx.subir(ctx.profesor, ctx.de_inventados(export), export, numero, asignatura)
    assert respuesta.status_code == 201, respuesta.text
    assert ctx.carga_id is not None
    ctx.carga_previa = ctx.carga_id
    ctx.antes = ctx.api.conteos()


@given(parsers.re(r'que la sección 410 de "450002" tiene una carga PUBLICADA de "(?P<export>[^"]+)", subida por '
                  r'"(?P<correo>[^"]+)", con los códigos (?P<desde>[0-9]+) a (?P<hasta>[0-9]+)'))
def _carga_ajena_publicada(ctx: Escenario, export: str, correo: str, desde: str, hasta: str) -> None:
    respuesta = ctx.subir(correo, ctx.de_inventados(export), export, "410", "450002")
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "PUBLICADA", respuesta.text
    ctx.carga_previa = ctx.carga_id
    assert ctx.uno("SELECT u.correo FROM abet.carga c JOIN acceso.usuario_autorizado u ON u.usuario_id = c.subida_por"
                   " WHERE c.carga_id = %s", ctx.carga_id) == correo
    codigos = {c for (c,) in ctx.filas("SELECT codigo FROM abet.estudiante")}
    assert codigos == {str(n) for n in range(int(desde), int(hasta) + 1)}
    ctx.antes = ctx.api.conteos()


# Cuando

@when(parsers.re(r'se envía GET (?P<ruta>/api/secciones\?periodo=2026-2)'))
def _lista_las_secciones(ctx: Escenario, ruta: str) -> None:
    ctx.antes = ctx.api.conteos()
    ctx.respuesta = ctx.sesion(ctx.profesor).get(ruta)


@when(parsers.re(r'el profesor sube "(?P<export>[^"]+)" a la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)"'))
def _profesor_sube(ctx: Escenario, export: str, numero: str, asignatura: str) -> None:
    ctx.subir(ctx.profesor, ctx.de_inventados(export), export, numero, asignatura)


@when(parsers.re(r'el profesor sube otra vez "(?P<export>[^"]+)", ahora a la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)"'))
def _profesor_sube_otra_vez(ctx: Escenario, export: str, numero: str, asignatura: str) -> None:
    ctx.subir(ctx.profesor, ctx.de_inventados(export), export, numero, asignatura)


def _ruta_de(ctx: Escenario, plantilla: str) -> str:
    """Ruta con las llaves de los .feature resueltas contra la base, como {sección 410 de 450002} y {carga de la 410 de 450002}."""
    def resolver(m: re.Match[str]) -> str:
        texto = m[1]
        if seccion := re.fullmatch(r"sección ([0-9]+) de ([0-9]+)", texto):
            return str(ctx.seccion_id(seccion[1], seccion[2]))
        if carga := re.fullmatch(r"carga de la ([0-9]+) de ([0-9]+)", texto):
            return str(ctx.uno("SELECT carga_id FROM abet.carga WHERE seccion_id = %s",
                               ctx.seccion_id(carga[1], carga[2])))
        raise AssertionError(f"No se reconoce la llave {{{texto}}} de la ruta.")
    return re.sub(r"\{([^}]+)\}", resolver, plantilla)


@when(parsers.re(r'el profesor envía (?P<metodo>POST|GET) (?P<ruta>/(?:[^ {]|\{[^}]*\})+) (?P<cuerpo>con "[^"]+" en el campo multipart «archivo»|sin cuerpo)'))
def _profesor_envia(ctx: Escenario, metodo: str, ruta: str, cuerpo: str) -> None:
    ctx.antes = ctx.api.conteos()
    ruta = _ruta_de(ctx, ruta)
    cliente = ctx.sesion(ctx.profesor)
    if metodo == "POST":
        export = re.search(r'"([^"]+)"', cuerpo)[1]
        seccion_id = int(re.fullmatch(r"/api/secciones/([0-9]+)/cargas", ruta)[1])
        ctx.respuesta = _conftest(ctx).A.subir(cliente, seccion_id, ctx.de_inventados(export), export)
    else:
        assert cuerpo == "sin cuerpo"
        ctx.respuesta = cliente.get(ruta)


# Entonces, US-06

@then(parsers.re(r'la API responde 200 con 3 secciones'))
def _responde_tres(ctx: Escenario) -> None:
    assert len(_secciones_visibles(ctx)) == 3
    visibles = ctx.filas("SELECT a.codigo, s.numero FROM acceso.docente_seccion d JOIN abet.seccion s USING (seccion_id)"
                         " JOIN abet.asignatura a USING (asignatura_id) WHERE d.usuario_id = %s ORDER BY 1, 2",
                         ctx.usuario_id(ctx.profesor))
    assert sorted((s["asignatura"]["codigo"], s["numero"]) for s in ctx.respuesta.json()) == visibles


@then(parsers.re(r'una es la 412 de 450002 "(?P<nombre>[^"]+)" en 2026-2, con los PI (?P<pis>[0-9.]+(?:, [0-9.]+)* y [0-9.]+)'))
def _una_es_la_412(ctx: Escenario, nombre: str, pis: str) -> None:
    fila = _fila_de(_secciones_visibles(ctx), "412", "450002")
    assert (fila["asignatura"]["nombre"], fila["periodo"], fila["pi"]) == (nombre, PERIODO, _pis(pis))


@then(parsers.re(r'las otras dos son la 410 y la 412 de 450010 "(?P<nombre>[^"]+)" en 2026-2, cada una con los PI '
                 r'(?P<pis>[0-9.]+(?:, [0-9.]+)* y [0-9.]+)'))
def _las_otras_dos(ctx: Escenario, nombre: str, pis: str) -> None:
    for numero in ("410", "412"):
        fila = _fila_de(_secciones_visibles(ctx), numero, "450010")
        assert (fila["asignatura"]["nombre"], fila["periodo"], fila["pi"]) == (nombre, PERIODO, _pis(pis))


@then(parsers.re(r'las 3 traen tiene_plan verdadero y el estado de carga "(?P<estado>[A-Z_]+)"'))
def _traen_plan_y_estado(ctx: Escenario, estado: str) -> None:
    lista = _secciones_visibles(ctx)
    assert len(lista) == 3
    for fila in lista:
        assert fila["tiene_plan"] is True and fila["estado"] == estado, fila
        assert (fila["carga_id"], fila["filas_leidas"], fila["filas_aceptadas"]) == (None, None, None)


@then(parsers.re(r'las dos secciones 412 traen seccion_id distintos'))
def _412_distintas(ctx: Escenario) -> None:
    lista = _secciones_visibles(ctx)
    ids = [fila["seccion_id"] for fila in lista if fila["numero"] == "412"]
    assert len(ids) == 2 and ids[0] != ids[1]
    assert sorted(ids) == sorted([ctx.seccion_id("412", "450002"), ctx.seccion_id("412", "450010")])


@then(parsers.re(r'la respuesta no trae ningún dato de las secciones 410 y 411 de 450002, ni sus seccion_id'))
def _sin_las_ajenas(ctx: Escenario) -> None:
    lista = _secciones_visibles(ctx)
    ajenas = {ctx.seccion_id(numero, asignatura) for asignatura, numero in CONTROLADAS}
    assert {fila["seccion_id"] for fila in lista}.isdisjoint(ajenas)
    assert [fila for fila in lista if fila["asignatura"]["codigo"] == "450002" and fila["numero"] in ("410", "411")] == []
    texto = ctx.respuesta.text
    for correo in (DOCENTE_410, DOCENTE_411, COORDINACION):
        assert correo not in texto
    assert not any(re.search(rf'"seccion_id": ?{identificador}[,}}]', texto) for identificador in ajenas)


@then(parsers.re(r'la pantalla P2 «Mis secciones» muestra 3 filas, una por sección, con su asignatura, su número, sus PI, el '
                 r'estado "Sin carga" y el botón "Subir export" activo'))
def _p2_datos(ctx: Escenario) -> None:
    """Lo que la API entrega a P2. El dibujo de la pantalla lo comprueba Vitest en el Front (T045)."""
    lista = _secciones_visibles(ctx)
    assert len(lista) == 3
    for fila in lista:
        assert fila["asignatura"]["codigo"] and fila["asignatura"]["nombre"] and fila["numero"] and fila["pi"]
        assert fila["estado"] == "SIN_CARGA"
        # El botón «Subir export» está activo cuando la sección tiene plan de medición.
        assert fila["tiene_plan"] is True


@then(parsers.re(r'en P2 el botón "Subir export" de cada fila abre la pantalla P3 con la asignatura y el número de esa fila, '
                 r'y P3 sube el archivo a POST /api/secciones/\{seccion_id de esa fila\}/cargas, también en las dos filas 412'))
def _p3_datos(ctx: Escenario) -> None:
    """Cada fila trae el seccion_id al que P3 sube el archivo, distinto por fila y del profesor, también en las dos 412."""
    lista = _secciones_visibles(ctx)
    ids = [fila["seccion_id"] for fila in lista]
    assert len(set(ids)) == 3
    for fila in lista:
        assert ctx.seccion_id(fila["numero"], fila["asignatura"]["codigo"]) == fila["seccion_id"]
    # La ruta de subida de cada fila existe y exige que la sección sea del profesor, así que una subida sin
    # archivo a cada una responde 422 de validación y no 403 ni 404.
    cliente = ctx.sesion(ctx.profesor)
    for identificador in ids:
        assert cliente.post(f"/api/secciones/{identificador}/cargas").status_code == 422
    assert ctx.api.conteos() == ctx.antes


# Entonces, US-07

@then(parsers.re(r'abet\.archivo_origen tiene 1 fila con nombre_archivo "(?P<nombre>[^"]+)", hoja "(?P<hoja>[^"]+)", '
                 r'filas_de_datos (?P<filas>[0-9]+) y tipo_fuente "(?P<tipo>[A-Z_]+)"'))
def _archivo_origen_completo(ctx: Escenario, nombre: str, hoja: str, filas: str, tipo: str) -> None:
    assert ctx.cuenta("archivo_origen", "nombre_archivo = %s AND hoja = %s AND filas_de_datos = %s AND tipo_fuente = %s",
                      nombre, hoja, int(filas), tipo) == 1
    assert ctx.cuenta("archivo_origen") == 1


@then(parsers.re(r'abet\.archivo_origen tiene 1 fila con hoja "(?P<hoja>[^"]+)"'))
def _archivo_origen_con_hoja(ctx: Escenario, hoja: str) -> None:
    assert ctx.cuenta("archivo_origen", "hoja = %s", hoja) == 1
    assert ctx.cuenta("archivo_origen") == 1


@then(parsers.re(r'la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" tiene 1 sola carga, en estado '
                 r'"(?P<estado>[A-Z]+)" y con el archivo_id de esa fila'))
def _una_sola_carga(ctx: Escenario, numero: str, asignatura: str, estado: str) -> None:
    filas = ctx.filas("SELECT carga_id, estado, archivo_id FROM abet.carga WHERE seccion_id = %s",
                      ctx.seccion_id(numero, asignatura))
    assert len(filas) == 1 and filas[0][0] == ctx.carga_id and filas[0][1] == estado
    assert ctx.filas("SELECT archivo_id FROM abet.archivo_origen") == [(filas[0][2],)]


@then(parsers.re(r'carga\.subida_por apunta a la fila de acceso\.usuario_autorizado de "(?P<correo>[^"]+)"'))
def _subida_por(ctx: Escenario, correo: str) -> None:
    assert ctx.uno("SELECT subida_por FROM abet.carga WHERE carga_id = %s", ctx.carga_id) == ctx.usuario_id(correo)


@then(parsers.re(r'abet\.carga_columna de esa carga tiene los PI (?P<pis>[0-9.]+(?:, [0-9.]+)* y [0-9.]+)'))
def _columnas_de_la_carga(ctx: Escenario, pis: str) -> None:
    assert [pi for (pi,) in ctx.filas("SELECT pi_codigo FROM abet.carga_columna WHERE carga_id = %s ORDER BY pi_codigo",
                                      ctx.carga_id)] == sorted(_pis(pis))


@then(parsers.re(r'abet\.medicion tiene (?P<n>[0-9]+) filas de esa carga'))
def _mediciones(ctx: Escenario, n: str) -> None:
    assert ctx.cuenta("medicion", "carga_id = %s", ctx.carga_id) == int(n)


@then(parsers.re(r'abet\.estudiante tiene los códigos (?P<desde>[0-9]+) a (?P<hasta>[0-9]+) y ningún otro'))
def _estudiantes(ctx: Escenario, desde: str, hasta: str) -> None:
    assert {codigo for (codigo,) in ctx.filas("SELECT codigo FROM abet.estudiante")} == {
        str(n) for n in range(int(desde), int(hasta) + 1)}


@then(parsers.re(r'abet\.estudiante no tiene ninguno de los códigos (?P<desde>[0-9]+) a (?P<hasta>[0-9]+)'))
def _sin_estudiantes(ctx: Escenario, desde: str, hasta: str) -> None:
    assert ctx.cuenta("estudiante", "codigo BETWEEN %s AND %s", desde, hasta) == 0


@then(parsers.re(r'las otras dos secciones del profesor y las secciones 410 y 411 de "450002" no tienen ninguna carga'))
def _las_otras_sin_carga(ctx: Escenario) -> None:
    propias = ctx.filas("SELECT s.seccion_id FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                        " JOIN acceso.docente_seccion d USING (seccion_id) WHERE d.usuario_id = %s",
                        ctx.usuario_id(ctx.profesor))
    con_carga = {seccion for (seccion,) in ctx.filas("SELECT seccion_id FROM abet.carga")}
    assert len(propias) == 3 and len(con_carga) == 1
    assert len({seccion for (seccion,) in propias} & con_carga) == 1
    for asignatura, numero in CONTROLADAS:
        assert ctx.seccion_id(numero, asignatura) not in con_carga


@then(parsers.re(r'GET /api/secciones\?periodo=2026-2 trae la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" con el '
                 r'estado de carga "(?P<estado>[A-Z]+)" y filas_aceptadas (?P<aceptadas>[0-9]+), y las otras dos '
                 r'secciones del profesor con "(?P<sin>[A-Z_]+)"'))
def _lista_tras_la_carga(ctx: Escenario, numero: str, asignatura: str, estado: str, aceptadas: str, sin: str) -> None:
    lista = ctx.sesion(ctx.profesor).get(f"/api/secciones?periodo={PERIODO}").json()
    assert len(lista) == 3
    propia = _fila_de(lista, numero, asignatura)
    assert (propia["estado"], propia["filas_aceptadas"], propia["carga_id"]) == (estado, int(aceptadas), ctx.carga_id)
    for fila in lista:
        if fila is not propia:
            assert (fila["estado"], fila["filas_aceptadas"], fila["carga_id"]) == (sin, None, None), fila


# Entonces, US-13

@then(parsers.re(r'la carga queda en la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)", en estado "(?P<estado>[A-Z]+)" '
                 r'y con filas_leidas (?P<leidas>[0-9]+), filas_aceptadas (?P<aceptadas>[0-9]+) y filas_rechazadas '
                 r'(?P<rechazadas>[0-9]+)'))
def _carga_rechazada(ctx: Escenario, numero: str, asignatura: str, estado: str, leidas: str, aceptadas: str,
                     rechazadas: str) -> None:
    assert ctx.filas("SELECT carga_id, estado, filas_leidas, filas_aceptadas, filas_rechazadas FROM abet.carga"
                     " WHERE seccion_id = %s", ctx.seccion_id(numero, asignatura)) == [
        (ctx.carga_id, estado, int(leidas), int(aceptadas), int(rechazadas))]


@then(parsers.re(r'abet\.rechazo_fila tiene exactamente 1 fila de esa carga, con motivo "(?P<motivo>[A-Z_]+)", efecto '
                 r'"(?P<efecto>[A-Z_]+)" y fila_origen nulo'))
def _un_rechazo(ctx: Escenario, motivo: str, efecto: str) -> None:
    assert ctx.filas("SELECT motivo, efecto, fila_origen FROM abet.rechazo_fila WHERE carga_id = %s", ctx.carga_id) == [
        (motivo, efecto, None)]


@then(parsers.re(r'la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" no tiene ninguna carga "(?P<estado>[A-Z]+)"'))
def _sin_carga_en_estado(ctx: Escenario, numero: str, asignatura: str, estado: str) -> None:
    assert ctx.cuenta("carga", "seccion_id = %s AND estado = %s", ctx.seccion_id(numero, asignatura), estado) == 0


@then(parsers.re(r'la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" no tiene ninguna carga'))
def _sin_ninguna_carga(ctx: Escenario, numero: str, asignatura: str) -> None:
    assert ctx.cuenta("carga", "seccion_id = %s", ctx.seccion_id(numero, asignatura)) == 0


# Entonces, el 403 y el 409

@then(parsers.re(r'la API responde 403 con el cuerpo (?P<cuerpo>\{.+\})'))
def _responde_403(ctx: Escenario, cuerpo: str) -> None:
    assert ctx.respuesta.status_code == 403, ctx.respuesta.text
    assert ctx.respuesta.json() == json.loads(cuerpo)


@then(parsers.re(r'la respuesta no trae ningún dato de la sección 410 de "450002" ni de su carga'))
def _sin_datos_de_la_410(ctx: Escenario) -> None:
    assert ctx.respuesta.json().keys() == {"detail"}
    texto = ctx.respuesta.text
    huella = ctx.uno("SELECT sha256 FROM abet.archivo_origen WHERE archivo_id = (SELECT archivo_id FROM abet.carga"
                     " WHERE carga_id = %s)", ctx.carga_previa)
    for prohibido in (str(ctx.carga_previa), huella, "99000001", DOCENTE_410, "sintetico_20262_450002_410"):
        assert prohibido not in texto, prohibido
    assert str(ctx.seccion_id("410", "450002")) not in re.findall(r"[0-9]+", texto)


@then(parsers.re(r'el cuerpo de la respuesta no contiene ese carga_id, la huella del archivo, el número 412 ni la asignatura 450002'))
def _409_sin_datos(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 409
    texto = ctx.respuesta.text
    huella = ctx.uno("SELECT sha256 FROM abet.archivo_origen WHERE archivo_id = (SELECT archivo_id FROM abet.carga"
                     " WHERE carga_id = %s)", ctx.carga_previa)
    assert str(ctx.carga_previa) not in re.findall(r"[0-9]+", texto)
    assert huella not in texto and "412" not in texto and "450002" not in texto


@then(parsers.re(r'la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" sigue con 1 carga "(?P<estado>[A-Z]+)", la de '
                 r'"(?P<export>[^"]+)", y sus (?P<mediciones>[0-9]+) mediciones'))
def _sigue_con_su_carga(ctx: Escenario, numero: str, asignatura: str, estado: str, export: str, mediciones: str) -> None:
    filas = ctx.filas("SELECT c.carga_id, c.estado, ao.nombre_archivo FROM abet.carga c JOIN abet.archivo_origen ao"
                      " USING (archivo_id) WHERE c.seccion_id = %s", ctx.seccion_id(numero, asignatura))
    assert filas == [(ctx.carga_previa, estado, export)]
    assert ctx.cuenta("medicion", "carga_id = %s", ctx.carga_previa) == int(mediciones)
