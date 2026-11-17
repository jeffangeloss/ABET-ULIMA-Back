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

Orden de las revisiones de leer(), con el cambio de la spec 003 (US-27, US-28, US-31 y US-32, J-18 a
J-20), que suma el .csv y el .xls de Blackboard.
1. El tamaño, con 1 MB (1 048 576 bytes, propuesta) como tope (BR-CARGA-04).
2. El nombre. Un carácter de control (U+0000 a U+001F o U+007F) en cualquier parte del nombre, que
   psycopg no guardaría, da TIPO_NO_ADMITIDO (S-09), y después la extensión .xlsx, .csv o .xls del
   nombre sin ruta, sin distinguir mayúsculas, también (TIPO_NO_ADMITIDO).
3. Los primeros bytes eligen el lector, con esta precedencia cerrada. Un archivo vacío no abre
   (NO_SE_PUDO_ABRIR, detalle VACIO). Un zip (PK 03 04) es un libro y sigue los pasos 4 a 6, sea cual
   sea la extensión. Un contenedor de vinculación e incrustación de objetos (Object Linking and
   Embedding, OLE) con los flujos EncryptionInfo y EncryptedPackage es un libro cifrado con
   contraseña, y un OLE sin ellos, como un .xls de Excel 97-2003, no es un export de Blackboard
   (CONTENIDO_NO_ES_LIBRO). EF BB BF es texto UTF-8 y FF FE es texto UTF-16 LE, y el lector quita ese
   marcador de orden de bytes (byte order mark, BOM) una sola vez. FE FF, el UTF-16 BE, no se admite
   (detalle CODIFICACION). Sin ninguna de esas firmas, un nombre .csv o .xls se lee como UTF-8 sin BOM
   y un nombre .xlsx no es un export de Blackboard.
   En las dos rutas UTF-8, un byte 0x00 detiene el archivo antes de decodificarlo (CARACTER_NULO), así
   que un UTF-16 LE sin BOM con «á» no queda en CODIFICACION. El texto se decodifica en modo estricto.
   Un texto que no se decodifica, que todavía empieza con
   U+FEFF o que trae U+0000 se detiene (CODIFICACION y CARACTER_NULO), y uno vacío también (VACIO).
   La primera línea, hasta el primer \r\n, \r o \n, elige el separador, el tabulador si lo trae y la
   coma si no, y sin ninguno de los dos se detiene (SEPARADOR). csv lee el texto con comillas dobles y
   strict=True. Una comilla mal cerrada da COMILLAS, un campo de más de 131 072 caracteres, el límite
   por omisión de csv que el lector no cambia, da CAMPO_LARGO, y un registro de más de 16 384
   columnas da COLUMNAS. Una primera línea con «;» cuyo encabezado no trae Username ni Student ID es
   un export separado por punto y coma, y se detiene con SEPARADOR. Todos esos casos responden
   NO_SE_PUDO_ABRIR, y el detalle va solo al registro (BR-CARGA-08). Ninguna excepción original se
   encadena, porque un UnicodeDecodeError lleva los bytes del archivo. El texto no tiene hoja, así que
   LibroLeido.hoja es None, y sus celdas llegan como texto a la misma clasificación y a las mismas
   filas de datos que el libro.
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
7. El tope de 5 000 filas de datos, en el libro y en el texto (J-20), y el de 1 000 000 de celdas
   recorridas después del encabezado, que cuenta también las filas vacías del final (propuesta, S-03).
   Pasar cualquiera de los dos detiene el archivo con NO_SE_PUDO_ABRIR y el detalle FILAS.

En el libro, cada ArchivoIlegible se lanza fuera del bloque except, igual que en el texto, así que su
contexto no guarda la excepción de zipfile u openpyxl, que puede traer el valor de una celda (S-08).
Una parte del zip que no se descomprime, por dañada, cifrada o con un método que zipfile no admite,
da NO_SE_PUDO_ABRIR (S-01).

El lector lee la primera hoja, que en el export de Blackboard es la única, y toma la fila 1 como
encabezado. Ignora la dimensión que declara la hoja, porque una dimensión equivocada cortaría filas
o columnas. Al leer cada fila conserva solo la celda de la columna del código y las de las columnas
de los indicadores de desempeño (performance indicators, PI), y suelta las demás, entre ellas Last
Name, First Name, Last Access, Availability y las actividades, antes de pasar a la fila siguiente
(BR-CARGA-17). openpyxl guarda la tabla de cadenas compartidas mientras el libro está abierto, y el
lector lo cierra antes de devolver el resultado. El nombre de la hoja llega hasta 100 caracteres, el
ancho de archivo_origen.hoja, aunque Excel no pase de 31.

