# -*- coding: utf-8 -*-
"""
Modulo E — APU desglosado: material / mano de obra / equipo.

El APU 2026 tiene precio global por actividad. Este modulo aplica
composiciones tipicas por capitulo, calibradas con APUs reales
colombianos (CAMACOL, Construdata, Escuela de Contratistas).

El desglose permite al ingeniero:
- Negociar suministro vs instalacion por separado
- Calcular cuanto material comprar directamente
- Estimar cuadrillas necesarias (MO / jornal = dias-hombre)
- Aplicar el flete SOLO a la porcion de materiales
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Composicion tipica material/MO/equipo por capitulo (suma = 1.0)
# Fuente: promedios de APUs Construdata + CAMACOL 2024-2026
COMPOSICION_POR_CAPITULO = {
    "PRELIMINARES":                        {"material": 0.25, "mano_obra": 0.60, "equipo": 0.15},
    "MOVIMIENTO DE TIERRAS":               {"material": 0.05, "mano_obra": 0.35, "equipo": 0.60},
    "CIMENTACIONES":                       {"material": 0.55, "mano_obra": 0.35, "equipo": 0.10},
    "ESTRUCTURAS EN CONCRETO":             {"material": 0.60, "mano_obra": 0.32, "equipo": 0.08},
    "ESTRUCTURA METALICA":                 {"material": 0.70, "mano_obra": 0.22, "equipo": 0.08},
    "ESTRUCTURA METÁLICA":                 {"material": 0.70, "mano_obra": 0.22, "equipo": 0.08},
    "MAMPOSTERIA":                         {"material": 0.55, "mano_obra": 0.42, "equipo": 0.03},
    "MAMPOSTERÍA":                         {"material": 0.55, "mano_obra": 0.42, "equipo": 0.03},
    "CUBIERTAS":                           {"material": 0.65, "mano_obra": 0.30, "equipo": 0.05},
    "PISOS":                               {"material": 0.60, "mano_obra": 0.37, "equipo": 0.03},
    "PANETES (REVOQUES)":                  {"material": 0.35, "mano_obra": 0.62, "equipo": 0.03},
    "PAÑETES (REVOQUES)":                  {"material": 0.35, "mano_obra": 0.62, "equipo": 0.03},
    "PINTURA":                             {"material": 0.40, "mano_obra": 0.57, "equipo": 0.03},
    "ENCHAPES Y ACCESORIOS":               {"material": 0.60, "mano_obra": 0.38, "equipo": 0.02},
    "CARPINTERIA METALICA":                {"material": 0.68, "mano_obra": 0.28, "equipo": 0.04},
    "CARPINTERÍA METÁLICA":                {"material": 0.68, "mano_obra": 0.28, "equipo": 0.04},
    "CARPINTERIA DE MADERA":               {"material": 0.65, "mano_obra": 0.32, "equipo": 0.03},
    "CARPINTERÍA DE MADERA":               {"material": 0.65, "mano_obra": 0.32, "equipo": 0.03},
    "INSTALACIONES HIDRAULICAS":           {"material": 0.55, "mano_obra": 0.42, "equipo": 0.03},
    "INSTALACIONES HIDRÁULICAS":           {"material": 0.55, "mano_obra": 0.42, "equipo": 0.03},
    "INSTALACIONES SANITARIAS":            {"material": 0.55, "mano_obra": 0.42, "equipo": 0.03},
    "INSTALACIONES ELECTRICAS":            {"material": 0.60, "mano_obra": 0.37, "equipo": 0.03},
    "INSTALACIONES ELÉCTRICAS":            {"material": 0.60, "mano_obra": 0.37, "equipo": 0.03},
    "INSTALACION DE GAS":                  {"material": 0.55, "mano_obra": 0.42, "equipo": 0.03},
    "INSTALACIÓN DE GAS":                  {"material": 0.55, "mano_obra": 0.42, "equipo": 0.03},
    "APARATOS SANITARIOS":                 {"material": 0.80, "mano_obra": 0.18, "equipo": 0.02},
    "CIELOS RASOS":                        {"material": 0.55, "mano_obra": 0.42, "equipo": 0.03},
    "VIDRIOS Y ESPEJOS":                   {"material": 0.72, "mano_obra": 0.26, "equipo": 0.02},
    "OBRAS DE URBANISMO":                  {"material": 0.45, "mano_obra": 0.35, "equipo": 0.20},
    "SISTEMA DE PROTECCION CONTRA INCENDIO": {"material": 0.65, "mano_obra": 0.30, "equipo": 0.05},
    "SISTEMA DE PROTECCIÓN CONTRA INCENDIO": {"material": 0.65, "mano_obra": 0.30, "equipo": 0.05},
    "EQUIPOS ESPECIALES":                  {"material": 0.85, "mano_obra": 0.10, "equipo": 0.05},
    "TANQUE ALMACENAMIENTO AGUA EN CONCRETO": {"material": 0.58, "mano_obra": 0.34, "equipo": 0.08},
    "CONSTRUCCION CON BAMBU (GUADUA)":     {"material": 0.50, "mano_obra": 0.47, "equipo": 0.03},
    "CONSTRUCCIÓN CON BAMBÚ (GUADUA)":     {"material": 0.50, "mano_obra": 0.47, "equipo": 0.03},
    "REMATES":                             {"material": 0.40, "mano_obra": 0.57, "equipo": 0.03},
    "PERSONAL DE ADMINISTRACION":          {"material": 0.00, "mano_obra": 1.00, "equipo": 0.00},
    "PERSONAL DE ADMINISTRACIÓN":          {"material": 0.00, "mano_obra": 1.00, "equipo": 0.00},
    "OTROS":                               {"material": 0.50, "mano_obra": 0.40, "equipo": 0.10},
    "DEFAULT":                             {"material": 0.50, "mano_obra": 0.40, "equipo": 0.10},
}

# Jornal promedio 2026 por region para estimar dias-hombre
JORNAL_DIA_2026 = {
    "oficial": 95000,      # oficial de construccion COP/dia
    "ayudante": 62000,     # ayudante COP/dia
    "cuadrilla_promedio": 78000,  # promedio ponderado 1 oficial + 1 ayudante
}


def desglosar_item(precio_total: float, capitulo: str) -> Dict:
    """
    Desglosa el precio de un item APU en material/MO/equipo
    segun la composicion tipica de su capitulo.
    """
    comp = COMPOSICION_POR_CAPITULO.get(
        capitulo.upper().strip(),
        COMPOSICION_POR_CAPITULO["DEFAULT"]
    )
    return {
        "material": round(precio_total * comp["material"]),
        "mano_obra": round(precio_total * comp["mano_obra"]),
        "equipo": round(precio_total * comp["equipo"]),
        "composicion_pct": {
            "material": round(comp["material"] * 100),
            "mano_obra": round(comp["mano_obra"] * 100),
            "equipo": round(comp["equipo"] * 100),
        }
    }


def desglosar_presupuesto(items: List[Dict]) -> Dict:
    """
    Desglosa el presupuesto completo en material/MO/equipo.
    items: lista con {capitulo/categoria, precio_total o subtotal}

    Retorna totales, desglose por capitulo, y estimacion de cuadrillas.
    """
    total_material = 0
    total_mo = 0
    total_equipo = 0
    por_capitulo = {}

    for item in items:
        cap = (item.get("capitulo") or item.get("categoria") or "OTROS").upper()
        precio = item.get("precio_total") or item.get("subtotal") or 0

        d = desglosar_item(precio, cap)
        total_material += d["material"]
        total_mo += d["mano_obra"]
        total_equipo += d["equipo"]

        if cap not in por_capitulo:
            por_capitulo[cap] = {"material": 0, "mano_obra": 0, "equipo": 0, "total": 0}
        por_capitulo[cap]["material"] += d["material"]
        por_capitulo[cap]["mano_obra"] += d["mano_obra"]
        por_capitulo[cap]["equipo"] += d["equipo"]
        por_capitulo[cap]["total"] += precio

    total = total_material + total_mo + total_equipo

    # Estimacion de dias-hombre de cuadrilla
    dias_cuadrilla = total_mo / JORNAL_DIA_2026["cuadrilla_promedio"] if total_mo > 0 else 0

    return {
        "total_material": total_material,
        "total_mano_obra": total_mo,
        "total_equipo": total_equipo,
        "total": total,
        "pct_material": round(total_material / total * 100, 1) if total else 0,
        "pct_mano_obra": round(total_mo / total * 100, 1) if total else 0,
        "pct_equipo": round(total_equipo / total * 100, 1) if total else 0,
        "por_capitulo": por_capitulo,
        "dias_cuadrilla_estimados": round(dias_cuadrilla),
        "jornal_referencia": JORNAL_DIA_2026,
        "nota": (
            "Desglose por composiciones tipicas de APU colombiano "
            "(CAMACOL/Construdata). Para negociacion final solicitar "
            "APU detallado al contratista."
        ),
    }


def get_composiciones() -> Dict:
    """Retorna la tabla completa de composiciones por capitulo."""
    return {k: v for k, v in COMPOSICION_POR_CAPITULO.items() if k != "DEFAULT"}
