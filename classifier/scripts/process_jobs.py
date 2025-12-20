#!/usr/bin/env python3
"""
Procesador de Empleos V3 - Solo Ollama
=====================================

Sistema simplificado que utiliza únicamente Ollama para clasificación adicional con regex.


Funcionalidades:
- Clasificación automática con patrones regex (base + aprendidos)
- Clasificación adicional con Ollama para términos no encontrados
- Aprendizaje automático de nuevos patrones
- Soporte para esquema Escudero (habilidades blandas + duras)
- Exportación a CSV consolidado
"""

import sys
import json
import logging
import argparse
import pandas as pd
import time
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# Colores para terminal
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

# Importar el PatternManager solo cuando sea necesario (lazy loading)
# from pattern_manager import PatternManager  # Movido a load_dictionaries()

# Intentar importar clasificador Ollama
try:
    import ollama_classifier
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print(f"{Colors.GRAY}ollama_classifier no disponible - Use --ollama requiere instalación{Colors.RESET}")

def validate_ai_requirement(requirement_text):
    """
    Valida que un requisito extraído por AI sea apropiado para crear un patrón regex.
    Rechaza términos muy largos, genéricos, o que parecen descripciones de trabajo.
    """
    if not requirement_text or len(requirement_text.strip()) == 0:
        return False
    
    text = requirement_text.strip().lower()
    
    # Rechazar si es muy largo (más de 4 palabras)
    words = text.split()
    if len(words) > 4:
        return False
    
    # Rechazar si contiene frases genéricas o descripciones de trabajo
    rejected_patterns = [
        'experiencia', 'conocimientos', 'habilidades', 'capacidad', 'manejo',
        'gestión', 'realizar', 'desarrollar', 'implementar', 'trabajar',
        'años', 'mínimo', 'deseable', 'preferible', 'responsabilidades',
        'funciones', 'tareas', 'actividades', 'nivel', 'grado', 'dominio'
    ]
    
    for pattern in rejected_patterns:
        if pattern in text:
            return False
    
    # Rechazar si es solo números o muy corto
    if len(text) < 2 or text.isdigit():
        return False
        
    return True

# Variables globales que se configurarán con argumentos
USE_OLLAMA = False  # Será modificado por --ollama
FILTER_SKILLS = None  # Será configurado por --habilidades
PATTERN_MANAGER = None  # Se cargará en main()

# Los mensajes de inicio se moverán a main()

# --- Configuración del Logger ---
Path('output_logs').mkdir(exist_ok=True)
logging.basicConfig(
    filename='output_logs/process_jobs.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --- Variables Globales ---
# Estadísticas globales
classification_stats = {
    'total_jobs': 0,
    'total_requirements': 0,
    'regex_classified': 0,
    'ollama_classified': 0,
    'regex_percentage': 0.0,
    'ollama_percentage': 0.0
}

def parse_arguments():
    """Configura y parsea argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description='Procesador de empleos con clasificación híbrida (Regex + Ollama AI)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python process_jobs.py                                        # Procesa all_jobs.json con regex
  python process_jobs.py --ollama                               # all_jobs.json con Regex + Ollama  
  python process_jobs.py --habilidades soft                     # Solo habilidades blandas
  python process_jobs.py --habilidades duro                     # Solo habilidades técnicas
  python process_jobs.py --ollama --habilidades soft            # Ollama + soft skills
  python process_jobs.py --directorio /other/path               # Usar otro directorio
        """
    )
    
    parser.add_argument(
        '--ollama',
        action='store_true', 
        help='Usa Ollama para clasificación adicional con regex'
    )
    
    parser.add_argument(
        '--habilidades',
        choices=['soft', 'duro', 'idioma', 'all'],
        default='all',
        help='Filtra por tipo de habilidad: soft (blandas), duro (técnicas), idioma, all (todas)'
    )
    
    parser.add_argument(
        '--directorio',
        type=str,
        default="../../../Base de Datos Tablas",
        help='Directorio donde está all_jobs.json (por defecto: ../../../Base de Datos Tablas)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Nombre del archivo CSV consolidado de salida (ej: resultados_clasificacion_ollama.csv)'
    )
    
    return parser.parse_args()

def load_dictionaries():
    """
    Carga y inicializa el sistema de patrones
    """
    print(f"{Colors.CYAN}Cargando patrones regex...{Colors.RESET}")
    global PATTERN_MANAGER
    try:
        # Importar PatternManager solo aquí para evitar carga automática
        from .pattern_manager import PatternManager
        PATTERN_MANAGER = PatternManager()
        return True
    except Exception as e:
        print(f"{Colors.RED}Error cargando patrones: {e}{Colors.RESET}")
        return False

