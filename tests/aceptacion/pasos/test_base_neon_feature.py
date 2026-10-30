"""Pasos de base_neon.feature (US-01 a US-04), ejecutables con pytest-bdd en español (T051).

El .feature manda. Los criterios que se pueden probar en un PostgreSQL 16 desechable corren aquí, cada
«Entonces» contra la base, la salida del comando o el archivo. Los escenarios de US-01 que migran y controlan
la base en Neon quedan omitidos con la razón «se comprueban en Neon con T021 y T027», como dice el encabezado
del .feature y T051.

Todo script de psql corre contra una base abet_demo_ del clúster desechable de tests/conftest.py, a través de
tests/base_desechable.py, que se niega a trabajar sin las variables de ese clúster. La clave del rol de la
aplicación, cuando un escenario la pide, se genera al vuelo y solo vive en el entorno del proceso de psql.
"""

from __future__ import annotations

import os
import re
import secrets
import subprocess
import sys
import tomllib
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
import pytest
from psycopg import errors
from psycopg.conninfo import make_conninfo
from pytest_bdd import given, parsers, scenarios, then, when

from app.main import ConfiguracionDeLaApi


A = sys.modules["api_de_prueba"]
Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
DATOS_2026_2 = RAIZ / "db" / "datos" / "periodo_2026_2_inventado.sql"
ROL_APP = RAIZ / "db" / "plataforma" / "neon" / "crear_rol_app.sql"
CONTROLES = RAIZ / "db" / "plataforma" / "neon" / "controles_neon.sql"
SINTETICOS = RAIZ / "db" / "pruebas" / "datos_sinteticos.sql"
CALLBACK = RAIZ / "db" / "callbacks" / "afterMigrate__permisos_lectura.sql"
V1_07 = RAIZ / "db" / "migration" / "V1_07__crear_registro_cargas.sql"
V1_09 = RAIZ / "db" / "migration" / "V1_09__crear_acceso.sql"
RAZON_NEON = "se comprueban en Neon con T021 y T027"

scenarios("specs/001-mvp-carga-r17/aceptacion/base_neon.feature")


# Ayudas

def _bd(ctx: Escenario) -> ModuleType:
    return ctx.plantillas.base_desechable


def _propia(ctx: Escenario, **opciones: Any) -> Any:
    """Base desechable propia del escenario, que se borra al terminar, y la API de prueba que la usa."""
    base = _bd(ctx).crear(**opciones)
    ctx.pila.callback(_bd(ctx).borrar, base)
    dueno = ctx.pila.enter_context(psycopg.connect(base.conexion, autocommit=True))
    ctx.api = A.Api(base=base, dueno=dueno, ajustes=A.ajustes_de(base), pila=ctx.pila)
    return base


