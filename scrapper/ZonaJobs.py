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
from checkpoint_manager import CheckpointManager, ZonaJobsCheckpoint, get_resume_info

# Colores ANSI para tmux - Verde para ZonaJobs
GREEN = '\033[0;32m'
RESET = '\033[0m'

# Sobrescribir la función print para colorear todo
_original_print = builtins.print
def print(*args, **kwargs):
    """Print coloreado en verde para ZonaJobs"""
    colored_args = [f"{GREEN}{arg}{RESET}" if isinstance(arg, str) else arg for arg in args]
    _original_print(*colored_args, **kwargs)
builtins.print = print

# Configurar argumentos de línea de comandos
parser = argparse.ArgumentParser(description='Script de scraping para ZonaJobs')
parser.add_argument('--debug', action='store_true', help='Activar mensajes de debug')
parser.add_argument('--start-from', type=str, help='Iniciar desde una área específica (ej: tecnologia-sistemas-y-telecomunicaciones)')
args = parser.parse_args()

def colorize(text):
    """Colorea el texto en verde para ZonaJobs"""
    return f"{GREEN}{text}{RESET}"

def debug_print(*mensaje, **kwargs):
    if args.debug:
        _original_print(colorize(' '.join(map(str, mensaje))), **kwargs)

def print_colored(*mensaje, **kwargs):
    """Imprime siempre con color"""
    _original_print(colorize(' '.join(map(str, mensaje))), **kwargs)

# Global variables for signal handler
driver = None
checkpoint_manager = None
current_area_index = 0
current_page = 1
areas_completed = set()
total_jobs_scraped = 0

