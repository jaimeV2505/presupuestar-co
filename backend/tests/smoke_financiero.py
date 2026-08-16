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

print("── otrosies: amortizacion con tope ──")
from app.services.otrosi_service import amortizacion_con_tope
# Contrato 10M ant 50% (anticipo=5M) + otrosi aprobado de 2M -> total efectivo 12M
ANT_TOTAL = 5_000_000
a1 = amortizacion_con_tope(3_000_000, 50, ANT_TOTAL, 0)
assert a1 == 1_500_000, a1
a2 = amortizacion_con_tope(4_000_000, 50, ANT_TOTAL, 1_500_000)
assert a2 == 2_000_000, a2
# Corte final 5M (incluye el adicional): teorica 2.5M pero solo restan 1.5M por amortizar
a3 = amortizacion_con_tope(5_000_000, 50, ANT_TOTAL, 3_500_000)
assert a3 == 1_500_000, a3
print("  ✓ el tope recorta la amortizacion al anticipo restante")
n1, n2, n3 = 3_000_000 - a1, 4_000_000 - a2, 5_000_000 - a3
assert ANT_TOTAL + n1 + n2 + n3 == 12_000_000, ANT_TOTAL + n1 + n2 + n3
print(f"  ✓ cuadre CON adicional: {ANT_TOTAL:,} + {n1:,} + {n2:,} + {n3:,} = 12.000.000 (10M + otrosi 2M)")
# Sin tope habria amortizado 6M (mas que el anticipo recibido) — el contratista perderia 1M
assert round(12_000_000 * 0.5) - ANT_TOTAL == 1_000_000
print("  ✓ sin el tope, el contratista perderia $1.000.000 — candado justificado")

print("── retegarantia ──")
def liquidar_full(ejec, cobrado_bruto_previo, ant_pct, rete_pct, ant_total, amort_previa):
    corte = max(0, ejec - cobrado_bruto_previo)
    amort = min(round(corte * ant_pct / 100), max(0, ant_total - amort_previa))
    rete = round(corte * rete_pct / 100)
    return corte, amort, rete, corte - amort - rete

# Contrato 10M, anticipo 50%, retegarantia 5%
c1 = liquidar_full(3_000_000, 0, 50, 5, 5_000_000, 0)
assert c1 == (3_000_000, 1_500_000, 150_000, 1_350_000), c1
c2 = liquidar_full(7_000_000, 3_000_000, 50, 5, 5_000_000, 1_500_000)
assert c2 == (4_000_000, 2_000_000, 200_000, 1_800_000), c2
c3 = liquidar_full(10_000_000, 7_000_000, 50, 5, 5_000_000, 3_500_000)
assert c3 == (3_000_000, 1_500_000, 150_000, 1_350_000), c3
rete_total = c1[2] + c2[2] + c3[2]
assert rete_total == 500_000
liberacion = rete_total  # cuenta final tras el acta
recibido = 5_000_000 + c1[3] + c2[3] + c3[3] + liberacion
assert recibido == 10_000_000, recibido
print(f"  ✓ rete 5%: retenido {rete_total:,} por el camino, liberado al acta — cuadre {recibido:,}")

print("\nNUCLEO FINANCIERO INTACTO ✅")


# ═══ CONSTRUCTOR DE APU PROPIO (composicion determinista) ═══
from app.services.apu_propio_service import componer_precio

# Caso 1: panete 1:4 por m2 — 0.35 bulto cemento($28.500, 5% desp) + 0.04 m3 arena($65.000) + MO $9.000 + herr 5%
r = componer_precio(
    [{"nombre": "Cemento gris", "unidad": "bulto", "cantidad": 0.35, "precio": 28500, "desperdicio_pct": 5},
     {"nombre": "Arena lavada", "unidad": "m3", "cantidad": 0.04, "precio": 65000}],
    mano_obra=9000, herramienta_pct=5)
assert r["materiales"] == round(0.35*28500*1.05 + 0.04*65000) == 13074, r["materiales"]
assert r["herramienta"] == 450
assert r["precio_unitario"] == 13074 + 9000 + 450 == 22524, r["precio_unitario"]

