"""Lector del export de Blackboard (T031 de specs/001-mvp-carga-r17/tasks.md).

Aplica las reglas de negocio (business rules, BR) BR-CARGA-04, BR-CARGA-05, BR-CARGA-06, BR-CARGA-14 y
BR-CARGA-17 de specs/features/carga-export/carga-export.spec.md, en el orden de los pasos 3 y 4 de
BR-CARGA-03. leer(contenido, nombre_archivo=...) devuelve un LibroLeido o lanza ArchivoIlegible con
un motivo de la lista cerrada MotivoIlegible. La firma suma nombre_archivo a la que propone el plan,
porque BR-CARGA-05 revisa la extensión antes que el contenido y BR-CARGA-11 coteja la sección con el
nombre del archivo cuando la hoja no la declara.

La huella de huella() es el paso 2 de BR-CARGA-03, antes del tope, así que cargar() la calcula sobre
todo cuerpo que llega y después llama a leer(). Con la huella y el nombre del motivo, el registro de
un archivo detenido por su tamaño o por ilegible no necesita la hoja, las celdas ni los códigos
(BR-CARGA-08).

Orden de las revisiones de leer().
1. El tamaño, con 1 MB (1 048 576 bytes, propuesta) como tope (BR-CARGA-04).
2. La extensión .xlsx del nombre sin ruta, en mayúsculas o minúsculas.
3. Los primeros bytes. Un contenedor de vinculación e incrustación de objetos (Object Linking and
   Embedding, OLE) con los flujos EncryptionInfo y EncryptedPackage es un libro cifrado con
   contraseña, y un OLE sin ellos, como un .xls de Excel 97 renombrado, o cualquier contenido que no
   empieza como un zip no es un libro de Excel. Un archivo vacío no abre.
4. El zip, revisado con zipfile antes de abrir el libro. Más de 100 partes, más de 20 MB
   descomprimidos o una parte de más de 100 KiB que se descomprime más de 100 veces su tamaño
   detienen el archivo con CONTENIDO_INFLADO (propuesta, los tres límites). zipfile no entrega más
   bytes que los que declara cada parte, así que la suma declarada acota lo que openpyxl lee. La
   proporción de 100 es la que Apache POI aplica por omisión. xl/vbaProject.bin y xl/externalLinks/,
   o una parte que [Content_Types].xml o xl/_rels/workbook.xml.rels declaran como macros o como
   vínculo externo con otro nombre, detienen el archivo con MACROS_O_VINCULOS (propuesta, la
   detección por tipo), y un zip sin [Content_Types].xml ni xl/workbook.xml no
   es un libro de Excel.
5. La apertura con openpyxl.load_workbook(read_only=True, data_only=True), sin pandas y solo si
   openpyxl lee el lenguaje de marcado extensible (Extensible Markup Language, XML) con defusedxml.
   Sin defusedxml el lector lanza RuntimeError y no abre ningún archivo, porque es un defecto del
   despliegue y no del export.
6. La cuadrícula de Excel. Una fila después de la 1 048 576 o una celda después de la columna XFD,
   la 16 384, detienen el archivo con NO_SE_PUDO_ABRIR, porque Excel no las abre, openpyxl rellena
   con filas vacías el salto hasta una fila lejana y una columna de PI después de la 32 767 no cabe
   en carga_columna.posicion.

El lector lee la primera hoja, que en el export de Blackboard es la única, y toma la fila 1 como
encabezado. Ignora la dimensión que declara la hoja, porque una dimensión equivocada cortaría filas
o columnas. Al leer cada fila conserva solo la celda de la columna del código y las de las columnas
de los indicadores de desempeño (performance indicators, PI), y suelta las demás, entre ellas Last
Name, First Name, Last Access, Availability y las actividades, antes de pasar a la fila siguiente
(BR-CARGA-17). openpyxl guarda la tabla de cadenas compartidas mientras el libro está abierto, y el
lector lo cierra antes de devolver el resultado. El nombre de la hoja llega hasta 100 caracteres, el
ancho de archivo_origen.hoja, aunque Excel no pase de 31.

El código sale de Username y, si el archivo no la trae, de Student ID (BR-CARGA-15). Una columna es
de PI cuando su encabezado empieza por número, punto, número y « [», como
«5.1 [Total Pts: 4 Score] |9000051», y de ahí salen el número de Blackboard tras «|» y el Total Pts
(BR-CARGA-14). Esos dos datos quedan en None si no caben en carga_columna, declara_puntaje dice si el
encabezado trae un Total Pts aunque no quepa, y el encabezado se guarda hasta 200 caracteres, el
ancho de carga_columna.encabezado, para que la carga no choque con la base.

Las filas vacías del final no cuentan como filas de datos. Una fila vacía entre filas con datos sí
cuenta, con su número, porque fila_origen es la fila del archivo y la consulta de control Q12 exige
que no pase de filas_de_datos + 1 (BR-CARGA-16). La validación la rechaza después por código vacío.
"""

