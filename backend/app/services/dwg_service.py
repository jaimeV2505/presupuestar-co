"""
Servicio de lectura de archivos DWG/DXF — PresupuestarCO v4.

Estrategia dual:
  1. ezdxf → parsea texto, dimensiones, bloques y capas directamente (datos estructurados)
  2. ezdxf matplotlib renderer → renderiza a imagen PNG para Claude Vision

Esto da lo mejor de los dos mundos:
  - Datos estructurados: cotas exactas, textos de notas, referencias de elementos
  - Imagen: Claude Vision entiende la disposición espacial del plano
"""
import logging
import io
import re
import tempfile
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ElementoDWG:
    """Elemento extraído del DWG."""
    tipo: str           # TEXT, DIMENSION, MTEXT, INSERT (bloque), LINE, etc.
    contenido: str      # Texto o descripción
    capa: str           # Layer del AutoCAD
    coordenadas: Tuple  # (x, y) o (x1,y1,x2,y2)
    valor_numerico: Optional[float] = None  # Para dimensiones


@dataclass
class ExtraccionDWG:
    """Resultado completo de la extracción de un DWG."""
    textos: List[str] = field(default_factory=list)
    dimensiones: List[Dict] = field(default_factory=list)
    bloques: List[str] = field(default_factory=list)
    capas: List[str] = field(default_factory=list)
    notas_generales: List[str] = field(default_factory=list)
    cuadro_columnas: List[Dict] = field(default_factory=list)
    cuadro_vigas: List[Dict] = field(default_factory=list)
    especificaciones: Dict = field(default_factory=dict)
    resumen_texto: str = ""
    imagen_png: Optional[bytes] = None
    error: Optional[str] = None


def leer_dwg(file_bytes: bytes, filename: str = "") -> ExtraccionDWG:
    """
    Lee un archivo DWG o DXF y extrae toda la información relevante.
    
    Args:
        file_bytes: Bytes del archivo DWG/DXF
        filename: Nombre original del archivo
    
    Returns:
        ExtraccionDWG con textos, dimensiones, imagen y resumen
    """
    try:
        import ezdxf
        from ezdxf.enums import TextEntityAlignment
    except ImportError:
        return ExtraccionDWG(
            error="ezdxf no está instalado. Ejecuta: pip install ezdxf"
        )

    resultado = ExtraccionDWG()

    # Guardar en archivo temporal (ezdxf necesita archivo en disco para DWG)
    suffix = ".dwg" if filename.lower().endswith(".dwg") else ".dxf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        # ── Leer el archivo ───────────────────────────────────────────────────
        try:
            doc = ezdxf.readfile(tmp_path)
        except ezdxf.DXFStructureError as e:
            # Intentar recuperación
            try:
                doc, auditor = ezdxf.recover.readfile(tmp_path)
                if auditor.has_errors:
                    logger.warning(f"DWG recuperado con {len(auditor.errors)} errores")
            except Exception:
                resultado.error = f"No se pudo leer el archivo: {e}"
                return resultado

        msp = doc.modelspace()

        # ── Extraer capas (layers) ────────────────────────────────────────────
        resultado.capas = [layer.dxf.name for layer in doc.layers
                          if not layer.dxf.name.startswith("0")]
        logger.info(f"DWG capas: {resultado.capas[:10]}")

        # ── Extraer textos ────────────────────────────────────────────────────
        todos_textos = []
        for entity in msp:
            texto = None
            capa = entity.dxf.layer if hasattr(entity.dxf, 'layer') else ""

            if entity.dxftype() == "TEXT":
                texto = entity.dxf.text.strip()
            elif entity.dxftype() == "MTEXT":
                texto = _limpiar_mtext(entity.plain_mtext())
            elif entity.dxftype() == "ATTRIB":
                texto = entity.dxf.text.strip()

            if texto and len(texto) > 1:
                todos_textos.append(texto)
                resultado.textos.append(texto)

        # ── Extraer de bloques (INSERT) ───────────────────────────────────────
        for entity in msp.query("INSERT"):
            bloque_nombre = entity.dxf.name
            resultado.bloques.append(bloque_nombre)
            # Extraer atributos del bloque
            if entity.has_attribs:
                for attrib in entity.attribs:
                    txt = attrib.dxf.text.strip()
                    if txt and len(txt) > 1:
                        todos_textos.append(txt)
                        resultado.textos.append(txt)

        # ── Extraer dimensiones ───────────────────────────────────────────────
        for entity in msp.query("DIMENSION"):
            try:
                dim_val = entity.dxf.actual_measurement
                if dim_val and dim_val > 0:
                    resultado.dimensiones.append({
                        "valor": round(dim_val, 4),
                        "valor_m": round(dim_val / 1000, 4) if dim_val > 100 else round(dim_val, 4),
                        "tipo": entity.dimtype,
                        "capa": entity.dxf.layer,
                    })
            except Exception:
                pass

        logger.info(f"DWG: {len(resultado.textos)} textos, {len(resultado.dimensiones)} dimensiones")

        # ── Analizar textos para extraer información estructural ──────────────
        resultado.cuadro_columnas = _detectar_cuadro_columnas(todos_textos)
        resultado.cuadro_vigas    = _detectar_cuadro_vigas(todos_textos)
        resultado.notas_generales = _detectar_notas(todos_textos)
        resultado.especificaciones = _detectar_especificaciones(todos_textos)

        # ── Generar resumen de texto para Claude ──────────────────────────────
        resultado.resumen_texto = _generar_resumen(resultado)

        # ── Renderizar a imagen PNG ───────────────────────────────────────────
        resultado.imagen_png = _renderizar_a_png(doc, msp)

    except Exception as e:
        logger.error(f"Error leyendo DWG: {e}", exc_info=True)
        resultado.error = str(e)
    finally:
        os.unlink(tmp_path)

    return resultado


