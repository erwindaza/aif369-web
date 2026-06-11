# Configuración de Billing Export a BigQuery

## ¿Por qué es necesario?

El billing export de GCP envía automáticamente datos detallados de costos a BigQuery cada ~24 horas. Esto permite:

- **Desglose por servicio**: Cloud Run, BigQuery, Storage, Gemini API, etc.
- **Tendencias diarias**: ver cómo evolucionan los costos día a día
- **Top SKUs**: identificar qué operaciones específicas cuestan más
- **Proyecciones**: estimar el costo mensual basado en el consumo actual
- **Historial**: mantener datos de meses anteriores para comparación

## Pasos de Configuración

### 1. Aplicar Terraform (crea el dataset)

```bash
cd infra/terraform
terraform plan
terraform apply
```

Esto crea el dataset `billing_export` en BigQuery.

### 2. Habilitar Billing Export en GCP Console

1. Ir a: [GCP Console → Billing → Billing Export](https://console.cloud.google.com/billing/exports?project=aif369-backend)
2. Click en **"BigQuery Export"** tab
3. En **"Standard usage cost"**:
   - Click **"Edit Settings"**
   - Project: `aif369-backend`
   - Dataset: `billing_export`
   - Click **"Save"**
4. (Opcional) También habilitar **"Detailed usage cost"** con el mismo dataset

### 3. Esperar datos (~24 horas)

- GCP comienza a enviar datos al dataset dentro de las próximas 24 horas
- La tabla se crea automáticamente con nombre: `gcp_billing_export_v1_0174A7_3C06E7_A99F49`
- Los datos tienen un delay de ~4-6 horas respecto al uso real

### 4. Verificar

```bash
# Verificar que la tabla existe
bq ls billing_export

# Query de prueba
bq query --use_legacy_sql=false \
  "SELECT service.description, SUM(cost) as total 
   FROM \`aif369-backend.billing_export.gcp_billing_export_v1_0174A7_3C06E7_A99F49\`
   WHERE project.id = 'aif369-backend'
   GROUP BY 1 ORDER BY 2 DESC"
```

### 5. Verificar el Dashboard

Una vez que los datos fluyen, el dashboard en `/cost-dashboard.html` mostrará datos reales automáticamente.

El endpoint de health check indica el estado:
```
GET /api/costs/health
```

## Notas

- **Costo del billing export**: ~$0 (BigQuery storage es negligible para billing data)
- **Sin billing export**: el sistema muestra estimaciones estáticas basadas en el free tier
- **Data freshness**: los datos se actualizan cada ~4-6 horas
- **Retención**: datos disponibles indefinidamente en BigQuery

## Schema de la Tabla (auto-generada por GCP)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| billing_account_id | STRING | ID de la cuenta de billing |
| service.id | STRING | ID del servicio GCP |
| service.description | STRING | Nombre del servicio (ej: "Cloud Run") |
| sku.id | STRING | ID del SKU |
| sku.description | STRING | Nombre del SKU (ej: "CPU Allocation Time") |
| usage_start_time | TIMESTAMP | Inicio del uso |
| usage_end_time | TIMESTAMP | Fin del uso |
| project.id | STRING | ID del proyecto |
| cost | FLOAT | Costo bruto |
| currency | STRING | Moneda (CLP o USD) |
| credits | RECORD[] | Créditos aplicados |
| usage.amount | FLOAT | Cantidad de uso |
| usage.unit | STRING | Unidad de uso |
| invoice.month | STRING | Mes de facturación (YYYYMM) |

## Servicios Monitoreados

| Servicio | Free Tier | Estimación AIF369 |
|----------|-----------|-------------------|
| Cloud Run | 2M req/mes, 360K vCPU-sec | ~$0 |
| BigQuery | 1TB queries, 10GB storage | ~$0 |
| Cloud Storage | 5GB | ~$0.02 |
| Secret Manager | 6 versions | ~$0 |
| Artifact Registry | 500MB free | ~$0.10 |
| Cloud Build | 120 min/day | ~$0 |
| Gemini API | Variable | ~$0.50 |
| Cloud Logging | 50GB/month | ~$0 |
| **TOTAL ESTIMADO** | | **< $1/mes** |
