"""
Patrones Regex Base para Clasificación de Requisitos de Empleo
=============================================================

Este archivo contiene los patrones regex base estructurados según el esquema de Escudero:
- Habilidades Blandas (subcategorías específicas del diccionario)
- Habilidades Duras 
- Títulos Académicos
- Idiomas

Las categorías de habilidades blandas son fijas y no pueden modificarse:
1. Habilidades de carácter
2. Habilidades sociales  
3. Habilidades de gestión de personal
4. Habilidades de servicio al cliente

IMPORTANTE: Los patrones usan \b para word boundaries y re.IGNORECASE
"""

import re
from classifier.dictionaries.escudero_blandas_dictionary import (
    DICCIONARIO_ESCUDERO,
    get_skills_by_category as get_escudero_skills_by_category,
    get_skill_to_category_mapping
)
from classifier.dictionaries.oecd_lightcast_skills_dictionary import (
    DICCIONARIO_OECD_LIGHTCAST,
    get_all_skills_oecd,
    find_category_for_skill_oecd
)

# ============================================================================
# CARGAR DICCIONARIOS PARA MAPEO DE CATEGORÍAS
# ============================================================================

# Cargar diccionarios al importar el módulo
ESCUDERO_DICT = DICCIONARIO_ESCUDERO
OECD_DICT = DICCIONARIO_OECD_LIGHTCAST

# Mapeo de subcategorías a categorías principales usando el diccionario de Escudero
SUBCATEGORY_TO_MAIN_CATEGORY = get_skill_to_category_mapping()# ============================================================================
# PATRONES BASE PARA HABILIDADES BLANDAS (4 CATEGORÍAS FIJAS)
# ============================================================================

# ============================================================================
# PATRONES BASE PARA HABILIDADES BLANDAS (USANDO SUBCATEGORÍAS ESPECÍFICAS)
# ============================================================================
# Los patrones usan las subcategorías específicas del diccionario de Escudero
# Luego se mapean a las 4 categorías principales usando el diccionario

