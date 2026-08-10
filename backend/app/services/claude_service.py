# -*- coding: utf-8 -*-
"""
Extraccion de planos con Claude Vision -- v6.
NUEVO: Extraccion pagina por pagina + consolidacion + coherencia.
Cada pagina se analiza individualmente para mayor precision en longitudes.
"""
import anthropic, base64, json, logging, re, fitz
from typing import List, Dict, Tuple, Optional
from app.services.feedback_service import get_few_shot_prompt, registrar_analisis
from app.services.dwg_service import leer_dwg, dwg_to_contexto_claude
from app.services.scale_service import detectar_escala
from app.services.tesseract_ocr import procesar_imagen_plano, esta_disponible as tesseract_ok

logger = logging.getLogger(__name__)
MAX_PX = 4000

SYSTEM_EXPERTO = """Eres ingeniero civil estructural senior, 25 anos cuantificando obras en Colombia.
Experto en: NSR-10, AISC, ASTM, planos estructurales de cualquier oficina de calculo,
perfiles metalicos, concreto reforzado, cimentaciones especiales, muros de contencion.

=== PRINCIPIOS UNIVERSALES DE CUANTIFICACION (aplican a CUALQUIER plano) ===

P1. LEE PRIMERO LA NOMENCLATURA DEL PLANO. Casi todo plano tiene un bloque
    de convenciones/nomenclatura/leyenda que define SU forma de nombrar
    vigas, columnas, refuerzos, soldaduras, anclajes. Ese bloque es tu
    diccionario: usalo para interpretar TODAS las etiquetas del plano.
    Cada oficina usa convenciones distintas — nunca asumas, lee la del plano.

P2. CUENTA POR ETIQUETAS REPETIDAS. Sea cual sea la convencion (ANC1, A-1,
    TIPO 1, PB-2...), cada aparicion de una etiqueta de referencia marca UN
    elemento fisico. Contar repeticiones de etiquetas es mas confiable que
    contar dibujos. Aplica a: anclajes, conexiones, zapatas, columnas, nudos.

P3. DETECTA LA UNIDAD DE COTAS. Planos de Revit/CAD colombianos suelen cotizar
    en mm (7000 = 7.0m); planos antiguos a mano en m (7.00) o cm (700).
    Regla: si las cotas de luces son numeros de 4-5 digitos, son mm.
    Declara en observaciones que unidad detectaste y aplicala consistentemente.

P4. SUMA CADENAS DE COTAS. La longitud de un eje/viga/correa es la suma de
    sus cotas parciales. Sumalas — no adivines si puedes sumar.

P5. CADA VISTA TIENE SU DATO: plantas dan cantidades y longitudes horizontales;
    cortes/secciones dan alturas; detalles dan especificaciones (platinas,
    pernos, soldaduras, refuerzos); cuadros dan dimensiones y despieces;
    vistas 3D y arquitectonicas NO se cuantifican.

P6. ELEMENTOS SECUNDARIOS SIEMPRE: ademas de la estructura principal, extrae
    si existen: platinas y pernos de anclaje, conexiones (soldadas o pernadas)
    por tipo, canoas/bajantes, tensores/riostras, angulos de fijacion,
    mallas, juntas. Son 10-20% del costo y todos los olvidan.

P7. VALIDACION CRUZADA: los conteos deben cuadrar entre si
    (columnas==anclajes==platinas; pernos==platinas x pernos_por_platina;
    todo perfil de la lista de materiales debe estar cuantificado).
    Reporta discrepancias en observaciones — no las ocultes.

REGLAS DE SALIDA:
1. Responde SOLO con JSON valido y COMPLETO. Sin markdown.
2. Metalica: nombre EXACTO del perfil + unidad "m" (long total = piezas x largo).
   EXCEPCION: columnas metalicas pueden ir en "un" si das altura_libre_m.
3. Platinas/pernos/conexiones: unidad "un" con la cuenta exacta.
4. Concreto: dimensiones exactas en cm del cuadro del plano.
5. Zapatas: cada TIPO por separado segun la convencion del plano.
6. El carcamo es canal de desague, NO viga. Pedestales son columnas cortas."""

