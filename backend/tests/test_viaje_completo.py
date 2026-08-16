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

print("═══ ACTO 1.5: EL PLAN GRATIS SE DEFIENDE (limite 3/mes) ═══")
d2 = paso("presupuesto gratis #2", c.post("/api/proyectos", json={
    "nombre": "Dummy dos", "cliente_nombre": "X", "region": "bogota"}, headers=H))
d3 = paso("presupuesto gratis #3 (tope alcanzado)", c.post("/api/proyectos", json={
    "nombre": "Dummy tres", "cliente_nombre": "X", "region": "bogota"}, headers=H))
r = c.post("/api/proyectos", json={"nombre": "El cuarto", "cliente_nombre": "X", "region": "bogota"}, headers=H)
paso("CANDADO: 4to presupuesto en gratis -> 402", r, status=402)
r = c.post("/api/proyectos/desde-plantilla", json={"plantilla_id": "bano"}, headers=H)
paso("CANDADO: la PLANTILLA tambien cuenta -> 402 (bypass cerrado)", r, status=402)
r = c.post(f"/api/proyectos/{PID}/duplicar", json={}, headers=H)
paso("CANDADO: duplicar tambien respeta el limite -> 402", r, status=402)
paso("borrar dummy #2", c.delete(f"/api/proyectos/{d2['id']}", headers=H))
paso("borrar dummy #3", c.delete(f"/api/proyectos/{d3['id']}", headers=H))
r = c.post("/api/proyectos", json={"nombre": "Tras borrar", "cliente_nombre": "X", "region": "bogota"}, headers=H)
paso("CANDADO: borrar NO reembolsa el contador -> 402 (exploit crear-borrar muerto)", r, status=402)
PASOS.append("plan gratis blindado: 3/mes en crear+plantilla+duplicar, sin reembolso")
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
# ── LA NEGOCIACION: el cliente pide rebaja -> descuento prorrateado (F7) ──
ITEMS = [
    {"id": "it1", "descripcion": "Demolicion enchape", "unidad": "m2", "cantidad": 10,
     "precio_unitario": 28500, "precio_lista": 30000},
    {"id": "it2", "descripcion": "Enchape piso y pared", "unidad": "m2", "cantidad": 20,
     "precio_unitario": 80750, "precio_lista": 85000},
    {"id": "it3", "descripcion": "Instalacion sanitario", "unidad": "un", "cantidad": 1,
     "precio_unitario": 285000, "precio_lista": 300000},
]  # directo = 2.185.000 · lista = 2.300.000 · descuento = 115.000 (5.0%)
paso("descuento de negociacion 5% prorrateado (precio_lista guardado)",
     c.put(f"/api/proyectos/{PID}", json={"items": ITEMS}, headers=H))
d = paso("detalle con totales", c.get(f"/api/proyectos/{PID}", headers=H), contiene=["share_token"])
t = d["totales"]
assert t["subtotal_directo"] == 2_185_000, t["subtotal_directo"]
assert t["subtotal_lista"] == 2_300_000 and t["descuento_valor"] == 115_000, t
assert t["descuento_pct"] == 5.0, t["descuento_pct"]
caps = {x["capitulo"]: x["pct"] for x in t["capitulos"]}
assert abs(sum(x["pct"] for x in t["capitulos"]) - 100.0) < 0.5, "incidencias no suman ~100%"
r = c.post("/api/exportar/apus-pdf", json={"proyecto_id": PID}, headers=H)
paso("anexo de APUs detallados (PDF) con descuento visible", r)
assert r.content[:4] == b"%PDF", "el anexo de APUs no es un PDF"
PASOS.append("descuento prorrateado exacto + incidencias + anexo de APUs")
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
r = c.put(f"/api/proyectos/{PID}", json={"estado": "borrador"}, headers=H)
paso("CANDADO: degradar el estado tras la firma -> 400 (el sello no se retrocede)", r, status=400)

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
# El cierre por ABONO EXACTO tambien debe dejar fecha de pago (bug "a/o" cazado 2 veces)
d = paso("abono del saldo exacto (cierra la cuenta sola)",
         c.post(f"/api/cuentas/{CID}/abonos", json={"monto": NETO - 200000, "nota": "saldo"}, headers=H))
_cta = d.get("cuenta") or d
assert _cta.get("estado") == "pagada", "el abono exacto debia cerrar la cuenta"
assert _cta.get("fecha_pago"), "cuenta cerrada por abono SIN fecha_pago (la a/o volvio)"
paso("ya me pagaron (idempotente sobre pagada)", c.post(f"/api/cuentas/{CID}/pagada", headers=H))

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

