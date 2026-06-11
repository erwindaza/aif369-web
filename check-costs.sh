#!/bin/bash
# ============================================================
# AIF369 - GCP Cost Report (Enhanced v2)
# Muestra estado de servicios, uso real y costos del proyecto.
# Consulta: Cloud Run, BigQuery, Storage, Secrets, Billing.
#
# Uso: ./check-costs.sh [--month YYYY-MM]
# ============================================================

export CLOUDSDK_CONFIG=~/.gcloud-aif369
PROJECT="aif369-backend"
BILLING_ACCOUNT="0174A7-3C06E7-A99F49"
BILLING_DATASET="billing_export"
BILLING_TABLE="gcp_billing_export_v1_0174A7_3C06E7_A99F49"
BUDGET_USD=10

# Parse month argument
CURRENT_MONTH=$(date '+%Y-%m')
MONTH="${1:-$CURRENT_MONTH}"
if [[ "$1" == "--month" ]]; then
    MONTH="${2:-$CURRENT_MONTH}"
fi
INVOICE_MONTH=$(echo "$MONTH" | tr -d '-')

echo "======================================"
echo "  AIF369 - GCP Cost Report v2"
echo "  Período: $MONTH"
echo "  $(date '+%Y-%m-%d %H:%M')"
echo "======================================"
echo ""

# ─── 1. Cloud Run Services ───
echo "🔧 CLOUD RUN SERVICES"
echo "--------------------------------------"
gcloud run services list \
  --region=us-central1 \
  --project="$PROJECT" \
  --format='table(SERVICE, REGION, LAST_DEPLOYED_AT, URL)' 2>/dev/null
echo ""

