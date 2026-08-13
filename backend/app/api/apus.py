# -*- coding: utf-8 -*-
"""MIS APUs — la coleccion personal del usuario.
Regla sagrada: la base 2026 es INMUTABLE (vigilada por hash en el CI);
aqui vive lo propio: manual, duplicado de la base, o compuesto por insumos."""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict
from app.db import get_db, Usuario, ApuUsuario
from app.api.auth import usuario_actual
from app.services.apu_propio_service import componer_precio

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
        return componer_precio(req.insumos, req.mano_obra, req.herramienta_pct)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/{apu_id}")
def actualizar(apu_id: int, req: ApuRequest, componer_req: Optional[ComponerRequest] = None,
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
        r = componer_precio(req.insumos, req.mano_obra, req.herramienta_pct)
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
