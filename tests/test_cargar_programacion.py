"""Pruebas del guion de la programación docente de la spec 006 (T021, T030, T032 a T034).

db/herramientas/cargar_programacion.py lee el CSV de la programación docente, revisa la forma de cada fila
antes de conectarse (FR-003) y entrega las filas a psql 18, que corre db/herramientas/cargar_programacion.sql
en una sola transacción (FR-004 a FR-006). Las pruebas sin base llaman a main() en el mismo proceso, con
PSQL apuntando a un programa que no existe y PGHOST a una carpeta vacía, así que un intento de conexión daría
el código 3 y nunca alcanza un servidor. Las pruebas con base corren el guion como proceso aparte con
python -I, como en el Windows de Jefferson, contra copias de una base desechable del clúster de
tests/cluster_desechable.py, nunca en localhost:5432. Los archivos se arman en tmp_path y solo traen correos
de @example.invalid.

Cada prueba nombra lo que debe pasar y lo que no debe pasar (AGENTS.md, regla 8). Los escenarios de los dos
.feature de la spec viven en tests/aceptacion/pasos/, y estas pruebas cubren los casos que esos escenarios no
recorren.
"""

from __future__ import annotations

import ast
import csv
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from app.sesion import normalizar_correo

RAIZ = Path(__file__).resolve().parent.parent
GUION = RAIZ / "db" / "herramientas" / "cargar_programacion.py"
SQL = RAIZ / "db" / "herramientas" / "cargar_programacion.sql"
ENCABEZADOS = ("periodo", "asignatura", "seccion", "correo", "curso_blackboard")
BASE = (
    ("2026-2", "450002", "410", "docente410@example.invalid", "SINTETICO_20262_450002_410"),
    ("2026-2", "450002", "411", "docente411@example.invalid", "SINTETICO_20262_450002_411"),
)
RECHAZADO = "Archivo rechazado. Nada se escribió."
USO = "Uso: python -I db/herramientas/cargar_programacion.py --periodo 2026-2 --archivo RUTA [--aplicar]"
CONTRASENA = "Los usuarios nuevos no tienen contraseña. Asígnela con asignar_claves.py o con el código por correo."


def _modulo(nombre: str, ruta: Path) -> ModuleType:
    """Módulo cargado por su ruta, porque tests/ y db/herramientas/ no son paquetes."""
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, ruta)
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


C = _modulo("cargas_de_prueba", RAIZ / "tests" / "cargas_de_prueba.py")


@pytest.fixture(scope="module")
def guion() -> ModuleType:
    return _modulo("cargar_programacion", GUION)


def _csv(filas: tuple[tuple[str, ...], ...] | list[tuple[str, ...]], encabezados: tuple[str, ...] = ENCABEZADOS,
         *, bom: bool = False, salto: str = "\r\n") -> bytes:
    salida = io.StringIO(newline="")
    escritor = csv.writer(salida, lineterminator=salto)
    escritor.writerow(encabezados)
    escritor.writerows(filas)
    return (b"\xef\xbb\xbf" if bom else b"") + salida.getvalue().encode("utf-8")


def _archivo(tmp_path: Path, datos: bytes, nombre: str = "programacion_20262_inventada.csv") -> Path:
    ruta = tmp_path / nombre
    ruta.write_bytes(datos)
    return ruta


