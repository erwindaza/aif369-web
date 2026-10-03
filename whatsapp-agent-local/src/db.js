import { readFile } from 'node:fs/promises';
import pg from 'pg';
import { config } from './config.js';

const { Pool } = pg;

export const pool = new Pool({
  host: config.db.host,
  port: config.db.port,
  database: config.db.database,
  user: config.db.user,
  password: config.db.password,
  max: 5,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

pool.on('error', (err) => console.error('[db] error de conexión:', err.message));

export const query = (text, params) => pool.query(text, params);

export async function ensureSchema() {
  const sql = await readFile(new URL('../schema.sql', import.meta.url), 'utf8');
  await pool.query(sql);
}

export async function upsertContact({ jid, phone, pushName, displayName }) {
  const { rows } = await pool.query(
    `INSERT INTO contacts (jid, phone, display_name, push_name, conversation_id, last_message_at, last_seen)
     VALUES ($1, $2, $3, $4, $5, now(), now())
     ON CONFLICT (jid) DO UPDATE SET
       last_seen = now(),
       last_message_at = now(),
       push_name = COALESCE(EXCLUDED.push_name, contacts.push_name),
       display_name = COALESCE(NULLIF(EXCLUDED.display_name, ''), contacts.display_name),
       conversation_id = COALESCE(contacts.conversation_id, EXCLUDED.conversation_id),
       message_count = contacts.message_count + 1
     RETURNING *`,
    [jid, phone, displayName || '', pushName || '', `wa:${String(phone || '').split(':')[0]}`]
  );
  return rows[0];
}

export async function saveMessage({
  chatJid,
  msgId,
  direction,
  sender,
  body,
  intent,
  model,
  latencyMs,
  processingStatus = 'processed',
  route = null,
  inboundAt = null,
  outboundAt = null,
  retrievalMs = null,
  llmMs = null,
  totalMs = null,
}) {
  const { rows } = await pool.query(
    `INSERT INTO messages (
       chat_jid, msg_id, direction, sender, body, intent, model, latency_ms,
       processing_status, route, inbound_at, outbound_at, retrieval_ms, llm_ms, total_ms
     )
     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
     ON CONFLICT (chat_jid, msg_id) DO NOTHING
     RETURNING msg_id`,
    [
      chatJid,
      msgId,
      direction,
      sender || null,
      body || null,
      intent || null,
      model || null,
      latencyMs || null,
      processingStatus,
      route,
      inboundAt,
      outboundAt,
      retrievalMs,
      llmMs,
      totalMs,
    ]
  );
  return rows.length > 0;
}

export async function recentMessages(chatJid, limit) {
  const { rows } = await pool.query(
    `SELECT direction, body, created_at
     FROM messages
     WHERE chat_jid = $1 AND body IS NOT NULL
     ORDER BY created_at DESC
     LIMIT $2`,
    [chatJid, limit]
  );
  return rows.reverse();
}

export async function countMessages(chatJid) {
  const { rows } = await pool.query(
    `SELECT count(*)::int AS total,
            count(*) FILTER (WHERE direction = 'in')::int AS inbound
     FROM messages WHERE chat_jid = $1`,
    [chatJid]
  );
  return rows[0];
}

export async function setContactFlags(jid, { hotLead, humanHandoff, intent, notes }) {
  const { rows } = await pool.query(
    `UPDATE contacts SET
       hot_lead = COALESCE($2, hot_lead),
       human_handoff = COALESCE($3, human_handoff),
       intent = COALESCE($4, intent),
       notes = COALESCE($5, notes),
       updated_at = now()
     WHERE jid = $1
     RETURNING *`,
    [jid, hotLead ?? null, humanHandoff ?? null, intent ?? null, notes ?? null]
  );
  return rows[0];
}

export async function updateConversationState(
  jid,
  { lastIntent, leadStatus, summary, qualification, humanHandoff, optedOut, hotLead, score }
) {
  const { rows } = await pool.query(
    `UPDATE contacts SET
       last_intent = COALESCE($2, last_intent),
       last_message_at = now(),
       lead_status = COALESCE($3, lead_status),
       summary = COALESCE($4, summary),
       qualification = CASE WHEN $5::jsonb IS NULL THEN qualification ELSE qualification || $5::jsonb END,
       human_handoff = COALESCE($6, human_handoff),
       opted_out = COALESCE($7, opted_out),
       hot_lead = COALESCE($8, hot_lead),
       lead_score = COALESCE($9, lead_score),
       updated_at = now()
     WHERE jid = $1
     RETURNING *`,
    [
      jid,
      lastIntent ?? null,
      leadStatus ?? null,
      summary ?? null,
      qualification ? JSON.stringify(qualification) : null,
      humanHandoff ?? null,
      optedOut ?? null,
      hotLead ?? null,
      score ?? null,
    ]
  );
  return rows[0];
}

const STAGE_BY_STATUS = {
  NEW: 'new',
  QUALIFYING: 'new',
  QUALIFIED: 'qualified',
  HOT: 'qualified',
  HUMAN_HANDOFF: 'handoff',
  CLOSED: 'lost',
};

export async function upsertOpportunity({
  contactJid,
  intent,
  serviceKey,
  serviceLabel,
  leadStatus,
  leadScore,
  painPoint,
  urgency,
  humanHandoff = false,
  lastMessage,
  metadata,
}) {
  const stage = STAGE_BY_STATUS[leadStatus] || 'new';
  const { rows: existing } = await pool.query(
    `SELECT id FROM opportunities
     WHERE contact_jid = $1 AND stage NOT IN ('won', 'lost')
     ORDER BY created_at DESC LIMIT 1`,
    [contactJid]
  );

  if (existing.length) {
    const { rows } = await pool.query(
      `UPDATE opportunities SET
         service_key = COALESCE($2, service_key),
         service_label = COALESCE($3, service_label),
         stage = $4,
         lead_score = COALESCE($5, lead_score),
         intent = COALESCE($6, intent),
         pain_point = COALESCE($7, pain_point),
         urgency = COALESCE($8, urgency),
         human_handoff = COALESCE($9, human_handoff),
         last_message = COALESCE($10, last_message),
         metadata = CASE WHEN $11::jsonb IS NULL THEN metadata ELSE metadata || $11::jsonb END,
         updated_at = now()
       WHERE id = $1
       RETURNING id, stage, lead_score`,
      [
        existing[0].id,
        serviceKey,
        serviceLabel,
        stage,
        leadScore ?? null,
        intent,
        painPoint || null,
        urgency || null,
        humanHandoff,
        lastMessage || null,
        metadata ? JSON.stringify(metadata) : null,
      ]
    );
    return { row: rows[0], created: false };
  }

  const { rows } = await pool.query(
    `INSERT INTO opportunities (
       contact_jid, service_key, service_label, stage, lead_score, intent,
       pain_point, urgency, human_handoff, last_message, metadata
     ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
     RETURNING id, stage, lead_score`,
    [
      contactJid,
      serviceKey,
      serviceLabel,
      stage,
      leadScore ?? null,
      intent,
      painPoint || null,
      urgency || null,
      humanHandoff,
      lastMessage || null,
      metadata ? JSON.stringify(metadata) : null,
    ]
  );
  return { row: rows[0], created: true };
}

export async function listLeads({ limit = 30 } = {}) {
  const { rows } = await pool.query(
    `SELECT jid, phone, push_name, conversation_id, last_intent, lead_status, lead_score,
            human_handoff, opted_out, qualification, summary, last_message_at, message_count
     FROM contacts
     WHERE lead_status <> 'NEW' OR hot_lead OR human_handoff
     ORDER BY last_message_at DESC NULLS LAST
     LIMIT $1`,
    [limit]
  );
  return rows;
}

export async function listOpportunities({ limit = 30 } = {}) {
  const { rows } = await pool.query(
    `SELECT id, contact_jid, service_key, service_label, stage, lead_score, intent,
            human_handoff, updated_at
     FROM opportunities
     ORDER BY updated_at DESC
     LIMIT $1`,
    [limit]
  );
  return rows;
}

export async function enqueueOpportunityJob({
  opportunityId,
  contactJid,
  jobType = 'draft_proposal',
  priority = 70,
  payload = {},
  agentName = 'agent02',
}) {
  const { rows } = await pool.query(
    `INSERT INTO worker_jobs (agent_name, job_type, priority, opportunity_id, contact_jid, payload)
     VALUES ($1, $2, $3, $4, $5, $6::jsonb)
     RETURNING id, agent_name, job_type, status, priority, opportunity_id, contact_jid, created_at`,
    [agentName, jobType, priority, opportunityId || null, contactJid || null, JSON.stringify(payload || {})]
  );
  return rows[0];
}

export async function enqueueProposalJobsForQualified({ limit = 20 } = {}) {
  const { rows } = await pool.query(
    `WITH candidates AS (
       SELECT o.id, o.contact_jid, o.stage, o.lead_score, o.intent, o.service_key, o.service_label
       FROM opportunities o
       WHERE o.stage IN ('qualified', 'proposal', 'handoff')
         AND NOT EXISTS (
           SELECT 1 FROM worker_jobs j
           WHERE j.opportunity_id = o.id
             AND j.job_type = 'draft_proposal'
             AND j.status IN ('pending', 'claimed', 'done')
         )
       ORDER BY o.lead_score DESC NULLS LAST, o.updated_at DESC
       LIMIT $1
     )
     INSERT INTO worker_jobs (agent_name, job_type, priority, opportunity_id, contact_jid, payload)
     SELECT 'agent02',
            'draft_proposal',
            CASE WHEN lead_score >= 80 THEN 90 ELSE 70 END,
            id,
            contact_jid,
            jsonb_build_object(
              'stage', stage,
              'lead_score', lead_score,
              'intent', intent,
              'service_key', service_key,
              'service_label', service_label
            )
     FROM candidates
     RETURNING id, agent_name, job_type, status, priority, opportunity_id, contact_jid, created_at`,
    [limit]
  );
  return rows;
}

export async function claimNextWorkerJob({ agentName = 'agent02', jobTypes = ['draft_proposal'] } = {}) {
  const { rows } = await pool.query(
    `WITH next_job AS (
       SELECT id
       FROM worker_jobs
       WHERE status = 'pending'
         AND agent_name = $1
         AND job_type = ANY($2::text[])
       ORDER BY priority DESC, created_at ASC
       LIMIT 1
       FOR UPDATE SKIP LOCKED
     )
     UPDATE worker_jobs j SET
       status = 'claimed',
       claimed_by = $1,
       claimed_at = now(),
       updated_at = now()
     FROM next_job
     WHERE j.id = next_job.id
     RETURNING j.*`,
    [agentName, jobTypes]
  );
  return rows[0] || null;
}

export async function loadOpportunityBrief(opportunityId) {
  const { rows } = await pool.query(
    `SELECT
       o.*,
       c.phone,
       c.display_name,
       c.push_name,
       c.lead_status,
       c.summary,
       c.qualification,
       c.conversation_id
     FROM opportunities o
     LEFT JOIN contacts c ON c.jid = o.contact_jid
     WHERE o.id = $1`,
    [opportunityId]
  );
  return rows[0] || null;
}

export async function createSalesDraft({
  opportunityId,
  contactJid,
  draftType,
  title,
  body,
  assumptions = [],
  missingFields = [],
  createdBy = 'agent02',
  metadata = {},
}) {
  const { rows } = await pool.query(
    `INSERT INTO sales_drafts (
       opportunity_id, contact_jid, draft_type, status, title, body,
       assumptions, missing_fields, created_by, metadata
     )
     VALUES ($1, $2, $3, 'ready_for_review', $4, $5, $6::jsonb, $7::jsonb, $8, $9::jsonb)
     RETURNING id, draft_type, status, title, created_at`,
    [
      opportunityId || null,
      contactJid || null,
      draftType,
      title,
      body,
      JSON.stringify(assumptions || []),
      JSON.stringify(missingFields || []),
      createdBy,
      JSON.stringify(metadata || {}),
    ]
  );
  return rows[0];
}

export async function completeWorkerJob(jobId, { result, error } = {}) {
  const failed = Boolean(error);
  const { rows } = await pool.query(
    `UPDATE worker_jobs SET
       status = $2,
       result = CASE WHEN $3::jsonb IS NULL THEN result ELSE $3::jsonb END,
       error = $4,
       updated_at = now()
     WHERE id = $1
     RETURNING id, status, result, error`,
    [jobId, failed ? 'failed' : 'done', result ? JSON.stringify(result) : null, error || null]
  );
  return rows[0];
}

export async function listSalesDrafts({ limit = 30 } = {}) {
  const { rows } = await pool.query(
    `SELECT d.id, d.draft_type, d.status, d.title, d.created_by, d.created_at,
            d.opportunity_id, c.phone, c.push_name
     FROM sales_drafts d
     LEFT JOIN contacts c ON c.jid = d.contact_jid
     ORDER BY d.created_at DESC
     LIMIT $1`,
    [limit]
  );
  return rows;
}

export async function loadConversationState(conversationId) {
  if (!conversationId) return null;
  const { rows } = await pool.query(
    `SELECT state FROM conversation_state WHERE conversation_id = $1`,
    [conversationId]
  );
  return rows[0]?.state || null;
}

export async function saveConversationState(conversationId, tenant, state) {
  if (!conversationId) return null;
  const { rows } = await pool.query(
    `INSERT INTO conversation_state (conversation_id, tenant, state, updated_at)
     VALUES ($1, $2, $3::jsonb, now())
     ON CONFLICT (conversation_id) DO UPDATE SET
       tenant = EXCLUDED.tenant,
       state = EXCLUDED.state,
       updated_at = now()
     RETURNING conversation_id`,
    [conversationId, tenant || 'aif369', JSON.stringify(state || {})]
  );
  return rows[0];
}

export async function logEvent(kind, chatJid, detail) {
  await pool.query(`INSERT INTO events (kind, chat_jid, detail) VALUES ($1, $2, $3)`, [
    kind,
    chatJid || null,
    detail ? JSON.stringify(detail) : null,
  ]);
}
