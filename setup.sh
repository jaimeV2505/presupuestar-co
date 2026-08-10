#!/bin/bash
# PresupuestarCO — Script de configuración inicial

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║   PresupuestarCO — Configuración         ║"
echo "║   Generador de presupuestos con IA       ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker no está instalado. Instálalo desde https://docker.com${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker encontrado${NC}"

# Crear .env si no existe
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠ Archivo .env creado. Debes configurar tu ANTHROPIC_API_KEY${NC}"
    echo ""
    
    # Pedir la API key
    echo -e "Ingresa tu Anthropic API Key (o presiona Enter para configurar después):"
    read -r API_KEY
    
    if [ -n "$API_KEY" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/$API_KEY/" .env
        else
            sed -i "s/sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/$API_KEY/" .env
        fi
        echo -e "${GREEN}✓ API Key configurada${NC}"
    else
        echo -e "${YELLOW}⚠ Recuerda configurar ANTHROPIC_API_KEY en .env antes de continuar${NC}"
        exit 0
    fi
else
    echo -e "${GREEN}✓ Archivo .env encontrado${NC}"
    
    # Verificar que tiene API key real
    if grep -q "sk-ant-xxx" .env; then
        echo -e "${RED}✗ Configura tu ANTHROPIC_API_KEY en .env antes de continuar${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}Construyendo y levantando contenedores...${NC}"
echo "(El primer build puede tomar 3-5 minutos)"
echo ""

docker compose up --build -d

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ¡PresupuestarCO listo!                 ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                                          ║${NC}"
echo -e "${GREEN}║  App:  http://localhost:3000             ║${NC}"
echo -e "${GREEN}║  API:  http://localhost:8000/docs        ║${NC}"
echo -e "${GREEN}║                                          ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo "Para ver logs: docker compose logs -f"
echo "Para detener:  docker compose down"