El código sale de Username y, si el archivo no la trae, de Student ID (BR-CARGA-15). Una columna es
de PI cuando sus primeros 200 caracteres, sin espacios a los lados, empiezan por «ABET» opcional,
«SO» o «PI» opcional y número, punto, número y «[», con cero a tres espacios ASCII entre las partes,
como «ABET SO5.1 [Total Pts: 100 Score] |9000051», «ABET SO 5.3 [» o «5.1 [Total Pts: 4 Score]»
(J-19, la misma regla de ck_carga_columna_encabezado en V1_10). «6.10 [» es el PI 6.10 y nunca el
6.1. De ahí salen el número de Blackboard tras «|» y el Total Pts, que se buscan en el encabezado
entero (BR-CARGA-14). Esos dos datos quedan en None si no caben en carga_columna, declara_puntaje dice si el
encabezado trae un Total Pts aunque no quepa, y el encabezado se guarda hasta 200 caracteres, el
ancho de carga_columna.encabezado, para que la carga no choque con la base.

Las filas vacías del final no cuentan como filas de datos. Una fila vacía entre filas con datos sí
cuenta, con su número, porque fila_origen es la fila del archivo y la consulta de control Q12 exige
que no pase de filas_de_datos + 1 (BR-CARGA-16). La validación la rechaza después por código vacío.
"""

from __future__ import annotations

import csv
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
    DetalleIlegible,
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
# Tope de filas de datos de un export, para el libro y para el texto (spec 003, J-20).
MAXIMAS_FILAS_DE_DATOS = 5_000
# Tope de celdas recorridas después del encabezado, también las de las filas vacías del final, para el
# libro y para el texto (propuesta, S-03 de la revisión de seguridad de la spec 003). Cuenta las celdas
# que trae cada fila, así que las filas sin celdas con que openpyxl rellena el salto hasta una fila
# lejana, o una línea vacía del texto, no suman, porque no cuestan el relleno hasta XFD.
MAXIMAS_CELDAS = 1_000_000
EXTENSIONES = (".xlsx", ".csv", ".xls")
COLUMNAS_DE_CODIGO = ("Username", "Student ID")

_FIRMA_ZIP = b"PK\x03\x04"
_FIRMA_OLE = bytes.fromhex("D0CF11E0A1B11AE1")
_BOM_UTF8 = b"\xef\xbb\xbf"
_BOM_UTF16_LE = b"\xff\xfe"
_BOM_UTF16_BE = b"\xfe\xff"
_FIN_DE_LINEA = re.compile(r"\r\n|\r|\n")
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
# La misma regla de ck_carga_columna_encabezado en V1_10 (J-19). Las letras van en clases explícitas y
# el espacio es el ASCII, así que «ſ», el espacio duro o una cifra de ancho completo no pasan.
_ENCABEZADO_DE_PI = re.compile(
    r"(?:[Aa][Bb][Ee][Tt] {0,3})?(?:(?:[Ss][Oo]|[Pp][Ii]) {0,3})?(?P<pi>[0-9]+\.[0-9]+) {0,3}\[", re.ASCII
)
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
    # psycopg no guarda U+0000 en un campo de texto, y un carácter de control no es de un export (S-09).
    if any(ord(caracter) < 32 or caracter == "\x7f" for caracter in nombre_archivo):
        raise ArchivoIlegible(MotivoIlegible.TIPO_NO_ADMITIDO)
    nombre = nombre_sin_ruta(nombre_archivo)
    _revisar_extension(nombre)
    if not contenido:
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR, DetalleIlegible.VACIO)
    if contenido.startswith(_FIRMA_ZIP):
        _revisar_contenedor(contenido)
        return _abrir(contenido, nombre)
    if contenido.startswith(_FIRMA_OLE):
        cifrado = all(flujo in contenido for flujo in _FLUJOS_DE_CIFRADO)
        raise ArchivoIlegible(
            MotivoIlegible.PROTEGIDO_CON_CONTRASENA if cifrado else MotivoIlegible.CONTENIDO_NO_ES_LIBRO
        )
    if contenido.startswith(_BOM_UTF8):
        return _leer_texto(contenido[len(_BOM_UTF8):], "utf-8", nombre)
    if contenido.startswith(_BOM_UTF16_LE):
        return _leer_texto(contenido[len(_BOM_UTF16_LE):], "utf-16-le", nombre)
    if contenido.startswith(_BOM_UTF16_BE):
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR, DetalleIlegible.CODIFICACION)
    if nombre.lower().endswith(".xlsx"):
        raise ArchivoIlegible(MotivoIlegible.CONTENIDO_NO_ES_LIBRO)
    return _leer_texto(contenido, "utf-8", nombre)


def _exigir_defusedxml() -> None:
    if openpyxl.xml.DEFUSEDXML is not True:
        raise RuntimeError("openpyxl no usa defusedxml en este entorno, así que el lector no abre ningún archivo.")


def _revisar_extension(nombre: str) -> None:
    if not nombre.lower().endswith(EXTENSIONES):
        raise ArchivoIlegible(MotivoIlegible.TIPO_NO_ADMITIDO)


def _revisar_contenedor(contenido: bytes) -> None:
    """Revisa el zip de un libro antes de abrirlo. contenido empieza con la firma de un zip."""
    partes = _partes_del_zip(contenido)
    if _se_infla(partes):
        raise ArchivoIlegible(MotivoIlegible.CONTENIDO_INFLADO)
    if any(_es_macro_o_vinculo(parte.filename) for parte in partes) or _declara_macro_o_vinculo(contenido):
        raise ArchivoIlegible(MotivoIlegible.MACROS_O_VINCULOS)
    if not _PARTES_DE_UN_LIBRO <= {parte.filename for parte in partes}:
        raise ArchivoIlegible(MotivoIlegible.CONTENIDO_NO_ES_LIBRO)


def _partes_del_zip(contenido: bytes) -> list[zipfile.ZipInfo]:
    # El índice de un zip cortado o alterado falla de muchas formas, y ninguna le dice más al profesor.
    # El ArchivoIlegible se lanza fuera del except, para que su contexto no guarde la excepción (S-08).
    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
            partes: list[zipfile.ZipInfo] | None = paquete.infolist()
    except Exception:
        partes = None
    if partes is None:
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR)
    return partes


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
    """Dice si [Content_Types].xml o las relaciones del libro declaran macros o un vínculo externo.

    Una parte dañada, cifrada o con un método de compresión que zipfile no admite lanza zlib.error,
    RuntimeError, NotImplementedError o BadZipFile, y el lector la detiene con NO_SE_PUDO_ABRIR (S-01).
    """
    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
            nombres = set(paquete.namelist())
            textos: list[bytes] | None = [
                paquete.read(parte).lower() for parte in _PARTES_CON_DECLARACIONES if parte in nombres
            ]
    except Exception:
        textos = None
    if textos is None:
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR)
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
    # openpyxl falla con muchos tipos de excepción ante un XML roto o una entidad prohibida, y el
    # mensaje original puede citar partes del archivo, así que se lanza fuera del except (S-08).
    try:
        libro: Workbook | None = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    except Exception:
        libro = None
    if libro is None:
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR)
    return libro


def _filas_del_archivo(hoja: ReadOnlyWorksheet) -> Iterator[tuple[object, ...]]:
    """Filas tal como las entrega openpyxl, desde la 1. Un XML que no se puede leer detiene el archivo.

    Una fila o una celda fuera de la cuadrícula de Excel también lo detiene, porque Excel no la abre y
    openpyxl rellena con filas vacías el salto hasta ella. Solo la lectura de openpyxl pasa por el
    except, y el ArchivoIlegible se lanza fuera de él, para que su contexto no guarde la excepción de
    openpyxl, que puede traer el valor de una celda (S-08).
    """
    filas = hoja.iter_rows(values_only=True)
    numero = 0
    while True:
        try:
            fila = next(filas, None)
            legible = True
        except Exception:
            fila, legible = None, False
        if not legible:
            raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR)
        if fila is None:
            return
        numero += 1
        if numero > MAXIMA_FILA or len(fila) > MAXIMA_COLUMNA:
            raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR)
        yield fila


def _leer_texto(datos: bytes, codificacion: str, nombre_archivo: str) -> LibroLeido:
    """Lee un export de texto, el .csv o el .xls de Blackboard, ya sin su BOM (spec 003, BR-CARGA-05).

    Cada ArchivoIlegible se lanza fuera del bloque except, así que ni su causa ni su contexto llevan
    la excepción original, que en un UnicodeDecodeError trae los bytes del archivo.
    """
    # En UTF-8 un 0x00 crudo es casi siempre un UTF-16 sin BOM, y se detiene antes de decodificar, así
    # que no queda en CODIFICACION aunque el texto traiga «á». En UTF-16 LE el 0x00 es normal y se mira
    # el U+0000 del texto decodificado.
    if codificacion == "utf-8" and b"\x00" in datos:
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR, DetalleIlegible.CARACTER_NULO)
    texto = _decodificado(datos, codificacion)
    if texto is None or texto.startswith("\ufeff"):
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR, DetalleIlegible.CODIFICACION)
    # csv de Python 3.12 acepta el U+0000 dentro de un campo, así que se revisa antes de leer.
    if "\x00" in texto:
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR, DetalleIlegible.CARACTER_NULO)
    if not texto:
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR, DetalleIlegible.VACIO)
    primera_linea = _FIN_DE_LINEA.split(texto, maxsplit=1)[0]
    if "\t" in primera_linea:
        separador = "\t"
    elif "," in primera_linea:
        separador = ","
    else:
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR, DetalleIlegible.SEPARADOR)
    filas = _filas_del_texto(texto, separador)
    columnas = _clasificar(next(filas, ()))
    # Un export separado por «;» que se leyó con la coma no trae la columna del código en su encabezado.
    if ";" in primera_linea and not any(columna.tipo is TipoColumna.CODIGO for columna in columnas):
        raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR, DetalleIlegible.SEPARADOR)
    datos_leidos = tuple(_filas_de_datos(filas, columnas))
    return LibroLeido(nombre_archivo=nombre_archivo, hoja=None, columnas=columnas, filas=datos_leidos)


def _decodificado(datos: bytes, codificacion: str) -> str | None:
    """Texto decodificado en modo estricto, o None si los bytes no son de esa codificación."""
    try:
        return datos.decode(codificacion, errors="strict")
    except UnicodeDecodeError:
        return None


def _filas_del_texto(texto: str, separador: str) -> Iterator[tuple[str, ...]]:
    """Registros del texto, desde el encabezado, como tuplas de str, sin leer el archivo entero de una vez.

    csv lee con comillas dobles y strict=True, sin csv.Sniffer y con el límite de campo por omisión
    de 131 072 caracteres, que el lector no cambia porque csv.field_size_limit() es estado global.
    Una comilla mal cerrada da COMILLAS, un campo más largo que el límite da CAMPO_LARGO y un
    registro de más de 16 384 columnas, la cuadrícula de Excel, da COLUMNAS. Solo los errores de csv
    pasan por el except, porque un error de quien consume las filas no entra al generador.
    """
    lector = csv.reader(
        io.StringIO(texto, newline=""), delimiter=separador, quotechar='"', doublequote=True, strict=True
    )
    while True:
        try:
            fila = next(lector, None)
        except csv.Error as error:
            detalle = DetalleIlegible.CAMPO_LARGO if "field limit" in str(error) else DetalleIlegible.COMILLAS
            break
        if fila is None:
            return
        if len(fila) > MAXIMA_COLUMNA:
            detalle = DetalleIlegible.COLUMNAS
            break
        yield tuple(fila)
    raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR, detalle)


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
    # El PI se reconoce sobre el encabezado cortado, el que guarda la base, para que
    # ck_carga_columna_encabezado reciba exactamente lo que el lector reconoce (J-19).
    pi = _ENCABEZADO_DE_PI.match(encabezado)
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


def _filas_de_datos(filas: Iterator[Sequence[object]], columnas: Sequence[ColumnaLeida]) -> Iterator[FilaLeida]:
    """Filas de datos desde la 2, con las vacías intermedias y sin las del final.

    Al pasar de 5 000 filas entregadas, o de 1 000 000 de celdas recorridas contando también las filas
    vacías del final, detiene el archivo con NO_SE_PUDO_ABRIR y el detalle FILAS, en el libro y en el
    texto (spec 003, J-20 y S-03). openpyxl rellena cada fila hasta su última celda, así que sin el
    tope de celdas un libro pequeño con filas vacías que llegan a XFD tardaba segundos en leerse.
    """
    codigo = next((c.posicion for c in columnas if c.tipo is TipoColumna.CODIGO), None)
    de_pi = [c.posicion for c in columnas if c.tipo is TipoColumna.PI]
    vacias: list[int] = []
    entregadas = 0
    celdas = 0
    for numero, fila in enumerate(filas, start=2):
        celdas += len(fila)
        if celdas > MAXIMAS_CELDAS:
            raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR, DetalleIlegible.FILAS)
        if all(es_celda_vacia(valor) for valor in fila):
            vacias.append(numero)
            continue
        entregadas += len(vacias) + 1
        if entregadas > MAXIMAS_FILAS_DE_DATOS:
            raise ArchivoIlegible(MotivoIlegible.NO_SE_PUDO_ABRIR, DetalleIlegible.FILAS)
        # Las filas vacías que quedaron atrás están entre filas con datos, así que cuentan.
        yield from (FilaLeida(vacia, None, (None,) * len(de_pi)) for vacia in vacias)
        vacias.clear()
        yield FilaLeida(numero, _celda(fila, codigo), tuple(_celda(fila, posicion) for posicion in de_pi))


def _celda(fila: Sequence[object], posicion: int | None) -> object:
    if posicion is None or posicion > len(fila):
        return None
    return fila[posicion - 1]
