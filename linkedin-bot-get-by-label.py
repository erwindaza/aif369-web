#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - GET_BY_LABEL
Usa page.get_by_label() para encontrar los campos.
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
    log("🤖 LINKEDIN BOT - GET_BY_LABEL")
    log("="*80)

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
            page.screenshot(path="/tmp/gbl1_inicio.png")

            # EMAIL - usando get_by_label
            log("\n✍️ EMAIL (get_by_label)")
            try:
                email_loc = page.get_by_label("Email o teléfono").first
                email_loc.fill(EMAIL)
                log(f"   ✅ Email rellenado")
            except Exception as e:
                log(f"   ❌ Error: {str(e)[:50]}")

            log("📸 Foto 2: Email")
            page.screenshot(path="/tmp/gbl2_email.png")

            time.sleep(0.5)

            # PASSWORD - usando get_by_label
            log("\n🔐 PASSWORD (get_by_label)")
            try:
                pass_loc = page.get_by_label("Contraseña").first
                pass_loc.fill(PASSWORD)
                log(f"   ✅ Password rellenado")
            except Exception as e:
                log(f"   ❌ Error: {str(e)[:50]}")

            log("📸 Foto 3: Password")
            page.screenshot(path="/tmp/gbl3_password.png")

            time.sleep(0.5)

            # ENTER
            log("\n🔑 ENTER...")
            page.keyboard.press("Enter")
            time.sleep(3)

            log("📸 Foto 4: Después ENTER")
            page.screenshot(path="/tmp/gbl4_enter.png")

            # Esperar
            log("\n⏳ Esperando feed (15s)...")
            start = time.time()
            while time.time() - start < 15:
                url = page.url
                if "feed" in url.lower():
                    log(f"\n✅ ¡LOGIN EXITOSO!")
                    log("📸 Foto 5: Feed")
                    page.screenshot(path="/tmp/gbl5_feed.png")
                    browser.close()
                    log("\n" + "="*80)
                    log("✅ ¡ÉXITO COMPLETADO!")
                    log("="*80)
                    return True
                time.sleep(1)

            log(f"\n❌ Login rechazado")
            log("📸 Foto 5: Fallo")
            page.screenshot(path="/tmp/gbl5_fallo.png")
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
