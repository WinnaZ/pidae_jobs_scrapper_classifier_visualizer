from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import tempfile
import time
import json
import shutil
import os
from datetime import date
import hashlib
import random
import argparse
import re
import builtins
import signal
import sys
from checkpoint_manager import CheckpointManager, ComputrabajoCheckpoint, get_resume_info

# Colores ANSI para tmux - Amarillo para Computrabajo México
YELLOW = '\033[0;33m'
RESET = '\033[0m'

# Sobrescribir la función print para colorear todo
_original_print = builtins.print
def print(*args, **kwargs):
    """Print coloreado en amarillo para Computrabajo México"""
    colored_args = [f"{YELLOW}{arg}{RESET}" if isinstance(arg, str) else arg for arg in args]
    _original_print(*colored_args, **kwargs)
builtins.print = print

# Configurar argumentos de línea de comandos
parser = argparse.ArgumentParser(description='Script de scraping para Computrabajo México')
parser.add_argument('--debug', action='store_true', help='Activar mensajes de debug')
args = parser.parse_args()

def debug_print(*mensaje, **kwargs):
    if args.debug:
        _original_print(f"{YELLOW}{' '.join(map(str, mensaje))}{RESET}", **kwargs)

# Global variables for signal handler
driver = None
checkpoint_manager = None
current_area_index = 0
current_page = 1
areas_completed = set()
total_jobs_scraped = 0

def signal_handler(sig, frame):
    """Handle CTRL+C gracefully by saving checkpoint"""
    print(f"\n\n⚠️  Interrupción detectada (CTRL+C)")
    print("💾 Guardando checkpoint para poder reanudar...")
    
    if checkpoint_manager:
        checkpoint_data = ComputrabajoCheckpoint.create_checkpoint_data(
            current_area_index, current_page, list(areas_completed), total_jobs_scraped
        )
        checkpoint_manager.save_checkpoint(checkpoint_data)
        print("✅ Checkpoint guardado exitosamente")
    
    if driver:
        try:
            driver.quit()
            print("🔒 Driver cerrado correctamente")
        except:
            pass
    
    print("👋 Hasta la próxima! Usa el mismo comando para reanudar.")
    sys.exit(0)

# Register signal handler
signal.signal(signal.SIGINT, signal_handler)

def guardar_datos_incremental(empleos, area, archivo_base="output_jobs/Computrabajo_MX"):
    """
    Guarda los datos incrementalmente para México
    """
    # Crear directorio si no existe
    os.makedirs("output_jobs", exist_ok=True)
    
    # Nombre del archivo
    timestamp = date.today().strftime("%Y%m%d")
    nombre_archivo = f"{archivo_base}_{area}_{timestamp}.json"
    
    # Leer datos existentes si el archivo existe
    empleos_existentes = []
    
    if os.path.exists(nombre_archivo):
        try:
            with open(nombre_archivo, 'r', encoding='utf-8') as f:
                empleos_existentes = json.load(f)
            print(f"Cargados {len(empleos_existentes)} empleos existentes del archivo")
        except Exception as ex:
            print(f"Archivo existente pero no se pudo leer ({ex}), creando nuevo")
    
    # Combinar y guardar
    todos_empleos = empleos_existentes + empleos
    
    with open(nombre_archivo, 'w', encoding='utf-8') as f:
        json.dump(todos_empleos, f, ensure_ascii=False, indent=4)
    
    print(f"\n📁 Guardado: {nombre_archivo}")
    print(f"  - Empleos nuevos: {len(empleos)}")
    print(f"  - Total en archivo: {len(todos_empleos)}")
    
    return nombre_archivo, len(empleos), 0

