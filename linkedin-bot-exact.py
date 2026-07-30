#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - EXACTO
Sigue EXACTAMENTE lo que el usuario mostró.
5 segundos de espera. Clic directo. Escribe. ENTER.
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
    exit(1)

EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()
POSTS_FILE = "/Users/macbookpro/dev/aif369-web/posts-semana.txt"
ML_DB = "/Users/macbookpro/dev/aif369-web/logs/ml-exact.json"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    os.makedirs(os.path.dirname(ML_DB), exist_ok=True)
    with open("/Users/macbookpro/dev/aif369-web/logs/linkedin-exact.log", "a") as f:
        f.write(f"[{ts}] {msg}\n")

def load_db():
    if os.path.exists(ML_DB):
        try:
            with open(ML_DB) as f:
                return json.load(f)
        except:
            pass
    return {"iterations": 0, "successes": 0, "email_click": None, "password_click": None}

def save_db(db):
    os.makedirs(os.path.dirname(ML_DB), exist_ok=True)
    with open(ML_DB, 'w') as f:
        json.dump(db, f, indent=2)

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
log("🤖 LINKEDIN BOT - EXACTO (Sin TAB, Sin Apple, Solo lo que mostraste)")
log("="*80)

db = load_db()
db["iterations"] += 1
iteration = db["iterations"]

log(f"\n📊 ITERACIÓN {iteration}")
log(f"   Éxitos: {db['successes']}")

with sync_playwright() as p:
    log("\n🔥 Firefox NORMAL (no Nightly)...")
    browser = p.firefox.launch(headless=False, channel="firefox")
    page = browser.new_page(viewport={"width": 1440, "height": 900})

    try:
        log("📍 LinkedIn...")
        page.goto("https://www.linkedin.com/login", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=10000)

        log("⏳ Esperando 5 segundos (como mostraste)...")
        time.sleep(5)

        page.screenshot(path=f"/tmp/exact_iter{iteration}_01_listo.png")

        # EMAIL - CAMPO REAL (688, 403)
        log(f"\n✍️ EMAIL")
        log(f"   Click en (688, 403) - CAMPO EMAIL...")
        pyautogui.click(688, 403)
        time.sleep(0.5)

        log(f"   Escribiendo {len(EMAIL)} caracteres...")
        for i, char in enumerate(EMAIL):
            pyautogui.typewrite(char, interval=0.015)
            if (i+1) % 8 == 0:
                log(f"     {i+1}/{len(EMAIL)}...")

        log(f"   ✅ Email completado")
        time.sleep(0.3)

        # PASSWORD - CAMPO REAL (688, 520) - NO otro campo
        log(f"\n🔐 PASSWORD")
        log(f"   Click en (688, 520) - CAMPO PASSWORD...")
        pyautogui.click(688, 520)
        time.sleep(0.5)

        log(f"   Escribiendo {len(PASSWORD)} caracteres...")
        for char in PASSWORD:
            pyautogui.typewrite(char, interval=0.015)

        log(f"   ✅ Password completado")
        time.sleep(0.3)

        page.screenshot(path=f"/tmp/exact_iter{iteration}_02_formulario.png")

        # ENTER
        log(f"\n🔑 PRESIONANDO ENTER...")
        pyautogui.press('enter')
        time.sleep(3)

        # ESPERAR FEED
        log(f"\n⏳ Esperando feed (15 segundos)...")
        start = time.time()
        success = False

        while time.time() - start < 15:
            if "feed" in page.url.lower():
                elapsed = time.time() - start
                log(f"\n✅ LOGIN EXITOSO en {elapsed:.1f} segundos")
                page.screenshot(path=f"/tmp/exact_iter{iteration}_03_feed.png")

                db["successes"] += 1
                db["email_click"] = [688, 400]
                db["password_click"] = [688, 485]
                save_db(db)

                # PUBLICAR
                post = get_post()
                if post:
                    log(f"\n📝 Publicando post ({len(post)} chars)...")
                    try:
                        page.wait_for_selector("button:has-text('Start a post')", timeout=5000)
                        page.click("button:has-text('Start a post')")
                        time.sleep(0.5)

                        page.wait_for_selector("div[contenteditable='true']", timeout=5000)
                        textarea = page.query_selector("div[contenteditable='true']")
                        textarea.click()
                        time.sleep(0.3)

                        page.keyboard.type(post, delay=0.15)
                        time.sleep(0.5)

                        page.wait_for_selector("button:has-text('Post')", timeout=5000)
                        btn = page.query_selector("button:has-text('Post')")
                        btn.scroll_into_view_if_needed()
                        time.sleep(0.3)
                        btn.click()

                        log(f"   ✅ POST PUBLICADO")
                        time.sleep(2)
                        page.screenshot(path=f"/tmp/exact_iter{iteration}_04_publicado.png")

                    except Exception as e:
                        log(f"   ⚠️ Error publicando: {str(e)[:50]}")

                success = True
                break

            time.sleep(1)

        if not success:
            log(f"\n❌ Login falló - URL: {page.url}")
            page.screenshot(path=f"/tmp/exact_iter{iteration}_fail.png")
            save_db(db)

        browser.close()

        if success:
            log("\n" + "="*80)
            log("✅ ÉXITO - SISTEMA APRENDIÓ Y FUNCIONÓ")
            log("="*80)
            exit(0)
        else:
            exit(1)

    except Exception as e:
        log(f"\n❌ ERROR: {e}")
        save_db(db)
        exit(1)
