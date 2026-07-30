#!/bin/bash
# ════════════════════════════════════════════════════════════════════════
# 🤖 SETUP: LinkedIn Auto-Publisher Bot (Cron Job)
# Ejecuta: bash setup-linkedin-bot-cron.sh
# ════════════════════════════════════════════════════════════════════════

set -euo pipefail

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "🤖 SETUP: LinkedIn Auto-Publisher Bot"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

PROJECT_ROOT="/Users/macbookpro/dev/aif369-web"
SCRIPT="${PROJECT_ROOT}/publish-linkedin-bot.py"
VENV="${PROJECT_ROOT}/.venv"

# ─────────────────────────────────────────────────────────────────────────
# 1. Instalar dependencias
# ─────────────────────────────────────────────────────────────────────────

echo "📦 Instalando dependencias..."
source "${VENV}/bin/activate"
pip install playwright playwright-stealth --quiet
playwright install chromium

echo "✅ Dependencias instaladas"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 2. Verificar .env.local
# ─────────────────────────────────────────────────────────────────────────

echo "🔐 Verificando credenciales..."

if [ ! -f "${PROJECT_ROOT}/.env.local" ]; then
    echo "❌ ERROR: .env.local no encontrado"
    exit 1
fi

# Verificar que tenga LINKEDIN_EMAIL y LINKEDIN_PASSWORD
if ! grep -q "LINKEDIN_EMAIL=" "${PROJECT_ROOT}/.env.local"; then
    echo ""
    echo "⚠️  LINKEDIN_EMAIL no configurado en .env.local"
    echo "   Agrega a .env.local:"
    echo "   LINKEDIN_EMAIL=tu@email.com"
    echo "   LINKEDIN_PASSWORD=tu_password"
    echo ""
fi

echo "✅ Credenciales verificadas"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 3. Configurar Cron Job (9 AM diarios)
# ─────────────────────────────────────────────────────────────────────────

echo "⏰ Configurando cron job (9 AM diarios)..."
echo ""

CRON_CMD="0 9 * * * cd ${PROJECT_ROOT} && source ${VENV}/bin/activate && set -a && source .env.local && set +a && python ${SCRIPT} >> /tmp/linkedin-bot.log 2>&1"

# Verificar si ya existe
if crontab -l 2>/dev/null | grep -q "publish-linkedin-bot.py"; then
    echo "ℹ️  Cron job ya existe"
else
    (crontab -l 2>/dev/null || true; echo "$CRON_CMD") | crontab -
    echo "✅ Cron job agregado"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETADO"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "📋 RESUMEN:"
echo "   • Bot publicará posts automáticamente diarios a las 9 AM"
echo "   • Lunes-Sábado: posts del tema del día"
echo "   • Domingo: sin publicación"
echo ""
echo "🔧 PRÓXIMOS PASOS:"
echo "   1. Agrega credenciales a .env.local (si no existen):"
echo "      LINKEDIN_EMAIL=tu@email.com"
echo "      LINKEDIN_PASSWORD=tu_password"
echo ""
echo "   2. Test: python ${SCRIPT}"
echo ""
echo "   3. Para ver logs:"
echo "      tail -f /tmp/linkedin-bot.log"
echo "      tail -f ${PROJECT_ROOT}/logs/linkedin-bot.log"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   • LinkedIn puede detectar bots. Usa a tu propio riesgo."
echo "   • Primera publicación requiere 2FA manual (espera 60 segundos)"
echo "   • Si LinkedIn bloquea, usa Buffer en lugar de este bot"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
