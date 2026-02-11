#!/usr/bin/env python3
"""
Fix Ubicaciones Computrabajo
Corrige ubicaciones que tienen nombres de empresas/consultoras en lugar de ubicaciones reales.
Extrae la ubicación correcta desde la URL del empleo.
"""

import json
import re
import os
import glob

# Ubicaciones incorrectas específicas a corregir (match exacto, case-insensitive)
UBICACIONES_A_CORREGIR = [
    # Consultoras/RRHH
    'recursos humanos',
    'búsqueda y selección',
    'busqueda y seleccion',
    'capital humano',
    'gestión integral de rrhh',
    'gestion integral de rrhh',
    'soluciones en rrhh',
    'gestión humana',
    'gestion humana',
    'human capital',
    'gap soluciones rrhh',
    'gestión humana para empresas',
    'gestion humana para empresas',
    'consultora de rrhh',
    'consultora en rrhh',
    
    # Empresas/Marcas
    'technologies',
    'selection group',
    'biz consultores',
    'tecsan ingenieria ambiental s.a. u',
    'on s. a.',
    'club privado de vinos',
    'agustina castro',
    'chemsearch srl',
    '(re/max ii)',
    'logos s.r.l.',
    'clean force s.a.c.',
    'ingenieria y construcciones s.a',
    'sspsa s.a',
    'sur srl',
    'matic s.a.',
    'aguamora',
    'disegno',
    'indushomes',
    'ronda 360 s.r.l. u. t. e.',
    'tourn ingenieria srl',
    'libreria "utiles"',
    '5 seguridad privada',
    'it outsourcing',
    'control de plagas',
    'comunidad de inversión',
    'comunidad de inversion',
    'iluminación',
    'iluminacion',
    'escuela de vuelo s.r.l.',
    'estudio jurídico integral',
    'estudio juridico integral',
    'contadores públicos',
    'contadores publicos',
    'concesionario oficial de toyota',
    'deport show',
    '5 s.a.',
    
    # Palabras sueltas/sin sentido
    'sur',
    'in',
    'corp',
    'spa',
    'net',
    'on',
    'pep sh',
    'hr',
    'rp',
    'stop',
    'n',
    'extranjero',
    'la capital',
    'curuzú',
    
    # Países (no son ubicaciones de trabajo en Argentina)
    'colombia',
    'perú',
    'peru',
    'méxico',
    'mexico',
    'estados unidos',
    'españa',
    'espana',
    'venezuela',
    'ecuador',
    'uruguay',
    'italia',
    'armenia',
    'cabo verde',
    'el salvador',
    'uganda',
]

# Patrones que indican ubicación incorrecta (frases de trabajo mezcladas)
PATRONES_INCORRECTOS = [
    'full time en',
    'part time en',
    'remoto en',
    'hibrido en',
    'híbrido en',
    'presencial en',
    'caba en',
    'prov bs as',
    'bs as en',
    'bsas en',
    ' en el ',
    ' para ',
    'usd en',
    'us en',
    'call center en',
    'autoelevador',
    'cocina china',
    'cocina japonesa',
    'colchones y sommiers',
    'sistemas jr',
    'ventas y cotizaciones',
    'gestion de equipos',
    'gestion comercial',
    'retencion de clientes',
    'productos frescos',
    'consumo masivo',
    'expansion ',
    'capacitacion incluida',
    'varias vacantes',
    'transporte en',
    'tecnologia electronica',
    'soldadura ',
    'farmacia en',
    'obras industriales',
    'electronica para',
    'sistemas contra incendio',
    'campanas digitales',
    'administracion de empresas',
    'financieras para',
    'mora para',
    'sanitarios ',
    'salon ecommerce',
    'la industria optica',
]


def es_ubicacion_a_corregir(ubicacion):
    """Determina si una ubicación debe ser corregida"""
    if not ubicacion:
        return False
    
    ubicacion_lower = ubicacion.lower().strip()
    
    # Match exacto
    if ubicacion_lower in UBICACIONES_A_CORREGIR:
        return True
    
    # Buscar patrones incorrectos
    for patron in PATRONES_INCORRECTOS:
        if patron in ubicacion_lower:
            return True
    
    return False


def extraer_ubicacion_de_url(url):
    """Extrae la ubicación desde la URL de Computrabajo"""
    if not url:
        return None
    
    # Patrón: buscar "en-UBICACION" antes del hash o ID
    # Ejemplo: ...analista-administrativa-san-martin-en-san-martin-DCA0A6FB...
    
    # Primero intentar el patrón más específico: "-en-UBICACION-" seguido de hash
    match = re.search(r'-en-([a-z\-]+)-[A-F0-9]{20,}', url, re.IGNORECASE)
    if match:
        ubicacion = match.group(1).replace('-', ' ').title()
        return ubicacion
    
    # Segundo intento: buscar después de "en-" hasta el final o el hash
    match = re.search(r'-en-([a-z\-]+?)(?:-[A-F0-9]+|#|$)', url, re.IGNORECASE)
    if match:
        ubicacion = match.group(1).replace('-', ' ').title()
        return ubicacion
    
    return None


