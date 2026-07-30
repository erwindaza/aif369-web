#!/bin/bash
# ════════════════════════════════════════════════════════════════════════
# DUAL-MARKET CRON SETUP
# El Androide + The Android — Publicador automático multinivel
#
# Mañana (9 AM CET):   The Android (ENGLISH) → Europa
# Tarde (2 PM UTC-5):  El Androide (ESPAÑOL) → LATAM + USA
#
# Ejecutar: bash scripts/setup-dual-market-cron.sh
# ════════════════════════════════════════════════════════════════════════

set -euo pipefail

PROJECT_ROOT="/Users/macbookpro/dev/aif369-web"
SCRIPT="${PROJECT_ROOT}/scripts/androide-dual-market-agent.py"
VENV="${PROJECT_ROOT}/.venv"

echo "════════════════════════════════════════════════════════════════════════"
echo " SETUP: EL ANDROIDE + THE ANDROID — Dual-Market Publishing"
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
# 2. Verificar credenciales (DUAL)
# ─────────────────────────────────────────────────────────────────────────

echo ""
echo "✓ Verificando credenciales..."

if [ -z "${ANDROIDE_LINKEDIN_TOKEN:-}" ]; then
    echo "⚠️  ANDROIDE_LINKEDIN_TOKEN no configurado (cuenta El Androide - ES)"
fi

if [ -z "${ANDROIDE_LINKEDIN_ID:-}" ]; then
    echo "⚠️  ANDROIDE_LINKEDIN_ID no configurado"
fi

if [ -z "${THE_ANDROID_LINKEDIN_TOKEN:-}" ]; then
    echo "⚠️  THE_ANDROID_LINKEDIN_TOKEN no configurado (cuenta The Android - EN)"
fi

if [ -z "${THE_ANDROID_LINKEDIN_ID:-}" ]; then
    echo "⚠️  THE_ANDROID_LINKEDIN_ID no configurado"
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
    echo "⚠️  GEMINI_API_KEY no configurado"
fi

# ─────────────────────────────────────────────────────────────────────────
# 3. Crear directorio de logs
# ─────────────────────────────────────────────────────────────────────────

mkdir -p "${PROJECT_ROOT}/logs"
touch "${PROJECT_ROOT}/logs/androide_dual_posts.log"
touch "${PROJECT_ROOT}/logs/androide_dual_cron.log"

echo "✓ Directorio de logs creado"

# ─────────────────────────────────────────────────────────────────────────
# 4. Setup dual cron jobs
# ─────────────────────────────────────────────────────────────────────────

echo ""
echo "✓ Configurando cron jobs (DUAL)..."

# CRON JOB 1: THE ANDROID (MAÑANA - 9 AM CET)
# Nota: Si tu servidor no está en CET, ajusta la hora UTC equivalente
# 9 AM CET = 8 AM GMT = 3 AM EST
CRON_MORNING="0 8 * * 0-5 cd ${PROJECT_ROOT} && source ${VENV}/bin/activate && python scripts/androide-dual-market-agent.py >> logs/androide_dual_cron.log 2>&1"

# CRON JOB 2: EL ANDROIDE (TARDE - 2 PM UTC-5)
# Nota: Si tu servidor está en UTC, son 7 PM UTC
CRON_AFTERNOON="0 19 * * 0-5 cd ${PROJECT_ROOT} && source ${VENV}/bin/activate && python scripts/androide-dual-market-agent.py >> logs/androide_dual_cron.log 2>&1"

# Agregar a crontab (sin duplicados)
EXISTING_CRON=$(crontab -l 2>/dev/null || true)

if echo "$EXISTING_CRON" | grep -q "androide-dual-market-agent"; then
    echo "   ℹ️  Cron jobs ya existen"
else
    {
        echo "$EXISTING_CRON"
        echo ""
        echo "# ═══════════════════════════════════════════════════════════"
        echo "# EL ANDROIDE + THE ANDROID — Dual-Market Publisher"
        echo "# ═══════════════════════════════════════════════════════════"
        echo ""
        echo "# THE ANDROID: 9 AM CET (Europa) — ENGLISH"
        echo "$CRON_MORNING"
        echo ""
        echo "# EL ANDROIDE: 2 PM UTC-5 (LATAM) — ESPAÑOL"
        echo "$CRON_AFTERNOON"
    } | crontab -

    echo "   ✅ Cron jobs agregados:"
    echo "      • 09:00 CET (morning) → The Android (ENGLISH - Europa)"
    echo "      • 14:00 UTC-5 (afternoon) → El Androide (ESPAÑOL - LATAM)"
fi

# ─────────────────────────────────────────────────────────────────────────
# 5. Test local
# ─────────────────────────────────────────────────────────────────────────

echo ""
echo "⚙️  Ejecutando test local..."
echo ""

source "${VENV}/bin/activate"
python "${SCRIPT}"

# ─────────────────────────────────────────────────────────════════════════
# 6. Resumen
# ─────────────────────════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo " ✅ SETUP COMPLETADO — DUAL-MARKET SYSTEM"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "📍 MERCADOS Y HORARIOS:"
echo ""
echo "   🌅 MAÑANA (9 AM CET):"
echo "      Account:  The Android"
echo "      Market:   Europe + Global"
echo "      Language: English"
echo "      Cron:     0 8 * * 0-5 (ajusta a tu timezone)"
echo ""
echo "   🌆 TARDE (2 PM UTC-5):"
echo "      Account:  El Androide"
echo "      Market:   LATAM + USA Hispano"
echo "      Language: Spanish"
echo "      Cron:     0 19 * * 0-5 (ajusta a tu timezone)"
echo ""
echo "📅 CALENDARIO (LUNES-SÁBADO, IDÉNTICO PARA AMBAS CUENTAS):"
echo "   🤖 Automation Mondays"
echo "   📈 Transformation Tuesday / Martes de Transformación"
echo "   🎯 Win Wednesday / Miércoles de Éxito"
echo "   🛠️  Toolkit Thursday / Jueves de Herramientas"
echo "   🚀 Future Friday / Viernes del Futuro"
echo "   💡 Strategic Saturday / Sábado Estratégico"
echo ""
echo "🔑 CREDENCIALES REQUERIDAS:"
echo "   [ ] ANDROIDE_LINKEDIN_TOKEN (El Androide - ES)"
echo "   [ ] ANDROIDE_LINKEDIN_ID"
echo "   [ ] THE_ANDROID_LINKEDIN_TOKEN (The Android - EN)"
echo "   [ ] THE_ANDROID_LINKEDIN_ID"
echo "   [ ] GEMINI_API_KEY"
echo ""
echo "📊 LOGS:"
echo "   - Posts:  logs/androide_dual_posts.log"
echo "   - Cron:   logs/androide_dual_cron.log"
echo ""
echo "⏰ TIMEZONE CONVERSION:"
echo "   Si tu servidor NO está en UTC:"
echo "   - CET (Central European Time) = UTC+1"
echo "   - UTC-5 (EST/Colombia time) = UTC-5"
echo "   - Ejemplo: Si servidor está en UTC:"
echo "     * 9 AM CET → 8 AM UTC"
echo "     * 2 PM UTC-5 → 7 PM UTC"
echo ""
echo "════════════════════════════════════════════════════════════════════════"
