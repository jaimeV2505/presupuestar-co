"""
Extractor de cotas de planos estructurales usando Pillow.
Detecta líneas de dimensión y extrae el texto de la cota asociada.
Sin OpenCV — solo Pillow que ya está instalado.
"""
import io, re, logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CotaDetectada:
    valor_m: float          # Valor en metros
    texto_original: str     # Texto tal como aparece en el plano
    confianza: float        # 0-1
    ubicacion: str          # "horizontal" | "vertical" | "desconocida"


def extraer_cotas_de_imagen(img_bytes: bytes, escala_denominador: int = 100) -> List[CotaDetectada]:
    """
    Extrae cotas de dimensión de la imagen del plano.
    
    Estrategia: buscar patrones numéricos con unidades en el texto
    extraído por región de contraste alto (donde están las cotas).
    
    Retorna lista de valores en metros.
    """
    cotas = []
    
    try:
        from PIL import Image, ImageFilter
        import io
        
        img = Image.open(io.BytesIO(img_bytes)).convert('L')
        w, h = img.size
        
        # Las cotas suelen estar en zonas de texto pequeño fuera de los elementos
        # Estrategia: analizar el texto de la imagen con regiones de contraste
        cotas_texto = _extraer_cotas_por_patrones_texto(img_bytes, escala_denominador)
        cotas.extend(cotas_texto)
        
    except Exception as e:
        logger.warning(f"OCR cotas falló: {e}")
    
    return cotas


def _extraer_cotas_por_patrones_texto(img_bytes: bytes, escala: int) -> List[CotaDetectada]:
    """
    Extrae cotas buscando patrones numéricos conocidos en planos colombianos.
    Usa heurísticas sobre cómo se escriben las cotas en AutoCAD colombia:
    - En metros: "5.80", "18.50", "29.00"
    - En centímetros: "30", "55", "1.20" (ambiguo)
    - Con unidad: "5.80m", "580cm"
    """
    cotas = []
    
    # Patrones típicos de cotas en planos colombianos
    patrones_m = [
        r'\b(\d+\.\d{2})\s*m\b',           # 5.80m
        r'\b(\d+[.,]\d{2})\b(?=\s*m)',      # 5.80 m
    ]
    patrones_cm = [
        r'\b(\d{2,4})\s*cm\b',              # 580cm, 30cm
    ]
    patrones_ambiguos = [
        r'\b(\d+[.,]\d{2})\b',              # 5.80 (puede ser m o m)
        r'\b(\d+)\b(?=\s+\d)',               # 30 (cm si < 100, m si > 100)
    ]
    
    # Por ahora retornamos lista vacía — el OCR real requeriría Tesseract
    # que no está instalado. En cambio, las cotas las extrae Claude Vision.
    # Esta función sirve de placeholder para cuando se integre Tesseract.
    return []


def extraer_dimensiones_de_textos(textos: List[str], escala_denominador: int = 100) -> List[float]:
    """
    Extrae dimensiones en metros de una lista de textos del plano.
    Funciona con los textos extraídos por ezdxf o Claude Vision.
    
    Esta es la función principal que SÍ funciona sin Tesseract.
    """
    dimensiones_m = []
    
    patrones = [
        # Metros explícitos
        (r'(\d+[.,]\d+)\s*m\b', 1.0),
        # Centímetros explícitos  
        (r'(\d+[.,]?\d*)\s*cm\b', 0.01),
        # Milímetros (AutoCAD)
        (r'(\d+)\s*mm\b', 0.001),
        # Fracción de metro sin unidad (ej: 5.80 en planos a escala)
        (r'\b(\d+\.\d{2})\b', 1.0),
        # Solo centímetros (ej: "30", "55" en cuadros de columnas)
        (r'\b([2-9]\d|[1-9]\d{2})\b(?!\s*[×xX])', 0.01),
    ]
    
    for texto in textos:
        t = texto.replace(',', '.')
        for patron, factor in patrones:
            matches = re.findall(patron, t, re.IGNORECASE)
            for m in matches:
                try:
                    val = float(m) * factor
                    if 0.05 <= val <= 100:  # Rango razonable para elementos estructurales
                        dimensiones_m.append(round(val, 3))
                except ValueError:
                    pass
    
    return list(set(dimensiones_m))  # Eliminar duplicados


def enriquecer_contexto_con_cotas(
    textos_dwg: List[str],
    escala_denominador: int,
    tipo_plano: str
) -> str:
    """
    Genera contexto adicional con las cotas detectadas en el plano.
    Este contexto se agrega al prompt de Claude para mejorar la extracción.
    """
    dims = extraer_dimensiones_de_textos(textos_dwg, escala_denominador)
    
    if not dims:
        return ""
    
    dims_sorted = sorted(set(dims))
    
    # Clasificar por rango
    dims_col = [d for d in dims_sorted if 0.20 <= d <= 1.00]   # dimensiones de sección
    dims_vano = [d for d in dims_sorted if 2.0 <= d <= 15.0]    # vanos y longitudes
    dims_altura = [d for d in dims_sorted if 2.5 <= d <= 12.0]  # alturas de piso
    
    ctx = f"COTAS DETECTADAS EN EL PLANO (escala 1:{escala_denominador}):\n"
    if dims_col:
        ctx += f"  Secciones: {[f'{d*100:.0f}cm' for d in dims_col[:6]]}\n"
    if dims_vano:
        ctx += f"  Vanos/longitudes: {[f'{d:.2f}m' for d in dims_vano[:8]]}\n"
    if dims_altura:
        ctx += f"  Alturas: {[f'{d:.2f}m' for d in dims_altura[:4]]}\n"
    
    return ctx
