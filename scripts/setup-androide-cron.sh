#!/bin/bash
# ════════════════════════════════════════════════════════════════════════
# Setup automatizado para El Androide — Publicador diario LinkedIn
# Ejecutar: bash scripts/setup-androide-cron.sh
# ════════════════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="/Users/macbookpro/dev/aif369-web"
SCRIPT="${PROJECT_ROOT}/scripts/androide-linkedin-agent.py"
VENV="${PROJECT_ROOT}/.venv"

echo "════════════════════════════════════════════════════════════════════════"
echo " SETUP: El Androide — LinkedIn Daily Publisher"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 1. Verificar ambiente
# ─────────────────────────────────────────────────────────────────────────

echo "✓ Verificando ambiente..."

if [ ! -d "$VENV" ]; then
    echo "❌ Virtual env no encontrado. Ejecuta: python -m venv .venv"
    exit 1
fi

if [ ! -f "$SCRIPT" ]; then
    echo "❌ Script no encontrado: $SCRIPT"
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────
# 2. Verificar variables de entorno
# ─────────────────────────────────────────────────────────────────────────

echo ""
echo "✓ Verificando credenciales..."

if [ -z "${LINKEDIN_ACCESS_TOKEN:-}" ]; then
    echo "⚠️  LINKEDIN_ACCESS_TOKEN no configurado"
    echo "   Obtén un token en: https://www.linkedin.com/developers/apps"
    echo "   Luego ejecuta: export LINKEDIN_ACCESS_TOKEN='tu_token'"
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "⚠️  GEMINI_API_KEY no configurado"
    echo "   Obtén en: https://aistudio.google.com/apikey"
    echo "   Luego ejecuta: export GEMINI_API_KEY='tu_clave'"
fi

# ─────────────────────────────────────────────────────────────────────────
# 3. Crear directorio de logs
# ─────────────────────────────────────────────────────────────────────────

mkdir -p "${PROJECT_ROOT}/logs"
touch "${PROJECT_ROOT}/logs/androide_posts.log"

echo "✓ Directorio de logs creado"

# ─────────────────────────────────────────────────────────────────────────
# 4. Setup cron job (publica a las 9 AM de lunes-sábado)
# ─────────────────────────────────────────────────────────────────────────

echo ""
echo "✓ Configurando cron job..."

CRON_CMD="0 9 * * 0-5 cd ${PROJECT_ROOT} && source ${VENV}/bin/activate && python scripts/androide-linkedin-agent.py >> logs/androide_cron.log 2>&1"

# Agregar a crontab (sin duplicados)
if crontab -l 2>/dev/null | grep -q "androide-linkedin-agent.py"; then
    echo "   ℹ️  Cron job ya existe"
else
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "   ✅ Cron job agregado (9 AM, lunes-sábado)"
fi

# ─────────────────────────────────────────────────────────────────────────
# 5. Test local (publicar post de prueba)
# ─────────────────────────────────────────────────────────────────────────

echo ""
echo "⚙️  Ejecutando test local..."
echo ""

source "${VENV}/bin/activate"
python "${SCRIPT}"

# ─────────────────────────────────────────────────────────════════════════
# 6. Resumen
# ─────────────────────────════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo " ✅ SETUP COMPLETADO"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "📅 Calendario de publicación:"
echo "   🤖 Lunes     → Automation Mondays"
echo "   📈 Martes    → Martes de Transformación"
echo "   🎯 Miércoles → Miércoles de Éxito"
echo "   🛠️  Jueves   → Jueves de Herramientas"
echo "   🚀 Viernes   → Viernes del Futuro"
echo "   💡 Sábado    → Sábado Estratégico"
echo "   ❌ Domingo   → (sin publicación)"
echo ""
echo "⏰ Hora de publicación: 9:00 AM (ajusta en la variable CRON_CMD)"
echo ""
echo "📊 Logs:"
echo "   - Posts: logs/androide_posts.log"
echo "   - Cron:  logs/androide_cron.log"
echo ""
echo "🔑 REQUISITOS PENDIENTES:"
echo "   [ ] Configurar LINKEDIN_ACCESS_TOKEN"
echo "   [ ] Configurar LINKEDIN_PERSON_ID en el script"
echo "   [ ] Revisar primer post generado"
echo "   [ ] Aprobar antes de activar cron"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