from __future__ import annotations

import hashlib
import io
import re
import zipfile
from collections.abc import Iterator, Sequence
from decimal import ROUND_HALF_UP, Decimal

import openpyxl.xml
from openpyxl import Workbook, load_workbook
from openpyxl.worksheet._read_only import ReadOnlyWorksheet

from abet_carga.modelos import (
    ArchivoIlegible,
    ColumnaLeida,
    FilaLeida,
    LibroLeido,
    MotivoIlegible,
    TipoColumna,
    es_celda_vacia,
)

MAXIMO_BYTES = 1_048_576
MAXIMO_DESCOMPRIMIDO = 20 * MAXIMO_BYTES
MAXIMO_PARTES = 100
MAXIMA_PROPORCION = 100
PARTE_CON_PROPORCION = 100 * 1024
# La cuadrícula de Excel termina en la fila 1 048 576 y en la columna XFD, la 16 384.
MAXIMA_FILA = 1_048_576
MAXIMA_COLUMNA = 16_384
LARGO_ENCABEZADO = 200
LARGO_HOJA = 100
COLUMNAS_DE_CODIGO = ("Username", "Student ID")

_FIRMA_ZIP = b"PK\x03\x04"
_FIRMA_OLE = bytes.fromhex("D0CF11E0A1B11AE1")
_FLUJOS_DE_CIFRADO = tuple(nombre.encode("utf-16-le") for nombre in ("EncryptionInfo", "EncryptedPackage"))
_PARTES_DE_UN_LIBRO = frozenset({"[Content_Types].xml", "xl/workbook.xml"})
_PARTES_CON_DECLARACIONES = ("[Content_Types].xml", "xl/_rels/workbook.xml.rels")
# Tipos de contenido y de relación que Excel usa para un proyecto de macros (VBA, Visual Basic for
# Applications) y para un vínculo externo, en minúsculas porque el lector compara sin distinguirlas.
_MARCAS_DE_MACRO_O_VINCULO = (
    b"application/vnd.ms-office.vbaproject",
    b"spreadsheetml.externallink+xml",
    b"/relationships/externallink",
)
_ENCABEZADO_DE_PI = re.compile(r"(?P<pi>[0-9]+\.[0-9]+) \[")
_TOTAL_PTS = re.compile(r"\[Total Pts:\s*(?:up to\s+)?(?P<puntos>[0-9]+(?:[.,][0-9]+)?)", re.IGNORECASE)
_COLUMNA_DE_BLACKBOARD = re.compile(r"\|\s*(?P<bb>[0-9]{1,12})\s*$")
_CENTESIMA = Decimal("0.01")
_PUNTAJE_MAXIMO = Decimal("9999.99")


def huella(contenido: bytes) -> str:
    """Huella SHA-256 (Secure Hash Algorithm de 256 bits) de los bytes recibidos (BR-CARGA-06).

    Son 64 cifras hexadecimales en minúscula, como archivo_origen.sha256 y la salida de shasum -a 256.
    """
    return hashlib.sha256(contenido).hexdigest()


def nombre_sin_ruta(nombre_archivo: str) -> str:
    """Nombre del archivo sin la ruta que agregan algunos navegadores con «/» o «\\» (BR-CARGA-17)."""
    return re.split(r"[/\\]", nombre_archivo)[-1]


def revisar_tamano(contenido: bytes) -> None:
    """Detiene un archivo de más de 1 MB antes de leerlo (BR-CARGA-04)."""
    if len(contenido) > MAXIMO_BYTES:
        raise ArchivoIlegible(MotivoIlegible.ARCHIVO_DEMASIADO_GRANDE)


