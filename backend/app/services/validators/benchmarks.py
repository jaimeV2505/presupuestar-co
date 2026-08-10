"""
Validación cruzada de cantidades contra benchmarks reales de ingeniería.
Un ingeniero con experiencia siempre pregunta: ¿esto tiene sentido?

Benchmarks calibrados con proyectos reales colombianos 2020-2026.
Fuente: Escuela de Contratistas, CAMACOL, proyectos reales analizados.
"""
import math
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class AlertaBenchmark:
    tipo: str           # "SUBESTIMADO" | "SOBREESTIMADO" | "OK" | "VERIFICAR"
    mensaje: str
    valor_calculado: float
    rango_esperado: Tuple[float, float]
    unidad: str
    recomendacion: str
    confianza: str      # "alta" | "media" | "baja"


@dataclass
class ResultadoBenchmark:
    alertas: List[AlertaBenchmark] = field(default_factory=list)
    indicadores: Dict = field(default_factory=dict)
    resumen: str = ""
    pasa_validacion: bool = True


# ── Benchmarks por tipo de estructura ─────────────────────────────────────────
# Fuente: Proyectos reales Colombia | Escuela de Contratistas | CAMACOL
# Unidades: kg/m², COP/m², m³/m², etc. según tipo

BENCHMARKS_METALICA = {
    # Cubierta metálica
    "cubierta_liviana":  {"kg_m2": (12, 22),  "desc": "Cubierta metálica liviana (PTE pequeños, correas livianas)"},
    "cubierta_pesada":   {"kg_m2": (28, 48),  "desc": "Cubierta metálica pesada (PTE 250+, cerchas Warren)"},
    "cubierta_deportiva":{"kg_m2": (30, 50),  "desc": "Cubierta deportiva (coliseo, cancha)"},
    "bodega_industrial": {"kg_m2": (18, 35),  "desc": "Bodega industrial (pórticos metálicos)"},
    # Columnas metálicas
    "columna_PTE_ligera": {"kg_ml": (18, 35),  "desc": "Columna PTE liviana (PTE100-150)"},
    "columna_PTE_pesada": {"kg_ml": (60, 100), "desc": "Columna PTE pesada (PTE200-300)"},
}

BENCHMARKS_CONCRETO = {
    # Acero de refuerzo
    "vivienda_1piso":    {"kg_m2": (60,  100), "desc": "Vivienda unifamiliar 1 piso"},
    "vivienda_2pisos":   {"kg_m2": (80,  130), "desc": "Vivienda 2 pisos"},
    "edificio_3_5pisos": {"kg_m2": (120, 200), "desc": "Edificio residencial 3-5 pisos"},
    "edificio_6_10pisos":{"kg_m2": (180, 280), "desc": "Edificio residencial 6-10 pisos"},
    "comercial":         {"kg_m2": (150, 250), "desc": "Edificio comercial u oficinas"},
    "industrial":        {"kg_m2": (80,  150), "desc": "Industrial / bodega concreto"},
    # Concreto
    "concreto_m3_m2_vivienda": {"m3_m2": (0.20, 0.35), "desc": "m³ concreto por m² de placa"},
    # Cimentación
    "zapata_acero_kg": {"kg_und": (60, 180),   "desc": "Acero por zapata aislada"},
    "zapata_concreto_m3": {"m3_und": (0.4, 2.5),"desc": "Concreto por zapata aislada"},
}

BENCHMARKS_COSTOS = {
    # Costo por m² construido (COP 2026, sin AIU ni IVA)
    "vivienda_VIS":       {"cop_m2": (800_000,  1_200_000), "desc": "Vivienda VIS"},
    "vivienda_estrato3_4":{"cop_m2": (1_200_000,2_000_000), "desc": "Vivienda estrato 3-4"},
    "vivienda_estrato5_6":{"cop_m2": (2_000_000,4_000_000), "desc": "Vivienda estrato 5-6"},
    "cubierta_metalica":  {"cop_m2": (180_000,  350_000),   "desc": "Cubierta metálica (solo estructura)"},
    "bodega_industrial":  {"cop_m2": (400_000,  800_000),   "desc": "Bodega industrial"},
}