P_RECONOCIMIENTO = """RECONOCIMIENTO RAPIDO. Busca el bloque de NOMENCLATURA/CONVENCIONES del plano
(todo plano define su propia forma de nombrar elementos — capturala). JSON:
{"tipo_plano":"planta_estructural|cimentacion|corte|detalle|cubierta_metalica|muro_contencion|arquitectonico|vista_3d",
"escala":"1:50|1:75|1:100|1:200|sin_escala",
"unidad_cotas":"mm|cm|m",
"sistema_estructural":"porticos_concreto|estructura_metalica|mixto|muros_contencion",
"tiene_cuadro_columnas":false,"tiene_perfiles_metalicos":false,"tiene_caissones":false,
"tiene_muros_contencion":false,"tiene_cuadro_zapatas":false,
"nomenclatura_detectada":"resumen de las convenciones del plano: como nombra columnas, vigas, anclajes, conexiones, refuerzos (ej: ANC#=anclaje, VC-#=viga de carga, o lo que use ESTE plano)",
"elementos_visibles":["lista de lo que ves en ESTA pagina"],
"legibilidad":"excelente|buena|regular|mala","observacion":""}"""

P_EXTRACCION_PAGINA = """{few_shot}

EXTRACCION DE ESTA PAGINA. Escala: {escala}. Tipo: {tipo_plano}.
Contexto global: {ctx}

=== REGLA DE ORO: CANTIDAD NUNCA VACIA ===
Eres un ingeniero cuantificando para presupuesto. Un elemento sin cantidad
NO SIRVE. Aplica esta metodologia EN ORDEN para cada elemento:

1. TOTAL EXPLICITO: si el plano dice el total (ej: "12 columnas", tabla con
   cantidades), usalo. confianza_extraccion=0.95

2. CONTAR EN PLANTA: si es planta, CUENTA los elementos visibles uno por uno.
   Cuenta las marcas de columna, los ejes, las intersecciones. confianza=0.85

3. CALCULAR DE LA GEOMETRIA: usa las cotas del plano:
   - Correas @separacion: ancho_cubierta / separacion + 1 = numero de correas
     numero x longitud_crujia = metros totales
   - Vigas por eje: numero de ejes x longitud entre apoyos = metros
   - Columnas: intersecciones de ejes (ejes A-D x ejes 1-5 = hasta 20 columnas)
   confianza=0.70, dato_estimado=true

4. ESTIMAR DE LA ESCALA: mide sobre el plano usando la escala declarada.
   confianza=0.60, dato_estimado=true

5. SOLO SI TODO FALLA: cantidad=0 y en "notas" escribe EXACTAMENTE que
   informacion falta (ej: "plano no muestra longitud de crujia").

PARA METALICA (cerchas, correas, vigas, columnas tubo):
- unidad SIEMPRE "m" (metros lineales) — el presupuesto convierte a kg
- cantidad = numero_de_piezas x longitud_de_cada_pieza
- Ej: 24 correas de 6.1m -> cantidad=146.4, unidad="m"
- El nombre DEBE incluir el perfil exacto: "Correa PHR 220x80x2.0mm"
- Anclajes/pernos/platinas: unidad "un", cuenta los visibles en el detalle

PARA CONCRETO:
- Columnas/zapatas: unidad "un" + dimensiones en cm + altura_libre_m
- Vigas: unidad "m" (metros totales) + seccion en cm
- Losas: unidad "m2" con area_m2

DIMENSIONES: extrae SIEMPRE que esten en el plano:
- dimension_largo_m para elementos lineales (CRITICO para calcular kg)
- Si el elemento aparece en varias longitudes, crea UN elemento por longitud

{instruccion_especial}

MAXIMO 15 elementos por pagina. Extrae SOLO lo visible en ESTA pagina.

JSON COMPLETO:
{{"pagina":{num_pag},"tipo_contenido":"cuadro_columnas|planta|detalle|cercha|correas|cimentacion|notas",
"elementos":[{{"tipo":"columnas|vigas|losa|cimentacion|muros|cubierta|viga_amarre|caisson|muro_contencion|otros",
"referencia":"","nombre":"nombre EXACTO con perfil/dimensiones","cantidad":0,"unidad":"m|m2|m3|un|kg",
"dimension_ancho_cm":null,"dimension_alto_cm":null,"dimension_largo_m":null,"altura_libre_m":null,
"espesor_cm":null,"area_m2":null,"dimension_diametro_cm":null,
"acero_longitudinal":"","acero_transversal":"","material":"","ubicacion":"",
"notas":"como calculaste la cantidad (ej: 24 correas x 6.1m contadas en planta)",
"confianza_extraccion":0.9,"dato_estimado":false}}],
"especificaciones_pagina":{{"fc_mpa":null,"fy_mpa":null,"escala":"","zona_sismica":"","notas_generales":[]}},
"observaciones":""}}"""

