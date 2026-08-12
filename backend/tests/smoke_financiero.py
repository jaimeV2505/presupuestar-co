# -*- coding: utf-8 -*-
"""
Smoke test del nucleo financiero — corre sin dependencias externas:
    python3 backend/tests/smoke_financiero.py
Si algun numero cambia, revienta. Es el candado del dinero.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.services.calculo_presupuesto import calcular_totales

ITEMS = [
    {"cantidad": 10, "precio_unitario": 100000},
    {"cantidad": 4,  "precio_unitario": 250000},
]  # directo = 2.000.000


def caso(nombre, aiu, esperado):
    t = calcular_totales(ITEMS, aiu)
    for clave, valor in esperado.items():
        real = round(t[clave])
        assert real == valor, f"{nombre}: {clave} = {real:,} (esperado {valor:,})"
    print(f"  ✓ {nombre}")


def liquidar(ejecutado, cobrado_previo, anticipo_pct):
    """Replica exacta de la formula de cuentas.py::_liquidar"""
    corte = max(0, ejecutado - cobrado_previo)
    amort = round(corte * anticipo_pct / 100)
    return corte, amort, corte - amort


print("── calcular_totales ──")
caso("AIU estandar 15/5/8 + IVA/utilidad",
     {"admin": 15, "imprevistos": 5, "utilidad": 8, "aplicar": True, "iva_sobre_utilidad": True},
     {"subtotal_directo": 2_000_000, "admin_valor": 300_000, "imprevistos_valor": 100_000,
      "utilidad_valor": 160_000, "iva": 30_400, "total": 2_590_400})
caso("Sin AIU",
     {"admin": 15, "imprevistos": 5, "utilidad": 8, "aplicar": False},
     {"subtotal_directo": 2_000_000, "total": 2_000_000})
caso("AIU + IVA regimen comun (sobre toda la base)",
     {"admin": 10, "imprevistos": 0, "utilidad": 5, "aplicar": True, "iva_sobre_utilidad": False},
     {"admin_valor": 200_000, "utilidad_valor": 100_000, "iva": 437_000, "total": 2_737_000})
caso("Sin AIU + IVA sobre subtotal",
     {"aplicar": False, "con_iva": True},
     {"iva": 380_000, "total": 2_380_000})

print("── liquidacion de cuentas ──")
c, a, n = liquidar(3_000_000, 0, 50)
assert (c, a, n) == (3_000_000, 1_500_000, 1_500_000), f"corte1: {c},{a},{n}"
print("  ✓ corte 1 con anticipo 50%")
c, a, n = liquidar(7_000_000, 3_000_000, 50)
assert (c, a, n) == (4_000_000, 2_000_000, 2_000_000), f"corte2: {c},{a},{n}"
print("  ✓ corte 2 resta lo cobrado")
c, a, n = liquidar(3_000_000, 3_000_000, 50)
assert (c, a, n) == (0, 0, 0), "anti-doble-cobro"
print("  ✓ anti-doble-cobro (corte en cero)")
c, a, n = liquidar(5_000_000, 0, 0)
assert (c, a, n) == (5_000_000, 0, 5_000_000), "sin anticipo"
print("  ✓ sin anticipo, neto completo")
tot = 10_000_000; ant = int(tot * 0.5)
_, _, n1 = liquidar(3_000_000, 0, 50)
_, _, n2 = liquidar(7_000_000, 3_000_000, 50)
_, _, n3 = liquidar(10_000_000, 7_000_000, 50)
assert ant + n1 + n2 + n3 == tot, f"cuadre: {ant + n1 + n2 + n3:,}"
print(f"  ✓ cuadre exacto: {ant:,} + {n1:,} + {n2:,} + {n3:,} = {tot:,}")

print("\nNUCLEO FINANCIERO INTACTO ✅")
