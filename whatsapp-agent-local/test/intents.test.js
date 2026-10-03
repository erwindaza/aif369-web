import test from 'node:test';
import assert from 'node:assert/strict';
import { detectIntent, INTENTS, wantsHuman, wantsOptOut, wantsBot, isStatusRequest, isHotLead } from '../src/intents.js';

const cases = [
  ['Hola', 'GREETING'],
  ['¿Qué servicios ofrece AIF369?', 'SERVICES'],
  ['Tengo SAP, Excel y PostgreSQL y quiero una fuente única de verdad.', 'INTEGRATION'],
  ['Tenemos un proyecto ETL detenido. ¿Pueden tomarlo y terminarlo?', 'PROJECT_RECOVERY'],
  ['Quiero cotizar.', 'QUOTE_REQUEST'],
  ['Quiero hablar con una persona.', 'HUMAN'],
  ['Hola, tengo una empresa y necesito integrar datos de Excel, PostgreSQL y un ERP para tener una sola fuente de verdad. ¿Ustedes hacen eso?', 'INTEGRATION'],
  ['necesito integrar SAP y Excel', 'INTEGRATION'],
  ['quiero automatizar ETLs', 'ETL_ELT'],
  ['tenemos reportes que no cuadran', 'DATA_AI'],
  ['queremos implementar IA', 'SERVICES'],
  ['tenemos un proyecto detenido', 'PROJECT_RECOVERY'],
  ['necesito un agente', 'AI_AGENT'],
  ['¿Trabajan con GCP y AWS?', 'SERVICES'],
  ['¿Pueden hacer agentes con IA?', 'AI_AGENT'],
  ['Quiero agendar una llamada', 'MEETING'],
  ['¿Qué es el gobierno de IA y la Ley 21.719?', 'GOVERNANCE'],
  ['no me interesa', 'OTHER'],
];

test('clasificador cubre los 12 intents del dominio', () => {
  assert.deepEqual(
    [...INTENTS].sort(),
    ['AI_AGENT', 'DATA_AI', 'ETL_ELT', 'GOVERNANCE', 'GREETING', 'HUMAN', 'INTEGRATION', 'MEETING', 'OTHER', 'PROJECT_RECOVERY', 'QUOTE_REQUEST', 'SERVICES'].sort()
  );
});

test('casos comerciales reales', () => {
  for (const [text, expected] of cases) {
    assert.equal(detectIntent(text), expected, `input: ${text}`);
  }
});

test('handoff, opt-out, resume y estado', () => {
  assert.ok(wantsHuman('quiero hablar con una persona'));
  assert.ok(wantsHuman('llámame'));
  assert.ok(wantsHuman('quiero conversar con un experto'));
  assert.ok(wantsOptOut('no me contacten más'));
  assert.ok(wantsOptOut('darme de baja'));
  assert.ok(wantsBot('bot'));
  assert.ok(isStatusRequest('estado'));
  assert.ok(isStatusRequest('ping'));
  assert.ok(!wantsHuman('quiero cotizar'));
});

test('lead caliente detectado', () => {
  assert.ok(isHotLead('Quiero cotizar', 'QUOTE_REQUEST'));
  assert.ok(isHotLead('tenemos un proyecto detenido', 'PROJECT_RECOVERY'));
  assert.ok(!isHotLead('hola', 'GREETING'));
});
