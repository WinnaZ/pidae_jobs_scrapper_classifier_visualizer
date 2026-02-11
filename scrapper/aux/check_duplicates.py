#!/usr/bin/env python3
"""
Diagnóstico de duplicados - Verifica si los duplicados son reales
"""

import json
import hashlib
from collections import Counter, defaultdict
import sys

def analyze_duplicates(filepath):
    print("=" * 70)
    print("  DIAGNÓSTICO DE DUPLICADOS")
    print("=" * 70)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        jobs = json.load(f)
    
    print(f"\nTotal empleos: {len(jobs):,}")
    
    # Group by source
    by_source = defaultdict(list)
    for job in jobs:
        source = job.get("Fuente", "Unknown")
        by_source[source].append(job)
    
    print("\n" + "-" * 70)
    print("ANÁLISIS POR FUENTE")
    print("-" * 70)
    
    for source, source_jobs in sorted(by_source.items()):
        print(f"\n{'='*50}")
        print(f"  {source}: {len(source_jobs)} empleos")
        print(f"{'='*50}")
        
        # Check hash distribution
        hashes = [job.get("hash Descripcion", "") for job in source_jobs]
        hash_counts = Counter(hashes)
        
        # Find duplicates
        duplicate_hashes = {h: c for h, c in hash_counts.items() if c > 1 and h}
        
        if duplicate_hashes:
            total_dups = sum(c - 1 for c in duplicate_hashes.values())
            print(f"\n  ⚠️  Hashes duplicados: {len(duplicate_hashes)}")
            print(f"  ⚠️  Total entradas duplicadas: {total_dups}")
            
            # Show examples of duplicates
            print(f"\n  Ejemplos de duplicados:")
            for i, (dup_hash, count) in enumerate(list(duplicate_hashes.items())[:3]):
                print(f"\n  --- Duplicado {i+1} (aparece {count} veces) ---")
                
                # Find all jobs with this hash
                dup_jobs = [j for j in source_jobs if j.get("hash Descripcion") == dup_hash]
                
                for j, job in enumerate(dup_jobs[:2]):  # Show first 2 occurrences
                    print(f"\n    Ocurrencia {j+1}:")
                    print(f"      Id Interno: {job.get('Id Interno', 'N/A')}")
                    print(f"      Título: {job.get('titulo', 'N/A')[:60]}")
                    print(f"      Empresa: {job.get('Empresa', 'N/A')[:40]}")
                    print(f"      Fecha: {job.get('fecha', 'N/A')}")
                    print(f"      URL: {job.get('url', 'N/A')[:70]}")
                    desc = job.get('descripcion', '')[:100].replace('\n', ' ')
                    print(f"      Descripción: {desc}...")
        else:
            print(f"\n  ✅ No hay hashes duplicados")
        
        # Check for empty/missing hashes
        empty_hashes = sum(1 for h in hashes if not h)
        if empty_hashes:
            print(f"\n  ⚠️  Empleos sin hash: {empty_hashes}")
        
        # Check Id Interno duplicates
        ids = [job.get("Id Interno", "") for job in source_jobs]
        id_counts = Counter(ids)
        duplicate_ids = {k: v for k, v in id_counts.items() if v > 1}
        
        if duplicate_ids:
            print(f"\n  ⚠️  Id Interno duplicados: {len(duplicate_ids)}")
            # Show first 5
            for id_val, count in list(duplicate_ids.items())[:5]:
                print(f"      '{id_val}': {count} veces")
        
        # Check for description issues
        descriptions = [job.get("descripcion", "") for job in source_jobs]
        desc_lengths = [len(d) for d in descriptions]
        short_descs = sum(1 for d in desc_lengths if d < 50)
        empty_descs = sum(1 for d in descriptions if not d or d == "Descripción no disponible")
        
        print(f"\n  Estadísticas de descripción:")
        print(f"    - Promedio longitud: {sum(desc_lengths)/len(desc_lengths):.0f} chars")
        print(f"    - Descripciones cortas (<50 chars): {short_descs}")
        print(f"    - Descripciones vacías/no disponible: {empty_descs}")
        
        if empty_descs > 0:
            print(f"\n    ⚠️  Las descripciones vacías pueden causar falsos duplicados!")

    # Overall duplicate analysis
    print("\n" + "=" * 70)
    print("VERIFICACIÓN CRUZADA DE DUPLICADOS")
    print("=" * 70)
    
    all_hashes = defaultdict(list)
    for job in jobs:
        h = job.get("hash Descripcion", "")
        if h:
            all_hashes[h].append(job)
    
    cross_source_dups = 0
    for h, jobs_with_hash in all_hashes.items():
        sources = set(j.get("Fuente") for j in jobs_with_hash)
        if len(sources) > 1:
            cross_source_dups += 1
            if cross_source_dups <= 3:
                print(f"\n  Mismo trabajo en múltiples fuentes:")
                print(f"    Hash: {h[:16]}...")
                for job in jobs_with_hash:
                    print(f"    - {job.get('Fuente')}: {job.get('titulo', 'N/A')[:50]}")
    
    if cross_source_dups:
        print(f"\n  Total duplicados entre fuentes: {cross_source_dups}")
    else:
        print("\n  ✅ No hay duplicados entre diferentes fuentes")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        # Try to find the backup (before fix)
        import glob
        backups = glob.glob("../*_backup_*.json")
        if backups:
            filepath = sorted(backups)[-1]  # Latest backup
            print(f"Usando backup: {filepath}")
        else:
            filepath = "all_jobs.json"
    
    analyze_duplicates(filepath)