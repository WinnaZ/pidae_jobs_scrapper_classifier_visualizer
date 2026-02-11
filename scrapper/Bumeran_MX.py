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
    driver.implicitly_wait(3)
    
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
    """Verifica si una página existe y tiene empleos"""
    try:
        url = f"{url_base}.html?page={page_num}"
        driver.get(url)
        time.sleep(1.5)
        
        # Buscar enlaces a empleos
        job_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/empleos/']")
        
        valid_jobs = 0
        for link in job_links:
            try:
                href = link.get_attribute("href")
                if not href or '/empleos/' not in href:
                    continue
                
                if 'empleos-area' in href or '-pagina-' in href or '?page=' in href:
                    continue
                
                if not href.endswith('.html'):
                    continue
                
                parts = href.split('/empleos/')
                if len(parts) > 1:
                    slug = parts[1].replace('.html', '')
                    
                    if len(slug) < 15 or '-' not in slug:
                        continue
                    
                    last_part = slug.split('-')[-1]
                    if not last_part.isdigit():
                        continue
                    
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
    url_base = f"{COUNTRY_CONFIG['base_url']}/empleos-area-{url_categoria}"
    
    print(f"Analizando categoría: {url_categoria}")
    
    # Verificar primera página
    if not verificar_pagina_existe(driver, url_base, 1):
        print("No se encontraron empleos en la primera página")
        return 0
    
    # Fase 1: Encontrar límite superior con saltos de 50
    ultima_valida = 1
    right = 50
    
    while True:
        if verificar_pagina_existe(driver, url_base, right):
            ultima_valida = right
            right += 50
        else:
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
                                    'url': href
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
                            # Try to find parent link
                            parent = h2
                            url_found = None
                            for _ in range(5):
                                try:
                                    parent = parent.find_element(By.XPATH, "./..")
                                    links = parent.find_elements(By.CSS_SELECTOR, "a[href*='/empleos/']")
                                    for link in links:
                                        href = link.get_attribute("href")
                                        if href and href.endswith('.html') and '/empleos/' in href:
                                            url_found = href
                                            break
                                    if url_found:
                                        break
                                except:
                                    break
                            
                            if url_found:
                                job_cards.append({
                                    'titulo': texto,
                                    'url': url_found
                                })
                except:
                    continue
        
        print(f"{len(job_cards)} empleos encontrados")
        for idx, job in enumerate(job_cards[:25]):
            print(f"  {idx} - {job['titulo'][:60]}")
        
        return job_cards[:25]
        
    except Exception as e:
        debug_print(f"Error en extract_jobs_from_listing: {e}")
        return []
def extract_sections_from_text(text):
    """
    Busca encabezados comunes y separa 'responsabilidades' y 'requisitos' del resto.
    Devuelve dict con keys: descripcion, responsabilidades, requisitos
    """
    if not text:
        return {
            "descripcion": "",
            "responsabilidades": "No especificado",
            "requisitos": "No especificado"
        }

    # Normalizar saltos
    text = re.sub(r'\r\n?', '\n', text).strip()
    # Patrón que detecta encabezados al inicio de línea
    header_re = re.compile(
        r'(?im)^(responsabilidades|responsabilidad|funciones|responsabilidades y funciones|requisitos|requerimientos|perfil)[\s:─\-]*$'
    )

    matches = list(header_re.finditer(text))
    result = {
        "descripcion": text,
        "responsabilidades": "No especificado",
        "requisitos": "No especificado"
    }

    if matches:
        # Texto antes del primer encabezado -> descripción principal
        first = matches[0]
        before = text[: first.start()].strip()
        result["descripcion"] = before if before else text.strip()

        # Para cada encabezado, extraer su bloque hasta el siguiente encabezado
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            heading = m.group(1).lower()
            content = text[start:end].strip()
            # Guardar según heading
            if "requis" in heading:
                if content:
                    result["requisitos"] = content
            else:
                # cualquier heading no-req lo consideramos responsabilidades/funciones
                if content:
                    # si ya existe, concatenar con doble salto para legibilidad
                    if result["responsabilidades"] != "No especificado":
                        result["responsabilidades"] += "\n\n" + content
                    else:
                        result["responsabilidades"] = content
    else:
        # fallback: buscar inline "Responsabilidades:" o "Requisitos:" en el texto
        m_resp = re.search(r'(?is)Responsabilidad(?:es)?[:\s\-]+\n?\s*([\s\S]{20,2000})', text)
        if m_resp:
            result["responsabilidades"] = m_resp.group(1).strip()
        m_req = re.search(r'(?is)(Requisitos|Requerimientos)[:\s\-]+\n?\s*([\s\S]{20,2000})', text)
        if m_req:
            result["requisitos"] = m_req.group(2).strip()
        # mantener la descripcion como el texto original si no hubo matches

    # limpieza final: normalizar saltos múltiples
    for k in result:
        if isinstance(result[k], str):
            result[k] = re.sub(r'\n{3,}', '\n\n', result[k]).strip()

    return result