HABILIDADES_BLANDAS_PATTERNS = {
    # === HABILIDADES DE CARÁCTER ===
    'organizado': [
        (r'\b(organizado|capacidad\s+organizativa|estructurado|sistematizado|organizacion)\b', 'organizado'),
    ],
    'detallista': [
        (r'\b(detallista|meticuloso|metodico)\b', 'detallista'),
    ],
    'multi tarea': [
        (r'\b(multi\s*tarea|multitasking|versatil|gestion\s+del\s+tiempo|versatilidad)\b', 'multi tarea'),
    ],
    'puntual': [
        (r'\b(puntual|regular|preciso|diligente|puntualidad)\b', 'puntual'),
    ],
    'energico': [
        (r'\b(energico|activo|dinamico|dinamismo|energia|eficaz|tenaz)\b', 'energico'),
    ],
    'iniciativa propia': [
        (r'\b(iniciativa\s+propia|decidido|curiosidad|iniciativa|proactivo)\b', 'iniciativa propia'),
    ],
    'motivado': [
        (r'\b(motivado|aprendizaje)\b', 'motivado'),
    ],
    'competente': [
        (r'\b(competente|capacitado|cualificado|apto|idoneo|experto|entendido|capaz|preparado|habil|cumplir\s+objetivos)\b', 'competente'),
    ],
    'diligente': [
        (r'\b(diligente|resuelto|solicito)\b', 'diligente'),
    ],
    'esforzado': [
        (r'\b(esforzado|dedicado)\b', 'esforzado'),
    ],
    'confiable': [
        (r'\b(confiable|comprometido)\b', 'confiable'),
    ],
    'resistente estres': [
        (r'\b(resistente\s+estres|adaptabilidad|resiliencia|trabajo\s+bajo\s+presion|manejo\s+del\s+estres)\b', 'resistente estres'),
    ],
    'creativo': [
        (r'\b(creativo|innovador)\b', 'creativo'),
    ],
    'independiente': [
        (r'\b(independiente|autosuficiente|autonomo)\b', 'independiente'),
    ],

    # === HABILIDADES SOCIALES ===
    'comunicacion': [
        (r'\b(comunicacion|comunicativo)\b', 'comunicacion'),
    ],
    'trabajo equipo': [
        (r'\b(trabajo\s+equipo|espiritu\s+de\s+equipo)\b', 'trabajo equipo'),
    ],
    'colaboracion': [
        (r'\b(colaboracion|cooperacion|asistencia|contribucion)\b', 'colaboracion'),
    ],
    'negociacion': [
        (r'\b(negociacion)\b', 'negociacion'),
    ],
    'persuasion': [
        (r'\b(persuasion|convencimiento|captar|influenciar|convencer|inducir|atraer|incitar|impulsar)\b', 'persuasion'),
    ],
    'escucha': [
        (r'\b(escucha|atender|percibir|enterar)\b', 'escucha'),
    ],
    'flexibilidad': [
        (r'\b(flexibilidad|ductilidad|maleabilidad|plasticidad)\b', 'flexibilidad'),
    ],
    'empatia': [
        (r'\b(empatia)\b', 'empatia'),
    ],
    'asertividad': [
        (r'\b(asertividad)\b', 'asertividad'),
    ],
    'entretener': [
        (r'\b(entretener|distraer|divertir|animar|alegrar|deleitar)\b', 'entretener'),
    ],
    'ensenar': [
        (r'\b(ensenar|instruir|educar|ilustrar|alfabetizar|explicar|preparar|capacitar|mentoria)\b', 'ensenar'),
    ],
    'interaccion': [
        (r'\b(interaccion|relaciones\s+interpersonales)\b', 'interaccion'),
    ],

    'habilidades verbales': [
        (r'\b(habilidades\s+verbales)\b', 'habilidades verbales'),
    ],
    # === GESTIÓN DE PERSONAL ===
    'supervision': [
        (r'\b(supervision|inspeccion|revision)\b', 'supervision'),
    ],
    'liderazgo': [
        (r'\b(liderazgo)\b', 'liderazgo'),
    ],
    'gestion': [
        (r'\b(gestion|gestion\s+de\s+equipos|desarrollo\s+de\s+equipos|manejo\s+de\s+equipo)\b', 'gestion'),
    ],
    'staff': [
        (r'\b(staff)\b', 'staff'),
    ],
    'supervision equipo': [
        (r'\b(supervision\s+equipo)\b', 'supervision equipo'),
    ],
    'desarrollo equipo': [
        (r'\b(desarrollo\s+equipo)\b', 'desarrollo equipo'),
    ],
    'gestion desempeno': [
        (r'\b(gestion\s+desempeno)\b', 'gestion desempeno'),
    ],
    'gestion persona': [
        (r'\b(gestion\s+persona)\b', 'gestion persona'),
    ],
    # === SERVICIO AL CLIENTE ===
    'cliente': [
        (r'\b(cliente|comprador)\b', 'cliente'),
    ],
    'paciente': [
        (r'\b(paciente|tolerante|tranquilo|estoico)\b', 'paciente'),
    ],
    'servicio cliente': [
        (r'\b(servicio\s+cliente|cierre\s+de\s+ventas|atencion\s+al\s+cliente|servicio\s+al\s+cliente)\b', 'servicio cliente'),
    ],
}

# ============================================================================
# PATRONES BASE PARA HABILIDADES DURAS (BASADOS EN OECD+LIGHTCAST)
# ============================================================================

