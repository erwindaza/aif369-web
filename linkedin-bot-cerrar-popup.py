#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - CERRAR POPUP DE GOOGLE PRIMERO
Cierra el popup de Google → luego clickea el formulario.
"""

import os
import time
import pyautogui
from dotenv import load_dotenv

load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

try:
    from playwright.sync_api import sync_playwright
except:
    exit(1)

EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()

log_file = "/tmp/linkedin-cerrar-popup.log"

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(log_file, "a") as f:
        f.write(line + "\n")

def main():
    log("="*80)
    log("🤖 LINKEDIN BOT - CERRAR POPUP PRIMERO")
    log("="*80)

    with sync_playwright() as p:
        log("🔥 Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            log("📍 LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)

            log("⏳ Esperando 5 segundos...")
            time.sleep(5)

            # FOTO 1: INICIAL
            log("📸 Foto 1: Con popup abierto")
            page.screenshot(path="/tmp/p1_con_popup.png")

            # CERRAR POPUP DE GOOGLE
            log("🔐 Cerrando popup de Google...")
            log("   Clickeando X en (1339, 171)...")
            pyautogui.click(1339, 171)
            time.sleep(1)

            # FOTO 2: DESPUÉS DE CERRAR POPUP
            log("📸 Foto 2: Después de cerrar popup")
            page.screenshot(path="/tmp/p2_popup_cerrado.png")

            # CLICKEAR EMAIL - AHORA SÍ DEBERÍA FUNCIONAR
            log("\n✍️ EMAIL")
            log("   Clickeando en (688, 373)...")
            pyautogui.click(688, 373)
            time.sleep(0.5)

            log("   Escribiendo email lentamente...")
            for i, char in enumerate(EMAIL):
                pyautogui.typewrite(char, interval=0.050)
                if (i + 1) % 6 == 0:
                    log(f"      {i+1}/{len(EMAIL)}...")

            time.sleep(0.5)

            # FOTO 3: EMAIL ESCRITO
            log("📸 Foto 3: Email escrito")
            page.screenshot(path="/tmp/p3_email_escrito.png")

            # CLICKEAR PASSWORD
            log("\n🔐 PASSWORD")
            log("   Clickeando en (688, 484)...")
            pyautogui.click(688, 484)
            time.sleep(0.5)

            log("   Escribiendo password lentamente...")
            for i, char in enumerate(PASSWORD):
                pyautogui.typewrite(char, interval=0.050)
                if (i + 1) % 3 == 0:
                    log(f"      {i+1}/{len(PASSWORD)}...")

            time.sleep(0.5)

            # FOTO 4: PASSWORD ESCRITO
            log("📸 Foto 4: Password escrito")
            page.screenshot(path="/tmp/p4_password_escrito.png")

            # ENTER
            log("\n🔑 ENTER...")
            pyautogui.press('enter')
            time.sleep(3)

            # FOTO 5: DESPUÉS DE ENTER
            log("📸 Foto 5: Después de ENTER")
            page.screenshot(path="/tmp/p5_enter.png")

            # ESPERAR FEED
            log("\n⏳ Esperando feed (15s)...")
            start = time.time()

            while time.time() - start < 15:
                url = page.url
                if "feed" in url.lower():
                    elapsed = time.time() - start
                    log(f"\n✅ ¡LOGIN EXITOSO EN {elapsed:.1f}s!")
                    log("📸 Foto 6: Feed exitoso")
                    page.screenshot(path="/tmp/p6_feed_exito.png")

                    browser.close()
                    log("\n" + "="*80)
                    log("✅ ÉXITO COMPLETADO")
                    log("="*80)
                    return True

                time.sleep(1)

            log(f"\n❌ Login rechazado - URL: {url}")
            log("📸 Foto 6: Fallo")
            page.screenshot(path="/tmp/p6_fallo.png")

            browser.close()
            return False

        except Exception as e:
            log(f"\n❌ ERROR: {e}")
            browser.close()
            return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n⏸️ Detenido")
    except Exception as e:
        log(f"\n❌ ERROR: {e}")
