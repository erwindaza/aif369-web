#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT FINAL V2
Usa coordenadas aprendidas de visual analysis.
Modelo: Manual visual coordinate extraction + continuous learning.
"""

import os
import sys
import time
import json
import pyautogui
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

try:
    from playwright.sync_api import sync_playwright
except:
    print("❌ pip install playwright")
    sys.exit(1)

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()
POSTS_FILE = "/Users/macbookpro/dev/aif369-web/posts-semana.txt"
FIELD_COORDS_FILE = "/Users/macbookpro/dev/aif369-web/logs/linkedin-field-coords.json"

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def load_field_coords():
    """Carga coordenadas aprendidas."""
    try:
        with open(FIELD_COORDS_FILE) as f:
            data = json.load(f)
        return data["linkedin_login_page"]["layout"]
    except:
        log("⚠️  No se encontraron coordenadas, usando defaults...")
        return {
            "email_field": {"x": 688, "y": 400},
            "password_field": {"x": 688, "y": 485},
            "login_button": {"x": 688, "y": 632}
        }

def get_today_post():
    if not os.path.exists(POSTS_FILE):
        return None
    today = datetime.now().weekday()
    if today == 6:
        return None
    SCHED = {0: "🤖 Automation Mondays", 1: "📈 Martes de Transformación", 2: "🎯 Miércoles de Éxito", 3: "🛠️ Jueves de Herramientas", 4: "🚀 Viernes del Futuro", 5: "💡 Sábado Estratégico"}
    label = SCHED.get(today)
    with open(POSTS_FILE) as f:
        lines = f.read().split("\n")
    for i, line in enumerate(lines):
        if label in line:
            for j in range(i+3, len(lines)):
                if lines[j].startswith("-"*80):
                    return "\n".join(lines[i+3:j]).strip()
    return None

def main():
    log("="*80)
    log("🤖 LINKEDIN BOT FINAL V2 — Learned Coordinates")
    log("="*80)

    coords = load_field_coords()

    log(f"\n📍 Coordenadas aprendidas:")
    log(f"   Email: ({coords['email_field']['x']}, {coords['email_field']['y']})")
    log(f"   Password: ({coords['password_field']['x']}, {coords['password_field']['y']})")
    log(f"   Login btn: ({coords['login_button']['x']}, {coords['login_button']['y']})")

    with sync_playwright() as p:
        log("\n🔥 Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            log("📍 LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(1)

            # Cerrar popup de Google si aparece
            try:
                close_btn = page.query_selector("button[aria-label*='Close'], button:has-text('X')")
                if close_btn:
                    log("⚠️  Cerrando popup de Google...")
                    close_btn.click()
                    time.sleep(0.5)
            except:
                pass

            page.screenshot(path="/tmp/v2_01_login.png")

            # EMAIL
            log(f"\n⌨️ EMAIL...")
            email_x = coords['email_field']['x']
            email_y = coords['email_field']['y']

            log(f"   Click en ({email_x}, {email_y})...")
            pyautogui.click(email_x, email_y)
            time.sleep(0.3)

            log(f"   Escribiendo {len(LINKEDIN_EMAIL)} chars...")
            for char in LINKEDIN_EMAIL:
                pyautogui.typewrite(char, interval=0.015)

            log(f"   ✅ Email escrito")
            time.sleep(0.2)

            # PASSWORD
            log(f"\n⌨️ PASSWORD...")
            pass_x = coords['password_field']['x']
            pass_y = coords['password_field']['y']

            pyautogui.click(pass_x, pass_y)
            time.sleep(0.2)

            for char in LINKEDIN_PASSWORD:
                pyautogui.typewrite(char, interval=0.015)

            log(f"   ✅ Password escrito")
            time.sleep(0.2)

            page.screenshot(path="/tmp/v2_02_credentials.png")

            # ENTER
            log(f"\n🔑 ENTER...")
            pyautogui.press('enter')
            time.sleep(2)

            # ESPERAR FEED
            log(f"\n⏳ Esperando feed (15s)...")
            start = time.time()

            while time.time() - start < 15:
                if "feed" in page.url.lower():
                    elapsed = time.time() - start
                    log(f"✅ LOGIN EXITOSO en {elapsed:.1f}s")

                    page.screenshot(path="/tmp/v2_03_feed.png")

                    # PUBLICAR
                    post = get_today_post()
                    if post:
                        log(f"\n📝 Publicando post...")
                        try:
                            page.wait_for_selector("button:has-text('Start a post')", timeout=5000)
                            page.click("button:has-text('Start a post')")
                            time.sleep(0.5)

                            page.wait_for_selector("div[contenteditable='true']", timeout=5000)
                            textarea = page.query_selector("div[contenteditable='true']")
                            textarea.click()
                            time.sleep(0.3)

                            page.keyboard.type(post, delay=0.3)
                            time.sleep(0.5)

                            page.wait_for_selector("button:has-text('Post')", timeout=5000)
                            post_btn = page.query_selector("button:has-text('Post')")
                            post_btn.scroll_into_view_if_needed()
                            time.sleep(0.3)
                            post_btn.click()

                            log(f"   ✅ POST PUBLICADO")
                            time.sleep(2)
                            page.screenshot(path="/tmp/v2_04_published.png")

                        except Exception as e:
                            log(f"   ⚠️ Error: {str(e)[:50]}")

                    browser.close()
                    return True

                time.sleep(1)

            log(f"❌ Login timeout")
            page.screenshot(path="/tmp/v2_failed.png")
            return False

        except Exception as e:
            log(f"\n❌ ERROR: {e}")
            return False


if __name__ == "__main__":
    log(f"\n📚 MODELO DE APRENDIZAJE:")
    log(f"   Tipo: Manual Visual Analysis + Coordinate Extraction")
    log(f"   Fuente: Análisis de screenshots con visión humana")
    log(f"   Almacenamiento: /logs/linkedin-field-coords.json")
    log(f"   Actualización: Basado en iteraciones previas")

    success = main()

    log("\n" + "="*80)
    log("✅ ÉXITO" if success else "❌ FALLO")
    log("="*80)

    sys.exit(0 if success else 1)
