#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT INTERACTIVO
Paso a paso. Verificación visual en cada acción.
Aprendiendo de lo que realmente está pasando en pantalla.
"""

import os
import time
import pyautogui
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

def step(number: int, title: str):
    print(f"\n{'='*80}")
    print(f"PASO {number}: {title}")
    print(f"{'='*80}\n")

def main():
    log("🚀 LINKEDIN BOT INTERACTIVO")
    log(f"   EMAIL: {LINKEDIN_EMAIL}")
    log(f"   PASSWORD: {'*' * len(LINKEDIN_PASSWORD)}\n")

    # PASO 1: Abrir Firefox
    step(1, "Abre Firefox y navega a https://www.linkedin.com/login")
    log("⏳ Esperando que abras LinkedIn manualmente...")
    log("   → Abre Firefox")
    log("   → Ve a https://www.linkedin.com/login")
    log("   → Haz click en el campo de EMAIL\n")
    input("PRESIONA ENTER cuando estés listo en el campo de email >>> ")

    # PASO 2: Escribir EMAIL
    step(2, "Escribir EMAIL carácter por carácter")
    log(f"📝 Escribiendo: {LINKEDIN_EMAIL}\n")

    for i, char in enumerate(LINKEDIN_EMAIL):
        if char == '@':
            log(f"   [{i+1:2d}] '@' → Presionando Option+2")
            pyautogui.hotkey('option', '2')
        elif char == '.':
            log(f"   [{i+1:2d}] '.' → Presionando Period")
            pyautogui.press('period')
        else:
            log(f"   [{i+1:2d}] '{char}'")
            pyautogui.typewrite(char, interval=0.05)
        time.sleep(0.2)

    log(f"\n✅ EMAIL ESCRITO ({len(LINKEDIN_EMAIL)} caracteres)\n")
    input("PAUSA: Verifica visualmente que se escribió correctamente. PRESIONA ENTER >>> ")

    # PASO 3: Tab a Password
    step(3, "Presionar TAB para ir al campo de PASSWORD")
    log("⏳ Presionando TAB...\n")
    pyautogui.press('tab')
    time.sleep(0.5)

    log("✅ TAB presionado\n")
    input("PAUSA: El cursor debe estar en el campo de PASSWORD. PRESIONA ENTER >>> ")

    # PASO 4: Escribir PASSWORD
    step(4, "Escribir PASSWORD carácter por carácter")
    log(f"📝 Escribiendo: {LINKEDIN_PASSWORD}\n")

    for i, char in enumerate(LINKEDIN_PASSWORD):
        log(f"   [{i+1:2d}] '{char}'")
        pyautogui.typewrite(char, interval=0.05)
        time.sleep(0.2)

    log(f"\n✅ PASSWORD ESCRITO ({len(LINKEDIN_PASSWORD)} caracteres)\n")
    input("PAUSA: Verifica que se escribió la contraseña. PRESIONA ENTER >>> ")

    # PASO 5: Presionar ENTER
    step(5, "Presionar ENTER para iniciar sesión")
    log("⏳ Presionando ENTER...\n")
    pyautogui.press('enter')
    time.sleep(5)

    log("✅ ENTER presionado\n")
    input("PAUSA: LinkedIn debería estar procesando el login. PRESIONA ENTER >>> ")

    # PASO 6: Esperar resultado
    step(6, "Esperando resultado del login")
    log("⏳ Esperando 30 segundos para que complete el login...\n")
    time.sleep(30)

    log("✅ Tiempo de espera completado\n")
    input("PAUSA: ¿Entraste al feed de LinkedIn? Si no, ¿qué pasó? PRESIONA ENTER >>> ")

    log("\n" + "="*80)
    log("🎯 DIAGNÓSTICO COMPLETADO")
    log("="*80)
    log("\nAhora sabemos exactamente qué está pasando.")
    log("Podemos ajustar el script basado en lo que vimos.\n")


if __name__ == "__main__":
    main()
