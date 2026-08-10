"""
Motor de presupuesto APU 2026 — v5.
Integra: validador NSR-10, calculadora acero exacta, escala gráfica, precios mercado.
"""
import logging, re, math, sys, os
from typing import List, Dict, Optional
from datetime import datetime
from app.models.schemas import ElementoEstructural, ItemPresupuesto, PresupuestoResponse, ResumenFinanciero
from app.services import apu_service as APU

# Importar tablas técnicas y validadores v5
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../data'))
try:
    from tablas_tecnicas import (
        get_varilla, calcular_kg_acero_por_especificacion,
        get_materiales_por_m3, calcular_acero_columna,
        calcular_acero_zapata, VARILLAS
    )
    TABLAS_OK = True
except ImportError:
    TABLAS_OK = False

try:
    from app.services.validators.nsr10_validator import validar_elementos, formatear_alertas_para_claude
    from app.services.validators.steel_calculator import (
        calcular_acero_columna_exacto, calcular_acero_viga_exacto, calcular_acero_zapata_exacto
    )
    from app.services.validators.benchmarks import validar_completo as validar_benchmarks
    from app.services.validators.coherencia import verificar_coherencia, generar_checklist_ingeniero
    from app.services.validators.predim import verificar_predimensionamiento, CARGAS_USO, QA_SUELO
    from app.services.validators.elementos_secundarios import enriquecer_elementos_con_calculos
    from app.services.price_scraper import analisis_sensibilidad, calcular_costo_materiales_concreto
    VALIDATORS_OK = True
except ImportError as e:
    VALIDATORS_OK = False
    import logging
    logging.getLogger(__name__).warning(f"Validators v5 no cargados: {e}")

logger = logging.getLogger(__name__)

# ── Factores técnicos NSR-10 (fallback si no hay especificación exacta) ────
# Estos se usan cuando el plano NO especifica el acero explícitamente
ACERO_KG_M3 = {
    "columnas_alta":85, "columnas_media":75, "columnas_baja":65,
    "vigas_alta":80,    "vigas_media":70,    "vigas_baja":55,
    "losa_nervada_m2":12, "losa_maciza_m2":18,
    "cimentacion":60,   "escaleras":50,     "viga_amarre_ml":16,
    "muro_contencion_m3":70,
}
DESP = {"col":1.05,"viga":1.05,"losa":1.08,"cim":1.10,"acero":1.08}
FACTOR_EXC = 3.5; FACTOR_RELL = 0.65

# Adicionales estructura metálica (% sobre costo perfiles)
ADICIONAL_TORNILLERIA = 0.015
ADICIONAL_SOLDADURA   = 0.020
ADICIONAL_PLATINERIA  = 0.040

def _zona(el) -> str:
    t = ((el.notas or "")+(el.material or "")).lower()
    return "baja" if "baja" in t else "media" if "media" in t or "intermedia" in t else "alta"

def _parse(dim: str) -> Dict:
    r = {"a":None,"b":None,"h":None,"l":None,"e":None,"d":None}
    if not dim: return r
    s = dim.replace(",",".")
    m = re.search(r'(\d+(?:\.\d+)?)\s*[x×\/]\s*(\d+(?:\.\d+)?)\s*(cm|m)?', s, re.I)
    if m:
        v,w = float(m.group(1)), float(m.group(2))
        u = (m.group(3) or "cm").lower()
        r["a"] = v/100 if u=="cm" else v
        r["b"] = w/100 if u=="cm" else w
    for pat,key in [(r'(?:h|altura)\s*[=:]\s*(\d+(?:\.\d+)?)\s*(m|cm)',"h"),
                    (r'(?:L|long)\s*[=:]\s*(\d+(?:\.\d+)?)\s*m',"l"),
                    (r'(?:e|esp)\s*[=:]\s*(\d+(?:\.\d+)?)\s*(m|cm)',"e"),
                    (r'(?:D|diam)\s*[=:]\s*(\d+(?:\.\d+)?)\s*(m|cm)',"d")]:
        m2 = re.search(pat,s,re.I)
        if m2:
            v = float(m2.group(1))
            u2 = m2.group(2).lower() if m2.lastindex>=2 else "m"
            r[key] = v if u2=="m" else v/100
    return r

