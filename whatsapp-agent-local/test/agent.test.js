import test from 'node:test';
import assert from 'node:assert/strict';
import { buildMessages, polishReply } from '../src/agent.js';
import { SYSTEM_PROMPT, FALLBACK_REPLY, GREETING_REPLY, QUOTE_REPLY, MEETING_REPLY, HANDOFF_REPLY, NEXT_QUESTION } from '../src/prompt.js';

test('system prompt es pequeño y estricto', () => {
  assert.ok(SYSTEM_PROMPT.length < 1600, `len=${SYSTEM_PROMPT.length}`);
  assert.match(SYSTEM_PROMPT, /SOLO con el CONOCIMIENTO/);
  assert.match(SYSTEM_PROMPT, /Nunca inventes precios/);
  assert.match(SYSTEM_PROMPT, /como estas construido/);
  assert.match(SYSTEM_PROMPT, /{{KNOWLEDGE}}/);
});

test('respuestas deterministicas no inventan montos', () => {
  for (const reply of [FALLBACK_REPLY, GREETING_REPLY, QUOTE_REPLY, MEETING_REPLY, HANDOFF_REPLY]) {
    assert.ok(!/\d[\d.,]{2,}\s*(usd|d[oó]lares|clp)/i.test(reply), reply);
    assert.ok(reply.length < 400, `too long: ${reply.length}`);
  }
  assert.match(MEETING_REPLY, /calendly\.com/);
});

test('todas las preguntas de calificación existen', () => {
  for (const field of ['empresa', 'problema', 'fuentes', 'urgencia', 'objetivo', 'contacto']) {
    assert.ok(NEXT_QUESTION[field]?.[0], `falta ${field}`);
  }
});

test('buildMessages inyecta conocimiento, resumen, datos y historial acotado', () => {
  const history = Array.from({ length: 20 }, (_, i) => ({
    direction: i % 2 ? 'out' : 'in',
    body: `mensaje ${i}`,
  }));
  const messages = buildMessages({
    context: 'Data & AI Factory > ETL',
    history,
    summary: 'estado=QUALIFYING intent=INTEGRATION',
    qualification: { empresa: 'ACME', fuentes: 'sap' },
    suggestedQuestion: '¿Cual es el principal problema que quieres resolver?',
  });

  assert.equal(messages[0].role, 'system');
  assert.match(messages[0].content, /Data & AI Factory > ETL/);
  assert.match(messages[0].content, /SOLO con el CONOCIMIENTO/);

  const notes = messages.find((m) => m.role === 'system' && m !== messages[0]);
  assert.match(notes.content, /RESUMEN DE LA CONVERSACION/);
  assert.match(notes.content, /empresa: ACME/);
  assert.match(notes.content, /SIGUIENTE PASO/);

  const turns = messages.filter((m) => m.role !== 'system');
  assert.equal(turns.length, 20, 'se envía todo el historial');
  assert.equal(turns.filter((m) => m.role === 'assistant').length, 10);
});

test('sin conocimiento el prompt lo indica', () => {
  const messages = buildMessages({ context: '', history: [] });
  assert.match(messages[0].content, /No hay fragmentos de conocimiento/);
});

test('polishReply garantiza la pregunta de calificacion', () => {
  const q = '¿En que empresa trabajas?';
  assert.equal(polishReply('Sí, podemos tomarlo y terminarlo.', q), `Sí, podemos tomarlo y terminarlo. ${q}`);
  // Respuesta que es solo una pregunta ajena: se reemplaza por la sugerida (una sola pregunta).
  assert.equal(polishReply('¿Ya tienes datos en Excel?', q), q);
  // Si ademas trae contenido, se conserva el contenido y se cambia la pregunta.
  assert.equal(polishReply('Tenemos sí. ¿Ya tienes datos en Excel?', q), `Tenemos sí. ${q}`);
  assert.equal(polishReply('  hola   \n\n\n mundo  ', q), `hola\n\n mundo. ${q}`);
  assert.equal(polishReply('', q), q);
});