def _limpiar_mtext(texto: str) -> str:
    """Limpia códigos de formato MTEXT de AutoCAD."""
    # Remover códigos de formato: \P, \L, \l, \H, \W, etc.
    texto = re.sub(r'\\[A-Za-z][\d.]*;?', '', texto)
    texto = re.sub(r'\{\\[^}]*\}', '', texto)
    texto = texto.replace("\\P", "\n").replace("\\~", " ")
    return texto.strip()


def _detectar_cuadro_columnas(textos: List[str]) -> List[Dict]:
    """
    Detecta el cuadro de columnas en los textos del DWG.
    Busca patrones como: C1, 30x30, 4Ø5/8", #3@15cm
    """
    columnas = []
    # Buscar referencias de columna: C1, C2, C-1, COL-1, etc.
    patron_ref = re.compile(r'C[-_]?(\d+)', re.IGNORECASE)
    patron_sec = re.compile(r'(\d+(?:\.\d+)?)[xX×](\d+(?:\.\d+)?)\s*(?:cm|m)?')
    patron_acero = re.compile(r'(\d+)\s*[Øø#N]\s*([\d/]+)"?')

    for i, texto in enumerate(textos):
        m_ref = patron_ref.search(texto)
        if m_ref:
            columna = {"referencia": f"C{m_ref.group(1)}", "texto_original": texto}
            # Buscar sección en textos cercanos
            for j in range(max(0,i-3), min(len(textos), i+4)):
                m_sec = patron_sec.search(textos[j])
                if m_sec:
                    columna["ancho_cm"] = float(m_sec.group(1))
                    columna["alto_cm"] = float(m_sec.group(2))
                m_ace = patron_acero.search(textos[j])
                if m_ace:
                    columna["acero"] = f"{m_ace.group(1)}Ø{m_ace.group(2)}\""
            if "ancho_cm" in columna:
                columnas.append(columna)

    # Eliminar duplicados por referencia
    vistas = set()
    unicas = []
    for c in columnas:
        if c["referencia"] not in vistas:
            vistas.add(c["referencia"])
            unicas.append(c)
    return unicas


