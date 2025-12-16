from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re
import random
import hashlib
from datetime import date
import os
import argparse
import builtins
import signal
import sys
from checkpoint_manager import CheckpointManager, WorkanaCheckpoint, get_resume_info

# Colores ANSI para tmux - Cyan para Workana
CYAN = '\033[0;36m'
RESET = '\033[0m'

# Sobrescribir la función print para colorear todo
_original_print = builtins.print
def print(*args, **kwargs):
    """Print coloreado en cyan para Workana"""
    colored_args = [f"{CYAN}{arg}{RESET}" if isinstance(arg, str) else arg for arg in args]
    _original_print(*colored_args, **kwargs)
builtins.print = print

# Configurar argumentos de línea de comandos
parser = argparse.ArgumentParser(description='Script de scraping para Workana')
parser.add_argument('--debug', action='store_true', help='Activar mensajes de debug')
args = parser.parse_args()

def debug_print(*mensaje, **kwargs):
    if args.debug:
        _original_print(f"{CYAN}{' '.join(map(str, mensaje))}{RESET}", **kwargs)

# Global variables for signal handler
driver = None
checkpoint_manager = None
current_category_index = 0
current_page = 1
categories_completed = set()
total_jobs_scraped = 0

def signal_handler(sig, frame):
    """Handle CTRL+C gracefully by saving checkpoint"""
    print(f"\n\nInterrupción detectada (CTRL+C)")
    print("Guardando checkpoint para poder reanudar...")
    
    if checkpoint_manager:
        checkpoint_data = WorkanaCheckpoint.create_checkpoint_data(
            current_category_index, current_page, list(categories_completed), total_jobs_scraped
        )
        checkpoint_manager.save_checkpoint(checkpoint_data)
        print("Checkpoint guardado exitosamente")
    
    if driver:
        try:
            driver.quit()
            print("Driver cerrado correctamente")
        except:
            pass
    
    print("Hasta la próxima! Usa el mismo comando para reanudar.")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)
# Configuración del driver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)
driver.maximize_window()

def calcular_hash(texto):
    if not isinstance(texto, str):
        return None
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def guardar_datos_incremental(empleos, categoria, archivo_base="output_jobs/Workana"):
    """
    Guarda los datos incrementalmente (ya no necesita filtrar duplicados)
    """
    # Crear directorio si no existe
    os.makedirs("output_jobs", exist_ok=True)
    
    # Nombre del archivo
    timestamp = date.today().strftime("%Y%m%d")
    nombre_archivo = f"{archivo_base}_{categoria}_{timestamp}.json"
    
    # Leer datos existentes si el archivo existe
    empleos_existentes = []
    
    if os.path.exists(nombre_archivo):
        try:
            with open(nombre_archivo, 'r', encoding='utf-8') as f:
                empleos_existentes = json.load(f)
            print(f"Cargados {len(empleos_existentes)} empleos existentes del archivo")
        except:
            print("Archivo existente pero no se pudo leer, creando nuevo")
    
    # Combinar y guardar (los duplicados ya fueron filtrados antes)
    todos_empleos = empleos_existentes + empleos
    
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        json.dump(todos_empleos, f, ensure_ascii=False, indent=4)
    
    print(f"\nGuardado: {nombre_archivo}")
    print(f"  - Empleos nuevos: {len(empleos)}")
    print(f"  - Total en archivo: {len(todos_empleos)}")
    
    return nombre_archivo, len(empleos), 0