# Caso 2: solo mano de obra (instalacion) — sin insumos
r = componer_precio([], mano_obra=45000, herramienta_pct=10)
assert r["precio_unitario"] == 49500 and r["materiales"] == 0

# Caso 3: candados del constructor
for malo in [
    ([{"cantidad": -1, "precio": 100}], 0, 0),
    ([{"cantidad": 1, "precio": 100, "desperdicio_pct": 80}], 0, 0),
    ([], 1000, 45),
]:
    try:
        componer_precio(*malo); assert False, "debia rechazar"
    except ValueError:
        pass

print("OK constructor de APU: 2 composiciones exactas + 3 candados")


# ═══ BALANCE DE OBRA (oficial vs ejecutado) ═══
from app.services.balance_service import balance_de_obra

# Contrato: 2 items base ($4.2M + $6.76M) + 1 adicional ($7.6M). Avances: 100%, 30%, 50%.
b = balance_de_obra(
    [{"id": "it1", "descripcion": "Replanteo", "unidad": "m2", "cantidad": 1200, "precio_unitario": 3500},
     {"id": "it2", "descripcion": "Panete", "unidad": "m2", "cantidad": 300, "precio_unitario": 22524},
     {"id": "ot1:ex1", "descripcion": "Recebo", "unidad": "m3", "cantidad": 80, "precio_unitario": 95000}],
    {"it1": 100, "it2": 30, "ot1:ex1": 50},
    [{"total": 3_000_000, "pagada": True}, {"total": 2_000_000, "pagada": False}])
r = b["resumen"]
assert r["valor_contrato_base"] == 1200*3500 + 300*22524 == 10957200
assert r["valor_adicionales"] == 80*95000 == 7600000
assert r["valor_total"] == 18557200
assert r["valor_ejecutado"] == 4200000 + round(6757200*0.3) + 3800000 == 10027160
assert r["saldo_por_ejecutar"] == 18557200 - 10027160
assert r["avance_fisico_pct"] == 54.0
assert r["facturado"] == 5000000 and r["pagado"] == 3000000
assert r["avance_financiero_pct"] == 26.9
assert b["filas"][2]["es_adicional"] is True
assert b["filas"][1]["cantidad_ejecutada"] == 90.0

# candado: sin items -> ceros sin dividir por cero
b2 = balance_de_obra([], {}, [])
assert b2["resumen"]["avance_fisico_pct"] == 0

print("OK balance de obra: caso exacto de 3 items + division segura")


# ═══ ADAPTADOR DE FUENTES DE PRECIOS ═══
from app.services.fuentes_precios import fuente_curada, fuente_externa

# candado de calidad: la base curada es un ACTIVO — 200+ insumos, sin duplicados, precios sanos
import json as _j, os as _o
_base = _j.load(open(_o.path.join(_o.path.dirname(__file__), "..", "app", "data", "insumos_2026.json"), encoding="utf-8"))
_ins = _base["insumos"]
assert len(_ins) >= 200, f"la base curada bajo de 200: {len(_ins)}"
_noms = [i["nombre"] for i in _ins]
assert len(_noms) == len(set(_noms)), "insumos duplicados en la base"
for i in _ins:
    assert i["nombre"] and i["unidad"] and i["categoria"], i
    assert 500 <= i["precio"] <= 5_000_000, f"precio sospechoso: {i}"
assert len({i["categoria"] for i in _ins}) >= 15
assert _base["version"] >= "2026.2"

r = fuente_curada("cemento")
assert any(i["nombre"].startswith("Cemento gris") and i["precio"] == 28500 for i in r), r
assert all(i["fuente"] == "referencia" and i["fecha"] for i in r)
assert fuente_curada("ceramica") and fuente_curada("CERÁMICA")   # sin tildes, case-insensitive
assert fuente_curada("zzz-no-existe") == []
assert fuente_externa("cemento") == []   # sin cache configurado: degradacion elegante
import os as _os, tempfile as _tf
_bad = _tf.mktemp(suffix=".json"); open(_bad, "w").write("{corrupto sin cerrar")
_os.environ["PRECIOS_EXTERNOS_JSON"] = _bad
assert fuente_externa("cemento") == []   # cache CORRUPTO: degrada, no explota
_ok = _tf.mktemp(suffix=".json")
open(_ok, "w").write('[{"fuente": "homecenter", "nombre": "Cemento gris 50kg", "precio": 29900, "unidad": "bulto", "fecha": "01/08/2026"}]')
_os.environ["PRECIOS_EXTERNOS_JSON"] = _ok
_r = fuente_externa("cemento")
assert _r and _r[0]["fuente"] == "homecenter" and _r[0]["precio"] == 29900
del _os.environ["PRECIOS_EXTERNOS_JSON"]

