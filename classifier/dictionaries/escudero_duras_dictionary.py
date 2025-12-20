"""
Diccionario de Escudero et al para Habilidades Duras
===================================================

Diccionario base para clasificación de habilidades técnicas según el trabajo de Escudero.
Contiene 8 categorías principales y sus subcategorías con sinónimos.
"""

DICCIONARIO_ESCUDERO_DURAS = {
    "title": "Diccionario del trabajo de Escudero et al para Habilidades Duras",
    "note": "Algunas habilidades cognitivas deberían pasar a habilidades blandas",
    "categories": {
        "habilidades_cognitivas": {
            "name": "Habilidades cognitivas (sentido estricto)",
            "skills": [
                {"original": "resolver problemas", "sinonimos": ["solucionar", "aclarar", "averiguar", "descrifrar"]},
                {"original": "investigación", "sinonimos": ["exploración", "indagación", "averiguación", "búsqueda", "encuesta", "pesquisa", "sondeo"]},
                {"original": "análisis", "sinonimos": ["estudio", "examen", "observación", "comparación", "partición", "separación", "distinción"]},
                {"original": "pensamiento crítico", "sinonimos": []},
                {"original": "matemática", "sinonimos": ["exacto", "cabal", "preciso", "justo", "riguroso", "automático"]},
                {"original": "estadística", "sinonimos": ["catastral", "censual", "demográfico", "descriptivo"]},
                {"original": "adaptabilidad", "sinonimos": ["ductilidad", "elasticidad"]},
                {"original": "dirección", "sinonimos": ["gobierno", "mando", "jefatura", "administración", "directivo", "gerencia"]},
                {"original": "control", "sinonimos": ["inspección", "observación", "examen", "comprobación", "registro"]},
                {"original": "planificación", "sinonimos": ["proyecto"]},
                {"original": "análisis datos", "sinonimos": []},
                {"original": "ingeniería datos", "sinonimos": []},
                {"original": "modelamiento datos", "sinonimos": []},
                {"original": "visualización datos", "sinonimos": []},
                {"original": "minería datos", "sinonimos": []},
                {"original": "ciencia datos", "sinonimos": ["sabiduría", "sapiencia", "conocimiento", "erudición"]},
                {"original": "análisis predictivo", "sinonimos": []},
                {"original": "modelos predictivos", "sinonimos": []},
                {"original": "analizar", "sinonimos": ["examinar", "estudiar", "observar", "averiguar", "comparar", "considerar", "descomponer", "detallar", "distinguir", "individualizar", "separar"]},
                {"original": "diseñar", "sinonimos": ["proyectar", "trazar", "esbozar", "esquematizar", "abocetar", "delinear", "plantear"]},
                {"original": "reglas diseño", "sinonimos": []},
                {"original": "evaluación", "sinonimos": ["valoración", "tasación", "peritaje", "estimación", "apreciación"]},
                {"original": "interpretación", "sinonimos": ["comentario", "explicación", "análisis", "apreciación", "lectura", "glosa", "definición", "conclusión", "deducción", "entendimiento", "exegesis"]},
                {"original": "cálculo", "sinonimos": ["computo"]},
                {"original": "contabilidad", "sinonimos": ["administración", "tesorería", "caja"]},
                {"original": "corregir", "sinonimos": ["enmendar", "subsanar", "reformar", "rehacer", "modificar", "retocar", "perfeccionar"]},
                {"original": "medición", "sinonimos": ["medida", "evaluación", "cálculo", "sondeo"]},
                {"original": "procesamiento información", "sinonimos": ["proceso"]},
                {"original": "toma decisiones", "sinonimos": ["determinación", "resolución"]},
                {"original": "generación ideas", "sinonimos": ["representación", "sensación", "percepción", "imaginación", "ilusión", "pensamiento", "juicio", "compresión", "conocimiento", "concepto", "noción", "reflexión", "designio", "arquetipo", "modelo"]},
                {"original": "memoria", "sinonimos": ["recuerdo", "evocación", "retentivo", "rememoración", "mención", "conmemoración"]}
            ]
        },
        "habilidades_computacionales_generales": {
            "name": "Habilidades computacionales (generales)",
            "skills": [
                {"original": "computadora", "sinonimos": ["ordenador", "calculadora", "procesador", "electrónico"]},
                {"original": "hojas cálculo", "sinonimos": []},
                {"original": "programa", "sinonimos": ["exposición", "plan", "planteamiento", "proyecto", "sistema", "línea", "conducto", "programación", "esquema", "borrador", "boceto", "bosquejo", "anuncio", "aviso"]},
                {"original": "software", "sinonimos": []},
                {"original": "excel", "sinonimos": []},
                {"original": "powerpoint", "sinonimos": []},
                {"original": "internet", "sinonimos": []},
                {"original": "word", "sinonimos": []},
                {"original": "outlook", "sinonimos": []},
                {"original": "office", "sinonimos": []},
                {"original": "windows", "sinonimos": []}
            ]
        },
        "habilidades_computacionales_especificas": {
            "name": "Habilidades computacionales (específicas)",
            "skills": [
                {"original": "lenguaje programación", "sinonimos": []},
                {"original": "programación", "sinonimos": ["programa"]},
                {"original": "java", "sinonimos": []},
                {"original": "sql", "sinonimos": []},
                {"original": "python", "sinonimos": []},
                {"original": "javascript", "sinonimos": ["js"]},
                {"original": "html", "sinonimos": []},
                {"original": "css", "sinonimos": []},
                {"original": "react", "sinonimos": []},
                {"original": "angular", "sinonimos": []},
                {"original": "nodejs", "sinonimos": ["node.js", "node"]},
                {"original": "instalación de computadoras", "sinonimos": []},
                {"original": "reparación de computadoras", "sinonimos": []},
                {"original": "mantenimiento de computadoras", "sinonimos": []},
                {"original": "desarrollo web", "sinonimos": []},
                {"original": "diseño web", "sinonimos": []},
                {"original": "erp", "sinonimos": ["softland", "sap", "xubio", "wave", "cloudbooks", "nubox", "bloomberg", "anfix"]}
            ]
        },
        "habilidades_aprendizaje_maquinal_ia": {
            "name": "Habilidades de aprendizaje maquinal e inteligencia artificial",
            "skills": [
                {"original": "inteligencia artificial", "sinonimos": []},
                {"original": "artificial intelligence", "sinonimos": []},
                {"original": "aprendizaje maquinal", "sinonimos": []},
                {"original": "machine learning", "sinonimos": []},
                {"original": "árboles de decisión", "sinonimos": []},
                {"original": "apache hadoop", "sinonimos": []},
                {"original": "redes bayesianas", "sinonimos": []},
                {"original": "automatización", "sinonimos": []},
                {"original": "redes neuronales", "sinonimos": []},
                {"original": "support vector machines", "sinonimos": ["svm"]},
                {"original": "tensorflow", "sinonimos": []},
                {"original": "mapreduce", "sinonimos": []},
                {"original": "splunk", "sinonimos": []},
                {"original": "convolutional neural network", "sinonimos": ["cnn"]},
                {"original": "análisis cluster", "sinonimos": []}
            ]
        },
        "habilidades_financieras": {
            "name": "Habilidades financieras",
            "skills": [
                {"original": "presupuesto", "sinonimos": ["cálculo", "computo", "estimación", "evaluación", "partida", "fondo", "coste", "determinación"]},
                {"original": "contabilidad", "sinonimos": []},
                {"original": "finanzas", "sinonimos": ["negocio", "economía", "dinero", "inversión", "hacienda", "capital"]},
                {"original": "costos", "sinonimos": ["coste", "precio", "importe", "gasto", "tarifa"]},
                {"original": "análisis presupuesto", "sinonimos": []},
                {"original": "análisis financiero", "sinonimos": []},
                {"original": "análisis costos", "sinonimos": []}
            ]
        },
        "habilidades_escritura": {
            "name": "Habilidades de escritura",
            "skills": [
                {"original": "escribir", "sinonimos": ["transcribir", "manuscribir", "copiar", "anotar", "firmar", "rubricar", "autografiar", "trazar", "caligrafiar", "mecanografiar", "taquigrafiar"]},
                {"original": "editar", "sinonimos": ["publicar", "imprimir", "difundir", "reproducir", "reimprimir"]},
                {"original": "reportes", "sinonimos": ["contener", "refrenar", "frenar", "aplacar", "apaciguar", "calmar", "sosegar"]},
                {"original": "propuestas", "sinonimos": ["proposición"]}
            ]
        },
        "habilidades_administracion_proyectos": {
            "name": "Habilidades de administración de proyectos",
            "skills": [
                {"original": "administración proyectos", "sinonimos": []},
                {"original": "project management", "sinonimos": []},
                {"original": "gestión proyectos", "sinonimos": []},
                {"original": "scrum", "sinonimos": []},
                {"original": "agile", "sinonimos": ["ágil"]},
                {"original": "kanban", "sinonimos": []}
            ]
        },
        "bases_datos": {
            "name": "Bases de Datos",
            "skills": [
                {"original": "mysql", "sinonimos": []},
                {"original": "postgresql", "sinonimos": ["postgres"]},
                {"original": "mongodb", "sinonimos": []},
                {"original": "oracle", "sinonimos": []},
                {"original": "sql server", "sinonimos": []},
                {"original": "sqlite", "sinonimos": []},
                {"original": "redis", "sinonimos": []},
                {"original": "nosql", "sinonimos": []}
            ]
        }
    }
}

