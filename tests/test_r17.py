"""Pruebas del R-17, el reporte de medición de la sección, y de su hoja «Constancia» (T035).

r17.generar() arma el R-17 de una carga PUBLICADA desde abet.v_r17_por_pi y las tablas de la carga,
sobre plantillas/R017_ambiental_general.xlsx, con el rol de la aplicación, como la ruta
GET /api/cargas/{carga_id}/r17.xlsx. Las bases son desechables (tests/base_desechable.py) y parten de
db/pruebas/datos_sinteticos.sql, con las cargas que arma tests/cargas_de_prueba.py, porque la carga
real (T033) se escribe en otra etapa. Cada regla de negocio (business rule, BR) de BR-R17-01 a
BR-R17-09 tiene pruebas de lo que debe pasar y de lo que no debe pasar (AGENTS.md, regla 8), con
valores esperados que salen de los escenarios de r17_constancia.feature o de la cuenta a mano sobre
los niveles de los datos sintéticos. Los indicadores de desempeño (performance indicators, PI) y el
resultado del estudiante (student outcome, SO) ocupan las filas fijas del mapa de plantillas/README.md.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import zipfile
from collections import Counter
from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import openpyxl
import openpyxl.drawing.image
import psycopg
import pytest
from openpyxl.worksheet.worksheet import Worksheet

from abet_carga import constancia, r17


def _modulo(nombre: str) -> ModuleType:
    """Módulo de tests/ cargado por su ruta, porque tests/ no es un paquete."""
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, Path(__file__).with_name(f"{nombre}.py"))
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


CARGAS = _modulo("cargas_de_prueba")
RAIZ = Path(__file__).resolve().parent.parent
LOGOTIPO = RAIZ / "plantillas" / "R017_logotipo.png"
EXPORT_CON_ERROR = RAIZ / "tests" / "datos_inventados" / "export_inventado_410_con_error.xlsx"
HOJA = "Cursos de Carrera"
HUELLA_CORRECTO = "c92c5056de54d0bb3500ce84bf3f991027741f32ec0e0432dc697ecabee5578f"
HUELLA_CON_ERROR = "2b94db8d8abfd5ff24425584172de7942383c480f25ee0a8cacf927e17df2d15"
PIS_410 = ("5.1", "5.2", "5.3")
# Fila del archivo y niveles en 5.1, 5.2 y 5.3 de cada estudiante de la 410, de db/pruebas/datos_sinteticos.sql.
NIVELES_410 = {
    "99000001": (2, 3, 4, 3), "99000002": (3, 4, 3, 4), "99000003": (4, 2, 3, 3), "99000004": (5, 3, 2, 3),
    "99000005": (6, 1, 2, 2), "99000006": (7, 4, 3, 4), "99000007": (8, 3, 4, 3), "99000008": (9, 2, 1, 1),
    "99000009": (10, 4, 3, 4), "99000010": (11, 3, 4, 3), "99000011": (12, 2, 2, 2),
}
FRASE_FINAL = ("Los números de este R-17 los calcula el sistema desde la carga registrada en la base, "
               "no desde fórmulas.")
FRANJA_BORRADOR = ("R-17 PROVISIONAL. Las reglas de la carrera (conjunto R-2026-BORRADOR) aún no están aprobadas. "
                   "No usar como evidencia oficial.")
NO_LOGRADO = "El indicador aún no alcanza lo esperado, pero es una buena oportunidad para mejorar"
LOGRADO = "¡Felicidades! Logró alcanzar el indicador. Lo animamos a seguir mejorando con nuevas iniciativas."
AVISO_5_3 = "PI 5.3. La columna declara 20 puntos y sus notas están entre 1 y 4. Se cargó igual."
FILAS_DE_LA_TABLA = range(43, 185)


# Ayudas

def _generar(base: Any, carga_id: int, carpeta: Path) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(base.conexion_app) as conexion:
        return r17.generar(conexion, carga_id, carpeta)


def _consulta(base: Any, consulta: str, parametros: tuple[object, ...]) -> list[tuple[Any, ...]]:
    with psycopg.connect(base.conexion) as conexion:
        return conexion.execute(consulta, parametros).fetchall()


def _vista(base: Any, carga_id: int) -> list[tuple[Any, ...]]:
    """Filas de v_r17_por_pi de la carga, por PI, con el porcentaje, la meta y los conteos por nivel."""
    return _consulta(
        base,
        "SELECT pi, pct_logro_sobre_calificados, meta_logro_pct, n_nivel_1, n_nivel_2, n_nivel_3, n_nivel_4, "
        "provisional, carga_id FROM abet.v_r17_por_pi WHERE carga_id = %s ORDER BY so, pi",
        (carga_id,),
    )


def _libro(ruta: Path) -> openpyxl.Workbook:
    return openpyxl.load_workbook(ruta)


def _tabla(hoja: Worksheet) -> list[tuple[Any, ...]]:
    """Filas ocupadas de la tabla de estudiantes, de B a F."""
    filas = [tuple(hoja.cell(fila, columna).value for columna in range(2, 7)) for fila in FILAS_DE_LA_TABLA]
    return [fila for fila in filas if any(valor is not None for valor in fila)]


def _tabla_esperada(sin: str | None = None) -> list[tuple[Any, ...]]:
    """La tabla de la 410 hecha a mano con los niveles de los datos sintéticos, por PI y por fila de origen."""
    por_fila = sorted(NIVELES_410.items(), key=lambda par: par[1][0])
    return [(5, pi, None, codigo, niveles[1 + i]) for i, pi in enumerate(PIS_410)
            for codigo, niveles in por_fila if codigo != sin]


def _textos(libro: openpyxl.Workbook) -> list[str]:
    return [str(celda.value) for hoja in libro.worksheets for fila in hoja.iter_rows() for celda in fila
            if celda.value is not None]


def _pares(hoja: Worksheet) -> dict[Any, Any]:
    """Rótulo de la columna A y valor de la columna B de cada fila de la hoja «Constancia» que trae los dos."""
    return {a.value: b.value for a, b in hoja.iter_rows(min_col=1, max_col=2)
            if a.value is not None and b.value is not None}


def _niveles(hoja: Worksheet) -> list[tuple[Any, ...]]:
    return [tuple(hoja.cell(fila, columna).value for columna in range(11, 18)) for fila in (29, 30, 31)]


def _partes(ruta: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(ruta) as libro:
        return {nombre: libro.read(nombre) for nombre in libro.namelist()}


# Bases y R-17 de cada caso

@pytest.fixture(scope="module")
def base_410(base_desechable: ModuleType) -> Iterator[tuple[Any, dict[str, int]]]:
    """Base con la 410 de los datos sintéticos publicada y cargas de otras asignaturas y secciones del plan."""
    with base_desechable.abierta(datos_2026_2=False, despues=[CARGAS.SINTETICOS, base_desechable.DATOS_2026_2]) as base:
        with psycopg.connect(base.conexion) as conexion:
            ids = _cargas_de_la_410(conexion)
        yield base, ids


def _cargas_de_la_410(conexion: psycopg.Connection) -> dict[str, int]:
    publicar, fila = CARGAS.publicar, CARGAS.Fila
    ids = {"correcta": CARGAS.preparar_410(conexion)}
    ids["sin_5_2"] = CARGAS.rechazar(
        conexion, motivo="PI_DEL_PLAN_AUSENTE", pi="5.2", nombre_archivo="sin_5_2_410.xlsx")
    # 450020 mide solo el PI 1.1 del SO 1, y la fila 5 trae la celda vacía (SIN_EVIDENCIA).
    ids["un_pi"] = publicar(
        conexion, asignatura="450020", numero="301", pis=["1.1"], nombre_archivo="export_450020_301.xlsx",
        hoja="gc_SINTETICO_20262_450020_301_f",
        filas=[fila(2, "99000401", (3,)), fila(3, "99000402", (4,)), fila(4, "99000403", (2,)),
               fila(5, "99000404", (None,))],
    )
    CARGAS.plan(conexion, "450001", ["2.1", "2.2", "7.1"])
    ids["dos_so"] = publicar(
        conexion, asignatura="450001", numero="401", pis=["2.1", "2.2", "7.1"], nombre_archivo="export_450001_401.xlsx",
        hoja="gc_SINTETICO_20262_450001_401_f", filas=[fila(2, "99000411", (4, 3, 2)), fila(3, "99000412", (1, 2, 3))],
    )
    CARGAS.plan(conexion, "450012", ["2.1", "2.2", "7.1", "7.2"])
    ids["cuatro_pi"] = publicar(
        conexion, asignatura="450012", numero="401", pis=["2.1", "2.2", "7.1", "7.2"],
        nombre_archivo="export_450012_401.xlsx", hoja="gc_SINTETICO_20262_450012_401_f",
        filas=[fila(2, "99000421", (3, 3, 3, 3))],
    )
    ids["142"] = publicar(
        conexion, asignatura="450020", numero="302", pis=["1.1"], nombre_archivo="export_450020_302.xlsx",
        hoja="gc_SINTETICO_20262_450020_302_f", filas=CARGAS.filas_inventadas(142, desde=99000501, niveles=(3,)),
    )
    ids["143"] = publicar(
        conexion, asignatura="450020", numero="303", pis=["1.1"], nombre_archivo="export_450020_303.xlsx",
        hoja="gc_SINTETICO_20262_450020_303_f", filas=CARGAS.filas_inventadas(143, desde=99000701, niveles=(3,)),
    )
    # Un PI con todas sus mediciones SIN_EVIDENCIA y otro con un conjunto sin nivel esperado ni meta.
    ids["sin_evidencia"] = publicar(
        conexion, asignatura="450020", numero="304", pis=["1.1"], nombre_archivo="export_450020_304.xlsx",
        hoja="gc_SINTETICO_20262_450020_304_f", filas=CARGAS.filas_inventadas(2, desde=99000431, niveles=(None,)),
    )
    CARGAS.conjunto_pendiente(conexion, "R-PRUEBA-PENDIENTE")
    ids["sin_reglas"] = publicar(
        conexion, asignatura="450020", numero="305", pis=["1.1"], nombre_archivo="export_450020_305.xlsx",
        hoja="gc_SINTETICO_20262_450020_305_f", conjunto="R-PRUEBA-PENDIENTE",
        filas=[fila(2, "99000441", (3,)), fila(3, "99000442", (4,))],
    )
    # 4 de 5 con nivel 3 o más dan 80,0 %, justo la meta de R-2026-BORRADOR.
    ids["en_la_meta"] = publicar(
        conexion, asignatura="450020", numero="306", pis=["1.1"], nombre_archivo="export_450020_306.xlsx",
        hoja="gc_SINTETICO_20262_450020_306_f",
        filas=[fila(2 + i, f"9900045{i}", (nivel,)) for i, nivel in enumerate((3, 3, 4, 3, 2))],
    )
    # Un nombre de archivo que empieza por «=» y trae un carácter de control, que llega de la petición.
    ids["hostil"] = publicar(
        conexion, asignatura="450002", numero="411", pis=list(PIS_410), nombre_archivo="=1+1\x01.xlsx",
        hoja="gc_SINTETICO_20262_450002_411_f", filas=[fila(2, "99000901", (3, 3, 3))],
    )
    return ids


@pytest.fixture(scope="module")
def r17_correcto(base_410: tuple[Any, dict[str, int]], tmp_path_factory: pytest.TempPathFactory) -> Path:
    base, ids = base_410
    return _generar(base, ids["correcta"], tmp_path_factory.mktemp("r17_correcto"))


@pytest.fixture(scope="module")
def base_con_error(base_desechable: ModuleType) -> Iterator[tuple[Any, dict[str, int]]]:
    """Base de los datos sintéticos con la 410 reemplazada por la carga del export con el 5 en la fila 3."""
    with base_desechable.abierta(datos_2026_2=False, despues=[CARGAS.SINTETICOS, base_desechable.DATOS_2026_2]) as base:
        with psycopg.connect(base.conexion) as conexion:
            reemplazada = CARGAS.preparar_410(conexion)
            ids = {"reemplazada": reemplazada, "con_error": CARGAS.con_error(conexion, reemplazada)}
        yield base, ids


@pytest.fixture(scope="module")
def r17_con_error(base_con_error: tuple[Any, dict[str, int]], tmp_path_factory: pytest.TempPathFactory) -> Path:
    base, ids = base_con_error
    return _generar(base, ids["con_error"], tmp_path_factory.mktemp("r17_con_error"))


@pytest.fixture(scope="module")
def base_aprobada(base_desechable: ModuleType) -> Iterator[tuple[Any, dict[str, int]]]:
    """Base con la 410 reprocesada con R-PRUEBA-APROBADO y la 411 con un conjunto aprobado e incompleto.

    Al conjunto de la 411 le falta definir TRATO_SIN_EVIDENCIA, y su archivo es el export de la 411, que
    esta base no usa en otra carga.
    """
    with base_desechable.abierta(datos_2026_2=False, despues=[CARGAS.SINTETICOS, base_desechable.DATOS_2026_2]) as base:
        with psycopg.connect(base.conexion) as conexion:
            ids = {"aprobada": CARGAS.aprobar(conexion, CARGAS.preparar_410(conexion))}
            CARGAS.conjunto_aprobado(conexion, "R-PRUEBA-INCOMPLETO", completo=False)
            ids["incompleta"] = CARGAS.publicar(
                conexion, asignatura="450002", numero="411", pis=list(PIS_410),
                nombre_archivo="export_inventado_411.xlsx", hoja="gc_SINTETICO_20262_450002_411_f",
                conjunto="R-PRUEBA-INCOMPLETO",
                filas=CARGAS.filas_inventadas(3, desde=99000012, niveles=(3, 3, 3)),
            )
        yield base, ids


@pytest.fixture(scope="module")
def base_mutada(base_desechable: ModuleType) -> Iterator[tuple[Any, int]]:
    """Base de la 410 con dos mediciones cambiadas a mano después de publicarse.

    99000001 pasa del 3 al 1 en el PI 5.1, y 99000002 queda SIN_EVIDENCIA en el PI 5.2, así que la
    base ya no dice lo mismo que el export correcto.
    """
    with base_desechable.abierta(datos_2026_2=False, despues=[CARGAS.SINTETICOS, base_desechable.DATOS_2026_2]) as base:
        with psycopg.connect(base.conexion) as conexion:
            carga_id = CARGAS.preparar_410(conexion)
            cambio = ("UPDATE abet.medicion m SET estado_evidencia = %s, nivel_original = %s "
                      "FROM abet.estudiante e, abet.pi p WHERE m.carga_id = %s AND e.estudiante_id = m.estudiante_id "
                      "AND p.pi_id = m.pi_id AND e.codigo = %s AND p.codigo = %s")
            conexion.execute(cambio, ("CALIFICADO", 1, carga_id, "99000001", "5.1"))
            conexion.execute(cambio, ("SIN_EVIDENCIA", None, carga_id, "99000002", "5.2"))
        yield base, carga_id


# BR-R17-01: R-17 solo de una carga PUBLICADA.

def test_br_r17_01_el_r17_de_una_carga_publicada_abre_con_openpyxl_con_sus_dos_hojas(r17_correcto: Path) -> None:
    assert r17_correcto.is_file()
    assert _libro(r17_correcto).sheetnames == [HOJA, "Constancia"]
    solo_lectura = openpyxl.load_workbook(r17_correcto, read_only=True, data_only=True)
    assert solo_lectura.sheetnames == [HOJA, "Constancia"]
    solo_lectura.close()


def test_br_r17_01_una_carga_rechazada_no_tiene_r17_y_no_deja_archivo(
    base_410: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_410
    with pytest.raises(r17.CargaNoPublicada) as error:
        _generar(base, ids["sin_5_2"], tmp_path)
    assert (error.value.mensaje, error.value.codigo_http) == ("La carga no está publicada y no tiene R-17.", 409)
    assert list(tmp_path.iterdir()) == []
    assert _vista(base, ids["sin_5_2"]) == []


def test_br_r17_01_una_carga_reemplazada_no_tiene_r17(
    base_con_error: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_con_error
    with pytest.raises(r17.CargaNoPublicada):
        _generar(base, ids["reemplazada"], tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_br_r17_01_una_carga_que_no_existe_no_tiene_r17(base_410: tuple[Any, dict[str, int]], tmp_path: Path) -> None:
    base, ids = base_410
    with pytest.raises(constancia.CargaInexistente):
        _generar(base, max(ids.values()) + 1000, tmp_path)
    assert list(tmp_path.iterdir()) == []


# BR-R17-02: la vista abet.v_r17_por_pi como única fuente de las cifras.

def test_br_r17_02_la_cabecera_y_el_bloque_ii_muestran_las_cifras_de_la_vista(
    r17_correcto: Path, base_410: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_410
    hoja = _libro(r17_correcto)[HOJA]
    assert [hoja[ref].value for ref in ("D8", "D10", "D11", "I11")] == ["450002", None, "410", "2026-2"]
    nombre = _consulta(base, "SELECT nombre FROM abet.asignatura WHERE codigo = %s", ("450002",))[0][0]
    assert hoja["D9"].value == nombre
    assert [hoja[f"B{fila}"].value for fila in (24, 25, 26)] == list(PIS_410)
    assert [hoja[f"E{fila}"].value for fila in (24, 25, 26)] == pytest.approx([0.636, 0.636, 0.727])
    assert {hoja[f"E{fila}"].number_format for fila in (24, 25, 26)} == {"0.0%"}
    assert [hoja[f"G{fila}"].value for fila in (24, 25, 26)] == pytest.approx([0.8, 0.8, 0.8])
    assert _niveles(hoja) == [("5.1", 1, 3, 4, 3, "7 de 11", pytest.approx(0.636)),
                              ("5.2", 1, 3, 4, 3, "7 de 11", pytest.approx(0.636)),
                              ("5.3", 1, 2, 5, 3, "8 de 11", pytest.approx(0.727))]
    vista = _vista(base, ids["correcta"])
    for fila, (pi, pct, meta, *conteos, _provisional, _carga) in zip((24, 25, 26), vista, strict=True):
        assert hoja[f"B{fila}"].value == pi
        assert hoja[f"E{fila}"].value == pytest.approx(float(pct) / 100)
        assert hoja[f"G{fila}"].value == pytest.approx(float(meta) / 100)
        assert list(_niveles(hoja)[fila - 24][1:5]) == conteos
    assert [hoja[ref].value for ref in ("M24", "M25")] == [11, 22]
    assert hoja["M26"].value == pytest.approx(22 / 33)
    assert [hoja[f"H{fila}"].value for fila in (24, 25, 26)] == [NO_LOGRADO] * 3


def test_br_r17_02_el_bloque_i_muestra_el_so_y_los_pi_del_plan(
    r17_correcto: Path, base_410: tuple[Any, dict[str, int]],
) -> None:
    base, _ids = base_410
    hoja = _libro(r17_correcto)[HOJA]
    descripciones = dict(
        _consulta(base, "SELECT codigo, descripcion FROM abet.pi WHERE codigo = ANY(%s)", (list(PIS_410),)))
    assert hoja["B15"].value == "Student Outcome (SO) 5"
    assert [hoja[f"B{fila}"].value for fila in (17, 18, 19)] == list(PIS_410)
    assert [hoja[f"C{fila}"].value for fila in (17, 18, 19)] == [descripciones[pi] for pi in PIS_410]
    assert [hoja[f"E{fila}"].value for fila in (17, 18, 19)] == ["Trabajo Integrador"] * 3
    assert [hoja[f"C{fila}"].value for fila in (24, 25, 26)] == ["Trabajo Integrador"] * 3
    assert [hoja[f"G{fila}"].value for fila in (17, 18, 19)] == [None] * 3


def test_br_r17_02_con_el_export_con_error_el_bloque_ii_muestra_60_60_y_70(r17_con_error: Path) -> None:
    hoja = _libro(r17_con_error)[HOJA]
    assert [hoja[f"E{fila}"].value for fila in (24, 25, 26)] == pytest.approx([0.6, 0.6, 0.7])
    assert _niveles(hoja) == [("5.1", 1, 3, 4, 2, "6 de 10", pytest.approx(0.6)),
                              ("5.2", 1, 3, 3, 3, "6 de 10", pytest.approx(0.6)),
                              ("5.3", 1, 2, 5, 2, "7 de 10", pytest.approx(0.7))]
    assert [hoja[ref].value for ref in ("M24", "M25")] == [11, 19]


def test_br_r17_02_el_r17_sigue_a_la_base_y_no_al_archivo_subido(base_mutada: tuple[Any, int], tmp_path: Path) -> None:
    base, carga_id = base_mutada
    hoja = _libro(_generar(base, carga_id, tmp_path))[HOJA]
    # El export correcto daría 63,6 % en 5.1; la base, con el 1 de 99000001, da 6 de 11.
    assert hoja["E24"].value == pytest.approx(0.545)
    assert _niveles(hoja)[0][:6] == ("5.1", 2, 3, 3, 3, "6 de 11")
    assert [fila[0] for fila in _vista(base, carga_id)] == list(PIS_410)


def test_br_r17_02_un_porcentaje_igual_a_la_meta_alcanza_el_indicador(
    base_410: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_410
    hoja = _libro(_generar(base, ids["en_la_meta"], tmp_path))[HOJA]
    assert [hoja[ref].value for ref in ("E24", "G24")] == pytest.approx([0.8, 0.8])
    assert hoja["H24"].value == LOGRADO


def test_br_r17_02_un_pi_sin_mediciones_calificadas_queda_sin_porcentaje_y_nunca_logrado(
    base_410: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_410
    hoja = _libro(_generar(base, ids["sin_evidencia"], tmp_path))[HOJA]
    # La vista da el porcentaje nulo sin calificados (H80), y el R-17 no lo convierte en 0 ni en logrado.
    assert [hoja[ref].value for ref in ("E24", "H24", "M24", "M25", "M26")] == [None, None, 0, 0, None]
    assert hoja["G24"].value == pytest.approx(0.8)
    assert _niveles(hoja)[0] == ("1.1", 0, 0, 0, 0, "0 de 0", 0.0)
    assert [fila[4] for fila in _tabla(hoja)] == [None, None]


def test_br_r17_02_sin_nivel_esperado_ni_meta_el_r17_no_inventa_cifras(
    base_410: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_410
    hoja = _libro(_generar(base, ids["sin_reglas"], tmp_path))[HOJA]
    assert [hoja[ref].value for ref in ("E24", "G24", "H24")] == [None, None, None]
    assert _niveles(hoja)[0] == ("1.1", 0, 0, 1, 1, None, None)
    assert [hoja[ref].value for ref in ("M24", "M25", "M26")] == [0, 2, 1.0]
    assert "R-PRUEBA-PENDIENTE" in hoja["B7"].value


def test_br_r17_02_sirve_para_otra_asignatura_con_un_solo_pi(
    base_410: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_410
    ruta = _generar(base, ids["un_pi"], tmp_path)
    hoja = _libro(ruta)[HOJA]
    assert ruta.name == "R017_450020_301_2026-2_PROVISIONAL.xlsx"
    assert [hoja[ref].value for ref in ("D8", "D11", "I11", "B15")] == [
        "450020", "301", "2026-2", "Student Outcome (SO) 1"]
    assert [hoja[f"B{fila}"].value for fila in (17, 18, 19, 24, 25, 26)] == ["1.1", None, None, "1.1", None, None]
    assert hoja["E24"].value == pytest.approx(0.667) and hoja["E25"].value is None
    assert _niveles(hoja) == [("1.1", 0, 1, 1, 1, "2 de 3", pytest.approx(0.5)), (None,) * 7, (None,) * 7]
    assert _tabla(hoja) == [(1, "1.1", None, "99000401", 3), (1, "1.1", None, "99000402", 4),
                            (1, "1.1", None, "99000403", 2), (1, "1.1", None, "99000404", None)]


def test_br_r17_02_un_plan_con_pi_de_dos_so_nombra_los_dos(
    base_410: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_410
    hoja = _libro(_generar(base, ids["dos_so"], tmp_path))[HOJA]
    assert hoja["B15"].value == "Student Outcome (SO) 2 y 7"
    assert [hoja[f"B{fila}"].value for fila in (17, 18, 19)] == ["2.1", "2.2", "7.1"]
    assert [(so, pi) for so, pi, *_ in _tabla(hoja)] == [
        (2, "2.1"), (2, "2.1"), (2, "2.2"), (2, "2.2"), (7, "7.1"), (7, "7.1")]


# BR-R17-03: denominador de calificados.

def test_br_r17_03_la_cifra_entre_parentesis_usa_los_calificados(r17_correcto: Path) -> None:
    assert [fila[5] for fila in _niveles(_libro(r17_correcto)[HOJA])] == ["7 de 11", "7 de 11", "8 de 11"]


def test_br_r17_03_una_medicion_sin_evidencia_sale_del_denominador_y_no_del_total(
    base_mutada: tuple[Any, int], tmp_path: Path,
) -> None:
    base, carga_id = base_mutada
    hoja = _libro(_generar(base, carga_id, tmp_path))[HOJA]
    # 5.2 sin la evidencia de 99000002: 6 de 10 calificados (60,0 %) y 6 de 11 sobre el total (54,5 %).
    assert hoja["E25"].value == pytest.approx(0.6)
    assert _niveles(hoja)[1] == ("5.2", 1, 3, 3, 3, "6 de 10", pytest.approx(0.545))
    sin_evidencia = [fila for fila in _tabla(hoja) if fila[1] == "5.2" and fila[3] == "99000002"]
    assert sin_evidencia == [(5, "5.2", None, "99000002", None)]


# BR-R17-04: valores sin fórmulas en las filas fijas de la plantilla, con el logotipo.

def test_br_r17_04_ninguna_celda_trae_formulas_ni_ref_y_los_recuadros_quedan_vacios(r17_correcto: Path) -> None:
    libro = _libro(r17_correcto)
    celdas = [celda for hoja in libro.worksheets for fila in hoja.iter_rows() for celda in fila]
    assert not [celda.coordinate for celda in celdas if celda.data_type == "f"]
    assert not [texto for texto in _textos(libro) if texto.startswith("=") or "#REF!" in texto]
    assert not [nombre for nombre, datos in _partes(r17_correcto).items() if b"<f>" in datos or b"#REF!" in datos]
    hoja = libro[HOJA]
    for rango in ("B29:I31", "B34:I36"):
        assert all(celda.value is None for fila in hoja[rango] for celda in fila), rango


def test_br_r17_04_el_porcentaje_del_bloque_ii_no_queda_sobre_un_relleno_automatico(r17_correcto: Path) -> None:
    # Tres estilos de los formatos condicionales perdieron patternType="none" al vaciar la plantilla, y un
    # relleno sin patrón con el color automático se ve negro bajo la fuente roja cuando la celda tiene valor.
    reglas = {regla.priority: regla for formato in _libro(r17_correcto)[HOJA].conditional_formatting
              for regla in formato.rules}
    assert sorted(reglas) == [1, 2, 3, 4, 5, 6, 7]
    # Color guarda un solo tipo, así que el color automático se reconoce por type y no por auto.
    automaticos = [prioridad for prioridad, regla in reglas.items()
                   if regla.dxf is not None and regla.dxf.fill is not None
                   and regla.dxf.fill.patternType is None and regla.dxf.fill.bgColor.type == "auto"]
    assert automaticos == []
    # La regla de prioridad 3, «menor que 0,8», conserva su fuente roja en negrita sobre blanco, como la hoja
    # original.
    assert (reglas[3].dxf.font.b, reglas[3].dxf.font.color.rgb, reglas[3].dxf.fill.bgColor.rgb) == (
        True, "FF9C0006", "FFFFFFFF")


def test_br_r17_02_cada_encabezado_de_la_tabla_de_niveles_cabe_en_su_columna(r17_correcto: Path) -> None:
    hoja = _libro(r17_correcto)[HOJA]
    for columna in "KLMNOPQ":
        encabezado = hoja[f"{columna}28"].value
        assert (hoja.column_dimensions[columna].width or 8.43) >= len(encabezado) + 1, columna


def test_br_r17_09_la_hoja_constancia_se_imprime_en_el_ancho_de_una_pagina(r17_correcto: Path) -> None:
    hoja = _libro(r17_correcto)["Constancia"]
    assert hoja.sheet_properties.pageSetUpPr.fitToPage
    assert (hoja.page_setup.fitToWidth, hoja.page_setup.fitToHeight) == (1, 0)
    # El título, el autor y la frase final ocupan las dos columnas para no cortarse en la impresión.
    fusionadas = {str(rango) for rango in hoja.merged_cells.ranges}
    autor = next(c.row for fila in hoja.iter_rows() for c in fila if str(c.value or "").startswith("Subido por"))
    assert {"A1:B1", f"A{autor}:B{autor}", f"A{hoja.max_row}:B{hoja.max_row}"} <= fusionadas


def test_br_r17_04_el_libro_conserva_el_logotipo_de_la_plantilla(r17_correcto: Path) -> None:
    libro = _libro(r17_correcto)
    imagenes = libro[HOJA]._images
    assert len(imagenes) == 1 and not libro["Constancia"]._images
    assert imagenes[0]._data() == LOGOTIPO.read_bytes()
    ancla = imagenes[0].anchor
    assert (ancla._from.col, ancla._from.colOff, ancla._from.row, ancla._from.rowOff) == (1, 19050, 0, 0)
    assert (ancla.to.col, ancla.to.colOff, ancla.to.row, ancla.to.rowOff) == (1, 744818, 3, 140297)
    medios = [datos for nombre, datos in _partes(r17_correcto).items() if nombre.startswith("xl/media/")]
    assert medios == [LOGOTIPO.read_bytes()]


def test_br_r17_04_pillow_esta_instalado_y_openpyxl_lo_ve() -> None:
    import PIL

    assert PIL.__version__ and openpyxl.drawing.image.PILImage


def test_br_r17_04_sin_pillow_no_sale_un_r17_sin_logotipo(
    base_410: tuple[Any, dict[str, int]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    base, ids = base_410
    # Así se ve openpyxl en un entorno sin Pillow, que descarta las imágenes sin aviso.
    monkeypatch.setattr(openpyxl.drawing.image, "PILImage", False)
    with pytest.raises(ImportError):
        _generar(base, ids["correcta"], tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_br_r17_04_un_texto_de_la_peticion_que_empieza_por_igual_queda_como_texto(
    base_410: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_410
    ruta = _generar(base, ids["hostil"], tmp_path)
    archivo = next(celda for fila in _libro(ruta)["Constancia"].iter_rows() for celda in fila
                   if isinstance(celda.value, str) and celda.value.startswith("=1+1"))
    assert archivo.value == "=1+1\ufffd.xlsx" and archivo.data_type == "s"
    # Con el prefijo de comillas, Excel lo sigue mostrando como texto aunque alguien edite la celda.
    assert archivo.quotePrefix
    assert not [nombre for nombre, datos in _partes(ruta).items() if b"<f>" in datos]


# BR-R17-05: franja PROVISIONAL si y solo si la vista lo dice.

def test_br_r17_05_con_reglas_en_borrador_el_r17_lleva_la_franja_el_sufijo_y_el_titulo(
    r17_correcto: Path, base_410: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_410
    assert {fila[7] for fila in _vista(base, ids["correcta"])} == {True}
    libro = _libro(r17_correcto)
    hoja = libro[HOJA]
    assert hoja["B7"].value == FRANJA_BORRADOR
    assert "B7:I7" in {str(rango) for rango in hoja.merged_cells.ranges}
    assert r17_correcto.name.endswith("_PROVISIONAL.xlsx")
    assert "PROVISIONAL" in (libro.properties.title or "")


def test_br_r17_05_con_reglas_aprobadas_ninguna_hoja_lleva_la_franja(
    base_aprobada: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_aprobada
    assert [(fila[0], fila[1], fila[2], fila[7]) for fila in _vista(base, ids["aprobada"])] == [
        (pi, Decimal("90.9"), Decimal("70.0"), False) for pi in PIS_410]
    ruta = _generar(base, ids["aprobada"], tmp_path)
    libro = _libro(ruta)
    hoja = libro[HOJA]
    assert not [texto for texto in _textos(libro) if "PROVISIONAL" in texto.upper()]
    assert hoja["B7"].value is None and not [r for r in hoja.merged_cells.ranges if r.min_row == 7]
    assert "PROVISIONAL" not in (libro.properties.title or "").upper()
    assert [hoja[f"E{fila}"].value for fila in (24, 25, 26)] == pytest.approx([0.909] * 3)
    assert [hoja[f"G{fila}"].value for fila in (24, 25, 26)] == pytest.approx([0.7] * 3)
    assert [fila[5] for fila in _niveles(hoja)] == ["10 de 11"] * 3
    assert [hoja[f"H{fila}"].value for fila in (24, 25, 26)] == [LOGRADO] * 3


def test_br_r17_05_un_conjunto_aprobado_al_que_le_falta_un_parametro_sigue_provisional(
    base_aprobada: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_aprobada
    ruta = _generar(base, ids["incompleta"], tmp_path)
    franja = _libro(ruta)[HOJA]["B7"].value
    assert "PROVISIONAL" in franja and "R-PRUEBA-INCOMPLETO" in franja
    # El conjunto está aprobado, así que la franja no dice que sus reglas esperan la aprobación.
    assert "aún no están aprobadas" not in franja
    assert ruta.name == "R017_450002_411_2026-2_PROVISIONAL.xlsx"


# BR-R17-06: nombre del archivo.

def test_br_r17_06_el_nombre_lleva_asignatura_seccion_periodo_y_el_sufijo_provisional(r17_correcto: Path) -> None:
    assert r17_correcto.name == "R017_450002_410_2026-2_PROVISIONAL.xlsx"
    assert r17_correcto.parent.name.startswith("r17_correcto")


def test_br_r17_06_sin_franja_el_nombre_no_lleva_el_sufijo_ni_personas(
    base_aprobada: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_aprobada
    ruta = _generar(base, ids["aprobada"], tmp_path)
    assert ruta.name == "R017_450002_410_2026-2.xlsx"
    assert "@" not in ruta.name and "docente" not in ruta.name.lower()


# BR-R17-07: libro sin personas.

def test_br_r17_07_el_autor_y_el_ultimo_autor_dicen_abet_sis_med(r17_correcto: Path) -> None:
    propiedades = _libro(r17_correcto).properties
    assert (propiedades.creator, propiedades.lastModifiedBy) == ("ABET_SIS_MED", "ABET_SIS_MED")
    # La creación es la de la generación y no la fecha fija de la plantilla, el 2026-10-28 a las 00:00.
    assert datetime(2026, 10, 28) < propiedades.created <= propiedades.modified
    for parte in ("docProps/core.xml", "docProps/app.xml"):
        assert b"@" not in _partes(r17_correcto)[parte] and b"docente" not in _partes(r17_correcto)[parte]


def test_br_r17_07_el_correo_de_quien_sube_va_solo_en_la_hoja_constancia(r17_correcto: Path) -> None:
    libro = _libro(r17_correcto)
    correo = "docente410@example.invalid"
    en_constancia = [str(c.value) for fila in libro["Constancia"].iter_rows() for c in fila
                     if correo in str(c.value or "")]
    assert en_constancia == [f"Subido por {correo}"]
    assert not [c for fila in libro[HOJA].iter_rows() for c in fila if "@" in str(c.value or "")]
    hoja = libro[HOJA]
    assert hoja["D10"].value is None and all(hoja[f"D{fila}"].value is None for fila in FILAS_DE_LA_TABLA)
    # Ni la hoja del reporte ni las propiedades ni otra parte del zip, salvo la hoja «Constancia» (sheet2.xml).
    fuera_de_la_constancia = b"".join(datos for nombre, datos in _partes(r17_correcto).items()
                                      if nombre != "xl/worksheets/sheet2.xml")
    assert correo.encode() not in fuera_de_la_constancia


def test_br_r17_07_ninguna_hoja_trae_nombres_del_export(r17_con_error: Path) -> None:
    export = openpyxl.load_workbook(EXPORT_CON_ERROR, read_only=True)
    filas = list(export.worksheets[0].iter_rows(values_only=True))
    export.close()
    columnas = [filas[0].index("Last Name"), filas[0].index("First Name")]
    nombres = {str(fila[i]) for fila in filas[1:] for i in columnas if fila[i]}
    assert nombres, "el export inventado trae nombres para comparar"
    textos = _textos(_libro(r17_con_error))
    assert not [nombre for nombre in nombres for texto in textos if nombre in texto]


# BR-R17-08: tabla de estudiantes y tope de 142 filas.

def test_br_r17_08_la_tabla_trae_una_fila_por_medicion_por_pi_y_fila_de_origen(r17_correcto: Path) -> None:
    hoja = _libro(r17_correcto)[HOJA]
    assert _tabla(hoja) == _tabla_esperada()
    assert all(hoja.cell(fila, 2).value is not None for fila in range(43, 76))
    assert all(hoja.cell(fila, columna).value is None for fila in range(76, 185) for columna in range(2, 7))
    assert hoja.tables["Tabla26"].ref == "B42:F184"


def test_br_r17_08_con_el_export_con_error_la_tabla_trae_30_filas_sin_99000002(r17_con_error: Path) -> None:
    tabla = _tabla(_libro(r17_con_error)[HOJA])
    assert len(tabla) == 30 and tabla == _tabla_esperada(sin="99000002")


def test_br_r17_08_la_tabla_trae_las_mismas_filas_de_v_tabla_maestra_pi(
    r17_con_error: Path, base_con_error: tuple[Any, dict[str, int]],
) -> None:
    base, _ids = base_con_error
    maestra = _consulta(
        base,
        'SELECT "SO", "PI", "PROFESOR", "CÓDIGO DEL ESTUDIANTE", "CALIFICACIÓN" FROM abet.v_tabla_maestra_pi '
        'WHERE "CÓDIGO DEL CURSO" = %s AND "SECCIÓN" = %s',
        ("450002", "410"),
    )
    assert Counter(_tabla(_libro(r17_con_error)[HOJA])) == Counter(maestra)


def test_br_r17_08_142_mediciones_llenan_la_tabla_hasta_la_fila_184(
    base_410: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_410
    hoja = _libro(_generar(base, ids["142"], tmp_path))[HOJA]
    assert len(_tabla(hoja)) == 142
    assert (hoja["E43"].value, hoja["E184"].value) == ("99000501", "99000642")
    assert hoja.tables["Tabla26"].ref == "B42:F184" and hoja["E185"].value is None


def test_br_r17_08_143_mediciones_no_caben_y_el_r17_no_se_trunca(
    base_410: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_410
    with pytest.raises(r17.SeccionSuperaPlantilla) as error:
        _generar(base, ids["143"], tmp_path)
    assert (error.value.mensaje, error.value.codigo_http) == (
        "La sección supera las filas de la plantilla del R-17.", 422)
    assert list(tmp_path.iterdir()) == []


def test_br_r17_08_un_plan_de_mas_de_3_pi_no_cabe_en_las_filas_fijas_y_no_se_trunca(
    base_410: tuple[Any, dict[str, int]], tmp_path: Path,
) -> None:
    base, ids = base_410
    with pytest.raises(r17.SeccionSuperaPlantilla):
        _generar(base, ids["cuatro_pi"], tmp_path)
    assert list(tmp_path.iterdir()) == []


# BR-R17-09: hoja «Constancia».

def test_br_r17_09_la_hoja_constancia_muestra_la_carga_el_archivo_y_sus_cifras(
    r17_correcto: Path, base_410: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_410
    libro = _libro(r17_correcto)
    assert libro.sheetnames[-1] == "Constancia"
    hoja = libro["Constancia"]
    pares = _pares(hoja)
    assert pares["Carga"] == ids["correcta"] == _vista(base, ids["correcta"])[0][8]
    assert pares["Archivo"] == "sintetico_20262_450002_410.xlsx"
    assert pares["Hoja"] == "gc_SINTETICO_20262_450002_410_f"
    assert pares["Filas de datos / leídas / aceptadas / rechazadas"] == "11 / 11 / 11 / 0"
    assert pares["Huella SHA-256"] == HUELLA_CORRECTO
    assert (pares["Estado"], pares["Versión del programa"]) == ("PUBLICADA", "v0.0.0-prueba")
    assert pares["Conjunto de reglas"] == "R-2026-BORRADOR (BORRADOR)"
    assert pares["Parámetros pendientes"] == "TRATO_SIN_EVIDENCIA, CORTE_ROJO y CONVERSION_NIVEL_0_1"
    avisos_y_rechazos = (pares["Avisos"], pares["PUNTAJE_MAXIMO_DISTINTO en el PI 5.3"], pares["Rechazos de fila"])
    assert avisos_y_rechazos == (1, AVISO_5_3, 0)
    textos = [str(c.value) for fila in hoja.iter_rows() for c in fila if c.value is not None]
    assert "Subido por docente410@example.invalid" in textos and textos[-1] == FRASE_FINAL
    iniciada, terminada = _consulta(base, "SELECT iniciada_en, terminada_en FROM abet.carga WHERE carga_id = %s",
                                    (ids["correcta"],))[0]
    inicio, fin = (datetime.fromisoformat(pares[r]) for r in ("Inicio (hora de Lima)", "Fin (hora de Lima)"))
    assert (inicio, fin) == (iniciada, terminada) and fin > inicio
    assert pares["Inicio (hora de Lima)"].endswith("-05:00")


def test_br_r17_09_con_el_export_con_error_la_constancia_trae_el_rechazo_de_la_fila_3(r17_con_error: Path) -> None:
    pares = _pares(_libro(r17_con_error)["Constancia"])
    assert pares["Archivo"] == "export_inventado_410_con_error.xlsx" and pares["Huella SHA-256"] == HUELLA_CON_ERROR
    assert pares["Filas de datos / leídas / aceptadas / rechazadas"] == "11 / 11 / 10 / 1"
    assert pares["Rechazos de fila"] == 1
    assert pares["Fila 3, PI 5.2, NIVEL_FUERA_DE_ESCALA, RECHAZA_FILA"] == (
        "Fila 3, PI 5.2, nivel fuera de la escala 1 a 4. La fila completa queda fuera, también de 5.1 y 5.3.")
    assert pares["PUNTAJE_MAXIMO_DISTINTO en el PI 5.3"] == AVISO_5_3


def test_br_r17_09_la_fila_del_rechazo_no_muestra_el_valor_leido(r17_con_error: Path) -> None:
    hoja = _libro(r17_con_error)["Constancia"]
    fila = next(f for f in hoja.iter_rows() if f[0].value == "Fila 3, PI 5.2, NIVEL_FUERA_DE_ESCALA, RECHAZA_FILA")
    ocupadas = [celda.value for celda in fila if celda.value is not None]
    assert len(ocupadas) == 2
    # El 5 leído en la celda no aparece suelto, solo dentro de los códigos de PI y de la escala 1 a 4.
    assert not [texto for texto in ocupadas if re.search(r"(?<![\d.])5(?![\d.])", str(texto))]


def test_br_r17_09_la_hoja_constancia_dice_lo_mismo_que_la_constancia_en_json(
    r17_con_error: Path, base_con_error: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_con_error
    with psycopg.connect(base.conexion_app) as conexion:
        cuerpo = constancia.armar(conexion, ids["con_error"])
    pares = _pares(_libro(r17_con_error)["Constancia"])
    assert (pares["Carga"], pares["Archivo"], pares["Hoja"], pares["Huella SHA-256"], pares["Estado"]) == (
        cuerpo["carga_id"], cuerpo["nombre_archivo"], cuerpo["hoja"], cuerpo["sha256"], cuerpo["estado"])
    cuentas = " / ".join(str(cuerpo[c])
                         for c in ("filas_de_datos", "filas_leidas", "filas_aceptadas", "filas_rechazadas"))
    assert pares["Filas de datos / leídas / aceptadas / rechazadas"] == cuentas
    assert (pares["Inicio (hora de Lima)"], pares["Fin (hora de Lima)"]) == (
        cuerpo["iniciada_en"], cuerpo["terminada_en"])
    assert pares["Conjunto de reglas"] == f"{cuerpo['conjunto_reglas']} ({cuerpo['conjunto_reglas_estado']})"
    mensajes = {mensaje for clave, mensaje in pares.items()
                if isinstance(clave, str) and clave.startswith(("Fila ", "PUNTAJE"))}
    assert mensajes == {elemento["mensaje"] for elemento in cuerpo["rechazos"] + cuerpo["avisos"]}
