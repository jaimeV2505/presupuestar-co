# -*- coding: utf-8 -*-
"""
Modulo D — Flete por distancia obra-proveedor.

En Colombia el flete puede representar 5-50% del costo de materiales
segun la distancia al centro de distribucion mas cercano.

Datos base: SICE-TAC MinTransporte (costos de operacion vehicular)
+ factores empiricos de obra por region.
"""
import math
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Distancia aproximada (km por carretera) desde el centro de distribucion
# de materiales mas cercano (Bogota, Medellin, Cali, Barranquilla, B/manga)
# a la capital de cada departamento
DISTANCIAS_CENTRO_DISTRIBUCION = {
    # Ciudad: (km al centro mas cercano, centro, condicion via)
    "bogota":         (0,    "Bogota",       "buena"),
    "medellin":       (0,    "Medellin",     "buena"),
    "cali":           (0,    "Cali",         "buena"),
    "barranquilla":   (0,    "Barranquilla", "buena"),
    "bucaramanga":    (0,    "Bucaramanga",  "buena"),
    "cartagena":      (120,  "Barranquilla", "buena"),
    "santa_marta":    (100,  "Barranquilla", "buena"),
    "pereira":        (200,  "Medellin",     "buena"),
    "manizales":      (190,  "Medellin",     "regular"),
    "armenia":        (280,  "Cali",         "buena"),
    "ibague":         (200,  "Bogota",       "buena"),
    "villavicencio":  (110,  "Bogota",       "regular"),
    "neiva":          (300,  "Bogota",       "regular"),
    "pasto":          (380,  "Cali",         "mala"),
    "popayan":        (140,  "Cali",         "regular"),
    "cucuta":         (200,  "Bucaramanga",  "regular"),
    "monteria":       (320,  "Barranquilla", "regular"),
    "sincelejo":      (200,  "Barranquilla", "buena"),
    "valledupar":     (300,  "Barranquilla", "buena"),
    "riohacha":       (270,  "Barranquilla", "regular"),
    "tunja":          (140,  "Bogota",       "buena"),
    "yopal":          (340,  "Bogota",       "regular"),
    "arauca":         (610,  "Bucaramanga",  "mala"),
    "florencia":      (500,  "Bogota",       "mala"),
    "mocoa":          (560,  "Cali",         "mala"),
    "quibdo":         (230,  "Medellin",     "mala"),
    "san_andres":     (999,  "Cartagena",    "maritimo"),
    "leticia":        (999,  "Bogota",       "aereo_fluvial"),
    "mitu":           (999,  "Bogota",       "aereo"),
    "puerto_carreno": (999,  "Bogota",       "aereo_fluvial"),
    "inirida":        (999,  "Bogota",       "aereo_fluvial"),
    "san_jose_guaviare": (400, "Bogota",     "mala"),
}

# Costo de flete terrestre por ton-km (COP 2026, base SICE-TAC)
COSTO_TON_KM = {
    "buena":   350,    # via pavimentada en buen estado
    "regular": 480,    # via mixta o montanosa
    "mala":    680,    # via destapada o de alta montana
}

# Recargos para zonas sin acceso terrestre (% sobre el precio del material)
RECARGO_ZONAS_ESPECIALES = {
    "maritimo":       0.35,   # San Andres: barco desde Cartagena
    "aereo":          0.90,   # Mitu: solo aereo
    "aereo_fluvial":  0.55,   # Leticia, Puerto Carreno: rio + avion
}

# Peso aproximado de materiales por unidad de presupuesto (para calcular flete)
PESO_MATERIAL_TON = {
    "concreto_m3": 2.4,      # 1 m3 de concreto = 2.4 ton
    "acero_kg": 0.001,       # 1 kg = 0.001 ton
    "cemento_saco": 0.05,    # saco 50kg
    "arena_m3": 1.6,
    "grava_m3": 1.7,
    "ladrillo_und": 0.003,
    "teja_m2": 0.012,
}

