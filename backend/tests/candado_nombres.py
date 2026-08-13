"""Candado #4 EXTENDIDO: resolucion de nombres en cuerpos, con closures y scopes reales."""
import ast, os, sys

def nombres_de_modulo(tree):
    """Todo nombre definido a nivel de modulo (incluye dentro de if/try/with de modulo)."""
    nombres = set(dir(__builtins__)) | {'__name__', '__file__', '__doc__'}
    def visitar(nodos):
        for node in nodos:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                nombres.add(node.name)          # el nombre si, el cuerpo no
                continue
            if isinstance(node, ast.Import):
                for a in node.names: nombres.add((a.asname or a.name).split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                for a in node.names: nombres.add(a.asname or a.name)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    for n in ast.walk(t):
                        if isinstance(n, ast.Name): nombres.add(n.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                nombres.add(node.target.id)
            elif isinstance(node, ast.For):
                for n in ast.walk(node.target):
                    if isinstance(n, ast.Name): nombres.add(n.id)
            # recursion en bloques de control de modulo
            for campo in ('body', 'orelse', 'finalbody', 'handlers'):
                sub = getattr(node, campo, None)
                if sub:
                    visitar([h for h in sub] if campo != 'handlers' else sub)
            if isinstance(node, ast.Try):
                for h in node.handlers:
                    if h.name: nombres.add(h.name)
                    visitar(h.body)
            if isinstance(node, (ast.With,)):
                for item in node.items:
                    if item.optional_vars:
                        for n in ast.walk(item.optional_vars):
                            if isinstance(n, ast.Name): nombres.add(n.id)
    visitar(tree.body)
    return nombres

def locales_de(fn):
    loc = {a.arg for a in fn.args.args} | {a.arg for a in fn.args.kwonlyargs} | {a.arg for a in fn.args.posonlyargs}
    if fn.args.vararg: loc.add(fn.args.vararg.arg)
    if fn.args.kwarg: loc.add(fn.args.kwarg.arg)
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            loc.add(node.id)
        elif isinstance(node, ast.Import):
            for a in node.names: loc.add((a.asname or a.name).split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            for a in node.names: loc.add(a.asname or a.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not fn:
            loc.add(node.name)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            loc.add(node.name)
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            for gen in node.generators:
                for t in ast.walk(gen.target):
                    if isinstance(t, ast.Name): loc.add(t.id)
        elif isinstance(node, ast.Lambda):
            for a in node.args.args: loc.add(a.arg)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars:
                    for n in ast.walk(item.optional_vars):
                        if isinstance(n, ast.Name): loc.add(n.id)
        elif isinstance(node, ast.Global):
            loc.update(node.names)
    return loc

def revisar(path):
    tree = ast.parse(open(path).read())
    modulo = nombres_de_modulo(tree)
    problemas = []

    def revisar_fn(fn, heredados):
        propios = locales_de(fn)
        alcance = propios | heredados
        usados = set()
        # usos directos de ESTA funcion (sin entrar a funciones anidadas)
        def recolectar(n):
            for hijo in ast.iter_child_nodes(n):
                if isinstance(hijo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                    continue
                if isinstance(hijo, ast.Name) and isinstance(hijo.ctx, ast.Load):
                    usados.add(hijo.id)
                recolectar(hijo)
        recolectar(fn)
        falta = usados - alcance - modulo
        if falta:
            problemas.append(f"{os.path.basename(path)}::{fn.name} -> {sorted(falta)}")
        # anidadas heredan el alcance del padre (closure)
        for node in ast.walk(fn):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not fn:
                # solo hijas directas del arbol de fn (evitar re-procesar nietos dos veces): iter sencillo
                pass
        for node in fn.body:
            for sub in ast.walk(node):
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    revisar_fn(sub, alcance)

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            revisar_fn(node, set())
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    revisar_fn(sub, set())
    return problemas

if __name__ == '__main__':
    raiz = sys.argv[1] if len(sys.argv) > 1 else 'backend/app'
    todos = []
    for root, dirs, files in os.walk(raiz):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in files:
            if f.endswith('.py'):
                todos += revisar(os.path.join(root, f))
    if todos:
        print("NOMBRES SIN RESOLVER (potencial NameError en runtime):")
        for p in todos: print("  ", p)
        sys.exit(1)
    print("OK: todos los cuerpos resuelven")
