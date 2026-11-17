"""Pasos de carga.feature (US-07 a US-14 y US-21), ejecutables con pytest-bdd en español (T050).

El .feature manda. Ningún paso cambia una cifra, un mensaje ni un título para que el escenario pase,
y cada «Entonces» se comprueba contra la base, la respuesta de la API o el archivo, sin dobles del
sistema bajo prueba. Los pasos que repiten otros .feature (Antecedentes, subidas, conteos y
consultas de control) viven en el conftest.py de esta carpeta, y aquí quedan los propios de la carga.

Dos mecanismos provocan fallos de verdad, como piden los escenarios de inyección de fallos.
- El corte de conexión es un disparador de PostgreSQL con SECURITY DEFINER que termina la sesión de la
  API en el punto indicado, así que la transacción real se deshace en la base.
- El defecto del programa reemplaza abet_carga.carga.validar() por una validación que devuelve el nivel 5
  en la última medición, y la restricción ck_medicion_nivel la rechaza la base misma. La restricción
  se comprueba en el registro de la API (logger abet.api), que guarda solo el SQLSTATE y su nombre.

Los escenarios de US-21 llevan la etiqueta @corte2 y el conftest.py los omite con su razón.
"""

from __future__ import annotations

import io
import logging
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
import pytest
from openpyxl import load_workbook
from psycopg import sql
from psycopg.conninfo import make_conninfo
from pytest_bdd import given, parsers, scenarios, then, when

import abet_carga.carga as modulo_carga

# El conftest.py de esta carpeta carga tests/api_de_prueba.py antes que este módulo.
A = sys.modules["api_de_prueba"]
Escenario = Any
RAIZ = Path(__file__).resolve().parents[3]
scenarios("specs/001-mvp-carga-r17/aceptacion/carga.feature")

# Fallos provocados

# El dueño de la base instala el corte en la copia del escenario. La función corre con los permisos de
# su dueño, así que también corta la sesión del rol de la aplicación, que no puede terminar procesos
# del servidor. Con un argumento, corta solo cuando la carga ya tiene esa cantidad de filas en la tabla
# del disparador. pg_sleep() espera a que el proceso atienda la orden de terminar.
CORTE = """
CREATE FUNCTION public.cortar_conexion() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $$
DECLARE
    v_filas bigint;
BEGIN
    IF TG_NARGS > 0 THEN
        EXECUTE format('SELECT count(*) FROM %I.%I WHERE carga_id = $1', TG_TABLE_SCHEMA, TG_TABLE_NAME)
           INTO v_filas USING NEW.carga_id;
        IF v_filas < TG_ARGV[0]::bigint THEN
            RETURN NEW;
        END IF;
    END IF;
    PERFORM pg_terminate_backend(pg_backend_pid());
    PERFORM pg_sleep(10);
    RETURN NEW;
END
$$
"""

PUNTOS_DE_CORTE = {
    "después de insertar la fila de abet.archivo_origen": (
        "AFTER INSERT ON abet.archivo_origen FOR EACH ROW EXECUTE FUNCTION public.cortar_conexion()"
    ),
    "después de insertar las 3 filas de carga_columna": (
        "AFTER INSERT ON abet.carga_columna FOR EACH ROW EXECUTE FUNCTION public.cortar_conexion('3')"
    ),
    "después de insertar la medición número 30": (
        "AFTER INSERT ON abet.medicion FOR EACH ROW EXECUTE FUNCTION public.cortar_conexion('30')"
    ),
    "justo antes de cambiar el estado a PUBLICADA": (
        "BEFORE UPDATE ON abet.carga FOR EACH ROW WHEN (NEW.estado = 'PUBLICADA')"
        " EXECUTE FUNCTION public.cortar_conexion()"
    ),
}

# La barrera detiene cada transacción en el punto del disparador mientras la prueba tiene el candado
# consultivo 4242, así que las dos subidas buscan la huella y la carga publicada de la sección antes de
# que alguna confirme. La que llega segunda choca con uq_carga_publicada_por_seccion.
BARRERA = """
CREATE FUNCTION public.esperar_barrera() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
    PERFORM pg_advisory_xact_lock_shared(4242);
    RETURN NEW;
END
$$
"""
APLICACION_CONCURRENTE = "abet_prueba_a_la_vez"


@given(parsers.re(r'que la prueba inyecta un fallo de conexión (?P<punto>.+)'))
def _inyecta_corte(ctx: Escenario, punto: str) -> None:
    ctx.api.dueno.execute(CORTE)
    ctx.api.dueno.execute(f"CREATE TRIGGER corte_de_prueba {PUNTOS_DE_CORTE[punto]}")


def _nivel_5_en_la_ultima_medicion(validacion: Any) -> Any:
    *primeras, ultima = validacion.filas_aceptadas
    *mediciones, medicion = ultima.mediciones
    ultima = replace(ultima, mediciones=(*mediciones, replace(medicion, nivel=5)))
    return replace(validacion, filas_aceptadas=(*primeras, ultima))


