from fastapi import APIRouter, HTTPException
import logging
from app.models.schemas import PresupuestoRequest, PresupuestoResponse
from app.services.budget_service import calcular_presupuesto

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/calcular", response_model=PresupuestoResponse)
async def calcular(req: PresupuestoRequest):
    try:
        return await calcular_presupuesto(
            elementos=req.elementos, region=req.region,
            fc_mpa=req.fc_concreto_mpa, fy_mpa=req.fy_acero_mpa,
            incluir_iva=req.incluir_iva, incluir_aiu=req.incluir_aiu,
            porcentaje_aiu=req.porcentaje_aiu,
        )
    except Exception as e:
        logger.error(f"Error cálculo: {e}", exc_info=True)
        raise HTTPException(500, str(e))
