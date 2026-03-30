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
  description = "Environment name (dev/qa/production) - used for BigQuery naming"
  type        = string
  default     = "production"

  validation {
    condition     = contains(["dev", "qa", "production"], var.environment)
    error_message = "Environment must be one of: dev, qa, production."
  }
}

variable "dataset_id" {
  description = "BigQuery dataset ID (for shared analytics)"
  type        = string
  default     = "aif369_analytics"
}

variable "environments" {
  description = "Map of environments to deploy (dev, qa, production)"
  type = map(object({
    service_name = string
    dataset_id   = string
    min_instances = number
    max_instances = number
  }))
  default = {
    dev = {
      service_name  = "aif369-backend-api-dev"
      dataset_id    = "aif369_analytics_dev"
      min_instances = 0
      max_instances = 2
    }
    qa = {
      service_name  = "aif369-backend-api-qa"
      dataset_id    = "aif369_analytics"
      min_instances = 0
      max_instances = 2
    }
    production = {
      service_name  = "aif369-backend-api"
      dataset_id    = "aif369_analytics"
      min_instances = 0
      max_instances = 3
    }
  }
}

# ── Billing & Alerts ────────────────────────────────────────────
variable "billing_account_id" {
  description = "GCP Billing Account ID (format: XXXXXX-XXXXXX-XXXXXX)"
  type        = string
}

variable "alert_email" {
  description = "Email address for billing alerts"
  type        = string
}

variable "monthly_budget_usd" {
  description = "Monthly budget in USD"
  type        = number
  default     = 10
}
