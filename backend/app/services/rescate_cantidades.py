# -*- coding: utf-8 -*-
"""
Autocompletado de cantidades post-extraccion.

Cuando Claude extrae un elemento sin cantidad, este modulo intenta
rescatarlo usando la geometria de OTROS elementos del mismo plano:

  - Correa sin total pero con @separacion -> usa area de la cubierta
  - Viga sin total pero hay N columnas -> estima vigas por retícula
  - Elemento con dimension_largo_m pero cantidad=0 -> usa la longitud
  - Anclajes sin cantidad pero hay N columnas -> 1 juego por columna

Cada rescate se marca con dato_estimado=true y una nota explicando
el calculo, para que el ingeniero pueda verificar.
"""
import re
import math
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


def rescatar_cantidades(elementos: List[Dict]) -> Tuple[List[Dict], List[str]]:
    """
    Intenta completar cantidades faltantes usando la geometria del plano.
    Retorna (elementos_actualizados, notas_de_rescate).
    """
    notas = []

    # ── Recolectar geometria disponible del plano ─────────────────────────
    area_cubierta = 0
    ancho_estimado = 0
    largo_estimado = 0
    num_columnas = 0
    num_porticos = 0

    for el in elementos:
        tipo = el.get("tipo", "")
        nombre = (el.get("nombre", "") or "").upper()

        if el.get("area_m2"):
            area_cubierta = max(area_cubierta, el["area_m2"])

        if tipo == "columnas" or "COLUMNA" in nombre:
            c = el.get("cantidad") or 0
            if el.get("unidad", "un") == "un" and c > 0:
                num_columnas += int(c)

    # Estimar porticos: en naves industriales tipicas, columnas van en pares
    if num_columnas >= 4:
        num_porticos = num_columnas // 2

    # Estimar dimensiones de la nave desde el area o desde longitudes de vigas
    vigas_largas = [
        el.get("dimension_largo_m") or 0
        for el in elementos
        if el.get("tipo") in ("vigas", "cubierta") and (el.get("dimension_largo_m") or 0) > 3
    ]
    if vigas_largas:
        ancho_estimado = max(vigas_largas)  # la luz mayor suele ser el ancho de la nave

    if area_cubierta > 0 and ancho_estimado > 0:
        largo_estimado = area_cubierta / ancho_estimado
    elif num_porticos > 1 and ancho_estimado > 0:
        # Separacion tipica de porticos: 5-6m
        largo_estimado = (num_porticos - 1) * 5.5
        area_cubierta = area_cubierta or (ancho_estimado * largo_estimado)

    # ── Rescatar elemento por elemento ────────────────────────────────────
    out = []
    for el in elementos:
        el_new = dict(el)
        cant = el.get("cantidad") or 0
        nombre = (el.get("nombre", "") or "")
        nombre_u = nombre.upper()
        notas_el = (el.get("notas", "") or "")
        tipo = el.get("tipo", "")
        ref = el.get("referencia", "") or nombre[:30]

        if cant > 0:
            out.append(el_new)
            continue

        rescatado = False

        # CASO 1: tiene dimension_largo_m -> usar como cantidad en metros
        largo = el.get("dimension_largo_m") or 0
        if largo > 0 and not rescatado:
            el_new["cantidad"] = round(largo, 2)
            el_new["unidad"] = "m"
            el_new["dato_estimado"] = True
            el_new["notas"] = f"{notas_el} | RESCATE: usando longitud {largo}m como cantidad (1 pieza)".strip(" |")
            notas.append(f"'{ref}': cantidad rescatada de la longitud ({largo}m)")
            rescatado = True

        # CASO 2: correa con @separacion y hay geometria de nave
        sep_match = re.search(r'@\s*([\d.,]+)\s*(m|cm)?', nombre + " " + notas_el, re.I)
        es_correa = any(k in nombre_u for k in ["CORREA", "PHR", "CANAL", "OMEGA"])
        if not rescatado and es_correa and sep_match and ancho_estimado > 0 and largo_estimado > 0:
            sv = float(sep_match.group(1).replace(",", "."))
            su = (sep_match.group(2) or "m").lower()
            sep = sv / 100 if su == "cm" else sv
            if 0.3 <= sep <= 3.0:
                n_correas = math.ceil(ancho_estimado / sep) + 1
                metros = round(n_correas * largo_estimado * 1.05, 1)
                el_new["cantidad"] = metros
                el_new["unidad"] = "m"
                el_new["dato_estimado"] = True
                el_new["notas"] = (
                    f"{notas_el} | RESCATE: {n_correas} correas @ {sep}m x "
                    f"{largo_estimado:.1f}m +5% = {metros}m. VERIFICAR contra plano."
                ).strip(" |")
                notas.append(f"'{ref}': {n_correas} correas calculadas por separacion @ {sep}m")
                rescatado = True

        # CASO 3: viga de cubierta / cercha sin total pero hay porticos
        es_viga_cub = tipo in ("vigas", "cubierta") and any(
            k in nombre_u for k in ["VIGA", "CERCHA", "PTE", "IPE", "HEA", "W"]
        )
        if not rescatado and es_viga_cub and num_porticos > 0 and ancho_estimado > 0:
            metros = round(num_porticos * ancho_estimado * 1.05, 1)
            el_new["cantidad"] = metros
            el_new["unidad"] = "m"
            el_new["dato_estimado"] = True
            el_new["notas"] = (
                f"{notas_el} | RESCATE: {num_porticos} porticos x {ancho_estimado:.1f}m "
                f"+5% = {metros}m. VERIFICAR contra plano."
            ).strip(" |")
            notas.append(f"'{ref}': estimado por {num_porticos} porticos x {ancho_estimado:.1f}m")
            rescatado = True

        # CASO 4: anclajes/pernos/platinas sin cantidad -> 1 juego por columna
        es_anclaje = any(k in nombre_u for k in ["ANCLAJE", "PERNO", "PLATINA", "PLACA BASE", "PLACA_BASE"])
        if not rescatado and es_anclaje and num_columnas > 0:
            # Tipico: 4 pernos por placa base, 1 placa por columna
            if "PERNO" in nombre_u:
                cant_est = num_columnas * 4
            else:
                cant_est = num_columnas
            el_new["cantidad"] = cant_est
            el_new["unidad"] = "un"
            el_new["dato_estimado"] = True
            el_new["notas"] = (
                f"{notas_el} | RESCATE: {cant_est} un estimadas de {num_columnas} columnas. "
                f"VERIFICAR detalle de anclaje."
            ).strip(" |")
            notas.append(f"'{ref}': {cant_est} un estimadas ({num_columnas} columnas)")
            rescatado = True

        # CASO 5: conexiones soldadas -> estimar por numero de nudos
        es_conexion = "CONEXION" in nombre_u or "SOLDAD" in nombre_u or "NUDO" in nombre_u
        if not rescatado and es_conexion and num_columnas > 0:
            cant_est = num_columnas * 2  # 2 nudos tipicos por columna en portico
            el_new["cantidad"] = cant_est
            el_new["unidad"] = "un"
            el_new["dato_estimado"] = True
            el_new["notas"] = (
                f"{notas_el} | RESCATE: ~{cant_est} conexiones estimadas de la reticula. VERIFICAR."
            ).strip(" |")
            notas.append(f"'{ref}': {cant_est} conexiones estimadas")
            rescatado = True

        if not rescatado:
            el_new["notas"] = (
                f"{notas_el} | SIN CANTIDAD: el plano no da datos suficientes. "
                f"Completar manualmente."
            ).strip(" |")
            notas.append(f"'{ref}': NO se pudo rescatar — completar manualmente")

        out.append(el_new)

    if notas:
        logger.info(f"Rescate de cantidades: {len(notas)} elementos procesados")

    return out, notas


