# -*- coding: utf-8 -*-
"""
TEST DE VIAJE PUBLICO — el segundo robot: la historia de una OBRA PUBLICA.

El ingeniero gana un contrato estatal y lo administra completo DENTRO de la
plataforma (sin cliente final): crea el proyecto publico -> construye sus
propios APUs (manual, duplicado de la base 2026, y COMPUESTO con precios de
SU proveedor) -> presupuesto -> candado anti-compartir -> avance -> acta
parcial (cuenta) -> adicional aprobado internamente -> termina y liquida
la retegarantia. Todo con los candados de la casa.

Correr local: cd backend && python3 tests/test_viaje_publico.py
"""
import os
import sys
import tempfile

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mkdtemp()}/publico.db")
os.environ.setdefault("JWT_SECRET", "secreto-viaje-publico-0123456789abcdef")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app                   # noqa: E402

c = TestClient(app)
PASOS = []


def paso(nombre, resp, status=200, contiene=None):
    ok = resp.status_code == status
    cuerpo = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
    if ok and contiene:
        ok = all(k in str(cuerpo) for k in contiene)
    print(f"  {'✓' if ok else '❌'} {nombre}")
    if not ok:
        print(f"     status={resp.status_code} esperado={status}")
        print(f"     cuerpo={str(cuerpo)[:400]}")
        raise SystemExit(f"VIAJE PUBLICO ROTO EN: {nombre}")
    PASOS.append(nombre)
    return cuerpo


print("═══ ACTO 0: EL INGENIERO Y SU CONTRATO ESTATAL ═══")
d = paso("registro", c.post("/api/auth/registro",
         json={"email": "ing@publico.test", "password": "ObraPublica2026"}))
H = {"Authorization": f"Bearer {d['token']}"}

d = paso("crear proyecto PUBLICO (entidad + contrato)", c.post("/api/proyectos", json={
    "nombre": "Mantenimiento via terciaria vereda El Roble",
    "sector": "publico",
    "entidad_nombre": "Alcaldia de Prueba - Secretaria de Infraestructura",
    "contrato_numero": "OP-2026-0457",
    "supervisor_nombre": "Ing. Supervisora Perez",
    "cliente_nombre": "", "region": "bogota"}, headers=H))
PID = d["id"]
d = paso("detalle refleja el sector", c.get(f"/api/proyectos/{PID}", headers=H),
         contiene=["publico", "OP-2026-0457"])
TOKEN = d["share_token"]

print("═══ ACTO 1: MIS APUs — las tres vias ═══")
d = paso("APU manual", c.post("/api/apus", json={
    "codigo": "MI-001", "descripcion": "Localizacion y replanteo via terciaria",
    "unidad": "m2", "precio": 3500, "sector_tag": "publico"}, headers=H))
APU_MANUAL = d["id"]

r = c.post("/api/apus", json={"descripcion": "x", "precio": 100}, headers=H)
paso("CANDADO: descripcion de 1 caracter -> 400", r, status=400)
r = c.post("/api/apus", json={"descripcion": "precio absurdo", "precio": 3_000_000_000}, headers=H)
paso("CANDADO: precio fuera de rango -> 400", r, status=400)

# duplicar de la base 2026 (la base JAMAS se toca)
import json as _json
base = _json.load(open(os.path.join(os.path.dirname(__file__), "..", "app", "data", "apu_2026.json")))
items_base = base if isinstance(base, list) else list(base.values())[0]
CODIGO_BASE = items_base[0]["codigo"]
d = paso("duplicar de la base como MIO", c.post(
    f"/api/apus/duplicar-de-base?codigo={CODIGO_BASE}&region=bogota", headers=H),
    contiene=["MI-"])
assert d["origen_base"] == CODIGO_BASE
d = paso("EDITAR mi APU (el bug del doble body, vigilado)", c.put(f"/api/apus/{APU_MANUAL}", json={
    "codigo": "MI-001", "descripcion": "Localizacion y replanteo via terciaria (rev.1)",
    "unidad": "m2", "precio": 3600, "sector_tag": "publico"}, headers=H))
assert d["precio"] == 3600 and "rev.1" in d["descripcion"]

