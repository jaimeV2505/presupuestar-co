# -*- coding: utf-8 -*-
"""MIS PROVEEDORES — la ferreteria del contratista y sus precios negociados,
cada precio con su fecha de captura (honestidad de frescura)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db import get_db, Usuario, Proveedor, PrecioProveedor
from app.api.auth import usuario_actual

router = APIRouter()
MAX_PROVEEDORES = 50
MAX_PRECIOS = 300   # por proveedor


def _prov_out(p: Proveedor, n_precios: int = 0) -> dict:
    return {"id": p.id, "nombre": p.nombre, "categoria": p.categoria,
            "ciudad": p.ciudad, "telefono": p.telefono, "notas": p.notas,
            "n_precios": n_precios}


def _mio(pid: int, user: Usuario, db: Session) -> Proveedor:
    p = db.query(Proveedor).filter(Proveedor.id == pid,
                                   Proveedor.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proveedor no encontrado")
    return p


class ProveedorRequest(BaseModel):
    nombre: str
    categoria: str = "ferreteria"
    ciudad: str = ""
    telefono: str = ""
    notas: str = ""


class PrecioRequest(BaseModel):
    insumo: str
    unidad: str = "un"
    precio: int


@router.get("")
def listar(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    provs = (db.query(Proveedor).filter(Proveedor.user_id == user.id)
             .order_by(Proveedor.nombre).all())
    conteos = {p.id: db.query(PrecioProveedor).filter(PrecioProveedor.proveedor_id == p.id).count()
               for p in provs}
    return {"proveedores": [_prov_out(p, conteos[p.id]) for p in provs]}


@router.post("")
def crear(req: ProveedorRequest, user: Usuario = Depends(usuario_actual),
          db: Session = Depends(get_db)):
    if db.query(Proveedor).filter(Proveedor.user_id == user.id).count() >= MAX_PROVEEDORES:
        raise HTTPException(400, f"Limite de {MAX_PROVEEDORES} proveedores")
    nombre = (req.nombre or "").strip()
    if len(nombre) < 2:
        raise HTTPException(400, "Nombre del proveedor requerido")
    p = Proveedor(user_id=user.id, nombre=nombre[:120],
                  categoria=(req.categoria or "ferreteria")[:40],
                  ciudad=(req.ciudad or "")[:60],
                  telefono=(req.telefono or "").strip()[:20],
                  notas=(req.notas or "")[:300])
    db.add(p); db.commit(); db.refresh(p)
    return _prov_out(p)


@router.delete("/{pid}")
def eliminar(pid: int, user: Usuario = Depends(usuario_actual),
             db: Session = Depends(get_db)):
    p = _mio(pid, user, db)
    db.query(PrecioProveedor).filter(PrecioProveedor.proveedor_id == p.id).delete()
    db.delete(p); db.commit()
    return {"ok": True}


@router.get("/{pid}/precios")
def precios(pid: int, user: Usuario = Depends(usuario_actual),
            db: Session = Depends(get_db)):
    p = _mio(pid, user, db)
    rows = (db.query(PrecioProveedor).filter(PrecioProveedor.proveedor_id == p.id)
            .order_by(PrecioProveedor.insumo).all())
    return {"precios": [{"id": r.id, "insumo": r.insumo, "unidad": r.unidad,
                         "precio": r.precio,
                         "capturado": r.capturado.strftime("%d/%m/%Y") if r.capturado else ""}
                        for r in rows]}


@router.post("/{pid}/precios")
def agregar_precio(pid: int, req: PrecioRequest,
                   user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _mio(pid, user, db)
    if db.query(PrecioProveedor).filter(PrecioProveedor.proveedor_id == p.id).count() >= MAX_PRECIOS:
        raise HTTPException(400, f"Limite de {MAX_PRECIOS} precios por proveedor")
    insumo = (req.insumo or "").strip()
    if len(insumo) < 2:
        raise HTTPException(400, "Nombre del insumo requerido")
    if req.precio < 0 or req.precio > 500_000_000:
        raise HTTPException(400, "Precio fuera de rango")
    r = PrecioProveedor(proveedor_id=p.id, user_id=user.id, insumo=insumo[:160],
                        unidad=(req.unidad or "un")[:15], precio=req.precio)
    db.add(r); db.commit(); db.refresh(r)
    return {"id": r.id, "ok": True}


@router.delete("/precios/{precio_id}")
def eliminar_precio(precio_id: int, user: Usuario = Depends(usuario_actual),
                    db: Session = Depends(get_db)):
    r = db.query(PrecioProveedor).filter(PrecioProveedor.id == precio_id,
                                         PrecioProveedor.user_id == user.id).first()
    if not r:
        raise HTTPException(404, "Precio no encontrado")
    db.delete(r); db.commit()
    return {"ok": True}