P_CONSOLIDACION = """CONSOLIDA estos elementos de {n_paginas} paginas del mismo plano
COMO UN INGENIERO SENIOR REVISANDO EL TRABAJO DE SU CUANTIFICADOR.

Paginas extraidas:
{resumen_paginas}

REGLAS DE CONSOLIDACION:
- Si el mismo perfil aparece en multiples paginas, SUMA sus longitudes
- Si una pagina da dimensiones y otra da cantidad, COMBINA en un elemento
- La pagina de detalles (platinas, pernos, conexiones) da las ESPECIFICACIONES;
  la planta da las CANTIDADES. Cruzalas.
- Vistas 3D y paginas arquitectonicas NO aportan cantidades — ignora sus conteos
- Usa las especificaciones mas detalladas (fc_mpa, fy_mpa, escala)
- Maximo 25 elementos finales

VALIDACION CRUZADA OBLIGATORIA (reporta en observaciones):
1. numero_columnas == numero_anclajes? Si ANC1+ANC2 = 12 pero contaste 10
   columnas, corrige al valor de los anclajes (son mas confiables).
2. numero_platinas == numero_columnas (1 platina por columna tipicamente)
3. pernos_totales == platinas x pernos_por_platina (del detalle)
4. Cada perfil de la leyenda/lista de materiales aparece en los elementos?
   Si un perfil esta en la leyenda pero no lo cuantificaste, agregalo con
   cantidad=0 y nota "en leyenda, no localizado en planta — verificar".
5. Todo elemento con dato_estimado=true conserva la nota de COMO se estimo.
6. CRITICO: usa EXACTAMENTE los nombres de campo del JSON de ejemplo.
   El campo "nombre" es OBLIGATORIO en cada elemento — nunca lo omitas ni
   uses campos alternativos como "descripcion", "id" o "elemento".

JSON COMPLETO:
{{"descripcion_proyecto":"","tipo_plano":"","escala":"","norma":"NSR-10",
"sistema_estructural":"","especificaciones":{{"fc_concreto_mpa":20.7,"fy_acero_mpa":420,
"zona_sismica":"alta","grupo_uso":"II","tipo_suelo":"S2","acero_perfiles":"A500|A36|A572"}},
"elementos":[{{"tipo":"columnas|vigas|losa|cimentacion|muros|cubierta|viga_amarre|caisson|muro_contencion|otros",
"referencia":"","nombre":"OBLIGATORIO: nombre descriptivo con perfil exacto (ej: Columna PTE 150x150x4)",
"cantidad":0,"unidad":"m|m2|m3|un|kg",
"dimension_ancho_cm":null,"dimension_alto_cm":null,"dimension_largo_m":null,"altura_libre_m":null,
"espesor_cm":null,"area_m2":null,"dimension_diametro_cm":null,
"acero_longitudinal":"","acero_transversal":"","material":"","ubicacion":"",
"notas":"como se calculo la cantidad","confianza_extraccion":0.9,"dato_estimado":false}}],
"notas_generales_plano":[],"observaciones":"resultado de las 5 validaciones cruzadas",
"advertencias":["discrepancias encontradas"],"confianza":"alta|media|baja"}}"""

P_VALIDACION = """VALIDACI??N T??CNICA. Verifica coherencia entre todos los elementos.
Elementos: {elementos}. Specs: {specs}

Para metalica: ??longitudes razonables para el area del plano?
Para concreto: ??cuantias coherentes con zona sismica?
Para zapatas: ??cada tipo cuantificado individualmente?

JSON:
{{"elementos_validados":[...mismos campos...],"correcciones":[],"alertas_tecnicas":[],"confianza_final":"alta|media|baja"}}"""

