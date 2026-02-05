# Infraestructura Backend AIF369 (GCP + Terraform)

Este módulo levanta la infraestructura mínima para el backend de **aif369.com** en GCP.

## Componentes
- **APIs**: BigQuery, Cloud Storage, Cloud Run, Artifact Registry, Cloud Build, IAM.
- **GCS**: buckets raw / processed / assets.
- **BigQuery**: dataset `aif369_analytics`.
- **Service Account**: `aif369-backend-sa` para el backend.

## Requisitos
- Proyecto GCP creado (ej: `aif369-backend`).
- `gcloud` configurado y Terraform instalado.
- Credenciales para Terraform (Workload Identity en CI o `GOOGLE_APPLICATION_CREDENTIALS` local).

## Variables
- `project_id`: ID del proyecto GCP (ej: `aif369-backend`).
- `region`: región principal (ej: `us-central1`).
- `location`: ubicación para BigQuery (ej: `US`).
- `environment`: `dev` o `prod`.

## Ejecución local
```bash
cd infra/terraform
terraform init
terraform plan -var="project_id=aif369-backend" -var="region=us-central1" -var="location=US" -var="environment=dev"
terraform apply -var="project_id=aif369-backend" -var="region=us-central1" -var="location=US" -var="environment=dev"
```

## CI/CD
El pipeline de GitHub Actions ejecuta `fmt`, `init` y `plan`. Para aplicar en **dev** o **prod** se recomienda usar un workflow manual o un job separado con aprobación.
