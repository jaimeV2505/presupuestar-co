# -*- coding: utf-8 -*-
"""CANDADO ANTI-DECORADOR — los handlers son puros y unicos.

Dos leyes:
  1. NO REDEFINIR: dos funciones con el mismo nombre en un mismo modulo api
     hacen que Python pise la primera en silencio — FastAPI registra rutas
     fantasma o pierde una sin avisar.
  2. HANDLER NO LLAMA HANDLER: una funcion decorada con @router jamas invoca
     directamente a otra decorada (le pasaria Depends sin resolver: user y db
     llegarian como objetos Depends crudos). La logica compartida vive en
     helpers sin decorar (_proyecto, _liquidar, componer_precio...).
"""
import ast
import os
import sys

RAIZ = os.path.join(os.path.dirname(__file__), "..", "..")
API = os.path.join(RAIZ, "backend", "app", "api")

errores = []
total_handlers = 0

for fn in sorted(os.listdir(API)):
    if not fn.endswith(".py") or fn == "__init__.py":
        continue
    tree = ast.parse(open(os.path.join(API, fn), encoding="utf-8").read())

    # nombres de funciones top-level y cuales son handlers
    vistos = {}
    handlers = set()
    cuerpos = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in vistos:
                errores.append(f"{fn}: '{node.name}' REDEFINIDA (lineas {vistos[node.name]} y {node.lineno}) — la primera muere en silencio")
            vistos[node.name] = node.lineno
            es_handler = any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                             and d.func.attr in ("get", "post", "put", "delete", "patch")
                             for d in node.decorator_list)
            if es_handler:
                handlers.add(node.name)
                cuerpos[node.name] = node

    total_handlers += len(handlers)

    # ley 2: handler no llama handler
    for nombre, node in cuerpos.items():
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                if sub.func.id in handlers and sub.func.id != nombre:
                    errores.append(f"{fn}: handler '{nombre}' llama al handler '{sub.func.id}' "
                                   f"(linea {sub.lineno}) — los Depends llegan crudos; extrae un helper")

if errores:
    print("CANDADO ANTI-DECORADOR EN ROJO:")
    for e in errores:
        print("  ", e)
    sys.exit(1)
print(f"OK anti-decorador: {total_handlers} handlers unicos y puros (nadie redefine, nadie llama handlers)")
