"""
Validador NSR-10 — Reglamento Colombiano de Construcción Sismo Resistente.
Verifica cuantías mínimas, recubrimientos, espaciamientos y configuraciones
permitidas para pórticos y muros en zonas sísmicas colombianas.

Fuente: NSR-10 Título C (Concreto Estructural), Título D (Mampostería),
        Título F (Cimentaciones), Título G (Estructura Metálica).
"""
import re
import math
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AlertaNSR:
    codigo: str          # "C.21.3.2.1"
    severidad: str       # "ERROR", "ADVERTENCIA", "INFO"
    elemento: str        # Nombre del elemento
    mensaje: str
    valor_actual: Optional[float] = None
    valor_requerido: Optional[float] = None
    unidad: str = ""


@dataclass
class ResultadoValidacion:
    alertas: List[AlertaNSR] = field(default_factory=list)
    correcciones: List[str] = field(default_factory=list)
    puntuacion: float = 100.0  # 100 = todo OK, 0 = múltiples errores
    zona_sismica: str = "alta"


# ── Tablas NSR-10 ────────────────────────────────────────────────────────────

# Cuantías mínimas de acero longitudinal en columnas (NSR-10 C.10.9.1)
CUANTIA_MIN_COLUMNA = 0.01    # 1% del área bruta
CUANTIA_MAX_COLUMNA = 0.08    # 8% del área bruta

# Cuantías mínimas en vigas (NSR-10 C.10.5.1)
# ρ_min = max(0.25√f'c/fy, 1.4/fy) — en unidades MPa
def cuantia_min_viga(fc_mpa: float, fy_mpa: float) -> float:
    return max(0.25 * math.sqrt(fc_mpa) / fy_mpa, 1.4 / fy_mpa)

# Espaciamiento máximo de estribos en columnas — zona sísmica alta (NSR-10 C.21.3.5)
def espaciamiento_max_estribo_columna(dim_menor_cm: float, fy_mpa: float = 420) -> float:
    """Retorna espaciamiento máximo en cm según NSR-10 zona alta."""
    s1 = dim_menor_cm / 4           # 1/4 de la dimensión menor
    s2 = 6 * 1.59 if fy_mpa >= 420 else 6 * 1.27  # 6 × diámetro barra longitudinal típica
    s3 = 10.0                       # 10 cm (zona de confinamiento)
    return min(s1, s2, s3)

# Recubrimientos mínimos NSR-10 (C.7.7.1) en cm
RECUBRIMIENTOS = {
    "interior_seco": 4.0,        # Columnas y vigas interiores
    "interior_humedo": 5.0,      # Elementos en contacto con humedad
    "exterior_a": 4.0,           # Exposición A (moderada)
    "exterior_b": 5.0,           # Exposición B (severa)
    "cimentacion": 7.5,          # Zapatas en contacto con suelo
    "losa_superior": 2.0,        # Losa cara superior sin exposición
    "losa_inferior": 2.0,
}

# Longitudes mínimas de desarrollo (ancla) NSR-10 C.12
def longitud_desarrollo(varilla_mm: float, fc_mpa: float, fy_mpa: float) -> float:
    """Longitud de desarrollo en mm según NSR-10 C.12.2.2."""
    db = varilla_mm  # diámetro en mm
    # Fórmula simplificada: ld = (fy × db) / (17.7 × √f'c)
    ld = (fy_mpa * db) / (17.7 * math.sqrt(fc_mpa))
    return max(ld, 300)  # mínimo 300mm

# Relación altura/ancho máxima en vigas (NSR-10 C.21.5.1)
MAX_RELACION_H_B_VIGA = 3.5
MIN_ANCHO_VIGA_CM = 25.0  # cm — zona sísmica alta

# Relación mínima ancho/alto en columnas — zona sísmica alta
MIN_DIMENSION_COLUMNA_CM = 25.0
MIN_RELACION_CORTA_LARGA = 0.40  # dimensión corta ≥ 40% de la larga


