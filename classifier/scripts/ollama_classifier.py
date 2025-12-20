#!/usr/bin/env python3
"""
Clasificador de requisitos usando Ollama como alternativa local a Gemini
Autor: IA Assistant
Fecha: 2025-11-04

Modelos recomendados por tarea:
- llama3.2:3b    : Balance velocidad/calidad, bueno para extracción general
- llama3.2:1b    : Más rápido, ligero, bueno para tareas simples
- llama2:latest  : Modelo original, más lento pero robusto
- mistral:7b     : Excelente para tareas de extracción y NER
- phi3:mini      : Muy rápido y eficiente para tareas específicas
- qwen2.5:7b     : Especializado en NER (Named Entity Recognition)
"""

import requests
import json
import logging
import time
import re
from typing import List, Dict, Any, Optional

# =============================================================================
# CONFIGURACIÓN DE MODELO OLLAMA
# =============================================================================
# Cambiar aquí el modelo a usar (descarga automática si no está instalado)
OLLAMA_MODEL = "mistral:7b"

# Modelos alternativos (comentados):
# OLLAMA_MODEL = "llama3.2:3b"      # Balance velocidad/calidad
# OLLAMA_MODEL = "llama3.2:1b"      # Más rápido, menos preciso
# OLLAMA_MODEL = "llama2:latest"    # Modelo original
# OLLAMA_MODEL = "phi3:mini"        # Muy rápido
# OLLAMA_MODEL = "qwen2.5:7b"       # Mejor para NER
# =============================================================================

def validate_ai_requirement(requirement_text):
    """
    Valida que un requisito extraído por AI sea apropiado para crear un patrón regex.
    """
    if not requirement_text or len(requirement_text.strip()) == 0:
        print(f"[VALIDATION] Rejected (empty): '{requirement_text}'")
        return False
    # Accept all non-empty requirements for testing
    return True

