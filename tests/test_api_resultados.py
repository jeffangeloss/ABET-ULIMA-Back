"""Pruebas de GET /api/resultados, la ruta 12 de la spec 004 (T032, T034 y T035).

Cada prueba nombra la regla de negocio (business rule, BR) de specs/features/resultados/resultados.spec.md que
comprueba, con lo que debe pasar y lo que no debe pasar (AGENTS.md, regla 8). Las cargas se siembran con publicar() de
tests/cargas_de_prueba.py y la conexión del dueño de una copia de la base desechable, como pide FR-019, así que ningún
export nuevo entra a tests/datos_inventados/. Los repartos por nivel son los de la tabla de cifras de
specs/004-reportes-docente/spec.md, y cada porcentaje esperado está calculado a mano desde ellos, con el redondeo a un
decimal de la vista.
"""

from __future__ import annotations

import importlib.util
import json
import statistics
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
import pytest
from psycopg import sql

from app import permisos
from app.rutas import resultados as ruta


def _modulo(nombre: str) -> ModuleType:
    """Módulo de tests/ cargado por su ruta, porque tests/ no es un paquete."""
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, Path(__file__).with_name(f"{nombre}.py"))
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


A = _modulo("api_de_prueba")
C = _modulo("cargas_de_prueba")
_GENERADOR = importlib.util.spec_from_file_location(
    "generar_exports_inventados", Path(__file__).resolve().parent.parent / "scripts" / "generar_exports_inventados.py")
G = sys.modules.get("generar_exports_inventados") or importlib.util.module_from_spec(_GENERADOR)
if "generar_exports_inventados" not in sys.modules:
    sys.modules["generar_exports_inventados"] = G
    _GENERADOR.loader.exec_module(G)
plantilla, base, api = A.plantilla, A.base, A.api

INSTRUMENTO = "Trabajo Integrador"
PENDIENTES_BORRADOR = ["TRATO_SIN_EVIDENCIA", "CORTE_ROJO", "CONVERSION_NIVEL_0_1"]
CLAVES = {"periodo", "so", "secciones"}
CLAVES_SO = {"numero", "descripcion"}
CLAVES_SECCION = {"seccion_id", "asignatura", "numero", "estado", "carga_id", "pi", "conjunto_reglas",
                  "conjunto_reglas_estado", "parametros_pendientes", "provisional", "indicadores"}
CLAVES_INDICADOR = {"so", "pi", "instrumento", "nivel_esperado", "estudiantes_por_nivel", "logrados", "calificados",
                    "sin_evidencia", "total", "pct_sobre_calificados", "pct_sobre_total", "meta_pct", "en_meta"}
VENCIDA = {"detail": "La sesión venció. Ingrese otra vez."}
# Repartos por nivel (niveles 1, 2, 3 y 4 y, si lo hay, un quinto valor con los estudiantes sin evidencia).
CORRECTO_410 = {"5.1": [1, 3, 4, 3], "5.2": [1, 3, 4, 3], "5.3": [1, 2, 5, 3]}
VARIAS = {
    ("450002", "412"): {"5.1": [1, 1, 5, 4], "5.2": [2, 3, 4, 2], "5.3": [0, 1, 4, 6]},
    ("450010", "410"): {"2.1": [1, 2, 4, 4], "2.2": [2, 4, 3, 2], "5.1": [3, 4, 3, 1]},
    ("450010", "412"): {"2.1": [0, 1, 5, 5], "2.2": [1, 3, 5, 2], "5.1": [2, 3, 3, 3]},
}


# Ayudas

def _filas(repartos: dict[str, list[int]], desde: int) -> list[Any]:
    """Filas inventadas que dan en cada PI el reparto pedido, con códigos consecutivos desde «desde»."""
    columnas = []
    for reparto in repartos.values():
        niveles = [nivel for nivel, cantidad in zip((1, 2, 3, 4), reparto[:4], strict=True) for _ in range(cantidad)]
        columnas.append(niveles + [None] * (reparto[4] if len(reparto) > 4 else 0))
    assert len({len(columna) for columna in columnas}) == 1, "todos los PI deben sumar las mismas filas"
    return [C.Fila(2 + i, str(desde + i), tuple(columna[i] for columna in columnas)) for i in range(len(columnas[0]))]


def _publicar(api: Any, asignatura: str, numero: str, repartos: dict[str, list[int]], *, desde: int,
              conjunto: str = C.BORRADOR, subida_por: str | None = A.DOCENTE_410) -> int:
    return C.publicar(api.dueno, asignatura=asignatura, numero=numero, pis=list(repartos),
                      filas=_filas(repartos, desde), nombre_archivo=f"inventado_{asignatura}_{numero}_{desde}.xlsx",
                      conjunto=conjunto, subida_por=subida_por)


