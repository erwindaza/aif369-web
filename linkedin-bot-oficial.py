#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT - OFICIAL
Método COMPROBADO que funciona. Copia exacta del código que logró login exitoso.
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

try:
    from playwright.sync_api import sync_playwright
except:
    print("❌ pip install playwright")
    exit(1)

EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()
POSTS_FILE = "/Users/macbookpro/dev/aif369-web/posts-semana-full.txt"
LOG_DIR = "/Users/macbookpro/dev/aif369-web/logs"
LOG_FILE = f"{LOG_DIR}/linkedin-oficial.log"

os.makedirs(LOG_DIR, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

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

def main():
    log("="*80)
    log("🤖 LINKEDIN BOT - OFICIAL (MÉTODO COMPROBADO)")
    log("="*80)

    with sync_playwright() as p:
        log("\n🔥 Firefox...")
        b = p.firefox.launch(headless=False)
        page = b.new_page(viewport={"width": 1440, "height": 900})

        try:
            log("[1] Abriendo...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            time.sleep(5)
            log("    ✅ Página cargada")

            log("[2] Cerrando popup...")
            close_btn = page.locator("button[aria-label*='Close'], button:has-text('X')").first
            try:
                close_btn.click(timeout=5000)
                log("    ✅ Popup cerrado")
                time.sleep(1)
            except:
                log("    ⚠️ No se encontró botón de cerrar")

            log("[3] Buscando inputs...")
            inputs = page.query_selector_all("input[type='text'], input[type='email'], input[type='password'], input:not([type='hidden'])")
            log(f"    Encontrados: {len(inputs)}")

            # Email en inputs[3], Password en inputs[4]
            if len(inputs) >= 5:
                log("[4] Email en inputs[3]...")
                inputs[3].fill(EMAIL)
                log("    ✅ Email rellenado")
                time.sleep(0.5)

                log("[5] Password en inputs[4]...")
                inputs[4].fill(PASSWORD)
                log("    ✅ Password rellenado")
                time.sleep(0.5)

            log("[6] ENTER...")
            page.keyboard.press("Enter")
            time.sleep(3)

            log("[7] Esperando feed (15s)...")
            for i in range(15):
                if "feed" in page.url.lower():
                    log(f"\n✅ LOGIN EXITOSO!\n")

                    # Intentar publicar post
                    post = get_post()
                    if post:
                        log("[8] Publicando post...")
                        try:
                            page.locator("button:has-text('Start a post')").first.click(timeout=5000)
                            time.sleep(0.5)
                            page.locator("div[contenteditable='true']").first.click()
                            time.sleep(0.3)
                            page.keyboard.type(post, delay=0.15)
                            time.sleep(0.5)
                            page.locator("button:has-text('Post')").first.click()
                            log("    ✅ Post publicado")
                        except Exception as e:
                            log(f"    ⚠️ Error: {str(e)[:40]}")
                    else:
                        log("[8] No hay post para hoy")

                    b.close()
                    log("\n" + "="*80)
                    log("✅ ÉXITO COMPLETADO")
                    log("="*80)
                    return True

                log(f"   {i+1}s - Esperando...")
                time.sleep(1)

            log(f"\n❌ Falló - URL final: {page.url}")
            b.close()
            return False

        except Exception as e:
            log(f"\n❌ ERROR: {e}")
            b.close()
            return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        log("\n⏸️ Detenido")
        exit(1)
    except Exception as e:
        log(f"\n❌ {e}")
        exit(1)
