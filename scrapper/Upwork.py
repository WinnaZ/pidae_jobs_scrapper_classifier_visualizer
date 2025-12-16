from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import date
import json
import time
import random
import argparse

# Variable global para modo debug
DEBUG_MODE = False

def debug_print(message):
    """Imprime mensaje solo si el modo debug está activado"""
    if DEBUG_MODE:
        print(message)

def handle_cloudflare_checkbox(driver, timeout=10):
    """
    Intenta hacer clic en el checkbox de verificación de Cloudflare
    Retorna True si tuvo éxito, False en caso contrario
    """
    try:
        debug_print("Buscando checkbox de Cloudflare...")
        
        # Esperar un poco para que cargue el challenge
        time.sleep(2)
        
        # Buscar todos los iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        debug_print(f"Encontrados {len(iframes)} iframes")
        
        for idx, iframe in enumerate(iframes):
            try:
                # Cambiar al iframe
                driver.switch_to.frame(iframe)
                debug_print(f"Revisando iframe {idx + 1}/{len(iframes)}")
                
                # Intentar diferentes selectores para el checkbox
                checkbox_selectors = [
                    "input[type='checkbox']",
                    ".cb-lb",
                    "#challenge-stage input",
                    "span.mark",
                    ".ctp-checkbox-label"
                ]
                
                for selector in checkbox_selectors:
                    try:
                        checkbox = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        debug_print(f"Checkbox encontrado con: {selector}")
                        
                        # Hacer clic
                        checkbox.click()
                        print("Checkbox de Cloudflare clickeado!")
                        time.sleep(3)
                        
                        # Volver al contenido principal
                        driver.switch_to.default_content()
                        return True
                        
                    except:
                        continue
                
                # Si no encontramos nada en este iframe, volver al contenido principal
                driver.switch_to.default_content()
                
            except Exception as e:
                debug_print(f"Error procesando iframe {idx + 1}: {e}")
                driver.switch_to.default_content()
                continue
        
        debug_print("No se encontró checkbox de Cloudflare")
        return False
        
    except Exception as e:
        debug_print(f"Error en handle_cloudflare_checkbox: {e}")
        try:
            driver.switch_to.default_content()
        except:
            pass
        return False

