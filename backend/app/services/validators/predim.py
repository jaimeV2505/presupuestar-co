# -*- coding: utf-8 -*-
"""
Motor de predimensionamiento estructural simplificado.
Verifica si las secciones del plano son coherentes con las cargas.

No reemplaza el calculo estructural completo (ETABS/SAP2000).
Hace lo que un ingeniero hace "de cabeza" para detectar errores groseros:
  - Losa 20cm + sobrecarga 200kg/m^2 -> momento -> viga minima
  - Columna 30x30 con h=6m -> esbeltez -> cuantia minima necesaria
  - Zapata 1.20x1.20 con suelo qa=150kN/m^2 -> carga maxima admisible

NSR-10 Referencias: C.9, C.10, C.21, F.
"""
import math
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Cargas de diseno por uso (kN/m^2) segun NSR-10 B.4
CARGAS_USO = {
    "vivienda":        {"cm": 2.0,  "cv": 1.8,  "desc": "Residencial"},
    "oficina":         {"cm": 2.0,  "cv": 2.5,  "desc": "Oficinas"},
    "comercial":       {"cm": 2.5,  "cv": 5.0,  "desc": "Comercial"},
    "institucional":   {"cm": 2.0,  "cv": 3.0,  "desc": "Institucional/educacion"},
    "industrial":      {"cm": 3.0,  "cv": 7.5,  "desc": "Industrial liviano"},
    "cubierta_plana":  {"cm": 1.5,  "cv": 1.0,  "desc": "Cubierta plana"},
    "cubierta_inclinada": {"cm": 1.2, "cv": 0.5,"desc": "Cubierta inclinada"},
    "deportivo":       {"cm": 2.0,  "cv": 5.0,  "desc": "Instalacion deportiva"},
    "default":         {"cm": 2.0,  "cv": 2.5,  "desc": "General (conservador)"},
}

# Capacidad admisible del suelo por tipo (kN/m^2)
QA_SUELO = {
    "S1": 300,  # Roca o suelo muy rigido
    "S2": 200,  # Suelo rigido
    "S3": 120,  # Suelo blando
    "S4":  80,  # Suelo muy blando
    "default": 150,
}


@dataclass
class AlertaPredim:
    severidad: str       # "ERROR" | "ADVERTENCIA" | "INFO"
    elemento: str
    mensaje: str
    valor_actual: Optional[float] = None
    valor_minimo: Optional[float] = None
    unidad: str = ""
    recomendacion: str = ""


@dataclass
class ResultadoPredim:
    alertas: List[AlertaPredim] = field(default_factory=list)
    indicadores: Dict = field(default_factory=dict)
    resumen: str = ""


# ── Predimensionamiento de vigas ─────────────────────────────────────────────

def predim_viga(
    luz_m: float,
    ancho_m: float,
    alto_m: float,
    fc_mpa: float = 20.7,
    carga_total_kn_m2: float = 8.0,
    tributaria_m: float = 3.0,
    fy_mpa: float = 420.0
) -> Tuple[float, float, str]:
    """
    Verifica si la seccion de viga es adecuada para la luz y carga.
    Retorna (Mu_kNm, capacidad_kNm, evaluacion).

    Metodo simplificado ACI/NSR-10:
    - Carga lineal: w = carga_total * tributaria
    - Momento ultimo: Mu = 1.2*CM + 1.6*CV aplicado simplificado
    - Capacidad: Mn = 0.85*fc*b*(d - a/2) donde a = As*fy/(0.85*fc*b)
    """
    # Carga lineal sobre la viga (kN/m)
    w_kn_m = carga_total_kn_m2 * tributaria_m

    # Momento ultimo simplificado (viga continua interior)
    Mu = w_kn_m * luz_m ** 2 / 10  # kN*m (coeficiente 1/10 para viga continua)

    # Altura efectiva (d = h - recubrimiento - d_estribo - db/2)
    # Estimado: d = h - 7cm
    d_m = alto_m - 0.07
    if d_m <= 0:
        d_m = alto_m * 0.85

    # Cuantia minima de diseno: rho = max(0.25*sqrt(fc)/fy, 1.4/fy)
    rho_min = max(0.25 * math.sqrt(fc_mpa) / fy_mpa, 1.4 / fy_mpa)  # NSR-10 C.10.5.1

    # Momento resistente con cuantia minima
    # Trabajar en unidades consistentes: N y mm
    b_mm = ancho_m * 1000
    d_mm = d_m * 1000
    fc_n_mm2 = fc_mpa          # 1 MPa = 1 N/mm^2
    fy_n_mm2 = fy_mpa  # MPa = N/mm^2

    As_min_mm2 = rho_min * b_mm * d_mm
    a_mm = As_min_mm2 * fy_n_mm2 / (0.85 * fc_n_mm2 * b_mm)
    Mn_Nmm = As_min_mm2 * fy_n_mm2 * (d_mm - a_mm / 2)
    Mn_kNm = Mn_Nmm / 1e6

    # Phi = 0.90 para flexion
    phi_Mn = 0.90 * Mn_kNm

    if phi_Mn < Mu * 0.7:
        evaluacion = "INSUFICIENTE"
    elif phi_Mn < Mu:
        evaluacion = "AJUSTADO"
    else:
        evaluacion = "OK"

    return Mu, phi_Mn, evaluacion


