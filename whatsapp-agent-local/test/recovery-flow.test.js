import { test } from 'node:test';
import assert from 'node:assert/strict';
import { runGraph } from '../src/graph.js';
import { extractDeterministic, detectRejection } from '../src/extract.js';
import { createConversationState, applyExtraction } from '../src/conversation-state.js';
import { getRegistry, slotQuestion } from '../src/slot-registry.js';
import { getTenant } from '../src/tenants.js';
import { route } from '../src/router.js';
import { CONTACT_TRIGGER } from '../src/contact.js';

const aif = getTenant('aif369');
const clim = getTenant('priceclima');
const aifReg = getRegistry('aif369');
const climReg = getRegistry('priceclima');

// Solo reglas: sin llamadas al modelo en los tests.
const rulesExtract = async (args) =>
  extractDeterministic(args.text, args.registry, args.currentSlots, args.activeIntents, args.pendingSlot);

const canaryGenerate = () => {
  const box = { calls: 0 };
  box.fn = async () => {
    box.calls += 1;
    return { reply: 'No deberia usarme. ¿Cuántos equipos necesitas?', model: 'ollama', latencyMs: 1 };
  };
  return box;
};

test('peticion de manager/gerente activa handoff humano', () => {
  for (const text of ['Dame con tu manager', 'Quiero hablar con tu jefe', 'Me atiende una persona real?']) {
    const d = route({ text, conversation_id: 'wa:t' }, { tenant: aif });
    assert.equal(d.intent, 'HUMAN', text);
    assert.equal(d.handoff, true, text);
    assert.equal(d.llm, false, text);
  }
});

test('rechazo: el usuario frena la direccion y se ofrece derivar sin insistir', async () => {
  const gen = canaryGenerate();
  let state = applyExtraction(
    createConversationState({ conversationId: 'wa:rej', tenant: 'priceclima' }),
    { new_intents: ['air_conditioning_installation'], slots: {} },
    climReg
  );
  state = { ...state, asked_slots: ['customer.location'] };

  const result = await runGraph({
    state,
    text: 'No yo solo quiero un aire acondicionado',
    tenant: clim,
    history: [],
    deps: { extract: rulesExtract, generate: gen.fn },
  });

  assert.equal(detectRejection('No yo solo quiero un aire acondicionado'), true);
  assert.equal(result.action, 'clarify_intent');
  assert.equal(result.model, 'state_machine');
  assert.equal(gen.calls, 0, 'sin LLM en la respuesta de clarification');
  assert.match(result.reply, /derive con una persona/);
  assert.equal((result.reply.match(/\?/g) || []).length, 1, result.reply);
  assert.ok(result.validation.ok, result.validation.issues.join(','));
});

test('atribucion: la respuesta de texto va al slot que estaba preguntado', () => {
  const run = (text, pending, current = {}) =>
    extractDeterministic(text, aifReg, current, ['data_ai_project'], pending);

  assert.equal(run('De parte de bejoby', 'empresa').slots.empresa, 'bejoby');
  assert.equal(run('soy de la empresa bejoby', 'empresa').slots.empresa, 'bejoby');

  const problema = run('Necesito la arquitectura medallion para pasarle a una ia', 'problema');
  assert.match(problema.slots.problema, /arquitectura medallion/);

  assert.equal(run('Un etl', 'fuentes').slots.fuentes, 'Un etl');

  // Respuestas que no son datos no rellenan nada.
  assert.equal(run('Si', 'empresa').slots.empresa, undefined);
  assert.equal(run('¿Qué onda?', 'problema').slots.problema, undefined);
  // Si el mensaje responde otro campo requerido, no se lo damos al pendiente.
  const otro = run('Somos de ACME', 'problema');
  assert.equal(otro.slots.empresa, 'ACME');
  assert.equal(otro.slots.problema, undefined);
});

test('atribucion: en priceclima una falla sin patron va al slot de problema', () => {
  const out = extractDeterministic(
    'Se apaga sola cuando calienta',
    climReg,
    { 'maintenance.quantity': 1 },
    ['air_conditioning_maintenance'],
    'maintenance.problem'
  );
  assert.equal(out.slots['maintenance.problem'], 'Se apaga sola cuando calienta');

  // Si el mensaje extrajo otro slot del mismo intento, no atribuimos.
  const otro = extractDeterministic(
    'Hace calor en verano',
    climReg,
    {},
    ['air_conditioning_installation'],
    'customer.location'
  );
  assert.equal(otro.slots['customer.location'], undefined);
  assert.equal(otro.slots['installation.climate'], 'calor_en_verano');
});

test('sin datos nuevos la respuesta no repite el mismo resumen', async () => {
  const gen = canaryGenerate();
  let state = createConversationState({ conversationId: 'wa:rep', tenant: 'priceclima' });

  const first = await runGraph({
    state,
    text: 'Me interesa instalar aire acondicionado',
    tenant: clim,
    history: [],
    deps: { extract: rulesExtract, generate: gen.fn },
  });
  state = first.state;
  const second = await runGraph({
    state,
    text: 'Dale',
    tenant: clim,
    history: [],
    deps: { extract: rulesExtract, generate: gen.fn },
  });

  assert.match(first.reply, /Entonces buscas instalación de aire acondicionado/);
  assert.ok(!second.reply.includes('Entonces buscas'), second.reply);
  assert.ok(!second.reply.includes(first.reply.split('?')[0]), 'frase identica repetida');
  assert.equal(gen.calls, 0);
});

