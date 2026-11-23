"""Pasos de capacitacion_en_develop.feature (US-85, US-86 y US-89 de la spec 008), con pytest-bdd en español (T027).

El .feature manda. db/herramientas/sembrar_quimica.py corre como proceso aparte con python -I y las variables de libpq
de una base desechable del escenario, en el clúster desechable de tests/cluster_desechable.py y nunca en
localhost:5432 ni en Neon. El CSV de la programación se arma en tmp_path, fuera del repositorio, porque
cargar_programacion.py se niega a leer un archivo dentro de uno.

Aquí están ocho de los nueve escenarios de US-86. La siembra completa corre sobre una base en V1_11, como la rama
develop de hoy, primero en seco y después con --aplicar en los dos tramos que separa el despliegue del Back. Flyway no
alcanza el clúster desechable, que escucha solo en un socket de Unix, así que FLYWAY nombra un doble de prueba que
aplica las migraciones pendientes con psql -1, como tests/base_desechable.py, y después
db/callbacks/afterMigrate__permisos_lectura.sql, como Flyway al final de cada migrate. El rol de la aplicación nace en
V1_11, como abet_app en Neon, así que la siembra prueba también el SELECT de acceso.coordinacion_alcance que le da el
callback. La lectura de la siembra real espera al Windows de Jefferson (T071), y los de Playwright y el cierre llegan
con T053 y T056.
"""

from __future__ import annotations

import importlib.util
import io
import os
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
from openpyxl import load_workbook
from psycopg import sql
from pytest_bdd import given, parsers, scenario, then, when

from abet_carga import r17
from abet_carga.carga import Configuracion, cargar

Escenario = Any
A = sys.modules["api_de_prueba"]
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/capacitacion_en_develop.feature"
SEMBRAR = RAIZ / "db" / "herramientas" / "sembrar_quimica.py"
PROGRAMACION = RAIZ / "db" / "herramientas" / "cargar_programacion.py"
HUELLA = RAIZ / "db" / "plataforma" / "neon" / "huella_ambiental.sql"
CORREO_COORDINACION = "real.inventado@example.invalid"
# Valores inventados que el entorno de la siembra lleva y que ninguna salida debe repetir.
OTRAS_VARIABLES = {"PGPASSWORD": "clave-inventada-de-prueba", "CORREO_COORDINACION": CORREO_COORDINACION,
                   "DESCRIPCION_INSTRUMENTO": "Texto de prueba del Portafolio 3"}


@scenario(FEATURE, "La siembra completa deja la misma huella de Ambiental y los controles limpios")
def test_la_siembra_completa_deja_la_misma_huella() -> None:
    """Corrección del 2026-11-23 a T027."""


@scenario(FEATURE, "La programación de Química acepta 2026-1 y una asignatura de cuatro cifras")
def test_la_programacion_de_quimica_acepta_2026_1() -> None:
    """Corrección del 2026-11-23 a T027."""


@scenario(FEATURE, "Una segunda siembra completa no suma filas")
def test_una_segunda_siembra_completa_no_suma_filas() -> None:
    """Corrección del 2026-11-23 a T027."""


@scenario(FEATURE, "Ninguna salida de la siembra repite el correo de la coordinación")
def test_ninguna_salida_repite_el_correo_de_la_coordinacion() -> None:
    """Corrección del 2026-11-23 a T027."""


@scenario(FEATURE, "El alcance de Ambiental queda antes que la vigencia de Industrial")
def test_el_alcance_de_ambiental_queda_antes_que_la_vigencia() -> None:
    """T027."""


@scenario(FEATURE, "Un paso que falla deja la base como estaba en ese paso y detiene los siguientes")
def test_un_paso_que_falla_detiene_los_siguientes() -> None:
    """T027."""


@scenario(FEATURE, "La rama principal exige una confirmación aparte")
def test_la_rama_principal_exige_una_confirmacion_aparte() -> None:
    """T027."""


@scenario(FEATURE, "La versión de prueba acepta los códigos que no empiezan con 99")
def test_la_version_de_prueba_acepta_los_codigos() -> None:
    """T027."""


