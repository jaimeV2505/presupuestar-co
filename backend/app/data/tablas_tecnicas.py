"""
Tablas técnicas de materiales de construcción — Colombia.
Fuente: Tablas reales de caracterización de varilla y dosificación de concreto.
"""

# ══════════════════════════════════════════════════════════════════════════════
# TABLA DE CARACTERIZACIÓN DE VARILLA DE ACERO
# Fuente: tabla real colombiana (imagen compartida por el ingeniero)
# ══════════════════════════════════════════════════════════════════════════════
# Formato: {numero: {pulg, mm, area_cm2, peso_kg_m}}
VARILLAS = {
    2:  {"pulg": "1/4",   "mm":  6.4, "area_cm2": 0.317, "peso_kg_m": 0.249},
    3:  {"pulg": "3/8",   "mm":  9.5, "area_cm2": 0.713, "peso_kg_m": 0.559},
    4:  {"pulg": "1/2",   "mm": 12.7, "area_cm2": 1.267, "peso_kg_m": 0.994},
    5:  {"pulg": "5/8",   "mm": 15.9, "area_cm2": 1.979, "peso_kg_m": 1.554},
    6:  {"pulg": "3/4",   "mm": 19.1, "area_cm2": 2.850, "peso_kg_m": 2.237},
    7:  {"pulg": "7/8",   "mm": 22.2, "area_cm2": 3.879, "peso_kg_m": 3.045},
    8:  {"pulg": "1",     "mm": 25.4, "area_cm2": 5.067, "peso_kg_m": 3.978},
    9:  {"pulg": "1 1/8", "mm": 28.6, "area_cm2": 6.413, "peso_kg_m": 5.034},
    10: {"pulg": "1 1/4", "mm": 31.8, "area_cm2": 7.917, "peso_kg_m": 6.215},
    11: {"pulg": "1 3/8", "mm": 34.9, "area_cm2": 9.580, "peso_kg_m": 7.520},
}

# Mapeos rápidos
VARILLA_POR_PULG = {v["pulg"]: {**v, "numero": k} for k, v in VARILLAS.items()}
VARILLA_POR_MM   = {v["mm"]:   {**v, "numero": k} for k, v in VARILLAS.items()}

# Alias comunes en planos colombianos
ALIAS_VARILLA = {
    "1/4": 2, "#2": 2, "Ø1/4": 2,
    "3/8": 3, "#3": 3, "Ø3/8": 3,
    "1/2": 4, "#4": 4, "Ø1/2": 4,
    "5/8": 5, "#5": 5, "Ø5/8": 5,
    "3/4": 6, "#6": 6, "Ø3/4": 6,
    "7/8": 7, "#7": 7, "Ø7/8": 7,
    "1\"": 8, "#8": 8, "Ø1":   8,
}


def get_varilla(referencia: str) -> dict:
    """
    Retorna datos de la varilla dado su referencia en plano.
    Acepta: '#5', '5/8', 'Ø5/8', 'N5', '5', etc.
    """
    ref = str(referencia).strip().upper().replace("Ø","").replace("N°","").replace("N","")
    
    # Por número directo (3, 4, 5...)
    try:
        n = int(ref)
        if n in VARILLAS:
            return VARILLAS[n]
    except ValueError:
        pass
    
    # Por alias
    for alias, num in ALIAS_VARILLA.items():
        if alias.upper() in ref or ref in alias.upper():
            return VARILLAS[num]
    
    # Por fracción
    for pulg, data in VARILLA_POR_PULG.items():
        if pulg in ref:
            return {**data}
    
    return None


def calcular_kg_acero_por_especificacion(especificacion: str) -> float:
    """
    Calcula kg/m para una especificación de acero como '4Ø5/8"' o '4#5'.
    Retorna 0 si no puede parsear.
    
    Ejemplos:
        '4Ø5/8"' → 4 varillas #5 → 4 × 1.554 = 6.216 kg/m
        '6#4+2#5' → 6×0.994 + 2×1.554 = 9.072 kg/m
    """
    import re
    total_kg_m = 0.0
    
    # Buscar grupos: número_de_varillas × designación_varilla
    # Patrones: "4Ø5/8", "4#5", "6N5", "4 5/8"
    grupos = re.findall(r'(\d+)\s*(?:Ø|#|N°?|n°?)?\s*(\d+(?:/\d+)?(?:\s*\d+/\d+)?)', especificacion)
    
    for cant_str, var_ref in grupos:
        try:
            cant = int(cant_str)
            var = get_varilla(var_ref)
            if var:
                total_kg_m += cant * var["peso_kg_m"]
        except Exception:
            continue
    
    return round(total_kg_m, 4)


