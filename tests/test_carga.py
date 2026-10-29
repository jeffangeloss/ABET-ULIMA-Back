"""Pruebas de la carga del export en una sola transacción (T033 de specs/001-mvp-carga-r17/tasks.md).

Cada prueba nombra en su función la regla de negocio (business rule, BR) de
specs/features/carga-export/carga-export.spec.md que comprueba, con lo que debe pasar y lo que no
debe pasar (AGENTS.md, regla 8). Las cifras, los motivos y los mensajes son literales de
carga.feature y del contrato de la interfaz de programación de aplicaciones (application
programming interface, API), en docs/03-api/contrato.md del Front.

Las pruebas que escriben corren en el clúster desechable de tests/conftest.py, nunca en el de la
Mac. La plantilla es una base de tests/base_desechable.py con las migraciones, el rol de la
aplicación de db/plataforma/neon/crear_rol_app.sql y los datos de 2026-2, y cada prueba trabaja
en una copia propia de esa plantilla. Cada prueba corre dos veces, con la conexión del dueño de la
base y con SET ROLE al rol de la aplicación, que tiene el privilegio mínimo de Neon. Las copias
de un export con cambios se arman en tmp_path con el generador y nunca se versionan.
"""

from __future__ import annotations

import hashlib
import io
import re
import secrets
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, replace
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo
from openpyxl import load_workbook
from psycopg.rows import dict_row

import abet_carga
import abet_carga.carga as modulo_carga
from abet_carga.lector import leer
from abet_carga.modelos import ContextoSeccion, Efecto, Motivo, PiDelPlan, Rechazo

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "tests" / "datos_inventados"
CONTROLES = RAIZ / "db" / "plataforma" / "neon" / "controles_neon.sql"

CORRECTO = "sintetico_20262_450002_410.xlsx"
CON_ERROR = "export_inventado_410_con_error.xlsx"
EXPORT_411 = "export_inventado_411.xlsx"
HOJA_410 = "gc_SINTETICO_20262_450002_410_f"
DOCENTE_410 = "docente410@example.invalid"
DOCENTE_411 = "docente411@example.invalid"
REGLAS = "R-2026-BORRADOR"
CONFIGURACION = modulo_carga.Configuracion(conjunto_reglas=REGLAS)
SIN_GUARDIA = modulo_carga.Configuracion(conjunto_reglas=REGLAS, guardia_datos_inventados=False)
TABLAS = ("archivo_origen", "carga", "carga_columna", "carga_fila", "estudiante", "medicion", "rechazo_fila")
VACIAS = dict.fromkeys(TABLAS, 0)


# Bases de las pruebas

@pytest.fixture(scope="module")
def plantilla(base_desechable: ModuleType) -> Iterator[Any]:
    """Base con las migraciones, el rol de la aplicación y los datos de 2026-2, que cada prueba copia."""
    with base_desechable.abierta() as base:
        yield base


@pytest.fixture
def base(base_desechable: ModuleType, plantilla: Any) -> Iterator[Any]:
    """Copia propia de la plantilla, con el mismo rol de la aplicación, que se borra al terminar la prueba.

    CREATE DATABASE con TEMPLATE copia la plantilla en una décima de segundo, mientras que aplicar otra
    vez las migraciones tarda casi un segundo. borrar() quita la copia con su guardia de nombres, y la
    copia llega a borrar() sin rol_app, así que el rol sigue con la plantilla.
    """
    nombre = f"{plantilla.nombre}_{secrets.token_hex(3)}"
    with psycopg.connect(make_conninfo(plantilla.conexion, dbname="postgres"), autocommit=True) as servidor:
        servidor.execute(
            sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(sql.Identifier(nombre), sql.Identifier(plantilla.nombre))
        )
    copia = base_desechable.BaseDesechable(nombre, make_conninfo(plantilla.conexion, dbname=nombre), None, None)
    try:
        yield replace(copia, rol_app=plantilla.rol_app)
    finally:
        base_desechable.borrar(copia)


@pytest.fixture(params=["dueno", "rol_app"])
def modo(request: pytest.FixtureRequest) -> str:
    """Conexión con que corre cargar(), la del dueño de la base o la del rol de la aplicación."""
    return str(request.param)


@pytest.fixture
def conexion(base: Any, modo: str) -> Iterator[psycopg.Connection]:
    conexion = _conectar(base, modo)
    try:
        yield conexion
    finally:
        conexion.close()


@pytest.fixture
def revision(base: Any) -> Iterator[psycopg.Connection]:
    """Conexión aparte del dueño de la base, que comprueba lo que la carga deja escrito."""
    with psycopg.connect(base.conexion, autocommit=True) as conexion:
        yield conexion


# Ayudas de las pruebas

def _conectar(base: Any, modo: str, **opciones: Any) -> psycopg.Connection:
    """Conexión del dueño o, con SET ROLE, del rol de la aplicación, como en db/pruebas/probar_rol_app.sql."""
    conexion = psycopg.connect(base.conexion, autocommit=True, **opciones)
    if modo == "rol_app":
        conexion.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(base.rol_app)))
    return conexion


def _filas(revision: psycopg.Connection, consulta: str, *parametros: object) -> list[dict[str, Any]]:
    with revision.cursor(row_factory=dict_row) as cursor:
        return cursor.execute(consulta, parametros or None).fetchall()


def _valores(revision: psycopg.Connection, consulta: str, *parametros: object) -> list[tuple[Any, ...]]:
    return revision.execute(consulta, parametros or None).fetchall()


def _uno(revision: psycopg.Connection, consulta: str, *parametros: object) -> Any:
    fila = revision.execute(consulta, parametros or None).fetchone()
    assert fila is not None
    return fila[0]


def _seccion_id(revision: psycopg.Connection, numero: str = "410", asignatura: str = "450002") -> int:
    return int(
        _uno(
            revision,
            "SELECT s.seccion_id FROM abet.seccion s"
            " JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id"
            " JOIN abet.periodo p ON p.periodo_id = s.periodo_id"
            " WHERE s.numero = %s AND a.codigo = %s AND p.codigo = '2026-2'",
            numero,
            asignatura,
        )
    )


def _usuario_id(revision: psycopg.Connection, correo: str = DOCENTE_410) -> int:
    return int(_uno(revision, "SELECT usuario_id FROM acceso.usuario_autorizado WHERE correo = %s", correo))


def _archivo(nombre: str) -> bytes:
    return (CARPETA / nombre).read_bytes()


def _subir(
    conexion: psycopg.Connection,
    revision: psycopg.Connection,
    contenido: bytes,
    nombre: str,
    *,
    seccion: str = "410",
    correo: str = DOCENTE_410,
    configuracion: modulo_carga.Configuracion = CONFIGURACION,
) -> Any:
    return modulo_carga.cargar(
        conexion,
        contenido,
        nombre_archivo=nombre,
        seccion_id=_seccion_id(revision, seccion),
        usuario_id=_usuario_id(revision, correo),
        configuracion=configuracion,
    )


def _export_410(generador: ModuleType) -> Any:
    plantilla, _ = generador.leer_plantilla()
    return generador.export_410(plantilla)


def _bytes(generador: ModuleType, export: Any, tmp_path: Path, nombre: str = "copia.xlsx") -> bytes:
    """Bytes de una copia del export que arma el generador en tmp_path, nunca en tests/datos_inventados/."""
    return bytes(generador.escribir(export, tmp_path / nombre).read_bytes())


def _rechazos(revision: psycopg.Connection, carga_id: int | None) -> list[tuple[Any, ...]]:
    """Motivo, efecto, fila, PI de la columna (carga_columna_id) y PI del plan (pi_id) de cada fila de rechazo_fila."""
    return _valores(
        revision,
        "SELECT r.motivo, r.efecto, r.fila_origen, cc.pi_codigo, p.codigo FROM abet.rechazo_fila r"
        " LEFT JOIN abet.carga_columna cc ON cc.carga_columna_id = r.carga_columna_id"
        " LEFT JOIN abet.pi p ON p.pi_id = r.pi_id"
        " WHERE r.carga_id = %s ORDER BY r.motivo, r.fila_origen NULLS FIRST",
        carga_id,
    )


