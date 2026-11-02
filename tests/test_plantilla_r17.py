"""Pruebas de la plantilla del R-17, el reporte de medición de la sección (T034).

La plantilla es plantillas/R017_ambiental_general.xlsx, la hoja «Cursos de Carrera» vaciada, y su
logotipo es plantillas/R017_logotipo.png, que r17.py vuelve a insertar. Cada revisión devuelve la
lista de problemas que encuentra, con la parte o la celda y sin copiar el contenido hallado, y corre
dos veces, sobre la plantilla versionada (lo que debe pasar) y sobre una copia alterada en tmp_path
(lo que no debe pasar). Las pruebas nombran la regla de negocio (business rule, BR) de
specs/features/r17/r17.spec.md que cubren, y las de la regla 2 de scripts/preflight.sh repiten aquí,
con Python, su alcance sobre la plantilla. Los indicadores de desempeño (performance indicators, PI)
y el resultado del estudiante (student outcome, SO) ocupan filas fijas de la hoja.
"""

from __future__ import annotations

import re
import zipfile
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import openpyxl
from defusedxml.ElementTree import fromstring
from openpyxl.comments import Comment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet
from PIL import Image, PngImagePlugin

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = RAIZ / "plantillas" / "R017_ambiental_general.xlsx"
LOGOTIPO = RAIZ / "plantillas" / "R017_logotipo.png"
HOJA = "Cursos de Carrera"
AUTOR = "ABET_SIS_MED"
FECHA_FIJA = "2026-10-28T00:00:00Z"
FECHA_DEL_ZIP = (1980, 1, 1, 0, 0, 0)

# Lista cerrada de cadenas de la plantilla, cada una en su celda. Son los rótulos de la hoja
# original, con sus espacios tal como vienen (C23 termina en espacio y B21 lleva dos tras «II.»).
ROTULOS: dict[str, str] = {
    "B5": "Facultad de Ingeniería",
    "B6": "Carrera de Ingeniería Ambiental",
    "E6": "REPORTE DE MEDICIÓN DE LOS INDICADORES DE DESEMPEÑO (PI) DE LA SECCIÓN",
    "B8": "Código:",
    "B9": "Asignatura:",
    "B10": "Profesor:",
    "B11": "Sección:",
    "H11": "Período:",
    "B13": "I. CONTENIDOS DE EVALUACIÓN Y HERRAMIENTAS DE MEDICIÓN (ASSESSMENT)",
    "B15": "Student Outcome (SO)",
    "B16": "Indicadores de Desempeño (PI)",
    "E16": "Instrumento de medición",
    "G16": "Descripción del instrumento de medición",
    "B21": "II.  REPORTE DEL NIVEL DE LOGRO ALCANZADO POR INDICADOR DE DESEMPEÑO (PI) "
           "E IDENTIFICACIÓN DE OPORTUNIDADES DE MEJORA",
    "B23": "Indicador de Desempeño (PI)",
    "C23": "Instrumento de medición ",
    "E23": "Porcentaje de alumnos que cumplen con el PI",
    "G23": "Meta",
    "H23": "Plan de acción",
    "K23": "Conteo de Frecuencias",
    "K24": "Número de alumnos que obtuvieron 1 y 2",
    "K25": "Número de alumnos que obtuvieron 3 y 4",
    "K26": "Porcentaje de cumplimiento del PI",
    "B28": "A. Identifique las causas principales que pudieron influir en no alcanzar el indicador "
           "(por ejemplo: planificación, participación, recursos, tiempos, entre otros).",
    "B33": "B. Proponga acciones concretas que permitan superar las causas identificadas y/o mejorar "
           "el resultado del indicador",
    "B38": "III. MEDICIÓN DEL LOGRO DE LOS INDICADORES DE DESEMPEÑO (PI) POR ESTUDIANTE:",
    "B40": "1= No satisfactorio, 2= En proceso, 3= Satisfactorio, 4= Sobresaliente",
    "B42": "SO",
    "C42": "PI",
    "D42": "PROFESOR",
    "E42": "CÓDIGO DEL ESTUDIANTE",
    "F42": "CALIFICACIÓN",
}

# Mapa de celdas que llena r17.py (plantillas/README.md). Todas quedan vacías en la plantilla.
CABECERA = {"D8": "D8:I8", "D9": "D9:I9", "D10": "D10:I10", "D11": "D11:G11", "I11": "I11"}
BLOQUE_I = {
    fila: (f"B{fila}", f"C{fila}:D{fila}", f"E{fila}:F{fila}", f"G{fila}:I{fila}") for fila in (17, 18, 19)
}
BLOQUE_II = {
    fila: (f"B{fila}", f"C{fila}:D{fila}", f"E{fila}:F{fila}", f"G{fila}", f"H{fila}:I{fila}", f"M{fila}")
    for fila in (24, 25, 26)
}
RECUADROS = ("B29:I31", "B34:I36")
FRANJA = "B7:I7"
TABLA = "Tabla26"
TABLA_RANGO = "B42:F184"
ENCABEZADOS = ["SO", "PI", "PROFESOR", "CÓDIGO DEL ESTUDIANTE", "CALIFICACIÓN"]