def alto_minimo_viga(luz_m: float, tipo: str = "continua") -> float:
    """
    Altura minima de viga segun NSR-10 C.9.5.2 (tabla).
    tipo: "simple" | "continua" | "voladizo"
    Retorna h_min en metros.
    """
    factores = {"simple": 1/16, "continua": 1/21, "voladizo": 1/8}
    factor = factores.get(tipo, 1/16)
    h_min = luz_m * factor
    return max(h_min, 0.25)  # minimo 25cm


# ── Predimensionamiento de columnas ─────────────────────────────────────────

def predim_columna(
    ancho_m: float,
    alto_m: float,
    h_libre_m: float,
    fc_mpa: float = 20.7,
    fy_mpa: float = 420,
    carga_axial_kn: float = None,
    num_pisos: int = 1,
    area_tributaria_m2: float = 9.0
) -> Tuple[float, float, str]:
    """
    Verifica si la columna tiene seccion suficiente para la carga axial.
    Retorna (Pu_kN, capacidad_kN, evaluacion).
    """
    area_col = ancho_m * alto_m  # m^2

    # Estimar carga axial si no se da
    if carga_axial_kn is None:
        # Carga por piso: asume carga total 10 kN/m^2 (CM+CV amplificada)
        carga_por_piso = 10.0 * area_tributaria_m2
        Pu = num_pisos * carga_por_piso * 1.2  # factor amplificacion
    else:
        Pu = carga_axial_kn

    # Capacidad axial minima (con cuantia minima 1%)
    # Unidades: mm, N, MPa
    rho_min = 0.01
    Ag_mm2 = area_col * 1e6   # m^2 -> mm^2
    Ast_mm2 = rho_min * Ag_mm2
    # NSR-10 C.10.3.6: Pn = 0.80*(0.85*fc*(Ag-Ast) + fy*Ast)
    Pn_N = 0.80 * (0.85 * fc_mpa * (Ag_mm2 - Ast_mm2) + fy_mpa * Ast_mm2)
    phi_Pn = 0.65 * Pn_N / 1000  # N -> kN

    if phi_Pn < Pu * 0.8:
        evaluacion = "INSUFICIENTE"
    elif phi_Pn < Pu:
        evaluacion = "AJUSTADO"
    else:
        evaluacion = "OK"

    return Pu, phi_Pn, evaluacion


# ── Predimensionamiento de zapatas ──────────────────────────────────────────

