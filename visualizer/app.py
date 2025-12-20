import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import glob
from datetime import datetime
import numpy as np
import json
import networkx as nx

# Configuración de la página
st.set_page_config(
    page_title="Visualizador PIDAE - Análisis de Empleos",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("PIDAE - Análisis Integral de Empleos y Habilidades")
st.markdown("### Dashboard de Estadísticas Generales")
st.markdown("---")

def create_hard_soft_skills_explorer(df):
    """Crea un explorador interactivo de habilidades duras con sus habilidades blandas asociadas"""
    if 'tipo_habilidad' not in df.columns or 'habilidad_detectada' not in df.columns or 'job_id' not in df.columns:
        return None
    
    # Filtrar solo habilidades duras
    hard_skills_df = df[df['tipo_habilidad'] == 'Habilidad Dura'].copy()
    soft_skills_df = df[df['tipo_habilidad'] == 'Habilidad Blanda'].copy()
    
    if hard_skills_df.empty or soft_skills_df.empty:
        return None
    
    # Obtener top 15 habilidades duras más frecuentes
    top_hard_skills = hard_skills_df['habilidad_detectada'].value_counts().head(15).index.tolist()
    
    return {
        'hard_skills': top_hard_skills,
        'all_data': df,
        'hard_df': hard_skills_df,
        'soft_df': soft_skills_df
    }

@st.cache_data
def load_all_csv_files(directory):
    """Cargar y combinar todos los archivos CSV de resultados"""
    all_data = []
    csv_files = []
    
    if os.path.exists(directory):
        # Buscar primero el archivo consolidado
        consolidated_file = os.path.join(directory, "resultados_clasificacion.csv")
        if os.path.exists(consolidated_file):
            csv_files = [consolidated_file]
        else:
            # Si no existe, buscar archivos individuales
            pattern = os.path.join(directory, "*_clasificado.csv")
            csv_files = glob.glob(pattern)
        
        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path)
                
                # Solo procesar archivos con datos - aceptar variantes de nombres (mayúsculas/minúsculas)
                if len(df) > 0:
                    # Normalizar nombres de columnas para búsqueda resiliente (case-insensitive)
                    cols_map = {c.lower(): c for c in df.columns}

                    # Comprobar si existe alguna columna que represente 'requisito' / termino detectado
                    requisito_candidates = ['requisito', 'termino_encontrado', 'termino', 'habilidad_detectada', 'term']
                    requisito_col = None
                    for cand in requisito_candidates:
                        if cand in cols_map:
                            requisito_col = cols_map[cand]
                            break

                    # Si no tenemos ninguna columna con los términos esperados, saltamos este archivo
                    if requisito_col is None:
                        continue
                    # Limpiar y estandarizar datos
                    filename = os.path.basename(file_path)
                    df['archivo_origen'] = filename

                    # Crear nombres de columna estandarizados a partir de posibles variantes
                    # Mapeo flexible para columnas comunes en distintos CSV
                    def map_col(lower_name, target_name):
                        if lower_name in cols_map:
                            df[target_name] = df[cols_map[lower_name]]

                    map_col('requisito', 'habilidad_detectada')
                    map_col('termino_encontrado', 'habilidad_detectada')
                    map_col('termino', 'habilidad_detectada')
                    map_col('habilidad_detectada', 'habilidad_detectada')

                    map_col('titulo', 'job_title')
                    map_col('id_interno', 'job_id')
                    map_col('id_internos', 'job_id')
                    map_col('id', 'job_id')

                    # Categoría: preferir categoria_portal, categoria_nombre, o columna 'categoria'
                    map_col('categoria_portal', 'categoria')
                    map_col('categoria_nombre', 'categoria')
                    map_col('categoria', 'categoria')

                    # Fuente / origen
                    map_col('fuente', 'fuente_origen')
                    map_col('fuente_clasificacion', 'metodo_clasificacion')
                    map_col('metodo', 'metodo_clasificacion')
                    
                    # Mapear columnas a nombres más amigables
                    if 'categoria_tipo' in df.columns:
                        df['tipo_habilidad'] = df['categoria_tipo'].map({
                            'duro': 'Habilidad Dura',
                            'blando': 'Habilidad Blanda', 
                            'idioma': 'Idioma'
                        }).fillna(df['categoria_tipo'])
                    
                    # Usar categoria_portal (área original del portal) si existe, sino usar categoria_nombre
                    if 'categoria_portal' in df.columns:
                        df['categoria'] = df['categoria_portal']
                    elif 'categoria_nombre' in df.columns:
                        df['categoria'] = df['categoria_nombre']

                    # Mapear tipos de habilidad a un valor estandarizado (case-insensitive / variantes)
                    # Primero si viene en alguna columna esperada ya mapeada por columnas normalizadas
                    if 'tipo_habilidad' not in df.columns:
                        # Try multiple candidate column names (case-insensitive)
                        if 'categoria_tipo' in cols_map:
                            raw = df[cols_map['categoria_tipo']]
                            df['tipo_habilidad'] = raw.map({
                                'duro': 'Habilidad Dura',
                                'blando': 'Habilidad Blanda', 
                                'idioma': 'Idioma'
                            }).fillna(raw)
                        elif 'area' in cols_map:
                            raw = df[cols_map['area']].astype(str).str.lower()
                            def area_to_tipo(x):
                                if 'blanda' in x or 'blandas' in x or 'blando' in x:
                                    return 'Habilidad Blanda'
                                if 'dura' in x or 'duras' in x or 'tecnica' in x or 'tecnicas' in x:
                                    return 'Habilidad Dura'
                                if 'idioma' in x or 'idiomas' in x:
                                    return 'Idioma'
                                return x.title()
                            df['tipo_habilidad'] = raw.apply(area_to_tipo)
                        # else keep it missing and dropna later will remove unsuitable rows
                    
                    # Si todavía no se creó 'habilidad_detectada', usar el candidato detectado
                    if 'habilidad_detectada' not in df.columns and requisito_col is not None:
                        df['habilidad_detectada'] = df[requisito_col]
                    
                    if 'titulo' in df.columns:
                        df['job_title'] = df['titulo']
                    
                    # job_id puede venir con distintos nombres (Id_Interno, id_interno, id, etc.)
                    if 'job_id' not in df.columns:
                        for cand in ['id_interno', 'id', 'id_internos', 'id_internos']:
                            if cand in cols_map:
                                df['job_id'] = df[cols_map[cand]]
                                break
                        
                    # Normalizar metodo de clasificación si viene con otro nombre
                    if 'metodo_clasificacion' not in df.columns:
                        for cand in ['metodo', 'fuente_clasificacion', 'metodo_clasificacion']:
                            if cand in cols_map:
                                raw = df[cols_map[cand]]
                                # Mapear valores conocidos
                                df['metodo_clasificacion'] = raw.map({
                                    'regex': 'Regex',
                                    'gemini': 'Gemini AI'
                                }).fillna(raw)
                                break
                    
                    # Determinar la columna fuente_origen. Preferir columna ya presente, luego 'fuente' y por último extraer del nombre de archivo
                    if 'fuente_origen' in df.columns:
                        # already present (keep it)
                        pass
                    elif 'fuente' in cols_map:
                        df['fuente_origen'] = df[cols_map['fuente']]
                    else:
                        # Extraer información del nombre del archivo (para archivos individuales)
                        name_parts = filename.replace('_clasificado.csv', '').split('_')
                        df['fuente_origen'] = name_parts[0] if len(name_parts) >= 1 else 'Desconocido'
                    
                    # Extraer información adicional del nombre del archivo
                    name_parts = filename.replace('_clasificado.csv', '').replace('resultados_clasificacion.csv', '').split('_')
                    df['categoria_busqueda'] = name_parts[1].replace('-', ' ').title() if len(name_parts) >= 2 else 'General'
                    df['fecha_procesamiento'] = name_parts[2] if len(name_parts) >= 3 else 'Sin fecha'
                    
                    all_data.append(df)
                    
            except Exception as e:
                st.warning(f"Error cargando archivo {file_path}: {e}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)

        # --- Normalize/ensure required columns exist before dropping NaNs ---
        # Ensure 'habilidad_detectada' exists: try common variants
        if 'habilidad_detectada' not in combined_df.columns:
            for cand in ['requisito', 'termino_encontrado', 'termino', 'term']:
                if cand in combined_df.columns:
                    combined_df['habilidad_detectada'] = combined_df[cand]
                    break

        # Ensure 'tipo_habilidad' exists: try to infer from available columns
        if 'tipo_habilidad' not in combined_df.columns:
            # Prefer 'categoria_tipo' if present
            if 'categoria_tipo' in combined_df.columns:
                combined_df['tipo_habilidad'] = combined_df['categoria_tipo'].map({
                    'duro': 'Habilidad Dura',
                    'blando': 'Habilidad Blanda',
                    'idioma': 'Idioma'
                }).fillna(combined_df['categoria_tipo'])
            # Try to infer from the 'categoria' textual column
            elif 'categoria' in combined_df.columns:
                def _infer_tipo(x):
                    try:
                        s = str(x).lower()
                    except Exception:
                        return 'Desconocido'
                    if 'dura' in s:
                        return 'Habilidad Dura'
                    if 'bland' in s:
                        return 'Habilidad Blanda'
                    if 'idioma' in s or 'language' in s:
                        return 'Idioma'
                    return 'Desconocido'

                combined_df['tipo_habilidad'] = combined_df['categoria'].apply(_infer_tipo)
            # Map directly from 'Area' column if present (common in process_jobs outputs)
            elif 'Area' in combined_df.columns or 'area' in combined_df.columns:
                area_col = 'Area' if 'Area' in combined_df.columns else 'area'
                def _map_from_area(x):
                    try:
                        s = str(x).lower()
                    except Exception:
                        return 'Desconocido'
                    if 'dura' in s:
                        return 'Habilidad Dura'
                    if 'bland' in s:
                        return 'Habilidad Blanda'
                    if 'idioma' in s or 'language' in s:
                        return 'Idioma'
                    return 'Desconocido'

                combined_df['tipo_habilidad'] = combined_df[area_col].apply(_map_from_area)
            else:
                combined_df['tipo_habilidad'] = 'Desconocido'

        # --- Normalize source names (fuente_origen) and classification method values ---
        def _normalize_source_value(val):
            try:
                s = str(val).strip()
            except Exception:
                return 'Desconocido'
            if not s:
                return 'Desconocido'
            low = s.lower()
            # common portal names variations
            if 'zona' in low or 'zonajobs' in low:
                return 'ZonaJobs'
            if 'computra' in low or 'computrabajo' in low:
                return 'Computrabajo'
            if 'workana' in low:
                return 'Workana'
            if 'indeed' in low:
                return 'Indeed'
            if 'linkedin' in low or 'linked' in low:
                return 'LinkedIn'
            if 'upwork' in low:
                return 'Upwork'
            # default: keep original trimmed value
            return s

        if 'fuente_origen' in combined_df.columns:
            combined_df['fuente_origen'] = combined_df['fuente_origen'].astype(str).apply(_normalize_source_value)

        # Normalize metodo_clasificacion / Fuente_Clasificacion -> metodo_clasificacion
        if 'Fuente_Clasificacion' in combined_df.columns and 'metodo_clasificacion' not in combined_df.columns:
            combined_df['metodo_clasificacion'] = combined_df['Fuente_Clasificacion']

        if 'metodo_clasificacion' in combined_df.columns:
            combined_df['metodo_clasificacion'] = combined_df['metodo_clasificacion'].astype(str).str.strip().map(
                lambda x: 'Regex' if x.lower().startswith('regex') else ('Ollama' if 'ollama' in x.lower() or 'ai' in x.lower() else x)
            )

        # Drop rows that don't contain the core fields we actually care about.
        # Only request subset of columns that actually exist in the combined dataframe
        cleanup_subset = [c for c in ['habilidad_detectada', 'tipo_habilidad'] if c in combined_df.columns]
        if cleanup_subset:
            combined_df = combined_df.dropna(subset=cleanup_subset)

        return combined_df, len(csv_files)
    else:
        return None, 0

def main():
    # Sidebar para configuración
    st.sidebar.header("⚙️ Configuración")
    
    # Directorio de resultados
    results_dir = st.sidebar.text_input(
        "Directorio de resultados:", 
        value="../Base de Datos Tablas"
    )
    
    # Botón para recargar datos
    if st.sidebar.button("Recargar datos"):
        st.cache_data.clear()
    
    # Cargar todos los archivos CSV
    with st.spinner("Cargando datos..."):
        df, num_files = load_all_csv_files(results_dir)

    # Mostrar información clara sobre archivos detectados para facilitar debug
    if df is not None and 'archivo_origen' in df.columns:
        unique_files = sorted(df['archivo_origen'].unique().tolist())
        display_files = unique_files if len(unique_files) <= 6 else unique_files[:6] + ['...']
        st.success(f"Se detectaron {num_files} archivo(s) en el directorio. Archivos leídos: {', '.join(display_files)}\nRegistros totales combinados: {len(df):,}")
    
    if df is None or df.empty:
        st.warning("No se encontraron archivos CSV clasificados en el directorio.")
        st.info("Los datos están sin clasificar. Mostrando estadísticas básicas del archivo unificado...")
        
        # Mostrar estadísticas básicas de all_jobs.json
        jobs_data = load_jobs_json(results_dir)
        if jobs_data:
            show_basic_stats(jobs_data)
        else:
            st.error("No se encontró all_jobs.json. Ejecutar primero unify_jobs.py")
        return
    
    # Filtros interactivos en sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros Interactivos")
    
    # Filtro de fuentes con checkboxes
    st.sidebar.markdown("**Fuentes de Datos:**")
    if 'fuente_origen' in df.columns:
        available_sources = sorted(df['fuente_origen'].unique())
        selected_sources = []
        
        # Crear checkboxes para cada fuente
        for source in available_sources:
            source_name = source.lower()
            if 'zona' in source_name:
                display_name = "ZonaJobs"
            elif 'computra' in source_name:
                display_name = "Computrabajo"
            elif 'workana' in source_name:
                display_name = "Workana"
            else:
                display_name = f"📋 {source}"
            
            if st.sidebar.checkbox(display_name, value=True, key=f"source_{source}"):
                selected_sources.append(source)
    else:
        selected_sources = []
    
    # Filtro de tipos de habilidades
    st.sidebar.markdown("**Tipos de Habilidades:**")
    if 'tipo_habilidad' in df.columns:
        show_soft_skills = st.sidebar.checkbox("🤝 Habilidades Blandas", value=True)
        show_hard_skills = st.sidebar.checkbox("💻 Habilidades Duras", value=True)
        show_languages = st.sidebar.checkbox("🌍 Idiomas", value=True)
        
        # Construir lista de tipos seleccionados
        selected_skill_types = []
        if show_soft_skills:
            selected_skill_types.append("Habilidad Blanda")
        if show_hard_skills:
            selected_skill_types.append("Habilidad Dura")
        if show_languages:
            selected_skill_types.append("Idioma")
    else:
        selected_skill_types = []
    
    # Aplicar filtros
    filtered_df = df.copy()
    
    # Filtrar por fuentes
    if 'fuente_origen' in df.columns:
        if selected_sources:  # Si hay fuentes seleccionadas
            filtered_df = filtered_df[filtered_df['fuente_origen'].isin(selected_sources)]
        else:  # Si no hay fuentes seleccionadas, mostrar dataframe vacío
            filtered_df = filtered_df.iloc[0:0]  # Dataframe vacío con las mismas columnas
    
    # Filtrar por tipos de habilidades (solo si aún hay datos)
    if not filtered_df.empty and 'tipo_habilidad' in df.columns:
        if selected_skill_types:  # Si hay tipos seleccionados
            filtered_df = filtered_df[filtered_df['tipo_habilidad'].isin(selected_skill_types)]
        else:  # Si no hay tipos seleccionados, mostrar dataframe vacío
            filtered_df = filtered_df.iloc[0:0]  # Dataframe vacío con las mismas columnas
    
    # Información filtrada en sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("Datos Filtrados")
    st.sidebar.metric("Registros mostrados", f"{len(filtered_df):,}")
    st.sidebar.metric("Empleos únicos", f"{filtered_df['job_id'].nunique() if 'job_id' in filtered_df.columns else 'N/A'}")
    if 'habilidad_detectada' in filtered_df.columns:
        st.sidebar.metric("Habilidades únicas", f"{filtered_df['habilidad_detectada'].nunique():,}")
    
    # Mostrar dashboard integral con datos filtrados
    display_integrated_dashboard(filtered_df, df, results_dir)

@st.cache_data
def load_jobs_json(directory):
    """Cargar all_jobs.json para mostrar estadísticas básicas"""
    json_file = os.path.join(directory, "all_jobs.json")
    
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Verificar si es un archivo de Git LFS
                if content.startswith('version https://git-lfs.github.com'):
                    st.warning("⚠️ all_jobs.json está en Git LFS y no está disponible localmente")
                    return []
                jobs = json.loads(content)
                return jobs
        except json.JSONDecodeError as e:
            st.error(f"Error al parsear all_jobs.json: {str(e)}")
            return []
        except Exception as e:
            st.warning(f"Error cargando all_jobs.json: {str(e)}")
            return []
    return []

def show_basic_stats(jobs):
    """Mostrar estadísticas básicas de all_jobs.json"""
    if not jobs:
        st.warning("No se encontró all_jobs.json")
        return
    
    st.success(f"Datos cargados: **{len(jobs):,} empleos** en all_jobs.json")
    
    # Crear DataFrame para análisis básico
    df_jobs = pd.DataFrame(jobs)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Empleos", f"{len(jobs):,}")
    
    with col2:
        fuentes = df_jobs['Fuente'].value_counts() if 'Fuente' in df_jobs.columns else {}
        st.metric("Fuentes", len(fuentes))
    
    with col3:
        empresas = df_jobs['Empresa'].nunique() if 'Empresa' in df_jobs.columns else 0
        st.metric("Empresas Únicas", f"{empresas:,}")
    
    with col4:
        paises = df_jobs['Pais'].nunique() if 'Pais' in df_jobs.columns else 0
        st.metric("Países", paises)
    
    # Gráficos básicos
    col1, col2 = st.columns(2)
    
    with col1:
        if 'Fuente' in df_jobs.columns:
            st.subheader("Distribución por Fuente")
            fuentes_count = df_jobs['Fuente'].value_counts()
            fig = px.pie(
                values=fuentes_count.values,
                names=fuentes_count.index,
                title="Empleos por Fuente de Datos"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if 'Pais' in df_jobs.columns:
            st.subheader("Distribución por País")
            paises_count = df_jobs['Pais'].value_counts().head(10)
            fig = px.bar(
                x=paises_count.values,
                y=paises_count.index,
                orientation='h',
                title="Top 10 Países con más Empleos"
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
    
    # Información adicional
    st.subheader("Información del Dataset")
    st.info("""
    **Estado:** Datos sin clasificar - Se requiere ejecutar el clasificador
    
    **Próximos pasos:**
    1. Ejecutar `clasificador_simple.py` en Base de Datos Tablas
    2. Esperar a que se generen los archivos CSV clasificados
    3. Recargar esta página para ver análisis completo de requisitos
    
    **Archivos que se generarán:**
    - `empleos_clasificados.csv`
    - `requisitos_clasificados.csv` 
    - `empleo_requisito_clasificados.csv`
    """)

def display_integrated_dashboard(filtered_df, original_df=None, results_dir=None):
    """Dashboard integrado con todas las estadísticas generales"""
    df = filtered_df
    
    # Verificar si hay datos para mostrar
    if df.empty:
        st.warning("⚠️ No hay datos que mostrar con los filtros aplicados.")
        st.info("💡 Selecciona al menos una fuente de datos y un tipo de habilidad en la barra lateral.")
        return
    
    # Mostrar información de filtrado y explicación
    if original_df is not None and len(filtered_df) != len(original_df):
        st.info(f"Mostrando {len(filtered_df):,} habilidades/requisitos de {len(original_df):,} totales (filtrados)")
    else:
        st.info(f"Mostrando todos los {len(df):,} habilidades/requisitos detectados")
    
    # Explicación importante
    st.markdown("""
    **💡 Explicación de los datos:**
    - **Cada registro = 1 habilidad/requisito** detectado en una oferta laboral
    - **Un empleo puede tener múltiples habilidades** (comunicación, Excel, experiencia, etc.)
    - **Por eso hay más registros que empleos únicos**
    - El gráfico "Datos por Fuente" muestra la cantidad de habilidades detectadas, no empleos únicos
    """)
    
    st.markdown("---")
    
    # Métricas principales
    st.header("Métricas Principales")
    
    # Primera fila - Métricas generales
    col1, col2, col3, col4 = st.columns(4)
    
    
    with col1:
        # Mostrar total de empleos procesados (si existe all_jobs.json)
        jobs_json = load_jobs_json(results_dir)
        if jobs_json:
            total_processed_jobs = len(jobs_json)
            st.metric("📦 Empleos Procesados (all_jobs.json)", f"{total_processed_jobs:,}")
        else:
            st.metric("📦 Empleos Procesados (all_jobs.json)", "N/A")

    with col2:
        total_jobs = df['job_id'].nunique() if 'job_id' in df.columns else len(df)
        st.metric("💼 Empleos Totales (con registros)", f"{total_jobs:,}")
    
    with col3:
        if 'tipo_habilidad' in df.columns:
            total_soft = len(df[df['tipo_habilidad'] == 'Habilidad Blanda'])
            st.metric("🤝 Total Habilidades Blandas", f"{total_soft:,}")
        else:
            st.metric("🤝 Total Habilidades Blandas", "N/A")
    
    with col4:
        if 'tipo_habilidad' in df.columns:
            total_hard = len(df[df['tipo_habilidad'] == 'Habilidad Dura'])
            st.metric("💻 Total Habilidades Duras", f"{total_hard:,}")
        else:
            st.metric("💻 Total Habilidades Duras", "N/A")
    
    # Dirección: mostrar cuántos empleos no tienen requisitos detectados (diferencia entre all_jobs.json y los presentes)
    if results_dir is None:
        # default to previous expected path for backwards compatibility
        results_dir = "../Base de Datos Tablas"

    jobs_json = load_jobs_json(results_dir)

    if jobs_json and isinstance(total_jobs, int):
        missing_jobs = max(0, total_processed_jobs - total_jobs)
        st.caption(f"Empleos sin requisitos detectados: {missing_jobs:,} (diferencia entre all_jobs.json y CSV) | Empleos con registros: {total_jobs:,}")

    # Segunda fila - Porcentaje por Fuente
    st.markdown("---")
    st.markdown("#### % de Empleos por Fuente")
    
    if 'fuente_origen' in df.columns:
        sources = df['fuente_origen'].unique()
        num_sources = len(sources)
        
        # Crear columnas dinámicamente basadas en el número de fuentes
        cols = st.columns(min(num_sources, 4))  # Máximo 4 columnas
        
        source_counts = df.groupby('fuente_origen')['job_id'].nunique()
        total_jobs_all_sources = source_counts.sum()
        
        for idx, source in enumerate(sorted(sources)):
            col = cols[idx % len(cols)]
            jobs_in_source = source_counts.get(source, 0)
            percentage = (jobs_in_source / total_jobs_all_sources * 100) if total_jobs_all_sources > 0 else 0
            col.metric(f"📍 {source}", f"{percentage:.1f}%")
    
    st.markdown("---")
    
    # Row 1: Gráficos principales
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart de tipos de habilidades
        if 'tipo_habilidad' in df.columns:
            skill_counts = df['tipo_habilidad'].value_counts()
            
            fig = px.pie(
                values=skill_counts.values,
                names=skill_counts.index,
                title="Distribución por Tipo de Habilidad",
                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            )
            fig.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                textfont_size=12
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        # Gráfico de fuentes de datos
        if 'fuente_origen' in df.columns:
            source_counts = df['fuente_origen'].value_counts()
            
            # Mapear nombres más amigables
            source_mapping = {
                'ZonaJobs': 'ZonaJobs',
                'Computrabajo': 'Computrabajo', 
                'Workana': 'Workana'
            }
            source_display = [source_mapping.get(src, f"📋 {src}") for src in source_counts.index]
            
            fig = px.bar(
                x=source_display,
                y=source_counts.values,
                title="Habilidades/Requisitos Detectados por Fuente",
                color=source_counts.index,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(
                xaxis_title="Fuente",
                yaxis_title="Cantidad de Habilidades/Requisitos",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, width='stretch')
    
    # Row 2: Categorías
    col1, col2 = st.columns(2)
    
    with col1:
        if 'metodo_clasificacion' in df.columns:
            method_counts = df['metodo_clasificacion'].value_counts()

            # If the CSV only contains 'Regex' rows (common when Ollama results weren't appended),
            # fall back to using the aggregated Regex_Encontrados / Ollama_Encontrados counts
            if len(method_counts) == 1 and 'Regex' in method_counts.index and 'Regex_Encontrados' in df.columns and 'Ollama_Encontrados' in df.columns:
                r = int(df['Regex_Encontrados'].sum())
                o = int(df['Ollama_Encontrados'].sum())
                # Only consider fallback when Ollama has non-zero contributions
                if o > 0:
                    method_counts = {'Regex': r, 'Ollama': o}

            fig = px.pie(
                values=list(method_counts.values()),
                names=list(method_counts.keys()),
                title="🔬 Métodos de Clasificación Utilizados",
                color_discrete_sequence=['#FFB6C1', '#98FB98', '#87CEEB']
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, width="stretch")
    
    with col2:
        # Top habilidades por fuente de datos
        if 'fuente_origen' in df.columns and 'habilidad_detectada' in df.columns:
            # Obtener top 8 habilidades más comunes
            top_skills = df['habilidad_detectada'].value_counts().head(8).index
            
            # Filtrar solo esas habilidades y agrupar por fuente
            skills_by_source = df[df['habilidad_detectada'].isin(top_skills)].groupby(['fuente_origen', 'habilidad_detectada']).size().reset_index(name='count')
            
            fig = px.bar(
                skills_by_source,
                x='habilidad_detectada',
                y='count',
                color='fuente_origen',
                title="� Top Habilidades por Fuente de Datos",
                barmode='group',
                color_discrete_map={
                    'Computrabajo': '#FF7F50',
                    'ZonaJobs': '#87CEEB', 
                    'Workana': '#98FB98'
                }
            )
            fig.update_layout(
                xaxis_title="Habilidad",
                yaxis_title="Frecuencia",
                height=400,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, width="stretch")
    
    # NOTE: "Análisis por Categorías de Trabajo" removed by request — keep a placeholder in case we add it later

    # --- Sección nueva: visualización de patrones aprendidos por Ollama ---
    st.markdown("---")
    st.header("🔗 Patrones aprendidos por Ollama / IA")

    # Helper: load learned patterns file from results_dir or known locations
    def load_learned_patterns(results_dir_path):
        candidates = []
        if results_dir_path:
            candidates.append(os.path.join(results_dir_path, 'learned_patterns.json'))
        # common fallback
        candidates.append('Process_Job Carpeta/EmpleosETL/output_logs/learned_patterns.json')
        candidates.append('Process_Job Carpeta/EmpleosETL/output_logs/learned_patterns_backup.json')

        for path in candidates:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    continue
        return None

    learned = load_learned_patterns(results_dir)
    if not learned:
        st.info('No se encontró `learned_patterns.json` en el directorio. Ejecuta el clasificador con --ollama para generar patrones aprendidos.')
    else:
        # Extract patterns and metadata
        patterns = learned.get('learned_patterns', learned.get('learned_patterns', {}))
        meta = learned.get('metadata', learned.get('metadata', {}))

        # UI controls: choose graph mode and Top-K for sampled mode (single control defined below)

        # extract counts from history to let the user sample by frequency
        history = meta.get('learning_history', []) if isinstance(meta, dict) else []
        pattern_counts = {}
        for item in history:
            p = item.get('pattern') or item.get('pattern', '')
            if p:
                pattern_counts[p] = pattern_counts.get(p, 0) + 1

        # --- UI controls for graph size and mode ---
        # default to sampled mode to avoid accidental heavy renders
        graph_mode = st.selectbox(
            'Modo grafo',
            ['area -> category (compact)', 'area -> category -> pattern (full)', 'sampled: top-K patterns (fast)'],
            index=2
        )

        # Top-K slider uses number of unique learned patterns and will limit the graph when in sampled mode
        total_unique_patterns = len(pattern_counts)
        # Set safe defaults and upper bounds to prevent UI freeze
        SAFE_DEFAULT_K = 1000
        SAFE_MAX_K = max(1000, min(3000, total_unique_patterns))
        default_k = min(SAFE_DEFAULT_K, total_unique_patterns) if total_unique_patterns > 0 else 0
        top_k = st.slider('Top K patterns to show (for sampled mode)', min_value=0, max_value=max(0, total_unique_patterns), value=default_k, step=10)

        if top_k > SAFE_MAX_K:
            st.warning(f"Selected Top-K ({top_k}) is large — consider using <= {SAFE_MAX_K} to keep the UI responsive.")

        # Build graph: area -> category -> pattern (label)
        if nx is None:
            # networkx not available — fallback to bar chart summary
            st.warning('La librería `networkx` no está instalada — mostrando resumen alternativo (instala networkx para ver el grafo).')
            # Prepare counts by area and category
            by_area = {}
            for area, content in patterns.items():
                if isinstance(content, dict):
                    cat_counts = {cat: len(plist) for cat, plist in content.items()}
                    by_area[area] = cat_counts
                else:
                    by_area[area] = len(content)

            # Create simple bar chart: categories per area (top categories for readability)
            rows = []
            for area, cats in by_area.items():
                if isinstance(cats, dict):
                    for cat, cnt in cats.items():
                        rows.append({'area': area, 'category': cat, 'count': cnt})
                else:
                    rows.append({'area': area, 'category': area, 'count': cats})

            import pandas as _pd
            df_summary = _pd.DataFrame(rows)
            if not df_summary.empty:
                top = df_summary.sort_values('count', ascending=False).head(30)
                fig_alt = px.bar(
                    top,
                    x='category', y='count', color='area', barmode='group',
                    title='Top categories learned by area (fallback)'
                )
                fig_alt.update_layout(xaxis_tickangle=-45, height=450)
                st.plotly_chart(fig_alt, use_container_width=True)
            else:
                st.info('No hay patrones aprendidos para mostrar.')
            # Skip graph creation
            G = None
        else:
            G = nx.Graph()

        # Cache helpers: build graph data and compute layout only when the user requests it
        @st.cache_data(show_spinner=False)
        def build_graph_data(patterns, meta_ts, graph_mode, top_k, pattern_counts):
            nodes_meta = {}
            edges = []

            # Determine selected patterns if sampled
            selected_patterns = None
            if graph_mode.startswith('sampled') and top_k > 0:
                if pattern_counts:
                    sorted_patterns = sorted(pattern_counts.items(), key=lambda x: -x[1])
                    selected_patterns = set([p for p, _ in sorted_patterns[:top_k]])
                else:
                    selected_patterns = set()
                    for area, content in patterns.items():
                        if isinstance(content, dict):
                            for cat, plist in content.items():
                                for pat_entry in plist:
                                    pat_str = pat_entry[0] if isinstance(pat_entry, (list, tuple)) else str(pat_entry)
                                    selected_patterns.add(pat_str)
                                    if len(selected_patterns) >= top_k:
                                        break
                                if len(selected_patterns) >= top_k:
                                    break
                        if len(selected_patterns) >= top_k:
                            break

            # Build node attributes and edges (serializable)
            for area, content in patterns.items():
                if isinstance(content, dict):
                    nodes_meta[area] = {'type': 'area'}
                    for cat, plist in content.items():
                        nodes_meta.setdefault(cat, {'type': 'category'})
                        edges.append((area, cat))
                        if graph_mode == 'area -> category -> pattern (full)' or (graph_mode.startswith('sampled') and selected_patterns is not None):
                            for pat_entry in plist:
                                pat_str = pat_entry[0] if isinstance(pat_entry, (list, tuple)) else str(pat_entry)
                                if selected_patterns is not None and pat_str not in selected_patterns:
                                    continue
                                label = pat_entry[1] if isinstance(pat_entry, (list, tuple)) and len(pat_entry) > 1 and pat_entry[1] else pat_str
                                node_id = f'{cat}__{label}'
                                nodes_meta.setdefault(node_id, {'type': 'pattern', 'label': label, 'pattern': pat_str})
                                edges.append((cat, node_id))

            return nodes_meta, edges

        @st.cache_data(show_spinner=False)
        def compute_layout(nodes_meta, edges):
            # Build a temporary networkx graph and compute layout
            gtmp = nx.Graph()
            for n, attrs in nodes_meta.items():
                gtmp.add_node(n, **attrs)
            gtmp.add_edges_from(edges)
            try:
                pos = nx.spring_layout(gtmp, k=0.8, iterations=80, seed=42)
            except Exception:
                pos = nx.spring_layout(gtmp)
            return pos
        # If graph_mode is sampled and networkx exists, trim graph before layout
        if G is not None and graph_mode.startswith('sampled'):
            # compute global pattern counts and pick top_k
            # pattern_counts already built from history
            if pattern_counts:
                # select top_k pattern strings by frequency
                sorted_patterns = sorted(pattern_counts.items(), key=lambda x: -x[1])
                selected_patterns = set([p for p,_ in sorted_patterns[:top_k]])
            else:
                # fallback: select patterns by scanning data and taking first top_k
                selected_patterns = set()
                for area, content in patterns.items():
                    if isinstance(content, dict):
                        for cat, plist in content.items():
                            for pat_entry in plist:
                                pat_str = pat_entry[0] if isinstance(pat_entry, (list,tuple)) else str(pat_entry)
                                selected_patterns.add(pat_str)
                                if len(selected_patterns) >= top_k:
                                    break
                            if len(selected_patterns) >= top_k:
                                break
                    if len(selected_patterns) >= top_k:
                        break

            # rebuild graph only with selected patterns
            G2 = nx.Graph()
            for area, content in patterns.items():
                if isinstance(content, dict):
                    G2.add_node(area, type='area')
                    for cat, plist in content.items():
                        # filter patterns for this category
                        filtered = []
                        for pat_entry in plist:
                            pat_str = pat_entry[0] if isinstance(pat_entry, (list,tuple)) else str(pat_entry)
                            if not selected_patterns or pat_str in selected_patterns:
                                filtered.append(pat_entry)
                        if not filtered:
                            continue
                        G2.add_node(cat, type='category')
                        G2.add_edge(area, cat)
                        for pat_entry in filtered:
                            pat_str = pat_entry[0] if isinstance(pat_entry,(list,tuple)) else str(pat_entry)
                            label = pat_entry[1] if isinstance(pat_entry,(list,tuple)) and len(pat_entry)>1 else pat_str
                            node_id = f'{cat}__{label}'
                            G2.add_node(node_id, type='pattern', label=label, pattern=pat_str)
                            G2.add_edge(cat, node_id)
            G = G2
        # Add area & category nodes
        for area, content in patterns.items():
            if isinstance(content, dict):
                G.add_node(area, type='area')
                for cat, plist in content.items():
                    G.add_node(cat, type='category')
                    G.add_edge(area, cat)
                    # plist contains tuples (pattern, etiqueta)
                    # only include pattern nodes here if in full or sampled modes
                    if graph_mode == 'area -> category -> pattern (full)' or graph_mode.startswith('sampled'):
                        for pat_entry in plist:
                            if isinstance(pat_entry, (list, tuple)) and len(pat_entry) >= 1:
                                pat_str = pat_entry[0]
                                label = pat_entry[1] if len(pat_entry) > 1 and pat_entry[1] else pat_str
                            else:
                                pat_str = str(pat_entry)
                                label = pat_str

                            node_id = f'{cat}__{label}'
                            G.add_node(node_id, type='pattern', label=label, pattern=pat_str)
                            G.add_edge(cat, node_id)
        # Compute node sizes
        sizes = []
        labels = []
        node_x = []
        node_y = []

        # (layout will be computed after any sampling step)

        # If sampled mode: select top_k patterns and rebuild a reduced graph to avoid rendering huge graphs
        if graph_mode.startswith('sampled') and top_k > 0 and total_unique_patterns > 0:
            # Determine top patterns by count
            top_patterns = set([p for p, _ in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:top_k]])
            G_small = nx.Graph()
            for area, content in patterns.items():
                if isinstance(content, dict):
                    G_small.add_node(area, type='area')
                    for cat, plist in content.items():
                        added_cat = False
                        for pat_entry in plist:
                            pat_str = pat_entry[0] if isinstance(pat_entry, (list, tuple)) and len(pat_entry) >= 1 else str(pat_entry)
                            label = pat_entry[1] if isinstance(pat_entry, (list, tuple)) and len(pat_entry) > 1 else pat_str
                            if pat_str in top_patterns:
                                if not added_cat:
                                    G_small.add_node(cat, type='category')
                                    G_small.add_edge(area, cat)
                                    added_cat = True
                                node_id = f'{cat}__{label}'
                                G_small.add_node(node_id, type='pattern', label=label, pattern=pat_str)
                                G_small.add_edge(cat, node_id)
            G = G_small

        # Rendering strategy:
        # - compact mode: compute and render immediately (small graph)
        # - sampled/full: require user to click "Generar grafo" to compute (layout can be heavy)
        if graph_mode == 'area -> category (compact)':
            try:
                pos = nx.spring_layout(G, k=0.8, iterations=80, seed=42)
            except Exception:
                pos = nx.spring_layout(G)

            nodes_iter = list(G.nodes(data=True))

            # Build visualization using the compact graph right away
            for n in nodes_iter:
                node = n[0]
                meta_n = n[1]
                typ = meta_n.get('type', 'pattern')
                label = meta_n.get('label', node)
                pattern = meta_n.get('pattern', '')
            # size: if pattern, use pattern_counts else area/category small size
            if typ == 'pattern':
                cnt = pattern_counts.get(pattern, 1)
                size = 6 + min(cnt, 50) * 2
            elif typ == 'category':
                # size = number of connected patterns
                size = 20 + len(list(G.neighbors(node))) * 3
            else:
                size = 35

                x, y = pos.get(node, (0, 0))
                node_x.append(x)
                node_y.append(y)
                sizes.append(size)
                labels.append(label)

            # Build edge traces
            edge_x = []
            edge_y = []
            for e in G.edges():
                x0, y0 = pos[e[0]]
                x1, y1 = pos[e[1]]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]

            edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

            node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=labels,
            textposition='top center',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                reversescale=True,
                color=sizes,
                size=sizes,
                colorbar=dict(thickness=10, title='node size'),
                line_width=1
            )
            )

            fig = go.Figure(data=[edge_trace, node_trace])
            fig.update_layout(
            title='Grafo de Patrones aprendidos por Ollama',
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
            st.plotly_chart(fig, use_container_width=True)
        else:
            # Full / sampled modes: only compute heavy work when user requests it
            can_generate = True
            button_help = 'Generar grafo (puede tardar varios segundos según Top-K).'
            if total_unique_patterns == 0:
                st.info('No hay patrones aprendidos detectados. Nada que generar.')
                can_generate = False

            if can_generate:
                # Show estimated graph size and let the user launch generation
                if graph_mode.startswith('sampled'):
                    est_nodes = None
                    est_nodes = min(total_unique_patterns, top_k) * 1.75 + 50
                    st.info(f'Previsualización: Top-K={top_k}. Est. nodos ≈ {int(est_nodes)} (usar valores bajos para más rapidez).')
                else:
                    st.info('Modo FULL: el grafo puede ser muy grande y demorar mucho en calcularse.')

                if st.button('Generar grafo', key='generate_graph'):
                    with st.spinner('Calculando grafo y posiciones (esto puede tardar)...'):
                        nodes_meta, edges = build_graph_data(patterns, meta.get('last_update'), graph_mode, top_k, pattern_counts)
                        pos = compute_layout(nodes_meta, edges)

                        # Build lists for plotting
                        node_x.clear(); node_y.clear(); sizes.clear(); labels.clear()
                        for node, attrs in nodes_meta.items():
                            typ = attrs.get('type', 'pattern')
                            label = attrs.get('label', node)
                            pattern = attrs.get('pattern', '')
                            if typ == 'pattern':
                                cnt = pattern_counts.get(pattern, 1)
                                size = 6 + min(cnt, 50) * 2
                            elif typ == 'category':
                                size = 20 + 3 * len([e for e in edges if e[0] == node or e[1] == node])
                            else:
                                size = 35

                            x, y = pos.get(node, (0, 0))
                            node_x.append(x); node_y.append(y); sizes.append(size); labels.append(label)

                        edge_x = []
                        edge_y = []
                        for e in edges:
                            p0 = pos.get(e[0]); p1 = pos.get(e[1])
                            # pos entries are numpy arrays — avoid ambiguous truth value by checking for None
                            if p0 is None or p1 is None:
                                continue
                            x0, y0 = p0; x1, y1 = p1
                            edge_x += [x0, x1, None]
                            edge_y += [y0, y1, None]

                        edge_trace = go.Scatter(
                            x=edge_x, y=edge_y,
                            line=dict(width=0.5, color='#888'),
                            hoverinfo='none',
                            mode='lines'
                        )

                        node_trace = go.Scatter(
                            x=node_x, y=node_y,
                            mode='markers+text',
                            text=labels,
                            textposition='top center',
                            hoverinfo='text',
                            marker=dict(
                                showscale=True,
                                colorscale='YlGnBu',
                                reversescale=True,
                                color=sizes,
                                size=sizes,
                                colorbar=dict(thickness=10, title='node size'),
                                line_width=1
                            )
                        )

                        fig = go.Figure(data=[edge_trace, node_trace])
                        fig.update_layout(
                            title='Grafo de Patrones aprendidos por Ollama',
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=20,l=5,r=5,t=40),
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                        )

                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info('Pulsa "Generar grafo" para calcular y mostrar el grafo. Usa Top-K menor para resultados más rápidos.')
