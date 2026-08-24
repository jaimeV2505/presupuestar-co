# -*- coding: utf-8 -*-
"""
Generador del CONTRATO DE EJECUCION DE OBRA CIVIL.

Construye las clausulas desde los datos del presupuesto, el contratista
y la firma del cliente. Modelo basado en el contrato tipico colombiano
de obra civil entre particulares.

Nota de honestidad legal: este es un acuerdo privado con evidencia
digital (Ley 527 de 1999 reconoce los mensajes de datos como medio
de prueba). No es firma electronica certificada ni escritura publica.
"""
import json
from typing import Dict, List, Optional


def _fmt(v) -> str:
    return f"${round(v or 0):,}".replace(",", ".")


def generar_contrato(proyecto, usuario, items: List[Dict], totales: Dict,
                     firma: Optional[Dict] = None) -> Dict:
    """
    Retorna el contrato estructurado: partes, clausulas, tabla de items, firmas.
    firma: {nombre, documento, fecha} del cliente cuando ya firmo.
    """
    cfg = json.loads(proyecto.contrato_json or "{}")
    plazo = int(cfg.get("plazo_dias") or 45)
    anticipo_pct = float(cfg.get("anticipo_pct") or 50)
    fecha_inicio = cfg.get("fecha_inicio") or "por definir de comun acuerdo"
    lugar = cfg.get("lugar") or proyecto.direccion or proyecto.region or "Colombia"

    total = totales["total"]
    anticipo_valor = round(total * anticipo_pct / 100)
    saldo_pct = round(100 - anticipo_pct, 1)
    saldo_valor = total - anticipo_valor

    contratante = {
        "rol": "CONTRATANTE",
        "nombre": (firma or {}).get("nombre") or proyecto.cliente_nombre or "[Nombre del cliente]",
        "documento": (firma or {}).get("documento") or "[C.C.]",
    }
    contratista = {
        "rol": "CONTRATISTA",
        "nombre": usuario.nombre,
        "documento": getattr(usuario, "documento", "") or "[C.C./NIT]",
        "empresa": usuario.empresa or "",
    }

    encabezado = (
        f"Entre los suscritos, {contratante['nombre'].upper()}, identificado(a) con "
        f"documento N° {contratante['documento']}, quien en adelante se denomina "
        f"la CONTRATANTE; y {contratista['nombre'].upper()}"
        f"{' (' + contratista['empresa'] + ')' if contratista['empresa'] else ''}, "
        f"identificado(a) con documento N° {contratista['documento']}, quien en "
        f"adelante se denomina el CONTRATISTA, hemos celebrado el presente contrato "
        f"de ejecucion de obra civil, que se rige por las siguientes clausulas:"
    )

    forma_pago_extra = ""
    if getattr(usuario, "pago_info", ""):
        forma_pago_extra = (
            f" PARAGRAFO: Los pagos podran realizarse en efectivo o en la cuenta "
            f"del contratista: {usuario.pago_info}."
        )

    clausulas = [
        {
            "titulo": "PRIMERA: OBJETO",
            "texto": (
                f"La contratante {contratante['nombre']} requiere la ejecucion del "
                f"proyecto \"{proyecto.nombre}\" en {lugar}, para lo cual contrata "
                f"los servicios del contratista {contratista['nombre']}. Las partes "
                f"acuerdan que el contratista debera ejecutar las actividades "
                f"detalladas en la tabla de la clausula tercera, correspondientes a "
                f"la cotizacion {proyecto.numero}."
            ),
        },
        {
            "titulo": "SEGUNDA: TERMINO DE EJECUCION",
            "texto": (
                f"Las partes acuerdan que la ejecucion de la obra tendra una duracion "
                f"de {plazo} dias habiles, iniciando desde {fecha_inicio}, sin "
                f"perjuicio de que, por situaciones de fuerza mayor o caso fortuito, "
                f"dicho tiempo pueda extenderse previo acuerdo entre las partes por "
                f"medios escritos o digitales."
            ),
        },
        {
            "titulo": "TERCERA: COSTO DE LA OBRA A EJECUTAR",
            "texto": (
                f"Las partes acuerdan como valor total de la obra la suma de "
                f"{_fmt(total)}, que se discrimina en la tabla de actividades anexa "
                f"a este contrato (cotizacion {proyecto.numero}). "
                f"{totales.get('regimen_iva', '')}"
            ),
            "incluye_tabla": True,
        },
        {
            "titulo": "CUARTA: FORMA DE PAGO",
            "texto": (
                f"Para la ejecucion e inicio de la obra, el CONTRATANTE pagara al "
                f"CONTRATISTA la suma de {_fmt(total)} asi: A) Por anticipo del "
                f"{anticipo_pct:g}%, esto es la suma de {_fmt(anticipo_valor)}. "
                f"B) El saldo del {saldo_pct:g}%, esto es la suma de {_fmt(saldo_valor)}, "
                f"contra avance de obra y/o acta de terminacion y entrega firmada por "
                f"ambas partes.{forma_pago_extra}"
            ),
        },
        {
            "titulo": "QUINTA: RESPONSABILIDADES",
            "texto": (
                "DEL CONTRATISTA: 1. Ejecutar la obra con responsabilidad y "
                "profesionalismo. 2. Informar los avances de la obra al contratante. "
                "3. Permitir el ingreso a la obra al contratante. 4. Informar de "
                "manera inmediata cualquier irregularidad o anomalia no atribuible "
                "al contratista. 5. Contratar personal idoneo bajo su subordinacion. "
                "6. Cumplir las normas legales aplicables y preservar la seguridad "
                "de los trabajadores. DEL CONTRATANTE: 1. Cumplir con los pagos "
                "acordados. 2. Permitir con libertad la ejecucion de la obra civil. "
                "3. Las demas que acuerden las partes."
            ),
        },
        {
            "titulo": "SEXTA: INCUMPLIMIENTO",
            "texto": (
                "Las partes acuerdan que, ante un incumplimiento no justificado, se "
                "procedera de mutuo acuerdo a reformular la ejecucion del contrato "
                "a fin de terminar en debida forma su ejecucion."
            ),
        },
        {
            "titulo": "SEPTIMA: LUGAR Y NOTIFICACIONES",
            "texto": (
                f"Las partes acuerdan como lugar de cumplimiento de las obligaciones "
                f"{lugar}. Las notificaciones entre las partes podran realizarse por "
                f"medios digitales (WhatsApp, correo electronico) a los contactos "
                f"registrados en la plataforma."
            ),
        },
        {
            "titulo": "OCTAVA: ACEPTACION POR MEDIOS DIGITALES",
            "texto": (
                "Las partes reconocen que la aceptacion de este contrato se realiza "
                "por medios digitales y que el registro electronico de la firma "
                "(nombre, documento, fecha y hora) constituye manifestacion valida "
                "de su voluntad, conforme al reconocimiento de los mensajes de datos "
                "previsto en la Ley 527 de 1999 de la Republica de Colombia."
            ),
        },
    ]

    tabla = [
        {
            "item": i + 1,
            "descripcion": it.get("descripcion", ""),
            "unidad": it.get("unidad", ""),
            "cantidad": it.get("cantidad", 0),
            "v_unitario": round(it.get("precio_unitario") or 0),
            "subtotal": round((it.get("cantidad") or 0) * (it.get("precio_unitario") or 0)),
        }
        for i, it in enumerate(items)
    ]

    firmas = {
        "contratista": {
            "nombre": contratista["nombre"],
            "documento": contratista["documento"],
            "fecha": proyecto.actualizado.strftime("%d/%m/%Y") if proyecto.actualizado else "",
            "estado": "Emitido digitalmente al compartir la cotizacion",
        },
        "contratante": {
            "nombre": firma["nombre"] if firma else None,
            "documento": firma.get("documento", "") if firma else None,
            "fecha": firma.get("fecha", "") if firma else None,
            "estado": "Firmado digitalmente" if firma else "Pendiente de firma",
        },
    }

    return {
        "firma_imagen": (firma or {}).get("imagen", ""),
        "titulo": "CONTRATO DE EJECUCION DE OBRA CIVIL",
        "numero": proyecto.numero,
        "encabezado": encabezado,
        "clausulas": clausulas,
        "tabla": tabla,
        "total": total,
        "config": {"plazo_dias": plazo, "anticipo_pct": anticipo_pct,
                   "fecha_inicio": fecha_inicio, "lugar": lugar},
        "firmas": firmas,
        "firmado": bool(firma),

    }