# Estructura de la hoja original que la plantilla conserva.
COMBINADAS = {
    "B5:D5", "B6:D6", "B8:C8", "D8:I8", "B9:C9", "D9:I9", "B10:C10", "D10:I10", "D11:G11",
    "B13:I13", "B15:I15", "B16:D16", "E16:F16", "G16:I16",
    "C17:D17", "E17:F17", "G17:I17", "C18:D18", "E18:F18", "G18:I18", "C19:D19", "E19:F19", "G19:I19",
    "B21:I21", "C23:D23", "E23:F23", "H23:I23", "K23:M23",
    "C24:D24", "E24:F24", "H24:I24", "K24:L24", "C25:D25", "E25:F25", "H25:I25", "K25:L25",
    "C26:D26", "E26:F26", "H26:I26", "K26:L26",
    "B29:I31", "B33:H33", "B34:I36", "B38:I38", "B40:I40",
}
ANCHOS = {
    "A": 10.140625, "B": 19.140625, "C": 19.140625, "D": 33.42578125, "E": 34.28515625, "F": 25.42578125,
    "G": 25.140625, "H": 25.140625, "I": 26.85546875, "J": 12.0, "K": 23.85546875, "L": 12.7109375,
}
ALTOS = {
    6: 15.75, 14: 15.75, 16: 15.0, 17: 77.25, 18: 75.75, 19: 75.75, 24: 48.75, 25: 48.75, 26: 48.75, 40: 15.0,
}
FORMATOS = {"E24": "0%", "E25": "0%", "E26": "0%", "G24": "0.00%", "G25": "0.00%", "G26": "0.00%",
            "M24": "0", "M25": "0", "M26": "0%"}
REGLAS_CONDICIONALES = {
    "E24:F26": [("greaterThan", ["0.79"]), ("lessThan", ["0.8"]), ("lessThan", ["0.8"]),
                ("between", ["0.75", "0.8"]), ("between", ["0.75", "0.8"]), ("lessThan", ["0.8"])],
    "M26": [("greaterThan", ["0.8"])],
}

PARTES_NECESARIAS = {"xl/workbook.xml", "xl/styles.xml", "docProps/core.xml", "docProps/app.xml"}
# Partes que la plantilla no puede traer, por subcadena del nombre en minúsculas. El logotipo no va
# en la plantilla, porque r17.py lo inserta desde plantillas/R017_logotipo.png.
PARTES_PROHIBIDAS = ("comment", "person", "externallink", "customxml", "docprops/custom.xml", "printersettings",
                     "vbaproject", "drawings/", "media/", "calcchain", "embeddings/", "activex/", "ctrlprops/")
# Lista cerrada de partes del zip. Una parte nueva, como un caché de tabla dinámica, un registro de
# revisiones o una etiqueta de confidencialidad, puede traer datos o personas, así que entra solo
# después de revisarla y de sumarla aquí.
PARTES_PERMITIDAS = frozenset({
    "[Content_Types].xml", "_rels/.rels", "docProps/app.xml", "docProps/core.xml", "xl/workbook.xml",
    "xl/_rels/workbook.xml.rels", "xl/styles.xml", "xl/theme/theme1.xml", "xl/worksheets/sheet1.xml",
    "xl/worksheets/_rels/sheet1.xml.rels", "xl/tables/table1.xml",
})
# Atributos con texto libre, como el nombre de una hoja, de una tabla, de una columna o de un estilo,
# la descripción de un dibujo o el autor de una revisión. Los demás atributos traen anchos, colores y
# medidas, como 33.42578125 o 00808080, que no son códigos ni nombres.
ATRIBUTOS_DE_TEXTO = frozenset({
    "name", "displayName", "descr", "title", "tooltip", "display", "prompt", "promptTitle", "error",
    "errorTitle", "comment", "userName", "userId", "author", "codeName", "totalsRowLabel",
})
# Textos que el libro admite fuera de los rótulos, en la lista cerrada de todas sus partes. Son las
# propiedades fijas, el nombre y la versión de openpyxl, los umbrales de los formatos condicionales y
# los nombres de la hoja, de la tabla, de sus columnas y de su estilo, de dos estilos de celda y del
# tema de Office.
TEXTOS_DE_ESTRUCTURA = frozenset({
    AUTOR, FECHA_FIJA, "Microsoft Excel Compatible / Openpyxl 3.1.5", "3.1", "0.75", "0.79", "0.8",
    HOJA, TABLA, *ENCABEZADOS, "Normal", "Porcentaje", "TableStyleLight10", "Tema de Office", "Office",
    "Office Theme",
})
TROZOS_PNG_PERMITIDOS = {"IHDR", "PLTE", "tRNS", "IDAT", "IEND"}
OCHO_DIGITOS = re.compile(r"(?<!\d)\d{8}(?!\d)")
CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