HABILIDADES_DURAS_PATTERNS = {
    'ai_related_skills': [
        (r'\b(machine\s+learning|aprendizaje\s+autom[aá]tico|ml)\b', 'AI-Related Skills'),
        (r'\b(deep\s+learning|aprendizaje\s+profundo|redes\s+profundas)\b', 'AI-Related Skills'),
        (r'\b(natural\s+language\s+processing|nlp|procesamiento\s+lenguaje\s+natural|procesamiento\s+del\s+lenguaje)\b', 'AI-Related Skills'),
        (r'\b(computer\s+vision|visi[oó]n\s+por\s+computador|visi[oó]n\s+artificial)\b', 'AI-Related Skills'),
        (r'\b(reinforcement\s+learning|aprendizaje\s+por\s+refuerzo)\b', 'AI-Related Skills'),
        (r'\b(neural\s+networks|redes\s+neuronales|redes\s+de\s+neuronas)\b', 'AI-Related Skills'),
        (r'\b(convolutional\s+neural\s+networks|cnn|redes\s+neuronales\s+convolucionales)\b', 'AI-Related Skills'),
        (r'\b(recurrent\s+neural\s+networks|rnn|redes\s+neuronales\s+recurrentes)\b', 'AI-Related Skills'),
        (r'\b(transformers|modelos\s+transformer)\b', 'AI-Related Skills'),
        (r'\b(feature\s+engineering|ingenier[ií]a\s+de\s+caracter[ií]sticas)\b', 'AI-Related Skills'),
        (r'\b(model\s+deployment|despliegue\s+de\s+modelos|puesta\s+en\s+producci[oó]n\s+de\s+modelos|deployment)\b', 'AI-Related Skills'),
        (r'\b(prompt\s+engineering|ingenier[ií]a\s+de\s+prompts|prompt\s+design)\b', 'AI-Related Skills'),
        (r'\b(ai\s+ethics|[eé]tica\s+de\s+ia|[eé]tica\s+en\s+inteligencia\s+artificial)\b', 'AI-Related Skills'),
        (r'\b(ai\s+governance|gobernanza\s+de\s+ia|goberanza\s+en\s+ia)\b', 'AI-Related Skills'),
        (r'\b(autonomous\s+systems|sistemas\s+aut[oó]nomos)\b', 'AI-Related Skills'),
        (r'\b(autonomous\s+driving|conducci[oó]n\s+aut[oó]noma|veh[ií]culos\s+aut[oó]nomos)\b', 'AI-Related Skills'),
        (r'\b(image\s+processing|procesamiento\s+de\s+im[aá]genes|procesamiento\s+de\s+imagen)\b', 'AI-Related Skills'),
        (r'\b(robotics\s+ai|rob[oó]tica\s+con\s+ia|rob[oó]tica\s+inteligente)\b', 'AI-Related Skills'),
        (r'\b(ai\s+systems|sistemas\s+de\s+ia|sistemas\s+inteligentes)\b', 'AI-Related Skills'),
        (r'\b(data\s+engineering\s+ai|ingenier[ií]a\s+de\s+datos\s+para\s+ia)\b', 'AI-Related Skills'),
        (r'\b(big\s+data\s+ai|big\s+data\s+para\s+ia|tecnolog[ií]as\s+big\s+data\s+aplicadas\s+a\s+ia)\b', 'AI-Related Skills'),
        (r'\b(tensorflow)\b', 'AI-Related Skills'),
        (r'\b(pytorch)\b', 'AI-Related Skills'),
        (r'\b(keras)\b', 'AI-Related Skills'),
        (r'\b(scikit-learn|sklearn)\b', 'AI-Related Skills'),
        (r'\b(opencv)\b', 'AI-Related Skills'),
        (r'\b(hugging\s+face|huggingface)\b', 'AI-Related Skills'),
        (r'\b(llama)\b', 'AI-Related Skills'),
        (r'\b(gpt)\b', 'AI-Related Skills'),
        (r'\b(bert)\b', 'AI-Related Skills'),
        (r'\b(computer\s+linguistics|ling[üu][ií]stica\s+computacional)\b', 'AI-Related Skills'),
    ],
    
    'tech_non_ai_skills': [
        # Programming Languages
        (r'\b(python|python\s+programming)\b', 'Tech Non-AI Skills'),
        (r'\b(java|java\s+programming)\b', 'Tech Non-AI Skills'),
        (r'\b(c\+\+|c\s+plus\s+plus|cpp)\b', 'Tech Non-AI Skills'),
        (r'\b(c#|csharp|c\s+sharp)\b', 'Tech Non-AI Skills'),
        (r'\b(javascript|js|node\.js)\b', 'Tech Non-AI Skills'),
        (r'\b(typescript|ts)\b', 'Tech Non-AI Skills'),
        (r'\b(go|golang|go\s+programming)\b', 'Tech Non-AI Skills'),
        (r'\b(rust)\b', 'Tech Non-AI Skills'),
        (r'\b(php)\b', 'Tech Non-AI Skills'),
        (r'\b(ruby)\b', 'Tech Non-AI Skills'),
        (r'\b(kotlin)\b', 'Tech Non-AI Skills'),
        (r'\b(swift)\b', 'Tech Non-AI Skills'),
        (r'\b(scala)\b', 'Tech Non-AI Skills'),
        (r'\b(r\s+programming|r\s+language)\b', 'Tech Non-AI Skills'),
        
        # Software Development
        (r'\b(software\s+development|desarrollo\s+de\s+software|ingenier[ií]a\s+de\s+software)\b', 'Tech Non-AI Skills'),
        (r'\b(software\s+engineering|ingenier[ií]a\s+de\s+software)\b', 'Tech Non-AI Skills'),
        (r'\b(web\s+development|desarrollo\s+web|web\s+dev)\b', 'Tech Non-AI Skills'),
        (r'\b(backend\s+development|desarrollo\s+backend)\b', 'Tech Non-AI Skills'),
        (r'\b(frontend\s+development|desarrollo\s+frontend)\b', 'Tech Non-AI Skills'),
        (r'\b(full\s+stack\s+development|full\s+stack)\b', 'Tech Non-AI Skills'),
        (r'\b(api\s+development|desarrollo\s+de\s+apis|api\s+design)\b', 'Tech Non-AI Skills'),
        (r'\b(microservices|arquitectura\s+de\s+microservicios)\b', 'Tech Non-AI Skills'),
        (r'\b(rest\s+api|restful\s+api)\b', 'Tech Non-AI Skills'),
        (r'\b(graphql)\b', 'Tech Non-AI Skills'),
        
        # Data Engineering
        (r'\b(data\s+engineering|ingenier[ií]a\s+de\s+datos)\b', 'Tech Non-AI Skills'),
        (r'\b(etl|extract\s+transform\s+load)\b', 'Tech Non-AI Skills'),
        (r'\b(big\s+data|big\s+data\s+technologies)\b', 'Tech Non-AI Skills'),
        (r'\b(apache\s+spark|spark|pyspark)\b', 'Tech Non-AI Skills'),
        (r'\b(apache\s+hadoop|hadoop)\b', 'Tech Non-AI Skills'),
        (r'\b(apache\s+kafka|kafka)\b', 'Tech Non-AI Skills'),
        (r'\b(airflow|apache\s+airflow)\b', 'Tech Non-AI Skills'),
        (r'\b(data\s+pipelines|tuber[ií]as\s+de\s+datos)\b', 'Tech Non-AI Skills'),
        
        # Databases
        (r'\b(database\s+management|gesti[oó]n\s+de\s+bases\s+de\s+datos|administraci[oó]n\s+de\s+bases\s+de\s+datos)\b', 'Tech Non-AI Skills'),
        (r'\b(sql|sql\s+programming)\b', 'Tech Non-AI Skills'),
        (r'\b(mysql)\b', 'Tech Non-AI Skills'),
        (r'\b(postgresql|postgres)\b', 'Tech Non-AI Skills'),
        (r'\b(mongodb)\b', 'Tech Non-AI Skills'),
        (r'\b(oracle)\b', 'Tech Non-AI Skills'),
        (r'\b(sql\s+server)\b', 'Tech Non-AI Skills'),
        (r'\b(elasticsearch)\b', 'Tech Non-AI Skills'),
        (r'\b(dynamodb)\b', 'Tech Non-AI Skills'),
        (r'\b(cassandra)\b', 'Tech Non-AI Skills'),
        (r'\b(redis)\b', 'Tech Non-AI Skills'),
        (r'\b(nosql|no-sql)\b', 'Tech Non-AI Skills'),
        
        # DevOps / CI-CD
        (r'\b(devops|devops\s+engineering)\b', 'Tech Non-AI Skills'),
        (r'\b(ci\s+cd|continuous\s+integration\s+continuous\s+deployment|cicd)\b', 'Tech Non-AI Skills'),
        (r'\b(docker|containerization)\b', 'Tech Non-AI Skills'),
        (r'\b(kubernetes|k8s)\b', 'Tech Non-AI Skills'),
        (r'\b(jenkins)\b', 'Tech Non-AI Skills'),
        (r'\b(gitlab\s+ci|gitlab-ci)\b', 'Tech Non-AI Skills'),
        (r'\b(github\s+actions)\b', 'Tech Non-AI Skills'),
        (r'\b(terraform)\b', 'Tech Non-AI Skills'),
        (r'\b(ansible)\b', 'Tech Non-AI Skills'),
        (r'\b(infrastructure\s+as\s+code|iac|infraestructura\s+como\s+c[oó]digo)\b', 'Tech Non-AI Skills'),
        
        # Cloud Computing
        (r'\b(cloud\s+computing|computaci[oó]n\s+en\s+la\s+nube)\b', 'Tech Non-AI Skills'),
        (r'\b(aws|amazon\s+web\s+services)\b', 'Tech Non-AI Skills'),
        (r'\b(azure|microsoft\s+azure)\b', 'Tech Non-AI Skills'),
        (r'\b(google\s+cloud|gcp|google\s+cloud\s+platform)\b', 'Tech Non-AI Skills'),
        (r'\b(aws\s+lambda|lambda)\b', 'Tech Non-AI Skills'),
        (r'\b(aws\s+ec2|ec2)\b', 'Tech Non-AI Skills'),
        (r'\b(aws\s+s3|s3)\b', 'Tech Non-AI Skills'),
        (r'\b(aws\s+rds|rds)\b', 'Tech Non-AI Skills'),
        
        # Cybersecurity
        (r'\b(cybersecurity|ciberseguridad|seguridad\s+inform[aá]tica)\b', 'Tech Non-AI Skills'),
        (r'\b(security|información\s+security|data\s+security)\b', 'Tech Non-AI Skills'),
        (r'\b(encryption|cifrado|encriptaci[oó]n)\b', 'Tech Non-AI Skills'),
        (r'\b(penetration\s+testing|pen\s+testing)\b', 'Tech Non-AI Skills'),
        (r'\b(vulnerability\s+assessment|evaluaci[oó]n\s+de\s+vulnerabilidades)\b', 'Tech Non-AI Skills'),
        
        # UX/UI Design
        (r'\b(ux\s+design|user\s+experience\s+design|dise[ñn]o\s+de\s+experiencia\s+de\s+usuario)\b', 'Tech Non-AI Skills'),
        (r'\b(ui\s+design|user\s+interface\s+design|dise[ñn]o\s+de\s+interfaz)\b', 'Tech Non-AI Skills'),
        (r'\b(figma)\b', 'Tech Non-AI Skills'),
        (r'\b(adobe\s+xd|xd)\b', 'Tech Non-AI Skills'),
        (r'\b(sketch)\b', 'Tech Non-AI Skills'),
        (r'\b(prototyping|prototipado)\b', 'Tech Non-AI Skills'),
        
        # Mobile Development
        (r'\b(mobile\s+app\s+development|desarrollo\s+de\s+aplicaciones\s+m[oó]viles)\b', 'Tech Non-AI Skills'),
        (r'\b(ios\s+development|desarrollo\s+ios)\b', 'Tech Non-AI Skills'),
        (r'\b(android\s+development|desarrollo\s+android)\b', 'Tech Non-AI Skills'),
        (r'\b(react\s+native)\b', 'Tech Non-AI Skills'),
        (r'\b(flutter)\b', 'Tech Non-AI Skills'),
        
        # Web Frameworks
        (r'\b(react|react\.js)\b', 'Tech Non-AI Skills'),
        (r'\b(angular|angularjs)\b', 'Tech Non-AI Skills'),
        (r'\b(vue|vue\.js)\b', 'Tech Non-AI Skills'),
        (r'\b(django)\b', 'Tech Non-AI Skills'),
        (r'\b(flask)\b', 'Tech Non-AI Skills'),
        (r'\b(spring|spring\s+framework)\b', 'Tech Non-AI Skills'),
        (r'\b(express|express\.js)\b', 'Tech Non-AI Skills'),
        (r'\b(asp\.net|aspnet)\b', 'Tech Non-AI Skills'),
        
        # Data Visualization
        (r'\b(data\s+visualization|visualizaci[oó]n\s+de\s+datos)\b', 'Tech Non-AI Skills'),
        (r'\b(tableau)\b', 'Tech Non-AI Skills'),
        (r'\b(power\s+bi|powerbi)\b', 'Tech Non-AI Skills'),
        (r'\b(d3\.js|d3)\b', 'Tech Non-AI Skills'),
        (r'\b(matplotlib)\b', 'Tech Non-AI Skills'),
        (r'\b(ggplot)\b', 'Tech Non-AI Skills'),
        
        # Testing / QA
        (r'\b(software\s+testing|pruebas\s+de\s+software|testing)\b', 'Tech Non-AI Skills'),
        (r'\b(qa|quality\s+assurance|aseguramiento\s+de\s+calidad)\b', 'Tech Non-AI Skills'),
        (r'\b(unit\s+testing|pruebas\s+unitarias)\b', 'Tech Non-AI Skills'),
        (r'\b(integration\s+testing|pruebas\s+de\s+integraci[oó]n)\b', 'Tech Non-AI Skills'),
        (r'\b(selenium)\b', 'Tech Non-AI Skills'),
        (r'\b(junit)\b', 'Tech Non-AI Skills'),
        (r'\b(pytest)\b', 'Tech Non-AI Skills'),
        
        # Systems Architecture
        (r'\b(systems\s+architecture|arquitectura\s+de\s+sistemas)\b', 'Tech Non-AI Skills'),
        (r'\b(design\s+patterns|patrones\s+de\s+dise[ñn]o)\b', 'Tech Non-AI Skills'),
        (r'\b(system\s+design|dise[ñn]o\s+de\s+sistemas)\b', 'Tech Non-AI Skills'),
        
        # Network Administration
        (r'\b(network\s+administration|administraci[oó]n\s+de\s+redes)\b', 'Tech Non-AI Skills'),
        (r'\b(networking|redes\s+inform[aá]ticas)\b', 'Tech Non-AI Skills'),
        (r'\b(tcp\s+ip|tcp/ip)\b', 'Tech Non-AI Skills'),
        (r'\b(dns)\b', 'Tech Non-AI Skills'),
        (r'\b(load\s+balancing|balanceo\s+de\s+carga)\b', 'Tech Non-AI Skills'),
        
        # Version Control
        (r'\b(git)\b', 'Tech Non-AI Skills'),
        (r'\b(github)\b', 'Tech Non-AI Skills'),
        (r'\b(gitlab)\b', 'Tech Non-AI Skills'),
        (r'\b(bitbucket)\b', 'Tech Non-AI Skills'),
        
        # Office / Productivity
        (r'\b(excel)\b', 'Tech Non-AI Skills'),
        (r'\b(powerpoint)\b', 'Tech Non-AI Skills'),
        (r'\b(word)\b', 'Tech Non-AI Skills'),
        (r'\b(office|microsoft\s+office)\b', 'Tech Non-AI Skills'),
    ]
}

