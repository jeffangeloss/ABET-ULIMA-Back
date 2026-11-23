"""Pasos de capacitacion_en_develop.feature (US-85, US-86 y US-89 de la spec 008), con pytest-bdd en español (T027).

El .feature manda. db/herramientas/sembrar_quimica.py corre como proceso aparte con python -I y las variables de libpq
de una base desechable del escenario, en el clúster desechable de tests/cluster_desechable.py y nunca en
localhost:5432 ni en Neon. El CSV de la programación se arma en tmp_path, fuera del repositorio, porque
cargar_programacion.py se niega a leer un archivo dentro de uno.

Aquí están los escenarios de US-86 que prueban el guion de la siembra sin los pasos que faltan. La siembra completa,
la segunda siembra, la programación por la ruta 4, el registro de la coordinación con en_windows.py y la lectura
de la siembra real esperan a registrar_coordinacion.py (T032), al periodo de la ruta 4 (T033) y al Windows de
Jefferson (T071), y los de Playwright y el cierre llegan con T053 y T056.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from pytest_bdd import given, parsers, scenario, then, when

Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/capacitacion_en_develop.feature"
SEMBRAR = RAIZ / "db" / "herramientas" / "sembrar_quimica.py"
# Valores inventados que el entorno de la siembra lleva y que ninguna salida debe repetir.
OTRAS_VARIABLES = {"PGPASSWORD": "clave-inventada-de-prueba", "CORREO_COORDINACION": "real.inventado@example.invalid",
                   "DESCRIPCION_INSTRUMENTO": "Texto de prueba del Portafolio 3"}


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
    """La siembra como proceso aparte. Con base, las variables de libpq apuntan a la base del escenario."""
    assert SEMBRAR.exists(), "falta db/herramientas/sembrar_quimica.py (T027)"
    entorno = {clave: valor for clave, valor in OTRAS_VARIABLES.items()}
    entorno["PATH"] = os.environ["PATH"]
    if base:
        entorno.update(ctx.plantillas.base_desechable._entorno())
        entorno["PGDATABASE"] = ctx.api.base.nombre
        entorno["PGPASSWORD"] = OTRAS_VARIABLES["PGPASSWORD"]
    if guardia is not None:
        entorno["GUARDIA_DATOS_INVENTADOS"] = guardia
    return subprocess.run([sys.executable, "-I", str(SEMBRAR), *argumentos], env=entorno, capture_output=True,
                          text=True, check=False)


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


# Cuando

@when(parsers.re(r'se revisa el orden'))
def _revisa(ctx: Escenario) -> None:
    pasos = ctx.extras["pasos"]
    ctx.extras["posicion"] = {nombre: pasos.index(nombre) for nombre in pasos}


@when(parsers.re(r'la siembra llega a la programación con --aplicar'))
def _siembra_programacion(ctx: Escenario) -> None:
    ctx.antes = ctx.conteos()
    ctx.extras["corrida"] = sembrar(ctx, "--rama", "develop", "--aplicar", "--desde", "programacion",
                                    "--programacion", str(ctx.extras["csv"]))


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
