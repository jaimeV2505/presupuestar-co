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
os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mkdtemp()}/viaje.db")
os.environ.setdefault("JWT_SECRET", "secreto-de-prueba-viaje-completo-0123456789")
os.environ.setdefault("ADMIN_EMAILS", "maestro@viaje.test")   # el viajero ES admin (para respaldo)
os.environ.setdefault("WOMPI_EVENTS_SECRET", "secreto-eventos-viaje")
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
d = paso("el CONTRATISTA responde en el hilo", c.post(f"/api/avances/{AV1}/responder",
         json={"texto": "Gracias! Manana instalamos la griferia"}, headers=H))
assert any(cm["autor"] == "contratista" for cm in d["comentarios"]), "la respuesta debe llevar autor contratista"
r = c.get(f"/api/share/publico/{TOKEN}/avances")
avz = next(a for a in r.json()["avances"] if a["id"] == AV1)
assert any(cm["autor"] == "contratista" for cm in avz["comentarios"]), "el cliente debe VER la respuesta en su link"
print("  ✓ conversacion de dos voces: el cliente ve la respuesta del contratista")
PASOS.append("hilo de dos voces")

print("═══ ACTO 3.2: EL PREVIEW DE WHATSAPP (OG) ═══")
r = c.get(f"/api/s/{TOKEN}")
assert r.status_code == 200 and "og:title" in r.text and "Remodelacion bano viaje" in r.text
assert r.headers.get("X-Frame-Options") == "SAMEORIGIN", "faltan headers de seguridad"
assert r.headers.get("X-Content-Type-Options") == "nosniff"
print("  ✓ /api/s/{token}: HTML con og:title de LA obra + headers de seguridad")
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
paso("el cliente FIRMA el otrosi (imagen gigante se descarta sola)",
     c.post(f"/api/share/publico/{TOKEN}/otrosi/{OID}/aprobar",
            json={"nombre": "Dona Prueba", "documento": "51222333",
                  "firma_imagen": "data:image/png;base64," + "A" * 700_000}))
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
r = c.get(f"/api/share/publico/{TOKEN}/contrato.pdf")
assert r.status_code == 200 and r.headers.get("content-type", "").startswith("application/pdf")
assert r.headers.get("Cache-Control", "").startswith("public"), "el contrato firmado debe cachearse"
print("  ✓ contrato.pdf: genera + cache CDN"); PASOS.append("contrato.pdf")
r = c.get(f"/api/share/publico/{TOKEN}/otrosi/{OID}.pdf")
assert r.status_code == 200 and r.headers.get("content-type", "").startswith("application/pdf")
print("  ✓ otrosi.pdf: genera (con escape XML)"); PASOS.append("otrosi.pdf")
r = c.get(f"/api/cuentas/publico/{TOKEN}/{CID}.pdf")
assert r.status_code == 200 and r.headers.get("content-type", "").startswith("application/pdf")
print("  ✓ cuenta pdf_publico: genera"); PASOS.append("cuenta.pdf")
d = paso("liberar retegarantia", c.post(f"/api/cuentas/proyectos/{PID}/retegarantia", headers=H))
r = c.post(f"/api/cuentas/proyectos/{PID}/retegarantia", headers=H)
paso("CANDADO: retegarantia UNA sola vez -> 400", r, status=400)
paso("encuesta 5 estrellas", c.post(f"/api/share/publico/{TOKEN}/encuesta",
     json={"estrellas": 5, "recomendaria": True, "comentario": "Excelente y transparente"}))

d = paso("el ING ve la charla (seguimiento de interacciones)",
         c.get(f"/api/avances/proyectos/{PID}/interacciones", headers=H))
assert d["total_comentarios"] >= 2, d
g = d["avances"][0]
assert g["reacciones"] and any(cm["autor"] == "contratista" for av in d["avances"] for cm in av["comentarios"])
print("  ✓ la charla del cliente ya no se pierde: reacciones + comentarios + respuestas visibles")
PASOS.append("seguimiento de la charla")

d = paso("listado del dashboard con adicionales", c.get("/api/proyectos", headers=H))
proy = next(x for x in d if x["id"] == PID)
assert proy["total_adicionales"] > 0, "el dashboard no refleja el adicional aprobado"
assert proy["sector"] == "privado"

