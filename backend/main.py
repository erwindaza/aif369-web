import os
import json
import uuid
import smtplib
import re
import requests as http_requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
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
    re.compile(r"^https://.*\\.vercel\\.app$"),
    re.compile(r"^http://localhost(:\\d+)?$")
])

# Cliente de BigQuery
PROJECT_ID = os.getenv("PROJECT_ID", "aif369-backend")
DATASET_ID = os.getenv("DATASET_ID", "aif369_analytics")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
TABLE_ID = "contact_form_submissions"

bq_client = bigquery.Client(project=PROJECT_ID)

# Configuración SMTP de Zoho Mail
SMTP_HOST = "smtp.zoho.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER", "edaza@aif369.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "edaza@aif369.com")
CC_EMAIL = os.getenv("CC_EMAIL", "erwin.daza@gmail.com")

# Configuración de Gemini para el chatbot
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Configuración de Ollama como fallback
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b")

SYSTEM_PROMPT = """Eres el asistente virtual de AIF369, una consultora chilena especializada en AI Factory, Governance, Risk y Business Value.
Tu nombre es AIF369 Assistant. Responde en el mismo idioma que el usuario.

IMPORTANTE — REGLAS ESTRICTAS (OBLIGATORIAS):
1. SOLO hablas de: servicios de AIF369, Método 369, contratación, empleo y temas directamente relacionados con lo que se lista abajo.
2. Si te preguntan algo que NO está en este prompt, responde: "No tengo esa información. Para consultas específicas, escríbenos por WhatsApp: +56 9 9754 7192"
3. NUNCA inventes, supongas ni especules. 0% creatividad. Solo responde con datos que están aquí.
4. Si no sabes algo con certeza, di que no lo sabes y redirige a WhatsApp.
5. Máximo 3-4 oraciones por respuesta. Sé directo y preciso.
6. No respondas preguntas personales, políticas, de entretenimiento ni de ningún tema ajeno a AIF369.

MÉTODO 369 (Metodología propietaria de AIF369):
- 3 Capas de Dirección: (1) Estratégica — visión, priorización, roadmap; (2) Riesgo y Cumplimiento — risk register, compliance, privacidad; (3) Implementación — arquitectura, MLOps, despliegue.
- 6 Fases de Transformación: Descubrir, Diagnosticar, Diseñar, Desplegar, Dominar, Escalar.
- 9 Métricas de Control CAIO: Estrategia IA, Gobierno IA, Gestión de Riesgos IA, Privacidad y Datos, AI Factory Design, Observabilidad de Modelos, Ética y Responsible AI, Regulación y Compliance, Formación y Cultura.

SERVICIOS (sin mencionar precios, redirigir a contacto para cotización):
- CAIO Advisory as a Service — Acompañamiento ejecutivo: estrategia, gobierno, riesgos y adopción de IA.
- AI Governance & Responsible AI — Marco de gobierno, accountability, políticas, controles y roles.
- AI Risk, Privacy & Compliance — Evaluación de riesgos, privacidad y preparación regulatoria.
- AI Factory Design — Diseño de capacidades internas para construir, operar y escalar IA.
- Executive Workshops & Board Enablement — Talleres para directorio y C-level.
- Thought Leadership & Content Advisory — Posicionamiento de marca y contenido original.

PAQUETES DE ENGAGEMENT:
- Starter 369 (4-6 semanas) — Diagnóstico + hoja de ruta.
- Governed Pilot 369 (8-12 semanas) — Un caso de uso en producción con gobernanza integrada.
- Enterprise 369 (3-6 meses) — Estrategia + gobierno + AI Factory + despliegue completo.

IMPORTANTE SOBRE PRECIOS:
- NO menciones precios ni valores específicos. Si preguntan por precios, responde: "Los precios dependen de cada proyecto. Coordina por WhatsApp +56 9 9754 7192 para una cotización personalizada."

MODALIDAD DE CONTRATACIÓN:
- AIF369 opera desde Chile y emite boleta de honorarios.
- Los servicios se contratan directamente con AIF369.
- Para coordinar contratación, forma de pago o facturación: WhatsApp +56 9 9754 7192

HERRAMIENTA GRATUITA:
- AI Readiness Scorecard: Evaluación gratuita de madurez en IA en 5 minutos. Disponible en aif369.com/scorecard.html

SOBRE AIF369:
- Fundada por Erwin Daza Castillo — CAIO Advisor, Data & AI Architect, AI Governance Strategist.
- Creador del Método 369 para adopción gobernada de IA.
- Empresa chilena. Emite boleta de honorarios.
- Enfoque: ROI medible, governance, riesgo y operación continua.

CONTEXTO REGULATORIO:
- EU AI Act: marco de referencia para clasificación de riesgo de sistemas IA.
- Chile Ley 21.719: Protección de datos personales, vigencia 1 dic 2026.
- Boletín 16821-19: Proyecto de ley de IA en Chile, actualmente en tramitación.

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
            <p><strong>Empresa/Cargo:</strong> {submission_data["company"]}</p>
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


@app.route("/api/config/paypal", methods=["GET"])
def get_paypal_config():
    """Return PayPal client-id from environment (Secret Manager in production)."""
    client_id = os.getenv("PAYPAL_CLIENT_ID", "")
    if not client_id:
        return jsonify({"error": "PayPal not configured"}), 503
    return jsonify({"client_id": client_id}), 200


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
        company = data.get("company") or data.get("role") or ""
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
            "message": message,
            "source_page": data.get("source_page", request.referrer or ""),
            "user_agent": request.headers.get("User-Agent", ""),
            "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr),
            "form_type": data.get("form_type") or None,
            "interest": interest or None,
            "team_size": team_size or None
        }
        
        # Insertar en BigQuery
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        errors = bq_client.insert_rows_json(table_ref, [row])
        
        if errors:
            print(f"BigQuery insert errors: {errors}")
            return jsonify({
                "error": "Failed to save submission",
                "details": errors
            }), 500
        
        # Enviar notificaciones por email
        email_data = {
            **row,
            "submission_id": submission_id
        }
        send_email_notification(email_data)  # A nosotros
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
        errors = bq_client.insert_rows_json(table_ref, [row])

        if errors:
            print(f"BigQuery insert errors: {errors}")
            return jsonify({
                "error": "Failed to save submission",
                "details": errors
            }), 500

        email_data = {
            **row,
            "submission_id": submission_id
        }
        send_email_notification(email_data)
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
        errors = bq_client.insert_rows_json(table_ref, [message_data])
        if errors:
            print(f"Chat BQ insert errors: {errors}")
            return False
        print(f"Chat saved to BQ: session={message_data.get('session_id', '?')}, turn={message_data.get('turn_number', '?')}")
        return True
    except Exception as e:
        print(f"Error saving chat to BigQuery: {e}")
        return False

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
        dimensions_data = data.get("dimensions", {})
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
            errors = bq_client.insert_rows_json(table_ref, [row])
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
            bq_client.insert_rows_json(table_ref, [fallback_row])

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

        return jsonify({
            "success": True,
            "submission_id": submission_id,
            "message": "Scorecard submitted successfully"
        }), 200

    except Exception as e:
        print(f"Error processing scorecard: {str(e)}")
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Chatbot endpoint. Primary: Gemini. Fallback: Ollama (local).
    Expected JSON: { "message": "...", "history": [...], "session_id": "...", "turn_number": 1, "source_page": "..." }
    Persiste cada intercambio en BigQuery para seguimiento y analytics.
    """
    try:
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

        # Detectar intención e idioma para analytics
        intent = detect_intent(user_message)
        language = detect_language(user_message)

        reply = None
        provider = "none"

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
                print("Chat response via Gemini")
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
                "user_message": user_message[:5000],       # Limitar tamaño
                "assistant_response": reply[:5000],
                "provider": provider,
                "turn_number": turn_number,
                "source_page": source_page,
                "user_agent": request.headers.get("User-Agent", ""),
                "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr),
                "language": language,
                "intent_detected": intent
            }
            save_chat_to_bigquery(chat_row)
        except Exception as bq_err:
            print(f"Non-blocking BQ save error: {bq_err}")

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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