def sanear_elementos(elementos: List[Dict]) -> List[Dict]:
    """
    Garantiza que TODO elemento tenga nombre, tipo, cantidad y unidad validos.
    Se aplica SIEMPRE antes de devolver la extraccion al frontend.

    Reglas de fallback para nombre:
      1. nombre existente
      2. material (ej: "PTE 150x150x4")
      3. referencia + tipo (ej: "ANC1 anclaje")
      4. tipo solo (ej: "elemento vigas")
    """
    TIPOS_VALIDOS = {
        "columnas", "vigas", "losa", "cimentacion", "muros", "escaleras",
        "cubierta", "viga_amarre", "caisson", "muro_contencion", "otros"
    }
    MAPA_TIPOS = {
        "columna_metalica": "columnas", "columna": "columnas",
        "viga_metalica": "vigas", "viga": "vigas",
        "correa_metalica": "cubierta", "correa": "cubierta",
        "cercha": "cubierta", "tensor": "cubierta",
        "anclaje_placa_base": "otros", "anclaje": "otros",
        "conexion_soldada": "otros", "conexion": "otros",
        "platina": "otros", "canoa": "cubierta", "canal": "cubierta",
        "zapata": "cimentacion", "pilote": "caisson",
        "arriostramiento": "otros", "riostra": "otros",
    }

    out = []
    for el in elementos:
        if not isinstance(el, dict):
            continue
        e = dict(el)

        # Tipo: normalizar y validar
        tipo_raw = (e.get("tipo") or "otros").lower().strip()
        e["tipo"] = MAPA_TIPOS.get(tipo_raw, tipo_raw if tipo_raw in TIPOS_VALIDOS else "otros")

        # Nombre: cascada de fallbacks (incluye campos alternativos que
        # el modelo puede inventar: descripcion, perfil, elemento, item)
        nombre = ""
        for campo in ("nombre", "descripcion", "perfil", "elemento", "item", "material"):
            v = e.get(campo)
            if v and isinstance(v, str) and v.strip():
                nombre = v.strip()
                break
        if not nombre:
            ref = (e.get("referencia") or e.get("ref") or e.get("id") or "").strip()
            nombre = f"{ref} {tipo_raw}".strip() if ref else ""
        if not nombre:
            # Ultimo recurso: buscar CUALQUIER string largo en el dict
            for k, v in e.items():
                if isinstance(v, str) and len(v.strip()) > 8 and k not in ("unidad", "tipo", "notas", "ubicacion"):
                    nombre = v.strip()
                    break
        if not nombre:
            nombre = f"elemento {e['tipo']}"
        e["nombre"] = nombre[:120]

        # Cantidad: buscar tambien en campos alternativos
        if not e.get("cantidad"):
            for campo in ("cant", "qty", "total", "cantidad_total", "metros", "longitud_total_m"):
                v = e.get(campo)
                if v:
                    try:
                        e["cantidad"] = float(str(v).replace(",", "."))
                        break
                    except (ValueError, TypeError):
                        pass

        # Cantidad: numerica siempre
        cant = e.get("cantidad")
        if isinstance(cant, str):
            try:
                cant = float(cant.replace(",", "."))
            except (ValueError, AttributeError):
                cant = 0
        e["cantidad"] = float(cant) if cant else 0.0

        # Unidad: valida siempre
        uni = (e.get("unidad") or "").strip().lower()
        uni = uni.replace("m2", "m²").replace("m3", "m³")
        if uni not in ("un", "m", "m²", "m³", "kg", "pto", "gl"):
            uni = "un"
        e["unidad"] = uni

        # Numericos opcionales: coercion segura
        for campo in ("dimension_ancho_cm", "dimension_alto_cm", "dimension_largo_m",
                      "altura_libre_m", "espesor_cm", "area_m2", "dimension_diametro_cm"):
            v = e.get(campo)
            if isinstance(v, str):
                try:
                    e[campo] = float(v.replace(",", "."))
                except (ValueError, AttributeError):
                    e[campo] = None

        out.append(e)
    return out
