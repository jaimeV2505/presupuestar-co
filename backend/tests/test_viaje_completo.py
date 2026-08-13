# -*- coding: utf-8 -*-
"""
TEST DE VIAJE COMPLETO — el probador humano automatizado.

Ejecuta la historia ENTERA de una obra contra la API real (FastAPI TestClient
+ SQLite temporal), como lo haria una persona probando a mano:

  registro -> login -> crear proyecto -> items+AIU+contrato -> el cliente VE
  -> el cliente FIRMA -> candado post-firma -> avance 40% -> cuenta liquidada
  -> abono parcial -> abono excesivo (bloqueado) -> otrosi propuesto -> el
  cliente lo firma -> avance con item del otrosi -> anti-doble-cobro ->
  solicitar entrega -> acta bilateral -> retegarantia liberada -> encuesta.

Correr local:   cd backend && python3 tests/test_viaje_completo.py
En CI corre automaticamente en cada push (.github/workflows/ci.yml).
Si algun paso rompe: imprime el paso, el status y el cuerpo de la respuesta.
"""
import os
import sys
import tempfile

# ── Entorno de prueba ANTES de importar la app ──
os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkdtemp()}/viaje.db"
os.environ.setdefault("JWT_SECRET", "secreto-de-prueba-viaje-completo-0123456789")
os.environ.setdefault("ADMIN_EMAILS", "admin@viaje.test")
os.environ.pop("RESEND_API_KEY", None)   # sin emails reales en pruebas

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
    marca = "✓" if ok else "❌"
    print(f"  {marca} {nombre}")
    if not ok:
        print(f"     status={resp.status_code} esperado={status}")
        print(f"     cuerpo={str(cuerpo)[:400]}")
        raise SystemExit(f"VIAJE ROTO EN: {nombre}")
    PASOS.append(nombre)
    return cuerpo


print("═══ ACTO 0: EL CONTRATISTA LLEGA ═══")
r = c.post("/api/auth/registro", json={"email": "maestro@viaje.test", "password": "Obra2026segura"})
d = paso("registro", r, contiene=["token"])
H = {"Authorization": f"Bearer {d['token']}"}
r = c.post("/api/auth/login", json={"email": "maestro@viaje.test", "password": "Obra2026segura"})
paso("login", r, contiene=["token"])
paso("perfil /yo", c.get("/api/auth/yo", headers=H))

print("═══ ACTO 1: LA COTIZACION ═══")
d = paso("crear proyecto", c.post("/api/proyectos", json={
    "nombre": "Remodelacion bano viaje", "cliente_nombre": "Dona Prueba",
    "cliente_telefono": "3000000000", "region": "bogota"}, headers=H))
PID = d["id"]
ITEMS = [
    {"id": "it1", "descripcion": "Demolicion enchape", "unidad": "m2", "cantidad": 10, "precio_unitario": 30000},
    {"id": "it2", "descripcion": "Enchape piso y pared", "unidad": "m2", "cantidad": 20, "precio_unitario": 85000},
    {"id": "it3", "descripcion": "Instalacion sanitario", "unidad": "un", "cantidad": 1, "precio_unitario": 300000},
]  # directo = 2.300.000
d = paso("items + AIU + contrato (anticipo 50%, rete 5%)", c.put(f"/api/proyectos/{PID}", json={
    "items": ITEMS,
    "aiu": {"admin": 10, "imprevistos": 0, "utilidad": 10, "aplicar": True, "iva_sobre_utilidad": True},
    "contrato": {"plazo_dias": 20, "anticipo_pct": 50, "retegarantia_pct": 5,
                 "fecha_inicio": "2026-09-01", "lugar": "Bogota"},
}, headers=H))
d = paso("detalle con totales", c.get(f"/api/proyectos/{PID}", headers=H), contiene=["share_token"])
TOKEN = d["share_token"]
TOTAL = round(d["totales"]["total"])
print(f"     total del contrato: ${TOTAL:,}")

d = paso("compartir devuelve ruta con preview OG", c.post(f"/api/share/proyectos/{PID}/compartir", headers=H),
         contiene=["ruta_preview"])

