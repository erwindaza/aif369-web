# Cloud Run services for AIF369 Master Program API (dev, qa, production)
# Deploys the multi-agent orchestration system

locals {
  master_environments = {
    dev = {
      service_name   = "aif369-master-api-dev"
      min_instances  = 1
      max_instances  = 5
      memory         = "2Gi"
      cpu            = "2"
      timeout        = 3600
    }
    qa = {
      service_name   = "aif369-master-api-qa"
      min_instances  = 1
      max_instances  = 10
      memory         = "2Gi"
      cpu            = "2"
      timeout        = 3600
    }
    production = {
      service_name   = "aif369-master-api"
      min_instances  = 2
      max_instances  = 20
      memory         = "4Gi"
      cpu            = "4"
      timeout        = 3600
    }
  }
}

resource "google_cloud_run_service" "master_api" {
  for_each = local.master_environments

  name     = each.value.service_name
  location = var.region
  project  = var.project_id

  template {
    spec {
      service_account_name = google_service_account.backend.email
      timeout_seconds      = each.value.timeout

      containers {
        image = "gcr.io/${var.project_id}/aif369-master-api-${each.key}:latest"

        ports {
          container_port = 8000  # FastAPI default
        }

        resources {
          limits = {
            cpu    = each.value.cpu
            memory = each.value.memory
          }
        }

        # Environment variables
        env {
          name  = "ENVIRONMENT"
          value = each.key
        }

        env {
          name  = "PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "LOG_LEVEL"
          value = each.key == "production" ? "INFO" : "DEBUG"
        }

        env {
          name  = "OLLAMA_HOST"
          value = "http://localhost:11434"
        }

        # Database connection
        env {
          name = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = "aif369-master-db-url-${each.key}"
              key  = "latest"
            }
          }
        }

        # Secrets from GCP Secret Manager
        env {
          name = "MASTER_API_KEY"
          value_from {
            secret_key_ref {
              name = "aif369-master-api-key-${each.key}"
              key  = "latest"
            }
          }
        }

        # Allow local Ollama connection
        env {
          name  = "OLLAMA_TIMEOUT"
          value = "300"
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = each.value.min_instances
        "autoscaling.knative.dev/maxScale" = each.value.max_instances
        "run.googleapis.com/cpu-throttling-after-init" = "false"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  lifecycle {
    ignore_changes = [
      template[0].metadata[0].generation,
      template[0].metadata[0].labels,
    ]
  }

  depends_on = [google_project_service.services]
}

# Public access for Master API (no auth required for demo)
resource "google_cloud_run_service_iam_member" "master_api_public" {
  for_each = local.master_environments

  service  = google_cloud_run_service.master_api[each.key].name
  location = google_cloud_run_service.master_api[each.key].location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Output Master API URLs
output "master_api_urls" {
  value = {
    for env, service in google_cloud_run_service.master_api :
    env => service.status[0].url
  }
  description = "URLs for Master API services by environment"
}

output "master_api_health_checks" {
  value = {
    for env, service in google_cloud_run_service.master_api :
    env => "${service.status[0].url}/api/master/health"
  }
  description = "Health check endpoints for Master API"
}