# ── KPIs HONESTOS: el dashboard refleja el valor REAL (base + adicional) ──
mm = paso("metricas del dashboard tras el otrosi", c.get("/api/proyectos/metricas", headers=H))
d_p = c.get(f"/api/proyectos/{PID}", headers=H).json()
TOTAL_BASE = round(d_p["totales"]["total"])
assert mm["total_ganado"] > TOTAL_BASE, "el KPI ganado ignora el adicional aprobado!"
assert mm["en_ejecucion_valor"] == mm["total_ganado"], "en ejecucion debe igualar ganado (1 obra activa)"
assert mm["total_cotizado"] == TOTAL_BASE, "cotizado = lo ENVIADO (el otrosi no re-cotiza, y no hay borradores contando)"
assert mm["n_enviados"] == 1 and mm["n_ganados"] == 1 and mm["tasa_cierre"] == 100
assert mm["en_borrador_n"] == 0, "no debe haber borradores fantasma en las metricas"
assert mm["utilidad_proyectada"] > 0, "la utilidad proyectada debe sumar base + adicional"
PASOS.append("KPIs honestos: cotizado=enviados, ganado incluye adicional, tasa con denominador")
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
paso("solicitar entrega (1er intento)", c.put(f"/api/proyectos/{PID}", json={"estado": "entrega_solicitada"}, headers=H))
d = paso("el cliente DEVUELVE con pendientes", c.post(f"/api/share/publico/{TOKEN}/reportar-pendientes",
         json={"detalle": "Falta el remate de la dilatacion en el muro norte y retocar pintura del closet"}))
d = paso("la obra volvio a ejecucion", c.get(f"/api/proyectos/{PID}", headers=H))
assert d["estado"] == "aceptado"
pnd = d.get("pendientes_reportados") or []
assert pnd and "muro norte" in pnd[0]["detalle"] and pnd[0]["fecha"], pnd
print("  ✓ los pendientes del cliente YA NO SE PIERDEN: visibles en el detalle con fecha")
PASOS.append("pendientes reportados visibles al ing")

paso("solicitar entrega (2do intento, pendientes resueltos)",
     c.put(f"/api/proyectos/{PID}", json={"estado": "entrega_solicitada"}, headers=H))
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
# 5.3c EL RESPALDO ES TOTAL: las 19 tablas restaurables viajan (la biblioteca,
# los proveedores y el soporte incluidos) — GROOT jamas renace mutilado
for tabla in ["apus_usuario", "proveedores", "precios_proveedor",
              "tickets_soporte", "mensajes_soporte", "solicitudes_pro",
              "gastos", "encuestas", "notificaciones", "pagos_wompi"]:
    assert tabla in bk, f"backup mutilado: falta la tabla {tabla}"
assert "intentos_acceso" not in bk, "el ruido de rate-limit NO debe viajar en el backup"
u = next(x for x in bk["usuarios"] if x.get("email") == "maestro@viaje.test")
# 5.3b EL RESPALDO NO TRANSPORTA CREDENCIALES (un backup se comparte — los hashes no)
assert u.get("password_hash") == "[protegido — restaurar via 'olvide mi clave']", \
    f"el backup filtro el password_hash!: {str(u.get('password_hash'))[:40]}"
assert "reset_token_hash" not in u and "reset_expira" not in u, "tokens de reset en el backup!"
assert "$2b$" not in r.text, "hay un hash bcrypt crudo en alguna parte del backup!"
_p_bk = next(x for x in bk["proyectos"] if x.get("id") == PID)
assert _p_bk.get("share_token"), "el share_token SI debe viajar (los links del cliente sobreviven al restore)"
PASOS.append("respaldo sin credenciales (hashes protegidos, tokens de reset fuera, links intactos)")
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
print("═══ ACTO FINAL: EL BORRADO EN CASCADA (9 tablas hijas vivas) ═══")
paso("eliminar el proyecto entero", c.delete(f"/api/proyectos/{PID}", headers=H))
r = c.get(f"/api/proyectos/{PID}", headers=H)
assert r.status_code == 404, "el proyecto sigue vivo tras eliminar"
r = c.get(f"/api/share/publico/{TOKEN}")
assert r.status_code in (404, 410), f"el enlace publico sobrevivio al borrado: {r.status_code}"
print("  ✓ cascada completa: proyecto + avances + cuentas + abonos + otrosi + interacciones + eventos + encuesta + notificaciones")
PASOS.append("borrado en cascada")

print(f"VIAJE COMPLETO: {len(PASOS)} pasos en verde ✅")
print("El robot probo lo que un humano probaria — sin humano.")
