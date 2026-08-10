"""
Motor de coherencia estructural — PresupuestarCO v6.
Verifica las relaciones LÓGICAS entre elementos del plano.

Un ingeniero experimentado siempre pregunta:
  - Si hay columnas, ¿dónde están sus zapatas?
  - Si hay zapatas, ¿dónde están las vigas de amarre?
  - Si hay losa de 200m², ¿por qué solo hay 300kg de acero?
  - ¿El acero de las columnas puede soportar la losa encima?

Este módulo hace exactamente eso: coherencia entre elementos, no solo
validación individual.
"""
import math
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ProblemaCoherencia:
    severidad: str          # "CRITICO" | "ADVERTENCIA" | "INFO"
    categoria: str          # "ELEMENTO_FALTANTE" | "DIMENSION_INCOHERENTE" | "CANTIDAD_INCOHERENTE"
    mensaje: str
    elemento_origen: str    # qué elemento generó el problema
    elemento_faltante: str  # qué elemento debería existir (si aplica)
    recomendacion: str
    valor_calculado: Optional[float] = None
    valor_esperado: Optional[float] = None
    unidad: str = ""


@dataclass
class ResultadoCoherencia:
    problemas: List[ProblemaCoherencia] = field(default_factory=list)
    elementos_faltantes: List[str] = field(default_factory=list)
    elementos_redundantes: List[str] = field(default_factory=list)
    resumen: str = ""
    puntuacion: float = 100.0
    completo: bool = True   # True si el juego de elementos es completo


# ── Reglas de coherencia ─────────────────────────────────────────────────────

REGLAS_ELEMENTOS_OBLIGATORIOS = {
    # Si existe X → debe existir Y
    "columnas":       ["cimentacion"],           # columna → zapata
    "vigas":          ["columnas"],               # viga → columna
    "losa":           ["vigas", "columnas"],      # losa → vigas + columnas
    "cimentacion":    ["viga_amarre"],            # zapata → viga de amarre
    "muros":          ["cimentacion"],            # muro → cimentación
    "escaleras":      ["losa"],                   # escalera → losa
    "cubierta":       ["columnas", "viga_amarre"], # cubierta → estructura soporte
}

# Ratios esperados columna/zapata
RATIO_COL_ZAPATA = (0.8, 1.5)  # 0.8-1.5 zapatas por columna (puede haber combinadas)

# Acero mínimo esperado por m² según sistema (kg/m²)
ACERO_MIN_KG_M2 = {
    "porticos_concreto": {"losa": 8, "columnas_ml": 12, "vigas_ml": 8},
    "mixto":             {"losa": 6, "columnas_ml": 10, "vigas_ml": 6},
    "estructura_metalica": {"cubierta_m2": 12},
    "muros":             {"losa": 5, "muro_m2": 15},
}

# Dimensiones coherentes columna → zapata
# Una columna de 30×30 no puede tener una zapata de 0.5×0.5 (no aguanta)
def zapata_minima_para_columna(ancho_col_cm: float, alto_col_cm: float,
                                 fc_mpa: float = 20.7, fy_mpa: float = 420) -> float:
    """Retorna el lado mínimo de zapata para una columna dada (en metros)."""
    # Carga aproximada en columna: 0.35×Ag×f'c (NSR-10 carga axial típica)
    area_col = (ancho_col_cm/100) * (alto_col_cm/100)
    carga_kn = 0.35 * area_col * fc_mpa * 1000  # kN
    # Capacidad admisible de suelo típica: 150 kN/m² (suelo S2 mediano)
    qa = 150
    area_minima = carga_kn / qa
    lado_minimo = math.sqrt(area_minima)
    return max(lado_minimo, 0.80)  # mínimo 80cm