def _dims(el) -> Dict:
    a = (el.dimension_ancho_cm/100) if el.dimension_ancho_cm else None
    b = (el.dimension_alto_cm/100)  if el.dimension_alto_cm  else None
    l = el.dimension_largo_m        if el.dimension_largo_m  else None
    h = el.altura_libre_m           if el.altura_libre_m     else None
    e = (el.espesor_cm/100)         if el.espesor_cm         else None
    d = (el.dimension_diametro_cm/100) if el.dimension_diametro_cm else None
    ar = el.area_m2
    if not a and not d:
        p = _parse(el.dimension or "")
        a=p["a"]; b=p["b"]; h=h or p["h"]; l=l or p["l"]
        e=e or p["e"]; d=d or p["d"]
    return {"a":a,"b":b,"h":h,"l":l,"e":e,"d":d,"area":ar}

def _es_metalica(el) -> bool:
    """Detecta si el elemento es estructura metálica."""
    indicadores = ["PTE","PHR","CAJÓN","W10","W12","W14","W18","HEA","HEB","IPE",
                   "ANGULO","ÁNGULO","CERCHA","CORREA","TEMPLERO","METALIC","METÁLIC"]
    texto = f"{el.nombre} {el.material or ''} {el.notas or ''}".upper()
    return any(ind in texto for ind in indicadores)

def _extraer_perfil_nombre(el) -> Optional[str]:
    """Extrae nombre del perfil metálico del elemento."""
    texto = f"{el.nombre} {el.material or ''}"
    patterns = [
        r'PTE\s*\d+[xX]\d+[xX][\d.]+(?:mm)?',
        r'PHR\s*[CcKk]?\s*\d+[xX]\d+[xX][\d.]+(?:mm)?',
        r'PHR\s*CAJÓN\s*\d+[xX]\d+[xX][\d.]+',
        r'W\d+[xX]\d+',
        r'ANGULO\s*[\d\s"]+[xX][\d/"]+'
    ]
    for pat in patterns:
        m = re.search(pat, texto.upper())
        if m: return m.group(0).strip()
    return None


