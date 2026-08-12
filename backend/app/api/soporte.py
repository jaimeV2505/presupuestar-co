# -*- coding: utf-8 -*-
"""
Soporte: el usuario reporta errores/dudas con evidencia (screenshots).

Doble garantia de que el reporte llega:
1. SIEMPRE se guarda en la BD (visible en el panel /admin)
2. Se envia por email a SOPORTE_EMAIL via Resend si RESEND_API_KEY esta configurada
   (resend.com — gratis 100 emails/dia, el 'from' onboarding@resend.dev
    funciona sin verificar dominio para enviar a tu propio correo)

Variables de entorno:
  SOPORTE_EMAIL   = jdvv25@gmail.com   (destino; ese es el default)
  RESEND_API_KEY  = re_xxxx            (opcional — sin ella, solo BD + admin)
"""
import os
import json
import logging
import httpx
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, TicketSoporte
from app.api.auth import usuario_actual
from app.api.pagos import admin_actual

logger = logging.getLogger(__name__)
router = APIRouter()

ESTADOS = ("pendiente_soporte", "pendiente_cliente", "finalizado")


def _estado_norm(e: str) -> str:
    return {"abierto": "pendiente_soporte", "resuelto": "finalizado"}.get(e, e if e in ESTADOS else "pendiente_soporte")


def _mensajes_de(t, db):
    from app.db import MensajeSoporte
    msgs = (db.query(MensajeSoporte).filter(MensajeSoporte.ticket_id == t.id)
            .order_by(MensajeSoporte.creado).all())
    out = [{"autor": m.autor, "texto": m.texto,
            "fecha": m.creado.strftime("%d/%m %H:%M")} for m in msgs]
    if t.respuesta and not any(m["autor"] == "soporte" for m in out):
        out.insert(0, {"autor": "soporte", "texto": t.respuesta,
                       "fecha": t.respondido.strftime("%d/%m %H:%M") if t.respondido else ""})
    return out

SOPORTE_EMAIL = os.environ.get("SOPORTE_EMAIL", "jdvv25@gmail.com").strip()
MAX_FOTOS = 2
MAX_FOTO_BYTES = 450_000


class TicketRequest(BaseModel):
    asunto: str
    descripcion: str = ""
    contexto: str = ""      # pagina actual, enviado por el frontend
    fotos: List[str] = []   # data URLs


def _enviar_email(user: Usuario, ticket: TicketSoporte, fotos: List[str]) -> bool:
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        return False
    try:
        html = f"""
        <h2>🛟 Nuevo ticket de soporte — PresupuestarCO</h2>
        <p><b>Ticket #{ticket.id}</b> · {ticket.creado.strftime('%d/%m/%Y %H:%M')} UTC</p>
        <hr>
        <p><b>Usuario:</b> {user.nombre} ({user.email})<br>
        <b>Empresa:</b> {user.empresa or '-'} · <b>WhatsApp:</b> {user.telefono or '-'}<br>
        <b>Plan:</b> {user.plan} · <b>Ciudad:</b> {user.ciudad}</p>
        <p><b>Contexto:</b> {ticket.contexto or '-'}</p>
        <hr>
        <h3>{ticket.asunto}</h3>
        <p style="white-space:pre-wrap">{ticket.descripcion or '(sin descripcion)'}</p>
        <p><i>{len(fotos)} evidencia(s) adjunta(s). Gestionar en /admin.</i></p>
        """
        attachments = []
        for i, f in enumerate(fotos):
            try:
                b64 = f.split(",", 1)[1]
                ext = "png" if "png" in f[:30] else "jpg"
                attachments.append({"filename": f"evidencia_{i+1}.{ext}", "content": b64})
            except Exception:
                pass

        payload = {
            "from": "PresupuestarCO Soporte <onboarding@resend.dev>",
            "to": [SOPORTE_EMAIL],
            "subject": f"[Soporte #{ticket.id}] {ticket.asunto[:80]} — {user.email}",
            "html": html,
        }
        if attachments:
            payload["attachments"] = attachments

        r = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload, timeout=15,
        )
        ok = r.status_code in (200, 201)
        if not ok:
            logger.warning(f"Resend fallo {r.status_code}: {r.text[:200]}")
        return ok
    except Exception as e:
        logger.warning(f"Email soporte no enviado: {e}")
        return False


