# ── BigQuery Billing Export ───────────────────────────────────────
# Dataset dedicado para recibir el billing export de GCP.
# Una vez creado, habilitar el export desde la Console:
# Console → Billing → Billing Export → BigQuery Export → Enable
#
# Tabla auto-generada por GCP:
#   gcp_billing_export_v1_<BILLING_ACCOUNT_ID_with_underscores>
# ──────────────────────────────────────────────────────────────────

resource "google_bigquery_dataset" "billing_export" {
  dataset_id    = "billing_export"
  friendly_name = "GCP Billing Export"
  description   = "Dataset para recibir el export automático de billing de GCP. No borrar tablas manualmente."
  location      = var.location
  project       = var.project_id

  labels = {
    purpose     = "billing"
    environment = "shared"
    app         = "aif369-cost-monitor"
  }

  # Billing export data se retiene por 365 días
  default_table_expiration_ms = null

  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }

  access {
    role          = "READER"
    user_by_email = google_service_account.backend.email
  }

  depends_on = [google_project_service.services]
}

# ── IAM: Billing viewer para el service account ─────────────────
# Permite al backend leer datos del billing export en BigQuery.
# Nota: roles/bigquery.dataViewer y NOT roles/billing.viewer
# porque billing.viewer requiere acceso a nivel de billing account.

resource "google_project_iam_member" "backend_bq_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# ── Cloud Monitoring viewer para métricas de uso ────────────────
resource "google_project_iam_member" "backend_monitoring_viewer" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# ── Output ──────────────────────────────────────────────────────
output "billing_export_dataset" {
  description = "BigQuery dataset ID for billing export"
  value       = google_bigquery_dataset.billing_export.dataset_id
}

output "billing_export_table_name" {
  description = "Expected billing export table name (after enabling export in Console)"
  value       = "gcp_billing_export_v1_${replace(var.billing_account_id, "-", "_")}"
}
