#!/bin/bash
# ════════════════════════════════════════════════════════════════════════
# 🔍 Verificar Modelos Disponibles de Gemini API
# ════════════════════════════════════════════════════════════════════════

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "🔍 MODELOS DISPONIBLES EN GEMINI API"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

read -rsp "Ingresa tu GEMINI_API_KEY: " GEMINI_API_KEY
echo ""
echo ""

export GEMINI_API_KEY="$GEMINI_API_KEY"

python3 << 'PYEOF'
import google.generativeai as genai
import os
import sys

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY no configurado")
    sys.exit(1)

genai.configure(api_key=api_key)

try:
    models = genai.list_models()

    print("✅ MODELOS DISPONIBLES:\n")

    available_models = []
    for model in models:
        try:
            model_name = str(model.name).replace("models/", "")
            available_models.append(model_name)
            print(f"  ✓ {model_name}")
        except:
            pass

    print("")
    print("════════════════════════════════════════════════════════════════════════")
    print(f"Total: {len(available_models)} modelos disponibles")
    print("════════════════════════════════════════════════════════════════════════")
    print("")

    if available_models:
        print("📝 RECOMENDACIÓN PARA EL ANDROIDE:")
        print(f"   Usa: {available_models[0]}")

        flash_models = [m for m in available_models if "flash" in m.lower()]
        if flash_models:
            print(f"   ⭐ Mejor (rápido/económico): {flash_models[0]}")

except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    sys.exit(1)
PYEOF
