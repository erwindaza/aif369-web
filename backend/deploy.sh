# Script para construir y desplegar el backend a Cloud Run

#!/bin/bash
set -e

PROJECT_ID="aif369-backend"
REGION="us-central1"
SERVICE_NAME="aif369-backend-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/aif369-backend:latest"

echo "🏗️  Construyendo imagen Docker..."
cd backend
docker build --platform linux/amd64 -t ${IMAGE_NAME} .

echo "📤 Subiendo imagen a Container Registry..."
docker push ${IMAGE_NAME}

echo "🚀 Desplegando a Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --allow-unauthenticated \
  --service-account aif369-backend-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars "PROJECT_ID=${PROJECT_ID},DATASET_ID=aif369_analytics,ENVIRONMENT=production" \
  --update-secrets "GEMINI_API_KEY=aif369-gemini-api-key:latest,SMTP_PASSWORD=aif369-smtp-password:latest,CONTENT_API_KEY=aif369-content-api-key:latest"

echo "✅ Despliegue completado!"
gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --format='value(status.url)'