#             # Distribución detallada de habilidades específicas por categoría
#             if 'tipo_habilidad' in df.columns and 'habilidad_detectada' in df.columns:
#                 # Crear un dataset más detallado para el sunburst
#                 # Usar categoria en lugar de categoria_busqueda si no está disponible
#                 group_col = 'categoria_busqueda' if 'categoria_busqueda' in df.columns else 'categoria'
#                 detailed_skills = df.groupby([group_col, 'tipo_habilidad', 'habilidad_detectada']).size().reset_index(name='count')
#                 
#                 # Tomar las top habilidades más simples
#                 top_detailed = detailed_skills.nlargest(30, 'count')
#                 
#                 # Crear una columna de ID único más simple
#                 top_detailed = top_detailed.reset_index()
#                 top_detailed['skill_id'] = (top_detailed['tipo_habilidad'].str[:1] + 
#                                           top_detailed.index.astype(str))
#                 
#                 # Mapear colores por tipo de habilidad
#                 color_map = {
#                     'Habilidad Blanda': '#FF6B6B',    # Rojo suave
#                     'Habilidad Dura': '#4ECDC4',      # Turquesa
#                     'Idioma': '#45B7D1'               # Azul
#                 }
#                 
#                 top_detailed['color'] = top_detailed['tipo_habilidad'].map(color_map).fillna('#95A5A6')
#                 
#                 fig = px.sunburst(
#                     top_detailed.head(60),
#                     path=[group_col, 'tipo_habilidad', 'skill_id'],
#                     values='count',
#                     color='tipo_habilidad',
#                     color_discrete_map=color_map,
#                     title='� Habilidades Específicas por Categoría',
#                     hover_data=['habilidad_detectada']
#                 )
#                 
#                 # Personalizar el hover para mostrar la habilidad real
#                 fig.update_traces(
#                     hovertemplate='<b>%{label}</b><br>' +
#                                 'Categoría: %{parent}<br>' +
#                                 'Tipo: %{customdata[0] if customdata else "N/A"}<br>' +
#                                 'Habilidad: %{customdata[1] if customdata else "N/A"}<br>' +
#                                 'Cantidad: %{value}<br>' +
#                                 '<extra></extra>',
#                     customdata=list(zip(top_detailed['tipo_habilidad'], top_detailed['habilidad_detectada']))
#                 )
#                 
#                 fig.update_layout(height=500)
#                 st.plotly_chart(fig, width='stretch')
                
                # (Treemap disabled) - original treemap code commented out to avoid indentation issues
                # --- Treemap visualization temporarily disabled. ---
    
    # Análisis por ubicación geográfica
    if 'ubicacion' in df.columns:
        st.markdown("### 🌍 Análisis Geográfico")
        col1, col2 = st.columns(2)
        
        with col1:
            # Limpiar y agrupar ubicaciones
            df['ubicacion_clean'] = df['ubicacion'].fillna('No especificada')
            # Extraer ciudad principal
            df['ciudad'] = df['ubicacion_clean'].str.split(',').str[0].str.strip()
            
            top_cities = df['ciudad'].value_counts().head(15)
            
            fig = px.bar(
                x=top_cities.values,
                y=top_cities.index,
                orientation='h',
                title="🏙️ Top 15 Ciudades con Más Ofertas",
                color=top_cities.values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            # Habilidades más demandadas por ciudad (top 5 ciudades)
            top_5_cities = top_cities.head(5).index
            city_skills = df[df['ciudad'].isin(top_5_cities)].groupby(['ciudad', 'habilidad_detectada']).size().reset_index(name='count')
            
            # Tomar las top 3 habilidades por ciudad
            top_skills_by_city = city_skills.groupby('ciudad').apply(
                lambda x: x.nlargest(3, 'count')
            ).reset_index(drop=True)
            
            fig = px.bar(
                top_skills_by_city,
                x='count',
                y='ciudad',
                color='habilidad_detectada',
                orientation='h',
                title='🎯 Top 3 Habilidades por Ciudad Principal',
                text='habilidad_detectada'
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, width='stretch')
    
    # Análisis específico por tipo de habilidad
    st.markdown("---")
    st.header("🎯 Análisis por Tipo de Habilidad")
    
    if 'tipo_habilidad' in df.columns and 'habilidad_detectada' in df.columns:
        # Crear tabs para cada tipo de habilidad
        tab1, tab2, tab3 = st.tabs(["🤝 Habilidades Blandas", "💻 Habilidades Duras", "🌍 Idiomas"])
        
        with tab1:
            # Habilidades Blandas
            soft_skills_df = df[df['tipo_habilidad'] == 'Habilidad Blanda']
            if not soft_skills_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Habilidades Blandas Detectadas", len(soft_skills_df))
                
                with col2:
                    if 'categoria' in soft_skills_df.columns:
                        soft_cats = soft_skills_df['categoria'].value_counts().head(8)
                        fig = px.pie(
                            values=soft_cats.values,
                            names=soft_cats.index,
                            title="Categorías de Habilidades Blandas"
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, width="stretch")
                
                st.metric("Total Habilidades Blandas Detectadas", len(soft_skills_df))
            else:
                st.info("No se encontraron habilidades blandas en los datos filtrados.")
        
        with tab2:
            # Habilidades Duras
            hard_skills_df = df[df['tipo_habilidad'] == 'Habilidad Dura']
            if not hard_skills_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Habilidades Duras Detectadas", len(hard_skills_df))
                
                with col2:
                    if 'categoria' in hard_skills_df.columns:
                        hard_cats = hard_skills_df['categoria'].value_counts().head(8)
                        fig = px.pie(
                            values=hard_cats.values,
                            names=hard_cats.index,
                            title="Categorías de Habilidades Duras"
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, width="stretch")
            else:
                st.info("No se encontraron habilidades duras en los datos filtrados.")
        
        with tab3:
            # Idiomas
            languages_df = df[df['tipo_habilidad'] == 'Idioma']
            if not languages_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    top_languages = languages_df['habilidad_detectada'].value_counts().head(10)
                    fig = px.bar(
                        x=top_languages.values,
                        y=top_languages.index,
                        orientation='h',
                        title="🌍 Top 10 Idiomas Demandados",
                        color_discrete_sequence=['#45B7D1'],
                        text=top_languages.values
                    )
                    fig.update_layout(
                        yaxis={'categoryorder':'total ascending'},
                        height=400,
                        yaxis_title="Idioma",
                        xaxis_title="Frecuencia"
                    )
                    fig.update_traces(textposition='outside')
                    st.plotly_chart(fig, width="stretch")
                
                with col2:
                    # Distribución de niveles de idiomas si existe esa información
                    if 'categoria' in languages_df.columns:
                        lang_cats = languages_df['categoria'].value_counts()
                        fig = px.pie(
                            values=lang_cats.values,
                            names=lang_cats.index,
                            title="Niveles/Tipos de Idiomas"
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, width="stretch")
                
                st.metric("Total Idiomas Detectados", len(languages_df))
            else:
                st.info("No se encontraron idiomas en los datos filtrados.")

    # Sección de explorador de habilidades
    st.markdown("---")
    st.header("🔗 Explorador: Habilidades Duras → Blandas")
    
    explorer_data = create_hard_soft_skills_explorer(df)
    
    if explorer_data:
        # Selector de habilidad dura
        selected_hard_skill = st.selectbox(
            "Selecciona una Habilidad Técnica para ver sus Habilidades Blandas Asociadas:",
            explorer_data['hard_skills'],
            key="hard_skill_selector"
        )
        
        if selected_hard_skill:
            # Obtener empleos que tienen esta habilidad dura
            jobs_with_hard = df[df['habilidad_detectada'] == selected_hard_skill]['job_id'].unique()
            
            # Obtener habilidades blandas en esos empleos
            associated_soft_skills = df[
                (df['tipo_habilidad'] == 'Habilidad Blanda') & 
                (df['job_id'].isin(jobs_with_hard))
            ]['habilidad_detectada'].value_counts()
            
            if not associated_soft_skills.empty:
                # Información principal
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("💼 Habilidad Técnica", selected_hard_skill)
                
                with col2:
                    st.metric("👥 Empleos que la piden", len(jobs_with_hard))
                
                with col3:
                    st.metric("🧠 Habilidades Blandas Asociadas", len(associated_soft_skills))
                
                # Gráfico de barras horizontales
                st.subheader(f"Top Habilidades Blandas para: {selected_hard_skill}")
                
                top_soft = associated_soft_skills.head(12)
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=top_soft.values,
                        y=top_soft.index,
                        orientation='h',
                        marker=dict(
                            color=top_soft.values,
                            colorscale='Reds',
                            showscale=True,
                            colorbar=dict(title="Frecuencia")
                        ),
                        text=top_soft.values,
                        textposition='inside',
                        hovertemplate='<b>%{y}</b><br>Frecuencia: %{x}<extra></extra>'
                    )
                ])
                
                fig.update_layout(
                    title=f"Habilidades Blandas Más Requeridas con {selected_hard_skill}",
                    xaxis_title="Número de Empleos",
                    yaxis_title="Habilidad Blanda",
                    height=600,
                    yaxis={'categoryorder': 'total ascending'},
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabla detallada
                st.subheader("Tabla Detallada")
                
                soft_skills_table = pd.DataFrame({
                    'Habilidad Blanda': associated_soft_skills.index,
                    'Frecuencia': associated_soft_skills.values,
                    'Porcentaje': (associated_soft_skills.values / associated_soft_skills.sum() * 100).round(1)
                }).reset_index(drop=True)
                
                st.dataframe(soft_skills_table, use_container_width=True)
                
                # Estadísticas
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Promedio de habilidades blandas por empleo", 
                             f"{associated_soft_skills.sum() / len(jobs_with_hard):.1f}")
                
                with col2:
                    st.metric("Habilidad Blanda Más Común", 
                             f"{associated_soft_skills.index[0]} ({associated_soft_skills.values[0]} veces)")
                
                with col3:
                    st.metric("Variedad de Habilidades Blandas", 
                             f"{len(associated_soft_skills)} diferentes")
            else:
                st.warning(f"No se encontraron habilidades blandas asociadas con {selected_hard_skill}")
    else:
        st.info("No hay datos suficientes de habilidades duras y blandas para crear el explorador")
    
    # Sección de filtros interactivos
    st.markdown("---")
    st.header("🔍 Análisis Detallado con Filtros")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'tipo_habilidad' in df.columns:
            skill_types = ['Todos'] + list(df['tipo_habilidad'].unique())
            selected_skill_type = st.selectbox("Filtrar por Tipo de Habilidad:", skill_types, key="skill_type_filter")
        else:
            selected_skill_type = 'Todos'
    
    with col2:
        if 'fuente_origen' in df.columns:
            sources = ['Todas'] + sorted(list(df['fuente_origen'].unique()))
            selected_source = st.selectbox("Filtrar por Fuente:", sources, key="source_filter")
        else:
            selected_source = 'Todas'
    
    with col3:
        if 'categoria' in df.columns:
            # Si se seleccionó una fuente específica, mostrar solo categorías de esa fuente
            if selected_source != 'Todas' and 'fuente_origen' in df.columns:
                categories_filtered = sorted(list(df[df['fuente_origen'] == selected_source]['categoria'].unique()))
            else:
                categories_filtered = sorted(list(df['categoria'].unique()))
            
            categories = ['Todas'] + categories_filtered
            selected_category = st.selectbox("Filtrar por Categoría (Área):", categories, key="category_filter")
        else:
            selected_category = 'Todas'
    
    # Aplicar filtros
    filtered_df = df.copy()
    
    if selected_skill_type != 'Todos' and 'tipo_habilidad' in df.columns:
        filtered_df = filtered_df[filtered_df['tipo_habilidad'] == selected_skill_type]
    
    if selected_source != 'Todas' and 'fuente_origen' in df.columns:
        filtered_df = filtered_df[filtered_df['fuente_origen'] == selected_source]
    
    if selected_category != 'Todas' and 'categoria' in df.columns:
        filtered_df = filtered_df[filtered_df['categoria'] == selected_category]
    
    # Mostrar datos filtrados
    if not filtered_df.empty:
        st.subheader(f"📊 Resultados Filtrados ({len(filtered_df):,} registros)")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'habilidad_detectada' in filtered_df.columns:
                filtered_skills = filtered_df['habilidad_detectada'].value_counts().head(10)
                
                fig = px.bar(
                    x=filtered_skills.values,
                    y=filtered_skills.index,
                    orientation='h',
                    title="🎯 Top 10 Habilidades (Filtrado)",
                    color=filtered_skills.values,
                    color_continuous_scale='Blues'
                )
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, width="stretch")
        
        with col2:
            # Treemap de categorías filtradas
            if 'categoria' in filtered_df.columns:
                cat_counts = filtered_df['categoria'].value_counts().head(10)
                
                fig = px.treemap(
                    names=cat_counts.index,
                    values=cat_counts.values,
                    title="🌳 Categorías (Filtrado)"
                )
                st.plotly_chart(fig, width="stretch")
        
        # Tabla de datos filtrados (muestra)
        st.subheader("📋 Datos Filtrados")
        
        # Control para número de registros a mostrar
        col1, col2 = st.columns([3, 1])
        with col2:
            num_rows = st.selectbox(
                "Registros a mostrar:",
                [500, 1000, 2000, 5000, "Todos"],
                index=1,
                key="num_rows_selector"
            )
        
        display_columns = [col for col in ['job_title', 'empresa', 'habilidad_detectada', 'tipo_habilidad', 'categoria', 'fuente_origen', 'ubicacion'] if col in filtered_df.columns]
        
        # Renombrar columnas para mejor visualización
        if num_rows == "Todos":
            display_df = filtered_df[display_columns].copy()
        else:
            display_df = filtered_df[display_columns].head(num_rows).copy()
            
        column_names = {
            'job_title': 'Título del Empleo',
            'empresa': 'Empresa', 
            'habilidad_detectada': 'Habilidad/Requisito',
            'tipo_habilidad': 'Tipo',
            'categoria': 'Categoría',
            'fuente_origen': 'Fuente',
            'ubicacion': 'Ubicación'
        }
        display_df = display_df.rename(columns={k: v for k, v in column_names.items() if k in display_df.columns})
        
        # Mostrar información sobre los datos
        total_filtered = len(filtered_df)
        showing = len(display_df)
        st.info(f"📊 Mostrando {showing:,} de {total_filtered:,} registros filtrados")
        
        st.dataframe(display_df, width="stretch")
        
        # Opción de descarga
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Descargar datos filtrados (CSV)",
            data=csv,
            file_name=f"datos_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    else:
        st.warning("No hay datos que mostrar con los filtros aplicados.")





if __name__ == "__main__":
    main()