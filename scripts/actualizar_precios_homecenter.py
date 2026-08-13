#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FETCHER DE REFERENCIA HOMECENTER -> cache de precios externos (OFFLINE, manual).

⚠️  LEER ANTES DE USAR:
  - Corre EN TU MAQUINA, manualmente o por cron (jamas dentro de la app: la
    fuente_externa solo lee el JSON cacheado — si esto se rompe, nada se cae).
  - Los T&C de sitios retail suelen restringir el acceso automatizado. Este
    script consulta POCOS terminos (los 20 insumos top), con pausas de varios
    segundos, identificandose honestamente. Aun asi: usalo bajo tu criterio,
    o mejor: usa precios_desde_csv.py con listas de ferreterias ALIADAS.
  - El HTML/API de retail cambia sin aviso: cuando se rompa, el cache viejo
    sigue sirviendo (con su fecha visible) y las demas fuentes responden.

Uso:  python3 scripts/actualizar_precios_homecenter.py > precios_externos.json
"""
import json
import sys
import time
from datetime import date

TERMINOS = ["cemento gris", "arena", "triturado", "ladrillo", "bloque",
            "acero refuerzo", "malla electrosoldada", "tubo pvc sanitaria",
            "tubo pvc presion", "cable thhn", "pintura vinilo", "estuco",
            "ceramica piso", "porcelanato", "pegante ceramica", "drywall",
            "teja fibrocemento", "impermeabilizante", "toma corriente", "breaker"]

PAUSA_SEG = 6          # respeto: una consulta cada 6s
TIMEOUT = 10
UA = "PresupuestarCO-precios/1.0 (referencia de mercado; contacto: soporte@presupuestar.co)"


def buscar(termino: str) -> list:
    """Consulta la busqueda publica y extrae (nombre, precio) del primer resultado util.
    Implementacion minima y fragil A PROPOSITO: si el sitio cambia, retorna [] y ya."""
    try:
        import requests
    except ImportError:
        print("pip install requests", file=sys.stderr)
        sys.exit(1)
    try:
        r = requests.get(
            "https://www.homecenter.com.co/s/search/v1/soco",
            params={"q": termino, "currentpage": 1},
            headers={"User-Agent": UA, "Accept": "application/json"},
            timeout=TIMEOUT,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        productos = (data.get("data") or {}).get("results") or []
        out = []
        for p in productos[:2]:
            nombre = p.get("displayName") or ""
            precios = p.get("prices") or []
            precio = None
            for pr in precios:
                try:
                    precio = int(float(str(pr.get("price", [None])[0]).replace(",", "")))
                    break
                except (TypeError, ValueError, IndexError):
                    continue
            if nombre and precio and 100 <= precio <= 500_000_000:
                out.append({"fuente": "homecenter", "nombre": nombre[:160],
                            "unidad": "un", "precio": precio,
                            "fecha": date.today().strftime("%d/%m/%Y"),
                            "detalle": "Precio vitrina Homecenter (referencia)"})
        return out
    except Exception as e:
        print(f"  ({termino}: {e.__class__.__name__} — se omite)", file=sys.stderr)
        return []


def main():
    todos = []
    for i, t in enumerate(TERMINOS):
        print(f"[{i+1}/{len(TERMINOS)}] {t}", file=sys.stderr)
        todos += buscar(t)
        if i < len(TERMINOS) - 1:
            time.sleep(PAUSA_SEG)
    json.dump(todos, sys.stdout, ensure_ascii=False, indent=1)
    print(f"\n-- {len(todos)} precios cacheados. Sube el JSON y apunta PRECIOS_EXTERNOS_JSON.", file=sys.stderr)


if __name__ == "__main__":
    main()
