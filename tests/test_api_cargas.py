"""Pruebas de las rutas de cargas, constancia y R-17 de la API (T038).

Siguen los escenarios de carga.feature, r17_constancia.feature, acceso.feature y
varias_secciones.feature que pasan por la interfaz HTTP. Cada prueba nombra la regla de negocio
(business rule, BR) de specs/features/ que comprueba, con lo que debe pasar y lo que no debe pasar.
La biblioteca abet_carga ya tiene sus pruebas, así que estas comprueban el orden de la ruta, sus
códigos, sus cuerpos, sus cabeceras y lo que deja el registro de la aplicación. Las copias de un
export con cambios se arman en tmp_path con el generador y nunca se versionan.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import logging
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest
from openpyxl import load_workbook


def _modulo(nombre: str) -> ModuleType:
    """Módulo de tests/ cargado por su ruta, porque tests/ no es un paquete."""
    if nombre not in sys.modules:
        especificacion = importlib.util.spec_from_file_location(nombre, Path(__file__).with_name(f"{nombre}.py"))
        assert especificacion is not None and especificacion.loader is not None
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[nombre] = modulo
        especificacion.loader.exec_module(modulo)
    return sys.modules[nombre]


A = _modulo("api_de_prueba")
plantilla, base, api = A.plantilla, A.base, A.api
AJENA = {"detail": "La sección no está a su cargo."}
GUARDIA = ("El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. "
           "No se guardó nada.")
FALLA = "La carga no se completó y no se guardó ningún dato. Intente de nuevo."
RECHAZO_FILA_3 = {
    "fila": 3, "pi": "5.2", "motivo": "NIVEL_FUERA_DE_ESCALA", "efecto": "RECHAZA_FILA",
    "mensaje": "Fila 3, PI 5.2, nivel fuera de la escala 1 a 4. La fila completa queda fuera, también de 5.1 y 5.3.",
}
AVISO_5_3 = {
    "pi": "5.3", "motivo": "PUNTAJE_MAXIMO_DISTINTO", "efecto": "AVISO",
    "mensaje": "PI 5.3. La columna declara 20 puntos y sus notas están entre 1 y 4. Se cargó igual.",
}


def _guardia(generador: ModuleType, tmp_path: Path) -> bytes:
    return generador.escribir_export_guardia(tmp_path / "guardia.xlsx").read_bytes()


# BR-CARGA-15, BR-R17-10 y la confirmación de Jefferson del 2026-10-29 sobre los avisos de P4

def test_br_carga_15_el_export_con_error_responde_201_con_su_rechazo_y_su_aviso(api: object) -> None:
    respuesta = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), A.archivo(A.CON_ERROR), A.CON_ERROR)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert (cuerpo["estado"], cuerpo["filas_leidas"], cuerpo["filas_aceptadas"], cuerpo["filas_rechazadas"]) == (
        "PUBLICADA", 11, 10, 1)
    assert cuerpo["rechazos"] == [RECHAZO_FILA_3]
    assert cuerpo["avisos"] == [AVISO_5_3]
    assert cuerpo["subida_por"] == A.DOCENTE_410 and cuerpo["mensaje"] is None
    assert cuerpo["sha256"] == hashlib.sha256(A.archivo(A.CON_ERROR)).hexdigest()
    assert all("valor" not in r and "valor_leido" not in r for r in cuerpo["rechazos"] + cuerpo["avisos"])
    assert "9900000" not in respuesta.text and "Inventado" not in respuesta.text


def test_br_r17_10_la_constancia_leida_despues_es_igual_a_la_respuesta_201(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    subida = A.subir(cliente, api.seccion("410"), A.archivo(A.CON_ERROR), A.CON_ERROR).json()
    leida = cliente.get(f"/api/cargas/{subida['carga_id']}")
    assert leida.status_code == 200 and leida.json() == subida


def test_br_carga_13_una_carga_rechazada_por_estructura_responde_201_y_tiene_constancia(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    respuesta = A.subir(cliente, api.seccion("410"), A.archivo("sin_5_2_410.xlsx"), "sin_5_2_410.xlsx")
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    mensaje = "Falta la columna del PI 5.2 que el plan de medición pide para esta sección."
    assert (cuerpo["estado"], cuerpo["filas_leidas"], cuerpo["mensaje"]) == ("RECHAZADA", 0, mensaje)
    assert cuerpo["rechazos"] == [{"fila": None, "pi": "5.2", "motivo": "PI_DEL_PLAN_AUSENTE",
                                   "efecto": "RECHAZA_CARGA", "mensaje": mensaje}]
    assert cliente.get(f"/api/cargas/{cuerpo['carga_id']}").json() == cuerpo


def test_br_carga_11_el_nombre_del_archivo_se_guarda_sin_ruta(api: object) -> None:
    nombre = "C:\\Users\\docente\\Descargas\\export_inventado_410_con_error.xlsx"
    cuerpo = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), A.archivo(A.CON_ERROR), nombre).json()
    assert cuerpo["nombre_archivo"] == A.CON_ERROR


# BR-CARGA-09 y BR-CARGA-10: segunda subida y sección con carga

def test_br_carga_09_subir_otra_vez_el_export_publicado_responde_200_sin_escribir(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    primera = A.subir(cliente, api.seccion("410"), A.archivo(A.CORRECTO), A.CORRECTO)
    antes = api.conteos()
    segunda = A.subir(cliente, api.seccion("410"), A.archivo(A.CORRECTO), "copia de notas 410.xlsx")
    assert (primera.status_code, segunda.status_code) == (201, 200)
    assert segunda.json() == primera.json()
    assert api.conteos() == antes


def test_br_carga_10_otro_archivo_no_entra_en_una_seccion_con_carga_publicada(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    assert A.subir(cliente, api.seccion("410"), A.archivo(A.CORRECTO), A.CORRECTO).status_code == 201
    antes = api.conteos()
    respuesta = A.subir(cliente, api.seccion("410"), A.archivo(A.CON_ERROR), A.CON_ERROR)
    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "La sección 410 ya tiene una carga publicada. No se cargó el archivo."}
    assert api.conteos() == antes


def test_br_carga_09_un_archivo_publicado_en_otra_seccion_se_detiene_sin_sus_datos(api: object) -> None:
    contenido = A.archivo(A.EXPORT_411)
    publicada = A.subir(api.sesion(A.DOCENTE_411), api.seccion("411"), contenido, A.EXPORT_411).json()
    respuesta = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), contenido, "notas.xlsx")
    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "Este archivo ya está publicado en otra sección. No se cargó."}
    assert str(publicada["carga_id"]) not in respuesta.text and publicada["sha256"] not in respuesta.text


# BR-CARGA-07: guardia de datos inventados

def test_br_carga_07_la_guardia_responde_422_sin_el_codigo_y_sin_rastro(
    api: object, generador: ModuleType, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    contenido = _guardia(generador, tmp_path)
    antes = api.conteos()
    respuesta = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), contenido, "guardia.xlsx")
    assert respuesta.status_code == 422 and respuesta.json() == {"detail": GUARDIA}
    assert str(generador.CODIGO_GUARDIA) not in respuesta.text
    assert api.conteos() == antes
    assert hashlib.sha256(contenido).hexdigest() in caplog.text
    assert str(generador.CODIGO_GUARDIA) not in caplog.text


def test_br_carga_07_ningun_campo_de_la_peticion_apaga_la_guardia(
    api: object, generador: ModuleType, tmp_path: Path
) -> None:
    contenido = _guardia(generador, tmp_path)
    respuesta = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), contenido, "guardia.xlsx",
                        data={"guardia": "0", "GUARDIA_DATOS_INVENTADOS": "0"}, params={"guardia": "0"})
    assert respuesta.status_code == 422 and respuesta.json() == {"detail": GUARDIA}


def test_br_carga_07_con_la_guardia_apagada_en_el_despliegue_el_codigo_rechaza_su_fila(
    api: object, generador: ModuleType, tmp_path: Path
) -> None:
    api.ajustes = A.replace(api.ajustes, carga=A.Configuracion(conjunto_reglas=A.REGLAS,
                                                              guardia_datos_inventados=False))
    export = generador.con_celda(generador.export_410(generador.leer_plantilla()[0]), 4, "Username", 9900001)
    contenido = generador.escribir(export, tmp_path / "mal_formado.xlsx").read_bytes()
    respuesta = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), contenido, A.CORRECTO)
    assert respuesta.status_code == 201
    assert (respuesta.json()["filas_aceptadas"], respuesta.json()["filas_rechazadas"]) == (10, 1)


# BR-CARGA-04, BR-CARGA-05 y BR-CARGA-08: archivo detenido y registro de la aplicación

def test_br_carga_04_08_un_archivo_de_mas_de_1_mb_se_detiene_con_la_huella_de_todo_el_cuerpo(
    api: object, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    contenido = A.archivo(A.CORRECTO) + b"\0" * (1_048_576 + 1)
    antes = api.conteos()
    respuesta = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), contenido, A.CORRECTO)
    assert respuesta.status_code == 422 and respuesta.json() == {"detail": "El archivo supera el máximo de 1 MB."}
    assert api.conteos() == antes
    [linea] = [r.getMessage() for r in caplog.records if r.name == "abet.api" and "sha256=" in r.getMessage()]
    assert f"sha256={hashlib.sha256(contenido).hexdigest()}" in linea
    assert "motivo=ARCHIVO_DEMASIADO_GRANDE" in linea and "hora=" in linea
    # Sin detalle, el registro lo dice con un guion (spec 003, BR-CARGA-08).
    assert re.fullmatch(r"evento=archivo_detenido hora=\S+ sha256=[0-9a-f]{64} motivo=ARCHIVO_DEMASIADO_GRANDE detalle=-",
                        linea)


@pytest.mark.parametrize(("contenido", "nombre", "detalle"), [
    (b'\xef\xbb\xbf"Username","5.1 [Total Pts: 4 Score]\r\n"99000001",4\r\n',
     "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04.csv", "COMILLAS"),
    (b"\xef\xbb\xbfUsername,5.1 [Total Pts: 4 Score]\r\n99000001,4\x00\r\n",
     "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04.csv", "CARACTER_NULO"),
    (b"\xfe\xff\x00U", "gc_SINTETICO_20262_450002_410_fullgc_2026-11-04.xls", "CODIFICACION"),
])
def test_br_carga_08_spec003_un_texto_danado_se_registra_con_su_detalle_y_sin_nombres(
    api: object, caplog: pytest.LogCaptureFixture, contenido: bytes, nombre: str, detalle: str
) -> None:
    caplog.set_level(logging.DEBUG)
    antes = api.conteos()
    respuesta = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), contenido, nombre)
    assert respuesta.status_code == 422
    assert respuesta.json() == {"detail": "No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard."}
    assert api.conteos() == antes
    [linea] = [r.getMessage() for r in caplog.records if r.name == "abet.api" and "sha256=" in r.getMessage()]
    assert linea == (f"evento=archivo_detenido hora={linea.split()[1].removeprefix('hora=')} "
                     f"sha256={hashlib.sha256(contenido).hexdigest()} motivo=NO_SE_PUDO_ABRIR detalle={detalle}")
    # Lo que no debe pasar: ni el nombre del archivo, ni un código, ni el detalle en la respuesta.
    assert nombre not in caplog.text and "SINTETICO" not in caplog.text and "99000001" not in caplog.text
    assert detalle not in respuesta.text


@pytest.mark.parametrize(("nombre", "subido", "mensaje"), [
    ("danado_410.xlsx", "danado_410.xlsx", "No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard."),
    ("pdf_renombrado.xlsx", "export_410.pdf", "Solo se admiten exports de Blackboard en formato .xlsx, .csv o .xls."),
    ("pdf_renombrado.xlsx", "export_410.xlsx",
     "El contenido del archivo no es un export de Blackboard aunque su nombre termine en .xlsx, .csv o .xls."),
    ("protegido_410.xlsx", "protegido_410.xlsx",
     "El archivo está protegido con contraseña. Guárdelo sin contraseña y súbalo."),
])
def test_br_carga_05_un_archivo_ilegible_responde_422_sin_rastro(
    api: object, nombre: str, subido: str, mensaje: str
) -> None:
    antes = api.conteos()
    respuesta = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), A.archivo(nombre), subido)
    assert respuesta.status_code == 422 and respuesta.json() == {"detail": mensaje}
    assert api.conteos() == antes


def test_br_carga_03_sin_el_campo_archivo_responde_422_con_un_texto(api: object) -> None:
    respuesta = api.sesion(A.DOCENTE_410).post(f"/api/secciones/{api.seccion('410')}/cargas",
                                               data={"otro": "campo"})
    assert respuesta.status_code == 422
    assert respuesta.json() == {"detail": "La petición no tiene la forma esperada."}


def test_br_carga_02_08_una_falla_de_la_base_responde_500_y_el_registro_no_trae_el_detail(
    api: object, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    api.dueno.execute("""
        CREATE FUNCTION public.falla_de_prueba() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'falla de prueba' USING ERRCODE = '23514', CONSTRAINT = 'ck_medicion_nivel',
                DETAIL = 'Failing row contains (99000005, 5)';
        END $$""")
    api.dueno.execute("CREATE TRIGGER falla_de_prueba AFTER INSERT ON abet.medicion FOR EACH ROW"
                      " EXECUTE FUNCTION public.falla_de_prueba()")
    antes = api.conteos()
    respuesta = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), A.archivo(A.CORRECTO), A.CORRECTO)
    assert respuesta.status_code == 500 and respuesta.json() == {"detail": FALLA}
    assert api.conteos() == antes
    assert "sqlstate=23514" in caplog.text and "restriccion=ck_medicion_nivel" in caplog.text
    assert "Failing row" not in caplog.text and "99000005" not in caplog.text


def test_br_carga_08_el_registro_no_trae_valores_leidos_ni_secretos(
    api: object, generador: ModuleType, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    cliente = api.sesion(A.DOCENTE_410)
    token = cliente.cookies.get("abet_sesion")
    seccion = api.seccion("410")
    A.subir(cliente, seccion, A.archivo(A.CON_ERROR), A.CON_ERROR)
    A.subir(cliente, seccion, _guardia(generador, tmp_path), "guardia.xlsx")
    A.subir(cliente, seccion, A.archivo("danado_410.xlsx"), "danado_410.xlsx")
    cliente.get(f"/api/cargas/{api.uno('SELECT max(carga_id) FROM abet.carga')}/r17.xlsx")
    texto = caplog.text
    secretos = [api.claves[A.DOCENTE_410], token, api.ajustes.sesion_secreto]
    assert texto and not any(secreto in texto for secreto in secretos)
    assert "Inventado" not in texto and "gc_SINTETICO" not in texto
    assert not [codigo for codigo in range(99000001, 99000012) if str(codigo) in texto]
    assert str(generador.CODIGO_GUARDIA) not in texto


# BR-ACCESO-08: un solo 403 para lo ajeno

def test_br_acceso_08_el_profesor_no_alcanza_una_seccion_ajena(api: object) -> None:
    publicada = A.subir(api.sesion(A.DOCENTE_411), api.seccion("411"), A.archivo(A.EXPORT_411), A.EXPORT_411).json()
    cliente = api.sesion(A.DOCENTE_410)
    antes = api.conteos()
    respuestas = [
        A.subir(cliente, api.seccion("411"), A.archivo(A.EXPORT_411), A.EXPORT_411),
        cliente.get(f"/api/cargas/{publicada['carga_id']}"),
        cliente.get(f"/api/cargas/{publicada['carga_id']}/r17.xlsx"),
    ]
    for respuesta in respuestas:
        assert respuesta.status_code == 403 and respuesta.json() == AJENA
        assert "411" not in respuesta.text
    assert api.conteos() == antes


def test_br_acceso_08_una_seccion_o_una_carga_que_no_existe_da_el_mismo_403(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    for respuesta in (A.subir(cliente, 999_999, A.archivo(A.CORRECTO), A.CORRECTO),
                      cliente.get("/api/cargas/999999"), cliente.get("/api/cargas/999999/r17.xlsx")):
        assert respuesta.status_code == 403 and respuesta.json() == AJENA


def test_br_acceso_08_el_coordinador_no_sube_en_el_corte_1_pero_lee_constancia_y_r17(api: object) -> None:
    publicada = A.subir(api.sesion(A.DOCENTE_410), api.seccion("410"), A.archivo(A.CON_ERROR), A.CON_ERROR).json()
    coordinacion = api.sesion(A.COORDINACION)
    antes = api.conteos()
    subida = A.subir(coordinacion, api.seccion("410"), A.archivo(A.CORRECTO), A.CORRECTO)
    assert subida.status_code == 403 and subida.json() == AJENA
    assert api.conteos() == antes
    assert coordinacion.get(f"/api/cargas/{publicada['carga_id']}").json() == publicada
    assert coordinacion.get(f"/api/cargas/{publicada['carga_id']}/r17.xlsx").status_code == 200


def test_br_acceso_08_el_profesor_de_varias_secciones_no_alcanza_una_que_no_dicta(api: object) -> None:
    antes = api.conteos()
    respuesta = A.subir(api.sesion(A.VARIAS_CORREO), api.seccion("410"), A.archivo(A.CORRECTO), A.CORRECTO)
    assert respuesta.status_code == 403 and respuesta.json() == AJENA
    assert api.conteos() == antes


def test_br_carga_11_el_export_de_otra_seccion_del_profesor_se_rechaza(api: object) -> None:
    nombre = "sintetico_20262_450010_410.xlsx"
    respuesta = A.subir(api.sesion(A.VARIAS_CORREO), api.seccion("412", "450010"), A.archivo(nombre), nombre)
    assert respuesta.status_code == 201 and respuesta.json()["estado"] == "RECHAZADA"
    assert respuesta.json()["mensaje"] == "El archivo corresponde a la sección 410 y usted eligió la 412. No se publicó."


def test_br_periodo_04_una_seccion_sin_plan_no_admite_la_subida(api: object) -> None:
    api.dueno.execute("DELETE FROM abet.plan_medicion pm USING abet.asignatura a"
                      " WHERE a.asignatura_id = pm.asignatura_id AND a.codigo = '450010'")
    nombre = "sintetico_20262_450010_410.xlsx"
    respuesta = A.subir(api.sesion(A.VARIAS_CORREO), api.seccion("410", "450010"), A.archivo(nombre), nombre)
    assert respuesta.status_code == 422
    assert respuesta.json() == {"detail": "La carrera aún no registra el plan de medición de esta sección."}


# BR-R17-01, BR-R17-06 y BR-R17-09: descarga del R-17

def test_br_r17_06_09_el_r17_se_descarga_con_sus_cabeceras_y_su_hoja_constancia(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    carga_id = A.subir(cliente, api.seccion("410"), A.archivo(A.CON_ERROR), A.CON_ERROR).json()["carga_id"]
    respuesta = cliente.get(f"/api/cargas/{carga_id}/r17.xlsx")
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == A.XLSX
    assert respuesta.headers["content-disposition"] == 'attachment; filename="R017_450002_410_2026-2_PROVISIONAL.xlsx"'
    assert respuesta.headers["cache-control"] == "no-store"
    libro = load_workbook(io.BytesIO(respuesta.content))
    assert libro.sheetnames[-1] == "Constancia"
    textos = " ".join(str(c.value) for fila in libro["Constancia"].iter_rows() for c in fila if c.value)
    assert AVISO_5_3["mensaje"] in textos and RECHAZO_FILA_3["mensaje"] in textos
    assert libro.properties.creator == "ABET_SIS_MED"


def test_br_r17_06_el_r17_no_deja_que_el_navegador_adivine_su_tipo(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    carga_id = A.subir(cliente, api.seccion("410"), A.archivo(A.CON_ERROR), A.CON_ERROR).json()["carga_id"]
    respuesta = cliente.get(f"/api/cargas/{carga_id}/r17.xlsx")
    assert respuesta.status_code == 200
    assert respuesta.headers.get("x-content-type-options") == "nosniff"


def test_br_r17_01_una_carga_rechazada_no_tiene_r17(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    carga_id = A.subir(cliente, api.seccion("410"), A.archivo("sin_5_2_410.xlsx"), "sin_5_2_410.xlsx").json()["carga_id"]
    respuesta = cliente.get(f"/api/cargas/{carga_id}/r17.xlsx")
    assert respuesta.status_code == 409
    assert respuesta.json() == {"detail": "La carga no está publicada y no tiene R-17."}


# Caché: ninguna respuesta de /api con datos de la sesión queda guardada (propuesta del contrato)

def test_toda_respuesta_de_la_api_lleva_cache_control_no_store(api: object) -> None:
    cliente = api.sesion(A.DOCENTE_410)
    subida = A.subir(cliente, api.seccion("410"), A.archivo(A.CON_ERROR), A.CON_ERROR)
    carga_id = subida.json()["carga_id"]
    respuestas = {
        "POST cargas": subida,
        "GET sesion": cliente.get("/api/sesion"),
        "GET secciones": cliente.get("/api/secciones", params={"periodo": A.PERIODO}),
        "GET carga": cliente.get(f"/api/cargas/{carga_id}"),
        "GET r17": cliente.get(f"/api/cargas/{carga_id}/r17.xlsx"),
        "403 ajena": cliente.get(f"/api/cargas/{carga_id + 999}"),
        "401 sin sesion": api.cliente().get("/api/secciones", params={"periodo": A.PERIODO}),
    }
    sin_cabecera = {nombre: r.headers.get("cache-control") for nombre, r in respuestas.items()
                    if r.headers.get("cache-control") != "no-store"}
    assert sin_cabecera == {}


def test_una_ruta_fuera_de_api_no_recibe_la_cabecera_de_cache(api: object) -> None:
    assert "cache-control" not in api.cliente().get("/fuera").headers
