#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════╗
║  🤖 LINKEDIN AUTO-PUBLISHER BOT                                            ║
║  Publica posts automáticamente en LinkedIn (stealth mode)                   ║
║  Ejecuta diariamente a las 9 AM via cron                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Cargar .env.local
from dotenv import load_dotenv
load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

from playwright.sync_api import sync_playwright, expect

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────────────

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")
LINKEDIN_2FA_WAIT = 60  # Segundos para completar 2FA manualmente

POSTS_FILE = "/Users/macbookpro/dev/aif369-web/posts-semana.txt"
LOG_FILE = "/Users/macbookpro/dev/aif369-web/logs/linkedin-bot.log"

# Días de semana (0=lunes, 6=domingo)
PUBLISH_SCHEDULE = {
    0: "🤖 Automation Mondays",
    1: "📈 Martes de Transformación",
    2: "🎯 Miércoles de Éxito",
    3: "🛠️ Jueves de Herramientas",
    4: "🚀 Viernes del Futuro",
    5: "💡 Sábado Estratégico",
}

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
# OBTENER POST DEL DÍA
# ─────────────────────────────────────────────────────────────────────────

def get_today_post() -> str:
    """Lee el post correspondiente al día de hoy desde posts-semana.txt"""

    if not os.path.exists(POSTS_FILE):
        log(f"❌ ERROR: {POSTS_FILE} no encontrado")
        return None

    today_weekday = datetime.now().weekday()
    log(f"📅 Día de hoy: {today_weekday} (0=Lun, 1=Mar, 2=Mié, 3=Jue, 4=Vie, 5=Sab, 6=Dom)")

    if today_weekday == 6:  # Domingo
        log("ℹ️  Domingo: Sin publicación programada")
        return None

    day_label = PUBLISH_SCHEDULE.get(today_weekday, "Unknown")

    with open(POSTS_FILE, "r") as f:
        content = f.read()

    # Buscar el post del día
    lines = content.split("\n")
    post_start = None
    post_end = None

    for i, line in enumerate(lines):
        if day_label in line:
            # Encontró el título del día
            post_start = i + 3  # Saltar línea de score y separador
            # Buscar el siguiente separador
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
# PUBLICAR EN LINKEDIN
# ─────────────────────────────────────────────────────────────────────────

def publish_to_linkedin(post_content: str) -> bool:
    """Publica el post en LinkedIn usando Playwright stealth."""

    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        log("❌ ERROR: LINKEDIN_EMAIL o LINKEDIN_PASSWORD no configurados")
        log("   Configura en .env.local:")
        log("   LINKEDIN_EMAIL=tu@email.com")
        log("   LINKEDIN_PASSWORD=tu_password")
        return False

    try:
        with sync_playwright() as p:
            # Browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

            page = context.new_page()

            log("🚀 Iniciando navegador...")

            # ─── STEP 1: Login ───
            log("📝 Accediendo a LinkedIn...")
            page.goto("https://www.linkedin.com/login")
            page.wait_for_timeout(2000)

            # Email
            page.fill("input[name='session_key']", LINKEDIN_EMAIL)
            page.wait_for_timeout(1000)

            # Password
            page.fill("input[name='session_password']", LINKEDIN_PASSWORD)
            page.wait_for_timeout(1000)

            # Click login
            page.click("button[type='submit']")
            log("🔐 Esperando autenticación...")

            # Esperar a 2FA (si existe)
            try:
                page.wait_for_url("https://www.linkedin.com/feed/**", timeout=30000)
                log("✅ Autenticación completada")
            except:
                log("⏳ Requiere 2FA - esperando 60 segundos para completarlo manualmente...")
                page.wait_for_timeout(LINKEDIN_2FA_WAIT * 1000)

            # ─── STEP 2: Abrir composer ───
            log("📝 Abriendo composer de posts...")

            # Buscar botón "Start a post"
            page.wait_for_selector("button:has-text('Start a post')", timeout=10000)
            page.click("button:has-text('Start a post')")
            page.wait_for_timeout(2000)

            # ─── STEP 3: Escribir post ───
            log("✍️  Escribiendo post...")

            # Click en el textarea
            page.wait_for_selector("div[contenteditable='true']", timeout=5000)
            textarea = page.query_selector("div[contenteditable='true']")

            # Pegar contenido
            textarea.focus()
            page.keyboard.press("Control+A")
            page.keyboard.type(post_content, delay=1)  # delay para evitar detección

            page.wait_for_timeout(2000)

            # ─── STEP 4: Publicar ───
            log("🚀 Publicando...")

            # Buscar botón "Post"
            page.wait_for_selector("button:has-text('Post')", timeout=5000)
            post_button = page.query_selector("button:has-text('Post')")

            # Scroll si es necesario
            post_button.scroll_into_view_if_needed()
            page.wait_for_timeout(500)

            # Click
            post_button.click()

            # Esperar a confirmación
            page.wait_for_timeout(5000)

            log("✅ POST PUBLICADO EN LINKEDIN")

            # Cleanup
            context.close()
            browser.close()

            return True

    except Exception as e:
        log(f"❌ ERROR en publicación: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ─────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────

def main():
    log("="*80)
    log("🤖 LINKEDIN AUTO-PUBLISHER BOT — Iniciado")
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
    success = publish_to_linkedin(post)

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