def _psql(ctx: Escenario, *argumentos: str, entorno: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """psql contra la base del escenario, sin lanzar si el script falla, para que el escenario lea el código."""
    variables = _bd(ctx)._entorno()
    variables.update(entorno or {})
    return subprocess.run([variables.get("PSQL", "psql"), "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d",
                           ctx.api.base.nombre, *argumentos], env=variables, capture_output=True, text=True,
                          check=False)


def _psql_ok(ctx: Escenario, *argumentos: str, entorno: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    corrida = _psql(ctx, *argumentos, entorno=entorno)
    assert corrida.returncode == 0, f"psql sale con el código {corrida.returncode}\n{corrida.stderr.strip()}"
    return corrida


def _hasta_v1_08(ctx: Escenario) -> Any:
    """Base con los esquemas abet y acceso y las migraciones versionadas V1_01 a V1_08, sin repetibles."""
    bd = _bd(ctx)
    nombre = bd.PREFIJO + bd._sufijo_nuevo()
    bd._psql("postgres", "-c", f"CREATE DATABASE {nombre} TEMPLATE template0 ENCODING 'UTF8'")
    base = bd.BaseDesechable(nombre, bd._conexion(nombre), None, None)
    ctx.pila.callback(bd.borrar, base)
    bd._psql(nombre, "-c", "CREATE SCHEMA abet", "-c", "CREATE SCHEMA acceso")
    for ruta in bd.migraciones():
        if ruta.name.startswith("V") and bd._version(ruta) < (1, 9):
            bd._psql(nombre, "-1", "-f", str(ruta), opciones="-c client_min_messages=warning")
    dueno = ctx.pila.enter_context(psycopg.connect(base.conexion, autocommit=True))
    ctx.api = A.Api(base=base, dueno=dueno, ajustes=A.ajustes_de(base), pila=ctx.pila)
    return base


def _repetibles(ctx: Escenario) -> None:
    for ruta in _bd(ctx).migraciones():
        if ruta.name.startswith("R"):
            _psql_ok(ctx, "-1", "-f", str(ruta), entorno={"PGOPTIONS": "-c client_min_messages=warning"})


def _controles() -> dict[str, str]:
    """Q01 a Q14 de controles_neon.sql, copia literal de las de db/pruebas/pruebas.sql."""
    texto = CONTROLES.read_text(encoding="utf-8")
    bloques = re.findall(r"\\echo '(Q[0-9]{2})\.[^\n]*\n(.*?);\n\\set q[0-9]{2} :ROW_COUNT", texto, flags=re.S)
    consultas = {nombre: consulta.strip() for nombre, consulta in bloques}
    assert sorted(consultas) == [f"Q{n:02d}" for n in range(1, 15)]
    return consultas


def _conexion_de_la_aplicacion(ctx: Escenario) -> None:
    conexion = make_conninfo(ctx.api.base.conexion, user=ctx.api.base.rol_app)
    ctx.directa = ctx.pila.enter_context(psycopg.connect(conexion, autocommit=True))
    assert ctx.directa.execute("SELECT current_user").fetchone()[0] == ctx.api.base.rol_app


def _conteos(ctx: Escenario, lista: str) -> dict[str, int]:
    return {tabla: int(ctx.uno(f"SELECT count(*) FROM {tabla}")) for tabla in re.findall(r"(?:abet|acceso)\.\w+", lista)}


# Dado, las bases

@given(parsers.re(r'una base PostgreSQL 16 desechable con V1_01 a V1_(?P<hasta>0[89])(?P<resto>.*)'))
def _base(ctx: Escenario, hasta: str, resto: str) -> None:
    mismos_datos = {
        " y los datos de periodo_2026_2_inventado.sql",
        " y periodo_2026_2_inventado.sql ya aplicado",
        " y los usuarios de prueba registrados por periodo_2026_2_inventado.sql",
        ", el rol de crear_rol_app.sql y los datos de periodo_2026_2_inventado.sql",
        " y abet_app creado con crear_rol_app.sql",
    }
    if hasta == "08":
        base = _hasta_v1_08(ctx)
        if resto:
            assert resto == " y la carga PUBLICADA de la sección 410 de db/pruebas/datos_sinteticos.sql", resto
            _psql_ok(ctx, "-1", "-f", str(SINTETICOS), entorno={"PGOPTIONS": "-c client_min_messages=warning"})
        assert ctx.uno("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'acceso'") == 0
        return
    if resto in mismos_datos:
        ctx.crear_base("periodo")
    elif resto == " y sin datos operativos de 2026-2":
        _propia(ctx, datos_2026_2=False)
    elif resto == "":
        _propia(ctx, rol_app=False, datos_2026_2=False)
    else:
        raise AssertionError(f"No se reconoce el estado de base {resto!r}.")
    assert ctx.uno("SHOW server_version_num").startswith("16"), "la base desechable no es PostgreSQL 16"
    assert ctx.uno("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'acceso'"
                   " AND table_name = 'usuario_autorizado'") == 1, "falta la migración V1_09"
    hay_datos = ctx.uno("SELECT count(*) FROM abet.seccion s JOIN abet.periodo p USING (periodo_id)"
                        " WHERE p.codigo = '2026-2'")
    assert (hay_datos > 0) == (resto in mismos_datos), "el estado de los datos de 2026-2 no es el que pide el escenario"


@given("la variable APP_DB_CLAVE definida solo en el entorno de la terminal")
def _clave_del_rol(ctx: Escenario) -> None:
    ctx.extras["clave_app"] = secrets.token_hex(32)


@given(parsers.re(r'(?:que )?la sección 411 de 450002 en 2026-2 sin ninguna carga'))
def _seccion_411_sin_carga(ctx: Escenario) -> None:
    assert ctx.cuenta("carga", "seccion_id = %s", ctx.seccion_id("411")) == 0


@given("una conexión con el usuario abet_app")
def _conexion_con_el_usuario(ctx: Escenario) -> None:
    _conexion_de_la_aplicacion(ctx)


@given(parsers.re(r'(?:que )?una carga PUBLICADA de la sección 410 con 33 mediciones'
                  r'|una carga PUBLICADA de la sección 410 hecha con "(?P<reglas>[^"]+)"'))
def _carga_publicada_de_la_410(ctx: Escenario, reglas: str | None = None) -> None:
    respuesta = ctx.subir(A.DOCENTE_410, A.archivo(A.CORRECTO), A.CORRECTO, "410")
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "PUBLICADA", respuesta.text
    ctx.carga_id = respuesta.json()["carga_id"]
    assert ctx.cuenta("medicion", "carga_id = %s", ctx.carga_id) == 33
    if reglas is not None:
        assert ctx.uno("SELECT cr.version FROM abet.carga c JOIN abet.conjunto_reglas cr USING (conjunto_reglas_id)"
                       " WHERE c.carga_id = %s", ctx.carga_id) == reglas


# US-01, los escenarios que se comprueban en Neon

@given(parsers.re(r'(?:que )?la base de Neon .+'))
def _escenario_de_neon(ctx: Escenario) -> None:
    pytest.skip(RAZON_NEON)


# US-01, ninguna credencial en lo que sigue git

def _git(*argumentos: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(RAIZ), *argumentos], capture_output=True, check=False)


@given("que el administrador técnico guarda la conexión de Neon solo en un archivo local .env.neon")
def _env_neon_local(ctx: Escenario) -> None:
    seguidos = _git("ls-files", "-z").stdout.split(b"\0")
    assert b".env.neon" not in seguidos, ".env.neon figura entre los archivos que sigue git"


@when(parsers.re(r'se busca el valor de NEON_DB_PASSWORD en los archivos que lista "git ls-files" y en la salida de '
                 r'"git log -p --all" del repositorio que guarda las migraciones'))
def _buscar_el_valor(ctx: Escenario) -> None:
    # La clave real vive solo en la terminal del administrador, así que en la CI y en las pruebas locales no
    # suele estar en el entorno. Por eso, además del valor cuando existe, la búsqueda recorre los archivos
    # seguidos y toda la historia con las formas que toma una credencial de Neon (una URL de PostgreSQL con
    # usuario y clave, o una clave npg_), que sí pueden aparecer y hacer fallar el escenario. Los dos scripts
    # del preflight quedan fuera porque traen esos patrones y un secreto falso a propósito, como en la regla 4.
    valor = os.environ.get("NEON_DB_PASSWORD")
    ctx.request.node.user_properties.append(
        ("valor_buscado", "NEON_DB_PASSWORD del entorno y patrones de credencial" if valor
         else "solo patrones de credencial, porque NEON_DB_PASSWORD no está en el entorno"))
    patron = re.compile(rb"postgres(?:ql)?://[^:/@\s]+:[^@\s]+@|npg_[A-Za-z0-9]{12,}")
    fuera = {"scripts/preflight.sh", "scripts/probar_preflight.sh"}

    def aparece(contenido: bytes) -> bool:
        return bool(patron.search(contenido)) or (valor is not None and valor.encode() in contenido)

    hallazgos = []
    for ruta in filter(None, _git("ls-files", "-z").stdout.split(b"\0")):
        nombre = ruta.decode()
        archivo = RAIZ / nombre
        if nombre not in fuera and archivo.is_file() and aparece(archivo.read_bytes()):
            hallazgos.append(nombre)
    historia = _git("log", "-p", "--all", "--", ".", *(f":!{nombre}" for nombre in sorted(fuera))).stdout
    if aparece(historia):
        hallazgos.append("git log -p --all")
    ctx.extras["hallazgos"] = hallazgos


@then("el valor no aparece en ningún archivo seguido ni en ningún commit, incluido flyway.toml")
def _valor_ausente(ctx: Escenario) -> None:
    assert ctx.extras["hallazgos"] == []
    assert (RAIZ / "db" / "flyway.toml").read_text(encoding="utf-8").count("password = \"${env.") >= 1


@then(parsers.re(r'"git check-ignore -v \.env\.neon" responde con la regla "\.env\.\*" de \.gitignore'))
def _regla_de_gitignore(ctx: Escenario) -> None:
    salida = _git("check-ignore", "-v", ".env.neon").stdout.decode()
    asunto = salida.split("\t")[0].split(":")
    assert asunto[0] == ".gitignore" and asunto[-1] == ".env.*", salida


@then(parsers.re(r'"bash scripts/preflight\.sh" termina sin fallas de la regla 3 ni de la regla 4'))
def _preflight(ctx: Escenario) -> None:
    corrida = subprocess.run(["bash", "scripts/preflight.sh"], cwd=RAIZ, capture_output=True, text=True, check=False)
    salida = corrida.stdout + corrida.stderr
    assert "(regla 3)" not in salida and "(regla 4)" not in salida, salida


# US-01, la CI reproduce la base sin Redgate

@given("el contenido de bd/ trasladado a db/ del Back con su historia de git")
def _contenido_trasladado(ctx: Escenario) -> None:
    assert not (RAIZ / "bd").exists(), "bd/ sigue en el Back"
    assert sorted(p.name for p in (RAIZ / "db" / "migration").glob("V1_0[1-9]__*.sql")), "faltan las migraciones en db/"
    assert _git("log", "--merges", "--grep", "git subtree desde", "--format=%H", "-1").stdout.strip(), (
        "el Back no tiene la fusión de git subtree que trajo la base")


@when("la CI del Back corre correr_pruebas.sh con psql contra un PostgreSQL 16 desechable")
def _correr_pruebas(ctx: Escenario) -> None:
    corrida = subprocess.run(["bash", "db/pruebas/correr_pruebas.sh"], cwd=RAIZ, capture_output=True, text=True,
                             check=False, timeout=600)
    ctx.extras["ci"] = corrida


@then('la salida del paso termina con "RESULTADO: todo pasó" y el código de salida es 0')
def _resultado_de_la_ci(ctx: Escenario) -> None:
    corrida = ctx.extras["ci"]
    assert corrida.returncode == 0, corrida.stdout[-2000:] + corrida.stderr[-2000:]
    assert corrida.stdout.rstrip().splitlines()[-1] == "RESULTADO: todo pasó"


@then("ningún archivo de .github/workflows/ del Back nombra una imagen o una acción de Redgate o de Flyway")
def _sin_redgate(ctx: Escenario) -> None:
    archivos = sorted((RAIZ / ".github" / "workflows").glob("*.y*ml"))
    assert archivos, "el Back no tiene archivos en .github/workflows/"
    for archivo in archivos:
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            codigo = linea.split("#", 1)[0]
            if re.match(r"\s*(?:-\s*)?(?:uses|image):", codigo):
                assert not re.search(r"redgate|flyway", codigo, re.I), f"{archivo.name}: {linea.strip()}"


@then(parsers.re(r'"git log --follow" del archivo V1_07__crear_registro_cargas\.sql en el Back muestra los commits que '
                 r'tenía en ABET_ULIMA'))
def _historia_de_v1_07(ctx: Escenario) -> None:
    # La historia de ABET_ULIMA entra por el segundo padre de la fusión de git subtree. Sin -m, git log no calcula
    # el diff de una fusión y --follow se detiene en ella, así que el paso usa «git log --follow -m». Los commits
    # que el archivo tenía en ABET_ULIMA son los que lo tocan en la historia de ese segundo padre, y todos deben
    # aparecer en el seguimiento desde el Back.
    fusion = _git("log", "--merges", "--grep", "git subtree desde", "--format=%P", "-1").stdout.decode().split()
    assert len(fusion) == 2, "no se encontró la fusión de git subtree que trajo la base de ABET_ULIMA"
    origen = fusion[1]
    ruta = "db/migration/V1_07__crear_registro_cargas.sql"
    en_abet_ulima = _git("log", "--format=%H", origen, "--", ruta).stdout.decode().split()
    assert en_abet_ulima, f"V1_07 no tiene commits en la historia de ABET_ULIMA ({origen[:7]})"
    seguidos = set(_git("log", "--follow", "-m", "--format=%H", "--", ruta).stdout.decode().split())
    faltan = [commit[:7] for commit in en_abet_ulima if commit not in seguidos]
    assert not faltan, f"git log --follow -m no muestra los commits de ABET_ULIMA {faltan}"


# US-02, crear el rol de la aplicación

@when("el administrador técnico corre db/plataforma/neon/crear_rol_app.sql con psql")
def _crear_el_rol(ctx: Escenario) -> None:
    base = ctx.api.base
    rol = base.nombre.replace(_bd(ctx).PREFIJO, f"{_bd(ctx).PREFIJO}app_", 1)
    ctx.pila.callback(_bd(ctx).borrar, replace(base, rol_app=rol))
    ctx.extras["rol"] = rol
    corrida = _psql_ok(ctx, "-v", f"rol_app={rol}", "-f", str(ROL_APP),
                       entorno={"APP_DB_CLAVE": ctx.extras["clave_app"]})
    ctx.extras["salida"] = corrida.stdout + corrida.stderr


@then("pg_roles muestra abet_app con rolcanlogin verdadero")
def _rol_puede_entrar(ctx: Escenario) -> None:
    fila = ctx.filas("SELECT rolcanlogin FROM pg_roles WHERE rolname = %s", ctx.extras["rol"])
    assert fila == [(True,)]


@then("rolsuper, rolbypassrls, rolcreaterole, rolcreatedb y rolreplication de abet_app son falsos")
def _rol_sin_administracion(ctx: Escenario) -> None:
    fila = ctx.filas("SELECT rolsuper, rolbypassrls, rolcreaterole, rolcreatedb, rolreplication FROM pg_roles"
                     " WHERE rolname = %s", ctx.extras["rol"])
    assert fila == [(False, False, False, False, False)]


@then("la salida del script no muestra el valor de APP_DB_CLAVE")
def _salida_sin_clave(ctx: Escenario) -> None:
    assert ctx.extras["clave_app"] not in ctx.extras["salida"]


# US-02, publicar con el rol de la aplicación

PUBLICAR = (
    """INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)
       VALUES (encode(sha256(convert_to('export inventado 2026-2 450002 411', 'UTF8')), 'hex'),
               'export_inventado_411.xlsx', 'gc_SINTETICO_20262_450002_411_f', 11)""",
    """INSERT INTO abet.carga (seccion_id, archivo_id, filas_de_datos, carrera_id, conjunto_reglas_id, programa_version,
                             subida_por)
       SELECT s.seccion_id, ao.archivo_id, ao.filas_de_datos, cr.carrera_id, cr.conjunto_reglas_id, 'v0.0.0-prueba',
              u.usuario_id
       FROM abet.seccion s
       JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id AND a.codigo = '450002'
       JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id AND pe.codigo = '2026-2'
       JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'export_inventado_411.xlsx'
       JOIN abet.conjunto_reglas cr ON cr.version = 'R-2026-BORRADOR'
       JOIN acceso.usuario_autorizado u ON u.correo = 'docente411@example.invalid'
       WHERE s.numero = '411'""",
    """INSERT INTO abet.carga_columna (carga_id, seccion_id, carrera_id, periodo_id, asignatura_id, plan_medicion_id,
                                     pi_id, pi_codigo, posicion, encabezado, bb_columna_id, puntaje_maximo_declarado)
       SELECT c.carga_id, s.seccion_id, c.carrera_id, s.periodo_id, s.asignatura_id, pm.plan_medicion_id, pm.pi_id,
              p.codigo, v.posicion, v.pi || ' [Total Pts: ' || v.puntos || ' Score] |' || v.bb_id, v.bb_id, v.puntos
       FROM (VALUES ('5.1', 5, '9000051', 4), ('5.2', 6, '9000052', 4), ('5.3', 7, '9000053', 20))
            AS v (pi, posicion, bb_id, puntos)
       JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'export_inventado_411.xlsx'
       JOIN abet.carga c ON c.archivo_id = ao.archivo_id
       JOIN abet.seccion s ON s.seccion_id = c.seccion_id
       JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
                                 AND pm.carrera_id = c.carrera_id
       JOIN abet.pi p ON p.pi_id = pm.pi_id AND p.codigo = v.pi""",
    """INSERT INTO abet.estudiante (codigo)
       SELECT CAST(99000000 + n AS varchar(8)) FROM generate_series(12, 22) AS g (n)""",
    """INSERT INTO abet.carga_fila (carga_id, fila_origen, estudiante_id)
       SELECT c.carga_id, CAST(e.codigo AS integer) - 99000010, e.estudiante_id
       FROM abet.estudiante e
       JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'export_inventado_411.xlsx'
       JOIN abet.carga c ON c.archivo_id = ao.archivo_id
       WHERE e.codigo BETWEEN '99000012' AND '99000022'""",
    """INSERT INTO abet.medicion (carga_id, carga_columna_id, pi_id, estudiante_id, estado_evidencia, nivel_original,
                                fila_origen)
       SELECT cc.carga_id, cc.carga_columna_id, cc.pi_id, f.estudiante_id, 'CALIFICADO',
              CASE cc.pi_codigo WHEN '5.1' THEN v.n51 WHEN '5.2' THEN v.n52 ELSE v.n53 END, f.fila_origen
       FROM (VALUES (2, 2, 2, 2), (3, 3, 4, 3), (4, 4, 3, 4), (5, 2, 1, 1), (6, 3, 4, 3), (7, 4, 3, 4), (8, 1, 2, 2),
                    (9, 3, 2, 3), (10, 2, 3, 3), (11, 4, 3, 4), (12, 3, 4, 3)) AS v (fila, n51, n52, n53)
       JOIN abet.archivo_origen ao ON ao.nombre_archivo = 'export_inventado_411.xlsx'
       JOIN abet.carga c ON c.archivo_id = ao.archivo_id
       JOIN abet.carga_fila f ON f.carga_id = c.carga_id AND f.fila_origen = v.fila
       JOIN abet.carga_columna cc ON cc.carga_id = c.carga_id""",
)
FILAS_ESPERADAS = (1, 1, 3, 11, 11, 33)


@when(parsers.re(r'la aplicación inserta en una sola transacción el archivo_origen, la carga, 3 carga_columna, '
                 r'11 estudiante con los códigos 99000012 a 99000022, 11 carga_fila y 33 medicion de la sección 411'))
def _publicar_en_una_transaccion(ctx: Escenario) -> None:
    ctx.directa.execute("BEGIN")
    ctx.extras["transaccion"] = True
    ganadas = tuple(ctx.directa.execute(sentencia).rowcount for sentencia in PUBLICAR)
    assert ganadas == FILAS_ESPERADAS


@when(parsers.re(r'actualiza esa carga a estado "PUBLICADA" con filas_leidas 11, filas_aceptadas 11, filas_rechazadas 0 '
                 r'y terminada_en no nulo'))
def _publicar_la_carga(ctx: Escenario) -> None:
    ganadas = ctx.directa.execute(
        "UPDATE abet.carga c SET estado = 'PUBLICADA', filas_leidas = 11, filas_aceptadas = 11, filas_rechazadas = 0,"
        " terminada_en = clock_timestamp() FROM abet.archivo_origen ao WHERE ao.archivo_id = c.archivo_id"
        " AND ao.nombre_archivo = 'export_inventado_411.xlsx'").rowcount
    assert ganadas == 1


@then("la transacción confirma sin errores")
def _confirmar(ctx: Escenario) -> None:
    ctx.directa.execute("COMMIT")
    assert ctx.filas("SELECT estado, filas_leidas, filas_aceptadas, filas_rechazadas, terminada_en IS NOT NULL"
                     " FROM abet.carga WHERE seccion_id = %s", ctx.seccion_id("411")) == [("PUBLICADA", 11, 11, 0, True)]


@when(parsers.re(r'consulta "(?P<primera>SELECT count\(\*\) FROM abet\.v_r17_por_pi)" y '
                 r'"(?P<segunda>SELECT count\(\*\) FROM abet\.v_tabla_maestra_pi)"'))
def _leer_las_vistas(ctx: Escenario, primera: str, segunda: str) -> None:
    ctx.extras["vistas"] = []
    for consulta in (primera, segunda):
        ctx.intentar(consulta)
        assert ctx.error_directo is None, str(ctx.error_directo)
        ctx.extras["vistas"].append(ctx.directa.execute(consulta).fetchone()[0])


@then("las dos consultas responden sin error de permisos")
def _vistas_leidas(ctx: Escenario) -> None:
    assert ctx.error_directo is None and len(ctx.extras["vistas"]) == 2
    assert all(isinstance(n, int) for n in ctx.extras["vistas"])


# US-02, lo que el rol de la aplicación no puede hacer

@when(parsers.re(r'ejecuta "(?P<sentencia>(?:DELETE FROM|TRUNCATE) abet\.[a-z_]+)"'))
def _ejecutar_sentencia(ctx: Escenario, sentencia: str) -> None:
    ctx.antes = ctx.api.conteos()
    ctx.intentar(sentencia)


COLUMNAS_DE_CARGA = {"conjunto_reglas_id", "subida_por", "archivo_id", "seccion_id", "reemplaza_carga_id"}


@when(parsers.re(r'ejecuta un UPDATE de la columna (?P<columna>[a-z_]+) de esa fila de abet\.carga'))
def _actualizar_columna(ctx: Escenario, columna: str) -> None:
    assert columna in COLUMNAS_DE_CARGA
    ctx.extras["columna"] = columna
    ctx.extras["valor_anterior"] = ctx.uno(f"SELECT {columna} FROM abet.carga WHERE carga_id = %s", ctx.carga_id)
    ctx.intentar(f"UPDATE abet.carga SET {columna} = {columna} WHERE carga_id = %s", ctx.carga_id)


@when(parsers.re(r'ejecuta un (?P<orden>UPDATE|INSERT) sobre abet\.(?P<tabla>[a-z_]+)'))
def _escribir_en_abet(ctx: Escenario, orden: str, tabla: str) -> None:
    if orden == "INSERT":
        ctx.intentar(f"INSERT INTO abet.{tabla} DEFAULT VALUES")
    else:
        columna = ctx.uno("SELECT column_name FROM information_schema.columns WHERE table_schema = 'abet'"
                          " AND table_name = %s AND is_identity = 'NO' ORDER BY ordinal_position LIMIT 1", tabla)
        ctx.intentar(f'UPDATE abet.{tabla} SET "{columna}" = "{columna}"')


@when(parsers.re(r'ejecuta (?P<orden>un DELETE|un INSERT de un usuario nuevo|un UPDATE que cambia el rol a "COORDINADOR"'
                 r'|un INSERT que asigna la sección 411 al usuario de "docente410@example\.invalid") '
                 r'sobre acceso\.(?P<tabla>[a-z_]+)'))
def _escribir_en_acceso(ctx: Escenario, orden: str, tabla: str) -> None:
    if orden == "un DELETE":
        ctx.intentar(f"DELETE FROM acceso.{tabla}")
    elif orden == "un INSERT de un usuario nuevo":
        ctx.intentar("INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES ('nuevo@example.invalid', 'PROFESOR')")
    elif orden.startswith("un UPDATE"):
        ctx.intentar("UPDATE acceso.usuario_autorizado SET rol = 'COORDINADOR' WHERE correo = 'docente410@example.invalid'")
    else:
        ctx.intentar("INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) VALUES (%s, %s)",
                     ctx.usuario_id("docente410@example.invalid"), ctx.seccion_id("411"))


@then(parsers.re(r'PostgreSQL responde "(?P<mensaje>permission denied for table [a-z_]+)"'))
def _permiso_denegado(ctx: Escenario, mensaje: str) -> None:
    assert isinstance(ctx.error_directo, errors.InsufficientPrivilege), repr(ctx.error_directo)
    assert ctx.error_directo.diag.message_primary == mensaje


@then(parsers.re(r'abet\.medicion sigue con las 33 filas de la carga de la sección 410'))
def _mediciones_intactas(ctx: Escenario) -> None:
    assert ctx.cuenta("medicion") == 33 and ctx.cuenta("medicion", "carga_id = %s", ctx.carga_id) == 33


@then(parsers.re(r'la carga conserva su valor anterior en (?P<columna>[a-z_]+)'))
def _valor_conservado(ctx: Escenario, columna: str) -> None:
    assert columna == ctx.extras["columna"]
    assert ctx.uno(f"SELECT {columna} FROM abet.carga WHERE carga_id = %s", ctx.carga_id) == ctx.extras["valor_anterior"]


@when("la prueba aplica con psql una migración de prueba y después db/callbacks/afterMigrate__permisos_lectura.sql")
def _migracion_y_callback(ctx: Escenario) -> None:
    # La migración de prueba vuelve a crear las vistas, como una repetible R__, y con ello el rol pierde su SELECT.
    # El callback llega con el git subtree pull de preparacion-neon, que espera la fusión de T022, y T027 suma
    # filesystem:callbacks a db/flyway.toml. Mientras el archivo no exista el escenario se omite con esa razón, y
    # en cuanto exista corre entero, sin ningún cambio en estos pasos.
    if not CALLBACK.is_file():
        pytest.skip("db/callbacks/afterMigrate__permisos_lectura.sql llega con el git subtree pull de "
                    "preparacion-neon (T022 y T027)")
    _repetibles(ctx)
    _psql_ok(ctx, "-v", f"rol_app={ctx.api.base.rol_app}", "-f", str(CALLBACK))


@then(parsers.re(r"has_table_privilege\('abet_app', '(?P<tabla>[a-z_.]+)', '(?P<privilegio>[A-Z]+)'\) devuelve "
                 r"(?P<valor>verdadero|falso)"))
def _privilegio(ctx: Escenario, tabla: str, privilegio: str, valor: str) -> None:
    tiene = ctx.uno("SELECT has_table_privilege(%s, %s, %s)", ctx.api.base.rol_app, tabla, privilegio)
    assert tiene is (valor == "verdadero")


# US-03, el periodo 2026-2

@when(parsers.re(r'el administrador técnico ejecuta db/datos/periodo_2026_2_inventado\.sql'
                 r'(?: con los valores que entrega el coordinador)?'))
def _ejecutar_datos(ctx: Escenario) -> None:
    _psql_ok(ctx, "-f", str(DATOS_2026_2))


@then(parsers.re(r'abet\.catalogo_vigencia tiene 1 fila de Ambiental en 2026-2 con la versión "(?P<version>[^"]+)"'))
def _vigencia(ctx: Escenario, version: str) -> None:
    filas = ctx.filas("SELECT ca.nombre, cv.codigo FROM abet.catalogo_vigencia v JOIN abet.periodo p USING (periodo_id)"
                      " JOIN abet.carrera ca USING (carrera_id) JOIN abet.catalogo_version cv USING (catalogo_version_id)"
                      " WHERE p.codigo = '2026-2'")
    assert len(filas) == 1 and "Ambiental" in filas[0][0] and filas[0][1] == version, filas


@then(parsers.re(r'abet\.seccion tiene las secciones 410 y 411 de 450002 en 2026-2 con curso_blackboard '
                 r'"(?P<a>[^"]+)" y "(?P<b>[^"]+)"'))
def _secciones(ctx: Escenario, a: str, b: str) -> None:
    filas = ctx.filas("SELECT a.codigo, s.numero, s.curso_blackboard FROM abet.seccion s JOIN abet.asignatura a"
                      " USING (asignatura_id) JOIN abet.periodo p USING (periodo_id) WHERE p.codigo = '2026-2'"
                      " ORDER BY s.numero")
    assert filas == [("450002", "410", a), ("450002", "411", b)]


@then(parsers.re(r'abet\.plan_medicion tiene 3 filas de 450002 en 2026-2, con los PI 5\.1, 5\.2 y 5\.3 del SO 5'))
def _plan(ctx: Escenario) -> None:
    filas = ctx.filas("SELECT p.codigo, so.numero FROM abet.plan_medicion pm JOIN abet.asignatura a USING (asignatura_id)"
                      " JOIN abet.periodo pe USING (periodo_id) JOIN abet.pi p USING (pi_id)"
                      " JOIN abet.so so ON so.so_id = p.so_id WHERE a.codigo = '450002' AND pe.codigo = '2026-2'"
                      " ORDER BY p.codigo")
    assert filas == [("5.1", 5), ("5.2", 5), ("5.3", 5)]


@then(parsers.re(r'(?P<lista>abet\.\w+(?:(?:, | y )abet\.\w+)*) siguen con 0 filas'))
def _siguen_en_cero(ctx: Escenario, lista: str) -> None:
    assert set(_conteos(ctx, lista).values()) == {0}


@when("el administrador técnico lo ejecuta otra vez")
def _ejecutar_otra_vez(ctx: Escenario) -> None:
    ctx.extras["conteos"] = _conteos(ctx, "abet.catalogo_vigencia abet.seccion abet.plan_medicion "
                                          "acceso.usuario_autorizado acceso.docente_seccion")
    assert all(n > 0 for n in ctx.extras["conteos"].values()), "el primer paso no sembró todas las tablas"
    _psql_ok(ctx, "-f", str(DATOS_2026_2))


@then(parsers.re(r'(?P<lista>(?:abet|acceso)\.\w+(?:(?:, | y )(?:abet|acceso)\.\w+)*) tienen el mismo número de filas que '
                 r'después de la primera ejecución'))
def _mismos_conteos(ctx: Escenario, lista: str) -> None:
    ahora = _conteos(ctx, lista)
    assert ahora == {tabla: ctx.extras["conteos"][tabla] for tabla in ahora}


@when(parsers.re(r'el administrador técnico inserta la sección "0410" de 450002 en 2026-2'))
def _insertar_seccion_con_cero(ctx: Escenario) -> None:
    ctx.directa = ctx.api.dueno
    ctx.intentar("INSERT INTO abet.seccion (periodo_id, asignatura_id, numero) SELECT p.periodo_id, a.asignatura_id, '0410'"
                 " FROM abet.periodo p, abet.asignatura a WHERE p.codigo = '2026-2' AND a.codigo = '450002'")


@when("se buscan en periodo_2026_2_inventado.sql los números de 8 dígitos y los correos")
def _buscar_en_el_script(ctx: Escenario) -> None:
    texto = DATOS_2026_2.read_text(encoding="utf-8")
    ctx.extras["numeros"] = re.findall(r"(?<![0-9])[0-9]{8}(?![0-9])", texto)
    ctx.extras["correos"] = re.findall(r"[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+", texto)


@then("todo número de 8 dígitos empieza con 99")
def _numeros_inventados(ctx: Escenario) -> None:
    """Exige que todo número de 8 dígitos del script empiece con 99.

    Hoy periodo_2026_2_inventado.sql no trae ningún número de 8 dígitos, porque no siembra estudiantes, y el paso
    se cumple sin casos. Queda anotado en la propiedad «sin_casos» para que se vea en el informe. Si el script
    suma códigos, cada uno se comprueba sin cambiar nada aquí.
    """
    if not ctx.extras["numeros"]:
        ctx.request.node.user_properties.append(
            ("sin_casos", "periodo_2026_2_inventado.sql no trae números de 8 dígitos"))
    assert all(numero.startswith("99") for numero in ctx.extras["numeros"])


@then('todo correo termina en "@example.invalid"')
def _correos_inventados(ctx: Escenario) -> None:
    assert ctx.extras["correos"], "el script no trae ningún correo, así que no hay nada que comprobar"
    assert all(correo.endswith("@example.invalid") for correo in ctx.extras["correos"])


@given(parsers.re(r'la API configurada con PERIODO_VIGENTE "(?P<periodo>[^"]+)" y CONJUNTO_REGLAS "(?P<reglas>[^"]+)"'))
def _api_sin_arrancar(ctx: Escenario, periodo: str, reglas: str) -> None:
    """Prepara la API con el periodo y las reglas del paso, sin arrancarla, y con GUARDIA_DATOS_INVENTADOS encendida.

    El paso no nombra la guardia. Queda encendida, el valor del piloto, porque el escenario comprueba que el
    arranque se detiene por el periodo o las reglas, y la guardia no interviene en esa validación.
    """
    ctx.configurar_api(periodo, reglas, "1")


@when("la API arranca contra esa base")
def _arrancar_la_api(ctx: Escenario) -> None:
    ctx.antes = ctx.api.conteos()
    ctx.extras["arranque"] = None
    try:
        ctx.api.cliente()
    except ConfiguracionDeLaApi as falla:
        ctx.extras["arranque"] = str(falla)


@then(parsers.re(r'el arranque se detiene con el mensaje "(?P<mensaje>[^"]+)"'))
def _arranque_detenido(ctx: Escenario, mensaje: str) -> None:
    assert ctx.extras["arranque"] is not None, "la API arrancó con una configuración que la base no conoce"
    assert mensaje in ctx.extras["arranque"], ctx.extras["arranque"]


# US-04, el esquema acceso

@given('db/flyway.toml con schemas ["abet", "acceso"] en sus entornos')
def _flyway_con_acceso(ctx: Escenario) -> None:
    configuracion = tomllib.loads((RAIZ / "db" / "flyway.toml").read_text(encoding="utf-8"))
    entornos = configuracion["environments"]
    assert entornos and all(e["schemas"] == ["abet", "acceso"] for e in entornos.values())


@when(parsers.re(r'la prueba aplica V1_09__crear_acceso\.sql con psql(?:, como correr_pruebas\.sh)?'))
def _aplicar_v1_09(ctx: Escenario) -> None:
    ctx.extras["psql"] = _psql(ctx, "-1", "-f", str(V1_09), entorno={"PGOPTIONS": "-c client_min_messages=warning"})
    if ctx.extras["psql"].returncode == 0:
        _repetibles(ctx)


@then("psql termina con código de salida 0")
def _psql_cero(ctx: Escenario) -> None:
    corrida = ctx.extras["psql"]
    assert corrida.returncode == 0, corrida.stderr.strip()


@then(parsers.re(r'el esquema acceso tiene las tablas usuario_autorizado, credencial, sesion, intento_fallido, '
                 r'docente_seccion y codigo_acceso'))
def _tablas_de_acceso(ctx: Escenario) -> None:
    tablas = {f[0] for f in ctx.filas("SELECT table_name FROM information_schema.tables WHERE table_schema = 'acceso'"
                                      " AND table_type = 'BASE TABLE'")}
    assert tablas == {"usuario_autorizado", "credencial", "sesion", "intento_fallido", "docente_seccion",
                      "codigo_acceso"}


@then(parsers.re(r'abet\.carga tiene la columna subida_por, que admite nulo y tiene una FK hacia '
                 r'acceso\.usuario_autorizado'))
def _subida_por(ctx: Escenario) -> None:
    assert ctx.filas("SELECT is_nullable FROM information_schema.columns WHERE table_schema = 'abet'"
                     " AND table_name = 'carga' AND column_name = 'subida_por'") == [("YES",)]
    assert ctx.filas("SELECT a.attname, c.confrelid::regclass::text FROM pg_constraint c JOIN pg_attribute a"
                     " ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey) WHERE c.contype = 'f'"
                     " AND c.conrelid = 'abet.carga'::regclass AND a.attname = 'subida_por'") == [
        ("subida_por", "acceso.usuario_autorizado")]


def _motivos(texto: str) -> set[str]:
    return set(re.findall(r"'([A-Z_]+)'", texto))


@then(parsers.re(r'ck_rechazo_fila_motivo admite "(?P<a>[A-Z_]+)", "(?P<b>[A-Z_]+)", "(?P<c>[A-Z_]+)" y "(?P<d>[A-Z_]+)" '
                 r'además de los 10 motivos de V1_07'))
def _motivos_de_rechazo(ctx: Escenario, a: str, b: str, c: str, d: str) -> None:
    actuales = _motivos(ctx.uno("SELECT pg_get_constraintdef(oid) FROM pg_constraint"
                                " WHERE conname = 'ck_rechazo_fila_motivo'"))
    bloque = re.search(r"ck_rechazo_fila_motivo\s+CHECK \(motivo IN \((.*?)\)\)", V1_07.read_text(encoding="utf-8"), re.S)
    antiguos = _motivos(bloque[1])
    assert len(antiguos) == 10 and {a, b, c, d}.isdisjoint(antiguos)
    assert actuales == antiguos | {a, b, c, d}


@then(parsers.re(r'cada una de las consultas de control Q01 a Q14 sigue en 0 filas'))
def _controles_siguen_en_cero(ctx: Escenario) -> None:
    for nombre, consulta in _controles().items():
        assert ctx.filas(consulta) == [], f"{nombre} devuelve filas"


@then(parsers.re(r'esa carga sigue en estado "PUBLICADA" con subida_por nulo'))
def _carga_anterior(ctx: Escenario) -> None:
    assert ctx.filas("SELECT estado, subida_por FROM abet.carga c JOIN abet.seccion s USING (seccion_id)"
                     " WHERE s.numero = '410'") == [("PUBLICADA", None)]


@then(parsers.re(r'acceso\.usuario_autorizado tiene estos usuarios activos'))
def _usuarios_activos(ctx: Escenario, datatable: list[list[str]]) -> None:
    esperados = sorted((fila[0], fila[1]) for fila in datatable[1:])
    assert datatable[0] == ["correo", "rol"]
    assert ctx.filas("SELECT correo, rol FROM acceso.usuario_autorizado WHERE activo ORDER BY correo") == esperados


@then(parsers.re(r'acceso\.docente_seccion asigna la sección 410 de 450002 en 2026-2 a "(?P<d410>[^"]+)" y la sección '
                 r'411 a "(?P<d411>[^"]+)"'))
def _asignaciones(ctx: Escenario, d410: str, d411: str) -> None:
    filas = ctx.filas("SELECT u.correo, a.codigo, s.numero, p.codigo FROM acceso.docente_seccion d"
                      " JOIN acceso.usuario_autorizado u USING (usuario_id) JOIN abet.seccion s USING (seccion_id)"
                      " JOIN abet.asignatura a USING (asignatura_id) JOIN abet.periodo p USING (periodo_id)"
                      " ORDER BY s.numero")
    assert filas == [(d410, "450002", "410", "2026-2"), (d411, "450002", "411", "2026-2")]


@then(parsers.re(r'acceso\.docente_seccion no tiene filas de "(?P<correo>[^"]+)"'))
def _sin_filas_del_coordinador(ctx: Escenario, correo: str) -> None:
    assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion WHERE usuario_id = %s", ctx.usuario_id(correo)) == 0


@then(parsers.re(r'acceso\.credencial no tiene filas, porque la contraseña se asigna aparte con el comando de US-05'))
def _sin_credenciales(ctx: Escenario) -> None:
    assert ctx.uno("SELECT count(*) FROM acceso.credencial") == 0


@when(parsers.re(r'el administrador técnico (?P<accion>inserta el usuario "[^"]*" con rol "[^"]+"'
                 r'|inserta otra vez el usuario "[^"]*" con rol "[^"]+"'
                 r'|inserta el usuario "[^"]*" sin normalizar'
                 r'|asigna otra vez la sección 410 a "[^"]+"'
                 r'|asigna a "[^"]+" una seccion_id que no existe)'))
def _registro_invalido(ctx: Escenario, accion: str) -> None:
    ctx.directa = ctx.api.dueno
    if (usuario := re.fullmatch(r'inserta (?:otra vez )?el usuario "([^"]*)" con rol "([^"]+)"', accion)):
        ctx.intentar("INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES (%s, %s)", usuario[1], usuario[2])
    elif (usuario := re.fullmatch(r'inserta el usuario "([^"]*)" sin normalizar', accion)):
        ctx.intentar("INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES (%s, 'PROFESOR')", usuario[1])
    elif (otra := re.fullmatch(r'asigna otra vez la sección 410 a "([^"]+)"', accion)):
        ctx.intentar("INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) VALUES (%s, %s)",
                     ctx.usuario_id(otra[1]), ctx.seccion_id("410"))
    else:
        inexistente = re.fullmatch(r'asigna a "([^"]+)" una seccion_id que no existe', accion)
        assert inexistente is not None, accion
        ctx.intentar("INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) VALUES (%s, %s)",
                     ctx.usuario_id(inexistente[1]), 999999999)


@then(parsers.re(r'la base rechaza la fila por la restricción "(?P<restriccion>[a-z0-9_]+)"'))
def _fila_rechazada(ctx: Escenario, restriccion: str) -> None:
    assert isinstance(ctx.error_directo, psycopg.errors.IntegrityError), repr(ctx.error_directo)
    assert ctx.error_directo.diag.constraint_name == restriccion, ctx.error_directo.diag.constraint_name


@when("el administrador técnico corre la consulta de control Q04")
def _correr_q04(ctx: Escenario) -> None:
    ctx.extras["q04"] = ctx.filas(_controles()["Q04"])


@when("corre la consulta Q15, nueva en pruebas.sql, que aplica el filtro de columnas de Q04 al esquema acceso")
def _correr_q15(ctx: Escenario) -> None:
    assert "Q15" in (RAIZ / "db" / "pruebas" / "pruebas.sql").read_text(encoding="utf-8")
    q04 = _controles()["Q04"]
    assert "table_schema = 'abet'" in q04
    ctx.extras["q15"] = ctx.filas(q04.replace("table_schema = 'abet'", "table_schema = 'acceso'"))


@then("Q04 devuelve 0 filas")
def _q04_en_cero(ctx: Escenario) -> None:
    assert ctx.extras["q04"] == []


@then("Q15 devuelve solo la columna de correo de acceso.usuario_autorizado")
def _q15_solo_el_correo(ctx: Escenario) -> None:
    assert ctx.extras["q15"] == [("usuario_autorizado", "correo")]