import re

def normalize_single_line(text, stop_headers=None):
    """
    Normaliza una descripción multi-línea / con viñetas a UN único párrafo.
    - elimina secciones finales como "Palabras clave", "OFRECEMOS", "BENEFICIOS"
    - convierte viñetas en oraciones
    - colapsa saltos de línea y espacios
    - elimina oraciones duplicadas consecutivas o repetidas exactas
    - retorna una sola línea que termina en punto.
    """
    if not text:
        return ""

    s = text

    # 0) Normalize CRLF
    s = re.sub(r'\r\n?', '\n', s)

    # 1) Remove trailing sections that start with common headers (case-insensitive)
    if stop_headers is None:
        stop_headers = ['palabras clave', 'ofrecemos', 'beneficios', 'contacto', 'postular', 'reclutamiento']
    # build pattern like (?is)\b(?:palabras clave|ofrecemos|beneficios)\b.*$
    pat = r'(?is)\b(?:' + '|'.join(re.escape(h) for h in stop_headers) + r')\b.*$'
    s = re.sub(pat, '', s).strip()

    # 2) Remove obvious timestamps like "Hace 12 horas (actualizada)"
    s = re.sub(r'(?is)\bhace\s+\d+\s+\w+.*$', '', s).strip()

    # 3) Convert bullet marks to sentence separators
    s = s.replace('•', '. ')
    s = s.replace('·', '. ')
    s = s.replace(' - ', '. ')
    s = s.replace('•\u200b', '. ')  # invisible bullet varieties

    # 4) Keep headings separated: replace "Resumen del Puesto" etc with markers
    headings = ['Resumen del Puesto', 'Responsabilidades', 'Funciones', 'Requisitos', 'Detalles de la oferta laboral']
    for h in headings:
        s = re.sub(r'(?i)\b' + re.escape(h) + r'\b', '\n\n' + h + '\n', s)

    # 5) Collapse remaining newlines into spaces
    s = re.sub(r'[\n\r]+', ' ', s)

    # 6) Split into sentences (simple heuristic), trim, and deduplicate exact sentences while preserving order
    # Split on . ! ? followed by space (also treat as sentence end if followed by end-of-string)
    parts = re.split(r'(?<=[\.\!\?])\s+', s)
    clean_parts = []
    seen = set()
    for p in parts:
        p = p.strip()
        if not p:
            continue
        # Ensure it ends with punctuation
        if not re.search(r'[\.\!\?]$', p):
            p = p + '.'
        # Deduplicate exact sentences
        key = p.lower()
        if key in seen:
            continue
        seen.add(key)
        clean_parts.append(p)

    # 7) join into one line
    result = ' '.join(clean_parts)
    result = re.sub(r'\s{2,}', ' ', result).strip()

    # 8) Remove accidental repeated phrases (if a phrase appears twice contiguous inside the line)
    # simple: if the first 5 words repeated twice, remove second occurrence
    words = result.split()
    if len(words) > 10:
        first5 = ' '.join(words[:5])
        if first5 in result[len(first5):len(first5)*2+10]:
            # remove second occurrence naive
            result = result.replace(first5, '', 1).strip()
            result = re.sub(r'\s{2,}', ' ', result)

    # final punctuation
    if result and not re.search(r'[\.\!\?]$', result):
        result += '.'

    return result


