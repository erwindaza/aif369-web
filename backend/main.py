import os
import json
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import bigquery

app = Flask(__name__)

# Configurar CORS para permitir requests desde Vercel
CORS(app, origins=[
    "https://aif369.com",
    "https://www.aif369.com",
    "https://*.vercel.app",
    "http://localhost:*"
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
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "erwin.daza@gmail.com")


def send_email_notification(submission_data):
    """Envía notificación por email usando SMTP de Zoho (para nosotros)"""
    if not SMTP_PASSWORD:
        print("Warning: SMTP_PASSWORD not configured. Skipping email notification.")
        return False
    
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Nuevo contacto: {submission_data["name"]}'
        msg['From'] = SMTP_USER
        msg['To'] = NOTIFICATION_EMAIL
        
        # Contenido HTML
        html = f'''
        <html>
          <body>
            <h2>Nuevo formulario de contacto recibido</h2>
            <p><strong>Nombre:</strong> {submission_data["name"]}</p>
            <p><strong>Email:</strong> {submission_data["email"]}</p>
            <p><strong>Empresa/Cargo:</strong> {submission_data["company"]}</p>
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
        
        print(f"Email notification sent to {NOTIFICATION_EMAIL}")
        return True
    except Exception as e:
        print(f"Error sending email notification: {e}")
        return False


def send_confirmation_email(submission_data):
    """Envía email de confirmación al cliente"""
    if not SMTP_PASSWORD:
        return False
    
    try:
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
        
        # Validar campos requeridos
        required_fields = ["name", "email", "message"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                "error": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400
        
        # Preparar datos para BigQuery
        submission_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        row = {
            "submission_id": submission_id,
            "timestamp": timestamp,
            "name": data["name"],
            "email": data["email"],
            "company": data.get("company", ""),
            "message": data["message"],
            "source_page": data.get("source_page", request.referrer or ""),
            "user_agent": request.headers.get("User-Agent", ""),
            "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr)
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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
