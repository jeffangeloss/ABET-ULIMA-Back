"""Pasos de reemplazo_y_cargas.feature (US-18 y US-19), ejecutables con pytest-bdd en español (T087).

El .feature manda. Ningún paso cambia una cifra, un mensaje ni un título para que el escenario pase, y cada
«Entonces» se comprueba contra la respuesta de la API o contra la base, sin dobles del sistema bajo prueba. Las
cargas de partida se suben por la API con la sesión de quien el escenario nombra, así que pasan por las mismas
reglas que la carga que se prueba, y sus identificadores se capturan de la respuesta y se nombran con la letra
del escenario (A, B, C y D) en ctx.extras["cargas"], porque una transacción deshecha también consume números.

Los dos escenarios que nombran la base sin la API («La base impide dos cargas publicadas en la misma sección» y
«La base no deja que una carga reemplace a otra de otra sección») escriben con una conexión directa del rol de la
aplicación, el mismo de Neon, dentro de una transacción que se deshace, así que no dejan filas.

Los pasos que nombran la pantalla P3 o P5 comprueban aquí la respuesta de la API que la pantalla muestra y
registran con la propiedad «delegado_a_vitest» la prueba de Vitest del Front que comprueba la pantalla, como
test_acceso_feature.py. Un paso de pantalla sin su prueba anotada hace fallar el escenario.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import sys
from pathlib import Path
from typing import Any

import psycopg
from psycopg.conninfo import make_conninfo
from pytest_bdd import given, parsers, scenarios, then, when

A = sys.modules["api_de_prueba"]
Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
CONTROLES = RAIZ / "db" / "plataforma" / "neon" / "controles_neon.sql"
ASIGNATURA = "450002"
SIN_ALCANCE = {"detail": "La sección no está a su cargo."}
CON_CARGA_410 = "La sección 410 ya tiene una carga publicada. No se cargó el archivo."
TODAS_RECHAZADAS = 'una copia de "sintetico_20262_450002_410.xlsx" con un 5 en la columna 5.2 de las 11 filas de datos'
CAMPOS_DE_LA_LISTA = {
    "carga_id", "estado", "seccion", "nombre_archivo", "sha256_corto", "filas_leidas", "filas_aceptadas",
    "filas_rechazadas", "motivo", "reemplaza_carga_id", "reemplazada_por", "subida_por", "iniciada_en", "terminada_en",
}

scenarios("specs/001-mvp-carga-r17/aceptacion/reemplazo_y_cargas.feature")


# Pasos de pantalla delegados a Vitest

VITEST_P3 = "front/tests/pantallas/SubirExport.test.tsx › P3 Subir export › "
VITEST_P5 = "front/tests/pantallas/Cargas.test.tsx › P5 Cargas › "
CUBIERTO_POR_VITEST = {
    "la pantalla P3 pregunta": VITEST_P3 + "un 409 de la sección con carga publicada pregunta si se reemplaza y reenvía "
                                           "el archivo con reemplaza",
    "la pantalla P3 muestra": VITEST_P3 + "en el reemplazo, el 422 del archivo que no abre muestra que la carga "
                                          "publicada no cambió",
    "se abre la pantalla P5": VITEST_P5 + "no muestra nombres de estudiantes, valores leídos ni rutas locales",
    "ningún valor de las columnas Last Name ni First Name": VITEST_P5 + "no muestra nombres de estudiantes, valores "
                                                                        "leídos ni rutas locales",
}


def _delegar(ctx: Escenario, texto: str) -> None:
    """Deja constancia del paso de pantalla y de la prueba de Vitest del Front que lo comprueba."""
    pruebas = [prueba for inicio, prueba in CUBIERTO_POR_VITEST.items() if texto.startswith(inicio)]
    assert len(pruebas) == 1, f"el paso de pantalla «{texto}» no tiene una prueba de Vitest anotada"
    ctx.request.node.user_properties.append(("delegado_a_vitest", f"{texto} → {pruebas[0]}"))


# Ayudas

def _cargas(ctx: Escenario) -> dict[str, int]:
    return ctx.extras.setdefault("cargas", {})


def _id(ctx: Escenario, letra: str) -> int:
    assert letra in _cargas(ctx), f"el escenario todavía no tiene la carga {letra}"
    return _cargas(ctx)[letra]


def _estado(ctx: Escenario, letra: str) -> str:
    return str(ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", _id(ctx, letra)))


def _archivo(ctx: Escenario, que: str) -> tuple[bytes, str]:
    """Bytes y nombre de un export que nombra el escenario, de tests/datos_inventados/ o armado en memoria."""
    if que.startswith("una copia de"):
        return ctx.copia_de(que)
    return ctx.de_inventados(que), que


def _subir(ctx: Escenario, correo: str, numero: str, contenido: bytes, nombre: str,
           reemplaza: int | None = None) -> Any:
    """POST del export con la sesión de correo y, si llega, el parámetro reemplaza."""
    params = {"reemplaza": str(reemplaza)} if reemplaza is not None else None
    return ctx.subir(correo, contenido, nombre, numero, ASIGNATURA, params=params)


def _publicada_en(ctx: Escenario, numero: str) -> int | None:
    fila = ctx.filas("SELECT carga_id FROM abet.carga WHERE seccion_id = %s AND estado = 'PUBLICADA'",
                     ctx.seccion_id(numero))
    return int(fila[0][0]) if fila else None


def _subir_o_reemplazar(ctx: Escenario, letra: str, correo: str, numero: str, que: str) -> Any:
    """Sube el export en la sección y, si la sección ya tiene una carga publicada, la reemplaza con él."""
    contenido, nombre = _archivo(ctx, que)
    respuesta = _subir(ctx, correo, numero, contenido, nombre, reemplaza=_publicada_en(ctx, numero))
    assert respuesta.status_code == 201, respuesta.text
    _cargas(ctx)[letra] = respuesta.json()["carga_id"]
    ctx.extras.setdefault("archivos", {})[letra] = (contenido, nombre)
    return respuesta


def _cargas_de_us19(ctx: Escenario, con_d: bool) -> None:
    """Las cargas A, B y C de la 410, subidas por docente410 en ese orden, y la D de la 411, subida después de C.

    A es el export de la 411 subido en la 410, que queda RECHAZADA con SECCION_NO_COINCIDE. B es el export con el
    error, que se publica porque A no lo impide, y C es el export correcto, que reemplaza a B. D es el mismo export
    de la 411 subido en la 411 por docente411, que se publica con el archivo_id de A (BR-CARGA-09).
    """
    _subir_o_reemplazar(ctx, "A", A.DOCENTE_410, "410", A.EXPORT_411)
    _subir_o_reemplazar(ctx, "B", A.DOCENTE_410, "410", A.CON_ERROR)
    _subir_o_reemplazar(ctx, "C", A.DOCENTE_410, "410", A.CORRECTO)
    if con_d:
        _subir_o_reemplazar(ctx, "D", A.DOCENTE_411, "411", A.EXPORT_411)
    estados = {letra: _estado(ctx, letra) for letra in _cargas(ctx)}
    esperados = {"A": "RECHAZADA", "B": "REEMPLAZADA", "C": "PUBLICADA"} | ({"D": "PUBLICADA"} if con_d else {})
    assert estados == esperados


def _usuario(ctx: Escenario) -> str:
    correo = ctx.extras.get("usuario")
    assert correo is not None, "el escenario no inició la sesión de nadie"
    return correo


def _directa(ctx: Escenario, autocommit: bool) -> psycopg.Connection:
    """Conexión directa con el rol de la aplicación, que la pila del escenario cierra al terminar."""
    conexion = ctx.pila.enter_context(psycopg.connect(
        make_conninfo(ctx.api.base.conexion, user=ctx.api.base.rol_app), autocommit=autocommit))
    assert conexion.execute("SELECT current_user").fetchone()[0] == ctx.api.base.rol_app
    return conexion


def _carga_directa(ctx: Escenario, conexion: psycopg.Connection, numero: str, reemplaza: int) -> int:
    """Inserta, con el rol de la aplicación, un archivo inventado y una carga EN_CURSO de la sección que reemplaza a otra."""
    seccion = ctx.seccion_id(numero)
    carrera, reglas = ctx.filas(
        "SELECT (SELECT pm.carrera_id FROM abet.plan_medicion pm JOIN abet.seccion s"
        " ON s.asignatura_id = pm.asignatura_id AND s.periodo_id = pm.periodo_id WHERE s.seccion_id = %s LIMIT 1),"
        " (SELECT conjunto_reglas_id FROM abet.conjunto_reglas WHERE version = %s AND carrera_id = (SELECT carrera_id FROM abet.carrera WHERE codigo = 'AMB'))", seccion, A.REGLAS)[0]
    archivo = conexion.execute(
        "INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)"
        " VALUES (%s, 'archivo_de_prueba.xlsx', 'Hoja_de_prueba', 11) RETURNING archivo_id",
        (secrets.token_hex(32),)).fetchone()[0]
    return int(conexion.execute(
        "INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id,"
        " programa_version, reemplaza_carga_id) VALUES (%s, %s, 11, %s, %s, 'prueba', %s) RETURNING carga_id",
        (seccion, archivo, carrera, reglas, reemplaza)).fetchone()[0])


def _lista(ctx: Escenario) -> list[dict[str, Any]]:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    cuerpo = ctx.respuesta.json()
    assert isinstance(cuerpo, list)
    return cuerpo


def _letras(ctx: Escenario, lista: list[dict[str, Any]]) -> list[str]:
    por_id = {carga_id: letra for letra, carga_id in _cargas(ctx).items()}
    return [por_id.get(item["carga_id"], f"ajena {item['carga_id']}") for item in lista]


def _nombres_de_los_exports(ctx: Escenario) -> set[str]:
    """Apellidos y nombres inventados de las columnas Last Name y First Name de los exports del escenario."""
    nombres: set[str] = set()
    for contenido, _ in ctx.extras["archivos"].values():
        export = ctx.generador.leer_export(contenido)
        for fila in range(2, len(export.filas) + 2):
            for columna in ("Last Name", "First Name"):
                valor = export.valor(fila, columna)
                if valor:
                    nombres.add(str(valor))
    assert nombres, "los exports del escenario no traen nombres que buscar"
    return nombres


# Antecedentes

@given(parsers.re(r'la base con los datos inventados de 2026-2 de periodo_2026_2_inventado\.sql'))
def _base(ctx: Escenario) -> None:
    ctx.crear_base("periodo")
    assert ctx.uno("SHOW server_version_num").startswith("18"), "la base desechable no es PostgreSQL 18"
    assert ctx.uno("SELECT count(*) FROM abet.periodo WHERE codigo = '2026-2'") == 1


@given(parsers.re(r'"(?P<correo>[^"]+)" activo con rol "(?P<rol>[A-Z]+)" y sin secciones en acceso\.docente_seccion'))
def _sin_secciones(ctx: Escenario, correo: str, rol: str) -> None:
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, True)]
    assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion WHERE usuario_id = %s", ctx.usuario_id(correo)) == 0


@given(parsers.re(r'"(?P<correo>[^"]+)" activo con rol "(?P<rol>[A-Z]+)" y la sección (?P<numero>[0-9]+) de '
                  r'(?P<asignatura>[0-9]+) en (?P<periodo>[0-9]{4}-[0-2])'))
def _con_seccion(ctx: Escenario, correo: str, rol: str, numero: str, asignatura: str, periodo: str) -> None:
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, True)]
    assert periodo == A.PERIODO
    assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion WHERE usuario_id = %s AND seccion_id = %s",
                   ctx.usuario_id(correo), ctx.seccion_id(numero, asignatura)) == 1


@given(parsers.re(r'la API configurada con PERIODO_VIGENTE "(?P<periodo>[^"]+)", CONJUNTO_REGLAS "(?P<reglas>[^"]+)" '
                  r'y GUARDIA_DATOS_INVENTADOS "(?P<guardia>[01])"'))
def _api(ctx: Escenario, periodo: str, reglas: str, guardia: str) -> None:
    ctx.configurar_api(periodo, reglas, guardia)
    ctx.api.cliente()
    assert ctx.api.ajustes.carga.guardia_datos_inventados is (guardia == "1")


@given(parsers.re(r'los exports de prueba en tests/datos_inventados/'))
def _exports(ctx: Escenario) -> None:
    for nombre in (A.CORRECTO, A.CON_ERROR, A.EXPORT_411, "danado_410.xlsx"):
        assert (RAIZ / "tests" / "datos_inventados" / nombre).is_file(), nombre


@given(parsers.re(r'que "(?P<correo>[^"]+)" tiene la sesión iniciada'))
def _sesion(ctx: Escenario, correo: str) -> None:
    ctx.sesion(correo)
    ctx.extras["usuario"] = correo


# Dado, cargas de partida subidas por la API

@given(parsers.re(r'la carga (?P<letra>[A-D]) PUBLICADA de "(?P<nombre>[^"]+)" en la sección (?P<numero>[0-9]+)'
                  r'(?: con (?P<leidas>[0-9]+) filas leídas, (?P<aceptadas>[0-9]+) aceptadas, (?P<rechazadas>[0-9]+) '
                  r'rechazadas? y (?P<mediciones>[0-9]+) mediciones)?'))
def _publicada(ctx: Escenario, letra: str, nombre: str, numero: str, leidas: str | None, aceptadas: str | None,
               rechazadas: str | None, mediciones: str | None) -> None:
    respuesta = _subir_o_reemplazar(ctx, letra, A.DOCENTE_410, numero, nombre)
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "PUBLICADA"
    if leidas is not None:
        assert (cuerpo["filas_leidas"], cuerpo["filas_aceptadas"], cuerpo["filas_rechazadas"]) == (
            int(leidas), int(aceptadas), int(rechazadas))
        assert ctx.cuenta("medicion", "carga_id = %s", _id(ctx, letra)) == int(mediciones)


@given(parsers.re(r'la carga (?P<letra>[A-D]) PUBLICADA en la sección (?P<numero>[0-9]+)'))
def _publicada_sin_archivo(ctx: Escenario, letra: str, numero: str) -> None:
    _publicada(ctx, letra, A.CORRECTO, numero, None, None, None, None)


@given(parsers.re(r'una carga RECHAZADA de un reemplazo fallido de A, con reemplaza_carga_id nulo'))
def _reemplazo_fallido(ctx: Escenario) -> None:
    contenido, nombre = _archivo(ctx, TODAS_RECHAZADAS)
    respuesta = _subir(ctx, A.DOCENTE_410, "410", contenido, nombre, reemplaza=_id(ctx, "A"))
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "RECHAZADA", respuesta.text
    _cargas(ctx)["fallida"] = respuesta.json()["carga_id"]
    assert ctx.uno("SELECT reemplaza_carga_id FROM abet.carga WHERE carga_id = %s", _id(ctx, "fallida")) is None
    assert _estado(ctx, "A") == "PUBLICADA"


@given(parsers.re(r'la carga A REEMPLAZADA de "(?P<a>[^"]+)" y la carga B PUBLICADA de "(?P<b>[^"]+)" que la '
                  r'reemplaza en la sección 410'))
def _a_reemplazada_por_b(ctx: Escenario, a: str, b: str) -> None:
    _subir_o_reemplazar(ctx, "A", A.DOCENTE_410, "410", a)
    _subir_o_reemplazar(ctx, "B", A.DOCENTE_410, "410", b)
    assert (_estado(ctx, "A"), _estado(ctx, "B")) == ("REEMPLAZADA", "PUBLICADA")


@given(parsers.re(r'la carga A REEMPLAZADA y la carga B PUBLICADA que la reemplaza en la sección 410'))
def _a_reemplazada_sin_archivos(ctx: Escenario) -> None:
    """A es el export correcto y B el export con el error, para que el archivo pedido después no sea el de B."""
    _a_reemplazada_por_b(ctx, A.CORRECTO, A.CON_ERROR)


@given(parsers.re(r'la carga D PUBLICADA del export inventado de la 411 en la sección 411, subida por "(?P<correo>[^"]+)"'))
def _d_publicada(ctx: Escenario, correo: str) -> None:
    respuesta = _subir_o_reemplazar(ctx, "D", correo, "411", A.EXPORT_411)
    assert respuesta.json()["estado"] == "PUBLICADA"


@given(parsers.re(r'la carga D PUBLICADA de la sección 411 de 450002 en 2026-2'))
def _d_publicada_por_docente411(ctx: Escenario) -> None:
    _d_publicada(ctx, A.DOCENTE_411)


@given(parsers.re(r'que la sección 410 tiene estas cargas, subidas por "(?P<correo>[^"]+)" en este orden'))
def _tabla_de_cargas(ctx: Escenario, correo: str, datatable: list[list[str]]) -> None:
    assert datatable[0] == ["carga", "archivo", "estado", "leídas", "aceptadas", "rechazadas"]
    assert correo == A.DOCENTE_410
    for letra, archivo, _, _, _, _ in datatable[1:]:
        _subir_o_reemplazar(ctx, letra, correo, "410", archivo)
    for letra, _, estado, leidas, aceptadas, rechazadas in datatable[1:]:
        fila = ctx.filas("SELECT estado, filas_leidas, filas_aceptadas, filas_rechazadas FROM abet.carga"
                         " WHERE carga_id = %s", _id(ctx, letra))
        assert fila == [(estado, int(leidas), int(aceptadas), int(rechazadas))], (letra, fila)


@given(parsers.re(r'que la sección 411 tiene la carga D PUBLICADA del export inventado de la 411, subida por '
                  r'"(?P<correo>[^"]+)" después de C'))
def _d_despues_de_c(ctx: Escenario, correo: str) -> None:
    assert "C" in _cargas(ctx)
    _d_publicada(ctx, correo)


@given(parsers.re(r'las cargas A, B y C de la sección 410 y la carga D de la sección 411'))
def _cuatro_cargas(ctx: Escenario) -> None:
    _cargas_de_us19(ctx, con_d=True)


@given(parsers.re(r'las cargas A, B y C de la sección 410'))
def _tres_cargas(ctx: Escenario) -> None:
    _cargas_de_us19(ctx, con_d=False)


# Dado y Cuando, la base sin la API

@given(parsers.re(r'una transacción abierta que inserta una carga B EN_CURSO de la misma sección con '
                  r'reemplaza_carga_id igual a A'))
def _transaccion_abierta(ctx: Escenario) -> None:
    conexion = _directa(ctx, autocommit=False)
    _cargas(ctx)["B"] = _carga_directa(ctx, conexion, "410", _id(ctx, "A"))
    ctx.extras["transaccion"] = conexion


@when(parsers.re(r'un programa defectuoso intenta pasar B a "PUBLICADA" en esa transacción sin marcar antes A como '
                 r'"REEMPLAZADA"'))
def _publica_sin_marcar(ctx: Escenario) -> None:
    conexion = ctx.extras["transaccion"]
    ctx.error_directo = None
    try:
        conexion.execute("UPDATE abet.carga SET estado = 'PUBLICADA', filas_leidas = 11, filas_aceptadas = 11,"
                         " filas_rechazadas = 0, terminada_en = clock_timestamp() WHERE carga_id = %s",
                         (_id(ctx, "B"),))
    except psycopg.Error as falla:
        ctx.error_directo = falla
    conexion.rollback()


@when(parsers.re(r'la aplicación intenta registrar una carga de la sección 410 con reemplaza_carga_id igual a D'))
def _registra_carga_ajena(ctx: Escenario) -> None:
    conexion = _directa(ctx, autocommit=True)
    ctx.antes = ctx.api.conteos()
    ctx.error_directo = None
    try:
        with conexion.transaction():
            _carga_directa(ctx, conexion, "410", _id(ctx, "D"))
    except psycopg.Error as falla:
        ctx.error_directo = falla


# Cuando, peticiones a la API

@when(parsers.re(r'se envía POST /api/secciones/\{sección (?P<numero>[0-9]+)\}/cargas\?reemplaza=\{(?P<letra>[A-D])\} '
                 r'con (?P<que>el archivo "[^"]+"|un archivo \.xlsx dañado que no abre como zip|un export de la 410 que '
                 r'trae un 5 en la columna 5\.2 de las 11 filas|un export de la 411)'))
def _reemplaza(ctx: Escenario, numero: str, letra: str, que: str) -> None:
    if que.startswith("el archivo"):
        contenido, nombre = _archivo(ctx, que.split('"')[1])
    elif que.startswith("un archivo .xlsx dañado"):
        contenido, nombre = ctx.de_inventados("danado_410.xlsx"), "danado_410.xlsx"
    elif que.startswith("un export de la 410"):
        contenido, nombre = _archivo(ctx, TODAS_RECHAZADAS)
    else:
        contenido, nombre = ctx.de_inventados(A.EXPORT_411), A.EXPORT_411
    _subir(ctx, _usuario(ctx), numero, contenido, nombre, reemplaza=_id(ctx, letra))


@when(parsers.re(r'se envía POST /api/secciones/\{sección (?P<numero>[0-9]+)\}/cargas sin el parámetro reemplaza, con el '
                 r'archivo "(?P<nombre>[^"]+)"'))
def _sube_sin_reemplazo(ctx: Escenario, numero: str, nombre: str) -> None:
    contenido, nombre = _archivo(ctx, nombre)
    _subir(ctx, _usuario(ctx), numero, contenido, nombre)


@when(parsers.re(r'se envía GET /api/cargas(?:\?seccion_id=\{sección (?P<numero>[0-9]+)\})?'))
def _lista_de_cargas(ctx: Escenario, numero: str | None) -> None:
    params = {"seccion_id": str(ctx.seccion_id(numero))} if numero is not None else None
    ctx.respuesta = ctx.sesion(_usuario(ctx)).get("/api/cargas", params=params)


@when(parsers.re(r'se envía GET /api/cargas/\{(?P<letra>[A-D])\}'))
def _constancia(ctx: Escenario, letra: str) -> None:
    ctx.respuesta = ctx.sesion(_usuario(ctx)).get(f"/api/cargas/{_id(ctx, letra)}")


@when(parsers.re(r'(?P<texto>se envía GET /api/cargas y se abre la pantalla P5 «Cargas»)'))
def _lista_y_p5(ctx: Escenario, texto: str) -> None:
    _lista_de_cargas(ctx, None)
    _delegar(ctx, texto.removeprefix("se envía GET /api/cargas y "))


# Entonces, las respuestas de la API

@then(parsers.re(r'la API responde (?P<codigo>[0-9]+)'))
def _responde(ctx: Escenario, codigo: str) -> None:
    assert ctx.respuesta.status_code == int(codigo), ctx.respuesta.text
    if int(codigo) == 403:
        assert ctx.respuesta.json() == SIN_ALCANCE


@then(parsers.re(r'la API responde 201 con la constancia de una carga(?: (?P<letra>[A-D]))? en estado "(?P<estado>[A-Z]+)"'))
def _responde_201(ctx: Escenario, letra: str | None, estado: str) -> None:
    assert ctx.respuesta.status_code == 201, ctx.respuesta.text
    cuerpo = ctx.cuerpo()
    assert cuerpo["estado"] == estado
    leida = ctx.sesion(_usuario(ctx)).get(f"/api/cargas/{cuerpo['carga_id']}")
    assert leida.status_code == 200 and leida.json() == cuerpo, "la constancia leída después no es la de la respuesta"
    _cargas(ctx)[letra or "nueva"] = cuerpo["carga_id"]


@then(parsers.re(r'la API responde 201 con una carga (?:(?P<letra>[A-D]) )?en estado "(?P<estado>[A-Z]+)"'
                 r'(?:, el mismo archivo_id de la carga (?P<archivo_de>[A-D]))? y reemplaza_carga_id igual a '
                 r'(?P<reemplazada>[A-D])'))
def _responde_201_con_reemplazo(ctx: Escenario, letra: str | None, estado: str, archivo_de: str | None,
                                reemplazada: str) -> None:
    _responde_201(ctx, letra, estado)
    nueva = ctx.cuerpo()["carga_id"]
    assert ctx.cuerpo()["reemplaza_carga_id"] == _id(ctx, reemplazada)
    assert ctx.uno("SELECT reemplaza_carga_id FROM abet.carga WHERE carga_id = %s", nueva) == _id(ctx, reemplazada)
    if archivo_de is not None:
        archivos = ctx.filas("SELECT carga_id, archivo_id FROM abet.carga WHERE carga_id IN (%s, %s)",
                             nueva, _id(ctx, archivo_de))
        assert len({archivo for _, archivo in archivos}) == 1, archivos


@then(parsers.re(r'la API responde 200 con la constancia de la carga (?P<letra>[A-D])'))
def _responde_200_con_constancia(ctx: Escenario, letra: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    cuerpo = dict(ctx.cuerpo())
    assert cuerpo["carga_id"] == _id(ctx, letra)
    aviso = cuerpo.pop("aviso", None)
    assert aviso is not None, "la respuesta del mismo archivo no trae el aviso"
    leida = ctx.sesion(_usuario(ctx)).get(f"/api/cargas/{_id(ctx, letra)}")
    assert leida.status_code == 200 and leida.json() == cuerpo


@then(parsers.re(r'el cuerpo trae el aviso "(?P<aviso>[^"]+)"'))
def _cuerpo_con_aviso(ctx: Escenario, aviso: str) -> None:
    assert ctx.cuerpo()["aviso"] == aviso


@then(parsers.re(r'(?P<texto>la pantalla P3 pregunta "La sección (?P<numero>[0-9]+) ya tiene una carga publicada\. '
                 r'¿Desea reemplazarla\?")'))
def _p3_pregunta(ctx: Escenario, texto: str, numero: str) -> None:
    """La API responde lo que P3 necesita para preguntar, el 409 de la sección y el carga_id de la carga publicada."""
    assert ctx.respuesta.status_code == 409
    assert ctx.cuerpo() == {"detail": f"La sección {numero} ya tiene una carga publicada. No se cargó el archivo.",
                            "carga_publicada": _publicada_en(ctx, numero)}
    _delegar(ctx, texto)


@then(parsers.re(r'(?P<texto>la pantalla P3 muestra "(?P<mensaje>[^"]+)")'))
def _p3_muestra(ctx: Escenario, texto: str, mensaje: str) -> None:
    """P3 muestra el detail de la API sin reescribirlo, así que aquí se comprueba ese detail."""
    assert ctx.cuerpo() == {"detail": mensaje}
    _delegar(ctx, texto)


# Entonces, lo que queda en la base

@then(parsers.re(r'la carga (?P<letra>[A-D]) (?:sigue en estado|queda en estado|sigue) "(?P<estado>[A-Z]+)"'))
def _carga_en_estado(ctx: Escenario, letra: str, estado: str) -> None:
    assert _estado(ctx, letra) == estado


@then(parsers.re(r'la carga A queda en estado "REEMPLAZADA" y conserva sus (?P<mediciones>[0-9]+) mediciones y sus '
                 r'(?P<rechazos>[0-9]+) filas de abet\.rechazo_fila, NIVEL_FUERA_DE_ESCALA en la fila 3 del PI 5\.2 y '
                 r'PUNTAJE_MAXIMO_DISTINTO en el PI 5\.3'))
def _a_reemplazada_conserva(ctx: Escenario, mediciones: str, rechazos: str) -> None:
    carga = _id(ctx, "A")
    assert _estado(ctx, "A") == "REEMPLAZADA"
    assert ctx.cuenta("medicion", "carga_id = %s", carga) == int(mediciones)
    filas = ctx.filas(
        "SELECT r.motivo, r.efecto, r.fila_origen, cc.pi_codigo FROM abet.rechazo_fila r"
        " LEFT JOIN abet.carga_columna cc ON cc.carga_columna_id = r.carga_columna_id"
        " WHERE r.carga_id = %s ORDER BY r.motivo", carga)
    assert len(filas) == int(rechazos)
    assert filas == [("NIVEL_FUERA_DE_ESCALA", "RECHAZA_FILA", 3, "5.2"), ("PUNTAJE_MAXIMO_DISTINTO", "AVISO", None, "5.3")]


@then(parsers.re(r'la carga B tiene filas_leidas (?P<leidas>[0-9]+), filas_aceptadas (?P<aceptadas>[0-9]+), '
                 r'filas_rechazadas (?P<rechazadas>[0-9]+), (?P<mediciones>[0-9]+) mediciones y reemplaza_carga_id '
                 r'igual a A'))
def _b_reemplaza_a(ctx: Escenario, leidas: str, aceptadas: str, rechazadas: str, mediciones: str) -> None:
    fila = ctx.filas("SELECT filas_leidas, filas_aceptadas, filas_rechazadas, reemplaza_carga_id FROM abet.carga"
                     " WHERE carga_id = %s", _id(ctx, "B"))
    assert fila == [(int(leidas), int(aceptadas), int(rechazadas), _id(ctx, "A"))]
    assert ctx.cuenta("medicion", "carga_id = %s", _id(ctx, "B")) == int(mediciones)


@then(parsers.re(r'la carga B tiene subida_por igual al usuario_id de "(?P<correo>[^"]+)"'))
def _b_subida_por(ctx: Escenario, correo: str) -> None:
    assert ctx.uno("SELECT subida_por FROM abet.carga WHERE carga_id = %s", _id(ctx, "B")) == ctx.usuario_id(correo)
    assert ctx.cuerpo()["subida_por"] == correo


@then(parsers.re(r'la sección (?P<numero>[0-9]+) tiene 1 sola carga en estado "PUBLICADA"'))
def _una_publicada(ctx: Escenario, numero: str) -> None:
    assert ctx.cuenta("carga", "seccion_id = %s AND estado = 'PUBLICADA'", ctx.seccion_id(numero)) == 1


@then(parsers.re(r'abet\.v_r17_por_pi devuelve solo filas de la carga B, con (?P<p1>[0-9]+,[0-9]) en el PI 5\.1, '
                 r'(?P<p2>[0-9]+,[0-9]) en el PI 5\.2 y (?P<p3>[0-9]+,[0-9]) en el PI 5\.3'))
def _r17_de_b(ctx: Escenario, p1: str, p2: str, p3: str) -> None:
    filas = ctx.filas("SELECT v.carga_id, v.pi, v.pct_logro_sobre_calificados FROM abet.v_r17_por_pi v"
                      " WHERE v.carga_id IN (SELECT carga_id FROM abet.carga WHERE seccion_id = %s) ORDER BY v.pi",
                      ctx.seccion_id("410"))
    assert {carga for carga, _, _ in filas} == {_id(ctx, "B")}
    assert [(pi, str(pct)) for _, pi, pct in filas] == [("5.1", p1.replace(",", ".")), ("5.2", p2.replace(",", ".")),
                                                        ("5.3", p3.replace(",", "."))]


@then(parsers.re(r'cada una de las consultas de control (?P<lista>Q[0-9]{2}(?:, Q[0-9]{2})* y Q[0-9]{2}) devuelve 0 filas'))
def _cada_control_en_cero(ctx: Escenario, lista: str) -> None:
    consultas = _consultas_de_control()
    # Q18 a Q21 llegan con la spec 008 (FR-021), y estos escenarios nombran solo consultas de Q01 a Q14.
    assert sorted(consultas) == [f"Q{n:02d}" for n in (*range(1, 15), *range(18, 22))]
    for nombre in lista.replace(" y ", ", ").split(", "):
        assert ctx.filas(consultas[nombre]) == [], f"{nombre} devuelve filas"


def _consultas_de_control() -> dict[str, str]:
    """Q01 a Q14 de controles_neon.sql, con la misma lectura que el conftest.py de esta carpeta."""
    texto = CONTROLES.read_text(encoding="utf-8")
    bloques = re.findall(r"\\echo '(Q[0-9]{2})\.[^\n]*\n(.*?);\n\\set q[0-9]{2} :ROW_COUNT", texto, flags=re.S)
    return {nombre: consulta.strip() for nombre, consulta in bloques}


@then(parsers.re(r'esa carga tiene filas_leidas (?P<leidas>[0-9]+), filas_aceptadas (?P<aceptadas>[0-9]+) y '
                 r'filas_rechazadas (?P<rechazadas>[0-9]+)'))
def _esa_carga(ctx: Escenario, leidas: str, aceptadas: str, rechazadas: str) -> None:
    fila = ctx.filas("SELECT filas_leidas, filas_aceptadas, filas_rechazadas FROM abet.carga WHERE carga_id = %s",
                     ctx.cuerpo()["carga_id"])
    assert fila == [(int(leidas), int(aceptadas), int(rechazadas))]


@then(parsers.re(r'su reemplaza_carga_id es nulo desde el INSERT, sin ningún UPDATE de esa columna'))
def _sin_reemplazo(ctx: Escenario) -> None:
    carga = ctx.cuerpo()["carga_id"]
    assert ctx.uno("SELECT reemplaza_carga_id FROM abet.carga WHERE carga_id = %s", carga) is None
    assert ctx.cuerpo()["reemplaza_carga_id"] is None
    # El rol de la aplicación no tiene UPDATE de esa columna, así que ningún programa con ese rol la pudo cambiar.
    assert ctx.uno("SELECT has_column_privilege(%s, 'abet.carga', 'reemplaza_carga_id', 'UPDATE')",
                   ctx.api.base.rol_app) is False


@then(parsers.re(r'la base no rechaza esa carga por "uq_carga_reemplaza"'))
def _sin_choque_de_reemplazo(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 201
    assert ctx.filas("SELECT carga_id FROM abet.carga WHERE reemplaza_carga_id = %s", _id(ctx, "A")) == [
        (ctx.cuerpo()["carga_id"],)]
    assert ctx.uno("SELECT reemplaza_carga_id FROM abet.carga WHERE carga_id = %s", _id(ctx, "fallida")) is None


@then(parsers.re(r'abet\.archivo_origen sigue con 1 sola fila para la huella de "(?P<nombre>[^"]+)"'))
def _una_fila_por_huella(ctx: Escenario, nombre: str) -> None:
    huella = hashlib.sha256(ctx.de_inventados(nombre)).hexdigest()
    assert ctx.cuenta("archivo_origen", "sha256 = %s", huella) == 1


@then(parsers.re(r'la carga A sigue en estado "REEMPLAZADA" y la carga B pasa a "REEMPLAZADA"'))
def _a_y_b_reemplazadas(ctx: Escenario) -> None:
    assert (_estado(ctx, "A"), _estado(ctx, "B")) == ("REEMPLAZADA", "REEMPLAZADA")


@then(parsers.re(r'la base rechaza (?:el cambio|la fila) por (?:la restricción )?"(?P<restriccion>[a-z0-9_]+)"'))
def _base_rechaza(ctx: Escenario, restriccion: str) -> None:
    assert ctx.error_directo is not None, "la base aceptó la sentencia"
    assert ctx.error_directo.diag.constraint_name == restriccion, ctx.error_directo.diag.constraint_name


@then(parsers.re(r'la transacción completa se deshace, así que B no existe y A sigue "PUBLICADA"'))
def _transaccion_deshecha(ctx: Escenario) -> None:
    assert ctx.cuenta("carga", "carga_id = %s", _id(ctx, "B")) == 0
    assert _estado(ctx, "A") == "PUBLICADA"
    assert ctx.cuenta("archivo_origen", "nombre_archivo = 'archivo_de_prueba.xlsx'") == 0


# Entonces, la lista de cargas y la constancia

@then(parsers.re(r'la API responde 200 con (?P<n>[0-9]+) cargas en el orden (?P<orden>[A-D](?:, [A-D])* y [A-D])'))
def _lista_en_orden(ctx: Escenario, n: str, orden: str) -> None:
    lista = _lista(ctx)
    assert len(lista) == int(n)
    assert _letras(ctx, lista) == orden.replace(" y ", ", ").split(", ")


@then(parsers.re(r'la API responde 200 con solo la carga (?P<letra>[A-D])'))
def _lista_de_una(ctx: Escenario, letra: str) -> None:
    assert _letras(ctx, _lista(ctx)) == [letra]


@then(parsers.re(r'la API responde 200 con las cargas (?P<orden>[A-D](?:, [A-D])* y [A-D])'))
def _lista_de_varias(ctx: Escenario, orden: str) -> None:
    assert _letras(ctx, _lista(ctx)) == orden.replace(" y ", ", ").split(", ")


@then(parsers.re(r'cada carga trae su sección, su estado, filas_leidas, filas_aceptadas, filas_rechazadas, el nombre '
                 r'del archivo, los primeros 12 caracteres de la huella y el correo de quien la sube'))
def _campos_de_cada_carga(ctx: Escenario) -> None:
    quien = {"A": A.DOCENTE_410, "B": A.DOCENTE_410, "C": A.DOCENTE_410, "D": A.DOCENTE_411}
    for item, letra in zip(_lista(ctx), _letras(ctx, _lista(ctx)), strict=True):
        assert set(item) == CAMPOS_DE_LA_LISTA, sorted(item)
        contenido, nombre = ctx.extras["archivos"][letra]
        fila = ctx.filas("SELECT c.estado, c.filas_leidas, c.filas_aceptadas, c.filas_rechazadas, s.numero"
                         " FROM abet.carga c JOIN abet.seccion s USING (seccion_id) WHERE c.carga_id = %s",
                         item["carga_id"])[0]
        assert (item["estado"], item["filas_leidas"], item["filas_aceptadas"], item["filas_rechazadas"],
                item["seccion"]["numero"]) == fila
        assert item["seccion"] == {"seccion_id": ctx.seccion_id(fila[4]), "asignatura": ASIGNATURA,
                                   "numero": fila[4], "periodo": A.PERIODO}
        assert item["nombre_archivo"] == nombre
        assert item["sha256_corto"] == hashlib.sha256(contenido).hexdigest()[:12]
        assert item["subida_por"] == quien[letra]


@then(parsers.re(r'la carga (?P<letra>[A-D]) trae el motivo "(?P<motivo>[A-Z_]+)"'))
def _motivo(ctx: Escenario, letra: str, motivo: str) -> None:
    item = next(i for i in _lista(ctx) if i["carga_id"] == _id(ctx, letra))
    assert item["motivo"] == motivo
    otras = [i["motivo"] for i in _lista(ctx) if i["carga_id"] != _id(ctx, letra)]
    assert otras == [None] * len(otras), "solo la carga RECHAZADA por su sección trae un motivo"


@then(parsers.re(r'la carga (?P<nueva>[A-D]) indica que reemplaza a la carga (?P<anterior>[A-D])'))
def _indica_reemplazo(ctx: Escenario, nueva: str, anterior: str) -> None:
    items = {i["carga_id"]: i for i in _lista(ctx)}
    assert items[_id(ctx, nueva)]["reemplaza_carga_id"] == _id(ctx, anterior)
    assert items[_id(ctx, anterior)]["reemplazada_por"] == _id(ctx, nueva)


@then(parsers.re(r'iniciada_en y terminada_en de cada carga vienen con el desfase "(?P<desfase>[-+][0-9]{2}:[0-9]{2})"'))
def _desfase(ctx: Escenario, desfase: str) -> None:
    for item in _lista(ctx):
        assert item["iniciada_en"].endswith(desfase) and item["terminada_en"].endswith(desfase), item


@then(parsers.re(r'la respuesta no trae la carga D ni ningún dato de la sección 411'))
def _sin_la_411(ctx: Escenario) -> None:
    lista = _lista(ctx)
    assert _id(ctx, "D") not in [i["carga_id"] for i in lista]
    assert {i["seccion"]["numero"] for i in lista} == {"410"}
    seccion_411 = ctx.seccion_id("411")
    assert all(i["seccion"]["seccion_id"] != seccion_411 for i in lista)
    assert "docente411" not in ctx.respuesta.text


@then(parsers.re(r'GET /api/cargas\?seccion_id=\{sección (?P<numero>[0-9]+)\} responde 403'))
def _filtro_ajeno(ctx: Escenario, numero: str) -> None:
    respuesta = ctx.sesion(_usuario(ctx)).get("/api/cargas", params={"seccion_id": str(ctx.seccion_id(numero))})
    assert (respuesta.status_code, respuesta.json()) == (403, SIN_ALCANCE)


@then(parsers.re(r'la API responde 200 con el estado "(?P<estado>[A-Z]+)", filas_leidas (?P<leidas>[0-9]+), '
                 r'filas_aceptadas (?P<aceptadas>[0-9]+) y filas_rechazadas (?P<rechazadas>[0-9]+)'))
def _constancia_con_estado(ctx: Escenario, estado: str, leidas: str, aceptadas: str, rechazadas: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    cuerpo = ctx.cuerpo()
    assert (cuerpo["estado"], cuerpo["filas_leidas"], cuerpo["filas_aceptadas"], cuerpo["filas_rechazadas"]) == (
        estado, int(leidas), int(aceptadas), int(rechazadas))


@then(parsers.re(r'la constancia lista el rechazo de la fila (?P<fila>[0-9]+) en el PI (?P<pi>[0-9]\.[0-9]) con el motivo '
                 r'"(?P<motivo>[A-Z_]+)" y el efecto "(?P<efecto>[A-Z_]+)"'))
def _constancia_con_rechazo(ctx: Escenario, fila: str, pi: str, motivo: str, efecto: str) -> None:
    rechazos = [(r["fila"], r["pi"], r["motivo"], r["efecto"]) for r in ctx.cuerpo()["rechazos"]]
    assert rechazos == [(int(fila), pi, motivo, efecto)]


@then(parsers.re(r'la constancia indica que la carga (?P<nueva>[A-D]) reemplaza a la carga (?P<anterior>[A-D])'))
def _constancia_con_sucesora(ctx: Escenario, nueva: str, anterior: str) -> None:
    cuerpo = ctx.cuerpo()
    assert cuerpo["carga_id"] == _id(ctx, anterior)
    assert cuerpo["reemplazada_por"] == _id(ctx, nueva)


@then(parsers.re(r'GET /api/cargas/\{(?P<letra>[A-D])\}/r17\.xlsx responde 409 y no entrega ningún archivo'))
def _sin_r17(ctx: Escenario, letra: str) -> None:
    respuesta = ctx.sesion(_usuario(ctx)).get(f"/api/cargas/{_id(ctx, letra)}/r17.xlsx")
    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "La carga no está publicada y no tiene R-17."}
    assert "content-disposition" not in respuesta.headers
    assert not respuesta.content.startswith(b"PK")


@then(parsers.re(r'(?P<texto>ningún valor de las columnas Last Name ni First Name de los exports de prueba aparece en la '
                 r'respuesta ni en la pantalla)'))
def _sin_nombres(ctx: Escenario, texto: str) -> None:
    texto_de_la_respuesta = ctx.respuesta.text
    for nombre in _nombres_de_los_exports(ctx):
        assert nombre not in texto_de_la_respuesta, "la lista repite un nombre de un export"
    _delegar(ctx, texto)


@then(parsers.re(r'ningún nombre de archivo de la respuesta contiene "/" ni "\\"'))
def _nombres_sin_ruta(ctx: Escenario) -> None:
    for item in _lista(ctx):
        assert "/" not in item["nombre_archivo"] and "\\" not in item["nombre_archivo"]


@then(parsers.re(r'la respuesta no trae ningún valor leído de una celda de PI'))
def _sin_valores_leidos(ctx: Escenario) -> None:
    for item in _lista(ctx):
        assert set(item) == CAMPOS_DE_LA_LISTA, "la lista trae un campo que el contrato no nombra"
    assert "valor" not in ctx.respuesta.text
