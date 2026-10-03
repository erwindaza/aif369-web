import { getRegistry, slotQuestion } from './slot-registry.js';
import { extractMessage } from './extract.js';
import { buildKnowledgeContext } from './knowledge.js';
import { generateReply } from './agent.js';
import { getTenant, knowledgeDirFor } from './tenants.js';
import {
  applyExtraction,
  calcMissingSlots,
  selectNextSlot,
  determineNextAction,
  validateQuestion,
  stateSummary,
  activeIntents,
  composeMissingSlotReply,
  composeClarifyReply,
  composeCreateLeadReply,
  pendingSlotFor,
  renderSlot,
} from './conversation-state.js';
import { validateResponse, repairHint, deterministicReply, priceSummary, PRICE_QUESTION_RE } from './response-validator.js';

// Grafo pequeño, nodos nombrados como en el diseño (port a LangGraph 1:1).
export const GRAPH_NODES = [
  'extract_message',
  'update_state',
  'detect_intent',
  'calculate_missing_slots',
  'route',
  'next_slot',
  'rag',
  'generate_response',
  'response_validator',
  'end',
];

const INTERROGATIVE = /^(que|qué|cual|cuál|cuanto|cuánto|como|cómo|donde|dónde|cuando|cuándo|quien|quién|por ?qué|por ?que)/i;

export const isQuestionText = (text) => {
  const value = String(text || '').trim();
  if (!value) return false;
  if (value.includes('?')) return true;
  return INTERROGATIVE.test(value);
};

const defaultDeps = (tenant) => ({
  extract: (args) => extractMessage(args),
  retrieve: async (text) =>
    buildKnowledgeContext(text, { dir: knowledgeDirFor(tenant.id) }),
  generate: (payload) => generateReply(payload),
});

