"""Pasos de la ruta 17 GET /api/avance, con pytest-bdd en español (T038 de la spec 008, T031 a T033 de la spec 007).

El .feature manda. Cada «Entonces» se comprueba con la respuesta de la API y con la base desechable del escenario, sin
dobles del sistema bajo prueba, en el clúster desechable de tests/cluster_desechable.py y nunca en localhost:5432.

- avance_del_registro.feature (spec 007, US-64). Los Antecedentes parten de la variante «avance» de conftest.py, los
  datos de 2026-2 con el plan de 450010 que suma tests/cargas_de_prueba.base_del_avance_007(), y cada sección del
  escenario nace en su paso Dado con sus asignaciones y sus cargas, escritas con las ayudas de cargas_de_prueba.py.
  US-66 (el campo profesores) espera a D-47 y no se ata aquí, y los escenarios de P7 los prueba Vitest en el Front.
- avance_del_curso.feature (spec 008, US-79). Los Antecedentes arman la base de la spec 008 con el plan de 5643 en
  2026-1, y las cargas de Química General se suben por la ruta 5 con la sesión de cada profesor. Los escenarios de
  US-80 esperan a D-32 (J-54) y los de pantalla, a T046 del Front, así que no se atan aquí.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

from pytest_bdd import given, parsers, scenario, then, when

Escenario = Any
A = sys.modules["api_de_prueba"]
C = sys.modules["cargas_de_prueba"]
REGISTRO = "specs/007-experiencia-por-cuenta/aceptacion/avance_del_registro.feature"
CURSO = "specs/008-ciclo-quimica-industrial/aceptacion/avance_del_curso.feature"
ETAPAS = ("PUBLICADA", "CON_RECHAZO", "SIN_CARGA", "SIN_PROFESOR", "SIN_PLAN")
# Claves cerradas de la respuesta y de cada sección (BR-AVANCE-04). profesores espera a D-47 y D-51 (BR-AVANCE-05).
CLAVES = {"periodo", "conteo", "secciones"}
CLAVES_DE_SECCION = {"seccion_id", "asignatura", "numero", "etapa", "carga_id"}
PLANES = {"450002": ("5.1", "5.2", "5.3"), "450010": ("2.1", "2.2", "5.1")}


# Spec 007, US-64

@scenario(REGISTRO, "La ruta 17 da la etapa de cada sección en el orden de asignatura y número")
def test_la_ruta_17_da_la_etapa_de_cada_seccion() -> None:
    """T031 y T032 de la spec 007, en T038 de la spec 008."""


@scenario(REGISTRO, "La precedencia de J-48 decide la etapa de cada sección")
def test_la_precedencia_de_j_48_decide_la_etapa() -> None:
    """T032 de la spec 007, en T038 de la spec 008."""


@scenario(REGISTRO, "Solo la coordinación lee el avance, en el orden 401, 403 y 422")
def test_solo_la_coordinacion_lee_el_avance() -> None:
    """T031 y T033 de la spec 007, en T038 de la spec 008."""


@scenario(REGISTRO, "Sin periodo, la ruta 17 usa el periodo vigente")
def test_sin_periodo_la_ruta_17_usa_el_vigente() -> None:
    """T032 de la spec 007, en T038 de la spec 008."""


# Spec 008, US-79

@scenario(CURSO, "La ruta 17 da la etapa de cada sección del curso y ninguna de otro curso")
def test_la_ruta_17_da_la_etapa_del_curso() -> None:
    """T038."""


@scenario(CURSO, "Un periodo sin secciones del curso responde vacío")
def test_un_periodo_sin_secciones_del_curso_responde_vacio() -> None:
    """T038."""


@scenario(CURSO, "El profesor del curso no lee el avance")
def test_el_profesor_del_curso_no_lee_el_avance() -> None:
    """T038."""


@scenario(CURSO, "La coordinación de Ambiental no ve el avance de Química")
def test_la_coordinacion_de_ambiental_no_ve_el_avance_de_quimica() -> None:
    """T038."""


# Ayudas

def _cuerpo(ctx: Escenario, codigo: int = 200) -> Any:
    assert ctx.respuesta is not None, "el escenario todavía no pidió nada"
    assert ctx.respuesta.status_code == codigo, ctx.respuesta.text
    assert ctx.respuesta.headers["cache-control"] == "no-store"
    return ctx.respuesta.json()


def _filas(ctx: Escenario) -> list[tuple[str, str, str, int | None]]:
    """Asignatura, número, etapa y carga_id de cada sección de la respuesta, en su orden, con las claves cerradas."""
    cuerpo = _cuerpo(ctx)
    assert set(cuerpo) == CLAVES, sorted(cuerpo)
    filas = []
    for seccion in cuerpo["secciones"]:
        assert set(seccion) == CLAVES_DE_SECCION, sorted(seccion)
        assert set(seccion["asignatura"]) == {"codigo", "nombre"}
        assert seccion["etapa"] in ETAPAS, seccion["etapa"]
        filas.append((seccion["asignatura"]["codigo"], seccion["numero"], seccion["etapa"], seccion["carga_id"]))
    return filas


def _seccion_id(ctx: Escenario, numero: str, asignatura: str) -> int:
    return ctx.seccion_de(numero, asignatura)


def _asignar(ctx: Escenario, correo: str, numero: str, asignatura: str) -> None:
    ctx.api.dueno.execute("INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) VALUES (%s, %s)"
                          " ON CONFLICT DO NOTHING",
                          (ctx.usuario_id(correo), C.seccion(ctx.api.dueno, asignatura, numero)))


def _profesor(ctx: Escenario, correo: str, activo: bool = True) -> None:
    ctx.api.dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol, activo) VALUES (%s, 'PROFESOR', %s)",
                          (correo, activo))


def _publicar(ctx: Escenario, numero: str, asignatura: str) -> int:
    """Carga PUBLICADA inventada de una sección de 2026-2, con códigos del rango 99 propios de la sección."""
    desde = 99000000 + int(asignatura[-2:]) * 10000 + int(numero) * 10
    carga = C.publicar(ctx.api.dueno, asignatura=asignatura, numero=numero, pis=PLANES[asignatura],
                       filas=C.filas_inventadas(2, desde=desde, niveles=(3,) * len(PLANES[asignatura])),
                       nombre_archivo=f"avance_{asignatura}_{numero}_{len(ctx.extras.get('cargas', {}))}.xlsx")
    ctx.extras.setdefault("cargas", {})[(asignatura, numero)] = carga
    return carga


def _rechazar(ctx: Escenario, numero: str, asignatura: str) -> int:
    return C.rechazar(ctx.api.dueno, motivo="SECCION_NO_COINCIDE", asignatura=asignatura, numero=numero,
                      nombre_archivo=f"avance_rechazada_{asignatura}_{numero}.xlsx")


def _activos(ctx: Escenario, numero: str, asignatura: str) -> int:
    return int(ctx.uno("SELECT count(*) FROM acceso.docente_seccion d JOIN acceso.usuario_autorizado u"
                       " USING (usuario_id) WHERE d.seccion_id = %s AND u.activo AND u.rol = 'PROFESOR'",
                       _seccion_id(ctx, numero, asignatura)))


def _sin_datos_de_personas(texto: str) -> None:
    """Ningún porcentaje, nivel, código de ocho cifras, correo ni dato de credencial en el cuerpo (BR-AVANCE-04)."""
    assert not re.search(r"(?<![0-9])[0-9]{8}(?![0-9])", texto), "la respuesta trae un número de ocho cifras"
    for prohibido in ("pct", "porcentaje", "nivel", "logro", "@", "hash", "clave", "estudiante", "nombre_archivo",
                      "subida_por", "profesores"):
        assert prohibido not in texto.lower(), f"la respuesta trae «{prohibido}»"


# Dado

@given("una base desechable del avance de la spec 007 con la vigencia de AMB-2026 en 2026-2 y el plan de medición de "
       "450002 y 450010")
def _base_del_avance(ctx: Escenario) -> None:
    ctx.crear_base("avance")
    for asignatura, pis in PLANES.items():
        registrados = [fila[0] for fila in ctx.filas(
            "SELECT p.codigo FROM abet.plan_medicion pm JOIN abet.pi p USING (pi_id) JOIN abet.asignatura a"
            " USING (asignatura_id) JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id"
            " WHERE a.codigo = %s AND pe.codigo = '2026-2' ORDER BY p.codigo", asignatura)]
        assert registrados == sorted(pis), (asignatura, registrados)
    assert ctx.uno("SELECT count(*) FROM abet.plan_medicion pm JOIN abet.asignatura a USING (asignatura_id)"
                   " WHERE a.codigo = '450020'") == 0


@given(parsers.re(r'"(?P<correo>[^"]+)" con rol "(?P<rol>[A-Z]+)", activo'))
def _activo_con_rol(ctx: Escenario, correo: str, rol: str) -> None:
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, True)]


@given(parsers.re(r'la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" (?P<estado>.+)'))
def _seccion_en_estado(ctx: Escenario, numero: str, asignatura: str, estado: str) -> None:
    """Sección de 2026-2 en el estado que describe el paso, creada si no existe (cargas_de_prueba.seccion)."""
    C.seccion(ctx.api.dueno, asignatura, numero)
    asignada = re.fullmatch(r'asignada a "(?P<correo>[^"]+)"(?P<resto>.*)', estado)
    if asignada:
        _asignar(ctx, asignada["correo"], numero, asignatura)
        resto = asignada["resto"]
        if resto == " con una carga PUBLICADA":
            _publicar(ctx, numero, asignatura)
        elif resto == " con una sola carga RECHAZADA":
            _rechazar(ctx, numero, asignatura)
        else:
            assert resto == " y sin cargas", f"estado sin regla: {estado}"
        return
    docente = f"docente{numero}@example.invalid"
    if estado == "sin ningún usuario activo con rol PROFESOR en acceso.docente_seccion":
        pass
    elif estado == "sin plan de medición y sin profesor":
        assert ctx.uno("SELECT count(*) FROM abet.plan_medicion pm JOIN abet.asignatura a USING (asignatura_id)"
                       " WHERE a.codigo = %s", asignatura) == 0
    elif estado == "con un profesor dado de baja y sin otro activo":
        _profesor(ctx, "docente.baja@example.invalid", activo=False)
        _asignar(ctx, "docente.baja@example.invalid", numero, asignatura)
    elif estado == 'asignada solo a "coordinacion@example.invalid"':
        _asignar(ctx, "coordinacion@example.invalid", numero, asignatura)
    elif estado == "con una carga PUBLICADA y su único profesor dado de baja después":
        _profesor(ctx, docente)
        _asignar(ctx, docente, numero, asignatura)
        _publicar(ctx, numero, asignatura)
        ctx.api.dueno.execute("UPDATE acceso.usuario_autorizado SET activo = false WHERE correo = %s", (docente,))
    elif estado == "con un profesor activo y una carga EN_CURSO":
        _profesor(ctx, docente)
        _asignar(ctx, docente, numero, asignatura)
        archivo = ctx.uno("INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)"
                          " VALUES (%s, %s, NULL, 2) RETURNING archivo_id",
                          C.huella_de(f"en_curso_{numero}.xlsx"), f"en_curso_{numero}.xlsx")
        ctx.api.dueno.execute(
            "INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id,"
            " programa_version, subida_por) SELECT %s, %s, 2, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba',"
            " %s FROM abet.conjunto_reglas cr JOIN abet.carrera c USING (carrera_id)"
            " WHERE cr.version = %s AND c.codigo = 'AMB'",
            (_seccion_id(ctx, numero, asignatura), archivo, ctx.usuario_id(docente), C.BORRADOR))
        assert ctx.cuenta("carga", "seccion_id = %s AND estado = 'EN_CURSO'", _seccion_id(ctx, numero, asignatura)) == 1
    elif estado == "con una carga RECHAZADA y después una PUBLICADA":
        _profesor(ctx, docente)
        _asignar(ctx, docente, numero, asignatura)
        _rechazar(ctx, numero, asignatura)
        _publicar(ctx, numero, asignatura)
    elif estado == "con una carga REEMPLAZADA y la que la reemplaza PUBLICADA":
        _profesor(ctx, docente)
        _asignar(ctx, docente, numero, asignatura)
        anterior = _publicar(ctx, numero, asignatura)
        ctx.extras["cargas"][(asignatura, numero)] = C.reemplazar(ctx.api.dueno, anterior)
        assert ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", anterior) == "REEMPLAZADA"
    else:
        raise AssertionError(f"estado sin regla: {estado}")
    # Ninguna sección de un estado «sin profesor» o «dado de baja» queda con un profesor activo por descuido.
    if "sin" in estado or "baja" in estado or "solo a" in estado:
        assert _activos(ctx, numero, asignatura) == 0


@given(parsers.re(r'la API configurada con PERIODO_VIGENTE "(?P<periodo>[0-9]{4}-[0-9])"'))
def _api_con_vigente(ctx: Escenario, periodo: str) -> None:
    ctx.reiniciar_api(periodo_vigente=periodo)
    ctx.api.cliente()
    assert ctx.api.ajustes.periodo_vigente == periodo


@given(parsers.re(r'la 701 con una carga PUBLICADA inventada, la 702 con una sola carga RECHAZADA y la 703 sin cargas'))
def _cargas_de_quimica(ctx: Escenario) -> None:
    contenido, nombre = ctx.export_de_quimica("701")
    respuesta = A.subir(ctx.sesion("docente701@example.invalid"), ctx.seccion_de("701"), contenido, nombre)
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "PUBLICADA", respuesta.text
    ctx.extras["cargas"] = {("5643", "701"): respuesta.json()["carga_id"]}
    # Un export de la 701, con otros niveles para que su huella sea otra, subido a la 702 declara otra sección, así
    # que la carga queda RECHAZADA.
    contenido, nombre = ctx.export_de_quimica("701", niveles=(4, 1, 3, 2))
    respuesta = A.subir(ctx.sesion("docente702@example.invalid"), ctx.seccion_de("702"), contenido, nombre)
    assert respuesta.json().get("estado") == "RECHAZADA", respuesta.text
    for numero, estados in (("701", ["PUBLICADA"]), ("702", ["RECHAZADA"]), ("703", []), ("704", [])):
        assert [fila[0] for fila in ctx.filas("SELECT estado FROM abet.carga WHERE seccion_id = %s",
                                              ctx.seccion_de(numero))] == estados, numero


# Cuando

@when(parsers.re(r'"(?P<correo>[^"]+)" pide GET (?P<ruta>/api/\S+?)(?P<sin> sin periodo)?'))
def _pide_con_sesion(ctx: Escenario, correo: str, ruta: str, sin: str | None) -> None:
    assert (sin is None) == ("periodo=" in ruta), ruta
    ctx.extras["con_sesion"] = correo
    ctx.respuesta = ctx.sesion(correo).get(ruta)


@when(parsers.re(r'pide GET (?P<ruta>/api/\S+)'))
def _pide(ctx: Escenario, ruta: str) -> None:
    ctx.pedir(ruta)


# Entonces

@then("recibe 200 con Cache-Control no-store y estas secciones, en este orden")
def _estas_secciones(ctx: Escenario, datatable: list[list[str]]) -> None:
    assert datatable[0] == ["asignatura", "seccion", "etapa", "carga_id"]
    esperadas = []
    for asignatura, numero, etapa, carga in datatable[1:]:
        if carga == "null":
            carga_id = None
        else:
            assert carga == f"la de la {numero}", carga
            carga_id = ctx.extras["cargas"][(asignatura, numero)]
        esperadas.append((asignatura, numero, etapa, carga_id))
    assert _filas(ctx) == esperadas
    cuerpo = _cuerpo(ctx)
    assert cuerpo["periodo"] == "2026-2"
    for seccion in cuerpo["secciones"]:
        assert seccion["seccion_id"] == _seccion_id(ctx, seccion["numero"], seccion["asignatura"]["codigo"])
    ctx.extras["primeras"] = esperadas


@then("recibe 200 con Cache-Control no-store")
def _recibe_200(ctx: Escenario) -> None:
    _filas(ctx)


@then(parsers.re(r'el conteo (?:trae|dice) (?P<n>[0-9]+) secciones, (?P<publicada>[0-9]+) PUBLICADA, '
                 r'(?P<rechazo>[0-9]+) CON_RECHAZO, (?P<sin_carga>[0-9]+) SIN_CARGA, (?P<sin_profesor>[0-9]+) '
                 r'SIN_PROFESOR y (?P<sin_plan>[0-9]+) SIN_PLAN'))
def _conteo(ctx: Escenario, n: str, publicada: str, rechazo: str, sin_carga: str, sin_profesor: str,
            sin_plan: str) -> None:
    conteo = _cuerpo(ctx)["conteo"]
    assert list(conteo) == ["secciones", *ETAPAS]
    assert conteo == {"secciones": int(n), "PUBLICADA": int(publicada), "CON_RECHAZO": int(rechazo),
                      "SIN_CARGA": int(sin_carga), "SIN_PROFESOR": int(sin_profesor), "SIN_PLAN": int(sin_plan)}
    # El conteo es el de las secciones que la respuesta trae, no otro.
    filas = _filas(ctx)
    assert conteo["secciones"] == len(filas)
    for etapa in ETAPAS:
        assert conteo[etapa] == sum(1 for fila in filas if fila[2] == etapa), etapa


@then("ninguna sección trae un porcentaje de logro, un nivel ni un dato de estudiantes")
def _sin_cifras(ctx: Escenario) -> None:
    _filas(ctx)
    assert ctx.cuenta("medicion") > 0, "la base no tiene mediciones, así que la prueba no revisaría nada"
    _sin_datos_de_personas(ctx.respuesta.text)


@then(parsers.re(r'la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" trae la etapa (?P<etapa>[A-Z_]+)'))
def _trae_la_etapa(ctx: Escenario, numero: str, asignatura: str, etapa: str) -> None:
    filas = {(fila[0], fila[1]): fila for fila in _filas(ctx)}
    assert (asignatura, numero) in filas, sorted(filas)
    _, _, obtenida, carga_id = filas[(asignatura, numero)]
    assert obtenida == etapa
    publicada = ctx.filas("SELECT carga_id FROM abet.carga WHERE seccion_id = %s AND estado = 'PUBLICADA'",
                          _seccion_id(ctx, numero, asignatura))
    assert carga_id == (publicada[0][0] if publicada else None)
    # Las secciones de los Antecedentes no cambian con la del ejemplo.
    assert [fila[2] for fila in _filas(ctx) if fila[:2] != (asignatura, numero)] == [
        "PUBLICADA", "CON_RECHAZO", "SIN_CARGA", "SIN_PROFESOR", "SIN_PLAN"]


@then(parsers.re(r'recibe 403 con (?:detail "(?P<entre_comillas>[^"]+)"|«(?P<entre_angulares>[^»]+)»)'))
def _recibe_403(ctx: Escenario, entre_comillas: str | None, entre_angulares: str | None) -> None:
    assert _cuerpo(ctx, 403) == {"detail": entre_comillas or entre_angulares}


@then(parsers.re(r'"(?P<correo>[^"]+)" recibe el mismo 403 con el periodo "(?P<periodo>[^"]+)"'))
def _mismo_403(ctx: Escenario, correo: str, periodo: str) -> None:
    respuesta = ctx.sesion(correo).get("/api/avance", params={"periodo": periodo})
    assert respuesta.status_code == 403, respuesta.text
    assert respuesta.json() == ctx.respuesta.json()


@then("la misma ruta sin sesión responde 401")
def _sin_sesion(ctx: Escenario) -> None:
    respuesta = ctx.api.cliente().get("/api/avance", params={"periodo": "2026-2"})
    assert respuesta.status_code == 401, respuesta.text
    assert respuesta.json() == {"detail": "La sesión venció. Ingrese otra vez."}
    assert respuesta.headers["cache-control"] == "no-store"


@then(parsers.re(r'"(?P<correo>[^"]+)" con el periodo "(?P<periodo>[^"]+)" recibe 422 con detail "(?P<detalle>[^"]+)"'))
def _recibe_422(ctx: Escenario, correo: str, periodo: str, detalle: str) -> None:
    respuesta = ctx.sesion(correo).get("/api/avance", params={"periodo": periodo})
    assert respuesta.status_code == 422, respuesta.text
    assert respuesta.json() == {"detail": detalle}


@then(parsers.re(r'recibe 200 con periodo "(?P<periodo>[^"]+)" y las mismas (?P<n>[0-9]+) secciones'))
def _mismas_secciones(ctx: Escenario, periodo: str, n: str) -> None:
    assert _cuerpo(ctx)["periodo"] == periodo
    filas = _filas(ctx)
    assert len(filas) == int(n)
    con_periodo = ctx.sesion(ctx.extras["con_sesion"]).get("/api/avance", params={"periodo": periodo})
    assert con_periodo.status_code == 200, con_periodo.text
    assert con_periodo.json() == ctx.respuesta.json()
    # Refuerzo. Sin periodo la ruta sigue a PERIODO_VIGENTE y no a un valor fijo, así que con 2026-1 responde ese
    # periodo, en el que la coordinación de Ambiental no tiene secciones.
    ctx.reiniciar_api(periodo_vigente="2026-1")
    otro = ctx.sesion(ctx.extras["con_sesion"]).get("/api/avance")
    assert otro.status_code == 200, otro.text
    assert otro.json()["periodo"] == "2026-1" and otro.json()["secciones"] == []


@then(parsers.re(r'(?P<texto>la 70[0-9] viene .+), en ese orden'))
def _en_ese_orden(ctx: Escenario, texto: str) -> None:
    esperadas = re.findall(r"la (70[0-9]) (?:viene )?([A-Z_]+)", texto)
    assert len(esperadas) == 4, texto
    filas = _filas(ctx)
    assert [(fila[0], fila[1], fila[2]) for fila in filas] == [("5643", n, e) for n, e in esperadas]
    cargas = {fila[1]: fila[3] for fila in filas}
    assert cargas == {"701": ctx.extras["cargas"][("5643", "701")], "702": None, "703": None, "704": None}
    assert _cuerpo(ctx)["periodo"] == "2026-1"


@then(parsers.re(r'la respuesta no trae la 410 ni la 411 de "(?P<asignatura>[0-9]+)" ni ningún porcentaje, nivel o '
                 r'código de estudiante'))
def _sin_otro_curso(ctx: Escenario, asignatura: str) -> None:
    ajenas = {_seccion_id(ctx, numero, asignatura) for numero in ("410", "411")}
    cuerpo = _cuerpo(ctx)
    assert all(seccion["asignatura"]["codigo"] == "5643" for seccion in cuerpo["secciones"])
    assert not ajenas & {seccion["seccion_id"] for seccion in cuerpo["secciones"]}
    assert ctx.cuenta("medicion") > 0, "la base no tiene mediciones, así que la prueba no revisaría nada"
    _sin_datos_de_personas(json.dumps(cuerpo, ensure_ascii=False))


@then(parsers.re(r'recibe 200 con secciones vacías(?P<conteo> y el conteo en 0)?'))
def _vacias(ctx: Escenario, conteo: str | None) -> None:
    cuerpo = _cuerpo(ctx)
    assert set(cuerpo) == CLAVES
    assert cuerpo["secciones"] == []
    assert cuerpo["conteo"] == {"secciones": 0, **{etapa: 0 for etapa in ETAPAS}}
    # Las secciones de Química existen en 2026-1 con el plan de IND-2026, así que el vacío lo decide el alcance.
    assert ctx.uno("SELECT count(*) FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                   " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id WHERE a.codigo = '5643'"
                   " AND pe.codigo = '2026-1'") == 4
