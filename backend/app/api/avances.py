# -*- coding: utf-8 -*-
"""Avances de obra: el contratista sube progreso, el cliente lo ve con su enlace."""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto, Avance
from app.api.auth import usuario_actual

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FOTOS = 3
MAX_FOTO_BYTES = 450_000  # ~450KB por foto en base64


class AvanceCreate(BaseModel):
    titulo: str
    descripcion: str = ""
    porcentaje: int = 0
    fotos: List[str] = []  # data URLs base64


def _avance_out(a: Avance):
    return {
        "id": a.id,
        "titulo": a.titulo,
        "descripcion": a.descripcion,
        "porcentaje": a.porcentaje,
        "fotos": json.loads(a.fotos_json or "[]"),
        "fecha": a.creado.strftime("%d/%m/%Y %H:%M"),
    }


def _proyecto_del_usuario(proyecto_id: int, user: Usuario, db: Session) -> Proyecto:
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    return p


@router.get("/proyectos/{proyecto_id}/avances")
def listar(proyecto_id: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto_del_usuario(proyecto_id, user, db)
    avances = (
        db.query(Avance).filter(Avance.proyecto_id == p.id)
        .order_by(Avance.creado.desc()).limit(100).all()
    )
    return [_avance_out(a) for a in avances]


@router.post("/proyectos/{proyecto_id}/avances")
def crear(proyecto_id: int, req: AvanceCreate,
          user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto_del_usuario(proyecto_id, user, db)

    if not req.titulo.strip():
        raise HTTPException(400, "El avance necesita un titulo (ej: 'Cimentacion terminada')")

    fotos = [f for f in (req.fotos or []) if isinstance(f, str) and f.startswith("data:image")]
    if len(fotos) > MAX_FOTOS:
        raise HTTPException(400, f"Maximo {MAX_FOTOS} fotos por avance")
    for f in fotos:
        if len(f) > MAX_FOTO_BYTES * 1.4:  # base64 pesa ~1.37x
            raise HTTPException(400, "Cada foto debe pesar menos de 450KB — reduce el tamano")

    a = Avance(
        proyecto_id=p.id,
        titulo=req.titulo.strip()[:160],
        descripcion=(req.descripcion or "")[:2000],
        porcentaje=max(0, min(100, int(req.porcentaje or 0))),
        fotos_json=json.dumps(fotos),
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    logger.info(f"Avance creado en proyecto {p.id}: {a.titulo} ({a.porcentaje}%)")
    return _avance_out(a)


@router.delete("/proyectos/{proyecto_id}/avances/{avance_id}")
def eliminar(proyecto_id: int, avance_id: int,
             user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto_del_usuario(proyecto_id, user, db)
    a = db.query(Avance).filter(Avance.id == avance_id, Avance.proyecto_id == p.id).first()
    if not a:
        raise HTTPException(404, "Avance no encontrado")
    db.delete(a)
    db.commit()
    return {"ok": True}