INSTRUCCIONES_ESPECIALES = {
    "planta_estructural": "Cuenta TODOS los elementos por etiquetas repetidas. Suma cadenas de cotas para longitudes.",
    "cimentacion": "Extrae cada TIPO de zapata por separado (Z-1, Z-2...). Lee dimensiones del cuadro.",
    "cubierta_metalica": (
        "METODO OBLIGATORIO: "
        "(1) Cuenta anclajes ANC1, ANC2 -> numero de columnas por tipo de perfil. "
        "(2) Cada etiqueta PTE con posicion unica = 1 columna. Agrupa por perfil: "
        "'9 un PTE 150x150x4' y '3 un PTE 200x200x5' como elementos SEPARADOS. "
        "(3) Vigas: suma cadenas de cotas por eje (en mm) para metros totales de cada perfil. "
        "(4) Correas: cuenta tramos visibles x longitud de cada tramo. "
        "(5) Extrae platinas (PL AxBxE), pernos (tipo y total), conexiones CON1-CON4 con cantidades, canoas. "
        "(6) Alturas de columna: de las cotas verticales en secciones (mm -> m)."
    ),
    "cercha": "Descomponer en: chord superior, chord inferior, diagonales, montantes. Cada uno con longitud total.",
    "correas": "Contar correas visibles x longitud de crujia. Tambien angulos de fijacion y tensores.",
    "detalle": "Extraer especificaciones exactas: perfil, platina, pernos, soldadura. Cuantificar solo si el detalle dice cuantos (ej: 4 pernos).",
    "muro_contencion": "Identificar tipo (voladizo/contrafuerte), altura y espesor. Calcular m2 de alzado.",
    "arquitectonico": "Solo extraer areas y numero de pisos. No cuantificar estructura aqui.",
    "vista_3d": "NO cuantificar desde vistas 3D. Solo confirmar sistema estructural y reportar tipo_contenido='notas'.",
}


def pdf_to_images_hd(pdf_bytes: bytes, dpi: int = 150) -> List[Tuple[bytes, str, int]]:
    """Convierte PDF a lista de (imagen, media_type, num_pagina)."""
    images = []
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for i in range(len(doc)):
            page = doc[i]
            px_w = page.rect.width * dpi / 72
            px_h = page.rect.height * dpi / 72
            dpi_u = int(dpi * MAX_PX / max(px_w, px_h)) if max(px_w, px_h) > MAX_PX else dpi
            mat = fitz.Matrix(dpi_u/72, dpi_u/72)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB, alpha=False)
            img = pix.tobytes("jpeg", jpg_quality=92)
            images.append((img, "image/jpeg", i+1))
            logger.info(f"Pag {i+1}: {pix.width}??{pix.height}px @ {dpi_u}DPI")
        doc.close()
    except Exception as e:
        logger.error(f"Error PDF???img: {e}"); raise
    return images


def _ib(b: bytes, t: str) -> Dict:
    return {"type":"image","source":{"type":"base64","media_type":t,
            "data":base64.standard_b64encode(b).decode()}}


def _clean(raw: str) -> str:
    s = raw.strip()
    if s.startswith("```"):
        parts = s.split("```"); s = parts[1] if len(parts)>1 else s
        if s.startswith("json"): s = s[4:]
    return s.strip()


def _fix_json(raw: str) -> str:
    s = _clean(raw)
    ob = s.count('{') - s.count('}')
    obrk = s.count('[') - s.count(']')
    if ob > 0 or obrk > 0:
        lc = s.rfind('},')
        if lc == -1: lc = s.rfind('}')
        if lc > 0:
            s = s[:lc+1]
            ob = s.count('{') - s.count('}')
            obrk = s.count('[') - s.count(']')
        s += ']'*obrk + '}'*ob
    return s


def _parse_json(raw: str) -> Optional[Dict]:
    """Intenta parsear JSON con fallback a reparacion."""
    for fn in [_clean, _fix_json]:
        try:
            return json.loads(fn(raw))
        except Exception:
            continue
    return None


async def _reconocer_pagina(client, img_block: Dict) -> Dict:
    """Reconocimiento rapido de una pagina con Haiku."""
    r = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=600,
        system=SYSTEM_EXPERTO,
        messages=[{"role":"user","content":[img_block, {"type":"text","text":P_RECONOCIMIENTO}]}]
    )
    return _parse_json(r.content[0].text) or {"tipo_plano":"desconocido","legibilidad":"regular"}