def _publicar_410(api: Any, *, conjunto: str = C.BORRADOR) -> int:
    """La carga del export correcto de la 410, con los niveles de cada estudiante de NIVELES_410 del generador."""
    filas = [C.Fila(fila, str(codigo), niveles) for fila, codigo, niveles in G.NIVELES_410]
    return C.publicar(api.dueno, asignatura="450002", numero="410", pis=["5.1", "5.2", "5.3"], filas=filas,
                      nombre_archivo=A.CORRECTO, hoja=C.HOJA_410, conjunto=conjunto)


def _varias(api: Any) -> dict[tuple[str, str], int]:
    """Las tres cargas PUBLICADAS de docente.varias, con los repartos de VARIAS."""
    return {clave: _publicar(api, *clave, repartos, desde=99100001 + 100 * i, subida_por=A.VARIAS_CORREO)
            for i, (clave, repartos) in enumerate(VARIAS.items())}


def _pedir(cliente: Any, **parametros: str) -> Any:
    return cliente.get("/api/resultados", params=parametros or {"periodo": A.PERIODO})


def _cuerpo(cliente: Any, **parametros: str) -> dict[str, Any]:
    respuesta = _pedir(cliente, **parametros)
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def _seccion(cuerpo: dict[str, Any], numero: str, asignatura: str = "450002") -> dict[str, Any]:
    [seccion] = [s for s in cuerpo["secciones"] if (s["asignatura"]["codigo"], s["numero"]) == (asignatura, numero)]
    return seccion


def _indicador(seccion: dict[str, Any], pi: str) -> dict[str, Any]:
    [indicador] = [i for i in seccion["indicadores"] if i["pi"] == pi]
    return indicador


def _cifras(seccion: dict[str, Any]) -> list[tuple[str, Any, Any, Any, Any]]:
    return [(i["pi"], i["pct_sobre_calificados"], i["logrados"], i["calificados"], i["en_meta"])
            for i in seccion["indicadores"]]


def _so_de_amb_2026(api: Any) -> dict[int, str]:
    filas = api.dueno.execute("SELECT so.numero, so.descripcion FROM abet.so so JOIN abet.catalogo_version cv"
                              " USING (catalogo_version_id) WHERE cv.codigo = 'AMB-2026'").fetchall()
    return dict(filas)


def _indicador_esperado(so: int, pi: str, reparto: list[int], pct: float, en_meta: bool, *, nivel: int = 3,
                        meta: float = 80.0) -> dict[str, Any]:
    logrados = sum(reparto[nivel - 1:4])
    calificados = sum(reparto[:4])
    return {"so": so, "pi": pi, "instrumento": INSTRUMENTO, "nivel_esperado": nivel, "estudiantes_por_nivel": reparto[:4],
            "logrados": logrados, "calificados": calificados, "sin_evidencia": 0, "total": calificados,
            "pct_sobre_calificados": pct, "pct_sobre_total": pct, "meta_pct": meta, "en_meta": en_meta}


# BR-RESULTADOS-03 y BR-RESULTADOS-04, las cifras de la vista con el catálogo del plan

def test_br_resultados_03_la_412_de_450002_trae_las_cifras_de_su_carga_campo_por_campo(api: Any) -> None:
    cargas = _varias(api)
    cuerpo = _cuerpo(api.sesion(A.VARIAS_CORREO))
    assert _seccion(cuerpo, "412") == {
        "seccion_id": api.seccion("412"),
        "asignatura": {"codigo": "450002", "nombre": "Principios de Ingeniería Sostenible"},
        "numero": "412",
        "estado": "PUBLICADA",
        "carga_id": cargas[("450002", "412")],
        "pi": ["5.1", "5.2", "5.3"],
        "conjunto_reglas": "R-2026-BORRADOR",
        "conjunto_reglas_estado": "BORRADOR",
        "parametros_pendientes": PENDIENTES_BORRADOR,
        "provisional": True,
        "indicadores": [
            _indicador_esperado(5, "5.1", [1, 1, 5, 4], 81.8, True),
            _indicador_esperado(5, "5.2", [2, 3, 4, 2], 54.5, False),
            _indicador_esperado(5, "5.3", [0, 1, 4, 6], 90.9, True),
        ],
    }


