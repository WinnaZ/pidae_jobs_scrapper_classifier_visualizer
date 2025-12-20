# scripts/config.py

# --- Configuración de la Base de Datos SQL Server ---> configura según tu entorno
DB_CONFIG = {
            
}

# --- Configuración de Ollama ---
# Configuración para el servidor Ollama local
OLLAMA_CONFIG = {
    'host': 'localhost',
    'port': 11434,
    'model': 'llama3.2:1b',
    'timeout': 30
}