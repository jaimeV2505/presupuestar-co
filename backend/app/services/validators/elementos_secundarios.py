# -*- coding: utf-8 -*-
"""Calculo automatico de elementos secundarios — v7."""
import re, math, logging
from typing import List, Dict, Optional, Tuple
logger = logging.getLogger(__name__)

MALLAS_ELECTROSOLDADAS = {
    "M-106": {"descripcion": "4.2mm@15x15cm", "peso_kg_m2": 1.85, "area_cm2_m": 9.24},
    "M-132": {"descripcion": "4.2mm@10x25cm", "peso_kg_m2": 2.32, "area_cm2_m": 13.85},
    "M-188": {"descripcion": "5.0mm@15x15cm", "peso_kg_m2": 2.60, "area_cm2_m": 13.08},
    "M-235": {"descripcion": "5.5mm@15x15cm", "peso_kg_m2": 3.12, "area_cm2_m": 15.90},
    "M-283": {"descripcion": "6.0mm@15x15cm", "peso_kg_m2": 3.72, "area_cm2_m": 18.85},
    "M-335": {"descripcion": "6.5mm@15x15cm", "peso_kg_m2": 4.36, "area_cm2_m": 22.17},
    "M-424": {"descripcion": "7.3mm@15x15cm", "peso_kg_m2": 5.52, "area_cm2_m": 27.95},
    "M-503": {"descripcion": "8.0mm@15x15cm", "peso_kg_m2": 6.61, "area_cm2_m": 33.51},
    "M-636": {"descripcion": "9.0mm@15x15cm", "peso_kg_m2": 8.33, "area_cm2_m": 42.41},
}

def calcular_correas_desde_separacion(
    area_cubierta_m2: float, separacion_m: float, longitud_crujia_m: float,
    perfil: str = "PHR 160x60x2", ancho_cubierta_m: float = None
) -> Dict:
    if area_cubierta_m2 <= 0 or separacion_m <= 0 or longitud_crujia_m <= 0:
        return {"error": "Datos insuficientes"}
    if ancho_cubierta_m is None:
        ancho_cubierta_m = area_cubierta_m2 / longitud_crujia_m
    # Correas por fila
    n_fila = math.ceil(ancho_cubierta_m / separacion_m) + 1
    # Cubierta a dos aguas: duplicar si ancho > 70% de la crujia
    n_total = n_fila * 2 if ancho_cubierta_m > longitud_crujia_m * 0.7 else n_fila
    metros = n_total * longitud_crujia_m
    metros_desp = metros * 1.05
    res = {
        "perfil": perfil,
        "separacion_m": separacion_m,
        "longitud_crujia_m": longitud_crujia_m,
        "ancho_cubierta_m": round(ancho_cubierta_m, 2),
        "num_correas": n_total,
        "num_correas_por_fila": n_fila,
        "metros_lineales": round(metros, 1),
        "metros_con_desperdicio": round(metros_desp, 1),
        "unidad": "m",
        "nota": f"{n_total} correas ({n_fila}/fila x {longitud_crujia_m:.2f}m c/u)",
    }
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))
        from services.apu_service import get_peso_perfil
        peso = get_peso_perfil(perfil)
        if peso:
            res["peso_kg_m"] = peso
            res["kg_total"] = round(metros_desp * peso, 1)
    except Exception:
        pass
    logger.info(f"Correas: {n_total} x {longitud_crujia_m:.1f}m = {metros:.0f}m")
    return res

def calcular_malla_electrosoldada(
    area_m2: float, referencia_malla: str = "M-188", desperdicio_pct: float = 5.0
) -> Dict:
    ref_solicitada = referencia_malla.upper().strip()
    ref = ref_solicitada
    malla = MALLAS_ELECTROSOLDADAS.get(ref)
    if not malla:
        for key in MALLAS_ELECTROSOLDADAS:
            if ref in key or key in ref:
                malla = MALLAS_ELECTROSOLDADAS[key]; ref = key; break
    no_reconocida = not malla
    if no_reconocida:
        # NUNCA sustituir en silencio: el peso puede variar mas del doble entre
        # mallas (2.60 a 8.33 kg/m2). Se devuelve M-188 como referencia MINIMA de
        # trabajo, pero marcado explicitamente — el llamador debe advertir, no
        # mostrar "M-188" como si fuera lo detectado.
        ref = "M-188"; malla = MALLAS_ELECTROSOLDADAS["M-188"]
    area_desp = area_m2 * (1 + desperdicio_pct / 100)
    return {
        "referencia": ref,
        "referencia_solicitada": ref_solicitada,
        "no_reconocida": no_reconocida,
        "descripcion": malla["descripcion"],
        "area_m2": area_m2,
        "peso_kg_m2": malla["peso_kg_m2"],
        "kg_total": round(area_desp * malla["peso_kg_m2"], 1),
        "area_acero_cm2_m": malla["area_cm2_m"],
        "desperdicio_pct": desperdicio_pct,
    }

def enriquecer_elementos_con_calculos(
    elementos: List[Dict], area_total_m2: float = 0
) -> Tuple[List[Dict], List[str]]:
    elementos_out = []
    notas = []
    area_cubierta = area_total_m2
    for el in elementos:
        if el.get("tipo") in ("cubierta","losa") and el.get("area_m2"):
            area_cubierta = max(area_cubierta, el["area_m2"])
    for el in elementos:
        el_new = dict(el)
        nombre = el.get("nombre","").upper()
        notas_el = el.get("notas","") or ""
        material = el.get("material","") or ""
        # CASO 1: Correa con separacion
        sep_m = re.search(r'@\s*([\d.,]+)\s*(m|cm)?', notas_el+" "+nombre, re.I)
        es_correa = any(k in nombre for k in ["CORREA","PHR","CANAL"])
        if es_correa and sep_m and area_cubierta > 0 and el.get("unidad","") != "m":
            sv = float(sep_m.group(1).replace(",",".")); su = (sep_m.group(2) or "m").lower()
            sep = sv/100 if su=="cm" else sv
            lc = el.get("dimension_largo_m") or math.sqrt(area_cubierta)
            if sep > 0 and lc > 0:
                r = calcular_correas_desde_separacion(area_cubierta, sep, lc, material or nombre)
                if "metros_lineales" in r:
                    el_new["cantidad"] = r["metros_con_desperdicio"]
                    el_new["unidad"] = "m"
                    el_new["notas"] = notas_el + " | AUTO: " + r["nota"]
                    notas.append(f"{el.get('referencia','')}: {r['nota']} = {r['metros_con_desperdicio']:.0f}m")
        # CASO 2: Losa con malla
        mm = re.search(r'M[-\s]?(\d{3})', nombre+" "+material+" "+notas_el, re.I)
        if el.get("tipo")=="losa" and mm and el.get("area_m2"):
            rm = calcular_malla_electrosoldada(el["area_m2"], f"M-{mm.group(1)}")
            el_new["_malla_kg"] = rm["kg_total"]
            el_new["_malla_ref"] = rm["referencia"]
            if rm["no_reconocida"]:
                notas.append(f"⚠ Malla '{rm['referencia_solicitada']}' no esta en el catalogo — "
                             f"se uso {rm['referencia']} como referencia MINIMA de trabajo "
                             f"({el['area_m2']}m^2 = {rm['kg_total']}kg). Verificar la malla real del plano.")
            else:
                notas.append(f"Malla {rm['referencia']} {el['area_m2']}m^2 = {rm['kg_total']}kg")
        elementos_out.append(el_new)
    return elementos_out, notas

def get_malla_catalogo() -> Dict:
    return MALLAS_ELECTROSOLDADAS
