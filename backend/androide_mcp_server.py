#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════╗
║  EL ANDROIDE — MCP SERVER                                                  ║
║  Model Context Protocol Implementation                                      ║
║  ────────────────────────────────────────────────────────────────────────  ║
║  Validación de posts + Integración con Gemini API + Error Recovery         ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
from typing import Dict, List, Any
from datetime import datetime
import re
import google.generativeai as genai

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN GEMINI
# ─────────────────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

# System Prompt Global para El Androide
ANDROIDE_SYSTEM_PROMPT = open(
    "/Users/macbookpro/dev/aif369-web/scripts/androide-system-prompt.md"
).read()

# ─────────────────────────────────────────────────────────────────────────
# VALIDACIÓN DE POSTS
# ─────────────────────────────────────────────────────────────────────────

class PostValidator:
    """Valida posts contra checklist de El Androide."""

    VALIDATION_RULES = {
        "min_words": 150,
        "max_words": 200,
        "max_emojis": 3,
        "max_hashtags": 0,  # Sin hashtags en cuerpo
        "require_cta": True,
        "require_hook": True,
        "require_problem": True,
    }

    WEAK_CTAS = [
        "sígueme para más",
        "follow for more",
        "dame un like",
        "comparte esto",
        "share this",
    ]

    @staticmethod
    def validate(post: str, day_config: Dict) -> Dict[str, Any]:
        """Valida un post contra todas las reglas."""

        errors = []
        warnings = []
        score = 100

        # ─── Word Count ───
        words = len(post.split())
        if words < PostValidator.VALIDATION_RULES["min_words"]:
            errors.append(f"❌ Muy corto: {words} palabras (min: 150)")
            score -= 20
        elif words > PostValidator.VALIDATION_RULES["max_words"]:
            errors.append(f"❌ Muy largo: {words} palabras (max: 200)")
            score -= 20

        # ─── Emoji Count ───
        emoji_count = len(re.findall(r"[😀-🙏🌀-🗿🚀-🛿]", post))
        if emoji_count > PostValidator.VALIDATION_RULES["max_emojis"]:
            warnings.append(f"⚠️  {emoji_count} emojis (max: 3)")
            score -= 10

        # ─── Hashtags ───
        hashtags = len(re.findall(r"#\w+", post))
        if hashtags > 0:
            warnings.append(f"⚠️  {hashtags} hashtags en cuerpo (debe estar al final)")
            score -= 5

        # ─── CTA Analysis ───
        if PostValidator.VALIDATION_RULES["require_cta"]:
            has_cta = any(
                cta in post.lower() for cta in [
                    "agenda", "hablemos", "consulta", "demo",
                    "schedule", "talk", "consultation", "book"
                ]
            )
            if not has_cta:
                errors.append("❌ Sin CTA claro. Requiere: Agenda, Hablemos, Demo, etc.")
                score -= 30

            # Detectar CTAs débiles
            if any(weak in post.lower() for weak in PostValidator.WEAK_CTAS):
                errors.append("❌ CTA demasiado vago (ej: 'sígueme para más')")
                score -= 25

        # ─── Hook Analysis ───
        if PostValidator.VALIDATION_RULES["require_hook"]:
            lines = post.split("\n")
            first_line = lines[0] if lines else ""
            if len(first_line) < 15:
                warnings.append("⚠️  Hook débil. Primera línea < 15 caracteres")
                score -= 15

        # ─── Problem/Solution ───
        if PostValidator.VALIDATION_RULES["require_problem"]:
            problem_keywords = ["problema", "dolor", "issue", "problem", "lose"]
            solution_keywords = ["solución", "cómo", "automatización", "solution", "how"]

            has_problem = any(kw in post.lower() for kw in problem_keywords)
            has_solution = any(kw in post.lower() for kw in solution_keywords)

            if not has_problem:
                warnings.append("⚠️  No menciona problema/dolor cliente")
                score -= 10
            if not has_solution:
                warnings.append("⚠️  No menciona solución")
                score -= 10

        # ─── Language Check ───
        if re.search(r"\b[a-z]+\b\s+\b[a-z]+\b", post):  # Mix de idiomas
            if re.search(r"(español.*english|english.*español)", post.lower()):
                warnings.append("⚠️  Detectado mix de idiomas (debe ser 100% español)")
                score -= 10

        # ─── Resultado ───
        is_valid = len(errors) == 0 and score >= 70

        return {
            "is_valid": is_valid,
            "score": max(0, score),
            "errors": errors,
            "warnings": warnings,
            "word_count": words,
            "emoji_count": emoji_count,
            "has_cta": has_cta if PostValidator.VALIDATION_RULES["require_cta"] else None,
            "day": day_config.get("es_name", "Unknown"),
        }


# ─────────────────────────────────────────────────────────────────────────
# GENERACIÓN DE POSTS CON VALIDACIÓN
# ─────────────────────────────────────────────────────────────────────────

