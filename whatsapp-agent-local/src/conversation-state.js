import { getRegistry, slotQuestion, intentsFor } from './slot-registry.js';

export const NEXT_ACTIONS = [
  'ask_missing_slot',
  'answer_question',
  'retrieve_information',
  'create_lead',
  'request_contact_information',
  'handoff_human',
  'finish_workflow',
  'clarify_intent',
  'recover_conversation',
];

export const FRICTION_PATTERNS = [
  'ya te dije',
  'ya te lo dije',
  'ya lo dije',
  'ya te di ',
  'te acabo de decir',
  'ya te acabo de decir',
  'ya respondi',
  'ya respondí',
  'otra vez',
  'no me entiendes',
  'no me estas entendiendo',
  'no me estás entendiendo',
  'eso ya lo dije',
  'no me escuchas',
  'repites lo mismo',
  'lo mismo de antes',
];

const norm = (value) =>
  String(value || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

export function detectFriction(message) {
  const msg = norm(message);
  if (!msg) return false;
  return FRICTION_PATTERNS.some((p) => msg.includes(norm(p)));
}

export function createConversationState({ conversationId, tenant = 'aif369', phone = null } = {}) {
  return {
    conversation_id: conversationId,
    tenant,
    phone_number: phone,
    intents: [],
    known_slots: {},
    missing_slots: [],
    asked_slots: [],
    asked_counts: {},
    new_slots: [],
    confirmed_slots: [],
    added_intents: [],
    frustration_this_turn: false,
    rejection_this_turn: false,
    conversation_summary: '',
    friction_score: 0,
    frustration_detected: false,
    workflow: null,
    workflow_status: 'new',
    next_slot: null,
    next_action: null,
    last_user_message: '',
    last_assistant_message: '',
    message_count: 0,
    updated_at: null,
  };
}

export const normalizeState = (raw, fallback = {}) => {
  const src = raw || {};
  const base = createConversationState({
    conversationId: src.conversation_id || fallback.conversation_id || null,
    tenant: src.tenant || fallback.tenant || 'aif369',
    phone: src.phone_number || fallback.phone || null,
  });
  const state = { ...base, ...src };
  if (!Array.isArray(state.intents)) state.intents = [];
  if (!Array.isArray(state.asked_slots)) state.asked_slots = [];
  if (!Array.isArray(state.missing_slots)) state.missing_slots = [];
  if (!Array.isArray(state.new_slots)) state.new_slots = [];
  if (!Array.isArray(state.confirmed_slots)) state.confirmed_slots = [];
  if (!Array.isArray(state.added_intents)) state.added_intents = [];
  if (typeof state.asked_counts !== 'object' || !state.asked_counts) state.asked_counts = {};
  if (typeof state.frustration_this_turn !== 'boolean') state.frustration_this_turn = false;
  if (typeof state.rejection_this_turn !== 'boolean') state.rejection_this_turn = false;
  if (typeof state.known_slots !== 'object' || !state.known_slots) state.known_slots = {};
  return state;
};

const intentRecency = (state, intent) => state.intents.lastIndexOf(intent);

const fillRatio = (state, definition) => {
  if (!definition.required.length) return 1;
  const filled = definition.required.filter((k) => state.known_slots[k] !== undefined).length;
  return filled / definition.required.length;
};

export function activeIntents(state, registry = getRegistry(state.tenant)) {
  const present = (state.intents || []).filter((i) => registry.intents[i]);
  // 1) más avanzados primero, 2) mencionados más recientemente.
  return [...present].sort(
    (a, b) =>
      fillRatio(state, registry.intents[b]) - fillRatio(state, registry.intents[a]) ||
      intentRecency(state, b) - intentRecency(state, a)
  );
}

export function calcMissingSlots(state, registry = getRegistry(state.tenant)) {
  const missing = [];
  for (const intent of activeIntents(state, registry)) {
    for (const slot of registry.intents[intent].required) {
      if (state.known_slots[slot] === undefined && !missing.includes(slot)) missing.push(slot);
    }
  }
  return missing;
}

export function selectNextSlot(state, registry = getRegistry(state.tenant)) {
  const missing = state.missing_slots.length ? state.missing_slots : calcMissingSlots(state, registry);
  const asked = new Set(state.asked_slots || []);
  const unasked = missing.filter((s) => !asked.has(s));
  // Si ya preguntamos todo lo que falta, volvemos al primero (no bloquear la conversación).
  return unasked[0] || missing[0] || null;
}

export function validateQuestion(state, proposedSlot, registry = getRegistry(state.tenant)) {
  if (!proposedSlot) return false;
  if (state.known_slots[proposedSlot] !== undefined) return false;
  const asked = new Set(state.asked_slots || []);
  if (!asked.has(proposedSlot)) return true;
  const missing = state.missing_slots.length ? state.missing_slots : calcMissingSlots(state, registry);
  return !missing.some((s) => s !== proposedSlot && !asked.has(s));
}

export const salesReady = (state, registry = getRegistry(state.tenant)) => {
  const intents = activeIntents(state, registry);
  if (!intents.length) return false;
  return intents.every((i) =>
    registry.intents[i].required.every((s) => state.known_slots[s] !== undefined)
  );
};

export function determineNextAction(state, ctx = {}) {
  if (ctx.handoff) return 'handoff_human';
  if (ctx.rejection) return 'clarify_intent';
  if (ctx.frustrationThisTurn) return 'recover_conversation';
  if (ctx.isQuestion) return 'answer_question';
  if (ctx.contactRequested) return 'request_contact_information';
  if (state.missing_slots && state.missing_slots.length) return 'ask_missing_slot';
  if (salesReady(state, ctx.registry)) return 'create_lead';
  return 'retrieve_information';
}

export function applyExtraction(state, extraction = {}, registry = getRegistry(state.tenant)) {
  const next = { ...state, known_slots: { ...state.known_slots }, intents: [...state.intents] };
  const before = new Set(next.intents);

  for (const intent of extraction.new_intents || []) {
    if (registry.intents[intent] && !next.intents.includes(intent)) next.intents.push(intent);
  }

  const new_slots = [];
  for (const [key, value] of Object.entries(extraction.slots || {})) {
    if (!registry.slots[key]) continue;
    if (value === undefined || value === null || value === '') continue;
    if (next.known_slots[key] !== value) new_slots.push(key);
    next.known_slots[key] = value;
  }

  next.added_intents = next.intents.filter((i) => !before.has(i));
  next.new_slots = new_slots;
  next.confirmed_slots = (extraction.reconfirmed || []).filter(
    (key) => registry.slots[key] && next.known_slots[key] !== undefined
  );
  next.frustration_this_turn = Boolean(extraction.frustration);
  next.rejection_this_turn = Boolean(extraction.rejection);

  if (extraction.frustration) {
    next.friction_score = (next.friction_score || 0) + 1;
    next.frustration_detected = true;
    next.frustration_slot =
      new_slots[0] ||
      next.frustration_slot ||
      Object.keys(next.known_slots)[Object.keys(next.known_slots).length - 1] ||
      null;
  }

  if (next.intents.length) {
    next.workflow = 'sales';
    next.workflow_status = 'active';
  }

  next.missing_slots = calcMissingSlots(next, registry);
  next.next_slot = selectNextSlot(next, registry);
  return next;
}

export function markSlotAsked(state, slotKey) {
  if (!slotKey) return state;
  const asked = new Set(state.asked_slots || []);
  asked.add(slotKey);
  return { ...state, asked_slots: [...asked] };
}

export function stateSummary(state, registry = getRegistry(state.tenant)) {
  const parts = [];
  const intents = activeIntents(state, registry);
  if (intents.length) {
    const labels = intents.map((i) => registry.intents[i].label);
    parts.push(
      `el cliente busca ${labels.slice(0, -1).join(', ')}${labels.length > 1 ? ' y ' : ''}${
        labels[labels.length - 1]
      }`
    );
  }
  const known = Object.entries(state.known_slots || {});
  if (known.length) {
    parts.push(
      `datos ya entregados: ${known
        .map(([k, v]) => `${registry.slots[k]?.label || k}=${v}`)
        .join(', ')}`
    );
  }
  if (state.asked_slots?.length) {
    parts.push(`ya se preguntó: ${state.asked_slots.join(', ')}`);
  }
  if (state.friction_score > 0) parts.push(`molestia del cliente detectada ${state.friction_score} vez/veces`);
  return parts.length ? `ESTADO DE LA CONVERSACION: ${parts.join('; ')}.` : '';
}

export const renderSlot = (registry, key, value) => {
  const def = registry.slots[key];
  if (def && typeof def.render === 'function') return def.render(value);
  if (def && def.type === 'area') return `${value} m²`;
  if (def && def.type === 'bool') return value ? 'sí' : 'no';
  return String(value);
};

const cmp = (value) =>
  String(value || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

// Slot que todavia estamos esperando: la ultima pregunta sin respuesta (o la siguiente).
export function pendingSlotFor(state, registry = getRegistry(state.tenant)) {
  const asked = state.asked_slots || [];
  for (let i = asked.length - 1; i >= 0; i -= 1) {
    const key = asked[i];
    if (registry.slots[key] && state.known_slots[key] === undefined) return key;
  }
  const next = state.next_slot;
  if (next && registry.slots[next] && state.known_slots[next] === undefined) return next;
  return null;
}

// Hecho conocido que se puede reconocer sin repetir todo el resumen.
function knownFact(registry, state) {
  const entries = Object.entries(state.known_slots || {}).filter(([, v]) => v !== '' && v !== undefined && v !== null);
  if (!entries.length) return null;
  const msg = cmp(state.last_user_message);
  const has = ([, v]) => cmp(v).length >= 4 && msg.includes(cmp(v));
  const frustrationKey = state.frustration_slot;
  const order = [
    ...entries.filter(has),
    ...entries.filter(([k]) => k === frustrationKey),
    ...entries.filter(([k, v]) => k !== frustrationKey && cmp(v).length >= 4),
    ...entries.filter(([k]) => k !== frustrationKey),
  ];
  for (const [key, raw] of order) {
    const rendered = String(renderSlot(registry, key, raw)).replace(/[?¿]/g, '').replace(/\s+/g, ' ').trim();
    if (cmp(rendered).includes(cmp(raw).slice(0, 18))) return rendered.slice(0, 80);
  }
  return String(order[0][1]).slice(0, 80);
}

// Respuesta determinista de la rama "sales": solo comenta lo nuevo y pregunta lo que falta.
// Cada turno se arma desde lo que cambio ahora, asi nunca repite la misma frase.
export function composeMissingSlotReply(state, registry = getRegistry(state.tenant), question = null) {
  const parts = [];

  const labels = (state.added_intents || [])
    .map((i) => registry.intents[i]?.label)
    .filter(Boolean);
  if (labels.length === 1) parts.push(`Entonces buscas ${labels[0]}.`);
  else if (labels.length > 1) {
    parts.push(`Entonces buscas ${labels.slice(0, -1).join(', ')} y además ${labels[labels.length - 1]}.`);
  }

  let ackFact = null;
  if (state.frustration_this_turn) {
    ackFact = knownFact(registry, state);
    parts.push(ackFact ? `Disculpa, ya me habías dicho ${ackFact}.` : 'Disculpa si no me expliqué bien.');
  }

  const required = new Set(activeIntents(state, registry).flatMap((i) => registry.intents[i].required));
  const seen = new Set();
  const facts = [];
  const ordered = (state.new_slots || []).slice().sort((a, b) => (required.has(b) ? 1 : 0) - (required.has(a) ? 1 : 0));
  for (const key of ordered) {
    const def = registry.slots[key];
    const label = def?.label || key;
    const value = String(renderSlot(registry, key, state.known_slots[key]))
      .replace(/[?¿]/g, '')
      .replace(/\s+/g, ' ')
      .trim();
    if (!value || seen.has(cmp(value))) continue;
    seen.add(cmp(value));
    facts.push(`${label}: ${value}`.slice(0, 90));
    if (facts.length >= 3) break;
  }
  if (facts.length) parts.push(`Perfecto, anoto ${facts.join('; ')}.`);

  const confirmed = (state.confirmed_slots || [])
    .filter((key) => !(state.new_slots || []).includes(key))
    .map((key) => ({
      key,
      rendered: String(renderSlot(registry, key, state.known_slots[key]))
        .replace(/[?¿]/g, '')
        .replace(/\s+/g, ' ')
        .trim(),
    }))
    .filter(({ rendered }) => !(ackFact && cmp(ackFact).includes(cmp(rendered))))
    .slice(0, 2)
    .map(({ key, rendered }) => `${registry.slots[key]?.label || key}: ${rendered}`.slice(0, 90));
  if (confirmed.length) parts.push(`Perfecto, ${confirmed.join('; ')} ya lo tengo.`);

  const head = parts.join(' ').replace(/\s+/g, ' ').trim();
  if (!head) return question ? String(question).trim() : 'Entendido.';
  if (!question) return head;
  return `${head} ${String(question).trim()}`;
}

// Rechazo del usuario: nunca insistir; ofrecer continuar o pasar a una persona.
export function composeClarifyReply(state, registry = getRegistry(state.tenant), tenant = {}) {
  const name = tenant.name || 'el equipo';
  return `Disculpa si me pasé con las preguntas. ¿Seguimos por aquí o prefiero que te derive con una persona de ${name}?`;
}

// Lead completo: si falta el contacto se pide; si no, se cierra con la propuesta.
export function composeCreateLeadReply(state, registry = getRegistry(state.tenant), tenant = {}) {
  const intents = activeIntents(state, registry);
  const label = intents.length ? registry.intents[intents[0]].label : 'tu caso';
  const required = new Set(intents.flatMap((i) => registry.intents[i].required));
  const keys = Object.keys(state.known_slots || {}).filter((k) => registry.slots[k]);
  const facts = [...keys.filter((k) => required.has(k)), ...keys.filter((k) => !required.has(k))]
    .slice(0, 3)
    .map((k) => registry.slots[k].label || k);
  const base = facts.length
    ? `Perfecto, con ${facts.slice(0, -1).join(', ')}${facts.length > 1 ? ' y ' : ''}${
        facts[facts.length - 1]
      } ya tengo lo necesario para ${label}.`
    : `Perfecto, ya tengo lo necesario para ${label}.`;

  const contact = registry.slots.contacto;
  const asked = new Set(state.asked_slots || []);
  if (contact && state.known_slots.contacto === undefined && !asked.has('contacto')) {
    const times = state.asked_counts?.contacto || 0;
    return `${base} ${slotQuestion(registry, 'contacto', [], times)}`.trim();
  }
  return `${base} Preparo la propuesta y te aviso por aquí.`;
}

export function nextQuestionFor(state, registry = getRegistry(state.tenant)) {
  const slot = state.next_slot;
  if (!slot || !validateQuestion(state, slot, registry)) return null;
  return slotQuestion(registry, slot, state.asked_slots || [], state.asked_counts?.[slot]);
}

export { slotQuestion, intentsFor };
