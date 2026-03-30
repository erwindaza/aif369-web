# ── Billing Budget & Alerts ──────────────────────────────────────
# Presupuesto mensual con alertas por email al 50%, 80% y 100%.
# Las alertas llegan al email configurado en var.alert_email.
# Budget existente importado: billingAccounts/0174A7-3C06E7-A99F49/budgets/7c3d7908-f869-45af-856d-72d5d5b4b95a

data "google_project" "current" {
  project_id = var.project_id
}

resource "google_billing_budget" "monthly" {
  billing_account = var.billing_account_id
  display_name    = "AIF369 Monthly Budget"

  budget_filter {
    projects               = ["projects/${data.google_project.current.number}"]
    calendar_period        = "MONTH"
    credit_types_treatment = "INCLUDE_ALL_CREDITS"
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.monthly_budget_usd)
    }
  }

  # Alerta al 50%
  threshold_rules {
    threshold_percent = 0.5
    spend_basis       = "CURRENT_SPEND"
  }

  # Alerta al 80%
  threshold_rules {
    threshold_percent = 0.8
    spend_basis       = "CURRENT_SPEND"
  }

  # Alerta al 100%
  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "CURRENT_SPEND"
  }

  all_updates_rule {
    monitoring_notification_channels = [
      google_monitoring_notification_channel.email.id
    ]
    disable_default_iam_recipients = false
  }

  depends_on = [google_project_service.services]
}

resource "google_monitoring_notification_channel" "email" {
  project      = var.project_id
  display_name = "Billing Alerts - ${var.alert_email}"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }

  depends_on = [google_project_service.services]
}
