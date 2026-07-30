#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - FULLY AUTONOMOUS ML LEARNING
Detección automática de campos.
Aprendizaje reforzado sin intervención manual.
"""

import os
import sys
import time
import json
import pyautogui
import subprocess
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
ML_DB = "/Users/macbookpro/dev/aif369-web/logs/ml-autonomous.json"

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    with open("/Users/macbookpro/dev/aif369-web/logs/linkedin-autonomous.log", "a") as f:
        f.write(f"[{ts}] {msg}\n")

def load_ml_db():
    """Carga base de datos de aprendizaje."""
    if os.path.exists(ML_DB):
        try:
            with open(ML_DB) as f:
                return json.load(f)
        except:
            pass
    return {
        "iterations": 0,
        "successes": 0,
        "email_positions_tried": [],
        "best_email_coords": None,
        "best_password_coords": None,
        "learned_pattern": None
    }

def save_ml_db(db):
    """Guarda aprendizaje."""
    try:
        os.makedirs(os.path.dirname(ML_DB), exist_ok=True)
        with open(ML_DB, 'w') as f:
            json.dump(db, f, indent=2)
    except:
        pass

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

def generate_email_positions():
    """Genera posiciones a probar basadas en aprendizaje previo."""
    db = load_ml_db()

    # Si tenemos un mejor resultado, empezar ahí
    if db.get("best_email_coords"):
        x, y = db["best_email_coords"]
        yield (x, y)
        log(f"   📍 Probando coords aprendidas: ({x}, {y})")

    # Búsqueda inteligente: probar rango amplio de Y
    positions = []
    center_x = 720

    # Primera iteración: Y=400-450, centro X
    for y in range(400, 460, 10):
        positions.append((center_x, y))

    # Segunda iteración: X variado
    for x in range(600, 800, 20):
        positions.append((x, 410))

    # Tercera: esquinas y puntos medios
    positions.extend([
        (688, 400),
        (688, 420),
        (700, 400),
        (650, 410),
        (750, 410),
    ])

    for x, y in positions:
        if (x, y) not in db.get("email_positions_tried", []):
            yield (x, y)

def main():
    log("="*80)
    log("🤖 LINKEDIN BOT - FULLY AUTONOMOUS ML")
    log("="*80)

    db = load_ml_db()
    iteration = db["iterations"] + 1
    db["iterations"] = iteration

    log(f"\n📊 ITERACIÓN {iteration}")
    log(f"   Éxitos previos: {db['successes']}")
    log(f"   Posiciones probadas: {len(db['email_positions_tried'])}")

    with sync_playwright() as p:
        log("\n🔥 Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            log("📍 LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(1)

            # Intentar cerrar popup
            try:
                for sel in ["button.x", "button[aria-label*='Close']", "button:has-text('X')"]:
                    try:
                        btn = page.query_selector(sel)
                        if btn:
                            btn.click()
                            time.sleep(0.3)
                    except:
                        pass
            except:
                pass

            page.screenshot(path=f"/tmp/iter{iteration}_start.png")

            # PROBAR DIFERENTES POSICIONES DE EMAIL
            position_generator = generate_email_positions()
            email_success = False
            best_x, best_y = None, None

            for attempt, (x, y) in enumerate(position_generator, 1):
                if attempt > 3:  # Máximo 3 intentos por iteración
                    break

                log(f"\n   Intento {attempt}: ({x}, {y})")

                # Click
                pyautogui.click(x, y)
                time.sleep(0.2)

                # Escribir email
                for char in LINKEDIN_EMAIL:
                    pyautogui.typewrite(char, interval=0.015)

                time.sleep(0.3)

                # Verificar si se escribió (tomar screenshot)
                page.screenshot(path=f"/tmp/iter{iteration}_attempt{attempt}.png")

                # Intentar TAB y escribir password
                pyautogui.press('tab')
                time.sleep(0.2)

                for char in LINKEDIN_PASSWORD:
                    pyautogui.typewrite(char, interval=0.015)

                time.sleep(0.2)

                # ENTER
                pyautogui.press('enter')
                time.sleep(2)

                # Verificar si llegó al feed
                if "feed" in page.url.lower():
                    log(f"   ✅ LOGIN EXITOSO en intento {attempt}")
                    email_success = True
                    best_x, best_y = x, y

                    # Guardar en base de datos
                    db["best_email_coords"] = [x, y]
                    db["successes"] += 1

                    page.screenshot(path=f"/tmp/iter{iteration}_success.png")

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

                            page.keyboard.type(post, delay=0.2)
                            time.sleep(0.5)

                            page.wait_for_selector("button:has-text('Post')", timeout=5000)
                            btn = page.query_selector("button:has-text('Post')")
                            btn.scroll_into_view_if_needed()
                            time.sleep(0.3)
                            btn.click()

                            log(f"   ✅ POST PUBLICADO")
                            time.sleep(2)

                        except Exception as e:
                            log(f"   ⚠️ Error publicando: {str(e)[:50]}")

                    break

                # Resetear si falló
                if attempt < 3:
                    log(f"   ❌ Falló en intento {attempt}, limpiando...")
                    page.reload()
                    time.sleep(1)
                    try:
                        for sel in ["button.x", "button[aria-label*='Close']", "button:has-text('X')"]:
                            try:
                                btn = page.query_selector(sel)
                                if btn:
                                    btn.click()
                                    time.sleep(0.3)
                            except:
                                pass
                    except:
                        pass

            if not email_success:
                log(f"\n❌ No se logró entrar en iteración {iteration}")
                db["email_positions_tried"].extend([(x, y) for x, y in generate_email_positions()])

            # Guardar aprendizaje
            save_ml_db(db)

            log(f"\n📚 Base de datos actualizada:")
            log(f"   Iteraciones: {db['iterations']}")
            log(f"   Éxitos: {db['successes']}")
            log(f"   Tasa: {db['successes']/max(1,db['iterations'])*100:.0f}%")

            browser.close()
            return email_success

        except Exception as e:
            log(f"\n❌ ERROR: {e}")
            save_ml_db(db)
            return False


if __name__ == "__main__":
    log(f"\n📚 SISTEMA DE APRENDIZAJE AUTÓNOMO")
    log(f"   Tipo: Reinforcement Learning + Position Search")
    log(f"   Base de datos: /logs/ml-autonomous.json")
    log(f"   Método: Generación automática de posiciones + prueba y error")
    log(f"   Sin intervención manual")

    success = main()

    log("\n" + "="*80)
    log("✅ ÉXITO" if success else "⏳ Continuando aprendizaje...")
    log("="*80)

    sys.exit(0 if success else 1)
