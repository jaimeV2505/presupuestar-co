# -*- coding: utf-8 -*-
"""Proyectos: CRUD + items del presupuesto + limites por plan."""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto, EventoShare
from app.api.auth import usuario_actual
from app.services.calculo_presupuesto import calcular_totales, validar_items

logger = logging.getLogger(__name__)
router = APIRouter()

LIMITE_GRATIS = 3  # presupuestos por mes en plan gratis


def _mes_actual() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _verificar_limite(user: Usuario, db: Session):
    """Plan gratis: 3 presupuestos nuevos por mes."""
    if user.plan != "gratis":
        return
    mes = _mes_actual()
    if user.mes_actual != mes:
        user.mes_actual = mes
        user.presupuestos_mes = 0
        db.commit()
    if user.presupuestos_mes >= LIMITE_GRATIS:
        raise HTTPException(
            402,
            f"Plan gratis: limite de {LIMITE_GRATIS} presupuestos/mes alcanzado. "
            f"Pasa a Pro para presupuestos ilimitados."
        )


def _generar_numero(user_id: int, db: Session) -> str:
    """Numero de cotizacion secuencial por usuario: COT-2026-0001"""
    year = datetime.now(timezone.utc).year
    total = db.query(Proyecto).filter(Proyecto.user_id == user_id).count()
    return f"COT-{year}-{total + 1:04d}"


def _proyecto_out(p: Proyecto, incluir_items: bool = False) -> Dict:
    items = json.loads(p.items_json or "[]")
    aiu = json.loads(p.aiu_json or "{}")
    out = {
        "id": p.id,
        "numero": p.numero or f"COT-{p.id:04d}",
        "nombre": p.nombre,
        "cliente_nombre": p.cliente_nombre,
        "cliente_telefono": p.cliente_telefono,
        "direccion": p.direccion,
        "region": p.region,
        "estado": p.estado,
        "num_items": len(items),
        "aiu": aiu,
        "totales": calcular_totales(items, aiu),
        "share_token": p.share_token,
        "notas": p.notas,
        "creado": p.creado.isoformat() if p.creado else None,
        "actualizado": p.actualizado.isoformat() if p.actualizado else None,
    }
    if incluir_items:
        out["items"] = items
    return out


class ProyectoCreate(BaseModel):
    nombre: str
    cliente_nombre: str = ""
    cliente_telefono: str = ""
    direccion: str = ""
    region: str = "bogota"


class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    cliente_nombre: Optional[str] = None
    cliente_telefono: Optional[str] = None
    direccion: Optional[str] = None
    region: Optional[str] = None
    estado: Optional[str] = None
    notas: Optional[str] = None
    items: Optional[List[Dict]] = None
    aiu: Optional[Dict] = None


@router.get("")
def listar(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    proyectos = (
        db.query(Proyecto)
        .filter(Proyecto.user_id == user.id)
        .order_by(Proyecto.actualizado.desc())
        .limit(200).all()
    )
    return [_proyecto_out(p) for p in proyectos]


@router.post("")
def crear(req: ProyectoCreate, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    _verificar_limite(user, db)
    if not req.nombre.strip():
        raise HTTPException(400, "El proyecto necesita un nombre")
    p = Proyecto(
        user_id=user.id,
        numero=_generar_numero(user.id, db),
        nombre=req.nombre.strip()[:200],
        cliente_nombre=req.cliente_nombre.strip()[:160],
        cliente_telefono=req.cliente_telefono.strip()[:30],
        direccion=req.direccion.strip()[:250],
        region=req.region,
    )
    db.add(p)
    if user.plan == "gratis":
        user.presupuestos_mes += 1
    db.commit()
    db.refresh(p)
    logger.info(f"Proyecto creado: {p.id} por user {user.id}")
    return _proyecto_out(p, incluir_items=True)


@router.get("/{proyecto_id}")
def obtener(proyecto_id: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    return _proyecto_out(p, incluir_items=True)


@router.put("/{proyecto_id}")
def actualizar(proyecto_id: int, req: ProyectoUpdate, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")

    if req.nombre is not None: p.nombre = req.nombre.strip()[:200]
    if req.cliente_nombre is not None: p.cliente_nombre = req.cliente_nombre.strip()[:160]
    if req.cliente_telefono is not None: p.cliente_telefono = req.cliente_telefono.strip()[:30]
    if req.direccion is not None: p.direccion = req.direccion.strip()[:250]
    if req.region is not None: p.region = req.region
    if req.estado in ("borrador", "enviado", "visto", "aceptado", "rechazado"): p.estado = req.estado
    if req.notas is not None: p.notas = req.notas[:2000]

    if req.items is not None:
        items_validos = validar_items(req.items)
        p.items_json = json.dumps(items_validos, ensure_ascii=False)

    if req.aiu is not None:
        aiu_limpio = {
            "admin": max(0, min(50, float(req.aiu.get("admin", 15) or 0))),
            "imprevistos": max(0, min(30, float(req.aiu.get("imprevistos", 5) or 0))),
            "utilidad": max(0, min(50, float(req.aiu.get("utilidad", 8) or 0))),
            "aplicar": bool(req.aiu.get("aplicar", True)),
            "iva_sobre_utilidad": bool(req.aiu.get("iva_sobre_utilidad", True)),
        }
        p.aiu_json = json.dumps(aiu_limpio)

    db.commit()
    db.refresh(p)
    return _proyecto_out(p, incluir_items=True)


@router.delete("/{proyecto_id}")
def eliminar(proyecto_id: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    db.query(EventoShare).filter(EventoShare.proyecto_id == p.id).delete()
    db.delete(p)
    db.commit()
    return {"ok": True}


@router.post("/{proyecto_id}/duplicar")
def duplicar(proyecto_id: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    _verificar_limite(user, db)
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    nuevo = Proyecto(
        user_id=user.id,
        numero=_generar_numero(user.id, db),
        nombre=f"{p.nombre} (copia)",
        cliente_nombre=p.cliente_nombre,
        cliente_telefono=p.cliente_telefono,
        direccion=p.direccion,
        region=p.region,
        items_json=p.items_json,
        aiu_json=p.aiu_json,
        notas=p.notas,
    )
    db.add(nuevo)
    if user.plan == "gratis":
        user.presupuestos_mes += 1
    db.commit()
    db.refresh(nuevo)
    return _proyecto_out(nuevo, incluir_items=True)