def validar_columna(
    ancho_cm: float, alto_cm: float, altura_m: float,
    fc_mpa: float, fy_mpa: float, zona: str,
    acero_long: str = "", acero_trans: str = "",
    nombre: str = "Columna"
) -> List[AlertaNSR]:
    alertas = []

    # ── Dimensiones mínimas ───────────────────────────────────────────────────
    dim_menor = min(ancho_cm, alto_cm)
    dim_mayor = max(ancho_cm, alto_cm)

    if zona == "alta":
        if dim_menor < MIN_DIMENSION_COLUMNA_CM:
            alertas.append(AlertaNSR(
                codigo="C.21.6.1.1", severidad="ERROR", elemento=nombre,
                mensaje=f"Dimensión mínima {dim_menor}cm < 25cm requerido NSR-10 zona alta",
                valor_actual=dim_menor, valor_requerido=MIN_DIMENSION_COLUMNA_CM, unidad="cm"
            ))
        if dim_menor / dim_mayor < MIN_RELACION_CORTA_LARGA:
            alertas.append(AlertaNSR(
                codigo="C.21.6.1.2", severidad="ADVERTENCIA", elemento=nombre,
                mensaje=f"Relación b/h = {dim_menor/dim_mayor:.2f} < 0.40 — columna muy esbelta",
                valor_actual=dim_menor/dim_mayor, valor_requerido=MIN_RELACION_CORTA_LARGA
            ))

    # ── Cuantía de acero longitudinal ─────────────────────────────────────────
    if acero_long:
        kg_m = _calcular_kg_m_acero(acero_long)
        area_acero_cm2 = kg_m / 7.85 * 100  # aprox cm²/m
        area_bruta = ancho_cm * alto_cm
        cuantia = area_acero_cm2 / area_bruta

        if cuantia < CUANTIA_MIN_COLUMNA:
            alertas.append(AlertaNSR(
                codigo="C.10.9.1", severidad="ERROR", elemento=nombre,
                mensaje=f"Cuantía acero {cuantia:.3f} < 1% mínimo NSR-10 en columnas",
                valor_actual=cuantia, valor_requerido=CUANTIA_MIN_COLUMNA
            ))
        if cuantia > CUANTIA_MAX_COLUMNA:
            alertas.append(AlertaNSR(
                codigo="C.10.9.1", severidad="ADVERTENCIA", elemento=nombre,
                mensaje=f"Cuantía acero {cuantia:.3f} > 8% máximo NSR-10 (dificultad de colocación)",
                valor_actual=cuantia, valor_requerido=CUANTIA_MAX_COLUMNA
            ))

    # ── Estribos — zona sísmica alta ─────────────────────────────────────────
    if acero_trans and zona == "alta":
        espaciamiento = _extraer_espaciamiento(acero_trans)
        if espaciamiento:
            s_max = espaciamiento_max_estribo_columna(dim_menor, fy_mpa)
            if espaciamiento > s_max:
                alertas.append(AlertaNSR(
                    codigo="C.21.3.5", severidad="ERROR", elemento=nombre,
                    mensaje=f"Estribo @{espaciamiento}cm > máximo {s_max:.1f}cm NSR-10 zona alta (zona confinamiento)",
                    valor_actual=espaciamiento, valor_requerido=s_max, unidad="cm"
                ))

    # ── Esbeltez ──────────────────────────────────────────────────────────────
    esbeltez = altura_m * 100 / dim_menor
    if esbeltez > 22:
        alertas.append(AlertaNSR(
            codigo="C.10.10", severidad="ADVERTENCIA", elemento=nombre,
            mensaje=f"Esbeltez kL/r ≈ {esbeltez:.1f} — verificar efectos de segundo orden",
            valor_actual=esbeltez, valor_requerido=22.0
        ))

    return alertas