def _porcentajes(revision: psycopg.Connection, carga_id: int | None) -> list[tuple[str, Decimal]]:
    return _valores(
        revision,
        "SELECT pi, pct_logro_sobre_calificados FROM abet.v_r17_por_pi WHERE carga_id = %s ORDER BY pi",
        carga_id,
    )


def _esperados(pct_51: str, pct_52: str, pct_53: str) -> list[tuple[str, Decimal]]:
    return [("5.1", Decimal(pct_51)), ("5.2", Decimal(pct_52)), ("5.3", Decimal(pct_53))]


def _cuentas(revision: psycopg.Connection, carga_id: int | None) -> tuple[Any, ...]:
    """Estado y filas leídas, aceptadas y rechazadas de la carga, más sus filas de carga_fila y de medicion."""
    return tuple(
        _valores(
            revision,
            "SELECT c.estado, c.filas_leidas, c.filas_aceptadas, c.filas_rechazadas,"
            " (SELECT count(*) FROM abet.carga_fila f WHERE f.carga_id = c.carga_id),"
            " (SELECT count(*) FROM abet.medicion m WHERE m.carga_id = c.carga_id)"
            " FROM abet.carga c WHERE c.carga_id = %s",
            carga_id,
        )[0]
    )


def _conteos(revision: psycopg.Connection) -> dict[str, int]:
    """Filas de las siete tablas que escribe una carga, para comprobar que un rechazo no deja rastro."""
    return {
        tabla: _uno(revision, sql.SQL("SELECT count(*) FROM abet.{}").format(sql.Identifier(tabla)).as_string(revision))
        for tabla in TABLAS
    }


def _consultas_de_control() -> dict[str, str]:
    """Q01 a Q14 de controles_neon.sql, copia literal de las de db/pruebas/pruebas.sql que correr_pruebas.sh coteja."""
    texto = CONTROLES.read_text(encoding="utf-8")
    bloques = re.findall(r"\\echo '(Q[0-9]{2})\.[^\n]*\n(.*?);\n\\set q[0-9]{2} :ROW_COUNT", texto, flags=re.S)
    return {nombre: consulta.strip() for nombre, consulta in bloques}


def _controles_con_filas(revision: psycopg.Connection) -> dict[str, int]:
    """Consultas de control que devuelven filas, con cuántas devuelve cada una. Vacío es Q01 a Q14 en cero."""
    consultas = _consultas_de_control()
    assert sorted(consultas) == [f"Q{numero:02d}" for numero in range(1, 15)]
    con_filas = {nombre: len(_valores(revision, consulta)) for nombre, consulta in consultas.items()}
    return {nombre: filas for nombre, filas in con_filas.items() if filas}


# Configuración del despliegue (BR-CARGA-01 y BR-CARGA-07)

def test_br_carga_01_el_conjunto_de_reglas_de_la_carga_sale_de_conjunto_reglas() -> None:
    configuracion = modulo_carga.Configuracion.desde_entorno({"CONJUNTO_REGLAS": "R-2026-BORRADOR"})
    assert configuracion.conjunto_reglas == "R-2026-BORRADOR"


@pytest.mark.parametrize("entorno", [{}, {"CONJUNTO_REGLAS": ""}, {"CONJUNTO_REGLAS": "   "}])
def test_br_carga_01_sin_conjunto_reglas_no_hay_configuracion(entorno: dict[str, str]) -> None:
    with pytest.raises(modulo_carga.ConfiguracionInvalida, match="CONJUNTO_REGLAS"):
        modulo_carga.Configuracion.desde_entorno(entorno)


@pytest.mark.parametrize(
    ("valor", "encendida"),
    [("1", True), (None, True), ("", True), ("false", True), ("no", True), ("0", False), (" 0 ", False)],
)
def test_br_carga_07_solo_un_cero_en_guardia_datos_inventados_apaga_la_guardia(
    valor: str | None, encendida: bool
) -> None:
    entorno = {"CONJUNTO_REGLAS": "R-2026-BORRADOR"}
    if valor is not None:
        entorno["GUARDIA_DATOS_INVENTADOS"] = valor
    assert modulo_carga.Configuracion.desde_entorno(entorno).guardia_datos_inventados is encendida


