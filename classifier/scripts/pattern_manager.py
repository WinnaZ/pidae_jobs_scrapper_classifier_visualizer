"""
Gestor Principal de Patrones Regex
=================================

Este módulo unifica el sistema de patrones base y aprendidos para clasificación
de requisitos de empleo según el esquema de Escudero.

Funcionalidades:
- Carga y combina patrones base + patrones aprendidos
- Clasificación automática usando regex
- Interfaz unificada para el sistema de procesamiento
- Gestión de aprendizaje automático desde Ollama

Estructura de clasificación:
1. Habilidades Blandas (4 categorías fijas)
2. Habilidades Duras (categorías extensibles)  
3. Títulos Académicos
4. Idiomas
"""

import re
import json
from datetime import datetime
from collections import defaultdict

# Importar módulos del sistema
from .base_patterns import get_all_base_patterns, compile_base_patterns, get_categories_info, get_escudero_category_mapping
from classifier.dictionaries.learned_patterns import (
    get_learned_patterns, add_learned_pattern, compile_learned_patterns,
    save_learned_patterns_to_file, load_learned_patterns_from_file,
    get_learning_statistics
)
from classifier.dictionaries.oecd_lightcast_skills_dictionary import find_category_for_skill_oecd, DICCIONARIO_OECD_LIGHTCAST, get_main_categories_oecd
from classifier.dictionaries.escudero_blandas_dictionary import (
    DICCIONARIO_ESCUDERO,
    get_main_categories as get_escudero_blandas_main_categories,
    get_skills_by_category as escudero_get_skills_by_category,
    get_all_synonyms_for_skill as escudero_get_all_synonyms_for_skill,
    get_category_display_name as escudero_get_category_display_name
)