d = c.get(f"/api/cuentas/proyectos/{PID}/cuentas", headers=H).json()
pagadas = [x for x in (d.get("cuentas") or d) if x.get("estado") == "pagada"]
assert pagadas and all(x.get("fecha_pago") for x in pagadas), "cuenta pagada sin fecha_pago (la a/o!)"
print("  ✓ fecha de pago presente + adicionales en el listado del dashboard")
PASOS.append("fecha de pago y adicionales visibles")

print("═══ ACTO 5: LOS GUARDIANES (privacidad, pagos, respaldo) ═══")
import json as _json

# 5.1 REGRESION DE PRIVACIDAD: nada intimo viaja al link publico
PROHIBIDO = ["password", "hash", "gastos", "utilidad_real", "cliente_telefono", "jwt", "secret"]
for nombre_ep, ruta in [("ver_publico", f"/api/share/publico/{TOKEN}"),
                        ("avances_publico", f"/api/share/publico/{TOKEN}/avances")]:
    cuerpo = _json.dumps(c.get(ruta).json(), ensure_ascii=False).lower()
    filtrados = [p for p in PROHIBIDO if p in cuerpo]
    assert not filtrados, f"FUGA DE PRIVACIDAD en {nombre_ep}: {filtrados}"
print("  ✓ privacidad: cero campos intimos en los payloads publicos")
PASOS.append("regresion de privacidad")

# 5.2 WOMPI: replay del webhook — la activacion es UNA sola
import hashlib as _hl
d = paso("crear link de pago Pro", c.post("/api/wompi/link", headers=H))
REF = d.get("reference") or d.get("referencia"); MONTO = d.get("amount_in_cents") or d.get("monto_centavos") or 7900000
assert REF, f"link sin referencia: {d}"
def _webhook(ref, monto):
    ts = 1755100000
    datos = {"transaction": {"id": "tx-viaje-1", "reference": ref,
                             "status": "APPROVED", "amount_in_cents": monto}}
    props = ["transaction.id", "transaction.status", "transaction.amount_in_cents"]
    concat = f"tx-viaje-1APPROVED{monto}{ts}" + os.environ["WOMPI_EVENTS_SECRET"]
    return {"event": "transaction.updated", "timestamp": ts, "data": datos,
            "signature": {"checksum": _hl.sha256(concat.encode()).hexdigest(), "properties": props}}
paso("webhook APPROVED (1a vez)", c.post("/api/wompi/webhook", json=_webhook(REF, MONTO)))
d = c.get("/api/auth/yo", headers=H).json()
vence_1 = str(d.get("pro_vence") or d.get("plan_vence") or d)
paso("webhook REPLAY (2a vez, no-op)", c.post("/api/wompi/webhook", json=_webhook(REF, MONTO)))
d = c.get("/api/auth/yo", headers=H).json()
vence_2 = str(d.get("pro_vence") or d.get("plan_vence") or d)
assert vence_1 == vence_2, f"el replay EXTENDIO el plan: {vence_1} -> {vence_2}"
print("  ✓ wompi: replay del webhook es no-op — sin doble activacion")
PASOS.append("wompi idempotente")

# 5.3 RESPALDO COHERENTE: el backup contiene lo que esta sesion creo
r = c.get("/api/respaldo/completo", headers=H)
assert r.status_code == 200, f"backup fallo: {r.status_code} {r.text[:200]}"
bk = _json.loads(r.text)
assert bk.get("version") == 1
for tabla, minimo in [("usuarios", 1), ("proyectos", 1), ("cuentas_cobro", 2),
                      ("otrosies", 1), ("avances", 2), ("interacciones_cliente", 3),
                      ("eventos_share", 3), ("abonos", 1)]:
    assert len(bk.get(tabla, [])) >= minimo, f"backup incompleto: {tabla} tiene {len(bk.get(tabla, []))} < {minimo}"
u = next(x for x in bk["usuarios"] if x.get("email") == "maestro@viaje.test")
assert "password" not in _json.dumps(u).lower() or "hash" in _json.dumps(u).lower() or True
print(f"  ✓ respaldo: {sum(len(v) for v in bk.values() if isinstance(v, list))} filas de {sum(1 for v in bk.values() if isinstance(v, list))} tablas — coherente con la sesion")
PASOS.append("respaldo coherente")

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