def verificar_pagina_existe(driver, url, intentos=3):
    page_num = re.search(r'page=(\d+)', url)
    page_num = int(page_num.group(1)) if page_num else 1
    
    for intento in range(intentos):
        try:
            driver.get(url)
            time.sleep(random.uniform(2, 3))
            
            # Esperar a que cargue la página completamente
            time.sleep(2)
            
            # Verificar si hay mensaje de "no results found"
            try:
                no_results = driver.find_elements(By.XPATH, "//*[contains(text(), 'No encontramos') or contains(text(), 'no results') or contains(text(), 'Sin resultados')]")
                if no_results and any(elem.is_displayed() for elem in no_results):
                    print(f"Página {page_num}: 0 empleos válidos encontrados")
                    return False, 0
            except:
                pass
            
            # Intentar múltiples selectores para encontrar empleos
            links_empleos = []
            
            # Selector 1: Original
            links_empleos = driver.find_elements(By.CSS_SELECTOR, "div.project-header h2 a")
            debug_print(f"    Selector 1 encontró: {len(links_empleos)} enlaces")
            
            # Selector 2: Alternativo si el primero falla
            if len(links_empleos) == 0:
                links_empleos = driver.find_elements(By.CSS_SELECTOR, ".project-title a")
                debug_print(f"    Selector 2 encontró: {len(links_empleos)} enlaces")
            
            # Selector 3: Más general
            if len(links_empleos) == 0:
                links_empleos = driver.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/']")
                debug_print(f"    Selector 3 encontró: {len(links_empleos)} enlaces")
            
            empleos_validos = []
            
            for link in links_empleos:
                try:
                    # Verificar que el enlace tenga href y texto
                    href = link.get_attribute("href")
                    texto = link.text.strip()
                    
                    debug_print(f"    Analizando: href={href}, texto={texto[:30] if texto else 'sin texto'}")
                    
                    # Un empleo válido debe tener URL válida de workana (singular /job/ no /jobs/)
                    if href and 'workana.com' in href and '/job/' in href and '/jobs?' not in href:
                        if texto and len(texto) > 5:
                            empleos_validos.append(link)
                            debug_print(f"Empleo válido: {texto[:50]}")
                        else:
                            debug_print(f"Rechazado por texto corto o vacío")
                    else:
                        debug_print(f"Rechazado por URL inválida")
                except Exception as e:
                    debug_print(f"Error: {str(e)}")
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
                continue
            else:
                debug_print(f"  × Error verificando página: {str(e)}")
                print(f"Página {page_num}: Error al verificar")
                return False, 0
    
    return False, 0

def obtener_total_paginas(driver, categoria_slug, subcategoria_slug):
    # Obtener todos los trabajos disponibles
    url_base = f"https://www.workana.com/jobs?category={categoria_slug}&language=en%2Ces&subcategory={subcategoria_slug}"
    
    print(f"\nAnalizando categoría: {categoria_slug} - subcategoría: {subcategoria_slug}")
    print("Buscando total de páginas disponibles...")
    
    # Verificar primera página
    existe, num_empleos = verificar_pagina_existe(driver, f"{url_base}&page=1")
    if not existe:
        print("No se encontraron empleos en la primera página")
        return 1

    # Búsqueda optimizada por incrementos de 50
    # Comenzar con incrementos de 50 páginas
    left = 1
    right = 50
    ultima_pagina_valida = 1

    # Fase 1: Encontrar un límite superior usando incrementos de 50
    while True:
        existe, _ = verificar_pagina_existe(driver, f"{url_base}&page={right}")
        if not existe:
            break
        ultima_pagina_valida = right
        left = right
        right += 50  # Incrementar en 50 páginas cada vez
        
    # Fase 2: Búsqueda binaria refinada entre el último válido y el primer inválido
    while left <= right:
        mid = (left + right) // 2
        if left == mid or right == mid:  # Evitar bucle infinito
            break

        existe, _ = verificar_pagina_existe(driver, f"{url_base}&page={mid}")
        if existe:
            ultima_pagina_valida = mid
            left = mid + 1
        else:
            right = mid - 1

    # Fase 3: Verificación final
    while ultima_pagina_valida > 0:
        existe, _ = verificar_pagina_existe(driver, f"{url_base}&page={ultima_pagina_valida}")
        if existe:
            break
        ultima_pagina_valida -= 1

    print(f"Total de páginas encontradas: {ultima_pagina_valida}")
    return ultima_pagina_valida

EMPLEOS = []


