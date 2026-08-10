"""
Calculadora precisa de acero de refuerzo.
Calcula kg exactos de acero longitudinal Y transversal (estribos)
desde las especificaciones del plano estructural.
"""
import re
import math
import logging
from typing import Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Importar tabla de varillas
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../data'))
try:
    from tablas_tecnicas import get_varilla, VARILLAS
    TABLAS_OK = True
except ImportError:
    TABLAS_OK = False
    logger.warning("tablas_tecnicas no disponible")


@dataclass
class ResultadoAcero:
    kg_longitudinal: float
    kg_transversal: float
    kg_total: float
    detalle_longitudinal: str
    detalle_transversal: str
    metodo: str  # "especificacion_exacta" | "factor_estimado"
    advertencias: list


def calcular_acero_columna_exacto(
    ancho_cm: float, alto_cm: float, altura_m: float,
    acero_long: str, acero_trans: str,
    num_columnas: int = 1,
    fc_mpa: float = 20.7, fy_mpa: float = 420
) -> ResultadoAcero:
    """
    Calcula acero exacto de una columna desde su especificación completa.

    acero_long: "4Ø5/8\"" o "6#5+2#4" o "8N5"
    acero_trans: "#3@15cm" o "Estribo #3 c/15cm zona conf c/10cm"
    """
    advertencias = []

    # ── Acero longitudinal ────────────────────────────────────────────────────
    kg_long = 0.0
    detalle_long = ""

    if acero_long and TABLAS_OK:
        grupos = _parsear_grupos_varilla(acero_long)
        detalles = []
        for cant, var_ref in grupos:
            var = get_varilla(var_ref)
            if var:
                kg_barra = cant * altura_m * var["peso_kg_m"] * num_columnas
                kg_long += kg_barra
                detalles.append(f"{cant}Ø{var['pulg']}\" ({var['peso_kg_m']}kg/m×{altura_m}m×{cant}barras×{num_columnas}col={kg_barra:.1f}kg)")
            else:
                advertencias.append(f"Varilla '{var_ref}' no encontrada en tabla — usando estimado")
                kg_long += cant * altura_m * 1.554 * num_columnas  # #5 por defecto
        detalle_long = " + ".join(detalles)
    elif not TABLAS_OK:
        advertencias.append("Tablas de varilla no disponibles — usando factor kg/m³")
        vol = (ancho_cm/100) * (alto_cm/100) * altura_m * num_columnas
        kg_long = vol * 85 * 1.08
        detalle_long = f"Factor estimado 85kg/m³ × {vol:.3f}m³"

    # ── Acero transversal (estribos) ──────────────────────────────────────────
    kg_trans = 0.0
    detalle_trans = ""

    if acero_trans and TABLAS_OK:
        # Extraer varilla del estribo
        m_var = re.search(r'#(\d+)|N(\d+)|Ø([\d/]+)', acero_trans)
        # Extraer espaciamientos (puede haber dos: zona confinamiento y zona central)
        espaciamientos = re.findall(
            r'(?:@|c/)\s*(\d+(?:\.\d+)?)\s*(cm|m)?', acero_trans, re.IGNORECASE
        )

        if m_var and espaciamientos:
            var_num = m_var.group(1) or m_var.group(2) or m_var.group(3)
            var_estribo = get_varilla(var_num)

            if var_estribo:
                # Perímetro del estribo (sin recubrimiento)
                rec = 0.04  # 4cm de recubrimiento típico
                perimetro_m = 2 * ((ancho_cm/100 - 2*rec) + (alto_cm/100 - 2*rec))
                # Agregar ganchos: 2 ganchos a 135° = 2 × 12db
                gancho_m = 2 * 12 * (var_estribo["mm"]/1000)
                long_estribo_m = perimetro_m + gancho_m

                detalles_t = []
                total_estribos = 0

                if len(espaciamientos) >= 2:
                    # Dos zonas: confinamiento (h/4) y central
                    s1_cm = float(espaciamientos[0][0])
                    s2_cm = float(espaciamientos[1][0])
                    long_conf_m = max(altura_m/6, max(ancho_cm,alto_cm)/100, 0.45)
                    n_conf = int(long_conf_m * 2 / (s1_cm/100))  # 2 zonas de confinamiento
                    n_central = int((altura_m - long_conf_m * 2) / (s2_cm/100))
                    total_estribos = n_conf + n_central
                    detalles_t.append(f"Confinamiento: {n_conf} estribos @{s1_cm}cm")
                    detalles_t.append(f"Central: {n_central} estribos @{s2_cm}cm")
                else:
                    s_cm = float(espaciamientos[0][0])
                    total_estribos = int(altura_m / (s_cm/100))
                    detalles_t.append(f"{total_estribos} estribos @{s_cm}cm")

                kg_trans_un = total_estribos * long_estribo_m * var_estribo["peso_kg_m"]
                kg_trans = kg_trans_un * num_columnas
                detalle_trans = (
                    f"Estribo #{var_num} (L={long_estribo_m:.2f}m/estribo): "
                    f"{', '.join(detalles_t)} × {num_columnas} col = {kg_trans:.1f}kg"
                )
            else:
                advertencias.append(f"Varilla estribo '{var_num}' no en tabla")
        else:
            # Fallback: estribo #3 c/15cm
            var_e = get_varilla("3") if TABLAS_OK else None
            if var_e:
                perimetro_m = 2 * ((ancho_cm/100 - 0.08) + (alto_cm/100 - 0.08))
                n_est = int(altura_m / 0.15)
                kg_trans = n_est * perimetro_m * var_e["peso_kg_m"] * num_columnas
                detalle_trans = f"Estimado #3@15cm (sin especificación)"
                advertencias.append("Estribo estimado como #3@15cm — verificar plano")

    return ResultadoAcero(
        kg_longitudinal=round(kg_long, 2),
        kg_transversal=round(kg_trans, 2),
        kg_total=round(kg_long + kg_trans, 2),
        detalle_longitudinal=detalle_long,
        detalle_transversal=detalle_trans,
        metodo="especificacion_exacta" if acero_long and TABLAS_OK else "factor_estimado",
        advertencias=advertencias
    )


