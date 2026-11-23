"""Pasos de resultados.feature de la spec 004 (US-37, US-39, US-40, US-41, US-43 y US-44), con pytest-bdd (T033).

El .feature manda. Ningún paso cambia una cifra, un mensaje ni un título para que el escenario pase, y cada
«Entonces» se comprueba contra la respuesta de GET /api/resultados, contra la base o contra el R-17 descargado de la
misma carga, sin dobles del sistema bajo prueba. Las cargas de partida se suben por la API con la sesión de quien el
escenario nombra, así que pasan por las mismas reglas que cualquier carga. Los pasos que repite
alcance_y_privacidad.feature (los Antecedentes, las subidas de partida y la petición a la ruta 12) viven en el
conftest.py de esta carpeta.

Los escenarios de la pantalla P6 llevan @delegado_a_vitest. Sus pasos registran la propiedad «delegado_a_vitest» con
las pruebas de Vitest del Front que los comprueban, en tests/pantallas/MisLogros.test.tsx y tests/App.test.tsx, como
test_acceso_feature.py. Un escenario de pantalla sin sus pruebas anotadas hace fallar sus pasos.
"""

from __future__ import annotations

import io
import re
import sys
from dataclasses import replace
from typing import Any

from openpyxl import load_workbook
from pytest_bdd import given, parsers, scenarios, then, when
from pytest_bdd.scenario import scenario_wrapper_template_registry

from abet_carga import r17

A = sys.modules["api_de_prueba"]
C = sys.modules.get("cargas_de_prueba")
Escenario = Any

scenarios("specs/004-reportes-docente/aceptacion/resultados.feature")

CIFRA = re.compile(r"([0-9]+,[0-9]) % \(([0-9]+) de ([0-9]+)\)")
FILAS_DEL_BLOQUE_II = (24, 25, 26)
FILAS_DE_FRECUENCIAS = (29, 30, 31)


def _cargas_de_prueba() -> Any:
    """tests/cargas_de_prueba.py, cargado por su ruta como lo cargan las pruebas del R-17."""
    if "cargas_de_prueba" not in sys.modules:
        import importlib.util
        from pathlib import Path

        ruta = Path(__file__).resolve().parents[2] / "cargas_de_prueba.py"
        especificacion = importlib.util.spec_from_file_location("cargas_de_prueba", ruta)
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules["cargas_de_prueba"] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules["cargas_de_prueba"]


def _conftest(ctx: Escenario) -> Any:
    """Módulo conftest.py de esta carpeta, que pytest registra como plugin, para reutilizar sus ayudas."""
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            return plugin
    raise AssertionError("no se encontró el conftest.py del arnés de aceptación")


# Lectura de la respuesta

def _cuerpo(ctx: Escenario) -> dict[str, Any]:
    assert ctx.respuesta is not None and ctx.respuesta.status_code == 200, ctx.respuesta.text
    return ctx.respuesta.json()


def _seccion(ctx: Escenario, numero: str, asignatura: str = "450002") -> dict[str, Any]:
    secciones = [s for s in _cuerpo(ctx)["secciones"] if (s["asignatura"]["codigo"], s["numero"]) == (asignatura, numero)]
    assert len(secciones) == 1, f"la respuesta trae {len(secciones)} veces la sección {numero} de {asignatura}"
    return secciones[0]


def _unica_seccion(ctx: Escenario) -> dict[str, Any]:
    [seccion] = _cuerpo(ctx)["secciones"]
    return seccion


def _indicador(seccion: dict[str, Any], pi: str) -> dict[str, Any]:
    indicadores = [i for i in seccion["indicadores"] if i["pi"] == pi]
    assert len(indicadores) == 1, f"la sección {seccion['numero']} trae {len(indicadores)} indicadores {pi}"
    return indicadores[0]


def _indicadores(ctx: Escenario) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    return [(s, i) for s in _cuerpo(ctx)["secciones"] for i in s["indicadores"]]


def _lista(texto: str) -> list[str]:
    """Elementos de una enumeración en español, «5.1, 5.2 y 5.3»."""
    return [parte.strip() for parte in re.split(r", | y ", texto) if parte.strip()]


def _cifras(texto: str) -> list[tuple[float, int, int]]:
    return [(float(p.replace(",", ".")), int(n), int(d)) for p, n, d in CIFRA.findall(texto)]


def _valor(texto: str) -> Any:
    """Valor de un campo como lo escribe el .feature, «[1, 3, 4, 3]», «81.8», «11», «nulo» o «verdadero»."""
    texto = texto.strip()
    if texto.startswith("["):
        return [int(x) for x in re.findall(r"[0-9]+", texto)]
    if texto in ("verdadero", "falso", "nulo"):
        return {"verdadero": True, "falso": False, "nulo": None}[texto]
    if texto.startswith('"'):
        return texto.strip('"')
    return float(texto) if "." in texto else int(texto)


def _campos(texto: str) -> dict[str, Any]:
    """Pares «campo valor» de una frase como «logrados 8, calificados 10 y en_meta verdadero»."""
    partes = re.split(r"(?:, | y )(?=[a-z_]+ )", texto)
    return {campo: _valor(valor) for campo, valor in (parte.split(" ", 1) for parte in partes)}


