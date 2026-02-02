#!/usr/bin/env python3
"""
InfoJobs Brasil Scraper
https://www.infojobs.com.br/
Infinite scroll handling
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
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

sys.stdout.reconfigure(line_buffering=True)

# =============================================================================
# CONFIGURACIÓN
# =============================================================================
COUNTRY_CONFIG = {
    "code": "BR",
    "name": "Brasil",
    "base_url": "https://www.infojobs.com.br",
    "color": '\033[0;36m',  # Cyan para InfoJobs
}

COLOR = COUNTRY_CONFIG["color"]
RESET = '\033[0m'

_original_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    colored_args = [f"{COLOR}{arg}{RESET}" if isinstance(arg, str) else arg for arg in args]
    _original_print(*colored_args, **kwargs)
builtins.print = print

parser = argparse.ArgumentParser(description='Script de scraping para InfoJobs Brasil')
parser.add_argument('--debug', action='store_true', help='Activar mensajes de debug')
parser.add_argument('--start-from', type=str, help='Iniciar desde una categoría específica')
parser.add_argument('--max-scroll', type=int, default=50, help='Máximo de scrolls por categoría')
args = parser.parse_args()

def debug_print(*mensaje, **kwargs):
    if args.debug:
        _original_print(f"{COLOR}{' '.join(map(str, mensaje))}{RESET}", flush=True, **kwargs)

# =============================================================================
# CATEGORÍAS - Extraídas de infojobs.com.br
# =============================================================================
CATEGORIAS = [
    # Columna izquierda (ordenadas por cantidad)
    ("Comercial, Vendas", "comercial-vendas"),
    ("Alimentação / Gastronomia", "alimentacao-gastronomia"),
    ("Administração", "administracao"),
    ("Industrial, Produção, Fábrica", "industrial-producao-fabrica"),
    ("Saúde", "saude"),
    ("Segurança", "seguranca"),
    ("Transportes", "transportes"),
    ("Engenharia", "engenharia"),
    ("Educação, Ensino, Idiomas", "educacao-ensino-idiomas"),
    ("Jurídica", "juridica"),
    ("Qualidade", "qualidade"),
    ("Estética", "estetica"),
    ("Arquitetura, Decoração, Design", "arquitetura-decoracao-design"),
    ("Meio Ambiente, Ecologia", "meio-ambiente-ecologia"),
    ("Auditoria", "auditoria"),
    ("Artes", "artes"),
    ("Ciências, Pesquisa", "ciencias-pesquisa"),
    # Columna derecha
    ("Logística", "logistica"),
    ("Construção, Manutenção", "construcao-manutencao"),
    ("Serviços Gerais", "servicos-gerais"),
    ("Contábil, Finanças, Economia", "contabil-financas-economia"),
    ("Telemarketing", "telemarketing"),
    ("Informática, TI, Telecomunicações", "informatica-ti-telecomunicacoes"),
    ("Recursos Humanos", "recursos-humanos"),
    ("Marketing", "marketing"),
    ("Compras", "compras"),
    ("Hotelaria, Turismo", "hotelaria-turismo"),
    ("Agricultura, Pecuária, Veterinária", "agricultura-pecuaria-veterinaria"),
    ("Moda", "moda"),
    ("Química, Petroquímica", "quimica-petroquimica"),
    ("Comunicação, TV, Cinema", "comunicacao-tv-cinema"),
    ("Comércio Exterior, Importação, Exportação", "comercio-exterior-importacao-exportacao"),
    ("Cultura, Lazer, Entretenimento", "cultura-lazer-entretenimento"),
    ("Serviço Social e Comunitário", "servico-social-e-comunitario"),
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

def guardar_datos_incremental(empleos, categoria, archivo_base="output_jobs/InfoJobs_BR"):
    os.makedirs("output_jobs", exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d")
    nombre_archivo = f"{archivo_base}_{categoria}_{timestamp}.json"
    
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

def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Disable images for speed
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2
    }
    options.add_experimental_option("prefs", prefs)
    options.page_load_strategy = 'eager'
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    driver.set_page_load_timeout(5)
    driver.implicitly_wait(1)
    
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

def build_url(slug):
    """Construye URL de categoría"""
    return f"https://www.infojobs.com.br/empregos-de-{slug}.aspx"

def extract_job_urls_from_page(driver):
    """Extrae URLs de vagas de la página actual"""
    job_urls = []
    
    # Selectores posibles para links de vagas
    selectors = [
        "a[href*='/vaga-de-']",
        "a[href*='/emprego-de-']",
        ".vagaTitle a",
        ".job-title a",
        "h2 a[href*='infojobs']",
        "a.vaga-link"
    ]
    
    for selector in selectors:
        try:
            links = driver.find_elements(By.CSS_SELECTOR, selector)
            for link in links:
                href = link.get_attribute("href")
                if href and 'infojobs.com.br' in href and ('/vaga-de-' in href or '/emprego-de-' in href):
                    titulo = link.text.strip() or link.get_attribute("title") or ""
                    if href not in [j['url'] for j in job_urls]:
                        job_urls.append({
                            'url': href,
                            'titulo': titulo[:100] if titulo else "Sin título"
                        })
            if job_urls:
                break
        except:
            continue
    
    return job_urls

def scroll_and_load(driver, max_scrolls=50):
    """Hace scroll infinito y carga más vagas"""
    all_jobs = []
    seen_urls = set()
    no_new_count = 0
    
    for scroll_num in range(max_scrolls):
        # Extraer jobs actuales
        current_jobs = extract_job_urls_from_page(driver)
        new_jobs = [j for j in current_jobs if j['url'] not in seen_urls]
        
        if new_jobs:
            for job in new_jobs:
                seen_urls.add(job['url'])
                all_jobs.append(job)
            print(f"  Scroll {scroll_num + 1}: +{len(new_jobs)} vagas (total: {len(all_jobs)})")
            no_new_count = 0
        else:
            no_new_count += 1
            debug_print(f"  Scroll {scroll_num + 1}: sin nuevas vagas ({no_new_count}/3)")
        
        # Si 3 scrolls sin nuevos, terminar
        if no_new_count >= 3:
            print(f"  Fin del scroll (sin nuevas vagas)")
            break
        
        # Scroll down
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.3)  # Pequeña espera para cargar
        except:
            break
    
    return all_jobs

def extract_job_details(driver, job_url):
    """Extrae detalles de una vaga"""
    try:
        try:
            driver.get(job_url)
        except:
            driver.execute_script("window.stop();")
        
        details = {
            'titulo': '',
            'empresa': 'Confidencial',
            'ubicacion': 'Brasil',
            'salario': 'A combinar',
            'descripcion': ''
        }
        
        # Título - h1
        try:
            h1 = driver.find_element(By.TAG_NAME, "h1")
            details['titulo'] = h1.text.strip()
        except:
            pass
        
        # Empresa
        for sel in ["[class*='ompany']", "[class*='mpresa']", ".company-name", "[class*='Company']"]:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                txt = elem.text.strip()
                if txt and 2 < len(txt) < 100:
                    details['empresa'] = txt
                    break
            except:
                continue
        
        # Ubicación
        for sel in ["[class*='ocation']", "[class*='ocal']", "[class*='city']", ".location"]:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                txt = elem.text.strip()
                if txt and len(txt) > 2:
                    details['ubicacion'] = txt
                    break
            except:
                continue
        
        # Salario
        for sel in ["[class*='alario']", "[class*='alary']", ".salary"]:
            try:
                elem = driver.find_element(By.CSS_SELECTOR, sel)
                txt = elem.text.strip()
                if txt and ('R$' in txt or 'combinar' in txt.lower()):
                    details['salario'] = txt
                    break
            except:
                continue
        
        # Descripción
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            details['descripcion'] = body.text[:4000]
        except:
            pass
        
        return details
        
    except Exception as e:
        debug_print(f"Error extrayendo: {str(e)}")
        return None

def scrape_categoria(driver, nombre_cat, slug_cat, cat_index, total_cats):
    """Scrape una categoría completa con infinite scroll"""
    global total_jobs_scraped, jobs_this_session, EMPLEOS, HASHES_GLOBALES, current_category
    
    current_category = slug_cat
    
    print(f"\n{'='*80}")
    print(f"PROCESANDO CATEGORÍA {cat_index}/{total_cats}: {nombre_cat}")
    print(f"{'='*80}")
    
    url = build_url(slug_cat)
    print(f"URL: {url}")
    
    # Cargar página inicial
    try:
        try:
            driver.get(url)
        except:
            driver.execute_script("window.stop();")
    except Exception as e:
        print(f"Error cargando página: {e}")
        return 0
    
    # Scroll y cargar todas las vagas
    print("Haciendo scroll para cargar vagas...")
    jobs = scroll_and_load(driver, max_scrolls=args.max_scroll)
    
    if not jobs:
        print("No se encontraron vagas en esta categoría")
        return 0
    
    print(f"\n{len(jobs)} vagas encontradas. Extrayendo detalles...")
    
    cat_jobs = 0
    
    for i, job in enumerate(jobs):
        try:
            job_url = job.get('url', '')
            titulo = job.get('titulo', 'Sin título')
            
            if not job_url:
                continue
            
            print(f"  {i+1}/{len(jobs)}: {titulo[:50]}...")
            
            driver = recrear_driver_si_necesario(driver)
            
            details = extract_job_details(driver, job_url)
            
            if not details:
                details = {
                    'titulo': titulo,
                    'empresa': 'Confidencial',
                    'ubicacion': 'Brasil',
                    'salario': 'A combinar',
                    'descripcion': f"Vaga: {titulo} - Categoria: {nombre_cat}"
                }
            
            # Hash = descripcion + ubicacion + empresa
            ubicacion = details.get("ubicacion", "Brasil")
            empresa = details.get("empresa", "Confidencial")
            hash_content = details.get("descripcion", titulo) + "|" + ubicacion + "|" + empresa
            hash_empleo = calcular_hash(hash_content)
            
            if hash_empleo in HASHES_GLOBALES:
                print(f"    ^ [DUPLICADO]")
                continue
            
            EMPLEOS.append({
                "Id Interno": f"INFOJOBS-{slug_cat[:15]}-{i+1}",
                "titulo": details.get("titulo", titulo),
                "descripcion": details.get("descripcion", ""),
                "Empresa": empresa,
                "Fuente": "InfoJobs Brasil",
                "Tipo Portal": "Tradicional",
                "url": job_url,
                "Pais": COUNTRY_CONFIG["name"],
                "ubicacion": ubicacion,
                "salario": details.get("salario", "A combinar"),
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
    
    # Guardar al finalizar categoría
    print(f"\n{'='*60}")
    print(f"Categoría '{nombre_cat}' completada")
    print(f"Vagas en esta categoría: {cat_jobs}")
    print(f"Total acumulado: {total_jobs_scraped}")
    print(f"{'='*60}")
    
    if EMPLEOS:
        guardar_datos_incremental(EMPLEOS, slug_cat)
        EMPLEOS = []
    
    return cat_jobs

# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("="*60)
    print("INFOJOBS BRASIL SCRAPER")
    print("="*60)
    
    if args.debug:
        print("Modo debug activado")
    
    print(f"Max scrolls por categoría: {args.max_scroll}")
    
    # Cargar hashes existentes
    print("\nCargando hashes existentes...")
    for nombre, slug in CATEGORIAS:
        timestamp = date.today().strftime("%Y%m%d")
        archivo = f"output_jobs/InfoJobs_BR_{slug}_{timestamp}.json"
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
            if slug == args.start_from or nombre == args.start_from:
                start_index = i
                break
        print(f"Iniciando desde: {CATEGORIAS[start_index][0]}")
    
    # Crear driver
    print("\nIniciando navegador...")
    driver = create_driver()
    
    try:
        for idx, (nombre, slug) in enumerate(CATEGORIAS[start_index:], start_index + 1):
            try:
                scrape_categoria(driver, nombre, slug, idx, len(CATEGORIAS))
            except Exception as e:
                print(f"Error en categoría {nombre}: {e}")
                driver = recrear_driver_si_necesario(driver)
                continue
    
    finally:
        try:
            driver.quit()
        except:
            pass
    
    print(f"\n{'='*60}")
    print("SCRAPING COMPLETADO")
    print(f"Jobs esta sesión: {jobs_this_session}")
    print(f"Total jobs: {total_jobs_scraped}")
    print(f"{'='*60}")