def test_br_resultados_03_el_profesor_de_varias_secciones_recibe_sus_nueve_indicadores_por_so(api: Any) -> None:
    _varias(api)
    cuerpo = _cuerpo(api.sesion(A.VARIAS_CORREO))
    descripciones = _so_de_amb_2026(api)
    assert cuerpo["periodo"] == "2026-2"
    assert cuerpo["so"] == [{"numero": 2, "descripcion": descripciones[2]}, {"numero": 5, "descripcion": descripciones[5]}]
    assert [(s["asignatura"]["codigo"], s["numero"]) for s in cuerpo["secciones"]] == [
        ("450002", "412"), ("450010", "410"), ("450010", "412")]
    assert _cifras(_seccion(cuerpo, "410", "450010")) == [
        ("2.1", 72.7, 8, 11, False), ("2.2", 45.5, 5, 11, False), ("5.1", 36.4, 4, 11, False)]
    assert _cifras(_seccion(cuerpo, "412", "450010")) == [
        ("2.1", 90.9, 10, 11, True), ("2.2", 63.6, 7, 11, False), ("5.1", 54.5, 6, 11, False)]
    indicadores = [i for s in cuerpo["secciones"] for i in s["indicadores"]]
    assert len(indicadores) == 9 and sum(i["en_meta"] is True for i in indicadores) == 3
    assert {i["so"] for i in _seccion(cuerpo, "410", "450010")["indicadores"]} == {2, 5}
    assert all(i["instrumento"] == INSTRUMENTO and i["meta_pct"] == 80.0 for i in indicadores)


def test_br_resultados_05_los_porcentajes_viajan_como_numeros_json_y_no_como_textos(api: Any) -> None:
    _varias(api)
    respuesta = _pedir(api.sesion(A.VARIAS_CORREO))
    assert '"pct_sobre_calificados":81.8' in respuesta.text and '"meta_pct":80.0' in respuesta.text
    assert '"81.8"' not in respuesta.text
    indicador = _indicador(_seccion(respuesta.json(), "412"), "5.1")
    assert all(isinstance(indicador[c], float) for c in ("pct_sobre_calificados", "pct_sobre_total", "meta_pct"))


def test_br_resultados_09_cada_objeto_trae_solo_las_claves_de_la_lista_cerrada(api: Any) -> None:
    _varias(api)
    respuesta = _pedir(api.sesion(A.VARIAS_CORREO))
    cuerpo = respuesta.json()
    assert set(cuerpo) == CLAVES
    assert all(set(so) == CLAVES_SO for so in cuerpo["so"])
    assert all(set(s) == CLAVES_SECCION and set(s["asignatura"]) == {"codigo", "nombre"} for s in cuerpo["secciones"])
    assert all(set(i) == CLAVES_INDICADOR for s in cuerpo["secciones"] for i in s["indicadores"])
    for prohibido in ("subida_por", "nombre_archivo", "sha256", "trato_sin_evidencia", "pct_logro_segun_regla", "@",
                      "inventado_"):
        assert prohibido not in respuesta.text, prohibido


def test_br_resultados_04_los_indicadores_van_por_numero_de_pi_y_el_5_10_queda_despues_del_5_2(api: Any) -> None:
    # T035. Un PI 5.10 inventado en el catálogo vigente y en el plan de 450002, que ningún export trae.
    api.dueno.execute(
        "INSERT INTO abet.pi (catalogo_version_id, so_id, so_numero, numero, codigo, descripcion)"
        " SELECT so.catalogo_version_id, so.so_id, 5, 10, '5.10', 'PI inventado de prueba'"
        " FROM abet.so so JOIN abet.catalogo_version cv USING (catalogo_version_id)"
        " WHERE cv.codigo = 'AMB-2026' AND so.numero = 5")
    C.plan(api.dueno, "450002", ["5.10"])
    _publicar(api, "450002", "410", {**CORRECTO_410, "5.10": [0, 0, 5, 6]}, desde=99000001)
    seccion = _seccion(_cuerpo(api.sesion(A.DOCENTE_410)), "410")
    assert seccion["pi"] == ["5.1", "5.2", "5.3", "5.10"]
    assert [i["pi"] for i in seccion["indicadores"]] == ["5.1", "5.2", "5.3", "5.10"]
    assert _indicador(seccion, "5.10")["pct_sobre_calificados"] == 100.0


