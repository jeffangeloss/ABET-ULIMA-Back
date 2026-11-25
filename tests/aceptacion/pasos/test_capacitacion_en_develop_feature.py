"""Pasos de capacitacion_en_develop.feature (US-85, US-86 y US-89 de la spec 008), con pytest-bdd en español (T027).

El .feature manda. db/herramientas/sembrar_quimica.py corre como proceso aparte con python -I y las variables de libpq
de una base desechable del escenario, en el clúster desechable de tests/cluster_desechable.py y nunca en
localhost:5432 ni en Neon. El CSV de la programación se arma en tmp_path, fuera del repositorio, porque
cargar_programacion.py se niega a leer un archivo dentro de uno.

Aquí están los nueve escenarios de US-86. La siembra completa corre sobre una base en V1_11, como la rama
develop de hoy, primero en seco y después con --aplicar en los dos tramos que separa el despliegue del Back. Flyway no
alcanza el clúster desechable, que escucha solo en un socket de Unix, así que FLYWAY nombra un doble de prueba que
aplica las migraciones pendientes con psql -1, como tests/base_desechable.py, y después
db/callbacks/afterMigrate__permisos_lectura.sql, como Flyway al final de cada migrate. El rol de la aplicación nace en
V1_11, como abet_app en Neon, así que la siembra prueba también el SELECT de acceso.coordinacion_alcance que le da el
callback. La lectura que confirma el alcance corre db/plataforma/neon/alcance_capacitacion.sql por la entrada
estándar de psql, con la cabecera y el filtro de sql_lectura de herramientas_neon/lectura_neon.sh, sobre una copia con
18 secciones inventadas que la propia siembra carga desde la programación, y la corrida en develop queda para el
Windows de Jefferson (T071). Los de Playwright llegan con T053.

Los cinco escenarios de US-89 (T056) corren db/herramientas/cerrar_capacitacion.py como proceso aparte. La baja de
las cuentas corre sobre una copia desechable con la siembra inventada y el plan de 5643, y la comprobación del
respaldo sobre carpetas inventadas en tmp_path, con PGHOST en una carpeta que no existe, así que ninguna conexión llega
a un PostgreSQL de la Mac. El escenario de D-55 pone primero en el PATH unos dobles de neonctl, neon, flyway, git y
vercel que dejan una marca si alguien los llama, y compara el contenido de cada tabla de abet antes y después.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
from openpyxl import Workbook, load_workbook
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
CERRAR = RAIZ / "db" / "herramientas" / "cerrar_capacitacion.py"
CONCILIADOR = RAIZ / "db" / "herramientas" / "conciliar_tabla_maestra.py"
ROLES_DE_LECTURA = RAIZ / "db" / "plataforma" / "neon" / "crear_roles_lectura.sql"
# Las cuatro cuentas de la siembra inventada que el cierre da de baja (US-89).
CUENTAS_DE_LA_CAPACITACION = ("docente701@example.invalid", "docente702@example.invalid", "docente703@example.invalid",
                              "coordinador.quimica@example.invalid")
D_55 = "Destino de las cargas de Química General pendiente de decisión (D-55)."
# Programas que restablecen una rama de Neon, despliegan o escriben en un repositorio. El cierre no llama a ninguno.
DOBLES_PROHIBIDOS = ("neonctl", "neon", "flyway", "git", "vercel")
OCHO_CIFRAS = re.compile(r"(?<![0-9])[0-9]{8}(?![0-9])")
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
        # La base todavía no tiene V1_15, así que el R-17 de antes sale sin la declaración de la spec 005.
        ctx.extras["r17_antes"] = celdas(r17.generar(conexion, resultado.carga_id, carpeta,
                                                     exigir_declaracion=False).read_bytes())
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
    for ruta in ("/api/sesion", "/api/secciones"):
        assert cliente.get(ruta).status_code == 200, ruta
    assert ctx.uno("SELECT has_table_privilege(%s, 'acceso.coordinacion_alcance', 'SELECT')", ctx.api.base.rol_app)
    # Desde la spec 005 (US-49) la ruta 7 pide la declaración vigente, que una base en V1_14 no puede tener, así que
    # responde el 409 de la declaración pendiente, después del alcance, y no un 403 ni un 500. Las celdas se comparan
    # con el mismo generador y el rol de la aplicación, sin la declaración, como el R-17 de antes.
    pendiente = cliente.get(f"/api/cargas/{ctx.carga_id}/r17.xlsx")
    assert pendiente.status_code == 409 and pendiente.json()["detail"] == r17.DeclaracionPendiente.mensaje
    carpeta = _tmp(ctx) / "r17_despues"
    carpeta.mkdir()
    with psycopg.connect(ctx.api.base.conexion) as conexion:
        conexion.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(ctx.api.base.rol_app)))
        despues = celdas(r17.generar(conexion, ctx.carga_id, carpeta, exigir_declaracion=False).read_bytes())
    antes = ctx.extras["r17_antes"]
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


# La lectura sin correos que confirma el alcance después de la siembra de la capacitación (T071)

@scenario(FEATURE, "Después de la siembra de la capacitación, una lectura sin correos confirma el alcance")
def test_una_lectura_sin_correos_confirma_el_alcance() -> None:
    """Consulta de comprobación de la lectura de T071."""


ALCANCE = RAIZ / "db" / "plataforma" / "neon" / "alcance_capacitacion.sql"
# Las 18 secciones inventadas de la capacitación, de la 701 a la 718 de 5643 en 2026-1.
SECCIONES_DE_LA_CAPACITACION = tuple(str(numero) for numero in range(701, 719))
# La cabecera y el filtro de sql_lectura de herramientas_neon/lectura_neon.sh, que vive fuera del repositorio. La
# lectura de develop rechaza antes de enviarlo un SQL con alguno de estos patrones, y antepone la cabecera, que pasa
# la sesión a solo lectura.
CABECERA_DE_LA_LECTURA = ("\\set ON_ERROR_STOP 1\nSET default_transaction_read_only = on;\n"
                          "SELECT 'solo_lectura=' || current_setting('default_transaction_read_only');\n"
                          "SELECT 'rol=' || current_user;\n")
PROHIBIDOS_EN_LA_LECTURA = (
    r"read[\s_]+write", r"(?<![a-z_])reset(?![a-z_])", r"read_only\s*(=|to)\s*'?(off|false|0|no)\b",
    r"session\s+characteristics", r"(?<![a-z_])(set_config|pg_reload_conf)\s*\(",
    r"(?<![a-z_])(alter|create|drop|insert|update|delete|truncate|grant|revoke|copy|comment|vacuum|call)\s",
    r"\\(!|o|out|c|connect|copy|w|write|g|gx|gexec|i|ir|include|include_relative|setenv|cd|s|lo_\w+)(?![a-z_])",
)
NUMERO_DE_SECCION = re.compile(r"(?<![0-9])7(?:0[1-9]|1[0-8])(?![0-9])")
SQLSTATE_SOLO_LECTURA = "25006"


def sembrar_la_capacitacion(ctx: Escenario, correos: dict[str, str] | None = None) -> None:
    """La siembra con --aplicar desde la programación, con el CSV de las 18 secciones y la coordinación por
    CORREO_COORDINACION, sobre el plan de 5643 en 2026-1 y sin la siembra inventada de 701 a 704. Con correos, una
    sección toma el profesor de otra."""
    ctx.crear_base("quimica_plan_sin_secciones")
    ruta = escribir_programacion(ctx, SECCIONES_DE_LA_CAPACITACION)
    if correos:
        filas = ruta.read_text(encoding="utf-8").splitlines()
        for numero, otro in correos.items():
            filas = [fila.replace(f",docente{numero}@", f",docente{otro}@") for fila in filas]
        ruta.write_text("\n".join(filas) + "\n", encoding="utf-8")
    corrida = sembrar(ctx, "--rama", "develop", "--aplicar", "--desde", "programacion", "--programacion", str(ruta),
                      "--huella-antes", huella_de_ambiental(ctx))
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert ctx.uno("SELECT count(*) FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                   " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id"
                   " WHERE a.codigo = '5643' AND pe.codigo = '2026-1'") == len(SECCIONES_DE_LA_CAPACITACION)


def leer_el_alcance(ctx: Escenario) -> subprocess.CompletedProcess[str]:
    """La consulta de comprobación como la corre sql_lectura de lectura_neon.sh, por la entrada estándar de psql, con
    la cabecera de solo lectura y la sesión en solo lectura también por PGOPTIONS."""
    assert ALCANCE.exists(), "falta db/plataforma/neon/alcance_capacitacion.sql (T071)"
    consulta = ALCANCE.read_text(encoding="utf-8")
    for patron in PROHIBIDOS_EN_LA_LECTURA:
        assert not re.search(patron, consulta, re.IGNORECASE), f"lectura_neon.sh no envía la consulta ({patron})"
    entorno = {**_bd(ctx)._entorno(), "PGDATABASE": ctx.api.base.nombre, "PGCLIENTENCODING": "UTF8",
               "PGOPTIONS": "-c default_transaction_read_only=on"}
    corrida = subprocess.run([entorno.get("PSQL", "psql"), "-X", "-At", "-q", "-v", "ON_ERROR_STOP=1"],
                             input=CABECERA_DE_LA_LECTURA + consulta, env=entorno, capture_output=True, text=True,
                             encoding="utf-8", check=False)
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert "solo_lectura=on" in corrida.stdout.splitlines(), corrida.stdout
    return corrida


def conteos_del_alcance(corrida: subprocess.CompletedProcess[str]) -> dict[str, str]:
    """Cada línea «etiqueta|valor» de la consulta, sin la cabecera de la lectura."""
    lineas = [linea for linea in corrida.stdout.splitlines()
              if "|" in linea and not linea.startswith(("solo_lectura=", "rol="))]
    return dict(linea.split("|", 1) for linea in lineas)


@given(parsers.re(r'la rama develop con la siembra de la capacitación'))
def _develop_con_la_capacitacion(ctx: Escenario) -> None:
    sembrar_la_capacitacion(ctx)


@when(parsers.re(r'lectura_neon\.sh corre desde el Windows la consulta de comprobación(?: \(propuesta\))?'))
def _lectura_del_alcance(ctx: Escenario) -> None:
    ctx.extras["filas_antes"] = filas_por_tabla(ctx)
    ctx.extras["lectura"] = leer_el_alcance(ctx)


@then(parsers.re(r'cuenta (?P<secciones>[0-9]+) secciones de (?P<asignatura>[0-9]+) en (?P<periodo>[0-9]{4}-[0-2]) con '
                 r'plan, (?P<filas>[0-9]+) filas de acceso\.docente_seccion con (?P<profesores>[0-9]+) profesores '
                 r'distintos y (?P<alcance>[0-9]+) fila de alcance de (?P=asignatura) en (?P=periodo) que cubre las '
                 r'(?P<cubiertas>[0-9]+)'))
def _cuenta_el_alcance(ctx: Escenario, secciones: str, asignatura: str, periodo: str, filas: str, profesores: str,
                       alcance: str, cubiertas: str) -> None:
    assert conteos_del_alcance(ctx.extras["lectura"]) == {
        "asignatura": asignatura, "periodo": periodo, "secciones con plan": secciones,
        "filas de acceso.docente_seccion": filas, "profesores distintos": profesores, "filas de alcance": alcance,
        "secciones que cubre el alcance": cubiertas}
    assert filas_por_tabla(ctx) == ctx.extras["filas_antes"], "la lectura escribió en la base"


@then(parsers.re(r'la salida no trae correos ni códigos'))
def _sin_correos_ni_codigos(ctx: Escenario) -> None:
    corrida = ctx.extras["lectura"]
    salida = corrida.stdout + corrida.stderr
    assert "@" not in salida, "la lectura repite un correo"
    assert not OCHO_CIFRAS.search(salida), "la lectura trae un número de ocho cifras"
    assert "SINTETICO" not in salida, "la lectura repite un curso de Blackboard"
    assert not NUMERO_DE_SECCION.search(salida), "la lectura nombra una sección"


def test_la_lectura_del_alcance_cuenta_cada_profesor_una_vez(ctx: Escenario) -> None:
    """Fuera del .feature. Con la 718 a cargo del profesor de la 717, la lectura cuenta 18 filas de
    acceso.docente_seccion y 17 profesores distintos. Una sección de otra asignatura en 2026-1 y una de 5643 en 2026-2,
    cada una con su profesor, no cambian ninguna cifra."""
    sembrar_la_capacitacion(ctx, {"718": "717"})
    dueno = ctx.api.dueno
    for asignatura, periodo, numero in (("450002", "2026-1", "412"), ("5643", "2026-2", "719")):
        dueno.execute("INSERT INTO abet.seccion (periodo_id, asignatura_id, numero) SELECT pe.periodo_id,"
                      " a.asignatura_id, %s FROM abet.periodo pe, abet.asignatura a WHERE pe.codigo = %s"
                      " AND a.codigo = %s", (numero, periodo, asignatura))
        dueno.execute("INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) SELECT u.usuario_id, s.seccion_id"
                      " FROM acceso.usuario_autorizado u, abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                      " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id WHERE u.correo = %s"
                      " AND s.numero = %s AND a.codigo = %s AND pe.codigo = %s",
                      ("docente701@example.invalid", numero, asignatura, periodo))
    assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion d JOIN abet.seccion s USING (seccion_id)"
                   " WHERE s.numero IN ('412', '719')") == 2
    conteos = conteos_del_alcance(leer_el_alcance(ctx))
    assert conteos["secciones con plan"] == "18", conteos
    assert (conteos["filas de acceso.docente_seccion"], conteos["profesores distintos"]) == ("18", "17"), conteos
    assert (conteos["filas de alcance"], conteos["secciones que cubre el alcance"]) == ("1", "18"), conteos


def test_la_lectura_del_alcance_no_cubre_sin_una_coordinacion_activa(ctx: Escenario) -> None:
    """Fuera del .feature. Con la coordinación del curso dada de baja, la fila de alcance sigue y no cubre ninguna
    sección, y sin la fila la lectura cuenta 0 filas de alcance, sin cambiar las demás cifras."""
    sembrar_la_capacitacion(ctx)
    completo = conteos_del_alcance(leer_el_alcance(ctx))
    dueno = ctx.api.dueno
    dueno.execute("UPDATE acceso.usuario_autorizado SET activo = false WHERE correo = %s", (CORREO_COORDINACION,))
    de_baja = conteos_del_alcance(leer_el_alcance(ctx))
    assert (de_baja["filas de alcance"], de_baja["secciones que cubre el alcance"]) == ("1", "0"), de_baja
    dueno.execute("DELETE FROM acceso.coordinacion_alcance ca USING abet.asignatura a"
                  " WHERE a.asignatura_id = ca.asignatura_id AND a.codigo = '5643'")
    sin_alcance = conteos_del_alcance(leer_el_alcance(ctx))
    assert (sin_alcance["filas de alcance"], sin_alcance["secciones que cubre el alcance"]) == ("0", "0"), sin_alcance
    for etiqueta in ("secciones con plan", "filas de acceso.docente_seccion", "profesores distintos"):
        assert de_baja[etiqueta] == sin_alcance[etiqueta] == completo[etiqueta] == "18", etiqueta


def test_la_lectura_del_alcance_cuenta_solo_lo_que_declara(ctx: Escenario) -> None:
    """Fuera del .feature (cambio del 2026-11-24). Una fila de acceso.docente_seccion de una cuenta COORDINADOR y otra
    de una cuenta PROFESOR dada de baja suman a las filas y no a los profesores distintos, una fila de alcance de 5643
    en 2026-2 no suma a las filas de alcance y, sin el plan de 5643 en 2026-1, la lectura cuenta 0 secciones con plan.
    No debe contar como profesor a una cuenta que no es PROFESOR activa, ni el alcance de otro periodo, ni una sección
    sin plan."""
    sembrar_la_capacitacion(ctx)
    dueno = ctx.api.dueno
    dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol, activo)"
                  " VALUES ('docente.de.baja@example.invalid', 'PROFESOR', false)")
    for correo, numero in (("docente.de.baja@example.invalid", "701"), (CORREO_COORDINACION, "702")):
        dueno.execute("INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) SELECT u.usuario_id, s.seccion_id"
                      " FROM acceso.usuario_autorizado u, abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                      " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id WHERE u.correo = %s AND s.numero = %s"
                      " AND a.codigo = '5643' AND pe.codigo = '2026-1'", (correo, numero))
    dueno.execute("INSERT INTO acceso.coordinacion_alcance (usuario_id, asignatura_id, periodo_id)"
                  " SELECT u.usuario_id, a.asignatura_id, pe.periodo_id FROM acceso.usuario_autorizado u,"
                  " abet.asignatura a, abet.periodo pe WHERE u.correo = %s AND a.codigo = '5643'"
                  " AND pe.codigo = '2026-2'", (CORREO_COORDINACION,))
    assert ctx.uno("SELECT count(*) FROM acceso.coordinacion_alcance ca JOIN abet.asignatura a USING (asignatura_id)"
                   " WHERE a.codigo = '5643'") == 2
    conteos = conteos_del_alcance(leer_el_alcance(ctx))
    assert (conteos["filas de acceso.docente_seccion"], conteos["profesores distintos"]) == ("20", "18"), conteos
    assert (conteos["filas de alcance"], conteos["secciones que cubre el alcance"]) == ("1", "18"), conteos
    assert conteos["secciones con plan"] == "18", conteos
    borrados = dueno.execute("DELETE FROM abet.plan_medicion pm USING abet.asignatura a, abet.periodo pe"
                             " WHERE a.asignatura_id = pm.asignatura_id AND pe.periodo_id = pm.periodo_id"
                             " AND a.codigo = '5643' AND pe.codigo = '2026-1'").rowcount
    assert borrados > 0
    sin_plan = conteos_del_alcance(leer_el_alcance(ctx))
    assert sin_plan["secciones con plan"] == "0", sin_plan
    assert {etiqueta: valor for etiqueta, valor in sin_plan.items() if etiqueta != "secciones con plan"} == \
        {etiqueta: valor for etiqueta, valor in conteos.items() if etiqueta != "secciones con plan"}


def test_la_lectura_del_alcance_deja_la_sesion_en_solo_lectura_sin_la_cabecera(ctx: Escenario) -> None:
    """Fuera del .feature (cambio del 2026-11-24). Con la forma directa que documenta el archivo, psql -f sin la
    cabecera de sql_lectura y sin PGOPTIONS, la sesión debe quedar en solo lectura y rechazar una escritura posterior
    con el SQLSTATE 25006. No debe depender de la cabecera ni de PGOPTIONS ni cambiar ninguna fila."""
    ctx.crear_base("quimica_plan")
    antes = filas_por_tabla(ctx)
    entorno = {**_bd(ctx)._entorno(), "PGDATABASE": ctx.api.base.nombre, "PGCLIENTENCODING": "UTF8"}
    entorno.pop("PGOPTIONS", None)
    corrida = subprocess.run(
        [entorno.get("PSQL", "psql"), "-X", "-At", "-q", "-v", "ON_ERROR_STOP=1", "-v", "VERBOSITY=sqlstate",
         "-v", "asignatura=5643", "-v", "periodo=2026-1", "-f", str(ALCANCE),
         "-c", "SELECT 'solo_lectura=' || current_setting('default_transaction_read_only')",
         "-c", "UPDATE abet.periodo SET codigo = codigo WHERE false"],
        env=entorno, capture_output=True, text=True, encoding="utf-8", check=False)
    assert "solo_lectura=on" in corrida.stdout.splitlines(), corrida.stdout + corrida.stderr
    assert corrida.returncode != 0, "la sesión aceptó una escritura después de la consulta"
    assert SQLSTATE_SOLO_LECTURA in corrida.stderr, corrida.stderr
    assert filas_por_tabla(ctx) == antes


# US-89, el cierre de la capacitación (T056)

@scenario(FEATURE, "Las cuentas de ejemplo se dan de baja en seco primero y pierden su sesión")
def test_las_cuentas_de_ejemplo_se_dan_de_baja() -> None:
    """T056."""


@scenario(FEATURE, "El cierre comprueba el respaldo por huella y no borra nada")
def test_el_cierre_comprueba_el_respaldo() -> None:
    """T056."""


@scenario(FEATURE, "Un respaldo incompleto se informa y no se recomienda borrar")
def test_un_respaldo_incompleto_se_informa() -> None:
    """T056."""


@scenario(FEATURE, "Sin decisión sobre el destino de las cargas, el cierre no toca develop ni main")
def test_sin_d_55_el_cierre_no_toca_develop_ni_main() -> None:
    """T056."""


@scenario(FEATURE, "Después del cierre la conciliación de develop sigue disponible")
def test_despues_del_cierre_la_conciliacion_sigue() -> None:
    """T056."""


def cerrar(ctx: Escenario, *argumentos: str, base: bool = True,
           camino: Path | None = None) -> subprocess.CompletedProcess[str]:
    """El cierre como proceso aparte con python -I. Con base, las variables de libpq apuntan a la copia del escenario,
    y sin base PGHOST nombra una carpeta que no existe, así ninguna conexión llega a un PostgreSQL de la Mac."""
    assert CERRAR.exists(), "falta db/herramientas/cerrar_capacitacion.py (T056)"
    if base:
        entorno = {**_bd(ctx)._entorno(), "PGDATABASE": ctx.api.base.nombre}
    else:
        entorno = {"PATH": os.environ["PATH"], "PGHOST": str(_tmp(ctx) / "sin_servidor"), "PGDATABASE": "ninguna"}
    if camino is not None:
        entorno["PATH"] = f"{camino}{os.pathsep}{entorno['PATH']}"
    corrida = subprocess.run([sys.executable, "-I", str(CERRAR), *argumentos], env=entorno, capture_output=True,
                             text=True, encoding="utf-8", check=False, cwd=_tmp(ctx))
    salida = corrida.stdout + corrida.stderr
    assert "@" not in salida, "la salida del cierre repite un correo"
    assert not OCHO_CIFRAS.search(salida), "la salida del cierre trae un número de ocho cifras"
    ctx.extras["cierre"] = corrida
    return corrida


def cuentas(ctx: Escenario) -> list[tuple[Any, ...]]:
    return ctx.filas("SELECT correo, rol, activo FROM acceso.usuario_autorizado ORDER BY correo")


def sesiones(ctx: Escenario) -> list[tuple[Any, ...]]:
    return ctx.filas("SELECT sesion_id, usuario_id, expira_en FROM acceso.sesion ORDER BY sesion_id")


def contenido_de_abet(ctx: Escenario) -> dict[str, str]:
    """La huella del contenido de cada tabla de abet, fila por fila."""
    tablas = ctx.filas("SELECT table_name FROM information_schema.tables WHERE table_schema = 'abet'"
                       " AND table_type = 'BASE TABLE' ORDER BY 1")
    return {tabla: ctx.uno(sql.SQL("SELECT coalesce(md5(string_agg(t::text, '|' ORDER BY t::text)), '') FROM abet.{} t")
                           .format(sql.Identifier(tabla))) for (tabla,) in tablas}


def con_cuentas_de_la_capacitacion(ctx: Escenario) -> None:
    """La siembra inventada con el plan de 5643, la sesión de docente701 y su carga PUBLICADA de la 701."""
    ctx.crear_base("quimica_plan")
    contenido, nombre = ctx.export_de_quimica("701")
    respuesta = A.subir(ctx.sesion("docente701@example.invalid"), ctx.seccion_de("701"), contenido, nombre)
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "PUBLICADA", respuesta.text
    ctx.carga_id = respuesta.json()["carga_id"]
    assert ctx.sesion("docente701@example.invalid").get("/api/sesion").status_code == 200
    escribir_programacion(ctx)
    activas = dict((correo, activo) for correo, _, activo in cuentas(ctx))
    assert all(activas[correo] for correo in CUENTAS_DE_LA_CAPACITACION)


def carpeta_de_la_capacitacion(ctx: Escenario) -> Path:
    """Tres exports inventados de la 701, la 702 y la 703 y su manifiesto, con la forma que escribe el generador."""
    if "capacitacion" in ctx.extras:
        return ctx.extras["capacitacion"]
    carpeta = _tmp(ctx) / "capacitacion_inventada"
    carpeta.mkdir()
    entradas = []
    for numero in ("701", "702", "703"):
        contenido, nombre = ctx.export_de_quimica(numero)
        (carpeta / nombre).write_bytes(contenido)
        entradas.append({"seccion": numero, "archivo": nombre, "sha256": hashlib.sha256(contenido).hexdigest(),
                         "filas": 4})
    manifiesto = {"periodo": "2026-1", "asignatura": "5643", "pi": "6.1", "exports": entradas}
    (carpeta / "manifiesto.json").write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2) + "\n",
                                             encoding="utf-8")
    ctx.extras["capacitacion"] = carpeta
    ctx.extras["huellas"] = huellas_de(carpeta)
    return carpeta


def huellas_de(carpeta: Path) -> dict[str, str]:
    return {ruta.name: hashlib.sha256(ruta.read_bytes()).hexdigest() for ruta in sorted(carpeta.iterdir())}


def respaldo_de(ctx: Escenario, sin: int = 0) -> Path:
    """Copia inventada de la carpeta de la capacitación, como la que restaura el respaldo, sin los últimos exports."""
    carpeta = carpeta_de_la_capacitacion(ctx)
    respaldo = _tmp(ctx) / "respaldo_restaurado"
    shutil.copytree(carpeta, respaldo)
    exports = sorted(ruta for ruta in respaldo.iterdir() if ruta.suffix == ".xlsx")
    for ruta in exports[len(exports) - sin:] if sin else []:
        ruta.unlink()
    ctx.extras["respaldo"] = respaldo
    ctx.extras["huellas_respaldo"] = huellas_de(respaldo)
    return respaldo


def _maestra_inventada(ctx: Escenario) -> Path:
    """Tabla maestra inventada en tmp_path con los mismos niveles que los exports de export_de_quimica()."""
    columnas = ("AÑO", "CICLO", "CÓDIGO DEL CURSO", "CURSO", "CICLO DEL CURSO", "SO", "PI", "PROFESOR",
                "CÓDIGO DEL ESTUDIANTE", "SECCIÓN", "CALIFICACIÓN", "ARCHIVO")
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Tabla maestra"
    hoja.append(list(columnas))
    for numero in ("701", "702", "703"):
        for n, nivel in enumerate((3, 4, 2, 3), start=1):
            hoja.append([2026, 1, "5643", "QUÍMICA GENERAL", 1, "6", "6.1", f"Docente Inventado {numero}",
                         str(99100000 + int(numero) * 100 + n), numero, nivel, f"R017_inventado_{numero}.xlsx"])
    ruta = _tmp(ctx) / "entrada" / "tabla_maestra_inventada.xlsx"
    ruta.parent.mkdir(exist_ok=True)
    libro.save(ruta)
    return ruta


def conciliar(ctx: Escenario) -> subprocess.CompletedProcess[str]:
    """El conciliador de US-83 con el rol abet_respaldo, que crea crear_roles_lectura.sql en la copia del escenario."""
    if not ctx.extras.get("roles"):
        for plugin in ctx.request.config.pluginmanager.get_plugins():
            if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
                plugin.correr_guion(ctx.api.dueno, ROLES_DE_LECTURA, {})
                ctx.extras["roles"] = True
        assert ctx.extras.get("roles"), "no se encuentra tests/aceptacion/pasos/conftest.py"
    entorno = {**_bd(ctx)._entorno(), "PGDATABASE": ctx.api.base.nombre, "PGUSER": "abet_respaldo"}
    return subprocess.run([sys.executable, "-I", str(CONCILIADOR), "--maestra", str(ctx.extras["maestra"]), "--periodo",
                           "2026-1", "--asignatura", "5643", "--pi", "6.1"], env=entorno, capture_output=True,
                          text=True, encoding="utf-8", check=False, cwd=_tmp(ctx))


def dobles_prohibidos(ctx: Escenario) -> Path:
    """Dobles de los programas que restablecen develop, despliegan o escriben en main, que dejan una marca."""
    carpeta = _tmp(ctx) / "dobles_prohibidos"
    carpeta.mkdir()
    marca = _tmp(ctx) / "llamadas_prohibidas.txt"
    for nombre in DOBLES_PROHIBIDOS:
        doble = carpeta / nombre
        doble.write_text(f"#!/bin/sh\necho {nombre} >> '{marca}'\nexit 1\n", encoding="utf-8")
        doble.chmod(0o755)
    ctx.extras["marca"] = marca
    return carpeta


# Dado

@given(parsers.re(r'una base desechable con la siembra inventada, la sesión vigente de "(?P<correo>[^"]+)" y una carga '
                  r'PUBLICADA de la 701'))
def _siembra_con_sesion(ctx: Escenario, correo: str) -> None:
    assert correo == "docente701@example.invalid"
    con_cuentas_de_la_capacitacion(ctx)


@given(parsers.re(r'una carpeta inventada de la capacitación en tmp_path con 3 exports y su manifiesto'))
def _carpeta_inventada(ctx: Escenario) -> None:
    carpeta = carpeta_de_la_capacitacion(ctx)
    assert len([r for r in carpeta.iterdir() if r.suffix == ".xlsx"]) == 3


@given(parsers.re(r'un respaldo inventado cuyas huellas coinciden con el manifiesto'))
def _respaldo_completo(ctx: Escenario) -> None:
    respaldo_de(ctx)
    assert ctx.extras["huellas_respaldo"] == ctx.extras["huellas"]


@given(parsers.re(r'un respaldo inventado al que le falta un export del manifiesto'))
def _respaldo_incompleto(ctx: Escenario) -> None:
    respaldo_de(ctx, sin=1)
    assert len(ctx.extras["huellas_respaldo"]) == len(ctx.extras["huellas"]) - 1


@given(parsers.re(r'D-55 sin respuesta'))
def _d_55_sin_respuesta(ctx: Escenario) -> None:
    spec = (RAIZ / "specs" / "008-ciclo-quimica-industrial" / "spec.md").read_text(encoding="utf-8")
    fila = next(linea for linea in spec.splitlines() if linea.startswith("| D-55 |"))
    assert "Quedan en develop, sin pasar a main" in fila
    con_cuentas_de_la_capacitacion(ctx)
    ctx.extras["abet_antes"] = contenido_de_abet(ctx)


@given(parsers.re(r'el cierre ya corrido con --aplicar'))
def _cierre_ya_corrido(ctx: Escenario) -> None:
    con_cuentas_de_la_capacitacion(ctx)
    for numero in ("702", "703"):
        contenido, nombre = ctx.export_de_quimica(numero)
        respuesta = A.subir(ctx.sesion(f"docente{numero}@example.invalid"), ctx.seccion_de(numero), contenido, nombre)
        assert respuesta.status_code == 201 and respuesta.json()["estado"] == "PUBLICADA", respuesta.text
    ctx.extras["maestra"] = _maestra_inventada(ctx)
    antes = conciliar(ctx)
    assert antes.returncode == 0 and "3 de 3 secciones iguales." in antes.stdout, antes.stdout + antes.stderr
    ctx.extras["conciliacion_antes"] = antes.stdout
    corrida = cerrar(ctx, "--programacion", str(ctx.extras["csv"]), "--periodo", "2026-1", "--aplicar")
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    activas = dict((correo, activo) for correo, _, activo in cuentas(ctx))
    assert not any(activas[correo] for correo in CUENTAS_DE_LA_CAPACITACION)


# Cuando

@when(parsers.re(r'db/herramientas/cerrar_capacitacion\.py corre con el CSV de la programación sin --aplicar'
                 r'(?: \(propuesta\))?'))
def _cierre_en_seco(ctx: Escenario) -> None:
    ctx.extras["cuentas_antes"], ctx.extras["sesiones_antes"] = cuentas(ctx), sesiones(ctx)
    corrida = cerrar(ctx, "--programacion", str(ctx.extras["csv"]), "--periodo", "2026-1")
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    ctx.extras["seco"] = corrida


@when(parsers.re(r'corre con --aplicar'))
def _cierre_aplicado(ctx: Escenario) -> None:
    ctx.extras["cuentas_antes"] = cuentas(ctx)
    corrida = cerrar(ctx, "--programacion", str(ctx.extras["csv"]), "--periodo", "2026-1", "--aplicar")
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr


@when(parsers.re(r'el cierre comprueba el respaldo'))
def _comprueba_el_respaldo(ctx: Escenario) -> None:
    cerrar(ctx, "--capacitacion", str(carpeta_de_la_capacitacion(ctx)), "--respaldo", str(ctx.extras["respaldo"]),
           base=False)


@when(parsers.re(r'el cierre corre con --aplicar'))
def _cierre_con_aplicar(ctx: Escenario) -> None:
    respaldo_de(ctx)
    corrida = cerrar(ctx, "--programacion", str(ctx.extras["csv"]), "--periodo", "2026-1", "--capacitacion",
                     str(carpeta_de_la_capacitacion(ctx)), "--respaldo", str(ctx.extras["respaldo"]), "--aplicar",
                     camino=dobles_prohibidos(ctx))
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr


@when(parsers.re(r'el conciliador de US-83 corre sobre develop con el rol abet_respaldo'))
def _concilia_despues(ctx: Escenario) -> None:
    ctx.extras["conciliacion"] = conciliar(ctx)


# Entonces

@then(parsers.re(r'el informe dice que daría de baja 3 cuentas de profesor y 1 de coordinación, sin repetir los '
                 r'correos'))
def _informe_en_seco(ctx: Escenario) -> None:
    salida = ctx.extras["seco"].stdout
    assert "Daría de baja 3 cuentas de profesor y 1 de coordinación" in salida, salida
    assert "No se guardó nada, y --aplicar lo guarda." in salida, salida
    for correo in CUENTAS_DE_LA_CAPACITACION:
        assert correo.split("@")[0] not in salida


@then(parsers.re(r'ninguna cuenta cambia'))
def _ninguna_cambia(ctx: Escenario) -> None:
    assert cuentas(ctx) == ctx.extras["cuentas_antes"]
    assert sesiones(ctx) == ctx.extras["sesiones_antes"]


@then(parsers.re(r'las 4 cuentas quedan con activo falso'))
def _cuatro_de_baja(ctx: Escenario) -> None:
    antes = {correo: (rol, activo) for correo, rol, activo in ctx.extras["cuentas_antes"]}
    despues = {correo: (rol, activo) for correo, rol, activo in cuentas(ctx)}
    assert sorted(despues) == sorted(antes)
    for correo, (rol, activo) in despues.items():
        esperado = False if correo in CUENTAS_DE_LA_CAPACITACION else antes[correo][1]
        assert (rol, activo) == (antes[correo][0], esperado), correo
    assert any(activo for correo, (_, activo) in despues.items()), "el cierre dio de baja otras cuentas"
    assert "Dio de baja 3 cuentas de profesor y 1 de coordinación" in ctx.extras["cierre"].stdout


@then(parsers.re(r'la ruta 2 con la cookie de "(?P<correo>[^"]+)" responde 401'))
def _sin_sesion(ctx: Escenario, correo: str) -> None:
    assert ctx.sesiones[correo].get("/api/sesion").status_code == 401
    assert ctx.uno("SELECT count(*) FROM acceso.sesion s JOIN acceso.usuario_autorizado u USING (usuario_id)"
                   " WHERE u.correo = %s AND s.expira_en > now()", correo) == 0


@then(parsers.re(r'la ruta 1 con su correo responde el mismo 401 que un correo desconocido'))
def _ingreso_como_desconocido(ctx: Escenario) -> None:
    correo = "docente701@example.invalid"
    propio = ctx.api.cliente().post("/api/sesion", json={"correo": correo, "contrasena": ctx.api.claves[correo]})
    desconocido = ctx.api.cliente().post("/api/sesion", json={"correo": "desconocido@example.invalid",
                                                               "contrasena": secrets.token_urlsafe(18)})
    assert propio.status_code == desconocido.status_code == 401
    assert propio.json() == desconocido.json()
    assert "set-cookie" not in propio.headers


@then(parsers.re(r'la carga PUBLICADA de la 701 sigue PUBLICADA'))
def _carga_sigue(ctx: Escenario) -> None:
    assert ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", ctx.carga_id) == "PUBLICADA"


@then(parsers.re(r'dice «(?P<mensaje>[^»]+)»(?: \(propuesta\))?'))
def _dice(ctx: Escenario, mensaje: str) -> None:
    corrida = ctx.extras["cierre"]
    assert mensaje in corrida.stdout.splitlines(), corrida.stdout + corrida.stderr


@then(parsers.re(r'los 3 exports siguen en la carpeta'))
def _siguen(ctx: Escenario) -> None:
    assert ctx.extras["cierre"].returncode == 0
    assert huellas_de(ctx.extras["capacitacion"]) == ctx.extras["huellas"]
    assert huellas_de(ctx.extras["respaldo"]) == ctx.extras["huellas_respaldo"]


@then(parsers.re(r'termina con código 1'))
def _codigo_1(ctx: Escenario) -> None:
    corrida = ctx.extras["cierre"]
    assert corrida.returncode == 1, corrida.stdout + corrida.stderr
    assert "Se pueden borrar" not in corrida.stdout
    assert huellas_de(ctx.extras["capacitacion"]) == ctx.extras["huellas"]


@then(parsers.re(r'no restablece develop ni escribe en main'))
def _no_toca_develop_ni_main(ctx: Escenario) -> None:
    assert not ctx.extras["marca"].exists(), ctx.extras["marca"].read_text(encoding="utf-8")
    assert contenido_de_abet(ctx) == ctx.extras["abet_antes"]
    assert ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", ctx.carga_id) == "PUBLICADA"
    assert "Dio de baja 3 cuentas de profesor y 1 de coordinación" in ctx.extras["cierre"].stdout


@then(parsers.re(r'lee las cargas PUBLICADA de 5643 en 2026-1 como antes del cierre'))
def _lee_como_antes(ctx: Escenario) -> None:
    corrida = ctx.extras["conciliacion"]
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert corrida.stdout == ctx.extras["conciliacion_antes"]
    assert "3 de 3 secciones iguales." in corrida.stdout


# Pruebas del cierre fuera del .feature (T056). Lo que el cierre no debe dar de baja.

def test_el_cierre_no_da_de_baja_una_cuenta_con_algo_fuera_de_la_capacitacion(ctx: Escenario) -> None:
    """Un profesor del CSV que dicta también la 410 de 2026-2, una coordinación con otro curso y la coordinación de
    Ambiental, que suma el alcance de 5643 a su carrera, quedan activos, los profesores de 2026-2 no cambian, y una
    segunda corrida no da de baja a nadie."""
    con_cuentas_de_la_capacitacion(ctx)
    ctx.filas("INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) VALUES (%s, %s) RETURNING 1",
              ctx.usuario_id("docente702@example.invalid"), ctx.seccion_de("410"))
    ctx.filas("INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES ('coordinador.doble@example.invalid',"
              " 'COORDINADOR') RETURNING 1")
    ctx.filas("INSERT INTO acceso.coordinacion_alcance (usuario_id, asignatura_id, periodo_id)"
              " SELECT u.usuario_id, a.asignatura_id, pe.periodo_id FROM acceso.usuario_autorizado u,"
              " abet.asignatura a, abet.periodo pe WHERE u.correo = 'coordinador.doble@example.invalid'"
              " AND a.codigo IN ('5643', '450002') AND pe.codigo = '2026-1' RETURNING 1")
    ambiental = ctx.uno("SELECT u.correo FROM acceso.usuario_autorizado u JOIN acceso.coordinacion_alcance ca"
                        " USING (usuario_id) WHERE ca.carrera_id IS NOT NULL")
    ctx.filas("INSERT INTO acceso.coordinacion_alcance (usuario_id, asignatura_id, periodo_id)"
              " SELECT u.usuario_id, a.asignatura_id, pe.periodo_id FROM acceso.usuario_autorizado u,"
              " abet.asignatura a, abet.periodo pe WHERE u.correo = %s AND a.codigo = '5643' AND pe.codigo = '2026-1'"
              " RETURNING 1", ambiental)
    antes = {correo: activo for correo, _, activo in cuentas(ctx)}
    corrida = cerrar(ctx, "--programacion", str(ctx.extras["csv"]), "--periodo", "2026-1", "--aplicar")
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert "Dio de baja 2 cuentas de profesor y 1 de coordinación" in corrida.stdout
    assert ("3 cuentas tienen secciones o alcance fuera de 5643 en 2026-1 y quedan activas."
            in corrida.stdout.splitlines())
    despues = {correo: activo for correo, _, activo in cuentas(ctx)}
    dadas_de_baja = {"docente701@example.invalid", "docente703@example.invalid", "coordinador.quimica@example.invalid"}
    assert {correo for correo, activo in despues.items() if antes[correo] and not activo} == dadas_de_baja
    assert despues["docente702@example.invalid"] and despues["coordinador.doble@example.invalid"] and despues[ambiental]
    otra = cerrar(ctx, "--programacion", str(ctx.extras["csv"]), "--periodo", "2026-1", "--aplicar")
    assert otra.returncode == 0, otra.stdout + otra.stderr
    assert "Dio de baja 0 cuentas de profesor y 0 de coordinación" in otra.stdout
    assert "3 cuentas ya estaban dadas de baja." in otra.stdout.splitlines()
    assert {correo: activo for correo, _, activo in cuentas(ctx)} == despues


def test_el_cierre_cuenta_los_correos_sin_cuenta_y_no_crea_ninguna(ctx: Escenario) -> None:
    """Un correo de la programación sin cuenta de profesor se cuenta sin mostrarlo, y la base no gana filas."""
    con_cuentas_de_la_capacitacion(ctx)
    ruta = escribir_programacion(ctx, ("701", "702", "703", "704"))
    filas = ruta.read_text(encoding="utf-8").replace("docente704@", "ausente704@")
    ruta.write_text(filas, encoding="utf-8")
    antes = filas_por_tabla(ctx)
    corrida = cerrar(ctx, "--programacion", str(ruta), "--periodo", "2026-1")
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert "1 correo de la programación no tiene una cuenta de profesor." in corrida.stdout.splitlines()
    assert "Daría de baja 3 cuentas de profesor y 1 de coordinación" in corrida.stdout
    assert filas_por_tabla(ctx) == antes
