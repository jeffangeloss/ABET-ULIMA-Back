"""Pasos de declaracion.feature que cubren las rutas 14 a 16 (spec 005, T032, BR-MEJORA-04 a BR-MEJORA-10).

El .feature manda. Ningún paso cambia un texto para que el escenario pase, y cada «Entonces» se comprueba contra la
respuesta de la API o contra la base, sin dobles del sistema bajo prueba. Este módulo enlaza con @scenario los
escenarios del Back de declaracion.feature, los de las rutas 14 a 16 y V1_15, los del R-17 con el análisis (US-49,
T033 y T037), los de la herencia de US-54 (T036) y, desde T038, los de la base sola («Las tablas de V1_15…» y «La base
rechaza…») y los de Q16 y Q17. Quedan fuera solo los @delegado_a_vitest, que prueba el Front. «con su análisis
declarado» es el paso compartido de conftest.py, que llama a declarar() de tests/cargas_de_prueba.py con los registros
de prueba de la sección (T037, FR-017). Los escenarios de Q16 y Q17 corren los cuerpos de db/pruebas/pruebas.sql sobre
las cargas del escenario, y la corrida completa del archivo la hace db/pruebas/correr_pruebas.sh.

Los registros de prueba son los del encabezado del .feature, inventados y sin datos de estudiantes. Las subidas van por
la API, así que los carga_id salen de sus respuestas y nunca se suponen.
"""

from __future__ import annotations

import io
import os
import re
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import psycopg
from psycopg.conninfo import make_conninfo
from openpyxl import load_workbook
from pytest_bdd import given, parsers, scenario, then, when

from abet_carga import r17

Escenario = Any
FEATURE = "specs/005-oportunidades-de-mejora/aceptacion/declaracion.feature"
PIS = ("5.1", "5.2", "5.3")
OM, BP = "OPORTUNIDAD_MEJORA", "BUENA_PRACTICA"
ASIGNADAS = {("docente410@example.invalid", "410"), ("docente411@example.invalid", "411"),
             ("docente.varias@example.invalid", "412")}
# Los registros de prueba del encabezado del .feature, en tests/cargas_de_prueba.py desde T037.
REGISTROS = sys.modules["cargas_de_prueba"].REGISTROS_DE_PRUEBA
CAMINOS = {"/api/cargas/{carga_id}/mejora/borrador": "PUT", "/api/cargas/{carga_id}/mejora/declaracion": "POST"}
TABLAS_V1_15 = ("mejora_borrador", "mejora_borrador_pi", "mejora_declaracion", "mejora_declaracion_pi")
RAIZ = Path(__file__).resolve().parents[3]
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# La corrección de la 410 del encabezado del .feature, que cambia solo 5.1.
CORRECCION_410 = ("La entrega coincidió con la semana de parciales y de feriado.",
                  "Mover la entrega a la semana 10 y revisar el avance en tutoría.")
COPIA_PARA_REEMPLAZAR = 'una copia de "sintetico_20262_450002_410.xlsx" con la columna 5.3 vacía en la fila 9'


# US-47

@scenario(FEATURE, "El profesor registra y declara los tres PI de la 412, con dos buenas prácticas y una oportunidad "
                   "de mejora")
def test_registra_y_declara_la_412() -> None:
    """US-47, con sus tres Ejemplos."""


@scenario(FEATURE, "Una carga sin texto responde con la declaración y el borrador nulos")
def test_una_carga_sin_texto() -> None:
    """US-47."""


@scenario(FEATURE, "Declarar con un registro incompleto no crea ninguna declaración")
def test_declaracion_incompleta() -> None:
    """US-47, con sus cuatro Ejemplos."""


@scenario(FEATURE, "Declarar la versión 0 sin ningún borrador no crea ninguna declaración")
def test_version_0_sin_borrador() -> None:
    """US-47."""


@scenario(FEATURE, "Un PI sin calificaciones no exige registro y no lo admite")
def test_pi_sin_calificaciones() -> None:
    """US-47, D-40."""


@scenario(FEATURE, "Un PI que la carga no mide se rechaza en la ruta y en la base")
def test_pi_ajeno() -> None:
    """US-47."""


@scenario(FEATURE, "El tipo de registro lo fija el semáforo, en la ruta y en la base")
def test_tipo_del_semaforo() -> None:
    """US-47, D-39."""


@scenario(FEATURE, "Un texto demasiado largo o con caracteres de control se rechaza y nada cambia")
def test_texto_invalido() -> None:
    """US-47, J-39, con sus dos Ejemplos."""


@scenario(FEATURE, "Una causa de 800 puntos de código se acepta")
def test_800_puntos_de_codigo() -> None:
    """US-47, J-39."""


@scenario(FEATURE, "El profesor no fija responsable, plazo ni estado")
def test_sin_responsable_plazo_ni_estado() -> None:
    """US-47, D-42, con sus tres Ejemplos."""


@scenario(FEATURE, "Un PI repetido en el cuerpo se rechaza")
def test_pi_repetido() -> None:
    """US-47."""


@scenario(FEATURE, "Solo el profesor asignado escribe, aunque el cuerpo no sea JSON")
def test_solo_el_profesor_asignado() -> None:
    """US-47, BR-MEJORA-05, con sus cuatro Ejemplos."""


@scenario(FEATURE, "Una carga que no está publicada responde 409 al guardar y al declarar")
def test_carga_no_publicada() -> None:
    """US-47, AD-27, con sus cuatro Ejemplos."""


@scenario(FEATURE, "Una regla sin definir detiene la declaración")
def test_regla_sin_definir() -> None:
    """US-47."""


@scenario(FEATURE, "El coordinador lee la declaración sin editarla ni ver el borrador")
def test_coordinador_lee() -> None:
    """US-47, J-33."""


@scenario(FEATURE, "Corregir una declaración deja la anterior guardada y vigente hasta declarar la nueva")
def test_corregir_una_declaracion() -> None:
    """US-47, D-37, con el R-17 de US-49 y US-50 (T033)."""


# US-49

@scenario(FEATURE, "Sin declaración el R-17 no se entrega")
def test_sin_declaracion_no_hay_r17() -> None:
    """US-49, con sus dos Ejemplos."""


@scenario(FEATURE, "Con la declaración el R-17 se entrega")
def test_con_declaracion_hay_r17() -> None:
    """US-49."""


@scenario(FEATURE, "El coordinador recibe el mismo 409 sin declaración y el archivo con ella")
def test_coordinador_y_r17() -> None:
    """US-49, J-33, con sus dos Ejemplos."""


@scenario(FEATURE, "Una sección con todos sus PI en la meta también registra sus buenas prácticas")
def test_todos_en_la_meta_declaran_bp() -> None:
    """US-49, D-36."""


@scenario(FEATURE, "El 409 de una carga rechazada manda sobre el de la declaración")
def test_rechazada_manda() -> None:
    """US-49."""


@scenario(FEATURE, "El comando r17 de una carga sin declaración termina sin escribir ningún archivo")
def test_comando_sin_declaracion() -> None:
    """US-49."""


# US-48

@scenario(FEATURE, "Un borrador parcial se acepta")
def test_borrador_parcial() -> None:
    """US-48."""


@scenario(FEATURE, "Dos pestañas no se pisan el borrador")
def test_dos_pestanas() -> None:
    """US-48, AD-19."""


# US-53

@scenario(FEATURE, "Un código o un correo de estudiante se rechaza y no se guarda ni como borrador")
def test_codigo_o_correo() -> None:
    """US-53, con sus dos Ejemplos."""


@scenario(FEATURE, "Un número de 9 dígitos o una fecha no son un código de estudiante")
def test_falsos_positivos() -> None:
    """US-53, con sus dos Ejemplos."""


@scenario(FEATURE, "Las rutas 13 a 16 no se guardan en caché y no traen datos de estudiantes")
def test_sin_cache() -> None:
    """US-53."""


# US-54 (T036)

@scenario(FEATURE, "La carga nueva hereda el análisis declarado con el tipo de sus cifras")
def test_hereda_lo_declarado() -> None:
    """US-54, AD-17."""


@scenario(FEATURE, "Un PI que queda sin calificaciones en la carga nueva no se hereda")
def test_sin_calificaciones_no_se_hereda() -> None:
    """US-54."""


@scenario(FEATURE, "Sin texto declarado se hereda lo que haya, o nada")
def test_hereda_lo_que_haya() -> None:
    """US-54, con sus dos Ejemplos."""


@scenario(FEATURE, "Subir el mismo archivo no cambia nada")
def test_mismo_archivo() -> None:
    """US-54."""