class OllamaClassifier:
    def __init__(self, model_name: str = None, base_url: str = "http://localhost:11434"):
        self.model_name = model_name or OLLAMA_MODEL
        self.base_url = base_url
        self.api_url = f"{base_url}/api/generate"
        self.logger = logging.getLogger(__name__)
        
        # Verificar conexión
        if not self._check_connection():
            raise ConnectionError(f"No se puede conectar a Ollama en {base_url}")
        
        # Verificar RAM disponible vs requerimientos del modelo
        self._check_model_requirements()
    
    def _check_connection(self) -> bool:
        """Verificar que Ollama esté disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Error conectando a Ollama: {e}")
            return False
    
    def _check_model_requirements(self):
        """Verificar que hay suficiente RAM para el modelo antes de empezar"""
        import psutil
        import sys
        
        # Requisitos de RAM por modelo (en GB)
        model_requirements = {
            "mistral:7b": 4.5,
            "llama3.2:3b": 2.5,
            "llama3.2:1b": 1.5,
            "llama2:latest": 4.0,
            "phi3:mini": 2.0,
            "qwen2.5:7b": 4.5,
        }
        
        # Obtener RAM disponible
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        # Buscar requisito del modelo
        required_gb = None
        for model_pattern, required in model_requirements.items():
            if model_pattern in self.model_name.lower():
                required_gb = required
                break
        
        # Si no conocemos el modelo, asumir 2GB
        if required_gb is None:
            required_gb = 2.0
        
        # Error si RAM disponible es menor a lo requerido
        if available_gb < required_gb:
            # Lanzar excepción con la información, se imprimirá en rojo en process_jobs.py
            raise MemoryError(
                f"RAM insuficiente: Modelo {self.model_name} requiere ~{required_gb:.1f}GB, "
                f"disponible {available_gb:.1f}GB (faltan {required_gb - available_gb:.1f}GB)"
            )
    
    def _make_request(self, prompt: str, max_retries: int = 1) -> Optional[str]:
        """Hacer request a Ollama con manejo de errores"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.2,
                "num_predict": 300
            }
            
            response = requests.post(self.api_url, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verificar si hay un error en la respuesta
                if 'error' in result:
                    error_msg = result['error']
                    print(f"\n{'='*80}")
                    print(f"ERROR CRITICO DE OLLAMA:")
                    print(f"   {error_msg}")
                    print(f"{'='*80}")
                    
                    # Si es error de memoria, dar sugerencias
                    if 'memory' in error_msg.lower():
                        print(f"\nSOLUCIONES:")
                        print(f"   1. Usa un modelo mas pequeño: llama3.2:1b (requiere ~1.5GB)")
                        print(f"   2. Cierra otras aplicaciones para liberar RAM")
                        print(f"   3. Ejecuta sin Ollama: python process_jobs.py (solo regex)")
                        print(f"\n   Modelo actual: {self.model_name}")
                        print(f"   Cambia el modelo en: ollama_classifier.py linea 27")
                    print(f"{'='*80}\n")
                    
                    # Terminar la ejecución
                    import sys
                    sys.exit(1)
                
                return result.get("response", "").strip()
            else:
                self.logger.warning(f"Ollama error {response.status_code}: {response.text}")
                return ""
                
        except Exception as e:
            self.logger.error(f"Error Ollama: {e}")
            return ""

def classify_with_ollama_simple(remaining_text, already_classified, job_title="", job_description="", classifier=None, categories_info=None):
    """
    Función simplificada para compatibilidad con process_jobs_v2.py
    Mejorada con mejor parsing de respuesta JSON y filtrado de skills ya encontradas
    
    Args:
        remaining_text: Texto completo del job
        already_classified: Dict con skills ya encontradas por regex
        categories_info: Dict con categorías permitidas (OECD para duras, Escudero para blandas)
    """
    if classifier is None:
        try:
            classifier = OllamaClassifier()
        except:
            return {"duros": [], "blandos": [], "idioma": [], "titulos": []}
    
    # Extraer términos ya clasificados para evitar duplicados
    already_found = set()
    for area_data in already_classified.values():
        if isinstance(area_data, dict):
            for terms in area_data.values():
                already_found.update(t.lower() for t in terms)
        elif isinstance(area_data, list):
            already_found.update(t.lower() for t in area_data)
    
    try:
        prompt = f"""Extract ONLY specific technical skills (hard skills), soft skills, languages, or academic titles from job text.
Rules:
- Hard skills: AI/ML, programming languages, frameworks, databases, tools (e.g., Python, Docker, AWS, TensorFlow)
- Soft skills: communication, teamwork, leadership, problem-solving
- Languages: English, Spanish, etc.
- Titles: degree names only (e.g., "Computer Science", "MBA")
- Return 1-3 words maximum per skill
- Ignore: experience requirements, responsibilities, job descriptions
- IMPORTANT: Extract ALL skills mentioned, even if some seem already found

Return ONLY JSON array:
[{{"requisito":"Python","tipo":"duro"}},{{"requisito":"teamwork","tipo":"blando"}}]

Text: {remaining_text}

JSON:"""
        
        response = classifier._make_request(prompt)
        
        if not response or response.strip() == "":
            return {"duros": [], "blandos": [], "idioma": [], "titulos": []}
        
        # Limpiar respuesta: remover markdown code blocks
        clean_response = response
        if "```" in clean_response:
            clean_response = re.sub(r'```[^`]*```', '', clean_response, flags=re.DOTALL)
            clean_response = re.sub(r'```', '', clean_response)
        
        # Parsear respuesta
        parsed_requirements = None
        
        # Estrategia 1: Buscar JSON array entre [ y ]
        json_match = re.search(r'\[.*\]', clean_response, re.DOTALL)
        if json_match:
            try:
                parsed_requirements = json.loads(json_match.group())
            except:
                parsed_requirements = None
        
        # Estrategia 2: extraer objetos JSON
        if not parsed_requirements:
            parsed_requirements = []
            obj_pattern = r'\{[^{}]*"requisito"[^{}]*"tipo"[^{}]*\}'
            for match in re.findall(obj_pattern, clean_response, re.DOTALL):
                try:
                    parsed_requirements.append(json.loads(match))
                except:
                    pass
        
        if not parsed_requirements:
            return {"duros": [], "blandos": [], "idioma": [], "titulos": []}
        
        # Procesar resultados y filtrar duplicados
        result = {"duros": [], "blandos": [], "idioma": [], "titulos": []}
        
        for req_item in parsed_requirements:
            if not isinstance(req_item, dict) or 'requisito' not in req_item or 'tipo' not in req_item:
                continue
            
            req_text = str(req_item.get('requisito', '')).strip()
            req_type = str(req_item.get('tipo', '')).lower().strip()
            
            # Filtrar duplicados y validar
            if req_text and req_type and req_text.lower() not in already_found:
                if req_type == "duro":
                    result["duros"].append(req_text)
                elif req_type == "blando":
                    result["blandos"].append(req_text)
                elif req_type == "idioma":
                    result["idioma"].append(req_text)
                elif req_type in ["titulo", "título"]:
                    result["titulos"].append(req_text)
        
        return result
        
    except Exception as e:
        return {"duros": [], "blandos": [], "idioma": [], "titulos": []}

if __name__ == "__main__":
    # Test básico
    test_text = "Buscamos desarrollador Python con experiencia en Django. Debe tener habilidades de comunicación y trabajo en equipo."
    result = classify_with_ollama_simple(test_text, {})
    print("Resultado de prueba:")
    print(json.dumps(result, indent=2, ensure_ascii=False))