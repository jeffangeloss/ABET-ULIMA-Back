"""Pruebas de scripts/generar_exports_inventados.py y de los exports de tests/datos_inventados/ (T017).

Cubren lo que debe pasar (salida determinista, regla 2 en las partes que lee scripts/preflight.sh y
en todas las demás, porcentajes y estructura copiada de la plantilla) y lo que no debe pasar
(archivos dañados que abren, un código ajeno fuera de las hojas, el export de la guardia en la
carpeta versionada, también por otra ruta, y una plantilla alterada). Leen los libros con openpyxl
por su cuenta, sin el lector del generador, para que la comprobación no dependa del código que
comprueba.
"""

from __future__ import annotations

import base64
import fnmatch
import io
import os
import re
import shutil
import struct
import subprocess
import sys
import zipfile
import zlib
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from types import ModuleType

import pytest
from defusedxml.ElementTree import ParseError, fromstring
from openpyxl import load_workbook

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "tests" / "datos_inventados"
SCRIPT = RAIZ / "scripts" / "generar_exports_inventados.py"
SQL_SINTETICOS = RAIZ / "db" / "pruebas" / "datos_sinteticos.sql"

CORRECTO = "sintetico_20262_450002_410.xlsx"
CON_ERROR = "export_inventado_410_con_error.xlsx"
EXPORT_411 = "export_inventado_411.xlsx"
DANADO = "danado_410.xlsx"
PROTEGIDO = "protegido_410.xlsx"
PDF = "pdf_renombrado.xlsx"
VACIO = "vacio_410.xlsx"
SIN_5_2 = "sin_5_2_410.xlsx"
SIN_CODIGO = "sin_username_ni_student_id_410.xlsx"
HOJA1 = "hoja1_sin_seccion.xlsx"

VERSIONADOS = (CORRECTO, CON_ERROR, EXPORT_411, DANADO, PROTEGIDO, PDF, VACIO, SIN_5_2, SIN_CODIGO, HOJA1)
LIBROS = (CORRECTO, CON_ERROR, EXPORT_411, VACIO, SIN_5_2, SIN_CODIGO, HOJA1)
NO_ABREN = (DANADO, PROTEGIDO, PDF)
PI = ("5.1", "5.2", "5.3")
HOJA_410 = "gc_SINTETICO_20262_450002_410_f"
HOJA_411 = "gc_SINTETICO_20262_450002_411_f"


# Lectura independiente de los libros

def _libro(nombre_o_ruta: str | Path) -> tuple[str, list[str], list[tuple[object, ...]]]:
    """Nombre de hoja, encabezado y filas de datos, leídos con openpyxl en modo de solo lectura."""
    ruta = nombre_o_ruta if isinstance(nombre_o_ruta, Path) else CARPETA / nombre_o_ruta
    libro = load_workbook(ruta, read_only=True, data_only=True)
    try:
        assert len(libro.worksheets) == 1
        hoja = libro.worksheets[0]
        filas = list(hoja.iter_rows(values_only=True))
        return hoja.title, [str(c) for c in filas[0]], [tuple(f) for f in filas[1:]]
    finally:
        libro.close()


def _columna(encabezado: list[str], nombre: str) -> int:
    coincidencias = [i for i, e in enumerate(encabezado) if e == nombre or e.startswith(f"{nombre} [")]
    assert len(coincidencias) == 1, f"{nombre}: {coincidencias}"
    return coincidencias[0]


def _niveles(nombre: str) -> list[tuple[int, object, tuple[object, ...]]]:
    """Fila del libro, Username y valores de 5.1, 5.2 y 5.3 de cada fila de datos."""
    _, encabezado, filas = _libro(nombre)
    usuario = _columna(encabezado, "Username")
    columnas = [_columna(encabezado, pi) for pi in PI]
    return [(n, fila[usuario], tuple(fila[c] for c in columnas)) for n, fila in enumerate(filas, start=2)]


