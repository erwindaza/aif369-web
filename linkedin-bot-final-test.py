#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - FINAL TEST
Corregido: usa .first para evitar strict mode violation.
"""

import os
import time
from dotenv import load_dotenv

load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

try:
    from playwright.sync_api import sync_playwright
except:
    exit(1)

EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def main():
    log("="*80)
    log("🤖 LINKEDIN BOT - FINAL TEST (.first fix)")
    log("="*80)
    log(f"Email: {EMAIL}")

    with sync_playwright() as p:
        log("\n🔥 Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            log("📍 LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)

            log("⏳ 5 segundos...")
            time.sleep(5)

            log("📸 Foto 1: Inicio")
            page.screenshot(path="/tmp/ft1_inicio.png")

            # EMAIL - usando .first
            log("\n✍️ EMAIL (usando .first)")
            email_loc = page.locator("input[name='session_key']").first
            email_loc.focus()
            time.sleep(0.3)
            email_loc.type(EMAIL, delay=50)
            log(f"   ✅ Email escribiendo...")

            log("📸 Foto 2: Después email")
            page.screenshot(path="/tmp/ft2_email.png")

            time.sleep(0.5)

            # PASSWORD - usando .first
            log("\n🔐 PASSWORD (usando .first)")
            pass_loc = page.locator("input[type='password']").first
            pass_loc.focus()
            time.sleep(0.3)
            pass_loc.type(PASSWORD, delay=50)
            log(f"   ✅ Password escribiendo...")

            log("📸 Foto 3: Después password")
            page.screenshot(path="/tmp/ft3_password.png")

            time.sleep(0.5)

            # CLICK BOTÓN O ENTER
            log("\n🔑 ENTER...")
            page.keyboard.press("Enter")
            time.sleep(3)

            log("📸 Foto 4: Después ENTER")
            page.screenshot(path="/tmp/ft4_enter.png")

            # Esperar
            log("\n⏳ Esperando feed (15s)...")
            start = time.time()
            while time.time() - start < 15:
                url = page.url
                if "feed" in url.lower():
                    log(f"\n✅ ¡LOGIN EXITOSO!")
                    log("📸 Foto 5: Feed")
                    page.screenshot(path="/tmp/ft5_feed.png")
                    browser.close()
                    log("\n" + "="*80)
                    log("✅ ÉXITO!")
                    log("="*80)
                    return True
                time.sleep(1)

            log(f"\n❌ Login rechazado - URL: {page.url}")
            log("📸 Foto 5: Fallo")
            page.screenshot(path="/tmp/ft5_fallo.png")
            browser.close()
            return False

        except Exception as e:
            log(f"\n❌ ERROR: {e}")
            import traceback
            log(traceback.format_exc())
            try:
                browser.close()
            except:
                pass
            return False

if __name__ == "__main__":
    main()