def _comprobar_campos(indicador: dict[str, Any], campos: dict[str, Any]) -> None:
    for campo, esperado in campos.items():
        assert indicador[campo] == esperado, (indicador["pi"], campo, indicador[campo], esperado)
        if isinstance(esperado, float):
            assert isinstance(indicador[campo], float), (campo, type(indicador[campo]))


# Pantalla P6, delegada a Vitest

VITEST_P6 = "front/tests/pantallas/MisLogros.test.tsx › P6 Mis logros por SO › "
VITEST_APP = "front/tests/App.test.tsx › App › "
CUBIERTO_POR_VITEST = {
    "P6 agrupa los PI por SO y escribe cada cifra": [
        VITEST_P6 + "agrupa los PI bajo su SO y cada fila escribe su PI, su sección, su porcentaje, su fracción y su estado",
        VITEST_P6 + "cada barra lleva aria-hidden, su ancho es el porcentaje y la meta va marcada con una línea y con texto",
    ],
    "P6 se abre desde P2 y desde P4 sin confundirse con «Ver resultado»": [
        VITEST_APP + "la cabecera ofrece una sola vez «Ver mis logros por SO», que abre P6, y P6 vuelve a P2 con «Volver»",
        VITEST_APP + "P4 de una carga publicada ofrece también el enlace a P6",
    ],
    "P6 ofrece el R-17 de cada sección publicada": [
        VITEST_P6 + "ofrece el R-17 solo de cada sección publicada, con el carga_id de su carga",
    ],
    "P6 no pinta lo que no se mide": [
        VITEST_P6 + "escribe lo que no se mide y no dibuja ninguna barra de 0 %",
    ],
    "P6 muestra la espera, el error y la lista vacía": [
        VITEST_P6 + "dice que espera mientras la API responde, el error del servicio y la lista vacía",
        VITEST_APP + "un 401 en P6 vuelve a P1 con el aviso de sesión vencida",
    ],
    "P6 escribe la marca provisional de cada sección": [
        VITEST_P6 + "escribe la marca provisional de una sección según su conjunto de reglas ($conjunto en $estado)",
    ],
    "P6 escribe el reparto por nivel": [
        VITEST_P6 + "escribe el reparto por nivel de cada PI, con el conteo de cada tramo",
    ],
    "P6 del coordinador agrupa por asignatura y no ordena por resultado": [
        VITEST_P6 + "el coordinador ve las secciones agrupadas por asignatura y en el orden de su número, nunca por su porcentaje",
        VITEST_APP + "el coordinador abre P6 con «Ver los logros por SO de la carrera»",
    ],
}


def _delegar(ctx: Escenario, texto: str) -> None:
    """Deja constancia de un paso de pantalla y de las pruebas de Vitest del Front que comprueban su escenario."""
    escenario = scenario_wrapper_template_registry[ctx.request.node.function].name
    pruebas = CUBIERTO_POR_VITEST.get(escenario)
    assert pruebas, f"el escenario de pantalla «{escenario}» no tiene pruebas de Vitest anotadas"
    ctx.request.node.user_properties.append(("delegado_a_vitest", f"{texto} → {'; '.join(pruebas)}"))


@given(parsers.re(r'(?P<texto>la respuesta del escenario «[^»]+»|"[^"]+" en la pantalla P2 «Mis secciones» con .+'
                  r'|una respuesta de GET /api/resultados con .+|respuestas de GET /api/resultados con .+'
                  r'|el profesor con la sesión iniciada que abre P6|una sección de GET /api/resultados con provisional .+)'))
def _pantalla_dada(ctx: Escenario, texto: str) -> None:
    _delegar(ctx, texto)


@when(parsers.re(r'(?P<texto>(?:"[^"]+"|el profesor) abre (?:la pantalla )?P6.*)'))
def _abre_p6(ctx: Escenario, texto: str) -> None:
    _delegar(ctx, texto)


@then(parsers.re(r'(?P<texto>P6 .+|cada fila escribe .+|[0-9]+ filas dicen .+|la barra de cada fila .+'
                 r'|la cabecera muestra .+|la fila de la 410 conserva .+|P4 de la carga .+'
                 r'|la sección 412 de "450002" ofrece el enlace .+|las secciones 410 y 412 de "450010" no ofrecen .+'
                 r'|la sección en "SIN_CARGA" dice .+|el 5\.[0-9] dice .+|mientras la API responde, .+'
                 r'|con un 401 vuelve .+|sin respuesta del servicio .+|con "secciones" vacío .+|esa sección .+'
                 r'|la barra apilada de .+)'))
def _pantalla_muestra(ctx: Escenario, texto: str) -> None:
    _delegar(ctx, texto)


# Antecedentes y datos de partida propios de este .feature

@given('plan_medicion registra los PI 5.1, 5.2 y 5.3 para la asignatura "450002" en "2026-2" y los PI 2.1, 2.2 y 5.1 '
       'para "450010", con el instrumento "Trabajo Integrador"')
