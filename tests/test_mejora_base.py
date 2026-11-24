"""Pruebas de V1_15 y de los permisos de abet_app sobre sus cuatro tablas (T021 de la spec 005, BR-MEJORA-03,
BR-MEJORA-06, BR-MEJORA-07, BR-MEJORA-09, BR-MEJORA-10 y BR-MEJORA-12).

V1_15 crea abet.mejora_borrador y abet.mejora_declaracion, cabeceras por carga, y abet.mejora_borrador_pi y
abet.mejora_declaracion_pi, hijas por PI con su clave foránea a abet.carga_columna por uq_carga_columna_pi (J-38).
La declaración guarda el tipo y la foto del semáforo, con un CHECK que ata el tipo al semáforo, y ninguna tabla tiene
columnas de estado, responsable ni plazo. Las causas y las acciones rechazan códigos de 8 dígitos y correos en la base
(US-53). db/plataforma/neon/crear_rol_app.sql da a abet_app el borrador por columnas exactas y solo el INSERT de la
declaración, sin DELETE.

Cada prueba que escribe lo hace en una transacción que se deshace, sobre una base desechable con la carga PUBLICADA
del export correcto de la 410 de 450002, en el clúster desechable de tests/cluster_desechable.py y nunca en
localhost:5432. Los textos son de prueba y los códigos, inventados.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import psycopg
import pytest
from psycopg import errors, sql

from abet_carga.carga import Configuracion, Resultado, cargar

RAIZ = Path(__file__).resolve().parent.parent
MIGRACION = RAIZ / "db" / "migration" / "V1_15__mejora_borrador_y_declaracion.sql"
ROL_APP = RAIZ / "db" / "plataforma" / "neon" / "crear_rol_app.sql"
EXPORT_410 = RAIZ / "tests" / "datos_inventados" / "sintetico_20262_450002_410.xlsx"
TABLAS = ("mejora_borrador", "mejora_borrador_pi", "mejora_declaracion", "mejora_declaracion_pi")
BLANCOS = [chr(punto) for punto in range(0x110000) if chr(punto).isspace()]
CAUSA = "La entrega coincidió con la semana de parciales."
ACCION = "Mover la entrega a la semana 10 y revisar el avance en clase."


@pytest.fixture(scope="module")
def base(base_desechable: ModuleType) -> Iterator[Any]:
    with base_desechable.abierta() as base:
        with psycopg.connect(base.conexion, autocommit=True) as conexion:
            conexion.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(base.rol_app)))
            seccion_id = conexion.execute(
                "SELECT s.seccion_id FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                " WHERE a.codigo = '450002' AND s.numero = '410'").fetchone()[0]
            usuario_id = conexion.execute("SELECT usuario_id FROM acceso.usuario_autorizado WHERE correo = %s",
                                          ("docente410@example.invalid",)).fetchone()[0]
            resultado = cargar(conexion, EXPORT_410.read_bytes(), nombre_archivo=EXPORT_410.name,
                               seccion_id=seccion_id, usuario_id=usuario_id,
                               configuracion=Configuracion(conjunto_reglas="R-2026-BORRADOR"))
            assert resultado.resultado == Resultado.PUBLICADA
        yield base


@pytest.fixture
def dueno(base: Any) -> Iterator[psycopg.Connection]:
    """Conexión del dueño en una transacción que se deshace al terminar, así que ninguna prueba deja filas."""
    with psycopg.connect(base.conexion) as conexion:
        yield conexion
        conexion.rollback()


@pytest.fixture
def app(base: Any) -> Iterator[psycopg.Connection]:
    """Conexión del rol de la aplicación en una transacción que se deshace al terminar."""
    with psycopg.connect(base.conexion_app) as conexion:
        yield conexion
        conexion.rollback()


def _ids(conexion: psycopg.Connection) -> tuple[int, int]:
    """carga_id de la 410 publicada y usuario_id de su profesor."""
    fila = conexion.execute(
        "SELECT c.carga_id, u.usuario_id FROM abet.carga c JOIN abet.seccion s ON s.seccion_id = c.seccion_id"
        " JOIN abet.asignatura a ON a.asignatura_id = s.asignatura_id, acceso.usuario_autorizado u"
        " WHERE a.codigo = '450002' AND s.numero = '410' AND c.estado = 'PUBLICADA'"
        " AND u.correo = 'docente410@example.invalid'").fetchone()
    assert fila is not None
    return fila[0], fila[1]


def _pi(conexion: psycopg.Connection, codigo: str) -> int:
    return conexion.execute("SELECT pi_id FROM abet.pi p JOIN abet.catalogo_version cv USING (catalogo_version_id)"
                            " WHERE p.codigo = %s AND cv.codigo = 'AMB-2026'", (codigo,)).fetchone()[0]


def _borrador(conexion: psycopg.Connection, causa: str | None = CAUSA, accion: str | None = ACCION,
              pi: str = "5.1") -> None:
    carga_id, usuario_id = _ids(conexion)
    conexion.execute("INSERT INTO abet.mejora_borrador (carga_id, version, actualizado_por) VALUES (%s, 1, %s)",
                     (carga_id, usuario_id))
    conexion.execute("INSERT INTO abet.mejora_borrador_pi (carga_id, pi_id, causa, accion) VALUES (%s, %s, %s, %s)",
                     (carga_id, _pi(conexion, pi), causa, accion))


def _declaracion(conexion: psycopg.Connection) -> int:
    carga_id, usuario_id = _ids(conexion)
    return conexion.execute(
        "INSERT INTO abet.mejora_declaracion (carga_id, version_borrador, declarada_por) VALUES (%s, 1, %s)"
        " RETURNING declaracion_id", (carga_id, usuario_id)).fetchone()[0]


def _fila_declarada(conexion: psycopg.Connection, declaracion_id: int, *, tipo: str = "OPORTUNIDAD_MEJORA",
                    semaforo: str | None = "ROJO", causa: str = CAUSA, accion: str = ACCION, pi: str = "5.1",
                    carga_id: int | None = None) -> None:
    carga_id = _ids(conexion)[0] if carga_id is None else carga_id
    conexion.execute(
        "INSERT INTO abet.mejora_declaracion_pi (declaracion_id, pi_id, carga_id, tipo, causa, accion, logro_pct,"
        " meta_pct, semaforo) VALUES (%s, %s, %s, %s, %s, %s, 63.6, 80.0, %s)",
        (declaracion_id, _pi(conexion, pi), carga_id, tipo, causa, accion, semaforo))


def _restriccion(falla: pytest.ExceptionInfo[psycopg.Error]) -> str | None:
    return falla.value.diag.constraint_name


# Forma de las cuatro tablas

def test_v1_15_crea_cuatro_tablas_y_ningun_otro_objeto() -> None:
    texto = MIGRACION.read_text(encoding="utf-8")
    sin_comentarios = re.sub(r"--[^\n]*", "", texto)
    sin_textos = re.sub(r"'[^']*'", "''", sin_comentarios)
    creadas = re.findall(r"CREATE\s+(\w+(?:\s+\w+)?)\s+([a-z_.]+)", sin_comentarios, flags=re.I)
    assert creadas == [("TABLE", f"abet.{tabla}") for tabla in TABLAS]
    assert not re.search(r"\b(ALTER|DROP|GRANT|REVOKE|INSERT|UPDATE|DELETE|FUNCTION|TRIGGER)\b", sin_textos, flags=re.I)


def test_br_mejora_07_las_tablas_no_tienen_estado_responsable_ni_plazo(base: Any) -> None:
    with psycopg.connect(base.conexion) as conexion:
        columnas = conexion.execute(
            "SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'abet'"
            " AND table_name = ANY(%s) ORDER BY table_name, ordinal_position", (list(TABLAS),)).fetchall()
    assert columnas == [
        ("mejora_borrador", "carga_id"), ("mejora_borrador", "version"), ("mejora_borrador", "actualizado_en"),
        ("mejora_borrador", "actualizado_por"),
        ("mejora_borrador_pi", "carga_id"), ("mejora_borrador_pi", "pi_id"), ("mejora_borrador_pi", "causa"),
        ("mejora_borrador_pi", "accion"),
        ("mejora_declaracion", "declaracion_id"), ("mejora_declaracion", "carga_id"),
        ("mejora_declaracion", "version_borrador"), ("mejora_declaracion", "declarada_en"),
        ("mejora_declaracion", "declarada_por"),
        ("mejora_declaracion_pi", "declaracion_id"), ("mejora_declaracion_pi", "pi_id"),
        ("mejora_declaracion_pi", "carga_id"), ("mejora_declaracion_pi", "tipo"), ("mejora_declaracion_pi", "causa"),
        ("mejora_declaracion_pi", "accion"), ("mejora_declaracion_pi", "logro_pct"),
        ("mejora_declaracion_pi", "meta_pct"), ("mejora_declaracion_pi", "semaforo"),
    ]
    assert not {c for _, c in columnas} & {"estado", "responsable", "plazo"}


def test_br_mejora_08_las_causas_y_las_acciones_son_varchar_800(base: Any) -> None:
    with psycopg.connect(base.conexion) as conexion:
        filas = conexion.execute(
            "SELECT table_name, column_name, character_maximum_length, is_nullable FROM information_schema.columns"
            " WHERE table_schema = 'abet' AND column_name IN ('causa', 'accion') ORDER BY table_name, column_name"
        ).fetchall()
    assert filas == [("mejora_borrador_pi", "accion", 800, "YES"), ("mejora_borrador_pi", "causa", 800, "YES"),
                     ("mejora_declaracion_pi", "accion", 800, "NO"), ("mejora_declaracion_pi", "causa", 800, "NO")]


# Lo que la base acepta

def test_br_mejora_09_la_base_guarda_un_borrador_y_una_declaracion_sanos(dueno: psycopg.Connection) -> None:
    _borrador(dueno, causa="Solo la causa.", accion=None)
    declaracion_id = _declaracion(dueno)
    _fila_declarada(dueno, declaracion_id, tipo="OPORTUNIDAD_MEJORA", semaforo="ROJO")
    _fila_declarada(dueno, declaracion_id, tipo="BUENA_PRACTICA", semaforo="VERDE", pi="5.2")
    _fila_declarada(dueno, declaracion_id, tipo="OPORTUNIDAD_MEJORA", semaforo="AMBAR", pi="5.3")
    assert dueno.execute("SELECT count(*) FROM abet.mejora_declaracion_pi").fetchone() == (3,)
    assert dueno.execute("SELECT version, actualizado_en IS NOT NULL FROM abet.mejora_borrador").fetchone() == (1, True)
    assert dueno.execute("SELECT declarada_en IS NOT NULL FROM abet.mejora_declaracion").fetchone() == (True,)


@pytest.mark.parametrize("tipo", ["OPORTUNIDAD_MEJORA", "BUENA_PRACTICA"])
def test_br_mejora_03_sin_foto_del_semaforo_la_base_acepta_cualquier_tipo(dueno: psycopg.Connection,
                                                                          tipo: str) -> None:
    _fila_declarada(dueno, _declaracion(dueno), tipo=tipo, semaforo=None)


@pytest.mark.parametrize("texto", ["Resolución 990000041 del periodo", "Entrega del 18/11/2026 en parciales",
                                   "Código 1234567 de siete cifras", "Correo en la clase @martes"])
def test_br_mejora_10_un_numero_que_no_es_un_codigo_se_acepta(dueno: psycopg.Connection, texto: str) -> None:
    _borrador(dueno, causa=texto, accion=texto)
    _fila_declarada(dueno, _declaracion(dueno), causa=texto, accion=texto)


def test_br_mejora_08_800_caracteres_caben_en_cada_campo(dueno: psycopg.Connection) -> None:
    _borrador(dueno, causa="á" * 800, accion="x" * 800)
    _fila_declarada(dueno, _declaracion(dueno), causa="á" * 800, accion="x" * 800)


# Lo que la base rechaza

def test_br_mejora_07_un_pi_que_la_carga_no_mide_falla_por_la_fk_a_carga_columna(dueno: psycopg.Connection) -> None:
    with pytest.raises(errors.ForeignKeyViolation) as falla:
        _borrador(dueno, pi="2.1")
    assert _restriccion(falla) == "fk_mejora_borrador_pi_columna"


def test_br_mejora_07_una_fila_declarada_de_un_pi_ajeno_falla_por_la_fk_a_carga_columna(
        dueno: psycopg.Connection) -> None:
    declaracion_id = _declaracion(dueno)
    with pytest.raises(errors.ForeignKeyViolation) as falla:
        _fila_declarada(dueno, declaracion_id, pi="2.1")
    assert _restriccion(falla) == "fk_mejora_declaracion_pi_columna"


def test_br_mejora_06_un_registro_del_borrador_sin_su_cabecera_falla(dueno: psycopg.Connection) -> None:
    carga_id, _ = _ids(dueno)
    with pytest.raises(errors.ForeignKeyViolation) as falla:
        dueno.execute("INSERT INTO abet.mejora_borrador_pi (carga_id, pi_id, causa) VALUES (%s, %s, 'Causa.')",
                      (carga_id, _pi(dueno, "5.1")))
    assert _restriccion(falla) == "fk_mejora_borrador_pi_borrador"


@pytest.mark.parametrize("version", [0, -1])
def test_br_mejora_06_el_borrador_guardado_empieza_en_la_version_1(dueno: psycopg.Connection, version: int) -> None:
    carga_id, usuario_id = _ids(dueno)
    with pytest.raises(errors.CheckViolation) as falla:
        dueno.execute("INSERT INTO abet.mejora_borrador (carga_id, version, actualizado_por) VALUES (%s, %s, %s)",
                      (carga_id, version, usuario_id))
    assert _restriccion(falla) == "ck_mejora_borrador_version"


def test_br_mejora_06_una_carga_tiene_un_solo_borrador(dueno: psycopg.Connection) -> None:
    _borrador(dueno)
    carga_id, usuario_id = _ids(dueno)
    with pytest.raises(errors.UniqueViolation) as falla:
        dueno.execute("INSERT INTO abet.mejora_borrador (carga_id, version, actualizado_por) VALUES (%s, 2, %s)",
                      (carga_id, usuario_id))
    assert _restriccion(falla) == "pk_mejora_borrador"


def test_br_mejora_09_una_fila_declarada_repite_la_carga_de_su_cabecera(dueno: psycopg.Connection) -> None:
    declaracion_id = _declaracion(dueno)
    with pytest.raises(errors.ForeignKeyViolation) as falla:
        _fila_declarada(dueno, declaracion_id, carga_id=_ids(dueno)[0] + 1000)
    assert _restriccion(falla) == "fk_mejora_declaracion_pi_cabecera"


@pytest.mark.parametrize(("tipo", "semaforo", "restriccion"), [
    ("BUENA_PRACTICA", "ROJO", "ck_mejora_declaracion_pi_coherencia"),
    ("BUENA_PRACTICA", "AMBAR", "ck_mejora_declaracion_pi_coherencia"),
    ("OPORTUNIDAD_MEJORA", "VERDE", "ck_mejora_declaracion_pi_coherencia"),
    ("OM", "ROJO", "ck_mejora_declaracion_pi_tipo"),
    ("OPORTUNIDAD_MEJORA", "AZUL", "ck_mejora_declaracion_pi_semaforo"),
])
def test_br_mejora_03_la_base_ata_el_tipo_al_semaforo(dueno: psycopg.Connection, tipo: str, semaforo: str,
                                                       restriccion: str) -> None:
    declaracion_id = _declaracion(dueno)
    with pytest.raises(errors.CheckViolation) as falla:
        _fila_declarada(dueno, declaracion_id, tipo=tipo, semaforo=semaforo)
    assert _restriccion(falla) == restriccion


@pytest.mark.parametrize("campo", ["causa", "accion"])
@pytest.mark.parametrize("texto", ["", "   ", *BLANCOS], ids=["vacio", "tres_espacios",
                                                              *[f"U+{ord(b):04X}" for b in BLANCOS]])
def test_br_mejora_09_la_declaracion_rechaza_un_campo_en_blanco(dueno: psycopg.Connection, campo: str,
                                                                 texto: str) -> None:
    declaracion_id = _declaracion(dueno)
    with pytest.raises(errors.CheckViolation) as falla:
        _fila_declarada(dueno, declaracion_id, **{campo: texto})
    assert _restriccion(falla) == "ck_mejora_declaracion_pi_texto"


def test_br_mejora_06_el_borrador_admite_un_campo_en_blanco_o_nulo(dueno: psycopg.Connection) -> None:
    _borrador(dueno, causa="   ", accion=None)


@pytest.mark.parametrize("campo", ["causa", "accion"])
def test_br_mejora_09_la_declaracion_no_admite_un_campo_nulo(dueno: psycopg.Connection, campo: str) -> None:
    declaracion_id = _declaracion(dueno)
    with pytest.raises(errors.NotNullViolation):
        _fila_declarada(dueno, declaracion_id, **{campo: None})


@pytest.mark.parametrize("texto", ["99000004 no entregó", "El 99000004 no entregó", "código:99000004.",
                                   "escribir a alguien@example.invalid", "ALGUIEN@EXAMPLE.INVALID avisa"])
@pytest.mark.parametrize("campo", ["causa", "accion"])
def test_br_mejora_10_el_borrador_rechaza_un_codigo_o_un_correo(dueno: psycopg.Connection, campo: str,
                                                                 texto: str) -> None:
    with pytest.raises(errors.CheckViolation) as falla:
        _borrador(dueno, **{campo: texto})
    assert _restriccion(falla) == "ck_mejora_borrador_pi_sin_codigos"


@pytest.mark.parametrize("texto", ["99000004 no entregó", "escribir a alguien@example.invalid"])
@pytest.mark.parametrize("campo", ["causa", "accion"])
def test_br_mejora_10_la_declaracion_rechaza_un_codigo_o_un_correo(dueno: psycopg.Connection, campo: str,
                                                                    texto: str) -> None:
    declaracion_id = _declaracion(dueno)
    with pytest.raises(errors.CheckViolation) as falla:
        _fila_declarada(dueno, declaracion_id, **{campo: texto})
    assert _restriccion(falla) == "ck_mejora_declaracion_pi_sin_codigos"


def test_br_mejora_10_los_dos_checks_usan_el_mismo_patron(base: Any) -> None:
    with psycopg.connect(base.conexion) as conexion:
        definiciones = dict(conexion.execute(
            "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conname IN"
            " ('ck_mejora_borrador_pi_sin_codigos', 'ck_mejora_declaracion_pi_sin_codigos')").fetchall())
    patrones = {nombre: set(re.findall(r"'([^']*)'::text", definicion)) for nombre, definicion in definiciones.items()}
    assert len(patrones) == 2
    assert patrones["ck_mejora_borrador_pi_sin_codigos"] == patrones["ck_mejora_declaracion_pi_sin_codigos"]
    assert len(patrones["ck_mejora_borrador_pi_sin_codigos"]) == 1


@pytest.mark.parametrize("campo", ["causa", "accion"])
def test_br_mejora_08_801_caracteres_no_caben(dueno: psycopg.Connection, campo: str) -> None:
    with pytest.raises(errors.StringDataRightTruncation):
        _borrador(dueno, **{campo: "x" * 801})


# Permisos de abet_app (BR-MEJORA-12)

def test_br_mejora_12_abet_app_inserta_la_declaracion_y_no_la_cambia_ni_borra(base: Any) -> None:
    with psycopg.connect(base.conexion) as conexion:
        privilegios = {
            tabla: [p for p in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE", "REFERENCES", "TRIGGER")
                    if conexion.execute("SELECT has_table_privilege(%s, %s, %s)",
                                        (base.rol_app, f"abet.{tabla}", p)).fetchone()[0]]
            for tabla in TABLAS}
    assert privilegios == {"mejora_borrador": ["SELECT"], "mejora_borrador_pi": ["SELECT"],
                           "mejora_declaracion": ["SELECT", "INSERT"], "mejora_declaracion_pi": ["SELECT", "INSERT"]}


def test_br_mejora_12_abet_app_escribe_el_borrador_por_columnas_exactas(base: Any) -> None:
    with psycopg.connect(base.conexion) as conexion:
        por_columna = conexion.execute(
            "SELECT c.relname, a.attname, has_column_privilege(%s, c.oid, a.attnum, 'INSERT'),"
            " has_column_privilege(%s, c.oid, a.attnum, 'UPDATE') FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid"
            " JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'abet' AND c.relname IN"
            " ('mejora_borrador', 'mejora_borrador_pi') AND a.attnum > 0 AND NOT a.attisdropped ORDER BY c.relname, a.attnum",
            (base.rol_app, base.rol_app)).fetchall()
    assert por_columna == [
        ("mejora_borrador", "carga_id", True, False), ("mejora_borrador", "version", True, True),
        ("mejora_borrador", "actualizado_en", False, True), ("mejora_borrador", "actualizado_por", True, True),
        ("mejora_borrador_pi", "carga_id", True, False), ("mejora_borrador_pi", "pi_id", True, False),
        ("mejora_borrador_pi", "causa", True, True), ("mejora_borrador_pi", "accion", True, True),
    ]


def test_br_mejora_12_abet_app_guarda_borrador_y_declaracion_como_la_ruta(app: psycopg.Connection) -> None:
    _borrador(app, causa="   ", accion=None)
    carga_id, usuario_id = _ids(app)
    app.execute("UPDATE abet.mejora_borrador SET version = version + 1, actualizado_en = now(), actualizado_por = %s"
                " WHERE carga_id = %s", (usuario_id, carga_id))
    app.execute("UPDATE abet.mejora_borrador_pi SET causa = %s, accion = %s WHERE carga_id = %s", (CAUSA, ACCION,
                                                                                                  carga_id))
    _fila_declarada(app, _declaracion(app))
    assert app.execute("SELECT version FROM abet.mejora_borrador").fetchone() == (2,)


@pytest.mark.parametrize("sentencia", [
    "DELETE FROM abet.mejora_borrador_pi",
    "DELETE FROM abet.mejora_borrador",
    "DELETE FROM abet.mejora_declaracion_pi",
    "DELETE FROM abet.mejora_declaracion",
    "TRUNCATE abet.mejora_declaracion_pi",
    "UPDATE abet.mejora_declaracion_pi SET causa = 'Otra causa.'",
    "UPDATE abet.mejora_declaracion SET declarada_en = now()",
    "UPDATE abet.mejora_borrador_pi SET pi_id = pi_id",
    "UPDATE abet.mejora_borrador SET carga_id = carga_id",
    "INSERT INTO abet.mejora_borrador (carga_id, version, actualizado_en, actualizado_por)"
    " SELECT carga_id, 1, now() - interval '1 day', 1 FROM abet.carga",
])
def test_br_mejora_12_abet_app_no_borra_ni_corrige(app: psycopg.Connection, sentencia: str) -> None:
    with pytest.raises(errors.InsufficientPrivilege):
        app.execute(sentencia)


def test_br_mejora_12_crear_rol_app_sigue_sirviendo_antes_de_v1_15(base_desechable: ModuleType) -> None:
    with base_desechable.abierta(hasta=(1, 14)) as anterior, psycopg.connect(anterior.conexion) as conexion:
        assert conexion.execute("SELECT to_regclass('abet.mejora_borrador')").fetchone() == (None,)
        assert conexion.execute("SELECT has_table_privilege(%s, 'abet.carga', 'INSERT')",
                                (anterior.rol_app,)).fetchone() == (True,)


@pytest.mark.parametrize(("permiso", "mensaje"), [
    ("GRANT UPDATE (causa) ON abet.mejora_declaracion_pi TO {rol}", "actualiza otras columnas"),
    ("GRANT INSERT (actualizado_en) ON abet.mejora_borrador TO {rol}", "inserta otras columnas"),
    ("GRANT DELETE ON abet.mejora_borrador_pi TO {rol}", "puede modificar o vaciar"),
    ("REVOKE SELECT ON abet.mejora_declaracion FROM {rol}", "no lee las cuatro tablas"),
])
def test_br_mejora_12_la_comprobacion_de_crear_rol_app_detiene_un_permiso_de_mas_o_de_menos(
        base_desechable: ModuleType, base: Any, tmp_path: Path, permiso: str, mensaje: str) -> None:
    texto = ROL_APP.read_text(encoding="utf-8")
    ancla = "-- Comprobación final."
    assert texto.count(ancla) == 1
    copia = tmp_path / "crear_rol_app_con_un_cambio.sql"
    copia.write_text(texto.replace(ancla, permiso.format(rol=base.rol_app) + ";\n" + ancla), encoding="utf-8")
    with pytest.raises(base_desechable.ErrorDeBase, match=mensaje):
        base_desechable._psql(base.nombre, "-v", f"rol_app={base.rol_app}", "-f", str(copia))
    # La transacción del archivo se deshace, así que el rol conserva los permisos exactos.
    with psycopg.connect(base.conexion) as conexion:
        assert conexion.execute("SELECT has_table_privilege(%s, 'abet.mejora_declaracion', 'SELECT'),"
                                " has_column_privilege(%s, 'abet.mejora_declaracion_pi', 'causa', 'UPDATE')",
                                (base.rol_app, base.rol_app)).fetchone() == (True, False)


# Q16 y Q17 de db/pruebas/pruebas.sql y db/plataforma/neon/controles_neon.sql (T039, BR-MEJORA-11)

CONTROLES = RAIZ / "db" / "plataforma" / "neon" / "controles_neon.sql"


def _consultas_de_control() -> dict[str, str]:
    texto = CONTROLES.read_text(encoding="utf-8")
    bloques = re.findall(r"\\echo '(Q[0-9]{2})\.[^\n]*\n(.*?);\n\\set q[0-9]{2} :ROW_COUNT", texto, flags=re.S)
    return {nombre: consulta.strip() for nombre, consulta in bloques}


def _declarar_410(conexion: psycopg.Connection, pis: tuple[str, ...] = ("5.1", "5.2", "5.3")) -> int:
    _borrador(conexion)
    declaracion_id = _declaracion(conexion)
    for pi in pis:
        _fila_declarada(conexion, declaracion_id, pi=pi)
    return declaracion_id


def test_br_mejora_11_controles_neon_trae_q16_y_q17() -> None:
    consultas = _consultas_de_control()
    assert sorted(consultas) == [f"Q{n:02d}" for n in (*range(1, 15), *range(16, 22))]
    assert "mejora_borrador_pi" in consultas["Q16"] and "mejora_declaracion_pi" in consultas["Q16"]
    assert "CALIFICADO" in consultas["Q17"] and "PUBLICADA" in consultas["Q17"]


def test_br_mejora_11_q16_usa_el_patron_de_los_checks(base: Any) -> None:
    with psycopg.connect(base.conexion) as conexion:
        definicion = conexion.execute("SELECT pg_get_constraintdef(oid) FROM pg_constraint"
                                      " WHERE conname = 'ck_mejora_borrador_pi_sin_codigos'").fetchone()[0]
    [patron] = set(re.findall(r"'([^']*)'::text", definicion))
    assert _consultas_de_control()["Q16"].count(f"'{patron}'") == 4


def test_br_mejora_11_q16_y_q17_dan_0_filas_con_una_declaracion_sana(dueno: psycopg.Connection) -> None:
    _declarar_410(dueno)
    consultas = _consultas_de_control()
    assert dueno.execute(consultas["Q16"]).fetchall() == []
    assert dueno.execute(consultas["Q17"]).fetchall() == []


def test_br_mejora_11_q17_ve_el_pi_con_calificados_que_falta_en_la_vigente(dueno: psycopg.Connection) -> None:
    _declarar_410(dueno, ("5.1", "5.2"))
    carga_id, _ = _ids(dueno)
    filas = dueno.execute(_consultas_de_control()["Q17"]).fetchall()
    assert filas == [(carga_id, "5.3")]
    assert all(CAUSA not in str(valor) and ACCION not in str(valor) for fila in filas for valor in fila)


def test_br_mejora_11_q17_mira_solo_la_declaracion_vigente(dueno: psycopg.Connection) -> None:
    # Una declaración anterior incompleta no cuenta si la vigente, la de mayor declaracion_id, está completa.
    declaracion_id = _declaracion(dueno)
    _borrador(dueno)
    _fila_declarada(dueno, declaracion_id, pi="5.1")
    vigente = _declaracion(dueno)
    for pi in ("5.1", "5.2", "5.3"):
        _fila_declarada(dueno, vigente, pi=pi)
    assert dueno.execute(_consultas_de_control()["Q17"]).fetchall() == []


def test_br_mejora_11_q17_no_mira_una_carga_que_no_esta_publicada(dueno: psycopg.Connection) -> None:
    _declarar_410(dueno, ("5.1",))
    carga_id, _ = _ids(dueno)
    dueno.execute("UPDATE abet.carga SET estado = 'RECHAZADA' WHERE carga_id = %s", (carga_id,))
    assert dueno.execute(_consultas_de_control()["Q17"]).fetchall() == []


def test_br_mejora_11_q17_no_pide_el_pi_sin_calificaciones(dueno: psycopg.Connection) -> None:
    _declarar_410(dueno, ("5.1", "5.2"))
    carga_id, _ = _ids(dueno)
    dueno.execute("UPDATE abet.medicion m SET estado_evidencia = 'SIN_EVIDENCIA', nivel_original = NULL FROM abet.pi p"
                  " WHERE p.pi_id = m.pi_id AND p.codigo = '5.3' AND m.carga_id = %s", (carga_id,))
    assert dueno.execute(_consultas_de_control()["Q17"]).fetchall() == []


@pytest.mark.parametrize("tabla", ["borrador", "declaracion"])
def test_br_mejora_11_q16_ve_un_codigo_que_salta_el_check(dueno: psycopg.Connection, tabla: str) -> None:
    dueno.execute(f"ALTER TABLE abet.mejora_{tabla}_pi DROP CONSTRAINT ck_mejora_{tabla}_pi_sin_codigos")
    declaracion_id = _declarar_410(dueno)
    if tabla == "borrador":
        dueno.execute("UPDATE abet.mejora_borrador_pi SET accion = '99000004 no entregó'")
    else:
        dueno.execute("UPDATE abet.mejora_declaracion_pi SET causa = 'escribir a alguien@example.invalid'"
                      " WHERE declaracion_id = %s AND pi_id = %s", (declaracion_id, _pi(dueno, "5.2")))
    filas = dueno.execute(_consultas_de_control()["Q16"]).fetchall()
    assert len(filas) == 1
    assert not any("99000004" in str(valor) or "@" in str(valor) for valor in filas[0])


def test_br_mejora_11_controles_neon_cierra_con_q16_a_q21_desde_v1_15(base_desechable: ModuleType,
                                                                     base: Any) -> None:
    salida = base_desechable._psql(base.nombre, "-f", str(CONTROLES))
    assert "RESULTADO: Q01 a Q14 y Q16 a Q21 devuelven 0 filas." in salida.splitlines()


def test_br_mejora_11_controles_neon_sigue_sirviendo_antes_de_v1_15(base_desechable: ModuleType) -> None:
    with base_desechable.abierta(hasta=(1, 14)) as anterior:
        salida = base_desechable._psql(anterior.nombre, "-f", str(CONTROLES))
    lineas = salida.splitlines()
    assert "RESULTADO: Q01 a Q14 y Q18 a Q21 devuelven 0 filas." in lineas
    assert "Q16 y Q17 esperan a V1_15 (spec 005), que esta base todavía no tiene." in lineas