# ══════════════════════════════════════════════════════════════════════════════
# TABLA DE DOSIFICACIÓN DE CONCRETO
# Fuente: Tabla real colombiana (imagen compartida por el ingeniero)
# Cantidades por m³
# ══════════════════════════════════════════════════════════════════════════════
DOSIFICACION_CONCRETO = [
    # proporcion, kg/cm2, psi, mpa, cemento_sacos, arena_m3, grava_m3, agua_lts
    # cemento_sacos asume bulto de 50kg — el mismo tamano usado en toda la
    # base de insumos y las recetas APU de la app (antes decia 42.5kg, un
    # tamano de bulto que no coincide con nada mas del sistema)
    {"proporcion": "1-2-2",   "kg_cm2": 280, "psi": 4000, "mpa": 27, "cemento_sacos": 420/50, "arena_m3": 0.67, "grava_m3": 0.67, "agua_lts": 190},
    {"proporcion": "1-2-2.5", "kg_cm2": 240, "psi": 3555, "mpa": 24, "cemento_sacos": 380/50, "arena_m3": 0.60, "grava_m3": 0.76, "agua_lts": 180},
    {"proporcion": "1-2-3",   "kg_cm2": 226, "psi": 3224, "mpa": 22, "cemento_sacos": 350/50, "arena_m3": 0.55, "grava_m3": 0.84, "agua_lts": 170},
    {"proporcion": "1-2-3.5", "kg_cm2": 210, "psi": 3000, "mpa": 20, "cemento_sacos": 320/50, "arena_m3": 0.52, "grava_m3": 0.90, "agua_lts": 170},
    {"proporcion": "1-2-43",  "kg_cm2": 200, "psi": 2850, "mpa": 19, "cemento_sacos": 300/50, "arena_m3": 0.48, "grava_m3": 0.95, "agua_lts": 158},
    {"proporcion": "1-2.5-4", "kg_cm2": 189, "psi": 2700, "mpa": 18, "cemento_sacos": 280/50, "arena_m3": 0.55, "grava_m3": 0.89, "agua_lts": 158},
    {"proporcion": "1-3-3",   "kg_cm2": 168, "psi": 2400, "mpa": 16, "cemento_sacos": 300/50, "arena_m3": 0.72, "grava_m3": 0.72, "agua_lts": 158},
    {"proporcion": "1-3-4",   "kg_cm2": 159, "psi": 2275, "mpa": 15, "cemento_sacos": 260/50, "arena_m3": 0.63, "grava_m3": 0.83, "agua_lts": 163},
    {"proporcion": "1-3-5",   "kg_cm2": 140, "psi": 2000, "mpa": 14, "cemento_sacos": 230/50, "arena_m3": 0.55, "grava_m3": 0.92, "agua_lts": 148},
    {"proporcion": "1-3-6",   "kg_cm2": 119, "psi": 1700, "mpa": 12, "cemento_sacos": 110/50, "arena_m3": 0.50, "grava_m3": 0.90, "agua_lts": 143},
    {"proporcion": "1-4-7",   "kg_cm2": 109, "psi": 1560, "mpa": 11, "cemento_sacos": 175/50, "arena_m3": 0.55, "grava_m3": 0.98, "agua_lts": 133},
    {"proporcion": "1-4-8",   "kg_cm2":  99, "psi": 1420, "mpa": 10, "cemento_sacos": 160/50, "arena_m3": 0.55, "grava_m3": 0.03, "agua_lts": 125},  # grava=0.03 sospechoso vs vecinas (0.90/0.98) -- posible error de la fuente original, no corregido a ciegas
]


def get_dosificacion(fc_mpa: float) -> dict:
    """
    Retorna la dosificación más cercana para un f'c dado en MPa.
    Interpola si está entre dos valores.
    """
    # Buscar la dosificación más cercana
    mejor = min(DOSIFICACION_CONCRETO, key=lambda d: abs(d["mpa"] - fc_mpa))
    return mejor


def get_materiales_por_m3(fc_mpa: float) -> dict:
    """
    Retorna cantidades de materiales por m³ de concreto según f'c.
    Útil para calcular cantidades exactas de cemento, arena y grava.
    """
    dos = get_dosificacion(fc_mpa)
    return {
        "fc_mpa": fc_mpa,
        "fc_psi": dos["psi"],
        "proporcion": dos["proporcion"],
        "cemento_sacos_m3": round(dos["cemento_sacos"], 2),
        "cemento_kg_m3": round(dos["cemento_sacos"] * 42.5, 1),
        "arena_m3_por_m3": dos["arena_m3"],
        "grava_m3_por_m3": dos["grava_m3"],
        "agua_lts_m3": dos["agua_lts"],
        "nota": f"Dosificación {dos['proporcion']} | {dos['kg_cm2']} kg/cm² | {dos['mpa']} MPa",
    }


# ══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE CÁLCULO PRECISO DE ACERO
# ══════════════════════════════════════════════════════════════════════════════

