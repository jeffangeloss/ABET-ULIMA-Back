"""Pasos de alcance_coordinacion.feature (US-70 a US-72 de la spec 008), con pytest-bdd en español (T023 y T024).

El .feature manda. Cada «Entonces» se comprueba contra la base desechable del escenario, sin dobles del sistema bajo
prueba. Los Antecedentes arman la base de la spec 008 con los datos de 2026-2 y los de Química General
(db/datos/quimica_2026_1_inventado.sql), en el clúster desechable de tests/cluster_desechable.py y nunca en
localhost:5432.

Cada escenario se ata con @scenario y el nombre de su tarea. Aquí están los de la base (T023 y T024), los de la API
con el alcance nuevo (T030), los de la sesión con el campo alcance (T031) y los del guion de registro (T032), que corre
como proceso aparte con las variables de libpq de la copia del escenario, como el guion de la spec 006. Los de
pantalla los prueba Vitest en el Front.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import psycopg
from psycopg.conninfo import make_conninfo
from pytest_bdd import given, parsers, scenario, then, when

Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/alcance_coordinacion.feature"
PROBAR_ROL_APP = RAIZ / "db" / "pruebas" / "probar_rol_app.sql"
PRIVILEGIOS = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")
A = sys.modules["api_de_prueba"]
C = sys.modules["cargas_de_prueba"]
ALCANCE_AMB = RAIZ / "db" / "datos" / "alcance_coordinacion_ambiental.sql"
REGISTRAR = RAIZ / "db" / "herramientas" / "registrar_coordinacion.py"
SIN_ALCANCE = "La sección no está a su cargo."
VENCIDA = "La sesión venció. Ingrese otra vez."
EXPORT_410 = "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04-14-36-02.xlsx"


@scenario(FEATURE, "La base exige un solo alcance por fila")
def test_la_base_exige_un_solo_alcance_por_fila() -> None:
    """T023."""


@scenario(FEATURE, "El rol de la aplicación solo lee el alcance")
def test_el_rol_de_la_aplicacion_solo_lee_el_alcance() -> None:
    """T023."""


@scenario(FEATURE, "Q20 lista una coordinación de curso con una sección propia en acceso.docente_seccion")
def test_q20_lista_una_coordinacion_de_curso_con_una_seccion_propia() -> None:
    """T023."""


# Ayudas

def _id(ctx: Escenario, consulta: str, *parametros: object) -> int:
    return int(ctx.uno(consulta, *parametros))


def _ids(ctx: Escenario) -> dict[str, int]:
    return {
        "usuario": _id(ctx, "SELECT usuario_id FROM acceso.usuario_autorizado WHERE correo = 'coordinacion@example.invalid'"),
        "carrera": _id(ctx, "SELECT carrera_id FROM abet.carrera WHERE codigo = 'AMB'"),
        "asignatura": _id(ctx, "SELECT asignatura_id FROM abet.asignatura WHERE codigo = '5643'"),
        "periodo": _id(ctx, "SELECT periodo_id FROM abet.periodo WHERE codigo = '2026-1'"),
    }


# Cuando

@when(parsers.re(r'el dueño de la base inserta en acceso\.coordinacion_alcance una fila con (?P<valores>.+)'))
def _inserta_fila(ctx: Escenario, valores: str) -> None:
    i = _ids(ctx)
    filas = {
        'la carrera "AMB" y la asignatura 5643 a la vez': (i["usuario"], i["carrera"], i["asignatura"], i["periodo"]),
        "ni carrera ni asignatura": (i["usuario"], None, None, None),
        "la asignatura 5643 sin periodo": (i["usuario"], None, i["asignatura"], None),
        # La fila de AMB de coordinacion@example.invalid ya está desde los Antecedentes.
        'la carrera "AMB" repetida para el mismo usuario': (i["usuario"], i["carrera"], None, None),
    }
    assert valores in filas, f"valores sin regla: {valores}"
    ctx.antes = ctx.conteos()
    ctx.error_directo = None
    try:
        ctx.api.dueno.execute("INSERT INTO acceso.coordinacion_alcance (usuario_id, carrera_id, asignatura_id, periodo_id)"
                              " VALUES (%s, %s, %s, %s)", filas[valores])
    except psycopg.Error as falla:
        ctx.error_directo = falla


@when(parsers.re(r'abet_app inserta una fila en acceso\.coordinacion_alcance'))
def _rol_app_inserta(ctx: Escenario) -> None:
    conexion = make_conninfo(ctx.api.base.conexion, user=ctx.api.base.rol_app)
    ctx.directa = ctx.pila.enter_context(psycopg.connect(conexion, autocommit=True))
    assert ctx.directa.execute("SELECT current_user").fetchone()[0] == ctx.api.base.rol_app
    ctx.antes = ctx.conteos()
    usuario = _id(ctx, "SELECT usuario_id FROM acceso.usuario_autorizado WHERE correo = 'docente701@example.invalid'")
    ctx.intentar("INSERT INTO acceso.coordinacion_alcance (usuario_id, carrera_id)"
                 " SELECT %s, carrera_id FROM abet.carrera WHERE codigo = 'IND'", usuario)


@given(parsers.re(r'"(?P<correo>[^"]+)" asignado también a la (?P<numero>[0-9]+) en acceso\.docente_seccion'))
def _asignado_tambien(ctx: Escenario, correo: str, numero: str) -> None:
    ctx.api.dueno.execute(
        "INSERT INTO acceso.docente_seccion (usuario_id, seccion_id)"
        " SELECT u.usuario_id, s.seccion_id FROM acceso.usuario_autorizado u, abet.seccion s"
        " JOIN abet.asignatura a USING (asignatura_id) JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
        " WHERE u.correo = %s AND s.numero = %s AND a.codigo = '5643' AND pe.codigo = '2026-1'", (correo, numero))


# Entonces

@then(parsers.re(r'PostgreSQL la rechaza con (?P<restriccion>[a-z_]+)'))
def _rechaza(ctx: Escenario, restriccion: str) -> None:
    assert ctx.error_directo is not None, "la base aceptó la fila"
    assert ctx.error_directo.diag.constraint_name == restriccion, ctx.error_directo.diag.message_primary
    ahora = ctx.conteos()
    assert ahora["acceso.coordinacion_alcance"] == ctx.antes["acceso.coordinacion_alcance"]


@then(parsers.re(r'PostgreSQL responde el SQLSTATE (?P<estado>[0-9A-Z]{5})'))
def _sqlstate(ctx: Escenario, estado: str) -> None:
    assert ctx.error_directo is not None, "el rol de la aplicación pudo insertar"
    assert ctx.error_directo.sqlstate == estado
    assert ctx.conteos()["acceso.coordinacion_alcance"] == ctx.antes["acceso.coordinacion_alcance"]


@then(parsers.re(r'db/pruebas/probar_rol_app\.sql lista SELECT como único privilegio de abet_app en esa tabla'))
def _solo_select(ctx: Escenario) -> None:
    rol = ctx.api.base.rol_app
    tiene = {privilegio for privilegio in PRIVILEGIOS if ctx.uno(
        "SELECT has_table_privilege(%s, 'acceso.coordinacion_alcance', %s)", rol, privilegio)}
    assert tiene == {"SELECT"}
    texto = PROBAR_ROL_APP.read_text(encoding="utf-8")
    assert "ok N09 el rol solo lee acceso.coordinacion_alcance" in texto
    # La lista de sentencias denegadas suma la escritura de la tabla de alcance.
    for sentencia in ("INSERT INTO acceso.coordinacion_alcance", "UPDATE acceso.coordinacion_alcance",
                      "DELETE FROM acceso.coordinacion_alcance", "TRUNCATE acceso.coordinacion_alcance"):
        assert sentencia in texto, sentencia


@then(parsers.re(r'devuelve 1 fila con su usuario_id y su rol, sin el correo'))
def _q20_una_fila(ctx: Escenario) -> None:
    usuario = _id(ctx, "SELECT usuario_id FROM acceso.usuario_autorizado"
                       " WHERE correo = 'coordinador.quimica@example.invalid'")
    filas = ctx.extras["control"]
    assert [tuple(fila) for fila in filas] == [(usuario, "COORDINADOR")]
    assert "@" not in repr(filas)


# US-70 y US-71. Escenarios de la API con el alcance nuevo (T030) y de la sesión con el campo alcance (T031)

@scenario(FEATURE, "La coordinación de Ambiental no ve las secciones de Química General")
def test_la_coordinacion_de_ambiental_no_ve_quimica() -> None:
    """T030."""


@scenario(FEATURE, "La coordinación de Ambiental conserva lo que ya veía")
def test_la_coordinacion_de_ambiental_conserva_lo_que_veia() -> None:
    """T030."""


@scenario(FEATURE, "Una sección o una carga de Química pedida por la coordinación de Ambiental responde el 403 de siempre")
def test_quimica_pedida_por_ambiental_responde_403() -> None:
    """T030."""


@scenario(FEATURE, "Un coordinador sin alcance no ve ninguna sección y Q20 lo lista")
def test_un_coordinador_sin_alcance_no_ve_nada() -> None:
    """T030 y T031."""


@scenario(FEATURE, "Con las dos carreras vigentes en el mismo periodo, el curso compartido sigue el valor provisional de J-50")
def test_el_curso_compartido_sigue_j_50() -> None:
    """T030."""


@scenario(FEATURE, "El guion de alcance de Ambiental corre antes del código nuevo y no deja a la coordinación sin alcance")
def test_el_guion_de_alcance_de_ambiental_corre_antes() -> None:
    """T023 y T030."""


@scenario(FEATURE, "La coordinación del curso ve las secciones de 5643 en orden y ninguna otra")
def test_la_coordinacion_del_curso_ve_sus_secciones() -> None:
    """T030."""


@scenario(FEATURE, "La sesión dice el alcance del curso sin un rol nuevo")
def test_la_sesion_dice_el_alcance() -> None:
    """T031."""


@scenario(FEATURE, "Una cuenta con alcance de carrera y de curso recibe el tipo más amplio")
def test_carrera_y_curso_recibe_el_tipo_mas_amplio() -> None:
    """T030 y T031."""


@scenario(FEATURE, "La asignación vale solo en su periodo")
def test_la_asignacion_vale_solo_en_su_periodo() -> None:
    """T030."""


@scenario(FEATURE, "Lee la constancia y el R-17 de una sección de su curso")
def test_lee_la_constancia_y_el_r17_de_su_curso() -> None:
    """T030."""


@scenario(FEATURE, "La coordinación del curso no alcanza otro curso")
def test_la_coordinacion_del_curso_no_alcanza_otro_curso() -> None:
    """T030."""


@scenario(FEATURE, "La coordinación del curso no sube una carga nueva")
def test_la_coordinacion_del_curso_no_sube() -> None:
    """T030."""


@scenario(FEATURE, "La coordinación del curso reemplaza en su curso con el valor provisional de D-52")
def test_la_coordinacion_del_curso_reemplaza() -> None:
    """T030."""


@scenario(FEATURE, "Una cuenta de coordinación dada de baja no alcanza nada")
def test_una_coordinacion_dada_de_baja_no_alcanza_nada() -> None:
    """T030."""


@scenario(FEATURE, "El profesor del curso sigue viendo solo su sección")
def test_el_profesor_del_curso_sigue_viendo_su_seccion() -> None:
    """T030."""


# US-72. Escenarios del guion de registro (T032)

@scenario(FEATURE, "La corrida en seco del registro de la coordinación informa sin repetir el correo")
def test_registro_en_seco() -> None:
    """T032."""


@scenario(FEATURE, "Con --aplicar escribe una vez y se puede repetir")
def test_registro_aplicado_dos_veces() -> None:
    """T032."""


@scenario(FEATURE, "Un correo que ya es profesor detiene el guion sin cambiar su rol")
def test_registro_de_un_profesor() -> None:
    """T032."""


@scenario(FEATURE, "Una cuenta dada de baja no se reactiva")
def test_registro_de_una_baja() -> None:
    """T032."""


@scenario(FEATURE, "Un argumento inválido se rechaza antes de escribir")
def test_registro_con_un_argumento_invalido() -> None:
    """T032."""


@scenario(FEATURE, "Sin la variable del correo el guion no adivina")
def test_registro_sin_la_variable() -> None:
    """T032."""


@scenario(FEATURE, "Una asignatura sin plan de medición entra con aviso")
def test_registro_de_una_asignatura_sin_plan() -> None:
    """T032."""


@scenario(FEATURE, "El guion no escribe contraseñas ni las muestra")
def test_registro_sin_contrasenas() -> None:
    """T032."""


# Ayudas de la API

def _cuerpo(ctx: Escenario, respuesta: Any = None) -> Any:
    respuesta = respuesta if respuesta is not None else ctx.respuesta
    assert respuesta is not None, "el escenario todavía no pidió nada"
    return respuesta.json()


def _secciones(ctx: Escenario, respuesta: Any = None) -> list[tuple[str, str]]:
    respuesta = respuesta if respuesta is not None else ctx.respuesta
    assert respuesta.status_code == 200, respuesta.text
    return [(fila["asignatura"]["codigo"], fila["numero"]) for fila in respuesta.json()]


def _lista(texto: str) -> list[str]:
    return re.findall(r'"([^"]+)"', texto)


def _publicar(ctx: Escenario, numero: str, quien: str | None = None, asignatura: str | None = None) -> int:
    """Carga PUBLICADA inventada de la sección, subida por la ruta 5 con la sesión de su profesor."""
    if numero.startswith("70") and asignatura in (None, "5643"):
        contenido, nombre = ctx.export_de_quimica(numero)
    else:
        contenido, nombre = ctx.de_inventados(EXPORT_410), EXPORT_410
    quien = quien or f"docente{numero}@example.invalid"
    respuesta = A.subir(ctx.sesion(quien), ctx.seccion_de(numero, asignatura), contenido, nombre)
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "PUBLICADA", respuesta.text
    carga = int(respuesta.json()["carga_id"])
    ctx.extras.setdefault("cargas", {})[numero] = carga
    ctx.carga_id = carga
    return carga


def _alcance_de(ctx: Escenario, correo: str) -> dict[str, Any]:
    respuesta = ctx.sesion(correo).get("/api/sesion")
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["alcance"]


def _psql(ctx: Escenario, *argumentos: str) -> subprocess.CompletedProcess[str]:
    """psql sobre la base del escenario, siempre en el clúster desechable de tests/base_desechable.py."""
    entorno = ctx.plantillas.base_desechable._entorno()
    return subprocess.run([entorno.get("PSQL", "psql"), "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", ctx.api.base.nombre,
                           *argumentos], env=entorno, capture_output=True, text=True, check=False)


# Dado

@given(parsers.re(r'la carga PUBLICADA inventada de la (?P<numero>[0-9]+)(?: de "(?P<asignatura>[0-9]+)")?'
                  r'(?:, subida por "(?P<quien>[^"]+)")?'))
def _carga_publicada(ctx: Escenario, numero: str, asignatura: str | None, quien: str | None) -> None:
    _publicar(ctx, numero, quien, asignatura)


@given(parsers.re(r'"(?P<correo>[^"]+)" con rol "(?P<rol>[A-Z]+)", activo y sin fila en acceso\.coordinacion_alcance'))
def _coordinador_sin_alcance(ctx: Escenario, correo: str, rol: str) -> None:
    ctx.api.dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES (%s, %s)", (correo, rol))
    assert ctx.uno("SELECT count(*) FROM acceso.coordinacion_alcance WHERE usuario_id = %s", ctx.usuario_id(correo)) == 0
    ctx.extras["sin_alcance"] = correo


@given(parsers.re(r'AMB-2026 también vigente en 2026-1, con 5643 en su plan de estudios y sin plan de medición de '
                  r'Ambiental para 5643'))
def _amb_vigente_en_2026_1(ctx: Escenario) -> None:
    ctx.api.dueno.execute("INSERT INTO abet.catalogo_vigencia (periodo_id, carrera_id, catalogo_version_id)"
                          " SELECT pe.periodo_id, cv.carrera_id, cv.catalogo_version_id FROM abet.periodo pe,"
                          " abet.catalogo_version cv WHERE pe.codigo = '2026-1' AND cv.codigo = 'AMB-2026'")
    assert ctx.uno("SELECT count(*) FROM abet.plan_estudios pl JOIN abet.catalogo_version cv USING (catalogo_version_id)"
                   " JOIN abet.asignatura a USING (asignatura_id) WHERE cv.codigo = 'AMB-2026' AND a.codigo = '5643'") == 1
    assert ctx.uno("SELECT count(*) FROM abet.plan_medicion pm JOIN abet.carrera c USING (carrera_id)"
                   " JOIN abet.asignatura a USING (asignatura_id) WHERE c.codigo = 'AMB' AND a.codigo = '5643'") == 0


@given(parsers.re(r'una base desechable con periodo_2026_2_inventado\.sql, V1_14 aplicada y "(?P<correo>[^"]+)" sin '
                  r'fila en acceso\.coordinacion_alcance'))
def _base_sin_el_alcance(ctx: Escenario, correo: str) -> None:
    # Una base propia con los datos de 2026-2 y todas las migraciones, a la que se le quita la fila que
    # periodo_2026_2_inventado.sql da a la coordinación, como en Neon antes de alcance_coordinacion_ambiental.sql.
    ctx.crear_base("periodo")
    ctx.sesiones.clear()
    assert ctx.uno("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'acceso'"
                   " AND table_name = 'coordinacion_alcance'") == 1
    ctx.api.dueno.execute("DELETE FROM acceso.coordinacion_alcance WHERE usuario_id = %s", (ctx.usuario_id(correo),))
    ctx.extras["correo_del_guion"] = correo


@given(parsers.re(r'"(?P<correo>[^"]+)" también con alcance de la asignatura "(?P<asignatura>[0-9]+)" en '
                  r'"(?P<periodo>[^"]+)"'))
def _tambien_con_curso(ctx: Escenario, correo: str, asignatura: str, periodo: str) -> None:
    ctx.api.dueno.execute("INSERT INTO acceso.coordinacion_alcance (usuario_id, asignatura_id, periodo_id)"
                          " SELECT %s, a.asignatura_id, pe.periodo_id FROM abet.asignatura a, abet.periodo pe"
                          " WHERE a.codigo = %s AND pe.codigo = %s", (ctx.usuario_id(correo), asignatura, periodo))


@given(parsers.re(r'la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" también en (?P<periodo>[0-9]{4}-[0-9]), '
                  r'sin fila de alcance de [0-9]+ en [0-9]{4}-[0-9]'))
def _seccion_en_otro_periodo(ctx: Escenario, numero: str, asignatura: str, periodo: str) -> None:
    ctx.api.dueno.execute("INSERT INTO abet.seccion (periodo_id, asignatura_id, numero) SELECT pe.periodo_id,"
                          " a.asignatura_id, %s FROM abet.periodo pe, abet.asignatura a WHERE pe.codigo = %s"
                          " AND a.codigo = %s", (numero, periodo, asignatura))
    assert ctx.uno("SELECT count(*) FROM acceso.coordinacion_alcance ca JOIN abet.periodo pe USING (periodo_id)"
                   " WHERE pe.codigo = %s", periodo) == 0


@given(parsers.re(r'su cuenta pasa a activo falso'))
def _dada_de_baja(ctx: Escenario) -> None:
    ctx.api.dueno.execute("UPDATE acceso.usuario_autorizado SET activo = false WHERE correo = %s",
                          (ctx.extras["con_sesion"],))


# Cuando

@when(parsers.re(r'pide (?P<rutas>GET \S+(?: y GET \S+)?)(?: de esa carga| con el identificador de la '
                 r'(?P<numero>[0-9]+)| con su cookie anterior)?'))
def _pide(ctx: Escenario, rutas: str, numero: str | None) -> None:
    respuestas = {}
    for ruta in re.findall(r"GET (\S+)", rutas):
        camino = ruta
        if numero is not None:
            camino = camino.replace("{seccion}", str(ctx.seccion_de(numero)))
            camino = camino.replace("{carga}", str(ctx.extras.get("cargas", {}).get(numero)))
        elif "{carga}" in camino:
            assert ctx.carga_id is not None, "el escenario no tiene «esa carga»"
            camino = camino.replace("{carga}", str(ctx.carga_id))
        respuestas[ruta] = ctx.pedir(camino)
    ctx.extras["respuestas"] = respuestas


@when(parsers.re(r'sube un export inventado válido a POST /api/secciones/\{(?P<numero>[0-9]+)\}/cargas sin reemplaza'))
def _sube_sin_reemplaza(ctx: Escenario, numero: str) -> None:
    contenido, nombre = ctx.export_de_quimica(numero)
    ctx.antes = ctx.conteos()
    ctx.respuesta = A.subir(ctx.sesion(ctx.extras["con_sesion"]), ctx.seccion_de(numero), contenido, nombre)


@when(parsers.re(r'sube un export corregido de la (?P<numero>[0-9]+) con reemplaza igual a esa carga'))
def _sube_con_reemplaza(ctx: Escenario, numero: str) -> None:
    # Otros niveles, así el archivo corregido tiene otra huella que el publicado.
    contenido, nombre = ctx.export_de_quimica(numero, (4, 4, 3, 3))
    ctx.carga_previa = ctx.extras["cargas"][numero]
    ctx.antes = ctx.conteos()
    ctx.respuesta = A.subir(ctx.sesion(ctx.extras["con_sesion"]), ctx.seccion_de(numero), contenido, nombre,
                            params={"reemplaza": str(ctx.carga_previa)})


@when(parsers.re(r'psql corre db/datos/alcance_coordinacion_ambiental\.sql con -v aplicar=1'))
def _corre_alcance_amb(ctx: Escenario) -> None:
    corrida = _psql(ctx, "-v", "aplicar=1", "-f", str(ALCANCE_AMB))
    assert corrida.returncode == 0, corrida.stderr
    assert "1 filas nuevas" in corrida.stdout, corrida.stdout


# Entonces

@then(parsers.re(r'recibe 200 con una lista vacía(?P<porque>, porque AMB-2026 no tiene vigencia en 2026-1)?'
                 r'(?: y no la 410 ni la 411)?'))
def _lista_vacia(ctx: Escenario, porque: str | None) -> None:
    assert _secciones(ctx) == []
    if porque:
        vigencias = ctx.filas("SELECT c.codigo FROM abet.catalogo_vigencia v JOIN abet.carrera c USING (carrera_id)"
                              " JOIN abet.periodo pe USING (periodo_id) WHERE pe.codigo = '2026-1' ORDER BY 1")
        # IND-2026 sí está vigente en 2026-1, así que el escenario prueba el alcance por carrera.
        assert vigencias == [("IND",)]


@then(parsers.re(r'recibe 200 con la 410 y la 411 de "450002", como antes del cambio'))
def _la_410_y_la_411(ctx: Escenario) -> None:
    assert _secciones(ctx) == [("450002", "410"), ("450002", "411")]


@then(parsers.re(r'recibe 403 con «(?P<mensaje>[^»]+)»'))
def _recibe_403(ctx: Escenario, mensaje: str) -> None:
    assert ctx.respuesta.status_code == 403, ctx.respuesta.text
    assert _cuerpo(ctx) == {"detail": mensaje}


@then(parsers.re(r'la respuesta no trae datos de la 701'))
def _sin_datos_de_la_701(ctx: Escenario) -> None:
    assert _cuerpo(ctx) == {"detail": SIN_ALCANCE}
    assert "701" not in ctx.respuesta.text and "5643" not in ctx.respuesta.text


@then(parsers.re(r'la consulta de control Q20 devuelve 1 fila con su usuario_id y su rol, sin el correo'))
def _q20_del_sin_alcance(ctx: Escenario) -> None:
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            filas = ctx.filas(plugin.consultas_de_control()["Q20"])
            break
    else:
        raise AssertionError("no se encuentra tests/aceptacion/pasos/conftest.py")
    assert [tuple(fila) for fila in filas] == [(ctx.usuario_id(ctx.extras["sin_alcance"]), "COORDINADOR")]
    assert "@" not in repr(filas)


@then(parsers.re(r'GET /api/sesion trae el alcance de tipo "(?P<tipo>[A-Z]+)" con las carreras (?P<carreras>\[[^\]]*\]) '
                 r'y las asignaturas (?P<asignaturas>\[[^\]]*\])'))
def _sesion_trae(ctx: Escenario, tipo: str, carreras: str, asignaturas: str) -> None:
    assert _alcance_de(ctx, ctx.extras["con_sesion"]) == {"tipo": tipo, "carreras": _lista(carreras),
                                                          "asignaturas": _lista(asignaturas)}


@then(parsers.re(r'recibe las secciones 701 a 704 de "5643", porque la regla provisional es el plan de estudios del '
                 r'catálogo vigente de su carrera'))
def _las_cuatro_por_j_50(ctx: Escenario) -> None:
    assert _secciones(ctx) == [("5643", n) for n in ("701", "702", "703", "704")]


@then(parsers.re(r'recibe 200 con la 701, la 702, la 703 y la 704 de "5643" en ese orden'))
def _las_cuatro_en_orden(ctx: Escenario) -> None:
    assert _secciones(ctx) == [("5643", n) for n in ("701", "702", "703", "704")]


@then(parsers.re(r'la respuesta no trae la 410 ni la 411 de "450002"'))
def _sin_450002(ctx: Escenario) -> None:
    assert all(asignatura != "450002" for asignatura, _ in _secciones(ctx))


@then(parsers.re(r'recibe 200 con el rol "(?P<rol>[A-Z]+)" y el alcance de tipo "(?P<tipo>[A-Z]+)" con las asignaturas '
                 r'(?P<asignaturas>\[[^\]]*\]) \(propuesta\)'))
def _sesion_con_alcance(ctx: Escenario, rol: str, tipo: str, asignaturas: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    assert _cuerpo(ctx) == {"correo": ctx.extras["con_sesion"], "rol": rol,
                            "alcance": {"tipo": tipo, "carreras": [], "asignaturas": _lista(asignaturas)}}


@then(parsers.re(r'la sesión de "(?P<correo>[^"]+)" trae el alcance de tipo "(?P<tipo>[A-Z]+)"'
                 r'(?: con las carreras (?P<carreras>\[[^\]]*\]))?'))
def _sesion_de(ctx: Escenario, correo: str, tipo: str, carreras: str | None) -> None:
    alcance = _alcance_de(ctx, correo)
    assert alcance["tipo"] == tipo
    assert alcance["carreras"] == (_lista(carreras) if carreras is not None else [])
    assert alcance["asignaturas"] == []


@then(parsers.re(r'el alcance es de tipo "(?P<tipo>[A-Z]+)" con las carreras (?P<carreras>\[[^\]]*\]) y las asignaturas '
                 r'(?P<asignaturas>\[[^\]]*\])'))
def _alcance_es(ctx: Escenario, tipo: str, carreras: str, asignaturas: str) -> None:
    respuesta = ctx.extras["respuestas"]["/api/sesion"]
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["alcance"] == {"tipo": tipo, "carreras": _lista(carreras),
                                           "asignaturas": _lista(asignaturas)}


@then(parsers.re(r'recibe la 701, la 702, la 703 y la 704 de "5643", la unión de las dos filas'))
def _la_union(ctx: Escenario) -> None:
    respuesta = ctx.extras["respuestas"]["/api/secciones?periodo=2026-1"]
    assert _secciones(ctx, respuesta) == [("5643", n) for n in ("701", "702", "703", "704")]


@then(parsers.re(r'las dos rutas responden 200'))
def _dos_en_200(ctx: Escenario) -> None:
    respuestas = ctx.extras["respuestas"]
    assert len(respuestas) == 2
    for ruta, respuesta in respuestas.items():
        assert respuesta.status_code == 200, f"{ruta}: {respuesta.text}"


@then(parsers.re(r'recibe 201 con la carga nueva PUBLICADA y la anterior REEMPLAZADA'))
def _reemplazada(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 201, ctx.respuesta.text
    ctx.carga_id = int(_cuerpo(ctx)["carga_id"])
    assert _cuerpo(ctx)["estado"] == "PUBLICADA"
    assert ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", ctx.carga_previa) == "REEMPLAZADA"


@then(parsers.re(r'subida_por de la carga nueva es el usuario de "(?P<correo>[^"]+)"'))
def _subida_por(ctx: Escenario, correo: str) -> None:
    assert ctx.uno("SELECT subida_por FROM abet.carga WHERE carga_id = %s", ctx.carga_id) == ctx.usuario_id(correo)


@then(parsers.re(r'recibe 401 y ninguna sección'))
def _recibe_401(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 401, ctx.respuesta.text
    assert _cuerpo(ctx) == {"detail": VENCIDA}


@then(parsers.re(r'recibe 200 solo con la 701'))
def _solo_la_701(ctx: Escenario) -> None:
    assert _secciones(ctx) == [("5643", "701")]


@then(parsers.re(r'"(?P<correo>[^"]+)" queda con el alcance de la carrera "(?P<carrera>[A-Z]+)"'))
def _queda_con_la_carrera(ctx: Escenario, correo: str, carrera: str) -> None:
    assert ctx.filas("SELECT c.codigo, ca.asignatura_id, ca.periodo_id FROM acceso.coordinacion_alcance ca"
                     " JOIN abet.carrera c USING (carrera_id) WHERE ca.usuario_id = %s",
                     ctx.usuario_id(correo)) == [(carrera, None, None)]


@then(parsers.re(r'con el _ALCANCE nuevo sigue viendo la 410 y la 411 de 2026-2'))
def _sigue_viendo(ctx: Escenario) -> None:
    respuesta = ctx.sesion(ctx.extras["correo_del_guion"]).get("/api/secciones?periodo=2026-2")
    assert _secciones(ctx, respuesta) == [("450002", "410"), ("450002", "411")]


@then(parsers.re(r'una segunda corrida no suma filas'))
def _segunda_corrida(ctx: Escenario) -> None:
    antes = ctx.conteos()["acceso.coordinacion_alcance"]
    corrida = _psql(ctx, "-v", "aplicar=1", "-f", str(ALCANCE_AMB))
    assert corrida.returncode == 0, corrida.stderr
    assert "0 filas nuevas" in corrida.stdout, corrida.stdout
    assert ctx.conteos()["acceso.coordinacion_alcance"] == antes


# US-72. El guion de registro

def _correr_registro(ctx: Escenario, argumentos: str, aplicar: bool, veces: int = 1) -> None:
    assert REGISTRAR.exists(), "falta db/herramientas/registrar_coordinacion.py (T032)"
    entorno = C.entorno_de_programacion(ctx.api.base.nombre)
    entorno.pop("CORREO_COORDINACION", None)
    if ctx.extras.get("correo_coordinacion") is not None:
        entorno["CORREO_COORDINACION"] = ctx.extras["correo_coordinacion"]
    ctx.antes = ctx.conteos()
    orden = [sys.executable, "-I", str(REGISTRAR), *argumentos.split(), *(["--aplicar"] if aplicar else [])]
    ctx.extras["corridas"] = [subprocess.run(orden, env=entorno, capture_output=True, text=True, encoding="utf-8",
                                             check=False, timeout=120) for _ in range(veces)]


def _salida(ctx: Escenario, indice: int = 0) -> str:
    corrida = ctx.extras["corridas"][indice]
    return corrida.stdout + corrida.stderr


def _codigo(ctx: Escenario, codigo: int) -> None:
    corrida = ctx.extras["corridas"][-1]
    assert corrida.returncode == codigo, corrida.stdout + corrida.stderr


@given(parsers.re(r'la variable CORREO_COORDINACION con "(?P<valor>[^"]*)"'))
def _con_la_variable(ctx: Escenario, valor: str) -> None:
    ctx.extras["correo_coordinacion"] = valor


@given(parsers.re(r'la variable CORREO_COORDINACION sin definir'))
def _sin_la_variable(ctx: Escenario) -> None:
    ctx.extras["correo_coordinacion"] = None


@given(parsers.re(r'"(?P<correo>[^"]+)" con rol "(?P<rol>[A-Z]+)" y activo falso'))
def _cuenta_dada_de_baja(ctx: Escenario, correo: str, rol: str) -> None:
    ctx.api.dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol, activo) VALUES (%s, %s, false)",
                          (correo, rol))


@when(parsers.re(r'(?:db/herramientas/registrar_coordinacion\.py|el guion) corre con '
                 r'(?P<argumentos>--asignatura [0-9]+ --periodo [0-9]{4}-[0-9])'
                 r'(?: (?P<seco>sin --aplicar)| y (?P<aplicar>--aplicar)(?P<dos> dos veces)?)?'))
def _corre_el_registro(ctx: Escenario, argumentos: str, seco: str | None, aplicar: str | None, dos: str | None) -> None:
    _correr_registro(ctx, argumentos, aplicar is not None, 2 if dos else 1)


@then(parsers.re(r'el informe dice que registraría 1 cuenta de coordinación nueva con el alcance de (?P<asignatura>[0-9]+) '
                 r'en (?P<periodo>[0-9]{4}-[0-9])'))
def _informe_en_seco(ctx: Escenario, asignatura: str, periodo: str) -> None:
    salida = _salida(ctx)
    assert f"Registraría 1 cuenta de coordinación nueva con el alcance de {asignatura} en {periodo}." in salida, salida
    assert "No se guardó nada, y --aplicar lo guarda." in salida


@then(parsers.re(r'el informe no repite el correo'))
def _sin_el_correo(ctx: Escenario) -> None:
    valor = ctx.extras["correo_coordinacion"]
    for indice in range(len(ctx.extras["corridas"])):
        salida = _salida(ctx, indice)
        assert valor not in salida and valor.strip().lower() not in salida and "@" not in salida


@then(parsers.re(r'el guion termina con código (?P<codigo>[0-9])'))
def _termina_con(ctx: Escenario, codigo: str) -> None:
    _codigo(ctx, int(codigo))


@then(parsers.re(r'acceso\.usuario_autorizado tiene 1 fila "(?P<correo>[^"]+)" con rol "(?P<rol>[A-Z]+)", activa y sin '
                 r'fila en acceso\.credencial'))
def _una_cuenta(ctx: Escenario, correo: str, rol: str) -> None:
    for corrida in ctx.extras["corridas"]:
        assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert ctx.filas("SELECT correo, rol, activo FROM acceso.usuario_autorizado WHERE lower(correo) LIKE %s",
                     correo.split("@")[0] + "@%") == [(correo, rol, True)]
    assert ctx.uno("SELECT count(*) FROM acceso.credencial WHERE usuario_id = %s", ctx.usuario_id(correo)) == 0
    ctx.extras["cuenta"] = correo


@then(parsers.re(r'acceso\.coordinacion_alcance tiene 1 fila de (?P<asignatura>[0-9]+) en (?P<periodo>[0-9]{4}-[0-9]) '
                 r'para esa cuenta'))
def _un_alcance(ctx: Escenario, asignatura: str, periodo: str) -> None:
    assert ctx.filas("SELECT ca.carrera_id, a.codigo, pe.codigo FROM acceso.coordinacion_alcance ca"
                     " LEFT JOIN abet.asignatura a USING (asignatura_id) LEFT JOIN abet.periodo pe USING (periodo_id)"
                     " WHERE ca.usuario_id = %s", ctx.usuario_id(ctx.extras["cuenta"])) == [(None, asignatura, periodo)]


@then(parsers.re(r'la segunda corrida informa 0 filas nuevas'))
def _segunda_sin_filas(ctx: Escenario) -> None:
    assert "Registró 2 filas nuevas." in _salida(ctx, 0), _salida(ctx, 0)
    assert "Registró 0 filas nuevas." in _salida(ctx, 1), _salida(ctx, 1)


@then(parsers.re(r'termina con código 1 y el informe dice que la cuenta ya existe con otro rol'))
def _otro_rol(ctx: Escenario) -> None:
    _codigo(ctx, 1)
    assert "La cuenta ya existe con otro rol" in _salida(ctx), _salida(ctx)


@then(parsers.re(r'el rol de "(?P<correo>[^"]+)" sigue siendo "(?P<rol>[A-Z]+)"'))
def _mismo_rol(ctx: Escenario, correo: str, rol: str) -> None:
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, True)]


@then(parsers.re(r'termina con código 1, activo sigue falso y el informe dice que la cuenta está dada de baja'))
def _sigue_de_baja(ctx: Escenario) -> None:
    _codigo(ctx, 1)
    assert "La cuenta está dada de baja" in _salida(ctx), _salida(ctx)
    assert ctx.filas("SELECT activo FROM acceso.usuario_autorizado WHERE correo = %s",
                     ctx.extras["correo_coordinacion"]) == [(False,)]
    assert ctx.conteos() == ctx.antes


@then(parsers.re(r'termina con código 1 y el informe nombra (?P<motivo>.+)'))
def _nombra(ctx: Escenario, motivo: str) -> None:
    _codigo(ctx, 1)
    salida = _salida(ctx).lower()
    for parte in re.sub(r"^(?:la|el) ", "", motivo).split(", que "):
        assert parte.lower() in salida, salida


@then(parsers.re(r'ninguna tabla de acceso gana filas'))
def _acceso_sin_filas(ctx: Escenario) -> None:
    ahora = ctx.conteos()
    de_acceso = [clave for clave in ahora if clave.startswith("acceso.")]
    assert de_acceso and {clave: ahora[clave] for clave in de_acceso} == {clave: ctx.antes[clave] for clave in de_acceso}


@then(parsers.re(r'termina con código 2 y dice «(?P<mensaje>[^»]+)»(?: \(propuesta\))?'))
def _codigo_2(ctx: Escenario, mensaje: str) -> None:
    _codigo(ctx, 2)
    assert mensaje in _salida(ctx), _salida(ctx)
    assert ctx.conteos() == ctx.antes


@then(parsers.re(r'el informe avisa que la asignatura (?P<asignatura>[0-9]+) no tiene plan de medición en '
                 r'(?P<periodo>[0-9]{4}-[0-9])'))
def _aviso_sin_plan(ctx: Escenario, asignatura: str, periodo: str) -> None:
    _codigo(ctx, 0)
    assert f"Aviso. La asignatura {asignatura} no tiene plan de medición en {periodo}" in _salida(ctx), _salida(ctx)
    assert "Registraría 1 cuenta de coordinación nueva" in _salida(ctx)
    assert ctx.conteos() == ctx.antes


@then(parsers.re(r'la salida no contiene la palabra «contraseña» seguida de un valor'))
def _sin_contrasena(ctx: Escenario) -> None:
    _codigo(ctx, 0)
    salida = _salida(ctx)
    assert not re.search(r"contrase(?:ñ|n)a\s*[:=]?\s*[^\s.,;]", salida, flags=re.IGNORECASE), salida
