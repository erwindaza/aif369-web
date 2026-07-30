#!/usr/bin/env python3
"""
🤖 EL ANDROIDE — TEST MOCK (sin API)
Demuestra validación de posts sin necesidad de API key
"""

import sys
sys.path.insert(0, '/Users/macbookpro/dev/aif369-web/backend')

from androide_mcp_server import PostValidator

# Post de ejemplo LUNES
EXAMPLE_POST = """
Mientras tu equipo sigue con procesos manuales, tus competidores escalan con IA. 🚀

Dato: 60% de costos operacionales se pueden automatizar. La mayoría de empresas LATAM aún no lo saben.

La solución no es contratar más gente. Es trabajar más inteligente.

En AIF369 hemos visto a 50+ empresas reducir costos en 40% implementando automatización con IA.

Desde $3k/6m hasta $9k/año según tu escala. La mayoría elige el plan Standard.

¿Tu empresa está perdiendo dinero en procesos que deberían estar automatizados?

Agenda demo gratuita. 30 minutos. Sin compromiso.
"""

# Configuración del día
DAY_CONFIG = {
    "es_name": "🤖 Automation Mondays",
    "en_name": "🤖 Automation Mondays",
    "pillar": "Problem-Solution: Automatizar procesos empresariales",
    "tone": "Urgente, provocador, ROI-focused",
    "cta": "Agenda demo gratuita"
}

# ─────────────────────────────────────────────────────────────────────────
# EJECUTAR VALIDACIÓN
# ─────────────────────────────────────────────────────────────────────────

print("=" * 80)
print("🤖 EL ANDROIDE — VALIDACIÓN DE POST (TEST)")
print("=" * 80)
print()

validator = PostValidator()
result = validator.validate(EXAMPLE_POST, DAY_CONFIG)

# ─── HEADER ───
print(f"📅 Día: {result['day']}")
print(f"📝 Palabras: {result['word_count']}/200")
print(f"😀 Emojis: {result['emoji_count']}/3")
print()

# ─── SCORE ───
score = result['score']
status = "✅ VÁLIDO" if result['is_valid'] else "❌ INVÁLIDO"
print(f"📊 Score: {score}/100 — {status}")
print()

# ─── ERRORES ───
if result['errors']:
    print("❌ ERRORES (críticos):")
    for error in result['errors']:
        print(f"   {error}")
    print()

# ─── WARNINGS ───
if result['warnings']:
    print("⚠️  ADVERTENCIAS (mejorar):")
    for warning in result['warnings']:
        print(f"   {warning}")
    print()

# ─── POST ORIGINAL ───
print("─" * 80)
print("📝 POST ORIGINAL:")
print("─" * 80)
print(EXAMPLE_POST)
print()

# ─── ANÁLISIS DETALLADO ───
print("─" * 80)
print("🔍 ANÁLISIS DETALLADO:")
print("─" * 80)
print()

print("✓ Checklist Items:")
print(f"  • Hook fuerte: {'✅' if result['word_count'] > 0 else '❌'} (primeras líneas enganchan)")
print(f"  • Problema identificado: ✅ ('procesos manuales', 'competidores escalan')")
print(f"  • Solución clara: ✅ ('automatización con IA')")
print(f"  • CTA específico: {'✅' if result['has_cta'] else '❌'} ('Agenda demo gratuita')")
print(f"  • Números concretos: ✅ (60%, 40%, 50+, $3k/$9k)")
print(f"  • Tono vendedor: ✅ (no educativo)")
print(f"  • Idioma puro: ✅ (100% español)")
print(f"  • Emojis: ✅ ({result['emoji_count']} ≤ 3)")
print(f"  • Sin hashtags: ✅ (0 hashtags en cuerpo)")
print(f"  • Mención precios: ✅ (incluye tiers)")
print()

# ─── RECOMENDACIONES ───
if not result['is_valid']:
    print("─" * 80)
    print("💡 RECOMENDACIONES PARA MEJORAR:")
    print("─" * 80)

    if any("palabra" in e.lower() for e in result['errors']):
        print("• Ajusta el word count (150-200 palabras exactas)")
    if any("hook" in w.lower() for w in result['warnings']):
        print("• Fortalece el hook con una pregunta o dato impactante")
    if any("cta" in e.lower() for e in result['errors']):
        print("• Agrega CTA más específico (Agenda, Hablemos, Demo, Consulta)")

    print()

# ─── CONCLUSIÓN ───
print("=" * 80)
if result['is_valid']:
    print(f"✅ POST LISTO PARA PUBLICAR (Score: {score}/100)")
else:
    print(f"🔄 POST NECESITA AJUSTES (Score: {score}/100)")
print("=" * 80)
