#!/usr/bin/env python3
"""
Job Unifier Script v2 - With Deduplication
Reads all JSON files from output_jobs, removes duplicates using hash, and creates all_jobs.json
"""

import json
import glob
import os
import shutil
from datetime import datetime
import hashlib

def generate_unique_id(job, index):
    """
    Generates a truly unique Id Interno based on source + hash
    Format: SOURCE-YYYYMMDD-HASH8
    """
    source = job.get("Fuente", "Unknown")
    hash_desc = job.get("hash Descripcion", "")
    fecha = job.get("fecha", datetime.now().strftime("%d/%m/%Y"))
    
    # Convert fecha from DD/MM/YYYY to YYYYMMDD
    try:
        parts = fecha.split("/")
        if len(parts) == 3:
            date_str = f"{parts[2]}{parts[1]}{parts[0]}"
        else:
            date_str = datetime.now().strftime("%Y%m%d")
    except:
        date_str = datetime.now().strftime("%Y%m%d")
    
    # Use first 8 chars of hash for brevity
    hash_short = hash_desc[:8] if hash_desc else hashlib.md5(str(index).encode()).hexdigest()[:8]
    
    return f"{source}-{date_str}-{hash_short}"

def unify_jobs():
    """Unifica todos los archivos JSON de empleos en un solo archivo, eliminando duplicados"""
    # Path to output_jobs directory
    output_jobs_dir = "output_jobs"
    output_base_dir = "../database"
    processed_dir = os.path.join(output_jobs_dir, "unified_jobs")
    
    # Verificar que existen los directorios
    if not os.path.exists(output_jobs_dir):
        print(f"ERROR: Directorio {output_jobs_dir} no existe")
        return False
        
    if not os.path.exists(output_base_dir):
        os.makedirs(output_base_dir, exist_ok=True)
        print(f"Creado directorio: {output_base_dir}")
    
    # Get all JSON files but exclude all_jobs.json to avoid duplicating
    json_files = glob.glob(os.path.join(output_jobs_dir, "*.json"))
    json_files = [f for f in json_files if not os.path.basename(f) == "all_jobs.json"]
    
    if not json_files:
        print(f"ERROR: No se encontraron archivos JSON en {output_jobs_dir}")
        return False
    
    # Use dict with hash as key for deduplication
    jobs_by_hash = {}
    processed_files_list = []
    processed_files_count = 0
    error_files = 0
    total_jobs_read = 0
    duplicates_found = 0
    duplicates_by_source = {}
    
    print(f"Encontrados {len(json_files)} archivos JSON (excluyendo all_jobs.json)")
    print(f"Directorio origen: {output_jobs_dir}")
    print(f"Directorio destino: {output_base_dir}")
    print("-" * 60)
    
    for file_path in sorted(json_files):
        try:
            # Verificar tamaño del archivo antes de procesarlo
            file_size = os.path.getsize(file_path)
            if file_size < 100:
                print(f"SALTADO: {os.path.basename(file_path)}: archivo demasiado pequeño ({file_size} bytes)")
                continue
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Validar estructura de datos
                jobs_list = []
                if isinstance(data, list):
                    if len(data) == 0:
                        print(f"SALTADO: {os.path.basename(file_path)}: array vacío")
                        continue
                    jobs_list = data
                elif isinstance(data, dict):
                    jobs_list = [data]
                else:
                    print(f"ADVERTENCIA: {os.path.basename(file_path)} tiene formato inesperado")
                    continue
                
                file_jobs = 0
                file_duplicates = 0
                
                for idx, job in enumerate(jobs_list):
                    total_jobs_read += 1
                    
                    # Get hash for deduplication
                    job_hash = job.get("hash Descripcion")
                    
                    # If no hash exists, generate one from description
                    if not job_hash:
                        desc = job.get("descripcion", "") or job.get("description", "")
                        if desc:
                            job_hash = hashlib.sha256(desc.encode('utf-8')).hexdigest()
                            job["hash Descripcion"] = job_hash
                        else:
                            # Use URL as fallback
                            url = job.get("url", str(idx))
                            job_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
                            job["hash Descripcion"] = job_hash
                    
                    # Check for duplicate
                    if job_hash in jobs_by_hash:
                        duplicates_found += 1
                        file_duplicates += 1
                        source = job.get("Fuente", "Unknown")
                        duplicates_by_source[source] = duplicates_by_source.get(source, 0) + 1
                    else:
                        # Generate unique Id Interno
                        job["Id Interno"] = generate_unique_id(job, len(jobs_by_hash))
                        jobs_by_hash[job_hash] = job
                        file_jobs += 1
                
                status = "OK"
                if file_duplicates > 0:
                    status = f"OK ({file_duplicates} duplicados removidos)"
                    
                print(f"{status}: {os.path.basename(file_path)}: {file_jobs} empleos únicos de {len(jobs_list)}")
                processed_files_list.append(file_path)
                processed_files_count += 1
                
        except json.JSONDecodeError as e:
            print(f"ERROR JSON en {os.path.basename(file_path)}: {e}")
            error_files += 1
        except Exception as e:
            print(f"ERROR procesando {os.path.basename(file_path)}: {e}")
            error_files += 1
    
    # Convert dict values to list
    all_jobs = list(jobs_by_hash.values())
    
    print("-" * 60)
    print(f"Resumen del proceso:")
    print(f"   - Archivos procesados: {processed_files_count}")
    print(f"   - Archivos con error: {error_files}")
    print(f"   - Total empleos leídos: {total_jobs_read}")
    print(f"   - Duplicados eliminados: {duplicates_found}")
    print(f"   - Empleos únicos finales: {len(all_jobs)}")
    
    if duplicates_by_source:
        print(f"\n   Duplicados por fuente:")
        for source, count in sorted(duplicates_by_source.items(), key=lambda x: -x[1]):
            print(f"      - {source}: {count}")
    
    # Write unified file to database directory
    output_file = os.path.join(output_base_dir, "all_jobs.json")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_jobs, f, ensure_ascii=False, indent=2)
        
        print(f"\nArchivo unificado creado: {output_file}")
        print(f"Tamaño: {os.path.getsize(output_file) / (1024*1024):.1f} MB")
        
        # Save deduplication stats
        stats_file = os.path.join(output_base_dir, "deduplication_stats.json")
        stats = {
            "timestamp": datetime.now().isoformat(),
            "total_read": total_jobs_read,
            "duplicates_removed": duplicates_found,
            "unique_jobs": len(all_jobs),
            "duplicates_by_source": duplicates_by_source,
            "files_processed": processed_files_count
        }
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"Estadísticas guardadas en: {stats_file}")
        
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


