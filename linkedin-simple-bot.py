#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT SIMPLE - Publica posts con validación visual
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ Instala playwright: pip install playwright")
    sys.exit(1)

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")
POSTS_FILE = "/Users/macbookpro/dev/aif369-web/posts-semana.txt"
LOG_FILE = "/Users/macbookpro/dev/aif369-web/logs/linkedin-bot.log"

PUBLISH_SCHEDULE = {
    0: "🤖 Automation Mondays",
    1: "📈 Martes de Transformación",
    2: "🎯 Miércoles de Éxito",
    3: "🛠️ Jueves de Herramientas",
    4: "🚀 Viernes del Futuro",
    5: "💡 Sábado Estratégico",
}

def log(msg: str):
    """Log con timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{ts}] {msg}"
    print(log_msg)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")


def get_today_post() -> str:
    """Obtiene el post del día."""
    if not os.path.exists(POSTS_FILE):
        log(f"❌ {POSTS_FILE} no encontrado")
        return None

    today_weekday = datetime.now().weekday()
    log(f"📅 Día: {today_weekday} (0=Lun, 6=Dom)")

    if today_weekday == 6:
        log("ℹ️  Domingo: sin publicación")
        return None

    day_label = PUBLISH_SCHEDULE.get(today_weekday, "Unknown")

    with open(POSTS_FILE, "r") as f:
        content = f.read()

    lines = content.split("\n")
    post_start = None

    for i, line in enumerate(lines):
        if day_label in line:
            post_start = i + 3
            for j in range(post_start, len(lines)):
                if lines[j].startswith("-" * 80):
                    post = "\n".join(lines[post_start:j]).strip()
                    log(f"✅ Post obtenido: {day_label}")
                    return post

    log(f"❌ No se encontró post para: {day_label}")
    return None


def main():
    log("="*80)
    log("🤖 LINKEDIN BOT SIMPLE")
    log("="*80)

    post = get_today_post()
    if not post:
        return False

    log(f"\n📄 POST ({len(post)} caracteres):\n{post}\n")

    with sync_playwright() as p:
        log("🚀 Abriendo Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1280, "height": 1024})

        try:
            # ─── STEP 1: LOGIN ───
            log("📝 Navegando a LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)

            log("\n⏸️  PAUSA: Ingresa email y contraseña manualmente")
            log("    Tienes 120 segundos...")
            log("    El bot continuará automáticamente después.\n")

            # Esperar a que el usuario ingrese manualmente
            page.wait_for_url("https://www.linkedin.com/feed/**", timeout=120000)

            log("✅ Login detectado")
            page.wait_for_load_state("networkidle", timeout=10000)

            # ─── STEP 2: ABRIR COMPOSER ───
            log("📝 Abriendo composer...")
            page.wait_for_selector("button:has-text('Start a post')", timeout=10000)
            page.click("button:has-text('Start a post')")
            page.wait_for_timeout(2000)

            # ─── STEP 3: ESCRIBIR POST ───
            log("✍️  Pegando contenido del post...")
            page.wait_for_selector("div[contenteditable='true']", timeout=5000)
            textarea = page.query_selector("div[contenteditable='true']")
            textarea.click()
            page.wait_for_timeout(500)

            # Usar keyboard.type que es más confiable
            page.keyboard.type(post, delay=2)
            page.wait_for_timeout(2000)

            # ─── STEP 4: PUBLICAR ───
            log("🚀 Publicando...")
            page.wait_for_selector("button:has-text('Post')", timeout=5000)
            post_button = page.query_selector("button:has-text('Post')")
            post_button.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)
            post_button.click()

            log("⏳ Esperando confirmación...")
            page.wait_for_timeout(5000)

            log("✅ POST PUBLICADO EN LINKEDIN")
            page.wait_for_timeout(2000)
            browser.close()

            return True

        except Exception as e:
            log(f"\n❌ ERROR: {str(e)}")
            log("\n⏸️  El navegador se mantiene abierto para debugging")
            log("    Ciérralo manualmente cuando termines\n")
            # NO cerrar el navegador, dejar que el usuario vea qué pasó
            return False


if __name__ == "__main__":
    log("="*80)
    log("🤖 LINKEDIN BOT SIMPLE — Iniciado")
    log("="*80)

    success = main()

    log("="*80)
    if success:
        log("✅ ÉXITO")
    else:
        log("❌ FALLO")
    log("="*80)

    sys.exit(0 if success else 1)