def procesar_archivo_json(archivo_json, modo_dry_run=True):
    """Procesa un archivo JSON corrigiendo solo empleos de Computrabajo"""
    
    print(f"\n  Procesando: {os.path.basename(archivo_json)}")
    
    try:
        with open(archivo_json, 'r', encoding='utf-8') as f:
            empleos = json.load(f)
    except Exception as e:
        print(f"    ERROR leyendo archivo: {e}")
        return 0, 0, 0
    
    if not isinstance(empleos, list):
        print(f"    ERROR: no es una lista de empleos")
        return 0, 0, 0
    
    # Filtrar solo Computrabajo
    empleos_computrabajo = [e for e in empleos if e.get('Fuente') == 'Computrabajo']
    
    if len(empleos_computrabajo) == 0:
        print(f"    Sin empleos de Computrabajo, saltando...")
        return len(empleos), 0, 0
    
    corregidos = 0
    ejemplos_correccion = []
    
    for empleo in empleos_computrabajo:
        ubicacion_original = empleo.get('ubicacion', '')
        url = empleo.get('url', '')
        
        if es_ubicacion_a_corregir(ubicacion_original):
            ubicacion_nueva = extraer_ubicacion_de_url(url)
            
            if ubicacion_nueva:
                if not modo_dry_run:
                    empleo['ubicacion'] = ubicacion_nueva
                    empleo['ubicacion_original'] = ubicacion_original
                
                corregidos += 1
                if len(ejemplos_correccion) < 3:
                    ejemplos_correccion.append({
                        'original': ubicacion_original,
                        'corregida': ubicacion_nueva,
                    })
    
    # Mostrar ejemplos
    if ejemplos_correccion:
        for p in ejemplos_correccion:
            print(f"      '{p['original'][:40]}' → '{p['corregida']}'")
    
    if corregidos > 0:
        print(f"    Corregidos: {corregidos}/{len(empleos_computrabajo)} empleos de Computrabajo")
    else:
        print(f"    Sin correcciones necesarias")
    
    # Guardar si no es dry run y hubo cambios
    if not modo_dry_run and corregidos > 0:
        with open(archivo_json, 'w', encoding='utf-8') as f:
            json.dump(empleos, f, ensure_ascii=False, indent=2)
        print(f"    ✓ Guardado")
    
    return len(empleos), len(empleos_computrabajo), corregidos


def procesar_carpeta(carpeta, modo_dry_run=True):
    """Procesa todos los archivos JSON en una carpeta"""
    
    # Buscar archivos JSON
    patron = os.path.join(carpeta, "*.json")
    archivos = glob.glob(patron)
    
    if not archivos:
        print(f"No se encontraron archivos JSON en: {carpeta}")
        return 0, 0, 0
    
    print(f"Encontrados {len(archivos)} archivos JSON en {carpeta}")
    
    total_empleos = 0
    total_computrabajo = 0
    total_corregidos = 0
    
    for archivo in sorted(archivos):
        empleos, computrabajo, corregidos = procesar_archivo_json(archivo, modo_dry_run)
        total_empleos += empleos
        total_computrabajo += computrabajo
        total_corregidos += corregidos
    
    return total_empleos, total_computrabajo, total_corregidos


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Corrige ubicaciones incorrectas en datos de Computrabajo')
    parser.add_argument('--aplicar', action='store_true', 
                        help='Aplica los cambios (por defecto solo muestra qué haría)')
    parser.add_argument('--archivo', type=str,
                        help='Archivo JSON a procesar')
    parser.add_argument('--carpeta', type=str,
                        help='Carpeta con archivos JSON a procesar')
    args = parser.parse_args()
    
    modo_dry_run = not args.aplicar
    
    print("=" * 60)
    print("FIX UBICACIONES COMPUTRABAJO")
    print("=" * 60)
    
    if modo_dry_run:
        print("\n⚠️  MODO SIMULACIÓN (dry-run)")
        print("   Usa --aplicar para guardar los cambios")
    else:
        print("\n✓ MODO APLICAR - Los cambios se guardarán")
    
    # Determinar qué procesar
    if args.carpeta:
        if not os.path.isdir(args.carpeta):
            print(f"\n❌ ERROR: No se encontró la carpeta: {args.carpeta}")
            return
        total_empleos, total_computrabajo, total_corregidos = procesar_carpeta(args.carpeta, modo_dry_run)
    elif args.archivo:
        if not os.path.exists(args.archivo):
            print(f"\n❌ ERROR: No se encontró el archivo: {args.archivo}")
            return
        total_empleos, total_computrabajo, total_corregidos = procesar_archivo_json(args.archivo, modo_dry_run)
    else:
        # Default: buscar all_jobs.json o carpeta output_jobs
        if os.path.exists('all_jobs.json'):
            total_empleos, total_computrabajo, total_corregidos = procesar_archivo_json('all_jobs.json', modo_dry_run)
        elif os.path.isdir('output_jobs'):
            total_empleos, total_computrabajo, total_corregidos = procesar_carpeta('output_jobs', modo_dry_run)
        else:
            print("\n❌ ERROR: No se encontró all_jobs.json ni carpeta output_jobs")
            print("   Usa --archivo o --carpeta para especificar la fuente")
            return
    
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Total empleos analizados: {total_empleos}")
    print(f"Empleos de Computrabajo: {total_computrabajo}")
    print(f"Ubicaciones corregidas: {total_corregidos}")
    if total_computrabajo > 0:
        print(f"Porcentaje corregido: {(total_corregidos/total_computrabajo*100):.1f}%")
    
    if modo_dry_run and total_corregidos > 0:
        print(f"\n💡 Para aplicar los cambios, ejecuta con --aplicar")


if __name__ == "__main__":
    main()