def signal_handler(sig, frame):
    """Handle CTRL+C gracefully by saving checkpoint"""
    print(f"\n\nInterrupción detectada (CTRL+C)")
    print("Guardando checkpoint para poder reanudar...")
    
    if checkpoint_manager:
        checkpoint_data = ZonaJobsCheckpoint.create_checkpoint_data(
            current_area_index, current_page, list(areas_completed), total_jobs_scraped
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
def create_driver():
    """Crea un nuevo driver de Chrome con configuración optimizada"""
    options = webdriver.ChromeOptions()
    
    # Configuración para estabilidad
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')
    
    # Configuración de memoria
    options.add_argument('--max_old_space_size=4096')
    options.add_argument('--memory-pressure-off')
    
    # Configuración de red
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=VizDisplayCompositor')
    
    # Evitar detección como bot
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.maximize_window()
    
    return driver

def verificar_sesion_activa(driver):
    """Verifica si la sesión del driver sigue activa"""
    try:
        driver.current_url
        return True
    except Exception:
        return False

def recrear_driver_si_necesario(driver):
    """Recrea el driver si la sesión está perdida"""
    if not verificar_sesion_activa(driver):
        print("Sesión perdida. Recreando driver...")
        try:
            driver.quit()
        except:
            pass
        return create_driver()
    return driver

driver = create_driver()
import hashlib

def calcular_hash(texto):
    if not isinstance(texto, str):
        return None
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

def guardar_datos_incremental(empleos, area, archivo_base="output_jobs/ZonaJobs"):
    """
    Guarda los datos incrementalmente (ya no necesita filtrar duplicados)
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

areas = [
"comercial-ventas-y-negocios",
"administracion-contabilidad-y-finanzas",
"produccion-y-manufactura",
"oficios-y-otros",
"abastecimiento-y-logistica",
"salud-medicina-y-farmacia",
"gastronomia-y-turismo",
"tecnologia-sistemas-y-telecomunicaciones",
"atencion-al-cliente-call-center-y-telemarketing",
"marketing-y-publicidad",
"ingenieria-civil-y-construccion",
"recursos-humanos-y-capacitacion",
"ingenierias",
"diseno",
"secretarias-y-recepcion",
"seguros",
"legales",
"aduana-y-comercio-exterior",
"educacion-docencia-e-investigacion",
"gerencia-y-direccion-general",
"comunicacion-relaciones-institucionales-y-publicas",
"departamento-tecnico",
"enfermeria",
"minería-petroleo-y-gas",
"sociologia-trabajo-social",
"naviero-maritimo-portuario",
]

#categoria_slug = "tecnologia-sistemas-y-telecomunicaciones"  # Para nombre archivo
EMPLEOS = []

def verificar_pagina_existe(driver, url, page_num):
    test_url = f"{url}?page={page_num}"
    driver.get(test_url)
    intentos = 3  # Número de intentos en caso de error
    
    for intento in range(intentos):
        try:
            # Esperar a que cargue el contenido
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#listado-avisos'))
            )
            
            # Esperar un poco más para asegurar que los empleos se carguen
            driver.implicitly_wait(2)
            
            # Esperar a que cargue el contenido
            listado = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#listado-avisos'))
            )
            
            # Esperar a que desaparezca el mensaje de "Buscando ofertas de empleo" si existe
            try:
                WebDriverWait(driver, 5).until_not(
                    EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Buscando ofertas')]"))
                )
            except:
                pass

            
            # Intentar diferentes selectores hasta encontrar los empleos
            empleos = []
            
            # Obtener empleos usando el selector optimizado
            empleos = driver.find_elements(By.CSS_SELECTOR, '#listado-avisos > div > a')
            
            # Filtrar empleos válidos
            empleos_validos = []
            for empleo in empleos:
                try:
                    # Si el elemento es un enlace, usar directamente
                    if empleo.tag_name == 'a':
                        elemento_a = empleo
                    else:
                        # Si no es un enlace, buscar el enlace dentro del elemento
                        elemento_a = empleo.find_element(By.TAG_NAME, 'a')
                    
                    href = elemento_a.get_attribute('href')
                    texto = elemento_a.text.strip()
                    
                    # Un empleo válido debe:
                    # 1. Tener URL
                    # 2. No ser enlace de paginación
                    # 3. No ser enlace de navegación
                    # 4. Contener texto de título
                    # 5. No ser mensaje de búsqueda
                    if (href and 
                        'page=' not in href and 
                        '#' not in href and 
                        'empleos-area-' not in href and
                        texto and
                        not texto.isdigit() and  # No es un número de página
                        texto.lower() not in ['relevantes', 'recientes', 'buscando ofertas de empleo']):  # No es botón de ordenamiento ni mensaje de búsqueda
                        
                        empleos_validos.append(elemento_a)
                        debug_print(f"\nDEBUG - Empleo válido encontrado:")
                        debug_print(f"URL: {href}")
                        debug_print(f"Título: {texto[:100]}")
                        
                except Exception as e:
                    debug_print(f"Error al procesar empleo: {str(e)}")
                    continue
                    
            # Verificar si estamos en la página correcta
            if page_num > 1:
                current_url = driver.current_url
                if f"page={page_num}" not in current_url:
                    print(f"Página {page_num}: Redirección detectada")
                    return False
            
            # DEBUG: Imprimir información detallada de los empleos encontrados
            debug_print(f"\nDEBUG - Página {page_num}:")
            debug_print(f"URL solicitada: {test_url}")
            debug_print(f"Empleos totales encontrados: {len(empleos)}")
            debug_print(f"Empleos válidos (excluyendo navegación): {len(empleos_validos)}")
            
            # La página existe solo si tiene empleos válidos (excluyendo navegación)
            tiene_empleos = len(empleos_validos) > 0
            print(f"Página {page_num}: {len(empleos_validos)} empleos válidos encontrados")
           
            
            return tiene_empleos
            
        except Exception as e:
            if intento < intentos - 1:
                print(f"Intento {intento + 1} falló, reintentando...")
                driver.refresh()
                continue
            else:
                print(f"Error verificando página {page_num}: {str(e)}")
                return False
    
    return False

def obtener_total_paginas(driver, area):
    url = f"https://www.zonajobs.com.ar/empleos-area-{area}.html"
    driver.get(url)
    try:
        print(f"Analizando área: {area}")
        debug_print("Esperando que cargue la página inicial...")
        # Esperar a que el contenedor principal esté presente
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#listado-avisos'))
        )
        # Esperar a que desaparezca cualquier indicador de carga si existe
        driver.implicitly_wait(5)
        
        # Imprimir información de debug sobre la página
        debug_print("\nDEBUG - Información de la página inicial:")
        debug_print(f"URL actual: {driver.current_url}")
        debug_print(f"Título de la página: {driver.title}")
        
        # Verificar que la primera página tiene contenido
        if not verificar_pagina_existe(driver, url, 1):
            print("No se encontraron empleos en la primera página")
            return 1

        # Verificación rápida de páginas clave
        debug_print("\nRealizando verificación inicial de páginas clave...")
        paginas_prueba = [50, 100, 150]
        ultima_valida = 1
        
        for pagina in paginas_prueba:
            if verificar_pagina_existe(driver, url, pagina):
                ultima_valida = pagina
            else:
                break
        
        # Ajustar el rango de búsqueda basado en la verificación inicial
        if ultima_valida == 1:
            rango_busqueda = 50
        elif ultima_valida == 50:
            rango_busqueda = 100
        else:
            rango_busqueda = ultima_valida + 50

        # Búsqueda binaria refinada para encontrar la última página
        debug_print("\nRealizando búsqueda binaria para encontrar la última página...")
        left = ultima_valida
        right = rango_busqueda
        ultima_pagina_valida = ultima_valida
        pagina_actual = None
        
        # Primera fase: búsqueda binaria
        while left <= right:
            mid = (left + right) // 2
            if pagina_actual == mid:  # Evitar verificar la misma página dos veces
                break
                
            pagina_actual = mid
            debug_print(f"\nProbando página {mid}...")
            
            if verificar_pagina_existe(driver, url, mid):
                ultima_pagina_valida = mid
                left = mid + 1
            else:
                right = mid - 1
        
        # Segunda fase: búsqueda secuencial desde la última página válida
        # Límite razonable para evitar bucles infinitos
        max_paginas_secuencial = 50
        paginas_verificadas = 0
        
        pagina = ultima_pagina_valida
        while paginas_verificadas < max_paginas_secuencial:
            if not verificar_pagina_existe(driver, url, pagina + 1):
                debug_print(f"Encontrada última página válida: {pagina}")
                return pagina
            
            pagina += 1
            paginas_verificadas += 1
            debug_print(f"Verificada página {pagina} (verificaciones: {paginas_verificadas})")
        
        # Si llegamos aquí, hemos verificado demasiadas páginas
        debug_print(f"Límite de verificaciones alcanzado, retornando página {pagina}")
        return pagina

    except Exception as e:
        print(f"\nError al obtener total de páginas: {str(e)}")
        if verificar_pagina_existe(driver, url, 1):
            print("Usando valor conservador de 50 páginas")
            return 50
        return 1

print("Iniciando scraping de ZonaJobs...")
if args.debug:
    print("Modo debug activado - Se mostrarán mensajes detallados")

if args.start_from:
    print(f"Iniciando desde la categoría: {args.start_from}")

# HASH GLOBAL para evitar duplicados entre categorías
HASHES_GLOBALES = set()

# Cargar hashes existentes de todos los archivos
print("Cargando hashes existentes para evitar duplicados entre categorías...")
for area in areas:
    timestamp = date.today().strftime("%Y%m%d")
    archivo_existente = f"output_jobs/ZonaJobs_{area}_{timestamp}.json"
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

# =============================================================================
# SISTEMA DE CHECKPOINT - REANUDAR SESIÓN INTERRUMPIDA
# =============================================================================
should_resume, checkpoint_data, checkpoint_manager = get_resume_info("zonajobs")

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
    checkpoint_manager = CheckpointManager("zonajobs")

# Update global variables for signal handler
current_area_index = start_area_index
current_page = start_page

jobs_this_session = 0

# Determinar desde qué área comenzar (combinando checkpoint con --start-from si está presente)
start_index = start_area_index
if args.start_from and not should_resume:
    try:
        start_index = areas.index(args.start_from)
        print(f"Iniciando desde el índice {start_index}: {args.start_from}")
    except ValueError:
        print(f"Área '{args.start_from}' no encontrada. Iniciando desde el principio.")
        print(f"Áreas disponibles: {', '.join(areas[:5])}...")

areas_to_process = areas[start_index:]
print(f"Procesando {len(areas_to_process)} áreas restantes...")

import time  # Add import for time

for area_index, area in enumerate(areas_to_process, start_index):
    # Skip areas that were already completed
    if area in areas_completed:
        print(f"Saltando área ya completada: {area}")
        continue
        
    # Update global variables for signal handler
    current_area_index = area_index
    
    print(f"\n{'='*80}")
    print(f"PROCESANDO ÁREA {area_index + 1}/{len(areas)}: {area}")
    print(f"{'='*80}")
    
    # Verificar y recrear driver si es necesario
    driver = recrear_driver_si_necesario(driver)
    
    try:
        # Obtener el número total de páginas para esta área
        total_paginas = obtener_total_paginas(driver, area)
        print(f"Encontradas {total_paginas} páginas para {area}")
        print("Comenzando extracción de empleos...")
        
        # Determine starting page (resume from checkpoint if this is the current area)
        current_start_page = start_page if area_index == start_area_index else 1
        
        for pagina in range(current_start_page, total_paginas + 1):
            print(f"\n Procesando página {pagina}/{total_paginas} de {area}")
            
            # Update global variables for signal handler
            current_page = pagina
            
            # Save checkpoint before each page
            checkpoint_data = ZonaJobsCheckpoint.create_checkpoint_data(
                area_index, pagina, list(areas_completed), total_jobs_scraped
            )
            checkpoint_manager.save_checkpoint(checkpoint_data)
            
            # Verificar sesión antes de cada página
            driver = recrear_driver_si_necesario(driver)
            
            url = f"https://www.zonajobs.com.ar/empleos-area-{area}.html?page={pagina}"

            try:
                driver.get(url)

                # Esperar a que carguen los links de empleo
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#listado-avisos > div > a'))
                    )
                except:
                    print(f"No se encontraron empleos en la página {pagina}")
                    continue

                # Extraer URLs de todos los empleos para no invalidar elementos
                links_empleos = driver.find_elements(By.CSS_SELECTOR, '#listado-avisos > div > a')
                urls_empleos = []
                
                # Filtrar empleos válidos
                for link in links_empleos:
                    texto = link.text.strip()
                    href = link.get_attribute("href")
                    if (href and 
                        texto and 
                        texto.lower() != 'buscando ofertas de empleo'):
                        urls_empleos.append(href)
                
                # Mostrar progreso
                if not args.debug:
                    print(f"\nPágina {pagina}/{total_paginas} - {len(urls_empleos)} empleos encontrados:")

                # Procesar empleos con manejo de errores mejorado
                for i, url_empleo in enumerate(urls_empleos):
                    try:
                        # Verificar sesión antes de procesar cada empleo
                        driver = recrear_driver_si_necesario(driver)
                        
                        if args.debug:
                            debug_print(f"Procesando empleo {i+1} en página {pagina}/{total_paginas}: {url_empleo}")
                        elif i == 0 and pagina % 10 == 0:
                            print(f"Página {pagina}/{total_paginas}: Procesando {len(urls_empleos)} empleos...")

                        # Navegar directamente a la URL del empleo en la ventana actual
                        driver.get(url_empleo)
                        
                        WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
                        )
                        
                        # OPTIMIZED: Reduced sleep from 1 to 0.3 seconds
                        time.sleep(0.3)
                        
                        # --- DETECCIÓN TEMPRANA DE DUPLICADOS ---
                        # Primero extraer solo descripción para verificar duplicados
                        try:
                            descripcion = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.XPATH, '//*[@id="ficha-detalle"]/div[2]/div/div[1]/p'))
                            ).text
                        except:
                            descripcion = "Descripción no disponible"
                        
                        # Calcular hash temprano para verificar duplicados
                        hash_empleo = calcular_hash(descripcion)
                        
                        # DETECCIÓN TEMPRANA DE DUPLICADOS: Si ya existe, saltar al siguiente sin extraer más datos
                        if hash_empleo in HASHES_GLOBALES:
                            debug_print(f"    [DUPLICADO TEMPRANO] Saltando empleo {i+1} - ya existe")
                            if not args.debug:
                                print(f"{i} - [DUPLICADO] Saltando...")
                            continue
                        
                        # Si no es duplicado, extraer el resto de los datos
                        try:
                            tituloPuesto = WebDriverWait(driver, 2).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
                            ).text
                            if not args.debug:  # En modo normal, mostrar cada empleo
                                print(f"{i} - {tituloPuesto}")
                        except:
                            tituloPuesto = "Título no disponible"
                            if not args.debug:
                                print(f"{i} - [Título no disponible]")

                        try:
                            ubicacion = WebDriverWait(driver, 3).until(
                                EC.presence_of_element_located((By.XPATH, '//*[@id="ficha-detalle"]/div[2]/div/div[1]/div[1]/div[2]/div/div'))
                            ).find_element(By.TAG_NAME, "h2").text
                        except:
                            ubicacion = "Ubicación no disponible"

                        try:
                            # Buscar el elemento de empresa con múltiples selectores
                            empresa_element = None
                            empresa_selectors = [
                                '//*[@id="root"]/div/div[2]/div[2]/div/div[2]/div[2]/div[3]/div/div/div[2]',
                                '//div[contains(@class, "company")]//span',
                                '//div[contains(text(), "Empresa")]/following-sibling::div',
                                '//span[contains(@class, "company-name")]'
                            ]
                            
                            for selector in empresa_selectors:
                                try:
                                    empresa_element = WebDriverWait(driver, 1).until(
                                        EC.presence_of_element_located((By.XPATH, selector))
                                    )
                                    break
                                except:
                                    continue
                            
                            if not empresa_element:
                                empresa = "NA/NA"
                            else:
                                max_attempts = 3
                                empresa = ""
                                
                                for attempt in range(max_attempts):
                                    try:
                                        empresa = empresa_element.text.strip()
                                        
                                        # Verificar si el contenido se ha cargado correctamente
                                        if (empresa and 
                                            empresa != "Loading..." and 
                                            empresa != "" and
                                            len(empresa) > 0 and
                                            not empresa.startswith("Loading")):
                                            debug_print(f"Empresa encontrada: '{empresa}' (intento {attempt + 1})")
                                            break
                                            
                                    except Exception:
                                        pass
                                    
                                    time.sleep(0.3)
                                
                                # Si después de todo sigue siendo Loading o vacío, usar NA/NA
                                if not empresa or empresa == "Loading..." or empresa.startswith("Loading"):
                                    empresa = "NA/NA"
                                
                        except Exception as e:
                            debug_print(f"Error extrayendo empresa: {str(e)}")
                            empresa = "NA/NA"
                            
                        try:
                            categoria_portal = WebDriverWait(driver, 0.5).until(
                                EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div[2]/div[1]/div/div/div/h2/a[2]'))
                            ).text.strip()
                        except:
                            categoria_portal = "No disponible"

                        try:
                            subcategoria_portal = WebDriverWait(driver, 0.5).until(
                                EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/div[2]/div[1]/div/div/div/h2/a[3]'))
                            ).text.strip()
                        except:
                            subcategoria_portal = "No disponible"

                        today = date.today().strftime("%d/%m/%Y")

                        # Como ya verificamos que no es duplicado arriba, agregarlo directamente
                        EMPLEOS.append({
                            "Id Interno": f"{pagina}-{i+1}",
                            "titulo": tituloPuesto,
                            "descripcion": descripcion,
                            "Empresa": empresa,
                            "Fuente": "ZonaJobs",
                            "Tipo Portal":"Tradicional",
                            "url": url_empleo,
                            "Pais": "Argentina",
                            "ubicacion": ubicacion,
                            "Categoria Portal": categoria_portal,
                            "Subcategoria Portal": subcategoria_portal,
                            "Categorria":"",
                            "Subcategoria":"",
                            "hash Descripcion": hash_empleo,
                            "fecha":today 
                        })
                        HASHES_GLOBALES.add(hash_empleo)
                        total_jobs_scraped += 1
                        jobs_this_session += 1
                        debug_print(f"    [NUEVO] Empleo agregado (Total: {total_jobs_scraped})")
                        
                    except Exception as e:
                        print(f"Error procesando empleo {i+1}: {str(e)}")
                        continue
                        
            except Exception as e:
                print(f"Error en página {pagina}: {str(e)}")
                # Recrear driver si es necesario
                driver = recrear_driver_si_necesario(driver)
                continue
        
        # Guardar empleos de esta área
        print(f"\n{'='*60}")
        print(f" Área '{area}' completada - Guardando datos...")
        print(f" Jobs en esta área: {len(EMPLEOS)}")
        print(f" Total acumulado: {total_jobs_scraped}")
        print(f"{'='*60}")
        
        guardar_datos_incremental(EMPLEOS, area)
        EMPLEOS = []  # Limpiar lista después de guardar
        
        # Mark area as completed
        areas_completed.add(area)
        
        # Reset start_page for next area
        start_page = 1
        
    except Exception as e:
        print(f"Error crítico en área {area}: {str(e)}")
        print("Intentando continuar con la siguiente área...")
        driver = recrear_driver_si_necesario(driver)
        continue

# Final cleanup
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
print(f"   - Áreas completadas: {len(areas_completed)}/{len(areas)}")
print(f"   - Todos los datos guardados en: output_jobs/")
print(f"Archivos guardados en: output_jobs/")
print(f"{'='*60}\n")