# -*- coding: utf-8 -*-
"""
OCR de cotas en planos estructurales con Tesseract — v6.

Estrategia de 3 capas:
  1. OCR directo sobre la imagen completa (rapido, para textos grandes)
  2. OCR por zonas de alta densidad de texto (para cuadros de columnas)
  3. OCR sobre recortes de lineas de dimension (para cotas numericas)

Retorna un contexto enriquecido para pasar a Claude con todos los
valores numericos detectados en el plano.
"""
import io
import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Disponibilidad de Tesseract
TESSERACT_OK = False
try:
    import pytesseract
    from PIL import Image, ImageFilter, ImageEnhance
    pytesseract.get_tesseract_version()
    TESSERACT_OK = True
    logger.info("Tesseract OCR disponible")
except Exception as e:
    logger.warning(f"Tesseract no disponible: {e}")


@dataclass
class CotaOCR:
    valor_texto: str        # "7.80m", "580cm", "30"
    valor_m: float          # valor en metros
    confianza: float        # 0-1
    tipo: str               # "longitud" | "seccion" | "altura" | "area" | "desconocido"
    contexto: str           # texto cercano para identificar a que elemento corresponde


@dataclass
class ResultadoOCR:
    texto_completo: str = ""
    cotas: List[CotaOCR] = field(default_factory=list)
    especificaciones: Dict = field(default_factory=dict)
    cuadros_detectados: List[Dict] = field(default_factory=list)
    contexto_para_claude: str = ""
    tesseract_usado: bool = False


def procesar_imagen_plano(img_bytes: bytes, escala_denominador: int = 100) -> ResultadoOCR:
    """
    Funcion principal: aplica OCR a la imagen del plano y extrae
    toda la informacion textual relevante para el presupuesto.
    """
    resultado = ResultadoOCR()

    if not TESSERACT_OK:
        resultado.contexto_para_claude = ""
        return resultado

    try:
        from PIL import Image
        img = Image.open(io.BytesIO(img_bytes))
        resultado.tesseract_usado = True

        # CAPA 1: OCR completo de la imagen
        texto_raw = _ocr_imagen_completa(img)
        resultado.texto_completo = texto_raw

        # CAPA 2: Extraer cotas y dimensiones del texto
        resultado.cotas = _extraer_cotas(texto_raw, escala_denominador)

        # CAPA 3: Extraer especificaciones tecnicas
        resultado.especificaciones = _extraer_especificaciones(texto_raw)

        # CAPA 4: Detectar cuadros de columnas/vigas
        resultado.cuadros_detectados = _detectar_cuadros(texto_raw)

        # CAPA 5: Generar contexto para Claude
        resultado.contexto_para_claude = _generar_contexto(resultado)

        logger.info(
            f"OCR: {len(texto_raw)} chars | "
            f"{len(resultado.cotas)} cotas | "
            f"{len(resultado.cuadros_detectados)} cuadros"
        )

    except Exception as e:
        logger.warning(f"OCR fallo: {e}")

    return resultado


def _ocr_imagen_completa(img) -> str:
    """
    OCR sobre la imagen completa con preprocesamiento para planos.
    Los planos tienen fondo blanco y texto negro — ideal para Tesseract.
    """
    from PIL import ImageFilter, ImageEnhance

    # Preprocesamiento para mejorar OCR en planos
    # 1. Convertir a escala de grises
    img_gray = img.convert('L')

    # 2. Aumentar contraste (los planos tienen texto fino)
    enhancer = ImageEnhance.Contrast(img_gray)
    img_contrast = enhancer.enhance(2.0)

    # 3. Aplicar threshold para binarizar
    img_bin = img_contrast.point(lambda x: 0 if x < 180 else 255)

    # Config Tesseract para planos:
    # --psm 6 = bloque de texto uniforme
    # -l spa+eng = espanol + ingles (planos colombianos mezclan)
    config = '--psm 6 -l spa+eng --oem 3'

    try:
        texto = pytesseract.image_to_string(img_bin, config=config)
        return texto
    except Exception as e:
        logger.warning(f"OCR pagina completa fallo: {e}")
        # Intentar con imagen original
        try:
            return pytesseract.image_to_string(img_gray, config='--psm 6 -l eng')
        except Exception:
            return ""