print("═══ ACTO 2: EL CLIENTE (sin cuenta, solo el link) ═══")
paso("el cliente VE (evento visto)", c.get(f"/api/share/publico/{TOKEN}"), contiene=["capitulos"])
paso("el cliente FIRMA", c.post(f"/api/share/publico/{TOKEN}/aceptar",
     json={"nombre": "Dona Prueba", "documento": "51222333", "firma_imagen": ""}))
r = c.put(f"/api/proyectos/{PID}", json={"items": ITEMS[:1]}, headers=H)
paso("CANDADO: editar tras la firma -> 400", r, status=400)

print("═══ ACTO 3: LA OBRA ═══")
d = paso("avance 40% (it1 100%, it2 ~44%)", c.post(f"/api/avances/proyectos/{PID}/avances", json={
    "titulo": "Corte semana 1", "items": [{"id": "it1", "pct": 100}, {"id": "it2", "pct": 44.1}],
}, headers=H))
AV1 = d["id"]

print("═══ ACTO 3.1: EL CLIENTE PARTICIPA (reacciones y comentarios) ═══")
paso("el cliente reacciona ❤️ al avance", c.post(
    f"/api/share/publico/{TOKEN}/avances/{AV1}/interaccion",
    json={"tipo": "reaccion", "valor": "❤️", "nombre": "Dona Prueba"}))
d = paso("el cliente comenta", c.post(
    f"/api/share/publico/{TOKEN}/avances/{AV1}/interaccion",
    json={"tipo": "comentario", "valor": "Quedo hermoso el enchape!", "nombre": "Dona Prueba"}),
    contiene=["comentarios"])
assert d["reacciones"].get("❤️") == 1 and len(d["comentarios"]) == 1
r = c.post(f"/api/share/publico/{TOKEN}/avances/{AV1}/interaccion",
           json={"tipo": "reaccion", "valor": "🔥"})
paso("CANDADO: reaccion fuera de la lista -> 400", r, status=400)
r = c.post(f"/api/share/publico/{TOKEN}/avances/{AV1}/interaccion",
           json={"tipo": "comentario", "valor": "x" * 301})
paso("CANDADO: comentario de 301 caracteres -> 400", r, status=400)
r = c.get("/api/notificaciones", headers=H)
notifs = r.json().get("notificaciones", [])
assert any(n["tipo"] == "comentario" for n in notifs), "el contratista debia recibir la notificacion del comentario"
print("  ✓ la campana del contratista sono: comentario notificado")

print("═══ ACTO 3.2: EL PREVIEW DE WHATSAPP (OG) ═══")
r = c.get(f"/api/s/{TOKEN}")
assert r.status_code == 200 and "og:title" in r.text and "Remodelacion bano viaje" in r.text
print("  ✓ /api/s/{token}: HTML con og:title de LA obra")
PASOS.append("preview OG")
r = c.get("/api/s/token-que-no-existe")
assert r.status_code == 404
print("  ✓ token falso -> 404")
PASOS.append("preview OG 404")
d = paso("liquidacion preview", c.get(f"/api/cuentas/proyectos/{PID}/cuentas/preview",
                                      params={"avance_id": AV1}, headers=H))
d = paso("generar cuenta de cobro", c.post(f"/api/cuentas/proyectos/{PID}/cuentas",
                                           json={"avance_id": AV1}, headers=H))
CID = d.get("id") or d.get("cuenta", {}).get("id")
NETO = d.get("neto") or d.get("cuenta", {}).get("neto")
RETE1 = d.get("retencion") or d.get("cuenta", {}).get("retencion") or 0
print(f"     cuenta: neto=${NETO:,} retuvo=${RETE1:,}")
assert RETE1 > 0, "la retegarantia del 5% debia retener algo"

paso("abono parcial de $200.000", c.post(f"/api/cuentas/{CID}/abonos",
     json={"monto": 200000, "nota": "Nequi viernes"}, headers=H))