def predim_zapata(
    largo_m: float,
    ancho_m: float,
    alto_m: float,
    carga_columna_kn: float = None,
    tipo_suelo: str = "S2",
    ancho_col_m: float = 0.30,
    largo_col_m: float = 0.30,
    fc_mpa: float = 20.7
) -> Tuple[float, float, str, bool]:
    """
    Verifica si la zapata puede soportar la carga de la columna.
    Retorna (carga_kN, capacidad_kN, evaluacion, punzonamiento_verificar).
    """
    qa = QA_SUELO.get(tipo_suelo, QA_SUELO["default"])  # kN/m^2
    area_zapata = largo_m * ancho_m  # m^2

    # Capacidad admisible
    capacidad_kn = qa * area_zapata

    # Carga estimada si no se da
    if carga_columna_kn is None:
        area_tributaria = 9.0  # m^2 tipico
        carga_columna_kn = 10.0 * area_tributaria * 3  # 3 pisos tipico

    # Verificar punzonamiento (perimetro critico a d/2 del borde columna)
    d = alto_m - 0.075  # altura efectiva
    punzonamiento_verificar = False
    if d > 0:
        bo = 2 * ((ancho_col_m + d) + (largo_col_m + d))
        Vc_punch = 0.17 * (1 + 2/1) * math.sqrt(fc_mpa) * 1000 * bo * d / 1000
        if carga_columna_kn > Vc_punch * 0.75:
            # el calculo simplificado asume columna cuadrada (bc=1) — no reemplaza
            # el chequeo real de punzonamiento, solo marca que hay que revisarlo
            punzonamiento_verificar = True

    if capacidad_kn < carga_columna_kn * 0.8:
        evaluacion = "INSUFICIENTE"
    elif capacidad_kn < carga_columna_kn:
        evaluacion = "AJUSTADO"
    else:
        evaluacion = "OK"

    return carga_columna_kn, capacidad_kn, evaluacion, punzonamiento_verificar


# ── Motor principal ──────────────────────────────────────────────────────────