def _extraer_cotas(texto: str, escala: int) -> List[CotaOCR]:
    """
    Extrae valores de cotas del texto OCR.
    Maneja los formatos tipicos en planos colombianos.
    """
    cotas = []
    lineas = texto.split('\n')

    # Patrones de cotas en planos colombianos
    patrones = [
        # Metros explicitos: 5.80m, 18.50m, 5,80m
        (r'(\d+[.,]\d{2})\s*m\b', 'longitud', 1.0),
        # Metros sin unidad en contexto de vano: "5.80" entre ejes
        (r'\b(\d+[.,]\d{2})\b', 'longitud', 1.0),
        # Centimetros: 30cm, 55cm, 300cm
        (r'(\d{2,4})\s*cm\b', 'seccion', 0.01),
        # Solo numero entero (secciones en cm): "30", "25", "55"
        (r'\b([2-9]\d|[12]\d{2})\b', 'seccion', 0.01),
        # Metros con unidad completa: 1.60m, 7.80m
        (r'(\d+[.,]\d+)\s*m\b', 'longitud', 1.0),
        # Milimetros: 250mm, 300mm
        (r'(\d{3,4})\s*mm\b', 'seccion', 0.001),
    ]

    vistas = set()  # Evitar duplicados

    for linea in lineas:
        linea_clean = linea.strip()
        if len(linea_clean) < 2:
            continue

        for patron, tipo, factor in patrones:
            for m in re.finditer(patron, linea_clean, re.IGNORECASE):
                try:
                    val_str = m.group(1).replace(',', '.')
                    val = float(val_str) * factor

                    # Filtrar valores fuera de rango estructural
                    if tipo == 'longitud' and not (0.10 <= val <= 100):
                        continue
                    if tipo == 'seccion' and not (0.05 <= val <= 2.0):
                        continue

                    # Redondear para deduplicacion
                    val_r = round(val, 3)
                    key = f"{val_r}_{tipo}"
                    if key in vistas:
                        continue
                    vistas.add(key)

                    # Determinar tipo mas especifico por contexto
                    tipo_final = _clasificar_cota(val, linea_clean, tipo)

                    cotas.append(CotaOCR(
                        valor_texto=m.group(0).strip(),
                        valor_m=val_r,
                        confianza=0.85 if factor == 1.0 else 0.70,
                        tipo=tipo_final,
                        contexto=linea_clean[:80]
                    ))
                except ValueError:
                    continue

    # Ordenar por confianza
    cotas.sort(key=lambda c: c.confianza, reverse=True)
    return cotas[:50]  # Max 50 cotas por pagina


def _clasificar_cota(valor_m: float, contexto: str, tipo_base: str) -> str:
    """Clasifica la cota segun su valor y contexto."""
    ctx = contexto.upper()

    # Alturas de piso: 2.5-5.0m
    if 2.0 <= valor_m <= 6.0:
        if any(k in ctx for k in ['PISO', 'ALTURA', 'H=', 'ALT', 'LIBRE']):
            return 'altura'

    # Longitudes de vano: 2.0-15.0m
    if 2.0 <= valor_m <= 20.0:
        if any(k in ctx for k in ['VANO', 'LUZ', 'L=', 'EJE']):
            return 'longitud'

    # Secciones: 0.20-1.0m
    if 0.15 <= valor_m <= 1.50:
        if any(k in ctx for k in ['COL', 'VIGA', 'SECC', 'SEC', 'X', 'CM']):
            return 'seccion'

    return tipo_base


