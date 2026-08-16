# -*- coding: utf-8 -*-
"""Proyectos: CRUD + items del presupuesto + limites por plan."""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto, EventoShare
from app.api.auth import usuario_actual
from app.services.calculo_presupuesto import calcular_totales, validar_items

logger = logging.getLogger(__name__)
router = APIRouter()

LIMITE_GRATIS = 3  # presupuestos por mes en plan gratis


def _mes_actual() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _verificar_limite(user: Usuario, db: Session):
    """Plan gratis: limite de 3 presupuestos al mes. Pro: ilimitado."""
    if user.plan != "gratis":
        return
    mes = _mes_actual()
    if user.mes_actual != mes:
        user.mes_actual = mes
        user.presupuestos_mes = 0
        db.commit()
    if user.presupuestos_mes >= LIMITE_GRATIS:
        raise HTTPException(
            402,
            f"Plan gratis: limite de {LIMITE_GRATIS} presupuestos/mes alcanzado. "
            f"Pasa a Pro para presupuestos ilimitados."
        )


def _generar_numero(user_id: int, db: Session) -> str:
    """Numero de cotizacion secuencial por usuario: COT-2026-0001"""
    year = datetime.now(timezone.utc).year
    total = (db.query(Proyecto)
             .filter(Proyecto.user_id == user_id, Proyecto.es_demo == False)  # noqa: E712
             .count())
    return f"COT-{year}-{total + 1:04d}"


def _proyecto_out(p: Proyecto, incluir_items: bool = False, db=None) -> Dict:
    items = json.loads(p.items_json or "[]")
    aiu = json.loads(p.aiu_json or "{}")
    out = {
        "id": p.id,
        "numero": p.numero or f"COT-{p.id:04d}",
        "es_demo": bool(getattr(p, "es_demo", False)),
        "nombre": p.nombre,
        "cliente_nombre": p.cliente_nombre,
        "cliente_telefono": p.cliente_telefono,
        "direccion": p.direccion,
        "region": p.region,
        "estado": p.estado,
        "num_items": len(items),
        "aiu": aiu,
        "contrato": json.loads(p.contrato_json or "{}"),
        "totales": calcular_totales(items, aiu),
        "share_token": p.share_token,
        "pendientes_reportados": ([
            {"detalle": e.detalle, "fecha": e.creado.strftime("%d/%m/%Y %H:%M") if e.creado else ""}
            for e in db.query(EventoShare)
                       .filter(EventoShare.proyecto_id == p.id,
                               EventoShare.tipo == "pendientes")
                       .order_by(EventoShare.creado.desc()).limit(10).all()
        ] if db is not None else []),
        "sector": p.sector or "privado",
        "entidad_nombre": p.entidad_nombre or "",
        "contrato_numero": p.contrato_numero or "",
        "supervisor_nombre": p.supervisor_nombre or "",
        "notas": p.notas,
        "creado": p.creado.isoformat() if p.creado else None,
        "actualizado": p.actualizado.isoformat() if p.actualizado else None,
    }
    if incluir_items:
        out["items"] = items
    return out


class ProyectoCreate(BaseModel):
    nombre: str
    cliente_nombre: str = ""
    cliente_telefono: str = ""
    direccion: str = ""
    region: str = "bogota"
    sector: str = "privado"
    entidad_nombre: str = ""
    contrato_numero: str = ""
    supervisor_nombre: str = ""



class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    sector: Optional[str] = None
    entidad_nombre: Optional[str] = None
    contrato_numero: Optional[str] = None
    supervisor_nombre: Optional[str] = None
    cliente_nombre: Optional[str] = None
    cliente_telefono: Optional[str] = None
    direccion: Optional[str] = None
    region: Optional[str] = None
    estado: Optional[str] = None
    notas: Optional[str] = None
    items: Optional[List[Dict]] = None
    aiu: Optional[Dict] = None
    contrato: Optional[Dict] = None


