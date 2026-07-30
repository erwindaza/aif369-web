#!/usr/bin/env python3
"""
✅ VALIDADOR DE POSTS - Asegura que los posts estén bien formateados
"""

import os
import re

POSTS_FILE = "/Users/macbookpro/dev/aif369-web/posts-semana-full.txt"

def validate_posts():
    if not os.path.exists(POSTS_FILE):
        print(f"❌ {POSTS_FILE} no encontrado")
        return False

    with open(POSTS_FILE) as f:
        content = f.read()

    print("=" * 80)
    print("📋 VALIDADOR DE POSTS - El Androide")
    print("=" * 80)

    # Patrones esperados (flexible para emojis)
    required_labels = [
        "LUNES - Automation Mondays",
        "MARTES - Martes de Transformación",
        "MIÉRCOLES - Miércoles de Éxito",
        "JUEVES - Jueves de Herramientas",
        "VIERNES - Viernes del Futuro",
        "SÁBADO - Sábado Estratégico MAÑANA",
        "SÁBADO - Sábado Estratégico TARDE",
        "DOMINGO - Domingo de Conexiones MAÑANA",
        "DOMINGO - Domingo de Conexiones TARDE",
    ]

    posts = []
    errors = []
    found_labels = []

    # Parsear usando separadores de sección (===)
    sections = content.split("=" * 80)

    for section in sections[1:]:  # Skip first empty section
        if not section.strip():
            continue

        lines = section.strip().split("\n")
        if len(lines) < 2:
            continue

        # Primera línea contiene el label
        header = lines[0].strip()

        # Encontrar matching label
        matching_label = None
        for label in required_labels:
            if label in header:
                matching_label = label
                found_labels.append(label)
                break

        if not matching_label:
            continue

        # El contenido está después del separador de dashes
        content_lines = []
        in_content = False

        for line in lines[1:]:
            if line.startswith("-" * 20):
                in_content = True
                continue
            if line.strip():
                content_lines.append(line)

        post_text = "\n".join(content_lines).strip()

        if post_text:
            posts.append({
                "label": matching_label,
                "header": header,
                "content": post_text,
                "length": len(post_text),
                "words": len(post_text.split())
            })

    # Validaciones
    print("\n📊 RESULTADOS:")
    print(f"\n   Posts encontrados: {len(posts)}/{len(required_labels)}")

    # Verificar labels faltantes
    missing = set(required_labels) - set(found_labels)
    if missing:
        print(f"\n   ❌ Labels faltantes:")
        for label in sorted(missing):
            print(f"      - {label}")
        errors.append(f"Faltan {len(missing)} labels")
    else:
        print(f"   ✅ Todos los labels presentes")

    # Validar contenido de cada post
    print(f"\n📝 ANÁLISIS DE POSTS:")
    for post in posts:
        label = post["label"]
        length = post["length"]
        words = post["words"]

        status = "✅" if 500 < length < 2000 and 50 < words < 400 else "⚠️"
        print(f"\n   {status} {label}")
        print(f"      Caracteres: {length} | Palabras: {words}")

        # Validaciones específicas
        if length < 500:
            errors.append(f"{label}: post muy corto ({length} caracteres)")
            print(f"      ❌ Post muy corto (mínimo 500)")
        elif length > 2000:
            errors.append(f"{label}: post muy largo ({length} caracteres)")
            print(f"      ❌ Post muy largo (máximo 2000)")

        # Verificar menciones de AIF369 y pricing
        content = post["content"].lower()

        if "aif369" not in content:
            print(f"      ⚠️ Falta mención de AIF369")

        if "$3k" not in content and "$3.000" not in content:
            print(f"      ⚠️ Falta mención de pricing básico ($3k)")

        if "$9k" not in content and "$9.000" not in content:
            print(f"      ⚠️ Falta mención de pricing premium ($9k)")

    # Resumen
    print("\n" + "=" * 80)
    if errors:
        print("❌ ERRORES ENCONTRADOS:")
        for error in errors:
            print(f"   - {error}")
        return False
    else:
        print("✅ TODOS LOS POSTS VÁLIDOS")
        print(f"\n   Total: {len(posts)} posts")
        print(f"   Cobertura: Semana completa + fin de semana")
        print(f"   Horarios: L-V 8:30 AM + S-D 14:00 y 18:00")

        # Estadísticas
        total_chars = sum(p["length"] for p in posts)
        total_words = sum(p["words"] for p in posts)
        avg_chars = total_chars // len(posts)
        avg_words = total_words // len(posts)

        print(f"\n   Estadísticas:")
        print(f"      Total caracteres: {total_chars}")
        print(f"      Total palabras: {total_words}")
        print(f"      Promedio por post: {avg_chars} caracteres, {avg_words} palabras")

        return True

def test_schedule():
    """Test: Simula el schedule de publicación"""
    print("\n" + "=" * 80)
    print("📅 SCHEDULE DE PUBLICACIÓN")
    print("=" * 80)

    schedule = {
        "Monday": "8:30 AM - Automation Mondays",
        "Tuesday": "8:30 AM - Martes de Transformación",
        "Wednesday": "8:30 AM - Miércoles de Éxito",
        "Thursday": "8:30 AM - Jueves de Herramientas",
        "Friday": "8:30 AM - Viernes del Futuro",
        "Saturday": "14:00 - Sábado Estratégico MAÑANA | 18:00 - Sábado Estratégico TARDE",
        "Sunday": "14:00 - Domingo de Conexiones MAÑANA | 18:00 - Domingo de Conexiones TARDE",
    }

    for day, times in schedule.items():
        print(f"\n   📅 {day}")
        for time_str in times.split(" | "):
            print(f"      {time_str}")

    return True

if __name__ == "__main__":
    success = validate_posts()
    test_schedule()

    print("\n" + "=" * 80)
    if success:
        print("✅ LISTO PARA PRODUCCIÓN")
    else:
        print("❌ NECESITA CORRECCIONES")
    print("=" * 80)

    exit(0 if success else 1)
