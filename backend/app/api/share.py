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
from app.db import get_db, Usuario, Proyecto, EventoShare, Avance, Encuesta
from app.api.notificaciones import notificar
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
        "ruta_preview": f"/api/s/{p.share_token}",   # URL con OG de la obra — usar en WhatsApp/copiar
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
    if token == "demo":
        return _demo_payload()
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Este presupuesto no existe o fue retirado")

    # PROYECTO TERMINADO: el acceso al presupuesto se cierra — solo encuesta
    if p.estado == "terminado":
        user_t = db.query(Usuario).filter(Usuario.id == p.user_id).first()
        enc = db.query(Encuesta).filter(Encuesta.proyecto_id == p.id).first()
        return {
            "terminado": True,
            "proyecto": p.nombre,
            "numero": p.numero or "",
            "contratista": {
                "nombre": user_t.nombre if user_t else "",
                "empresa": user_t.empresa if user_t else "",
                "logo_b64": user_t.logo_b64 if user_t else "",
            },
            "encuesta_respondida": enc is not None,
        }

    # Registrar vista + cambiar estado a "visto" automaticamente
    try:
        ua = (request.headers.get("user-agent") or "")[:300]
        primera_vista = not db.query(EventoShare).filter(
            EventoShare.proyecto_id == p.id, EventoShare.tipo == "visto").first()
        db.add(EventoShare(proyecto_id=p.id, tipo="visto", user_agent=ua))
        if p.estado == "enviado":
            p.estado = "visto"
        db.commit()
        if primera_vista:
            notificar(db, p.user_id, "visto",
                      f"👁 Tu cliente abrio {p.numero}",
                      f"'{p.nombre}' fue visto por primera vez. Buen momento para llamar.",
                      p.id)
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
        "estado": p.estado if p.estado in ("entrega_solicitada", "terminado") else ("aceptado" if ya_aceptado else ("rechazado" if ya_rechazado else p.estado)),
        "contratista": {
            "nombre": user.nombre if user else "",
            "empresa": user.empresa if user else "",
            "telefono": user.telefono if user else "",
            "logo_b64": user.logo_b64 if user else "",
            "condiciones": (getattr(user, "condiciones", "") or "") if user else "",
            "reputacion": _badge_reputacion(p.user_id, db),
        },
        "capitulos": capitulos,
        "totales": totales,
        "otrosies": _otrosies_publicos(p, db),
        "notas": p.notas,
        "fecha": p.actualizado.strftime("%d/%m/%Y") if p.actualizado else "",
    }


