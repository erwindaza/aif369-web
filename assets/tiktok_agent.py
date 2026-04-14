#!/usr/bin/env python3
"""
AIF369 — TikTok Marketing Agent (Local)
=========================================
Automatiza la preparación de contenido para TikTok @aifactory369.

Funciones:
  1. Genera imágenes de texto overlay para cada clip de video
  2. Crea captions listos para copiar-pegar
  3. Graba screen recordings del sitio con Selenium
  4. Muestra el calendario y qué publicar hoy

Uso:
  python tiktok_agent.py today           # ¿Qué publico hoy?
  python tiktok_agent.py overlays 3      # Genera overlays del video 3
  python tiktok_agent.py overlays all    # Genera overlays de todos los videos
  python tiktok_agent.py captions        # Genera captions de todos los videos
  python tiktok_agent.py record 1        # Screen recording de services.html
  python tiktok_agent.py bio             # Muestra bio lista para copiar
  python tiktok_agent.py week            # Calendario de la semana

Requisitos:
  pip install Pillow
  pip install selenium webdriver-manager  # solo para screen recording
"""

import json
import os
import sys
import textwrap
from datetime import datetime, timedelta
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
PLAN_PATH = PROJECT_ROOT / "jsons" / "tiktok-content-plan.json"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "tiktok"
SITE_URL = "http://localhost:8888"  # local dev server
PROD_URL = "https://aif369.com"

# TikTok vertical video dimensions
TIKTOK_W = 1080
TIKTOK_H = 1920

# Colors (AIF369 brand)
BG_DARK = (11, 17, 32)        # #0B1120
BG_OVERLAY = (15, 31, 53)     # #0F1F35
PRIMARY = (0, 136, 255)       # #0088FF
SECONDARY = (0, 217, 204)     # #00D9CC
WHITE = (255, 255, 255)
GRAY = (168, 184, 216)        # #A8B8D8


