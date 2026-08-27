# -*- coding: utf-8 -*-
"""
Clientes — el mini-CRM del contratista.

Cada cliente es una entidad: sus proyectos, cuanto ha contratado, cuanto
ha pagado y como te ha calificado. El vinculo se crea automaticamente al
crear/editar un proyecto (find-or-create por nombre).
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto, Cliente, CuentaCobro, Encuesta
from app.api.auth import usuario_actual
from app.services.calculo_presupuesto import calcular_totales

logger = logging.getLogger(__name__)
router = APIRouter()

GANADOS = ("aceptado", "entrega_solicitada", "terminado")


def vincular_cliente(p: Proyecto, user_id: int, db: Session):
    """Find-or-create del cliente por nombre y amarre al proyecto. Nunca rompe el flujo."""
    try:
        nombre = (p.cliente_nombre or "").strip()
        if not nombre:
            p.cliente_id = None
            return
        c = (db.query(Cliente)
             .filter(Cliente.user_id == user_id, Cliente.nombre.ilike(nombre))
             .first())
        if not c:
            c = Cliente(user_id=user_id, nombre=nombre,
                        telefono=(p.cliente_telefono or "").strip()[:30])
            db.add(c)
            db.flush()
        elif p.cliente_telefono and not c.telefono:
            c.telefono = p.cliente_telefono.strip()[:30]
        p.cliente_id = c.id
    except Exception as e:
        logger.warning(f"vincular_cliente: {e}")


@router.get("")
def listar(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    clientes = (db.query(Cliente).filter(Cliente.user_id == user.id)
                .order_by(Cliente.creado.desc()).limit(300).all())
    proyectos = (db.query(Proyecto)
                 .filter(Proyecto.user_id == user.id, Proyecto.es_demo == False)  # noqa: E712
                 .all())
    por_cliente = {}
    for p in proyectos:
        if p.cliente_id:
            por_cliente.setdefault(p.cliente_id, []).append(p)

    cuentas = db.query(CuentaCobro).filter(CuentaCobro.user_id == user.id).all()
    pagado_por_proyecto = {}
    for c in cuentas:
        if c.estado == "pagada":
            pagado_por_proyecto[c.proyecto_id] = pagado_por_proyecto.get(c.proyecto_id, 0) + c.neto

    encuestas = (db.query(Encuesta, Proyecto.cliente_id)
                 .join(Proyecto, Proyecto.id == Encuesta.proyecto_id)
                 .filter(Proyecto.user_id == user.id).all())
    stars_por_cliente = {}
    for e, cid in encuestas:
        if cid:
            stars_por_cliente.setdefault(cid, []).append(e.estrellas)

    # adicionales aprobados por proyecto — UNA sola query (anti N+1), mismo
    # patron que metricas() en proyectos.py
    from app.db import Otrosi
    ids_proyectos = [p.id for p in proyectos]
    adicionales_por_proyecto = {}
    if ids_proyectos:
        for o in db.query(Otrosi).filter(Otrosi.proyecto_id.in_(ids_proyectos),
                                         Otrosi.estado == "aprobado").all():
            t = json.loads(o.totales_json or "{}")
            adicionales_por_proyecto[o.proyecto_id] = adicionales_por_proyecto.get(o.proyecto_id, 0) + int(t.get("total") or 0)

    out = []
    for c in clientes:
        ps = por_cliente.get(c.id, [])
        total_contratado = 0
        for p in ps:
            if p.estado in GANADOS:
                items = json.loads(p.items_json or "[]")
                aiu = json.loads(p.aiu_json or "{}")
                # base + adicionales aprobados — mismo criterio que metricas() en proyectos.py,
                # si no, el total contratado del cliente queda subestimado cuando hay otrosies
                total_contratado += calcular_totales(items, aiu)["total"] + adicionales_por_proyecto.get(p.id, 0)
        pagado = sum(pagado_por_proyecto.get(p.id, 0) for p in ps)
        stars = stars_por_cliente.get(c.id, [])
        out.append({
            "id": c.id, "nombre": c.nombre, "telefono": c.telefono,
            "n_proyectos": len(ps),
            "n_terminados": sum(1 for p in ps if p.estado == "terminado"),
            "total_contratado": total_contratado,
            "pagado": pagado,
            "calificacion": round(sum(stars) / len(stars), 1) if stars else None,
            "proyectos": [
                {"id": p.id, "numero": p.numero, "nombre": p.nombre, "estado": p.estado}
                for p in sorted(ps, key=lambda x: x.id, reverse=True)[:10]
            ],
        })
    return out
