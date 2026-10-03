// Simula el pipeline del agente (sin WhatsApp ni PostgreSQL) para pruebas rapidas.
// Uso:
//   node scripts/simulate.mjs                            # casos A-F (grafo)
//   node scripts/simulate.mjs --tenant priceclima        # otro bot
//   node scripts/simulate.mjs --no-graph "hola"          # pipeline viejo (sin grafo)
//   node scripts/simulate.mjs --no-llm "hola"            # solo reglas + retrieval
//   node scripts/simulate.mjs --json "quiero cotizar"
import { route } from '../src/router.js';
import { buildKnowledgeContext, loadKnowledge } from '../src/knowledge.js';
import { generateReply, knowledgeGuard, knowledgeGuardReply } from '../src/agent.js';
import { extractQualification, computeLeadStatus, nextQuestion, leadScore } from '../src/qualification.js';
import { runGraph } from '../src/graph.js';
import { createConversationState } from '../src/conversation-state.js';
import { getTenant, knowledgeDirFor } from '../src/tenants.js';
import { withContactFooter } from '../src/contact.js';

const DEFAULT_CASES = [
  ['A', 'Hola'],
  ['B', '¿Qué servicios ofrece AIF369?'],
  ['C', 'Tengo SAP, Excel y PostgreSQL y quiero una fuente única de verdad.'],
  ['D', 'Tenemos un proyecto ETL detenido. ¿Pueden tomarlo y terminarlo?'],
  ['E', 'Quiero cotizar.'],
  ['F', 'Quiero hablar con una persona.'],
];

const DEFAULT_PRICECLIMA_CASES = [
  ['1', 'Me dijeron que también instalan aire acondicionado'],
  ['2', 'Marca Daikin'],
  ['3', 'Un dormitorio'],
  ['4', 'Es un dormitorio normal'],
  ['5', 'Hace calor en verano'],
  ['6', '¿Tienen para dormitorio?'],
  ['7', 'Me interesa la mantención'],
  ['8', 'Ya te dije que es un dormitorio'],
];

const args = process.argv.slice(2);
const useLlm = !args.includes('--no-llm');
const asJson = args.includes('--json');
const useGraph = !args.includes('--no-graph');
const tenantId = args.includes('--tenant') ? args[args.indexOf('--tenant') + 1] : undefined;
const tenant = getTenant(tenantId);
const isDefaultTenant = tenant.id === 'aif369';
const texts = args.filter(
  (a, i) => !a.startsWith('--') && args[i - 1] !== '--tenant' && args[i - 1] !== '--'
);

const cases = texts.length
  ? texts.map((t, i) => [String(i + 1), t])
  : isDefaultTenant
    ? DEFAULT_CASES
    : DEFAULT_PRICECLIMA_CASES;

const knowledgeDir = knowledgeDirFor(tenant.id);
await loadKnowledge({ force: true, dir: knowledgeDir });

const stubDeps = {
  generate: async () => ({ reply: '(llm omitido con --no-llm)', model: 'none', latencyMs: 0, ok: false }),
};

let state = createConversationState({ conversationId: 'wa:simulado', tenant: tenant.id });
const history = [];
const results = [];

