#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - DIRECT FILL
Playwright fill() directamente sin click.
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
    log("🤖 LINKEDIN BOT - DIRECT FILL")

    with sync_playwright() as p:
        log("🔥 Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            log("📍 LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)

            log("⏳ 5 segundos...")
            time.sleep(5)

            log("📸 Foto 1")
            page.screenshot(path="/tmp/df1_inicio.png")

            # Intentar llenar email directamente
            log("✍️ Intentando llenar email...")
            try:
                page.fill("input[name='session_key']", EMAIL)
                log(f"   ✅ Usando session_key")
            except:
                try:
                    page.fill("input[type='email']", EMAIL)
                    log(f"   ✅ Usando type=email")
                except:
                    try:
                        # Último intento: fill() en el primer input
                        inputs = page.query_selector_all("input")
                        if inputs:
                            page.fill_locator(page.locator("input").first, EMAIL)
                            log(f"   ✅ Usando primer input")
                    except Exception as e:
                        log(f"   ❌ Error: {str(e)[:50]}")

            log("📸 Foto 2: Email")
            page.screenshot(path="/tmp/df2_email.png")

            # Intentar llenar password directamente
            log("🔐 Intentando llenar password...")
            try:
                page.fill("input[name='password']", PASSWORD)
                log(f"   ✅ Usando name=password")
            except:
                try:
                    page.fill("input[type='password']", PASSWORD)
                    log(f"   ✅ Usando type=password")
                except:
                    try:
                        inputs = page.query_selector_all("input")
                        if len(inputs) > 1:
                            page.fill_locator(page.locator("input").nth(1), PASSWORD)
                            log(f"   ✅ Usando segundo input")
                    except Exception as e:
                        log(f"   ❌ Error: {str(e)[:50]}")

            log("📸 Foto 3: Password")
            page.screenshot(path="/tmp/df3_password.png")

            # Presionar ENTER
            log("🔑 ENTER...")
            page.keyboard.press("Enter")
            time.sleep(3)

            log("📸 Foto 4: Después ENTER")
            page.screenshot(path="/tmp/df4_enter.png")

            # Esperar
            log("⏳ Esperando feed...")
            start = time.time()
            while time.time() - start < 15:
                if "feed" in page.url.lower():
                    log(f"✅ LOGIN EXITOSO!")
                    log("📸 Foto 5: Feed")
                    page.screenshot(path="/tmp/df5_feed.png")
                    browser.close()
                    return True
                time.sleep(1)

            log(f"❌ Fallo - URL: {page.url}")
            log("📸 Foto 5: Fallo")
            page.screenshot(path="/tmp/df5_fallo.png")
            browser.close()
            return False

        except Exception as e:
            log(f"❌ ERROR: {e}")
            browser.close()
            return False

if __name__ == "__main__":
    main()
