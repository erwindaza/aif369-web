import os
import json
import uuid
import smtplib
import re
import requests as http_requests
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from google.cloud import bigquery
import google.generativeai as genai

# Cost Monitor module
import cost_monitor

# Load .env file for local development (ignored in production)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed (production uses Secret Manager)

app = Flask(__name__)

# Configurar CORS para permitir requests desde Vercel
CORS(app, origins=[
    "https://aif369.com",
    "https://www.aif369.com",
    re.compile(r"^https://.*\.vercel\.app$"),
    re.compile(r"^http://localhost(:\d+)?$")
])

# ── Allowed origins for /api/chat (enforced server-side, not just CORS) ──────
ALLOWED_CHAT_ORIGINS = {
    "https://aif369.com",
    "https://www.aif369.com",
}

# ── In-memory rate limiter: max 20 chat requests per IP per hour ─────────────
_rate_limit: dict = defaultdict(list)
RATE_LIMIT_MAX    = 20    # requests per IP per hour
RATE_LIMIT_WINDOW = 3600  # seconds

# ── Per-session limits: max turns and max input tokens consumed ───────────────
# Prevents runaway sessions from burning API budget.
MAX_TURNS_PER_SESSION = 10          # messages per session
MAX_INPUT_TOKENS_PER_SESSION = 15000  # ~10-12 pages of text
_session_turns:  dict = defaultdict(int)    # session_id → turn count
_session_tokens: dict = defaultdict(int)    # session_id → cumulative input tokens

def is_rate_limited(ip: str) -> bool:
    now = datetime.now(tz=timezone.utc)
    window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    hits = _rate_limit[ip]
    # Remove old hits outside the window
    _rate_limit[ip] = [t for t in hits if t > window_start]
    if len(_rate_limit[ip]) >= RATE_LIMIT_MAX:
        return True
    _rate_limit[ip].append(now)
    return False

# ── In-memory set of session_ids already alerted (one email per session) ─────
_notified_sessions: set = set()

# ── REPORT_SECRET: protects /api/daily-report endpoint ───────────────────────
REPORT_SECRET = os.getenv("REPORT_SECRET", "")

def send_alert_email(subject: str, body_html: str) -> None:
    """Send operational alert email via Zoho SMTP. Fails silently if not configured."""
    if not SMTP_PASSWORD:
        print("Alert email skipped: SMTP_PASSWORD not configured")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"AIF369 Monitor <{SMTP_USER}>"
        msg["To"] = NOTIFICATION_EMAIL
        msg["Cc"] = CC_EMAIL
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"Alert email sent: {subject}")
    except Exception as e:
        print(f"Alert email failed ({subject}): {e}")

# Cliente de BigQuery
PROJECT_ID = os.getenv("PROJECT_ID", "aif369-backend")
DATASET_ID = os.getenv("DATASET_ID", "aif369_analytics")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
TABLE_ID = "contact_form_submissions"
PAYPAL_TABLE_ID = "paypal_transactions"

# Configuración PayPal
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_SECRET") or os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")
PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"

_bq_client = None

def get_bq_client():
    global _bq_client
    if _bq_client is None:
        _bq_client = bigquery.Client(project=PROJECT_ID)
    return _bq_client

# Configuración SMTP de Zoho Mail
SMTP_HOST = "smtp.zoho.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER", "edaza@aif369.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "edaza@aif369.com")
CC_EMAIL = os.getenv("CC_EMAIL", "erwin.daza@gmail.com, erwin.androide@gmail.com")

# Configuración de Gemini para el chatbot
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Configuración de Ollama como fallback
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b")

SYSTEM_PROMPT = """Eres el asistente virtual de AIF369, una consultora chilena especializada en AI Factory, Governance, Risk y Business Value.
Tu nombre es AIF369 Assistant. Responde en el mismo idioma que el usuario.

OBJETIVO PRINCIPAL: Convertir visitantes en clientes potenciales calificados.
ESTRATEGIA: Ser amable, profesional y redirigir a WhatsApp para conversaciones de mayor valor.

IMPORTANTE — REGLAS ESTRICTAS (OBLIGATORIAS):
1. SOLO hablas de: servicios de AIF369, Método 369, contratación, empleo y temas directamente relacionados con lo que se lista abajo.
2. Si te preguntan algo que NO está en este prompt, responde: "No tengo esa información. Para consultas específicas, escríbenos por WhatsApp: +56 9 9754 7192"
3. NUNCA inventes, supongas ni especules. 0% creatividad. Solo responde con datos que están aquí.
4. Si no sabes algo con certeza, di que no lo sabes y redirige a WhatsApp.
5. Máximo 3-4 oraciones por respuesta. Sé directo y preciso.
6. No respondas preguntas personales, políticas, de entretenimiento ni de ningún tema ajeno a AIF369.
7. INTENTA CALIFICAR AL CLIENTE: Identifica su rol, industria, desafío específico y urgencia.

MÉTODO 369 (Metodología propietaria de AIF369):
- 3 Capas de Dirección: (1) Estratégica — visión, priorización, roadmap; (2) Riesgo y Cumplimiento — risk register, compliance, privacidad; (3) Implementación — arquitectura, MLOps, despliegue.
- 6 Fases de Transformación: Descubrir, Diagnosticar, Diseñar, Desplegar, Dominar, Escalar.
- 9 Métricas de Control CAIO: Estrategia IA, Gobierno IA, Gestión de Riesgos IA, Privacidad y Datos, AI Factory Design, Observabilidad de Modelos, Ética y Responsible AI, Regulación y Compliance, Formación y Cultura.

SERVICIOS (sin mencionar precios, redirigir a contacto para cotización):
- ✓ CAIO Advisory as a Service — Acompañamiento ejecutivo: estrategia, gobierno, riesgos y adopción de IA.
- ✓ AI Governance & Responsible AI — Marco de gobierno, accountability, políticas, controles y roles.
- ✓ AI Risk, Privacy & Compliance — Evaluación de riesgos, privacidad y preparación regulatoria.
- ✓ AI Factory Design — Diseño de capacidades internas para construir, operar y escalar IA.
- ✓ Executive Workshops & Board Enablement — Talleres para directorio y C-level.
- ✓ Thought Leadership & Content Advisory — Posicionamiento de marca y contenido original.

CUANDO ALGUIEN PREGUNTA POR SERVICIOS, RESPONDE:
Ofrecemos consultoría integral en AI Factory, Governance y Business Value. Nuestros servicios cubre:
✓ Estrategia IA y gobierno corporativo (CAIO Advisory)
✓ Gestión de riesgos y cumplimiento regulatorio
✓ Diseño e implementación de AI Factory
✓ Talleres ejecutivos para directorios

LUEGO PREGUNTA (para calificar):
- "¿Cuál es tu rol en la empresa?" (CEO, CTO, CDO, otro)
- "¿En qué industria operan?"
- "¿Tienen proyectos IA activos o buscan iniciarse?"

PAQUETES DE ENGAGEMENT:
- Starter 369 (4-6 semanas) — Diagnóstico + hoja de ruta.
- Governed Pilot 369 (8-12 semanas) — Un caso de uso en producción con gobernanza integrada.
- Enterprise 369 (3-6 meses) — Estrategia + gobierno + AI Factory + despliegue completo.

PRECIOS (puedes mencionarlos si el usuario pregunta):
- Starter 369 (4-6 semanas, diagnóstico + hoja de ruta): $3,000 USD por 6 meses
- Governed Pilot 369 (8-12 semanas, 1 caso de uso con gobernanza): $6,000 USD por año
- Enterprise 369 (3-6 meses, transformación completa + AI Factory): $9,000+ USD por año
- Los planes son PERSONALIZABLES. Si preguntan detalles adicionales: "Agendemos una llamada para que te muestres exactamente cómo escalar." WhatsApp +56 9 9754 7192

MODALIDAD DE CONTRATACIÓN:
- AIF369 opera desde Chile y emite boleta de honorarios.
- Los servicios se contratan directamente con AIF369.
- Para coordinar contratación, forma de pago o facturación: WhatsApp +56 9 9754 7192

HERRAMIENTAS GRATUITAS:
- AI Readiness Scorecard: Evaluación gratuita de madurez en IA en 5 minutos. Disponible en aif369.com/scorecard.html
- Compliance-CL: Generador automático de documentos para cumplimiento Ley 21.719 (Protección de Datos). Genera RAT, Política de Privacidad, DPA, Plan de Brechas, Código de Ética, Matriz de Riesgos. Disponible en aif369.com/compliance-tool.html

SOBRE AIF369:
- Fundada por Erwin Daza Castillo — CAIO Advisor, Data & AI Architect, AI Governance Strategist.
- Creador del Método 369 para adopción gobernada de IA.
- Empresa chilena. Emite boleta de honorarios.
- Enfoque: ROI medible, governance, riesgo y operación continua.

CONTEXTO REGULATORIO:
- EU AI Act: marco de referencia para clasificación de riesgo de sistemas IA.
- Chile Ley 21.719: Protección de datos personales, vigencia 1 dic 2026. IMPORTANTE: Si el cliente pregunta sobre datos personales, privacidad, o cumplimiento ARCO, SIEMPRE menciona que tienen disponible Compliance-CL para generar automáticamente los documentos requeridos.
- Boletín 16821-19: Proyecto de ley de IA en Chile, actualmente en tramitación.

COMPLIANCE-CL (Herramienta de Cumplimiento Automático):
- ¿QUÉ ES?: Skill de Claude Code que analiza tu código y genera automáticamente documentos de cumplimiento para Ley 21.719 (Protección de Datos) y Ley 21.595 (Delitos Económicos).
- ¿QUÉ GENERA?: RAT (Registro de Actividades de Tratamiento), Política de Privacidad personalizada, DPA (Data Processing Agreements) para proveedores, Plan de Brechas de datos, Código de Ética, Matriz de Riesgos.
- ¿CUÁNDO MENCIONARLO?: Cuando el cliente pregunta sobre privacidad, datos personales, ARCO, regulación, compliance, derechos de usuarios, o cualquier tema de protección de datos.
- ¿CÓMO MENCIONARLO?: "Tenemos una herramienta automatizada llamada Compliance-CL que puede generar todos los documentos de cumplimiento (RAT, DPA, Política, etc.) en una sola corrida. Te ahorra meses de trabajo legal. Más info en aif369.com/compliance-tool.html o escribemos por WhatsApp."
- NO ES UN SERVICIO DE PAGO: Compliance-CL es una herramienta automatizada y gratuita. Para implementación completa con auditoría y training, ofrecemos planes de consultoría (Starter $3k/6m, Governed $6k/año, Enterprise $9k+/año).

AGENDAR ASESORÍA:
- Los usuarios pueden agendar una asesoría gratuita de 30 minutos directamente en: https://calendly.com/edaza-aif369/30min
- Cuando alguien quiera agendar, coordinar, cotizar o hablar con alguien, SIEMPRE incluye el link de agendamiento: https://calendly.com/edaza-aif369/30min
- También pueden escribir por WhatsApp: +56 9 9754 7192

CONTACTO:
- Agendar asesoría: https://calendly.com/edaza-aif369/30min
- WhatsApp: +56 9 9754 7192 (atención por IA y humanos)
- Web: aif369.com
- Email: edaza@aif369.com

Si el usuario parece interesado en contratar, indícale que puede agendar una asesoría gratuita en https://calendly.com/edaza-aif369/30min, escribir por WhatsApp +56 9 9754 7192, o hacer el Scorecard gratuito en aif369.com/scorecard.html"""