def _extraer_especificaciones(texto: str) -> Dict:
    """
    Extrae especificaciones tecnicas del texto OCR:
    f'c, fy, recubrimientos, zona sismica, etc.
    """
    specs = {}
    texto_upper = texto.upper()

    # f'c del concreto
    for patron in [
        r"F'?C\s*=?\s*(\d+[.,]?\d*)\s*(MPA|KG|PSI)",
        r"(\d+[.,]?\d*)\s*MPA",
        r"(\d{4,5})\s*PSI",
        r"(\d+[.,]?\d*)\s*KG/?CM",
    ]:
        m = re.search(patron, texto_upper)
        if m:
            try:
                val = float(m.group(1).replace(',', '.'))
                unit = m.group(2) if m.lastindex >= 2 else 'MPA'
                if 'KG' in unit: val = val / 10.2
                if 'PSI' in unit: val = val / 145.0
                if 10 <= val <= 60:
                    specs['fc_mpa'] = round(val, 1)
                    break
            except Exception:
                pass

    # fy del acero
    for patron in [
        r"FY\s*=?\s*(\d+[.,]?\d*)\s*(MPA|KSI)",
        r"ACERO\s+G(\d+)",
        r"(\d{3})\s*MPA",
    ]:
        m = re.search(patron, texto_upper)
        if m:
            try:
                val = float(m.group(1).replace(',', '.'))
                if 'KSI' in (m.group(2) if m.lastindex >= 2 else ''):
                    val *= 6.895
                if 'G' in patron:
                    val = {'60': 420, '40': 276}.get(m.group(1), 420)
                if 200 <= val <= 600:
                    specs['fy_mpa'] = round(val, 0)
                    break
            except Exception:
                pass

    # Zona sismica
    if 'ZONA ALTA' in texto_upper or 'AA=' in texto_upper:
        specs['zona_sismica'] = 'alta'
    elif 'ZONA INTERMEDIA' in texto_upper or 'MODERADA' in texto_upper:
        specs['zona_sismica'] = 'intermedia'
    elif 'ZONA BAJA' in texto_upper:
        specs['zona_sismica'] = 'baja'

    # Recubrimiento
    for patron in [r'RECUBRIMIENTO\s*[:=]?\s*(\d+)\s*(CM|MM)', r'REC\s*[:=]\s*(\d+)']:
        m = re.search(patron, texto_upper)
        if m:
            try:
                val = float(m.group(1))
                unit = m.group(2) if m.lastindex >= 2 else 'CM'
                if 'MM' in unit: val /= 10
                if 1 <= val <= 10:
                    specs['recubrimiento_cm'] = val
                    break
            except Exception:
                pass

    # Norma
    if 'NSR-10' in texto_upper or 'NSR10' in texto_upper:
        specs['norma'] = 'NSR-10'
    if 'AISC' in texto_upper:
        specs['norma_metalica'] = 'AISC'

    return specs


def _detectar_cuadros(texto: str) -> List[Dict]:
    """
    Detecta cuadros de columnas, vigas y zapatas en el texto OCR.
    Busca patrones tabulares tipicos de planos colombianos.
    """
    cuadros = []
    lineas = texto.split('\n')

    # Patron de cuadro de columnas: referencia + seccion + acero
    patron_col = re.compile(
        r'(C[-_]?\d+|CL[-_]?\d+)\s+'   # referencia C1, CL-3
        r'(\d{2,3})[xX×](\d{2,3})\s+'  # seccion 30x30
        r'.*?(\d+)\s*[#NOo]?\s*(\d+)',  # acero 4#5, 6N4
        re.IGNORECASE
    )

    # Patron de cuadro de vigas: VP-1 25x40
    patron_viga = re.compile(
        r'(V[PS]?[-_]?\d+|VP\d+)\s+'
        r'(\d{2,3})[xX×](\d{2,3})',
        re.IGNORECASE
    )

    # Patron de cuadro de zapatas: Z-1 1.60x1.60x0.30
    patron_zap = re.compile(
        r'(Z[-_]?\d+)\s+'
        r'(\d+[.,]\d+)[xX×](\d+[.,]\d+)',
        re.IGNORECASE
    )

    # Buscar en el texto completo
    for m in patron_col.finditer(texto):
        cuadros.append({
            'tipo': 'columna',
            'referencia': m.group(1).upper(),
            'ancho_cm': int(m.group(2)),
            'alto_cm': int(m.group(3)),
            'texto': m.group(0)[:60],
        })

    for m in patron_viga.finditer(texto):
        cuadros.append({
            'tipo': 'viga',
            'referencia': m.group(1).upper(),
            'ancho_cm': int(m.group(2)),
            'alto_cm': int(m.group(3)),
            'texto': m.group(0)[:60],
        })

    for m in patron_zap.finditer(texto):
        cuadros.append({
            'tipo': 'zapata',
            'referencia': m.group(1).upper(),
            'largo_m': float(m.group(2).replace(',', '.')),
            'ancho_m': float(m.group(3).replace(',', '.')),
            'texto': m.group(0)[:60],
        })

    return cuadros