@pytest.fixture
def sin_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Entorno sin servidor alcanzable. Un psql invocado no existe, así que el guion daría el código 3."""
    carpeta = tmp_path / "sin_servidor"
    carpeta.mkdir()
    for clave in [c for c in os.environ if c.startswith("PG")]:
        monkeypatch.delenv(clave)
    monkeypatch.setenv("PGHOST", str(carpeta))
    monkeypatch.setenv("PSQL", str(carpeta / "psql_que_no_existe"))
    return carpeta


def _main(guion: ModuleType, capsys: pytest.CaptureFixture[str], *argumentos: str) -> tuple[int, list[str]]:
    codigo = guion.main(list(argumentos))
    return codigo, capsys.readouterr().out.splitlines()


# Lectura y forma, sin base (T030)

@pytest.mark.parametrize("correo", [" Docente410@EXAMPLE.invalid ", "\tDOCENTE.VARIAS@Example.Invalid\n",
                                    "docente411@example.invalid", "ÁNGEL@EXAMPLE.INVALID"])
def test_el_correo_se_normaliza_como_en_app_sesion(guion: ModuleType, correo: str) -> None:
    assert guion.normalizar_correo(correo) == normalizar_correo(correo)


def test_el_guion_solo_usa_la_biblioteca_estandar() -> None:
    arbol = ast.parse(GUION.read_text(encoding="utf-8"))
    modulos = {alias.name.split(".")[0] for nodo in ast.walk(arbol) if isinstance(nodo, ast.Import)
               for alias in nodo.names}
    modulos |= {nodo.module.split(".")[0] for nodo in ast.walk(arbol)
                if isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0}
    assert modulos and modulos <= set(sys.stdlib_module_names), modulos - set(sys.stdlib_module_names)


def test_la_bom_no_cambia_lo_leido(guion: ModuleType) -> None:
    con_bom = guion.leer(_csv(BASE, bom=True))
    sin_bom = guion.leer(_csv(BASE, salto="\n"))
    assert con_bom == sin_bom
    assert [(f.fila, f.seccion, f.correo) for f in con_bom] == [
        (2, "410", "docente410@example.invalid"), (3, "411", "docente411@example.invalid")]


def test_las_columnas_ajenas_se_ignoran_sin_leer_sus_valores(guion: ModuleType) -> None:
    # Cambio del 2026-11-25 (spec 010, FR-007). La columna nombre ya se lee, así que la prueba nombra otras columnas de
    # persona que siguen ignoradas, aunque se parezcan a nombre, y comprueba que sus valores no llegan a ninguna fila.
    ajenas = ("nombre_profesor", "nombres", "apellido", "docente", "Nombre completo", "correo_personal")
    filas = [(*fila, *(f"Valor Inventado {columna}" for columna in ajenas)) for fila in BASE]
    leidas = guion.leer(_csv(filas, (*ENCABEZADOS, *ajenas)))
    assert all("Valor Inventado" not in repr(fila) for fila in leidas)
    assert len(leidas) == 2
    assert leidas.con_nombre is False and [fila.nombre for fila in leidas] == [None, None]


# La columna opcional nombre (spec 010, US-96, T030)

NOMBRES = ("Profesor Inventado Cuatrocientos Diez", "Profesor Inventado Cuatrocientos Once")
CON_NOMBRE = ("periodo", "asignatura", "seccion", "correo", "curso_blackboard", "nombre")


def _con_nombres(*nombres: str | None) -> bytes:
    return _csv([(*fila, nombre or "") for fila, nombre in zip(BASE, nombres, strict=True)], CON_NOMBRE)


def test_la_columna_nombre_se_lee_y_el_archivo_lo_dice(guion: ModuleType) -> None:
    leidas = guion.leer(_con_nombres(*NOMBRES))
    assert leidas.con_nombre is True
    assert [fila.nombre for fila in leidas] == list(NOMBRES)
    assert guion.revisar(leidas, "2026-2") == {}


def test_una_celda_de_nombre_vacia_significa_sin_nombre_aunque_la_columna_exista(guion: ModuleType) -> None:
    leidas = guion.leer(_con_nombres(None, "  "))
    assert leidas.con_nombre is True and [fila.nombre for fila in leidas] == [None, None]
    assert guion.revisar(leidas, "2026-2") == {}


def test_la_columna_nombre_se_reconoce_sin_importar_las_mayusculas_ni_el_lugar(guion: ModuleType) -> None:
    datos = _csv([("Profesor Inventado Uno", *fila) for fila in BASE], ("NOMBRE", *ENCABEZADOS))
    assert [fila.nombre for fila in guion.leer(datos)] == ["Profesor Inventado Uno"] * 2


@pytest.mark.parametrize(("celda", "esperado"), [
    ("  Profesor   Inventado Cuatrocientos Diez ", "Profesor Inventado Cuatrocientos Diez"),
    ("Profesor Inventado A\u0301ngel", "Profesor Inventado \u00c1ngel"),
    ("Profesor Inventado \u00c1ngel", "Profesor Inventado \u00c1ngel"),
    ("Profesor     Inventado    Muñoz", "Profesor Inventado Muñoz"),
])
def test_el_nombre_se_normaliza_a_nfc_sin_espacios_a_los_lados_ni_dobles(guion: ModuleType, celda: str, esperado: str) -> None:
    [primera, _] = guion.leer(_con_nombres(celda, None))
    assert primera.nombre == esperado


@pytest.mark.parametrize("nombre", [
    "docente411@example.invalid", "Profesor Inventado 411", "Profesor Inventado, Cuatrocientos", "Inventado, Profesor",
    "Profesor Inventado\nCuatrocientos Once", "Profesor Inventado\tUno", "Profesor Inventado\u200bUno",
    "Profesor Inventado\ufeffUno", "Profesor Inventado\u00adUno", "Profesor Inventado\u2060Uno",
    "Profesor Inventado\x07Uno", "Profesor Inventado\x85Uno", "Profesor Inventado\r", "\nProfesor Inventado",
    "Profesor Inventado " + "a" * 102, "Profesor Inventado\u2028Uno", "Profesor Inventado\u2029Uno",
    "Profesor Inventado\u2066Uno", "Profesor Inventado\U000e0041Uno",
], ids=["arroba", "digito", "coma", "coma_inicial", "salto", "tab", "u200b", "ufeff", "u00ad", "u2060", "bel", "c1", "cr",
        "salto_al_comienzo", "121_caracteres", "u2028", "u2029", "u2066", "etiqueta"])
def test_un_nombre_invalido_rechaza_la_fila_sin_repetir_su_valor(guion: ModuleType, nombre: str) -> None:
    assert len("Profesor Inventado " + "a" * 102) == 121
    errores = guion.revisar(guion.leer(_con_nombres(NOMBRES[0], nombre)), "2026-2")
    assert errores == {3: "Fila 3. El nombre no es válido."}


def test_un_nombre_de_exactamente_120_caracteres_es_valido(guion: ModuleType) -> None:
    nombre = "Profesor Inventado " + "a" * 101
    assert len(nombre) == 120
    assert guion.revisar(guion.leer(_con_nombres(nombre, None)), "2026-2") == {}


@pytest.mark.parametrize("nombre", ["Profesor Inventado D'Ángelo-Núñez", "PROFESOR INVENTADO UNO", "Profesor Inventado Ñandú Güemes"])
def test_el_apostrofo_el_guion_las_enes_y_las_mayusculas_son_validos_y_no_se_cambian(guion: ModuleType, nombre: str) -> None:
    [primera, _] = guion.leer(_con_nombres(nombre, None))
    assert primera.nombre == nombre
    assert guion.revisar([primera], "2026-2") == {}


def test_dos_nombres_distintos_para_un_mismo_correo_rechazan_la_segunda_fila(guion: ModuleType) -> None:
    filas = [(*BASE[0], NOMBRES[0]), ("2026-2", "450010", "410", BASE[0][3], "", "Profesor Inventado Otro")]
    errores = guion.revisar(guion.leer(_csv(filas, CON_NOMBRE)), "2026-2")
    assert errores == {3: "Fila 3. El correo trae otro nombre en otra fila."}


def test_el_mismo_nombre_o_un_nombre_vacio_en_otra_fila_del_mismo_correo_no_choca(guion: ModuleType) -> None:
    mismo = [(*BASE[0], NOMBRES[0]), ("2026-2", "450010", "410", BASE[0][3], "", NOMBRES[0])]
    vacio = [(*BASE[0], NOMBRES[0]), ("2026-2", "450010", "410", BASE[0][3], "", "")]
    vacio_antes = [(*BASE[0], ""), ("2026-2", "450010", "410", BASE[0][3], "", NOMBRES[0])]
    for filas in (mismo, vacio, vacio_antes):
        assert guion.revisar(guion.leer(_csv(filas, CON_NOMBRE)), "2026-2") == {}


def test_una_fila_con_otra_falla_no_cuenta_para_el_choque_de_nombres(guion: ModuleType) -> None:
    # La fila 2 trae un periodo que no es el de la corrida, así que su nombre no se toma como el primero del correo.
    filas = [("2026-1", "450002", "410", BASE[0][3], "", NOMBRES[0]), ("2026-2", "450002", "411", BASE[0][3], "", NOMBRES[1])]
    errores = guion.revisar(guion.leer(_csv(filas, CON_NOMBRE)), "2026-2")
    assert list(errores) == [2]


def test_un_archivo_con_un_nombre_invalido_se_rechaza_sin_conectarse_aunque_la_base_tambien_lo_rechazaria(
    guion: ModuleType, sin_base: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    filas = [(*BASE[0], "Profesor Inventado 410"), ("2026-2", "999999", "411", BASE[1][3], "", NOMBRES[1])]
    ruta = _archivo(tmp_path, _csv(filas, CON_NOMBRE))
    codigo, informe = _main(guion, capsys, "--periodo", "2026-2", "--archivo", str(ruta), "--aplicar")
    # Con un psql invocado, que no existe, el código sería 3 y no 1. La asignatura 999999 solo la rechazaría la base.
    assert codigo == 1
    assert informe == ["Fila 2. El nombre no es válido.", RECHAZADO]
    assert "Profesor Inventado" not in capsys.readouterr().err


def test_dos_nombres_distintos_se_rechazan_sin_conectarse(guion: ModuleType, sin_base: Path, tmp_path: Path,
                                                         capsys: pytest.CaptureFixture[str]) -> None:
    filas = [(*BASE[0], NOMBRES[0]), ("2026-2", "450010", "410", BASE[0][3], "", "Profesor Inventado Otro")]
    ruta = _archivo(tmp_path, _csv(filas, CON_NOMBRE))
    codigo, informe = _main(guion, capsys, "--periodo", "2026-2", "--archivo", str(ruta))
    assert codigo == 1 and informe == ["Fila 3. El correo trae otro nombre en otra fila.", RECHAZADO]
    assert all("Profesor Inventado" not in linea for linea in informe)


def test_sin_la_columna_del_curso_cada_fila_queda_sin_curso(guion: ModuleType) -> None:
    leidas = guion.leer(_csv([fila[:4] for fila in BASE], ENCABEZADOS[:4]))
    assert [fila.curso_blackboard for fila in leidas] == [None, None]


def test_las_lineas_vacias_se_saltan_y_las_filas_siguen_su_numero(guion: ModuleType) -> None:
    datos = _csv(BASE).replace(b"\r\n2026-2,450002,411", b"\r\n\r\n2026-2,450002,411")
    assert [fila.fila for fila in guion.leer(datos)] == [2, 4]


@pytest.mark.parametrize(("datos", "mensajes"), [
    ("periodo,asignatura,seccion,correo\r\n2026-2,450002,41é,x@example.invalid\r\n".encode("cp1252"),
     ["El archivo no está en UTF-8."]),
    (_csv([fila[1:] for fila in BASE], ENCABEZADOS[1:]), ["Falta la columna periodo."]),
    (_csv([(f[0], f[3]) for f in BASE], ("periodo", "correo")), ["Falta la columna asignatura.",
                                                                  "Falta la columna seccion."]),
    (_csv([]), ["El archivo no trae filas."]),
    (b"", ["Falta la columna periodo.", "Falta la columna asignatura.", "Falta la columna seccion.",
           "Falta la columna correo."]),
    (_csv([("", "", "", "", "")]), ["El archivo no trae filas."]),
], ids=["no_utf8", "sin_periodo", "sin_dos_columnas", "sin_filas", "vacio", "solo_una_fila_vacia"])
def test_un_archivo_que_no_se_puede_leer_se_rechaza_sin_conectarse(
    guion: ModuleType, sin_base: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], datos: bytes,
    mensajes: list[str],
) -> None:
    ruta = _archivo(tmp_path, datos)
    codigo, informe = _main(guion, capsys, "--periodo", "2026-2", "--archivo", str(ruta), "--aplicar")
    # Con un psql invocado, que no existe, el código sería 3 y no 1.
    assert codigo == 1
    assert informe == [*mensajes, RECHAZADO]


CASOS_DE_FORMA = [
    (("2026-1", "450002", "411", "docente411@example.invalid", ""), "Fila 3. El periodo 2026-1 no es el de la corrida, 2026-2."),
    (("2026-2/", "450002", "411", "docente411@example.invalid", ""), "Fila 3. El periodo 2026-2/ no es el de la corrida, 2026-2."),
    (("", "450002", "411", "docente411@example.invalid", ""), "Fila 3. Falta el periodo."),
    (("2026-2", "45000", "411", "docente411@example.invalid", ""), "Fila 3. El código de asignatura 45000 no es válido."),
    (("2026-2", "", "411", "docente411@example.invalid", ""), "Fila 3. Falta la asignatura."),
    (("2026-2", "450002", "0411", "docente411@example.invalid", ""), "Fila 3. El número de sección 0411 no es válido."),
    (("2026-2", "450002", "411a", "docente411@example.invalid", ""), "Fila 3. El número de sección 411a no es válido."),
    (("2026-2", "450002", " ", "docente411@example.invalid", ""), "Fila 3. Falta la sección."),
    (("2026-2", "450002", "411", "docente411example.invalid", ""), "Fila 3. El correo docente411example.invalid no es válido."),
    (("2026-2", "450002", "411", "docente@411@example.invalid", ""), "Fila 3. El correo docente@411@example.invalid no es válido."),
    (("2026-2", "450002", "411", "  ", ""), "Fila 3. Falta el correo."),
    (("2026-2", "450002", "411", "docente411@example.invalid", "x" * 101), "Fila 3. El curso de Blackboard tiene más de 100 caracteres."),
    (("2026-2", "450002", "411", "docente411@example.invalid", "SINTETICO_20262_450002_410"),
     "Fila 3. El curso de Blackboard SINTETICO_20262_450002_410 ya es de la sección 410 de 450002."),
]


@pytest.mark.parametrize(("fila", "mensaje"), CASOS_DE_FORMA, ids=[m.split(". ", 1)[1][:40] for _, m in CASOS_DE_FORMA])
def test_cada_falla_de_forma_da_su_mensaje(guion: ModuleType, fila: tuple[str, ...], mensaje: str) -> None:
    errores = guion.revisar(guion.leer(_csv([BASE[0], fila])), "2026-2")
    assert errores == {3: mensaje}


# Caracteres que no se ven al copiar una celda desde Outlook, una web o Excel (Alt+Enter), de las categorías
# Unicode Cf y Cc. El patrón de ck_usuario_autorizado_correo los deja pasar, y la celda no coincidiría con lo que
# escribe el profesor al entrar ni con el curso de un export de Blackboard.
INVISIBLES = ["\u200b", "\ufeff", "\u2060", "\u00ad", "\x07", "\n", "\r"]


@pytest.mark.parametrize("caracter", INVISIBLES, ids=lambda c: f"U+{ord(c):04X}")
def test_un_correo_con_un_caracter_invisible_no_es_valido(guion: ModuleType, caracter: str) -> None:
    # Al final de la celda, strip() ya quita el salto de línea y el retorno de carro, que sí se ven como espacio.
    correos = [f"docente{caracter}411@example.invalid"]
    if not caracter.isspace():
        correos.append(f"docente411@example.invalid{caracter}")
    for correo in correos:
        errores = guion.revisar(guion.leer(_csv([BASE[0], (*BASE[1][:3], correo, "")])), "2026-2")
        # El motivo no repite la celda, que partiría la línea del informe o mostraría un correo que parece válido.
        assert errores == {3: "Fila 3. El correo trae un carácter invisible o de control."}, repr(correo)


@pytest.mark.parametrize("caracter", INVISIBLES, ids=lambda c: f"U+{ord(c):04X}")
def test_un_curso_con_un_caracter_invisible_no_es_valido(guion: ModuleType, caracter: str) -> None:
    cursos = [f"CURSO{caracter}CON SALTO"]
    if not caracter.isspace():
        cursos.append(f"SINTETICO_20262_450002_411{caracter}")
    for curso in cursos:
        errores = guion.revisar(guion.leer(_csv([BASE[0], (*BASE[1][:4], curso)])), "2026-2")
        assert errores == {3: "Fila 3. El curso de Blackboard trae un carácter invisible o de control."}, repr(curso)


def test_un_correo_y_un_curso_con_letras_acentuadas_siguen_siendo_validos(guion: ModuleType) -> None:
    filas = [("2026-2", "450002", "410", "ÁNGEL.MUÑOZ@example.invalid", "SINTÉTICO_20262_450002_410")]
    assert guion.revisar(guion.leer(_csv(filas)), "2026-2") == {}


def test_un_correo_de_mas_de_254_caracteres_no_es_valido(guion: ModuleType) -> None:
    correo = "d" * 250 + "@example.invalid"
    errores = guion.revisar(guion.leer(_csv([(*BASE[0][:3], correo, "")])), "2026-2")
    assert errores == {2: f"Fila 2. El correo {correo} no es válido."}


def test_una_seccion_con_dos_cursos_distintos_rechaza_la_segunda_fila(guion: ModuleType) -> None:
    filas = [BASE[1], ("2026-2", "450002", "411", "docente.varias@example.invalid", "SINTETICO_OTRO_411")]
    errores = guion.revisar(guion.leer(_csv(filas)), "2026-2")
    assert errores == {3: "Fila 3. La sección 411 de 450002 trae otro curso de Blackboard en la fila 2."}


def test_en_codocencia_un_curso_vacio_no_cuenta_como_otro_curso(guion: ModuleType) -> None:
    filas = [BASE[1], ("2026-2", "450002", "411", "docente.varias@example.invalid", ""), BASE[1]]
    assert guion.revisar(guion.leer(_csv(filas)), "2026-2") == {}


def test_una_fila_con_un_motivo_y_todas_las_filas_en_orden(guion: ModuleType) -> None:
    filas = [("2026-1", "45", "0410", "sin_arroba", ""), BASE[1], ("2026-2", "4500", "0411", "", "")]
    errores = guion.revisar(guion.leer(_csv(filas)), "2026-2")
    assert list(errores) == [2, 4]
    assert errores[2] == "Fila 2. El periodo 2026-1 no es el de la corrida, 2026-2."
    assert errores[4] == "Fila 4. El número de sección 0411 no es válido."


def test_el_correo_y_las_celdas_se_leen_sin_espacios(guion: ModuleType) -> None:
    filas = [(" 2026-2 ", " 450002", "410 ", " Docente410@EXAMPLE.invalid ", " SINTETICO_20262_450002_410 ")]
    [leida] = guion.leer(_csv(filas))
    assert (leida.periodo, leida.asignatura, leida.seccion, leida.correo, leida.curso_blackboard) == BASE[0]
    assert guion.revisar([leida], "2026-2") == {}


# Argumentos y archivo dentro de un repositorio (T030, FR-008 y FR-009)

@pytest.mark.parametrize(("argumentos", "mensaje"), [
    (("--archivo", "{archivo}"), "Falta el periodo, por ejemplo --periodo 2026-2."),
    (("--periodo", "2026-13", "--archivo", "{archivo}"), "El periodo no tiene la forma AAAA-C."),
    (("--periodo", "26-2", "--archivo", "{archivo}"), "El periodo no tiene la forma AAAA-C."),
    (("--periodo", "2026-2"), "Falta el archivo, por ejemplo --archivo RUTA."),
    (("--periodo", "2026-2", "--archivo", "{tmp}/no_existe.csv"), "No se encuentra el archivo de la programación."),
    (("--periodo", "2026-2", "--archivo", "{tmp}"), "No se encuentra el archivo de la programación."),
], ids=["sin_periodo", "periodo_2026_13", "periodo_corto", "sin_archivo", "no_existe", "es_carpeta"])
def test_un_argumento_invalido_da_el_codigo_2_sin_conectarse(
    guion: ModuleType, sin_base: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    argumentos: tuple[str, ...], mensaje: str,
) -> None:
    archivo = _archivo(tmp_path, _csv(BASE))
    valores = [a.format(archivo=archivo, tmp=tmp_path) for a in argumentos]
    codigo, informe = _main(guion, capsys, *valores)
    assert (codigo, informe) == (2, [mensaje])


def test_un_argumento_desconocido_da_el_codigo_2(guion: ModuleType, sin_base: Path, tmp_path: Path,
                                                capsys: pytest.CaptureFixture[str]) -> None:
    archivo = _archivo(tmp_path, _csv(BASE))
    codigo, informe = _main(guion, capsys, "--periodo", "2026-2", "--archivo", str(archivo), "--borrar")
    assert codigo == 2
    assert informe == ["Uso: python -I db/herramientas/cargar_programacion.py --periodo 2026-2 --archivo RUTA [--aplicar]"]


@pytest.mark.parametrize("abreviatura", ["--ap", "--apl", "--aplica", "--per"])
def test_una_opcion_abreviada_da_el_codigo_2(guion: ModuleType, sin_base: Path, tmp_path: Path,
                                             capsys: pytest.CaptureFixture[str], abreviatura: str) -> None:
    # --aplicar es la única llave entre la corrida en seco y la escritura, así que no se abre con un prefijo.
    archivo = _archivo(tmp_path, _csv(BASE))
    argumentos = ["--periodo", "2026-2", "--archivo", str(archivo), abreviatura]
    if abreviatura == "--per":
        argumentos = ["--per", "2026-2", "--archivo", str(archivo)]
    codigo, informe = _main(guion, capsys, *argumentos)
    assert (codigo, informe) == (2, [USO])


def test_un_archivo_que_no_se_puede_abrir_se_rechaza_sin_conectarse(
    guion: ModuleType, sin_base: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Como en el Windows cuando Excel tiene abierto el CSV, el archivo existe pero leerlo lanza PermissionError.
    archivo = _archivo(tmp_path, _csv(BASE))

    def sin_permiso(self: Path) -> bytes:
        raise PermissionError(13, "Permission denied", str(self))

    monkeypatch.setattr(Path, "read_bytes", sin_permiso)
    codigo, informe = _main(guion, capsys, "--periodo", "2026-2", "--archivo", str(archivo), "--aplicar")
    # Con un psql invocado, que no existe, el código sería 3 y no 1.
    assert (codigo, informe) == (1, ["El archivo no se puede abrir.", RECHAZADO])


@pytest.mark.parametrize("como", ["archivo", "carpeta"])
def test_un_archivo_dentro_de_un_repositorio_no_se_lee(
    guion: ModuleType, sin_base: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str], como: str,
) -> None:
    # En un worktree, .git es un archivo que apunta al repositorio principal, y en un clon es una carpeta.
    repo = tmp_path / "repo_falso"
    (repo / "datos" / "ciclo").mkdir(parents=True)
    if como == "archivo":
        (repo / ".git").write_text("gitdir: /ruta/inventada/.git/worktrees/repo_falso\n", encoding="utf-8")
    else:
        (repo / ".git").mkdir()
    archivo = _archivo(repo / "datos" / "ciclo", _csv(BASE))
    codigo, informe = _main(guion, capsys, "--periodo", "2026-2", "--archivo", str(archivo))
    assert (codigo, informe) == (2, ["El archivo de la programación debe estar fuera del repositorio."])
    assert guion.dentro_de_un_repositorio(archivo)
    assert not guion.dentro_de_un_repositorio(_archivo(tmp_path, _csv(BASE)))


def test_el_guion_corre_con_python_aislado(sin_base: Path, tmp_path: Path) -> None:
    # Con -I no entra la carpeta del guion en sys.path ni se leen PYTHONUTF8 ni PYTHONIOENCODING, como en el
    # Windows de Jefferson, y el guion escribe su informe en UTF-8 aunque la consola use otra codificación.
    corrida = subprocess.run([sys.executable, "-I", str(GUION), "--periodo", "2026-2", "--archivo",
                              str(tmp_path / "no_existe.csv")], capture_output=True, check=False)
    assert corrida.returncode == 2
    assert corrida.stdout.decode("utf-8").splitlines() == ["No se encuentra el archivo de la programación."]


def test_sin_psql_el_guion_da_el_codigo_3(guion: ModuleType, sin_base: Path, tmp_path: Path,
                                          capsys: pytest.CaptureFixture[str]) -> None:
    archivo = _archivo(tmp_path, _csv(BASE))
    codigo, informe = _main(guion, capsys, "--periodo", "2026-2", "--archivo", str(archivo))
    assert (codigo, informe) == (3, ["No se encuentra psql."])


def test_un_psql_de_otra_version_da_el_codigo_3(guion: ModuleType, sin_base: Path, tmp_path: Path,
                                                capsys: pytest.CaptureFixture[str],
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    falso = tmp_path / "psql_17"
    falso.write_text("#!/bin/sh\necho 'psql (PostgreSQL) 17.6'\n", encoding="utf-8")
    falso.chmod(0o755)
    monkeypatch.setenv("PSQL", str(falso))
    archivo = _archivo(tmp_path, _csv(BASE))
    codigo, informe = _main(guion, capsys, "--periodo", "2026-2", "--archivo", str(archivo))
    assert (codigo, informe) == (3, ["psql no es de PostgreSQL 18."])


@pytest.mark.parametrize(("opciones", "mensaje"), [
    ((), "La base no responde y no se guardó nada."),
    (("--aplicar",), "La base no responde y no se sabe si guardó los cambios. Una corrida en seco lo muestra."),
], ids=["en_seco", "aplicar"])
def test_psql_corre_sin_pedir_contrasena(guion: ModuleType, sin_base: Path, tmp_path: Path,
                                         capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch,
                                         opciones: tuple[str, ...], mensaje: str) -> None:
    # Sin -w, un PGPASSWORD ausente haría que psql pida la contraseña y, sin terminal, la tome de la primera
    # línea del CSV que le llega por la entrada estándar. Este psql falso anota sus argumentos y termina con 2,
    # como un psql que no alcanza la base o pierde la conexión. Con --aplicar, el corte pudo llegar después
    # del COMMIT, así que el informe no afirma que nada se guardó.
    anotados = tmp_path / "argumentos.txt"
    falso = tmp_path / "psql_18"
    falso.write_text("#!/bin/sh\nif [ \"$1\" = --version ]; then echo 'psql (PostgreSQL) 18.1'; exit 0; fi\n"
                     f"printf '%s\\n' \"$@\" > '{anotados}'\ncat > /dev/null\nexit 2\n", encoding="utf-8")
    falso.chmod(0o755)
    monkeypatch.setenv("PSQL", str(falso))
    archivo = _archivo(tmp_path, _csv(BASE))
    codigo, informe = _main(guion, capsys, "--periodo", "2026-2", "--archivo", str(archivo), *opciones)
    assert (codigo, informe) == (3, [mensaje])
    argumentos = anotados.read_text(encoding="utf-8").splitlines()
    assert "-w" in argumentos and "-X" in argumentos
    assert ("aplicar=1" if opciones else "aplicar=0") in argumentos


# Bases de partida de la spec 006 (T021) y corridas contra la base (T031 a T034)

@pytest.fixture(scope="module")
def plantilla_006(base_desechable: ModuleType) -> Iterator[Any]:
    """Base con las migraciones, el rol de la aplicación y la base de partida de la spec 006, que cada prueba copia."""
    with base_desechable.abierta(datos_2026_2=False) as base:
        with psycopg.connect(base.conexion, autocommit=True) as conexion:
            C.base_de_partida_006(conexion)
        yield base


@pytest.fixture
def copia(base_desechable: ModuleType, plantilla_006: Any) -> Iterator[Any]:
    nombre = f"{plantilla_006.nombre}_{os.urandom(3).hex()}"
    with psycopg.connect(make_conninfo(plantilla_006.conexion, dbname="postgres"), autocommit=True) as servidor:
        servidor.execute(sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(sql.Identifier(nombre),
                                                                          sql.Identifier(plantilla_006.nombre)))
    base = base_desechable.BaseDesechable(nombre, make_conninfo(plantilla_006.conexion, dbname=nombre), None, None)
    try:
        yield replace(base, rol_app=plantilla_006.rol_app)
    finally:
        base_desechable.borrar(base)


@pytest.fixture
def dueno(copia: Any) -> Iterator[psycopg.Connection]:
    with psycopg.connect(copia.conexion, autocommit=True) as conexion:
        yield conexion


def _correr(copia: Any, tmp_path: Path, filas: Any, *opciones: str, encabezados: tuple[str, ...] = ENCABEZADOS,
            periodo: str = "2026-2") -> subprocess.CompletedProcess[str]:
    archivo = _archivo(tmp_path, _csv(filas, encabezados))
    return C.correr_programacion(C.entorno_de_programacion(copia.nombre), "--periodo", periodo,
                                 "--archivo", str(archivo), *opciones)


def _tres_tablas(conexion: psycopg.Connection) -> dict[str, list[tuple[Any, ...]]]:
    return {
        "seccion": conexion.execute("SELECT * FROM abet.seccion ORDER BY seccion_id").fetchall(),
        "usuario_autorizado": conexion.execute("SELECT * FROM acceso.usuario_autorizado ORDER BY usuario_id").fetchall(),
        "docente_seccion": conexion.execute("SELECT * FROM acceso.docente_seccion ORDER BY docente_seccion_id").fetchall(),
    }


def _seccion(conexion: psycopg.Connection, asignatura: str, numero: str, curso: str | None = None) -> None:
    conexion.execute(
        "INSERT INTO abet.seccion (periodo_id, asignatura_id, numero, curso_blackboard) "
        "SELECT pe.periodo_id, a.asignatura_id, %s, %s FROM abet.periodo pe, abet.asignatura a "
        "WHERE pe.codigo = '2026-2' AND a.codigo = %s", (numero, curso, asignatura))


def test_la_base_de_partida_trae_la_vigencia_los_dos_planes_y_el_coordinador(dueno: psycopg.Connection) -> None:
    planes = dueno.execute(
        "SELECT a.codigo, string_agg(p.codigo, ',' ORDER BY p.codigo) FROM abet.plan_medicion pm "
        "JOIN abet.asignatura a USING (asignatura_id) JOIN abet.pi p USING (pi_id) "
        "JOIN abet.periodo pe ON pe.periodo_id = pm.periodo_id WHERE pe.codigo = '2026-2' GROUP BY a.codigo "
        "ORDER BY a.codigo").fetchall()
    assert planes == [("450002", "5.1,5.2,5.3"), ("450010", "2.1,2.2,5.1")]
    assert dueno.execute("SELECT cv.codigo FROM abet.catalogo_vigencia v JOIN abet.catalogo_version cv "
                         "USING (catalogo_version_id) JOIN abet.periodo pe ON pe.periodo_id = v.periodo_id "
                         "WHERE pe.codigo = '2026-2'").fetchall() == [("AMB-2026",)]
    assert dueno.execute("SELECT correo, rol, activo FROM acceso.usuario_autorizado").fetchall() == [
        ("coordinacion@example.invalid", "COORDINADOR", True)]
    assert dueno.execute("SELECT count(*) FROM abet.seccion").fetchone()[0] == 0
    assert dueno.execute("SELECT count(*) FROM acceso.docente_seccion").fetchone()[0] == 0
    # El ayudante se puede repetir sin filas nuevas.
    antes = _tres_tablas(dueno)
    C.base_de_partida_006(dueno)
    assert _tres_tablas(dueno) == antes
    assert dueno.execute("SELECT count(*) FROM abet.plan_medicion").fetchone()[0] == 6


def test_una_fila_repetida_cuenta_una_sola_vez(copia: Any, dueno: psycopg.Connection, tmp_path: Path) -> None:
    corrida = _correr(copia, tmp_path, [*BASE, BASE[1]], "--aplicar")
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert "Resumen. 2 secciones nuevas, 2 usuarios nuevos y 2 asignaciones nuevas." in corrida.stdout.splitlines()
    assert dueno.execute("SELECT count(*) FROM acceso.docente_seccion").fetchone()[0] == 2


def test_el_resumen_usa_el_singular_con_una_fila(copia: Any, tmp_path: Path) -> None:
    corrida = _correr(copia, tmp_path, [BASE[0]])
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert corrida.stdout.splitlines()[0] == "Resumen. 1 sección nueva, 1 usuario nuevo y 1 asignación nueva."


def test_una_seccion_sin_curso_lo_recibe_y_la_corrida_no_dice_sin_cambios(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    primera = _correr(copia, tmp_path, [fila[:4] for fila in BASE], "--aplicar", encabezados=ENCABEZADOS[:4])
    assert primera.returncode == 0, primera.stdout + primera.stderr
    assert dueno.execute("SELECT count(*) FROM abet.seccion WHERE curso_blackboard IS NOT NULL").fetchone()[0] == 0
    seco = _correr(copia, tmp_path, BASE)
    assert seco.stdout.splitlines()[-1] == "Corrida en seco. Nada se escribió."
    assert dueno.execute("SELECT count(*) FROM abet.seccion WHERE curso_blackboard IS NOT NULL").fetchone()[0] == 0
    segunda = _correr(copia, tmp_path, BASE, "--aplicar")
    informe = segunda.stdout.splitlines()
    assert informe[0] == "Resumen. 0 secciones nuevas, 0 usuarios nuevos y 0 asignaciones nuevas."
    # El UPDATE del curso nulo escribe en la base, así que el cierre no es «Sin cambios.» (duda de FR-007 en la
    # Clarification «Session 2026-11-22» de spec.md).
    assert informe[-1] == "Cambios guardados."
    assert dueno.execute("SELECT numero, curso_blackboard FROM abet.seccion ORDER BY numero").fetchall() == [
        ("410", "SINTETICO_20262_450002_410"), ("411", "SINTETICO_20262_450002_411")]
    # Sin la columna del curso, el curso que ya tiene la sección queda como está.
    tercera = _correr(copia, tmp_path, [fila[:4] for fila in BASE], "--aplicar", encabezados=ENCABEZADOS[:4])
    assert tercera.stdout.splitlines()[-1] == "Sin cambios."
    assert dueno.execute("SELECT count(*) FROM abet.seccion WHERE curso_blackboard IS NOT NULL").fetchone()[0] == 2


def test_una_seccion_con_otro_curso_en_la_base_rechaza_la_fila(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    _seccion(dueno, "450002", "410", "SINTETICO_ANTERIOR_410")
    antes = _tres_tablas(dueno)
    corrida = _correr(copia, tmp_path, BASE, "--aplicar")
    assert corrida.returncode == 1
    assert corrida.stdout.splitlines() == [
        "Fila 2. La sección 410 de 450002 ya tiene otro curso de Blackboard en la base.", RECHAZADO]
    assert _tres_tablas(dueno) == antes


def test_un_curso_de_otra_seccion_en_la_base_rechaza_la_fila(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    # uq_seccion_curso_bb es global, así que el curso de una sección de otro periodo también choca.
    dueno.execute(
        "INSERT INTO abet.seccion (periodo_id, asignatura_id, numero, curso_blackboard) "
        "SELECT pe.periodo_id, a.asignatura_id, '420', 'SINTETICO_20262_450002_411' FROM abet.periodo pe, "
        "abet.asignatura a WHERE pe.codigo = '2026-1' AND a.codigo = '450002'")
    antes = _tres_tablas(dueno)
    corrida = _correr(copia, tmp_path, BASE, "--aplicar")
    assert corrida.returncode == 1
    assert corrida.stdout.splitlines() == [
        "Fila 3. El curso de Blackboard SINTETICO_20262_450002_411 ya es de la sección 420 de 450002.", RECHAZADO]
    assert _tres_tablas(dueno) == antes


@pytest.mark.parametrize("con_curso_en_la_base", [False, True], ids=["base_vacia", "curso_en_2026_2"])
def test_un_periodo_que_no_existe_rechaza_el_archivo(copia: Any, dueno: psycopg.Connection, tmp_path: Path,
                                                    con_curso_en_la_base: bool) -> None:
    # Sin periodo no hay sección que comparar, así que el curso de la 410 de 2026-2 no se informa como de otra
    # sección, un motivo que parecería contradecir la propia fila.
    if con_curso_en_la_base:
        _seccion(dueno, "450002", "410", BASE[0][4])
    antes = _tres_tablas(dueno)
    filas = [("2030-1", *fila[1:]) for fila in BASE]
    corrida = _correr(copia, tmp_path, filas, "--aplicar", periodo="2030-1")
    assert corrida.returncode == 1
    assert corrida.stdout.splitlines() == ["El periodo 2030-1 no existe en la base.", RECHAZADO]
    assert _tres_tablas(dueno) == antes


def test_los_errores_de_forma_y_de_la_base_salen_juntos_por_fila(copia: Any, tmp_path: Path) -> None:
    filas = [("2026-2", "450002", "0410", "docente410@example.invalid", ""), ("2026-2", "999999", "411",
             "docente411@example.invalid", ""), ("2026-2", "450002", "412", "sin_arroba", "")]
    corrida = _correr(copia, tmp_path, filas)
    assert corrida.returncode == 1
    assert corrida.stdout.splitlines() == [
        "Fila 2. El número de sección 0410 no es válido.",
        "Fila 3. La asignatura 999999 no existe en el catálogo.",
        "Fila 4. El correo sin_arroba no es válido.",
        RECHAZADO,
    ]


def test_avisa_la_seccion_de_la_base_que_el_archivo_no_trae(copia: Any, dueno: psycopg.Connection,
                                                           tmp_path: Path) -> None:
    _seccion(dueno, "450002", "413")
    _seccion(dueno, "450010", "412")
    dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES ('docente.varias@example.invalid', "
                  "'PROFESOR')")
    dueno.execute("INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) SELECT u.usuario_id, s.seccion_id "
                  "FROM acceso.usuario_autorizado u, abet.seccion s JOIN abet.asignatura a USING (asignatura_id) "
                  "WHERE u.correo = 'docente.varias@example.invalid' AND a.codigo = '450010' AND s.numero = '412'")
    corrida = _correr(copia, tmp_path, BASE, "--aplicar")
    informe = corrida.stdout.splitlines()
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert informe == [
        "Resumen. 2 secciones nuevas, 2 usuarios nuevos y 2 asignaciones nuevas.",
        "Aviso. La sección 413 de 450002 está en la base con 0 asignaciones y el archivo no la trae.",
        "Aviso. La sección 412 de 450010 está en la base con 1 asignación y el archivo no la trae.",
        "Aviso. La sección 412 de 450010 tiene en la base a docente.varias@example.invalid y el archivo no la trae.",
        CONTRASENA,
        "Cambios guardados.",
    ]
    assert dueno.execute("SELECT count(*) FROM abet.seccion").fetchone()[0] == 4


def test_avisa_la_asignatura_fuera_del_plan_de_estudios(copia: Any, dueno: psycopg.Connection,
                                                       tmp_path: Path) -> None:
    # Una asignatura inventada que existe en abet.asignatura y no en el plan de estudios de AMB-2026.
    dueno.execute("INSERT INTO abet.asignatura (codigo, nombre) VALUES ('990001', 'Asignatura inventada de prueba')")
    corrida = _correr(copia, tmp_path, [("2026-2", "990001", "410", "docente410@example.invalid", "")], "--aplicar")
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert corrida.stdout.splitlines()[1:3] == [
        "Aviso. La asignatura 990001 no tiene plan de medición en 2026-2, así que su sección 410 no podrá recibir exports.",
        "Aviso. La asignatura 990001 no está en el plan de estudios vigente en 2026-2, así que la coordinación no verá su sección 410.",
    ]


def test_sin_aplicar_el_sql_no_guarda_nada(copia: Any, dueno: psycopg.Connection) -> None:
    # El SQL solo, sin -v aplicar, se detiene antes de abrir la transacción en lugar de cerrar como en seco.
    entorno = C.entorno_de_programacion(copia.nombre)
    corrida = subprocess.run(["psql", "-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1", "-v", "periodo=2026-2",
                              "-f", str(SQL)], env=entorno, input="", capture_output=True, text=True, check=False)
    assert corrida.returncode == 3
    assert "Falta aplicar, por ejemplo -v aplicar=0." in corrida.stdout
    assert dueno.execute("SELECT count(*) FROM abet.seccion").fetchone()[0] == 0


def test_los_insert_nombran_su_restriccion_y_no_hay_delete() -> None:
    # Con el objetivo nombrado, un choque de uq_seccion_curso_bb llega como error de la base (código 3) y no se
    # salta en silencio (AD-03 de la revisión de T006).
    texto = SQL.read_text(encoding="utf-8")
    sentencias = "\n".join(linea for linea in texto.splitlines() if not linea.lstrip().startswith("--"))
    assert "ON CONFLICT (periodo_id, asignatura_id, numero) DO NOTHING" in sentencias
    assert "ON CONFLICT (usuario_id, seccion_id) DO NOTHING" in sentencias
    # Desde la spec 010 el INSERT de usuarios tiene dos formas, con y sin la columna nombre, según la base tenga V1_16.
    assert sentencias.count("ON CONFLICT") == 4 and sentencias.count("ON CONFLICT (correo) DO NOTHING") == 2
    assert "DELETE" not in sentencias.upper()
    # Cambio del 2026-11-25 (spec 010, FR-005). Hay un segundo UPDATE, el del nombre nulo de un PROFESOR que ya existe, y
    # ninguno cambia rol ni activo.
    assert sentencias.upper().count("UPDATE ") == 2
    assert "SET curso_blackboard = ps.curso_blackboard" in sentencias and "SET nombre = pn.nombre" in sentencias
    assert "u.nombre IS NULL" in sentencias and "u.rol = 'PROFESOR'" in sentencias
    assert "SET rol" not in sentencias and "SET activo" not in sentencias
    assert "acceso.credencial" not in sentencias


@pytest.mark.parametrize(("opciones", "mensaje"), [
    ((), "La base no responde y no se guardó nada."),
    (("--aplicar",), "La base no responde y no se sabe si guardó los cambios. Una corrida en seco lo muestra."),
], ids=["en_seco", "aplicar"])
def test_una_base_que_no_responde_da_el_codigo_3(copia: Any, tmp_path: Path, opciones: tuple[str, ...],
                                                 mensaje: str) -> None:
    entorno = C.entorno_de_programacion(copia.nombre)
    carpeta = tmp_path / "sin_socket"
    carpeta.mkdir()
    entorno["PGHOST"] = str(carpeta)
    corrida = C.correr_programacion(entorno, "--periodo", "2026-2", "--archivo", str(_archivo(tmp_path, _csv(BASE))),
                                    *opciones)
    assert corrida.returncode == 3
    assert corrida.stdout.splitlines() == [mensaje]


@pytest.mark.parametrize("abreviatura", ["--ap", "--apli"])
def test_una_abreviatura_de_aplicar_no_escribe(copia: Any, dueno: psycopg.Connection, tmp_path: Path,
                                               abreviatura: str) -> None:
    antes = _tres_tablas(dueno)
    corrida = _correr(copia, tmp_path, BASE, abreviatura)
    assert (corrida.returncode, corrida.stdout.splitlines()) == (2, [USO])
    assert _tres_tablas(dueno) == antes


def test_un_correo_con_un_espacio_de_ancho_cero_no_crea_un_usuario(copia: Any, dueno: psycopg.Connection,
                                                                    tmp_path: Path) -> None:
    antes = _tres_tablas(dueno)
    filas = [BASE[0], (*BASE[1][:3], BASE[1][3] + "\u200b", BASE[1][4])]
    corrida = _correr(copia, tmp_path, filas, "--aplicar")
    assert corrida.returncode == 1
    assert corrida.stdout.splitlines() == ["Fila 3. El correo trae un carácter invisible o de control.", RECHAZADO]
    assert _tres_tablas(dueno) == antes


def test_el_dueno_sin_superusuario_corre_el_guion(copia: Any, dueno: psycopg.Connection, tmp_path: Path) -> None:
    # En Neon corre neondb_owner, que no es superusuario y conserva TEMP como dueño de la base, aunque
    # crear_roles_lectura.sql lo quita a PUBLIC.
    rol = f"abet_demo_dueno_{os.urandom(3).hex()}"
    dueno.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER").format(sql.Identifier(rol)))
    try:
        dueno.execute(sql.SQL("ALTER DATABASE {} OWNER TO {}").format(sql.Identifier(copia.nombre), sql.Identifier(rol)))
        dueno.execute(sql.SQL("REVOKE TEMPORARY ON DATABASE {} FROM PUBLIC").format(sql.Identifier(copia.nombre)))
        dueno.execute(sql.SQL("GRANT USAGE ON SCHEMA abet, acceso TO {}").format(sql.Identifier(rol)))
        dueno.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA abet, acceso TO {}").format(sql.Identifier(rol)))
        dueno.execute(sql.SQL("GRANT INSERT, UPDATE ON abet.seccion, acceso.usuario_autorizado, "
                              "acceso.docente_seccion TO {}").format(sql.Identifier(rol)))
        entorno = {**C.entorno_de_programacion(copia.nombre), "PGUSER": rol}
        corrida = C.correr_programacion(entorno, "--periodo", "2026-2", "--archivo", str(_archivo(tmp_path, _csv(BASE))),
                                        "--aplicar")
        assert corrida.returncode == 0, corrida.stdout + corrida.stderr
        assert corrida.stdout.splitlines()[-1] == "Cambios guardados."
        assert dueno.execute("SELECT count(*) FROM acceso.docente_seccion").fetchone()[0] == 2
    finally:
        dueno.execute(sql.SQL("ALTER DATABASE {} OWNER TO CURRENT_USER").format(sql.Identifier(copia.nombre)))
        dueno.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(rol)))
        dueno.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(rol)))


def test_la_corrida_en_seco_de_300_filas_termina_en_menos_de_10_s(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    # SC-005 y T034. Un archivo inventado de 300 filas, cada una con su sección, su profesor y su curso.
    filas = [("2026-2", "450002", str(1000 + n), f"docente{1000 + n}@example.invalid", f"SINTETICO_20262_450002_{1000 + n}")
             for n in range(300)]
    antes = _tres_tablas(dueno)
    inicio = time.monotonic()
    corrida = _correr(copia, tmp_path, filas)
    duracion = time.monotonic() - inicio
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert corrida.stdout.splitlines()[0] == "Resumen. 300 secciones nuevas, 300 usuarios nuevos y 300 asignaciones nuevas."
    assert duracion < 10, f"la corrida en seco de 300 filas tarda {duracion:.1f} s"
    assert _tres_tablas(dueno) == antes


# .gitignore (T033)

@pytest.mark.skipif(shutil.which("git") is None, reason="git no está instalado")
@pytest.mark.parametrize("ruta", ["programacion_20262_real.csv", "db/herramientas/programacion_x.csv",
                                  "tests/datos_inventados/programacion_x.csv"])
def test_un_archivo_de_programacion_queda_fuera_de_git(ruta: str) -> None:
    corrida = subprocess.run(["git", "check-ignore", "-q", "--no-index", ruta], cwd=RAIZ, capture_output=True,
                             check=False)
    assert corrida.returncode == 0, f"{ruta} no queda ignorado"


# La columna nombre contra la base (spec 010, US-96, T031)

def _filas_con_nombre(*nombres: str) -> list[tuple[str, ...]]:
    return [(*fila, nombre) for fila, nombre in zip(BASE, nombres, strict=True)]


def _nombres(conexion: psycopg.Connection) -> dict[str, str | None]:
    # La coordinación de la base de partida queda fuera, porque ningún archivo de estas pruebas la nombra.
    return dict(conexion.execute("SELECT correo, nombre FROM acceso.usuario_autorizado"
                                 " WHERE correo <> 'coordinacion@example.invalid'").fetchall())


def test_la_corrida_en_seco_cuenta_los_nombres_completados_y_no_guarda_ninguno(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES (%s, 'PROFESOR')", (BASE[0][3],))
    antes = _tres_tablas(dueno)
    corrida = _correr(copia, tmp_path, _filas_con_nombre(*NOMBRES), encabezados=CON_NOMBRE)
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert corrida.stdout.splitlines()[0] == ("Resumen. 2 secciones nuevas, 1 usuario nuevo, 2 asignaciones nuevas y "
                                              "1 nombre completado.")
    assert corrida.stdout.splitlines()[-1] == "Corrida en seco. Nada se escribió."
    assert _tres_tablas(dueno) == antes
    assert not any(nombre in corrida.stdout + corrida.stderr for nombre in NOMBRES)


def test_una_cuenta_coordinador_nunca_recibe_nombre_y_el_informe_no_lo_dice(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES (%s, 'COORDINADOR')", (BASE[0][3],))
    corrida = _correr(copia, tmp_path, _filas_con_nombre(*NOMBRES), "--aplicar", encabezados=CON_NOMBRE)
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert _nombres(dueno) == {BASE[0][3]: None, BASE[1][3]: NOMBRES[1]}
    assert dueno.execute("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", (BASE[0][3],)
                         ).fetchall() == [("COORDINADOR", True)]
    assert "0 nombres completados" in corrida.stdout.splitlines()[0]
    assert not any(nombre in corrida.stdout + corrida.stderr for nombre in NOMBRES)


def test_el_mismo_nombre_ya_guardado_no_da_aviso_y_la_segunda_corrida_no_cambia_nada(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    primera = _correr(copia, tmp_path, _filas_con_nombre(*NOMBRES), "--aplicar", encabezados=CON_NOMBRE)
    assert primera.returncode == 0 and primera.stdout.splitlines()[-1] == "Cambios guardados.", primera.stdout
    despues_de_la_primera = _tres_tablas(dueno)
    segunda = _correr(copia, tmp_path, _filas_con_nombre(*NOMBRES), "--aplicar", encabezados=CON_NOMBRE)
    assert segunda.returncode == 0, segunda.stdout + segunda.stderr
    assert segunda.stdout.splitlines() == ["Resumen. 0 secciones nuevas, 0 usuarios nuevos, 0 asignaciones nuevas y "
                                           "0 nombres completados.", "Sin cambios."]
    assert _tres_tablas(dueno) == despues_de_la_primera


def test_con_la_columna_nombre_vacia_el_resumen_trae_el_cuarto_termino_y_nadie_recibe_nombre(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    corrida = _correr(copia, tmp_path, _filas_con_nombre("", ""), "--aplicar", encabezados=CON_NOMBRE)
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert corrida.stdout.splitlines()[0] == ("Resumen. 2 secciones nuevas, 2 usuarios nuevos, 2 asignaciones nuevas y "
                                              "0 nombres completados.")
    assert set(_nombres(dueno).values()) == {None}


def test_un_profesor_con_dos_filas_y_el_nombre_en_una_sola_lo_recibe(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    filas = [(*BASE[0], ""), (*BASE[1][:3], BASE[0][3], BASE[1][4], NOMBRES[0])]
    corrida = _correr(copia, tmp_path, filas, "--aplicar", encabezados=CON_NOMBRE)
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert _nombres(dueno) == {BASE[0][3]: NOMBRES[0]}


def test_un_nombre_que_la_base_rechazaria_no_llega_a_ella_porque_el_guion_lo_normaliza(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    corrida = _correr(copia, tmp_path, _filas_con_nombre(" Profesor   Inventado Uno ", "Profesor Inventado Ángel"),
                      "--aplicar", encabezados=CON_NOMBRE)
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert _nombres(dueno) == {BASE[0][3]: "Profesor Inventado Uno", BASE[1][3]: "Profesor Inventado Ángel"}


def test_los_nombres_de_dos_filas_de_correos_distintos_no_se_mezclan(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    corrida = _correr(copia, tmp_path, _filas_con_nombre(NOMBRES[1], NOMBRES[0]), "--aplicar", encabezados=CON_NOMBRE)
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert _nombres(dueno) == {BASE[0][3]: NOMBRES[1], BASE[1][3]: NOMBRES[0]}


def test_el_aviso_de_otro_nombre_lleva_el_correo_y_ninguno_de_los_dos_nombres(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol, nombre) VALUES (%s, 'PROFESOR', %s)",
                  (BASE[1][3], "Profesor Inventado Anterior"))
    corrida = _correr(copia, tmp_path, _filas_con_nombre(*NOMBRES), "--aplicar", encabezados=CON_NOMBRE)
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    avisos = [linea for linea in corrida.stdout.splitlines() if "otro nombre" in linea]
    assert avisos == [f"Aviso. {BASE[1][3]} ya tiene otro nombre en la base y no se cambia."]
    assert not any(n in corrida.stdout + corrida.stderr for n in (*NOMBRES, "Profesor Inventado Anterior"))
    assert _nombres(dueno)[BASE[1][3]] == "Profesor Inventado Anterior"


# Una base sin V1_16 (spec 010, FR-014 y el riesgo del plan)

def _sin_v1_16(dueno: psycopg.Connection) -> None:
    dueno.execute("ALTER TABLE acceso.usuario_autorizado DROP COLUMN nombre")


def test_una_base_sin_v1_16_carga_un_archivo_sin_la_columna_nombre_como_en_la_spec_006(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    _sin_v1_16(dueno)
    corrida = _correr(copia, tmp_path, BASE, "--aplicar")
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    assert corrida.stdout.splitlines()[0] == "Resumen. 2 secciones nuevas, 2 usuarios nuevos y 2 asignaciones nuevas."
    assert corrida.stdout.splitlines()[-1] == "Cambios guardados."


def test_una_base_sin_v1_16_rechaza_un_archivo_con_la_columna_nombre_sin_escribir_nada(
    copia: Any, dueno: psycopg.Connection, tmp_path: Path,
) -> None:
    _sin_v1_16(dueno)
    antes = _tres_tablas(dueno)
    corrida = _correr(copia, tmp_path, _filas_con_nombre(*NOMBRES), "--aplicar", encabezados=CON_NOMBRE)
    assert corrida.returncode == 3, corrida.stdout + corrida.stderr
    assert corrida.stdout.splitlines() == ["La base rechazó la escritura y no guardó nada."]
    assert _tres_tablas(dueno) == antes
    assert not any(nombre in corrida.stdout + corrida.stderr for nombre in NOMBRES)
