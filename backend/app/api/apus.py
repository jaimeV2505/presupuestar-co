# -*- coding: utf-8 -*-
"""MIS APUs — la coleccion personal del usuario.
Regla sagrada: la base 2026 es INMUTABLE (vigilada por hash en el CI);
aqui vive lo propio: manual, duplicado de la base, o compuesto por insumos."""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from app.db import get_db, Usuario, ApuUsuario
from app.api.auth import usuario_actual
from app.services.apu_propio_service import componer_precio

logger = logging.getLogger(__name__)
router = APIRouter()
MAX_APUS = 500          # candado de volumen por usuario
SECTORES = ("privado", "publico", "ambos")


def _out(a: ApuUsuario) -> dict:
    return {"id": a.id, "codigo": a.codigo, "descripcion": a.descripcion,
            "unidad": a.unidad, "precio": a.precio, "sector_tag": a.sector_tag,
            "region": a.region, "origen_base": a.origen_base,
            "desglose": json.loads(a.desglose_json) if a.desglose_json else None,
            "actualizado": a.actualizado.strftime("%d/%m/%Y") if a.actualizado else ""}


def _mio(apu_id: int, user: Usuario, db: Session) -> ApuUsuario:
    a = db.query(ApuUsuario).filter(ApuUsuario.id == apu_id,
                                    ApuUsuario.user_id == user.id).first()
    if not a:
        raise HTTPException(404, "APU no encontrado")
    return a


class ApuRequest(BaseModel):
    codigo: str = ""
    descripcion: str
    unidad: str = "un"
    precio: int = 0
    sector_tag: str = "ambos"
    region: str = ""


class ComponerRequest(BaseModel):
    insumos: List[Dict] = []
    mano_obra: int = 0
    herramienta_pct: float = 0
    transporte: int = 0