async def _extraer_pagina(
    client, img_block: Dict, rec: Dict, num_pag: int,
    contexto: str, few_shot: str, escala_info: str
) -> Optional[Dict]:
    """Extrae elementos de una pagina especifica con Sonnet."""
    tipo = rec.get("tipo_plano", "planta_estructural")
    escala = rec.get("escala", "sin_escala")
    unidad_cotas = rec.get("unidad_cotas", "")
    nomenclatura = rec.get("nomenclatura_detectada", "")
    instruccion = INSTRUCCIONES_ESPECIALES.get(tipo, "Extrae todos los elementos visibles.")
    if nomenclatura:
        instruccion = f"NOMENCLATURA DE ESTE PLANO (usala para interpretar etiquetas): {nomenclatura}\n{instruccion}"
    if unidad_cotas:
        instruccion = f"UNIDAD DE COTAS DETECTADA: {unidad_cotas}\n{instruccion}"

    prompt = P_EXTRACCION_PAGINA.format(
        few_shot=few_shot,
        escala=f"{escala} {escala_info}".strip(),
        tipo_plano=tipo,
        ctx=contexto or "No especificado",
        instruccion_especial=instruccion,
        num_pag=num_pag
    )

    r = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=4096,
        system=SYSTEM_EXPERTO,
        messages=[{"role":"user","content":[img_block, {"type":"text","text":prompt}]}]
    )
    logger.info(f"Pag {num_pag} tokens: in={r.usage.input_tokens} out={r.usage.output_tokens}")
    return _parse_json(r.content[0].text)


async def _consolidar(client, paginas_data: List[Dict]) -> Optional[Dict]:
    """Consolida elementos de multiples paginas eliminando duplicados y sumando."""
    resumen = []
    for i, pag in enumerate(paginas_data):
        if pag:
            els = pag.get("elementos", [])
            specs = pag.get("especificaciones_pagina", {})
            resumen.append(
                f"P??GINA {i+1} ({pag.get('tipo_contenido','?')}):\n"
                f"  Specs: fc={specs.get('fc_mpa','?')}MPa, fy={specs.get('fy_mpa','?')}MPa\n"
                f"  Elementos ({len(els)}):\n" +
                "\n".join(
                    f"    - {e.get('nombre','')} | {e.get('cantidad',0)} {e.get('unidad','')} "
                    f"| {e.get('material','')}"
                    for e in els[:10]
                )
            )

    prompt = P_CONSOLIDACION.format(
        n_paginas=len(paginas_data),
        resumen_paginas="\n\n".join(resumen)
    )

    r = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=8096,
        system=SYSTEM_EXPERTO,
        messages=[{"role":"user","content":prompt}]
    )
    logger.info(f"Consolidacion tokens: in={r.usage.input_tokens} out={r.usage.output_tokens}")
    return _parse_json(r.content[0].text)


async def _validar(client, elementos: List[Dict], specs: Dict) -> Optional[Dict]:
    """Valida coherencia tecnica con Sonnet."""
    prompt = P_VALIDACION.format(
        elementos=json.dumps(elementos[:20], ensure_ascii=False),
        specs=json.dumps(specs, ensure_ascii=False)
    )
    r = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=4096,
        system=SYSTEM_EXPERTO,
        messages=[{"role":"user","content":prompt}]
    )
    return _parse_json(r.content[0].text)


