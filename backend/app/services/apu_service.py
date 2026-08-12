"""
Servicio BD APU 2026 — Escuela de Contratistas.
v4: BD completa perfiles NTC/ACESCO (~200 perfiles), motor de búsqueda mejorado.
"""
import json, logging, re, os
from typing import List, Dict, Optional
logger = logging.getLogger(__name__)

FACTORES_REGION = {
    "bogota":       {"nombre":"Bogotá D.C.",           "factor":1.00},
    "medellin":     {"nombre":"Medellín / Antioquia",  "factor":0.93},
    "cali":         {"nombre":"Cali / Valle del Cauca","factor":0.89},
    "barranquilla": {"nombre":"Barranquilla",          "factor":0.96},
    "bucaramanga":  {"nombre":"Bucaramanga",           "factor":0.91},
    "pereira":      {"nombre":"Pereira",               "factor":0.87},
    "manizales":    {"nombre":"Manizales",             "factor":0.86},
    "cartagena":    {"nombre":"Cartagena",             "factor":0.94},
    "cucuta":       {"nombre":"Cúcuta",                "factor":0.85},
    "ibague":       {"nombre":"Ibagué",                "factor":0.88},
    "villavicencio":{"nombre":"Villavicencio",         "factor":0.84},
    "monteria":     {"nombre":"Montería",              "factor":0.86},
    "pasto":        {"nombre":"Pasto",                 "factor":0.85},
}