def _planes_de_la_spec_004(ctx: Escenario) -> None:
    filas = ctx.filas("SELECT a.codigo, p.codigo, i.nombre FROM abet.plan_medicion pm JOIN abet.pi p USING (pi_id)"
                      " JOIN abet.asignatura a USING (asignatura_id) JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id"
                      " LEFT JOIN abet.instrumento i ON i.instrumento_id = pm.instrumento_id WHERE pe.codigo = '2026-2'")
    assert sorted(filas) == [("450002", "5.1", "Trabajo Integrador"), ("450002", "5.2", "Trabajo Integrador"),
                             ("450002", "5.3", "Trabajo Integrador"), ("450010", "2.1", "Trabajo Integrador"),
                             ("450010", "2.2", "Trabajo Integrador"), ("450010", "5.1", "Trabajo Integrador")]


@given(parsers.re(r'que "(?P<nombre>[^"]+)" está subido por "(?P<quien>[^"]+)" a la sección (?P<numero>[0-9]+) de '
                  r'"(?P<asignatura>[0-9]+)" con respuesta 201 y su carga_id'))
def _subido_a_una_seccion_de_otra_asignatura(ctx: Escenario, nombre: str, quien: str, numero: str,
                                            asignatura: str) -> None:
    respuesta = ctx.subir(quien, ctx.de_inventados(nombre), nombre, numero, asignatura)
    assert respuesta.status_code == 201, respuesta.text
    ctx.carga_previa = ctx.carga_id


@given(parsers.re(r'que "(?P<correo>[^"]+)", activo, con rol "(?P<rol>[A-Z]+)" y sin filas en acceso\.docente_seccion, '
                  r'tiene la sesión iniciada'))
def _profesor_sin_secciones(ctx: Escenario, correo: str, rol: str) -> None:
    # El dueño de la base crea este usuario solo en la base desechable, porque abet_app no escribe en acceso.
    ctx.api.dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES (%s, %s)", (correo, rol))
    assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion d JOIN acceso.usuario_autorizado u USING (usuario_id)"
                   " WHERE u.correo = %s", correo) == 0
    ctx.sesion(correo)
    ctx.extras["con_sesion"] = correo


@given(parsers.re(r'que la base tiene el conjunto "(?P<version>[^"]+)" de Ambiental en estado "APROBADO" con META_LOGRO 0,70, '
                  r'NIVEL_ESPERADO 2, CORTE_ROJO 0,50, TRATO_SIN_EVIDENCIA "SE_EXCLUYE_DEL_DENOMINADOR" y la conversión '
                  r'de sus 4 niveles, como en el caso A03 de pruebas\.sql'))
def _conjunto_aprobado(ctx: Escenario, version: str) -> None:
    _cargas_de_prueba().conjunto_aprobado(ctx.api.dueno, version)
    assert ctx.filas("SELECT estado FROM abet.conjunto_reglas WHERE version = %s AND carrera_id = (SELECT carrera_id FROM abet.carrera WHERE codigo = 'AMB')", version) == [("APROBADO",)]


@given(parsers.re(r'que la base tiene el conjunto "(?P<version>[^"]+)" de Ambiental en estado "APROBADO" con META_LOGRO 0,80 '
                  r'y NIVEL_ESPERADO 3 en DEFINIDO y TRATO_SIN_EVIDENCIA en PENDIENTE'))
def _conjunto_aprobado_incompleto(ctx: Escenario, version: str) -> None:
    dueno = ctx.api.dueno
    dueno.execute("INSERT INTO abet.conjunto_reglas (carrera_id, version, estado, aprobado_por, aprobado_en)"
                  " SELECT carrera_id, %s, 'APROBADO', 'Comité de prueba', DATE '2026-10-01' FROM abet.carrera"
                  " WHERE codigo = 'AMB'", (version,))
    for clave, estado, numero, texto in (("META_LOGRO", "DEFINIDO", 0.80, None), ("NIVEL_ESPERADO", "DEFINIDO", 3, None),
                                         ("CORTE_ROJO", "DEFINIDO", 0.50, None),
                                         ("CONVERSION_NIVEL_0_1", "DEFINIDO", None, None),
                                         ("TRATO_SIN_EVIDENCIA", "PENDIENTE", None, None)):
        dueno.execute("INSERT INTO abet.parametro_valor (conjunto_reglas_id, clave, estado, valor_numero, valor_texto)"
                      " SELECT conjunto_reglas_id, %s, %s, %s, %s FROM abet.conjunto_reglas WHERE version = %s AND carrera_id = (SELECT carrera_id FROM abet.carrera WHERE codigo = 'AMB')",
                      (clave, estado, numero, texto, version))
    for nivel, valor in ((1, 0.0), (2, 0.3333), (3, 0.6667), (4, 1.0)):
        dueno.execute("INSERT INTO abet.conversion_nivel_0_1 (conjunto_reglas_id, nivel_original, valor_0_1)"
                      " SELECT conjunto_reglas_id, %s, %s FROM abet.conjunto_reglas WHERE version = %s AND carrera_id = (SELECT carrera_id FROM abet.carrera WHERE codigo = 'AMB')",
                      (nivel, valor, version))
    # Es el caso que vigila la consulta de control Q11, un conjunto aprobado con un parámetro de la vista en PENDIENTE.
    assert len(ctx.filas(_conftest(ctx).consultas_de_control()["Q11"])) == 1


