"""Demo del corte 1 de punta a punta con la biblioteca, el camino que recorre scripts/demo_corte1.sh.

El profesor de la 410 de 450002 carga export_inventado_410_con_error.xlsx en 2026-2 con el rol de la
aplicación, lo vuelve a cargar y obtiene el R-17 y la constancia. Las pruebas nombran las reglas de
negocio (business rules, BR) de carga-export.spec.md y r17.spec.md que comprueban, con lo que debe
pasar y lo que no debe pasar (AGENTS.md, regla 8), y corren en bases desechables del clúster de
tests/conftest.py. La última revisa el guion sin correrlo, porque correrlo arma otro clúster.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import openpyxl
import psycopg
import pytest
from psycopg import sql

from abet_carga import constancia, r17
from abet_carga.carga import Configuracion, Resultado, cargar

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "tests" / "datos_inventados"
CON_ERROR = DATOS / "export_inventado_410_con_error.xlsx"
EXPORT_411 = DATOS / "export_inventado_411.xlsx"
GUION = RAIZ / "scripts" / "demo_corte1.sh"
CONTROLES = RAIZ / "db" / "plataforma" / "neon" / "controles_neon.sql"
HUELLA_CON_ERROR = "2b94db8d8abfd5ff24425584172de7942383c480f25ee0a8cacf927e17df2d15"
CONFIGURACION = Configuracion(conjunto_reglas="R-2026-BORRADOR")
FRANJA = ("R-17 PROVISIONAL. Las reglas de la carrera (conjunto R-2026-BORRADOR) aún no están aprobadas. "
          "No usar como evidencia oficial.")


@pytest.fixture
def conexion(base_demo: Any) -> Iterator[psycopg.Connection]:
    with psycopg.connect(base_demo.conexion, autocommit=True) as conexion:
        conexion.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(base_demo.rol_app)))
        yield conexion


def _id(conexion: psycopg.Connection, consulta: str, *parametros: object) -> int:
    fila = conexion.execute(consulta, parametros).fetchone()
    assert fila is not None
    return int(fila[0])


def _subir(conexion: psycopg.Connection, archivo: Path) -> Any:
    seccion_id = _id(conexion, "SELECT s.seccion_id FROM abet.seccion s JOIN abet.asignatura a USING (asignatura_id)"
                     " WHERE a.codigo = '450002' AND s.numero = '410'")
    usuario_id = _id(conexion, "SELECT usuario_id FROM acceso.usuario_autorizado WHERE correo = %s",
                     "docente410@example.invalid")
    return cargar(conexion, archivo.read_bytes(), nombre_archivo=archivo.name, seccion_id=seccion_id,
                  usuario_id=usuario_id, configuracion=CONFIGURACION)


def _controles_con_filas(base: Any) -> dict[str, int]:
    """Q01 a Q14 de controles_neon.sql con las filas que devuelve cada una, como en tests/test_carga.py."""
    texto = CONTROLES.read_text(encoding="utf-8")
    bloques = re.findall(r"\\echo '(Q[0-9]{2})\.[^\n]*\n(.*?);\n\\set q[0-9]{2} :ROW_COUNT", texto, flags=re.S)
    assert [nombre for nombre, _ in bloques] == [f"Q{numero:02d}" for numero in range(1, 15)]
    with psycopg.connect(base.conexion, autocommit=True) as revision:
        filas = {nombre: len(revision.execute(consulta.strip()).fetchall()) for nombre, consulta in bloques}
    return {nombre: cuantas for nombre, cuantas in filas.items() if cuantas}


def test_br_carga_09_16_la_410_con_error_se_publica_una_sola_vez_con_11_10_y_1(
    base_demo: Any, conexion: psycopg.Connection
) -> None:
    assert hashlib.sha256(CON_ERROR.read_bytes()).hexdigest() == HUELLA_CON_ERROR
    primera = _subir(conexion, CON_ERROR)
    assert (primera.resultado, primera.codigo_http) == (Resultado.PUBLICADA, 201)
    cuerpo = constancia.armar(conexion, primera.carga_id)
    assert (cuerpo["sha256"], cuerpo["filas_leidas"], cuerpo["filas_aceptadas"], cuerpo["filas_rechazadas"]) == (
        HUELLA_CON_ERROR, 11, 10, 1)
    assert [(r["fila"], r["pi"], r["motivo"]) for r in cuerpo["rechazos"]] == [(3, "5.2", "NIVEL_FUERA_DE_ESCALA")]
    segunda = _subir(conexion, CON_ERROR)
    assert (segunda.resultado, segunda.codigo_http, segunda.carga_id) == (Resultado.YA_PUBLICADA, 200,
                                                                         primera.carga_id)
    assert conexion.execute("SELECT count(*) FROM abet.carga").fetchone() == (1,)
    assert conexion.execute("SELECT count(*) FROM abet.medicion").fetchone() == (30,)
    assert _controles_con_filas(base_demo) == {}


def test_br_r17_01_05_el_r17_de_la_410_trae_nombre_franja_cifras_logotipo_y_constancia(
    conexion: psycopg.Connection, tmp_path: Path
) -> None:
    carga_id = _subir(conexion, CON_ERROR).carga_id
    ruta = r17.generar(conexion, carga_id, tmp_path)
    assert ruta.name == "R017_450002_410_2026-2_PROVISIONAL.xlsx"
    libro = openpyxl.load_workbook(ruta)
    hoja = libro[r17.HOJA]
    assert libro.sheetnames == [r17.HOJA, "Constancia"]
    assert hoja["B7"].value == FRANJA
    assert [hoja[f"B{fila}"].value for fila in (24, 25, 26)] == ["5.1", "5.2", "5.3"]
    assert [hoja[f"E{fila}"].value for fila in (24, 25, 26)] == pytest.approx([0.6, 0.6, 0.7])
    assert len(hoja._images) == 1 and not libro["Constancia"]._images
    valores = {str(c.value) for fila in libro["Constancia"].iter_rows() for c in fila if c.value is not None}
    assert HUELLA_CON_ERROR in valores


def test_br_r17_01_una_carga_rechazada_no_tiene_r17(conexion: psycopg.Connection, tmp_path: Path) -> None:
    rechazada = _subir(conexion, EXPORT_411)
    assert rechazada.resultado is Resultado.RECHAZADA
    with pytest.raises(r17.CargaNoPublicada):
        r17.generar(conexion, rechazada.carga_id, tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_br_carga_02_el_guion_de_la_demo_vive_en_un_cluster_desechable_y_nunca_en_el_de_la_mac() -> None:
    texto = GUION.read_text(encoding="utf-8")
    assert subprocess.run(["bash", "-n", str(GUION)], check=False).returncode == 0
    assert 'source "$RAIZ/db/pruebas/cluster_desechable.sh"' in texto
    assert "iniciar_cluster_desechable" in texto and "detener_cluster_desechable" in texto
    assert "trap " in texto
    assert "5432" not in texto and "localhost" not in texto
    assert "SET ROLE" in texto or "--rol" in texto


def test_br_carga_17_el_guion_no_versiona_rutas_de_una_sesion_ni_de_una_cuenta() -> None:
    # La carpeta de salida por omisión vale en cualquier máquina y no nombra a nadie.
    texto = GUION.read_text(encoding="utf-8")
    assert "/private/tmp/claude-" not in texto and "/Users/" not in texto
    assert 'SALIDA="${TMPDIR:-/tmp}/abet_demo_corte1"' in texto