# ══════════════════════════════════════════════════════════════════════════════
# BD COMPLETA DE PERFILES METÁLICOS — NTC 2500, ASTM A500/A36/A572
# Fuente: Catálogo ACESCO, Steelcol, Corpacero, tablas AISC/NTC
# Unidad: kg/m (peso lineal)
# ══════════════════════════════════════════════════════════════════════════════
PESOS_PERFILES: Dict[str, float] = {

    # ── PTE CUADRADO (Perfil Tubular Estructural cuadrado) ─────────────────
    # Norma: ASTM A500 Gr.C | NTC 2500
    "PTE40x40x2":    2.34,  "PTE40x40x3":    3.41,
    "PTE50x50x2":    2.93,  "PTE50x50x2.5":  3.62,  "PTE50x50x3":   4.29,
    "PTE60x60x2":    3.56,  "PTE60x60x2.5":  4.39,  "PTE60x60x3":   5.19,  "PTE60x60x4":   6.80,
    "PTE70x70x2":    4.18,  "PTE70x70x3":    6.11,  "PTE70x70x4":   7.98,
    "PTE80x80x2":    4.82,  "PTE80x80x2.5":  5.97,  "PTE80x80x3":   7.10,  "PTE80x80x4":   9.30,  "PTE80x80x5":  11.40,
    "PTE90x90x3":    8.06,  "PTE90x90x4":   10.60,  "PTE90x90x5":   13.00,
    "PTE100x100x2":  6.08,  "PTE100x100x2.5":7.54,  "PTE100x100x3": 9.00,  "PTE100x100x3mm":9.20,
    "PTE100x100x4": 11.80,  "PTE100x100x5": 14.60,  "PTE100x100x6": 17.20,
    "PTE120x120x3": 10.90,  "PTE120x120x4": 14.40,  "PTE120x120x5": 17.80,  "PTE120x120x6": 21.00,
    "PTE140x140x4": 17.00,  "PTE140x140x5": 21.00,  "PTE140x140x6": 24.90,  "PTE140x140x8": 32.40,
    "PTE150x150x3": 13.50,  "PTE150x150x4": 18.00,  "PTE150x150x5": 22.30,  "PTE150x150x6": 26.40,  "PTE150x150x8": 34.50,
    "PTE160x160x4": 19.30,  "PTE160x160x5": 23.90,  "PTE160x160x6": 28.40,  "PTE160x160x8": 37.10,
    "PTE180x180x5": 27.20,  "PTE180x180x6": 32.30,  "PTE180x180x8": 42.30,  "PTE180x180x10":52.00,
    "PTE200x200x4": 24.00,  "PTE200x200x5": 29.80,  "PTE200x200x6": 35.50,  "PTE200x200x8": 46.50,  "PTE200x200x10":57.30,
    "PTE220x220x6": 39.30,  "PTE220x220x8": 51.60,  "PTE220x220x10":63.50,
    "PTE250x250x4": 30.00,  "PTE250x250x4.5":33.80, "PTE250x250x5": 37.60,  "PTE250x250x6": 44.80,
    "PTE250x250x8": 59.00,  "PTE250x250x9": 68.34,  "PTE250x250x9mm":68.34, "PTE250x250x10":72.80,  "PTE250x250x12":86.80,
    "PTE300x300x6": 53.70,  "PTE300x300x8": 71.20,  "PTE300x300x10":88.30,  "PTE300x300x12":105.00,
    "PTE350x350x8": 83.80,  "PTE350x350x10":104.00, "PTE350x350x12":124.00,
    "PTE400x400x10":119.00, "PTE400x400x12":142.00, "PTE400x400x16":188.00,

    # ── PTE RECTANGULAR (Perfil Tubular Estructural rectangular) ──────────
    "PTE60x40x2":    2.93,  "PTE60x40x3":    4.29,
    "PTE80x40x2":    3.56,  "PTE80x40x3":    5.19,  "PTE80x40x4":   6.80,
    "PTE80x60x2":    4.20,  "PTE80x60x3":    6.11,  "PTE80x60x4":   7.98,
    "PTE100x50x2":   4.43,  "PTE100x50x2.5": 5.47,  "PTE100x50x3":  6.48,  "PTE100x50x4":   8.49,
    "PTE100x60x2":   4.82,  "PTE100x60x3":   7.10,  "PTE100x60x4":  9.30,
    "PTE120x60x2":   5.42,  "PTE120x60x3":   7.93,  "PTE120x60x4": 10.40,
    "PTE120x80x3":   8.74,  "PTE120x80x4":  11.50,  "PTE120x80x5": 14.20,
    "PTE150x50x2":   5.82,  "PTE150x50x3":   8.57,  "PTE150x50x4": 11.20,
    "PTE150x100x4": 14.40,  "PTE150x100x5": 17.80,  "PTE150x100x6": 21.00,
    "PTE200x100x4": 17.90,  "PTE200x100x5": 22.10,  "PTE200x100x6": 26.20,
    "PTE200x150x5": 24.80,  "PTE200x150x6": 29.50,  "PTE200x150x8": 38.70,
    "PTE250x150x6": 34.30,  "PTE250x150x8": 45.10,  "PTE250x150x10":55.60,
    "PTE300x150x6": 39.30,  "PTE300x150x8": 51.80,  "PTE300x200x8": 59.20,  "PTE300x200x10":73.40,

    # ── PHR / CANAL C (Perfil tipo C laminado en frío) ────────────────────
    # Norma: NTC 2086 | ASTM A653
    "PHR60x20x1.5":  1.40,  "PHR60x20x2":    1.88,
    "PHR80x30x1.5":  1.80,  "PHR80x30x2":    2.38,  "PHR80x30x2.5":  2.93,
    "PHR100x40x1.5": 2.20,  "PHR100x40x2":   2.93,  "PHR100x40x2.5": 3.62,  "PHR100x40x3":   4.29,
    "PHR120x50x2":   3.41,  "PHR120x50x2.5": 4.23,  "PHR120x50x3":   5.05,
    "PHR140x50x2":   3.75,  "PHR140x50x2.5": 4.65,  "PHR140x50x3":   5.55,
    "PHR160x60x1.5": 3.56,  "PHR160x60x2":   4.50,  "PHR160x60x2mm": 4.50,
                             "PHR160x60x2.5": 5.59,  "PHR160x60x3":   6.65,
    "PHR180x70x2":   5.10,  "PHR180x70x2.5": 6.33,  "PHR180x70x3":   7.56,
    "PHR200x75x2":   5.55,  "PHR200x75x2.5": 6.89,  "PHR200x75x3":   8.23,
    "PHR203x67x2":   6.85,  "PHR203x67x2.5": 7.03,  "PHR203x67x3":   8.47,
    "PHR220x80x2.5": 7.68,  "PHR220x80x3":   9.18,
    "PHR250x85x2.5": 8.71,  "PHR250x85x3":  10.41,  "PHR250x85x4":  13.70,
    "PHR300x90x3":  12.40,  "PHR300x90x4":  16.40,
    "PHR355x110x2":  9.50,  "PHR355x110x2mm":9.50,  "PHR355x110x2.5":11.83, "PHR355x110x3":  14.10,

    # ── PHR CAJÓN (Canal doble / cajón soldado) ────────────────────────────
    "PHRCAJON100x50x2":   5.86,  "PHRCAJON100x50x2.5":  7.25,
    "PHRCAJON120x60x2":   7.03,  "PHRCAJON120x60x2.5":  8.71,
    "PHRCAJON160x60x2":   8.15,  "PHRCAJON160x60x2.5": 10.10,  "PHRCAJON160x60x3": 12.00,
    "PHRCAJON200x67x2.5":12.65,  "PHRCAJON200x67x3":   15.10,
    "PHRCAJON355x110x2": 19.00,  "PHRCAJON355x110x2.5":23.66,

    # ── ÁNGULOS (L) ────────────────────────────────────────────────────────
    # Norma: NTC 1920 | ASTM A36
    # Formato: ANGULOAxBxt donde A=ala1 B=ala2 t=espesor (mm)
    'ANGULO1x1x1/8':  0.72,  'ANGULO1x1x3/16':  1.07,  'ANGULO1x1x1/4':  1.40,
    'ANGULO1.25x1.25x1/8': 0.90, 'ANGULO1.25x1.25x3/16': 1.36, 'ANGULO1.25x1.25x1/4': 1.78,
    'ANGULO1-1/4"x1/8':  1.54,  # notación alternativa colombiana
    'ANGULO1.5x1.5x1/8':  1.09,  'ANGULO1.5x1.5x3/16':  1.61,  'ANGULO1.5x1.5x1/4':  2.12,
    'ANGULO2x2x1/8':    1.46,  'ANGULO2x2x3/16':   2.16,  'ANGULO2x2x1/4':   2.84,  'ANGULO2x2x5/16': 3.51,
    'ANGULO2.5x2.5x3/16': 2.72, 'ANGULO2.5x2.5x1/4': 3.59, 'ANGULO2.5x2.5x5/16': 4.44,
    'ANGULO3x3x1/4':    4.36,  'ANGULO3x3x5/16':   5.37,  'ANGULO3x3x3/8':   6.37,  'ANGULO3x3x1/2': 8.30,
    'ANGULO3.5x3.5x1/4': 5.12, 'ANGULO3.5x3.5x5/16': 6.31, 'ANGULO3.5x3.5x3/8': 7.49,
    'ANGULO4x4x1/4':    5.84,  'ANGULO4x4x5/16':   7.21,  'ANGULO4x4x3/8':   8.55,  'ANGULO4x4x1/2': 11.20,
    'ANGULO5x5x5/16':   9.12,  'ANGULO5x5x3/8':   10.80,  'ANGULO5x5x1/2':  14.30,
    'ANGULO6x6x3/8':   13.00,  'ANGULO6x6x1/2':   17.20,  'ANGULO6x6x5/8':  21.30,
    # Ángulos métricos (mm)
    'ANGULO25x25x3':    1.12,  'ANGULO25x25x4':    1.46,
    'ANGULO30x30x3':    1.36,  'ANGULO30x30x4':    1.78,
    'ANGULO40x40x3':    1.84,  'ANGULO40x40x4':    2.42,  'ANGULO40x40x5':   2.97,
    'ANGULO50x50x4':    3.06,  'ANGULO50x50x5':    3.77,  'ANGULO50x50x6':   4.47,
    'ANGULO60x60x5':    4.57,  'ANGULO60x60x6':    5.42,  'ANGULO60x60x8':   7.09,
    'ANGULO70x70x6':    6.38,  'ANGULO70x70x7':    7.38,  'ANGULO70x70x8':   8.36,
    'ANGULO80x80x6':    7.34,  'ANGULO80x80x8':    9.63,  'ANGULO80x80x10': 11.90,
    'ANGULO100x100x8': 12.20,  'ANGULO100x100x10':15.10,  'ANGULO100x100x12':17.80,
    'ANGULO120x120x10':18.20,  'ANGULO120x120x12':21.60,
    'ANGULO150x150x12':26.80,  'ANGULO150x150x15':33.10,

    # ── PERFILES I AMERICANOS (W-shapes) ──────────────────────────────────
    # Norma: ASTM A992 | AISC
    "W4x13":   19.4,  "W5x16":   23.8,  "W5x19":   28.3,
    "W6x9":    13.4,  "W6x12":   17.9,  "W6x15":   22.3,  "W6x20":  29.8,  "W6x25":  37.2,
    "W8x10":   14.9,  "W8x13":   19.4,  "W8x15":   22.3,  "W8x18":  26.8,  "W8x21":  31.3,
    "W8x24":   35.7,  "W8x28":   41.7,  "W8x31":   46.2,  "W8x35":  52.1,  "W8x40":  59.6,
    "W10x12":  17.9,  "W10x15":  22.3,  "W10x17":  25.3,  "W10x19": 28.3,  "W10x22": 32.7,
    "W10x26":  38.7,  "W10x30":  44.6,  "W10x33":  49.1,  "W10x39": 58.1,  "W10x45": 67.0,
    "W12x14":  20.9,  "W12x16":  23.8,  "W12x19":  28.3,  "W12x22": 32.7,  "W12x26": 38.7,
    "W12x30":  44.6,  "W12x35":  52.1,  "W12x40":  59.6,  "W12x45": 67.0,  "W12x50": 74.4,
    "W14x22":  32.7,  "W14x26":  38.7,  "W14x30":  44.6,  "W14x34": 50.6,  "W14x38": 56.6,
    "W14x43":  64.0,  "W14x48":  71.4,  "W14x53":  78.9,  "W14x61": 90.8,  "W14x68":101.2,
    "W16x26":  38.7,  "W16x31":  46.2,  "W16x36":  53.6,  "W16x40": 59.6,  "W16x45": 67.0,
    "W18x35":  52.1,  "W18x40":  59.6,  "W18x46":  68.5,  "W18x50": 74.4,  "W18x55": 81.9,
    "W21x44":  65.5,  "W21x50":  74.4,  "W21x57":  84.9,  "W21x62": 92.3,  "W21x68":101.2,
    "W24x55":  81.9,  "W24x62":  92.3,  "W24x68": 101.2,  "W24x76":113.1,  "W24x84":125.0,

    # ── PERFILES IPE / HEA / HEB (europeos, usados en Colombia) ──────────
    # Norma: EN 10034
    "IPE80":   6.00,  "IPE100":   8.10,  "IPE120":  10.40,  "IPE140":  12.90,  "IPE160":  15.80,
    "IPE180":  18.80, "IPE200":  22.40,  "IPE220":  26.20,  "IPE240":  30.70,  "IPE270":  36.10,
    "IPE300":  42.20, "IPE330":  49.10,  "IPE360":  57.10,  "IPE400":  66.30,  "IPE450":  77.60,
    "HEA100":  16.70, "HEA120":  19.90,  "HEA140":  24.70,  "HEA160":  30.40,  "HEA180":  35.50,
    "HEA200":  42.30, "HEA220":  50.50,  "HEA240":  60.30,  "HEA260":  68.20,  "HEA280":  76.40,
    "HEB100":  20.40, "HEB120":  26.70,  "HEB140":  33.70,  "HEB160":  42.60,  "HEB180":  51.20,
    "HEB200":  61.30, "HEB220":  71.50,  "HEB240":  83.20,  "HEB260":  93.00,  "HEB280": 103.10,

    # ── TENSORES / VARILLAS LISAS ──────────────────────────────────────────
    "VARILLA_LISA_1/4":  0.25,  "VARILLA_LISA_3/8":  0.56,
    "VARILLA_LISA_1/2":  1.00,  "VARILLA_LISA_5/8":  1.55,
    "VARILLA_LISA_3/4":  2.24,  "VARILLA_LISA_7/8":  3.04,
    "VARILLA_LISA_1":    4.00,

    # ── LÁMINAS / PLANCHAS (kg/m² — se multiplica por área) ───────────────
    # Se identifican aparte por unidad diferente
    "LAMINA_PL3":   23.55,  "LAMINA_PL4":   31.40,  "LAMINA_PL5":   39.25,
    "LAMINA_PL6":   47.10,  "LAMINA_PL8":   62.80,  "LAMINA_PL10":  78.50,
    "LAMINA_PL12":  94.20,  "LAMINA_PL16": 125.60,  "LAMINA_PL20": 157.00,

    # ── RIOSTRAS / CABLES ──────────────────────────────────────────────────
    "RIOSTRA_1/2":   1.00,  "RIOSTRA_5/8":   1.55,  "RIOSTRA_3/4":   2.24,
    "CABLE_1/4":     0.18,  "CABLE_3/8":     0.40,  "CABLE_1/2":     0.72,
}