r = c.post("/api/apus/duplicar-de-base?codigo=NO-EXISTE-999", headers=H)
paso("CANDADO: codigo inexistente en la base -> 404", r, status=404)

print("═══ ACTO 1.5: EL CONSTRUCTOR (proveedor propio + composicion) ═══")
d = paso("crear MI proveedor", c.post("/api/proveedores", json={
    "nombre": "Ferreteria El Roble", "ciudad": "Bogota", "telefono": "3001112233"}, headers=H))
PROV = d["id"]
paso("capturar precio del cemento", c.post(f"/api/proveedores/{PROV}/precios",
     json={"insumo": "Cemento gris", "unidad": "bulto", "precio": 28500}, headers=H))
r = c.post(f"/api/proveedores/{PROV}/precios",
           json={"insumo": "x", "precio": -5}, headers=H)
paso("CANDADO: precio negativo -> 400", r, status=400)

d = paso("buscar insumo MULTI-FUENTE (mi proveedor + referencia)",
         c.get("/api/insumos/buscar?q=cemento", headers=H))
fuentes = {r["fuente"] for r in d["resultados"]}
assert "mi_proveedor" in fuentes and "referencia" in fuentes, fuentes
mio = next(r for r in d["resultados"] if r["fuente"] == "mi_proveedor")
assert mio["precio"] == 28500 and mio["detalle"] == "Ferreteria El Roble" and mio["fecha"]

d = paso("comparador: mi precio vs referencia", c.get("/api/insumos/comparar?q=cemento", headers=H))
assert d["mi_mejor"]["precio"] == 28500 and d["referencia"]["precio"] == 28500
assert d["ahorro"] == 0   # mismo precio de referencia — el calculo cuadra
r = c.get("/api/insumos/buscar?q=x", headers=H)
paso("CANDADO: busqueda de 1 letra -> 4xx", r, status=422) if r.status_code == 422 else paso("CANDADO: busqueda corta rechazada", r, status=400)

d = paso("componer APU con mis insumos (vista previa)", c.post("/api/apus/componer", json={
    "insumos": [
        {"nombre": "Cemento gris", "unidad": "bulto", "cantidad": 0.35, "precio": 28500, "desperdicio_pct": 5},
        {"nombre": "Arena lavada", "unidad": "m3", "cantidad": 0.04, "precio": 65000}],
    "mano_obra": 9000, "herramienta_pct": 5}, headers=H))
assert d["precio_unitario"] == 22524, d   # el mismo caso exacto del smoke
d2 = paso("crear APU y guardar su desglose compuesto", c.post("/api/apus", json={
    "codigo": "MI-COMP-1", "descripcion": "Panete 1:4 muros (compuesto)",
    "unidad": "m2", "precio": 0, "sector_tag": "publico"}, headers=H))
APU_COMP = d2["id"]
d = paso("fijar desglose", c.put(f"/api/apus/{APU_COMP}/desglose", json={
    "insumos": [
        {"nombre": "Cemento gris", "unidad": "bulto", "cantidad": 0.35, "precio": 28500, "desperdicio_pct": 5},
        {"nombre": "Arena lavada", "unidad": "m3", "cantidad": 0.04, "precio": 65000}],
    "mano_obra": 9000, "herramienta_pct": 5}, headers=H))
assert d["precio"] == 22524 and d["desglose"]["materiales"] == 13074
d = paso("mis APUs listados (filtro sector publico)", c.get("/api/apus?sector=publico", headers=H))
assert len(d["items"]) >= 3

print("═══ ACTO 1.9: EL LADRON (ownership cruzado) ═══")
d2 = paso("registro del intruso", c.post("/api/auth/registro",
          json={"email": "intruso@publico.test", "password": "Intruso2026x"}))
H2 = {"Authorization": f"Bearer {d2['token']}"}
r = c.put(f"/api/apus/{APU_MANUAL}", json={"descripcion": "hackeado", "precio": 1}, headers=H2)
paso("CANDADO: editar APU ajeno -> 404", r, status=404)
r = c.delete(f"/api/apus/{APU_COMP}", headers=H2)
paso("CANDADO: borrar APU ajeno -> 404", r, status=404)
r = c.get(f"/api/proveedores/{PROV}/precios", headers=H2)
paso("CANDADO: espiar precios de proveedor ajeno -> 404", r, status=404)
d = c.get("/api/apus", headers=H2).json()
assert d["total"] == 0, "el intruso VE apus ajenos!"
print("  ✓ el intruso no ve, no edita, no borra nada ajeno")
PASOS.append("ownership cruzado blindado")

