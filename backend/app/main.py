# -*- coding: utf-8 -*-
"""PresupuestarCO v8 — Presupuestador APU para el contratista colombiano."""
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="PresupuestarCO", version="8.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar BD
from app.db import init_db
init_db()
logger.info("Base de datos inicializada")

# Routers core del nuevo producto
from app.api import auth, proyectos, share, precios, exportar, avances, pagos, soporte, notificaciones, gastos, cuentas, clientes, onboarding, wompi, respaldo, otrosies, apus, proveedores, insumos, disenos
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(proyectos.router, prefix="/api/proyectos", tags=["proyectos"])
app.include_router(share.router, prefix="/api/share", tags=["share"])
app.include_router(avances.router, prefix="/api/avances", tags=["avances"])
app.include_router(pagos.router, prefix="/api/pagos", tags=["pagos"])
app.include_router(soporte.router, prefix="/api/soporte", tags=["soporte"])
app.include_router(notificaciones.router, prefix="/api/notificaciones", tags=["notificaciones"])
app.include_router(gastos.router, prefix="/api/gastos", tags=["gastos"])
app.include_router(cuentas.router, prefix="/api/cuentas", tags=["cuentas"])
app.include_router(clientes.router, prefix="/api/clientes", tags=["clientes"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(wompi.router, prefix="/api/wompi", tags=["wompi"])
app.include_router(respaldo.router, prefix="/api/respaldo", tags=["respaldo"])
app.include_router(apus.router, prefix="/api/apus", tags=["apus"])
app.include_router(insumos.router, prefix="/api/insumos", tags=["insumos"])
app.include_router(disenos.router, prefix="/api/disenos", tags=["disenos"])
app.include_router(proveedores.router, prefix="/api/proveedores", tags=["proveedores"])
app.include_router(otrosies.router, prefix="/api/otrosies", tags=["otrosies"])


@app.get("/api/health")
def health():
    """Monitor de vida (UptimeRobot): app + base de datos."""
    from sqlalchemy import text
    from app.db import SessionLocal
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    finally:
        try:
            db.close()
        except Exception:
            pass
    return {"ok": db_ok, "db": "ok" if db_ok else "error"}
app.include_router(precios.router, prefix="/api/precios", tags=["precios"])
app.include_router(exportar.router, prefix="/api/exportar", tags=["exportar"])

# Routers heredados (feature premium IA + validacion)
try:
    from app.api import planos, presupuesto, mercado, validacion, feedback
    app.include_router(planos.router, prefix="/api/planos", tags=["planos-ia"])
    app.include_router(presupuesto.router, prefix="/api/presupuesto", tags=["presupuesto-ia"])
    app.include_router(mercado.router, prefix="/api/mercado", tags=["mercado"])
    app.include_router(validacion.router, prefix="/api/validacion", tags=["validacion"])
    app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])
    logger.info("Modulos IA premium cargados")
except Exception as e:
    logger.warning(f"Modulos IA no disponibles: {e}")


@app.get("/api/config")
async def config_publica():
    """Config publica para el frontend (sin auth)."""
    import os
    return {
        "whatsapp_soporte": os.environ.get("WHATSAPP_SOPORTE", "").strip(),
    }


@app.get("/health")
async def health():
    from app.services.apu_service import load_apu_db
    try:
        n_apus = len(load_apu_db())
    except Exception:
        n_apus = 0
    return {
        "status": "ok",
        "version": "8.0.0",
        "producto": "PresupuestarCO — Presupuestos APU para contratistas",
        "apus_disponibles": n_apus,
        "features": [
            "Presupuestos con APU 2026 (2,288 actividades)",
            "AIU configurable + IVA sobre utilidad (Art. 462-1 ET)",
            "Enlace WhatsApp con tracking de vistas y boton aceptar",
            "Export Excel y PDF con logo",
            "Precios por region (13 ciudades)",
            "PREMIUM: lectura de planos con IA + validacion NSR-10",
        ],
    }

# ═══════════ PREVIEW DE WHATSAPP: /api/s/{token} ═══════════
# Los bots de WhatsApp/redes leen las meta OG (que una SPA no puede personalizar);
# los humanos son redirigidos al instante a /p/{token}. El boton de compartir usa esta URL.
from fastapi.responses import HTMLResponse, Response as _Resp


@app.middleware("http")
async def headers_de_seguridad(request, call_next):
    """Blindaje perimetral: anti-iframe (phishing), anti-sniffing, referrer sobrio."""
    resp = await call_next(request)
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return resp


@app.get("/api/s/{token}")
def preview_social(token: str):
    import html as _html
    import json as _json
    from app.db import SessionLocal, Proyecto, Usuario
    db = SessionLocal()
    try:
        p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
        if not p or (p.sector or "privado") == "publico":
            return HTMLResponse("<h1>Este enlace no existe o fue retirado</h1>", status_code=404)
        u = db.query(Usuario).filter(Usuario.id == p.user_id).first()
        # PRIVACIDAD: el MONTO jamas viaja en el preview (WhatsApp lo cachea y
        # cualquiera en el chat lo ve sin abrir). La cifra se ve AL ABRIR, con el token.
        titulo = _html.escape(f"🏗️ {p.nombre} — {u.empresa or u.nombre}")
        firmado = p.estado not in ("borrador", "enviado", "visto", "rechazado")
        desc = _html.escape(
            ("Tu obra en vivo: avances con fotos, cuentas claras y documentos al dia"
             if firmado else
             "Tu presupuesto esta listo — revisa el detalle y firma desde tu celular"))
        destino = f"/p/{token}"
        # ¿foto del ultimo avance como imagen del preview?
        tiene_foto = False
        try:
            from app.db import Avance
            ult = (db.query(Avance).filter(Avance.proyecto_id == p.id)
                   .order_by(Avance.creado.desc()).first())
            tiene_foto = bool(ult and _json.loads(ult.fotos_json or "[]"))
        except Exception:
            pass
        imagen = f"/api/s/{token}/foto.jpg" if tiene_foto else "/og.png"
        base = os.environ.get("APP_URL", "https://presupuestar-co.vercel.app").rstrip("/")
        return HTMLResponse(f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>{titulo}</title>
<meta property="og:type" content="website">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{base}{imagen}">
<meta property="og:url" content="{base}{destino}">
<meta name="twitter:card" content="summary_large_image">
<meta http-equiv="refresh" content="0;url={destino}">
</head><body>
<p style="font-family:sans-serif">Abriendo tu obra... <a href="{destino}">clic aqui si no avanza</a></p>
<script>location.replace("{destino}")</script>
</body></html>""")
    finally:
        db.close()


@app.get("/api/s/{token}/foto.jpg")
def preview_foto(token: str):
    """La foto del ultimo avance como imagen del preview (decodificada del base64)."""
    import base64
    import json as _json
    from app.db import SessionLocal, Proyecto, Avance
    db = SessionLocal()
    try:
        p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
        if not p or (p.sector or "privado") == "publico":
            return _Resp(status_code=404)
        ult = (db.query(Avance).filter(Avance.proyecto_id == p.id)
               .order_by(Avance.creado.desc()).first())
        fotos = _json.loads(ult.fotos_json or "[]") if ult else []
        if not fotos or "," not in fotos[0]:
            return _Resp(status_code=404)
        datos = base64.b64decode(fotos[0].split(",", 1)[1])
        return _Resp(content=datos, media_type="image/jpeg",
                     headers={"Cache-Control": "public, max-age=3600"})
    finally:
        db.close()