@given(parsers.re(r'la API configurada con CONJUNTO_REGLAS "(?P<version>[^"]+)"'))
def _api_con_otro_conjunto(ctx: Escenario, version: str) -> None:
    ctx.reiniciar_api(carga=replace(ctx.api.ajustes.carga, conjunto_reglas=version))
    assert ctx.api.ajustes.carga.conjunto_reglas == version


@given(parsers.re(r'que esa carga A se reemplaza con "(?P<nombre>[^"]+)" en la carga B, como en US-18'))
def _reemplazo_de_a_por_b(ctx: Escenario, nombre: str) -> None:
    anterior = ctx.carga_previa
    assert anterior is not None
    respuesta = ctx.subir(ctx.profesor, ctx.de_inventados(nombre), nombre, "410", params={"reemplaza": str(anterior)})
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "PUBLICADA", respuesta.text
    ctx.extras["cargas"] = {"A": anterior, "B": respuesta.json()["carga_id"]}
    assert ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", anterior) == "REEMPLAZADA"


# Cuando, las variantes de la petición que solo usa este .feature

@when(parsers.re(r'se envía GET /api/resultados\?periodo=(?P<periodo>[0-9]+-[0-9]+) cinco veces'))
def _pide_cinco_veces(ctx: Escenario, periodo: str) -> None:
    ctx.extras["filas_antes"] = _filas_por_tabla(ctx)
    for _ in range(5):
        assert _conftest(ctx).pedir_resultados(ctx, periodo).status_code == 200


@when(parsers.re(r'se envía GET /api/resultados\?periodo=(?P<periodo>[0-9]+-[0-9]+) y se descarga el R-17 de '
                 r'(?P<cuales>cada una de las tres cargas|esa carga)'))
def _pide_y_descarga(ctx: Escenario, periodo: str, cuales: str) -> None:
    _conftest(ctx).pedir_resultados(ctx, periodo)
    cliente = ctx.sesion(ctx.extras["con_sesion"])
    if cuales == "esa carga":
        cargas = [ctx.carga_previa]
    else:
        cargas = [s["carga_id"] for s in _cuerpo(ctx)["secciones"] if s["carga_id"] is not None]
        assert len(cargas) == 3, cargas
    libros = {}
    for carga_id in cargas:
        descarga = cliente.get(f"/api/cargas/{carga_id}/r17.xlsx")
        assert descarga.status_code == 200, descarga.text
        libros[carga_id] = load_workbook(io.BytesIO(descarga.content), data_only=True)[r17.HOJA]
    ctx.extras["r17"] = libros


# Entonces, el cuerpo de la ruta 12

@then(parsers.re(r'la API responde 200 con (?P<n>[0-9]+) secciones y (?P<m>[0-9]+) indicadores, cada uno con meta_pct '
                 r'(?P<meta>[0-9.]+) e instrumento "(?P<instrumento>[^"]+)"'))
def _secciones_e_indicadores(ctx: Escenario, n: str, m: str, meta: str, instrumento: str) -> None:
    assert len(_cuerpo(ctx)["secciones"]) == int(n)
    indicadores = [i for _, i in _indicadores(ctx)]
    assert len(indicadores) == int(m)
    assert all(i["meta_pct"] == float(meta) and i["instrumento"] == instrumento for i in indicadores), indicadores


@then(parsers.re(r'la API responde 200 con (?P<n>[0-9]+) secciones y (?P<m>[0-9]+) indicadores, los de la sección '
                 r'(?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)"'))
def _indicadores_de_una_seccion(ctx: Escenario, n: str, m: str, numero: str, asignatura: str) -> None:
    assert len(_cuerpo(ctx)["secciones"]) == int(n)
    con_indicadores = [s for s in _cuerpo(ctx)["secciones"] if s["indicadores"]]
    assert [(s["asignatura"]["codigo"], s["numero"]) for s in con_indicadores] == [(asignatura, numero)]
    assert len(con_indicadores[0]["indicadores"]) == int(m)


@then(parsers.re(r'la API responde 200 con 1 sección, la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)", con estado '
                 r'"SIN_CARGA", carga_id nulo e indicadores vacíos'))
def _una_seccion_sin_carga(ctx: Escenario, numero: str, asignatura: str) -> None:
    seccion = _unica_seccion(ctx)
    assert (seccion["asignatura"]["codigo"], seccion["numero"]) == (asignatura, numero)
    assert (seccion["estado"], seccion["carga_id"], seccion["indicadores"]) == ("SIN_CARGA", None, [])


@then(parsers.re(r'la API responde 200 con "so" vacío y "secciones" vacío'))
def _listas_vacias(ctx: Escenario) -> None:
    cuerpo = _cuerpo(ctx)
    assert (cuerpo["so"], cuerpo["secciones"]) == ([], [])


@then(parsers.re(r'las secciones llegan en el orden (?P<orden>.+)'))
def _orden_de_las_secciones(ctx: Escenario, orden: str) -> None:
    esperado = re.findall(r'([0-9]+) de "([0-9]+)"', orden)
    assert [(s["numero"], s["asignatura"]["codigo"]) for s in _cuerpo(ctx)["secciones"]] == esperado