def validar_viga(
    ancho_cm: float, alto_cm: float, longitud_m: float,
    fc_mpa: float, fy_mpa: float, zona: str,
    acero_long: str = "", nombre: str = "Viga"
) -> List[AlertaNSR]:
    alertas = []

    # ── Dimensión mínima de ancho ─────────────────────────────────────────────
    if zona == "alta" and ancho_cm < MIN_ANCHO_VIGA_CM:
        alertas.append(AlertaNSR(
            codigo="C.21.5.1.3", severidad="ERROR", elemento=nombre,
            mensaje=f"Ancho {ancho_cm}cm < 25cm mínimo NSR-10 zona alta",
            valor_actual=ancho_cm, valor_requerido=MIN_ANCHO_VIGA_CM, unidad="cm"
        ))

    # ── Relación alto/ancho ───────────────────────────────────────────────────
    relacion = alto_cm / ancho_cm
    if relacion > MAX_RELACION_H_B_VIGA:
        alertas.append(AlertaNSR(
            codigo="C.21.5.1.4", severidad="ADVERTENCIA", elemento=nombre,
            mensaje=f"Relación h/b = {relacion:.1f} > 3.5 — viga muy profunda",
            valor_actual=relacion, valor_requerido=MAX_RELACION_H_B_VIGA
        ))

    # ── Cuantía mínima ────────────────────────────────────────────────────────
    if acero_long:
        rho_min = cuantia_min_viga(fc_mpa, fy_mpa)
        # Estimación de cuantía desde especificación
        # Solo verificamos si podemos parsear el acero
        nota = f"Cuantía mínima requerida: ρ_min = {rho_min:.4f} ({rho_min*100:.2f}%)"
        alertas.append(AlertaNSR(
            codigo="C.10.5.1", severidad="INFO", elemento=nombre,
            mensaje=nota, valor_requerido=rho_min
        ))

    return alertas


def validar_zapata(
    largo_cm: float, ancho_cm: float, alto_cm: float,
    fc_mpa: float, num_zapatas: int = 1, nombre: str = "Zapata"
) -> List[AlertaNSR]:
    alertas = []

    # ── Altura mínima de zapata ───────────────────────────────────────────────
    if alto_cm < 25:
        alertas.append(AlertaNSR(
            codigo="C.15.7.3", severidad="ERROR", elemento=nombre,
            mensaje=f"Altura zapata {alto_cm}cm < 25cm mínimo NSR-10",
            valor_actual=alto_cm, valor_requerido=25.0, unidad="cm"
        ))

    # ── Recubrimiento en cimentación ─────────────────────────────────────────
    alertas.append(AlertaNSR(
        codigo="C.7.7.1", severidad="INFO", elemento=nombre,
        mensaje=f"Recubrimiento mínimo en cimentación: 7.5cm (NSR-10 C.7.7.1b)",
        valor_requerido=7.5, unidad="cm"
    ))

    return alertas


def validar_losa(
    espesor_cm: float, tipo: str, fc_mpa: float,
    nombre: str = "Losa"
) -> List[AlertaNSR]:
    alertas = []

    # Espesores mínimos NSR-10 C.9.5
    if "maciza" in tipo.lower():
        espesor_min = 12.0
    elif "nervada" in tipo.lower() or "aligerada" in tipo.lower():
        espesor_min = 25.0  # Total incluyendo nervio
    else:
        espesor_min = 12.0

    if espesor_cm < espesor_min:
        alertas.append(AlertaNSR(
            codigo="C.9.5.3", severidad="ADVERTENCIA", elemento=nombre,
            mensaje=f"Espesor {espesor_cm}cm puede ser insuficiente para {tipo} (mín referencial {espesor_min}cm)",
            valor_actual=espesor_cm, valor_requerido=espesor_min, unidad="cm"
        ))

    return alertas




