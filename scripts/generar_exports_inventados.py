"""Genera los exports inventados de tests/datos_inventados/ (T017 de specs/001-mvp-carga-r17/tasks.md).

Uso, desde la raíz del repositorio
    uv run python -I scripts/generar_exports_inventados.py
    uv run python -I scripts/generar_exports_inventados.py --salida /carpeta/temporal
    uv run python -I scripts/generar_exports_inventados.py --plantilla /ruta/de/export_inventado_410_con_error.xlsx

Todo es inventado. Los códigos de estudiante van de 99000001 a 99000011 en la sección 410, de
99000012 a 99000022 en la 411 y de 99000023 a 99000055 en las tres secciones del profesor con
varias secciones, y los nombres son genéricos, como en el export de ejemplo.

La plantilla es export_inventado_410_con_error.xlsx, la copia byte a byte del export inventado de
ejemplo, con un 5 en el PI 5.2 de la fila 3. El generador comprueba su huella SHA-256, copia de
ella la estructura (nombre de hoja, encabezado, columnas de identificación, de acceso, de
actividades y de los PI con su puntaje posible) y toma los niveles de los PI de la sección 410 de
db/pruebas/datos_sinteticos.sql (NIVELES_410). La salida es la misma byte a byte en cada corrida,
porque las propiedades del libro y las fechas de las partes del zip son fijas.

Los exports de docente.varias@example.invalid (SECCIONES_DE_VARIAS) son los de la 412 de 450002 y
de la 410 y la 412 de 450010, las secciones de db/datos/varias_secciones_2026_2_inventado.sql.
Conservan las columnas de identificación, de acceso y de actividades del export correcto de la 410,
con los ids de Blackboard de su propio curso, y llevan al final las columnas de PI del plan de su
asignatura, todas con un puntaje posible de 4, con niveles que dan porcentajes distintos en cada
sección.

El export de la guardia, con un código que no es inventado en la fila 4, nunca se versiona.
escribir_export_guardia() lo arma en la ruta que pida la prueba, por ejemplo dentro de tmp_path.
Las demás funciones (con_celda, sin_columnas, con_columna, con_hoja, sin_filas y escribir) arman
las copias que piden los escenarios de carga.feature sin versionarlas.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import os
import re
import stat
import struct
import sys
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook

RAIZ = Path(__file__).resolve().parent.parent
CARPETA_DATOS = RAIZ / "tests" / "datos_inventados"

NOMBRE_PLANTILLA = "export_inventado_410_con_error.xlsx"
RUTA_PLANTILLA = CARPETA_DATOS / NOMBRE_PLANTILLA
SHA256_PLANTILLA = "2b94db8d8abfd5ff24425584172de7942383c480f25ee0a8cacf927e17df2d15"

NOMBRE_CORRECTO_410 = "sintetico_20262_450002_410.xlsx"
NOMBRE_411 = "export_inventado_411.xlsx"
NOMBRE_DANADO = "danado_410.xlsx"
NOMBRE_PROTEGIDO = "protegido_410.xlsx"
NOMBRE_PDF = "pdf_renombrado.xlsx"
NOMBRE_VACIO = "vacio_410.xlsx"
NOMBRE_SIN_5_2 = "sin_5_2_410.xlsx"
NOMBRE_SIN_CODIGO = "sin_username_ni_student_id_410.xlsx"
NOMBRE_HOJA1 = "hoja1_sin_seccion.xlsx"
NOMBRE_450002_412 = "sintetico_20262_450002_412.xlsx"
NOMBRE_450010_410 = "sintetico_20262_450010_410.xlsx"
NOMBRE_450010_412 = "sintetico_20262_450010_412.xlsx"

HOJA_410 = "gc_SINTETICO_20262_450002_410_f"
HOJA_411 = "gc_SINTETICO_20262_450002_411_f"
PI_DEL_PLAN = ("5.1", "5.2", "5.3")
# Plan de 450010 en 2026-2 de db/datos/varias_secciones_2026_2_inventado.sql, con los PI 2.1 y 2.2 del
# SO 2 y el 5.1 del SO 5. PI_DEL_PLAN es el de 450002.
PLAN_450010 = ("2.1", "2.2", "5.1")

# Fechas fijas, las mismas del export de ejemplo, para que la salida no dependa del reloj.
# FECHA_PROPIEDADES va en created y modified de docProps/core.xml (UTC) y FECHA_PARTES_ZIP en cada
# parte del zip.
FECHA_PROPIEDADES = datetime(2026, 10, 28, 13, 14, 17)
FECHA_PARTES_ZIP = (2026, 10, 28, 8, 14, 16)

# Niveles de 5.1, 5.2 y 5.3 de la sección 410, copiados de db/pruebas/datos_sinteticos.sql, con la
# fila del archivo y el código. Dan 63,6 %, 63,6 % y 72,7 % de estudiantes con nivel 3 o 4, y
# tests/test_generador_exports.py comprueba que coinciden con ese archivo.
NIVELES_410: tuple[tuple[int, int, tuple[int, int, int]], ...] = (
    (2, 99000001, (3, 4, 3)),
    (3, 99000002, (4, 3, 4)),
    (4, 99000003, (2, 3, 3)),
    (5, 99000004, (3, 2, 3)),
    (6, 99000005, (1, 2, 2)),
    (7, 99000006, (4, 3, 4)),
    (8, 99000007, (3, 4, 3)),
    (9, 99000008, (2, 1, 1)),
    (10, 99000009, (4, 3, 4)),
    (11, 99000010, (3, 4, 3)),
    (12, 99000011, (2, 2, 2)),
)

# La 411 usa los códigos 99000012 a 99000022, para que la consulta de control Q08 no vea a un
# estudiante en dos secciones, y los niveles de la 410 en orden inverso, que dan los mismos
# porcentajes (99000012 lleva los niveles de 99000011 y 99000022 los de 99000001).
DESPLAZAMIENTO_411 = 11

# Código que no es inventado para el export de la guardia (US-08 y T052).
CODIGO_GUARDIA = 10000004
FILA_GUARDIA = 4

# Niveles de las tres secciones de docente.varias@example.invalid, con la fila del archivo, el código y
# un nivel por PI en el orden del plan de la asignatura. db/pruebas/pruebas.sql (sección 9) carga los
# mismos niveles, y tests/test_generador_exports.py lo comprueba y calcula aparte las cifras del R-17.
# La 412 de 450002 da 81,8 %, 54,5 % y 90,9 % de estudiantes con nivel 3 o 4 en 5.1, 5.2 y 5.3.
NIVELES_450002_412: tuple[tuple[int, int, tuple[int, int, int]], ...] = (
    (2, 99000023, (4, 3, 4)),
    (3, 99000024, (3, 2, 4)),
    (4, 99000025, (4, 4, 3)),
    (5, 99000026, (3, 1, 4)),
    (6, 99000027, (2, 2, 3)),
    (7, 99000028, (3, 3, 4)),
    (8, 99000029, (4, 2, 2)),
    (9, 99000030, (1, 1, 3)),
    (10, 99000031, (3, 3, 4)),
    (11, 99000032, (3, 4, 3)),
    (12, 99000033, (4, 3, 4)),
)
# La 410 de 450010 da 72,7 %, 45,5 % y 36,4 % en 2.1, 2.2 y 5.1.
NIVELES_450010_410: tuple[tuple[int, int, tuple[int, int, int]], ...] = (
    (2, 99000034, (3, 2, 2)),
    (3, 99000035, (4, 3, 1)),
    (4, 99000036, (2, 1, 2)),
    (5, 99000037, (4, 4, 3)),
    (6, 99000038, (3, 2, 1)),
    (7, 99000039, (1, 1, 2)),
    (8, 99000040, (4, 3, 3)),
    (9, 99000041, (3, 2, 4)),
    (10, 99000042, (2, 2, 1)),
    (11, 99000043, (4, 4, 2)),
    (12, 99000044, (3, 3, 3)),
)
# La 412 de 450010 da 90,9 %, 63,6 % y 54,5 % en 2.1, 2.2 y 5.1.
NIVELES_450010_412: tuple[tuple[int, int, tuple[int, int, int]], ...] = (
    (2, 99000045, (4, 3, 3)),
    (3, 99000046, (3, 2, 1)),
    (4, 99000047, (4, 4, 4)),
    (5, 99000048, (3, 3, 2)),
    (6, 99000049, (2, 1, 2)),
    (7, 99000050, (4, 3, 4)),
    (8, 99000051, (3, 2, 1)),
    (9, 99000052, (4, 3, 3)),
    (10, 99000053, (3, 4, 2)),
    (11, 99000054, (4, 2, 4)),
    (12, 99000055, (3, 3, 3)),
)

# Cada curso de Blackboard numera sus columnas por su cuenta, así que los ids de cada sección de
# docente.varias se mueven a su bloque, 1000 por bloque sobre los del export de ejemplo (9000101 de la
# «Actividad 01» pasa a 9001101 en el bloque 1).
DESPLAZAMIENTO_POR_BLOQUE = 1000
_ID_DE_BLACKBOARD = re.compile(r"\|([0-9]+)$")


@dataclass(frozen=True)
class Export:
    """Contenido de un export de Blackboard con una sola hoja.

    filas no incluye el encabezado. La fila 2 del libro es filas[0], como en Excel.
    """

    hoja: str
    encabezado: tuple[str, ...]
    filas: tuple[tuple[object, ...], ...]

    def indice(self, columna: str) -> int:
        """Posición de la columna, por su encabezado exacto o, en un PI como «5.2», por «5.2 [»."""
        for posicion, encabezado in enumerate(self.encabezado):
            if encabezado == columna or encabezado.startswith(f"{columna} ["):
                return posicion
        raise KeyError(f"El export no tiene la columna {columna!r}.")

    def valor(self, fila: int, columna: str) -> object:
        """Valor de la celda en la fila del libro (la primera de datos es la 2) y la columna dada."""
        return self.filas[fila - 2][self.indice(columna)]


@dataclass(frozen=True)
class SeccionDeVarias:
    """Sección de docente.varias@example.invalid en db/datos/varias_secciones_2026_2_inventado.sql y su export.

    plan trae los PI de la asignatura en el orden de sus columnas, niveles trae por fila del libro el
    código y un nivel por PI del plan, y bloque elige los ids de Blackboard del curso de la sección.
    """

    nombre: str
    asignatura: str
    seccion: str
    plan: tuple[str, ...]
    bloque: int
    niveles: tuple[tuple[int, int, tuple[int, ...]], ...]

    @property
    def hoja(self) -> str:
        """Hoja gc_<curso_blackboard>_f, con el curso SINTETICO_20262_<asignatura>_<sección> de la base."""
        return f"gc_SINTETICO_20262_{self.asignatura}_{self.seccion}_f"


SECCIONES_DE_VARIAS = (
    SeccionDeVarias(NOMBRE_450002_412, "450002", "412", PI_DEL_PLAN, 1, NIVELES_450002_412),
    SeccionDeVarias(NOMBRE_450010_410, "450010", "410", PLAN_450010, 2, NIVELES_450010_410),
    SeccionDeVarias(NOMBRE_450010_412, "450010", "412", PLAN_450010, 3, NIVELES_450010_412),
)


def con_celda(export: Export, fila: int, columna: str, valor: object) -> Export:
    """Copia del export con valor en la fila del libro y la columna dadas. None deja la celda vacía."""
    if not 2 <= fila <= len(export.filas) + 1:
        raise ValueError(f"La fila {fila} no es una fila de datos del export.")
    posicion = export.indice(columna)
    filas = list(export.filas)
    celdas = list(filas[fila - 2])
    celdas[posicion] = valor
    filas[fila - 2] = tuple(celdas)
    return Export(export.hoja, export.encabezado, tuple(filas))


def sin_columnas(export: Export, *columnas: str) -> Export:
    """Copia del export sin las columnas dadas (por encabezado exacto o por código de PI)."""
    quitar = {export.indice(columna) for columna in columnas}
    return Export(
        export.hoja,
        tuple(e for i, e in enumerate(export.encabezado) if i not in quitar),
        tuple(tuple(v for i, v in enumerate(fila) if i not in quitar) for fila in export.filas),
    )


def con_columna(export: Export, encabezado: str, valores: Iterable[object]) -> Export:
    """Copia del export con una columna más al final, con un valor por fila de datos."""
    valores = tuple(valores)
    if len(valores) != len(export.filas):
        raise ValueError("La columna nueva necesita un valor por cada fila de datos.")
    return Export(
        export.hoja,
        (*export.encabezado, encabezado),
        tuple((*fila, valor) for fila, valor in zip(export.filas, valores, strict=True)),
    )


def con_hoja(export: Export, hoja: str) -> Export:
    """Copia del export con otro nombre de hoja."""
    return Export(hoja, export.encabezado, export.filas)


def sin_filas(export: Export) -> Export:
    """Copia del export con el encabezado y ninguna fila de datos."""
    return Export(export.hoja, export.encabezado, ())


def huella(datos: bytes) -> str:
    """Huella SHA-256 en hexadecimal y minúscula, como archivo_origen.sha256."""
    return hashlib.sha256(datos).hexdigest()


def leer_export(datos: bytes) -> Export:
    """Lee un .xlsx de una sola hoja con openpyxl en modo de solo lectura."""
    libro = load_workbook(io.BytesIO(datos), read_only=True, data_only=True)
    try:
        if len(libro.worksheets) != 1:
            raise ValueError("El export debe tener una sola hoja.")
        hoja = libro.worksheets[0]
        filas = list(hoja.iter_rows(values_only=True))
        titulo = hoja.title
    finally:
        libro.close()
    if not filas:
        raise ValueError("El export no tiene encabezado.")
    encabezado = tuple(str(celda) for celda in filas[0])
    ancho = len(encabezado)
    datos_filas = tuple(tuple(fila) + (None,) * (ancho - len(fila)) for fila in filas[1:])
    return Export(titulo, encabezado, datos_filas)


def leer_plantilla(ruta: Path = RUTA_PLANTILLA) -> tuple[Export, bytes]:
    """Lee la plantilla y comprueba que su huella sea la del export inventado de ejemplo."""
    datos = ruta.read_bytes()
    if huella(datos) != SHA256_PLANTILLA:
        raise ValueError(
            f"{ruta.name} no es la copia byte a byte del export inventado de ejemplo "
            f"(su huella SHA-256 debe ser {SHA256_PLANTILLA})."
        )
    return leer_export(datos), datos


_MODIFICADO = re.compile(rb"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)")


def _zip_determinista(datos: bytes) -> bytes:
    """Reescribe el zip de openpyxl con las mismas partes, en el mismo orden y con fechas fijas.

    openpyxl pone la hora del momento en dcterms:modified y en la fecha de cada parte del zip, y
    esas dos marcas son lo único que cambia entre dos corridas. Los atributos de cada parte quedan
    como los deja openpyxl en Unix (las hojas salen de un archivo temporal con permisos 0600 y las
    demás partes no), así que la salida tampoco depende del sistema operativo.
    """
    marca = FECHA_PROPIEDADES.strftime("%Y-%m-%dT%H:%M:%SZ").encode()
    salida = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(datos)) as origen,
        zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as destino,
    ):
        for parte in origen.infolist():
            contenido = origen.read(parte)
            if parte.filename == "docProps/core.xml":
                contenido, cambios = _MODIFICADO.subn(rb"\g<1>" + marca + rb"\g<2>", contenido)
                if cambios != 1:
                    raise RuntimeError("docProps/core.xml no trae una sola fecha dcterms:modified.")
            info = zipfile.ZipInfo(parte.filename, date_time=FECHA_PARTES_ZIP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            tipo = stat.S_IFREG if stat.S_ISREG(parte.external_attr >> 16) else 0
            info.external_attr = (tipo | 0o600) << 16
            destino.writestr(info, contenido)
    return salida.getvalue()


def a_bytes(export: Export) -> bytes:
    """Arma el .xlsx del export con openpyxl, con propiedades y fechas fijas."""
    libro = Workbook()
    hoja = libro.active
    hoja.title = export.hoja
    hoja.append(list(export.encabezado))
    for fila in export.filas:
        hoja.append(list(fila))
    libro.properties.created = FECHA_PROPIEDADES
    libro.properties.modified = FECHA_PROPIEDADES
    crudo = io.BytesIO()
    libro.save(crudo)
    return _zip_determinista(crudo.getvalue())


def escribir(export: Export, destino: Path) -> Path:
    """Escribe el .xlsx del export en destino y devuelve la ruta."""
    destino.write_bytes(a_bytes(export))
    return destino


def export_410(plantilla: Export) -> Export:
    """Export correcto de la 410, la plantilla con los niveles de NIVELES_410 (un 3 en 5.2 de la fila 3)."""
    export = plantilla
    for fila, codigo, niveles in NIVELES_410:
        if export.valor(fila, "Username") != codigo:
            raise ValueError(f"La fila {fila} de la plantilla no trae el código {codigo}.")
        for pi, nivel in zip(PI_DEL_PLAN, niveles, strict=True):
            export = con_celda(export, fila, pi, nivel)
    return export


def export_411(plantilla: Export) -> Export:
    """Export correcto de la 411, con su hoja, los códigos 99000012 a 99000022 y los niveles invertidos."""
    export = con_hoja(export_410(plantilla), HOJA_411)
    for (fila, codigo_410, _), (_, _, niveles) in zip(NIVELES_410, reversed(NIVELES_410), strict=True):
        codigo = codigo_410 + DESPLAZAMIENTO_411
        export = con_celda(export, fila, "Last Name", f"Inventado {codigo - 99000000:02d}")
        export = con_celda(export, fila, "Username", codigo)
        for pi, nivel in zip(PI_DEL_PLAN, niveles, strict=True):
            export = con_celda(export, fila, pi, nivel)
    return export


def export_guardia(plantilla: Export) -> Export:
    """Export correcto de la 410 con un código que no es inventado en la fila 4 (US-08)."""
    return con_celda(export_410(plantilla), FILA_GUARDIA, "Username", CODIGO_GUARDIA)


def id_de_blackboard(pi: str, bloque: int = 0) -> str:
    """Id de Blackboard inventado de la columna de un PI, como 9000051 para el 5.1 del export de ejemplo."""
    so, numero = (int(parte) for parte in pi.split("."))
    if not 1 <= numero <= 9:
        raise ValueError(f"El PI {pi} no cabe en el esquema de ids de Blackboard del generador.")
    return str(9000000 + DESPLAZAMIENTO_POR_BLOQUE * bloque + 10 * so + numero)


def con_bloque_de_blackboard(export: Export, bloque: int) -> Export:
    """Copia del export con los ids de Blackboard de su encabezado movidos al bloque de otro curso."""

    def mover(encabezado: str) -> str:
        return _ID_DE_BLACKBOARD.sub(
            lambda id_: f"|{int(id_.group(1)) + DESPLAZAMIENTO_POR_BLOQUE * bloque}", encabezado
        )

    return Export(export.hoja, tuple(mover(e) for e in export.encabezado), export.filas)


def export_de_varias(plantilla: Export, seccion: SeccionDeVarias) -> Export:
    """Export correcto de una sección de docente.varias, con la estructura de la plantilla y el plan de su asignatura.

    Parte del export correcto de la 410, cambia su hoja, mueve los ids de Blackboard al bloque de la
    sección y reemplaza las columnas 5.1, 5.2 y 5.3 por las del plan, al final y con un puntaje
    posible de 4. Cada fila recibe el código de la sección y el nombre genérico que le corresponde.
    """
    export = con_bloque_de_blackboard(sin_columnas(con_hoja(export_410(plantilla), seccion.hoja), *PI_DEL_PLAN),
                                      seccion.bloque)
    if [fila for fila, _, _ in seccion.niveles] != list(range(2, len(export.filas) + 2)):
        raise ValueError(f"Los niveles de {seccion.nombre} no cubren en orden las filas de datos de la plantilla.")
    if any(len(niveles) != len(seccion.plan) for _, _, niveles in seccion.niveles):
        raise ValueError(f"Cada fila de {seccion.nombre} lleva un nivel por PI del plan.")
    for posicion, pi in enumerate(seccion.plan):
        export = con_columna(
            export,
            f"{pi} [Total Pts: 4 Score] |{id_de_blackboard(pi, seccion.bloque)}",
            (niveles[posicion] for _, _, niveles in seccion.niveles),
        )
    for fila, codigo, _ in seccion.niveles:
        export = con_celda(export, fila, "Last Name", f"Inventado {codigo - 99000000:02d}")
        export = con_celda(export, fila, "Username", codigo)
    return export


def _cae_en_la_carpeta_de_datos(destino: Path) -> bool:
    """Indica si destino cae en tests/datos_inventados/, por su ruta o por la identidad de la carpeta.

    La ruta sola no alcanza, porque en un sistema de archivos que no distingue mayúsculas, como el
    de la Mac, tests/DATOS_INVENTADOS es la misma carpeta con otro texto. os.path.samefile compara
    el dispositivo y el nodo de cada carpeta de la ruta que ya existe con los de la carpeta de datos.
    """
    ruta = destino.resolve()
    carpeta = CARPETA_DATOS.resolve()
    if ruta.is_relative_to(carpeta):
        return True
    if not carpeta.is_dir():
        return False
    return any(ancestro.exists() and os.path.samefile(ancestro, carpeta) for ancestro in (ruta, *ruta.parents))


def escribir_export_guardia(destino: Path, ruta_plantilla: Path = RUTA_PLANTILLA) -> Path:
    """Escribe el export de la guardia en destino. Solo para pruebas en tmp_path, nunca en tests/datos_inventados/."""
    if _cae_en_la_carpeta_de_datos(destino):
        raise ValueError("El export de la guardia no se escribe en tests/datos_inventados/.")
    plantilla, _ = leer_plantilla(ruta_plantilla)
    return escribir(export_guardia(plantilla), destino)


def cortar_a_la_mitad(datos: bytes) -> bytes:
    """Primera mitad de los bytes, un zip sin directorio central que no se puede abrir."""
    return datos[: len(datos) // 2]


# Contenedor OLE (formato de archivo compuesto de Microsoft, versión 3, sectores de 512 bytes), la
# forma de un libro de Excel cifrado con contraseña. EncryptionInfo lleva un descriptor bien formado
# del cifrado ágil, con sal y valores cifrados inventados, y EncryptedPackage lleva bytes
# pseudoaleatorios. El archivo imita solo esa forma, así que no trae ninguna clave, ninguna
# contraseña lo abre y dentro no hay un libro.
_FIRMA_OLE = bytes.fromhex("D0CF11E0A1B11AE1")
_ESPACIO_CIFRADO = b"http://schemas.microsoft.com/office/2006/encryption"
_ESPACIO_CONTRASENA = b"http://schemas.microsoft.com/office/2006/keyEncryptor/password"
_FIN_DE_CADENA = 0xFFFFFFFE
_SECTOR_DE_FAT = 0xFFFFFFFD
_SECTOR_LIBRE = 0xFFFFFFFF
_SIN_ENTRADA = 0xFFFFFFFF
_SECTOR = 512
_CORTE_MINIFLUJO = 4096
_SECTORES_POR_FLUJO = 8  # 4096 bytes, sin miniflujo ni mini FAT, porque llega al corte


def _entrada_ole(
    nombre: str,
    *,
    tipo: int,
    color: int,
    derecha: int = _SIN_ENTRADA,
    hijo: int = _SIN_ENTRADA,
    sector: int,
    tamano: int,
) -> bytes:
    """Entrada de 128 bytes del directorio OLE. tipo 5 es la raíz y 2 un flujo, y color 1 es negro y 0 rojo."""
    nombre_utf16 = (nombre + "\0").encode("utf-16-le") if nombre else b""
    return struct.pack(
        "<64sHBBIII16sIQQIQ",
        nombre_utf16.ljust(64, b"\0"),
        len(nombre_utf16),
        tipo,
        color,
        _SIN_ENTRADA,
        derecha,
        hijo,
        b"\0" * 16,
        0,
        0,
        0,
        sector,
        tamano,
    )


def _base64_inventado(etiqueta: str, largo: int) -> bytes:
    """largo bytes pseudoaleatorios y fijos, en base64, para un valor inventado del descriptor."""
    return base64.b64encode(hashlib.shake_256(f"ABET_SIS_MED {etiqueta}".encode()).digest(largo))


def descriptor_de_cifrado() -> bytes:
    """Descriptor del cifrado ágil de EncryptionInfo, con los elementos de un libro cifrado de Excel.

    Trae keyData, dataIntegrity y la llave de la contraseña en keyEncryptors, con los algoritmos que
    usa Excel (AES de 256 bits y SHA-512) y sal y valores cifrados inventados. Con esos elementos,
    un lector como msoffcrypto-tool lo reconoce como cifrado en lugar de fallar al leerlo.
    """
    algoritmo = (
        b'saltSize="16" blockSize="16" keyBits="256" hashSize="64" cipherAlgorithm="AES" '
        b'cipherChaining="ChainingModeCBC" hashAlgorithm="SHA512"'
    )
    return b"".join(
        (
            b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n',
            b'<encryption xmlns="%s" xmlns:p="%s">' % (_ESPACIO_CIFRADO, _ESPACIO_CONTRASENA),
            b"<!-- Descriptor inventado para las pruebas de ABET_SIS_MED, sin clave. -->",
            b'<keyData %s saltValue="%s"/>' % (algoritmo, _base64_inventado("sal de los datos", 16)),
            b'<dataIntegrity encryptedHmacKey="%s" encryptedHmacValue="%s"/>'
            % (_base64_inventado("llave de integridad", 64), _base64_inventado("valor de integridad", 64)),
            b'<keyEncryptors><keyEncryptor uri="%s">' % _ESPACIO_CONTRASENA,
            b'<p:encryptedKey spinCount="100000" %s saltValue="%s" encryptedVerifierHashInput="%s" '
            b'encryptedVerifierHashValue="%s" encryptedKeyValue="%s"/>'
            % (
                algoritmo,
                _base64_inventado("sal del verificador", 16),
                _base64_inventado("entrada del verificador", 16),
                _base64_inventado("huella del verificador", 64),
                _base64_inventado("llave cifrada", 32),
            ),
            b"</keyEncryptor></keyEncryptors></encryption>",
        )
    )


def contenedor_ole_cifrado() -> bytes:
    """Bytes de un contenedor OLE con la firma D0 CF 11 E0, como un .xlsx protegido con contraseña."""
    tamano_flujo = _SECTOR * _SECTORES_POR_FLUJO
    if tamano_flujo < _CORTE_MINIFLUJO:
        raise ValueError("Cada flujo del contenedor necesita al menos 4096 bytes.")
    # Versión 4.4 (cifrado ágil) y el valor reservado 0x40, seguidos del descriptor.
    info_cifrado = struct.pack("<HHI", 4, 4, 0x40) + descriptor_de_cifrado()
    if len(info_cifrado) > tamano_flujo:
        raise ValueError("El descriptor de cifrado no cabe en el flujo EncryptionInfo.")
    # El relleno hasta 4096 bytes va con espacios, que el XML admite después del elemento raíz. Un
    # relleno con bytes nulos deja el descriptor mal formado.
    info_cifrado = info_cifrado.ljust(tamano_flujo, b" ")
    paquete = struct.pack("<Q", tamano_flujo - 8)
    paquete += hashlib.shake_256(b"ABET_SIS_MED paquete cifrado inventado").digest(tamano_flujo - 8)

    primer_info, primer_paquete = 2, 2 + _SECTORES_POR_FLUJO
    fat = [_SECTOR_DE_FAT, _FIN_DE_CADENA]
    fat += list(range(primer_info + 1, primer_paquete)) + [_FIN_DE_CADENA]
    fat += list(range(primer_paquete + 1, primer_paquete + _SECTORES_POR_FLUJO)) + [_FIN_DE_CADENA]
    fat += [_SECTOR_LIBRE] * (_SECTOR // 4 - len(fat))

    cabecera = struct.pack(
        "<8s16sHHHHH6sIIIIIIIII",
        _FIRMA_OLE,
        b"\0" * 16,
        0x003E,
        0x0003,
        0xFFFE,
        9,
        6,
        b"\0" * 6,
        0,
        1,
        1,
        0,
        _CORTE_MINIFLUJO,
        _FIN_DE_CADENA,
        0,
        _FIN_DE_CADENA,
        0,
    ) + struct.pack("<109I", 0, *([_SECTOR_LIBRE] * 108))

    # Árbol rojo y negro del directorio. EncryptionInfo es la raíz (negra) y EncryptedPackage, con
    # un nombre más largo, su hijo derecho (rojo).
    directorio = (
        _entrada_ole("Root Entry", tipo=5, color=1, hijo=1, sector=_FIN_DE_CADENA, tamano=0)
        + _entrada_ole("EncryptionInfo", tipo=2, color=1, derecha=2, sector=primer_info, tamano=tamano_flujo)
        + _entrada_ole("EncryptedPackage", tipo=2, color=0, sector=primer_paquete, tamano=tamano_flujo)
        + _entrada_ole("", tipo=0, color=0, sector=0, tamano=0)
    )
    return cabecera + struct.pack(f"<{len(fat)}I", *fat) + directorio + info_cifrado + paquete


def pdf_inventado() -> bytes:
    """PDF inventado de una página, con su tabla de referencias cruzadas exacta."""
    texto = b"BT /F1 12 Tf 72 770 Td (Documento inventado para las pruebas de ABET_SIS_MED.) Tj ET\n"
    objetos = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        b"<< /Length %d >>\nstream\n" % len(texto) + texto + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    )
    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    posiciones = []
    for numero, cuerpo in enumerate(objetos, start=1):
        posiciones.append(len(pdf))
        pdf += b"%d 0 obj\n" % numero + cuerpo + b"\nendobj\n"
    inicio_xref = len(pdf)
    pdf += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for posicion in posiciones:
        pdf += b"%010d 00000 n \n" % posicion
    pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objetos) + 1, inicio_xref)
    return bytes(pdf)


def generar(salida: Path = CARPETA_DATOS, ruta_plantilla: Path = RUTA_PLANTILLA) -> dict[str, Path]:
    """Escribe en salida los exports versionados y devuelve sus rutas por nombre."""
    plantilla, datos_plantilla = leer_plantilla(ruta_plantilla)
    correcto = export_410(plantilla)
    datos_correcto = a_bytes(correcto)
    archivos = {
        NOMBRE_CORRECTO_410: datos_correcto,
        NOMBRE_PLANTILLA: datos_plantilla,
        NOMBRE_411: a_bytes(export_411(plantilla)),
        NOMBRE_DANADO: cortar_a_la_mitad(datos_correcto),
        NOMBRE_PROTEGIDO: contenedor_ole_cifrado(),
        NOMBRE_PDF: pdf_inventado(),
        NOMBRE_VACIO: a_bytes(sin_filas(correcto)),
        NOMBRE_SIN_5_2: a_bytes(sin_columnas(correcto, "5.2")),
        NOMBRE_SIN_CODIGO: a_bytes(sin_columnas(correcto, "Username", "Student ID")),
        NOMBRE_HOJA1: a_bytes(con_hoja(correcto, "Hoja1")),
    }
    for seccion in SECCIONES_DE_VARIAS:
        archivos[seccion.nombre] = a_bytes(export_de_varias(plantilla, seccion))
    salida.mkdir(parents=True, exist_ok=True)
    rutas = {}
    for nombre, datos in archivos.items():
        rutas[nombre] = salida / nombre
        rutas[nombre].write_bytes(datos)
    return rutas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera los exports inventados de tests/datos_inventados/.")
    parser.add_argument("--salida", type=Path, default=CARPETA_DATOS, help="carpeta de salida")
    parser.add_argument("--plantilla", type=Path, default=RUTA_PLANTILLA, help="copia del export inventado de ejemplo")
    argumentos = parser.parse_args(argv)
    try:
        rutas = generar(argumentos.salida, argumentos.plantilla)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for nombre, ruta in rutas.items():
        datos = ruta.read_bytes()
        print(f"{huella(datos)}  {len(datos):>6} bytes  {nombre}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