def verificar_predimensionamiento(
    elementos: List[Dict],
    uso: str = "vivienda",
    fc_mpa: float = 20.7,
    fy_mpa: float = 420,
    tipo_suelo: str = "S2",
    num_pisos: int = 1
) -> ResultadoPredim:
    """
    Verifica el predimensionamiento de todos los elementos estructurales.
    Detecta secciones insuficientes ANTES de calcular el presupuesto.
    """
    resultado = ResultadoPredim()

    cargas = CARGAS_USO.get(uso, CARGAS_USO["default"])
    carga_total = cargas["cm"] + cargas["cv"]  # kN/m^2 sin amplificar

    columnas = [e for e in elementos if e.get("tipo") == "columnas"]
    vigas = [e for e in elementos if e.get("tipo") == "vigas"]
    zapatas = [e for e in elementos if e.get("tipo") == "cimentacion"]

    errores = 0
    advertencias = 0

    # ── Verificar vigas ────────────────────────────────────────────────────
    for v in vigas:
        nombre = f"{v.get('referencia','')} {v.get('nombre','')}".strip()
        a_m = (v.get("dimension_ancho_cm") or 25) / 100
        h_m = (v.get("dimension_alto_cm") or 40) / 100
        luz = v.get("dimension_largo_m") or 5.0

        # Altura minima segun NSR-10
        h_min = alto_minimo_viga(luz, "continua")
        if h_m < h_min * 0.85:
            resultado.alertas.append(AlertaPredim(
                severidad="ADVERTENCIA",
                elemento=nombre,
                mensaje=(
                    f"Altura {h_m*100:.0f}cm puede ser baja para luz {luz:.1f}m "
                    f"(NSR-10 recomienda >= {h_min*100:.0f}cm para deflexion)"
                ),
                valor_actual=h_m * 100,
                valor_minimo=h_min * 100,
                unidad="cm",
                recomendacion=f"Considerar h >= {math.ceil(h_min*100/5)*5}cm"
            ))
            advertencias += 1

        # Capacidad vs demanda
        Mu, phi_Mn, eval_v = predim_viga(luz, a_m, h_m, fc_mpa, carga_total)
        if eval_v == "INSUFICIENTE":
            resultado.alertas.append(AlertaPredim(
                severidad="ERROR",
                elemento=nombre,
                mensaje=(
                    f"Seccion {a_m*100:.0f}x{h_m*100:.0f}cm puede ser insuficiente "
                    f"para luz {luz:.1f}m con carga {carga_total:.1f}kN/m^2. "
                    f"Mu={Mu:.0f}kNm > phi*Mn={phi_Mn:.0f}kNm"
                ),
                valor_actual=phi_Mn,
                valor_minimo=Mu,
                unidad="kNm",
                recomendacion="Verificar con calculo estructural completo (ETABS/SAP2000)"
            ))
            errores += 1
        elif eval_v == "AJUSTADO":
            resultado.alertas.append(AlertaPredim(
                severidad="INFO",
                elemento=nombre,
                mensaje=f"Viga ajustada: Mu={Mu:.0f}kNm ~ phi*Mn={phi_Mn:.0f}kNm",
                recomendacion="Verificar acero de refuerzo en memoria de calculo"
            ))

    # ── Verificar columnas ─────────────────────────────────────────────────
    for c in columnas:
        nombre = f"{c.get('referencia','')} {c.get('nombre','')}".strip()
        a_m = (c.get("dimension_ancho_cm") or 30) / 100
        b_m = (c.get("dimension_alto_cm") or 30) / 100
        h_libre = c.get("altura_libre_m") or 3.0
        cant = c.get("cantidad", 1)

        # Area tributaria estimada
        area_trib = 9.0  # m^2 tipico — mejorar si se tiene el plano de ejes

        Pu, phi_Pn, eval_c = predim_columna(
            a_m, b_m, h_libre, fc_mpa, fy_mpa,
            num_pisos=num_pisos, area_tributaria_m2=area_trib
        )

        if eval_c == "INSUFICIENTE":
            resultado.alertas.append(AlertaPredim(
                severidad="ERROR",
                elemento=nombre,
                mensaje=(
                    f"Columna {a_m*100:.0f}x{b_m*100:.0f}cm puede ser insuficiente. "
                    f"Pu est.={Pu:.0f}kN > phi*Pn={phi_Pn:.0f}kN con {num_pisos} piso(s)"
                ),
                valor_actual=phi_Pn,
                valor_minimo=Pu,
                unidad="kN",
                recomendacion="Aumentar seccion o verificar con calculo completo"
            ))
            errores += 1

    # ── Verificar zapatas ──────────────────────────────────────────────────
    for z in zapatas:
        nombre = f"{z.get('referencia','')} {z.get('nombre','')}".strip()
        largo = (z.get("dimension_ancho_cm") or 120) / 100
        ancho = (z.get("dimension_alto_cm") or 120) / 100
        h_zap = (z.get("espesor_cm") or 30) / 100
        cant = z.get("cantidad", 1)

        # Columna asociada estimada
        area_trib = 9.0
        carga_col = 10.0 * area_trib * max(num_pisos, 1) * 1.3

        carga, cap, eval_z, punz_verificar = predim_zapata(
            largo, ancho, h_zap, carga_col, tipo_suelo
        )

        if punz_verificar:
            resultado.alertas.append(AlertaPredim(
                severidad="INFO",
                elemento=nombre,
                mensaje=f"Zapata {largo*100:.0f}x{ancho*100:.0f}cm: verificar punzonamiento (carga cercana al límite estimado)",
                recomendacion="Chequeo simplificado (asume columna cuadrada) — verificar punzonamiento real en memoria de cálculo (NSR-10 C.11.11)."
            ))

        if eval_z == "INSUFICIENTE":
            area_min = carga / QA_SUELO.get(tipo_suelo, 150)
            lado_min = math.sqrt(area_min)
            resultado.alertas.append(AlertaPredim(
                severidad="ADVERTENCIA",
                elemento=nombre,
                mensaje=(
                    f"Zapata {largo*100:.0f}x{ancho*100:.0f}cm con suelo {tipo_suelo} "
                    f"(qa={QA_SUELO.get(tipo_suelo,150)} kN/m^2): "
                    f"capacidad {cap:.0f}kN < carga est. {carga:.0f}kN"
                ),
                valor_actual=cap,
                valor_minimo=carga,
                unidad="kN",
                recomendacion=f"Considerar zapata >= {lado_min*100:.0f}x{lado_min*100:.0f}cm"
            ))
            advertencias += 1
        elif eval_z == "OK":
            resultado.indicadores[f"zapata_{nombre}_util"] = round(carga / cap * 100, 1)

    # ── Indicadores globales ───────────────────────────────────────────────
    resultado.indicadores.update({
        "uso": cargas["desc"],
        "carga_total_kn_m2": carga_total,
        "tipo_suelo": tipo_suelo,
        "num_pisos": num_pisos,
        "qa_kn_m2": QA_SUELO.get(tipo_suelo, 150),
    })

    resultado.resumen = (
        f"Predimensionamiento {cargas['desc']}, {num_pisos} piso(s), suelo {tipo_suelo}: "
        f"{errores} error(es), {advertencias} advertencia(s)"
    )

    logger.info(resultado.resumen)
    return resultado