def extract_job_details(driver, job_url):
    """
    Extrae detalles completos de un empleo
    IMPROVED: Better waiting, scrolling, and selector strategies for SPA
    """
    try:
        driver.get(job_url)
        
        # CRITICAL: Wait for React SPA to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            time.sleep(2)  # Extra wait for dynamic content
        except:
            debug_print(f"Timeout esperando contenido")
            return None
        
        # Scroll to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        
        # Get full page text for fallback parsing
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # ===== TÍTULO =====
        titulo = ""
        try:
            titulo = driver.find_element(By.TAG_NAME, "h1").text.strip()
        except:
            titulo = "Título no disponible"
        
        # ===== EMPRESA =====
        empresa = "NA/NA"
        try:
            company_selectors = [
                "a[href*='bolsa-trabajo']",
                "a[href*='/empresas/']",
                "[data-testid*='company']",
                ".company-name",
                "[class*='company']",
                "[class*='empresa']",
                "span[class*='CompanyName']",
                "div[class*='CompanyName']"
            ]
            
            for selector in company_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    text = elem.text.strip()
                    if text and len(text) > 2 and len(text) < 100:
                        if text.lower() not in ['ver empresa', 'postular', 'guardar', 'compartir']:
                            empresa = text
                            break
                except:
                    continue
            
            # Fallback: Parse from page text
            if empresa == "NA/NA":
                lines = [l.strip() for l in page_text.split('\n') if l.strip()]
                for i, line in enumerate(lines):
                    if 'empresa' in line.lower() or 'compañía' in line.lower():
                        for j in range(1, 4):
                            if i + j < len(lines):
                                candidate = lines[i + j]
                                if candidate and len(candidate) > 2 and len(candidate) < 100:
                                    skip_terms = ['méxico', 'cdmx', 'postula', 'ver', 'guardar', 'compartir']
                                    if not any(term in candidate.lower() for term in skip_terms):
                                        empresa = candidate
                                        break
                        if empresa != "NA/NA":
                            break
        except:
            pass
        
        # ===== UBICACIÓN =====
        ubicacion = "México"
        try:
            ubicaciones = ['CDMX', 'Ciudad de México', 'Jalisco', 'Nuevo León',
                          'Monterrey', 'Guadalajara', 'Estado de México', 'Puebla',
                          'Querétaro', 'Tijuana', 'Veracruz', 'Chihuahua', 'Sonora',
                          'Cancún', 'Mérida', 'Aguascalientes', 'Guanajuato']
            
            location_selectors = [
                "[data-testid*='location']",
                "[class*='location']",
                "[class*='ubicacion']",
                "[class*='Ubicacion']",
                "[class*='Location']",
                "svg + span"
            ]
            
            for selector in location_selectors:
                try:
                    elems = driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elems:
                        text = elem.text.strip()
                        for ub in ubicaciones:
                            if ub.lower() in text.lower():
                                ubicacion = text
                                break
                        if ubicacion != "México":
                            break
                    if ubicacion != "México":
                        break
                except:
                    continue
            
            if ubicacion == "México":
                for ub in ubicaciones:
                    if ub in page_text:
                        for line in page_text.split('\n'):
                            if ub in line and len(line) < 100:
                                ubicacion = line.strip()
                                break
                        if ubicacion != "México":
                            break
        except:
            pass
        
        # ===== SALARIO =====
        salario = "No especificado"
        try:
            salary_patterns = [
                r'\$\s*[\d,]+(?:\.\d{2})?\s*(?:-|a)\s*\$?\s*[\d,]+',
                r'\$\s*[\d,]+\s+(?:MXN|pesos|mensual)',
                r'[\d,]+\s*[-a]\s*[\d,]+\s+(?:MXN|pesos)',
            ]
            
            for pattern in salary_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    salario = match.group(0).strip()
                    break
            
            if salario == "No especificado":
                salary_selectors = [
                    "[data-testid*='salary']",
                    "[class*='salary']",
                    "[class*='salario']"
                ]
                for selector in salary_selectors:
                    try:
                        elem = driver.find_element(By.CSS_SELECTOR, selector)
                        text = elem.text.strip()
                        if '$' in text or 'mensual' in text.lower():
                            salario = text
                            break
                    except:
                        continue
        except:
            pass
        
        # ===== DESCRIPCIÓN =====
        descripcion = ""
        try:
            desc_selectors = [
                "[data-testid*='description']",
                "[class*='description']",
                "[class*='descripcion']",
                "[class*='JobDescription']",
                "article",
                "section[class*='detail']"
            ]
            
            for selector in desc_selectors:
                try:
                    elem = driver.find_element(By.CSS_SELECTOR, selector)
                    text = elem.text.strip()
                    if len(text) > 100:
                        descripcion = text
                        break
                except:
                    continue
            
            # Fallback: collect paragraphs
            if not descripcion or len(descripcion) < 100:
                paragraphs = driver.find_elements(By.TAG_NAME, "p")
                desc_parts = []
                for p in paragraphs:
                    text = p.text.strip()
                    if len(text) > 50:
                        desc_parts.append(text)
                if desc_parts:
                    descripcion = '\n\n'.join(desc_parts[:10])
            
            # Fallback 2: parse page text structure
            if not descripcion or len(descripcion) < 100:
                lines = page_text.split('\n')
                collecting = False
                collected_lines = []
                
                for line in lines:
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in ['descripción', 'description', 'sobre el puesto']):
                        collecting = True
                        continue
                    if collecting and any(keyword in line_lower for keyword in ['requisitos', 'postular', 'contacto']):
                        break
                    if collecting and line.strip():
                        collected_lines.append(line.strip())
                
                if collected_lines:
                    descripcion = '\n'.join(collected_lines[:50])
        except:
            pass
        
        if not descripcion or len(descripcion) < 50:
            descripcion = f"{titulo} - {empresa} - {ubicacion}"
        
        if len(descripcion) > 4000:
            descripcion = descripcion[:4000]
        
        sections = extract_sections_from_text(descripcion)
        descripcion_principal = sections["descripcion"]
        responsabilidades_text = sections["responsabilidades"]
        requisitos_text = sections["requisitos"]
        descripcion = normalize_single_line(descripcion_principal)


        return {
            'titulo': titulo,
            'empresa': empresa,
            'ubicacion': ubicacion,
            'salario': salario,
            'descripcion': descripcion,
            'responsabilidades': responsabilidades_text,
            'requisitos': requisitos_text
        }
    
    except Exception as e:
        debug_print(f"Error en extract_job_details: {e}")
        return None

