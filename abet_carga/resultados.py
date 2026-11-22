"""Regla de la meta y conversión de cifras de los logros por indicador (spec 004, BR-RESULTADOS-05 y BR-RESULTADOS-06).

Las reglas de negocio (business rules, BR) viven en specs/features/resultados/resultados.spec.md. Este módulo no lee
la base ni conoce FastAPI. Sus funciones son puras y las usan la ruta GET /api/resultados (app/rutas/resultados.py) y
el plan de acción del bloque II del R-17 (_plan_de_accion de abet_carga/r17.py), así que la pantalla P6 y el R-17 de
una carga deciden la meta con la misma regla.

1. en_meta() dice si el logro de un indicador de desempeño (performance indicator, PI) llega a la meta. Es verdadero
   cuando el porcentaje sobre los calificados es mayor o igual que la meta, falso cuando es menor y None cuando falta
   alguno de los dos, como en un PI sin calificaciones o en un conjunto de reglas sin META_LOGRO definida.
2. cifra() convierte un Decimal de abet.v_r17_por_pi, que la vista ya redondea a un decimal con ROUND(…, 1), en el
   número de JavaScript Object Notation (JSON) que viaja por la API, y deja None como None, nunca como 0.
"""

from __future__ import annotations

from decimal import Decimal


def en_meta(logro: Decimal | None, meta: Decimal | None) -> bool | None:
    """Si el logro llega a la meta o la supera, o None si falta el logro o la meta (BR-RESULTADOS-06)."""
    if logro is None or meta is None:
        return None
    return logro >= meta


def cifra(valor: Decimal | None) -> float | None:
    """Porcentaje o meta de la vista como número JSON, 63,6 como 63.6, y el nulo como None (BR-RESULTADOS-05)."""
    return float(valor) if valor is not None else None
