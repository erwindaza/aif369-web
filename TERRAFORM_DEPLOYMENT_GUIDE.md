# Terraform Deployment Guide — AIF369 Backend

Desde ahora, todos los deploys de infraestructura van por **Terraform**, no por comandos `gcloud run deploy` manuales.

## 📋 Quick Reference

### 1️⃣ Después de cambios en el código backend
```bash
# Rebuild Docker image para linux/amd64
cd backend/
docker buildx build --platform linux/amd64 -t gcr.io/aif369-backend/aif369-backend:latest --push .

# Luego notifica a Terraform que hay una nueva imagen
cd ../infra/terraform/
```

### 2️⃣ Deploy a DEV
```bash
cd infra/terraform/
terraform plan -var-file=terraform.tfvars -target="google_cloud_run_service.backend[\"dev\"]"
terraform apply -var-file=terraform.tfvars -target="google_cloud_run_service.backend[\"dev\"]"
```

### 3️⃣ Deploy a QA (después de testing en dev)
```bash
cd infra/terraform/
terraform plan -var-file=terraform.tfvars -target="google_cloud_run_service.backend[\"qa\"]"
terraform apply -var-file=terraform.tfvars -target="google_cloud_run_service.backend[\"qa\"]"
```

### 4️⃣ Deploy a PROD (después de testing en qa)
```bash
cd infra/terraform/
terraform plan -var-file=terraform.tfvars -target="google_cloud_run_service.backend[\"production\"]"
terraform apply -var-file=terraform.tfvars -target="google_cloud_run_service.backend[\"production\"]"
```

### 5️⃣ Deploy todos los ambientes a la vez (CUIDADO)
```bash
cd infra/terraform/
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

## 🔧 Estructura Terraform

### Variables
- **environments**: Map con configuración de cada ambiente (service_name, dataset_id, min/max instances)
  - dev: `aif369-backend-api-dev` (2 máx instancias)
  - qa: `aif369-backend-api-qa` (2 máx instancias)
  - production: `aif369-backend-api` (3 máx instancias)

### Recursos generados
- `google_cloud_run_service.backend[\"dev\"]`
- `google_cloud_run_service.backend[\"qa\"]`
- `google_cloud_run_service.backend[\"production\"]`
- IAM policies para acceso público en cada uno

### Outputs
```bash
terraform output backend_urls
# Output:
# backend_urls = {
#   "dev" = "https://aif369-backend-api-dev-830685315001.us-central1.run.app"
#   "qa" = "https://aif369-backend-api-qa-830685315001.us-central1.run.app"
#   "production" = "https://aif369-backend-api-830685315001.us-central1.run.app"
# }
```

## 📝 Qué cambiar si necesitas...

### Cambiar límites de memoria/CPU
Edita [cloud_run.tf](cloud_run.tf) línea ~73:
```terraform
resources {
  limits = {
    cpu    = "2"    # Cambiar aquí
    memory = "1Gi"  # Cambiar aquí
  }
}
```

### Cambiar autoscaling (max instances)
Edita [terraform.tfvars](terraform.tfvars) en el mapa `environments`:
```terraform
production = {
  service_name  = "aif369-backend-api"
  dataset_id    = "aif369_analytics"
  min_instances = 0
  max_instances = 5  # Cambiar aquí
}
```

### Agregar un nuevo secret/environment variable
Edita [cloud_run.tf](cloud_run.tf) y agrega:
```terraform
env {
  name = "MY_NEW_VAR"
  value_from {
    secret_key_ref {
      name = "my-secret-in-secret-manager"
      key  = "latest"
    }
  }
}
```

## ✅ Checklist: Push to Production

- [ ] Backend code está committeado
- [ ] Docker image rebuildeada: `docker buildx build --platform linux/amd64 -t gcr.io/aif369-backend/aif369-backend:latest --push backend/`
- [ ] Pushear cambios en código frontend (HTML, JS) a main branch
- [ ] Tests en DEV pasados: `pytest tests/ -v --deployed-url=https://aif369-backend-api-dev-...`
- [ ] Tests en QA pasados: `pytest tests/ -v --deployed-url=https://aif369-backend-api-qa-...`
- [ ] Terraform plan en PROD revisado: sin cambios inesperados
- [ ] Terraform apply a PROD con confianza

## 🚨 Troubleshooting

### "Caller does not have required permission"
- Este error ocurre a veces. Espera 5 minutos y reintenta.

### "Service already exists"
- Los servicios ya existen en GCP. Terraform los va a "adoptar" (importar al state).
- Ejecuta: `terraform import google_cloud_run_service.backend[\"dev\"] aif369-backend-api-dev` (si es necesario)

### ¿Cómo ver el estado actual?
```bash
terraform state show 'google_cloud_run_service.backend["production"]'
```

### ¿Cómo destruir un servicio?
```bash
terraform destroy -target="google_cloud_run_service.backend[\"dev\"]"
```

## 📚 Documentación base
- [Terraform Google Cloud Run](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_service)
- [Terraform for_each Documentation](https://www.terraform.io/language/meta-arguments/for_each)
