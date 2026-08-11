# -*- coding: utf-8 -*-
"""PresupuestarCO v8 — Presupuestador APU para el contratista colombiano."""
import logging
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
from app.api import auth, proyectos, share, precios, exportar, avances, pagos, soporte, notificaciones, gastos, cuentas, clientes, onboarding
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