@then(parsers.re(r'"so" trae los SO (?P<lista>[0-9]+ y [0-9]+), en ese orden, cada uno con su descripción de abet\.so'))
def _so_con_descripcion(ctx: Escenario, lista: str) -> None:
    numeros = [int(x) for x in _lista(lista)]
    descripciones = dict(ctx.filas("SELECT so.numero, so.descripcion FROM abet.so so JOIN abet.catalogo_version cv"
                                   " USING (catalogo_version_id) WHERE cv.codigo = 'AMB-2026'"))
    assert _cuerpo(ctx)["so"] == [{"numero": n, "descripcion": descripciones[n]} for n in numeros]


@then('"so" trae los SO 2 y 5, porque el plan de 450010 mide el SO 2 aunque sus secciones no tengan carga')
def _so_de_los_planes(ctx: Escenario) -> None:
    assert [so["numero"] for so in _cuerpo(ctx)["so"]] == [2, 5]
    assert all(not s["indicadores"] for s in _cuerpo(ctx)["secciones"] if s["asignatura"]["codigo"] == "450010")


CLAUSULA = re.compile(r'(?:(?P<pis>[0-9]+\.[0-9]+(?:(?:, | y )[0-9]+\.[0-9]+)*) )?de (?:la sección (?P<una>[0-9]+)'
                      r'|las secciones (?P<dos>[0-9]+ y [0-9]+)) de "(?P<asignatura>[0-9]+)", con (?P<cifras>'
                      r'[0-9]+,[0-9] % \([0-9]+ de [0-9]+\)(?:(?:, | y )[0-9]+,[0-9] % \([0-9]+ de [0-9]+\))*)')


@then(parsers.re(r'el SO (?P<so>[0-9]+) reúne (?P<resto>.+)'))
def _so_reune(ctx: Escenario, so: str, resto: str) -> None:
    esperados, pis = {}, None
    for clausula in CLAUSULA.finditer(resto):
        pis = _lista(clausula["pis"]) if clausula["pis"] else pis
        secciones = [clausula["una"]] if clausula["una"] else _lista(clausula["dos"])
        cifras = _cifras(clausula["cifras"])
        pares = ([(pi, secciones[0]) for pi in pis] if len(secciones) == 1 else [(pis[0], s) for s in secciones])
        assert len(pares) == len(cifras), (pares, cifras)
        for (pi, numero), cifra in zip(pares, cifras, strict=True):
            esperados[(clausula["asignatura"], numero, pi)] = cifra
    assert esperados, f"no se reconoce ninguna sección en «{resto}»"
    del_so = {(s["asignatura"]["codigo"], s["numero"], i["pi"]): (i["pct_sobre_calificados"], i["logrados"],
                                                                   i["calificados"])
              for s, i in _indicadores(ctx) if i["so"] == int(so)}
    assert del_so == esperados


@then(parsers.re(r'en_meta es verdadero en (?P<n>[0-9]+) indicadores, (?P<lista>.+), y falso en los otros (?P<m>[0-9]+)'))
def _en_meta_por_indicador(ctx: Escenario, n: str, lista: str, m: str) -> None:
    verdaderos = set()
    for grupo in re.finditer(r'(?P<pis>[0-9]+\.[0-9]+(?: y [0-9]+\.[0-9]+)?) de la sección (?P<numero>[0-9]+) de '
                             r'"(?P<asignatura>[0-9]+)"', lista):
        verdaderos |= {(grupo["asignatura"], grupo["numero"], pi) for pi in _lista(grupo["pis"])}
    assert len(verdaderos) == int(n)
    por_indicador = {(s["asignatura"]["codigo"], s["numero"], i["pi"]): i["en_meta"] for s, i in _indicadores(ctx)}
    assert {clave for clave, valor in por_indicador.items() if valor is True} == verdaderos
    assert sum(valor is False for valor in por_indicador.values()) == int(m)


@then('la sección 412 de "450002" y la sección 412 de "450010" traen seccion_id y carga_id distintos, cada una con su '
      'propio 5.1')
def _dos_secciones_412(ctx: Escenario) -> None:
    a, b = _seccion(ctx, "412", "450002"), _seccion(ctx, "412", "450010")
    assert a["seccion_id"] != b["seccion_id"] and a["carga_id"] != b["carga_id"]
    for seccion, asignatura in ((a, "450002"), (b, "450010")):
        assert seccion["seccion_id"] == ctx.seccion_id("412", asignatura)
        assert seccion["carga_id"] == ctx.uno("SELECT carga_id FROM abet.carga WHERE seccion_id = %s"
                                              " AND estado = 'PUBLICADA'", seccion["seccion_id"])
    assert _indicador(a, "5.1")["pct_sobre_calificados"] != _indicador(b, "5.1")["pct_sobre_calificados"]


@then(parsers.re(r'el indicador (?P<pi>[0-9]+\.[0-9]+) de la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" '
                 r'trae (?P<campos>.+)'))
def _indicador_trae(ctx: Escenario, pi: str, numero: str, asignatura: str, campos: str) -> None:
    _comprobar_campos(_indicador(_seccion(ctx, numero, asignatura), pi), _campos(campos))


