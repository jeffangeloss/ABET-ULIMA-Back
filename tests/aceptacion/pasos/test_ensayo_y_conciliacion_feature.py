"""Pasos de ensayo_y_conciliacion.feature (US-83 y US-84 de la spec 008), con pytest-bdd en español (T037 y T057).

El .feature manda. Los Antecedentes arman la base de la spec 008 con el plan de 5643 en 2026-1 y los datos inventados
de Química General, en el clúster desechable de tests/cluster_desechable.py y nunca en localhost:5432, y una tabla
maestra INVENTADA en tmp_path con las secciones 701 a 703, códigos del rango 99 y profesores inventados. Las cargas se
publican con la biblioteca abet_carga, como lo hará el ensayo de US-84, y cada R-17 se descarga con abet_carga.r17.

El conciliador db/herramientas/conciliar_tabla_maestra.py corre como proceso aparte, como lo correría Jefferson, con
las variables de libpq hacia la copia desechable del escenario y el rol abet_respaldo, que crea
db/plataforma/neon/crear_roles_lectura.sql en esa copia. Cada «Entonces» se comprueba con el código de salida y el
informe del proceso, con la base desechable o con las celdas del R-17, sin dobles del conciliador.

Los escenarios del ensayo de US-84 (T057) arman los exports con scripts/generar_exports_desde_maestra.py, el generador
de US-74, sobre la misma tabla inventada y una programación inventada en tmp_path, y corren
db/herramientas/ensayar_capacitacion.py como proceso aparte con las variables de libpq hacia la copia desechable. El
ensayo sube cada export con la biblioteca abet_carga, descarga su R-17 y corre el conciliador con abet_respaldo. Al
final del módulo, cinco pruebas más recorren las secciones inventadas 701 a 704, la 704 sin profesor, una base que ya
tiene cargas del curso, el rol de lectura del conciliador y los códigos sin 99 con la opción de datos reales.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
from openpyxl import Workbook, load_workbook
from psycopg.conninfo import make_conninfo
from pytest_bdd import given, parsers, scenario, then, when

from abet_carga import r17
from abet_carga.carga import Configuracion, Resultado, cargar

Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/ensayo_y_conciliacion.feature"
CONCILIADOR = RAIZ / "db" / "herramientas" / "conciliar_tabla_maestra.py"
ENSAYO = RAIZ / "db" / "herramientas" / "ensayar_capacitacion.py"
GENERADOR = RAIZ / "scripts" / "generar_exports_desde_maestra.py"
ROLES_DE_LECTURA = RAIZ / "db" / "plataforma" / "neon" / "crear_roles_lectura.sql"
COLUMNAS = ("AÑO", "CICLO", "CÓDIGO DEL CURSO", "CURSO", "CICLO DEL CURSO", "SO", "PI", "PROFESOR",
            "CÓDIGO DEL ESTUDIANTE", "SECCIÓN", "CALIFICACIÓN", "ARCHIVO")
COLUMNA_6_1 = "ABET SO6.1 [Total Pts: 4 Score] |9000061"
FECHA = "2026-07-15-00-00-00"
REGLAS = "R-2026-BORRADOR"
SECCIONES = ("701", "702", "703")
# Niveles inventados de los 5 estudiantes de cada sección, con todos los niveles de 1 a 4 y un 3 en la 702.
NIVELES = {"701": (3, 4, 2, 3, 1), "702": (2, 3, 4, 1, 3), "703": (4, 3, 1, 2, 3)}
OCHO_CIFRAS = re.compile(r"(?<![0-9])[0-9]{8}(?![0-9])")
SQLSTATE_SOLO_LECTURA = "25006"


@dataclass
class Maestra:
    """Filas de la tabla maestra inventada, cada una con las doce columnas, en el orden del libro desde la fila 2."""

    filas: list[dict[str, object]] = field(default_factory=list)

    def escribir(self, destino: Path) -> Path:
        libro = Workbook()
        hoja = libro.active
        hoja.title = "Tabla maestra"
        hoja.append(list(COLUMNAS))
        for fila in self.filas:
            hoja.append([fila.get(columna) for columna in COLUMNAS])
        libro.save(destino)
        return destino

    def de(self, seccion: str, pi: str = "6.1") -> list[dict[str, object]]:
        return [fila for fila in self.filas if fila["SECCIÓN"] == seccion and fila["PI"] == pi]


def _fila(seccion: str, codigo: str, calificacion: int, pi: str = "6.1") -> dict[str, object]:
    return {"AÑO": 2026, "CICLO": 1, "CÓDIGO DEL CURSO": "5643", "CURSO": "QUÍMICA GENERAL", "CICLO DEL CURSO": 1,
            "SO": pi.split(".")[0], "PI": pi, "PROFESOR": f"Docente Inventado {seccion}", "CÓDIGO DEL ESTUDIANTE": codigo,
            "SECCIÓN": seccion, "CALIFICACIÓN": calificacion, "ARCHIVO": f"R017_inventado_{seccion}.xlsx"}


def _codigo_99(seccion: str, n: int) -> str:
    """Código inventado del rango 99, como 99701001, distinto en cada sección."""
    return f"99{seccion}{n:03d}"


def _codigo_sin_99(seccion: str, n: int) -> str:
    """Código inventado de ocho cifras que no empieza con 99, armado aquí para que ningún archivo lo traiga escrito."""
    return f"5{seccion}{n:04d}"


def _maestra_de(codigo: Any, niveles: dict[str, tuple[int, ...]] = NIVELES) -> Maestra:
    return Maestra([_fila(seccion, codigo(seccion, n), nivel) for seccion in SECCIONES
                    for n, nivel in enumerate(niveles[seccion], start=1)])


def _maestra(ctx: Escenario) -> Maestra:
    return ctx.extras["maestra"]


def _tmp(ctx: Escenario) -> Path:
    return ctx.request.getfixturevalue("tmp_path")


def _carpeta(ctx: Escenario, nombre: str) -> Path:
    carpeta = _tmp(ctx) / nombre
    carpeta.mkdir(exist_ok=True)
    return carpeta


def modulo() -> ModuleType:
    """El conciliador como módulo, cargado por su ruta porque db/herramientas/ no es un paquete. Va a sys.modules
    antes de ejecutarse, porque sus dataclasses buscan ahí su módulo."""
    if "conciliar_tabla_maestra" not in sys.modules:
        especificacion = importlib.util.spec_from_file_location("conciliar_tabla_maestra", CONCILIADOR)
        conciliador = importlib.util.module_from_spec(especificacion)
        sys.modules["conciliar_tabla_maestra"] = conciliador
        especificacion.loader.exec_module(conciliador)
    return sys.modules["conciliar_tabla_maestra"]


# Cargas y R-17, con la biblioteca abet_carga sobre la copia desechable

def publicar(ctx: Escenario, seccion: str, filas: list[tuple[str, int]], *, guardia: bool = True,
             reemplaza: int | None = None, fecha: str = FECHA) -> int:
    """Sube un export de la sección con la biblioteca, como docente70N, y exige la carga PUBLICADA."""
    curso = f"SINTETICO_20261_5643_{seccion}"
    export = ctx.generador.Export(f"gc_{curso}_f", ("Username", COLUMNA_6_1), tuple(filas))
    resultado = cargar(ctx.api.dueno, bytes(ctx.generador.a_bytes(export)), nombre_archivo=f"gc_{curso}_fullgc_{fecha}.xlsx",
                       seccion_id=ctx.seccion_de(seccion), usuario_id=ctx.usuario_id(f"docente{seccion}@example.invalid"),
                       configuracion=Configuracion(REGLAS, guardia_datos_inventados=guardia), reemplaza=reemplaza)
    assert resultado.resultado is Resultado.PUBLICADA, resultado
    ctx.extras.setdefault("cargas", {})[seccion] = resultado.carga_id
    return resultado.carga_id


def publicar_como_la_tabla(ctx: Escenario, secciones: tuple[str, ...] = SECCIONES, *, guardia: bool = True) -> None:
    for seccion in secciones:
        filas = [(str(f["CÓDIGO DEL ESTUDIANTE"]), int(f["CALIFICACIÓN"])) for f in _maestra(ctx).de(seccion)]
        publicar(ctx, seccion, filas, guardia=guardia)


def descargar_r17(ctx: Escenario) -> Path:
    carpeta = _carpeta(ctx, "r17")
    for carga_id in ctx.extras["cargas"].values():
        r17.generar(ctx.api.dueno, carga_id, carpeta)
    ctx.extras["r17"] = carpeta
    return carpeta


def _roles_de_lectura(ctx: Escenario) -> None:
    """abet_respaldo con sus permisos en la copia del escenario, con el mismo guion que corre Jefferson en Neon."""
    if ctx.extras.get("roles"):
        return
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            plugin.correr_guion(ctx.api.dueno, ROLES_DE_LECTURA, {})
            ctx.extras["roles"] = True
            return
    raise AssertionError("no se encuentra tests/aceptacion/pasos/conftest.py")


def correr(ctx: Escenario, *extra: str, maestra: Path | None = None, base: str | None = None,
           rol: str = "abet_respaldo") -> subprocess.CompletedProcess[str]:
    """Corre el conciliador con python -I, con la tabla del escenario y, si se descargaron, sus R-17."""
    if base is None:
        _roles_de_lectura(ctx)
    ruta = maestra or _maestra(ctx).escribir(_carpeta(ctx, "entrada") / "tabla_maestra_inventada.xlsx")
    argumentos = ["--maestra", str(ruta), "--periodo", "2026-1", "--asignatura", "5643", "--pi", "6.1"]
    if "r17" in ctx.extras:
        argumentos += ["--r17", str(ctx.extras["r17"])]
    entorno = {**ctx.request.getfixturevalue("base_desechable")._entorno(),
               "PGDATABASE": base or ctx.api.base.nombre, "PGUSER": rol}
    corrida = subprocess.run([sys.executable, "-I", str(CONCILIADOR), *argumentos, *extra], env=entorno,
                             capture_output=True, text=True, encoding="utf-8", check=False, cwd=_tmp(ctx))
    ctx.extras["corrida"] = corrida
    return corrida


def _salida(ctx: Escenario) -> str:
    corrida = ctx.extras["corrida"]
    return corrida.stdout + corrida.stderr


def _lineas(ctx: Escenario) -> list[str]:
    return ctx.extras["corrida"].stdout.splitlines()


def _igual(seccion: str, n: int) -> str:
    return f"Sección {seccion}. Igual en {n} de {n} estudiantes, en el conteo por nivel y en el porcentaje."


# Escenarios de US-83

@scenario(FEATURE, "Todo coincide en la base, en la vista y en los R-17")
def test_todo_coincide() -> None:
    """T037."""


@scenario(FEATURE, "Una calificación distinta se informa sin el código")
def test_una_calificacion_distinta() -> None:
    """T037."""


@scenario(FEATURE, "Cada diferencia se cuenta por su tipo y por sección")
def test_cada_diferencia_por_su_tipo() -> None:
    """T037, con sus cuatro Ejemplos."""


@scenario(FEATURE, "Una sección sin carga publicada se nombra")
def test_una_seccion_sin_carga_publicada() -> None:
    """T037."""


@scenario(FEATURE, "El mismo cociente con otro redondeo cuenta como igual")
def test_el_mismo_cociente_con_otro_redondeo() -> None:
    """T037."""


@scenario(FEATURE, "Una carga reemplazada no duplica filas")
def test_una_carga_reemplazada_no_duplica() -> None:
    """T037."""


@scenario(FEATURE, "El orden de las filas y la columna PROFESOR no cuentan como diferencia")
def test_el_orden_y_profesor_no_cuentan() -> None:
    """T037."""


@scenario(FEATURE, "Los códigos que no empiezan con 99 se aceptan con 8 cifras")
def test_los_codigos_sin_99() -> None:
    """T037."""


@scenario(FEATURE, "El conciliador no lee un archivo dentro de un repositorio")
def test_no_lee_dentro_de_un_repositorio() -> None:
    """T037."""


@scenario(FEATURE, "La conciliación no escribe en la base")
def test_la_conciliacion_no_escribe() -> None:
    """T037."""


# Dado

@given(parsers.re(r'una tabla maestra inventada en tmp_path con 5 estudiantes por sección en la 701, la 702 y la 703, '
                  r'códigos del rango 99 y calificaciones de 1 a 4'))
def _tabla_inventada(ctx: Escenario) -> None:
    ctx.extras["maestra"] = _maestra_de(_codigo_99)
    niveles = {int(f["CALIFICACIÓN"]) for f in _maestra(ctx).filas}
    assert niveles == {1, 2, 3, 4} and all(len(_maestra(ctx).de(s)) == 5 for s in SECCIONES)


@given(parsers.re(r'las cargas PUBLICADA de la 701, la 702 y la 703 con los mismos niveles de la tabla'))
def _cargas_iguales(ctx: Escenario) -> None:
    publicar_como_la_tabla(ctx)


@given(parsers.re(r'sus R-17 descargados en una carpeta de tmp_path'))
def _r17_descargados(ctx: Escenario) -> None:
    assert len(list(descargar_r17(ctx).glob("R017_5643_70*_2026-1*.xlsx"))) == 3


def _nivel_cambiado(ctx: Escenario) -> None:
    fila = next(f for f in _maestra(ctx).de("702") if f["CALIFICACIÓN"] == 3)
    fila["CALIFICACIÓN"] = 2


def _fila_mas(ctx: Escenario) -> None:
    _maestra(ctx).filas.append(_fila("701", _codigo_99("701", 6), 3))


def _fila_menos(ctx: Escenario) -> None:
    _maestra(ctx).filas.remove(_maestra(ctx).de("703")[-1])


def _pi_6_2(ctx: Escenario) -> None:
    for fila in _maestra(ctx).de("702"):
        fila["PI"], fila["SO"] = "6.2", "6"


def _m25_cambiado(ctx: Escenario) -> None:
    [ruta] = descargar_r17(ctx).glob("R017_5643_701_2026-1*.xlsx")
    libro = load_workbook(ruta)
    hoja = libro["Cursos de Carrera"]
    hoja["M25"] = hoja["M25"].value + 1
    libro.save(ruta)


DIFERENCIAS = {
    "la calificación de un estudiante de la 702 cambiada de 3 a 2": _nivel_cambiado,
    "una fila más en la 701 que la base no tiene": _fila_mas,
    "una fila menos en la 703": _fila_menos,
    "las filas de la 702 en el PI 6.2": _pi_6_2,
    "un R-17 descargado de la 701 con M25 cambiado": _m25_cambiado,
}


@given(parsers.re(r'las cargas PUBLICADA de las tres secciones y la tabla con (?P<diferencia>.+)'))
def _cargas_y_diferencia(ctx: Escenario, diferencia: str) -> None:
    publicar_como_la_tabla(ctx)
    DIFERENCIAS[diferencia](ctx)


@given(parsers.re(r'la carga PUBLICADA de la 701 y la 702 y la 703 sin carga PUBLICADA'))
def _sin_la_703(ctx: Escenario) -> None:
    publicar_como_la_tabla(ctx, ("701", "702"))
    assert ctx.cuenta("carga", "seccion_id = %s", ctx.seccion_de("703")) == 0


@given(parsers.re(r'la 701 con 2 de 3 estudiantes con nivel 3 o 4 en la base y en la tabla'))
def _dos_de_tres(ctx: Escenario) -> None:
    ctx.extras["maestra"] = _maestra_de(_codigo_99, {**NIVELES, "701": (3, 1, 4)})
    publicar_como_la_tabla(ctx)
    descargar_r17(ctx)


@given(parsers.re(r'la 703 con una carga REEMPLAZADA y su sucesora PUBLICADA con los mismos niveles'))
def _carga_reemplazada(ctx: Escenario) -> None:
    publicar_como_la_tabla(ctx, ("701", "702"))
    filas = [(str(f["CÓDIGO DEL ESTUDIANTE"]), int(f["CALIFICACIÓN"])) for f in _maestra(ctx).de("703")]
    # La primera carga trae las filas en otro orden, así sus bytes y su huella son otros que los de la sucesora.
    primera = publicar(ctx, "703", list(reversed(filas)))
    sucesora = publicar(ctx, "703", filas, reemplaza=primera, fecha="2026-07-16-00-00-00")
    assert ctx.filas("SELECT carga_id, estado FROM abet.carga WHERE carga_id IN (%s, %s) ORDER BY carga_id",
                     primera, sucesora) == [(primera, "REEMPLAZADA"), (sucesora, "PUBLICADA")]
    ctx.extras["reemplazo"] = (primera, sucesora)


@given(parsers.re(r'la tabla con las filas en otro orden y la columna PROFESOR llena'))
def _otro_orden(ctx: Escenario) -> None:
    publicar_como_la_tabla(ctx)
    _maestra(ctx).filas.reverse()
    assert all(fila["PROFESOR"] for fila in _maestra(ctx).filas)


@given(parsers.re(r'una tabla y una base inventadas con códigos de ocho cifras que no empiezan con 99, armados por la '
                  r'prueba en tmp_path'))
def _codigos_sin_99(ctx: Escenario) -> None:
    ctx.extras["maestra"] = _maestra_de(_codigo_sin_99)
    publicar_como_la_tabla(ctx, guardia=False)
    codigos = {fila[0] for fila in ctx.filas('SELECT "CÓDIGO DEL ESTUDIANTE" FROM abet.v_tabla_maestra_pi')}
    assert len(codigos) == 15 and not any(codigo.startswith("99") for codigo in codigos)


@given(parsers.re(r'la tabla inventada copiada dentro de una carpeta con \.git'))
def _dentro_de_un_repositorio(ctx: Escenario) -> None:
    repositorio = _carpeta(ctx, "repositorio")
    (repositorio / ".git").mkdir()
    ruta = _maestra(ctx).escribir(_carpeta(ctx, "entrada") / "tabla_maestra_inventada.xlsx")
    copia = repositorio / "datos" / ruta.name
    copia.parent.mkdir()
    shutil.copyfile(ruta, copia)
    # Sin permiso de lectura, un conciliador que abriera el archivo antes de la negativa terminaría con otro código.
    copia.chmod(0)
    ctx.pila.callback(copia.chmod, 0o600)
    ctx.extras["en_repositorio"] = copia


# Cuando

@when(parsers.re(r'el conciliador corre con --periodo 2026-1 --asignatura 5643 --pi 6\.1, la tabla y la carpeta de los '
                 r'R-17'))
def _corre_con_todo(ctx: Escenario) -> None:
    assert "r17" in ctx.extras
    correr(ctx)


@when("el conciliador corre")
def _corre(ctx: Escenario) -> None:
    correr(ctx)


@when(parsers.re(r'el conciliador corre con la opción de datos reales \(propuesta\)'))
def _corre_con_datos_reales(ctx: Escenario) -> None:
    correr(ctx, "--datos-reales")


@when("el conciliador corre con esa ruta")
def _corre_con_esa_ruta(ctx: Escenario) -> None:
    # Una base que no existe, así un conciliador que se conectara antes de la negativa terminaría con otro código.
    correr(ctx, maestra=ctx.extras["en_repositorio"], base="abet_demo_no_existe")


@when("el conciliador corre con el rol abet_respaldo")
def _corre_con_abet_respaldo(ctx: Escenario) -> None:
    # Sin cargas no habría nada que leer, así que el escenario publica las tres y descarga sus R-17 antes del conteo.
    publicar_como_la_tabla(ctx)
    descargar_r17(ctx)
    ctx.antes = ctx.conteos()
    corrida = correr(ctx, rol="abet_respaldo")
    assert corrida.returncode == 0, _salida(ctx)
    assert "3 de 3 secciones iguales." in _lineas(ctx)


# Entonces

@then(parsers.re(r'termina con código (?P<codigo>[0-9])'))
def _termina_con(ctx: Escenario, codigo: str) -> None:
    assert ctx.extras["corrida"].returncode == int(codigo), _salida(ctx)


@then(parsers.re(r'por cada sección dice «Sección 701\. Igual en 5 de 5 estudiantes, en el conteo por nivel y en el '
                 r'porcentaje\.» \(propuesta\)'))
def _cada_seccion_igual(ctx: Escenario) -> None:
    for seccion in SECCIONES:
        assert _igual(seccion, 5) in _lineas(ctx), _salida(ctx)


@then(parsers.re(r'el resumen dice «(?P<resumen>[0-9]+ de [0-9]+ secciones iguales\.)» \(propuesta\)'))
def _resumen(ctx: Escenario, resumen: str) -> None:
    assert _lineas(ctx)[-1] == resumen, _salida(ctx)


@then(parsers.re(r'dice (?P<citas>«[^»]+»(?: y «[^»]+»)*)(?: \(propuesta\))?'))
def _dice(ctx: Escenario, citas: str) -> None:
    for cita in re.findall(r"«([^»]+)»", citas):
        assert cita in _lineas(ctx), _salida(ctx)


@then("ninguna línea del informe trae un número de ocho cifras")
def _sin_ocho_cifras(ctx: Escenario) -> None:
    assert not OCHO_CIFRAS.findall(_salida(ctx)), _salida(ctx)


@then(parsers.re(r'la 701 es igual, porque compara el cociente 2 de 3 y el porcentaje con un decimal'))
def _mismo_cociente(ctx: Escenario) -> None:
    assert ctx.extras["corrida"].returncode == 0, _salida(ctx)
    assert _igual("701", 3) in _lineas(ctx) and _lineas(ctx)[-1] == "3 de 3 secciones iguales."
    # El caso no es vacío: la base redondea 2 de 3 a 66,7, el R-17 guarda 0,667 en E24 y 2/3 en M26.
    fila = ctx.filas("SELECT n_esperado_o_superior, n_total, pct_logro_sobre_calificados FROM abet.v_r17_por_pi"
                     " WHERE carga_id = %s", ctx.extras["cargas"]["701"])
    assert [(x, n, str(pct)) for x, n, pct in fila] == [(2, 3, "66.7")]
    [ruta] = ctx.extras["r17"].glob("R017_5643_701_2026-1*.xlsx")
    hoja = load_workbook(ruta, data_only=True)["Cursos de Carrera"]
    assert abs(hoja["E24"].value - 0.667) < 1e-12 and abs(hoja["M26"].value - 2 / 3) < 1e-12
    assert hoja["E24"].value != hoja["M26"].value


@then(parsers.re(r'la 703 trae 5 estudiantes y es igual, porque abet\.v_tabla_maestra_pi lee solo la carga PUBLICADA'))
def _reemplazada_sin_duplicar(ctx: Escenario) -> None:
    assert ctx.extras["corrida"].returncode == 0, _salida(ctx)
    assert _igual("703", 5) in _lineas(ctx)
    # abet.medicion guarda las filas de las dos cargas, y solo la vista deja fuera las de la REEMPLAZADA.
    primera, sucesora = ctx.extras["reemplazo"]
    assert ctx.cuenta("medicion", "carga_id IN (%s, %s)", primera, sucesora) == 10


@then("las tres secciones son iguales")
def _tres_iguales(ctx: Escenario) -> None:
    assert ctx.extras["corrida"].returncode == 0, _salida(ctx)
    for seccion in SECCIONES:
        assert _igual(seccion, 5) in _lineas(ctx)
    assert _lineas(ctx)[-1] == "3 de 3 secciones iguales."


@then(parsers.re(r'compara las secciones y su informe no trae ningún número de ocho cifras'))
def _compara_sin_99(ctx: Escenario) -> None:
    assert ctx.extras["corrida"].returncode == 0, _salida(ctx)
    assert _lineas(ctx)[-1] == "3 de 3 secciones iguales."
    assert not OCHO_CIFRAS.findall(_salida(ctx))
    # Sin la opción, los mismos códigos se rechazan por su fila, también sin mostrarlos.
    sin_la_opcion = correr(ctx)
    assert sin_la_opcion.returncode == 1, _salida(ctx)
    assert "Fila 2. El código del estudiante no es del rango inventado 99. Con datos reales, use --datos-reales." \
        in sin_la_opcion.stdout.splitlines()
    assert not OCHO_CIFRAS.findall(_salida(ctx))


@then(parsers.re(r'termina con código 2 antes de leer el archivo'))
def _codigo_2_antes_de_leer(ctx: Escenario) -> None:
    corrida = ctx.extras["corrida"]
    assert corrida.returncode == 2, _salida(ctx)
    assert "La tabla maestra está dentro de un repositorio git. Use una copia fuera de los repositorios." \
        in corrida.stdout.splitlines()
    assert "Sección" not in corrida.stdout and not corrida.stderr


@then(parsers.re(r'un INSERT del conciliador fallaría con el SQLSTATE 25006 de la transacción READ ONLY'))
def _insert_de_solo_lectura(ctx: Escenario) -> None:
    # Con el dueño de la base, que sí puede escribir, así lo que detiene el INSERT es la transacción y no el rol.
    conexion = modulo().abrir(ctx.api.base.conexion)
    try:
        try:
            conexion.execute("INSERT INTO abet.estudiante (codigo) VALUES (%s)", (_codigo_99("709", 1),))
        except psycopg.Error as falla:
            assert falla.sqlstate == SQLSTATE_SOLO_LECTURA, falla
        else:
            raise AssertionError("el INSERT no falló en la conexión del conciliador")
    finally:
        conexion.close()
    assert ctx.cuenta("estudiante", "codigo = %s", _codigo_99("709", 1)) == 0


# Ensayo de US-84 (T057), con los exports del generador de US-74 y db/herramientas/ensayar_capacitacion.py

@scenario(FEATURE, "El ensayo sube los exports generados y deja las secciones iguales")
def test_el_ensayo_deja_las_secciones_iguales() -> None:
    """T057."""


@scenario(FEATURE, "El manifiesto del generador y lo publicado coinciden por huella y por conteo")
def test_el_manifiesto_y_lo_publicado_coinciden() -> None:
    """T057."""


@scenario(FEATURE, "Un nivel distinto en el ensayo se nombra sin el código y detiene la conclusión")
def test_un_nivel_distinto_detiene_la_conclusion() -> None:
    """T057."""


@scenario(FEATURE, "El ensayo corre en una base aparte y no deja huellas en la de la capacitación")
def test_el_ensayo_corre_en_una_base_aparte() -> None:
    """T057."""


def generar_exports(ctx: Escenario, maestra: Maestra, nombre: str = "exports") -> Path:
    """Exports y manifiesto del generador de US-74, como proceso aparte, con una programación inventada que da a cada
    sección de la tabla su curso SINTETICO_20261_5643_70N."""
    entrada = _carpeta(ctx, f"entrada_{nombre}")
    tabla = maestra.escribir(entrada / "tabla_maestra_inventada.xlsx")
    secciones = sorted({str(fila["SECCIÓN"]) for fila in maestra.filas}, key=int)
    programacion = entrada / "programacion_20261_inventada.csv"
    programacion.write_text("periodo,asignatura,seccion,correo,curso_blackboard\r\n" + "".join(
        f"2026-1,5643,{s},docente{s}@example.invalid,SINTETICO_20261_5643_{s}\r\n" for s in secciones), encoding="utf-8")
    salida = _tmp(ctx) / nombre
    corrida = subprocess.run([sys.executable, "-I", str(GENERADOR), "--maestra", str(tabla), "--programacion",
                              str(programacion), "--salida", str(salida), "--periodo", "2026-1", "--asignatura", "5643",
                              "--pi", "6.1", "--fecha", FECHA], capture_output=True, text=True, encoding="utf-8",
                             check=False, cwd=_tmp(ctx))
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    ctx.extras["exports"] = salida
    return salida


def manifiesto(ctx: Escenario) -> dict[str, Any]:
    return json.loads((ctx.extras["exports"] / "manifiesto.json").read_text(encoding="utf-8"))


def ensayar(ctx: Escenario, *extra: str, r17: str = "r17_del_ensayo") -> subprocess.CompletedProcess[str]:
    """Corre el ensayo con python -I sobre los exports del escenario, la tabla maestra sin cambios y una carpeta nueva
    para los R-17, con las variables de libpq hacia la copia desechable del escenario y su dueño, que puede escribir.
    El conciliador que llama el ensayo lee con abet_respaldo."""
    _roles_de_lectura(ctx)
    tabla = _maestra(ctx).escribir(_carpeta(ctx, "entrada") / "tabla_maestra_inventada.xlsx")
    entorno = {**ctx.request.getfixturevalue("base_desechable")._entorno(), "PGDATABASE": ctx.api.base.nombre}
    argumentos = ["--exports", str(ctx.extras["exports"]), "--maestra", str(tabla), "--r17", str(_tmp(ctx) / r17),
                  "--reglas", REGLAS]
    corrida = subprocess.run([sys.executable, "-I", str(ENSAYO), *argumentos, *extra], env=entorno,
                             capture_output=True, text=True, encoding="utf-8", check=False, cwd=_tmp(ctx))
    ctx.extras["corrida"] = corrida
    return corrida


def _cargas_del_curso(ctx: Escenario, conexion: psycopg.Connection | None = None) -> list[tuple[Any, ...]]:
    return (conexion or ctx.api.dueno).execute(
        "SELECT s.numero, c.estado, c.filas_aceptadas, c.filas_rechazadas, ao.sha256 FROM abet.carga c"
        " JOIN abet.archivo_origen ao ON ao.archivo_id = c.archivo_id JOIN abet.seccion s USING (seccion_id)"
        " JOIN abet.asignatura a USING (asignatura_id) WHERE a.codigo = '5643' ORDER BY s.numero").fetchall()


@given(parsers.re(r'los exports de la 701, la 702 y la 703 que el generador de US-74 arma desde la tabla inventada, con '
                  r'su manifiesto'))
def _exports_generados_de_las_tres(ctx: Escenario) -> None:
    generar_exports(ctx, _maestra(ctx))
    assert [entrada["seccion"] for entrada in manifiesto(ctx)["exports"]] == list(SECCIONES)


@given("los exports generados con su manifiesto")
def _exports_generados(ctx: Escenario) -> None:
    generar_exports(ctx, _maestra(ctx))


@given(parsers.re(r'el export de la 702 con el nivel de un estudiante cambiado de 3 a 2 frente a la tabla'))
def _export_con_un_nivel_cambiado(ctx: Escenario) -> None:
    # Los exports salen de una copia de la tabla con el cambio, así el manifiesto describe lo que se sube, y el
    # conciliador compara con la tabla sin cambios.
    copia = Maestra([dict(fila) for fila in _maestra(ctx).filas])
    fila = next(f for f in copia.de("702") if f["CALIFICACIÓN"] == 3)
    fila["CALIFICACIÓN"] = 2
    generar_exports(ctx, copia)
    [entrada] = [e for e in manifiesto(ctx)["exports"] if e["seccion"] == "702"]
    assert entrada["niveles"]["2"] == sum(1 for f in _maestra(ctx).de("702") if f["CALIFICACIÓN"] == 2) + 1


@given("una base para el ensayo y otra para la capacitación")
def _dos_bases(ctx: Escenario) -> None:
    # La del ensayo es la de los Antecedentes, y la de la capacitación es otra copia de la misma plantilla.
    capacitacion = ctx.plantillas.copia("quimica_plan", ctx.pila)
    conexion = ctx.pila.enter_context(psycopg.connect(capacitacion.conexion, autocommit=True))
    assert conexion.info.dbname != ctx.api.base.nombre
    ctx.extras["capacitacion"] = conexion
    ctx.extras["archivos_antes"] = conexion.execute("SELECT count(*) FROM abet.archivo_origen").fetchone()[0]
    generar_exports(ctx, _maestra(ctx))


@when(parsers.re(r'el ensayo sube cada export con la biblioteca abet_carga y descarga su R-17'))
def _ensayo_sube_y_descarga(ctx: Escenario) -> None:
    ensayar(ctx)


@when("el ensayo termina")
def _ensayo_termina(ctx: Escenario) -> None:
    corrida = ensayar(ctx)
    assert corrida.returncode == 0, _salida(ctx)


@when("el ensayo sube los exports y corre el conciliador")
def _ensayo_con_conciliador(ctx: Escenario) -> None:
    ensayar(ctx)


@when("el ensayo sube los exports en la base del ensayo")
def _ensayo_en_su_base(ctx: Escenario) -> None:
    corrida = ensayar(ctx)
    assert corrida.returncode == 0, _salida(ctx)


@then("cada carga queda PUBLICADA con 0 filas rechazadas")
def _cargas_publicadas_sin_rechazos(ctx: Escenario) -> None:
    filas = [(numero, estado, aceptadas, rechazadas) for numero, estado, aceptadas, rechazadas, _ in _cargas_del_curso(ctx)]
    assert filas == [(s, "PUBLICADA", 5, 0) for s in SECCIONES], _salida(ctx)
    assert ctx.cuenta("rechazo_fila") == 0
    # Cada carga la sube el profesor de su sección, como en la sala, y cada R-17 queda en la carpeta del ensayo.
    subidas = ctx.filas("SELECT s.numero, u.correo FROM abet.carga c JOIN abet.seccion s USING (seccion_id)"
                        " JOIN acceso.usuario_autorizado u ON u.usuario_id = c.subida_por ORDER BY s.numero")
    assert subidas == [(s, f"docente{s}@example.invalid") for s in SECCIONES]
    assert sorted(ruta.name for ruta in (_tmp(ctx) / "r17_del_ensayo").iterdir()) == \
        [f"R017_5643_{s}_2026-1_PROVISIONAL.xlsx" for s in SECCIONES]


@then(parsers.re(r'el conciliador dice (?P<citas>«[^»]+»(?: y «[^»]+»)*)(?: y termina con código (?P<codigo>[0-9]))?'))
def _el_conciliador_dice(ctx: Escenario, citas: str, codigo: str | None) -> None:
    lineas = _lineas(ctx)
    # Las líneas del conciliador van en el informe del ensayo, después de su encabezado.
    assert "Conciliación de 5643 en 2026-1, PI 6.1." in lineas, _salida(ctx)
    despues = lineas[lineas.index("Conciliación de 5643 en 2026-1, PI 6.1."):]
    for cita in re.findall(r"«([^»]+)»", citas):
        assert cita in despues, _salida(ctx)
    if codigo is not None:
        assert ctx.extras["corrida"].returncode == int(codigo), _salida(ctx)
    assert not OCHO_CIFRAS.findall(_salida(ctx)), _salida(ctx)


@then(parsers.re(r'cada abet\.archivo_origen tiene la huella SHA-256 que el manifiesto da para su sección'))
def _huellas_del_manifiesto(ctx: Escenario) -> None:
    entradas = manifiesto(ctx)["exports"]
    for entrada in entradas:
        contenido = (ctx.extras["exports"] / entrada["archivo"]).read_bytes()
        assert hashlib.sha256(contenido).hexdigest() == entrada["sha256"]
    publicadas = {numero: sha.strip() for numero, _, _, _, sha in _cargas_del_curso(ctx)}
    assert publicadas == {entrada["seccion"]: entrada["sha256"] for entrada in entradas}
    assert ctx.uno("SELECT count(*) FROM abet.archivo_origen") == len(entradas) == 3


@then(parsers.re(r'el conteo por nivel de cada sección en abet\.v_r17_por_pi es el del manifiesto'))
def _conteo_del_manifiesto(ctx: Escenario) -> None:
    vista = {numero: {"1": n1, "2": n2, "3": n3, "4": n4} for numero, n1, n2, n3, n4 in ctx.filas(
        "SELECT seccion, n_nivel_1, n_nivel_2, n_nivel_3, n_nivel_4 FROM abet.v_r17_por_pi"
        " WHERE periodo = '2026-1' AND codigo_asignatura = '5643' AND pi = '6.1'")}
    assert vista == {entrada["seccion"]: entrada["niveles"] for entrada in manifiesto(ctx)["exports"]}


@then(parsers.re(r'el ensayo termina con código (?P<codigo>[0-9])'))
def _el_ensayo_termina_con(ctx: Escenario, codigo: str) -> None:
    corrida = ctx.extras["corrida"]
    assert corrida.returncode == int(codigo), _salida(ctx)
    if codigo != "0":
        assert _lineas(ctx)[-1] == "Ensayo con diferencias. No se da por bueno hasta resolverlas.", _salida(ctx)


@then(parsers.re(r'la base de la capacitación no gana ninguna fila en abet\.archivo_origen'))
def _capacitacion_sin_huellas(ctx: Escenario) -> None:
    capacitacion = ctx.extras["capacitacion"]
    assert capacitacion.execute("SELECT count(*) FROM abet.archivo_origen").fetchone()[0] == ctx.extras["archivos_antes"]
    # El ensayo sí escribió, en su propia base.
    assert ctx.uno("SELECT count(*) FROM abet.archivo_origen") == 3


def _subir_en(conexion: psycopg.Connection, entrada: dict[str, Any], carpeta: Path) -> Any:
    """Sube el export de la entrada del manifiesto en la base de la conexión, como el profesor de su sección."""
    seccion_id, usuario_id = conexion.execute(
        "SELECT s.seccion_id, d.usuario_id FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
        " JOIN abet.periodo pe ON pe.periodo_id = s.periodo_id JOIN acceso.docente_seccion d USING (seccion_id)"
        " WHERE a.codigo = '5643' AND pe.codigo = '2026-1' AND s.numero = %s", (entrada["seccion"],)).fetchone()
    return cargar(conexion, (carpeta / entrada["archivo"]).read_bytes(), nombre_archivo=entrada["archivo"],
                  seccion_id=seccion_id, usuario_id=usuario_id, configuracion=Configuracion(REGLAS))


@then(parsers.re(r'la misma subida en la base de la capacitación crea cargas nuevas y no devuelve la constancia de una '
                 r'carga del ensayo'))
def _subida_nueva_en_la_capacitacion(ctx: Escenario) -> None:
    capacitacion, carpeta = ctx.extras["capacitacion"], ctx.extras["exports"]
    for entrada in manifiesto(ctx)["exports"]:
        resultado = _subir_en(capacitacion, entrada, carpeta)
        assert resultado.resultado is Resultado.PUBLICADA and resultado.codigo_http == 201, resultado
        # En la base del ensayo, la misma subida devuelve la carga que el ensayo ya publicó, y eso evita la base aparte.
        en_el_ensayo = _subir_en(ctx.api.dueno, entrada, carpeta)
        assert en_el_ensayo.resultado is Resultado.YA_PUBLICADA, en_el_ensayo
    assert capacitacion.execute("SELECT count(*) FROM abet.archivo_origen").fetchone()[0] == 3
    assert [fila[:4] for fila in _cargas_del_curso(ctx, capacitacion)] == [(s, "PUBLICADA", 5, 0) for s in SECCIONES]


# Pruebas del ensayo fuera del .feature, con las secciones inventadas 701 a 704 de quimica_2026_1_inventado.sql

NIVELES_704 = (1, 3, 4, 4, 2)


def _base_del_ensayo(ctx: Escenario, *, profesor_704: bool) -> None:
    """La base de los Antecedentes y una tabla con la 704, que la siembra inventada deja sin profesor."""
    ctx.crear_base("quimica_plan")
    ctx.extras["maestra"] = _maestra_de(_codigo_99)
    ctx.extras["maestra"].filas += [_fila("704", _codigo_99("704", n), nivel)
                                    for n, nivel in enumerate(NIVELES_704, start=1)]
    if profesor_704:
        ctx.api.dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol)"
                              " VALUES ('docente704@example.invalid', 'PROFESOR')")
        ctx.api.dueno.execute("INSERT INTO acceso.docente_seccion (usuario_id, seccion_id) VALUES (%s, %s)",
                              (ctx.usuario_id("docente704@example.invalid"), ctx.seccion_de("704")))
    generar_exports(ctx, _maestra(ctx))


def test_el_ensayo_recorre_las_secciones_701_a_704(ctx: Escenario) -> None:
    """Debe publicar las cuatro secciones, descargar sus cuatro R-17 y terminar con «4 de 4 secciones iguales.». No debe
    mostrar un número de ocho cifras."""
    _base_del_ensayo(ctx, profesor_704=True)
    corrida = ensayar(ctx)
    assert corrida.returncode == 0, _salida(ctx)
    secciones = (*SECCIONES, "704")
    for seccion in secciones:
        assert _igual(seccion, 5) in _lineas(ctx), _salida(ctx)
        assert f"Sección {seccion}. Carga PUBLICADA con 5 filas aceptadas y 0 rechazadas, y su R-17 descargado." \
            in _lineas(ctx), _salida(ctx)
    assert "4 de 4 secciones iguales." in _lineas(ctx)
    assert _lineas(ctx)[-1] == "Ensayo sin diferencias. Las 4 secciones salen iguales a la tabla maestra."
    assert [fila[:4] for fila in _cargas_del_curso(ctx)] == [(s, "PUBLICADA", 5, 0) for s in secciones]
    assert len(list((_tmp(ctx) / "r17_del_ensayo").glob("R017_5643_70*_2026-1*.xlsx"))) == 4
    assert not OCHO_CIFRAS.findall(_salida(ctx))


def test_una_seccion_sin_profesor_detiene_el_ensayo_antes_de_subir(ctx: Escenario) -> None:
    """Debe nombrar la 704 sin profesor y terminar con 1. No debe subir ninguna sección ni escribir un R-17."""
    _base_del_ensayo(ctx, profesor_704=False)
    corrida = ensayar(ctx)
    assert corrida.returncode == 1, _salida(ctx)
    assert "Sección 704. No tiene un profesor asignado en la base del ensayo." in _lineas(ctx), _salida(ctx)
    assert _lineas(ctx)[-1] == "Ensayo detenido antes de subir. No se cargó ningún archivo."
    assert ctx.uno("SELECT count(*) FROM abet.archivo_origen") == 0
    assert not (_tmp(ctx) / "r17_del_ensayo").exists() or not any((_tmp(ctx) / "r17_del_ensayo").iterdir())


def test_una_base_con_cargas_del_curso_detiene_el_ensayo(ctx: Escenario) -> None:
    """Debe negarse a correr otra vez sobre una base con cargas de 5643 en 2026-1 y terminar con 1. No debe sumar
    filas a abet.archivo_origen ni a abet.carga."""
    _base_del_ensayo(ctx, profesor_704=True)
    assert ensayar(ctx).returncode == 0, _salida(ctx)
    antes = ctx.conteos()
    corrida = ensayar(ctx, r17="r17_segunda_vez")
    assert corrida.returncode == 1, _salida(ctx)
    assert "La base ya tiene cargas de 5643 en 2026-1. El ensayo corre en una base aparte, sin cargas del curso (J-52)." \
        in _lineas(ctx), _salida(ctx)
    assert ctx.conteos() == antes


def test_el_conciliador_del_ensayo_lee_con_el_rol_de_lectura(ctx: Escenario) -> None:
    """Debe pasar --rol-lectura al conciliador, así un rol que no existe da el 3 de la base que no responde aunque el
    rol que carga sí exista. No debe leer con el rol que carga ni dar por bueno el ensayo."""
    _base_del_ensayo(ctx, profesor_704=True)
    corrida = ensayar(ctx, "--rol-lectura", "abet_rol_que_no_existe")
    assert corrida.returncode == 3, _salida(ctx)
    assert _lineas(ctx)[-1] == "La base no responde. Revise las variables de conexión de libpq.", _salida(ctx)
    assert ctx.uno("SELECT count(*) FROM abet.carga WHERE estado = 'PUBLICADA'") == 4


def test_los_codigos_sin_99_piden_la_opcion_de_datos_reales(ctx: Escenario) -> None:
    """Con códigos de ocho cifras que no empiezan con 99, armados aquí, debe detenerse por la guardia sin la opción y
    dejar las secciones iguales con --datos-reales. No debe mostrar un número de ocho cifras en ninguna de las dos."""
    ctx.crear_base("quimica_plan")
    ctx.extras["maestra"] = _maestra_de(_codigo_sin_99)
    generar_exports(ctx, _maestra(ctx))
    sin_la_opcion = ensayar(ctx)
    assert sin_la_opcion.returncode == 1, _salida(ctx)
    assert "Sección 701. La carga no quedó PUBLICADA (GUARDIA)." in _lineas(ctx), _salida(ctx)
    assert _lineas(ctx)[-1] == "Ensayo con diferencias. No se da por bueno hasta resolverlas."
    assert ctx.uno("SELECT count(*) FROM abet.carga") == 0
    assert not OCHO_CIFRAS.findall(_salida(ctx))
    con_la_opcion = ensayar(ctx, "--datos-reales", r17="r17_con_datos_reales")
    assert con_la_opcion.returncode == 0, _salida(ctx)
    assert "3 de 3 secciones iguales." in _lineas(ctx)
    assert not OCHO_CIFRAS.findall(_salida(ctx))
