import {
  systemMessages,
  contactMessage,
  FALLBACK_REPLY,
  noKnowledgeReply,
  EMPTY_KNOWLEDGE_NOTE,
} from './prompt.js';
import { chat } from './ollama.js';
import { nextField, filledFields } from './qualification.js';

export function buildMessages({
  context = '',
  history = [],
  summary = '',
  qualification = {},
  suggestedQuestion = null,
  hint = null,
  tenant = {},
}) {
  const messages = systemMessages(context, tenant);
  const tenantName = tenant.name || 'AIF369';

  const notes = [];
  if (context && context.includes(EMPTY_KNOWLEDGE_NOTE)) {
    notes.push(
      'CONOCIMIENTO VACIO: no hay nada en la fuente sobre eso. NO inventes servicios, precios, ' +
        `clientes, marcas ni capacidades. Di que no tienes ese dato confirmado para ${tenantName} y ` +
        'cierra con la pregunta sugerida.'
    );
  } else if (context) {
    notes.push(
      'DATO A CITAR: menciona al menos un servicio, alcance o precio concreto del CONOCIMIENTO antes de preguntar. ' +
        'NO repitas tu respuesta anterior ni el resumen: responde a lo ultimo que pregunto el cliente, con una sola pregunta al final.'
    );
  }
  if (summary) notes.push(`RESUMEN DE LA CONVERSACION:\n${summary}`);
  const contact = contactMessage(tenant);
  if (contact) notes.push(contact);
  const filled = filledFields(qualification);
  if (filled.length) {
    notes.push(`DATOS YA CONOCIDOS DEL CLIENTE:\n${filled.map((f) => `${f}: ${qualification[f]}`).join('\n')}`);
  }
  const field = nextField(qualification);
  if (field && suggestedQuestion) {
    notes.push(`SIGUIENTE PASO: responde el contenido y termina con esta pregunta exacta: "${suggestedQuestion}"`);
  }
  if (hint) notes.push(`NOTA: ${hint}`);
  if (notes.length) {
    messages.push({ role: 'system', content: notes.join('\n\n') });
  }

  for (const row of history) {
    if (!row.body) continue;
    messages.push({
      role: row.direction === 'out' ? 'assistant' : 'user',
      content: String(row.body).slice(0, 600),
    });
  }
  return messages;
}

const norm = (s) =>
  String(s || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9ñ\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const tokenSet = (s) =>
  new Set(
    norm(s)
      .split(' ')
      .filter((w) => w.length > 3)
  );

const isEchoQuestion = (sentence, echo) => {
  const text = String(sentence || '').trim();
  if (!text.endsWith('?')) return false;
  const ta = tokenSet(text);
  const tb = tokenSet(echo);
  if (ta.size < 2 || tb.size === 0) return false;
  let common = 0;
  for (const t of ta) if (tb.has(t)) common += 1;
  return common / ta.size >= 0.5;
};

const stripEcho = (text, echo) => {
  const nEcho = norm(echo);
  if (!nEcho || nEcho.length < 8) return text;
  const sentences = text.split(/\n+|(?<=\.)\s+/);
  const last = sentences[sentences.length - 1] || '';
  const nLast = norm(last);
  const remove =
    nLast &&
    ((nLast === nEcho || nEcho.startsWith(nLast) || nLast.startsWith(nEcho)) || isEchoQuestion(last, echo));
  if (remove) {
    sentences.pop();
    return sentences.join('\n').replace(/\n{3,}/g, '\n\n').trim();
  }
  return text;
};

const flattenBullets = (text) => {
  const out = [];
  let buffer = [];
  const flush = () => {
    if (buffer.length) out.push(`Incluye: ${buffer.join('; ')}.`);
    buffer = [];
  };
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (/^[-*•]\s*/.test(line)) {
      buffer.push(line.replace(/^[-*•]\s*/, '').replace(/[.,;]$/, ''));
    } else {
      flush();
      out.push(raw);
    }
  }
  flush();
  return out.join('\n');
};