print("═══ ACTO 2: EL PRESUPUESTO OFICIAL Y LOS CANDADOS DEL SECTOR ═══")
paso("items desde MIS APUs + contrato (anticipo 30%, rete 10%)", c.put(f"/api/proyectos/{PID}", json={
    "items": [
        {"id": "it1", "descripcion": "Localizacion y replanteo", "unidad": "m2",
         "cantidad": 1200, "precio_unitario": 3500},
        {"id": "it2", "descripcion": "Panete 1:4 muros (compuesto)", "unidad": "m2",
         "cantidad": 300, "precio_unitario": 22524},
    ],
    "aiu": {"admin": 20, "imprevistos": 3, "utilidad": 7, "aplicar": True, "iva_sobre_utilidad": True},
    "contrato": {"plazo_dias": 90, "anticipo_pct": 30, "retegarantia_pct": 10,
                 "fecha_inicio": "2026-09-01", "lugar": "Vereda El Roble",
                 "deducciones": [
                     {"nombre": "Contribución obra pública 5% (Ley 1106/2006)", "pct": 5},
                     {"nombre": "Estampillas territoriales", "pct": 4},
                     {"nombre": "Retefuente construcción", "pct": 2}]},
}, headers=H))

r = c.put(f"/api/proyectos/{PID}", json={"contrato": {"anticipo_pct": 30, "retegarantia_pct": 10,
    "deducciones": [{"nombre": "Estampilla absurda", "pct": 30}]}}, headers=H)
paso("CANDADO: deduccion del 30% -> 400", r, status=400)
# restaurar el contrato bueno (el candado no debe haberlo tocado)
paso("contrato restaurado con las 3 de ley", c.put(f"/api/proyectos/{PID}", json={
    "contrato": {"plazo_dias": 90, "anticipo_pct": 30, "retegarantia_pct": 10,
                 "fecha_inicio": "2026-09-01", "lugar": "Vereda El Roble",
                 "deducciones": [
                     {"nombre": "Contribución obra pública 5% (Ley 1106/2006)", "pct": 5},
                     {"nombre": "Estampillas territoriales", "pct": 4},
                     {"nombre": "Retefuente construcción", "pct": 2}]}}, headers=H))

r = c.post(f"/api/share/proyectos/{PID}/compartir", headers=H)
paso("CANDADO ESTRELLA: obra publica NO comparte -> 400", r, status=400,
     ) if r.status_code == 400 else paso("candado publico", r, status=400)

# En publico el contrato "se firma" marcando aceptado internamente via estado
paso("marcar contrato en ejecucion", c.put(f"/api/proyectos/{PID}",
     json={"estado": "aceptado"}, headers=H))

print("═══ ACTO 3: EJECUCION — ACTAS PARCIALES ═══")
d = paso("avance 50%", c.post(f"/api/avances/proyectos/{PID}/avances", json={
    "titulo": "Acta parcial No. 1", "items": [{"id": "it1", "pct": 100}, {"id": "it2", "pct": 30}],
}, headers=H))
AV1 = d["id"]
d = paso("acta parcial (cuenta) liquidada con anticipo 30% y rete 10%",
         c.post(f"/api/cuentas/proyectos/{PID}/cuentas", json={"avance_id": AV1}, headers=H))
CID = d.get("id") or d.get("cuenta", {}).get("id")
cc = d.get("cuenta") or d
CORTE = cc["valor_corte"]; RETE = cc["retencion"]; AMORT = cc["amortizacion"]
assert RETE == round(CORTE * 0.10), f"rete no es 10%: {RETE} de {CORTE} (BUG #2 vigilado)"
DED = cc["deducciones"]
esperado_ded = round(CORTE*0.05) + round(CORTE*0.04) + round(CORTE*0.02)
assert DED == esperado_ded, f"deducciones {DED} != {esperado_ded}"
assert len(cc["deducciones_detalle"]) == 3 and "Ley 1106" in cc["deducciones_detalle"][0]["nombre"]
assert cc["neto"] == CORTE - AMORT - RETE - DED, "el NETO REAL no cuadra"
print(f"  ✓ acta publica liquidada a peso: corte {CORTE:,} - amort {AMORT:,} - rete {RETE:,} - deducciones {DED:,} = neto {cc['neto']:,}")
PASOS.append("deducciones de ley exactas")
paso("acta cobrada (pagada por la entidad)", c.post(f"/api/cuentas/{CID}/pagada", headers=H))