# Lectura de la plantilla

def partes_del_zip(ruta: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(ruta) as libro:
        return {nombre: libro.read(nombre) for nombre in libro.namelist()}


def hoja_de(ruta: Path) -> Worksheet:
    return openpyxl.load_workbook(ruta)[HOJA]


def nombre_local(etiqueta: str) -> str:
    return etiqueta.rsplit("}", 1)[-1]


def ancho(hoja: Worksheet, letra: str) -> float | None:
    """Ancho de una columna, también cuando openpyxl la agrupa con sus vecinas (min y max)."""
    indice = openpyxl.utils.column_index_from_string(letra)
    for dimension in hoja.column_dimensions.values():
        if dimension.min and dimension.max and dimension.min <= indice <= dimension.max:
            return dimension.width
    return None


def celdas_de(rango: str) -> list[str]:
    inicio, _, fin = rango.partition(":")
    fin = fin or inicio
    columnas = range(openpyxl.utils.column_index_from_string(re.sub(r"\d", "", inicio)),
                     openpyxl.utils.column_index_from_string(re.sub(r"\d", "", fin)) + 1)
    filas = range(int(re.sub(r"\D", "", inicio)), int(re.sub(r"\D", "", fin)) + 1)
    return [f"{openpyxl.utils.get_column_letter(c)}{f}" for f in filas for c in columnas]


def textos_de_un_xml(datos: bytes) -> list[str]:
    """Textos de los nodos y de los atributos de texto libre de un XML (Extensible Markup Language)."""
    textos: list[str] = []
    for elemento in fromstring(datos).iter():
        textos += [t for t in (elemento.text, elemento.tail) if t and t.strip()]
        textos += [v for k, v in elemento.attrib.items() if nombre_local(k) in ATRIBUTOS_DE_TEXTO]
    return textos


def trozos_png(ruta: Path) -> list[str]:
    """Tipos de los trozos (chunks) de un PNG (Portable Network Graphics), en orden."""
    datos = ruta.read_bytes()
    if datos[:8] != b"\x89PNG\r\n\x1a\n":
        return ["no es PNG"]
    trozos, posicion = [], 8
    while posicion + 8 <= len(datos):
        largo = int.from_bytes(datos[posicion:posicion + 4], "big")
        trozos.append(datos[posicion + 4:posicion + 8].decode("latin-1"))
        posicion += 12 + largo
    return trozos


# Revisiones. Cada una devuelve la lista de problemas, vacía si la plantilla cumple.

def problemas_de_formulas(ruta: Path) -> list[str]:
    problemas = [f"{nombre} trae #REF!" for nombre, datos in partes_del_zip(ruta).items() if b"#REF!" in datos]
    for hoja in openpyxl.load_workbook(ruta).worksheets:
        for fila in hoja.iter_rows():
            problemas += [f"{celda.coordinate} trae una fórmula" for celda in fila if celda.data_type == "f"]
        if hoja.data_validations.dataValidation:
            problemas.append(f"la hoja trae {len(hoja.data_validations.dataValidation)} validaciones de datos")
    return problemas


def problemas_de_rotulos(ruta: Path) -> list[str]:
    hoja = hoja_de(ruta)
    return [f"{ref} no trae su rótulo" for ref, rotulo in ROTULOS.items() if hoja[ref].value != rotulo]


def cadenas_fuera_de_la_lista(ruta: Path) -> list[str]:
    """Valores que no son el rótulo de su celda, en cualquier hoja, y hojas o tablas ajenas a la plantilla."""
    libro = openpyxl.load_workbook(ruta)
    problemas = [f"hoja con otro nombre en la posición {i}" for i, n in enumerate(libro.sheetnames) if n != HOJA]
    for hoja in libro.worksheets:
        for fila in hoja.iter_rows():
            problemas += [f"{celda.coordinate} trae un valor fuera de la lista de rótulos" for celda in fila
                          if celda.value is not None and ROTULOS.get(celda.coordinate) != celda.value]
        for nombre in hoja.tables:
            if nombre != TABLA or [c.name for c in hoja.tables[nombre].tableColumns] != ENCABEZADOS:
                problemas.append("una tabla con otro nombre u otras columnas")
    return problemas


def problemas_de_estructura(ruta: Path) -> list[str]:
    hoja = hoja_de(ruta)
    problemas = []
    combinadas = {str(rango) for rango in hoja.merged_cells.ranges}
    if combinadas != COMBINADAS:
        problemas.append(f"celdas combinadas que difieren de la fuente ({len(combinadas ^ COMBINADAS)})")
    problemas += [f"ancho de la columna {letra}" for letra, valor in ANCHOS.items() if ancho(hoja, letra) != valor]
    problemas += [f"alto de la fila {fila}" for fila, valor in ALTOS.items()
                  if hoja.row_dimensions[fila].height != valor]
    problemas += [f"formato numérico de {ref}" for ref, formato in FORMATOS.items()
                  if hoja[ref].number_format != formato]
    reglas = {str(rango.sqref): [(regla.operator, list(regla.formula)) for regla in rango.rules]
              for rango in hoja.conditional_formatting}
    if reglas != REGLAS_CONDICIONALES:
        problemas.append("formatos condicionales distintos")
    if hoja.sheet_view.showGridLines is not False or hoja.sheet_view.zoomScale != 90:
        problemas.append("vista de la hoja")
    if hoja.page_setup.paperSize not in (9, "9") or hoja.page_setup.orientation != "portrait":
        problemas.append("página A4 vertical")
    return problemas


def problemas_de_la_tabla(ruta: Path) -> list[str]:
    hoja = hoja_de(ruta)
    if TABLA not in hoja.tables:
        return ["falta la tabla de estudiantes"]
    tabla = hoja.tables[TABLA]
    problemas = [] if tabla.ref == TABLA_RANGO else ["la tabla no va de B42 a F184"]
    if [c.name for c in tabla.tableColumns] != ENCABEZADOS:
        problemas.append("columnas de la tabla")
    ocupadas = [ref for ref in celdas_de("B43:F184") if hoja[ref].value is not None]
    problemas += [f"{ref} de la tabla trae un valor" for ref in ocupadas]
    return problemas


def problemas_de_la_franja(ruta: Path) -> list[str]:
    hoja = hoja_de(ruta)
    problemas = [f"{ref} de la fila 7 trae un valor" for ref in celdas_de(FRANJA) if hoja[ref].value is not None]
    if any(rango.min_row <= 7 <= rango.max_row for rango in hoja.merged_cells.ranges):
        problemas.append("la fila 7 trae celdas combinadas")
    for fila in hoja.iter_rows():
        problemas += [f"{c.coordinate} dice PROVISIONAL" for c in fila if "PROVISIONAL" in str(c.value or "").upper()]
    return problemas


def partes_prohibidas(ruta: Path) -> list[str]:
    partes = partes_del_zip(ruta)
    problemas = [f"parte prohibida {nombre}" for nombre in partes
                 if any(marca in nombre.lower() for marca in PARTES_PROHIBIDAS)]
    problemas += [f"{nombre} trae un vínculo externo" for nombre, datos in partes.items()
                  if nombre.endswith(".rels") and b'TargetMode="External"' in datos]
    problemas += [f"falta la parte {nombre}" for nombre in sorted(PARTES_NECESARIAS - set(partes))]
    return problemas


def partes_fuera_de_la_lista(ruta: Path) -> list[str]:
    sobrantes = sorted(set(partes_del_zip(ruta)) - PARTES_PERMITIDAS)
    return [f"parte fuera de la lista cerrada {nombre}" for nombre in sobrantes]


def textos_fuera_de_la_lista(ruta: Path) -> list[str]:
    """Partes con textos que no son rótulos ni textos de estructura, con cuántos trae cada una."""
    permitidos = {texto.strip() for texto in (*ROTULOS.values(), *TEXTOS_DE_ESTRUCTURA)}
    fuera = Counter(nombre for nombre, datos in partes_del_zip(ruta).items() if nombre.endswith((".xml", ".rels"))
                    for texto in textos_de_un_xml(datos) if texto.strip() not in permitidos)
    return [f"{nombre} trae textos fuera de la lista cerrada ({cantidad})"
            for nombre, cantidad in sorted(fuera.items())]


def hojas_ocultas(ruta: Path) -> list[str]:
    libro = fromstring(partes_del_zip(ruta)["xl/workbook.xml"])
    estados = [h.attrib.get("state", "visible") for h in libro.iter() if nombre_local(h.tag) == "sheet"]
    return [f"hoja {i} en estado {estado}" for i, estado in enumerate(estados) if estado != "visible"]


def propiedades_con_personas(ruta: Path) -> list[str]:
    partes = partes_del_zip(ruta)
    nucleo = {nombre_local(e.tag): (e.text or "").strip() for e in fromstring(partes["docProps/core.xml"])}
    esperado = {"creator": AUTOR, "lastModifiedBy": AUTOR, "created": FECHA_FIJA, "modified": FECHA_FIJA}
    problemas = [f"core.xml {clave}" for clave in sorted(set(nucleo) | set(esperado))
                 if nucleo.get(clave, "") != esperado.get(clave, "")]
    extendidas = {nombre_local(e.tag) for e in fromstring(partes["docProps/app.xml"]).iter() if (e.text or "").strip()}
    problemas += [f"app.xml {clave}" for clave in sorted(extendidas - {"Application", "AppVersion"})]
    with zipfile.ZipFile(ruta) as libro:
        if any(info.date_time != FECHA_DEL_ZIP for info in libro.infolist()):
            problemas.append("partes del zip con fecha distinta de la fija")
    return problemas


def codigos_reales_en_xml(datos: bytes) -> int:
    """Números de exactamente 8 dígitos que no empiezan con 99, en los nodos y en los atributos de texto libre."""
    return sum(1 for texto in textos_de_un_xml(datos) for numero in OCHO_DIGITOS.findall(texto)
               if not numero.startswith("99"))


def codigos_y_correos(ruta: Path) -> list[str]:
    problemas = []
    for nombre, datos in partes_del_zip(ruta).items():
        if CORREO.search(datos.decode("utf-8", errors="ignore")):
            problemas.append(f"{nombre} trae un correo")
        if nombre.endswith((".xml", ".rels", ".vml")) and codigos_reales_en_xml(datos):
            problemas.append(f"{nombre} trae números de 8 dígitos que no empiezan con 99")
    return problemas


def problemas_del_logotipo(ruta: Path) -> list[str]:
    trozos = trozos_png(ruta)
    problemas = [f"trozo {tipo} con metadatos" for tipo in trozos if tipo not in TROZOS_PNG_PERMITIDOS]
    if "no es PNG" not in trozos:
        with Image.open(ruta) as imagen:
            if imagen.size != (176, 173):
                problemas.append("tamaño distinto de 176 × 173 píxeles")
    return problemas


# Copias alteradas para lo que no debe pasar

def copia_con_cambio(tmp_path: Path, cambio: Callable[[Worksheet], None]) -> Path:
    libro = openpyxl.load_workbook(PLANTILLA)
    cambio(libro[HOJA])
    destino = tmp_path / "copia.xlsx"
    libro.save(destino)
    return destino


def copia_con_parte(tmp_path: Path, parte: str, contenido: bytes | None) -> Path:
    """Copia byte a byte de la plantilla con una parte reemplazada, agregada o, con None, quitada."""
    destino = tmp_path / "copia_parte.xlsx"
    with zipfile.ZipFile(PLANTILLA) as origen, zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as copia:
        for nombre in origen.namelist():
            if nombre != parte:
                copia.writestr(origen.getinfo(nombre), origen.read(nombre))
        if contenido is not None:
            copia.writestr(zipfile.ZipInfo(parte, FECHA_DEL_ZIP), contenido)
    return destino


def parte_de_la_plantilla(parte: str) -> bytes:
    return partes_del_zip(PLANTILLA)[parte]


# Pruebas

def test_br_r17_04_la_plantilla_abre_con_openpyxl_con_solo_la_hoja_cursos_de_carrera() -> None:
    assert PLANTILLA.is_file(), "falta plantillas/R017_ambiental_general.xlsx"
    assert openpyxl.load_workbook(PLANTILLA).sheetnames == [HOJA]
    solo_lectura = openpyxl.load_workbook(PLANTILLA, read_only=True, data_only=True)
    assert solo_lectura.sheetnames == [HOJA]
    solo_lectura.close()


def test_br_r17_02_cada_rotulo_esta_en_su_celda_y_la_estructura_se_conserva() -> None:
    assert problemas_de_rotulos(PLANTILLA) == []
    assert problemas_de_estructura(PLANTILLA) == []


def test_br_r17_02_un_rotulo_borrado_o_la_estructura_alterada_se_detectan(tmp_path: Path) -> None:
    def alterar(hoja: Worksheet) -> None:
        hoja["B8"] = None
        hoja.unmerge_cells("D8:I8")
        hoja.column_dimensions["D"].width = 10
        hoja.conditional_formatting = type(hoja.conditional_formatting)()

    copia = copia_con_cambio(tmp_path, alterar)
    assert problemas_de_rotulos(copia) == ["B8 no trae su rótulo"]
    estructura = problemas_de_estructura(copia)
    assert "celdas combinadas que difieren de la fuente (1)" in estructura
    assert "ancho de la columna D" in estructura
    assert "formatos condicionales distintos" in estructura


def test_br_r17_02_las_celdas_del_mapa_estan_vacias_y_combinadas() -> None:
    hoja = hoja_de(PLANTILLA)
    rangos = [*CABECERA.values(), *(r for fila in BLOQUE_I.values() for r in fila),
              *(r for fila in BLOQUE_II.values() for r in fila), *RECUADROS]
    for rango in rangos:
        assert all(hoja[ref].value is None for ref in celdas_de(rango)), rango
        assert ":" not in rango or rango in COMBINADAS, rango
    assert cadenas_fuera_de_la_lista(PLANTILLA) == []


def test_br_r17_02_un_dato_en_una_celda_del_mapa_se_detecta(tmp_path: Path) -> None:
    def llenar(hoja: Worksheet) -> None:
        hoja["D8"] = "450002"
        hoja["D11"] = 410
        hoja["E24"] = 0.636

    assert cadenas_fuera_de_la_lista(copia_con_cambio(tmp_path, llenar)) == [
        "D8 trae un valor fuera de la lista de rótulos",
        "D11 trae un valor fuera de la lista de rótulos",
        "E24 trae un valor fuera de la lista de rótulos",
    ]


def test_br_r17_04_la_plantilla_no_trae_formulas_ni_ref_ni_validaciones() -> None:
    assert problemas_de_formulas(PLANTILLA) == []


def test_br_r17_04_una_formula_un_ref_o_una_validacion_se_detectan(tmp_path: Path) -> None:
    def romper(hoja: Worksheet) -> None:
        hoja["M24"] = "=COUNTIF(F43:F184,1)"
        validacion = DataValidation(type="list", formula1="#REF!")
        validacion.add("F43:F184")
        hoja.add_data_validation(validacion)

    assert problemas_de_formulas(copia_con_cambio(tmp_path, romper)) == [
        "xl/worksheets/sheet1.xml trae #REF!", "M24 trae una fórmula", "la hoja trae 1 validaciones de datos"]
    # Un nombre definido roto vive en xl/workbook.xml, fuera de las celdas.
    nombre = parte_de_la_plantilla("xl/workbook.xml").replace(
        b"<definedNames />", b'<definedNames><definedName name="Lista_inventada">#REF!</definedName></definedNames>')
    assert problemas_de_formulas(copia_con_parte(tmp_path, "xl/workbook.xml", nombre)) == ["xl/workbook.xml trae #REF!"]


def test_br_r17_04_el_logotipo_es_un_png_sin_metadatos_y_la_plantilla_no_lo_trae() -> None:
    assert LOGOTIPO.is_file(), "falta plantillas/R017_logotipo.png"
    assert problemas_del_logotipo(LOGOTIPO) == []
    assert trozos_png(LOGOTIPO)[0] == "IHDR" and trozos_png(LOGOTIPO)[-1] == "IEND"
    # r17.py inserta el logotipo, así que la plantilla no trae dibujos y la salida tiene uno solo.
    assert not [n for n in partes_del_zip(PLANTILLA) if "drawing" in n or "media" in n]


def test_br_r17_04_un_png_con_metadatos_se_detecta(tmp_path: Path) -> None:
    info = PngImagePlugin.PngInfo()
    info.add_text("Author", "Persona Inventada")
    con_texto = tmp_path / "con_texto.png"
    Image.new("RGBA", (176, 173)).save(con_texto, pnginfo=info, dpi=(96, 96))
    assert sorted(problemas_del_logotipo(con_texto)) == ["trozo pHYs con metadatos", "trozo tEXt con metadatos"]


def test_br_r17_05_la_fila_7_queda_libre_para_la_franja_provisional() -> None:
    assert problemas_de_la_franja(PLANTILLA) == []


def test_br_r17_05_una_plantilla_con_la_franja_escrita_se_detecta(tmp_path: Path) -> None:
    def con_franja(hoja: Worksheet) -> None:
        hoja.merge_cells(FRANJA)
        hoja["B7"] = "R-17 PROVISIONAL"

    assert problemas_de_la_franja(copia_con_cambio(tmp_path, con_franja)) == [
        "B7 de la fila 7 trae un valor",
        "la fila 7 trae celdas combinadas",
        "B7 dice PROVISIONAL",
    ]


def test_br_r17_07_propiedades_sin_personas_y_con_fechas_fijas() -> None:
    assert propiedades_con_personas(PLANTILLA) == []


def test_br_r17_07_un_autor_una_empresa_o_una_fecha_en_las_propiedades_se_detectan(tmp_path: Path) -> None:
    nucleo = parte_de_la_plantilla("docProps/core.xml").replace(
        f"<dc:creator>{AUTOR}</dc:creator>".encode(), "<dc:creator>Persona Inventada</dc:creator>".encode())
    assert propiedades_con_personas(copia_con_parte(tmp_path, "docProps/core.xml", nucleo)) == ["core.xml creator"]
    extendidas = parte_de_la_plantilla("docProps/app.xml").replace(
        b"</Properties>", b"<Company>Empresa Inventada</Company><Manager>Persona Inventada</Manager></Properties>")
    assert propiedades_con_personas(copia_con_parte(tmp_path, "docProps/app.xml", extendidas)) == [
        "app.xml Company", "app.xml Manager"]
    fecha = parte_de_la_plantilla("docProps/core.xml").replace(FECHA_FIJA.encode(), b"2025-01-01T08:00:00Z", 1)
    assert propiedades_con_personas(copia_con_parte(tmp_path, "docProps/core.xml", fecha)) == ["core.xml created"]
    # openpyxl guarda con la hora actual en la fecha de modificación y en cada parte del zip.
    assert propiedades_con_personas(copia_con_cambio(tmp_path, lambda hoja: None)) == [
        "core.xml modified", "partes del zip con fecha distinta de la fija"]


def test_br_r17_07_sin_comentarios_vinculos_externos_ni_hojas_ocultas() -> None:
    assert partes_prohibidas(PLANTILLA) == []
    assert hojas_ocultas(PLANTILLA) == []


def test_br_r17_07_un_comentario_un_vinculo_externo_o_una_hoja_oculta_se_detectan(tmp_path: Path) -> None:
    def comentar(hoja: Worksheet) -> None:
        hoja["B8"].comment = Comment("Texto inventado", "Persona Inventada")
        hoja.parent.create_sheet("Oculta").sheet_state = "hidden"

    copia = copia_con_cambio(tmp_path, comentar)
    assert [p for p in partes_prohibidas(copia) if "comment" in p]
    assert hojas_ocultas(copia) == ["hoja 1 en estado hidden"]
    vinculo = parte_de_la_plantilla("xl/_rels/workbook.xml.rels").replace(
        b"</Relationships>",
        b'<Relationship Id="rId99" Target="file:///C:/carpeta/libro.xlsx" TargetMode="External"'
        b' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/externalLinkPath"/>'
        b"</Relationships>")
    assert partes_prohibidas(copia_con_parte(tmp_path, "xl/_rels/workbook.xml.rels", vinculo)) == [
        "xl/_rels/workbook.xml.rels trae un vínculo externo"]
    assert partes_prohibidas(copia_con_parte(tmp_path, "docProps/custom.xml", b"<Properties/>")) == [
        "parte prohibida docProps/custom.xml"]
    assert partes_prohibidas(copia_con_parte(tmp_path, "docProps/app.xml", None)) == ["falta la parte docProps/app.xml"]


def test_br_r17_07_el_zip_trae_solo_las_partes_de_la_lista_cerrada() -> None:
    assert partes_fuera_de_la_lista(PLANTILLA) == []


def test_br_r17_07_una_parte_fuera_de_la_lista_cerrada_se_detecta(tmp_path: Path) -> None:
    # Un caché de tabla dinámica guarda valores, un registro de revisiones guarda autores y una etiqueta
    # de confidencialidad guarda el identificador de la organización.
    for parte in ("xl/pivotCache/pivotCacheRecords1.xml", "xl/revisions/revisionHeaders.xml",
                  "docMetadata/LabelInfo.xml"):
        assert partes_fuera_de_la_lista(copia_con_parte(tmp_path, parte, b"<inventado/>")) == [
            f"parte fuera de la lista cerrada {parte}"]


def test_br_r17_07_cada_texto_de_cada_parte_esta_en_la_lista_cerrada() -> None:
    assert textos_fuera_de_la_lista(PLANTILLA) == []


def test_br_r17_07_un_texto_fuera_de_la_lista_cerrada_en_cualquier_parte_se_detecta(tmp_path: Path) -> None:
    def cabecera_y_hoja(hoja: Worksheet) -> None:
        hoja.oddHeader.center.text = "Persona Inventada"
        hoja.title = "Hoja Inventada"

    # openpyxl pone al guardar la hora actual como fecha de modificación, que tampoco es la fecha fija.
    assert textos_fuera_de_la_lista(copia_con_cambio(tmp_path, cabecera_y_hoja)) == [
        "docProps/core.xml trae textos fuera de la lista cerrada (1)",
        "xl/workbook.xml trae textos fuera de la lista cerrada (1)",
        "xl/worksheets/sheet1.xml trae textos fuera de la lista cerrada (1)",
    ]
    huerfana = (b'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="1" uniqueCount="1">'
                b"<si><t>Persona Inventada</t></si></sst>")
    assert textos_fuera_de_la_lista(copia_con_parte(tmp_path, "xl/sharedStrings.xml", huerfana)) == [
        "xl/sharedStrings.xml trae textos fuera de la lista cerrada (1)"]
    columna = parte_de_la_plantilla("xl/tables/table1.xml").replace(b'name="PROFESOR"', b'name="Persona Inventada"')
    assert textos_fuera_de_la_lista(copia_con_parte(tmp_path, "xl/tables/table1.xml", columna)) == [
        "xl/tables/table1.xml trae textos fuera de la lista cerrada (1)"]
    nombre = parte_de_la_plantilla("xl/workbook.xml").replace(
        b"<definedNames />", b'<definedNames><definedName name="Lista_inventada">#REF!</definedName></definedNames>')
    assert textos_fuera_de_la_lista(copia_con_parte(tmp_path, "xl/workbook.xml", nombre)) == [
        "xl/workbook.xml trae textos fuera de la lista cerrada (2)"]
    titulo = parte_de_la_plantilla("docProps/core.xml").replace(
        b"</cp:coreProperties>", b"<dc:title>Persona Inventada</dc:title></cp:coreProperties>")
    assert textos_fuera_de_la_lista(copia_con_parte(tmp_path, "docProps/core.xml", titulo)) == [
        "docProps/core.xml trae textos fuera de la lista cerrada (1)"]


def test_br_r17_07_ninguna_cadena_del_libro_es_un_dato() -> None:
    assert cadenas_fuera_de_la_lista(PLANTILLA) == []
    assert openpyxl.load_workbook(PLANTILLA)[HOJA].tables[TABLA].displayName == TABLA


def test_br_r17_07_una_cadena_fuera_de_la_lista_o_una_hoja_nueva_se_detectan(tmp_path: Path) -> None:
    def agregar(hoja: Worksheet) -> None:
        hoja["J41"] = "Inventado 01"
        hoja["E43"] = "Estudiante"
        hoja.parent.create_sheet("Base de cursos")

    assert cadenas_fuera_de_la_lista(copia_con_cambio(tmp_path, agregar)) == [
        "hoja con otro nombre en la posición 1",
        "J41 trae un valor fuera de la lista de rótulos",
        "E43 trae un valor fuera de la lista de rótulos",
    ]


def test_br_r17_08_la_tabla_de_estudiantes_tiene_142_filas_vacias_de_la_43_a_la_184() -> None:
    assert problemas_de_la_tabla(PLANTILLA) == []
    _, encabezado, _, ultima = openpyxl.utils.range_boundaries(hoja_de(PLANTILLA).tables[TABLA].ref)
    assert (encabezado, ultima, ultima - encabezado) == (42, 184, 142)


def test_br_r17_08_una_tabla_mas_corta_o_con_datos_se_detecta(tmp_path: Path) -> None:
    def acortar(hoja: Worksheet) -> None:
        hoja.tables[TABLA].ref = "B42:F183"
        hoja.tables[TABLA].autoFilter.ref = "B42:F183"
        hoja["E43"] = "99000001"
        hoja["F43"] = 3

    assert problemas_de_la_tabla(copia_con_cambio(tmp_path, acortar)) == [
        "la tabla no va de B42 a F184", "E43 de la tabla trae un valor", "F43 de la tabla trae un valor"]


def test_regla_2_la_plantilla_no_trae_codigos_reales_ni_correos_en_ninguna_parte() -> None:
    assert codigos_y_correos(PLANTILLA) == []


def test_regla_2_anchos_y_colores_no_cuentan_y_un_codigo_en_un_texto_o_en_un_nombre_si() -> None:
    hoja = b'<worksheet><cols><col min="4" max="4" width="33.42578125"/></cols><sheetData><row r="9">' \
           b'<c r="D9" t="inlineStr"><is><t>20231234</t></is></c></row></sheetData></worksheet>'
    assert codigos_reales_en_xml(hoja) == 1
    assert codigos_reales_en_xml(hoja.replace(b"20231234", b"99000001")) == 0
    # El nombre de una hoja es texto libre; el color 00808080 de los estilos tiene 8 cifras y no es un código.
    assert codigos_reales_en_xml(b'<workbook><sheets><sheet name="20231234" sheetId="1"/></sheets></workbook>') == 1
    assert codigos_reales_en_xml(b'<styleSheet><colors><indexedColors><rgbColor rgb="00808080"/>'
                                 b"</indexedColors></colors></styleSheet>") == 0


def test_regla_2_un_codigo_real_o_un_correo_en_la_plantilla_se_detectan(tmp_path: Path) -> None:
    def con_datos(hoja: Worksheet) -> None:
        hoja["D9"] = "20231234"
        hoja["D10"] = "alguien@example.invalid"

    assert codigos_y_correos(copia_con_cambio(tmp_path, con_datos)) == [
        "xl/worksheets/sheet1.xml trae un correo",
        "xl/worksheets/sheet1.xml trae números de 8 dígitos que no empiezan con 99",
    ]
    nucleo = parte_de_la_plantilla("docProps/core.xml").replace(
        f"<dc:creator>{AUTOR}</dc:creator>".encode(), b"<dc:creator>20231234</dc:creator>")
    assert codigos_y_correos(copia_con_parte(tmp_path, "docProps/core.xml", nucleo)) == [
        "docProps/core.xml trae números de 8 dígitos que no empiezan con 99"]
    columna = parte_de_la_plantilla("xl/tables/table1.xml").replace(b'name="PROFESOR"', b'name="20231234"')
    assert codigos_y_correos(copia_con_parte(tmp_path, "xl/tables/table1.xml", columna)) == [
        "xl/tables/table1.xml trae números de 8 dígitos que no empiezan con 99"]