# ============================================================================
# PATRONES BASE PARA TÍTULOS ACADÉMICOS
# ============================================================================

TITULOS_PATTERNS = [
    (r'\b(ingeniero|ingenier[ií]a)\s+(en\s+)?([a-záéíóúñ\s]+)?\b', 'Títulos Académicos'),
    (r'\b(licenciado|licenciatura)\s+(en\s+)?([a-záéíóúñ\s]+)?\b', 'Títulos Académicos'),
    (r'\b(t[ée]cnico|tecnicatura)\s+(en\s+)?([a-záéíóúñ\s]+)?\b', 'Títulos Académicos'),
    (r'\b(analista)\s+(de\s+)?([a-záéíóúñ\s]+)?\b', 'Títulos Académicos'),
    (r'\b(programador|desarrollador)\s+(de\s+)?([a-záéíóúñ\s]+)?\b', 'Títulos Académicos'),
    (r'\b(bachiller)\b', 'Títulos Académicos'),
    (r'\b(universitario|estudios?\s*universitarios?)\b', 'Títulos Académicos'),
    (r'\b(maestr[ií]a|m[aá]ster|master)\b', 'Títulos Académicos'),
    (r'\b(doctorado|phd|ph\.d)\b', 'Títulos Académicos'),
]

# ============================================================================
# PATRONES BASE PARA IDIOMAS
# ============================================================================

