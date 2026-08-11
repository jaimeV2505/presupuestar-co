# -*- coding: utf-8 -*-
"""
Avances de obra atados al presupuesto.

El contratista marca el % de avance POR ACTIVIDAD del presupuesto.
El sistema calcula:
  - valor_ejecutado = suma(valor_actividad x pct/100)
  - porcentaje global = valor_ejecutado / costo_directo (avance ponderado por valor)

Asi el avance refleja el dinero real ejecutado, no una percepcion.
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto, Avance
from app.api.auth import usuario_actual

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_FOTOS = 3
MAX_FOTO_BYTES = 450_000


class ItemAvance(BaseModel):
    id: str
    pct: float = 0


class AvanceCreate(BaseModel):
    titulo: str
    descripcion: str = ""
    items: List[ItemAvance] = []   # % de avance por actividad del presupuesto
    fotos: List[str] = []


def _calcular_avance(proyecto: Proyecto, items_pct: List[ItemAvance]):
    """
    Cruza los % por actividad con los items del presupuesto.
    Retorna (porcentaje_ponderado, valor_ejecutado, detalle).
    """
    items_presupuesto = json.loads(proyecto.items_json or "[]")
    pct_map = {i.id: max(0.0, min(100.0, float(i.pct or 0))) for i in items_pct}

    total = 0.0
    ejecutado = 0.0
    detalle = []

    for it in items_presupuesto:
        valor_item = round((it.get("cantidad") or 0) * (it.get("precio_unitario") or 0))
        pct = pct_map.get(it.get("id"), 0.0)
        valor_ejec = round(valor_item * pct / 100)
        total += valor_item
        ejecutado += valor_ejec
        detalle.append({
            "id": it.get("id"),
            "descripcion": (it.get("descripcion") or "")[:120],
            "capitulo": it.get("capitulo", ""),
            "unidad": it.get("unidad", ""),
            "valor_item": valor_item,
            "pct": pct,
            "valor_ejec": valor_ejec,
        })

    porcentaje = round(ejecutado / total * 100, 1) if total > 0 else 0.0
    return porcentaje, round(ejecutado), detalle, round(total)


def _avance_out(a: Avance):
    return {
        "id": a.id,
        "titulo": a.titulo,
        "descripcion": a.descripcion,
        "porcentaje": a.porcentaje,
        "valor_ejecutado": a.valor_ejecutado or 0,
        "items": json.loads(a.items_json or "[]"),
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
    # Valor total del presupuesto (costo directo) para contexto
    items = json.loads(p.items_json or "[]")
    total = round(sum((i.get("cantidad") or 0) * (i.get("precio_unitario") or 0) for i in items))
    return {
        "valor_total_directo": total,
        "avances": [_avance_out(a) for a in avances],
    }


@router.post("/proyectos/{proyecto_id}/avances")
def crear(proyecto_id: int, req: AvanceCreate,
          user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto_del_usuario(proyecto_id, user, db)

    if not req.titulo.strip():
        raise HTTPException(400, "El avance necesita un titulo (ej: 'Corte semana 3')")

    items_presupuesto = json.loads(p.items_json or "[]")
    if not items_presupuesto:
        raise HTTPException(400, "El presupuesto no tiene actividades — el avance se calcula sobre ellas")

    fotos = [f for f in (req.fotos or []) if isinstance(f, str) and f.startswith("data:image")]
    if len(fotos) > MAX_FOTOS:
        raise HTTPException(400, f"Maximo {MAX_FOTOS} fotos por avance")
    for f in fotos:
        if len(f) > MAX_FOTO_BYTES * 1.4:
            raise HTTPException(400, "Cada foto debe pesar menos de 450KB")

    porcentaje, valor_ejec, detalle, total = _calcular_avance(p, req.items)

    a = Avance(
        proyecto_id=p.id,
        titulo=req.titulo.strip()[:160],
        descripcion=(req.descripcion or "")[:2000],
        porcentaje=int(round(porcentaje)),
        valor_ejecutado=valor_ejec,
        items_json=json.dumps(detalle, ensure_ascii=False),
        fotos_json=json.dumps(fotos),
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    logger.info(f"Avance proyecto {p.id}: {porcentaje}% = ${valor_ejec:,} de ${total:,}")
    out = _avance_out(a)
    out["valor_total_directo"] = total
    return out


@router.delete("/proyectos/{proyecto_id}/avances/{avance_id}")
def eliminar(proyecto_id: int, avance_id: int,
             user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto_del_usuario(proyecto_id, user, db)
    a = db.query(Avance).filter(Avance.id == avance_id, Avance.proyecto_id == p.id).first()
    if not a:
        raise HTTPException(404, "Avance no encontrado")
    from app.db import CuentaCobro
    con_cuenta = db.query(CuentaCobro).filter(CuentaCobro.avance_id == a.id).first()
    if con_cuenta:
        raise HTTPException(400, f"Este avance sustenta la cuenta de cobro {con_cuenta.numero} — no se puede eliminar")
    db.delete(a)
    db.commit()
    return {"ok": True}
