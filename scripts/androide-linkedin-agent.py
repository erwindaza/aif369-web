#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════╗
║  EL ANDROIDE — LinkedIn Sales Agent                                       ║
║  Publicador automático de contenido de ventas (Lunes-Sábado)              ║
║  Genera posts con hooks atractivos + CTAs para cerrar deals               ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import requests
from datetime import datetime
from anthropic import Anthropic

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────

LINKEDIN_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")  # Obten de LinkedIn OAuth
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Schedule de publicación (lunes=0, domingo=6)
PUBLISHING_SCHEDULE = {
    0: {  # LUNES
        "es_name": "🤖 Automation Mondays",
        "en_name": "🤖 Automation Mondays",
        "pillar": "Problem-Solution: Automatizar procesos empresariales",
        "tone": "Urgente, provocador, ROI-focused",
        "cta": "Agenda demo gratuita"
    },
    1: {  # MARTES
        "es_name": "📈 Martes de Transformación",
        "en_name": "📈 Transformation Tuesday",
        "pillar": "Case Study: Resultados reales de clientes",
        "tone": "Social proof, números concretos",
        "cta": "Mira cómo lo hicimos"
    },
    2: {  # MIÉRCOLES
        "es_name": "🎯 Miércoles de Éxito",
        "en_name": "🎯 Win Wednesday",
        "pillar": "Testimonios y success stories",
        "tone": "Inspirador, aspiracional",
        "cta": "Sé el próximo caso de éxito"
    },
    3: {  # JUEVES
        "es_name": "🛠️ Jueves de Herramientas",
        "en_name": "🛠️ Toolkit Thursday",
        "pillar": "Tip/Hack práctico de IA + Automatización",
        "tone": "Educativo pero con CTA",
        "cta": "Descubre cómo en nuestra consulta"
    },
    4: {  # VIERNES
        "es_name": "🚀 Viernes del Futuro",
        "en_name": "🚀 Future Friday",
        "pillar": "Trend/Vision + Limited Time Offer",
        "tone": "Urgencia, FOMO positivo",
        "cta": "Únete a las empresas que escalan con IA"
    },
    5: {  # SÁBADO
        "es_name": "💡 Sábado Estratégico",
        "en_name": "💡 Strategic Saturday",
        "pillar": "Thought Leadership / Deep Insight",
        "tone": "Autoridad, reflexión estratégica",
        "cta": "Hablemos de tu estrategia"
    }
}

# Targets por plan
PRICING_TIERS = {
    "basic": {"price": "$3,000 USD", "duration": "6 meses"},
    "premium": {"price": "$6,000 USD", "duration": "1 año"},
    "standard": {"price": "$9,000 USD", "duration": "1 año"}
}

# ─────────────────────────────────────────────────────────────────────────
# ANTHROPIC CLIENT (Claude)
# ─────────────────────────────────────────────────────────────────────────

client = Anthropic()

def generate_linkedin_post(day_config: dict) -> str:
    """Genera un post de LinkedIn automático usando Claude."""

    prompt = f"""
Eres El Androide, Head of Sales de AIF369 (empresa de consultoría en IA, automatización y transformación digital).

CONTEXTO DEL DÍA:
- Nombre: {day_config['es_name']} / {day_config['en_name']}
- Pilar: {day_config['pillar']}
- Tono: {day_config['tone']}
- CTA: {day_config['cta']}

INSTRUCCIONES:
1. Genera un post de LinkedIn BILINGÜE (español + inglés separados por ——— )
2. Post en ESPAÑOL: 150-200 palabras, hook emocional fuerte, 2-3 emojis máximo
3. Post en INGLÉS: 150-200 palabras, hook emocional fuerte, 2-3 emojis máximo
4. Ambos DEBEN terminar con CTA claro (Agenda demo, Mira cómo, etc.)
5. Menciona planes de precios si es relevante:
   - Básico: $3,000 USD / 6 meses
   - Premium: $6,000 USD / año
   - Standard: $9,000 USD / año (HIGHLIGHTED)
6. NO escribas hashtags (Los agregaremos después)
7. Format:
   [SPANISH]
   {tu post en español}

   ———————————————————————————————

   [ENGLISH]
   {tu post en inglés}

EJEMPLOS DE HOOKS FUERTES:
- "La mayoría de empresas pierden 60% en costos operacionales porque..."
- "Mientras competidores escalan con IA, tú sigues haciendo esto manualmente..."
- "El dato que nadie te dice sobre automatización..."

Genera el post AHORA:
"""

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def post_to_linkedin(content: str, day_name: str) -> bool:
    """Publica el contenido en LinkedIn (requiere token OAuth)."""

    if not LINKEDIN_TOKEN:
        print(f"⚠️  LINKEDIN_TOKEN no configurado. Mock publish: {day_name}")
        print(f"Content:\n{content}\n")
        return True  # Mock success

    try:
        # LinkedIn API v2 endpoint
        url = "https://api.linkedin.com/v2/posts"
        headers = {
            "Authorization": f"Bearer {LINKEDIN_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "author": "urn:li:person:{LINKEDIN_PERSON_ID}",  # Tu LinkedIn ID
            "commentary": content,
            "visibility": "PUBLIC"
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 201:
            print(f"✅ Post publicado en LinkedIn ({day_name})")
            return True
        else:
            print(f"❌ Error LinkedIn API: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error posting to LinkedIn: {e}")
        return False


def run_daily_publisher():
    """Ejecuta el publicador automático (debe correr diariamente)."""

    today = datetime.now().weekday()

    if today == 6:  # Domingo: no publicar
        print("Domingo: Sin publicaciones programadas")
        return

    day_config = PUBLISHING_SCHEDULE[today]

    print(f"\n{'='*70}")
    print(f"📅 GENERANDO POST: {day_config['es_name']} / {day_config['en_name']}")
    print(f"{'='*70}\n")

    # Generar post
    print("🤖 Generando contenido con Claude...")
    post_content = generate_linkedin_post(day_config)

    print(f"\n📝 POST GENERADO:\n{post_content}\n")

    # Publicar
    print("📤 Publicando en LinkedIn...")
    success = post_to_linkedin(post_content, day_config['es_name'])

    if success:
        # Guardar en logs
        with open("logs/androide_posts.log", "a") as f:
            f.write(f"\n[{datetime.now().isoformat()}] {day_config['es_name']}\n{post_content}\n")
        print(f"✅ Publicación completada")
    else:
        print(f"❌ Fallo en publicación")


if __name__ == "__main__":
    run_daily_publisher()