# ============================================================================
# FUNCIONES DE CONVENIENCIA PARA ACCEDER AL DICCIONARIO DURAS
# ============================================================================

def get_main_categories_duras():
    """Retorna las categorías principales de habilidades duras"""
    return list(DICCIONARIO_ESCUDERO_DURAS['categories'].keys())

def get_skills_by_category_duras(category):
    """Retorna las habilidades de una categoría específica de habilidades duras"""
    return DICCIONARIO_ESCUDERO_DURAS['categories'].get(category, {}).get('skills', [])

def get_all_skills_duras():
    """Retorna todas las habilidades duras de todas las categorías"""
    all_skills = []
    for category_data in DICCIONARIO_ESCUDERO_DURAS['categories'].values():
        all_skills.extend(category_data['skills'])
    return all_skills

def get_skill_to_category_mapping_duras():
    """Retorna un mapeo de habilidad -> categoría principal para habilidades duras"""
    mapping = {}
    for category, category_data in DICCIONARIO_ESCUDERO_DURAS['categories'].items():
        for skill in category_data['skills']:
            # Mapear tanto la habilidad original como los sinónimos
            mapping[skill['original']] = category
            for sinonimo in skill['sinonimos']:
                mapping[sinonimo] = category
    return mapping

def get_all_synonyms_for_skill_duras(skill_name):
    """Retorna todos los sinónimos para una habilidad específica dura"""
    for category_data in DICCIONARIO_ESCUDERO_DURAS['categories'].values():
        for skill in category_data['skills']:
            if skill['original'] == skill_name:
                return skill['sinonimos']
    return []

