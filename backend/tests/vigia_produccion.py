# -*- coding: utf-8 -*-
"""EL VIGIA — el robot que patrulla PRODUCCION en vivo, cada media hora.

CI previene ("nada roto llega"); el VIGIA vigila ("y si algo se cae a las
3am, me entero yo antes que un usuario"). Entra con la cuenta canario,
cotiza, verifica la matematica A PESO, comparte, mira como cliente y borra.

Secrets: APP_URL, VIGIA_EMAIL, VIGIA_PASSWORD (cuenta canario dedicada).
"""
import os
import sys

import httpx

URL = os.environ["APP_URL"].rstrip("/")
EMAIL = os.environ["VIGIA_EMAIL"]
CLAVE = os.environ["VIGIA_PASSWORD"]

FALLAS = []


def paso(nombre, r, status=200):
    ok = r.status_code == status
    print(("  ✓ " if ok else "  ❌ ") + nombre + ("" if ok else f"  [{r.status_code}] {r.text[:200]}"))
    if not ok:
        FALLAS.append(nombre)
    try:
        return r.json()
    except Exception:
        return {}


c = httpx.Client(timeout=30)

print(f"═══ EL VIGIA patrulla {URL} ═══")

# 1) la plataforma respira
paso("salud del API", c.get(f"{URL}/api/health"))

# 2) el canario entra
d = paso("login del canario", c.post(f"{URL}/api/auth/login",
         json={"email": EMAIL, "password": CLAVE}))
tok = d.get("token") or d.get("access_token") or ""
H = {"Authorization": f"Bearer {tok}"}
if not tok:
    print("VIGIA ROTO: sin token — nada mas que hacer")
    sys.exit(1)

# 3) cotiza — y la MATEMATICA a peso (numeros autocontenidos, sin depender de la base)
d = paso("crear presupuesto canario", c.post(f"{URL}/api/proyectos",
         json={"nombre": "🐤 Canario del vigia", "cliente_nombre": "Vigia", "region": "bogota"}, headers=H))
pid = d.get("id")
if not pid:
    print()
    print("🚨 EL VIGIA NO PUDO CREAR EL CANARIO — la causa esta arriba (¿cuota del plan gratis?)")
    print("   Cura: la cuenta canario debe ser PRO (ilimitada). En Neon SQL:")
    print("   UPDATE usuarios SET plan='pro', plan_vence=NULL WHERE email='<canario>';")
    sys.exit(1)
d = paso("items + AIU", c.put(f"{URL}/api/proyectos/{pid}", json={
    "items": [{"id": "v1", "capitulo": "VIGIA", "descripcion": "Item canario",
               "unidad": "un", "cantidad": 3, "precio_unitario": 1000}],
    "aiu": {"aplicar": True, "admin": 10, "imprevistos": 5, "utilidad": 5,
            "iva_sobre_utilidad": True}}, headers=H))
t = (d.get("totales") or {})
esperado_total = 3000 + 300 + 150 + 150 + round(150 * 0.19)   # 3.629
if t.get("total") != esperado_total:
    FALLAS.append(f"MATEMATICA ROTA EN PROD: total={t.get('total')} esperado={esperado_total}")
    print(f"  ❌ la matematica: total={t.get('total')} esperado={esperado_total}")
else:
    print(f"  ✓ la matematica cuadra a peso en PROD: {esperado_total}")

# 4) el enlace del cliente vive
d = paso("compartir", c.post(f"{URL}/api/share/proyectos/{pid}/compartir", headers=H))
token_pub = d.get("share_token") or (d.get("ruta_publica") or "").split("/p/")[-1]
d = paso("el cliente lo ve", c.get(f"{URL}/api/share/publico/{token_pub}"))
if (d.get("totales") or {}).get("total") not in (esperado_total, None):
    FALLAS.append("el cliente ve un total distinto")

# 5) limpiar el nido (la cascada del DELETE, patrullada de paso)
paso("borrar el canario (cascada)", c.delete(f"{URL}/api/proyectos/{pid}", headers=H))
r = c.get(f"{URL}/api/share/publico/{token_pub}")
paso("el enlace murio con el proyecto -> 404", r, status=404)

print()
if FALLAS:
    print(f"🚨 EL VIGIA ENCONTRO {len(FALLAS)} PROBLEMA(S) EN PRODUCCION:")
    for f in FALLAS:
        print("   -", f)
    sys.exit(1)
print("🐤 PRODUCCION SANA: la plataforma respira, la matematica cuadra, el enlace vive y muere bien.")
