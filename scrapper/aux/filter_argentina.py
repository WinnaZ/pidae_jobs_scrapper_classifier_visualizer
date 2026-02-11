#!/usr/bin/env python3
"""
Script para filtrar trabajos y quedarse solo con los de Argentina
Procesa archivos JSON y elimina trabajos de otros países

Uso:
    python filter_argentina.py                     # Procesa todos los JSON en output_jobs/
    python filter_argentina.py --dry-run           # Solo muestra qué haría, sin modificar
    python filter_argentina.py archivo.json        # Procesa un archivo específico
    python filter_argentina.py all_jobs.json --dry-run  # Dry-run en archivo específico
"""

import json
import glob
import os
import sys
import argparse
from datetime import datetime

def normalizar_ubicacion(texto):
    """Normaliza el texto de ubicación para comparación"""
    if not texto or not isinstance(texto, str):
        return ""
    return texto.lower().strip()

def es_argentina(empleo):
    """
    Verifica si un empleo es de Argentina
    Revisa múltiples campos: Pais, Ubicacion, ubicacion
    """
    # Lista de variantes de "Argentina"
    variantes_argentina = [
        "argentina",
        "ar",
        "buenos aires",
        "caba",
        "capital federal",
        "córdoba",
        "cordoba", 
        "rosario",
        "mendoza",
        "tucumán",
        "tucuman",
        "santa fe",
        "mar del plata",
        "salta",
        "san juan",
        "neuquén",
        "neuquen",
        "la plata",
        "bahía blanca",
        "bahia blanca",
        "san miguel de tucumán",
        "resistencia",
        "posadas",
        "san salvador de jujuy",
        "paraná",
        "parana",
        "formosa",
        "corrientes",
        "san luis",
        "santiago del estero",
        "catamarca",
        "la rioja",
        "río gallegos",
        "rio gallegos",
        "ushuaia",
        "rawson",
        "viedma",
        "santa rosa",
        "río cuarto",
        "rio cuarto"
    ]
    
    # Campos a revisar
    campos_ubicacion = ['Pais', 'Ubicacion', 'ubicacion', 'pais', 'location', 'country']
    
    for campo in campos_ubicacion:
        if campo in empleo:
            valor = normalizar_ubicacion(empleo[campo])
            if valor:
                # Verificar si contiene alguna variante de Argentina
                for variante in variantes_argentina:
                    if variante in valor:
                        return True
                
                # Si el campo tiene un país explícito que NO es Argentina, rechazar
                paises_excluir = [
                    "españa", "spain", "colombia", "méxico", "mexico", "chile",
                    "perú", "peru", "venezuela", "ecuador", "uruguay", "paraguay",
                    "bolivia", "costa rica", "panamá", "panama", "guatemala",
                    "honduras", "el salvador", "nicaragua", "cuba", "puerto rico",
                    "república dominicana", "dominicana", "brasil", "brazil",
                    "estados unidos", "united states", "usa", "rumania", "romania",
                    "portugal", "italia", "italy", "francia", "france", "alemania",
                    "germany", "reino unido", "uk", "united kingdom", "canadá", 
                    "canada", "australia", "nueva zelanda", "new zealand"
                ]
                
                for pais in paises_excluir:
                    if pais in valor:
                        return False
    
    # Si no hay información de ubicación clara, mantener por defecto
    return True

def obtener_pais(empleo):
    """Obtiene el país del empleo para mostrar en reportes"""
    campos = ['Pais', 'Ubicacion', 'ubicacion', 'pais']
    for campo in campos:
        if campo in empleo and empleo[campo]:
            return empleo[campo]
    return "Sin ubicación"

