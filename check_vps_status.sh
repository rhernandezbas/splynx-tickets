#!/bin/bash
# ============================================================================
# Verificar estado del VPS y detectar cambios no autorizados
# ============================================================================

VPS_HOST="root@190.7.234.37"
VPS_PROJECT_DIR="/opt/splynx-tickets"

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        Verificación de Estado del VPS - App Splynx            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Ejecutar verificación en el VPS
ssh "$VPS_HOST" << 'ENDSSH'
cd /opt/splynx-tickets

echo -e "\033[0;34m📊 Estado del Proyecto\033[0m"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Git status
echo ""
echo "📋 Git Status:"
CHANGES=$(git status --porcelain)

if [ -z "$CHANGES" ]; then
    echo -e "\033[0;32m✅ Sin cambios - Repositorio limpio\033[0m"
else
    UNAUTHORIZED=$(echo "$CHANGES" | grep -vE '(\.env|\.log|backup_.*\.tar\.gz|vps_monitor\.log|ALERT_CAMBIOS\.txt)')

    if [ -n "$UNAUTHORIZED" ]; then
        echo -e "\033[0;31m❌ CAMBIOS NO AUTORIZADOS DETECTADOS:\033[0m"
        echo "$UNAUTHORIZED"
        echo ""
        echo -e "\033[1;33m⚠️  Acción requerida: Revertir cambios o sincronizar\033[0m"
    else
        echo -e "\033[0;32m✅ Solo cambios permitidos (.env, logs)\033[0m"
        echo "$CHANGES"
    fi
fi

# Verificar si hay archivo de alerta
if [ -f "ALERT_CAMBIOS.txt" ]; then
    echo ""
    echo -e "\033[0;31m⚠️  ALERTA ACTIVA - Ver detalles:\033[0m"
    cat ALERT_CAMBIOS.txt
fi

# Branch y commit
echo ""
echo "🌿 Branch: $(git branch --show-current)"
echo "📝 Último commit: $(git log -1 --pretty=format:'%h - %s (%ar)')"

# Docker status
echo ""
echo "🐳 Estado de Contenedores:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose ps

# Health check
echo ""
echo "🏥 Health Check:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if curl -sf http://localhost:7842/ > /dev/null; then
    echo -e "\033[0;32m✅ Aplicación respondiendo correctamente\033[0m"
else
    echo -e "\033[0;31m❌ Aplicación no responde\033[0m"
fi

# Logs recientes
echo ""
echo "📋 Últimos 5 logs del backend:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose logs --tail=5 backend 2>/dev/null | grep -v "UserWarning"

# Disk usage
echo ""
echo "💾 Uso de Disco:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
df -h /opt | tail -1

echo ""
ENDSSH

echo ""
echo "✅ Verificación completada"
echo ""
echo "📋 Comandos útiles:"
echo "   ./sync_env_from_vps.sh           - Sincronizar .env desde VPS"
echo "   ./monitor_vps.sh                 - Ejecutar monitoreo manual"
echo "   ssh root@190.7.234.37            - Conectar al VPS"
echo ""