print("═══ ACTO 3.5: ADICIONAL / MAYORES CANTIDADES (aprobacion interna) ═══")
d = paso("proponer adicional", c.post("/api/otrosies", json={
    "proyecto_id": PID, "motivo": "Mayores cantidades por inestabilidad del terreno",
    "items": [{"id": "ex1", "descripcion": "Recebo compactado adicional", "unidad": "m3",
               "cantidad": 80, "precio_unitario": 95000}]}, headers=H))
OID = d["id"]
paso("aprobar INTERNAMENTE (sin cliente — es obra publica)",
     c.post(f"/api/otrosies/{OID}/aprobar-interno", headers=H))
r = c.post(f"/api/otrosies/{OID}/aprobar-interno", headers=H)
paso("CANDADO: doble aprobacion -> 400", r, status=400)

paso("avance final con el adicional", c.post(f"/api/avances/proyectos/{PID}/avances", json={
    "titulo": "Acta parcial No. 2 — final",
    "items": [{"id": "it1", "pct": 100}, {"id": "it2", "pct": 100}, {"id": "ot1:ex1", "pct": 100}],
}, headers=H))

print("═══ ACTO 3.75: BALANCE DE OBRA (oficial vs ejecutado) ═══")
d = paso("balance del proyecto", c.get(f"/api/proyectos/{PID}/balance", headers=H))
rs = d["resumen"]
VALOR_BASE = 1200*3500 + 300*22524          # 10.957.200
VALOR_ADIC = 80*95000                        # 7.600.000
assert rs["valor_contrato_base"] == VALOR_BASE, rs
assert rs["valor_adicionales"] == VALOR_ADIC, rs
assert rs["valor_total"] == VALOR_BASE + VALOR_ADIC
assert rs["avance_fisico_pct"] == 100.0      # avance final: todo al 100
assert rs["facturado"] > 0 and rs["pagado"] > 0
adicionales = [f for f in d["filas"] if f["es_adicional"]]
assert len(adicionales) == 1 and adicionales[0]["id"] == "ot1:ex1"
print("  ✓ el balance cuadra a peso: base + adicional + avances + actas")
PASOS.append("balance de obra exacto")

print("═══ ACTO 3.9: LINK DE INTERVENTORIA ═══")
d = paso("generar enlace de interventoria", c.post(f"/api/share/proyectos/{PID}/interventoria", headers=H))
TOKEN_INT = d["token"]
assert d["modo"] == "interventoria"
d = paso("el interventor VE el panel", c.get(f"/api/share/publico/{TOKEN_INT}"))
assert d["sector"] == "publico" and "Alcaldia" in d["entidad_nombre"] and d["contrato_numero"] == "OP-2026-0457"
cuerpo = str(d).lower()
for prohibido in ["password", "gastos", "utilidad_real", "jwt"]:
    assert prohibido not in cuerpo, f"FUGA en panel interventoria: {prohibido}"
print("  ✓ interventoria: entidad y contrato visibles, cero datos intimos")
PASOS.append("panel de interventoria blindado")

print("═══ ACTO 4: LIQUIDACION DEL CONTRATO ═══")
paso("terminar directo (publico: sin confirmacion de cliente)",
     c.put(f"/api/proyectos/{PID}", json={"estado": "terminado"}, headers=H))
d = paso("liberar retegarantia", c.post(f"/api/cuentas/proyectos/{PID}/retegarantia", headers=H))
r = c.post(f"/api/cuentas/proyectos/{PID}/retegarantia", headers=H)
paso("CANDADO: liberar dos veces -> 400", r, status=400)

print(f"\n{'='*52}")
print(f"VIAJE PUBLICO: {len(PASOS)} pasos en verde ✅")
print("El ingeniero administro su contrato estatal completo — sin salir de la plataforma.")
