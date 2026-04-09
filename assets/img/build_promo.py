#!/usr/bin/env python3
"""
Genera material promocional Black Week para AIF369.
- QR que apunta a aif369.com/education.html
- Flyers digitales (1080x1080 IG, 1080x1920 Story, 1200x628 LinkedIn/FB)
- Listos para imprimir o compartir en redes
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import qrcode

# ══════ CONFIG ══════
EDUCATION_URL = "https://aif369.com/education.html"
IMG_DIR = Path(__file__).parent
OUTPUT_DIR = IMG_DIR / "promo"
OUTPUT_DIR.mkdir(exist_ok=True)

# Colores (design system AIF369)
NAVY = (10, 22, 40)           # #0A1628
BLUE = (0, 136, 255)          # #0088FF
CYAN = (0, 217, 204)          # #00D9CC
GREEN = (16, 185, 129)        # #10B981
RED = (239, 68, 68)           # #EF4444
ORANGE = (245, 158, 11)       # #F59E0B
WHITE = (255, 255, 255)
LIGHT_GRAY = (200, 210, 230)
MUTED = (120, 140, 170)


def get_font(size, bold=False):
    """Try system fonts, fallback to default."""
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def generate_qr(url, size=400):
    """Generate QR code image for a URL."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=NAVY, back_color="white").convert("RGBA")
    return img.resize((size, size), Image.LANCZOS)


def draw_rounded_rect(draw, xy, fill, radius=20):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def draw_gradient_bar(img, xy, color_left, color_right, height=6):
    """Draw a horizontal gradient bar."""
    x0, y0, x1, y1 = xy
    draw = ImageDraw.Draw(img)
    width = x1 - x0
    for i in range(width):
        ratio = i / max(width - 1, 1)
        r = int(color_left[0] + (color_right[0] - color_left[0]) * ratio)
        g = int(color_left[1] + (color_right[1] - color_left[1]) * ratio)
        b = int(color_left[2] + (color_right[2] - color_left[2]) * ratio)
        draw.line([(x0 + i, y0), (x0 + i, y0 + height)], fill=(r, g, b))


