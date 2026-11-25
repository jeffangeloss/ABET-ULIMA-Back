"""Pasos de conciliacion_del_curso.feature, la opción --curso del conciliador (T023 de la spec 009, US-94).

El .feature manda. Los Antecedentes arman la base de la spec 009 con el plan de 5643 en 2026-1 y los datos inventados de
Química General, la tabla maestra INVENTADA del ensayo de la spec 008 (701, 702 y 703 con 5 estudiantes cada una, códigos
del rango 99) y las tres cargas PUBLICADA con los mismos niveles, subidas con la biblioteca abet_carga como las sube el
ensayo. Todo corre en el clúster desechable de tests/cluster_desechable.py y nunca en localhost:5432.

El conciliador db/herramientas/conciliar_tabla_maestra.py corre como proceso aparte con python -I, con el rol abet_respaldo
y con --curso, y cada «Entonces» se comprueba con su código de salida y su informe. Las pruebas del final cubren lo que el
.feature no nombra, como una diferencia solo del promedio, una sección en la meta distinta y la corrida sin --curso.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from pytest_bdd import given, parsers, scenario, then, when


def _ensayo_de_la_spec_008() -> ModuleType:
    """Pasos de ensayo_y_conciliacion.feature (spec 008) cargados por su ruta, para reusar la tabla maestra inventada, la
    publicación de las tres cargas y la corrida del conciliador, que tests/aceptacion/pasos no importa como paquete."""
    nombre = "ensayo_y_conciliacion_de_la_spec_008"
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(
            nombre, Path(__file__).with_name("test_ensayo_y_conciliacion_feature.py"))
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


E = _ensayo_de_la_spec_008()
Escenario = Any
FEATURE = "specs/009-resumen-del-curso/aceptacion/conciliacion_del_curso.feature"
CURSO_IGUAL = ("Curso igual en alumnos en el nivel esperado o superior, en el porcentaje, en el promedio y en las "
               "secciones en la meta.")
OCHO_CIFRAS = re.compile(r"(?<![0-9])[0-9]{8}(?![0-9])")


# Escenarios de US-94

@scenario(FEATURE, "El conciliador dice que el curso es igual a la tabla maestra")
def test_el_conciliador_dice_que_el_curso_es_igual() -> None:
    """T023."""


@scenario(FEATURE, "Una calificación cambiada en la tabla maestra hace distinto al curso")
def test_una_calificacion_cambiada_hace_distinto_al_curso() -> None:
    """T023."""


# Dado

@given("una base desechable de la spec 009 con el ensayo inventado de 5643 en 2026-1 publicado")
def _base_con_el_ensayo_publicado(ctx: Escenario) -> None:
    ctx.crear_base("resumen_curso")
    assert ctx.uno("SHOW server_version_num").startswith("18"), "la base desechable no es PostgreSQL 18"
    ctx.extras["maestra"] = E._maestra_de(E._codigo_99)
    E.publicar_como_la_tabla(ctx)
    assert ctx.filas("SELECT s.numero, c.estado FROM abet.carga c JOIN abet.seccion s USING (seccion_id)"
                     " ORDER BY s.numero") == [("701", "PUBLICADA"), ("702", "PUBLICADA"), ("703", "PUBLICADA")]


@given("la tabla maestra inventada con una calificación de la 702 cambiada de 4 a 2")
def _calificacion_cambiada(ctx: Escenario) -> None:
    [fila] = [f for f in E._maestra(ctx).de("702") if f["CALIFICACIÓN"] == 4]
    fila["CALIFICACIÓN"] = 2
    ctx.extras["cambiado"] = str(fila["CÓDIGO DEL ESTUDIANTE"])


# Cuando

@when(parsers.re(r'corre el conciliador con la tabla maestra inventada y la opción --curso \(propuesta\)'))
def _corre_con_curso(ctx: Escenario) -> None:
    E.correr(ctx, "--curso")


@when("corre el conciliador con --curso")
def _corre_con_curso_a_secas(ctx: Escenario) -> None:
    E.correr(ctx, "--curso")


# Entonces

@then(parsers.re(r'la salida trae «(?P<linea>[^»]+)»'))
def _la_salida_trae(ctx: Escenario, linea: str) -> None:
    assert linea == CURSO_IGUAL
    assert E._lineas(ctx).count(linea) == 1, E._salida(ctx)


@then("cada sección trae su línea de la spec 008 y además «promedio igual»")
def _cada_seccion_con_promedio_igual(ctx: Escenario) -> None:
    lineas = E._lineas(ctx)
    for seccion in E.SECCIONES:
        assert E._igual(seccion, 5) in lineas, E._salida(ctx)
        [promedio] = [linea for linea in lineas if linea.startswith(f"Sección {seccion}. ") and "promedio" in linea]
        assert "promedio igual" in promedio and "distinta" not in promedio.lower(), promedio
    assert "3 de 3 secciones iguales." in lineas


@then(parsers.re(r'el código de salida es (?P<codigo>[0-9])'))
def _codigo_de_salida(ctx: Escenario, codigo: str) -> None:
    assert ctx.extras["corrida"].returncode == int(codigo), E._salida(ctx)


@then("la salida dice que el curso y la 702 son distintos en el promedio y en el porcentaje")
def _curso_y_702_distintos(ctx: Escenario) -> None:
    lineas = E._lineas(ctx)
    [curso] = [linea for linea in lineas if linea.startswith("Curso distinto")]
    assert "el porcentaje" in curso and "el promedio" in curso, curso
    assert CURSO_IGUAL not in lineas
    # Solo la 702 cambia, así que las otras dos secciones siguen con su línea igual y su promedio igual.
    assert "Sección 702. Distinta en el promedio y en el porcentaje." in lineas, E._salida(ctx)
    assert E._igual("701", 5) in lineas and E._igual("703", 5) in lineas
    assert "Sección 701. Con promedio igual." in lineas and "Sección 703. Con promedio igual." in lineas
    assert "Sección 702. Con promedio igual." not in lineas
    assert "2 de 3 secciones iguales." in lineas


@then("no muestra el código del estudiante ni la calificación")
def _sin_codigo_ni_calificacion(ctx: Escenario) -> None:
    salida = E._salida(ctx)
    assert not OCHO_CIFRAS.search(salida), "el informe trae un número de ocho cifras"
    assert ctx.extras["cambiado"] not in salida
    for codigo in (f["CÓDIGO DEL ESTUDIANTE"] for f in E._maestra(ctx).filas):
        assert str(codigo) not in salida
    # Ninguna línea trae un decimal, salvo el PI del encabezado, así que ni un promedio ni un porcentaje ni una calificación salen escritos.
    assert not re.search(r"[0-9][.,][0-9]", "\n".join(E._lineas(ctx)[1:])), salida
    assert "calificación" not in salida.lower()


# Lo que el .feature no nombra

def _cambiar(ctx: Escenario, seccion: str, antes: int, despues: int) -> None:
    [fila] = [f for f in E._maestra(ctx).de(seccion) if f["CALIFICACIÓN"] == antes][:1]
    fila["CALIFICACIÓN"] = despues


def test_una_diferencia_solo_del_promedio_no_toca_el_porcentaje(ctx: Escenario) -> None:
    _base_con_el_ensayo_publicado(ctx)
    # Un 3 pasa a 4 en la 701: sigue del mismo lado del logro, así que el porcentaje y los alumnos son los mismos y el
    # promedio sube de 2,6 a 2,8.
    _cambiar(ctx, "701", 3, 4)
    corrida = E.correr(ctx, "--curso")
    lineas = E._lineas(ctx)
    assert corrida.returncode == 1, E._salida(ctx)
    assert "Curso distinto en el promedio." in lineas, E._salida(ctx)
    assert "Curso igual en alumnos en el nivel esperado o superior, en el porcentaje y en las secciones en la meta." in lineas
    assert "Sección 701. Distinta en el promedio." in lineas
    assert not any("Distinta en el porcentaje" in linea for linea in lineas)


def test_una_seccion_en_la_meta_en_la_tabla_y_no_en_el_sistema_cambia_el_conteo_de_secciones_en_la_meta(
        ctx: Escenario) -> None:
    _base_con_el_ensayo_publicado(ctx)
    # La 701 de la tabla pasa a cinco estudiantes con nivel 4, 100 %, y la del sistema sigue en 60 %.
    for fila in E._maestra(ctx).de("701"):
        fila["CALIFICACIÓN"] = 4
    corrida = E.correr(ctx, "--curso")
    lineas = E._lineas(ctx)
    assert corrida.returncode == 1, E._salida(ctx)
    [curso] = [linea for linea in lineas if linea.startswith("Curso distinto")]
    assert curso == ("Curso distinto en alumnos en el nivel esperado o superior, en el porcentaje, en el promedio y en "
                     "las secciones en la meta.")
    assert "Sección 701. Distinta en el promedio y en el porcentaje." in lineas


def test_una_seccion_sin_carga_publicada_hace_distinto_al_curso_y_no_tiene_linea_de_promedio(ctx: Escenario) -> None:
    ctx.crear_base("resumen_curso")
    ctx.extras["maestra"] = E._maestra_de(E._codigo_99)
    E.publicar_como_la_tabla(ctx, ("701", "702"))
    corrida = E.correr(ctx, "--curso")
    lineas = E._lineas(ctx)
    assert corrida.returncode == 1, E._salida(ctx)
    assert "Sección 703. Sin carga publicada." in lineas
    assert not any(linea.startswith("Sección 703. ") and "promedio" in linea for linea in lineas)
    assert any(linea.startswith("Curso distinto en alumnos") for linea in lineas), E._salida(ctx)
    assert "2 de 3 secciones iguales." in lineas


def test_sin_curso_el_informe_es_el_de_la_spec_008_y_no_dice_nada_del_curso(ctx: Escenario) -> None:
    _base_con_el_ensayo_publicado(ctx)
    sin = E.correr(ctx)
    assert sin.returncode == 0, E._salida(ctx)
    assert not any(linea.startswith("Curso") or "promedio" in linea for linea in E._lineas(ctx)), E._salida(ctx)
    assert E._lineas(ctx)[-1] == "3 de 3 secciones iguales."


def test_con_curso_la_conciliacion_sigue_sin_escribir_y_el_informe_no_trae_ocho_cifras(ctx: Escenario) -> None:
    _base_con_el_ensayo_publicado(ctx)
    ctx.antes = ctx.conteos()
    corrida = E.correr(ctx, "--curso")
    assert corrida.returncode == 0, E._salida(ctx)
    assert ctx.conteos() == ctx.antes
    assert not OCHO_CIFRAS.search(E._salida(ctx))
    assert E._lineas(ctx)[-1] == "3 de 3 secciones iguales."


def test_con_curso_y_r17_se_comparan_las_dos_cosas(ctx: Escenario) -> None:
    _base_con_el_ensayo_publicado(ctx)
    E.descargar_r17(ctx)
    corrida = E.correr(ctx, "--curso")
    assert corrida.returncode == 0, E._salida(ctx)
    assert CURSO_IGUAL in E._lineas(ctx)
    assert E._lineas(ctx)[-1] == "3 de 3 secciones iguales."


def test_una_meta_distinta_en_el_sistema_hace_distinto_al_curso_con_las_tres_secciones_iguales(ctx: Escenario) -> None:
    _base_con_el_ensayo_publicado(ctx)
    # Con la meta del sistema en 50 %, las tres secciones de 60 % cumplen, y la tabla, con la meta provisional de 80 %, no
    # cuenta ninguna. Los alumnos, los niveles, los porcentajes y los promedios son los mismos.
    ctx.api.dueno.execute(
        "UPDATE abet.parametro_valor SET valor_numero = 0.50 WHERE clave = 'META_LOGRO' AND conjunto_reglas_id ="
        " (SELECT cr.conjunto_reglas_id FROM abet.conjunto_reglas cr JOIN abet.carrera c USING (carrera_id)"
        " WHERE cr.version = 'R-2026-BORRADOR' AND c.codigo = 'IND')")
    corrida = E.correr(ctx, "--curso")
    lineas = E._lineas(ctx)
    assert corrida.returncode == 1, E._salida(ctx)
    assert "Curso distinto en las secciones en la meta." in lineas
    assert "3 de 3 secciones iguales." in lineas


def test_curso_lee_el_curso_del_sistema_y_sin_curso_no_lo_lee(ctx: Escenario) -> None:
    _base_con_el_ensayo_publicado(ctx)
    conciliador = E.modulo()
    with conciliador.abrir(ctx.api.base.conexion) as conexion:
        sin = conciliador.leer_base(conexion, "2026-1", "5643")
    with conciliador.abrir(ctx.api.base.conexion) as conexion:
        con = conciliador.leer_base(conexion, "2026-1", "5643", "6.1")
    assert sin.curso is None
    assert (con.curso.logrados, con.curso.calificados, con.curso.en_la_meta) == (9, 15, 0)
    assert sorted(con.curso.por_seccion) == ["701", "702", "703"]
    with conciliador.abrir(ctx.api.base.conexion) as conexion:
        assert conciliador.leer_base(conexion, "2026-1", "5643", "6.9").curso is None
