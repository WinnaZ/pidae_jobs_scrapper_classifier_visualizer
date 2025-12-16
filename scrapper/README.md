# Web Scrapers - Bolsas de Trabajo

Sistema de web scraping para extraer ofertas laborales de múltiples plataformas argentinas.

## Contenido

- [Scrapers Disponibles](#scrapers-disponibles)
- [Instalación](#instalación)
- [Uso Individual](#uso-individual)
- [Uso con Script Maestro](#uso-con-script-maestro)
- [Características](#características)
- [Salida de Datos](#salida-de-datos)

---

## Scrapers Disponibles

### 1. **ZonaJobs.py**
Scraper para [ZonaJobs.com.ar](https://www.zonajobs.com.ar)
- **Categorías**: Scraping por áreas laborales
- **Características**: 
  - Búsqueda binaria inteligente para detección de páginas
  - Filtrado automático de ofertas duplicadas
  - Manejo de paginación dinámica

### 2. **Workana.py**
Scraper para [Workana.com](https://www.workana.com)
- **Categorías**: Scraping por categorías y subcategorías de freelance
- **Características**: 
  - Validación estricta de URLs
  - Extracción de proyectos remotos
  - Manejo de subcategorías anidadas

### 3. **Computrabajo.py**
Scraper para [Computrabajo.com.ar](https://ar.computrabajo.com)
- **Categorías**: Scraping por cargos/títulos laborales
- **Características**: 
  - Lista predeterminada de empleos más demandados
  - Búsqueda binaria con incrementos de 50 páginas
  - Extracción detallada de requisitos

---

## Instalación

### Requisitos Previos
- Python 3.8+
- Google Chrome instalado
- pip (gestor de paquetes de Python)

### Instalar Dependencias

```bash
cd "Archivos de Scraping"
pip install -r requirements.txt
```

Las dependencias incluyen:
- `selenium` - Automatización del navegador
- `webdriver-manager` - Gestión automática de ChromeDriver
- `argparse` - Manejo de argumentos de línea de comandos

---

## Uso Individual

### Ejecución Básica

```bash
# ZonaJobs
python ZonaJobs.py

# Workana
python Workana.py

# Computrabajo
python Computrabajo.py
```

### Modo Debug

Activa mensajes detallados para ver el progreso completo:

```bash
python ZonaJobs.py --debug
python Workana.py --debug
python Computrabajo.py --debug
```

**Diferencias entre modos:**

| Modo Normal | Modo Debug |
|-------------|------------|
| `Página 5/136 - 25 empleos encontrados` | Muestra cada URL analizada |
| Solo muestra títulos de empleos | Muestra validaciones y rechazos |
| Progreso cada 10 páginas | Progreso detallado de cada paso |

---

## Uso con Script Maestro

### Opción 1: Script Python (Salida Entrelazada)

Ejecuta los 3 scrapers en paralelo con colores distintivos:

```bash
python ScraperMaestro.py
```

**Opciones:**

```bash
# Todos los scrapers
python ScraperMaestro.py --scrapers all

# Solo algunos scrapers
python ScraperMaestro.py --scrapers zonaJobs workana

# Con modo debug
python ScraperMaestro.py --debug
```

**Colores de identificación:**
- **Verde** - ZonaJobs
- **Cyan** - Workana
- **Violeta** - Computrabajo

---

### Opción 2: TMUX (Paneles Divididos) - Recomendado

Visualiza los 3 scrapers simultáneamente en paneles separados:

```bash
./ScraperMaestro_tmux.sh
```

**Layout Visual:**
```
┌─────────────────────┬─────────────────────┐
│                     │                     │
│  ZonaJobs           │  Workana            │
│                     │                     │
│                     ├─────────────────────┤
│                     │                     │
│                     │  Computrabajo       │
│                     │                     │
└─────────────────────┴─────────────────────┘
```

**Controles de TMUX:**

| Comando | Acción |
|---------|--------|
| `Ctrl+B` → `↑↓←→` | Navegar entre paneles |
| `Ctrl+B` → `D` | Desconectar (sigue ejecutándose) |
| `Ctrl+B` → `[` | Modo scroll (presiona `q` para salir) |
| `Ctrl+B` → `Z` | Zoom en panel actual |
| `Ctrl+C` | Detener scraper en panel activo |

**Comandos útiles:**
```bash
# Reconectar a sesión existente
tmux attach -t scrapers

# Ver sesiones activas
tmux ls

# Cerrar sesión completamente
tmux kill-session -t scrapers
```

**Instalar TMUX:**
```bash
# Ubuntu/Debian
sudo apt-get install tmux

# macOS
brew install tmux

# Fedora
sudo dnf install tmux
```

---

### Opción 3: GNU Screen (Ventanas Independientes)

Si prefieres ventanas separadas en lugar de paneles:

```bash
./ScraperMaestro_screen.sh
```

**Controles de Screen:**

| Comando | Acción |
|---------|--------|
| `Ctrl+A` → `0/1/2` | Cambiar a ventana específica |
| `Ctrl+A` → `N` | Siguiente ventana |
| `Ctrl+A` → `P` | Ventana anterior |
| `Ctrl+A` → `D` | Desconectar |

---

## Características

### Búsqueda Binaria Inteligente
- Detecta automáticamente el número máximo de páginas
- Incrementos adaptativos (50 páginas por salto)
- Reduce tiempo de detección de límites

### Modo Debug
- Mensajes detallados de cada paso
- Validación de URLs en tiempo real
- Útil para diagnosticar problemas

### Manejo de Errores
- Reintentos automáticos en páginas fallidas
- Gestión de timeouts y elementos no encontrados
- Logs de errores para debugging

### Progreso Visual
- Indicadores de páginas procesadas (n/m)
- Conteo de empleos por página
- Barra de progreso en scripts maestros

### Ejecución Concurrente
- Threads independientes para cada scraper
- Salida en tiempo real con colores
- No bloquea la terminal

---

## Salida de Datos

### Ubicación
```
output_jobs/
├── ZonaJobs_{area}_{fechas}.json
├── Workana_{categoria}_{fechas}.json
└── Computrabajo_{cargo}_{fechas}.json
```

### Formato JSON

Cada archivo contiene un array de objetos con la siguiente estructura:

```json
{
  "Id Interno": "vendedor-1-5",
  "titulo": "Vendedor de Seguros - Córdoba",
  "descripcion": "Buscamos vendedor con experiencia...",
  "ubicacion": "Córdoba, Argentina",
  "empresa": "Seguros XYZ S.A.",
  "fecha_publicacion": "21/10/2025",
  "url": "https://..."
}
```

---

## Solución de Problemas

### ChromeDriver no encontrado
```bash
# El script usa webdriver-manager que descarga automáticamente
# Si hay problemas, reinstala:
pip install --upgrade webdriver-manager
```

### Errores de timeout
- Revisa tu conexión a internet
- Aumenta los timeouts en el código si es necesario
- Usa `--debug` para ver dónde falla

### No se encuentran empleos (0 empleos)
- Verifica que el sitio web esté accesible
- Puede que hayan cambiado los selectores CSS
- Ejecuta con `--debug` para ver las URLs analizadas

### TMUX no disponible
```bash
# Si prefieres no instalar tmux, usa:
python ScraperMaestro.py
# O ejecuta cada script individualmente
```

---

## Notas

- **Velocidad**: Los scrapers incluyen delays aleatorios para evitar sobrecargar los servidores
- **Ética**: Respeta los términos de servicio de cada sitio web
- **Rate Limiting**: Los scripts tienen throttling incorporado
- **Cookies**: Se limpian automáticamente entre páginas

---

## Soporte

Si encuentras problemas:
1. Ejecuta con `--debug` para diagnosticar
2. Verifica que las dependencias estén actualizadas
3. Revisa los logs generados en `output_logs/`

---

## Licencia

Este proyecto es parte de la investigación PIDAE - Universidad [Nombre].

---

**Última actualización**: Octubre 2025
