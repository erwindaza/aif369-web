#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════╗
║  🤖 LINKEDIN RPA BOT — Robotic Process Automation                          ║
║  Controla mouse + teclado como un humano                                   ║
║  Evade detección de bots con delays realistas                              ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

try:
    import pyautogui
    import pyperclip
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ Dependencias no instaladas. Ejecuta:")
    print("   pip install pyautogui pyperclip pillow playwright")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")

POSTS_FILE = "/Users/macbookpro/dev/aif369-web/posts-semana.txt"
LOG_FILE = "/Users/macbookpro/dev/aif369-web/logs/linkedin-rpa-bot.log"

# Días de semana (0=lunes, 6=domingo)
PUBLISH_SCHEDULE = {
    0: "🤖 Automation Mondays",
    1: "📈 Martes de Transformación",
    2: "🎯 Miércoles de Éxito",
    3: "🛠️ Jueves de Herramientas",
    4: "🚀 Viernes del Futuro",
    5: "💡 Sábado Estratégico",
}

# Human-like delays (segundos)
DELAY_KEYSTROKE = (0.05, 0.15)  # Entre caracteres
DELAY_ACTION = (1.5, 3.0)  # Entre acciones
DELAY_WAIT = (2.0, 4.0)  # Esperas de página

# ─────────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────────