def validar_cubierta_metalica(
    elementos: List[Dict],
    area_m2: float,
    total_cop: float,
    sistema: str = ""
) -> ResultadoBenchmark:
    """
    Valida una cubierta metálica contra benchmarks reales.
    El ingeniero pregunta: ¿cuántos kg/m² tiene? ¿es razonable?
    """
    resultado = ResultadoBenchmark()
    if area_m2 <= 0:
        resultado.resumen = "No se puede validar: área no detectada"
        return resultado

    # Calcular kg totales de estructura metálica
    kg_total = sum(
        el.get("cantidad", 0) * _get_kg_m(el)
        for el in elementos
        if _es_metalico(el)
    )

    if kg_total <= 0:
        resultado.alertas.append(AlertaBenchmark(
            tipo="VERIFICAR",
            mensaje="No se detectó acero estructural metálico en los elementos",
            valor_calculado=0,
            rango_esperado=(12, 50),
            unidad="kg/m²",
            recomendacion="Verificar si el sistema extractó correctamente los perfiles metálicos",
            confianza="alta"
        ))
        resultado.pasa_validacion = False
        return resultado

    kg_m2 = kg_total / area_m2

    # Determinar tipo de cubierta por los perfiles detectados
    tiene_PTE250 = any("250" in (el.get("nombre","") + el.get("material","")) for el in elementos)
    tiene_cercha = any("cercha" in el.get("nombre","").lower() or
                       "100x100" in (el.get("nombre","") + el.get("material",""))
                       for el in elementos)

    if tiene_PTE250 or tiene_cercha:
        bench_key = "cubierta_deportiva"
        rango = BENCHMARKS_METALICA["cubierta_deportiva"]["kg_m2"]
    else:
        bench_key = "cubierta_liviana"
        rango = BENCHMARKS_METALICA["cubierta_liviana"]["kg_m2"]

    resultado.indicadores["kg_total_acero"] = round(kg_total, 1)
    resultado.indicadores["kg_m2"] = round(kg_m2, 2)
    resultado.indicadores["area_m2"] = area_m2
    resultado.indicadores["rango_esperado_kg_m2"] = rango

    if kg_m2 < rango[0] * 0.7:
        resultado.alertas.append(AlertaBenchmark(
            tipo="SUBESTIMADO",
            mensaje=f"Acero muy bajo: {kg_m2:.1f} kg/m² — rango normal {rango[0]}-{rango[1]} kg/m²",
            valor_calculado=kg_m2,
            rango_esperado=rango,
            unidad="kg/m²",
            recomendacion=(
                f"Probable que falten perfiles. Esperados: {area_m2*rango[0]:.0f}-{area_m2*rango[1]:.0f} kg total. "
                f"Revisar correas, ángulos y tensores que pueden no haberse cuantificado."
            ),
            confianza="alta"
        ))
        resultado.pasa_validacion = False

    elif kg_m2 > rango[1] * 1.3:
        resultado.alertas.append(AlertaBenchmark(
            tipo="SOBREESTIMADO",
            mensaje=f"Acero alto: {kg_m2:.1f} kg/m² — rango normal {rango[0]}-{rango[1]} kg/m²",
            valor_calculado=kg_m2,
            rango_esperado=rango,
            unidad="kg/m²",
            recomendacion="Posible doble conteo de perfiles. Verificar que no se sume el mismo perfil dos veces.",
            confianza="media"
        ))

    else:
        resultado.alertas.append(AlertaBenchmark(
            tipo="OK",
            mensaje=f"Acero en rango: {kg_m2:.1f} kg/m² — rango {rango[0]}-{rango[1]} kg/m²",
            valor_calculado=kg_m2,
            rango_esperado=rango,
            unidad="kg/m²",
            recomendacion="",
            confianza="alta"
        ))

    # Validar costo por m²
    if total_cop > 0:
        cop_m2 = total_cop / area_m2
        rango_cop = BENCHMARKS_COSTOS["cubierta_metalica"]["cop_m2"]
        resultado.indicadores["cop_m2"] = round(cop_m2)

        if cop_m2 < rango_cop[0] * 0.6:
            resultado.alertas.append(AlertaBenchmark(
                tipo="SUBESTIMADO",
                mensaje=f"Costo bajo: ${cop_m2:,.0f}/m² — normal ${rango_cop[0]:,}-${rango_cop[1]:,}/m²",
                valor_calculado=cop_m2,
                rango_esperado=rango_cop,
                unidad="COP/m²",
                recomendacion="El presupuesto puede estar incompleto. Revisar montaje, pintura anticorrosiva y platinería.",
                confianza="alta"
            ))

    resultado.resumen = (
        f"Cubierta {area_m2:.0f}m²: {kg_total:.0f}kg acero ({kg_m2:.1f}kg/m²). "
        f"{'✓ Dentro del rango' if resultado.pasa_validacion else '⚠ Fuera del rango esperado'}"
    )
    return resultado


