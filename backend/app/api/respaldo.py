# -*- coding: utf-8 -*-
"""
Respaldo completo de la base de datos — solo admins.

GET /api/respaldo/completo -> descarga un JSON con TODAS las tablas.
Guardalo semanalmente (Drive, disco): es tu seguro contra desastres.
Incluye las imagenes base64 (firmas, fotos, recibos) — el respaldo es total.
"""
import json
import logging
from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db import (get_db, Usuario, Cliente, Proyecto, EventoShare, Avance,
                    Gasto, CuentaCobro, Encuesta, Notificacion, PagoWompi)
from app.api.pagos import admin_actual

logger = logging.getLogger(__name__)
router = APIRouter()

MODELOS = [Usuario, Cliente, Proyecto, EventoShare, Avance, Gasto,
           CuentaCobro, Encuesta, Notificacion, PagoWompi]


def _serializar(obj):
    out = {}
    for col in obj.__table__.columns:
        v = getattr(obj, col.name)
        if isinstance(v, (datetime, date)):
            v = v.isoformat()
        out[col.name] = v
    return out


@router.get("/completo")
def backup_completo(admin: Usuario = Depends(admin_actual), db: Session = Depends(get_db)):
    def generar():
        yield '{"generado": "%s", "version": 1' % datetime.now(timezone.utc).isoformat()
        for modelo in MODELOS:
            yield ', "%s": [' % modelo.__tablename__
            primera = True
            for fila in db.query(modelo).yield_per(200):
                prefijo = '' if primera else ','
                primera = False
                yield prefijo + json.dumps(_serializar(fila), ensure_ascii=False, default=str)
            yield ']'
        yield '}'
        logger.info(f"Backup completo descargado por {admin.email}")

    fecha = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    return StreamingResponse(
        generar(), media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="presupuestarco-backup-{fecha}.json"'})


@router.get("/resumen")
def resumen(admin: Usuario = Depends(admin_actual), db: Session = Depends(get_db)):
    """Conteos rapidos para saber que respaldarias."""
    return {m.__tablename__: db.query(m).count() for m in MODELOS}
