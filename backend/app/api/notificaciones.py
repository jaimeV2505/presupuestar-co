# -*- coding: utf-8 -*-
"""Notificaciones in-app para el contratista + helper para crearlas."""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Notificacion
from app.api.auth import usuario_actual

logger = logging.getLogger(__name__)
router = APIRouter()

ICONOS = {"visto": "👁", "firmado": "✍️", "rechazado": "✕", "entrega": "🏁",
          "pendientes": "⚠️", "encuesta": "⭐", "soporte": "🛟", "comentario": "💬", "info": "🔔"}


def notificar(db: Session, user_id: int, tipo: str, titulo: str,
              cuerpo: str = "", proyecto_id: int = None):
    """Crear notificacion — usar desde cualquier modulo. Nunca rompe el flujo principal."""
    try:
        db.add(Notificacion(
            user_id=user_id, tipo=tipo, titulo=titulo[:200],
            cuerpo=(cuerpo or "")[:400], proyecto_id=proyecto_id,
        ))
        db.commit()
    except Exception as e:
        logger.warning(f"Notificacion no creada: {e}")
        db.rollback()


@router.get("")
def listar(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    notifs = (
        db.query(Notificacion)
        .filter(Notificacion.user_id == user.id)
        .order_by(Notificacion.creado.desc())
        .limit(30).all()
    )
    # Conteo real de no leidas — independiente del limite de 30 de la lista mostrada.
    no_leidas = (
        db.query(Notificacion)
        .filter(Notificacion.user_id == user.id, Notificacion.leida == False)  # noqa: E712
        .count()
    )
    return {
        "no_leidas": no_leidas,
        "notificaciones": [
            {
                "id": n.id, "tipo": n.tipo,
                "icono": ICONOS.get(n.tipo, "🔔"),
                "titulo": n.titulo, "cuerpo": n.cuerpo,
                "proyecto_id": n.proyecto_id, "leida": n.leida,
                "fecha": n.creado.strftime("%d/%m %H:%M"),
            } for n in notifs
        ],
    }


@router.post("/leer")
def marcar_leidas(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    db.query(Notificacion).filter(
        Notificacion.user_id == user.id, Notificacion.leida == False  # noqa: E712
    ).update({"leida": True})
    db.commit()
    return {"ok": True}
