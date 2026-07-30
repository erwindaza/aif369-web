#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT V3 — Robusto con manejo de 2FA
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ pip install playwright")
    sys.exit(1)

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()
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
    log("🤖 LINKEDIN BOT V3 — ROBUSTO")
    log("="*80)

    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        log(f"❌ Credenciales vacías")
        log(f"   EMAIL: '{LINKEDIN_EMAIL}'")
        log(f"   PASSWORD: '{LINKEDIN_PASSWORD}'")
        return False

    post = get_today_post()
    if not post:
        return False

    log(f"\n📄 POST ({len(post)} chars):\n{post[:100]}...\n")

    with sync_playwright() as p:
        log("🚀 Abriendo Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1280, "height": 1024})

        try:
            # ─── LOGIN ───
            log("📝 Navegando a LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)

            log("⏳ Esperando campo de email (5s)...")
            time.sleep(5)

            # Buscar input con placeholder o aria-label
            log("🔍 Buscando campo de email...")
            try:
                page.wait_for_selector("input", timeout=5000)
                email_input = page.query_selector("input")
                if email_input:
                    log("   ✅ Campo encontrado")
                    email_input.focus()
                    time.sleep(0.5)

                    log(f"⌨️  Escribiendo email: {LINKEDIN_EMAIL}")
                    page.keyboard.type(LINKEDIN_EMAIL, delay=50)
                    time.sleep(1)

                    log("📌 Tab a password...")
                    page.keyboard.press("Tab")
                    time.sleep(1)

                    log(f"🔐 Escribiendo contraseña ({len(LINKEDIN_PASSWORD)} chars)...")
                    page.keyboard.type(LINKEDIN_PASSWORD, delay=50)
                    time.sleep(1)

                    log("👆 Presionando Enter...")
                    page.keyboard.press("Enter")
                    time.sleep(3)

            except Exception as e:
                log(f"   ⚠️  Error llenando campos: {e}")

            # ─── ESPERAR LOGIN ───
            log("\n⏸️  Esperando login (120 segundos)...")
            log("    Si aparece 2FA, complétalo manualmente\n")

            try:
                page.wait_for_url(
                    "https://www.linkedin.com/feed/**",
                    timeout=120000  # 120 segundos para 2FA manual
                )
                log("✅ Login exitoso")
            except:
                log("⚠️  Timeout en login - posible 2FA manual o credenciales incorrectas")
                log("    Navegación actual:", page.url)

                # Si el usuario completó 2FA manualmente, intentar continuar
                if "feed" in page.url.lower():
                    log("   ✅ Se detectó navegación a feed")
                else:
                    log("   ❌ No se llegó al feed")
                    raise Exception("Login fallido")

            page.wait_for_load_state("networkidle", timeout=10000)

            # ─── PUBLICAR ───
            log("📝 Abriendo composer...")
            page.wait_for_selector("button:has-text('Start a post')", timeout=10000)
            page.click("button:has-text('Start a post')")
            time.sleep(2)

            log("✍️  Pegando post...")
            page.wait_for_selector("div[contenteditable='true']", timeout=5000)
            textarea = page.query_selector("div[contenteditable='true']")
            textarea.click()
            time.sleep(1)

            page.keyboard.type(post, delay=2)
            time.sleep(2)

            log("🚀 Publicando...")
            page.wait_for_selector("button:has-text('Post')", timeout=5000)
            post_btn = page.query_selector("button:has-text('Post')")
            post_btn.scroll_into_view_if_needed()
            time.sleep(1)
            post_btn.click()

            log("⏳ Esperando confirmación...")
            time.sleep(5)

            log("✅ POST PUBLICADO")
            time.sleep(2)
            browser.close()

            return True

        except Exception as e:
            log(f"\n❌ ERROR: {e}")
            log("\n🔍 DEBUG: Navegador sigue abierto para inspeccionar")
            log("    URL actual:", page.url if 'page' in locals() else "N/A")
            return False


if __name__ == "__main__":
    success = main()
    log("="*80)
    log("✅ ÉXITO" if success else "❌ FALLO")
    log("="*80)
    sys.exit(0 if success else 1)
