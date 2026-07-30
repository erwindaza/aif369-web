#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════╗
║  EL ANDROIDE — MCP SERVER (GEMINI OPTIMIZADO)                             ║
║  ────────────────────────────────────────────────────────────────────────  ║
║  Versión económica usando Google Gemini API (FREE/ULTRA BARATO)           ║
║  Validación automática + Generación de posts + Error Recovery             ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
from typing import Dict, Any
import google.generativeai as genai
import sys

sys.path.insert(0, '/Users/macbookpro/dev/aif369-web/backend')
from androide_mcp_server import PostValidator

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN GEMINI
# ─────────────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    print("❌ ERROR: GEMINI_API_KEY no configurado")
    print("   Obtén en: https://aistudio.google.com/apikey")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# System Prompt
ANDROIDE_SYSTEM_PROMPT = open(
    "/Users/macbookpro/dev/aif369-web/scripts/androide-system-prompt.md"
).read()


# ─────────────────────────────────────────────────────────────────────────
# GENERADOR CON VALIDACIÓN
# ─────────────────────────────────────────────────────────────────────────

class AndroideGeminiGenerator:
    """Genera posts con Gemini + validación automática."""

    def __init__(self):
        self.validator = PostValidator()
        self.max_retries = 3

    def generate_with_validation(self, day_config: Dict) -> Dict[str, Any]:
        """Genera post con Gemini, valida y regenera si es necesario."""

        for attempt in range(self.max_retries):
            print(f"\n🤖 Intento {attempt + 1}/{self.max_retries}...")

            # Generar con Gemini
            post = self._generate_with_gemini(day_config)

            # Validar
            validation = self.validator.validate(post, day_config)

            if validation["is_valid"]:
                print(f"✅ Post válido (Score: {validation['score']}/100)")
                return {
                    "post": post,
                    "validation": validation,
                    "success": True,
                    "attempts": attempt + 1,
                    "model": "gemini-1.5-flash",
                }

            # Si falla, mostrar y regenerar
            print(f"⚠️  Score: {validation['score']}/100")
            for error in validation["errors"]:
                print(f"   {error}")

            if attempt < self.max_retries - 1:
                day_config["validation_feedback"] = validation
                print(f"🔄 Regenerando...")

        # Falló después de max_retries
        return {
            "post": post,
            "validation": validation,
            "success": False,
            "attempts": self.max_retries,
            "error": f"No se logró post válido tras {self.max_retries} intentos",
            "model": "gemini-1.5-flash",
        }

    def _generate_with_gemini(self, day_config: Dict) -> str:
        """Genera post con Gemini API."""

        feedback = day_config.get("validation_feedback", {})
        feedback_text = ""

        if feedback:
            feedback_text = f"""
FEEDBACK (intento anterior):
- Score: {feedback.get('score', 0)}/100
- Errores: {feedback.get('errors', [])}
- Corrige estos errores en esta regeneración.
"""

        prompt = f"""
{ANDROIDE_SYSTEM_PROMPT}

{feedback_text}

GENERAR POST PARA: {day_config['es_name']}
Pilar: {day_config['pillar']}
Tono: {day_config['tone']}
CTA: {day_config['cta']}

REQUISITOS (NON-NEGOTIABLE):
✓ 150-200 palabras exactas
✓ Hook fuerte (primera línea enganche)
✓ Problema + Solución
✓ CTA específico (Agenda, Hablemos, Demo)
✓ Máx 3 emojis
✓ SIN hashtags en cuerpo
✓ 100% español natural
✓ Tono: vendedor (no educador)

MENCIONA PRECIOS SI ES RELEVANTE:
- $3k/6m, $6k/1año, $9k/1año
- Destaca: "La mayoría elige Standard ($9k/año)"

RESPONDE SOLO CON EL POST (sin explicaciones):
"""

        response = model.generate_content(prompt)
        return response.text.strip()


# ─────────────────────────────────────────────────────────────────────────
# MAIN / DEMO
# ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 80)
    print("🤖 EL ANDROIDE — GEMINI MCP (ECONÓMICO)")
    print("=" * 80)
    print()
    print(f"💰 Costo: GRATIS (Gemini free tier)")
    print(f"⚡ Modelo: gemini-1.5-flash (super rápido)")
    print()

    # Config LUNES
    day_config = {
        "es_name": "🤖 Automation Mondays",
        "pillar": "Problem-Solution: Automatizar procesos empresariales",
        "tone": "Urgente, provocador, ROI-focused",
        "cta": "Agenda demo gratuita"
    }

    print(f"📅 Generando post: {day_config['es_name']}")
    print("=" * 80)
    print()

    generator = AndroideGeminiGenerator()
    result = generator.generate_with_validation(day_config)

    print()
    print("=" * 80)
    print(f"✅ SUCCESS: {result['success']}")
    print(f"📊 Attempts: {result['attempts']}")
    print(f"🤖 Model: {result['model']}")
    print("=" * 80)
    print()

    if result["success"]:
        print("✅ POST FINAL (LISTO PARA LINKEDIN):")
    else:
        print("❌ POST (NECESITA AJUSTES):")

    print("-" * 80)
    print(result["post"])
    print("-" * 80)
    print()

    validation = result["validation"]
    print(f"📊 Score: {validation['score']}/100")
    print(f"📝 Palabras: {validation['word_count']}")
    print(f"😀 Emojis: {validation['emoji_count']}/3")

    if result["success"]:
        print()
        print("=" * 80)
        print("🚀 LISTO PARA PUBLICAR EN LINKEDIN")
        print("=" * 80)
