#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONVERSOR DE LISTAS DE ALIADOS -> cache de precios externos.
El camino RECOMENDADO para nutrir la fuente externa: la ferreteria aliada
manda su lista (CSV: nombre,unidad,precio) y esto genera el JSON que
fuente_externa() consume via PRECIOS_EXTERNOS_JSON. Cero scraping, cero ToS,
y el aliado gana visibilidad ante contratistas que compran.

Uso:
  python3 scripts/precios_desde_csv.py lista_ferreteria.csv "Ferreteria El Roble" > precios_externos.json
  # en Vercel: subir el JSON y setear PRECIOS_EXTERNOS_JSON=/ruta/al/json
"""
import csv
import json
import sys
from datetime import date

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit(1)

ruta, fuente = sys.argv[1], sys.argv[2][:60]
hoy = date.today().strftime("%d/%m/%Y")
out = []
with open(ruta, encoding="utf-8-sig") as f:
    for fila in csv.DictReader(f):
        try:
            precio = int(float(str(fila.get("precio", "0")).replace(".", "").replace(",", ".")))
        except ValueError:
            continue
        nombre = (fila.get("nombre") or "").strip()
        if len(nombre) < 2 or precio <= 0 or precio > 500_000_000:
            continue
        out.append({"fuente": fuente, "nombre": nombre[:160],
                    "unidad": (fila.get("unidad") or "un").strip()[:15],
                    "precio": precio, "fecha": hoy,
                    "detalle": f"Lista {fuente} {hoy}"})
json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
print(f"\n-- {len(out)} precios validos de {fuente}", file=sys.stderr)