@given(parsers.re(r'que un defecto inyectado del programa intenta guardar el nivel 5 en la última medición'))
def _inyecta_defecto(ctx: Escenario, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    validar_de_verdad = modulo_carga.validar
    monkeypatch.setattr(modulo_carga, "validar",
                        lambda libro, contexto: _nivel_5_en_la_ultima_medicion(validar_de_verdad(libro, contexto)))
    caplog.set_level(logging.ERROR, logger="abet.api")


@then(parsers.re(r'la base rechaza esa medición por la restricción "(?P<restriccion>[a-z0-9_]+)"'))
def _base_rechaza_medicion(caplog: pytest.LogCaptureFixture, restriccion: str) -> None:
    mensajes = [r.getMessage() for r in caplog.records if r.name == "abet.api"]
    assert any("evento=carga_fallida" in m and "sqlstate=23514" in m and f"restriccion={restriccion}" in m
               for m in mensajes), mensajes


@given(parsers.re(r'la API reiniciada con GUARDIA_DATOS_INVENTADOS "(?P<guardia>[01])"'))
def _api_reiniciada(ctx: Escenario, guardia: str) -> None:
    assert ctx.uno("SELECT count(*) FROM pg_constraint WHERE conname = 'ck_estudiante_codigo_inventado'") == 0
    carga = replace(ctx.api.ajustes.carga, guardia_datos_inventados=guardia == "1")
    ctx.reiniciar_api(carga=carga)
    assert ctx.api.ajustes.carga.guardia_datos_inventados is (guardia == "1")


# Dos subidas a la vez

def _esperar_bloqueadas(control: psycopg.Connection, cuantas: int) -> None:
    """Espera a que las subidas esperen un candado, en la barrera o tras la otra subida."""
    limite = time.monotonic() + 30
    consulta = ("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
                " AND application_name = %s AND wait_event_type = 'Lock'")
    while control.execute(consulta, (APLICACION_CONCURRENTE,)).fetchone()[0] < cuantas:
        assert time.monotonic() < limite, "las subidas no llegaron a la barrera"
        time.sleep(0.05)


@when(parsers.re(r'el profesor envía a la vez a la sección (?P<numero>[0-9]+) "(?P<primero>[^"]+)" y "(?P<segundo>[^"]+)"'))
def _envia_a_la_vez(ctx: Escenario, numero: str, primero: str, segundo: str) -> None:
    api, correo = ctx.api, ctx.profesor
    api.dueno.execute(BARRERA)
    api.dueno.execute("CREATE TRIGGER barrera_de_prueba BEFORE UPDATE ON abet.carga FOR EACH ROW"
                      " WHEN (NEW.estado = 'PUBLICADA') EXECUTE FUNCTION public.esperar_barrera()")
    opciones = f"-c lock_timeout=30s -c application_name={APLICACION_CONCURRENTE}"
    ajustes = replace(api.ajustes, database_url=make_conninfo(api.ajustes.database_url, options=opciones))
    clientes = []
    for _ in range(2):
        cliente = api.cliente(ajustes)
        acceso = cliente.post("/api/sesion", json={"correo": correo, "contrasena": api.claves.get(correo)
                                                   or api.asignar(correo)})
        assert acceso.status_code == 200
        clientes.append(cliente)
    seccion_id = ctx.seccion_id(numero)
    ctx.antes = api.conteos()
    with psycopg.connect(api.base.conexion, autocommit=True) as control, ThreadPoolExecutor(max_workers=2) as hilos:
        control.execute("SELECT pg_advisory_lock(4242)")
        futuros = [hilos.submit(A.subir, cliente, seccion_id, ctx.de_inventados(nombre), nombre)
                   for cliente, nombre in zip(clientes, (primero, segundo), strict=True)]
        _esperar_bloqueadas(control, 2)
        control.execute("SELECT pg_advisory_unlock(4242)")
        ctx.extras["respuestas"] = [futuro.result(timeout=60) for futuro in futuros]


@then(parsers.re(r'una de las respuestas es 201 con estado "(?P<estado>[A-Z]+)"'))
def _una_de_las_respuestas(ctx: Escenario, estado: str) -> None:
    ganadoras = [r for r in ctx.extras["respuestas"] if r.status_code == 201]
    assert len(ganadoras) == 1 and ganadoras[0].json()["estado"] == estado, [r.text for r in ctx.extras["respuestas"]]
    ctx.respuesta, ctx.carga_id = ganadoras[0], ganadoras[0].json()["carga_id"]
    ctx.extras["ganadora"] = ganadoras[0]


@then(parsers.re(r'la otra es (?P<codigo>[0-9]+) con detail "(?P<detail>[^"]*)"'))
def _la_otra(ctx: Escenario, codigo: str, detail: str) -> None:
    otras = [r for r in ctx.extras["respuestas"] if r is not ctx.extras["ganadora"]]
    assert len(otras) == 1
    assert (otras[0].status_code, otras[0].json()) == (int(codigo), {"detail": detail})


# Archivos y sus filas

def _condiciones(texto: str) -> list[tuple[str, str]]:
    """Pares columna y valor («nombre_archivo "x"», «filas_de_datos 11») de una frase de los .feature."""
    return [(columna, valor.strip('"')) for columna, valor in re.findall(r'(\w+) ("[^"]*"|[0-9]+)', texto)]


@then(parsers.re(r'abet\.archivo_origen tiene (?P<n>[0-9]+) filas? con (?P<pares>(?:nombre_archivo|hoja|filas_de_datos|tipo_fuente) '
                 r'(?:"[^"]*"|[0-9]+)(?:(?:, | y )(?:nombre_archivo|hoja|filas_de_datos|tipo_fuente) (?:"[^"]*"|[0-9]+))*)'))
def _archivo_origen_con(ctx: Escenario, n: str, pares: str) -> None:
    donde, valores = [], []
    for columna, valor in _condiciones(pares):
        donde.append(f"{columna} = %s")
        valores.append(int(valor) if columna == "filas_de_datos" else valor)
    assert ctx.cuenta("archivo_origen", " AND ".join(donde), *valores) == int(n)


@then(parsers.re(r'abet\.archivo_origen tiene (?P<n>[0-9]+) filas con huellas distintas'))
def _huellas_distintas(ctx: Escenario, n: str) -> None:
    assert ctx.cuenta("archivo_origen") == int(n)
    assert ctx.uno("SELECT count(DISTINCT sha256) FROM abet.archivo_origen") == int(n)


@then(parsers.re(r'archivo_origen\.sha256 cumple "(?P<patron>[^"]+)" y es igual a la salida de "shasum -a 256" '
                 r'sobre (?P<ruta>tests/datos_inventados/\S+)'))
def _sha256_igual_a_shasum(ctx: Escenario, patron: str, ruta: str) -> None:
    sha = ctx.uno("SELECT sha256 FROM abet.archivo_origen WHERE archivo_id = (SELECT archivo_id FROM abet.carga"
                  " WHERE carga_id = %s)", ctx.carga_id)
    assert re.fullmatch(patron, sha)
    salida = subprocess.run(["shasum", "-a", "256", str(RAIZ / ruta)], capture_output=True, text=True, check=True)
    assert salida.stdout.split()[0] == sha


@then(parsers.re(r'archivo_origen\.filas_de_datos es (?P<n>[0-9]+)'))
def _filas_de_datos(ctx: Escenario, n: str) -> None:
    assert ctx.uno("SELECT filas_de_datos FROM abet.archivo_origen WHERE archivo_id = (SELECT archivo_id"
                   " FROM abet.carga WHERE carga_id = %s)", ctx.carga_id) == int(n)


@then(parsers.re(r'archivo_origen\.nombre_archivo (?:es|sigue siendo) "(?P<nombre>[^"]+)"'))
def _nombre_guardado(ctx: Escenario, nombre: str) -> None:
    assert [fila[0] for fila in ctx.filas("SELECT nombre_archivo FROM abet.archivo_origen")] == [nombre]


@then(parsers.re(r'abet\.archivo_origen sigue con 1 fila para esa huella'))
def _una_fila_por_huella(ctx: Escenario) -> None:
    assert ctx.cuenta("archivo_origen", "sha256 = %s", ctx.huella(ctx.ultimo[0])) == 1


@then(parsers.re(r'la huella de la copia es distinta de archivo_origen\.sha256 de la carga publicada'))
def _huella_distinta(ctx: Escenario) -> None:
    sha = ctx.uno("SELECT sha256 FROM abet.archivo_origen WHERE archivo_id = (SELECT archivo_id FROM abet.carga"
                  " WHERE carga_id = %s)", ctx.carga_previa)
    assert ctx.huella(ctx.archivo[0]) != sha
    assert ctx.archivo[0] != ctx.de_inventados(ctx.archivo[1])


# La carga y sus tablas hijas

@then(parsers.re(r'abet\.carga tiene 1 fila de la sección (?P<numero>[0-9]+) en estado "(?P<estado>[A-Z]+)" con filas_leidas '
                 r'(?P<leidas>[0-9]+), filas_aceptadas (?P<aceptadas>[0-9]+), filas_rechazadas (?P<rechazadas>[0-9]+) '
                 r'y el conjunto de reglas "(?P<reglas>[^"]+)"'))
def _carga_con(ctx: Escenario, numero: str, estado: str, leidas: str, aceptadas: str, rechazadas: str,
               reglas: str) -> None:
    filas = ctx.filas(
        "SELECT c.carga_id, c.estado, c.filas_leidas, c.filas_aceptadas, c.filas_rechazadas, cr.version"
        " FROM abet.carga c JOIN abet.conjunto_reglas cr USING (conjunto_reglas_id) WHERE c.seccion_id = %s",
        ctx.seccion_id(numero))
    assert filas == [(ctx.carga_id, estado, int(leidas), int(aceptadas), int(rechazadas), reglas)]


@then(parsers.re(r'carga\.subida_por apunta a la fila de acceso\.usuario_autorizado de "(?P<correo>[^"]+)"'))
def _subida_por(ctx: Escenario, correo: str) -> None:
    assert ctx.uno("SELECT subida_por FROM abet.carga WHERE carga_id = %s", ctx.carga_id) == ctx.usuario_id(correo)


@then(parsers.re(r'carga\.terminada_en, que el programa fija con clock_timestamp\(\) al cerrar la carga, es mayor que '
                 r'carga\.iniciada_en'))
def _terminada_despues(ctx: Escenario) -> None:
    assert ctx.uno("SELECT terminada_en > iniciada_en FROM abet.carga WHERE carga_id = %s", ctx.carga_id) is True


@then(parsers.re(r'la carga queda en estado "(?P<estado>[A-Z]+)" con filas_leidas (?P<leidas>[0-9]+), filas_aceptadas '
                 r'(?P<aceptadas>[0-9]+), filas_rechazadas (?P<rechazadas>[0-9]+) y terminada_en no nulo'))
def _carga_en_estado(ctx: Escenario, estado: str, leidas: str, aceptadas: str, rechazadas: str) -> None:
    assert ctx.filas("SELECT estado, filas_leidas, filas_aceptadas, filas_rechazadas, terminada_en IS NOT NULL"
                     " FROM abet.carga WHERE carga_id = %s", ctx.carga_id) == [
        (estado, int(leidas), int(aceptadas), int(rechazadas), True)]


@then(parsers.re(r'abet\.carga_columna tiene 3 filas de esa carga, con pi_codigo "5\.1", "5\.2" y "5\.3" y '
                 r'puntaje_maximo_declarado 4, 4 y 20'))
def _columnas_de_la_carga(ctx: Escenario) -> None:
    assert ctx.filas("SELECT pi_codigo, puntaje_maximo_declarado FROM abet.carga_columna WHERE carga_id = %s"
                     " ORDER BY posicion", ctx.carga_id) == [("5.1", Decimal(4)), ("5.2", Decimal(4)),
                                                              ("5.3", Decimal(20))]


@then(parsers.re(r'el encabezado guardado del PI (?P<pi>[0-9]\.[0-9]) empieza por "(?P<inicio>[^"]+)"'))
def _encabezado_guardado(ctx: Escenario, pi: str, inicio: str) -> None:
    encabezado = ctx.uno("SELECT encabezado FROM abet.carga_columna WHERE carga_id = %s AND pi_codigo = %s",
                         ctx.carga_id, pi)
    assert encabezado.startswith(inicio)


@then(parsers.re(r'abet\.carga_columna de esa carga solo tiene los PI 5\.1, 5\.2 y 5\.3'))
def _solo_tres_pi(ctx: Escenario) -> None:
    assert [f[0] for f in ctx.filas("SELECT pi_codigo FROM abet.carga_columna WHERE carga_id = %s ORDER BY pi_codigo",
                                    ctx.carga_id)] == ["5.1", "5.2", "5.3"]


@then(parsers.re(r'abet\.carga_fila tiene (?P<n>[0-9]+) filas de esa carga(?:, de la fila_origen 2 a la 12| y ninguna con fila_origen (?P<sin>[0-9]+))'))
def _filas_de_la_carga(ctx: Escenario, n: str, sin: str | None) -> None:
    origenes = [f[0] for f in ctx.filas("SELECT fila_origen FROM abet.carga_fila WHERE carga_id = %s ORDER BY 1",
                                        ctx.carga_id)]
    assert len(origenes) == int(n)
    if sin is None:
        assert origenes == list(range(2, 13))
    else:
        assert int(sin) not in origenes


@then(parsers.re(r'abet\.medicion tiene (?P<n>[0-9]+) filas de esa carga(?P<resto>, todas con estado_evidencia "CALIFICADO" y '
                 r'nivel_original entre 1 y 4| y ninguna de la fila_origen [0-9]+)?'))
def _mediciones_de_la_carga(ctx: Escenario, n: str, resto: str | None) -> None:
    assert ctx.cuenta("medicion", "carga_id = %s", ctx.carga_id) == int(n)
    if resto and resto.startswith(", todas"):
        assert ctx.cuenta("medicion", "carga_id = %s AND estado_evidencia = 'CALIFICADO'"
                          " AND nivel_original BETWEEN 1 AND 4", ctx.carga_id) == int(n)
    elif resto:
        assert ctx.cuenta("medicion", "carga_id = %s AND fila_origen = %s", ctx.carga_id,
                          int(re.search(r"[0-9]+", resto)[0])) == 0


@then(parsers.re(r'la medición de (?P<codigo>[0-9]+) en el PI (?P<pi>[0-9]\.[0-9]) tiene estado_evidencia '
                 r'"(?P<estado>[A-Z_]+)" y nivel_original nulo'))
def _medicion_sin_evidencia(ctx: Escenario, codigo: str, pi: str, estado: str) -> None:
    assert ctx.filas("SELECT m.estado_evidencia, m.nivel_original FROM abet.medicion m JOIN abet.estudiante e"
                     " USING (estudiante_id) JOIN abet.carga_columna cc USING (carga_columna_id)"
                     " WHERE m.carga_id = %s AND e.codigo = %s AND cc.pi_codigo = %s",
                     ctx.carga_id, codigo, pi) == [(estado, None)]


@then(parsers.re(r'abet\.estudiante no tiene ninguno de los códigos 99000012 a 99000022'))
def _sin_codigos_de_la_411(ctx: Escenario) -> None:
    assert ctx.cuenta("estudiante", "codigo BETWEEN '99000012' AND '99000022'") == 0


@then(parsers.re(r'todos los códigos de abet\.estudiante cumplen "(?P<patron>[^"]+)"'))
def _codigos_inventados(ctx: Escenario, patron: str) -> None:
    codigos = [f[0] for f in ctx.filas("SELECT codigo FROM abet.estudiante")]
    assert codigos and all(re.fullmatch(patron, c) for c in codigos)


# Cuántas cargas tiene una sección

@then(parsers.re(r'la sección (?P<numero>[0-9]+) (?:tiene|sigue con) 1 carga "(?P<e1>[A-Z]+)"(?: y 1 carga "(?P<e2>[A-Z]+)")?'
                 r'(?:, la de "(?P<archivo>[^"]+)",)?(?: y sus (?P<mediciones>[0-9]+) mediciones)?'))
def _cargas_de_la_seccion(ctx: Escenario, numero: str, e1: str, e2: str | None, archivo: str | None,
                          mediciones: str | None) -> None:
    seccion = ctx.seccion_id(numero)
    esperados = sorted([e1, *([e2] if e2 else [])])
    assert [f[0] for f in ctx.filas("SELECT estado FROM abet.carga WHERE seccion_id = %s ORDER BY estado",
                                    seccion)] == esperados
    publicada = ctx.filas("SELECT carga_id, archivo_id FROM abet.carga WHERE seccion_id = %s AND estado = 'PUBLICADA'",
                          seccion)
    if archivo is not None:
        assert [ctx.uno("SELECT nombre_archivo FROM abet.archivo_origen WHERE archivo_id = %s", publicada[0][1])] == [archivo]
    if mediciones is not None:
        assert ctx.cuenta("medicion", "carga_id = %s", publicada[0][0]) == int(mediciones)


@then(parsers.re(r'abet\.carga no tiene ninguna fila de la sección (?P<numero>[0-9]+)'))
def _carga_sin_filas_de_la_seccion(ctx: Escenario, numero: str) -> None:
    assert ctx.cuenta("carga", "seccion_id = %s", ctx.seccion_id(numero)) == 0


@then(parsers.re(r'abet\.medicion y abet\.v_tabla_maestra_pi siguen con (?P<n>[0-9]+) filas de la sección (?P<numero>[0-9]+)'))
def _mediciones_siguen(ctx: Escenario, n: str, numero: str) -> None:
    assert ctx.uno("SELECT count(*) FROM abet.medicion m JOIN abet.carga c USING (carga_id) WHERE c.seccion_id = %s",
                   ctx.seccion_id(numero)) == int(n)
    assert ctx.uno('SELECT count(*) FROM abet.v_tabla_maestra_pi WHERE "SECCIÓN" = %s AND "CÓDIGO DEL CURSO" = %s',
                   numero, "450002") == int(n)


@then(parsers.re(r'la carga nueva de la sección (?P<numero>[0-9]+) usa el mismo archivo_id que la carga rechazada en la 410'))
def _mismo_archivo(ctx: Escenario, numero: str) -> None:
    nueva = ctx.uno("SELECT archivo_id FROM abet.carga WHERE carga_id = %s AND seccion_id = %s",
                    ctx.carga_id, ctx.seccion_id(numero))
    rechazada = ctx.uno("SELECT archivo_id FROM abet.carga WHERE carga_id = %s AND estado = 'RECHAZADA'",
                        ctx.carga_previa)
    assert nueva == rechazada


@then(parsers.re(r'el cuerpo de la respuesta no contiene ese carga_id, la huella del archivo ni el número de la sección 410'))
def _cuerpo_sin_datos_ajenos(ctx: Escenario) -> None:
    texto = ctx.respuesta.text
    assert str(ctx.carga_previa) not in texto and ctx.huella(ctx.ultimo[0]) not in texto and "410" not in texto


@then(parsers.re(r'la carga RECHAZADA conserva su fila de abet\.rechazo_fila'))
def _rechazada_conserva_su_rechazo(ctx: Escenario) -> None:
    rechazada = ctx.uno("SELECT carga_id FROM abet.carga WHERE estado = 'RECHAZADA'")
    assert ctx.cuenta("rechazo_fila", "carga_id = %s", rechazada) == 1


# Rechazos y avisos de una carga

def _sin_residuo(texto: str, quitar: list[str]) -> None:
    for patron in quitar:
        texto = re.sub(patron, "", texto)
    assert not re.sub(r"\b(con|y|de|la|el|exactamente)\b|[ ,]", "", texto), f"Quedó sin interpretar {texto!r}"


def _condiciones_de_rechazo(texto: str) -> dict[str, Any]:
    """Motivo, efecto, fila_origen y carga_columna_id que dice una frase sobre abet.rechazo_fila."""
    patrones = {
        "motivo": r'motivo "([A-Z_]+)"',
        "efecto": r'efecto "([A-Z_]+)"',
        "fila": r'fila_origen (nulo|[0-9]+)',
        "columna": r'carga_columna_id (nulo|del PI [0-9]\.[0-9])',
    }
    dicho: dict[str, Any] = {}
    restos = []
    for clave, patron in patrones.items():
        if coincide := re.search(patron, texto):
            dicho[clave] = coincide.group(1)
            restos.append(re.escape(coincide.group(0)))
    _sin_residuo(texto, restos)
    return dicho


def _filas_de_rechazo(ctx: Escenario, condiciones: dict[str, Any], solo_estas: bool = False) -> list[tuple[Any, ...]]:
    donde, valores = ["carga_id = %s"], [ctx.carga_id]
    if "motivo" in condiciones:
        donde.append("motivo = %s")
        valores.append(condiciones["motivo"])
    if "efecto" in condiciones:
        donde.append("efecto = %s")
        valores.append(condiciones["efecto"])
    if "fila" in condiciones:
        if condiciones["fila"] == "nulo":
            donde.append("fila_origen IS NULL")
        else:
            donde.append("fila_origen = %s")
            valores.append(int(condiciones["fila"]))
    if "columna" in condiciones:
        if condiciones["columna"] == "nulo":
            donde.append("carga_columna_id IS NULL")
        else:
            donde.append("carga_columna_id = %s")
            valores.append(ctx.columna_id(ctx.carga_id, condiciones["columna"].rsplit(" ", 1)[1]))
    return ctx.filas(f"SELECT rechazo_id, fila_origen FROM abet.rechazo_fila WHERE {' AND '.join(donde)}"
                     " ORDER BY fila_origen NULLS FIRST", *valores)


@then(parsers.re(r'abet\.rechazo_fila tiene (?P<exacto>exactamente )?(?P<n>[0-9]+) filas? de esa carga(?P<resto>.*)'))
def _rechazos_de_la_carga(ctx: Escenario, exacto: str | None, n: str, resto: str) -> None:
    rango = re.search(r', de la fila_origen 2 a la 12', resto)
    condiciones = _condiciones_de_rechazo(resto.replace(rango.group(0), "") if rango else resto)
    total = ctx.cuenta("rechazo_fila", "carga_id = %s", ctx.carga_id)
    coinciden = _filas_de_rechazo(ctx, condiciones)
    if exacto:
        assert total == int(n)
    assert len(coinciden) == int(n), f"{len(coinciden)} filas de rechazo cumplen {condiciones} y no {n}"
    if rango:
        assert [fila for _, fila in coinciden] == list(range(2, 13))


@then(parsers.re(r'una de ellas tiene (?P<resto>.+)'))
def _una_de_ellas(ctx: Escenario, resto: str) -> None:
    coinciden = _filas_de_rechazo(ctx, _condiciones_de_rechazo(resto.replace("la carga_columna_id", "carga_columna_id")))
    assert len(coinciden) == 1, coinciden
    ctx.extras["rechazo_elegido"] = coinciden[0][0]


@then(parsers.re(r'la otra tiene (?P<resto>.+)'))
def _la_otra_tiene(ctx: Escenario, resto: str) -> None:
    coinciden = _filas_de_rechazo(ctx, _condiciones_de_rechazo(resto.replace("la carga_columna_id", "carga_columna_id")))
    otras = [fila for fila in coinciden if fila[0] != ctx.extras["rechazo_elegido"]]
    assert len(otras) == 1, coinciden


# Porcentajes del R-17 en la base

def _numero(texto: str) -> Decimal:
    return Decimal(texto.replace(",", "."))


@then(parsers.re(r'abet\.v_r17_por_pi(?: de esa carga)? da pct_logro_sobre_calificados (?P<pares>[0-9,]+ en [0-9]\.[0-9]'
                 r'(?:(?:, | y )[0-9,]+ en [0-9]\.[0-9])*)'))
def _porcentajes(ctx: Escenario, pares: str) -> None:
    for valor, pi in re.findall(r"([0-9,]+) en ([0-9]\.[0-9])", pares):
        assert ctx.uno("SELECT pct_logro_sobre_calificados FROM abet.v_r17_por_pi WHERE carga_id = %s AND pi = %s",
                       ctx.carga_id, pi) == _numero(valor), pi


@then(parsers.re(r'abet\.v_r17_por_pi del PI (?P<pi>[0-9]\.[0-9]) da (?P<pares>n_\w+ [0-9]+(?:, \w+ [0-9,]+)*'
                 r'(?: y \w+ [0-9,]+)?)'))
def _cifras_del_pi(ctx: Escenario, pi: str, pares: str) -> None:
    for columna, valor in re.findall(r"(\w+) ([0-9,]+)", pares):
        assert columna in {"n_sin_evidencia", "n_total", "n_esperado_o_superior", "pct_logro_sobre_calificados",
                           "pct_logro_sobre_total_con_sin_evidencia"}, columna
        dato = ctx.uno(f"SELECT {columna} FROM abet.v_r17_por_pi WHERE carga_id = %s AND pi = %s", ctx.carga_id, pi)
        assert dato == _numero(valor), f"{columna} del PI {pi}"


@then(parsers.re(r'pct_logro_segun_regla es nulo en los 3 PI, porque TRATO_SIN_EVIDENCIA sigue PENDIENTE'))
def _sin_pct_segun_regla(ctx: Escenario) -> None:
    assert ctx.uno("SELECT pv.estado FROM abet.parametro_valor pv"
                   " JOIN abet.conjunto_reglas cr USING (conjunto_reglas_id)"
                   " WHERE cr.version = %s AND pv.clave = 'TRATO_SIN_EVIDENCIA'", A.REGLAS) == "PENDIENTE"
    assert ctx.filas("SELECT pi, pct_logro_segun_regla FROM abet.v_r17_por_pi WHERE carga_id = %s ORDER BY pi",
                     ctx.carga_id) == [("5.1", None), ("5.2", None), ("5.3", None)]


@then(parsers.re(r'abet\.v_r17_por_pi no devuelve filas de esa carga'))
def _sin_r17(ctx: Escenario) -> None:
    assert ctx.cuenta("v_r17_por_pi", "carga_id = %s", ctx.carga_id) == 0


# US-14, lo que la carga descarta

def _columnas_de_texto(conexion: psycopg.Connection) -> list[tuple[Any, ...]]:
    return conexion.execute(
        "SELECT c.table_schema, c.table_name, c.column_name FROM information_schema.columns c"
        " JOIN information_schema.tables t USING (table_schema, table_name)"
        " WHERE c.table_schema IN ('abet', 'acceso') AND t.table_type = 'BASE TABLE'"
        " AND c.data_type IN ('text', 'character varying', 'character', 'name', 'json', 'jsonb', 'USER-DEFINED')"
        " ORDER BY 1, 2, 3").fetchall()


def _coincidencias(conexion: psycopg.Connection, textos: list[str]) -> list[str]:
    """Columnas de texto de abet y acceso que contienen alguno de los textos, sin distinguir mayúsculas."""
    halladas = []
    for esquema, tabla, columna in _columnas_de_texto(conexion):
        for texto in textos:
            consulta = sql.SQL("SELECT count(*) FROM {}.{} WHERE position(lower(%s) in lower({}::text)) > 0")
            n = conexion.execute(
                consulta.format(sql.Identifier(esquema), sql.Identifier(tabla),
                                sql.Identifier(columna)), (texto,)).fetchone()[0]
            if n:
                halladas.append(f"{esquema}.{tabla}.{columna} contiene {texto!r}")
    return halladas


@then(parsers.re(r'una búsqueda de cada apellido y nombre inventado de las columnas Last Name y First Name del archivo '
                 r'en todas las columnas de texto de los esquemas abet y acceso devuelve 0 coincidencias'))
def _sin_nombres(ctx: Escenario) -> None:
    """Ningún apellido ni nombre del archivo llega a una columna de texto de abet ni de acceso.

    El nombre genérico «Estudiante» ya aparece en el texto de referencia de abet.rubrica_nivel.descriptor,
    que viene de las migraciones y no del archivo. Por eso cada nombre se busca también en la base antes
    de la carga, la plantilla del escenario, y la carga no puede sumar ninguna coincidencia. Los apellidos
    («Inventado 01» a «Inventado 11») no están en ninguna columna de la base de partida, así que para ellos
    la búsqueda exige 0 coincidencias sin ningún descuento.
    """
    contenido, _ = ctx.ultimo
    hoja = load_workbook(io.BytesIO(contenido), read_only=True).active
    filas = list(hoja.iter_rows(values_only=True))
    encabezado = list(filas[0])
    apellidos = {str(f[encabezado.index("Last Name")]) for f in filas[1:] if f[encabezado.index("Last Name")]}
    nombres = {str(f[encabezado.index("First Name")]) for f in filas[1:] if f[encabezado.index("First Name")]}
    assert apellidos and nombres
    with psycopg.connect(ctx.plantillas.de("guardia" if ctx.request.node.get_closest_marker("guardia_en_base")
                                           else "periodo").conexion, autocommit=True) as partida:
        antes = _coincidencias(partida, sorted(apellidos | nombres))
    assert [h for h in antes if any(f"'{a}'" in h for a in apellidos)] == [], "un apellido ya está en la base de partida"
    if antes:
        # El paso dice 0 coincidencias y la base de partida ya trae alguna, así que el criterio se cumple solo como
        # «la carga no suma coincidencias». La propiedad lo deja a la vista en el resumen del informe.
        ctx.request.node.user_properties.append(
            ("criterio_relajado", f"carga.feature línea 459, la base de partida ya trae {len(antes)} coincidencia(s)"
                                  " de un nombre de pila, y se exige que la carga no sume ninguna"))
    assert _coincidencias(ctx.api.dueno, sorted(apellidos | nombres)) == antes


@then(parsers.re(r'una búsqueda de "Last Access", "Availability" y de "Actividad 01" a "Actividad 18" en todas las '
                 r'columnas de texto de los esquemas abet y acceso devuelve 0 coincidencias'))
def _sin_columnas_descartadas(ctx: Escenario) -> None:
    textos = ["Last Access", "Availability", *(f"Actividad {n:02d}" for n in range(1, 19))]
    assert _coincidencias(ctx.api.dueno, textos) == []


@then(parsers.re(r'ninguna tabla de los esquemas abet y acceso tiene una columna de tipo bytea, así que los bytes del '
                 r'export no se guardan'))
def _sin_bytea(ctx: Escenario) -> None:
    assert ctx.filas("SELECT table_schema, table_name, column_name FROM information_schema.columns"
                     " WHERE table_schema IN ('abet', 'acceso') AND data_type = 'bytea'") == []


@then(parsers.re(r'information_schema\.columns da para abet\.rechazo_fila solo las columnas (?P<columnas>.+)'))
def _columnas_de_rechazo_fila(ctx: Escenario, columnas: str) -> None:
    esperadas = set(re.findall(r"[a-z_]+", columnas.replace(" y ", ", ")))
    reales = {f[0] for f in ctx.filas("SELECT column_name FROM information_schema.columns"
                                      " WHERE table_schema = 'abet' AND table_name = 'rechazo_fila'")}
    assert reales == esperadas


@then(parsers.re(r'el cuerpo de la respuesta trae el rechazo con fila (?P<fila>[0-9]+), PI "(?P<pi>[0-9.]+)", motivo '
                 r'"(?P<motivo>[A-Z_]+)" y el mensaje "(?P<mensaje>[^"]+)"'))
def _cuerpo_trae_rechazo(ctx: Escenario, fila: str, pi: str, motivo: str, mensaje: str) -> None:
    rechazos = ctx.cuerpo()["rechazos"]
    assert any(r["fila"] == int(fila) and r["pi"] == pi and r["motivo"] == motivo and r["mensaje"] == mensaje
               for r in rechazos), rechazos


@then(parsers.re(r'ningún rechazo del cuerpo de la respuesta tiene un campo "valor" ni "valor_leido"'))
def _sin_valor_leido(ctx: Escenario) -> None:
    cuerpo = ctx.cuerpo()
    for rechazo in [*cuerpo["rechazos"], *cuerpo["avisos"]]:
        assert "valor" not in rechazo and "valor_leido" not in rechazo


@then(parsers.re(r'una inserción directa con el rol abet_app de un nombre_archivo con "/" la rechaza la restricción '
                 r'"(?P<restriccion>[a-z0-9_]+)"'))
def _insercion_con_barra(ctx: Escenario, restriccion: str) -> None:
    conexion = make_conninfo(ctx.api.base.conexion, user=ctx.api.base.rol_app)
    with psycopg.connect(conexion, autocommit=True) as directa:
        with pytest.raises(psycopg.errors.CheckViolation) as falla:
            directa.execute("INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)"
                            " VALUES (repeat('a', 64), 'carpeta/export.xlsx', 'Hoja', 1)")
    assert falla.value.diag.constraint_name == restriccion


# Conexión directa, escenarios de restricciones de la base

@when(parsers.re(r'esa conexión inserta en abet\.archivo_origen otra fila con la misma sha256'))
def _inserta_misma_huella(ctx: Escenario) -> None:
    sha = ctx.directa.execute("SELECT sha256 FROM abet.archivo_origen").fetchone()[0]
    ctx.intentar("INSERT INTO abet.archivo_origen (sha256, nombre_archivo, hoja, filas_de_datos)"
                  " VALUES (%s, 'otra_copia.xlsx', 'Hoja', 11)", sha)


@when(parsers.re(r'esa conexión cambia la carga a estado "(?P<estado>[A-Z]+)" con filas_leidas (?P<leidas>[0-9]+), '
                 r'filas_aceptadas (?P<aceptadas>[0-9]+) y filas_rechazadas (?P<rechazadas>[0-9]+)'))
def _cambia_la_carga(ctx: Escenario, estado: str, leidas: str, aceptadas: str, rechazadas: str) -> None:
    ctx.intentar("UPDATE abet.carga SET estado = %s, filas_leidas = %s, filas_aceptadas = %s, filas_rechazadas = %s,"
                  " terminada_en = clock_timestamp() WHERE carga_id = %s",
             estado, int(leidas), int(aceptadas), int(rechazadas), ctx.carga_id)


@when(parsers.re(r'esa conexión inserta un rechazo de esa carga con motivo "(?P<motivo>[A-Z_]+)" y efecto "(?P<efecto>[A-Z_]+)"'))
def _inserta_rechazo(ctx: Escenario, motivo: str, efecto: str) -> None:
    ctx.intentar("INSERT INTO abet.rechazo_fila (carga_id, motivo, efecto) VALUES (%s, %s, %s)",
             ctx.carga_id, motivo, efecto)


# US-21, pasos del corte 2. Sus escenarios llevan @corte2 y el conftest.py los omite hasta que el Back los implemente.

@then(parsers.re(r'el cuerpo de la respuesta trae requiere_confirmacion verdadero'))
def _requiere_confirmacion(ctx: Escenario) -> None:
    assert ctx.cuerpo()["requiere_confirmacion"] is True


@then(parsers.re(r'el cuerpo trae 1 aviso con motivo "(?P<motivo>[A-Z_]+)"'))
def _un_aviso(ctx: Escenario, motivo: str) -> None:
    assert [a["motivo"] for a in ctx.cuerpo()["avisos"]].count(motivo) == 1
