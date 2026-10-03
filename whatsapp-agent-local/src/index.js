import { randomUUID } from 'node:crypto';
import { config } from './config.js';
import {
  ensureSchema,
  upsertContact,
  saveMessage,
  recentMessages,
  countMessages,
  setContactFlags,
  updateConversationState,
  upsertOpportunity,
  logEvent,
  loadConversationState,
  saveConversationState,
  pool,
} from './db.js';
import { isReady as ollamaReady } from './ollama.js';
import { installSignalGuard } from './signal-guard.js';
import { markOutbound, States, setState, getState } from './state.js';
import { route } from './router.js';
import { generateReply } from './agent.js';
import { buildKnowledgeContext, loadKnowledge, getKnowledgeStats } from './knowledge.js';
import { extractQualification, computeLeadStatus, leadScore, nextQuestion, qualificationSummary } from './qualification.js';
import { serviceForIntent } from './intents.js';
import { startHealthServer } from './health.js';
import { runGraph } from './graph.js';
import { normalizeState } from './conversation-state.js';
import { getTenant, tenantForContact, knowledgeDirFor } from './tenants.js';
import { withContactFooter } from './contact.js';
import { connect, wa } from './whatsapp.js';

const chains = new Map();
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

let ollamaStatus = false;

function enqueue(conversationId, task) {
  const previous = chains.get(conversationId) || Promise.resolve();
  const next = previous.then(task).catch((err) => console.error(`[agent] ${conversationId}: ${err.message}`));
  chains.set(conversationId, next);
  return next;
}

const delayFor = (instant) =>
  instant
    ? config.instantReplyDelay.min +
      Math.floor(Math.random() * (config.instantReplyDelay.max - config.instantReplyDelay.min))
    : config.replyDelay.min + Math.floor(Math.random() * (config.replyDelay.max - config.replyDelay.min));

async function sendReply(chatJid, text, { instant = false } = {}) {
  if (!wa.socket) throw new Error('socket de WhatsApp no listo');
  try {
    await wa.socket.sendPresenceUpdate('composing', chatJid);
  } catch {}
  await sleep(delayFor(instant));
  const sent = await wa.socket.sendMessage(chatJid, { text });
  markOutbound();
  try {
    await wa.socket.sendPresenceUpdate('paused', chatJid);
  } catch {}
  return sent;
}

async function persistOutbound({ chatJid, text, intent, model, latencyMs, routeName, metrics = {} }) {
  await saveMessage({
    chatJid,
    msgId: `local-${randomUUID()}`,
    direction: 'out',
    sender: 'agent',
    body: text,
    intent,
    model,
    latencyMs,
    processingStatus: 'sent',
    route: routeName,
    inboundAt: metrics.inboundAt || null,
    outboundAt: new Date(),
    retrievalMs: metrics.retrievalMs ?? null,
    llmMs: metrics.llmMs ?? null,
    totalMs: metrics.totalMs ?? null,
  });
}

const statusText = () =>
  `WhatsApp ${getState()}, base de datos ok, Ollama ${ollamaStatus ? config.ollama.model : 'no disponible'}`;

async function finalizeTurn({
  chatJid, senderId, contact, decision, text, qualification, metrics, forceLead = false, leadIntent = null,
}) {
  const handoff = Boolean(decision.handoff);
  const optOut = Boolean(decision.optOut);
  const intent = leadIntent || decision.intent;
  const leadStatus = computeLeadStatus({
    intent,
    qualification,
    hot: Boolean(decision.hot),
    handoff,
    optOut,
    current: contact.lead_status || 'NEW',
  });
  const score = leadScore(leadStatus, qualification);
  const summary = `estado=${leadStatus} intent=${intent || contact.last_intent || '-'} ${
    qualificationSummary(qualification) || 'sin datos de calificacion'
  }`;

  await updateConversationState(chatJid, {
    lastIntent: intent || null,
    leadStatus,
    summary,
    qualification,
    humanHandoff: handoff ? true : decision.resume ? false : null,
    optedOut: optOut ? true : null,
    hotLead: decision.hot ? true : null,
    score,
  });

  if ((decision.lead || forceLead) && !optOut) {
    const { row, created } = await upsertOpportunity({
      contactJid: chatJid,
      intent,
      ...serviceForIntent(intent),
      leadStatus,
      leadScore: score,
      painPoint: qualification.problema || null,
      urgency: qualification.urgencia || null,
      humanHandoff: handoff,
      lastMessage: (text || '').slice(0, 300),
      metadata: {
        conversation_id: contact.conversation_id || `wa:${senderId}`,
        sender_id: senderId,
        last_intent: intent || null,
        qualification,
        updated_by: 'whatsapp-agent',
      },
    });
    if (created && decision.hot) {
      await logEvent('opportunity_created', chatJid, { stage: row.stage, intent: decision.intent });
    }
  }

  if (metrics) {
    console.log(
      `[metrics] route=${decision.route} intent=${decision.intent || '-'} model=${metrics.model || '-'} ` +
        `retrieval=${metrics.retrievalMs ?? 0}ms llm=${metrics.llmMs ?? 0}ms total=${metrics.totalMs ?? 0}ms ` +
        `status=${leadStatus}`
    );
  }
  return { leadStatus, summary };
}

