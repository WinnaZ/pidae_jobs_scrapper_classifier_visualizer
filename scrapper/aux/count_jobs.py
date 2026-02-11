#!/usr/bin/env python3
"""
Script simple para contar empleos en archivos JSON
Cuenta por Fuente, por Área y total
"""

import json
import glob
import os
from collections import defaultdict

# Colores para output
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

def count_jobs_in_files():
    """Lee todos los archivos JSON y cuenta empleos"""
    
    # Buscar archivos JSON en output_jobs
    input_dir = '.'
    
    json_files = glob.glob(f'{input_dir}/*.json')
    
    if not json_files:
        print(f"{Colors.RED}No se encontraron archivos .json en '{input_dir}'{Colors.RESET}")
        return
    
    # Contadores
    total_jobs = 0
    jobs_by_source = defaultdict(int)  # Por Fuente
    jobs_by_file = {}                  # Por archivo
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== CONTADOR DE EMPLEOS ==={Colors.RESET}\n")
    print(f"{Colors.YELLOW}Analizando {len(json_files)} archivos...{Colors.RESET}\n")
    
    # Procesar cada archivo
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                jobs_data = json.load(f)
            
            file_count = len(jobs_data)
            filename = os.path.basename(json_file)
            jobs_by_file[filename] = file_count
            total_jobs += file_count
            
            # Contar por fuente y área
            for job in jobs_data:
                fuente = job.get('Fuente', '') or job.get('fuente', 'Desconocido')
                jobs_by_source[fuente] += 1
                
            print(f"  {Colors.GRAY}[OK]{Colors.RESET} {filename:<60s} {Colors.GREEN}{file_count:>6,}{Colors.RESET} empleos")
            
        except Exception as e:
            print(f"  {Colors.RED}[ERROR]{Colors.RESET} {filename}: Error - {e}")
    
    # Mostrar resultados
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== RESUMEN GENERAL ==={Colors.RESET}")
    print(f"{Colors.WHITE}Total de empleos:{Colors.RESET} {Colors.GREEN}{Colors.BOLD}{total_jobs:,}{Colors.RESET}")
    print(f"{Colors.WHITE}Total de archivos:{Colors.RESET} {Colors.CYAN}{len(json_files)}{Colors.RESET}")
    print(f"{Colors.WHITE}Promedio por archivo:{Colors.RESET} {Colors.YELLOW}{total_jobs//len(json_files):,}{Colors.RESET}")
    
    # Contar por fuente
    if jobs_by_source:
        print(f"\n{Colors.BOLD}{Colors.BLUE}=== POR FUENTE ==={Colors.RESET}")
        for fuente, count in sorted(jobs_by_source.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_jobs * 100) if total_jobs > 0 else 0
            print(f"  {Colors.CYAN}{fuente:<30s}{Colors.RESET} {Colors.WHITE}{count:>8,}{Colors.RESET} empleos {Colors.GRAY}({percentage:.1f}%){Colors.RESET}")
    
    print()

if __name__ == "__main__":
    count_jobs_in_files()
