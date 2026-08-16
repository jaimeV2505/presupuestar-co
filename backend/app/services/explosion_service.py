# -*- coding: utf-8 -*-
"""EXPLOSION DE INSUMOS — la lista de compras de la obra completa.

El presupuesto habla en actividades ("300 m2 de pañete"); la ferreteria vende
insumos ("bultos de cemento"). Este servicio recorre los items del presupuesto,
toma el desglose de los que nacieron del CONSTRUCTOR y consolida:

    cantidad_total(insumo) = Σ  cantidad_item × cantidad_insumo × (1 + desperdicio%)

Puro y determinista, como JARVIS: sin BD, sin red. El endpoint le pasa los
desgloses ya resueltos y (opcional) los precios de MIS proveedores para el
cruce "esta obra necesita $X en materiales segun TUS precios".
"""
from typing import Dict, List, Callable, Optional


def _num(v, default=0.0):
    if v is None or v == "":
        return default
    try:
        return float(str(v).replace(",", "."))
    except (ValueError, TypeError):
        return default


def explosion_de_insumos(items: List[Dict],
                         desglose_de: Callable[[Dict], Optional[Dict]],
                         precios_ref: Optional[Dict] = None) -> Dict:
    """
    items: los items del presupuesto (cantidad, descripcion, ...)
    desglose_de: resuelve el desglose {insumos:[{nombre,unidad,cantidad,precio,
                 desperdicio_pct}], mano_obra, herramienta...} de un item, o None
    precios_ref: {nombre_lower: {"precio": int, "proveedor": str, "fecha": str}}
                 — el mejor precio negociado del usuario por insumo (opcional)

    Devuelve la lista consolidada + el parte honesto de cobertura.
    """
    precios_ref = precios_ref or {}
    consolidado: Dict = {}   # (nombre_lower, unidad) -> acumulador
    explotados, sin_desglose = 0, []

    for it in items or []:
        cant_item = _num(it.get("cantidad"))
        d = desglose_de(it) if it else None
        if not d or not d.get("insumos") or cant_item <= 0:
            if cant_item > 0:
                sin_desglose.append(str(it.get("descripcion") or "Item")[:80])
            continue
        explotados += 1
        for ins in d["insumos"]:
            nombre = str(ins.get("nombre") or "").strip()
            if not nombre:
                continue
            unidad = str(ins.get("unidad") or "un").strip()
            desp = _num(ins.get("desperdicio_pct"))
            # cantidad del insumo por unidad del item, con su desperdicio
            por_unidad = _num(ins.get("cantidad")) * (1 + desp / 100)
            clave = (nombre.lower(), unidad.lower())
            acc = consolidado.setdefault(clave, {
                "nombre": nombre, "unidad": unidad,
                "cantidad": 0.0, "en_items": 0,
                "precio_apu": _num(ins.get("precio")) or None,
            })
            acc["cantidad"] += cant_item * por_unidad
            acc["en_items"] += 1

    insumos, total_estimado, con_precio = [], 0, 0
    for acc in consolidado.values():
        cantidad = round(acc["cantidad"], 2)
        ref = precios_ref.get(acc["nombre"].lower())
        precio = (ref or {}).get("precio") or acc["precio_apu"]
        subtotal = round(cantidad * precio) if precio else None
        if ref:
            con_precio += 1
        if subtotal:
            total_estimado += subtotal
        insumos.append({
            "nombre": acc["nombre"], "unidad": acc["unidad"],
            "cantidad": cantidad, "en_items": acc["en_items"],
            "precio": round(precio) if precio else None,
            "fuente_precio": ("mi_proveedor" if ref else ("apu" if acc["precio_apu"] else None)),
            "proveedor": (ref or {}).get("proveedor") or "",
            "fecha_precio": (ref or {}).get("fecha") or "",
            "subtotal": subtotal,
        })
    insumos.sort(key=lambda x: -(x["subtotal"] or 0))

    return {
        "insumos": insumos,
        "total_estimado": total_estimado,
        "n_insumos": len(insumos),
        "items_explotados": explotados,
        "items_sin_desglose": len(sin_desglose),
        "sin_desglose": sin_desglose[:12],
        "con_precio_negociado": con_precio,
    }
