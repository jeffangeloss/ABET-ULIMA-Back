"""Pruebas del lector del export de Blackboard (T031 de specs/001-mvp-carga-r17/tasks.md).

Cada prueba nombra en su función la regla de negocio (business rule, BR) de
specs/features/carga-export/carga-export.spec.md que comprueba, con lo que debe pasar y lo que no
debe pasar (AGENTS.md, regla 8). Los libros salen de tests/datos_inventados/ o se arman con openpyxl
y el generador en tmp_path, y ninguna variante con un código fuera de 99 se escribe en esa carpeta.
Los valores esperados son literales del contrato (docs/03-api/contrato.md del Front) y de los
escenarios de carga.feature, o salen de leer el libro con openpyxl por otro camino.
"""

from __future__ import annotations

import io
import random
import re
import shutil
import subprocess
import xml.etree.ElementTree as ElementTree
import zipfile
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import openpyxl.xml
import pytest
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

from abet_carga.lector import MAXIMO_BYTES, huella, leer, nombre_sin_ruta, revisar_tamano
from abet_carga.modelos import ArchivoIlegible, FilaLeida, LibroLeido, MotivoIlegible, TipoColumna

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "tests" / "datos_inventados"

CORRECTO = "sintetico_20262_450002_410.xlsx"
CON_ERROR = "export_inventado_410_con_error.xlsx"
DANADO = "danado_410.xlsx"
PROTEGIDO = "protegido_410.xlsx"
PDF = "pdf_renombrado.xlsx"
HOJA_410 = "gc_SINTETICO_20262_450002_410_f"

# Mensajes del 422 de un archivo ilegible, copiados del contrato y de carga.feature.
MENSAJE_TOPE = "El archivo supera el máximo de 1 MB."
MENSAJE_TIPO = "Solo se admiten exports de Blackboard en formato .xlsx."
MENSAJE_NO_ES_LIBRO = "El contenido del archivo no es un libro de Excel aunque su nombre termine en .xlsx."
MENSAJE_PROTEGIDO = "El archivo está protegido con contraseña. Guárdelo sin contraseña y súbalo."
MENSAJE_MACROS = "El archivo trae macros o vínculos externos y no se admite."
MENSAJE_INFLADO = "El contenido del archivo supera el tamaño admitido al descomprimirse."
MENSAJE_NO_ABRE = "No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard."


# Ayudas de las pruebas

def _bytes(nombre: str) -> bytes:
    return (CARPETA / nombre).read_bytes()


def _ilegible(contenido: bytes, nombre_archivo: str = "export_410.xlsx") -> ArchivoIlegible:
    """Excepción que lanza el lector con ese contenido y ese nombre."""
    with pytest.raises(ArchivoIlegible) as error:
        leer(contenido, nombre_archivo=nombre_archivo)
    return error.value


def _partes(datos: bytes) -> list[tuple[zipfile.ZipInfo, bytes]]:
    with zipfile.ZipFile(io.BytesIO(datos)) as libro:
        return [(parte, libro.read(parte)) for parte in libro.infolist()]


def _parte(datos: bytes, nombre: str) -> bytes:
    """Contenido de una parte del libro."""
    return dict((parte.filename, contenido) for parte, contenido in _partes(datos))[nombre]


def _con_fila_al_final(datos: bytes, fila: bytes) -> bytes:
    """Copia del libro con el XML de una fila más al final de la hoja."""
    hoja = _parte(datos, "xl/worksheets/sheet1.xml")
    return _con_parte_reemplazada(datos, "xl/worksheets/sheet1.xml", hoja.replace(b"</sheetData>", fila + b"</sheetData>"))


def _zip(partes: Iterable[tuple[str, bytes, int]]) -> bytes:
    """Zip con las partes dadas, cada una con su nombre, su contenido y su compresión."""
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w") as destino:
        for nombre, contenido, compresion in partes:
            destino.writestr(zipfile.ZipInfo(nombre, date_time=(2026, 10, 28, 8, 0, 0)), contenido, compresion)
    return salida.getvalue()


def _con_partes(datos: bytes, extra: Iterable[tuple[str, bytes, int]]) -> bytes:
    """Copia del libro con sus partes y las partes extra al final."""
    propias = [(p.filename, contenido, p.compress_type) for p, contenido in _partes(datos)]
    return _zip([*propias, *extra])


def _con_parte_reemplazada(datos: bytes, nombre: str, contenido: bytes) -> bytes:
    """Copia del libro con otro contenido en la parte dada."""
    return _zip(
        (p.filename, contenido if p.filename == nombre else original, p.compress_type)
        for p, original in _partes(datos)
    )


def _con_relleno_hasta(datos: bytes, total: int) -> bytes:
    """Copia del libro con una parte de bytes al azar sin comprimir que lo deja en total bytes."""
    vacio = _con_partes(datos, [("xl/media/relleno.bin", b"", zipfile.ZIP_STORED)])
    relleno = random.Random(410).randbytes(total - len(vacio))
    resultado = _con_partes(datos, [("xl/media/relleno.bin", relleno, zipfile.ZIP_STORED)])
    assert len(resultado) == total
    return resultado


