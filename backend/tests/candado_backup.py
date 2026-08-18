# -*- coding: utf-8 -*-
"""CANDADO DEL BACKUP — GROOT jamas renace mutilado.

Ley: TODA tabla de db.py debe estar en MODELOS del respaldo, o declarada
en EXCLUIDAS con su razon escrita. La tabla `disenos` se quedo fuera en
silencio (nacio despues de la ronda del backup total) — este candado
convierte ese olvido en IMPOSIBLE. Fundado el 18/8/2026, dia del estreno.
"""
import os
import re
import sys

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")

# tabla -> razon por la que NO viaja, a proposito
EXCLUIDAS = {
    "intentos_acceso": "ruido de rate-limit, sin valor de restore",
}

db = open(os.path.join(RAIZ, "backend", "app", "db.py"), encoding="utf-8").read()
clase_a_tabla = dict(re.findall(r'class (\w+)\(Base\):.*?__tablename__ = "(\w+)"', db, re.S))

resp = open(os.path.join(RAIZ, "backend", "app", "api", "respaldo.py"), encoding="utf-8").read()
m = re.search(r"MODELOS = \[(.*?)\]", resp, re.S)
modelos = {x.strip() for x in m.group(1).replace("\n", "").split(",") if x.strip()}
respaldadas = {clase_a_tabla[c] for c in modelos if c in clase_a_tabla}

todas = set(clase_a_tabla.values())
huerfanas = todas - respaldadas - set(EXCLUIDAS)
fantasmas = respaldadas - todas

if huerfanas or fantasmas:
    print("CANDADO DEL BACKUP EN ROJO:")
    for t in sorted(huerfanas):
        print(f"  ❌ la tabla '{t}' NO viaja en el respaldo ni esta excluida a proposito — "
              f"sus datos se PERDERIAN en un restore. Sumala a MODELOS o declarala en EXCLUIDAS.")
    for t in sorted(fantasmas):
        print(f"  ❌ MODELOS respalda '{t}' que ya no existe en db.py")
    sys.exit(1)
print(f"OK backup: {len(respaldadas)}/{len(todas)} tablas viajan; "
      f"excluidas a proposito: {sorted(EXCLUIDAS)} — GROOT renace completo")