async def generar_items(
    elementos: List[ElementoEstructural],
    region: str, fc_mpa: float, fy_mpa: float
) -> List[ItemPresupuesto]:

    items = []
    idx = 1

    def add(cap, nombre, uni, cant, precio_u, codigo=None, rend=None, notas_c=None):
        nonlocal idx
        if cant <= 0 or precio_u <= 0: return
        items.append(ItemPresupuesto(
            idx=idx, capitulo=cap, codigo=codigo, nombre=nombre,
            unidad=uni, cantidad=round(cant,3),
            precio_unitario=round(precio_u),
            precio_total=round(cant*precio_u),
            rendimiento=rend, notas_calculo=notas_c
        ))
        idx += 1

    # ── Acumulador para estructura metálica ──────────────────────────────
    metal_kg_total = 0.0
    metal_items_detail = []  # Para desglose por perfil
    notas = []  # Notas de cuantificacion acumuladas durante el proceso

    for el in elementos:
        tipo = el.tipo
        d = _dims(el); zona = _zona(el)
        ref = f"[{el.referencia}] " if el.referencia else ""
        nom = f"{ref}{el.nombre}"
        cant = el.cantidad or 0
        uni = (el.unidad or "un").lower()

        # Elemento sin cantidad: intentar estimar de dimensiones, sino saltar con nota
        if cant <= 0:
            if d.get("l") and d["l"] > 0:
                cant = d["l"]
                uni = "m"
                notas.append(f"'{nom}': cantidad no extraida del plano — usando longitud {d['l']}m como estimado. VERIFICAR.")
            else:
                notas.append(f"'{nom}': SIN CANTIDAD en el plano — no incluido en el presupuesto. Agregar manualmente en la extraccion.")
                continue

        # ── ESTRUCTURA METÁLICA ──────────────────────────────────────────
        if _es_metalica(el) or tipo in ("cubierta","otros") and _es_metalica(el):
            perfil_nombre = _extraer_perfil_nombre(el)
            longitud_m = cant if uni == "m" else (cant * (d["l"] or d["h"] or 6.0))

            if perfil_nombre:
                peso_kg_m = APU.get_peso_perfil(perfil_nombre)
                if peso_kg_m:
                    kg = round(longitud_m * peso_kg_m, 2)
                    metal_kg_total += kg
                    metal_items_detail.append({
                        "perfil": perfil_nombre, "longitud": longitud_m,
                        "peso_kg_m": peso_kg_m, "kg_total": kg, "nombre": nom
                    })
                    # Precio por metro de perfil desde BD o por kg
                    precio_item = APU.get_precio_perfil_metalico(perfil_nombre, region)
                    if precio_item and precio_item.get("unidad_base") == "m":
                        add("ESTRUCTURA METÁLICA", f"Perfil {perfil_nombre} — {nom}",
                            "m", longitud_m, precio_item["precio"], precio_item["codigo"],
                            "200 m/semana (taller)", f"{kg}kg total")
                    else:
                        # Precio por kg instalado
                        p_kg = APU.get_precio("5.29", region)
                        if p_kg:
                            add("ESTRUCTURA METÁLICA", f"Sumin. e Instal. {perfil_nombre} — {nom}",
                                "Kg", kg, p_kg["precio"], "5.29",
                                "500 kg/jornada", f"Peso unitario: {peso_kg_m} kg/m")
                else:
                    # Sin peso conocido — precio por kg genérico
                    p_kg = APU.get_precio("5.29", region)
                    if p_kg:
                        kg_est = longitud_m * 10  # estimado conservador
                        add("ESTRUCTURA METÁLICA", f"Estructura metálica — {nom}",
                            "Kg", kg_est, p_kg["precio"], "5.29",
                            None, "Peso estimado — verificar con memoria de cálculo")
            else:
                # Sin perfil identificado — usar longitud directa
                p_kg = APU.get_precio("5.29", region)
                if p_kg:
                    kg_est = longitud_m * 8
                    add("ESTRUCTURA METÁLICA", f"Estructura metálica — {nom}",
                        "Kg", kg_est, p_kg["precio"], "5.29")
            continue

        # ── COLUMNAS concreto ────────────────────────────────────────────
        if tipo == "columnas":
            a = d["a"] or 0.30; b = d["b"] or 0.30; h = d["h"] or 3.0
            if d["d"]: vol_u = math.pi*(d["d"]/2)**2*h; form_u = math.pi*d["d"]*h
            else:       vol_u = a*b*h; form_u = 2*(a+b)*h
            n = cant if uni=="un" else 1
            l_total = h * n

            col_item = APU.buscar_columna(a, b, fc_mpa, region)
            if col_item and l_total > 0:
                nota = f"Sección APU: {col_item.get('seccion_usada',f'{a:.2f}x{b:.2f}m')}"
                if col_item.get("ajuste"): nota += " (interpolada)"
                add("ESTRUCTURAS EN CONCRETO", f"Concreto columna — {nom}",
                    "m", l_total, col_item["precio"], col_item["codigo"], "3 m/jornada", nota)
            elif vol_u * n > 0:
                vol = vol_u * n * DESP["col"]
                p = APU.get_precio("4.29", region)
                if p: add("ESTRUCTURAS EN CONCRETO", f"Concreto columna m³ — {nom}",
                          "m3", vol, p["precio"], "4.29", "3 m³/jornada", "Sección no en BD, precio m³")

            # ── ACERO COLUMNA: usar especificación real si está disponible ──
            acero_long = el.acero_longitudinal or ""
            acero_trans = el.acero_transversal or ""
            if TABLAS_OK and acero_long:
                # Calcular acero exacto desde especificación del plano
                res_acero = calcular_acero_columna(acero_long, acero_trans, h, int(n))
                kg_acero_real = res_acero["kg_total"]
                if kg_acero_real > 0:
                    acero_item = APU.buscar_acero(fy_mpa, region)
                    if acero_item:
                        add("ESTRUCTURAS EN CONCRETO",
                            f"Acero fy={fy_mpa}MPa ({acero_long}) — {nom}",
                            "Kg", kg_acero_real, acero_item["precio"], acero_item["codigo"],
                            "200 kg/jornada",
                            f"Calculado por varilla: {res_acero['detalle']}")
            # NOTA: Si el APU de columna ya incluye acero (precio por metro incluye refuerzo típico),
            # no agregar acero extra para evitar doble conteo.
            # Solo agregar si el APU es por m³ genérico.

        # ── VIGAS concreto ───────────────────────────────────────────────
        elif tipo == "vigas":
            a = d["a"] or 0.25; b = d["b"] or 0.40; l = d["l"] or 5.0
            n = cant if uni=="un" else 1; l_total = l*n
            viga_item = APU.buscar_viga(a, b, fc_mpa, region)
            if viga_item and l_total > 0:
                add("ESTRUCTURAS EN CONCRETO", f"Concreto viga — {nom}",
                    "m", l_total, viga_item["precio"], viga_item["codigo"],
                    "4 m/jornada", f"Sección APU: {viga_item.get('seccion_usada',f'{a:.2f}x{b:.2f}m')}")
            elif l_total > 0:
                vol = a*b*l_total*DESP["viga"]
                p = APU.get_precio("4.151", region)
                if p: add("ESTRUCTURAS EN CONCRETO", f"Concreto viga m³ — {nom}",
                          "m3", vol, p["precio"], "4.151", "3.5 m³/jornada")

        # ── VIGA DE AMARRE ───────────────────────────────────────────────
        elif tipo == "viga_amarre":
            l = d["l"] or (cant if uni=="m" else cant*3.5)
            a = d["a"] or 0.15; b = d["b"] or 0.20
            va_cod = "4.150" if b >= 0.25 else "4.149"
            va = APU.get_precio(va_cod, region)
            if va and l > 0:
                add("CIMENTACIONES", f"Viga de amarre — {nom}",
                    "m", l, va["precio"], va_cod, "4 m/jornada")
            acero = APU.buscar_acero(fy_mpa, region)
            if acero and l > 0:
                kg = l * ACERO_KG_M3["viga_amarre_ml"] * DESP["acero"]
                add("CIMENTACIONES", f"Acero refuerzo viga amarre — {nom}",
                    "Kg", kg, acero["precio"], acero["codigo"], "200 kg/jornada")

        # ── CIMENTACIÓN — zapatas por tipo ───────────────────────────────
        elif tipo == "cimentacion":
            # Calcular volumen exacto
            if uni == "m³":
                vol = cant
            elif uni == "m²":
                vol = cant * (d["e"] or 0.30)
            elif uni == "un":
                aw = d["a"] or 1.2; bw = d["b"] or 1.2; hw = d["e"] or d["h"] or 0.30
                vol = cant * aw * bw * hw
            else:
                vol = cant * 0.5

            vol *= DESP["cim"]
            vol_exc = vol * FACTOR_EXC
            vol_rell = vol_exc * FACTOR_RELL
            kg_acero = vol * ACERO_KG_M3["cimentacion"] * DESP["acero"]
            prof = abs(d["h"] or 1.5)

            exc = APU.buscar_excavacion(prof, False, region)
            if exc and vol_exc > 0:
                add("CIMENTACIONES", f"Excavación — {nom}",
                    "m3", vol_exc, exc["precio"], exc["codigo"], "2.5 m³/jornada")

            rell = APU.buscar_relleno(region)
            if rell and vol_rell > 0:
                add("CIMENTACIONES", f"Relleno compactado — {nom}",
                    "m3", vol_rell, rell["precio"], rell["codigo"], "3.5 m³/jornada")

            conc = APU.buscar_concreto_cimentacion(fc_mpa, region)
            if conc and vol > 0:
                add("CIMENTACIONES", f"Concreto f'c={fc_mpa}MPa — {nom}",
                    "m3", vol, conc["precio"], None, "3.5 m³/jornada",
                    f"f'c={fc_mpa}MPa (ajustado -15% vs columna)")

            # Acero cimentación: usar especificación real si está disponible
            acero_item = APU.buscar_acero(fy_mpa, region)
            if acero_item:
                if TABLAS_OK and el.acero_longitudinal:
                    # Calcular kg exactos desde especificación de varilla
                    aw = d["a"] or 1.2; bw = d["b"] or 1.2; hw = d["e"] or d["h"] or 0.30
                    res = calcular_acero_zapata(
                        aw, bw, hw,
                        el.acero_longitudinal,
                        el.acero_transversal,
                        int(cant) if uni == "un" else 1
                    )
                    kg_acero_real = res["kg_total"]
                    nota_acero = f"Calculado por varilla: dir1={res['kg_direccion_1']}kg + dir2={res['kg_direccion_2']}kg"
                    add("CIMENTACIONES", f"Acero fy={fy_mpa}MPa ({el.acero_longitudinal}) — {nom}",
                        "Kg", kg_acero_real, acero_item["precio"], acero_item["codigo"],
                        "200 kg/jornada", nota_acero)
                elif kg_acero > 0:
                    add("CIMENTACIONES", f"Acero fy={fy_mpa}MPa — {nom}",
                        "Kg", kg_acero, acero_item["precio"], acero_item["codigo"],
                        "200 kg/jornada", "Kg estimados por factor técnico NSR-10")

        # ── CAISSON / PILOTE ─────────────────────────────────────────────
        elif tipo in ("caisson","pilote","pila") or ("caisson" in (el.nombre or "").lower() or "pilote" in (el.nombre or "").lower()):
            d_m = d["d"] or 0.60
            prof = d["h"] or d["l"] or 6.0
            n_und = cant if uni in ("un","und") else 1
            data = APU.buscar_caisson(d_m, prof, fc_mpa, region)

            if data["excavacion"]:
                exc_vol = data["volumen_m3"] * 1.2 * n_und
                add("CIMENTACIONES", f"Excavación pila/caisson D={d_m}m — {nom}",
                    "m3", exc_vol, data["excavacion"]["precio"],
                    data["excavacion"]["codigo"], "4 m³/jornada")

            if data["concreto"]:
                add("CIMENTACIONES", f"Concreto pila/caisson f'c={fc_mpa}MPa — {nom}",
                    "m3", data["volumen_m3"]*n_und, data["concreto"]["precio"],
                    data["concreto"]["codigo"], "2 m³/jornada")

            if data["acero"]:
                add("CIMENTACIONES", f"Acero refuerzo pila/caisson — {nom}",
                    "Kg", data["kg_acero"]*n_und, data["acero"]["precio"],
                    data["acero"]["codigo"], "150 kg/jornada")

        # ── MURO DE CONTENCIÓN ───────────────────────────────────────────
        elif tipo == "muros" and any(x in (el.nombre or "").lower() for x in ["contención","contencion","contenci"]):
            area_m = d["area"] or (cant if uni == "m²" else cant*9.0)
            e_m = d["e"] or 0.30
            vol_m = area_m * e_m * DESP["col"]
            prof_m = d["h"] or 3.0
            kg_ac = vol_m * ACERO_KG_M3["muro_contencion_m3"] * DESP["acero"]

            exc = APU.buscar_excavacion(prof_m/2, False, region)
            if exc:
                add("CIMENTACIONES", f"Excavación muro contención — {nom}",
                    "m3", vol_m * 1.5, exc["precio"], exc["codigo"])

            mc = APU.buscar_muro_contencion(fc_mpa, region)
            if mc and vol_m > 0:
                add("CIMENTACIONES", f"Muro contención f'c={fc_mpa}MPa — {nom}",
                    "m3", vol_m, mc["precio"], mc["codigo"],
                    "2.5 m³/jornada", f"e={e_m*100:.0f}cm, h≈{prof_m}m")

            acero = APU.buscar_acero(fy_mpa, region)
            if acero and kg_ac > 0:
                add("CIMENTACIONES", f"Acero refuerzo muro contención — {nom}",
                    "Kg", kg_ac, acero["precio"], acero["codigo"], "180 kg/jornada")

        # ── MUROS mampostería ────────────────────────────────────────────
        elif tipo == "muros":
            area = d["area"] or (cant if uni=="m²" else cant*9.0)
            if area <= 0: continue
            nom_m = (el.nombre or "").lower(); mat_m = (el.material or "").lower()
            mi = APU.buscar_muro_mamposteria(nom_m+mat_m, region)
            if mi:
                add("MAMPOSTERÍA", f"Muro — {nom}", "m2", area, mi["precio"], mi.get("codigo"), "8 m²/jornada")
            if "drywall" not in nom_m:
                pan = APU.buscar("pañete mortero", "PAÑETES (REVOQUES)", region, 1)
                if pan:
                    add("PAÑETES (REVOQUES)", f"Pañete 1:4 doble cara — {nom}",
                        "m2", round(area*1.95,1), pan[0]["precio"], pan[0].get("codigo"), "14 m²/jornada")

        # ── LOSA ─────────────────────────────────────────────────────────
        elif tipo == "losa":
            area = d["area"] or (cant if uni=="m²" else cant*25.0)
            if area <= 0: continue
            esp = d["e"] or 0.25
            nom_l = (el.nombre or "").lower()
            tipo_losa = "maciza" if any(x in nom_l for x in ["maciza","macizo"]) else "aligerada"
            losa_item = APU.buscar_losa(tipo_losa, esp, fc_mpa, region)
            if losa_item:
                add("ESTRUCTURAS EN CONCRETO", f"Placa {tipo_losa} — {nom}",
                    "m2", area, losa_item["precio"], losa_item["codigo"],
                    "15 m²/jornada", f"e={round(esp*100)}cm")
            if tipo_losa == "maciza" and area > 0:
                malla = APU.get_precio("4.85", region)
                if malla: add("ESTRUCTURAS EN CONCRETO", f"Malla electrosoldada M-188 — {nom}",
                              "m2", area, malla["precio"], "4.85", "20 m²/jornada")

        # ── ESCALERAS ────────────────────────────────────────────────────
        elif tipo == "escaleras":
            area = d["area"] or (cant if uni=="m²" else cant*12.0)
            e_item = APU.get_precio("4.76", region)
            if e_item and area > 0:
                add("ESTRUCTURAS EN CONCRETO", f"Escalera concreto — {nom}",
                    "m2", area, e_item["precio"], "4.76")
            acero = APU.buscar_acero(fy_mpa, region)
            if acero and area > 0:
                kg = area * 0.15 * ACERO_KG_M3["escaleras"] * DESP["acero"]
                add("ESTRUCTURAS EN CONCRETO", f"Acero escalera — {nom}",
                    "Kg", kg, acero["precio"], acero["codigo"])

        # ── CUBIERTA ─────────────────────────────────────────────────────
        elif tipo == "cubierta":
            if _es_metalica(el): continue  # Ya manejado arriba
            area = d["area"] or (cant if uni=="m²" else cant*20.0)
            if area <= 0: continue
            nom_c = (el.nombre or "").lower()
            if "termoacu" in nom_c or "sandwich" in nom_c or "panel" in nom_c:
                c = APU.get_precio("6.18", region)  # Panel sandwich Aluzinc
            elif "zinc" in nom_c:
                c = APU.buscar("cubierta zinc", "CUBIERTAS", region, 1)
                c = c[0] if c else None
            elif "fibrocemento" in nom_c or "eternit" in nom_c:
                c = APU.buscar("fibrocemento", "CUBIERTAS", region, 1)
                c = c[0] if c else None
            else:
                c = APU.buscar("cubierta", "CUBIERTAS", region, 1)
                c = c[0] if c else None
            if c: add("CUBIERTAS", f"Cubierta — {nom}", "m2", area, c["precio"], c.get("codigo"))

    # ── Desglose estructura metálica con adicionales ─────────────────────
    if metal_items_detail:
        costo_metal = sum(
            i.precio_total for i in items if i.capitulo == "ESTRUCTURA METÁLICA"
        )
        if costo_metal > 0:
            # Sandblasting + pintura
            p_sb = APU.get_precio("5.28", region)
            if p_sb:
                add("ESTRUCTURA METÁLICA", "Sandblasting y pintura anticorrosiva",
                    "Kg", round(metal_kg_total, 1), p_sb["precio"], "5.28",
                    "300 kg/jornada", f"Total acero: {metal_kg_total:.0f}kg")
            # Tornillería, soldadura, platinería
            p_inst = APU.get_precio("5.29", region)
            base_p = p_inst["precio"] if p_inst else 18365
            add("ESTRUCTURA METÁLICA", "Tornillería (1.5% sobre materiales)",
                "Gl", 1, round(costo_metal * ADICIONAL_TORNILLERIA), None)
            add("ESTRUCTURA METÁLICA", "Soldadura E70 (2.0% sobre materiales)",
                "Gl", 1, round(costo_metal * ADICIONAL_SOLDADURA), None)
            add("ESTRUCTURA METÁLICA", "Platinería y conexiones (4.0% sobre materiales)",
                "Gl", 1, round(costo_metal * ADICIONAL_PLATINERIA), None)

    # ── Instalaciones estimadas ──────────────────────────────────────────
    area_ref = sum(
        (el.area_m2 or 0) for el in elementos if el.tipo == "losa"
    )
    if area_ref <= 0: area_ref = 80
    puntos_e = max(8, round(area_ref / 6))
    puntos_h = max(4, round(area_ref / 12))

    pto_tom = APU.buscar("tomacorriente doble", "INSTALACIONES ELÉCTRICAS", region, 1)
    pto_lum = APU.buscar("punto de iluminación", "INSTALACIONES ELÉCTRICAS", region, 1)
    if pto_tom: add("INSTALACIONES ELÉCTRICAS","Puntos tomacorriente 110V (RETIE 1/6m²)",
                    "Un", round(puntos_e*0.6), pto_tom[0]["precio"], pto_tom[0].get("codigo"))
    if pto_lum: add("INSTALACIONES ELÉCTRICAS","Puntos iluminación (RETIE)",
                    "Un", round(puntos_e*0.4), pto_lum[0]["precio"], pto_lum[0].get("codigo"))

    pto_af = APU.buscar("punto hidráulico agua fría", "INSTALACIONES HIDRÁULICAS", region, 1)
    pto_san = APU.buscar("punto sanitario", "INSTALACIONES SANITARIAS", region, 1)
    if pto_af: add("INSTALACIONES HIDRÁULICAS","Puntos hidráulicos (NTC 1500)",
                   "Un", puntos_h, pto_af[0]["precio"], pto_af[0].get("codigo"))
    if pto_san: add("INSTALACIONES SANITARIAS","Puntos sanitarios (NTC 1500)",
                    "Un", puntos_h, pto_san[0]["precio"], pto_san[0].get("codigo"))

    return items


