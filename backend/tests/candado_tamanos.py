# -*- coding: utf-8 -*-
"""CANDADO DE TAMANOS: sqlite ignora String(N); Postgres lo hace cumplir a sangre.
Caza kwargs literales en CONSTRUCTORES de modelos que excedan su columna exacta.
(Nacio del bug real: EventoShare(tipo="pendientes_reportados") 21 > String(20) -> 500 en PG)."""
import os
import re
import sys

RAIZ = os.path.join(os.path.dirname(__file__), '..', 'app')


def limites_por_modelo(db_src: str) -> dict:
    """{(Modelo, campo): N} desde db.py — precision de tabla, cero homonimos."""
    out = {}
    for m in re.finditer(r'class (\w+)\(Base\):\n((?:    .*\n|\n)*?)(?=class |\Z)', db_src):
        modelo, cuerpo = m.group(1), m.group(2)
        for c in re.finditer(r'^\s+(\w+) = Column\(String\((\d+)\)', cuerpo, re.M):
            out[(modelo, c.group(1))] = int(c.group(2))
    return out


def kwargs_de_constructores(src: str, modelos: set):
    """[(modelo, campo, literal)] de cada Modelo(...) con parentesis balanceados."""
    out = []
    for m in re.finditer(r'\b(' + '|'.join(modelos) + r')\(', src):
        i, prof = m.end(), 1
        while i < len(src) and prof:
            if src[i] == '(':
                prof += 1
            elif src[i] == ')':
                prof -= 1
            i += 1
        for kw in re.finditer(r'(\w+)\s*=\s*"([^"\n]*)"', src[m.end():i - 1]):
            out.append((m.group(1), kw.group(1), kw.group(2)))
    return out


def revisar():
    limites = limites_por_modelo(open(os.path.join(RAIZ, 'db.py')).read())
    modelos = {mo for mo, _ in limites}
    problemas = []
    for root, dirs, files in os.walk(RAIZ):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for fn in files:
            if not fn.endswith('.py'):
                continue
            src = open(os.path.join(root, fn)).read()
            for modelo, campo, valor in kwargs_de_constructores(src, modelos):
                lim = limites.get((modelo, campo))
                if lim and len(valor) > lim:
                    problemas.append(f'{fn}: {modelo}({campo}="{valor[:40]}") mide {len(valor)} > String({lim})')
    return problemas


if __name__ == "__main__":
    # AUTO-TEST del candado: debe cazar el bug historico si volviera
    _caso = 'x = EventoShare(proyecto_id=1, tipo="pendientes_reportados", ip="1.2.3.4")'
    _lims = {("EventoShare", "tipo"): 20}
    _hits = [(mo, ca, va) for mo, ca, va in kwargs_de_constructores(_caso, {"EventoShare"})
             if _lims.get((mo, ca)) and len(va) > _lims[(mo, ca)]]
    assert _hits and _hits[0][1] == "tipo", "el auto-test del candado fallo"

    problemas = revisar()
    if problemas:
        print("❌ LITERALES MAS LARGOS QUE SU COLUMNA (Postgres los rechaza):")
        for p in problemas:
            print("   ", p)
        sys.exit(1)
    print("OK: constructores dentro de sus columnas (auto-test del cazador incluido)")
