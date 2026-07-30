#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════╗
║  EL ANDROIDE + THE ANDROID — Dual-Market LinkedIn Agent                   ║
║  ────────────────────────────────────────────────────────────────────────  ║
║  Mañana (9 AM CET):   The Android (EN) → Mercado Europeo                  ║
║  Tarde (2 PM UTC-5):  El Androide (ES) → LATAM + USA Hispano              ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import requests
from datetime import datetime
from anthropic import Anthropic

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DUAL-MARKET
# ─────────────────────────────────────────────────────────────────────────

ACCOUNTS = {
    "el_androide": {
        "name": "El Androide",
        "market": "LATAM + USA Hispano",
        "language": "Spanish",
        "linkedin_id": os.getenv("ANDROIDE_LINKEDIN_ID", ""),
        "linkedin_token": os.getenv("ANDROIDE_LINKEDIN_TOKEN", ""),
        "publish_hour": 14,  # 2 PM UTC-5
        "publish_minute": 0,
        "headline": "Chief AI Officer Advisory | Estrategia de IA, Automatización & Transformación Digital | Asesor CAIO"
    },
    "the_android": {
        "name": "The Android",
        "market": "Europe + Global",
        "language": "English",
        "linkedin_id": os.getenv("THE_ANDROID_LINKEDIN_ID", ""),
        "linkedin_token": os.getenv("THE_ANDROID_LINKEDIN_TOKEN", ""),
        "publish_hour": 9,  # 9 AM CET
        "publish_minute": 0,
        "headline": "Chief AI Officer Advisory | AI Strategy, Automation & Digital Transformation | CAIO Advisor"
    }
}

# Schedule (IDÉNTICO PARA AMBAS CUENTAS, PERO DIFERENTE IDIOMA)
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

# Targets por plan (BILINGÜE)
PRICING_TIERS = {
    "basic": {
        "es": {"price": "$3.000 USD", "duration": "6 meses"},
        "en": {"price": "$3,000 USD", "duration": "6 months"}
    },
    "premium": {
        "es": {"price": "$6.000 USD", "duration": "1 año"},
        "en": {"price": "$6,000 USD", "duration": "1 year"}
    },
    "standard": {
        "es": {"price": "$9.000 USD", "duration": "1 año"},
        "en": {"price": "$9,000 USD", "duration": "1 year"}
    }
}

# ─────────────────────────────────────────────────────────────────────────
# ANTHROPIC CLIENT
# ─────────────────────────────────────────────────────────────────────────

client = Anthropic()

