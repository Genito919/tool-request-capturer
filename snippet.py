#!/usr/bin/env python3
"""
Atajo de linea de comandos para generar curl + Python de una peticion capturada.

Uso:
    python3 snippet.py            # lista las peticiones
    python3 snippet.py 12         # genera curl + Python de la #12
"""

import argparse
import core


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("indice", nargs="?", type=int)
    ap.add_argument("--archivo", default="capturas.json")
    args = ap.parse_args()

    try:
        peticiones, cookies = core.cargar(args.archivo)
    except FileNotFoundError:
        print(f"No existe {args.archivo}. Corre primero capturar.py (o menu.py)."); return

    if args.indice is None:
        print(f"{len(peticiones)} peticiones capturadas:\n")
        for i, p in enumerate(peticiones):
            url = p.get("url") or ""
            print(f"  [{i:3}] {p.get('method','?'):5} {str(p.get('status','')):3}  {url[:88]}")
        print("\n  -> python3 snippet.py <n>")
        return

    if not (0 <= args.indice < len(peticiones)):
        print(f"indice fuera de rango (0..{len(peticiones)-1})"); return
    p = peticiones[args.indice]
    print("=" * 64)
    print(f"  Peticion #{args.indice}: {p.get('method')} {p.get('url')}")
    print("=" * 64)
    print("\n----- curl -----\n")
    print(core.gen_curl(p, cookies))
    print("\n\n----- Python (requests) -----\n")
    print(core.gen_python(p, cookies))


if __name__ == "__main__":
    main()