@scenario(FEATURE, "Un reemplazo hecho por coordinación hereda igual y coordinación no ve el texto heredado")
def test_reemplazo_de_coordinacion() -> None:
    """US-54, BR-MEJORA-05."""


@scenario(FEATURE, "Un PUT a la carga reemplazada responde 409 con la carga nueva")
def test_put_a_la_reemplazada() -> None:
    """US-54, AD-27."""


@scenario(FEATURE, "Las tablas de V1_15 no tienen estado, responsable ni plazo, y abet_app no corrige una declaración")
def test_tablas_sin_estado_y_permisos() -> None:
    """US-47, BR-MEJORA-07 y BR-MEJORA-12."""


@scenario(FEATURE, "La base rechaza un código en el borrador aunque la API se salte la validación")
def test_base_rechaza_codigo_en_el_borrador() -> None:
    """US-53, BR-MEJORA-10."""


@scenario(FEATURE, "La base rechaza un correo en la declaración")
def test_base_rechaza_correo_en_la_declaracion() -> None:
    """US-53, BR-MEJORA-10."""


@scenario(FEATURE, "Q16 y Q17 dan 0 filas con declaraciones sanas")
def test_q16_y_q17_en_cero() -> None:
    """US-53, BR-MEJORA-11."""


@scenario(FEATURE, "Q17 ve un PI con calificados sin su registro en la declaración vigente")
def test_q17_ve_el_pi_que_falta() -> None:
    """US-53, BR-MEJORA-11."""


@scenario(FEATURE, "Neon corre los mismos controles")
def test_neon_corre_los_mismos_controles() -> None:
    """US-53, BR-MEJORA-11."""


# Ayudas

def _cargas() -> Any:
    """tests/cargas_de_prueba.py, el mismo módulo que carga el conftest del arnés."""
    return sys.modules["cargas_de_prueba"]


def _seccion_de_la_carga(ctx: Escenario) -> str:
    return str(ctx.uno("SELECT s.numero FROM abet.carga c JOIN abet.seccion s USING (seccion_id) WHERE c.carga_id = %s",
                       ctx.carga_id))


def _tipos(ctx: Escenario, correo: str) -> dict[str, str | None]:
    """tipo_registro de cada PI de la carga, de la ruta 13, que el paso copia como hace P4."""
    respuesta = ctx.sesion(correo).get(f"/api/cargas/{ctx.carga_id}/indicadores")
    assert respuesta.status_code == 200, respuesta.text
    return {i["pi"]: i["tipo_registro"] for i in respuesta.json()["indicadores"]}


def _de_prueba(ctx: Escenario, correo: str, seccion: str, pis: tuple[str, ...] = PIS) -> list[dict[str, Any]]:
    tipos = _tipos(ctx, correo)
    return [{"pi": pi, "tipo": tipos[pi], "causa": REGISTROS[seccion][pi][0], "accion": REGISTROS[seccion][pi][1]}
            for pi in pis]


def _put(ctx: Escenario, correo: str, indicadores: list[dict[str, Any]], version: int,
         carga_id: int | None = None) -> Any:
    ctx.respuesta = ctx.sesion(correo).put(f"/api/cargas/{carga_id or ctx.carga_id}/mejora/borrador",
                                           json={"version": version, "indicadores": indicadores})
    return ctx.respuesta


def _post(ctx: Escenario, correo: str, version: int) -> Any:
    ctx.respuesta = ctx.sesion(correo).post(f"/api/cargas/{ctx.carga_id}/mejora/declaracion", json={"version": version})
    return ctx.respuesta


def _mejora(ctx: Escenario, correo: str | None = None) -> dict[str, Any]:
    respuesta = ctx.sesion(correo or ctx.profesor).get(f"/api/cargas/{ctx.carga_id}/mejora")
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def _quien(ctx: Escenario, quien: str | None) -> str:
    return quien.strip('"') if quien else ctx.profesor


def _guardar_de_prueba(ctx: Escenario, correo: str, version: int) -> None:
    seccion = _seccion_de_la_carga(ctx)
    respuesta = _put(ctx, correo, _de_prueba(ctx, correo, seccion), version)
    assert respuesta.status_code == 200 and respuesta.json()["version"] == version + 1, respuesta.text


# Antecedentes propios de este archivo

@given('acceso.docente_seccion asigna la sección 410 de "450002" a "docente410@example.invalid", la 411 de "450002" a '
       '"docente411@example.invalid" y la 412 de "450002" a "docente.varias@example.invalid"')
def _asignaciones(ctx: Escenario) -> None:
    filas = set(ctx.filas("SELECT u.correo, s.numero FROM acceso.docente_seccion d"
                          " JOIN acceso.usuario_autorizado u USING (usuario_id) JOIN abet.seccion s USING (seccion_id)"
                          " JOIN abet.asignatura a USING (asignatura_id) WHERE a.codigo = '450002'"))
    assert ASIGNADAS <= filas, filas
    for _, numero in ASIGNADAS:
        assert ctx.uno("SELECT count(*) FROM acceso.docente_seccion WHERE seccion_id = %s",
                       ctx.seccion_id(numero)) == 1, numero


@given("ninguna sección de 2026-2 tiene cargas")
def _sin_cargas(ctx: Escenario) -> None:
    assert ctx.uno("SELECT count(*) FROM abet.carga c JOIN abet.seccion s USING (seccion_id)"
                   " JOIN abet.periodo p USING (periodo_id) WHERE p.codigo = '2026-2'") == 0


# Dado

@given(parsers.re(r'que "(?P<correo>[^"]+)" guardó en la versión 1 los registros de prueba de la '
                  r'(?P<seccion>410|412)(?:, salvo (?P<falta>.+))?'))
def _guardo_salvo(ctx: Escenario, correo: str, seccion: str, falta: str | None) -> None:
    registros = _de_prueba(ctx, correo, seccion)
    if falta is not None:
        quitar = re.fullmatch(r'(?P<campo>la acción|la causa) de (?P<pi>[0-9.]+), que queda (?:nula|en "(?P<v>[^"]*)")'
                              r'|el registro entero de (?P<entero>[0-9.]+)', falta)
        assert quitar is not None, falta
        if quitar["entero"]:
            registros = [r for r in registros if r["pi"] != quitar["entero"]]
        else:
            [registro] = [r for r in registros if r["pi"] == quitar["pi"]]
            registro["accion" if quitar["campo"] == "la acción" else "causa"] = quitar["v"]
    assert _put(ctx, correo, registros, 0).status_code == 200, ctx.respuesta.text
    ctx.antes = ctx.conteos()


@given(parsers.re(r'que "(?P<correo>[^"]+)" guardó el borrador hasta la versión (?P<n>[0-9]+)'))
def _guardo_hasta(ctx: Escenario, correo: str, n: str) -> None:
    for version in range(int(n)):
        _guardar_de_prueba(ctx, correo, version)
    ctx.extras["guardado"] = _mejora(ctx, correo)["borrador"]


@given(parsers.re(r'que "(?P<correo>[^"]+)" guardó un borrador posterior en la versión (?P<n>[0-9]+)'))
def _borrador_posterior(ctx: Escenario, correo: str, n: str) -> None:
    registros = _de_prueba(ctx, correo, _seccion_de_la_carga(ctx))
    registros[0]["causa"] = "Texto del borrador posterior, sin declarar."
    assert _put(ctx, correo, registros, int(n) - 1).json()["version"] == int(n), ctx.respuesta.text


@given(parsers.re(r'que una copia de "(?P<nombre>[^"]+)" sin la columna del PI (?P<pi>[0-9.]+) está subida a la '
                  r'sección (?P<numero>[0-9]+) y su carga está "RECHAZADA"'))
def _rechazada(ctx: Escenario, nombre: str, pi: str, numero: str) -> None:
    contenido, archivo = ctx.copia_de(f'una copia de "{nombre}" sin la columna del PI {pi}')
    respuesta = ctx.subir(ctx.profesor, contenido, archivo, numero)
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "RECHAZADA", respuesta.text
    ctx.extras["reemplazada_por"] = None
    ctx.antes = ctx.conteos()


@given(parsers.re(r'que la carga A REEMPLAZADA y la carga B PUBLICADA que la reemplaza en la sección '
                  r'(?P<numero>[0-9]+)(?:, y se escribe en A)?'))