async def extract_from_plan(
    file_bytes: bytes, media_type: str,
    contexto: str = "", filename: str = ""
) -> Dict:
    client = anthropic.Anthropic()
    fn_lower = filename.lower()

    # ?????? Preparar imagenes ??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
    imagenes = []  # lista de (img_bytes, media_type, num_pag)
    contexto_dwg = ""

    is_dwg = fn_lower.endswith(".dwg") or fn_lower.endswith(".dxf") or \
             media_type in ("application/dwg","application/dxf","application/acad",
                            "image/vnd.dwg","application/octet-stream")

    if is_dwg:
        logger.info("DWG/DXF detectado...")
        ext_dwg = leer_dwg(file_bytes, filename)
        if not ext_dwg.error:
            contexto_dwg = dwg_to_contexto_claude(ext_dwg)
        if ext_dwg.imagen_png:
            imagenes = [(ext_dwg.imagen_png, "image/png", 1)]
    elif media_type == "application/pdf" or fn_lower.endswith(".pdf"):
        logger.info("PDF ??? imagenes por pagina...")
        imagenes = pdf_to_images_hd(file_bytes, dpi=150)
    else:
        mt = "image/png" if "png" in media_type else "image/jpeg"
        imagenes = [(file_bytes, mt, 1)]

    logger.info(f"Total paginas: {len(imagenes)}")
    if not imagenes:
        raise ValueError("No se pudieron generar imagenes del archivo")

    # ── OCR Tesseract en paralelo (threads, no bloquea el event loop) ──────
    import asyncio as _aio
    contexto_ocr_global = ""
    _ocr_specs = {}
    if tesseract_ok():
        logger.info("Tesseract disponible -- OCR en paralelo...")

        def _ocr_una(args):
            ib_t, np_t = args
            try:
                return np_t, procesar_imagen_plano(ib_t, escala_denominador=100)
            except Exception as e:
                logger.warning(f"OCR pag {np_t}: {e}")
                return np_t, None

        try:
            ocr_results = await _aio.gather(*[
                _aio.to_thread(_ocr_una, (ib, np))
                for ib, _, np in imagenes[:6]
            ])
            ocr_parts = []
            for np_r, res_ocr in sorted(ocr_results, key=lambda x: x[0]):
                if res_ocr and res_ocr.contexto_para_claude:
                    ocr_parts.append(f"[PAGINA {np_r}]\n{res_ocr.contexto_para_claude}")
                    if res_ocr.especificaciones.get('fc_mpa') and 'fc_mpa' not in _ocr_specs:
                        _ocr_specs['fc_mpa'] = res_ocr.especificaciones['fc_mpa']
            if ocr_parts:
                contexto_ocr_global = "\n\n".join(ocr_parts)
                logger.info(f"OCR completo: {len(contexto_ocr_global)} chars")
        except Exception as e:
            logger.warning(f"OCR paralelo fallo: {e}")
    else:
        logger.info("Tesseract no disponible -- usando solo Claude Vision")
    # ?????? Enriquecer contexto ????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
    ctx_completo = contexto or ""
    if contexto_dwg:
        ctx_completo = f"{contexto_dwg}\n\n{ctx_completo}".strip()
    # Enriquecer con specs detectadas por OCR (bug fix: antes se perdian)
    if _ocr_specs.get('fc_mpa') and "fc" not in ctx_completo.lower():
        ctx_completo = f"f'c={_ocr_specs['fc_mpa']}MPa. {ctx_completo}"
    if contexto_ocr_global:
        ctx_completo = f"{contexto_ocr_global}\n\nCONTEXTO DEL USUARIO: {ctx_completo}".strip()

    # ?????? Paso 0: Reconocimiento de la primera pagina ????????????????????????????????????????????????????????????????????????
    logger.info("Paso 0: Reconocimiento global...")
    img0 = _ib(imagenes[0][0], imagenes[0][1])
    rec_global = await _reconocer_pagina(client, img0)
    tipo_global = rec_global.get("tipo_plano","desconocido")
    sis_global = rec_global.get("sistema_estructural","")
    logger.info(f"Sistema: {sis_global} | Tipo: {tipo_global}")

    # ?????? Deteccion de escala ????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
    escala_info = ""
    try:
        textos_ctx = [ctx_completo] if ctx_completo else []
        escala = detectar_escala(
            textos=textos_ctx,
            tipo_plano=tipo_global,
            sistema=sis_global
        )
        if escala:
            escala_info = (
                f"ESCALA: {escala.escala_texto} "
                f"[{escala.metodo}, confianza {escala.confianza}]. "
                f"1mm en plano = {escala.denominador/1000:.4f}m real."
            )
            logger.info(f"Escala: {escala.escala_texto}")
    except Exception as e:
        logger.warning(f"Escala no detectada: {e}")

    # ?????? Few-shot learning ??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
    few_shot = get_few_shot_prompt(tipo_plano=tipo_global, limite=5)

    # ?????? Paso 1: Extraer CADA P??GINA por separado ??????????????????????????????????????????????????????????????????????????????
    # Limitar a 6 paginas maximo para controlar costo
    paginas_a_procesar = imagenes[:6]

    # PARALELO: procesar todas las paginas simultaneamente (reduce tiempo 4-6x)
    import asyncio

    async def _procesar_pagina(img_bytes, img_mt, num_pag):
        try:
            logger.info(f"Extrayendo pagina {num_pag} (paralelo)...")
            img_block = _ib(img_bytes, img_mt)
            rec_pag = await _reconocer_pagina(client, img_block)
            if rec_pag.get("tipo_plano") in ("arquitectonico", "vista_3d") and len(paginas_a_procesar) > 1:
                logger.info(f"Pag {num_pag}: {rec_pag.get('tipo_plano')}, omitiendo")
                return None
            return await _extraer_pagina(
                client, img_block, rec_pag, num_pag,
                ctx_completo, few_shot, escala_info
            )
        except Exception as e:
            logger.warning(f"Pag {num_pag} fallo: {e}")
            return None

    resultados = await asyncio.gather(*[
        _procesar_pagina(ib, mt, np) for ib, mt, np in paginas_a_procesar
    ])
    paginas_data = [r for r in resultados if r]

    logger.info(f"Paginas extraidas: {len(paginas_data)}")

    # ?????? Paso 2: Consolidar si hay multiples paginas ????????????????????????????????????????????????????????????????????????
    if len(paginas_data) == 1:
        # Una sola pagina: convertir formato de pagina a formato final
        pag = paginas_data[0]
        extraccion = {
            "descripcion_proyecto": ctx_completo[:100] if ctx_completo else "Proyecto estructural",
            "tipo_plano": tipo_global,
            "escala": rec_global.get("escala",""),
            "norma": "NSR-10",
            "sistema_estructural": sis_global,
            "especificaciones": {
                "fc_concreto_mpa": pag.get("especificaciones_pagina",{}).get("fc_mpa") or 20.7,
                "fy_acero_mpa": pag.get("especificaciones_pagina",{}).get("fy_mpa") or 420,
                "zona_sismica": "alta",
                "grupo_uso": "II",
                "tipo_suelo": "S2",
            },
            "elementos": pag.get("elementos", []),
            "notas_generales_plano": pag.get("especificaciones_pagina",{}).get("notas_generales",[]),
            "observaciones": pag.get("observaciones",""),
            "confianza": "media",
            "advertencias": [],
            "datos_faltantes": []
        }
    elif len(paginas_data) > 1:
        logger.info(f"Paso 2: Consolidando {len(paginas_data)} paginas...")
        extraccion = await _consolidar(client, paginas_data)
        if not extraccion:
            # Fallback: usar solo la primera pagina
            logger.warning("Consolidacion fallo, usando primera pagina")
            extraccion = {"elementos": paginas_data[0].get("elementos",[]),
                         "especificaciones": {"fc_concreto_mpa":20.7,"fy_acero_mpa":420,"zona_sismica":"alta"},
                         "confianza":"baja","advertencias":["Consolidacion parcial"]}
    else:
        raise ValueError("No se pudo extraer informacion del plano")

    # ?????? Paso 3: Validacion tecnica ???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
    elementos = extraccion.get("elementos", [])
    specs = extraccion.get("especificaciones", {})

    if elementos:
        logger.info(f"Paso 3: Validando {len(elementos)} elementos...")
        val = await _validar(client, elementos, specs)
        if val:
            if val.get("elementos_validados"):
                extraccion["elementos"] = val["elementos_validados"]
            extraccion["correcciones"] = val.get("correcciones", [])
            extraccion["alertas_tecnicas"] = val.get("alertas_tecnicas", [])
            extraccion["confianza"] = val.get("confianza_final", extraccion.get("confianza","media"))

    # Agregar escala al resultado
    extraccion["reconocimiento"] = rec_global
    extraccion["escala_detectada"] = escala_info
    extraccion["paginas_analizadas"] = len(paginas_data)

    # Registrar en feedback
    try:
        registrar_analisis(
            plano_nombre=filename or "plano",
            elementos_extraidos=len(extraccion.get("elementos",[])),
            confianza=extraccion.get("confianza","media")
        )
    except Exception:
        pass

    # ── Saneamiento + Rescate de cantidades ─────────────────────────────────
    try:
        from app.services.rescate_cantidades import rescatar_cantidades, sanear_elementos
        els_saneados = sanear_elementos(extraccion.get("elementos", []))
        els_rescatados, notas_rescate = rescatar_cantidades(els_saneados)
        extraccion["elementos"] = els_rescatados
        if notas_rescate:
            advertencias = extraccion.get("advertencias", []) or []
            advertencias.extend(notas_rescate[:8])
            extraccion["advertencias"] = advertencias
    except Exception as e:
        logger.warning(f"Rescate de cantidades fallo: {e}")

    logger.info(
        f"Extraccion completa: {len(extraccion.get('elementos',[]))} elementos "
        f"| {len(paginas_data)} paginas | confianza={extraccion.get('confianza')}"
    )
    return extraccion
