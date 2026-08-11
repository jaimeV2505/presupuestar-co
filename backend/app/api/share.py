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
    return {
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


# ── CONTRATO DE EJECUCION DE OBRA ────────────────────────────────────────────
from fastapi.responses import StreamingResponse
from app.services.contrato_service import generar_contrato


def _contrato_de_token(token: str, db: Session):
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
        tf = Table(firmas_data, colWidths=[8.3*cm, 8.3*cm])
        tf.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (0, 0), 0.7, colors.black),
            ("LINEABOVE", (1, 0), (1, 0), 0.7, colors.black),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
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