def _detectar_cuadro_vigas(textos: List[str]) -> List[Dict]:
    """Detecta el cuadro de vigas."""
    vigas = []
    patron_ref = re.compile(r'V[PSA]?[-_]?(\d+)', re.IGNORECASE)
    patron_sec = re.compile(r'(\d+(?:\.\d+)?)[xX×](\d+(?:\.\d+)?)\s*(?:cm|m)?')

    for i, texto in enumerate(textos):
        m_ref = patron_ref.search(texto)
        if m_ref:
            viga = {"referencia": m_ref.group(0).upper(), "texto_original": texto}
            for j in range(max(0,i-2), min(len(textos), i+3)):
                m_sec = patron_sec.search(textos[j])
                if m_sec:
                    viga["ancho_cm"] = float(m_sec.group(1))
                    viga["alto_cm"] = float(m_sec.group(2))
            if "ancho_cm" in viga:
                vigas.append(viga)

    vistas = set()
    unicas = []
    for v in vigas:
        if v["referencia"] not in vistas:
            vistas.add(v["referencia"])
            unicas.append(v)
    return unicas


def _detectar_notas(textos: List[str]) -> List[str]:
    """Detecta las notas generales del plano."""
    notas = []
    indicadores = ["nota", "especific", "material", "concreto", "acero",
                   "f'c", "fy=", "nsr", "zona", "recubr"]
    for texto in textos:
        if len(texto) > 20:  # Textos largos son probablemente notas
            txt_lower = texto.lower()
            if any(ind in txt_lower for ind in indicadores):
                notas.append(texto[:200])  # Máx 200 chars por nota
    return notas[:20]  # Máx 20 notas


def _detectar_especificaciones(textos: List[str]) -> Dict:
    """Extrae especificaciones técnicas de los textos."""
    specs = {}
    texto_completo = " ".join(textos).upper()

    # f'c del concreto
    m_fc = re.search(r"F['']?C\s*=?\s*([\d.]+)\s*(MPA|KG|PSI|KSI)?", texto_completo)
    if m_fc:
        val = float(m_fc.group(1))
        unit = m_fc.group(2) or "MPA"
        if "KG" in unit:  val = val / 10.2  # kg/cm² → MPa aprox
        if "PSI" in unit: val = val / 145.0
        specs["fc_mpa"] = round(val, 1)

    # fy del acero
    m_fy = re.search(r"FY\s*=?\s*([\d.]+)\s*(MPA|KSI|KG)?", texto_completo)
    if m_fy:
        val = float(m_fy.group(1))
        unit = m_fy.group(2) or "MPA"
        if "KSI" in unit: val = val * 6.895
        specs["fy_mpa"] = round(val, 0)

    # Zona sísmica
    if "ZONA ALTA" in texto_completo or "AA=" in texto_completo:
        specs["zona_sismica"] = "alta"
    elif "ZONA INTERMEDIA" in texto_completo or "MODERADA" in texto_completo:
        specs["zona_sismica"] = "media"
    elif "ZONA BAJA" in texto_completo:
        specs["zona_sismica"] = "baja"

    # NSR-10
    if "NSR-10" in texto_completo or "NSR10" in texto_completo:
        specs["norma"] = "NSR-10"

    return specs


