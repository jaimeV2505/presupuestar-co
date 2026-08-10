from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional, List
from app.services import feedback_service as FB

router = APIRouter()

class CorreccionRequest(BaseModel):
    elemento_original: Dict
    elemento_corregido: Dict
    tipo_plano: Optional[str] = ""
    contexto: Optional[str] = ""

class AnalisisRequest(BaseModel):
    plano_nombre: str
    elementos_extraidos: int
    confianza: str

@router.post("/correccion")
def registrar_correccion(req: CorreccionRequest):
    """Registra una corrección del ingeniero — alimenta el sistema de aprendizaje."""
    try:
        result = FB.registrar_correccion(
            req.elemento_original, req.elemento_corregido,
            req.tipo_plano, req.contexto
        )
        return result
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/analisis")
def registrar_analisis(req: AnalisisRequest):
    """Registra que se procesó un plano."""
    try:
        FB.registrar_analisis(req.plano_nombre, req.elementos_extraidos, req.confianza)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/stats")
def get_stats():
    """Estadísticas del sistema de aprendizaje."""
    return FB.get_stats()

@router.get("/patrones")
def get_patrones():
    """Lista de patrones aprendidos del feedback."""
    stats = FB.get_stats()
    return {
        "total_patrones": stats["patrones_aprendidos"],
        "total_planos": stats["total_planos"],
        "total_correcciones": stats["total_correcciones"],
        "top_patrones": stats.get("top_patrones", []),
        "top_correcciones": stats.get("top_correcciones", []),
    }

@router.delete("/limpiar")
def limpiar(dias: int = 90):
    """Limpia correcciones antiguas."""
    return FB.limpiar_patrones_antiguos(dias)
