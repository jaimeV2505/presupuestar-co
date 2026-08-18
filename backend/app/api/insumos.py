# -*- coding: utf-8 -*-
"""BUSCADOR DE INSUMOS MULTI-FUENTE — alimenta el constructor de APUs.
Mezcla: MIS proveedores (mis precios negociados, primero) + base curada de
referencia (+ fuentes externas cuando existan). Cada precio viaja con su
fuente y su fecha — jamas como verdad absoluta."""
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proveedor, PrecioProveedor
from app.api.auth import usuario_actual
from app.services.fuentes_precios import fuente_curada, fuente_externa

router = APIRouter()


def _buscar_nucleo(q: str, user: Usuario, db: Session):
    """Buscador multi-fuente: MIS proveedores > referencia curada > externas."""
    q = q.strip()[:80]
    if len(q) < 2:
        raise HTTPException(400, "Escribe al menos 2 letras")

    # 1. MIS proveedores primero (mis precios negociados > cualquier referencia)
    mios = (db.query(PrecioProveedor, Proveedor)
            .join(Proveedor, Proveedor.id == PrecioProveedor.proveedor_id)
            .filter(PrecioProveedor.user_id == user.id,
                    PrecioProveedor.insumo.ilike(f"%{q}%"))
            .limit(10).all())
    resultados = [{
        "fuente": "mi_proveedor", "nombre": pp.insumo, "unidad": pp.unidad,
        "precio": pp.precio,
        "fecha": pp.capturado.strftime("%d/%m/%Y") if pp.capturado else "",
        "edad_dias": (datetime.now(timezone.utc).replace(tzinfo=None) - pp.capturado.replace(tzinfo=None)).days if pp.capturado else None,
        "precio_viejo": bool(pp.capturado and (datetime.now(timezone.utc).replace(tzinfo=None) - pp.capturado.replace(tzinfo=None)).days > 180),
        "detalle": prov.nombre,
    } for pp, prov in mios]

    # 2. Referencia curada + 3. externas (enchufables, degradan a vacio)
    resultados += fuente_curada(q, limit=10)
    resultados += fuente_externa(q, limit=6)
    return {"q": q, "resultados": resultados[:24]}


@router.get("/buscar")
def buscar(q: str = Query(..., min_length=2), user: Usuario = Depends(usuario_actual),
           db: Session = Depends(get_db)):
    """El buscador (handler delgado — la logica vive en el nucleo compartido)."""
    return _buscar_nucleo(q, user, db)


@router.get("/comparar")
def comparar(q: str = Query(..., min_length=2), user: Usuario = Depends(usuario_actual),
             db: Session = Depends(get_db)):
    """El comparador: mi mejor precio vs la referencia — cuanto me ahorro."""
    data = _buscar_nucleo(q, user, db)
    mios = [r for r in data["resultados"] if r["fuente"] == "mi_proveedor"]
    refs = [r for r in data["resultados"] if r["fuente"] == "referencia"]
    mejor_mio = min(mios, key=lambda r: r["precio"]) if mios else None
    ref = min(refs, key=lambda r: r["precio"]) if refs else None
    ahorro = (ref["precio"] - mejor_mio["precio"]) if (mejor_mio and ref) else None
    return {"q": data["q"], "mi_mejor": mejor_mio, "referencia": ref, "ahorro": ahorro}


@router.get("/catalogo")
def catalogo(categoria: str = "", user: Usuario = Depends(usuario_actual)):
    """El catalogo curado navegable: categorias con conteo, o los insumos de una categoria."""
    from app.services.fuentes_precios import _cargar_curada
    data = _cargar_curada()
    if not categoria:
        cats = {}
        for i in data["insumos"]:
            cats[i["categoria"]] = cats.get(i["categoria"], 0) + 1
        return {"version": data["version"], "nota": data.get("nota", ""),
                "total": len(data["insumos"]),
                "categorias": [{"nombre": k, "n": v} for k, v in sorted(cats.items())]}
    items = [i for i in data["insumos"] if i["categoria"] == categoria.strip()[:40]][:60]
    return {"categoria": categoria, "insumos": items, "version": data["version"]}