def calcular_hash(texto):
    if not isinstance(texto, str):
        return None
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def verificar_pagina_existe(driver, url, intentos=3):
    page_num = re.search(r'p=(\d+)', url)
    page_num = int(page_num.group(1)) if page_num else 1
    
    for intento in range(intentos):
        try:
            driver.get(url)
            driver.delete_all_cookies()
            time.sleep(random.uniform(1, 2))
            
            # Esperar a que cargue la página
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Verificar si hay mensaje de "no hay resultados"
            try:
                no_results = driver.find_elements(By.XPATH, "//*[contains(text(), 'No se encontraron') or contains(text(), 'no hay ofertas') or contains(text(), 'Sin resultados') or contains(text(), 'No hay ofertas')]")
                if no_results and any(elem.is_displayed() for elem in no_results):
                    print(f"Página {page_num}: 0 empleos válidos encontrados")
                    return False, 0
            except:
                pass
            
            # Selector principal para enlaces de empleos
            links_empleos = driver.find_elements(By.CSS_SELECTOR, "a.js-o-link")
            debug_print(f"    Selector encontró: {len(links_empleos)} enlaces")
            
            empleos_validos = []
            
            for link in links_empleos:
                try:
                    href = link.get_attribute("href")
                    
                    debug_print(f"    Analizando: href={href}")
                    
                    # Un empleo válido debe:
                    # 1. Tener URL de computrabajo México
                    # 2. Contener /ofertas-de-trabajo/oferta-de-trabajo-de- (página de detalle del empleo)
                    if href and 'mx.computrabajo.com' in href and '/ofertas-de-trabajo/oferta-de-trabajo-de-' in href:
                        empleos_validos.append(link)
                        debug_print(f"    [OK] Empleo válido")
                    else:
                        debug_print(f"    [X] Rechazado por URL inválida")
                except Exception as e:
                    debug_print(f"    [X] Error: {str(e)}")
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
                debug_print(f"  [X] Error verificando página: {str(e)}")
                print(f"Página {page_num}: Error al verificar")
                return False, 0
    
    return False, 0

def obtener_total_paginas(driver, categoria_slug):
    url_base = f"https://mx.computrabajo.com/trabajo-de-{categoria_slug}"
    
    print(f"\n🔍 Analizando cargo: {categoria_slug}")
    
    # Verificar primera página
    existe, num_empleos = verificar_pagina_existe(driver, f"{url_base}?p=1")
    if not existe:
        print("No se encontraron empleos en la primera página")
        return 1

    # Búsqueda optimizada por incrementos de 50
    left = 1
    right = 50
    ultima_pagina_valida = 1

    # Fase 1: Encontrar un límite superior usando incrementos de 50
    while True:
        existe, _ = verificar_pagina_existe(driver, f"{url_base}?p={right}")
        if not existe:
            break
        ultima_pagina_valida = right
        left = right
        right += 50
        
    # Fase 2: Búsqueda binaria refinada entre el último válido y el primer inválido
    while left <= right:
        mid = (left + right) // 2
        if left == mid or right == mid:
            break

        existe, _ = verificar_pagina_existe(driver, f"{url_base}?p={mid}")
        if existe:
            ultima_pagina_valida = mid
            left = mid + 1
        else:
            right = mid - 1

    # Fase 3: Verificación final
    while ultima_pagina_valida > 0:
        existe, _ = verificar_pagina_existe(driver, f"{url_base}?p={ultima_pagina_valida}")
        if existe:
            break
        ultima_pagina_valida -= 1

    print(f"📊 Total de páginas encontradas: {ultima_pagina_valida}")
    return ultima_pagina_valida

# Crear perfil temporal
temp_profile_dir = tempfile.mkdtemp()

# Configuración del driver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument(f"--user-data-dir={temp_profile_dir}")
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--log-level=3")
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.maximize_window()

EMPLEOS = []

# Lista de áreas/cargos más demandados en México
# Basada en "Empleos más demandados" de Computrabajo México (mx.computrabajo.com)
areas_predeterminadas = [
    # Empleos más buscados según la página
    "asesor-a-de-ventas",
    "ejecutivo-a-de-ventas",
    "atencion-al-cliente",
    "atencion-a-clientes",
    "auxiliar-administrativo-a",
    "gestor-de-cobranza",
    "asesor-de-ventas",
    "auxiliar-de-almacen",
    "ejecutivo-de-ventas",
    "auxiliar",
    "asesor-a",
    "auxiliar-contable",
    "almacenista",
    "vendedor-a",
    "ayudante-general",
    "agente-de-ventas",
    "chofer-de-reparto",
    "asesor-a-de-credito",
    "chofer",
    "supervisor-a",
    # Adicionales populares
    "recepcionista",
    "cajero-a",
    "promotor-a",
    "capturista",
    "contador-a",
    "secretaria",
    "programador",
    "desarrollador-web",
    "soporte-tecnico",
    "recursos-humanos",
    "disenador-grafico",
    "community-manager",
    "ingeniero-industrial",
    "mecanico",
    "electricista",
]

# Configuración
pagina_inicio = 1

# Ruta guardado
carpeta_salida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_jobs")
os.makedirs(carpeta_salida, exist_ok=True)

print("🇲🇽 Iniciando scraping de Computrabajo MÉXICO...")
if args.debug:
    print("🔧 Modo debug activado - Se mostrarán mensajes detallados")

# Usar directamente la lista predeterminada
areas = areas_predeterminadas
print(f"📋 Áreas a procesar: {', '.join(areas[:5])}... ({len(areas)} total)")

# HASH GLOBAL para evitar duplicados entre categorías
HASHES_GLOBALES = set()