export async function runGraph({
  state,
  text,
  tenant = getTenant(),
  history = [],
  deps: overrides = {},
}) {
  const startedAt = Date.now();
  const registry = getRegistry(tenant.slotRegistry);
  const deps = { ...defaultDeps(tenant), ...overrides };
  const isQuestion = isQuestionText(text);

  const ctx = {
    state: { ...state },
    text,
    tenant,
    registry,
    history,
    deps,
    isQuestion,
    branch: null,
    action: null,
    extraction: null,
    context: '',
    hits: [],
    retrievalMs: 0,
    reply: null,
    model: null,
    generated: false,
    validation: null,
    nodes: [],
    log: (name) => ctx.nodes.push(name),
  };

  const nodes = [
    ['extract_message', async () => {
      const pending = pendingSlotFor(ctx.state, registry);
      const run = (pendingSlot) =>
        deps.extract({
          text,
          registry,
          currentSlots: ctx.state.known_slots,
          activeIntents: ctx.state.intents || [],
          summary: stateSummary(ctx.state, registry),
          pendingSlot,
        });
      ctx.extraction = await run(pending);
      // Primera conversacion todavia sin pregunta registrada: el intento aparece al extraer.
      if (!pending && !Object.keys(ctx.extraction.slots || {}).length) {
        const freshPending = pendingSlotFor(applyExtraction(ctx.state, ctx.extraction, registry), registry);
        if (freshPending) {
          const second = await run(freshPending);
          if (Object.keys(second.slots || {}).length) ctx.extraction = second;
        }
      }
    }],
    ['update_state', () => {
      ctx.frustrationThisTurn = Boolean(ctx.extraction?.frustration);
      ctx.state = applyExtraction(ctx.state, ctx.extraction, registry);
      ctx.state.last_user_message = text;
      ctx.state.message_count = (ctx.state.message_count || 0) + 1;
      if (ctx.frustrationThisTurn) ctx.state.frustration_detected = true;
    }],
    ['detect_intent', () => {
      if (ctx.state.intents.length) {
        ctx.state.workflow = 'sales';
        ctx.state.workflow_status = 'active';
      } else {
        ctx.state.workflow = ctx.state.workflow || 'faq';
      }
    }],
    ['calculate_missing_slots', () => {
      ctx.state.missing_slots = calcMissingSlots(ctx.state, registry);
      ctx.state.next_slot = selectNextSlot(ctx.state, registry);
    }],
    ['route', () => {
      ctx.branch = ctx.isQuestion || PRICE_QUESTION_RE.test(text) ? 'faq' : 'sales';
    }],
    ['next_slot', () => {
      if (ctx.branch !== 'sales') return;
      ctx.action = determineNextAction(ctx.state, {
        isQuestion: ctx.isQuestion,
        frustrationThisTurn: ctx.frustrationThisTurn,
        rejection: Boolean(ctx.extraction?.rejection),
        registry,
      });
      ctx.state.next_action = ctx.action;
    }],
    ['rag', async () => {
      if (ctx.branch !== 'faq') return;
      const retrievalQuery = PRICE_QUESTION_RE.test(text)
        ? `${text} precios valores paquetes servicios ${tenant.name}`
        : text;
      const result = await deps.retrieve(retrievalQuery);
      ctx.context = result.context;
      ctx.hits = result.hits || [];
      ctx.retrievalMs = result.retrievalMs || 0;
      ctx.action = determineNextAction(ctx.state, {
        isQuestion: ctx.isQuestion,
        frustrationThisTurn: ctx.frustrationThisTurn,
        rejection: Boolean(ctx.extraction?.rejection),
        registry,
      });
      ctx.state.next_action = ctx.action;
    }],
    ['generate_response', async () => {
      const question = ctx.state.next_slot
        ? slotQuestion(registry, ctx.state.next_slot, ctx.state.asked_slots || [], ctx.state.asked_counts?.[ctx.state.next_slot])
        : null;
      ctx.question = question;
      ctx.state.workflow_status = ctx.state.missing_slots.length ? 'qualifying' : 'ready';

      if (ctx.action === 'clarify_intent') {
        // Rechazo explicito: respuesta corta, amable y sin insistir con el formulario.
        ctx.question = null;
        ctx.reply = composeClarifyReply(ctx.state, registry, tenant);
        ctx.model = 'state_machine';
        ctx.generated = false;
        return;
      }

      if (ctx.action === 'create_lead') {
        // Lead completo: se pide el contacto una sola vez y si no, se cierra con la propuesta.
        const contactSlot =
          registry.slots.contacto &&
          ctx.state.known_slots.contacto === undefined &&
          !(ctx.state.asked_slots || []).includes('contacto')
            ? 'contacto'
            : null;
        if (contactSlot) {
          ctx.question = slotQuestion(registry, contactSlot, ctx.state.asked_slots || [], ctx.state.asked_counts?.[contactSlot]);
          ctx.state = { ...ctx.state, next_slot: contactSlot };
        } else {
          ctx.question = null;
        }
        ctx.reply = composeCreateLeadReply(ctx.state, registry, tenant);
        ctx.model = 'state_machine';
        ctx.generated = false;
        return;
      }

      if (ctx.action === 'recover_conversation' || ctx.action === 'ask_missing_slot') {
        ctx.reply = composeMissingSlotReply(ctx.state, registry, question);
        ctx.model = 'state_machine';
        ctx.generated = true;
        return;
      }

      const result = await deps.generate({
        context: ctx.context,
        history: promptHistory(ctx.history, text),
        summary: stateSummary(ctx.state, registry),
        qualification: ctx.state.known_slots,
        suggestedQuestion: question,
        lastUserText: text,
        knowledgeHits: ctx.hits.length,
        tenant,
        hint: PRICE_QUESTION_RE.test(text)
          ? 'El cliente pregunta por precios: cita los montos del CONOCIMIENTO con su periodo; si no hay precio publicado para eso, dilo.'
          : null,
      });
      ctx.reply = result.reply;
      ctx.model = result.model;
      ctx.latencyMs = result.latencyMs;
      ctx.generated = result.model === 'ollama';
    }],
    ['response_validator', async () => {
      const question = ctx.question || null;
      const expectQuestion =
        Boolean(question) && ['ask_missing_slot', 'answer_question', 'recover_conversation'].includes(ctx.action);
      ctx.validation = validateResponse({
        state: { ...ctx.state, next_action: ctx.action },
        reply: ctx.reply,
        registry,
        question,
        expectQuestion,
        context: ctx.context,
        lastUserText: text,
      });

      if (!ctx.validation.ok && ctx.generated) {
        console.log(`[graph] validacion fallida (${ctx.validation.issues.join(',')}); reintento`);
        const retry = await deps.generate({
          context: ctx.context,
          history: promptHistory(ctx.history, text),
          summary: stateSummary(ctx.state, registry),
          qualification: ctx.state.known_slots,
          suggestedQuestion: question,
          lastUserText: text,
          knowledgeHits: ctx.hits.length,
          tenant,
          hint: repairHint({ issues: ctx.validation.issues, question }),
        });
        const check = validateResponse({
          state: { ...ctx.state, next_action: ctx.action },
          reply: retry.reply,
          registry,
          question,
          expectQuestion,
          context: ctx.context,
          lastUserText: text,
        });
        if (check.ok) {
          ctx.reply = retry.reply;
          ctx.model = retry.model;
          ctx.validation = check;
        } else {
          console.log(`[graph] reintento fallido (${check.issues.join(',')}); uso respuesta determinista`);
          ctx.reply =
            priceSummary(ctx.context, check.issues, question) ||
            deterministicReply({ state: { ...ctx.state, next_action: ctx.action }, registry, question });
          ctx.model = 'state_machine';
        }
      } else if (!ctx.validation.ok && !ctx.generated) {
        ctx.reply =
          priceSummary(ctx.context, ctx.validation.issues, question) ||
          deterministicReply({ state: { ...ctx.state, next_action: ctx.action }, registry, question });
        ctx.model = 'state_machine';
      }

      if (ctx.model === 'state_machine' && !ctx.validation.ok) {
        // La respuesta determinista se vuelve a validar: es la que de verdad sale.
        ctx.validation = validateResponse({
          state: { ...ctx.state, next_action: ctx.action },
          reply: ctx.reply,
          registry,
          question,
          expectQuestion,
          context: ctx.context,
          lastUserText: text,
        });
      }

      if (ctx.reply && question) {
        ctx.state = markAsked(ctx.state, question, registry, ctx.reply);
      }
      ctx.state.last_assistant_message = ctx.reply || '';
      ctx.state.conversation_summary = stateSummary(ctx.state, registry);
    }],
    ['end', () => {}],
  ];

  for (const [name, run] of nodes) {
    ctx.log(name);
    await run();
  }

  return {
    state: ctx.state,
    reply: ctx.reply,
    model: ctx.model,
    action: ctx.action,
    branch: ctx.branch,
    nextSlot: ctx.state.next_slot,
    question: ctx.question || null,
    hits: ctx.hits,
    retrievalMs: ctx.retrievalMs,
    llmMs: ctx.latencyMs || 0,
    totalMs: Date.now() - startedAt,
    validation: ctx.validation,
    nodes: ctx.nodes,
  };
}