def classify_with_regex(description_text):
    """
    Clasifica un texto usando solo patrones regex
    """
    if not description_text:
        return {
            'habilidades_blandas': {},
            'habilidades_duras': {},
            'titulos': [],
            'idiomas': [],
            'total_found': 0
        }
    
    # Usar el PatternManager para clasificar
    result = PATTERN_MANAGER.classify_text(description_text)
    
    # Filtrar por tipo de habilidad si está configurado
    if FILTER_SKILLS and FILTER_SKILLS != 'all':
        if FILTER_SKILLS == 'soft':
            result['habilidades_duras'] = {}
            result['idiomas'] = []
        elif FILTER_SKILLS == 'duro':
            result['habilidades_blandas'] = {}
            result['idiomas'] = []
        elif FILTER_SKILLS == 'idioma':
            result['habilidades_blandas'] = {}
            result['habilidades_duras'] = {}
    
    # Calcular total encontrado
    total = 0
    for area, matches in result.items():
        if isinstance(matches, dict):
            total += sum(len(terms) for terms in matches.values())
        elif isinstance(matches, list):
            total += len(matches)
    
    result['total_found'] = total
    return result

def process_and_insert_jobs(json_filepath):
    """Procesa el archivo JSON de empleos con clasificación híbrida (regex + Ollama)."""
    global classification_stats
    
    # Crear directorio de resultados
    Path('database').mkdir(exist_ok=True)
    
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            empleos = json.load(f)
    except Exception as e:
        print(f"{Colors.RED}Error leyendo {json_filepath}: {e}{Colors.RESET}")
        return
    
    if not empleos:
        print(f"{Colors.YELLOW}Archivo {json_filepath} está vacío{Colors.RESET}")
        return
    
    # Configurar nombre de archivo de salida - usar nombre hardcodeado para all_jobs
    csv_output = "database/all_jobs_clasificado.csv"
    
    print(f"  Cargados: {len(empleos):,} empleos del archivo")
    print(f"  CSV de salida: all_jobs_clasificado.csv")
    
    # Configurar Ollama si está habilitado
    if USE_OLLAMA and OLLAMA_AVAILABLE:
        print(f"  Método: Regex + Ollama")
        try:
            classifier = ollama_classifier.OllamaClassifier()
        except MemoryError as e:
            print(f"{Colors.RED}")
            print(f"{'='*80}")
            print(f"ERROR: {str(e)}")
            print(f"{'='*80}")
            print(f"Ejecuta sin Ollama: python process_jobs.py")
            print(f"O cambia el modelo en ollama_classifier.py linea 27")
            print(f"{'='*80}")
            print(f"{Colors.RESET}")
            sys.exit(1)
    else:
        print(f"  Método: Solo Regex")
        classifier = None
    
    print(f"  Iniciando clasificación de {len(empleos)} empleos...")
    
    # Listas para almacenar resultados
    resultados = []
    total_requirements_found = 0
    regex_count = 0
    ollama_count = 0
    
    for i, empleo in enumerate(empleos, 1):
        # Mostrar progreso
        if i % 500 == 0 or i <= 10:
            percentage = (i / len(empleos)) * 100
            print(f"  [{i}/{len(empleos)}] {percentage:.1f}% - ID:{empleo.get('Id Interno', 'N/A')} {empleo.get('titulo', 'Sin título')[:50]}...")
        
        # Obtener texto completo
        descripcion = empleo.get('descripcion', '')
        titulo = empleo.get('titulo', '')
        texto_completo = f"{titulo} {descripcion}"
        
        # Clasificar con regex
        literal_results = classify_with_regex(texto_completo)
        regex_found = literal_results['total_found']
        regex_count += regex_found
        
        # Clasificar con Ollama si está habilitado y hay texto restante
        ollama_results = {}
        ollama_found = 0
        ollama_learned = 0
        
        if USE_OLLAMA and OLLAMA_AVAILABLE and classifier and texto_completo.strip():
            try:
                ollama_response = ollama_classifier.classify_with_ollama_simple(
                    texto_completo, 
                    literal_results,
                    classifier=classifier
                )
                
                if ollama_response:
                    for req_type, req_list in ollama_response.items():
                        for req_text in req_list:
                            if not validate_ai_requirement(req_text):
                                continue
                                
                            # Mapear tipos
                            if req_type == "duros":
                                area = "duro"
                            elif req_type == "blandos":
                                area = "blando"
                            elif req_type == "idioma":
                                area = "idioma"
                            elif req_type == "titulos":
                                area = "titulo"
                            else:
                                continue
                                    
                            try:
                                success = PATTERN_MANAGER.learn_from_ai_classification(
                                    req_text, area, None
                                )
                                if success:
                                    ollama_learned += 1
                                    ollama_found += 1
                            except:
                                pass
                                
                ollama_count += ollama_learned
                
            except Exception as e:
                print(f"{Colors.RED}    Error con Ollama: {str(e)[:100]}{Colors.RESET}")
        
        # Mostrar progreso detallado
        total_found = regex_found + ollama_found
        total_requirements_found += total_found
        
        if i % 500 == 0:
            if USE_OLLAMA and OLLAMA_AVAILABLE:
                print(f"    → {total_found} reqs (Regex: {regex_found}, Ollama: {ollama_found}) | Total: {total_requirements_found}")
            else:
                print(f"    → {regex_found} reqs | Total: {total_requirements_found}")
        
        # Crear registro para CSV
        registro = {
            'Id_Interno': empleo.get('Id Interno', ''),
            'Titulo': empleo.get('titulo', ''),
            'Empresa': empleo.get('Empresa', ''),
            'Fuente': empleo.get('Fuente', ''),
            'Tipo_Portal': empleo.get('Tipo Portal', ''),
            'URL': empleo.get('url', ''),
            'Pais': empleo.get('Pais', ''),
            'Ubicacion': empleo.get('Ubicacion', ''),
            'Categoria_Portal': empleo.get('Categoria Portal', ''),
            'Subcategoria_Portal': empleo.get('Subcategoria Portal', ''),
            'Hash_Descripcion': empleo.get('hash Descripcion', ''),
            'Fecha': empleo.get('fecha', ''),
            'Total_Requisitos': total_found,
            'Regex_Encontrados': regex_found,
            'Ollama_Encontrados': ollama_found
        }
        
        # Agregar habilidades encontradas al registro
        for area, matches in literal_results.items():
            if area in ['habilidades_blandas', 'habilidades_duras']:
                for categoria, terminos in matches.items():
                    for termino in terminos:
                        resultado_individual = registro.copy()
                        resultado_individual.update({
                            'Area': area,
                            'Categoria': categoria,
                            'Termino_Encontrado': termino,
                            'Fuente_Clasificacion': 'Regex'
                        })
                        resultados.append(resultado_individual)
            elif area in ['titulos', 'idiomas']:
                for termino in matches:
                    resultado_individual = registro.copy()
                    resultado_individual.update({
                        'Area': area,
                        'Categoria': area,
                        'Termino_Encontrado': termino,
                        'Fuente_Clasificacion': 'Regex'
                    })
                    resultados.append(resultado_individual)
    
    # Actualizar estadísticas globales
    classification_stats['total_jobs'] += len(empleos)
    classification_stats['total_requirements'] += total_requirements_found
    classification_stats['regex_classified'] += regex_count
    classification_stats['ollama_classified'] += ollama_count
    
    # Calcular porcentajes
    if total_requirements_found > 0:
        classification_stats['regex_percentage'] = (regex_count / total_requirements_found) * 100
        classification_stats['ollama_percentage'] = (ollama_count / total_requirements_found) * 100
    
    print(f"\n  Archivo procesado exitosamente:")
    print(f"     Empleos procesados: {len(empleos):,}")
    print(f"     Requisitos totales: {total_requirements_found}")
    if USE_OLLAMA and OLLAMA_AVAILABLE:
        print(f"     Clasificados con Regex: {regex_count} ({classification_stats['regex_percentage']:.1f}%)")
        print(f"     Clasificados con Ollama: {ollama_count} ({classification_stats['ollama_percentage']:.1f}%)")
    else:
        print(f"     Clasificados con Regex: {regex_count} (100%)")
    
    # Guardar resultados en CSV
    if resultados:
        df = pd.DataFrame(resultados)
        df.to_csv(csv_output, index=False, encoding='utf-8')
        print(f"  CSV guardado: {csv_output}")
    else:
        # Crear archivo vacío si no hay resultados
        pd.DataFrame().to_csv(csv_output, index=False, encoding='utf-8')
        print(f"  CSV vacío guardado: {csv_output}")

