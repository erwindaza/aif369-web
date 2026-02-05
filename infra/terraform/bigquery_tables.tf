# Tabla para almacenar los formularios de contacto
resource "google_bigquery_table" "contact_form" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  table_id   = "contact_form_submissions"
  project    = var.project_id

  schema = jsonencode([
    {
      name        = "submission_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "ID único de la submisión"
    },
    {
      name        = "timestamp"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Fecha y hora de la submisión"
    },
    {
      name        = "name"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Nombre del contacto"
    },
    {
      name        = "email"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Email del contacto"
    },
    {
      name        = "company"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Empresa del contacto"
    },
    {
      name        = "message"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Mensaje del contacto"
    },
    {
      name        = "source_page"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Página desde donde se envió el formulario"
    },
    {
      name        = "user_agent"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "User agent del navegador"
    },
    {
      name        = "ip_address"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "IP del usuario (opcional)"
    },
    {
      name        = "form_type"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Tipo de formulario: contact, education, etc"
    },
    {
      name        = "interest"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Área de interés (para formulario de educación)"
    },
    {
      name        = "team_size"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Tamaño del equipo (para formulario de educación)"
    }
  ])

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["email", "timestamp"]

  labels = {
    environment = var.environment
    app         = "aif369-web"
  }
}