const enforceConcise = (text, maxWords = 48) => {
  const words = text.split(/\s+/).filter(Boolean);
  if (words.length <= maxWords + 8) return text;
  let endIndex = -1;
  const window = Math.min(24, words.length - maxWords);
  for (let i = 0; i < window; i += 1) {
    if (/[.!?]["»)]?$/.test(words[maxWords + i])) {
      endIndex = maxWords + i;
      break;
    }
  }
  let cut = words.slice(0, endIndex >= 0 ? endIndex + 1 : maxWords).join(' ');
  if (!/[.!?]["»)]?$/.test(cut)) cut += '.';
  return cut;
};

const tidyEnd = (text) => {
  let out = String(text || '').trim();
  out = out.replace(/(?:[;,:]\s*)+[.!?]?$/, '').trim();
  return out;
};

const normText = (value) =>
  String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[¿?¡!.,;:]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const DANGLING = new Set(
  'y o e u de del la el los las un una unas unos que con para en por su sus al se es son y o ni pero como mas mas mas'.split(
    /\s+/
  )
);

const trimDangling = (text) => {
  let out = String(text || '');
  for (let guard = 0; guard < 8; guard += 1) {
    out = out.replace(/\s+$/, '');
    const token = (out.match(/(\S+)$/) || [])[1];
    if (!token) break;
    const bare = token.replace(/[,;:–-]+$/, '');
    if (DANGLING.has(bare.toLowerCase()) || /[,;:–-]$/.test(token)) {
      out = out.replace(/\s*\S+$/, '');
    } else break;
  }
  return out.trim();
};

export const polishReply = (reply, suggestedQuestion, lastUserText = '') => {
  let text = String(reply || '')
    .replace(/\r/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]{2,}/g, ' ')
    .replace(/[ \t]+\n/g, '\n')
    .trim();
  text = flattenBullets(text);
  text = text.replace(/[*_`~]{1,2}/g, '').replace(/[ \t]{2,}/g, ' ');
  text = stripEcho(text, lastUserText);
  text = enforceConcise(text);
  text = trimDangling(text);
  text = tidyEnd(text);
  if (text && !/[.!?]["»)]?$/.test(text)) text += '.';
  if (suggestedQuestion) {
    const core = normText(suggestedQuestion);
    if (core && normText(text).includes(core)) {
      text = /\.$/.test(text) ? `${text.slice(0, -1)}?` : text;
    } else {
      // UNA sola pregunta: se retira la del modelo y cierra con la sugerida.
      const own = text.match(/[^.!?\n]*\?/);
      if (own && own[0].trim()) text = text.replace(own[0], ' ');
      text = text.replace(/[ \t]{2,}/g, ' ').replace(/[ \t]+([.,;:])/g, '$1').replace(/[.,;:][ \t]*$/, '').trim();
      if (text && !/[.!?]$/.test(text)) text += '.';
      text = `${text ? `${text} ` : ''}${suggestedQuestion}`.trim();
    }
  }
  return text;
};

const fallbackReply = (qualification = {}, tenant = {}) => {
  const name = tenant.name || 'AIF369';
  const base =
    name === 'AIF369'
      ? FALLBACK_REPLY
      : `Puedo ayudarte, pero necesito confirmar ese dato con el equipo de ${name}.`;
  // La pregunta de calificacion la agrega polishReply (siempre la sugerida del tenant).
  return base;
};

const META_REFUSAL = 'no comparto detalles tecnicos internos';

const isMisfire = (text, isMeta) =>
  !isMeta && String(text || '').toLowerCase().includes(META_REFUSAL);

// Sin fragmentos relevantes el modelo de 1B inventa servicios: no se le pregunta.
export const knowledgeGuard = (hits, text) =>
  Number(hits || 0) === 0 && String(text || '').trim().length >= 20;

export const knowledgeGuardReply = (text, suggestedQuestion, tenant = {}) =>
  polishReply(
    noKnowledgeReply(tenant.name || 'AIF369', tenant.knowledgeScope),
    suggestedQuestion,
    text
  );

export async function generateReply(payload) {
  const startedAt = Date.now();
  if (knowledgeGuard(payload.knowledgeHits, payload.lastUserText)) {
    console.log('[agent] guardia de conocimiento: 0 fragmentos, respuesta deterministica');
    return {
      reply: knowledgeGuardReply(payload.lastUserText, payload.suggestedQuestion, payload.tenant),
      model: 'knowledge_guard',
      latencyMs: 0,
      ok: true,
    };
  }
  try {
    let raw = await chat(buildMessages(payload));
    if (!raw) throw new Error('respuesta vacia');

    if (isMisfire(raw, payload.isMeta)) {
      console.log('[agent] rechazo indebidamente aplicado; reintento con nota de contexto');
      const retry = await chat(
        buildMessages({
          ...payload,
          hint:
            'El cliente NO pregunto por tu configuracion ni por tu modelo: es una consulta de negocio. ' +
            'Responde con el CONOCIMIENTO y termina con la pregunta sugerida.',
        })
      );
      if (retry && !isMisfire(retry, payload.isMeta)) {
        raw = retry;
      } else {
        console.log('[agent] rechazo persistente; uso respuesta de respaldo');
        raw = fallbackReply(payload.qualification, payload.tenant);
      }
    }

    const reply = polishReply(raw, payload.suggestedQuestion, payload.lastUserText);
    if (!reply) throw new Error('respuesta vacia');
    return { reply, model: 'ollama', latencyMs: Date.now() - startedAt, ok: true };
  } catch (err) {
    console.error(`[agent] ollama fallo: ${err.message}`);
    return {
      reply: polishReply(
        fallbackReply(payload.qualification, payload.tenant),
        payload.suggestedQuestion,
        payload.lastUserText
      ),
      model: 'fallback',
      latencyMs: Date.now() - startedAt,
      ok: false,
    };
  }
}
