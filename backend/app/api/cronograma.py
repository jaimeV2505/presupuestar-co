# -*- coding: utf-8 -*-
"""
Cronograma de obra — SOLO para proyectos de sector publico (obra estatal).

Filas libres (el usuario decide si son capitulos, items, o una mezcla), cada
una con duracion en semanas y, opcionalmente, una predecesora (dependencia
fin-a-inicio: arranca justo cuando termina la anterior). Se cruza con el
ultimo % de avance real cargado (avances.py) para mostrar planeado-vs-real.
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto, Avance
from app.api.auth import usuario_actual
from app.services.cronograma_service import (
    resolver_cronograma, duracion_total_semanas, cruzar_con_avance_real,
    CronogramaError, MAX_FILAS,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class FilaCronograma(BaseModel):
    id: str = Field(..., min_length=1, max_length=40)
    nombre: str = Field(..., min_length=1, max_length=200)
    duracion_semanas: float = Field(..., gt=0, le=260)  # hasta 5 años, tope razonable
    semana_inicio: Optional[float] = Field(0, ge=0, le=520)
    predecesora_id: Optional[str] = None
    orden: Optional[int] = 0


class CronogramaRequest(BaseModel):
    filas: List[FilaCronograma]


def _proyecto_publico(proyecto_id: int, user: Usuario, db: Session) -> Proyecto:
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    if (p.sector or "privado") != "publico":
        raise HTTPException(400, "El cronograma es una herramienta exclusiva de obra publica")
    return p


def _armar_respuesta(p: Proyecto, db: Session) -> dict:
    data = json.loads(p.cronograma_json or "{}")
    filas = data.get("filas", [])
    contrato = json.loads(p.contrato_json or "{}")
    try:
        resueltas = resolver_cronograma(filas) if filas else []
        error = None
    except CronogramaError as e:
        # datos guardados quedaron inconsistentes (no deberia pasar si PUT valida
        # bien, pero si pasa, mejor mostrar el error que un 500)
        resueltas, error = [], str(e)

    ultimo = (db.query(Avance).filter(Avance.proyecto_id == p.id)
              .order_by(Avance.creado.desc()).first())
    pct_real = ultimo.porcentaje if ultimo else None
    resueltas = cruzar_con_avance_real(resueltas, pct_real)

    return {
        "filas": resueltas,
        "error": error,
        "fecha_inicio": contrato.get("fecha_inicio"),
        "plazo_dias_contrato": contrato.get("plazo_dias"),
        "pct_avance_real": pct_real,
        "duracion_total_semanas": duracion_total_semanas(resueltas) if resueltas else 0,
    }


@router.get("/{proyecto_id}")
def obtener(proyecto_id: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto_publico(proyecto_id, user, db)
    return _armar_respuesta(p, db)


@router.put("/{proyecto_id}")
def guardar(proyecto_id: int, req: CronogramaRequest,
           user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto_publico(proyecto_id, user, db)
    if len(req.filas) > MAX_FILAS:
        raise HTTPException(400, f"Maximo {MAX_FILAS} filas en el cronograma")

    filas = [f.dict() for f in req.filas]
    ids = [f["id"] for f in filas]
    if len(ids) != len(set(ids)):
        raise HTTPException(400, "Hay ids de fila repetidos")

    try:
        resolver_cronograma(filas)  # solo para validar (ciclos, predecesora inexistente) ANTES de guardar
    except CronogramaError as e:
        raise HTTPException(400, str(e))

    p.cronograma_json = json.dumps({"filas": filas}, ensure_ascii=False)
    db.commit()
    logger.info(f"cronograma guardado: proyecto {p.id}, {len(filas)} filas")
    return _armar_respuesta(p, db)
