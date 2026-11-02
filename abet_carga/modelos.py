"""Modelos compartidos de la biblioteca abet_carga (T031 a T035 de specs/001-mvp-carga-r17/tasks.md).

Son clases de datos inmutables y excepciones que usan el lector y la validación y, en las etapas que
siguen, la carga, la constancia y el R-17. Ninguna guarda nombres de estudiantes, accesos ni el valor
leído de una celda en un rechazo, como pide la regla de negocio (business rule, BR) BR-CARGA-17 de
specs/features/carga-export/carga-export.spec.md. Las clases que llevan valores leídos los ocultan
en su representación, así que un registro o una traza de error no los copia. Las columnas que
interesan son la del código del estudiante y las de los indicadores de desempeño (performance
indicators, PI) del plan de medición de la sección.

Las excepciones que heredan de ArchivoNoAdmitido son la respuesta 422 sin rastro en la base que fija
el contrato de la interfaz de programación de aplicaciones (application programming interface, API),
en docs/03-api/contrato.md del Front. Su atributo mensaje es el texto literal del contrato y nunca
lleva un código de estudiante ni el contenido del archivo.

La interfaz sigue la propuesta del plan de la demo con los ajustes que piden las reglas.
ColumnaLeida numera su posición desde 1, como carga_columna.posicion (BR-CARGA-14), en lugar de un
índice, y suma declara_puntaje por el aviso de D-04. LibroLeido suma nombre_archivo, porque
BR-CARGA-11 coteja la sección con el nombre del archivo cuando la hoja no la declara. Validacion
suma filas_de_datos, que la conciliación de BR-CARGA-16 compara con las filas leídas, y las columnas
del plan (ColumnaDelPlan) que entran a carga_columna. CodigoNoInventado y SeccionSinDeclarar son los
422 sin rastro de BR-CARGA-07 y BR-CARGA-11.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum, StrEnum


def es_celda_vacia(valor: object) -> bool:
    """Indica si una celda no trae valor o trae solo espacios."""
    return valor is None or (isinstance(valor, str) and not valor.strip())


class TipoColumna(StrEnum):
    """Tipo de una columna del export según su encabezado."""

    CODIGO = "CODIGO"
    PI = "PI"
    OTRA = "OTRA"


class MotivoIlegible(Enum):
    """Lista cerrada de motivos de un archivo que no se lee (BR-CARGA-04 y BR-CARGA-05).

    El valor de cada motivo es el mensaje del contrato. CONTENIDO_INFLADO cubre el tamaño
    descomprimido, la proporción de compresión y el número de partes del zip, y su límite y su texto
    son (propuesta) en la spec viva.
    """

    ARCHIVO_DEMASIADO_GRANDE = "El archivo supera el máximo de 1 MB."
    TIPO_NO_ADMITIDO = "Solo se admiten exports de Blackboard en formato .xlsx."
    CONTENIDO_NO_ES_LIBRO = "El contenido del archivo no es un libro de Excel aunque su nombre termine en .xlsx."
    PROTEGIDO_CON_CONTRASENA = "El archivo está protegido con contraseña. Guárdelo sin contraseña y súbalo."
    MACROS_O_VINCULOS = "El archivo trae macros o vínculos externos y no se admite."
    CONTENIDO_INFLADO = "El contenido del archivo supera el tamaño admitido al descomprimirse."
    NO_SE_PUDO_ABRIR = "No se pudo abrir el archivo. Descárguelo otra vez desde Blackboard."

    @property
    def mensaje(self) -> str:
        return self.value


class ArchivoNoAdmitido(Exception):
    """Archivo que la carga detiene con 422 antes de escribir nada en la base."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class ArchivoIlegible(ArchivoNoAdmitido):
    """Archivo que no se puede leer, con su motivo de MotivoIlegible (BR-CARGA-04 y BR-CARGA-05)."""

    def __init__(self, motivo: MotivoIlegible) -> None:
        super().__init__(motivo.mensaje)
        self.motivo = motivo


@dataclass(frozen=True)
class ColumnaLeida:
    """Columna del encabezado del export.

    posicion cuenta desde 1, como carga_columna.posicion. pi_codigo, bb_columna_id y
    puntaje_maximo_declarado solo existen en una columna de PI, y los dos últimos quedan en None
    cuando el encabezado no los trae o la base no los admitiría (BR-CARGA-14). declara_puntaje dice si
    el encabezado trae un Total Pts, quepa o no en la base, porque un Total Pts de 0 queda sin
    puntaje y deja igual el aviso PUNTAJE_MAXIMO_DISTINTO (valor provisional de D-04).
    """

    posicion: int
    encabezado: str
    tipo: TipoColumna
    pi_codigo: str | None = None
    bb_columna_id: str | None = None
    puntaje_maximo_declarado: Decimal | None = None
    declara_puntaje: bool = False


