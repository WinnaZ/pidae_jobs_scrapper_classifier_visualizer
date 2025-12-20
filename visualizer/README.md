# PIDAE Visualizador - Análisis Interactivo de Empleos

Visualizador interactivo para analizar los resultados del procesamiento de empleos y extracción de habilidades del proyecto PIDAE.

## Características

- **Dashboard Interactivo**: Métricas generales y visualizaciones principales
- **Análisis de Habilidades**: Filtros avanzados y análisis detallado de habilidades blandas y duras
- **Análisis de Empleos**: Estadísticas por empleo y distribución de requisitos
- **Estadísticas Detalladas**: Información completa del dataset y calidad de datos
- **Exploración de Datos**: Visualización y filtrado de datos raw con opción de descarga

## Requisitos

- Python 3.8 o superior
- Las librerías especificadas en `requirements.txt`

## Instalación

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

## Uso

### Opción 1: Script Python (Recomendado)
```bash
python run.py
```
Este script automáticamente instalará las dependencias si es necesario.

### Opción 2: Streamlit Directo
```bash
streamlit run app.py
```

**Navegador:**
- Automáticamente se abrirá en `http://localhost:8501`
- Si no se abre automáticamente, ve a esa URL

**Configurar directorio:**
- En la barra lateral, especifica el directorio donde están los archivos CSV de resultados
- Por defecto apunta a: `../Process_Job Carpeta/EmpleosETL/scripts/output_results`

## Estructura de Datos

El visualizador espera archivos CSV con la siguiente estructura mínima:

### Columnas Principales
- `job_id`: ID único del empleo
- `job_title`: Título del empleo
- `requisito`: Texto del requisito original
- `habilidad_detectada`: Habilidad identificada
- `tipo_habilidad`: Tipo (Habilidad Blanda/Habilidad Dura)
- `categoria`: Categoría de la habilidad
- `metodo_clasificacion`: Método usado (Regex/Gemini AI)
- `confianza`: Nivel de confianza de la clasificación

### Formato de Archivos
Los archivos deben seguir el patrón de nomenclatura:
```
{fuente}_{categoria}_{fecha}.csv
```

Ejemplo: `Computrabajo_informatica-y-telecom_20241203.csv`

## Funcionalidades por Pestaña

### 1. Dashboard
- Métricas generales (total empleos, requisitos, habilidades)
- Distribución por tipo de habilidad
- Top categorías más demandadas
- Información del procesamiento

### 2. Habilidades
- Filtros por tipo, categoría y método de clasificación
- Top habilidades más demandadas
- Visualización TreeMap de categorías
- Métricas filtradas en tiempo real

### 3. Empleos
- Análisis estadístico por empleo
- Distribución de habilidades por empleo
- Empleos con más requisitos detectados
- Promedios y extremos

### 4. Estadísticas
- Información completa del dataset
- Análisis de calidad de datos
- Estadísticas por columna
- Detección de valores faltantes

### 5. Datos Raw
- Visualización completa de datos
- Filtros dinámicos por columna
- Selección de columnas a mostrar
- Descarga de datos filtrados

## Configuración Avanzada

### Personalizar Directorio de Datos
Puedes cambiar el directorio por defecto editando la línea en `app.py`:
```python
value="../Process_Job Carpeta/EmpleosETL/scripts/output_results"
```

### Ajustar Caché
El visualizador usa caché de Streamlit para mejorar el rendimiento. Si los datos cambian frecuentemente, puedes limpiar el caché con `Ctrl+C` > `R` en la interfaz.

## Troubleshooting

### Problema: "No se encontraron archivos CSV"
- Verifica que el directorio especificado es correcto
- Asegúrate de que existen archivos .csv en el directorio
- Ejecuta primero el procesador de empleos para generar datos

### Problema: "Error cargando archivo"
- Verifica que los archivos CSV tienen el formato correcto
- Revisa que las columnas esperadas existen
- Comprueba la codificación del archivo (debe ser UTF-8)

### Problema: Visualizaciones vacías
- Verifica que los datos no están vacíos
- Revisa los filtros aplicados
- Comprueba que las columnas necesarias existen

## Notas

- El visualizador está optimizado para datasets grandes usando caché de Streamlit
- Las visualizaciones son interactivas y responsivas
- Todos los filtros se aplican en tiempo real
- Los datos se pueden exportar en formato CSV

## Contribución

Para contribuir al visualizador:
1. Crea una rama para tu feature
2. Implementa los cambios
3. Asegúrate de que todo funciona correctamente
4. Envía un pull request

