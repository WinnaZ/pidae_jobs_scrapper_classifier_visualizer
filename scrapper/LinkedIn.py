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
from checkpoint_manager import CheckpointManager, LinkedInCheckpoint, get_resume_info

# Colores ANSI - Azul para LinkedIn
BLUE = '\033[0;34m'
RESET = '\033[0m'

_original_print = builtins.print
def print(*args, **kwargs):
    colored_args = [f"{BLUE}{arg}{RESET}" if isinstance(arg, str) else arg for arg in args]
    _original_print(*colored_args, **kwargs)
builtins.print = print

parser = argparse.ArgumentParser(description='Script de scraping para LinkedIn Jobs Argentina')
parser.add_argument('--debug', action='store_true', help='Activar mensajes de debug')
parser.add_argument('--start-from', type=str, help='Iniciar desde una categorÃ­a especÃ­fica')
args = parser.parse_args()

def debug_print(*mensaje, **kwargs):
    if args.debug:
        _original_print(f"{BLUE}{' '.join(map(str, mensaje))}{RESET}", **kwargs)

# LinkedIn Job Functions
AREAS = {
    "accounting": "acct",
    "administrative": "adm",
    "arts-design": "art",
    "business-development": "bd",
    "community-social-services": "css",
    "consulting": "cns",
    "education": "edu",
    "engineering": "eng",
    "entrepreneurship": "ent",
    "finance": "fin",
    "healthcare-services": "hea",
    "human-resources": "hr",
    "information-technology": "it",
    "legal": "lgl",
    "marketing": "mrkt",
    "media-communications": "med",
    "military-protective-services": "mil",
    "operations": "ops",
    "product-management": "prdt",
    "program-project-management": "ppm",
    "purchasing": "pur",
    "quality-assurance": "qa",
    "real-estate": "re",
    "research": "rsch",
    "sales": "sales",
    "support": "sup",
}

# Global variables
driver = None
checkpoint_manager = None
total_jobs_scraped = 0
jobs_this_session = 0
EMPLEOS = []
HASHES_GLOBALES = set()
current_area = ""
current_area_index = 0
current_page = 0
areas_completed = set()

