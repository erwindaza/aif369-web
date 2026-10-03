import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  validateResponse,
  repairHint,
  deterministicReply,
  priceSummary,
  PRICE_QUESTION_RE,
} from '../src/response-validator.js';
import { getRegistry } from '../src/slot-registry.js';

const registry = getRegistry('aif369');
const CONTEXT =
  'Starter 369 $3,000 USD por 6 meses con diagnóstico de 1–2 semanas. Governed Pilot 369 $6,000 USD por año. Enterprise 369 $9,000+ USD por año.';

const base = {
  registry,
  context: CONTEXT,
  question: null,
  expectQuestion: false,
  state: { known_slots: {}, asked_slots: [], tenant: 'aif369' },
};

test('precio preguntado sin montos en la respuesta: falla', () => {
  const bad = validateResponse({
    ...base,
    reply: '¡Hola! Tenemos soluciones increíbles para empresas.',
    lastUserText: '¿Y precios tienes?',
  });
  assert.ok(bad.issues.includes('prices_not_cited'), bad.issues.join(','));
  assert.match(repairHint({ issues: bad.issues }), /precios/);

  const good = validateResponse({
    ...base,
    reply: 'El Starter 369 cuesta $3,000 USD por 6 meses.',
    lastUserText: '¿Y precios tienes?',
  });
  assert.ok(!good.issues.includes('prices_not_cited'), good.issues.join(','));
  assert.equal(good.ok, true, good.issues.join(','));
});

test('un monto con otro separador no se marca como inventado', () => {
  const out = validateResponse({
    ...base,
    reply: 'Starter 369 cuesta $3.000 USD por 6 meses.',
    lastUserText: '¿Cuánto cuesta?',
  });
  assert.ok(!out.issues.includes('invented_price'), out.issues.join(','));
});

test('monto que no esta en el conocimiento sigue marcado', () => {
  const out = validateResponse({
    ...base,
    reply: 'Solo USD $250 por proyecto.',
    lastUserText: '¿Y precios?',
  });
  assert.ok(out.issues.includes('invented_price'), out.issues.join(','));
});

test('resumen de precios determinista usa solo frases del conocimiento', () => {
  const none = priceSummary(CONTEXT, []);
  assert.equal(none, null, 'sin la falla no interfiere');
  const summary = priceSummary(CONTEXT, ['prices_not_cited']);
  assert.match(summary, /3,000 USD/);
  assert.match(summary, /6,000 USD/);
  assert.equal(PRICE_QUESTION_RE.test('¿Cuánto vale?'), true);
  assert.equal(PRICE_QUESTION_RE.test('Un dormitorio'), false);
});

test('respuesta determinista segun la accion: clarify y create_lead no inventan', () => {
  const clarify = deterministicReply({
    state: { ...base.state, next_action: 'clarify_intent' },
    registry,
    question: '¿En que empresa trabajas?',
  });
  assert.match(clarify, /derive con una persona/);

  const lead = deterministicReply({
    state: { ...base.state, next_action: 'create_lead' },
    registry,
    question: null,
  });
  assert.match(lead, /propuesta|contacto/i);
  assert.equal((lead.match(/\?/g) || []).length <= 1, true, lead);
});