def load_plan():
    """Load the TikTok content plan JSON."""
    if not PLAN_PATH.exists():
        print(f"❌ No se encontró {PLAN_PATH}")
        sys.exit(1)
    with open(PLAN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════
# COMMAND: today — ¿Qué publico hoy?
# ═══════════════════════════════════════════════════════════
def cmd_today(plan):
    """Show what to publish today based on the calendar."""
    today = datetime.now()
    day_name = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"][today.weekday()]

    # Calculate which week we're in (week 1 starts April 14, 2026 — next Monday)
    start_date = datetime(2026, 4, 13)  # Sunday before week 1
    days_since = (today - start_date).days
    week_num = min(max(days_since // 7 + 1, 1), 3)
    week_key = f"week_{week_num}"

    cal = plan.get("calendar", {})
    week = cal.get(week_key, {})

    print(f"\n{'═' * 60}")
    print(f"  📅 {today.strftime('%A %d de %B, %Y')}")
    print(f"  📍 Semana {week_num} del calendario TikTok")
    print(f"{'═' * 60}\n")

    if day_name in week:
        assignment = week[day_name]
        print(f"  🎬 HOY TOCA: {assignment}\n")

        # Find the video number
        for v in plan.get("videos", []):
            if f"VIDEO {v['id']}" in assignment.upper():
                _print_video_summary(v)
                break
    elif day_name in ("sabado", "domingo"):
        print("  🎉 Fin de semana — No hay publicacion programada.")
        print("  💡 Tip: Graba los 3 videos de la proxima semana en batch.\n")
    else:
        print(f"  📝 No hay video programado para {day_name}.")
        print(f"  💡 Los dias de publicacion son: lunes, miercoles, viernes.\n")

    # Show upcoming
    print(f"  📋 Semana {week_num} completa:")
    for d, v in week.items():
        marker = " 👈 HOY" if d == day_name else ""
        print(f"     {d.capitalize():12s} → {v}{marker}")
    print()


def _print_video_summary(video):
    """Print a single video's details for quick reference."""
    print(f"  {'─' * 56}")
    print(f"  📹 Video {video['id']}: {video['title']}")
    print(f"  ⏱  Duracion: {video['duration']}")
    print(f"  🎙  Formato: {video['format']}")
    print(f"  🎵  Audio: {video['audio']}")
    print(f"  🎯  Objetivo: {video['objective']}")
    print(f"  {'─' * 56}")

    # Print script sections
    script = video.get("script", {})
    for key, section in script.items():
        if isinstance(section, dict):
            overlay = section.get("texto_overlay", "")
            voz = section.get("voz", "")
            if overlay:
                print(f"\n  📌 [{key}]")
                print(f"     OVERLAY: {overlay}")
            if voz:
                print(f"     VOZ:     {voz}")

            # Handle nested points
            puntos = section.get("puntos", [])
            for p in puntos:
                if isinstance(p, dict):
                    print(f"     • {p.get('texto_overlay', p.get('overlay', ''))}: {p.get('voz', '')}")
                elif isinstance(p, str):
                    print(f"     • {p}")

    print(f"\n  📋 CAPTION (copiar-pegar):")
    print(f"  {video.get('caption', '')}")
    print(f"\n  # {video.get('hashtags', '')}")

    tips = video.get("tips", [])
    if tips:
        print(f"\n  💡 TIPS:")
        for tip in tips:
            print(f"     • {tip}")
    print()


# ═══════════════════════════════════════════════════════════
# COMMAND: overlays — Genera imágenes de texto overlay
# ═══════════════════════════════════════════════════════════
def cmd_overlays(plan, video_id):
    """Generate text overlay images for a video."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("❌ Falta Pillow. Instala con: pip install Pillow")
        sys.exit(1)

    videos = plan.get("videos", [])
    if video_id == "all":
        targets = videos
    else:
        targets = [v for v in videos if v["id"] == int(video_id)]
        if not targets:
            print(f"❌ Video {video_id} no encontrado. Videos disponibles: {[v['id'] for v in videos]}")
            return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for video in targets:
        vid = video["id"]
        video_dir = OUTPUT_DIR / f"video_{vid}"
        video_dir.mkdir(exist_ok=True)

        print(f"\n🎬 Generando overlays para Video {vid}: {video['title']}")

        script = video.get("script", {})
        clip_num = 0

        for key, section in script.items():
            if not isinstance(section, dict):
                continue

            overlay_text = section.get("texto_overlay", "")
            if not overlay_text:
                continue

            clip_num += 1
            img = _create_overlay_image(overlay_text, key)
            filename = video_dir / f"clip_{clip_num:02d}_{key}.png"
            img.save(filename)
            print(f"  ✅ {filename.name} — \"{overlay_text}\"")

            # Generate sub-overlays for points
            puntos = section.get("puntos", [])
            for i, p in enumerate(puntos):
                if isinstance(p, dict):
                    point_text = p.get("texto_overlay", p.get("overlay", ""))
                elif isinstance(p, str):
                    point_text = p
                else:
                    continue

                if point_text:
                    clip_num += 1
                    img = _create_overlay_image(point_text, f"point_{i+1}")
                    filename = video_dir / f"clip_{clip_num:02d}_point_{i+1}.png"
                    img.save(filename)
                    print(f"  ✅ {filename.name} — \"{point_text}\"")

        # Generate caption card
        caption = video.get("caption", "")
        if caption:
            img = _create_caption_card(caption, video.get("hashtags", ""))
            filename = video_dir / "caption_card.png"
            img.save(filename)
            print(f"  ✅ caption_card.png")

        print(f"  📁 {clip_num} overlays guardados en {video_dir}/")


def _create_overlay_image(text, label=""):
    """Create a TikTok-style text overlay image (1080x1920)."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (TIKTOK_W, TIKTOK_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try to load a bold font, fall back to default
    font_size = 72 if len(text) < 30 else 56 if len(text) < 60 else 44
    try:
        # macOS system fonts
        for font_path in [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSDisplay.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ]:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                break
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Wrap text
    max_chars = 20 if font_size >= 72 else 28 if font_size >= 56 else 35
    lines = textwrap.wrap(text, width=max_chars)
    line_height = font_size + 16

    # Calculate total height
    total_h = len(lines) * line_height
    y_start = (TIKTOK_H - total_h) // 2

    # Draw semi-transparent background
    padding = 40
    bg_top = y_start - padding
    bg_bottom = y_start + total_h + padding
    draw.rounded_rectangle(
        [(60, bg_top), (TIKTOK_W - 60, bg_bottom)],
        radius=24,
        fill=(0, 0, 0, 180)
    )

    # Draw text centered
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (TIKTOK_W - text_w) // 2
        y = y_start + i * line_height

        # White text with slight shadow
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 128))
        draw.text((x, y), line, font=font, fill=WHITE)

    # Label in corner
    if label:
        try:
            small_font = ImageFont.truetype(
                "/System/Library/Fonts/Helvetica.ttc", 24
            )
        except Exception:
            small_font = ImageFont.load_default()
        draw.text((40, 40), f"[{label}]", font=small_font, fill=SECONDARY)

    return img


def _create_caption_card(caption, hashtags):
    """Create a reference card with the caption text."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (TIKTOK_W, TIKTOK_H), BG_DARK)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
    except Exception:
        font = small = title_font = ImageFont.load_default()

    # Title
    draw.text((60, 80), "📋 CAPTION", font=title_font, fill=PRIMARY)
    draw.text((60, 140), "(copiar-pegar en TikTok)", font=small, fill=GRAY)

    # Divider
    draw.line([(60, 200), (TIKTOK_W - 60, 200)], fill=PRIMARY, width=2)

    # Caption text wrapped
    lines = textwrap.wrap(caption, width=35)
    y = 240
    for line in lines:
        draw.text((60, y), line, font=font, fill=WHITE)
        y += 50

    # Hashtags
    y += 40
    draw.line([(60, y), (TIKTOK_W - 60, y)], fill=SECONDARY, width=1)
    y += 20
    ht_lines = textwrap.wrap(hashtags, width=40)
    for line in ht_lines:
        draw.text((60, y), line, font=small, fill=SECONDARY)
        y += 40

    # AIF369 branding
    draw.text((60, TIKTOK_H - 100), "@aifactory369", font=font, fill=PRIMARY)

    return img


# ═══════════════════════════════════════════════════════════
# COMMAND: captions — Genera archivo de captions
# ═══════════════════════════════════════════════════════════
def cmd_captions(plan):
    """Generate a text file with all captions ready to copy-paste."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    captions_file = OUTPUT_DIR / "captions.txt"

    lines = [
        "=" * 60,
        "AIF369 TikTok Captions — @aifactory369",
        f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 60,
        "",
    ]

    for video in plan.get("videos", []):
        lines.append(f"{'─' * 60}")
        lines.append(f"VIDEO {video['id']}: {video['title']}")
        lines.append(f"{'─' * 60}")
        lines.append(f"CAPTION:")
        lines.append(video.get("caption", ""))
        lines.append("")
        lines.append(f"HASHTAGS:")
        lines.append(video.get("hashtags", ""))
        lines.append("")

    content = "\n".join(lines)
    captions_file.write_text(content, encoding="utf-8")
    print(f"\n✅ Captions guardados en {captions_file}")
    print(f"\n{content}")


# ═══════════════════════════════════════════════════════════
# COMMAND: record — Screen recording con Selenium
# ═══════════════════════════════════════════════════════════
def cmd_record(plan, video_id):
    """Take screenshots of the website pages for screen recording."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
    except ImportError:
        print("❌ Falta Selenium. Instala con: pip install selenium webdriver-manager")
        print("   Alternativa: usa la grabacion de pantalla del iPhone/Mac directamente.")
        sys.exit(1)

    # Pages to capture for each video
    video_pages = {
        1: [("services.html", "Servicios — scroll lento")],
        2: [("caso-ai-factory-ecommerce.html", "Caso estudio — seccion bias")],
        3: [("services.html", "Services — scroll rapido")],
        4: [("metodologia.html", "Metodo 369"), ("scorecard.html", "Scorecard")],
        5: [("scorecard.html", "Scorecard — demo en vivo")],
        9: [("caso-ai-factory-ecommerce.html", "Stack tecnico")],
    }

    pages = video_pages.get(int(video_id), [])
    if not pages:
        print(f"  ℹ️  Video {video_id} no requiere screen recording (es cara a cámara).")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    video_dir = OUTPUT_DIR / f"video_{video_id}"
    video_dir.mkdir(exist_ok=True)

    # Setup Chrome in mobile viewport (vertical TikTok)
    options = Options()
    options.add_argument("--headless")
    options.add_argument(f"--window-size={TIKTOK_W},{TIKTOK_H}")
    options.add_argument("--force-device-scale-factor=1")
    mobile_emulation = {"deviceMetrics": {"width": 390, "height": 844, "pixelRatio": 3}}
    options.add_experimental_option("mobileEmulation", mobile_emulation)

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception:
        driver = webdriver.Chrome(options=options)

    print(f"\n📸 Capturando screenshots para Video {video_id}:")
    base_url = SITE_URL  # Use local server

    for page, desc in pages:
        url = f"{base_url}/{page}"
        driver.get(url)
        driver.implicitly_wait(3)

        # Full page screenshot
        filename = video_dir / f"screenshot_{page.replace('.html', '')}.png"
        driver.save_screenshot(str(filename))
        print(f"  ✅ {filename.name} — {desc}")

        # Scroll and capture multiple frames (for video effect)
        total_height = driver.execute_script("return document.body.scrollHeight")
        viewport_height = driver.execute_script("return window.innerHeight")
        scroll_steps = min(total_height // viewport_height, 10)

        for i in range(1, scroll_steps + 1):
            scroll_pos = (total_height * i) // scroll_steps
            driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
            driver.implicitly_wait(0.5)
            frame_file = video_dir / f"scroll_{page.replace('.html', '')}_{i:02d}.png"
            driver.save_screenshot(str(frame_file))

        print(f"      + {scroll_steps} scroll frames capturados")

    driver.quit()
    print(f"\n  📁 Todo guardado en {video_dir}/")
    print(f"  💡 Importa las imagenes en CapCut como slideshow para simular scroll.")


# ═══════════════════════════════════════════════════════════
# COMMAND: bio — Muestra bio para copiar
# ═══════════════════════════════════════════════════════════
def cmd_bio(plan):
    """Show the bio text ready to copy-paste."""
    meta = plan.get("metadata", {})
    bio = meta.get("bio_suggestion", "")
    linktree = meta.get("linktree_urls", [])

    print(f"\n{'═' * 60}")
    print(f"  📝 BIO para @aifactory369 (copiar-pegar)")
    print(f"{'═' * 60}\n")
    print(f"  {bio}\n")
    print(f"{'─' * 60}")
    print(f"  🔗 LINKTREE URLs:")
    print(f"{'─' * 60}")
    for link in linktree:
        print(f"  {link['label']}")
        print(f"    → {link['url']}")
    print()


# ═══════════════════════════════════════════════════════════
# COMMAND: week — Calendario semanal
# ═══════════════════════════════════════════════════════════
def cmd_week(plan):
    """Show full 3-week calendar."""
    cal = plan.get("calendar", {})
    today = datetime.now()
    day_name = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"][today.weekday()]

    print(f"\n{'═' * 60}")
    print(f"  📅 Calendario TikTok @aifactory369")
    print(f"  📍 Hoy: {today.strftime('%A %d/%m/%Y')} ({day_name})")
    print(f"{'═' * 60}\n")

    for week_key in ["week_1", "week_2", "week_3"]:
        week = cal.get(week_key, {})
        week_label = week_key.replace("_", " ").upper()
        print(f"  {week_label}:")
        for d, v in week.items():
            print(f"    {d.capitalize():12s} → {v}")
        print()

    ongoing = cal.get("ongoing", "")
    if ongoing:
        print(f"  🔄 ONGOING: {ongoing}\n")


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
def main():
    if len(sys.argv) < 2:
        print("""
🎬 AIF369 TikTok Marketing Agent — @aifactory369

Uso:
  python tiktok_agent.py today           ¿Qué publico hoy?
  python tiktok_agent.py overlays 3      Genera overlays del video 3
  python tiktok_agent.py overlays all    Genera overlays de todos
  python tiktok_agent.py captions        Genera captions.txt
  python tiktok_agent.py record 1        Screenshots para screen recording
  python tiktok_agent.py bio             Bio lista para copiar
  python tiktok_agent.py week            Calendario completo
        """)
        sys.exit(0)

    plan = load_plan()
    command = sys.argv[1].lower()

    if command == "today":
        cmd_today(plan)
    elif command == "overlays":
        vid = sys.argv[2] if len(sys.argv) > 2 else "all"
        cmd_overlays(plan, vid)
    elif command == "captions":
        cmd_captions(plan)
    elif command == "record":
        vid = sys.argv[2] if len(sys.argv) > 2 else "3"
        cmd_record(plan, vid)
    elif command == "bio":
        cmd_bio(plan)
    elif command == "week":
        cmd_week(plan)
    else:
        print(f"❌ Comando desconocido: {command}")
        print("   Comandos válidos: today, overlays, captions, record, bio, week")
        sys.exit(1)


if __name__ == "__main__":
    main()
