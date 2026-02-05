#!/usr/bin/env python3
"""
Catho Brasil Scraper
https://www.catho.com.br/
Versión para SPA (Single Page Application)
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import os
from datetime import date
import sys
import argparse
import builtins
import signal
import time
import hashlib
import random
import re

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
COUNTRY_CONFIG = {
    "code": "BR",
    "name": "Brasil",
    "base_url": "https://www.catho.com.br",
    "color": '\033[0;33m',  # Amarillo para Brasil
}

COLOR = COUNTRY_CONFIG["color"]
RESET = '\033[0m'

_original_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    colored_args = [f"{COLOR}{arg}{RESET}" if isinstance(arg, str) else arg for arg in args]
    _original_print(*colored_args, **kwargs)
builtins.print = print

parser = argparse.ArgumentParser(description='Script de scraping para Catho Brasil')
parser.add_argument('--debug', action='store_true', help='Activar mensajes de debug')
parser.add_argument('--start-from', type=str, help='Iniciar desde una categoría específica')
args = parser.parse_args()

def debug_print(*mensaje, **kwargs):
    if args.debug:
        _original_print(f"{COLOR}{' '.join(map(str, mensaje))}{RESET}", flush=True, **kwargs)

# =============================================================================
# CATEGORÍAS - Extraídas de catho.com.br
# =============================================================================
CATEGORIAS = [
    ("Primeiro Emprego", "estagio-aprendiz-estagiario"),
    ("Administrativo", "administrativo"),
    ("Vendas", "vendas"),
    ("Jurídico", "area-juridica"),
    ("Financeiro", "financeiro"),
    ("Produção", "producao"),
    ("RH", "recrutamento"),
    ("Saúde", "saude"),
    ("Educação", "educacao"),
    ("Tecnologia", "tecnologia"),
    ("Cozinha", "cozinha"),
    ("PCD", "pcd"),
]

# Variables globales
driver = None
total_jobs_scraped = 0
jobs_this_session = 0
EMPLEOS = []
HASHES_GLOBALES = set()
current_category = ""

def signal_handler(sig, frame):
    print(f"\n\nInterrupción detectada (CTRL+C)")
    if EMPLEOS:
        print(f"Guardando {len(EMPLEOS)} empleos pendientes...")
        guardar_datos_incremental(EMPLEOS, current_category or "partial")
    if driver:
        try:
            driver.quit()
        except:
            pass
    print(f"Total empleos guardados: {total_jobs_scraped}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def calcular_hash(texto):
    if not isinstance(texto, str):
        return None
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def guardar_datos_incremental(empleos, area, archivo_base="output_jobs/Catho_BR"):
    os.makedirs("output_jobs", exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d")
    nombre_archivo = f"{archivo_base}_{area}_{timestamp}.json"
    
    empleos_existentes = []
    if os.path.exists(nombre_archivo):
        try:
            with open(nombre_archivo, 'r', encoding='utf-8') as f:
                empleos_existentes = json.load(f)
            print(f"Cargados {len(empleos_existentes)} empleos existentes del archivo")
        except:
            print("Archivo existente pero no se pudo leer, creando nuevo")
    
    todos_empleos = empleos_existentes + empleos
    
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        json.dump(todos_empleos, f, ensure_ascii=False, indent=4)
    
    print(f"\nGuardado: {nombre_archivo}")
    print(f"  - Empleos nuevos: {len(empleos)}")
    print(f"  - Total en archivo: {len(todos_empleos)}")
    return nombre_archivo

def create_driver():
    """Crea un driver de Chrome optimizado para Catho"""
    options = webdriver.ChromeOptions()
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Disable images for faster loading
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2
    }
    options.add_experimental_option("prefs", prefs)
    
    # EAGER = don't wait for all resources, just DOM
    options.page_load_strategy = 'eager'
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Override webdriver detection
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    driver.set_page_load_timeout(5)
    driver.implicitly_wait(3)  # Reducido de 10s
    
    return driver

def verificar_sesion_activa(driver):
    try:
        driver.current_url
        return True
    except:
        return False

def recrear_driver_si_necesario(driver):
    if not verificar_sesion_activa(driver):
        print("Sesión perdida. Recreando driver...")
        try:
            driver.quit()
        except:
            pass
        return create_driver()
    return driver

def build_url(url_categoria, page_num):
    """
    Construye la URL correcta para Catho:
    - Page 1: https://www.catho.com.br/vagas/{slug}/
    - Page N: https://www.catho.com.br/vagas/{slug}/?page=N
    """
    base = f"{COUNTRY_CONFIG['base_url']}/vagas/{url_categoria}/"
    if page_num == 1:
        return base
    else:
        return f"{base}?page={page_num}"

def extract_valid_job_urls(driver):
    """
    Extrae URLs válidas de vagas de la página actual.
    URLs válidas tienen formato: /vagas/{slug}/{id_numerico}/
    Ejemplo: /vagas/analista-de-sistemas/12345678/
    """
    job_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/vagas/']")
    
    valid_jobs = []
    seen_urls = set()
    
    for link in job_links:
        try:
            href = link.get_attribute("href")
            if not href or href in seen_urls:
                continue
            
            debug_print(f"  URL encontrada: {href}")
            
            # Excluir páginas de listado y navegación
            if '?page=' in href or '/por-local/' in href:
                debug_print(f"    -> Rechazado: es paginación o filtro")
                continue
            
            # Buscar patrón de ID numérico al final (mínimo 5 dígitos)
            # Ejemplo: /vagas/analista-de-sistemas/12345678/
            match = re.search(r'/vagas/([^/]+)/(\d{5,})/?$', href)
            if match:
                slug = match.group(1)
                job_id = match.group(2)
                
                # Verificar que el slug tenga contenido real (no sea solo categoría)
                if len(slug) > 3 and '-' in slug:
                    seen_urls.add(href)
                    
                    # Intentar obtener título del enlace
                    titulo = ""
                    try:
                        titulo = link.text.strip().split('\n')[0]
                    except:
                        titulo = slug.replace('-', ' ').title()
                    
                    valid_jobs.append({
                        'url': href,
                        'titulo': titulo if titulo else slug.replace('-', ' ').title(),
                        'id': job_id
                    })
                    debug_print(f"    -> VÁLIDO: {slug} (ID: {job_id})")
                else:
                    debug_print(f"    -> Rechazado: slug muy corto '{slug}'")
            else:
                debug_print(f"    -> Rechazado: no tiene ID numérico")
                
        except Exception as e:
            debug_print(f"    -> Error: {e}")
            continue
    
    return valid_jobs

def verificar_pagina_existe(driver, url_categoria, page_num):
    """Verifica si una página tiene vagas válidas"""
    url = build_url(url_categoria, page_num)
    
    try:
        try:
            driver.get(url)
            time.sleep(1.5)

        except:
            driver.execute_script("window.stop();")
        # Verificar mensajes de no resultados
        page_source = driver.page_source.lower()
        no_results_phrases = [
            "nenhuma vaga",
            "sem resultados", 
            "não encontramos",
            "Não encontramos nenhuma",
            "não há vagas"
        ]
        
        for phrase in no_results_phrases:
            if phrase in page_source:
                print(f"Página {page_num}: 0 vagas")
                return False
        
        # Extraer vagas válidas
        valid_jobs = extract_valid_job_urls(driver)
        
        if len(valid_jobs) > 0:
            print(f"Página {page_num}: {len(valid_jobs)} vagas")
            return True
        else:
            print(f"Página {page_num}: 0 vagas")
            return False
            
    except Exception as e:
        debug_print(f"Error verificando página {page_num}: {e}")
        return False

def obtener_total_paginas(driver, url_categoria):
    """Encuentra el número real de páginas usando búsqueda binaria"""
    print(f"\nAnalizando categoría: {url_categoria}")
    
    # Verificar primera página
    if not verificar_pagina_existe(driver, url_categoria, 1):
        print("No se encontraron vagas en la primera página")
        return 1
    
    # Fase 1: Saltos de 50 para encontrar límite superior
    ultima_valida = 1
    pagina = 50
    
    while verificar_pagina_existe(driver, url_categoria, pagina):
        ultima_valida = pagina
        pagina += 50
  
    
    # Fase 2: Búsqueda binaria refinada
    left = ultima_valida
    right = pagina
    
    while left < right - 1:
        mid = (left + right) // 2
        
        if verificar_pagina_existe(driver, url_categoria, mid):
            ultima_valida = mid
            left = mid
        else:
            right = mid
    
    # Fase 3: Verificación secuencial final
    pagina = ultima_valida
    while verificar_pagina_existe(driver, url_categoria, pagina + 1):
        pagina += 1
        ultima_valida = pagina
 
    print(f"Total de páginas encontradas: {ultima_valida}")
    return ultima_valida

def close_popups(driver):
    """Intenta cerrar popups - versión rápida"""
    try:
        from selenium.webdriver.common.keys import Keys
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except:
        pass

def extract_job_details(driver, job_url):
    """Extrae los detalles de una vaga específica - versión ultra rápida"""
    try:
        try:
            driver.get(job_url)
            WebDriverWait(driver, 0.3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.js-o-link")))

        except:
            driver.execute_script("window.stop();")
        
        details = {
            'titulo': '',
            'empresa': '',
            'ubicacion': 'Brasil',
            'salario': '',
            'descripcion': ''
        }
        
        # Título - h1
        try:
            h1 = driver.find_element(By.TAG_NAME, "h1")
            details['titulo'] = h1.text.strip()
        except:
            pass
        
        # Empresa
        elem = driver.find_element(By.ID, "__NEXT_DATA__").get_attribute("innerHTML")
        data = json.loads(elem)
        empresa = (
            data.get("props", {})
                .get("pageProps", {})
                .get("jobAdData", {})
                .get("contratante", {})
                .get("nome", "")
                .strip()
        )
        if empresa:
            details["empresa"] = empresa.lower().capitalize()
        
        # Ubicación
        for sel in ["[class*='ocation']", "[class*='ocal']"]:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                txt = elem.text.strip()
                if txt and len(txt) > 2:
                    details['ubicacion'] = txt
                    break
            except:
                continue
        
        # Descripción - body text
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            details['descripcion'] = body.text[:4000]
        except:
            pass
        
        return details
        
    except Exception as e:
        debug_print(f"Error extrayendo: {str(e)}")
        return None

def scrape_categoria(driver, nombre_cat, url_cat, cat_index, total_cats):
    """Scrape una categoría completa"""
    global total_jobs_scraped, jobs_this_session, EMPLEOS, HASHES_GLOBALES, current_category
    
    current_category = url_cat
    
    print(f"\n{'='*80}")
    print(f"PROCESANDO CATEGORÍA {cat_index}/{total_cats}: {nombre_cat}")
    print(f"{'='*80}")
    
    # Obtener total de páginas
    total_paginas = obtener_total_paginas(driver, url_cat)
    print(f"Encontradas {total_paginas} páginas para {nombre_cat}")
    print("Comenzando extracción de vagas...")
    
    cat_jobs = 0
    pagina = 1
    consecutive_empty = 0
    
    while pagina <= total_paginas and consecutive_empty < 3:
        url = build_url(url_cat, pagina)
        
        print(f"\nProcesando página {pagina}/{total_paginas} de {nombre_cat}")
        
        try:
            try:
                driver.get(url)
            except:
                driver.execute_script("window.stop();")
            
            # Extraer jobs de la página
            jobs = extract_valid_job_urls(driver)
            
            if len(jobs) == 0:
                consecutive_empty += 1
                pagina += 1
                continue
            
            consecutive_empty = 0
            
            # Mostrar jobs encontrados
            # print(f"{len(jobs)} vagas encontradas:")
            # for idx, job in enumerate(jobs):
            #     print(f"{idx} - {job['titulo'][:60]}")
            
            # Procesar cada job
            for i, job in enumerate(jobs):
                try:
                    job_url = job.get('url', '')
                    titulo = job.get('titulo', 'Sin título')
                    
                    if not job_url:
                        continue
                    
                    print(f"  Procesando {i+1}/{len(jobs)}: {titulo[:40]}...")
                    
                    # Recrear driver si es necesario
                    driver = recrear_driver_si_necesario(driver)
                    
                    # Obtener detalles con timeout de seguridad
                    details = None
                    try:
                        details = extract_job_details(driver, job_url)
                    except Exception as e:
                        debug_print(f"  Error en extract_job_details: {e}")
                    
                    if not details:
                        debug_print(f"  Usando datos básicos para {titulo[:30]}")
                        details = {
                            'titulo': titulo,
                            'empresa': 'N/A',
                            'ubicacion': 'Brasil',
                            'salario': 'N/A',
                            'descripcion': f"Vaga: {titulo} - Categoria: {nombre_cat}"
                        }
                    
                    # Hash = descripcion + ubicacion + empresa
                    ubicacion = details.get("ubicacion", "Brasil")
                    empresa = details.get("empresa", "NA/NA")
                    hash_content = details.get("descripcion", titulo) + "|" + ubicacion + "|" + empresa
                    hash_empleo = calcular_hash(hash_content)
                    
                    if hash_empleo in HASHES_GLOBALES:
                        print(f"  ^ [DUPLICADO]")
                        continue
                    
                    EMPLEOS.append({
                        "Id Interno": f"CATHO-{url_cat[:15]}-{pagina}-{i+1}",
                        "titulo": details.get("titulo", titulo),
                        "descripcion": details.get("descripcion", ""),
                        "Empresa": empresa,
                        "Fuente": "Catho Brasil",
                        "Tipo Portal": "Tradicional",
                        "url": job_url,
                        "Pais": COUNTRY_CONFIG["name"],
                        "ubicacion": ubicacion,
                        "salario": details.get("salario", "N/A"),
                        "Categoria Portal": nombre_cat,
                        "Subcategoria Portal": "",
                        "Categorria": "",
                        "Subcategoria": "",
                        "hash Descripcion": hash_empleo,
                        "fecha": date.today().strftime("%d/%m/%Y")
                    })
                    
                    HASHES_GLOBALES.add(hash_empleo)
                    total_jobs_scraped += 1
                    jobs_this_session += 1
                    cat_jobs += 1
                    
                except Exception as e:
                    debug_print(f"Error procesando vaga {i+1}: {str(e)}")
                    continue
            
            pagina += 1
            # Sin sleep entre páginas
            
        except Exception as e:
            debug_print(f"Error en página {pagina}: {str(e)}")
            driver = recrear_driver_si_necesario(driver)
            pagina += 1
            continue
    
    # Guardar al finalizar categoría
    print(f"\n{'='*60}")
    print(f"Categoría '{nombre_cat}' completada - Guardando datos...")
    print(f"Vagas en esta categoría: {cat_jobs}")
    print(f"Total acumulado: {total_jobs_scraped}")
    print(f"{'='*60}")
    
    if EMPLEOS:
        guardar_datos_incremental(EMPLEOS, url_cat)
        EMPLEOS = []
    
    return cat_jobs

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("="*60)
    print("CATHO BRASIL SCRAPER")
    print("="*60)
    print(f"\nIniciando scraping de Catho Brasil...")
    
    if args.debug:
        print("Modo debug activado")
    
    if args.start_from:
        print(f"Iniciando desde la categoría: {args.start_from}")
    
    # Cargar hashes existentes
    print("Cargando hashes existentes...")
    for nombre, url_cat in CATEGORIAS:
        timestamp = date.today().strftime("%Y%m%d")
        archivo = f"output_jobs/Catho_BR_{url_cat}_{timestamp}.json"
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
    
    # Determinar categorías a procesar
    start_index = 0
    if args.start_from:
        for i, (nombre, slug) in enumerate(CATEGORIAS):
            if slug == args.start_from or args.start_from.lower() in nombre.lower():
                start_index = i
                break
    
    categorias_to_process = CATEGORIAS[start_index:]
    print(f"\nProcesando {len(categorias_to_process)} categorías...")
    
    # Crear driver
    driver = create_driver()
    
    try:
        for idx, (nombre_cat, url_cat) in enumerate(categorias_to_process, start_index + 1):
            try:
                scrape_categoria(driver, nombre_cat, url_cat, idx, len(CATEGORIAS))
            except Exception as e:
                print(f"Error crítico en categoría {nombre_cat}: {str(e)}")
                driver = recrear_driver_si_necesario(driver)
                continue
            
            # Sin sleep entre categorías
            
    finally:
        try:
            driver.quit()
        except:
            pass
    
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETADO!")
    print(f"Vagas recolectadas en esta sesión: {jobs_this_session}")
    print(f"Total de vagas: {total_jobs_scraped}")
    print(f"Archivos guardados en: output_jobs/")
    print(f"{'='*60}\n")