def _a_reemplazada_por_b(ctx: Escenario, numero: str) -> None:
    nombre = "sintetico_20262_450002_410.xlsx"
    primera = ctx.subir(ctx.profesor, ctx.de_inventados(nombre), nombre, numero)
    assert primera.status_code == 201 and primera.json()["estado"] == "PUBLICADA", primera.text
    anterior = primera.json()["carga_id"]
    contenido, archivo = ctx.copia_de(COPIA_PARA_REEMPLAZAR)
    segunda = ctx.subir(ctx.profesor, contenido, archivo, numero, params={"reemplaza": str(anterior)})
    assert segunda.status_code == 201 and segunda.json()["estado"] == "PUBLICADA", segunda.text
    assert ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", anterior) == "REEMPLAZADA"
    ctx.extras["cargas"] = {"A": anterior, "B": segunda.json()["carga_id"]}
    ctx.extras["reemplazada_por"] = segunda.json()["carga_id"]
    ctx.carga_id = anterior
    ctx.antes = ctx.conteos()


@given(parsers.re(r'que la base tiene un conjunto de reglas de prueba de Ambiental con (?P<parametro>NIVEL_ESPERADO|'
                  r'META_LOGRO) sin DEFINIR, y la API configurada con ese CONJUNTO_REGLAS'))
def _conjunto_sin_un_parametro(ctx: Escenario, parametro: str) -> None:
    version = f"R-PRUEBA-SIN-{parametro.replace('_', '-')}"
    valores = {"meta_logro": 0.80, "nivel_esperado": 3, "corte_rojo": 0.75, parametro.lower(): None}
    _cargas().conjunto_aprobado(ctx.api.dueno, version, **valores)
    ctx.reiniciar_api(carga=replace(ctx.api.ajustes.carga, conjunto_reglas=version))


# Dado, US-49

@given(parsers.re(r'que la carga (?P<situacion>no tiene ningún texto|tiene solo un borrador con los tres registros)'))
def _situacion(ctx: Escenario, situacion: str) -> None:
    if situacion.startswith("tiene solo"):
        _guardar_de_prueba(ctx, ctx.profesor, 0)
        assert ctx.cuenta("mejora_borrador_pi", "carga_id = %s AND causa IS NOT NULL", ctx.carga_id) == 3
    assert ctx.cuenta("mejora_declaracion", "carga_id = %s", ctx.carga_id) == 0


@given(parsers.re(r'que la base tiene el conjunto "(?P<version>R-PRUEBA-APROBADO)" de Ambiental en estado "APROBADO" con '
                  r'META_LOGRO 0,70, NIVEL_ESPERADO 2, CORTE_ROJO 0,50, TRATO_SIN_EVIDENCIA "SE_EXCLUYE_DEL_DENOMINADOR" y '
                  r'la conversión de sus 4 niveles, como en el caso A03 de pruebas\.sql'))
def _conjunto_a03(ctx: Escenario, version: str) -> None:
    _cargas().conjunto_aprobado(ctx.api.dueno, version)
    assert ctx.filas("SELECT estado FROM abet.conjunto_reglas WHERE version = %s", version) == [("APROBADO",)]


@given(parsers.re(r'la API configurada con CONJUNTO_REGLAS "(?P<version>[^"]+)"'))
def _api_con_conjunto(ctx: Escenario, version: str) -> None:
    ctx.reiniciar_api(carga=replace(ctx.api.ajustes.carga, conjunto_reglas=version))
    assert ctx.api.ajustes.carga.conjunto_reglas == version


# Cuando, el R-17 y el comando

def _r17(ctx: Escenario, correo: str | None = None) -> Any:
    ctx.respuesta = ctx.sesion(correo or ctx.profesor).get(f"/api/cargas/{ctx.carga_id}/r17.xlsx")
    return ctx.respuesta


def _b29_y_b34(ctx: Escenario) -> tuple[str, str]:
    respuesta = _r17(ctx)
    assert respuesta.status_code == 200, respuesta.text
    hoja = load_workbook(io.BytesIO(respuesta.content))[r17.HOJA]
    return hoja["B29"].value, hoja["B34"].value


@when(parsers.re(r'"(?P<correo>[^"]+)" descarga el R-17 de esa carga'))
def _descarga(ctx: Escenario, correo: str) -> None:
    _r17(ctx, correo)


@when(parsers.re(r'"(?P<correo>[^"]+)" guarda el borrador con los registros de prueba de la 410 y version 0, y declara '
                 r'la versión 1'))
def _guarda_y_declara(ctx: Escenario, correo: str) -> None:
    _guardar_de_prueba(ctx, correo, 0)
    assert _post(ctx, correo, 1).status_code == 201, ctx.respuesta.text


@when(parsers.re(r'"(?P<correo>[^"]+)" guarda otro borrador con la corrección de la 410 y version (?P<version>[0-9]+)'))
def _guarda_la_correccion(ctx: Escenario, correo: str, version: str) -> None:
    ctx.extras["anterior"] = _b29_y_b34(ctx)
    registros = _de_prueba(ctx, correo, "410")
    registros[0]["causa"], registros[0]["accion"] = CORRECCION_410
    assert _put(ctx, correo, registros, int(version)).status_code == 200, ctx.respuesta.text


@when("el administrador técnico corre el comando python -m abet_carga r17 para esa carga")
def _corre_el_comando(ctx: Escenario, tmp_path: Path) -> None:
    carpeta = tmp_path / "r17_del_comando"
    entorno = {clave: valor for clave, valor in os.environ.items() if clave != "DATABASE_URL"}
    entorno["CONJUNTO_REGLAS"] = ctx.api.ajustes.carga.conjunto_reglas
    ctx.extras["carpeta"] = carpeta
    ctx.extras["comando"] = subprocess.run(
        [sys.executable, "-m", "abet_carga", "r17", "--carga", str(ctx.carga_id), "--correo",
         "coordinacion@example.invalid", "--carpeta", str(carpeta), "--base", ctx.api.base.conexion,
         "--rol", ctx.api.base.rol_app],
        cwd=RAIZ, env=entorno, capture_output=True, text=True, check=False, timeout=120)


# Cuando, la ruta 15

@when(parsers.re(r'"(?P<correo>[^"]+)" guarda el borrador con los registros de prueba de la (?P<seccion>410|412)'
                 r'(?: de (?P<pis>[0-9.]+ y [0-9.]+))? y version (?P<version>[0-9]+)'))
def _guarda_de_prueba(ctx: Escenario, correo: str, seccion: str, pis: str | None, version: str) -> None:
    elegidos = tuple(re.findall(r"[0-9]\.[0-9]+", pis)) if pis else PIS
    _put(ctx, correo, _de_prueba(ctx, correo, seccion, elegidos), int(version))


@when(parsers.re(r'"(?P<correo>[^"]+)" guarda el borrador con los registros de prueba de la 412, con (?P<pi>[0-9.]+) '
                 r'de tipo "(?P<tipo>[A-Z_]+)", y version (?P<version>[0-9]+)'))
def _guarda_con_otro_tipo(ctx: Escenario, correo: str, pi: str, tipo: str, version: str) -> None:
    registros = _de_prueba(ctx, correo, "412")
    [registro] = [r for r in registros if r["pi"] == pi]
    registro["tipo"] = tipo
    _put(ctx, correo, registros, int(version))


@when(parsers.re(r'"(?P<correo>[^"]+)" guarda el borrador con (?P<cuantos>un registro|dos registros) (?:del PI |de )'
                 r'(?P<pi>[0-9.]+) y version (?P<version>[0-9]+)'))
def _guarda_un_registro(ctx: Escenario, correo: str, cuantos: str, pi: str, version: str) -> None:
    tipo = _tipos(ctx, correo).get(pi)
    registro = {"pi": pi, "tipo": tipo or OM, "causa": "Una causa inventada.", "accion": "Una acción inventada."}
    _put(ctx, correo, [registro] * (2 if cuantos == "dos registros" else 1), int(version))


def _causa(texto: str) -> str:
    if texto == "un texto de 801 puntos de código":
        return "a" * 801
    if (control := re.fullmatch(r'"(?P<t>[^"]+)" con el carácter de control U\+(?P<cp>[0-9A-F]{4})', texto)):
        return control["t"] + chr(int(control["cp"], 16))
    assert texto.startswith('"') and texto.endswith('"'), texto
    return texto.strip('"')


@when(parsers.re(r'"(?P<correo>[^"]+)" guarda el borrador con la causa de 5\.1 (?P<causa>.+) y la acción de 5\.1 '
                 r'"(?P<accion>[^"]+)" con version (?P<version>[0-9]+)'))
def _guarda_causa_y_accion(ctx: Escenario, correo: str, causa: str, accion: str, version: str) -> None:
    registro = {"pi": "5.1", "tipo": _tipos(ctx, correo)["5.1"], "causa": _causa(causa), "accion": accion}
    _put(ctx, correo, [registro], int(version))


@when(parsers.re(r'"(?P<correo>[^"]+)" guarda el borrador con la causa de 5\.1 de (?P<n>[0-9]+) puntos de código y '
                 r'version (?P<version>[0-9]+)'))
