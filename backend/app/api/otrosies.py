# -*- coding: utf-8 -*-
"""
Otrosies (adicionales de obra) — lado del CONTRATISTA.

Flujo: en un proyecto FIRMADO aparecen trabajos extra -> el contratista propone
un otrosi con items adicionales -> el cliente lo aprueba con nueva firma desde
su enlace (endpoints en share.py) -> los items entran a avances y cuentas.
El contrato original JAMAS se toca: el valor crece por adicion firmada.
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto, Otrosi
from app.api.auth import usuario_actual
from app.services.calculo_presupuesto import validar_items
from app.services.otrosi_service import totales_otrosi

logger = logging.getLogger(__name__)
router = APIRouter()

ESTADOS_SIN_FIRMA = ("borrador", "enviado", "visto", "rechazado")


def _proyecto_de(pid: int, user: Usuario, db: Session) -> Proyecto:
    p = db.query(Proyecto).filter(Proyecto.id == pid, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    return p


def _serializar(o: Otrosi, aiu: dict) -> dict:
    items = json.loads(o.items_json or "[]")
    totales = json.loads(o.totales_json or "{}")
    if not totales:  # propuesto: vista previa con el AIU del contrato
        totales = totales_otrosi(items, aiu)
    return {
        "id": o.id, "numero": o.numero, "estado": o.estado, "motivo": o.motivo,
        "items": items, "totales": totales,
        "nombre_firma": o.nombre_firma, "fecha": o.creado.strftime("%d/%m/%Y"),
        "resuelto": o.resuelto.strftime("%d/%m/%Y %H:%M") if o.resuelto else None,
    }


class OtrosiRequest(BaseModel):
    proyecto_id: int
    motivo: str = ""
    items: List[Dict]


@router.get("/{proyecto_id}")
def listar(proyecto_id: int, user: Usuario = Depends(usuario_actual),
           db: Session = Depends(get_db)):
    p = _proyecto_de(proyecto_id, user, db)
    aiu = json.loads(p.aiu_json or "{}")
    lst = (db.query(Otrosi).filter(Otrosi.proyecto_id == p.id)
           .order_by(Otrosi.numero).all())
    return [_serializar(o, aiu) for o in lst]


@router.post("")
def crear(req: OtrosiRequest, user: Usuario = Depends(usuario_actual),
          db: Session = Depends(get_db)):
    p = _proyecto_de(req.proyecto_id, user, db)
    if p.estado in ESTADOS_SIN_FIRMA:
        raise HTTPException(400, "Los adicionales son para proyectos con contrato firmado — "
                                 "antes de la firma, edita el presupuesto directamente")
    if p.estado == "terminado":
        raise HTTPException(400, "La obra ya fue entregada — los adicionales van antes del acta")
    items = validar_items(req.items)
    if not items:
        raise HTTPException(400, "Agrega al menos un item adicional")
    ultimo = (db.query(Otrosi).filter(Otrosi.proyecto_id == p.id)
              .order_by(Otrosi.numero.desc()).first())
    o = Otrosi(
        proyecto_id=p.id,
        numero=(ultimo.numero + 1) if ultimo else 1,
        items_json=json.dumps(items, ensure_ascii=False),
        motivo=(req.motivo or "").strip()[:300],
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    logger.info(f"Otrosi N.{o.numero} propuesto en {p.numero} por {user.email}")
    return _serializar(o, json.loads(p.aiu_json or "{}"))


@router.put("/{otrosi_id}")
def actualizar(otrosi_id: int, req: OtrosiRequest,
               user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    o = db.query(Otrosi).filter(Otrosi.id == otrosi_id).first()
    if not o:
        raise HTTPException(404, "Otrosi no encontrado")
    p = _proyecto_de(o.proyecto_id, user, db)
    if o.estado != "propuesto":
        raise HTTPException(400, f"Este otrosi ya fue {o.estado} — es inmutable. Propon uno nuevo.")
    items = validar_items(req.items)
    if not items:
        raise HTTPException(400, "Agrega al menos un item")
    o.items_json = json.dumps(items, ensure_ascii=False)
    o.motivo = (req.motivo or "").strip()[:300]
    db.commit()
    return _serializar(o, json.loads(p.aiu_json or "{}"))


@router.delete("/{otrosi_id}")
def eliminar(otrosi_id: int, user: Usuario = Depends(usuario_actual),
             db: Session = Depends(get_db)):
    o = db.query(Otrosi).filter(Otrosi.id == otrosi_id).first()
    if not o:
        raise HTTPException(404, "Otrosi no encontrado")
    _proyecto_de(o.proyecto_id, user, db)
    if o.estado == "aprobado":
        raise HTTPException(400, "Un otrosi APROBADO es parte del contrato — no se puede eliminar")
    db.delete(o)
    db.commit()
    return {"ok": True}


@router.post("/{otrosi_id}/aprobar-interno")
def aprobar_interno(otrosi_id: int, user: Usuario = Depends(usuario_actual),
                    db: Session = Depends(get_db)):
    """OBRA PUBLICA: el adicional/mayores cantidades se aprueba internamente
    (no hay cliente final — el registro queda a nombre del contratista)."""
    o = db.query(Otrosi).filter(Otrosi.id == otrosi_id).first()
    if not o:
        raise HTTPException(404, "Adicional no encontrado")
    p = db.query(Proyecto).filter(Proyecto.id == o.proyecto_id,
                                  Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Adicional no encontrado")
    if (p.sector or "privado") != "publico":
        raise HTTPException(400, "En proyectos privados el adicional lo firma el cliente desde su enlace")
    if o.estado == "aprobado":
        raise HTTPException(400, "Este adicional ya esta aprobado")
    from app.services.otrosi_service import totales_otrosi
    import json as _json
    items = _json.loads(o.items_json or "[]")
    aiu = _json.loads(p.aiu_json or "{}")
    o.totales_json = _json.dumps(totales_otrosi(items, aiu), ensure_ascii=False)
    o.estado = "aprobado"
    o.nombre_firma = (user.nombre or "Contratista")[:120]
    o.resuelto = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "estado": "aprobado"}