def signal_handler(sig, frame):
    print(f"\n\nInterrupciÃ³n detectada (CTRL+C)")
    print("Guardando checkpoint para poder reanudar...")
    
    if checkpoint_manager:
        checkpoint_data = LinkedInCheckpoint.create_checkpoint_data(
            current_area_index, current_page, list(areas_completed), total_jobs_scraped
        )
        checkpoint_manager.save_checkpoint(checkpoint_data)
        print("Checkpoint guardado exitosamente")
    
    if EMPLEOS:
        print(f"Guardando {len(EMPLEOS)} empleos pendientes...")
        guardar_datos_incremental(EMPLEOS, current_area)
    
    if driver:
        try:
            driver.quit()
            print("Driver cerrado correctamente")
        except:
            pass
    
    print(f"Total empleos guardados: {total_jobs_scraped}")
    print("Hasta la prÃ³xima! Usa el mismo comando para reanudar.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def calcular_hash(texto):
    if not isinstance(texto, str):
        return None
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def guardar_datos_incremental(empleos, area, archivo_base="output_jobs/LinkedIn"):
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
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def verificar_sesion_activa(driver):
    try:
        driver.current_url
        return True
    except:
        return False

def recrear_driver_si_necesario(driver):
    if not verificar_sesion_activa(driver):
        print("SesiÃ³n perdida. Recreando driver...")
        try:
            driver.quit()
        except:
            pass
        return create_driver()
    return driver

def scroll_and_load_jobs(driver, max_jobs=50):
    last_count = 0
    attempts = 0
    
    while attempts < 15:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        try:
            btn = driver.find_element(By.CSS_SELECTOR, 'button.infinite-scroller__show-more-button, button[aria-label="Ver mÃ¡s empleos"]')
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(2)
        except:
            pass
        
        jobs = driver.find_elements(By.CSS_SELECTOR, 'div.base-card, div.job-search-card')
        current_count = len(jobs)
        
        debug_print(f"Jobs cargados: {current_count}")
        
        if current_count >= max_jobs or current_count == last_count:
            break
        
        last_count = current_count
        attempts += 1
    
    return current_count

def extract_job_details(driver, job_url):
    try:
        driver.get(job_url)
        time.sleep(2)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1, h2'))
        )
        
        try:
            titulo = driver.find_element(By.CSS_SELECTOR, 'h1.top-card-layout__title, h2.top-card-layout__title, h1').text.strip()
        except:
            titulo = "TÃ­tulo no disponible"
        
        try:
            empresa = driver.find_element(By.CSS_SELECTOR, 'a.topcard__org-name-link, span.topcard__flavor, a[data-tracking-control-name="public_jobs_topcard-org-name"]').text.strip()
        except:
            empresa = "Confidencial"
        
        try:
            ubicacion = driver.find_element(By.CSS_SELECTOR, 'span.topcard__flavor--bullet').text.strip()
        except:
            ubicacion = "Argentina"
        
        try:
            show_more = driver.find_element(By.CSS_SELECTOR, 'button.show-more-less-html__button')
            driver.execute_script("arguments[0].click();", show_more)
            time.sleep(1)
        except:
            pass
        
        try:
            descripcion = driver.find_element(By.CSS_SELECTOR, 'div.show-more-less-html__markup, div.description__text').text.strip()
        except:
            descripcion = "DescripciÃ³n no disponible"
        
        categoria_portal = ""
        subcategoria_portal = ""
        try:
            criterios = driver.find_elements(By.CSS_SELECTOR, 'li.description__job-criteria-item')
            for criterio in criterios:
                header = criterio.find_element(By.CSS_SELECTOR, 'h3').text.strip().lower()
                value = criterio.find_element(By.CSS_SELECTOR, 'span').text.strip()
                if 'funciÃ³n' in header or 'function' in header:
                    categoria_portal = value
                elif 'sector' in header or 'industries' in header:
                    subcategoria_portal = value
        except:
            pass
        
        return {
            'titulo': titulo,
            'empresa': empresa,
            'ubicacion': ubicacion,
            'descripcion': descripcion,
            'categoria_portal': categoria_portal,
            'subcategoria_portal': subcategoria_portal
        }
        
    except Exception as e:
        debug_print(f"Error: {str(e)}")
        return None

def get_job_urls_from_page(driver):
    job_cards = driver.find_elements(By.CSS_SELECTOR, 'div.base-card, div.job-search-card')
    job_urls = []
    
    for card in job_cards:
        try:
            link = card.find_element(By.CSS_SELECTOR, 'a.base-card__full-link, a[data-tracking-control-name="public_jobs_jserp-result_search-card"]')
            url = link.get_attribute('href')
            if url and '/jobs/view/' in url:
                job_urls.append(url.split('?')[0])
        except:
            continue
    
    return list(dict.fromkeys(job_urls))

