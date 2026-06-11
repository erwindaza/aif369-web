output "service_account_email" {
  description = "Backend service account email"
  value       = google_service_account.backend.email
}

output "bucket_names" {
  description = "GCS bucket names"
  value       = { for k, v in google_storage_bucket.buckets : k => v.name }
}

output "bigquery_dataset" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.analytics.dataset_id
}

output "billing_budget_name" {
  description = "Billing budget resource name"
  value       = google_billing_budget.monthly.display_name
}

output "billing_alert_email" {
  description = "Email receiving billing alerts"
  value       = var.alert_email
}
