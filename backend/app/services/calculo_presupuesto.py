# -*- coding: utf-8 -*-
"""
Motor de calculo del presupuesto — LA parte que debe ser 100% correcta.

Regla tributaria colombiana (Art. 462-1 ET, contratos de construccion):
  - Subtotal directo = suma de items (cantidad x precio unitario)
  - A, I, U se calculan cada uno como % del subtotal directo
  - IVA en contratos de construccion con AIU: 19% SOLO sobre la Utilidad
  - IVA sin AIU (venta directa/otros): 19% sobre el subtotal

Todos los calculos con redondeo a peso entero al final de cada componente.
"""
from typing import List, Dict


def calcular_totales(items: List[Dict], aiu: Dict) -> Dict:
    """
    items: [{cantidad, precio_unitario, ...}]
    aiu: {admin: 15, imprevistos: 5, utilidad: 8, aplicar: true, iva_sobre_utilidad: true}

    Retorna todos los componentes del presupuesto.
    """
    subtotal = 0.0
    for it in items:
        cant = _num(it.get("cantidad"))
        precio = _num(it.get("precio_unitario"))
        subtotal += cant * precio
    subtotal = round(subtotal)

    aplicar_aiu = bool(aiu.get("aplicar", True))
    pct_a = float(aiu.get("admin", 15) or 0)
    pct_i = float(aiu.get("imprevistos", 5) or 0)
    pct_u = float(aiu.get("utilidad", 8) or 0)
    iva_sobre_utilidad = bool(aiu.get("iva_sobre_utilidad", True))

    if aplicar_aiu:
        val_a = round(subtotal * pct_a / 100)
        val_i = round(subtotal * pct_i / 100)
        val_u = round(subtotal * pct_u / 100)
        base_con_aiu = subtotal + val_a + val_i + val_u

        if iva_sobre_utilidad:
            # Art. 462-1 ET: contratos de construccion — IVA solo sobre la utilidad
            iva = round(val_u * 0.19)
            regimen_iva = "IVA 19% sobre utilidad (Art. 462-1 ET — contratos de construccion)"
        else:
            iva = round(base_con_aiu * 0.19)
            regimen_iva = "IVA 19% sobre base + AIU"
    else:
        val_a = val_i = val_u = 0
        base_con_aiu = subtotal
        iva = round(subtotal * 0.19) if bool(aiu.get("con_iva", False)) else 0
        regimen_iva = "IVA 19% sobre subtotal" if iva else "Sin IVA"

    total = base_con_aiu + iva

    # ── F3: Incidencia por capitulo (el ojo del presupuestador senior) ──────
    # % que pesa cada capitulo sobre el costo directo — detecta errores gruesos
    # ("¿cimentacion al 2%? falta algo") de un vistazo.
    por_cap: Dict[str, int] = {}
    for it in items:
        v = round((_num(it.get("cantidad")) or 0) * (_num(it.get("precio_unitario")) or 0))
        cap = str(it.get("capitulo") or "OTROS")
        por_cap[cap] = por_cap.get(cap, 0) + v
    capitulos = sorted(
        [{"capitulo": k, "valor": v,
          "pct": round(v * 100 / subtotal, 1) if subtotal else 0}
         for k, v in por_cap.items()],
        key=lambda x: -x["valor"])

    # ── F7: Descuento de negociacion (prorrateado, con precio de lista) ─────
    # El descuento vive en los items (precio_lista = antes, precio_unitario =
    # pactado): los APUs quedan honestos, la cadena del dinero no se bifurca.
    subtotal_lista = 0
    for it in items:
        cant = _num(it.get("cantidad")) or 0
        pu = _num(it.get("precio_unitario")) or 0
        pl = _num(it.get("precio_lista")) or 0
        subtotal_lista += round(cant * (pl if pl > pu else pu))
    descuento_valor = max(0, subtotal_lista - subtotal)
    descuento_pct = round(descuento_valor * 100 / subtotal_lista, 1) if subtotal_lista else 0

    return {
        "subtotal_directo": subtotal,
        "admin_pct": pct_a, "admin_valor": val_a,
        "imprevistos_pct": pct_i, "imprevistos_valor": val_i,
        "utilidad_pct": pct_u, "utilidad_valor": val_u,
        "aiu_total": val_a + val_i + val_u,
        "base_con_aiu": base_con_aiu,
        "iva": iva,
        "regimen_iva": regimen_iva,
        "total": total,
        "num_items": len(items),
        "capitulos": capitulos,
        "subtotal_lista": subtotal_lista,
        "descuento_valor": descuento_valor,
        "descuento_pct": descuento_pct,
    }


def _num(v, default=0.0):
    if v is None or v == "":
        return default
    try:
        return float(str(v).replace(",", "."))
    except (ValueError, TypeError):
        return default


def validar_item(item: Dict) -> Dict:
    """Sanea un item del presupuesto. Garantiza tipos correctos."""
    def _f(v, default=0.0):
        if v is None or v == "":
            return default
        try:
            return float(str(v).replace(",", "."))
        except (ValueError, TypeError):
            return default

    return {
        "id": str(item.get("id") or "")[:40],
        "codigo": str(item.get("codigo") or "")[:20],
        "capitulo": str(item.get("capitulo") or item.get("categoria") or "OTROS")[:80],
        "descripcion": str(item.get("descripcion") or item.get("nombre") or "Item")[:250],
        "unidad": str(item.get("unidad") or "un")[:10],
        "cantidad": max(0.0, _f(item.get("cantidad"))),
        "precio_unitario": max(0.0, _f(item.get("precio_unitario") or item.get("precio"))),
        "precio_lista": max(0.0, _f(item.get("precio_lista"))) or None,  # F7: precio antes del descuento
        "apu_id": int(item["apu_id"]) if str(item.get("apu_id") or "").isdigit() else None,  # F1: enlace al desglose
        "precio_editado": bool(item.get("precio_editado", False)),
        "notas": str(item.get("notas") or "")[:300],
        "calc": _validar_calc(item.get("calc")),
    }


def _validar_calc(calc) -> Dict:
    """Persiste los datos de la calculadora de cantidades (largo/ancho/alto/n)."""
    if not isinstance(calc, dict):
        return None
    out = {}
    for k in ("largo", "ancho", "alto", "n"):
        v = calc.get(k)
        if v is not None and v != "":
            try:
                out[k] = float(str(v).replace(",", "."))
            except (ValueError, TypeError):
                pass
    return out or None


def validar_items(items: List) -> List[Dict]:
    if not isinstance(items, list):
        return []
    return [validar_item(it) for it in items if isinstance(it, dict)][:500]
