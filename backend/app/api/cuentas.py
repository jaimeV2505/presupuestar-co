# -*- coding: utf-8 -*-
"""
Cuentas de cobro por avance — el documento con el que cobra el contratista.

Liquidacion automatica de cada corte:
  valor_corte  = ejecutado acumulado del avance - cortes ya cobrados
  amortizacion = valor_corte x % de anticipo (del contrato firmado)
  neto         = valor_corte - amortizacion

El PDF sale con los datos del perfil (cedula, cuenta bancaria, firma
manuscrita) y el cliente lo abre desde un enlace publico ligado al
share_token del proyecto.
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto, Avance, CuentaCobro
from app.api.auth import usuario_actual

logger = logging.getLogger(__name__)
router = APIRouter()


def _proyecto(pid: int, user: Usuario, db: Session) -> Proyecto:
    p = db.query(Proyecto).filter(Proyecto.id == pid, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    return p


def _numero_cc(user: Usuario, db: Session) -> str:
    year = datetime.now(timezone.utc).year
    total = db.query(CuentaCobro).filter(CuentaCobro.user_id == user.id).count()
    return f"CC-{year}-{total + 1:04d}"


def _liquidar(p: Proyecto, avance: Avance, db: Session) -> dict:
    """Calcula la liquidacion del corte sin crear nada."""
    ya_cobrado = (
        db.query(CuentaCobro)
        .filter(CuentaCobro.proyecto_id == p.id)
        .all()
    )
    cobrado_previo = sum(c.valor_corte for c in ya_cobrado)
    valor_corte = max(0, (avance.valor_ejecutado or 0) - cobrado_previo)

    cfg = json.loads(p.contrato_json or "{}")
    anticipo_pct = float(cfg.get("anticipo_pct") or 0)
    amortizacion = round(valor_corte * anticipo_pct / 100)
    neto = valor_corte - amortizacion

    return {
        "avance_id": avance.id,
        "avance_titulo": avance.titulo,
        "avance_pct": avance.porcentaje,
        "ejecutado_acumulado": avance.valor_ejecutado or 0,
        "cobrado_previo": cobrado_previo,
        "valor_corte": valor_corte,
        "anticipo_pct": anticipo_pct,
        "amortizacion": amortizacion,
        "neto": neto,
    }


def _cc_out(c: CuentaCobro):
    return {
        "id": c.id, "numero": c.numero, "concepto": c.concepto,
        "valor_corte": c.valor_corte, "anticipo_pct": c.anticipo_pct,
        "amortizacion": c.amortizacion, "neto": c.neto,
        "estado": c.estado, "avance_id": c.avance_id,
        "fecha": c.creado.strftime("%d/%m/%Y"),
        "fecha_pago": c.pagado.strftime("%d/%m/%Y") if c.pagado else None,
    }


def _resumen_caja(p: Proyecto, db: Session):
    cuentas = db.query(CuentaCobro).filter(CuentaCobro.proyecto_id == p.id).all()
    cobrado = sum(c.neto for c in cuentas if c.estado == "pagada")
    por_cobrar = sum(c.neto for c in cuentas if c.estado == "enviada")
    return {"cobrado": cobrado, "por_cobrar": por_cobrar, "n_cuentas": len(cuentas)}


@router.get("/proyectos/{pid}/cuentas")
def listar(pid: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto(pid, user, db)
    cuentas = (db.query(CuentaCobro).filter(CuentaCobro.proyecto_id == p.id)
               .order_by(CuentaCobro.creado.desc()).all())
    return {"resumen": _resumen_caja(p, db), "cuentas": [_cc_out(c) for c in cuentas]}


@router.get("/proyectos/{pid}/cuentas/preview")
def preview(pid: int, avance_id: int,
            user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """Liquidacion del corte antes de generar la cuenta."""
    p = _proyecto(pid, user, db)
    a = db.query(Avance).filter(Avance.id == avance_id, Avance.proyecto_id == p.id).first()
    if not a:
        raise HTTPException(404, "Avance no encontrado")
    return _liquidar(p, a, db)


class CrearCuentaRequest(BaseModel):
    avance_id: int


@router.post("/proyectos/{pid}/cuentas")
def crear(pid: int, req: CrearCuentaRequest,
          user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto(pid, user, db)
    a = db.query(Avance).filter(Avance.id == req.avance_id, Avance.proyecto_id == p.id).first()
    if not a:
        raise HTTPException(404, "Avance no encontrado")

    liq = _liquidar(p, a, db)
    if liq["valor_corte"] <= 0:
        raise HTTPException(400, "Este corte ya fue cobrado en cuentas anteriores")

    concepto = (
        f"Corte de obra segun avance '{a.titulo}' ({a.porcentaje}% acumulado) del "
        f"proyecto \"{p.nombre}\" — contrato {p.numero}."
    )
    c = CuentaCobro(
        user_id=user.id, proyecto_id=p.id, avance_id=a.id,
        numero=_numero_cc(user, db),
        concepto=concepto,
        valor_corte=liq["valor_corte"],
        anticipo_pct=int(liq["anticipo_pct"]),
        amortizacion=liq["amortizacion"],
        neto=liq["neto"],
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    logger.info(f"Cuenta {c.numero}: neto ${c.neto:,} proyecto {p.id}")
    out = _cc_out(c)
    out["resumen"] = _resumen_caja(p, db)
    return out


@router.post("/{cid}/pagada")
def marcar_pagada(cid: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    c = (db.query(CuentaCobro)
         .filter(CuentaCobro.id == cid, CuentaCobro.user_id == user.id).first())
    if not c:
        raise HTTPException(404, "Cuenta no encontrada")
    c.estado = "pagada"
    c.pagado = datetime.now(timezone.utc)
    db.commit()
    return {"ok": True, "fecha_pago": c.pagado.strftime("%d/%m/%Y")}


@router.delete("/{cid}")
def eliminar(cid: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    c = (db.query(CuentaCobro)
         .filter(CuentaCobro.id == cid, CuentaCobro.user_id == user.id).first())
    if not c:
        raise HTTPException(404, "Cuenta no encontrada")
    if c.estado == "pagada":
        raise HTTPException(400, "Una cuenta pagada no se elimina")
    db.delete(c)
    db.commit()
    return {"ok": True}


# ── PDF publico: el cliente lo abre desde el enlace del proyecto ─────────────
@router.get("/publico/{token}/{cid}.pdf")
def pdf_publico(token: str, cid: int, db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.share_token == token).first()
    if not p:
        raise HTTPException(404, "Enlace no valido")
    c = (db.query(CuentaCobro)
         .filter(CuentaCobro.id == cid, CuentaCobro.proyecto_id == p.id).first())
    if not c:
        raise HTTPException(404, "Cuenta no encontrada")
    user = db.query(Usuario).filter(Usuario.id == p.user_id).first()
    return _generar_pdf(c, p, user)


def _generar_pdf(c: CuentaCobro, p: Proyecto, user: Usuario):
    try:
        import io, base64
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                        Paragraph, Spacer, Image as RLImage)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        def fmt(v):
            return f"${round(v or 0):,}".replace(",", ".")

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=2.2*cm,
                                bottomMargin=2*cm, leftMargin=2.2*cm, rightMargin=2.2*cm)
        st = getSampleStyleSheet()
        cuerpo = ParagraphStyle("cu", parent=st["Normal"], fontSize=9.5, leading=14)

        story = [
            Paragraph(f"CUENTA DE COBRO N° {c.numero}",
                      ParagraphStyle("t", parent=st["Title"], fontSize=14, spaceAfter=4)),
            Paragraph(f"{(user.ciudad or 'Colombia').capitalize()}, {c.creado.strftime('%d de %B de %Y')}",
                      ParagraphStyle("f", parent=st["Normal"], fontSize=9,
                                     textColor=colors.HexColor("#64748B"), spaceAfter=16)),
            Paragraph(f"<b>{(p.cliente_nombre or 'EL CONTRATANTE').upper()}</b>", cuerpo),
            Paragraph("DEBE A:", ParagraphStyle("d", parent=st["Normal"], fontSize=9,
                                                textColor=colors.HexColor("#64748B"), spaceBefore=4, spaceAfter=4)),
            Paragraph(f"<b>{user.nombre.upper()}</b>"
                      f"{' — ' + user.empresa if user.empresa else ''}"
                      f"<br/>Documento: {getattr(user, 'documento', '') or '—'}"
                      f"{('<br/>Tel: ' + user.telefono) if user.telefono else ''}", cuerpo),
            Spacer(1, 14),
            Paragraph("<b>CONCEPTO</b>", cuerpo),
            Paragraph(c.concepto, cuerpo),
            Spacer(1, 12),
        ]

        data = [
            ["Valor ejecutado del corte", fmt(c.valor_corte)],
        ]
        if c.amortizacion:
            data.append([f"(-) Amortizacion anticipo ({c.anticipo_pct}%)", f"- {fmt(c.amortizacion)}"])
        data.append(["NETO A PAGAR", fmt(c.neto)])
        t = Table(data, colWidths=[11*cm, 5*cm])
        t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EFF6FF")),
        ]))
        story.append(t)
        story.append(Spacer(1, 14))

        if getattr(user, "pago_info", ""):
            story.append(Paragraph(f"<b>Forma de pago:</b> {user.pago_info}", cuerpo))
            story.append(Spacer(1, 8))

        story.append(Paragraph(
            "El presente cobro corresponde a servicios de construccion prestados en "
            "ejecucion del contrato de obra referido. Documento generado digitalmente "
            "con registro de fecha y hora.", ParagraphStyle(
                "n", parent=st["Normal"], fontSize=8, textColor=colors.HexColor("#94A3B8"))))
        story.append(Spacer(1, 30))

        firma_elems = []
        if getattr(user, "firma_b64", ""):
            try:
                raw = base64.b64decode(user.firma_b64.split(",", 1)[1])
                firma_elems.append(RLImage(io.BytesIO(raw), width=4.5*cm, height=1.8*cm,
                                           kind="proportional"))
            except Exception:
                pass
        firma_elems.append(Paragraph(
            f"<b>{user.nombre}</b><br/>Doc: {getattr(user, 'documento', '') or '—'}", cuerpo))
        tf = Table([[firma_elems]], colWidths=[8*cm])
        tf.setStyle(TableStyle([("LINEABOVE", (0, 0), (0, 0), 0.7, colors.black),
                                ("TOPPADDING", (0, 0), (-1, -1), 6)]))
        story.append(tf)

        doc.build(story)
        buf.seek(0)
        return StreamingResponse(
            buf, media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{c.numero}.pdf"'})
    except Exception as e:
        logger.error(f"PDF cuenta: {e}", exc_info=True)
        raise HTTPException(500, "Error generando la cuenta de cobro")
