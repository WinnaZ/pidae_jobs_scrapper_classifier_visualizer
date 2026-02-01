# Web Scrapers - Bolsas de Trabajo Multi-País

Sistema de web scraping para extraer ofertas laborales de múltiples plataformas de LATAM.

## 🌎 Países y Portales Soportados

### 🇦🇷 Argentina (ARG)
| Portal | URL | Script |
|--------|-----|--------|
| ZonaJobs | https://www.zonajobs.com.ar | `ZonaJobs.py` |
| Computrabajo | https://ar.computrabajo.com/ | `Computrabajo.py` |
| Workana | https://www.workana.com/es/freelancers/argentina | `Workana.py` |
| Indeed | https://ar.indeed.com/ | `Indeed_ARG.py` |

### 🇲🇽 México (MX)
| Portal | URL | Script |
|--------|-----|--------|
| OCC Mundial | https://www.occ.com.mx/ | `OCC_MX.py` |
| Bumeran | https://www.bumeran.com.mx/ | `Bumeran_MX.py` |
| Indeed | https://mx.indeed.com/ | `Indeed_MX.py` |

### 🇧🇷 Brasil (BR)
| Portal | URL | Script |
|--------|-----|--------|
| Catho | https://www.catho.com.br/ | `Catho_BR.py` |
| InfoJobs | https://www.infojobs.com.br/ | `InfoJobs_BR.py` |
| Indeed (opcional) | https://br.indeed.com/ | `Indeed_BR.py` |

### 🇨🇴 Colombia (CO)
| Portal | URL | Script |
|--------|-----|--------|
| Computrabajo | https://co.computrabajo.com/ | `Computrabajo_CO.py` |
| Indeed | https://co.indeed.com/ | `Indeed_CO.py` |

---

## 🚀 Instalación

### Requisitos Previos
- Python 3.8+
- Google Chrome instalado
- pip (gestor de paquetes de Python)
- tmux (para ejecución multi-panel)

### Instalar Dependencias

```bash
cd scrapper
pip install -r requirements.txt
```

### Instalar tmux (si no está instalado)

```bash
# Ubuntu/Debian
sudo apt-get install tmux

# macOS
brew install tmux

# Fedora
sudo dnf install tmux
```

---

## 📋 Uso

### Opción 1: Script Maestro Multi-País (Recomendado)

```bash
./ScraperMaestro_tmux.sh
```

Esto mostrará un menú interactivo:

```
┌────────────────────────────────────────────────────────────┐
│           SELECCIONA UN PAÍS O REGIÓN                      │
├────────────────────────────────────────────────────────────┤
│  1) 🇦🇷 ARG - Argentina                                    │
│  2) 🇲🇽 MX  - México                                       │
│  3) 🇧🇷 BR  - Brasil                                       │
│  4) 🇨🇴 CO  - Colombia                                     │
│  5) 🌎 ALL - Ejecutar TODOS los países                     │
│  0) ❌ Salir                                               │
└────────────────────────────────────────────────────────────┘
```

### Ejecución Directa por País

```bash
# Argentina
./ScraperMaestro_tmux.sh arg

# México
./ScraperMaestro_tmux.sh mx

# Brasil
./ScraperMaestro_tmux.sh br

# Colombia
./ScraperMaestro_tmux.sh co

# Todos los países
./ScraperMaestro_tmux.sh all
```

### Opción 2: Scrapers Individuales

```bash
# Argentina
python ZonaJobs.py
python Computrabajo.py
python Workana.py
python Indeed_ARG.py

# México
python OCC_MX.py
python Bumeran_MX.py
python Indeed_MX.py

# Brasil
python Catho_BR.py
python InfoJobs_BR.py
python Indeed_BR.py

# Colombia
python Computrabajo_CO.py
python Indeed_CO.py
```

### Modo Debug

Todos los scrapers soportan `--debug` para información detallada:

```bash
python ZonaJobs.py --debug
python Indeed_ARG.py --debug
```

---

## 🖥️ Controles de tmux

### Navegación

