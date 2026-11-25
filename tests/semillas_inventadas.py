"""Revisión de los nombres de las semillas y de los CSV rastreados por git (US-99 y FR-013 de la spec 010, T022).

cargar_y_revisar() carga las semillas de db/datos/ una por una en una base desechable de tests/base_desechable.py, así
que cada problema se atribuye a su archivo, y comprueba que cada nombre nuevo tenga la forma inventada («Profesor
Inventado» y una o más palabras con mayúscula inicial y solo letras) y que cada correo nuevo sea de example.invalid.
csv_con_columna_nombre() lista los CSV que git rastrea fuera de tests/datos_inventados/ y traen una columna nombre en su
encabezado, porque un archivo de programación con nombres reales vive siempre fuera del repositorio (FR-009 de la spec
006). Los mensajes nombran el archivo y nunca el valor de un nombre ni de un correo. Nada de aquí toca localhost:5432 ni
Neon, porque base_desechable._psql() exige el clúster desechable de las pruebas.
"""

from __future__ import annotations

import csv
import io
import re
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "db" / "datos"
SEMILLAS = [DATOS / "periodo_2026_2_inventado.sql", DATOS / "varias_secciones_2026_2_inventado.sql",
            DATOS / "quimica_2026_1_inventado.sql"]
ALCANCE_AMBIENTAL = DATOS / "alcance_coordinacion_ambiental.sql"
# Una letra Unicode es un carácter de palabra que no es un dígito ni el guion bajo.
_FORMA_INVENTADA = re.compile(r"Profesor Inventado( [A-ZÁÉÍÓÚÑÜ][^\W\d_]*)+")
_CORREO_INVENTADO = re.compile(r"[^@\s]+@example\.invalid")
CARPETA_INVENTADA = "tests/datos_inventados/"


def es_de_la_forma_inventada(nombre: str) -> bool:
    return _FORMA_INVENTADA.fullmatch(nombre) is not None


def es_de_example_invalid(correo: str) -> bool:
    return _CORREO_INVENTADO.fullmatch(correo) is not None


def _base_desechable() -> ModuleType:
    modulo = sys.modules.get("base_desechable")
    assert modulo is not None, "la fixture base_desechable todavía no cargó tests/base_desechable.py"
    return modulo


def correr_sql(base: Any, sentencia: str) -> str:
    """Una sentencia con psql sobre la base desechable, siempre en el clúster desechable."""
    return _base_desechable()._psql(base.nombre, "-At", "-c", sentencia)


def correr_semilla(base: Any, semilla: Path) -> None:
    """Corre una semilla con psql, con el alcance de Ambiental antes de la de Química, como en el orden de FR-020."""
    desechable = _base_desechable()
    if semilla.name == "quimica_2026_1_inventado.sql":
        desechable._psql(base.nombre, "-v", "aplicar=1", "-f", str(ALCANCE_AMBIENTAL))
    desechable._psql(base.nombre, "-f", str(semilla))


def nombres_de(base: Any, solo_coordinadores: bool = False) -> list[tuple[str, str]]:
    """Correo y nombre de cada usuario con nombre, o de cada cuenta COORDINADOR con nombre."""
    filtro = "AND rol = 'COORDINADOR'" if solo_coordinadores else ""
    salida = correr_sql(base, "SELECT correo || '|' || nombre FROM acceso.usuario_autorizado"
                              f" WHERE nombre IS NOT NULL {filtro} ORDER BY correo")
    return [tuple(linea.split("|", 1)) for linea in salida.splitlines()]  # type: ignore[misc]


def _correos(base: Any) -> set[str]:
    return set(correr_sql(base, "SELECT correo FROM acceso.usuario_autorizado").splitlines())


def _plural(cantidad: int, singular: str, plural: str) -> str:
    return f"{cantidad} {singular if cantidad == 1 else plural}"


def cargar_y_revisar(base: Any, semillas: list[Path]) -> tuple[list[str], dict[str, str]]:
    """Carga las semillas en orden y devuelve los problemas, uno por archivo y tipo, y los nombres que dejan.

    Un problema dice el archivo, cuántos nombres nuevos o cambiados no tienen la forma inventada o cuántos correos
    nuevos no son de example.invalid, sin repetir ningún valor.
    """
    problemas: list[str] = []
    for semilla in semillas:
        antes_nombres, antes_correos = dict(nombres_de(base)), _correos(base)
        correr_semilla(base, semilla)
        ahora = dict(nombres_de(base))
        nuevos = {correo: nombre for correo, nombre in ahora.items() if antes_nombres.get(correo) != nombre}
        fuera_de_forma = [correo for correo, nombre in nuevos.items() if not es_de_la_forma_inventada(nombre)]
        correos_fuera = [correo for correo in _correos(base) - antes_correos if not es_de_example_invalid(correo)]
        if fuera_de_forma:
            problemas.append(f"{semilla.name}: "
                             f"{_plural(len(fuera_de_forma), 'nombre', 'nombres')} fuera de la forma inventada")
        if correos_fuera:
            problemas.append(f"{semilla.name}: {_plural(len(correos_fuera), 'correo', 'correos')} fuera de example.invalid")
    return problemas, dict(nombres_de(base))


def _encabezado(contenido: bytes) -> list[str]:
    """Celdas de la primera línea de un CSV en UTF-8 con o sin BOM o en UTF-16, separadas por coma, punto y coma o tab."""
    if contenido[:2] in (b"\xff\xfe", b"\xfe\xff"):
        texto = contenido.decode("utf-16", errors="replace")
    else:
        texto = contenido.decode("utf-8-sig", errors="replace")
    primera = texto.splitlines()[0] if texto.splitlines() else ""
    for separador in (",", ";", "\t"):
        if separador in primera:
            break
    else:
        separador = ","
    celdas = next(csv.reader(io.StringIO(primera), delimiter=separador, skipinitialspace=True), [])
    return [celda.strip().lower() for celda in celdas]


def csv_con_columna_nombre(raiz: Path = RAIZ) -> list[str]:
    """CSV y TSV que git rastrea en raiz, fuera de tests/datos_inventados/, con una columna «nombre» en el encabezado.

    Un archivo sin agregar al índice no se revisa, porque git no lo rastrea, y raiz sin repositorio falla en lugar de
    devolver una lista vacía que parezca limpia.
    """
    corrida = subprocess.run(["git", "-C", str(raiz), "ls-files", "-z"], capture_output=True, check=False)
    if corrida.returncode != 0:
        raise RuntimeError("git ls-files falló, así que no se puede revisar qué CSV rastrea git")
    rutas = [ruta for ruta in corrida.stdout.decode("utf-8").split("\0") if ruta]
    encontrados = []
    for ruta in rutas:
        if not ruta.lower().endswith((".csv", ".tsv")) or ruta.startswith(CARPETA_INVENTADA):
            continue
        archivo = raiz / ruta
        if archivo.is_file() and "nombre" in _encabezado(archivo.read_bytes()[:4096]):
            encontrados.append(ruta)
    return sorted(encontrados)