def verificar_pagina_existe(driver, url, page_num):
    """
    Verifica si una página contiene trabajos válidos
    Retorna: (existe, numero_de_trabajos)
    """
    intentos = 3
    for intento in range(intentos):
        try:
            driver.get(url)
            time.sleep(random.uniform(3, 6))
            
            # Esperar a que cargue la página
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Verificar si Cloudflare está bloqueando - MEJORADO
            cloudflare_detectado = False
            try:
                # Buscar indicadores de Cloudflare
                page_text = driver.page_source.lower()
                cloudflare_indicators = [
                    "verify you are human",
                    "checking your browser",
                    "just a moment",
                    "cloudflare"
                ]
                
                for indicator in cloudflare_indicators:
                    if indicator in page_text:
                        cloudflare_detectado = True
                        break
                
                if cloudflare_detectado:
                    print(f"\nCloudflare detectado en página {page_num}!")
                    print("Intentando resolver automáticamente...")
                    
                    # Intentar clickear el checkbox hasta 3 veces
                    for cf_intento in range(3):
                        if handle_cloudflare_checkbox(driver):
                            print(f"Intento {cf_intento + 1}: Checkbox clickeado. Esperando verificación...")
                            time.sleep(8)
                            
                            # Verificar si pasamos
                            page_text_nuevo = driver.page_source.lower()
                            if not any(ind in page_text_nuevo for ind in cloudflare_indicators):
                                print("Cloudflare superado exitosamente!")
                                break
                        else:
                            print(f"Intento {cf_intento + 1}: No se encontró checkbox")
                            time.sleep(5)
                            
                            if cf_intento < 2:
                                print("Refrescando página...")
                                driver.refresh()
                                time.sleep(5)
                    
                    # Si después de 3 intentos seguimos bloqueados, pedir intervención manual
                    page_text_final = driver.page_source.lower()
                    if any(ind in page_text_final for ind in cloudflare_indicators):
                        print("\nNo se pudo resolver automáticamente.")
                        print("Por favor, resuelve la verificación manualmente en el navegador.")
                        print("Presiona Enter cuando hayas completado la verificación...")
                        input()
                        
            except Exception as e:
                debug_print(f"Error verificando Cloudflare: {e}")
            
            # Verificar si hay mensaje de "no hay resultados"
            try:
                no_results = driver.find_elements(By.XPATH, "//*[contains(text(), 'No results found') or contains(text(), 'No jobs found')]")
                if no_results and any(elem.is_displayed() for elem in no_results):
                    print(f"Página {page_num}: 0 trabajos válidos encontrados")
                    return False, 0
            except:
                pass
            
            # Selector para trabajos de Upwork
            jobs = driver.find_elements(By.CSS_SELECTOR, "article.job-tile, section[data-test='JobTile']")
            debug_print(f"    Selector encontró: {len(jobs)} trabajos")
            
            trabajos_validos = []
            
            for job in jobs:
                try:
                    # Verificar que tenga un título
                    title = job.find_element(By.CSS_SELECTOR, "h2, h3, .job-tile-title")
                    if title and title.text.strip():
                        trabajos_validos.append(job)
                        debug_print(f"    [OK] Trabajo válido: {title.text.strip()[:50]}")
                except Exception as e:
                    debug_print(f"    [X] Error al validar trabajo: {str(e)}")
                    continue
            
            num_trabajos = len(trabajos_validos)
            
            if num_trabajos > 0:
                print(f"Página {page_num}: {num_trabajos} trabajos válidos encontrados")
                return True, num_trabajos
            else:
                print(f"Página {page_num}: 0 trabajos válidos encontrados")
                return False, 0
                
        except Exception as e:
            if intento < intentos - 1:
                debug_print(f"    Intento {intento + 1} falló, reintentando...")
                time.sleep(2)
            else:
                print(f"Error al verificar página {page_num}: {str(e)}")
                return False, 0
    
    return False, 0

def obtener_total_paginas(driver, categoria):
    """
    Usa búsqueda binaria para encontrar el número total de páginas disponibles
    """
    try:
        url_base = f"https://www.upwork.com/nx/search/jobs/?q={categoria}"
        
        debug_print(f"\n=== Búsqueda del total de páginas para: {categoria} ===")
        
        # Fase inicial: verificar páginas clave
        debug_print("Fase 1: Verificando páginas clave (1, 50, 100)...")
        
        ultima_valida = 1
        
        # Verificar página 1
        url = f"{url_base}&page=1"
        if not verificar_pagina_existe(driver, url, 1)[0]:
            print("No se encontraron trabajos en la primera página")
            return 1
        
        # Verificar saltos de 50 páginas
        for pagina in [50, 100, 150]:
            url = f"{url_base}&page={pagina}"
            debug_print(f"\nProbando página {pagina}...")
            if verificar_pagina_existe(driver, url, pagina)[0]:
                ultima_valida = pagina
            else:
                break
        
        # Ajustar el rango de búsqueda
        if ultima_valida == 1:
            rango_busqueda = 50
        elif ultima_valida == 50:
            rango_busqueda = 100
        elif ultima_valida == 100:
            rango_busqueda = 150
        else:
            rango_busqueda = ultima_valida + 50

        # Búsqueda binaria refinada
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
            url = f"{url_base}&page={mid}"
            debug_print(f"\nProbando página {mid}...")
            
            if verificar_pagina_existe(driver, url, mid)[0]:
                ultima_pagina_valida = mid
                left = mid + 1
            else:
                right = mid - 1
        
        # Búsqueda secuencial desde la última página válida
        debug_print("\nFase 3: Búsqueda secuencial final...")
        pagina = ultima_pagina_valida
        while True:
            url = f"{url_base}&page={pagina + 1}"
            if not verificar_pagina_existe(driver, url, pagina + 1)[0]:
                debug_print(f"Encontrada última página válida: {pagina}")
                return pagina
            pagina += 1
            ultima_pagina_valida = pagina
        
        return ultima_pagina_valida

    except Exception as e:
        print(f"\nError al obtener total de páginas: {str(e)}")
        return 1

