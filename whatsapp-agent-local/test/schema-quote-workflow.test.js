import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('schema incluye flujo de cotizacion con calculo, aprobacion y email', async () => {
  const schema = await readFile(new URL('../schema.sql', import.meta.url), 'utf8');

  assert.match(schema, /CREATE TABLE IF NOT EXISTS quote_calculations/);
  assert.match(schema, /CREATE TABLE IF NOT EXISTS quote_approvals/);
  assert.match(schema, /CREATE TABLE IF NOT EXISTS outbound_email_queue/);
  assert.match(schema, /calculate_quote/);
  assert.match(schema, /request_internal_quote_approval/);
  assert.match(schema, /send_approved_quote/);
  assert.match(schema, /supplier_quote/);
  assert.match(schema, /internal_quote_review/);
  assert.match(schema, /client_quote/);
  assert.match(schema, /edaza@aif369\.com/);
});