def test_br_resultados_04_una_segunda_version_de_catalogo_no_duplica_indicadores_ni_so(api: Any) -> None:
    # T035. AMB-2099 repite los códigos del SO 5 y de sus PI en otra versión de catálogo, que no rige en 2026-2.
    api.dueno.execute(
        "INSERT INTO abet.catalogo_version (carrera_id, codigo) SELECT carrera_id, 'AMB-2099' FROM abet.carrera"
        " WHERE codigo = 'AMB'")
    api.dueno.execute(
        "INSERT INTO abet.so (catalogo_version_id, numero, descripcion) SELECT catalogo_version_id, 5,"
        " 'SO 5 de una versión de prueba' FROM abet.catalogo_version WHERE codigo = 'AMB-2099'")
    api.dueno.execute(
        "INSERT INTO abet.pi (catalogo_version_id, so_id, so_numero, numero, codigo, descripcion)"
        " SELECT so.catalogo_version_id, so.so_id, 5, v.numero, '5.' || v.numero, 'PI de una versión de prueba'"
        " FROM abet.so so JOIN abet.catalogo_version cv USING (catalogo_version_id), (VALUES (1), (2), (3)) AS v (numero)"
        " WHERE cv.codigo = 'AMB-2099'")
    _publicar_410(api)
    cuerpo = _cuerpo(api.sesion(A.DOCENTE_410))
    assert cuerpo["so"] == [{"numero": 5, "descripcion": _so_de_amb_2026(api)[5]}]
    assert _cifras(_seccion(cuerpo, "410")) == [
        ("5.1", 63.6, 7, 11, False), ("5.2", 63.6, 7, 11, False), ("5.3", 72.7, 8, 11, False)]


def test_br_resultados_04_un_pi_sin_instrumento_en_el_plan_llega_con_instrumento_nulo(api: Any) -> None:
    api.dueno.execute(
        "UPDATE abet.plan_medicion pm SET instrumento_id = NULL FROM abet.pi p, abet.asignatura a"
        " WHERE p.pi_id = pm.pi_id AND a.asignatura_id = pm.asignatura_id AND a.codigo = '450002' AND p.codigo = '5.3'")
    _publicar_410(api)
    seccion = _seccion(_cuerpo(api.sesion(A.DOCENTE_410)), "410")
    assert [i["instrumento"] for i in seccion["indicadores"]] == [INSTRUMENTO, INSTRUMENTO, None]


# BR-RESULTADOS-05 y BR-RESULTADOS-06, los nulos y la meta

def test_br_resultados_06_el_80_justo_queda_en_la_meta(api: Any) -> None:
    _publicar(api, "450002", "410", {"5.1": [1, 3, 4, 3, 0], "5.2": [1, 3, 4, 3, 0], "5.3": [0, 2, 5, 3, 1]},
              desde=99000001)
    seccion = _seccion(_cuerpo(api.sesion(A.DOCENTE_410)), "410")
    assert _cifras(seccion) == [("5.1", 63.6, 7, 11, False), ("5.2", 63.6, 7, 11, False), ("5.3", 80.0, 8, 10, True)]


def test_br_resultados_05_un_pi_sin_calificaciones_no_sale_como_0(api: Any) -> None:
    _publicar(api, "450002", "410", {"5.1": [1, 3, 4, 3, 0], "5.2": [1, 3, 4, 3, 0], "5.3": [0, 0, 0, 0, 11]},
              desde=99000001)
    indicador = _indicador(_seccion(_cuerpo(api.sesion(A.DOCENTE_410)), "410"), "5.3")
    assert (indicador["estudiantes_por_nivel"], indicador["logrados"], indicador["calificados"],
            indicador["sin_evidencia"], indicador["total"]) == ([0, 0, 0, 0], 0, 0, 11, 11)
    assert (indicador["pct_sobre_calificados"], indicador["pct_sobre_total"], indicador["en_meta"]) == (None, 0.0, None)


def test_br_resultados_07_un_estudiante_sin_evidencia_deja_dos_porcentajes(api: Any) -> None:
    _publicar(api, "450002", "410", {"5.1": [1, 3, 4, 3, 0], "5.2": [1, 3, 3, 3, 1], "5.3": [1, 2, 5, 3, 0]},
              desde=99000001)
    indicador = _indicador(_seccion(_cuerpo(api.sesion(A.DOCENTE_410)), "410"), "5.2")
    assert (indicador["estudiantes_por_nivel"], indicador["logrados"], indicador["calificados"],
            indicador["sin_evidencia"], indicador["total"]) == ([1, 3, 3, 3], 6, 10, 1, 11)
    assert (indicador["pct_sobre_calificados"], indicador["pct_sobre_total"], indicador["en_meta"]) == (60.0, 54.5, False)


def test_br_resultados_05_sin_nivel_esperado_definido_los_porcentajes_y_la_meta_quedan_nulos(api: Any) -> None:
    C.conjunto_pendiente(api.dueno, "R-PRUEBA-PENDIENTE")
    _publicar(api, "450002", "410", CORRECTO_410, desde=99000001, conjunto="R-PRUEBA-PENDIENTE")
    indicador = _indicador(_seccion(_cuerpo(api.sesion(A.DOCENTE_410)), "410"), "5.1")
    assert indicador["estudiantes_por_nivel"] == [1, 3, 4, 3] and indicador["calificados"] == 11
    assert [indicador[c] for c in ("nivel_esperado", "logrados", "pct_sobre_calificados", "pct_sobre_total",
                                   "meta_pct", "en_meta")] == [None] * 6