def procesar_archivo(filepath, dry_run=False, verbose=False):
    """
    Procesa un archivo JSON y retorna estadísticas
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            empleos = json.load(f)
        
        if not isinstance(empleos, list):
            return None, None, 0, 0, "No es una lista"
        
        total_original = len(empleos)
        empleos_argentina = []
        empleos_eliminados = []
        
        for e in empleos:
            if es_argentina(e):
                empleos_argentina.append(e)
            else:
                empleos_eliminados.append(e)
        
        total_filtrado = len(empleos_argentina)
        eliminados = total_original - total_filtrado
        
        return empleos_argentina, empleos_eliminados, total_original, eliminados, None
        
    except json.JSONDecodeError as e:
        return None, None, 0, 0, f"Error JSON: {e}"
    except Exception as e:
        return None, None, 0, 0, f"Error: {e}"

def main():
    parser = argparse.ArgumentParser(
        description='Filtra trabajos para quedarse solo con los de Argentina',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python filter_argentina.py                        # Procesa output_jobs/
  python filter_argentina.py --dry-run              # Solo muestra, no modifica
  python filter_argentina.py all_jobs.json          # Procesa archivo específico
  python filter_argentina.py all_jobs.json --dry-run --verbose  # Detalle completo
        """
    )
    parser.add_argument('archivo', nargs='?', help='Archivo JSON específico a procesar')
    parser.add_argument('--dry-run', '-n', action='store_true', 
                        help='Solo mostrar qué se haría, sin modificar archivos')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Mostrar detalle de trabajos eliminados')
    parser.add_argument('--output', '-o', type=str,
                        help='Archivo de salida (solo con archivo específico)')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("   FILTRO DE TRABAJOS - SOLO ARGENTINA")
    if args.dry_run:
        print("   ⚠️  MODO DRY-RUN - NO SE MODIFICARÁN ARCHIVOS")
    print("=" * 70)
    print()
    
    # Determinar qué archivos procesar
    if args.archivo:
        # Archivo específico
        if not os.path.exists(args.archivo):
            print(f"❌ Error: No existe el archivo '{args.archivo}'")
            sys.exit(1)
        archivos = [args.archivo]
        print(f"Procesando archivo: {args.archivo}")
    else:
        # Buscar archivos JSON en output_jobs
        posibles_paths = [
            "output_jobs/*.json",
            "../output_jobs/*.json",
            "/mnt/project/output_jobs/*.json",
        ]
        
        archivos = []
        for path in posibles_paths:
            archivos = glob.glob(path)
            if archivos:
                print(f"Buscando en: {path}")
                break
        
        if not archivos:
            print("No se encontraron archivos JSON en output_jobs/")
            print("Usa: python filter_argentina.py archivo.json")
            sys.exit(1)
    
    print(f"Encontrados {len(archivos)} archivo(s) para procesar")
    print("-" * 70)
    
    total_original_global = 0
    total_filtrado_global = 0
    total_eliminados_global = 0
    archivos_procesados = 0
    archivos_error = 0
    
    # Estadísticas por país
    paises_eliminados = {}
    
    # Crear directorio de backup si no es dry-run
    if not args.dry_run:
        backup_dir = "output_jobs_backup"
        os.makedirs(backup_dir, exist_ok=True)
    
    for filepath in sorted(archivos):
        filename = os.path.basename(filepath)
        
        empleos_filtrados, empleos_eliminados, total_orig, eliminados, error = procesar_archivo(filepath)
        
        if error:
            print(f"❌ {filename}: {error}")
            archivos_error += 1
            continue
        
        if total_orig == 0:
            print(f"⏭️  {filename}: Archivo vacío")
            continue
        
        # Contar países eliminados
        for empleo in (empleos_eliminados or []):
            pais = obtener_pais(empleo)
            paises_eliminados[pais] = paises_eliminados.get(pais, 0) + 1
        
        porcentaje_eliminado = (eliminados / total_orig * 100) if total_orig > 0 else 0
        
        if eliminados > 0:
            print(f"{'🔍' if args.dry_run else '✅'} {filename}: {total_orig} → {len(empleos_filtrados)} ({eliminados} eliminados, {porcentaje_eliminado:.1f}%)")
            
            # Mostrar detalle si es verbose
            if args.verbose and empleos_eliminados:
                print(f"   Países eliminados en este archivo:")
                paises_archivo = {}
                for e in empleos_eliminados:
                    p = obtener_pais(e)
                    paises_archivo[p] = paises_archivo.get(p, 0) + 1
                for pais, count in sorted(paises_archivo.items(), key=lambda x: -x[1])[:10]:
                    print(f"      - {pais}: {count}")
        else:
            print(f"✓  {filename}: {total_orig} trabajos (sin cambios)")
        
        # Guardar cambios si no es dry-run
        if not args.dry_run and eliminados > 0:
            # Backup del archivo original
            backup_dir = "output_jobs_backup"
            backup_path = os.path.join(backup_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                with open(backup_path, 'w', encoding='utf-8') as bf:
                    bf.write(f.read())
            
            # Determinar archivo de salida
            if args.output and len(archivos) == 1:
                output_path = args.output
            else:
                output_path = filepath
            
            # Guardar archivo filtrado
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(empleos_filtrados, f, ensure_ascii=False, indent=2)
        
        total_original_global += total_orig
        total_filtrado_global += len(empleos_filtrados)
        total_eliminados_global += eliminados
        archivos_procesados += 1
    
    # Resumen final
    print()
    print("=" * 70)
    print("   RESUMEN")
    print("=" * 70)
    print(f"Archivos procesados: {archivos_procesados}")
    print(f"Archivos con error:  {archivos_error}")
    print()
    print(f"Total trabajos originales:  {total_original_global:,}")
    print(f"Total trabajos Argentina:   {total_filtrado_global:,}")
    print(f"Total a eliminar:           {total_eliminados_global:,}")
    
    if total_original_global > 0:
        porcentaje = (total_eliminados_global / total_original_global * 100)
        print(f"Porcentaje a eliminar:      {porcentaje:.1f}%")
    
    # Mostrar países eliminados
    if paises_eliminados:
        print()
        print("Trabajos por país/ubicación (a eliminar):")
        for pais, count in sorted(paises_eliminados.items(), key=lambda x: -x[1])[:15]:
            print(f"   - {pais}: {count:,}")
        if len(paises_eliminados) > 15:
            print(f"   ... y {len(paises_eliminados) - 15} ubicaciones más")
    
    print()
    if args.dry_run:
        print("⚠️  MODO DRY-RUN: No se modificó ningún archivo")
        print("   Ejecuta sin --dry-run para aplicar los cambios")
    else:
        print(f"📁 Backup guardado en: output_jobs_backup/")
    print()

if __name__ == "__main__":
    main()