def _un_decimal(numerador: int, denominador: int) -> Decimal:
    return (Decimal(100 * numerador) / Decimal(denominador)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _resultado(nombre: str) -> tuple[int, int, int, tuple[Decimal, ...], tuple[Counter, ...]]:
    """Leídas, aceptadas, rechazadas, porcentaje con nivel 3 o 4 y conteo por nivel de cada PI.

    Aplica el valor provisional de D-01. Una celda de PI fuera de 1 a 4 rechaza la fila completa.
    """
    filas = _niveles(nombre)
    aceptadas = [niveles for _, _, niveles in filas if all(v is None or v in (1, 2, 3, 4) for v in niveles)]
    porcentajes, conteos = [], []
    for posicion in range(len(PI)):
        calificados = [n[posicion] for n in aceptadas if n[posicion] is not None]
        porcentajes.append(_un_decimal(sum(1 for v in calificados if v >= 3), len(calificados)))
        conteos.append(Counter(calificados))
    return len(filas), len(aceptadas), len(filas) - len(aceptadas), tuple(porcentajes), tuple(conteos)


def _partes(datos: bytes) -> list[tuple[str, tuple[int, ...], int, int, int, bytes]]:
    """Partes del zip con su contenido descomprimido y sus metadatos, en el orden del archivo."""
    with zipfile.ZipFile(io.BytesIO(datos)) as libro:
        return [
            (i.filename, i.date_time, i.compress_type, i.external_attr, i.create_system, libro.read(i))
            for i in libro.infolist()
        ]


def _ocho_digitos_ajenos(texto: bytes) -> int:
    """Números de exactamente 8 dígitos que no empiezan con 99, sin mostrarlos."""
    return sum(1 for n in re.findall(rb"[0-9]+", texto) if len(n) == 8 and not n.startswith(b"99"))


def _como_la_regla_2(datos: bytes) -> int:
    """Lo que cuenta la regla 2 de scripts/preflight.sh en un .xlsx (hojas y cadenas compartidas)."""
    try:
        with zipfile.ZipFile(io.BytesIO(datos)) as libro:
            partes = [
                libro.read(n)
                for n in libro.namelist()
                if fnmatch.fnmatch(n, "xl/worksheets/*.xml") or n == "xl/sharedStrings.xml"
            ]
    except zipfile.BadZipFile:
        return 0
    return sum(_ocho_digitos_ajenos(p) for p in partes)


# Constantes de formato de 8 dígitos que openpyxl escribe en todo libro y que no son códigos. Son
# los colores de la paleta indexedColors de xl/styles.xml, con 8 cifras hexadecimales como
# 00800000, y el ángulo 16200000 de los degradados de xl/theme/theme1.xml.
_FORMATO_DE_8_DIGITOS = {
    "xl/styles.xml": re.compile(rb'\brgb="[0-9A-Fa-f]{8}"'),
    "xl/theme/theme1.xml": re.compile(rb'\bang="[0-9]+"'),
}


def _partes_locales(datos: bytes) -> list[tuple[str, bytes]]:
    """Partes de un zip leídas de sus cabeceras locales, aunque le falte el directorio central.

    La última parte de un zip cortado puede quedar incompleta, y de ella sale lo que alcanza a
    descomprimirse.
    """
    partes, inicio = [], 0
    while datos.startswith(b"PK\x03\x04", inicio) and inicio + 30 <= len(datos):
        (metodo,) = struct.unpack_from("<H", datos, inicio + 8)
        (comprimido,) = struct.unpack_from("<I", datos, inicio + 18)
        largo_nombre, largo_extra = struct.unpack_from("<HH", datos, inicio + 26)
        nombre = datos[inicio + 30 : inicio + 30 + largo_nombre].decode("utf-8", "replace")
        comienzo = inicio + 30 + largo_nombre + largo_extra
        bloque = datos[comienzo : comienzo + comprimido]
        partes.append((nombre, zlib.decompressobj(-15).decompress(bloque) if metodo == 8 else bloque))
        inicio = comienzo + comprimido
    return partes


def _partes_descomprimidas(datos: bytes) -> list[tuple[str, bytes]]:
    """Cada parte descomprimida de un zip, tenga o no su directorio central, o los bytes de otro archivo."""
    if zipfile.is_zipfile(io.BytesIO(datos)):
        with zipfile.ZipFile(io.BytesIO(datos)) as libro:
            return [(n, libro.read(n)) for n in libro.namelist()]
    if datos.startswith(b"PK\x03\x04"):
        return _partes_locales(datos)
    return [("", datos)]


def _en_todas_las_partes(datos: bytes) -> int:
    """Números de 8 dígitos que no empiezan con 99 en todo el contenido, fuera de las constantes de formato."""
    total = 0
    for nombre, contenido in _partes_descomprimidas(datos):
        formato = _FORMATO_DE_8_DIGITOS.get(nombre)
        total += _ocho_digitos_ajenos(formato.sub(b"", contenido) if formato else contenido)
    return total


def _con_texto_al_final(datos: bytes, parte: str, texto: bytes) -> bytes:
    """Copia del zip con texto agregado al final de una de sus partes."""
    salida = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(datos)) as origen,
        zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as destino,
    ):
        for info in origen.infolist():
            contenido = origen.read(info)
            destino.writestr(info, contenido + texto if info.filename == parte else contenido)
    return salida.getvalue()