for (const [id, text] of cases) {
  const inboundAt = Date.now();
  const message = { text, conversation_id: 'wa:simulado', sender_id: 'simulado' };
  const decision = route(message, { health: 'simulado', tenant });
  const qualification = extractQualification(text, {});
  const entry = {
    id,
    text,
    tenant: tenant.id,
    route: decision.route,
    intent: decision.intent || '-',
    llm: Boolean(decision.llm),
    hot: Boolean(decision.hot),
    lead: Boolean(decision.lead),
    handoff: Boolean(decision.handoff),
    optOut: Boolean(decision.optOut),
    lead_status: computeLeadStatus({
      intent: decision.intent,
      qualification,
      hot: decision.hot,
      handoff: decision.handoff,
      optOut: decision.optOut,
    }),
    score: leadScore(computeLeadStatus({ intent: decision.intent, qualification, hot: decision.hot }), qualification),
    qualification,
    next_question: nextQuestion(qualification),
    reply: decision.reply || null,
    retrieval_ms: 0,
    llm_ms: 0,
    total_ms: 0,
    chunks: [],
  };

  if (decision.llm && useGraph) {
    const result = await runGraph({
      state,
      text,
      tenant,
      history,
      deps: useLlm ? {} : stubDeps,
    });
    state = result.state;
    history.push({ direction: 'in', body: text }, { direction: 'out', body: result.reply });
    entry.reply = result.reply;
    entry.model = result.model;
    entry.retrieval_ms = result.retrievalMs;
    entry.llm_ms = result.llmMs;
    entry.chunks = (result.hits || []).map((h) => ({
      doc: h.chunk.doc,
      heading: h.chunk.heading,
      score: Number(h.score.toFixed(3)),
      source: h.source,
    }));
    entry.context_chars = entry.chunks.length ? 1 : 0;
    entry.branch = result.branch;
    entry.action = result.action;
    entry.intents = state.intents;
    entry.known_slots = state.known_slots;
    entry.missing_slots = state.missing_slots;
    entry.next_slot = state.next_slot;
    entry.asked_slots = state.asked_slots;
    entry.validation = result.validation?.ok ? 'ok' : (result.validation?.issues || []).join(',');
    entry.qualification = state.known_slots;
    entry.next_question = result.question || state.next_slot || null;
  } else if (decision.llm) {
    const { context, retrievalMs, hits } = await buildKnowledgeContext(text, { dir: knowledgeDir });
    entry.retrieval_ms = retrievalMs;
    entry.chunks = hits.map((h) => ({
      doc: h.chunk.doc,
      heading: h.chunk.heading,
      score: Number(h.score.toFixed(3)),
      source: h.source,
    }));
    entry.context_chars = context.length;
    if (knowledgeGuard(hits.length, text)) {
      entry.reply = knowledgeGuardReply(text, entry.next_question, tenant);
      entry.model = 'knowledge_guard';
      entry.llm_ok = true;
    } else if (useLlm) {
      const result = await generateReply({
        context,
        history: [{ direction: 'in', body: text }],
        summary: `estado=${entry.lead_status} intent=${entry.intent}`,
        qualification,
        suggestedQuestion: nextQuestion(qualification),
        lastUserText: text,
        knowledgeHits: hits.length,
        tenant,
      });
      entry.reply = result.reply;
      entry.model = result.model;
      entry.llm_ok = result.ok;
      entry.llm_ms = result.latencyMs;
    } else {
      entry.reply = '(llm omitido con --no-llm)';
      entry.model = 'none';
    }
  } else {
    entry.model = 'instant_rule';
  }

  entry.reply = withContactFooter(entry.reply, tenant, { route: entry.route, model: entry.model });
  entry.total_ms = Date.now() - inboundAt;
  results.push(entry);

  if (!asJson) {
    console.log(`\n=== ${id}) ${text}`);
    console.log(
      `route=${entry.route} intent=${entry.intent} llm=${entry.llm} model=${entry.model} ` +
        `lead_status=${entry.lead_status} score=${entry.score}`
    );
    if (entry.branch) {
      console.log(
        `branch=${entry.branch} action=${entry.action} intents=${(entry.intents || []).join(',') || '-'} ` +
          `missing=${(entry.missing_slots || []).length} next_slot=${entry.next_slot || '-'} ` +
          `valid=${entry.validation || '-'}`
      );
    }
    if (entry.chunks.length) {
      console.log(`retrieval (${entry.retrieval_ms}ms):`);
      for (const c of entry.chunks) console.log(`  - ${c.doc} :: ${c.heading} (${c.score})`);
    }
    if (entry.next_question) console.log(`siguiente pregunta: ${entry.next_question}`);
    console.log(`retrieval=${entry.retrieval_ms}ms llm=${entry.llm_ms}ms total=${entry.total_ms}ms`);
    console.log(`>> ${entry.reply}`);
  }
}

if (asJson) console.log(JSON.stringify(results, null, 2));
