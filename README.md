# request-capturer

Herramienta para acelerar la creación de automatizaciones web.

Muchas tareas repetitivas en sistemas web siguen el mismo patrón: entrar a un módulo, aplicar filtros, presionar "Generar" y obtener un resultado (una tabla, un reporte, un archivo). Por debajo, esa acción es **una sola petición HTTP**. Si la identificas, puedes replicarla directamente y saltarte todos los clics — pasando de minutos de navegación manual a una ejecución instantánea.

`request-capturer` graba las peticiones de un flujo mientras lo navegas a mano, y genera el código (`curl` y Python) para replicar cualquiera de ellas.

## Cómo funciona

1. **Capturar** — Abre Chromium; te logueas y haces el flujo manual una vez. La herramienta intercepta cada petición XHR/fetch (método, URL, headers, cuerpo, respuesta) y guarda también las cookies de sesión.
2. **Identificar** — Revisas la lista de peticiones capturadas y ubicas la que hace la acción que te interesa (por ejemplo, la que genera la tabla).
3. **Generar** — La herramienta produce el `curl` y el snippet de Python listos para replicar esa petición, con sus headers, cookies y cuerpo.
4. **Automatizar** — Tomas ese snippet como base de tu script.

## Instalación

```bash
pip install -r requirements.txt
```
Requiere Chromium (`/usr/bin/chromium`). Selenium descarga el driver automáticamente.

## Uso

### Menú interactivo (recomendado)
```bash
python3 menu.py
```
Menú con opciones para capturar, listar, generar código y buscar peticiones.

### Atajos de línea de comandos
```bash
python3 capturar.py https://mi-sistema.com/login --filtro mi-sistema.com   # capturar
python3 snippet.py            # listar peticiones capturadas
python3 snippet.py 12         # generar curl + Python de la #12
```

`--filtro` (opcional) guarda solo las peticiones cuya URL contenga ese texto, para separar señal de ruido (analytics, CDNs, etc.).

### Como módulo (scripting)
```python
import core
data = core.capturar_flujo("https://sistema.com", filtro="sistema.com")  # ENTER para terminar
# o captura automática por N segundos (sin interacción):
data = core.capturar_flujo("https://sistema.com/reporte", espera=8, headless=True)

buenos = core.buscar(data["peticiones"], "reportes/generar")
print(core.gen_python(buenos[0][1], data["cookies"]))
```

## Ejemplo de salida

```
----- Python (requests) -----

import requests

url = 'https://mi-sistema.com/api/reportes/generar'
headers = {'content-type': 'application/json'}
cookies = {'session': 'abc123'}
payload = {'fechaInicio': '2026-01-01', 'fechaFin': '2026-01-31', 'omitidos': True}

r = requests.post(url, headers=headers, cookies=cookies, json=payload)
print(r.status_code)
print(r.text[:500])
```

A partir de ahí, cambias los filtros del `payload`, lo metes en un bucle, y automatizas.

## Archivos

- `core.py` — el motor: captura, búsqueda y generación de código (importable).
- `menu.py` — menú interactivo en terminal.
- `capturar.py` — atajo para capturar un flujo a `capturas.json`.
- `snippet.py` — atajo para generar `curl` / Python de una petición.

## Notas

- La captura ocurre a nivel del navegador, así que funciona con la sesión ya autenticada (no hay que reimplementar el login).
- Las cookies y tokens capturados son de tu sesión: trátalos como credenciales.
- Pensada para automatizar sistemas a los que tienes acceso legítimo.
