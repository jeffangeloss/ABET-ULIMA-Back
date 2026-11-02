"""Arnés común de los pasos de aceptación en español (T050 a T052 de specs/001-mvp-carga-r17/tasks.md).

Los .feature de specs/001-mvp-carga-r17/aceptacion/ se ejecutan con pytest-bdd 9. Este archivo reúne
lo que repiten sus Antecedentes y sus escenarios.

- Las bases. Cada módulo de pasos arma una plantilla por variante (los datos de 2026-2, esos datos con
  los de varias secciones, y esos datos con la guardia de Neon) en el clúster desechable de
  tests/conftest.py, y cada escenario trabaja en una copia propia que se borra al terminar. Ninguna
  prueba alcanza el clúster de la Mac, porque la fixture cluster_postgres y tests/base_desechable.py
  mantienen sus guardias.
- La API. El TestClient de FastAPI se conecta con el rol de la aplicación, como en Neon, y la revisión
  de lo escrito usa la conexión del dueño de la base. Las contraseñas y SESION_SECRETO se generan al
  vuelo en tests/api_de_prueba.py y no se escriben en ningún archivo.
- Los pasos. Cada «Entonces» se comprueba con una consulta a la base, con la respuesta de la API o con
  el archivo descargado, nunca con un doble del sistema bajo prueba. Los pasos que solo usa un .feature
  viven en su propio módulo, y los que repiten varios viven aquí.
- El estado de un escenario vive en la fixture ctx (clase Escenario), que guarda la respuesta, el
  conteo previo de las tablas de la carga, el archivo en uso y la carga a la que se refiere «esa carga».
- Las etiquetas. Todo escenario con la etiqueta @corte2 se omite con su razón, porque la spec lo deja
  para el corte 2 y el Back del corte 1 todavía no lo implementa.

Los exports modificados se arman en memoria con scripts/generar_exports_inventados.py y nunca se
versionan.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import re
import secrets
import sys
import zipfile
from collections.abc import Iterator
from contextlib import ExitStack
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from pytest_bdd import given, parsers, then, when

from abet_carga.carga import Configuracion

RAIZ = Path(__file__).resolve().parents[3]
CONTROLES = RAIZ / "db" / "plataforma" / "neon" / "controles_neon.sql"
GUARDIA_SQL = "db/plataforma/neon/guardia_datos_inventados.sql"
VARIAS_SQL = RAIZ / "db" / "datos" / "varias_secciones_2026_2_inventado.sql"
ASIGNATURA = "450002"
RAZON_CORTE_2 = "Escenario del corte 2 (@corte2), todavía sin implementar en el Back del corte 1."


def _modulo_de_pruebas(nombre: str) -> ModuleType:
    """Módulo de tests/ cargado por su ruta, porque tests/ no es un paquete."""
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, RAIZ / "tests" / f"{nombre}.py")
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


A = _modulo_de_pruebas("api_de_prueba")


# Omisión de los escenarios del corte 2

def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "tests/aceptacion/pasos" in item.nodeid and item.get_closest_marker("corte2") is not None:
            item.add_marker(pytest.mark.skip(reason=RAZON_CORTE_2))


# Resumen de los pasos que no comprueban todo en el Back

PROPIEDADES_A_LA_VISTA = ("criterio_relajado", "delegado_a_vitest", "sin_casos", "valor_buscado")


def pytest_terminal_summary(terminalreporter: Any) -> None:
    """Lista, al final del informe, los escenarios con un criterio relajado, delegado al Front o sin casos.

    Esas marcas viven en las propiedades de cada prueba y el informe normal no las muestra, así que este resumen
    impide que un escenario aprobado esconda que su «Entonces» se comprobó de otro modo o en otra suite.
    """
    lineas = []
    for reportes in terminalreporter.stats.values():
        for reporte in reportes:
            if getattr(reporte, "when", None) != "call":
                continue
            for nombre, valor in getattr(reporte, "user_properties", ()):
                if nombre in PROPIEDADES_A_LA_VISTA:
                    lineas.append(f"{nombre}  {reporte.nodeid}  {valor}")
    if lineas:
        terminalreporter.section("pasos de aceptación con criterio relajado, delegado o sin casos")
        for linea in sorted(set(lineas)):
            terminalreporter.line(linea)


# Bases de los escenarios

VARIANTES = {
    "periodo": {},
    "varias": {"despues": (VARIAS_SQL,)},
    "guardia": {"guardia": True},
}


class Plantillas:
    """Plantillas de base de la sesión, una por variante, que cada escenario copia con CREATE DATABASE."""

    def __init__(self, base_desechable: ModuleType, pila: ExitStack) -> None:
        self.base_desechable, self.pila, self.creadas = base_desechable, pila, {}

    def de(self, variante: str) -> Any:
        if variante not in self.creadas:
            self.creadas[variante] = self.pila.enter_context(self.base_desechable.abierta(**VARIANTES[variante]))
        return self.creadas[variante]

    def copia(self, variante: str, pila: ExitStack) -> Any:
        """Copia propia de la plantilla, con el rol de la aplicación de la plantilla, que la pila borra al cerrarse."""
        plantilla = self.de(variante)
        nombre = f"{plantilla.nombre}_{secrets.token_hex(3)}"
        with psycopg.connect(make_conninfo(plantilla.conexion, dbname="postgres"), autocommit=True) as servidor:
            servidor.execute(sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(sql.Identifier(nombre),
                                                                              sql.Identifier(plantilla.nombre)))
        copia = self.base_desechable.BaseDesechable(nombre, make_conninfo(plantilla.conexion, dbname=nombre),
                                                    None, None)
        pila.callback(self.base_desechable.borrar, copia)
        return replace(copia, rol_app=plantilla.rol_app)


@pytest.fixture(scope="module")
def plantillas(base_desechable: ModuleType) -> Iterator[Plantillas]:
    """Plantillas de base de un módulo de pasos, que se borran al terminarlo.

    El alcance es el módulo y no la sesión, como el de la plantilla de tests/api_de_prueba.py, porque
    tests/test_base_desechable.py exige que no quede ninguna base abet_demo_ viva mientras corre.
    """
    with ExitStack() as pila:
        yield Plantillas(base_desechable, pila)


# Estado de un escenario

@dataclass
class Escenario:
    """Estado compartido por los pasos de un escenario, con su base, su API y lo que va pasando."""

    plantillas: Plantillas
    request: pytest.FixtureRequest
    generador: ModuleType
    pila: ExitStack = field(default_factory=ExitStack)
    api: Any = None
    profesor: str | None = None
    sesiones: dict[str, Any] = field(default_factory=dict)
    respuesta: Any = None
    antes: dict[str, int] = field(default_factory=dict)
    archivo: tuple[bytes, str] | None = None
    ultimo: tuple[bytes, str] | None = None
    carga_id: int | None = None
    carga_previa: int | None = None
    directa: psycopg.Connection | None = None
    error_directo: psycopg.Error | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    # Base y API

    def crear_base(self, variante: str) -> None:
        base = self.plantillas.copia(variante, self.pila)
        dueno = self.pila.enter_context(psycopg.connect(base.conexion, autocommit=True))
        self.api = A.Api(base=base, dueno=dueno, ajustes=A.ajustes_de(base), pila=self.pila)

    def configurar_api(self, periodo: str, reglas: str, guardia: str) -> None:
        carga = Configuracion.desde_entorno({"CONJUNTO_REGLAS": reglas, "GUARDIA_DATOS_INVENTADOS": guardia})
        self.api.ajustes = replace(A.ajustes_de(self.api.base), periodo_vigente=periodo, carga=carga)

    def reiniciar_api(self, **cambios: Any) -> None:
        """Arranca la API otra vez con otros ajustes y vuelve a iniciar la sesión de quien ya la tenía."""
        self.api.ajustes = replace(self.api.ajustes, **cambios)
        quienes = list(self.sesiones)
        self.sesiones.clear()
        for correo in quienes:
            self.sesion(correo)

    def sesion(self, correo: str) -> Any:
        if correo not in self.sesiones:
            self.sesiones[correo] = self.api.sesion(correo)
        return self.sesiones[correo]

    # Consultas a la base con la conexión del dueño

    def uno(self, consulta: str, *parametros: object) -> Any:
        return self.api.uno(consulta, *parametros)

    def filas(self, consulta: str, *parametros: object) -> list[tuple[Any, ...]]:
        return self.api.dueno.execute(consulta, parametros or None).fetchall()

    def cuenta(self, tabla: str, donde: str = "true", *parametros: object) -> int:
        consulta = sql.SQL("SELECT count(*) FROM abet.{} WHERE ").format(sql.Identifier(tabla)) + sql.SQL(donde)
        return int(self.api.dueno.execute(consulta, parametros or None).fetchone()[0])

    def seccion_id(self, numero: str = "410", asignatura: str = ASIGNATURA) -> int:
        return int(self.api.seccion(numero, asignatura))

    def usuario_id(self, correo: str) -> int:
        return int(self.uno("SELECT usuario_id FROM acceso.usuario_autorizado WHERE correo = %s", correo))

    def columna_id(self, carga_id: int, pi: str) -> int:
        return int(self.uno("SELECT carga_columna_id FROM abet.carga_columna WHERE carga_id = %s AND pi_codigo = %s",
                            carga_id, pi))

    # Subidas

    def subir(self, correo: str, contenido: bytes, nombre: str, seccion: str = "410",
              asignatura: str = ASIGNATURA, **opciones: Any) -> Any:
        """POST del export con la sesión de correo. Guarda el conteo previo, la respuesta y la carga que trae."""
        cliente = self.sesion(correo)
        seccion_id = self.seccion_id(seccion, asignatura)
        self.antes = self.api.conteos()
        self.carga_id = None
        self.respuesta = A.subir(cliente, seccion_id, contenido, nombre, **opciones)
        self.ultimo = (contenido, nombre)
        cuerpo = self.cuerpo()
        if isinstance(cuerpo, dict) and isinstance(cuerpo.get("carga_id"), int):
            self.carga_id = cuerpo["carga_id"]
        return self.respuesta

    def cuerpo(self) -> Any:
        assert self.respuesta is not None, "el escenario todavía no tiene respuesta"
        return self.respuesta.json()

    def de_inventados(self, nombre: str) -> bytes:
        return A.archivo(nombre)

    def intentar(self, consulta: str, *parametros: object) -> None:
        """Ejecuta la sentencia por la conexión directa y guarda el error de la base, si la base la rechaza."""
        self.error_directo = None
        try:
            self.directa.execute(consulta, parametros or None)
        except psycopg.Error as falla:
            self.error_directo = falla

    def huella(self, contenido: bytes) -> str:
        return hashlib.sha256(contenido).hexdigest()

    def copia_de(self, texto: str) -> tuple[bytes, str]:
        """Archivo que describe una frase como «una copia de "X" con ...». Devuelve sus bytes y su nombre."""
        return armar_archivo(self, texto)


@pytest.fixture
def ctx(request: pytest.FixtureRequest, plantillas: Plantillas, generador: ModuleType) -> Iterator[Escenario]:
    escenario = Escenario(plantillas=plantillas, request=request, generador=generador)
    with escenario.pila:
        yield escenario


# Copias de un export, armadas en memoria

def _zip(partes: list[tuple[str, bytes, int]]) -> bytes:
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w") as libro:
        for nombre, contenido, compresion in partes:
            libro.writestr(zipfile.ZipInfo(nombre, (2026, 10, 30, 0, 0, 0)), contenido, compress_type=compresion)
    return salida.getvalue()


def con_partes(datos: bytes, extra: list[tuple[str, bytes, int]]) -> bytes:
    """Copia del libro con sus partes y las partes extra al final."""
    with zipfile.ZipFile(io.BytesIO(datos)) as libro:
        propias = [(p.filename, libro.read(p), p.compress_type) for p in libro.infolist()]
    return _zip([*propias, *extra])


def contenido_que_se_infla(megas: int) -> bytes:
    """Bloques de 128 bytes elegidos entre 64 patrones, con proporción de compresión cercana a 25."""
    import random

    azar = random.Random(20262)
    patrones = [azar.randbytes(128) for _ in range(64)]
    return b"".join(azar.choice(patrones) for _ in range(megas * 1_048_576 // 128))


def abierto_y_guardado_otra_vez(datos: bytes) -> bytes:
    """Abre el libro con openpyxl y lo guarda de nuevo, como Excel, con las mismas celdas y otros bytes."""
    from openpyxl import load_workbook

    libro = load_workbook(io.BytesIO(datos))
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _valor_de_celda(texto: str) -> object:
    """Entero si el texto es un entero (como en un export real), y el texto tal cual en otro caso."""
    return int(texto) if re.fullmatch(r"-?[0-9]+", texto) else texto


def _export(ctx: Escenario, nombre: str) -> Any:
    return ctx.generador.leer_export(ctx.de_inventados(nombre))


def _con_celda(ctx: Escenario, nombre: str, fila: str, columna: str, valor: object) -> bytes:
    export = ctx.generador.con_celda(_export(ctx, nombre), int(fila), columna, valor)
    return bytes(ctx.generador.a_bytes(export))


# Cada regla es (expresión del cambio, función). La función recibe el escenario, el nombre del archivo base y
# los grupos de la expresión, y devuelve los bytes de la copia y, si cambia, el nombre con que se sube.
def _celda_username(ctx: Escenario, nombre: str, v: str, f: str) -> tuple[bytes, str]:
    return _con_celda(ctx, nombre, f, "Username", None if v == "vacío" else int(v)), nombre


def _celda_pi(ctx: Escenario, nombre: str, pi: str, v: str, f: str) -> tuple[bytes, str]:
    return _con_celda(ctx, nombre, f, pi, _valor_de_celda(v)), nombre


def _pi_vacio(ctx: Escenario, nombre: str, pi: str, f: str) -> tuple[bytes, str]:
    return _con_celda(ctx, nombre, f, pi, None), nombre


def _columna_mas(ctx: Escenario, nombre: str, enc: str) -> tuple[bytes, str]:
    export = _export(ctx, nombre)
    return bytes(ctx.generador.a_bytes(ctx.generador.con_columna(export, enc, [3] * len(export.filas)))), nombre


def _nivel_en_todas(ctx: Escenario, nombre: str, v: str, pi: str, n: str) -> tuple[bytes, str]:
    export = _export(ctx, nombre)
    assert len(export.filas) == int(n), f"el export trae {len(export.filas)} filas de datos y no {n}"
    for fila in range(2, len(export.filas) + 2):
        export = ctx.generador.con_celda(export, fila, pi, _valor_de_celda(v))
    return bytes(ctx.generador.a_bytes(export)), nombre


def _hoja(ctx: Escenario, nombre: str, hoja: str, otro: str | None) -> tuple[bytes, str]:
    export = ctx.generador.con_hoja(_export(ctx, nombre), hoja)
    return bytes(ctx.generador.a_bytes(export)), otro or nombre


def _sin_filas(ctx: Escenario, nombre: str) -> tuple[bytes, str]:
    return bytes(ctx.generador.a_bytes(ctx.generador.sin_filas(_export(ctx, nombre)))), nombre


def _sin_pi(ctx: Escenario, nombre: str, pi: str) -> tuple[bytes, str]:
    return bytes(ctx.generador.a_bytes(ctx.generador.sin_columnas(_export(ctx, nombre), pi))), nombre


def _sin_codigos(ctx: Escenario, nombre: str) -> tuple[bytes, str]:
    export = ctx.generador.sin_columnas(_export(ctx, nombre), "Username", "Student ID")
    return bytes(ctx.generador.a_bytes(export)), nombre


def _pi_repetido(ctx: Escenario, nombre: str, enc: str) -> tuple[bytes, str]:
    return _columna_mas(ctx, nombre, enc)


REGLAS_DE_COPIA: list[tuple[str, Any]] = [
    (r'con el Username (?P<v>vacío|[0-9]+) en la fila (?P<f>[0-9]+)', _celda_username),
    (r'cuya columna (?P<pi>[0-9]\.[0-9]) trae "(?P<v>[^"]*)" en la fila (?P<f>[0-9]+)', _celda_pi),
    (r'con la columna (?P<pi>[0-9]\.[0-9]) vacía en la fila (?P<f>[0-9]+)', _pi_vacio),
    (r'con una columna más "(?P<enc>[^"]+)"', _columna_mas),
    (r'con un (?P<v>-?[0-9]+) en la columna (?P<pi>[0-9]\.[0-9]) de las (?P<n>[0-9]+) filas de datos', _nivel_en_todas),
    (r'con la hoja renombrada "(?P<hoja>[^"]+)"(?: y el nombre "(?P<otro>[^"]+)")?', _hoja),
    (r'con el encabezado y ninguna fila de datos', _sin_filas),
    (r'sin la columna del PI (?P<pi>[0-9]\.[0-9])', _sin_pi),
    (r'sin la columna (?P<pi>[0-9]\.[0-9])', _sin_pi),
    (r'sin las columnas Username ni Student ID', _sin_codigos),
    (r'con una segunda columna "(?P<enc>[^"]+)"', _pi_repetido),
    (r'cortada a la mitad de sus bytes',
     lambda ctx, nombre: (ctx.generador.cortar_a_la_mitad(ctx.de_inventados(nombre)), nombre)),
    (r'protegida con contraseña', lambda ctx, nombre: (ctx.generador.contenedor_ole_cifrado(), nombre)),
    (r'con la parte xl/vbaProject\.bin',
     lambda ctx, nombre: (con_partes(ctx.de_inventados(nombre), [("xl/vbaProject.bin", b"inventado", 8)]), nombre)),
    (r'con una parte xl/externalLinks/',
     lambda ctx, nombre: (con_partes(ctx.de_inventados(nombre),
                                     [("xl/externalLinks/externalLink1.xml", b"<externalLink/>", 8)]), nombre)),
    (r'abierta y guardada otra vez, con las mismas celdas y otros bytes',
     lambda ctx, nombre: (abierto_y_guardado_otra_vez(ctx.de_inventados(nombre)), nombre)),
]


def armar_archivo(ctx: Escenario, texto: str) -> tuple[bytes, str]:
    """Bytes y nombre de lo que dice una frase de los .feature sobre un archivo de prueba."""
    if (pdf := re.fullmatch(r'(?:un PDF inventado de una página con el nombre|el mismo PDF con el nombre) "([^"]+)"',
                            texto)):
        return ctx.generador.pdf_inventado(), pdf.group(1)
    if re.fullmatch(r'un \.xlsx inventado de 1,2 MB con códigos 99000001 a 99000011', texto):
        return ctx.de_inventados(A.CORRECTO).ljust(1_200_000, b"\0"), "inventado_1_2_mb.xlsx"
    if re.fullmatch(r'un \.xlsx inventado de menos de 1 MB cuyo contenido descomprimido supera los 20 MB', texto):
        contenido = con_partes(ctx.de_inventados(A.CORRECTO),
                               [("xl/media/inflado.bin", contenido_que_se_infla(22), 8)])
        assert len(contenido) < 1_048_576
        return contenido, "inflado.xlsx"
    copia = re.fullmatch(r'una copia de "(?P<base>[^"]+)" (?P<cambio>.+)', texto)
    assert copia is not None, f"No se reconoce la descripción del archivo {texto!r}."
    for expresion, funcion in REGLAS_DE_COPIA:
        coincide = re.fullmatch(expresion, copia["cambio"])
        if coincide:
            return funcion(ctx, copia["base"], **coincide.groupdict())
    raise AssertionError(f"No se reconoce el cambio {copia['cambio']!r} de la copia.")


# Antecedentes

@given(parsers.re(r'una base PostgreSQL 18 desechable con las migraciones V1_01 a V1_09(?P<resto>.*)'))
def _base_desechable(ctx: Escenario, resto: str) -> None:
    con_varias = "varias_secciones_2026_2_inventado.sql" in resto
    guardia = ctx.request.node.get_closest_marker("guardia_en_base") is not None
    ctx.crear_base("varias" if con_varias else "guardia" if guardia else "periodo")
    assert ctx.uno("SHOW server_version_num").startswith("18"), "la base desechable no es PostgreSQL 18"
    assert ctx.uno("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'acceso'"
                   " AND table_name = 'usuario_autorizado'") == 1, "falta la migración V1_09"
    assert ctx.uno("SELECT count(*) FROM abet.periodo WHERE codigo = '2026-2'") == 1, "faltan los datos de 2026-2"
    if con_varias:
        assert ctx.uno("SELECT count(*) FROM acceso.usuario_autorizado WHERE correo = %s", A.VARIAS_CORREO) == 1


@given(parsers.re(r'la API conectada a esa base con el rol abet_app y configurada con PERIODO_VIGENTE "(?P<periodo>[^"]+)", '
                  r'CONJUNTO_REGLAS "(?P<reglas>[^"]+)" y GUARDIA_DATOS_INVENTADOS "(?P<guardia>[01])"'))
def _api_conectada(ctx: Escenario, periodo: str, reglas: str, guardia: str) -> None:
    ctx.configurar_api(periodo, reglas, guardia)
    # Crear el cliente arranca la API, y su arranque se niega a seguir con un rol de administración.
    ctx.api.cliente()
    assert conninfo_to_dict(ctx.api.ajustes.database_url)["user"] == ctx.api.base.rol_app
    assert ctx.api.ajustes.carga.guardia_datos_inventados is (guardia == "1")


@given(parsers.re(r'plan_medicion registra los PI (?P<pis>[0-9.]+(?:, [0-9.]+)* y [0-9.]+) para la asignatura '
                  r'"(?P<asignatura>[0-9]+)" en "(?P<periodo>[^"]+)"'))
def _plan_registrado(ctx: Escenario, pis: str, asignatura: str, periodo: str) -> None:
    esperados = sorted(re.findall(r"[0-9]\.[0-9]+", pis))
    registrados = [fila[0] for fila in ctx.filas(
        "SELECT p.codigo FROM abet.plan_medicion pm JOIN abet.pi p USING (pi_id)"
        " JOIN abet.asignatura a USING (asignatura_id) JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id"
        " WHERE a.codigo = %s AND pe.codigo = %s ORDER BY p.codigo", asignatura, periodo)]
    assert registrados == esperados


@given(parsers.re(r'(?:que )?"(?P<correo>[^"]+)" tiene la sesión iniciada con rol "(?P<rol>[A-Z]+)"'
                  r'(?: y acceso\.docente_seccion le asigna la sección (?P<numero>[0-9]+)'
                  r'(?: de "(?P<asignatura>[0-9]+)" en "(?P<periodo>[^"]+)")?)?'))
def _sesion_iniciada(ctx: Escenario, correo: str, rol: str, numero: str | None, asignatura: str | None,
                     periodo: str | None) -> None:
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, True)]
    if numero is not None:
        seccion = ctx.seccion_id(numero, asignatura or ASIGNATURA)
        assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion WHERE usuario_id = %s AND seccion_id = %s",
                       ctx.usuario_id(correo), seccion) == 1
    ctx.sesion(correo)
    if rol == "PROFESOR" and ctx.profesor is None:
        ctx.profesor = correo


@given(parsers.re(r'la sección (?P<numero>[0-9]+) no tiene ninguna carga'))
def _seccion_sin_carga(ctx: Escenario, numero: str) -> None:
    assert ctx.cuenta("carga", "seccion_id = %s", ctx.seccion_id(numero)) == 0


# Archivos y subidas previas

@given(parsers.re(r'(?P<que>una copia de "[^"]+" .+|un PDF inventado de una página con el nombre "[^"]+"'
                  r'|el mismo PDF con el nombre "[^"]+"|un \.xlsx inventado de .+)'))
def _archivo_descrito(ctx: Escenario, que: str) -> None:
    ctx.archivo = ctx.copia_de(que)


def _subido_antes(ctx: Escenario, quien: str, que: str, numero: str) -> Any:
    contenido, nombre = (ctx.copia_de(que) if que.startswith("una copia") else
                         (ctx.de_inventados(que.strip('"')), que.strip('"')))
    respuesta = ctx.subir(quien, contenido, nombre, numero)
    assert respuesta.status_code == 201, respuesta.text
    ctx.carga_previa = ctx.carga_id
    return respuesta


@given(parsers.re(r'que (?P<que>"[^"]+"|una copia de "[^"]+" .+?) está subid[oa](?: por "(?P<quien>[^"]+)")? '
                  r'a la sección (?P<numero>[0-9]+)(?: con respuesta 201(?: y su carga_id)?'
                  r'| y su carga está "(?P<estado>[A-Z]+)" con (?P<motivo>[A-Z_]+))'))
def _subido_a_la_seccion(ctx: Escenario, que: str, quien: str | None, numero: str, estado: str | None,
                         motivo: str | None) -> None:
    respuesta = _subido_antes(ctx, quien or ctx.profesor, que, numero)
    if estado is not None:
        assert respuesta.json()["estado"] == estado
        assert ctx.cuenta("rechazo_fila", "carga_id = %s AND motivo = %s", ctx.carga_previa, motivo) >= 1
    ctx.antes = ctx.api.conteos()


# Cuando, subidas

@when(parsers.re(
    r'(?P<quien>el profesor|"[^"]+") sube (?P<que>"[^"]+"|esa copia|ese archivo|otra vez "[^"]+"'
    r'|los mismos bytes con el nombre "[^"]+") a la sección (?P<numero>[0-9]+)'
    r'(?: con el campo multipart "(?P<campo>[a-z_]+)" igual a "(?P<valor>[^"]*)"'
    r'(?: y el parámetro de consulta "(?P<consulta>[a-z_]+=[^"]*)")?'
    r'| con el nombre de archivo multipart "(?P<enviado>.+)")?'))
def _sube(ctx: Escenario, quien: str, que: str, numero: str, campo: str | None, valor: str | None,
          consulta: str | None, enviado: str | None) -> None:
    correo = ctx.profesor if quien == "el profesor" else quien.strip('"')
    assert correo is not None
    if que in ("esa copia", "ese archivo"):
        assert ctx.archivo is not None, "el escenario no armó ningún archivo antes de subirlo"
        contenido, nombre = ctx.archivo
    elif que.startswith("los mismos bytes"):
        assert ctx.ultimo is not None
        contenido, nombre = ctx.ultimo[0], re.search(r'"([^"]+)"', que)[1]
    else:
        nombre = re.search(r'"([^"]+)"', que)[1]
        contenido = ctx.de_inventados(nombre)
    opciones: dict[str, Any] = {}
    if campo is not None:
        opciones["data"] = {campo: valor}
    if consulta is not None:
        clave, _, valor_consulta = consulta.partition("=")
        opciones["params"] = {clave: valor_consulta}
    ctx.subir(correo, contenido, enviado or nombre, numero, **opciones)


# Entonces, la respuesta

@then(parsers.re(
    r'la respuesta es (?P<codigo>[0-9]+)'
    r'(?: y su cuerpo trae estado "(?P<e1>[A-Z_]+)"'
    r'(?:, filas_leidas (?P<leidas>[0-9]+), filas_aceptadas (?P<aceptadas>[0-9]+) y filas_rechazadas (?P<rechazadas>[0-9]+)'
    r'| y el mensaje "(?P<mensaje>[^"]*)")?'
    r'| con estado "(?P<e2>[A-Z_]+)"'
    r'| con detail "(?P<detail>[^"]*)"'
    r'|(?P<constancia> y su cuerpo es la constancia de ese mismo carga_id)(?:, en estado "(?P<e3>[A-Z_]+)")?)?'))
def _la_respuesta_es(ctx: Escenario, codigo: str, e1: str | None, leidas: str | None, aceptadas: str | None,
                     rechazadas: str | None, mensaje: str | None, e2: str | None, detail: str | None,
                     constancia: str | None, e3: str | None) -> None:
    respuesta = ctx.respuesta
    assert respuesta.status_code == int(codigo), respuesta.text
    cuerpo = respuesta.json()
    if detail is not None:
        assert cuerpo == {"detail": detail}
    if e1 or e2:
        assert cuerpo["estado"] == (e1 or e2)
    if leidas is not None:
        assert (cuerpo["filas_leidas"], cuerpo["filas_aceptadas"], cuerpo["filas_rechazadas"]) == (
            int(leidas), int(aceptadas), int(rechazadas))
    if mensaje is not None:
        assert cuerpo["mensaje"] == mensaje
    if constancia is not None:
        assert ctx.carga_previa is not None and cuerpo["carga_id"] == ctx.carga_previa
        leida = ctx.sesion(ctx.profesor).get(f"/api/cargas/{ctx.carga_previa}")
        assert leida.status_code == 200 and leida.json() == cuerpo
        if e3 is not None:
            assert cuerpo["estado"] == e3


@then(parsers.re(r'el cuerpo trae el mensaje "(?P<mensaje>[^"]*)"'))
def _cuerpo_mensaje(ctx: Escenario, mensaje: str) -> None:
    assert ctx.cuerpo()["mensaje"] == mensaje


@then(parsers.re(r'el cuerpo de la respuesta no contiene el texto "(?P<texto>[^"]*)"'))
def _cuerpo_sin_texto(ctx: Escenario, texto: str) -> None:
    assert texto not in ctx.respuesta.text


# Entonces, lo que gana o no gana la base

def _tablas(lista: str) -> list[str]:
    return re.findall(r"abet\.(\w+)", lista)


LISTA = r"abet\.\w+(?:(?:, | y )abet\.\w+)*"


@then(parsers.re(rf'(?P<lista>{LISTA}) no ganan ninguna fila'))
def _no_ganan(ctx: Escenario, lista: str) -> None:
    ahora = ctx.api.conteos()
    for tabla in _tablas(lista):
        assert ahora[tabla] == ctx.antes[tabla], f"abet.{tabla} cambió de {ctx.antes[tabla]} a {ahora[tabla]} filas"


@then(parsers.re(rf'(?P<lista>{LISTA}) no gana ninguna fila'))
def _no_gana(ctx: Escenario, lista: str) -> None:
    _no_ganan(ctx, lista)


@then(parsers.re(r'abet\.(?P<tabla>\w+) gana (?P<n>[0-9]+) sola fila'))
def _gana(ctx: Escenario, tabla: str, n: str) -> None:
    assert ctx.api.conteos()[tabla] - ctx.antes[tabla] == int(n)


@then(parsers.re(rf'(?P<lista>{LISTA}) no tienen? filas de esa carga'))
def _sin_filas_de_la_carga(ctx: Escenario, lista: str) -> None:
    assert ctx.carga_id is not None
    for tabla in _tablas(lista):
        assert ctx.cuenta(tabla, "carga_id = %s", ctx.carga_id) == 0, tabla


@then(parsers.re(r'ninguna carga queda en estado "EN_CURSO"'))
def _ninguna_en_curso(ctx: Escenario) -> None:
    assert ctx.cuenta("carga", "estado = 'EN_CURSO'") == 0


# Entonces, consultas de control Q01 a Q14

def consultas_de_control() -> dict[str, str]:
    """Q01 a Q14 de controles_neon.sql, copia literal de las de db/pruebas/pruebas.sql."""
    texto = CONTROLES.read_text(encoding="utf-8")
    bloques = re.findall(r"\\echo '(Q[0-9]{2})\.[^\n]*\n(.*?);\n\\set q[0-9]{2} :ROW_COUNT", texto, flags=re.S)
    return {nombre: consulta.strip() for nombre, consulta in bloques}


@then(parsers.re(r'(?:la consulta|las consultas) de control (?P<lista>Q[0-9]{2}(?:, Q[0-9]{2})*(?: y Q[0-9]{2})?) devuelven? 0 filas'))
def _controles_en_cero(ctx: Escenario, lista: str) -> None:
    consultas = consultas_de_control()
    assert sorted(consultas) == [f"Q{n:02d}" for n in range(1, 15)]
    for nombre in re.findall(r"Q[0-9]{2}", lista):
        assert ctx.filas(consultas[nombre]) == [], f"{nombre} devuelve filas"


# Conexión directa con el rol de la aplicación y violaciones de restricciones

@given(parsers.re(r'(?:que )?la base tiene aplicado db/plataforma/neon/guardia_datos_inventados\.sql'))
def _guardia_aplicada(ctx: Escenario) -> None:
    assert ctx.uno("SELECT count(*) FROM pg_constraint WHERE conname = 'ck_estudiante_codigo_inventado'"
                   " AND convalidated") == 1


def _abrir_directa(ctx: Escenario) -> None:
    conexion = make_conninfo(ctx.api.base.conexion, user=ctx.api.base.rol_app)
    ctx.directa = ctx.pila.enter_context(psycopg.connect(conexion, autocommit=True))
    assert ctx.directa.execute("SELECT current_user").fetchone()[0] == ctx.api.base.rol_app


@given(parsers.re(r'una conexión directa con el rol abet_app'))
def _conexion_directa(ctx: Escenario) -> None:
    _abrir_directa(ctx)


@given(parsers.re(r'una conexión directa con el rol abet_app y una carga EN_CURSO de la sección (?P<numero>[0-9]+)'
                  r'(?: con un archivo de filas_de_datos (?P<filas>[0-9]+))?'))
def _conexion_con_carga_en_curso(ctx: Escenario, numero: str, filas: str | None) -> None:
    _abrir_directa(ctx)
    seccion = ctx.seccion_id(numero)
    carrera, reglas = ctx.filas(
        "SELECT (SELECT pm.carrera_id FROM abet.plan_medicion pm JOIN abet.seccion s"
        " ON s.asignatura_id = pm.asignatura_id AND s.periodo_id = pm.periodo_id WHERE s.seccion_id = %s LIMIT 1),"
        " (SELECT conjunto_reglas_id FROM abet.conjunto_reglas WHERE version = %s)", seccion, A.REGLAS)[0]
    de_datos = int(filas or 11)
    archivo = ctx.directa.execute(
        "INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)"
        " VALUES (%s, 'archivo_de_prueba.xlsx', 'Hoja_de_prueba', %s) RETURNING archivo_id",
        (secrets.token_hex(32), de_datos)).fetchone()[0]
    ctx.carga_id = ctx.directa.execute(
        "INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id,"
        " programa_version) VALUES (%s, %s, %s, %s, %s, 'prueba') RETURNING carga_id",
        (seccion, archivo, de_datos, carrera, reglas)).fetchone()[0]


@when(parsers.re(r'esa conexión inserta en abet\.estudiante el código "(?P<codigo>[0-9]+)"'))
def _inserta_estudiante(ctx: Escenario, codigo: str) -> None:
    ctx.antes = ctx.api.conteos()
    ctx.intentar("INSERT INTO abet.estudiante (codigo) VALUES (%s)", codigo)


@then(parsers.re(r'la base rechaza (?:la inserción|el cambio) por la restricción "(?P<restriccion>[a-z0-9_]+)"'))
def _base_rechaza(ctx: Escenario, restriccion: str) -> None:
    assert ctx.error_directo is not None, "la base aceptó la sentencia"
    assert ctx.error_directo.diag.constraint_name == restriccion, ctx.error_directo.diag.constraint_name


@then(parsers.re(r'abet\.estudiante no tiene el código "(?P<codigo>[0-9]+)"'))
def _sin_codigo(ctx: Escenario, codigo: str) -> None:
    assert ctx.cuenta("estudiante", "codigo = %s", codigo) == 0


@then(parsers.re(r'abet\.estudiante tiene el código "(?P<codigo>[0-9]+)"'))
def _con_codigo(ctx: Escenario, codigo: str) -> None:
    assert ctx.cuenta("estudiante", "codigo = %s", codigo) == 1


# Entonces, cuántas cargas tiene una sección

@then(parsers.re(r'la sección (?P<numero>[0-9]+) no tiene ninguna carga "(?P<estado>[A-Z]+)"'))
def _seccion_sin_carga_en_estado(ctx: Escenario, numero: str, estado: str) -> None:
    assert ctx.cuenta("carga", "seccion_id = %s AND estado = %s", ctx.seccion_id(numero), estado) == 0


@then(parsers.re(r'la sección (?P<numero>[0-9]+) no tiene ninguna carga'))
def _seccion_sin_ninguna_carga(ctx: Escenario, numero: str) -> None:
    assert ctx.cuenta("carga", "seccion_id = %s", ctx.seccion_id(numero)) == 0
