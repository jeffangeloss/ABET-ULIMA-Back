"""Pruebas de la constancia de una carga en JavaScript Object Notation (JSON), BR-R17-10 (T035).

constancia.armar() lee la constancia de la base con el rol de la aplicación, igual que la ruta
GET /api/cargas/{carga_id}. Las bases son desechables (tests/base_desechable.py) y parten de
db/pruebas/datos_sinteticos.sql, con las cargas que arma tests/cargas_de_prueba.py, porque la carga
real (T033) se escribe en otra etapa. Cada regla de negocio (business rule, BR) tiene pruebas de lo
que debe pasar y de lo que no debe pasar (AGENTS.md, regla 8), y los valores esperados son literales
del contrato, de los escenarios o de la cuenta a mano. Los indicadores de desempeño (performance
indicators, PI) se nombran por su código.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
import pytest

from abet_carga import constancia
from abet_carga.modelos import Motivo


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
CAMPOS = {
    "carga_id", "estado", "seccion", "nombre_archivo", "hoja", "sha256", "filas_de_datos", "filas_leidas",
    "filas_aceptadas", "filas_rechazadas", "mensaje", "columnas", "rechazos", "avisos", "conjunto_reglas",
    "conjunto_reglas_estado", "parametros_pendientes", "provisional", "programa_version", "subida_por",
    "iniciada_en", "terminada_en",
}
# Huellas de shasum -a 256 sobre los archivos de tests/datos_inventados/.
HUELLA_CORRECTO = "c92c5056de54d0bb3500ce84bf3f991027741f32ec0e0432dc697ecabee5578f"
HUELLA_CON_ERROR = "2b94db8d8abfd5ff24425584172de7942383c480f25ee0a8cacf927e17df2d15"
AVISO_5_3 = {
    "pi": "5.3", "motivo": "PUNTAJE_MAXIMO_DISTINTO", "efecto": "AVISO",
    "mensaje": "PI 5.3. La columna declara 20 puntos y sus notas están entre 1 y 4. Se cargó igual.",
}
COLUMNAS_410 = [
    {"pi": "5.1", "puntaje_maximo_declarado": 4},
    {"pi": "5.2", "puntaje_maximo_declarado": 4},
    {"pi": "5.3", "puntaje_maximo_declarado": 20},
]
HORA_ISO_DE_LIMA = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?-05:00")


def _armar(base: Any, carga_id: int) -> dict[str, Any]:
    with psycopg.connect(base.conexion_app) as conexion:
        return constancia.armar(conexion, carga_id)


def _fila_de_la_base(base: Any, consulta: str, carga_id: int) -> tuple[Any, ...]:
    with psycopg.connect(base.conexion) as conexion:
        fila = conexion.execute(consulta, (carga_id,)).fetchone()
    assert fila is not None
    return fila


def _claves(valor: object) -> set[str]:
    """Todas las claves de un cuerpo JSON, en cualquier nivel."""
    if isinstance(valor, dict):
        return set(valor) | {clave for hijo in valor.values() for clave in _claves(hijo)}
    if isinstance(valor, list):
        return {clave for hijo in valor for clave in _claves(hijo)}
    return set()


@pytest.fixture(scope="module")
def base_410(base_desechable: ModuleType) -> Iterator[tuple[Any, dict[str, int]]]:
    """Base con la 410 de los datos sintéticos publicada y una carga de cada motivo en otras cargas."""
    with base_desechable.abierta(datos_2026_2=False, despues=[CARGAS.SINTETICOS, base_desechable.DATOS_2026_2]) as base:
        with psycopg.connect(base.conexion) as conexion:
            ids = _cargas_de_la_410(conexion)
        yield base, ids


def _cargas_de_la_410(conexion: psycopg.Connection) -> dict[str, int]:
    ids = {"correcta": CARGAS.preparar_410(conexion)}
    rechazar = CARGAS.rechazar
    ids["sin_5_2"] = rechazar(conexion, motivo="PI_DEL_PLAN_AUSENTE", pi="5.2", nombre_archivo="sin_5_2_410.xlsx")
    ids["5_1_repetido"] = rechazar(conexion, motivo="PI_REPETIDO", pi="5.1", nombre_archivo="dos_5_1_410.xlsx")
    ids["de_la_411"] = rechazar(conexion, motivo="SECCION_NO_COINCIDE", nombre_archivo="export_inventado_411.xlsx",
                                hoja="gc_SINTETICO_20262_450002_411_f")
    ids["de_450010"] = rechazar(conexion, motivo="SECCION_NO_COINCIDE", nombre_archivo="curso_450010.xlsx",
                                hoja="gc_SINTETICO_20262_450010_410_f")
    ids["411_por_nombre"] = rechazar(conexion, motivo="SECCION_NO_COINCIDE", hoja="Hoja1",
                                     nombre_archivo="gc_SINTETICO_20262_450002_411_fullgc_2026-10-20.xlsx")
    ids["de_20261"] = rechazar(conexion, motivo="PERIODO_NO_COINCIDE", nombre_archivo="periodo_20261.xlsx",
                               hoja="gc_SINTETICO_20261_450002_410_f")
    ids["vacio"] = rechazar(conexion, motivo="ARCHIVO_SIN_FILAS", nombre_archivo="vacio_410.xlsx", filas_de_datos=0)
    ids["sin_codigo"] = rechazar(conexion, motivo="COLUMNA_CODIGO_AUSENTE",
                                 nombre_archivo="sin_username_ni_student_id_410.xlsx")
    ids["todas_rechazadas"] = CARGAS.publicar(
        conexion, asignatura="450002", numero="410", pis=["5.1", "5.2", "5.3"], filas=[],
        nombre_archivo="todo_cinco_410.xlsx", hoja=CARGAS.HOJA_410, estado="RECHAZADA",
        rechazos_de_fila=[(fila, "5.2", "NIVEL_FUERA_DE_ESCALA") for fila in range(2, 13)],
    )
    ids["por_codigo"] = CARGAS.publicar(
        conexion, asignatura="450002", numero="411", pis=["5.1", "5.2", "5.3"],
        filas=[CARGAS.Fila(fila, f"990001{fila:02d}", (3, 3, 3)) for fila in (2, 6, 7, 8, 9, 10, 11)],
        nombre_archivo="export_411_con_codigos.xlsx", hoja="gc_SINTETICO_20262_450002_411_f",
        rechazos_de_fila=[(12, None, "CODIGO_DUPLICADO"), (3, None, "CODIGO_VACIO"), (5, "5.1", "NIVEL_NO_NUMERICO"),
                          (4, None, "CODIGO_INVALIDO")],
        avisos=[(None, "COLUMNA_PI_FUERA_DEL_PLAN"), ("5.3", "PUNTAJE_MAXIMO_DISTINTO"),
                ("5.2", "PUNTAJE_MAXIMO_DISTINTO")],
        puntajes={"5.2": 4.5, "5.3": None},
    )
    ids["sin_autor"] = CARGAS.publicar(
        conexion, asignatura="450002", numero="412", pis=["5.1", "5.2", "5.3"],
        filas=CARGAS.filas_inventadas(2, desde=99000301, niveles=(4, 4, 4)), nombre_archivo="notas.xlsx",
        hoja="Hoja1", subida_por=None, avisos=[(None, "SECCION_SIN_DECLARAR")],
    )
    CARGAS.conjunto_aprobado(conexion)
    CARGAS.conjunto_aprobado(conexion, "R-PRUEBA-INCOMPLETO", completo=False)
    CARGAS.conjunto_aprobado(conexion, "R-PRUEBA-BORRADOR-COMPLETO", aprobado=False)
    ids["aprobada"] = rechazar(conexion, motivo="PI_DEL_PLAN_AUSENTE", pi="5.3", nombre_archivo="sin_5_3_a.xlsx",
                               conjunto=CARGAS.APROBADO)
    ids["incompleta"] = rechazar(conexion, motivo="PI_DEL_PLAN_AUSENTE", pi="5.3", nombre_archivo="sin_5_3_i.xlsx",
                                 conjunto="R-PRUEBA-INCOMPLETO")
    ids["borrador_completo"] = rechazar(conexion, motivo="PI_DEL_PLAN_AUSENTE", pi="5.3",
                                        nombre_archivo="sin_5_3_b.xlsx", conjunto="R-PRUEBA-BORRADOR-COMPLETO")
    # Una carga anterior a la lectura de la hoja deja archivo_origen.hoja nulo, y la sección sale del nombre.
    ids["412_sin_hoja"] = rechazar(conexion, motivo="SECCION_NO_COINCIDE", hoja=None,
                                   nombre_archivo="gc_SINTETICO_20262_450002_412_fullgc_2026-10-21.xlsx")
    return ids


@pytest.fixture(scope="module")
def base_con_error(base_desechable: ModuleType) -> Iterator[tuple[Any, int]]:
    """Base de los datos sintéticos con la 410 reemplazada por la carga del export con el 5 en la fila 3."""
    with base_desechable.abierta(datos_2026_2=False, despues=[CARGAS.SINTETICOS, base_desechable.DATOS_2026_2]) as base:
        with psycopg.connect(base.conexion) as conexion:
            carga_id = CARGAS.con_error(conexion, CARGAS.preparar_410(conexion))
        yield base, carga_id


# BR-R17-10. Lo que debe pasar.

def test_br_r17_10_la_constancia_de_la_carga_publicada_trae_el_cuerpo_plano_del_contrato(
    base_410: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_410
    cuerpo = _armar(base, ids["correcta"])
    seccion_id = _fila_de_la_base(base, "SELECT seccion_id FROM abet.carga WHERE carga_id = %s", ids["correcta"])[0]
    assert set(cuerpo) == CAMPOS
    assert {clave: cuerpo[clave] for clave in CAMPOS - {"iniciada_en", "terminada_en"}} == {
        "carga_id": ids["correcta"],
        "estado": "PUBLICADA",
        "seccion": {"seccion_id": seccion_id, "asignatura": "450002", "numero": "410", "periodo": "2026-2"},
        "nombre_archivo": "sintetico_20262_450002_410.xlsx",
        "hoja": "gc_SINTETICO_20262_450002_410_f",
        "sha256": HUELLA_CORRECTO,
        "filas_de_datos": 11,
        "filas_leidas": 11,
        "filas_aceptadas": 11,
        "filas_rechazadas": 0,
        "mensaje": None,
        "columnas": COLUMNAS_410,
        "rechazos": [],
        "avisos": [AVISO_5_3],
        "conjunto_reglas": "R-2026-BORRADOR",
        "conjunto_reglas_estado": "BORRADOR",
        "parametros_pendientes": ["TRATO_SIN_EVIDENCIA", "CORTE_ROJO", "CONVERSION_NIVEL_0_1"],
        "provisional": True,
        "programa_version": "v0.0.0-prueba",
        "subida_por": "docente410@example.invalid",
    }
    # Un puntaje sin decimales viaja como entero, como en el ejemplo del contrato, y no como 4.0.
    assert json.dumps(cuerpo["columnas"]) == (
        '[{"pi": "5.1", "puntaje_maximo_declarado": 4}, {"pi": "5.2", "puntaje_maximo_declarado": 4}, '
        '{"pi": "5.3", "puntaje_maximo_declarado": 20}]')


def test_br_r17_10_la_constancia_del_export_con_error_trae_el_rechazo_de_la_fila_3_y_el_aviso(
    base_con_error: tuple[Any, int],
) -> None:
    base, carga_id = base_con_error
    cuerpo = _armar(base, carga_id)
    assert (cuerpo["estado"], cuerpo["nombre_archivo"], cuerpo["hoja"], cuerpo["sha256"]) == (
        "PUBLICADA", "export_inventado_410_con_error.xlsx", "gc_SINTETICO_20262_450002_410_f", HUELLA_CON_ERROR)
    assert [cuerpo[clave] for clave in ("filas_de_datos", "filas_leidas", "filas_aceptadas", "filas_rechazadas")] == [
        11, 11, 10, 1]
    assert cuerpo["rechazos"] == [{
        "fila": 3, "pi": "5.2", "motivo": "NIVEL_FUERA_DE_ESCALA", "efecto": "RECHAZA_FILA",
        "mensaje": ("Fila 3, PI 5.2, nivel fuera de la escala 1 a 4. "
                    "La fila completa queda fuera, también de 5.1 y 5.3."),
    }]
    assert cuerpo["avisos"] == [AVISO_5_3]
    assert cuerpo["columnas"] == COLUMNAS_410
    assert cuerpo["mensaje"] is None


def test_br_r17_10_las_horas_viajan_con_el_desfase_de_lima_e_iguales_a_las_de_la_carga(
    base_410: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_410
    cuerpo = _armar(base, ids["correcta"])
    iniciada, terminada = _fila_de_la_base(
        base, "SELECT iniciada_en, terminada_en FROM abet.carga WHERE carga_id = %s", ids["correcta"])
    assert HORA_ISO_DE_LIMA.fullmatch(cuerpo["iniciada_en"]), cuerpo["iniciada_en"]
    assert HORA_ISO_DE_LIMA.fullmatch(cuerpo["terminada_en"]), cuerpo["terminada_en"]
    assert datetime.fromisoformat(cuerpo["iniciada_en"]) == iniciada
    assert datetime.fromisoformat(cuerpo["terminada_en"]) == terminada
    assert datetime.fromisoformat(cuerpo["terminada_en"]) > datetime.fromisoformat(cuerpo["iniciada_en"])


def test_br_r17_10_la_constancia_se_serializa_en_json_y_sale_igual_en_cada_lectura(
    base_410: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_410
    for carga_id in ids.values():
        cuerpo = _armar(base, carga_id)
        assert set(cuerpo) == CAMPOS and cuerpo["carga_id"] == carga_id
        assert json.loads(json.dumps(cuerpo, ensure_ascii=False)) == cuerpo
        assert _armar(base, carga_id) == cuerpo


def test_br_r17_10_una_carga_rechazada_tambien_tiene_constancia_con_el_pi_que_falta(
    base_410: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_410
    cuerpo = _armar(base, ids["sin_5_2"])
    mensaje = "Falta la columna del PI 5.2 que el plan de medición pide para esta sección."
    assert set(cuerpo) == CAMPOS
    assert cuerpo["estado"] == "RECHAZADA"
    assert [cuerpo[clave] for clave in ("filas_de_datos", "filas_leidas", "filas_aceptadas", "filas_rechazadas")] == [
        11, 0, 0, 0]
    assert cuerpo["rechazos"] == [
        {"fila": None, "pi": "5.2", "motivo": "PI_DEL_PLAN_AUSENTE", "efecto": "RECHAZA_CARGA", "mensaje": mensaje}]
    assert cuerpo["mensaje"] == mensaje
    assert cuerpo["sha256"] == CARGAS.huella_de("sin_5_2_410.xlsx")
    assert (cuerpo["columnas"], cuerpo["avisos"], cuerpo["subida_por"]) == ([], [], "docente410@example.invalid")
    assert cuerpo["provisional"] is True


@pytest.mark.parametrize(
    ("carga", "pi", "mensaje"),
    [
        ("5_1_repetido", "5.1", "El PI 5.1 aparece en dos columnas del archivo."),
        ("de_la_411", None, "El archivo corresponde a la sección 411 y usted eligió la 410. No se publicó."),
        ("de_450010", None, "El archivo corresponde a la asignatura 450010 y usted eligió la 450002. No se publicó."),
        ("411_por_nombre", None, "El archivo corresponde a la sección 411 y usted eligió la 410. No se publicó."),
        ("412_sin_hoja", None, "El archivo corresponde a la sección 412 y usted eligió la 410. No se publicó."),
        ("de_20261", None,
         "El archivo corresponde al periodo 2026-1 y la sección elegida es de 2026-2. No se publicó."),
        ("vacio", None, "El archivo no trae filas de estudiantes."),
        ("sin_codigo", None, "El archivo no tiene la columna Username ni Student ID."),
    ],
)
def test_br_r17_10_cada_rechazo_de_carga_trae_su_pi_y_el_mensaje_de_la_respuesta_201(
    base_410: tuple[Any, dict[str, int]], carga: str, pi: str | None, mensaje: str,
) -> None:
    base, ids = base_410
    cuerpo = _armar(base, ids[carga])
    assert cuerpo["estado"] == "RECHAZADA"
    assert cuerpo["mensaje"] == mensaje
    assert [(r["fila"], r["pi"], r["efecto"], r["mensaje"]) for r in cuerpo["rechazos"]] == [
        (None, pi, "RECHAZA_CARGA", mensaje)]


def test_br_r17_10_una_carga_sin_filas_aceptadas_resume_su_motivo_y_lista_cada_fila(
    base_410: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_410
    cuerpo = _armar(base, ids["todas_rechazadas"])
    assert cuerpo["estado"] == "RECHAZADA"
    assert cuerpo["mensaje"] == "Ninguna fila se pudo aceptar. La carga no se publicó."
    assert [(r["fila"], r["pi"], r["motivo"]) for r in cuerpo["rechazos"]] == [
        (fila, "5.2", "NIVEL_FUERA_DE_ESCALA") for fila in range(2, 13)]
    assert [cuerpo[clave] for clave in ("filas_leidas", "filas_aceptadas", "filas_rechazadas")] == [11, 0, 11]


def test_br_r17_10_el_provisional_de_una_carga_rechazada_sigue_la_regla_de_la_vista(
    base_410: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_410
    aprobada, incompleta = _armar(base, ids["aprobada"]), _armar(base, ids["incompleta"])
    assert (aprobada["conjunto_reglas"], aprobada["conjunto_reglas_estado"]) == ("R-PRUEBA-APROBADO", "APROBADO")
    assert (aprobada["provisional"], aprobada["parametros_pendientes"]) == (False, [])
    # Aprobado, pero con TRATO_SIN_EVIDENCIA en PENDIENTE, sigue provisional, como en v_r17_por_pi.
    assert (incompleta["conjunto_reglas_estado"], incompleta["provisional"]) == ("APROBADO", True)
    assert incompleta["parametros_pendientes"] == ["TRATO_SIN_EVIDENCIA"]
    # Con sus parámetros DEFINIDOS y sin aprobar, también sigue provisional.
    borrador = _armar(base, ids["borrador_completo"])
    assert (borrador["conjunto_reglas_estado"], borrador["parametros_pendientes"], borrador["provisional"]) == (
        "BORRADOR", [], True)


def test_br_r17_10_el_provisional_de_una_carga_publicada_es_el_de_la_vista(
    base_410: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_410
    vista = _fila_de_la_base(
        base, "SELECT bool_and(provisional) FROM abet.v_r17_por_pi WHERE carga_id = %s", ids["correcta"])[0]
    assert _armar(base, ids["correcta"])["provisional"] is vista is True


# BR-R17-10. Lo que no debe pasar.

def test_br_r17_10_ningun_elemento_trae_el_valor_leido(
    base_410: tuple[Any, dict[str, int]], base_con_error: tuple[Any, int],
) -> None:
    base, ids = base_410
    cuerpos = [_armar(base, carga_id) for carga_id in ids.values()] + [_armar(*base_con_error)]
    for cuerpo in cuerpos:
        assert not _claves(cuerpo) & {"valor", "valor_leido"}
        for elemento in cuerpo["rechazos"] + cuerpo["avisos"]:
            assert set(elemento) <= {"fila", "pi", "motivo", "efecto", "mensaje"}


def test_br_r17_10_un_rechazo_por_codigo_no_trae_pi_y_ninguno_trae_el_codigo(
    base_410: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_410
    cuerpo = _armar(base, ids["por_codigo"])
    por_fila = {r["fila"]: r for r in cuerpo["rechazos"]}
    assert [r["fila"] for r in cuerpo["rechazos"]] == [3, 4, 5, 12]
    for fila, motivo in ((3, "CODIGO_VACIO"), (4, "CODIGO_INVALIDO"), (12, "CODIGO_DUPLICADO")):
        rechazo = por_fila[fila]
        assert (rechazo["pi"], rechazo["motivo"], rechazo["efecto"]) == (None, motivo, "RECHAZA_FILA")
        assert por_fila[fila]["mensaje"].startswith(f"Fila {fila}, ")
        assert por_fila[fila]["mensaje"].endswith("La fila completa queda fuera.")
        assert "PI" not in por_fila[fila]["mensaje"]
    assert por_fila[5]["pi"] == "5.1"
    assert por_fila[5]["mensaje"].startswith("Fila 5, PI 5.1, ")
    assert por_fila[5]["mensaje"].endswith("La fila completa queda fuera, también de 5.2 y 5.3.")
    for elemento in cuerpo["rechazos"] + cuerpo["avisos"]:
        assert not re.search(r"\d{8}", elemento["mensaje"])


def test_br_r17_10_un_aviso_sin_columna_en_la_carga_no_trae_pi_y_el_puntaje_va_como_numero(
    base_410: tuple[Any, dict[str, int]],
) -> None:
    base, ids = base_410
    cuerpo = _armar(base, ids["por_codigo"])
    assert cuerpo["columnas"] == [
        {"pi": "5.1", "puntaje_maximo_declarado": 4},
        {"pi": "5.2", "puntaje_maximo_declarado": 4.5},
        {"pi": "5.3", "puntaje_maximo_declarado": None},
    ]
    assert [(a["pi"], a["motivo"]) for a in cuerpo["avisos"]] == [
        ("5.2", "PUNTAJE_MAXIMO_DISTINTO"), ("5.3", "PUNTAJE_MAXIMO_DISTINTO"), (None, "COLUMNA_PI_FUERA_DEL_PLAN")]
    puntaje_5_2, puntaje_5_3, fuera = (a["mensaje"] for a in cuerpo["avisos"])
    assert puntaje_5_2 == "PI 5.2. La columna declara 4,5 puntos y sus notas están entre 1 y 4. Se cargó igual."
    # Un Total Pts que la base no guarda deja la columna sin puntaje, y el aviso no inventa la cifra.
    assert puntaje_5_3.startswith("PI 5.3. ") and not re.search(r"\d+ puntos", puntaje_5_3)
    assert "PI" in fuera and not re.search(r"\d\.\d", fuera)


def test_br_r17_10_una_carga_sin_autor_registrado_trae_subida_por_nulo(base_410: tuple[Any, dict[str, int]]) -> None:
    base, ids = base_410
    cuerpo = _armar(base, ids["sin_autor"])
    assert cuerpo["subida_por"] is None
    assert [(a["pi"], a["motivo"], a["efecto"]) for a in cuerpo["avisos"]] == [(None, "SECCION_SIN_DECLARAR", "AVISO")]
    assert cuerpo["mensaje"] is None and cuerpo["hoja"] == "Hoja1"


def test_br_r17_10_cada_motivo_de_la_lista_cerrada_tiene_su_mensaje(base_410: tuple[Any, dict[str, int]]) -> None:
    base, ids = base_410
    elementos = [e for carga_id in ids.values() for c in [_armar(base, carga_id)] for e in c["rechazos"] + c["avisos"]]
    assert {e["motivo"] for e in elementos} == {motivo.value for motivo in Motivo}
    assert all(e["mensaje"] and e["mensaje"].endswith(".") for e in elementos)


def test_br_r17_10_una_carga_que_no_existe_no_tiene_constancia(base_410: tuple[Any, dict[str, int]]) -> None:
    base, ids = base_410
    with pytest.raises(constancia.CargaInexistente) as error:
        _armar(base, max(ids.values()) + 1000)
    assert error.value.mensaje == "La carga no existe."
    assert error.value.codigo_http == 404
