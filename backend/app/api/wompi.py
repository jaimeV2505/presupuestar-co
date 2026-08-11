# -*- coding: utf-8 -*-
"""
Wompi (Bancolombia) — pagos automaticos del plan Pro.

Arquitectura (la fuente de verdad es el WEBHOOK, nunca el redirect):

  1. POST /api/wompi/link       -> crea referencia unica + firma de integridad
                                   SHA256(referencia + centavos + COP + secreto)
                                   y devuelve la URL del Web Checkout.
  2. El usuario paga en Wompi (tarjeta, Nequi, PSE) y vuelve a /pro?id=...
  3. POST /api/wompi/webhook    -> Wompi notifica transaction.updated. Se valida
                                   el checksum: SHA256(valores de
                                   signature.properties en orden + timestamp +
                                   secreto de eventos). Si APPROVED -> activa
                                   Pro 30 dias (idempotente: solo una vez por
                                   transaccion; renovar antes de vencer SUMA).
  4. GET /api/wompi/estado      -> polling del frontend tras el redirect.

Env vars (Vercel): WOMPI_PUBLIC_KEY, WOMPI_INTEGRITY_SECRET,
WOMPI_EVENTS_SECRET, PRO_PRECIO_COP (opcional, default 79000),
APP_URL (opcional, default https://presupuestar-co.vercel.app).
"""
import os
import json
import hmac
import hashlib
import secrets
import logging
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, PagoWompi
from app.api.auth import usuario_actual

logger = logging.getLogger(__name__)
router = APIRouter()

CHECKOUT_URL = "https://checkout.wompi.co/p/"
PRO_DIAS = 30
ESTADOS_FINALES = ("APPROVED", "DECLINED", "VOIDED", "ERROR")


def _cfg():
    return {
        "public_key": os.environ.get("WOMPI_PUBLIC_KEY", "").strip(),
        "integrity": os.environ.get("WOMPI_INTEGRITY_SECRET", "").strip(),
        "events": os.environ.get("WOMPI_EVENTS_SECRET", "").strip(),
        "precio_cop": int(os.environ.get("PRO_PRECIO_COP", "79000")),
        "app_url": os.environ.get("APP_URL", "https://presupuestar-co.vercel.app").rstrip("/"),
    }


@router.get("/disponible")
def disponible():
    """El frontend decide si mostrar el boton de pago automatico."""
    c = _cfg()
    listo = bool(c["public_key"] and c["integrity"] and c["events"])
    return {"disponible": listo, "precio_cop": c["precio_cop"],
            "sandbox": c["public_key"].startswith("pub_test_")}