class AndroidePostGenerator:
    """Genera posts con validación automática."""

    def __init__(self):
        self.client = Anthropic()
        self.max_retries = 3
        self.validator = PostValidator()

    def generate_with_validation(self, day_config: Dict) -> Dict[str, Any]:
        """Genera post y valida. Si falla, regenera."""

        for attempt in range(self.max_retries):
            print(f"\n🤖 Intento {attempt + 1}/{self.max_retries}...")

            # Generar
            post = self._generate_raw(day_config)

            # Validar
            validation = self.validator.validate(post, day_config)

            if validation["is_valid"]:
                print(f"✅ Post válido (Score: {validation['score']}/100)")
                return {
                    "post": post,
                    "validation": validation,
                    "success": True,
                    "attempts": attempt + 1,
                }

            # Si falla, mostrar errores y regenerar
            print(f"⚠️  Validación falló (Score: {validation['score']}/100)")
            for error in validation["errors"]:
                print(f"   {error}")
            for warning in validation["warnings"]:
                print(f"   {warning}")

            if attempt < self.max_retries - 1:
                print(f"🔄 Regenerando con feedback...")
                # Pasar feedback de validación al siguiente intento
                day_config["validation_feedback"] = validation

        # Si llega aquí, falló después de max_retries
        return {
            "post": post,
            "validation": validation,
            "success": False,
            "attempts": self.max_retries,
            "error": f"No se logró generar post válido después de {self.max_retries} intentos",
        }

    def _generate_raw(self, day_config: Dict) -> str:
        """Genera post raw sin validación."""

        feedback = day_config.get("validation_feedback", {})
        feedback_prompt = ""

        if feedback:
            feedback_prompt = f"""
FEEDBACK DE VALIDACIÓN (intento anterior falló):
- Errores: {feedback.get('errors', [])}
- Advertencias: {feedback.get('warnings', [])}
- Score: {feedback.get('score', 0)}/100

CORRIGE ESTOS ERRORES EN LA REGENERACIÓN:
"""

        prompt = f"""
{feedback_prompt}

Genera un post de LinkedIn para {day_config['es_name']}.

Pilar: {day_config['pillar']}
Tono: {day_config['tone']}
CTA: {day_config['cta']}

REQUISITOS OBLIGATORIOS:
- 150-200 palabras exactas
- Hook fuerte en primera línea
- Menciona PROBLEMA y SOLUCIÓN
- CTA claro y específico (ej: "Agenda demo", "Hablemos")
- Máx 3 emojis
- SIN hashtags en el cuerpo
- 100% español natural (NO Spanglish)
- Tono: vendedor directo (no educador)

OPCIONAL: Menciona precios si es relevante:
- Desde $3k/6m hasta $9k/año
- Highlight: "La mayoría elige el plan Standard ($9k/año)"

Genera el post AHORA:
"""

        message = self.client.messages.create(
            model="claude-opus-4-8",
            max_tokens=500,
            system=ANDROIDE_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return message.content[0].text


# ─────────────────────────────────────────────────────────────────────────
# MCP TOOLS (Lo que expone el servidor)
# ─────────────────────────────────────────────────────────────────────────

def mcp_generate_post(day_config: Dict) -> Dict:
    """MCP Tool: Generar post con validación."""
    generator = AndroidePostGenerator()
    result = generator.generate_with_validation(day_config)
    return result


def mcp_validate_post(post: str, day_config: Dict) -> Dict:
    """MCP Tool: Validar un post existente."""
    validator = PostValidator()
    validation = validator.validate(post, day_config)
    return validation


def mcp_get_system_prompt() -> str:
    """MCP Tool: Obtener system prompt."""
    return ANDROIDE_SYSTEM_PROMPT


# ─────────────────────────────────────────────────────────────────────────
# MCP SERVER DEFINITION
# ─────────────────────────────────────────────────────────────────────────

MCP_SERVER_SCHEMA = {
    "name": "androide-mcp",
    "version": "1.0.0",
    "description": "El Androide MCP Server — Post Generation + Validation",
    "tools": [
        {
            "name": "generate_post",
            "description": "Genera un post de LinkedIn con validación automática",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "day_config": {
                        "type": "object",
                        "description": "Configuración del día (es_name, en_name, pillar, tone, cta)",
                        "properties": {
                            "es_name": {"type": "string"},
                            "en_name": {"type": "string"},
                            "pillar": {"type": "string"},
                            "tone": {"type": "string"},
                            "cta": {"type": "string"},
                        },
                        "required": ["es_name", "pillar", "tone", "cta"]
                    }
                },
                "required": ["day_config"]
            }
        },
        {
            "name": "validate_post",
            "description": "Valida un post contra checklist de El Androide",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "post": {"type": "string", "description": "Contenido del post"},
                    "day_config": {"type": "object", "description": "Configuración del día"}
                },
                "required": ["post", "day_config"]
            }
        },
        {
            "name": "get_system_prompt",
            "description": "Obtiene el system prompt de El Androide",
            "inputSchema": {"type": "object", "properties": {}}
        }
    ]
}


# ─────────────────────────────────────────────────────────────────────────
# MAIN / TEST
# ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🤖 EL ANDROIDE MCP SERVER")
    print("=" * 70)
    print(json.dumps(MCP_SERVER_SCHEMA, indent=2, ensure_ascii=False))
    print("=" * 70)

    # Test: Generar post lunes con validación
    print("\n📅 TEST: Generando post LUNES con validación...")

    day_config = {
        "es_name": "🤖 Automation Mondays",
        "en_name": "🤖 Automation Mondays",
        "pillar": "Problem-Solution: Automatizar procesos empresariales",
        "tone": "Urgente, provocador, ROI-focused",
        "cta": "Agenda demo gratuita"
    }

    result = mcp_generate_post(day_config)

    print(f"\n✅ Success: {result['success']}")
    print(f"📊 Attempts: {result['attempts']}")
    print(f"📝 Post:\n{result['post']}")
    print(f"\n✓ Validation Score: {result['validation']['score']}/100")
    if result['validation']['errors']:
        print(f"❌ Errors: {result['validation']['errors']}")
    if result['validation']['warnings']:
        print(f"⚠️  Warnings: {result['validation']['warnings']}")