# Lista de categorías y subcategorías a scrapear
categoria_para_archivo="all_categories"
categorias = [
    # === Programación y Tecnología ===
    {"slug": "it-programming", "subcategoria": "web-development", "nombre": "IT_Web_Development"},
    {"slug": "it-programming", "subcategoria": "web-design", "nombre": "IT_Web_Design"},
    {"slug": "it-programming", "subcategoria": "e-commerce", "nombre": "IT_E_Commerce"},
    {"slug": "it-programming", "subcategoria": "wordpress-1", "nombre": "IT_WordPress"},
    {"slug": "it-programming", "subcategoria": "mobile-development", "nombre": "IT_Mobile_Development"},
    {"slug": "it-programming", "subcategoria": "data-science-1", "nombre": "IT_Data_Science"},
    {"slug": "it-programming", "subcategoria": "desktop-apps", "nombre": "IT_Desktop_Apps"},
    {"slug": "it-programming", "subcategoria": "artificial-intelligence-1", "nombre": "IT_Artificial_Intelligence"},
    {"slug": "it-programming", "subcategoria": "others-5", "nombre": "IT_Others"},

    # === Diseño y Multimedia ===
    {"slug": "design-multimedia", "subcategoria": "logo-design", "nombre": "Design_Logo_Design"},
    {"slug": "design-multimedia", "subcategoria": "web-design-1", "nombre": "Design_Web_Design"},
    {"slug": "design-multimedia", "subcategoria": "banners", "nombre": "Design_Banners"},
    {"slug": "design-multimedia", "subcategoria": "illustrations", "nombre": "Design_Illustrations"},
    {"slug": "design-multimedia", "subcategoria": "make-or-edit-a-video", "nombre": "Design_Video_Editing"},
    {"slug": "design-multimedia", "subcategoria": "infographics", "nombre": "Design_Infographics"},
    {"slug": "design-multimedia", "subcategoria": "images-for-social-networks", "nombre": "Design_Social_Media_Images"},
    {"slug": "design-multimedia", "subcategoria": "mobile-app-design", "nombre": "Design_Mobile_App_Design"},
    {"slug": "design-multimedia", "subcategoria": "corporate-image", "nombre": "Design_Corporate_Image"},
    {"slug": "design-multimedia", "subcategoria": "3d-models", "nombre": "Design_3D_Models"},
    {"slug": "design-multimedia", "subcategoria": "landing-page", "nombre": "Design_Landing_Page"},
    {"slug": "design-multimedia", "subcategoria": "fashion-design-1", "nombre": "Design_Fashion_Design"},
    {"slug": "design-multimedia", "subcategoria": "artificial-intelligence-2", "nombre": "Design_AI"},
    {"slug": "design-multimedia", "subcategoria": "others-1", "nombre": "Design_Others"},

    # === Redacción y Traducción ===
    {"slug": "writing-translation", "subcategoria": "article-writing-1", "nombre": "Writing_Article_Writing"},
    {"slug": "writing-translation", "subcategoria": "writing-for-websites", "nombre": "Writing_Web_Content"},
    {"slug": "writing-translation", "subcategoria": "proofreading-1", "nombre": "Writing_Proofreading"},
    {"slug": "writing-translation", "subcategoria": "content-for-social-networks", "nombre": "Writing_Social_Media_Content"},
    {"slug": "writing-translation", "subcategoria": "translation", "nombre": "Writing_Translation"},
    {"slug": "writing-translation", "subcategoria": "subtitling-1", "nombre": "Writing_Subtitling"},
    {"slug": "writing-translation", "subcategoria": "artificial-intelligence-7", "nombre": "Writing_AI"},
    {"slug": "writing-translation", "subcategoria": "others-6", "nombre": "Writing_Others"},

    # === Marketing Digital y Ventas ===
    {"slug": "sales-marketing", "subcategoria": "seo", "nombre": "Sales_SEO"},
    {"slug": "sales-marketing", "subcategoria": "community-management", "nombre": "Sales_Community_Management"},
    {"slug": "sales-marketing", "subcategoria": "advertising-on-google-facebook", "nombre": "Sales_Online_Advertising"},
    {"slug": "sales-marketing", "subcategoria": "e-mail-marketing", "nombre": "Sales_Email_Marketing"},
    {"slug": "sales-marketing", "subcategoria": "data-analytics", "nombre": "Sales_Data_Analytics"},
    {"slug": "sales-marketing", "subcategoria": "televentas", "nombre": "Sales_Telemarketing"},
    {"slug": "sales-marketing", "subcategoria": "sales-executive", "nombre": "Sales_Executive"},
    {"slug": "sales-marketing", "subcategoria": "artificial-intelligence-6", "nombre": "Sales_AI"},
    {"slug": "sales-marketing", "subcategoria": "others", "nombre": "Sales_Others"},

    # === Soporte Administrativo ===
    {"slug": "admin-support", "subcategoria": "virtual-assistant-1", "nombre": "Admin_Virtual_Assistant"},
    {"slug": "admin-support", "subcategoria": "customer-support", "nombre": "Admin_Customer_Support"},
    {"slug": "admin-support", "subcategoria": "data-entry-1", "nombre": "Admin_Data_Entry"},
    {"slug": "admin-support", "subcategoria": "market-research-1", "nombre": "Admin_Market_Research"},
    {"slug": "admin-support", "subcategoria": "telesales", "nombre": "Admin_Telesales"},
    {"slug": "admin-support", "subcategoria": "artificial-intelligence-3", "nombre": "Admin_AI"},
    {"slug": "admin-support", "subcategoria": "others-2", "nombre": "Admin_Others"},

    # === Legal ===
    {"slug": "legal", "subcategoria": "", "nombre": "Legal_All"},

    # === Finanzas y Negocios ===
    {"slug": "finance-management", "subcategoria": "gather-data", "nombre": "Finance_Data_Collection"},
    {"slug": "finance-management", "subcategoria": "work-with-a-crm", "nombre": "Finance_CRM_Management"},
    {"slug": "finance-management", "subcategoria": "project-management-1", "nombre": "Finance_Project_Management"},
    {"slug": "finance-management", "subcategoria": "recruiting", "nombre": "Finance_Recruiting"},
    {"slug": "finance-management", "subcategoria": "strategic-planning-1", "nombre": "Finance_Strategic_Planning"},
    {"slug": "finance-management", "subcategoria": "accounting-1", "nombre": "Finance_Accounting"},
    {"slug": "finance-management", "subcategoria": "artificial-intelligence-5", "nombre": "Finance_AI"},
    {"slug": "finance-management", "subcategoria": "others-4", "nombre": "Finance_Others"},

    # === Ingeniería y Arquitectura ===
    {"slug": "engineering-manufacturing", "subcategoria": "industrial-design-1", "nombre": "Engineering_Industrial_Design"},
    {"slug": "engineering-manufacturing", "subcategoria": "cad-drawing", "nombre": "Engineering_CAD_Drawing"},
    {"slug": "engineering-manufacturing", "subcategoria": "3d-modelling-1", "nombre": "Engineering_3D_Modelling"},
    {"slug": "engineering-manufacturing", "subcategoria": "interior-design-1", "nombre": "Engineering_Interior_Design"},
    {"slug": "engineering-manufacturing", "subcategoria": "artificial-intelligence-4", "nombre": "Engineering_AI"},
    {"slug": "engineering-manufacturing", "subcategoria": "others-3", "nombre": "Engineering_Others"},
]