def obtener_total_paginas(driver, area_code):
    """Estima el total de pÃ¡ginas para un Ã¡rea"""
    url = f"https://www.linkedin.com/jobs/search/?f_F={area_code}&geoId=100446943&location=Argentina"
    driver.get(url)
    time.sleep(3)
    
    try:
        # Buscar el contador de resultados
        results_text = driver.find_element(By.CSS_SELECTOR, 'span.results-context-header__job-count, div.results-context-header span').text
        total_jobs = int(''.join(filter(str.isdigit, results_text)))
        total_pages = (total_jobs // 25) + 1
        return min(total_pages, 40)  # LinkedIn limit
    except:
        return 10  # Default

def scrape_area(driver, area_name, area_code, area_index, total_areas, start_page=1):
    global total_jobs_scraped, jobs_this_session, EMPLEOS, HASHES_GLOBALES, current_page
    
    print(f"\n{'='*80}")
    print(f"PROCESANDO ÃREA {area_index}/{total_areas}: {area_name}")
    print(f"{'='*80}")
    
    print(f"Analizando Ã¡rea: {area_name}")
    
    total_paginas = obtener_total_paginas(driver, area_code)
    print(f"Encontradas {total_paginas} pÃ¡ginas para {area_name}")
    print("Comenzando extracciÃ³n de empleos...")
    
    area_jobs = 0
    current_page = start_page  # Resume from checkpoint if available
    consecutive_empty = 0
    
    while current_page <= total_paginas:
        start = (current_page - 1) * 25
        url = f"https://www.linkedin.com/jobs/search/?f_F={area_code}&geoId=100446943&location=Argentina&start={start}"
        

        # Save checkpoint before each page
        checkpoint_data = LinkedInCheckpoint.create_checkpoint_data(
            area_index, current_page, list(areas_completed), total_jobs_scraped
        )
        checkpoint_manager.save_checkpoint(checkpoint_data)
        print(f"\nðŸ” Procesando pÃ¡gina {current_page}/{total_paginas} de {area_name}")
        
        try:
            driver.get(url)
            time.sleep(3)
            
            try:
                no_results = driver.find_element(By.CSS_SELECTOR, 'div.no-results, h1.no-results__header')
                print(f"No se encontraron empleos en la pÃ¡gina {current_page}")
                break
            except:
                pass
            
            scroll_and_load_jobs(driver, max_jobs=25)
            
            job_urls = get_job_urls_from_page(driver)
            print(f"PÃ¡gina {current_page}/{total_paginas} - {len(job_urls)} empleos encontrados:")
            
            if len(job_urls) == 0:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    break
                current_page += 1
                continue
            
            consecutive_empty = 0
            
            for i, job_url in enumerate(job_urls):
                try:
                    driver = recrear_driver_si_necesario(driver)
                    
                    details = extract_job_details(driver, job_url)
                    if not details:
                        continue
                    
                    hash_empleo = calcular_hash(details['descripcion'])
                    
                    if hash_empleo in HASHES_GLOBALES:
                        print(f"{i} - [DUPLICADO] Saltando...")
                        continue
                    
                    print(f"{i} - {details['titulo']}")
                    
                    EMPLEOS.append({
                        "Id Interno": f"{current_page}-{i+1}",
                        "titulo": details['titulo'],
                        "descripcion": details['descripcion'],
                        "Empresa": details['empresa'],
                        "Fuente": "LinkedIn",
                        "Tipo Portal": "Red Profesional",
                        "url": job_url,
                        "Pais": "Argentina",
                        "ubicacion": details['ubicacion'],
                        "Categoria Portal": details['categoria_portal'] or area_name,
                        "Subcategoria Portal": details['subcategoria_portal'],
                        "Categorria": "",
                        "Subcategoria": "",
                        "hash Descripcion": hash_empleo,
                        "fecha": date.today().strftime("%d/%m/%Y")
                    })
                    
                    HASHES_GLOBALES.add(hash_empleo)
                    total_jobs_scraped += 1
                    jobs_this_session += 1
                    area_jobs += 1
                    
                    time.sleep(1.5)
                    
                except Exception as e:
                    print(f"Error procesando empleo {i+1}: {str(e)}")
                    continue
            
            current_page += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"Error en pÃ¡gina {current_page}: {str(e)}")
            driver = recrear_driver_si_necesario(driver)
            current_page += 1
            continue
    
    # Guardar al finalizar Ã¡rea
    print(f"\n{'='*60}")
    print(f"âœ… Ãrea '{area_name}' completada - Guardando datos...")
    print(f"ðŸ“Š Jobs en esta Ã¡rea: {area_jobs}")
    print(f"ðŸ“ˆ Total acumulado: {total_jobs_scraped}")
    print(f"{'='*60}")
    
    if EMPLEOS:
        guardar_datos_incremental(EMPLEOS, area_name)
        EMPLEOS = []
    
    return area_jobs