def test_br_resultados_05_sin_meta_definida_el_logro_sigue_y_en_meta_queda_nulo(api: Any) -> None:
    api.dueno.execute("INSERT INTO abet.conjunto_reglas (carrera_id, version) SELECT carrera_id, 'R-PRUEBA-SIN-META'"
                      " FROM abet.carrera WHERE codigo = 'AMB'")
    api.dueno.execute(
        "INSERT INTO abet.parametro_valor (conjunto_reglas_id, clave, estado, valor_numero)"
        " SELECT cr.conjunto_reglas_id, p.clave, CASE WHEN p.clave = 'NIVEL_ESPERADO' THEN 'DEFINIDO' ELSE 'PENDIENTE' END,"
        " CASE WHEN p.clave = 'NIVEL_ESPERADO' THEN 3 END FROM abet.conjunto_reglas cr, abet.parametro p"
        " WHERE cr.version = 'R-PRUEBA-SIN-META'")
    _publicar(api, "450002", "410", CORRECTO_410, desde=99000001, conjunto="R-PRUEBA-SIN-META")
    indicador = _indicador(_seccion(_cuerpo(api.sesion(A.DOCENTE_410)), "410"), "5.1")
    assert (indicador["nivel_esperado"], indicador["logrados"], indicador["pct_sobre_calificados"]) == (3, 7, 63.6)
    assert (indicador["meta_pct"], indicador["en_meta"]) == (None, None)


# BR-RESULTADOS-07, lo que todavía no tiene resultado

def test_br_resultados_07_una_seccion_sin_carga_trae_su_plan_y_ninguna_cifra(api: Any) -> None:
    _publicar(api, "450002", "412", VARIAS[("450002", "412")], desde=99100001, subida_por=A.VARIAS_CORREO)
    cuerpo = _cuerpo(api.sesion(A.VARIAS_CORREO))
    assert _seccion(cuerpo, "410", "450010") == {
        "seccion_id": api.seccion("410", "450010"),
        "asignatura": {"codigo": "450010", "nombre": "Gestión Sostenible de Residuos"},
        "numero": "410", "estado": "SIN_CARGA", "carga_id": None, "pi": ["2.1", "2.2", "5.1"],
        "conjunto_reglas": None, "conjunto_reglas_estado": None, "parametros_pendientes": None, "provisional": None,
        "indicadores": [],
    }
    assert [so["numero"] for so in cuerpo["so"]] == [2, 5]
    assert sum(len(s["indicadores"]) for s in cuerpo["secciones"]) == 3


def test_br_resultados_07_una_seccion_con_solo_cargas_rechazadas_sigue_sin_carga(api: Any) -> None:
    C.rechazar(api.dueno, motivo="PI_DEL_PLAN_AUSENTE", nombre_archivo="sin_5_2_410.xlsx", pi="5.2")
    [seccion] = _cuerpo(api.sesion(A.DOCENTE_410))["secciones"]
    assert (seccion["estado"], seccion["carga_id"], seccion["indicadores"]) == ("SIN_CARGA", None, [])


def test_br_resultados_07_una_carga_reemplazada_sale_y_entra_la_que_la_reemplaza(api: Any) -> None:
    anterior = _publicar_410(api)
    nueva = C.con_error(api.dueno, anterior)
    seccion = _seccion(_cuerpo(api.sesion(A.DOCENTE_410)), "410")
    assert seccion["carga_id"] == nueva != anterior
    assert [i["pct_sobre_calificados"] for i in seccion["indicadores"]] == [60.0, 60.0, 70.0]


def test_br_resultados_07_una_seccion_sin_plan_llega_sin_pi_y_sin_carga(api: Any) -> None:
    api.dueno.execute("DELETE FROM abet.plan_medicion pm USING abet.asignatura a"
                      " WHERE a.asignatura_id = pm.asignatura_id AND a.codigo = '450010'")
    cuerpo = _cuerpo(api.sesion(A.VARIAS_CORREO))
    seccion = _seccion(cuerpo, "412", "450010")
    assert (seccion["estado"], seccion["pi"], seccion["indicadores"]) == ("SIN_CARGA", [], [])
    assert [so["numero"] for so in cuerpo["so"]] == [5]


# BR-RESULTADOS-08, la marca provisional por sección