# Ayudas

def modulo() -> ModuleType:
    """db/herramientas/sembrar_quimica.py cargado por su ruta, porque db/ no es un paquete."""
    assert SEMBRAR.exists(), "falta db/herramientas/sembrar_quimica.py (T027)"
    especificacion = importlib.util.spec_from_file_location("sembrar_quimica", SEMBRAR)
    assert especificacion is not None and especificacion.loader is not None
    cargado = importlib.util.module_from_spec(especificacion)
    # dataclasses busca el módulo en sys.modules mientras lo carga.
    sys.modules["sembrar_quimica"] = cargado
    especificacion.loader.exec_module(cargado)
    return cargado


def sembrar(ctx: Escenario | None, *argumentos: str, guardia: str | None = "0",
            base: bool = True) -> subprocess.CompletedProcess[str]:
    """La siembra como proceso aparte. Con base, las variables de libpq apuntan a la base del escenario, y FLYWAY al
    doble de prueba de la base, si el escenario lo armó."""
    assert SEMBRAR.exists(), "falta db/herramientas/sembrar_quimica.py (T027)"
    entorno = {clave: valor for clave, valor in OTRAS_VARIABLES.items()}
    entorno["PATH"] = os.environ["PATH"]
    if base:
        entorno.update(_bd(ctx)._entorno())
        entorno["PGDATABASE"] = ctx.api.base.nombre
        entorno["PGPASSWORD"] = OTRAS_VARIABLES["PGPASSWORD"]
        entorno.update(ctx.extras.get("flyway", {}))
    if guardia is not None:
        entorno["GUARDIA_DATOS_INVENTADOS"] = guardia
    return subprocess.run([sys.executable, "-I", str(SEMBRAR), *argumentos], env=entorno, capture_output=True,
                          text=True, check=False)


def _bd(ctx: Escenario) -> ModuleType:
    return ctx.plantillas.base_desechable


def _tmp(ctx: Escenario) -> Path:
    return ctx.request.getfixturevalue("tmp_path")


# Doble de Flyway para la siembra de las pruebas. Recibe los argumentos del paso «migraciones» con la carpeta db/ como
# carpeta de trabajo, lleva la última versión aplicada en el archivo de HISTORIAL_DEL_DOBLE_DE_FLYWAY, como
# flyway_schema_history, aplica cada migración pendiente hasta -target con psql -1 y, al final de cada migrate, corre
# el callback afterMigrate, como Flyway con locations = ["filesystem:migration", "filesystem:callbacks"].
DOBLE_DE_FLYWAY = '''
import os
import subprocess
import sys
from pathlib import Path

argumentos = sys.argv[1:]
if "-configFiles=flyway.toml" not in argumentos or "-environment=neon" not in argumentos:
    sys.exit("el doble de Flyway espera -configFiles=flyway.toml y -environment=neon")


def version(texto):
    return tuple(int(parte) for parte in texto.split("."))


def de_la_migracion(ruta):
    return version(ruta.name[1:].split("__", 1)[0].replace("_", "."))


historial = Path(os.environ["HISTORIAL_DEL_DOBLE_DE_FLYWAY"])
aplicada = version(historial.read_text(encoding="utf-8").strip())
objetivos = [version(a.split("=", 1)[1]) for a in argumentos if a.startswith("-target=")]
pendientes = sorted((ruta for ruta in Path("migration").glob("V*__*.sql") if de_la_migracion(ruta) > aplicada
                     and (not objetivos or de_la_migracion(ruta) <= objetivos[0])), key=de_la_migracion)
psql = [os.environ.get("PSQL", "psql"), "-X", "-q", "-v", "ON_ERROR_STOP=1"]
entorno = {**os.environ, "PGOPTIONS": "-c client_min_messages=warning"}
if "info" in argumentos:
    for ruta in pendientes:
        print(f"Pending  {ruta.name}")
    sys.exit(0)
if "migrate" not in argumentos:
    sys.exit("el doble de Flyway solo conoce info y migrate")
for ruta in pendientes:
    corrida = subprocess.run([*psql, "-1", "-f", str(ruta)], env=entorno, capture_output=True, text=True)
    if corrida.returncode != 0:
        sys.exit(corrida.stderr)
    historial.write_text(".".join(str(parte) for parte in de_la_migracion(ruta)), encoding="utf-8")
    print(f"Migrating schema abet with {ruta.name}")
corrida = subprocess.run([*psql, "-f", "callbacks/afterMigrate__permisos_lectura.sql"], env=entorno,
                         capture_output=True, text=True)
if corrida.returncode != 0:
    sys.exit(corrida.stderr)
print(f"Successfully applied {len(pendientes)} migrations" if pendientes
      else "Schema abet is up to date. No migration necessary.")
'''