IDIOMAS_PATTERNS = [
    (r'\b(ingl[ée]s|ingles|english)\s*(avanzado|intermedio|b[aá]sico|nativo|fluido|conversacional|bilingüe|a1|a2|b1|b2|c1|c2)?\b', 'Idiomas'),
    (r'\b(portugu[ée]s|portugues|portuguese)\s*(avanzado|intermedio|b[aá]sico|nativo|fluido|conversacional|bilingüe)?\b', 'Idiomas'),
    (r'\b(franc[ée]s|frances|french|fran[cç]ais)\s*(avanzado|intermedio|b[aá]sico|nativo|fluido|conversacional|bilingüe)?\b', 'Idiomas'),
    (r'\b(alem[aá]n|aleman|german|deutsch)\s*(avanzado|intermedio|b[aá]sico|nativo|fluido|conversacional|bilingüe)?\b', 'Idiomas'),
    (r'\b(italiano|italian)\s*(avanzado|intermedio|b[aá]sico|nativo|fluido|conversacional|bilingüe)?\b', 'Idiomas'),
    (r'\b(chino|mandar[ií]n|mandarin|chinese)\s*(avanzado|intermedio|b[aá]sico|nativo|fluido|conversacional|bilingüe)?\b', 'Idiomas'),
    (r'\b(japon[ée]s|japones|japanese)\s*(avanzado|intermedio|b[aá]sico|nativo|fluido|conversacional|bilingüe)?\b', 'Idiomas'),
    (r'\b(espa[ñn]ol|spanish|castellano)\s*(avanzado|intermedio|b[aá]sico|nativo|fluido|conversacional|bilingüe)?\b', 'Idiomas'),
    (r'\b(ruso|russian)\s*(avanzado|intermedio|b[aá]sico|nativo|fluido|conversacional|bilingüe)?\b', 'Idiomas'),
    (r'\b([aá]rabe|arabic)\s*(avanzado|intermedio|b[aá]sico|nativo|fluido|conversacional|bilingüe)?\b', 'Idiomas'),
    (r'\b(coreano|korean)\s*(avanzado|intermedio|b[aá]sico|nativo|fluido|conversacional|bilingüe)?\b', 'Idiomas'),
]

