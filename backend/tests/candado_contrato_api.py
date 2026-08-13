"""Candado de contrato API: cada llamada del frontend debe tener su endpoint en el backend."""
import ast, os, re, sys

RAIZ = os.path.join(os.path.dirname(__file__), '..', '..')

def rutas_backend():
    """Todas las rutas reales: prefijo del include_router + path del decorador."""
    main = open(os.path.join(RAIZ, 'backend/app/main.py')).read()
    prefijos = dict(re.findall(r'include_router\((\w+)\.router,\s*prefix="([^"]+)"', main))
    rutas = set()
    # rutas directas en main (p.ej. /api/s/{token})
    for m in re.finditer(r'@app\.(?:get|post|put|delete)\("([^"]+)"\)', main):
        rutas.add(m.group(1))
    api_dir = os.path.join(RAIZ, 'backend/app/api')
    for fn in os.listdir(api_dir):
        if not fn.endswith('.py') or fn == '__init__.py':
            continue
        mod = fn[:-3]
        pref = prefijos.get(mod, f"/api/{mod}")
        src = open(os.path.join(api_dir, fn)).read()
        for m in re.finditer(r'@router\.(?:get|post|put|delete)\("([^"]*)"\)', src):
            rutas.add(pref + m.group(1))
    return rutas

def llamadas_frontend():
    src = open(os.path.join(RAIZ, 'frontend/src/services/api.js')).read()
    llamadas = []
    for m in re.finditer(r'api\.(get|post|put|delete)\((`[^`]+`|\'[^\']+\'|"[^"]+")', src):
        ruta = m.group(2)[1:-1]
        ruta = ruta.split('?')[0]                          # query string no es parte de la ruta
        ruta = re.sub(r'\$\{[^}]+\}', '{X}', ruta)   # template vars -> comodin
        llamadas.append(ruta)
    return llamadas

def normal(r):
    return re.sub(r'\{[^}]+\}', '{X}', r).rstrip('/')

backend = {normal(r) for r in rutas_backend()}
faltantes = []
for ll in llamadas_frontend():
    objetivo = normal('/api' + ll if not ll.startswith('/api') else ll)
    if objetivo not in backend:
        faltantes.append(objetivo)
if faltantes:
    print("LLAMADAS SIN ENDPOINT:")
    for f in sorted(set(faltantes)):
        print("  ", f)
    sys.exit(1)
print(f"OK: {len(llamadas_frontend())} llamadas del frontend tienen endpoint real")