// El mensaje actual siempre va en el historial: sin el, el modelo responde a la nada.
// Las respuestas de maquina (templates) no se leen: un modelo de 1B solo las repite.
const TEMPLATE_REPLY =
  /^(Entonces buscas|Entendido\.|Disculpa, ya me habías dicho|Perfecto, anoto|Perfecto, con |Perfecto, .* ya lo tengo|Ya me diste|Perfecto\. El cliente)/;

function promptHistory(history, text) {
  const rows = (Array.isArray(history) ? history : []).filter(
    (row) => row.direction !== 'out' || !TEMPLATE_REPLY.test(String(row.body || ''))
  );
  const last = rows[rows.length - 1];
  if (!last || last.body !== text || last.direction !== 'in') {
    rows.push({ direction: 'in', body: text });
  }
  return rows;
}

// Si la respuesta realmente preguntó por ese slot, queda registrado para no repetirlo.
function markAsked(state, question, registry, reply) {
  const q = String(question || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const text = String(reply || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  if (!text.includes(q.replace(/\s+/g, ' ').trim())) return state;
  const slot = state.next_slot;
  if (!slot || !validateQuestion(state, slot, registry)) return state;
  const counts = { ...(state.asked_counts || {}) };
  counts[slot] = (counts[slot] || 0) + 1;
  return { ...state, asked_slots: [...new Set([...(state.asked_slots || []), slot])], asked_counts: counts };
}