test('la molestia solo se reconoce ese turno, no queda en cada respuesta', async () => {
  const gen = canaryGenerate();
  let state = applyExtraction(
    createConversationState({ conversationId: 'wa:tone', tenant: 'priceclima' }),
    { new_intents: ['air_conditioning_installation'], slots: { 'installation.brand': 'daikin' } },
    climReg
  );
  state = { ...state, asked_slots: ['installation.room_type'] };

  const friction = await runGraph({
    state,
    text: 'Ya te dije que es un dormitorio',
    tenant: clim,
    history: [],
    deps: { extract: rulesExtract, generate: gen.fn },
  });
  assert.equal(friction.action, 'recover_conversation');
  assert.match(friction.reply, /ya me habías dicho/i);
  assert.doesNotMatch(friction.reply, /no lo repitas/i);

  const calm = await runGraph({
    state: friction.state,
    text: 'Necesito instalarlo en Providencia',
    tenant: clim,
    history: [],
    deps: { extract: rulesExtract, generate: gen.fn },
  });
  assert.ok(!/Disculpa/i.test(calm.reply), calm.reply);
  assert.equal(gen.calls, 0);
});

test('lead completo: pide contacto una vez y despues cierra con la propuesta', async () => {
  const gen = canaryGenerate();
  const base = applyExtraction(
    createConversationState({ conversationId: 'wa:lead', tenant: 'aif369' }),
    {
      new_intents: ['data_ai_project'],
      slots: { empresa: 'ACME', problema: 'reportes que no cuadran', fuentes: 'excel,sap' },
    },
    aifReg
  );
  assert.equal(base.missing_slots.length, 0);

  const first = await runGraph({
    state: base,
    text: 'Perfecto, seguimos',
    tenant: aif,
    history: [],
    deps: { extract: rulesExtract, generate: gen.fn },
  });
  assert.equal(first.action, 'create_lead');
  assert.equal(first.model, 'state_machine');
  assert.match(first.reply, /ya tengo lo necesario para proyecto de datos e IA/);
  assert.match(first.reply, /\?/, 'pregunta el contacto');
  assert.equal(first.state.asked_slots.includes('contacto'), true);
  assert.ok(first.validation.ok, first.validation.issues.join(','));

  const second = await runGraph({
    state: first.state,
    text: 'mi correo es gerencia@acme.cl',
    tenant: aif,
    history: [],
    deps: { extract: rulesExtract, generate: gen.fn },
  });
  assert.equal(second.action, 'create_lead');
  assert.equal(second.state.known_slots.contacto, 'gerencia@acme.cl');
  assert.match(second.reply, /Preparo la propuesta/);
  assert.doesNotMatch(second.reply, /\?/, 'no vuelve a preguntar el contacto');
  assert.equal(gen.calls, 0, 'el cierre es determinista, sin LLM');
});

test('el pie de contacto acompana pedidos de derivacion y humanos', () => {
  assert.equal(CONTACT_TRIGGER.test('¿Me derivas con una persona?'), true);
  assert.equal(CONTACT_TRIGGER.test('Quiero hablar con un humano'), true);
  assert.equal(CONTACT_TRIGGER.test('Solo una duda rápida'), false);
});

test('dato repetido: se confirma sin rellenar otro slot ni repetir la frase', async () => {
  const gen = canaryGenerate();
  let state = applyExtraction(
    createConversationState({ conversationId: 'wa:dup', tenant: 'aif369' }),
    { new_intents: ['data_ai_project'], slots: { empresa: 'bejoby' } },
    aifReg
  );
  state = { ...state, asked_slots: ['problema'] };

  const result = await runGraph({
    state,
    text: 'soy de la empresa bejoby',
    tenant: aif,
    history: [],
    deps: { extract: rulesExtract, generate: gen.fn },
  });

  assert.equal(result.state.known_slots.problema, undefined, 'la frase no es el problema');
  assert.match(result.reply, /empresa: bejoby ya lo tengo/, result.reply);
  assert.match(result.reply, /\?/, 'vuelve a preguntar lo que falta');
  assert.equal(result.state.asked_counts.fuentes, 1, 'cuenta las preguntas hechas');
  assert.equal(gen.calls, 0);
});

test('las preguntas rotan entre variantes cada vez que se repiten', () => {
  const reg = getRegistry('aif369');
  const first = slotQuestion(reg, 'problema', [], 0);
  const second = slotQuestion(reg, 'problema', ['problema'], 1);
  const third = slotQuestion(reg, 'problema', ['problema'], 2);
  assert.notEqual(first, second);
  assert.equal(first, third, 'vuelve a la primera variante');
});
