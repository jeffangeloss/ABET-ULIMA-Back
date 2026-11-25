"""Pasos de programacion_con_nombre.feature (US-96 de la spec 010, BR-ACCESO-15 y BR-ACCESO-11), con pytest-bdd.

El .feature manda. El guion db/herramientas/cargar_programacion.py corre como proceso aparte con python -I y las variables
de libpq de la copia del escenario, que arma tests/cargas_de_prueba.entorno_de_programacion() en el clúster desechable y
nunca en localhost:5432. Los Antecedentes y la corrida viven en el conftest.py de esta carpeta (correr_guion_006), y los
pasos del informe son los de programacion_docente.feature de la spec 006, repetidos aquí porque un paso vive solo en su
módulo. Cada «Entonces» se comprueba contra el informe del guion o la base, nunca con un doble. Ningún mensaje de falla
repite un nombre.

Los nombres de los Ejemplos llevan \\n escrito como secuencia, que decodificar() convierte en el salto de línea. Gherkin ya
convierte \\n de una celda, y decodificar() lo deja como está. «Un nombre de 121 letras» es «Profesor Inventado » seguido de
letras hasta sumar 121 caracteres. El texto «(propuesta)» al final de un paso solo marca que la línea no está fijada en
las decisiones de la spec, y el paso exige la línea completa igual.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from pytest_bdd import given, parsers, scenario, then, when

Escenario = Any
FEATURE = "specs/010-nombre-del-profesor/aceptacion/programacion_con_nombre.feature"
CP = sys.modules["cargas_de_prueba"]
PROPUESTA = r"(?: \(propuestas?\))?"


@scenario(FEATURE, "Un profesor nuevo entra con su nombre")
def test_un_profesor_nuevo_entra_con_su_nombre() -> None:
    """US-96, escenario 1."""


@scenario(FEATURE, "Un profesor ya cargado sin nombre lo recibe y su rol y su estado no cambian")
def test_un_profesor_ya_cargado_recibe_su_nombre() -> None:
    """US-96, escenario 2."""


@scenario(FEATURE, "Un nombre que ya existe no se cambia")
def test_un_nombre_que_ya_existe_no_se_cambia() -> None:
    """US-96, escenario 3."""


@scenario(FEATURE, "Un archivo sin la columna nombre responde como en la spec 006")
def test_un_archivo_sin_la_columna_nombre_responde_como_la_spec_006() -> None:
    """US-96, escenario 4."""


@scenario(FEATURE, "Los espacios del nombre se normalizan antes de guardarlo")
def test_los_espacios_del_nombre_se_normalizan() -> None:
    """US-96, escenario 5."""


@scenario(FEATURE, "Un nombre inválido rechaza el archivo antes de conectarse")
def test_un_nombre_invalido_rechaza_el_archivo() -> None:
    """US-96, escenario 6, con cuatro casos."""


@scenario(FEATURE, "Dos nombres distintos para un mismo correo rechazan el archivo")
def test_dos_nombres_distintos_rechazan_el_archivo() -> None:
    """US-96, escenario 7."""


def _conftest(ctx: Escenario) -> Any:
    """Módulo conftest.py de esta carpeta, que pytest registra como plugin, para reutilizar sus ayudas."""
    for plugin in ctx.request.config.pluginmanager.get_plugins():
        if (getattr(plugin, "__file__", "") or "").endswith("aceptacion/pasos/conftest.py"):
            return plugin
    raise AssertionError("no se encuentra tests/aceptacion/pasos/conftest.py")


def decodificar(texto: str) -> str:
    """Convierte la secuencia \\n de un Ejemplo en el salto de línea, y deja un salto que Gherkin ya convirtió."""
    return re.sub(r"\\u([0-9A-Fa-f]{4})", lambda c: chr(int(c.group(1), 16)), texto.replace("\\n", "\n"))


def _nombre_del_ejemplo(texto: str) -> str:
    if texto == "un nombre de 121 letras":
        nombre = "Profesor Inventado " + "a" * 102
        assert len(nombre) == 121
        return nombre
    coincide = re.fullmatch(r'(?s)"(.*)"', texto)
    assert coincide is not None, f"No se reconoce el nombre {texto!r}."
    return decodificar(coincide.group(1))


def _informe(ctx: Escenario) -> list[str]:
    corrida = ctx.extras.get("corrida_006")
    assert corrida is not None, "el escenario todavía no corrió el guion"
    return corrida.stdout.splitlines()


# Dado, el archivo

@given(parsers.re(r'el archivo base de la spec 006, sin la columna nombre(?P<aplicado>, ya aplicado con --aplicar)?'))
def _archivo_sin_nombre(ctx: Escenario, aplicado: str | None) -> None:
    conftest = _conftest(ctx)
    base = conftest.ArchivoDeProgramacion()
    assert "nombre" not in base.encabezados
    if aplicado is None:
        # El archivo del escenario pasa a ser el base de la spec 006, sin la columna.
        ctx.extras["archivo_006"] = base
        return
    # Una corrida anterior con el archivo base, en otra carpeta, que no cambia el archivo con nombres del escenario.
    previa = ctx.request.getfixturevalue("tmp_path") / "previa"
    previa.mkdir()
    corrida = conftest.correr_guion_006(
        ctx, "--periodo", "2026-2", "--archivo", str(conftest.escribir_archivo_006(ctx, base, previa)), aplicar=True)
    assert corrida.returncode == 0 and corrida.stdout.splitlines()[-1] == "Cambios guardados.", corrida.stdout
    assert ctx.uno("SELECT count(*) FROM acceso.usuario_autorizado WHERE nombre IS NOT NULL") == 0


@given(parsers.re(r'el archivo base con nombres con la fila (?P<fila>[0-9]+) cambiada al nombre (?P<nombre>"(?s:.*)"|un nombre de 121 letras)'))
def _fila_con_otro_nombre(ctx: Escenario, fila: str, nombre: str) -> None:
    archivo = _conftest(ctx).archivo_006(ctx)
    assert archivo.encabezados[-1] == "nombre"
    archivo.filas[int(fila) - 2][-1] = _nombre_del_ejemplo(nombre)


@given(parsers.re(r'el archivo base con nombres con una fila (?P<fila>[0-9]+) de la (?P<numero>[0-9]+) de '
                  r'(?P<asignatura>[0-9]+) con "(?P<correo>[^"]+)" y el nombre "(?P<nombre>[^"]+)"'))
def _fila_de_otra_asignatura(ctx: Escenario, fila: str, numero: str, asignatura: str, correo: str, nombre: str) -> None:
    archivo = _conftest(ctx).archivo_006(ctx)
    assert len(archivo.filas) + 2 == int(fila), f"la fila {fila} no va al final del archivo"
    archivo.filas.append(["2026-2", asignatura, numero, correo, "", nombre])


# Dado, la base

@given(parsers.re(r'"(?P<correo>[^"]+)" ya cargado con el nombre "(?P<nombre>[^"]+)"'))
def _ya_cargado_con_nombre(ctx: Escenario, correo: str, nombre: str) -> None:
    ctx.api.dueno.execute("INSERT INTO acceso.usuario_autorizado (correo, rol, nombre) VALUES (%s, 'PROFESOR', %s)",
                          (correo, nombre))
    ctx.extras["nombre_previo"] = (correo, nombre)


# Cuando

@when(parsers.re(r'el administrador corre el guion con (?:el archivo base con nombres|ese archivo) y --aplicar'))
def _corre_con_aplicar(ctx: Escenario) -> None:
    _conftest(ctx).correr_guion_006(ctx, aplicar=True)


# Entonces, el informe y el código

@then(parsers.re(r'el guion termina con código (?P<codigo>[0-9])(?P<sin> sin conectarse a la base)?'
                 r'(?P<tablas> y ninguna de las tres tablas cambia)?'))
def _termina_con(ctx: Escenario, codigo: str, sin: str | None, tablas: str | None) -> None:
    conftest = _conftest(ctx)
    corrida = ctx.extras["corrida_006"]
    assert corrida.returncode == int(codigo), corrida.stdout + corrida.stderr
    if sin is not None:
        # Sin servidor, un intento de conexión daría el código 3, así que el mismo archivo da el mismo informe sin tocar psql.
        tmp_path: Path = ctx.request.getfixturevalue("tmp_path")
        carpeta = tmp_path / "sin_servidor"
        carpeta.mkdir()
        entorno = CP.entorno_de_programacion(ctx.api.base.nombre, sin_servidor=carpeta)
        archivo = conftest.escribir_archivo_006(ctx, conftest.archivo_006(ctx), carpeta)
        sin_base = CP.correr_programacion(entorno, "--periodo", "2026-2", "--archivo", str(archivo), "--aplicar")
        assert sin_base.returncode == int(codigo) and sin_base.stdout == corrida.stdout, sin_base.stdout + sin_base.stderr
    if sin is not None or tablas is not None:
        assert ctx.extras["antes_006"] == conftest.tres_tablas_006(ctx), "las tres tablas cambiaron"


@then(parsers.re(rf'el informe dice «(?P<linea>[^»]+)»{PROPUESTA}'))
def _informe_dice(ctx: Escenario, linea: str) -> None:
    assert linea in _informe(ctx), _informe(ctx)


@then(parsers.re(rf'la línea final es «(?P<linea>[^»]+)»{PROPUESTA}'))
def _linea_final(ctx: Escenario, linea: str) -> None:
    assert _informe(ctx)[-1:] == [linea], _informe(ctx)


@then(parsers.re(r'ningún texto del informe repite (?:un nombre|el nombre de la fila (?P<fila>[0-9]+))'))
def _sin_nombres_en_el_informe(ctx: Escenario, fila: str | None) -> None:
    corrida = ctx.extras["corrida_006"]
    texto = corrida.stdout + corrida.stderr
    archivo = _conftest(ctx).archivo_006(ctx)
    del_archivo = [f[-1] for f in archivo.filas if archivo.encabezados[-1] == "nombre"]
    if fila is not None:
        del_archivo = [archivo.filas[int(fila) - 2][-1]]
    de_la_base = [n for (n,) in ctx.filas("SELECT nombre FROM acceso.usuario_autorizado WHERE nombre IS NOT NULL")]
    nombres = [n.strip() for n in (*del_archivo, *de_la_base) if n and n.strip()]
    assert nombres, "el escenario no tiene ningún nombre que buscar"
    assert not [n for n in nombres if n in texto], "el informe repite un nombre"
    # Las palabras de la forma inventada tampoco salen sueltas en ningún mensaje, salvo el nombre de la herramienta.
    assert "Profesor Inventado" not in texto


# Entonces, la base

@then(parsers.re(r'acceso\.usuario_autorizado trae "(?P<correo>[^"]+)" con rol "(?P<rol>[A-Z]+)", activo y el nombre '
                 r'"(?P<nombre>[^"]+)"'))
def _usuario_con_nombre(ctx: Escenario, correo: str, rol: str, nombre: str) -> None:
    assert ctx.filas("SELECT rol, activo, nombre FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [
        (rol, True, nombre)]


@then(parsers.re(r'"(?P<a>[^"]+)" y "(?P<b>[^"]+)" quedan con sus nombres del archivo'))
def _quedan_con_sus_nombres(ctx: Escenario, a: str, b: str) -> None:
    del_archivo = {fila[3]: fila[-1] for fila in _conftest(ctx).archivo_006(ctx).filas}
    for correo in (a, b):
        assert ctx.filas("SELECT nombre FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(del_archivo[correo],)]


@then(parsers.re(r'"(?P<correo>[^"]+)" sigue con rol "(?P<rol>[A-Z]+)" y activo falso'))
def _sigue_de_baja(ctx: Escenario, correo: str, rol: str) -> None:
    assert ctx.filas("SELECT rol, activo FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(rol, False)]


@then(parsers.re(r'el nombre de "(?P<correo>[^"]+)" sigue siendo "(?P<nombre>[^"]+)"'))
def _el_nombre_sigue(ctx: Escenario, correo: str, nombre: str) -> None:
    assert ctx.filas("SELECT nombre FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(nombre,)]


@then(parsers.re(r'"(?P<correo>[^"]+)" queda con el nombre "(?P<nombre>[^"]+)"'))
def _queda_con_el_nombre(ctx: Escenario, correo: str, nombre: str) -> None:
    assert ctx.filas("SELECT nombre FROM acceso.usuario_autorizado WHERE correo = %s", correo) == [(nombre,)]


@then("ningún usuario tiene nombre")
def _ningun_usuario_tiene_nombre(ctx: Escenario) -> None:
    assert ctx.uno("SELECT count(*) FROM acceso.usuario_autorizado") >= 2
    assert ctx.uno("SELECT count(*) FROM acceso.usuario_autorizado WHERE nombre IS NOT NULL") == 0
