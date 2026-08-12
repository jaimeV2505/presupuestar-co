from fastapi import APIRouter, Query
from typing import Optional
from app.services import apu_service as APU

router = APIRouter()

@router.get("/")
def get_precios(
    region: str = Query("bogota"),
    categoria: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
):
    db = APU.load_apu_db()
    from app.services.apu_service import FACTORES_REGION
    factor = FACTORES_REGION.get(region, FACTORES_REGION["bogota"])["factor"]
    nombre = FACTORES_REGION.get(region, FACTORES_REGION["bogota"])["nombre"]

    results = []
    for item in db:
        if categoria and item["categoria"] != categoria: continue
        from app.services.apu_service import _sin_tildes as _st
        if q and _st(q) not in _st(item["descripcion"]) and _st(q) not in _st(item.get("categoria", "")): continue
        results.append({**item, "precio": round(item["precio"] * factor)})

    return {
        "items": results[:limit],
        "total": len(results),
        "region": region,
        "nombre_region": nombre,
        "factor_region": factor,
        "fuente": "APU 2026 — Escuela de Contratistas",
        "categorias": APU.get_all_categories(),
    }

@router.get("/regiones")
def get_regiones():
    return {"regiones": APU.get_all_regions()}

@router.get("/stats")
def get_stats():
    db = APU.load_apu_db()
    from collections import Counter
    cats = Counter(x["categoria"] for x in db)
    return {"total_actividades": len(db), "categorias": dict(cats)}

@router.get("/varillas")
def get_varillas():
    """Tabla de caracterización de varillas de acero — pesos reales kg/m."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../data'))
    from tablas_tecnicas import VARILLAS
    return {
        "varillas": [
            {"numero": n, **v} for n, v in VARILLAS.items()
        ],
        "fuente": "Tabla de caracterización de varilla — Colombia",
        "nota": "Pesos según diámetro nominal ASTM/NTC"
    }

@router.get("/dosificacion-concreto")
def get_dosificacion_concreto(fc_mpa: float = 20.7):
    """Tabla de dosificación de concreto — cantidades por m³."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../data'))
    from tablas_tecnicas import get_materiales_por_m3, DOSIFICACION_CONCRETO
    return {
        "para_fc_mpa": fc_mpa,
        "dosificacion": get_materiales_por_m3(fc_mpa),
        "tabla_completa": DOSIFICACION_CONCRETO,
        "fuente": "Tabla de dosificación de concreto — Colombia",
        "nota": "Cantidades por m³ de concreto. Cemento: saco de 42.5kg"
    }
