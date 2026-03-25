variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "Primary region"
  type        = string
  default     = "us-central1"
}

variable "location" {
  description = "BigQuery location"
  type        = string
  default     = "US"
}

variable "environment" {
  description = "Environment name (dev/qa/production)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "qa", "production"], var.environment)
    error_message = "Environment must be one of: dev, qa, production."
  }
}

variable "dataset_id" {
  description = "BigQuery dataset ID (varies per environment)"
  type        = string
  default     = "aif369_analytics"
}

variable "cloud_run_service_name" {
  description = "Cloud Run service name (varies per environment)"
  type        = string
  default     = "aif369-backend-api"
}
