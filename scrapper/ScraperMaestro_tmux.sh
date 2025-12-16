#!/bin/bash
# Script para ejecutar los scrapers en paneles separados de tmux

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Nombre de la sesión
SESSION_NAME="scrapers"

# Directorio de trabajo
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}   SCRAPER MAESTRO - EJECUCIÓN EN PANELES TMUX${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "Directorio: ${CYAN}${SCRIPT_DIR}${NC}"
echo ""

# Verificar si tmux está instalado
if ! command -v tmux &> /dev/null; then
    echo -e "${YELLOW}⚠ tmux no está instalado${NC}"
    echo ""
    echo "Para instalar tmux, ejecuta:"
    echo "  Ubuntu/Debian: sudo apt-get install tmux"
    echo "  macOS: brew install tmux"
    echo "  Fedora: sudo dnf install tmux"
    echo ""
    exit 1
fi

# Verificar si ya existe una sesión con el mismo nombre
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Ya existe una sesión '$SESSION_NAME'${NC}"
    echo ""
    read -p "¿Deseas cerrarla y crear una nueva? (s/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        tmux kill-session -t "$SESSION_NAME"
        echo -e "${GREEN}✓ Sesión anterior cerrada${NC}"
    else
        echo -e "${BLUE}Adjuntándote a la sesión existente...${NC}"
        tmux attach-session -t "$SESSION_NAME"
        exit 0
    fi
fi

echo -e "${GREEN}Creando sesión de tmux...${NC}"
echo ""

# Crear nueva sesión de tmux
tmux new-session -d -s "$SESSION_NAME" -n "Scrapers"

# Configurar el primer panel (ZonaJobs) - panel 0 (arriba izquierda)
tmux send-keys -t "$SESSION_NAME:0.0" "cd '$SCRIPT_DIR'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "clear" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo '========================================'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo '         ZONAJOBS SCRAPER              '" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo '========================================'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo ''" C-m

# Dividir horizontalmente (crear panel 1 - Workana) (arriba derecha)
tmux split-window -h -t "$SESSION_NAME:0"
tmux send-keys -t "$SESSION_NAME:0.1" "cd '$SCRIPT_DIR'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "clear" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo '========================================'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo '         WORKANA SCRAPER               '" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo '========================================'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo ''" C-m

# Dividir el primer panel verticalmente (crear panel 2 - Computrabajo) (abajo izquierda)
tmux split-window -v -t "$SESSION_NAME:0.0"
tmux send-keys -t "$SESSION_NAME:0.2" "cd '$SCRIPT_DIR'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "clear" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo '========================================'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo '       COMPUTRABAJO SCRAPER            '" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo '========================================'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo ''" C-m

# Dividir el segundo panel verticalmente (crear panel 3 - LinkedIn) (abajo derecha)
tmux split-window -v -t "$SESSION_NAME:0.1"
tmux send-keys -t "$SESSION_NAME:0.3" "cd '$SCRIPT_DIR'" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "clear" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo '========================================'" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo '         LINKEDIN SCRAPER              '" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo '========================================'" C-m
tmux send-keys -t "$SESSION_NAME:0.3" "echo ''" C-m

# Ajustar tamaños de paneles para mejor visualización (2x2 grid)
tmux select-layout -t "$SESSION_NAME:0" tiled

# Esperar un momento para que se estabilice
sleep 1

# Iniciar los scrapers en cada panel
echo -e "${GREEN}Iniciando ZonaJobs...${NC}"
tmux send-keys -t "$SESSION_NAME:0.0" "python ZonaJobs.py" C-m

sleep 1

echo -e "${CYAN}Iniciando Workana...${NC}"
tmux send-keys -t "$SESSION_NAME:0.1" "python Workana.py" C-m

sleep 1

echo -e "${MAGENTA}Iniciando Computrabajo...${NC}"
tmux send-keys -t "$SESSION_NAME:0.2" "python Computrabajo.py" C-m

sleep 1

echo -e "${BLUE}Iniciando LinkedIn...${NC}"
tmux send-keys -t "$SESSION_NAME:0.3" "python LinkedIn.py" C-m

echo ""
echo -e "${GREEN}✓ Todos los scrapers iniciados${NC}"
echo ""
echo -e "${YELLOW}Layout de paneles:${NC}"
echo "  ┌─────────────┬─────────────┐"
echo "  │  ZonaJobs   │   Workana   │"
echo "  ├─────────────┼─────────────┤"
echo "  │ Computrabajo│  LinkedIn   │"
echo "  └─────────────┴─────────────┘"
echo ""
echo -e "${YELLOW}Comandos útiles de tmux:${NC}"
echo -e "  Ctrl+B, luego tecla de flecha: Cambiar entre paneles"
echo -e "  Ctrl+B, luego D: Desconectar de la sesión (sigue ejecutándose)"
echo -e "  Ctrl+B, luego [: Modo scroll (q para salir)"
echo -e "  Ctrl+C en cada panel: Detener el scraper"
echo -e "  ${CYAN}tmux attach -t $SESSION_NAME${NC}: Reconectar a la sesión"
echo -e "  ${CYAN}tmux kill-session -t $SESSION_NAME${NC}: Cerrar todo"
echo ""
echo -e "${GREEN}Adjuntándote a la sesión...${NC}"
echo ""

# Adjuntar a la sesión
tmux attach-session -t "$SESSION_NAME"