class PatternManager:
    """
    Gestor principal del sistema de patrones para clasificación de requisitos
    """
    
    def __init__(self):
        self.base_patterns = None
        self.learned_patterns = None  
        self.combined_patterns = None
        self.categories_info = get_categories_info()
        self.escudero_mapping = get_escudero_category_mapping()
        self.reload_patterns()
    
    def reload_patterns(self):
        """Recarga y recompila todos los patrones (base + aprendidos)"""
        print("Cargando patrones base...")
        self.base_patterns = compile_base_patterns()
        
        print("Cargando patrones aprendidos...")
        load_learned_patterns_from_file()  # Asegurar que están actualizados
        self.learned_patterns = compile_learned_patterns()
        
        print("Combinando patrones...")
        self.combined_patterns = self._combine_patterns()
        
        print(f"Sistema de patrones cargado. Estadísticas:")
        self._print_pattern_statistics()
    
    def _combine_patterns(self):
        """Combina patrones base y aprendidos en una estructura unificada"""
        combined = {
            'habilidades_blandas': {},
            'habilidades_duras': {},
            'titulos': [],
            'idiomas': []
        }
        
        # Combinar habilidades blandas y duras (estructura por categorías)
        for area in ['habilidades_blandas', 'habilidades_duras']:
            # Agregar patrones base
            if area in self.base_patterns:
                for category, patterns in self.base_patterns[area].items():
                    if category not in combined[area]:
                        combined[area][category] = []
                    combined[area][category].extend(patterns)
            
            # Agregar patrones aprendidos
            if area in self.learned_patterns:
                for category, patterns in self.learned_patterns[area].items():
                    if category not in combined[area]:
                        combined[area][category] = []
                    combined[area][category].extend(patterns)
        
        # Combinar títulos e idiomas (listas simples)
        for area in ['titulos', 'idiomas']:
            if area in self.base_patterns:
                combined[area].extend(self.base_patterns[area])
            if area in self.learned_patterns:
                combined[area].extend(self.learned_patterns[area])
        
        return combined
    
    def classify_text(self, text, use_subcategories=False):
        """
        Clasifica un texto usando todos los patrones disponibles
        
        Args:
            text (str): Texto a clasificar
            use_subcategories (bool): Si True, retorna subcategorías específicas.
                                    Si False, mapea a las 4 categorías principales de Escudero.
            
        Returns:
            dict: Clasificaciones encontradas por área {
                'habilidades_blandas': {'categoria': [matches], ...},
                'habilidades_duras': {'categoria': [matches], ...},
                'titulos': [matches],
                'idiomas': [matches]
            }
        """
        if not text:
            return self._empty_classification()
        
        results = {
            'habilidades_blandas': {},
            'habilidades_duras': {},
            'titulos': [],
            'idiomas': []
        }
        
        text_lower = text.lower()
        
        # Clasificar habilidades blandas y duras
        for area in ['habilidades_blandas', 'habilidades_duras']:
            if area not in self.combined_patterns:
                continue
                
            for subcategory, patterns in self.combined_patterns[area].items():
                matches = []
                for compiled_pattern, label in patterns:
                    found_matches = compiled_pattern.findall(text)
                    if found_matches:
                        # Agregar matches únicos
                        for match in found_matches:
                            if isinstance(match, tuple):
                                match = ' '.join([m for m in match if m])  # Unir grupos capturados
                            if match and match not in matches:
                                matches.append(match)
                
                if matches:
                    if use_subcategories:
                        # Usar subcategorías específicas
                        results[area][subcategory] = matches
                    else:
                        # Mapear a categorías principales para habilidades blandas
                        if area == 'habilidades_blandas':
                            main_category = self.escudero_mapping.get(label, subcategory)
                            if main_category not in results[area]:
                                results[area][main_category] = []
                            results[area][main_category].extend([m for m in matches if m not in results[area][main_category]])
                        else:
                            # Para habilidades duras, usar subcategorías como están
                            results[area][subcategory] = matches
        
        # Clasificar títulos e idiomas
        for area in ['titulos', 'idiomas']:
            if area not in self.combined_patterns:
                continue
                
            matches = []
            for compiled_pattern, label in self.combined_patterns[area]:
                found_matches = compiled_pattern.findall(text)
                if found_matches:
                    for match in found_matches:
                        if isinstance(match, tuple):
                            match = ' '.join([m for m in match if m])
                        if match and match not in matches:
                            matches.append(match)
            
            if matches:
                results[area] = matches
        
        return results
    
    def classify_text_with_details(self, text):
        """
        Clasifica un texto y retorna tanto subcategorías como categorías principales
        
        Args:
            text (str): Texto a clasificar
            
        Returns:
            dict: {
                'subcategories': {...},  # Clasificaciones con subcategorías específicas
                'main_categories': {...}, # Clasificaciones mapeadas a categorías principales
                'mapping_info': {...}    # Información del mapeo realizado
            }
        """
        subcategory_results = self.classify_text(text, use_subcategories=True)
        main_category_results = self.classify_text(text, use_subcategories=False)
        
        # Crear información de mapeo
        mapping_info = {}
        if 'habilidades_blandas' in subcategory_results:
            mapping_info['habilidades_blandas'] = {}
            for subcat, matches in subcategory_results['habilidades_blandas'].items():
                main_cat = self.escudero_mapping.get(subcat, subcat)
                mapping_info['habilidades_blandas'][subcat] = {
                    'maps_to': main_cat,
                    'matches': matches
                }
        
        return {
            'subcategories': subcategory_results,
            'main_categories': main_category_results, 
            'mapping_info': mapping_info
        }
    
    def classify_requirement(self, requirement_text):
        """
        Clasifica un requisito individual y retorna el resultado estructurado
        
        Args:
            requirement_text (str): Texto del requisito a clasificar
            
        Returns:
            dict: {
                'text': requirement_text,
                'classifications': {...},
                'found_in_patterns': bool,
                'needs_ai_classification': bool
            }
        """
        classifications = self.classify_text(requirement_text)
        
        # Determinar si se encontraron clasificaciones
        has_classifications = (
            bool(classifications['habilidades_blandas']) or
            bool(classifications['habilidades_duras']) or
            bool(classifications['titulos']) or
            bool(classifications['idiomas'])
        )
        
        return {
            'text': requirement_text,
            'classifications': classifications,
            'found_in_patterns': has_classifications,
            'needs_ai_classification': not has_classifications
        }
    
    def learn_from_ai_classification(self, requirement, ai_area, ai_categoria):
        """
        Aprende un nuevo patrón desde una clasificación de IA (Ollama)
        Agrega nuevas habilidades/sinónimos DENTRO de las categorías Escudero existentes
        
        Args:
            requirement (str): Texto del requisito clasificado por IA
            ai_area (str): Área identificada por IA ('duro', 'blando', 'idioma', 'titulo')
            ai_categoria (str): Categoría identificada por IA
            
        Returns:
            bool: True si se aprendió el patrón exitosamente
        """
        # Mapear áreas de IA al esquema del sistema
        area_mapping = {
            'duro': 'habilidades_duras',
            'blando': 'habilidades_blandas', 
            'idioma': 'idiomas',
            'titulo': 'titulos'
        }
        
        mapped_area = area_mapping.get(ai_area.lower())
        if not mapped_area:
            return False
        
        # Determinar la categoría donde va a entrar este término
        if mapped_area == 'habilidades_duras':
            # Encontrar la categoría OECD-Lightcast más probable para esta habilidad
            categoria = find_category_for_skill_oecd(requirement)
            # Si no se encontró una categoría específica, intentar con búsqueda fuzzy
            if not categoria:
                # Buscar categoría basada en palabras clave del requisito
                categoria = self._find_best_category_for_skill(requirement)
            # Si aún no hay categoría, ignorar (no queremos crear nuevas categorías)
            if not categoria:
                return False
        elif mapped_area == 'habilidades_blandas':
            # Para habilidades blandas, mapear a una de las 4 categorías fijas
            categoria = self._map_to_fixed_soft_skills_category(ai_categoria, requirement)
        else:
            # Para idiomas y títulos, usar la categoría sugerida o general
            categoria = self._normalize_category_name(ai_categoria) if ai_categoria else 'general'
        
        # Crear patrón regex simple del requisito
        pattern = self._create_pattern_from_text(requirement)
        
        # Agregar al sistema de patrones aprendidos (como nuevo sinónimo/variación)
        success = add_learned_pattern(
            area=mapped_area,
            categoria=categoria,
            pattern=pattern,
            etiqueta=requirement,  # Usar el requisito como etiqueta
            source='ollama'
        )
        
        if success:
            save_learned_patterns_to_file()
            print(f"Sinónimo aprendido: '{requirement}' -> {mapped_area}.{categoria}")
        
        return success
    
    def _find_best_category_for_skill(self, skill_text):
        """
        Encuentra la categoría OECD-Lightcast más probable basada en palabras clave del diccionario
        Retorna: 'ai_related_skills' o 'tech_non_ai_skills'
        """
        skill_lower = skill_text.lower()
        max_matches = 0
        best_category = None
        
        # Iterar sobre todas las categorías del diccionario OECD
        for category_key, category_data in DICCIONARIO_OECD_LIGHTCAST['categories'].items():
            matches = 0
            # Buscar coincidencias con skills en esta categoría
            for skill in category_data.get('skills', []):
                original = skill.get('original', '').lower()
                # Coincidencia con el nombre original
                if original in skill_lower or skill_lower in original:
                    matches += 2
                
                # Coincidencias con sinónimos
                for sinonimo in skill.get('sinonimos', []):
                    sinonimo_lower = sinonimo.lower()
                    if sinonimo_lower in skill_lower or skill_lower in sinonimo_lower:
                        matches += 1
            
            # Actualizar mejor categoría si encontramos más coincidencias
            if matches > max_matches:
                max_matches = matches
                best_category = category_key
        
        # Si encontramos coincidencias, retornar la mejor categoría
        if best_category:
            return best_category
        
        # Fallback: buscar por palabras clave generales
        ai_indicators = ['ai', 'machine', 'learning', 'deep', 'neural', 'nlp', 'vision']
        has_ai_keyword = any(keyword in skill_lower for keyword in ai_indicators)
        
        # Por defecto, retornar la primera categoría del diccionario
        available_categories = get_main_categories_oecd()
        return available_categories[0] if available_categories else 'tech_non_ai_skills'
    
    def _map_to_fixed_soft_skills_category(self, ai_categoria, requirement_text):
        """
        Mapea una categoría de IA a una de las categorías fijas de habilidades blandas
        Usa el diccionario `escudero_blandas_dictionary.DICCIONARIO_ESCUDERO` para las 4 categorías
        """
        # Obtener categorías fijas desde el diccionario de Escudero
        soft_skills_categories = DICCIONARIO_ESCUDERO.get('categories', {})

        if not soft_skills_categories:
            return 'habilidades_de_caracter'

        # Texto a buscar: combinar categoría sugerida con texto del requisito
        search_text = (str(ai_categoria or '') + ' ' + requirement_text).lower()

        # Evaluar coincidencias usando nombres, originales y sinónimos
        max_matches = 0
        best_category = None

        for category_key, category_data in soft_skills_categories.items():
            matches = 0
            # Buscar en cada skill de la categoría
            for skill in category_data.get('skills', []):
                original = skill.get('original', '').lower()
                if original and (original in search_text or search_text in original):
                    matches += 3
                for syn in skill.get('sinonimos', []):
                    syn_low = syn.lower()
                    if syn_low and (syn_low in search_text or search_text in syn_low):
                        matches += 2

            # Contar coincidencias con el nombre de la categoría
            cat_name = category_data.get('name', category_key).lower()
            if cat_name in search_text:
                matches += 1

            if matches > max_matches:
                max_matches = matches
                best_category = category_key

        if best_category and max_matches > 0:
            return best_category

        return next(iter(soft_skills_categories.keys())) if soft_skills_categories else 'habilidades_de_caracter'
    
    def _normalize_category_name(self, category_name):
        """Normaliza nombres de categorías para ser consistentes"""
        if category_name is None:
            return 'general'
        return category_name.lower().replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
    
    def _create_pattern_from_text(self, text):
        """Crea un patrón regex simple desde un texto"""
        # Escapar caracteres especiales y crear patrón con word boundaries
        escaped = re.escape(text.lower().strip())
        return rf'\b{escaped}\b'
    
    def _empty_classification(self):
        """Retorna una clasificación vacía"""
        return {
            'habilidades_blandas': {},
            'habilidades_duras': {},
            'titulos': [],
            'idiomas': []
        }
    
    def _print_pattern_statistics(self):
        """Imprime estadísticas de los patrones cargados"""
        base_stats = self._count_patterns(self.base_patterns)
        learned_stats = get_learning_statistics()
        
        print(f"  Patrones base: {base_stats['total']}")
        print(f"  Patrones aprendidos: {learned_stats['total_patterns']}")
        print(f"  Total combinado: {base_stats['total'] + learned_stats['total_patterns']}")
        
        for area in ['habilidades_blandas', 'habilidades_duras']:
            if area in self.combined_patterns:
                area_total = sum(len(patterns) for patterns in self.combined_patterns[area].values())
                print(f"    {area}: {area_total} patrones")
    
    def _count_patterns(self, pattern_dict):
        """Cuenta el total de patrones en una estructura"""
        total = 0
        for area, patterns in pattern_dict.items():
            if area in ['habilidades_blandas', 'habilidades_duras']:
                total += sum(len(pattern_list) for pattern_list in patterns.values())
            else:
                total += len(patterns)
        return {'total': total}
    
    def get_pattern_statistics(self):
        """
        Retorna estadísticas de los patrones en formato dict
        
        Returns:
            dict: Estadísticas con totales por área
        """
        base_stats = self._count_patterns(self.base_patterns)
        learned_stats = get_learning_statistics()
        
        stats = {
            'total': base_stats['total'] + learned_stats['total_patterns'],
            'base_patterns': base_stats['total'],
            'learned_patterns': learned_stats['total_patterns']
        }
        
        # Agregar estadísticas por área
        for area in ['habilidades_blandas', 'habilidades_duras', 'titulos', 'idiomas']:
            if area in self.combined_patterns:
                if area in ['habilidades_blandas', 'habilidades_duras']:
                    area_total = sum(len(patterns) for patterns in self.combined_patterns[area].values())
                else:
                    area_total = len(self.combined_patterns[area])
                stats[area] = area_total
            else:
                stats[area] = 0
        
        return stats
    
    def get_system_info(self):
        """
        Retorna información completa del sistema
        
        Returns:
            dict: Información del sistema de patrones
        """
        return {
            'categories_info': self.categories_info,
            'pattern_statistics': {
                'base': self._count_patterns(self.base_patterns),
                'learned': get_learning_statistics(),
                'combined': self._count_patterns(self.combined_patterns)
            },
            'areas': ['habilidades_blandas', 'habilidades_duras', 'titulos', 'idiomas'],
            'soft_skills_categories': DICCIONARIO_ESCUDERO.get('categories', {})
        }

