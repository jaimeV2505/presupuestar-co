from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from app.services.claude_service import extract_from_plan

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED = {
    "application/pdf",
    "image/png","image/jpeg","image/jpg","image/webp",
    # DWG/DXF
    "application/dwg","application/dxf","application/acad",
    "image/vnd.dwg","application/octet-stream",
}

@router.post("/extraer")
async def extraer(
    file: UploadFile = File(...),
    contexto: Optional[str] = Form(None),
    region: str = Form("bogota"),
):
    ct = file.content_type or ""
    fn = file.filename or ""
    is_pdf = ct == "application/pdf" or fn.lower().endswith(".pdf")
    is_img = any(fn.lower().endswith(e) for e in [".png",".jpg",".jpeg",".webp"])
    is_dwg = any(fn.lower().endswith(e) for e in [".dwg",".dxf"])

    if ct not in ALLOWED and not is_pdf and not is_img and not is_dwg:
        raise HTTPException(415, f"Tipo no soportado: {ct}. Use PDF, PNG, JPG o DWG/DXF.")

    data = await file.read()
    if len(data) > 30 * 1024 * 1024:
        raise HTTPException(413, "Archivo muy grande. Máximo 30MB.")

    logger.info(f"Procesando: {fn} ({len(data)//1024}KB) | región: {region}")

    try:
        result = await extract_from_plan(data, ct or "application/pdf", contexto or "", fn)
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        logger.error(f"Error extracción: {e}", exc_info=True)
        raise HTTPException(500, f"Error procesando plano: {str(e)}")
