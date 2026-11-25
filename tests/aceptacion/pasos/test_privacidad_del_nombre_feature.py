"""Pasos de privacidad_del_nombre.feature (US-99 de la spec 010, BR-R17-07 y BR-R17-14), con pytest-bdd en español.

El .feature manda. El nombre del profesor sale solo en D10 de la hoja «Cursos de Carrera», y estas pruebas lo buscan en las
demás celdas y partes del libro, en las respuestas de las rutas de sesión y de cargas, en el registro abet.api y en los
archivos que git rastrea. Las bases son las del clúster desechable de tests/cluster_desechable.py, nunca localhost:5432 ni
Neon. Los Antecedentes y la generación del R-17 viven en el conftest.py de esta carpeta, porque profesores_en_el_r17.feature
los repite, y la revisión de las semillas y de los CSV rastreados vive en tests/semillas_inventadas.py, que
tests/test_semillas_con_nombre.py prueba aparte. Ningún mensaje de falla repite un nombre ni un correo.

El texto «(propuesta)» al final de un paso solo marca que la línea no está fijada en las decisiones de la spec, y el paso
exige la línea completa igual.
"""

from __future__ import annotations

import importlib.util
import io
import logging
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest
from openpyxl import load_workbook
from pytest_bdd import given, parsers, scenario, then, when

Escenario = Any
FEATURE = "specs/010-nombre-del-profesor/aceptacion/privacidad_del_nombre.feature"
A = sys.modules["api_de_prueba"]
C = sys.modules["cargas_de_prueba"]
RAIZ = Path(__file__).resolve().parents[3]
HOJA = "Cursos de Carrera"
NOMBRE_701 = "Profesor Inventado Setecientos Uno"
CORREO_701 = "docente701@example.invalid"
PROPUESTA = r"(?: \(propuestas?\))?"


@scenario(FEATURE, "Fuera de D10 el libro no repite el nombre")
def test_fuera_de_d10_el_libro_no_repite_el_nombre() -> None:
    """US-99, escenario 1."""


@scenario(FEATURE, "Las rutas de cargas y de sesión no traen el nombre")
def test_las_rutas_de_cargas_y_de_sesion_no_traen_el_nombre() -> None:
    """US-99, escenario 2."""


@scenario(FEATURE, "El registro de la aplicación no trae el nombre")
def test_el_registro_de_la_aplicacion_no_trae_el_nombre() -> None:
    """US-99, escenario 3."""


@scenario(FEATURE, "Las semillas solo traen nombres inventados con correos de example.invalid")
def test_las_semillas_solo_traen_nombres_inventados() -> None:
    """US-99, escenario 4, FR-013."""


@scenario(FEATURE, "Git no rastrea un archivo de programación con la columna nombre fuera de los datos inventados")
def test_git_no_rastrea_un_csv_con_la_columna_nombre() -> None:
    """US-99, escenario 5, FR-013."""


def _conftest(ctx: Escenario) -> Any:
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            return plugin
    raise AssertionError("no se encuentra tests/aceptacion/pasos/conftest.py")


def _semillas() -> Any:
    """tests/semillas_inventadas.py cargado por su ruta, porque tests/ no es un paquete."""
    if "semillas_inventadas" not in sys.modules:
        especificacion = importlib.util.spec_from_file_location("semillas_inventadas", RAIZ / "tests" / "semillas_inventadas.py")
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[especificacion.name] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules["semillas_inventadas"]


def _libro(ctx: Escenario) -> Any:
    respuesta = ctx.extras["libros_010"][-1]
    assert respuesta.status_code == 200, f"la ruta 7 respondió {respuesta.status_code}"
    return respuesta, load_workbook(io.BytesIO(respuesta.content))


# Escenario 1, el libro

@then(parsers.re(r'ninguna celda fuera de D10 de la hoja «Cursos de Carrera» trae "(?P<nombre>[^"]+)"'))
def _ninguna_celda_fuera_de_d10(ctx: Escenario, nombre: str) -> None:
    _, libro = _libro(ctx)
    hoja = libro[HOJA]
    assert hoja["D10"].value == nombre, "D10 no trae el nombre, así que la prueba no comprobaría nada"
    con_el_nombre = [celda.coordinate for fila in hoja.iter_rows() for celda in fila
                     if celda.coordinate != "D10" and isinstance(celda.value, str) and nombre in celda.value]
    assert con_el_nombre == []


@then(parsers.re(r'la hoja «Constancia» no trae "(?P<nombre>[^"]+)"'))
def _constancia_sin_el_nombre(ctx: Escenario, nombre: str) -> None:
    _, libro = _libro(ctx)
    assert [c.coordinate for fila in libro["Constancia"].iter_rows() for c in fila
            if isinstance(c.value, str) and nombre in c.value] == []
    assert any(isinstance(c.value, str) and CORREO_701 in c.value for fila in libro["Constancia"].iter_rows() for c in fila)