@then('pct_sobre_calificados, pct_sobre_total y meta_pct llegan como números JSON y no como textos')
def _numeros_json(ctx: Escenario) -> None:
    texto = ctx.respuesta.text
    for campo in ("pct_sobre_calificados", "pct_sobre_total", "meta_pct"):
        assert re.search(rf'"{campo}":[0-9]', texto), campo
        assert not re.search(rf'"{campo}":"', texto), campo


@then(parsers.re(r'los indicadores (?P<pis>[0-9]+\.[0-9]+ y [0-9]+\.[0-9]+) traen (?P<cifra>[0-9]+,[0-9] % '
                 r'\([0-9]+ de [0-9]+\))(?: y en_meta (?P<en_meta>verdadero|falso))?'))
def _indicadores_traen(ctx: Escenario, pis: str, cifra: str, en_meta: str | None) -> None:
    [(pct, logrados, calificados)] = _cifras(cifra)
    seccion = _unica_seccion(ctx)
    for pi in _lista(pis):
        indicador = _indicador(seccion, pi)
        assert (indicador["pct_sobre_calificados"], indicador["logrados"], indicador["calificados"]) == (
            pct, logrados, calificados), indicador
        if en_meta is not None:
            assert indicador["en_meta"] is (en_meta == "verdadero")


@then(parsers.re(r'los indicadores (?P<pis>[0-9]+\.[0-9]+ y [0-9]+\.[0-9]+) traen el mismo número en '
                 r'pct_sobre_calificados y en pct_sobre_total, (?P<valores>[0-9.]+ y [0-9.]+)'))
def _mismo_numero(ctx: Escenario, pis: str, valores: str) -> None:
    seccion = _unica_seccion(ctx)
    for pi, valor in zip(_lista(pis), _lista(valores), strict=True):
        indicador = _indicador(seccion, pi)
        assert indicador["pct_sobre_calificados"] == indicador["pct_sobre_total"] == float(valor), indicador


@then(parsers.re(r'las secciones (?P<a>[0-9]+) y (?P<b>[0-9]+) de "(?P<asignatura>[0-9]+)" traen estado "SIN_CARGA", '
                 r'carga_id nulo, pi \[(?P<pis>[^\]]*)\] e indicadores vacíos, como el estado de GET /api/secciones'))
def _sin_carga_como_en_secciones(ctx: Escenario, a: str, b: str, asignatura: str, pis: str) -> None:
    lista = ctx.sesion(ctx.extras["con_sesion"]).get("/api/secciones", params={"periodo": "2026-2"}).json()
    de_secciones = {(s["asignatura"]["codigo"], s["numero"]): s for s in lista}
    for numero in (a, b):
        seccion = _seccion(ctx, numero, asignatura)
        assert (seccion["estado"], seccion["carga_id"], seccion["pi"], seccion["indicadores"]) == (
            "SIN_CARGA", None, re.findall(r'"([^"]+)"', pis), [])
        assert (seccion["estado"], seccion["pi"]) == (de_secciones[(asignatura, numero)]["estado"],
                                                       de_secciones[(asignatura, numero)]["pi"])


# Entonces, las cifras contra el R-17 de la misma carga

def _fila_del_r17(hoja: Any, filas: tuple[int, ...], columna: str, pi: str) -> int:
    encontradas = [fila for fila in filas if hoja[f"{columna}{fila}"].value == pi]
    assert len(encontradas) == 1, (pi, [hoja[f"{columna}{fila}"].value for fila in filas])
    return encontradas[0]


def _por_cada_indicador(ctx: Escenario) -> list[tuple[dict[str, Any], dict[str, Any], Any]]:
    return [(s, i, ctx.extras["r17"][s["carga_id"]]) for s, i in _indicadores(ctx)]


@then('en cada indicador pct_sobre_calificados es igual a round(100 × la celda E de su fila del bloque II, 1) y a '
      'pct_logro_sobre_calificados de abet.v_r17_por_pi para esa carga y ese PI')
def _logro_igual_al_r17(ctx: Escenario) -> None:
    revisados = 0
    for seccion, indicador, hoja in _por_cada_indicador(ctx):
        fila = _fila_del_r17(hoja, FILAS_DEL_BLOQUE_II, "B", indicador["pi"])
        assert indicador["pct_sobre_calificados"] == round(100 * hoja[f"E{fila}"].value, 1)
        vista = ctx.uno("SELECT pct_logro_sobre_calificados FROM abet.v_r17_por_pi WHERE carga_id = %s AND pi = %s",
                        seccion["carga_id"], indicador["pi"])
        assert indicador["pct_sobre_calificados"] == float(vista)
        revisados += 1
    assert revisados == 9


@then('meta_pct es igual a round(100 × la celda G de esa fila, 1) y pct_sobre_total es igual a round(100 × la celda Q '
      'de su fila de las frecuencias, 1)')
def _meta_y_total_iguales_al_r17(ctx: Escenario) -> None:
    for _, indicador, hoja in _por_cada_indicador(ctx):
        fila = _fila_del_r17(hoja, FILAS_DEL_BLOQUE_II, "B", indicador["pi"])
        assert indicador["meta_pct"] == round(100 * hoja[f"G{fila}"].value, 1)
        frecuencia = _fila_del_r17(hoja, FILAS_DE_FRECUENCIAS, "K", indicador["pi"])
        assert indicador["pct_sobre_total"] == round(100 * hoja[f"Q{frecuencia}"].value, 1)


