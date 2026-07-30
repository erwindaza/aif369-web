#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT AUTOMÁTICO
Control total. Aprendizaje continuo. Sin pausas.
"""

import os
import sys
import time
import pyautogui
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
LOG_FILE = "/Users/macbookpro/dev/aif369-web/logs/linkedin-bot-auto.log"

PUBLISH_SCHEDULE = {
    0: "🤖 Automation Mondays",
    1: "📈 Martes de Transformación",
    2: "🎯 Miércoles de Éxito",
    3: "🛠️ Jueves de Herramientas",
    4: "🚀 Viernes del Futuro",
    5: "💡 Sábado Estratégico",
}

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{ts}] {msg}"
    print(log_msg)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")

def get_today_post() -> str:
    if not os.path.exists(POSTS_FILE):
        return None
    today_weekday = datetime.now().weekday()
    if today_weekday == 6:
        return None
    day_label = PUBLISH_SCHEDULE.get(today_weekday)
    with open(POSTS_FILE, "r") as f:
        content = f.read()
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if day_label in line:
            post_start = i + 3
            for j in range(post_start, len(lines)):
                if lines[j].startswith("-" * 80):
                    return "\n".join(lines[post_start:j]).strip()
    return None

def main():
    log("="*80)
    log("🤖 LINKEDIN BOT AUTOMÁTICO — CONTROL TOTAL")
    log("="*80)

    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        log(f"❌ Credenciales vacías: EMAIL='{LINKEDIN_EMAIL}' PASSWORD='{LINKEDIN_PASSWORD}'")
        return False

    post = get_today_post()
    if not post:
        log("❌ No hay post para publicar")
        return False

    log(f"\n✅ POST LISTO ({len(post)} chars)")

    with sync_playwright() as p:
        log("\n🔥 ABRIENDO FIREFOX...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1280, "height": 1024})

        try:
            # ─── NAVEGACIÓN ───
            log("\n📍 Navegando a LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            log("   ✅ Página cargada")

            # Screenshot 1
            page.screenshot(path="/tmp/01-inicio.png")
            log("   📸 Screenshot: /tmp/01-inicio.png")

            time.sleep(3)

            # ─── ESCRIBIR EMAIL ───
            log("\n⌨️ ESCRIBIENDO EMAIL...")
            log(f"   Email: {LINKEDIN_EMAIL}")
            log(f"   Longitud: {len(LINKEDIN_EMAIL)} caracteres\n")

            # Usar page.fill() que inyecta JavaScript (evita bloqueo de keyboard)
            log("   Usando page.fill() para inyectar email...")

            # Primero intentar con input[type='email']
            try:
                page.fill("input[type='email']", LINKEDIN_EMAIL, timeout=5000)
                log(f"   ✅ Email inyectado con input[type='email']")
            except Exception as e1:
                log(f"   ⚠️ Falló input[type='email']: {str(e1)[:50]}")
                # Intentar con el primer input
                try:
                    page.fill("input", LINKEDIN_EMAIL, timeout=5000)
                    log(f"   ✅ Email inyectado con input genérico")
                except Exception as e2:
                    log(f"   ❌ Error inyectando email: {str(e2)[:50]}")

            log(f"\n   ✅ Email completado\n")

            # Screenshot 2
            time.sleep(1)
            page.screenshot(path="/tmp/02-email-escrito.png")
            log("   📸 Screenshot: /tmp/02-email-escrito.png")

            # ─── TAB A PASSWORD ───
            log("\n↹ Presionando TAB...")
            pyautogui.press('tab')
            time.sleep(1)
            log("   ✅ TAB presionado\n")

            # ─── ESCRIBIR PASSWORD ───
            log("⌨️ ESCRIBIENDO PASSWORD...")
            log(f"   Password: {'*' * len(LINKEDIN_PASSWORD)}")
            log(f"   Longitud: {len(LINKEDIN_PASSWORD)} caracteres\n")

            for i, char in enumerate(LINKEDIN_PASSWORD):
                pyautogui.typewrite(char, interval=0.05)
                log(f"   [{i+1:2d}] '{char}'")
                time.sleep(0.2)

            log(f"\n   ✅ Password completado\n")

            # Screenshot 3
            time.sleep(1)
            page.screenshot(path="/tmp/03-password-escrito.png")
            log("   📸 Screenshot: /tmp/03-password-escrito.png")

            # ─── ENTER ───
            log("\n🔑 Presionando ENTER para login...")
            pyautogui.press('enter')
            time.sleep(3)
            log("   ✅ ENTER presionado\n")

            # ─── ESPERAR LOGIN ───
            log("⏳ Esperando login (120 segundos)...")
            try:
                page.wait_for_url("https://www.linkedin.com/feed/**", timeout=120000)
                log("   ✅ LOGIN EXITOSO - EN FEED\n")

                time.sleep(3)
                page.screenshot(path="/tmp/04-feed-logueado.png")
                log("   📸 Screenshot: /tmp/04-feed-logueado.png")

                # ─── PUBLICAR POST ───
                log("\n📝 PUBLICANDO POST...")
                log("   Abriendo composer...")
                page.wait_for_selector("button:has-text('Start a post')", timeout=10000)
                page.click("button:has-text('Start a post')")
                time.sleep(2)

                log("   Pegando post...")
                page.wait_for_selector("div[contenteditable='true']", timeout=5000)
                textarea = page.query_selector("div[contenteditable='true']")
                textarea.click()
                time.sleep(1)

                page.keyboard.type(post, delay=2)
                time.sleep(2)

                page.screenshot(path="/tmp/05-post-escrito.png")
                log("   📸 Screenshot: /tmp/05-post-escrito.png")

                log("   Publicando...")
                page.wait_for_selector("button:has-text('Post')", timeout=5000)
                post_btn = page.query_selector("button:has-text('Post')")
                post_btn.scroll_into_view_if_needed()
                time.sleep(1)
                post_btn.click()
                time.sleep(5)

                page.screenshot(path="/tmp/06-post-publicado.png")
                log("   📸 Screenshot: /tmp/06-post-publicado.png")

                log("\n" + "="*80)
                log("✅ POST PUBLICADO EXITOSAMENTE")
                log("="*80)

                time.sleep(2)
                browser.close()
                return True

            except Exception as e:
                log(f"   ⚠️ Login timeout o error: {str(e)[:100]}")
                log(f"   URL actual: {page.url}\n")

                page.screenshot(path="/tmp/ERROR-login.png")
                log("   📸 Screenshot: /tmp/ERROR-login.png")

                return False

        except Exception as e:
            log(f"\n❌ ERROR: {str(e)[:200]}\n")
            return False


if __name__ == "__main__":
    success = main()
    log("\n" + "="*80)
    log("✅ ÉXITO" if success else "❌ FALLO")
    log("="*80 + "\n")
    sys.exit(0 if success else 1)
