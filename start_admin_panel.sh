#!/bin/bash

# Script de inicio rápido para el Panel de Administración
# Sistema de Tickets Splynx

echo "🚀 Iniciando Panel de Administración Splynx..."
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Verificar si estamos en el directorio correcto
if [ ! -f "ADMIN_PANEL_README.md" ]; then
    echo -e "${RED}❌ Error: Ejecuta este script desde el directorio raíz del proyecto${NC}"
    exit 1
fi

# Función para verificar si un puerto está en uso
check_port() {
    lsof -i:$1 > /dev/null 2>&1
    return $?
}

# Verificar Backend
echo -e "${YELLOW}📡 Verificando Backend...${NC}"
if check_port 5605; then
    echo -e "${GREEN}✅ Backend corriendo en puerto 5605${NC}"
else
    echo -e "${RED}❌ Backend NO está corriendo en puerto 5605${NC}"
    echo -e "${YELLOW}   Iniciando backend...${NC}"
    python -m app &
    BACKEND_PID=$!
    echo -e "${GREEN}   Backend iniciado (PID: $BACKEND_PID)${NC}"
    sleep 3
fi

# Verificar Frontend
echo -e "${YELLOW}🎨 Verificando Frontend...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}📦 Instalando dependencias del frontend...${NC}"
    cd frontend
    npm install
    cd ..
    echo -e "${GREEN}✅ Dependencias instaladas${NC}"
fi

# Verificar Base de Datos
echo -e "${YELLOW}🗄️  Verificando Base de Datos...${NC}"
echo "   Verifica manualmente que las tablas existan:"
echo "   mysql -u mysql -p -h 190.7.234.37 -P 3025 ipnext < migrations/create_admin_tables.sql"
echo ""

# Iniciar Frontend
echo -e "${YELLOW}🚀 Iniciando Frontend...${NC}"
cd frontend

# Verificar si ya está corriendo
if check_port 3000; then
    echo -e "${YELLOW}⚠️  Puerto 3000 ya está en uso${NC}"
    echo -e "${YELLOW}   ¿Deseas detener el proceso existente? (s/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Ss]$ ]]; then
        lsof -ti:3000 | xargs kill -9
        echo -e "${GREEN}   Proceso detenido${NC}"
    else
        echo -e "${YELLOW}   Usando proceso existente${NC}"
        exit 0
    fi
fi

echo -e "${GREEN}✅ Iniciando servidor de desarrollo...${NC}"
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Panel de Administración iniciado exitosamente!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📍 URLs:${NC}"
echo -e "   Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "   Backend:  ${GREEN}http://localhost:5605${NC}"
echo ""
echo -e "${YELLOW}📝 PIDs:${NC}"
if [ ! -z "$BACKEND_PID" ]; then
    echo -e "   Backend:  ${GREEN}$BACKEND_PID${NC}"
fi
if [ ! -z "$FRONTEND_PID" ]; then
    echo -e "   Frontend: ${GREEN}$FRONTEND_PID${NC}"
fi
echo ""
echo -e "${YELLOW}⏹️  Para detener:${NC}"
echo "   Ctrl+C o ejecuta: ./stop_admin_panel.sh"
echo ""
echo -e "${YELLOW}📚 Documentación:${NC}"
echo "   cat ADMIN_PANEL_README.md"
echo ""

# Esperar a que el usuario presione Ctrl+C
trap 'echo -e "\n${YELLOW}🛑 Deteniendo servicios...${NC}"; kill $FRONTEND_PID 2>/dev/null; exit 0' INT

wait