def armar_flyway(ctx: Escenario, aplicada: str) -> None:
    """Deja en tmp_path el doble de Flyway con la última versión aplicada de la base del escenario."""
    carpeta = _tmp(ctx) / "flyway_de_prueba"
    carpeta.mkdir(exist_ok=True)
    doble = carpeta / "flyway"
    doble.write_text(f"#!{sys.executable} -I\n{DOBLE_DE_FLYWAY}", encoding="utf-8")
    doble.chmod(0o755)
    historial = carpeta / "historial.txt"
    historial.write_text(aplicada, encoding="utf-8")
    ctx.extras["flyway"] = {"FLYWAY": str(doble), "HISTORIAL_DEL_DOBLE_DE_FLYWAY": str(historial)}


def escribir_programacion(ctx: Escenario, numeros: tuple[str, ...] = ("701", "702", "703")) -> Path:
    """CSV inventado de la programación de 5643 en 2026-1 en tmp_path, con un profesor y un curso por sección."""
    ruta = _tmp(ctx) / "programacion_20261_inventada.csv"
    filas = "".join(f"2026-1,5643,{n},docente{n}@example.invalid,SINTETICO_20261_5643_{n}\n" for n in numeros)
    ruta.write_text("periodo,asignatura,seccion,correo,curso_blackboard\n" + filas, encoding="utf-8")
    ctx.extras["csv"] = ruta
    return ruta


def huella_de_ambiental(ctx: Escenario) -> str:
    """La huella completa de la última fila de huella_ambiental.sql sobre la base del escenario."""
    entorno = _bd(ctx)._entorno()
    corrida = subprocess.run([entorno.get("PSQL", "psql"), "-X", "-q", "-At", "-v", "ON_ERROR_STOP=1", "-d",
                              ctx.api.base.nombre, "-f", str(HUELLA)], env=entorno, capture_output=True, text=True,
                             check=False)
    assert corrida.returncode == 0, corrida.stderr
    ultima = corrida.stdout.strip().splitlines()[-1]
    assert ultima.startswith("HUELLA DE AMBIENTAL|"), ultima
    return ultima.split("|")[-1]


def filas_por_tabla(ctx: Escenario) -> dict[str, int]:
    """Número de filas de cada tabla de abet y de acceso."""
    tablas = ctx.filas("SELECT table_schema, table_name FROM information_schema.tables"
                       " WHERE table_schema IN ('abet', 'acceso') AND table_type = 'BASE TABLE' ORDER BY 1, 2")
    return {f"{esquema}.{tabla}": int(ctx.uno(sql.SQL("SELECT count(*) FROM {}.{}").format(
        sql.Identifier(esquema), sql.Identifier(tabla)))) for esquema, tabla in tablas}