# ── Normalización de nombres de perfiles ──────────────────────────────────────
def _normalize_perfil(nombre: str) -> str:
    """Normaliza el nombre de un perfil para búsqueda robusta."""
    if not nombre:
        return ""
    n = nombre.upper().strip()
    # Coma decimal → punto (planos colombianos usan coma: 2,5 → 2.5)
    n = re.sub(r'(\d),(\d)', r'\1.\2', n)
    # Remover espacios alrededor de x y entre número y unidad
    n = re.sub(r'\s*[xX×]\s*', 'x', n)
    n = re.sub(r'\s*(MM|mm)\s*$', '', n)
    n = re.sub(r'\s+', '', n)
    # Normalizar separadores de cajón
    n = n.replace('CAJON', 'CAJON').replace('CAJÓN', 'CAJON')
    # PHR C → PHR
    n = re.sub(r'^PHRC(\d)', r'PHR\1', n)
    n = re.sub(r'^PHR\s*C\s*', 'PHR', n)
    return n


def get_peso_perfil(nombre_perfil: str) -> Optional[float]:
    """
    Busca el peso unitario (kg/m) de un perfil metálico.
    Estrategia: exacto → normalizado → fuzzy por dimensiones.
    """
    if not nombre_perfil:
        return None

    n_orig = nombre_perfil.strip()
    n_norm = _normalize_perfil(n_orig)

    # 1. Búsqueda exacta
    if n_orig in PESOS_PERFILES:
        return PESOS_PERFILES[n_orig]
    if n_norm in PESOS_PERFILES:
        return PESOS_PERFILES[n_norm]

    # 2. Búsqueda normalizada en todas las claves
    for key, peso in PESOS_PERFILES.items():
        k_norm = _normalize_perfil(key)
        if k_norm == n_norm:
            return peso

    # 3. Búsqueda parcial — el nombre contiene la clave o viceversa
    for key, peso in PESOS_PERFILES.items():
        k_norm = _normalize_perfil(key)
        if k_norm in n_norm or n_norm in k_norm:
            return peso

    # 4. Extracción de dimensiones y búsqueda por tipo + dims
    tipo = ""
    if "PTE" in n_norm:    tipo = "PTE"
    elif "PHR" in n_norm:  tipo = "PHR"
    elif "ANGULO" in n_norm or "ANG" in n_norm: tipo = "ANGULO"
    elif n_norm.startswith("W"):   tipo = "W"
    elif n_norm.startswith("IPE"): tipo = "IPE"
    elif n_norm.startswith("HEA"): tipo = "HEA"
    elif n_norm.startswith("HEB"): tipo = "HEB"

    if tipo:
        nums = re.findall(r'(\d+(?:\.\d+)?)', n_norm)
        if nums and len(nums) >= 2:
            # Buscar el perfil más cercano del mismo tipo
            mejor_key = None
            mejor_diff = float('inf')
            d1, d2 = float(nums[0]), float(nums[1])
            for key, peso in PESOS_PERFILES.items():
                if not key.startswith(tipo):
                    continue
                k_nums = re.findall(r'(\d+(?:\.\d+)?)', _normalize_perfil(key))
                if len(k_nums) >= 2:
                    diff = abs(float(k_nums[0]) - d1) + abs(float(k_nums[1]) - d2)
                    if diff < mejor_diff:
                        mejor_diff = diff
                        mejor_key = key
            if mejor_key and mejor_diff < 30:  # tolerancia razonable en mm
                logger.info(f"Perfil '{nombre_perfil}' → aproximado a '{mejor_key}' (diff={mejor_diff})")
                return PESOS_PERFILES[mejor_key]

    # Detección especial: tensores y varillas lisas
    # "Tensor varilla lisa 5/8\"" → VARILLA_LISA_5/8 → 1.55 kg/m
    n_check = nombre_perfil.upper()
    if any(t in n_check for t in ["TENSOR", "VARILLA LISA", "V. LISA", "BARRA LISA"]):
        fracciones = re.findall(r'(\d+/\d+)', n_check)
        for frac in fracciones:
            key = f"VARILLA_LISA_{frac}"
            if key in PESOS_PERFILES:
                logger.info(f"Tensor/varilla lisa detectada: '{nombre_perfil}' → {key}")
                return PESOS_PERFILES[key]
        # Buscar por pulgada directa "5/8", "3/4", etc.
        for key, peso in PESOS_PERFILES.items():
            if "VARILLA_LISA" in key:
                frac = key.split("_")[-1]
                if frac in n_check:
                    return peso

    logger.warning(f"Perfil no encontrado en BD: '{nombre_perfil}'")
    return None