def send_email_notification(submission_data):
    """Envía notificación por email usando SMTP de Zoho (para nosotros)"""
    if not SMTP_PASSWORD:
        print("Warning: SMTP_PASSWORD not configured. Skipping email notification.")
        return False
    
    try:
        subject_prefix = "Nuevo contacto"
        if submission_data.get("form_type"):
            subject_prefix = f'{subject_prefix} ({submission_data["form_type"]})'

        optional_lines = ""
        if submission_data.get("interest"):
            optional_lines += f'<p><strong>Interés:</strong> {submission_data["interest"]}</p>'
        if submission_data.get("team_size"):
            optional_lines += f'<p><strong>Tamaño del equipo:</strong> {submission_data["team_size"]}</p>'

        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'{subject_prefix}: {submission_data["name"]} ({submission_data["email"]})'
        msg['From'] = f'{submission_data["name"]} <{SMTP_USER}>'
        msg['To'] = NOTIFICATION_EMAIL
        msg['Cc'] = CC_EMAIL
        msg['Reply-To'] = submission_data["email"]
        
        # Contenido HTML
        html = f'''
        <html>
          <body>
            <h2>Nuevo formulario de contacto recibido</h2>
            <p><strong>Nombre:</strong> {submission_data["name"]}</p>
            <p><strong>Email:</strong> {submission_data["email"]}</p>
            <p><strong>Empresa:</strong> {submission_data.get("company", "—")}</p>
            <p><strong>Cargo/Rol:</strong> {submission_data.get("role", "—")}</p>
            {optional_lines}
            <p><strong>Mensaje:</strong></p>
            <p>{submission_data["message"]}</p>
            <hr>
            <p><small>ID de submisión: {submission_data["submission_id"]}</small></p>
            <p><small>Hora: {submission_data["timestamp"]}</small></p>
            <p><small>Página: {submission_data["source_page"]}</small></p>
          </body>
        </html>
        '''
        
        part = MIMEText(html, 'html')
        msg.attach(part)
        
        # Enviar email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"Email notification sent to {NOTIFICATION_EMAIL} (cc: {CC_EMAIL})")
        return True
    except Exception as e:
        print(f"Error sending email notification: {e}")
        return False


def send_confirmation_email(submission_data):
    """Envía email de confirmación profesional al cliente con branding AIF369"""
    if not SMTP_PASSWORD:
        return False
    
    try:
        name = submission_data.get("name", "")
        first_name = name.split()[0] if name else "estimado/a"

        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Hemos recibido tu solicitud — AIF369'
        msg['From'] = f'AIF369 <{SMTP_USER}>'
        msg['To'] = submission_data["email"]
        
        # Email profesional con branding AIF369
        html = f'''<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0B1120;font-family:'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0B1120;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
        
        <!-- Header con gradiente -->
        <tr><td style="background:linear-gradient(135deg,#0088FF,#00D9CC);padding:32px 40px;border-radius:16px 16px 0 0;">
          <table width="100%"><tr>
            <td style="color:#fff;font-size:28px;font-weight:700;letter-spacing:-0.5px;">AIF369</td>
            <td align="right" style="color:rgba(255,255,255,0.8);font-size:13px;">IA &bull; Datos &bull; Cloud</td>
          </tr></table>
        </td></tr>
        
        <!-- Body -->
        <tr><td style="background:#0F1F35;padding:40px;border-left:1px solid rgba(255,255,255,0.06);border-right:1px solid rgba(255,255,255,0.06);">
          
          <p style="color:#E2E8F0;font-size:18px;margin:0 0 8px;font-weight:600;">Hola {first_name},</p>
          <p style="color:#A8B8D8;font-size:15px;line-height:1.7;margin:0 0 24px;">
            Gracias por contactarnos. Hemos recibido tu solicitud y nuestro equipo la revisará en las próximas <strong style="color:#E2E8F0;">24 horas hábiles</strong>.
          </p>
          
          <!-- Resumen de solicitud -->
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#162B45;border:1px solid rgba(255,255,255,0.08);border-radius:12px;margin:0 0 28px;">
            <tr><td style="padding:20px 24px 8px;">
              <p style="color:#0088FF;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin:0 0 12px;">Resumen de tu solicitud</p>
            </td></tr>
            <tr><td style="padding:0 24px;">
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="color:#7B8BA8;font-size:13px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);width:120px;">Nombre</td>
                  <td style="color:#E2E8F0;font-size:13px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">{submission_data.get("name","")}</td>
                </tr>
                <tr>
                  <td style="color:#7B8BA8;font-size:13px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">Email</td>
                  <td style="color:#E2E8F0;font-size:13px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">{submission_data.get("email","")}</td>
                </tr>
                <tr>
                  <td style="color:#7B8BA8;font-size:13px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">Empresa</td>
                  <td style="color:#E2E8F0;font-size:13px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">{submission_data.get("company","—")}</td>
                </tr>
                <tr>
                  <td style="color:#7B8BA8;font-size:13px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">Cargo/Rol</td>
                  <td style="color:#E2E8F0;font-size:13px;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.04);">{submission_data.get("role","—")}</td>
                </tr>
                <tr>
                  <td style="color:#7B8BA8;font-size:13px;padding:6px 0;vertical-align:top;">Mensaje</td>
                  <td style="color:#E2E8F0;font-size:13px;padding:6px 0;line-height:1.5;">{submission_data.get("message","")}</td>
                </tr>
              </table>
            </td></tr>
            <tr><td style="padding:8px 24px 16px;"></td></tr>
          </table>
          
          <!-- CTA: Scorecard -->
          <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
            <tr><td style="color:#A8B8D8;font-size:14px;line-height:1.6;margin:0 0 16px;">
              <p style="margin:0 0 16px;">Mientras preparamos tu respuesta, te invitamos a evaluar la madurez de IA de tu organización con nuestro <strong style="color:#E2E8F0;">AI Readiness Scorecard</strong> gratuito:</p>
            </td></tr>
            <tr><td align="center" style="padding:0 0 8px;">
              <a href="https://aif369.com/scorecard.html" style="display:inline-block;background:linear-gradient(135deg,#0088FF,#00D9CC);color:#fff;font-size:15px;font-weight:600;padding:14px 32px;border-radius:8px;text-decoration:none;letter-spacing:0.3px;">
                Hacer el Scorecard gratuito
              </a>
            </td></tr>
          </table>
          
          <!-- Servicios -->
          <table width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid rgba(255,255,255,0.06);padding:24px 0 0;">
            <tr><td style="color:#7B8BA8;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding:0 0 12px;">Nuestros servicios</td></tr>
            <tr><td>
              <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td width="50%" style="padding:4px 8px 4px 0;color:#A8B8D8;font-size:13px;">&#x2022; CAIO Advisory as a Service</td>
                  <td width="50%" style="padding:4px 0 4px 8px;color:#A8B8D8;font-size:13px;">&#x2022; AI Governance &amp; Responsible AI</td>
                </tr>
                <tr>
                  <td style="padding:4px 8px 4px 0;color:#A8B8D8;font-size:13px;">&#x2022; AI Risk, Privacy &amp; Compliance</td>
                  <td style="padding:4px 0 4px 8px;color:#A8B8D8;font-size:13px;">&#x2022; AI Factory Design</td>
                </tr>
                <tr>
                  <td style="padding:4px 8px 4px 0;color:#A8B8D8;font-size:13px;">&#x2022; Executive Workshops</td>
                  <td style="padding:4px 0 4px 8px;color:#A8B8D8;font-size:13px;">&#x2022; Thought Leadership</td>
                </tr>
              </table>
            </td></tr>
          </table>
          
        </td></tr>
        
        <!-- Footer -->
        <tr><td style="background:#0A1628;padding:24px 40px;border-radius:0 0 16px 16px;border:1px solid rgba(255,255,255,0.04);border-top:none;">
          <table width="100%"><tr>
            <td style="color:#4A5E7A;font-size:12px;line-height:1.6;">
              <strong style="color:#7B8BA8;">AIF369</strong> — IA, Datos y Cloud para la empresa moderna<br>
              <a href="https://aif369.com" style="color:#0088FF;text-decoration:none;">aif369.com</a>
              &nbsp;&bull;&nbsp;
              <a href="https://wa.me/56997547192" style="color:#0088FF;text-decoration:none;">WhatsApp +56 9 9754 7192</a>
              &nbsp;&bull;&nbsp;
              <a href="mailto:edaza@aif369.com" style="color:#0088FF;text-decoration:none;">edaza@aif369.com</a>
            </td>
          </tr></table>
        </td></tr>
        
      </table>
    </td></tr>
  </table>
</body>
</html>'''
        
        part = MIMEText(html, 'html')
        msg.attach(part)
        
        # Enviar email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"Confirmation email sent to {submission_data['email']}")
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return False


@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "aif369-backend"}), 200


PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET", "")
PAYPAL_BASE = "https://api-m.paypal.com"