@router.get("")
def listar(q: Optional[str] = Query(None), sector: Optional[str] = Query(None),
           user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    qs = db.query(ApuUsuario).filter(ApuUsuario.user_id == user.id)
    if q:
        qs = qs.filter(ApuUsuario.descripcion.ilike(f"%{q.strip()[:80]}%"))
    if sector in ("privado", "publico"):
        qs = qs.filter(ApuUsuario.sector_tag.in_((sector, "ambos")))
    items = qs.order_by(ApuUsuario.actualizado.desc()).limit(200).all()
    return {"items": [_out(a) for a in items], "total": qs.count()}


@router.post("")
def crear(req: ApuRequest, user: Usuario = Depends(usuario_actual),
          db: Session = Depends(get_db)):
    if db.query(ApuUsuario).filter(ApuUsuario.user_id == user.id).count() >= MAX_APUS:
        raise HTTPException(400, f"Limite de {MAX_APUS} APUs propios alcanzado")
    desc = (req.descripcion or "").strip()
    if len(desc) < 3:
        raise HTTPException(400, "Describe la actividad (minimo 3 caracteres)")
    if req.precio < 0 or req.precio > 2_000_000_000:
        raise HTTPException(400, "Precio fuera de rango")
    if req.sector_tag not in SECTORES:
        raise HTTPException(400, "Sector no valido")
    a = ApuUsuario(user_id=user.id, codigo=(req.codigo or "").strip()[:30],
                   descripcion=desc[:300], unidad=(req.unidad or "un")[:15],
                   precio=req.precio, sector_tag=req.sector_tag,
                   region=(req.region or "")[:30])
    db.add(a); db.commit(); db.refresh(a)
    return _out(a)


@router.post("/duplicar-de-base")
def duplicar_de_base(codigo: str = Query(...), region: str = Query("bogota"),
                     user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """Clona un APU de la base 2026 a MI coleccion. La base jamas se toca."""
    from app.services.apu_service import get_precio
    base = get_precio(codigo, region)
    if not base:
        raise HTTPException(404, "Codigo no existe en la base 2026")
    if db.query(ApuUsuario).filter(ApuUsuario.user_id == user.id).count() >= MAX_APUS:
        raise HTTPException(400, f"Limite de {MAX_APUS} APUs propios alcanzado")
    a = ApuUsuario(user_id=user.id, codigo=f"MI-{base['codigo']}"[:30],
                   descripcion=base["descripcion"][:300], unidad=base["unidad"][:15],
                   precio=int(base["precio"]), sector_tag="ambos",
                   region=region[:30], origen_base=base["codigo"][:30])
    db.add(a); db.commit(); db.refresh(a)
    return _out(a)


@router.post("/componer")
def componer(req: ComponerRequest, user: Usuario = Depends(usuario_actual)):
    """Vista previa del constructor: insumos + MO + herramienta -> precio compuesto."""
    if len(req.insumos) > 40:
        raise HTTPException(400, "Maximo 40 insumos por APU")
    try:
        return componer_precio(req.insumos, req.mano_obra, req.herramienta_pct, req.transporte)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/{apu_id}")
def actualizar(apu_id: int, req: ApuRequest,
               user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    a = _mio(apu_id, user, db)
    desc = (req.descripcion or "").strip()
    if len(desc) < 3:
        raise HTTPException(400, "Describe la actividad")
    if req.precio < 0 or req.precio > 2_000_000_000:
        raise HTTPException(400, "Precio fuera de rango")
    if req.sector_tag not in SECTORES:
        raise HTTPException(400, "Sector no valido")
    a.codigo = (req.codigo or "").strip()[:30]
    a.descripcion = desc[:300]
    a.unidad = (req.unidad or "un")[:15]
    a.precio = req.precio
    a.sector_tag = req.sector_tag
    a.region = (req.region or "")[:30]
    db.commit(); db.refresh(a)
    return _out(a)


@router.put("/{apu_id}/desglose")
def guardar_desglose(apu_id: int, req: ComponerRequest,
                     user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """Guarda la composicion del constructor y fija el precio compuesto."""
    a = _mio(apu_id, user, db)
    if len(req.insumos) > 40:
        raise HTTPException(400, "Maximo 40 insumos por APU")
    try:
        r = componer_precio(req.insumos, req.mano_obra, req.herramienta_pct, req.transporte)
    except ValueError as e:
        raise HTTPException(400, str(e))
    a.desglose_json = json.dumps(r, ensure_ascii=False)
    a.precio = r["precio_unitario"]
    db.commit(); db.refresh(a)
    return _out(a)


@router.delete("/{apu_id}")
def eliminar(apu_id: int, user: Usuario = Depends(usuario_actual),
             db: Session = Depends(get_db)):
    a = _mio(apu_id, user, db)
    db.delete(a); db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════
# R1 — EL RECETARIO SEMILLA 🍳
# 16 APUs compuestos tipicos, listos para duplicar-y-ajustar. Convierte el
# constructor de examen en plantilla: el maestro no arranca desde cero.
# Idempotente por codigo (llamarlo dos veces no duplica) y el precio lo
# calcula SIEMPRE el servidor (componer_precio) — la misma fuente de verdad.
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/recetario")
def cargar_recetario(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    import os
    ruta = os.path.join(os.path.dirname(__file__), "..", "data", "recetario_semilla.json")
    with open(ruta, encoding="utf-8") as f:
        recetario = json.load(f)

    existentes = {a.codigo for a in db.query(ApuUsuario.codigo)
                  .filter(ApuUsuario.user_id == user.id).all()}
    total_actual = db.query(ApuUsuario).filter(ApuUsuario.user_id == user.id).count()

    creados, ya_existian = [], []
    for r in recetario.get("recetas", []):
        if r["codigo"] in existentes:
            ya_existian.append(r["codigo"])
            continue
        if total_actual + len(creados) >= MAX_APUS:
            break
        try:
            d = componer_precio(r.get("insumos", []), r.get("mano_obra", 0),
                                r.get("herramienta_pct", 0), r.get("transporte", 0))
        except ValueError:
            continue
        db.add(ApuUsuario(
            user_id=user.id, codigo=r["codigo"][:30],
            descripcion=r["descripcion"][:250], unidad=r["unidad"][:10],
            precio=d["precio_unitario"], sector_tag="ambos",
            origen_base="recetario", desglose_json=json.dumps(d, ensure_ascii=False),
        ))
        creados.append(r["codigo"])
    db.commit()
    logger.info(f"Recetario: {len(creados)} recetas sembradas para {user.email}")
    return {"creados": len(creados), "ya_existian": len(ya_existian),
            "codigos": creados, "version": recetario.get("version", "1.0")}