@then('en_meta es verdadero si y solo si la celda H de esa fila trae el texto de logro del plan de acción del R-17')
def _en_meta_igual_al_r17(ctx: Escenario) -> None:
    for _, indicador, hoja in _por_cada_indicador(ctx):
        fila = _fila_del_r17(hoja, FILAS_DEL_BLOQUE_II, "B", indicador["pi"])
        assert hoja[f"H{fila}"].value in (r17.LOGRADO, r17.NO_LOGRADO)
        assert indicador["en_meta"] is (hoja[f"H{fila}"].value == r17.LOGRADO)


@then(parsers.re(r'el indicador (?P<pi>[0-9]+\.[0-9]+) trae pct_sobre_calificados (?P<logro>[0-9.]+), igual a '
                 r'round\(100 × (?P<celda_e>[A-Z][0-9]+), 1\), y pct_sobre_total (?P<total>[0-9.]+), igual a '
                 r'round\(100 × (?P<celda_q>[A-Z][0-9]+), 1\)'))
def _segundo_porcentaje_igual_al_r17(ctx: Escenario, pi: str, logro: str, celda_e: str, total: str,
                                     celda_q: str) -> None:
    indicador = _indicador(_unica_seccion(ctx), pi)
    [hoja] = ctx.extras["r17"].values()
    assert hoja[f"B{celda_e[1:]}"].value == pi and hoja[f"K{celda_q[1:]}"].value == pi
    assert indicador["pct_sobre_calificados"] == float(logro) == round(100 * hoja[celda_e].value, 1)
    assert indicador["pct_sobre_total"] == float(total) == round(100 * hoja[celda_q].value, 1)


# Entonces, la lectura no escribe

def _filas_por_tabla(ctx: Escenario) -> dict[str, int]:
    tablas = [fila[0] for fila in ctx.filas("SELECT format('%I.%I', table_schema, table_name) FROM information_schema.tables"
                                            " WHERE table_schema IN ('abet', 'acceso') AND table_type = 'BASE TABLE'")]
    return {tabla: int(ctx.uno(f"SELECT count(*) FROM {tabla}")) for tabla in tablas}


@then(parsers.re(r'(?P<lista>(?:abet|acceso)\.\w+(?:(?:, | y )(?:abet|acceso)\.\w+)*) conservan su número de filas'))
def _conservan_filas(ctx: Escenario, lista: str) -> None:
    antes, ahora = ctx.extras["filas_antes"], _filas_por_tabla(ctx)
    for tabla in _lista(lista):
        assert ahora[tabla] == antes[tabla], f"{tabla} cambió de {antes[tabla]} a {ahora[tabla]} filas"
    # Ninguna otra tabla de abet ni de acceso cambia tampoco (SC-006).
    assert ahora == antes


@then('las consultas de control Q01 a Q14 devuelven 0 filas')
def _q01_a_q14(ctx: Escenario) -> None:
    consultas = _conftest(ctx).consultas_de_control()
    # Q18 a Q21 llegan con la spec 008 (FR-021), y este escenario nombra Q01 a Q14.
    assert sorted(consultas) == [f"Q{n:02d}" for n in (*range(1, 15), *range(18, 22))]
    for nombre, consulta in ((n, c) for n, c in consultas.items() if n <= "Q14"):
        assert ctx.filas(consulta) == [], f"{nombre} devuelve filas"


# Entonces, el reemplazo del corte 2

@then(parsers.re(r'la sección 410 de "450002" trae el carga_id de B con (?P<cifras>.+)'))
def _trae_la_carga_b(ctx: Escenario, cifras: str) -> None:
    seccion = _seccion(ctx, "410")
    assert seccion["carga_id"] == ctx.extras["cargas"]["B"]
    assert [(i["pct_sobre_calificados"], i["logrados"], i["calificados"]) for i in seccion["indicadores"]] == _cifras(cifras)


@then(parsers.re(r'ningún indicador trae (?P<a>[0-9]+,[0-9] % \([0-9]+ de [0-9]+\)) ni (?P<b>[0-9]+,[0-9] % '
                 r'\([0-9]+ de [0-9]+\)), las cifras de A'))
def _ninguna_cifra_de_a(ctx: Escenario, a: str, b: str) -> None:
    cifras = {(i["pct_sobre_calificados"], i["logrados"], i["calificados"]) for _, i in _indicadores(ctx)}
    assert not cifras & set(_cifras(a) + _cifras(b)), cifras
    assert f'"carga_id":{ctx.extras["cargas"]["A"]},' not in ctx.respuesta.text


# Entonces, la marca provisional

@then(parsers.re(r'la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" trae (?P<campos>provisional .+)'))
def _seccion_trae(ctx: Escenario, numero: str, asignatura: str, campos: str) -> None:
    seccion = _seccion(ctx, numero, asignatura)
    pendientes = re.search(r"parametros_pendientes con (?P<lista>.+)$", campos)
    if pendientes is not None:
        assert set(seccion["parametros_pendientes"]) == set(_lista(pendientes["lista"])), seccion["parametros_pendientes"]
        campos = campos[:pendientes.start()].rstrip(", y")
    for campo, valor in _campos(campos).items():
        assert seccion[campo] == valor, (campo, seccion[campo], valor)


