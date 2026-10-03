-- ============================================================
-- Canonical Sales Opportunities - AIF369
-- ============================================================
-- Purpose:
--   Create one canonical commercial entity fed by web forms, web chat,
--   scorecards, WhatsApp Cloud API, local WhatsApp, quotes and payments.
--
-- Replace before running:
--   __PROJECT_ID__ -> GCP project, for example aif369-backend
--   __DATASET_ID__ -> environment dataset, for example aif369_analytics_dev
--
-- Privacy:
--   Do not store raw WhatsApp phone numbers. Use contact_hash for WhatsApp.
--   Email may be stored for web forms/payments where the user provided it.

CREATE TABLE IF NOT EXISTS `__PROJECT_ID__.__DATASET_ID__.sales_opportunities` (
  opportunity_id STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP,
  environment STRING,

  -- Source and lineage
  source_channel STRING NOT NULL, -- web_form | web_chat | scorecard | whatsapp_cloud | whatsapp_local | payment | manual
  source_system STRING,           -- backend | meta_whatsapp_cloud | baileys_local | paypal | scorecard
  source_record_id STRING,        -- submission_id | message_id | quote_id | order_id | local event id
  session_id STRING,
  trace_id STRING,

  -- Contact identity. Keep raw phone out of BigQuery.
  contact_hash STRING,
  email STRING,
  display_name STRING,
  company_name STRING,
  role STRING,
  industry STRING,

  -- Commercial state
  service_key STRING,
  service_label STRING,
  stage STRING NOT NULL,          -- new | qualified | proposal | scheduled | won | lost | nurture | handoff
  lead_score INT64,
  intent STRING,
  pain_point STRING,
  urgency STRING,
  budget_range STRING,
  next_action STRING,
  owner STRING,
  human_handoff BOOL,

  -- Value
  currency STRING,
  estimated_min NUMERIC,
  estimated_max NUMERIC,
  expected_value NUMERIC,
  probability FLOAT64,

  -- Flexible payloads
  last_message STRING,
  notes STRING,
  metadata_json STRING
)
PARTITION BY DATE(created_at)
CLUSTER BY source_channel, stage, service_key, contact_hash
OPTIONS(description="Canonical sales opportunities across forms, chat, WhatsApp, scorecards, quotes and payments");

CREATE OR REPLACE VIEW `__PROJECT_ID__.__DATASET_ID__.sales_opportunities_silver` AS
SELECT
  opportunity_id,
  created_at,
  updated_at,
  DATE(created_at, "America/Santiago") AS opportunity_date,
  environment,
  source_channel,
  source_system,
  source_record_id,
  session_id,
  trace_id,
  contact_hash,
  email,
  display_name,
  company_name,
  role,
  industry,
  service_key,
  service_label,
  stage,
  CASE
    WHEN stage IN ("won") THEN "closed_won"
    WHEN stage IN ("lost") THEN "closed_lost"
    WHEN stage IN ("proposal", "scheduled", "handoff") THEN "active_pipeline"
    WHEN stage IN ("qualified") THEN "qualified"
    ELSE "early"
  END AS stage_group,
  lead_score,
  CASE
    WHEN lead_score >= 80 THEN "hot"
    WHEN lead_score >= 50 THEN "warm"
    WHEN lead_score IS NOT NULL THEN "cold"
    ELSE "unknown"
  END AS lead_temperature,
  intent,
  pain_point,
  urgency,
  budget_range,
  next_action,
  owner,
  human_handoff,
  currency,
  estimated_min,
  estimated_max,
  COALESCE(expected_value, SAFE_DIVIDE(estimated_min + estimated_max, 2)) AS expected_value,
  probability,
  last_message,
  notes,
  metadata_json
FROM `__PROJECT_ID__.__DATASET_ID__.sales_opportunities`;

CREATE OR REPLACE VIEW `__PROJECT_ID__.__DATASET_ID__.sales_pipeline_gold` AS
SELECT
  opportunity_date,
  source_channel,
  stage_group,
  stage,
  service_key,
  service_label,
  COUNT(*) AS opportunities_total,
  COUNT(DISTINCT COALESCE(contact_hash, email, session_id)) AS unique_contacts,
  COUNTIF(lead_temperature = "hot") AS hot_leads,
  COUNTIF(human_handoff) AS handoffs_total,
  ROUND(AVG(lead_score), 2) AS avg_lead_score,
  SUM(COALESCE(expected_value, 0)) AS pipeline_expected_value,
  SUM(COALESCE(estimated_min, 0)) AS pipeline_min,
  SUM(COALESCE(estimated_max, 0)) AS pipeline_max
FROM `__PROJECT_ID__.__DATASET_ID__.sales_opportunities_silver`
GROUP BY
  opportunity_date,
  source_channel,
  stage_group,
  stage,
  service_key,
  service_label;

CREATE OR REPLACE VIEW `__PROJECT_ID__.__DATASET_ID__.sales_opportunity_sources_gold` AS
SELECT
  source_channel,
  source_system,
  COUNT(*) AS opportunities_total,
  COUNTIF(stage = "won") AS won_total,
  COUNTIF(stage_group = "active_pipeline") AS active_pipeline_total,
  COUNTIF(lead_temperature = "hot") AS hot_leads,
  SUM(COALESCE(expected_value, 0)) AS expected_value_total,
  MAX(created_at) AS last_seen_at
FROM `__PROJECT_ID__.__DATASET_ID__.sales_opportunities_silver`
GROUP BY source_channel, source_system;
