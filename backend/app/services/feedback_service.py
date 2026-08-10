"""
Sistema de Feedback Loop — PresupuestarCO v4.
El ingeniero corrige elementos → el sistema aprende patrones.

Flujo:
  1. Ingeniero corrige elemento en Paso 2 (StepExtraccion)
  2. Frontend envía corrección a POST /api/feedback/correccion
  3. FeedbackService guarda y extrae patrón
  4. Próximo análisis incluye los patrones aprendidos en el prompt (few-shot)
"""
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "../data/feedback_db.json")
)


def _load_db() -> Dict:
    try:
        with open(DB_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "version": "1.0",
            "correcciones": [],
            "patrones_aprendidos": {},
            "stats": {"total_planos": 0, "total_correcciones": 0, "precision_promedio": 0.0}
        }


def _save_db(db: Dict):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def registrar_analisis(plano_nombre: str, elementos_extraidos: int, confianza: str):
    """Registra que se analizó un plano."""
    db = _load_db()
    db["stats"]["total_planos"] += 1
    _save_db(db)
    logger.info(f"Análisis registrado: {plano_nombre} ({elementos_extraidos} elementos, confianza={confianza})")


def registrar_correccion(
    elemento_original: Dict,
    elemento_corregido: Dict,
    tipo_plano: str = "",
    contexto: str = ""
):
    """
    Registra una corrección del ingeniero y extrae el patrón aprendido.

    El patrón se construye así:
    - Clave: tipo_elemento + dimensiones_originales (lo que Claude vio mal)
    - Valor: la corrección correcta (lo que el ingeniero indicó)
    """
    db = _load_db()

    correccion = {
        "timestamp": datetime.now().isoformat(),
        "tipo_plano": tipo_plano,
        "original": elemento_original,
        "corregido": elemento_corregido,
        "campos_cambiados": _diff_elementos(elemento_original, elemento_corregido),
        "contexto": contexto,
    }
    db["correcciones"].append(correccion)
    db["stats"]["total_correcciones"] += 1

    # Extraer patrón aprendido
    patron = _extraer_patron(elemento_original, elemento_corregido)
    if patron:
        clave = patron["clave"]
        if clave not in db["patrones_aprendidos"]:
            db["patrones_aprendidos"][clave] = {
                "ejemplo_incorrecto": patron["incorrecto"],
                "ejemplo_correcto": patron["correcto"],
                "ocurrencias": 0,
                "tipo": elemento_original.get("tipo", ""),
            }
        db["patrones_aprendidos"][clave]["ocurrencias"] += 1
        logger.info(f"Patrón aprendido: '{clave}' (ocurrencias: {db['patrones_aprendidos'][clave]['ocurrencias']})")

    _save_db(db)
    return {"ok": True, "patrones_totales": len(db["patrones_aprendidos"])}


def _diff_elementos(orig: Dict, corr: Dict) -> List[str]:
    """Detecta qué campos cambiaron entre el original y el corregido."""
    campos = []
    for key in set(list(orig.keys()) + list(corr.keys())):
        if orig.get(key) != corr.get(key):
            campos.append(key)
    return campos


def _extraer_patron(orig: Dict, corr: Dict) -> Optional[Dict]:
    """
    Extrae un patrón reutilizable de la corrección.
    Retorna None si no hay un patrón claro.
    """
    tipo = orig.get("tipo", "")
    nombre_orig = orig.get("nombre", "")
    nombre_corr = corr.get("nombre", "")

    # Patrón: Claude confundió el tipo de elemento
    if orig.get("tipo") != corr.get("tipo"):
        return {
            "clave": f"tipo_{tipo}_a_{corr.get('tipo')}_{nombre_orig[:20]}",
            "incorrecto": f"tipo='{tipo}', nombre='{nombre_orig}'",
            "correcto": f"tipo='{corr.get('tipo')}', nombre='{nombre_corr}'",
        }

    # Patrón: Claude se equivocó con las dimensiones
    dims_orig = {k: orig.get(k) for k in ["dimension_ancho_cm", "dimension_alto_cm",
                                            "dimension_largo_m", "altura_libre_m", "espesor_cm"]}
    dims_corr = {k: corr.get(k) for k in dims_orig.keys()}
    if dims_orig != dims_corr:
        return {
            "clave": f"dims_{tipo}_{nombre_orig[:20]}",
            "incorrecto": str(dims_orig),
            "correcto": str(dims_corr),
        }

    # Patrón: Claude se equivocó con la cantidad
    if orig.get("cantidad") != corr.get("cantidad"):
        return {
            "clave": f"cant_{tipo}_{nombre_orig[:20]}",
            "incorrecto": f"cantidad={orig.get('cantidad')} {orig.get('unidad')}",
            "correcto": f"cantidad={corr.get('cantidad')} {corr.get('unidad')}",
        }

    return None


