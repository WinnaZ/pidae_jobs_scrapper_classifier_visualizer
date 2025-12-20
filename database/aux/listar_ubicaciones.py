#!/usr/bin/env python3
"""
Lista todas las ubicaciones únicas de all_jobs.json
"""

import json
import os
from collections import Counter

def main():
    archivo = "all_jobs.json"
    
    if not os.path.exists(archivo):
        print(f"No se encontró: {archivo}")
        return
    
    with open(archivo, 'r', encoding='utf-8') as f:
        empleos = json.load(f)
    
    print(f"Total empleos: {len(empleos)}")
    
    # Contar ubicaciones
    ubicaciones = Counter()
    for empleo in empleos:
        ubi = empleo.get('ubicacion', '').strip()
        fuente = empleo.get('Fuente', '')
        if ubi:
            ubicaciones[(ubi, fuente)] += 1
    
    # Mostrar ordenado por frecuencia
    print(f"\nUbicaciones únicas: {len(ubicaciones)}")
    print("=" * 80)
    print(f"{'UBICACIÓN':<40} {'FUENTE':<15} {'CANTIDAD':>8}")
    print("=" * 80)
    
    for (ubi, fuente), count in ubicaciones.most_common():
        print(f"{ubi[:40]:<40} {fuente:<15} {count:>8}")

if __name__ == "__main__":
    main()