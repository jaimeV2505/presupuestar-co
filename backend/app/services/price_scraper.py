"""
Scraper de precios materiales Colombia — v6.
Integra: DANE IPC materiales construcción (API real), ICCV, precios base 2026.
"""
import asyncio, httpx, json, logging, os, re
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)
CACHE_PATH = os.path.join(os.path.dirname(__file__), "../../data/precios_cache.json")

# Precios base enero 2026 (COP)
PRECIOS_BASE_2026 = {
    "cemento_50kg":        38500,   # Promedio Argos/Cemex/Holcim saco 50kg
    "cemento_42.5kg":      32700,   # Saco 42.5kg (variante menos comun -- el estandar real de la app es 50kg, ver cemento_50kg)
    "acero_kg":             3850,   # Varilla corrugada G60 $/kg Paz del Río
    "acero_malla_kg":       4200,   # Malla electrosoldada $/kg
    "perfil_PTE_kg":        6800,   # PTE A500 puesto obra $/kg
    "perfil_PHR_kg":        5900,   # PHR canal puesto obra $/kg
    "perfil_angulo_kg":     5600,   # Ángulo A36 puesto obra $/kg
    "perfil_W_kg":          7200,   # Perfil W americano puesto obra $/kg
    "arena_m3":            95000,   # Arena lavada $/m³
    "gravilla_m3":         88000,   # Gravilla $/m³
    "bloque_arcilla_und":   2100,   # Bloque 0.10×0.20×0.40 arcilla
    "bloque_concreto_und":  1850,   # Bloque concreto #4
    "ladrillo_und":          890,   # Tolete 9×12×24cm
    "jornal_oficial":      185000,  # Oficial construcción 2026
    "jornal_ayudante":     145000,  # Ayudante 2026
    "jornal_maestro":      230000,  # Maestro de obra 2026
}

# Variaciones mensuales típicas (para proyectar si DANE no responde)
VARIACION_MENSUAL_TIPICA = {
    "acero_kg":    0.025,   # ~2.5% mensual (volátil)
    "cemento_50kg": 0.008,  # ~0.8% mensual (estable)
    "arena_m3":    0.005,
    "gravilla_m3": 0.005,
    "perfil_PTE_kg": 0.020,
}

_cache: Dict = {}
_cache_fecha: Optional[str] = None


def _load_cache() -> Dict:
    global _cache, _cache_fecha
    try:
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH) as f:
                data = json.load(f)
                fecha = data.get("fecha", "")
                # Cache válido por 24 horas
                if fecha == datetime.now().strftime("%Y-%m-%d"):
                    _cache = data
                    _cache_fecha = fecha
                    return data
    except Exception:
        pass
    return {}


def _save_cache(data: Dict):
    try:
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        with open(CACHE_PATH, "w") as f:
            json.dump({**data, "fecha": datetime.now().strftime("%Y-%m-%d")}, f, indent=2)
    except Exception as e:
        logger.warning(f"No se pudo guardar cache: {e}")


async def get_factor_iccv() -> Dict:
    """
    Obtiene el ICCV del DANE — Índice de Costos de Construcción de Vivienda.
    API pública: https://www.dane.gov.co
    """
    cached = _load_cache()
    if cached.get("iccv"):
        return cached["iccv"]

    resultado = {"factor": 1.0, "variacion_anual": 0.0, "fuente": "base_2026", "fecha": "2026-01"}

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            # Endpoint oficial DANE ICCV
            resp = await client.get(
                "https://www.dane.gov.co/files/investigaciones/boletines/iccv/iccv.json",
                follow_redirects=True,
                headers={"User-Agent": "PresupuestarCO/6.0"}
            )
            if resp.status_code == 200:
                data = resp.json()
                var_anual = float(data.get("variacion", {}).get("anual", 0)) / 100
                factor = 1 + var_anual
                resultado = {
                    "factor": round(factor, 4),
                    "variacion_anual": round(var_anual * 100, 2),
                    "fuente": "DANE ICCV oficial",
                    "fecha": data.get("periodo", datetime.now().strftime("%Y-%m")),
                }
                logger.info(f"ICCV DANE: factor={factor:.4f} (var anual {var_anual:.2%})")
    except Exception as e:
        logger.warning(f"DANE ICCV no disponible: {e}. Usando factor base.")
        # Estimación: 6% anual (ICCV promedio histórico Colombia)
        meses_desde_base = 7  # Enero 2026 a Agosto 2026
        factor_est = 1 + (0.06 * meses_desde_base / 12)
        resultado = {
            "factor": round(factor_est, 4),
            "variacion_anual": 6.0,
            "fuente": "estimado_histórico",
            "fecha": datetime.now().strftime("%Y-%m"),
        }

    _save_cache({"iccv": resultado})
    return resultado


