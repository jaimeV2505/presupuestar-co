# -*- coding: utf-8 -*-
"""
Gastos reales vs presupuesto — la metrica que salva al contratista pequeno.

Registra gastos de obra (materiales, nomina, transporte...) con foto del
recibo, y los compara contra el presupuesto:
  - Costo directo presupuestado vs gastado
  - Utilidad proyectada (la U del AIU) vs utilidad REAL (total contrato - gastos)
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto, Gasto
from app.api.auth import usuario_actual
from app.services.calculo_presupuesto import calcular_totales

logger = logging.getLogger(__name__)
router = APIRouter()

CATEGORIAS = ("materiales", "nomina", "transporte", "herramienta", "otros")
MAX_FOTO = 450_000


class GastoCreate(BaseModel):
    categoria: str = "materiales"
    descripcion: str
    valor: int
    foto: str = ""


def _proyecto(pid: int, user: Usuario, db: Session) -> Proyecto:
    p = db.query(Proyecto).filter(Proyecto.id == pid, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    return p


def _resumen(p: Proyecto, gastos, db: Session):
    items = json.loads(p.items_json or "[]")
    aiu = json.loads(p.aiu_json or "{}")
    t = calcular_totales(items, aiu)
    gastado = sum(g.valor for g in gastos)
    por_categoria = {}
    for g in gastos:
        por_categoria[g.categoria] = por_categoria.get(g.categoria, 0) + g.valor
    utilidad_real = t["total"] - gastado
    return {
        "presupuesto_directo": t["subtotal"],
        "total_contrato": t["total"],
        "gastado": gastado,
        "por_categoria": por_categoria,
        "utilidad_proyectada": t["utilidad_valor"],
        "utilidad_real": utilidad_real,
        "pct_ejecutado_gasto": round(gastado / t["subtotal"] * 100, 1) if t["subtotal"] else 0,
    }


@router.get("/proyectos/{pid}/gastos")
def listar(pid: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto(pid, user, db)
    gastos = (db.query(Gasto).filter(Gasto.proyecto_id == p.id)
              .order_by(Gasto.creado.desc()).limit(300).all())
    return {
        "resumen": _resumen(p, gastos, db),
        "gastos": [
            {
                "id": g.id, "categoria": g.categoria, "descripcion": g.descripcion,
                "valor": g.valor, "tiene_foto": bool(g.foto_b64),
                "foto": g.foto_b64 or "",
                "fecha": g.creado.strftime("%d/%m/%Y"),
            } for g in gastos
        ],
    }


@router.post("/proyectos/{pid}/gastos")
def crear(pid: int, req: GastoCreate,
          user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto(pid, user, db)
    if not req.descripcion.strip():
        raise HTTPException(400, "Describe el gasto (ej: '20 bultos de cemento')")
    if req.valor <= 0:
        raise HTTPException(400, "El valor debe ser mayor a 0")
    foto = req.foto or ""
    if foto and (not foto.startswith("data:image") or len(foto) > MAX_FOTO * 1.4):
        raise HTTPException(400, "La foto del recibo debe pesar menos de 450KB")

    g = Gasto(
        proyecto_id=p.id,
        categoria=req.categoria if req.categoria in CATEGORIAS else "otros",
        descripcion=req.descripcion.strip()[:300],
        valor=int(req.valor),
        foto_b64=foto,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    gastos = db.query(Gasto).filter(Gasto.proyecto_id == p.id).all()
    return {"ok": True, "id": g.id, "resumen": _resumen(p, gastos, db)}


@router.delete("/proyectos/{pid}/gastos/{gid}")
def eliminar(pid: int, gid: int,
             user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto(pid, user, db)
    g = db.query(Gasto).filter(Gasto.id == gid, Gasto.proyecto_id == p.id).first()
    if not g:
        raise HTTPException(404, "Gasto no encontrado")
    db.delete(g)
    db.commit()
    gastos = db.query(Gasto).filter(Gasto.proyecto_id == p.id).all()
    return {"ok": True, "resumen": _resumen(p, gastos, db)}