def print_final_statistics():
    """Imprime estadísticas finales del procesamiento"""
    print(f"\n{Colors.BOLD}PROCESO COMPLETADO{Colors.RESET}")
    print(f"Empleos procesados: {classification_stats['total_jobs']:,}")
    print(f"Requisitos extraídos: {classification_stats['total_requirements']:,}")
    
    if USE_OLLAMA and OLLAMA_AVAILABLE:
        print(f"Clasificados con Regex: {classification_stats['regex_classified']:,} ({classification_stats['regex_percentage']:.1f}%)")
        print(f"Clasificados con Ollama: {classification_stats['ollama_classified']:,} ({classification_stats['ollama_percentage']:.1f}%)")
        
        # Obtener estadísticas de patrones aprendidos
        try:
            info = PATTERN_MANAGER.get_system_info()
            learned_stats = info['pattern_statistics']['learned']
            print(f"Términos aprendidos: {learned_stats.get('total_patterns', 0)}")
        except:
            print("Términos aprendidos: No disponible")
    else:
        print(f"Clasificados con Regex: {classification_stats['regex_classified']:,} (100%)")
    
    # Guardar estadísticas
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stats_file = f"output_logs/estadisticas_finales_{timestamp}.log"
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("ESTADÍSTICAS FINALES DE PROCESAMIENTO\n")
        f.write("=" * 50 + "\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Empleos procesados: {classification_stats['total_jobs']:,}\n")
        f.write(f"Requisitos extraídos: {classification_stats['total_requirements']:,}\n")
        f.write(f"Clasificados con Regex: {classification_stats['regex_classified']:,} ({classification_stats['regex_percentage']:.1f}%)\n")
        if USE_OLLAMA and OLLAMA_AVAILABLE:
            f.write(f"Clasificados con Ollama: {classification_stats['ollama_classified']:,} ({classification_stats['ollama_percentage']:.1f}%)\n")
    
    print(f"Estadísticas guardadas en: {stats_file}")
    
    # Guardar estadísticas en JSON para análisis
    json_stats = {
        'timestamp': datetime.now().isoformat(),
        'total_jobs': classification_stats['total_jobs'],
        'total_requirements': classification_stats['total_requirements'],
        'regex_classified': classification_stats['regex_classified'],
        'ollama_classified': classification_stats['ollama_classified'],
        'regex_percentage': classification_stats['regex_percentage'],
        'ollama_percentage': classification_stats['ollama_percentage'],
        'ollama_enabled': USE_OLLAMA and OLLAMA_AVAILABLE
    }
    
    with open('output_logs/classification_statistics.json', 'w', encoding='utf-8') as f:
        json.dump(json_stats, f, indent=2, ensure_ascii=False)
    
    print("Estadísticas guardadas en: output_logs/classification_statistics.json")