def _flujo_ole(datos: bytes, nombre: str) -> bytes:
    """Contenido de un flujo del contenedor OLE, por su cadena de sectores en la FAT."""
    sector = 1 << struct.unpack_from("<H", datos, 0x1E)[0]
    (primer_fat,) = struct.unpack_from("<I", datos, 0x4C)
    (primer_directorio,) = struct.unpack_from("<I", datos, 0x30)
    fat = struct.unpack_from(f"<{sector // 4}I", datos, sector * (primer_fat + 1))
    for posicion in range(sector // 128):
        entrada = sector * (primer_directorio + 1) + 128 * posicion
        (largo,) = struct.unpack_from("<H", datos, entrada + 64)
        if largo and datos[entrada : entrada + largo - 2].decode("utf-16-le") == nombre:
            actual, tamano = struct.unpack_from("<IQ", datos, entrada + 116)
            break
    else:
        raise KeyError(nombre)
    contenido = b""
    while actual != 0xFFFFFFFE:
        contenido += datos[sector * (actual + 1) : sector * (actual + 2)]
        actual = fat[actual]
    return contenido[:tamano]


def _correr_generador(*argumentos: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), *argumentos], capture_output=True, text=True, check=False
    )


@pytest.fixture(scope="module")
def generado(tmp_path_factory: pytest.TempPathFactory) -> Path:
    salida = tmp_path_factory.mktemp("generado")
    corrida = _correr_generador("--salida", str(salida))
    assert corrida.returncode == 0, corrida.stderr
    return salida


# Determinismo y origen de los archivos

def test_dos_corridas_escriben_los_mismos_bytes(generado: Path, tmp_path: Path) -> None:
    corrida = _correr_generador("--salida", str(tmp_path))
    assert corrida.returncode == 0, corrida.stderr
    primera = {p.name: p.read_bytes() for p in generado.iterdir()}
    segunda = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    assert sorted(primera) == sorted(VERSIONADOS)
    assert primera == segunda