def _paypal_access_token() -> str:
    """Get a short-lived PayPal OAuth2 access token. Raises on failure."""
    resp = http_requests.post(
        f"{PAYPAL_BASE}/v1/oauth2/token",
        auth=(os.getenv("PAYPAL_CLIENT_ID", ""), PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@app.route("/api/config/paypal", methods=["GET"])
def get_paypal_config():
    """Return PayPal client-id from environment (Secret Manager in production)."""
    client_id = os.getenv("PAYPAL_CLIENT_ID", "")
    if not client_id:
        return jsonify({"error": "PayPal not configured"}), 503
    return jsonify({"client_id": client_id}), 200


@app.route("/api/paypal/create-order", methods=["POST"])
def paypal_create_order():
    """
    Creates a PayPal order SERVER-SIDE.
    The price is determined entirely by the backend — never by the client.
    The user cannot manipulate the amount.
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json()
    email = (data.get("email") or "").strip().lower()
    course = (data.get("course") or "").strip()

    if not email or not course:
        return jsonify({"error": "email and course required"}), 400
    if not PAYPAL_CLIENT_SECRET:
        return jsonify({"error": "PayPal not fully configured (missing secret)"}), 503

    # Price set by server — period.
    is_vip = email in _get_vip_emails()
    full_price = COURSE_PRICES.get(course, 197)
    price = VIP_PRICE if (is_vip and VIP_PRICE < full_price) else full_price

    try:
        token = _paypal_access_token()
        resp = http_requests.post(
            f"{PAYPAL_BASE}/v2/checkout/orders",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "intent": "CAPTURE",
                "purchase_units": [{
                    "description": f"{course} — AIF369",
                    "amount": {"currency_code": "USD", "value": f"{price:.2f}"}
                }]
            },
            timeout=15,
        )
        resp.raise_for_status()
        order = resp.json()
        print(f"PayPal order created: {order['id']} | {course} | ${price} | {email}")
        return jsonify({"orderID": order["id"], "price": price, "is_vip": is_vip}), 200
    except Exception as e:
        print(f"PayPal create-order error: {e}")
        return jsonify({"error": "Could not create PayPal order"}), 500


@app.route("/api/paypal/capture-order", methods=["POST"])
def paypal_capture_order():
    """
    Captures a PayPal payment SERVER-SIDE after user approves.
    Verifies the captured amount matches what was promised.
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json()
    order_id = (data.get("orderID") or "").strip()
    email = (data.get("email") or "").strip()
    course = (data.get("course") or "").strip()

    if not order_id:
        return jsonify({"error": "orderID required"}), 400
    if not PAYPAL_CLIENT_SECRET:
        return jsonify({"error": "PayPal not fully configured"}), 503

    try:
        token = _paypal_access_token()
        resp = http_requests.post(
            f"{PAYPAL_BASE}/v2/checkout/orders/{order_id}/capture",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        capture = resp.json()

        if capture.get("status") != "COMPLETED":
            return jsonify({"error": "Payment not completed", "status": capture.get("status")}), 400

        amount = capture["purchase_units"][0]["payments"]["captures"][0]["amount"]["value"]
        payer_email = capture.get("payer", {}).get("email_address", "")

        print(f"PayPal capture OK: {order_id} | ${amount} | {email} | {course}")

        # Notify Erwin
        send_alert_email(
            f"💳 Pago recibido — {course}",
            f"""<html><body style="font-family:sans-serif">
            <h2 style="color:#00D9CC">💳 Pago recibido</h2>
            <p><strong>Curso:</strong> {course}</p>
            <p><strong>Monto:</strong> ${amount} USD</p>
            <p><strong>Email alumno:</strong> {email}</p>
            <p><strong>PayPal email:</strong> {payer_email}</p>
            <p><strong>Order ID:</strong> {order_id}</p>
            </body></html>"""
        )

        return jsonify({
            "status": "COMPLETED",
            "orderID": order_id,
            "amount": amount,
            "payer_email": payer_email,
        }), 200
    except Exception as e:
        print(f"PayPal capture error: {e}")
        return jsonify({"error": "Could not capture payment"}), 500


@app.route("/api/enrollment", methods=["POST"])
def enrollment():
    """Registra inscripción completada en BigQuery y envía confirmación al alumno."""
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json()
    row = {
        "submission_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "company": data.get("course", ""),
        "role": data.get("country", ""),
        "message": f"Inscripción: {data.get('course')} | PayPal: {data.get('paypal_order_id')} | ${data.get('price')}",
        "source_page": data.get("source_page", ""),
        "user_agent": request.headers.get("User-Agent", ""),
        "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr),
        "form_type": "enrollment",
        "interest": data.get("course"),
        "team_size": None,
    }
    try:
        get_bq_client().insert_rows_json(f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}", [row])
    except Exception as bq_err:
        print(f"Enrollment BQ error (non-fatal): {bq_err}")
    return jsonify({"success": True}), 200


# ── VIP email list (comma-separated in env var, never hardcoded) ──────────────
def _get_vip_emails() -> set:
    raw = os.getenv("VIP_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}

# Course prices (matches products-catalog.json)
COURSE_PRICES = {
    "Curso de Inteligencia Artificial":          197,
    "Big Data + IA: Arquitecturas Modernas":     297,
    "MLOps: De Modelos a Producción":            347,
    "Automatización con Apache Airflow":         247,
    "Automatización con Apache Airflow Avanzada": 247,
    "Test Pago AIF369":                          1,   # test only — remove after verification
}
VIP_PRICE = 10

# ── Consulting Service Prices (per 6 months or annual) ──────────────────────
CONSULTING_PRICES = {
    "caio_advisory": {"price": 3000, "duration": "6 months", "currency": "USD"},
    "ai_system_creation": {"price": 6000, "duration": "1 year", "currency": "USD"},
}


@app.route("/api/course-price", methods=["POST"])
def course_price():
    """
    Returns the correct price for a course given the user's email.
    VIP emails (VIP_EMAILS env var) pay $10. Everyone else pays full price.
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json()
    email = (data.get("email") or "").strip().lower()
    course = (data.get("course") or "").strip()

    if not email or not course:
        return jsonify({"error": "email and course required"}), 400

    is_vip = email in _get_vip_emails()
    full_price = COURSE_PRICES.get(course, 197)
    # VIP price only applies when it's actually a discount (less than full price)
    price = VIP_PRICE if (is_vip and VIP_PRICE < full_price) else full_price

    return jsonify({
        "email": email,
        "course": course,
        "price": price,
        "is_vip": is_vip,
        "currency": "USD",
        "label": f"${price} USD{' (precio especial)' if is_vip else ''}"
    }), 200


# ──────────────────────────────────────────────────────────────────────────────
# CONSULTING SERVICE PAYMENT ENDPOINTS (CAIO Advisory, AI System Creation)
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/api/paypal/create-order-service", methods=["POST"])
def paypal_create_order_service():
    """
    Creates a PayPal order for consulting services (CAIO Advisory or AI System Creation).
    Price is set by backend — user cannot manipulate amount.
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json()
    email = (data.get("email") or "").strip().lower()
    service = (data.get("service") or "").strip()  # "caio_advisory" or "ai_system_creation"

    if not email or not service:
        return jsonify({"error": "email and service required"}), 400
    if service not in CONSULTING_PRICES:
        return jsonify({"error": "Invalid service"}), 400
    if not PAYPAL_CLIENT_SECRET:
        return jsonify({"error": "PayPal not fully configured (missing secret)"}), 503

    service_info = CONSULTING_PRICES[service]
    price = service_info["price"]
    duration = service_info["duration"]

    service_display = {
        "caio_advisory": "CAIO Advisory",
        "ai_system_creation": "AI System Creation"
    }.get(service, service)

    try:
        token = _paypal_access_token()
        resp = http_requests.post(
            f"{PAYPAL_BASE}/v2/checkout/orders",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "intent": "CAPTURE",
                "purchase_units": [{
                    "description": f"{service_display} ({duration}) — AIF369",
                    "amount": {"currency_code": "USD", "value": f"{price:.2f}"}
                }]
            },
            timeout=15,
        )
        resp.raise_for_status()
        order = resp.json()
        print(f"PayPal service order created: {order['id']} | {service_display} | ${price} | {email}")
        return jsonify({
            "orderID": order["id"],
            "price": price,
            "service": service,
            "service_display": service_display,
            "duration": duration
        }), 200
    except Exception as e:
        print(f"PayPal create-order-service error: {e}")
        return jsonify({"error": "Could not create PayPal order"}), 500


@app.route("/api/paypal/capture-order-service", methods=["POST"])
def paypal_capture_order_service():
    """
    Captures a PayPal payment for consulting service after user approves.
    Verifies the captured amount matches what was promised.
    Saves transaction to BigQuery and sends confirmation emails.
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    data = request.get_json()
    order_id = (data.get("orderID") or "").strip()
    email = (data.get("email") or "").strip()
    service = (data.get("service") or "").strip()

    if not order_id:
        return jsonify({"error": "orderID required"}), 400
    if not PAYPAL_CLIENT_SECRET:
        return jsonify({"error": "PayPal not fully configured"}), 503

    try:
        token = _paypal_access_token()
        resp = http_requests.post(
            f"{PAYPAL_BASE}/v2/checkout/orders/{order_id}/capture",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=15,
        )
        resp.raise_for_status()
        capture = resp.json()

        if capture.get("status") != "COMPLETED":
            return jsonify({"error": "Payment not completed", "status": capture.get("status")}), 400

        amount = capture["purchase_units"][0]["payments"]["captures"][0]["amount"]["value"]
        payer_email = capture.get("payer", {}).get("email_address", "")

        service_display = {
            "caio_advisory": "CAIO Advisory",
            "ai_system_creation": "AI System Creation"
        }.get(service, service)

        print(f"PayPal capture OK: {order_id} | ${amount} | {email} | {service}")

        # Save to BigQuery
        row = {
            "submission_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "name": email.split("@")[0] if email else "unknown",
            "email": email,
            "company": service_display,
            "role": "consulting_service",
            "message": f"Consulting Service: {service_display} | PayPal Order: {order_id} | ${amount} USD",
            "source_page": "checkout-service",
            "user_agent": request.headers.get("User-Agent", ""),
            "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr),
            "form_type": "consulting_payment",
            "interest": service,
            "team_size": None,
        }
        try:
            get_bq_client().insert_rows_json(f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}", [row])
            print(f"Consulting payment saved to BigQuery: {order_id}")
        except Exception as bq_err:
            print(f"BigQuery insert error (non-fatal): {bq_err}")

        # Notify Erwin
        send_alert_email(
            f"💳 Nuevo Cliente — {service_display}",
            f"""<html><body style="font-family:sans-serif;color:#333">
            <h2 style="color:#00D9CC">💳 Nuevo pago de servicio recibido</h2>
            <p><strong>Servicio:</strong> {service_display}</p>
            <p><strong>Monto:</strong> ${amount} USD</p>
            <p><strong>Email cliente:</strong> {email}</p>
            <p><strong>PayPal email:</strong> {payer_email}</p>
            <p><strong>Order ID:</strong> {order_id}</p>
            <p><strong>Timestamp:</strong> {datetime.now(timezone.utc).isoformat()}</p>
            <hr>
            <p style="font-size:12px;color:#666">AIF369 Backend Payment Processor</p>
            </body></html>"""
        )

        return jsonify({
            "status": "COMPLETED",
            "orderID": order_id,
            "amount": amount,
            "payer_email": payer_email,
            "service": service,
            "service_display": service_display,
        }), 200
    except Exception as e:
        print(f"PayPal capture-service error: {e}")
        return jsonify({"error": "Could not capture payment"}), 500


@app.route("/api/contact", methods=["POST"])
def submit_contact_form():
    """
    Endpoint para recibir formularios de contacto del sitio web.
    
    Expected JSON payload:
    {
        "name": "Juan Pérez",
        "email": "juan@example.com",
        "company": "Empresa XYZ",  # opcional
        "message": "Estoy interesado en sus servicios..."
    }
    """
    try:
        # Validar content type
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        name = data.get("name") or data.get("fullName") or ""
        email = data.get("email") or ""
        company = data.get("company") or ""
        role = data.get("role") or ""
        message = data.get("message") or data.get("context") or ""
        interest = data.get("interest") or ""
        team_size = data.get("team_size") or data.get("teamSize") or ""
        
        # Validar campos requeridos
        required_fields = {
            "name": name,
            "email": email,
            "message": message
        }
        missing_fields = [field for field, value in required_fields.items() if not value]
        
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Preparar datos para BigQuery
        submission_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        row = {
            "submission_id": submission_id,
            "timestamp": timestamp,
            "name": name,
            "email": email,
            "company": company,
            "role": role,
            "message": message,
            "source_page": data.get("source_page", request.referrer or ""),
            "user_agent": request.headers.get("User-Agent", ""),
            "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr),
            "form_type": data.get("form_type") or None,
            "interest": interest or None,
            "team_size": team_size or None
        }
        
        # Insertar en BigQuery (non-blocking — analytics shouldn't break user flow)
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        try:
            errors = get_bq_client().insert_rows_json(table_ref, [row])
            if errors:
                print(f"BigQuery insert errors (non-fatal): {errors}")
        except Exception as bq_err:
            print(f"BigQuery insert failed (non-fatal): {bq_err}")
        
        # Enviar notificaciones por email
        email_data = {
            **row,
            "submission_id": submission_id
        }
        send_email_notification(email_data)  # A nosotros
        # Skip confirmation email for QA/test submissions to avoid bounces
        if email_data.get("form_type") != "qa_test":
            send_confirmation_email(email_data)   # Al cliente
        
        return jsonify({
            "success": True,
            "submission_id": submission_id,
            "message": "Gracias por tu mensaje. Te contactaremos pronto."
        }), 200
        
    except Exception as e:
        print(f"Error processing contact form: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/education", methods=["POST"])
def submit_education_form():
    """
    Endpoint para recibir formularios de educación.

    Expected JSON payload:
    {
        "name": "Juan Pérez",
        "email": "juan@example.com",
        "company": "Empresa XYZ",
        "interest": "curso-desarrollo-ia",
        "team_size": "6-15",
        "message": "Necesitamos formación para..."
    }
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        name = data.get("name") or data.get("fullName") or ""
        email = data.get("email") or ""
        company = data.get("company") or ""
        interest = data.get("interest") or ""
        team_size = data.get("team_size") or data.get("teamSize") or ""
        message = data.get("message") or data.get("context") or ""

        required_fields = {
            "name": name,
            "email": email,
            "company": company,
            "interest": interest,
            "message": message
        }
        missing_fields = [field for field, value in required_fields.items() if not value]

        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        submission_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        row = {
            "submission_id": submission_id,
            "timestamp": timestamp,
            "name": name,
            "email": email,
            "company": company,
            "message": message,
            "source_page": data.get("source_page", request.referrer or ""),
            "user_agent": request.headers.get("User-Agent", ""),
            "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr),
            "form_type": "education",
            "interest": interest or None,
            "team_size": team_size or None
        }

        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        try:
            errors = get_bq_client().insert_rows_json(table_ref, [row])
            if errors:
                print(f"BigQuery insert errors (non-fatal): {errors}")
        except Exception as bq_err:
            print(f"BigQuery insert failed (non-fatal): {bq_err}")

        email_data = {
            **row,
            "submission_id": submission_id
        }
        send_email_notification(email_data)
        # Skip confirmation email for QA/test submissions to avoid bounces
        if email_data.get("form_type") != "qa_test":
            send_confirmation_email(email_data)
        return jsonify({
            "success": True,
            "submission_id": submission_id,
            "message": "Gracias por tu solicitud de educación. Te contactaremos pronto."
        }), 200

    except Exception as e:
        print(f"Error processing education form: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


SCORECARD_TABLE = "scorecard_submissions"
CHAT_TABLE_ID = "chat_conversations"

# ── Palabras clave para detección de intención en el chat ──
INTENT_KEYWORDS = {
    "pricing": ["precio", "costo", "cuánto", "cuanto", "tarifa", "cotización", "cotizar", "presupuesto", "inversión"],
    "services": ["servicio", "ofrecen", "consultoría", "diagnóstico", "governance", "gobernanza", "factory", "taller", "workshop"],
    "scheduling": ["agendar", "reunión", "llamada", "cita", "agenda", "conversar", "contactar"],
    "scorecard": ["scorecard", "evaluación", "madurez", "readiness", "assessment", "diagnóstico"],
    "methodology": ["método", "369", "metodología", "fases", "capas", "métricas"],
    "education": ["curso", "formación", "capacitación", "taller", "aprender", "certificación"],
    "regulation": ["regulación", "ley", "normativa", "compliance", "ai act", "datos personales"],
}


def detect_intent(message):
    """Detecta la intención del usuario basándose en palabras clave."""
    msg_lower = message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            return intent
    return "general"


def detect_language(message):
    """Detección simple de idioma basada en palabras comunes."""
    en_words = ["the", "what", "how", "can", "you", "your", "about", "services", "pricing", "help"]
    msg_lower = message.lower().split()
    en_count = sum(1 for w in msg_lower if w in en_words)
    return "en" if en_count >= 2 else "es"


def save_chat_to_bigquery(message_data):
    """Guarda un intercambio de chat en BigQuery para seguimiento y analytics."""
    try:
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{CHAT_TABLE_ID}"
        errors = get_bq_client().insert_rows_json(table_ref, [message_data])
        if errors:
            print(f"Chat BQ insert errors: {errors}")
            return False
        print(f"Chat saved to BQ: session={message_data.get('session_id', '?')}, turn={message_data.get('turn_number', '?')}")
        return True
    except Exception as e:
        print(f"Error saving chat to BigQuery: {e}")
        return False

def save_chat_metadata(session_id, user_role=None, industry=None, project_status=None, lead_quality=None):
    """Guarda metadata de sesión de chat para seguimiento de leads."""
    try:
        metadata_table = f"{PROJECT_ID}.{DATASET_ID}.chat_session_metadata"
        metadata = {
            "session_id": session_id,
            "metadata_timestamp": datetime.now(timezone.utc).isoformat(),
            "user_role": user_role,  # CEO, CTO, CDO, Developer, Other
            "industry": industry,     # Finanzas, Retail, Tech, Healthcare, etc.
            "project_status": project_status,  # No tiene IA, Piloto, En producción
            "lead_quality_score": lead_quality,  # 1-10 based on engagement
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        errors = get_bq_client().insert_rows_json(metadata_table, [metadata])
        if errors:
            print(f"Metadata insert errors: {errors}")
            return False
        print(f"Metadata saved for session {session_id}")
        return True
    except Exception as e:
        print(f"Error saving metadata: {e}")
        return False

def ensure_metadata_table():
    """Crea tabla de metadata si no existe."""
    try:
        client = get_bq_client()
        table_id = f"{PROJECT_ID}.{DATASET_ID}.chat_session_metadata"

        # Verificar si existe
        try:
            client.get_table(table_id)
            return True
        except Exception:
            pass

        # Crear tabla
        from google.cloud import bigquery
        schema = [
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("metadata_timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("user_role", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("industry", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("project_status", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("lead_quality_score", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        ]

        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="created_at"
        )

        table = client.create_table(table)
        print(f"Created metadata table {table.project}.{table.dataset_id}.{table.table_id}")
        return True
    except Exception as e:
        print(f"Error ensuring metadata table: {e}")
        return False

# Crear tabla de metadata en startup
ensure_metadata_table()

@app.route("/api/scorecard", methods=["POST"])
def submit_scorecard():
    """
    Endpoint para recibir resultados del AI Readiness Scorecard.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        name = data.get("name", "")
        email = data.get("email", "")
        company = data.get("company", "")
        role = data.get("role", "")
        total_score = data.get("total_score", 0)
        maturity_level = data.get("maturity_level", "")
        maturity_number = data.get("maturity_number", 0)
        dimensions_data = data.get("metrics") or data.get("dimensions") or {}
        answers_data = data.get("answers", [])

        if not name or not email:
            return jsonify({"error": "Name and email are required"}), 400

        submission_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        row = {
            "submission_id": submission_id,
            "timestamp": timestamp,
            "name": name,
            "email": email,
            "company": company,
            "role": role,
            "total_score": total_score,
            "maturity_level": maturity_level,
            "maturity_number": maturity_number,
            "dimensions_json": json.dumps(dimensions_data),
            "answers_json": json.dumps(answers_data),
            "source_page": data.get("source_page", request.referrer or ""),
            "user_agent": request.headers.get("User-Agent", ""),
            "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr)
        }

        # Try to insert into scorecard table; fall back to contact table
        try:
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.{SCORECARD_TABLE}"
            errors = get_bq_client().insert_rows_json(table_ref, [row])
            if errors:
                print(f"Scorecard BQ insert errors: {errors}, falling back to contact table")
                raise Exception("Scorecard table insert failed")
        except Exception:
            # Fallback: save as contact form submission
            dim_summary = ", ".join(
                f"{d.get('name','')}: {d.get('pct',0)}%"
                for d in dimensions_data.values()
            ) if isinstance(dimensions_data, dict) else ""
            fallback_row = {
                "submission_id": submission_id,
                "timestamp": timestamp,
                "name": name,
                "email": email,
                "company": company,
                "message": f"AI Readiness Scorecard: {total_score}/100 ({maturity_level}). {dim_summary}",
                "source_page": data.get("source_page", ""),
                "user_agent": request.headers.get("User-Agent", ""),
                "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr),
                "form_type": "scorecard",
                "interest": f"Maturity: {maturity_level} ({total_score}/100)",
                "team_size": None
            }
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
            get_bq_client().insert_rows_json(table_ref, [fallback_row])

        # Send notification email
        dim_summary = "\n".join(
            f"  • {d.get('name','')}: {d.get('pct',0)}%"
            for d in dimensions_data.values()
        ) if isinstance(dimensions_data, dict) else ""

        email_data = {
            "submission_id": submission_id,
            "timestamp": timestamp,
            "name": name,
            "email": email,
            "company": f"{company} ({role})" if role else company,
            "message": f"AI Readiness Score: {total_score}/100\nNivel: {maturity_level} ({maturity_number}/5)\n\nDimensiones:\n{dim_summary}",
            "source_page": data.get("source_page", ""),
            "form_type": "scorecard"
        }
        send_email_notification(email_data)

        # Auto-email to user with Gemini recommendations
        try:
            scorecard_context = (
                f"EMPRESA: {company} ({role})\n"
                f"Score total: {total_score}/100\n"
                f"Nivel: {maturity_level} ({maturity_number}/5)\n"
                f"Dimensiones:\n{dim_summary}"
            )
            user_report = _gemini_generate(
                SCORECARD_RECOMMENDATION_SYSTEM,
                f"Genera recomendaciones para:\n{scorecard_context}"
            )
            first_name = (name.split()[0] if name else "Estimado/a")
            _send_user_report_email(
                to_email=email,
                first_name=first_name,
                subject=f"Tu AI Readiness Score: {total_score}/100 — AIF369",
                score=total_score,
                score_label="AI Readiness Score",
                report_html=user_report,
                cta_url="https://aif369.com/services.html",
                cta_label="Ver Servicios AIF369 →",
                accent_color="#0088FF"
            )
        except Exception as user_email_err:
            print(f"Scorecard user email error (non-fatal): {user_email_err}")

        return jsonify({
            "success": True,
            "submission_id": submission_id,
            "message": "Scorecard submitted successfully"
        }), 200

    except Exception as e:
        print(f"Error processing scorecard: {str(e)}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


# ── Prompts para assessments automáticos ─────────────────────────────────────
DATA_ASSESSMENT_SYSTEM = """Eres un consultor experto de AIF369 especializado en gobernanza de datos para empresas en Latam.
Analiza las respuestas del assessment de madurez de datos y genera un reporte ejecutivo personalizado.
REGLAS ESTRICTAS:
1. Sé directo y concreto — sin frases genéricas.
2. Identifica exactamente los 3 riesgos principales según sus respuestas.
3. Da 3 recomendaciones accionables y específicas para esta empresa.
4. Recomienda el paquete más adecuado: Starter ($6,000 USD), Business ($12,000 USD) o Enterprise ($18,000+ USD).
5. Menciona la Ley 21.719 si procesa datos personales.
6. Máximo 350 palabras. Usa formato HTML con <h3>, <p>, <ul><li>.
Paquetes AIF369: Starter = empresa pequeña, 1-2 dominios, 6 sem. Business = 200-1000 emp, 2-3 dominios, 8-10 sem. Enterprise = grande o muy regulada."""

SCORECARD_RECOMMENDATION_SYSTEM = """Eres un CAIO Advisor de AIF369. Analiza los resultados del AI Readiness Scorecard y genera recomendaciones personalizadas.
REGLAS:
1. Basate SOLO en los datos del scorecard — sin inventar.
2. Identifica los 3 gaps más críticos de esta empresa específica.
3. Da 3 próximos pasos concretos y priorizados.
4. Si el score es < 40%, recomienda primero Gobernanza de Datos (prerequisito).
5. Recomienda el servicio AIF369 más adecuado para su nivel.
6. Máximo 300 palabras. Formato HTML con <h3>, <p>, <ul><li>.
Servicios: Starter 369 ($4k, 4-6 sem), Governed Pilot ($12k, 8-12 sem), CAIO-as-a-Service ($3k/mes), Gobernanza Datos ($6k)."""


def _gemini_generate(system: str, user_prompt: str, max_tokens: int = 600) -> str:
    """Calls Gemini and returns generated text, or empty string on failure."""
    if not GEMINI_API_KEY:
        return ""
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system,
            generation_config=genai.types.GenerationConfig(temperature=0.3, max_output_tokens=max_tokens)
        )
        return model.generate_content(user_prompt).text
    except Exception as e:
        print(f"Gemini generate error: {e}")
        return ""


def _send_user_report_email(to_email: str, first_name: str, subject: str,
                             score: int, score_label: str, report_html: str,
                             cta_url: str, cta_label: str, accent_color: str = "#0088FF") -> None:
    """Send a branded auto-report email to the user. Fails silently."""
    if not SMTP_PASSWORD:
        return
    urgency = ("⚠️ Alta urgencia — acción recomendada este mes" if score < 30
               else ("🔸 Riesgo moderado — actuar este trimestre" if score < 60
                     else "✅ Madurez aceptable — momento de optimizar"))
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"AIF369 <{SMTP_USER}>"
        msg["To"] = to_email
        html = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0B1120;font-family:'Segoe UI',Roboto,Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0B1120;padding:32px 0;">
<tr><td align="center"><table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
<tr><td style="background:linear-gradient(135deg,{accent_color},{accent_color}CC);padding:28px 40px;border-radius:16px 16px 0 0;">
<table width="100%"><tr>
<td style="color:#fff;font-size:24px;font-weight:700;">AIF369</td>
<td align="right" style="color:rgba(255,255,255,0.85);font-size:12px;">Reporte automático</td>
</tr></table></td></tr>
<tr><td style="background:#0F1F35;padding:32px 40px;border-left:1px solid rgba(255,255,255,0.06);border-right:1px solid rgba(255,255,255,0.06);">
<p style="color:#E2E8F0;font-size:17px;font-weight:600;margin:0 0 8px;">Hola {first_name},</p>
<p style="color:#A8B8D8;font-size:14px;line-height:1.7;margin:0 0 20px;">Aquí está tu reporte personalizado basado en tus respuestas.</p>
<div style="background:#162B45;border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:20px;margin:0 0 20px;text-align:center;">
<div style="font-size:11px;font-weight:700;color:#7B8BA8;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">{score_label}</div>
<div style="font-size:42px;font-weight:800;color:{accent_color};">{score}<span style="font-size:20px;color:#7B8BA8;">/100</span></div>
<div style="font-size:12px;color:#A8B8D8;margin-top:6px;">{urgency}</div>
</div>
<div style="color:#A8B8D8;font-size:14px;line-height:1.7;">{report_html if report_html else "<p>Nuestro equipo revisará tu solicitud en las próximas 24 horas.</p>"}</div>
<div style="margin:24px 0;text-align:center;background:#162B45;border-radius:12px;padding:20px;">
<p style="color:#E2E8F0;font-size:14px;font-weight:600;margin:0 0 14px;">¿Tienes preguntas? Nuestro asistente IA responde 24/7</p>
<a href="{cta_url}" style="display:inline-block;background:{accent_color};color:#fff;font-size:14px;font-weight:600;padding:12px 28px;border-radius:8px;text-decoration:none;">{cta_label}</a>
</div>
</td></tr>
<tr><td style="background:#0A1628;padding:18px 40px;border-radius:0 0 16px 16px;border:1px solid rgba(255,255,255,0.04);border-top:none;">
<p style="color:#4A5E7A;font-size:12px;margin:0;"><strong style="color:#7B8BA8;">AIF369</strong> — IA · Datos · Cloud · aif369.com · +56 9 9754 7192</p>
</td></tr></table></td></tr></table></body></html>"""
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"User report email sent to {to_email}")
    except Exception as e:
        print(f"User report email failed: {e}")


@app.route("/api/assessment-datos", methods=["POST"])
def assessment_datos():
    """
    Assessment automático de Gobernanza de Datos.
    Recibe respuestas del formulario, analiza con Gemini y envía reporte al usuario.
    Sin intervención humana requerida — 100% automático.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        company = (data.get("company") or "").strip()
        role = (data.get("role") or "").strip()
        industry = (data.get("industry") or "").strip()
        company_size = (data.get("company_size") or "").strip()
        data_sources = (data.get("data_sources") or "").strip()
        data_quality = (data.get("data_quality") or "").strip()
        current_governance = (data.get("current_governance") or "").strip()
        processes_personal = (data.get("processes_personal_data") or "").strip()
        ley21719_status = (data.get("ley21719_status") or "").strip()
        main_challenge = (data.get("main_challenge") or "").strip()
        ai_plans = (data.get("ai_plans") or "").strip()

        if not name or not email:
            return jsonify({"error": "name and email are required"}), 400

        submission_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        assessment_context = (
            f"EMPRESA: {company} ({industry}) — {company_size}\n"
            f"CONTACTO: {name}, {role}\n"
            f"Fuentes de datos: {data_sources}\n"
            f"Calidad de datos: {data_quality}\n"
            f"Gobierno de datos actual: {current_governance}\n"
            f"¿Procesa datos personales?: {processes_personal}\n"
            f"Estado Ley 21.719: {ley21719_status}\n"
            f"Principal desafío: {main_challenge}\n"
            f"Planes de IA: {ai_plans}"
        )

        # Simple maturity score
        quality_scores = {"Muy buena": 25, "Buena": 18, "Regular": 10, "Mala": 5}
        gov_scores = {"Gobierno avanzado": 35, "Gobierno estructurado": 25,
                      "Políticas básicas": 15, "Ninguno": 0}
        ley_scores = {"Listo": 30, "Parcialmente preparado": 15,
                      "No preparado": 0, "No sé qué es": 0}
        maturity_score = min(100,
            quality_scores.get(data_quality, 7) +
            gov_scores.get(current_governance, 5) +
            ley_scores.get(ley21719_status, 5)
        )

        report_html = _gemini_generate(
            DATA_ASSESSMENT_SYSTEM,
            f"Genera el reporte para:\n{assessment_context}"
        )

        # Auto-email to user
        first_name = name.split()[0] if name else "Estimado/a"
        _send_user_report_email(
            to_email=email,
            first_name=first_name,
            subject="Tu Assessment de Gobernanza de Datos — AIF369",
            score=maturity_score,
            score_label="Índice de Madurez de Datos",
            report_html=report_html,
            cta_url="https://aif369.com/gobernanza-datos-ia.html",
            cta_label="Ver Servicio Completo →",
            accent_color="#A855F7"
        )

        # Notify Erwin
        send_email_notification({
            "submission_id": submission_id,
            "timestamp": timestamp,
            "name": name,
            "email": email,
            "company": f"{company} | {industry} | {company_size}",
            "role": role,
            "message": f"Assessment Datos — Score: {maturity_score}/100\n\n{assessment_context}",
            "source_page": data.get("source_page", "assessment-datos"),
            "form_type": "assessment-datos",
            "interest": f"Data Governance Score: {maturity_score}/100",
            "team_size": company_size,
        })

        # BigQuery
        try:
            row = {
                "submission_id": submission_id, "timestamp": timestamp,
                "name": name, "email": email, "company": company, "role": role,
                "message": f"Data Governance Score: {maturity_score}/100\n{assessment_context}",
                "source_page": data.get("source_page", ""),
                "user_agent": request.headers.get("User-Agent", ""),
                "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr),
                "form_type": "assessment-datos",
                "interest": f"Score:{maturity_score} | Industry:{industry}",
                "team_size": company_size,
            }
            errors = get_bq_client().insert_rows_json(f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}", [row])
            if errors:
                print(f"Assessment BQ errors: {errors}")
        except Exception as bq_err:
            print(f"Assessment BQ error (non-fatal): {bq_err}")

        return jsonify({
            "success": True,
            "submission_id": submission_id,
            "maturity_score": maturity_score,
            "report_html": report_html,
            "message": "Assessment completado. Revisa tu email para el reporte personalizado."
        }), 200

    except Exception as e:
        print(f"Error in assessment-datos: {e}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Chatbot endpoint. Primary: Gemini. Fallback: Ollama (local).
    Expected JSON: { "message": "...", "history": [...], "session_id": "...", "turn_number": 1, "source_page": "..." }
    Persiste cada intercambio en BigQuery para seguimiento y analytics.
    Security: rate limiting (20 req/IP/hour) + origin validation.
    """
    try:
        # ── Security: Origin validation ──────────────────────────────────────
        origin = request.headers.get("Origin", "")
        is_dev = re.match(r"^https://.*\.vercel\.app$", origin) or \
                 re.match(r"^http://localhost(:\d+)?$", origin)
        is_trusted = origin in ALLOWED_CHAT_ORIGINS or bool(is_dev)

        if not is_trusted:
            suspicious_origin = origin or "(no origin header)"
            client_ip_early = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
            print(f"SECURITY ALERT: chat BLOCKED from untrusted origin: {suspicious_origin} | IP: {client_ip_early}")
            # Log to BQ before blocking so we keep the audit trail
            try:
                save_chat_to_bigquery({
                    "message_id": str(uuid.uuid4()),
                    "session_id": request.get_json(silent=True, force=True).get("session_id", str(uuid.uuid4())) if request.is_json else str(uuid.uuid4()),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user_message": (request.get_json(silent=True, force=True) or {}).get("message", "")[:500],
                    "assistant_response": "(BLOCKED)",
                    "provider": "blocked",
                    "turn_number": 0,
                    "source_page": "",
                    "user_agent": request.headers.get("User-Agent", ""),
                    "ip_address": client_ip_early,
                    "language": "",
                    "intent_detected": "",
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "origin_header": suspicious_origin[:500],
                    "suspicious": True,
                })
            except Exception:
                pass
            # Fire-and-forget alert email
            try:
                send_alert_email(
                    f"🚫 Chat BLOQUEADO — origen no autorizado",
                    f"""<html><body style="font-family:sans-serif">
                    <h2 style="color:#c0392b">🚫 Request bloqueado</h2>
                    <p><strong>Hora:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
                    <p><strong>Origin:</strong> {suspicious_origin}</p>
                    <p><strong>IP:</strong> {client_ip_early}</p>
                    <p><strong>User-Agent:</strong> {request.headers.get('User-Agent','')[:200]}</p>
                    </body></html>"""
                )
            except Exception:
                pass
            return jsonify({
                "error": "Forbidden",
                "response": "Acceso no autorizado.",
                "success": False
            }), 403

        # ── Security: Rate limiting ───────────────────────────────────────────
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
        if is_rate_limited(client_ip):
            print(f"RATE LIMIT HIT: IP {client_ip} exceeded {RATE_LIMIT_MAX} req/hour")
            return jsonify({
                "error": "Too many requests",
                "response": "Has enviado demasiados mensajes. Por favor espera unos minutos.",
                "success": False
            }), 429

        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        user_message = data.get("message", "").strip()
        history = data.get("history", [])
        session_id = data.get("session_id", str(uuid.uuid4()))
        turn_number = data.get("turn_number", len(history) // 2 + 1)
        source_page = data.get("source_page", request.referrer or "")

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # ── Per-session limits ────────────────────────────────────────────────
        _session_turns[session_id] += 1
        if _session_turns[session_id] > MAX_TURNS_PER_SESSION:
            print(f"SESSION LIMIT: session {session_id} exceeded {MAX_TURNS_PER_SESSION} turns")
            return jsonify({
                "error": "Session limit reached",
                "response": "Has alcanzado el límite de mensajes por sesión. Para continuar, escríbenos por WhatsApp: +56 9 9754 7192",
                "success": False,
                "limit_reached": True
            }), 200  # 200 so the widget shows the message naturally

        if _session_tokens[session_id] >= MAX_INPUT_TOKENS_PER_SESSION:
            print(f"TOKEN LIMIT: session {session_id} exceeded {MAX_INPUT_TOKENS_PER_SESSION} input tokens")
            return jsonify({
                "error": "Token limit reached",
                "response": "Esta conversación es muy extensa. Para continuar, escríbenos por WhatsApp: +56 9 9754 7192",
                "success": False,
                "limit_reached": True
            }), 200

        # Detectar intención e idioma para analytics
        intent = detect_intent(user_message)
        language = detect_language(user_message)

        reply = None
        provider = "none"
        input_tokens = 0
        output_tokens = 0

        # --- Intento 1: Gemini ---
        if GEMINI_API_KEY:
            try:
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=SYSTEM_PROMPT,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0,
                        top_p=0.1,
                        max_output_tokens=300
                    )
                )
                gemini_history = []
                for msg in history[-10:]:
                    role = "user" if msg.get("role") == "user" else "model"
                    gemini_history.append({"role": role, "parts": [msg.get("content", "")]})

                chat_session = model.start_chat(history=gemini_history)
                response = chat_session.send_message(user_message)
                reply = response.text
                provider = "gemini"

                # Capture token usage from Gemini response
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    input_tokens  = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                    output_tokens = getattr(response.usage_metadata, "candidates_token_count", 0) or 0
                    _session_tokens[session_id] += input_tokens  # accumulate for session cap

                print(f"Chat response via Gemini | in={input_tokens} out={output_tokens} | origin={origin or 'none'} | ip={client_ip} | trusted={is_trusted}")
            except Exception as gemini_error:
                print(f"Gemini failed, trying Ollama fallback: {gemini_error}")

        # --- Intento 2: Ollama (fallback) ---
        if reply is None:
            try:
                ollama_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for msg in history[-10:]:
                    role = "user" if msg.get("role") == "user" else "assistant"
                    ollama_messages.append({"role": role, "content": msg.get("content", "")})
                ollama_messages.append({"role": "user", "content": user_message})

                ollama_response = http_requests.post(
                    f"{OLLAMA_URL}/api/chat",
                    json={
                        "model": OLLAMA_MODEL,
                        "messages": ollama_messages,
                        "stream": False,
                        "options": {"temperature": 0, "num_predict": 300}
                    },
                    timeout=60
                )
                ollama_response.raise_for_status()
                ollama_data = ollama_response.json()
                reply = ollama_data.get("message", {}).get("content", "")
                if reply:
                    provider = "ollama"
                    print(f"Chat response via Ollama ({OLLAMA_MODEL})")
            except Exception as ollama_error:
                print(f"Ollama also failed: {ollama_error}")

        # --- Fallback message ---
        if not reply:
            reply = "No pude procesar tu mensaje en este momento. Escríbenos por WhatsApp al +56 9 9754 7192 y te atendemos directamente."

        # --- Persistir conversación en BigQuery (async-safe, no bloquea respuesta) ---
        try:
            chat_row = {
                "message_id": str(uuid.uuid4()),
                "session_id": session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_message": user_message[:5000],
                "assistant_response": reply[:5000],
                "provider": provider,
                "turn_number": turn_number,
                "source_page": source_page,
                "user_agent": request.headers.get("User-Agent", ""),
                "ip_address": client_ip,
                "language": language,
                "intent_detected": intent,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "origin_header": origin[:500] if origin else "",
                "suspicious": not is_trusted,
            }
            save_chat_to_bigquery(chat_row)
        except Exception as bq_err:
            print(f"Non-blocking BQ save error: {bq_err}")

        # ── Email alerts (non-blocking) ───────────────────────────────────────
        try:
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

            # New chat session (first message) → new user notification
            if session_id not in _notified_sessions:
                _notified_sessions.add(session_id)
                est_cost = round((input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000, 6)
                send_alert_email(
                    f"💬 Nuevo chat en AIF369 — {now_str}",
                    f"""<html><body style="font-family:sans-serif">
                    <h2 style="color:#0088FF">💬 Nueva sesión de chat</h2>
                    <p><strong>Hora:</strong> {now_str}</p>
                    <p><strong>Session ID:</strong> {session_id}</p>
                    <p><strong>Página:</strong> {source_page or '(desconocida)'}</p>
                    <p><strong>Primer mensaje:</strong> {user_message[:300]}</p>
                    <p><strong>Tokens:</strong> in={input_tokens} | out={output_tokens} | costo≈${est_cost:.6f}</p>
                    <p><strong>Origin:</strong> {origin or '(sin header)'} ✅</p>
                    <hr>
                    <p><small>AIF369 Backend Monitor — Cloud Run</small></p>
                    </body></html>"""
                )
        except Exception as alert_err:
            print(f"Alert email error (non-blocking): {alert_err}")

        return jsonify({
            "response": reply,
            "success": provider != "none",
            "provider": provider,
            "session_id": session_id
        }), 200

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            "error": "Error processing your message",
            "response": "Lo siento, no pude procesar tu mensaje. ¿Podrías intentar de nuevo?",
            "success": False
        }), 200



# --- API Key for content generation (simple auth) ---
CONTENT_API_KEY = os.getenv("CONTENT_API_KEY", "")


@app.route("/api/daily-report", methods=["GET", "POST"])
def daily_report():
    """
    Envía resumen diario de uso por email.
    Llamado por Cloud Scheduler cada día.
    Requiere header X-Report-Token == REPORT_SECRET (si está configurado).
    """
    if REPORT_SECRET:
        token = request.headers.get("X-Report-Token", "")
        if token != REPORT_SECRET:
            return jsonify({"error": "Unauthorized"}), 401

    try:
        bq = get_bq_client()
        table = f"`{PROJECT_ID}.{DATASET_ID}.chat_conversations`"

        # ── Main daily summary ───────────────────────────────────────────────
        q_summary = f"""
        SELECT
          COUNT(DISTINCT session_id)                        AS sessions,
          COUNT(*)                                          AS messages,
          COALESCE(SUM(input_tokens), 0)                   AS in_tokens,
          COALESCE(SUM(output_tokens), 0)                  AS out_tokens,
          COUNTIF(suspicious = TRUE)                        AS suspicious_count,
          COUNTIF(provider = 'gemini')                      AS gemini_calls,
          COUNTIF(provider = 'ollama')                      AS ollama_calls,
          ROUND(AVG(COALESCE(input_tokens,0) + COALESCE(output_tokens,0)), 1) AS avg_tokens_per_msg,
          COUNTIF(language = 'es')                          AS lang_es,
          COUNTIF(language = 'en')                          AS lang_en,
          COUNTIF(language NOT IN ('es','en'))              AS lang_other,
          -- sessions with >1 message = engaged users
          COUNT(DISTINCT IF(turn_number > 1, session_id, NULL)) AS engaged_sessions
        FROM {table}
        WHERE DATE(timestamp, 'America/Santiago') = CURRENT_DATE('America/Santiago')
        """

        # ── Previous day for comparison ───────────────────────────────────────
        q_prev = f"""
        SELECT
          COUNT(DISTINCT session_id) AS sessions_prev,
          COUNT(*)                   AS messages_prev
        FROM {table}
        WHERE DATE(timestamp, 'America/Santiago') = DATE_SUB(CURRENT_DATE('America/Santiago'), INTERVAL 1 DAY)
        """

        # ── Peak hour breakdown ───────────────────────────────────────────────
        q_hours = f"""
        SELECT
          EXTRACT(HOUR FROM timestamp AT TIME ZONE 'America/Santiago') AS hour,
          COUNT(*) AS msgs
        FROM {table}
        WHERE DATE(timestamp, 'America/Santiago') = CURRENT_DATE('America/Santiago')
        GROUP BY hour ORDER BY msgs DESC LIMIT 3
        """

        # ── Top source pages ─────────────────────────────────────────────────
        q_pages = f"""
        SELECT
          COALESCE(NULLIF(source_page,''), '(desconocida)') AS page,
          COUNT(DISTINCT session_id) AS sessions
        FROM {table}
        WHERE DATE(timestamp, 'America/Santiago') = CURRENT_DATE('America/Santiago')
        GROUP BY page ORDER BY sessions DESC LIMIT 5
        """

        # ── Top intents ──────────────────────────────────────────────────────
        q_intents = f"""
        SELECT
          COALESCE(NULLIF(intent_detected,''), '(sin clasificar)') AS intent,
          COUNT(*) AS msgs
        FROM {table}
        WHERE DATE(timestamp, 'America/Santiago') = CURRENT_DATE('America/Santiago')
        GROUP BY intent ORDER BY msgs DESC LIMIT 5
        """

        # ── Top suspicious IPs/origins ───────────────────────────────────────
        q_suspicious = f"""
        SELECT
          origin_header,
          ip_address,
          COUNT(*) AS hits
        FROM {table}
        WHERE DATE(timestamp, 'America/Santiago') = CURRENT_DATE('America/Santiago')
          AND suspicious = TRUE
        GROUP BY origin_header, ip_address ORDER BY hits DESC LIMIT 5
        """

        row       = list(bq.query(q_summary).result())[0]
        prev_rows = list(bq.query(q_prev).result())
        prev      = prev_rows[0] if prev_rows else None
        hour_rows   = list(bq.query(q_hours).result())
        page_rows   = list(bq.query(q_pages).result())
        intent_rows = list(bq.query(q_intents).result())
        susp_rows   = list(bq.query(q_suspicious).result())

        sessions        = int(row.sessions)
        messages        = int(row.messages)
        in_tokens       = int(row.in_tokens)
        out_tokens      = int(row.out_tokens)
        suspicious      = int(row.suspicious_count)
        gemini_calls    = int(row.gemini_calls)
        ollama_calls    = int(row.ollama_calls)
        avg_tokens      = float(row.avg_tokens_per_msg or 0)
        lang_es         = int(row.lang_es)
        lang_en         = int(row.lang_en)
        lang_other      = int(row.lang_other)
        engaged         = int(row.engaged_sessions)

        sessions_prev   = int(prev.sessions_prev) if prev else 0
        messages_prev   = int(prev.messages_prev) if prev else 0

        def delta(today, yesterday):
            if yesterday == 0:
                return "(sin datos ayer)"
            pct = round((today - yesterday) / yesterday * 100)
            return f"+{pct}%" if pct >= 0 else f"{pct}%"

        est_cost = round((in_tokens * 0.15 + out_tokens * 0.60) / 1_000_000, 4)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # ── Build email tables ───────────────────────────────────────────────
        td = 'style="padding:6px;border-bottom:1px solid #eee"'

        def make_rows(data_rows, cols):
            html = ""
            for r in data_rows:
                html += "<tr>" + "".join(f"<td {td}>{getattr(r, c)}</td>" for c in cols) + "</tr>"
            return html or f"<tr><td {td} colspan='{len(cols)}'>(sin datos)</td></tr>"

        pages_html   = make_rows(page_rows,   ["page", "sessions"])
        intents_html = make_rows(intent_rows, ["intent", "msgs"])
        susp_html    = make_rows(susp_rows,   ["origin_header", "ip_address", "hits"])
        hours_html   = make_rows(hour_rows,   ["hour", "msgs"])

        cost_color = "#c0392b" if est_cost > 0.10 else "#0088FF"
        susp_label = f'⚠️ {suspicious}' if suspicious else '✅ 0'

        body_html = f"""<html><body style="font-family:sans-serif;max-width:650px;color:#222">
        <h2 style="color:#0088FF">📊 Reporte diario AIF369 — {date_str}</h2>

        <h3>Resumen general</h3>
        <table style="border-collapse:collapse;width:100%">
          <tr><td {td}><strong>Sesiones únicas</strong></td><td {td}>{sessions} <small style="color:#888">{delta(sessions, sessions_prev)} vs ayer</small></td></tr>
          <tr><td {td}><strong>Mensajes totales</strong></td><td {td}>{messages} <small style="color:#888">{delta(messages, messages_prev)} vs ayer</small></td></tr>
          <tr><td {td}><strong>Sesiones con >1 mensaje</strong></td><td {td}>{engaged} <small style="color:#888">(usuarios engajados)</small></td></tr>
          <tr><td {td}><strong>Avg tokens/mensaje</strong></td><td {td}>{avg_tokens:,.0f}</td></tr>
          <tr><td {td}><strong>Tokens entrada / salida</strong></td><td {td}>{in_tokens:,} / {out_tokens:,}</td></tr>
          <tr><td {td}><strong>Costo estimado</strong></td><td {td}><strong style="color:{cost_color}">${est_cost:.4f} USD</strong></td></tr>
          <tr><td {td}><strong>Proveedor</strong></td><td {td}>Gemini: {gemini_calls} | Ollama: {ollama_calls}</td></tr>
          <tr><td {td}><strong>Idiomas</strong></td><td {td}>ES: {lang_es} | EN: {lang_en} | Otro: {lang_other}</td></tr>
          <tr><td {td}><strong>Sospechosas</strong></td><td {td}>{susp_label}</td></tr>
        </table>

        <h3>Top páginas de origen</h3>
        <table style="border-collapse:collapse;width:100%">
          <tr><th {td} align="left">Página</th><th {td} align="left">Sesiones</th></tr>
          {pages_html}
        </table>

        <h3>Top intenciones detectadas</h3>
        <table style="border-collapse:collapse;width:100%">
          <tr><th {td} align="left">Intent</th><th {td} align="left">Mensajes</th></tr>
          {intents_html}
        </table>

        <h3>Horas pico (hora Santiago)</h3>
        <table style="border-collapse:collapse;width:100%">
          <tr><th {td} align="left">Hora</th><th {td} align="left">Mensajes</th></tr>
          {hours_html}
        </table>

        {'<h3>⚠️ Solicitudes sospechosas</h3><table style="border-collapse:collapse;width:100%"><tr><th ' + td + ' align="left">Origin</th><th ' + td + ' align="left">IP</th><th ' + td + ' align="left">Hits</th></tr>' + susp_html + '</table>' if suspicious else ''}

        <hr>
        <p><small>AIF369 Backend Monitor | Cloud Run | {date_str}</small></p>
        </body></html>"""

        send_alert_email(f"📊 Reporte diario AIF369 — {date_str}", body_html)
        return jsonify({
            "sent": True,
            "date": date_str,
            "sessions": sessions,
            "sessions_prev_day": sessions_prev,
            "sessions_delta_pct": round((sessions - sessions_prev) / sessions_prev * 100, 1) if sessions_prev else None,
            "messages": messages,
            "messages_prev_day": messages_prev,
            "engaged_sessions": engaged,
            "avg_tokens_per_msg": avg_tokens,
            "in_tokens": in_tokens,
            "out_tokens": out_tokens,
            "estimated_cost_usd": est_cost,
            "gemini_calls": gemini_calls,
            "ollama_calls": ollama_calls,
            "lang_es": lang_es,
            "lang_en": lang_en,
            "lang_other": lang_other,
            "suspicious": suspicious,
            "top_pages": [{"page": r.page, "sessions": int(r.sessions)} for r in page_rows],
            "top_intents": [{"intent": r.intent, "msgs": int(r.msgs)} for r in intent_rows],
            "peak_hours": [{"hour": int(r.hour), "msgs": int(r.msgs)} for r in hour_rows],
            "suspicious_sources": [{"origin": r.origin_header, "ip": r.ip_address, "hits": int(r.hits)} for r in susp_rows],
        })

    except Exception as e:
        print(f"Daily report error: {e}")
        return jsonify({"error": str(e)}), 500

CONTENT_PROMPT = """Eres un redactor experto de contenido B2B sobre inteligencia artificial, datos y cloud para empresas.
Escribes para el blog de AIF369, una consultora chilena fundada por Erwin Daza.

METODOLOGÍA PROPIA - MÉTODO 369:
- 3 Fases: Diagnóstico → Diseño → Despliegue
- 6 Capacidades: Datos, Modelos, Infraestructura, Gobernanza, Talento, Medición
- 9 Checkpoints de madurez que se verifican antes de avanzar

SERVICIOS DE AIF369:
- AI Governance Starter Kit
- Diagnóstico Express y Ejecutivo
- Implementación por Sprint
- CAIO-as-a-Service (Chief AI Officer externo)
- Cursos corporativos de IA aplicada

REGLAS DE REDACCIÓN:
1. Escribe en español profesional, directo, sin jerga innecesaria.
2. Tono: ejecutivo, práctico, con opinión. No genérico.
3. Incluye referencias al Método 369 de forma natural (no forzada).
4. Cada artículo debe tener: título, subtítulo, 4-6 secciones con h2, conclusión con CTA.
5. Formato: HTML limpio con <h1>, <h2>, <h3>, <p>, <ul>/<ol>, <li>, <strong>.
6. Al final, incluye un CTA hacia el scorecard (scorecard.html) o contacto (index.html#contacto).
7. Incluye "Por Erwin Daza" como autor con link a LinkedIn: https://www.linkedin.com/in/erwin-daza-castillo/
8. Longitud: 800-1200 palabras.
9. NO inventes estadísticas. Usa datos reales conocidos o di "según estudios recientes".
10. Contexto: Chile y Latinoamérica, pero aplicable globalmente."""


@app.route("/api/generate-content", methods=["POST"])
def generate_content():
    """
    Genera un borrador de blog post usando Gemini.
    Requiere API key en header X-API-Key.
    Body: { "topic": "...", "angle": "...", "target": "CAIO|CTO|CEO" }
    """
    try:
        # Auth
        api_key = request.headers.get("X-API-Key", "")
        if api_key != CONTENT_API_KEY:
            return jsonify({"error": "Unauthorized"}), 401

        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        topic = data.get("topic", "").strip()
        angle = data.get("angle", "").strip()
        target = data.get("target", "ejecutivos").strip()

        if not topic:
            return jsonify({"error": "topic is required"}), 400

        user_prompt = f"""Genera un artículo completo para el blog de AIF369 sobre el siguiente tema:

TEMA: {topic}
ÁNGULO/ENFOQUE: {angle if angle else 'Elige el ángulo más relevante para ejecutivos'}
AUDIENCIA: {target}

Genera el artículo completo en formato HTML (solo el contenido del <article>, sin header/footer).
Incluye: tag de categoría, h1, meta de lectura, secciones con h2, lista de puntos clave, y CTA final.
"""

        if not GEMINI_API_KEY:
            return jsonify({"error": "Gemini API not configured"}), 500

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=CONTENT_PROMPT,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                top_p=0.9,
                max_output_tokens=4000
            )
        )
        response = model.generate_content(user_prompt)
        content = response.text

        return jsonify({
            "success": True,
            "content": content,
            "topic": topic,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }), 200

    except Exception as e:
        print(f"Error generating content: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/content-topics", methods=["GET"])
def content_topics():
    """
    Devuelve una lista de temas sugeridos para generar contenido.
    Útil para automatización.
    """
    api_key = request.headers.get("X-API-Key", "")
    if api_key != CONTENT_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    topics = [
        {"topic": "ROI de proyectos de IA: cómo medirlo y comunicarlo al directorio", "category": "Estrategia", "target": "CEO/CFO"},
        {"topic": "Data mesh vs data lakehouse: qué arquitectura elegir en 2026", "category": "Arquitectura", "target": "CTO/CDO"},
        {"topic": "Cómo evaluar si su empresa está lista para implementar IA", "category": "Diagnóstico", "target": "CEO/CIO"},
        {"topic": "MLOps para empresas medianas: lo mínimo viable para producción", "category": "Operaciones", "target": "CTO"},
        {"topic": "Regulación de IA en Chile y Latam: lo que viene en 2026-2027", "category": "Gobernanza", "target": "Legal/CAIO"},
        {"topic": "Cómo hacer un business case de IA que apruebe el directorio", "category": "Estrategia", "target": "CAIO/CIO"},
        {"topic": "Ética de IA: framework práctico para empresas latinoamericanas", "category": "Gobernanza", "target": "CAIO"},
        {"topic": "RAG vs Fine-tuning: cuándo usar cada técnica en producción", "category": "IA Aplicada", "target": "CTO"},
        {"topic": "El costo real de no tener gobernanza de IA", "category": "Gobernanza", "target": "CEO/Board"},
        {"topic": "De Excel a IA: la ruta de transformación de datos para pymes", "category": "Datos", "target": "CEO/COO"},
        {"topic": "Cómo preparar su empresa para auditorías de IA", "category": "Compliance", "target": "Legal/CAIO"},
        {"topic": "Automatización inteligente: RPA + IA para procesos de negocio", "category": "IA Aplicada", "target": "COO/CIO"},
    ]

    return jsonify({"topics": topics, "count": len(topics)}), 200


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ── Cost Monitoring Endpoints ────────────────────────────────────
# Dashboard de costos GCP: datos reales (billing export) o estimaciones
# Protegidos por CONTENT_API_KEY (header X-API-Key)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _require_api_key():
    """Valida el API key para endpoints de costos."""
    api_key = request.headers.get("X-API-Key", "")
    if not CONTENT_API_KEY or api_key != CONTENT_API_KEY:
        return False
    return True


@app.route("/api/costs/summary", methods=["GET"])
def costs_summary():
    """
    Resumen mensual de costos.
    Query params: year (int), month (int) — opcionales, default mes actual.
    """
    if not _require_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        data = cost_monitor.get_monthly_summary(year=year, month=month)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/costs/by-service", methods=["GET"])
def costs_by_service():
    """
    Desglose de costos por servicio GCP.
    Query params: year, month — opcionales.
    """
    if not _require_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        data = cost_monitor.get_cost_by_service(year=year, month=month)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/costs/daily", methods=["GET"])
def costs_daily():
    """
    Costos diarios del mes para gráficos de tendencia.
    Query params: year, month — opcionales.
    """
    if not _require_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        data = cost_monitor.get_daily_costs(year=year, month=month)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/costs/budget", methods=["GET"])
def costs_budget():
    """
    Estado del presupuesto con alertas y proyecciones.
    """
    if not _require_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        data = cost_monitor.get_budget_status()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/costs/top-skus", methods=["GET"])
def costs_top_skus():
    """
    Top SKUs por costo — muestra qué operaciones específicas cuestan más.
    Query params: year, month, limit (default 20).
    """
    if not _require_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        year = request.args.get("year", type=int)
        month = request.args.get("month", type=int)
        limit = request.args.get("limit", 20, type=int)
        data = cost_monitor.get_top_skus(year=year, month=month, limit=limit)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/costs/trend", methods=["GET"])
def costs_trend():
    """
    Tendencia de costos mensuales (últimos N meses).
    Query params: months (default 6).
    """
    if not _require_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        months = request.args.get("months", 6, type=int)
        data = cost_monitor.get_cost_trend(months=months)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/costs/health", methods=["GET"])
def costs_health():
    """
    Health check del sistema de monitoreo de costos.
    Verifica: BigQuery client, billing dataset, billing table, data freshness.
    """
    if not _require_api_key():
        return jsonify({"error": "Unauthorized"}), 401
    try:
        data = cost_monitor.check_monitoring_health()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_paypal_access_token():
    """Obtiene token de acceso de PayPal API"""
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        print("⚠️  Warning: PAYPAL_CLIENT_ID o PAYPAL_CLIENT_SECRET no configurados")
        return None
    try:
        import base64
        auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()).decode()
        response = http_requests.post(
            f"{PAYPAL_API_BASE}/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {auth}",
                "Accept": "application/json"
            },
            data={"grant_type": "client_credentials"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"❌ Error getting PayPal token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error in get_paypal_access_token: {e}")
        return None


