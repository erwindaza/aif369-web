#!/usr/bin/env bash
# =============================================================================
# rotate-secrets.sh — Rotación completa de credenciales tras incidente de seguridad
# Ejecutar SOLO después de que GCP reactive el proyecto aif369-backend.
# =============================================================================
set -euo pipefail

PROJECT="aif369-backend"
REGION="us-central1"

echo "========================================================"
echo " ROTACIÓN DE CREDENCIALES — Proyecto: $PROJECT"
echo " Ejecutar con: bash scripts/rotate-secrets.sh"
echo "========================================================"
echo ""

gcloud config set project "$PROJECT"

# ------------------------------------------------------------
# PASO 1: Deshabilitar la clave de API de Gemini comprometida
# ------------------------------------------------------------
echo "⚠️  PASO 1: Ve a https://aistudio.google.com/apikey"
echo "   Elimina la clave anterior (esta fue expuesta, debe ser rotada)."
echo "   Genera una nueva clave y pégala aquí abajo."
echo ""
read -rsp "Nueva GEMINI_API_KEY: " NEW_GEMINI_KEY
echo ""

# ------------------------------------------------------------
# PASO 2: Cambiar contraseña SMTP en Zoho
# ------------------------------------------------------------
echo "⚠️  PASO 2: Ve a https://accounts.zoho.com → Security → App Passwords"
echo "   Elimina la contraseña de aplicación existente y crea una nueva."
echo ""
read -rsp "Nueva SMTP_PASSWORD: " NEW_SMTP_PASS
echo ""

# ------------------------------------------------------------
# PASO 3: Nuevo CONTENT_API_KEY (clave interna)
# ------------------------------------------------------------
NEW_CONTENT_KEY=$(openssl rand -hex 24)
echo "✅  Nuevo CONTENT_API_KEY generado: $NEW_CONTENT_KEY"
echo ""

# ------------------------------------------------------------
# PASO 4: Credenciales de PayPal
# ------------------------------------------------------------
echo "⚠️  PASO 4: Ve a https://developer.paypal.com/dashboard/applications"
echo "   Regenera el Client Secret de tu app de producción."
echo ""
read -rsp "PAYPAL_CLIENT_ID: " NEW_PAYPAL_CLIENT_ID
echo ""
read -rsp "PAYPAL_SECRET: " NEW_PAYPAL_SECRET
echo ""

# ------------------------------------------------------------
# PASO 5: Actualizar Secret Manager
# ------------------------------------------------------------
echo ""
echo "🔄  Actualizando Secret Manager..."

update_or_create_secret() {
  local name="$1"
  local value="$2"

  if gcloud secrets describe "$name" --project="$PROJECT" &>/dev/null; then
    echo "$value" | gcloud secrets versions add "$name" \
      --project="$PROJECT" --data-file=-
    echo "   ✅  $name — nueva versión añadida"
  else
    echo "$value" | gcloud secrets create "$name" \
      --project="$PROJECT" --data-file=- --replication-policy="automatic"
    echo "   ✅  $name — secret creado"
  fi
}

update_or_create_secret "aif369-gemini-api-key"    "$NEW_GEMINI_KEY"
update_or_create_secret "aif369-smtp-password"     "$NEW_SMTP_PASS"
update_or_create_secret "aif369-content-api-key"   "$NEW_CONTENT_KEY"
update_or_create_secret "aif369-paypal-client-id"  "$NEW_PAYPAL_CLIENT_ID"
update_or_create_secret "aif369-paypal-secret"     "$NEW_PAYPAL_SECRET"

# ------------------------------------------------------------
# PASO 6: Deshabilitar versiones antiguas (las comprometidas)
# ------------------------------------------------------------
echo ""
echo "🔒  Deshabilitando versiones anteriores comprometidas..."
for SECRET in aif369-gemini-api-key aif369-smtp-password aif369-content-api-key aif369-paypal-client-id aif369-paypal-secret; do
  VERSIONS=$(gcloud secrets versions list "$SECRET" --project="$PROJECT" \
    --filter="state=ENABLED" --format="value(name)" 2>/dev/null | sort -t/ -k2 -n | head -n -1)
  for V in $VERSIONS; do
    gcloud secrets versions disable "$V" --secret="$SECRET" --project="$PROJECT" --quiet
    echo "   🔒  $SECRET versión $V deshabilitada"
  done
