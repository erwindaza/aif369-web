import test from 'node:test';
import assert from 'node:assert/strict';
import { loadKnowledge, retrieve, formatContext, getKnowledgeStats } from '../src/knowledge.js';

test('carga los documentos de knowledge/', async () => {
  const kb = await loadKnowledge({ force: true });
  const stats = getKnowledgeStats();
  assert.equal(stats.docs, 7);
  assert.ok(stats.chunks > 30, `chunks=${stats.chunks}`);
  assert.ok(kb.chunks.every((c) => c.heading && c.text && c.doc));
  assert.ok(kb.docs.find((d) => d.name === 'sales-rules'));
  assert.ok(stats.retriever === 'lexical' || stats.retriever === 'embedding');
});

test('retrieval lexical encuentra el fragmento correcto', async () => {
  const hits = await retrieve('tengo SAP, Excel y PostgreSQL y quiero una fuente única de verdad');
  assert.ok(hits.length > 0, 'sin resultados');
  assert.ok(hits[0].score > 0);
  const docs = hits.map((h) => h.chunk.doc);
  assert.ok(
    docs.includes('data-ai') || docs.includes('faq') || docs.includes('services'),
    `docs=${docs.join(',')}`
  );
});

test('retrieval para precio usa faq/sales-rules', async () => {
  const hits = await retrieve('¿cuánto cuesta el plan Starter 369?');
  const docs = hits.map((h) => h.chunk.doc);
  assert.ok(docs.includes('faq') || docs.includes('sales-rules'), `docs=${docs.join(',')}`);
});

test('retrieval para gobierno de IA', async () => {
  const hits = await retrieve('¿hacen gobierno de IA y cumplimiento de la Ley 21.719?');
  const docs = hits.map((h) => h.chunk.doc);
  assert.ok(docs.includes('governance') || docs.includes('faq'), `docs=${docs.join(',')}`);
});

test('formatContext respeta el limite de caracteres', async () => {
  const hits = await retrieve('integración de datos ETL pipelines reportes');
  const ctx = formatContext(hits, 500);
  assert.ok(ctx.length <= 501, `len=${ctx.length}`);
  assert.ok(ctx.length > 0);
});

test('retrieve devuelve vacio sin consulta', async () => {
  assert.deepEqual(await retrieve(''), []);
  assert.deepEqual(await retrieve('   '), []);
});