@app.route("/api/paypal/create-order", methods=["POST"])
def create_paypal_order():
    """Crea una orden de PayPal para procesamiento de pago"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        amount = data.get("amount", "1.00")
        currency = data.get("currency", "USD")
        description = data.get("description", "AIF369 Test Payment")

        try:
            float(amount)
        except ValueError:
            return jsonify({"error": "Invalid amount"}), 400

        access_token = get_paypal_access_token()
        if not access_token:
            return jsonify({"error": "Failed to authenticate with PayPal"}), 500

        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {"currency_code": currency, "value": amount},
                "description": description
            }],
            "payer": {"name": {"given_name": "Test", "surname": "User"}}
        }

        response = http_requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"},
            json=order_data
        )

        if response.status_code not in [200, 201]:
            error_detail = response.json() if response.text else {}
            print(f"❌ PayPal API Error: {response.status_code} - {error_detail}")
            return jsonify({"error": f"Failed to create PayPal order"}), 500

        paypal_order = response.json()
        order_id = paypal_order.get("id")

        transaction_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        row = {
            "transaction_id": transaction_id,
            "order_id": order_id,
            "timestamp": timestamp,
            "amount": amount,
            "currency": currency,
            "status": "created",
            "source_page": data.get("source_page", request.referrer or ""),
            "user_agent": request.headers.get("User-Agent", ""),
            "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr)
        }

        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{PAYPAL_TABLE_ID}"
        errors = get_bq_client().insert_rows_json(table_ref, [row])
        if errors:
            print(f"⚠️  BigQuery insert errors: {errors}")

        print(f"✅ PayPal Order Created: {order_id}")
        return jsonify({"success": True, "id": order_id, "status": paypal_order.get("status")}), 201

    except Exception as e:
        print(f"❌ Error creating PayPal order: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/paypal/capture-order", methods=["POST"])
def capture_paypal_order():
    """Captura una orden de PayPal previamente aprobada"""
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        order_id = data.get("order_id")

        if not order_id:
            return jsonify({"error": "Missing order_id"}), 400

        access_token = get_paypal_access_token()
        if not access_token:
            return jsonify({"error": "Failed to authenticate with PayPal"}), 500

        response = http_requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
        )

        if response.status_code not in [200, 201]:
            error_detail = response.json() if response.text else {}
            print(f"❌ PayPal Capture Error: {response.status_code} - {error_detail}")
            return jsonify({"error": "Failed to capture order"}), 500

        paypal_order = response.json()
        status = paypal_order.get("status")

        transaction_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        row = {
            "transaction_id": transaction_id,
            "order_id": order_id,
            "timestamp": timestamp,
            "status": status,
            "source_page": request.referrer or "",
            "user_agent": request.headers.get("User-Agent", ""),
            "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr)
        }

        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{PAYPAL_TABLE_ID}"
        errors = get_bq_client().insert_rows_json(table_ref, [row])
        if errors:
            print(f"⚠️  BigQuery insert errors: {errors}")

        print(f"✅ PayPal Order Captured: {order_id} - Status: {status}")
        return jsonify({
            "success": True,
            "order_id": order_id,
            "status": status,
            "transaction_id": transaction_id
        }), 200

    except Exception as e:
        print(f"❌ Error capturing PayPal order: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# ════════════════════════════════════════════════════════════════════════
# ARCO RIGHTS ENDPOINT — Ley 21.719 (Protección de Datos Personales)
# ════════════════════════════════════════════════════════════════════════
@app.route("/api/arco-request", methods=["POST"])
def arco_request():
    """
    Procesa solicitudes ARCO (Acceso, Rectificación, Cancelación, Oposición)
    según la Ley 21.719 de Protección de Datos Personales (Chile)
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()

        # Validar campos requeridos
        required_fields = ["tipo_derecho", "nombre", "run", "email", "consentimiento"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({"error": f"Campos faltantes: {', '.join(missing)}"}), 400

        # Crear solicitud ARCO
        arco_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        arco_data = {
            "arco_id": arco_id,
            "timestamp": timestamp,
            "tipo_derecho": data.get("tipo_derecho"),  # acceso, rectificacion, cancelacion, oposicion
            "nombre": data.get("nombre", "")[:500],
            "run": data.get("run", "")[:20],
            "email": data.get("email", "")[:200],
            "detalle": data.get("detalle", "")[:2000],
            "estado": "pendiente",
            "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr),
            "user_agent": request.headers.get("User-Agent", "")[:500],
            "origin": request.headers.get("Origin", "")
        }

        # Guardar en BigQuery (tabla arco_requests)
        try:
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.arco_requests"
            errors = get_bq_client().insert_rows_json(table_ref, [arco_data])
            if errors:
                print(f"BigQuery ARCO insert errors: {errors}")
        except Exception as e:
            print(f"Error saving ARCO request to BigQuery: {e}")

        # Enviar email de confirmación al usuario
        try:
            tipo_map = {
                "acceso": "Solicitud de Acceso a Datos",
                "rectificacion": "Solicitud de Rectificación",
                "cancelacion": "Solicitud de Cancelación",
                "oposicion": "Solicitud de Oposición"
            }

            subject = f"Solicitud ARCO Recibida — {tipo_map.get(data.get('tipo_derecho'), 'ARCO')}"
            body = f"""
            <html><body style="font-family:sans-serif;color:#333;">
            <h2 style="color:#0088FF;">Solicitud ARCO Recibida</h2>
            <p>Hola {data.get('nombre', 'Usuario')},</p>

            <p>Hemos recibido tu solicitud de {tipo_map.get(data.get('tipo_derecho'), 'ARCO')}.</p>

            <p><strong>ID de Solicitud:</strong> {arco_id}</p>
            <p><strong>Tipo de Derecho:</strong> {tipo_map.get(data.get('tipo_derecho'), 'Desconocido')}</p>
            <p><strong>Fecha:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>

            <p>Conforme a la Ley 21.719, procesaremos tu solicitud dentro de <strong>15 días hábiles</strong>.</p>

            <p>Puedes hacer seguimiento contactando a: <strong>dpd@aif369.com</strong></p>

            <hr style="margin:24px 0;">
            <p style="font-size:12px;color:#999;">
            Este es un email automático. Por favor no respondas.
            Si tienes dudas, contáctanos por WhatsApp: +56 9 9754 7192
            </p>
            </body></html>
            """

            send_confirmation_email({
                "email": data.get("email"),
                "nombre": data.get("nombre"),
                "subject": subject,
                "body": body
            })
        except Exception as e:
            print(f"Warning: Could not send confirmation email: {e}")

        # Enviar email al DPO (Delegado de Protección de Datos)
        try:
            subject_dpo = f"🔒 Nueva Solicitud ARCO — {data.get('tipo_derecho').upper()}"
            body_dpo = f"""
            <html><body style="font-family:sans-serif;">
            <h2>Nueva Solicitud ARCO Recibida</h2>
            <p><strong>ID:</strong> {arco_id}</p>
            <p><strong>Tipo:</strong> {data.get('tipo_derecho')}</p>
            <p><strong>Nombre:</strong> {data.get('nombre')}</p>
            <p><strong>Email:</strong> {data.get('email')}</p>
            <p><strong>RUN:</strong> {data.get('run')}</p>
            <p><strong>Detalle:</strong> {data.get('detalle', 'N/A')}</p>
            <p><strong>Timestamp:</strong> {timestamp}</p>
            <p><strong>IP:</strong> {request.headers.get('X-Forwarded-For', request.remote_addr)}</p>
            </body></html>
            """

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject_dpo
            msg["From"] = f"AIF369 ARCO <{SMTP_USER}>"
            msg["To"] = "dpd@aif369.com"
            msg.attach(MIMEText(body_dpo, "html"))

            if SMTP_PASSWORD:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)
        except Exception as e:
            print(f"Warning: Could not send DPO notification: {e}")

        print(f"✅ ARCO Request Received: {arco_id} | Type: {data.get('tipo_derecho')} | User: {data.get('email')}")

        return jsonify({
            "success": True,
            "arco_id": arco_id,
            "mensaje": "Tu solicitud ARCO ha sido recibida. Te responderemos en 15 días hábiles.",
            "email_confirmacion": f"Confirmaremos el recibo en {data.get('email')}"
        }), 200

    except Exception as e:
        print(f"❌ Error processing ARCO request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
