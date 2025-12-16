from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from checkpoint_manager import CheckpointManager, LinkedInCheckpoint, get_resume_info
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
parser.add_argument('--start-from', type=str, help='Iniciar desde una categoría específica')
args = parser.parse_args()

def debug_print(*mensaje, **kwargs):
    if args.debug:
        _original_print(f"{BLUE}{' '.join(map(str, mensaje))}{RESET}", **kwargs)

# LinkedIn Job Functions - Using numerical codes from LinkedIn's official reference
# Source: https://support.captaindata.co/hc/en-us/articles/19832314901917
AREAS = {
    "accounting": "1",
    "administrative": "2",
    "arts-and-design": "3",
    "business-development": "4",
    "community-and-social-services": "5",
    "consulting": "6",
    "education": "7",
    "engineering": "8",
    "entrepreneurship": "9",
    "finance": "10",
    "healthcare-services": "11",
    "human-resources": "12",
    "information-technology": "13",
    "legal": "14",
    "marketing": "15",
    "media-and-communication": "16",
    "military-and-protective-services": "17",
    "operations": "18",
    "product-management": "19",
    "program-and-project-management": "20",
    "purchasing": "21",
    "quality-assurance": "22",
    "real-estate": "23",
    "research": "24",
    "sales": "25",
    "support": "26",
}

# Global variables
driver = None
checkpoint_manager = None
total_jobs_scraped = 0
jobs_this_session = 0
EMPLEOS = []
HASHES_GLOBALES = set()
URLS_VISTAS = set()  # Track URLs to avoid re-fetching details
current_area = ""
current_area_index = 0
current_page = 1
areas_completed = set()

def signal_handler(sig, frame):
    print(f"\n\n Interrupción detectada (CTRL+C)")
    print(" Guardando checkpoint para poder reanudar...")
    
    if checkpoint_manager:
        checkpoint_data = LinkedInCheckpoint.create_checkpoint_data(
            current_area_index, current_page, list(areas_completed), total_jobs_scraped
        )
        checkpoint_manager.save_checkpoint(checkpoint_data)
        print(" Checkpoint guardado exitosamente")
    
    if EMPLEOS:
        guardar_datos_incremental(EMPLEOS, current_area)
    
    if driver:
        try:
            driver.quit()
            print(" Driver cerrado correctamente")
        except:
            pass
    
    print(" Hasta la próxima! Usa el mismo comando para reanudar.")
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
        print("Sesión perdida. Recreando driver...")
        try:
            driver.quit()
        except:
            pass
        return create_driver()
    return driver


def verificar_pagina_existe(driver, area_code, page_num, intentos=3):
    """
    Verifica si una página contiene trabajos válidos
    LinkedIn usa start= para paginación (0, 25, 50, etc.)
    Usa el endpoint /jobs-guest/jobs/api/seeMoreJobPostings/search para paginación correcta
    Retorna: (existe, numero_de_trabajos)
    """
    start = (page_num - 1) * 25
    # Usar el endpoint de guest API que sí soporta paginación
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=&location=Argentina&geoId=100446943&f_F={area_code}&start={start}"
    
    for intento in range(intentos):
        try:
            driver.get(url)
            time.sleep(random.uniform(2, 4))
            
            # Este endpoint devuelve HTML con <li> elements
            job_items = driver.find_elements(By.CSS_SELECTOR, 'li')
            
            debug_print(f"    Encontrados: {len(job_items)} items")
            
            empleos_validos = []
            
            for item in job_items:
                try:
                    # Buscar el enlace dentro del item
                    link = item.find_element(By.CSS_SELECTOR, 'a.base-card__full-link')
                    href = link.get_attribute('href')
                    
                    # Un empleo válido debe tener URL de LinkedIn jobs
                    if href and '/jobs/view/' in href:
                        empleos_validos.append(href)
                        debug_print(f"    [OK] Empleo válido: {href[:60]}...")
                except:
                    continue
            
            num_empleos = len(empleos_validos)
            
            if num_empleos > 0:
                print(f"Página {page_num}: {num_empleos} empleos válidos encontrados")
                return True, num_empleos
            else:
                print(f"Página {page_num}: 0 empleos válidos encontrados")
                return False, 0
                
        except Exception as e:
            if intento < intentos - 1:
                debug_print(f"  ! Intento {intento + 1} falló, reintentando...")
                time.sleep(2)
                continue
            else:
                debug_print(f"  [X] Error verificando página: {str(e)}")
                print(f"Página {page_num}: Error al verificar")
                return False, 0
    
    return False, 0