def verificar_coherencia(
    elementos: List[Dict],
    sistema_estructural: str = "",
    area_m2: float = 0,
    fc_mpa: float = 20.7,
    fy_mpa: float = 420
) -> ResultadoCoherencia:
    """
    Función principal: verifica coherencia completa entre todos los elementos.
    """
    resultado = ResultadoCoherencia()
    sis = sistema_estructural.lower()

    # Clasificar elementos por tipo
    por_tipo: Dict[str, List[Dict]] = {}
    for el in elementos:
        tipo = el.get("tipo", "otros")
        if tipo not in por_tipo:
            por_tipo[tipo] = []
        por_tipo[tipo].append(el)

    tipos_presentes = set(por_tipo.keys())

    # ── REGLA 1: Elementos obligatorios ──────────────────────────────────────
    for tipo_origen, tipos_requeridos in REGLAS_ELEMENTOS_OBLIGATORIOS.items():
        if tipo_origen in tipos_presentes:
            for tipo_req in tipos_requeridos:
                if tipo_req not in tipos_presentes:
                    # Excepción: cubierta metálica no necesita columnas de concreto
                    if tipo_req == "columnas" and "metalic" in sis:
                        continue
                    # Excepción: losa puede no tener vigas si es plana
                    if tipo_req == "vigas" and "plana" in sis:
                        continue

                    nombre_req = {
                        "cimentacion": "zapatas/cimentación",
                        "viga_amarre": "vigas de amarre",
                        "columnas": "columnas",
                        "vigas": "vigas",
                        "losa": "placa/losa",
                    }.get(tipo_req, tipo_req)

                    resultado.elementos_faltantes.append(nombre_req)
                    resultado.problemas.append(ProblemaCoherencia(
                        severidad="CRITICO",
                        categoria="ELEMENTO_FALTANTE",
                        mensaje=f"Hay {tipo_origen} pero no se detectó {nombre_req}",
                        elemento_origen=tipo_origen,
                        elemento_faltante=tipo_req,
                        recomendacion=(
                            f"Verificar si el plano tiene {nombre_req}. "
                            f"NSR-10 los requiere cuando existen {tipo_origen}. "
                            f"Pueden estar en otra hoja del plano no analizada."
                        )
                    ))

    # ── REGLA 2: Coherencia columna ↔ zapata ─────────────────────────────────
    columnas = por_tipo.get("columnas", [])
    zapatas = por_tipo.get("cimentacion", [])

    if columnas and zapatas:
        n_col = sum(el.get("cantidad", 1) for el in columnas)
        n_zap = sum(el.get("cantidad", 1) for el in zapatas)

        ratio = n_zap / n_col if n_col > 0 else 0
        if ratio < RATIO_COL_ZAPATA[0]:
            resultado.problemas.append(ProblemaCoherencia(
                severidad="ADVERTENCIA",
                categoria="CANTIDAD_INCOHERENTE",
                mensaje=f"Hay {n_col:.0f} columnas pero solo {n_zap:.0f} zapatas ({ratio:.1f} zapatas/columna)",
                elemento_origen="columnas",
                elemento_faltante="cimentacion",
                recomendacion=(
                    f"Cada columna necesita su cimentación. "
                    f"Faltan ~{max(0, n_col - n_zap):.0f} zapatas o el plano tiene más hojas."
                ),
                valor_calculado=ratio,
                valor_esperado=1.0
            ))

        # Verificar que las zapatas sean suficientemente grandes para las columnas
        for col in columnas:
            a_cm = col.get("dimension_ancho_cm") or 30
            b_cm = col.get("dimension_alto_cm") or 30
            zap_min = zapata_minima_para_columna(a_cm, b_cm, fc_mpa)

            for zap in zapatas:
                za = (zap.get("dimension_ancho_cm") or 120) / 100
                zb = (zap.get("dimension_alto_cm") or 120) / 100
                lado_zap = min(za, zb)

                if lado_zap < zap_min * 0.7:  # 30% tolerancia
                    ref_col = col.get("referencia") or col.get("nombre","Col")
                    ref_zap = zap.get("referencia") or zap.get("nombre","Zapata")
                    resultado.problemas.append(ProblemaCoherencia(
                        severidad="ADVERTENCIA",
                        categoria="DIMENSION_INCOHERENTE",
                        mensaje=(
                            f"{ref_zap} ({za*100:.0f}×{zb*100:.0f}cm) puede ser pequeña "
                            f"para soportar {ref_col} ({a_cm:.0f}×{b_cm:.0f}cm)"
                        ),
                        elemento_origen="columnas",
                        elemento_faltante="",
                        recomendacion=(
                            f"Para columna {a_cm:.0f}×{b_cm:.0f}cm con f'c={fc_mpa}MPa "
                            f"y qa=150kN/m², zapata mínima ≈ {zap_min*100:.0f}×{zap_min*100:.0f}cm"
                        ),
                        valor_calculado=lado_zap,
                        valor_esperado=zap_min,
                        unidad="m"
                    ))
                    break  # Solo reportar una vez por columna

    # ── REGLA 3: Coherencia acero total vs área ───────────────────────────────
    kg_acero_total = sum(
        el.get("cantidad", 0)
        for el in elementos
        if el.get("unidad","") in ("Kg","kg") and
           "acero" in (el.get("nombre","") + el.get("capitulo","")).lower()
    )

    if area_m2 > 0 and kg_acero_total > 0:
        kg_m2 = kg_acero_total / area_m2

        if "metalic" not in sis and kg_m2 < 5:
            resultado.problemas.append(ProblemaCoherencia(
                severidad="CRITICO",
                categoria="CANTIDAD_INCOHERENTE",
                mensaje=f"Acero muy bajo: {kg_m2:.1f}kg/m² para {area_m2:.0f}m² — mínimo esperado ~30kg/m²",
                elemento_origen="acero",
                elemento_faltante="",
                recomendacion=(
                    "El acero calculado es sospechosamente bajo. "
                    f"Para este proyecto se esperaría al menos {area_m2*30:,.0f}kg. "
                    "Verificar que se cuantificó el acero de TODOS los elementos."
                ),
                valor_calculado=kg_m2,
                valor_esperado=30,
                unidad="kg/m²"
            ))

    # ── REGLA 4: Losa sin vigas en zona sísmica alta ──────────────────────────
    if "losa" in tipos_presentes and "vigas" not in tipos_presentes:
        if "alta" in sis or "zona alta" in sis.lower():
            resultado.problemas.append(ProblemaCoherencia(
                severidad="ADVERTENCIA",
                categoria="ELEMENTO_FALTANTE",
                mensaje="Losa sin vigas en zona sísmica — NSR-10 C.21 requiere vigas perimetrales",
                elemento_origen="losa",
                elemento_faltante="vigas",
                recomendacion=(
                    "NSR-10 Cap. C.21 exige vigas perimetrales en edificios con "
                    "pórticos en zona sísmica alta. Verificar si son losas planas "
                    "postensadas (diferente diseño) o si las vigas están en otra hoja."
                )
            ))

    # ── REGLA 5: Muros de contención sin drenaje ─────────────────────────────
    muros_cont = [el for el in por_tipo.get("muro_contencion", []) +
                              por_tipo.get("muros", [])
                  if "contenci" in (el.get("nombre","") + el.get("notas","")).lower()]

    if muros_cont:
        tiene_drenaje = any(
            "dren" in (el.get("nombre","") + el.get("notas","")).lower()
            for el in elementos
        )
        if not tiene_drenaje:
            resultado.problemas.append(ProblemaCoherencia(
                severidad="INFO",
                categoria="ELEMENTO_FALTANTE",
                mensaje="Muros de contención sin sistema de drenaje detectado",
                elemento_origen="muro_contencion",
                elemento_faltante="drenaje",
                recomendacion=(
                    "NSR-10 F.4.1 requiere sistema de drenaje en muros de contención. "
                    "Incluir lloraderos o tubo perforado en el presupuesto si aplica."
                )
            ))

    # ── REGLA 6: Caissones sin vigas de amarre ────────────────────────────────
    caissones = por_tipo.get("caisson", [])
    if caissones and "viga_amarre" not in tipos_presentes:
        resultado.problemas.append(ProblemaCoherencia(
            severidad="ADVERTENCIA",
            categoria="ELEMENTO_FALTANTE",
            mensaje=f"Hay {len(caissones)} caisson(es) pero no se detectaron vigas de amarre",
            elemento_origen="caisson",
            elemento_faltante="viga_amarre",
            recomendacion=(
                "Los caissones requieren vigas de amarre que conecten las cabezas "
                "de los pilotes (NSR-10 F.5.4). Verificar en el plano de cimentación."
            )
        ))

    # ── REGLA 7: Estructura metálica sin placa base ───────────────────────────
    if "estructura_metalica" in sis or "metalic" in sis:
        tiene_placa = any(
            any(p in (el.get("nombre","") + el.get("material","") + el.get("notas","")).upper()
                for p in ["PLACA BASE","PL 460","PL460","PLACA","ANCHOR","PERNO"])
            for el in elementos
        )
        if not tiene_placa:
            resultado.problemas.append(ProblemaCoherencia(
                severidad="INFO",
                categoria="ELEMENTO_FALTANTE",
                mensaje="Estructura metálica sin platinas base / pernos de anclaje detectados",
                elemento_origen="columnas",
                elemento_faltante="placa_base",
                recomendacion=(
                    "Las columnas metálicas requieren placa base (PL) y pernos de anclaje "
                    "al pedestal de concreto. Incluir en el presupuesto si aplica."
                )
            ))

    # ── Calcular puntuación ───────────────────────────────────────────────────
    criticos = len([p for p in resultado.problemas if p.severidad == "CRITICO"])
    advertencias = len([p for p in resultado.problemas if p.severidad == "ADVERTENCIA"])
    resultado.puntuacion = max(0, 100 - criticos * 25 - advertencias * 8)
    resultado.completo = len(resultado.elementos_faltantes) == 0

    # ── Resumen ───────────────────────────────────────────────────────────────
    if not resultado.problemas:
        resultado.resumen = f"✓ Coherencia estructural OK — {len(elementos)} elementos verificados"
    else:
        faltantes = ", ".join(resultado.elementos_faltantes[:3])
        resultado.resumen = (
            f"{criticos} problema(s) crítico(s), {advertencias} advertencia(s). "
            + (f"Elementos faltantes: {faltantes}" if faltantes else "")
        )

    logger.info(f"Coherencia: {resultado.resumen} | puntuación={resultado.puntuacion}")
    return resultado


def generar_checklist_ingeniero(resultado: ResultadoCoherencia) -> List[str]:
    """
    Genera un checklist que un ingeniero usaría para revisar el presupuesto.
    """
    checklist = []

    for p in resultado.problemas:
        if p.severidad == "CRITICO":
            checklist.append(f"☐ CRÍTICO: {p.mensaje} → {p.recomendacion}")
        elif p.severidad == "ADVERTENCIA":
            checklist.append(f"☐ Verificar: {p.mensaje}")
        else:
            checklist.append(f"☐ Info: {p.mensaje}")

    if not checklist:
        checklist.append("✓ Todos los elementos presentes y coherentes")

    return checklist
