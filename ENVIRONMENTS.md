# AIF369 Multi-Environment Setup

## Estructura de Ramas

### `main` (Producción)
- **Frontend**: https://aif369.com (Vercel deployment automático)
- **Backend**: https://aif369-backend-api-830685315001.us-central1.run.app
- **BigQuery Dataset**: `aif369_analytics`
- **Terraform Config**: `infra/terraform/terraform.tfvars` → `environment = "production"`

### `dev` (Desarrollo)
- **Frontend**: https://aif369-web.vercel.app (Vercel preview automático)
- **Backend**: https://aif369-backend-api-dev-830685315001.us-central1.run.app (por crear)
- **BigQuery Dataset**: `aif369_analytics_dev` (por crear)
- **Terraform Config**: `infra/terraform/terraform.tfvars` → `environment = "dev"`

## Flujo de Trabajo

### Trabajando en Development
```bash
# Cambiar a rama dev
git checkout dev

# Verificar configuración
cat infra/terraform/terraform.tfvars
# Debe mostrar: environment = "dev"

# Hacer cambios y probar
# ... commits ...

# Desplegar backend dev (cuando esté configurado)
cd backend
gcloud run deploy aif369-backend-api-dev \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --project aif369-backend \
  --set-env-vars "SMTP_USERNAME=edaza@aif369.com,SMTP_PASSWORD=CK8rvsq7HSSw,SMTP_FROM=edaza@aif369.com,NOTIFICATION_EMAIL=erwin.daza@gmail.com"

# Push a dev (trigger Vercel preview)
git push origin dev
```

### Promover a Producción
```bash
# Cambiar a main
git checkout main

# Merge desde dev
git merge dev

# Verificar configuración
cat infra/terraform/terraform.tfvars
# Debe mostrar: environment = "production"

# Desplegar backend prod
cd backend
gcloud run deploy aif369-backend-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --project aif369-backend \
  --set-env-vars "SMTP_USERNAME=edaza@aif369.com,SMTP_PASSWORD=CK8rvsq7HSSw,SMTP_FROM=edaza@aif369.com,NOTIFICATION_EMAIL=erwin.daza@gmail.com"

# Push a main (trigger Vercel production)
git push origin main
```

## Detección Automática de Entorno

El archivo `scripts.js` detecta automáticamente el entorno basándose en el hostname:

```javascript
const isProduction = window.location.hostname === 'aif369.com' 
    || window.location.hostname === 'www.aif369.com';
    
const BACKEND_URL = isProduction 
    ? 'https://aif369-backend-api-830685315001.us-central1.run.app'
    : 'https://aif369-backend-api-dev-830685315001.us-central1.run.app';
```

- **Producción**: `aif369.com` → backend prod
- **Dev/Preview**: `aif369-web.vercel.app` o `*.vercel.app` → backend dev

## Terraform por Entorno

### Aplicar cambios en DEV
```bash
cd infra/terraform
terraform init
terraform plan   # usa terraform.tfvars de rama dev
terraform apply
```

### Aplicar cambios en PROD
```bash
git checkout main
cd infra/terraform
terraform init
terraform plan   # usa terraform.tfvars de rama main
terraform apply
```

### Usar archivos específicos (alternativa)
```bash
# Prod
terraform apply -var-file="terraform.tfvars.production"

# Dev
terraform apply -var-file="terraform.tfvars.dev"
```

## Pendientes para Completar Setup Dev

1. **Crear Cloud Run Dev**:
   ```bash
   cd backend
   gcloud run deploy aif369-backend-api-dev \
     --source . \
     --region us-central1 \
     --project aif369-backend
   ```

2. **Crear BigQuery Dataset Dev**:
   ```bash
   # Actualizar infra/terraform con condicional para dataset_id según environment
   # O crear manualmente:
   bq mk --dataset --location=us-central1 aif369-backend:aif369_analytics_dev
   ```

3. **Configurar CI/CD en GitHub Actions** (opcional):
   - Auto-deploy backend dev cuando se push a `dev`
   - Auto-deploy backend prod cuando se push a `main`

## Formularios Disponibles

### 1. Formulario de Contacto (`/api/contact`)
- Ubicación: `index.html#contacto`
- Campos: name, email, company, message
- Storage: BigQuery `contact_form_submissions` con `form_type = null` o ausente

### 2. Formulario de Educación (`/api/education`)
- Ubicación: `education.html#contacto-educacion`
- Campos: name, email, company, interest, team_size, message
- Storage: BigQuery `contact_form_submissions` con `form_type = "education"`

Ambos formularios envían:
- Email de notificación a `erwin.daza@gmail.com`
- Email de confirmación al cliente

## Variables de Entorno del Backend

Requeridas en Cloud Run:
- `SMTP_USERNAME`: edaza@aif369.com
- `SMTP_PASSWORD`: [App-specific password de Zoho]
- `SMTP_FROM`: edaza@aif369.com
- `NOTIFICATION_EMAIL`: erwin.daza@gmail.com
- `PROJECT_ID`: aif369-backend (auto-detectado)

## Troubleshooting

### Frontend muestra código viejo
```bash
# Hard refresh en el navegador
Cmd + Shift + R (Mac)
Ctrl + Shift + R (Windows/Linux)

# O forzar redeploy en Vercel
git commit --allow-empty -m "chore: force redeploy"
git push
```

### Backend no recibe requests
```bash
# Verificar logs
gcloud run services logs read aif369-backend-api --project=aif369-backend --region=us-central1

# Verificar que el servicio está up
gcloud run services describe aif369-backend-api --project=aif369-backend --region=us-central1
```

### Emails no llegan
- Verificar variables de entorno en Cloud Run
- Revisar logs del backend para errores SMTP
- Confirmar que la app-specific password de Zoho es válida
