#!/bin/bash
# ============================================================
# AIF369 - GCP Cost Report (fast version)
# Muestra estado de servicios y uso del proyecto
# Uso: ./check-costs.sh
# ============================================================

export CLOUDSDK_CONFIG=~/.gcloud-aif369
PROJECT="aif369-backend"

echo "======================================"
echo "  AIF369 - GCP Cost Report"
echo "  $(date '+%Y-%m-%d %H:%M')"
echo "======================================"
echo ""

# 1. Cloud Run services
echo "🔧 CLOUD RUN SERVICES"
echo "--------------------------------------"
gcloud run services list \
  --region=us-central1 \
  --project="$PROJECT" \
  --format='table(SERVICE, LAST_DEPLOYED_AT)' 2>/dev/null
echo ""

# 2. Request counts last 24h
echo "📈 REQUESTS (últimas 24h)"
echo "--------------------------------------"
YESTERDAY=$(date -u -v-1d '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -d '1 day ago' '+%Y-%m-%dT%H:%M:%SZ')
for svc in aif369-backend-api aif369-backend-api-dev; do
  count=$(gcloud logging read \
    "resource.type=cloud_run_revision AND resource.labels.service_name=$svc AND httpRequest.requestMethod!='' AND timestamp>=\"$YESTERDAY\"" \
    --project="$PROJECT" \
    --format='value(httpRequest.requestMethod)' \
    --limit=10000 --freshness=1d 2>/dev/null | wc -l | tr -d ' ')
  echo "  $svc: $count requests"
done
echo ""

# 3. Secrets count
echo "🔑 SECRETS"
echo "--------------------------------------"
gcloud secrets list --project="$PROJECT" --format='value(name)' 2>/dev/null | while read s; do echo "  • $s"; done
echo ""

# 4. Container images
echo "📦 CONTAINER IMAGES"
echo "--------------------------------------"
gcloud container images list --repository="gcr.io/$PROJECT" --format='value(NAME)' 2>/dev/null | while read img; do
  tags=$(gcloud container images list-tags "$img" --format='value(tags)' --limit=5 2>/dev/null | wc -l | tr -d ' ')
  echo "  $img ($tags tags)"
done
echo ""

# 5. Cost estimate
echo "======================================"
echo "  💰 ESTIMACIÓN MENSUAL"
echo "--------------------------------------"
echo "  Cloud Run:    \$0 (free tier: 2M req/mes)"
echo "  BigQuery:     \$0 (free tier: 1TB + 10GB)"
echo "  Secrets:      \$0 (free tier: 6 secrets)"
echo "  Gemini API:   ~\$0.01-0.50 según uso"
echo "  GCR Storage:  ~\$0.10-0.50"
echo "  ─────────────────────────────"
echo "  TOTAL EST:    < USD 5/mes"
echo ""
echo "  Presupuesto: CLP 10.000/mes"
echo "  Alertas: 50%, 80%, 100%"
echo "  Console: https://console.cloud.google.com/billing?project=$PROJECT"
echo "======================================"