def siembra_completa(ctx: Escenario) -> dict[str, subprocess.CompletedProcess[str]]:
    """La siembra en el orden de FR-020, primero en seco y después con --aplicar en los dos tramos del despliegue.

    El primer tramo empieza en huella_antes, porque el respaldo cifrado sale solo de Neon, y se detiene en el
    despliegue con la orden que lo reanuda. Antes del segundo tramo, los pasos que siguen corren otra vez en seco, ya
    con V1_12 a V1_14 en la base. Devuelve la corrida de cada tramo.
    """
    programacion = ("--programacion", str(ctx.extras["csv"]))
    antes = filas_por_tabla(ctx)
    corridas = {"seco": sembrar(ctx, "--rama", "develop", *programacion)}
    assert corridas["seco"].returncode == 0, corridas["seco"].stdout + corridas["seco"].stderr
    assert "Siembra terminada en seco. No se guardó nada." in corridas["seco"].stdout
    assert filas_por_tabla(ctx) == antes, "la siembra en seco escribió en la base"
    corridas["tramo_1"] = sembrar(ctx, "--rama", "develop", "--aplicar", "--desde", "huella_antes", *programacion)
    salida = corridas["tramo_1"].stdout
    assert corridas["tramo_1"].returncode == 1, salida + corridas["tramo_1"].stderr
    reanudar = re.search(r"--desde plan_quimica --back-desplegado --huella-antes ([0-9a-f]{64})", salida)
    assert reanudar is not None, salida
    huella = reanudar[1]
    corridas["seco_tras_despliegue"] = sembrar(ctx, "--rama", "develop", "--desde", "plan_quimica", "--huella-antes",
                                               huella, *programacion)
    assert corridas["seco_tras_despliegue"].returncode == 0, corridas["seco_tras_despliegue"].stdout
    corridas["tramo_2"] = sembrar(ctx, "--rama", "develop", "--aplicar", "--desde", "plan_quimica", "--back-desplegado",
                                  "--huella-antes", huella, *programacion)
    assert corridas["tramo_2"].returncode == 0, corridas["tramo_2"].stdout + corridas["tramo_2"].stderr
    for corrida in corridas.values():
        _sin_otras_variables(corrida)
    ctx.extras["huella_antes"] = huella
    return corridas


def celdas(libro: bytes) -> dict[tuple[str, str], object]:
    """Cada celda con valor del libro, por hoja y coordenada."""
    abierto = load_workbook(io.BytesIO(libro))
    return {(hoja.title, celda.coordinate): celda.value for hoja in abierto.worksheets for fila in hoja.iter_rows()
            for celda in fila if celda.value is not None}


def _sin_otras_variables(corrida: subprocess.CompletedProcess[str]) -> None:
    salida = corrida.stdout + corrida.stderr
    for valor in OTRAS_VARIABLES.values():
        assert valor not in salida, "la salida repite el valor de una variable del entorno"


# Dado

@given(parsers.re(r'la lista ordenada de pasos de la siembra'))
def _lista(ctx: Escenario) -> None:
    ctx.extras["pasos"] = [paso.nombre for paso in modulo().PASOS]


@given(parsers.re(r'un CSV de programación con una fila de sección "(?P<numero>[0-9]+)"'))
def _csv_con_seccion(ctx: Escenario, numero: str) -> None:
    ctx.crear_base("quimica")
    ruta = ctx.request.getfixturevalue("tmp_path") / "programacion_20261_inventada.csv"
    ruta.write_text("periodo,asignatura,seccion,correo,curso_blackboard\n"
                    f"2026-1,5643,{numero},docente701@example.invalid,SINTETICO_20261_5643_{numero}\n", encoding="utf-8")
    ctx.extras["csv"] = ruta


@given(parsers.re(r'la API de la versión de prueba con GUARDIA_DATOS_INVENTADOS "(?P<valor>[01])", como fija D-10'))
def _api_de_prueba(ctx: Escenario, valor: str) -> None:
    ctx.crear_base("periodo")
    ctx.extras["guardia"] = valor


@given(parsers.re(r'una base desechable que imita la rama develop, con V1_01 a V1_11, la 410 y la 411 de 450002 y una '
                  r'carga PUBLICADA inventada de la 410'))