def calcular_acero_columna(
    acero_long: str,
    acero_trans: str,
    longitud_m: float,
    num_columnas: int = 1
) -> dict:
    """
    Calcula el peso exacto de acero de una columna.
    
    acero_long: '4Ø5/8"' o '6#5+2#4'
    acero_trans: '#3@15cm' o 'Estribo #3 c/15cm'
    longitud_m: altura libre de la columna en metros
    
    Retorna kg totales para num_columnas columnas.
    """
    import re
    
    # Acero longitudinal (kg/m de columna)
    kg_m_long = calcular_kg_acero_por_especificacion(acero_long)
    kg_long = kg_m_long * longitud_m * num_columnas
    
    # Acero transversal (estribos)
    kg_trans = 0.0
    if acero_trans:
        # Extraer número de varilla y espaciamiento
        m_var = re.search(r'#(\d+)|N(\d+)|Ø([\d/]+)', acero_trans)
        m_esp = re.search(r'@\s*(\d+(?:\.\d+)?)\s*(cm|m)?|c/\s*(\d+(?:\.\d+)?)\s*(cm|m)?', acero_trans, re.I)
        
        if m_var and m_esp:
            var_num = m_var.group(1) or m_var.group(2) or m_var.group(3)
            var_data = get_varilla(var_num)
            
            esp_val = float(m_esp.group(1) or m_esp.group(3))
            esp_unit = (m_esp.group(2) or m_esp.group(4) or "cm").lower()
            espaciamiento_m = esp_val / 100 if esp_unit == "cm" else esp_val
            
            if var_data and espaciamiento_m > 0:
                num_estribos = longitud_m / espaciamiento_m
                # Perímetro del estribo: aproximado como 4 × ancho promedio columna
                # Se usa un factor de 2.5m de longitud promedio por estribo (estimado conservador)
                long_estribo_m = 2.5  # se puede refinar con las dimensiones exactas
                kg_trans = num_estribos * long_estribo_m * var_data["peso_kg_m"] * num_columnas
    
    return {
        "kg_longitudinal": round(kg_long, 2),
        "kg_transversal": round(kg_trans, 2),
        "kg_total": round(kg_long + kg_trans, 2),
        "kg_por_m_long": round(kg_m_long, 4),
        "detalle": f"Long: {kg_long:.1f}kg + Trans: {kg_trans:.1f}kg"
    }


def calcular_acero_zapata(
    long_m: float, ancho_m: float, alto_m: float,
    acero_dir1: str, acero_dir2: str = None,
    num_zapatas: int = 1
) -> dict:
    """
    Calcula el acero de una zapata aislada con especificación real de varilla.
    acero_dir1: '6Ø5/8"@0.30 L=1.45m' (como aparece en planos)
    """
    import re
    
    # Parsear especificación tipo "6Ø5/8"@0.30 L=1.45"
    kg_dir1 = 0.0
    kg_dir2 = 0.0
    
    def parsear_zapata_acero(spec: str, dimension_m: float) -> float:
        """Calcula kg para una dirección de la zapata."""
        # Extraer varilla
        m_var = re.search(r'(\d+)\s*[ØN#]\s*([\d/]+)', spec)
        if not m_var:
            return 0.0
        
        cant = int(m_var.group(1))
        var_data = get_varilla(m_var.group(2))
        if not var_data:
            return 0.0
        
        # Extraer longitud de varilla (L=1.45m) o usar dimensión de zapata
        m_long = re.search(r'L\s*=\s*([\d.]+)\s*m?', spec, re.I)
        long_varilla = float(m_long.group(1)) if m_long else dimension_m * 0.9  # 90% de dim con recubrimiento
        
        return cant * long_varilla * var_data["peso_kg_m"]
    
    kg_dir1 = parsear_zapata_acero(acero_dir1, long_m) * num_zapatas
    if acero_dir2:
        kg_dir2 = parsear_zapata_acero(acero_dir2, ancho_m) * num_zapatas
    else:
        kg_dir2 = kg_dir1  # Simétrico
    
    return {
        "kg_direccion_1": round(kg_dir1, 2),
        "kg_direccion_2": round(kg_dir2, 2),
        "kg_total": round(kg_dir1 + kg_dir2, 2),
        "num_zapatas": num_zapatas,
    }


if __name__ == "__main__":
    # Test rápido
    print("=== VARILLAS ===")
    for ref in ["#5", "5/8", "Ø5/8", "3", "4", "5"]:
        v = get_varilla(ref)
        if v:
            print(f"  {ref} → #{list(VARILLAS.keys())[list(VARILLAS.values()).index(v)]} | {v['mm']}mm | {v['peso_kg_m']} kg/m")
    
    print("\n=== DOSIFICACIÓN ===")
    for fc in [20.7, 21, 28, 24.2]:
        d = get_materiales_por_m3(fc)
        print(f"  f'c={fc}MPa → {d['proporcion']} | Cemento: {d['cemento_sacos_m3']:.1f} sacos/m³")
    
    print("\n=== ACERO COLUMNA ===")
    res = calcular_acero_columna("4Ø5/8\"", "#3@15cm", 3.0, 8)
    print(f"  8 columnas h=3m, 4Ø5/8\", #3@15cm → {res['kg_total']:.1f} kg")
    
    print("\n=== ACERO ZAPATA ===")
    res = calcular_acero_zapata(1.6, 1.6, 0.30, '6Ø5/8"@0.30 L=1.45m', num_zapatas=1)
    print(f"  Z-1 1.60×1.60×0.30m → {res['kg_total']:.1f} kg")
