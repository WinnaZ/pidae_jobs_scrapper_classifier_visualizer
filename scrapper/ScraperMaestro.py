#!/usr/bin/env python3
"""
Script Maestro para ejecutar múltiples scrapers en paralelo
Ejecuta ZonaJobs, Workana, Computrabajo y LinkedIn usando threads
"""

import threading
import subprocess
import sys
import time
from datetime import datetime
import argparse
import os

# Colores para la terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class ScraperThread(threading.Thread):
    """Thread personalizado para ejecutar un scraper"""
    
    # Colores únicos para cada scraper
    SCRAPER_COLORS = {
        'ZonaJobs': Colors.OKGREEN,
        'Workana': Colors.OKCYAN,
        'Computrabajo': Colors.HEADER,  # Magenta/Violeta
        'LinkedIn': Colors.OKBLUE       # Azul
    }
    
    def __init__(self, nombre, script_path, debug=False):
        threading.Thread.__init__(self)
        self.nombre = nombre
        self.script_path = script_path
        self.debug = debug
        self.inicio = None
        self.fin = None
        self.exitcode = None
        self.error = None
        self.color = self.SCRAPER_COLORS.get(nombre, Colors.ENDC)
        self.lock = threading.Lock()
        
    def print_output(self, line):
        """Imprime una línea con el color del scraper"""
        with self.lock:
            print(f"{self.color}[{self.nombre:13}]{Colors.ENDC} {line}", flush=True)
        
    def run(self):
        """Ejecuta el scraper"""
        self.print_output("Iniciando scraper...")
        self.inicio = datetime.now()
        
        try:
            # Construir el comando con -u para salida sin buffer
            cmd = [sys.executable, '-u', self.script_path]
            if self.debug:
                cmd.append("--debug")
            
            # Ejecutar el scraper con salida en tiempo real
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env={**os.environ, 'PYTHONUNBUFFERED': '1'}
            )
            
            # Leer y mostrar salida en tiempo real
            for line in process.stdout:
                line = line.rstrip()
                if line:  # Solo mostrar líneas no vacías
                    self.print_output(line)
            
            # Esperar a que termine el proceso
            process.wait()
            self.exitcode = process.returncode
            
            if self.exitcode == 0:
                self.print_output(f"{Colors.OKGREEN}✓ Completado exitosamente{Colors.ENDC}")
            else:
                self.print_output(f"{Colors.FAIL}✗ Error en ejecución (código: {self.exitcode}){Colors.ENDC}")
                
        except Exception as e:
            self.print_output(f"{Colors.FAIL}✗ Excepción: {str(e)}{Colors.ENDC}")
            self.error = str(e)
            self.exitcode = -1
            
        finally:
            self.fin = datetime.now()
    
    def duracion(self):
        """Retorna la duración de ejecución"""
        if self.inicio and self.fin:
            delta = self.fin - self.inicio
            return delta.total_seconds()
        return 0

def main():
    parser = argparse.ArgumentParser(description='Ejecuta múltiples scrapers en paralelo')
    parser.add_argument('--debug', action='store_true', help='Activa el modo debug en todos los scrapers')
    parser.add_argument('--scrapers', nargs='+', 
                        choices=['zonajobs', 'workana', 'computrabajo', 'linkedin', 'all'],
                        default=['all'],
                        help='Scrapers a ejecutar (default: all)')
    args = parser.parse_args()
    
    # Banner
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}")
    print("   SCRAPER MAESTRO - EJECUCIÓN PARALELA")
    print(f"{'='*60}{Colors.ENDC}\n")
    
    inicio_total = datetime.now()
    print(f"Inicio: {inicio_total.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modo debug: {Colors.OKGREEN if args.debug else Colors.WARNING}{'Activado' if args.debug else 'Desactivado'}{Colors.ENDC}\n")
    
    # Obtener el directorio donde está este script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Definir scrapers disponibles con rutas absolutas
    scrapers_config = {
        'zonajobs': {
            'nombre': 'ZonaJobs',
            'script': os.path.join(script_dir, 'ZonaJobs.py')
        },
        'workana': {
            'nombre': 'Workana',
            'script': os.path.join(script_dir, 'Workana.py')
        },
        'computrabajo': {
            'nombre': 'Computrabajo',
            'script': os.path.join(script_dir, 'Computrabajo.py')
        },
        'linkedin': {
            'nombre': 'LinkedIn',
            'script': os.path.join(script_dir, 'LinkedIn.py')
        }
    }
    
    # Determinar qué scrapers ejecutar
    if 'all' in args.scrapers:
        scrapers_a_ejecutar = list(scrapers_config.keys())
    else:
        scrapers_a_ejecutar = args.scrapers
    
    print(f"Scrapers a ejecutar: {Colors.OKCYAN}{', '.join([scrapers_config[s]['nombre'] for s in scrapers_a_ejecutar])}{Colors.ENDC}\n")
    
    # Crear threads para cada scraper
    threads = []
    for scraper_key in scrapers_a_ejecutar:
        config = scrapers_config[scraper_key]
        thread = ScraperThread(
            nombre=config['nombre'],
            script_path=config['script'],
            debug=args.debug
        )
        threads.append(thread)
    
    # Iniciar todos los threads
    print(f"{Colors.BOLD}Iniciando scrapers en paralelo...{Colors.ENDC}")
    print(f"{Colors.BOLD}Leyenda de colores:{Colors.ENDC}")
    print(f"  {Colors.OKGREEN}[ZonaJobs     ]{Colors.ENDC} - Verde")
    print(f"  {Colors.OKCYAN}[Workana      ]{Colors.ENDC} - Cyan")
    print(f"  {Colors.HEADER}[Computrabajo ]{Colors.ENDC} - Violeta")
    print(f"  {Colors.OKBLUE}[LinkedIn     ]{Colors.ENDC} - Azul")
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    for thread in threads:
        thread.start()
        time.sleep(0.5)  # Pequeña pausa entre inicios
    
    # Esperar a que terminen todos
    for thread in threads:
        thread.join()
    
    fin_total = datetime.now()
    duracion_total = (fin_total - inicio_total).total_seconds()
    
    # Mostrar resumen
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}")
    print("   RESUMEN DE EJECUCIÓN")
    print(f"{'='*60}{Colors.ENDC}\n")
    
    exitosos = 0
    fallidos = 0
    
    for thread in threads:
        duracion_mins = thread.duracion() / 60
        estado_color = Colors.OKGREEN if thread.exitcode == 0 else Colors.FAIL
        estado_texto = "✓ EXITOSO" if thread.exitcode == 0 else "✗ FALLIDO"
        
        print(f"{thread.color}{thread.nombre:15}{Colors.ENDC} - {estado_color}{estado_texto}{Colors.ENDC} - Duración: {duracion_mins:.2f} mins")
        
        if thread.exitcode == 0:
            exitosos += 1
        else:
            fallidos += 1
            if thread.error:
                print(f"  └─ Error: {thread.error[:200]}")
    
    print(f"\n{Colors.BOLD}Estadísticas:{Colors.ENDC}")
    print(f"  Total scrapers: {len(threads)}")
    print(f"  {Colors.OKGREEN}Exitosos: {exitosos}{Colors.ENDC}")
    print(f"  {Colors.FAIL}Fallidos: {fallidos}{Colors.ENDC}")
    print(f"  Duración total: {Colors.OKCYAN}{duracion_total/60:.2f} minutos{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Finalizado: {fin_total.strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}\n")
    
    # Exit code basado en resultados
    sys.exit(0 if fallidos == 0 else 1)

if __name__ == "__main__":
    main()