def log(message: str):
    """Log con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")


# ─────────────────────────────────────────────────────────────────────────
# UTILIDADES RPA
# ─────────────────────────────────────────────────────────────────────────

def human_delay(min_sec=0.5, max_sec=2.0):
    """Delay realista entre acciones."""
    time.sleep(random.uniform(min_sec, max_sec))


def type_human(text: str, delay_range=DELAY_KEYSTROKE):
    """Escribir texto con delays humanos (fallback para caracteres simples)."""
    for char in text:
        if char.isalnum() or char in ".-_":
            pyautogui.typewrite(char, interval=random.uniform(delay_range[0], delay_range[1]))
        else:
            pyautogui.hotkey('shift', 'right') if char == '@' else None


def paste_text(text: str):
    """Escribe texto carácter por carácter usando los atajos correctos para Mac."""
    log(f"   Escribiendo: {text[:15]}...")

    for i, char in enumerate(text):
        try:
            if char == '@':
                # Arroba: Option+2 en Mac español
                pyautogui.hotkey('option', '2')
                log(f"   [{i+1}] @ (option+2)")
            elif char == '.':
                # Punto: tecla period
                pyautogui.press('period')
                log(f"   [{i+1}] . (period)")
            elif char == '-':
                # Guion: tecla minus
                pyautogui.press('minus')
                log(f"   [{i+1}] - (minus)")
            else:
                # Letras y números normales
                pyautogui.typewrite(char, interval=0.05)

        except Exception as e:
            log(f"   ⚠️ Error en '{char}': {e}")

        # Delay consistente entre caracteres
        human_delay(0.15, 0.25)

    log(f"   ✅ {len(text)} caracteres escritos correctamente")
    human_delay(1, 2)


# ─────────────────────────────────────────────────────────────────────────
# OBTENER POST DEL DÍA
# ─────────────────────────────────────────────────────────────────────────

def get_today_post() -> str:
    """Lee el post correspondiente al día de hoy."""

    if not os.path.exists(POSTS_FILE):
        log(f"❌ ERROR: {POSTS_FILE} no encontrado")
        return None

    from datetime import datetime
    today_weekday = datetime.now().weekday()
    log(f"📅 Día de hoy: {today_weekday} (0=Lun, 1=Mar, 2=Mié, 3=Jue, 4=Vie, 5=Sab, 6=Dom)")

    if today_weekday == 6:  # Domingo
        log("ℹ️  Domingo: Sin publicación programada")
        return None

    day_label = PUBLISH_SCHEDULE.get(today_weekday, "Unknown")

    with open(POSTS_FILE, "r") as f:
        content = f.read()

    lines = content.split("\n")
    post_start = None
    post_end = None

    for i, line in enumerate(lines):
        if day_label in line:
            post_start = i + 3
            for j in range(post_start, len(lines)):
                if lines[j].startswith("-" * 80):
                    post_end = j
                    break
            break

    if post_start is None or post_end is None:
        log(f"❌ No se encontró post para: {day_label}")
        return None

    post = "\n".join(lines[post_start:post_end]).strip()
    log(f"✅ Post obtenido: {day_label[:30]}...")

    return post


# ─────────────────────────────────────────────────────────────────────────
# RPA — PUBLICAR EN LINKEDIN
# ─────────────────────────────────────────────────────────────────────────

def publish_to_linkedin_rpa(post_content: str) -> bool:
    """RPA: Abre navegador + publica como humano."""

    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        log("❌ ERROR: LINKEDIN_EMAIL o LINKEDIN_PASSWORD no configurados")
        return False

    browser = None
    try:
        with sync_playwright() as p:
            log("🚀 Iniciando Firefox...")
            browser = p.firefox.launch(headless=False)
            page = browser.new_page()

            # Función auxiliar: tomar screenshot para debugging
            def screenshot(name: str):
                path = f"/tmp/linkedin-bot-{name}.png"
                page.screenshot(path=path)
                log(f"   📸 Screenshot: {path}")
                return path

            # ─── STEP 1: Login ───
            log("📝 Accediendo a LinkedIn...")
            page.goto("https://www.linkedin.com/login")
            page.wait_for_load_state("networkidle", timeout=15000)
            human_delay(2, 3)

            # Esperar a que el campo de email sea visible
            log("⏳ Esperando campo de email...")
            page.wait_for_selector("input[type='text'], input[type='email'], input", timeout=10000)
            human_delay(1, 2)

            # Click en el primer input (campo de email)
            log("👆 Click en campo de email...")
            page.click("input", timeout=5000)
            human_delay(1, 2)

            # Escribir email con keyboard.type (más lento pero confiable)
            log(f"⌨️  Escribiendo email...")
            page.keyboard.type(LINKEDIN_EMAIL, delay=30)  # 30ms por carácter
            human_delay(1, 2)

            # Tab a password field
            log("📌 Tab al campo de contraseña...")
            page.press("input", "Tab")
            human_delay(1, 2)

            # Escribir password
            log(f"🔐 Escribiendo contraseña...")
            page.keyboard.type(LINKEDIN_PASSWORD, delay=30)  # 30ms por carácter
            human_delay(1, 2)

            # Click botón "Iniciar sesión"
            log("👆 Click en botón Iniciar sesión...")
            page.click("button:has-text('Iniciar sesión'), button[type='submit']", timeout=5000)
            human_delay(2, 3)

            # Click login button (usando Tab + Enter)
            log("👆 Haciendo click en Login...")
            pyautogui.press('enter')

            log("⏳ Esperando a que cargue el feed...")
            page.wait_for_url("https://www.linkedin.com/feed/**", timeout=60000)

            human_delay(3, 5)

            # ─── STEP 2: Abrir composer ───
            log("📝 Abriendo composer de posts...")

            # Buscar botón "Start a post"
            page.wait_for_selector("button:has-text('Start a post')", timeout=10000)
            page.click("button:has-text('Start a post')")

            human_delay(*DELAY_WAIT)

            # ─── STEP 3: Pegar post ───
            log("✍️  Pegando contenido del post...")

            # Click en el textarea
            page.wait_for_selector("div[contenteditable='true']", timeout=5000)
            textarea = page.query_selector("div[contenteditable='true']")
            textarea.click()

            human_delay(1, 2)

            # Pegar contenido (usar clipboard para ser más confiable)
            paste_text(post_content)

            human_delay(2, 3)

            # ─── STEP 4: Publicar ───
            log("🚀 Buscando botón Publicar...")

            page.wait_for_selector("button:has-text('Post')", timeout=5000)
            post_button = page.query_selector("button:has-text('Post')")

            # Scroll si es necesario
            post_button.scroll_into_view_if_needed()

            human_delay(1, 2)

            log("👆 Haciendo click en Publicar...")
            post_button.click()

            # Esperar a confirmación
            human_delay(3, 5)

            log("✅ POST PUBLICADO EN LINKEDIN")

            # Cleanup
            human_delay(2, 3)
            browser.close()

            return True

    except Exception as e:
        log(f"❌ ERROR en publicación RPA: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ─────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────

def main():
    log("="*80)
    log("🤖 LINKEDIN RPA BOT — Iniciado")
    log("="*80)

    # Obtener post del día
    post = get_today_post()

    if not post:
        log("ℹ️  No hay post para publicar hoy")
        return False

    log(f"\n📄 Contenido a publicar ({len(post)} caracteres):\n")
    print(post)
    print("")

    # Publicar
    success = publish_to_linkedin_rpa(post)

    log("="*80)
    if success:
        log("✅ ÉXITO - Post publicado")
    else:
        log("❌ FALLO - No se pudo publicar")
    log("="*80)

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
