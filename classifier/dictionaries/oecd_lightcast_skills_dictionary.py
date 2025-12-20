"""
Diccionario de Habilidades Técnicas basado en OECD + Lightcast
==============================================================

Clasificación de habilidades técnicas basada en:
- Organisation for Economic Co-operation and Development (OECD)
- Lightcast (antes Burning Glass) - "AI skill demand" taxonomy

Divide las habilidades técnicas en dos grandes categorías:
1. AI-Related Skills: Habilidades específicas de Inteligencia Artificial
2. Tech Non-AI Skills: Habilidades tecnológicas que no involucran específicamente IA
"""

DICCIONARIO_OECD_LIGHTCAST = {
    "title": "Diccionario OECD + Lightcast para Habilidades Técnicas",
    "source": "OECD + Lightcast (Burning Glass) AI Skill Demand",
    "version": "1.0",
    "categories": {
        "ai_related_skills": {
            "name": "AI-Related Skills (Habilidades específicas de IA)",
            "description": "Habilidades directamente relacionadas con inteligencia artificial y aprendizaje automático",
            "skills": [
                {"original": "machine learning", "sinonimos": ["aprendizaje automático", "ml"]},
                {"original": "deep learning", "sinonimos": ["aprendizaje profundo", "redes profundas"]},
                {"original": "natural language processing", "sinonimos": ["nlp", "procesamiento lenguaje natural", "procesamiento del lenguaje"]},
                {"original": "computer vision", "sinonimos": ["visión por computador", "visión artificial", "computer vision"]},
                {"original": "reinforcement learning", "sinonimos": ["aprendizaje por refuerzo"]},
                {"original": "neural networks", "sinonimos": ["redes neuronales", "redes de neuronas"]},
                {"original": "convolutional neural networks", "sinonimos": ["cnn", "redes neuronales convolucionales"]},
                {"original": "recurrent neural networks", "sinonimos": ["rnn", "redes neuronales recurrentes"]},
                {"original": "transformers", "sinonimos": ["modelos transformer"]},
                {"original": "feature engineering", "sinonimos": ["ingeniería de características"]},
                {"original": "model deployment", "sinonimos": ["despliegue de modelos", "puesta en producción de modelos", "deployment"]},
                {"original": "prompt engineering", "sinonimos": ["ingeniería de prompts", "prompt design"]},
                {"original": "ai ethics", "sinonimos": ["ética de IA", "ética en inteligencia artificial"]},
                {"original": "ai governance", "sinonimos": ["gobernanza de IA", "goberanza en IA"]},
                {"original": "autonomous systems", "sinonimos": ["sistemas autónomos"]},
                {"original": "autonomous driving", "sinonimos": ["conducción autónoma", "vehículos autónomos"]},
                {"original": "image processing", "sinonimos": ["procesamiento de imágenes", "procesamiento de imagen"]},
                {"original": "robotics ai", "sinonimos": ["robótica con IA", "robótica inteligente"]},
                {"original": "ai systems", "sinonimos": ["sistemas de IA", "sistemas inteligentes"]},
                {"original": "data engineering ai", "sinonimos": ["ingeniería de datos para IA"]},
                {"original": "big data ai", "sinonimos": ["big data para IA", "tecnologías big data aplicadas a IA"]},
                {"original": "tensorflow", "sinonimos": []},
                {"original": "pytorch", "sinonimos": []},
                {"original": "keras", "sinonimos": []},
                {"original": "scikit-learn", "sinonimos": ["sklearn"]},
                {"original": "opencv", "sinonimos": []},
                {"original": "hugging face", "sinonimos": ["huggingface"]},
                {"original": "llama", "sinonimos": []},
                {"original": "gpt", "sinonimos": []},
                {"original": "bert", "sinonimos": []},
                {"original": "computer linguistics", "sinonimos": ["lingüística computacional"]},
            ]
        },
        "tech_non_ai_skills": {
            "name": "Tech Non-AI Skills (Habilidades tecnológicas no-IA)",
            "description": "Habilidades tecnológicas esenciales que no involucran específicamente IA",
            "skills": [
                # Programming Languages
                {"original": "python", "sinonimos": ["python programming"]},
                {"original": "java", "sinonimos": ["java programming"]},
                {"original": "c++", "sinonimos": ["c plus plus", "cpp"]},
                {"original": "c#", "sinonimos": ["csharp", "c sharp"]},
                {"original": "javascript", "sinonimos": ["js", "node.js"]},
                {"original": "typescript", "sinonimos": ["ts"]},
                {"original": "go", "sinonimos": ["golang", "go programming"]},
                {"original": "rust", "sinonimos": []},
                {"original": "php", "sinonimos": []},
                {"original": "ruby", "sinonimos": []},
                {"original": "kotlin", "sinonimos": []},
                {"original": "swift", "sinonimos": []},
                {"original": "scala", "sinonimos": []},
                {"original": "r programming", "sinonimos": ["r language"]},
                
                # Software Development
                {"original": "software development", "sinonimos": ["desarrollo de software", "ingeniería de software"]},
                {"original": "software engineering", "sinonimos": ["ingeniería de software"]},
                {"original": "web development", "sinonimos": ["desarrollo web", "web dev"]},
                {"original": "backend development", "sinonimos": ["desarrollo backend"]},
                {"original": "frontend development", "sinonimos": ["desarrollo frontend"]},
                {"original": "full stack development", "sinonimos": ["full stack"]},
                {"original": "api development", "sinonimos": ["desarrollo de APIs", "api design"]},
                {"original": "microservices", "sinonimos": ["arquitectura de microservicios"]},
                {"original": "rest api", "sinonimos": ["restful api"]},
                {"original": "graphql", "sinonimos": []},
                
                # Data Engineering
                {"original": "data engineering", "sinonimos": ["ingeniería de datos"]},
                {"original": "etl", "sinonimos": ["extract transform load"]},
                {"original": "big data", "sinonimos": ["big data technologies"]},
                {"original": "apache spark", "sinonimos": ["spark", "pyspark"]},
                {"original": "apache hadoop", "sinonimos": ["hadoop"]},
                {"original": "apache kafka", "sinonimos": ["kafka"]},
                {"original": "airflow", "sinonimos": ["apache airflow"]},
                {"original": "data pipelines", "sinonimos": ["tuberías de datos"]},
                
                # Databases
                {"original": "database management", "sinonimos": ["gestión de bases de datos", "administración de bases de datos"]},
                {"original": "sql", "sinonimos": ["sql programming"]},
                {"original": "mysql", "sinonimos": []},
                {"original": "postgresql", "sinonimos": ["postgres"]},
                {"original": "mongodb", "sinonimos": []},
                {"original": "oracle", "sinonimos": []},
                {"original": "sql server", "sinonimos": []},
                {"original": "elasticsearch", "sinonimos": []},
                {"original": "dynamodb", "sinonimos": []},
                {"original": "cassandra", "sinonimos": []},
                {"original": "redis", "sinonimos": []},
                {"original": "nosql", "sinonimos": ["no-sql"]},
                
                # DevOps / CI-CD
                {"original": "devops", "sinonimos": ["devops engineering"]},
                {"original": "ci cd", "sinonimos": ["continuous integration continuous deployment", "cicd"]},
                {"original": "docker", "sinonimos": ["containerization"]},
                {"original": "kubernetes", "sinonimos": ["k8s"]},
                {"original": "jenkins", "sinonimos": []},
                {"original": "gitlab ci", "sinonimos": ["gitlab-ci"]},
                {"original": "github actions", "sinonimos": []},
                {"original": "terraform", "sinonimos": []},
                {"original": "ansible", "sinonimos": []},
                {"original": "infrastructure as code", "sinonimos": ["iac", "infraestructura como código"]},
                
                # Cloud Computing
                {"original": "cloud computing", "sinonimos": ["computación en la nube"]},
                {"original": "aws", "sinonimos": ["amazon web services"]},
                {"original": "azure", "sinonimos": ["microsoft azure"]},
                {"original": "google cloud", "sinonimos": ["gcp", "google cloud platform"]},
                {"original": "aws lambda", "sinonimos": ["lambda"]},
                {"original": "aws ec2", "sinonimos": ["ec2"]},
                {"original": "aws s3", "sinonimos": ["s3"]},
                {"original": "aws rds", "sinonimos": ["rds"]},
                
                # Cybersecurity
                {"original": "cybersecurity", "sinonimos": ["ciberseguridad", "seguridad informática"]},
                {"original": "security", "sinonimos": ["información security", "data security"]},
                {"original": "encryption", "sinonimos": ["cifrado", "encriptación"]},
                {"original": "penetration testing", "sinonimos": ["pen testing"]},
                {"original": "vulnerability assessment", "sinonimos": ["evaluación de vulnerabilidades"]},
                
                # UX/UI Design
                {"original": "ux design", "sinonimos": ["user experience design", "diseño de experiencia de usuario"]},
                {"original": "ui design", "sinonimos": ["user interface design", "diseño de interfaz"]},
                {"original": "figma", "sinonimos": []},
                {"original": "adobe xd", "sinonimos": ["xd"]},
                {"original": "sketch", "sinonimos": []},
                {"original": "prototyping", "sinonimos": ["prototipado"]},
                
                # Mobile Development
                {"original": "mobile app development", "sinonimos": ["desarrollo de aplicaciones móviles"]},
                {"original": "ios development", "sinonimos": ["desarrollo ios"]},
                {"original": "android development", "sinonimos": ["desarrollo android"]},
                {"original": "react native", "sinonimos": []},
                {"original": "flutter", "sinonimos": []},
                
                # Web Frameworks
                {"original": "react", "sinonimos": ["react.js"]},
                {"original": "angular", "sinonimos": ["angularjs"]},
                {"original": "vue", "sinonimos": ["vue.js"]},
                {"original": "django", "sinonimos": []},
                {"original": "flask", "sinonimos": []},
                {"original": "spring", "sinonimos": ["spring framework"]},
                {"original": "express", "sinonimos": ["express.js"]},
                {"original": "asp.net", "sinonimos": ["aspnet"]},
                
                # Data Visualization
                {"original": "data visualization", "sinonimos": ["visualización de datos"]},
                {"original": "tableau", "sinonimos": []},
                {"original": "power bi", "sinonimos": ["powerbi"]},
                {"original": "d3.js", "sinonimos": ["d3"]},
                {"original": "matplotlib", "sinonimos": []},
                {"original": "ggplot", "sinonimos": []},
                
                # Testing / QA
                {"original": "software testing", "sinonimos": ["pruebas de software", "testing"]},
                {"original": "qa", "sinonimos": ["quality assurance", "aseguramiento de calidad"]},
                {"original": "unit testing", "sinonimos": ["pruebas unitarias"]},
                {"original": "integration testing", "sinonimos": ["pruebas de integración"]},
                {"original": "selenium", "sinonimos": []},
                {"original": "junit", "sinonimos": []},
                {"original": "pytest", "sinonimos": []},
                
                # Systems Architecture
                {"original": "systems architecture", "sinonimos": ["arquitectura de sistemas"]},
                {"original": "design patterns", "sinonimos": ["patrones de diseño"]},
                {"original": "system design", "sinonimos": ["diseño de sistemas"]},
                
                # Network Administration
                {"original": "network administration", "sinonimos": ["administración de redes"]},
                {"original": "networking", "sinonimos": ["redes informáticas"]},
                {"original": "tcp ip", "sinonimos": ["tcp/ip"]},
                {"original": "dns", "sinonimos": []},
                {"original": "load balancing", "sinonimos": ["balanceo de carga"]},
                
                # Version Control
                {"original": "git", "sinonimos": []},
                {"original": "github", "sinonimos": []},
                {"original": "gitlab", "sinonimos": []},
                {"original": "bitbucket", "sinonimos": []},
                
                # Office / Productivity
                {"original": "excel", "sinonimos": []},
                {"original": "powerpoint", "sinonimos": []},
                {"original": "word", "sinonimos": []},
                {"original": "office", "sinonimos": ["microsoft office"]},
            ]
        }
    }
}