@router.post("/link")
def crear_link(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    c = _cfg()
    if not (c["public_key"] and c["integrity"]):
        raise HTTPException(503, "Pago automatico no configurado — usa el pago manual")

    referencia = f"PRO-{user.id}-{secrets.token_hex(6)}"
    centavos = c["precio_cop"] * 100

    pago = PagoWompi(user_id=user.id, referencia=referencia, monto_centavos=centavos)
    db.add(pago)
    db.commit()

    # Firma de integridad: SHA256(referencia + centavos + COP + secreto)
    firma = hashlib.sha256(
        f"{referencia}{centavos}COP{c['integrity']}".encode()
    ).hexdigest()

    params = {
        "public-key": c["public_key"],
        "currency": "COP",
        "amount-in-cents": str(centavos),
        "reference": referencia,
        "signature:integrity": firma,
        "redirect-url": f"{c['app_url']}/pro",
        "customer-data:email": user.email,
        "customer-data:full-name": user.nombre[:80],
    }
    logger.info(f"Wompi link {referencia} para {user.email}")
    return {"url": f"{CHECKOUT_URL}?{urlencode(params)}", "referencia": referencia}


def _extraer(data: dict, ruta: str):
    """Navega 'transaction.id' dentro del objeto data del evento."""
    actual = data
    for parte in ruta.split("."):
        if not isinstance(actual, dict) or parte not in actual:
            return None
        actual = actual[parte]
    return actual


def _activar_pro(user: Usuario):
    ahora = datetime.now(timezone.utc)
    base = ahora
    if user.plan == "pro" and user.plan_vence:
        v = user.plan_vence if user.plan_vence.tzinfo else user.plan_vence.replace(tzinfo=timezone.utc)
        if v > ahora:
            base = v  # renovacion anticipada: los dias se SUMAN
    user.plan = "pro"
    user.plan_vence = base + timedelta(days=PRO_DIAS)


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    """Recibe eventos de Wompi. SIEMPRE responde 200 rapido (Wompi reintenta 3 veces)."""
    c = _cfg()
    try:
        evento = await request.json()
    except Exception:
        return {"ok": True}

    try:
        firma = evento.get("signature") or {}
        checksum_recibido = (firma.get("checksum") or "").lower()
        propiedades = firma.get("properties") or []
        timestamp = evento.get("timestamp")
        data = evento.get("data") or {}

        if not (checksum_recibido and propiedades and timestamp is not None and c["events"]):
            logger.warning("Wompi webhook incompleto o sin secreto configurado")
            return {"ok": True}

        # Checksum: valores de properties (en orden) + timestamp + secreto -> SHA256
        concatenado = "".join(str(_extraer(data, p)) for p in propiedades)
        concatenado += f"{timestamp}{c['events']}"
        checksum_calculado = hashlib.sha256(concatenado.encode()).hexdigest()

        if not hmac.compare_digest(checksum_calculado, checksum_recibido):
            logger.warning("Wompi webhook: checksum INVALIDO — evento descartado")
            return {"ok": True}

        tx = data.get("transaction") or {}
        referencia = tx.get("reference") or ""
        estado = (tx.get("status") or "").upper()
        if not referencia.startswith("PRO-"):
            return {"ok": True}

        pago = db.query(PagoWompi).filter(PagoWompi.referencia == referencia).first()
        if not pago:
            logger.warning(f"Wompi webhook: referencia desconocida {referencia}")
            return {"ok": True}

        # Idempotencia: los estados finales no se reprocesan
        if pago.estado in ESTADOS_FINALES:
            return {"ok": True}

        # Verificacion extra: el monto no puede haber cambiado
        if estado == "APPROVED" and int(tx.get("amount_in_cents") or 0) != pago.monto_centavos:
            logger.error(f"Wompi: monto alterado en {referencia} — NO se activa")
            pago.estado = "ERROR"
            db.commit()
            return {"ok": True}

        pago.estado = estado if estado in ESTADOS_FINALES else pago.estado
        pago.transaction_id = str(tx.get("id") or "")[:80]
        pago.medio = str(tx.get("payment_method_type") or "")[:40]
        pago.actualizado = datetime.now(timezone.utc)

        if estado == "APPROVED":
            user = db.query(Usuario).filter(Usuario.id == pago.user_id).first()
            if user:
                _activar_pro(user)
                logger.info(f"Wompi APPROVED {referencia}: Pro activado para {user.email} "
                            f"hasta {user.plan_vence} via {pago.medio}")
        db.commit()
    except Exception as e:
        logger.error(f"Wompi webhook error: {e}", exc_info=True)
        db.rollback()
    return {"ok": True}


@router.get("/estado")
def estado_pago(referencia: str, user: Usuario = Depends(usuario_actual),
                db: Session = Depends(get_db)):
    """Polling del frontend tras volver del checkout."""
    pago = (db.query(PagoWompi)
            .filter(PagoWompi.referencia == referencia, PagoWompi.user_id == user.id)
            .first())
    if not pago:
        raise HTTPException(404, "Pago no encontrado")
    return {
        "estado": pago.estado,
        "medio": pago.medio,
        "plan": user.plan,
        "plan_vence": user.plan_vence.strftime("%d/%m/%Y") if user.plan_vence else None,
    }
