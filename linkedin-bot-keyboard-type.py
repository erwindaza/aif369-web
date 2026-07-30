#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - KEYBOARD.TYPE()
Usa page.keyboard.type() después de focus().
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
    log("🤖 LINKEDIN BOT - KEYBOARD.TYPE()")
    log("="*80)
    log(f"Email: {EMAIL}")
    log(f"Password: {'*'*len(PASSWORD)}")

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

            log("📸 Foto 1")
            page.screenshot(path="/tmp/kt1_inicio.png")

            # EMAIL - focus y type
            log("\n✍️ EMAIL")
            log("   Buscando campo...")

            # Buscar por selector
            email_field = page.query_selector("input[name='session_key']")
            if not email_field:
                # Intenta primer input
                all_inputs = page.query_selector_all("input")
                for inp in all_inputs:
                    field_type = inp.get_attribute("type") or ""
                    if field_type != "password":
                        email_field = inp
                        break

            if email_field:
                log("   ✅ Campo encontrado")
                log("   Focus y type...")
                # Usar locator para más robustez
                email_locator = page.locator("input[name='session_key'], input[type='email'], input").first
                email_locator.focus()
                time.sleep(0.5)
                email_locator.type(EMAIL, delay=50)
                log(f"   ✅ Email escrito")
            else:
                log("   ❌ Campo NO encontrado")

            log("📸 Foto 2: Email")
            page.screenshot(path="/tmp/kt2_email.png")

            # PASSWORD - focus y type
            log("\n🔐 PASSWORD")
            log("   Buscando campo...")

            pass_field = page.query_selector("input[type='password']")

            if pass_field:
                log("   ✅ Campo encontrado")
                log("   Focus y type...")
                pass_locator = page.locator("input[type='password']")
                pass_locator.focus()
                time.sleep(0.5)
                pass_locator.type(PASSWORD, delay=50)
                log(f"   ✅ Password escrito")
            else:
                log("   ❌ Campo NO encontrado")

            log("📸 Foto 3: Password")
            page.screenshot(path="/tmp/kt3_password.png")

            # ENTER
            log("\n🔑 ENTER...")
            page.keyboard.press("Enter")
            time.sleep(3)

            log("📸 Foto 4: Después ENTER")
            page.screenshot(path="/tmp/kt4_enter.png")

            # Esperar
            log("\n⏳ Esperando feed (15s)...")
            start = time.time()
            while time.time() - start < 15:
                url = page.url
                log(f"   URL: {url}")

                if "feed" in url.lower():
                    log(f"\n✅ ¡LOGIN EXITOSO!")
                    log("📸 Foto 5: Feed exitoso")
                    page.screenshot(path="/tmp/kt5_feed.png")
                    browser.close()

                    log("\n" + "="*80)
                    log("✅ ÉXITO TOTAL!")
                    log("="*80)
                    return True

                time.sleep(1)

            log(f"\n❌ Login rechazado")
            log(f"   Final URL: {page.url}")
            log("📸 Foto 5: Fallo")
            page.screenshot(path="/tmp/kt5_fallo.png")
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
    try:
        main()
    except KeyboardInterrupt:
        log("\n⏸️ Detenido")