def _guarda_causa_larga(ctx: Escenario, correo: str, n: str, version: str) -> None:
    _put(ctx, correo, [{"pi": "5.1", "tipo": _tipos(ctx, correo)["5.1"], "causa": "á" * int(n)}], int(version))


@when(parsers.re(r'"(?P<correo>[^"]+)" guarda el borrador con solo la causa de (?P<pi>[0-9.]+) «(?P<causa>[^»]+)» y '
                 r'version (?P<version>[0-9]+)'))
def _guarda_solo_la_causa(ctx: Escenario, correo: str, pi: str, causa: str, version: str) -> None:
    ctx.extras["causa"] = (pi, causa)
    _put(ctx, correo, [{"pi": pi, "tipo": _tipos(ctx, correo)[pi], "causa": causa}], int(version))


@when(parsers.re(r'"(?P<correo>[^"]+)" guarda el borrador con otro texto en 5\.1 y version (?P<version>[0-9]+)'))
def _guarda_otro_texto(ctx: Escenario, correo: str, version: str) -> None:
    registros = _de_prueba(ctx, correo, _seccion_de_la_carga(ctx))
    registros[0]["causa"] = "Otro texto escrito en la segunda pestaña."
    _put(ctx, correo, registros, int(version))


@when(parsers.re(r'"(?P<correo>[^"]+)" guarda el borrador con (?P<campo>la causa|la acción) de (?P<pi>[0-9.]+) '
                 r'"(?P<texto>[^"]+)", los demás registros de prueba de la 410 y version (?P<version>[0-9]+)'))
def _guarda_con_un_texto(ctx: Escenario, correo: str, campo: str, pi: str, texto: str, version: str) -> None:
    registros = _de_prueba(ctx, correo, "410")
    [registro] = [r for r in registros if r["pi"] == pi]
    registro["causa" if campo == "la causa" else "accion"] = texto
    _put(ctx, correo, registros, int(version))


@when(parsers.re(r'"(?P<correo>[^"]+)" guarda el borrador en la carga A con la causa de (?P<pi>[0-9.]+) '
                 r'«(?P<causa>[^»]+)» y version (?P<version>[0-9]+)'))
def _guarda_en_a(ctx: Escenario, correo: str, pi: str, causa: str, version: str) -> None:
    _put(ctx, correo, [{"pi": pi, "tipo": OM, "causa": causa}], int(version), ctx.extras["cargas"]["A"])


# Cuando, la ruta 16 y las demás peticiones

@when(parsers.re(r'(?:"(?P<quien>[^"]+)" )?declara la versión (?P<version>[0-9]+)'))
def _declara(ctx: Escenario, quien: str | None, version: str) -> None:
    _post(ctx, _quien(ctx, quien), int(version))


@when("se envía GET /api/cargas/{carga_id}/indicadores")
def _pide_indicadores(ctx: Escenario) -> None:
    ctx.pedir(f"/api/cargas/{ctx.carga_id}/indicadores")


@when("se envía GET /api/cargas/{carga_id}/mejora")
def _pide_mejora(ctx: Escenario) -> None:
    ctx.pedir(f"/api/cargas/{ctx.carga_id}/mejora")


def _enviar(ctx: Escenario, metodo: str, ruta: str, **opciones: Any) -> None:
    assert CAMINOS[ruta] == metodo, (metodo, ruta)
    correo = ctx.extras.get("con_sesion") or ctx.profesor
    ctx.respuesta = ctx.sesion(correo).request(metodo, ruta.replace("{carga_id}", str(ctx.carga_id)), **opciones)


def _valido(ctx: Escenario, metodo: str) -> dict[str, Any]:
    if metodo == "POST":
        return {"version": 1}
    version = _mejora(ctx)["borrador"]
    return {"version": version["version"] if version else 0,
            "indicadores": [{"pi": "5.1", "tipo": OM, "causa": "Una causa inventada."}]}


@when(parsers.re(r'se envía (?P<metodo>PUT|POST) (?P<ruta>\S+) con un cuerpo válido más la clave "(?P<clave>[a-z_]+)"'))
def _con_clave_ajena(ctx: Escenario, metodo: str, ruta: str, clave: str) -> None:
    _enviar(ctx, metodo, ruta, json={**_valido(ctx, metodo), clave: "Coordinación del curso"})


@when(parsers.re(r'se envía (?P<metodo>PUT|POST) (?P<ruta>\S+) con un cuerpo que no es JSON'))
def _sin_json(ctx: Escenario, metodo: str, ruta: str) -> None:
    _enviar(ctx, metodo, ruta, content=b"{esto no es JSON", headers={"content-type": "text/plain"})


@when(parsers.re(r'se envía (?P<metodo>PUT|POST) (?P<ruta>\S+) con un cuerpo JSON válido'))
def _con_json_valido(ctx: Escenario, metodo: str, ruta: str) -> None:
    cuerpo = {"version": 1} if metodo == "POST" else {
        "version": 0, "indicadores": [{"pi": "5.1", "tipo": OM, "causa": "Una causa inventada."}]}
    _enviar(ctx, metodo, ruta, json=cuerpo)


@when("una conexión directa con el rol abet_app inserta en abet.mejora_borrador_pi un registro del PI 2.1 para esa "
      "carga")
def _inserta_pi_ajeno(ctx: Escenario) -> None:
    from psycopg.conninfo import make_conninfo

    ctx.directa = ctx.pila.enter_context(psycopg.connect(
        make_conninfo(ctx.api.base.conexion, user=ctx.api.base.rol_app), autocommit=True))
    pi_id = ctx.uno("SELECT pi_id FROM abet.pi WHERE codigo = '2.1'")
    # La cabecera del borrador existe, así que la única FK que puede fallar es la de la columna.
    ctx.api.dueno.execute("INSERT INTO abet.mejora_borrador (carga_id, version, actualizado_por) VALUES (%s, 1, %s)",
                          (ctx.carga_id, ctx.usuario_id(ctx.profesor)))
    ctx.intentar("INSERT INTO abet.mejora_borrador_pi (carga_id, pi_id, causa) VALUES (%s, %s, 'Una causa inventada.')",
                 ctx.carga_id, pi_id)


@when(parsers.re(r'una conexión directa del dueño de la base inserta en abet\.mejora_declaracion_pi el PI '
                 r'(?P<pi>[0-9.]+) con tipo "(?P<tipo>[A-Z_]+)" y semaforo "(?P<semaforo>[A-Z]+)"'))
def _inserta_incoherente(ctx: Escenario, pi: str, tipo: str, semaforo: str) -> None:
    ctx.directa = ctx.api.dueno
    with ctx.api.dueno.transaction():
        declaracion = ctx.api.dueno.execute(
            "INSERT INTO abet.mejora_declaracion (carga_id, version_borrador, declarada_por) VALUES (%s, 1, %s)"
            " RETURNING declaracion_id", (ctx.carga_id, ctx.usuario_id(ctx.profesor))).fetchone()[0]
        ctx.api.dueno.execute("SAVEPOINT antes_del_pi")
        ctx.intentar("INSERT INTO abet.mejora_declaracion_pi (declaracion_id, pi_id, carga_id, tipo, causa, accion,"
                     " semaforo) SELECT %s, pi_id, %s, %s, 'Una causa inventada.', 'Una acción inventada.', %s"
                     " FROM abet.carga_columna WHERE carga_id = %s AND pi_codigo = %s",
                     declaracion, ctx.carga_id, tipo, semaforo, ctx.carga_id, pi)
        ctx.api.dueno.execute("ROLLBACK TO SAVEPOINT antes_del_pi")


@when("se envían GET /api/cargas/{carga_id}/indicadores, GET /api/cargas/{carga_id}/mejora, PUT "
      "/api/cargas/{carga_id}/mejora/borrador y POST /api/cargas/{carga_id}/mejora/declaracion con cuerpos válidos")
def _las_cuatro(ctx: Escenario) -> None:
    cliente = ctx.sesion(ctx.profesor)
    base = f"/api/cargas/{ctx.carga_id}"
    respuestas = [cliente.get(f"{base}/indicadores"), cliente.get(f"{base}/mejora")]
    respuestas.append(cliente.put(f"{base}/mejora/borrador",
                                  json={"version": 0, "indicadores": _de_prueba(ctx, ctx.profesor, "410")}))
    respuestas.append(cliente.post(f"{base}/mejora/declaracion", json={"version": 1}))
    assert [r.status_code for r in respuestas] == [200, 200, 200, 201], [r.text for r in respuestas]
    ctx.extras["respuestas"] = respuestas


# Entonces

