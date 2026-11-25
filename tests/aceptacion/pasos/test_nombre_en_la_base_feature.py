"""Pasos de nombre_en_la_base.feature (US-95 de la spec 010, BR-ACCESO-15), con pytest-bdd en español (T020 y T021).

El .feature manda. Cada «Entonces» se comprueba con una consulta a la base de la copia del escenario o con el
SQLSTATE y el nombre de la restricción que informa la base, nunca con un doble del sistema bajo prueba. Las bases son
las del clúster desechable de tests/cluster_desechable.py, así que ninguna prueba alcanza localhost:5432 ni Neon.

Los nombres de los Ejemplos llevan \\n y \\uXXXX escritos como secuencias de texto, y decodificar() las convierte en el
salto de línea y en el punto de código que nombran antes de insertar. Gherkin ya convierte \\n de una celda en un salto
de línea, y decodificar() deja ese salto como está. Ningún mensaje de falla repite un nombre.

El texto «(propuesta)» al final de un paso solo marca que la línea no está fijada en las decisiones de la spec, y el
paso exige la línea completa igual.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import psycopg
from psycopg.conninfo import make_conninfo
from pytest_bdd import given, parsers, scenario, then, when

Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/010-nombre-del-profesor/aceptacion/nombre_en_la_base.feature"
PRUEBAS = RAIZ / "db" / "pruebas" / "pruebas.sql"
CONTROLES = RAIZ / "db" / "plataforma" / "neon" / "controles_neon.sql"
ROLES_DE_LECTURA = RAIZ / "db" / "plataforma" / "neon" / "crear_roles_lectura.sql"
PROPUESTA = r"(?: \(propuestas?\))?"
VIOLACION_DE_CHECK, SIN_PERMISO = "23514", "42501"


def decodificar(texto: str) -> str:
    """Convierte las secuencias \\n y \\uXXXX de un Ejemplo en el carácter que nombran, y deja lo demás como está."""
    texto = texto.replace("\\n", "\n")
    return re.sub(r"\\u([0-9A-Fa-f]{4})", lambda coincidencia: chr(int(coincidencia.group(1), 16)), texto)


@scenario(FEATURE, "Un usuario sin nombre sigue siendo válido")
def test_un_usuario_sin_nombre_sigue_siendo_valido() -> None:
    """US-95, escenario 1."""


@scenario(FEATURE, "La base acepta un nombre normalizado con tildes y eñes")
def test_la_base_acepta_un_nombre_normalizado() -> None:
    """US-95, escenario 2."""


@scenario(FEATURE, "La base rechaza un nombre que no está normalizado o que no parece un nombre")
def test_la_base_rechaza_un_nombre_que_no_parece_un_nombre() -> None:
    """US-95, escenario 3, con nueve casos."""


@scenario(FEATURE, "Q15 encuentra en acceso solo el correo y el nombre del usuario")
def test_q15_encuentra_solo_el_correo_y_el_nombre() -> None:
    """US-95, escenario 4, FR-002."""


@scenario(FEATURE, "Ninguna tabla de abet gana una columna de nombre")
def test_ninguna_tabla_de_abet_gana_una_columna_de_nombre() -> None:
    """US-95, escenario 5, Q04."""


@scenario(FEATURE, "La aplicación lee el nombre y no lo escribe")
def test_la_aplicacion_lee_el_nombre_y_no_lo_escribe() -> None:
    """US-95, escenario 6, FR-003."""


@scenario(FEATURE, "Los roles de lectura no alcanzan el nombre y el rol de respaldo sí lo lee")
def test_los_roles_de_lectura_no_alcanzan_el_nombre() -> None:
    """US-95, escenario 7, FR-003."""


# Cuando, el dueño de la base inserta

def _insertar(ctx: Escenario, correo: str, rol: str, nombre: str | None) -> None:
    ctx.extras["correo_010"] = correo
    ctx.error_directo = None
    try:
        ctx.api.dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol, nombre) VALUES (%s, %s, %s)",
                              (correo, rol, nombre))
    except psycopg.Error as falla:
        ctx.error_directo = falla


@when(parsers.re(r'el dueño de la base inserta "(?P<correo>[^"]+)" con rol "(?P<rol>[A-Z]+)" y sin nombre'))
def _inserta_sin_nombre(ctx: Escenario, correo: str, rol: str) -> None:
    _insertar(ctx, correo, rol, None)
    assert ctx.error_directo is None, f"la base rechazó un usuario sin nombre con el SQLSTATE {ctx.error_directo.sqlstate}"


@when(parsers.re(r'(?s)el dueño de la base inserta "(?P<correo>[^"]+)" con el nombre "(?P<nombre>.*)"$'))
def _inserta_con_nombre(ctx: Escenario, correo: str, nombre: str) -> None:
    _insertar(ctx, correo, "PROFESOR", decodificar(nombre))


# Entonces, la fila

@then("la fila queda con nombre nulo")
def _fila_con_nombre_nulo(ctx: Escenario) -> None:
    assert ctx.filas("SELECT nombre IS NULL FROM acceso.usuario_autorizado WHERE correo = %s",
                     ctx.extras["correo_010"]) == [(True,)]


@then("acceso.usuario_autorizado tiene la columna nombre de hasta 120 caracteres que admite nulo")
def _columna_de_120_que_admite_nulo(ctx: Escenario) -> None:
    assert ctx.filas("SELECT data_type, character_maximum_length, is_nullable FROM information_schema.columns"
                     " WHERE table_schema = 'acceso' AND table_name = 'usuario_autorizado' AND column_name = 'nombre'"
                     ) == [("character varying", 120, "YES")]


@then("la fila queda con ese nombre")
def _fila_con_ese_nombre(ctx: Escenario) -> None:
    assert ctx.error_directo is None, f"la base rechazó el nombre con el SQLSTATE {ctx.error_directo.sqlstate}"
    guardado = ctx.uno("SELECT nombre FROM acceso.usuario_autorizado WHERE correo = %s", ctx.extras["correo_010"])
    assert guardado == "Profesor Inventado Ángel Muñoz"


@then(parsers.re(r'la base rechaza la fila por (?P<restriccion>ck_usuario_autorizado_nombre)'))
def _fila_rechazada(ctx: Escenario, restriccion: str) -> None:
    falla = ctx.error_directo
    assert isinstance(falla, psycopg.errors.CheckViolation), f"la base respondió {type(falla).__name__}"
    assert falla.sqlstate == VIOLACION_DE_CHECK
    assert falla.diag.constraint_name == restriccion, falla.diag.constraint_name
    assert ctx.uno("SELECT count(*) FROM acceso.usuario_autorizado WHERE correo = %s", ctx.extras["correo_010"]) == 0


# Q04 y Q15

def _consulta_de_q04() -> str:
    texto = CONTROLES.read_text(encoding="utf-8")
    bloque = re.search(r"\\echo 'Q04\.[^\n]*\n(.*?);\n\\set q04 :ROW_COUNT", texto, flags=re.S)
    assert bloque is not None, "controles_neon.sql no trae Q04"
    return bloque.group(1).strip()


def _conftest(ctx: Escenario) -> Any:
    """Módulo conftest.py de esta carpeta, que pytest registra como plugin, para reutilizar sus ayudas."""
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            return plugin
    raise AssertionError("no se encuentra tests/aceptacion/pasos/conftest.py")


FILTRO_DE_Q15 = ("SELECT string_agg(table_name || '.' || column_name, ',' ORDER BY table_name, column_name)"
                 " FROM information_schema.columns WHERE table_schema = 'acceso'"
                 " AND (column_name ~ '(apellido|first_name|last_name|correo|email|telefono|dni)'"
                 " OR column_name LIKE '%nombre%')")


@when("corre Q15")
def _corre_q15(ctx: Escenario) -> None:
    ctx.extras["q15"] = _conftest(ctx).correr_q15(ctx)


@then("el filtro sobre acceso encuentra exactamente usuario_autorizado.correo y usuario_autorizado.nombre")
def _q15_encuentra_correo_y_nombre(ctx: Escenario) -> None:
    corrida = ctx.extras["q15"]
    assert corrida.returncode == 0, corrida.stderr
    assert "ok Q15" in corrida.stderr, corrida.stderr
    assert ctx.uno(FILTRO_DE_Q15) == "usuario_autorizado.correo,usuario_autorizado.nombre"


@then(parsers.re(r'con una columna nombre_contacto agregada a acceso\.credencial Q15 falla con «(?P<mensaje>[^»]+)»'
                 + PROPUESTA))
def _q15_falla_con_otra_columna(ctx: Escenario, mensaje: str) -> None:
    ctx.api.dueno.execute("ALTER TABLE acceso.credencial ADD COLUMN nombre_contacto varchar(120)")
    corrida = _conftest(ctx).correr_q15(ctx)
    assert corrida.returncode != 0, "Q15 pasó con una columna de nombre en acceso.credencial"
    assert f"FALLA Q15: {mensaje.removeprefix('FALLA Q15: ')}" in corrida.stderr, corrida.stderr


@when("corre la consulta de control Q04")
def _corre_q04(ctx: Escenario) -> None:
    ctx.extras["q04"] = ctx.filas(_consulta_de_q04())


@then("devuelve 0 filas")
def _devuelve_cero_filas(ctx: Escenario) -> None:
    assert ctx.extras["q04"] == []


# La aplicación y los roles de lectura

def _con_el_rol(ctx: Escenario, rol: str) -> psycopg.Connection:
    return ctx.pila.enter_context(psycopg.connect(make_conninfo(ctx.api.base.conexion, user=rol), autocommit=True))


def _sqlstate(conexion: psycopg.Connection, consulta: str, *parametros: object) -> str | None:
    """SQLSTATE con el que la base responde a la sentencia, o None si la acepta. Una sentencia aceptada se deshace."""
    conexion.autocommit = False
    try:
        conexion.execute(consulta, parametros or None)
    except psycopg.Error as falla:
        return falla.sqlstate
    finally:
        conexion.rollback()
        conexion.autocommit = True
    return None


@given("el rol abet_app creado con crear_rol_app.sql")
def _rol_abet_app(ctx: Escenario) -> None:
    rol = ctx.api.base.rol_app
    assert rol is not None
    assert ctx.uno("SELECT count(*) FROM pg_roles WHERE rolname = %s", rol) == 1
    ctx.extras["rol_app_010"] = rol


@when("abet_app consulta el nombre de acceso.usuario_autorizado")
def _app_consulta_el_nombre(ctx: Escenario) -> None:
    conexion = _con_el_rol(ctx, ctx.extras["rol_app_010"])
    ctx.extras["app_010"] = conexion
    ctx.extras["lectura_de_la_app"] = _sqlstate(conexion, "SELECT correo, nombre FROM acceso.usuario_autorizado")


@then("la consulta responde sin error")
def _consulta_sin_error(ctx: Escenario) -> None:
    assert ctx.extras["lectura_de_la_app"] is None, f"SQLSTATE {ctx.extras['lectura_de_la_app']}"


@then(parsers.re(r'un UPDATE de nombre de abet_app responde con el SQLSTATE (?P<codigo>[0-9]{5})'))
def _app_no_actualiza_el_nombre(ctx: Escenario, codigo: str) -> None:
    assert codigo == SIN_PERMISO
    consulta = "SELECT nombre FROM acceso.usuario_autorizado WHERE correo = 'docente410@example.invalid'"
    antes = ctx.uno(consulta)
    assert _sqlstate(ctx.extras["app_010"], "UPDATE acceso.usuario_autorizado SET nombre = 'Profesor Inventado Uno'"
                     " WHERE correo = 'docente410@example.invalid'") == codigo
    # El nombre de las semillas (T022) o su ausencia queda como estaba.
    assert ctx.uno(consulta) == antes != "Profesor Inventado Uno"


@then(parsers.re(r'un INSERT con nombre de abet_app responde con el SQLSTATE (?P<codigo>[0-9]{5})'))
def _app_no_inserta_con_nombre(ctx: Escenario, codigo: str) -> None:
    antes = ctx.uno("SELECT count(*) FROM acceso.usuario_autorizado")
    assert _sqlstate(ctx.extras["app_010"], "INSERT INTO acceso.usuario_autorizado (correo, rol, nombre)"
                     " VALUES ('docente733@example.invalid', 'PROFESOR', 'Profesor Inventado Uno')") == codigo
    assert ctx.uno("SELECT count(*) FROM acceso.usuario_autorizado") == antes


@given("los roles de crear_roles_lectura.sql creados en la copia")
def _roles_de_lectura(ctx: Escenario) -> None:
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            plugin.correr_guion(ctx.api.dueno, ROLES_DE_LECTURA, {})
            return
    raise AssertionError("no se encuentra tests/aceptacion/pasos/conftest.py")


@when("abet_lectura y powerbi_lectura consultan acceso.usuario_autorizado")
def _lectores_consultan(ctx: Escenario) -> None:
    consulta = "SELECT nombre FROM acceso.usuario_autorizado"
    # abet_lectura es un rol de grupo sin inicio de sesión, así que se asume con SET ROLE desde el dueño de la copia.
    rol = ctx.pila.enter_context(psycopg.connect(ctx.api.base.conexion, autocommit=True))
    rol.execute("SET ROLE abet_lectura")
    ctx.extras["lectores_010"] = {"abet_lectura": _sqlstate(rol, consulta),
                                  "powerbi_lectura": _sqlstate(_con_el_rol(ctx, "powerbi_lectura"), consulta)}


@then(parsers.re(r'ambos reciben el SQLSTATE (?P<codigo>[0-9]{5})'))
def _ambos_sin_permiso(ctx: Escenario, codigo: str) -> None:
    assert ctx.extras["lectores_010"] == {"abet_lectura": codigo, "powerbi_lectura": codigo}


@then("abet_respaldo lee la columna nombre sin error")
def _respaldo_lee_el_nombre(ctx: Escenario) -> None:
    assert _sqlstate(_con_el_rol(ctx, "abet_respaldo"), "SELECT correo, nombre FROM acceso.usuario_autorizado") is None