class FirmaRequest(BaseModel):
    nombre: str
    documento: str = ""
    firma_imagen: str = ""  # base64 PNG de firma dibujada o subida (opcional)


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
    img = firma.firma_imagen or ""
    if img and (not img.startswith("data:image") or len(img) > 600_000):
        img = ""
    ev = EventoShare(
        proyecto_id=p.id, tipo="aceptado", user_agent=ua,
        nombre_firma=nombre[:160],
        documento_firma=(firma.documento or "").strip()[:30],
        firma_imagen=img,
    )
    db.add(ev)
    p.estado = "aceptado"
    db.commit()
    notificar(db, p.user_id, "firmado",
              f"¡Firmaron el contrato de {p.numero}!",
              f"{nombre} acepto '{p.nombre}'. Ya puedes descargar el contrato firmado.",
              p.id)
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
    if token == "demo":
        return _demo_avances()
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
    items_p = _json.loads(p.items_json or "[]")
    total_directo = round(sum((i.get("cantidad") or 0) * (i.get("precio_unitario") or 0) for i in items_p))
    ultimo = avances[0] if avances else None

    # Cuentas de cobro visibles para el cliente
    from app.db import CuentaCobro, Abono

    def _abonado_de(c, db):
        return sum(a.monto for a in db.query(Abono).filter(Abono.cuenta_id == c.id).all())

    ccs = (db.query(CuentaCobro).filter(CuentaCobro.proyecto_id == p.id)
           .order_by(CuentaCobro.creado.desc()).all())
    cuentas = [
        {
            "id": c.id, "numero": c.numero, "neto": c.neto,
            "estado": c.estado, "tipo": getattr(c, "tipo", "corte") or "corte",
            "retencion": getattr(c, "retencion", 0) or 0,
            "abonado": _abonado_de(c, db),
            "fecha": c.creado.strftime("%d/%m/%Y"),
            "fecha_pago": c.pagado.strftime("%d/%m/%Y") if c.pagado else None,
        } for c in ccs
    ]
    pagado_total = sum(c.neto for c in ccs if c.estado == "pagada")
    pendiente_total = sum(c.neto for c in ccs if c.estado == "enviada")

    return {
        "cuentas": cuentas,
        "pagado_total": pagado_total,
        "pendiente_total": pendiente_total,
        "proyecto": p.nombre,
        "numero": p.numero,
        "porcentaje_actual": ultimo.porcentaje if ultimo else 0,
        "valor_ejecutado_actual": (ultimo.valor_ejecutado or 0) if ultimo else 0,
        "valor_total_directo": total_directo,
        "avances": [
            {
                "id": a.id, "titulo": a.titulo, "descripcion": a.descripcion,
                "porcentaje": a.porcentaje,
                "valor_ejecutado": a.valor_ejecutado or 0,
                "items": _json.loads(a.items_json or "[]"),
                "fotos": _json.loads(a.fotos_json or "[]"),
                "fecha": a.creado.strftime("%d/%m/%Y %H:%M"),
                **_interacciones_de(a.id, db),
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
    notificar(db, p.user_id, "rechazado",
              f"Rechazaron {p.numero}",
              f"El cliente no acepto '{p.nombre}'. Considera ajustar y reenviar.",
              p.id)
    logger.info(f"Presupuesto {p.id} rechazado por el cliente")
    return {"ok": True, "mensaje": "Gracias por tu respuesta. El contratista sera notificado."}


# ── CONTRATO DE EJECUCION DE OBRA ────────────────────────────────────────────
from fastapi.responses import StreamingResponse
from app.services.contrato_service import generar_contrato


def _demo_contrato():
    """Contrato de muestra para /p/demo — el visitante descarga un PDF real."""
    from types import SimpleNamespace
    from datetime import datetime
    items = [
        {"capitulo": "PRELIMINARES", "descripcion": "Localizacion y replanteo", "unidad": "m2", "cantidad": 96, "precio_unitario": 4200},
        {"capitulo": "ESTRUCTURA", "descripcion": "Columna en concreto 3000 PSI 30x30", "unidad": "m3", "cantidad": 6.5, "precio_unitario": 894601},
        {"capitulo": "MAMPOSTERIA", "descripcion": "Muro en bloque de concreto e=15cm", "unidad": "m2", "cantidad": 210, "precio_unitario": 68450},
        {"capitulo": "CUBIERTA", "descripcion": "Cubierta en teja sandwich cal. 26", "unidad": "m2", "cantidad": 110, "precio_unitario": 145900},
        {"capitulo": "ACABADOS", "descripcion": "Panete liso muros interiores", "unidad": "m2", "cantidad": 380, "precio_unitario": 22800},
    ]
    aiu = {"admin": 15, "imprevistos": 5, "utilidad": 8, "aplicar": True, "iva_sobre_utilidad": True}
    totales = calcular_totales(items, aiu)
    p = SimpleNamespace(
        id=0, nombre="Construccion local comercial — Covenas, Sucre",
        numero="COT-2026-0001", cliente_nombre="Carlos Martinez",
        cliente_telefono="", direccion="Covenas, Sucre", region="monteria",
        contrato_json='{"plazo_dias": 45, "anticipo_pct": 50, "fecha_inicio": "", "lugar": "Covenas, Sucre"}',
        share_token="demo",
        creado=datetime(2026, 7, 20, 9, 0),
        actualizado=datetime(2026, 7, 22, 10, 14),
        estado="aceptado",
    )
    user = SimpleNamespace(
        nombre="Jaime Vergara", empresa="Construcciones JV",
        documento="1.098.765.432", telefono="300 123 4567",
        email="demo@presupuestar.co", ciudad="monteria",
        logo_b64="", firma_b64="", pago_info="Nequi 300 123 4567",
    )
    firma = {"nombre": "Carlos Martinez", "documento": "9.876.543",
             "fecha": "22/07/2026 10:14", "imagen": ""}
    return p, user, generar_contrato(p, user, items, totales, firma)


def _contrato_de_token(token: str, db: Session):
    if token == "demo":
        return _demo_contrato()
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Enlace no valido")
    user = db.query(Usuario).filter(Usuario.id == p.user_id).first()
    items = json.loads(p.items_json or "[]")
    aiu = json.loads(p.aiu_json or "{}")
    totales = calcular_totales(items, aiu)
    firma_ev = (
        db.query(EventoShare)
        .filter(EventoShare.proyecto_id == p.id, EventoShare.tipo == "aceptado")
        .first()
    )
    firma = None
    if firma_ev and firma_ev.nombre_firma:
        firma = {
            "nombre": firma_ev.nombre_firma,
            "documento": firma_ev.documento_firma or "",
            "fecha": firma_ev.creado.strftime("%d/%m/%Y %H:%M"),
            "imagen": firma_ev.firma_imagen or "",
        }
    return p, user, generar_contrato(p, user, items, totales, firma)


@router.get("/publico/{token}/contrato")
def ver_contrato(token: str, db: Session = Depends(get_db)):
    """El contrato completo — se muestra en el modal antes de firmar."""
    _, _, contrato = _contrato_de_token(token, db)
    return contrato


@router.get("/publico/{token}/contrato.pdf")
def contrato_pdf(token: str, db: Session = Depends(get_db)):
    """PDF del contrato — descargable por cliente y contratista."""
    p, user, c = _contrato_de_token(token, db)
    try:
        import io
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                        Paragraph, Spacer)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=1.8*cm,
                                bottomMargin=1.8*cm, leftMargin=2*cm, rightMargin=2*cm)
        st = getSampleStyleSheet()
        titulo = ParagraphStyle("t", parent=st["Title"], fontSize=13, spaceAfter=14)
        clau_t = ParagraphStyle("ct", parent=st["Normal"], fontSize=9.5,
                                fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=3)
        cuerpo = ParagraphStyle("cu", parent=st["Normal"], fontSize=9,
                                leading=13, alignment=4)  # justificado
        story = [Paragraph(f"{c['titulo']} — {c['numero']}", titulo),
                 Paragraph(c["encabezado"], cuerpo), Spacer(1, 6)]

        for cl in c["clausulas"]:
            story.append(Paragraph(cl["titulo"] + ".", clau_t))
            story.append(Paragraph(cl["texto"], cuerpo))
            if cl.get("incluye_tabla"):
                data = [["ITEM", "DESCRIPCION", "UND", "CANT", "V. UNITARIO", "SUBTOTAL"]]
                for r in c["tabla"]:
                    data.append([
                        str(r["item"]),
                        Paragraph(r["descripcion"][:120], ParagraphStyle("d", parent=st["Normal"], fontSize=7.5)),
                        r["unidad"], f"{r['cantidad']:g}",
                        f"${r['v_unitario']:,}".replace(",", "."),
                        f"${r['subtotal']:,}".replace(",", "."),
                    ])
                data.append(["", "", "", "", "TOTAL A PAGAR",
                             f"${c['total']:,}".replace(",", ".")])
                t = Table(data, colWidths=[1*cm, 8*cm, 1.2*cm, 1.4*cm, 2.4*cm, 2.6*cm],
                          repeatRows=1)
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1C3A5E")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
                    ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EFF6FF")),
                ]))
                story.append(Spacer(1, 5))
                story.append(t)

        # Firmas
        story.append(Spacer(1, 22))
        f = c["firmas"]
        import base64 as _b64
        from reportlab.platypus import Image as RLImage

        def _img_de(b64):
            try:
                if not b64:
                    return None
                raw = _b64.b64decode(b64.split(",", 1)[1])
                return RLImage(io.BytesIO(raw), width=4.5*cm, height=1.8*cm, kind="proportional")
            except Exception:
                return None

        img_firma = _img_de(c.get("firma_imagen") or "")
        img_firma_contratista = _img_de(getattr(user, "firma_b64", "") or "")
        firmas_data = [[
            Paragraph(f"<b>EL CONTRATANTE</b><br/>{f['contratante']['nombre'] or '________________'}"
                      f"<br/>Doc: {f['contratante']['documento'] or '________________'}"
                      f"<br/><font size=7 color='#64748B'>{f['contratante']['estado']}"
                      f"{(' · ' + f['contratante']['fecha']) if f['contratante']['fecha'] else ''}</font>", cuerpo),
            Paragraph(f"<b>EL CONTRATISTA</b><br/>{f['contratista']['nombre']}"
                      f"<br/>Doc: {f['contratista']['documento']}"
                      f"<br/><font size=7 color='#64748B'>{f['contratista']['estado']}"
                      f" · {f['contratista']['fecha']}</font>", cuerpo),
        ]]
        if img_firma:
            firmas_data[0][0] = [img_firma, firmas_data[0][0]]
        if img_firma_contratista:
            firmas_data[0][1] = [img_firma_contratista, firmas_data[0][1]]
        tf = Table(firmas_data, colWidths=[8.3*cm, 8.3*cm])
        tf.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (0, 0), 0.7, colors.black),
            ("LINEABOVE", (1, 0), (1, 0), 0.7, colors.black),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(tf)

        doc.build(story)
        buf.seek(0)
        return StreamingResponse(
            buf, media_type="application/pdf",
            headers={"Content-Disposition":
                     f'attachment; filename="contrato_{p.numero or p.id}.pdf"'})
    except Exception as e:
        logger.error(f"PDF contrato: {e}", exc_info=True)
        raise HTTPException(500, "Error generando el contrato PDF")


