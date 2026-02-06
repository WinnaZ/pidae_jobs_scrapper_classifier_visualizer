#!/usr/bin/env python3
"""
Computrabajo Colombia Scraper - FIXED VERSION
https://co.computrabajo.com/
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import tempfile
import time
import json
import shutil
import os
from datetime import date
import hashlib
import re
import argparse
import builtins
import signal
import sys

# Colores ANSI - Amarillo para Colombia
YELLOW = '\033[0;33m'
RESET = '\033[0m'

_original_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    colored_args = [f"{YELLOW}{arg}{RESET}" if isinstance(arg, str) else arg for arg in args]
    _original_print(*colored_args, **kwargs)
builtins.print = print

parser = argparse.ArgumentParser(description='Script de scraping para Computrabajo Colombia')
parser.add_argument('--debug', action='store_true', help='Activar mensajes de debug')
parser.add_argument('--start-from', type=str, help='Iniciar desde una categoría específica')
args = parser.parse_args()

def debug_print(*mensaje, **kwargs):
    if args.debug:
        _original_print(f"{YELLOW}{' '.join(map(str, mensaje))}{RESET}", flush=True, **kwargs)

# Variables globales
driver = None
total_jobs_scraped = 0
jobs_this_session = 0
EMPLEOS = []
HASHES_GLOBALES = set()
current_area = ""

def signal_handler(sig, frame):
    print(f"\n\nInterrupción detectada (CTRL+C)")
    if EMPLEOS:
        print(f"Guardando {len(EMPLEOS)} empleos pendientes...")
        guardar_datos_incremental(EMPLEOS, current_area or "partial")
    if driver:
        try:
            driver.quit()
        except:
            pass
    print(f"Total empleos guardados: {total_jobs_scraped}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def guardar_datos_incremental(empleos, area, archivo_base="output_jobs/Computrabajo_CO"):
    os.makedirs("output_jobs", exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d")
    nombre_archivo = f"{archivo_base}_{area}_{timestamp}.json"
    
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
    
    print(f"Guardado: {nombre_archivo} ({len(empleos)} nuevos, {len(todos_empleos)} total)")
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
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.set_page_load_timeout(30)
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

# =============================================================================
# BINARY SEARCH - ENCONTRAR NÚMERO EXACTO DE PÁGINAS
# =============================================================================

def verificar_pagina_existe(driver, url_base, page_num):
    """
    Verifica si una página existe y tiene empleos válidos
    Returns: (existe: bool, num_empleos: int)
    """
    try:
        url = f"{url_base}?p={page_num}"
        debug_print(f"Verificando página {page_num}: {url}")
        
        try:
            driver.get(url)
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a.js-o-link")))
        except:
            driver.execute_script("window.stop();")
        
        time.sleep(0.5)
        
        # Buscar enlaces a empleos
        links = driver.find_elements(By.CSS_SELECTOR, "a.js-o-link")
        valid_jobs = 0
        
        for link in links:
            try:
                href = link.get_attribute("href")
                if href and '/ofertas-de-trabajo/' in href:
                    valid_jobs += 1
            except:
                continue
        
        if valid_jobs > 0:
            debug_print(f"Página {page_num}: {valid_jobs} empleos válidos")
            return True, valid_jobs
        else:
            debug_print(f"Página {page_num}: 0 empleos")
            return False, 0
            
    except Exception as e:
        debug_print(f"Error verificando página {page_num}: {e}")
        return False, 0

def obtener_total_paginas(driver, area):
    url_base = f"https://co.computrabajo.com/trabajo-de-{area}"
    
    print(f"Analizando área: {area}")
    
    # Verificar primera página
    existe, num_jobs = verificar_pagina_existe(driver, url_base, 1)
    if not existe:
        print("No se encontraron empleos en la primera página")
        return 0
    
    print(f"Página 1: {num_jobs} empleos encontrados")
    
    # FASE 1: Búsqueda exponencial para encontrar límite superior
    ultima_valida = 1
    salto = 50
    right = salto
    
    while True:
        existe, num_jobs = verificar_pagina_existe(driver, url_base, right)
        if existe:
            ultima_valida = right
            print(f"Página {right}: {num_jobs} empleos")
            right += salto
        else:
            print(f"Página {right} 0 empleos")
            break
    
    # FASE 2: Búsqueda binaria
    left = ultima_valida
    
    while left < right - 1:
        mid = (left + right) // 2
        existe, num_jobs = verificar_pagina_existe(driver, url_base, mid)
        
        if existe:
            ultima_valida = mid
            left = mid
        else:
            right = mid
    
    # FASE 3: Verificación final secuencial
    pagina = ultima_valida
    
    while True:
        existe, num_jobs = verificar_pagina_existe(driver, url_base, pagina + 1)
        if not existe:
            break
        ultima_valida = pagina + 1
        print(f"Página {ultima_valida}:({num_jobs} empleos)")
        pagina += 1
        
        # Límite de seguridad
        if pagina > ultima_valida + 5:
            break
    
    print(f"Total de páginas encontradas: {ultima_valida}")
    return ultima_valida

# =============================================================================
# EXTRACTION - CAMPOS SEPARADOS
# =============================================================================

def extract_job_details_structured(driver):
    """
    Extrae datos del empleo y retorna diccionario con campos SEPARADOS
    """
    try:
        result = {
            'descripcion': '',
            'requerimientos': '',
            'aptitudes': ''
        }
        
        # 1. DESCRIPCIÓN PRINCIPAL
        try:
            main_desc_selectors = [
                "//div[contains(@class, 'box_detail')]//p",
                "//main//div[contains(@class, 'fs16')]//p",
                "//div[contains(@class, 'fs16')]//p"
            ]
            
            paragraphs = []
            for selector in main_desc_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        for elem in elements[:5]:
                            text = elem.text.strip()
                            if len(text) > 20:
                                paragraphs.append(text)
                        if paragraphs:
                            break
                except:
                    continue
            
            if paragraphs:
                desc = '\n\n'.join(paragraphs).strip()
                # Eliminar timestamps como "Hace 12 horas (actualizada)" o variantes
                desc = re.sub(r'\s*Hace\s+\d+\s+\w+.*$', '', desc, flags=re.IGNORECASE)
                # Normalizar líneas en blanco múltiples
                result['descripcion'] = re.sub(r'\n{3,}', '\n\n', desc).strip()
        except:
            pass
        
        if not result['descripcion']:
            try:
                all_p = driver.find_elements(By.TAG_NAME, "p")
                for p in all_p:
                    text = p.text.strip()
                    if len(text) > 100:
                        text = re.sub(r'\s*Hace\s+\d+\s+\w+.*$', '', text, flags=re.IGNORECASE)
                        result['descripcion'] = text.strip()
                        break

            except:
                result['descripcion'] = "Descripción no disponible"

        
        # 2. REQUERIMIENTOS
        try:
            req_xpath_options = [
                "//*[contains(text(),'Requerimientos')]",
                "//*[contains(text(),'Requisitos')]"
            ]
            
            requerimientos_text = ""
            for xpath in req_xpath_options:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    if elements:
                        for elem in elements:
                            text = elem.text.strip()
                            if len(text) < 50 and 'requerimientos' in text.lower():
                                content_xpaths = [
                                    "//*[contains(text(),'Requerimientos')]/following::ul[1]",
                                    "//*[contains(text(),'Requerimientos')]/following-sibling::*[1]",
                                    "//*[contains(text(),'Requerimientos')]/following::*[self::ul or self::div or self::p][1]"
                                ]
                                
                                for content_xpath in content_xpaths:
                                    try:
                                        content_elem = driver.find_element(By.XPATH, content_xpath)
                                        if content_elem:
                                            content_text = content_elem.text.strip()
                                            if len(content_text) > 10:
                                                requerimientos_text = content_text
                                                break
                                    except:
                                        continue
                                
                                if requerimientos_text:
                                    break
                        
                        if requerimientos_text:
                            break
                except:
                    continue
            
            result['requerimientos'] = requerimientos_text if requerimientos_text else "No especificado"
        
        except:
            result['requerimientos'] = "No especificado"
        
        # 3. APTITUDES
        try:
            apt_xpath_options = [
                "//*[contains(text(),'Aptitudes')]",
                "//*[contains(text(),'aptitudes')]"
            ]
            
            aptitudes_text = ""
            for xpath in apt_xpath_options:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    if elements:
                        for elem in elements:
                            text = elem.text.strip()
                            if 'aptitud' in text.lower() and len(text) < 100:
                                content_xpaths = [
                                    "//*[contains(text(),'Aptitudes')]/following::ul[1]",
                                    "//*[contains(text(),'Aptitudes')]/following-sibling::*[1]",
                                    "//*[contains(text(),'Aptitudes')]/following::div[contains(@class, 'tag')][1]/parent::*",
                                    "//*[contains(text(),'Aptitudes')]/following::*[self::ul or self::div][1]"
                                ]
                                
                                for content_xpath in content_xpaths:
                                    try:
                                        content_elem = driver.find_element(By.XPATH, content_xpath)
                                        if content_elem:
                                            content_text = content_elem.text.strip()
                                            if len(content_text) > 5:
                                                aptitudes_text = content_text
                                                break
                                    except:
                                        continue
                                
                                if aptitudes_text:
                                    break
                        
                        if aptitudes_text:
                            break
                except:
                    continue
            
            result['aptitudes'] = aptitudes_text if aptitudes_text else "No especificado"
        
        except:
            result['aptitudes'] = "No especificado"
        
        result['descripcion'] = re.sub(r'\n{2,}', '\n\n', result['descripcion']).strip()
        result['requerimientos'] = result['requerimientos']
        result['aptitudes'] = result['aptitudes']
        
        return result
        
    except Exception as e:
        debug_print(f"Error en extract_job_details_structured: {e}")
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body_text = body.text[:3000]
            return {
                'descripcion': body_text,
                'requerimientos': 'No especificado',
                'aptitudes': 'No especificado'
            }
        except:
            return {
                'descripcion': 'Descripción no disponible',
                'requerimientos': 'No especificado',
                'aptitudes': 'No especificado'
            }

# =============================================================================
# CATEGORÍAS
# =============================================================================

AREAS = {
    "servicio-al-cliente": "Servicio al Cliente",
    "auxiliar-de-bodega": "Auxiliar de Bodega",
    "auxiliar-de-cocina": "Auxiliar de Cocina",
    "auxiliar-administrativo": "Auxiliar Administrativo",
    "auxiliar-logistico": "Auxiliar Logístico",
    "asesor-comercial": "Asesor Comercial",
    "call-center": "Call Center",
    "auxiliar-de-enfermeria": "Auxiliar de Enfermería",
    "asesor-de-ventas": "Asesor de Ventas",
    "analista": "Analista",
    "conductor": "Conductor",
    "atencion-a-clientes": "Atención a Clientes",
    "auxiliar-contable": "Auxiliar Contable",
    "operario": "Operario",
    "mercaderista": "Mercaderista",
    "auxiliar": "Auxiliar",
    "ejecutivo-comercial": "Ejecutivo Comercial",
    "coordinador": "Coordinador",
    "asesores-comerciales": "Asesores Comerciales",
}



# =============================================================================
# MAIN SCRAPING FUNCTION
# =============================================================================

def scrape_area(driver, area, area_idx, total_areas):
    """Scrape una área completa"""
    global total_jobs_scraped, jobs_this_session, EMPLEOS, HASHES_GLOBALES, current_area
    
    current_area = area
    
    print(f"\n{'='*80}")
    print(f"ÁREA {area_idx}/{total_areas}: {AREAS[area]}")
    print(f"{'='*80}")
    
    # BINARY SEARCH: Obtener número exacto de páginas
    total_paginas = obtener_total_paginas(driver, area)
    
    if total_paginas == 0:
        print(f"No se encontraron empleos para {AREAS[area]}")
        return 0
    
    print(f"Encontradas {total_paginas} páginas para {AREAS[area]}")
    print("Comenzando extracción de empleos...")
    
    area_jobs = 0
    
    # Iterar por todas las páginas encontradas
    for pag in range(1, total_paginas + 1):
        url = f"https://co.computrabajo.com/trabajo-de-{area}?p={pag}"
        
        print(f"\nProcesando página {pag}/{total_paginas}")
        
        try:
            try:
                driver.get(url)
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.js-o-link")))
            except:
                driver.execute_script("window.stop();")
            
            links = driver.find_elements(By.CSS_SELECTOR, "a.js-o-link")
            urls = list(set([l.get_attribute("href") for l in links if '/ofertas-de-trabajo/' in (l.get_attribute("href") or "")]))
            
            if len(urls) == 0:
                print(f"Página {pag}: 0 empleos (saltando)")
                continue
            
            print(f"Página {pag}: {len(urls)} empleos")
            
            for i, url_emp in enumerate(urls):
                try:
                    try:
                        driver.get(url_emp)
                        WebDriverWait(driver, 3).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "a.js-o-link")))
                        driver.delete_all_cookies()
                    except:
                        driver.execute_script("window.stop();")
                    
                    # Título
                    try:
                        titulo = driver.find_element(By.TAG_NAME, "h1").text.strip()
                        print(f"  {i+1}/{len(urls)} - {titulo[:50]}")
                    except:
                        titulo = "Sin título"
                        print(f"  {i+1}/{len(urls)} - [Sin título]")
                    
                    # Extraer datos estructurados
                    details = extract_job_details_structured(driver)
                    
                    # Empresa/Ubicación
                    empresa = "N/A"
                    ubicacion = "Colombia"
                    try:
                        p = driver.find_element(By.CSS_SELECTOR, "p.fs16")
                        txt = p.text.strip()
                        if '-' in txt:
                            partes = txt.split('-')
                            empresa = partes[0].strip()
                            ubicacion = partes[1].strip()
                    except:
                        pass
                    
                    # Hash
                    hash_content = details['descripcion'] + "|" + ubicacion + "|" + empresa
                    hash_empleo = calcular_hash(hash_content)
                    
                    if hash_empleo in HASHES_GLOBALES:
                        print(f"    ^ [DUPLICADO]")
                        continue
                    
                    # AGREGAR CON CAMPOS SEPARADOS
                    EMPLEOS.append({
                        "Id Interno": f"CO-{area}-{pag}-{i+1}",
                        "titulo": titulo,
                        "descripcion": details['descripcion'],
                        "requerimientos": details['requerimientos'],
                        "aptitudes": details['aptitudes'],
                        "Empresa": empresa if empresa != "N/A" else "Confidencial",
                        "Fuente": "Computrabajo Colombia",
                        "Tipo Portal": "Tradicional",
                        "url": url_emp,
                        "Pais": "Colombia",
                        "ubicacion": ubicacion,
                        "Categoria Portal": area,
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
                    area_jobs += 1
                    
                except Exception as e:
                    debug_print(f"Error en empleo {i+1}: {e}")
                    continue
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error en página {pag}: {e}")
            driver = recrear_driver_si_necesario(driver)
            continue
    
    # Guardar al finalizar área
    print(f"\n{'='*60}")
    print(f"Área '{AREAS[area]}' completada - Guardando datos...")
    print(f"Jobs en esta área: {area_jobs}")
    print(f"Total acumulado: {total_jobs_scraped}")
    print(f"{'='*60}")
    
    if EMPLEOS:
        guardar_datos_incremental(EMPLEOS, area)
        EMPLEOS = []
    
    return area_jobs

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("Iniciando Computrabajo Colombia Scraper")
    
    if args.debug:
        print("Modo debug activado")
    
    # Cargar hashes existentes
    print("Cargando hashes existentes...")
    for area in AREAS.keys():
        timestamp = date.today().strftime("%Y%m%d")
        archivo = f"output_jobs/Computrabajo_CO_{area}_{timestamp}.json"
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
    
    # Determinar desde dónde comenzar
    start_index = 0
    if args.start_from:
        areas_list = list(AREAS.keys())
        for i, area in enumerate(areas_list):
            if args.start_from.lower() in area.lower():
                start_index = i
                print(f"Iniciando desde: {AREAS[area]}")
                break
    
    print(f"Procesando {len(AREAS) - start_index} áreas...")
    
    driver = create_driver()
    
    try:
        areas_list = list(AREAS.keys())
        for idx, area in enumerate(areas_list[start_index:], start_index + 1):
            try:
                scrape_area(driver, area, idx, len(AREAS))
            except Exception as e:
                print(f"Error crítico en área {area}: {e}")
                driver = recrear_driver_si_necesario(driver)
                continue
            
            time.sleep(2)
    
    finally:
        try:
            driver.quit()
        except:
            pass
    
    print(f"\nSCRAPING COMPLETADO!")
    print(f"Resumen:")
    print(f"   - Jobs esta sesión: {jobs_this_session}")
    print(f"   - Total jobs: {total_jobs_scraped}")
    print(f"   - Áreas procesadas: {len(AREAS)}")
    print(f"   - Archivos en: output_jobs/")