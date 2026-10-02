-- ============================================================
-- CRM Agent Medallion Schema - AIF369
-- Objetivo: registrar cotizaciones online, conversaciones y
-- señales comerciales para analitica y cierre de ventas.
-- ============================================================

-- BRONZE: eventos crudos de cotizacion generados por el agente
CREATE TABLE IF NOT EXISTS `aif369-backend.aif369_analytics.crm_agent_quotes` (
  quote_id STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  session_id STRING,
  source_page STRING,
  service_key STRING,
  service_label STRING,
  user_message STRING,
  currency STRING,
  estimated_min INT64,
  estimated_max INT64,
  complexity_multiplier FLOAT64,
  assumptions_json STRING,
  crm_context_json STRING,
  stage STRING,
  ip_address STRING
)
PARTITION BY DATE(created_at)
CLUSTER BY service_key, stage, session_id
OPTIONS (
  description="Bronze CRM agent quotes: cotizaciones online generadas por el agente comercial"
);

-- SILVER: vista normalizada para analitica comercial
CREATE OR REPLACE VIEW `aif369-backend.aif369_analytics.crm_agent_quotes_silver` AS
SELECT
  quote_id,
  created_at,
  DATE(created_at, "America/Santiago") AS quote_date,
  session_id,
  source_page,
  service_key,
  service_label,
  currency,
  estimated_min,
  estimated_max,
  ROUND((estimated_min + estimated_max) / 2, 2) AS estimated_midpoint,
  complexity_multiplier,
  stage,
  JSON_VALUE(crm_context_json, "$.source") AS crm_context_source,
  SAFE_CAST(JSON_VALUE(crm_context_json, "$.contact_leads_90d") AS INT64) AS contact_leads_90d,
  SAFE_CAST(JSON_VALUE(crm_context_json, "$.matched_quote_count_180d") AS INT64) AS matched_quote_count_180d
FROM `aif369-backend.aif369_analytics.crm_agent_quotes`;

-- GOLD: dashboard ejecutivo del agente CRM
CREATE OR REPLACE VIEW `aif369-backend.aif369_analytics.crm_agent_quote_pipeline_gold` AS
SELECT
  quote_date,
  service_key,
  service_label,
  COUNT(*) AS quotes_total,
  COUNT(DISTINCT session_id) AS sessions_total,
  ROUND(AVG(estimated_midpoint), 2) AS avg_estimated_ticket,
  SUM(estimated_min) AS pipeline_min_usd,
  SUM(estimated_max) AS pipeline_max_usd,
  ROUND(AVG(complexity_multiplier), 2) AS avg_complexity_multiplier
FROM `aif369-backend.aif369_analytics.crm_agent_quotes_silver`
GROUP BY quote_date, service_key, service_label
ORDER BY quote_date DESC, pipeline_max_usd DESC;

