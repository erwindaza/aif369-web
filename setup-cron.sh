#!/bin/bash
# Setup cron jobs para LinkedIn Bot v2 - El Androide
# Horarios: 8:30 AM (L-V), 14:00 + 18:00 (S-D)

REPO="/Users/macbookpro/dev/aif369-web"
BOT="$REPO/linkedin-bot-v2.py"
LOG_DIR="$REPO/logs"
CRON_ID="el-androide-linkedin-bot"

# Crear directorio de logs
mkdir -p "$LOG_DIR"

# Función para remover crons anteriores
remove_old_crons() {
    echo "🧹 Limpiando crons anteriores..."
    crontab -l 2>/dev/null | grep -v "$CRON_ID" | crontab - 2>/dev/null
}

# Función para agregar cron
add_cron() {
    local schedule=$1
    local description=$2
    local entry="$schedule cd $REPO && python3 $BOT >> $LOG_DIR/cron.log 2>&1 # $CRON_ID - $description"

    (crontab -l 2>/dev/null; echo "$entry") | crontab -
    echo "✅ Agregado: $description ($schedule)"
}

# Remover anteriores
remove_old_crons

echo ""
echo "📝 Configurando crons nuevos..."
echo ""

# Lunes-Viernes 8:30 AM
add_cron "30 8 * * 1-5" "Lunes-Viernes 8:30 AM"

# Sábado 14:00 (2 PM)
add_cron "0 14 * * 6" "Sábado 14:00"

# Sábado 18:00 (6 PM)
add_cron "0 18 * * 6" "Sábado 18:00"

# Domingo 14:00 (2 PM)
add_cron "0 14 * * 0" "Domingo 14:00"

# Domingo 18:00 (6 PM)
add_cron "0 18 * * 0" "Domingo 18:00"

echo ""
echo "="*60
echo "✅ CRONS CONFIGURADOS:"
echo "   📅 Lunes-Viernes: 8:30 AM"
echo "   📅 Sábado: 14:00 y 18:00"
echo "   📅 Domingo: 14:00 y 18:00"
echo ""
echo "Ver crons: crontab -l"
echo "Ver logs: tail -f $LOG_DIR/cron.log"
echo "Stats: $LOG_DIR/bot-stats.json"
echo "="*60
