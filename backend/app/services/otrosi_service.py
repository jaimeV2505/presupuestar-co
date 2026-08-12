# -*- coding: utf-8 -*-
"""
Servicio de otrosies (adicionales de obra).

Reglas de negocio:
  - Un otrosi lleva items adicionales que el cliente aprueba con NUEVA firma.
  - Al aprobar, sus totales se CONGELAN con el mismo AIU/IVA del contrato original.
  - Los items aprobados entran a los avances (prefijo de id "ot{n}:") y por tanto
    al valor ejecutado y a las cuentas de cobro.
  - AMORTIZACION CON TOPE: el anticipo se pacto sobre el contrato ORIGINAL.
    La amortizacion acumulada nunca puede superar ese anticipo — si un corte
    incluye adicionales, se amortiza corte x % pero recortado al anticipo restante.
    Asi el cuadre siempre da: anticipo + suma(netos) = total efectivo.
"""
import json
from app.services.calculo_presupuesto import calcular_totales, validar_items


def aprobados_de(proyecto, db):
    from app.db import Otrosi
    return (db.query(Otrosi)
            .filter(Otrosi.proyecto_id == proyecto.id, Otrosi.estado == "aprobado")
            .order_by(Otrosi.numero).all())


def valor_adicionales(proyecto, db) -> int:
    """Suma de los totales congelados de los otrosies aprobados."""
    total = 0
    for o in aprobados_de(proyecto, db):
        t = json.loads(o.totales_json or "{}")
        total += int(t.get("total") or 0)
    return total


def items_efectivos(proyecto, db):
    """Items del contrato + items de otrosies aprobados (ids prefijados 'ot{n}:')."""
    items = json.loads(proyecto.items_json or "[]")
    for o in aprobados_de(proyecto, db):
        for it in json.loads(o.items_json or "[]"):
            it = dict(it)
            it["id"] = f"ot{o.numero}:{it.get('id') or it.get('codigo') or ''}"
            it["capitulo"] = f"ADICIONALES — OTROSI N.{o.numero}"
            items.append(it)
    return items


def totales_otrosi(items, aiu_proyecto) -> dict:
    """Totales del otrosi con el MISMO regimen AIU/IVA del contrato."""
    return calcular_totales(validar_items(items), aiu_proyecto or {})


def amortizacion_con_tope(valor_corte: int, anticipo_pct: float,
                          anticipo_total: int, amortizado_previo: int) -> int:
    """corte x % pero sin exceder el anticipo restante por amortizar."""
    teorica = round(valor_corte * anticipo_pct / 100)
    restante = max(0, anticipo_total - amortizado_previo)
    return min(teorica, restante)
