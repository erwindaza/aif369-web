#!/usr/bin/env python3
"""
🔍 DIAGNÓSTICO DE TECLADO MAC
Prueba cada tecla antes de usarla para escribir credenciales
"""

import pyautogui
import time

print("\n" + "="*80)
print("🔍 DIAGNÓSTICO DE TECLADO MAC")
print("="*80)
print("\n⚠️  Abre un editor de texto (Notes, TextEdit) y haz click en él")
print("   Tendrás 5 segundos para hacerlo...\n")

time.sleep(5)

# Test individual characters
tests = [
    ('e', "letra 'e'"),
    ('r', "letra 'r'"),
    ('w', "letra 'w'"),
    ('i', "letra 'i'"),
    ('n', "letra 'n'"),
    ('.', "punto (.)", 'period'),
    ('a', "letra 'a'"),
    ('d', "letra 'd'"),
    ('o', "letra 'o'"),
    ('@', "arroba (@)", 'option', '2'),
    ('g', "letra 'g'"),
    ('m', "letra 'm'"),
    ('l', "letra 'l'"),
    ('c', "letra 'c'"),
]

print("PRUEBAS DE TECLADO:\n")

for test in tests:
    char_name = test[1]
    keys = test[2:] if len(test) > 2 else None

    try:
        if keys:
            print(f"  Probando {char_name:20} → Presionando: {keys}")
            pyautogui.hotkey(*keys)
        else:
            print(f"  Probando {char_name:20} → Escribiendo: {test[0]}")
            pyautogui.typewrite(test[0], interval=0.1)

        time.sleep(0.3)
        print(f"    ✅ OK\n")
    except Exception as e:
        print(f"    ❌ FALLÓ: {e}\n")

print("\n" + "="*80)
print("✅ DIAGNÓSTICO COMPLETADO")
print("="*80)
print("\nAhora verifica en el editor de texto si todos los caracteres se escribieron correctamente.")
print("Si alguno falló, reporta el error y ajustaremos la configuración.\n")