def _generar_resumen(ext: ExtraccionDWG) -> str:
    """Genera un resumen de texto estructurado para pasar a Claude."""
    lines = ["=== INFORMACIÓN EXTRAÍDA DEL ARCHIVO DWG/DXF ===\n"]

    if ext.capas:
        lines.append(f"CAPAS DEL DIBUJO: {', '.join(ext.capas[:15])}")

    if ext.especificaciones:
        lines.append("\nESPECIFICACIONES DETECTADAS:")
        for k, v in ext.especificaciones.items():
            lines.append(f"  {k}: {v}")

    if ext.cuadro_columnas:
        lines.append(f"\nCUADRO DE COLUMNAS ({len(ext.cuadro_columnas)} tipos):")
        for c in ext.cuadro_columnas:
            dim = f"{c.get('ancho_cm','')}x{c.get('alto_cm','')}cm" if "ancho_cm" in c else ""
            acero = c.get("acero", "")
            lines.append(f"  {c['referencia']}: {dim} {acero}".strip())

    if ext.cuadro_vigas:
        lines.append(f"\nCUADRO DE VIGAS ({len(ext.cuadro_vigas)} tipos):")
        for v in ext.cuadro_vigas:
            dim = f"{v.get('ancho_cm','')}x{v.get('alto_cm','')}cm" if "ancho_cm" in v else ""
            lines.append(f"  {v['referencia']}: {dim}".strip())

    if ext.notas_generales:
        lines.append(f"\nNOTAS GENERALES ({len(ext.notas_generales)}):")
        for n in ext.notas_generales[:5]:
            lines.append(f"  - {n[:100]}")

    if ext.dimensiones:
        vals = sorted([d["valor_m"] for d in ext.dimensiones if d["valor_m"] > 0])
        if vals:
            lines.append(f"\nDIMENSIONES DETECTADAS: {len(vals)} cotas")
            lines.append(f"  Rango: {min(vals):.3f}m — {max(vals):.3f}m")
            # Dimensiones más comunes
            from collections import Counter
            comunes = Counter(round(v, 2) for v in vals).most_common(5)
            lines.append(f"  Más frecuentes: {[f'{v}m (x{n})' for v,n in comunes]}")

    lines.append(f"\nTOTAL TEXTOS EXTRAÍDOS: {len(ext.textos)}")
    lines.append("=== FIN INFORMACIÓN DWG ===")

    return "\n".join(lines)


def _renderizar_a_png(doc, msp, max_px: int = 3000) -> Optional[bytes]:
    """
    Renderiza el modelspace del DWG a PNG usando ezdxf + matplotlib.
    Retorna None si matplotlib no está disponible.
    """
    try:
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        import matplotlib
        matplotlib.use('Agg')  # Backend sin GUI
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(20, 14), dpi=150)
        ax = fig.add_axes([0, 0, 1, 1])
        ctx = RenderContext(doc)
        backend = MatplotlibBackend(ax)
        frontend = Frontend(ctx, backend)
        frontend.draw_layout(msp, finalize=True)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight',
                   facecolor='white', dpi=150)
        plt.close(fig)
        buf.seek(0)
        img_bytes = buf.read()
        logger.info(f"DWG renderizado: {len(img_bytes)//1024}KB PNG")
        return img_bytes

    except ImportError:
        logger.warning("matplotlib no disponible — solo extracción de texto")
        return None
    except Exception as e:
        logger.warning(f"No se pudo renderizar DWG: {e}")
        return None


def dwg_to_contexto_claude(ext: ExtraccionDWG) -> str:
    """
    Convierte la extracción DWG en contexto enriquecido para Claude.
    Este texto se agrega al prompt de extracción.
    """
    if ext.error:
        return f"Nota: El archivo DWG tuvo un error de lectura: {ext.error}"

    ctx_parts = ["DATOS EXTRAÍDOS DIRECTAMENTE DEL ARCHIVO DWG (sin imagen):"]
    ctx_parts.append(ext.resumen_texto)

    if ext.cuadro_columnas:
        ctx_parts.append("\nUSA ESTOS DATOS DE COLUMNAS (son más precisos que la imagen):")
        for c in ext.cuadro_columnas:
            ctx_parts.append(f"  {c['referencia']}: {c.get('ancho_cm','')}x{c.get('alto_cm','')}cm {c.get('acero','')}")

    if ext.especificaciones:
        ctx_parts.append(f"\nEspecificaciones confirmadas del DWG: {ext.especificaciones}")

    return "\n".join(ctx_parts)
