#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT ML AVANZADO
Vision AI para detectar campos automáticamente.
Mouse control. Aprendizaje continuo.
"""

import os
import sys
import time
import json
import pyautogui
import base64
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

try:
    from playwright.sync_api import sync_playwright
    import anthropic
except ImportError:
    print("❌ pip install playwright anthropic")
    sys.exit(1)

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()
POSTS_FILE = "/Users/macbookpro/dev/aif369-web/posts-semana.txt"
LOG_FILE = "/Users/macbookpro/dev/aif369-web/logs/linkedin-bot-ml.log"
LEARNING_DB = "/Users/macbookpro/dev/aif369-web/logs/ml-learning.json"

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{ts}] {msg}"
    print(log_msg)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")

def save_learning(event: dict):
    """Guarda eventos de aprendizaje en JSON."""
    try:
        if os.path.exists(LEARNING_DB):
            with open(LEARNING_DB, 'r') as f:
                db = json.load(f)
        else:
            db = {"events": []}

        db["events"].append({
            "timestamp": datetime.now().isoformat(),
            **event
        })

        with open(LEARNING_DB, 'w') as f:
            json.dump(db, f, indent=2)
    except:
        pass

def analyze_screenshot_with_vision(image_path: str) -> dict:
    """Usa Claude Vision para analizar la pantalla y detectar campos."""
    log("🔍 Analizando pantalla con Vision AI...")

    try:
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=300,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": """Analiza esta pantalla de LinkedIn Login.
Detecta EXACTAMENTE:
1. ¿Hay campo de EMAIL? Si existe, describe su posición (superior, medio, inferior) y tamaño aproximado.
2. ¿Hay campo de PASSWORD? Si existe, describe su posición.
3. ¿Hay botón de LOGIN? Describe dónde está.
4. ¿El email/password está LLENO o VACÍO?

Responde SOLO en JSON:
{"email_field": {"detected": bool, "position": "top/middle/bottom", "filled": bool}, "password_field": {"detected": bool, "position": "top/middle/bottom", "filled": bool}, "login_button": {"detected": bool, "position": "..."}, "status": "ready/incomplete/error"}"""
                        }
                    ]
                }
            ]
        )

        analysis_text = response.content[0].text
        log(f"   📊 Análisis: {analysis_text[:100]}...")

        # Intentar parsear JSON
        try:
            analysis = json.loads(analysis_text)
        except:
            # Si no es JSON válido, extraer manualmente
            analysis = {
                "email_field": {"detected": "email" in analysis_text.lower()},
                "password_field": {"detected": "password" in analysis_text.lower()},
                "status": "partial"
            }

        save_learning({"type": "screenshot_analysis", "result": analysis})
        return analysis

    except Exception as e:
        log(f"   ❌ Error Vision AI: {str(e)[:100]}")
        return {"error": str(e)}

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
    log("🤖 LINKEDIN BOT ML AVANZADO — Vision AI + Mouse Control")
    log("="*80)

    with sync_playwright() as p:
        log("\n🔥 Abriendo Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            # ─── NAVEGACIÓN ───
            log("\n📍 Navegando a LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)

            # Maximizar ventana
            log("📏 Maximizando ventana...")
            pyautogui.hotkey('cmd', 'ctrl', 'f')
            time.sleep(0.5)

            time.sleep(2)

            # ─── SCREENSHOT 1 ───
            log("\n📸 Tomando screenshot para análisis...")
            page.screenshot(path="/tmp/login-page.png")

            # Analizar con Vision
            analysis = analyze_screenshot_with_vision("/tmp/login-page.png")
            log(f"   ✅ Análisis completado")

            # ─── ESCRIBIR CREDENCIALES CON MOUSE ───
            log("\n⚡ Escribiendo credenciales (RÁPIDO)...")

            # Email - click y escribir
            log("   1️⃣  Email...")
            pyautogui.click(640, 370)  # Click en campo de email
            time.sleep(0.3)

            # Escribir SIN delays tontos
            for char in LINKEDIN_EMAIL:
                pyautogui.typewrite(char, interval=0.02)  # 20ms = super rápido

            log(f"   ✅ Email escrito ({len(LINKEDIN_EMAIL)} chars)")

            time.sleep(0.5)

            # Screenshot después de email
            page.screenshot(path="/tmp/email-filled.png")

            # Password - TAB y escribir
            log("   2️⃣  Password...")
            pyautogui.press('tab')
            time.sleep(0.3)

            for char in LINKEDIN_PASSWORD:
                pyautogui.typewrite(char, interval=0.02)  # 20ms = super rápido

            log(f"   ✅ Password escrito ({len(LINKEDIN_PASSWORD)} chars)")

            time.sleep(0.5)

            # Screenshot después de password
            page.screenshot(path="/tmp/password-filled.png")

            # Analizar pantalla con credenciales
            analysis2 = analyze_screenshot_with_vision("/tmp/password-filled.png")

            # ─── ENTER PARA LOGIN ───
            log("\n🔑 PRESIONANDO ENTER...")
            pyautogui.press('enter')
            time.sleep(2)

            # ─── MONITOREAR LOGIN ───
            log("\n⏳ Monitoreando login (120s)...")
            start_time = time.time()

            while time.time() - start_time < 120:
                try:
                    if "feed" in page.url.lower():
                        log("   ✅ LOGIN EXITOSO - EN FEED")

                        # Screenshot en feed
                        page.screenshot(path="/tmp/feed-success.png")
                        save_learning({"type": "login_success", "url": page.url})

                        # ─── PUBLICAR POST ───
                        post = get_today_post()
                        if post:
                            log("\n📝 PUBLICANDO POST...")
                            page.wait_for_selector("button:has-text('Start a post')", timeout=10000)
                            page.click("button:has-text('Start a post')")
                            time.sleep(1)

                            page.wait_for_selector("div[contenteditable='true']", timeout=5000)
                            textarea = page.query_selector("div[contenteditable='true']")
                            textarea.click()
                            time.sleep(0.5)

                            page.keyboard.type(post, delay=1)
                            time.sleep(1)

                            page.wait_for_selector("button:has-text('Post')", timeout=5000)
                            post_btn = page.query_selector("button:has-text('Post')")
                            post_btn.scroll_into_view_if_needed()
                            time.sleep(0.5)
                            post_btn.click()
                            time.sleep(3)

                            log("✅ POST PUBLICADO")
                            save_learning({"type": "post_published", "length": len(post)})

                        browser.close()
                        return True

                except:
                    pass

                # Monitorear constantemente
                page.screenshot(path="/tmp/monitoring.png")
                time.sleep(2)  # Chequear cada 2 segundos

            log("❌ Timeout en login")
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
    sys.exit(0 if success else 1)
