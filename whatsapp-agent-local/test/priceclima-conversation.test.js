import { test } from 'node:test';
import assert from 'node:assert/strict';
import { runGraph } from '../src/graph.js';
import { createConversationState } from '../src/conversation-state.js';
import { extractDeterministic } from '../src/extract.js';
import { getRegistry } from '../src/slot-registry.js';
import { getTenant } from '../src/tenants.js';

const registry = getRegistry('priceclima');
const tenant = getTenant('priceclima');
const questions = (text) => (String(text).match(/\?/g) || []).length;

// El transcript que fallo en la prueba manual: 8 mensajes de climatizacion.
const TRANSCRIPT = [
  'Me dijeron que también instalan aire acondicionado',
  'Marca Daikin',
  'Un dormitorio',
  'Es un dormitorio normal',
  'Hace calor en verano',
  '¿Tienen para dormitorio?',
  'Me interesa la mantención',
  'Ya te dije que es un dormitorio',
];

const badGenerate = async () => ({
  reply: 'Tenemos varias opciones. ¿Qué garantía tienen? ¿Cuántos equipos son en total?',
  model: 'ollama',
  latencyMs: 1,
  ok: true,
});

async function replay(generate = badGenerate) {
  let state = createConversationState({ conversationId: 'wa:test', tenant: tenant.id });
  const out = [];
  for (const text of TRANSCRIPT) {
    const result = await runGraph({
      state,
      text,
      tenant,
      history: out.map((r) => ({ direction: 'in', body: r.text })),
      deps: { generate },
    });
    state = result.state;
    out.push({ text, result, state });
  }
  return out;
}

test('extraction determinista: no inventa comuna ni slot de otro intent', () => {
  const loc = extractDeterministic('Hace calor en verano', registry, {}, ['air_conditioning_installation']);
  assert.equal(loc.slots['customer.location'], undefined);
  assert.equal(loc.slots['installation.climate'], 'calor_en_verano');

  const brand = extractDeterministic('Marca Daikin', registry, {}, ['air_conditioning_installation']);
  assert.equal(brand.slots['installation.brand'], 'daikin');
  assert.equal(brand.slots['maintenance.brand'], undefined);

  const qty = extractDeterministic('Necesito 3 equipos', registry, {}, ['air_conditioning_installation']);
  assert.equal(qty.slots['installation.quantity'], 3);

  const m2 = extractDeterministic('Son como 3 x 4 metros', registry, {}, ['air_conditioning_installation']);
  assert.equal(m2.slots['installation.room_size_m2'], 12);
});

test('transcript de climatizacion: estado, intents y siguiente slot', async () => {
  const out = await replay();
  const [, m2, m3, , m5] = out;

  assert.deepEqual(m2.state.intents, ['air_conditioning_installation']);
  assert.equal(m2.state.known_slots['installation.brand'], 'daikin');
  assert.equal(m2.state.next_slot, 'installation.room_type');
  assert.equal(m3.state.known_slots['installation.room_type'], 'dormitorio');
  assert.equal(m3.state.next_slot, 'installation.room_size_m2');

  // El bug original: "hace calor en verano" no puede responder la pregunta de m2.
  assert.equal(m5.state.known_slots['installation.climate'], 'calor_en_verano');
  assert.notEqual(m5.state.next_slot, 'installation.climate');
  assert.equal(m5.state.known_slots['customer.location'], undefined);

  assert.ok(m5.result.reply.includes('calor en verano'));
  assert.equal(m5.state.asked_slots.includes('installation.room_size_m2'), true);
});

test('transcript: mantencion agrega un segundo intent sin perder el primero', async () => {
  const out = await replay();
  const m7 = out[6];
  assert.deepEqual(m7.state.intents, ['air_conditioning_installation', 'air_conditioning_maintenance']);
  assert.equal(m7.state.next_slot, 'maintenance.quantity');
  assert.ok(m7.result.reply.includes('mantención'));
});

test('transcript: la molestia se detecta y se reconoce el dato repetido', async () => {
  const out = await replay();
  const m8 = out[7];
  assert.equal(m8.state.frustration_detected, true);
  assert.equal(m8.result.action, 'recover_conversation');
  assert.equal(m8.result.model, 'state_machine');
  assert.ok(m8.result.reply.includes('ya me habías dicho un dormitorio'), m8.result.reply);
  assert.doesNotMatch(m8.result.reply, /no lo repitas/i, 'tono reprochador');
  assert.doesNotMatch(m8.result.reply, /Ya me diste ese dato/, 'mensaje rudo viejo');
});

test('validador: una sola pregunta por respuesta y sin preguntar lo conocido', async () => {
  const out = await replay();
  for (const { result } of out) {
    assert.equal(questions(result.reply), 1, `mas de una pregunta: ${result.reply}`);
    assert.ok(result.validation?.ok, `validacion fallida: ${result.validation?.issues.join(',')}`);
    assert.equal(result.reply.includes('$'), false, 'precio fuera del conocimiento');
  }
});

test('validador: reintenta con nota y si no cae a respuesta determinista', async () => {
  let calls = 0;
  const out = await replay(async () => {
    calls += 1;
    return badGenerate();
  });
  assert.ok(calls >= 2, 'el validador reintento antes de rendirse');
  for (const { result } of out) {
    if (result.branch === 'faq') assert.equal(result.model, 'state_machine');
  }
});

test('generador correcto pasa el validador sin caer a determinista', async () => {
  const out = await replay(async ({ suggestedQuestion }) => ({
    reply: `Sí, tenemos equipos Clark y Midea con instalación en terreno. ${
      suggestedQuestion || '¿Cuántos equipos necesitas?'
    }`,
    model: 'ollama',
    latencyMs: 2,
    ok: true,
  }));
  const faq = out.find(({ result }) => result.branch === 'faq');
  assert.equal(faq.result.model, 'ollama');
  assert.equal(faq.result.validation.ok, true);
  assert.equal(questions(faq.result.reply), 1);
});

test('el modelo siempre recibe el mensaje actual en el historial', async () => {
  let seen = null;
  let state = createConversationState({ conversationId: 'wa:hist', tenant: tenant.id });
  await runGraph({
    state,
    text: '¿Qué servicios ofrecen?',
    tenant,
    history: [],
    deps: {
      generate: async (payload) => {
        seen = payload.history;
        return { reply: 'Ok. ¿Cuántos equipos necesitas instalar?', model: 'ollama', latencyMs: 1, ok: true };
      },
    },
  });
  assert.equal(seen[seen.length - 1].body, '¿Qué servicios ofrecen?');
  assert.equal(seen[seen.length - 1].direction, 'in');
  assert.equal(seen.filter((r) => r.body === '¿Qué servicios ofrecen?').length, 1, 'mensaje duplicado');

  // Si el historial ya trae el mensaje (caso de index.js), no se duplica.
  let seen2 = null;
  await runGraph({
    state,
    text: '¿Qué servicios ofrecen?',
    tenant,
    history: [{ direction: 'in', body: '¿Qué servicios ofrecen?' }],
    deps: {
      generate: async (payload) => {
        seen2 = payload.history;
        return { reply: 'Ok.', model: 'ollama', latencyMs: 1, ok: true };
      },
    },
  });
  assert.equal(seen2.filter((r) => r.body === '¿Qué servicios ofrecen?').length, 1);
});
