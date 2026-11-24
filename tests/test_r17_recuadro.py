from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import load_workbook

from abet_carga import r17


PLANTILLA = Path(__file__).resolve().parents[1] / "plantillas" / "R017_ambiental_general.xlsx"


@pytest.fixture
def hoja():
    """Abre una copia en memoria de la hoja del R-17 ambiental."""
    libro = load_workbook(PLANTILLA)
    yield libro["Cursos de Carrera"]
    libro.close()


def test_ejemplo_410_con_tres_oportunidades():
    pis = [
        ("5.1", "OM", "Falta justificar el método.", "Solicitar la justificación."),
        ("5.2", "OM", "Falta contrastar los resultados.", "Incluir una comparación."),
        ("5.3", "OM", "Falta sustentar la conclusión.", "Vincularla con la evidencia."),
    ]

    assert r17.componer_recuadros(pis) == (
        "5.1 · Oportunidad de mejora. Falta justificar el método.\n"
        "5.2 · Oportunidad de mejora. Falta contrastar los resultados.\n"
        "5.3 · Oportunidad de mejora. Falta sustentar la conclusión.",
        "5.1 · Oportunidad de mejora. Solicitar la justificación.\n"
        "5.2 · Oportunidad de mejora. Incluir una comparación.\n"
        "5.3 · Oportunidad de mejora. Vincularla con la evidencia.",
    )


def test_buena_practica_y_pi_sin_calificaciones():
    pis = [
        ("5.1", "BP", "Se justificó el método.", "Compartir el ejemplo."),
        ("5.3", None, "Causa que debe omitirse.", "Acción que debe omitirse."),
    ]

    assert r17.componer_recuadros(pis) == (
        "5.1 · Buena práctica. Se justificó el método.\n"
        "5.3 · Sin calificaciones en esta carga.",
        "5.1 · Buena práctica. Compartir el ejemplo.\n"
        "5.3 · Sin calificaciones en esta carga.",
    )


def test_lista_de_pi_vacia():
    assert r17.componer_recuadros([]) == ("", "")


@pytest.mark.parametrize(("texto", "esperado"), [
    ("", 1),
    ("a" * 187, 1),
    ("a" * 188, 2),
    ("a" * 188 + "\n\nb", 4),
])
def test_lineas_con_ancho_de_plantilla(texto, esperado):
    assert r17.lineas_del_recuadro(texto) == esperado


def test_lineas_con_otro_ancho():
    assert r17.lineas_del_recuadro("abcdefghij", ancho=10) == 2


@pytest.mark.parametrize(("lineas", "esperado"), [
    (1, 15.0), (3, 15.0), (4, 30.0), (29, 405.0), (30, 409.0),
])
def test_alto_de_la_ultima_fila(lineas, esperado):
    assert r17.alto_de_fila_final(lineas) == esperado


def test_formula_literal_y_alturas_independientes(hoja):
    r17.aplicar_recuadros(hoja, "=SUMA(1;2)", "uno\ndos\ntres\ncuatro")

    assert hoja.row_dimensions[31].height == 15.0
    assert hoja.row_dimensions[36].height == 30.0
    with BytesIO() as archivo:
        hoja.parent.save(archivo)
        archivo.seek(0)
        libro = load_workbook(archivo)
        celda = libro[hoja.title]["B29"]
        assert celda.value == "=SUMA(1;2)"
        assert celda.data_type == "s"
        assert celda.quotePrefix is True
        libro.close()


def _estado_del_bloque_derecho(hoja):
    """Captura valores, tipos y estilos de K28:Q31, incluida la última fila."""
    return [
        (celda.coordinate, celda.value, celda.data_type, celda.style_id)
        for fila in hoja["K28:Q31"]
        for celda in fila
    ]


def test_textos_largos_conservan_la_plantilla(hoja):
    pis = [(pi, "OM", "c" * 800, "a" * 800) for pi in ("5.1", "5.2", "5.3")]
    texto_a, texto_b = r17.componer_recuadros(pis)
    combinaciones = set(hoja.merged_cells.ranges)
    assert len(combinaciones) == 45
    bloque_derecho = _estado_del_bloque_derecho(hoja)

    r17.aplicar_recuadros(hoja, texto_a, texto_b)

    for referencia, letra, fila_final in [("B29", "c", 31), ("B34", "a", 36)]:
        celda = hoja[referencia]
        assert celda.value == "\n".join(
            f"{pi} · Oportunidad de mejora. " + letra * 800 for pi, *_ in pis
        )
        assert celda.alignment.horizontal == "left"
        assert celda.alignment.vertical == "top"
        assert celda.alignment.wrap_text is True
        assert hoja.row_dimensions[fila_final].height == 195.0
    assert all(hoja.row_dimensions[fila].height is None for fila in (29, 30, 34, 35))
    assert set(hoja.merged_cells.ranges) == combinaciones
    assert _estado_del_bloque_derecho(hoja) == bloque_derecho
