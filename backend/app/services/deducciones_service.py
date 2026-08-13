# -*- coding: utf-8 -*-
"""DEDUCCIONES DE LEY — obra publica.
La entidad retiene de CADA acta: contribucion especial de obra publica del 5%
(Ley 1106/2006 art. 6, permanente por Ley 1738/2014 art. 8), estampillas
territoriales (varian por departamento/municipio) y retenciones tributarias.
El neto real del ingeniero es DESPUES de esto — aqui vive esa verdad."""

MAX_DEDUCCIONES = 10

SUGERIDAS = [
    {"nombre": "Contribución obra pública 5% (Ley 1106/2006)", "pct": 5.0},
    {"nombre": "Estampillas territoriales", "pct": 4.0},
    {"nombre": "Retefuente construcción", "pct": 2.0},
]


def validar_deducciones(lista) -> list:
    """Limpia y acota: nombre 2-120 chars, pct 0-25, maximo 10 lineas."""
    out = []
    for d in (lista or [])[:MAX_DEDUCCIONES]:
        nombre = str(d.get("nombre") or "").strip()[:120]
        try:
            pct = float(d.get("pct") or 0)
        except (TypeError, ValueError):
            raise ValueError("Porcentaje de deduccion invalido")
        if len(nombre) < 2:
            raise ValueError("Cada deduccion necesita un nombre")
        if pct < 0 or pct > 25:
            raise ValueError("Cada deduccion debe estar entre 0% y 25%")
        out.append({"nombre": nombre, "pct": pct})
    if sum(d["pct"] for d in out) > 50:
        raise ValueError("Las deducciones no pueden superar el 50% del corte")
    return out


def aplicar_deducciones(valor_corte: int, lista: list) -> dict:
    """Aplica cada deduccion sobre el valor del corte (redondeo por linea,
    como liquida la entidad). Determinista y testeable."""
    detalle = []
    total = 0
    for d in validar_deducciones(lista):
        v = round(valor_corte * d["pct"] / 100)
        detalle.append({"nombre": d["nombre"], "pct": d["pct"], "valor": v})
        total += v
    return {"detalle": detalle, "total": total}
