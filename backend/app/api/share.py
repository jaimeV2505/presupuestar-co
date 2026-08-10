# -*- coding: utf-8 -*-
"""
El diferenciador: enlace publico del presupuesto para WhatsApp.

- POST /compartir: genera token unico -> URL publica
- GET /publico/{token}: datos del presupuesto (sin auth) + registra "visto"
- POST /publico/{token}/aceptar: el cliente acepta con un boton
- GET /eventos: el contratista ve cuando lo abrieron
"""
import json
import secrets
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto, EventoShare, Avance
from pydantic import BaseModel
from app.api.auth import usuario_actual
from app.services.calculo_presupuesto import calcular_totales

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/proyectos/{proyecto_id}/compartir")
def compartir(proyecto_id: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")

    items = json.loads(p.items_json or "[]")
    if not items:
        raise HTTPException(400, "El presupuesto esta vacio — agrega items antes de compartir")

    if not p.share_token:
        p.share_token = secrets.token_urlsafe(12)  # ~16 chars, no adivinable
        p.estado = "enviado"
        db.commit()

    aiu = json.loads(p.aiu_json or "{}")
    totales = calcular_totales(items, aiu)
    telefono = (p.cliente_telefono or "").replace(" ", "").replace("-", "").replace("+", "")

    # Mensaje de WhatsApp pre-armado
    mensaje = (
        f"Hola {p.cliente_nombre or ''}! Te comparto el presupuesto de "
        f"*{p.nombre}* por ${totales['total']:,.0f}. "
        f"Puedes verlo completo aqui:"
    ).strip()

    return {
        "share_token": p.share_token,
        "ruta_publica": f"/p/{p.share_token}",
        "mensaje_whatsapp": mensaje,
        "telefono_cliente": telefono,
        "whatsapp_url_base": (
            f"https://wa.me/{('57' + telefono) if telefono and not telefono.startswith('57') else telefono}"
            if telefono else "https://wa.me/"
        ),
    }


@router.get("/proyectos/{proyecto_id}/eventos")
def eventos(proyecto_id: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    evs = (
        db.query(EventoShare)
        .filter(EventoShare.proyecto_id == p.id)
        .order_by(EventoShare.creado.desc())
        .limit(100).all()
    )
    vistos = [e for e in evs if e.tipo == "visto"]
    aceptados = [e for e in evs if e.tipo == "aceptado"]
    return {
        "total_vistas": len(vistos),
        "primera_vista": vistos[-1].creado.isoformat() if vistos else None,
        "ultima_vista": vistos[0].creado.isoformat() if vistos else None,
        "aceptado": len(aceptados) > 0,
        "fecha_aceptado": aceptados[0].creado.isoformat() if aceptados else None,
        "eventos": [
            {"tipo": e.tipo, "fecha": e.creado.isoformat()}
            for e in evs[:20]
        ],
    }


# ── Endpoints PUBLICOS (sin auth) ────────────────────────────────────────────

@router.get("/publico/{token}")
def ver_publico(token: str, request: Request, db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Este presupuesto no existe o fue retirado")

    # Registrar vista + cambiar estado a "visto" automaticamente
    try:
        ua = (request.headers.get("user-agent") or "")[:300]
        db.add(EventoShare(proyecto_id=p.id, tipo="visto", user_agent=ua))
        if p.estado == "enviado":
            p.estado = "visto"
        db.commit()
    except Exception as e:
        logger.warning(f"No se registro vista: {e}")
        db.rollback()

    user = db.query(Usuario).filter(Usuario.id == p.user_id).first()
    items = json.loads(p.items_json or "[]")
    aiu = json.loads(p.aiu_json or "{}")
    totales = calcular_totales(items, aiu)

    # Agrupar items por capitulo para la vista
    capitulos = {}
    for it in items:
        cap = it.get("capitulo", "OTROS")
        if cap not in capitulos:
            capitulos[cap] = {"items": [], "subtotal": 0}
        precio_total = round(it["cantidad"] * it["precio_unitario"])
        capitulos[cap]["items"].append({
            "descripcion": it["descripcion"],
            "unidad": it["unidad"],
            "cantidad": it["cantidad"],
            "precio_unitario": it["precio_unitario"],
            "precio_total": precio_total,
        })
        capitulos[cap]["subtotal"] += precio_total

    ya_aceptado = (
        db.query(EventoShare)
        .filter(EventoShare.proyecto_id == p.id, EventoShare.tipo == "aceptado")
        .first() is not None
    )
    ya_rechazado = (
        db.query(EventoShare)
        .filter(EventoShare.proyecto_id == p.id, EventoShare.tipo == "rechazado")
        .first() is not None
    ) and not ya_aceptado

    firma_ev = (
        db.query(EventoShare)
        .filter(EventoShare.proyecto_id == p.id, EventoShare.tipo == "aceptado")
        .first()
    )

    return {
        "proyecto": p.nombre,
        "numero": p.numero or "",
        "firma": {
            "nombre": firma_ev.nombre_firma,
            "fecha": firma_ev.creado.strftime("%d/%m/%Y %H:%M"),
        } if firma_ev and firma_ev.nombre_firma else None,
        "cliente": p.cliente_nombre,
        "direccion": p.direccion,
        "estado": "aceptado" if ya_aceptado else ("rechazado" if ya_rechazado else p.estado),
        "contratista": {
            "nombre": user.nombre if user else "",
            "empresa": user.empresa if user else "",
            "telefono": user.telefono if user else "",
            "logo_b64": user.logo_b64 if user else "",
            "condiciones": (getattr(user, "condiciones", "") or "") if user else "",
        },
        "capitulos": capitulos,
        "totales": totales,
        "notas": p.notas,
        "fecha": p.actualizado.strftime("%d/%m/%Y") if p.actualizado else "",
    }


class FirmaRequest(BaseModel):
    nombre: str
    documento: str = ""


@router.post("/publico/{token}/aceptar")
def aceptar_publico(token: str, firma: FirmaRequest, request: Request, db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Este presupuesto no existe")

    nombre = (firma.nombre or "").strip()
    if len(nombre) < 5:
        raise HTTPException(400, "Escribe tu nombre completo para aceptar")

    ya = (
        db.query(EventoShare)
        .filter(EventoShare.proyecto_id == p.id, EventoShare.tipo == "aceptado")
        .first()
    )
    if ya:
        return {"ok": True, "mensaje": "Este presupuesto ya fue aceptado",
                "firmado_por": ya.nombre_firma, "fecha": ya.creado.isoformat()}

    ua = (request.headers.get("user-agent") or "")[:300]
    ev = EventoShare(
        proyecto_id=p.id, tipo="aceptado", user_agent=ua,
        nombre_firma=nombre[:160],
        documento_firma=(firma.documento or "").strip()[:30],
    )
    db.add(ev)
    p.estado = "aceptado"
    db.commit()
    db.refresh(ev)
    logger.info(f"Presupuesto {p.id} ACEPTADO y firmado por {nombre}")
    return {
        "ok": True,
        "mensaje": "Presupuesto aceptado y firmado. El contratista sera notificado.",
        "firmado_por": nombre,
        "fecha": ev.creado.isoformat(),
    }


@router.get("/publico/{token}/avances")
def avances_publico(token: str, db: Session = Depends(get_db)):
    """El cliente ve los avances de su obra con el mismo enlace."""
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Enlace no valido")
    avances = (
        db.query(Avance)
        .filter(Avance.proyecto_id == p.id)
        .order_by(Avance.creado.desc())
        .limit(50).all()
    )
    import json as _json
    return {
        "proyecto": p.nombre,
        "numero": p.numero,
        "porcentaje_actual": max((a.porcentaje for a in avances), default=0),
        "avances": [
            {
                "id": a.id, "titulo": a.titulo, "descripcion": a.descripcion,
                "porcentaje": a.porcentaje,
                "fotos": _json.loads(a.fotos_json or "[]"),
                "fecha": a.creado.strftime("%d/%m/%Y %H:%M"),
            } for a in avances
        ],
    }


@router.post("/publico/{token}/rechazar")
def rechazar_publico(token: str, request: Request, db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Este presupuesto no existe")

    ya_aceptado = (
        db.query(EventoShare)
        .filter(EventoShare.proyecto_id == p.id, EventoShare.tipo == "aceptado")
        .first()
    )
    if ya_aceptado:
        return {"ok": False, "mensaje": "Este presupuesto ya fue aceptado"}

    ua = (request.headers.get("user-agent") or "")[:300]
    db.add(EventoShare(proyecto_id=p.id, tipo="rechazado", user_agent=ua))
    p.estado = "rechazado"
    db.commit()
    logger.info(f"Presupuesto {p.id} rechazado por el cliente")
    return {"ok": True, "mensaje": "Gracias por tu respuesta. El contratista sera notificado."}