def scrape_categoria(driver, nombre_cat, url_cat, cat_index, total_cats):
    """Scrape una categoría completa"""
    seen_job_urls = set()
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

                    if not job_url:
                        print(f"  {i+1}/{len(jobs_found)}: No URL para {titulo[:50]}, omitiendo")
                        continue

                    if job_url in seen_job_urls:
                        debug_print(f"  {i+1}: URL repetida, saltando")
                        continue

                    seen_job_urls.add(job_url)

                    driver = recrear_driver_si_necesario(driver)
                    details = extract_job_details(driver, job_url)
                    
                    if not details:
                        print(f"    ^ No se pudieron extraer detalles, omitiendo")
                        continue
                    
                    # Hash = descripcion + ubicacion + empresa
                    ubicacion = details.get("ubicacion", "México")
                    empresa = details.get("empresa", "NA/NA")
                    hash_content = (
                        job_url + "|" +
                        details.get("descripcion", titulo) + "|" +
                        ubicacion + "|" +
                        empresa
                    )
                    hash_empleo = calcular_hash(hash_content)
                    
                    if hash_empleo in HASHES_GLOBALES:
                        print(f"    ^ [DUPLICADO]")
                        continue
                    
                    EMPLEOS.append({
                        "Id Interno": f"BUM-MX-{url_cat[:15]}-{pagina}-{i+1}",
                        "titulo": details.get("titulo", titulo),
                        "descripcion": details.get("descripcion", ""),
                        "responsabilidades": details.get("responsabilidades", "No especificado"),
                        "requisitos": details.get("requisitos", "No especificado"),
                        "Empresa": empresa,
                        "Fuente": "Bumeran México",
                        "Tipo Portal": "Tradicional",
                        "url": job_url,
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
                    # from pprint import pprint
                    # pprint(EMPLEOS)
                    
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