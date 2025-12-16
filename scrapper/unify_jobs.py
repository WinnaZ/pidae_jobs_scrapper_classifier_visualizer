#!/usr/bin/env python3
"""
Job Unifier Script - Stable Version
Reads all JSON files from output_jobs and creates all_jobs.json
Includes validation and error handling for production use
"""

import json
import glob
import os
import shutil
from datetime import datetime

def unify_jobs():
    """Unifica todos los archivos JSON de empleos en un solo archivo"""
    # Path to output_jobs directory
    output_jobs_dir = "output_jobs"
    output_base_dir = "../Base de Datos Tablas"
    processed_dir = os.path.join(output_jobs_dir, "unified_jobs")
    
    # Verificar que existen los directorios
    if not os.path.exists(output_jobs_dir):
        print(f"ERROR: Directorio {output_jobs_dir} no existe")
        return False
        
    if not os.path.exists(output_base_dir):
        print(f"ERROR: Directorio {output_base_dir} no existe")
        return False
    
    # Get all JSON files but exclude all_jobs.json to avoid duplicating
    json_files = glob.glob(os.path.join(output_jobs_dir, "*.json"))
    json_files = [f for f in json_files if not os.path.basename(f) == "all_jobs.json"]
    
    if not json_files:
        print(f"ERROR: No se encontraron archivos JSON en {output_jobs_dir}")
        return False
    
    all_jobs = []
    processed_files_list = []
    processed_files_count = 0
    error_files = 0
    
    print(f"Encontrados {len(json_files)} archivos JSON (excluyendo all_jobs.json)")
    print(f"Directorio origen: {output_jobs_dir}")
    print(f"Directorio destino: {output_base_dir}")
    print("-" * 60)
    
    for file_path in json_files:
        try:
            # Verificar tamaño del archivo antes de procesarlo
            file_size = os.path.getsize(file_path)
            if file_size < 100:  # Archivos menores a 100 bytes son probablemente vacíos
                print(f"SALTADO: {os.path.basename(file_path)}: archivo demasiado pequeño ({file_size} bytes)")
                continue
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Validar estructura de datos
                job_count = 0
                if isinstance(data, list):
                    job_count = len(data)
                    if job_count == 0:  # Array vacío
                        print(f"SALTADO: {os.path.basename(file_path)}: array vacío")
                        continue
                    all_jobs.extend(data)
                elif isinstance(data, dict):
                    job_count = 1
                    all_jobs.append(data)
                else:
                    print(f"ADVERTENCIA: {os.path.basename(file_path)} tiene formato inesperado")
                    continue
                    
            print(f"OK: {os.path.basename(file_path)}: {job_count} empleos")
            processed_files_list.append(file_path)
            processed_files_count += 1
            
        except json.JSONDecodeError as e:
            print(f"ERROR JSON en {os.path.basename(file_path)}: {e}")
            error_files += 1
        except Exception as e:
            print(f"ERROR procesando {os.path.basename(file_path)}: {e}")
            error_files += 1
    
    print("-" * 60)
    print(f"Resumen del proceso:")
    print(f"   - Archivos procesados: {processed_files_count}")
    print(f"   - Archivos con error: {error_files}")
    print(f"   - Total empleos unificados: {len(all_jobs)}")
    
    # Write unified file to Base de Datos Tablas directory
    output_file = os.path.join(output_base_dir, "all_jobs.json")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
        
        print(f"Archivo unificado creado: {output_file}")
        print(f"Tamaño: {os.path.getsize(output_file) / (1024*1024):.1f} MB")
        
        # Move processed JSON files to unified_jobs folder
        try:
            os.makedirs(processed_dir, exist_ok=True)
            moved_files = []
            
            for file_path in processed_files_list:
                filename = os.path.basename(file_path)
                new_path = os.path.join(processed_dir, filename)
                shutil.move(file_path, new_path)
                moved_files.append(filename)
            
            if moved_files:
                print(f"Archivos movidos a unified_jobs/: {len(moved_files)}")
                print(f"   - {', '.join(moved_files[:3])}{'...' if len(moved_files) > 3 else ''}")
        
        except Exception as e:
            print(f"⚠️ Error moviendo archivos a unified_jobs/: {e}")
        
        return True
        
    except Exception as e:
        print(f"ERROR al guardar archivo unificado: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando unificación de empleos...")
    print("=" * 60)
    
    success = unify_jobs()
    
    if success:
        print("=" * 60)
        print("Unificación completada exitosamente!")
    else:
        print("=" * 60)
        print("La unificación falló. Revisar errores arriba.")
        exit(1)