def get_precio_perfil_metalico(perfil: str, region: str = "bogota") -> Optional[Dict]:
    """Precio APU para perfil metálico — por metro si existe en BD, sino por kg."""
    f = _factor(region)
    db = load_apu_db()
    p_upper = perfil.upper()

    # Buscar por perfil C en la BD APU ($/m)
    if "PHR" in p_upper or "CANAL" in p_upper:
        dims = re.findall(r'(\d+)', perfil)
        if len(dims) >= 2:
            h, b = dims[0], dims[1]
            t = dims[2] if len(dims) > 2 else "2"
            for item in db:
                if (item["categoria"] == "ESTRUCTURA METÁLICA" and
                    f"C {h}x{b}x{t}" in item["descripcion"]):
                    return {**item, "precio": round(item["precio"] * f), "unidad_base": "m"}

    # Fallback: precio por kg instalado (incluye suministro + montaje + pintura)
    item_kg = get_precio("5.29", region)
    if item_kg:
        return {**item_kg, "unidad_base": "kg"}
    return None


# ── BD APU 2026 ───────────────────────────────────────────────────────────────
_APU_DB: List[Dict] = []

def load_apu_db() -> List[Dict]:
    global _APU_DB
    if _APU_DB:
        return _APU_DB
    db_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "../data/apu_2026.json"))
    with open(db_path, encoding="utf-8") as f:
        _APU_DB = json.load(f)
    logger.info(f"BD APU 2026: {len(_APU_DB)} actividades | Perfiles NTC: {len(PESOS_PERFILES)}")
    return _APU_DB