@then(parsers.re(r'ni el nombre del archivo ni docProps traen "(?P<nombre>[^"]+)"'))
def _ni_el_archivo_ni_las_propiedades(ctx: Escenario, nombre: str) -> None:
    respuesta, _ = _libro(ctx)
    cabecera = respuesta.headers.get("content-disposition", "")
    assert cabecera, "la ruta 7 no nombra el archivo"
    assert nombre not in cabecera and "Profesor" not in cabecera
    with zipfile.ZipFile(io.BytesIO(respuesta.content)) as zip_:
        partes = {n: zip_.read(n) for n in zip_.namelist()}
    # sharedStrings.xml y la hoja «Cursos de Carrera» traen el nombre por diseño. Se revisan docProps y las demás hojas.
    revisadas = [n for n in partes if n.startswith("docProps/") or n == "xl/worksheets/sheet2.xml"]
    assert len(revisadas) >= 3, revisadas
    assert [n for n in revisadas if nombre.encode() in partes[n] or b"Profesor Inventado" in partes[n]] == []
    assert not any(nombre in n for n in partes)


# Escenario 2, las rutas

@when(parsers.re(r'(?P<correo>[^ ]+@[^ ]+) pide GET /api/sesion, GET /api/cargas y GET /api/cargas/\{carga_id\}'))
def _pide_las_rutas(ctx: Escenario, correo: str) -> None:
    cliente = ctx.sesion(correo)
    ctx.extras["respuestas_010"] = [cliente.get("/api/sesion"), cliente.get("/api/cargas", params={"periodo": "2026-1"}),
                                    cliente.get(f"/api/cargas/{ctx.carga_id}")]


@then(parsers.re(r'ninguna respuesta trae "(?P<nombre>[^"]+)"'))
def _ninguna_respuesta_trae_el_nombre(ctx: Escenario, nombre: str) -> None:
    respuestas = ctx.extras["respuestas_010"]
    assert [r.status_code for r in respuestas] == [200, 200, 200], [r.status_code for r in respuestas]
    assert [r.request.url.path for r in respuestas if nombre in r.text or "Profesor Inventado" in r.text] == []
    # La lista de cargas trae la carga publicada, así que la prueba no pasa por una lista vacía.
    assert len(respuestas[1].json()) >= 1


@then(parsers.re(r'subida_por sigue siendo "(?P<correo>[^"]+)"'))
def _subida_por(ctx: Escenario, correo: str) -> None:
    constancia = ctx.extras["respuestas_010"][2].json()
    assert constancia["subida_por"] == correo


# Escenario 3, el registro

@given("el registro abet.api capturado en el nivel INFO")
def _registro_capturado(ctx: Escenario, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="abet.api")
    caplog.set_level(logging.INFO)
    ctx.extras["caplog_010"] = caplog


@when(parsers.re(r'(?P<correo>[^ ]+@[^ ]+) inicia sesión, sube el export de la 701, declara su análisis y genera el R-17'))
def _recorre_el_flujo(ctx: Escenario, correo: str) -> None:
    cliente = ctx.sesion(correo)
    assert cliente.get("/api/sesion").status_code == 200
    contenido, nombre = ctx.export_de_quimica("701")
    subida = A.subir(cliente, ctx.seccion_de("701", "5643"), contenido, nombre)
    assert subida.status_code == 201 and subida.json()["estado"] == "PUBLICADA", subida.status_code
    ctx.carga_id = int(subida.json()["carga_id"])
    # La declaración pasa por las rutas 15 y 16, que también escriben en el registro.
    base = f"/api/cargas/{ctx.carga_id}"
    tipos = {i["pi"]: i["tipo_registro"] for i in cliente.get(f"{base}/indicadores").json()["indicadores"]}
    indicadores = [{"pi": pi, "tipo": tipo, "causa": f"Causa de prueba del PI {pi}.", "accion": f"Acción de prueba del PI {pi}."}
                   for pi, tipo in tipos.items()]
    assert cliente.put(f"{base}/mejora/borrador", json={"version": 0, "indicadores": indicadores}).status_code == 200
    assert cliente.post(f"{base}/mejora/declaracion", json={"version": 1}).status_code == 201
    ctx.extras["quien_010"] = correo
    _conftest(ctx).generar_r17_010(ctx, correo)
    assert ctx.extras["libros_010"][-1].status_code == 200


@then(parsers.re(r'ninguna línea del registro abet\.api contiene "(?P<nombre>[^"]+)"'))
def _el_registro_sin_el_nombre(ctx: Escenario, nombre: str) -> None:
    caplog = ctx.extras["caplog_010"]
    assert ctx.uno("SELECT nombre FROM acceso.usuario_autorizado WHERE correo = %s", CORREO_701) == nombre
    # Un flujo sin fallas no escribe nada en el registro de la aplicación, así que la prueba daría verde con una captura
    # rota. El control positivo sube un archivo vacío a la misma sección, que la API detiene con un aviso en el registro,
    # y exige ver esa línea antes de buscar el nombre en todas.
    detenida = A.subir(ctx.sesion(CORREO_701), ctx.seccion_de("701", "5643"), b"", "vacio_701.xlsx")
    assert detenida.status_code == 422, detenida.status_code
    lineas = [r.getMessage() for r in caplog.records if r.name == "abet.api"]
    assert any("evento=archivo_detenido" in linea for linea in lineas), "la captura del registro abet.api no ve la API"
    texto = "\n".join(r.getMessage() for r in caplog.records)
    assert nombre not in texto and "Profesor Inventado" not in texto