test('polishReply elimina el eco de la pregunta del cliente', () => {
  const q = '¿En que empresa trabajas?';
  const echo = '¿Qué servicios ofrece AIF369?';
  const reply = 'Ofrecemos consultoría de datos e IA para empresas.\n\n¿Qué servicios ofrece AIF369?';
  const out = polishReply(reply, q, echo);
  assert.ok(!out.includes('Ofrecemos consultoría de datos e IA para empresas.\n\n¿Qué servicios'), out);
  assert.match(out, /¿En que empresa trabajas\?$/);
  assert.match(out, /consultoría/);
});

test('polishReply elimina preguntas reformuladas del cliente y exige cerrar con pregunta', () => {
  const q = '¿En que empresa trabajas?';
  const echo = '¿Qué servicios ofrece AIF369?';
  const out = polishReply('AIF369 ofrece consultoría de datos. ¿Qué servicios ofrecemos?', q, echo);
  assert.match(out, /¿En que empresa trabajas\?$/);
  assert.ok(!/servicios ofrecemos/i.test(out), out);

  const conPreguntaEnElMedio = polishReply(
    'Somos AIF369. ¿Te suena familiar? Ofrecemos diagnóstico gratuito.',
    q,
    echo
  );
  assert.match(conPreguntaEnElMedio, /¿En que empresa trabajas\?$/);
});

test('polishReply limpia signos colgantes al final', () => {
  const q = '¿En que empresa trabajas?';
  assert.ok(!/[;,:] ¿En/.test(polishReply('Ofrecemos dos cosas; .', q)), 'signo colgante');
  assert.ok(!polishReply('Hola;', q).startsWith('Hola;'), 'punto y coma');
  assert.ok(polishReply('Solo lista: a, b:', q).endsWith('?'), q);
});

test('polishReply no duplica la pregunta si el modelo ya la hizo', () => {
  const q = '¿En que empresa trabajas?';
  const out = polishReply('Hola. Entiendo. Necesito saber en qué empresa trabajas.', q);
  assert.ok(!out.includes('¿En que empresa trabajas?'), out);
  assert.ok(out.endsWith('?'), out);
  assert.ok(out.split('?').length <= 2, out);
});

test('polishReply aplana listas y recorta respuestas largas', () => {
  const q = '¿En que empresa trabajas?';
  const bullets =
    'AIF369 ofrece:\n\n* Diagnóstico gratuito de 30 minutos\n* Gobernanza de Datos para IA';
  const out = polishReply(bullets, q);
  assert.ok(!out.includes('*'), out);
  assert.match(out, /Incluye: Diagnóstico gratuito de 30 minutos; Gobernanza de Datos para IA\./);
  assert.ok(out.endsWith('?'), out);

  const long = `${Array.from({ length: 90 }, (_, i) => `palabra${i}`).join(' ')}.`;
  const cut = polishReply(long, q);
  assert.ok(cut.split(/\s+/).length < 60, `words=${cut.split(/\s+/).length}`);
  assert.ok(cut.endsWith('?'), cut.slice(-60));
});

test('knowledgeGuard bloquea el LLM cuando no hay fragmentos', async () => {
  const { knowledgeGuard, knowledgeGuardReply } = await import('../src/agent.js');
  assert.strictEqual(knowledgeGuard(0, 'Me dijeron que instalan aire acondicionado'), true);
  assert.strictEqual(knowledgeGuard(0, '¿Hacen SEO y publicidad en Google?'), true);
  assert.strictEqual(knowledgeGuard(0, 'hola'), false, 'saludo corto no necesita conocimiento');
  assert.strictEqual(knowledgeGuard(0, ''), false);
  assert.strictEqual(knowledgeGuard(4, 'Me dijeron que instalan aire acondicionado'), false);
  const reply = knowledgeGuardReply('Me dijeron que instalan aire acondicionado', '¿En que empresa trabajas?');
  assert.ok(!/aire acondicionado\./i.test(reply), reply);
  assert.ok(reply.endsWith('¿En que empresa trabajas?'), reply);
  assert.ok(/no tengo ese dato confirmado/i.test(reply), reply);
});
