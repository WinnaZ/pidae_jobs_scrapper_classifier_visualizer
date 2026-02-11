#!/usr/bin/env python3
"""
Indeed Argentina Scraper - JSON Extraction Method
Usa selenium-stealth para evitar detección de Cloudflare
Extrae datos de empleos desde el JSON embebido en la página
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
import json
import os
import re
import time
import random
import hashlib
from datetime import date
import sys
import argparse
import builtins
import signal
import tempfile
import shutil

# Colores ANSI - Naranja/Amarillo para Indeed
YELLOW = '\033[1;33m'
RESET = '\033[0m'

_original_print = builtins.print
def print(*args, **kwargs):
    colored_args = [f"{YELLOW}{arg}{RESET}" if isinstance(arg, str) else arg for arg in args]
    _original_print(*colored_args, **kwargs)
builtins.print = print

parser = argparse.ArgumentParser(description='Script de scraping para Indeed Argentina')
parser.add_argument('--debug', action='store_true', help='Activar mensajes de debug')
parser.add_argument('--start-from', type=str, help='Iniciar desde una categoría específica')
args = parser.parse_args()

def debug_print(*mensaje, **kwargs):
    if args.debug:
        _original_print(f"{YELLOW}[DEBUG] {' '.join(map(str, mensaje))}{RESET}", **kwargs)

# Categorías de búsqueda
CATEGORIAS = [
    "desarrollador",
    "programador", 
    "sistemas",
    "administrativo",
    "ventas",
    "marketing",
    "contador",
    "recursos humanos",
    "diseñador",
    "ingeniero",
    "analista",
    "atención al cliente",
    "logística",
    "producción",
    "mantenimiento",
    "recepcionista",
    "vendedor",
    "data analyst",
    "project manager",
    "community manager"
]

# Variables globales
driver = None
temp_profile_dir = None
total_jobs_scraped = 0
jobs_this_session = 0
EMPLEOS = []
HASHES_GLOBALES = set()
current_categoria = ""
current_categoria_index = 0
categorias_completed = set()

def signal_handler(sig, frame):
    print(f"\n\nInterrupción detectada (CTRL+C)")
    print("Guardando datos recolectados...")
    
    if EMPLEOS:
        guardar_datos_incremental(EMPLEOS, current_categoria)
    
    if driver:
        try:
            driver.quit()
        except:
            pass
    
    if temp_profile_dir:
        shutil.rmtree(temp_profile_dir, ignore_errors=True)
    
    print(f"Total empleos guardados: {total_jobs_scraped}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def calcular_hash(texto):
    if not isinstance(texto, str):
        return None
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def guardar_datos_incremental(empleos, categoria, archivo_base="output_jobs/Indeed"):
    os.makedirs("output_jobs", exist_ok=True)
    
    # Limpiar nombre de categoría para archivo
    categoria_limpia = categoria.replace(" ", "_").replace("/", "-")
    timestamp = date.today().strftime("%Y%m%d")
    nombre_archivo = f"{archivo_base}_{categoria_limpia}_{timestamp}.json"
    
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
    
    print(f"\nGuardado: {nombre_archivo}")
    print(f"  - Empleos nuevos: {len(empleos)}")
    print(f"  - Total en archivo: {len(todos_empleos)}")
    return nombre_archivo

def create_driver():
    """Crea driver con selenium-stealth para evitar detección"""
    global temp_profile_dir
    
    temp_profile_dir = tempfile.mkdtemp()
    
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={temp_profile_dir}")
    
    # Configuración anti-detección
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--lang=es-AR')
    
    # Excluir switches de automatización
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Preferencias
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    options.add_experimental_option("prefs", prefs)
    
    # Crear driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Aplicar stealth
    stealth(driver,
        languages=["es-AR", "es", "en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    
    driver.maximize_window()
    return driver

def extraer_jobs_de_json(page_source):
    """
    Extrae los datos de empleos del JSON embebido en la página.
    Indeed almacena los datos en window.mosaic.providerData["mosaic-provider-jobcards"]
    """
    jobs = []
    
    try:
        # Patrón para extraer el JSON de los job cards
        pattern = r'window\.mosaic\.providerData\["mosaic-provider-jobcards"\]\s*=\s*(\{.+?\});'
        match = re.search(pattern, page_source, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)
            
            # Los resultados están en metaData.mosaicProviderJobCardsModel.results
            results = data.get('metaData', {}).get('mosaicProviderJobCardsModel', {}).get('results', [])
            
            debug_print(f"Encontrados {len(results)} empleos en JSON")
            
            for job in results:
                if job.get('jobkey'):
                    jobs.append({
                        'jobkey': job.get('jobkey'),
                        'title': job.get('title') or job.get('displayTitle', ''),
                        'company': job.get('company', ''),
                        'location': job.get('formattedLocation', ''),
                        'snippet': job.get('snippet', ''),
                        'salary': job.get('salarySnippet', {}).get('text', '') if job.get('salarySnippet') else '',
                        'pubDate': job.get('pubDate', ''),
                        'jobTypes': job.get('jobTypes', []),
                    })
            
            return jobs
    except json.JSONDecodeError as e:
        debug_print(f"Error decodificando JSON: {e}")
    except Exception as e:
        debug_print(f"Error extrayendo jobs de JSON: {e}")
    
    # Fallback: intentar otro patrón
    try:
        # Patrón alternativo para Indeed Argentina
        pattern2 = r'window\.mosaic\.providerData\["jobcards-appcast"\]\s*=\s*(\{.+?\});'
        match2 = re.search(pattern2, page_source, re.DOTALL)
        
        if match2:
            json_str = match2.group(1)
            data = json.loads(json_str)
            results = data.get('results', [])
            
            for job in results:
                if job.get('jobkey'):
                    jobs.append({
                        'jobkey': job.get('jobkey'),
                        'title': job.get('title', ''),
                        'company': job.get('company', ''),
                        'location': job.get('formattedLocation', ''),
                        'snippet': job.get('snippet', ''),
                    })
    except:
        pass
    
    return jobs

def extraer_job_detalle(driver, job_url):
    """
    Extrae detalles completos de un empleo individual.
    Usa el endpoint móvil que es más fácil de parsear.
    """
    try:
        driver.get(job_url)
        time.sleep(random.uniform(2, 4))
        
        page_source = driver.page_source
        
        # Buscar el JSON con los datos del empleo
        pattern = r'window\._initialData\s*=\s*(\{.+?\});'
        match = re.search(pattern, page_source, re.DOTALL)
        
        if match:
            json_str = match.group(1)
            data = json.loads(json_str)
            
            job_info = data.get('jobInfoWrapperModel', {}).get('jobInfoModel', {})
            header = job_info.get('jobInfoHeaderModel', {})
            
            return {
                'titulo': header.get('jobTitle', ''),
                'empresa': header.get('companyName', ''),
                'ubicacion': header.get('formattedLocation', ''),
                'descripcion': job_info.get('sanitizedJobDescription', {}).get('content', ''),
                'salario': header.get('salaryText', ''),
            }
    except Exception as e:
        debug_print(f"Error extrayendo detalle: {e}")
    
    return None

def esperar_cloudflare(driver, max_intentos=5):
    """
    Espera a que Cloudflare se resuelva automáticamente.
    undetected-chromedriver generalmente lo bypasea solo.
    Retorna True si se resolvió, False si necesita intervención manual.
    """
    for intento in range(max_intentos):
        page_source = driver.page_source.lower()
        
        # Indicadores de Cloudflare
        cloudflare_indicators = [
            "just a moment",
            "verify you are human",
            "checking your browser",
            "ray id",
            "cloudflare"
        ]
        
        # Verificar si hay Cloudflare
        tiene_cloudflare = any(ind in page_source for ind in cloudflare_indicators)
        
        # Verificar si hay contenido de Indeed (indica que pasamos)
        tiene_indeed = "indeed" in page_source and ("job" in page_source or "empleo" in page_source)
        
        if not tiene_cloudflare or tiene_indeed:
            return True
        
        debug_print(f"Cloudflare detectado, esperando... (intento {intento + 1}/{max_intentos})")
        time.sleep(5)  # Esperar 5 segundos entre intentos
    
    return False

def verificar_pagina_existe(driver, url, page_num):
    """Verifica si una página tiene empleos válidos usando extracción JSON"""
    try:
        driver.get(url)
        time.sleep(random.uniform(3, 5))
        
        # Esperar a que Cloudflare se resuelva automáticamente
        if not esperar_cloudflare(driver):
            print(f"Cloudflare no se resolvió automáticamente en página {page_num}")
            print("Por favor, resuélvelo manualmente en el navegador.")
            input("Presiona Enter cuando hayas terminado...")
        
        page_source = driver.page_source
        
        # Extraer empleos del JSON
        jobs = extraer_jobs_de_json(page_source)
        
        if jobs:
            print(f"Página {page_num}: {len(jobs)} empleos encontrados")
            return True, len(jobs), jobs
        else:
            # Fallback: buscar por selectores tradicionales
            try:
                job_cards = driver.find_elements(By.CSS_SELECTOR, 'div.job_seen_beacon, div.jobsearch-ResultsList > div, .resultContent')
                if job_cards:
                    print(f"Página {page_num}: {len(job_cards)} empleos (selector fallback)")
                    return True, len(job_cards), []
            except:
                pass
            
            print(f"Página {page_num}: 0 empleos encontrados")
            return False, 0, []
            
    except Exception as e:
        debug_print(f"Error verificando página {page_num}: {e}")
        return False, 0, []

def obtener_total_paginas(driver, categoria):
    """Determina el número total de páginas para una categoría"""
    from urllib.parse import quote
    
    categoria_encoded = quote(categoria)
    url_base = f"https://ar.indeed.com/jobs?q={categoria_encoded}&l=Argentina"
    
    print(f"\nAnalizando categoría: {categoria}")
    
    # Verificar primera página
    existe, num_jobs, _ = verificar_pagina_existe(driver, f"{url_base}&start=0", 1)
    if not existe:
        return 0
    
    # Búsqueda binaria para encontrar última página
    # Indeed usa start=0, 10, 20, etc. (10 empleos por página)
    left = 0
    right = 100  # Máximo 1000 empleos (100 páginas)
    ultima_valida = 0
    
    while left <= right:
        mid = (left + right) // 2
        start = mid * 10
        
        existe, _, _ = verificar_pagina_existe(driver, f"{url_base}&start={start}", mid + 1)
        
        if existe:
            ultima_valida = mid
            left = mid + 1
        else:
            right = mid - 1
    
    total_paginas = ultima_valida + 1
    print(f"Total de páginas encontradas: {total_paginas}")
    return total_paginas

def scrape_categoria(driver, categoria, cat_index, total_cats):
    """Scrapea una categoría completa"""
    global total_jobs_scraped, jobs_this_session, EMPLEOS, HASHES_GLOBALES
    
    from urllib.parse import quote
    
    print(f"\n{'='*80}")
    print(f"PROCESANDO CATEGORÍA {cat_index}/{total_cats}: {categoria}")
    print(f"{'='*80}")
    
    categoria_encoded = quote(categoria)
    url_base = f"https://ar.indeed.com/jobs?q={categoria_encoded}&l=Argentina"
    
    total_paginas = obtener_total_paginas(driver, categoria)
    
    if total_paginas == 0:
        print(f"No se encontraron empleos para: {categoria}")
        return 0
    
    print(f"Comenzando extracción de empleos...")
    
    categoria_jobs = 0
    
    for pagina in range(total_paginas):
        start = pagina * 10
        url = f"{url_base}&start={start}"
        
        print(f"\nProcesando página {pagina + 1}/{total_paginas}")
        
        try:
            driver.get(url)
            time.sleep(random.uniform(3, 5))
            
            # Esperar a que Cloudflare se resuelva automáticamente
            if not esperar_cloudflare(driver):
                print("Cloudflare no se resolvió automáticamente.")
                print("Por favor, resuélvelo manualmente en el navegador.")
                input("Presiona Enter cuando hayas terminado...")
            
            page_source = driver.page_source
            
            # Extraer empleos del JSON
            jobs = extraer_jobs_de_json(page_source)
            
            if not jobs:
                debug_print("No se encontraron empleos en JSON, intentando selectores...")
                continue
            
            print(f"Página {pagina + 1}/{total_paginas} - {len(jobs)} empleos encontrados:")
            
            for i, job in enumerate(jobs):
                try:
                    jobkey = job.get('jobkey', '')
                    titulo = job.get('title', 'Título no disponible')
                    empresa = job.get('company', 'Empresa no disponible')
                    ubicacion = job.get('location', 'Argentina')
                    snippet = job.get('snippet', '')
                    
                    # Limpiar HTML del snippet
                    snippet_limpio = re.sub(r'<[^>]+>', '', snippet)
                    
                    # Calcular hash para detectar duplicados
                    hash_empleo = calcular_hash(f"{titulo}{empresa}{snippet_limpio}")
                    
                    if hash_empleo in HASHES_GLOBALES:
                        debug_print(f"  {i+1} - [DUPLICADO] {titulo[:50]}")
                        continue
                    
                    print(f"  {i+1} - {titulo[:60]}")
                    
                    # URL del empleo
                    job_url = f"https://ar.indeed.com/viewjob?jk={jobkey}"
                    
                    EMPLEOS.append({
                        "Id Interno": f"{categoria.replace(' ', '-')}-{pagina+1}-{i+1}",
                        "titulo": titulo,
                        "descripcion": snippet_limpio,
                        "Empresa": empresa,
                        "Fuente": "Indeed",
                        "Tipo Portal": "Tradicional",
                        "url": job_url,
                        "Pais": "Argentina",
                        "ubicacion": ubicacion,
                        "Categoria Portal": categoria,
                        "Subcategoria Portal": "",
                        "Categorria": "",
                        "Subcategoria": "",
                        "hash Descripcion": hash_empleo,
                        "fecha": date.today().strftime("%d/%m/%Y")
                    })
                    
                    HASHES_GLOBALES.add(hash_empleo)
                    total_jobs_scraped += 1
                    jobs_this_session += 1
                    categoria_jobs += 1
                    
                except Exception as e:
                    debug_print(f"Error procesando empleo {i+1}: {e}")
                    continue
            
            # Pausa entre páginas
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            print(f"Error en página {pagina + 1}: {e}")
            continue
    
    # Guardar al finalizar categoría
    print(f"\n{'='*60}")
    print(f"Categoría '{categoria}' completada")
    print(f"Jobs en esta categoría: {categoria_jobs}")
    print(f"Total acumulado: {total_jobs_scraped}")
    print(f"{'='*60}")
    
    if EMPLEOS:
        guardar_datos_incremental(EMPLEOS, categoria)
        EMPLEOS = []
    
    return categoria_jobs

# Main
if __name__ == "__main__":
    print("="*60)
    print("   INDEED ARGENTINA SCRAPER")
    print("   Método: selenium-stealth + JSON extraction")
    print("="*60)
    
    if args.debug:
        print("Modo debug activado")
    
    # Cargar hashes existentes
    print("\nCargando hashes existentes...")
    timestamp = date.today().strftime("%Y%m%d")
    for cat in CATEGORIAS:
        cat_limpia = cat.replace(" ", "_").replace("/", "-")
        archivo = f"output_jobs/Indeed_{cat_limpia}_{timestamp}.json"
        if os.path.exists(archivo):
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    for empleo in json.load(f):
                        h = empleo.get("hash Descripcion")
                        if h:
                            HASHES_GLOBALES.add(h)
            except:
                pass
    print(f"Cargados {len(HASHES_GLOBALES)} hashes existentes")
    
    # Determinar categoría de inicio
    start_index = 0
    if args.start_from:
        for i, cat in enumerate(CATEGORIAS):
            if cat.lower() == args.start_from.lower():
                start_index = i
                print(f"Iniciando desde categoría: {cat}")
                break
    
    categorias_a_procesar = CATEGORIAS[start_index:]
    print(f"\nProcesando {len(categorias_a_procesar)} categorías...")
    
    # Crear driver
    print("\nIniciando navegador...")
    driver = create_driver()
    
    try:
        # Cargar Indeed por primera vez
        print("Cargando Indeed por primera vez...")
        driver.get("https://ar.indeed.com")
        time.sleep(5)
        
        # Esperar a que Cloudflare se resuelva automáticamente
        print("Esperando bypass de Cloudflare (esto puede tomar unos segundos)...")
        if not esperar_cloudflare(driver, max_intentos=10):
            print("\nCloudflare no se resolvió automáticamente.")
            print("Por favor, resuelve el captcha manualmente en el navegador.")
            input("Presiona Enter cuando hayas terminado...")
        else:
            print("Cloudflare bypasseado exitosamente!")
        
        print("Página inicial cargada.\n")
        
        # Procesar categorías
        for idx, categoria in enumerate(categorias_a_procesar):
            current_categoria = categoria
            current_categoria_index = start_index + idx + 1
            
            try:
                scrape_categoria(driver, categoria, current_categoria_index, len(CATEGORIAS))
                categorias_completed.add(categoria)
                
            except Exception as e:
                print(f"Error en categoría {categoria}: {e}")
                continue
            
            # Pausa entre categorías
            time.sleep(random.uniform(3, 6))
        
    except Exception as e:
        print(f"Error general: {e}")
        
    finally:
        if driver:
            driver.quit()
        if temp_profile_dir:
            shutil.rmtree(temp_profile_dir, ignore_errors=True)
    
    print(f"\n{'='*60}")
    print("SCRAPING COMPLETADO")
    print(f"Jobs en esta sesión: {jobs_this_session}")
    print(f"Total de jobs: {total_jobs_scraped}")
    print(f"Categorías completadas: {len(categorias_completed)}/{len(CATEGORIAS)}")
    print(f"Archivos guardados en: output_jobs/")
    print(f"{'='*60}")