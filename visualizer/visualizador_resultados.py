#!/usr/bin/env python3
"""
Visualizador Interactivo de Resultados de Clasificación
======================================================

Dashboard interactivo para explorar los resultados de la clasificación
de habilidades blandas y técnicas extraídas de ofertas de trabajo.

Uso:
    streamlit run visualizador_resultados.py
    
Requisitos:
    pip install streamlit pandas plotly
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import glob
import os
from datetime import datetime
import json

# Configuración de la página
st.set_page_config(
    page_title="📊 Visualizador de Resultados PIDAE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .stSelectbox {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def load_classification_data():
    """Carga todos los archivos CSV de resultados"""
    results_path = "output_results"
    if not os.path.exists(results_path):
        return None, []
    
    csv_files = glob.glob(os.path.join(results_path, "*_clasificado.csv"))
    
    if not csv_files:
        return None, []
    
    all_data = []
    file_info = []
    
    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            if not df.empty:
                # Agregar información del archivo
                filename = os.path.basename(file_path)
                df['Archivo_Fuente'] = filename
                
                # Extraer información del nombre del archivo
                parts = filename.replace('_clasificado.csv', '').split('_')
                if len(parts) >= 2:
                    df['Portal'] = parts[0]
                    df['Categoria_Archivo'] = '_'.join(parts[1:-1]) if len(parts) > 2 else parts[1]
                    df['Fecha_Archivo'] = parts[-1] if parts[-1].isdigit() else 'unknown'
                
                all_data.append(df)
                
                # Información del archivo
                file_stats = {
                    'archivo': filename,
                    'empleos': len(df['Id Interno'].unique()) if 'Id Interno' in df.columns else 0,
                    'requisitos': len(df),
                    'tamaño_mb': os.path.getsize(file_path) / (1024*1024)
                }
                file_info.append(file_stats)
                
        except Exception as e:
            st.warning(f"Error cargando {file_path}: {str(e)}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        return combined_df, file_info
    
    return None, []

def load_statistics():
    """Carga estadísticas del proceso de clasificación"""
    stats_file = "output_logs/classification_statistics.json"
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return None

def create_skills_relationship_network(df_data):
    """Crea un gráfico de red mostrando relaciones entre habilidades duras y blandas"""
    
    # Separar habilidades por tipo
    hard_skills = df_data[df_data['Tipo'] == 'Duro']['Habilidad'].unique()
    soft_skills = df_data[df_data['Tipo'] == 'Blando']['Habilidad'].unique()
    
    if len(hard_skills) == 0 or len(soft_skills) == 0:
        return None
    
    # Para cada empleo, encontrar qué hard skills aparecen con qué soft skills
    empleos = df_data['Id Interno'].unique() if 'Id Interno' in df_data.columns else []
    
    connections = {}
    
    for empleo in empleos:
        empleo_data = df_data[df_data['Id Interno'] == empleo]
        empleo_hard = set(empleo_data[empleo_data['Tipo'] == 'Duro']['Habilidad'].unique())
        empleo_soft = set(empleo_data[empleo_data['Tipo'] == 'Blando']['Habilidad'].unique())
        
        # Crear conexiones entre hard y soft skills
        for hard in empleo_hard:
            for soft in empleo_soft:
                key = (hard, soft)
                connections[key] = connections.get(key, 0) + 1
    
    if not connections:
        return None
    
    # Ordenar por frecuencia y tomar las top conexiones
    sorted_connections = sorted(connections.items(), key=lambda x: x[1], reverse=True)[:30]
    
    # Crear datos para Sankey
    hard_list = sorted(set([c[0][0] for c in sorted_connections]))
    soft_list = sorted(set([c[0][1] for c in sorted_connections]))
    
    # Crear índices
    hard_idx = {skill: idx for idx, skill in enumerate(hard_list)}
    soft_idx = {skill: idx + len(hard_list) for idx, skill in enumerate(soft_list)}
    
    # Crear arrays para Sankey
    source = [hard_idx[c[0][0]] for c in sorted_connections]
    target = [soft_idx[c[0][1]] for c in sorted_connections]
    value = [c[1] for c in sorted_connections]
    
    # Crear etiquetas
    labels = hard_list + soft_list
    
    # Crear colores (azul para hard skills, rojo para soft skills)
    colors = ['#3498db'] * len(hard_list) + ['#e74c3c'] * len(soft_list)
    
    # Crear figura Sankey
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=labels,
            color=colors
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=['rgba(52, 152, 219, 0.4)'] * len(source)
        )
    )])
    
    fig.update_layout(
        title="Relaciones entre Habilidades Técnicas y Blandas (Top 30 conexiones)",
        font=dict(size=10),
        height=600
    )
    
    return fig

def create_skills_network_graph(df_data):
    """Crea un gráfico de red interactivo usando plotly"""
    
    import networkx as nx
    
    # Separar habilidades por tipo
    hard_skills_list = df_data[df_data['Tipo'] == 'Duro']['Habilidad'].value_counts().head(10).index.tolist()
    soft_skills_list = df_data[df_data['Tipo'] == 'Blando']['Habilidad'].value_counts().head(10).index.tolist()
    
    if not hard_skills_list or not soft_skills_list:
        return None
    
    # Para cada empleo, encontrar conexiones
    empleos = df_data['Id Interno'].unique() if 'Id Interno' in df_data.columns else []
    
    connections = {}
    
    for empleo in empleos:
        empleo_data = df_data[df_data['Id Interno'] == empleo]
        empleo_hard = set(empleo_data[empleo_data['Tipo'] == 'Duro']['Habilidad'].unique())
        empleo_soft = set(empleo_data[empleo_data['Tipo'] == 'Blando']['Habilidad'].unique())
        
        for hard in empleo_hard:
            if hard in hard_skills_list:
                for soft in empleo_soft:
                    if soft in soft_skills_list:
                        key = (hard, soft)
                        connections[key] = connections.get(key, 0) + 1
    
    if not connections:
        return None
    
    # Crear grafo
    G = nx.Graph()
    
    # Agregar nodos
    for skill in hard_skills_list:
        G.add_node(skill, skill_type='hard')
    for skill in soft_skills_list:
        G.add_node(skill, skill_type='soft')
    
    # Agregar aristas
    for (hard, soft), weight in connections.items():
        G.add_edge(hard, soft, weight=weight)
    
    # Generar posiciones con spring layout
    pos = nx.spring_layout(G, k=2, iterations=50)
    
    # Crear datos para plotly
    edge_x = []
    edge_y = []
    edge_weights = []
    
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_weights.append(edge[2]['weight'])
    
    # Crear traza de aristas
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        showlegend=False
    )
    
    # Crear nodos
    node_x = []
    node_y = []
    node_color = []
    node_size = []
    node_text = []
    node_type = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        # Color según tipo
        if G.nodes[node]['skill_type'] == 'hard':
            node_color.append('#3498db')
        else:
            node_color.append('#e74c3c')
        
        # Tamaño según grado
        degree = G.degree(node)
        node_size.append(20 + degree * 5)
        
        # Frecuencia de la habilidad
        freq = len(df_data[df_data['Habilidad'] == node])
        node_text.append(f"{node}<br>Apariciones: {freq}")
        node_type.append(G.nodes[node]['skill_type'])
    
    # Crear traza de nodos
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[n for n in G.nodes()],
        textposition="top center",
        hovertext=node_text,
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line_width=2,
            line_color='white'
        ),
        showlegend=False
    )
    
    # Crear figura
    fig = go.Figure(data=[edge_trace, node_trace])
    
    fig.update_layout(
        title="Red de Conexiones entre Habilidades Técnicas y Blandas",
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[
            dict(
                text="<b style='color: #3498db'>●</b> Habilidades Técnicas | <b style='color: #e74c3c'>●</b> Habilidades Blandas",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=-0.05,
                xanchor='center'
            )
        ],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=700
    )

def main():
    # Header principal
    st.markdown('<h1 class="main-header">📊 PIDAE - Visualizador de Resultados</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Cargar datos
    with st.spinner("Cargando datos..."):
        df, file_info = load_classification_data()
        stats = load_statistics()
    
    if df is None or df.empty:
        st.error("❌ No se encontraron archivos CSV de resultados en la carpeta 'output_results'")
        st.info("💡 Ejecuta primero el proceso de clasificación para generar los datos")
        return
    
    # Sidebar con filtros
    st.sidebar.header("🎛️ Filtros")
    
    # Filtro por portal
    portales = ['Todos'] + sorted(df['Portal'].unique().tolist())
    portal_seleccionado = st.sidebar.selectbox("Portal:", portales)
    
    # Filtro por categoría
    categorias = ['Todas'] + sorted(df['Categoria_Archivo'].unique().tolist())
    categoria_seleccionada = st.sidebar.selectbox("Categoría:", categorias)
    
    # Filtro por tipo de habilidad
    if 'Tipo' in df.columns:
        tipos = ['Todos'] + sorted(df['Tipo'].unique().tolist())
        tipo_seleccionado = st.sidebar.selectbox("Tipo de Habilidad:", tipos)
    else:
        tipo_seleccionado = 'Todos'
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if portal_seleccionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Portal'] == portal_seleccionado]
    
    if categoria_seleccionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Categoria_Archivo'] == categoria_seleccionada]
        
    if tipo_seleccionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Tipo'] == tipo_seleccionado]
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Archivos Procesados", len(file_info))
    
    with col2:
        empleos_unicos = len(df_filtrado['Id Interno'].unique()) if 'Id Interno' in df_filtrado.columns else 0
        st.metric("💼 Empleos Únicos", empleos_unicos)
    
    with col3:
        st.metric("🎯 Requisitos Extraídos", len(df_filtrado))
    
    with col4:
        if 'Habilidad' in df_filtrado.columns:
            habilidades_unicas = len(df_filtrado['Habilidad'].unique())
            st.metric("🧠 Habilidades Únicas", habilidades_unicas)
        else:
            st.metric("📊 Total Registros", len(df_filtrado))
    
    st.markdown("---")
    
    # Pestañas principales
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Análisis General", "🏆 Top Habilidades", "🔍 Exploración Detallada", "📋 Datos por Archivo", "📊 Estadísticas", "🔗 Relaciones Hard-Soft Skills"])
    
    with tab1:
        st.subheader("📈 Análisis General")
        
        if 'Habilidad' in df_filtrado.columns and 'Tipo' in df_filtrado.columns:
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico por tipo de habilidad
                tipo_counts = df_filtrado['Tipo'].value_counts()
                fig_tipo = px.pie(
                    values=tipo_counts.values, 
                    names=tipo_counts.index,
                    title="Distribución por Tipo de Habilidad",
                    color_discrete_sequence=['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
                )
                st.plotly_chart(fig_tipo, use_container_width=True)
            
            with col2:
                # Gráfico por portal
                portal_counts = df_filtrado['Portal'].value_counts()
                fig_portal = px.bar(
                    x=portal_counts.index,
                    y=portal_counts.values,
                    title="Requisitos por Portal",
                    labels={'x': 'Portal', 'y': 'Cantidad de Requisitos'}
                )
                fig_portal.update_traces(marker_color='#1f77b4')
                st.plotly_chart(fig_portal, use_container_width=True)
        
        # Análisis temporal si hay datos de fecha
        if 'Fecha_Archivo' in df_filtrado.columns:
            fecha_counts = df_filtrado['Fecha_Archivo'].value_counts().sort_index()
            if len(fecha_counts) > 1:
                fig_temporal = px.line(
                    x=fecha_counts.index,
                    y=fecha_counts.values,
                    title="Evolución Temporal de Requisitos Extraídos",
                    labels={'x': 'Fecha', 'y': 'Cantidad de Requisitos'}
                )
                st.plotly_chart(fig_temporal, use_container_width=True)
    
    with tab2:
        st.subheader("🏆 Top Habilidades Más Demandadas")
        
        if 'Habilidad' in df_filtrado.columns:
            # Top habilidades generales
            top_habilidades = df_filtrado['Habilidad'].value_counts().head(20)
            
            fig_top = px.bar(
                x=top_habilidades.values,
                y=top_habilidades.index,
                orientation='h',
                title="Top 20 Habilidades Más Demandadas",
                labels={'x': 'Frecuencia', 'y': 'Habilidad'}
            )
            fig_top.update_traces(marker_color='#2ecc71')
            fig_top.update_layout(height=600)
            st.plotly_chart(fig_top, use_container_width=True)
            
            # Top por tipo si existe la columna
            if 'Tipo' in df_filtrado.columns:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🧠 Top Habilidades Blandas")
                    soft_skills = df_filtrado[df_filtrado['Tipo'] == 'Blando']['Habilidad'].value_counts().head(10)
                    if not soft_skills.empty:
                        fig_soft = px.bar(
                            x=soft_skills.values,
                            y=soft_skills.index,
                            orientation='h',
                            title="Top 10 Habilidades Blandas"
                        )
                        fig_soft.update_traces(marker_color='#e74c3c')
                        st.plotly_chart(fig_soft, use_container_width=True)
                
                with col2:
                    st.subheader("⚙️ Top Habilidades Técnicas") 
                    hard_skills = df_filtrado[df_filtrado['Tipo'] == 'Duro']['Habilidad'].value_counts().head(10)
                    if not hard_skills.empty:
                        fig_hard = px.bar(
                            x=hard_skills.values,
                            y=hard_skills.index,
                            orientation='h',
                            title="Top 10 Habilidades Técnicas"
                        )
                        fig_hard.update_traces(marker_color='#3498db')
                        st.plotly_chart(fig_hard, use_container_width=True)
    
    with tab3:
        st.subheader("🔍 Exploración Detallada")
        
        # Búsqueda por habilidad
        if 'Habilidad' in df_filtrado.columns:
            st.subheader("Buscar por Habilidad")
            habilidad_busqueda = st.text_input("Ingresa una habilidad para buscar:")
            
            if habilidad_busqueda:
                resultados = df_filtrado[df_filtrado['Habilidad'].str.contains(habilidad_busqueda, case=False, na=False)]
                
                if not resultados.empty:
                    st.success(f"Se encontraron {len(resultados)} resultados para '{habilidad_busqueda}'")
                    
                    # Mostrar distribución por portal
                    portal_dist = resultados['Portal'].value_counts()
                    fig_search = px.bar(
                        x=portal_dist.index,
                        y=portal_dist.values,
                        title=f"Distribución de '{habilidad_busqueda}' por Portal"
                    )
                    st.plotly_chart(fig_search, use_container_width=True)
                    
                    # Mostrar algunos ejemplos
                    st.subheader("Ejemplos de Empleos")
                    ejemplos = resultados[['Id Interno', 'Habilidad', 'Portal', 'Categoria_Archivo']].head(10)
                    st.dataframe(ejemplos, use_container_width=True)
                else:
                    st.warning(f"No se encontraron resultados para '{habilidad_busqueda}'")
        
        # Análisis por categoría
        if 'Categoria_Archivo' in df_filtrado.columns and 'Habilidad' in df_filtrado.columns:
            st.subheader("Análisis por Categoría de Empleo")
            categoria_analisis = st.selectbox("Selecciona una categoría para análisis detallado:", 
                                           sorted(df_filtrado['Categoria_Archivo'].unique()))
            
            if categoria_analisis:
                cat_data = df_filtrado[df_filtrado['Categoria_Archivo'] == categoria_analisis]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Empleos en esta categoría", len(cat_data['Id Interno'].unique()) if 'Id Interno' in cat_data.columns else 0)
                with col2:
                    st.metric("Requisitos totales", len(cat_data))
                
                # Top habilidades en esta categoría
                top_cat = cat_data['Habilidad'].value_counts().head(15)
                fig_cat = px.bar(
                    x=top_cat.values,
                    y=top_cat.index,
                    orientation='h',
                    title=f"Top Habilidades en {categoria_analisis}"
                )
                st.plotly_chart(fig_cat, use_container_width=True)
    
    with tab4:
        st.subheader("📋 Información por Archivo")
        
        # Tabla con información de archivos
        if file_info:
            df_files = pd.DataFrame(file_info)
            df_files['tamaño_mb'] = df_files['tamaño_mb'].round(2)
            
            st.dataframe(
                df_files.rename(columns={
                    'archivo': 'Archivo',
                    'empleos': 'Empleos',
                    'requisitos': 'Requisitos',
                    'tamaño_mb': 'Tamaño (MB)'
                }),
                use_container_width=True
            )
            
            # Gráficos de archivos
            col1, col2 = st.columns(2)
            
            with col1:
                fig_empleos = px.bar(
                    df_files,
                    x='archivo',
                    y='empleos',
                    title="Empleos por Archivo"
                )
                fig_empleos.update_xaxes(tickangle=45)
                st.plotly_chart(fig_empleos, use_container_width=True)
            
            with col2:
                fig_requisitos = px.bar(
                    df_files,
                    x='archivo', 
                    y='requisitos',
                    title="Requisitos por Archivo"
                )
                fig_requisitos.update_xaxes(tickangle=45)
                st.plotly_chart(fig_requisitos, use_container_width=True)
    
    with tab5:
        st.subheader("📊 Estadísticas del Proceso")
        
        if stats:
            # Mostrar estadísticas del proceso
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if 'empleos_procesados' in stats:
                    st.metric("Empleos Procesados", stats['empleos_procesados'])
                if 'regex_matches' in stats:
                    st.metric("Matches por Regex", stats['regex_matches'])
            
            with col2:
                if 'gemini_calls' in stats:
                    st.metric("Llamadas a Gemini", stats['gemini_calls'])
                if 'processing_time' in stats:
                    st.metric("Tiempo Total (min)", f"{stats['processing_time']:.1f}")
            
            with col3:
                if 'unique_skills' in stats:
                    st.metric("Habilidades Únicas", stats['unique_skills'])
                if 'error_rate' in stats:
                    st.metric("Tasa de Error (%)", f"{stats['error_rate']:.1f}")
            
            # Mostrar estadísticas completas
            st.subheader("Estadísticas Completas")
            st.json(stats)
        else:
            st.info("No hay estadísticas del proceso disponibles")
        
        # Información del sistema
        st.subheader("ℹ️ Información del Sistema")
        st.info(f"""
        **Última actualización:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        **Archivos procesados:** {len(file_info)}
        
        **Total de datos:** {len(df_filtrado):,} registros
        """)
    
    with tab6:
        st.subheader("🔗 Relaciones entre Habilidades Técnicas y Blandas")
        
        if 'Tipo' not in df_filtrado.columns:
            st.warning("⚠️ No hay datos de clasificación de habilidades por tipo disponibles")
        else:
            hard_skills_count = len(df_filtrado[df_filtrado['Tipo'] == 'Duro'])
            soft_skills_count = len(df_filtrado[df_filtrado['Tipo'] == 'Blando'])
            
            if hard_skills_count == 0 or soft_skills_count == 0:
                st.warning("⚠️ Se requieren tanto habilidades técnicas como blandas para mostrar las relaciones")
            else:
                # Opción de tipo de visualización
                viz_type = st.radio(
                    "Tipo de visualización:",
                    ["Gráfico Sankey (Flujos)", "Red de Conexiones"],
                    horizontal=True
                )
                
                if viz_type == "Gráfico Sankey (Flujos)":
                    st.markdown("**Gráfico Sankey:** Muestra el flujo de conexiones entre las 10 habilidades técnicas "
                               "más frecuentes y las 10 habilidades blandas más frecuentes.")
                    
                    fig_sankey = create_skills_relationship_network(df_filtrado)
                    
                    if fig_sankey:
                        st.plotly_chart(fig_sankey, use_container_width=True)
                        
                        # Explicación
                        st.info("""
                        📌 **Cómo leer este gráfico:**
                        - El ancho de las líneas representa la frecuencia de la conexión
                        - Las líneas azules representan habilidades técnicas
                        - Las líneas rojas representan habilidades blandas
                        - Un flujo mayor indica que esas habilidades aparecen juntas en más empleos
                        """)
                    else:
                        st.warning("No hay suficientes datos para generar el gráfico Sankey")
                
                else:  # Red de Conexiones
                    st.markdown("**Red de Conexiones:** Muestra una red interactiva de las relaciones "
                               "entre las habilidades técnicas y blandas más relevantes.")
                    
                    fig_network = create_skills_network_graph(df_filtrado)
                    
                    if fig_network:
                        st.plotly_chart(fig_network, use_container_width=True)
                        
                        # Explicación
                        st.info("""
                        📌 **Cómo leer este gráfico:**
                        - 🔵 Puntos azules = Habilidades técnicas
                        - 🔴 Puntos rojos = Habilidades blandas
                        - El tamaño del punto indica cuántas veces aparece en los empleos
                        - Las líneas conectan habilidades que aparecen juntas
                        - Los puntos más cercanos aparecen frecuentemente juntos
                        """)
                    else:
                        st.warning("No hay suficientes datos para generar la red de conexiones")
                
                # Panel de análisis detallado
                st.markdown("---")
                st.subheader("📊 Análisis Detallado de Relaciones")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🧠 Habilidades Blandas más frecuentes")
                    soft_top = df_filtrado[df_filtrado['Tipo'] == 'Blando']['Habilidad'].value_counts().head(10)
                    fig_soft_freq = px.bar(
                        x=soft_top.values,
                        y=soft_top.index,
                        orientation='h',
                        title="Top 10 Habilidades Blandas",
                        color=soft_top.values,
                        color_continuous_scale='Reds'
                    )
                    fig_soft_freq.update_traces(showlegend=False)
                    st.plotly_chart(fig_soft_freq, use_container_width=True)
                
                with col2:
                    st.subheader("⚙️ Habilidades Técnicas más frecuentes")
                    hard_top = df_filtrado[df_filtrado['Tipo'] == 'Duro']['Habilidad'].value_counts().head(10)
                    fig_hard_freq = px.bar(
                        x=hard_top.values,
                        y=hard_top.index,
                        orientation='h',
                        title="Top 10 Habilidades Técnicas",
                        color=hard_top.values,
                        color_continuous_scale='Blues'
                    )
                    fig_hard_freq.update_traces(showlegend=False)
                    st.plotly_chart(fig_hard_freq, use_container_width=True)
                
                # Tabla de coocurrencias
                st.markdown("---")
                st.subheader("📈 Tabla de Coocurrencias")
                
                st.markdown("Las siguientes tablas muestran las habilidades blandas más asociadas con cada habilidad técnica top:")
                
                hard_skills_top = df_filtrado[df_filtrado['Tipo'] == 'Duro']['Habilidad'].value_counts().head(5).index
                
                for hard_skill in hard_skills_top:
                    empleos_with_hard = df_filtrado[df_filtrado['Habilidad'] == hard_skill]['Id Interno'].unique() if 'Id Interno' in df_filtrado.columns else []
                    
                    soft_with_hard = df_filtrado[
                        (df_filtrado['Tipo'] == 'Blando') & 
                        (df_filtrado['Id Interno'].isin(empleos_with_hard))
                    ]['Habilidad'].value_counts().head(5)
                    
                    if not soft_with_hard.empty:
                        st.markdown(f"**{hard_skill}** → Habilidades blandas más comunes:")
                        col_data = pd.DataFrame({
                            'Habilidad Blanda': soft_with_hard.index,
                            'Frecuencia': soft_with_hard.values
                        }).reset_index(drop=True)
                        st.dataframe(col_data, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("*Desarrollado para el proyecto PIDAE - Investigación en IA y Trabajo*")

if __name__ == "__main__":
    main()