def test_br_resultados_08_la_marca_provisional_es_la_de_la_constancia_de_la_carga(api: Any) -> None:
    carga = _publicar_410(api)
    cliente = api.sesion(A.DOCENTE_410)
    seccion = _seccion(_cuerpo(cliente), "410")
    constancia = cliente.get(f"/api/cargas/{carga}").json()
    campos = ("conjunto_reglas", "conjunto_reglas_estado", "parametros_pendientes", "provisional")
    assert [seccion[c] for c in campos] == [constancia[c] for c in campos] == [
        "R-2026-BORRADOR", "BORRADOR", PENDIENTES_BORRADOR, True]


def test_br_resultados_08_con_reglas_aprobadas_y_completas_la_seccion_no_es_provisional(api: Any) -> None:
    C.conjunto_aprobado(api.dueno)
    _publicar_410(api, conjunto=C.APROBADO)
    seccion = _seccion(_cuerpo(api.sesion(A.DOCENTE_410)), "410")
    assert (seccion["provisional"], seccion["conjunto_reglas_estado"], seccion["parametros_pendientes"]) == (
        False, "APROBADO", [])
    assert [(i["nivel_esperado"], i["meta_pct"], i["pct_sobre_calificados"], i["logrados"], i["en_meta"])
            for i in seccion["indicadores"]] == [(2, 70.0, 90.9, 10, True)] * 3


def test_br_resultados_08_un_conjunto_aprobado_al_que_le_falta_un_parametro_sigue_provisional(api: Any) -> None:
    C.conjunto_aprobado(api.dueno, "R-PRUEBA-INCOMPLETO", completo=False)
    _publicar(api, "450002", "410", CORRECTO_410, desde=99000001, conjunto="R-PRUEBA-INCOMPLETO")
    seccion = _seccion(_cuerpo(api.sesion(A.DOCENTE_410)), "410")
    assert (seccion["provisional"], seccion["conjunto_reglas_estado"], seccion["parametros_pendientes"]) == (
        True, "APROBADO", ["TRATO_SIN_EVIDENCIA"])


# BR-RESULTADOS-01, el periodo, los parámetros y la sesión

def test_br_resultados_01_sin_periodo_la_ruta_usa_el_periodo_vigente(api: Any) -> None:
    _publicar_410(api)
    cliente = api.sesion(A.DOCENTE_410)
    sin_periodo = cliente.get("/api/resultados")
    assert sin_periodo.status_code == 200 and sin_periodo.json() == _cuerpo(cliente)
    assert sin_periodo.json()["periodo"] == "2026-2"


@pytest.mark.parametrize("periodo", ["2026-13", "2026-3", "2026", "26-2", "2026-2; DROP"])
def test_br_resultados_01_un_periodo_mal_formado_responde_422_sin_secciones(api: Any, periodo: str) -> None:
    respuesta = _pedir(api.sesion(A.DOCENTE_410), periodo=periodo)
    assert respuesta.status_code == 422
    assert respuesta.json() == {"detail": "El periodo no tiene la forma AAAA-C."}
    assert respuesta.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("periodo", ["2026-1", "2030-1"])
def test_br_resultados_01_un_periodo_sin_secciones_da_listas_vacias(api: Any, periodo: str) -> None:
    _publicar_410(api)
    assert _cuerpo(api.sesion(A.DOCENTE_410), periodo=periodo) == {"periodo": periodo, "so": [], "secciones": []}


def test_br_resultados_01_un_profesor_sin_secciones_recibe_listas_vacias(api: Any) -> None:
    api.dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol) VALUES ('docente.sinseccion@example.invalid',"
                      " 'PROFESOR')")
    assert _cuerpo(api.sesion("docente.sinseccion@example.invalid")) == {"periodo": "2026-2", "so": [], "secciones": []}


def test_br_resultados_01_un_seccion_id_en_la_consulta_no_cambia_la_respuesta(api: Any) -> None:
    _publicar_410(api)
    _publicar(api, "450002", "411", CORRECTO_410, desde=99000012, subida_por=A.DOCENTE_411)
    cliente = api.sesion(A.DOCENTE_411)
    con_parametro = _cuerpo(cliente, periodo="2026-2", seccion_id=str(api.seccion("410")), carga_id="1")
    assert con_parametro == _cuerpo(cliente)
    assert [s["numero"] for s in con_parametro["secciones"]] == ["411"]