# ============================================================================
# FUNCIONES DE CONVENIENCIA PARA ACCEDER AL DICCIONARIO OECD-LIGHTCAST
# ============================================================================

def get_main_categories_oecd():
    """Retorna las categorías principales de habilidades técnicas OECD-Lightcast"""
    return list(DICCIONARIO_OECD_LIGHTCAST['categories'].keys())


def get_skills_in_category_oecd(category):
    """Retorna las skills de una categoría específica"""
    return DICCIONARIO_OECD_LIGHTCAST['categories'].get(category, {}).get('skills', [])


def get_all_skills_oecd():
    """Retorna todas las skills del diccionario"""
    all_skills = []
    for category_data in DICCIONARIO_OECD_LIGHTCAST['categories'].values():
        all_skills.extend(category_data.get('skills', []))
    return all_skills


def find_skill_by_original_oecd(skill_name):
    """Busca una skill por su nombre original"""
    skill_lower = skill_name.lower().strip()
    for category, category_data in DICCIONARIO_OECD_LIGHTCAST['categories'].items():
        for skill in category_data.get('skills', []):
            if skill.get('original', '').lower() == skill_lower:
                return {'category': category, 'skill': skill}
    return None


def find_skill_by_synonym_oecd(skill_name):
    """Busca una skill por cualquiera de sus sinónimos"""
    skill_lower = skill_name.lower().strip()
    for category, category_data in DICCIONARIO_OECD_LIGHTCAST['categories'].items():
        for skill in category_data.get('skills', []):
            # Buscar en el nombre original
            if skill.get('original', '').lower() == skill_lower:
                return {'category': category, 'skill': skill}
            # Buscar en sinónimos
            for syn in skill.get('sinonimos', []):
                if syn.lower() == skill_lower:
                    return {'category': category, 'skill': skill}
    return None