def create_flyer_square():
    """1080x1080 Instagram/Social post."""
    W, H = 1080, 1080
    img = Image.new("RGBA", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    # Top gradient bar
    draw_gradient_bar(img, (0, 0, W, 6), RED, ORANGE)

    # BLACK WEEK tag
    font_tag = get_font(22, bold=True)
    draw_rounded_rect(draw, (60, 50, 420, 90), fill=RED, radius=20)
    draw.text((80, 54), "⚡ BLACK WEEK — 83% OFF", fill=WHITE, font=font_tag)

    # Main title
    font_title = get_font(52, bold=True)
    font_subtitle = get_font(28)
    draw.text((60, 120), "Cursos de", fill=LIGHT_GRAY, font=font_subtitle)
    draw.text((60, 160), "Inteligencia Artificial", fill=WHITE, font=font_title)
    draw.text((60, 225), "Big Data & Automatización", fill=CYAN, font=font_title)

    # Price
    font_old = get_font(30)
    font_new = get_font(60, bold=True)
    font_save = get_font(20)
    draw.text((60, 310), "USD $3,000", fill=MUTED, font=font_old)
    # Strikethrough
    bbox = draw.textbbox((60, 310), "USD $3,000", font=font_old)
    mid_y = (bbox[1] + bbox[3]) // 2
    draw.line([(bbox[0], mid_y), (bbox[2], mid_y)], fill=RED, width=2)
    # Arrow
    draw.text((290, 310), "→", fill=ORANGE, font=font_old)
    draw.text((60, 355), "USD $500", fill=GREEN, font=font_new)
    draw.text((60, 430), "Ahorras USD $2,500 — Oferta limitada", fill=ORANGE, font=font_save)

    # Courses list
    font_course = get_font(22)
    font_course_bold = get_font(22, bold=True)
    courses = [
        ("🧠", "IA Fundamentos", "Desde cero"),
        ("📊", "Big Data + IA", "Intermedio"),
        ("⚡", "Automatización Airflow", "Intermedio"),
        ("🚀", "Airflow + IA Avanzada", "Avanzado"),
    ]
    y = 480
    for emoji, name, level in courses:
        draw_rounded_rect(draw, (60, y, 620, y + 48), fill=(20, 35, 60), radius=10)
        draw.text((76, y + 10), f"{emoji}  {name}", fill=WHITE, font=font_course_bold)
        draw.text((480, y + 12), level, fill=CYAN, font=get_font(18))
        y += 58

    # Includes
    font_sm = get_font(18)
    draw.text((60, 730), "✓ Proyectos reales  ✓ Certificación  ✓ Coaching", fill=LIGHT_GRAY, font=font_sm)
    draw.text((60, 758), "✓ Comunidad  ✓ Empleo en BeJoby.com", fill=GREEN, font=font_sm)

    # QR Code
    qr = generate_qr(EDUCATION_URL, 260)
    qr_x, qr_y = 740, 430
    # White background for QR
    draw_rounded_rect(draw, (qr_x - 15, qr_y - 15, qr_x + 275, qr_y + 310), fill=WHITE, radius=16)
    img.paste(qr, (qr_x, qr_y), qr)
    # QR label
    font_qr = get_font(16, bold=True)
    draw.text((qr_x + 30, qr_y + 265), "Escanea e inscríbete", fill=NAVY, font=font_qr)

    # Bottom bar
    draw_rounded_rect(draw, (40, 820, W - 40, 1040), fill=(15, 30, 55), radius=16)
    font_brand = get_font(36, bold=True)
    font_url = get_font(22)
    font_contact = get_font(18)
    draw.text((80, 840), "AIF369", fill=BLUE, font=font_brand)
    draw.text((240, 850), "Aprende IA · Encuentra Empleo", fill=LIGHT_GRAY, font=font_url)
    draw.text((80, 900), "🌐 aif369.com/education.html", fill=CYAN, font=font_contact)
    draw.text((80, 930), "📱 WhatsApp: +56 9 9754 7192", fill=WHITE, font=font_contact)
    draw.text((80, 960), "📅 calendly.com/edaza-aif369/30min", fill=LIGHT_GRAY, font=font_contact)
    draw.text((80, 990), "💼 Empleo: BeJoby.com", fill=GREEN, font=font_contact)

    # Bottom gradient
    draw_gradient_bar(img, (0, H - 4, W, H), RED, ORANGE, height=4)

    return img


def create_flyer_story():
    """1080x1920 Instagram/WhatsApp Story."""
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    # Top gradient bar
    draw_gradient_bar(img, (0, 0, W, 8), RED, ORANGE)

    # BLACK WEEK tag
    font_tag = get_font(28, bold=True)
    draw_rounded_rect(draw, (60, 80, 520, 130), fill=RED, radius=24)
    draw.text((85, 86), "⚡ BLACK WEEK — 83% OFF", fill=WHITE, font=font_tag)

    # Main title
    font_title = get_font(64, bold=True)
    font_sub = get_font(34)
    draw.text((60, 180), "Cursos de", fill=LIGHT_GRAY, font=font_sub)
    draw.text((60, 230), "Inteligencia", fill=WHITE, font=font_title)
    draw.text((60, 310), "Artificial", fill=WHITE, font=font_title)
    draw.text((60, 400), "Big Data &", fill=CYAN, font=font_title)
    draw.text((60, 480), "Automatización", fill=CYAN, font=font_title)

    # Price block
    font_old = get_font(36)
    font_new = get_font(80, bold=True)
    font_save = get_font(24)
    draw.text((60, 600), "USD $3,000", fill=MUTED, font=font_old)
    bbox = draw.textbbox((60, 600), "USD $3,000", font=font_old)
    mid_y = (bbox[1] + bbox[3]) // 2
    draw.line([(bbox[0], mid_y), (bbox[2], mid_y)], fill=RED, width=3)
    draw.text((350, 600), "→", fill=ORANGE, font=font_old)
    draw.text((60, 660), "USD $500", fill=GREEN, font=font_new)
    draw.text((60, 760), "Ahorras USD $2,500 — Oferta por tiempo limitado", fill=ORANGE, font=font_save)

    # Courses
    font_course = get_font(28, bold=True)
    courses = [
        ("🧠", "IA Fundamentos"),
        ("📊", "Big Data + IA"),
        ("⚡", "Automatización con Airflow"),
        ("🚀", "Airflow + IA Avanzada"),
    ]
    y = 840
    for emoji, name in courses:
        draw_rounded_rect(draw, (60, y, W - 60, y + 60), fill=(20, 35, 60), radius=12)
        draw.text((85, y + 12), f"{emoji}  {name}", fill=WHITE, font=font_course)
        y += 75

    # Includes
    font_incl = get_font(22)
    y_incl = 1160
    includes = [
        "✓ Proyectos reales con datos reales",
        "✓ Certificación AIF369",
        "✓ Coaching experto personalizado",
        "✓ Acceso a empleo en BeJoby.com",
    ]
    for line in includes:
        draw.text((80, y_incl), line, fill=LIGHT_GRAY, font=font_incl)
        y_incl += 35

    # QR — centered
    qr = generate_qr(EDUCATION_URL, 320)
    qr_x = (W - 350) // 2
    qr_y = 1380
    draw_rounded_rect(draw, (qr_x - 15, qr_y - 15, qr_x + 335, qr_y + 380), fill=WHITE, radius=20)
    img.paste(qr, (qr_x, qr_y), qr)
    font_qr = get_font(22, bold=True)
    # Center text under QR
    draw.text((qr_x + 40, qr_y + 330), "Escanea e inscríbete →", fill=NAVY, font=font_qr)

    # Bottom
    font_brand = get_font(30, bold=True)
    font_contact = get_font(20)
    draw.text((60, 1800), "AIF369", fill=BLUE, font=font_brand)
    draw.text((190, 1805), "· aif369.com", fill=CYAN, font=font_contact)
    draw.text((60, 1840), "WhatsApp +56 9 9754 7192", fill=WHITE, font=font_contact)
    draw.text((520, 1840), "💼 BeJoby.com", fill=GREEN, font=font_contact)

    # Bottom gradient
    draw_gradient_bar(img, (0, H - 6, W, H), RED, ORANGE, height=6)

    return img


def create_flyer_landscape():
    """1200x628 LinkedIn / Facebook link preview."""
    W, H = 1200, 628
    img = Image.new("RGBA", (W, H), NAVY)
    draw = ImageDraw.Draw(img)

    # Top gradient
    draw_gradient_bar(img, (0, 0, W, 5), RED, ORANGE)

    # Left side — text
    font_tag = get_font(18, bold=True)
    draw_rounded_rect(draw, (50, 40, 340, 72), fill=RED, radius=16)
    draw.text((68, 44), "⚡ BLACK WEEK — 83% OFF", fill=WHITE, font=font_tag)

    font_title = get_font(38, bold=True)
    font_sub = get_font(22)
    draw.text((50, 95), "Cursos de IA, Big Data", fill=WHITE, font=font_title)
    draw.text((50, 145), "& Automatización", fill=CYAN, font=font_title)

    font_old = get_font(24)
    font_new = get_font(48, bold=True)
    draw.text((50, 210), "USD $3,000", fill=MUTED, font=font_old)
    bbox = draw.textbbox((50, 210), "USD $3,000", font=font_old)
    mid_y = (bbox[1] + bbox[3]) // 2
    draw.line([(bbox[0], mid_y), (bbox[2], mid_y)], fill=RED, width=2)
    draw.text((240, 210), "→", fill=ORANGE, font=font_old)
    draw.text((50, 250), "USD $500", fill=GREEN, font=font_new)

    font_save = get_font(18)
    draw.text((50, 315), "Ahorras USD $2,500 — Oferta limitada", fill=ORANGE, font=font_save)

    # Courses mini
    font_c = get_font(17)
    draw.text((50, 365), "🧠 IA Fund.  📊 Big Data  ⚡ Airflow  🚀 Avanzado", fill=LIGHT_GRAY, font=font_c)

    # Includes
    font_inc = get_font(16)
    draw.text((50, 405), "✓ Proyectos reales · Certificación · Coaching · Empleo BeJoby.com", fill=LIGHT_GRAY, font=font_inc)

    # Bottom bar
    draw_rounded_rect(draw, (30, 450, 700, 600), fill=(15, 30, 55), radius=12)
    font_brand = get_font(28, bold=True)
    font_url = get_font(18)
    draw.text((55, 465), "AIF369", fill=BLUE, font=font_brand)
    draw.text((195, 470), "Aprende IA · Encuentra Empleo", fill=LIGHT_GRAY, font=font_url)
    draw.text((55, 510), "🌐 aif369.com/education.html", fill=CYAN, font=font_url)
    draw.text((55, 540), "📱 +56 9 9754 7192", fill=WHITE, font=font_url)
    draw.text((350, 540), "💼 BeJoby.com", fill=GREEN, font=font_url)

    # Right side — QR
    qr = generate_qr(EDUCATION_URL, 280)
    qr_x, qr_y = 830, 60
    draw_rounded_rect(draw, (qr_x - 15, qr_y - 15, qr_x + 295, qr_y + 340), fill=WHITE, radius=16)
    img.paste(qr, (qr_x, qr_y), qr)
    font_qr = get_font(18, bold=True)
    draw.text((qr_x + 30, qr_y + 288), "Escanea e inscríbete →", fill=NAVY, font=font_qr)

    # Contact under QR
    font_sm = get_font(16)
    draw.text((qr_x, qr_y + 370), "📅 calendly.com/edaza-aif369", fill=LIGHT_GRAY, font=font_sm)
    draw.text((qr_x, qr_y + 395), "Asesoría gratuita 30 min", fill=CYAN, font=font_sm)

    # Bottom gradient
    draw_gradient_bar(img, (0, H - 4, W, H), RED, ORANGE, height=4)

    return img


def create_qr_standalone():
    """QR standalone grande para imprimir."""
    size = 800
    padding = 80
    total = size + padding * 2 + 120
    img = Image.new("RGBA", (total, total), WHITE)
    draw = ImageDraw.Draw(img)

    # QR
    qr = generate_qr(EDUCATION_URL, size)
    img.paste(qr, (padding, padding), qr)

    # Label below
    font_title = get_font(28, bold=True)
    font_url = get_font(20)
    font_sub = get_font(18)
    draw.text((padding, size + padding + 15), "AIF369 — Cursos de IA, Big Data & Automatización", fill=NAVY, font=font_title)
    draw.text((padding, size + padding + 55), "aif369.com/education.html", fill=BLUE, font=font_url)
    draw.text((padding, size + padding + 85), "Escanea para ver cursos y Black Week 83% OFF", fill=(100, 100, 100), font=font_sub)

    return img


def main():
    print("🎨 Generando material promocional Black Week AIF369...")
    print(f"   QR apunta a: {EDUCATION_URL}\n")

    # 1. QR Standalone
    qr_img = create_qr_standalone()
    qr_path = OUTPUT_DIR / "qr-education-cursos.png"
    qr_img.save(str(qr_path), "PNG")
    print(f"✓ QR standalone: {qr_path}")

    # 2. Flyer cuadrado (Instagram/Social)
    sq = create_flyer_square()
    sq_path = OUTPUT_DIR / "flyer-blackweek-1080x1080.png"
    sq.save(str(sq_path), "PNG")
    print(f"✓ Flyer cuadrado (IG/Social): {sq_path}")

    # 3. Flyer story (Instagram/WhatsApp)
    st = create_flyer_story()
    st_path = OUTPUT_DIR / "flyer-blackweek-story-1080x1920.png"
    st.save(str(st_path), "PNG")
    print(f"✓ Flyer story (IG/WA): {st_path}")

    # 4. Flyer horizontal (LinkedIn/Facebook)
    ln = create_flyer_landscape()
    ln_path = OUTPUT_DIR / "flyer-blackweek-linkedin-1200x628.png"
    ln.save(str(ln_path), "PNG")
    print(f"✓ Flyer LinkedIn/Facebook: {ln_path}")

    print(f"\n🎉 4 archivos generados en {OUTPUT_DIR}/")
    print("   Todos los QR apuntan a: aif369.com/education.html")
    print("   Listos para compartir en redes, WhatsApp o imprimir.")


if __name__ == "__main__":
    main()
