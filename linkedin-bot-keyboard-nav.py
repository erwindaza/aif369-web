#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - KEYBOARD NAVIGATION
Sin coordenadas. Usa TAB para navegar.
Más robusto que hacer clic.
"""

import os
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
    exit(1)

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()
POSTS_FILE = "/Users/macbookpro/dev/aif369-web/posts-semana.txt"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    with open("/Users/macbookpro/dev/aif369-web/logs/linkedin-keyboard.log", "a") as f:
        f.write(f"[{ts}] {msg}\n")

def get_post():
    if not os.path.exists(POSTS_FILE):
        return None
    today = datetime.now().weekday()
    if today == 6:
        return None
    sched = {0: "🤖 Automation Mondays", 1: "📈 Martes de Transformación", 2: "🎯 Miércoles de Éxito", 3: "🛠️ Jueves de Herramientas", 4: "🚀 Viernes del Futuro", 5: "💡 Sábado Estratégico"}
    label = sched.get(today)
    with open(POSTS_FILE) as f:
        lines = f.read().split("\n")
    for i, line in enumerate(lines):
        if label in line:
            for j in range(i+3, len(lines)):
                if lines[j].startswith("-"*80):
                    return "\n".join(lines[i+3:j]).strip()
    return None

log("="*80)
log("🤖 LINKEDIN BOT - KEYBOARD NAVIGATION")
log("="*80)

with sync_playwright() as p:
    log("\n🔥 Firefox...")
    browser = p.firefox.launch(headless=False)
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    try:
        log("📍 LinkedIn...")
        page.goto("https://www.linkedin.com/login", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=10000)
        time.sleep(2)

        # Close popup if exists
        try:
            btns = page.query_selector_all("button")
            for btn in btns:
                aria = btn.get_attribute("aria-label") or ""
                if "close" in aria.lower() or btn.text_content().strip() == "X":
                    btn.click()
                    time.sleep(0.3)
        except:
            pass

        page.screenshot(path="/tmp/kb_01_start.png")

        # KEYBOARD NAVIGATION
        log("\n⌨️ Navegación por teclado...")
        log("   1. Presionando TAB para encontrar campo de email...")

        # TAB hasta el primer input
        for i in range(5):
            pyautogui.press('tab')
            time.sleep(0.3)

        log("   2. Escribiendo email...")
        for char in LINKEDIN_EMAIL:
            pyautogui.typewrite(char, interval=0.015)

        log(f"   ✅ Email ({len(LINKEDIN_EMAIL)} chars)")
        time.sleep(0.2)

        log("   3. TAB a password...")
        pyautogui.press('tab')
        time.sleep(0.3)

        log("   4. Escribiendo password...")
        for char in LINKEDIN_PASSWORD:
            pyautogui.typewrite(char, interval=0.015)

        log(f"   ✅ Password ({len(LINKEDIN_PASSWORD)} chars)")
        time.sleep(0.2)

        page.screenshot(path="/tmp/kb_02_credentials.png")

        log("   5. Presionando ENTER...")
        pyautogui.press('enter')
        time.sleep(3)

        # ESPERAR FEED
        log("\n⏳ Esperando feed...")
        start = time.time()

        while time.time() - start < 15:
            if "feed" in page.url.lower():
                elapsed = time.time() - start
                log(f"✅ LOGIN EXITOSO en {elapsed:.1f}s")
                page.screenshot(path="/tmp/kb_03_feed.png")

                # PUBLICAR
                post = get_post()
                if post:
                    log(f"\n📝 Publicando...")
                    try:
                        page.wait_for_selector("button:has-text('Start a post')", timeout=5000)
                        page.click("button:has-text('Start a post')")
                        time.sleep(0.5)

                        page.wait_for_selector("div[contenteditable='true']", timeout=5000)
                        textarea = page.query_selector("div[contenteditable='true']")
                        textarea.click()
                        time.sleep(0.3)

                        page.keyboard.type(post, delay=0.2)
                        time.sleep(0.5)

                        page.wait_for_selector("button:has-text('Post')", timeout=5000)
                        btn = page.query_selector("button:has-text('Post')")
                        btn.scroll_into_view_if_needed()
                        time.sleep(0.3)
                        btn.click()

                        log("   ✅ POST PUBLICADO")
                        time.sleep(2)
                        page.screenshot(path="/tmp/kb_04_published.png")

                    except Exception as e:
                        log(f"   ⚠️ Error: {str(e)[:50]}")

                browser.close()
                exit(0)

            time.sleep(1)

        log(f"❌ Login timeout")
        page.screenshot(path="/tmp/kb_failed.png")
        exit(1)

    except Exception as e:
        log(f"\n❌ ERROR: {e}")
        exit(1)
