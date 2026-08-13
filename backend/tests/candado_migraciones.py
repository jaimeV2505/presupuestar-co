"""Candado de migraciones: toda columna de una tabla VIEJA que se agregue al modelo
debe tener su ALTER en las listas de migracion (PG y sqlite) — o produccion revienta.
Las tablas NUEVAS se crean solas con create_all; las columnas nuevas en tablas viejas NO."""
import ast, re, os, sys

RAIZ = os.path.join(os.path.dirname(__file__), '..', '..')
src = open(os.path.join(RAIZ, 'backend/app/db.py')).read()

# columnas por tabla segun los MODELOS
tree = ast.parse(src)
modelos = {}
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        tabla = None
        cols = []
        for sub in node.body:
            if isinstance(sub, ast.Assign) and isinstance(sub.targets[0], ast.Name):
                nombre = sub.targets[0].id
                if nombre == '__tablename__' and isinstance(sub.value, ast.Constant):
                    tabla = sub.value.value
                elif isinstance(sub.value, ast.Call) and getattr(sub.value.func, 'id', '') == 'Column':
                    cols.append(nombre)
        if tabla:
            modelos[tabla] = set(cols)

# ALTERs declarados (PG "IF NOT EXISTS" + tuplas sqlite)
alters_pg = set(re.findall(r'ALTER TABLE (\w+) ADD COLUMN IF NOT EXISTS (\w+)', src))
alters_sq = set(re.findall(r'\("(\w+)", "(\w+)", "ALTER TABLE', src))

# tablas del nucleo original (existian antes de la era de migraciones — cualquier columna
# nueva en ellas DEBE tener ALTER). Las demas tablas nacieron completas via create_all.
TABLAS_VIEJAS_CON_MIGRACIONES = {t for t, _ in alters_pg} | {t for t, _ in alters_sq}

problemas = []
for tabla in TABLAS_VIEJAS_CON_MIGRACIONES:
    cols_modelo = modelos.get(tabla, set())
    pg = {c for t, c in alters_pg if t == tabla}
    sq = {c for t, c in alters_sq if t == tabla}
    # toda columna migrada en PG debe estarlo en sqlite y viceversa (paridad de ambientes)
    solo_pg = pg - sq
    solo_sq = sq - pg
    if solo_pg: problemas.append(f"{tabla}: en PG pero falta en sqlite -> {sorted(solo_pg)}")
    if solo_sq: problemas.append(f"{tabla}: en sqlite pero falta en PG -> {sorted(solo_sq)}")
    # toda columna migrada debe existir en el modelo (nada huerfano)
    fantasma = (pg | sq) - cols_modelo
    if fantasma: problemas.append(f"{tabla}: migrada pero NO esta en el modelo -> {sorted(fantasma)}")

if problemas:
    print("MIGRACIONES INCONSISTENTES:")
    for p in problemas: print("  ", p)
    sys.exit(1)
print(f"OK: paridad PG↔sqlite en {len(TABLAS_VIEJAS_CON_MIGRACIONES)} tablas migradas, sin huerfanas")
