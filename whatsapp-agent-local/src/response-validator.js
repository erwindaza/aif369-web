import { getRegistry, slotQuestion } from './slot-registry.js';
import { validateQuestion, composeMissingSlotReply, composeClarifyReply, composeCreateLeadReply } from './conversation-state.js';
import { getTenant } from './tenants.js';

const norm = (value) =>
  String(value || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

export const extractQuestion = (text) => {
  const match = String(text || '').match(/[^.!?]*\?/g);
  if (!match) return null;
  const last = match[match.length - 1].trim();
  return last || null;
};

const countQuestions = (text) => (String(text || '').match(/\?/g) || []).length;

const extractPrices = (text) => String(text || '').match(/\$\s?\d(?:[\d.,]*\d)?/g) || [];

// El usuario pregunto por plata: la respuesta debe citar montos del conocimiento.
export const PRICE_QUESTION_RE =
  /(precio|precios|cu[aá]nto (cuesta|vale|salen)|cu[aá]nto es|costo|costos|cotiz|presupuesto|tarifa|valen)/i;

const PRICE_VALUE_RE = /\$\s?\d/;

const slotForQuestion = (question, registry, state) => {
  const q = norm(question);
  if (!q) return null;
  for (const [key, def] of Object.entries(registry.slots)) {
    for (const ask of def.ask || []) {
      if (norm(ask) === q) return key;
    }
  }
  for (const [key, def] of Object.entries(registry.slots)) {
    if (q.includes(norm(def.label))) return key;
  }
  for (const [key, def] of Object.entries(registry.slots)) {
    if (q.includes(norm(key.split('.').pop().replace(/_/g, ' ')))) return key;
  }
  if (state) return null;
  return null;
};

// Validador deterministico: se ejecuta SIEMPRE antes de enviar por WhatsApp.
export function validateResponse({
  state,
  reply,
  registry,
  question = null,
  context = '',
  expectQuestion = false,
  lastUserText = '',
}) {
  const reg = registry || getRegistry(state?.tenant);
  const text = String(reply || '').trim();
  const issues = [];

  if (!text) issues.push('empty');
  if (countQuestions(text) > 1) issues.push('multiple_questions');

  const asked = extractQuestion(text);
  if (asked) {
    const slot = slotForQuestion(asked, reg, state);
    if (slot) {
      if (state.known_slots[slot] !== undefined) issues.push('question_about_known_slot');
      else if (state.asked_slots.includes(slot) && !validateQuestion(state, slot, reg)) {
        issues.push('repeated_question');
      }
    }
  }

  if (expectQuestion && question) {
    if (!norm(text).includes(norm(question))) issues.push('missing_next_question');
  }

  const priceKey = (p) => norm(p).replace(/(\d),(\d)/g, '$1.$2');
  const contextPrices = new Set(extractPrices(context).map(priceKey));
  for (const price of extractPrices(text)) {
    if (!contextPrices.has(priceKey(price))) {
      issues.push('invented_price');
      break;
    }
  }

  if (
    lastUserText &&
    PRICE_QUESTION_RE.test(lastUserText) &&
    contextPrices.size > 0 &&
    !PRICE_VALUE_RE.test(text)
  ) {
    issues.push('prices_not_cited');
  }

  if (state?.frustration_detected && state.friction_score > 0 && state.next_action === 'recover_conversation') {
    const known = Object.entries(state.known_slots || {});
    const echoed = known.some(([, v]) => norm(text).includes(norm(String(v)).slice(0, 18)));
    if (known.length && !echoed) issues.push('friction_not_acknowledged');
  }

  return { ok: issues.length === 0, issues, question: asked };
}

export function repairHint({ issues, question }) {
  const fixes = [];
  if (issues.includes('multiple_questions')) fixes.push('haz UNA sola pregunta');
  if (issues.includes('question_about_known_slot')) fixes.push('no preguntes por datos que ya te dieron');
  if (issues.includes('repeated_question')) fixes.push('no repitas una pregunta ya hecha');
  if (issues.includes('missing_next_question') && question) {
    fixes.push(`termina EXACTAMENTE con: "${question}"`);
  }
  if (issues.includes('invented_price')) fixes.push('no menciones precios que no estén en el conocimiento');
  if (issues.includes('prices_not_cited')) {
    fixes.push('el cliente preguntó por precios: cita los montos del CONOCIMIENTO con su periodo (ej. $3,000 USD por 6 meses)');
  }
  if (issues.includes('friction_not_acknowledged')) fixes.push('reconoce primero lo que ya te dijo el cliente');
  if (!fixes.length) fixes.push('responde de nuevo, corto y con una sola pregunta');
  return fixes.join('; ');
}

// Si el modelo no citó montos, se arman frases del conocimiento (no se inventa nada).
export function priceSummary(context = '', issues = []) {
  if (!issues.includes('prices_not_cited')) return null;
  const sentences = String(context || '')
    .split(/(?<=[.!?])\s+|\n+/)
    .map((s) => s.replace(/\s+/g, ' ').trim())
    .filter((s) => PRICE_VALUE_RE.test(s) && s.length >= 10 && s.length <= 300);
  if (!sentences.length) return null;
  return sentences.slice(0, 2).join(' ');
}

// Último recurso: respuesta 100% determinista (nunca inventa).
export function deterministicReply({ state, registry, question, contextNote = '' }) {
  const reg = registry || getRegistry(state?.tenant);
  const action = state?.next_action;
  const reply =
    action === 'clarify_intent'
      ? composeClarifyReply(state, reg, getTenant(state?.tenant))
      : action === 'create_lead'
        ? composeCreateLeadReply(state, reg, getTenant(state?.tenant))
        : composeMissingSlotReply(state, reg, question);
  return contextNote ? `${reply} ${contextNote}`.trim() : reply;
}

export { slotQuestion };