# ============================================================================
# FUNCIONES PARA OBTENER TODOS LOS PATRONES BASE
# ============================================================================

def get_escudero_category_mapping():
    """
    Retorna el mapeo de subcategorías específicas a las 4 categorías principales de Escudero
    usando el diccionario importado dinámicamente
    
    Returns:
        dict: Mapeo de subcategoria -> categoria_principal
    """
    return SUBCATEGORY_TO_MAIN_CATEGORY

def get_all_base_patterns():
    """
    Retorna todos los patrones base organizados por las 4 áreas principales
    
    Returns:
        dict: Diccionario con estructura: {
            'habilidades_blandas': {...},
            'habilidades_duras': {...}, 
            'titulos': [...],
            'idiomas': [...]
        }
    """
    return {
        'habilidades_blandas': HABILIDADES_BLANDAS_PATTERNS,
        'habilidades_duras': HABILIDADES_DURAS_PATTERNS,
        'titulos': TITULOS_PATTERNS,
        'idiomas': IDIOMAS_PATTERNS
    }

def compile_base_patterns():
    """
    Compila todos los patrones base en objetos regex
    
    Returns:
        dict: Patrones compilados con la misma estructura
    """
    base_patterns = get_all_base_patterns()
    compiled = {}
    
    for area, patterns in base_patterns.items():
        if area in ['habilidades_blandas', 'habilidades_duras']:
            compiled[area] = {}
            for category, pattern_list in patterns.items():
                compiled[area][category] = []
                for pattern_str, label in pattern_list:
                    try:
                        compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                        compiled[area][category].append((compiled_pattern, label))
                    except re.error as e:
                        print(f"Error compilando patrón base '{pattern_str}': {e}")
        else:
            # Para títulos e idiomas
            compiled[area] = []
            for pattern_str, label in patterns:
                try:
                    compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                    compiled[area].append((compiled_pattern, label))
                except re.error as e:
                    print(f"Error compilando patrón base '{pattern_str}': {e}")
    
    return compiled

def get_categories_info():
    """
    Retorna información sobre las categorías del sistema
    
    Returns:
        dict: Información sobre categorías por área
    """
    return {
        'areas': ['habilidades_blandas', 'habilidades_duras', 'titulos', 'idiomas'],
        'habilidades_blandas': {
            'categorias_fijas': [
                'habilidades_de_caracter',
                'habilidades_sociales', 
                'habilidades_gestion_personal',
                'habilidades_servicio_cliente'
            ],
            'nombres_categorias': {
                'habilidades_de_caracter': 'Habilidades de carácter',
                'habilidades_sociales': 'Habilidades sociales',
                'habilidades_gestion_personal': 'Habilidades de gestión de personal',
                'habilidades_servicio_cliente': 'Habilidades de servicio al cliente'
            }
        },
        'habilidades_duras': {
            'categorias_principales': list(OECD_DICT.get('categories', {}).keys())
        }
    }