#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - AUTO-CORRECCIÓN 30 MIN
Itera automáticamente, captura screenshots, se auto-corrige.
SIN intervención del usuario.
"""

import os
import time
import json
import pyautogui
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

try:
    from playwright.sync_api import sync_playwright
except:
    exit(1)

EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()
POSTS_FILE = "/Users/macbookpro/dev/aif369-web/posts-semana.txt"
ML_DB = "/Users/macbookpro/dev/aif369-web/logs/ml-30min.json"
SCREEN_DIR = "/tmp/linkedin-screens-30min"

os.makedirs(SCREEN_DIR, exist_ok=True)
os.makedirs(os.path.dirname(ML_DB), exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(f"{SCREEN_DIR}/log.txt", "a") as f:
        f.write(line + "\n")

def load_db():
    if os.path.exists(ML_DB):
        try:
            with open(ML_DB) as f:
                return json.load(f)
        except:
            pass
    return {
        "iterations": 0,
        "successes": 0,
        "email_x": 688,
        "email_y": 403,
        "password_y": 520,
        "attempts_this_session": []
    }

def save_db(db):
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

def try_login(email_x, email_y, password_y, iteration_num, attempt_num):
    """Intenta login con coordenadas específicas."""
    log(f"\n🔄 Iteración {iteration_num}, Intento {attempt_num}")
    log(f"   Coords: Email=({email_x},{email_y}), Password=({email_x},{password_y})")

    with sync_playwright() as p:
        log("🔥 Abriendo Firefox (sin Nightly)...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(5)

            # Screenshot 1: Inicial
            page.screenshot(path=f"{SCREEN_DIR}/i{iteration_num}_a{attempt_num}_01_inicio.png")
            log(f"   📸 Screenshot 1/5 tomada")

            # EMAIL CLICK
            log(f"   ✍️ Clickeando email en ({email_x},{email_y})...")
            pyautogui.click(email_x, email_y)
            time.sleep(0.3)

            # Screenshot 2: Después del click
            page.screenshot(path=f"{SCREEN_DIR}/i{iteration_num}_a{attempt_num}_02_email_click.png")
            log(f"   📸 Screenshot 2/5 tomada")

            # Escribir email
            log(f"   ⌨️ Escribiendo email ({len(EMAIL)} chars)...")
            for i, char in enumerate(EMAIL):
                pyautogui.typewrite(char, interval=0.020)
                if (i+1) % 6 == 0:
                    log(f"      {i+1}/{len(EMAIL)}...")

            time.sleep(0.5)

            # Screenshot 3: Después de email
            page.screenshot(path=f"{SCREEN_DIR}/i{iteration_num}_a{attempt_num}_03_email_escrito.png")
            log(f"   📸 Screenshot 3/5 tomada")

            # PASSWORD CLICK
            log(f"   🔐 Clickeando password en ({email_x},{password_y})...")
            pyautogui.click(email_x, password_y)
            time.sleep(0.3)

            # Escribir password
            log(f"   ⌨️ Escribiendo password ({len(PASSWORD)} chars)...")
            for char in PASSWORD:
                pyautogui.typewrite(char, interval=0.020)

            time.sleep(0.5)

            # Screenshot 4: Después de password
            page.screenshot(path=f"{SCREEN_DIR}/i{iteration_num}_a{attempt_num}_04_password_escrito.png")
            log(f"   📸 Screenshot 4/5 tomada")

            # ENTER
            log(f"   🔑 Presionando ENTER...")
            pyautogui.press('enter')
            time.sleep(3)

            # Esperar feed
            log(f"   ⏳ Esperando feed (15s)...")
            start = time.time()
            success = False

            while time.time() - start < 15:
                current_url = page.url
                if "feed" in current_url.lower():
                    elapsed = time.time() - start
                    log(f"\n   ✅ LOGIN EXITOSO en {elapsed:.1f}s")
                    page.screenshot(path=f"{SCREEN_DIR}/i{iteration_num}_a{attempt_num}_05_feed.png")
                    log(f"   📸 Screenshot 5/5 tomada (FEED)")

                    # PUBLICAR
                    post = get_post()
                    if post:
                        log(f"\n   📝 Publicando post ({len(post)} chars)...")
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
                            page.screenshot(path=f"{SCREEN_DIR}/i{iteration_num}_a{attempt_num}_06_publicado.png")
                        except Exception as e:
                            log(f"   ⚠️ Error publicando: {str(e)[:50]}")

                    success = True
                    browser.close()
                    return True

                time.sleep(1)

            # Screenshot 5: Fallo
            page.screenshot(path=f"{SCREEN_DIR}/i{iteration_num}_a{attempt_num}_05_fallo.png")
            log(f"   📸 Screenshot 5/5 tomada (FALLO)")
            log(f"   ❌ Login falló. URL: {current_url}")

            browser.close()
            return False

        except Exception as e:
            log(f"   ❌ ERROR: {e}")
            browser.close()
            return False

def main():
    log("="*80)
    log("🤖 LINKEDIN BOT - AUTO-CORRECCIÓN 30 MIN")
    log("="*80)
    log(f"📧 Email: {EMAIL}")
    log(f"🔐 Password: {'*' * len(PASSWORD)}")
    log(f"📁 Pantallas guardadas en: {SCREEN_DIR}")

    db = load_db()
    iteration = db["iterations"] + 1
    db["iterations"] = iteration

    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=30)

    log(f"\n⏰ Ejecutando hasta: {end_time.strftime('%H:%M:%S')} (~30 min)")

    # Coordenadas base
    base_x = 688
    base_y_email = 403
    base_y_pass = 520

    # Variaciones a probar
    x_offsets = [0, -10, 10, -20, 20]
    y_email_offsets = [0, -5, 5, -10, 10]
    y_pass_offsets = [0, -5, 5, -10, 10]

    attempt = 0

    while datetime.now() < end_time:
        attempt += 1

        # Seleccionar coordenadas para este intento
        if attempt == 1:
            x = base_x
            y_email = base_y_email
            y_pass = base_y_pass
        else:
            x_offset = x_offsets[(attempt - 1) % len(x_offsets)]
            y_e_offset = y_email_offsets[(attempt - 1) % len(y_email_offsets)]
            y_p_offset = y_pass_offsets[(attempt - 1) % len(y_pass_offsets)]

            x = base_x + x_offset
            y_email = base_y_email + y_e_offset
            y_pass = base_y_pass + y_p_offset

        success = try_login(x, y_email, y_pass, iteration, attempt)

        if success:
            log(f"\n✅ ¡ÉXITO! Coordenadas correctas:")
            log(f"   Email: ({x}, {y_email})")
            log(f"   Password: ({x}, {y_pass})")

            db["successes"] += 1
            db["email_x"] = x
            db["email_y"] = y_email
            db["password_y"] = y_pass
            save_db(db)

            log("\n" + "="*80)
            log("✅ SISTEMA COMPLETÓ CON ÉXITO")
            log("="*80)
            return True

        elapsed = (datetime.now() - start_time).total_seconds() / 60
        remaining = 30 - elapsed

        log(f"\n📊 Progreso: {attempt} intentos, {elapsed:.1f}/{30} min, {remaining:.1f} min restantes")

        # Esperar antes del próximo intento
        time.sleep(2)

    log("\n⏰ 30 minutos completados")
    log(f"   Intentos realizados: {attempt}")
    log(f"   Éxitos: {db['successes']}")

    save_db(db)

    log("\n" + "="*80)
    log("⏸️  TIEMPO COMPLETADO - ESPERANDO INSTRUCCIONES")
    log("="*80)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n⏸️  Detenido por usuario")
    except Exception as e:
        log(f"\n❌ ERROR CRÍTICO: {e}")