@dataclass(frozen=True)
class FilaLeida:
    """Fila de datos con su número en el archivo, el valor de la columna del código y los de las columnas de PI.

    valores_pi sigue el orden de LibroLeido.columnas_pi, con los valores tal como vienen. La
    representación muestra solo fila_origen, para que el código y los valores no lleguen a un
    registro ni a un mensaje (BR-CARGA-17).
    """

    fila_origen: int
    codigo: object = field(repr=False)
    valores_pi: tuple[object, ...] = field(repr=False)


@dataclass(frozen=True)
class LibroLeido:
    """Export leído, con el nombre del archivo sin ruta, la hoja, las columnas y las filas de datos.

    No trae los valores de Last Name, First Name, Last Access, Availability ni de las actividades,
    que el lector descarta al leer cada fila (BR-CARGA-17).
    """

    nombre_archivo: str
    hoja: str
    columnas: tuple[ColumnaLeida, ...]
    filas: tuple[FilaLeida, ...]

    @property
    def columna_codigo(self) -> ColumnaLeida | None:
        """Columna de la que sale el código del estudiante, o None si el archivo no la trae."""
        return next((c for c in self.columnas if c.tipo is TipoColumna.CODIGO), None)

    @property
    def columnas_pi(self) -> tuple[ColumnaLeida, ...]:
        """Columnas de PI en el orden del archivo, el mismo de FilaLeida.valores_pi."""
        return tuple(c for c in self.columnas if c.tipo is TipoColumna.PI)

    @property
    def filas_de_datos(self) -> int:
        """Filas de datos medidas antes de interpretarlas, la cifra de archivo_origen.filas_de_datos (BR-CARGA-16)."""
        return len(self.filas)


class Motivo(StrEnum):
    """Motivo de un rechazo o de un aviso, de la lista cerrada de ck_rechazo_fila_motivo en la versión de V1_09.

    La validación usa RECHAZA_FILA con CODIGO_VACIO, CODIGO_INVALIDO, CODIGO_DUPLICADO,
    NIVEL_FUERA_DE_ESCALA y NIVEL_NO_NUMERICO. Usa RECHAZA_CARGA con SECCION_NO_COINCIDE,
    PERIODO_NO_COINCIDE, ARCHIVO_SIN_FILAS, COLUMNA_CODIGO_AUSENTE, PI_DEL_PLAN_AUSENTE y PI_REPETIDO,
    y AVISO con COLUMNA_PI_FUERA_DEL_PLAN y PUNTAJE_MAXIMO_DISTINTO. SECCION_SIN_DECLARAR es el aviso
    del corte 2 (BR-CARGA-18), que la validación del corte 1 no produce.
    """

    CODIGO_VACIO = "CODIGO_VACIO"
    CODIGO_INVALIDO = "CODIGO_INVALIDO"
    CODIGO_DUPLICADO = "CODIGO_DUPLICADO"
    NIVEL_FUERA_DE_ESCALA = "NIVEL_FUERA_DE_ESCALA"
    NIVEL_NO_NUMERICO = "NIVEL_NO_NUMERICO"
    COLUMNA_PI_FUERA_DEL_PLAN = "COLUMNA_PI_FUERA_DEL_PLAN"
    PI_DEL_PLAN_AUSENTE = "PI_DEL_PLAN_AUSENTE"
    ARCHIVO_SIN_FILAS = "ARCHIVO_SIN_FILAS"
    SECCION_NO_COINCIDE = "SECCION_NO_COINCIDE"
    PUNTAJE_MAXIMO_DISTINTO = "PUNTAJE_MAXIMO_DISTINTO"
    COLUMNA_CODIGO_AUSENTE = "COLUMNA_CODIGO_AUSENTE"
    PI_REPETIDO = "PI_REPETIDO"
    PERIODO_NO_COINCIDE = "PERIODO_NO_COINCIDE"
    SECCION_SIN_DECLARAR = "SECCION_SIN_DECLARAR"


class Efecto(StrEnum):
    """Efecto de un rechazo, de la lista de ck_rechazo_fila_efecto."""

    RECHAZA_FILA = "RECHAZA_FILA"
    RECHAZA_CARGA = "RECHAZA_CARGA"
    AVISO = "AVISO"


class CodigoNoInventado(ArchivoNoAdmitido):
    """Código fuera de 99000000 a 99999999 en la columna del código (BR-CARGA-07).

    fila_origen es la primera fila que falla, y el mensaje la nombra sin mostrar el código.
    """

    def __init__(self, fila_origen: int) -> None:
        super().__init__(
            "El piloto solo admite códigos inventados, de 99000000 a 99999999. "
            f"Revise la fila {fila_origen}. No se guardó nada."
        )
        self.fila_origen = fila_origen


class SeccionSinDeclarar(ArchivoNoAdmitido):
    """Export cuya hoja y cuyo nombre no declaran la sección, que el corte 1 detiene (BR-CARGA-11 y D-02)."""

    def __init__(self) -> None:
        super().__init__(
            "El archivo no indica su sección. Sube el export de Blackboard sin cambiar el nombre de su hoja."
        )


_CODIGO_DE_PI = re.compile(r"[1-9][0-9]?\.[1-9][0-9]?")


@dataclass(frozen=True)
class PiDelPlan:
    """PI que el plan de medición pide a la sección, con su pi_id y su código de abet.pi."""

    pi_id: int
    codigo: str


