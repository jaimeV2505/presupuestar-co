# -*- coding: utf-8 -*-
"""Exportar presupuesto a Excel y PDF con logo del contratista."""
import json
import io
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto
from app.api.auth import usuario_actual
from app.services.calculo_presupuesto import calcular_totales

logger = logging.getLogger(__name__)
router = APIRouter()


class ExportRequest(BaseModel):
    proyecto_id: int


def _cargar(proyecto_id: int, user: Usuario, db: Session):
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    items = json.loads(p.items_json or "[]")
    if not items:
        raise HTTPException(400, "El presupuesto esta vacio")
    aiu = json.loads(p.aiu_json or "{}")
    return p, items, aiu, calcular_totales(items, aiu)


@router.post("/excel")
def exportar_excel(req: ExportRequest, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p, items, aiu, tot = _cargar(req.proyecto_id, user, db)
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        wb = Workbook()
        ws = wb.active
        ws.title = "Presupuesto"

        azul = PatternFill("solid", fgColor="1C3A5E")
        gris = PatternFill("solid", fgColor="F1F5F9")
        blanco_bold = Font(color="FFFFFF", bold=True, size=11)
        bold = Font(bold=True)
        thin = Border(bottom=Side(style="thin", color="E2E8F0"))

        # Encabezado
        ws["A1"] = user.empresa or user.nombre
        ws["A1"].font = Font(bold=True, size=14)
        ws["A2"] = f"Presupuesto: {p.nombre}"
        ws["A3"] = f"Cliente: {p.cliente_nombre or '-'}  |  {p.direccion or ''}"
        ws["A4"] = f"Fecha: {p.actualizado.strftime('%d/%m/%Y') if p.actualizado else ''}  |  Contacto: {user.telefono or user.email}"

        fila = 6
        headers = ["Item", "Capitulo", "Descripcion", "Und", "Cantidad", "Vr. Unitario", "Vr. Total"]
        for col, h in enumerate(headers, 1):
            c = ws.cell(row=fila, column=col, value=h)
            c.fill = azul; c.font = blanco_bold
            c.alignment = Alignment(horizontal="center")
        fila += 1

        cap_actual = None
        n = 0
        for it in items:
            cap = it.get("capitulo", "OTROS")
            if cap != cap_actual:
                cap_actual = cap
                c = ws.cell(row=fila, column=1, value=cap)
                ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=7)
                c.fill = gris; c.font = bold
                fila += 1
            n += 1
            total_item = round(it["cantidad"] * it["precio_unitario"])
            vals = [n, cap, it["descripcion"], it["unidad"], it["cantidad"], it["precio_unitario"], total_item]
            for col, v in enumerate(vals, 1):
                c = ws.cell(row=fila, column=col, value=v)
                c.border = thin
                if col in (6, 7): c.number_format = '"$"#,##0'
            fila += 1

        # Totales
        fila += 1
        def _linea(label, valor, es_total=False):
            nonlocal fila
            c1 = ws.cell(row=fila, column=6, value=label)
            c2 = ws.cell(row=fila, column=7, value=valor)
            c2.number_format = '"$"#,##0'
            if es_total:
                c1.font = bold; c2.font = bold
                c1.fill = gris; c2.fill = gris
            fila += 1

        _linea("Costo directo", tot["subtotal_directo"])
        if tot["aiu_total"] > 0:
            _linea(f"Administracion {tot['admin_pct']}%", tot["admin_valor"])
            _linea(f"Imprevistos {tot['imprevistos_pct']}%", tot["imprevistos_valor"])
            _linea(f"Utilidad {tot['utilidad_pct']}%", tot["utilidad_valor"])
        _linea("IVA", tot["iva"])
        _linea("TOTAL", tot["total"], es_total=True)

        ws.cell(row=fila + 1, column=1, value=tot["regimen_iva"]).font = Font(size=9, italic=True, color="64748B")
        fila += 2

        # Condiciones estandar del contratista
        condiciones = getattr(user, "condiciones", "") or ""
        if condiciones:
            ws.cell(row=fila + 1, column=1, value="CONDICIONES:").font = Font(bold=True, size=9)
            fila += 1
            for linea in condiciones.split("\n")[:15]:
                ws.cell(row=fila + 1, column=1, value=linea[:150]).font = Font(size=8, color="475569")
                fila += 1

        # Marca de agua plan gratis (motor de crecimiento)
        if user.plan == "gratis":
            fila += 1
            c = ws.cell(row=fila + 1, column=1, value="Hecho con PresupuestarCO — presupuestos profesionales en minutos · presupuestar.co")
            c.font = Font(size=8, italic=True, color="94A3B8")

        # Anchos
        for col, w in zip("ABCDEFG", [6, 22, 55, 8, 10, 14, 16]):
            ws.column_dimensions[col].width = w

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="presupuesto_{p.id}.xlsx"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel: {e}", exc_info=True)
        raise HTTPException(500, f"Error generando Excel: {e}")


