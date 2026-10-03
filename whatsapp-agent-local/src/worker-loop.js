import {
  pool,
  ensureSchema,
  enqueueProposalJobsForQualified,
  claimNextWorkerJob,
  loadOpportunityBrief,
  createSalesDraft,
  completeWorkerJob,
} from './db.js';
import { buildProposalDraft } from './proposal-worker.js';

const num = (value, fallback) => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const agentName = process.env.WORKER_NAME || 'agent02';
const intervalMs = num(process.env.WORKER_INTERVAL_MS, 30000);
const batchSize = num(process.env.WORKER_BATCH_SIZE, 5);

let stopping = false;
process.on('SIGTERM', () => {
  stopping = true;
});
process.on('SIGINT', () => {
  stopping = true;
});

async function processOne() {
  const job = await claimNextWorkerJob({ agentName, jobTypes: ['draft_proposal'] });
  if (!job) return false;

  try {
    const brief = await loadOpportunityBrief(job.opportunity_id);
    if (!brief) throw new Error(`oportunidad no encontrada: ${job.opportunity_id}`);

    const draft = buildProposalDraft(brief);
    const saved = await createSalesDraft({
      opportunityId: brief.id,
      contactJid: brief.contact_jid,
      createdBy: agentName,
      ...draft,
    });
    await completeWorkerJob(job.id, { result: { draft_id: saved.id, title: saved.title } });
    console.log(`[worker] draft listo job=${job.id} draft=${saved.id}`);
    return true;
  } catch (err) {
    await completeWorkerJob(job.id, { error: err.message });
    console.error(`[worker] job fallido job=${job.id} error=${err.message}`);
    return true;
  }
}

async function tick() {
  const created = await enqueueProposalJobsForQualified({ limit: 20 });
  if (created.length) console.log(`[worker] jobs nuevos=${created.length}`);

  let processed = 0;
  while (!stopping && processed < batchSize) {
    const didWork = await processOne();
    if (!didWork) break;
    processed += 1;
  }
  if (processed) console.log(`[worker] jobs procesados=${processed}`);
}

await ensureSchema();
console.log(`[worker] iniciado name=${agentName} interval_ms=${intervalMs}`);

while (!stopping) {
  await tick();
  if (!stopping) await new Promise((resolve) => setTimeout(resolve, intervalMs));
}

console.log('[worker] detenido');
await pool.end();
