import {
  pool,
  ensureSchema,
  enqueueProposalJobsForQualified,
  claimNextWorkerJob,
  loadOpportunityBrief,
  createSalesDraft,
  completeWorkerJob,
  listSalesDrafts,
} from './db.js';
import { buildProposalDraft } from './proposal-worker.js';

const [, , command = 'proposals'] = process.argv;

await ensureSchema();

if (command === 'proposals') {
  const createdJobs = await enqueueProposalJobsForQualified({ limit: 20 });
  console.log(`jobs nuevos: ${createdJobs.length}`);

  const job = await claimNextWorkerJob({ agentName: 'agent02', jobTypes: ['draft_proposal'] });
  if (!job) {
    console.log('sin trabajos pendientes para agent02');
  } else {
    try {
      const brief = await loadOpportunityBrief(job.opportunity_id);
      if (!brief) throw new Error(`oportunidad no encontrada: ${job.opportunity_id}`);

      const draft = buildProposalDraft(brief);
      const saved = await createSalesDraft({
        opportunityId: brief.id,
        contactJid: brief.contact_jid,
        ...draft,
      });
      await completeWorkerJob(job.id, { result: { draft_id: saved.id, title: saved.title } });
      console.log(`draft listo: ${saved.id} ${saved.title}`);
    } catch (err) {
      await completeWorkerJob(job.id, { error: err.message });
      console.error(`job fallido ${job.id}: ${err.message}`);
      process.exitCode = 1;
    }
  }
} else if (command === 'drafts') {
  const drafts = await listSalesDrafts({ limit: 40 });
  console.log(`\n=== DRAFTS (${drafts.length}) ===`);
  for (const d of drafts) {
    const when = new Date(d.created_at).toLocaleString('es-CL', { timeZone: 'America/Santiago' });
    console.log(`${when} ${d.status.padEnd(16)} ${d.draft_type.padEnd(14)} ${d.title}`);
  }
  console.log('');
} else {
  console.error(`comando desconocido: ${command} (disponibles: proposals, drafts)`);
  process.exit(1);
}

await pool.end();