def _develop_en_v1_11(ctx: Escenario) -> None:
    ctx.crear_base("catalogo_industrial")
    assert ctx.uno("SELECT to_regclass('acceso.coordinacion_alcance') IS NULL"), "la base ya tiene V1_14"
    assert ctx.uno("SELECT count(*) FROM abet.catalogo_version WHERE codigo = 'IND-2026'") == 0
    assert ctx.filas("SELECT s.numero FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                     " WHERE a.codigo = '450002' ORDER BY 1") == [("410",), ("411",)]
    # La carga entra con abet_carga y el dueño, como la subiría el Back de hoy, porque la ruta 5 del Back nuevo pide
    # V1_14 desde el ingreso. El R-17 de antes sale del mismo generador que usa la ruta 12.
    with psycopg.connect(ctx.api.base.conexion) as conexion:
        resultado = cargar(conexion, A.archivo(A.CORRECTO), nombre_archivo=A.CORRECTO, seccion_id=ctx.seccion_id("410"),
                           usuario_id=ctx.usuario_id(A.DOCENTE_410), configuracion=Configuracion(conjunto_reglas=A.REGLAS))
        assert resultado.carga_id is not None, resultado
        assert ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", resultado.carga_id) == "PUBLICADA"
        carpeta = _tmp(ctx) / "r17_antes"
        carpeta.mkdir()
        ctx.extras["r17_antes"] = celdas(r17.generar(conexion, resultado.carga_id, carpeta).read_bytes())
    ctx.carga_id = resultado.carga_id
    armar_flyway(ctx, "1.11")
    escribir_programacion(ctx)


@given(parsers.re(r'la huella de Ambiental tomada con db/plataforma/neon/huella_ambiental\.sql'))
def _huella_tomada(ctx: Escenario) -> None:
    ctx.extras["huella"] = huella_de_ambiental(ctx)


@given(parsers.re(r'el CSV inventado de la programación con la 701, la 702 y la 703 de "5643" en "2026-1" y su '
                  r'curso_blackboard'))
def _csv_inventado(ctx: Escenario) -> None:
    ctx.crear_base("quimica_plan_sin_secciones")
    assert ctx.uno("SELECT count(*) FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                   " WHERE a.codigo = '5643'") == 0
    escribir_programacion(ctx)


@given(parsers.re(r'que la siembra completa ya corrió'))
def _siembra_ya_corrio(ctx: Escenario) -> None:
    ctx.crear_base("catalogo_industrial")
    armar_flyway(ctx, "1.11")
    escribir_programacion(ctx)
    siembra_completa(ctx)


@given(parsers.re(r'la variable CORREO_COORDINACION con "(?P<correo>[^"]+)"'))
def _variable_del_correo(ctx: Escenario, correo: str) -> None:
    assert correo == OTRAS_VARIABLES["CORREO_COORDINACION"]
    ctx.crear_base("quimica_plan")
    assert ctx.uno("SELECT count(*) FROM acceso.usuario_autorizado WHERE correo = %s", correo) == 0


# Cuando

@when(parsers.re(r'se aplican en orden V1_12, V1_13, V1_14 con alcance_coordinacion_ambiental\.sql, el plan de '
                 r'Química, la programación inventada y la coordinación inventada, cada paso primero en seco'))
def _aplican_en_orden(ctx: Escenario) -> None:
    ctx.extras["corridas"] = siembra_completa(ctx)


@when(parsers.re(r'cargar_programacion\.py corre con --periodo 2026-1 y --aplicar'))
def _carga_la_programacion(ctx: Escenario) -> None:
    ctx.extras["secciones_antes"] = ctx.cuenta("seccion")
    entorno = {**_bd(ctx)._entorno(), "PGDATABASE": ctx.api.base.nombre}
    ctx.extras["corrida"] = subprocess.run([sys.executable, "-I", str(PROGRAMACION), "--periodo", "2026-1",
                                            "--archivo", str(ctx.extras["csv"]), "--aplicar"], env=entorno,
                                           capture_output=True, text=True, check=False)
    assert ctx.extras["corrida"].returncode == 0, ctx.extras["corrida"].stdout + ctx.extras["corrida"].stderr


@when(parsers.re(r'corre otra vez con los mismos archivos'))
def _corre_otra_vez(ctx: Escenario) -> None:
    ctx.extras["filas_antes"] = filas_por_tabla(ctx)
    ctx.extras["corridas"] = siembra_completa(ctx)


@when(parsers.re(r'la siembra corre el registro de la coordinación con la variable en su entorno, como la deja '
                 r'en_windows\.py'))
def _registro_de_la_coordinacion(ctx: Escenario) -> None:
    huella = huella_de_ambiental(ctx)
    ctx.extras["corridas"] = {
        modo: sembrar(ctx, "--rama", "develop", *aplicar, "--desde", "coordinacion", "--huella-antes", huella)
        for modo, aplicar in (("seco", ()), ("aplicada", ("--aplicar",)))}
    for corrida in ctx.extras["corridas"].values():
        assert corrida.returncode == 0, corrida.stdout + corrida.stderr


@when(parsers.re(r'se revisa el orden'))
def _revisa(ctx: Escenario) -> None:
    pasos = ctx.extras["pasos"]
    ctx.extras["posicion"] = {nombre: pasos.index(nombre) for nombre in pasos}


@when(parsers.re(r'la siembra llega a la programación con --aplicar'))
def _siembra_programacion(ctx: Escenario) -> None:
    ctx.antes = ctx.conteos()
    ctx.extras["corrida"] = sembrar(ctx, "--rama", "develop", "--aplicar", "--desde", "programacion",
                                    "--programacion", str(ctx.extras["csv"]), "--huella-antes", huella_de_ambiental(ctx))


@when(parsers.re(r'un paso que escribe recibe --rama principal sin --confirmo-principal'))
def _principal_sin_confirmar(ctx: Escenario) -> None:
    # Sin variables de libpq ni base, así un intento de conexión fallaría con otro código y otro mensaje.
    ctx.extras["corrida"] = sembrar(None, "--rama", "principal", "--aplicar", base=False)


@when(parsers.re(r'la comprobación previa de la siembra pide la configuración de la API'))
def _comprobacion_previa(ctx: Escenario) -> None:
    ctx.extras["corrida"] = sembrar(ctx, "--rama", "develop", "--solo-comprobar", guardia=ctx.extras["guardia"])


# Entonces

@then(parsers.re(r'V1_14 y alcance_coordinacion_ambiental\.sql corren antes del despliegue del Back con el _ALCANCE '
                 r'nuevo'))
def _alcance_antes_del_despliegue(ctx: Escenario) -> None:
    posicion = ctx.extras["posicion"]
    assert posicion["respaldo"] < posicion["huella_antes"] < posicion["migraciones"] < posicion["alcance_ambiental"]
    assert posicion["alcance_ambiental"] < posicion["despliegue"]
    migraciones = next(paso for paso in modulo().PASOS if paso.nombre == "migraciones")
    assert "1.14" in " ".join(migraciones.aplicado)


@then(parsers.re(r'el despliegue corre antes de plan_quimica_2026_1\.sql, que registra la vigencia de IND-2026 en '
                 r'2026-1'))
def _despliegue_antes_del_plan(ctx: Escenario) -> None:
    posicion = ctx.extras["posicion"]
    assert posicion["despliegue"] < posicion["plan_quimica"] < posicion["programacion"] < posicion["coordinacion"]
    assert posicion["coordinacion"] < posicion["contrasenas"] < posicion["huella_despues"] < posicion["controles"]
    plan = next(paso for paso in modulo().PASOS if paso.nombre == "plan_quimica")
    assert "db/datos/plan_quimica_2026_1.sql" in " ".join(plan.aplicado)


@then(parsers.re(r'la programación termina con código 1 con «(?P<mensaje>[^»]+)»'))
def _programacion_falla(ctx: Escenario, mensaje: str) -> None:
    corrida = ctx.extras["corrida"]
    assert corrida.returncode == 1, corrida.stdout + corrida.stderr
    assert mensaje in corrida.stdout
    assert "El paso «programacion» terminó con el código 1. Los pasos siguientes no corren." in corrida.stdout
    _sin_otras_variables(corrida)


@then(parsers.re(r'la coordinación y las contraseñas no corren'))
def _no_corren(ctx: Escenario) -> None:
    salida = ctx.extras["corrida"].stdout
    assert "== Paso programacion" in salida
    assert "== Paso coordinacion" not in salida and "== Paso contrasenas" not in salida


@then(parsers.re(r'termina con código 2 antes de conectarse'))
def _codigo_2(ctx: Escenario) -> None:
    corrida = ctx.extras["corrida"]
    assert corrida.returncode == 2, corrida.stdout + corrida.stderr
    assert "La rama principal pide también --confirmo-principal. No se conectó ni escribió nada." in corrida.stderr
    assert "== Paso" not in corrida.stdout


@then(parsers.re(r'informa que la guardia de datos inventados está apagada, sin mostrar ninguna otra variable'))
def _guardia_apagada(ctx: Escenario) -> None:
    corrida = ctx.extras["corrida"]
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert "La guardia de datos inventados está apagada en la API (GUARDIA_DATOS_INVENTADOS en 0)." in corrida.stdout
    _sin_otras_variables(corrida)


@then(parsers.re(r'con GUARDIA_DATOS_INVENTADOS "1" la comprobación se detiene antes de sembrar con «(?P<mensaje>[^»]+)»'
                 r'(?: \(propuesta\))?'))
def _guardia_encendida(ctx: Escenario, mensaje: str) -> None:
    # Una siembra con --aplicar desde el último paso, que no pide el CSV ni el respaldo, se detiene igual.
    corrida = sembrar(ctx, "--rama", "develop", "--aplicar", "--desde", "controles", guardia="1")
    assert corrida.returncode == 1 and mensaje in corrida.stderr, corrida.stdout + corrida.stderr
    assert "== Paso" not in corrida.stdout
    sin_variable = sembrar(ctx, "--rama", "develop", "--solo-comprobar", guardia=None)
    assert sin_variable.returncode == 2 and "Falta GUARDIA_DATOS_INVENTADOS" in sin_variable.stderr


@then(parsers.re(r'la comprobación informa que abet\.estudiante no tiene ck_estudiante_codigo_inventado en la rama '
                 r'develop, y se detiene si la tiene, con «(?P<mensaje>[^»]+)»(?: \(propuesta\))?'))
def _guardia_en_la_base(ctx: Escenario, mensaje: str) -> None:
    assert "abet.estudiante no tiene ck_estudiante_codigo_inventado." in ctx.extras["corrida"].stdout
    ctx.crear_base("guardia")
    con_guardia = sembrar(ctx, "--rama", "develop", "--aplicar", "--desde", "controles")
    assert con_guardia.returncode == 1 and mensaje in con_guardia.stderr, con_guardia.stdout + con_guardia.stderr
    assert "== Paso" not in con_guardia.stdout


@then(parsers.re(r'huella_ambiental\.sql devuelve la misma huella que antes'))
def _misma_huella(ctx: Escenario) -> None:
    assert huella_de_ambiental(ctx) == ctx.extras["huella"]
    assert ctx.extras["huella_antes"] == ctx.extras["huella"]
    assert "La huella de Ambiental es la misma antes y después de la siembra." in ctx.extras["corridas"]["tramo_2"].stdout


@then(parsers.re(r'controles_neon\.sql termina con «(?P<mensaje>[^»]+)»(?: \(propuesta\))?'))
def _controles_limpios(ctx: Escenario, mensaje: str) -> None:
    salida = ctx.extras["corridas"]["tramo_2"].stdout
    assert salida.index("== Paso controles") < salida.rindex(mensaje), salida
    assert salida.rstrip().endswith("Siembra terminada con --aplicar."), salida


@then(parsers.re(r'el R-17 de la carga de la 410 sale con las mismas celdas que antes, comparadas una por una'))
def _mismo_r17(ctx: Escenario) -> None:
    # Con el Back nuevo y el rol de la aplicación que nació en V1_11, como abet_app en Neon. El ingreso y la ruta 12
    # leen acceso.coordinacion_alcance, así que sin el SELECT del callback responden 500.
    cliente = ctx.sesion(A.DOCENTE_410)
    for ruta in ("/api/sesion", "/api/secciones", f"/api/cargas/{ctx.carga_id}/r17.xlsx"):
        assert cliente.get(ruta).status_code == 200, ruta
    assert ctx.uno("SELECT has_table_privilege(%s, 'acceso.coordinacion_alcance', 'SELECT')", ctx.api.base.rol_app)
    descarga = cliente.get(f"/api/cargas/{ctx.carga_id}/r17.xlsx")
    despues, antes = celdas(descarga.content), ctx.extras["r17_antes"]
    assert len(antes) > 50, "el R-17 de antes no trae las celdas de la carga"
    assert sorted(despues) == sorted(antes)
    for clave, valor in antes.items():
        assert despues[clave] == valor, f"la celda {clave} cambió"


@then(parsers.re(r'abet\.seccion gana las tres secciones con su curso_blackboard'))
def _tres_secciones(ctx: Escenario) -> None:
    assert ctx.cuenta("seccion") == ctx.extras["secciones_antes"] + 3
    assert ctx.filas("SELECT s.numero, s.curso_blackboard FROM abet.seccion s JOIN abet.asignatura a"
                     " USING (asignatura_id) JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
                     " WHERE a.codigo = '5643' AND pe.codigo = '2026-1' ORDER BY 1") == [
        (n, f"SINTETICO_20261_5643_{n}") for n in ("701", "702", "703")]
    assert "Resumen. 3 secciones nuevas, 3 usuarios nuevos y 3 asignaciones nuevas." in ctx.extras["corrida"].stdout


@then(parsers.re(r'"(?P<correo>[^"]+)" recibe solo la (?P<numero>[0-9]+) en GET /api/secciones\?periodo=2026-1'))
def _recibe_solo(ctx: Escenario, correo: str, numero: str) -> None:
    respuesta = ctx.sesion(correo).get("/api/secciones?periodo=2026-1")
    assert respuesta.status_code == 200, respuesta.text
    assert [(f["asignatura"]["codigo"], f["numero"], f["periodo"]) for f in respuesta.json()] == [
        ("5643", numero, "2026-1")]


@then(parsers.re(r'cada informe resume 0 filas nuevas'))
def _cero_filas_nuevas(ctx: Escenario) -> None:
    corridas = ctx.extras["corridas"]
    primero, segundo = corridas["tramo_1"].stdout, corridas["tramo_2"].stdout
    assert "Schema abet is up to date. No migration necessary." in primero, primero
    assert "Alcance de Ambiental guardado. 0 filas nuevas de alcance de la carrera AMB." in primero, primero
    for informe in ("Plan de Química General en 2026-1 guardado. Registró 0 vigencias y 0 filas de plan de medición.",
                    "Resumen. 0 secciones nuevas, 0 usuarios nuevos y 0 asignaciones nuevas.",
                    "La cuenta de coordinación ya existe y ya tiene el alcance de 5643 en 2026-1. Registró 0 filas "
                    "nuevas."):
        assert informe in segundo, segundo


@then(parsers.re(r'el número de filas de cada tabla de abet y de acceso es el mismo que antes'))
def _mismas_filas(ctx: Escenario) -> None:
    assert filas_por_tabla(ctx) == ctx.extras["filas_antes"]


@then(parsers.re(r'ni los informes ni la salida de la siembra muestran el valor de esa variable'))
def _sin_el_correo(ctx: Escenario) -> None:
    corridas = ctx.extras["corridas"]
    assert "Registraría 1 cuenta de coordinación nueva" in corridas["seco"].stdout
    assert "Registró 1 cuenta de coordinación nueva" in corridas["aplicada"].stdout
    for corrida in corridas.values():
        salida = corrida.stdout + corrida.stderr
        for forma in (CORREO_COORDINACION, CORREO_COORDINACION.upper(), CORREO_COORDINACION.split("@")[0]):
            assert forma not in salida, "la salida repite el correo de la coordinación"
        _sin_otras_variables(corrida)
    assert ctx.uno("SELECT count(*) FROM acceso.usuario_autorizado WHERE correo = %s AND rol = 'COORDINADOR'",
                   CORREO_COORDINACION) == 1