def _factor(region: str) -> float:
    return FACTORES_REGION.get(region, FACTORES_REGION["bogota"])["factor"]

def get_precio(codigo: str, region: str = "bogota") -> Optional[Dict]:
    db = load_apu_db(); f = _factor(region)
    for item in db:
        if item["codigo"] == codigo:
            return {**item, "precio": round(item["precio"] * f)}
    return None

def _sin_tildes(s: str) -> str:
    import unicodedata
    return "".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn").lower()


def buscar(query: str, categoria: str = None, region: str = "bogota", limit: int = 10) -> List[Dict]:
    db = load_apu_db(); f = _factor(region); q = _sin_tildes(query)
    results = []
    for item in db:
        if categoria and item["categoria"] != categoria:
            continue
        if q in _sin_tildes(item["descripcion"]) or q in _sin_tildes(item.get("categoria", "")):
            results.append({**item, "precio": round(item["precio"] * f)})
    return results[:limit]

def _mpa_str(fc: float) -> str:
    if fc <= 18:    return "17.2 MPa"
    if fc <= 21.5:  return "20.7 MPa"
    if fc <= 25:    return "24.2 MPa"
    return "27.6 MPa"

def buscar_columna(ancho_m, alto_m, fc_mpa=20.7, region="bogota"):
    db = load_apu_db(); f = _factor(region); fc_str = _mpa_str(fc_mpa)
    a, b = sorted([round(ancho_m,2), round(alto_m,2)])
    secciones = [(0.25,0.25),(0.25,0.30),(0.30,0.30),(0.30,0.60),(0.35,0.35),
                 (0.35,0.40),(0.35,0.50),(0.40,0.40),(0.40,0.50),(0.40,0.60),
                 (0.45,0.50),(0.50,0.50),(0.50,0.60),(0.60,0.60)]
    mejor = min(secciones, key=lambda s: abs(s[0]-a)+abs(s[1]-b))
    sa, sb = mejor
    for item in db:
        if (item["categoria"] == "ESTRUCTURAS EN CONCRETO" and
            f"Columna en concreto de {fc_str}" in item["descripcion"] and
            f"{sa:.2f}x{sb:.2f}" in item["descripcion"]):
            return {**item, "precio": round(item["precio"]*f),
                    "seccion_usada": f"{sa:.2f}x{sb:.2f}m",
                    "ajuste": abs(sa-a)+abs(sb-b) > 0.01}
    return get_precio("4.29", region)

