"""Pasos de carga_quimica.feature (US-75 a US-77 de la spec 008), con pytest-bdd en español (T024, T035).

El .feature manda. Los Antecedentes arman la base de la spec 008 con el plan de 5643 en 2026-1 y los datos inventados
de Química General, en el clúster desechable de tests/cluster_desechable.py y nunca en localhost:5432. Cada «Entonces»
se comprueba con la respuesta de la API, con la constancia de la ruta 6, con el registro de la aplicación o con la base
desechable, sin dobles del sistema bajo prueba. Los exports se arman en memoria con scripts/generar_exports_inventados.py
y ninguno entra a tests/datos_inventados/.

Aquí están Q21 (T024), la subida de 5643 en Industrial de US-75 y los errores probables de la sala de US-76 (T035), que
pasan con abet_carga/ sin cambios, y el export que arma scripts/generar_exports_desde_maestra.py de US-74 (T034),
que corre como proceso aparte sobre una tabla maestra inventada en tmp_path. Los consejos de P4 de US-77 llevan
@delegado_a_vitest y los prueba Vitest en el Front.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from pytest_bdd import given, parsers, scenario, then, when

Escenario = Any
A = sys.modules["api_de_prueba"]
RAIZ = Path(__file__).resolve().parents[3]
FEATURE = "specs/008-ciclo-quimica-industrial/aceptacion/carga_quimica.feature"
COLUMNA_6_1 = "ABET SO6.1 [Total Pts: 4 Score] |9000061"
COLUMNA_6_1_SOBRE_20 = "ABET SO6.1 [Total Pts: 20 Score] |9000061"
FECHA = "2026-07-15-00-00-00"
GENERADOR = RAIZ / "scripts" / "generar_exports_desde_maestra.py"
OCHO_CIFRAS = re.compile(r"(?<![0-9])[0-9]{8}(?![0-9])")


@scenario(FEATURE, "Q21 detecta una sección cuyo curso de Blackboard declara otra sección")
def test_q21_detecta_una_seccion_cuyo_curso_declara_otra() -> None:
    """T024."""


@scenario(FEATURE, "Un export de 34 filas con niveles de 1 a 4 queda PUBLICADA entero en Industrial")
def test_un_export_de_34_filas_queda_publicada_en_industrial() -> None:
    """T035."""


@scenario(FEATURE, "La asignatura de cuatro cifras se lee también en el nombre de un export de texto")
def test_la_asignatura_de_cuatro_cifras_en_un_export_de_texto() -> None:
    """T035."""


@scenario(FEATURE, "El export que arma el generador con la programación de la sección se publica sin rechazos")
def test_el_export_del_generador_se_publica_sin_rechazos() -> None:
    """T034."""


@scenario(FEATURE, "El export de otra sección del curso se rechaza con el número de las dos")
def test_el_export_de_otra_seccion_se_rechaza() -> None:
    """T035."""


@scenario(FEATURE, "Un nombre de columna que el lector no reconoce deja la carga sin el PI 6.1")
def test_una_columna_que_el_lector_no_reconoce() -> None:
    """T035, con sus dos Ejemplos."""


@scenario(FEATURE, "La nota sobre 20 entre otras filas válidas publica solo los niveles")
def test_la_nota_sobre_20_entre_filas_validas() -> None:
    """T035."""


@scenario(FEATURE, "Un Excel con todas las notas sobre 20 queda RECHAZADA sin repetir las notas")
def test_todas_las_notas_sobre_20() -> None:
    """T035."""


@scenario(FEATURE, "Un nivel con medio punto se rechaza como no numérico")
def test_un_nivel_con_medio_punto() -> None:
    """T035."""


@scenario(FEATURE, "Un libro sin Username ni Student ID se rechaza entero")
def test_un_libro_sin_username_ni_student_id() -> None:
    """T035."""


@scenario(FEATURE, "El mismo export subido dos veces en la misma sección devuelve la constancia existente")
def test_el_mismo_export_dos_veces() -> None:
    """T035."""


@scenario(FEATURE, "Los nombres de un libro con Last Name y First Name no llegan a la base")
def test_los_nombres_no_llegan_a_la_base() -> None:
    """T035."""


@scenario(FEATURE, "El registro de la aplicación no trae códigos ni notas fuera de la huella del archivo")
def test_el_registro_no_trae_codigos_ni_notas() -> None:
    """T035."""


# Ayudas

def _nombre(numero: str, extension: str = "xlsx") -> str:
    return f"gc_SINTETICO_20261_5643_{numero}_fullgc_{FECHA}.{extension}"


def _export(ctx: Escenario, encabezado: tuple[str, ...], filas: list[tuple[object, ...]], numero: str = "701") -> Any:
    return ctx.generador.Export(f"gc_SINTETICO_20261_5643_{numero}_f", encabezado, tuple(filas))


def _codigo(numero: str, n: int) -> str:
    """Código inventado del rango 99, distinto en cada sección, como el de Escenario.export_de_quimica()."""
    return str(99100000 + int(numero) * 100 + n)


def _con_pi(ctx: Escenario, valores: list[object], columna: str = COLUMNA_6_1, numero: str = "701") -> Any:
    return _export(ctx, ("Username", columna), [(_codigo(numero, n), v) for n, v in enumerate(valores, start=1)],
                   numero)


def _xlsx(ctx: Escenario, export: Any, numero: str = "701") -> None:
    ctx.archivo = (bytes(ctx.generador.a_bytes(export)), _nombre(numero))
    ctx.extras["export"] = export


def _subir(ctx: Escenario, numero: str, contenido: bytes, nombre: str) -> Any:
    ctx.antes = ctx.conteos()
    ctx.respuesta = A.subir(ctx.sesion(ctx.profesor), ctx.seccion_de(numero), contenido, nombre)
    cuerpo = ctx.respuesta.json()
    ctx.carga_id = cuerpo.get("carga_id") if isinstance(cuerpo, dict) else None
    return ctx.respuesta


def _constancia(ctx: Escenario) -> dict[str, Any]:
    assert ctx.carga_id is not None, ctx.respuesta.text
    respuesta = ctx.sesion(ctx.profesor).get(f"/api/cargas/{ctx.carga_id}")
    assert respuesta.status_code == 200, respuesta.text
    ctx.extras["constancia"] = respuesta
    return respuesta.json()


def _claves(objeto: Any) -> set[str]:
    """Todas las claves de un JSON, a cualquier profundidad."""
    if isinstance(objeto, dict):
        return set(objeto) | {clave for valor in objeto.values() for clave in _claves(valor)}
    if isinstance(objeto, list):
        return {clave for valor in objeto for clave in _claves(valor)}
    return set()


def _niveles(texto: str) -> list[object]:
    """«3 de nivel 1, 5 de nivel 2, 20 de nivel 3 y 6 de nivel 4» en la lista de niveles, en ese orden."""
    return [int(nivel) for cuantos, nivel in re.findall(r"([0-9]+) de nivel ([1-4])", texto) for _ in range(int(cuantos))]


# Dado

@given(parsers.re(r'la sección (?P<numero>[0-9]+) de (?P<asignatura>[0-9]+) en (?P<periodo>[0-9]{4}-[0-9]) con el '
                  r'curso_blackboard "(?P<curso>[^"]+)"'))
def _curso_de_otra_seccion(ctx: Escenario, numero: str, asignatura: str, periodo: str, curso: str) -> None:
    # El curso es único (uq_seccion_curso_bb), así que la sección dueña del curso queda sin él antes del cambio.
    ctx.api.dueno.execute("UPDATE abet.seccion SET curso_blackboard = NULL WHERE curso_blackboard = %s", (curso,))
    cambiadas = ctx.api.dueno.execute(
        "UPDATE abet.seccion s SET curso_blackboard = %s FROM abet.asignatura a, abet.periodo pe"
        " WHERE a.asignatura_id = s.asignatura_id AND pe.periodo_id = s.periodo_id AND s.numero = %s"
        " AND a.codigo = %s AND pe.codigo = %s", (curso, numero, asignatura, periodo)).rowcount
    assert cambiadas == 1


@given(parsers.re(r'el export "(?P<nombre>gc_[^"]+\.xlsx)" con la hoja "(?P<hoja>[^"]+)"'))
def _export_nombrado(ctx: Escenario, nombre: str, hoja: str) -> None:
    ctx.extras["nombre"], ctx.extras["hoja"] = nombre, hoja


@given(parsers.re(r'las columnas "(?P<a>[^"]+)" y "(?P<b>[^"]+)"'))
def _columnas(ctx: Escenario, a: str, b: str) -> None:
    ctx.extras["encabezado"] = (a, b)


@given(parsers.re(r'(?P<n>[0-9]+) filas con (?P<niveles>[0-9]+ de nivel 1, .+ de nivel 4)'))
def _filas_con_niveles(ctx: Escenario, n: str, niveles: str) -> None:
    valores = _niveles(niveles)
    assert len(valores) == int(n)
    filas = [(_codigo("701", i), nivel) for i, nivel in enumerate(valores, start=1)]
    export = ctx.generador.Export(ctx.extras["hoja"], ctx.extras["encabezado"], tuple(filas))
    ctx.archivo = (bytes(ctx.generador.a_bytes(export)), ctx.extras["nombre"])
    ctx.extras["export"] = export


@given(parsers.re(r'un export de texto "(?P<nombre>[^"]+\.csv)" sin hoja'))
def _export_de_texto(ctx: Escenario, nombre: str) -> None:
    export = _con_pi(ctx, [3, 4, 2, 3])
    ctx.archivo = (ctx.generador.a_texto(export), nombre)


@given(parsers.re(r'el CSV inventado de la programación con el curso_blackboard "(?P<curso>[^"]+)" de la (?P<numero>[0-9]+)'))
def _programacion_inventada(ctx: Escenario, curso: str, numero: str) -> None:
    assert ctx.uno("SELECT curso_blackboard FROM abet.seccion WHERE seccion_id = %s", ctx.seccion_de(numero)) == curso
    salida = io.StringIO(newline="")
    escritor = csv.writer(salida, lineterminator="\r\n")
    escritor.writerow(("periodo", "asignatura", "seccion", "correo", "curso_blackboard"))
    escritor.writerow(("2026-1", "5643", numero, f"docente{numero}@example.invalid", curso))
    ruta = ctx.request.getfixturevalue("tmp_path") / "programacion_20261_inventada.csv"
    ruta.write_bytes(salida.getvalue().encode("utf-8"))
    ctx.extras["programacion"] = ruta


@given(parsers.re(r'el export de la (?P<numero>[0-9]+) que el generador de US-74 arma con esa programación'))
def _export_del_generador(ctx: Escenario, numero: str) -> None:
    """Corre el generador como proceso aparte sobre una tabla maestra inventada de la sección, armada en tmp_path."""
    from openpyxl import Workbook

    tmp = ctx.request.getfixturevalue("tmp_path")
    libro = Workbook()
    hoja = libro.active
    hoja.append(["AÑO", "CICLO", "CÓDIGO DEL CURSO", "CURSO", "CICLO DEL CURSO", "SO", "PI", "PROFESOR",
                 "CÓDIGO DEL ESTUDIANTE", "SECCIÓN", "CALIFICACIÓN", "ARCHIVO"])
    for n, nivel in enumerate((1, 2, 3, 4, 3, 3), start=1):
        hoja.append([2026, 1, "5643", "QUÍMICA GENERAL", 1, "6", "6.1", "Docente Inventado", _codigo(numero, n),
                     numero, nivel, "R017_inventado.xlsx"])
    libro.save(tmp / "tabla_maestra_inventada.xlsx")
    corrida = subprocess.run(
        [sys.executable, "-I", str(GENERADOR), "--maestra", str(tmp / "tabla_maestra_inventada.xlsx"),
         "--programacion", str(ctx.extras["programacion"]), "--salida", str(tmp / "exports"), "--periodo", "2026-1",
         "--asignatura", "5643", "--pi", "6.1", "--fecha", FECHA], capture_output=True, text=True, encoding="utf-8",
        check=False)
    assert corrida.returncode == 0, corrida.stdout + corrida.stderr
    [ruta] = (tmp / "exports").glob("*.xlsx")
    ctx.archivo = (ruta.read_bytes(), ruta.name)


@given(parsers.re(r'el export inventado de la sección (?P<numero>[0-9]+) de "(?P<asignatura>[0-9]+)" en '
                  r'"(?P<periodo>[0-9]{4}-[0-9])"'))
def _export_de_otra_seccion(ctx: Escenario, numero: str, asignatura: str, periodo: str) -> None:
    assert (asignatura, periodo) == ("5643", "2026-1")
    ctx.archivo = ctx.export_de_quimica(numero)


@given(parsers.re(r'el export inventado de la 701 con la columna "(?P<encabezado>[^"]+)"'))
def _con_columna(ctx: Escenario, encabezado: str) -> None:
    _xlsx(ctx, _con_pi(ctx, [3, 4, 2, 3], encabezado))


@given(parsers.re(rf'el export inventado de la 701 con "{re.escape(COLUMNA_6_1_SOBRE_20)}"'
                  r'(?: y las notas (?P<notas>[0-9]+(?:, [0-9]+)* y [0-9]+))?'))
def _sobre_20(ctx: Escenario, notas: str | None) -> None:
    ctx.extras["columna"] = COLUMNA_6_1_SOBRE_20
    if notas is not None:
        valores = [int(nota) for nota in re.findall(r"[0-9]+", notas)]
        ctx.extras["notas"] = valores
        _xlsx(ctx, _con_pi(ctx, valores, COLUMNA_6_1_SOBRE_20))


@given(parsers.re(r'(?P<n>[0-9]+) filas con notas de (?P<desde>[0-9]+) a (?P<hasta>[0-9]+) y (?P<m>[0-9]+) filas con '
                  r'nivel (?P<nivel>[1-4])'))
def _notas_y_niveles(ctx: Escenario, n: str, desde: str, hasta: str, m: str, nivel: str) -> None:
    rango = list(range(int(desde), int(hasta) + 1))
    notas = [rango[i % len(rango)] for i in range(int(n))]
    assert min(notas) == int(desde) and max(notas) == int(hasta)
    ctx.extras["notas"] = notas
    _xlsx(ctx, _con_pi(ctx, [*notas, *([int(nivel)] * int(m))], ctx.extras["columna"]))


@given(parsers.re(r'el export inventado de la 701 con una fila de nivel "(?P<nivel>[^"]+)"'))
def _medio_punto(ctx: Escenario, nivel: str) -> None:
    _xlsx(ctx, _con_pi(ctx, [3, 4, nivel, 2]))
    # La fila del libro con el medio punto, con el encabezado en la 1.
    ctx.extras["fila"] = 4


@given(parsers.re(r'un libro inventado de la 701 con las columnas "(?P<a>[^"]+)" y "(?P<b>[^"]+)"'))
def _sin_username(ctx: Escenario, a: str, b: str) -> None:
    _xlsx(ctx, _export(ctx, (a, b), [(_codigo("701", n), nivel) for n, nivel in enumerate((3, 4, 2), start=1)]))


@given(parsers.re(r'que la 701 ya tiene publicada la carga del export inventado de la 701'))
def _ya_publicada(ctx: Escenario) -> None:
    contenido, nombre = ctx.export_de_quimica("701")
    respuesta = _subir(ctx, "701", contenido, nombre)
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "PUBLICADA", respuesta.text
    ctx.carga_previa = ctx.carga_id
    ctx.archivo = (contenido, nombre)


@given(parsers.re(r'el export inventado de la 701 con las columnas "Last Name" y "First Name" y el apellido '
                  r'"(?P<apellido>[^"]+)"'))
def _con_nombres(ctx: Escenario, apellido: str) -> None:
    filas = [(apellido if n == 1 else f"Inventado {n:02d}", "Estudiante", _codigo("701", n), nivel)
             for n, nivel in enumerate((3, 4, 2, 3), start=1)]
    _xlsx(ctx, _export(ctx, ("Last Name", "First Name", "Username", COLUMNA_6_1), filas))
    ctx.extras["apellido"] = apellido


# Cuando

@when(parsers.re(r'el profesor (?:sube el export|lo sube) en la sección (?P<numero>[0-9]+)'))
def _sube(ctx: Escenario, numero: str) -> None:
    assert ctx.archivo is not None, "el escenario no armó ningún archivo antes de subirlo"
    caplog = ctx.request.getfixturevalue("caplog")
    caplog.set_level(logging.DEBUG)
    caplog.clear()
    _subir(ctx, numero, *ctx.archivo)


@when("el profesor sube otra vez el mismo archivo con otro nombre")
def _sube_otra_vez(ctx: Escenario) -> None:
    contenido, nombre = ctx.archivo
    otro = nombre.replace(FECHA, "2026-07-16-00-00-00")
    assert otro != nombre
    _subir(ctx, "701", contenido, otro)


# Entonces

@then(parsers.re(r'devuelve 1 fila que nombra la sección (?P<numero>[0-9]+) de (?P<asignatura>[0-9]+) en '
                 r'(?P<periodo>[0-9]{4}-[0-9])'))
def _q21_una_fila(ctx: Escenario, numero: str, asignatura: str, periodo: str) -> None:
    filas = ctx.extras["control"]
    assert [tuple(fila[1:]) for fila in filas] == [(numero, asignatura, periodo)]
    assert "@" not in repr(filas)


@then(parsers.re(r'la carga queda PUBLICADA con (?P<aceptadas>[0-9]+) de (?P<leidas>[0-9]+) filas aceptadas'))
def _publicada_con(ctx: Escenario, aceptadas: str, leidas: str) -> None:
    assert ctx.respuesta.status_code == 201, ctx.respuesta.text
    cuerpo = ctx.respuesta.json()
    assert cuerpo["estado"] == "PUBLICADA"
    assert (cuerpo["filas_aceptadas"], cuerpo["filas_leidas"]) == (int(aceptadas), int(leidas))


@then(parsers.re(r'abet\.carga\.carrera_id es el de "(?P<carrera>[A-Z]+)" y su conjunto de reglas es '
                 r'(?P<conjunto>[A-Z0-9-]+) de "(?P<de>[A-Z]+)"'))
def _carrera_y_reglas(ctx: Escenario, carrera: str, conjunto: str, de: str) -> None:
    fila = ctx.filas("SELECT c.codigo, cr.version, rc.codigo FROM abet.carga cg"
                     " JOIN abet.carrera c ON c.carrera_id = cg.carrera_id"
                     " JOIN abet.conjunto_reglas cr ON cr.conjunto_reglas_id = cg.conjunto_reglas_id"
                     " JOIN abet.carrera rc ON rc.carrera_id = cr.carrera_id WHERE cg.carga_id = %s", ctx.carga_id)
    assert fila == [(carrera, conjunto, de)]


@then(parsers.re(r'abet\.medicion gana (?P<n>[0-9]+) filas del PI (?P<pi>[0-9.]+) de (?P<catalogo>[A-Z]+-[0-9]+)'))
def _mediciones(ctx: Escenario, n: str, pi: str, catalogo: str) -> None:
    assert ctx.api.conteos()["medicion"] - ctx.antes["medicion"] == int(n)
    por_pi = ctx.filas("SELECT p.codigo, cv.codigo, count(*) FROM abet.medicion m JOIN abet.pi p USING (pi_id)"
                       " JOIN abet.catalogo_version cv ON cv.catalogo_version_id = p.catalogo_version_id"
                       " WHERE m.carga_id = %s GROUP BY 1, 2", ctx.carga_id)
    assert por_pi == [(pi, catalogo, int(n))]
    # Los niveles de la base son los del archivo, fila por fila.
    leidos = ctx.filas("SELECT e.codigo, m.nivel_original FROM abet.medicion m JOIN abet.estudiante e USING"
                       " (estudiante_id) WHERE m.carga_id = %s ORDER BY m.fila_origen", ctx.carga_id)
    assert leidos == [(str(codigo), nivel) for codigo, nivel in ctx.extras["export"].filas]


@then(parsers.re(r'la carga queda PUBLICADA(?P<sin> sin el aviso (?P<aviso>[A-Z_]+))?'))
def _publicada(ctx: Escenario, sin: str | None, aviso: str | None) -> None:
    assert ctx.respuesta.status_code == 201, ctx.respuesta.text
    cuerpo = ctx.respuesta.json()
    assert cuerpo["estado"] == "PUBLICADA"
    if aviso is not None:
        assert aviso not in [elemento["motivo"] for elemento in cuerpo["avisos"]]
        assert cuerpo["hoja"] is None


@then(parsers.re(r'la carga queda PUBLICADA con (?P<rechazadas>[0-9]+) filas rechazadas y sin avisos'))
def _publicada_sin_rechazos(ctx: Escenario, rechazadas: str) -> None:
    assert ctx.respuesta.status_code == 201, ctx.respuesta.text
    cuerpo = ctx.respuesta.json()
    assert (cuerpo["estado"], cuerpo["filas_rechazadas"], cuerpo["rechazos"], cuerpo["avisos"]) == (
        "PUBLICADA", int(rechazadas), [], [])
    assert cuerpo["filas_aceptadas"] == cuerpo["filas_leidas"] == 6


@then(parsers.re(r'la carga queda RECHAZADA con (?P<motivo>[A-Z_]+) y (?P<leidas>[0-9]+) filas leídas'))
def _rechazada_con_leidas(ctx: Escenario, motivo: str, leidas: str) -> None:
    cuerpo = ctx.respuesta.json()
    assert cuerpo["estado"] == "RECHAZADA", ctx.respuesta.text
    assert cuerpo["filas_leidas"] == int(leidas)
    assert motivo in [rechazo["motivo"] for rechazo in cuerpo["rechazos"]]


@then(parsers.re(r'el mensaje es «(?P<mensaje>[^»]+)»'))
def _mensaje(ctx: Escenario, mensaje: str) -> None:
    assert ctx.respuesta.json()["mensaje"] == mensaje


@then(parsers.re(r'la carga queda RECHAZADA con (?P<motivo>[A-Z_]+)(?: y el PI (?P<pi>[0-9.]+))?'))
def _rechazada_con(ctx: Escenario, motivo: str, pi: str | None) -> None:
    cuerpo = ctx.respuesta.json()
    assert cuerpo["estado"] == "RECHAZADA", ctx.respuesta.text
    rechazos = [(rechazo["motivo"], rechazo["pi"]) for rechazo in cuerpo["rechazos"]]
    assert (motivo, pi) in rechazos if pi is not None else motivo in [m for m, _ in rechazos]
    assert ctx.cuenta("medicion", "carga_id = %s", ctx.carga_id) == 0


@then(parsers.re(r'la carga queda RECHAZADA con «(?P<mensaje>[^»]+)»'))
def _rechazada_con_mensaje(ctx: Escenario, mensaje: str) -> None:
    cuerpo = ctx.respuesta.json()
    assert (cuerpo["estado"], cuerpo["mensaje"]) == ("RECHAZADA", mensaje), ctx.respuesta.text


@then(parsers.re(r'la constancia trae (?P<n>[0-9]+) rechazos (?P<motivo>[A-Z_]+) y el aviso (?P<aviso>[A-Z_]+)'
                 r'(?: del PI (?P<pi>[0-9.]+))?'))
def _constancia_trae(ctx: Escenario, n: str, motivo: str, aviso: str, pi: str | None) -> None:
    constancia = _constancia(ctx)
    assert [rechazo["motivo"] for rechazo in constancia["rechazos"]] == [motivo] * int(n)
    assert [(elemento["motivo"], elemento["pi"]) for elemento in constancia["avisos"]] == [(aviso, pi or "6.1")]


@then("ningún rechazo trae el valor de la celda")
def _sin_valores(ctx: Escenario) -> None:
    rechazos = _constancia(ctx)["rechazos"]
    assert not _claves(rechazos) & {"valor", "valor_leido"}
    # La fila del libro sí va en cada rechazo, en su campo y en «Fila N» del mensaje, así que la búsqueda de notas mira
    # los textos sin los números de fila.
    textos = re.sub(r"Fila [0-9]+", "Fila", json.dumps(
        [{clave: valor for clave, valor in r.items() if clave != "fila"} for r in rechazos], ensure_ascii=False))
    assert not [nota for nota in set(ctx.extras["notas"]) if re.search(rf"(?<![0-9.]){nota}(?![0-9])", textos)]


@then(parsers.re(r'ni la respuesta de la ruta 5 ni la constancia de la ruta 6 traen un campo valor ni valor_leido'))
def _sin_campo_valor(ctx: Escenario) -> None:
    assert not (_claves(ctx.respuesta.json()) | _claves(_constancia(ctx))) & {"valor", "valor_leido"}


@then(parsers.re(r'esa fila queda rechazada con (?P<motivo>[A-Z_]+)'))
def _fila_rechazada(ctx: Escenario, motivo: str) -> None:
    rechazos = [(r["fila"], r["motivo"]) for r in ctx.respuesta.json()["rechazos"]]
    assert rechazos == [(ctx.extras["fila"], motivo)]


@then(parsers.re(r'recibe 200 con la constancia de la carga existente'))
def _constancia_existente(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    assert ctx.respuesta.json()["carga_id"] == ctx.carga_previa
    leida = ctx.sesion(ctx.profesor).get(f"/api/cargas/{ctx.carga_previa}")
    assert leida.status_code == 200 and leida.json() == ctx.respuesta.json()


@then(parsers.re(r'ninguna tabla del esquema abet trae "(?P<texto>[^"]+)"'))
def _ninguna_tabla_trae(ctx: Escenario, texto: str) -> None:
    tablas = [fila[0] for fila in ctx.filas("SELECT table_name FROM information_schema.tables"
                                            " WHERE table_schema = 'abet' AND table_type = 'BASE TABLE'")]
    assert tablas
    con_texto = [tabla for tabla in tablas
                 if ctx.uno(f'SELECT count(*) FROM abet."{tabla}" t WHERE t::text LIKE %s', f"%{texto}%")]
    assert not con_texto, con_texto


@then(parsers.re(r'el registro de esa petición, sin contar el campo sha256, no trae ningún código de ocho cifras ni '
                 r'ninguna nota'))
def _registro_limpio(ctx: Escenario) -> None:
    caplog = ctx.request.getfixturevalue("caplog")
    texto = "\n".join(registro.getMessage() for registro in caplog.records)
    huella = ctx.huella(ctx.archivo[0])
    sin_huella = re.sub(r"\b[0-9a-f]{64}\b", "", texto.replace(huella, ""))
    assert not OCHO_CIFRAS.findall(sin_huella)
    assert not [nota for nota in ctx.extras["notas"] if re.search(rf"(?<![0-9.]){nota}(?![0-9])", sin_huella)]
    # El registro trae al menos la petición, para que un registro vacío no apruebe el escenario sin probar nada.
    assert caplog.records, "la subida no dejó ningún registro"