# Escenarios 4 y 5, el repositorio

@when(parsers.re(r'la prueba de repositorio carga db/datos/periodo_2026_2_inventado\.sql, varias_secciones_2026_2_inventado\.sql '
                 r'y quimica_2026_1_inventado\.sql en una base desechable' + PROPUESTA))
def _carga_las_semillas(ctx: Escenario) -> None:
    semillas = _semillas()
    with ctx.plantillas.base_desechable.abierta(datos_2026_2=False) as base:
        ctx.extras["semillas_010"] = semillas.cargar_y_revisar(base, semillas.SEMILLAS)
        ctx.extras["coordinadores_010"] = semillas.nombres_de(base, solo_coordinadores=True)


@then("cada nombre no nulo de acceso.usuario_autorizado tiene la forma inventada")
def _nombres_con_la_forma_inventada(ctx: Escenario) -> None:
    problemas, nombres = ctx.extras["semillas_010"]
    assert nombres, "las semillas no dejaron ningún nombre"
    assert not [p for p in problemas if "nombre" in p], problemas
    assert all(_semillas().es_de_la_forma_inventada(n) for n in nombres.values())
    assert ctx.extras["coordinadores_010"] == []


@then("cada correo es del dominio example.invalid")
def _correos_de_example_invalid(ctx: Escenario) -> None:
    problemas, nombres = ctx.extras["semillas_010"]
    assert not [p for p in problemas if "correo" in p], problemas
    assert all(_semillas().es_de_example_invalid(c) for c in nombres)


@then("con una semilla que asigna un nombre fuera de la forma inventada la prueba falla nombrando el archivo y sin repetir el nombre")
def _una_semilla_con_otro_nombre_falla(ctx: Escenario) -> None:
    semillas = _semillas()
    tmp_path: Path = ctx.request.getfixturevalue("tmp_path")
    mala = tmp_path / "quimica_2026_1_inventado.sql"
    mala.write_text((RAIZ / "db" / "datos" / "quimica_2026_1_inventado.sql").read_text(encoding="utf-8")
                    .replace("Profesor Inventado Setecientos Dos", "Docente Sin Forma Inventada"), encoding="utf-8")
    with ctx.plantillas.base_desechable.abierta(datos_2026_2=False) as base:
        problemas, _ = semillas.cargar_y_revisar(base, [RAIZ / "db" / "datos" / "periodo_2026_2_inventado.sql", mala])
    assert problemas == ["quimica_2026_1_inventado.sql: 1 nombre fuera de la forma inventada"]
    assert not any("Docente" in p or "Sin Forma" in p or "docente702" in p for p in problemas)


@when(parsers.re(r'la prueba de repositorio lista los CSV rastreados con git ls-files' + PROPUESTA))
def _lista_los_csv(ctx: Escenario) -> None:
    ctx.extras["csv_010"] = _semillas().csv_con_columna_nombre(RAIZ)
    rastreados = subprocess.run(["git", "-C", str(RAIZ), "ls-files", "*.csv"], capture_output=True, text=True, check=True)
    assert rastreados.stdout.split(), "git no rastrea ningún CSV, así que la revisión no comprobaría nada"


@then("ningún CSV fuera de tests/datos_inventados trae la columna nombre en su encabezado")
def _ningun_csv_con_nombre(ctx: Escenario) -> None:
    assert ctx.extras["csv_010"] == []


@then("con un CSV con la columna nombre agregado al índice en una copia temporal la prueba falla nombrando el archivo")
def _un_csv_con_nombre_falla(ctx: Escenario) -> None:
    tmp_path: Path = ctx.request.getfixturevalue("tmp_path")
    copia = tmp_path / "copia"
    copia.mkdir()
    for orden in (["git", "init", "-q"], ["git", "config", "user.email", "prueba@example.invalid"],
                  ["git", "config", "user.name", "Prueba"]):
        subprocess.run(orden, cwd=copia, check=True, capture_output=True)
    (copia / "programacion_20262_inventada.csv").write_text(
        "periodo,asignatura,seccion,correo,curso_blackboard,nombre\n", encoding="utf-8")
    (copia / "tests" / "datos_inventados").mkdir(parents=True)
    (copia / "tests" / "datos_inventados" / "con_nombres.csv").write_text("correo,nombre\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=copia, check=True, capture_output=True)
    assert _semillas().csv_con_columna_nombre(copia) == ["programacion_20262_inventada.csv"]
