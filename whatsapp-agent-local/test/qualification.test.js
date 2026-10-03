import test from 'node:test';
import assert from 'node:assert/strict';
import {
  extractQualification,
  nextField,
  nextQuestion,
  computeLeadStatus,
  leadScore,
  qualificationSummary,
  FIELDS,
} from '../src/qualification.js';

test('extrae empresa, fuentes, contacto y urgencia', () => {
  const q = extractQualification(
    'Somos Retail Andino, tenemos SAP, Excel y PostgreSQL, es urgente para este mes, escríbeme a datos@retailandino.cl'
  );
  assert.match(q.empresa, /Retail Andino/);
  assert.ok(q.fuentes.includes('sap'));
  assert.ok(q.fuentes.includes('excel'));
  assert.ok(q.fuentes.includes('postgresql'));
  assert.equal(q.contacto, 'datos@retailandino.cl');
  assert.equal(q.urgencia, 'este mes');
});

test('la calificacion se acumula entre mensajes', () => {
  const first = extractQualification('Somos Clinica Sur');
  const second = extractQualification('queremos integrar excel con sap', first);
  assert.equal(second.empresa, 'Clinica Sur');
  assert.ok(second.fuentes.includes('excel'));
  assert.equal(nextField(first), 'problema');
});

test('pregunta siguiente en orden de campos', () => {
  const q = {};
  assert.equal(nextField(q), FIELDS[0]);
  assert.ok(nextQuestion(q));
  const full = Object.fromEntries(FIELDS.map((f) => [f, 'x']));
  assert.equal(nextField(full), null);
  assert.equal(nextQuestion(full), null);
});

test('estados de lead', () => {
  assert.equal(computeLeadStatus({ intent: 'GREETING', current: 'NEW' }), 'NEW');
  assert.equal(computeLeadStatus({ intent: 'INTEGRATION', current: 'NEW' }), 'QUALIFYING');
  assert.equal(
    computeLeadStatus({ intent: 'INTEGRATION', qualification: { empresa: 'X', fuentes: 'sap', problema: 'y' } }),
    'QUALIFIED'
  );
  assert.equal(computeLeadStatus({ intent: 'QUOTE_REQUEST', current: 'NEW' }), 'HOT');
  assert.equal(computeLeadStatus({ intent: 'SERVICES', handoff: true }), 'HUMAN_HANDOFF');
  assert.equal(computeLeadStatus({ intent: 'SERVICES', optOut: true }), 'CLOSED');
  assert.equal(computeLeadStatus({ intent: 'SERVICES', handoff: true, optOut: true }), 'CLOSED');
});

test('score crece con el estado y los campos', () => {
  const newScore = leadScore('NEW', {});
  const qualified = leadScore('QUALIFIED', { empresa: 'a', fuentes: 'b', problema: 'c' });
  assert.ok(qualified > newScore);
  assert.ok(leadScore('HOT', {}) <= 100);
  assert.equal(leadScore('CLOSED', {}), 0);
});

test('resumen legible', () => {
  const s = qualificationSummary({ empresa: 'ACME', fuentes: 'sap,excel' });
  assert.match(s, /empresa: ACME/);
  assert.match(s, /fuentes: sap,excel/);
});