def buscar_viga(ancho_m, alto_m, fc_mpa=20.7, region="bogota"):
    db = load_apu_db(); f = _factor(region); fc_str = _mpa_str(fc_mpa)
    a, b = sorted([round(ancho_m,2), round(alto_m,2)])
    secciones = [(0.25,0.25),(0.25,0.30),(0.25,0.35),(0.25,0.40),
                 (0.30,0.30),(0.30,0.35),(0.30,0.40),(0.30,0.50),(0.35,0.35),(0.40,0.40)]
    mejor = min(secciones, key=lambda s: abs(s[0]-a)+abs(s[1]-b))
    sa, sb = mejor
    for item in db:
        if (item["categoria"] == "ESTRUCTURAS EN CONCRETO" and
            "Viga en concreto" in item["descripcion"] and
            fc_str in item["descripcion"] and
            f"{sa:.2f}x{sb:.2f}" in item["descripcion"]):
            return {**item, "precio": round(item["precio"]*f),
                    "seccion_usada": f"{sa:.2f}x{sb:.2f}m"}
    return get_precio("4.151", region)

def buscar_losa(tipo: str, espesor_m: float, fc_mpa=20.7, region="bogota"):
    db = load_apu_db(); f = _factor(region)
    e_cm = round(espesor_m*100)
    if "maciza" in tipo.lower():
        for e in [10,12,15,20]:
            if abs(e-e_cm) <= 3:
                for item in db:
                    if "Placa maciza" in item["descripcion"] and f"e= 0.{e:02d}" in item["descripcion"]:
                        return {**item, "precio": round(item["precio"]*f)}
    for e in [15,30,40,45,50]:
        if abs(e-e_cm) <= 5:
            for item in db:
                if "Placa aligerada" in item["descripcion"] and f"e= 0.{e:02d}" in item["descripcion"]:
                    return {**item, "precio": round(item["precio"]*f)}
    return get_precio("4.121", region)