def test_br_carga_07_sin_entorno_explicito_la_configuracion_sale_de_os_environ(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONJUNTO_REGLAS", "R-2026-BORRADOR")
    monkeypatch.setenv("GUARDIA_DATOS_INVENTADOS", "0")
    configuracion = modulo_carga.Configuracion.desde_entorno()
    assert (configuracion.conjunto_reglas, configuracion.guardia_datos_inventados) == ("R-2026-BORRADOR", False)


# US-07, el export correcto (BR-CARGA-01, BR-CARGA-02, BR-CARGA-06, BR-CARGA-14 y BR-CARGA-16)

def test_br_carga_01_02_06_14_16_el_export_correcto_queda_publicado_entero(
    conexion: psycopg.Connection, revision: psycopg.Connection, generador: ModuleType
) -> None:
    contenido = _archivo(CORRECTO)
    resultado = _subir(conexion, revision, contenido, CORRECTO)

    assert (resultado.resultado, resultado.codigo_http, resultado.mensaje) == ("PUBLICADA", 201, None)
    [archivo] = _filas(revision, "SELECT * FROM abet.archivo_origen")
    assert (archivo["nombre_archivo"], archivo["hoja"], archivo["filas_de_datos"], archivo["tipo_fuente"]) == (
        CORRECTO,
        HOJA_410,
        11,
        "BLACKBOARD_EXPORT",
    )
    assert re.fullmatch("[0-9a-f]{64}", archivo["sha256"])
    assert archivo["sha256"] == hashlib.sha256(contenido).hexdigest()
    [carga] = _filas(
        revision,
        "SELECT c.*, cr.version AS reglas FROM abet.carga c"
        " JOIN abet.conjunto_reglas cr ON cr.conjunto_reglas_id = c.conjunto_reglas_id",
    )
    assert (carga["carga_id"], carga["seccion_id"], carga["archivo_id"]) == (
        resultado.carga_id,
        _seccion_id(revision),
        archivo["archivo_id"],
    )
    assert (carga["estado"], carga["filas_leidas"], carga["filas_aceptadas"], carga["filas_rechazadas"]) == (
        "PUBLICADA",
        11,
        11,
        0,
    )
    assert (carga["reglas"], carga["subida_por"], carga["programa_version"]) == (
        REGLAS,
        _usuario_id(revision),
        abet_carga.__version__,
    )
    # terminada_en sale de clock_timestamp() y iniciada_en de now(), la hora de inicio de la transacción.
    assert carga["terminada_en"] > carga["iniciada_en"]

    leidas = leer(contenido, nombre_archivo=CORRECTO).columnas_pi
    columnas = _valores(
        revision,
        "SELECT pi_codigo, posicion, encabezado, bb_columna_id, puntaje_maximo_declarado"
        " FROM abet.carga_columna ORDER BY posicion",
    )
    assert columnas == [
        (c.pi_codigo, c.posicion, c.encabezado, c.bb_columna_id, c.puntaje_maximo_declarado) for c in leidas
    ]
    assert [(pi, puntaje) for pi, _, _, _, puntaje in columnas] == [("5.1", 4), ("5.2", 4), ("5.3", 20)]
    assert columnas[0][2].startswith("5.1 [Total Pts: 4 Score]")

    filas = _valores(
        revision,
        "SELECT f.fila_origen, e.codigo FROM abet.carga_fila f"
        " JOIN abet.estudiante e ON e.estudiante_id = f.estudiante_id ORDER BY f.fila_origen",
    )
    assert filas == [(fila, str(codigo)) for fila, codigo, _ in generador.NIVELES_410]
    mediciones = _valores(
        revision,
        "SELECT m.fila_origen, cc.pi_codigo, m.estado_evidencia, m.nivel_original FROM abet.medicion m"
        " JOIN abet.carga_columna cc ON cc.carga_columna_id = m.carga_columna_id"
        " ORDER BY m.fila_origen, cc.pi_codigo",
    )
    assert mediciones == [
        (fila, pi, "CALIFICADO", nivel)
        for fila, _, niveles in generador.NIVELES_410
        for pi, nivel in zip(("5.1", "5.2", "5.3"), niveles, strict=True)
    ]
    # El Total Pts de 20 en 5.3 deja su aviso y la carga sigue (valor provisional de D-04).
    assert _valores(
        revision,
        "SELECT r.motivo, r.efecto, r.fila_origen, cc.pi_codigo, r.pi_id FROM abet.rechazo_fila r"
        " LEFT JOIN abet.carga_columna cc ON cc.carga_columna_id = r.carga_columna_id",
    ) == [("PUNTAJE_MAXIMO_DISTINTO", "AVISO", None, "5.3", None)]
    assert _valores(
        revision,
        "SELECT pi, pct_logro_sobre_calificados FROM abet.v_r17_por_pi WHERE carga_id = %s ORDER BY pi",
        resultado.carga_id,
    ) == [("5.1", Decimal("63.6")), ("5.2", Decimal("63.6")), ("5.3", Decimal("72.7"))]
    assert _uno(revision, "SELECT count(*) FROM abet.carga WHERE estado = 'EN_CURSO'") == 0
    assert _controles_con_filas(revision) == {}


# US-10, filas rechazadas y avisos de columna (BR-CARGA-14, BR-CARGA-15 y BR-CARGA-16)

def test_br_carga_15_16_el_5_de_la_fila_3_rechaza_esa_fila_completa(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    resultado = _subir(conexion, revision, _archivo(CON_ERROR), CON_ERROR)

    assert (resultado.resultado, resultado.codigo_http, resultado.mensaje) == ("PUBLICADA", 201, None)
    assert _cuentas(revision, resultado.carga_id) == ("PUBLICADA", 11, 10, 1, 10, 30)
    assert _uno(revision, "SELECT filas_de_datos FROM abet.archivo_origen") == 11
    # Una fila por rechazo y por aviso, sin el valor leído, que rechazo_fila no tiene dónde guardar.
    assert _rechazos(revision, resultado.carga_id) == [
        ("NIVEL_FUERA_DE_ESCALA", "RECHAZA_FILA", 3, "5.2", None),
        ("PUNTAJE_MAXIMO_DISTINTO", "AVISO", None, "5.3", None),
    ]
    assert _uno(revision, "SELECT count(*) FROM abet.carga_fila WHERE fila_origen = 3") == 0
    assert _uno(revision, "SELECT count(*) FROM abet.estudiante WHERE codigo = '99000002'") == 0
    assert _porcentajes(revision, resultado.carga_id) == _esperados("60.0", "60.0", "70.0")
    assert _controles_con_filas(revision) == {}


def test_br_carga_16_si_todas_las_filas_se_rechazan_la_carga_no_se_publica(
    conexion: psycopg.Connection, revision: psycopg.Connection, generador: ModuleType, tmp_path: Path
) -> None:
    export = _export_410(generador)
    for fila in range(2, 13):
        export = generador.con_celda(export, fila, "5.2", 5)
    resultado = _subir(conexion, revision, _bytes(generador, export, tmp_path), CORRECTO)

    assert (resultado.resultado, resultado.codigo_http) == ("RECHAZADA", 201)
    assert resultado.mensaje == "Ninguna fila se pudo aceptar. La carga no se publicó."
    assert _cuentas(revision, resultado.carga_id) == ("RECHAZADA", 11, 0, 11, 0, 0)
    rechazos = [r for r in _rechazos(revision, resultado.carga_id) if r[1] == "RECHAZA_FILA"]
    assert rechazos == [("NIVEL_FUERA_DE_ESCALA", "RECHAZA_FILA", fila, "5.2", None) for fila in range(2, 13)]
    assert _porcentajes(revision, resultado.carga_id) == []
    assert _uno(revision, "SELECT count(*) FROM abet.estudiante") == 0
    assert _controles_con_filas(revision) == {}


def test_br_carga_15_una_celda_de_pi_vacia_se_carga_sin_evidencia_y_no_rechaza_la_fila(
    conexion: psycopg.Connection, revision: psycopg.Connection, generador: ModuleType, tmp_path: Path
) -> None:
    export = generador.con_celda(_export_410(generador), 3, "5.2", None)
    resultado = _subir(conexion, revision, _bytes(generador, export, tmp_path), CORRECTO)

    assert _cuentas(revision, resultado.carga_id) == ("PUBLICADA", 11, 11, 0, 11, 33)
    assert _valores(
        revision,
        "SELECT m.estado_evidencia, m.nivel_original FROM abet.medicion m"
        " JOIN abet.carga_columna cc ON cc.carga_columna_id = m.carga_columna_id"
        " JOIN abet.estudiante e ON e.estudiante_id = m.estudiante_id"
        " WHERE e.codigo = '99000002' AND cc.pi_codigo = '5.2'",
    ) == [("SIN_EVIDENCIA", None)]
    assert _valores(
        revision,
        "SELECT n_sin_evidencia, n_total, n_esperado_o_superior, pct_logro_sobre_calificados,"
        " pct_logro_sobre_total_con_sin_evidencia, pct_logro_segun_regla"
        " FROM abet.v_r17_por_pi WHERE carga_id = %s AND pi = '5.2'",
        resultado.carga_id,
    ) == [(1, 11, 6, Decimal("60.0"), Decimal("54.5"), None)]
    assert _porcentajes(revision, resultado.carga_id) == _esperados("63.6", "60.0", "72.7")


@pytest.mark.parametrize(
    ("fila", "codigo", "motivo", "pct"),
    [
        (3, None, "CODIGO_VACIO", ("60.0", "60.0", "70.0")),
        (12, 99000001, "CODIGO_DUPLICADO", ("70.0", "70.0", "80.0")),
    ],
)
def test_br_carga_15_un_codigo_vacio_o_repetido_rechaza_su_fila_sin_pi(
    conexion: psycopg.Connection,
    revision: psycopg.Connection,
    generador: ModuleType,
    tmp_path: Path,
    fila: int,
    codigo: int | None,
    motivo: str,
    pct: tuple[str, str, str],
) -> None:
    export = generador.con_celda(_export_410(generador), fila, "Username", codigo)
    resultado = _subir(conexion, revision, _bytes(generador, export, tmp_path), CORRECTO)

    assert _cuentas(revision, resultado.carga_id) == ("PUBLICADA", 11, 10, 1, 10, 30)
    # Un rechazo por código no tiene PI, así que no lleva carga_columna_id ni pi_id.
    assert [r for r in _rechazos(revision, resultado.carga_id) if r[1] == "RECHAZA_FILA"] == [
        (motivo, "RECHAZA_FILA", fila, None, None)
    ]
    assert _porcentajes(revision, resultado.carga_id) == _esperados(*pct)
    assert _controles_con_filas(revision) == {}


def test_br_carga_07_15_con_la_guardia_apagada_un_codigo_mal_formado_rechaza_solo_su_fila(
    conexion: psycopg.Connection, revision: psycopg.Connection, generador: ModuleType, tmp_path: Path
) -> None:
    export = generador.con_celda(_export_410(generador), 4, "Username", 9900001)
    resultado = _subir(conexion, revision, _bytes(generador, export, tmp_path), CORRECTO, configuracion=SIN_GUARDIA)

    assert _cuentas(revision, resultado.carga_id) == ("PUBLICADA", 11, 10, 1, 10, 30)
    assert [r for r in _rechazos(revision, resultado.carga_id) if r[1] == "RECHAZA_FILA"] == [
        ("CODIGO_INVALIDO", "RECHAZA_FILA", 4, None, None)
    ]
    assert _porcentajes(revision, resultado.carga_id) == _esperados("70.0", "60.0", "70.0")
    assert _uno(revision, "SELECT count(*) FROM abet.estudiante WHERE codigo !~ '^99[0-9]{6}$'") == 0


def test_br_carga_14_una_columna_de_pi_fuera_del_plan_se_ignora_con_aviso(
    conexion: psycopg.Connection, revision: psycopg.Connection, generador: ModuleType, tmp_path: Path
) -> None:
    export = generador.con_columna(_export_410(generador), "4.1 [Total Pts: 4 Score] |9000041", [3] * 11)
    resultado = _subir(conexion, revision, _bytes(generador, export, tmp_path), CORRECTO)

    assert _cuentas(revision, resultado.carga_id) == ("PUBLICADA", 11, 11, 0, 11, 33)
    # El aviso de 4.1 no lleva carga_columna_id ni pi_id, porque la columna no entra a carga_columna.
    assert _rechazos(revision, resultado.carga_id) == [
        ("COLUMNA_PI_FUERA_DEL_PLAN", "AVISO", None, None, None),
        ("PUNTAJE_MAXIMO_DISTINTO", "AVISO", None, "5.3", None),
    ]
    assert _valores(revision, "SELECT pi_codigo FROM abet.carga_columna ORDER BY pi_codigo") == [
        ("5.1",),
        ("5.2",),
        ("5.3",),
    ]


def test_br_carga_15_cada_fila_aceptada_toma_el_estudiante_que_ya_existe(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    existente = _uno(revision, "INSERT INTO abet.estudiante (codigo) VALUES ('99000005') RETURNING estudiante_id")
    resultado = _subir(conexion, revision, _archivo(CORRECTO), CORRECTO)

    assert _cuentas(revision, resultado.carga_id) == ("PUBLICADA", 11, 11, 0, 11, 33)
    assert _uno(revision, "SELECT count(*) FROM abet.estudiante") == 11
    # 99000005 está en la fila 6 del export (NIVELES_410 del generador).
    assert _uno(revision, "SELECT estudiante_id FROM abet.carga_fila WHERE fila_origen = 6") == existente


# US-12 y US-13, la carga rechazada entera (BR-CARGA-11, BR-CARGA-12 y BR-CARGA-13)

def _segunda_5_1(generador: ModuleType) -> Any:
    return generador.con_columna(_export_410(generador), "5.1 [Total Pts: 4 Score]", [3] * 11)


def _rechazada_entera(revision: psycopg.Connection, resultado: Any) -> list[tuple[Any, ...]]:
    """Comprueba la forma de una carga RECHAZADA por estructura, sección o periodo y devuelve su rechazo."""
    assert (resultado.resultado, resultado.codigo_http) == ("RECHAZADA", 201)
    [carga] = _filas(revision, "SELECT * FROM abet.carga WHERE carga_id = %s", resultado.carga_id)
    assert (carga["estado"], carga["filas_leidas"], carga["filas_aceptadas"], carga["filas_rechazadas"]) == (
        "RECHAZADA",
        0,
        0,
        0,
    )
    assert carga["terminada_en"] is not None and carga["subida_por"] == _usuario_id(revision)
    # Sin columnas, filas, mediciones ni avisos, y fuera de la vista del R-17.
    assert _uno(revision, "SELECT count(*) FROM abet.carga_columna") == 0
    assert _cuentas(revision, resultado.carga_id)[4:] == (0, 0)
    assert _porcentajes(revision, resultado.carga_id) == []
    assert _uno(revision, "SELECT count(*) FROM abet.estudiante") == 0
    assert _controles_con_filas(revision) == {}
    return _rechazos(revision, resultado.carga_id)


@pytest.mark.parametrize(
    ("origen", "motivo", "pi", "mensaje"),
    [
        ("vacio_410.xlsx", "ARCHIVO_SIN_FILAS", None, "El archivo no trae filas de estudiantes."),
        (
            "sin_5_2_410.xlsx",
            "PI_DEL_PLAN_AUSENTE",
            "5.2",
            "Falta la columna del PI 5.2 que el plan de medición pide para esta sección.",
        ),
        (
            "sin_username_ni_student_id_410.xlsx",
            "COLUMNA_CODIGO_AUSENTE",
            None,
            "El archivo no tiene la columna Username ni Student ID.",
        ),
        (_segunda_5_1, "PI_REPETIDO", "5.1", "El PI 5.1 aparece en dos columnas del archivo."),
    ],
)
def test_br_carga_13_un_defecto_de_estructura_rechaza_la_carga_entera_y_deja_su_motivo(
    conexion: psycopg.Connection,
    revision: psycopg.Connection,
    generador: ModuleType,
    tmp_path: Path,
    origen: Any,
    motivo: str,
    pi: str | None,
    mensaje: str,
) -> None:
    contenido = _archivo(origen) if isinstance(origen, str) else _bytes(generador, origen(generador), tmp_path)
    resultado = _subir(conexion, revision, contenido, CORRECTO)

    assert resultado.mensaje == mensaje
    # pi_id guarda el PI que falta o que se repite, para que la constancia leída después lo nombre (BR-R17-10).
    assert _rechazada_entera(revision, resultado) == [(motivo, "RECHAZA_CARGA", None, None, pi)]
    assert _valores(revision, "SELECT hoja, filas_de_datos FROM abet.archivo_origen") == [
        (HOJA_410, leer(contenido, nombre_archivo=CORRECTO).filas_de_datos)
    ]


@pytest.mark.parametrize(
    ("hoja", "nombre", "motivo", "mensaje"),
    [
        (
            "gc_SINTETICO_20262_450002_411_f",
            CORRECTO,
            "SECCION_NO_COINCIDE",
            "El archivo corresponde a la sección 411 y usted eligió la 410. No se publicó.",
        ),
        (
            "gc_SINTETICO_20262_450010_410_f",
            CORRECTO,
            "SECCION_NO_COINCIDE",
            "El archivo corresponde a la asignatura 450010 y usted eligió la 450002. No se publicó.",
        ),
        (
            "gc_SINTETICO_20261_450002_410_f",
            CORRECTO,
            "PERIODO_NO_COINCIDE",
            "El archivo corresponde al periodo 2026-1 y la sección elegida es de 2026-2. No se publicó.",
        ),
        (
            "Hoja1",
            "gc_SINTETICO_20262_450002_411_fullgc_2026-10-20.xlsx",
            "SECCION_NO_COINCIDE",
            "El archivo corresponde a la sección 411 y usted eligió la 410. No se publicó.",
        ),
    ],
)
def test_br_carga_11_12_otra_seccion_asignatura_o_periodo_rechaza_la_carga(
    conexion: psycopg.Connection,
    revision: psycopg.Connection,
    generador: ModuleType,
    tmp_path: Path,
    hoja: str,
    nombre: str,
    motivo: str,
    mensaje: str,
) -> None:
    contenido = _bytes(generador, generador.con_hoja(_export_410(generador), hoja), tmp_path)
    resultado = _subir(conexion, revision, contenido, nombre)

    assert resultado.mensaje == mensaje
    assert _rechazada_entera(revision, resultado) == [(motivo, "RECHAZA_CARGA", None, None, None)]
    assert _valores(revision, "SELECT nombre_archivo, hoja FROM abet.archivo_origen") == [(nombre, hoja)]
    assert _uno(revision, "SELECT count(*) FROM abet.carga WHERE estado = 'PUBLICADA'") == 0


def test_br_carga_11_el_export_de_la_411_subido_en_la_410_no_deja_sus_estudiantes(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    resultado = _subir(conexion, revision, _archivo(EXPORT_411), EXPORT_411)

    assert resultado.mensaje == "El archivo corresponde a la sección 411 y usted eligió la 410. No se publicó."
    assert _rechazada_entera(revision, resultado) == [("SECCION_NO_COINCIDE", "RECHAZA_CARGA", None, None, None)]
    assert _valores(revision, "SELECT hoja FROM abet.archivo_origen") == [("gc_SINTETICO_20262_450002_411_f",)]


@pytest.mark.parametrize(
    ("hoja", "nombre"),
    [
        ("gc_SINTETICO_20262_450002_410", CORRECTO),
        ("Hoja1", "gc_SINTETICO_20262_450002_410_fullgc_2026-10-20.xlsx"),
    ],
)
def test_br_carga_11_la_hoja_truncada_o_el_nombre_del_archivo_declaran_la_410_y_publican(
    conexion: psycopg.Connection,
    revision: psycopg.Connection,
    generador: ModuleType,
    tmp_path: Path,
    hoja: str,
    nombre: str,
) -> None:
    contenido = _bytes(generador, generador.con_hoja(_export_410(generador), hoja), tmp_path)
    resultado = _subir(conexion, revision, contenido, nombre)

    assert (resultado.resultado, resultado.codigo_http, resultado.mensaje) == ("PUBLICADA", 201, None)
    assert _cuentas(revision, resultado.carga_id) == ("PUBLICADA", 11, 11, 0, 11, 33)


def test_br_carga_13_despues_de_un_rechazo_un_archivo_distinto_es_otro_archivo_y_se_publica(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    rechazada = _subir(conexion, revision, _archivo("sin_5_2_410.xlsx"), "sin_5_2_410.xlsx")
    publicada = _subir(conexion, revision, _archivo(CORRECTO), CORRECTO)

    assert (rechazada.resultado, publicada.resultado) == ("RECHAZADA", "PUBLICADA")
    assert _uno(revision, "SELECT count(DISTINCT sha256) FROM abet.archivo_origen") == 2
    assert _valores(revision, "SELECT estado, count(*) FROM abet.carga GROUP BY estado ORDER BY estado") == [
        ("PUBLICADA", 1),
        ("RECHAZADA", 1),
    ]
    assert _rechazos(revision, rechazada.carga_id) == [("PI_DEL_PLAN_AUSENTE", "RECHAZA_CARGA", None, None, "5.2")]
    assert _controles_con_filas(revision) == {}


# US-08, US-11 y US-13, lo que se detiene sin dejar rastro (BR-CARGA-01, BR-CARGA-03, BR-CARGA-07 y BR-CARGA-11)

MENSAJE_GUARDIA = (
    "El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada."
)


def _sin_rastro(revision: psycopg.Connection, antes: dict[str, int]) -> None:
    assert _conteos(revision) == antes
    assert _uno(revision, "SELECT count(*) FROM abet.carga WHERE estado = 'EN_CURSO'") == 0


@pytest.mark.parametrize("codigo", [10000004, 98999999, 9900001])
def test_br_carga_07_un_codigo_que_no_es_inventado_detiene_el_archivo_entero_sin_rastro(
    conexion: psycopg.Connection, revision: psycopg.Connection, generador: ModuleType, tmp_path: Path, codigo: int
) -> None:
    if codigo == generador.CODIGO_GUARDIA:
        contenido = generador.escribir_export_guardia(tmp_path / "guardia.xlsx").read_bytes()
    else:
        contenido = _bytes(generador, generador.con_celda(_export_410(generador), 4, "Username", codigo), tmp_path)
    antes = _conteos(revision)
    resultado = _subir(conexion, revision, contenido, CORRECTO)

    assert (resultado.resultado, resultado.codigo_http, resultado.mensaje) == ("GUARDIA", 422, MENSAJE_GUARDIA)
    assert resultado.carga_id is None
    # Ni el mensaje ni el resultado entero nombran el código, aunque el resultado vaya a un registro.
    assert str(codigo) not in repr(resultado)
    _sin_rastro(revision, antes)


@pytest.mark.parametrize("codigo", [99000000, 99999999])
def test_br_carga_07_los_extremos_del_rango_inventado_pasan_la_guardia(
    conexion: psycopg.Connection, revision: psycopg.Connection, generador: ModuleType, tmp_path: Path, codigo: int
) -> None:
    contenido = _bytes(generador, generador.con_celda(_export_410(generador), 4, "Username", codigo), tmp_path)
    resultado = _subir(conexion, revision, contenido, CORRECTO)

    assert _cuentas(revision, resultado.carga_id) == ("PUBLICADA", 11, 11, 0, 11, 33)
    assert _uno(revision, "SELECT count(*) FROM abet.estudiante WHERE codigo = %s", str(codigo)) == 1


def test_br_carga_03_la_guardia_va_antes_de_buscar_la_huella_en_la_base(
    conexion: psycopg.Connection, revision: psycopg.Connection, generador: ModuleType, tmp_path: Path
) -> None:
    # Con la guardia apagada, el 9900001 rechaza solo su fila y la huella del archivo queda registrada.
    contenido = _bytes(generador, generador.con_celda(_export_410(generador), 4, "Username", 9900001), tmp_path)
    assert _subir(conexion, revision, contenido, CORRECTO, configuracion=SIN_GUARDIA).resultado == "PUBLICADA"
    antes = _conteos(revision)

    # Con la guardia encendida, los mismos bytes se detienen en la guardia y no llegan al 200 de la
    # huella publicada en la 410 ni al 409 de la huella publicada en otra sección.
    en_la_410 = _subir(conexion, revision, contenido, CORRECTO)
    en_la_411 = _subir(conexion, revision, contenido, CORRECTO, seccion="411", correo=DOCENTE_411)

    assert (en_la_410.resultado, en_la_410.codigo_http, en_la_410.mensaje) == ("GUARDIA", 422, MENSAJE_GUARDIA)
    assert (en_la_411.resultado, en_la_411.codigo_http, en_la_411.carga_id) == ("GUARDIA", 422, None)
    _sin_rastro(revision, antes)


def _mayor_de_un_mega() -> bytes:
    return _archivo(CORRECTO).ljust(1_200_000, b"\0")


@pytest.mark.parametrize(
    ("origen", "nombre", "motivo", "mensaje"),
    [
        ("danado_410.xlsx", "danado_410.xlsx", "NO_SE_PUDO_ABRIR", "No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard."),
        (
            "protegido_410.xlsx",
            "protegido_410.xlsx",
            "PROTEGIDO_CON_CONTRASENA",
            "El archivo está protegido con contraseña. Guárdelo sin contraseña y súbalo.",
        ),
        ("pdf_renombrado.xlsx", "export_410.pdf", "TIPO_NO_ADMITIDO", "Solo se admiten exports de Blackboard en formato .xlsx."),
        (
            "pdf_renombrado.xlsx",
            "export_410.xlsx",
            "CONTENIDO_NO_ES_LIBRO",
            "El contenido del archivo no es un libro de Excel aunque su nombre termine en .xlsx.",
        ),
        (_mayor_de_un_mega, "export_410.xlsx", "ARCHIVO_DEMASIADO_GRANDE", "El archivo supera el máximo de 1 MB."),
    ],
)
def test_br_carga_03_un_archivo_que_no_se_puede_leer_se_detiene_sin_rastro_y_con_su_huella(
    conexion: psycopg.Connection, revision: psycopg.Connection, origen: Any, nombre: str, motivo: str, mensaje: str
) -> None:
    contenido = _archivo(origen) if isinstance(origen, str) else origen()
    antes = _conteos(revision)
    resultado = _subir(conexion, revision, contenido, nombre)

    assert (resultado.resultado, resultado.codigo_http, resultado.mensaje) == ("ILEGIBLE", 422, mensaje)
    # La huella y el motivo llegan al registro de la aplicación también del archivo de más de 1 MB (BR-CARGA-08).
    assert (resultado.sha256, resultado.motivo) == (hashlib.sha256(contenido).hexdigest(), motivo)
    _sin_rastro(revision, antes)


def test_br_carga_11_un_export_que_no_declara_su_seccion_se_detiene_sin_rastro(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    antes = _conteos(revision)
    resultado = _subir(conexion, revision, _archivo("hoja1_sin_seccion.xlsx"), "notas.xlsx")

    assert (resultado.resultado, resultado.codigo_http, resultado.mensaje) == (
        "SECCION_SIN_DECLARAR",
        422,
        "El archivo no indica su sección. Sube el export de Blackboard sin cambiar el nombre de su hoja.",
    )
    _sin_rastro(revision, antes)


def test_br_carga_01_03_una_seccion_sin_plan_responde_422_antes_de_leer_el_archivo(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    revision.execute("DELETE FROM abet.plan_medicion")
    antes = _conteos(revision)
    for contenido, nombre in ((_archivo(CORRECTO), CORRECTO), (_archivo("danado_410.xlsx"), "danado_410.xlsx")):
        resultado = _subir(conexion, revision, contenido, nombre)
        assert (resultado.resultado, resultado.codigo_http, resultado.mensaje) == (
            "SIN_PLAN",
            422,
            "La carrera aún no registra el plan de medición de esta sección.",
        )
    _sin_rastro(revision, antes)


def test_br_carga_01_una_seccion_que_no_existe_responde_404_sin_rastro(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    ajena = _uno(revision, "SELECT max(seccion_id) + 1000 FROM abet.seccion")
    antes = _conteos(revision)
    resultado = modulo_carga.cargar(
        conexion,
        _archivo(CORRECTO),
        nombre_archivo=CORRECTO,
        seccion_id=ajena,
        usuario_id=_usuario_id(revision),
        configuracion=CONFIGURACION,
    )

    assert (resultado.resultado, resultado.codigo_http, resultado.mensaje) == (
        "SECCION_INEXISTENTE",
        404,
        "La sección no existe.",
    )
    _sin_rastro(revision, antes)


def test_br_carga_01_un_conjunto_de_reglas_que_la_base_no_conoce_detiene_la_carga(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    antes = _conteos(revision)
    with pytest.raises(modulo_carga.ConfiguracionInvalida, match="R-NO-EXISTE"):
        _subir(conexion, revision, _archivo(CORRECTO), CORRECTO, configuracion=modulo_carga.Configuracion("R-NO-EXISTE"))
    _sin_rastro(revision, antes)


# US-09 y US-07, el archivo ya registrado y la sección con carga publicada (BR-CARGA-03, BR-CARGA-09 y BR-CARGA-10)

MENSAJE_OTRA_SECCION = "Este archivo ya está publicado en otra sección. No se cargó."
MENSAJE_SECCION_CON_CARGA = "La sección 410 ya tiene una carga publicada. No se cargó el archivo."


def _guardado_de_nuevo(contenido: bytes) -> bytes:
    """El export abierto y guardado otra vez con openpyxl, con las mismas celdas y otros bytes, como hace Excel."""
    libro = load_workbook(io.BytesIO(contenido))
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


@pytest.mark.parametrize("otro_nombre", [CORRECTO, "copia de notas 410.xlsx"])
def test_br_carga_09_subir_otra_vez_el_export_publicado_devuelve_su_carga_y_no_cambia_nada(
    conexion: psycopg.Connection, revision: psycopg.Connection, otro_nombre: str
) -> None:
    publicada = _subir(conexion, revision, _archivo(CORRECTO), CORRECTO)
    antes = _conteos(revision)
    otra_vez = _subir(conexion, revision, _archivo(CORRECTO), otro_nombre)

    assert (otra_vez.resultado, otra_vez.codigo_http, otra_vez.mensaje) == ("YA_PUBLICADA", 200, None)
    assert otra_vez.carga_id == publicada.carga_id
    assert _conteos(revision) == antes
    # archivo_origen conserva el primer nombre, y la sección sigue con sus 33 mediciones.
    assert _valores(revision, "SELECT nombre_archivo FROM abet.archivo_origen") == [(CORRECTO,)]
    assert _uno(revision, "SELECT count(*) FROM abet.v_tabla_maestra_pi WHERE \"SECCIÓN\" = '410'") == 33


def test_br_carga_03_09_un_archivo_publicado_en_otra_seccion_se_detiene_sin_datos_de_esa_seccion(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    publicada = _subir(conexion, revision, _archivo(CORRECTO), CORRECTO)
    antes = _conteos(revision)
    # La hoja declara la 410, así que el 409 prueba que la huella se busca antes que el cotejo de la sección.
    en_la_411 = _subir(conexion, revision, _archivo(CORRECTO), "notas 411.xlsx", seccion="411", correo=DOCENTE_411)

    assert (en_la_411.resultado, en_la_411.codigo_http, en_la_411.mensaje) == ("EN_OTRA_SECCION", 409, MENSAJE_OTRA_SECCION)
    assert en_la_411.carga_id is None
    huella = hashlib.sha256(_archivo(CORRECTO)).hexdigest()
    assert not {str(publicada.carga_id), huella, "410"} & set(re.findall(r"[0-9a-f]+", en_la_411.mensaje))
    assert _conteos(revision) == antes
    assert _uno(revision, "SELECT count(*) FROM abet.carga WHERE seccion_id = %s", _seccion_id(revision, "411")) == 0
    assert _cuentas(revision, publicada.carga_id) == ("PUBLICADA", 11, 11, 0, 11, 33)


def test_br_carga_09_un_archivo_rechazado_en_una_seccion_se_publica_despues_en_la_suya(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    contenido = _archivo(EXPORT_411)
    rechazada = _subir(conexion, revision, contenido, EXPORT_411)
    publicada = _subir(conexion, revision, contenido, EXPORT_411, seccion="411", correo=DOCENTE_411)

    assert (rechazada.resultado, publicada.resultado, publicada.codigo_http) == ("RECHAZADA", "PUBLICADA", 201)
    archivos = _valores(revision, "SELECT DISTINCT archivo_id FROM abet.carga")
    assert len(archivos) == 1 and _uno(revision, "SELECT count(*) FROM abet.archivo_origen") == 1
    subida_por = _uno(revision, "SELECT subida_por FROM abet.carga WHERE carga_id = %s", publicada.carga_id)
    assert subida_por == _usuario_id(revision, DOCENTE_411)
    assert _cuentas(revision, publicada.carga_id) == ("PUBLICADA", 11, 11, 0, 11, 33)
    assert _controles_con_filas(revision) == {}


@pytest.mark.parametrize("otro", ["export_con_error", "guardado_de_nuevo"])
def test_br_carga_10_otro_archivo_no_entra_en_una_seccion_que_ya_tiene_carga_publicada(
    conexion: psycopg.Connection, revision: psycopg.Connection, otro: str
) -> None:
    publicada = _subir(conexion, revision, _archivo(CORRECTO), CORRECTO)
    if otro == "export_con_error":
        contenido = _archivo(CON_ERROR)
    else:
        contenido = _guardado_de_nuevo(_archivo(CORRECTO))
        assert hashlib.sha256(contenido).hexdigest() != hashlib.sha256(_archivo(CORRECTO)).hexdigest()
    antes = _conteos(revision)
    resultado = _subir(conexion, revision, contenido, CON_ERROR)

    assert (resultado.resultado, resultado.codigo_http, resultado.mensaje) == (
        "SECCION_CON_CARGA",
        409,
        MENSAJE_SECCION_CON_CARGA,
    )
    assert resultado.carga_id is None
    assert _conteos(revision) == antes
    assert _cuentas(revision, publicada.carga_id) == ("PUBLICADA", 11, 11, 0, 11, 33)


def test_br_carga_03_la_seccion_con_carga_publicada_se_revisa_antes_que_la_seccion_sin_declarar(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    _subir(conexion, revision, _archivo(CORRECTO), CORRECTO)
    resultado = _subir(conexion, revision, _archivo("hoja1_sin_seccion.xlsx"), "notas.xlsx")

    assert (resultado.resultado, resultado.codigo_http) == ("SECCION_CON_CARGA", 409)


def test_br_carga_09_11_el_archivo_reutilizado_se_coteja_con_el_nombre_que_ya_tiene_registrado(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    contenido = _archivo("hoja1_sin_seccion.xlsx")
    primero = "gc_SINTETICO_20262_450002_411_fullgc_2026-10-20.xlsx"
    rechazada = _subir(conexion, revision, contenido, primero)
    # Los mismos bytes con un nombre que declara la 410 siguen siendo el archivo registrado con el nombre
    # que declara la 411, así que la constancia leída después dice lo mismo que esta respuesta (BR-R17-10).
    otra_vez = _subir(conexion, revision, contenido, "gc_SINTETICO_20262_450002_410_fullgc_2026-10-20.xlsx")

    assert (rechazada.resultado, otra_vez.resultado) == ("RECHAZADA", "RECHAZADA")
    assert otra_vez.mensaje == "El archivo corresponde a la sección 411 y usted eligió la 410. No se publicó."
    assert _valores(revision, "SELECT nombre_archivo FROM abet.archivo_origen") == [(primero,)]
    assert _uno(revision, "SELECT count(DISTINCT archivo_id) FROM abet.carga") == 1
    assert _controles_con_filas(revision) == {}


# US-07, una sola transacción ante fallas provocadas (BR-CARGA-02 y BR-CARGA-16)

MENSAJE_FALLA = "La carga no se completó y no se guardó ningún dato. Intente de nuevo."

# El dueño de la base instala el corte en la copia de la prueba. La función corre con los permisos de
# su dueño (SECURITY DEFINER), así que también corta la sesión del rol de la aplicación, que no puede
# terminar procesos del servidor. Con un argumento, corta solo cuando la carga ya tiene esa cantidad de
# filas en la tabla del disparador. pg_sleep() espera a que el proceso atienda la orden de terminar.
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


def _falla(resultado: Any) -> None:
    assert (resultado.resultado, resultado.codigo_http, resultado.mensaje, resultado.carga_id) == (
        "FALLA",
        500,
        MENSAJE_FALLA,
        None,
    )


@pytest.mark.parametrize("punto", list(PUNTOS_DE_CORTE))
def test_br_carga_02_un_corte_de_la_conexion_en_cualquier_punto_no_deja_nada_escrito(
    conexion: psycopg.Connection, revision: psycopg.Connection, punto: str
) -> None:
    revision.execute(CORTE)
    revision.execute(f"CREATE TRIGGER corte_de_prueba {PUNTOS_DE_CORTE[punto]}")
    antes = _conteos(revision)
    resultado = _subir(conexion, revision, _archivo(CORRECTO), CORRECTO)

    _falla(resultado)
    assert conexion.closed
    assert _conteos(revision) == antes == VACIAS
    assert _uno(revision, "SELECT count(*) FROM abet.carga WHERE estado = 'EN_CURSO'") == 0


def _validar_con_defecto(monkeypatch: pytest.MonkeyPatch, defecto: Any) -> None:
    """Reemplaza la validación que usa cargar() por una con un defecto inyectado del programa."""
    validar_de_verdad = modulo_carga.validar
    monkeypatch.setattr(modulo_carga, "validar", lambda libro, contexto: defecto(validar_de_verdad(libro, contexto)))


def _nivel_5_en_la_ultima_medicion(validacion: Any) -> Any:
    *primeras, ultima = validacion.filas_aceptadas
    *mediciones, medicion = ultima.mediciones
    ultima = replace(ultima, mediciones=(*mediciones, replace(medicion, nivel=5)))
    return replace(validacion, filas_aceptadas=(*primeras, ultima))


def test_br_carga_02_una_restriccion_violada_al_final_deshace_la_carga_entera(
    conexion: psycopg.Connection, revision: psycopg.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    _validar_con_defecto(monkeypatch, _nivel_5_en_la_ultima_medicion)
    antes = _conteos(revision)
    resultado = _subir(conexion, revision, _archivo(CORRECTO), CORRECTO)

    _falla(resultado)
    # Para el registro de la aplicación quedan el SQLSTATE y la restricción, nunca el DETAIL con la fila.
    assert (resultado.sqlstate, resultado.restriccion) == ("23514", "ck_medicion_nivel")
    assert "Failing row" not in repr(resultado) and "DETAIL" not in repr(resultado)
    assert _conteos(revision) == antes
    assert _uno(revision, "SELECT count(*) FROM abet.carga WHERE seccion_id = %s", _seccion_id(revision)) == 0


def test_br_carga_16_unas_cuentas_que_no_cuadran_chocan_con_ck_carga_filas_y_no_dejan_nada(
    conexion: psycopg.Connection, revision: psycopg.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    _validar_con_defecto(monkeypatch, lambda validacion: replace(validacion, rechazos_de_fila=()))
    antes = _conteos(revision)
    resultado = _subir(conexion, revision, _archivo(CON_ERROR), CORRECTO)

    _falla(resultado)
    assert (resultado.sqlstate, resultado.restriccion) == ("23514", "ck_carga_filas")
    assert _conteos(revision) == antes


def test_br_carga_02_una_conexion_con_una_transaccion_abierta_no_carga(
    base: Any, modo: str, revision: psycopg.Connection
) -> None:
    conexion = _conectar(base, modo)
    conexion.autocommit = False
    conexion.execute("SELECT 1")
    antes = _conteos(revision)
    try:
        # cargar() abre y confirma su propia transacción, y dentro de otra quedaría sin confirmar.
        with pytest.raises(ValueError, match="transacción abierta"):
            _subir(conexion, revision, _archivo(CORRECTO), CORRECTO)
    finally:
        conexion.rollback()
        conexion.close()
    assert _conteos(revision) == antes


def test_br_carga_02_la_carga_confirma_su_transaccion_con_autocommit_apagado(
    base: Any, modo: str, revision: psycopg.Connection
) -> None:
    conexion = _conectar(base, modo)
    conexion.autocommit = False
    try:
        resultado = _subir(conexion, revision, _archivo(CORRECTO), CORRECTO)
        assert conexion.info.transaction_status == psycopg.pq.TransactionStatus.IDLE
    finally:
        conexion.close()
    # Otra conexión ve la carga publicada, así que la transacción quedó confirmada.
    assert _cuentas(revision, resultado.carga_id) == ("PUBLICADA", 11, 11, 0, 11, 33)


def test_br_carga_02_la_carga_no_prepara_sentencias_aunque_la_conexion_lo_pida(
    base: Any, modo: str, revision: psycopg.Connection
) -> None:
    conexion = _conectar(base, modo)
    # Con 0, psycopg prepara cada sentencia, y el agrupador de conexiones de Neon no las admite.
    conexion.prepare_threshold = 0
    try:
        resultado = _subir(conexion, revision, _archivo(CORRECTO), CORRECTO)
        assert resultado.resultado == "PUBLICADA"
        assert conexion.prepare_threshold is None
        assert _uno(conexion, "SELECT count(*) FROM pg_prepared_statements") == 0
    finally:
        conexion.close()


def test_br_carga_07_la_guardia_de_la_base_rechaza_un_codigo_que_no_es_inventado_aunque_el_programa_falle(
    crear_base_demo: Any, modo: str, generador: ModuleType, tmp_path: Path
) -> None:
    base = crear_base_demo(guardia=True)
    contenido = generador.escribir_export_guardia(tmp_path / "guardia.xlsx").read_bytes()
    with psycopg.connect(base.conexion, autocommit=True) as revision:
        conexion = _conectar(base, modo)
        try:
            antes = _conteos(revision)
            resultado = _subir(conexion, revision, contenido, CORRECTO, configuracion=SIN_GUARDIA)
        finally:
            conexion.close()
        _falla(resultado)
        assert (resultado.sqlstate, resultado.restriccion) == ("23514", "ck_estudiante_codigo_inventado")
        # El DETAIL de esa violación repite el código, y el resultado no lo trae.
        assert str(generador.CODIGO_GUARDIA) not in repr(resultado)
        assert _conteos(revision) == antes


# US-07 y US-09, dos subidas a la vez (BR-CARGA-09 y BR-CARGA-10)

# La barrera detiene cada transacción en el punto del disparador mientras la prueba tiene el candado
# consultivo (advisory lock) 4242, así que las dos subidas buscan la huella y la carga publicada de la
# sección antes de que alguna confirme. La que llega segunda choca con un índice único.
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


def _subir_en_hilo(base: Any, modo: str, contenido: bytes, nombre: str, seccion_id: int, usuario_id: int) -> Any:
    opciones = f"-c lock_timeout=30s -c application_name={APLICACION_CONCURRENTE}"
    conexion = _conectar(base, modo, options=opciones)
    try:
        return modulo_carga.cargar(
            conexion,
            contenido,
            nombre_archivo=nombre,
            seccion_id=seccion_id,
            usuario_id=usuario_id,
            configuracion=CONFIGURACION,
        )
    finally:
        conexion.close()


def _esperar_bloqueadas(control: psycopg.Connection, cuantas: int) -> None:
    """Espera a que las subidas esperen un candado, en la barrera o tras la otra subida."""
    limite = time.monotonic() + 30
    consulta = (
        "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
        " AND application_name = %s AND wait_event_type = 'Lock'"
    )
    while _uno(control, consulta, APLICACION_CONCURRENTE) < cuantas:
        assert time.monotonic() < limite, "las subidas no llegaron a la barrera"
        time.sleep(0.05)


@pytest.mark.parametrize(
    ("segundo", "punto", "esperados"),
    [
        (
            "export_inventado_410_con_error.xlsx",
            "BEFORE UPDATE ON abet.carga FOR EACH ROW WHEN (NEW.estado = 'PUBLICADA')",
            ["PUBLICADA", "SECCION_CON_CARGA"],
        ),
        (CORRECTO, "BEFORE INSERT ON abet.archivo_origen FOR EACH ROW", ["PUBLICADA", "YA_PUBLICADA"]),
    ],
)
def test_br_carga_09_10_dos_subidas_a_la_vez_dejan_una_sola_carga_publicada(
    base: Any, modo: str, revision: psycopg.Connection, segundo: str, punto: str, esperados: list[str]
) -> None:
    revision.execute(BARRERA)
    revision.execute(f"CREATE TRIGGER barrera_de_prueba {punto} EXECUTE FUNCTION public.esperar_barrera()")
    seccion_id, usuario_id = _seccion_id(revision), _usuario_id(revision)
    with psycopg.connect(base.conexion, autocommit=True) as control, ThreadPoolExecutor(max_workers=2) as hilos:
        control.execute("SELECT pg_advisory_lock(4242)")
        futuros = [
            hilos.submit(_subir_en_hilo, base, modo, _archivo(nombre), nombre, seccion_id, usuario_id)
            for nombre in (CORRECTO, segundo)
        ]
        _esperar_bloqueadas(control, 2)
        control.execute("SELECT pg_advisory_unlock(4242)")
        resultados = [futuro.result(timeout=60) for futuro in futuros]

    assert sorted(resultado.resultado for resultado in resultados) == esperados
    publicada = next(resultado for resultado in resultados if resultado.resultado == "PUBLICADA")
    perdedora = next(resultado for resultado in resultados if resultado.resultado != "PUBLICADA")
    assert perdedora.codigo_http == {"SECCION_CON_CARGA": 409, "YA_PUBLICADA": 200}[perdedora.resultado]
    assert perdedora.carga_id == (publicada.carga_id if perdedora.resultado == "YA_PUBLICADA" else None)
    assert _valores(revision, "SELECT estado, count(*) FROM abet.carga GROUP BY estado") == [("PUBLICADA", 1)]
    assert _uno(revision, "SELECT count(*) FROM abet.archivo_origen") == 1
    assert _cuentas(revision, publicada.carga_id)[0] == "PUBLICADA"
    assert _controles_con_filas(revision) == {}


# US-14, el nombre del archivo y lo que la carga no guarda (BR-CARGA-06 y BR-CARGA-17)

@pytest.mark.parametrize(
    ("enviado", "guardado"),
    [
        (
            "C:\\Users\\docente\\Descargas\\export_inventado_410_con_error.xlsx",
            "export_inventado_410_con_error.xlsx",
        ),
        ("/home/docente/export_inventado_410_con_error.xlsx", "export_inventado_410_con_error.xlsx"),
        # archivo_origen.nombre_archivo es varchar(255), y la carga lo respeta antes de llegar a la base.
        ("notas_" + "x" * 300 + ".xlsx", ("notas_" + "x" * 300 + ".xlsx")[:255]),
    ],
)
def test_br_carga_17_el_nombre_del_archivo_se_guarda_sin_ruta_y_dentro_de_su_ancho(
    conexion: psycopg.Connection, revision: psycopg.Connection, enviado: str, guardado: str
) -> None:
    resultado = _subir(conexion, revision, _archivo(CON_ERROR), enviado)

    assert (resultado.resultado, resultado.codigo_http) == ("PUBLICADA", 201)
    assert _valores(revision, "SELECT nombre_archivo FROM abet.archivo_origen") == [(guardado,)]


def _textos_del_export(contenido: bytes, columnas: tuple[str, ...]) -> set[str]:
    """Valores de las columnas dadas del export, leídos aparte con openpyxl solo para buscarlos en la base."""
    libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    try:
        filas = list(libro.worksheets[0].iter_rows(values_only=True))
    finally:
        libro.close()
    posiciones = [filas[0].index(columna) for columna in columnas]
    return {str(fila[p]) for fila in filas[1:] for p in posiciones if fila[p] is not None}


def _coincidencias(revision: psycopg.Connection, textos: set[str]) -> dict[str, int]:
    """Filas de cada columna de texto de abet y acceso que contienen alguno de los textos."""
    columnas = _valores(
        revision,
        "SELECT table_schema, table_name, column_name FROM information_schema.columns"
        " JOIN information_schema.tables USING (table_catalog, table_schema, table_name)"
        " WHERE table_schema IN ('abet', 'acceso') AND table_type = 'BASE TABLE'"
        " AND data_type IN ('character varying', 'character', 'text')",
    )
    cuentas = {}
    for esquema, tabla, columna in columnas:
        consulta = sql.SQL(
            "SELECT count(*) FROM {}.{} WHERE EXISTS (SELECT 1 FROM unnest(%s::text[]) AS t (texto)"
            " WHERE strpos({}::text, t.texto) > 0)"
        ).format(sql.Identifier(esquema), sql.Identifier(tabla), sql.Identifier(columna))
        cuentas[f"{esquema}.{tabla}.{columna}"] = _uno(revision, consulta.as_string(revision), sorted(textos))
    return cuentas


def test_br_carga_17_los_nombres_y_las_columnas_que_no_son_pi_no_llegan_a_ninguna_tabla(
    conexion: psycopg.Connection, revision: psycopg.Connection
) -> None:
    contenido = _archivo(CON_ERROR)
    textos = _textos_del_export(contenido, ("Last Name", "First Name", "Last Access", "Availability"))
    textos |= {"Last Access", "Availability", *(f"Actividad {numero:02d}" for numero in range(1, 19))}
    antes = _coincidencias(revision, textos)
    resultado = _subir(conexion, revision, contenido, CON_ERROR)

    assert resultado.resultado == "PUBLICADA"
    # La carga no suma ninguna coincidencia, ni en sus siete tablas ni en las demás de abet y acceso.
    assert _coincidencias(revision, textos) == antes
    assert {columna: n for columna, n in antes.items() if columna.split(".")[1] in TABLAS and n} == {}
    assert _uno(revision, "SELECT count(*) FROM abet.estudiante WHERE codigo !~ '^99[0-9]{6}$'") == 0
    assert _uno(
        revision,
        "SELECT count(*) FROM information_schema.columns"
        " WHERE table_schema IN ('abet', 'acceso') AND data_type = 'bytea'",
    ) == 0
    # rechazo_fila no tiene dónde guardar el valor leído de una celda.
    assert _valores(
        revision,
        "SELECT column_name FROM information_schema.columns"
        " WHERE table_schema = 'abet' AND table_name = 'rechazo_fila' ORDER BY ordinal_position",
    ) == [(c,) for c in ("rechazo_id", "carga_id", "fila_origen", "carga_columna_id", "motivo", "efecto", "pi_id")]
    assert not {"valor", "valor_leido"} & {campo.name for campo in fields(resultado)}


# Mensajes de una carga rechazada, que la constancia arma después desde la base (BR-CARGA-13 y BR-CARGA-16)

CONTEXTO_410 = ContextoSeccion(periodo="2026-2", curso_codigo="450002", seccion_codigo="410", plan=(PiDelPlan(1, "5.1"),))


def test_br_carga_16_sin_rechazo_de_carga_el_mensaje_es_el_de_ninguna_fila_aceptada() -> None:
    assert modulo_carga.mensaje_de_carga_rechazada(None, CONTEXTO_410, None) == (
        "Ninguna fila se pudo aceptar. La carga no se publicó."
    )


@pytest.mark.parametrize("motivo", [Motivo.SECCION_NO_COINCIDE, Motivo.PERIODO_NO_COINCIDE])
def test_br_carga_11_12_sin_la_seccion_declarada_no_hay_mensaje_de_otra_seccion_ni_de_otro_periodo(
    motivo: Motivo,
) -> None:
    with pytest.raises(ValueError, match="sección que declara el archivo"):
        modulo_carga.mensaje_de_carga_rechazada(Rechazo(motivo, Efecto.RECHAZA_CARGA), CONTEXTO_410, None)
