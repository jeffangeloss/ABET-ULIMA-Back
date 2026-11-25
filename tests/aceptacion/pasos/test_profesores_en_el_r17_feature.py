"""Pasos de profesores_en_el_r17.feature (US-97 y US-98 de la spec 010, BR-R17-14), con pytest-bdd en español.

El .feature manda. Cada «Entonces» se comprueba con el libro que descarga la ruta 7 y se lee con openpyxl, o con la
base desechable del escenario, sin dobles del sistema bajo prueba. Los Antecedentes arman la base de la spec 010 con
Ambiental en 2026-2 y Química en 2026-1 y sus nombres inventados, en el clúster desechable de tests/cluster_desechable.py
y nunca en localhost:5432. Los pasos de los Dado y de «se genera el R-17 de esa carga» viven en el conftest.py de esta
carpeta, porque privacidad_del_nombre.feature los repite. La consulta informativa de US-98 corre con psql 18 del clúster
desechable y la salida sin alinear.

El texto «(propuesta)» al final de un paso solo marca que la línea no está fijada en las decisiones de la spec, y el
paso exige la línea completa igual.
"""

from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from pytest_bdd import parsers, scenario, then, when

from abet_carga import r17

Escenario = Any
CP = sys.modules["cargas_de_prueba"]
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/010-nombre-del-profesor/aceptacion/profesores_en_el_r17.feature"
CONSULTA = RAIZ / "db" / "plataforma" / "neon" / "profesores_sin_nombre.sql"
PROPUESTA = r"(?: \(propuestas?\))?"
HOJA = "Cursos de Carrera"
ALTO_MAXIMO = 409.0


@scenario(FEATURE, "Una sección con un profesor trae su nombre en D10")
def test_una_seccion_con_un_profesor_trae_su_nombre() -> None:
    """US-97, escenario 1, con dos Ejemplos."""


@scenario(FEATURE, "Varios profesores salen en orden alfabético sin tildes ni mayúsculas, separados por coma, y el orden es estable")
def test_varios_profesores_salen_en_orden_alfabetico() -> None:
    """US-97, escenario 2, J-68."""


@scenario(FEATURE, "Un profesor dado de baja sigue en D10 de su sección")
def test_un_profesor_dado_de_baja_sigue_en_d10() -> None:
    """US-97, escenario 3, J-67."""


@scenario(FEATURE, "Solo los profesores de la sección salen en D10")
def test_solo_los_profesores_de_la_seccion_salen_en_d10() -> None:
    """US-97, escenario 4."""


@scenario(FEATURE, "Un nombre que parece fórmula queda como texto")
def test_un_nombre_que_parece_formula_queda_como_texto() -> None:
    """US-97, escenario 5, BR-R17-04."""


@scenario(FEATURE, "Tres nombres caben en D10:I10 y la fila 10 crece sin mover el resto de la cabecera")
def test_tres_nombres_caben_y_la_fila_10_crece() -> None:
    """US-97, escenario 6, FR-009."""


@scenario(FEATURE, "Fuera de D10 y de la fila 10 la plantilla no cambia")
def test_fuera_de_d10_la_plantilla_no_cambia() -> None:
    """US-97, escenario 7."""


@scenario(FEATURE, "Un profesor sin nombre no sale y el otro sí")
def test_un_profesor_sin_nombre_no_sale_y_el_otro_si() -> None:
    """US-98, escenario 1, J-69."""


@scenario(FEATURE, "Si ningún profesor tiene nombre, D10 queda vacía como hoy")
def test_si_ningun_profesor_tiene_nombre_d10_queda_vacia() -> None:
    """US-98, escenario 2, FR-010."""


@scenario(FEATURE, "La sección sin profesor tiene R-17 con D10 vacía")
def test_la_seccion_sin_profesor_tiene_r17() -> None:
    """US-98, escenario 3, FR-010."""


@scenario(FEATURE, "La consulta informativa cuenta las secciones publicadas con un profesor sin nombre")
def test_la_consulta_informativa_cuenta_las_secciones() -> None:
    """US-98, escenario 4, FR-011."""


# Ayudas

