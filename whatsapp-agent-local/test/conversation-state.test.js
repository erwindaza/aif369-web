import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  createConversationState,
  normalizeState,
  detectFriction,
  calcMissingSlots,
  selectNextSlot,
  validateQuestion,
  determineNextAction,
  salesReady,
  applyExtraction,
} from '../src/conversation-state.js';
import { getRegistry } from '../src/slot-registry.js';

const priceclima = getRegistry('priceclima');
const aif369 = getRegistry('aif369');

test('detectFriction reconoce molestia explicita', () => {
  assert.equal(detectFriction('Ya te dije que es un dormitorio'), true);
  assert.equal(detectFriction('Otra vez lo mismo'), true);
  assert.equal(detectFriction('Un dormitorio normal'), false);
});

test('missing slots siguen el orden del intent activo', () => {
  const state = applyExtraction(
    createConversationState({ conversationId: 'c1', tenant: 'priceclima' }),
    { new_intents: ['air_conditioning_installation'], slots: { 'installation.room_type': 'dormitorio' } },
    priceclima
  );
  assert.deepEqual(state.missing_slots, [
    'installation.quantity',
    'installation.room_size_m2',
    'customer.location',
  ]);
  assert.equal(state.next_slot, 'installation.quantity');
});

test('next_slot salta los slots ya preguntados', () => {
  const state = applyExtraction(
    createConversationState({ conversationId: 'c2', tenant: 'priceclima' }),
    { new_intents: ['air_conditioning_installation'], slots: { 'installation.room_type': 'dormitorio' } },
    priceclima
  );
  assert.deepEqual(state.missing_slots, [
    'installation.quantity',
    'installation.room_size_m2',
    'customer.location',
  ]);
  assert.equal(selectNextSlot({ ...state, asked_slots: ['installation.room_size_m2'] }, priceclima), 'installation.quantity');
  assert.equal(selectNextSlot({ ...state, asked_slots: ['installation.quantity'] }, priceclima), 'installation.room_size_m2');
  // Todo lo que falta ya fue preguntado: se permite volver al primero (no bloquear).
  assert.equal(
    selectNextSlot(
      { ...state, asked_slots: ['installation.quantity', 'installation.room_size_m2', 'customer.location'] },
      priceclima
    ),
    'installation.quantity'
  );
});

test('validateQuestion bloquea datos ya conocidos y preguntas repetidas', () => {
  const state = applyExtraction(
    createConversationState({ conversationId: 'c3', tenant: 'priceclima' }),
    { new_intents: ['air_conditioning_installation'], slots: { 'installation.room_type': 'dormitorio' } },
    priceclima
  );
  assert.equal(validateQuestion(state, 'installation.room_type', priceclima), false);
  assert.equal(validateQuestion(state, 'installation.quantity', priceclima), true);

  const asked = { ...state, asked_slots: ['installation.room_size_m2'] };
  assert.equal(validateQuestion(asked, 'installation.room_size_m2', priceclima), false);
  assert.equal(validateQuestion(asked, 'customer.location', priceclima), true);
  assert.equal(validateQuestion(asked, 'installation.room_type', priceclima), false);
});

test('determineNextAction prioriza friccion y pregunta antes de crear lead', () => {
  const state = applyExtraction(
    createConversationState({ conversationId: 'c4', tenant: 'priceclima' }),
    { new_intents: ['air_conditioning_installation'], slots: {} },
    priceclima
  );
  assert.equal(
    determineNextAction(state, { frustrationThisTurn: true, isQuestion: false, registry: priceclima }),
    'recover_conversation'
  );
  assert.equal(
    determineNextAction(state, { isQuestion: true, registry: priceclima }),
    'answer_question'
  );
  assert.equal(
    determineNextAction(state, { isQuestion: false, registry: priceclima }),
    'ask_missing_slot'
  );
});

test('salesReady exige los slots requeridos de todos los intents activos', () => {
  const state = applyExtraction(
    createConversationState({ conversationId: 'c5', tenant: 'priceclima' }),
    {
      new_intents: ['air_conditioning_installation', 'air_conditioning_maintenance'],
      slots: {
        'installation.quantity': 1,
        'installation.room_type': 'dormitorio',
        'installation.room_size_m2': 12,
        'customer.location': 'Providencia',
        'maintenance.quantity': 1,
      },
    },
    priceclima
  );
  assert.equal(salesReady(state, priceclima), true);

  const missing = applyExtraction(
    createConversationState({ conversationId: 'c6', tenant: 'priceclima' }),
    { new_intents: ['air_conditioning_installation'], slots: { 'installation.room_type': 'dormitorio' } },
    priceclima
  );
  assert.equal(salesReady(missing, priceclima), false);
});

test('normalizeState restaura estructura desde JSON guardado', () => {
  const raw = JSON.parse(
    JSON.stringify({
      conversation_id: 'wa:1',
      tenant: 'priceclima',
      intents: ['air_conditioning_installation'],
      known_slots: { 'installation.room_type': 'dormitorio' },
      asked_slots: ['installation.quantity'],
    })
  );
  const state = normalizeState(raw, { conversation_id: 'wa:1', tenant: 'priceclima' });
  assert.equal(state.tenant, 'priceclima');
  assert.deepEqual(state.missing_slots, []);
  assert.equal(state.message_count, 0);
  assert.deepEqual(state.intents, ['air_conditioning_installation']);
});

test('registro aif369 mantiene los campos de calificacion', () => {
  assert.deepEqual(aif369.intents.data_ai_project.required, ['empresa', 'problema', 'fuentes']);
  const state = applyExtraction(
    createConversationState({ conversationId: 'c7', tenant: 'aif369' }),
    { new_intents: ['data_ai_project'], slots: { empresa: 'ACME', fuentes: 'excel,sap' } },
    aif369
  );
  assert.deepEqual(state.missing_slots, ['problema']);
  assert.equal(state.next_slot, 'problema');
});