def longitud_desarrollo(db_mm: float, fc_mpa: float, fy_mpa: float,
                        posicion: str = "otro") -> float:
    """
    Longitud de desarrollo de barras en tension NSR-10 C.12.2.
    db_mm: diametro de la barra en mm
    posicion: "superior" (barra horizontal con >300mm concreto abajo) o "otro"
    Retorna ld en cm.
    """
    import math
    # Factor de posicion: barras superiores tienen peor adherencia
    psi_t = 1.3 if posicion == "superior" else 1.0
    # Factor de recubrimiento (conservador sin recubrimiento especial)
    psi_e = 1.0
    # Formula NSR-10 C.12.2.2 simplificada
    ld_mm = (fy_mpa * psi_t * psi_e * db_mm) / (3.5 * math.sqrt(fc_mpa))
    ld_cm = ld_mm / 10
    # Minimo absoluto: 300mm = 30cm
    return max(ld_cm, 30.0)


def longitud_traslape(db_mm: float, fc_mpa: float, fy_mpa: float,
                      clase: str = "B") -> float:
    """
    Longitud de traslape en tension NSR-10 C.12.15.
    clase: "A" (<=50% barras traslapadas en zona) o "B" (>50% o zona plastica)
    Retorna longitud en cm.
    """
    ld = longitud_desarrollo(db_mm, fc_mpa, fy_mpa)
    factor = 1.0 if clase == "A" else 1.3
    return round(ld * factor, 1)


def es_columna_corta(h_libre_m: float, dim_menor_cm: float) -> bool:
    """
    NSR-10 C.21.3.3: columna corta si h_libre < 5 x dimension_menor.
    Estas columnas tienen un mecanismo de falla diferente en sismo.
    """
    return h_libre_m < (5 * dim_menor_cm / 100)


def verificar_traslapes(
    elementos: list, fc_mpa: float, fy_mpa: float
) -> list:
    """
    Verifica longitudes de traslape en columnas y vigas.
    Retorna lista de AlertaNSR adicionales.
    """
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../data"))
    try:
        from tablas_tecnicas import get_varilla, VARILLAS
        tablas_ok = True
    except ImportError:
        tablas_ok = False

    alertas = []

    for el in elementos:
        tipo = el.get("tipo", "")
        nombre = f"{el.get('referencia','')} {el.get('nombre','')}".strip()
        acero_long = el.get("acero_longitudinal", "") or ""
        h_m = el.get("altura_libre_m") or 3.0

        if not acero_long or not tablas_ok:
            continue

        # Extraer varilla principal
        import re
        m = re.search(r'#(\d+)|N(\d+)|(\d+)/(\d+)', acero_long)
        if not m:
            continue

        # Obtener diametro en mm
        var_ref = m.group(1) or m.group(2)
        if var_ref:
            var = get_varilla(var_ref)
            db_mm = var["mm"] if var else 15.9
        else:
            db_mm = 15.9  # #5 por defecto

        # Calcular traslape requerido
        # En zona sismica alta: siempre clase B fuera de zonas de confinamiento
        lt = longitud_traslape(db_mm, fc_mpa, fy_mpa, clase="B")

        if tipo == "columnas":
            # Verificar columna corta
            a_cm = el.get("dimension_ancho_cm") or 30
            b_cm = el.get("dimension_alto_cm") or 30
            dim_menor = min(a_cm, b_cm)

            if es_columna_corta(h_m, dim_menor):
                alertas.append(AlertaNSR(
                    codigo="C.21.3.3",
                    severidad="ERROR",
                    elemento=nombre,
                    mensaje=(
                        f"COLUMNA CORTA: h_libre={h_m:.2f}m < 5x{dim_menor:.0f}cm={dim_menor/100*5:.2f}m. "
                        f"Requiere diseno especial para sismo — mecanismo de falla diferente."
                    ),
                    valor_actual=h_m,
                    valor_requerido=dim_menor / 100 * 5,
                    unidad="m"
                ))

            # Traslape en columna: minimo en zona de confinamiento
            lt_col = longitud_traslape(db_mm, fc_mpa, fy_mpa, clase="B")
            if lt_col > h_m * 100 * 0.5:
                alertas.append(AlertaNSR(
                    codigo="C.12.15",
                    severidad="ADVERTENCIA",
                    elemento=nombre,
                    mensaje=(
                        f"Traslape requerido {lt_col:.0f}cm > 50% de altura columna. "
                        f"Considerar traslape escalonado o soldadura."
                    ),
                    valor_actual=lt_col,
                    valor_requerido=h_m * 100 * 0.5,
                    unidad="cm"
                ))

            alertas.append(AlertaNSR(
                codigo="C.12.15",
                severidad="INFO",
                elemento=nombre,
                mensaje=f"Traslape minimo clase B: {lt_col:.0f}cm (varilla {db_mm:.0f}mm, f'c={fc_mpa}MPa)",
                valor_requerido=lt_col,
                unidad="cm"
            ))

        elif tipo == "vigas":
            lt_viga = longitud_traslape(db_mm, fc_mpa, fy_mpa, clase="A")
            alertas.append(AlertaNSR(
                codigo="C.12.15",
                severidad="INFO",
                elemento=nombre,
                mensaje=f"Traslape viga clase A: {lt_viga:.0f}cm | clase B: {longitud_traslape(db_mm, fc_mpa, fy_mpa, 'B'):.0f}cm",
                valor_requerido=lt_viga,
                unidad="cm"
            ))

    return alertas


