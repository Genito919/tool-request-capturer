#!/usr/bin/env python3
"""
Motor del capturador de peticiones. Funciones reutilizables que usan tanto el
menu (menu.py) como los atajos de linea de comandos (capturar.py / snippet.py).

Importable:
    from core import capturar_flujo, cargar, gen_curl, gen_python, buscar
"""

import json
import os
import pprint
import shlex
import shutil
import time
from pathlib import Path
from urllib.parse import urlsplit

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

BASE = Path(__file__).resolve().parent


def _encontrar_navegador():
    """Detecta Chrome o Chromium en cualquier maquina (Linux/Mac/Win)."""
    env = os.environ.get("CAPTURADOR_BROWSER")   # override manual si hace falta
    if env and Path(env).exists():
        return env
    # buscar en el PATH
    for nombre in ("chromium", "chromium-browser", "google-chrome",
                   "google-chrome-stable", "chrome"):
        ruta = shutil.which(nombre)
        if ruta:
            return ruta
    # rutas comunes por si no esta en el PATH
    comunes = [
        "/usr/bin/chromium", "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/snap/bin/chromium",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    for r in comunes:
        if Path(r).exists():
            return r
    return None   # None -> Selenium usa el Chrome por defecto del sistema

# Gancho JS que se inyecta antes de cada pagina: envuelve XHR y fetch para
# registrar metodo, url, headers, body, status y respuesta de cada peticion.
HOOK = r"""
(function(){
  if (window.__CAP_INSTALLED) return;
  window.__CAP_INSTALLED = true;
  window.__CAP = window.__CAP || [];
  const MAX = 500000;
  const oOpen = XMLHttpRequest.prototype.open;
  const oSend = XMLHttpRequest.prototype.send;
  const oSet  = XMLHttpRequest.prototype.setRequestHeader;
  XMLHttpRequest.prototype.open = function(m,u){ this.__m=m; this.__u=u; this.__h={}; return oOpen.apply(this,arguments); };
  XMLHttpRequest.prototype.setRequestHeader = function(k,v){ try{this.__h[k]=v;}catch(e){} return oSet.apply(this,arguments); };
  XMLHttpRequest.prototype.send = function(body){
    const self=this;
    this.addEventListener('load', function(){
      let resp=''; try{ resp=(self.responseText||'').slice(0,MAX);}catch(e){}
      window.__CAP.push({via:'xhr',method:self.__m,url:self.__u,reqHeaders:self.__h||{},
        reqBody: body!=null ? (''+body).slice(0,MAX):null, status:self.status, resp:resp});
    });
    return oSend.apply(this,arguments);
  };
  const oFetch = window.fetch;
  window.fetch = function(input, init){
    const url=(typeof input==='string')?input:(input&&input.url);
    const method=(init&&init.method)||(input&&input.method)||'GET';
    let headers={};
    try{ const h=(init&&init.headers)||(input&&input.headers);
      if(h){ if(h.forEach) h.forEach((v,k)=>headers[k]=v); else Object.assign(headers,h);} }catch(e){}
    const reqBody=(init&&init.body!=null)?(''+init.body).slice(0,MAX):null;
    return oFetch.apply(this,arguments).then(r=>{
      r.clone().text().then(t=>{ window.__CAP.push({via:'fetch',method:method,url:url,reqHeaders:headers,
        reqBody:reqBody,status:r.status,resp:(t||'').slice(0,MAX)});}).catch(()=>{});
      return r;
    });
  };
})();
"""


def nuevo_driver(headless=False, perfil=None):
    o = Options()
    navegador = _encontrar_navegador()
    if navegador:
        o.binary_location = navegador   # si es None, Selenium usa el Chrome por defecto
    if headless:
        o.add_argument("--headless=new")
        o.add_argument("--no-sandbox")
    else:
        o.add_argument("--start-maximized")
    o.add_argument(f"--user-data-dir={perfil or (BASE / 'perfil_chrome')}")
    d = webdriver.Chrome(options=o)
    d.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": HOOK})
    return d


def _norm_filtro(filtro):
    """Si te pasan una URL completa como filtro, extrae solo el dominio.
    Asi 'https://sitio.com/en/home/' -> 'sitio.com' (evita filtrar de mas)."""
    if not filtro:
        return None
    filtro = filtro.strip()
    if "://" in filtro:
        return urlsplit(filtro).netloc or filtro
    return filtro.split("/")[0]  # 'sitio.com/ruta' -> 'sitio.com'


def capturar_flujo(url="about:blank", filtro=None, espera=None, headless=False):
    """Captura las peticiones de un flujo.

    espera=None  -> modo interactivo: espera a que presiones ENTER (para humanos).
    espera=<seg> -> captura durante N segundos y devuelve (para scripting/Claude).

    Devuelve dict {"cookies": [...], "peticiones": [...]}.
    """
    d = nuevo_driver(headless=headless)
    try:
        d.get(url)
    except Exception:
        print(f"  (no pude abrir {url!r} — navega tu mismo)")

    if espera is None:
        input("   >>> Navega tu flujo y presiona ENTER para terminar... ")
    else:
        time.sleep(espera)

    try:
        peticiones = d.execute_script("return window.__CAP || [];") or []
        cookies = d.get_cookies()
    except Exception:
        peticiones, cookies = [], []
    d.quit()

    dominio = _norm_filtro(filtro)
    if dominio:
        peticiones = [p for p in peticiones if dominio in (p.get("url") or "")]
    return {"cookies": cookies, "peticiones": peticiones}


def guardar(data, archivo="capturas.json"):
    ruta = BASE / archivo
    ruta.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return ruta


def cargar(archivo="capturas.json"):
    ruta = BASE / archivo
    data = json.loads(ruta.read_text())
    return data.get("peticiones", []), data.get("cookies", [])


def buscar(peticiones, texto):
    """Devuelve [(indice, peticion)] cuya URL contenga 'texto' (util para hallar la buena)."""
    t = texto.lower()
    return [(i, p) for i, p in enumerate(peticiones) if t in (p.get("url") or "").lower()]


# ---------- generacion de codigo ----------

def cookies_dict(cookies):
    return {c["name"]: c["value"] for c in cookies if "name" in c}


def py_literal(obj):
    return pprint.pformat(obj, indent=4, sort_dicts=False, width=88)


def gen_curl(p, cookies):
    partes = [f"curl -X {p.get('method','GET')} {shlex.quote(p.get('url',''))}"]
    for k, v in (p.get("reqHeaders") or {}).items():
        if k.lower() in ("content-length", "host"):
            continue
        partes.append(f"  -H {shlex.quote(f'{k}: {v}')}")
    ck = cookies_dict(cookies)
    if ck:
        partes.append(f"  -b {shlex.quote('; '.join(f'{k}={v}' for k, v in ck.items()))}")
    if p.get("reqBody"):
        partes.append(f"  --data {shlex.quote(p['reqBody'])}")
    return " \\\n".join(partes)


def gen_python(p, cookies):
    headers = {k: v for k, v in (p.get("reqHeaders") or {}).items()
               if k.lower() not in ("content-length", "host")}
    ck = cookies_dict(cookies)
    body = p.get("reqBody")
    out = ["import requests", "", f"url = {p.get('url','')!r}", f"headers = {py_literal(headers)}"]
    if ck:
        out.append(f"cookies = {py_literal(ck)}")
    data_kw = ""
    if body:
        try:
            out.append(f"payload = {py_literal(json.loads(body))}")
            data_kw = ", json=payload"
        except ValueError:
            out.append(f"payload = {body!r}")
            data_kw = ", data=payload"
    cookie_kw = ", cookies=cookies" if ck else ""
    out += ["", f"r = requests.{(p.get('method') or 'GET').lower()}(url, headers=headers{cookie_kw}{data_kw})",
            "print(r.status_code)", "print(r.text[:500])"]
    return "\n".join(out)