def get_category_display_name_duras(category_key):
    """Retorna el nombre para mostrar de una categoría dura"""
    return DICCIONARIO_ESCUDERO_DURAS['categories'].get(category_key, {}).get('name', category_key)

def find_category_for_skill_duras(skill_text):
    """
    Encuentra la categoría más apropiada para una habilidad dura
    
    Args:
        skill_text (str): Texto de la habilidad a clasificar
        
    Returns:
        str: Nombre de la categoría o 'general' si no se encuentra
    """
    skill_lower = skill_text.lower().strip()
    skill_mapping = get_skill_to_category_mapping_duras()
    
    # Buscar coincidencia exacta
    if skill_lower in skill_mapping:
        return skill_mapping[skill_lower]
    
    # Buscar coincidencia parcial
    for skill_key, category in skill_mapping.items():
        if skill_key.lower() in skill_lower or skill_lower in skill_key.lower():
            return category
    
    # Mapeo manual para habilidades comunes no cubiertas
    manual_mappings = {
        'excel': 'habilidades_computacionales_generales',
        'word': 'habilidades_computacionales_generales',
        'powerpoint': 'habilidades_computacionales_generales',
        'python': 'habilidades_computacionales_especificas',
        'java': 'habilidades_computacionales_especificas',
        'javascript': 'habilidades_computacionales_especificas',
        'sql': 'habilidades_computacionales_especificas',
        'react': 'habilidades_computacionales_especificas',
        'angular': 'habilidades_computacionales_especificas',
        'machine learning': 'habilidades_aprendizaje_maquinal_ia',
        'tensorflow': 'habilidades_aprendizaje_maquinal_ia',
        'contabilidad': 'habilidades_financieras',
        'finanzas': 'habilidades_financieras',
        'project management': 'habilidades_administracion_proyectos',
        'scrum': 'habilidades_administracion_proyectos',
        'mysql': 'bases_datos',
        'postgresql': 'bases_datos',
        'mongodb': 'bases_datos'
    }
    
    for manual_skill, manual_category in manual_mappings.items():
        if manual_skill.lower() in skill_lower:
            return manual_category
    
    # Si no se encuentra, retornar categoría por defecto
    return 'general'