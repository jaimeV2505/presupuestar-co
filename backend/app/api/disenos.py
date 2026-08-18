# -*- coding: utf-8 -*-
"""🎨 DISENOS DEL PROYECTO — renders y planos que el cliente VE y COMENTA.

SOLO universo privado: la doctrina publica no tiene ventana externa, asi que
en obra publica este modulo entero responde 400. Blindaje de nacimiento:
tope 12 disenos por proyecto, ~700KB por imagen, terminado = solo lectura,
hilo de comentarios con tope (20 x 500 chars) y notificacion al otro lado.
"""
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import get_db, Usuario, Proyecto, Diseno
from app.api.auth import usuario_actual

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_DISENOS = 12
MAX_IMAGEN_CHARS = 950_000     # ~700KB binarios en base64
MAX_COMENTARIOS = 20
MAX_TEXTO = 500


class DisenoRequest(BaseModel):
    titulo: str = ""
    imagen_b64: str


class ComentarioRequest(BaseModel):
    texto: str


def _proyecto_privado(pid: int, user: Usuario, db: Session) -> Proyecto:
    p = db.query(Proyecto).filter(Proyecto.id == pid, Proyecto.user_id == user.id).first()
    if not p:
        raise HTTPException(404, "Proyecto no encontrado")
    if (p.sector or "privado") == "publico":
        raise HTTPException(400, "Los disenos son del universo privado — "
                                 "en obra publica nada viaja por fuera del expediente")
    return p


def _hilo(d: Diseno) -> list:
    try:
        return json.loads(d.comentarios_json or "[]")
    except ValueError:
        return []


def _out(d: Diseno, con_imagen: bool = True) -> dict:
    out = {"id": d.id, "titulo": d.titulo, "creado": d.creado.isoformat() if d.creado else "",
           "comentarios": _hilo(d)}
    if con_imagen:
        out["imagen_b64"] = d.imagen_b64
    return out


@router.get("/proyectos/{pid}/disenos")
def listar(pid: int, user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto_privado(pid, user, db)
    ds = (db.query(Diseno).filter(Diseno.proyecto_id == p.id)
          .order_by(Diseno.creado.asc()).all())
    return {"disenos": [_out(d) for d in ds], "max": MAX_DISENOS}


@router.post("/proyectos/{pid}/disenos")
def crear(pid: int, req: DisenoRequest,
          user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto_privado(pid, user, db)
    if p.estado == "terminado":
        raise HTTPException(400, "Proyecto terminado — solo lectura (duplicalo para una obra nueva)")
    img = (req.imagen_b64 or "").strip()
    if not img.startswith("data:image/"):
        raise HTTPException(400, "Solo imagenes (JPG/PNG) — los planos PDF exportalos a imagen")
    if len(img) > MAX_IMAGEN_CHARS:
        raise HTTPException(400, "Imagen muy pesada (max ~700KB) — la app la comprime sola; "
                                 "si la pegaste por fuera, reduce la resolucion")
    n = db.query(Diseno).filter(Diseno.proyecto_id == p.id).count()
    if n >= MAX_DISENOS:
        raise HTTPException(400, f"Tope de {MAX_DISENOS} disenos por proyecto — "
                                 "elimina alguno para subir otro")
    d = Diseno(proyecto_id=p.id, user_id=user.id,
               titulo=(req.titulo or "").strip()[:120], imagen_b64=img)
    db.add(d)
    db.commit()
    db.refresh(d)
    logger.info(f"Diseno subido: proyecto {p.id} ({n + 1}/{MAX_DISENOS})")
    return _out(d)


@router.delete("/proyectos/{pid}/disenos/{did}")
def eliminar(pid: int, did: int,
             user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    p = _proyecto_privado(pid, user, db)
    if p.estado == "terminado":
        raise HTTPException(400, "Proyecto terminado — solo lectura")
    d = db.query(Diseno).filter(Diseno.id == did, Diseno.proyecto_id == p.id).first()
    if not d:
        raise HTTPException(404, "Diseno no encontrado")
    db.delete(d)
    db.commit()
    return {"ok": True}


@router.post("/proyectos/{pid}/disenos/{did}/comentario")
def comentar(pid: int, did: int, req: ComentarioRequest,
             user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """El contratista responde en el hilo del diseno."""
    p = _proyecto_privado(pid, user, db)
    d = db.query(Diseno).filter(Diseno.id == did, Diseno.proyecto_id == p.id).first()
    if not d:
        raise HTTPException(404, "Diseno no encontrado")
    texto = (req.texto or "").strip()[:MAX_TEXTO]
    if not texto:
        raise HTTPException(400, "El comentario esta vacio")
    hilo = _hilo(d)
    if len(hilo) >= MAX_COMENTARIOS:
        raise HTTPException(400, "Hilo lleno — este diseno ya tiene demasiados comentarios")
    hilo.append({"autor": "contratista", "nombre": user.nombre or "Contratista",
                 "texto": texto, "fecha": datetime.now(timezone.utc).isoformat()})
    d.comentarios_json = json.dumps(hilo, ensure_ascii=False)
    db.commit()
    return {"ok": True, "comentarios": hilo}
