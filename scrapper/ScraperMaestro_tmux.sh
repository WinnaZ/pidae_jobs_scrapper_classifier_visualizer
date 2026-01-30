#!/bin/bash
# Script para ejecutar los scrapers en paneles separados de tmux
# Organizado por país/región

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Directorio de trabajo
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Función para mostrar el banner
show_banner() {
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}   SCRAPER MAESTRO - EJECUCIÓN MULTI-PAÍS EN TMUX${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo ""
    echo -e "Directorio: ${CYAN}${SCRIPT_DIR}${NC}"
    echo ""
}

# Función para verificar tmux
check_tmux() {
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
}

# Función para mostrar menú de países
show_menu() {
    echo -e "${WHITE}┌────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${WHITE}│${NC}           ${CYAN}SELECCIONA UN PAÍS O REGIÓN${NC}                     ${WHITE}│${NC}"
    echo -e "${WHITE}├────────────────────────────────────────────────────────────┤${NC}"
    echo -e "${WHITE}│${NC}                                                            ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  ${GREEN}1)${NC} 🇦🇷 ARG - Argentina                                    ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}     ZonaJobs, Computrabajo, Workana, Indeed               ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}                                                            ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  ${GREEN}2)${NC} 🇲🇽 MX  - México                                       ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}     OCC Mundial, Bumeran, Indeed MX                        ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}                                                            ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  ${GREEN}3)${NC} 🇧🇷 BR  - Brasil                                       ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}     Catho, InfoJobs, Indeed BR (opcional)                  ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}                                                            ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  ${GREEN}4)${NC} 🇨🇴 CO  - Colombia                                     ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}     Computrabajo CO, Indeed CO                             ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}                                                            ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  ${YELLOW}5)${NC} 🌎 ALL - Ejecutar TODOS los países                     ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}                                                            ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}  ${RED}0)${NC} ❌ Salir                                               ${WHITE}│${NC}"
    echo -e "${WHITE}│${NC}                                                            ${WHITE}│${NC}"
    echo -e "${WHITE}└────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

# Función para manejar sesión existente
handle_existing_session() {
    local session_name=$1
    if tmux has-session -t "$session_name" 2>/dev/null; then
        echo -e "${YELLOW}⚠ Ya existe una sesión '$session_name'${NC}"
        echo ""
        read -p "¿Deseas cerrarla y crear una nueva? (s/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Ss]$ ]]; then
            tmux kill-session -t "$session_name"
            echo -e "${GREEN}✓ Sesión anterior cerrada${NC}"
            return 0
        else
            echo -e "${BLUE}Adjuntándote a la sesión existente...${NC}"
            tmux attach-session -t "$session_name"
            exit 0
        fi
    fi
    return 0
}

# ============================================================================
# FUNCIONES PARA CADA PAÍS
# ============================================================================

# Argentina (4 scrapers - grid 2x2)
run_argentina() {
    local SESSION_NAME="scrapers_ARG"
    
    echo -e "${GREEN}🇦🇷 Iniciando scrapers de ARGENTINA...${NC}"
    handle_existing_session "$SESSION_NAME"
    
    tmux new-session -d -s "$SESSION_NAME" -n "Argentina"
    
    # Panel 0 - ZonaJobs (arriba izquierda)
    tmux send-keys -t "$SESSION_NAME:0.0" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "clear && echo '========================================'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "echo '    🇦🇷 ZONAJOBS - Argentina'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "echo '    https://www.zonajobs.com.ar'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "echo '========================================'" C-m
    
    # Panel 1 - Workana (arriba derecha)
    tmux split-window -h -t "$SESSION_NAME:0"
    tmux send-keys -t "$SESSION_NAME:0.1" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "clear && echo '========================================'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '    🇦🇷 WORKANA - Argentina'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '    https://www.workana.com/es/freelancers/argentina'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '========================================'" C-m
    
    # Panel 2 - Computrabajo (abajo izquierda)
    tmux split-window -v -t "$SESSION_NAME:0.0"
    tmux send-keys -t "$SESSION_NAME:0.2" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "clear && echo '========================================'" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "echo '    🇦🇷 COMPUTRABAJO - Argentina'" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "echo '    https://ar.computrabajo.com/'" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "echo '========================================'" C-m
    
    # Panel 3 - Indeed ARG (abajo derecha)
    tmux split-window -v -t "$SESSION_NAME:0.1"
    tmux send-keys -t "$SESSION_NAME:0.3" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.3" "clear && echo '========================================'" C-m
    tmux send-keys -t "$SESSION_NAME:0.3" "echo '    🇦🇷 INDEED - Argentina'" C-m
    tmux send-keys -t "$SESSION_NAME:0.3" "echo '    https://ar.indeed.com/'" C-m
    tmux send-keys -t "$SESSION_NAME:0.3" "echo '========================================'" C-m
    
    tmux select-layout -t "$SESSION_NAME:0" tiled
    sleep 1
    
    # Iniciar scrapers
    tmux send-keys -t "$SESSION_NAME:0.0" "python ZonaJobs.py" C-m
    sleep 1
    tmux send-keys -t "$SESSION_NAME:0.1" "python Workana.py" C-m
    sleep 1
    tmux send-keys -t "$SESSION_NAME:0.2" "python Computrabajo.py" C-m
    sleep 1
    tmux send-keys -t "$SESSION_NAME:0.3" "python Indeed_ARG.py" C-m
    
    show_layout_info "Argentina" "$SESSION_NAME" "ZonaJobs" "Workana" "Computrabajo" "Indeed ARG"
    tmux attach-session -t "$SESSION_NAME"
}

# México (3 scrapers - grid 2x2 con uno vacío o 1+2)
run_mexico() {
    local SESSION_NAME="scrapers_MX"
    
    echo -e "${GREEN}🇲🇽 Iniciando scrapers de MÉXICO...${NC}"
    handle_existing_session "$SESSION_NAME"
    
    tmux new-session -d -s "$SESSION_NAME" -n "Mexico"
    
    # Panel 0 - OCC Mundial (arriba)
    tmux send-keys -t "$SESSION_NAME:0.0" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "clear && echo '========================================'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "echo '    🇲🇽 OCC MUNDIAL - México'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "echo '    https://www.occ.com.mx/'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "echo '========================================'" C-m
    
    # Panel 1 - Bumeran MX (arriba derecha)
    tmux split-window -h -t "$SESSION_NAME:0"
    tmux send-keys -t "$SESSION_NAME:0.1" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "clear && echo '========================================'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '    🇲🇽 BUMERAN - México'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '    https://www.bumeran.com.mx/'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '========================================'" C-m
    
    # Panel 2 - Indeed MX (abajo, ancho completo)
    tmux split-window -v -t "$SESSION_NAME:0.0"
    tmux send-keys -t "$SESSION_NAME:0.2" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "clear && echo '========================================'" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "echo '    🇲🇽 INDEED - México'" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "echo '    https://mx.indeed.com/'" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "echo '========================================'" C-m
    
    tmux select-layout -t "$SESSION_NAME:0" tiled
    sleep 1
    
    # Iniciar scrapers
    tmux send-keys -t "$SESSION_NAME:0.0" "python OCC_Mundial.py" C-m
    sleep 1
    tmux send-keys -t "$SESSION_NAME:0.1" "python Bumeran_MX.py" C-m
    sleep 1
    tmux send-keys -t "$SESSION_NAME:0.2" "python Indeed_MX.py" C-m
    
    show_layout_info_3 "México" "$SESSION_NAME" "OCC Mundial" "Bumeran MX" "Indeed MX"
    tmux attach-session -t "$SESSION_NAME"
}

# Brasil (3 scrapers - Catho, InfoJobs, Indeed BR opcional)
run_brasil() {
    local SESSION_NAME="scrapers_BR"
    
    echo -e "${GREEN}🇧🇷 Iniciando scrapers de BRASIL...${NC}"
    
    # Preguntar si incluir Indeed BR
    echo ""
    read -p "¿Incluir Indeed BR (opcional)? (s/n): " -n 1 -r
    echo ""
    local include_indeed=$([[ $REPLY =~ ^[Ss]$ ]] && echo "yes" || echo "no")
    
    handle_existing_session "$SESSION_NAME"
    
    tmux new-session -d -s "$SESSION_NAME" -n "Brasil"
    
    # Panel 0 - Catho
    tmux send-keys -t "$SESSION_NAME:0.0" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "clear && echo '========================================'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "echo '    🇧🇷 CATHO - Brasil'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "echo '    https://www.catho.com.br/'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "echo '========================================'" C-m
    
    # Panel 1 - InfoJobs
    tmux split-window -h -t "$SESSION_NAME:0"
    tmux send-keys -t "$SESSION_NAME:0.1" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "clear && echo '========================================'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '    🇧🇷 INFOJOBS - Brasil'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '    https://www.infojobs.com.br/'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '========================================'" C-m
    
    if [[ "$include_indeed" == "yes" ]]; then
        # Panel 2 - Indeed BR
        tmux split-window -v -t "$SESSION_NAME:0.0"
        tmux send-keys -t "$SESSION_NAME:0.2" "cd '$SCRIPT_DIR'" C-m
        tmux send-keys -t "$SESSION_NAME:0.2" "clear && echo '========================================'" C-m
        tmux send-keys -t "$SESSION_NAME:0.2" "echo '    🇧🇷 INDEED - Brasil (opcional)'" C-m
        tmux send-keys -t "$SESSION_NAME:0.2" "echo '    https://br.indeed.com/'" C-m
        tmux send-keys -t "$SESSION_NAME:0.2" "echo '========================================'" C-m
    fi
    
    tmux select-layout -t "$SESSION_NAME:0" tiled
    sleep 1
    
    # Iniciar scrapers
    tmux send-keys -t "$SESSION_NAME:0.0" "python Catho_BR.py" C-m
    sleep 1
    tmux send-keys -t "$SESSION_NAME:0.1" "python InfoJobs_BR.py" C-m
    
    if [[ "$include_indeed" == "yes" ]]; then
        sleep 1
        tmux send-keys -t "$SESSION_NAME:0.2" "python Indeed_BR.py" C-m
        show_layout_info_3 "Brasil" "$SESSION_NAME" "Catho" "InfoJobs" "Indeed BR"
    else
        show_layout_info_2 "Brasil" "$SESSION_NAME" "Catho" "InfoJobs"
    fi
    
    tmux attach-session -t "$SESSION_NAME"
}

# Colombia (2 scrapers)
run_colombia() {
    local SESSION_NAME="scrapers_CO"
    
    echo -e "${GREEN}🇨🇴 Iniciando scrapers de COLOMBIA...${NC}"
    handle_existing_session "$SESSION_NAME"
    
    tmux new-session -d -s "$SESSION_NAME" -n "Colombia"
    
    # Panel 0 - Computrabajo CO
    tmux send-keys -t "$SESSION_NAME:0.0" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "clear && echo '========================================'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "echo '    🇨🇴 COMPUTRABAJO - Colombia'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "echo '    https://co.computrabajo.com/'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "echo '========================================'" C-m
    
    # Panel 1 - Indeed CO
    tmux split-window -h -t "$SESSION_NAME:0"
    tmux send-keys -t "$SESSION_NAME:0.1" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "clear && echo '========================================'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '    🇨🇴 INDEED - Colombia'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '    https://co.indeed.com/'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "echo '========================================'" C-m
    
    tmux select-layout -t "$SESSION_NAME:0" tiled
    sleep 1
    
    # Iniciar scrapers
    tmux send-keys -t "$SESSION_NAME:0.0" "python Computrabajo_CO.py" C-m
    sleep 1
    tmux send-keys -t "$SESSION_NAME:0.1" "python Indeed_CO.py" C-m
    
    show_layout_info_2 "Colombia" "$SESSION_NAME" "Computrabajo CO" "Indeed CO"
    tmux attach-session -t "$SESSION_NAME"
}

# Ejecutar TODOS los países (cada país en una ventana diferente)
run_all() {
    local SESSION_NAME="scrapers_ALL"
    
    echo -e "${YELLOW}🌎 Iniciando scrapers de TODOS los países...${NC}"
    handle_existing_session "$SESSION_NAME"
    
    tmux new-session -d -s "$SESSION_NAME" -n "ARG"
    
    # ==================== VENTANA 1: ARGENTINA ====================
    # Panel 0 - ZonaJobs
    tmux send-keys -t "$SESSION_NAME:0.0" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.0" "clear && echo '🇦🇷 ZONAJOBS - Argentina'" C-m
    
    tmux split-window -h -t "$SESSION_NAME:0"
    tmux send-keys -t "$SESSION_NAME:0.1" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "clear && echo '🇦🇷 WORKANA - Argentina'" C-m
    
    tmux split-window -v -t "$SESSION_NAME:0.0"
    tmux send-keys -t "$SESSION_NAME:0.2" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "clear && echo '🇦🇷 COMPUTRABAJO - Argentina'" C-m
    
    tmux split-window -v -t "$SESSION_NAME:0.1"
    tmux send-keys -t "$SESSION_NAME:0.3" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:0.3" "clear && echo '🇦🇷 INDEED - Argentina'" C-m
    
    tmux select-layout -t "$SESSION_NAME:0" tiled
    
    # ==================== VENTANA 2: MÉXICO ====================
    tmux new-window -t "$SESSION_NAME" -n "MX"
    
    tmux send-keys -t "$SESSION_NAME:1.0" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:1.0" "clear && echo '🇲🇽 OCC MUNDIAL - México'" C-m
    
    tmux split-window -h -t "$SESSION_NAME:1"
    tmux send-keys -t "$SESSION_NAME:1.1" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:1.1" "clear && echo '🇲🇽 BUMERAN - México'" C-m
    
    tmux split-window -v -t "$SESSION_NAME:1.0"
    tmux send-keys -t "$SESSION_NAME:1.2" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:1.2" "clear && echo '🇲🇽 INDEED - México'" C-m
    
    tmux select-layout -t "$SESSION_NAME:1" tiled
    
    # ==================== VENTANA 3: BRASIL ====================
    tmux new-window -t "$SESSION_NAME" -n "BR"
    
    tmux send-keys -t "$SESSION_NAME:2.0" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:2.0" "clear && echo '🇧🇷 CATHO - Brasil'" C-m
    
    tmux split-window -h -t "$SESSION_NAME:2"
    tmux send-keys -t "$SESSION_NAME:2.1" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:2.1" "clear && echo '🇧🇷 INFOJOBS - Brasil'" C-m
    
    tmux select-layout -t "$SESSION_NAME:2" tiled
    
    # ==================== VENTANA 4: COLOMBIA ====================
    tmux new-window -t "$SESSION_NAME" -n "CO"
    
    tmux send-keys -t "$SESSION_NAME:3.0" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:3.0" "clear && echo '🇨🇴 COMPUTRABAJO - Colombia'" C-m
    
    tmux split-window -h -t "$SESSION_NAME:3"
    tmux send-keys -t "$SESSION_NAME:3.1" "cd '$SCRIPT_DIR'" C-m
    tmux send-keys -t "$SESSION_NAME:3.1" "clear && echo '🇨🇴 INDEED - Colombia'" C-m
    
    tmux select-layout -t "$SESSION_NAME:3" tiled
    
    sleep 1
    
    # ==================== INICIAR TODOS LOS SCRAPERS ====================
    echo -e "${GREEN}Iniciando scrapers de Argentina...${NC}"
    tmux send-keys -t "$SESSION_NAME:0.0" "python ZonaJobs.py" C-m
    tmux send-keys -t "$SESSION_NAME:0.1" "python Workana.py" C-m
    tmux send-keys -t "$SESSION_NAME:0.2" "python Computrabajo.py" C-m
    tmux send-keys -t "$SESSION_NAME:0.3" "python Indeed_ARG.py" C-m
    
    echo -e "${GREEN}Iniciando scrapers de México...${NC}"
    tmux send-keys -t "$SESSION_NAME:1.0" "python OCC_Mundial.py" C-m
    tmux send-keys -t "$SESSION_NAME:1.1" "python Bumeran_MX.py" C-m
    tmux send-keys -t "$SESSION_NAME:1.2" "python Indeed_MX.py" C-m
    
    echo -e "${GREEN}Iniciando scrapers de Brasil...${NC}"
    tmux send-keys -t "$SESSION_NAME:2.0" "python Catho_BR.py" C-m
    tmux send-keys -t "$SESSION_NAME:2.1" "python InfoJobs_BR.py" C-m
    
    echo -e "${GREEN}Iniciando scrapers de Colombia...${NC}"
    tmux send-keys -t "$SESSION_NAME:3.0" "python Computrabajo_CO.py" C-m
    tmux send-keys -t "$SESSION_NAME:3.1" "python Indeed_CO.py" C-m
    
    # Volver a la primera ventana
    tmux select-window -t "$SESSION_NAME:0"
    
    echo ""
    echo -e "${GREEN}✓ Todos los scrapers iniciados${NC}"
    echo ""
    echo -e "${YELLOW}Ventanas disponibles:${NC}"
    echo "  0: ARG - Argentina (4 scrapers)"
    echo "  1: MX  - México (3 scrapers)"
    echo "  2: BR  - Brasil (2 scrapers)"
    echo "  3: CO  - Colombia (2 scrapers)"
    echo ""
    echo -e "${YELLOW}Navegación entre ventanas:${NC}"
    echo "  Ctrl+B, 0-3: Ir a ventana específica"
    echo "  Ctrl+B, n: Siguiente ventana"
    echo "  Ctrl+B, p: Ventana anterior"
    echo ""
    echo -e "${YELLOW}Comandos útiles:${NC}"
    echo "  Ctrl+B, flechas: Cambiar entre paneles"
    echo "  Ctrl+B, D: Desconectar (sigue ejecutándose)"
    echo "  Ctrl+B, [: Modo scroll"
    echo "  tmux attach -t $SESSION_NAME: Reconectar"
    echo "  tmux kill-session -t $SESSION_NAME: Cerrar todo"
    echo ""
    echo -e "${GREEN}Adjuntándote a la sesión...${NC}"
    
    tmux attach-session -t "$SESSION_NAME"
}

# ============================================================================
# FUNCIONES DE AYUDA PARA MOSTRAR INFORMACIÓN
# ============================================================================

show_layout_info() {
    local country=$1
    local session=$2
    local s1=$3
    local s2=$4
    local s3=$5
    local s4=$6
    
    echo ""
    echo -e "${GREEN}✓ Scrapers de $country iniciados${NC}"
    echo ""
    echo -e "${YELLOW}Layout de paneles:${NC}"
    echo "  ┌─────────────────┬─────────────────┐"
    printf "  │ %-15s │ %-15s │\n" "$s1" "$s2"
    echo "  ├─────────────────┼─────────────────┤"
    printf "  │ %-15s │ %-15s │\n" "$s3" "$s4"
    echo "  └─────────────────┴─────────────────┘"
    echo ""
    show_tmux_commands "$session"
}

show_layout_info_3() {
    local country=$1
    local session=$2
    local s1=$3
    local s2=$4
    local s3=$5
    
    echo ""
    echo -e "${GREEN}✓ Scrapers de $country iniciados${NC}"
    echo ""
    echo -e "${YELLOW}Layout de paneles:${NC}"
    echo "  ┌─────────────────┬─────────────────┐"
    printf "  │ %-15s │ %-15s │\n" "$s1" "$s2"
    echo "  ├─────────────────┴─────────────────┤"
    printf "  │           %-15s          │\n" "$s3"
    echo "  └───────────────────────────────────┘"
    echo ""
    show_tmux_commands "$session"
}

show_layout_info_2() {
    local country=$1
    local session=$2
    local s1=$3
    local s2=$4
    
    echo ""
    echo -e "${GREEN}✓ Scrapers de $country iniciados${NC}"
    echo ""
    echo -e "${YELLOW}Layout de paneles:${NC}"
    echo "  ┌─────────────────┬─────────────────┐"
    printf "  │ %-15s │ %-15s │\n" "$s1" "$s2"
    echo "  └─────────────────┴─────────────────┘"
    echo ""
    show_tmux_commands "$session"
}

show_tmux_commands() {
    local session=$1
    echo -e "${YELLOW}Comandos útiles de tmux:${NC}"
    echo "  Ctrl+B, flechas: Cambiar entre paneles"
    echo "  Ctrl+B, D: Desconectar (sigue ejecutándose)"
    echo "  Ctrl+B, [: Modo scroll (q para salir)"
    echo "  Ctrl+C: Detener scraper en panel activo"
    echo -e "  ${CYAN}tmux attach -t $session${NC}: Reconectar"
    echo -e "  ${CYAN}tmux kill-session -t $session${NC}: Cerrar todo"
    echo ""
    echo -e "${GREEN}Adjuntándote a la sesión...${NC}"
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    show_banner
    check_tmux
    
    # Si se pasa un argumento directo, ejecutar sin menú
    case "${1:-}" in
        arg|ARG|1)
            run_argentina
            exit 0
            ;;
        mx|MX|2)
            run_mexico
            exit 0
            ;;
        br|BR|3)
            run_brasil
            exit 0
            ;;
        co|CO|4)
            run_colombia
            exit 0
            ;;
        all|ALL|5)
            run_all
            exit 0
            ;;
        help|--help|-h)
            echo "Uso: $0 [país]"
            echo ""
            echo "Países disponibles:"
            echo "  arg, ARG, 1  - Argentina"
            echo "  mx, MX, 2    - México"
            echo "  br, BR, 3    - Brasil"
            echo "  co, CO, 4    - Colombia"
            echo "  all, ALL, 5  - Todos los países"
            echo ""
            echo "Sin argumentos: muestra menú interactivo"
            exit 0
            ;;
    esac
    
    # Mostrar menú interactivo
    while true; do
        show_menu
        read -p "Selecciona una opción: " choice
        
        case $choice in
            1)
                run_argentina
                break
                ;;
            2)
                run_mexico
                break
                ;;
            3)
                run_brasil
                break
                ;;
            4)
                run_colombia
                break
                ;;
            5)
                run_all
                break
                ;;
            0)
                echo -e "${YELLOW}¡Hasta luego!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Opción inválida. Por favor selecciona 0-5${NC}"
                echo ""
                ;;
        esac
    done
}

# Ejecutar
main "$@"