"""Pruebas de la validación del export leído (T032 de specs/001-mvp-carga-r17/tasks.md).

Cada prueba nombra en su función la regla de negocio (business rule, BR) de
specs/features/carga-export/carga-export.spec.md que comprueba, con lo que debe pasar y lo que no
debe pasar (AGENTS.md, regla 8). Los libros salen de tests/datos_inventados/ o de copias que arma el
generador en tmp_path, y las copias con un código fuera de 99 nunca se escriben en esa carpeta. Los
motivos, las filas y los porcentajes esperados son literales de carga.feature y del contrato, y los
porcentajes se calculan aparte, sobre las filas aceptadas, con el redondeo de la vista del R-17.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import fields
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from types import ModuleType

import pytest

from abet_carga.lector import leer
from abet_carga.modelos import (
    CodigoNoInventado,
    ContextoSeccion,
    Efecto,
    FilaAceptada,
    LibroLeido,
    Motivo,
    PiDelPlan,
    Rechazo,
    SeccionDeclarada,
    SeccionSinDeclarar,
    Validacion,
)
from abet_carga.validacion import guardia, normalizar_codigo, seccion_declarada, validar

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "tests" / "datos_inventados"

CORRECTO = "sintetico_20262_450002_410.xlsx"
CON_ERROR = "export_inventado_410_con_error.xlsx"
EXPORT_411 = "export_inventado_411.xlsx"
HOJA1 = "hoja1_sin_seccion.xlsx"
NOMBRE_411 = "gc_SINTETICO_20262_450002_411_fullgc_2026-10-20.xlsx"

PLAN = (PiDelPlan(51, "5.1"), PiDelPlan(52, "5.2"), PiDelPlan(53, "5.3"))
CONTEXTO_410 = ContextoSeccion(periodo="2026-2", curso_codigo="450002", seccion_codigo="410", plan=PLAN)

MENSAJE_GUARDIA_FILA_4 = (
    "El piloto solo admite códigos inventados, de 99000000 a 99999999. Revise la fila 4. No se guardó nada."
)
MENSAJE_SIN_SECCION = (
    "El archivo no indica su sección. Sube el export de Blackboard sin cambiar el nombre de su hoja."
)

AVISO_5_3 = Rechazo(Motivo.PUNTAJE_MAXIMO_DISTINTO, Efecto.AVISO, None, "5.3")


# Ayudas de las pruebas

def _leido(nombre: str, nombre_archivo: str | None = None) -> LibroLeido:
    return leer((CARPETA / nombre).read_bytes(), nombre_archivo=nombre_archivo or nombre)


def _export(generador: ModuleType) -> object:
    plantilla, _ = generador.leer_plantilla()
    return generador.export_410(plantilla)


def _libro(generador: ModuleType, export: object, tmp_path: Path, nombre_archivo: str = CORRECTO) -> LibroLeido:
    """Escribe el export en tmp_path con el generador y lo lee con el lector."""
    return leer(generador.escribir(export, tmp_path / "copia.xlsx").read_bytes(), nombre_archivo=nombre_archivo)


def _con_celdas(generador: ModuleType, export: object, fila: int, cambios: dict[str, object]) -> object:
    for columna, valor in cambios.items():
        export = generador.con_celda(export, fila, columna, valor)
    return export


def _con_encabezado(generador: ModuleType, export: object, columna: str, nuevo: str) -> object:
    encabezado = list(export.encabezado)
    encabezado[export.indice(columna)] = nuevo
    return generador.Export(export.hoja, tuple(encabezado), export.filas)


def _validar(libro: LibroLeido) -> Validacion:
    return validar(libro, CONTEXTO_410)


def _porcentajes(validacion: Validacion) -> tuple[Decimal, ...]:
    """Porcentaje de calificados con nivel 3 o 4 en 5.1, 5.2 y 5.3, con un decimal."""
    resultado = []
    for pi in ("5.1", "5.2", "5.3"):
        niveles = [
            m.nivel
            for f in validacion.filas_aceptadas
            for m in f.mediciones
            if m.pi_codigo == pi and m.nivel is not None
        ]
        logro = Decimal(100 * sum(1 for n in niveles if n >= 3)) / Decimal(len(niveles))
        resultado.append(logro.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    return tuple(resultado)


def _cuentas(validacion: Validacion) -> tuple[int, int, int]:
    return validacion.filas_leidas, len(validacion.filas_aceptadas), validacion.filas_rechazadas


def _mediciones(validacion: Validacion) -> int:
    return sum(len(fila.mediciones) for fila in validacion.filas_aceptadas)


def _de_carga(motivo: Motivo, pi: str | None = None) -> Rechazo:
    return Rechazo(motivo, Efecto.RECHAZA_CARGA, None, pi)


def _sin_nada_mas(validacion: Validacion) -> bool:
    """Una carga rechazada entera no registra columnas, filas, mediciones ni avisos (BR-CARGA-13)."""
    return (validacion.columnas, validacion.filas_aceptadas, validacion.rechazos_de_fila, validacion.avisos) == (
        (),
        (),
        (),
        (),
    )


# BR-CARGA-07. Guardia de códigos inventados

def test_br_carga_07_el_export_correcto_pasa_la_guardia() -> None:
    assert guardia(_leido(CORRECTO)) is None


@pytest.mark.parametrize(
    ("codigo", "guardado"),
    [
        (99000000, "99000000"),
        (99999999, "99999999"),
        ("99000000", "99000000"),
        (" 99999999 ", "99999999"),
        (99000000.0, "99000000"),
    ],
)
def test_br_carga_07_los_extremos_del_rango_inventado_pasan_la_guardia(
    generador: ModuleType, tmp_path: Path, codigo: object, guardado: str
) -> None:
    libro = _libro(generador, generador.con_celda(_export(generador), 4, "Username", codigo), tmp_path)
    assert guardia(libro) is None
    validacion = _validar(libro)
    assert _cuentas(validacion) == (11, 11, 0)
    assert validacion.filas_aceptadas[2].codigo == guardado


def test_br_carga_07_el_export_de_la_guardia_se_detiene_en_la_fila_4(generador: ModuleType, tmp_path: Path) -> None:
    ruta = generador.escribir_export_guardia(tmp_path / "guardia.xlsx")
    with pytest.raises(CodigoNoInventado) as error:
        guardia(leer(ruta.read_bytes(), nombre_archivo=CORRECTO))
    assert error.value.fila_origen == 4
    assert error.value.mensaje == MENSAJE_GUARDIA_FILA_4
    assert str(generador.CODIGO_GUARDIA) not in f"{error.value} {error.value!r} {error.value.args}"


@pytest.mark.parametrize("codigo", [98999999, 9900001, "9900001", "99A00001", 10000004.0, "990000001"])
def test_br_carga_07_un_codigo_que_no_es_inventado_detiene_el_archivo(
    generador: ModuleType, tmp_path: Path, codigo: object
) -> None:
    libro = _libro(generador, generador.con_celda(_export(generador), 4, "Username", codigo), tmp_path)
    with pytest.raises(CodigoNoInventado) as error:
        guardia(libro)
    assert (error.value.fila_origen, error.value.mensaje) == (4, MENSAJE_GUARDIA_FILA_4)
    assert str(codigo).strip().removesuffix(".0") not in f"{error.value} {error.value!r} {error.value.args}"


def test_br_carga_07_la_guardia_nombra_la_primera_fila_que_falla(generador: ModuleType, tmp_path: Path) -> None:
    export = generador.con_celda(_export(generador), 9, "Username", 98999999)
    export = generador.con_celda(export, 6, "Username", 10000004)
    with pytest.raises(CodigoNoInventado) as error:
        guardia(_libro(generador, export, tmp_path))
    assert error.value.fila_origen == 6
    assert "Revise la fila 6." in error.value.mensaje


def test_br_carga_07_sin_username_la_guardia_revisa_student_id(generador: ModuleType, tmp_path: Path) -> None:
    export = _export(generador)
    for fila in range(2, 13):
        export = generador.con_celda(export, fila, "Student ID", 99000100 + fila)
    export = generador.con_celda(generador.sin_columnas(export, "Username"), 6, "Student ID", 10000004)
    with pytest.raises(CodigoNoInventado) as error:
        guardia(_libro(generador, export, tmp_path))
    assert error.value.fila_origen == 6


def test_br_carga_07_con_username_la_guardia_no_revisa_student_id(generador: ModuleType, tmp_path: Path) -> None:
    # El código sale de Username, y el lector descarta Student ID sin guardar sus valores.
    export = generador.con_celda(_export(generador), 4, "Student ID", 10000004)
    assert guardia(_libro(generador, export, tmp_path)) is None


def test_br_carga_07_un_username_vacio_no_detiene_la_guardia(generador: ModuleType, tmp_path: Path) -> None:
    libro = _libro(generador, generador.con_celda(_export(generador), 3, "Username", None), tmp_path)
    assert guardia(libro) is None
    assert _validar(libro).rechazos_de_fila == (Rechazo(Motivo.CODIGO_VACIO, Efecto.RECHAZA_FILA, 3, None),)


# BR-CARGA-11. Sección declarada por la hoja o por el nombre del archivo

def test_br_carga_11_la_hoja_de_la_410_declara_la_seccion_elegida() -> None:
    validacion = _validar(_leido(CORRECTO))
    assert validacion.rechazo_de_carga is None
    assert validacion.publicable


def test_br_carga_11_el_export_de_la_411_subido_en_la_410_se_rechaza() -> None:
    validacion = _validar(_leido(EXPORT_411))
    assert validacion.rechazo_de_carga == _de_carga(Motivo.SECCION_NO_COINCIDE)
    assert (validacion.filas_de_datos, *_cuentas(validacion)) == (11, 0, 0, 0)
    assert _sin_nada_mas(validacion)
    assert not validacion.publicable


@pytest.mark.parametrize(
    "hoja",
    # Blackboard corta la hoja a 31 caracteres, así que la de la sección con cero lleva un prefijo corto.
    ["gc_SINTETICO_20262_450010_410_f", "gc_SINTETICO_20262_450002_411", "gc_SINT_20262_450002_0411_f"],
    ids=["otra_asignatura", "otra_seccion_truncada", "otra_seccion_con_cero"],
)
def test_br_carga_11_otra_asignatura_u_otra_seccion_en_la_hoja_rechaza_la_carga(
    generador: ModuleType, tmp_path: Path, hoja: str
) -> None:
    validacion = _validar(_libro(generador, generador.con_hoja(_export(generador), hoja), tmp_path))
    assert validacion.rechazo_de_carga == _de_carga(Motivo.SECCION_NO_COINCIDE)
    assert _sin_nada_mas(validacion)


@pytest.mark.parametrize(
    ("nombre", "motivo"),
    [
        (NOMBRE_411, Motivo.SECCION_NO_COINCIDE),
        ("gc_SINTETICO_20261_450002_410_fullgc_2026-10-20.xlsx", Motivo.PERIODO_NO_COINCIDE),
        ("gc_SINTETICO_20262_450002_410_fullgc_2026-10-20 (1).xlsx", None),
    ],
    ids=["otra_seccion", "otro_periodo", "la_410"],
)
def test_br_carga_11_si_la_hoja_no_declara_la_seccion_se_coteja_el_nombre(nombre: str, motivo: Motivo | None) -> None:
    validacion = _validar(_leido(HOJA1, nombre))
    assert validacion.rechazo_de_carga == (None if motivo is None else _de_carga(motivo))


@pytest.mark.parametrize("hoja", ["gc_SINTETICO_20262_450002_410", "gc_SINTETICO_20262_450002_410_"])
def test_br_carga_11_una_hoja_truncada_a_31_caracteres_se_coteja_igual(
    generador: ModuleType, tmp_path: Path, hoja: str
) -> None:
    validacion = _validar(_libro(generador, generador.con_hoja(_export(generador), hoja), tmp_path))
    assert validacion.rechazo_de_carga is None
    assert _cuentas(validacion) == (11, 11, 0)


def test_br_carga_11_la_hoja_manda_sobre_el_nombre_del_archivo() -> None:
    assert _validar(_leido(CORRECTO, NOMBRE_411)).rechazo_de_carga is None


@pytest.mark.parametrize(
    "nombre", ["notas.xlsx", CORRECTO, "gc_SINTETICO_20262_450002_410.xlsx", "Notas_410_fullgc_2026.xlsx"]
)
def test_br_carga_11_un_export_que_no_declara_su_seccion_se_detiene(nombre: str) -> None:
    with pytest.raises(SeccionSinDeclarar) as error:
        _validar(_leido(HOJA1, nombre))
    assert error.value.mensaje == MENSAJE_SIN_SECCION


@pytest.mark.parametrize(
    ("hoja", "nombre", "esperada"),
    [
        ("gc_SINTETICO_20262_450002_410_f", "notas.xlsx", SeccionDeclarada("2026-2", "450002", "410")),
        ("gc_SINTETICO_20262_450002_410", "notas.xlsx", SeccionDeclarada("2026-2", "450002", "410")),
        ("gc_20260_4500_7_f", "notas.xlsx", SeccionDeclarada("2026-0", "4500", "7")),
        ("gc_SINTETICO_20262_450002_0410_f", "notas.xlsx", SeccionDeclarada("2026-2", "450002", "410")),
        ("Hoja1", NOMBRE_411, SeccionDeclarada("2026-2", "450002", "411")),
        ("Hoja1", "GC_SINTETICO_20262_450002_411_FULLGC_2026-10-20.XLSX", None),
        ("Hoja1", "notas.xlsx", None),
        ("gc_SINTETICO_20263_450002_410_f", "notas.xlsx", None),
        ("gc_SINTETICO_20262_45000_410_f", "notas.xlsx", None),
        ("gc_SINTETICO_20262_450002_f", "notas.xlsx", None),
        ("SINTETICO_20262_450002_410_f", "notas.xlsx", None),
    ],
    ids=[
        "hoja",
        "hoja_truncada",
        "verano_y_asignatura_de_4_cifras",
        "seccion_con_cero",
        "nombre_del_archivo",
        "nombre_en_mayusculas",
        "ninguno",
        "ciclo_que_no_existe",
        "asignatura_de_5_cifras",
        "sin_seccion",
        "sin_gc",
    ],
)
def test_br_carga_11_seccion_declarada_lee_periodo_asignatura_y_seccion(
    hoja: str, nombre: str, esperada: SeccionDeclarada | None
) -> None:
    assert seccion_declarada(hoja, nombre) == esperada


# BR-CARGA-12. Periodo declarado por el archivo

def test_br_carga_12_el_periodo_de_la_hoja_igual_al_de_la_seccion_no_rechaza_la_carga(
    generador: ModuleType, tmp_path: Path
) -> None:
    # El ciclo 0 es el de verano, que la hoja escribe 20260 y abet.periodo guarda como 2026-0.
    libro = _libro(generador, generador.con_hoja(_export(generador), "gc_SINTETICO_20260_450002_410_f"), tmp_path)
    verano = ContextoSeccion(periodo="2026-0", curso_codigo="450002", seccion_codigo="410", plan=PLAN)
    assert validar(libro, verano).rechazo_de_carga is None
    assert _cuentas(validar(libro, verano)) == (11, 11, 0)
    assert validar(libro, CONTEXTO_410).rechazo_de_carga == _de_carga(Motivo.PERIODO_NO_COINCIDE)


def test_br_carga_12_otro_periodo_en_la_hoja_rechaza_la_carga(generador: ModuleType, tmp_path: Path) -> None:
    export = generador.con_hoja(_export(generador), "gc_SINTETICO_20261_450002_410_f")
    validacion = _validar(_libro(generador, export, tmp_path))
    assert validacion.rechazo_de_carga == _de_carga(Motivo.PERIODO_NO_COINCIDE)
    assert _sin_nada_mas(validacion)


def test_br_carga_12_si_difieren_el_periodo_y_la_seccion_manda_seccion_no_coincide(
    generador: ModuleType, tmp_path: Path
) -> None:
    export = generador.con_hoja(_export(generador), "gc_SINTETICO_20261_450002_411_f")
    assert _validar(_libro(generador, export, tmp_path)).rechazo_de_carga == _de_carga(Motivo.SECCION_NO_COINCIDE)


# BR-CARGA-13. Rechazo por estructura

@pytest.mark.parametrize(
    ("archivo", "motivo", "pi", "filas_de_datos"),
    [
        ("vacio_410.xlsx", Motivo.ARCHIVO_SIN_FILAS, None, 0),
        ("sin_5_2_410.xlsx", Motivo.PI_DEL_PLAN_AUSENTE, "5.2", 11),
        ("sin_username_ni_student_id_410.xlsx", Motivo.COLUMNA_CODIGO_AUSENTE, None, 11),
    ],
)
def test_br_carga_13_un_defecto_de_estructura_rechaza_la_carga_entera(
    archivo: str, motivo: Motivo, pi: str | None, filas_de_datos: int
) -> None:
    validacion = _validar(_leido(archivo, CORRECTO))
    assert validacion.rechazo_de_carga == _de_carga(motivo, pi)
    assert (validacion.filas_de_datos, *_cuentas(validacion)) == (filas_de_datos, 0, 0, 0)
    assert _sin_nada_mas(validacion)
    assert not validacion.publicable


def test_br_carga_13_un_pi_en_dos_columnas_rechaza_la_carga(generador: ModuleType, tmp_path: Path) -> None:
    export = generador.con_columna(_export(generador), "5.1 [Total Pts: 4 Score]", [3] * 11)
    validacion = _validar(_libro(generador, export, tmp_path))
    assert validacion.rechazo_de_carga == _de_carga(Motivo.PI_REPETIDO, "5.1")
    assert _sin_nada_mas(validacion)


def test_br_carga_13_una_carga_rechazada_por_estructura_no_deja_avisos() -> None:
    libro = _leido("sin_5_2_410.xlsx", CORRECTO)
    # La columna 5.3 sigue declarando 20 puntos, y aun así no queda el aviso PUNTAJE_MAXIMO_DISTINTO.
    assert [(c.pi_codigo, c.puntaje_maximo_declarado) for c in libro.columnas_pi] == [("5.1", 4), ("5.3", 20)]
    assert _validar(libro).avisos == ()


_SIN_CODIGO = ("Username", "Student ID")
_REPETIDA_5_1 = "5.1 [Total Pts: 4 Score]"
_REPETIDA_5_3 = "5.3 [Total Pts: 20 Score]"


@pytest.mark.parametrize(
    ("armar", "esperado"),
    [
        (lambda g, e: g.sin_filas(g.sin_columnas(e, *_SIN_CODIGO)), _de_carga(Motivo.ARCHIVO_SIN_FILAS)),
        (lambda g, e: g.sin_columnas(e, *_SIN_CODIGO, "5.2"), _de_carga(Motivo.COLUMNA_CODIGO_AUSENTE)),
        (
            lambda g, e: g.con_columna(g.sin_columnas(e, "5.2"), _REPETIDA_5_1, [3] * 11),
            _de_carga(Motivo.PI_DEL_PLAN_AUSENTE, "5.2"),
        ),
        (lambda g, e: g.sin_columnas(e, "5.3", "5.1"), _de_carga(Motivo.PI_DEL_PLAN_AUSENTE, "5.1")),
        (
            lambda g, e: g.con_columna(g.con_columna(e, _REPETIDA_5_3, [3] * 11), _REPETIDA_5_1, [3] * 11),
            _de_carga(Motivo.PI_REPETIDO, "5.1"),
        ),
        (
            lambda g, e: g.con_hoja(g.sin_columnas(e, "5.2"), "gc_SINTETICO_20262_450002_411_f"),
            _de_carga(Motivo.SECCION_NO_COINCIDE),
        ),
        (
            lambda g, e: g.con_hoja(g.sin_filas(e), "gc_SINTETICO_20261_450002_410_f"),
            _de_carga(Motivo.PERIODO_NO_COINCIDE),
        ),
    ],
    ids=[
        "sin_filas_antes_que_sin_codigo",
        "sin_codigo_antes_que_sin_pi",
        "pi_ausente_antes_que_pi_repetido",
        "el_primer_pi_ausente_del_plan",
        "el_primer_pi_repetido_del_plan",
        "seccion_antes_que_estructura",
        "periodo_antes_que_estructura",
    ],
)
def test_br_carga_13_con_varios_defectos_manda_el_primero(
    generador: ModuleType, tmp_path: Path, armar: Callable[[ModuleType, object], object], esperado: Rechazo
) -> None:
    validacion = _validar(_libro(generador, armar(generador, _export(generador)), tmp_path))
    assert validacion.rechazo_de_carga == esperado


def test_br_carga_03_un_export_sin_seccion_declarada_se_detiene_antes_que_su_estructura(
    generador: ModuleType, tmp_path: Path
) -> None:
    export = generador.con_hoja(generador.sin_columnas(_export(generador), "5.2"), "Hoja1")
    with pytest.raises(SeccionSinDeclarar):
        _validar(_libro(generador, export, tmp_path, nombre_archivo="notas.xlsx"))


def test_br_carga_13_el_primer_pi_ausente_sigue_el_orden_natural_del_plan() -> None:
    # El plan llega desordenado y con 5.9 y 5.10, que el export no trae. El primero es 5.9, no 5.10.
    plan = (
        PiDelPlan(10, "5.10"), PiDelPlan(53, "5.3"), PiDelPlan(9, "5.9"), PiDelPlan(51, "5.1"), PiDelPlan(52, "5.2")
    )
    contexto = ContextoSeccion(periodo="2026-2", curso_codigo="450002", seccion_codigo="410", plan=plan)
    assert validar(_leido(CORRECTO), contexto).rechazo_de_carga == _de_carga(Motivo.PI_DEL_PLAN_AUSENTE, "5.9")


def test_br_carga_13_un_pi_fuera_del_plan_en_dos_columnas_no_rechaza_la_carga(
    generador: ModuleType, tmp_path: Path
) -> None:
    export = generador.con_columna(_export(generador), "4.1 [Total Pts: 4 Score] |9000041", [3] * 11)
    export = generador.con_columna(export, "4.1 [Total Pts: 4 Score] |9000042", [3] * 11)
    validacion = _validar(_libro(generador, export, tmp_path))
    fuera = Rechazo(Motivo.COLUMNA_PI_FUERA_DEL_PLAN, Efecto.AVISO, None, "4.1")
    assert validacion.rechazo_de_carga is None
    assert validacion.avisos == (AVISO_5_3, fuera, fuera)
    assert validacion.publicable


def test_br_carga_01_el_contexto_exige_un_plan_con_pi_distintos() -> None:
    # cargar() responde 422 a una sección sin plan antes de validar (BR-CARGA-01), y el contexto lo exige igual.
    with pytest.raises(ValueError):
        ContextoSeccion(periodo="2026-2", curso_codigo="450002", seccion_codigo="410", plan=())
    with pytest.raises(ValueError):
        ContextoSeccion("2026-2", "450002", "410", (PiDelPlan(51, "5.1"), PiDelPlan(52, "5.1")))
    with pytest.raises(ValueError):
        ContextoSeccion("2026-2", "450002", "410", (PiDelPlan(51, "5.1"), PiDelPlan(50, "5")))
    contexto = ContextoSeccion("2026-2", "450002", "410", (PiDelPlan(51, "5.1"), PiDelPlan(70, "7.10")))
    assert contexto.plan[1].codigo == "7.10"


# BR-CARGA-14. Columnas del plan y avisos de columna

def test_br_carga_14_el_export_correcto_registra_las_columnas_5_1_5_2_y_5_3() -> None:
    validacion = _validar(_leido(CORRECTO))
    assert [
        (c.pi_id, c.pi_codigo, c.posicion, c.bb_columna_id, c.puntaje_maximo_declarado) for c in validacion.columnas
    ] == [
        (51, "5.1", 25, "9000051", Decimal(4)),
        (52, "5.2", 26, "9000052", Decimal(4)),
        (53, "5.3", 27, "9000053", Decimal(20)),
    ]
    assert validacion.columnas[0].encabezado.startswith("5.1 [Total Pts: 4 Score]")
    assert validacion.avisos == (AVISO_5_3,)


def test_br_carga_14_una_columna_de_pi_que_no_esta_en_el_plan_se_ignora_con_aviso(
    generador: ModuleType, tmp_path: Path
) -> None:
    # Un 5 en la columna 4.1 no rechaza ninguna fila, porque la columna no entra a la carga.
    export = generador.con_columna(_export(generador), "4.1 [Total Pts: 4 Score] |9000041", [5] * 11)
    validacion = _validar(_libro(generador, export, tmp_path))
    assert _cuentas(validacion) == (11, 11, 0)
    assert [c.pi_codigo for c in validacion.columnas] == ["5.1", "5.2", "5.3"]
    assert validacion.avisos == (AVISO_5_3, Rechazo(Motivo.COLUMNA_PI_FUERA_DEL_PLAN, Efecto.AVISO, None, "4.1"))
    assert _mediciones(validacion) == 33


def test_br_carga_14_un_encabezado_5_10_no_pasa_como_el_pi_5_1(generador: ModuleType, tmp_path: Path) -> None:
    export = _con_encabezado(generador, _export(generador), "5.1", "5.10 [Total Pts: 4 Score] |9000510")
    validacion = _validar(_libro(generador, export, tmp_path))
    assert validacion.rechazo_de_carga == _de_carga(Motivo.PI_DEL_PLAN_AUSENTE, "5.1")


@pytest.mark.parametrize("total", ["0", "0.004", "9999.996", "10000"])
def test_br_carga_14_un_total_pts_que_la_base_no_guarda_deja_igual_el_aviso(
    generador: ModuleType, tmp_path: Path, total: str
) -> None:
    # Valor provisional de D-04. La columna entra sin puntaje, porque ck_carga_columna_puntaje exige más
    # de 0 en numeric(6, 2), y el aviso queda porque el encabezado declara un Total Pts distinto de 4.
    export = _con_encabezado(generador, _export(generador), "5.1", f"5.1 [Total Pts: {total} Score] |9000051")
    validacion = _validar(_libro(generador, export, tmp_path))
    assert validacion.avisos == (Rechazo(Motivo.PUNTAJE_MAXIMO_DISTINTO, Efecto.AVISO, None, "5.1"), AVISO_5_3)
    assert [(c.pi_codigo, c.puntaje_maximo_declarado) for c in validacion.columnas] == [
        ("5.1", None),
        ("5.2", Decimal(4)),
        ("5.3", Decimal(20)),
    ]
    assert _cuentas(validacion) == (11, 11, 0)


@pytest.mark.parametrize(
    "encabezado",
    [
        "5.3 [Total Pts: 4 Score] |9000053",
        "5.3 [Total Pts: 4.00 Score] |9000053",
        "5.3 [Total Pts: 4,004 Score] |9000053",
        "5.3 [Score]",
    ],
)
def test_br_carga_14_sin_un_total_pts_distinto_de_4_no_queda_aviso(
    generador: ModuleType, tmp_path: Path, encabezado: str
) -> None:
    export = _con_encabezado(generador, _export(generador), "5.3", encabezado)
    validacion = _validar(_libro(generador, export, tmp_path))
    assert validacion.avisos == ()
    assert validacion.publicable


# BR-CARGA-15. Rechazo de filas

def test_br_carga_15_el_export_correcto_acepta_las_11_filas() -> None:
    validacion = _validar(_leido(CORRECTO))
    assert _cuentas(validacion) == (11, 11, 0)
    assert validacion.rechazos_de_fila == ()
    assert [f.fila_origen for f in validacion.filas_aceptadas] == list(range(2, 13))
    assert [f.codigo for f in validacion.filas_aceptadas] == [str(c) for c in range(99000001, 99000012)]
    mediciones = [m for f in validacion.filas_aceptadas for m in f.mediciones]
    assert len(mediciones) == 33
    assert {m.estado_evidencia for m in mediciones} == {"CALIFICADO"}
    assert {m.nivel for m in mediciones} <= {1, 2, 3, 4}
    assert _porcentajes(validacion) == (Decimal("63.6"), Decimal("63.6"), Decimal("72.7"))


def test_br_carga_15_el_5_de_la_fila_3_rechaza_esa_fila_completa() -> None:
    validacion = _validar(_leido(CON_ERROR))
    assert _cuentas(validacion) == (11, 10, 1)
    assert validacion.rechazos_de_fila == (Rechazo(Motivo.NIVEL_FUERA_DE_ESCALA, Efecto.RECHAZA_FILA, 3, "5.2"),)
    assert validacion.avisos == (AVISO_5_3,)
    assert 3 not in [f.fila_origen for f in validacion.filas_aceptadas]
    assert "99000002" not in [f.codigo for f in validacion.filas_aceptadas]
    assert _mediciones(validacion) == 30
    assert _porcentajes(validacion) == (Decimal("60.0"), Decimal("60.0"), Decimal("70.0"))
    assert validacion.publicable


@pytest.mark.parametrize(
    ("valor", "motivo"),
    [
        (5, Motivo.NIVEL_FUERA_DE_ESCALA),
        (0, Motivo.NIVEL_FUERA_DE_ESCALA),
        (-1, Motivo.NIVEL_FUERA_DE_ESCALA),
        ("5", Motivo.NIVEL_FUERA_DE_ESCALA),
        ("-1", Motivo.NIVEL_FUERA_DE_ESCALA),
        (5.0, Motivo.NIVEL_FUERA_DE_ESCALA),
        ("3,5", Motivo.NIVEL_NO_NUMERICO),
        (3.5, Motivo.NIVEL_NO_NUMERICO),
        ("Needs Grading", Motivo.NIVEL_NO_NUMERICO),
        ("-", Motivo.NIVEL_NO_NUMERICO),
        ("NP", Motivo.NIVEL_NO_NUMERICO),
        (True, Motivo.NIVEL_NO_NUMERICO),
        (datetime(2026, 10, 28, 10, 15), Motivo.NIVEL_NO_NUMERICO),
        ("٣", Motivo.NIVEL_NO_NUMERICO),
    ],
)
def test_br_carga_15_una_celda_de_pi_invalida_en_la_fila_3_rechaza_esa_fila(
    generador: ModuleType, tmp_path: Path, valor: object, motivo: Motivo
) -> None:
    # Valores provisionales de D-06 (-1, 0 y 5 fuera de la escala) y de D-03 («-» y «NP» no son niveles).
    validacion = _validar(_libro(generador, generador.con_celda(_export(generador), 3, "5.2", valor), tmp_path))
    assert _cuentas(validacion) == (11, 10, 1)
    assert validacion.rechazos_de_fila == (Rechazo(motivo, Efecto.RECHAZA_FILA, 3, "5.2"),)
    assert _mediciones(validacion) == 30
    assert _porcentajes(validacion) == (Decimal("60.0"), Decimal("60.0"), Decimal("70.0"))


@pytest.mark.parametrize(("valor", "nivel"), [(3.0, 3), ("3", 3), (" 4 ", 4), ("+4", 4)])
def test_br_carga_15_un_nivel_entero_escrito_de_otra_forma_se_acepta(
    generador: ModuleType, tmp_path: Path, valor: object, nivel: int
) -> None:
    validacion = _validar(_libro(generador, generador.con_celda(_export(generador), 3, "5.2", valor), tmp_path))
    assert _cuentas(validacion) == (11, 11, 0)
    fila_3 = validacion.filas_aceptadas[1]
    assert [(m.pi_codigo, m.nivel) for m in fila_3.mediciones] == [("5.1", 4), ("5.2", nivel), ("5.3", 4)]


@pytest.mark.parametrize("vacia", [None, "   "], ids=["sin_valor", "con_espacios"])
def test_br_carga_15_una_celda_de_pi_vacia_es_sin_evidencia_y_no_rechaza_la_fila(
    generador: ModuleType, tmp_path: Path, vacia: object
) -> None:
    validacion = _validar(_libro(generador, generador.con_celda(_export(generador), 3, "5.2", vacia), tmp_path))
    assert _cuentas(validacion) == (11, 11, 0)
    assert _mediciones(validacion) == 33
    medicion = validacion.filas_aceptadas[1].mediciones[1]
    assert (medicion.pi_codigo, medicion.nivel, medicion.estado_evidencia) == ("5.2", None, "SIN_EVIDENCIA")
    assert _porcentajes(validacion) == (Decimal("63.6"), Decimal("60.0"), Decimal("72.7"))


@pytest.mark.parametrize(
    ("fila", "codigo", "motivo", "porcentajes"),
    [
        (3, None, Motivo.CODIGO_VACIO, ("60.0", "60.0", "70.0")),
        (3, "  ", Motivo.CODIGO_VACIO, ("60.0", "60.0", "70.0")),
        (12, 99000001, Motivo.CODIGO_DUPLICADO, ("70.0", "70.0", "80.0")),
        (12, "99000001", Motivo.CODIGO_DUPLICADO, ("70.0", "70.0", "80.0")),
    ],
    ids=["vacio", "con_espacios", "repetido", "repetido_como_texto"],
)
def test_br_carga_15_un_codigo_vacio_o_repetido_rechaza_su_fila(
    generador: ModuleType, tmp_path: Path, fila: int, codigo: object, motivo: Motivo, porcentajes: tuple[str, ...]
) -> None:
    export = generador.con_celda(_export(generador), fila, "Username", codigo)
    validacion = _validar(_libro(generador, export, tmp_path))
    assert _cuentas(validacion) == (11, 10, 1)
    assert validacion.rechazos_de_fila == (Rechazo(motivo, Efecto.RECHAZA_FILA, fila, None),)
    assert _porcentajes(validacion) == tuple(Decimal(p) for p in porcentajes)


def test_br_carga_15_el_codigo_repetido_conserva_la_primera_aparicion(generador: ModuleType, tmp_path: Path) -> None:
    export = generador.con_celda(_export(generador), 12, "Username", 99000001)
    primera = _validar(_libro(generador, export, tmp_path)).filas_aceptadas[0]
    assert (primera.fila_origen, primera.codigo) == (2, "99000001")


@pytest.mark.parametrize(
    "codigo", [9900001, "990000011", "99A00001"], ids=["siete_cifras", "nueve_cifras", "con_letra"]
)
def test_br_carga_15_con_la_guardia_apagada_un_codigo_mal_formado_rechaza_solo_su_fila(
    generador: ModuleType, tmp_path: Path, codigo: object
) -> None:
    # validar() no aplica la guardia, que cargar() llama aparte solo con GUARDIA_DATOS_INVENTADOS=1.
    validacion = _validar(_libro(generador, generador.con_celda(_export(generador), 4, "Username", codigo), tmp_path))
    assert _cuentas(validacion) == (11, 10, 1)
    assert validacion.rechazos_de_fila == (Rechazo(Motivo.CODIGO_INVALIDO, Efecto.RECHAZA_FILA, 4, None),)
    assert _porcentajes(validacion) == (Decimal("70.0"), Decimal("60.0"), Decimal("70.0"))


def test_br_carga_15_el_codigo_repetido_se_rechaza_aunque_su_primera_aparicion_quede_rechazada(
    generador: ModuleType, tmp_path: Path
) -> None:
    export = generador.con_celda(_export(generador), 2, "5.2", 5)
    export = generador.con_celda(export, 12, "Username", 99000001)
    validacion = _validar(_libro(generador, export, tmp_path))
    assert validacion.rechazos_de_fila == (
        Rechazo(Motivo.NIVEL_FUERA_DE_ESCALA, Efecto.RECHAZA_FILA, 2, "5.2"),
        Rechazo(Motivo.CODIGO_DUPLICADO, Efecto.RECHAZA_FILA, 12, None),
    )
    assert "99000001" not in [f.codigo for f in validacion.filas_aceptadas]


@pytest.mark.parametrize(
    ("cambios", "esperado"),
    [
        ({"Username": None, "5.2": 5}, Rechazo(Motivo.CODIGO_VACIO, Efecto.RECHAZA_FILA, 3, None)),
        ({"5.1": 5, "5.2": "NP"}, Rechazo(Motivo.NIVEL_FUERA_DE_ESCALA, Efecto.RECHAZA_FILA, 3, "5.1")),
        ({"5.1": "NP", "5.2": 5}, Rechazo(Motivo.NIVEL_NO_NUMERICO, Efecto.RECHAZA_FILA, 3, "5.1")),
        ({"5.3": 0, "5.2": "Needs Grading"}, Rechazo(Motivo.NIVEL_NO_NUMERICO, Efecto.RECHAZA_FILA, 3, "5.2")),
    ],
    ids=["codigo_antes_que_nivel", "fuera_de_escala_en_5_1", "no_numerico_en_5_1", "5_2_antes_que_5_3"],
)
def test_br_carga_15_con_varias_celdas_invalidas_manda_la_primera(
    generador: ModuleType, tmp_path: Path, cambios: dict[str, object], esperado: Rechazo
) -> None:
    validacion = _validar(_libro(generador, _con_celdas(generador, _export(generador), 3, cambios), tmp_path))
    assert validacion.rechazos_de_fila == (esperado,)


@pytest.mark.parametrize(
    ("valor", "codigo"),
    [
        (99000001, "99000001"),
        ("99000001", "99000001"),
        (" 99000001 ", "99000001"),
        (99000001.0, "99000001"),
        (99000001.5, "99000001.5"),
        (None, None),
        ("", None),
        ("   ", None),
    ],
)
def test_br_carga_15_el_codigo_se_normaliza_a_texto(valor: object, codigo: str | None) -> None:
    assert normalizar_codigo(valor) == codigo


# BR-CARGA-16. Conciliación y publicación

@pytest.mark.parametrize("archivo", [CORRECTO, CON_ERROR])
def test_br_carga_16_las_cuentas_de_la_validacion_cuadran(archivo: str) -> None:
    validacion = _validar(_leido(archivo))
    leidas, aceptadas, rechazadas = _cuentas(validacion)
    assert leidas == validacion.filas_de_datos == 11
    assert aceptadas + rechazadas == leidas
    assert len({r.fila_origen for r in validacion.rechazos_de_fila}) == rechazadas
    assert all(len(f.mediciones) == len(validacion.columnas) == 3 for f in validacion.filas_aceptadas)


def test_br_carga_16_si_todas_las_filas_se_rechazan_la_carga_no_es_publicable(
    generador: ModuleType, tmp_path: Path
) -> None:
    export = _export(generador)
    for fila in range(2, 13):
        export = generador.con_celda(export, fila, "5.2", 5)
    validacion = _validar(_libro(generador, export, tmp_path))
    assert validacion.rechazo_de_carga is None
    assert _cuentas(validacion) == (11, 0, 11)
    assert validacion.rechazos_de_fila == tuple(
        Rechazo(Motivo.NIVEL_FUERA_DE_ESCALA, Efecto.RECHAZA_FILA, fila, "5.2") for fila in range(2, 13)
    )
    assert not validacion.publicable


def test_br_carga_16_una_fila_vacia_entre_filas_con_datos_queda_rechazada_por_codigo_vacio(
    generador: ModuleType, tmp_path: Path
) -> None:
    export = _export(generador)
    export = generador.Export(export.hoja, export.encabezado, export.filas[:10] + ((None,) * 27,) + export.filas[10:])
    validacion = _validar(_libro(generador, export, tmp_path))
    assert (validacion.filas_de_datos, *_cuentas(validacion)) == (12, 12, 11, 1)
    assert validacion.rechazos_de_fila == (Rechazo(Motivo.CODIGO_VACIO, Efecto.RECHAZA_FILA, 12, None),)
    assert validacion.filas_aceptadas[-1].fila_origen == 13


# BR-CARGA-17. Ni el valor leído ni los nombres salen de la validación

def test_br_carga_17_ningun_rechazo_trae_el_valor_leido(generador: ModuleType, tmp_path: Path) -> None:
    validacion = _validar(
        _libro(generador, generador.con_celda(_export(generador), 3, "5.2", "Needs Grading"), tmp_path)
    )
    assert [campo.name for campo in fields(Rechazo)] == ["motivo", "efecto", "fila_origen", "pi_codigo"]
    assert validacion.rechazos_de_fila == (Rechazo(Motivo.NIVEL_NO_NUMERICO, Efecto.RECHAZA_FILA, 3, "5.2"),)
    assert "Needs Grading" not in repr(validacion)


def test_br_carga_17_la_validacion_no_muestra_codigos_ni_nombres() -> None:
    validacion = _validar(_leido(CON_ERROR))
    representacion = repr(validacion)
    assert not any(texto in representacion for texto in ("Inventado", "Estudiante", "99000001"))
    assert isinstance(validacion.filas_aceptadas[0], FilaAceptada)
    assert repr(validacion.filas_aceptadas[0]) == "FilaAceptada(fila_origen=2)"
