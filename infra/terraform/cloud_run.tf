# Cloud Run services para el backend de AIF369 (dev, qa, production)
resource "google_cloud_run_service" "backend" {
  for_each = var.environments

  name     = each.value.service_name
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

        env {
          name  = "DATASET_ID"
          value = each.value.dataset_id
        }

        env {
          name  = "ENVIRONMENT"
          value = each.key
        }

        env {
          name  = "BILLING_ACCOUNT_ID"
          value = var.billing_account_id
        }

        env {
          name  = "BILLING_DATASET"
          value = "billing_export"
        }

        env {
          name  = "BUDGET_AMOUNT_USD"
          value = tostring(var.monthly_budget_usd)
        }

        # Secrets from GCP Secret Manager
        env {
          name = "GEMINI_API_KEY"
          value_from {
            secret_key_ref {
              name = "aif369-gemini-api-key"
              key  = "latest"
            }
          }
        }

        env {
          name = "SMTP_PASSWORD"
          value_from {
            secret_key_ref {
              name = "aif369-smtp-password"
              key  = "latest"
            }
          }
        }

        env {
          name = "CONTENT_API_KEY"
          value_from {
            secret_key_ref {
              name = "aif369-content-api-key"
              key  = "latest"
            }
          }
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
        "autoscaling.knative.dev/maxScale" = each.value.max_instances
        "autoscaling.knative.dev/minScale" = each.value.min_instances
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.services]
}

# Permitir acceso público sin autenticación para todos los servicios
resource "google_cloud_run_service_iam_member" "public_access" {
  for_each = var.environments

  service  = google_cloud_run_service.backend[each.key].name
  location = google_cloud_run_service.backend[each.key].location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Output de las URLs de todos los servicios
output "backend_urls" {
  value = {
    for env, config in var.environments :
    env => google_cloud_run_service.backend[env].status[0].url
  }
  description = "URLs de los Cloud Run services por ambiente"
}