def calcular_acero_viga_exacto(
    ancho_cm: float, alto_cm: float, largo_m: float,
    acero_long_inf: str, acero_long_sup: str = "",
    acero_trans: str = "",
    num_vigas: int = 1,
    fc_mpa: float = 20.7, fy_mpa: float = 420
) -> ResultadoAcero:
    """
    Calcula acero exacto de una viga.
    acero_long_inf: acero de tensión (cara inferior) "3#5"
    acero_long_sup: acero de compresión (cara superior) "2#4"
    acero_trans: estribos "#3@20cm"
    """
    advertencias = []
    kg_long = 0.0
    detalles = []

    if TABLAS_OK:
        for spec, zona in [(acero_long_inf, "inferior"), (acero_long_sup, "superior")]:
            if spec:
                grupos = _parsear_grupos_varilla(spec)
                for cant, var_ref in grupos:
                    var = get_varilla(var_ref)
                    if var:
                        # Longitud de desarrollo en extremos
                        ld = max(0.40, 30 * var["mm"] / 1000)  # estimado
                        long_total = (largo_m + 2 * ld) * cant * num_vigas
                        kg = long_total * var["peso_kg_m"]
                        kg_long += kg
                        detalles.append(f"{cant}#{var_ref} {zona} ({kg:.1f}kg)")

    # Estribos de viga
    kg_trans = 0.0
    detalle_trans = ""
    if acero_trans and TABLAS_OK:
        m_var = re.search(r'#(\d+)|N(\d+)', acero_trans)
        m_esp = re.findall(r'(?:@|c/)\s*(\d+(?:\.\d+)?)', acero_trans)
        if m_var and m_esp:
            var_e = get_varilla(m_var.group(1) or m_var.group(2))
            if var_e:
                s_cm = float(m_esp[0])
                rec = 0.04
                perimetro_m = 2 * ((ancho_cm/100 - 2*rec) + (alto_cm/100 - 2*rec))
                n_est = int(largo_m / (s_cm/100))
                kg_trans = n_est * perimetro_m * var_e["peso_kg_m"] * num_vigas
                detalle_trans = f"#{m_var.group(1) or m_var.group(2)} @{s_cm}cm × {n_est}est × {num_vigas}vigas"

    return ResultadoAcero(
        kg_longitudinal=round(kg_long, 2),
        kg_transversal=round(kg_trans, 2),
        kg_total=round(kg_long + kg_trans, 2),
        detalle_longitudinal=" + ".join(detalles),
        detalle_transversal=detalle_trans,
        metodo="especificacion_exacta" if acero_long_inf and TABLAS_OK else "factor_estimado",
        advertencias=advertencias
    )


