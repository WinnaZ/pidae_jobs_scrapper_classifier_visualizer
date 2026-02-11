#!/usr/bin/env python3
"""
Script para limpiar duplicados de all_jobs.json existente
Uso: python fix_duplicates.py [ruta_al_archivo]
"""

import json
import hashlib
import os
import shutil
from datetime import datetime
from collections import Counter

def generate_unique_id(job, source, hash_short, date_str):
    """Genera un Id Interno verdaderamente único"""
    return f"{source}-{date_str}-{hash_short}"

def fix_duplicates(filepath):
    """
    Elimina duplicados y regenera Id Interno únicos
    """
    print("=" * 70)
    print("  LIMPIADOR DE DUPLICADOS - all_jobs.json")
    print("=" * 70)
    
    if not os.path.exists(filepath):
        print(f"\n❌ ERROR: Archivo no encontrado: {filepath}")
        return False
    
    # Load file
    print(f"\n📂 Cargando: {filepath}")
    file_size_mb = os.path.getsize(filepath) / (1024*1024)
    print(f"   Tamaño: {file_size_mb:.2f} MB")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error leyendo JSON: {e}")
        return False
    
    print(f"   Empleos cargados: {len(jobs):,}")
    
    # Analyze current state
    print("\n📊 Analizando datos actuales...")
    
    # Count by source
    sources = Counter(job.get("Fuente", "Unknown") for job in jobs)
    print("\n   Empleos por fuente:")
    for source, count in sources.most_common():
        print(f"      - {source}: {count:,}")
    
    # Check for duplicate Id Interno
    id_counts = Counter(job.get("Id Interno", "") for job in jobs)
    duplicate_ids = {k: v for k, v in id_counts.items() if v > 1}
    
    if duplicate_ids:
        print(f"\n   ⚠️  Id Interno duplicados encontrados: {len(duplicate_ids)}")
        print(f"      (Esto confirma el problema que reportaste)")
        # Show top 5 most duplicated
        top_dups = sorted(duplicate_ids.items(), key=lambda x: -x[1])[:5]
        for id_val, count in top_dups:
            print(f"      - '{id_val}': {count} veces")
    
    # Deduplicate using hash
    print("\n🔧 Eliminando duplicados usando 'hash Descripcion'...")
    
    jobs_by_hash = {}
    duplicates = 0
    no_hash_count = 0
    duplicates_by_source = Counter()
    
    for idx, job in enumerate(jobs):
        # Get or generate hash
        job_hash = job.get("hash Descripcion")
        
        if not job_hash:
            no_hash_count += 1
            # Generate hash from description
            desc = job.get("descripcion", "") or job.get("description", "")
            if desc and len(desc) > 10:
                job_hash = hashlib.sha256(desc.encode('utf-8')).hexdigest()
            else:
                # Fallback to URL
                url = job.get("url", "")
                if url:
                    job_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()
                else:
                    # Last resort: use index + random
                    job_hash = hashlib.sha256(f"{idx}_{datetime.now().timestamp()}".encode()).hexdigest()
        
        if job_hash in jobs_by_hash:
            duplicates += 1
            source = job.get("Fuente", "Unknown")
            duplicates_by_source[source] += 1
        else:
            # Generate new unique Id Interno
            source = job.get("Fuente", "Unknown")
            fecha = job.get("fecha", datetime.now().strftime("%d/%m/%Y"))
            
            # Parse date
            try:
                parts = fecha.split("/")
                if len(parts) == 3:
                    date_str = f"{parts[2]}{parts[1]}{parts[0]}"
                else:
                    date_str = datetime.now().strftime("%Y%m%d")
            except:
                date_str = datetime.now().strftime("%Y%m%d")
            
            hash_short = job_hash[:8]
            new_id = f"{source}-{date_str}-{hash_short}"
            
            job["Id Interno"] = new_id
            job["hash Descripcion"] = job_hash
            jobs_by_hash[job_hash] = job
    
    unique_jobs = list(jobs_by_hash.values())
    
    # Results
    print("\n" + "=" * 70)
    print("  RESULTADOS")
    print("=" * 70)
    
    print(f"\n   📥 Empleos originales: {len(jobs):,}")
    print(f"   🗑️  Duplicados eliminados: {duplicates:,}")
    print(f"   ✅ Empleos únicos: {len(unique_jobs):,}")
    print(f"   📝 Sin hash previo: {no_hash_count:,}")
    
    if duplicates_by_source:
        print(f"\n   Duplicados por fuente:")
        for source, count in duplicates_by_source.most_common():
            print(f"      - {source}: {count:,}")
    
    reduction_pct = (duplicates / len(jobs) * 100) if jobs else 0
    print(f"\n   📉 Reducción: {reduction_pct:.1f}%")
    
    # Backup original
    backup_dir = os.path.dirname(filepath) or "."
    backup_name = os.path.basename(filepath).replace(".json", f"_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    backup_path = os.path.join(backup_dir, backup_name)
    
    print(f"\n💾 Creando backup: {backup_name}")
    shutil.copy(filepath, backup_path)
    
    # Save cleaned file
    print(f"💾 Guardando archivo limpio...")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(unique_jobs, f, ensure_ascii=False, indent=2)
    
    new_size_mb = os.path.getsize(filepath) / (1024*1024)
    print(f"   Nuevo tamaño: {new_size_mb:.2f} MB")
    
    # Verify new Id Interno uniqueness
    new_ids = [job.get("Id Interno") for job in unique_jobs]
    if len(new_ids) == len(set(new_ids)):
        print(f"\n   ✅ Todos los Id Interno son ahora únicos!")
    else:
        remaining_dups = len(new_ids) - len(set(new_ids))
        print(f"\n   ⚠️  Todavía hay {remaining_dups} Id Interno duplicados")
    
    print("\n" + "=" * 70)
    print("  ✅ LIMPIEZA COMPLETADA")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        # Default paths to try
        default_paths = [
            "../Base de Datos Tablas/all_jobs.json",
            "Base de Datos Tablas/all_jobs.json",
            "all_jobs.json"
        ]
        
        filepath = None
        for path in default_paths:
            if os.path.exists(path):
                filepath = path
                break
        
        if not filepath:
            print("Uso: python fix_duplicates.py <ruta_a_all_jobs.json>")
            print("\nNo se encontró all_jobs.json en las rutas por defecto:")
            for path in default_paths:
                print(f"  - {path}")
            exit(1)
    
    fix_duplicates(filepath)