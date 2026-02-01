#!/usr/bin/env python3
"""
Bumeran México Scraper
https://www.bumeran.com.mx/
Versión actualizada para SPA (Single Page Application)
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
    "code": "MX",
    "name": "México",
    "base_url": "https://www.bumeran.com.mx",
    "color": '\033[0;36m',  # Cyan
}

COLOR = COUNTRY_CONFIG["color"]
RESET = '\033[0m'

_original_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    colored_args = [f"{COLOR}{arg}{RESET}" if isinstance(arg, str) else arg for arg in args]
    _original_print(*colored_args, **kwargs)
builtins.print = print

parser = argparse.ArgumentParser(description='Script de scraping para Bumeran México')
parser.add_argument('--debug', action='store_true', help='Activar mensajes de debug')
parser.add_argument('--start-from', type=str, help='Iniciar desde una categoría específica')
args = parser.parse_args()

def debug_print(*mensaje, **kwargs):
    if args.debug:
        _original_print(f"{COLOR}{' '.join(map(str, mensaje))}{RESET}", **kwargs)

# =============================================================================
# CATEGORÍAS - Extraídas de bumeran.com.mx
# =============================================================================
CATEGORIAS = [
    ("Oficios y Otros", "oficios-y-otros"),
    ("Administración, Contabilidad y Finanzas", "administracion-contabilidad-y-finanzas"),
    ("Producción y Manufactura", "produccion-y-manufactura"),
    ("Comercial, Ventas y Negocios", "comercial-ventas-y-negocios"),
    ("Recursos Humanos y Capacitación", "recursos-humanos-y-capacitacion"),
    ("Abastecimiento y Logística", "abastecimiento-y-logistica"),
    ("Tecnología, Sistemas y Telecomunicaciones", "tecnologia-sistemas-y-telecomunicaciones"),
    ("Marketing y Publicidad", "marketing-y-publicidad"),
    ("Atención al Cliente, Call Center y Telemarketing", "atencion-al-cliente-call-center-y-telemarketing"),
    ("Secretarias y Recepción", "secretarias-y-recepcion"),
    ("Gastronomía y Turismo", "gastronomia-y-turismo"),
    ("Ingenierías", "ingenierias"),
    ("Salud, Medicina y Farmacia", "salud-medicina-y-farmacia"),
    ("Ingeniería Civil y Construcción", "ingenieria-civil-y-construccion"),
    ("Comunicación, Relaciones Institucionales y Públicas", "comunicacion-relaciones-institucionales-y-publicas"),
    ("Diseño", "diseno"),
    ("Legales", "legales"),
    ("Seguros", "seguros"),
    ("Educación, Docencia e Investigación", "educacion-docencia-e-investigacion"),
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

def guardar_datos_incremental(empleos, categoria, archivo_base="output_jobs/Bumeran_MX"):
    os.makedirs("output_jobs", exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d")
    # Limpiar nombre de categoría para archivo
    cat_clean = re.sub(r'[^\w\-]', '_', categoria)[:30]
    nombre_archivo = f"{archivo_base}_{cat_clean}_{timestamp}.json"
    
    empleos_existentes = []
    if os.path.exists(nombre_archivo):
        try:
            with open(nombre_archivo, 'r', encoding='utf-8') as f:
                empleos_existentes = json.load(f)
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
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # JavaScript handling
    prefs = {
        'profile.default_content_setting_values.cookies': 1,
        'profile.default_content_setting_values.notifications': 2,
    }
    options.add_experimental_option('prefs', prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    driver.set_page_load_timeout(60)
    driver.implicitly_wait(10)
    
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

def verificar_pagina_existe(driver, url_base, page_num):
    """Verifica si una página tiene empleos válidos"""
    test_url = f"{url_base}.html?page={page_num}"
    
    try:
        driver.get(test_url)
        time.sleep(1.5)
        
        # Scroll para cargar contenido
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(0.3)
        
        # Verificar si hay mensaje de no resultados
        page_source = driver.page_source.lower()
        if "no encontramos" in page_source or "sin resultados" in page_source or "0 avisos" in page_source:
            print(f"Página {page_num}: 0 empleos")
            return False
        
        # Buscar enlaces a empleos individuales (no categorías)
        job_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/empleos/']")
        
        valid_jobs = 0
        seen_urls = set()
        
        for link in job_links:
            try:
                href = link.get_attribute("href")
                if not href:
                    continue
                
                # Debug: mostrar todas las URLs encontradas
                debug_print(f"  URL encontrada: {href}")
                    
                # Filtrar solo enlaces a empleos individuales
                if '/empleos/' in href and href not in seen_urls:
                    # Excluir páginas de categorías y listados
                    if 'empleos-area' in href:
                        debug_print(f"    -> Rechazado: es página de área")
                        continue
                    if '-pagina-' in href or '?page=' in href:
                        debug_print(f"    -> Rechazado: es paginación")
                        continue
                    
                    # Debe terminar en .html y tener un ID numérico al final
                    # Formato típico: /empleos/titulo-del-puesto-1234567.html
                    if not href.endswith('.html'):
                        debug_print(f"    -> Rechazado: no termina en .html")
                        continue
                    
                    # Extraer el slug después de /empleos/
                    parts = href.split('/empleos/')
                    if len(parts) > 1:
                        slug = parts[1].replace('.html', '')
                        
                        # El slug debe tener al menos 15 caracteres y contener guiones
                        if len(slug) < 15 or '-' not in slug:
                            debug_print(f"    -> Rechazado: slug muy corto o sin guiones: {slug}")
                            continue
                        
                        # Verificar que tenga un ID numérico al final (típico de Bumeran)
                        # Ejemplo: vendedor-telefonico-1234567
                        last_part = slug.split('-')[-1]
                        if not last_part.isdigit():
                            debug_print(f"    -> Rechazado: no tiene ID numérico: {last_part}")
                            continue
                        
                        seen_urls.add(href)
                        valid_jobs += 1
                        debug_print(f"    -> VÁLIDO: {slug[:50]}")
            except:
                continue
        
        if valid_jobs > 0:
            print(f"Página {page_num}: {valid_jobs} empleos")
            return True
        else:
            print(f"Página {page_num}: 0 empleos")
            return False
            
    except Exception as e:
        debug_print(f"Error verificando página {page_num}: {e}")
        return False

def obtener_total_paginas(driver, url_categoria):
    """Encuentra el número real de páginas usando búsqueda binaria"""
    url_base = f"{COUNTRY_CONFIG['base_url']}/empleos-area-{url_categoria}"
    
    print(f"Analizando categoría: {url_categoria}")
    
    # Verificar primera página
    if not verificar_pagina_existe(driver, url_base, 1):
        print("No se encontraron empleos en la primera página")
        return 0
    
    # Fase 1: Encontrar límite superior con saltos de 20
    ultima_valida = 1
    right = 20
    
    while True:
        if verificar_pagina_existe(driver, url_base, right):
            ultima_valida = right
            right += 20
        else:
            break
        
        if right > 200:
            break
    
    # Fase 2: Búsqueda binaria
    left = ultima_valida
    
    while left <= right:
        mid = (left + right) // 2
        if mid == left or mid == right:
            break
        
        if verificar_pagina_existe(driver, url_base, mid):
            ultima_valida = mid
            left = mid + 1
        else:
            right = mid - 1
    
    # Fase 3: Búsqueda secuencial final
    pagina = ultima_valida
    
    while True:
        if not verificar_pagina_existe(driver, url_base, pagina + 1):
            break
        pagina += 1
        ultima_valida = pagina
        
        if pagina > 300:
            break
    
    print(f"Total de páginas encontradas: {ultima_valida}")
    return ultima_valida

def extract_jobs_from_listing(driver):
    """Extrae empleos de la página de listado de Bumeran"""
    jobs = []
    
    try:
        time.sleep(1.5)
        
        # Scroll para cargar todo
        driver.execute_script("window.scrollTo(0, 500);")
        driver.execute_script("window.scrollTo(0, 1500);")
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        
        # Buscar enlaces a empleos individuales
        job_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/empleos/']")
        
        seen_urls = set()
        job_cards = []
        
        for link in job_links:
            try:
                href = link.get_attribute("href")
                if not href:
                    continue
                
                # Filtrar solo enlaces a empleos individuales
                if '/empleos/' in href and href not in seen_urls:
                    # Excluir páginas de categorías y listados
                    if 'empleos-area' in href or '-pagina-' in href or '?page=' in href:
                        continue
                    
                    # Debe terminar en .html
                    if not href.endswith('.html'):
                        continue
                    
                    # Extraer el slug después de /empleos/
                    parts = href.split('/empleos/')
                    if len(parts) > 1:
                        slug = parts[1].replace('.html', '')
                        
                        # El slug debe tener al menos 15 caracteres y contener guiones
                        if len(slug) < 15 or '-' not in slug:
                            continue
                        
                        # Verificar que tenga un ID numérico al final
                        last_part = slug.split('-')[-1]
                        if not last_part.isdigit():
                            continue
                        
                        seen_urls.add(href)
                        
                        # Obtener título del enlace o del h2 interno
                        titulo = ""
                        try:
                            h2 = link.find_element(By.TAG_NAME, "h2")
                            titulo = h2.text.strip()
                        except:
                            titulo = link.text.strip()
                        
                        # Limpiar título
                        if titulo and len(titulo) > 5:
                            # Tomar solo la primera línea si hay múltiples
                            titulo = titulo.split('\n')[0].strip()
                            
                            if len(titulo) > 5 and len(titulo) < 200:
                                job_cards.append({
                                    'titulo': titulo,
                                    'url': href,
                                    'element': link
                                })
            except:
                continue
        
        if len(job_cards) == 0:
            # Fallback: buscar h2 y extraer datos
            debug_print("Usando fallback por h2...")
            h2_elements = driver.find_elements(By.TAG_NAME, "h2")
            
            skip_texts = ['resultados', 'filtros', 'ordenar', 'buscar', 'bumeran', 
                          'alertas', 'aviso', 'página', 'empleos de']
            
            for h2 in h2_elements:
                try:
                    texto = h2.text.strip()
                    if texto and len(texto) > 5 and len(texto) < 150:
                        if not any(skip.lower() in texto.lower() for skip in skip_texts):
                            job_cards.append({
                                'titulo': texto,
                                'url': '',
                                'element': h2
                            })
                except:
                    continue
        
        print(f"{len(job_cards)} empleos encontrados:")
        
        # Procesar cada empleo
        for idx, job in enumerate(job_cards[:25]):
            try:
                titulo = job['titulo']
                print(f"{idx} - {titulo[:60]}")
                
                # Extraer datos adicionales
                job_data = {
                    'titulo': titulo,
                    'empresa': 'Confidencial',
                    'ubicacion': 'México',
                    'salario': 'No especificado',
                    'descripcion': ''
                }
                
                # Intentar obtener más datos del card
                try:
                    element = job['element']
                    parent = element
                    
                    # Subir en el DOM para encontrar el contenedor
                    for _ in range(5):
                        try:
                            parent = parent.find_element(By.XPATH, "./..")
                            card_text = parent.text
                            if len(card_text) > 50:
                                break
                        except:
                            break
                    
                    if parent and parent.text:
                        card_text = parent.text
                        lines = card_text.split('\n')
                        
                        for line in lines:
                            line = line.strip()
                            
                            # Buscar salario
                            if '$' in line and ('mes' in line.lower() or 'mensual' in line.lower()):
                                job_data['salario'] = line
                            
                            # Buscar ubicación (estados mexicanos)
                            ubicaciones = ['CDMX', 'Ciudad de México', 'Jalisco', 'Nuevo León',
                                          'Monterrey', 'Guadalajara', 'Estado de México', 'Puebla',
                                          'Querétaro', 'Tijuana', 'Veracruz', 'Chihuahua']
                            for ub in ubicaciones:
                                if ub.lower() in line.lower() and len(line) < 100:
                                    job_data['ubicacion'] = line
                                    break
                        
                        # Empresa puede estar en una línea corta sin símbolos
                        for line in lines[1:4]:
                            line = line.strip()
                            if line and len(line) > 3 and len(line) < 60:
                                if '$' not in line and 'hace' not in line.lower():
                                    if not any(ub.lower() in line.lower() for ub in ubicaciones):
                                        job_data['empresa'] = line
                                        break
                except:
                    pass
                
                # Descripción básica
                job_data['descripcion'] = f"{titulo} - {job_data['empresa']} - {job_data['ubicacion']}"
                
                jobs.append({
                    'titulo': titulo,
                    'url': job['url'],
                    'data': job_data
                })
                
            except Exception as e:
                debug_print(f"Error procesando empleo {idx}: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        debug_print(f"Error en extract_jobs_from_listing: {e}")
        return []

def extract_job_details(driver, job_url):
    """Extrae detalles completos de un empleo"""
    try:
        driver.get(job_url)
        time.sleep(1.5)
        
        # Título
        titulo = ""
        try:
            titulo = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            titulo = "Título no disponible"
        
        # Empresa
        empresa = "Confidencial"
        try:
            # Buscar por varios selectores
            for selector in ["a[href*='bolsa-trabajo']", "span[class*='empresa']", "div[class*='empresa']"]:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if elem.text.strip():
                        empresa = elem.text.strip()
                        break
                except:
                    continue
        except:
            pass
        
        # Ubicación
        ubicacion = "México"
        try:
            # Buscar span o div con ubicación
            page_text = driver.find_element(By.TAG_NAME, "body").text
            ubicaciones = ['CDMX', 'Ciudad de México', 'Jalisco', 'Nuevo León',
                          'Monterrey', 'Guadalajara', 'Estado de México', 'Puebla',
                          'Querétaro', 'Tijuana', 'Veracruz', 'Chihuahua', 'Sonora']
            for ub in ubicaciones:
                if ub in page_text:
                    ubicacion = ub
                    break
        except:
            pass
        
        # Salario
        salario = "No especificado"
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            salary_match = re.search(r'\$[\d,]+\s*[-a]\s*\$?[\d,]*\s*[Mm]ensual', page_text)
            if salary_match:
                salario = salary_match.group(0)
        except:
            pass
        
        # Descripción
        descripcion = ""
        try:
            # Buscar sección de descripción
            desc_selectors = [
                "div[class*='descripcion']",
                "div[class*='description']",
                "section[class*='descripcion']",
                "div[data-testid*='description']"
            ]
            
            for selector in desc_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    if elem.text and len(elem.text) > 100:
                        descripcion = elem.text[:5000]
                        break
                except:
                    continue
            
            if not descripcion:
                # Buscar párrafos largos
                paragraphs = driver.find_elements(By.TAG_NAME, "p")
                for p in paragraphs:
                    if len(p.text) > 200:
                        descripcion = p.text[:5000]
                        break
        except:
            pass
        
        if not descripcion:
            descripcion = f"{titulo} - {empresa} - {ubicacion}"
        
        return {
            "titulo": titulo,
            "empresa": empresa,
            "ubicacion": ubicacion,
            "salario": salario,
            "descripcion": descripcion,
        }
        
    except Exception as e:
        debug_print(f"Error extrayendo detalles: {e}")
        return None

def scrape_categoria(driver, nombre_cat, url_cat, cat_index, total_cats):
    """Scrape una categoría completa"""
    global total_jobs_scraped, jobs_this_session, EMPLEOS, HASHES_GLOBALES, current_category
    
    current_category = nombre_cat
    
    print(f"\n{'='*80}")
    print(f"PROCESANDO CATEGORÍA {cat_index}/{total_cats}: {nombre_cat}")
    print(f"{'='*80}")
    
    total_paginas = obtener_total_paginas(driver, url_cat)
    
    if total_paginas == 0:
        print(f"No se encontraron empleos para {nombre_cat}")
        return 0
    
    print(f"Encontradas {total_paginas} páginas para {nombre_cat}")
    print("Comenzando extracción de empleos...")
    
    cat_jobs = 0
    pagina = 1
    consecutive_empty = 0
    
    while pagina <= total_paginas and consecutive_empty < 3:
        url = f"{COUNTRY_CONFIG['base_url']}/empleos-area-{url_cat}.html?page={pagina}"
        
        print(f"\nProcesando página {pagina}/{total_paginas} de {nombre_cat}")
        debug_print(f"URL: {url}")
        
        try:
            driver.get(url)
            time.sleep(1.5)
            
            # Verificar si hay resultados
            page_text = driver.page_source.lower()
            if "no encontramos" in page_text or "sin resultados" in page_text:
                print("No se encontraron más resultados")
                break
            
            # Extraer empleos
            jobs_found = extract_jobs_from_listing(driver)
            
            if len(jobs_found) == 0:
                consecutive_empty += 1
                print(f"No se encontraron empleos en la página {pagina}")
                pagina += 1
                continue
            
            consecutive_empty = 0
            
            for i, job_info in enumerate(jobs_found):
                try:
                    titulo = job_info.get('titulo', 'Sin título')
                    job_url = job_info.get('url', '')
                    
                    if 'data' in job_info:
                        details = job_info['data']
                    elif job_url:
                        driver = recrear_driver_si_necesario(driver)
                        details = extract_job_details(driver, job_url)
                        if not details:
                            continue
                    else:
                        details = {
                            'titulo': titulo,
                            'empresa': 'Confidencial',
                            'ubicacion': 'México',
                            'salario': 'No especificado',
                            'descripcion': f"Empleo: {titulo} - Categoría: {nombre_cat}"
                        }
                    
                    # Hash = descripcion + ubicacion + empresa (same job, different city/company = not duplicate)
                    ubicacion = details.get("ubicacion", "México")
                    empresa = details.get("empresa", "Confidencial")
                    hash_content = details.get("descripcion", titulo) + "|" + ubicacion + "|" + empresa
                    hash_empleo = calcular_hash(hash_content)
                    
                    if hash_empleo in HASHES_GLOBALES:
                        print(f"  ^ [DUPLICADO]")
                        continue
                    
                    EMPLEOS.append({
                        "Id Interno": f"BUM-MX-{url_cat[:15]}-{pagina}-{i+1}",
                        "titulo": details.get("titulo", titulo),
                        "descripcion": details.get("descripcion", ""),
                        "Empresa": empresa,
                        "Fuente": "Bumeran México",
                        "Tipo Portal": "Tradicional",
                        "url": job_url if job_url else url,
                        "Pais": COUNTRY_CONFIG["name"],
                        "ubicacion": ubicacion,
                        "salario": details.get("salario", "No especificado"),
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
                    debug_print(f"Error procesando empleo {i+1}: {str(e)}")
                    continue
            
            pagina += 1
            time.sleep(random.uniform(0.5, 1))
            
        except Exception as e:
            print(f"Error en página {pagina}: {str(e)}")
            driver = recrear_driver_si_necesario(driver)
            pagina += 1
            continue
    
    # Guardar al finalizar categoría
    print(f"\n{'='*60}")
    print(f"Categoría '{nombre_cat}' completada - Guardando datos...")
    print(f"Jobs en esta categoría: {cat_jobs}")
    print(f"Total acumulado: {total_jobs_scraped}")
    print(f"{'='*60}")
    
    if EMPLEOS:
        guardar_datos_incremental(EMPLEOS, nombre_cat)
        EMPLEOS = []
    
    return cat_jobs

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print(f"Iniciando scraping de Bumeran - {COUNTRY_CONFIG['name']}...")
    print(f"URL base: {COUNTRY_CONFIG['base_url']}")
    
    if args.debug:
        print("Modo debug activado")
    
    # Cargar hashes existentes
    print("Cargando hashes existentes...")
    for nombre_cat, url_cat in CATEGORIAS:
        timestamp = date.today().strftime("%Y%m%d")
        cat_clean = re.sub(r'[^\w\-]', '_', nombre_cat)[:30]
        archivo = f"output_jobs/Bumeran_MX_{cat_clean}_{timestamp}.json"
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
    
    # Determinar desde qué categoría comenzar
    start_index = 0
    if args.start_from:
        for i, (nombre, slug) in enumerate(CATEGORIAS):
            if args.start_from.lower() in nombre.lower() or args.start_from.lower() in slug.lower():
                start_index = i
                print(f"Iniciando desde: {nombre}")
                break
    
    print(f"Procesando {len(CATEGORIAS) - start_index} categorías...")
    
    driver = create_driver()
    
    try:
        for idx, (nombre_cat, url_cat) in enumerate(CATEGORIAS[start_index:], start_index + 1):
            try:
                scrape_categoria(driver, nombre_cat, url_cat, idx, len(CATEGORIAS))
            except Exception as e:
                print(f"Error crítico en categoría {nombre_cat}: {str(e)}")
                driver = recrear_driver_si_necesario(driver)
                continue
            
            time.sleep(random.uniform(1, 2))
            
    finally:
        try:
            driver.quit()
        except:
            pass
    
    print(f"\nSCRAPING COMPLETADO!")
    print(f"Resumen de la sesión:")
    print(f"   - Jobs recolectados en esta sesión: {jobs_this_session}")
    print(f"   - Total de jobs: {total_jobs_scraped}")
    print(f"   - Categorías procesadas: {len(CATEGORIAS)}")
    print(f"   - Archivos guardados en: output_jobs/")