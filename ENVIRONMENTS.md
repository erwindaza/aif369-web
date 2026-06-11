# AIF369 Multi-Environment Setup

## Arquitectura de Entornos (DevOps)

```
dev ──► qa ──► main (producción)
 │       │       │
 ▼       ▼       ▼
BQ dev  BQ qa   BQ prod
CR dev  CR qa   CR prod
```

**Regla de oro**: nada llega a producción sin pasar antes por QA.

---

## Ramas y Entornos

| Rama   | Entorno    | Cloud Run Service         | BigQuery Dataset       | Frontend               |
|--------|------------|---------------------------|-----------------------|------------------------|
| `dev`  | Desarrollo | `aif369-backend-api-dev`  | `aif369_analytics_dev` | Vercel preview         |
| `qa`   | QA         | `aif369-backend-api-qa`   | `aif369_analytics_qa`  | Vercel preview (qa)    |
| `main` | Producción | `aif369-backend-api`      | `aif369_analytics`     | https://aif369.com     |

---

## Flujo de Trabajo (CI/CD)

### 1. Desarrollo (rama `dev`)
```bash
git checkout dev
# Hacer cambios, commits...
git push origin dev
# → GitHub Action ci-dev.yml:
#   ✅ Lint HTML
#   ✅ Tests backend (pytest)
#   ✅ Terraform validate
#   ✅ Build + deploy a Cloud Run DEV
#   ✅ Terraform apply DEV (si hay cambios en infra/)
```

### 2. Promoción a QA (PR dev → qa)
```bash
# Crear PR desde dev hacia qa en GitHub
# Revisar cambios, aprobar PR
# Al hacer merge → GitHub Action deploy-qa.yml:
#   ✅ Tests backend (QA gate)
#   ✅ Terraform apply QA (crea dataset + tablas en QA)
#   ✅ Build + deploy a Cloud Run QA
#   ✅ Health check QA
```

### 3. Promoción a Producción (PR qa → main)
```bash
# Crear PR desde qa hacia main en GitHub
# Solo después de validar en QA
# Al hacer merge → GitHub Action deploy-production.yml:
#   ✅ Tests backend (production gate)
#   ✅ Terraform apply PRODUCTION
#   ✅ Build + deploy a Cloud Run PROD
#   ✅ Health check PROD
#   ✅ Vercel auto-deploy frontend
```

---

## Terraform por Entorno

Cada entorno usa su propio archivo `.tfvars`:

| Archivo                      | Entorno    | Dataset                | Service Name              |
|------------------------------|------------|------------------------|---------------------------|
| `terraform.tfvars.dev`       | dev        | `aif369_analytics_dev` | `aif369-backend-api-dev`  |
| `terraform.tfvars.qa`        | qa         | `aif369_analytics_qa`  | `aif369-backend-api-qa`   |
| `terraform.tfvars.production`| production | `aif369_analytics`     | `aif369-backend-api`      |

### Aplicar manualmente (si necesario):
```bash
cd infra/terraform
terraform init

# DEV
terraform plan -var-file=terraform.tfvars.dev
terraform apply -var-file=terraform.tfvars.dev

# QA
terraform plan -var-file=terraform.tfvars.qa
terraform apply -var-file=terraform.tfvars.qa

# PRODUCCIÓN
terraform plan -var-file=terraform.tfvars.production
terraform apply -var-file=terraform.tfvars.production
```

---

## Variables de Entorno del Backend

Configuradas automáticamente por GitHub Actions en cada Cloud Run:

| Variable           | Valor                          |
|--------------------|--------------------------------|
| `PROJECT_ID`       | `aif369-backend`               |
| `DATASET_ID`       | Según entorno (ver tabla)      |
| `ENVIRONMENT`      | `dev` / `qa` / `production`    |
| `SMTP_USER`        | `edaza@aif369.com`             |
| `SMTP_PASSWORD`    | Secret Manager                 |
| `GEMINI_API_KEY`   | Secret Manager                 |
| `NOTIFICATION_EMAIL` | `edaza@aif369.com`           |
| `CC_EMAIL`         | `erwin.daza@gmail.com`         |

---

## BigQuery: Tablas por Entorno

Cada dataset contiene las mismas tablas:

1. **`contact_form_submissions`** — Formularios de contacto y educación
2. **`chat_conversations`** — Conversaciones del chat widget

Terraform crea ambas tablas automáticamente al hacer `apply` por entorno.

---

## GitHub Actions (Workflows)

| Workflow              | Trigger          | Qué hace                                    |
|-----------------------|------------------|----------------------------------------------|
| `ci-dev.yml`          | push a `dev`     | Tests + deploy DEV + TF apply DEV            |
| `deploy-qa.yml`       | push a `qa`      | Tests + TF apply QA + deploy QA              |
| `deploy-production.yml` | push a `main` | Tests + TF apply PROD + deploy PROD          |

---

## Detección Automática de Entorno (Frontend)

`chat-widget.js` y `scripts.js` detectan automáticamente:

```javascript
const isProd = location.hostname === 'aif369.com' || location.hostname === 'www.aif369.com';
const BASE = isProd
    ? 'https://aif369-backend-api-830685315001.us-central1.run.app'    // PROD
    : 'https://aif369-backend-api-dev-830685315001.us-central1.run.app'; // DEV
```

---

## Secrets de GitHub (requeridos)

Configurar en GitHub → Settings → Secrets and variables → Actions:

- `GCP_SA_KEY` — JSON key de la Service Account con roles:
  - `roles/run.admin`
  - `roles/bigquery.dataEditor`
  - `roles/storage.admin`
  - `roles/iam.serviceAccountUser`
  - `roles/cloudbuild.builds.editor`

---

## Troubleshooting

### Verificar entorno del backend
```bash
curl https://[SERVICE_URL]/ | jq .
# Debe retornar: {"status": "ok", "service": "aif369-backend"}
```

### Ver logs de Cloud Run
```bash
CLOUDSDK_CONFIG=~/.gcloud-aif369 gcloud run services logs read aif369-backend-api-dev --region=us-central1
```

### Verificar tablas BQ por entorno
```bash
echo Y | CLOUDSDK_CONFIG=~/.gcloud-aif369 bq ls --project_id=aif369-backend aif369_analytics_dev
echo Y | CLOUDSDK_CONFIG=~/.gcloud-aif369 bq ls --project_id=aif369-backend aif369_analytics_qa
echo Y | CLOUDSDK_CONFIG=~/.gcloud-aif369 bq ls --project_id=aif369-backend aif369_analytics
```