| Comando | Acción |
|---------|--------|
| `Ctrl+B` → `↑↓←→` | Navegar entre paneles |
| `Ctrl+B` → `0-3` | Ir a ventana específica (modo ALL) |
| `Ctrl+B` → `n` | Siguiente ventana |
| `Ctrl+B` → `p` | Ventana anterior |
| `Ctrl+B` → `D` | Desconectar (sigue ejecutándose) |
| `Ctrl+B` → `[` | Modo scroll (q para salir) |
| `Ctrl+B` → `Z` | Zoom en panel actual |
| `Ctrl+C` | Detener scraper en panel activo |

### Reconectar y Gestionar Sesiones

```bash
# Ver sesiones activas
tmux ls

# Reconectar a sesión de Argentina
tmux attach -t scrapers_ARG

# Reconectar a sesión de todos los países
tmux attach -t scrapers_ALL

# Cerrar sesión específica
tmux kill-session -t scrapers_ARG

# Cerrar todas las sesiones
tmux kill-server
```

---

## 📁 Estructura de Archivos de Salida

```
output_jobs/
├── ZonaJobs_{area}_{fecha}.json
├── Computrabajo_{area}_{fecha}.json
├── Workana_{categoria}_{fecha}.json
├── Indeed_ARG_{termino}_{fecha}.json
├── OCC_MX_{categoria}_{fecha}.json
├── Bumeran_MX_{area}_{fecha}.json
├── Indeed_MX_{termino}_{fecha}.json
├── Catho_BR_{termino}_{fecha}.json
├── InfoJobs_BR_{termino}_{fecha}.json
├── Indeed_BR_{termino}_{fecha}.json
├── Computrabajo_CO_{area}_{fecha}.json
└── Indeed_CO_{termino}_{fecha}.json
```

### Formato JSON de Salida

```json
{
  "Id Interno": "ZJ-tecnologia-1-5",
  "titulo": "Desarrollador Full Stack",
  "descripcion": "Buscamos desarrollador con experiencia...",
  "Empresa": "Tech Company S.A.",
  "Fuente": "ZonaJobs",
  "Tipo Portal": "Tradicional",
  "url": "https://...",
  "Pais": "Argentina",
  "ubicacion": "Buenos Aires, Argentina",
  "Categoria Portal": "tecnologia-sistemas",
  "Subcategoria Portal": "desarrollo-web",
  "Categorria": "",
  "Subcategoria": "",
  "hash Descripcion": "abc123...",
  "fecha": "30/01/2026"
}
```

---

## 🔧 Características

### Sistema de Checkpoints
- Guarda progreso automáticamente
- Permite reanudar sesiones interrumpidas
- Usa CTRL+C para interrumpir y guardar

### Deduplicación
- Hash SHA-256 de descripciones
- Evita duplicados entre categorías
- Funciona entre sesiones del mismo día

### Colores por Scraper
Cada scraper tiene un color único para fácil identificación:
- 🟢 **Verde** - ZonaJobs
- 🔵 **Cyan** - Workana
- 🟣 **Magenta** - Computrabajo
- 🔷 **Azul** - LinkedIn / Indeed
- 🟡 **Amarillo** - Catho
- 🔴 **Rojo** - InfoJobs

---

## 🛠️ Solución de Problemas

### ChromeDriver no encontrado
```bash
pip install --upgrade webdriver-manager
```

### Errores de timeout
- Verifica tu conexión a internet
- Aumenta los timeouts en el código si es necesario
- Usa `--debug` para ver dónde falla

### tmux no disponible
```bash
# Usa el script Python en su lugar
python ScraperMaestro.py
```

### Cloudflare bloqueando (Upwork, etc.)
- Algunos sitios requieren intervención manual
- El script te pedirá resolver el CAPTCHA
- Press Enter cuando hayas completado la verificación

---

## 📝 Notas

- Los scrapers incluyen delays aleatorios para evitar detección
- Respeta los términos de servicio de cada sitio web
- Los scripts tienen throttling incorporado
- Las cookies se limpian automáticamente entre páginas

---

## 📊 Unificación de Datos

Para combinar todos los archivos JSON en uno solo:

```bash
python unify_jobs.py
```

Esto crea `../database/all_jobs.json` con todos los empleos únicos.

---

## 📄 Licencia

Este proyecto es parte de la investigación PIDAE - Universidad.

---

**Última actualización**: Enero 2026