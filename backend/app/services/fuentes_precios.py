# -*- coding: utf-8 -*-
"""ADAPTADOR DE FUENTES DE PRECIOS — patron enchufable.
Cada fuente responde a buscar(q) con [{fuente, nombre, unidad, precio, fecha, detalle}].
Hoy: curada (nuestra base mensual) + mis_proveedores (via endpoint, con db).
Manana: externa (scraper aislado con cache / listas de aliados) — la interfaz ya existe;
si una fuente falla, las demas responden y nadie lo nota."""
import json
import os
import unicodedata

_CURADA = None


def _sin_tildes(s: str) -> str:
    return ''.join(ch for ch in unicodedata.normalize('NFD', s or '')
                   if unicodedata.category(ch) != 'Mn').lower()


def _cargar_curada():
    global _CURADA
    if _CURADA is None:
        ruta = os.path.join(os.path.dirname(__file__), "..", "data", "insumos_2026.json")
        _CURADA = json.load(open(ruta, encoding="utf-8"))
    return _CURADA


def fuente_curada(q: str, limit: int = 12) -> list:
    """Nuestra base de referencia — el colchon que nunca falla."""
    data = _cargar_curada()
    qn = _sin_tildes(q)
    out = []
    for i in data["insumos"]:
        if qn in _sin_tildes(i["nombre"]) or qn in _sin_tildes(i["categoria"]):
            out.append({"fuente": "referencia", "nombre": i["nombre"], "unidad": i["unidad"],
                        "precio": i["precio"], "fecha": data["version"],
                        "detalle": "Precio de referencia del mercado",
                        "imagen": i.get("imagen")})
            if len(out) >= limit:
                break
    return out


def fuente_externa(q: str, limit: int = 6) -> list:
    """FUTURO: scraper/aliados — aislada tras PRECIOS_EXTERNOS_JSON (cache pre-generado).
    Sin la variable, responde vacio: degradacion elegante, cero dependencias en vivo."""
    ruta = os.environ.get("PRECIOS_EXTERNOS_JSON", "")
    if not ruta or not os.path.exists(ruta):
        return []
    try:
        data = json.load(open(ruta, encoding="utf-8"))
        qn = _sin_tildes(q)
        return [{"fuente": d.get("fuente", "externa"), "nombre": d["nombre"],
                 "unidad": d.get("unidad", "un"), "precio": int(d["precio"]),
                 "fecha": d.get("fecha", ""), "detalle": d.get("detalle", "")}
                for d in data if qn in _sin_tildes(d.get("nombre", ""))][:limit]
    except Exception:
        return []   # una fuente rota jamas tumba la busqueda
