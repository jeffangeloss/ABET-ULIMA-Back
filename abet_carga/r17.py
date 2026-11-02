"""R-17, el reporte de medición de una sección, desde la carga publicada en la base (T035).

generar(conexion, carga_id, carpeta) escribe en carpeta el R-17 de una carga PUBLICADA y devuelve su
ruta. Cumple las reglas de negocio (business rules, BR) BR-R17-01 a BR-R17-09 de
specs/features/r17/r17.spec.md sobre plantillas/R017_ambiental_general.xlsx, con el mapa de celdas
de plantillas/README.md, y sirve a cualquier asignatura y sección del plan de medición. Lee con la
conexión que recibe, sin escribir en la base ni confirmar o deshacer su transacción.

1. Solo una carga PUBLICADA tiene R-17 (BR-R17-01). Una carga que no existe lanza
   constancia.CargaInexistente, y una que no está publicada lanza CargaNoPublicada, el 409 de la
   interfaz de programación de aplicaciones (application programming interface, API), antes de
   escribir ningún archivo.
2. Las cifras salen solo de abet.v_r17_por_pi (BR-R17-02). La cifra «7 de 11» divide
   n_esperado_o_superior entre n_total - n_sin_evidencia, porque la vista no expone los calificados
   (BR-R17-03). La descripción de cada indicador de desempeño (performance indicator, PI) sale de
   abet.pi, su instrumento del plan de medición y la tabla de estudiantes de abet.medicion de la
   carga, por PI y por fila de origen (BR-R17-08). Nada se recalcula del archivo subido, que la base
   no conserva.
3. Cada celda recibe un valor y nunca una fórmula (BR-R17-04). Un texto que llega de la petición,
   como el nombre del archivo o de la hoja, queda como texto aunque empiece por «=», y un carácter
   de control, que una hoja de Excel no admite, pasa a U+FFFD, el carácter de reemplazo. El
   logotipo vuelve desde plantillas/R017_logotipo.png con el ancla de la hoja original, y sin Pillow
   openpyxl lanza ImportError antes de escribir el archivo. Tres formatos condicionales de E24:F26
   perdieron patternType="none" al vaciar la plantilla, y su relleno automático se ve negro bajo la
   fuente roja en cuanto la celda tiene un porcentaje, así que r17.py lo pinta de blanco.
4. La franja PROVISIONAL, el sufijo _PROVISIONAL del nombre y «PROVISIONAL» en el título de las
   propiedades van si y solo si la vista lo dice (BR-R17-05 y BR-R17-06). La franja usa el texto que
   propone la spec y, si el conjunto está APROBADO pero le falta definir un parámetro de la vista,
   uno que no lo da por pendiente de aprobación (propuesta).
5. El autor y el último autor dicen «ABET_SIS_MED», y la fecha de creación es la de la generación
   (BR-R17-07). El correo de quien sube la carga va solo en la hoja «Constancia» (valor provisional
   de D-12).
6. Una carga con más de 142 mediciones o con más de 3 PI no cabe en las filas fijas y lanza
   SeccionSuperaPlantilla, el 422 de la API, en lugar de truncar la tabla o los bloques (BR-R17-08,
   propuesta). Más de 3 PI es posible con las asignaturas que tributan a dos o tres resultados del
   estudiante (student outcomes, SO), y la salida para ese caso la decide la coordinación (D-08).
7. La hoja «Constancia» va al final y repite la constancia de constancia.armar(), con la frase fija
   de BR-R17-09 al cierre. Las líneas de avisos y rechazos tienen la forma «PUNTAJE_MAXIMO_DISTINTO
   en el PI 5.3» y «Fila 3, PI 5.2, NIVEL_FUERA_DE_ESCALA, RECHAZA_FILA», con el mensaje al lado y
   sin el valor leído. La hoja se imprime en una página de ancho, con los rótulos junto a sus valores.

El conteo por nivel, la cifra entre paréntesis y el porcentaje sobre el total van en K28:Q31, la
zona libre que propone plantillas/README.md, y M24 a M26 repiten los conteos de la hoja original.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
from openpyxl import Workbook, load_workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.drawing.image import Image
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, TwoCellAnchor
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet
from psycopg.rows import dict_row

from abet_carga import constancia

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLA = RAIZ / "plantillas" / "R017_ambiental_general.xlsx"
LOGOTIPO = RAIZ / "plantillas" / "R017_logotipo.png"
HOJA = "Cursos de Carrera"
AUTOR = "ABET_SIS_MED"
FILAS_DEL_BLOQUE_I = (17, 18, 19)
FILAS_DEL_BLOQUE_II = (24, 25, 26)
FILAS_DE_FRECUENCIAS = (29, 30, 31)
PRIMERA_FILA_DE_LA_TABLA = 43
TOPE_DE_MEDICIONES = 142
TOPE_DE_PI = len(FILAS_DEL_BLOQUE_I)
FRASE_FINAL = ("Los números de este R-17 los calcula el sistema desde la carga registrada en la base, "
               "no desde fórmulas.")
# Los dos textos fijos que la fórmula de H24 a H26 de la hoja original elige (plantillas/README.md).
LOGRADO = "¡Felicidades! Logró alcanzar el indicador. Lo animamos a seguir mejorando con nuevas iniciativas."
NO_LOGRADO = "El indicador aún no alcanza lo esperado, pero es una buena oportunidad para mejorar"
ENCABEZADOS_DE_FRECUENCIAS = (
    "PI", "Nivel 1", "Nivel 2", "Nivel 3", "Nivel 4", "Logran / calificados", "% sobre el total",
)
# La fuente de la plantilla, que también nombran las celdas que r17.py resalta.
FUENTE = "Calibri"
BLANCO = "FFFFFFFF"
# Primeros caracteres con que Excel empieza una fórmula si alguien edita la celda.
_PREFIJOS_DE_FORMULA = ("=", "+", "-", "@")

_VISTA = """
SELECT periodo, codigo_asignatura, asignatura, seccion, carga_id, provisional, so, pi, n_nivel_1, n_nivel_2,
       n_nivel_3, n_nivel_4, n_esperado_o_superior, n_sin_evidencia, n_total, pct_logro_sobre_calificados,
       pct_logro_sobre_total_con_sin_evidencia, meta_logro_pct