def _hoja(ctx: Escenario, indice: int = -1) -> Any:
    return _conftest(ctx).hoja_r17_010(ctx, indice)


def _conftest(ctx: Escenario) -> Any:
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            return plugin
    raise AssertionError("no se encuentra tests/aceptacion/pasos/conftest.py")


def _celdas_con_texto(hoja: Any) -> list[str]:
    return [celda.value for fila in hoja.iter_rows() for celda in fila if isinstance(celda.value, str)]


def _alturas(hoja: Any, filas: list[int]) -> dict[int, float | None]:
    return {fila: hoja.row_dimensions[fila].height for fila in filas}


# Entonces, D10

@then(parsers.re(r'D10 de la hoja vale "(?P<nombre>[^"]+)"'))
def _d10_de_la_hoja_vale(ctx: Escenario, nombre: str) -> None:
    assert _hoja(ctx)["D10"].value == nombre


@then(parsers.re(r'D10 vale "(?P<nombre>[^"]+)"(?P<veces> las dos veces)?'))
def _d10_vale(ctx: Escenario, nombre: str, veces: str | None) -> None:
    libros = ctx.extras["libros_010"]
    assert len(libros) == (2 if veces else 1)
    for indice in range(len(libros)):
        assert _hoja(ctx, indice)["D10"].value == nombre, f"D10 del libro {indice + 1}"


@then(parsers.re(r'B10 de la hoja sigue diciendo "(?P<rotulo>[^"]+)"'))
def _b10_sigue_diciendo(ctx: Escenario, rotulo: str) -> None:
    assert _hoja(ctx)["B10"].value == rotulo


@then(parsers.re(r'B6 de la hoja dice "(?P<carrera>[^"]+)"'))
def _b6_de_la_hoja_dice(ctx: Escenario, carrera: str) -> None:
    assert _hoja(ctx)["B6"].value == carrera


@then(parsers.re(r'D10 no contiene "(?P<texto>[^"]+)"(?:, que dicta solo la 702)?'))
def _d10_no_contiene(ctx: Escenario, texto: str) -> None:
    assert texto not in (_hoja(ctx)["D10"].value or "")


@then(parsers.re(r'D10 es una cadena que empieza por "(?P<texto>[^"]+)"'))
def _d10_es_una_cadena(ctx: Escenario, texto: str) -> None:
    celda = _hoja(ctx)["D10"]
    assert celda.data_type == "s", celda.data_type
    assert isinstance(celda.value, str) and celda.value.startswith(texto)


@then("ninguna celda del libro es una fórmula")
def _ninguna_formula(ctx: Escenario) -> None:
    libro = load_workbook(io.BytesIO(ctx.extras["libros_010"][-1].content))
    formulas = [f"{hoja.title}!{celda.coordinate}" for hoja in libro.worksheets for fila in hoja.iter_rows()
                for celda in fila if celda.data_type == "f"]
    assert formulas == []


@then("D10 trae los tres nombres completos")
def _d10_trae_los_tres_nombres(ctx: Escenario) -> None:
    esperados = ["Profesor Inventado Bartolomé Cuatrecasas Villanueva", "Profesor Inventado Ángel Echeverría Santisteban",
                 "Profesor Inventado Setecientos Tres"]
    assert _hoja(ctx)["D10"].value == ", ".join(sorted(esperados, key=r17.clave_de_orden))


@then(parsers.re(r'D10 tiene ajuste de texto y la fila 10 es más alta que en la plantilla, sin pasar de 409 puntos'
                 + PROPUESTA))
def _d10_con_ajuste_y_fila_mas_alta(ctx: Escenario) -> None:
    hoja = _hoja(ctx)
    plantilla = load_workbook(r17.PLANTILLA)[HOJA]
    assert hoja["D10"].alignment.wrap_text is True
    assert hoja["D10"].alignment.vertical == "top"
    alto = hoja.row_dimensions[10].height
    assert alto is not None and (plantilla.row_dimensions[10].height or 15.0) < alto <= ALTO_MAXIMO, alto
    ctx.extras["alturas_010"] = _alturas(hoja, [9, 11, *range(29, 37)])