def obtener_total_paginas(driver, area_code):
    """
    Usa búsqueda binaria para encontrar el número total de páginas disponibles
    Similar a ZonaJobs y Computrabajo
    """
    print(f"\nBuscando total de páginas disponibles...")
    
    # Verificar primera página
    existe, num_empleos = verificar_pagina_existe(driver, area_code, 1)
    if not existe:
        print("No se encontraron empleos en la primera página")
        return 0

    # LinkedIn limita a ~40 páginas (1000 resultados)
    # Fase 1: Verificación rápida de páginas clave
    debug_print("\nFase 1: Verificando páginas clave...")
    paginas_prueba = [10, 20, 30, 40]
    ultima_valida = 1
    
    for pagina in paginas_prueba:
        existe, _ = verificar_pagina_existe(driver, area_code, pagina)
        if existe:
            ultima_valida = pagina
        else:
            break
    
    # Ajustar el rango de búsqueda
    if ultima_valida == 1:
        rango_busqueda = 10
    elif ultima_valida == 10:
        rango_busqueda = 20
    elif ultima_valida == 20:
        rango_busqueda = 30
    elif ultima_valida == 30:
        rango_busqueda = 40
    else:
        rango_busqueda = 40  # LinkedIn max

    # Fase 2: Búsqueda binaria refinada
    debug_print("\nFase 2: Búsqueda binaria para encontrar la última página...")
    left = ultima_valida
    right = rango_busqueda
    ultima_pagina_valida = ultima_valida
    pagina_actual = None
    
    while left <= right:
        mid = (left + right) // 2
        if pagina_actual == mid:
            break
            
        pagina_actual = mid
        debug_print(f"\nProbando página {mid}...")
        
        existe, _ = verificar_pagina_existe(driver, area_code, mid)
        if existe:
            ultima_pagina_valida = mid
            left = mid + 1
        else:
            right = mid - 1
    
    # Fase 3: Búsqueda secuencial final
    debug_print("\nFase 3: Búsqueda secuencial final...")
    pagina = ultima_pagina_valida
    while pagina < 40:  # LinkedIn limit
        existe, _ = verificar_pagina_existe(driver, area_code, pagina + 1)
        if not existe:
            debug_print(f"Encontrada última página válida: {pagina}")
            break
        pagina += 1
        ultima_pagina_valida = pagina

    print(f"Total de páginas encontradas: {ultima_pagina_valida}")
    return ultima_pagina_valida


def extract_job_details(driver, job_url):
    """Extrae detalles de un empleo"""
    try:
        driver.get(job_url)
        time.sleep(random.uniform(2, 3))
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h1, h2'))
        )
        
        # Título
        try:
            titulo = driver.find_element(By.CSS_SELECTOR, 'h1.top-card-layout__title, h2.top-card-layout__title, h1').text.strip()
        except:
            titulo = "Título no disponible"
        
        # Empresa
        try:
            empresa = driver.find_element(By.CSS_SELECTOR, 'a.topcard__org-name-link, span.topcard__flavor, a[data-tracking-control-name="public_jobs_topcard-org-name"]').text.strip()
        except:
            empresa = "Confidencial"
        
        # Ubicación
        try:
            ubicacion = driver.find_element(By.CSS_SELECTOR, 'span.topcard__flavor--bullet').text.strip()
        except:
            ubicacion = "Argentina"
        
        # Expandir descripción
        try:
            show_more = driver.find_element(By.CSS_SELECTOR, 'button.show-more-less-html__button')
            driver.execute_script("arguments[0].click();", show_more)
            time.sleep(1)
        except:
            pass
        
        # Descripción
        try:
            descripcion = driver.find_element(By.CSS_SELECTOR, 'div.show-more-less-html__markup, div.description__text').text.strip()
        except:
            descripcion = "Descripción no disponible"
        
        # Categorías
        categoria_portal = ""
        subcategoria_portal = ""
        try:
            criterios = driver.find_elements(By.CSS_SELECTOR, 'li.description__job-criteria-item')
            for criterio in criterios:
                header = criterio.find_element(By.CSS_SELECTOR, 'h3').text.strip().lower()
                value = criterio.find_element(By.CSS_SELECTOR, 'span').text.strip()
                if 'función' in header or 'function' in header:
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
        debug_print(f"Error extrayendo detalles: {str(e)}")
        return None