# Cargar hashes existentes de todos los archivos
print("🔄 Cargando hashes existentes para evitar duplicados entre categorías...")
for area in areas:
    timestamp = date.today().strftime("%Y%m%d")
    archivo_existente = f"output_jobs/Computrabajo_MX_{area}_{timestamp}.json"
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

print(f"✅ Cargados {len(HASHES_GLOBALES)} hashes existentes")

# =============================================================================
# SISTEMA DE CHECKPOINT - REANUDAR SESIÓN INTERRUMPIDA
# =============================================================================
should_resume, checkpoint_data, checkpoint_manager = get_resume_info("computrabajo_mx")

if should_resume:
    print("🔄 Reanudando desde checkpoint...")
    start_area_index = checkpoint_data.get('current_area_index', 0)
    start_page = checkpoint_data.get('current_page', 1)
    areas_completed = set(checkpoint_data.get('areas_completed', []))
    total_jobs_scraped = checkpoint_data.get('total_jobs_scraped', 0)
    print(f"📍 Iniciando desde área #{start_area_index + 1}, página {start_page}")
    print(f"📊 Jobs recolectados previamente: {total_jobs_scraped}")
else:
    print("🚀 Iniciando scraping completo desde el principio...")
    start_area_index = 0
    start_page = 1
    areas_completed = set()
    total_jobs_scraped = 0
    checkpoint_manager = CheckpointManager("computrabajo_mx")

# Update global variables for signal handler
current_area_index = start_area_index
current_page = start_page

jobs_this_session = 0

