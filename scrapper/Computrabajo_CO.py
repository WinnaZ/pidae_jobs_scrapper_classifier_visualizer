#!/usr/bin/env python3
"""
Computrabajo Colombia Scraper
https://co.computrabajo.com/
Paginación: ?p=N
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


import tempfile
import time
import json
import shutil
import os
from datetime import date
import hashlib
import re
import argparse
import builtins
import signal
import sys

# Colores ANSI - Amarillo para Colombia
YELLOW = '\033[0;33m'
RESET = '\033[0m'

_original_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    colored_args = [f"{YELLOW}{arg}{RESET}" if isinstance(arg, str) else arg for arg in args]
    _original_print(*colored_args, **kwargs)
builtins.print = print

parser = argparse.ArgumentParser(description='Script de scraping para Computrabajo Colombia')
parser.add_argument('--debug', action='store_true', help='Activar mensajes de debug')
parser.add_argument('--start-from', type=str, help='Iniciar desde una categoría específica')
args = parser.parse_args()

def debug_print(*mensaje, **kwargs):
    if args.debug:
        _original_print(f"{YELLOW}{' '.join(map(str, mensaje))}{RESET}", flush=True, **kwargs)

# Variables globales
driver = None
total_jobs_scraped = 0
jobs_this_session = 0
EMPLEOS = []
HASHES_GLOBALES = set()
current_area = ""

def signal_handler(sig, frame):
    print(f"\n\nInterrupción detectada (CTRL+C)")
    if EMPLEOS:
        print(f"Guardando {len(EMPLEOS)} empleos pendientes...")
        guardar_datos_incremental(EMPLEOS, current_area or "partial")
    if driver:
        try:
            driver.quit()
        except:
            pass
    print(f"Total empleos guardados: {total_jobs_scraped}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def guardar_datos_incremental(empleos, area, archivo_base="output_jobs/Computrabajo_CO"):
    os.makedirs("output_jobs", exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d")
    nombre_archivo = f"{archivo_base}_{area}_{timestamp}.json"
    
    empleos_existentes = []
    if os.path.exists(nombre_archivo):
        try:
            with open(nombre_archivo, 'r', encoding='utf-8') as f:
                empleos_existentes = json.load(f)
            print(f"Cargados {len(empleos_existentes)} empleos existentes")
        except:
            pass
    
    todos_empleos = empleos_existentes + empleos
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        json.dump(todos_empleos, f, ensure_ascii=False, indent=4)
    
    print(f"Guardado: {nombre_archivo} ({len(empleos)} nuevos, {len(todos_empleos)} total)")
    return nombre_archivo

def calcular_hash(texto):
    if not isinstance(texto, str):
        return None
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def verificar_pagina_existe(driver, url):
    page_num = re.search(r'p=(\d+)', url)
    page_num = int(page_num.group(1)) if page_num else 1
    
    try:
        try:
            driver.get(url)
        except:
            driver.execute_script("window.stop();")
        
        page_source = driver.page_source.lower()
        if 'no se encontraron' in page_source or 'no hay ofertas' in page_source:
            print(f"Página {page_num}: 0 empleos")
            return False
        
        links = driver.find_elements(By.CSS_SELECTOR, "a.js-o-link")
        valid = [l for l in links if '/ofertas-de-trabajo/' in (l.get_attribute("href") or "")]
        
        if len(valid) > 0:
            print(f"Página {page_num}: {len(valid)} empleos")
            return True
        else:
            print(f"Página {page_num}: 0 empleos")
            return False
            
    except:
        print(f"Página {page_num}: Error")
        return False

def obtener_total_paginas(driver, categoria_slug):
    url_base = f"https://co.computrabajo.com/trabajo-de-{categoria_slug}"
    print(f"\nAnalizando: {categoria_slug}")
    
    if not verificar_pagina_existe(driver, f"{url_base}?p=1"):
        return 1

    # Saltos de 50
    ultima = 1
    pagina = 50
    while verificar_pagina_existe(driver, f"{url_base}?p={pagina}"):
        ultima = pagina
        pagina += 50
       
    
    # Búsqueda binaria
    left, right = ultima, pagina
    while left < right - 1:
        mid = (left + right) // 2
        if verificar_pagina_existe(driver, f"{url_base}?p={mid}"):
            ultima = mid
            left = mid
        else:
            right = mid

    print(f"Total páginas: {ultima}")
    return ultima

# Categorías Colombia
areas = [
    "servicio-al-cliente",
    "auxiliar-de-bodega", 
    "auxiliar-de-cocina",
    "auxiliar-administrativo",
    "auxiliar-logistico",
    "asesor-comercial",
    "call-center",
    "auxiliar-de-enfermeria",
    "asesor-de-ventas",
    "analista",
    "conductor",
    "atencion-a-clientes",
    "auxiliar-contable",
    "operario",
    "mercaderista",
    "auxiliar",
    "ejecutivo-comercial",
    "coordinador",
    "asesores-comerciales",
]

# Setup
temp_profile_dir = tempfile.mkdtemp()
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f"--user-data-dir={temp_profile_dir}")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs)
chrome_options.page_load_strategy = 'eager'

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.set_page_load_timeout(5)
driver.implicitly_wait(1)

os.makedirs("output_jobs", exist_ok=True)

print("="*60)
print("COMPUTRABAJO COLOMBIA SCRAPER")
print("="*60)

# Cargar hashes
for area in areas:
    archivo = f"output_jobs/Computrabajo_CO_{area}_{date.today().strftime('%Y%m%d')}.json"
    if os.path.exists(archivo):
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                for e in json.load(f):
                    h = e.get("hash Descripcion")
                    if h:
                        HASHES_GLOBALES.add(h)
        except:
            pass
print(f"Hashes existentes: {len(HASHES_GLOBALES)}")

# Start index
start_idx = 0
if args.start_from:
    for i, a in enumerate(areas):
        if a == args.start_from:
            start_idx = i
            break

try:
    for area_idx, area in enumerate(areas[start_idx:], start_idx):
        current_area = area
        
        print(f"\n{'='*80}")
        print(f"ÁREA {area_idx + 1}/{len(areas)}: {area}")
        print(f"{'='*80}")
        
        total_pags = obtener_total_paginas(driver, area)
        area_jobs = 0
        
        for pag in range(1, total_pags + 1):
            print(f"\nPágina {pag}/{total_pags}")
            url = f"https://co.computrabajo.com/trabajo-de-{area}?p={pag}"
            
            try:
                try:
                    driver.get(url)
                    WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "a.js-o-link")))

                except:
                    driver.execute_script("window.stop();")

                links = driver.find_elements(By.CSS_SELECTOR, "a.js-o-link")
                urls = list(set([l.get_attribute("href") for l in links if '/ofertas-de-trabajo/' in (l.get_attribute("href") or "")]))
                
                print(f"{len(urls)} empleos:")

                for i, url_emp in enumerate(urls):
                    try:
                        try:
                            driver.get(url_emp)
                            WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "a.js-o-link")))
                            driver.delete_all_cookies()


                        except:
                            driver.execute_script("window.stop();")
                        
                        # Título
                        try:
                            titulo = driver.find_element(By.TAG_NAME, "h1").text.strip()
                            print(f"  {i} - {titulo[:50]}")
                        except:
                            titulo = "Sin título"
                            print(f"  {i} - [Sin título]")
                        
                        # Descripción
                        try:
                            body = driver.find_element(By.TAG_NAME, "body")
                            descripcion = body.text[:3000]
                        except:
                            descripcion = titulo
                        
                        # Empresa/Ubicación
                        empresa = "N/A"
                        ubicacion = "Colombia"
                        try:
                            p = driver.find_element(By.CSS_SELECTOR, "p.fs16")
                            txt = p.text.strip()
                            if '-' in txt:
                                partes = txt.split('-')
                                empresa = partes[0].strip()
                                ubicacion = partes[1].strip()
                        except:
                            pass
                        
                        # Hash
                        hash_content = descripcion + "|" + ubicacion + "|" + empresa
                        hash_emp = calcular_hash(hash_content)
                        
                        if hash_emp in HASHES_GLOBALES:
                            print(f"    ^ [DUP]")
                            continue
                        
                        EMPLEOS.append({
                            "Id Interno": f"CO-{area}-{pag}-{i+1}",
                            "titulo": titulo,
                            "descripcion": descripcion,
                            "Empresa": empresa,
                            "Fuente": "Computrabajo Colombia",
                            "Tipo Portal": "Tradicional",
                            "url": url_emp,
                            "Pais": "Colombia",
                            "ubicacion": ubicacion,
                            "Categoria Portal": area,
                            "Subcategoria Portal": "",
                            "Categorria": "",
                            "Subcategoria": "",
                            "hash Descripcion": hash_emp,
                            "fecha": date.today().strftime("%d/%m/%Y")
                        })
                        
                        HASHES_GLOBALES.add(hash_emp)
                        jobs_this_session += 1
                        total_jobs_scraped += 1
                        area_jobs += 1
                        
                    except Exception as e:
                        debug_print(f"Error: {e}")
                        continue
                        
            except Exception as e:
                debug_print(f"Error página: {e}")
                continue
        
        # Guardar
        print(f"\n{'='*60}")
        print(f"'{area}' completada: {area_jobs} empleos")
        print(f"Total: {total_jobs_scraped}")
        print(f"{'='*60}")
        
        if EMPLEOS:
            guardar_datos_incremental(EMPLEOS, area)
            EMPLEOS = []

except KeyboardInterrupt:
    print(f"\nInterrumpido")
    if EMPLEOS:
        guardar_datos_incremental(EMPLEOS, f"{current_area}_partial")

finally:
    driver.quit()
    shutil.rmtree(temp_profile_dir, ignore_errors=True)

print(f"\n{'='*60}")
print(f"COMPLETADO - Jobs: {total_jobs_scraped}")
print(f"{'='*60}")