def generate_linkedin_post(account: str, day_config: dict) -> str:
    """Genera un post de LinkedIn personalizado por cuenta/mercado."""

    account_info = ACCOUNTS[account]
    language = account_info["language"]
    market = account_info["market"]

    if language == "English":
        prompt = f"""
You are The Android, Head of Sales at AIF369 (AI consulting, automation & digital transformation firm).

CONTEXT FOR TODAY:
- Name: {day_config['en_name']}
- Pillar: {day_config['pillar']}
- Tone: {day_config['tone']}
- CTA: {day_config['cta']}
- Target Market: {market}

INSTRUCTIONS:
1. Generate a LinkedIn post for EUROPEAN MARKET in English
2. 150-200 words, strong emotional hook, 2-3 emojis max
3. Must end with clear CTA (Schedule demo, Check how, etc.)
4. Mention pricing tiers if relevant:
   - Basic: $3,000 USD / 6 months
   - Premium: $6,000 USD / 1 year
   - Standard: $9,000 USD / 1 year (HIGHLIGHT THIS ONE)
5. NO hashtags (we'll add them after)
6. Strong hooks for European B2B audience:
   - "Most European companies waste 60% on operational costs because..."
   - "While competitors scale with AI, you're still doing this manually..."
   - "The data nobody tells you about automation..."

Generate the post NOW (English only):
"""
    else:  # Spanish
        prompt = f"""
Eres El Androide, Head of Sales de AIF369 (consultoría en IA, automatización y transformación digital).

CONTEXTO DEL DÍA:
- Nombre: {day_config['es_name']}
- Pilar: {day_config['pillar']}
- Tono: {day_config['tone']}
- CTA: {day_config['cta']}
- Mercado Objetivo: {market}

INSTRUCCIONES:
1. Genera un post de LinkedIn para MERCADO LATINOAMERICANO en español
2. 150-200 palabras, hook emocional fuerte, 2-3 emojis máximo
3. DEBE terminar con CTA claro (Agenda demo, Mira cómo, etc.)
4. Menciona planes de precios si es relevante:
   - Básico: $3.000 USD / 6 meses
   - Premium: $6.000 USD / 1 año
   - Standard: $9.000 USD / 1 año (DESTACA ESTE)
5. NO escribas hashtags (los agregaremos después)
6. Hooks fuertes para audiencia LATAM B2B:
   - "La mayoría de empresas pierden 60% en costos porque..."
   - "Mientras competidores escalan con IA, tú sigues haciendo esto manualmente..."
   - "El dato que nadie te cuenta sobre automatización..."

Genera el post AHORA (solo en español):
"""

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def post_to_linkedin(account: str, content: str, day_name: str) -> bool:
    """Publica contenido en LinkedIn (con token específico de la cuenta)."""

    account_info = ACCOUNTS[account]
    token = account_info["linkedin_token"]
    linkedin_id = account_info["linkedin_id"]

    if not token or not linkedin_id:
        print(f"⚠️  {account_info['name']}: Token o LinkedIn ID faltante. Mock publish.")
        print(f"Content:\n{content}\n")
        return True  # Mock success

    try:
        url = "https://api.linkedin.com/v2/posts"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "author": f"urn:li:person:{linkedin_id}",
            "commentary": content,
            "visibility": "PUBLIC"
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 201:
            print(f"✅ {account_info['name']}: Post publicado en LinkedIn ({day_name})")
            return True
        else:
            print(f"❌ {account_info['name']}: Error LinkedIn API {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ {account_info['name']}: Error posting: {e}")
        return False


def run_daily_publisher():
    """Ejecuta publicador para AMBAS cuentas (una por mañana, otra por tarde)."""

    today = datetime.now().weekday()

    if today == 6:  # Sunday: no publish
        print("🌙 Sunday: No publications scheduled")
        return

    day_config = PUBLISHING_SCHEDULE[today]
    now = datetime.now()
    hour = now.hour
    minute = now.minute

    print(f"\n{'='*70}")
    print(f"🌍 DUAL-MARKET PUBLISHER — {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*70}\n")

    # Determinar cuál cuenta publica ahora
    accounts_to_publish = []

    for account_key, account in ACCOUNTS.items():
        if hour == account["publish_hour"] and minute == account["publish_minute"]:
            accounts_to_publish.append((account_key, account))

    if not accounts_to_publish:
        print(f"⏰ No scheduled publications at {hour}:{minute:02d}")
        print(f"   Next: The Android at 09:00 CET | El Androide at 14:00 UTC-5")
        return

    # Publicar en cuentas correspondientes
    for account_key, account in accounts_to_publish:
        print(f"\n📅 GENERANDO POST: {account['name']} ({account['market']})")
        print(f"   Idioma: {account['language']}")
        print(f"   Tema: {day_config['es_name' if account['language'] == 'Spanish' else 'en_name']}")
        print(f"{'─'*70}")

        # Generar contenido
        print(f"🤖 Generando contenido con Claude...")
        post_content = generate_linkedin_post(account_key, day_config)

        print(f"\n📝 CONTENIDO GENERADO:\n{post_content}\n")

        # Publicar
        print(f"📤 Publicando en LinkedIn...")
        success = post_to_linkedin(account_key, post_content, day_config['es_name' if account['language'] == 'Spanish' else 'en_name'])

        if success:
            # Guardar en logs
            with open("logs/androide_dual_posts.log", "a") as f:
                f.write(f"\n[{datetime.now().isoformat()}] {account['name']} ({account['language']})\n{post_content}\n")
            print(f"✅ Publicación completada ({account['name']})")
        else:
            print(f"❌ Fallo en publicación ({account['name']})")


if __name__ == "__main__":
    run_daily_publisher()