def _generar_contexto(resultado: 'ResultadoOCR') -> str:
    """
    Genera el bloque de contexto para incluir en el prompt de Claude.
    Este texto va antes del prompt de extraccion para enriquecer el analisis.
    """
    if not resultado.tesseract_usado:
        return ""

    lineas = ["=== OCR TESSERACT — TEXTO EXTRAIDO DEL PLANO ===\n"]

    # Especificaciones detectadas
    if resultado.especificaciones:
        lineas.append("ESPECIFICACIONES DETECTADAS POR OCR:")
        for k, v in resultado.especificaciones.items():
            lineas.append(f"  {k}: {v}")
        lineas.append("")

    # Cuadros detectados (lo mas valioso)
    if resultado.cuadros_detectados:
        lineas.append(f"CUADROS DE REFERENCIAS DETECTADOS ({len(resultado.cuadros_detectados)}):")
        for c in resultado.cuadros_detectados[:15]:
            if c['tipo'] == 'columna':
                lineas.append(
                    f"  {c['referencia']}: {c['ancho_cm']}x{c['alto_cm']}cm"
                )
            elif c['tipo'] == 'viga':
                lineas.append(
                    f"  {c['referencia']}: {c['ancho_cm']}x{c['alto_cm']}cm"
                )
            elif c['tipo'] == 'zapata':
                lineas.append(
                    f"  {c['referencia']}: {c['largo_m']}x{c['ancho_m']}m"
                )
        lineas.append("")

    # Cotas clave (longitudes y alturas)
    cotas_long = [c for c in resultado.cotas if c.tipo in ('longitud', 'altura') and c.valor_m >= 1.0]
    if cotas_long:
        vals = sorted(set(c.valor_m for c in cotas_long[:20]))
        lineas.append(f"COTAS/DIMENSIONES DETECTADAS (m):")
        lineas.append(f"  {[f'{v:.2f}m' for v in vals[:15]]}")
        lineas.append("")

    # Secciones detectadas
    cotas_sec = [c for c in resultado.cotas if c.tipo == 'seccion']
    if cotas_sec:
        vals_sec = sorted(set(round(c.valor_m * 100) for c in cotas_sec[:20]))
        lineas.append(f"SECCIONES DETECTADAS (cm):")
        lineas.append(f"  {[f'{v}cm' for v in vals_sec[:15]]}")
        lineas.append("")

    # Texto raw relevante (primeros 800 chars filtrado)
    texto_relevante = _filtrar_texto_relevante(resultado.texto_completo)
    if texto_relevante:
        lineas.append("TEXTO RELEVANTE DEL PLANO (OCR):")
        lineas.append(texto_relevante[:800])
        lineas.append("")

    lineas.append("=== FIN OCR ===\n")
    lineas.append("USA ESTOS DATOS COMO BASE. Si hay contradiccion con la imagen, prioriza el OCR.")

    return '\n'.join(lineas)


def _filtrar_texto_relevante(texto: str) -> str:
    """
    Filtra el texto OCR para quedarse solo con lo estructuralmente relevante.
    Elimina texto de membrete, sello, y partes irrelevantes.
    """
    lineas_relevantes = []
    palabras_clave = [
        'columna', 'viga', 'zapata', 'losa', 'placa', 'cercha', 'correa',
        'f\'c', 'fc', 'fy', 'acero', 'concreto', 'mpa', 'psi', 'kg',
        'nsr', 'zona', 'escala', 'esc:', 'nivel', 'n+',
        'pte', 'phr', 'angulo', 'perfil', 'astm', 'a500',
        'caisson', 'pilote', 'muro', 'contencion',
    ]

    for linea in texto.split('\n'):
        linea_l = linea.lower().strip()
        if len(linea_l) < 3:
            continue
        if any(kw in linea_l for kw in palabras_clave):
            lineas_relevantes.append(linea.strip())

    return '\n'.join(lineas_relevantes[:40])


def esta_disponible() -> bool:
    """Retorna True si Tesseract esta instalado y funcionando."""
    return TESSERACT_OK