@dataclass(frozen=True)
class ContextoSeccion:
    """Sección que elige el profesor, con su periodo como «2026-2», la asignatura, el número y el plan.

    seccion_codigo es abet.seccion.numero, sin ceros a la izquierda (ck_seccion_numero). El plan no
    puede venir vacío, repetir un PI ni traer un código distinto de los de abet.pi (ck_pi_codigo),
    porque cargar() responde 422 a una sección sin plan antes de validar (BR-CARGA-01) y la
    validación compara cada PI del plan con las columnas del archivo.
    """

    periodo: str
    curso_codigo: str
    seccion_codigo: str
    plan: tuple[PiDelPlan, ...]

    def __post_init__(self) -> None:
        codigos = [pi.codigo for pi in self.plan]
        if not codigos:
            raise ValueError("El plan de medición de la sección no trae ningún PI.")
        if len(set(codigos)) != len(codigos):
            raise ValueError("El plan de medición de la sección repite un PI.")
        if not all(_CODIGO_DE_PI.fullmatch(codigo) for codigo in codigos):
            raise ValueError("El plan de medición trae un código que no tiene la forma de abet.pi.")


@dataclass(frozen=True)
class SeccionDeclarada:
    """Periodo, asignatura y sección que declara la hoja o el nombre del archivo (BR-CARGA-11 y BR-CARGA-12)."""

    periodo: str
    curso_codigo: str
    seccion_codigo: str


@dataclass(frozen=True)
class Rechazo:
    """Rechazo o aviso, sin el valor leído (BR-CARGA-17).

    fila_origen solo existe en un RECHAZA_FILA. pi_codigo nombra el PI de la celda que rechaza la
    fila, el de la columna de un aviso, el PI del plan que falta (PI_DEL_PLAN_AUSENTE) o el que se
    repite (PI_REPETIDO), y queda en None en un rechazo por código, sección, periodo, falta de filas o
    falta de la columna del código. La carga guarda el PI de un rechazo de nivel y el de
    PUNTAJE_MAXIMO_DISTINTO como carga_columna_id, el de PI_DEL_PLAN_AUSENTE y PI_REPETIDO como
    rechazo_fila.pi_id, y no guarda el de COLUMNA_PI_FUERA_DEL_PLAN, porque esa columna no entra a
    carga_columna y ck_rechazo_fila_pi no admite el PI para ese motivo.
    """

    motivo: Motivo
    efecto: Efecto
    fila_origen: int | None = None
    pi_codigo: str | None = None


@dataclass(frozen=True)
class ColumnaDelPlan:
    """Columna de un PI del plan que entra a carga_columna, con su posición desde 1 (BR-CARGA-14)."""

    pi_id: int
    pi_codigo: str
    posicion: int
    encabezado: str
    bb_columna_id: str | None
    puntaje_maximo_declarado: Decimal | None


@dataclass(frozen=True)
class MedicionAceptada:
    """Nivel de un PI en una fila aceptada. None es una celda vacía, que se guarda SIN_EVIDENCIA (BR-CARGA-15)."""

    pi_codigo: str
    nivel: int | None

    @property
    def estado_evidencia(self) -> str:
        """Valor de abet.medicion.estado_evidencia, CALIFICADO con nivel y SIN_EVIDENCIA sin él."""
        return "CALIFICADO" if self.nivel is not None else "SIN_EVIDENCIA"


@dataclass(frozen=True)
class FilaAceptada:
    """Fila aceptada con su código de 8 cifras como texto y una medición por cada columna del plan.

    Las mediciones siguen el orden de Validacion.columnas. La representación muestra solo
    fila_origen (BR-CARGA-17).
    """

    fila_origen: int
    codigo: str = field(repr=False)
    mediciones: tuple[MedicionAceptada, ...] = field(repr=False)


@dataclass(frozen=True)
class Validacion:
    """Resultado de validar el export en memoria, antes de la transacción de BR-CARGA-02.

    Con rechazo_de_carga, la carga queda RECHAZADA con efecto RECHAZA_CARGA, filas_leidas 0 y sin
    columnas, filas, mediciones ni avisos (BR-CARGA-13). Sin él, filas_leidas es filas_de_datos, las
    filas aceptadas y las rechazadas suman las leídas, y la carga es publicable si acepta al menos una
    fila (BR-CARGA-16).
    """

    filas_de_datos: int
    rechazo_de_carga: Rechazo | None = None
    columnas: tuple[ColumnaDelPlan, ...] = ()
    filas_aceptadas: tuple[FilaAceptada, ...] = ()
    rechazos_de_fila: tuple[Rechazo, ...] = ()
    avisos: tuple[Rechazo, ...] = ()

    @property
    def filas_leidas(self) -> int:
        return 0 if self.rechazo_de_carga is not None else self.filas_de_datos

    @property
    def filas_rechazadas(self) -> int:
        return len(self.rechazos_de_fila)

    @property
    def publicable(self) -> bool:
        return self.rechazo_de_carga is None and bool(self.filas_aceptadas)
