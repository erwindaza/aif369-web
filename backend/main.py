import os
import json
import uuid
import smtplib
import re
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import bigquery
import base64

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
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "erwin.daza@gmail.com")

# Configuración PayPal
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_SECRET") or os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")  # sandbox o live
PAYPAL_API_BASE = "https://api-m.sandbox.paypal.com" if PAYPAL_MODE == "sandbox" else "https://api-m.paypal.com"
PAYPAL_TABLE_ID = "paypal_transactions"


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
        msg['Subject'] = f'{subject_prefix}: {submission_data["name"]}'
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
        
        print(f"Email notification sent to {NOTIFICATION_EMAIL}")
        return True
    except Exception as e:
        print(f"Error sending email notification: {e}")
        return False


def get_paypal_access_token():
    """Obtiene token de acceso de PayPal API"""
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        print("Warning: PAYPAL_CLIENT_ID or PAYPAL_CLIENT_SECRET not configured")
        return None

    try:
        auth = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()).decode()
        response = requests.post(
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
            print(f"Error getting PayPal token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error in get_paypal_access_token: {e}")
        return None


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
        timestamp = datetime.utcnow().isoformat()
        
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
        timestamp = datetime.utcnow().isoformat()

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


@app.route("/api/paypal/create-order", methods=["POST"])
def create_paypal_order():
    """
    Crea una orden de PayPal para procesamiento de pago.

    Expected JSON payload:
    {
        "amount": "1.00",
        "currency": "USD",
        "description": "Test Payment",
        "source_page": "https://..."
    }
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        amount = data.get("amount", "1.00")
        currency = data.get("currency", "USD")
        description = data.get("description", "AIF369 Test Payment")
        source_page = data.get("source_page", request.referrer or "")

        # Validar cantidad
        try:
            float(amount)
        except ValueError:
            return jsonify({"error": "Invalid amount"}), 400

        # Obtener token de acceso
        access_token = get_paypal_access_token()
        if not access_token:
            return jsonify({"error": "Failed to authenticate with PayPal"}), 500

        # Crear orden en PayPal
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": currency,
                        "value": amount
                    },
                    "description": description
                }
            ],
            "payer": {
                "name": {
                    "given_name": "Test",
                    "surname": "User"
                }
            }
        }

        response = requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            },
            json=order_data
        )

        if response.status_code not in [200, 201]:
            error_detail = response.json() if response.text else {}
            print(f"PayPal API Error: {response.status_code} - {error_detail}")
            return jsonify({
                "error": f"Failed to create PayPal order: {error_detail.get('message', 'Unknown error')}"
            }), 500

        paypal_order = response.json()
        order_id = paypal_order.get("id")

        # Guardar en BigQuery
        transaction_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        row = {
            "transaction_id": transaction_id,
            "order_id": order_id,
            "timestamp": timestamp,
            "amount": amount,
            "currency": currency,
            "status": "created",
            "source_page": source_page,
            "user_agent": request.headers.get("User-Agent", ""),
            "ip_address": request.headers.get("X-Forwarded-For", request.remote_addr)
        }

        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{PAYPAL_TABLE_ID}"
        errors = bq_client.insert_rows_json(table_ref, [row])

        if errors:
            print(f"BigQuery insert errors: {errors}")

        print(f"✅ PayPal Order Created: {order_id}")

        return jsonify({
            "success": True,
            "id": order_id,
            "status": paypal_order.get("status"),
            "transaction_id": transaction_id
        }), 201

    except Exception as e:
        print(f"Error creating PayPal order: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


@app.route("/api/paypal/capture-order", methods=["POST"])
def capture_paypal_order():
    """
    Captura una orden de PayPal previamente aprobada.

    Expected JSON payload:
    {
        "order_id": "3SE30521KFXPM"
    }
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.get_json()
        order_id = data.get("order_id")

        if not order_id:
            return jsonify({"error": "Missing order_id"}), 400

        # Obtener token de acceso
        access_token = get_paypal_access_token()
        if not access_token:
            return jsonify({"error": "Failed to authenticate with PayPal"}), 500

        # Capturar orden en PayPal
        response = requests.post(
            f"{PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
        )

        if response.status_code not in [200, 201]:
            error_detail = response.json() if response.text else {}
            print(f"PayPal Capture Error: {response.status_code} - {error_detail}")
            return jsonify({
                "error": f"Failed to capture order: {error_detail.get('message', 'Unknown error')}"
            }), 500

        paypal_order = response.json()
        status = paypal_order.get("status")

        # Actualizar en BigQuery (si es posible, o crear nuevo registro)
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
        errors = bq_client.insert_rows_json(table_ref, [row])

        if errors:
            print(f"BigQuery insert errors: {errors}")

        print(f"✅ PayPal Order Captured: {order_id} - Status: {status}")

        return jsonify({
            "success": True,
            "order_id": order_id,
            "status": status,
            "transaction_id": transaction_id,
            "amount": paypal_order.get("purchase_units", [{}])[0].get("payments", {}).get("captures", [{}])[0].get("amount", {}).get("value")
        }), 200

    except Exception as e:
        print(f"Error capturing PayPal order: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
