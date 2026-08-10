"""API de validación NSR-10 y calculadora de acero exacto."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.validators.nsr10_validator import validar_elementos, ResultadoValidacion
from app.services.validators.steel_calculator import (
    calcular_acero_columna_exacto, calcular_acero_viga_exacto, calcular_acero_zapata_exacto
)
from app.services.scale_service import detectar_escala

router = APIRouter()

class ValidarElementosReq(BaseModel):
    elementos: List[Dict]
    fc_mpa: float = 20.7
    fy_mpa: float = 420.0
    zona_sismica: str = "alta"

class AceroColumnaReq(BaseModel):
    ancho_cm: float; alto_cm: float; altura_m: float
    acero_long: str; acero_trans: str = ""
    num_columnas: int = 1
    fc_mpa: float = 20.7; fy_mpa: float = 420.0

class AceroZapataReq(BaseModel):
    largo_cm: float; ancho_cm: float; espesor_cm: float
    acero_dir1: str; acero_dir2: str = ""
    num_zapatas: int = 1

@router.post("/nsr10")
def validar_nsr10(req: ValidarElementosReq):
    """Valida elementos estructurales contra NSR-10."""
    try:
        resultado = validar_elementos(req.elementos, req.fc_mpa, req.fy_mpa, req.zona_sismica)
        return {
            "puntuacion": resultado.puntuacion,
            "zona_sismica": resultado.zona_sismica,
            "total_alertas": len(resultado.alertas),
            "errores": len([a for a in resultado.alertas if a.severidad=="ERROR"]),
            "advertencias": len([a for a in resultado.alertas if a.severidad=="ADVERTENCIA"]),
            "alertas": [{"codigo":a.codigo,"severidad":a.severidad,"elemento":a.elemento,
                         "mensaje":a.mensaje,"valor_actual":a.valor_actual,
                         "valor_requerido":a.valor_requerido,"unidad":a.unidad}
                        for a in resultado.alertas],
            "correcciones": resultado.correcciones,
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/acero/columna")
def acero_columna(req: AceroColumnaReq):
    """Calcula acero exacto de columna desde especificación."""
    try:
        r = calcular_acero_columna_exacto(
            req.ancho_cm, req.alto_cm, req.altura_m,
            req.acero_long, req.acero_trans, req.num_columnas, req.fc_mpa, req.fy_mpa
        )
        return {"kg_longitudinal":r.kg_longitudinal,"kg_transversal":r.kg_transversal,
                "kg_total":r.kg_total,"detalle_long":r.detalle_longitudinal,
                "detalle_trans":r.detalle_transversal,"metodo":r.metodo,"advertencias":r.advertencias}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/acero/zapata")
def acero_zapata(req: AceroZapataReq):
    """Calcula acero exacto de zapata desde especificación."""
    try:
        r = calcular_acero_zapata_exacto(
            req.largo_cm, req.ancho_cm, req.espesor_cm,
            req.acero_dir1, req.acero_dir2, req.num_zapatas
        )
        return {"kg_total":r.kg_total,"detalle":r.detalle_longitudinal,
                "metodo":r.metodo,"advertencias":r.advertencias}
    except Exception as e:
        raise HTTPException(500, str(e))

# ── Predimensionamiento ──────────────────────────────────────────────────────
from app.services.validators.predim import (
    verificar_predimensionamiento, CARGAS_USO, QA_SUELO,
    predim_viga, predim_columna, predim_zapata
)
from app.services.validators.elementos_secundarios import (
    calcular_correas_desde_separacion, calcular_malla_electrosoldada,
    get_malla_catalogo
)

class PredimRequest(BaseModel):
    elementos: List[Dict]
    uso: str = "vivienda"
    fc_mpa: float = 20.7
    fy_mpa: float = 420.0
    tipo_suelo: str = "S2"
    num_pisos: int = 1

@router.post("/predimensionamiento")
def predimensionamiento(req: PredimRequest):
    """Verifica si las secciones aguantan las cargas estimadas."""
    try:
        res = verificar_predimensionamiento(
            req.elementos, req.uso, req.fc_mpa, req.fy_mpa,
            req.tipo_suelo, req.num_pisos
        )
        return {
            "resumen": res.resumen,
            "alertas": [
                {"severidad": a.severidad, "elemento": a.elemento,
                 "mensaje": a.mensaje, "valor_actual": a.valor_actual,
                 "valor_minimo": a.valor_minimo, "unidad": a.unidad,
                 "recomendacion": a.recomendacion}
                for a in res.alertas
            ],
            "indicadores": res.indicadores,
            "usos_disponibles": {k: v["desc"] for k, v in CARGAS_USO.items()},
            "suelos_disponibles": QA_SUELO,
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/correas")
def calcular_correas(
    area_m2: float = 536.5,
    separacion_m: float = 1.52,
    longitud_crujia_m: float = 32.94,
    perfil: str = "PHR 160x60x2"
):
    """Calcula metros de correas desde separacion y area de cubierta."""
    try:
        return calcular_correas_desde_separacion(
            area_m2, separacion_m, longitud_crujia_m, perfil
        )
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/mallas")
def mallas_catalogo():
    """Catalogo de mallas electrosoldadas NTC 2261."""
    return get_malla_catalogo()

@router.get("/malla/calcular")
def calcular_malla(area_m2: float = 100.0, referencia: str = "M-188"):
    """Calcula kg de malla electrosoldada para una losa."""
    try:
        return calcular_malla_electrosoldada(area_m2, referencia)
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/traslapes")
def calcular_traslapes(
    db_mm: float = 15.9,
    fc_mpa: float = 20.7,
    fy_mpa: float = 420.0,
    clase: str = "B"
):
    """Calcula longitud de traslape NSR-10 C.12.15."""
    try:
        from app.services.validators.nsr10_validator import longitud_traslape, longitud_desarrollo
        lt = longitud_traslape(db_mm, fc_mpa, fy_mpa, clase)
        ld = longitud_desarrollo(db_mm, fc_mpa, fy_mpa)
        return {
            "db_mm": db_mm,
            "fc_mpa": fc_mpa,
            "fy_mpa": fy_mpa,
            "clase_traslape": clase,
            "longitud_desarrollo_cm": round(ld, 1),
            "longitud_traslape_cm": round(lt, 1),
            "referencia": "NSR-10 C.12.15",
            "nota": "Clase A: <= 50% barras traslapadas | Clase B: > 50% o zona plastica"
        }
    except Exception as e:
        raise HTTPException(500, str(e))