def test_br_resultados_01_sin_sesion_vigente_responde_401_sin_secciones(api: Any) -> None:
    _publicar_410(api)
    sin_cookie = _pedir(api.cliente())
    assert (sin_cookie.status_code, sin_cookie.json()) == (401, VENCIDA)
    assert sin_cookie.headers["cache-control"] == "no-store"
    cliente = api.sesion(A.DOCENTE_410)
    api.dueno.execute("UPDATE acceso.sesion s SET creada_en = now() - interval '13 hours',"
                      " expira_en = now() - interval '1 hour' FROM acceso.usuario_autorizado u"
                      " WHERE u.usuario_id = s.usuario_id AND u.correo = %s", (A.DOCENTE_410,))
    vencida = _pedir(cliente)
    assert (vencida.status_code, vencida.json()) == (401, VENCIDA)


def test_br_resultados_01_un_usuario_dado_de_baja_deja_de_ver_sus_resultados(api: Any) -> None:
    _publicar_410(api)
    cliente = api.sesion(A.DOCENTE_410)
    assert len(_cuerpo(cliente)["secciones"]) == 1
    api.dueno.execute("UPDATE acceso.usuario_autorizado SET activo = false WHERE correo = %s", (A.DOCENTE_410,))
    respuesta = _pedir(cliente)
    assert (respuesta.status_code, respuesta.json()) == (401, VENCIDA)


# BR-RESULTADOS-02 y BR-RESULTADOS-10, el alcance

def test_br_resultados_02_cada_profesor_ve_solo_su_seccion(api: Any) -> None:
    a410 = _publicar_410(api)
    a411 = _publicar(api, "450002", "411", CORRECTO_410, desde=99000012, subida_por=A.DOCENTE_411)
    for correo, propia, carga, ajena in ((A.DOCENTE_410, "410", a410, a411), (A.DOCENTE_411, "411", a411, a410)):
        respuesta = _pedir(api.sesion(correo))
        [seccion] = respuesta.json()["secciones"]
        assert (seccion["numero"], seccion["carga_id"]) == (propia, carga)
        assert f'"carga_id":{ajena},' not in respuesta.text


def test_br_resultados_02_dos_profesores_de_la_misma_seccion_la_ven_los_dos(api: Any) -> None:
    _publicar_410(api)
    api.dueno.execute("INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) SELECT usuario_id, %s"
                      " FROM acceso.usuario_autorizado WHERE correo = %s", (api.seccion("410"), A.DOCENTE_411))
    del410 = _seccion(_cuerpo(api.sesion(A.DOCENTE_410)), "410")
    del411 = _cuerpo(api.sesion(A.DOCENTE_411))
    assert [s["numero"] for s in del411["secciones"]] == ["410", "411"]
    assert _seccion(del411, "410") == del410


def test_br_resultados_10_el_coordinador_ve_las_cinco_secciones_por_asignatura_y_numero(api: Any) -> None:
    _publicar_410(api)
    # La 411 sube un mejor logro que la 410, y aun así va después, porque el orden nunca es por resultado.
    _publicar(api, "450002", "411", {"5.1": [0, 0, 5, 6], "5.2": [0, 0, 5, 6], "5.3": [0, 0, 5, 6]}, desde=99000012,
              subida_por=A.DOCENTE_411)
    _varias(api)
    respuesta = _pedir(api.sesion(A.COORDINACION))
    cuerpo = respuesta.json()
    assert [(s["asignatura"]["codigo"], s["numero"]) for s in cuerpo["secciones"]] == [
        ("450002", "410"), ("450002", "411"), ("450002", "412"), ("450010", "410"), ("450010", "412")]
    indicadores = [i for s in cuerpo["secciones"] for i in s["indicadores"]]
    assert (len(indicadores), sum(i["so"] == 5 for i in indicadores), sum(i["so"] == 2 for i in indicadores)) == (15, 11, 4)
    assert "@" not in respuesta.text and "subida_por" not in respuesta.text
    assert api.uno("SELECT count(*) FROM acceso.docente_seccion d JOIN acceso.usuario_autorizado u USING (usuario_id)"
                   " WHERE u.correo = %s", A.COORDINACION) == 0


# BR-RESULTADOS-03, la instantánea y la lectura sin escrituras

