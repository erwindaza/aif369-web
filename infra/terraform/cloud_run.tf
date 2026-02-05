# Cloud Run service para el backend de AIF369
resource "google_cloud_run_service" "backend" {
  name     = "aif369-backend-api"
  location = var.region
  project  = var.project_id

  template {
    spec {
      service_account_name = google_service_account.backend.email
      
      containers {
        image = "gcr.io/${var.project_id}/aif369-backend:latest"
        
        ports {
          container_port = 8080
        }
        
        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }
        
        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }
      }
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "10"
        "autoscaling.knative.dev/minScale" = "0"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.services]
}

# Permitir acceso público sin autenticación
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.backend.name
  location = google_cloud_run_service.backend.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Output de la URL del servicio
output "backend_url" {
  value       = google_cloud_run_service.backend.status[0].url
  description = "URL del backend API"
}