def verificar_titulo_g_metalica(elementos: list) -> list:
    """
    Verificacion basica NSR-10 Titulo G para estructura metalica.
    Relaciones b/t de compacidad AISC 360 para miembros sismicos.
    """
    alertas = []

    for el in elementos:
        nombre = f"{el.get('referencia','')} {el.get('nombre','')}".strip()
        material = (el.get("material","") + el.get("nombre","")).upper()
        tipo = el.get("tipo","")

        if not any(p in material for p in ["PTE","PHR","W1","W8","W10","W12","W14","W18"]):
            continue

        a_cm = el.get("dimension_ancho_cm") or 0
        b_cm = el.get("dimension_alto_cm") or 0

        # Para PTE (tubular cuadrado): b/t <= 0.64*sqrt(E/Fy)
        # Con E=200,000 MPa y Fy=345 MPa (A500 Gr.C): b/t <= 15.7
        # Con Fy=250 MPa (A36): b/t <= 18.4
        if "PTE" in material and a_cm > 0:
            # Extraer espesor del nombre: PTE 250x250x9 -> t=9mm
            import re
            m = re.search(r'PTE\s*\d+[xX]\d+[xX]([\d.]+)', material)
            if m:
                t_mm = float(m.group(1))
                b_t = (a_cm * 10) / t_mm  # dimension en mm / espesor
                fy_est = 345  # A500 Gr.C tipico
                limite = 0.64 * (200000 / fy_est) ** 0.5

                if b_t > limite:
                    alertas.append(AlertaNSR(
                        codigo="NSR-10 G.3.4",
                        severidad="ADVERTENCIA",
                        elemento=nombre,
                        mensaje=(
                            f"PTE: relacion b/t = {b_t:.1f} > limite compacto {limite:.1f} "
                            f"(AISC 360 Tabla B4.1). Verificar capacidad en zona sismica."
                        ),
                        valor_actual=b_t,
                        valor_requerido=limite
                    ))

    return alertas