pagina_inicio = 1
print("Iniciando scraping de Workana...")
if args.debug:
    print("Modo debug activado - Se mostrarán mensajes detallados")

# =============================================================================
# SISTEMA DE CHECKPOINT - REANUDAR SESIÓN INTERRUMPIDA
# =============================================================================
should_resume, checkpoint_data, checkpoint_manager = get_resume_info("workana")

if should_resume:
    print("Reanudando desde checkpoint...")
    start_category_index = checkpoint_data.get('current_category_index', 0)
    start_page = checkpoint_data.get('current_page', 1)
    categories_completed = set(checkpoint_data.get('categories_completed', []))
    total_jobs_scraped = checkpoint_data.get('total_jobs_scraped', 0)
    print(f"Iniciando desde categoría #{start_category_index + 1}, página {start_page}")
    print(f"Jobs recolectados previamente: {total_jobs_scraped}")
else:
    print("Iniciando scraping completo desde el principio...")
    start_category_index = 0
    start_page = 1
    categories_completed = set()
    total_jobs_scraped = 0
    checkpoint_manager = CheckpointManager("workana")

# Update global variables for signal handler
current_category_index = start_category_index
current_page = start_page

# HASH GLOBAL para evitar duplicados entre categorías
HASHES_GLOBALES = set()

# Cargar hashes existentes de todos los archivos
print("Cargando hashes existentes para evitar duplicados entre categorías...")
for cat in categorias:
    categoria_nombre = cat["nombre"]
    timestamp = date.today().strftime("%Y%m%d")
    archivo_existente = f"output_jobs/Workana_{categoria_nombre}_{timestamp}.json"
    if os.path.exists(archivo_existente):
        try:
            with open(archivo_existente, 'r', encoding='utf-8') as f:
                empleos_existentes = json.load(f)
                for empleo in empleos_existentes:
                    h = empleo.get("hash Descripcion")
                    if h:
                        HASHES_GLOBALES.add(h)
        except:
            pass

print(f"Cargados {len(HASHES_GLOBALES)} hashes existentes")