def calcular_acero_zapata_exacto(
    largo_cm: float, ancho_cm: float, espesor_cm: float,
    acero_dir1: str, acero_dir2: str = "",
    num_zapatas: int = 1
) -> ResultadoAcero:
    """Calcula acero exacto de zapata desde especificación del plano."""
    advertencias = []
    kg_d1 = kg_d2 = 0.0
    det1 = det2 = ""

    if TABLAS_OK:
        def calc_dir(spec: str, dim_cm: float) -> tuple:
            if not spec:
                return 0.0, ""
            grupos = _parsear_grupos_varilla(spec)
            kg = 0.0
            dets = []
            for cant, var_ref in grupos:
                var = get_varilla(var_ref)
                if var:
                    # Longitud de varilla = dimensión - 2 recubrimientos
                    rec = 0.075  # 7.5cm en cimentación
                    long_varilla = (dim_cm/100) - 2*rec
                    # Extrae longitud del plano si está especificada (L=1.45m)
                    m_l = re.search(r'L\s*=\s*([\d.]+)', spec)
                    if m_l:
                        long_varilla = float(m_l.group(1))
                    kg_dir = cant * long_varilla * var["peso_kg_m"] * num_zapatas
                    kg += kg_dir
                    dets.append(f"{cant}Ø{var['pulg']}\" L={long_varilla:.2f}m ({kg_dir:.1f}kg)")
            return kg, " + ".join(dets)

        kg_d1, det1 = calc_dir(acero_dir1, largo_cm)
        kg_d2, det2 = calc_dir(acero_dir2 or acero_dir1, ancho_cm)

    return ResultadoAcero(
        kg_longitudinal=round(kg_d1 + kg_d2, 2),
        kg_transversal=0.0,
        kg_total=round(kg_d1 + kg_d2, 2),
        detalle_longitudinal=f"Dir.1: {det1} | Dir.2: {det2}",
        detalle_transversal="N/A (zapata sin estribos)",
        metodo="especificacion_exacta" if acero_dir1 and TABLAS_OK else "factor_estimado",
        advertencias=advertencias
    )


def _parsear_grupos_varilla(spec: str) -> list:
    """
    Parsea una especificación de acero en grupos (cantidad, referencia).
    "4Ø5/8\"+2Ø1/2\"" → [(4,"5/8"), (2,"1/2")]
    "6#5+2#4" → [(6,"5"), (2,"4")]
    """
    patrones = [
        r'(\d+)\s*[Øø]\s*([\d]+/[\d]+)"?',   # 4Ø5/8"
        r'(\d+)\s*#\s*(\d+)',                   # 4#5
        r'(\d+)\s*N\s*(\d+)',                   # 4N5
        r'(\d+)\s*Ø\s*(\d+)',                   # 4Ø5
    ]
    grupos = []
    for pat in patrones:
        for m in re.finditer(pat, spec):
            cant = int(m.group(1))
            var_ref = m.group(2)
            if (cant, var_ref) not in grupos:
                grupos.append((cant, var_ref))
    return grupos if grupos else [(4, "5")]  # fallback #5