def consolidate_and_export_csv(custom_output=None):
    """Consolida todos los CSVs en uno solo y los copia a Base de Datos Tablas"""
    print(f"\n{Colors.CYAN}Consolidando resultados en CSV único...{Colors.RESET}")
    
    try:
        # Buscar archivo CSV específico (ya que solo procesamos all_jobs)
        csv_file = "database/all_jobs_clasificado.csv"
        
        # Verificar si existe el archivo CSV
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            total_records = len(df)
            print(f"  Encontrado: all_jobs_clasificado.csv")
            print(f"    - all_jobs_clasificado.csv: {total_records} registros")
        except FileNotFoundError:
            print(f"  {Colors.YELLOW}No se encontró archivo CSV all_jobs_clasificado.csv{Colors.RESET}")
            return
        except Exception as e:
            print(f"  {Colors.RED}Error leyendo all_jobs_clasificado.csv: {e}{Colors.RESET}")
            return
        
        # Definir nombre del archivo consolidado
        if custom_output:
            output_file = custom_output
        else:
            output_file = "resultados_clasificacion.csv"
        
        # Guardar en directorio actual
        df.to_csv(output_file, index=False, encoding='utf-8')
        
        # Copiar también a Base de Datos Tablas usando pathlib
        base_datos_dir = Path("../Base de Datos Tablas")
        if base_datos_dir.exists():
            import shutil
            dest_file = base_datos_dir / output_file
            shutil.copy2(output_file, dest_file)
            
            # Obtener información del archivo
            file_size = dest_file.stat().st_size / (1024 * 1024)  # MB
            
            print(f"  CSV consolidado creado exitosamente:")
            print(f"    Archivo: {output_file}")
            print(f"    Registros: {len(df):,}")
            print(f"    Tamaño: {file_size:.1f} MB")
            print(f"    Ubicación: {base_datos_dir}/")
        else:
            print(f"  {Colors.YELLOW}Directorio Base de Datos Tablas no encontrado{Colors.RESET}")
            print(f"  CSV consolidado guardado en: {output_file}")
        
    except Exception as e:
        print(f"  {Colors.RED}Error en consolidación: {e}{Colors.RESET}")