def get_few_shot_prompt(tipo_plano: str = "", limite: int = 5) -> str:
    """
    Genera el bloque de few-shot learning para incluir en el prompt de Claude.
    Incluye los patrones más frecuentes y ejemplos reales corregidos por ingenieros.
    """
    db = _load_db()

    ejemplos_base = _get_ejemplos_base(tipo_plano)
    patrones = db.get("patrones_aprendidos", {})

    if not patrones and not ejemplos_base:
        return ""

    lines = ["EJEMPLOS REALES DE EXTRACCIÓN CORRECTA (aprendidos de ingenieros colombianos):\n"]

    # Ejemplos base hardcoded (few-shot inicial)
    lines.append(ejemplos_base)

    # Patrones aprendidos del feedback (los más frecuentes)
    if patrones:
        top_patrones = sorted(patrones.items(), key=lambda x: x[1]["ocurrencias"], reverse=True)[:limite]
        lines.append("\nCORRECCIONES APRENDIDAS EN CAMPO:")
        for clave, data in top_patrones:
            lines.append(f"  ✗ Incorrecto: {data['ejemplo_incorrecto']}")
            lines.append(f"  ✓ Correcto:   {data['ejemplo_correcto']}")
            lines.append(f"  (corregido {data['ocurrencias']} veces por ingenieros)")
            lines.append("")

    return "\n".join(lines)


