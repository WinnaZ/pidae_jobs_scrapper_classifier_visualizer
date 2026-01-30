#!/usr/bin/env python3
"""
Lista todas las ubicaciones únicas de archivos JSON de empleos
Soporta archivo individual o carpeta con múltiples JSONs
"""

import json
import os
import glob
import argparse
from collections import Counter


def cargar_empleos_de_archivo(archivo):
    """Carga empleos de un archivo JSON"""
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception as e:
        print(f"Error leyendo {archivo}: {e}")
        return []


def cargar_empleos_de_carpeta(carpeta):
    """Carga empleos de todos los JSONs en una carpeta"""
    patron = os.path.join(carpeta, "*.json")
    archivos = glob.glob(patron)
    
    if not archivos:
        print(f"No se encontraron archivos JSON en: {carpeta}")
        return []
    
    print(f"Encontrados {len(archivos)} archivos JSON")
    
    todos_empleos = []
    for archivo in sorted(archivos):
        empleos = cargar_empleos_de_archivo(archivo)
        todos_empleos.extend(empleos)
    
    return todos_empleos


def obtener_ubicacion(empleo):
    """Obtiene la ubicación de un empleo (maneja diferentes nombres de campo)"""
    # Intentar diferentes variantes del campo
    return (empleo.get('ubicacion') or 
            empleo.get('Ubicacion') or 
            empleo.get('location') or 
            empleo.get('Location') or 
            '').strip()


def main():
    parser = argparse.ArgumentParser(description='Lista ubicaciones únicas de archivos de empleos')
    parser.add_argument('--archivo', type=str, help='Archivo JSON a procesar')
    parser.add_argument('--carpeta', type=str, help='Carpeta con archivos JSON')
    parser.add_argument('--fuente', type=str, help='Filtrar por fuente (ej: Computrabajo, ZonaJobs, Workana)')
    parser.add_argument('--top', type=int, default=0, help='Mostrar solo las N más frecuentes')
    args = parser.parse_args()
    
    # Cargar empleos
    if args.carpeta:
        if not os.path.isdir(args.carpeta):
            print(f"No se encontró la carpeta: {args.carpeta}")
            return
        empleos = cargar_empleos_de_carpeta(args.carpeta)
    elif args.archivo:
        if not os.path.exists(args.archivo):
            print(f"No se encontró: {args.archivo}")
            return
        empleos = cargar_empleos_de_archivo(args.archivo)
    else:
        # Default: buscar all_jobs.json o carpeta output_jobs
        if os.path.exists('all_jobs.json'):
            empleos = cargar_empleos_de_archivo('all_jobs.json')
        elif os.path.isdir('output_jobs'):
            empleos = cargar_empleos_de_carpeta('output_jobs')
        else:
            print("No se encontró all_jobs.json ni carpeta output_jobs")
            print("Usa --archivo o --carpeta para especificar la fuente")
            return
    
    if not empleos:
        print("No se encontraron empleos")
        return
    
    # Filtrar por fuente si se especificó
    if args.fuente:
        empleos = [e for e in empleos if e.get('Fuente', '').lower() == args.fuente.lower()]
        print(f"Filtrado por fuente: {args.fuente}")
    
    print(f"Total empleos: {len(empleos)}")
    
    # Contar ubicaciones
    ubicaciones = Counter()
    for empleo in empleos:
        ubi = obtener_ubicacion(empleo)
        fuente = empleo.get('Fuente', '')
        if ubi:
            ubicaciones[(ubi, fuente)] += 1
    
    # Mostrar ordenado por frecuencia
    print(f"\nUbicaciones únicas: {len(ubicaciones)}")
    print("=" * 80)
    print(f"{'UBICACIÓN':<40} {'FUENTE':<15} {'CANTIDAD':>8}")
    print("=" * 80)
    
    items = ubicaciones.most_common(args.top if args.top > 0 else None)
    for (ubi, fuente), count in items:
        print(f"{ubi[:40]:<40} {fuente:<15} {count:>8}")


if __name__ == "__main__":
    main()