# -*- coding: utf-8 -*-
"""CANDADO DEL DINERO GRANDE — un contrato estatal jamas revienta la base.

Ley: toda columna que guarde PESOS debe ser BigInteger (Postgres INTEGER
muere en $2.147.483.647 — un contrato publico MEDIANO). Cazado en la
auditoria pre-live del 18/8/2026: 11 columnas de dinero eran de 32 bits.
"""
import os, re, sys

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")
db = open(os.path.join(RAIZ, "backend", "app", "db.py"), encoding="utf-8").read()

CAMPOS_DINERO = ("valor", "valor_corte", "valor_ejecutado", "neto", "deducciones",
                 "retencion", "amortizacion", "monto_centavos", "monto", "precio",
                 "anticipo_total")
rotos = []
for c in CAMPOS_DINERO:
    for m in re.finditer(rf'^\s*{c}\w*\s*=\s*Column\((\w+)', db, re.M):
        if m.group(1) == "Integer":
            rotos.append(f"{c} usa Integer (32 bits) — un contrato de >$2.147M lo revienta")
# y toda columna NUEVA con nombre de dinero debe nacer grande
if rotos:
    print("CANDADO DEL DINERO EN ROJO:")
    for r in rotos: print("  ❌", r)
    sys.exit(1)
n_big = db.count("BigInteger")
print(f"OK dinero: {n_big} columnas en BigInteger — los contratos estatales caben completos")
