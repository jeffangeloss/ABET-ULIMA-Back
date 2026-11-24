"""Meta, cifras, semáforo y hallazgo por indicador (specs 004 y 005).

Las reglas de la meta y de las cifras viven en specs/features/resultados/resultados.spec.md. Este módulo no lee
la base ni conoce FastAPI. Sus funciones son puras y las usan la ruta GET /api/resultados (app/rutas/resultados.py) y
el plan de acción del bloque II del R-17 (_plan_de_accion de abet_carga/r17.py), así que la pantalla P6 y el R-17 de
una carga deciden la meta con la misma regla.

1. en_meta() dice si el logro de un indicador de desempeño (performance indicator, PI) llega a la meta. Es verdadero
   cuando el porcentaje sobre los calificados es mayor o igual que la meta, falso cuando es menor y None cuando falta
   alguno de los dos, como en un PI sin calificaciones o en un conjunto de reglas sin META_LOGRO definida.
2. cifra() convierte un Decimal de abet.v_r17_por_pi, que la vista ya redondea a un decimal con ROUND(…, 1), en el
   número de JavaScript Object Notation (JSON) que viaja por la API, y deja None como None, nunca como 0.
3. semaforo() usa en_meta() y el corte rojo. Por debajo de la meta, solo hay AMBAR si el corte está definido
   y el logro lo alcanza. tipo_de_registro() asigna el tipo de registro a cada color.
4. redactar_hallazgo() expresa el logro y la meta con un decimal y nombra el nivel esperado según la escala
   de la celda B40 del R-17. Si las reglas están incompletas, ese aviso tiene prioridad sobre la falta de calificaciones.
   Las reglas del semáforo, del registro y del hallazgo están en specs/features/mejora/mejora.spec.md.
"""

from __future__ import annotations

from decimal import Decimal

ESCALA = {1: "No satisfactorio", 2: "En proceso", 3: "Satisfactorio", 4: "Sobresaliente"}


def en_meta(logro: Decimal | None, meta: Decimal | None) -> bool | None:
    """Si el logro llega a la meta o la supera, o None si falta el logro o la meta (BR-RESULTADOS-06)."""
    if logro is None or meta is None:
        return None
    return logro >= meta


def cifra(valor: Decimal | None) -> float | None:
    """Porcentaje o meta de la vista como número JSON, 63,6 como 63.6, y el nulo como None (BR-RESULTADOS-05)."""
    return float(valor) if valor is not None else None


def semaforo(logro: Decimal | None, meta: Decimal | None, corte: Decimal | None) -> str:
    """VERDE, AMBAR, ROJO o SIN_DATO del indicador; corte None (CORTE_ROJO PENDIENTE) nunca da AMBAR (BR-MEJORA-02)."""
    if logro is None or meta is None:
        return "SIN_DATO"
    if en_meta(logro, meta):
        return "VERDE"
    if corte is not None and logro >= corte:
        return "AMBAR"
    return "ROJO"


def tipo_de_registro(semaforo: str) -> str | None:
    """BUENA_PRACTICA para VERDE, OPORTUNIDAD_MEJORA para AMBAR y ROJO, None para SIN_DATO (BR-MEJORA-03)."""
    if semaforo == "VERDE":
        return "BUENA_PRACTICA"
    if semaforo in ("AMBAR", "ROJO"):
        return "OPORTUNIDAD_MEJORA"
    return None


def redactar_hallazgo(pi: str, logro: Decimal | None, meta: Decimal | None, nivel_esperado: int | None) -> str:
    """Texto del hallazgo de un PI con coma decimal y un decimal; sin punto final solo en el caso con cifras."""
    if meta is None or nivel_esperado is None:
        return f"{pi}: el conjunto de reglas no define la meta o el nivel esperado."
    if logro is None:
        return f"{pi}: sin calificaciones en esta carga."
    logro_pct = f"{logro:.1f}".replace(".", ",")
    meta_pct = f"{meta:.1f}".replace(".", ",")
    return f"{pi}: {logro_pct} % en {ESCALA[nivel_esperado]} o más, meta {meta_pct} %"