def get_category_name_oecd(category_key):
    """Retorna el nombre amigable de una categoría"""
    return DICCIONARIO_OECD_LIGHTCAST['categories'].get(category_key, {}).get('name', category_key)


def find_category_for_skill_oecd(skill_name):
    """
    Encuentra la categoría más probable para una skill usando búsqueda fuzzy
    Retorna la categoría si encuentra coincidencia exacta o parcial
    """
    # Primero intentar coincidencia exacta
    result = find_skill_by_synonym_oecd(skill_name)
    if result:
        return result['category']
    
    # Si no hay coincidencia exacta, buscar por palabras clave
    skill_lower = skill_name.lower()
    keywords_ai = ['machine', 'learning', 'deep', 'neural', 'ai', 'artificial', 'nlp', 'vision', 
                   'reinforcement', 'feature', 'prompt', 'ethics', 'autonomous', 'robotics', 'image processing']
    
    # Contar coincidencias con cada categoría
    ai_matches = sum(1 for kw in keywords_ai if kw in skill_lower)
    
    # Si hay más de una palabra clave de IA, asignar a esa categoría
    if ai_matches >= 1:
        return 'ai_related_skills'
    
    # Por defecto, asignar a habilidades técnicas generales
    return 'tech_non_ai_skills'


if __name__ == "__main__":
    # Test básico
    print("Diccionario OECD+Lightcast cargado correctamente")
    print(f"Categorías principales: {get_main_categories_oecd()}")
    print(f"Total de categorías: {len(DICCIONARIO_OECD_LIGHTCAST['categories'])}")