async def get_ipc_materiales() -> Dict:
    """
    IPC de materiales de construcción del DANE.
    Desglosado por material: cemento, acero, agregados, etc.
    """
    cached = _load_cache()
    if cached.get("ipc_materiales"):
        return cached["ipc_materiales"]

    resultado = {
        "acero":     {"variacion_anual": 8.5,  "factor": 1.085},
        "cemento":   {"variacion_anual": 4.2,  "factor": 1.042},
        "agregados": {"variacion_anual": 3.8,  "factor": 1.038},
        "general":   {"variacion_anual": 5.5,  "factor": 1.055},
        "fuente": "estimado_histórico_colombia_2026",
    }

    try:
        # DANE publica el IPC con ~1 mes de rezago -- se apunta al mes anterior,
        # calculado dinamicamente (antes estaba hardcodeado a "agosto2026" para
        # siempre, lo que hubiera traido datos silenciosamente desactualizados
        # cada mes que pasara sin que nadie lo notara)
        MESES_ES = ["enero","febrero","marzo","abril","mayo","junio","julio",
                    "agosto","septiembre","octubre","noviembre","diciembre"]
        hoy = datetime.now()
        mes_anterior = hoy.month - 1 or 12
        anio_reporte = hoy.year if hoy.month > 1 else hoy.year - 1
        nombre_mes = MESES_ES[mes_anterior - 1]

        async with httpx.AsyncClient(timeout=8.0) as client:
            # API DANE IPC construcción
            resp = await client.get(
                "https://www.dane.gov.co/files/investigaciones/boletines/ipc/"
                f"ipc_{nombre_mes}{anio_reporte}.json",
                follow_redirects=True,
                headers={"User-Agent": "PresupuestarCO/6.0"}
            )
            if resp.status_code == 200:
                data = resp.json()
                # Parsear variaciones por material si está disponible
                result_parsado = _parsear_ipc_dane(data)
                if result_parsado:
                    resultado = result_parsado
                    logger.info("IPC materiales DANE actualizado")
    except Exception as e:
        logger.warning(f"IPC DANE no disponible: {e}")

    _save_cache({**(_load_cache() or {}), "ipc_materiales": resultado})
    return resultado


def _parsear_ipc_dane(data: Dict) -> Optional[Dict]:
    """Parsea la respuesta del DANE según su estructura."""
    try:
        # La estructura del DANE varía — intentar varias posibilidades
        if "grupos" in data:
            return {
                grupo: {"variacion_anual": float(v.get("var_anual", 0)),
                        "factor": 1 + float(v.get("var_anual", 0))/100}
                for grupo, v in data["grupos"].items()
            }
    except Exception:
        pass
    return None


async def get_precios_actualizados(region: str = "bogota") -> Dict:
    """
    Retorna todos los precios actualizados con ICCV y factores regionales.
    """
    factores_region = {
        "bogota": 1.00, "medellin": 0.95, "cali": 0.92, "barranquilla": 0.97,
        "bucaramanga": 0.93, "pereira": 0.90, "cartagena": 0.96,
        "cucuta": 0.88, "ibague": 0.91, "manizales": 0.89,
        "villavicencio": 0.87, "monteria": 0.88, "pasto": 0.86,
    }
    fr = factores_region.get(region, 1.00)

    iccv = await get_factor_iccv()
    ipc = await get_ipc_materiales()

    factor_acero = ipc.get("acero", {}).get("factor", iccv["factor"])
    factor_cemento = ipc.get("cemento", {}).get("factor", iccv["factor"])
    factor_agregados = ipc.get("agregados", {}).get("factor", iccv["factor"])
    factor_general = iccv["factor"]

    # Factores específicos por perfil metálico
    # (PTE y PHR tienen márgenes diferentes)
    FACTOR_PERFIL = {
        "PTE":    factor_acero * 1.15,  # Acero + fabricación PTE
        "PHR":    factor_acero * 1.10,  # Acero + fabricación canal
        "ANGULO": factor_acero * 1.08,
        "W":      factor_acero * 1.20,  # Perfil importado
    }

    precios = {}
    for key, precio_base in PRECIOS_BASE_2026.items():
        if "acero" in key or "perfil" in key:
            factor = factor_acero
        elif "cemento" in key:
            factor = factor_cemento
        elif "arena" in key or "gravilla" in key:
            factor = factor_agregados
        else:
            factor = factor_general

        precios[key] = {
            "precio_base_2026": precio_base,
            "precio_actual": round(precio_base * factor * fr),
            "factor_iccv": round(factor, 4),
            "factor_region": fr,
            "variacion_pct": round((factor - 1) * 100, 1),
        }

    return {
        "region": region,
        "factor_region": fr,
        "iccv": iccv,
        "ipc_materiales": ipc,
        "precios": precios,
        "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "fuentes": ["DANE ICCV", "DANE IPC Construcción", "Bases APU 2026"],
        "nota": (
            f"Precios en COP actualizados con ICCV DANE ({iccv['fuente']}). "
            f"Factor acero: {factor_acero:.3f} | Cemento: {factor_cemento:.3f}"
        )
    }


