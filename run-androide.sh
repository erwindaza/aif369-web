#!/bin/bash
# ════════════════════════════════════════════════════════════════════════
# 🤖 EL ANDROIDE — Runner Seguro
#
# Uso: bash run-androide.sh
#
# Te pedirá la API key interactivamente (sin mostrarla)
# La clave NUNCA se guarda en archivos
# ════════════════════════════════════════════════════════════════════════

set -euo pipefail

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "🤖 EL ANDROIDE — Generador de Posts con Gemini"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 1. Pedir API key de forma segura (sin mostrar lo que escribe)
# ─────────────────────────────────────────────────────────────────────────

echo "🔑 Configuración de Seguridad:"
echo "   La API key se carga de .env.local (seguro, en .gitignore)"
echo ""

# Cargar .env.local si existe
if [ -f ".env.local" ]; then
    echo "✅ Cargando credenciales de .env.local"
    set -a
    source .env.local
    set +a
    echo ""
else
    echo "⚠️  .env.local no encontrado"
    read -rsp "Ingresa tu GEMINI_API_KEY: " GEMINI_API_KEY
    export GEMINI_API_KEY="$GEMINI_API_KEY"
    echo ""
    echo ""
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ ERROR: API key no puede estar vacía"
    exit 1
fi

# ─────────────────────────────────────────────────────────────────────────
# 2. Activar venv
# ─────────────────────────────────────────────────────────────────────────

echo "⚙️  Activando virtual environment..."
source .venv/bin/activate

# ─────────────────────────────────────────────────────────────────────────
# 3. Exportar variables (solo en memoria, no en disco)
# ─────────────────────────────────────────────────────────────────────────

export GEMINI_API_KEY="$GEMINI_API_KEY"
export GCP_PROJECT="830685315001"

echo "✅ Variables configuradas en memoria (session)"
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 4. Ejecutar El Androide
# ─────────────────────────────────────────────────────────────────────────

echo "🚀 Iniciando El Androide..."
echo "════════════════════════════════════════════════════════════════════════"
echo ""

python backend/androide_gemini_mcp.py

# ─────────────────────────────────────────────────────────────────────────
# 5. Cleanup (limpiar variables de memoria)
# ─────────────────────────────────────────────────────────────────────────

unset GEMINI_API_KEY
unset GCP_PROJECT

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "✅ El Androide completó"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Posts guardados en: logs/androide_dual_posts.log"
echo ""
