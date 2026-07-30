#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT CORE
Solo lo esencial: Mouse + Keyboard + JSON Learning
Sin dependencias externas.
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
except ImportError:
    print("❌ pip install playwright")
    sys.exit(1)

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()
LOG_FILE = "/Users/macbookpro/dev/aif369-web/logs/linkedin-core.log"
LEARNING_DB = "/Users/macbookpro/dev/aif369-web/logs/core-learning.json"

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def save_learning(event: dict):
    """Aprende y guarda en JSON."""
    try:
        if os.path.exists(LEARNING_DB):
            with open(LEARNING_DB, 'r') as f:
                data = json.load(f)
        else:
            data = {"events": []}
        data["events"].append({**event, "timestamp": datetime.now().isoformat()})
        with open(LEARNING_DB, 'w') as f:
            json.dump(data, f, indent=2)
        log(f"   💾 Aprendizaje guardado: {event['type']}")
    except:
        pass

def main():
    log("="*80)
    log("🤖 LINKEDIN BOT CORE — Minimalista. Puro.")
    log("="*80)

    log(f"\n📋 Credenciales:")
    log(f"   Email: {LINKEDIN_EMAIL[:10]}...")
    log(f"   Pass:  {'*' * len(LINKEDIN_PASSWORD)}")

    with sync_playwright() as p:
        log("\n🔥 Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()

        try:
            # LINKEDIN LOGIN
            log("📍 LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(1)

            save_learning({"type": "page_loaded", "url": "linkedin.com/login"})

            # SCREENSHOT INICIAL
            page.screenshot(path="/tmp/start.png")
            log("📸 Screenshot: /tmp/start.png")

            # ─── ESCRIBIR EMAIL ───
            log("\n⌨️  EMAIL...")
            log(f"   Click en campo...")
            pyautogui.click(640, 370)
            time.sleep(0.5)

            log(f"   Escribiendo {len(LINKEDIN_EMAIL)} caracteres...")
            start_time = time.time()
            for i, char in enumerate(LINKEDIN_EMAIL):
                pyautogui.typewrite(char, interval=0.02)
                if (i+1) % 6 == 0:
                    elapsed = time.time() - start_time
                    log(f"   [{i+1}/{len(LINKEDIN_EMAIL)}] {elapsed:.1f}s")

            email_time = time.time() - start_time
            log(f"✅ EMAIL listo en {email_time:.1f}s")

            save_learning({
                "type": "email_written",
                "length": len(LINKEDIN_EMAIL),
                "time_seconds": email_time
            })

            time.sleep(0.5)

            # SCREENSHOT DESPUÉS DE EMAIL
            page.screenshot(path="/tmp/email-done.png")
            log("📸 Screenshot: /tmp/email-done.png")

            # ─── TAB + PASSWORD ───
            log("\n⌨️  PASSWORD...")
            log(f"   TAB...")
            pyautogui.press('tab')
            time.sleep(0.3)

            log(f"   Escribiendo {len(LINKEDIN_PASSWORD)} caracteres...")
            start_time = time.time()
            for i, char in enumerate(LINKEDIN_PASSWORD):
                pyautogui.typewrite(char, interval=0.02)
                if (i+1) % 3 == 0:
                    elapsed = time.time() - start_time
                    log(f"   [{i+1}/{len(LINKEDIN_PASSWORD)}] {elapsed:.1f}s")

            pass_time = time.time() - start_time
            log(f"✅ PASSWORD listo en {pass_time:.1f}s")

            save_learning({
                "type": "password_written",
                "length": len(LINKEDIN_PASSWORD),
                "time_seconds": pass_time
            })

            time.sleep(0.5)

            # SCREENSHOT FINAL ANTES DE ENTER
            page.screenshot(path="/tmp/ready.png")
            log("📸 Screenshot: /tmp/ready.png")

            # ─── ENTER ───
            log("\n🔑 ENTER...")
            pyautogui.press('enter')
            time.sleep(3)

            save_learning({"type": "enter_pressed"})

            # MONITOREAR LOGIN
            log("\n⏳ Esperando feed (10s MAX)...")
            login_start = time.time()

            while time.time() - login_start < 10:
                try:
                    current_url = page.url
                    if "feed" in current_url.lower():
                        login_time = time.time() - login_start
                        log(f"✅ LOGIN EXITOSO en {login_time:.1f}s")
                        log(f"   URL: {current_url}")

                        page.screenshot(path="/tmp/feed.png")
                        log("📸 Screenshot: /tmp/feed.png")

                        save_learning({
                            "type": "login_success",
                            "url": current_url,
                            "time_seconds": login_time
                        })

                        browser.close()
                        return True

                except:
                    pass

                time.sleep(2)

            log("❌ Login timeout - credenciales no aceptadas")
            page.screenshot(path="/tmp/failed.png")
            log("📸 Screenshot: /tmp/failed.png")
            log(f"   URL final: {page.url}")

            save_learning({"type": "login_failed", "url": page.url})
            return False

        except Exception as e:
            log(f"\n❌ ERROR: {e}")
            save_learning({"type": "error", "error": str(e)[:100]})
            return False


if __name__ == "__main__":
    success = main()
    log("\n" + "="*80)
    log("✅ ÉXITO" if success else "❌ FALLO")
    log("="*80)

    # Mostrar aprendizaje
    if os.path.exists(LEARNING_DB):
        with open(LEARNING_DB) as f:
            data = json.load(f)
        log(f"\n📚 Aprendizaje acumulado: {len(data.get('events', []))} eventos")
        for evt in data["events"][-5:]:
            log(f"   • {evt['type']}")

    sys.exit(0 if success else 1)
