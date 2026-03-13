import os
import json
import uuid
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from google.cloud import bigquery
import google.generativeai as genai

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
DATASET_ID = "aif369_analytics"
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

SYSTEM_PROMPT = """Eres el asistente virtual de AIF369, una consultora especializada en IA, Datos y Cloud para empresas.
Tu nombre es AIF369 Assistant. Responde en el mismo idioma que el usuario.

SERVICIOS Y PRECIOS:
- AI Governance Starter Kit: USD 890 — Diagnóstico de madurez, plantillas de gobernanza, roadmap de 90 días. Entregado en 10 días.
- Diagnóstico Express: USD 1.500 — Evaluación ejecutiva en 5 días con roadmap priorizado, entrevistas con stakeholders y presentación al C-level.
- Diagnóstico Ejecutivo: USD 4.500 — Deep-dive de 3-4 semanas, benchmark sectorial, plan de transformación completo, sesiones con hasta 10 stakeholders.
- Implementación: USD 12.000/sprint — Sprints de 2-4 semanas para desplegar pipelines de datos, modelos ML, agentes de IA o infraestructura cloud.
- CAIO-as-a-Service: USD 4.000/mes — Acompañamiento estratégico continuo como Chief AI Officer externo, governance avanzado, formación del equipo.

HERRAMIENTA GRATUITA:
- AI Readiness Scorecard: Evaluación gratuita de madurez en IA en 5 minutos con recomendaciones personalizadas. Disponible en aif369.com/scorecard.html

FORMACIÓN:
- Cursos corporativos de IA aplicada, Data Engineering, MLOps y Generative AI para equipos técnicos y ejecutivos.

SOBRE AIF369:
- Fundada por Erwin Daza, consultor con experiencia en transformación digital, IA y datos para corporaciones.
- Enfoque: ROI medible, governance, seguridad y operación continua.
- Trabajan con CIOs, CDOs, CAIOs y equipos de arquitectura.

REGLAS:
- Sé conciso, profesional y útil. Máximo 3-4 oraciones por respuesta.
- Si el usuario pregunta algo fuera de tu alcance, redirige amablemente a agendar una conversación gratuita.
- Siempre intenta conectar las necesidades del usuario con un servicio específico.
- Si el usuario parece interesado, sugiere agendar una conversación gratuita o hacer el AI Readiness Scorecard.
- No inventes datos ni estadísticas que no estén aquí.
- Para preguntas técnicas complejas, sugiere una conversación con el equipo."""


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
    """Envía email de confirmación al cliente"""
    if not SMTP_PASSWORD:
        return False
    
    try:
        optional_lines = ""
        if submission_data.get("interest"):
            optional_lines += f'<p><strong>Interés:</strong> {submission_data["interest"]}</p>'
        if submission_data.get("team_size"):
            optional_lines += f'<p><strong>Tamaño del equipo:</strong> {submission_data["team_size"]}</p>'

        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '✓ Hemos recibido tu solicitud - AIF369'
        msg['From'] = SMTP_USER
        msg['To'] = submission_data["email"]
        
        # Contenido HTML
        html = f'''
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2 style="color: #2563eb;">¡Gracias por contactarnos!</h2>
              <p>Hola <strong>{submission_data["name"]}</strong>,</p>
              <p>Hemos recibido tu solicitud y te contactaremos en las próximas 24 horas.</p>
              
              <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #1f2937;">Resumen de tu solicitud:</h3>
                <p><strong>Email:</strong> {submission_data["email"]}</p>
                <p><strong>Empresa/Cargo:</strong> {submission_data["company"]}</p>
                {optional_lines}
                <p><strong>Mensaje:</strong> {submission_data["message"]}</p>
              </div>
              
              <p>Mientras tanto, puedes explorar más sobre nuestros servicios en <a href="https://aif369.com" style="color: #2563eb;">aif369.com</a></p>
              
              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              
              <p style="font-size: 12px; color: #6b7280;">
                AIF369 - IA, Datos y Cloud para la empresa moderna<br>
                <a href="https://aif369.com" style="color: #2563eb;">aif369.com</a>
              </p>
            </div>
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
        
        print(f"Confirmation email sent to {submission_data['email']}")
        return True
    except Exception as e:
        print(f"Error sending confirmation email: {e}")
        return False


@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "aif369-backend"}), 200


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
    Chatbot endpoint powered by Gemini.
    Expected JSON: { "message": "...", "history": [...] }
    """
    try:
        if not GEMINI_API_KEY:
            return jsonify({"error": "Chat not configured"}), 503

        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        user_message = data.get("message", "").strip()
        history = data.get("history", [])

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # Build conversation for Gemini
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT
        )

        # Convert history to Gemini format
        gemini_history = []
        for msg in history[-10:]:  # Keep last 10 messages for context
            role = "user" if msg.get("role") == "user" else "model"
            gemini_history.append({"role": role, "parts": [msg.get("content", "")]})

        chat_session = model.start_chat(history=gemini_history)
        response = chat_session.send_message(user_message)

        return jsonify({
            "response": response.text,
            "success": True
        }), 200

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            "error": "Error processing your message",
            "response": "Lo siento, no pude procesar tu mensaje. ¿Podrías intentar de nuevo?",
            "success": False
        }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