@then("las filas 9 y 11 y las filas 29 a 36 tienen el mismo alto que con un solo profesor")
def _filas_con_el_mismo_alto(ctx: Escenario) -> None:
    # Con un solo profesor. Los dos nombres que el escenario agregó se retiran y la misma carga se descarga otra vez.
    for correo in ("docente721@example.invalid", "docente722@example.invalid"):
        ctx.api.dueno.execute("UPDATE acceso.usuario_autorizado SET nombre = NULL WHERE correo = %s", (correo,))
    _conftest(ctx).generar_r17_010(ctx)
    con_uno = _hoja(ctx)
    assert con_uno["D10"].value == "Profesor Inventado Setecientos Tres"
    assert con_uno.row_dimensions[10].height is None or con_uno.row_dimensions[10].height == 15.0
    assert _alturas(con_uno, [9, 11, *range(29, 37)]) == ctx.extras["alturas_010"]


# Entonces, fuera de D10

@then("B6, D8, D9, D11, I11 y B15 de la hoja valen lo mismo que antes de la spec 010")
def _cabecera_igual(ctx: Escenario) -> None:
    hoja = _hoja(ctx)
    asignatura = ctx.uno("SELECT nombre FROM abet.asignatura WHERE codigo = '450002'")
    assert [hoja[ref].value for ref in ("B6", "D8", "D9", "D11", "I11", "B15")] == [
        "Carrera de Ingeniería Ambiental", "450002", asignatura, "410", "2026-2", "Student Outcome (SO) 5"]


@then("las 45 celdas combinadas de la plantilla siguen combinadas")
def _celdas_combinadas(ctx: Escenario) -> None:
    de_la_plantilla = {str(rango) for rango in load_workbook(r17.PLANTILLA)[HOJA].merged_cells.ranges}
    del_libro = {str(rango) for rango in _hoja(ctx).merged_cells.ranges}
    assert len(de_la_plantilla) == 45
    assert de_la_plantilla <= del_libro
    # La única combinación que el R-17 suma es la franja PROVISIONAL de B7:I7 (BR-R17-05).
    assert del_libro - de_la_plantilla <= {"B7:I7"}


@then("los recuadros A y B traen lo mismo que antes de la spec 010")
def _recuadros_iguales(ctx: Escenario) -> None:
    hoja = _hoja(ctx)
    declaradas = ctx.filas("SELECT p.codigo, d.tipo, d.causa, d.accion FROM abet.mejora_declaracion_pi d"
                           " JOIN abet.pi p USING (pi_id) WHERE d.declaracion_id = (SELECT max(declaracion_id)"
                           " FROM abet.mejora_declaracion WHERE carga_id = %s) ORDER BY p.so_numero, p.numero",
                           ctx.carga_id)
    causas, acciones = r17.componer_recuadros(declaradas)
    assert (hoja["B29"].value, hoja["B34"].value) == (causas, acciones)


# Entonces, US-98

@then(parsers.re(r'la hoja «Cursos de Carrera» no contiene "(?P<texto>[^"]+)" en ninguna celda'))
def _sin_el_texto(ctx: Escenario, texto: str) -> None:
    libro = load_workbook(io.BytesIO(ctx.extras["libros_010"][-1].content))
    assert [celda for celda in _celdas_con_texto(libro[HOJA]) if texto in celda] == []


@then(parsers.re(r'la hoja «Constancia» sigue diciendo «(?P<texto>[^»]+)»'))
def _constancia_sigue_diciendo(ctx: Escenario, texto: str) -> None:
    libro = load_workbook(io.BytesIO(ctx.extras["libros_010"][-1].content))
    assert texto in _celdas_con_texto(libro["Constancia"])


@then(parsers.re(r"la respuesta es 200$"))
def _respuesta_200(ctx: Escenario) -> None:
    # El paso compartido de conftest.py lee un cuerpo JSON, y la ruta 7 responde un libro de Excel.
    assert ctx.extras["libros_010"][-1].status_code == 200
    assert ctx.extras["libros_010"][-1].content[:2] == b"PK"


