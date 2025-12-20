#!/usr/bin/env python3
"""
Script de lanzamiento simple para el Visualizador PIDAE
Uso: python run.py
"""

import subprocess
import sys
import os

def check_streamlit():
    """Verificar si Streamlit está instalado"""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def install_dependencies():
    """Instalar dependencias desde requirements.txt"""
    print("📦 Instalando dependencias...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error instalando dependencias")
        return False

def main():
    print("🚀 Lanzando Visualizador PIDAE...")
    
    # Verificar si estamos en el directorio correcto
    if not os.path.exists("app.py"):
        print("❌ Error: No se encuentra app.py. Ejecuta este script desde el directorio Visualizador")
        sys.exit(1)
    
    # Verificar si Streamlit está instalado
    if not check_streamlit():
        print("⚠️  Streamlit no está instalado. Instalando dependencias...")
        if not install_dependencies():
            sys.exit(1)
    
    # Verificar si el directorio de resultados existe
    results_dir = "../Process_Job Carpeta/EmpleosETL/scripts/output_results"
    if not os.path.exists(results_dir):
        print(f"⚠️  Advertencia: El directorio de resultados no existe: {results_dir}")
        print("   Puedes especificar otro directorio en la interfaz web")
    
    print("🌐 Iniciando servidor Streamlit...")
    print("📝 La aplicación se abrirá en: http://localhost:8501")
    print("⏹️  Para detener el servidor, presiona Ctrl+C")
    print()
    
    # Lanzar Streamlit
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", 
                       "--server.address", "localhost", "--server.port", "8501"])
    except KeyboardInterrupt:
        print("\n👋 ¡Hasta luego!")
    except Exception as e:
        print(f"❌ Error ejecutando Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()