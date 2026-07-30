#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT SMART
Local Vision: Tesseract OCR + OpenCV
Zero APIs. Aprende en JSON local.
"""

import os
import sys
import time
import json
import pyautogui
import cv2
import pytesseract
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ pip install playwright")
    sys.exit(1)

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()
LOG_FILE = "/Users/macbookpro/dev/aif369-web/logs/linkedin-smart.log"
LEARNING_DB = "/Users/macbookpro/dev/aif369-web/logs/smart-learning.json"

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def save_learning(event: dict):
    """Guarda aprendizajes localmente."""
    try:
        if os.path.exists(LEARNING_DB):
            with open(LEARNING_DB, 'r') as f:
                db = json.load(f)
        else:
            db = {"detections": [], "clicks": []}
        db["detections"].append({**event, "time": datetime.now().isoformat()})
        with open(LEARNING_DB, 'w') as f:
            json.dump(db, f, indent=2)
    except:
        pass

def detect_fields(image_path: str) -> dict:
    """Detecta campos EMAIL y PASSWORD usando OCR local."""
    log(f"🔍 Analizando con OCR local: {Path(image_path).name}")

    try:
        img = cv2.imread(image_path)
        if img is None:
            log("   ❌ No se pudo leer imagen")
            return {}

        # Convertir a escala de grises para OCR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # OCR - extraer texto
        text = pytesseract.image_to_string(gray)
        log(f"   📝 Texto detectado: {text[:100]}...")

        # Buscar palabras clave
        has_email = "email" in text.lower() or "correo" in text.lower()
        has_password = "password" in text.lower() or "contraseña" in text.lower() or "clave" in text.lower()

        # Detectar áreas blancas (campos de input típicamente)
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        fields = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 500 < area < 50000:  # Tamaño típico de campo
                x, y, w, h = cv2.boundingRect(contour)
                fields.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})

        result = {
            "has_email": has_email,
            "has_password": has_password,
            "fields_detected": len(fields),
            "fields": fields[:3]  # Top 3 campos
        }

        log(f"   ✅ Detectado: Email={has_email}, Password={has_password}, Campos={len(fields)}")
        save_learning(result)
        return result

    except Exception as e:
        log(f"   ❌ Error OCR: {str(e)[:100]}")
        return {}

def get_today_post() -> str:
    post_file = "/Users/macbookpro/dev/aif369-web/posts-semana.txt"
    if not os.path.exists(post_file):
        return None
    today_weekday = datetime.now().weekday()
    if today_weekday == 6:
        return None
    SCHEDULE = {0: "🤖 Automation Mondays", 1: "📈 Martes de Transformación", 2: "🎯 Miércoles de Éxito", 3: "🛠️ Jueves de Herramientas", 4: "🚀 Viernes del Futuro", 5: "💡 Sábado Estratégico"}
    day_label = SCHEDULE.get(today_weekday)
    with open(post_file, "r") as f:
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
    log("🤖 LINKEDIN BOT SMART — Local Vision + OCR")
    log("="*80)

    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        log("❌ Credenciales vacías")
        return False

    with sync_playwright() as p:
        log("\n🔥 Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            # Navegar
            log("📍 LinkedIn login...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(2)

            # Screenshot 1
            page.screenshot(path="/tmp/login.png")

            # Analizar campos
            analysis = detect_fields("/tmp/login.png")

            # ─── ESCRIBIR CON MOUSE ───
            log("\n⚡ Escribiendo EMAIL + PASSWORD...")

            # Usar campos detectados o coordenadas por defecto
            if analysis.get("fields"):
                email_field = analysis["fields"][0]
                email_x = email_field["x"] + email_field["w"] // 2
                email_y = email_field["y"] + email_field["h"] // 2
                log(f"   📧 Click en campo detectado: ({email_x}, {email_y})")
                pyautogui.click(email_x, email_y)
            else:
                log(f"   📧 Usando coordenadas por defecto")
                pyautogui.click(640, 370)

            time.sleep(0.3)

            # Escribir EMAIL - RÁPIDO
            for char in LINKEDIN_EMAIL:
                pyautogui.typewrite(char, interval=0.02)
            log(f"   ✅ Email ({len(LINKEDIN_EMAIL)} chars)")

            time.sleep(0.3)

            # TAB a password
            pyautogui.press('tab')
            time.sleep(0.2)

            # Escribir PASSWORD - RÁPIDO
            for char in LINKEDIN_PASSWORD:
                pyautogui.typewrite(char, interval=0.02)
            log(f"   ✅ Password ({len(LINKEDIN_PASSWORD)} chars)")

            time.sleep(0.3)

            # Screenshot 2
            page.screenshot(path="/tmp/filled.png")
            detect_fields("/tmp/filled.png")

            # ENTER
            log("\n🔑 ENTER...")
            pyautogui.press('enter')
            time.sleep(3)

            # Monitorear
            log("\n⏳ Login monitoring (120s)...")
            start = time.time()

            while time.time() - start < 120:
                try:
                    if "feed" in page.url.lower():
                        log("   ✅ LOGIN OK - FEED")
                        page.screenshot(path="/tmp/feed.png")
                        save_learning({"type": "login_success", "url": page.url})

                        # Publicar
                        post = get_today_post()
                        if post:
                            log("\n📝 Publicando...")
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

                            log("✅ POST OK")
                            save_learning({"type": "post_success"})

                        browser.close()
                        return True

                except:
                    pass

                # Monitoreo rápido
                page.screenshot(path="/tmp/monitoring.png")
                detect_fields("/tmp/monitoring.png")
                time.sleep(3)

            log("❌ Login timeout")
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
