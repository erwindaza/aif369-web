#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT FINAL — Simple, directo, verificable
Sin Playwright para credenciales. Solo pyautogui.
"""

import os
import sys
import time
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
LOG_FILE = "/Users/macbookpro/dev/aif369-web/logs/linkedin-bot.log"

PUBLISH_SCHEDULE = {
    0: "🤖 Automation Mondays",
    1: "📈 Martes de Transformación",
    2: "🎯 Miércoles de Éxito",
    3: "🛠️ Jueves de Herramientas",
    4: "🚀 Viernes del Futuro",
    5: "💡 Sábado Estratégico",
}

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{ts}] {msg}"
    print(log_msg)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")


def get_today_post() -> str:
    if not os.path.exists(POSTS_FILE):
        return None

    today_weekday = datetime.now().weekday()
    if today_weekday == 6:
        return None

    day_label = PUBLISH_SCHEDULE.get(today_weekday)
    with open(POSTS_FILE, "r") as f:
        content = f.read()

    lines = content.split("\n")
    for i, line in enumerate(lines):
        if day_label in line:
            post_start = i + 3
            for j in range(post_start, len(lines)):
                if lines[j].startswith("-" * 80):
                    return "\n".join(lines[post_start:j]).strip()
    return None


def write_text_char_by_char(text: str, name: str):
    """Escribe texto carácter por carácter, mostrando progreso."""
    log(f"\n📝 ESCRIBIENDO {name}:")
    log(f"   Texto: {text}")
    log(f"   Longitud: {len(text)} caracteres\n")

    for i, char in enumerate(text):
        if char == '@':
            log(f"   [{i+1:2d}] '@' → Option+2")
            pyautogui.hotkey('option', '2')
        elif char == '.':
            log(f"   [{i+1:2d}] '.' → Period")
            pyautogui.press('period')
        elif char == '-':
            log(f"   [{i+1:2d}] '-' → Minus")
            pyautogui.press('minus')
        else:
            log(f"   [{i+1:2d}] '{char}'")
            pyautogui.typewrite(char, interval=0.05)

        time.sleep(0.15)  # Delay entre caracteres

    log(f"\n   ✅ {len(text)} caracteres escritos\n")


def main():
    log("="*80)
    log("🤖 LINKEDIN BOT FINAL")
    log("="*80)

    # Validar credenciales
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        log(f"❌ CREDENCIALES VACÍAS")
        log(f"   EMAIL: '{LINKEDIN_EMAIL}'")
        log(f"   PASSWORD: '{LINKEDIN_PASSWORD}'")
        return False

    log(f"\n✅ CREDENCIALES CARGADAS:")
    log(f"   EMAIL: {LINKEDIN_EMAIL}")
    log(f"   PASSWORD: {'*' * len(LINKEDIN_PASSWORD)}")

    post = get_today_post()
    if not post:
        log("❌ No se encontró post para hoy")
        return False

    log(f"\n✅ POST OBTENIDO ({len(post)} chars)")

    with sync_playwright() as p:
        log("\n🚀 ABRIENDO FIREFOX...")
        browser = p.firefox.launch(headless=False)
        page = browser.new_page(viewport={"width": 1280, "height": 1024})

        try:
            # ─── STEP 1: NAVEGACIÓN ───
            log("\n1️⃣  NAVEGANDO A LINKEDIN...")
            page.goto("https://www.linkedin.com/login", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=10000)
            log("   ✅ Página cargada")

            # Screenshot inicial
            page.screenshot(path="/tmp/01-linkedin-login.png")
            log("   📸 Screenshot: /tmp/01-linkedin-login.png")

            # ─── STEP 2: ESPERAR A ESTAR LISTO ───
            log("\n2️⃣  ESPERANDO A QUE ESTÉ LISTO...")
            time.sleep(3)

            # ─── STEP 3: ESCRIBIR EMAIL ───
            log("\n3️⃣  ESCRIBIENDO CREDENCIALES...")
            log("   Encontrando coordenadas exactas del campo de email...")

            # Usar Playwright para obtener las coordenadas exactas del input
            email_input = page.query_selector("input[type='email']")
            if email_input:
                bbox = email_input.bounding_box()
                if bbox:
                    click_x = bbox["x"] + bbox["width"] / 2
                    click_y = bbox["y"] + bbox["height"] / 2
                    log(f"   ✅ Campo encontrado en: ({click_x:.0f}, {click_y:.0f})")
                    pyautogui.click(click_x, click_y)
                    time.sleep(1)
                else:
                    log("   ⚠️  No se pudo obtener bounding box, usando coordenadas aproximadas...")
                    pyautogui.click(640, 370)
            else:
                log("   ⚠️  No se encontró input[type='email'], buscando cualquier input...")
                pyautogui.click(640, 370)

            write_text_char_by_char(LINKEDIN_EMAIL, "EMAIL")

            # Screenshot después de email
            page.screenshot(path="/tmp/02-email-escrito.png")
            log("   📸 Screenshot: /tmp/02-email-escrito.png")

            # ─── STEP 4: TAB A PASSWORD ───
            log("4️⃣  TAB AL CAMPO DE CONTRASEÑA...")
            pyautogui.press('tab')
            time.sleep(0.5)

            # ─── STEP 5: ESCRIBIR PASSWORD ───
            write_text_char_by_char(LINKEDIN_PASSWORD, "PASSWORD")

            # Screenshot después de password
            page.screenshot(path="/tmp/03-password-escrito.png")
            log("   📸 Screenshot: /tmp/03-password-escrito.png")

            # ─── STEP 6: PRESIONAR ENTER ───
            log("5️⃣  PRESIONANDO ENTER...")
            pyautogui.press('enter')
            time.sleep(3)

            # ─── STEP 7: ESPERAR LOGIN ───
            log("\n6️⃣  ESPERANDO A QUE INICIE SESIÓN (120s)...")
            try:
                page.wait_for_url("https://www.linkedin.com/feed/**", timeout=120000)
                log("   ✅ LOGIN EXITOSO - EN FEED")
            except:
                log("   ⚠️  Timeout esperando feed (posible 2FA)")
                if "feed" in page.url.lower():
                    log("   ✅ Se detectó /feed en URL, continuando...")
                else:
                    log(f"   ❌ URL actual: {page.url}")
                    raise Exception("No se logró login")

            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                log("   ⚠️  networkidle timeout, continuando igual...")
            time.sleep(2)

            # Screenshot en feed
            page.screenshot(path="/tmp/04-feed.png")
            log("   📸 Screenshot: /tmp/04-feed.png")

            # ─── STEP 8: PUBLICAR POST ───
            log("\n7️⃣  PUBLICANDO POST...")
            log("   Abriendo composer...")
            page.wait_for_selector("button:has-text('Start a post')", timeout=10000)
            page.click("button:has-text('Start a post')")
            time.sleep(2)

            log("   Esperando textarea...")
            page.wait_for_selector("div[contenteditable='true']", timeout=5000)
            textarea = page.query_selector("div[contenteditable='true']")
            textarea.click()
            time.sleep(1)

            log("   Escribiendo post con keyboard.type()...")
            page.keyboard.type(post, delay=2)
            time.sleep(2)

            # Screenshot con post escrito
            page.screenshot(path="/tmp/05-post-escrito.png")
            log("   📸 Screenshot: /tmp/05-post-escrito.png")

            log("   Buscando botón Publicar...")
            page.wait_for_selector("button:has-text('Post')", timeout=5000)
            post_btn = page.query_selector("button:has-text('Post')")
            post_btn.scroll_into_view_if_needed()
            time.sleep(1)

            log("   ✅ HACIENDO CLICK EN PUBLICAR...")
            post_btn.click()
            time.sleep(5)

            # Screenshot final
            page.screenshot(path="/tmp/06-post-publicado.png")
            log("   📸 Screenshot: /tmp/06-post-publicado.png")

            log("\n" + "="*80)
            log("✅ POST PUBLICADO EXITOSAMENTE")
            log("="*80)

            time.sleep(2)
            browser.close()
            return True

        except Exception as e:
            log(f"\n❌ ERROR: {e}")
            log("\n📸 Tomando screenshot de debug...")
            page.screenshot(path="/tmp/DEBUG-error.png")
            log("   Screenshot: /tmp/DEBUG-error.png")
            log(f"   URL: {page.url}")
            return False


if __name__ == "__main__":
    success = main()
    log("="*80)
    log("✅ ÉXITO" if success else "❌ FALLO")
    log("="*80)
    sys.exit(0 if success else 1)