def validar_edificio_concreto(
    elementos: List[Dict],
    area_m2: float,
    num_pisos: int,
    total_cop: float
) -> ResultadoBenchmark:
    """Valida edificio de concreto reforzado contra benchmarks."""
    resultado = ResultadoBenchmark()
    if area_m2 <= 0: return resultado

    # kg acero de refuerzo total
    kg_acero = sum(
        el.get("cantidad", 0)
        for el in elementos
        if "acero" in el.get("nombre","").lower() or el.get("unidad","") == "Kg"
    )

    # m³ concreto total
    m3_concreto = sum(
        el.get("cantidad", 0)
        for el in elementos
        if el.get("unidad","") == "m3" or el.get("unidad","") == "m³"
    )

    if num_pisos <= 2:
        bench = "vivienda_2pisos"
    elif num_pisos <= 5:
        bench = "edificio_3_5pisos"
    else:
        bench = "edificio_6_10pisos"

    rango = BENCHMARKS_CONCRETO[bench]["kg_m2"]
    kg_m2 = kg_acero / area_m2 if area_m2 > 0 else 0

    resultado.indicadores = {
        "kg_acero_total": round(kg_acero, 1),
        "m3_concreto_total": round(m3_concreto, 2),
        "kg_m2_acero": round(kg_m2, 1),
        "m3_m2_concreto": round(m3_concreto / area_m2, 3) if area_m2 > 0 else 0,
        "num_pisos": num_pisos,
    }

    if kg_acero > 0:
        if kg_m2 < rango[0] * 0.7:
            resultado.alertas.append(AlertaBenchmark(
                tipo="SUBESTIMADO",
                mensaje=f"Acero bajo: {kg_m2:.0f}kg/m² — rango {rango[0]}-{rango[1]}kg/m² para {num_pisos} pisos",
                valor_calculado=kg_m2, rango_esperado=rango, unidad="kg/m²",
                recomendacion=f"Esperado: {area_m2*rango[0]:.0f}-{area_m2*rango[1]:.0f}kg total. Revisar acero de losas y vigas.",
                confianza="alta"
            ))
            resultado.pasa_validacion = False
        elif kg_m2 <= rango[1] * 1.2:
            resultado.alertas.append(AlertaBenchmark(
                tipo="OK",
                mensaje=f"Acero en rango: {kg_m2:.0f}kg/m²",
                valor_calculado=kg_m2, rango_esperado=rango, unidad="kg/m²",
                recomendacion="", confianza="alta"
            ))

    resultado.resumen = f"Edificio {num_pisos}p, {area_m2:.0f}m²: {kg_acero:.0f}kg acero ({kg_m2:.0f}kg/m²)"
    return resultado


def validar_cimentacion(
    elementos: List[Dict],
    fc_mpa: float = 20.7
) -> ResultadoBenchmark:
    """Valida cimentación — zapatas y caissones."""
    resultado = ResultadoBenchmark()

    zapatas = [el for el in elementos if el.get("tipo") == "cimentacion"]
    caissones = [el for el in elementos if "caisson" in el.get("tipo","").lower() or
                 "caisson" in el.get("nombre","").lower()]

    for zapata in zapatas:
        cant = zapata.get("cantidad", 1)
        a = (zapata.get("dimension_ancho_cm") or 120) / 100
        b = (zapata.get("dimension_alto_cm") or 120) / 100
        h = (zapata.get("espesor_cm") or 30) / 100
        vol = a * b * h * cant
        nombre = zapata.get("referencia") or zapata.get("nombre","Zapata")

        rango_vol = BENCHMARKS_CONCRETO["zapata_concreto_m3"]["m3_und"]
        vol_und = vol / cant if cant > 0 else 0

        if vol_und < rango_vol[0]:
            resultado.alertas.append(AlertaBenchmark(
                tipo="VERIFICAR",
                mensaje=f"{nombre}: volumen {vol_und:.2f}m³/und parece bajo (mín ref {rango_vol[0]}m³)",
                valor_calculado=vol_und, rango_esperado=rango_vol, unidad="m³/und",
                recomendacion=f"Verificar dimensiones de {nombre}: {a*100:.0f}×{b*100:.0f}×{h*100:.0f}cm",
                confianza="media"
            ))
        elif vol_und > rango_vol[1]:
            resultado.alertas.append(AlertaBenchmark(
                tipo="VERIFICAR",
                mensaje=f"{nombre}: volumen {vol_und:.2f}m³/und es grande — confirmar dimensiones",
                valor_calculado=vol_und, rango_esperado=rango_vol, unidad="m³/und",
                recomendacion="Zapata grande puede requerir análisis de fisuración (f'c ≥ 28MPa recomendado)",
                confianza="media"
            ))

    resultado.indicadores["num_zapatas_tipos"] = len(zapatas)
    resultado.indicadores["num_caissones"] = len(caissones)
    resultado.resumen = f"Cimentación: {len(zapatas)} tipos de zapata, {len(caissones)} caissones"
    return resultado


