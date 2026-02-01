#!/usr/bin/env python3
"""
OCC Mundial Scraper - México
https://www.occ.com.mx/empleos/
Versión actualizada con categorías reales del sitio
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
    "base_url": "https://www.occ.com.mx",
    "color": '\033[0;32m',  # Verde
}

COLOR = COUNTRY_CONFIG["color"]
RESET = '\033[0m'

_original_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    colored_args = [f"{COLOR}{arg}{RESET}" if isinstance(arg, str) else arg for arg in args]
    _original_print(*colored_args, **kwargs)
builtins.print = print

parser = argparse.ArgumentParser(description='Script de scraping para OCC Mundial México')
parser.add_argument('--debug', action='store_true', help='Activar mensajes de debug')
parser.add_argument('--start-from', type=str, help='Iniciar desde una categoría específica')
args = parser.parse_args()

def debug_print(*mensaje, **kwargs):
    if args.debug:
        _original_print(f"{COLOR}{' '.join(map(str, mensaje))}{RESET}", **kwargs)

# Variables globales
driver = None
total_jobs_scraped = 0
jobs_this_session = 0
EMPLEOS = []
HASHES_GLOBALES = set()
current_category = ""

def signal_handler(sig, frame):
    print(f"\n\nInterrupción detectada (CTRL+C)")
    print("Guardando datos antes de salir...")
    
    if EMPLEOS:
        print(f"Guardando {len(EMPLEOS)} empleos pendientes...")
        guardar_datos_incremental(EMPLEOS, current_category)
    
    if driver:
        try:
            driver.quit()
        except:
            pass
    
    print(f"Total empleos guardados: {total_jobs_scraped}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def guardar_datos_incremental(empleos, categoria, archivo_base="output_jobs/OCC_Mundial"):
    os.makedirs("output_jobs", exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d")
    cat_safe = re.sub(r'[^a-zA-Z0-9]', '_', categoria)[:50]
    nombre_archivo = f"{archivo_base}_{cat_safe}_{timestamp}.json"
    
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

def calcular_hash(texto):
    if not isinstance(texto, str):
        return None
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

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
    
    # Opciones para mejorar la carga de JavaScript
    options.add_argument('--enable-javascript')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-popup-blocking')
    
    # Preferencias para evitar bloqueos
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.cookies": 1,
        "profile.default_content_setting_values.javascript": 1,
    }
    options.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Evitar detección de bot
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    driver.maximize_window()
    
    # Configurar timeouts
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

# =============================================================================
# CATEGORÍAS DE OCC MUNDIAL (URLs reales del sitio)
# Formato: (nombre_display, slug_url)
# =============================================================================
CATEGORIAS = [
    ("Ventas", "trabajo-en-ventas"),
    ("Contabilidad - Finanzas", "trabajo-en-contabilidad-finanzas"),
    ("Administrativo", "trabajo-en-administrativo"),
    ("Tecnologías de la Información - Sistemas", "trabajo-en-tecnologias-de-la-informacion-sistemas"),
    ("Logística - Transporte - Distribución - Almacén", "trabajo-en-logistica-transporte-distribucion-almacen"),
    ("Ingeniería", "trabajo-en-ingenieria"),
    ("Manufactura - Producción - Operación", "trabajo-en-manufactura-produccion-operacion"),
    ("Recursos humanos", "trabajo-en-recursos-humanos"),
    ("Atención a clientes - Call Center", "trabajo-en-atencion-a-clientes-call-center"),
    ("Sector salud", "trabajo-en-sector-salud"),
    ("Servicios generales - Oficios - Seguridad", "trabajo-en-servicios-generales-oficios-seguridad"),
    ("Construcción - Inmobiliaria - Arquitectura", "trabajo-en-construccion-inmobiliaria-arquitectura"),
    ("Mercadotecnia - Publicidad - Relaciones Públicas", "trabajo-en-mercadotecnia-publicidad-relaciones-publicas"),
    ("Seguros y reaseguros", "trabajo-en-seguros-y-reaseguros"),
    ("Turismo - Hospitalidad - Gastronomía", "trabajo-en-turismo-hospitalidad-gastronomia"),
    ("Educación", "trabajo-en-educacion"),
    ("Derecho y leyes", "trabajo-en-derecho-y-leyes"),
    ("Arte y diseño", "trabajo-en-arte-y-diseno"),
    ("Comunicación y creatividad", "trabajo-en-comunicacion-y-creatividad"),
    ("Veterinaria - Agricultura", "trabajo-en-veterinaria-agricultura"),
    ("Minería - Energía - Recursos Naturales", "trabajo-en-mineria-energia-recursos-naturales"),
    ("Ciencias sociales - Humanidades", "trabajo-en-ciencias-sociales-humanidades"),
    ("Deportes - Salud - Belleza", "trabajo-en-deportes-salud-belleza"),
]

def verificar_pagina_existe(driver, url, page_num):
    """Verifica si una página tiene empleos válidos"""
    test_url = f"{url}/?page={page_num}"
    
    try:
        driver.get(test_url)
        time.sleep(1)
        
        # Verificar si hay mensaje de no resultados
        page_source = driver.page_source.lower()
        if "no encontramos" in page_source or "sin resultados" in page_source or "0 resultado" in page_source:
            print(f"Página {page_num}: 0 empleos")
            return False
        
        # Buscar h2 que sean títulos de empleo
        h2_elements = driver.find_elements(By.TAG_NAME, "h2")
        
        skip_texts = ['resultados', 'ordenar', 'relevancia', 'fecha', 'limpiar', 
                      'aplicar', 'buscar', 'occ', 'candidatos', 'reclutadores',
                      'empleos por', 'consigue un empleo', 'llegaste al final']
        
        valid_jobs = 0
        for h2 in h2_elements:
            try:
                texto = h2.text.strip().lower()
                if texto and len(texto) > 3:
                    if not any(skip in texto for skip in skip_texts):
                        valid_jobs += 1
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
    url_base = f"{COUNTRY_CONFIG['base_url']}/empleos/{url_categoria}"
    
    print(f"Analizando categoría: {url_categoria}")
    
    # Verificar primera página
    if not verificar_pagina_existe(driver, url_base, 1):
        print("No se encontraron empleos en la primera página")
        return 1
    
    # Fase 1: Encontrar límite superior con saltos de 50
    ultima_valida = 1
    right = 50
    
    while True:
        if verificar_pagina_existe(driver, url_base, right):
            ultima_valida = right
            right += 50
        else:
            break
        
        # Límite de seguridad
        if right > 500:
            break
    
    # Fase 2: Búsqueda binaria entre última válida y primera inválida
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
    
    # Fase 3: Búsqueda secuencial final para precisión
    pagina = ultima_valida
    
    while True:
        if not verificar_pagina_existe(driver, url_base, pagina + 1):
            break
        pagina += 1
        ultima_valida = pagina
        
        # Safety limit
        if pagina > 1000:
            break
    
    print(f"Total de páginas encontradas: {ultima_valida}")
    return ultima_valida

def extract_jobs_from_listing(driver):
    """
    Extrae empleos del listado de OCC.
    OCC muestra tarjetas a la izquierda con info básica y panel de detalles a la derecha.
    Extraemos datos de las tarjetas y hacemos clic para obtener descripción del panel.
    """
    jobs = []
    
    try:
        # Buscar h2 que son títulos de empleo
        h2_elements = driver.find_elements(By.TAG_NAME, "h2")
        
        skip_texts = ['resultados', 'ordenar', 'relevancia', 'fecha', 'limpiar', 
                      'aplicar', 'buscar', 'occ', 'candidatos', 'reclutadores',
                      'empleos por', 'consigue un empleo', 'llegaste al final',
                      'sobre el empleo', 'detalles', 'descripción']
        
        valid_h2s = []
        for h2 in h2_elements:
            try:
                text = h2.text.strip()
                if text and len(text) > 3 and len(text) < 200:
                    if not any(skip.lower() in text.lower() for skip in skip_texts):
                        valid_h2s.append({'element': h2, 'titulo': text})
            except:
                continue
        
        if len(valid_h2s) == 0:
            return []
        
        print(f"{len(valid_h2s)} empleos encontrados:", flush=True)
        
        for idx, job_info in enumerate(valid_h2s[:22]):
            try:
                h2 = job_info['element']
                titulo = job_info['titulo']
                
                print(f"{idx} - {titulo[:60]}")
                
                # Hacer clic para cargar detalles en panel derecho
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", h2)
                    driver.execute_script("arguments[0].click();", h2)
                    time.sleep(0.1)
                except:
                    pass
                
                # Extraer datos de la tarjeta (elemento padre del h2)
                job_data = {
                    'titulo': titulo,
                    'empresa': 'Confidencial',
                    'ubicacion': 'México',
                    'salario': 'No especificado',
                    'descripcion': ''
                }
                
                # Buscar contenedor de la tarjeta
                try:
                    card = h2
                    for _ in range(5):
                        card = card.find_element(By.XPATH, "./..")
                        card_text = card.text
                        if len(card_text) > 50:
                            break
                    
                    # Extraer salario del texto de la tarjeta
                    import re
                    salary_match = re.search(r'\$\s*[\d,]+\s*-?\s*\$?\s*[\d,]*\s*[Mm]ensual', card_text)
                    if salary_match:
                        job_data['salario'] = salary_match.group(0).strip()
                    
                    # Extraer ubicación (buscar líneas con estados/ciudades)
                    lines = card_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        # Buscar patrones de ubicación
                        if any(loc in line for loc in ['México', 'Jalisco', 'León', 'Monterrey', 
                                                        'CDMX', 'Guadalajara', 'Puebla', 'Veracruz',
                                                        'Querétaro', 'Tijuana', 'California', 'Sonora',
                                                        'Chihuahua', 'Nuevo León', 'Cancún']):
                            if len(line) < 80 and '$' not in line:
                                job_data['ubicacion'] = line
                                break
                    
                    # Extraer empresa (buscar enlaces a bolsa de trabajo o texto antes de ubicación)
                    try:
                        empresa_links = card.find_elements(By.CSS_SELECTOR, "a[href*='bolsa-de-trabajo']")
                        if empresa_links:
                            emp_text = empresa_links[0].text.strip()
                            if emp_text and len(emp_text) > 2:
                                job_data['empresa'] = emp_text
                    except:
                        pass
                    
                except:
                    pass
                
                # Extraer descripción del panel derecho
                try:
                    # Buscar sección de descripción
                    desc_elem = driver.find_elements(By.XPATH, "//h2[contains(text(),'Descripción')]/following::*[1]")
                    if desc_elem:
                        job_data['descripcion'] = desc_elem[0].text[:3000]
                    else:
                        # Buscar cualquier bloque grande de texto en la parte derecha
                        all_p = driver.find_elements(By.TAG_NAME, "p")
                        for p in all_p:
                            txt = p.text.strip()
                            if len(txt) > 200:
                                job_data['descripcion'] = txt[:3000]
                                break
                except:
                    pass
                
                if not job_data['descripcion']:
                    job_data['descripcion'] = f"Empleo: {titulo} - {job_data['empresa']} - {job_data['ubicacion']}"
                
                jobs.append({
                    'titulo': titulo,
                    'url': driver.current_url,
                    'data': job_data
                })
                
            except Exception as e:
                debug_print(f"Error en empleo {idx}: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        debug_print(f"Error en extract_jobs_from_listing: {e}")
        return []


def extract_job_data_from_card(driver, job_title):
    """
    Extrae información de un empleo directamente de la página de listado
    sin necesidad de navegar (fallback si no se puede obtener URL)
    """
    try:
        # Buscar el h2 con el título
        h2_elements = driver.find_elements(By.TAG_NAME, "h2")
        
        for h2 in h2_elements:
            if h2.text.strip() == job_title:
                # Encontrar el contenedor padre de la tarjeta
                parent = h2
                for _ in range(5):  # Subir hasta 5 niveles
                    try:
                        parent = parent.find_element(By.XPATH, "./..")
                        card_text = parent.text
                        
                        # Si el texto tiene suficiente contenido, es la tarjeta
                        if len(card_text) > 100:
                            # Extraer salario
                            salario = "No especificado"
                            salary_match = re.search(r'\$\s*[\d,]+(?:\s*-\s*\$?\s*[\d,]+)?\s*(?:Mensual)?', card_text)
                            if salary_match:
                                salario = salary_match.group(0).strip()
                            
                            # Extraer empresa (buscar enlace a bolsa-de-trabajo)
                            empresa = "Confidencial"
                            try:
                                empresa_link = parent.find_element(By.CSS_SELECTOR, "a[href*='bolsa-de-trabajo']")
                                empresa = empresa_link.text.strip()
                            except:
                                if "confidencial" in card_text.lower():
                                    empresa = "Confidencial"
                            
                            # Extraer ubicación
                            ubicacion = "México"
                            estados = ["Ciudad de México", "Nuevo León", "Jalisco", "Estado de México",
                                      "Querétaro", "Guanajuato", "Puebla", "Veracruz", "Coahuila",
                                      "Tamaulipas", "Chihuahua", "Baja California", "Sonora",
                                      "Quintana Roo", "Yucatán", "Nayarit", "Monterrey", "Guadalajara"]
                            for estado in estados:
                                if estado in card_text:
                                    ubicacion = estado
                                    break
                            
                            return {
                                'titulo': job_title,
                                'empresa': empresa,
                                'ubicacion': ubicacion,
                                'salario': salario,
                                'descripcion': card_text[:2000]  # Usar texto de la tarjeta como descripción básica
                            }
                    except:
                        continue
                break
        
        return None
    except:
        return None

def extract_job_details(driver, job_url):
    """Extrae los detalles completos de un empleo"""
    try:
        driver.get(job_url)
        time.sleep(1)
        
        # Esperar por el título
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except:
            debug_print("Timeout esperando h1")
        
        # Título
        titulo = ""
        try:
            titulo = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            titulo = "Título no disponible"
        
        # Empresa
        empresa = "Confidencial"
        try:
            # Buscar enlace a empresa
            empresa_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/bolsa-de-trabajo-']")
            for link in empresa_links:
                text = link.text.strip()
                if text and len(text) > 2:
                    empresa = text
                    break
            
            # Si no encontró, buscar "Empresa confidencial" en el texto
            if empresa == "Confidencial":
                page_source = driver.page_source
                if "confidencial" in page_source.lower():
                    empresa = "Confidencial"
        except:
            pass
        
        # Ubicación - buscar estados/ciudades de México
        ubicacion = "México"
        try:
            page_text = driver.page_source
            estados_mx = [
                "Ciudad de México", "Nuevo León", "Jalisco", "Estado de México",
                "Querétaro", "Guanajuato", "Puebla", "Chihuahua", "Baja California",
                "Coahuila", "Tamaulipas", "Veracruz", "Sonora", "Sinaloa",
                "Yucatán", "Quintana Roo", "San Luis Potosí", "Aguascalientes",
                "Morelos", "Michoacán", "Oaxaca", "Hidalgo", "Tabasco",
                "Monterrey", "Guadalajara", "Tijuana", "Mérida", "León",
                "Cancún", "Toluca", "Mexicali", "Hermosillo", "Saltillo"
            ]
            
            for estado in estados_mx:
                if estado in page_text:
                    ubicacion = estado
                    break
        except:
            pass
        
        # Salario
        salario = "No especificado"
        try:
            page_text = driver.page_source
            # Buscar patrones como: $15,000 - $20,000 Mensual
            salary_match = re.search(r'\$\s*[\d,]+(?:\s*-\s*\$?\s*[\d,]+)?\s*(?:Mensual|MXN|mensual)?', page_text)
            if salary_match:
                salario = salary_match.group(0).strip()
        except:
            pass
        
        # Descripción - buscar contenido sustancial
        descripcion = "Descripción no disponible"
        try:
            # Intentar varios selectores para la descripción
            desc_found = False
            
            # Buscar divs con contenido largo
            all_divs = driver.find_elements(By.TAG_NAME, "div")
            best_text = ""
            
            for div in all_divs:
                try:
                    text = div.text.strip()
                    # Buscar texto que parezca descripción de empleo
                    if len(text) > 200 and len(text) < 10000:
                        # Verificar que tenga características de descripción
                        keywords = ["requisitos", "experiencia", "actividades", "funciones", 
                                   "ofrecemos", "habilidades", "conocimientos", "perfil",
                                   "responsabilidades", "beneficios"]
                        has_keyword = any(kw in text.lower() for kw in keywords)
                        
                        if has_keyword and len(text) > len(best_text):
                            best_text = text
                            desc_found = True
                except:
                    continue
            
            if desc_found:
                descripcion = best_text[:8000]
            else:
                # Fallback: usar el body text
                try:
                    body_text = driver.find_element(By.TAG_NAME, "body").text
                    if len(body_text) > 500:
                        descripcion = body_text[:5000]
                except:
                    pass
                    
        except Exception as e:
            debug_print(f"Error extrayendo descripción: {e}")
        
        return {
            "titulo": titulo,
            "empresa": empresa,
            "ubicacion": ubicacion,
            "salario": salario,
            "descripcion": descripcion,
        }
        
    except Exception as e:
        debug_print(f"Error extrayendo detalles: {str(e)}")
        return None

def scrape_categoria(driver, nombre_cat, url_cat, cat_index, total_cats):
    """Scrape una categoría completa"""
    global total_jobs_scraped, jobs_this_session, EMPLEOS, HASHES_GLOBALES, current_category
    
    current_category = nombre_cat
    
    print(f"\n{'='*80}")
    print(f"PROCESANDO CATEGORÍA {cat_index}/{total_cats}: {nombre_cat}")
    print(f"{'='*80}")
    
    # Obtener total de páginas
    total_paginas = obtener_total_paginas(driver, url_cat)
    print(f"Encontradas {total_paginas} páginas para {nombre_cat}")
    print("Comenzando extracción de empleos...")
    
    cat_jobs = 0
    pagina = 1
    consecutive_empty = 0
    
    while pagina <= total_paginas and consecutive_empty < 3:
        url = f"{COUNTRY_CONFIG['base_url']}/empleos/{url_cat}/?page={pagina}"
        
        print(f"\nProcesando página {pagina}/{total_paginas} de {nombre_cat}", flush=True)
        debug_print(f"URL: {url}")
        
        try:
            driver.get(url)
            time.sleep(1)
            
            # Verificar si hay resultados
            page_text = driver.page_source.lower()
            if "no encontramos" in page_text or "sin resultados" in page_text:
                print("No se encontraron más resultados")
                break
            
            # Extraer empleos directamente de las tarjetas
            jobs_found = extract_jobs_from_listing(driver)
            
            if len(jobs_found) == 0:
                # Fallback: extraer solo los títulos y datos básicos
                debug_print("Intentando extracción de datos básicos de tarjetas...")
                
                h2_elements = driver.find_elements(By.TAG_NAME, "h2")
                job_titles = []
                
                for h2 in h2_elements:
                    try:
                        text = h2.text.strip()
                        if text and len(text) > 3 and len(text) < 200:
                            skip_texts = ['resultados', 'Ordenar', 'Relevancia', 'Fecha', 
                                          'Limpiar', 'Aplicar', 'Buscar', 'OCC', 'Candidatos',
                                          'Reclutadores', 'Empleos por', 'Consigue un empleo',
                                          'Llegaste al final']
                            if not any(skip in text for skip in skip_texts):
                                job_titles.append(text)
                    except:
                        continue
                
                if job_titles:
                    print(f"{len(job_titles)} empleos encontrados (fallback):", flush=True)
                    for idx, titulo in enumerate(job_titles[:20]):
                        print(f"{idx} - {titulo[:60]}", flush=True)
                        job_data = extract_job_data_from_card(driver, titulo)
                        if job_data:
                            jobs_found.append({
                                'titulo': job_data['titulo'],
                                'url': f"{url}#empleo-{len(jobs_found)}",
                                'data': job_data
                            })
            
            if len(jobs_found) == 0:
                consecutive_empty += 1
                print(f"No se encontraron empleos en la página {pagina}", flush=True)
                pagina += 1
                continue
            
            consecutive_empty = 0
            
            for i, job_info in enumerate(jobs_found):
                try:
                    titulo = job_info.get('titulo', 'Sin título')
                    job_url = job_info.get('url', '')
                    
                    # Si tenemos datos pre-extraídos, usarlos
                    if 'data' in job_info:
                        details = job_info['data']
                    elif job_url and '/empleo/' in job_url:
                        # Navegar a la página de detalle
                        driver = recrear_driver_si_necesario(driver)
                        details = extract_job_details(driver, job_url)
                        if not details:
                            debug_print(f"{i} - No se pudieron extraer detalles")
                            continue
                    else:
                        # Usar datos básicos
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
                        continue
                    
                    EMPLEOS.append({
                        "Id Interno": f"OCC-{url_cat[:20]}-{pagina}-{i+1}",
                        "titulo": details.get("titulo", titulo),
                        "descripcion": details.get("descripcion", ""),
                        "Empresa": empresa,
                        "Fuente": "OCC Mundial",
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
    print(f"Iniciando scraping de OCC Mundial - {COUNTRY_CONFIG['name']}...")
    print(f"URL base: {COUNTRY_CONFIG['base_url']}")
    print(f"Total categorías: {len(CATEGORIAS)}")
    
    if args.debug:
        print("Modo debug activado - Se mostrarán mensajes detallados")
    
    # Cargar hashes existentes
    print("\nCargando hashes existentes para evitar duplicados...")
    timestamp = date.today().strftime("%Y%m%d")
    for nombre_cat, url_cat in CATEGORIAS:
        cat_safe = re.sub(r'[^a-zA-Z0-9]', '_', nombre_cat)[:50]
        archivo = f"output_jobs/OCC_Mundial_{cat_safe}_{timestamp}.json"
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
        for i, (nombre, _) in enumerate(CATEGORIAS):
            if args.start_from.lower() in nombre.lower():
                start_index = i
                print(f"Iniciando desde categoría: {nombre}")
                break
    
    categories_to_process = CATEGORIAS[start_index:]
    print(f"\nProcesando {len(categories_to_process)} categorías...")
    
    driver = create_driver()
    
    try:
        for idx, (nombre_cat, url_cat) in enumerate(categories_to_process):
            try:
                scrape_categoria(driver, nombre_cat, url_cat, start_index + idx + 1, len(CATEGORIAS))
            except Exception as e:
                print(f"Error crítico en categoría {nombre_cat}: {str(e)}")
                print("Intentando continuar con la siguiente categoría...")
                driver = recrear_driver_si_necesario(driver)
                continue
            
            time.sleep(random.uniform(1, 2))
    finally:
        try:
            driver.quit()
        except:
            pass
    
    print(f"\nSCRAPING COMPLETADO EXITOSAMENTE!")
    print(f"Resumen de la sesión:")
    print(f"   - Jobs recolectados en esta sesión: {jobs_this_session}")
    print(f"   - Total de jobs recolectados: {total_jobs_scraped}")
    print(f"   - Categorías procesadas: {len(categories_to_process)}")
    print(f"   - Todos los datos guardados en: output_jobs/")
    print(f"{'='*60}\n")