def test_la_carpeta_versionada_es_la_salida_del_generador(generado: Path) -> None:
    # deflate puede dar otros bytes con otra versión de zlib, así que los .xlsx se comparan parte por
    # parte, con su contenido y sus metadatos, y los demás archivos byte a byte.
    assert sorted(p.name for p in CARPETA.glob("*.xlsx")) == sorted(VERSIONADOS)
    for nombre in LIBROS:
        assert _partes((CARPETA / nombre).read_bytes()) == _partes((generado / nombre).read_bytes()), nombre
    for nombre in (PROTEGIDO, PDF):
        assert (CARPETA / nombre).read_bytes() == (generado / nombre).read_bytes(), nombre
    correcto = (CARPETA / CORRECTO).read_bytes()
    assert (CARPETA / DANADO).read_bytes() == correcto[: len(correcto) // 2]


def test_la_plantilla_es_la_copia_byte_a_byte_del_ejemplo(generador: ModuleType) -> None:
    datos = (CARPETA / CON_ERROR).read_bytes()
    assert generador.huella(datos) == generador.SHA256_PLANTILLA
    plantilla, _ = generador.leer_plantilla(CARPETA / CON_ERROR)
    # El escritor del generador reproduce la plantilla parte por parte, así que el export correcto
    # difiere de ella solo en las celdas que cambia.
    assert _partes(generador.a_bytes(plantilla)) == _partes(datos)


def test_los_niveles_son_los_de_datos_sinteticos(generador: ModuleType) -> None:
    # Cada fila de niveles del archivo tiene la forma ('99000001',  2, 3, 4, 3), código, fila y niveles.
    patron = r"\('(99\d{6})',\s*(\d+),\s*(\d),\s*(\d),\s*(\d)\)"
    filas_sql = re.findall(patron, SQL_SINTETICOS.read_text(encoding="utf-8"))
    del_sql = tuple((int(f), int(c), (int(a), int(b), int(d))) for c, f, a, b, d in filas_sql)
    assert len(del_sql) == 11
    assert del_sql == generador.NIVELES_410
    assert [(f, c, n) for f, c, n in _niveles(CORRECTO)] == list(del_sql)


# Los exports correctos y el de error

def test_el_export_correcto_da_63_6_63_6_y_72_7() -> None:
    hoja, encabezado, filas = _libro(CORRECTO)
    assert hoja == HOJA_410
    assert len(filas) == 11
    assert [c for _, c, _ in _niveles(CORRECTO)] == list(range(99000001, 99000012))
    assert [encabezado[_columna(encabezado, pi)] for pi in PI] == [
        "5.1 [Total Pts: 4 Score] |9000051",
        "5.2 [Total Pts: 4 Score] |9000052",
        "5.3 [Total Pts: 20 Score] |9000053",
    ]
    leidas, aceptadas, rechazadas, porcentajes, conteos = _resultado(CORRECTO)
    assert (leidas, aceptadas, rechazadas) == (11, 11, 0)
    assert porcentajes == (Decimal("63.6"), Decimal("63.6"), Decimal("72.7"))
    # Bloque II de r17_constancia.feature, estudiantes por nivel 1, 2, 3 y 4.
    assert [tuple(c[n] for n in (1, 2, 3, 4)) for c in conteos] == [(1, 3, 4, 3), (1, 3, 4, 3), (1, 2, 5, 3)]


def test_el_export_con_error_tiene_un_solo_5_en_5_2_de_la_fila_3() -> None:
    fuera_de_escala = [
        (fila, pi, valor)
        for fila, _, niveles in _niveles(CON_ERROR)
        for pi, valor in zip(PI, niveles, strict=True)
        if valor not in (1, 2, 3, 4)
    ]
    assert fuera_de_escala == [(3, "5.2", 5)]
    leidas, aceptadas, rechazadas, porcentajes, _ = _resultado(CON_ERROR)
    assert (leidas, aceptadas, rechazadas) == (11, 10, 1)
    assert porcentajes == (Decimal("60.0"), Decimal("60.0"), Decimal("70.0"))
    # Fuera de esa celda, el export con error y el correcto son el mismo libro.
    hoja_e, encabezado_e, filas_e = _libro(CON_ERROR)
    hoja_c, encabezado_c, filas_c = _libro(CORRECTO)
    columna = _columna(encabezado_c, "5.2")
    distintas = [
        (n, i) for n, (fe, fc) in enumerate(zip(filas_e, filas_c, strict=True), start=2)
        for i, (ve, vc) in enumerate(zip(fe, fc, strict=True)) if ve != vc
    ]
    assert (hoja_e, encabezado_e) == (hoja_c, encabezado_c)
    assert distintas == [(3, columna)]


def test_el_export_de_la_411_usa_sus_codigos_su_hoja_y_los_mismos_porcentajes() -> None:
    hoja, encabezado, _ = _libro(EXPORT_411)
    assert hoja == HOJA_411
    assert encabezado == _libro(CORRECTO)[1]
    codigos_411 = [c for _, c, _ in _niveles(EXPORT_411)]
    assert codigos_411 == list(range(99000012, 99000023))
    assert not set(codigos_411) & {c for _, c, _ in _niveles(CORRECTO)}
    leidas, aceptadas, rechazadas, porcentajes, _ = _resultado(EXPORT_411)
    assert (leidas, aceptadas, rechazadas) == (11, 11, 0)
    assert porcentajes == (Decimal("63.6"), Decimal("63.6"), Decimal("72.7"))


# Regla 2 de la revisión previa

@pytest.mark.parametrize("nombre", (*VERSIONADOS, "README.md"))
def test_cada_archivo_cumple_la_regla_2(nombre: str) -> None:
    # El README también vive en la carpeta, aunque la regla no lea los .md.
    datos = (CARPETA / nombre).read_bytes()
    # Alcance de scripts/preflight.sh, las hojas y las cadenas compartidas de cada .xlsx que abre como zip.
    assert _como_la_regla_2(datos) == 0
    # Alcance mayor que el de la regla. Todas las partes descomprimidas, también las que conserva el
    # zip cortado, y los bytes del PDF y del contenedor OLE, salvo las constantes de formato.
    assert _partes_descomprimidas(datos)
    assert _en_todas_las_partes(datos) == 0


@pytest.mark.parametrize("nombre", LIBROS)
def test_fuera_de_las_hojas_solo_hay_colores_y_angulos_de_8_digitos(nombre: str) -> None:
    # También la copia byte a byte del export de ejemplo. Son las 27 constantes de formato que la
    # regla 2 no lee y que el README de la carpeta describe.
    partes = _partes_descomprimidas((CARPETA / nombre).read_bytes())
    ajenos = {parte: _ocho_digitos_ajenos(contenido) for parte, contenido in partes}
    assert {parte: n for parte, n in ajenos.items() if n} == {"xl/styles.xml": 25, "xl/theme/theme1.xml": 2}


@pytest.mark.parametrize("parte", ["docProps/core.xml", "xl/styles.xml", "xl/theme/theme1.xml", "xl/workbook.xml"])
def test_un_codigo_ajeno_fuera_de_las_hojas_no_pasa_la_revision_de_todas_las_partes(
    parte: str, generador: ModuleType
) -> None:
    datos = (CARPETA / CORRECTO).read_bytes()
    alterado = _con_texto_al_final(datos, parte, b"<!-- %d -->" % generador.CODIGO_GUARDIA)
    # La regla de scripts/preflight.sh no lee esa parte. La excepción de formato tampoco lo esconde,
    # porque el código no va en un atributo rgb ni ang.
    assert _como_la_regla_2(alterado) == 0
    assert _en_todas_las_partes(alterado) == 1


def test_un_zip_sin_directorio_central_con_un_codigo_ajeno_no_pasa(tmp_path: Path, generador: ModuleType) -> None:
    datos = generador.escribir_export_guardia(tmp_path / "guardia.xlsx").read_bytes()
    # Con el zip entero, las cabeceras locales dan las mismas partes que zipfile.
    with zipfile.ZipFile(io.BytesIO(datos)) as libro:
        assert _partes_locales(datos) == [(n, libro.read(n)) for n in libro.namelist()]
    # El final del zip guarda dónde empieza el directorio central, y el corte lo quita entero.
    (inicio_directorio,) = struct.unpack_from("<I", datos, len(datos) - 6)
    sin_directorio = datos[:inicio_directorio]
    assert not zipfile.is_zipfile(io.BytesIO(sin_directorio))
    assert _como_la_regla_2(sin_directorio) == 0
    assert _en_todas_las_partes(sin_directorio) == 1


@pytest.mark.skipif(shutil.which("git") is None or shutil.which("unzip") is None, reason="faltan git o unzip")
def test_la_revision_previa_acepta_la_carpeta_y_rechaza_el_export_de_la_guardia(
    tmp_path: Path, generador: ModuleType
) -> None:
    repositorio = tmp_path / "repositorio"
    (repositorio / "scripts").mkdir(parents=True)
    shutil.copy(RAIZ / "scripts" / "preflight.sh", repositorio / "scripts" / "preflight.sh")
    shutil.copytree(CARPETA, repositorio / "tests" / "datos_inventados")
    # Repositorio aislado de la configuración de git de la máquina, para que un .gitignore global
    # que excluya los .xlsx no cambie el resultado.
    entorno = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    entorno |= {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

    def correr(*comando: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(comando, cwd=repositorio, env=entorno, capture_output=True, text=True, check=False)

    assert correr("git", "init", "-q").returncode == 0
    assert correr("git", "add", "-A", "-f").returncode == 0
    limpia = correr("bash", "scripts/preflight.sh")
    assert limpia.returncode == 0, limpia.stdout + limpia.stderr

    generador.escribir_export_guardia(repositorio / "tests" / "datos_inventados" / "guardia.xlsx")
    assert correr("git", "add", "-A", "-f").returncode == 0
    con_guardia = correr("bash", "scripts/preflight.sh")
    assert con_guardia.returncode == 1
    assert "tests/datos_inventados/guardia.xlsx" in con_guardia.stdout
    assert "regla 2" in con_guardia.stdout
    assert str(generador.CODIGO_GUARDIA) not in con_guardia.stdout + con_guardia.stderr


# Archivos que no deben abrir

def test_el_danado_empieza_como_zip_pero_no_abre() -> None:
    datos = (CARPETA / DANADO).read_bytes()
    assert datos.startswith(b"PK\x03\x04")
    assert not zipfile.is_zipfile(io.BytesIO(datos))
    with pytest.raises(zipfile.BadZipFile):
        load_workbook(CARPETA / DANADO, read_only=True)


def test_el_protegido_es_un_contenedor_ole_cifrado_y_no_un_zip() -> None:
    datos = (CARPETA / PROTEGIDO).read_bytes()
    assert datos[:8] == bytes.fromhex("D0CF11E0A1B11AE1")
    assert not zipfile.is_zipfile(io.BytesIO(datos))
    with pytest.raises(zipfile.BadZipFile):
        load_workbook(CARPETA / PROTEGIDO, read_only=True)
    version_mayor, _, potencia_sector = struct.unpack_from("<HHH", datos, 0x1A)
    assert (version_mayor, potencia_sector) == (3, 9)
    sector = 1 << potencia_sector
    (primer_directorio,) = struct.unpack_from("<I", datos, 0x30)
    entradas = []
    for posicion in range(sector // 128):
        inicio = sector * (primer_directorio + 1) + 128 * posicion
        largo, tipo = struct.unpack_from("<HB", datos, inicio + 64)
        if tipo:
            entradas.append((datos[inicio : inicio + largo - 2].decode("utf-16-le"), tipo))
    assert entradas == [("Root Entry", 5), ("EncryptionInfo", 2), ("EncryptedPackage", 2)]


def test_el_protegido_trae_un_descriptor_de_cifrado_bien_formado() -> None:
    datos = (CARPETA / PROTEGIDO).read_bytes()
    info = _flujo_ole(datos, "EncryptionInfo")
    # Versión 4.4, la del cifrado ágil, y el valor reservado 0x40.
    assert struct.unpack_from("<HHI", info) == (4, 4, 0x40)
    cifrado = "{http://schemas.microsoft.com/office/2006/encryption}"
    contrasena = "{http://schemas.microsoft.com/office/2006/keyEncryptor/password}"
    descriptor = fromstring(info[8:])
    assert descriptor.tag == f"{cifrado}encryption"
    llave_de_datos = descriptor.find(f"{cifrado}keyData")
    integridad = descriptor.find(f"{cifrado}dataIntegrity")
    llave = descriptor.find(f"{cifrado}keyEncryptors/{cifrado}keyEncryptor/{contrasena}encryptedKey")
    assert llave_de_datos is not None and integridad is not None and llave is not None
    assert len(base64.b64decode(llave_de_datos.get("saltValue"))) == 16
    assert [len(base64.b64decode(integridad.get(a))) for a in ("encryptedHmacKey", "encryptedHmacValue")] == [64, 64]
    valores = ("saltValue", "encryptedVerifierHashInput", "encryptedVerifierHashValue", "encryptedKeyValue")
    assert [len(base64.b64decode(llave.get(a))) for a in valores] == [16, 16, 64, 32]
    # El relleno hasta el final del flujo son espacios. Con bytes nulos, el descriptor no se lee.
    assert info[8:].rstrip(b" ").endswith(b"</encryption>")
    with pytest.raises(ParseError):
        fromstring(info[8:].rstrip(b" ") + b"\0")
    paquete = _flujo_ole(datos, "EncryptedPackage")
    assert struct.unpack_from("<Q", paquete) == (len(paquete) - 8,)


def test_el_pdf_tiene_una_pagina_y_no_es_un_libro() -> None:
    datos = (CARPETA / PDF).read_bytes()
    assert datos.startswith(b"%PDF-1.4\n")
    assert datos.endswith(b"%%EOF\n")
    assert len(re.findall(rb"/Type /Page\b(?!s)", datos)) == 1
    assert not zipfile.is_zipfile(io.BytesIO(datos))
    with pytest.raises(zipfile.BadZipFile):
        load_workbook(CARPETA / PDF, read_only=True)
    # Cada entrada de la tabla de referencias cruzadas apunta a su objeto.
    inicio_xref = int(re.search(rb"startxref\n(\d+)\n", datos).group(1))
    assert datos[inicio_xref:].startswith(b"xref\n0 6\n")
    posiciones = [int(p) for p in re.findall(rb"(\d{10}) 00000 n \n", datos[inicio_xref:])]
    assert [datos[p:].split(b"\n", 1)[0] for p in posiciones] == [b"%d 0 obj" % n for n in range(1, 6)]


# Defectos de estructura y de sección

def test_el_vacio_tiene_el_encabezado_y_ninguna_fila() -> None:
    hoja, encabezado, filas = _libro(VACIO)
    assert hoja == HOJA_410
    assert encabezado == _libro(CORRECTO)[1]
    assert filas == []


def test_el_sin_5_2_conserva_5_1_y_5_3_de_20_puntos() -> None:
    hoja, encabezado, filas = _libro(SIN_5_2)
    assert hoja == HOJA_410
    assert not [e for e in encabezado if e.startswith("5.2 [")]
    assert encabezado[_columna(encabezado, "5.1")] == "5.1 [Total Pts: 4 Score] |9000051"
    assert encabezado[_columna(encabezado, "5.3")] == "5.3 [Total Pts: 20 Score] |9000053"
    assert len(filas) == 11


def test_el_sin_codigo_no_tiene_username_ni_student_id() -> None:
    hoja, encabezado, filas = _libro(SIN_CODIGO)
    correcto = _libro(CORRECTO)[1]
    assert hoja == HOJA_410
    assert "Username" not in encabezado and "Student ID" not in encabezado
    assert encabezado == [e for e in correcto if e not in ("Username", "Student ID")]
    assert len(filas) == 11


def test_la_hoja1_no_declara_su_seccion() -> None:
    hoja, encabezado, filas = _libro(HOJA1)
    _, encabezado_correcto, filas_correcto = _libro(CORRECTO)
    assert hoja == "Hoja1"
    assert not re.search(r"\d{3}", HOJA1)
    assert (encabezado, filas) == (encabezado_correcto, filas_correcto)


# El export de la guardia, que nunca se versiona

def test_el_export_de_la_guardia_se_arma_fuera_de_la_carpeta(tmp_path: Path, generador: ModuleType) -> None:
    ruta = generador.escribir_export_guardia(tmp_path / "guardia.xlsx")
    _, encabezado, filas = _libro(ruta)
    _, _, filas_correcto = _libro(CORRECTO)
    usuario = _columna(encabezado, "Username")
    assert filas[2][usuario] == generador.CODIGO_GUARDIA
    assert [f for n, f in enumerate(filas) if n != 2] == [f for n, f in enumerate(filas_correcto) if n != 2]
    assert _como_la_regla_2(ruta.read_bytes()) == 1
    assert _en_todas_las_partes(ruta.read_bytes()) == 1


@pytest.mark.parametrize(
    "partes",
    [
        ("tests", "datos_inventados"),
        ("tests", "datos_inventados", "..", "datos_inventados"),
        ("tests", "Datos_Inventados"),
        ("TESTS", "DATOS_INVENTADOS"),
    ],
    ids=["ruta_exacta", "con_punto_punto", "otras_mayusculas", "todo_en_mayusculas"],
)
def test_el_export_de_la_guardia_no_se_escribe_en_la_carpeta(generador: ModuleType, partes: tuple[str, ...]) -> None:
    carpeta = RAIZ.joinpath(*partes)
    # Con otras mayúsculas, la Mac nombra la misma carpeta, y un sistema de archivos que distingue
    # mayúsculas nombra otra que no existe. En ningún caso el archivo llega a la carpeta versionada.
    misma = carpeta.exists() and os.path.samefile(carpeta, CARPETA)
    antes = sorted(p.name for p in CARPETA.iterdir())
    assert "guardia.xlsx" not in antes
    try:
        with pytest.raises(ValueError if misma else FileNotFoundError):
            generador.escribir_export_guardia(carpeta / "guardia.xlsx")
    finally:
        # Si la barrera falla, la prueba falla igual y no deja el export de la guardia en la carpeta.
        (CARPETA / "guardia.xlsx").unlink(missing_ok=True)
    assert sorted(p.name for p in CARPETA.iterdir()) == antes


def test_una_plantilla_alterada_se_rechaza_sin_escribir_nada(tmp_path: Path) -> None:
    alterada = tmp_path / "plantilla.xlsx"
    datos = bytearray((CARPETA / CON_ERROR).read_bytes())
    datos[-1] ^= 0x01
    alterada.write_bytes(bytes(datos))
    salida = tmp_path / "salida"
    corrida = _correr_generador("--salida", str(salida), "--plantilla", str(alterada))
    assert corrida.returncode == 1
    assert "no es la copia byte a byte" in corrida.stderr
    assert not salida.exists()


# Ni nombres de personas ni datos reales

@pytest.mark.parametrize("nombre", LIBROS)
def test_los_nombres_son_genericos_y_las_propiedades_no_nombran_personas(nombre: str) -> None:
    _, encabezado, filas = _libro(nombre)
    apellido, nombre_pila = _columna(encabezado, "Last Name"), _columna(encabezado, "First Name")
    assert all(re.fullmatch(r"Inventado \d{2}", str(f[apellido])) for f in filas)
    assert all(f[nombre_pila] == "Estudiante" for f in filas)
    libro = load_workbook(CARPETA / nombre, read_only=True)
    try:
        assert libro.properties.creator == "openpyxl"
        assert libro.properties.lastModifiedBy is None
    finally:
        libro.close()