@router.post("")
def crear_ticket(req: TicketRequest, user: Usuario = Depends(usuario_actual),
                 db: Session = Depends(get_db)):
    if not req.asunto.strip():
        raise HTTPException(400, "Cuentanos brevemente que paso (asunto)")

    fotos = [f for f in (req.fotos or []) if isinstance(f, str) and f.startswith("data:image")][:MAX_FOTOS]
    for f in fotos:
        if len(f) > MAX_FOTO_BYTES * 1.4:
            raise HTTPException(400, "Cada imagen debe pesar menos de 450KB")

    t = TicketSoporte(
        user_id=user.id,
        asunto=req.asunto.strip()[:200],
        descripcion=(req.descripcion or "")[:4000],
        contexto=(req.contexto or "")[:300],
        fotos_json=json.dumps(fotos),
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    t.email_enviado = _enviar_email(user, t, fotos)
    db.commit()

    logger.info(f"Ticket #{t.id} de {user.email}: {t.asunto} (email={'si' if t.email_enviado else 'no'})")
    return {
        "ok": True,
        "ticket": t.id,
        "mensaje": "Recibimos tu reporte. Te respondemos por WhatsApp o email lo antes posible.",
    }


@router.get("/mis-tickets")
def mis_tickets(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """El usuario ve sus propios tickets con estado y respuesta."""
    tickets = (
        db.query(TicketSoporte)
        .filter(TicketSoporte.user_id == user.id)
        .order_by(TicketSoporte.creado.desc())
        .limit(50).all()
    )
    return [
        {
            "id": t.id, "asunto": t.asunto, "descripcion": t.descripcion,
            "estado": _estado_norm(t.estado),
            "mensajes": _mensajes_de(t, db),
            "fecha": t.creado.strftime("%d/%m/%Y %H:%M"),
            "fecha_respuesta": t.respondido.strftime("%d/%m/%Y %H:%M") if t.respondido else None,
            "num_fotos": len(json.loads(t.fotos_json or "[]")),
        }
        for t in tickets
    ]


@router.get("/admin")
def listar_tickets(admin: Usuario = Depends(admin_actual), db: Session = Depends(get_db)):
    tickets = (
        db.query(TicketSoporte, Usuario)
        .join(Usuario, Usuario.id == TicketSoporte.user_id)
        .order_by(TicketSoporte.creado.desc())
        .limit(200).all()
    )
    return [
        {
            "id": t.id, "asunto": t.asunto, "descripcion": t.descripcion,
            "contexto": t.contexto, "estado": _estado_norm(t.estado), "mensajes": _mensajes_de(t, db),
            "respuesta": t.respuesta or "",
            "email_enviado": t.email_enviado,
            "fotos": json.loads(t.fotos_json or "[]"),
            "fecha": t.creado.strftime("%d/%m/%Y %H:%M"),
            "usuario": {"nombre": u.nombre, "email": u.email,
                        "telefono": u.telefono, "plan": u.plan},
        }
        for t, u in tickets
    ]


class ResolverTicket(BaseModel):
    ticket_id: int


class ResponderTicket(BaseModel):
    ticket_id: int
    respuesta: str
    resolver: bool = True


class ResponderRequest(BaseModel):
    ticket_id: int
    respuesta: str


@router.post("/admin/responder")
def responder_ticket(req: ResponderRequest, admin: Usuario = Depends(admin_actual),
                     db: Session = Depends(get_db)):
    from app.db import MensajeSoporte
    t = db.query(TicketSoporte).filter(TicketSoporte.id == req.ticket_id).first()
    if not t:
        raise HTTPException(404, "Ticket no encontrado")
    db.add(MensajeSoporte(ticket_id=t.id, autor="soporte", texto=req.respuesta.strip()[:2000]))
    t.estado = "pendiente_cliente"
    t.respondido = datetime.now(timezone.utc)
    db.commit()
    try:
        from app.api.notificaciones import notificar
        notificar(db, t.user_id, "soporte",
                  f"Soporte respondio tu ticket #{t.id}",
                  req.respuesta.strip()[:180])
    except Exception as e:
        logger.warning(f"notif soporte: {e}")
    return {"ok": True, "estado": t.estado}


class FinalizarRequest(BaseModel):
    ticket_id: int


@router.post("/admin/finalizar")
def finalizar_ticket(req: FinalizarRequest, admin: Usuario = Depends(admin_actual),
                     db: Session = Depends(get_db)):
    t = db.query(TicketSoporte).filter(TicketSoporte.id == req.ticket_id).first()
    if not t:
        raise HTTPException(404, "Ticket no encontrado")
    t.estado = "finalizado"
    db.commit()
    try:
        from app.api.notificaciones import notificar
        notificar(db, t.user_id, "soporte",
                  f"Tu ticket #{t.id} fue finalizado",
                  "Si el tema persiste, responde el ticket y se reabre solo.")
    except Exception:
        pass
    return {"ok": True}


@router.post("/admin/resolver")
def resolver(req: ResolverTicket, admin: Usuario = Depends(admin_actual),
             db: Session = Depends(get_db)):
    t = db.query(TicketSoporte).filter(TicketSoporte.id == req.ticket_id).first()
    if not t:
        raise HTTPException(404, "Ticket no encontrado")
    t.estado = "resuelto"
    db.commit()
    return {"ok": True}


class ResponderUsuarioRequest(BaseModel):
    texto: str


@router.post("/{ticket_id}/responder")
def responder_usuario(ticket_id: int, req: ResponderUsuarioRequest,
                      user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    from app.db import MensajeSoporte
    t = (db.query(TicketSoporte)
         .filter(TicketSoporte.id == ticket_id, TicketSoporte.user_id == user.id).first())
    if not t:
        raise HTTPException(404, "Ticket no encontrado")
    if not req.texto.strip():
        raise HTTPException(400, "Escribe tu mensaje")
    db.add(MensajeSoporte(ticket_id=t.id, autor="usuario", texto=req.texto.strip()[:2000]))
    t.estado = "pendiente_soporte"   # reabre si estaba finalizado
    db.commit()
    return {"ok": True, "estado": t.estado}