# ─── 2. Request Counts (24h) ───
echo "📈 REQUESTS (últimas 24h)"
echo "--------------------------------------"
YESTERDAY=$(date -u -v-1d '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u -d '1 day ago' '+%Y-%m-%dT%H:%M:%SZ')
for svc in aif369-backend-api aif369-backend-api-dev aif369-backend-api-qa; do
  count=$(gcloud logging read \
    "resource.type=cloud_run_revision AND resource.labels.service_name=$svc AND httpRequest.requestMethod!='' AND timestamp>=\"$YESTERDAY\"" \
    --project="$PROJECT" \
    --format='value(httpRequest.requestMethod)' \
    --limit=10000 --freshness=1d 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$count" -gt 0 ]]; then
    echo "  $svc: $count requests"
  fi
done
echo ""

# ─── 3. BigQuery Usage ───
echo "📊 BIGQUERY USAGE"
echo "--------------------------------------"
for ds in aif369_analytics aif369_analytics_dev billing_export; do
  size=$(bq --project_id="$PROJECT" show --format=json "$ds" 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    tables=int(d.get('numTables',0) or 0)
    bytes_=int(d.get('numBytes',0) or 0)
    mb=bytes_/(1024*1024)
    print(f'{tables} tables, {mb:.2f} MB')
except: print('N/A')
" 2>/dev/null)
  echo "  $ds: $size"
done
echo ""

# ─── 4. Storage Buckets ───
echo "🪣 STORAGE BUCKETS"
echo "--------------------------------------"
gsutil ls -p "$PROJECT" 2>/dev/null | while read bucket; do
  size=$(gsutil du -s "$bucket" 2>/dev/null | awk '{
    bytes=$1
    if (bytes > 1073741824) printf "%.2f GB", bytes/1073741824
    else if (bytes > 1048576) printf "%.2f MB", bytes/1048576
    else if (bytes > 1024) printf "%.2f KB", bytes/1024
    else printf "%d B", bytes
  }')
  name=$(echo "$bucket" | sed 's/gs:\/\///' | sed 's/\///')
  echo "  $name: ${size:-empty}"
done
echo ""

# ─── 5. Secrets ───
echo "🔑 SECRETS"
echo "--------------------------------------"
gcloud secrets list --project="$PROJECT" --format='value(name)' 2>/dev/null | while read s; do
  versions=$(gcloud secrets versions list "$s" --project="$PROJECT" --format='value(name)' 2>/dev/null | wc -l | tr -d ' ')
  echo "  • $s ($versions versions)"
done
echo ""

# ─── 6. Container Images ───
echo "📦 CONTAINER IMAGES"
echo "--------------------------------------"
gcloud container images list --repository="gcr.io/$PROJECT" --format='value(NAME)' 2>/dev/null | while read img; do
  tags=$(gcloud container images list-tags "$img" --format='value(tags)' --limit=10 2>/dev/null | wc -l | tr -d ' ')
  echo "  $img ($tags tags)"
done
echo ""

# ─── 7. REAL COSTS (BigQuery Billing Export) ───
echo "======================================"
echo "  💰 COSTOS REALES - $MONTH"
echo "--------------------------------------"

# Check if billing export table exists
TABLE_EXISTS=$(bq --project_id="$PROJECT" show "$BILLING_DATASET.$BILLING_TABLE" 2>/dev/null && echo "yes" || echo "no")

if [[ "$TABLE_EXISTS" == "yes" ]]; then
  echo ""
  echo "  📊 Desglose por Servicio:"
  echo ""
  bq --project_id="$PROJECT" query --use_legacy_sql=false --format=pretty \
    "SELECT
       service.description AS Servicio,
       ROUND(SUM(cost), 4) AS Costo_USD,
       ROUND(SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 4) AS Creditos,
       ROUND(SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 4) AS Neto_USD
     FROM \`$PROJECT.$BILLING_DATASET.$BILLING_TABLE\`
     WHERE invoice.month = '$INVOICE_MONTH'
       AND project.id = '$PROJECT'
     GROUP BY 1
     ORDER BY Neto_USD DESC" 2>/dev/null

  echo ""
  echo "  📈 Resumen del Mes:"
  echo ""
  bq --project_id="$PROJECT" query --use_legacy_sql=false --format=pretty \
    "SELECT
       ROUND(SUM(cost), 4) AS Total_Bruto_USD,
       ROUND(SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 4) AS Total_Creditos,
       ROUND(SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 4) AS Total_Neto_USD,
       COUNT(DISTINCT service.description) AS Num_Servicios,
       COUNT(DISTINCT DATE(usage_start_time)) AS Dias_Activos,
       MAX(DATE(usage_start_time)) AS Ultimo_Dia
     FROM \`$PROJECT.$BILLING_DATASET.$BILLING_TABLE\`
     WHERE invoice.month = '$INVOICE_MONTH'
       AND project.id = '$PROJECT'" 2>/dev/null

  echo ""

  # Calculate budget usage
  TOTAL=$(bq --project_id="$PROJECT" query --use_legacy_sql=false --format=csv \
    "SELECT ROUND(SUM(cost) + SUM(IFNULL((SELECT SUM(c.amount) FROM UNNEST(credits) c), 0)), 4)
     FROM \`$PROJECT.$BILLING_DATASET.$BILLING_TABLE\`
     WHERE invoice.month = '$INVOICE_MONTH'
       AND project.id = '$PROJECT'" 2>/dev/null | tail -1)
  
  if [[ -n "$TOTAL" && "$TOTAL" != "null" ]]; then
    PCT=$(python3 -c "print(f'{float(${TOTAL:-0}) / $BUDGET_USD * 100:.1f}')" 2>/dev/null || echo "?")
    echo "  ─────────────────────────────"
    echo "  Total:        USD $TOTAL"
    echo "  Presupuesto:  USD $BUDGET_USD"
    echo "  Uso:          $PCT%"
    
    # Status indicator
    if (( $(echo "$PCT > 100" | bc -l 2>/dev/null || echo 0) )); then
      echo "  Estado:       ⚠️  SUPERADO"
    elif (( $(echo "$PCT > 80" | bc -l 2>/dev/null || echo 0) )); then
      echo "  Estado:       ⚡ PRECAUCIÓN"
    else
      echo "  Estado:       ✅ OK"
    fi
  fi

else
  echo ""
  echo "  ⚠️  Billing Export NO configurado."
  echo "  Los datos mostrados son ESTIMACIONES."
  echo ""
  echo "  Para habilitar datos reales:"
  echo "  1. terraform apply (crea dataset)"
  echo "  2. Console → Billing → Billing Export → BigQuery"
  echo "  3. Seleccionar dataset: billing_export"
  echo "  4. Esperar ~24h para datos"
  echo ""
  echo "  ── ESTIMACIÓN (Free Tier) ──"
  echo "  Cloud Run:    \$0.00 (free tier: 2M req/mes)"
  echo "  BigQuery:     \$0.00 (free tier: 1TB + 10GB)"
  echo "  Storage:      ~\$0.02"
  echo "  Secrets:      \$0.00 (free tier: 6 secrets)"
  echo "  GCR/Artifact: ~\$0.10"
  echo "  Cloud Build:  \$0.00 (120 min/day free)"
  echo "  Gemini API:   ~\$0.50 (según uso)"
  echo "  Logging:      \$0.00 (50GB free)"
  echo "  ─────────────────────────────"
  echo "  TOTAL EST:    < USD 1/mes"
fi

echo ""
echo "  Presupuesto:  USD $BUDGET_USD/mes"
echo "  Alertas:      50%, 80%, 100%"
echo "  Dashboard:    https://aif369.com/cost-dashboard.html"
echo "  Console:      https://console.cloud.google.com/billing?project=$PROJECT"
echo "======================================"
