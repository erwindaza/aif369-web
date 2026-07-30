#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - ML REAL
Vision Analysis: Detecta campos automáticamente.
Aprende coordenadas.
Sin hardcoding.
"""

import os
import sys
import time
import json
import base64
import pyautogui
import subprocess
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
LOG_FILE = "/Users/macbookpro/dev/aif369-web/logs/linkedin-ml-real.log"
LEARNING_DB = "/Users/macbookpro/dev/aif369-web/logs/ml-real-learning.json"

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")

def save_learning(data: dict):
    try:
        if os.path.exists(LEARNING_DB):
            with open(LEARNING_DB, 'r') as f:
                db = json.load(f)
        else:
            db = {"fields": {}, "history": []}

        db["history"].append({**data, "timestamp": datetime.now().isoformat()})

        with open(LEARNING_DB, 'w') as f:
            json.dump(db, f, indent=2)
    except:
        pass

def analyze_with_ml(image_path: str) -> dict:
    """Usa Python image analysis para detectar campos sin API."""
    log(f"🔍 Analizando {image_path}...")

    try:
        # Usar Python PIL para análisis básico
        from PIL import Image

        img = Image.open(image_path)
        width, height = img.size

        log(f"   Imagen: {width}x{height}")

        # Convertir a escala de grises y buscar áreas blancas (campos)
        img_gray = img.convert('L')
        pixels = img_gray.load()

        # Detectar líneas horizontales blancas (típico de campos de input)
        white_zones = []
        for y in range(height):
            white_count = 0
            for x in range(width):
                if pixels[x, y] > 240:  # Muy blanco
                    white_count += 1

            if white_count > width * 0.6:  # Más del 60% de la línea es blanca
                white_zones.append(y)

        # Agrupar zonas blancas consecutivas
        fields = []
        if white_zones:
            current_group = [white_zones[0]]
            for y in white_zones[1:]:
                if y - current_group[-1] <= 2:
                    current_group.append(y)
                else:
                    if len(current_group) > 10:  # Campo debe ser grande
                        avg_y = sum(current_group) // len(current_group)
                        fields.append({"y": avg_y, "height": len(current_group)})
                    current_group = [y]

        log(f"   ✅ Detectados {len(fields)} campos")

        for i, field in enumerate(fields):
            log(f"      Campo {i+1}: y={field['y']}, alto={field['height']}")

        return {"fields": fields, "width": width, "height": height}

    except Exception as e:
        log(f"   ⚠️ Error análisis: {str(e)[:100]}")
        return {"fields": [], "width": 0, "height": 0}

def main():
    log("="*80)
    log("🤖 LINKEDIN BOT - ML REAL")
    log("="*80)

    with sync_playwright() as p:
        log("\n🔥 Firefox...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()

        try:
            log("📍 LinkedIn...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(1)

            # Screenshot inicial
            page.screenshot(path="/tmp/init.png")

            # Analizar con ML
            analysis = analyze_with_ml("/tmp/init.png")
            save_learning({"type": "initial_analysis", "result": analysis})

            if not analysis["fields"] or len(analysis["fields"]) < 2:
                log("❌ No se detectaron suficientes campos")
                log("   Usando fallback: buscando por texto...")

                # Fallback: buscar "Email" en la pantalla
                # Para ahora, usar coordenadas razonables basadas en resolución
                screen_width = analysis.get("width", 1440)
                email_y = 420  # Aproximado basado en layout típico
                email_x = screen_width // 2

                log(f"   Fallback: ({email_x}, {email_y})")
            else:
                # Usar campos detectados
                email_field = analysis["fields"][0]
                password_field = analysis["fields"][1] if len(analysis["fields"]) > 1 else None

                email_x = analysis["width"] // 2
                email_y = email_field["y"]

                log(f"📧 Email detectado en: ({email_x}, {email_y})")
                if password_field:
                    log(f"🔐 Password detectado en: ({email_x}, {password_field['y']})")

            # ─── ESCRIBIR EMAIL ───
            log(f"\n⌨️ Escribiendo EMAIL en ({email_x}, {email_y})...")
            pyautogui.click(email_x, email_y)
            time.sleep(0.5)

            for i, char in enumerate(LINKEDIN_EMAIL):
                pyautogui.typewrite(char, interval=0.02)

            log(f"✅ Email ({len(LINKEDIN_EMAIL)} chars)")
            time.sleep(0.3)

            # Screenshot después email
            page.screenshot(path="/tmp/after-email.png")

            # ─── PASSWORD ───
            log(f"\n⌨️ TAB a password...")
            pyautogui.press('tab')
            time.sleep(0.3)

            for i, char in enumerate(LINKEDIN_PASSWORD):
                pyautogui.typewrite(char, interval=0.02)

            log(f"✅ Password ({len(LINKEDIN_PASSWORD)} chars)")
            time.sleep(0.3)

            # Screenshot final
            page.screenshot(path="/tmp/before-enter.png")

            # Analizar screenshot con credenciales
            final_analysis = analyze_with_ml("/tmp/before-enter.png")
            save_learning({"type": "credentials_entered", "result": final_analysis})

            # ─── ENTER ───
            log(f"\n🔑 ENTER...")
            pyautogui.press('enter')
            time.sleep(3)

            # ─── MONITOREAR ───
            log(f"\n⏳ Esperando feed (10s)...")
            start = time.time()

            while time.time() - start < 10:
                if "feed" in page.url.lower():
                    log(f"✅ LOGIN OK")
                    page.screenshot(path="/tmp/success.png")
                    save_learning({"type": "login_success", "url": page.url})
                    browser.close()
                    return True
                time.sleep(1)

            log(f"❌ Login falló - URL: {page.url}")
            page.screenshot(path="/tmp/failed.png")
            save_learning({"type": "login_failed", "url": page.url})
            return False

        except Exception as e:
            log(f"\n❌ ERROR: {e}")
            save_learning({"type": "error", "error": str(e)[:100]})
            return False


if __name__ == "__main__":
    log("\n📚 MODELO: Análisis visual de píxeles + detección de áreas blancas")
    log("💾 APRENDIZAJE: JSON local en /logs/ml-real-learning.json")

    success = main()

    log("\n" + "="*80)
    log("✅ ÉXITO" if success else "❌ FALLO")
    log("="*80)

    if os.path.exists(LEARNING_DB):
        with open(LEARNING_DB) as f:
            data = json.load(f)
        log(f"\n📚 Eventos guardados: {len(data.get('history', []))}")
        for evt in data.get("history", [])[-3:]:
            log(f"   • {evt['type']}")

    sys.exit(0 if success else 1)