def buscar_excavacion(prof_m=1.5, en_roca=False, region="bogota"):
    if en_roca:
        cod = "2.46" if prof_m<=2 else "2.47" if prof_m<=4 else "2.48"
    else:
        cod = "2.55" if prof_m<=2 else "2.56" if prof_m<=4 else "2.57"
    return get_precio(cod, region)

def buscar_relleno(region="bogota"):
    return get_precio("2.73", region)

def buscar_acero(fy_mpa=420, region="bogota"):
    cod = "4.02" if fy_mpa >= 400 else "4.01"
    return get_precio(cod, region)

def buscar_concreto_cimentacion(fc_mpa=20.7, region="bogota"):
    if fc_mpa <= 21:   cod = "4.29"
    elif fc_mpa <= 25: cod = "4.37"
    else:              cod = "4.45"
    item = get_precio(cod, region)
    if item:
        item = dict(item)
        item["precio"] = round(item["precio"] * 0.85)
        item["descripcion"] = f"Concreto f'c={fc_mpa}MPa en cimentación"
    return item

def buscar_caisson(diametro_m, profundidad_m, fc_mpa=20.7, region="bogota"):
    import math
    if profundidad_m <= 2:   exc_cod = "2.15"
    elif profundidad_m <= 4: exc_cod = "2.16"
    elif profundidad_m <= 6: exc_cod = "2.17"
    elif profundidad_m <= 8: exc_cod = "2.18"
    else:                    exc_cod = "2.19"
    vol_m3 = math.pi * (diametro_m/2)**2 * profundidad_m
    conc_cod = "3.19" if fc_mpa<=21 else "3.20" if fc_mpa<=25 else "3.21"
    return {
        "excavacion":  get_precio(exc_cod, region),
        "volumen_m3":  round(vol_m3, 3),
        "concreto":    get_precio(conc_cod, region),
        "acero":       get_precio("4.02", region),
        "kg_acero":    round(vol_m3 * 80),
        "profundidad": profundidad_m,
        "diametro":    diametro_m,
    }

