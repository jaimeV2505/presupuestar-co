"""
Detector de escala gráfica en planos estructurales.
Detecta la barra de escala (ej: |---5m---|) en la imagen del plano
y calcula el factor px/m para medir elementos reales.

Funciona en dos modos:
  1. Lectura de texto: busca "ESCALA 1:75", "1:100", etc. en los textos del plano
  2. Detección visual: busca la barra gráfica con Pillow (sin OpenCV para ligereza)
"""
import re
import logging
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Escalas comunes en planos colombianos
ESCALAS_COMUNES = [
    (1, 25), (1, 50), (1, 75), (1, 100),
    (1, 125), (1, 150), (1, 200), (1, 250),
    (1, 300), (1, 400), (1, 500), (1, 750), (1, 1000),
]


@dataclass
class ResultadoEscala:
    escala_texto: str           # "1:75", "1:100", etc.
    numerador: int              # 1
    denominador: int            # 75
    factor_m_por_mm: float      # metros reales por mm en el plano
    confianza: str              # "alta", "media", "baja"
    metodo: str                 # "texto_plano", "titulo", "estimado"
    nota: str = ""


def detectar_escala_desde_textos(textos: list) -> Optional[ResultadoEscala]:
    """
    Detecta la escala leyendo los textos extraídos del plano.
    Busca patrones como: "ESCALA 1:75", "ESC: 1:100", "SCALE 1/50"
    """
    patrones = [
        r'ESC(?:ALA)?\.?\s*:?\s*(\d+)\s*[:/]\s*(\d+)',
        r'SCALE\s*:?\s*(\d+)\s*[:/]\s*(\d+)',
        r'E\s*=\s*(\d+)\s*[:/]\s*(\d+)',
        r'(\d+)\s*:\s*(\d+)',  # genérico como último recurso
    ]

    texto_completo = " ".join(textos).upper()

    for patron in patrones:
        matches = re.findall(patron, texto_completo)
        for m in matches:
            num, den = int(m[0]), int(m[1])
            # Validar que sea una escala razonable
            if num == 1 and den in [d for _, d in ESCALAS_COMUNES]:
                factor = den / num / 1000  # metros reales por mm de plano: 1mm papel = den mm reales
                return ResultadoEscala(
                    escala_texto=f"1:{den}",
                    numerador=num,
                    denominador=den,
                    factor_m_por_mm=factor,
                    confianza="alta",
                    metodo="texto_plano",
                    nota=f"Detectado en texto del plano"
                )
            # También aceptar escalas inversas como "75:1"
            elif den == 1 and num in [d for _, d in ESCALAS_COMUNES]:
                factor = num / 1000  # denominador real de la escala es "num" (ej: "75:1" -> escala 1:75)
                return ResultadoEscala(
                    escala_texto=f"1:{num}",
                    numerador=1,
                    denominador=num,
                    factor_m_por_mm=factor,
                    confianza="alta",
                    metodo="texto_plano",
                )

    return None


def detectar_escala_desde_imagen(img_bytes: bytes, ancho_imagen_px: int) -> Optional[ResultadoEscala]:
    """
    Detecta la barra de escala gráfica en la imagen del plano.
    Usa análisis de contraste horizontal para encontrar la regla.
    
    Retorna None si no puede detectar con confianza suficiente.
    """
    try:
        from PIL import Image
        import io
        import statistics

        img = Image.open(io.BytesIO(img_bytes)).convert('L')  # Escala de grises
        w, h = img.size

        # La barra de escala suele estar en las esquinas
        # Analizar franja inferior (último 15% del plano)
        franja_y_start = int(h * 0.82)
        franja = img.crop((0, franja_y_start, w, h))

        # Buscar líneas horizontales largas y delgadas (la barra de escala)
        # Convertir a matriz de píxeles
        pixels = list(franja.getdata())
        fw, fh = franja.size

        # Buscar filas con alta varianza (alternancias blanco/negro = barra de escala)
        candidatas = []
        for row in range(fh):
            fila = pixels[row * fw:(row + 1) * fw]
            # Buscar alternancia de valores extremos (negro/blanco)
            extremos = [p for p in fila if p < 50 or p > 200]
            if len(extremos) > fw * 0.3:  # Al menos 30% de la fila tiene contraste alto
                # Buscar longitud de la barra (segmento continuo)
                inicio, fin = _encontrar_barra_continua(fila)
                if fin - inicio > fw * 0.1:  # Barra de al menos 10% del ancho
                    candidatas.append((row, inicio, fin, fin - inicio))

        if not candidatas:
            return None

        # Tomar la barra más larga
        mejor = max(candidatas, key=lambda x: x[3])
        largo_px = mejor[3]

        # Ahora necesitamos saber cuántos metros representa esa barra
        # Para esto, buscamos el texto cerca de la barra ("5m", "10m", etc.)
        # Como no podemos hacer OCR fácilmente aquí, estimamos por el tamaño relativo

        # La barra de escala típicamente es el 10-20% del ancho del plano
        fraccion_ancho = largo_px / w

        # Estimación: planos A1 a escala 1:75 tienen barra de ~5m
        # Esto es heurístico — funciona para planos colombianos estándar
        if 0.10 <= fraccion_ancho <= 0.20:
            den_estimado = 75
        elif 0.08 <= fraccion_ancho < 0.10:
            den_estimado = 100
        elif 0.05 <= fraccion_ancho < 0.08:
            den_estimado = 150
        elif 0.03 <= fraccion_ancho < 0.05:
            den_estimado = 200
        else:
            return None

        # Verificar contra escalas conocidas
        for _, den in ESCALAS_COMUNES:
            if abs(den - den_estimado) <= 25:
                den_estimado = den
                break

        factor = den_estimado / 1000
        return ResultadoEscala(
            escala_texto=f"1:{den_estimado}",
            numerador=1,
            denominador=den_estimado,
            factor_m_por_mm=factor,
            confianza="baja",
            metodo="deteccion_visual",
            nota=f"Barra detectada ({largo_px}px = {fraccion_ancho:.1%} ancho). Confirmar con texto del plano."
        )

    except Exception as e:
        logger.warning(f"Detección visual de escala falló: {e}")
        return None