def main():
    """Función principal"""
    global USE_OLLAMA, FILTER_SKILLS
    
    # Parsear argumentos PRIMERO
    args = parse_arguments()
    
    # Configurar variables globales
    USE_OLLAMA = args.ollama
    FILTER_SKILLS = args.habilidades
    
    # Mostrar inicio con colores DESPUÉS de parsear
    print(f"\n{Colors.BOLD}{Colors.CYAN}Inicio del procesador de empleos v3{Colors.RESET}")
    print(f"  - Ollama AI: {Colors.GREEN if USE_OLLAMA else Colors.RED}{'SI' if USE_OLLAMA else 'NO'}{Colors.RESET}")
    print(f"  - Regex patterns: {Colors.GREEN}SI{Colors.RESET}")
    
    # Validar que Ollama esté disponible si se solicita
    if USE_OLLAMA and not OLLAMA_AVAILABLE:
        print(f"{Colors.RED}Error: --ollama especificado pero ollama_classifier no está disponible{Colors.RESET}")
        sys.exit(1)
    
    # Cargar diccionarios
    if not load_dictionaries():
        print(f"{Colors.RED}Error fatal: No se pudieron cargar los patrones{Colors.RESET}")
        sys.exit(1)
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}PROCESADOR DE EMPLEOS V3{Colors.RESET} - {Colors.YELLOW}Clasificacion Hibrida{Colors.RESET}")
    
    # Mostrar configuración
    print(f"{Colors.BOLD}Configuración:{Colors.RESET}")
    if USE_OLLAMA and OLLAMA_AVAILABLE:
        print(f"  Modo IA: {Colors.GREEN}Ollama{Colors.RESET}")
        print(f"    Modelo: {Colors.CYAN}{ollama_classifier.OLLAMA_MODEL}{Colors.RESET}")
        print(f"    Servidor: {Colors.CYAN}localhost:11434{Colors.RESET}")
    else:
        print(f"  Modo IA: {Colors.RED}Desactivado{Colors.RESET}")
    
    print(f"  Filtro de habilidades: {Colors.CYAN}{'Todas las habilidades' if FILTER_SKILLS == 'all' else FILTER_SKILLS}{Colors.RESET}")
    
    # Información del sistema de patrones
    info = PATTERN_MANAGER.get_system_info()
    total_patterns = sum(info['pattern_statistics']['combined'].values()) - info['pattern_statistics']['combined']['total']
    print(f"  Regex Patterns: {Colors.GREEN}ACTIVADO{Colors.RESET} ({Colors.CYAN}{total_patterns} patrones{Colors.RESET})")
    
    print(f"\n{Colors.CYAN}  Directorio de entrada: {Colors.RESET}{args.directorio}")
    
    # Hardcodear la ruta del archivo all_jobs.json
    all_jobs_path = f"{args.directorio}/all_jobs.json"
    
    try:
        # Intentar abrir el archivo directamente
        with open(all_jobs_path, 'r', encoding='utf-8') as f:
            test_load = json.load(f)
        file_size = len(str(test_load)) / (1024 * 1024)  # MB aproximado
        print(f"{Colors.GREEN}Archivo encontrado: {Colors.RESET}all_jobs.json ({Colors.CYAN}{file_size:.2f} MB{Colors.RESET})")
    except FileNotFoundError:
        print(f"{Colors.RED}Error: No se encontró all_jobs.json en {args.directorio}{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Error leyendo all_jobs.json: {e}{Colors.RESET}")
        sys.exit(1)
    
    # Procesar archivo all_jobs.json
    print(f"\n{Colors.BOLD}{Colors.GREEN}Procesando: all_jobs.json{Colors.RESET}")
    process_and_insert_jobs(all_jobs_path)
    
    # Imprimir estadísticas finales
    print_final_statistics()
    
    # Consolidar CSVs
    consolidate_and_export_csv(args.output)
    
    print(f"\n{Colors.GREEN}Procesamiento completado{Colors.RESET}")

if __name__ == "__main__":
    main()