# ============================================================================
# INSTANCIA GLOBAL DEL GESTOR
# ============================================================================

# Crear instancia global para uso en otros módulos
pattern_manager = PatternManager()

# ============================================================================
# FUNCIONES DE CONVENIENCIA PARA COMPATIBILIDAD
# ============================================================================

def get_compiled_patterns():
    """
    Función de compatibilidad con el sistema anterior
    Retorna patrones compilados en el formato esperado por el código existente
    """
    patterns = pattern_manager.combined_patterns
    
    # Convertir al formato antiguo para compatibilidad
    legacy_format = {
        'duros': {},
        'blandos': {},
        'idiomas': {}
    }
    
    # Mapear habilidades duras
    for category, pattern_list in patterns['habilidades_duras'].items():
        category_name = category.replace('_', ' ').title()
        legacy_format['duros'][category_name] = [compiled_pattern for compiled_pattern, label in pattern_list]
    
    # Mapear habilidades blandas
    for category, pattern_list in patterns['habilidades_blandas'].items():
        category_name = category.replace('_', ' ').title()
        legacy_format['blandos'][category_name] = [compiled_pattern for compiled_pattern, label in pattern_list]
    
    # Mapear idiomas
    legacy_format['idiomas'] = [compiled_pattern for compiled_pattern, label in patterns['idiomas']]
    
    return legacy_format

def classify_requirements(text):
    """
    Función de conveniencia para clasificar texto
    
    Args:
        text (str): Texto a clasificar
        
    Returns:
        dict: Clasificaciones en formato compatible con el sistema anterior
    """
    return pattern_manager.classify_text(text)

def learn_from_ai(requirement, area, categoria):
    """
    Función de conveniencia para aprender desde IA (Ollama)
    
    Args:
        requirement (str): Requisito clasificado por IA
        area (str): Área ('duro', 'blando', 'idioma', 'titulo')
        categoria (str): Categoría específica
        
    Returns:
        bool: True si se aprendió exitosamente
    """
    return pattern_manager.learn_from_ai_classification(requirement, area, categoria)