def buscar_muro_contencion(fc_mpa=28, region="bogota"):
    if fc_mpa <= 21:   return get_precio("3.12", region)
    elif fc_mpa <= 25: return get_precio("3.13", region)
    else:              return get_precio("3.14", region)

def buscar_muro_mamposteria(tipo: str, region="bogota"):
    tipo_l = tipo.lower()
    if "drywall" in tipo_l: return get_precio("7.07", region)
    if "estructural" in tipo_l: return get_precio("7.05", region)
    r = buscar("muro ladrillo", "MAMPOSTERÍA", region, 3)
    return r[0] if r else None

def get_region_info(region: str) -> Dict:
    return FACTORES_REGION.get(region, FACTORES_REGION["bogota"])

def get_all_regions() -> List[Dict]:
    return [{"codigo": k, **v} for k, v in FACTORES_REGION.items()]

def get_all_categories() -> List[str]:
    db = load_apu_db(); seen = []
    for item in db:
        if item["categoria"] not in seen: seen.append(item["categoria"])
    return seen

def get_perfiles_stats() -> Dict:
    """Estadísticas de la BD de perfiles."""
    tipos = {}
    for key in PESOS_PERFILES:
        t = key.split("x")[0] if "x" in key else key
        tipos[t] = tipos.get(t, 0) + 1
    return {"total": len(PESOS_PERFILES), "por_tipo": tipos}