# Main
if __name__ == "__main__":
    print("Iniciando scraping de LinkedIn...")
    if args.debug:
        print("Modo debug activado - Se mostrarÃ¡n mensajes detallados")
    
    if args.start_from:
        print(f"Iniciando desde la categorÃ­a: {args.start_from}")
    
    print("Cargando hashes existentes para evitar duplicados entre categorÃ­as...")
    timestamp = date.today().strftime("%Y%m%d")
    for area_name in AREAS.keys():
        archivo = f"output_jobs/LinkedIn_{area_name}_{timestamp}.json"
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
    
    # =============================================================================
    # SISTEMA DE CHECKPOINT - REANUDAR SESIÃ"N INTERRUMPIDA
    # =============================================================================
    should_resume, checkpoint_data, checkpoint_manager = get_resume_info("linkedin")
    
    if should_resume:
        print("Reanudando desde checkpoint...")
        start_area_index = checkpoint_data.get('current_area_index', 0)
        start_page = checkpoint_data.get('current_page', 1)
        areas_completed = set(checkpoint_data.get('areas_completed', []))
        total_jobs_scraped = checkpoint_data.get('total_jobs_scraped', 0)
        print(f"Iniciando desde Ã¡rea #{start_area_index + 1}, pÃ¡gina {start_page}")
        print(f"Jobs recolectados previamente: {total_jobs_scraped}")
    else:
        print("Iniciando scraping completo desde el principio...")
        start_area_index = 0
        start_page = 1
        areas_completed = set()
        total_jobs_scraped = 0
        checkpoint_manager = CheckpointManager("linkedin")
    
    # Determinar desde quÃ© Ã¡rea comenzar
    areas_list = list(AREAS.items())
    start_index = start_area_index  # Use checkpoint if available
    
    # Only use --start-from if not resuming from checkpoint
    if args.start_from and not should_resume:
        for i, (name, code) in enumerate(areas_list):
            if name == args.start_from:
                start_index = i
                break
        else:
            print(f"Ãrea '{args.start_from}' no encontrada. Iniciando desde el principio.")
            print(f"Ãreas disponibles: {', '.join(list(AREAS.keys())[:5])}...")
    
    areas_to_process = areas_list[start_index:]
    print(f"Procesando {len(areas_to_process)} Ã¡reas restantes...")
    
    driver = create_driver()
    
    try:
        for idx, (area_name, area_code) in enumerate(areas_to_process):
            # Skip areas that were already completed
            if area_name in areas_completed:
                print(f"Saltando Ã¡rea ya completada: {area_name}")
                continue
            
            current_area = area_name
            current_area_index = start_index + idx
            
            try:
                # Determine starting page (resume from checkpoint if this is the current area)
                current_start_page = start_page if (start_index + idx == start_area_index) else 1
                
                scrape_area(driver, area_name, area_code, current_area_index + 1, len(AREAS), current_start_page)
                areas_completed.add(area_name)
                
            except Exception as e:
                print(f"Error crÃ­tico en Ã¡rea {area_name}: {str(e)}")
                print("Intentando continuar con la siguiente Ã¡rea...")
                driver = recrear_driver_si_necesario(driver)
                continue
            
            time.sleep(3)
    finally:
        try:
            driver.quit()
        except:
            pass
    
    # Clear checkpoint after successful completion
    checkpoint_manager.clear_checkpoint()
    
    print(f"\nðŸŽ‰ SCRAPING COMPLETADO EXITOSAMENTE!")
    print(f"ðŸ“Š Resumen de la sesiÃ³n:")
    print(f"   - Jobs recolectados en esta sesiÃ³n: {jobs_this_session}")
    print(f"   - Total de jobs recolectados: {total_jobs_scraped}")
    print(f"   - Ãreas completadas: {len(areas_completed)}/{len(AREAS)}")
    print(f"   - Todos los datos guardados en: output_jobs/")
    print(f"Archivos guardados en: output_jobs/")
    print(f"{'='*60}\n")
