#!/usr/bin/env python3
"""
Atajo de linea de comandos para capturar un flujo. (Para el menu: python3 menu.py)

Uso:
    python3 capturar.py [url] [--filtro dominio] [--salida archivo.json]
"""

import argparse
import core


def main():
    ap = argparse.ArgumentParser(description="Capturador de peticiones web")
    ap.add_argument("url", nargs="?", default="about:blank",
                    help="URL inicial (opcional; sin ella abre en blanco)")
    ap.add_argument("--filtro", help="guardar solo URLs que contengan esto")
    ap.add_argument("--salida", default="capturas.json")
    args = ap.parse_args()

    print("Abriendo Chromium... navega tu flujo y presiona ENTER al terminar.")
    data = core.capturar_flujo(url=args.url, filtro=args.filtro)
    ruta = core.guardar(data, args.salida)
    print(f"\n  Peticiones: {len(data['peticiones'])} | Cookies: {len(data['cookies'])}")
    print(f"  Archivo: {ruta}")
    print("  Ahora:  python3 snippet.py   |   python3 snippet.py <n>")


if __name__ == "__main__":
    main()