def calcular_costo_materiales_concreto(
    volumen_m3: float, fc_mpa: float = 20.7, region: str = "bogota"
) -> Dict:
    """Costo materiales de concreto por volumen y resistencia."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../data'))
    try:
        from tablas_tecnicas import get_materiales_por_m3
        dos = get_materiales_por_m3(fc_mpa)
    except ImportError:
        dos = {"cemento_sacos_m3": 7.5, "arena_m3_por_m3": 0.52, "grava_m3_por_m3": 0.90,
               "proporcion": "1-2-3.5"}

    fr = {"bogota":1.00,"medellin":0.95,"cali":0.92,"barranquilla":0.97}.get(region, 1.00)
    p_c = round(PRECIOS_BASE_2026["cemento_50kg"] * fr)  # por saco 50kg — consistente con dos["cemento_sacos_m3"]
    p_a = round(PRECIOS_BASE_2026["arena_m3"] * fr)
    p_g = round(PRECIOS_BASE_2026["gravilla_m3"] * fr)

    sacos = dos["cemento_sacos_m3"] * volumen_m3
    arena = dos["arena_m3_por_m3"] * volumen_m3
    grava = dos["grava_m3_por_m3"] * volumen_m3

    return {
        "fc_mpa": fc_mpa, "volumen_m3": volumen_m3, "proporcion": dos.get("proporcion"),
        "cantidades": {"cemento_sacos": round(sacos,1), "arena_m3": round(arena,2), "grava_m3": round(grava,2)},
        "costos_cop": {
            "cemento": round(sacos*p_c), "arena": round(arena*p_a), "grava": round(grava*p_g),
            "total": round(sacos*p_c + arena*p_a + grava*p_g),
            "por_m3": round((sacos*p_c + arena*p_a + grava*p_g)/volumen_m3) if volumen_m3 else 0
        }
    }


def analisis_sensibilidad(total_cop: float, items: list) -> Dict:
    """Análisis de sensibilidad ante alzas de precios."""
    cat = lambda kw: sum(i.get("precio_total",0) for i in items
                         if kw in (i.get("nombre","") + i.get("capitulo","")).lower())
    acero   = cat("acero")
    conc    = cat("concreto")
    metal   = sum(i.get("precio_total",0) for i in items if i.get("capitulo","") == "ESTRUCTURA METÁLICA")

    escenarios = []
    for mat, monto, alzas in [
        ("Acero refuerzo",    acero,  [5,10,15,20]),
        ("Concreto/cemento",  conc,   [5,10,15]),
        ("Estructura metálica", metal,[5,10,15,20]),
    ]:
        if monto > 0:
            for alza in alzas:
                impacto = monto * alza / 100
                escenarios.append({
                    "material": mat, "alza_pct": alza,
                    "monto_actual": round(monto),
                    "impacto_cop": round(impacto),
                    "impacto_total_pct": round(impacto/total_cop*100, 2) if total_cop else 0,
                    "nuevo_total": round(total_cop + impacto),
                })

    return {
        "presupuesto_base": total_cop,
        "distribucion": {
            "acero_pct":   round(acero/total_cop*100, 1) if total_cop else 0,
            "concreto_pct":round(conc/total_cop*100,  1) if total_cop else 0,
            "metalica_pct":round(metal/total_cop*100, 1) if total_cop else 0,
        },
        "escenarios": escenarios,
        "recomendacion": (
            "Acero: material más volátil. Si obra > 3 meses, incluir cláusula "
            "de reajuste de precios (CONPES 3714). Cemento: estable, sin urgencia."
        )
    }
