#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - SIMPLE & SLOW
Captura fotos antes/después. Escribe lentamente. Auto-corrige.
"""

import os
import time
import json
import pyautogui
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
SCREEN_DIR = "/tmp/linkedin-simple-30min"
ML_DB = "/Users/macbookpro/dev/aif369-web/logs/ml-simple.json"

os.makedirs(SCREEN_DIR, exist_ok=True)
os.makedirs(os.path.dirname(ML_DB), exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(f"{SCREEN_DIR}/log.txt", "a") as f:
        f.write(line + "\n")

def save_db(data):
    with open(ML_DB, 'w') as f:
        json.dump(data, f, indent=2)

def load_db():
    if os.path.exists(ML_DB):
        try:
            with open(ML_DB) as f:
                return json.load(f)
        except:
            pass
    return {"iterations": 0, "successes": 0, "coords": []}

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

def try_coords(email_x, email_y, pass_y, iter_num, attempt_num):
    """Intenta login con coordenadas específicas."""
    log(f"\n{'='*70}")
    log(f"ITERACIÓN {iter_num} | INTENTO {attempt_num}")
    log(f"Coords: Email=({email_x},{email_y}), Pass=({email_x},{pass_y})")
    log(f"{'='*70}")

    with sync_playwright() as p:
        log("🔥 Firefox normal...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            log("📍 LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)

            log("⏳ Esperando 5 segundos...")
            time.sleep(5)

            # FOTO 1: INICIO
            log("📸 Foto 1: Estado inicial")
            page.screenshot(path=f"{SCREEN_DIR}/i{iter_num}_a{attempt_num}_01_inicio.png")

            # CLIC EN EMAIL
            log(f"🖱️ Clic en EMAIL ({email_x},{email_y})...")
            pyautogui.click(email_x, email_y)
            time.sleep(0.5)

            # FOTO 2: DESPUÉS DEL CLIC
            log("📸 Foto 2: Después del clic en email")
            page.screenshot(path=f"{SCREEN_DIR}/i{iter_num}_a{attempt_num}_02_clic_email.png")

            # ESCRIBIR EMAIL - MUY LENTAMENTE
            log(f"✍️ Escribiendo email lentamente ({len(EMAIL)} chars)...")
            for i, char in enumerate(EMAIL):
                pyautogui.typewrite(char, interval=0.050)  # 50ms entre caracteres
                if (i + 1) % 5 == 0:
                    log(f"   {i+1}/{len(EMAIL)}...")

            time.sleep(0.5)

            # FOTO 3: DESPUÉS DE EMAIL
            log("📸 Foto 3: Después de escribir email")
            page.screenshot(path=f"{SCREEN_DIR}/i{iter_num}_a{attempt_num}_03_email_escrito.png")

            # CLIC EN PASSWORD
            log(f"🖱️ Clic en PASSWORD ({email_x},{pass_y})...")
            pyautogui.click(email_x, pass_y)
            time.sleep(0.5)

            # FOTO 4: DESPUÉS DEL CLIC PASSWORD
            log("📸 Foto 4: Después del clic en password")
            page.screenshot(path=f"{SCREEN_DIR}/i{iter_num}_a{attempt_num}_04_clic_password.png")

            # ESCRIBIR PASSWORD - MUY LENTAMENTE
            log(f"🔐 Escribiendo password lentamente ({len(PASSWORD)} chars)...")
            for i, char in enumerate(PASSWORD):
                pyautogui.typewrite(char, interval=0.050)  # 50ms entre caracteres
                if (i + 1) % 3 == 0:
                    log(f"   {i+1}/{len(PASSWORD)}...")

            time.sleep(0.5)

            # FOTO 5: DESPUÉS DE PASSWORD
            log("📸 Foto 5: Después de escribir password")
            page.screenshot(path=f"{SCREEN_DIR}/i{iter_num}_a{attempt_num}_05_password_escrito.png")

            # ENTER
            log("⌨️ ENTER...")
            pyautogui.press('enter')
            time.sleep(3)

            # FOTO 6: DESPUÉS DE ENTER
            log("📸 Foto 6: Después de ENTER")
            page.screenshot(path=f"{SCREEN_DIR}/i{iter_num}_a{attempt_num}_06_enter.png")

            # ESPERAR FEED
            log("⏳ Esperando feed (15s)...")
            start = time.time()

            while time.time() - start < 15:
                url = page.url
                log(f"   URL: {url}")

                if "feed" in url.lower():
                    elapsed = time.time() - start
                    log(f"\n✅✅✅ ¡LOGIN EXITOSO EN {elapsed:.1f}s! ✅✅✅")

                    # FOTO 7: FEED
                    log("📸 Foto 7: Feed (éxito)")
                    page.screenshot(path=f"{SCREEN_DIR}/i{iter_num}_a{attempt_num}_07_feed_exito.png")

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

                            log("✅ POST PUBLICADO")
                            time.sleep(2)
                            page.screenshot(path=f"{SCREEN_DIR}/i{iter_num}_a{attempt_num}_08_publicado.png")
                        except Exception as e:
                            log(f"⚠️ Error publicando: {str(e)[:50]}")

                    browser.close()
                    return True

                time.sleep(1)

            # FOTO 7B: FALLO
            log("❌ Login rechazado")
            log("📸 Foto 7: Fallo (credenciales rechazadas)")
            page.screenshot(path=f"{SCREEN_DIR}/i{iter_num}_a{attempt_num}_07_fallo.png")

            browser.close()
            return False

        except Exception as e:
            log(f"❌ ERROR: {e}")
            browser.close()
            return False

def main():
    log("="*80)
    log("🤖 LINKEDIN BOT - SIMPLE & SLOW (30 MIN AUTO-CORRECCIÓN)")
    log("="*80)
    log(f"Email: {EMAIL}")
    log(f"Pass: {'*' * len(PASSWORD)}")
    log(f"Fotos: {SCREEN_DIR}")

    db = load_db()
    db["iterations"] += 1
    iter_num = db["iterations"]

    start = datetime.now()
    end = start + timedelta(minutes=30)

    log(f"\nInicio: {start.strftime('%H:%M:%S')}")
    log(f"Fin: {end.strftime('%H:%M:%S')}")

    # Coordenadas base
    email_x = 688
    email_y = 403
    pass_y = 520

    attempt = 0

    while datetime.now() < end:
        attempt += 1

        # Ajustar coordenadas si no es primer intento
        if attempt > 1:
            offset = ((attempt - 1) % 10) - 5  # -5 a +5
            email_y = 403 + offset
            pass_y = 520 + offset

        success = try_coords(email_x, email_y, pass_y, iter_num, attempt)

        if success:
            log(f"\n{'='*80}")
            log(f"✅ ÉXITO ENCONTRADO")
            log(f"Coordenadas correctas: Email=({email_x},{email_y}), Pass=({email_x},{pass_y})")
            log(f"{'='*80}")

            db["successes"] += 1
            db["coords"] = [email_x, email_y, pass_y]
            save_db(db)
            return True

        elapsed_min = (datetime.now() - start).total_seconds() / 60
        remaining_min = 30 - elapsed_min

        log(f"\n⏱️ {attempt} intentos | {elapsed_min:.1f}/{30} min | {remaining_min:.1f} min restantes")
        time.sleep(2)

    log(f"\n{'='*80}")
    log("⏰ 30 MINUTOS COMPLETADOS")
    log(f"Intentos: {attempt}")
    log(f"Éxitos: {db['successes']}")
    log(f"{'='*80}")

    save_db(db)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("\n⏸️ Detenido")
    except Exception as e:
        log(f"\n❌ ERROR: {e}")
