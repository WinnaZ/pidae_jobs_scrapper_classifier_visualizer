"""
Diccionario de Escudero et al + sinónimos
========================================

Diccionario base para clasificación de habilidades blandas según el trabajo de Escudero.
Contiene las 4 categorías fijas y sus subcategorías con sinónimos.
"""

DICCIONARIO_ESCUDERO = {
    "title": "Diccionario del trabajo de Escudero et al + sinónimos",
    "categories": {
        "habilidades_de_caracter": {
            "name": "Habilidades de carácter",
            "skills": [
                {
                    "original": "organizado",
                    "sinonimos": ["capacidad organizativa", "estructurado", "sistematizado", "organización"]
                },
                {
                    "original": "detallista",
                    "sinonimos": ["meticuloso","metódico"]
                },
                {
                    "original": "multi tarea",
                    "sinonimos": ["multitasking","versátil","gestión del tiempo","versatilidad"]
                },
                {
                    "original": "puntual",
                    "sinonimos": ["regular", "preciso","diligente","regular","puntualidad"]
                },
                {
                    "original": "enérgico",
                    "sinonimos": ["activo", "dinámico","dinamismo","energía","eficaz","tenaz"]
                },
                {
                    "original": "iniciativa propia",
                    "sinonimos": ["decidido","curiosidad","iniciativa","proactivo"]
                },
                {
                    "original": "motivado",
                    "sinonimos": ["aprendizaje"]
                },
                {
                    "original": "competente",
                    "sinonimos": ["capacitado","cualificado","apto","idóneo","experto","entendido","capaz","preparado","hábil","cumplir objetivos"]
                },
                {
                    "original": "diligente",
                    "sinonimos": ["resuelto","solícito"]
                },
                {
                    "original": "esforzado",
                    "sinonimos": ["dedicado"]
                },
                {
                    "original": "confiable",
                    "sinonimos": ["comprometido"]
                },
                {
                    "original": "resistente estrés",
                    "sinonimos": ["adaptabilidad","resiliencia","trabajo bajo presión","manejo del estrés"]
                },
                {
                    "original": "creativo",
                    "sinonimos": ["innovador"]
                },
                {
                    "original": "independiente",
                    "sinonimos": ["autosuficiente", "autónomo"]
                }
            ]
        },
        "habilidades_sociales": {
            "name": "Habilidades sociales",
            "skills": [
                {
                    "original": "comunicación",
                    "sinonimos": ["comunicativo"]
                },
                {
                    "original": "trabajo equipo",
                    "sinonimos": ["espíritu de equipo"]
                },
                {
                    "original": "colaboración",
                    "sinonimos": ["cooperación", "asistencia", "contribución"]
                },
                {
                    "original": "negociación",
                    "sinonimos": []
                },
                {
                    "original": "persuasión",
                    "sinonimos": ["convencimiento","captar","influenciar","convencer","inducir","atraer","incitar","impulsar"]
                },
                {
                    "original": "escucha",
                    "sinonimos": ["atender", "percibir", "enterar"]
                },
                {
                    "original": "flexibilidad",
                    "sinonimos": ["ductilidad", "maleabilidad", "plasticidad"]
                },
                {
                    "original": "empatía",
                    "sinonimos": []
                },
                {
                    "original": "asertividad",
                    "sinonimos": []
                },
                {
                    "original": "entretener",
                    "sinonimos": ["distraer", "divertir","animar","alegrar", "deleitar"]
                },
                {
                    "original": "enseñar",
                    "sinonimos": ["instruir", "educar","ilustrar", "alfabetizar","explicar","preparar","capacitar","mentoría"]
                },
                {
                    "original": "interacción",
                    "sinonimos": ["relaciones interpersonales"]
                },
                {
                    "original": "habilidades verbales",
                    "sinonimos": []
                }
            ]
        },
        "habilidades_gestion_personal": {
            "name": "Habilidades de gestión de personal",
            "skills": [
                {
                    "original": "supervisión",
                    "sinonimos": ["inspección", "revisión"]
                },
                {
                    "original": "liderazgo",
                    "sinonimos": []
                },
                {
                    "original": "gestión",
                    "sinonimos": ["gestión de equipos","desarrollo de equipos","manejo de equipo"]
                },
                {
                    "original": "staff",
                    "sinonimos": []
                },
                {
                    "original": "supervisión equipo",
                    "sinonimos": []
                },
                {
                    "original": "desarrollo equipo",
                    "sinonimos": []
                },
                {
                    "original": "gestion desempeño",
                    "sinonimos": []
                },
                {
                    "original": "gestión persona",
                    "sinonimos": []
                }
            ]
        },
        "habilidades_servicio_cliente": {
            "name": "Habilidades de servicio al cliente",
            "skills": [
                {
                    "original": "cliente",
                    "sinonimos": ["comprador"]
                },
                {
                    "original": "paciente",
                    "sinonimos": ["tolerante", "comprador","tranquilo","estoico"]
                },
                {
                    "original": "servicio cliente",
                    "sinonimos": ["cierre de ventas","atención al cliente","servicio al cliente"]
                }
            ]
        }
    }
}

# ============================================================================
# FUNCIONES DE CONVENIENCIA PARA ACCEDER AL DICCIONARIO
# ============================================================================

def get_main_categories():
    """Retorna las 4 categorías principales de habilidades blandas"""
    return list(DICCIONARIO_ESCUDERO['categories'].keys())

def get_skills_by_category(category):
    """Retorna las habilidades de una categoría específica"""
    return DICCIONARIO_ESCUDERO['categories'].get(category, {}).get('skills', [])

def get_all_skills():
    """Retorna todas las habilidades de todas las categorías"""
    all_skills = []
    for category_data in DICCIONARIO_ESCUDERO['categories'].values():
        all_skills.extend(category_data['skills'])
    return all_skills

def get_skill_to_category_mapping():
    """Retorna un mapeo de habilidad -> categoría principal"""
    mapping = {}
    for category, category_data in DICCIONARIO_ESCUDERO['categories'].items():
        for skill in category_data['skills']:
            mapping[skill['original']] = category
    return mapping

def get_all_synonyms_for_skill(skill_name):
    """Retorna todos los sinónimos para una habilidad específica"""
    for category_data in DICCIONARIO_ESCUDERO['categories'].values():
        for skill in category_data['skills']:
            if skill['original'] == skill_name:
                return skill['sinonimos']
    return []

def get_category_display_name(category_key):
    """Retorna el nombre para mostrar de una categoría"""
    return DICCIONARIO_ESCUDERO['categories'].get(category_key, {}).get('name', category_key)