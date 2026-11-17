"""Validación en memoria del export leído (T032 de specs/001-mvp-carga-r17/tasks.md).

Aplica las reglas de negocio (business rules, BR) BR-CARGA-07 y BR-CARGA-11 a BR-CARGA-16 de
specs/features/carga-export/carga-export.spec.md sobre un LibroLeido, sin tocar la base. Las
decisiones abiertas de la carrera van con su valor provisional y su identificador de la spec 001.

guardia(libro) detiene el archivo entero con CodigoNoInventado si un código no vacío de la columna
del código no va de 99000000 a 99999999, también si está mal formado como 9900001 (BR-CARGA-07).
cargar() la llama solo con GUARDIA_DATOS_INVENTADOS=1 y antes de buscar la huella en la base, como
pide el paso 5 de BR-CARGA-03, así que validar() no la repite.

validar(libro, contexto) sigue los pasos 8 y 9 de BR-CARGA-03.
1. La sección declarada. La hoja de Blackboard tiene la forma gc_<curso_blackboard>_f, con el sufijo
   que Blackboard puede cortar a 31 caracteres, y el nombre del archivo la forma
   gc_<curso_blackboard>_fullgc_<fecha>.xlsx, .csv o .xls, sin distinguir mayúsculas en la extensión
   (spec 003, US-30). Un export de texto no tiene hoja, así que su sección sale solo del nombre. Los
   tres últimos segmentos numéricos del curso dan el periodo (20262 es 2026-2), la asignatura y la
   sección (propuesta, la regla de lectura). Manda la
   hoja, y el nombre solo cuenta si la hoja no declara nada. Si ninguno declara la sección,
   validar() lanza SeccionSinDeclarar, el 422 sin rastro del corte 1 (valor provisional de D-02).
2. La carga entera queda rechazada por el primer defecto en este orden, sección o asignatura
   distinta (SECCION_NO_COINCIDE, que manda también cuando difiere el periodo), periodo distinto
   (PERIODO_NO_COINCIDE), ninguna fila de datos (ARCHIVO_SIN_FILAS), ni Username ni Student ID
   (COLUMNA_CODIGO_AUSENTE), un indicador de desempeño (performance indicator, PI) del plan sin
   columna (PI_DEL_PLAN_AUSENTE) y un PI del plan en dos columnas (PI_REPETIDO). Entre varios PI manda
   el primero en el orden natural del plan, en el que 5.9 va antes que 5.10 (propuesta). Un PI que no
   está en el plan no rechaza la carga aunque se repita, porque su columna no entra.
3. Las columnas de los PI del plan entran a la carga con su posición, su encabezado, su número de
   Blackboard y su Total Pts. Un Total Pts distinto de 4 deja el aviso PUNTAJE_MAXIMO_DISTINTO y la
   carga sigue (valor provisional de D-04). El aviso compara el valor que guarda la base, así que
   4,004 pasa como 4,00, y un Total Pts que la base no guarda, como 0, deja la columna sin puntaje y
   el aviso igual. Una columna de un PI fuera del plan se ignora con el aviso
   COLUMNA_PI_FUERA_DEL_PLAN.
4. Una celda inválida rechaza la fila completa con RECHAZA_FILA, y el estudiante sale de todos los PI
   de la carga (valor provisional de D-01). Manda la primera celda inválida en el orden código y
   columnas del plan de izquierda a derecha. Un código vacío da CODIGO_VACIO, uno que no tiene 8
   cifras da CODIGO_INVALIDO y uno repetido da CODIGO_DUPLICADO en su segunda aparición, aunque la
   primera quede rechazada por un nivel (propuesta). Un nivel entero fuera de 1 a 4, como -1, 0 o 5,
   da NIVEL_FUERA_DE_ESCALA (valor provisional de D-06), y un valor que no es un entero escrito con
   cifras del 0 al 9, como «3,5», «Needs Grading», «-» o «NP», da NIVEL_NO_NUMERICO (valor provisional
   de D-03). Un texto vale el entero con uno o dos ceros decimales tras «.» o «,», como «3.00», «3,00»
   o «4.0», mientras «3.50», «1,000» y «3.000» siguen sin ser niveles (spec 003, US-29). Un texto con
   más de cuatro cifras significativas queda fuera de la escala sin convertirse a entero, porque
   int() lanza ValueError desde las 4 300 cifras. Una celda de PI vacía no rechaza la fila y se
   guarda SIN_EVIDENCIA.
5. Si hay filas aceptadas y ninguna trae un nivel en las columnas de los PI del plan, la carga entera
   queda rechazada con SIN_CALIFICACIONES y RECHAZA_CARGA, con la forma del paso 2 (spec 003, US-36 y
   D-31). Si ninguna fila se acepta, la carga sigue sin ser publicable, con sus rechazos de fila.

Ningún Rechazo lleva el valor leído, y las filas aceptadas ocultan su código y sus niveles en la
representación (BR-CARGA-17).
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Sequence

from abet_carga.modelos import (
    CodigoNoInventado,
    ColumnaDelPlan,
    ContextoSeccion,
    Efecto,
    FilaAceptada,
    FilaLeida,
    LibroLeido,
    MedicionAceptada,
    Motivo,
    PiDelPlan,
    Rechazo,
    SeccionDeclarada,
    SeccionSinDeclarar,
    Validacion,
    es_celda_vacia,
)

NIVELES = range(1, 5)
PUNTAJE_ESPERADO = 4

_CODIGO = re.compile(r"[0-9]{8}")
_CODIGO_INVENTADO = re.compile(r"99[0-9]{6}")
# Un nivel escrito como texto, con decimales nulos opcionales como «3.00», «3,00» o «4.0» (spec 003, D-03).
_ENTERO = re.compile(r"[+-]?(?P<cifras>[0-9]+)(?:[.,]0{1,2})?")
# Más cifras significativas que estas quedan fuera de la escala sin convertirse a entero, porque int()
# lanza ValueError desde las 4 300 cifras.
_CIFRAS_SIGNIFICATIVAS = 4
_FUERA_DE_ESCALA = 10_000
_CURSO = re.compile(r"(?:^|_)(?P<periodo>[0-9]{4}[0-2])_(?P<asignatura>[0-9]{6}|[0-9]{4})_(?P<seccion>[0-9]{1,5})$")
_NOMBRE_DE_BLACKBOARD = re.compile(r"gc_(?P<curso>.+)_fullgc_[^/\\]*\.(?i:xlsx|csv|xls)")


def normalizar_codigo(valor: object) -> str | None:
    """Código de la celda como texto sin espacios a los lados, o None si la celda está vacía.

    Un decimal sin fracción, como 99000001.0, pasa a sus cifras, y lo demás queda como texto para que
    la guardia y la validación decidan si son 8 cifras.
    """
    if es_celda_vacia(valor):
        return None
    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))
    return str(valor).strip()


def guardia(libro: LibroLeido) -> None:
    """Lanza CodigoNoInventado con la primera fila cuyo código no vacío no va de 99000000 a 99999999."""
    for fila in libro.filas:
        codigo = normalizar_codigo(fila.codigo)
        if codigo is not None and not _CODIGO_INVENTADO.fullmatch(codigo):
            raise CodigoNoInventado(fila.fila_origen)


def seccion_declarada(hoja: str | None, nombre_archivo: str) -> SeccionDeclarada | None:
    """Periodo, asignatura y sección que declara la hoja o, si la hoja no los declara, el nombre del archivo.

    hoja es None en un export de texto, que no tiene hoja, y entonces solo cuenta el nombre. La
    constancia la usa también para nombrar la sección o el periodo del archivo en el mensaje de
    una carga rechazada, desde archivo_origen.hoja y archivo_origen.nombre_archivo.
    """
    return _declarada_por(_curso_de_la_hoja(hoja)) or _declarada_por(_curso_del_nombre(nombre_archivo))


def validar(libro: LibroLeido, contexto: ContextoSeccion) -> Validacion:
    """Valida el export en memoria, o lanza SeccionSinDeclarar si el archivo no declara su sección."""
    declarada = seccion_declarada(libro.hoja, libro.nombre_archivo)
    if declarada is None:
        raise SeccionSinDeclarar()
    rechazo = _rechazo_de_carga(libro, contexto, declarada)
    if rechazo is not None:
        return Validacion(filas_de_datos=libro.filas_de_datos, rechazo_de_carga=rechazo)
    columnas, avisos = _columnas(libro, contexto)
    aceptadas, rechazos = _filas(libro, columnas)
    if aceptadas and not any(medicion.nivel is not None for fila in aceptadas for medicion in fila.mediciones):
        return Validacion(filas_de_datos=libro.filas_de_datos, rechazo_de_carga=_de_carga(Motivo.SIN_CALIFICACIONES))
    return Validacion(
        filas_de_datos=libro.filas_de_datos,
        columnas=columnas,
        filas_aceptadas=aceptadas,
        rechazos_de_fila=rechazos,
        avisos=avisos,
    )


def _curso_de_la_hoja(hoja: str | None) -> str | None:
    if hoja is None or not hoja.startswith("gc_"):
        return None
    curso = hoja.removeprefix("gc_")
    for sufijo in ("_f", "_"):
        if curso.endswith(sufijo):
            return curso.removesuffix(sufijo)
    return curso


def _curso_del_nombre(nombre_archivo: str) -> str | None:
    coincidencia = _NOMBRE_DE_BLACKBOARD.fullmatch(nombre_archivo)
    return coincidencia["curso"] if coincidencia else None


def _declarada_por(curso: str | None) -> SeccionDeclarada | None:
    coincidencia = _CURSO.search(curso) if curso else None
    if coincidencia is None:
        return None
    periodo = coincidencia["periodo"]
    return SeccionDeclarada(
        periodo=f"{periodo[:4]}-{periodo[4]}",
        curso_codigo=coincidencia["asignatura"],
        seccion_codigo=str(int(coincidencia["seccion"])),
    )


def _rechazo_de_carga(libro: LibroLeido, contexto: ContextoSeccion, declarada: SeccionDeclarada) -> Rechazo | None:
    if (declarada.curso_codigo, declarada.seccion_codigo) != (contexto.curso_codigo, contexto.seccion_codigo):
        return _de_carga(Motivo.SECCION_NO_COINCIDE)
    if declarada.periodo != contexto.periodo:
        return _de_carga(Motivo.PERIODO_NO_COINCIDE)
    if not libro.filas:
        return _de_carga(Motivo.ARCHIVO_SIN_FILAS)
    if libro.columna_codigo is None:
        return _de_carga(Motivo.COLUMNA_CODIGO_AUSENTE)
    return _rechazo_por_columnas(libro, contexto)


def _rechazo_por_columnas(libro: LibroLeido, contexto: ContextoSeccion) -> Rechazo | None:
    veces = Counter(columna.pi_codigo for columna in libro.columnas_pi)
    plan = _en_orden(contexto.plan)
    ausente = next((pi.codigo for pi in plan if veces[pi.codigo] == 0), None)
    if ausente is not None:
        return _de_carga(Motivo.PI_DEL_PLAN_AUSENTE, ausente)
    repetido = next((pi.codigo for pi in plan if veces[pi.codigo] > 1), None)
    if repetido is not None:
        return _de_carga(Motivo.PI_REPETIDO, repetido)
    return None


def _en_orden(plan: Iterable[PiDelPlan]) -> list[PiDelPlan]:
    """Plan en el orden natural de sus códigos, que tienen la forma de ck_pi_codigo."""
    return sorted(plan, key=lambda pi: tuple(int(parte) for parte in pi.codigo.split(".")))


def _columnas(libro: LibroLeido, contexto: ContextoSeccion) -> tuple[tuple[ColumnaDelPlan, ...], tuple[Rechazo, ...]]:
    pi_id = {pi.codigo: pi.pi_id for pi in contexto.plan}
    columnas: list[ColumnaDelPlan] = []
    avisos: list[Rechazo] = []
    for columna in libro.columnas_pi:
        codigo = columna.pi_codigo or ""
        if codigo not in pi_id:
            avisos.append(Rechazo(Motivo.COLUMNA_PI_FUERA_DEL_PLAN, Efecto.AVISO, None, codigo))
            continue
        columnas.append(
            ColumnaDelPlan(
                pi_id=pi_id[codigo],
                pi_codigo=codigo,
                posicion=columna.posicion,
                encabezado=columna.encabezado,
                bb_columna_id=columna.bb_columna_id,
                puntaje_maximo_declarado=columna.puntaje_maximo_declarado,
            )
        )
        if columna.declara_puntaje and columna.puntaje_maximo_declarado != PUNTAJE_ESPERADO:
            avisos.append(Rechazo(Motivo.PUNTAJE_MAXIMO_DISTINTO, Efecto.AVISO, None, codigo))
    return tuple(columnas), tuple(avisos)


def _filas(
    libro: LibroLeido, columnas: Sequence[ColumnaDelPlan]
) -> tuple[tuple[FilaAceptada, ...], tuple[Rechazo, ...]]:
    del_plan = {columna.posicion for columna in columnas}
    celdas = [(i, c.pi_codigo or "") for i, c in enumerate(libro.columnas_pi) if c.posicion in del_plan]
    vistos: set[str] = set()
    aceptadas: list[FilaAceptada] = []
    rechazos: list[Rechazo] = []
    for fila in libro.filas:
        resultado = _revisar_fila(fila, celdas, vistos)
        if isinstance(resultado, Rechazo):
            rechazos.append(resultado)
        else:
            aceptadas.append(resultado)
    return tuple(aceptadas), tuple(rechazos)


def _revisar_fila(fila: FilaLeida, celdas: Sequence[tuple[int, str]], vistos: set[str]) -> FilaAceptada | Rechazo:
    codigo = normalizar_codigo(fila.codigo)
    if codigo is None:
        return _de_fila(Motivo.CODIGO_VACIO, fila)
    if not _CODIGO.fullmatch(codigo):
        return _de_fila(Motivo.CODIGO_INVALIDO, fila)
    if codigo in vistos:
        return _de_fila(Motivo.CODIGO_DUPLICADO, fila)
    vistos.add(codigo)
    mediciones = []
    for indice, pi_codigo in celdas:
        motivo, nivel = _nivel(fila.valores_pi[indice])
        if motivo is not None:
            return _de_fila(motivo, fila, pi_codigo)
        mediciones.append(MedicionAceptada(pi_codigo, nivel))
    return FilaAceptada(fila.fila_origen, codigo, tuple(mediciones))


def _nivel(valor: object) -> tuple[Motivo | None, int | None]:
    """Motivo por el que la celda rechaza la fila o, si no la rechaza, su nivel, que es None en una celda vacía."""
    if es_celda_vacia(valor):
        return None, None
    entero = _entero(valor)
    if entero is None:
        return Motivo.NIVEL_NO_NUMERICO, None
    if entero not in NIVELES:
        return Motivo.NIVEL_FUERA_DE_ESCALA, None
    return None, entero


def _entero(valor: object) -> int | None:
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if isinstance(valor, float):
        return int(valor) if valor.is_integer() else None
    if not isinstance(valor, str):
        return None
    coincidencia = _ENTERO.fullmatch(valor.strip())
    if coincidencia is None:
        return None
    cifras = coincidencia["cifras"].lstrip("0") or "0"
    if len(cifras) > _CIFRAS_SIGNIFICATIVAS:
        return _FUERA_DE_ESCALA
    return -int(cifras) if valor.strip().startswith("-") else int(cifras)


def _de_carga(motivo: Motivo, pi_codigo: str | None = None) -> Rechazo:
    return Rechazo(motivo, Efecto.RECHAZA_CARGA, None, pi_codigo)


def _de_fila(motivo: Motivo, fila: FilaLeida, pi_codigo: str | None = None) -> Rechazo:
    return Rechazo(motivo, Efecto.RECHAZA_FILA, fila.fila_origen, pi_codigo)