def get_job_urls_from_page(driver, area_code, page_num):
    """Obtiene todas las URLs de empleos de una página específica usando el guest API"""
    start = (page_num - 1) * 25
    # Usar el endpoint de guest API que sí soporta paginación
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=&location=Argentina&geoId=100446943&f_F={area_code}&start={start}"
    
    driver.get(url)
    time.sleep(random.uniform(2, 4))
    
    # Este endpoint devuelve HTML con <li> elements
    job_items = driver.find_elements(By.CSS_SELECTOR, 'li')
    job_urls = []
    
    for item in job_items:
        try:
            link = item.find_element(By.CSS_SELECTOR, 'a.base-card__full-link')
            href = link.get_attribute('href')
            if href and '/jobs/view/' in href:
                # Limpiar URL (quitar parámetros)
                clean_url = href.split('?')[0]
                job_urls.append(clean_url)
        except:
            continue
    
    # Eliminar duplicados manteniendo orden
    return list(dict.fromkeys(job_urls))


def scrape_area(driver, area_name, area_code, area_index, total_areas, start_page=1):
    """Scrapea todos los empleos de un área, página por página"""
    global total_jobs_scraped, jobs_this_session, EMPLEOS, HASHES_GLOBALES, URLS_VISTAS
    global current_page, checkpoint_manager
    
    print(f"\n{'='*80}")
    print(f"PROCESANDO ÁREA {area_index}/{total_areas}: {area_name}")
    print(f"{'='*80}")
    
    print(f"Analizando área: {area_name}")
    
    # Obtener el número total de páginas para esta área
    total_paginas = obtener_total_paginas(driver, area_code)
    
    if total_paginas == 0:
        print(f"No se encontraron empleos en {area_name}")
        return 0
    
    print(f"Encontradas {total_paginas} páginas para {area_name}")
    print("Comenzando extracción de empleos...\n")
    
    area_jobs = 0
    
    # Iterar por TODAS las páginas
    for pagina in range(start_page, total_paginas + 1):
        print(f"\n Procesando página {pagina}/{total_paginas} de {area_name}")
        
        # Update global for signal handler
        current_page = pagina
        
        # Save checkpoint before each page
        checkpoint_data = LinkedInCheckpoint.create_checkpoint_data(
            area_index - 1, pagina, list(areas_completed), total_jobs_scraped
        )
        checkpoint_manager.save_checkpoint(checkpoint_data)
        
        try:
            # Obtener URLs de esta página
            job_urls = get_job_urls_from_page(driver, area_code, pagina)
            
            if len(job_urls) == 0:
                print(f"Página {pagina}/{total_paginas} - 0 empleos encontrados")
                continue
            
            # Filtrar URLs ya vistas
            nuevas_urls = [url for url in job_urls if url not in URLS_VISTAS]
            
            print(f"Página {pagina}/{total_paginas} - {len(job_urls)} empleos encontrados ({len(nuevas_urls)} nuevos, {len(job_urls) - len(nuevas_urls)} ya vistos)")
            
            if len(nuevas_urls) == 0:
                print(f"  [TODAS LAS URLs YA VISTAS] - Saltando página")
                continue
            
            # Procesar solo URLs nuevas
            for i, job_url in enumerate(nuevas_urls):
                # Mark URL as seen
                URLS_VISTAS.add(job_url)
                
                try:
                    driver = recrear_driver_si_necesario(driver)
                    
                    details = extract_job_details(driver, job_url)
                    if not details:
                        print(f"  {i} - [ERROR] No se pudieron extraer detalles")
                        continue
                    
                    # Calculate hash for duplicate detection
                    hash_empleo = calcular_hash(details['descripcion'])
                    
                    if hash_empleo in HASHES_GLOBALES:
                        print(f"  {i} - [DUPLICADO] {details['titulo'][:50]}...")
                        continue
                    
                    print(f"  {i} - {details['titulo']}")
                    
                    EMPLEOS.append({
                        "Id Interno": f"LI-{area_name}-{pagina}-{i+1}",
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
                    
                    time.sleep(random.uniform(1.5, 2.5))
                    
                except Exception as e:
                    print(f"  Error procesando empleo {i+1}: {str(e)}")
                    continue
            
            # Pausa entre páginas
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            print(f"Error en página {pagina}: {str(e)}")
            driver = recrear_driver_si_necesario(driver)
            continue
    
    # Guardar al finalizar área
    print(f"\n{'='*60}")
    print(f" Área '{area_name}' completada - Guardando datos...")
    print(f" Jobs en esta área: {area_jobs}")
    print(f" Total acumulado: {total_jobs_scraped}")
    print(f"{'='*60}")
    
    if EMPLEOS:
        guardar_datos_incremental(EMPLEOS, area_name)
        EMPLEOS = []
    
    return area_jobs


# Main
if __name__ == "__main__":
    print("Iniciando scraping de LinkedIn...")
    if args.debug:
        print("Modo debug activado - Se mostrarán mensajes detallados")
    
    if args.start_from:
        print(f"Iniciando desde la categoría: {args.start_from}")
    
    # Cargar hashes y URLs existentes
    print("Cargando hashes existentes para evitar duplicados entre categorías...")
    timestamp = date.today().strftime("%Y%m%d")
    for area_name in AREAS.keys():
        archivo = f"output_jobs/LinkedIn_{area_name}_{timestamp}.json"
        if os.path.exists(archivo):
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    empleos_existentes = json.load(f)
                    for empleo in empleos_existentes:
                        h = empleo.get("hash Descripcion")
                        if h:
                            HASHES_GLOBALES.add(h)
                        u = empleo.get("url")
                        if u:
                            URLS_VISTAS.add(u)
            except:
                pass
    print(f"Cargados {len(HASHES_GLOBALES)} hashes existentes")
    print(f"Cargadas {len(URLS_VISTAS)} URLs ya visitadas")
    
    # =============================================================================
    # SISTEMA DE CHECKPOINT
    # =============================================================================
    should_resume, checkpoint_data, checkpoint_manager = get_resume_info("linkedin")
    
    if should_resume:
        print("Reanudando desde checkpoint...")
        start_area_index = checkpoint_data.get('current_area_index', 0)
        start_page = checkpoint_data.get('current_page', 1)
        areas_completed = set(checkpoint_data.get('areas_completed', []))
        total_jobs_scraped = checkpoint_data.get('total_jobs_scraped', 0)
        print(f"Iniciando desde área #{start_area_index + 1}, página {start_page}")
        print(f"Jobs recolectados previamente: {total_jobs_scraped}")
    else:
        print("Iniciando scraping completo desde el principio...")
        start_area_index = 0
        start_page = 1
        areas_completed = set()
        total_jobs_scraped = 0
        checkpoint_manager = CheckpointManager("linkedin")
    
    # Update global variables
    current_area_index = start_area_index
    current_page = start_page
    
    # Determinar desde qué área comenzar
    areas_list = list(AREAS.items())
    start_index = start_area_index
    
    if args.start_from and not should_resume:
        for i, (name, code) in enumerate(areas_list):
            if name == args.start_from:
                start_index = i
                print(f"Iniciando desde el índice {start_index}: {args.start_from}")
                break
        else:
            print(f"Área '{args.start_from}' no encontrada. Iniciando desde el principio.")
            print(f"Áreas disponibles: {', '.join(list(AREAS.keys())[:5])}...")
    
    areas_to_process = areas_list[start_index:]
    print(f"Procesando {len(areas_to_process)} áreas restantes...")
    
    driver = create_driver()
    
    try:
        for idx, (area_name, area_code) in enumerate(areas_to_process):
            current_area = area_name
            current_area_index = start_index + idx
            
            # Skip completed areas
            if area_name in areas_completed:
                print(f"Saltando área ya completada: {area_name}")
                continue
            
            # Determine starting page
            current_start_page = start_page if idx == 0 and should_resume else 1
            
            try:
                scrape_area(driver, area_name, area_code, current_area_index + 1, len(AREAS), current_start_page)
                areas_completed.add(area_name)
                
                # Save checkpoint after each area
                checkpoint_data = LinkedInCheckpoint.create_checkpoint_data(
                    current_area_index + 1, 1, list(areas_completed), total_jobs_scraped
                )
                checkpoint_manager.save_checkpoint(checkpoint_data)
                
            except Exception as e:
                print(f"Error crítico en área {area_name}: {str(e)}")
                print("Intentando continuar con la siguiente área...")
                driver = recrear_driver_si_necesario(driver)
                continue
            
            # Reset start_page for subsequent areas
            start_page = 1
            
            time.sleep(random.uniform(3, 5))
        
    finally:
        try:
            driver.quit()
        except:
            pass
    
    # Clear checkpoint after successful completion
    checkpoint_manager.clear_checkpoint()
    
    print(f"\n SCRAPING COMPLETADO EXITOSAMENTE!")
    print(f" Resumen de la sesión:")
    print(f"   - Jobs recolectados en esta sesión: {jobs_this_session}")
    print(f"   - Total de jobs recolectados: {total_jobs_scraped}")
    print(f"   - Áreas completadas: {len(areas_completed)}/{len(AREAS)}")
    print(f"   - Todos los datos guardados en: output_jobs/")
    print(f"Archivos guardados en: output_jobs/")
    print(f"{'='*60}\n")