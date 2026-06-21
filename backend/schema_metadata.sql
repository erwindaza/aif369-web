-- ============================================================
-- TABLE: chat_session_metadata
-- Tabla para guardar metadata de sesiones de chat
-- VINCULACIÓN: session_id (FK) → chat_conversations.session_id
-- ============================================================

CREATE TABLE IF NOT EXISTS `aif369-backend.aif369_analytics.chat_session_metadata` (
  session_id STRING NOT NULL,
  metadata_timestamp TIMESTAMP NOT NULL,
  user_role STRING,  -- CEO, CTO, CDO, Developer, HR, Finance, Other
  industry STRING,   -- Finanzas, Retail, Tecnología, Salud, Logística, Educación, Otro
  project_status STRING,  -- sin_ia, explorando, piloto, en_produccion
  lead_quality_score INTEGER,  -- 1-10: calidad del lead basado en engagement
  lead_source STRING,  -- web_chat, scorecard, contacto_directo, email
  qualification_stage STRING,  -- awareness, consideration, evaluation, closed_won, closed_lost
  whatsapp_shared BOOL DEFAULT FALSE,
  email_captured STRING,
  company_name STRING,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP
)
PARTITION BY DATE(created_at)
CLUSTER BY session_id, user_role, industry
WITH CONNECTION OPTIONS (
  description="Metadata de sesiones de chat para lead scoring y seguimiento"
);

-- Crear índice virtual en session_id
-- BigQuery usa automatic indexing para estas columnas

-- ============================================================
-- VIEW: chat_lead_pipeline
-- Para ver el funnel de conversión de leads
-- ============================================================

CREATE OR REPLACE VIEW `aif369-backend.aif369_analytics.chat_lead_pipeline` AS
SELECT
  DATE(m.created_at) as date,
  m.user_role,
  m.industry,
  m.project_status,
  m.qualification_stage,
  COUNT(DISTINCT m.session_id) as total_sessions,
  COUNTIF(m.lead_quality_score >= 7) as high_quality_leads,
  COUNTIF(m.whatsapp_shared) as whatsapp_contacts,
  COUNTIF(m.email_captured IS NOT NULL) as email_captures,
  AVG(m.lead_quality_score) as avg_quality_score
FROM
  `aif369-backend.aif369_analytics.chat_session_metadata` m
GROUP BY
  date, user_role, industry, project_status, qualification_stage
ORDER BY
  date DESC, total_sessions DESC;
