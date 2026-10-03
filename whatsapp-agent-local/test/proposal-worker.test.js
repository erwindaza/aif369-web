import test from 'node:test';
import assert from 'node:assert/strict';
import { buildProposalDraft } from '../src/proposal-worker.js';

test('buildProposalDraft crea una propuesta revisable sin precios inventados', () => {
  const draft = buildProposalDraft({
    push_name: 'Erwin',
    stage: 'qualified',
    lead_score: 82,
    intent: 'QUOTE_REQUEST',
    service_label: 'Data & AI Factory',
    qualification: {
      empresa: 'Bejoby',
      fuentes: 'excel, postgresql, sap',
      problema: 'consolidar reportes comerciales',
      objetivo: 'automatizar seguimiento de ventas',
      urgencia: 'ya',
    },
  });

  assert.equal(draft.draftType, 'proposal');
  assert.match(draft.title, /Bejoby/);
  assert.match(draft.body, /consolidar reportes comerciales/);
  assert.match(draft.body, /excel, postgresql, sap/);
  assert.match(draft.body, /Correo de seguimiento sugerido/);
  assert.deepEqual(draft.missingFields, ['contacto_comercial']);
  assert.ok(draft.assumptions.some((item) => /No incluye precios/i.test(item)));
  assert.ok(!/\d[\d.,]{2,}\s*(usd|d[oó]lares|clp)/i.test(draft.body), draft.body);
});

test('buildProposalDraft marca campos faltantes', () => {
  const draft = buildProposalDraft({
    display_name: 'Cliente nuevo',
    qualification: {},
  });

  assert.match(draft.title, /Cliente nuevo/);
  assert.ok(draft.missingFields.includes('empresa'));
  assert.ok(draft.missingFields.includes('fuentes'));
  assert.ok(draft.missingFields.includes('contacto_comercial'));
});
