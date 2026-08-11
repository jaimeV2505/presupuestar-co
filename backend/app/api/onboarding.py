# -*- coding: utf-8 -*-
"""
Onboarding: proyecto de ejemplo sembrado + checklist de misiones.

Filosofia: las misiones se AUTO-MARCAN leyendo los datos reales del usuario
(tiene proyectos? tiene firma? genero un link?). Solo los flags manuales
(vio la vista del cliente, exploro el ejemplo, cerro el checklist, tipo de
negocio) se guardan en usuarios.onboarding_json.
"""
import json
import uuid
import logging
import secrets
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto, EventoShare, Avance
from app.api.auth import usuario_actual

logger = logging.getLogger(__name__)
router = APIRouter()


# ── SIEMBRA DEL PROYECTO DE EJEMPLO ──────────────────────────────────────────
DEMO_BUSQUEDAS = [
    (["demolicion", "enchape"], 12), (["alistado", "piso"], 4),
    (["enchape", "pared", "ceramica"], 18), (["enchape", "piso"], 4),
    (["sanitario"], 1), (["lavamanos"], 1),
    (["punto", "hidraulico"], 4), (["pintura", "vinilo"], 10),
]


def sembrar_demo(user: Usuario, db: Session):
    """Crea el proyecto de ejemplo al registrarse. Nunca rompe el registro."""
    try:
        from app.services import apu_service as APU
        from app.services.apu_service import FACTORES_REGION
        apu_db = APU.load_apu_db()
        factor = FACTORES_REGION.get(user.ciudad, FACTORES_REGION["bogota"])["factor"]

        items = []
        for palabras, cantidad in DEMO_BUSQUEDAS:
            palabras = [w.lower() for w in palabras]
            m = next((it for it in apu_db
                      if all(w in it["descripcion"].lower() for w in palabras)), None)
            if not m:
                m = next((it for it in apu_db
                          if palabras[0] in it["descripcion"].lower()), None)
            if m:
                items.append({
                    "id": uuid.uuid4().hex[:10],
                    "capitulo": m.get("categoria", "GENERAL"),
                    "descripcion": m["descripcion"],
                    "unidad": m.get("unidad", "un"),
                    "cantidad": cantidad,
                    "precio_unitario": round(m["precio"] * factor),
                })
        if not items:
            return

        p = Proyecto(
            user_id=user.id,
            es_demo=True,
            nombre="🎓 Proyecto de ejemplo — tócalo sin miedo",
            numero="EJEMPLO",
            cliente_nombre="",
            items_json=json.dumps(items, ensure_ascii=False),
            aiu_json=json.dumps({"admin": 15, "imprevistos": 5, "utilidad": 8,
                                 "aplicar": True, "iva_sobre_utilidad": True}),
            contrato_json=json.dumps({"plazo_dias": 20, "anticipo_pct": 50,
                                      "fecha_inicio": "", "lugar": ""}),
            region=user.ciudad,
            estado="aceptado",
            share_token=secrets.token_urlsafe(16),
        )
        db.add(p)
        db.flush()

        # Firma demo para que el contrato y los botones de obra esten activos
        db.add(EventoShare(proyecto_id=p.id, tipo="aceptado",
                           nombre_firma="Cliente de Ejemplo",
                           documento_firma="000000"))

        # Un avance publicado para explorar Avances/Cobros con datos
        detalle, total, ejec = [], 0, 0
        for i, it in enumerate(items):
            vi = round(it["cantidad"] * it["precio_unitario"])
            pct = 100 if i < 2 else (50 if i < 4 else 0)
            ve = round(vi * pct / 100)
            total += vi
            ejec += ve
            detalle.append({"id": it["id"], "descripcion": it["descripcion"][:120],
                            "capitulo": it["capitulo"], "unidad": it["unidad"],
                            "valor_item": vi, "pct": pct, "valor_ejec": ve})
        db.add(Avance(
            proyecto_id=p.id,
            titulo="Corte 1 — Demolición y alistado",
            descripcion="Este es un avance de ejemplo: el % se marca por actividad.",
            porcentaje=int(round(ejec / total * 100)) if total else 0,
            valor_ejecutado=ejec,
            items_json=json.dumps(detalle, ensure_ascii=False),
            fotos_json="[]",
        ))
        db.commit()
        logger.info(f"Demo sembrado para user {user.id}")
    except Exception as e:
        logger.warning(f"Siembra demo fallo: {e}")
        db.rollback()


# ── ESTADO DEL ONBOARDING ────────────────────────────────────────────────────
def _flags(user: Usuario) -> dict:
    try:
        return json.loads(user.onboarding_json or "{}")
    except Exception:
        return {}


@router.get("")
def estado(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    flags = _flags(user)
    reales = (db.query(Proyecto)
              .filter(Proyecto.user_id == user.id, Proyecto.es_demo == False)  # noqa: E712
              .all())
    demo = (db.query(Proyecto)
            .filter(Proyecto.user_id == user.id, Proyecto.es_demo == True)  # noqa: E712
            .first())

    marca = sum([bool(user.logo_b64), bool(getattr(user, "firma_b64", "")),
                 bool(getattr(user, "documento", ""))])

    misiones = {
        "m1_presupuesto": len(reales) > 0,
        "m2_marca": marca >= 2,
        "m3_whatsapp": any(p.share_token for p in reales),
        "m4_vista_cliente": bool(flags.get("vista_cliente")),
        "m5_explora": bool(flags.get("explora")),
    }
    completadas = sum(misiones.values())
    return {
        "tipo": flags.get("tipo"),
        "cerrado": bool(flags.get("cerrado")),
        "misiones": misiones,
        "progreso": round(completadas / 5 * 100),
        "marca_detalle": {"logo": bool(user.logo_b64),
                          "firma": bool(getattr(user, "firma_b64", "")),
                          "documento": bool(getattr(user, "documento", ""))},
        "demo": {"id": demo.id, "share_token": demo.share_token} if demo else None,
    }


class MarcarRequest(BaseModel):
    clave: str  # vista_cliente | explora | cerrado
    valor: bool = True


@router.post("/marcar")
def marcar(req: MarcarRequest, user: Usuario = Depends(usuario_actual),
           db: Session = Depends(get_db)):
    if req.clave not in ("vista_cliente", "explora", "cerrado"):
        return {"ok": False}
    flags = _flags(user)
    flags[req.clave] = bool(req.valor)
    user.onboarding_json = json.dumps(flags)
    db.commit()
    return {"ok": True}


class TipoRequest(BaseModel):
    tipo: str  # maestro | remodelador | contratista


@router.post("/tipo")
def definir_tipo(req: TipoRequest, user: Usuario = Depends(usuario_actual),
                 db: Session = Depends(get_db)):
    flags = _flags(user)
    flags["tipo"] = req.tipo if req.tipo in ("maestro", "remodelador", "contratista") else "contratista"
    user.onboarding_json = json.dumps(flags)
    db.commit()
    return {"ok": True, "tipo": flags["tipo"]}
