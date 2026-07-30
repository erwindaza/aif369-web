#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - PLAYWRIGHT FILL (No pyautogui para escribir)
Usa Playwright page.fill() para rellenar los campos.
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

log_file = "/tmp/linkedin-playwright-fill.log"

def log(msg):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(log_file, "a") as f:
        f.write(line + "\n")

def main():
    log("="*80)
    log("🤖 LINKEDIN BOT - PLAYWRIGHT FILL")
    log("="*80)
    log(f"Email: {EMAIL}")
    log(f"Pass: {'*' * len(PASSWORD)}")

    with sync_playwright() as p:
        log("\n🔥 Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            log("📍 LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)

            log("⏳ Esperando 5 segundos...")
            time.sleep(5)

            # FOTO 1
            log("📸 Foto 1: Inicial")
            page.screenshot(path="/tmp/pw1_inicio.png")

            # Cerrar popup si existe
            try:
                close_btn = page.query_selector("button[aria-label*='Close'], button:has-text('X')")
                if close_btn:
                    log("🔐 Cerrando popup...")
                    close_btn.click()
                    time.sleep(0.5)
            except:
                pass

            # FOTO 2: Después de intentar cerrar popup
            log("📸 Foto 2: Después de cerrar popup")
            page.screenshot(path="/tmp/pw2_popup_cerrado.png")

            # ENCONTRAR Y LLENAR EMAIL
            log("\n✍️ Buscando campo de email...")
            email_input = page.query_selector("input[name='session_key'], input[aria-label*='Email'], input[aria-label*='email']")

            if not email_input:
                # Intentar por placeholder
                email_input = page.query_selector("input[placeholder*='email'], input[placeholder*='Email']")

            if not email_input:
                # Intentar encontrar todos los inputs y usar el primero
                all_inputs = page.query_selector_all("input")
                if len(all_inputs) > 0:
                    email_input = all_inputs[0]

            if email_input:
                log(f"   ✅ Campo encontrado")
                log(f"   Rellenando email...")
                email_input.click()
                time.sleep(0.3)
                email_input.fill(EMAIL)
                log(f"   ✅ Email rellenado: {EMAIL}")
            else:
                log(f"   ❌ No se encontró campo de email")

            # FOTO 3
            log("📸 Foto 3: Email rellenado")
            page.screenshot(path="/tmp/pw3_email_rellenado.png")

            # ENCONTRAR Y LLENAR PASSWORD
            log("\n🔐 Buscando campo de password...")
            pass_input = page.query_selector("input[name='password'], input[type='password'], input[aria-label*='Password']")

            if not pass_input:
                # Intentar encontrar todos los inputs y usar el segundo
                all_inputs = page.query_selector_all("input")
                if len(all_inputs) > 1:
                    pass_input = all_inputs[1]

            if pass_input:
                log(f"   ✅ Campo encontrado")
                log(f"   Rellenando password...")
                pass_input.click()
                time.sleep(0.3)
                pass_input.fill(PASSWORD)
                log(f"   ✅ Password rellenado")
            else:
                log(f"   ❌ No se encontró campo de password")

            # FOTO 4
            log("📸 Foto 4: Password rellenado")
            page.screenshot(path="/tmp/pw4_password_rellenado.png")

            # ENCONTRAR Y CLICKEAR BOTÓN "Iniciar sesión"
            log("\n🔑 Buscando botón 'Iniciar sesión'...")
            login_btn = page.query_selector("button:has-text('Iniciar sesión')")

            if login_btn:
                log("   ✅ Botón encontrado")
                log("   Clickeando botón...")
                login_btn.click()
                time.sleep(3)
            else:
                log("   ❌ Botón no encontrado, presionando ENTER...")
                page.press("input[type='password']", "Enter")
                time.sleep(3)

            # FOTO 5
            log("📸 Foto 5: Después de ENTER/Click")
            page.screenshot(path="/tmp/pw5_enter.png")

            # ESPERAR FEED
            log("\n⏳ Esperando feed (15s)...")
            start = time.time()

            while time.time() - start < 15:
                url = page.url
                log(f"   URL: {url}")

                if "feed" in url.lower():
                    elapsed = time.time() - start
                    log(f"\n✅ ¡LOGIN EXITOSO EN {elapsed:.1f}s!")
                    log("📸 Foto 6: Feed")
                    page.screenshot(path="/tmp/pw6_feed_exito.png")

                    browser.close()
                    log("\n" + "="*80)
                    log("✅ ÉXITO TOTAL")
                    log("="*80)
                    return True

                time.sleep(1)

            log(f"\n❌ Login rechazado")
            log("📸 Foto 6: Fallo")
            page.screenshot(path="/tmp/pw6_fallo.png")

            browser.close()
            return False

        except Exception as e:
            log(f"\n❌ ERROR: {e}")
            import traceback
            log(traceback.format_exc())
            browser.close()
            return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n⏸️ Detenido")
    except Exception as e:
        log(f"\n❌ ERROR: {e}")