@then(parsers.re(r'sus tres indicadores traen meta_pct (?P<meta>[0-9.]+) y nivel_esperado (?P<nivel>[0-9]+)'))
def _tres_indicadores_con_meta(ctx: Escenario, meta: str, nivel: str) -> None:
    indicadores = _unica_seccion(ctx)["indicadores"]
    assert len(indicadores) == 3
    assert all((i["meta_pct"], i["nivel_esperado"]) == (float(meta), int(nivel)) for i in indicadores), indicadores


@then(parsers.re(r'(?P<pis>[0-9]+\.[0-9]+(?:, [0-9]+\.[0-9]+)* y [0-9]+\.[0-9]+) traen (?P<resto>.+)'))
def _pis_traen(ctx: Escenario, pis: str, resto: str) -> None:
    seccion = _unica_seccion(ctx)
    if CIFRA.match(resto):
        cifras = _cifras(resto)
        assert [(i["pct_sobre_calificados"], i["logrados"], i["calificados"])
                for i in (_indicador(seccion, pi) for pi in _lista(pis))] == cifras
        return
    for pi in _lista(pis):
        _comprobar_campos(_indicador(seccion, pi), _campos(resto))


# Entonces, el reparto por nivel

@then(parsers.re(r'el indicador (?P<p1>[0-9]+\.[0-9]+) trae estudiantes_por_nivel (?P<l1>\[[^\]]+\]), el '
                 r'(?P<p2>[0-9]+\.[0-9]+) trae (?P<l2>\[[^\]]+\]) y el (?P<p3>[0-9]+\.[0-9]+) trae (?P<l3>\[[^\]]+\])'))
def _repartos(ctx: Escenario, p1: str, l1: str, p2: str, l2: str, p3: str, l3: str) -> None:
    seccion = _unica_seccion(ctx)
    for pi, lista in ((p1, l1), (p2, l2), (p3, l3)):
        assert _indicador(seccion, pi)["estudiantes_por_nivel"] == _valor(lista)


@then(parsers.re(r'en cada indicador la suma de estudiantes_por_nivel es igual a calificados, (?P<calificados>[0-9]+), y '
                 r'la suma de sus dos últimos valores es igual a logrados, (?P<logrados>[0-9]+(?:, [0-9]+)* y [0-9]+)'))
def _sumas_del_reparto(ctx: Escenario, calificados: str, logrados: str) -> None:
    indicadores = _unica_seccion(ctx)["indicadores"]
    assert [sum(i["estudiantes_por_nivel"]) for i in indicadores] == [int(calificados)] * len(indicadores)
    assert all(sum(i["estudiantes_por_nivel"]) == i["calificados"] for i in indicadores)
    assert [sum(i["estudiantes_por_nivel"][2:]) for i in indicadores] == [int(x) for x in _lista(logrados)]
    assert all(sum(i["estudiantes_por_nivel"][2:]) == i["logrados"] for i in indicadores)


# Entonces, el coordinador

@then(parsers.re(r'la API responde 200 con (?P<n>[0-9]+) secciones, en el orden (?P<a1>[0-9]+), (?P<a2>[0-9]+) y '
                 r'(?P<a3>[0-9]+) de "(?P<asignatura_a>[0-9]+)" y (?P<b1>[0-9]+) y (?P<b2>[0-9]+) de '
                 r'"(?P<asignatura_b>[0-9]+)", y (?P<m>[0-9]+) indicadores, (?P<so5>[0-9]+) del SO 5 y (?P<so2>[0-9]+) '
                 r'del SO 2'))
def _secciones_del_coordinador(ctx: Escenario, n: str, a1: str, a2: str, a3: str, asignatura_a: str, b1: str, b2: str,
                               asignatura_b: str, m: str, so5: str, so2: str) -> None:
    cuerpo = _cuerpo(ctx)
    assert [(s["asignatura"]["codigo"], s["numero"]) for s in cuerpo["secciones"]] == [
        (asignatura_a, a1), (asignatura_a, a2), (asignatura_a, a3), (asignatura_b, b1), (asignatura_b, b2)]
    assert len(cuerpo["secciones"]) == int(n)
    indicadores = [i for _, i in _indicadores(ctx)]
    assert (len(indicadores), sum(i["so"] == 5 for i in indicadores), sum(i["so"] == 2 for i in indicadores)) == (
        int(m), int(so5), int(so2))


@then('la respuesta no trae ningún correo ni el campo subida_por')
def _sin_correos(ctx: Escenario) -> None:
    assert "@" not in ctx.respuesta.text and "subida_por" not in ctx.respuesta.text


@then(parsers.re(r'acceso\.docente_seccion sigue sin filas de "(?P<correo>[^"]+)"'))
def _sin_filas_de(ctx: Escenario, correo: str) -> None:
    assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion d JOIN acceso.usuario_autorizado u USING (usuario_id)"
                   " WHERE u.correo = %s", correo) == 0
