project_id  = "aif369-backend"
region      = "us-central1"
environment = "production"
dataset_id  = "aif369_analytics"

# Deploy todos los ambientes (dev, qa, production)
environments = {
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

# Billing Alerts
billing_account_id = "0174A7-3C06E7-A99F49"
alert_email        = "erwin.daza@gmail.com"
monthly_budget_usd = 10
