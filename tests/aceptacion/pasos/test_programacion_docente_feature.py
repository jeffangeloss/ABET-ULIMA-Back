"""Pasos de programacion_docente.feature (US-55, US-56 y US-57 de la spec 006), con pytest-bdd en español (T031).

El .feature manda. Ningún paso cambia una cifra ni un mensaje para que el escenario pase, y cada «Entonces» se
comprueba contra el informe del guion, la base o la respuesta de la API, sin dobles del sistema bajo prueba.
El guion db/herramientas/cargar_programacion.py corre como proceso aparte con python -I y las variables de libpq
de la copia del escenario, que arma tests/cargas_de_prueba.entorno_de_programacion() en el clúster desechable,
nunca en localhost:5432. El archivo se arma en tmp_path. Los pasos de los Antecedentes y la corrida del guion
viven en el conftest.py de esta carpeta, porque secciones_sin_docente.feature los repite.

El texto «(propuesta)» al final de un paso solo marca que la línea no está fijada en las decisiones de la spec,
y el paso exige la línea completa igual.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path
from typing import Any

from pytest_bdd import given, parsers, scenarios, then, when

Escenario = Any
scenarios("specs/006-programacion-docente/aceptacion/programacion_docente.feature")

CP = sys.modules["cargas_de_prueba"]
PROPUESTA = r"(?: \(propuestas?\))?"
COLUMNA = {"periodo": 0, "asignatura": 1, "sección": 2, "correo": 3, "curso de Blackboard": 4}


def _conftest(ctx: Escenario) -> Any:
    """Módulo conftest.py de esta carpeta, que pytest registra como plugin, para reutilizar sus ayudas."""
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            return plugin
    raise AssertionError("no se encuentra tests/aceptacion/pasos/conftest.py")


def _informe(ctx: Escenario) -> list[str]:
    corrida = ctx.extras.get("corrida_006")
    assert corrida is not None, "el escenario todavía no corrió el guion"
    return corrida.stdout.splitlines()


def _asignados(ctx: Escenario, numero: str, asignatura: str) -> set[str]:
    filas = ctx.filas("SELECT u.correo FROM acceso.docente_seccion d JOIN acceso.usuario_autorizado u USING (usuario_id)"
                      " JOIN abet.seccion s USING (seccion_id) JOIN abet.asignatura a USING (asignatura_id)"
                      " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
                      " WHERE s.numero = %s AND a.codigo = %s AND pe.codigo = '2026-2'", numero, asignatura)
    return {correo for (correo,) in filas}


def _sembrar_seccion(ctx: Escenario, numero: str, asignatura: str, periodo: str, curso: str | None = None) -> None:
    ctx.api.dueno.execute(
        "INSERT INTO abet.seccion (periodo_id, asignatura_id, numero, curso_blackboard)"
        " SELECT pe.periodo_id, a.asignatura_id, %s, %s FROM abet.periodo pe, abet.asignatura a"
        " WHERE pe.codigo = %s AND a.codigo = %s", (numero, curso, periodo, asignatura))


def _sembrar_usuario(ctx: Escenario, correo: str, rol: str = "PROFESOR", activo: bool = True) -> None:
    ctx.api.dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol, activo) VALUES (%s, %s, %s)",
                          (correo, rol, activo))


def _cambiar(ctx: Escenario, fila: int, cambio: str) -> None:
    """Cambia en la fila del archivo solo la columna que el valor indica («la asignatura "999999"», «el correo vacío»)."""
    archivo = _conftest(ctx).archivo_006(ctx)
    coincide = re.fullmatch(r'(?:la|el) (?P<columna>periodo|asignatura|sección|correo|curso de Blackboard)'
                            r'(?: "(?P<valor>[^"]*)"| «(?P<literal>[^»]*)»|(?P<vacio> vacío))', cambio)
    assert coincide is not None, f"No se reconoce el cambio {cambio!r}."
    valor = "" if coincide["vacio"] else coincide["valor"] if coincide["valor"] is not None else coincide["literal"]
    archivo.filas[fila - 2][COLUMNA[coincide["columna"]]] = valor


# Dado, el archivo

@given(parsers.re(r'el archivo base programacion_20262_inventada\.csv en tmp_path con estas filas'))
def _archivo_base(ctx: Escenario, datatable: list[list[str]]) -> None:
    conftest = _conftest(ctx)
    archivo = conftest.archivo_006(ctx)
    assert tuple(datatable[0]) == conftest.ENCABEZADOS_006
    assert [tuple(fila) for fila in datatable[1:]] == list(conftest.ARCHIVO_BASE_006)
    assert archivo.filas == [list(fila) for fila in datatable[1:]]


@given(parsers.re(r'el archivo base con la fila (?P<fila>[0-9]+) cambiada (?:a (?P<cambio>(?:la|el) .+?)'
                  r'|al (?P<al>correo .+?))(?: y la fila (?P<otra>[0-9]+) cambiada a (?P<otro>(?:la|el) .+))?'))
def _archivo_cambiado(ctx: Escenario, fila: str, cambio: str | None, al: str | None, otra: str | None,
                      otro: str | None) -> None:
    _cambiar(ctx, int(fila), cambio or f"el {al}")
    if otra is not None:
        _cambiar(ctx, int(otra), otro)


@given(parsers.re(r'el archivo base con una fila (?P<fila>[0-9]+) que asigna la (?P<numero>[0-9]+) de '
                  r'"(?P<asignatura>[0-9]+)" a "(?P<correo>[^"]+)" (?:con el curso "(?P<curso>[^"]+)"'
                  r'|(?P<sin>sin curso de Blackboard))'))
def _fila_agregada(ctx: Escenario, fila: str, numero: str, asignatura: str, correo: str, curso: str | None,
                   sin: str | None) -> None:
    archivo = _conftest(ctx).archivo_006(ctx)
    assert len(archivo.filas) + 2 == int(fila), f"la fila {fila} no va al final del archivo"
    archivo.filas.append(["2026-2", asignatura, numero, correo, curso or ""])


@given(parsers.re(r'el archivo base sin la columna (?P<columna>[a-z_]+)'))
def _sin_columna(ctx: Escenario, columna: str) -> None:
    archivo = _conftest(ctx).archivo_006(ctx)
    posicion = archivo.encabezados.index(columna)
    del archivo.encabezados[posicion]
    for fila in archivo.filas:
        del fila[posicion]


# Dado, la base

@given(parsers.re(r'la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" en "(?P<periodo>[^"]+)" asignada a '
                  r'"(?P<correo>[^"]+)", sembrada por el dueño de la base'))
def _asignacion_sembrada(ctx: Escenario, numero: str, asignatura: str, periodo: str, correo: str) -> None:
    _sembrar_seccion(ctx, numero, asignatura, periodo)
    _sembrar_usuario(ctx, correo)
    ctx.api.dueno.execute(
        "INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) SELECT u.usuario_id, s.seccion_id"
        " FROM acceso.usuario_autorizado u, abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
        " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
        " WHERE u.correo = %s AND s.numero = %s AND a.codigo = %s AND pe.codigo = %s",
        (correo, numero, asignatura, periodo))
    assert _asignados(ctx, numero, asignatura) == {correo}


@given(parsers.re(r'"(?P<correo>[^"]+)" con rol "(?P<rol>[A-Z]+)" y activo falso, sembrado por el dueño de la base'))
def _usuario_de_baja(ctx: Escenario, correo: str, rol: str) -> None:
    _sembrar_usuario(ctx, correo, rol, activo=False)
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, False)]


@given(parsers.re(r'que la base no tiene plan de medición de "(?P<asignatura>[0-9]+)" en "(?P<periodo>[^"]+)"'))
def _sin_plan(ctx: Escenario, asignatura: str, periodo: str) -> None:
    # Los Antecedentes siembran el plan de 450010, así que el paso lo retira en la copia del escenario, con la
    # conexión del dueño. Ninguna carga lo cita, porque la base de partida no tiene secciones.
    ctx.api.dueno.execute(
        "DELETE FROM abet.plan_medicion pm USING abet.asignatura a, abet.periodo pe"
        " WHERE a.asignatura_id = pm.asignatura_id AND pe.periodo_id = pm.periodo_id AND a.codigo = %s"
        " AND pe.codigo = %s", (asignatura, periodo))
    assert ctx.uno("SELECT count(*) FROM abet.plan_medicion pm JOIN abet.asignatura a USING (asignatura_id)"
                   " JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id WHERE a.codigo = %s AND pe.codigo = %s",
                   asignatura, periodo) == 0


@given(parsers.re(r'un disparador de prueba que rechaza la segunda fila que entra a acceso\.docente_seccion'))
def _disparador(ctx: Escenario) -> None:
    # Vive solo en la copia del escenario, que se borra al terminar, y nunca en un archivo de db/. Una secuencia
    # cuenta las filas, porque nextval() no se deshace con la transacción.
    dueno = ctx.api.dueno
    dueno.execute("CREATE SEQUENCE public.prueba_filas_docente_seccion")
    dueno.execute(
        "CREATE FUNCTION public.prueba_rechaza_la_segunda() RETURNS trigger LANGUAGE plpgsql AS $$"
        " BEGIN IF nextval('public.prueba_filas_docente_seccion') = 2 THEN"
        " RAISE EXCEPTION 'disparador de prueba de la spec 006'; END IF; RETURN NEW; END $$")
    dueno.execute("CREATE TRIGGER prueba_rechaza_la_segunda BEFORE INSERT ON acceso.docente_seccion"
                  " FOR EACH ROW EXECUTE FUNCTION public.prueba_rechaza_la_segunda()")


# Cuando

@when(parsers.re(r'el administrador corre (?P<otra>otra vez )?el guion con (?:el archivo base|ese archivo) y '
                 r'(?P<modo>sin|con) --aplicar'))
def _corre(ctx: Escenario, otra: str | None, modo: str) -> None:
    if otra is not None:
        assert "corrida_006" in ctx.extras, "«otra vez» pide una corrida anterior"
    correr = _conftest(ctx).correr_guion_006
    correr(ctx, aplicar=modo == "con")


@when(parsers.re(r'el administrador corre el guion (?P<caso>sin --periodo|con --periodo 2026-13'
                 r'|con un archivo que no existe|con una copia del archivo base dentro de la copia de trabajo)'))
def _corre_con_argumentos_invalidos(ctx: Escenario, caso: str) -> None:
    conftest = _conftest(ctx)
    tmp_path: Path = ctx.request.getfixturevalue("tmp_path")
    sin_servidor = tmp_path / "sin_servidor"
    sin_servidor.mkdir()
    # PGHOST apunta a una carpeta sin socket y PSQL a un programa que no existe, así que un intento de conexión
    # terminaría con el código 3 y no con el 2 que exige el escenario.
    entorno = CP.entorno_de_programacion(ctx.api.base.nombre, sin_servidor=sin_servidor)
    guion = None
    if caso == "con una copia del archivo base dentro de la copia de trabajo":
        # La copia de trabajo es un repositorio falso en tmp_path, con .git como archivo, como en un worktree, y con
        # su copia del guion y de su SQL, así que la prueba no escribe ningún archivo en el repositorio real.
        repo = tmp_path / "repo_falso"
        herramientas = repo / "db" / "herramientas"
        herramientas.mkdir(parents=True)
        (repo / ".git").write_text("gitdir: /ruta/inventada/.git/worktrees/repo_falso\n", encoding="utf-8")
        for original in (CP.GUION_006, CP.GUION_006.with_suffix(".sql")):
            shutil.copy2(original, herramientas / original.name)
        guion = herramientas / CP.GUION_006.name
        archivo = conftest.escribir_archivo_006(ctx, conftest.archivo_006(ctx), repo)
        argumentos = ("--periodo", "2026-2", "--archivo", str(archivo))
    else:
        archivo = conftest.escribir_archivo_006(ctx, conftest.archivo_006(ctx))
        argumentos = {
            "sin --periodo": ("--archivo", str(archivo)),
            "con --periodo 2026-13": ("--periodo", "2026-13", "--archivo", str(archivo)),
            "con un archivo que no existe": ("--periodo", "2026-2", "--archivo", str(tmp_path / "no_existe.csv")),
        }[caso]
    conftest.correr_guion_006(ctx, *argumentos, entorno=entorno, guion=guion)


@when(parsers.re(r'se envía GET /api/secciones\?periodo=(?P<periodo>[0-9]{4}-[0-9])'))
def _pide_secciones(ctx: Escenario, periodo: str) -> None:
    assert "con_sesion" in ctx.extras, "el escenario todavía no inició ninguna sesión"
    ctx.respuesta = ctx.sesion(ctx.extras["con_sesion"]).get("/api/secciones", params={"periodo": periodo})


# Entonces, el informe y el código

@then(parsers.re(r'el guion termina con código (?P<codigo>[0-9])(?P<sin> sin conectarse a la base)?'))
def _termina_con(ctx: Escenario, codigo: str, sin: str | None) -> None:
    corrida = ctx.extras["corrida_006"]
    assert corrida.returncode == int(codigo), corrida.stdout + corrida.stderr
    if sin is not None:
        # Con el entorno sin servidor, un psql invocado no existe y la corrida habría dado el código 3.
        assert ctx.extras["antes_006"] == _conftest(ctx).tres_tablas_006(ctx)


@then(parsers.re(rf'el informe dice «(?P<linea>[^»]+)»{PROPUESTA}'))
def _informe_dice(ctx: Escenario, linea: str) -> None:
    assert linea in _informe(ctx), _informe(ctx)


@then(parsers.re(rf'el informe termina con «(?P<linea>[^»]+)»{PROPUESTA}'))
def _informe_termina(ctx: Escenario, linea: str) -> None:
    assert _informe(ctx)[-1:] == [linea], _informe(ctx)


@then(parsers.re(rf'el informe dice «(?P<primera>[^»]+)» antes de «(?P<segunda>[^»]+)»{PROPUESTA}'))
def _informe_en_orden(ctx: Escenario, primera: str, segunda: str) -> None:
    informe = _informe(ctx)
    assert primera in informe and segunda in informe, informe
    assert informe.index(primera) < informe.index(segunda), informe


@then(parsers.re(r'ninguna de las tres tablas cambia(?: en la segunda corrida)?'))
def _sin_cambios(ctx: Escenario) -> None:
    antes, ahora = ctx.extras["antes_006"], _conftest(ctx).tres_tablas_006(ctx)
    for tabla in ("seccion", "usuario_autorizado", "docente_seccion"):
        assert ahora[tabla] == antes[tabla], f"{tabla} cambió"


# Entonces, la base

@then(parsers.re(r'abet\.seccion tiene la (?P<a>[0-9]+) de "(?P<asig_a>[0-9]+)" con el curso "(?P<curso_a>[^"]+)" y '
                 r'la (?P<b>[0-9]+) de "(?P<asig_b>[0-9]+)" con el curso "(?P<curso_b>[^"]+)" en "(?P<periodo>[^"]+)"'))
def _secciones_con_curso(ctx: Escenario, a: str, asig_a: str, curso_a: str, b: str, asig_b: str, curso_b: str,
                         periodo: str) -> None:
    filas = ctx.filas("SELECT a.codigo, s.numero, s.curso_blackboard FROM abet.seccion s JOIN abet.asignatura a"
                      " USING (asignatura_id) JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
                      " WHERE pe.codigo = %s ORDER BY a.codigo, s.numero", periodo)
    assert filas == sorted([(asig_a, a, curso_a), (asig_b, b, curso_b)])


@then(parsers.re(r'abet\.seccion tiene la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" en "(?P<periodo>[^"]+)" '
                 r'sin curso de Blackboard'))
def _seccion_sin_curso(ctx: Escenario, numero: str, asignatura: str, periodo: str) -> None:
    assert ctx.filas("SELECT s.curso_blackboard FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                     " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
                     " WHERE s.numero = %s AND a.codigo = %s AND pe.codigo = %s", numero, asignatura, periodo) == [(None,)]


@then(parsers.re(r'abet\.seccion conserva la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)"'))
def _conserva_seccion(ctx: Escenario, numero: str, asignatura: str) -> None:
    antes = [f for f in ctx.extras["antes_006"]["seccion"] if f[3] == numero]
    assert antes, f"la {numero} no estaba en la base antes de la corrida"
    assert ctx.uno("SELECT count(*) FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                   " WHERE s.numero = %s AND a.codigo = %s", numero, asignatura) == 1
    assert all(fila in _conftest(ctx).tres_tablas_006(ctx)["seccion"] for fila in antes)


@then(parsers.re(r'acceso\.usuario_autorizado tiene a "(?P<a>[^"]+)" y a "(?P<b>[^"]+)" con rol "(?P<rol>[A-Z]+)" y activos'))
def _usuarios_nuevos(ctx: Escenario, a: str, b: str, rol: str) -> None:
    for correo in (a, b):
        assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, True)]


@then(parsers.re(r'acceso\.usuario_autorizado tiene una sola fila con el correo "(?P<correo>[^"]+)"'))
def _una_sola_fila(ctx: Escenario, correo: str) -> None:
    assert ctx.uno("SELECT count(*) FROM acceso.usuario_autorizado WHERE lower(btrim(correo)) = %s", correo) == 1
    assert ctx.uno("SELECT count(*) FROM acceso.usuario_autorizado WHERE correo = %s", correo) == 1


@then(parsers.re(r'acceso\.docente_seccion asigna (?P<lista>la [0-9]+ de "[0-9]+" a .+)'))
def _asigna(ctx: Escenario, lista: str) -> None:
    for tramo in re.split(r' y (?=la [0-9]+ de ")', lista):
        partes = re.fullmatch(r'la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" a (?P<correos>"[^"]+"(?: y a "[^"]+")*)',
                              tramo)
        assert partes is not None, f"No se reconoce la asignación {tramo!r}."
        esperados = set(re.findall(r'"([^"]+)"', partes["correos"]))
        assert _asignados(ctx, partes["numero"], partes["asignatura"]) == esperados


@then(parsers.re(r'acceso\.docente_seccion conserva la asignación de la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" '
                 r'a "(?P<correo>[^"]+)"'))
def _conserva_asignacion(ctx: Escenario, numero: str, asignatura: str, correo: str) -> None:
    assert correo in _asignados(ctx, numero, asignatura)
    antes = ctx.extras["antes_006"]["docente_seccion"]
    assert all(fila in _conftest(ctx).tres_tablas_006(ctx)["docente_seccion"] for fila in antes)


@then(parsers.re(r'acceso\.credencial no gana ninguna fila'))
def _sin_credenciales(ctx: Escenario) -> None:
    assert _conftest(ctx).tres_tablas_006(ctx)["credencial"] == ctx.extras["antes_006"]["credencial"] == []


@then(parsers.re(r'el rol de "(?P<correo>[^"]+)" sigue en "(?P<rol>[A-Z]+)"'))
def _rol_igual(ctx: Escenario, correo: str, rol: str) -> None:
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, True)]


@then(parsers.re(r'"(?P<correo>[^"]+)" sigue con activo falso'))
def _sigue_de_baja(ctx: Escenario, correo: str) -> None:
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [("PROFESOR", False)]


# Entonces, la API

@then(parsers.re(r'la API responde 200 con (?P<n>[0-9]+) sección, la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)"'))
def _api_una_seccion(ctx: Escenario, n: str, numero: str, asignatura: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    cuerpo = ctx.respuesta.json()
    assert isinstance(cuerpo, list) and len(cuerpo) == int(n), cuerpo
    assert [(s["numero"], s["asignatura"]["codigo"]) for s in cuerpo] == [(numero, asignatura)]


@then(parsers.re(r'la respuesta no trae la (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)"'))
def _api_sin_seccion(ctx: Escenario, numero: str, asignatura: str) -> None:
    ajena = ctx.api.seccion(numero, asignatura)
    assert all(s["seccion_id"] != ajena for s in ctx.respuesta.json())
