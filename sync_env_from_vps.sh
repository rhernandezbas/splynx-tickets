#!/bin/bash
# ============================================================================
# Sincronizar .env desde VPS a Local
# Permite traer cambios del archivo .env de producción a local
# ============================================================================

VPS_HOST="root@190.7.234.37"
VPS_PROJECT_DIR="/opt/splynx-tickets"
LOCAL_PROJECT_DIR="/Users/rhernandezba/Downloads/Ipnext/app_splynx"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║      Sincronizar .env desde VPS a Local                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -d "$LOCAL_PROJECT_DIR/.git" ]; then
    echo -e "${RED}❌ Error: No estás en el directorio del proyecto${NC}"
    exit 1
fi

cd "$LOCAL_PROJECT_DIR" || exit 1

# Crear backup del .env local actual
if [ -f ".env" ]; then
    BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
    cp .env "$BACKUP_FILE"
    echo -e "${GREEN}✅ Backup creado: $BACKUP_FILE${NC}"
fi

# Descargar .env desde VPS
echo -e "${YELLOW}📥 Descargando .env desde VPS...${NC}"
scp "$VPS_HOST:$VPS_PROJECT_DIR/.env" ".env.vps" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ .env descargado desde VPS${NC}"
    echo ""

    # Mostrar diferencias
    if [ -f ".env" ]; then
        echo "📋 Diferencias entre local y VPS:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        diff -u .env .env.vps || true
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""

        read -p "¿Reemplazar .env local con la versión del VPS? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mv .env.vps .env
            echo -e "${GREEN}✅ .env actualizado con versión del VPS${NC}"
        else
            rm .env.vps
            echo -e "${YELLOW}⚠️  Operación cancelada - .env local sin cambios${NC}"
            exit 0
        fi
    else
        mv .env.vps .env
        echo -e "${GREEN}✅ .env creado desde VPS${NC}"
    fi

    echo ""
    echo "✅ Sincronización completada"
    echo ""
    echo "📋 Próximos pasos (opcional):"
    echo "   1. Revisa los cambios: cat .env"
    echo "   2. Valida configuración: poetry run python validate_env.py"
    echo "   3. Si quieres commitear cambios del .env:"
    echo "      git add .env.example  # Actualizar ejemplo si es necesario"
    echo "      git commit -m 'chore: update .env example from production'"
    echo ""
else
    echo -e "${RED}❌ Error descargando .env desde VPS${NC}"
    exit 1
fi