done

# ------------------------------------------------------------
# PASO 7: Eliminar revisiones antiguas de Cloud Run con claves planas
# ------------------------------------------------------------
echo ""
echo "🗑️   Eliminando revisiones antiguas de Cloud Run (con claves en plaintext)..."
for SERVICE in aif369-backend aif369-backend-qa aif369-backend-dev; do
  echo "   Servicio: $SERVICE"
  CURRENT=$(gcloud run services describe "$SERVICE" \
    --region="$REGION" --project="$PROJECT" \
    --format="value(status.latestReadyRevisionName)" 2>/dev/null || true)

  if [ -z "$CURRENT" ]; then
    echo "   ⚠️   $SERVICE no encontrado, saltando."
    continue
  fi

  REVISIONS=$(gcloud run revisions list \
    --service="$SERVICE" --region="$REGION" --project="$PROJECT" \
    --format="value(metadata.name)" 2>/dev/null | grep -v "^$CURRENT$" || true)

  for REV in $REVISIONS; do
    gcloud run revisions delete "$REV" \
      --region="$REGION" --project="$PROJECT" --quiet 2>/dev/null && \
      echo "   🗑️   Eliminada: $REV" || true
  done
done

# ------------------------------------------------------------
# PASO 8: Actualizar .env local con nuevas claves
# ------------------------------------------------------------
echo ""
echo "📝  Actualizando backend/.env local..."
cat > "$(dirname "$0")/../backend/.env" <<EOF
# AIF369 Backend — Local Development Environment
# Este archivo está en .gitignore. NUNCA commitear.

# GCP Project
PROJECT_ID=aif369-backend
DATASET_ID=aif369_analytics
ENVIRONMENT=dev

# SMTP (Zoho Mail)
SMTP_USER=edaza@aif369.com
NOTIFICATION_EMAIL=edaza@aif369.com
CC_EMAIL=erwin.daza@gmail.com

# Ollama fallback
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral:7b

# Secrets — en producción vienen de GCP Secret Manager
GEMINI_API_KEY=$NEW_GEMINI_KEY
SMTP_PASSWORD=$NEW_SMTP_PASS
CONTENT_API_KEY=$NEW_CONTENT_KEY
PAYPAL_CLIENT_ID=$NEW_PAYPAL_CLIENT_ID
PAYPAL_SECRET=$NEW_PAYPAL_SECRET
EOF
echo "   ✅  backend/.env actualizado"

# ------------------------------------------------------------
# PASO 9: Forzar redeploy de Cloud Run para cargar nuevos secrets
# ------------------------------------------------------------
echo ""
echo "🚀  Forzando redeploy de Cloud Run en todos los ambientes..."
for SERVICE in aif369-backend aif369-backend-qa aif369-backend-dev; do
  IMAGE=$(gcloud run services describe "$SERVICE" \
    --region="$REGION" --project="$PROJECT" \
    --format="value(spec.template.spec.containers[0].image)" 2>/dev/null || true)
  if [ -n "$IMAGE" ]; then
    gcloud run services update "$SERVICE" \
      --region="$REGION" --project="$PROJECT" \
      --image="$IMAGE" --quiet && \
      echo "   ✅  $SERVICE redesplegado"
  fi
done

echo ""
echo "========================================================"
echo " ✅  ROTACIÓN COMPLETA"
echo ""
echo " Próximos pasos manuales:"
echo " 1. Responde el correo de Google con evidencia de rotación"
echo " 2. Solicita la reactivación en: https://console.cloud.google.com/support"
echo " 3. Ejecuta los pipelines de CI para redesplegar con Terraform"
echo "========================================================"
