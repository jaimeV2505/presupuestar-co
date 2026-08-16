# -*- coding: utf-8 -*-
"""Constructor de APU propio: composicion determinista del precio unitario
a partir de insumos + mano de obra + herramienta. La misma filosofia de JARVIS:
el calculo es puro, testeable en el smoke, y la UI solo lo consume."""


def componer_precio(insumos: list, mano_obra: int = 0, herramienta_pct: float = 0) -> dict:
    """
    insumos: [{nombre, unidad, cantidad, precio, desperdicio_pct?}]
    mano_obra: valor de MO por unidad del APU (COP)
    herramienta_pct: % sobre la mano de obra (practica estandar: 3-10%)
    Devuelve el desglose completo con el precio unitario compuesto.
    """
    detalle = []
    total_materiales = 0.0
    for i in insumos or []:
        cant = float(i.get("cantidad") or 0)
        precio = float(i.get("precio") or 0)
        desp = float(i.get("desperdicio_pct") or 0)
        if cant < 0 or precio < 0 or desp < 0 or desp > 50:
            raise ValueError("Insumo con valores fuera de rango")
        parcial = cant * precio * (1 + desp / 100)
        total_materiales += parcial
        detalle.append({
            "nombre": str(i.get("nombre") or "")[:160],
            "unidad": str(i.get("unidad") or "un")[:15],
            "cantidad": cant, "precio": round(precio),
            "desperdicio_pct": desp, "parcial": round(parcial),
        })
    mo = max(0, int(mano_obra or 0))
    if herramienta_pct < 0 or herramienta_pct > 30:
        raise ValueError("Herramienta fuera de rango (0-30%)")
    herramienta = mo * herramienta_pct / 100
    total = total_materiales + mo + herramienta
    return {
        "insumos": detalle,
        "materiales": round(total_materiales),
        "mano_obra": mo,
        "herramienta_pct": herramienta_pct,
        "herramienta": round(herramienta),
        "precio_unitario": round(total),
    }
