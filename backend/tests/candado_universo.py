# -*- coding: utf-8 -*-
"""CANDADO DEL UNIVERSO — la coherencia total del multiverso.

Tres leyes:
  1. NO HAY MUERTOS: todo .jsx debe ser alcanzable desde main.jsx por la
     cadena de imports. Un archivo huerfano es codigo zombi que confunde,
     pesa y esconde bugs. (Fundado el dia del entierro de los 9: Step*,
     Stepper, PreciosModal, TablasModal, NSR10Panel, Sensibilidad, Desglose.)
  2. LAS RUTAS EXISTEN: toda pagina montada en App.jsx debe existir en disco.
  3. LOS ROBOTS TIENEN MUSCULO: los dos viajes y el smoke no pueden encoger
     (pasos minimos: privado >= 45, publico >= 70, smoke >= 7 familias).
Corre sin red. Un rojo = el universo perdio coherencia.
"""
import os
import re
import sys

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")
SRC = os.path.join(RAIZ, "frontend", "src")

errores = []

# ── LEY 1: no hay muertos (grafo de imports desde main.jsx) ────────────────
def _resolver(base_dir, ruta):
    """Resuelve './x' o '../y' a un archivo real .jsx/.js si existe."""
    p = os.path.normpath(os.path.join(base_dir, ruta))
    for cand in (p, p + ".jsx", p + ".js", os.path.join(p, "index.jsx"), os.path.join(p, "index.js")):
        if os.path.isfile(cand):
            return os.path.normpath(cand)
    return None

vivos = set()
pendientes = [os.path.join(SRC, "main.jsx")]
RE_IMPORT = re.compile(r"""(?:from|import)\s+['"](\.{1,2}/[^'"]+)['"]""")
while pendientes:
    f = os.path.normpath(pendientes.pop())
    if f in vivos or not os.path.isfile(f):
        continue
    vivos.add(f)
    src = open(f, encoding="utf-8").read()
    for m in RE_IMPORT.finditer(src):
        dest = _resolver(os.path.dirname(f), m.group(1))
        if dest and dest not in vivos:
            pendientes.append(dest)

todos = set()
for dirpath, _dirs, files in os.walk(SRC):
    for fn in files:
        if fn.endswith(".jsx"):
            todos.add(os.path.normpath(os.path.join(dirpath, fn)))

muertos = sorted(os.path.relpath(f, RAIZ) for f in (todos - vivos))
if muertos:
    errores.append("MUERTOS (jsx no alcanzables desde main.jsx):\n  " + "\n  ".join(muertos))

# ── LEY 2: toda pagina de App.jsx existe ────────────────────────────────────
app_src = open(os.path.join(SRC, "App.jsx"), encoding="utf-8").read()
for m in re.finditer(r"import\s+(\w+)\s+from\s+['\"](\./pages/[^'\"]+)['\"]", app_src):
    if not _resolver(SRC, m.group(2)):
        errores.append(f"App.jsx importa pagina inexistente: {m.group(2)}")

# ── LEY 3: los robots no encogen ────────────────────────────────────────────
TESTS = os.path.join(RAIZ, "backend", "tests")
minimos = [("test_viaje_completo.py", r"paso\(", 45),
           ("test_viaje_publico.py", r"paso\(", 70),
           ("smoke_financiero.py", r"^print\(\"OK", 7)]
for archivo, patron, minimo in minimos:
    src = open(os.path.join(TESTS, archivo), encoding="utf-8").read()
    n = len(re.findall(patron, src, re.M))
    if n < minimo:
        errores.append(f"{archivo}: {n} < {minimo} — ¡el guardian encogio!")

if errores:
    print("CANDADO DEL UNIVERSO EN ROJO:")
    for e in errores:
        print(" ", e)
    sys.exit(1)
print(f"OK universo: {len(todos)} jsx todos vivos, paginas de App existen, robots con musculo")

# ── el timeout del cliente HTTP cubre el cold start (la leccion del autosave) ──
_api = open(os.path.join(RAIZ, "frontend", "src", "services", "api.js"), encoding="utf-8").read()
import re as _re
_m = _re.search(r"timeout:\s*(\d+)", _api)
assert _m and int(_m.group(1)) >= 30000, (
    "el timeout de axios debe ser >= 30000ms: Neon dormido + lambda fria tardan 8-15s "
    "y un timeout corto grita 'el servidor no responde' cuando solo estaba despertando")
print("OK timeout: axios espera el cold start (>=30s) — el autosave no grita en falso")