r = c.post(f"/api/cuentas/{CID}/abonos", json={"monto": NETO * 2, "nota": "exceso"}, headers=H)
paso("CANDADO: abono mayor al saldo -> 400", r, status=400)
paso("ya me pagaron (cierra el saldo)", c.post(f"/api/cuentas/{CID}/pagada", headers=H))

print("═══ ACTO 3.5: EL ADICIONAL (otrosi) ═══")
d = paso("proponer otrosi", c.post("/api/otrosies", json={
    "proyecto_id": PID, "motivo": "La clienta pidio ademas el meson",
    "items": [{"id": "ex1", "descripcion": "Meson en granito", "unidad": "ml",
               "cantidad": 2, "precio_unitario": 400000}]}, headers=H))
OID = d["id"]
paso("el cliente FIRMA el otrosi", c.post(f"/api/share/publico/{TOKEN}/otrosi/{OID}/aprobar",
     json={"nombre": "Dona Prueba", "documento": "51222333"}))
r = c.delete(f"/api/otrosies/{OID}", headers=H)
paso("CANDADO: otrosi aprobado ineliminable -> 400", r, status=400)
d = paso("avance al 100% (incluye item del otrosi)", c.post(f"/api/avances/proyectos/{PID}/avances", json={
    "titulo": "Corte final", "items": [
        {"id": "it1", "pct": 100}, {"id": "it2", "pct": 100}, {"id": "it3", "pct": 100},
        {"id": "ot1:ex1", "pct": 100}]}, headers=H))
AV2 = d["id"]
d = paso("cuenta final", c.post(f"/api/cuentas/proyectos/{PID}/cuentas",
                                json={"avance_id": AV2}, headers=H))
CID2 = d.get("id") or d.get("cuenta", {}).get("id")
paso("pagar cuenta final", c.post(f"/api/cuentas/{CID2}/pagada", headers=H))
r = c.post(f"/api/cuentas/proyectos/{PID}/cuentas", json={"avance_id": AV2}, headers=H)
paso("CANDADO: anti-doble-cobro (nada nuevo que cobrar) -> 400", r, status=400)

print("═══ ACTO 4: LA ENTREGA Y EL CIERRE ═══")
paso("solicitar entrega", c.put(f"/api/proyectos/{PID}", json={"estado": "entrega_solicitada"}, headers=H))
paso("el cliente confirma (acta bilateral)", c.post(f"/api/share/publico/{TOKEN}/confirmar-entrega",
     json={"nombre": "Dona Prueba", "documento": "51222333", "firma_imagen": ""}))
r = c.get(f"/api/share/publico/{TOKEN}/acta.pdf")
paso("acta.pdf descargable", r)
d = paso("liberar retegarantia", c.post(f"/api/cuentas/proyectos/{PID}/retegarantia", headers=H))
r = c.post(f"/api/cuentas/proyectos/{PID}/retegarantia", headers=H)
paso("CANDADO: retegarantia UNA sola vez -> 400", r, status=400)
paso("encuesta 5 estrellas", c.post(f"/api/share/publico/{TOKEN}/encuesta",
     json={"estrellas": 5, "recomendaria": True, "comentario": "Excelente y transparente"}))

print("═══ VERIFICACION FINAL: EL CUADRE ═══")
d = paso("resumen de caja", c.get(f"/api/cuentas/proyectos/{PID}/cuentas", headers=H))
cuentas = d["cuentas"]
total_neto_pagado = sum(x["neto"] for x in cuentas if x["estado"] == "pagada")
total_rete = sum(x["retencion"] for x in cuentas if x.get("tipo") != "retegarantia")
liberada = sum(x["neto"] for x in cuentas if x.get("tipo") == "retegarantia")
print(f"     netos pagados=${total_neto_pagado:,} · rete retenida=${total_rete:,} · liberada=${liberada:,}")
assert liberada == total_rete, "la liberacion debe igualar lo retenido"

print(f"\n{'='*52}")
print(f"VIAJE COMPLETO: {len(PASOS)} pasos en verde ✅")
print("El robot probo lo que un humano probaria — sin humano.")