def _get_ejemplos_base(tipo_plano: str = "") -> str:
    """
    Ejemplos base de few-shot por tipo de plano.
    Estos son ejemplos hardcoded basados en planos colombianos reales.
    """

    base = """
EJEMPLOS DE CUADRO DE COLUMNAS (plano estructural colombiano):
  Referencia: C1 | Sección: 30x30cm | Altura: 3.0m | Cant: 8 | Acero: 4Ø5/8"+estrib #3@15cm
  → tipo="columnas", nombre="Columna C1 30x30cm", cantidad=8, unidad="un",
    dimension_ancho_cm=30, dimension_alto_cm=30, altura_libre_m=3.0,
    acero_longitudinal="4Ø5/8\"", acero_transversal="#3@15cm"

  Referencia: C2 | Sección: PTE 250x250x9mm | H: 7.80m | Cant: 12
  → tipo="columnas", nombre="Columna metálica PTE 250x250x9mm", cantidad=12, unidad="un",
    dimension_ancho_cm=25, dimension_alto_cm=25, altura_libre_m=7.80,
    material="PTE 250x250x9mm ASTM A500 Gr.C"

EJEMPLOS DE CUADRO DE VIGAS:
  Referencia: VP-1 | Sección: 25x50cm | L promedio: 5.80m | Cant: 6
  → tipo="vigas", nombre="Viga principal VP-1 25x50cm", cantidad=6, unidad="un",
    dimension_ancho_cm=25, dimension_alto_cm=50, dimension_largo_m=5.80

  PHR 160x60x2mm | Longitud total: 695m (correas)
  → tipo="cubierta", nombre="Correa PHR 160x60x2mm", cantidad=695, unidad="m",
    material="PHR 160x60x2mm NTC 2086"

EJEMPLOS DE ZAPATAS:
  Z-1: 1 und, 1.60x1.60x0.30m, 6Ø5/8"@0.30 L=1.45m
  → tipo="cimentacion", referencia="Z-1", nombre="Zapata Z-1 1.60x1.60m",
    cantidad=1, unidad="un", dimension_ancho_cm=160, dimension_alto_cm=160,
    espesor_cm=30, acero_longitudinal="6Ø5/8\"@0.30 L=1.45m"

  Z-2: 3 und, 1.25x1.25x0.30m, 5Ø5/8"@0.30 L=1.05m
  → tipo="cimentacion", referencia="Z-2", nombre="Zapata Z-2 1.25x1.25m",
    cantidad=3, unidad="un", dimension_ancho_cm=125, dimension_alto_cm=125, espesor_cm=30

PERFILES METÁLICOS — PESOS UNITARIOS REALES (kg/m):
  PTE 250x250x9mm → 68.34 kg/m
  PHR 160x60x2mm  → 4.50 kg/m
  PHR 203x67x2.5  → 7.03 kg/m
  PTE 100x100x3mm → 9.20 kg/m
  Angulo 1-1/4"x1/8 → 1.54 kg/m
  Tensor varilla lisa 5/8" → 1.55 kg/m

REGLAS IMPORTANTES PARA COLOMBIA:
  - Los pedestales (PED) siempre van separados de las zapatas
  - Un "Pedestal 55x55 L=1.65m" es una columna corta de concreto sobre la zapata
  - Las vigas de amarre (VGA) son diferentes de las vigas principales (VP)
  - Un nivel de desplante "-2.00m" significa prof de excavación = 2.0m
  - El cárcamo (detalle especial) es un canal de desagüe, NO una viga
"""

    if "cubierta" in tipo_plano.lower() or "metalic" in tipo_plano.lower():
        base += """
ADICIONAL PARA CUBIERTAS METÁLICAS:
  - Las CERCHAS se cuantifican en metros lineales de cada perfil componente
  - Las CORREAS son el PHR horizontal entre cerchas
  - Los TEMPLEROS son las riostras diagonales en Cruz de San Andrés
  - La VIGA DE AMARRE es el PHR CAJÓN que une las cerchas a la cumbrera
  - Siempre separar: perfiles principales (PTE 100x100) vs secundarios (PTE 60x60)
  - Angulo 1-1/4"x1/8 = angular de unión para fijación de correas
"""

    if "cimentac" in tipo_plano.lower():
        base += """
ADICIONAL PARA PLANOS DE CIMENTACIÓN:
  - Siempre extraer CADA tipo de zapata por separado (Z-1, Z-2, Z-3...)
  - Los CAISSONES se identifican por su diámetro y profundidad
  - La VIGA DE AMARRE conecta zapatas y tiene sección típica 15x20cm o 15x30cm
  - La PLACA DE CONTRAPISO es diferente de la zapata
"""

    return base


def get_stats() -> Dict:
    """Estadísticas del sistema de aprendizaje."""
    db = _load_db()
    patrones = db.get("patrones_aprendidos", {})
    correcciones = db.get("correcciones", [])

    # Top campos más corregidos
    campos_freq = {}
    for c in correcciones:
        for campo in c.get("campos_cambiados", []):
            campos_freq[campo] = campos_freq.get(campo, 0) + 1

    return {
        **db["stats"],
        "patrones_aprendidos": len(patrones),
        "top_correcciones": sorted(campos_freq.items(), key=lambda x: x[1], reverse=True)[:5],
        "top_patrones": [
            {"patron": k, "ocurrencias": v["ocurrencias"], "tipo": v["tipo"]}
            for k, v in sorted(patrones.items(), key=lambda x: x[1]["ocurrencias"], reverse=True)[:5]
        ]
    }


def limpiar_patrones_antiguos(dias: int = 90):
    """Limpia correcciones de más de N días (mantenimiento)."""
    db = _load_db()
    from datetime import timedelta
    limite = (datetime.now() - timedelta(days=dias)).isoformat()
    antes = len(db["correcciones"])
    db["correcciones"] = [c for c in db["correcciones"] if c.get("timestamp", "") > limite]
    despues = len(db["correcciones"])
    _save_db(db)
    logger.info(f"Limpieza: {antes - despues} correcciones eliminadas (>{dias} días)")
    return {"eliminadas": antes - despues, "restantes": despues}