def _contenido_que_se_infla(megas: int) -> bytes:
    """Bloques de 128 bytes elegidos al azar entre 64 patrones, con proporción de compresión cercana a 25."""
    azar = random.Random(20262)
    patrones = [azar.randbytes(128) for _ in range(64)]
    return b"".join(azar.choice(patrones) for _ in range(megas * 1_048_576 // 128))


def _export(generador: ModuleType) -> object:
    plantilla, _ = generador.leer_plantilla()
    return generador.export_410(plantilla)


def _escrito(generador: ModuleType, export: object, tmp_path: Path, nombre: str = "copia.xlsx") -> bytes:
    """Escribe el export en tmp_path con el generador y devuelve sus bytes."""
    return generador.escribir(export, tmp_path / nombre).read_bytes()


def _con_encabezado(generador: ModuleType, export: object, columna: str, nuevo: str) -> object:
    encabezado = list(export.encabezado)
    encabezado[export.indice(columna)] = nuevo
    return generador.Export(export.hoja, tuple(encabezado), export.filas)


def _libro_con_filas(
    export: object,
    filas: dict[int, tuple[object, ...]],
    con_formato: Iterable[int] = (),
    celdas: dict[tuple[int, int], object] | None = None,
) -> bytes:
    """Libro de openpyxl con el encabezado del export y las filas dadas por número.

    con_formato pone celdas A con formato y sin valor, y celdas suma celdas sueltas por (fila, columna).
    """
    libro = Workbook()
    hoja = libro.active
    hoja.title = export.hoja
    for columna, valor in enumerate(export.encabezado, start=1):
        hoja.cell(row=1, column=columna, value=valor)
    for numero, valores in filas.items():
        for columna, valor in enumerate(valores, start=1):
            hoja.cell(row=numero, column=columna, value=valor)
    for numero in con_formato:
        hoja.cell(row=numero, column=1).font = Font(bold=True)
    for (numero, columna), valor in (celdas or {}).items():
        hoja.cell(row=numero, column=columna, value=valor)
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _valores_de_columnas(nombre: str, columnas: Iterable[str]) -> list[object]:
    """Valores no vacíos de las columnas dadas, leídos con openpyxl sin el lector."""
    libro = load_workbook(CARPETA / nombre, read_only=True, data_only=True)
    try:
        filas = list(libro.worksheets[0].iter_rows(values_only=True))
    finally:
        libro.close()
    encabezado = [str(celda) for celda in filas[0]]
    posiciones = [i for i, texto in enumerate(encabezado) if any(texto.startswith(c) for c in columnas)]
    return [fila[i] for fila in filas[1:] for i in posiciones if fila[i] is not None]


# BR-CARGA-04. Tope de 1 MB antes de leer

def test_br_carga_04_un_libro_de_1_mb_exacto_se_lee() -> None:
    contenido = _con_relleno_hasta(_bytes(CORRECTO), 1_048_576)
    revisar_tamano(contenido)
    assert leer(contenido, nombre_archivo=CORRECTO).filas_de_datos == 11


@pytest.mark.parametrize("total", [1_048_577, 1_258_291], ids=["un_byte_mas", "1_2_mb"])
def test_br_carga_04_un_libro_de_mas_de_1_mb_se_rechaza_antes_de_leerse(total: int) -> None:
    # El ejemplo de carga.feature es un .xlsx inventado de 1,2 MB con los códigos 99000001 a 99000011.
    contenido = _con_relleno_hasta(_bytes(CORRECTO), total)
    with pytest.raises(ArchivoIlegible) as error:
        revisar_tamano(contenido)
    assert error.value.motivo is MotivoIlegible.ARCHIVO_DEMASIADO_GRANDE
    assert _ilegible(contenido).mensaje == MENSAJE_TOPE


def test_br_carga_03_el_tope_se_revisa_antes_que_el_nombre_y_el_contenido() -> None:
    pdf_grande = _bytes(PDF) + b"%" * MAXIMO_BYTES
    assert _ilegible(pdf_grande, "export_410.pdf").motivo is MotivoIlegible.ARCHIVO_DEMASIADO_GRANDE


# BR-CARGA-05. Archivo ilegible, con un motivo de una lista cerrada

def test_br_carga_05_el_export_correcto_se_lee() -> None:
    libro = leer(_bytes(CORRECTO), nombre_archivo=CORRECTO)
    assert isinstance(libro, LibroLeido)
    assert libro.hoja == HOJA_410
    assert libro.nombre_archivo == CORRECTO
    assert libro.filas_de_datos == 11
    assert [fila.fila_origen for fila in libro.filas] == list(range(2, 13))
    assert [fila.codigo for fila in libro.filas] == list(range(99000001, 99000012))


@pytest.mark.parametrize(
    "nombre", ["export_410.pdf", "export_410.xls", "export_410.xlsm", "export_410.csv", "export_410"]
)
def test_br_carga_05_un_nombre_que_no_termina_en_xlsx_no_se_admite(nombre: str) -> None:
    # El nombre se revisa antes que el contenido, así que el export correcto con otro nombre tampoco pasa.
    for contenido in (_bytes(PDF), _bytes(CORRECTO)):
        error = _ilegible(contenido, nombre)
        assert error.motivo is MotivoIlegible.TIPO_NO_ADMITIDO
        assert error.mensaje == MENSAJE_TIPO


def test_br_carga_05_la_extension_xlsx_se_admite_en_mayusculas() -> None:
    assert leer(_bytes(CORRECTO), nombre_archivo="EXPORT_410.XLSX").filas_de_datos == 11


def test_br_carga_05_un_pdf_con_nombre_xlsx_no_es_un_libro() -> None:
    error = _ilegible(_bytes(PDF), "export_410.xlsx")
    assert error.motivo is MotivoIlegible.CONTENIDO_NO_ES_LIBRO
    assert error.mensaje == MENSAJE_NO_ES_LIBRO


def test_br_carga_05_un_libro_protegido_con_contrasena_se_reconoce() -> None:
    error = _ilegible(_bytes(PROTEGIDO), PROTEGIDO)
    assert error.motivo is MotivoIlegible.PROTEGIDO_CON_CONTRASENA
    assert error.mensaje == MENSAJE_PROTEGIDO


def test_br_carga_05_un_contenedor_ole_sin_cifrado_no_pasa_por_protegido() -> None:
    # Un .xls de Excel 97 renombrado también empieza con la firma D0 CF 11 E0, pero no trae los
    # flujos EncryptionInfo y EncryptedPackage de un libro cifrado.
    xls = bytes.fromhex("D0CF11E0A1B11AE1") + bytes(504)
    assert _ilegible(xls).motivo is MotivoIlegible.CONTENIDO_NO_ES_LIBRO


@pytest.mark.parametrize(
    "partes",
    [
        [("documento.txt", b"Texto inventado.", zipfile.ZIP_DEFLATED)],
        [
            ("[Content_Types].xml", b"<Types/>", zipfile.ZIP_DEFLATED),
            ("word/document.xml", b"<w/>", zipfile.ZIP_DEFLATED),
        ],
    ],
    ids=["zip_con_texto", "documento_de_word"],
)
def test_br_carga_05_un_zip_que_no_es_un_libro_de_excel_no_se_admite(partes: list[tuple[str, bytes, int]]) -> None:
    assert _ilegible(_zip(partes)).motivo is MotivoIlegible.CONTENIDO_NO_ES_LIBRO


def test_br_carga_05_un_zip_cortado_a_la_mitad_no_abre() -> None:
    error = _ilegible(_bytes(DANADO), DANADO)
    assert error.motivo is MotivoIlegible.NO_SE_PUDO_ABRIR
    assert error.mensaje == MENSAJE_NO_ABRE


def test_br_carga_05_un_archivo_vacio_no_abre() -> None:
    assert _ilegible(b"").motivo is MotivoIlegible.NO_SE_PUDO_ABRIR


def test_br_carga_05_un_libro_con_el_xml_roto_no_abre() -> None:
    roto = _con_parte_reemplazada(_bytes(CORRECTO), "xl/workbook.xml", b"<workbook xmlns=")
    assert _ilegible(roto).motivo is MotivoIlegible.NO_SE_PUDO_ABRIR


def test_br_carga_05_una_celda_en_la_ultima_fila_de_excel_se_lee() -> None:
    # La fila 1 048 576 es la última de Excel. Una celda con formato y sin valor no suma filas de datos.
    contenido = _con_fila_al_final(_bytes(CORRECTO), b'<row r="1048576"><c r="A1048576" s="0"/></row>')
    assert leer(contenido, nombre_archivo=CORRECTO).filas_de_datos == 11


def test_br_carga_05_una_fila_despues_de_la_ultima_de_excel_no_abre() -> None:
    # openpyxl rellena con filas vacías el salto hasta una fila lejana, así que una sola celda en la
    # fila 2 000 000 000 haría recorrer al lector dos mil millones de filas en un archivo de 6 KB.
    fila = b'<row r="1048577"><c r="A1048577" t="inlineStr"><is><t>x</t></is></c></row>'
    error = _ilegible(_con_fila_al_final(_bytes(CORRECTO), fila))
    assert (error.motivo, error.mensaje) == (MotivoIlegible.NO_SE_PUDO_ABRIR, MENSAJE_NO_ABRE)


@pytest.mark.parametrize("fila", [1, 2], ids=["encabezado", "fila_de_datos"])
def test_br_carga_05_una_celda_en_la_ultima_columna_de_excel_se_lee(generador: ModuleType, fila: int) -> None:
    # XFD, la columna 16 384, es la última de Excel.
    export = _export(generador)
    contenido = _libro_con_filas(export, dict(enumerate(export.filas, start=2)), celdas={(fila, 16_384): "Relleno"})
    libro = leer(contenido, nombre_archivo=CORRECTO)
    assert libro.filas_de_datos == 11
    assert [c.posicion for c in libro.columnas_pi] == [25, 26, 27]


@pytest.mark.parametrize("fila", [1, 2], ids=["encabezado", "fila_de_datos"])
def test_br_carga_05_una_celda_despues_de_la_ultima_columna_de_excel_no_abre(generador: ModuleType, fila: int) -> None:
    # openpyxl lee hasta la columna ZZZ, y un PI más allá de la 32 767 desbordaría carga_columna.posicion,
    # que es smallint.
    export = _export(generador)
    contenido = _libro_con_filas(export, dict(enumerate(export.filas, start=2)), celdas={(fila, 16_385): "Relleno"})
    assert _ilegible(contenido).motivo is MotivoIlegible.NO_SE_PUDO_ABRIR


@pytest.mark.parametrize(
    "parte",
    ["xl/vbaProject.bin", "xl/externalLinks/externalLink1.xml", "XL/EXTERNALLINKS/externalLink2.xml"],
    ids=["macros", "vinculo_externo", "vinculo_en_mayusculas"],
)
def test_br_carga_05_macros_o_vinculos_externos_no_se_admiten(parte: str) -> None:
    contenido = _con_partes(_bytes(CORRECTO), [(parte, b"<externalLink/>", zipfile.ZIP_DEFLATED)])
    error = _ilegible(contenido)
    assert error.motivo is MotivoIlegible.MACROS_O_VINCULOS
    assert error.mensaje == MENSAJE_MACROS


_TIPO_VBA = "application/vnd.ms-office.vbaProject"
_TIPO_VINCULO = "application/vnd.openxmlformats-officedocument.spreadsheetml.externalLink+xml"
_RELACION_VINCULO = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/externalLink"


def _con_tipo_declarado(datos: bytes, declaracion: str, parte: str) -> bytes:
    """Copia del libro con una parte extra y su declaración al final de [Content_Types].xml."""
    tipos = dict((p.filename, c) for p, c in _partes(datos))["[Content_Types].xml"]
    tipos = tipos.replace(b"</Types>", declaracion.encode() + b"</Types>")
    return _con_partes(_con_parte_reemplazada(datos, "[Content_Types].xml", tipos), [(parte, b"<x/>", zipfile.ZIP_DEFLATED)])


@pytest.mark.parametrize(
    ("declaracion", "parte"),
    [
        (f'<Override PartName="/xl/codigo.bin" ContentType="{_TIPO_VBA}"/>', "xl/codigo.bin"),
        (f'<Default Extension="dat" ContentType="{_TIPO_VBA}"/>', "xl/codigo.dat"),
        (f'<Override PartName="/xl/otros/v1.xml" ContentType="{_TIPO_VINCULO.upper()}"/>', "xl/otros/v1.xml"),
    ],
    ids=["macros_con_otro_nombre", "macros_por_extension", "vinculo_en_otra_carpeta"],
)
def test_br_carga_05_macros_o_vinculos_declarados_por_su_tipo_no_se_admiten(declaracion: str, parte: str) -> None:
    # El nombre de la parte no decide; Excel la reconoce por el tipo que declara [Content_Types].xml.
    error = _ilegible(_con_tipo_declarado(_bytes(CORRECTO), declaracion, parte))
    assert (error.motivo, error.mensaje) == (MotivoIlegible.MACROS_O_VINCULOS, MENSAJE_MACROS)


def test_br_carga_05_un_vinculo_externo_enlazado_desde_el_libro_no_se_admite() -> None:
    datos = _bytes(CORRECTO)
    relaciones = dict((p.filename, c) for p, c in _partes(datos))["xl/_rels/workbook.xml.rels"]
    relacion = f'<Relationship Type="{_RELACION_VINCULO}" Target="otros/v1.xml" Id="rId99"/>'
    relaciones = relaciones.replace(b"</Relationships>", relacion.encode() + b"</Relationships>")
    error = _ilegible(_con_parte_reemplazada(datos, "xl/_rels/workbook.xml.rels", relaciones))
    assert (error.motivo, error.mensaje) == (MotivoIlegible.MACROS_O_VINCULOS, MENSAJE_MACROS)


def test_br_carga_05_un_tipo_de_contenido_comun_no_detiene_el_libro() -> None:
    # Una parte extra con un tipo ajeno a macros y vínculos no cambia la lectura.
    declaracion = '<Override PartName="/xl/otros/nota.xml" ContentType="application/xml"/>'
    libro = leer(_con_tipo_declarado(_bytes(CORRECTO), declaracion, "xl/otros/nota.xml"), nombre_archivo=CORRECTO)
    assert libro.filas_de_datos == 11


def test_br_carga_05_un_libro_que_pasa_de_20_mb_al_descomprimirse_se_rechaza() -> None:
    contenido = _con_partes(
        _bytes(CORRECTO), [("xl/media/inflado.bin", _contenido_que_se_infla(22), zipfile.ZIP_DEFLATED)]
    )
    # Menos de 1 MB comprimido y ninguna parte con proporción de bomba, así que lo detiene la suma.
    assert len(contenido) < 1_048_576
    with zipfile.ZipFile(io.BytesIO(contenido)) as libro:
        assert sum(p.file_size for p in libro.infolist()) > 20 * 1_048_576
        assert max(p.file_size / p.compress_size for p in libro.infolist()) < 100
    error = _ilegible(contenido)
    assert error.motivo is MotivoIlegible.CONTENIDO_INFLADO
    assert error.mensaje == MENSAJE_INFLADO


def test_br_carga_05_un_libro_de_menos_de_20_mb_descomprimido_se_lee() -> None:
    contenido = _con_partes(
        _bytes(CORRECTO), [("xl/media/inflado.bin", _contenido_que_se_infla(19), zipfile.ZIP_DEFLATED)]
    )
    assert leer(contenido, nombre_archivo=CORRECTO).filas_de_datos == 11


def test_br_carga_05_una_parte_con_proporcion_de_bomba_se_rechaza() -> None:
    # 1,8 MB de texto repetido que se comprime unas 600 veces, muy lejos de un export real.
    contenido = _con_partes(_bytes(CORRECTO), [("xl/media/bomba.xml", b"<row/>" * 300_000, zipfile.ZIP_DEFLATED)])
    assert _ilegible(contenido).motivo is MotivoIlegible.CONTENIDO_INFLADO


def test_br_carga_05_una_parte_pequena_y_muy_comprimible_se_admite() -> None:
    # Por debajo de 100 KiB la proporción no se revisa, porque una parte pequeña no infla nada.
    contenido = _con_partes(_bytes(CORRECTO), [("xl/media/repetido.xml", b"<row/>" * 15_000, zipfile.ZIP_DEFLATED)])
    assert leer(contenido, nombre_archivo=CORRECTO).filas_de_datos == 11


def test_br_carga_05_hasta_100_partes_se_lee_y_con_101_no() -> None:
    datos = _bytes(CORRECTO)
    propias = len(_partes(datos))
    extra = [(f"xl/media/parte{n:03d}.bin", b"", zipfile.ZIP_STORED) for n in range(100 - propias)]
    assert leer(_con_partes(datos, extra), nombre_archivo=CORRECTO).filas_de_datos == 11
    demasiadas = [*extra, ("xl/media/parte_de_mas.bin", b"", zipfile.ZIP_STORED)]
    assert _ilegible(_con_partes(datos, demasiadas)).motivo is MotivoIlegible.CONTENIDO_INFLADO


def test_br_carga_05_una_entidad_declarada_en_el_xml_no_se_expande() -> None:
    hoja = (
        b'<?xml version="1.0"?><!DOCTYPE worksheet [<!ENTITY inventado "Inventado 99">]>'
        b'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
        b'<row r="1"><c r="A1" t="inlineStr"><is><t>&inventado;</t></is></c></row></sheetData></worksheet>'
    )
    # La biblioteca estándar expandiría la entidad. defusedxml la prohíbe, y el lector no abre el libro.
    assert ElementTree.fromstring(hoja).findtext(".//{*}t") == "Inventado 99"
    con_entidad = _con_parte_reemplazada(_bytes(CORRECTO), "xl/worksheets/sheet1.xml", hoja)
    assert _ilegible(con_entidad).motivo is MotivoIlegible.NO_SE_PUDO_ABRIR


def test_br_carga_05_el_lector_corre_con_defusedxml() -> None:
    # Esta prueba falla si openpyxl no encuentra defusedxml, por ejemplo sin el paquete o con
    # OPENPYXL_DEFUSEDXML=False, porque entonces el lector no abre ningún archivo.
    assert openpyxl.xml.DEFUSEDXML is True
    assert leer(_bytes(CORRECTO), nombre_archivo=CORRECTO).filas_de_datos == 11


def test_br_carga_05_sin_defusedxml_el_lector_no_abre_ningun_archivo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(openpyxl.xml, "DEFUSEDXML", False)
    with pytest.raises(RuntimeError, match="defusedxml"):
        leer(_bytes(CORRECTO), nombre_archivo=CORRECTO)


def test_br_carga_05_cada_motivo_tiene_el_mensaje_del_contrato() -> None:
    assert {motivo.name: motivo.mensaje for motivo in MotivoIlegible} == {
        "ARCHIVO_DEMASIADO_GRANDE": MENSAJE_TOPE,
        "TIPO_NO_ADMITIDO": MENSAJE_TIPO,
        "CONTENIDO_NO_ES_LIBRO": MENSAJE_NO_ES_LIBRO,
        "PROTEGIDO_CON_CONTRASENA": MENSAJE_PROTEGIDO,
        "MACROS_O_VINCULOS": MENSAJE_MACROS,
        "CONTENIDO_INFLADO": MENSAJE_INFLADO,
        "NO_SE_PUDO_ABRIR": MENSAJE_NO_ABRE,
    }


# BR-CARGA-06. Huella SHA-256 de los bytes recibidos

def test_br_carga_06_la_huella_es_la_de_shasum() -> None:
    comando = (["shasum", "-a", "256"] if shutil.which("shasum") else ["sha256sum"]) + [str(CARPETA / CORRECTO)]
    if shutil.which(comando[0]) is None:
        pytest.skip("No hay shasum ni sha256sum en este sistema.")
    esperada = subprocess.run(comando, capture_output=True, text=True, check=True).stdout.split()[0]
    assert re.fullmatch(r"[0-9a-f]{64}", esperada)
    assert huella(_bytes(CORRECTO)) == esperada


def test_br_carga_06_un_libro_abierto_y_guardado_otra_vez_es_otro_archivo(tmp_path: Path) -> None:
    libro = load_workbook(CARPETA / CORRECTO)
    libro.save(tmp_path / "guardado_otra_vez.xlsx")
    copia = (tmp_path / "guardado_otra_vez.xlsx").read_bytes()
    assert huella(copia) != huella(_bytes(CORRECTO))
    # Las celdas que importan son las mismas, así que la huella mira los bytes y no el contenido leído.
    assert leer(copia, nombre_archivo=CORRECTO).filas == leer(_bytes(CORRECTO), nombre_archivo=CORRECTO).filas


# BR-CARGA-11. Nombre de la hoja, que archivo_origen.hoja guarda con 100 caracteres como máximo

@pytest.mark.parametrize("largo", [31, 100, 101, 160])
def test_br_carga_11_la_hoja_se_lee_entera_hasta_el_ancho_de_archivo_origen(largo: int) -> None:
    # Excel no pasa de 31 caracteres, pero openpyxl lee el nombre que traiga xl/workbook.xml, y uno de
    # más de 100 caracteres chocaría con archivo_origen.hoja, que es varchar(100).
    nombre = (HOJA_410 + "z" * 200)[:largo]
    datos = _bytes(CORRECTO)
    libro_xml = _parte(datos, "xl/workbook.xml").replace(f'name="{HOJA_410}"'.encode(), f'name="{nombre}"'.encode())
    libro = leer(_con_parte_reemplazada(datos, "xl/workbook.xml", libro_xml), nombre_archivo=CORRECTO)
    assert libro.hoja == nombre[:100]
    assert libro.filas_de_datos == 11


# BR-CARGA-14. Columnas de código y de indicadores de desempeño (performance indicators, PI)

def test_br_carga_14_el_lector_clasifica_las_columnas_del_export() -> None:
    libro = leer(_bytes(CORRECTO), nombre_archivo=CORRECTO)
    assert len(libro.columnas) == 27
    assert [c.posicion for c in libro.columnas] == list(range(1, 28))
    por_tipo = {tipo: [c.encabezado for c in libro.columnas if c.tipo is tipo] for tipo in TipoColumna}
    assert por_tipo[TipoColumna.CODIGO] == ["Username"]
    assert [c.posicion for c in libro.columnas_pi] == [25, 26, 27]
    assert [(c.pi_codigo, c.bb_columna_id, c.puntaje_maximo_declarado) for c in libro.columnas_pi] == [
        ("5.1", "9000051", Decimal(4)),
        ("5.2", "9000052", Decimal(4)),
        ("5.3", "9000053", Decimal(20)),
    ]
    assert libro.columnas_pi[0].encabezado == "5.1 [Total Pts: 4 Score] |9000051"
    # Student ID queda como columna cualquiera porque el código sale de Username.
    assert "Student ID" in por_tipo[TipoColumna.OTRA]
    assert "Actividad 01 [Total Pts: 20 Complete/Incomplete] |9000101" in por_tipo[TipoColumna.OTRA]
    assert libro.columna_codigo is not None and libro.columna_codigo.posicion == 3


@pytest.mark.parametrize(
    ("encabezado", "tipo", "pi", "bb", "puntaje"),
    [
        ("6.10 [Total Pts: 4 Score] |9000610", TipoColumna.PI, "6.10", "9000610", Decimal(4)),
        ("5.1 [Total Pts: 4.00 Score] |9000051", TipoColumna.PI, "5.1", "9000051", Decimal(4)),
        ("5.1 [Total Pts: up to 4 Score]", TipoColumna.PI, "5.1", None, Decimal(4)),
        ("5.1 [Sin puntaje]", TipoColumna.PI, "5.1", None, None),
        ("5.1[Total Pts: 4 Score] |9000051", TipoColumna.OTRA, None, None, None),
        ("Nota 5.1 [Total Pts: 4 Score] |9000051", TipoColumna.OTRA, None, None, None),
        ("Actividad 01 [Total Pts: 4 Score] |9000101", TipoColumna.OTRA, None, None, None),
        ("5 [Total Pts: 4 Score] |9000005", TipoColumna.OTRA, None, None, None),
    ],
)
def test_br_carga_14_un_encabezado_es_de_pi_si_empieza_por_numero_punto_numero_y_corchete(
    generador: ModuleType,
    tmp_path: Path,
    encabezado: str,
    tipo: TipoColumna,
    pi: str | None,
    bb: str | None,
    puntaje: Decimal | None,
) -> None:
    export = _con_encabezado(generador, _export(generador), "5.1", encabezado)
    columna = leer(_escrito(generador, export, tmp_path), nombre_archivo=CORRECTO).columnas[24]
    assert (columna.tipo, columna.pi_codigo, columna.bb_columna_id, columna.puntaje_maximo_declarado) == (
        tipo,
        pi,
        bb,
        puntaje,
    )
    assert columna.declara_puntaje is (puntaje is not None)


@pytest.mark.parametrize(
    ("total", "puntaje"),
    [
        ("0", None),
        ("0.004", None),
        ("0.01", Decimal("0.01")),
        ("4,5", Decimal("4.50")),
        ("9999.99", Decimal("9999.99")),
        ("9999.996", None),
        ("10000", None),
    ],
)
def test_br_carga_14_un_puntaje_que_la_base_no_admite_queda_sin_valor(
    generador: ModuleType, tmp_path: Path, total: str, puntaje: Decimal | None
) -> None:
    # carga_columna.puntaje_maximo_declarado es numeric(6, 2) y mayor que 0, y la base redondea a dos
    # decimales, así que 9999.996 pasaría a 10000.00 y 0.004 a 0.00. El encabezado sigue declarando un
    # Total Pts, y la validación deja por eso el aviso PUNTAJE_MAXIMO_DISTINTO.
    export = _con_encabezado(generador, _export(generador), "5.1", f"5.1 [Total Pts: {total} Score] |9000051")
    columna = leer(_escrito(generador, export, tmp_path), nombre_archivo=CORRECTO).columnas_pi[0]
    assert (columna.pi_codigo, columna.puntaje_maximo_declarado, columna.declara_puntaje) == ("5.1", puntaje, True)


def test_br_carga_14_un_numero_de_blackboard_de_mas_de_12_cifras_queda_sin_declarar(
    generador: ModuleType, tmp_path: Path
) -> None:
    # carga_columna.bb_columna_id admite de 1 a 12 cifras (ck_carga_columna_bb).
    export = _con_encabezado(generador, _export(generador), "5.1", "5.1 [Total Pts: 4 Score] |1234567890123")
    columna = leer(_escrito(generador, export, tmp_path), nombre_archivo=CORRECTO).columnas_pi[0]
    assert (columna.pi_codigo, columna.bb_columna_id) == ("5.1", None)


def test_br_carga_15_una_fila_que_termina_antes_que_el_encabezado_se_completa_con_vacias(
    generador: ModuleType, tmp_path: Path
) -> None:
    # openpyxl no escribe la celda final vacía, así que la fila 3 llega más corta que el encabezado.
    export = generador.con_celda(_export(generador), 3, "5.3", None)
    contenido = _escrito(generador, export, tmp_path)
    assert b'r="AA3"' not in dict((p.filename, c) for p, c in _partes(contenido))["xl/worksheets/sheet1.xml"]
    fila = leer(contenido, nombre_archivo=CORRECTO).filas[1]
    assert (fila.fila_origen, fila.codigo, fila.valores_pi) == (3, 99000002, (4, 3, None))


def test_br_carga_14_un_encabezado_largo_se_corta_en_200_caracteres(generador: ModuleType, tmp_path: Path) -> None:
    largo = "5.1 [Total Pts: 4 Score] " + "x" * 300 + " |9000051"
    export = _con_encabezado(generador, _export(generador), "5.1", largo)
    columna = leer(_escrito(generador, export, tmp_path), nombre_archivo=CORRECTO).columnas_pi[0]
    assert columna.encabezado == largo[:200]
    assert (columna.pi_codigo, columna.bb_columna_id) == ("5.1", "9000051")


# BR-CARGA-07 y BR-CARGA-15. Columna de la que sale el código

def test_br_carga_15_sin_username_el_codigo_sale_de_student_id(generador: ModuleType, tmp_path: Path) -> None:
    export = _export(generador)
    for fila in range(2, 13):
        export = generador.con_celda(export, fila, "Student ID", str(99000100 + fila))
    export = generador.sin_columnas(export, "Username")
    libro = leer(_escrito(generador, export, tmp_path), nombre_archivo=CORRECTO)
    assert libro.columna_codigo is not None and libro.columna_codigo.encabezado == "Student ID"
    assert [fila.codigo for fila in libro.filas] == [str(99000100 + n) for n in range(2, 13)]


def test_br_carga_17_con_username_los_valores_de_student_id_se_descartan(
    generador: ModuleType, tmp_path: Path
) -> None:
    export = generador.con_celda(_export(generador), 4, "Student ID", "99000999")
    libro = leer(_escrito(generador, export, tmp_path), nombre_archivo=CORRECTO)
    assert libro.columna_codigo is not None and libro.columna_codigo.encabezado == "Username"
    assert all("99000999" not in (fila.codigo, *fila.valores_pi) for fila in libro.filas)


def test_br_carga_13_sin_username_ni_student_id_no_hay_columna_de_codigo() -> None:
    libro = leer(_bytes("sin_username_ni_student_id_410.xlsx"), nombre_archivo=CORRECTO)
    assert libro.columna_codigo is None
    assert all(fila.codigo is None for fila in libro.filas)


# BR-CARGA-16. Filas de datos

def test_br_carga_16_las_filas_vacias_del_final_no_cuentan(generador: ModuleType) -> None:
    export = _export(generador)
    contenido = _libro_con_filas(export, dict(enumerate(export.filas, start=2)), con_formato=(13, 14, 15))
    libro = leer(contenido, nombre_archivo=CORRECTO)
    assert libro.filas_de_datos == 11
    assert libro.filas[-1].fila_origen == 12


def test_br_carga_16_una_fila_vacia_entre_filas_con_datos_cuenta_con_su_numero(generador: ModuleType) -> None:
    # fila_origen es la fila del archivo, y la consulta de control Q12 exige que no pase de
    # filas_de_datos + 1, así que la fila 12 vacía cuenta y la validación la rechaza por código vacío.
    export = _export(generador)
    filas = dict(enumerate(export.filas, start=2))
    filas[13] = filas.pop(12)
    libro = leer(_libro_con_filas(export, filas), nombre_archivo=CORRECTO)
    assert libro.filas_de_datos == 12
    assert [fila.fila_origen for fila in libro.filas] == list(range(2, 14))
    vacia = libro.filas[10]
    assert (vacia.fila_origen, vacia.codigo, vacia.valores_pi) == (12, None, (None, None, None))


def test_br_carga_16_una_dimension_equivocada_no_corta_columnas_ni_filas() -> None:
    datos = _bytes(CORRECTO)
    hoja = dict((p.filename, c) for p, c in _partes(datos))["xl/worksheets/sheet1.xml"]
    assert b'<dimension ref="A1:AA12" />' in hoja
    corta = _con_parte_reemplazada(datos, "xl/worksheets/sheet1.xml", hoja.replace(b"A1:AA12", b"A1:B2"))
    libro = leer(corta, nombre_archivo=CORRECTO)
    assert (len(libro.columnas), libro.filas_de_datos) == (27, 11)


def test_br_carga_13_un_libro_con_el_encabezado_y_sin_filas_no_tiene_filas_de_datos() -> None:
    libro = leer(_bytes("vacio_410.xlsx"), nombre_archivo=CORRECTO)
    assert (len(libro.columnas), libro.filas_de_datos) == (27, 0)


# BR-CARGA-17. Descarte de nombres, accesos, actividades y valores leídos

def test_br_carga_17_el_libro_leido_no_guarda_nombres_accesos_ni_actividades() -> None:
    columnas = ("Last Name", "First Name", "Last Access", "Availability", "Actividad")
    descartados = _valores_de_columnas(CON_ERROR, columnas)
    textos = {v for v in descartados if not isinstance(v, (int, float))}
    assert {"Inventado 01", "Estudiante", "Yes", "Complete", "Needs Grading"} <= textos
    libro = leer(_bytes(CON_ERROR), nombre_archivo=CON_ERROR)
    guardados = [valor for fila in libro.filas for valor in (fila.codigo, *fila.valores_pi)]
    # Cada fila conserva solo el código y los tres PI.
    assert len(guardados) == 11 * 4
    assert not textos & {v for v in guardados if not isinstance(v, (int, float))}
    # Los encabezados de las actividades dicen «Complete/Incomplete», así que las filas se miran aparte.
    assert not any(texto in repr(libro) for texto in ("Inventado", "Estudiante", "datetime"))
    assert not any(texto in repr(libro.filas) for texto in ("Inventado", "Estudiante", "Complete", "datetime", "Yes"))


def test_br_carga_17_la_representacion_de_una_fila_no_muestra_el_codigo_ni_los_valores() -> None:
    fila = leer(_bytes(CON_ERROR), nombre_archivo=CON_ERROR).filas[1]
    assert isinstance(fila, FilaLeida)
    assert (fila.fila_origen, fila.codigo, fila.valores_pi) == (3, 99000002, (4, 5, 4))
    assert repr(fila) == "FilaLeida(fila_origen=3)"


@pytest.mark.parametrize(
    ("enviado", "guardado"),
    [
        (r"C:\Users\docente\Descargas\export_inventado_410_con_error.xlsx", "export_inventado_410_con_error.xlsx"),
        ("/home/docente/Descargas/export_inventado_410_con_error.xlsx", "export_inventado_410_con_error.xlsx"),
        ("export_inventado_410_con_error.xlsx", "export_inventado_410_con_error.xlsx"),
    ],
    ids=["windows", "unix", "sin_ruta"],
)
def test_br_carga_17_el_nombre_del_archivo_se_guarda_sin_ruta(enviado: str, guardado: str) -> None:
    assert nombre_sin_ruta(enviado) == guardado
    assert leer(_bytes(CON_ERROR), nombre_archivo=enviado).nombre_archivo == guardado


def test_br_carga_17_un_mensaje_de_archivo_ilegible_no_trae_el_contenido() -> None:
    error = _ilegible(_bytes(PDF), "export_410.xlsx")
    assert str(error) == MENSAJE_NO_ES_LIBRO
    assert error.args == (MENSAJE_NO_ES_LIBRO,)
