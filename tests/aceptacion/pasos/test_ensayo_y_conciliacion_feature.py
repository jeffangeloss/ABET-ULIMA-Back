"""Pasos de ensayo_y_conciliacion.feature (US-83 de la spec 008), con pytest-bdd en español (T037).

El .feature manda. Los Antecedentes arman la base de la spec 008 con el plan de 5643 en 2026-1 y los datos inventados
de Química General, en el clúster desechable de tests/cluster_desechable.py y nunca en localhost:5432, y una tabla
maestra INVENTADA en tmp_path con las secciones 701 a 703, códigos del rango 99 y profesores inventados. Las cargas se
publican con la biblioteca abet_carga, como lo hará el ensayo de US-84, y cada R-17 se descarga con abet_carga.r17.

El conciliador db/herramientas/conciliar_tabla_maestra.py corre como proceso aparte, como lo correría Jefferson, con
las variables de libpq hacia la copia desechable del escenario y el rol abet_respaldo, que crea
db/plataforma/neon/crear_roles_lectura.sql en esa copia. Cada «Entonces» se comprueba con el código de salida y el
informe del proceso, con la base desechable o con las celdas del R-17, sin dobles del conciliador.

Los escenarios del ensayo de US-84 son de T057 y quedan sin pasos aquí.
"""

from __future__ import annotations

import importlib.util
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
from pytest_bdd import given, parsers, scenario, then, when

from abet_carga import r17
from abet_carga.carga import Configuracion, Resultado, cargar

Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/ensayo_y_conciliacion.feature"
CONCILIADOR = RAIZ / "db" / "herramientas" / "conciliar_tabla_maestra.py"
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
