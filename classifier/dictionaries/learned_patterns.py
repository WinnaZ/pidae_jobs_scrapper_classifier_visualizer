"""
Patrones Aprendidos Automáticamente por Gemini
==============================================

Este archivo mantiene los patrones que el sistema ha aprendido automáticamente
de las clasificaciones realizadas por Gemini AI.

Los patrones se organizan según el mismo esquema que base_patterns.py:
- habilidades_blandas (4 categorías fijas de Escudero)
- habilidades_duras (categorías extensibles)
- titulos (académicos)
- idiomas

IMPORTANTE: 
- Las categorías de habilidades blandas NO pueden modificarse
- Solo se pueden agregar sinónimos a las subcategorías existentes
- Las habilidades duras SÍ pueden tener nuevas categorías
"""

import re
import json
import os
from datetime import datetime

# ============================================================================
# PATRONES APRENDIDOS POR GEMINI - ESTRUCTURA ORGANIZADA
# ============================================================================

LEARNED_PATTERNS_GEMINI = {
    'habilidades_blandas': {
        'habilidades_de_caracter': [
            (r'\binovador\b', 'Habilidades de carácter'),
            (r'\bresponsable\b', 'Habilidades de carácter'),
            (r'\bcomprometido\b', 'Habilidades de carácter'),
        ],
        'habilidades_sociales': [
            (r'\bcomunicativo\b', 'Habilidades sociales'),
            (r'\bhabilidades\s+de\s+comunicaci[oó]n\s+excelentes\b', 'Habilidades sociales'),
        ],
        'habilidades_gestion_personal': [
            (r'\bliderazgo\b', 'Habilidades de gestión de personal'),
        ],
        'habilidades_servicio_cliente': [
            (r'\bservicio\s+de\s+calidad\b', 'Habilidades de servicio al cliente'),
        ]
    },
    
    'habilidades_duras': {
        'testing_qa': [
            (r'\bpostman\b', 'Testing y QA'),
            (r'\bselenium\b', 'Testing y QA'),
        ],
        'desarrollo_web': [
            (r'\blink\s+building\b', 'Desarrollo Web'),
        ],
        'marketing_digital': [
            (r'\bmarketing\s+online\b', 'Marketing Digital'),
            (r'\bestrategia\s+de\s+marketing\b', 'Marketing Digital'),
            (r'\bescritura\s+de\s+artículos\b', 'Marketing Digital'),
            (r'\boptimización\s+de\s+landing\s+pages\b', 'Marketing Digital'),
            (r'\binstagram\b', 'Marketing Digital'),
            (r'\bpublicidad\s+en\s+google\b', 'Marketing Digital'),
            (r'\blead\s+generation\b', 'Marketing Digital'),
            (r'\bsocial\s+media\s+marketing\b', 'Marketing Digital'),
            (r'\bedición\s+de\s+textos\b', 'Marketing Digital'),
            (r'\bbranding\s+personal\b', 'Marketing Digital'),
            (r'\bdesarrollo\s+de\s+presencia\s+digital\b', 'Marketing Digital'),
        ],
        'herramientas_investigacion': [
            (r'\binvestigación\b', 'Herramientas de Investigación'),
            (r'\bbokun\b', 'Herramientas de Investigación'),
            (r'\btripadvisor\b', 'Herramientas de Investigación'),
            (r'\bviator\b', 'Herramientas de Investigación'),
        ],
        'diseno_multimedia': [
            (r'\bdiseño\s+gráfico\b', 'Diseño y Multimedia'),
            (r'\badobe\s+creative\s+cloud\b', 'Diseño y Multimedia'),
        ]
    },
    
    'titulos': [
        # Títulos específicos aprendidos por Gemini (si los hay)
    ],
    
    'idiomas': [
        # Idiomas específicos aprendidos por Gemini (si los hay) 
    ]
}

# ============================================================================
# METADATOS DE APRENDIZAJE
# ============================================================================

LEARNING_METADATA = {
    'last_update': None,
    'total_learned_patterns': 0,
    'learning_history': [],
    'gemini_classifications_count': 0
}

# ============================================================================
# FUNCIONES PARA GESTIONAR PATRONES APRENDIDOS
# ============================================================================

def get_learned_patterns():
    """
    Retorna todos los patrones aprendidos por Gemini
    
    Returns:
        dict: Patrones aprendidos organizados por área y categoría
    """
    return LEARNED_PATTERNS_GEMINI