FROM abet.v_r17_por_pi
WHERE carga_id = %s
ORDER BY so, CAST(split_part(pi, '.', 2) AS smallint)
"""

_PLAN = """
SELECT p.codigo, p.descripcion, i.nombre AS instrumento
FROM abet.carga c
JOIN abet.seccion s        ON s.seccion_id = c.seccion_id
JOIN abet.plan_medicion pm ON pm.periodo_id = s.periodo_id AND pm.asignatura_id = s.asignatura_id
                          AND pm.carrera_id = c.carrera_id
JOIN abet.pi p             ON p.pi_id = pm.pi_id
LEFT JOIN abet.instrumento i ON i.instrumento_id = pm.instrumento_id
WHERE c.carga_id = %s
"""

# Una fila más que el tope basta para saber que la tabla no cabe.
_MEDICIONES = """
SELECT p.so_numero, p.codigo AS pi, e.codigo AS estudiante, m.nivel_original
FROM abet.medicion m
JOIN abet.pi p         ON p.pi_id = m.pi_id
JOIN abet.estudiante e ON e.estudiante_id = m.estudiante_id
WHERE m.carga_id = %s
ORDER BY p.so_numero, p.numero, m.fila_origen
LIMIT %s
"""


class R17NoDisponible(Exception):
    """La carga no da R-17, con el mensaje y el código de la respuesta que fija el contrato de la API."""

    mensaje = ""
    codigo_http = 500

    def __init__(self) -> None:
        super().__init__(self.mensaje)


class CargaNoPublicada(R17NoDisponible):
    """La carga no está PUBLICADA (BR-R17-01, con el código 409 como propuesta)."""

    mensaje = "La carga no está publicada y no tiene R-17."
    codigo_http = 409


class SeccionSuperaPlantilla(R17NoDisponible):
    """La carga no cabe en las filas fijas de la plantilla (BR-R17-08, propuesta)."""

    mensaje = "La sección supera las filas de la plantilla del R-17."
    codigo_http = 422


def generar(conexion: psycopg.Connection, carga_id: int, carpeta: Path) -> Path:
    """Escribe el R-17 de la carga en carpeta y devuelve su ruta, o lanza la razón por la que no lo tiene."""
    cuerpo = constancia.armar(conexion, carga_id)
    filas = _leer(conexion, _VISTA, carga_id)
    if cuerpo["estado"] != "PUBLICADA" or not filas:
        raise CargaNoPublicada()
    if len(filas) > TOPE_DE_PI:
        raise SeccionSuperaPlantilla()
    mediciones = _leer(conexion, _MEDICIONES, carga_id, TOPE_DE_MEDICIONES + 1)
    if len(mediciones) > TOPE_DE_MEDICIONES:
        raise SeccionSuperaPlantilla()
    plan = {detalle["codigo"]: detalle for detalle in _leer(conexion, _PLAN, carga_id)}
    provisional = any(fila["provisional"] for fila in filas)
    libro = _libro(filas, plan, mediciones, cuerpo, provisional)
    ruta = carpeta / _nombre(filas[0], provisional)
    libro.save(ruta)
    return ruta


def _leer(conexion: psycopg.Connection, consulta: str, *parametros: object) -> list[dict[str, Any]]:
    with conexion.cursor(row_factory=dict_row) as cursor:
        return cursor.execute(consulta, parametros).fetchall()


def _nombre(fila: dict[str, Any], provisional: bool) -> str:
    # ck_asignatura_codigo, ck_seccion_numero y ck_periodo_codigo dejan solo cifras y guiones en el nombre.
    sufijo = "_PROVISIONAL" if provisional else ""
    return f"R017_{fila['codigo_asignatura']}_{fila['seccion']}_{fila['periodo']}{sufijo}.xlsx"


def _libro(
    filas: list[dict[str, Any]],
    plan: dict[str, dict[str, Any]],
    mediciones: list[dict[str, Any]],
    cuerpo: dict[str, Any],
    provisional: bool,
) -> Workbook:
    libro = load_workbook(PLANTILLA)
    hoja = libro[HOJA]
    _sin_rellenos_automaticos(hoja)
    _logotipo(hoja)
    _cabecera(hoja, filas)
    if provisional:
        _franja(hoja, cuerpo)
    _bloques(hoja, filas, plan)
    _frecuencias(hoja, filas)
    _tabla(hoja, mediciones)
    _hoja_constancia(libro.create_sheet("Constancia"), cuerpo, provisional)
    _propiedades(libro, filas[0], provisional)
    return libro


def _escribir(hoja: Worksheet, referencia: str, valor: object, formato: str | None = None) -> None:
    """Escribe un valor, nunca una fórmula, en la celda."""
    celda = hoja[referencia]
    if isinstance(valor, str):
        celda.value = ILLEGAL_CHARACTERS_RE.sub("\ufffd", valor)
        # openpyxl toma como fórmula un texto que empieza por «=», así que el tipo vuelve a texto.
        celda.data_type = "s"
        if valor.startswith(_PREFIJOS_DE_FORMULA):
            celda.quotePrefix = True
    else:
        celda.value = valor
    if formato is not None:
        celda.number_format = formato


def _sin_rellenos_automaticos(hoja: Worksheet) -> None:
    """Pinta de blanco el relleno automático que tres formatos condicionales de E24:F26 heredan de la plantilla.

    En la hoja original esos estilos traen patternType="none", que openpyxl lee como un valor vacío y
    no escribe, y sin él el relleno automático se ve negro bajo la fuente roja en cuanto la celda tiene
    un porcentaje. El blanco conserva la prioridad de cada regla y deja la celda como en la hoja
    original, que no tiene relleno propio.
    """
    for formato in hoja.conditional_formatting:
        for regla in formato.rules:
            relleno = regla.dxf.fill if regla.dxf is not None else None
            if relleno is not None and relleno.patternType is None and relleno.bgColor.type == "auto":
                regla.dxf.fill = PatternFill(bgColor=BLANCO)


def _logotipo(hoja: Worksheet) -> None:
    # El ancla de la hoja original, en unidades métricas inglesas (English Metric Units, EMU), de B1 a B4.
    imagen = Image(str(LOGOTIPO))
    imagen.anchor = TwoCellAnchor(editAs="oneCell", _from=AnchorMarker(col=1, colOff=19050, row=0, rowOff=0),
                                  to=AnchorMarker(col=1, colOff=744818, row=3, rowOff=140297))
    hoja.add_image(imagen)


def _cabecera(hoja: Worksheet, filas: list[dict[str, Any]]) -> None:
    primera = filas[0]
    cabecera = (("D8", "codigo_asignatura"), ("D9", "asignatura"), ("D11", "seccion"), ("I11", "periodo"))
    for referencia, clave in cabecera:
        _escribir(hoja, referencia, primera[clave])
    resultados = sorted({fila["so"] for fila in filas})
    _escribir(hoja, "B15", f"Student Outcome (SO) {constancia.lista([str(so) for so in resultados])}")


def _franja(hoja: Worksheet, cuerpo: dict[str, Any]) -> None:
    conjunto = cuerpo["conjunto_reglas"]
    if cuerpo["conjunto_reglas_estado"] == "APROBADO":
        texto = (f"R-17 PROVISIONAL. El conjunto de reglas {conjunto} está aprobado, pero no define todos los "
                 "parámetros que usa el R-17. No usar como evidencia oficial.")
    else:
        texto = (f"R-17 PROVISIONAL. Las reglas de la carrera (conjunto {conjunto}) aún no están aprobadas. "
                 "No usar como evidencia oficial.")
    hoja.merge_cells("B7:I7")
    _escribir(hoja, "B7", texto)
    hoja["B7"].font = Font(name=FUENTE, size=11, bold=True, color="FFC00000")
    hoja["B7"].fill = PatternFill(fill_type="solid", start_color="FFFFF2CC", end_color="FFFFF2CC")
    hoja["B7"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    hoja.row_dimensions[7].height = 30


def _bloques(hoja: Worksheet, filas: list[dict[str, Any]], plan: dict[str, dict[str, Any]]) -> None:
    for indice, fila in enumerate(filas):
        detalle = plan[fila["pi"]]
        bloque_i, bloque_ii = FILAS_DEL_BLOQUE_I[indice], FILAS_DEL_BLOQUE_II[indice]
        _escribir(hoja, f"B{bloque_i}", fila["pi"])
        _escribir(hoja, f"C{bloque_i}", detalle["descripcion"])
        _escribir(hoja, f"E{bloque_i}", detalle["instrumento"])
        _escribir(hoja, f"B{bloque_ii}", fila["pi"])
        _escribir(hoja, f"C{bloque_ii}", detalle["instrumento"])
        _escribir(hoja, f"E{bloque_ii}", _fraccion(fila["pct_logro_sobre_calificados"]), "0.0%")
        _escribir(hoja, f"G{bloque_ii}", _fraccion(fila["meta_logro_pct"]))
        _escribir(hoja, f"H{bloque_ii}", _plan_de_accion(fila))


def _plan_de_accion(fila: dict[str, Any]) -> str | None:
    logro, meta = fila["pct_logro_sobre_calificados"], fila["meta_logro_pct"]
    if logro is None or meta is None:
        return None
    return LOGRADO if logro >= meta else NO_LOGRADO


def _frecuencias(hoja: Worksheet, filas: list[dict[str, Any]]) -> None:
    for columna, rotulo in zip("KLMNOPQ", ENCABEZADOS_DE_FRECUENCIAS, strict=True):
        _escribir(hoja, f"{columna}28", rotulo)
        hoja[f"{columna}28"].font = Font(name=FUENTE, size=11, bold=True)
        # K y L traen su ancho de la plantilla; de M a Q la hoja original no fija ninguno.
        if columna in "MNOPQ":
            hoja.column_dimensions[columna].width = len(rotulo) + 3
    for numero, fila in zip(FILAS_DE_FRECUENCIAS, filas, strict=False):
        valores = (fila["pi"], fila["n_nivel_1"], fila["n_nivel_2"], fila["n_nivel_3"], fila["n_nivel_4"],
                   _logran(fila), _fraccion(fila["pct_logro_sobre_total_con_sin_evidencia"]))
        for columna, valor in zip("KLMNOPQ", valores, strict=True):
            _escribir(hoja, f"{columna}{numero}", valor)
            hoja[f"{columna}{numero}"].alignment = Alignment(horizontal="center")
        hoja[f"Q{numero}"].number_format = "0.0%"
    bajos = sum(fila["n_nivel_1"] + fila["n_nivel_2"] for fila in filas)
    altos = sum(fila["n_nivel_3"] + fila["n_nivel_4"] for fila in filas)
    _escribir(hoja, "M24", bajos)
    _escribir(hoja, "M25", altos)
    _escribir(hoja, "M26", altos / (bajos + altos) if bajos + altos else None)


def _logran(fila: dict[str, Any]) -> str | None:
    """«7 de 11», con los calificados como n_total - n_sin_evidencia (BR-R17-03)."""
    if fila["n_esperado_o_superior"] is None:
        return None
    return f"{fila['n_esperado_o_superior']} de {fila['n_total'] - fila['n_sin_evidencia']}"


def _tabla(hoja: Worksheet, mediciones: list[dict[str, Any]]) -> None:
    for numero, medicion in enumerate(mediciones, start=PRIMERA_FILA_DE_LA_TABLA):
        valores = (medicion["so_numero"], medicion["pi"], medicion["estudiante"], medicion["nivel_original"])
        for columna, valor in zip("BCEF", valores, strict=True):
            _escribir(hoja, f"{columna}{numero}", valor)


def _hoja_constancia(hoja: Worksheet, cuerpo: dict[str, Any], provisional: bool) -> None:
    autor = f"Subido por {cuerpo['subida_por']}" if cuerpo["subida_por"] else "Sin registro de quién subió la carga"
    filas: list[tuple[object, object]] = [("Constancia de la carga", None), (None, None), *_datos(cuerpo, provisional)]
    filas += [(autor, None)]
    oraciones = [1, len(filas)]
    filas += [(None, None), ("Avisos", len(cuerpo["avisos"]))]
    filas += [(_linea_de_aviso(aviso), aviso["mensaje"]) for aviso in cuerpo["avisos"]]
    filas += [("Rechazos de fila", len(cuerpo["rechazos"]))]
    filas += [(_linea_de_rechazo(rechazo), rechazo["mensaje"]) for rechazo in cuerpo["rechazos"]]
    filas += [(None, None), (FRASE_FINAL, None)]
    oraciones.append(len(filas))
    for numero, (rotulo, valor) in enumerate(filas, start=1):
        _escribir(hoja, f"A{numero}", rotulo)
        _escribir(hoja, f"B{numero}", valor)
        for columna in "AB":
            hoja[f"{columna}{numero}"].alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    # El título, el autor y la frase final son oraciones que ocupan las dos columnas.
    for numero in oraciones:
        hoja.merge_cells(start_row=numero, start_column=1, end_row=numero, end_column=2)
    hoja["A1"].font = Font(name=FUENTE, size=14, bold=True)
    hoja.column_dimensions["A"].width = 48
    hoja.column_dimensions["B"].width = 75
    # Una página A4 de ancho y tantas de alto como haga falta, para que rótulos y valores no se separen.
    hoja.page_setup.paperSize = hoja.PAPERSIZE_A4
    hoja.page_setup.fitToWidth = 1
    hoja.page_setup.fitToHeight = 0
    hoja.sheet_properties.pageSetUpPr.fitToPage = True


def _datos(cuerpo: dict[str, Any], provisional: bool) -> list[tuple[object, object]]:
    seccion = cuerpo["seccion"]
    cuentas = " / ".join(str(cuerpo[clave]) for clave in
                         ("filas_de_datos", "filas_leidas", "filas_aceptadas", "filas_rechazadas"))
    return [
        ("Carga", cuerpo["carga_id"]),
        ("Sección", f"{seccion['numero']} de {seccion['asignatura']} en {seccion['periodo']}"),
        ("Archivo", cuerpo["nombre_archivo"]),
        ("Hoja", cuerpo["hoja"]),
        ("Filas de datos / leídas / aceptadas / rechazadas", cuentas),
        ("Huella SHA-256", cuerpo["sha256"]),
        ("Estado", cuerpo["estado"]),
        ("Versión del programa", cuerpo["programa_version"]),
        ("Conjunto de reglas", f"{cuerpo['conjunto_reglas']} ({cuerpo['conjunto_reglas_estado']})"),
        ("Parámetros pendientes", constancia.lista(cuerpo["parametros_pendientes"]) or "Ninguno"),
        ("Carácter del R-17", "PROVISIONAL" if provisional else "OFICIAL"),
        ("Columnas de PI", constancia.lista([_columna(columna) for columna in cuerpo["columnas"]])),
        ("Inicio (hora de Lima)", cuerpo["iniciada_en"]),
        ("Fin (hora de Lima)", cuerpo["terminada_en"]),
    ]


def _columna(columna: dict[str, Any]) -> str:
    puntaje = columna["puntaje_maximo_declarado"]
    total = f"Total Pts {str(puntaje).replace('.', ',')}" if puntaje is not None else "sin Total Pts en la base"
    return f"{columna['pi']} ({total})"


def _linea_de_aviso(aviso: dict[str, Any]) -> str:
    return f"{aviso['motivo']} en el PI {aviso['pi']}" if aviso["pi"] else aviso["motivo"]


def _linea_de_rechazo(rechazo: dict[str, Any]) -> str:
    partes = [f"Fila {rechazo['fila']}"] if rechazo["fila"] is not None else []
    partes += [f"PI {rechazo['pi']}"] if rechazo["pi"] else []
    return ", ".join([*partes, rechazo["motivo"], rechazo["efecto"]])


def _propiedades(libro: Workbook, fila: dict[str, Any], provisional: bool) -> None:
    titulo = f"R-17 {fila['codigo_asignatura']} {fila['seccion']} {fila['periodo']}"
    libro.properties.title = f"{titulo} PROVISIONAL" if provisional else titulo
    libro.properties.creator = AUTOR
    libro.properties.lastModifiedBy = AUTOR
    # openpyxl guarda las fechas de las propiedades en hora universal y sin huso.
    libro.properties.created = datetime.now(timezone.utc).replace(tzinfo=None)


def _fraccion(porcentaje: Decimal | None) -> float | None:
    """Porcentaje de la vista, como 63,6, en la fracción que muestra el formato de Excel, 0,636."""
    return float(porcentaje / 100) if porcentaje is not None else None
