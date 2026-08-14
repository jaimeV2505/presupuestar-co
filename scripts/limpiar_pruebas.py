#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIMPIEZA DE DATOS DE PRUEBA — empezar de cero sin ruido visual.

Borra TODO lo de uno o varios usuarios (proyectos, avances, actas, otrosies,
interacciones, APUs propios, proveedores, notificaciones...) en el ORDEN
correcto de dependencias. Las cuentas de usuario se conservan salvo que
pidas lo contrario.

CINTURONES DE SEGURIDAD:
  1. DRY-RUN por defecto: sin --borrar solo MUESTRA lo que borraria.
  2. Sin --email debes pasar --todos (borrar todo es una decision explicita).
  3. Antes de borrar de verdad, DESCARGA EL RESPALDO:
     curl -H "X-Backup-Token: TU_TOKEN" https://presupuestar-co.vercel.app/api/respaldo/completo > respaldo_antes_limpieza.json

USO (en tu maquina, con el venv del proyecto):
  export DATABASE_URL="postgresql://...tu-neon..."       # la misma de Vercel
  python3 scripts/limpiar_pruebas.py                      # dry-run de TODO
  python3 scripts/limpiar_pruebas.py --email test@x.com   # dry-run de ese usuario
  python3 scripts/limpiar_pruebas.py --email test@x.com --borrar
  python3 scripts/limpiar_pruebas.py --todos --borrar     # limpieza total (conserva cuentas)
  ... añade --incluir-usuarios para borrar tambien las cuentas
"""
import argparse
import os
import sys

# ── EL PLAN DE BORRADO: (tabla, filtro SQL) en orden hijos -> padres ──
# {U} = lista de user_ids. SQL identico para Postgres y SQLite (testeado en ambos caminos).
PLAN = [
    ("abonos",                "cuenta_id IN (SELECT id FROM cuentas_cobro WHERE user_id IN ({U}))"),
    ("mensajes_soporte",      "ticket_id IN (SELECT id FROM tickets_soporte WHERE user_id IN ({U}))"),
    ("interacciones_cliente", "proyecto_id IN (SELECT id FROM proyectos WHERE user_id IN ({U}))"),
    ("eventos_share",         "proyecto_id IN (SELECT id FROM proyectos WHERE user_id IN ({U}))"),
    ("encuestas",             "proyecto_id IN (SELECT id FROM proyectos WHERE user_id IN ({U}))"),
    ("gastos",                "proyecto_id IN (SELECT id FROM proyectos WHERE user_id IN ({U}))"),
    ("otrosies",              "proyecto_id IN (SELECT id FROM proyectos WHERE user_id IN ({U}))"),
    ("avances",               "proyecto_id IN (SELECT id FROM proyectos WHERE user_id IN ({U}))"),
    ("cuentas_cobro",         "user_id IN ({U})"),
    ("notificaciones",        "user_id IN ({U})"),
    ("precios_proveedor",     "user_id IN ({U})"),
    ("proveedores",           "user_id IN ({U})"),
    ("apus_usuario",          "user_id IN ({U})"),
    ("pagos_wompi",           "user_id IN ({U})"),
    ("solicitudes_pro",       "user_id IN ({U})"),
    ("tickets_soporte",       "user_id IN ({U})"),
    ("clientes",              "user_id IN ({U})"),
    ("proyectos",             "user_id IN ({U})"),
]
PLAN_USUARIOS = ("usuarios", "id IN ({U})")


def construir_sentencias(user_ids, incluir_usuarios=False):
    """Genera [(tabla, SELECT-count-sql, DELETE-sql)] con los ids embebidos (enteros, seguros)."""
    ids = ",".join(str(int(u)) for u in user_ids)  # int() = inmune a inyeccion
    plan = PLAN + ([PLAN_USUARIOS] if incluir_usuarios else [])
    out = []
    for tabla, filtro in plan:
        w = filtro.replace("{U}", ids)
        out.append((tabla, f"SELECT COUNT(*) FROM {tabla} WHERE {w}",
                    f"DELETE FROM {tabla} WHERE {w}"))
    return out


def main():
    ap = argparse.ArgumentParser(description="Limpieza de datos de prueba")
    ap.add_argument("--email", action="append", help="email del usuario a limpiar (repetible)")
    ap.add_argument("--todos", action="store_true", help="limpiar TODOS los usuarios")
    ap.add_argument("--borrar", action="store_true", help="ejecutar de verdad (sin esto: dry-run)")
    ap.add_argument("--incluir-usuarios", action="store_true", help="borrar tambien las cuentas")
    args = ap.parse_args()

    url = os.environ.get("DATABASE_URL", "")
    if not url:
        sys.exit("Falta DATABASE_URL (exporta la misma de Vercel/Neon)")
    url = url.replace("postgres://", "postgresql://", 1)

    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        sys.exit("pip install sqlalchemy psycopg2-binary (usa el venv del proyecto)")

    eng = create_engine(url)
    with eng.connect() as cx:
        if args.email:
            marcas = ",".join(f":e{i}" for i in range(len(args.email)))
            rows = cx.execute(text(f"SELECT id, email FROM usuarios WHERE email IN ({marcas})"),
                              {f"e{i}": e for i, e in enumerate(args.email)}).fetchall()
        elif args.todos:
            rows = cx.execute(text("SELECT id, email FROM usuarios")).fetchall()
        else:
            rows = cx.execute(text("SELECT id, email FROM usuarios")).fetchall()
            print(f"MODO VISTA: {len(rows)} usuario(s) en la base:")
            for r in rows:
                print(f"   · {r[1]} (id {r[0]})")
            print("\nElige: --email alguien@x.com  (o --todos)  · añade --borrar para ejecutar")
            return

        if not rows:
            sys.exit("No se encontro ningun usuario con ese email")
        user_ids = [r[0] for r in rows]
        print(f"{'🔥 BORRANDO' if args.borrar else '👀 DRY-RUN (nada se toca)'} — "
              f"{len(user_ids)} usuario(s): {', '.join(r[1] for r in rows)}\n")

        sentencias = construir_sentencias(user_ids, args.incluir_usuarios)
        total = 0
        for tabla, sql_count, sql_delete in sentencias:
            try:
                n = cx.execute(text(sql_count)).scalar() or 0
            except Exception as e:
                print(f"   {tabla:24} (tabla no existe aun — se omite)")
                continue
            total += n
            print(f"   {tabla:24} {n:>6} fila(s)")
            if args.borrar and n:
                cx.execute(text(sql_delete))
        if args.borrar:
            cx.commit()
            print(f"\n✅ LIMPIEZA HECHA: {total} filas eliminadas. "
                  f"{'Cuentas de usuario incluidas.' if args.incluir_usuarios else 'Las cuentas de usuario se conservaron — inicia sesion normal.'}")
        else:
            print(f"\n👀 Se borrarian {total} filas. Ejecuta con --borrar cuando estes listo "
                  f"(y descarga el respaldo primero).")


if __name__ == "__main__":
    main()
