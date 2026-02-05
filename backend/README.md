# Backend AIF369 - Formulario de Contacto

Backend API para recibir y almacenar formularios de contacto del sitio AIF369 en BigQuery.

## 📋 Arquitectura

```
Sitio Web (Vercel) → Cloud Run API → BigQuery (aif369_analytics)
```

## 🚀 Despliegue

### Opción 1: Despliegue manual con script

```bash
cd /Users/macbookpro/dev/aif369-web

# Hacer el script ejecutable
chmod +x backend/deploy.sh

# Configurar Docker para GCR
gcloud auth configure-docker

# Ejecutar despliegue
./backend/deploy.sh
```

### Opción 2: Terraform + despliegue manual

```bash
cd infra/terraform

# 1. Crear tabla BigQuery y recursos Cloud Run
terraform apply \
  -var="project_id=aif369-backend" \
  -var="region=us-central1" \
  -var="location=US" \
  -var="environment=dev"

# 2. Construir y subir imagen
cd ../../backend
docker build -t gcr.io/aif369-backend/aif369-backend:latest .
docker push gcr.io/aif369-backend/aif369-backend:latest

# 3. Desplegar a Cloud Run
gcloud run deploy aif369-backend-api \
  --image gcr.io/aif369-backend/aif369-backend:latest \
  --platform managed \
  --region us-central1 \
  --project aif369-backend \
  --allow-unauthenticated
```

## 📡 API Endpoints

### `POST /api/contact`

Recibe datos del formulario de contacto.

**Request:**
```json
{
  "name": "Juan Pérez",
  "email": "juan@example.com",
  "company": "Empresa XYZ",
  "message": "Estoy interesado en sus servicios...",
  "source_page": "https://aif369.com/services.html"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "submission_id": "uuid-here",
  "message": "Gracias por tu mensaje. Te contactaremos pronto."
}
```

**Response (400 Bad Request):**
```json
{
  "error": "Missing required fields: name, email"
}
```

## 🔧 Integración con el Frontend

En tu formulario HTML (Vercel), actualizar el JavaScript:

```javascript
// scripts.js o en el archivo correspondiente
const BACKEND_URL = "https://aif369-backend-api-XXXXXX-uc.a.run.app"; // URL de Cloud Run

async function handleContactForm(event) {
  event.preventDefault();
  
  const formData = {
    name: document.getElementById('name').value,
    email: document.getElementById('email').value,
    company: document.getElementById('company')?.value || '',
    message: document.getElementById('message').value,
    source_page: window.location.href
  };
  
  try {
    const response = await fetch(`${BACKEND_URL}/api/contact`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData)
    });
    
    const result = await response.json();
    
    if (response.ok) {
      alert(result.message);
      document.getElementById('contact-form').reset();
    } else {
      alert('Error: ' + result.error);
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Error al enviar el formulario. Por favor intenta de nuevo.');
  }
}

// Agregar listener al formulario
document.getElementById('contact-form').addEventListener('submit', handleContactForm);
```

## 📊 Consultar datos en BigQuery

```sql
-- Ver todos los contactos recibidos
SELECT 
  timestamp,
  name,
  email,
  company,
  message,
  source_page
FROM `aif369-backend.aif369_analytics.contact_form_submissions`
ORDER BY timestamp DESC
LIMIT 100;

-- Contactos por día
SELECT 
  DATE(timestamp) as date,
  COUNT(*) as submissions
FROM `aif369-backend.aif369_analytics.contact_form_submissions`
GROUP BY date
ORDER BY date DESC;
```

## 🧪 Testing local

```bash
cd backend

# Instalar dependencias
pip install -r requirements.txt

# Exportar credenciales
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export PROJECT_ID="aif369-backend"

# Ejecutar
python main.py

# Probar endpoint
curl -X POST http://localhost:8080/api/contact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "message": "This is a test message"
  }'
```

## 🔒 Seguridad

- CORS configurado para dominios específicos de AIF369
- Service Account con permisos mínimos (solo BigQuery dataEditor)
- Validación de campos requeridos
- Rate limiting configurado en Cloud Run (autoscaling)

## 📧 Próximos pasos

1. Configurar notificaciones por email cuando llegue un formulario
2. Agregar captcha para evitar spam
3. Dashboard de analytics con Looker Studio