print("OK fuentes de precios: curada busca + externa degrada sin romper")


# ═══ DEDUCCIONES DE LEY (obra publica) ═══
from app.services.deducciones_service import aplicar_deducciones, validar_deducciones, SUGERIDAS

# Corte de $6.227.160 con las 3 de ley: 5% + 4% + 2%
d = aplicar_deducciones(6_227_160, SUGERIDAS)
assert d["detalle"][0]["valor"] == round(6_227_160 * 0.05) == 311358
assert d["detalle"][1]["valor"] == round(6_227_160 * 0.04) == 249086
assert d["detalle"][2]["valor"] == round(6_227_160 * 0.02) == 124543
assert d["total"] == 311358 + 249086 + 124543 == 684987
assert "Ley 1106" in d["detalle"][0]["nombre"]

# candados
for malo in [[{"nombre": "x", "pct": 5}], [{"nombre": "Estampilla", "pct": 30}],
             [{"nombre": "A", "pct": 20}, {"nombre": "B", "pct": 20}, {"nombre": "C", "pct": 20}]]:
    try:
        validar_deducciones(malo); assert False, f"debia rechazar {malo}"
    except ValueError:
        pass
assert aplicar_deducciones(1_000_000, []) == {"detalle": [], "total": 0}

print("OK deducciones de ley: 5+4+2 exactas a peso + 3 candados")

# ═══ FAMILIA 6: INCIDENCIA POR CAPITULO + DESCUENTO DE NEGOCIACION (F3+F7) ═══
ITEMS_F = [
    {"capitulo": "ESTRUCTURA", "cantidad": 10, "precio_unitario": 60000, "precio_lista": 75000},
    {"capitulo": "ESTRUCTURA", "cantidad": 5,  "precio_unitario": 40000},
    {"capitulo": "ACABADOS",   "cantidad": 4,  "precio_unitario": 50000, "precio_lista": 50000},
]
r = calcular_totales(ITEMS_F, {"aplicar": False})
# directo: 600.000 + 200.000 + 200.000 = 1.000.000
assert r["subtotal_directo"] == 1_000_000, r["subtotal_directo"]
caps = {c["capitulo"]: c for c in r["capitulos"]}
assert caps["ESTRUCTURA"]["valor"] == 800_000 and caps["ESTRUCTURA"]["pct"] == 80.0, caps
assert caps["ACABADOS"]["valor"] == 200_000 and caps["ACABADOS"]["pct"] == 20.0, caps
assert r["capitulos"][0]["capitulo"] == "ESTRUCTURA", "incidencias deben venir ordenadas desc"
# lista: 750.000 + 200.000 + 200.000 = 1.150.000 -> descuento 150.000 = 13.0%
assert r["subtotal_lista"] == 1_150_000, r["subtotal_lista"]
assert r["descuento_valor"] == 150_000, r["descuento_valor"]
assert r["descuento_pct"] == 13.0, r["descuento_pct"]
# sin precio_lista: descuento cero, lista == directo
r0 = calcular_totales([{"capitulo": "X", "cantidad": 2, "precio_unitario": 100}], {"aplicar": False})
assert r0["descuento_valor"] == 0 and r0["subtotal_lista"] == r0["subtotal_directo"]
# precio_lista MENOR al pactado no genera "descuento negativo"
rneg = calcular_totales([{"cantidad": 1, "precio_unitario": 100, "precio_lista": 50}], {"aplicar": False})
assert rneg["descuento_valor"] == 0, rneg

print("OK incidencia por capitulo + descuento de negociacion: exactos a peso")
