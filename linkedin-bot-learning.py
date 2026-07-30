#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - LEARNING CONTINUO
Visión en tiempo real. Auto-mejora. Publicación automática.
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
POSTS_FILE = "/Users/macbookpro/dev/aif369-web/posts-semana.txt"
LOG_FILE = "/Users/macbookpro/dev/aif369-web/logs/linkedin-learning.log"
ML_MEMORY = "/Users/macbookpro/dev/aif369-web/logs/ml-memory.json"

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def load_memory():
    """Carga memoria de aprendizaje previo."""
    if os.path.exists(ML_MEMORY):
        try:
            with open(ML_MEMORY, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "email_coords": None,
        "password_coords": None,
        "successes": 0,
        "failures": 0,
        "iterations": []
    }

def save_memory(memory: dict):
    """Guarda memoria de aprendizaje."""
    try:
        with open(ML_MEMORY, 'w') as f:
            json.dump(memory, f, indent=2)
    except:
        pass

def get_today_post() -> str:
    if not os.path.exists(POSTS_FILE):
        return None
    today_weekday = datetime.now().weekday()
    if today_weekday == 6:
        return None
    SCHEDULE = {0: "🤖 Automation Mondays", 1: "📈 Martes de Transformación", 2: "🎯 Miércoles de Éxito", 3: "🛠️ Jueves de Herramientas", 4: "🚀 Viernes del Futuro", 5: "💡 Sábado Estratégico"}
    day_label = SCHEDULE.get(today_weekday)
    with open(POSTS_FILE, "r") as f:
        lines = f.read().split("\n")
    for i, line in enumerate(lines):
        if day_label in line:
            post_start = i + 3
            for j in range(post_start, len(lines)):
                if lines[j].startswith("-" * 80):
                    return "\n".join(lines[post_start:j]).strip()
    return None

def main():
    log("="*80)
    log("🤖 LINKEDIN BOT - CONTINUOUS LEARNING")
    log("="*80)

    memory = load_memory()
    iteration = len(memory.get("iterations", [])) + 1

    log(f"\n📊 ITERACIÓN {iteration}")
    log(f"   Éxitos previos: {memory['successes']}")
    log(f"   Fallos previos: {memory['failures']}")

    with sync_playwright() as p:
        log("\n🔥 Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            log("📍 LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(1)

            # SCREENSHOT 1
            page.screenshot(path=f"/tmp/iter{iteration}_01_login.png")
            log(f"📸 Screenshot 1: iter{iteration}_01_login.png")

            # CREDENCIALES
            log(f"\n⌨️ EMAIL + PASSWORD...")

            # Usar coords aprendidas o por defecto
            email_coords = memory.get("email_coords")
            if email_coords and isinstance(email_coords, dict):
                email_x = email_coords.get("x", 640)
                email_y = email_coords.get("y", 420)
            else:
                email_x = 640
                email_y = 420

            log(f"   Click email en ({email_x}, {email_y})...")
            pyautogui.click(email_x, email_y)
            time.sleep(0.3)

            # Escribir email
            for char in LINKEDIN_EMAIL:
                pyautogui.typewrite(char, interval=0.015)

            log(f"   ✅ Email ({len(LINKEDIN_EMAIL)} chars en {len(LINKEDIN_EMAIL)*0.015:.1f}s)")

            time.sleep(0.2)

            # SCREENSHOT 2
            page.screenshot(path=f"/tmp/iter{iteration}_02_email.png")

            # Password
            pyautogui.press('tab')
            time.sleep(0.2)

            for char in LINKEDIN_PASSWORD:
                pyautogui.typewrite(char, interval=0.015)

            log(f"   ✅ Password ({len(LINKEDIN_PASSWORD)} chars)")

            time.sleep(0.2)

            # SCREENSHOT 3
            page.screenshot(path=f"/tmp/iter{iteration}_03_credentials.png")
            log(f"📸 Screenshot 3: iter{iteration}_03_credentials.png")

            # ENTER
            log(f"\n🔑 ENTER...")
            pyautogui.press('enter')
            time.sleep(2)

            # MONITOREAR - MÁXIMO 15 segundos
            log(f"\n⏳ Esperando feed (15s)...")
            start = time.time()
            success = False

            while time.time() - start < 15:
                # Screenshot de monitoreo
                page.screenshot(path=f"/tmp/iter{iteration}_monitoring.png")

                # Chequear URL
                if "feed" in page.url.lower():
                    success = True
                    log(f"✅ LOGIN EXITOSO en {time.time()-start:.1f}s")
                    log(f"   URL: {page.url}")

                    # SCREENSHOT 4
                    page.screenshot(path=f"/tmp/iter{iteration}_04_feed.png")

                    # PUBLICAR POST
                    post = get_today_post()
                    if post:
                        log(f"\n📝 PUBLICANDO POST ({len(post)} chars)...")

                        try:
                            page.wait_for_selector("button:has-text('Start a post')", timeout=5000)
                            page.click("button:has-text('Start a post')")
                            time.sleep(0.8)

                            page.wait_for_selector("div[contenteditable='true']", timeout=5000)
                            textarea = page.query_selector("div[contenteditable='true']")
                            textarea.click()
                            time.sleep(0.3)

                            page.keyboard.type(post, delay=0.5)
                            time.sleep(0.8)

                            # SCREENSHOT 5
                            page.screenshot(path=f"/tmp/iter{iteration}_05_post_ready.png")

                            page.wait_for_selector("button:has-text('Post')", timeout=5000)
                            post_btn = page.query_selector("button:has-text('Post')")
                            post_btn.scroll_into_view_if_needed()
                            time.sleep(0.3)
                            post_btn.click()

                            log(f"   ✅ POST PUBLICADO")

                            time.sleep(2)
                            page.screenshot(path=f"/tmp/iter{iteration}_06_published.png")

                        except Exception as e:
                            log(f"   ⚠️ Error publicando: {str(e)[:50]}")

                    break

                time.sleep(1)

            if not success:
                log(f"❌ Login timeout")
                page.screenshot(path=f"/tmp/iter{iteration}_failed.png")

            # ACTUALIZAR MEMORIA
            memory["iterations"].append({
                "iteration": iteration,
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "email_coords": {"x": email_x, "y": email_y},
                "password_coords": None
            })

            if success:
                memory["successes"] += 1
            else:
                memory["failures"] += 1

            save_memory(memory)

            log(f"\n📊 MEMORIA ACTUALIZADA")
            log(f"   Total éxitos: {memory['successes']}")
            log(f"   Total fallos: {memory['failures']}")
            log(f"   Tasa de éxito: {memory['successes']/(memory['successes']+memory['failures'])*100:.0f}%")

            browser.close()
            return success

        except Exception as e:
            log(f"\n❌ ERROR: {e}")
            return False


if __name__ == "__main__":
    log("\n🤖 MODELO: Aprendizaje continuo + Visión en tiempo real")
    log("💾 MEMORIA: /logs/ml-memory.json")
    log("📸 SCREENSHOTS: /tmp/iterN_*.png")

    success = main()

    log("\n" + "="*80)
    log("✅ ÉXITO" if success else "❌ FALLO")
    log("="*80)

    sys.exit(0 if success else 1)