def validar_elementos(
    elementos: List[Dict],
    fc_mpa: float = 20.7,
    fy_mpa: float = 420.0,
    zona: str = "alta"
) -> ResultadoValidacion:
    """
    Valida todos los elementos estructurales contra NSR-10.
    Retorna alertas ordenadas por severidad.
    """
    resultado = ResultadoValidacion(zona_sismica=zona)
    total_errores = 0
    total_advertencias = 0

    for el in elementos:
        tipo = el.get("tipo", "")
        nombre = f"{el.get('referencia','')} {el.get('nombre','')}".strip()
        a_cm = el.get("dimension_ancho_cm") or 0
        b_cm = el.get("dimension_alto_cm") or 0
        h_m = el.get("altura_libre_m") or 3.0
        e_cm = el.get("espesor_cm") or 0
        area = el.get("area_m2") or 0
        acero_l = el.get("acero_longitudinal") or ""
        acero_t = el.get("acero_transversal") or ""
        cant = el.get("cantidad", 1)

        alertas_el = []

        if tipo == "columnas" and a_cm and b_cm:
            alertas_el = validar_columna(
                a_cm, b_cm, h_m, fc_mpa, fy_mpa, zona,
                acero_l, acero_t, nombre
            )
        elif tipo == "vigas" and a_cm and b_cm:
            alertas_el = validar_viga(
                a_cm, b_cm, el.get("dimension_largo_m", 5.0),
                fc_mpa, fy_mpa, zona, acero_l, nombre
            )
        elif tipo == "cimentacion" and a_cm and b_cm and e_cm:
            alertas_el = validar_zapata(a_cm, b_cm, e_cm, fc_mpa, cant, nombre)
        elif tipo == "losa" and e_cm:
            alertas_el = validar_losa(e_cm, el.get("nombre",""), fc_mpa, nombre)

        for alerta in alertas_el:
            resultado.alertas.append(alerta)
            if alerta.severidad == "ERROR":
                total_errores += 1
            elif alerta.severidad == "ADVERTENCIA":
                total_advertencias += 1

    # Calcular puntuación
    resultado.puntuacion = max(0, 100 - (total_errores * 20) - (total_advertencias * 5))

    # Generar correcciones sugeridas
    errores = [a for a in resultado.alertas if a.severidad == "ERROR"]
    for err in errores[:5]:  # Máx 5 correcciones
        if err.valor_actual and err.valor_requerido:
            resultado.correcciones.append(
                f"{err.elemento}: {err.mensaje} → ajustar a {err.valor_requerido}{err.unidad}"
            )
        else:
            resultado.correcciones.append(f"{err.elemento}: {err.mensaje}")

    logger.info(f"Validación NSR-10: {total_errores} errores, {total_advertencias} advertencias, puntuación={resultado.puntuacion}")
    return resultado


def _calcular_kg_m_acero(especificacion: str) -> float:
    """Estima kg/m de acero desde especificación. Simplificado."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../data'))
    try:
        from tablas_tecnicas import calcular_kg_acero_por_especificacion
        return calcular_kg_acero_por_especificacion(especificacion)
    except Exception:
        return 0.0


def _extraer_espaciamiento(acero_trans: str) -> Optional[float]:
    """Extrae el espaciamiento de estribo en cm."""
    m = re.search(r'@\s*(\d+(?:\.\d+)?)\s*(cm|m)?|c/\s*(\d+(?:\.\d+)?)\s*(cm|m)?',
                  acero_trans, re.IGNORECASE)
    if m:
        val = float(m.group(1) or m.group(3))
        unit = (m.group(2) or m.group(4) or "cm").lower()
        return val if unit == "cm" else val * 100
    return None


def formatear_alertas_para_claude(resultado: ResultadoValidacion) -> str:
    """Convierte las alertas NSR-10 en texto para incluir en el presupuesto."""
    if not resultado.alertas:
        return "✓ Todos los elementos cumplen NSR-10"

    lines = [f"VALIDACIÓN NSR-10 — Puntuación: {resultado.puntuacion:.0f}/100\n"]

    errores = [a for a in resultado.alertas if a.severidad == "ERROR"]
    advertencias = [a for a in resultado.alertas if a.severidad == "ADVERTENCIA"]
    infos = [a for a in resultado.alertas if a.severidad == "INFO"]

    if errores:
        lines.append(f"ERRORES ({len(errores)}) — Requieren corrección:")
        for e in errores:
            lines.append(f"  ✗ [{e.codigo}] {e.elemento}: {e.mensaje}")

    if advertencias:
        lines.append(f"\nADVERTENCIAS ({len(advertencias)}) — Revisar:")
        for a in advertencias:
            lines.append(f"  ⚠ [{a.codigo}] {a.elemento}: {a.mensaje}")

    if infos:
        lines.append(f"\nINFORMACIÓN:")
        for i in infos[:3]:
            lines.append(f"  ℹ [{i.codigo}] {i.elemento}: {i.mensaje}")

    return "\n".join(lines)
