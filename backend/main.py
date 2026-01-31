import os
import json
import uuid
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