def clean_existing_all_jobs(filepath):
    """
    Limpia un archivo all_jobs.json existente eliminando duplicados
    y regenerando Id Interno únicos
    """
    print(f"\n{'='*60}")
    print("LIMPIEZA DE ARCHIVO EXISTENTE")
    print(f"{'='*60}")
    
    if not os.path.exists(filepath):
        print(f"ERROR: Archivo no encontrado: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        
        print(f"Empleos cargados: {len(jobs)}")
        
        # Deduplicate using hash
        jobs_by_hash = {}
        duplicates = 0
        
        for idx, job in enumerate(jobs):
            job_hash = job.get("hash Descripcion")
            
            if not job_hash:
                desc = job.get("descripcion", "") or job.get("description", "")
                if desc:
                    job_hash = hashlib.sha256(desc.encode('utf-8')).hexdigest()
                else:
                    url = job.get("url", str(idx))
                    job_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
            
            if job_hash in jobs_by_hash:
                duplicates += 1
            else:
                # Regenerate unique Id Interno
                job["Id Interno"] = generate_unique_id(job, len(jobs_by_hash))
                job["hash Descripcion"] = job_hash
                jobs_by_hash[job_hash] = job
        
        unique_jobs = list(jobs_by_hash.values())
        
        print(f"Duplicados encontrados: {duplicates}")
        print(f"Empleos únicos: {len(unique_jobs)}")
        
        # Backup original
        backup_path = filepath.replace(".json", f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        shutil.copy(filepath, backup_path)
        print(f"Backup creado: {backup_path}")
        
        # Save cleaned file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(unique_jobs, f, ensure_ascii=False, indent=2)
        
        print(f"Archivo limpiado guardado: {filepath}")
        print(f"Tamaño: {os.path.getsize(filepath) / (1024*1024):.1f} MB")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("UNIFICADOR DE EMPLEOS v2 - CON DEDUPLICACIÓN")
    print("=" * 60)
    
    # Check for clean mode
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        if len(sys.argv) > 2:
            clean_existing_all_jobs(sys.argv[2])
        else:
            # Default path
            clean_existing_all_jobs("../database/all_jobs.json")
    else:
        print("\nIniciando unificación de empleos...")
        print("-" * 60)
        
        success = unify_jobs()
        
        if success:
            print("=" * 60)
            print("✅ Unificación completada exitosamente!")
            print("   Los duplicados han sido eliminados usando 'hash Descripcion'")
        else:
            print("=" * 60)
            print("❌ La unificación falló. Revisar errores arriba.")
            exit(1)