# ── ENCUESTA DE SATISFACCION (al terminar la obra) ──────────────────────────
class EncuestaRequest(BaseModel):
    estrellas: int
    recomendaria: bool = True
    comentario: str = ""


@router.post("/publico/{token}/encuesta")
def responder_encuesta(token: str, req: EncuestaRequest, db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Enlace no valido")
    if p.estado != "terminado":
        raise HTTPException(400, "La encuesta se habilita cuando la obra termina")

    ya = db.query(Encuesta).filter(Encuesta.proyecto_id == p.id).first()
    if ya:
        return {"ok": True, "mensaje": "Ya habias enviado tu calificacion. Gracias!"}

    estrellas = max(1, min(5, int(req.estrellas or 0)))
    e = Encuesta(
        proyecto_id=p.id,
        estrellas=estrellas,
        recomendaria=bool(req.recomendaria),
        comentario=(req.comentario or "")[:1500],
    )
    db.add(e)
    db.commit()
    notificar(db, p.user_id, "encuesta",
              f"⭐ Nueva calificacion: {estrellas}/5",
              f"Tu cliente califico '{p.nombre}'{' y te recomendaria' if e.recomendaria else ''}. Publicala en tu perfil desde Perfil > Reputacion.",
              p.id)
    logger.info(f"Encuesta proyecto {p.id}: {estrellas} estrellas")
    return {"ok": True, "mensaje": "Gracias por tu calificacion!"}


@router.get("/proyectos/{proyecto_id}/encuesta")
def ver_encuesta(proyecto_id: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """El contratista ve la calificacion que dejo su cliente."""
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    e = db.query(Encuesta).filter(Encuesta.proyecto_id == p.id).first()
    if not e:
        return {"respondida": False}
    return {
        "respondida": True,
        "estrellas": e.estrellas,
        "recomendaria": e.recomendaria,
        "comentario": e.comentario,
        "fecha": e.creado.strftime("%d/%m/%Y"),
    }


# ── PRESUPUESTO DE DEMOSTRACION (/p/demo) ────────────────────────────────────
DEMO_ITEMS = [
    {"id": "d1", "capitulo": "CIMENTACION", "descripcion": "Excavaciones de zapata de 2x2x1.20 de profundidad", "unidad": "un", "cantidad": 5, "precio_unitario": 210000},
    {"id": "d2", "capitulo": "CIMENTACION", "descripcion": "Excavaciones de zapatas laterales de 1.80x1.20x1.20", "unidad": "un", "cantidad": 10, "precio_unitario": 210000},
    {"id": "d3", "capitulo": "CIMENTACION", "descripcion": "Suministro e instalacion de mangles de 3.5m para zapata", "unidad": "un", "cantidad": 225, "precio_unitario": 55000},
    {"id": "d4", "capitulo": "ESTRUCTURA", "descripcion": "Fabricacion de columna zapata y pedestal a 3m, concreto 4000 PSI", "unidad": "un", "cantidad": 15, "precio_unitario": 3300000},
    {"id": "d5", "capitulo": "ESTRUCTURA", "descripcion": "Viga de cimiento 35x40 en varilla 5/8, concreto 4000 PSI", "unidad": "ml", "cantidad": 120, "precio_unitario": 160000},
    {"id": "d6", "capitulo": "ESTRUCTURA", "descripcion": "Placa en concreto rigido aligerada con icopor e=40cm, vigas 5/8", "unidad": "m2", "cantidad": 360, "precio_unitario": 360000},
    {"id": "d7", "capitulo": "MAMPOSTERIA", "descripcion": "Mamposteria 0/15 vibrado en muros perimetrales", "unidad": "m2", "cantidad": 230, "precio_unitario": 115000},
    {"id": "d8", "capitulo": "MAMPOSTERIA", "descripcion": "Mechones de confinamiento entre columnas, luces de 2.5m", "unidad": "un", "cantidad": 8, "precio_unitario": 450000},
    {"id": "d9", "capitulo": "MAMPOSTERIA", "descripcion": "Viga de amarre para muros perimetrales 3/8 y 1/4", "unidad": "ml", "cantidad": 80, "precio_unitario": 70000},
    {"id": "d10", "capitulo": "ACABADOS", "descripcion": "Plantilla en concreto rigido con malla 1/4 15x15, 4000 PSI", "unidad": "m2", "cantidad": 340, "precio_unitario": 80000},
]
DEMO_AIU = {"aplicar": False}


def _demo_payload():
    totales = calcular_totales(DEMO_ITEMS, DEMO_AIU)
    capitulos = {}
    for it in DEMO_ITEMS:
        cap = it["capitulo"]
        if cap not in capitulos:
            capitulos[cap] = {"items": [], "subtotal": 0}
        pt = round(it["cantidad"] * it["precio_unitario"])
        capitulos[cap]["items"].append({
            "descripcion": it["descripcion"], "unidad": it["unidad"],
            "cantidad": it["cantidad"], "precio_unitario": it["precio_unitario"],
            "precio_total": pt,
        })
        capitulos[cap]["subtotal"] += pt
    return {
        "demo": True,
        "proyecto": "Construccion local comercial — Covenas, Sucre",
        "numero": "COT-2026-0001",
        "firma": {"nombre": "Orledys Romero F. (demo)", "fecha": "12/06/2026 10:15"},
        "cliente": "Orledys Romero Fuentes",
        "direccion": "Municipio de Covenas, Sucre",
        "estado": "aceptado",
        "contratista": {
            "nombre": "Luis Alfredo Beltran (demo)",
            "empresa": "Construcciones LB",
            "telefono": "",
            "logo_b64": "",
            "condiciones": "Validez de la oferta: 15 dias calendario.\nForma de pago: 60% anticipo, 40% contra acta de entrega.\nNo incluye tramites ante curaduria ni disenos estructurales.",
        },
        "capitulos": capitulos,
        "totales": totales,
        "notas": "Este es un presupuesto de DEMOSTRACION para que veas exactamente lo que vera tu cliente.",
        "fecha": "12/06/2026",
    }


def _demo_avances():
    return {
        "cuentas": [
            {"id": 0, "numero": "CC-2026-0002", "neto": 41339250, "estado": "enviada",
             "fecha": "05/08/2026", "fecha_pago": None},
            {"id": 0, "numero": "CC-2026-0001", "neto": 16762500, "estado": "pagada",
             "fecha": "22/07/2026", "fecha_pago": "24/07/2026"},
        ],
        "pagado_total": 16762500,
        "pendiente_total": 41339250,
        "proyecto": "Construccion local comercial — Covenas, Sucre",
        "numero": "COT-2026-0001",
        "porcentaje_actual": 42,
        "valor_ejecutado_actual": 116203500,
        "valor_total_directo": 276675000,
        "avances": [
            {
                "id": 2, "titulo": "Corte 2 — Estructura en marcha",
                "descripcion": "Columnas fundidas y placa al 35%. Vamos dentro del cronograma.",
                "porcentaje": 42, "valor_ejecutado": 116203500,
                "items": [
                    {"descripcion": "Excavaciones de zapata 2x2x1.20", "pct": 100, "valor_ejec": 1050000},
                    {"descripcion": "Columnas zapata y pedestal 4000 PSI", "pct": 80, "valor_ejec": 39600000},
                    {"descripcion": "Placa aligerada e=40cm", "pct": 35, "valor_ejec": 45360000},
                ],
                "fotos": [], "fecha": "05/08/2026 16:40",
            },
            {
                "id": 1, "titulo": "Corte 1 — Cimentacion completa",
                "descripcion": "Zapatas excavadas y fundidas, mangles instalados.",
                "porcentaje": 12, "valor_ejecutado": 33525000,
                "items": [
                    {"descripcion": "Excavaciones de zapata 2x2x1.20", "pct": 100, "valor_ejec": 1050000},
                    {"descripcion": "Mangles de 3.5m para zapata", "pct": 100, "valor_ejec": 12375000},
                ],
                "fotos": [], "fecha": "22/07/2026 11:20",
            },
        ],
    }


def _badge_reputacion(user_id: int, db: Session):
    try:
        encs = (db.query(Encuesta).join(Proyecto, Proyecto.id == Encuesta.proyecto_id)
                .filter(Proyecto.user_id == user_id).all())
        if not encs:
            return None
        terminadas = db.query(Proyecto).filter(
            Proyecto.user_id == user_id, Proyecto.estado == "terminado").count()
        u = db.query(Usuario).filter(Usuario.id == user_id).first()
        return {
            "promedio": round(sum(e.estrellas for e in encs) / len(encs), 1),
            "obras": terminadas,
            "slug": u.slug or "",
        }
    except Exception:
        return None


# ── ACTA DE ENTREGA BILATERAL ────────────────────────────────────────────────
class ConfirmarEntregaRequest(BaseModel):
    nombre: str
    documento: str = ""
    firma_imagen: str = ""


class PendientesRequest(BaseModel):
    detalle: str


@router.post("/publico/{token}/confirmar-entrega")
def confirmar_entrega(token: str, req: ConfirmarEntregaRequest, request: Request,
                      db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Enlace no valido")
    if p.estado != "entrega_solicitada":
        raise HTTPException(400, "La entrega no esta pendiente de confirmacion")
    nombre = (req.nombre or "").strip()
    if len(nombre) < 5:
        raise HTTPException(400, "Escribe tu nombre completo para confirmar")

    img = req.firma_imagen or ""
    if img and (not img.startswith("data:image") or len(img) > 600_000):
        img = ""
    ua = (request.headers.get("user-agent") or "")[:300]
    db.add(EventoShare(proyecto_id=p.id, tipo="entrega_confirmada", user_agent=ua,
                       nombre_firma=nombre[:160],
                       documento_firma=(req.documento or "").strip()[:30],
                       firma_imagen=img))
    p.estado = "terminado"
    db.commit()
    notificar(db, p.user_id, "entrega",
              f"🏁 ¡Entrega confirmada en {p.numero}!",
              f"{nombre} recibio la obra a satisfaccion. El Acta de Entrega esta lista para descargar.",
              p.id)
    return {"ok": True, "mensaje": "Entrega confirmada. Gracias!"}


@router.post("/publico/{token}/reportar-pendientes")
def reportar_pendientes(token: str, req: PendientesRequest, db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Enlace no valido")
    if p.estado != "entrega_solicitada":
        raise HTTPException(400, "La entrega no esta pendiente")
    detalle = (req.detalle or "").strip()
    if len(detalle) < 5:
        raise HTTPException(400, "Describe los pendientes")
    p.estado = "aceptado"  # vuelve a obra
    db.commit()
    notificar(db, p.user_id, "pendientes",
              f"⚠️ Pendientes reportados en {p.numero}",
              f"El cliente indica: {detalle[:250]}",
              p.id)
    return {"ok": True, "mensaje": "Reportado al contratista. La obra continua."}


@router.get("/publico/{token}/acta.pdf")
def acta_pdf(token: str, db: Session = Depends(get_db)):
    """Acta de Entrega firmada por ambas partes."""
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Enlace no valido")
    entrega = db.query(EventoShare).filter(
        EventoShare.proyecto_id == p.id, EventoShare.tipo == "entrega_confirmada").first()
    if not entrega:
        raise HTTPException(400, "La entrega aun no ha sido confirmada")
    user = db.query(Usuario).filter(Usuario.id == p.user_id).first()
    items = json.loads(p.items_json or "[]")
    aiu = json.loads(p.aiu_json or "{}")
    totales = calcular_totales(items, aiu)

    try:
        import io, base64
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=2*cm, bottomMargin=2*cm,
                                leftMargin=2*cm, rightMargin=2*cm)
        st = getSampleStyleSheet()
        cuerpo = ParagraphStyle("cu", parent=st["Normal"], fontSize=9.5, leading=14, alignment=4)
        story = [
            Paragraph(f"ACTA DE TERMINACION Y ENTREGA DE OBRA — {p.numero}",
                      ParagraphStyle("t", parent=st["Title"], fontSize=13)),
            Spacer(1, 8),
            Paragraph(
                f"En cumplimiento del contrato de ejecucion de obra civil correspondiente a la "
                f"cotizacion {p.numero}, el CONTRATISTA {user.nombre.upper()}"
                f"{' (' + user.empresa + ')' if user.empresa else ''} hace entrega formal de la obra "
                f"\"{p.nombre}\" ubicada en {p.direccion or p.region}, y el CONTRATANTE "
                f"{entrega.nombre_firma.upper()}"
                f"{', identificado(a) con documento N° ' + entrega.documento_firma if entrega.documento_firma else ''}, "
                f"declara recibirla A SATISFACCION.", cuerpo),
            Spacer(1, 8),
            Paragraph(f"Valor total del contrato: <b>${totales['total']:,}</b>".replace(",", "."), cuerpo),
            Paragraph(f"Fecha de entrega: <b>{entrega.creado.strftime('%d de %B de %Y, %H:%M')} UTC</b>", cuerpo),
            Spacer(1, 6),
            Paragraph(
                "Con la firma de la presente acta, las partes declaran cumplidas las obligaciones "
                "del contrato, quedando habilitado el pago del saldo final conforme a la clausula "
                "de forma de pago. Registro digital conforme a la Ley 527 de 1999.", cuerpo),
            Spacer(1, 30),
        ]

        # Firmas (con imagen si existe)
        def celda_firma(titulo, nombre, doc_num, estado, img_b64):
            elems = []
            if img_b64:
                try:
                    raw = base64.b64decode(img_b64.split(",", 1)[1])
                    elems.append(RLImage(io.BytesIO(raw), width=4.5*cm, height=1.8*cm, kind="proportional"))
                except Exception:
                    pass
            elems.append(Paragraph(
                f"<b>{titulo}</b><br/>{nombre}<br/>Doc: {doc_num or '—'}"
                f"<br/><font size=7 color='#64748B'>{estado}</font>", cuerpo))
            return elems

        firmas = [[
            celda_firma("EL CONTRATANTE", entrega.nombre_firma, entrega.documento_firma,
                        f"Confirmo entrega · {entrega.creado.strftime('%d/%m/%Y %H:%M')}",
                        entrega.firma_imagen),
            celda_firma("EL CONTRATISTA", user.nombre, getattr(user, "documento", ""),
                        "Entrega emitida digitalmente", getattr(user, "firma_b64", "") or ""),
        ]]
        tf = Table(firmas, colWidths=[8.3*cm, 8.3*cm])
        tf.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (0, 0), 0.7, colors.black),
            ("LINEABOVE", (1, 0), (1, 0), 0.7, colors.black),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(tf)
        doc.build(story)
        buf.seek(0)
        return StreamingResponse(buf, media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="acta_entrega_{p.numero or p.id}.pdf"'})
    except Exception as e:
        logger.error(f"Acta PDF: {e}", exc_info=True)
        raise HTTPException(500, "Error generando el acta")


# ── PERFIL PUBLICO DE REPUTACION (/c/{slug}) ─────────────────────────────────
import re as _re


def _slug_de(user: Usuario, db: Session) -> str:
    if user.slug:
        return user.slug
    base = _re.sub(r"[^a-z0-9]+", "-", (user.empresa or user.nombre).lower()).strip("-")[:50]
    slug = f"{base}-{user.id}"
    user.slug = slug
    db.commit()
    return slug


def _stats_reputacion(user_id: int, db: Session):
    filas = (
        db.query(Encuesta, Proyecto)
        .join(Proyecto, Proyecto.id == Encuesta.proyecto_id)
        .filter(Proyecto.user_id == user_id)
        .order_by(Encuesta.creado.desc()).all()
    )
    if not filas:
        return {"promedio": 0, "total": 0, "pct_recomienda": 0}, []
    promedio = round(sum(e.estrellas for e, _ in filas) / len(filas), 1)
    pct = round(sum(1 for e, _ in filas if e.recomendaria) / len(filas) * 100)
    return {"promedio": promedio, "total": len(filas), "pct_recomienda": pct}, filas


@router.get("/c/{slug}")
def perfil_publico(slug: str, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.slug == slug).first()
    if not user:
        raise HTTPException(404, "Perfil no encontrado")
    stats, filas = _stats_reputacion(user.id, db)
    obras_terminadas = db.query(Proyecto).filter(
        Proyecto.user_id == user.id, Proyecto.estado == "terminado").count()
    return {
        "nombre": user.nombre, "empresa": user.empresa,
        "ciudad": user.ciudad, "telefono": user.telefono,
        "logo_b64": user.logo_b64 or "",
        "stats": {**stats, "obras_terminadas": obras_terminadas},
        "resenas": [
            {
                "estrellas": e.estrellas, "comentario": e.comentario,
                "recomendaria": e.recomendaria,
                "proyecto": pr.nombre, "fecha": e.creado.strftime("%m/%Y"),
            }
            for e, pr in filas if e.publico and e.comentario
        ][:20],
    }


@router.get("/reputacion")
def mi_reputacion(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """El contratista gestiona que resenas publica."""
    slug = _slug_de(user, db)
    stats, filas = _stats_reputacion(user.id, db)
    return {
        "slug": slug,
        "url_publica": f"/c/{slug}",
        "stats": stats,
        "encuestas": [
            {
                "id": e.id, "estrellas": e.estrellas, "comentario": e.comentario,
                "recomendaria": e.recomendaria, "publico": e.publico,
                "proyecto": pr.nombre, "fecha": e.creado.strftime("%d/%m/%Y"),
            } for e, pr in filas
        ],
    }


class PublicarResena(BaseModel):
    encuesta_id: int
    publico: bool


@router.post("/reputacion/publicar")
def publicar_resena(req: PublicarResena, user: Usuario = Depends(usuario_actual),
                    db: Session = Depends(get_db)):
    fila = (
        db.query(Encuesta).join(Proyecto, Proyecto.id == Encuesta.proyecto_id)
        .filter(Encuesta.id == req.encuesta_id, Proyecto.user_id == user.id).first()
    )
    if not fila:
        raise HTTPException(404, "Resena no encontrada")
    fila.publico = bool(req.publico)
    db.commit()
    return {"ok": True, "publico": fila.publico}


# ═══════════════════ OTROSIES (adicionales) — lado del cliente ═══════════════════
from app.db import Otrosi
from app.services.otrosi_service import totales_otrosi, valor_adicionales


def _otrosies_publicos(p, db):
    """Los adicionales que el cliente ve en su enlace, con vista previa liquidada."""
    aiu = json.loads(p.aiu_json or "{}")
    lst = (db.query(Otrosi).filter(Otrosi.proyecto_id == p.id)
           .order_by(Otrosi.numero).all())
    out = []
    for o in lst:
        items = json.loads(o.items_json or "[]")
        totales = json.loads(o.totales_json or "{}") or totales_otrosi(items, aiu)
        out.append({
            "id": o.id, "numero": o.numero, "estado": o.estado, "motivo": o.motivo,
            "items": [{"descripcion": i.get("descripcion"), "unidad": i.get("unidad"),
                       "cantidad": i.get("cantidad"), "precio_unitario": i.get("precio_unitario")}
                      for i in items],
            "total": totales.get("total", 0),
            "nombre_firma": o.nombre_firma,
            "resuelto": o.resuelto.strftime("%d/%m/%Y") if o.resuelto else None,
        })
    return out


class OtrosiFirmaRequest(BaseModel):
    nombre: str
    documento: str = ""
    firma_imagen: str = ""


@router.post("/publico/{token}/otrosi/{otrosi_id}/aprobar")
def otrosi_aprobar(token: str, otrosi_id: int, req: OtrosiFirmaRequest,
                   db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Enlace no valido")
    o = db.query(Otrosi).filter(Otrosi.id == otrosi_id, Otrosi.proyecto_id == p.id).first()
    if not o:
        raise HTTPException(404, "Adicional no encontrado")
    if o.estado != "propuesto":
        return {"ok": True, "mensaje": f"Este adicional ya fue {o.estado}"}
    if not req.nombre.strip():
        raise HTTPException(400, "Tu nombre es requerido para aprobar")

    # CONGELAR: totales con el mismo AIU/IVA del contrato original
    items = json.loads(o.items_json or "[]")
    totales = totales_otrosi(items, json.loads(p.aiu_json or "{}"))
    o.totales_json = json.dumps(totales, ensure_ascii=False)
    o.estado = "aprobado"
    o.nombre_firma = req.nombre.strip()[:120]
    o.documento_firma = (req.documento or "").strip()[:30]
    o.firma_imagen = req.firma_imagen or ""
    o.resuelto = datetime.now(timezone.utc)

    db.add(EventoShare(proyecto_id=p.id, tipo="otrosi_aprobado",
                       nombre_firma=o.nombre_firma, documento_firma=o.documento_firma,
                       firma_imagen=o.firma_imagen))
    db.commit()
    notificar(db, p.user_id, "firmado",
              f"Aprobaron el Otrosi N.{o.numero} de {p.numero}",
              f"{o.nombre_firma} firmo el adicional por ${totales['total']:,.0f}. "
              f"Ya cuenta en avances y cuentas de cobro.".replace(",", "."),
              p.id)
    logger.info(f"Otrosi N.{o.numero} APROBADO en {p.numero} por {o.nombre_firma}")
    return {"ok": True, "mensaje": "Adicional aprobado y firmado", "total": totales["total"]}


class OtrosiRechazoRequest(BaseModel):
    motivo: str = ""


@router.post("/publico/{token}/otrosi/{otrosi_id}/rechazar")
def otrosi_rechazar(token: str, otrosi_id: int, req: OtrosiRechazoRequest,
                    db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Enlace no valido")
    o = db.query(Otrosi).filter(Otrosi.id == otrosi_id, Otrosi.proyecto_id == p.id).first()
    if not o or o.estado != "propuesto":
        raise HTTPException(400, "Este adicional ya fue resuelto")
    o.estado = "rechazado"
    o.motivo = (o.motivo + " | Cliente: " + (req.motivo or "").strip()[:150]).strip(" |")[:300]
    o.resuelto = datetime.now(timezone.utc)
    db.commit()
    notificar(db, p.user_id, "rechazado",
              f"Rechazaron el Otrosi N.{o.numero} de {p.numero}",
              (req.motivo or "El cliente no aprobo el adicional.")[:180], p.id)
    return {"ok": True}


@router.get("/publico/{token}/otrosi/{otrosi_id}.pdf")
def otrosi_pdf(token: str, otrosi_id: int, db: Session = Depends(get_db)):
    """PDF del Otrosi aprobado — descargable por ambas partes."""
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Enlace no valido")
    o = db.query(Otrosi).filter(Otrosi.id == otrosi_id, Otrosi.proyecto_id == p.id).first()
    if not o or o.estado != "aprobado":
        raise HTTPException(404, "El otrosi debe estar aprobado")
    user = db.query(Usuario).filter(Usuario.id == p.user_id).first()
    items = json.loads(o.items_json or "[]")
    tot = json.loads(o.totales_json or "{}")
    tot_orig = calcular_totales(json.loads(p.items_json or "[]"), json.loads(p.aiu_json or "{}"))
    adic_hasta = valor_adicionales(p, db)

    import io
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import cm
    from reportlab.lib import colors as rcolors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=1.8*cm, bottomMargin=1.8*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    st = getSampleStyleSheet()
    tit = ParagraphStyle("t", parent=st["Title"], fontSize=13, spaceAfter=4)
    cu = ParagraphStyle("c", parent=st["Normal"], fontSize=9, leading=13, alignment=4)
    fcop = lambda v: "$" + f"{round(v):,}".replace(",", ".")

    story = [
        Paragraph(f"OTROSI N.{o.numero} AL CONTRATO DE EJECUCION DE OBRA CIVIL", tit),
        Paragraph(f"Referencia: {p.numero} — {p.nombre}", cu), Spacer(1, 8),
        Paragraph(f"Entre <b>{p.cliente_nombre or o.nombre_firma}</b> (EL CONTRATANTE) y "
                  f"<b>{user.nombre}{' — ' + user.empresa if user.empresa else ''}</b> (EL CONTRATISTA), "
                  f"quienes suscribieron el contrato de la referencia, se acuerda ADICIONAR las siguientes "
                  f"actividades de obra{': ' + o.motivo if o.motivo else '.'}", cu),
        Spacer(1, 8),
    ]
    data = [["DESCRIPCION", "UND", "CANT", "V. UNIT", "SUBTOTAL"]]
    for it in items:
        data.append([Paragraph(str(it.get("descripcion", ""))[:120], cu),
                     it.get("unidad", ""), f'{it.get("cantidad", 0):g}',
                     fcop(it.get("precio_unitario", 0)),
                     fcop(float(it.get("cantidad", 0)) * float(it.get("precio_unitario", 0)))])
    t = Table(data, colWidths=[8.2*cm, 1.4*cm, 1.6*cm, 2.6*cm, 2.8*cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, rcolors.HexColor("#CBD5E1")),
        ("BACKGROUND", (0, 0), (-1, 0), rcolors.HexColor("#1C3A5E")),
        ("TEXTCOLOR", (0, 0), (-1, 0), rcolors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8), ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story += [t, Spacer(1, 8)]
    resumen = [
        ["Subtotal adicional", fcop(tot.get("subtotal_directo", 0))],
        [f"AIU ({tot.get('admin_pct', 0):g}/{tot.get('imprevistos_pct', 0):g}/{tot.get('utilidad_pct', 0):g})",
         fcop(tot.get("aiu_total", 0))],
        ["IVA", fcop(tot.get("iva", 0))],
        ["VALOR DE ESTE OTROSI", fcop(tot.get("total", 0))],
        ["Valor contrato original", fcop(tot_orig["total"])],
        ["NUEVO VALOR TOTAL DEL CONTRATO", fcop(tot_orig["total"] + adic_hasta)],
    ]
    tr = Table(resumen, colWidths=[11*cm, 5.6*cm])
    tr.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9), ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 3), (-1, 3), "Helvetica-Bold"),
        ("FONTNAME", (0, 5), (-1, 5), "Helvetica-Bold"),
        ("LINEABOVE", (0, 5), (-1, 5), 0.8, rcolors.HexColor("#1C3A5E")),
    ]))
    story += [tr, Spacer(1, 10),
              Paragraph("Las demas clausulas del contrato original (plazo salvo pacto en contrario, "
                        "garantias, forma de pago proporcional a los cortes de avance) permanecen vigentes "
                        "y aplican integramente a las actividades aqui adicionadas. Firmado electronicamente "
                        "al amparo de la Ley 527 de 1999.", cu),
              Spacer(1, 18)]
    fdata = [["", ""],
             [f"{o.nombre_firma}\nC.C. {o.documento_firma or '—'}\nEL CONTRATANTE — "
              f"{o.resuelto.strftime('%d/%m/%Y %H:%M') if o.resuelto else ''}",
              f"{user.nombre}\n{user.empresa or ''}\nEL CONTRATISTA"]]
    ft = Table(fdata, colWidths=[8.3*cm, 8.3*cm], rowHeights=[1.6*cm, None])
    ft.setStyle(TableStyle([
        ("LINEABOVE", (0, 1), (0, 1), 0.8, rcolors.black),
        ("LINEABOVE", (1, 1), (1, 1), 0.8, rcolors.black),
        ("FONTSIZE", (0, 1), (-1, 1), 8), ("ALIGN", (0, 1), (-1, 1), "CENTRE"),
    ]))
    # firmas dibujadas si existen
    try:
        from reportlab.platypus import Image as RLImage
        import base64
        def _img(b64):
            if not b64 or "," not in b64:
                return ""
            return RLImage(io.BytesIO(base64.b64decode(b64.split(",", 1)[1])),
                           width=3.6*cm, height=1.4*cm, kind="proportional")
        fdata[0][0] = _img(o.firma_imagen) or ""
        fdata[0][1] = _img(getattr(user, "firma_b64", "")) or ""
        ft = Table(fdata, colWidths=[8.3*cm, 8.3*cm], rowHeights=[1.6*cm, None])
        ft.setStyle(TableStyle([
            ("LINEABOVE", (0, 1), (0, 1), 0.8, rcolors.black),
            ("LINEABOVE", (1, 1), (1, 1), 0.8, rcolors.black),
            ("FONTSIZE", (0, 1), (-1, 1), 8), ("ALIGN", (0, 0), (-1, -1), "CENTRE"),
            ("VALIGN", (0, 0), (-1, 0), "BOTTOM"),
        ]))
    except Exception:
        pass
    story.append(ft)
    doc.build(story)
    buf.seek(0)
    from fastapi.responses import StreamingResponse
    return StreamingResponse(buf, media_type="application/pdf",
                             headers={"Content-Disposition":
                                      f'inline; filename="otrosi-{o.numero}-{p.numero}.pdf"'})


# ═══════════════ PARTICIPACION DEL CLIENTE (reacciones y comentarios) ═══════════════
REACCIONES_VALIDAS = ("👍", "❤️", "👏")
MAX_INTERACCIONES_DIA = 40   # candado anti-spam por proyecto


def _interacciones_de(avance_id: int, db) -> dict:
    """Reacciones (conteos) y comentarios de un avance — para ambos lados del puente."""
    from app.db import InteraccionCliente
    rows = (db.query(InteraccionCliente)
            .filter(InteraccionCliente.avance_id == avance_id)
            .order_by(InteraccionCliente.creado).all())
    reacciones = {}
    comentarios = []
    for r in rows:
        if r.tipo == "reaccion":
            reacciones[r.valor] = reacciones.get(r.valor, 0) + 1
        else:
            comentarios.append({"texto": r.valor, "nombre": r.nombre or "Cliente",
                                "fecha": r.creado.strftime("%d/%m %H:%M")})
    return {"reacciones": reacciones, "comentarios": comentarios}


class InteraccionRequest(BaseModel):
    tipo: str            # reaccion | comentario
    valor: str
    nombre: str = ""


@router.post("/publico/{token}/avances/{avance_id}/interaccion")
def interactuar(token: str, avance_id: int, req: InteraccionRequest,
                db: Session = Depends(get_db)):
    """El cliente participa: reacciona o comenta un avance de SU obra."""
    from app.db import InteraccionCliente, Avance
    from datetime import timedelta
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Enlace no valido")
    if p.estado in ("borrador", "enviado", "visto", "rechazado"):
        raise HTTPException(400, "La participacion se activa cuando el contrato este firmado")
    a = db.query(Avance).filter(Avance.id == avance_id, Avance.proyecto_id == p.id).first()
    if not a:
        raise HTTPException(404, "Avance no encontrado")

    # Candados de contenido
    if req.tipo == "reaccion":
        if req.valor not in REACCIONES_VALIDAS:
            raise HTTPException(400, "Reaccion no valida")
    elif req.tipo == "comentario":
        texto = (req.valor or "").strip()
        if not texto:
            raise HTTPException(400, "Escribe tu comentario")
        if len(texto) > 300:
            raise HTTPException(400, "Maximo 300 caracteres")
        req.valor = texto
    else:
        raise HTTPException(400, "Tipo no valido")

    # Candado anti-spam: limite diario por proyecto
    hace_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    recientes = (db.query(InteraccionCliente)
                 .filter(InteraccionCliente.proyecto_id == p.id,
                         InteraccionCliente.creado >= hace_24h).count())
    if recientes >= MAX_INTERACCIONES_DIA:
        raise HTTPException(429, "Limite diario de interacciones alcanzado — intenta mañana")

    db.add(InteraccionCliente(
        proyecto_id=p.id, avance_id=a.id, tipo=req.tipo,
        valor=req.valor, nombre=(req.nombre or "").strip()[:120]))
    db.commit()

    # El puente suena: notificar al contratista (solo comentarios; las reacciones no interrumpen)
    if req.tipo == "comentario":
        notificar(db, p.user_id, "comentario",
                  f"💬 Comentario en {p.numero}",
                  f'{req.nombre or "Tu cliente"}: "{req.valor[:140]}"', p.id)
    return {"ok": True, **_interacciones_de(a.id, db)}
