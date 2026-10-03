CREATE TABLE IF NOT EXISTS contacts (
  jid            TEXT PRIMARY KEY,
  phone          TEXT NOT NULL,
  display_name   TEXT,
  push_name      TEXT,
  first_seen     TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen      TIMESTAMPTZ NOT NULL DEFAULT now(),
  intent         TEXT,
  hot_lead       BOOLEAN NOT NULL DEFAULT FALSE,
  human_handoff  BOOLEAN NOT NULL DEFAULT FALSE,
  message_count  INTEGER NOT NULL DEFAULT 0,
  notes          TEXT
);

CREATE TABLE IF NOT EXISTS messages (
  chat_jid   TEXT NOT NULL,
  msg_id     TEXT NOT NULL,
  direction  TEXT NOT NULL CHECK (direction IN ('in', 'out')),
  sender     TEXT,
  body       TEXT,
  intent     TEXT,
  model      TEXT,
  latency_ms INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (chat_jid, msg_id)
);

CREATE INDEX IF NOT EXISTS messages_chat_created_idx
  ON messages (chat_jid, created_at DESC);

CREATE TABLE IF NOT EXISTS events (
  id         BIGSERIAL PRIMARY KEY,
  kind       TEXT NOT NULL,
  chat_jid   TEXT,
  detail     JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS events_kind_created_idx
  ON events (kind, created_at DESC);

ALTER TABLE messages ADD COLUMN IF NOT EXISTS processing_status TEXT NOT NULL DEFAULT 'processed';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS route TEXT;

CREATE OR REPLACE VIEW conversations AS
SELECT m.chat_jid,
       c.phone,
       c.push_name,
       count(*) FILTER (WHERE m.direction = 'in')  AS inbound,
       count(*) FILTER (WHERE m.direction = 'out') AS outbound,
       max(m.created_at)                          AS last_activity,
       c.intent,
       c.hot_lead,
       c.human_handoff
FROM messages m
LEFT JOIN contacts c ON c.jid = m.chat_jid
GROUP BY m.chat_jid, c.phone, c.push_name, c.intent, c.hot_lead, c.human_handoff;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE contacts ADD COLUMN IF NOT EXISTS contact_hash TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS lead_score INTEGER;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS funnel_stage TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS next_action TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

CREATE UNIQUE INDEX IF NOT EXISTS contacts_contact_hash_idx
  ON contacts (contact_hash)
  WHERE contact_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_jid TEXT NOT NULL REFERENCES contacts(jid),
  contact_hash TEXT,
  source_channel TEXT NOT NULL DEFAULT 'whatsapp_local',
  source_system TEXT NOT NULL DEFAULT 'baileys_local',
  source_record_id TEXT,
  service_key TEXT,
  service_label TEXT,
  stage TEXT NOT NULL DEFAULT 'new'
    CHECK (stage IN ('new', 'qualified', 'proposal', 'scheduled', 'won', 'lost', 'nurture', 'handoff')),
  lead_score INTEGER CHECK (lead_score IS NULL OR (lead_score >= 0 AND lead_score <= 100)),
  intent TEXT,
  pain_point TEXT,
  urgency TEXT,
  budget_range TEXT,
  next_action TEXT,
  owner TEXT,
  human_handoff BOOLEAN NOT NULL DEFAULT FALSE,
  currency TEXT DEFAULT 'USD',
  estimated_min_usd INTEGER,
  estimated_max_usd INTEGER,
  expected_value_usd NUMERIC,
  probability NUMERIC CHECK (probability IS NULL OR (probability >= 0 AND probability <= 1)),
  last_message TEXT,
  notes TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS opportunities_contact_created_idx
  ON opportunities (contact_jid, created_at DESC);

CREATE INDEX IF NOT EXISTS opportunities_stage_created_idx
  ON opportunities (stage, created_at DESC);

CREATE INDEX IF NOT EXISTS opportunities_contact_hash_idx
  ON opportunities (contact_hash)
  WHERE contact_hash IS NOT NULL;

CREATE OR REPLACE VIEW sales_pipeline AS
SELECT
  o.stage,
  o.service_key,
  o.service_label,
  count(*) AS opportunities_total,
  count(*) FILTER (WHERE o.lead_score >= 80) AS hot_leads,
  count(*) FILTER (WHERE o.human_handoff) AS handoffs_total,
  avg(o.lead_score) AS avg_lead_score,
  sum(COALESCE(o.expected_value_usd, ((o.estimated_min_usd + o.estimated_max_usd) / 2.0), 0)) AS pipeline_expected_value_usd,
  max(o.created_at) AS last_seen_at
FROM opportunities o
GROUP BY o.stage, o.service_key, o.service_label;

-- Conversacion y estado de lead (agente comercial)
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS conversation_id TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS last_intent TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS last_message_at TIMESTAMPTZ;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS lead_status TEXT NOT NULL DEFAULT 'NEW';
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS qualification JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS opted_out BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE contacts DROP CONSTRAINT IF EXISTS contacts_lead_status_check;
ALTER TABLE contacts ADD CONSTRAINT contacts_lead_status_check
  CHECK (lead_status IN ('NEW', 'QUALIFYING', 'QUALIFIED', 'HOT', 'HUMAN_HANDOFF', 'CLOSED'));

UPDATE contacts SET conversation_id = 'wa:' || phone WHERE conversation_id IS NULL AND phone IS NOT NULL;

CREATE INDEX IF NOT EXISTS contacts_lead_status_idx ON contacts (lead_status, last_message_at DESC);

-- Metricas de latencia por mensaje
ALTER TABLE messages ADD COLUMN IF NOT EXISTS inbound_at TIMESTAMPTZ;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS outbound_at TIMESTAMPTZ;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS retrieval_ms INTEGER;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS llm_ms INTEGER;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS total_ms INTEGER;


-- Estado conversacional por turno (grafo: extract -> state -> route -> validate)
ALTER TABLE contacts ADD COLUMN IF NOT EXISTS tenant TEXT NOT NULL DEFAULT 'aif369';

CREATE TABLE IF NOT EXISTS conversation_state (
  conversation_id TEXT PRIMARY KEY,
  tenant          TEXT NOT NULL DEFAULT 'aif369',
  state           JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS conversation_state_tenant_idx ON conversation_state (tenant, updated_at DESC);

-- Backoffice agentico: agent02 puede preparar borradores comerciales sin enviar nada.
CREATE TABLE IF NOT EXISTS worker_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_name TEXT NOT NULL DEFAULT 'agent02',
  job_type TEXT NOT NULL
    CHECK (job_type IN (
      'draft_proposal',
      'draft_sow',
      'draft_email',
      'research_account',
      'human_followup',
      'calculate_quote',
      'request_internal_quote_approval',
      'send_approved_quote',
      'request_supplier_quote',
      'record_supplier_quote'
    )),
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'claimed', 'done', 'failed', 'cancelled')),
  priority INTEGER NOT NULL DEFAULT 50 CHECK (priority >= 0 AND priority <= 100),
  opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
  contact_jid TEXT REFERENCES contacts(jid) ON DELETE SET NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  result JSONB,
  error TEXT,
  claimed_by TEXT,
  claimed_at TIMESTAMPTZ,
  due_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS worker_jobs_status_priority_idx
  ON worker_jobs (status, priority DESC, created_at ASC);