def validar_completo(
    elementos: List[Dict],
    sistema_estructural: str,
    area_m2: float,
    num_pisos: int,
    total_cop: float,
    fc_mpa: float = 20.7
) -> Dict:
    """
    Validación cruzada completa como lo haría un ingeniero experimentado.
    Retorna alertas, indicadores y resumen ejecutivo.
    """
    alertas_todas = []
    indicadores = {}
    resumenes = []

    sis = sistema_estructural.lower()
    es_metalica = any(x in sis for x in ["metal", "pte", "phr", "acero"])
    es_concreto = any(x in sis for x in ["concreto", "pórtico", "portico"])

    if es_metalica and area_m2 > 0:
        res = validar_cubierta_metalica(elementos, area_m2, total_cop, sistema_estructural)
        alertas_todas.extend(res.alertas)
        indicadores.update(res.indicadores)
        resumenes.append(res.resumen)

    if es_concreto and area_m2 > 0 and num_pisos > 0:
        res = validar_edificio_concreto(elementos, area_m2, num_pisos, total_cop)
        alertas_todas.extend(res.alertas)
        indicadores.update(res.indicadores)
        resumenes.append(res.resumen)

    res_cim = validar_cimentacion(elementos, fc_mpa)
    alertas_todas.extend(res_cim.alertas)
    indicadores.update(res_cim.indicadores)
    if res_cim.resumen:
        resumenes.append(res_cim.resumen)

    # Clasificar alertas
    errores = [a for a in alertas_todas if a.tipo in ("SUBESTIMADO","SOBREESTIMADO")]
    oks     = [a for a in alertas_todas if a.tipo == "OK"]

    return {
        "pasa_validacion": len(errores) == 0,
        "alertas": [
            {
                "tipo": a.tipo,
                "mensaje": a.mensaje,
                "valor_calculado": a.valor_calculado,
                "rango_esperado": list(a.rango_esperado),
                "unidad": a.unidad,
                "recomendacion": a.recomendacion,
                "confianza": a.confianza,
            }
            for a in alertas_todas
        ],
        "indicadores": indicadores,
        "resumen": " | ".join(resumenes) if resumenes else "Sin benchmarks aplicables",
        "num_alertas_criticas": len(errores),
        "num_ok": len(oks),
    }


def _es_metalico(el: Dict) -> bool:
    texto = (el.get("nombre","") + el.get("material","") + el.get("tipo","")).upper()
    return any(x in texto for x in ["PTE","PHR","ANGULO","CERCHA","CORREA","METALIC","W10","W18","IPE"])


def _get_kg_m(el: Dict) -> float:
    """Peso en kg/m del elemento metálico — usa BD de perfiles si disponible."""
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
        from services.apu_service import get_peso_perfil
        nombre = el.get("nombre","") + " " + el.get("material","")
        peso = get_peso_perfil(nombre)
        if peso: return peso
    except Exception:
        pass
    # Fallback por tipo
    nombre = (el.get("nombre","") + el.get("material","")).upper()
    if "250X250X9" in nombre: return 68.34
    if "100X100X3" in nombre: return 9.20
    if "60X60X2.5" in nombre: return 4.39
    if "203X67"    in nombre: return 7.03
    if "355X110"   in nombre: return 9.50
    return 8.0  # estimado genérico kg/m