def leer(contenido: bytes, *, nombre_archivo: str) -> LibroLeido:
    """Revisa y lee el export, o lanza ArchivoIlegible con el motivo del primer defecto que encuentra."""
    _exigir_defusedxml()
    revisar_tamano(contenido)
    nombre = nombre_sin_ruta(nombre_archivo)
    _revisar_extension(nombre)
    _revisar_contenedor(contenido)
    return _abrir(contenido, nombre)


def _exigir_defusedxml() -> None:
    if openpyxl.xml.DEFUSEDXML is not True:
        raise RuntimeError("openpyxl no usa defusedxml en este entorno, así que el lector no abre ningún archivo.")


def _revisar_extension(nombre: str) -> None:
    if not nombre.lower().endswith(".xlsx"):
        raise ArchivoIlegible(MotivoIlegible.TIPO_NO_ADMITIDO)


def _revisar_contenedor(contenido: bytes) -> None:
    if not contenido:
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR)
    if contenido.startswith(_FIRMA_OLE):
        cifrado = all(flujo in contenido for flujo in _FLUJOS_DE_CIFRADO)
        raise ArchivoIlegible(
            MotivoIlegible.PROTEGIDO_CON_CONTRASENA if cifrado else MotivoIlegible.CONTENIDO_NO_ES_LIBRO
        )
    if not contenido.startswith(_FIRMA_ZIP):
        raise ArchivoIlegible(MotivoIlegible.CONTENIDO_NO_ES_LIBRO)
    partes = _partes_del_zip(contenido)
    if _se_infla(partes):
        raise ArchivoIlegible(MotivoIlegible.CONTENIDO_INFLADO)
    if any(_es_macro_o_vinculo(parte.filename) for parte in partes) or _declara_macro_o_vinculo(contenido):
        raise ArchivoIlegible(MotivoIlegible.MACROS_O_VINCULOS)
    if not _PARTES_DE_UN_LIBRO <= {parte.filename for parte in partes}:
        raise ArchivoIlegible(MotivoIlegible.CONTENIDO_NO_ES_LIBRO)


def _partes_del_zip(contenido: bytes) -> list[zipfile.ZipInfo]:
    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
            return paquete.infolist()
    except Exception:
        # El índice de un zip cortado o alterado falla de muchas formas, y ninguna le dice más al profesor.
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR) from None


def _se_infla(partes: Sequence[zipfile.ZipInfo]) -> bool:
    if len(partes) > MAXIMO_PARTES or sum(parte.file_size for parte in partes) > MAXIMO_DESCOMPRIMIDO:
        return True
    return any(
        parte.file_size > PARTE_CON_PROPORCION and parte.file_size > MAXIMA_PROPORCION * parte.compress_size
        for parte in partes
    )


def _es_macro_o_vinculo(nombre: str) -> bool:
    nombre = nombre.lower()
    return nombre.endswith("vbaproject.bin") or nombre.startswith("xl/externallinks/")


def _declara_macro_o_vinculo(contenido: bytes) -> bool:
    """Dice si [Content_Types].xml o las relaciones del libro declaran macros o un vínculo externo."""
    with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
        nombres = set(paquete.namelist())
        textos = [paquete.read(parte).lower() for parte in _PARTES_CON_DECLARACIONES if parte in nombres]
    return any(marca in texto for texto in textos for marca in _MARCAS_DE_MACRO_O_VINCULO)


def _abrir(contenido: bytes, nombre_archivo: str) -> LibroLeido:
    libro = _cargar_libro(contenido)
    try:
        if not libro.worksheets:
            raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR)
        hoja = libro.worksheets[0]
        hoja.reset_dimensions()
        filas = _filas_del_archivo(hoja)
        columnas = _clasificar(next(filas, ()))
        datos = tuple(_filas_de_datos(filas, columnas))
        titulo = str(hoja.title)[:LARGO_HOJA]
        return LibroLeido(nombre_archivo=nombre_archivo, hoja=titulo, columnas=columnas, filas=datos)
    finally:
        libro.close()


