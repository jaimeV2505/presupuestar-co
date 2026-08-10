"""API de precios de mercado en tiempo real y análisis de sensibilidad."""
from fastapi import APIRouter, Query
from app.services.price_scraper import (
    get_precios_actualizados, get_factor_iccv, analisis_sensibilidad,
    calcular_costo_materiales_concreto, PRECIOS_BASE_2026
)

router = APIRouter()

@router.get("/precios-mercado")
async def precios_mercado(region: str = Query("bogota")):
    """Precios de materiales actualizados con ICCV DANE."""
    return await get_precios_actualizados(region)

@router.get("/iccv")
async def iccv():
    """Factor ICCV actual del DANE."""
    factor = await get_factor_iccv()
    return {"factor_iccv": factor, "fuente": "DANE Colombia"}

@router.get("/costo-concreto")
async def costo_concreto(
    volumen_m3: float = Query(1.0, description="Volumen en m³"),
    fc_mpa: float = Query(20.7, description="Resistencia en MPa"),
    region: str = Query("bogota")
):
    """Calcula costo de materiales para concreto por volumen y resistencia."""
    return calcular_costo_materiales_concreto(volumen_m3, fc_mpa, region)

@router.post("/sensibilidad")
async def sensibilidad(presupuesto_total: float, items: list):
    """Análisis de sensibilidad ante alzas de precios."""
    return analisis_sensibilidad(presupuesto_total, items)

# ── Modulo D: Flete por distancia ────────────────────────────────────────────
from app.services.flete_service import calcular_factor_flete, get_regiones_disponibles

@router.get("/flete")
async def flete(
    region: str = "bogota",
    distancia_adicional_km: float = 0,
    tipo_estructura: str = "default"
):
    """Calcula el factor de flete para una region."""
    return calcular_factor_flete(region, distancia_adicional_km, tipo_estructura)

@router.get("/flete/regiones")
async def flete_regiones():
    """Lista todas las regiones con datos de flete."""
    return get_regiones_disponibles()

# ── Modulo E: APU desglosado ─────────────────────────────────────────────────
from app.services.apu_desglose import desglosar_item, desglosar_presupuesto, get_composiciones

@router.get("/apu/composiciones")
async def apu_composiciones():
    """Tabla de composiciones material/MO/equipo por capitulo."""
    return get_composiciones()

@router.get("/apu/desglosar")
async def apu_desglosar(precio: float, capitulo: str = "ESTRUCTURAS EN CONCRETO"):
    """Desglosa un precio en material/MO/equipo segun el capitulo."""
    return desglosar_item(precio, capitulo)