@router.get("/metricas")
def metricas(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """Metricas del negocio del contratista — calculadas de sus presupuestos."""
    from app.db import Encuesta
    proyectos = (db.query(Proyecto)
                 .filter(Proyecto.user_id == user.id, Proyecto.es_demo == False)  # noqa: E712
                 .all())

    GANADOS = ("aceptado", "entrega_solicitada", "terminado")
    ENVIADOS = ("enviado", "visto", "aceptado", "rechazado", "entrega_solicitada", "terminado")

    total_cotizado = 0
    total_ganado = 0
    utilidad_proyectada = 0
    en_ejecucion_valor = 0
    en_ejecucion_n = 0
    n_enviados = 0
    n_ganados = 0

    for p in proyectos:
        items = json.loads(p.items_json or "[]")
        aiu = json.loads(p.aiu_json or "{}")
        t = calcular_totales(items, aiu)
        total_cotizado += t["total"]
        if p.estado in ENVIADOS:
            n_enviados += 1
        if p.estado in GANADOS:
            n_ganados += 1
            total_ganado += t["total"]
            utilidad_proyectada += t["utilidad_valor"]
        if p.estado in ("aceptado", "entrega_solicitada"):
            en_ejecucion_valor += t["total"]
            en_ejecucion_n += 1

    from app.db import CuentaCobro, Gasto
    ccs = db.query(CuentaCobro).filter(CuentaCobro.user_id == user.id).all()
    cobrado = sum(c.neto for c in ccs if c.estado == "pagada")
    por_cobrar = sum(c.neto for c in ccs if c.estado == "enviada")
    ids_proyectos = [p.id for p in proyectos]
    gastado_total = sum(
        g.valor for g in db.query(Gasto).filter(Gasto.proyecto_id.in_(ids_proyectos)).all()
    ) if ids_proyectos else 0

    encs = (db.query(Encuesta).join(Proyecto, Proyecto.id == Encuesta.proyecto_id)
            .filter(Proyecto.user_id == user.id).all())
    calificacion = round(sum(e.estrellas for e in encs) / len(encs), 1) if encs else None

    return {
        "total_cotizado": total_cotizado,
        "total_ganado": total_ganado,
        "utilidad_proyectada": utilidad_proyectada,
        "en_ejecucion_valor": en_ejecucion_valor,
        "en_ejecucion_n": en_ejecucion_n,
        "tasa_cierre": round(n_ganados / n_enviados * 100) if n_enviados else 0,
        "n_presupuestos": len(proyectos),
        "n_ganados": n_ganados,
        "n_terminados": sum(1 for p in proyectos if p.estado == "terminado"),
        "calificacion": calificacion,
        "n_resenas": len(encs),
        "cobrado": cobrado,
        "por_cobrar": por_cobrar,
        "gastado": gastado_total,
        "caja_neta": cobrado - gastado_total,
    }


@router.get("")
def listar(user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    proyectos = (
        db.query(Proyecto)
        .filter(Proyecto.user_id == user.id)
        .order_by(Proyecto.actualizado.desc())
        .limit(200).all()
    )
    # adicionales aprobados por proyecto (una sola query, sin N+1)
    from app.db import Otrosi
    ids = [p.id for p in proyectos]
    adicionales = {}
    if ids:
        for o in db.query(Otrosi).filter(Otrosi.proyecto_id.in_(ids),
                                         Otrosi.estado == "aprobado").all():
            try:
                t = json.loads(o.totales_json or "{}").get("total") or 0
            except ValueError:
                t = 0
            adicionales[o.proyecto_id] = adicionales.get(o.proyecto_id, 0) + t
    out = []
    for p in proyectos:
        d = _proyecto_out(p)
        d["total_adicionales"] = adicionales.get(p.id, 0)
        d["sector"] = p.sector or "privado"
        out.append(d)
    return out


def _esta_firmado(p) -> bool:
    return p.estado not in ("borrador", "enviado", "visto", "rechazado")


@router.post("")
def crear(req: ProyectoCreate, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    _verificar_limite(user, db)
    if not req.nombre.strip():
        raise HTTPException(400, "El proyecto necesita un nombre")
    if req.sector not in ("privado", "publico"):
        raise HTTPException(400, "Sector no valido")
    if req.sector == "publico":
        if not (req.entidad_nombre or "").strip():
            raise HTTPException(400, "Un contrato de obra publica necesita la entidad contratante")
        if not (req.contrato_numero or "").strip():
            raise HTTPException(400, "Un contrato de obra publica necesita el numero de contrato")
    p = Proyecto(
        user_id=user.id,
        numero=_generar_numero(user.id, db),
        nombre=req.nombre.strip()[:200],
        sector=req.sector,
        entidad_nombre=(req.entidad_nombre or "").strip()[:200],
        contrato_numero=(req.contrato_numero or "").strip()[:60],
        supervisor_nombre=(req.supervisor_nombre or "").strip()[:120],
        cliente_nombre=req.cliente_nombre.strip()[:160],
        cliente_telefono=req.cliente_telefono.strip()[:30],
        direccion=req.direccion.strip()[:250],
        region=req.region,
    )
    db.add(p)
    from app.api.clientes import vincular_cliente
    vincular_cliente(p, user.id, db)
    if user.plan == "gratis":
        user.presupuestos_mes += 1
    db.commit()
    db.refresh(p)
    logger.info(f"Proyecto creado: {p.id} por user {user.id}")
    return _proyecto_out(p, incluir_items=True, db=db)


@router.get("/plantillas")
def listar_plantillas(user: Usuario = Depends(usuario_actual)):
    return [
        {"id": k, "nombre": v["nombre"], "emoji": v["emoji"],
         "descripcion": v["descripcion"], "n_items": len(v["items"])}
        for k, v in PLANTILLAS.items()
    ]


class DesdePlantillaRequest(BaseModel):
    plantilla_id: str
    nombre: str = ""


@router.post("/desde-plantilla")
def crear_desde_plantilla(req: DesdePlantillaRequest,
                          user: Usuario = Depends(usuario_actual),
                          db: Session = Depends(get_db)):
    tpl = PLANTILLAS.get(req.plantilla_id)
    if not tpl:
        raise HTTPException(404, "Plantilla no encontrada")
    _verificar_limite(user, db)

    from app.services import apu_service as APU
    from app.services.apu_service import FACTORES_REGION
    import uuid as _uuid
    apu_db = APU.load_apu_db()
    factor = FACTORES_REGION.get(user.ciudad, FACTORES_REGION["bogota"])["factor"]

    items = []
    for palabras, cantidad in tpl["items"]:
        m = _buscar_apu(palabras, apu_db, factor)
        if m:
            items.append({
                "id": _uuid.uuid4().hex[:10],
                "capitulo": m.get("categoria", "GENERAL"),
                "descripcion": m["descripcion"],
                "unidad": m.get("unidad", "un"),
                "cantidad": cantidad,
                "precio_unitario": m["precio"],
            })

    if not items:
        raise HTTPException(500, "No se encontraron actividades para la plantilla")

    p = Proyecto(
        user_id=user.id,
        nombre=(req.nombre or tpl["nombre"]).strip()[:150],
        numero=_generar_numero(user.id, db),
        items_json=json.dumps(items, ensure_ascii=False),
        aiu_json=json.dumps({"admin": 15, "imprevistos": 5, "utilidad": 8,
                             "aplicar": True, "iva_sobre_utilidad": True}),
        region=user.ciudad,
    )
    db.add(p)
    from app.api.clientes import vincular_cliente
    vincular_cliente(p, user.id, db)
    db.commit()
    db.refresh(p)
    logger.info(f"Proyecto desde plantilla '{req.plantilla_id}': {len(items)} items para {user.email}")
    return _proyecto_out(p)


@router.get("/{proyecto_id}")
def obtener(proyecto_id: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    return _proyecto_out(p, incluir_items=True, db=db)


@router.put("/{proyecto_id}")
def actualizar(proyecto_id: int, req: ProyectoUpdate, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")

    if req.sector is not None and req.sector != p.sector:
        if _esta_firmado(p):
            raise HTTPException(400, "El sector no se cambia despues de la firma del contrato")
        if req.sector not in ("privado", "publico"):
            raise HTTPException(400, "Sector no valido")
        p.sector = req.sector
        if req.sector == "publico":
            # Doctrina «nada viaja fuera»: al convertir a publico, el enlace legado muere de raiz
            p.share_token = None
    if req.entidad_nombre is not None:
        p.entidad_nombre = req.entidad_nombre.strip()[:200]
    if req.contrato_numero is not None:
        p.contrato_numero = req.contrato_numero.strip()[:60]
    if req.supervisor_nombre is not None:
        p.supervisor_nombre = req.supervisor_nombre.strip()[:120]
    if req.nombre is not None: p.nombre = req.nombre.strip()[:200]
    if req.cliente_nombre is not None:
        p.cliente_nombre = req.cliente_nombre.strip()[:160]
        from app.api.clientes import vincular_cliente
        vincular_cliente(p, user.id, db)
    if req.cliente_telefono is not None: p.cliente_telefono = req.cliente_telefono.strip()[:30]
    if req.direccion is not None: p.direccion = req.direccion.strip()[:250]
    if req.region is not None: p.region = req.region
    # ── Maquina de estados: el sello no se degrada ─────────────────────────
    # Doctrina: firmado/sellado = irreversible. Los cambios post-sello van por
    # adicionales, jamas por "devolver el estado y editar". Guardian del bypass
    # aceptado -> borrador -> editar items -> aceptado.
    _ORDEN = {"borrador": 0, "enviado": 1, "visto": 1, "rechazado": 1,
              "aceptado": 2, "entrega_solicitada": 3, "terminado": 4}
    _SOLO_PRIVADO = ("enviado", "visto", "rechazado", "entrega_solicitada")
    if req.estado in _ORDEN and req.estado != p.estado:
        if p.estado == "terminado":
            raise HTTPException(400, "La obra ya fue entregada y liquidada — el estado es final")
        if (p.sector or "privado") == "publico" and req.estado in _SOLO_PRIVADO:
            raise HTTPException(400, "Ese estado pertenece al enlace de cliente — no existe en obra publica")
        if _ORDEN.get(p.estado, 0) >= _ORDEN["aceptado"] and _ORDEN[req.estado] < _ORDEN[p.estado]:
            raise HTTPException(400, "El presupuesto esta sellado — no se retrocede el estado; "
                                     "los cambios entran por adicionales")
        p.estado = req.estado
    if req.notas is not None: p.notas = req.notas[:2000]

    if req.items is not None:
        if p.estado in ("aceptado", "entrega_solicitada", "terminado"):
            raise HTTPException(400, "Este presupuesto ya fue firmado — para cambios, duplica el proyecto")
        items_validos = validar_items(req.items)
        p.items_json = json.dumps(items_validos, ensure_ascii=False)

    if req.contrato is not None:
        c = req.contrato
        cfg = {
            "plazo_dias": max(1, min(720, int(c.get("plazo_dias") or 45))),
            "anticipo_pct": max(0, min(90, float(c.get("anticipo_pct") or 50))),
            "retegarantia_pct": max(0, min(20, float(c.get("retegarantia_pct") or 0))),
            "fecha_inicio": str(c.get("fecha_inicio") or "")[:60],
            "lugar": str(c.get("lugar") or "")[:150],
        }
        if c.get("deducciones") is not None:
            from app.services.deducciones_service import validar_deducciones
            try:
                cfg["deducciones"] = validar_deducciones(c.get("deducciones"))
            except ValueError as e:
                raise HTTPException(400, str(e))
        p.contrato_json = json.dumps(cfg, ensure_ascii=False)

    if req.aiu is not None:
        if p.estado == "aceptado":
            raise HTTPException(400, "Este presupuesto ya fue firmado — para cambios, duplica el proyecto")
        aiu_limpio = {
            "admin": max(0, min(50, float(req.aiu.get("admin", 15) or 0))),
            "imprevistos": max(0, min(30, float(req.aiu.get("imprevistos", 5) or 0))),
            "utilidad": max(0, min(50, float(req.aiu.get("utilidad", 8) or 0))),
            "aplicar": bool(req.aiu.get("aplicar", True)),
            "iva_sobre_utilidad": bool(req.aiu.get("iva_sobre_utilidad", True)),
        }
        p.aiu_json = json.dumps(aiu_limpio)

    db.commit()
    db.refresh(p)
    return _proyecto_out(p, incluir_items=True, db=db)


@router.delete("/{proyecto_id}")
def eliminar(proyecto_id: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    # CASCADA COMPLETA en orden de dependencias (Postgres exige el orden; sqlite lo agradece)
    from app.db import (Abono, CuentaCobro, InteraccionCliente, Encuesta,
                        Gasto, Otrosi, Avance, Notificacion)
    ids_cuentas = [c_.id for c_ in db.query(CuentaCobro.id).filter(CuentaCobro.proyecto_id == p.id).all()]
    if ids_cuentas:
        db.query(Abono).filter(Abono.cuenta_id.in_(ids_cuentas)).delete(synchronize_session=False)
    for Modelo in (InteraccionCliente, EventoShare, Encuesta, Gasto, Otrosi, Avance, CuentaCobro, Notificacion):
        db.query(Modelo).filter(Modelo.proyecto_id == p.id).delete(synchronize_session=False)
    db.delete(p)
    db.commit()
    return {"ok": True}


@router.post("/{proyecto_id}/terminar")
def terminar(proyecto_id: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """OBRA PUBLICA — Terminar y liquidar en un clic: estado terminado.
    (La retegarantia se libera aparte con POST /cuentas/proyectos/{id}/retegarantia.)
    En privado el cierre lo da el ACTA BILATERAL del cliente, no este boton."""
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    if (p.sector or "privado") != "publico":
        raise HTTPException(400, "En obra privada la entrega la confirma el cliente (acta bilateral)")
    if p.estado == "terminado":
        raise HTTPException(400, "Este contrato ya fue terminado y liquidado")
    if p.estado != "aceptado":
        raise HTTPException(400, "El contrato aun no esta en ejecucion — el primer avance sella el presupuesto oficial")
    p.estado = "terminado"
    db.commit()
    db.refresh(p)
    logger.info(f"Contrato publico terminado: {p.numero} por {user.email}")
    return _proyecto_out(p, incluir_items=False, db=db)


@router.post("/{proyecto_id}/duplicar")
def duplicar(proyecto_id: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    _verificar_limite(user, db)
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    nuevo = Proyecto(
        user_id=user.id,
        numero=_generar_numero(user.id, db),
        nombre=f"{p.nombre} (copia)",
        sector=p.sector or "privado",
        entidad_nombre=p.entidad_nombre or "",
        contrato_numero=p.contrato_numero or "",
        supervisor_nombre=p.supervisor_nombre or "",
        cliente_nombre=p.cliente_nombre,
        cliente_telefono=p.cliente_telefono,
        direccion=p.direccion,
        region=p.region,
        items_json=p.items_json,
        aiu_json=p.aiu_json,
        contrato_json=p.contrato_json,   # anticipo, rete, plazo y deducciones viajan con la copia
        notas=p.notas,
    )
    db.add(nuevo)
    from app.api.clientes import vincular_cliente
    vincular_cliente(nuevo, user.id, db)
    if user.plan == "gratis":
        user.presupuestos_mes += 1
    db.commit()
    db.refresh(nuevo)
    return _proyecto_out(nuevo, incluir_items=True)


# ── PLANTILLAS DE PRESUPUESTO ────────────────────────────────────────────────
# Cada item: (palabras clave para buscar en la base APU, cantidad tipica)
PLANTILLAS = {
    "bano": {
        "nombre": "Baño completo", "emoji": "🚿",
        "descripcion": "Demolición, enchape, aparatos y redes de un baño de ~4m²",
        "items": [
            (["demolicion", "enchape"], 12), (["alistado", "piso"], 4),
            (["impermeabilizacion"], 4), (["enchape", "pared", "ceramica"], 18),
            (["enchape", "piso", "ceramica"], 4), (["sanitario"], 1),
            (["lavamanos"], 1), (["ducha"], 1),
            (["punto", "hidraulico"], 4), (["punto", "sanitario"], 3),
            (["pintura", "vinilo"], 10),
        ],
    },
    "cocina": {
        "nombre": "Cocina integral", "emoji": "🍳",
        "descripcion": "Enchapes, mesón, redes y acabados de cocina de ~8m²",
        "items": [
            (["demolicion", "enchape"], 15), (["alistado", "piso"], 8),
            (["enchape", "pared", "ceramica"], 16), (["enchape", "piso"], 8),
            (["meson", "granito"], 3), (["lavaplatos"], 1),
            (["punto", "hidraulico"], 3), (["punto", "sanitario"], 2),
            (["punto", "electrico"], 6), (["pintura", "vinilo"], 20),
        ],
    },
    "cubierta": {
        "nombre": "Cubierta metálica", "emoji": "🏭",
        "descripcion": "Estructura y teja para cubierta de ~100m²",
        "items": [
            (["cercha", "metalica"], 100), (["correa"], 120),
            (["teja", "sandwich"], 100), (["canal", "aguas"], 24),
            (["bajante"], 12), (["anticorrosivo"], 100),
        ],
    },
    "casa60": {
        "nombre": "Casa básica 60m²", "emoji": "🏠",
        "descripcion": "Obra gris de vivienda de un piso: cimientos, muros, placa",
        "items": [
            (["localizacion", "replanteo"], 60), (["excavacion", "zapata"], 12),
            (["concreto", "zapata"], 6), (["viga", "cimiento"], 40),
            (["columna", "concreto"], 9), (["mamposteria", "ladrillo"], 140),
            (["viga", "amarre"], 40), (["placa", "concreto"], 60),
            (["panete", "muro"], 260), (["piso", "concreto"], 60),
        ],
    },
    "pintura": {
        "nombre": "Pintura apartamento", "emoji": "🎨",
        "descripcion": "Resane y pintura general de apartamento de ~70m²",
        "items": [
            (["resane", "muro"], 180), (["pintura", "vinilo", "muro"], 180),
            (["pintura", "cielo"], 70), (["esmalte", "puerta"], 6),
        ],
    },
    "placa": {
        "nombre": "Placa de entrepiso", "emoji": "🧱",
        "descripcion": "Placa aligerada de ~50m² con vigas y acero",
        "items": [
            (["placa", "aligerada"], 50), (["viga", "aerea"], 30),
            (["acero", "refuerzo"], 900), (["formaleta"], 50),
            (["concreto", "3000"], 8),
        ],
    },
}


def _buscar_apu(palabras, apu_db, factor):
    """Mejor coincidencia: item que contenga TODAS las palabras; fallback: la primera."""
    palabras = [w.lower() for w in palabras]
    mejor = None
    for it in apu_db:
        desc = it["descripcion"].lower()
        if all(w in desc for w in palabras):
            mejor = it
            break
    if not mejor:
        for it in apu_db:
            if palabras[0] in it["descripcion"].lower():
                mejor = it
                break
    if not mejor:
        return None
    return {**mejor, "precio": round(mejor["precio"] * factor)}


@router.get("/{proyecto_id}/balance")
def balance(proyecto_id: int, user: Usuario = Depends(usuario_actual),
            db: Session = Depends(get_db)):
    """BALANCE DE OBRA: oficial vs ejecutado — contrato + adicionales x avances x actas."""
    p = db.query(Proyecto).filter(Proyecto.id == proyecto_id,
                                  Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    from app.services.otrosi_service import items_efectivos
    from app.services.balance_service import balance_de_obra
    from app.db import Avance, CuentaCobro
    items = items_efectivos(p, db)
    # estado MAS RECIENTE por actividad: el maximo pct reportado
    pct_por_item = {}
    for a in db.query(Avance).filter(Avance.proyecto_id == p.id).all():
        for it in json.loads(a.items_json or "[]"):
            iid = str(it.get("id") or "")
            pct_por_item[iid] = max(pct_por_item.get(iid, 0), float(it.get("pct") or 0))
    cuentas = [{"total": c_.neto or 0, "pagada": c_.estado == "pagada"}
               for c_ in db.query(CuentaCobro).filter(CuentaCobro.proyecto_id == p.id).all()]
    return balance_de_obra(items, pct_por_item, cuentas)