jobs_this_session = 0

for cat_index, cat in enumerate(categorias):
    # Skip categories that were already completed
    if cat_index < start_category_index:
        continue
        
    categoria_slug = cat["slug"]
    subcategoria_slug = cat["subcategoria"]
    categoria_nombre = cat["nombre"]
    
    # Update global variables for signal handler
    current_category_index = cat_index
    
    # Skip categories that were already completed in previous session
    if categoria_nombre in categories_completed:
        print(f"Saltando categoría ya completada: {categoria_nombre}")
        continue

    print(f"\n{'='*80}")
    print(f"PROCESANDO CATEGORÍA {cat_index + 1}/{len(categorias)}: {categoria_nombre}")
    print(f"{'='*80}")

    # Obtener el número total de páginas para esta categoría/subcategoría
    total_paginas = obtener_total_paginas(driver, categoria_slug, subcategoria_slug)
    
    print(f"\nIniciando extracción para {categoria_nombre}")
    print(f"Encontradas {total_paginas} páginas para procesar")
    
    # Determine starting page (resume from checkpoint if this is the current category)
    current_start_page = start_page if cat_index == start_category_index else pagina_inicio
    
    # Usar todas las páginas encontradas por el binary search
    for pagina in range(current_start_page, total_paginas + 1):
        print(f"\n Procesando página {pagina}/{total_paginas} de {categoria_nombre}")
        
        # Update global variables for signal handler
        current_page = pagina
        
        # Save checkpoint before each page
        checkpoint_data = WorkanaCheckpoint.create_checkpoint_data(
            cat_index, pagina, list(categories_completed), total_jobs_scraped
        )
        checkpoint_manager.save_checkpoint(checkpoint_data)
        # Agregar filtros de ubicación también aquí
        url = f"https://www.workana.com/jobs?category={categoria_slug}&language=en%2Ces&subcategory={subcategoria_slug}&page={pagina}"
        debug_print(f"\nAccediendo a URL: {url}")
        
        driver.get(url)
        time.sleep(random.uniform(3, 5))  # Pausa más corta pero aún aleatoria

        try:
            links_empleos = WebDriverWait(driver, 5).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.project-header h2 a"))
            )
        except:
            debug_print(f"No se encontraron empleos en página {pagina}")
            continue
        
        if not args.debug:
            print(f"\nPágina {pagina}/{total_paginas} - {len(links_empleos)} empleos encontrados:")

        # Extract all URLs first to avoid stale element references
        urls_empleos = []
        for link in links_empleos:
            try:
                url = link.get_attribute("href")
                if url:
                    urls_empleos.append(url)
            except:
                continue

        for i, url_empleo in enumerate(urls_empleos):
            # Reuse the same window instead of opening new ones
            driver.get(url_empleo)

            debug_print(f"\nProcesando empleo {i+1}: {url_empleo}")
            
            try:
                contenedor = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div/div[2]/section/section/div/section/article/div[2]'))
                )
                descripcion = contenedor.text.strip()
                debug_print("  [OK] Descripción extraída correctamente")
            except Exception as e:
                descripcion = "Descripción no disponible"
                debug_print(f"  [ERROR] Al extraer descripción: {str(e)}")
                
            if not args.debug:
                print(f"  {i} - {tituloPuesto if 'tituloPuesto' in locals() else '...'}")

            categoria = "No disponible"
            subcategoria = "No disponible"
            try:
                parrafos = driver.find_elements(By.TAG_NAME, "p")
                for p in parrafos:
                    texto = p.text
                    if "Categoría" in texto:
                        match_categoria = re.search(r"Categor[ií]a\s*:?[\s\n]*([\w\sáéíóúÁÉÍÓÚñÑ\-]+)", texto)
                        if match_categoria:
                            categoria = match_categoria.group(1).strip()
                    if "Subcategoría" in texto:
                        match_subcategoria = re.search(r"Subcategor[ií]a\s*:?[\s\n]*([\w\sáéíóúÁÉÍÓÚñÑ\-]+)", texto)
                        if match_subcategoria:
                            subcategoria = match_subcategoria.group(1).strip()
            except:
                pass

            try:
                titulo = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.h3.title"))
                )
                tituloPuesto = titulo.text
            except:
                tituloPuesto = "Título no disponible"

            try:
                fecha_texto_elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="productName"]/p'))
                )
                texto_completo = fecha_texto_elem.text.strip()
                match_fecha = re.search(r'(\d{1,2}\s\w+,\s\d{4})', texto_completo)
                if match_fecha:
                    fecha_publicacion = match_fecha.group(1)
                else:
                    fecha_publicacion = "Fecha no disponible"
            except:
                fecha_publicacion = "Fecha no disponible"

            try:
                contenedor_requisitos = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div/div[2]/section/section[1]/div/section/article/div[3]'))
                )
                requisitos_elems = contenedor_requisitos.find_elements(By.TAG_NAME, "a")
                conocimientos_valorado = [elem.text.strip() for elem in requisitos_elems]
            except Exception:
                conocimientos_valorado = []

            try:
                perfil_elem = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div/div[2]/section/section[1]/div/aside/article[3]/div[1]/a'))
                )
                url_perfil_cliente = perfil_elem.get_attribute("href")
            except:
                url_perfil_cliente = None

            cliente_nombre = "Nombre no disponible"
            pais = "País no disponible"

            if url_perfil_cliente:
                # Save current job URL to return to it later
                current_job_url = driver.current_url
                driver.get(url_perfil_cliente)

                try:
                    nombre_elem = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#section-personal-data > div.h1"))
                    )
                    cliente_nombre = nombre_elem.text.strip()
                except:
                    pass

                try:
                    pais_elem = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "#section-personal-data > div:nth-child(3) > span.country > span > a"))
                    )
                    pais = pais_elem.text.strip()
                except:
                    pass

                # Return to the job page to continue processing
                driver.get(current_job_url)

            # Get current date for job entry
            today = date.today().strftime("%d/%m/%Y")

            # Convert conocimientos_valorado list to string
            conocimientos_str = ", ".join(conocimientos_valorado) if conocimientos_valorado else ""
            desc_completa = descripcion + ("\n\nConocimientos valorados: " + conocimientos_str if conocimientos_str else "")
            
            # Calcular hash del empleo
            hash_empleo = calcular_hash(descripcion)
            
            # Verificar si ya existe globalmente
            if hash_empleo not in HASHES_GLOBALES:
                EMPLEOS.append({
                    "Id Interno": f"{categoria_nombre}-{pagina}-{i+1}",
                    "titulo": tituloPuesto,
                    "descripcion": desc_completa,
                    "Empresa": cliente_nombre,
                    "Fuente": "Workana",
                    "Tipo Portal":"No Tradicional",
                    "url": url_empleo,
                    "Pais": pais,
                    "Ubicacion": pais,
                    "Categoria Portal": categoria_slug,
                    "Subcategoria Portal": subcategoria_slug,
                    "Categorria":"",
                    "Subcategoria":"",
                    "hash Descripcion": hash_empleo,
                    "fecha": today,
                    
                })
                HASHES_GLOBALES.add(hash_empleo)
                total_jobs_scraped += 1
                jobs_this_session += 1
                debug_print(f"    [NUEVO] Empleo agregado - País: {pais} (Total: {total_jobs_scraped})")
            else:
                debug_print(f"    [DUPLICADO] Ya existe en otra categoría, omitiendo")

            # Pausa corta entre cada empleo para no saturar
            time.sleep(random.uniform(1, 2))
    
    # Guardado incremental por categoría
    print(f"\n{'='*60}")
    print(f"Categoría '{categoria_nombre}' completada - Guardando datos...")
    print(f"Jobs en esta categoría: {len(EMPLEOS)}")
    print(f"Total acumulado: {total_jobs_scraped}")
    print(f"{'='*60}")
    
    guardar_datos_incremental(EMPLEOS, categoria_nombre)
    EMPLEOS = []  # Limpiar lista después de guardar
    
    # Mark category as completed
    categories_completed.add(categoria_nombre)
    
    # Reset start_page for next category
    start_page = 1

# Final cleanup
try:
    driver.quit()
except:
    pass

# Clear checkpoint after successful completion
checkpoint_manager.clear_checkpoint()

print(f"\nPROCESO COMPLETADO EXITOSAMENTE!")
print(f"Resumen de la sesión:")
print(f"   - Jobs recolectados en esta sesión: {jobs_this_session}")
print(f"   - Total de jobs recolectados: {total_jobs_scraped}")
print(f"   - Categorías completadas: {len(categories_completed)}/{len(categorias)}")
print(f"   - Todos los datos guardados en: output_jobs/")