def main():
    global DEBUG_MODE
    
    # Configurar argumentos
    parser = argparse.ArgumentParser(description='Scraper de trabajos de Upwork')
    parser.add_argument('--debug', action='store_true', help='Activa el modo debug con mensajes detallados')
    args = parser.parse_args()
    
    DEBUG_MODE = args.debug
    
    print("Iniciando scraping de Upwork...")
    if DEBUG_MODE:
        print("Modo debug activado - Se mostrarán mensajes detallados")
    
    # Categorías a buscar (puedes agregar más)
    categorias = [
        "web development",
        "mobile development",
        "data science",
        "graphic design",
        "content writing",
        "virtual assistant",
        "video editing",
        "social media marketing"
    ]
    
    print(f"Categorías a procesar: {', '.join(categorias)}\n")
    
    # Configurar Chrome para Upwork con evasión de Cloudflare
    options = webdriver.ChromeOptions()
    
    # Evasión básica de detección
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    
    # User agent realista
    options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
    
    # Preferencias adicionales
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Desactivar notificaciones y permisos
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False
    }
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Modificar propiedades de navegador para evitar detección
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    })
    
    # Eliminar propiedades que indican automatización
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    driver.maximize_window()
    
    print("\nNOTA: Upwork usa Cloudflare para protección anti-bot")
    print("La verificación aparecerá al acceder a las páginas de búsqueda.")
    print("El script intentará resolverla automáticamente...\n")
    
    # Primera carga simple - NO intentar resolver Cloudflare aquí
    try:
        print("Cargando Upwork...")
        driver.get("https://www.upwork.com")
        time.sleep(3)
        print("Página inicial cargada.\n")
        
    except Exception as e:
        print(f"Error en carga inicial: {e}")
    
    # Lista para guardar todos los trabajos
    TRABAJOS = []
    
    pagina_inicio = 1
    
    try:
        for categoria in categorias:
            print(f"\n{'='*60}")
            print(f"Iniciando búsqueda en categoría: {categoria}")
            print(f"{'='*60}")
            
            # Obtener el número total de páginas para esta categoría
            total_paginas = obtener_total_paginas(driver, categoria)
            print(f"Encontradas {total_paginas} páginas para {categoria}")
            print("Comenzando extracción de trabajos...\n")
            
            for pagina in range(pagina_inicio, total_paginas + 1):
                url = f"https://www.upwork.com/nx/search/jobs/?q={categoria}&page={pagina}"
                debug_print(f"\nAccediendo a URL: {url}")
                
                driver.get(url)
                # Delay más largo para evitar detección
                time.sleep(random.uniform(4, 7))
                
                # Verificar Cloudflare en el bucle principal también
                try:
                    page_text = driver.page_source.lower()
                    if "verify you are human" in page_text or "checking your browser" in page_text:
                        print(f"\nCloudflare detectado en página {pagina}!")
                        print("Intentando resolver...")
                        
                        for cf_intento in range(2):
                            if handle_cloudflare_checkbox(driver):
                                print("Checkbox clickeado. Esperando...")
                                time.sleep(8)
                                break
                            else:
                                if cf_intento == 0:
                                    print("Reintentando...")
                                    time.sleep(5)
                        
                        # Verificar si pasamos
                        if "verify you are human" in driver.page_source.lower():
                            print("Por favor, completa la verificación manualmente.")
                            print("Presiona Enter cuando termines...")
                            input()
                except:
                    pass

                # Esperar que carguen los trabajos
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.job-tile, section[data-test='JobTile']"))
                    )
                except:
                    print(f"No se encontraron trabajos en página {pagina}")
                    continue

                jobs = driver.find_elements(By.CSS_SELECTOR, "article.job-tile, section[data-test='JobTile']")
                
                if not args.debug:
                    print(f"\nPágina {pagina}/{total_paginas} - {len(jobs)} trabajos encontrados:")

                for i, job in enumerate(jobs):
                    debug_print(f"\nProcesando trabajo {i+1}")
                    
                    try:
                        # Título
                        try:
                            titulo_elem = job.find_element(By.CSS_SELECTOR, "h2 a, h3 a, .job-tile-title a")
                            titulo = titulo_elem.text.strip()
                            url_trabajo = titulo_elem.get_attribute("href")
                            if not args.debug:
                                print(f"  {i+1} - {titulo}")
                        except:
                            titulo = "Título no disponible"
                            url_trabajo = ""
                            if not args.debug:
                                print(f"  {i+1} - [Título no disponible]")
                        
                        # Descripción
                        try:
                            descripcion = job.find_element(By.CSS_SELECTOR, ".job-tile-description, [data-test='job-description']").text.strip()
                        except:
                            descripcion = "Descripción no disponible"
                        
                        # Presupuesto/Pago
                        try:
                            presupuesto = job.find_element(By.CSS_SELECTOR, ".job-tile-budget, [data-test='budget']").text.strip()
                        except:
                            presupuesto = "No especificado"
                        
                        # Nivel de experiencia
                        try:
                            nivel = job.find_element(By.CSS_SELECTOR, ".job-tile-experience, [data-test='experience-level']").text.strip()
                        except:
                            nivel = "No especificado"
                        
                        # Skills/Habilidades
                        try:
                            skills_elements = job.find_elements(By.CSS_SELECTOR, ".job-tile-skills span, [data-test='skill']")
                            skills = ", ".join([skill.text.strip() for skill in skills_elements if skill.text.strip()])
                        except:
                            skills = "No especificadas"
                        
                        # Tipo de trabajo (Fixed/Hourly)
                        try:
                            tipo_trabajo = job.find_element(By.CSS_SELECTOR, ".job-tile-type, [data-test='job-type']").text.strip()
                        except:
                            tipo_trabajo = "No especificado"
                        
                        today = date.today().strftime("%d/%m/%Y")

                        TRABAJOS.append({
                            "Id Interno": f"{categoria.replace(' ', '-')}-{pagina}-{i+1}",
                            "titulo": titulo,
                            "descripcion": descripcion,
                            "categoria": categoria,
                            "presupuesto": presupuesto,
                            "nivel_experiencia": nivel,
                            "tipo_trabajo": tipo_trabajo,
                            "skills": skills,
                            "fecha_extraccion": today,
                            "url": url_trabajo if url_trabajo.startswith('http') else f"https://www.upwork.com{url_trabajo}"
                        })
                        
                    except Exception as e:
                        debug_print(f"Error al procesar trabajo {i+1}: {str(e)}")
                        continue
                
                debug_print(f"Página {pagina} completada\n")
                # Delay más largo entre páginas para evitar bloqueo
                time.sleep(random.uniform(3, 6))
            
            print(f"\nCategoría '{categoria}' completada: {len([t for t in TRABAJOS if t['categoria'] == categoria])} trabajos extraídos")
        
        # Guardar todos los trabajos en un archivo JSON
        nombre_archivo = f"output_jobs/Upwork_multiple_categorias_{pagina_inicio}a{total_paginas}.json"
        with open(nombre_archivo, 'w', encoding='utf-8') as file:
            json.dump(TRABAJOS, file, ensure_ascii=False, indent=4)
        
        print(f"\n{'='*60}")
        print(f"Scraping completado exitosamente")
        print(f"Total de trabajos extraídos: {len(TRABAJOS)}")
        print(f"Archivo guardado: {nombre_archivo}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\nError durante el scraping: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