@then(parsers.re(r'D10 está vacía y B10 sigue diciendo "(?P<rotulo>[^"]+)"'))
def _d10_vacia(ctx: Escenario, rotulo: str) -> None:
    hoja = _hoja(ctx)
    assert hoja["D10"].value is None
    assert hoja["B10"].value == rotulo


@then("D10 está vacía y el resto de la cabecera es igual que antes de la spec 010")
def _d10_vacia_y_cabecera_igual(ctx: Escenario) -> None:
    hoja = _hoja(ctx)
    assert hoja["D10"].value is None
    asignatura = ctx.uno("SELECT nombre FROM abet.asignatura WHERE codigo = '5643'")
    assert [hoja[ref].value for ref in ("B6", "D8", "D9", "D11", "I11", "B15")] == [
        "Carrera de Ingeniería Industrial", "5643", asignatura, "704", "2026-1", "Student Outcome (SO) 6"]


# La consulta informativa

@when(parsers.re(r'corre db/plataforma/neon/profesores_sin_nombre\.sql con -v periodo=(?P<periodo>[0-9]{4}-[0-9])'
                 + PROPUESTA))
def _corre_la_consulta(ctx: Escenario, periodo: str) -> None:
    antes = _conteos(ctx)
    entorno = CP.entorno_de_programacion(ctx.api.base.nombre)
    ctx.extras["consulta_010"] = subprocess.run(
        ["psql", "-X", "-A", "-t", "-F", "|", "-v", "ON_ERROR_STOP=1", "-v", f"periodo={periodo}", "-f", str(CONSULTA)],
        env=entorno, capture_output=True, text=True, encoding="utf-8", check=False, timeout=60)
    ctx.extras["conteos_010"] = antes


def _conteos(ctx: Escenario) -> dict[str, int]:
    tablas = ctx.filas("SELECT table_schema, table_name FROM information_schema.tables"
                       " WHERE table_schema IN ('abet', 'acceso') AND table_type = 'BASE TABLE' ORDER BY 1, 2")
    return {f"{esquema}.{tabla}": int(ctx.uno(f'SELECT count(*) FROM "{esquema}"."{tabla}"')) for esquema, tabla in tablas}


def _salida(ctx: Escenario) -> list[str]:
    corrida = ctx.extras["consulta_010"]
    assert corrida.returncode == 0, corrida.stderr
    return corrida.stdout.splitlines()


@then(parsers.re(r'la salida dice (?P<secciones>[0-9]+) secci(?:ón|ones) publicadas? con un profesor sin nombre y '
                 r'(?P<profesores>[0-9]+) profesor(?:es)? asignados? sin nombre'))
def _la_salida_dice(ctx: Escenario, secciones: str, profesores: str) -> None:
    salida = _salida(ctx)
    assert salida[-4:] == ["Secciones publicadas del periodo con algún profesor asignado sin nombre.", secciones,
                           "Profesores asignados sin nombre a esas secciones.", profesores], salida


@then("la salida no contiene correos, nombres ni números de sección")
def _la_salida_sin_datos(ctx: Escenario) -> None:
    texto = "\n".join(_salida(ctx))
    assert not re.search(r"@|example|docente|Profesor Inventado|\b70[1-4]\b|\b45[0-9]{4}\b|5643", texto), texto
    # Cada línea es un rótulo fijo o un número, así que ninguna fila de datos puede colarse.
    assert all(re.fullmatch(r"[0-9]+", linea) or linea.endswith(".") or linea in ("SET", "on") for linea in _salida(ctx))
    assert _conteos(ctx) == ctx.extras["conteos_010"]


@then("la sesión queda en solo lectura antes de la primera consulta")
def _solo_lectura(ctx: Escenario) -> None:
    assert _salida(ctx)[:2] == ["SET", "on"], _salida(ctx)
    texto = CONSULTA.read_text(encoding="utf-8")
    primera = re.search(r"^(?:SELECT|WITH)\b", texto, flags=re.MULTILINE)
    assert primera is not None and 0 <= texto.index("\nSET default_transaction_read_only = on;\n") < primera.start()
