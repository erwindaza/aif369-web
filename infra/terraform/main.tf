locals {
  name_prefix = "aif369-${var.environment}"
  buckets = {
    raw       = "${local.name_prefix}-raw"
    processed = "${local.name_prefix}-processed"
    assets    = "${local.name_prefix}-assets"
  }
}

resource "google_project_service" "services" {
  for_each = toset([
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com"
  ])

  project                    = var.project_id
  service                    = each.key
  disable_dependent_services = false
  disable_on_destroy         = false
}

resource "google_storage_bucket" "buckets" {
  for_each = local.buckets

  name                        = each.value
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  depends_on = [google_project_service.services]
}

resource "google_bigquery_dataset" "analytics" {
  dataset_id    = var.dataset_id
  friendly_name = "AIF369 Analytics (${var.environment})"
  description   = "Dataset de eventos y formularios – entorno ${var.environment}."
  location      = var.location
  project       = var.project_id

  labels = {
    environment = var.environment
    app         = "aif369-web"
  }

  depends_on = [google_project_service.services]
}

resource "google_service_account" "backend" {
  account_id   = "aif369-backend-sa"
  display_name = "AIF369 Backend Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "backend_bq" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.backend.email}"
}
