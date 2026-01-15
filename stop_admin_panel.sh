#!/bin/bash

# Script para detener el Panel de Administración

echo "🛑 Deteniendo Panel de Administración..."

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Detener Frontend (puerto 3000)
if lsof -i:3000 > /dev/null 2>&1; then
    echo -e "${YELLOW}Deteniendo Frontend (puerto 3000)...${NC}"
    lsof -ti:3000 | xargs kill -9
    echo -e "${GREEN}✅ Frontend detenido${NC}"
else
    echo -e "${YELLOW}Frontend no está corriendo${NC}"
fi

# Nota sobre Backend
echo ""
echo -e "${YELLOW}⚠️  Nota: El backend (puerto 5605) sigue corriendo${NC}"
echo "   Si deseas detenerlo también:"
echo "   lsof -ti:5605 | xargs kill -9"
echo ""
echo -e "${GREEN}✅ Panel de Administración detenido${NC}"