# Porcentaje del presupuesto que corresponde a materiales transportables
# (el resto es mano de obra local que no paga flete)
PCT_MATERIAL_TRANSPORTABLE = {
    "concreto_reforzado": 0.55,
    "estructura_metalica": 0.65,
    "mamposteria": 0.60,
    "default": 0.50,
}


def calcular_factor_flete(
    region: str,
    distancia_adicional_km: float = 0,
    tipo_estructura: str = "default"
) -> Dict:
    """
    Calcula el factor de flete para una obra.

    region: ciudad o municipio (usa tabla de distancias)
    distancia_adicional_km: km adicionales desde la capital hasta la obra
        (ej: obra rural a 45km de Villavicencio)
    tipo_estructura: para estimar % de materiales transportables

    Retorna factor multiplicador sobre el costo de materiales.
    """
    region_key = region.lower().replace(" ", "_").replace(".", "").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")

    data = DISTANCIAS_CENTRO_DISTRIBUCION.get(region_key)
    if not data:
        # Region desconocida: asumir 150km via regular
        data = (150, "desconocido", "regular")
        logger.warning(f"Region '{region}' no encontrada, usando 150km regular")

    km_base, centro, condicion = data

    # Zonas especiales (sin acceso terrestre)
    if condicion in RECARGO_ZONAS_ESPECIALES:
        recargo = RECARGO_ZONAS_ESPECIALES[condicion]
        pct_mat = PCT_MATERIAL_TRANSPORTABLE.get(tipo_estructura, 0.50)
        factor_total = 1 + (recargo * pct_mat)
        return {
            "region": region,
            "centro_distribucion": centro,
            "modo_transporte": condicion,
            "recargo_materiales_pct": round(recargo * 100, 1),
            "factor_flete": round(factor_total, 3),
            "nota": f"Zona sin acceso terrestre — materiales via {condicion.replace('_', '/')}. "
                    f"Recargo {recargo*100:.0f}% sobre materiales.",
            "requiere_cotizacion_especial": True,
        }

    # Flete terrestre normal
    km_total = km_base + distancia_adicional_km

    if km_total <= 30:
        # Dentro del area metropolitana: flete ya incluido en precios base
        return {
            "region": region,
            "centro_distribucion": centro,
            "km_total": km_total,
            "factor_flete": 1.0,
            "nota": "Area metropolitana — flete incluido en precios base",
            "requiere_cotizacion_especial": False,
        }

    # Costo por ton-km segun condicion de via
    costo_ton_km = COSTO_TON_KM.get(condicion, 480)

    # Estimacion: para una obra tipica, el material transportable pesa
    # aprox 1.2 ton por cada millon COP de presupuesto de materiales
    # Flete por millon COP de material = 1.2 ton * km * costo_ton_km
    flete_por_millon = 1.2 * km_total * costo_ton_km
    pct_recargo_material = flete_por_millon / 1_000_000

    # Aplicar solo al % de materiales transportables
    pct_mat = PCT_MATERIAL_TRANSPORTABLE.get(tipo_estructura, 0.50)
    factor_total = 1 + (pct_recargo_material * pct_mat)

    # Limitar a maximo 50% de recargo (mas alla requiere cotizacion real)
    factor_total = min(factor_total, 1.50)

    return {
        "region": region,
        "centro_distribucion": centro,
        "km_total": km_total,
        "condicion_via": condicion,
        "costo_ton_km": costo_ton_km,
        "recargo_materiales_pct": round(pct_recargo_material * 100, 1),
        "factor_flete": round(factor_total, 3),
        "nota": f"{km_total:.0f}km desde {centro} por via {condicion} "
                f"(~{costo_ton_km} COP/ton-km)",
        "requiere_cotizacion_especial": km_total > 400,
    }


def get_regiones_disponibles() -> Dict:
    """Lista todas las regiones con sus datos de flete."""
    out = {}
    for k, (km, centro, cond) in DISTANCIAS_CENTRO_DISTRIBUCION.items():
        out[k] = {
            "km_a_centro": km if km < 999 else "sin acceso terrestre",
            "centro_distribucion": centro,
            "condicion": cond,
        }
    return out