@then(parsers.re(r'la API responde (?P<codigo>4[0-9]{2}) con el mensaje "(?P<mensaje>[^"]+)"(?: \(propuesta\))?'
                 r'(?P<resto>, sin reemplazada_por|, con reemplazada_por igual a B| y reemplazada_por igual a B'
                 r'|, los registros guardados y la versión (?P<version>[0-9]+))?'))
def _error(ctx: Escenario, codigo: str, mensaje: str, resto: str | None, version: str | None) -> None:
    respuesta = ctx.respuesta
    assert respuesta.status_code == int(codigo), respuesta.text
    assert respuesta.headers["cache-control"] == "no-store"
    cuerpo = respuesta.json()
    assert cuerpo["detail"] == mensaje
    if resto and "reemplazada_por" in resto:
        esperado = None if "sin" in resto else ctx.extras["cargas"]["B"]
        assert cuerpo.get("reemplazada_por") == esperado, cuerpo
        assert set(cuerpo) == ({"detail"} if esperado is None else {"detail", "reemplazada_por"})
    elif version is not None:
        assert cuerpo["borrador"] == ctx.extras["guardado"] and cuerpo["borrador"]["version"] == int(version)
    else:
        assert set(cuerpo) == {"detail"}, cuerpo


@then("la API responde 201 con declarada_en y tres indicadores")
def _201_con_tres(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 201, ctx.respuesta.text
    cuerpo = ctx.respuesta.json()
    assert set(cuerpo) == {"declarada_en", "indicadores"} and cuerpo["declarada_en"]
    assert [i["pi"] for i in cuerpo["indicadores"]] == list(PIS)


@then(parsers.re(r'abet\.mejora_declaracion_pi guarda el PI (?P<pi>[0-9.]+) con tipo "(?P<tipo>[A-Z_]+)", logro_pct '
                 r'(?P<logro>[0-9.]+), meta_pct (?P<meta>[0-9.]+) y semaforo "(?P<semaforo>[A-Z]+)"'))
def _fila_declarada(ctx: Escenario, pi: str, tipo: str, logro: str, meta: str, semaforo: str) -> None:
    filas = ctx.filas("SELECT d.tipo, d.logro_pct, d.meta_pct, d.semaforo FROM abet.mejora_declaracion_pi d"
                      " JOIN abet.carga_columna cc ON cc.carga_id = d.carga_id AND cc.pi_id = d.pi_id"
                      " WHERE d.carga_id = %s AND cc.pi_codigo = %s", ctx.carga_id, pi)
    assert [(t, float(lo), float(me), s) for t, lo, me, s in filas] == [(tipo, float(logro), float(meta), semaforo)]


@then(parsers.re(r'GET /api/cargas/\{carga_id\}/mejora responde 200 con el PI (?P<pi>[0-9.]+) declarado con tipo '
                 r'"(?P<tipo>[A-Z_]+)", su causa y su acción de prueba y estado "PROPUESTA"'))
def _leida_declarada(ctx: Escenario, pi: str, tipo: str) -> None:
    ctx.extras["mejora"] = cuerpo = _mejora(ctx)
    [indicador] = [i for i in cuerpo["declaracion"]["indicadores"] if i["pi"] == pi]
    causa, accion = REGISTROS[_seccion_de_la_carga(ctx)][pi]
    assert indicador == {"pi": pi, "tipo": tipo, "causa": causa, "accion": accion, "estado": "PROPUESTA"}


@then("borrador_pendiente es falso")
def _sin_pendiente(ctx: Escenario) -> None:
    assert ctx.extras["mejora"]["borrador_pendiente"] is False


@then("la API responde 200 con declaracion nulo, borrador nulo y puede_editar verdadero")
def _vacia(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    assert ctx.respuesta.headers["cache-control"] == "no-store"
    cuerpo = ctx.respuesta.json()
    assert (cuerpo["declaracion"], cuerpo["borrador"], cuerpo["puede_editar"]) == (None, None, True)


@then(parsers.re(r'la API responde 201 con dos indicadores, (?P<a>[0-9.]+) y (?P<b>[0-9.]+)'))
def _201_con_dos(ctx: Escenario, a: str, b: str) -> None:
    assert ctx.respuesta.status_code == 201, ctx.respuesta.text
    assert [i["pi"] for i in ctx.respuesta.json()["indicadores"]] == [a, b]


@then(parsers.re(r'abet\.mejora_declaracion_pi no tiene ninguna fila de (?P<pi>[0-9.]+)'))
def _sin_fila_de(ctx: Escenario, pi: str) -> None:
    assert ctx.uno("SELECT count(*) FROM abet.mejora_declaracion_pi d JOIN abet.carga_columna cc"
                   " ON cc.carga_id = d.carga_id AND cc.pi_id = d.pi_id WHERE cc.pi_codigo = %s", pi) == 0
    assert ctx.cuenta("mejora_declaracion_pi") == 2


@then("la base rechaza la inserción por la FK de abet.mejora_borrador_pi a abet.carga_columna")
def _rechaza_por_la_fk(ctx: Escenario) -> None:
    assert ctx.error_directo is not None, "la base aceptó la inserción"
    assert ctx.error_directo.diag.constraint_name == "fk_mejora_borrador_pi_columna"


@then(parsers.re(r'la API responde 200 con version (?P<version>[0-9]+)'))
def _200_con_version(ctx: Escenario, version: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    assert ctx.respuesta.json()["version"] == int(version)


@then("abet.mejora_borrador conserva la versión 1 y abet.mejora_declaracion no gana ninguna fila")
def _conserva_la_version(ctx: Escenario) -> None:
    assert ctx.uno("SELECT version FROM abet.mejora_borrador WHERE carga_id = %s", ctx.carga_id) == 1
    assert ctx.conteos()["mejora_declaracion"] == ctx.antes["mejora_declaracion"]


@then("las cuatro tablas de V1_15 no ganan ninguna fila")
def _cuatro_tablas_sin_filas(ctx: Escenario) -> None:
    ahora = ctx.conteos()
    assert {t: ahora[t] for t in TABLAS_V1_15} == {t: ctx.antes[t] for t in TABLAS_V1_15} == dict.fromkeys(TABLAS_V1_15, 0)


@then("la API responde 200 con la declaración vigente, borrador nulo y puede_editar falso")
def _coordinacion_lee(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    cuerpo = ctx.respuesta.json()
    assert cuerpo["borrador"] is None and cuerpo["puede_editar"] is False
    assert [(i["pi"], i["causa"], i["accion"], i["estado"]) for i in cuerpo["declaracion"]["indicadores"]] == [
        (pi, *REGISTROS["410"][pi], "PROPUESTA") for pi in PIS]
    assert "borrador posterior" not in ctx.respuesta.text


@then("GET /api/cargas/{carga_id}/mejora devuelve en el borrador esa causa en 5.2 y causa y accion nulas en los demás "
      "campos de 5.1, 5.2 y 5.3")
def _borrador_parcial(ctx: Escenario) -> None:
    pi, causa = ctx.extras["causa"]
    indicadores = _mejora(ctx)["borrador"]["indicadores"]
    assert [(i["pi"], i["causa"], i["accion"]) for i in indicadores] == [
        (p, causa if p == pi else None, None) for p in PIS]


@then("el borrador guardado no cambia")
def _no_cambia(ctx: Escenario) -> None:
    assert _mejora(ctx)["borrador"] == ctx.extras["guardado"]


@then("cada respuesta trae Cache-Control: no-store")
def _no_store(ctx: Escenario) -> None:
    assert {r.headers["cache-control"] for r in ctx.extras["respuestas"]} == {"no-store"}


@then('ningún cuerpo contiene los códigos "99000001" a "99000011", nombres ni correos de estudiantes')
def _sin_datos_de_estudiantes(ctx: Escenario) -> None:
    for respuesta in ctx.extras["respuestas"]:
        texto = respuesta.text
        assert not any(f"990000{n:02d}" in texto for n in range(1, 12)), respuesta.url
        assert "@" not in texto, respuesta.url
        # El export inventado de la 410 nombra a sus estudiantes «Inventado NN Estudiante», y ninguna respuesta lo repite.
        assert "Inventado" not in texto and "Estudiante" not in texto


# Entonces, US-49

@then("la respuesta no trae ningún archivo")
def _sin_archivo(ctx: Escenario) -> None:
    assert ctx.respuesta.headers["content-type"] == "application/json"
    assert "content-disposition" not in ctx.respuesta.headers
    assert not ctx.respuesta.content.startswith(b"PK")


@then(parsers.re(r'la API responde 200 con el archivo "(?P<nombre>[^"]+)"'))
def _200_con_el_archivo(ctx: Escenario, nombre: str) -> None:
    respuesta = ctx.respuesta
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.headers["content-type"] == XLSX
    assert respuesta.headers["content-disposition"] == f'attachment; filename="{nombre}"'
    assert load_workbook(io.BytesIO(respuesta.content)).sheetnames == [r17.HOJA, "Constancia"]


@then(parsers.re(r'los tres PI traen pct_sobre_calificados (?P<logro>[0-9.]+), semaforo "(?P<semaforo>[A-Z]+)" y '
                 r'tipo_registro "(?P<tipo>[A-Z_]+)"'))
def _tres_pi(ctx: Escenario, logro: str, semaforo: str, tipo: str) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    indicadores = ctx.respuesta.json()["indicadores"]
    assert [(i["pi"], i["pct_sobre_calificados"], i["semaforo"], i["tipo_registro"]) for i in indicadores] == [
        (pi, float(logro), semaforo, tipo) for pi in PIS]


@then(parsers.re(r'abet\.mejora_declaracion_pi guarda los tres PI con tipo "(?P<tipo>[A-Z_]+)"'))
def _tres_con_tipo(ctx: Escenario, tipo: str) -> None:
    filas = ctx.filas("SELECT cc.pi_codigo, d.tipo FROM abet.mejora_declaracion_pi d JOIN abet.carga_columna cc"
                      " ON cc.carga_id = d.carga_id AND cc.pi_id = d.pi_id WHERE d.carga_id = %s ORDER BY cc.pi_codigo",
                      ctx.carga_id)
    assert filas == [(pi, tipo) for pi in PIS]


@then("la descarga del R-17 de esa carga responde 200")
def _descarga_200(ctx: Escenario) -> None:
    respuesta = _r17(ctx)
    assert respuesta.status_code == 200 and respuesta.headers["content-type"] == XLSX, respuesta.text


@then("la carga no tiene ninguna declaración")
def _sin_declaracion(ctx: Escenario) -> None:
    assert ctx.cuenta("mejora_declaracion", "carga_id = %s", ctx.carga_id) == 0
    assert ctx.cuenta("mejora_declaracion_pi", "carga_id = %s", ctx.carga_id) == 0


@then(parsers.re(r'el comando termina con el mensaje "(?P<mensaje>[^"]+)"(?: \(propuesta\))?'))
def _comando_termina(ctx: Escenario, mensaje: str) -> None:
    corrida = ctx.extras["comando"]
    assert corrida.returncode == 1, corrida.stdout + corrida.stderr
    assert corrida.stdout.strip() == mensaje and corrida.stderr == ""


@then("el comando no escribe ningún archivo")
def _comando_sin_archivos(ctx: Escenario) -> None:
    carpeta = ctx.extras["carpeta"]
    assert not carpeta.exists() or list(carpeta.iterdir()) == []


# US-54, la herencia al leer (T036)

def _profesor_de_la_410(ctx: Escenario) -> str:
    return ctx.profesor or str(ctx.uno(
        "SELECT u.correo FROM acceso.docente_seccion d JOIN acceso.usuario_autorizado u USING (usuario_id)"
        " WHERE d.seccion_id = %s", ctx.seccion_id("410")))


@given(parsers.re(r'que "(?P<nombre>[^"]+)" está subido a la sección (?P<numero>[0-9]+) con respuesta 201 y su '
                  r'carga_id A(?P<texto>, con su análisis declarado|, con un borrador guardado y sin declaración)?'))
def _subida_a(ctx: Escenario, nombre: str, numero: str, texto: str | None) -> None:
    profesor = _profesor_de_la_410(ctx)
    respuesta = ctx.subir(profesor, ctx.de_inventados(nombre), nombre, numero)
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "PUBLICADA", respuesta.text
    ctx.extras["cargas"] = {"A": ctx.carga_id}
    if texto == ", con su análisis declarado":
        _cargas().declarar(ctx.api.dueno, ctx.carga_id, REGISTROS["410"], correo=profesor)
    elif texto:
        _guardar_de_prueba(ctx, profesor, 0)
        assert ctx.cuenta("mejora_declaracion", "carga_id = %s", ctx.carga_id) == 0
    ctx.antes = ctx.conteos()


def _reemplazar_a(ctx: Escenario, correo: str, que: str, numero: str = "410") -> None:
    if que.startswith("una copia"):
        contenido, nombre = ctx.copia_de(que)
    else:
        nombre = que.removeprefix("el archivo ").strip('"')
        contenido = ctx.de_inventados(nombre)
    anterior = ctx.extras["cargas"]["A"]
    ctx.subir(correo, contenido, nombre, numero, params={"reemplaza": str(anterior)})
    if ctx.respuesta.status_code == 201:
        ctx.extras["cargas"]["B"] = ctx.carga_id
        assert ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", anterior) == "REEMPLAZADA"
    else:
        ctx.carga_id = anterior


@when(parsers.re(r'se envía POST /api/secciones/\{sección (?P<numero>[0-9]+)\}/cargas\?reemplaza=\{A\} con '
                 r'(?P<que>una copia de "[^"]+" .+|el archivo "[^"]+")'))
def _reemplaza(ctx: Escenario, numero: str, que: str) -> None:
    _reemplazar_a(ctx, _profesor_de_la_410(ctx), que, numero)


@when(parsers.re(r'"(?P<correo>[^"]+)" reemplaza A con (?P<que>una copia de "[^"]+" .+)'))
def _reemplaza_quien(ctx: Escenario, correo: str, que: str) -> None:
    _reemplazar_a(ctx, correo, que)
    assert ctx.respuesta.status_code == 201, ctx.respuesta.text


@when("se envía GET /api/cargas/{B}/mejora")
def _pide_mejora_de_b(ctx: Escenario) -> None:
    ctx.pedir(f"/api/cargas/{ctx.extras['cargas']['B']}/mejora")


def _heredada(ctx: Escenario) -> dict[str, Any]:
    respuesta = ctx.respuesta
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.headers["cache-control"] == "no-store"
    return respuesta.json()


def _textos_de_a(borrador: dict[str, Any]) -> list[tuple[str, str | None, str | None]]:
    return [(i["pi"], i["causa"], i["accion"]) for i in borrador["indicadores"]]


@then(parsers.re(r'la API responde 200 con borrador con los registros (?:declarados de A en (?P<tres>5\.1, 5\.2 y 5\.3), '
                 r'version 0|de A solo en (?P<dos>5\.1 y 5\.2)) y heredado_de igual a A'))
def _hereda(ctx: Escenario, tres: str | None, dos: str | None) -> None:
    cuerpo = _heredada(ctx)
    pis = re.findall(r"[0-9]\.[0-9]+", tres or dos)
    assert cuerpo["heredado_de"] == ctx.extras["cargas"]["A"]
    assert cuerpo["declaracion"] is None and cuerpo["borrador_pendiente"] is False and cuerpo["puede_editar"] is True
    assert cuerpo["borrador"]["version"] == 0
    assert _textos_de_a(cuerpo["borrador"]) == [(pi, *REGISTROS["410"][pi]) for pi in pis]
    ctx.extras["heredado"] = cuerpo["borrador"]


@then('5.1 y 5.2 traen tipo "OPORTUNIDAD_MEJORA", y 5.3 trae tipo "BUENA_PRACTICA" con su causa y su acción de A')
def _tipos_nuevos(ctx: Escenario) -> None:
    indicadores = ctx.extras["heredado"]["indicadores"]
    assert [(i["pi"], i["tipo"]) for i in indicadores] == [("5.1", OM), ("5.2", OM), ("5.3", BP)]
    # El tipo es el de la ruta 13 de la carga nueva, y A tenía los tres PI como OM.
    ctx.carga_id = ctx.extras["cargas"]["B"]
    assert {pi: tipo for pi, tipo in _tipos(ctx, ctx.profesor).items()} == {"5.1": OM, "5.2": OM, "5.3": BP}
    assert ctx.filas("SELECT DISTINCT tipo FROM abet.mejora_declaracion_pi WHERE carga_id = %s",
                     ctx.extras["cargas"]["A"]) == [(OM,)]


@then("el R-17 de la carga B responde 409 hasta declarar")
def _r17_de_b(ctx: Escenario) -> None:
    ctx.carga_id = ctx.extras["cargas"]["B"]
    # La herencia no escribe nada en la carga nueva hasta el primer PUT.
    assert ctx.cuenta("mejora_borrador", "carga_id = %s", ctx.carga_id) == 0
    assert _r17(ctx).status_code == 409, ctx.respuesta.text
    heredado = [{"pi": i["pi"], "tipo": i["tipo"], "causa": i["causa"], "accion": i["accion"]}
                for i in ctx.extras["heredado"]["indicadores"]]
    assert _put(ctx, ctx.profesor, heredado, 0).status_code == 200, ctx.respuesta.text
    assert _r17(ctx).status_code == 409, ctx.respuesta.text
    assert _post(ctx, ctx.profesor, 1).status_code == 201, ctx.respuesta.text
    assert _r17(ctx).status_code == 200, ctx.respuesta.text
    assert _mejora(ctx)["heredado_de"] is None


@then("la API responde 200 con borrador nulo y heredado_de nulo")
def _sin_herencia(ctx: Escenario) -> None:
    cuerpo = _heredada(ctx)
    assert (cuerpo["borrador"], cuerpo["heredado_de"], cuerpo["declaracion"]) == (None, None, None)


@then("la API responde 200 con el borrador de A como borrador, version 0 y heredado_de igual a A")
def _hereda_el_borrador(ctx: Escenario) -> None:
    cuerpo = _heredada(ctx)
    assert cuerpo["heredado_de"] == ctx.extras["cargas"]["A"] and cuerpo["borrador"]["version"] == 0
    # La copia deja 5.3 en VERDE, así que el texto de A llega a la carga nueva con el tipo BP.
    assert [(i["pi"], i["tipo"], i["causa"], i["accion"]) for i in cuerpo["borrador"]["indicadores"]] == [
        (pi, tipo, *REGISTROS["410"][pi]) for pi, tipo in (("5.1", OM), ("5.2", OM), ("5.3", BP))]


@then("la API responde 200 sin carga nueva")
def _sin_carga_nueva(ctx: Escenario) -> None:
    assert ctx.respuesta.status_code == 200, ctx.respuesta.text
    assert ctx.respuesta.json()["carga_id"] == ctx.extras["cargas"]["A"]
    assert "B" not in ctx.extras["cargas"]


@then("la API responde 200 con heredado_de igual a A y borrador nulo")
def _coordinacion_sin_borrador(ctx: Escenario) -> None:
    cuerpo = _heredada(ctx)
    assert cuerpo["heredado_de"] == ctx.extras["cargas"]["A"]
    assert (cuerpo["borrador"], cuerpo["declaracion"], cuerpo["puede_editar"]) == (None, None, False)


@then("la respuesta no trae el texto heredado")
def _sin_texto_heredado(ctx: Escenario) -> None:
    assert not any(texto in ctx.respuesta.text for par in REGISTROS["410"].values() for texto in par)


@then(parsers.re(r'GET /api/cargas/\{B\}/mejora de "(?P<correo>[^"]+)" trae el borrador heredado'))
def _profesor_ve_lo_heredado(ctx: Escenario, correo: str) -> None:
    respuesta = ctx.sesion(correo).get(f"/api/cargas/{ctx.extras['cargas']['B']}/mejora")
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["heredado_de"] == ctx.extras["cargas"]["A"] and cuerpo["borrador"]["version"] == 0
    assert _textos_de_a(cuerpo["borrador"]) == [(pi, *REGISTROS["410"][pi]) for pi in PIS]


# Entonces, la corrección de una declaración

@then("GET /api/cargas/{carga_id}/mejora responde 200 con la declaración anterior vigente y borrador_pendiente verdadero")
def _anterior_vigente(ctx: Escenario) -> None:
    cuerpo = _mejora(ctx)
    assert [(i["pi"], i["causa"], i["accion"]) for i in cuerpo["declaracion"]["indicadores"]] == [
        (pi, *REGISTROS["410"][pi]) for pi in PIS]
    assert cuerpo["borrador_pendiente"] is True
    assert cuerpo["borrador"]["indicadores"][0]["causa"] == CORRECCION_410[0]


@then("el R-17 de esa carga sigue saliendo con el texto de la declaración anterior")
def _r17_anterior(ctx: Escenario) -> None:
    b29, b34 = _b29_y_b34(ctx)
    assert (b29, b34) == ctx.extras["anterior"]
    assert b29.split("\n\n")[0] == f"PI 5.1 · Oportunidad de mejora\n{REGISTROS['410']['5.1'][0]}"


@then("el R-17 de esa carga toma el texto nuevo de 5.1")
def _r17_nuevo(ctx: Escenario) -> None:
    b29, b34 = _b29_y_b34(ctx)
    assert b29.split("\n\n")[0] == f"PI 5.1 · Oportunidad de mejora\n{CORRECCION_410[0]}"
    assert b34.split("\n\n")[0] == f"PI 5.1 · Oportunidad de mejora\n{CORRECCION_410[1]}"
    anterior_a, anterior_b = ctx.extras["anterior"]
    assert b29.split("\n\n")[1:] == anterior_a.split("\n\n")[1:] and b34.split("\n\n")[1:] == anterior_b.split("\n\n")[1:]


@then(parsers.re(r'GET /api/cargas/\{carga_id\}/mejora responde los tres indicadores declarados con estado "PROPUESTA"'))
def _tres_propuesta(ctx: Escenario) -> None:
    cuerpo = _mejora(ctx)
    assert [(i["pi"], i["estado"]) for i in cuerpo["declaracion"]["indicadores"]] == [(pi, "PROPUESTA") for pi in PIS]
    assert cuerpo["declaracion"]["indicadores"][0]["causa"] == CORRECCION_410[0]
    assert cuerpo["borrador_pendiente"] is False


@then("abet.mejora_declaracion tiene 2 filas de esa carga, con la anterior y sus tres filas de "
      "abet.mejora_declaracion_pi intactas")
def _dos_declaraciones(ctx: Escenario) -> None:
    primera, segunda = [fila[0] for fila in ctx.filas(
        "SELECT declaracion_id FROM abet.mejora_declaracion WHERE carga_id = %s ORDER BY declaracion_id", ctx.carga_id)]
    anteriores = ctx.filas("SELECT cc.pi_codigo, d.causa, d.accion FROM abet.mejora_declaracion_pi d"
                           " JOIN abet.carga_columna cc ON cc.carga_id = d.carga_id AND cc.pi_id = d.pi_id"
                           " WHERE d.declaracion_id = %s ORDER BY cc.pi_codigo", primera)
    assert anteriores == [(pi, *REGISTROS["410"][pi]) for pi in PIS]
    assert ctx.cuenta("mejora_declaracion_pi", "declaracion_id = %s", segunda) == 3


# La base sola y los controles Q16 y Q17 (T038, US-47 y US-53)

CONTROLES_NEON = RAIZ / "db" / "plataforma" / "neon" / "controles_neon.sql"
PRUEBAS_SQL = RAIZ / "db" / "pruebas" / "pruebas.sql"
PROHIBIDAS = {"estado", "responsable", "plazo"}


def _control_de_pruebas(nombre: str) -> str:
    """Cuerpo de Q16 o Q17 tal como lo trae db/pruebas/pruebas.sql en su lista control_cero."""
    encontrado = re.search(rf"\('{nombre}', '[^']*', \$q\$(.*?)\$q\$\)", PRUEBAS_SQL.read_text(encoding="utf-8"), re.S)
    assert encontrado is not None, f"pruebas.sql no trae {nombre}"
    return encontrado.group(1).strip()


def _sin_espacios(texto: str) -> str:
    return " ".join(texto.split())


@given("la base con V1_15 y db/plataforma/neon/crear_rol_app.sql aplicado")
def _base_con_v1_15_y_rol(ctx: Escenario) -> None:
    for tabla in TABLAS_V1_15:
        assert ctx.uno("SELECT to_regclass(%s) IS NOT NULL", f"abet.{tabla}"), f"falta abet.{tabla}"
    assert ctx.uno("SELECT has_table_privilege(%s, 'abet.mejora_declaracion', 'INSERT')", ctx.api.base.rol_app)


@when(parsers.re(r"se consultan las columnas de abet\.mejora_borrador, abet\.mejora_borrador_pi, "
                 r"abet\.mejora_declaracion y abet\.mejora_declaracion_pi en information_schema\.columns"))
def _consulta_columnas(ctx: Escenario) -> None:
    ctx.extras["columnas"] = ctx.filas(
        "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'abet'"
        " AND table_name = ANY(%s)", list(TABLAS_V1_15))
    assert {t for t, _ in ctx.extras["columnas"]} == set(TABLAS_V1_15)


@then("ninguna columna se llama estado, responsable ni plazo")
def _sin_columnas_de_gestion(ctx: Escenario) -> None:
    assert not {c for _, c in ctx.extras["columnas"]} & PROHIBIDAS


def _privilegio(ctx: Escenario, tabla: str, privilegio: str) -> bool:
    return bool(ctx.uno("SELECT has_table_privilege(%s, %s, %s)", ctx.api.base.rol_app, f"abet.{tabla}", privilegio))


@then("has_table_privilege de abet_app es verdadero para INSERT y falso para UPDATE y DELETE en "
      "abet.mejora_declaracion y abet.mejora_declaracion_pi")
def _declaracion_solo_insert(ctx: Escenario) -> None:
    for tabla in ("mejora_declaracion", "mejora_declaracion_pi"):
        assert _privilegio(ctx, tabla, "INSERT"), tabla
        assert not _privilegio(ctx, tabla, "UPDATE"), tabla
        assert not _privilegio(ctx, tabla, "DELETE"), tabla


@then("has_table_privilege de abet_app es falso para DELETE en abet.mejora_borrador y abet.mejora_borrador_pi")
def _borrador_sin_delete(ctx: Escenario) -> None:
    for tabla in ("mejora_borrador", "mejora_borrador_pi"):
        assert not _privilegio(ctx, tabla, "DELETE"), tabla


def _carga_410_publicada(ctx: Escenario) -> int:
    respuesta = ctx.subir("docente410@example.invalid", ctx.de_inventados("sintetico_20262_450002_410.xlsx"),
                          "sintetico_20262_450002_410.xlsx", "410")
    assert respuesta.status_code == 201, respuesta.text
    assert ctx.uno("SELECT estado FROM abet.carga WHERE carga_id = %s", ctx.carga_id) == "PUBLICADA"
    return int(ctx.carga_id)


@given("una conexión directa con el rol abet_app y la carga PUBLICADA de la sección 410 con la cabecera de su borrador")
def _directa_con_cabecera_de_borrador(ctx: Escenario) -> None:
    _carga_410_publicada(ctx)
    ctx.directa = ctx.pila.enter_context(psycopg.connect(
        make_conninfo(ctx.api.base.conexion, user=ctx.api.base.rol_app), autocommit=True))
    assert ctx.directa.execute("SELECT current_user").fetchone()[0] == ctx.api.base.rol_app
    ctx.api.dueno.execute("INSERT INTO abet.mejora_borrador (carga_id, version, actualizado_por) VALUES (%s, 1, %s)",
                          (ctx.carga_id, ctx.usuario_id("docente410@example.invalid")))


@given("una conexión directa del dueño de la base y la carga PUBLICADA de la sección 410 con la cabecera de una "
       "declaración")
def _directa_con_cabecera_de_declaracion(ctx: Escenario) -> None:
    _carga_410_publicada(ctx)
    ctx.directa = ctx.api.dueno
    ctx.extras["declaracion_id"] = ctx.uno(
        "INSERT INTO abet.mejora_declaracion (carga_id, version_borrador, declarada_por) VALUES (%s, 1, %s)"
        " RETURNING declaracion_id", ctx.carga_id, ctx.usuario_id("docente410@example.invalid"))


@when(parsers.re(r'esa conexión inserta en abet\.mejora_borrador_pi la causa "(?P<causa>[^"]+)" para el PI '
                 r'(?P<pi>[0-9.]+)'))
def _inserta_causa_en_el_borrador(ctx: Escenario, causa: str, pi: str) -> None:
    ctx.intentar("INSERT INTO abet.mejora_borrador_pi (carga_id, pi_id, causa) SELECT carga_id, pi_id, %s"
                 " FROM abet.carga_columna WHERE carga_id = %s AND pi_codigo = %s", causa, ctx.carga_id, pi)


@when(parsers.re(r'esa conexión inserta en abet\.mejora_declaracion_pi la acción "(?P<accion>[^"]+)" para el PI '
                 r'(?P<pi>[0-9.]+)'))
def _inserta_accion_en_la_declaracion(ctx: Escenario, accion: str, pi: str) -> None:
    # 5.1 de la 410 da 63,6 % contra 80,0 % y queda en ROJO, así que solo el texto puede fallar.
    ctx.intentar("INSERT INTO abet.mejora_declaracion_pi (declaracion_id, pi_id, carga_id, tipo, causa, accion,"
                 " logro_pct, meta_pct, semaforo) SELECT %s, pi_id, carga_id, 'OPORTUNIDAD_MEJORA',"
                 " 'Una causa inventada.', %s, 63.6, 80.0, 'ROJO' FROM abet.carga_columna"
                 " WHERE carga_id = %s AND pi_codigo = %s", ctx.extras["declaracion_id"], accion, ctx.carga_id, pi)


@when("el dueño de la base corre db/pruebas/pruebas.sql")
def _corre_pruebas_sql(ctx: Escenario) -> None:
    # La corrida entera de pruebas.sql la hace db/pruebas/correr_pruebas.sh sobre sus propias bases, con su caso de
    # Q16 y Q17 de la línea «ok Q16 y Q17 en 0 filas». Aquí se corren los dos controles, tal como los trae
    # pruebas.sql, sobre las cargas declaradas por la API de este escenario.
    assert "ok Q16 y Q17 en 0 filas con la 410 declarada" in PRUEBAS_SQL.read_text(encoding="utf-8")
    ctx.extras["controles"] = {nombre: ctx.filas(_control_de_pruebas(nombre)) for nombre in ("Q16", "Q17")}


@then("Q16 y Q17 devuelven 0 filas")
def _q16_y_q17_en_cero(ctx: Escenario) -> None:
    assert ctx.extras["controles"] == {"Q16": [], "Q17": []}
    assert len(ctx.extras["declaradas"]) == 2


@given("una transacción del dueño de la base que quita la fila de 5.3 de la declaración vigente de esa carga y se "
       "deshace al final")
def _transaccion_que_quita_5_3(ctx: Escenario) -> None:
    transaccion = ctx.pila.enter_context(psycopg.connect(ctx.api.base.conexion))
    ctx.extras["transaccion"] = transaccion
    quitadas = transaccion.execute(
        "DELETE FROM abet.mejora_declaracion_pi d USING abet.carga_columna cc WHERE cc.carga_id = d.carga_id"
        " AND cc.pi_id = d.pi_id AND cc.pi_codigo = '5.3' AND d.carga_id = %s AND d.declaracion_id = ("
        "SELECT max(declaracion_id) FROM abet.mejora_declaracion WHERE carga_id = %s)", (ctx.carga_id, ctx.carga_id))
    assert quitadas.rowcount == 1


@when("corre Q17 dentro de esa transacción")
def _corre_q17_en_la_transaccion(ctx: Escenario) -> None:
    ctx.extras["filas_q17"] = ctx.extras["transaccion"].execute(_control_de_pruebas("Q17")).fetchall()
    ctx.extras["transaccion"].rollback()


@then("Q17 devuelve 1 fila con esa carga y el PI 5.3, sin ningún texto del profesor")
def _q17_devuelve_5_3(ctx: Escenario) -> None:
    assert ctx.extras["filas_q17"] == [(ctx.carga_id, "5.3")]
    # Se deshizo: la declaración vigente sigue con sus tres filas y Q17 vuelve a dar 0.
    assert ctx.cuenta("mejora_declaracion_pi", "carga_id = %s", ctx.carga_id) == 3
    assert ctx.filas(_control_de_pruebas("Q17")) == []


@given("db/plataforma/neon/controles_neon.sql")
def _dado_controles_neon(ctx: Escenario) -> None:
    assert CONTROLES_NEON.is_file()


@when("pruebas.sql lo compara con sus controles de 0 filas")
def _compara_con_pruebas_sql(ctx: Escenario) -> None:
    texto = CONTROLES_NEON.read_text(encoding="utf-8")
    bloques = re.findall(r"\\echo '(Q[0-9]{2})\.[^\n]*\n(.*?);\n\\set (q[0-9]{2}) :ROW_COUNT", texto, flags=re.S)
    ctx.extras["neon"] = {nombre: (_sin_espacios(cuerpo), variable) for nombre, cuerpo, variable in bloques}
    ctx.extras["texto_neon"] = texto


@then(r"trae Q16 y Q17 iguales salvo espacios, cada uno con su \set qNN :ROW_COUNT, y su cierre los suma")
def _neon_trae_q16_y_q17(ctx: Escenario) -> None:
    texto = ctx.extras["texto_neon"]
    cierre = texto.split("controles_en_cero", 1)[0].rsplit("SELECT (", 1)[-1]
    for nombre in ("Q16", "Q17"):
        cuerpo, variable = ctx.extras["neon"][nombre]
        assert cuerpo == _sin_espacios(_control_de_pruebas(nombre)), f"{nombre} difiere de pruebas.sql"
        assert variable == nombre.lower()
        assert texto.count(rf"\set {variable} :ROW_COUNT") == 1, nombre
        assert f":{variable}" in cierre, nombre
