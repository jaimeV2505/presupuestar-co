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
import os
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db import (get_db, Usuario, Cliente, Proyecto, EventoShare, Avance, Diseno,
                    Gasto, CuentaCobro, Encuesta, Notificacion, PagoWompi,
                    Otrosi, Abono, InteraccionCliente, ApuUsuario, Proveedor,
                    PrecioProveedor, TicketSoporte, MensajeSoporte, SolicitudPro)
from app.api.pagos import admin_actual, _admins

logger = logging.getLogger(__name__)
router = APIRouter()

# TODO lo que vale la pena renacer, en orden de restore (padres antes que hijos).
# Excluido A PROPOSITO: IntentoAcceso (ruido de rate-limit, sin valor de restore).
MODELOS = [Usuario, Cliente, Proyecto, EventoShare, Avance, Gasto,
           CuentaCobro, Abono, Otrosi, InteraccionCliente, Diseno,
           ApuUsuario, Proveedor, PrecioProveedor,
           Encuesta, Notificacion, PagoWompi,
           TicketSoporte, MensajeSoporte, SolicitudPro]


def _serializar(obj):
    # SEGURIDAD DEL RESPALDO: las credenciales JAMAS viajan en el backup.
    # Un backup se comparte, se sube a Drive, se pega en herramientas —
    # los hashes de clave y tokens de recuperacion no tienen por que ir.
    # Al restaurar, cada usuario recupera su clave con "olvide mi clave".
    SENSIBLES = {"password_hash": "[protegido — restaurar via 'olvide mi clave']",
                 "reset_token_hash": None, "reset_expira": None}
    out = {}
    for col in obj.__table__.columns:
        if obj.__table__.name == "usuarios" and col.name in SENSIBLES:
            if SENSIBLES[col.name] is not None:
                out[col.name] = SENSIBLES[col.name]
            continue
        v = getattr(obj, col.name)
        if isinstance(v, (datetime, date)):
            v = v.isoformat()
        out[col.name] = v
    return out


@router.get("/completo")
def backup_completo(x_backup_token: str = Header(default=""),
                    authorization: str = Header(default=""),
                    db: Session = Depends(get_db)):
    """Autenticacion dual: JWT de admin (boton del panel) o BACKUP_TOKEN (GitHub Action)."""
    import hmac
    esperado = os.environ.get("BACKUP_TOKEN", "").strip()
    admin_email = "github-action"
    token_ok = bool(esperado) and hmac.compare_digest(x_backup_token, esperado)
    if not token_ok:
        try:
            import jwt as _jwt
            from app.api.auth import JWT_SECRET, JWT_ALG
            token = (authorization or "").replace("Bearer ", "").strip()
            payload = _jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
            u = db.query(Usuario).filter(Usuario.id == int(payload["sub"])).first()
            if not (u and u.email.lower() in _admins()):
                raise ValueError("no es admin")
            admin_email = u.email
        except Exception:
            raise HTTPException(401, "Solo administradores")
    admin = type("A", (), {"email": admin_email})()
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
