# -*- coding: utf-8 -*-
"""CANDADO DE AUTHZ — ninguna ruta nace desnuda.

Ley: TODO endpoint debe declarar Depends(usuario_actual) o Depends(admin_actual),
o estar en la LISTA BLANCA CONSCIENTE de abajo (con su razon escrita).
Un endpoint nuevo sin auth y sin declarar aqui = ROJO en el CI.

Asi la proxima ruta que alguien agregue a las 3 a.m. nace protegida o
declarada — nunca desnuda por accidente.
"""
import ast
import os
import sys

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")
API = os.path.join(RAIZ, "backend", "app", "api")

# (archivo, metodo, path) -> razon por la que es publico A PROPOSITO
LISTA_BLANCA = {
    # auth propio del flujo de identidad
    ("auth.py", "POST", "/registro"): "crear cuenta",
    ("auth.py", "POST", "/login"): "iniciar sesion",
    ("auth.py", "POST", "/olvide"): "recuperar clave (token por correo)",
    ("auth.py", "POST", "/restablecer"): "restablecer con token",
    # el universo del CLIENTE: autenticado por share_token opaco (40 chars)
    ("share.py", "*", "/publico/*"): "el cliente sin cuenta — token opaco es la llave",
    ("share.py", "GET", "/c/{slug}"): "tarjeta publica del contratista",
    ("cuentas.py", "GET", "/publico/{token}/{cid}.pdf"): "PDF de cuenta para el cliente (token)",
    # pagos automaticos
    ("wompi.py", "GET", "/disponible"): "flag de configuracion, sin datos",
    ("wompi.py", "POST", "/webhook"): "Wompi firma con secreto de eventos (verificado adentro)",
    # respaldo: autenticacion dual propia (JWT admin o X-Backup-Token)
    ("respaldo.py", "GET", "/completo"): "auth dual adentro (admin JWT o BACKUP_TOKEN)",
    ("respaldo.py", "GET", "/resumen"): "auth dual adentro",
    # calculadoras de referencia (marketing tecnico, solo lectura, datos publicos)
    ("mercado.py", "*", "*"): "calculadoras publicas de referencia",
    ("precios.py", "*", "*"): "base de precios de referencia (lectura)",
    ("validacion.py", "*", "*"): "calculadoras NSR-10 publicas",
    ("presupuesto.py", "POST", "/calcular"): "calculadora publica",
    # radar conocido: modulos IA no cargan en Vercel; pendiente de decision
    ("planos.py", "POST", "/extraer"): "RADAR: legacy IA — no operativo en prod",
}


def _blanqueado(archivo, metodo, path):
    if (archivo, metodo, path) in LISTA_BLANCA:
        return True
    if (archivo, "*", "*") in LISTA_BLANCA:
        return True
    for (a, m, p), _razon in LISTA_BLANCA.items():
        if a == archivo and p.endswith("*") and path.startswith(p[:-1]) and m in ("*", metodo):
            return True
    return False


desnudos = []
total = 0
for fn in sorted(os.listdir(API)):
    if not fn.endswith(".py") or fn == "__init__.py":
        continue
    tree = ast.parse(open(os.path.join(API, fn), encoding="utf-8").read())
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        rutas = [d for d in node.decorator_list
                 if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                 and d.func.attr in ("get", "post", "put", "delete", "patch")]
        if not rutas:
            continue
        total += 1
        defaults = [a for a in (node.args.defaults + list(node.args.kw_defaults)) if a]
        con_auth = any(("usuario_actual" in ast.dump(a)) or ("admin_actual" in ast.dump(a))
                       for a in defaults)
        if con_auth:
            continue
        metodo = rutas[0].func.attr.upper()
        path = rutas[0].args[0].value if rutas[0].args and isinstance(rutas[0].args[0], ast.Constant) else "?"
        if not _blanqueado(fn, metodo, path):
            desnudos.append(f"{fn} {metodo} {path}")

if desnudos:
    print("CANDADO DE AUTHZ EN ROJO — endpoints sin auth NI lista blanca:")
    for d in desnudos:
        print("  ", d)
    print("Protegela con Depends(usuario_actual) o declarala CONSCIENTEMENTE en la lista blanca.")
    sys.exit(1)
print(f"OK authz: {total} endpoints — todos con auth o blanqueados a proposito")