@router.post("/pdf")
def exportar_pdf(req: ExportRequest, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p, items, aiu, tot = _cargar(req.proyecto_id, user, db)
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                        Paragraph, Spacer, Image as RLImage)
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=1.5*cm, bottomMargin=1.5*cm,
                                leftMargin=1.5*cm, rightMargin=1.5*cm)
        styles = getSampleStyleSheet()
        story = []

        # Logo si existe
        if user.logo_b64:
            try:
                import base64
                b64 = user.logo_b64.split(",")[-1]
                logo_bytes = base64.b64decode(b64)
                img = RLImage(io.BytesIO(logo_bytes), width=3*cm, height=3*cm, kind='proportional')
                story.append(img)
                story.append(Spacer(1, 8))
            except Exception:
                pass

        titulo = ParagraphStyle("t", parent=styles["Title"], fontSize=16, textColor=colors.HexColor("#1C3A5E"), alignment=0)
        story.append(Paragraph(user.empresa or user.nombre, titulo))
        story.append(Paragraph(f"<b>Presupuesto:</b> {p.nombre}", styles["Normal"]))
        story.append(Paragraph(f"<b>Cliente:</b> {p.cliente_nombre or '-'} | {p.direccion or ''}", styles["Normal"]))
        story.append(Paragraph(
            f"<b>Fecha:</b> {p.actualizado.strftime('%d/%m/%Y') if p.actualizado else ''} | "
            f"<b>Contacto:</b> {user.telefono or user.email}", styles["Normal"]))
        story.append(Spacer(1, 14))

        # Tabla de items agrupada por capitulo
        data = [["#", "Descripcion", "Und", "Cant", "Vr. Unit", "Vr. Total"]]
        estilos_extra = []
        fila_idx = 1
        cap_actual = None
        n = 0
        for it in items:
            cap = it.get("capitulo", "OTROS")
            if cap != cap_actual:
                cap_actual = cap
                data.append([cap, "", "", "", "", ""])
                estilos_extra.append(("SPAN", (0, fila_idx), (-1, fila_idx)))
                estilos_extra.append(("BACKGROUND", (0, fila_idx), (-1, fila_idx), colors.HexColor("#F1F5F9")))
                estilos_extra.append(("FONTNAME", (0, fila_idx), (-1, fila_idx), "Helvetica-Bold"))
                fila_idx += 1
            n += 1
            total_item = round(it["cantidad"] * it["precio_unitario"])
            desc = it["descripcion"][:80]
            data.append([str(n), Paragraph(desc, styles["BodyText"]), it["unidad"],
                         f"{it['cantidad']:g}", f"${it['precio_unitario']:,.0f}", f"${total_item:,.0f}"])
            fila_idx += 1

        tabla = Table(data, colWidths=[1*cm, 9.5*cm, 1.3*cm, 1.6*cm, 2.5*cm, 2.6*cm], repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1C3A5E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E8F0")),
            ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ] + estilos_extra))
        story.append(tabla)
        story.append(Spacer(1, 14))

        # Resumen
        resumen = [["Costo directo", f"${tot['subtotal_directo']:,.0f}"]]
        if tot["aiu_total"] > 0:
            resumen += [
                [f"Administracion {tot['admin_pct']}%", f"${tot['admin_valor']:,.0f}"],
                [f"Imprevistos {tot['imprevistos_pct']}%", f"${tot['imprevistos_valor']:,.0f}"],
                [f"Utilidad {tot['utilidad_pct']}%", f"${tot['utilidad_valor']:,.0f}"],
            ]
        resumen += [["IVA", f"${tot['iva']:,.0f}"], ["TOTAL", f"${tot['total']:,.0f}"]]
        tr = Table(resumen, colWidths=[13*cm, 5.5*cm])
        tr.setStyle(TableStyle([
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F1F5F9")),
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#1C3A5E")),
        ]))
        story.append(tr)
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<i>{tot['regimen_iva']}</i>",
                               ParagraphStyle("n", parent=styles["Normal"], fontSize=7, textColor=colors.HexColor("#64748B"))))
        if p.notas:
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<b>Notas:</b> {p.notas[:800]}", styles["Normal"]))

        # Condiciones estandar del contratista
        condiciones = getattr(user, "condiciones", "") or ""
        if condiciones:
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>Condiciones:</b>", styles["Normal"]))
            cond_style = ParagraphStyle("cond", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#475569"))
            for linea in condiciones.split("\n")[:15]:
                if linea.strip():
                    story.append(Paragraph(linea.strip()[:200], cond_style))

        # Marca de agua plan gratis
        if user.plan == "gratis":
            story.append(Spacer(1, 16))
            marca = ParagraphStyle("marca", parent=styles["Normal"], fontSize=7,
                                   textColor=colors.HexColor("#94A3B8"), alignment=1)
            story.append(Paragraph("Hecho con <b>PresupuestarCO</b> — presupuestos profesionales en minutos", marca))

        doc.build(story)
        buf.seek(0)
        return StreamingResponse(
            buf, media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="presupuesto_{p.id}.pdf"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF: {e}", exc_info=True)
        raise HTTPException(500, f"Error generando PDF: {e}")
