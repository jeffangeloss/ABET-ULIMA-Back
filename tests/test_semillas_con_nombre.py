"""Prueba de repositorio de los nombres de las semillas (US-99 y FR-013 de la spec 010, T022).

Las semillas db/datos/*_inventado.sql asignan a sus profesores los nombres inventados de las convenciones de
specs/010-nombre-del-profesor/spec.md, y git no rastrea ningún CSV con una columna nombre fuera de
tests/datos_inventados/. La lógica vive en tests/semillas_inventadas.py. Los mensajes de falla nombran el archivo y nunca
el valor de un nombre ni de un correo. Las bases son las del clúster desechable de tests/cluster_desechable.py.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest


RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "db" / "datos"
NOMBRES_DE_LAS_SEMILLAS = {
    "docente410@example.invalid": "Profesor Inventado Cuatrocientos Diez",
    "docente411@example.invalid": "Profesor Inventado Cuatrocientos Once",
    "docente.varias@example.invalid": "Profesor Inventado Varias",
    "docente701@example.invalid": "Profesor Inventado Setecientos Uno",
    "docente702@example.invalid": "Profesor Inventado Setecientos Dos",
    "docente703@example.invalid": "Profesor Inventado Setecientos Tres",
}


@pytest.fixture(scope="module")
def semillas() -> ModuleType:
    """tests/semillas_inventadas.py cargado por su ruta, porque tests/ no es un paquete."""
    especificacion = importlib.util.spec_from_file_location("semillas_inventadas", RAIZ / "tests" / "semillas_inventadas.py")
    assert especificacion is not None and especificacion.loader is not None
    modulo = importlib.util.module_from_spec(especificacion)
    sys.modules[especificacion.name] = modulo
    especificacion.loader.exec_module(modulo)
    return modulo


# La forma inventada, sin base

@pytest.mark.parametrize("nombre", [
    "Profesor Inventado Uno", "Profesor Inventado Ángel", "Profesor Inventado Cuatrocientos Diez",
    "Profesor Inventado Muñoz Núñez", "Profesor Inventado Varias",
])
def test_una_forma_inventada_con_palabras_de_letras_se_acepta(semillas: ModuleType, nombre: str) -> None:
    assert semillas.es_de_la_forma_inventada(nombre)


@pytest.mark.parametrize("nombre", [
    "Profesor Inventado", "Profesor Inventado 732", "Profesor Inventado uno", "Profesor Inventado Uno1",
    "Profesora Inventada Uno", "Ángel Muñoz", "profesor Inventado Uno", "Profesor Inventado  Uno",
    "Profesor Inventado Uno,", "Profesor Inventado D'Ángelo", "", " Profesor Inventado Uno",
])
def test_una_forma_que_no_es_la_inventada_se_rechaza(semillas: ModuleType, nombre: str) -> None:
    assert not semillas.es_de_la_forma_inventada(nombre)


@pytest.mark.parametrize("correo", ["docente410@example.invalid", "a.b@example.invalid"])
def test_un_correo_de_example_invalid_se_acepta(semillas: ModuleType, correo: str) -> None:
    assert semillas.es_de_example_invalid(correo)


@pytest.mark.parametrize("correo", ["docente410@example.com", "docente410@example.invalid.com", "x@EXAMPLE.invalid",
                                    "docente410", "@example.invalid"])
def test_un_correo_de_otro_dominio_se_rechaza(semillas: ModuleType, correo: str) -> None:
    assert not semillas.es_de_example_invalid(correo)


# Las semillas cargadas en una base desechable

def test_las_tres_semillas_dejan_solo_nombres_inventados_con_correos_de_example_invalid(
        semillas: ModuleType, base_desechable: ModuleType) -> None:
    with base_desechable.abierta(datos_2026_2=False) as base:
        problemas, nombres = semillas.cargar_y_revisar(base, semillas.SEMILLAS)
    assert problemas == []
    assert nombres == NOMBRES_DE_LAS_SEMILLAS


def test_una_semilla_con_un_nombre_fuera_de_la_forma_falla_nombrando_el_archivo_y_no_el_nombre(
        semillas: ModuleType, base_desechable: ModuleType, tmp_path: Path) -> None:
    malo = tmp_path / "periodo_2026_2_inventado.sql"
    malo.write_text((DATOS / "periodo_2026_2_inventado.sql").read_text(encoding="utf-8")
                    .replace("Profesor Inventado Cuatrocientos Diez", "Docente Sin Forma Inventada"), encoding="utf-8")
    with base_desechable.abierta(datos_2026_2=False) as base:
        problemas, _ = semillas.cargar_y_revisar(base, [malo])
    assert problemas == ["periodo_2026_2_inventado.sql: 1 nombre fuera de la forma inventada"]
    assert not any("Docente" in problema or "Sin Forma" in problema or "docente410" in problema for problema in problemas)


def test_una_semilla_con_un_correo_fuera_de_example_invalid_falla_nombrando_el_archivo(
        semillas: ModuleType, base_desechable: ModuleType, tmp_path: Path) -> None:
    malo = tmp_path / "periodo_2026_2_inventado.sql"
    texto = (DATOS / "periodo_2026_2_inventado.sql").read_text(encoding="utf-8")
    # El correo cambia en todo el archivo, así la semilla carga completa y pasa su comprobación final.
    malo.write_text(texto.replace("docente411@example.invalid", "docente411@ejemplo.com"), encoding="utf-8")
    assert malo.read_text(encoding="utf-8") != texto
    with base_desechable.abierta(datos_2026_2=False) as base:
        problemas, _ = semillas.cargar_y_revisar(base, [malo])
    assert problemas == ["periodo_2026_2_inventado.sql: 1 correo fuera de example.invalid"]
    assert not any("ejemplo.com" in problema for problema in problemas)


def test_cada_semilla_vuelve_a_correr_sin_cambiar_un_nombre_que_ya_existe(
        semillas: ModuleType, base_desechable: ModuleType) -> None:
    with base_desechable.abierta(datos_2026_2=False) as base:
        _, nombres = semillas.cargar_y_revisar(base, semillas.SEMILLAS)
        semillas.correr_sql(base, "UPDATE acceso.usuario_autorizado SET nombre = 'Profesor Inventado Anterior'"
                                  " WHERE correo = 'docente410@example.invalid'")
        # Una segunda corrida completa solo el nombre nulo y no pisa el de un usuario que ya lo tiene.
        for semilla in semillas.SEMILLAS:
            semillas.correr_semilla(base, semilla)
        despues = dict(semillas.nombres_de(base))
    assert despues["docente410@example.invalid"] == "Profesor Inventado Anterior"
    assert {correo: nombre for correo, nombre in despues.items() if correo != "docente410@example.invalid"} == {
        correo: nombre for correo, nombre in nombres.items() if correo != "docente410@example.invalid"}


def test_las_cuentas_coordinador_de_las_semillas_quedan_sin_nombre(
        semillas: ModuleType, base_desechable: ModuleType) -> None:
    with base_desechable.abierta(datos_2026_2=False) as base:
        semillas.cargar_y_revisar(base, semillas.SEMILLAS)
        filas = semillas.nombres_de(base, solo_coordinadores=True)
    assert filas == []


# Git no rastrea un CSV con la columna nombre fuera de los datos inventados

def _repo(carpeta: Path) -> Path:
    for orden in (["git", "init", "-q"], ["git", "config", "user.email", "prueba@example.invalid"],
                  ["git", "config", "user.name", "Prueba"]):
        subprocess.run(orden, cwd=carpeta, check=True, capture_output=True)
    return carpeta


def _agregar(carpeta: Path, ruta: str, contenido: str | bytes) -> None:
    destino = carpeta / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(contenido if isinstance(contenido, bytes) else contenido.encode("utf-8"))
    subprocess.run(["git", "add", ruta], cwd=carpeta, check=True, capture_output=True)


def test_el_repositorio_real_no_rastrea_ningun_csv_con_la_columna_nombre_fuera_de_los_datos_inventados(
        semillas: ModuleType) -> None:
    assert semillas.csv_con_columna_nombre(RAIZ) == []


def test_un_csv_con_la_columna_nombre_agregado_al_indice_falla_nombrando_el_archivo(
        semillas: ModuleType, tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _agregar(repo, "programacion_inventada.csv", "periodo,asignatura,seccion,correo,nombre\n2026-2,450002,410,a@example.invalid,x\n")
    assert semillas.csv_con_columna_nombre(repo) == ["programacion_inventada.csv"]


@pytest.mark.parametrize(("ruta", "contenido"), [
    ("tests/datos_inventados/programacion_con_nombres.csv", "periodo,correo,nombre\n"),
    ("docs/lista.csv", "periodo,asignatura,seccion,correo\n"),
    ("docs/nombres_de_columnas.csv", "periodo;nombre_de_la_seccion\n"),
    ("docs/vacio.csv", ""),
])
def test_un_csv_inventado_o_sin_la_columna_nombre_no_falla(semillas: ModuleType, tmp_path: Path, ruta: str,
                                                          contenido: str) -> None:
    repo = _repo(tmp_path)
    _agregar(repo, ruta, contenido)
    assert semillas.csv_con_columna_nombre(repo) == []


@pytest.mark.parametrize("encabezado", ["periodo,correo,NOMBRE", "periodo;correo;nombre", "periodo\tcorreo\tnombre",
                                        '"periodo","correo","nombre"', "﻿nombre,correo", "periodo, correo , nombre"])
def test_la_columna_nombre_se_reconoce_con_otro_separador_otra_forma_o_con_bom(
        semillas: ModuleType, tmp_path: Path, encabezado: str) -> None:
    repo = _repo(tmp_path)
    _agregar(repo, "otra/programacion.csv", encabezado + "\n")
    assert semillas.csv_con_columna_nombre(repo) == ["otra/programacion.csv"]


def test_un_csv_en_utf16_con_la_columna_nombre_se_reconoce(semillas: ModuleType, tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    _agregar(repo, "otra/programacion.csv", "periodo,correo,nombre\n".encode("utf-16"))
    assert semillas.csv_con_columna_nombre(repo) == ["otra/programacion.csv"]


def test_un_csv_sin_agregar_al_indice_no_se_revisa_porque_git_no_lo_rastrea(semillas: ModuleType, tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    (repo / "suelto.csv").write_text("periodo,correo,nombre\n", encoding="utf-8")
    assert semillas.csv_con_columna_nombre(repo) == []


def test_sin_un_repositorio_git_la_revision_falla_en_lugar_de_pasar_en_silencio(semillas: ModuleType, tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="git ls-files"):
        semillas.csv_con_columna_nombre(tmp_path)


