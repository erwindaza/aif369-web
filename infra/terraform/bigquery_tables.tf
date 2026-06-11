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
      name        = "role"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Cargo o rol del contacto"
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

# ── Tabla: scorecard_submissions ──
# Almacena los resultados completos del AI Readiness Scorecard 369:
# puntaje total, nivel de madurez, métricas por dimensión y respuestas individuales.
resource "google_bigquery_table" "scorecard_submissions" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  table_id   = "scorecard_submissions"
  project    = var.project_id

  schema = jsonencode([
    {
      name        = "submission_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "UUID único de la submisión"
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
      description = "Nombre del participante"
    },
    {
      name        = "email"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Email del participante"
    },
    {
      name        = "company"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Empresa del participante"
    },
    {
      name        = "role"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Cargo o rol del participante"
    },
    {
      name        = "total_score"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Puntaje total del scorecard (0-100)"
    },
    {
      name        = "maturity_level"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Nivel de madurez (Inicial, Exploratorio, Definido, Integrado, Optimizado)"
    },
    {
      name        = "maturity_number"
      type        = "INTEGER"
      mode        = "REQUIRED"
      description = "Número de nivel de madurez (1-5)"
    },
    {
      name        = "dimensions_json"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "JSON con puntajes por dimensión/métrica"
    },
    {
      name        = "answers_json"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "JSON con respuestas individuales a cada pregunta"
    },
    {
      name        = "source_page"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "URL de la página desde donde se envió"
    },
    {
      name        = "user_agent"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "User-Agent del navegador"
    },
    {
      name        = "ip_address"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Dirección IP del usuario"
    }
  ])

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["email", "maturity_level"]

  labels = {
    environment = var.environment
    app         = "aif369-web"
  }
}

# ── Tabla: chat_conversations ──
# Guarda cada intercambio del chat widget (pregunta + respuesta) para
# seguimiento comercial, analytics y mejora continua del asistente.
resource "google_bigquery_table" "chat_conversations" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  table_id   = "chat_conversations"
  project    = var.project_id

  schema = jsonencode([
    {
      name        = "message_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "UUID único del mensaje"
    },
    {
      name        = "session_id"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "ID de sesión del chat (agrupa una conversación completa)"
    },
    {
      name        = "timestamp"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Fecha y hora del intercambio"
    },
    {
      name        = "user_message"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Mensaje enviado por el usuario"
    },
    {
      name        = "assistant_response"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Respuesta generada por el asistente"
    },
    {
      name        = "provider"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Proveedor de IA usado (gemini, ollama, none)"
    },
    {
      name        = "turn_number"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Número de turno dentro de la sesión"
    },
    {
      name        = "source_page"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Página desde donde se abrió el chat"
    },
    {
      name        = "user_agent"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "User-Agent del navegador"
    },
    {
      name        = "ip_address"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Dirección IP del usuario"
    },
    {
      name        = "language"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Idioma detectado (es, en)"
    },
    {
      name        = "intent_detected"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Intención detectada (pricing, services, scheduling, etc.)"
    }
  ])

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["session_id", "timestamp"]

  labels = {
    environment = var.environment
    app         = "aif369-web"
  }
}