async def calcular_presupuesto(
    elementos, region="bogota", fc_mpa=20.7, fy_mpa=420.0,
    incluir_iva=True, incluir_aiu=True, porcentaje_aiu=28.0
) -> PresupuestoResponse:

    items = await generar_items(elementos, region, fc_mpa, fy_mpa)
    ri = APU.get_region_info(region)
    subtotal = sum(i.precio_total for i in items)
    aiu_v = round(subtotal * porcentaje_aiu / 100) if incluir_aiu else 0
    base = subtotal + aiu_v
    iva_v = round(base * 0.19) if incluir_iva else 0
    total = base + iva_v

    area_losa = next((el.area_m2 or 0 for el in elementos if el.tipo == "losa"), None)
    tiene_metal = any(_es_metalica(el) for el in elementos)

    # -- Modulo E: APU desglosado material/MO/equipo --------------------------
    desglose = None
    try:
        from app.services.apu_desglose import desglosar_presupuesto
        items_dict = [{"categoria": it.capitulo if hasattr(it, 'capitulo') else getattr(it, 'categoria', 'OTROS'),
                       "precio_total": it.precio_total if hasattr(it, 'precio_total') else getattr(it, 'subtotal', 0)}
                      for it in items]
        desglose = desglosar_presupuesto(items_dict)
    except Exception as e:
        logger.warning(f"Desglose APU fallo: {e}")

    # -- Modulo D: Flete por distancia ------------------------------------------
    flete_info = None
    try:
        from app.services.flete_service import calcular_factor_flete
        tipo_est = "estructura_metalica" if tiene_metal else "concreto_reforzado"
        flete_info = calcular_factor_flete(region, tipo_estructura=tipo_est)
        if flete_info.get("factor_flete", 1.0) > 1.0:
            notas.append(
                f"FLETE: {flete_info['nota']} — factor {flete_info['factor_flete']} "
                f"sobre materiales (~{flete_info.get('recargo_materiales_pct', 0)}% recargo)"
            )
    except Exception as e:
        logger.warning(f"Flete fallo: {e}")

    return PresupuestoResponse(
        items=items, region=ri["nombre"],
        desglose_apu=desglose, flete=flete_info,
        fc_concreto=f"{fc_mpa} MPa", fecha=datetime.now().strftime("%Y-%m-%d %H:%M"),
        fuente_precios="APU 2026 — Escuela de Contratistas",
        resumen=ResumenFinanciero(
            subtotal_directo=subtotal, aiu=aiu_v, subtotal_con_aiu=base,
            iva=iva_v, total=total,
            costo_m2=round(total/area_losa) if area_losa else None,
            area_ref_m2=area_losa, porcentaje_aiu=porcentaje_aiu,
            porcentaje_iva=19.0 if incluir_iva else 0.0
        ),
        notas=notas + [
            f"BD: APU 2026 Escuela de Contratistas ({len(APU.load_apu_db())} actividades)",
            f"Región: {ri['nombre']} — Factor: ×{ri['factor']:.2f}",
            f"f'c concreto: {fc_mpa} MPa | fy acero: {fy_mpa} MPa",
            "Estructura metálica: precio incluye suministro + montaje + pintura (ítem 5.29 APU)",
            "Adicionales metálica: tornillería 1.5%, soldadura 2.0%, platinería 4.0%",
            "Sandblasting y pintura anticorrosiva incluida en ítem separado (5.28)",
            f"AIU {porcentaje_aiu}% = Administración 15% + Imprevistos 5% + Utilidad 8%",
            "IVA 19% sobre base con AIU — ET Art. 468",
            "Norma: NSR-10 | ASTM A500 (perfiles tubulares) | AISC (conexiones)",
            "AVISO: Presupuesto preliminar. Validar con memoria de cálculo y cotizaciones.",
        ],
        correcciones=[], alertas_tecnicas=[]
    )