def add_learned_pattern(area, categoria, pattern, etiqueta, source='gemini'):
    """
    Agrega un nuevo patrón aprendido
    
    Args:
        area (str): Área principal ('habilidades_blandas', 'habilidades_duras', 'titulos', 'idiomas')
        categoria (str): Categoría específica dentro del área
        pattern (str): Patrón regex a agregar
        etiqueta (str): Etiqueta/nombre del patrón
        source (str): Fuente del aprendizaje (default: 'gemini')
        
    Returns:
        bool: True si se agregó exitosamente, False si hubo error
    """
    try:
        # Validar que el área existe
        if area not in LEARNED_PATTERNS_GEMINI:
            print(f"Error: Área '{area}' no existe")
            return False
            
        # Para habilidades blandas, validar que la categoría sea una de las 4 fijas
        if area == 'habilidades_blandas':
            categorias_fijas = [
                'habilidades_de_caracter',
                'habilidades_sociales', 
                'habilidades_gestion_personal',
                'habilidades_servicio_cliente'
            ]
            if categoria not in categorias_fijas:
                print(f"Error: No se pueden crear nuevas categorías en habilidades blandas. Categorías permitidas: {categorias_fijas}")
                return False
        
        # Preparar estructura según el área
        if area in ['habilidades_blandas', 'habilidades_duras']:
            if categoria not in LEARNED_PATTERNS_GEMINI[area]:
                if area == 'habilidades_blandas':
                    print(f"Error: Categoría '{categoria}' no existe en habilidades blandas")
                    return False
                else:
                    # Para habilidades duras, sí se pueden crear nuevas categorías
                    LEARNED_PATTERNS_GEMINI[area][categoria] = []
            
            # Verificar si el patrón ya existe para evitar duplicados
            existing_patterns = [p[0] for p in LEARNED_PATTERNS_GEMINI[area][categoria]]
            if pattern in existing_patterns:
                print(f"Patrón duplicado detectado, no agregado: {area}.{categoria} -> '{pattern}'")
                return False
            
            LEARNED_PATTERNS_GEMINI[area][categoria].append((pattern, etiqueta))
        else:
            # Para títulos e idiomas, también verificar duplicados
            existing_patterns = [p[0] for p in LEARNED_PATTERNS_GEMINI[area]]
            if pattern in existing_patterns:
                print(f"Patrón duplicado detectado, no agregado: {area} -> '{pattern}'")
                return False
            LEARNED_PATTERNS_GEMINI[area].append((pattern, etiqueta))
        
        # Actualizar metadatos
        LEARNING_METADATA['last_update'] = datetime.now().isoformat()
        LEARNING_METADATA['total_learned_patterns'] += 1
        LEARNING_METADATA['learning_history'].append({
            'timestamp': datetime.now().isoformat(),
            'area': area,
            'categoria': categoria,
            'pattern': pattern,
            'etiqueta': etiqueta,
            'source': source
        })
        
        print(f"Patrón aprendido agregado: {area}.{categoria} -> '{pattern}' ({etiqueta})")
        return True
        
    except Exception as e:
        print(f"Error agregando patrón aprendido: {e}")
        return False

def compile_learned_patterns():
    """
    Compila todos los patrones aprendidos en objetos regex
    
    Returns:
        dict: Patrones compilados con la misma estructura que base_patterns
    """
    compiled = {}
    
    for area, patterns in LEARNED_PATTERNS_GEMINI.items():
        if area in ['habilidades_blandas', 'habilidades_duras']:
            compiled[area] = {}
            for category, pattern_list in patterns.items():
                compiled[area][category] = []
                for pattern_str, label in pattern_list:
                    try:
                        compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                        compiled[area][category].append((compiled_pattern, label))
                    except re.error as e:
                        print(f"Error compilando patrón aprendido '{pattern_str}': {e}")
        else:
            # Para títulos e idiomas
            compiled[area] = []
            for pattern_str, label in patterns:
                try:
                    compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                    compiled[area].append((compiled_pattern, label))
                except re.error as e:
                    print(f"Error compilando patrón aprendido '{pattern_str}': {e}")
    
    return compiled

def save_learned_patterns_to_file(filepath=None):
    """
    Guarda los patrones aprendidos en un archivo JSON
    
    Args:
        filepath (str): Ruta del archivo donde guardar (opcional)
    """
    if filepath is None:
        filepath = 'output_logs/learned_patterns.json'
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    data = {
        'learned_patterns': LEARNED_PATTERNS_GEMINI,
        'metadata': LEARNING_METADATA
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Patrones aprendidos guardados en: {filepath}")

def load_learned_patterns_from_file(filepath=None):
    """
    Carga patrones aprendidos desde un archivo JSON
    
    Args:
        filepath (str): Ruta del archivo a cargar (opcional)
        
    Returns:
        bool: True si se cargó exitosamente, False si hubo error
    """
    global LEARNED_PATTERNS_GEMINI, LEARNING_METADATA
    
    if filepath is None:
        filepath = 'output_logs/learned_patterns.json'
    
    if not os.path.exists(filepath):
        print(f"Archivo de patrones aprendidos no encontrado: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        LEARNED_PATTERNS_GEMINI = data.get('learned_patterns', LEARNED_PATTERNS_GEMINI)
        LEARNING_METADATA = data.get('metadata', LEARNING_METADATA)
        
        print(f"Patrones aprendidos cargados desde: {filepath}")
        print(f"Total de patrones aprendidos: {LEARNING_METADATA.get('total_learned_patterns', 0)}")
        return True
        
    except Exception as e:
        print(f"Error cargando patrones aprendidos: {e}")
        return False

def get_learning_statistics():
    """
    Retorna estadísticas sobre el aprendizaje
    
    Returns:
        dict: Estadísticas de los patrones aprendidos
    """
    stats = {
        'total_patterns': LEARNING_METADATA.get('total_learned_patterns', 0),
        'last_update': LEARNING_METADATA.get('last_update'),
        'patterns_by_area': {}
    }
    
    for area, patterns in LEARNED_PATTERNS_GEMINI.items():
        if area in ['habilidades_blandas', 'habilidades_duras']:
            area_count = sum(len(pattern_list) for pattern_list in patterns.values())
            stats['patterns_by_area'][area] = {
                'total': area_count,
                'by_category': {cat: len(plist) for cat, plist in patterns.items()}
            }
        else:
            stats['patterns_by_area'][area] = {'total': len(patterns)}
    
    return stats

# ============================================================================
# INICIALIZACIÓN
# ============================================================================

# Intentar cargar patrones existentes al importar el módulo
load_learned_patterns_from_file()