try:
    for area_index, area in enumerate(areas):
        # Skip areas that were already completed
        if area_index < start_area_index:
            continue
            
        # Skip areas that were already completed in previous session
        if area in areas_completed:
            print(f"⏭️  Saltando área ya completada: {area}")
            continue
            
        # Update global variables for signal handler
        current_area_index = area_index
        
        print(f"\n{'='*80}")
        print(f"🇲🇽 PROCESANDO ÁREA {area_index + 1}/{len(areas)}: {area}")
        print(f"{'='*80}")
        
        # Obtener el número total de páginas para esta área
        total_paginas = obtener_total_paginas(driver, area)
        print(f"📄 Encontradas {total_paginas} páginas para {area}")
        print("⚙️  Comenzando extracción de empleos...")
        
        # Determine starting page (resume from checkpoint if this is the current area)
        current_start_page = start_page if area_index == start_area_index else pagina_inicio
        
        for pagina in range(current_start_page, total_paginas + 1):
            print(f"\n📄 Procesando página {pagina}/{total_paginas} de {area}")
            
            # Update global variables for signal handler
            current_page = pagina
            
            # Save checkpoint before each page
            checkpoint_data = ComputrabajoCheckpoint.create_checkpoint_data(
                area_index, pagina, list(areas_completed), total_jobs_scraped
            )
            checkpoint_manager.save_checkpoint(checkpoint_data)
            
            url = f"https://mx.computrabajo.com/trabajo-de-{area}?p={pagina}"
            debug_print(f"\nAccediendo a URL: {url}")
            
            driver.get(url)
            driver.delete_all_cookies()
            time.sleep(random.uniform(1, 3))

            # Esperar que carguen los enlaces de empleo
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.js-o-link"))
                )
            except TimeoutException:
                print(f"⚠️  No se encontraron enlaces en página {pagina}")
                continue

            links_empleos = [a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, "a.js-o-link")]
            
            # Filtrar solo URLs válidas de empleos de México
            links_empleos = [url for url in links_empleos if url and 'mx.computrabajo.com' in url and '/ofertas-de-trabajo/oferta-de-trabajo-de-' in url]
            
            if not args.debug:
                print(f"\nPágina {pagina}/{total_paginas} - {len(links_empleos)} empleos encontrados:")

            for i, url_empleo in enumerate(links_empleos):
                debug_print(f"\nProcesando empleo {i+1}: {url_empleo}")
                driver.get(url_empleo)

                # --- DETECCIÓN TEMPRANA DE DUPLICADOS ---
                try:
                    time.sleep(random.uniform(1, 3))
                    descripcion_elem = driver.find_element(By.XPATH, "/html/body/main/div[2]/div/div[2]/div[4]/p[1]")
                    descripcion = descripcion_elem.text.strip()
                except:
                    descripcion = "Requisitos no disponibles"

                try:
                    requisitos_elem = driver.find_element(By.XPATH, "//*[contains(text(),'Requerimientos')]/following::ul[1]")
                    requisitominimo = requisitos_elem.text.strip()
                except:
                    requisitominimo = "Requisitos no disponibles"
                
                # Calcular hash temprano para verificar duplicados
                desc_completa = descripcion + "\n\n" + requisitominimo
                hash_empleo = calcular_hash(desc_completa)
                
                # DETECCIÓN TEMPRANA DE DUPLICADOS
                if hash_empleo in HASHES_GLOBALES:
                    debug_print(f"    [DUPLICADO TEMPRANO] Saltando empleo {i+1} - ya existe")
                    if not args.debug:
                        print(f"  {i} - [DUPLICADO] 🔄 Saltando (ahorrando ~6s)...")
                    continue
                
                # Si no es duplicado, extraer el resto de los datos
                try:
                    tituloPuesto = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "h1"))
                    ).text.strip()
                    if not args.debug:
                        print(f"  {i} - {tituloPuesto}")
                except TimeoutException:
                    tituloPuesto = "Título no disponible"
                    if not args.debug:
                        print(f"  {i} - [Título no disponible]")

                try:
                    empresa_elem = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "/html/body/main/div[1]/p"))
                    )
                    texto_completo = empresa_elem.text.strip()
                    partes = texto_completo.split('-')
                    nombre_empresa = partes[0].strip()
                    ubicacionPuesto = partes[1].strip() if len(partes) > 1 else "Ubicación no disponible"
                except TimeoutException:
                    nombre_empresa = "Empresa no disponible"
                    ubicacionPuesto = "Ubicación no disponible"

                today = date.today().strftime("%d/%m/%Y")

                # Agregar empleo
                EMPLEOS.append({
                    "Id Interno": f"MX-{area}-{pagina}-{i+1}",
                    "titulo": tituloPuesto,
                    "descripcion": desc_completa,
                    "Empresa": nombre_empresa,
                    "Fuente": "Computrabajo",
                    "Tipo Portal": "Tradicional",
                    "url": url_empleo,
                    "Pais": "México",
                    "ubicacion": ubicacionPuesto,
                    "Categoria Portal": area,
                    "Subcategoria Portal": "No disponible",
                    "Categorria": "",
                    "Subcategoria": "",
                    "hash Descripcion": hash_empleo,
                    "fecha": today
                })
                HASHES_GLOBALES.add(hash_empleo)
                debug_print(f"    [NUEVO] ✅ Empleo agregado")
                
                # Update job counts for checkpoint
                jobs_this_session += 1
                total_jobs_scraped += 1
        
        # Guardado incremental por área
        print(f"\n{'='*60}")
        print(f"✅ Área '{area}' completada - Guardando datos...")
        print(f"{'='*60}")
        guardar_datos_incremental(EMPLEOS, area)
        EMPLEOS = []  # Limpiar lista después de guardar
        
        # Mark this area as completed
        areas_completed.add(area)
        print(f"📊 Área completada: {area}")
        print(f"📈 Jobs esta sesión: {jobs_this_session}")
        print(f"📊 Total jobs acumulados: {total_jobs_scraped}")
        
        # Save checkpoint after completing area
        checkpoint_data = ComputrabajoCheckpoint.create_checkpoint_data(
            area_index + 1, 1, list(areas_completed), total_jobs_scraped
        )
        checkpoint_manager.save_checkpoint(checkpoint_data)
    
    # All areas completed successfully
    print(f"\n🎉 ¡SCRAPING COMPLETADO EXITOSAMENTE!")
    print(f"📊 Jobs recolectados esta sesión: {jobs_this_session}")
    print(f"📈 Total jobs procesados: {total_jobs_scraped}")
    print(f"📋 Áreas procesadas: {len(areas)}")
    
    # Clear checkpoint since we completed successfully
    checkpoint_manager.clear_checkpoint()
    
except KeyboardInterrupt:
    print(f"\n⚠️  Scraping interrumpido por el usuario")
    print(f"💾 Checkpoint guardado automáticamente")
    print(f"📊 Jobs recolectados esta sesión: {jobs_this_session}")
    print(f"📈 Total jobs hasta ahora: {total_jobs_scraped}")
    print(f"🔄 Ejecuta el script nuevamente para continuar desde donde se detuvo")
    
    # Save any remaining jobs before exiting
    if EMPLEOS:
        print(f"💾 Guardando {len(EMPLEOS)} jobs pendientes...")
        guardar_datos_incremental(EMPLEOS, f"{area}_partial")
    
    sys.exit(0)

finally:
    driver.quit()
    shutil.rmtree(temp_profile_dir, ignore_errors=True)

print(f"\n✅ Proceso completado - Todos los datos guardados por área en output_jobs/")
print(f"🇲🇽 Archivos: Computrabajo_MX_[area]_[fecha].json")
print(f"🌐 Fuente: https://mx.computrabajo.com/")