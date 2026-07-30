#!/usr/bin/env python3
"""
🤖 LINKEDIN BOT v2 - ROBUSTO Y MEJORADO
Con manejo de reCAPTCHA, reintentos, y clicks humanizados
"""

import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv("/Users/macbookpro/dev/aif369-web/.env.local")

try:
    from playwright.sync_api import sync_playwright
    import pyautogui
except ImportError as e:
    print(f"❌ Instala: pip install playwright pyautogui python-dotenv")
    exit(1)

EMAIL = os.getenv("LINKEDIN_EMAIL", "").strip()
PASSWORD = os.getenv("LINKEDIN_PASSWORD", "").strip()
POSTS_FILE = "/Users/macbookpro/dev/aif369-web/posts-semana-full.txt"
LOG_DIR = "/Users/macbookpro/dev/aif369-web/logs"
LOG_FILE = f"{LOG_DIR}/linkedin-bot-v2.log"
STATS_FILE = f"{LOG_DIR}/bot-stats.json"

os.makedirs(LOG_DIR, exist_ok=True)

class LinkedInBot:
    def __init__(self):
        self.log_file = LOG_FILE
        self.max_retries = 3
        self.retry_delay = 5

    def log(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        with open(self.log_file, "a") as f:
            f.write(line + "\n")

    def save_stats(self, success, error=None):
        stats = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "error": error,
            "day": datetime.now().strftime("%A"),
        }
        try:
            if os.path.exists(STATS_FILE):
                with open(STATS_FILE) as f:
                    history = json.load(f)
            else:
                history = []
            history.append(stats)
            with open(STATS_FILE, "w") as f:
                json.dump(history, f, indent=2)
        except:
            pass

    def get_post(self):
        """Obtiene el post del día según el schedule"""
        if not os.path.exists(POSTS_FILE):
            self.log("❌ posts-semana-full.txt no encontrado")
            return None

        today = datetime.now().weekday()
        if today == 6:  # Domingo tiene dos posts
            hour = datetime.now().hour
            if hour < 14:
                label = "DOMINGO - Domingo de Conexiones MAÑANA"
            else:
                label = "DOMINGO - Domingo de Conexiones TARDE"
        elif today == 5:  # Sábado
            hour = datetime.now().hour
            if hour < 14:
                label = "SÁBADO - Sábado Estratégico MAÑANA"
            else:
                label = "SÁBADO - Sábado Estratégico TARDE"
        else:
            sched = {
                0: "LUNES - Automation Mondays",
                1: "MARTES - Martes de Transformación",
                2: "MIÉRCOLES - Miércoles de Éxito",
                3: "JUEVES - Jueves de Herramientas",
                4: "VIERNES - Viernes del Futuro",
            }
            label = sched.get(today)

        if not label:
            return None

        try:
            with open(POSTS_FILE) as f:
                lines = f.read().split("\n")

            for i, line in enumerate(lines):
                if label in line:
                    # Buscar el contenido entre este label y el siguiente separator
                    start = None
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith("---"):
                            start = j + 1
                            break

                    if start:
                        end = None
                        for j in range(start, len(lines)):
                            if lines[j].startswith("==="):
                                end = j
                                break

                        if end:
                            post = "\n".join(lines[start:end]).strip()
                            if post:
                                self.log(f"✓ Post obtenido: {len(post)} caracteres")
                                return post

            self.log(f"⚠️ No se encontró post para: {label}")
            return None
        except Exception as e:
            self.log(f"❌ Error leyendo posts: {e}")
            return None

    def wait_for_recaptcha(self, page, timeout=60):
        """Espera a que el usuario complete reCAPTCHA manualmente"""
        self.log("⚠️ reCAPTCHA detectado - esperando resolución manual...")
        start = time.time()
        while time.time() - start < timeout:
            if "feed" in page.url.lower() or "recaptcha" not in page.content().lower():
                self.log("✓ reCAPTCHA completado")
                return True
            time.sleep(2)
        return False

    def click_with_pyautogui(self, x, y, delay=0.5):
        """Click humanizado usando PyAutoGUI"""
        time.sleep(delay)
        pyautogui.moveTo(x, y, duration=0.3)
        time.sleep(0.2)
        pyautogui.click()
        time.sleep(0.3)

    def handle_publication_modal(self, page):
        """Maneja el modal de ajustes de publicación"""
        self.log("[Modal] Buscando opciones...")
        try:
            time.sleep(2)

            # Clickear "Solo contactos"
            self.log("[Modal] Intentando 'Solo contactos'...")
            labels = page.locator("label").all()
            for label in labels:
                try:
                    text = label.text_content()
                    if "Solo contactos" in text:
                        label.click()
                        self.log("   ✓ Clickeado 'Solo contactos'")
                        time.sleep(2)
                        break
                except:
                    pass

            # Verificar si HECHO está enabled
            time.sleep(1)
            hecho_btn = page.locator("button").filter(has_text="Hecho").first

            is_enabled = page.evaluate("""
                const btns = document.querySelectorAll('button');
                for (let btn of btns) {
                    if (btn.textContent.includes('Hecho')) {
                        return !btn.disabled;
                    }
                }
                return false;
            """)

            self.log(f"[Modal] ¿HECHO habilitado? {is_enabled}")

            if is_enabled:
                hecho_btn.click()
                self.log("   ✓ HECHO clickeado")
                time.sleep(3)
                return True
            else:
                self.log("   ⚠️ HECHO aún disabled, intentando JS...")
                page.evaluate("""
                    const btns = document.querySelectorAll('button');
                    for (let btn of btns) {
                        if (btn.textContent.includes('Hecho')) {
                            btn.click();
                            break;
                        }
                    }
                """)
                time.sleep(3)
                return True
        except Exception as e:
            self.log(f"   ❌ Error: {e}")
            return False

    def login(self, page):
        """Login con manejo de errores"""
        self.log("[1] Navegando a LinkedIn...")
        page.goto("https://www.linkedin.com/login", timeout=30000)
        time.sleep(5)

        # Verificar reCAPTCHA
        if "recaptcha" in page.content().lower():
            self.log("[2] reCAPTCHA detectado")
            if not self.wait_for_recaptcha(page):
                self.log("❌ reCAPTCHA timeout")
                return False

        self.log("[2] Buscando campos de email/password...")
        inputs = page.query_selector_all("input:not([type='hidden'])")

        if len(inputs) < 5:
            self.log(f"❌ Esperaba 5+ inputs, encontrados: {len(inputs)}")
            return False

        self.log(f"[3] Rellenando email en inputs[3]...")
        inputs[3].fill(EMAIL)
        time.sleep(0.5)

        self.log(f"[4] Rellenando password en inputs[4]...")
        inputs[4].fill(PASSWORD)
        time.sleep(0.5)

        self.log("[5] Presionando ENTER...")
        page.keyboard.press("Enter")
        time.sleep(3)

        # Esperar feed
        self.log("[6] Esperando feed (20s)...")
        for i in range(20):
            if "feed" in page.url.lower():
                self.log("✅ Login exitoso")
                time.sleep(3)
                return True
            time.sleep(1)

        self.log(f"❌ No llegó a feed. URL: {page.url}")
        return False

    def publish_post(self, page, post):
        """Publica un post"""
        self.log("[7] Abriendo post composer...")

        # Buscar botón "Start a post"
        found = False
        for _ in range(3):
            try:
                btns = page.locator("button").all()
                for btn in btns:
                    text = btn.text_content()
                    if "Start a post" in text or "Crear" in text:
                        btn.click(timeout=3000)
                        found = True
                        break
                if found:
                    break
            except:
                time.sleep(1)

        if not found:
            self.log("❌ No encontré botón de post")
            return False

        time.sleep(2)

        self.log("[8] Escribiendo post...")
        try:
            editor = page.locator("div[contenteditable='true']").first
            editor.click()
            time.sleep(0.5)
            page.keyboard.type(post, delay=0.02)
            time.sleep(1)
            self.log(f"   ✓ Post escrito ({len(post)} caracteres)")
        except Exception as e:
            self.log(f"   ❌ Error escribiendo: {e}")
            return False

        self.log("[9] Clickeando botón Publicar...")
        try:
            pub_btn = page.locator("button").filter(has_text="Post").first
            pub_btn.click(timeout=5000)
            time.sleep(5)
        except:
            self.log("   ⚠️ Usando JS para publicar...")
            page.evaluate("""
                const btns = document.querySelectorAll('button');
                for (let btn of btns) {
                    if (btn.textContent.includes('Post')) {
                        btn.click();
                        break;
                    }
                }
            """)
            time.sleep(5)

        # Verificar si apareció el modal
        if "Ajustes de la publicación" in page.content() or "Publication settings" in page.content():
            self.log("[10] Modal de ajustes detectado")
            return self.handle_publication_modal(page)

        self.log("✅ Post publicado sin modal")
        return True

    def run(self):
        """Ejecuta el bot completo"""
        self.log("=" * 80)
        self.log("🤖 LINKEDIN BOT v2 - INICIANDO")
        self.log("=" * 80)

        # Validar credenciales
        if not EMAIL or not PASSWORD:
            self.log("❌ EMAIL o PASSWORD no configurados en .env.local")
            self.save_stats(False, "Missing credentials")
            return False

        # Obtener post
        post = self.get_post()
        if not post:
            self.log("⚠️ No hay post para hoy")
            self.save_stats(True, "No post scheduled")
            return True

        # Ejecutar bot
        with sync_playwright() as p:
            try:
                self.log("\n🔥 Iniciando Firefox...")
                browser = p.firefox.launch(headless=False, channel="firefox")
                page = browser.new_page(viewport={"width": 1440, "height": 900})

                # Login
                if not self.login(page):
                    browser.close()
                    self.save_stats(False, "Login failed")
                    return False

                # Publicar
                if not self.publish_post(page, post):
                    browser.close()
                    self.save_stats(False, "Publish failed")
                    return False

                browser.close()
                self.log("\n" + "=" * 80)
                self.log("✅ PUBLICACIÓN EXITOSA")
                self.log("=" * 80)
                self.save_stats(True)
                return True

            except Exception as e:
                self.log(f"\n❌ ERROR: {e}")
                self.save_stats(False, str(e)[:100])
                return False

if __name__ == "__main__":
    bot = LinkedInBot()
    success = bot.run()
    exit(0 if success else 1)
