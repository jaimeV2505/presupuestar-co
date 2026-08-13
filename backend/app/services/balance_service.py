# -*- coding: utf-8 -*-
"""BALANCE DE OBRA — oficial vs ejecutado, la feature estrella del sector publico.
Puro y determinista: items efectivos (contrato + adicionales aprobados) x % de avance
x actas emitidas -> el tablero que el ingeniero arma en Excel cada corte."""


def balance_de_obra(items_efectivos: list, pct_por_item: dict, cuentas: list) -> dict:
    """
    items_efectivos: [{id, descripcion, unidad, cantidad, precio_unitario, capitulo?}]
                     (los adicionales llegan con id 'ot{n}:...' — asi los distinguimos)
    pct_por_item:    {item_id: pct_actual 0-100}  (el estado MAS RECIENTE de cada actividad)
    cuentas:         [{"total": int, "pagada": bool}]  (actas parciales emitidas)
    """
    filas = []
    valor_base = 0
    valor_adicionales = 0
    ejecutado = 0
    for it in items_efectivos or []:
        iid = str(it.get("id") or "")
        cant = float(it.get("cantidad") or 0)
        pu = float(it.get("precio_unitario") or 0)
        valor = round(cant * pu)
        pct = max(0.0, min(100.0, float(pct_por_item.get(iid, 0))))
        v_ejec = round(valor * pct / 100)
        es_adicional = iid.startswith("ot")
        if es_adicional:
            valor_adicionales += valor
        else:
            valor_base += valor
        ejecutado += v_ejec
        filas.append({
            "id": iid, "descripcion": str(it.get("descripcion") or "")[:200],
            "unidad": it.get("unidad") or "un",
            "cantidad_contratada": cant,
            "cantidad_ejecutada": round(cant * pct / 100, 2),
            "pct": pct, "valor_contratado": valor,
            "valor_ejecutado": v_ejec, "saldo": valor - v_ejec,
            "es_adicional": es_adicional,
        })
    valor_total = valor_base + valor_adicionales
    facturado = sum(int(c.get("total") or 0) for c in cuentas or [])
    pagado = sum(int(c.get("total") or 0) for c in cuentas or [] if c.get("pagada"))
    return {
        "filas": filas,
        "resumen": {
            "valor_contrato_base": valor_base,
            "valor_adicionales": valor_adicionales,
            "valor_total": valor_total,
            "valor_ejecutado": ejecutado,
            "saldo_por_ejecutar": valor_total - ejecutado,
            "avance_fisico_pct": round(ejecutado / valor_total * 100, 1) if valor_total else 0,
            "facturado": facturado,
            "pagado": pagado,
            "avance_financiero_pct": round(facturado / valor_total * 100, 1) if valor_total else 0,
        },
    }