async function handleInbound(message) {
  const inboundAt = Date.now();
  const { chatJid, message_id: msgId, sender_id: senderId, type, text } = message;

  const isNew = await saveMessage({
    chatJid,
    msgId,
    direction: 'in',
    sender: senderId,
    body: text || null,
    processingStatus: 'received',
    inboundAt: new Date(inboundAt),
  });

  if (!isNew) {
    console.log(`[whatsapp] duplicate message_id ignored message_id=${msgId}`);
    await logEvent('duplicate_ignored', chatJid, { message_id: msgId });
    return;
  }

  const contact = await upsertContact({
    jid: chatJid,
    phone: senderId,
    pushName: message.metadata.push_name,
  });

  if (type !== 'text') {
    await logEvent('unsupported_type', chatJid, { type });
    return;
  }

  let tenant = tenantForContact(contact);
  const knownName = contact.push_name || contact.display_name || null;
  const decision = route({ ...message, knownName }, { health: statusText(), tenant });
  if (decision.expert?.expert) {
    tenant = getTenant(decision.expert.expert);
  }
  const qualification = extractQualification(text, contact.qualification || {});
  console.log(
    `[router] route=${decision.route} intent=${decision.intent || '-'} conversation=${message.conversation_id}`
  );

  if (decision.optOut) {
    await logEvent('opt_out', chatJid, { phone: senderId });
    await finalizeTurn({ chatJid, senderId, contact, decision, text, qualification, metrics: null });
    const optOutText = withContactFooter(decision.reply, tenant, { route: decision.route, model: 'opt_out' });
    await sendReply(chatJid, optOutText, { instant: true });
    await persistOutbound({ chatJid, text: optOutText, model: 'opt_out', routeName: decision.route });
    console.log(`[agent] ***${senderId.slice(-4)} opt-out, bot detenido`);
    return;
  }

  if (decision.handoff) {
    await setContactFlags(chatJid, { humanHandoff: true });
    await logEvent('handoff_on', chatJid, { pushName: message.metadata.push_name, intent: decision.intent });
    const result = await finalizeTurn({ chatJid, senderId, contact, decision, text, qualification, metrics: null });
    console.log(`[router] handoff activado status=${result.leadStatus}`);
    const handoffText = withContactFooter(decision.reply, tenant, { route: decision.route, model: 'handoff_ack' });
    await sendReply(chatJid, handoffText, { instant: true });
    await persistOutbound({
      chatJid,
      text: handoffText,
      intent: decision.intent,
      model: 'handoff_ack',
      routeName: decision.route,
    });
    return;
  }

  if (decision.resume && (contact.human_handoff || contact.opted_out)) {
    await setContactFlags(chatJid, { humanHandoff: false });
    await updateConversationState(chatJid, { humanHandoff: false, optedOut: false, leadStatus: 'QUALIFYING' });
    await logEvent('handoff_off', chatJid, { pushName: message.metadata.push_name });
    console.log('[router] bot retomado por el usuario');
  } else if (contact.human_handoff) {
    await logEvent('held_for_human', chatJid, { preview: (text || '').slice(0, 200) });
    await updateConversationState(chatJid, { qualification, lastIntent: null });
    return;
  }

  if (decision.route === 'healthcheck') {
    const healthText = withContactFooter(decision.reply, tenant, { route: decision.route, model: 'healthcheck' });
    await sendReply(chatJid, healthText, { instant: true });
    await persistOutbound({ chatJid, text: healthText, model: 'healthcheck', routeName: decision.route });
    console.log(`[agent] ***${senderId.slice(-4)} route=healthcheck modelo=ping_pong`);
    return;
  }

  if (!decision.llm && decision.reply) {
    const metrics = { inboundAt: new Date(inboundAt), retrievalMs: 0, llmMs: 0, totalMs: Date.now() - inboundAt };
    await finalizeTurn({ chatJid, senderId, contact, decision, text, qualification, metrics });
    const instantText = withContactFooter(decision.reply, tenant, {
      route: decision.route,
      model: 'instant_rule',
    });
    await sendReply(chatJid, instantText, { instant: true });
    await persistOutbound({
      chatJid,
      text: instantText,
      intent: decision.intent,
      model: 'instant_rule',
      routeName: decision.route,
      metrics: { ...metrics, totalMs: Date.now() - inboundAt },
    });
    if (decision.hot) {
      await logEvent('hot_lead', chatJid, { phone: senderId, intent: decision.intent, preview: text.slice(0, 300) });
      console.log(`[agent] LEAD CALIENTE ***${senderId.slice(-4)} (${decision.intent})`);
    }
    return;
  }

  enqueue(message.conversation_id, async () => {
    const history = await recentMessages(chatJid, config.contextMessages);
    const counts = await countMessages(chatJid);

    if (!config.graphEnabled) {
      const { context, retrievalMs, hits } = await buildKnowledgeContext(text, { dir: knowledgeDirFor(tenant.id) });
      const summary = `estado=${contact.lead_status || 'NEW'} intent=${decision.intent || '-'} ${
        qualificationSummary(qualification) || 'sin datos de calificacion'
      } mensajes=${counts.inbound}`;
      const result = await generateReply({
        context,
        history,
        summary,
        qualification,
        suggestedQuestion: nextQuestion(qualification),
        lastUserText: text,
        knowledgeHits: hits.length,
        tenant,
      });
      const finalReply = withContactFooter(result.reply, tenant, { route: decision.route, model: result.model });
      await sendReply(chatJid, finalReply);
      const totalMs = Date.now() - inboundAt;
      await persistOutbound({
        chatJid,
        text: finalReply,
        intent: decision.intent,
        model: result.model,
        latencyMs: result.latencyMs,
        routeName: decision.route,
        metrics: { inboundAt: new Date(inboundAt), retrievalMs, llmMs: result.latencyMs, totalMs },
      });
      await finalizeTurn({
        chatJid, senderId, contact, decision, text, qualification,
        metrics: { model: result.model, retrievalMs, llmMs: result.latencyMs, totalMs },
      });
      return;
    }

    const stored = await loadConversationState(message.conversation_id);
    const state = normalizeState(stored, {
      conversation_id: message.conversation_id,
      tenant: tenant.id,
      phone: senderId,
    });

    const result = await runGraph({ state, text, tenant, history });
    const nextQualification = { ...(contact.qualification || {}), ...result.state.known_slots };
    const summary = `intents=${result.state.intents.join(',') || decision.intent || '-'} slots=${
      Object.keys(result.state.known_slots).length
    } missing=${result.state.missing_slots.length} mensajes=${counts.inbound}`;

    result.state.conversation_summary = summary;
    await saveConversationState(message.conversation_id, tenant.id, result.state);

    const finalReply = withContactFooter(result.reply, tenant, { route: decision.route, model: result.model });
    await sendReply(chatJid, finalReply);
    const totalMs = Date.now() - inboundAt;
    await persistOutbound({
      chatJid,
      text: finalReply,
      intent: result.state.intents.join(',') || decision.intent,
      model: result.model,
      latencyMs: result.llmMs,
      routeName: decision.route,
      metrics: { inboundAt: new Date(inboundAt), retrievalMs: result.retrievalMs, llmMs: result.llmMs, totalMs },
    });
    await finalizeTurn({
      chatJid, senderId, contact, decision, text, qualification: nextQualification,
      metrics: { model: result.model, retrievalMs: result.retrievalMs, llmMs: result.llmMs, totalMs },
      forceLead: result.action === 'create_lead',
      leadIntent: result.state.intents[0] || null,
    });
    if (decision.hot || result.action === 'create_lead') {
      await logEvent('hot_lead', chatJid, { phone: senderId, intent: decision.intent, preview: text.slice(0, 300) });
      console.log(`[agent] LEAD CALIENTE ***${senderId.slice(-4)} (${decision.intent})`);
    }
    console.log(
      `[graph] ***${senderId.slice(-4)} tenant=${tenant.id} branch=${result.branch} action=${result.action} ` +
        `intents=${result.state.intents.join(',') || '-'} missing=${result.state.missing_slots.length} ` +
        `next_slot=${result.nextSlot || '-'} modelo=${result.model} chunks=${result.hits.length} ` +
        `retrieval=${result.retrievalMs}ms llm=${result.llmMs}ms total=${totalMs}ms ` +
        `valid=${result.validation?.ok ? 'ok' : result.validation?.issues.join(',') || '-'}`
    );
  });
}

async function main() {
  installSignalGuard();
  console.log('=== AIF369 WhatsApp Agent (100% local) ===');
  setState(States.STARTING);

  await ensureSchema();
  console.log('[db] esquema listo');

  ollamaStatus = await ollamaReady();
  console.log(
    ollamaStatus
      ? `[ollama] ${config.ollama.model} listo en ${config.ollama.url}`
      : `[ollama] modelo ${config.ollama.model} no disponible; se usara mensaje de respaldo`
  );
  setInterval(async () => {
    ollamaStatus = await ollamaReady();
  }, 60000).unref();

  await loadKnowledge({ force: true });
  console.log(`[knowledge] ${JSON.stringify(getKnowledgeStats())}`);

  await startHealthServer(config.healthPort);
  await connect({ onMessage: handleInbound });
}

const shutdown = async () => {
  console.log('[agent] deteniendo...');
  try {
    await pool.end();
  } catch {}
  process.exit(0);
};

process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);

main().catch((err) => {
  setState(States.ERROR, err.message);
  console.error(`[agent] error fatal: ${err.stack || err}`);
  process.exit(1);
});

export { getState };