def _encontrar_barra_continua(fila: list) -> Tuple[int, int]:
    """Encuentra el segmento continuo más largo con contraste alto."""
    mejor_inicio, mejor_fin = 0, 0
    inicio_actual = None

    for i, px in enumerate(fila):
        if px < 80:  # Píxel oscuro (parte de la barra)
            if inicio_actual is None:
                inicio_actual = i
            if i - inicio_actual > mejor_fin - mejor_inicio:
                mejor_inicio = inicio_actual
                mejor_fin = i
        else:
            if px > 200 and inicio_actual is not None:
                pass  # Parte blanca de la barra alternada — OK
            elif inicio_actual is not None:
                inicio_actual = None

    return mejor_inicio, mejor_fin


def estimar_escala_por_contexto(tipo_plano: str, sistema: str) -> ResultadoEscala:
    """
    Estimación de escala basada en tipo de plano y sistema estructural.
    Fallback cuando no se puede detectar la escala.
    
    Basado en práctica colombiana:
    - Plantas de cimentación: 1:75 o 1:100
    - Cubiertas metálicas grandes: 1:150 o 1:200
    - Detalles: 1:25 o 1:50
    """
    tipo = tipo_plano.lower()
    sis = sistema.lower()

    if "detalle" in tipo or "seccion" in tipo:
        den = 25
    elif "cubierta" in tipo or "metalic" in sis:
        den = 150
    elif "cimentac" in tipo:
        den = 75
    elif "edificio" in tipo or "columnas" in tipo:
        den = 100
    else:
        den = 100  # Default más común

    return ResultadoEscala(
        escala_texto=f"1:{den}",
        numerador=1,
        denominador=den,
        factor_m_por_mm=den / 1000,
        confianza="baja",
        metodo="estimado",
        nota=f"Escala estimada por tipo de plano. Verificar manualmente."
    )


def calcular_dimension_real(
    dimension_px: float,
    escala: ResultadoEscala,
    dpi_imagen: int = 150
) -> float:
    """
    Convierte una dimensión en píxeles a metros reales.
    
    Args:
        dimension_px: Tamaño del elemento en píxeles
        escala: Resultado de detección de escala
        dpi_imagen: DPI de la imagen (150 por defecto en nuestro sistema)
    
    Returns:
        Dimensión en metros reales
    """
    # px → mm de papel (1 pulgada = 25.4mm)
    mm_papel = (dimension_px / dpi_imagen) * 25.4
    # mm de papel → metros reales
    metros_reales = mm_papel * escala.denominador / 1000
    return round(metros_reales, 3)


def detectar_escala(
    textos: list = None,
    img_bytes: bytes = None,
    tipo_plano: str = "",
    sistema: str = ""
) -> ResultadoEscala:
    """
    Función principal: detecta escala con todos los métodos disponibles.
    Prioridad: texto > visual > estimado.
    """
    # 1. Intentar desde textos (más confiable)
    if textos:
        resultado = detectar_escala_desde_textos(textos)
        if resultado:
            logger.info(f"Escala detectada en texto: {resultado.escala_texto}")
            return resultado

    # 2. Intentar detección visual
    if img_bytes:
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(img_bytes))
            resultado = detectar_escala_desde_imagen(img_bytes, img.width)
            if resultado:
                logger.info(f"Escala detectada visualmente: {resultado.escala_texto}")
                return resultado
        except Exception as e:
            logger.warning(f"Detección visual falló: {e}")

    # 3. Fallback: estimado por contexto
    resultado = estimar_escala_por_contexto(tipo_plano, sistema)
    logger.info(f"Escala estimada: {resultado.escala_texto} (confianza baja)")
    return resultado