def _cargar_libro(contenido: bytes) -> Workbook:
    try:
        return load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    except Exception:
        # openpyxl falla con muchos tipos de excepción ante un XML roto o una entidad prohibida, y el
        # mensaje original puede citar partes del archivo, así que no se encadena.
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR) from None


def _filas_del_archivo(hoja: ReadOnlyWorksheet) -> Iterator[tuple[object, ...]]:
    """Filas tal como las entrega openpyxl, desde la 1. Un XML que no se puede leer detiene el archivo.

    Una fila o una celda fuera de la cuadrícula de Excel también lo detiene, porque Excel no la abre y
    openpyxl rellena con filas vacías el salto hasta ella. Solo los errores de openpyxl y de esa
    revisión pasan por el except, porque un error de quien consume las filas no entra al generador.
    """
    try:
        for numero, fila in enumerate(hoja.iter_rows(values_only=True), start=1):
            if numero > MAXIMA_FILA or len(fila) > MAXIMA_COLUMNA:
                raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR)
            yield fila
    except Exception:
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR) from None


def _clasificar(encabezado: Sequence[object]) -> tuple[ColumnaLeida, ...]:
    textos = ["" if valor is None else str(valor).strip() for valor in encabezado]
    codigo = _posicion_del_codigo(textos)
    return tuple(_columna(posicion, texto, posicion == codigo) for posicion, texto in enumerate(textos, start=1))


def _posicion_del_codigo(textos: Sequence[str]) -> int | None:
    """Posición de Username o, si el archivo no la trae, de Student ID (BR-CARGA-07 y BR-CARGA-15)."""
    for nombre in COLUMNAS_DE_CODIGO:
        if nombre in textos:
            return textos.index(nombre) + 1
    return None


def _columna(posicion: int, texto: str, es_codigo: bool) -> ColumnaLeida:
    encabezado = texto[:LARGO_ENCABEZADO]
    if es_codigo:
        return ColumnaLeida(posicion, encabezado, TipoColumna.CODIGO)
    pi = _ENCABEZADO_DE_PI.match(texto)
    if pi is None:
        return ColumnaLeida(posicion, encabezado, TipoColumna.OTRA)
    bb = _COLUMNA_DE_BLACKBOARD.search(texto)
    total = _TOTAL_PTS.search(texto)
    return ColumnaLeida(
        posicion,
        encabezado,
        TipoColumna.PI,
        pi["pi"],
        bb["bb"] if bb else None,
        puntaje_maximo_declarado=_puntaje(total),
        declara_puntaje=total is not None,
    )


def _puntaje(total: re.Match[str] | None) -> Decimal | None:
    """Total Pts que declara el encabezado, solo si cabe en numeric(6, 2) y es mayor que 0.

    Así cumple ck_carga_columna_puntaje y el ancho de carga_columna.puntaje_maximo_declarado.
    """
    if total is None:
        return None
    valor = Decimal(total["puntos"].replace(",", "."))
    if not Decimal(0) < valor < Decimal(10_000):
        return None
    # PostgreSQL redondea numeric a la mitad hacia arriba en los positivos, y aquí se redondea igual.
    puntaje = valor.quantize(_CENTESIMA, rounding=ROUND_HALF_UP)
    return puntaje if Decimal(0) < puntaje <= _PUNTAJE_MAXIMO else None


def _filas_de_datos(filas: Iterator[tuple[object, ...]], columnas: Sequence[ColumnaLeida]) -> Iterator[FilaLeida]:
    codigo = next((c.posicion for c in columnas if c.tipo is TipoColumna.CODIGO), None)
    de_pi = [c.posicion for c in columnas if c.tipo is TipoColumna.PI]
    vacias: list[int] = []
    for numero, fila in enumerate(filas, start=2):
        if all(es_celda_vacia(valor) for valor in fila):
            vacias.append(numero)
            continue
        # Las filas vacías que quedaron atrás están entre filas con datos, así que cuentan.
        yield from (FilaLeida(vacia, None, (None,) * len(de_pi)) for vacia in vacias)
        vacias.clear()
        yield FilaLeida(numero, _celda(fila, codigo), tuple(_celda(fila, posicion) for posicion in de_pi))


def _celda(fila: Sequence[object], posicion: int | None) -> object:
    if posicion is None or posicion > len(fila):
        return None
    return fila[posicion - 1]
