#!/bin/bash
# ════════════════════════════════════════════════════════════════════════
# 📅 GENERAR POSTS PARA LA SEMANA (LUNES-SÁBADO)
# ════════════════════════════════════════════════════════════════════════

set -euo pipefail

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "📅 EL ANDROIDE — Generador Semanal de Posts"
echo "════════════════════════════════════════════════════════════════════════"
echo ""

# Cargar .env.local si existe
if [ -f ".env.local" ]; then
    echo "✅ Cargando GEMINI_API_KEY de .env.local"
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

source .venv/bin/activate

# Array de días
DIAS=(
    "0:🤖 Automation Mondays:Problem-Solution: Automatizar procesos empresariales:Urgente, provocador, ROI-focused:Agenda demo gratuita"
    "1:📈 Martes de Transformación:Case Study: Resultados reales de clientes:Social proof, números concretos:Mira cómo lo hicimos"
    "2:🎯 Miércoles de Éxito:Testimonios y success stories:Inspirador, aspiracional:Sé el próximo caso de éxito"
    "3:🛠️ Jueves de Herramientas:Tip/Hack práctico de IA + Automatización:Educativo pero con CTA:Descubre cómo en nuestra consulta"
    "4:🚀 Viernes del Futuro:Trend/Vision + Limited Time Offer:Urgencia, FOMO positivo:Únete a las empresas que escalan con IA"
    "5:💡 Sábado Estratégico:Thought Leadership / Deep Insight:Autoridad, reflexión estratégica:Hablemos de tu estrategia"
)

# Crear archivo de salida
OUTPUT_FILE="posts-semana-$(date +%Y%m%d).txt"
> "$OUTPUT_FILE"

python3 << 'PYEOF'
import sys
import os
import json

sys.path.insert(0, '/Users/macbookpro/dev/aif369-web/backend')
from androide_mcp_server import PostValidator
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY no configurado")
    sys.exit(1)

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

# System prompt (v2.0 - TECH EMERGENTE)
with open('/Users/macbookpro/dev/aif369-web/scripts/androide-system-prompt-v2.md') as f:
    system_prompt = f.read()

dias = [
    {"num": 0, "es": "🤖 AI Agents Monday", "pilar": "Autonomous AI Agents: Multi-step reasoning, tool use, memory", "tono": "Experto, directo, competitive threat", "cta": "Consulta gratuita: ¿Está tu empresa lista?"},
    {"num": 1, "es": "📈 LLM Implementation Tuesday", "pilar": "LLMs en producción: Fine-tuning + RAG", "tono": "Case study técnico, números concretos", "cta": "Descubre arquitectura enterprise"},
    {"num": 2, "es": "🎯 GenAI Success Wednesday", "pilar": "Generative AI: Code, Content, Vision, Data", "tono": "Success story, resultados medibles", "cta": "Sé el próximo caso de éxito"},
    {"num": 3, "es": "🛠️ Emerging Tech Toolkit Thursday", "pilar": "Tools/Frameworks/Techniques de punta (LangChain, Vector DBs, etc)", "tono": "Educativo técnico, actionable", "cta": "Implementemos en tu stack"},
    {"num": 4, "es": "🚀 AI Frontiers Friday", "pilar": "Tendencias emergentes (Research, Announcements, Vision)", "tono": "Urgencia, ventana de oportunidad", "cta": "Asegura tu posición"},
    {"num": 5, "es": "💡 AI Architecture Saturday", "pilar": "Thought Leadership: RAG vs Fine-tuning, Cost optimization, Evaluation", "tono": "Autoridad técnica, realidad vs mito", "cta": "Hablemos de tu arquitectura AI"}
]

validator = PostValidator()
posts_output = []

print("📅 GENERANDO POSTS PARA LA SEMANA (LUNES-SÁBADO)\n")
print("=" * 80)

for dia in dias:
    print(f"\n📝 Generando: {dia['es']}")

    prompt = f"""{system_prompt}

Genera un post de LinkedIn para {dia['es']}.

Pilar: {dia['pilar']}
Tono: {dia['tono']}
CTA: {dia['cta']}

REQUISITOS:
- 150-200 palabras exactas
- Hook fuerte
- Problema + Solución
- CTA específico
- Máx 3 emojis
- SIN hashtags en cuerpo
- 100% español
- Menciona precios si es relevante

Genera el post AHORA (solo el post, sin explicaciones):
"""

    response = model.generate_content(prompt)
    post = response.text.strip()

    # Validar
    validation = validator.validate(post, dia)

    if validation['is_valid']:
        status = f"✅ Score: {validation['score']}/100"
    else:
        status = f"⚠️  Score: {validation['score']}/100 (aceptable)"

    print(f"   {status}")

    posts_output.append({
        "dia": dia['es'],
        "post": post,
        "score": validation['score'],
        "palabras": validation['word_count']
    })

print("\n" + "=" * 80)
print(f"\n✅ SEMANA COMPLETA GENERADA ({len(posts_output)} posts)")
print(f"\n📁 Guardando en: posts-semana.txt\n")

# Guardar a archivo
with open('posts-semana.txt', 'w') as f:
    f.write("=" * 80 + "\n")
    f.write("📅 POSTS SEMANALES - EL ANDROIDE\n")
    f.write("=" * 80 + "\n\n")

    for post_data in posts_output:
        f.write(f"📅 {post_data['dia']}\n")
        f.write(f"   Score: {post_data['score']}/100 | Palabras: {post_data['palabras']}\n")
        f.write("-" * 80 + "\n")
        f.write(post_data['post'] + "\n")
        f.write("-" * 80 + "\n\n")

# Mostrar resumen
print("RESUMEN DE LA SEMANA:\n")
for i, post_data in enumerate(posts_output, 1):
    print(f"{i}. {post_data['dia']:30} | Score: {post_data['score']:3}/100 | {post_data['palabras']:3} palabras")

print(f"\n📁 Archivo: posts-semana.txt")

PYEOF

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "✅ POSTS SEMANALES GENERADOS"
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "📁 Archivo: posts-semana.txt"
echo ""
echo "Próximo paso: Configurar publicación automática en LinkedIn"
echo ""
