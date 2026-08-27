# -*- coding: utf-8 -*-
"""MIS PROVEEDORES — la ferreteria del contratista y sus precios negociados,
cada precio con su fecha de captura (honestidad de frescura)."""
import csv
import io
import logging
import unicodedata
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.db import get_db, Usuario, Proveedor, PrecioProveedor
from app.api.auth import usuario_actual

logger = logging.getLogger(__name__)
router = APIRouter()
MAX_PROVEEDORES = 50
MAX_PRECIOS = 3000        # por proveedor — subido de 300 para permitir carga masiva de base propia
MAX_FILA_MASIVO = 2500    # por archivo subido — evita procesar algo gigante en una sola request


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


# ── CARGA MASIVA: tu propia base de precios por Excel/CSV ──────────────────
def _sin_tildes(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower().strip()


# nombres de columna aceptados (sin tildes, minuscula) -> campo real
ALIAS_COLUMNAS = {
    "insumo": "insumo", "nombre": "insumo", "material": "insumo", "producto": "insumo",
    "descripcion": "insumo",
    "unidad": "unidad", "und": "unidad", "un": "unidad",
    "precio": "precio", "valor": "precio", "precio unitario": "precio", "vr unitario": "precio",
}


def _parsear_filas(contenido: bytes, nombre_archivo: str) -> List[dict]:
    """Lee un .xlsx o .csv y devuelve filas normalizadas {insumo, unidad, precio}.
    Encabezados tolerantes: cualquier orden, con/sin tildes, mayus/minus."""
    filas_crudas = []
    ext = (nombre_archivo or "").lower().rsplit(".", 1)[-1]

    if ext in ("xlsx", "xlsm"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(contenido), data_only=True, read_only=True)
            if not wb.worksheets:
                raise HTTPException(400, "El archivo no tiene ninguna hoja")
            ws = wb.worksheets[0]
            filas_crudas = list(ws.iter_rows(values_only=True))
        except HTTPException:
            raise
        except Exception:
            # archivo con extension .xlsx pero corrupto/no es realmente un excel
            # (BadZipFile y similares) — nunca un 500 crudo, siempre un mensaje claro
            raise HTTPException(400, "No pude leer este archivo — verifica que sea "
                                     "un Excel (.xlsx) valido y no este danado")
    elif ext == "csv":
        try:
            texto = contenido.decode("utf-8-sig", errors="replace")
            filas_crudas = list(csv.reader(io.StringIO(texto)))
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(400, "No pude leer este archivo CSV — verifica el formato")
    else:
        raise HTTPException(400, "Formato no soportado — sube un .xlsx o .csv")

    if not filas_crudas:
        raise HTTPException(400, "El archivo esta vacio")

    # localizar la fila de encabezado: la primera que reconozca al menos
    # "insumo" y "precio" entre sus columnas (tolera filas de titulo arriba)
    idx_header = None
    mapa_col = {}
    for i, fila in enumerate(filas_crudas[:10]):
        candidato = {}
        for j, celda in enumerate(fila or []):
            clave = ALIAS_COLUMNAS.get(_sin_tildes(str(celda or "")))
            if clave:
                candidato[clave] = j
        if "insumo" in candidato and "precio" in candidato:
            idx_header, mapa_col = i, candidato
            break
    if idx_header is None:
        raise HTTPException(400, 'No reconozco las columnas — el archivo necesita al menos '
                                  '"insumo/nombre" y "precio" (unidad es opcional, si falta se asume "un")')

    filas = []
    for fila in filas_crudas[idx_header + 1:]:
        if not fila or all(c in (None, "") for c in fila):
            continue
        def _get(clave, default=""):
            j = mapa_col.get(clave)
            return fila[j] if (j is not None and j < len(fila) and fila[j] is not None) else default
        insumo = str(_get("insumo")).strip()
        if not insumo:
            continue
        unidad = str(_get("unidad", "un")).strip() or "un"
        try:
            precio = round(float(str(_get("precio", 0)).replace(",", "").replace("$", "").strip() or 0))
        except ValueError:
            continue  # fila con precio ilegible: se ignora, no rompe el resto
        filas.append({"insumo": insumo, "unidad": unidad, "precio": precio})
    return filas


@router.post("/{pid}/precios/masivo")
async def cargar_masivo(pid: int, archivo: UploadFile = File(...),
                        user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """Carga masiva desde Excel/CSV — mismas 3 columnas que el alta manual
    (insumo, unidad, precio). Los nuevos se insertan directo. Si un insumo YA
    existe con un precio DISTINTO, no se pisa solo: se separa en 'conflictos'
    para que el usuario confirme via /precios/resolver-conflictos."""
    p = _mio(pid, user, db)
    contenido = await archivo.read()
    if len(contenido) > 8_000_000:
        raise HTTPException(400, "Archivo muy grande — maximo 8MB")

    filas = _parsear_filas(contenido, archivo.filename or "")
    if not filas:
        raise HTTPException(400, "No se encontraron filas validas en el archivo")
    if len(filas) > MAX_FILA_MASIVO:
        raise HTTPException(400, f"Maximo {MAX_FILA_MASIVO} filas por archivo — divide tu base en "
                                 f"partes mas chicas y sube una por una")

    existentes = (db.query(PrecioProveedor)
                  .filter(PrecioProveedor.proveedor_id == p.id).all())
    por_nombre = {_sin_tildes(e.insumo): e for e in existentes}

    nuevos_a_crear = []
    conflictos = []
    sin_cambios = 0
    invalidas = 0
    duplicados_en_archivo = 0
    vistos_en_archivo = set()

    for f in filas:
        insumo = f["insumo"][:160]
        if len(insumo) < 2 or f["precio"] < 0 or f["precio"] > 500_000_000:
            invalidas += 1
            continue
        clave = _sin_tildes(insumo)
        if clave in vistos_en_archivo:
            duplicados_en_archivo += 1  # mismo material listado 2+ veces en el archivo: se queda con el primero
            continue
        vistos_en_archivo.add(clave)

        existente = por_nombre.get(clave)
        if not existente:
            nuevos_a_crear.append({"insumo": insumo, "unidad": f["unidad"][:15], "precio": f["precio"]})
        elif existente.precio == f["precio"]:
            sin_cambios += 1
        else:
            conflictos.append({
                "id_existente": existente.id, "insumo": insumo,
                "unidad_actual": existente.unidad, "precio_actual": existente.precio,
                "unidad_nueva": f["unidad"][:15], "precio_nuevo": f["precio"],
            })

    total_final = len(existentes) + len(nuevos_a_crear)
    if total_final > MAX_PRECIOS:
        raise HTTPException(400, f"Este archivo llevaria a {total_final} precios en este proveedor "
                                 f"— el limite es {MAX_PRECIOS}. Divide la carga o crea otro proveedor.")

    for n in nuevos_a_crear:
        db.add(PrecioProveedor(proveedor_id=p.id, user_id=user.id, **n))
    db.commit()

    logger.info(f"Carga masiva proveedor {p.id}: {len(nuevos_a_crear)} nuevos, "
                f"{sin_cambios} sin cambios, {len(conflictos)} conflictos, {invalidas} invalidas, "
                f"{duplicados_en_archivo} duplicados en el archivo")
    return {
        "ok": True,
        "nuevos": len(nuevos_a_crear),
        "sin_cambios": sin_cambios,
        "invalidas": invalidas,
        "duplicados_en_archivo": duplicados_en_archivo,
        "conflictos": conflictos,
    }


class DecisionConflicto(BaseModel):
    id_existente: int
    accion: str  # "actualizar" | "mantener"
    precio_nuevo: Optional[int] = None
    unidad_nueva: Optional[str] = None


class ResolverConflictosRequest(BaseModel):
    decisiones: List[DecisionConflicto]


@router.post("/precios/resolver-conflictos")
def resolver_conflictos(req: ResolverConflictosRequest,
                        user: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    """Aplica las decisiones del usuario sobre los conflictos de la carga masiva
    (actualizar al precio nuevo, o mantener el que ya estaba)."""
    if len(req.decisiones) > MAX_FILA_MASIVO:
        raise HTTPException(400, "Demasiadas decisiones en una sola solicitud")
    actualizados = 0
    for d in req.decisiones:
        if d.accion != "actualizar":
            continue
        r = db.query(PrecioProveedor).filter(PrecioProveedor.id == d.id_existente,
                                             PrecioProveedor.user_id == user.id).first()
        if not r or d.precio_nuevo is None:
            continue
        if d.precio_nuevo < 0 or d.precio_nuevo > 500_000_000:
            continue
        r.precio = d.precio_nuevo
        if d.unidad_nueva:
            r.unidad = d.unidad_nueva[:15]
        actualizados += 1
    db.commit()
    return {"ok": True, "actualizados": actualizados}