def test_br_resultados_03_la_ruta_lee_en_una_transaccion_de_solo_lectura_y_repeatable_read(
        api: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _publicar_410(api)
    vistas = []
    original = permisos.secciones_visibles

    def espia(conexion: psycopg.Connection, *argumentos: Any) -> Any:
        vistas.append((conexion.execute("SHOW transaction_isolation").fetchone()[0],
                       conexion.execute("SHOW transaction_read_only").fetchone()[0]))
        return original(conexion, *argumentos)

    monkeypatch.setattr(permisos, "secciones_visibles", espia)
    assert len(_cuerpo(api.sesion(A.DOCENTE_410))["secciones"]) == 1
    assert vistas == [("repeatable read", "on")]


def test_br_resultados_03_un_reemplazo_a_mitad_de_la_lectura_no_deja_una_seccion_sin_indicadores(
        api: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    anterior = _publicar_410(api)
    cliente = api.sesion(A.DOCENTE_410)
    original = ruta._indicadores
    reemplazos = []

    def con_reemplazo(conexion: psycopg.Connection, cargas: list[int]) -> Any:
        # Otra conexión reemplaza la carga y confirma después de que la ruta ya leyó qué carga está PUBLICADA.
        reemplazos.append(C.con_error(api.dueno, anterior))
        return original(conexion, cargas)

    monkeypatch.setattr(ruta, "_indicadores", con_reemplazo)
    seccion = _seccion(_cuerpo(cliente), "410")
    assert len(reemplazos) == 1
    assert seccion["carga_id"] == anterior and [i["pct_sobre_calificados"] for i in seccion["indicadores"]] == [
        63.6, 63.6, 72.7]
    monkeypatch.setattr(ruta, "_indicadores", original)
    siguiente = _seccion(_cuerpo(cliente), "410")
    assert siguiente["carga_id"] == reemplazos[0]
    assert [i["pct_sobre_calificados"] for i in siguiente["indicadores"]] == [60.0, 60.0, 70.0]


def test_br_resultados_03_leer_la_ruta_no_escribe_en_ninguna_tabla(api: Any) -> None:
    _varias(api)
    cliente = api.sesion(A.VARIAS_CORREO)
    tablas = [fila[0] for fila in api.dueno.execute(
        "SELECT format('%I.%I', table_schema, table_name) FROM information_schema.tables"
        " WHERE table_schema IN ('abet', 'acceso') AND table_type = 'BASE TABLE' ORDER BY 1").fetchall()]
    contar = lambda: [api.uno(sql.SQL("SELECT count(*) FROM {}").format(sql.SQL(tabla))) for tabla in tablas]  # noqa: E731
    antes = contar()
    for _ in range(5):
        assert _pedir(cliente).status_code == 200
    assert contar() == antes


# SC-005 y T034, el volumen del coordinador

def _sembrar(api: Any, secciones: int) -> list[int]:
    """Secciones 500 en adelante de 450002 en 2026-2, cada una con una carga PUBLICADA de 11 filas inventadas."""
    with api.dueno.transaction():
        return [C.publicar(api.dueno, asignatura="450002", numero=str(500 + i), pis=["5.1", "5.2", "5.3"],
                           filas=C.filas_inventadas(11, desde=99200001 + 20 * i, niveles=(3, 4, 2)),
                           nombre_archivo=f"inventado_volumen_{500 + i}.xlsx", subida_por=None)
                for i in range(secciones)]


def _nodos(plan: dict[str, Any], dentro_de_agregado: bool = False) -> Iterator[tuple[dict[str, Any], bool]]:
    yield plan, dentro_de_agregado
    agregado = dentro_de_agregado or plan["Node Type"] == "Aggregate"
    for hijo in plan.get("Plans", []):
        yield from _nodos(hijo, agregado)


def test_sc_005_el_filtro_por_carga_id_baja_por_debajo_de_la_agregacion_de_la_vista(api: Any) -> None:
    cargas = _sembrar(api, 150)
    with psycopg.connect(api.ajustes.database_url, autocommit=True) as app:
        [[plan]] = app.execute(sql.SQL("EXPLAIN (FORMAT JSON) ") + sql.SQL(ruta._INDICADORES),
                               {"cargas": cargas}).fetchall()
    nodos = list(_nodos(plan[0]["Plan"]))
    condiciones = [(nodo, dentro) for nodo, dentro in nodos
                   if "carga_id = ANY" in json.dumps({k: v for k, v in nodo.items() if k != "Plans"})]
    assert any(nodo["Node Type"] == "Aggregate" for nodo, _ in nodos)
    assert condiciones and all(dentro for _, dentro in condiciones), json.dumps(plan, indent=1)[:4000]


def test_sc_005_la_ruta_del_coordinador_con_150_secciones_responde_en_menos_de_1_s(api: Any) -> None:
    _sembrar(api, 150)
    cliente = api.sesion(A.COORDINACION)
    assert len(_cuerpo(cliente)["secciones"]) == 155  # arranque en frío de la conexión, fuera de la medida
    tiempos = []
    for _ in range(3):
        inicio = time.perf_counter()
        respuesta = _pedir(cliente)
        tiempos.append(time.perf_counter() - inicio)
        assert respuesta.status_code == 200
    assert statistics.median(tiempos) < 1.0, tiempos
