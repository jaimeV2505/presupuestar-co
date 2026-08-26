# -*- coding: utf-8 -*-
"""
Pagos — Escalon 1 (manual):
El usuario reporta su pago (Nequi/Bancolombia) -> solicitud pendiente
-> el admin la aprueba desde el panel -> plan Pro por 30 dias.

Los datos de pago y los admins se configuran por variables de entorno:
  PAGO_NEQUI       = "300 123 4567"
  PAGO_BANCO       = "Ahorros Bancolombia 123-456789-01 a nombre de ..."
  ADMIN_EMAILS     = "jdvv25@gmail.com,otro@admin.com"
"""
import os
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, SolicitudPro
from app.api.auth import usuario_actual

logger = logging.getLogger(__name__)
router = APIRouter()

PRECIO_PRO = 79000
DIAS_PRO = 30


def _admins():
    return [e.strip().lower() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]


def admin_actual(user: Usuario = Depends(usuario_actual)) -> Usuario:
    if user.email.lower() not in _admins():
        raise HTTPException(403, "No autorizado")
    return user


# ── Publico para usuarios logueados ──────────────────────────────────────────

@router.get("/info")
def info_pago(user: Usuario = Depends(usuario_actual)):
    """Datos para pagar + estado del plan del usuario."""
    return {
        "precio_pro": PRECIO_PRO,
        "dias": DIAS_PRO,
        "nequi": os.environ.get("PAGO_NEQUI", "").strip(),
        "banco": os.environ.get("PAGO_BANCO", "").strip(),
        "plan": user.plan,
        "plan_vence": user.plan_vence.strftime("%d/%m/%Y") if user.plan_vence else None,
        "es_admin": user.email.lower() in _admins(),
    }


class SolicitudRequest(BaseModel):
    metodo: str = "nequi"
    referencia: str = ""


@router.post("/solicitud")
def crear_solicitud(req: SolicitudRequest, user: Usuario = Depends(usuario_actual),
                    db: Session = Depends(get_db)):
    if user.plan == "pro":
        raise HTTPException(400, "Ya tienes el plan Pro activo")
    pendiente = (
        db.query(SolicitudPro)
        .filter(SolicitudPro.user_id == user.id, SolicitudPro.estado == "pendiente")
        .first()
    )
    if pendiente:
        return {"ok": True, "estado": "pendiente",
                "mensaje": "Ya tienes una solicitud en verificacion — te activamos en menos de 24h"}
    s = SolicitudPro(
        user_id=user.id,
        metodo=req.metodo if req.metodo in ("nequi", "bancolombia", "otro") else "otro",
        referencia=(req.referencia or "").strip()[:120],
    )
    db.add(s)
    db.commit()
    logger.info(f"Solicitud Pro de {user.email} via {s.metodo} ref={s.referencia}")
    return {"ok": True, "estado": "pendiente",
            "mensaje": "Recibimos tu reporte de pago. Verificamos y activamos tu Pro en menos de 24 horas."}


@router.get("/mi-solicitud")
def mi_solicitud(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    s = (
        db.query(SolicitudPro)
        .filter(SolicitudPro.user_id == user.id)
        .order_by(SolicitudPro.creado.desc())
        .first()
    )
    if not s:
        return {"existe": False}
    return {"existe": True, "estado": s.estado, "metodo": s.metodo,
            "fecha": s.creado.strftime("%d/%m/%Y %H:%M")}


# ── Panel ADMIN ──────────────────────────────────────────────────────────────

@router.get("/admin/solicitudes")
def solicitudes(admin: Usuario = Depends(admin_actual), db: Session = Depends(get_db)):
    sols = (
        db.query(SolicitudPro, Usuario)
        .join(Usuario, Usuario.id == SolicitudPro.user_id)
        .order_by(SolicitudPro.creado.desc())
        .limit(200).all()
    )
    return [
        {
            "id": s.id, "estado": s.estado, "metodo": s.metodo,
            "referencia": s.referencia,
            "fecha": s.creado.strftime("%d/%m/%Y %H:%M"),
            "usuario": {"id": u.id, "nombre": u.nombre, "email": u.email,
                        "telefono": u.telefono, "empresa": u.empresa, "plan": u.plan},
        }
        for s, u in sols
    ]


class ResolverRequest(BaseModel):
    solicitud_id: int
    dias: int = DIAS_PRO


@router.post("/admin/aprobar")
def aprobar(req: ResolverRequest, admin: Usuario = Depends(admin_actual),
            db: Session = Depends(get_db)):
    s = db.query(SolicitudPro).filter(SolicitudPro.id == req.solicitud_id).first()
    if not s:
        raise HTTPException(404, "Solicitud no encontrada")
    if s.estado != "pendiente":
        raise HTTPException(400, f"Esta solicitud ya fue {s.estado} — no se puede volver a aprobar")
    user = db.query(Usuario).filter(Usuario.id == s.user_id).first()
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    ahora = datetime.now(timezone.utc)
    # Si ya es pro vigente, extender desde el vencimiento
    base = ahora
    if user.plan == "pro" and user.plan_vence:
        v = user.plan_vence if user.plan_vence.tzinfo else user.plan_vence.replace(tzinfo=timezone.utc)
        if v > ahora:
            base = v
    user.plan = "pro"
    user.plan_vence = base + timedelta(days=max(1, min(400, req.dias)))
    s.estado = "aprobada"
    s.resuelto = ahora
    db.commit()
    logger.info(f"ADMIN {admin.email} aprobo Pro para {user.email} hasta {user.plan_vence}")
    return {"ok": True, "usuario": user.email,
            "vence": user.plan_vence.strftime("%d/%m/%Y")}


@router.post("/admin/rechazar")
def rechazar(req: ResolverRequest, admin: Usuario = Depends(admin_actual),
             db: Session = Depends(get_db)):
    s = db.query(SolicitudPro).filter(SolicitudPro.id == req.solicitud_id).first()
    if not s:
        raise HTTPException(404, "Solicitud no encontrada")
    if s.estado != "pendiente":
        raise HTTPException(400, f"Esta solicitud ya fue {s.estado} — no se puede volver a resolver")
    s.estado = "rechazada"
    s.resuelto = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


class PlanManualRequest(BaseModel):
    email: str
    plan: str = "pro"
    dias: int = DIAS_PRO


@router.post("/admin/plan-manual")
def plan_manual(req: PlanManualRequest, admin: Usuario = Depends(admin_actual),
                db: Session = Depends(get_db)):
    """Activar/desactivar Pro directo por email (sin solicitud previa)."""
    user = db.query(Usuario).filter(Usuario.email == req.email.lower().strip()).first()
    if not user:
        raise HTTPException(404, "No existe un usuario con ese email")
    if req.plan == "pro":
        user.plan = "pro"
        user.plan_vence = datetime.now(timezone.utc) + timedelta(days=max(1, min(400, req.dias)))
    else:
        user.plan = "gratis"
        user.plan_vence = None
    db.commit()
    return {"ok": True, "usuario": user.email, "plan": user.plan,
            "vence": user.plan_vence.strftime("%d/%m/%Y") if user.plan_vence else None}
