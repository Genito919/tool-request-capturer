#!/usr/bin/env python3
"""
Menu interactivo del capturador de peticiones.

    python3 menu.py

Opciones: capturar un flujo, ver lo capturado, generar curl/Python, buscar.
"""

import core

# --- colores ANSI ---
C = dict(reset="\033[0m", bold="\033[1m", dim="\033[2m", cyan="\033[36m",
         green="\033[32m", yellow="\033[33m", red="\033[31m", blue="\033[34m")


def c(txt, color):
    return f"{C[color]}{txt}{C['reset']}"


def cabecera():
    print("\n" + c("=" * 54, "cyan"))
    print(c("  CAPTURADOR DE PETICIONES", "bold") + c("  ·  request-capturer", "dim"))
    print(c("=" * 54, "cyan"))


def pausa():
    input(c("\n  (ENTER para volver al menu) ", "dim"))


def op_capturar():
    url = input(c("\n  URL inicial", "cyan") + " (ENTER = abrir en blanco): ").strip() or "about:blank"
    filtro = input(c("  Filtro por dominio", "cyan") + " (ENTER = todo): ").strip() or None
    print(c("\n  Abriendo navegador... navega tu flujo y vuelve aqui.", "yellow"))
    data = core.capturar_flujo(url=url, filtro=filtro)
    ruta = core.guardar(data)
    n = len(data["peticiones"])
    color = "green" if n else "red"
    print(c(f"\n  {'✓' if n else '✗'} {n} peticiones capturadas", color)
          + c(f"  ({len(data['cookies'])} cookies)", "dim"))
    if n == 0:
        print(c("\n  0 capturadas. Posibles causas:", "yellow"))
        print(c("   - Filtro muy especifico: usa solo el dominio (ej. sitio.com), no la URL entera.", "dim"))
        print(c("   - La accion fue una descarga/navegacion directa (no XHR/fetch): eso no se captura.", "dim"))
        print(c("   - Prueba SIN filtro y haz una accion que cargue datos (buscar, filtrar, listar).", "dim"))
    print(c(f"  Guardado en {ruta.name}", "dim"))
    pausa()


def _cargar_o_avisar():
    try:
        return core.cargar()
    except FileNotFoundError:
        print(c("\n  No hay capturas todavia. Usa la opcion 1 primero.", "red"))
        pausa()
        return None, None


def op_listar():
    peticiones, _ = _cargar_o_avisar()
    if peticiones is None:
        return
    print(c(f"\n  {len(peticiones)} peticiones:\n", "bold"))
    for i, p in enumerate(peticiones):
        url = p.get("url") or ""
        url = url if len(url) <= 78 else url[:75] + "..."
        met = p.get("method", "?")
        col = "green" if str(p.get("status", "")).startswith("2") else "yellow"
        print(f"  {c(f'[{i:3}]', 'dim')} {c(f'{met:5}', 'blue')} {c(str(p.get('status','')), col):>3}  {url}")
    pausa()


def op_generar():
    peticiones, cookies = _cargar_o_avisar()
    if peticiones is None:
        return
    try:
        i = int(input(c("\n  Numero de peticion: ", "cyan")).strip())
        p = peticiones[i]
    except (ValueError, IndexError):
        print(c("  Numero invalido.", "red")); pausa(); return
    print(c(f"\n  #{i}: {p.get('method')} {p.get('url')}", "bold"))
    print(c("\n  ----- curl -----", "cyan"))
    print(core.gen_curl(p, cookies))
    print(c("\n  ----- Python -----", "cyan"))
    print(core.gen_python(p, cookies))
    if input(c("\n  Guardar el Python en un archivo .py? (s/N): ", "yellow")).strip().lower() == "s":
        nombre = input(c("  Nombre del archivo: ", "cyan")).strip() or "peticion.py"
        (core.BASE / nombre).write_text(core.gen_python(p, cookies) + "\n")
        print(c(f"  ✓ guardado {nombre}", "green"))
    pausa()


def op_buscar():
    peticiones, _ = _cargar_o_avisar()
    if peticiones is None:
        return
    texto = input(c("\n  Buscar en URL: ", "cyan")).strip()
    res = core.buscar(peticiones, texto)
    print(c(f"\n  {len(res)} coincidencias:\n", "bold"))
    for i, p in res:
        print(f"  {c(f'[{i:3}]', 'dim')} {c(p.get('method','?'), 'blue')}  {(p.get('url') or '')[:80]}")
    pausa()


def main():
    acciones = {"1": op_capturar, "2": op_listar, "3": op_generar, "4": op_buscar}
    while True:
        cabecera()
        print(f"""
  {c('1', 'green')}  Capturar un flujo nuevo
  {c('2', 'green')}  Ver peticiones capturadas
  {c('3', 'green')}  Generar codigo (curl + Python) de una
  {c('4', 'green')}  Buscar peticion por texto
  {c('5', 'green')}  Salir
""")
        op = input(c("  Opcion: ", "cyan")).strip()
        if op == "5":
            print(c("\n  Hasta la proxima.\n", "dim")); break
        accion = acciones.get(op)
        if accion:
            accion()
        else:
            print(c("  Opcion invalida.", "red"))


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print(c("\n  Saliendo.\n", "dim"))