CREATE INDEX IF NOT EXISTS worker_jobs_opportunity_idx
  ON worker_jobs (opportunity_id, created_at DESC)
  WHERE opportunity_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS sales_drafts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
  contact_jid TEXT REFERENCES contacts(jid) ON DELETE SET NULL,
  draft_type TEXT NOT NULL
    CHECK (draft_type IN ('proposal', 'sow', 'followup_email', 'contract_brief', 'quote_email', 'supplier_quote_request')),
  status TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft', 'ready_for_review', 'internal_review_sent', 'approved', 'rejected', 'sent', 'archived')),
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  assumptions JSONB NOT NULL DEFAULT '[]'::jsonb,
  missing_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_by TEXT NOT NULL DEFAULT 'agent02',
  reviewed_by TEXT,
  reviewed_at TIMESTAMPTZ,
  sent_at TIMESTAMPTZ,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sales_drafts_opportunity_idx
  ON sales_drafts (opportunity_id, created_at DESC)
  WHERE opportunity_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS sales_drafts_status_idx
  ON sales_drafts (status, created_at DESC);

CREATE TABLE IF NOT EXISTS quote_calculations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id UUID REFERENCES opportunities(id) ON DELETE SET NULL,
  draft_id UUID REFERENCES sales_drafts(id) ON DELETE SET NULL,
  calculator_agent TEXT NOT NULL DEFAULT 'accountant_agent',
  currency TEXT NOT NULL DEFAULT 'USD',
  subtotal NUMERIC NOT NULL DEFAULT 0,
  discount_percent NUMERIC NOT NULL DEFAULT 0 CHECK (discount_percent >= 0 AND discount_percent <= 100),
  discount_amount NUMERIC NOT NULL DEFAULT 0,
  tax_percent NUMERIC NOT NULL DEFAULT 0 CHECK (tax_percent >= 0 AND tax_percent <= 100),
  tax_amount NUMERIC NOT NULL DEFAULT 0,
  total NUMERIC NOT NULL DEFAULT 0,
  formula_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  line_items JSONB NOT NULL DEFAULT '[]'::jsonb,
  validation_status TEXT NOT NULL DEFAULT 'pending'
    CHECK (validation_status IN ('pending', 'valid', 'invalid')),
  validation_errors JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS quote_calculations_opportunity_idx
  ON quote_calculations (opportunity_id, created_at DESC)
  WHERE opportunity_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS quote_approvals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  draft_id UUID REFERENCES sales_drafts(id) ON DELETE CASCADE,
  calculation_id UUID REFERENCES quote_calculations(id) ON DELETE SET NULL,
  approval_channel TEXT NOT NULL CHECK (approval_channel IN ('email', 'whatsapp', 'manual')),
  approver_name TEXT NOT NULL DEFAULT 'Erwin Daza Castillo',
  approver_contact TEXT,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'approved', 'rejected', 'changes_requested')),
  approval_message TEXT,
  internal_email_subject TEXT,
  internal_email_to TEXT NOT NULL DEFAULT 'erwin.daza@gmail.con',
  internal_email_from TEXT NOT NULL DEFAULT 'edaza@aif369.com',
  sent_for_review_at TIMESTAMPTZ,
  decided_at TIMESTAMPTZ,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS quote_approvals_status_idx
  ON quote_approvals (status, created_at DESC);

CREATE TABLE IF NOT EXISTS outbound_email_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  draft_id UUID REFERENCES sales_drafts(id) ON DELETE SET NULL,
  approval_id UUID REFERENCES quote_approvals(id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'approved_to_send', 'sent', 'failed', 'cancelled')),
  email_from TEXT NOT NULL DEFAULT 'edaza@aif369.com',
  email_to TEXT NOT NULL,
  email_cc TEXT,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  purpose TEXT NOT NULL CHECK (purpose IN ('internal_quote_review', 'client_quote', 'supplier_quote_request', 'supplier_quote_response')),
  provider TEXT NOT NULL DEFAULT 'zoho_mail',
  provider_message_id TEXT,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  sent_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS outbound_email_queue_status_idx
  ON outbound_email_queue (status, created_at ASC);
