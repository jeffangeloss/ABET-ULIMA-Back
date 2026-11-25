"""Consulta del resumen del curso, abet_carga.resultados.resumen_del_curso() (T020 de la spec 009, US-91).

Las pruebas llaman a la función con las secciones que la ruta 20 le pasará y leen su resultado en una base desechable de
la spec 009, con las cargas inventadas de Química General en 2026-1 y sus niveles escritos como en
resumen_del_curso.feature, en el clúster desechable de tests/cluster_desechable.py y nunca en localhost:5432. Los
escenarios que piden la ruta 20 por HTTP viven en test_resumen_del_curso_feature.py (T021). Cada cifra esperada sale de
una cuenta a mano que el comentario deja a la vista.

Las pruebas con lo que debe pasar comprueban las cifras, el orden y los nulos, y las de lo que no debe pasar comprueban
que el curso no promedia porcentajes, que una sección sin carga publicada no trae un 0 y que la respuesta no trae más
claves que la lista cerrada de la ruta 20.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

import pytest

from abet_carga import resultados

Escenario = Any
C = sys.modules["cargas_de_prueba"]
SOLO_LECTURA = "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY"
CLAVES_DE_UN_INDICADOR = ["so", "pi", "nivel_esperado", "meta_pct", "provisional", "curso", "conteo_secciones", "secciones"]
CLAVES_DEL_CURSO = ["estudiantes_por_nivel", "logrados", "calificados", "sin_evidencia", "total",
                    "pct_sobre_calificados", "promedio_nivel", "en_meta"]
CLAVES_DE_UNA_SECCION = ["seccion_id", "numero", "estado", "carga_id", "logrados", "calificados", "sin_evidencia",
                         "pct_sobre_calificados", "promedio_nivel", "en_meta"]
CLAVES_DEL_CONTEO = ["total", "publicadas", "en_meta", "debajo_de_la_meta", "sin_dato"]
CUATRO = ("701", "702", "703", "704")


def _base(ctx: Escenario) -> None:
    ctx.crear_base("resumen_curso")


def _tres(ctx: Escenario) -> None:
    """Las tres secciones del primer escenario de resumen_del_curso.feature, con la 704 sin carga."""
    ctx.publicar_las_tres_del_primer_escenario()


def _publicar(ctx: Escenario, numero: str, niveles: tuple[int, int, int, int], sin: int = 0, **opciones: Any) -> int:
    return ctx.publicar_seccion_de_quimica(numero, niveles, sin, **opciones)


def _resumen(ctx: Escenario, numeros: tuple[str, ...] = CUATRO) -> list[dict[str, Any]]:
    """Indicadores de la función en una transacción READ ONLY con REPEATABLE READ, como la leerá la ruta 20."""
    conexion = ctx.api.dueno
    with conexion.transaction():
        conexion.execute(SOLO_LECTURA)
        return resultados.resumen_del_curso(conexion, [(ctx.seccion_de(numero), numero) for numero in numeros])


def _el_pi_61(ctx: Escenario, numeros: tuple[str, ...] = CUATRO) -> dict[str, Any]:
    [indicador] = _resumen(ctx, numeros)
    assert (indicador["so"], indicador["pi"]) == (6, "6.1")
    return indicador


def _seccion(indicador: dict[str, Any], numero: str) -> dict[str, Any]:
    [seccion] = [s for s in indicador["secciones"] if s["numero"] == numero]
    return seccion


# El curso suma alumnos y no promedia porcentajes

def test_br_resultados_13_el_curso_suma_alumnos_y_su_promedio_sale_de_la_suma_de_los_niveles(ctx: Escenario) -> None:
    _base(ctx)
    _tres(ctx)
    indicador = _el_pi_61(ctx)
    # Logrados 7 + 9 + 7 = 23 de 10 + 10 + 13 = 33 calificados, el 69,7 %. Niveles 3, 7, 13 y 10. La suma de cada nivel por su
    # conteo es 29 + 33 + 34 = 96, y 96 entre 33 da 2,91.
    assert indicador["curso"] == {"estudiantes_por_nivel": [3, 7, 13, 10], "logrados": 23, "calificados": 33,
                                  "sin_evidencia": 1, "total": 34, "pct_sobre_calificados": 69.7,
                                  "promedio_nivel": 2.91, "en_meta": False}
    assert (indicador["nivel_esperado"], indicador["meta_pct"], indicador["provisional"]) == (3, 80.0, True)


def test_br_resultados_13_el_curso_no_vale_el_promedio_de_los_porcentajes_ni_el_de_los_promedios(ctx: Escenario) -> None:
    _base(ctx)
    _tres(ctx)
    indicador = _el_pi_61(ctx)
    porcentajes = [s["pct_sobre_calificados"] for s in indicador["secciones"] if s["estado"] == "PUBLICADA"]
    promedios = [s["promedio_nivel"] for s in indicador["secciones"] if s["estado"] == "PUBLICADA"]
    assert porcentajes == [70.0, 90.0, 53.8]
    # El promedio de 70,0, 90,0 y 53,8 es 71,3, y el de 2,90, 3,30 y 2,62 es 2,94.
    assert round(sum(porcentajes) / 3, 1) == 71.3 != indicador["curso"]["pct_sobre_calificados"]
    assert round(sum(promedios) / 3, 2) == 2.94 != indicador["curso"]["promedio_nivel"]


def test_br_resultados_13_el_alumno_sin_evidencia_no_entra_a_los_calificados_ni_al_promedio(ctx: Escenario) -> None:
    _base(ctx)
    _publicar(ctx, "703", (2, 4, 4, 3), 1)
    indicador = _el_pi_61(ctx, ("703",))
    # 13 calificados y 1 sin evidencia, total 14. Con el sin evidencia contado como nivel 0 el promedio bajaría a 2,43.
    assert indicador["curso"]["calificados"] == 13 and indicador["curso"]["sin_evidencia"] == 1
    assert indicador["curso"]["total"] == 14 and indicador["curso"]["promedio_nivel"] == 2.62
    assert indicador["curso"]["pct_sobre_calificados"] == 53.8  # 7 de 13, y no 7 de 14 (50,0)
    assert _seccion(indicador, "703")["sin_evidencia"] == 1


# Cada sección, en orden de número

def test_br_resultados_13_cada_seccion_trae_sus_cifras_en_orden_de_numero_y_la_704_trae_nulos(ctx: Escenario) -> None:
    _base(ctx)
    _tres(ctx)
    secciones = _el_pi_61(ctx)["secciones"]
    assert [s["numero"] for s in secciones] == list(CUATRO)
    assert [{k: v for k, v in s.items() if k not in ("seccion_id", "carga_id")} for s in secciones] == [
        {"numero": "701", "estado": "PUBLICADA", "logrados": 7, "calificados": 10, "sin_evidencia": 0,
         "pct_sobre_calificados": 70.0, "promedio_nivel": 2.9, "en_meta": False},
        {"numero": "702", "estado": "PUBLICADA", "logrados": 9, "calificados": 10, "sin_evidencia": 0,
         "pct_sobre_calificados": 90.0, "promedio_nivel": 3.3, "en_meta": True},
        {"numero": "703", "estado": "PUBLICADA", "logrados": 7, "calificados": 13, "sin_evidencia": 1,
         "pct_sobre_calificados": 53.8, "promedio_nivel": 2.62, "en_meta": False},
        {"numero": "704", "estado": "SIN_CARGA", "logrados": None, "calificados": None, "sin_evidencia": None,
         "pct_sobre_calificados": None, "promedio_nivel": None, "en_meta": None},
    ]
    assert [s["carga_id"] for s in secciones[:3]] == [ctx.extras["cargas"][n] for n in CUATRO[:3]]
    assert secciones[3]["carga_id"] is None
    assert [s["seccion_id"] for s in secciones] == [ctx.seccion_de(n) for n in CUATRO]


def test_br_resultados_13_el_orden_es_el_de_las_secciones_que_recibe_y_no_el_del_resultado(ctx: Escenario) -> None:
    _base(ctx)
    _tres(ctx)
    secciones = _el_pi_61(ctx, ("703", "701", "702"))["secciones"]
    assert [s["numero"] for s in secciones] == ["703", "701", "702"]


def test_br_resultados_13_el_promedio_y_el_porcentaje_de_cada_seccion_son_los_de_su_r17(ctx: Escenario) -> None:
    _base(ctx)
    _tres(ctx)
    indicador = _el_pi_61(ctx)
    for numero in CUATRO[:3]:
        [(pct, n_nivel)] = [(fila[0], fila[1:5]) for fila in ctx.filas(
            "SELECT pct_logro_sobre_calificados, n_nivel_1, n_nivel_2, n_nivel_3, n_nivel_4 FROM abet.v_r17_por_pi"
            " WHERE carga_id = %s", ctx.extras["cargas"][numero])]
        seccion = _seccion(indicador, numero)
        assert seccion["pct_sobre_calificados"] == float(pct)
        # El promedio es el de la media de los niveles de los calificados, redondeada a dos decimales.
        pesos = sum(nivel * n for nivel, n in enumerate(n_nivel, start=1))
        assert seccion["promedio_nivel"] == pytest.approx(pesos / sum(n_nivel), abs=0.005)


# La meta es la del R-17

@pytest.mark.parametrize(("niveles", "pct", "en_meta"), [
    ((0, 1, 3, 1), 80.0, True),      # 4 de 5, justo en la meta
    ((0, 1, 2, 1), 75.0, False),     # 3 de 4
    ((27, 0, 107, 0), 79.9, False),  # 107 de 134 son 79,85 y el redondeo da 79,9
    ((200, 0, 799, 0), 80.0, True),  # 799 de 999 son 79,98 y el redondeo da 80,0, así que cumple igual que en el R-17
])
def test_br_resultados_14_el_curso_cumple_con_el_porcentaje_ya_redondeado_como_el_r17(
        ctx: Escenario, niveles: tuple[int, int, int, int], pct: float, en_meta: bool) -> None:
    _base(ctx)
    _publicar(ctx, "701", niveles)
    indicador = _el_pi_61(ctx, ("701",))
    assert indicador["curso"]["pct_sobre_calificados"] == pct and indicador["curso"]["en_meta"] is en_meta
    assert _seccion(indicador, "701")["en_meta"] is en_meta
    # Es lo que dice la vista del R-17 de la misma carga, y la regla es la de resultados.en_meta().
    [(vista, meta)] = ctx.filas("SELECT pct_logro_sobre_calificados, meta_logro_pct FROM abet.v_r17_por_pi"
                                " WHERE carga_id = %s", ctx.extras["cargas"]["701"])
    assert float(vista) == pct and resultados.en_meta(vista, meta) is en_meta


def test_br_resultados_14_el_conteo_de_secciones_cuenta_la_meta_solo_sobre_las_publicadas(ctx: Escenario) -> None:
    _base(ctx)
    _tres(ctx)
    assert _el_pi_61(ctx)["conteo_secciones"] == {"total": 4, "publicadas": 3, "en_meta": 1, "debajo_de_la_meta": 2,
                                                  "sin_dato": 1}


def test_br_resultados_14_una_carga_rechazada_o_reemplazada_sin_otra_publicada_cuenta_como_sin_dato(ctx: Escenario) -> None:
    _base(ctx)
    _publicar(ctx, "701", (1, 2, 4, 3))
    _publicar(ctx, "702", (0, 1, 5, 4), estado="RECHAZADA")
    reemplazada = _publicar(ctx, "703", (2, 4, 4, 3))
    ctx.api.dueno.execute("UPDATE abet.carga SET estado = 'REEMPLAZADA' WHERE carga_id = %s", (reemplazada,))
    indicador = _el_pi_61(ctx)
    assert indicador["conteo_secciones"] == {"total": 4, "publicadas": 1, "en_meta": 0, "debajo_de_la_meta": 1,
                                             "sin_dato": 3}
    for numero in ("702", "703", "704"):
        seccion = _seccion(indicador, numero)
        assert (seccion["estado"], seccion["carga_id"], seccion["pct_sobre_calificados"]) == ("SIN_CARGA", None, None)
    # El curso es solo lo que suma la 701, 7 de 10.
    assert (indicador["curso"]["logrados"], indicador["curso"]["calificados"]) == (7, 10)


def test_br_resultados_14_una_reemplazada_con_su_sucesora_publicada_cuenta_solo_la_sucesora(ctx: Escenario) -> None:
    _base(ctx)
    anterior = _publicar(ctx, "701", (0, 1, 3, 1))
    nueva = _publicar(ctx, "701", (0, 1, 2, 1), reemplaza=anterior)
    indicador = _el_pi_61(ctx, ("701",))
    assert _seccion(indicador, "701")["carga_id"] == nueva
    assert (indicador["curso"]["calificados"], indicador["curso"]["pct_sobre_calificados"]) == (4, 75.0)
    assert indicador["conteo_secciones"] == {"total": 1, "publicadas": 1, "en_meta": 0, "debajo_de_la_meta": 1,
                                             "sin_dato": 0}


# Un curso sin cargas

def test_br_resultados_14_un_curso_sin_cargas_publicadas_trae_nulos_y_no_ceros(ctx: Escenario) -> None:
    _base(ctx)
    indicador = _el_pi_61(ctx)
    assert indicador["curso"] == {"estudiantes_por_nivel": [0, 0, 0, 0], "logrados": 0, "calificados": 0,
                                  "sin_evidencia": 0, "total": 0, "pct_sobre_calificados": None,
                                  "promedio_nivel": None, "en_meta": None}
    assert indicador["conteo_secciones"] == {"total": 4, "publicadas": 0, "en_meta": 0, "debajo_de_la_meta": 0,
                                             "sin_dato": 4}
    assert (indicador["nivel_esperado"], indicador["meta_pct"], indicador["provisional"]) == (None, None, False)
    assert all(s["estado"] == "SIN_CARGA" and s["en_meta"] is None for s in indicador["secciones"])


def test_br_resultados_14_un_pi_sin_calificaciones_en_la_carga_publicada_no_inventa_un_porcentaje(ctx: Escenario) -> None:
    _base(ctx)
    _publicar(ctx, "701", (0, 0, 0, 0), 2)  # dos alumnos y los dos sin evidencia
    indicador = _el_pi_61(ctx, ("701",))
    assert indicador["curso"]["calificados"] == 0 and indicador["curso"]["sin_evidencia"] == 2
    assert (indicador["curso"]["pct_sobre_calificados"], indicador["curso"]["promedio_nivel"],
            indicador["curso"]["en_meta"]) == (None, None, None)
    assert _seccion(indicador, "701")["estado"] == "PUBLICADA"
    assert indicador["conteo_secciones"]["sin_dato"] == 1


# La marca provisional y las metas distintas

def test_br_resultados_13_el_curso_es_provisional_con_el_borrador_y_no_con_un_conjunto_aprobado_completo(ctx: Escenario) -> None:
    _base(ctx)
    _publicar(ctx, "701", (1, 2, 4, 3))
    assert _el_pi_61(ctx, ("701",))["provisional"] is True
    # Con un conjunto APROBADO y sus tres parámetros DEFINIDOS en otra sección, esa sección sola ya no es provisional.
    C.conjunto_aprobado(ctx.api.dueno, "R-IND-APROBADO", carrera="IND", meta_logro=0.80, nivel_esperado=3)
    _publicar(ctx, "702", (0, 1, 5, 4), conjunto="R-IND-APROBADO")
    assert _el_pi_61(ctx, ("702",))["provisional"] is False
    # Basta una sección provisional para que el curso lo sea.
    assert _el_pi_61(ctx, ("701", "702"))["provisional"] is True


def test_br_resultados_14_con_metas_distintas_el_curso_no_trae_meta_ni_en_meta_y_cada_seccion_conserva_la_suya(ctx: Escenario) -> None:
    _base(ctx)
    C.conjunto_aprobado(ctx.api.dueno, "R-IND-70", carrera="IND", meta_logro=0.70, nivel_esperado=3)
    _publicar(ctx, "701", (0, 1, 2, 1))                                # 75,0 con la meta de 80 %
    _publicar(ctx, "702", (0, 1, 2, 1), conjunto="R-IND-70")           # 75,0 con la meta de 70 %
    indicador = _el_pi_61(ctx, ("701", "702"))
    assert indicador["curso"]["pct_sobre_calificados"] == 75.0
    assert (indicador["meta_pct"], indicador["curso"]["en_meta"]) == (None, None)
    assert (_seccion(indicador, "701")["en_meta"], _seccion(indicador, "702")["en_meta"]) == (False, True)
    assert indicador["conteo_secciones"] == {"total": 2, "publicadas": 2, "en_meta": 1, "debajo_de_la_meta": 1,
                                             "sin_dato": 0}


def test_br_resultados_14_con_la_misma_meta_en_todas_las_secciones_el_curso_la_trae(ctx: Escenario) -> None:
    _base(ctx)
    _tres(ctx)
    indicador = _el_pi_61(ctx, ("701", "702"))
    assert (indicador["meta_pct"], indicador["nivel_esperado"]) == (80.0, 3)


def test_br_resultados_14_con_niveles_esperados_distintos_el_curso_no_trae_nivel_esperado_ni_logrados(ctx: Escenario) -> None:
    _base(ctx)
    C.conjunto_aprobado(ctx.api.dueno, "R-IND-N2", carrera="IND", meta_logro=0.80, nivel_esperado=2)
    _publicar(ctx, "701", (1, 2, 4, 3))
    _publicar(ctx, "702", (1, 2, 4, 3), conjunto="R-IND-N2")
    indicador = _el_pi_61(ctx, ("701", "702"))
    # 7 de 10 con el nivel 3 y 9 de 10 con el nivel 2. Sumar los dos mezclaría dos escalas.
    assert indicador["nivel_esperado"] is None
    assert indicador["curso"]["logrados"] is None and indicador["curso"]["pct_sobre_calificados"] is None
    assert indicador["curso"]["en_meta"] is None
    assert (_seccion(indicador, "701")["logrados"], _seccion(indicador, "702")["logrados"]) == (7, 9)
    assert indicador["curso"]["calificados"] == 20 and indicador["curso"]["promedio_nivel"] == 2.9


# Varios PI, el alcance y la lista cerrada

def test_br_resultados_13_un_curso_con_tres_pi_trae_un_elemento_por_pi_en_orden_con_sus_propias_cifras(ctx: Escenario) -> None:
    _base(ctx)
    C.publicar(ctx.api.dueno, asignatura="450002", numero="410", pis=("5.1", "5.2", "5.3"),
               filas=C.filas_inventadas(5, desde=99300000, niveles=(4, 3, 1)), nombre_archivo="resumen_450002_410.xlsx")
    ids = [(ctx.seccion_de("410", "450002"), "410"), (ctx.seccion_de("411", "450002"), "411")]
    conexion = ctx.api.dueno
    with conexion.transaction():
        conexion.execute(SOLO_LECTURA)
        indicadores = resultados.resumen_del_curso(conexion, ids)
    assert [(i["so"], i["pi"]) for i in indicadores] == [(5, "5.1"), (5, "5.2"), (5, "5.3")]
    # Los cinco alumnos tienen nivel 4 en el PI 5.1, 3 en el 5.2 y 1 en el 5.3, y cada PI se suma por separado.
    assert [i["curso"]["estudiantes_por_nivel"] for i in indicadores] == [[0, 0, 0, 5], [0, 0, 5, 0], [5, 0, 0, 0]]
    assert [i["curso"]["promedio_nivel"] for i in indicadores] == [4.0, 3.0, 1.0]
    assert [i["conteo_secciones"]["publicadas"] for i in indicadores] == [1, 1, 1]
    assert [[s["numero"] for s in i["secciones"]] for i in indicadores] == [["410", "411"]] * 3


def test_el_curso_sin_plan_o_sin_secciones_no_trae_indicadores(ctx: Escenario) -> None:
    _base(ctx)
    assert _resumen(ctx, ()) == []
    # La 450020 de 2026-2 no tiene plan de medición, así que su sección no trae ningún indicador, y la 450002 sí.
    sin_plan = C.seccion(ctx.api.dueno, "450020", "900")
    con_plan = ctx.seccion_de("410", "450002")
    conexion = ctx.api.dueno
    with conexion.transaction():
        conexion.execute(SOLO_LECTURA)
        assert resultados.resumen_del_curso(conexion, [(sin_plan, "900")]) == []
        assert len(resultados.resumen_del_curso(conexion, [(con_plan, "410")])) == 3


def test_solo_cuenta_las_secciones_que_recibe(ctx: Escenario) -> None:
    _base(ctx)
    _tres(ctx)
    indicador = _el_pi_61(ctx, ("701",))
    assert indicador["curso"]["calificados"] == 10 and indicador["conteo_secciones"]["total"] == 1
    assert [s["numero"] for s in indicador["secciones"]] == ["701"]


def test_br_resultados_12_la_respuesta_trae_solo_las_claves_de_la_lista_cerrada_y_ningun_dato_de_personas(ctx: Escenario) -> None:
    _base(ctx)
    _tres(ctx)
    [indicador] = _resumen(ctx)
    assert list(indicador) == CLAVES_DE_UN_INDICADOR
    assert list(indicador["curso"]) == CLAVES_DEL_CURSO
    assert list(indicador["conteo_secciones"]) == CLAVES_DEL_CONTEO
    assert all(list(seccion) == CLAVES_DE_UNA_SECCION for seccion in indicador["secciones"])
    texto = json.dumps(_resumen(ctx), ensure_ascii=False)
    assert not re.search(r"(?<![0-9])[0-9]{8}(?![0-9])", texto), "la respuesta trae un número de ocho cifras"
    for prohibido in ("@", "example.invalid", "subida_por", "nombre_archivo", "sha256", "profesor", "docente"):
        assert prohibido not in texto, prohibido


def test_la_consulta_no_escribe_en_la_base(ctx: Escenario) -> None:
    _base(ctx)
    _tres(ctx)
    antes = ctx.conteos()
    _resumen(ctx)
    assert ctx.conteos() == antes
