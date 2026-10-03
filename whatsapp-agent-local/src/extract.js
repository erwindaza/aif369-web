import { config } from './config.js';
import { chatJson } from './ollama.js';
import { getRegistry } from './slot-registry.js';
import { detectFriction } from './conversation-state.js';
import { extractQualification, EMPRESA_STOP } from './qualification.js';

const validValue = (def, value) => {
  if (value === undefined || value === null || value === '') return false;
  switch (def.type) {
    case 'int':
      return Number.isFinite(Number(value)) && Number(value) > 0;
    case 'bool':
      return typeof value === 'boolean';
    case 'area':
      return Number.isFinite(Number(value)) && Number(value) > 0;
    default:
      return typeof value === 'string' && value.trim().length > 0 && value.length <= 120;
  }
};

const coerce = (def, value) => {
  if (def.type === 'int' || def.type === 'area') {
    const n = Number(String(value).replace(',', '.'));
    return Number.isFinite(n) ? n : null;
  }
  if (def.type === 'bool') return value === true || value === 'true';
  return String(value).trim();
};

// Rechazo explicito: el usuario frena la direccion de la conversacion.
const REJECTION_RE =
  /\b(solo|solamente|[uú]nicamente) (quiero|busco|necesito|lo que busco|necesitamos)\b|^no\b[^?]{0,40}\b(quiero|busco|me interesa|necesito)\b|\bno es (eso|lo que busco|por ah[íi])\b|\bolv[íi]d(alo|ame|en)\b|\beso (no|nada) me (importa|interesa)\b/i;

export const detectRejection = (text) => REJECTION_RE.test(String(text || ''));

// Respuestas cortas que no aportan datos: no sirven para rellenar un slot.
const AFFIRMATION_RE = /^(s[ií]|no|nada|ningun[oa]|ya|ok|okay|dale|bueno[oa]?|buenas?|claro|perfecto|listo|obvio|tal vez|quiz[aá]|depende|ahora no)[.!,:;\s]*$/i;

const FRICTION_LEAD_RE = /^(ya te (dije|dijeron|acabo de decir)[^.!?]{0,60}[.!?]?\s*)/i;

const EMPRESA_VERB_RE =
  /\b(necesit\w*|quiero|queremos|querer|tenemos|buscamos|integr\w+|hacer|me gustar\w*|cotiz\w*|agendar|hablar|contactar|proyecto|arquitectura|resolver|reportes|datos|servicio)\b/i;

// El mensaje habla de la empresa: responde a "empresa", no al slot que quedo preguntando.
const EMPRESA_SIGNAL_RE =
  /\b(de parte de|somos de|somos la|somos|la empresa|empresa|compa[nñ][ií]a|organizaci[oó]n|trabajo en|laburo en)\b/i;

// Nombre de empresa corto, sin verbos ni articulos de arranque ("Un etl" no es una empresa).
const isEmpresaName = (v) =>
  v.length >= 3 &&
  v.length <= 60 &&
  v.split(/\s+/).length <= 4 &&
  !EMPRESA_VERB_RE.test(v) &&
  !EMPRESA_STOP.has(v.split(/\s+/)[0].toLowerCase());

const PENDING_GUARD = {
  empresa: isEmpresaName,
  problema: (v) => v.length >= 8 && v.length <= 160,
  fuentes: (v) => v.length <= 60 && v.split(/\s+/).length <= 6,
  urgencia: (v) => v.length <= 60,
  objetivo: (v) => v.length <= 100,
  contacto: (v) => v.length <= 60,
};

const cleanPendingAnswer = (text, key) => {
  let v = String(text || '')
    .replace(FRICTION_LEAD_RE, '')
    .replace(/^["'“”\s]+|["'“”\s]+$/g, '')
    .replace(/[.!;]+$/, '')
    .replace(/\s+/g, ' ')
    .trim();
  if (key === 'empresa') {
    const after = v.match(/(?:empresa|compa[nñ][ií]a|organizaci[oó]n)\s+(?:es\s+)?(.+)$/i);
    if (after) v = after[1];
    v = v.replace(/^(de parte de|somos(?: de)?|soy de|la empresa(?: es)?|trabajo en|laburo en)\s+/i, '').trim();
  }
  return v;
};

// Extraccion determinista: solo datos explícitamente entregados.
export function extractDeterministic(text, registry, currentSlots = {}, activeIntents = [], pendingSlot = null) {
  const value = String(text || '');
  const slots = {};

  if (detectRejection(value)) {
    return { new_intents: [], slots: {}, frustration: detectFriction(value), rejection: true, reconfirmed: [] };
  }

  let reconfirmed = [];
  if (registry.id === 'aif369') {
    const merged = extractQualification(value, currentSlots);
    // Que menciona el mensaje (sin heredar lo que ya sabemos) para distinguir "lo repite".
    const detected = extractQualification(value, {});
    for (const [k, v] of Object.entries(merged)) {
      if (currentSlots[k] !== v && v !== undefined && v !== null && v !== '') slots[k] = v;
    }
    reconfirmed = Object.keys(detected).filter(
      (k) => currentSlots[k] !== undefined && currentSlots[k] === detected[k]
    );
  } else {
    for (const [key, def] of Object.entries(registry.slots)) {
      for (const rule of def.extract || []) {
        const m = value.match(rule.re);
        if (!m) continue;
        const raw = rule.value(m);
        if (raw === null || raw === undefined || raw === '') continue;
        const coerced = coerce(def, raw);
        if (coerced !== null && validValue(def, coerced)) {
          slots[key] = coerced;
          break;
        }
      }
    }
  }

  const new_intents = [];
  for (const rule of registry.intentRules || []) {
    if (rule.re.test(value) && !new_intents.includes(rule.intent)) new_intents.push(rule.intent);
  }

  if (registry.id !== 'aif369') {
    // Solo slots del intent activo (detectado ahora o ya presente en la conversacion).
    const active = new Set([...activeIntents, ...new_intents]);
    for (const key of Object.keys(slots)) {
      const owner = registry.slots[key]?.intent;
      if (owner && !active.has(owner)) delete slots[key];
    }
    reconfirmed = Object.keys(slots).filter(
      (k) => currentSlots[k] !== undefined && currentSlots[k] === slots[k]
    );
  }

  // Si lo que preguntamos sigue vacio y la respuesta es texto plano, va al slot pendiente.
  const pending = pendingSlot && registry.slots[pendingSlot] ? pendingSlot : null;
  const pendingDef = pending ? registry.slots[pending] : null;
  if (pending && pendingDef.type === 'text' && slots[pending] === undefined) {
    const others = Object.keys(slots).filter((k) => k !== pending);
    const addedNow = new_intents.filter((i) => !activeIntents.includes(i));
    // Si el mensaje ya aporto otro dato (o declaro un intent nuevo), es otra cosa: no al pendiente.
    // En aif369 solo manda un campo requerido distinto: los opcionales no cortan.
    const requiredNow = new Set(
      [...activeIntents, ...new_intents].flatMap((i) => registry.intents[i]?.required || [])
    );
    const blocked =
      (registry.id === 'aif369'
        ? others.some((k) => requiredNow.has(k) || k === 'contacto')
        : others.length > 0 || addedNow.length > 0) ||
      reconfirmed.length > 0 ||
      (pending !== 'empresa' && EMPRESA_SIGNAL_RE.test(value));

    const cleaned = cleanPendingAnswer(value, pending);
    const friction = detectFriction(value);
    const guard = PENDING_GUARD[pending] || ((v) => v.length <= 60);
    const eligible =
      !blocked &&
      cleaned.length >= 2 &&
      cleaned.length <= 140 &&
      !cleaned.includes('?') &&
      !AFFIRMATION_RE.test(cleaned) &&
      // una molestia sin contenido nuevo no rellena nada (salvo un nombre corto tipo empresa)
      (!friction || (pending === 'empresa' && cleaned.split(/\s+/).length <= 4)) &&
      guard(cleaned);
    if (eligible) slots[pending] = cleaned;
  }

  return { new_intents, slots, frustration: detectFriction(value), rejection: false, reconfirmed };
}

function sanitizeExtraction(parsed, registry) {
  const out = { new_intents: [], slots: {}, frustration: false };
  if (!parsed || typeof parsed !== 'object') return out;

  out.frustration = parsed.frustration === true;

  for (const intent of Array.isArray(parsed.new_intents) ? parsed.new_intents : []) {
    if (registry.intents[intent] && !out.new_intents.includes(intent)) out.new_intents.push(intent);
  }

  const rawSlots = parsed.slots && typeof parsed.slots === 'object' ? parsed.slots : {};
  for (const [key, value] of Object.entries(rawSlots)) {
    const def = registry.slots[key];
    if (!def) continue; // clave fuera del registro: se descarta
    const coerced = coerce(def, value);
    if (coerced !== null && validValue(def, coerced)) out.slots[key] = coerced;
  }
  return out;
}

const extractionPrompt = (registry) =>
  'Extrae únicamente información explícitamente entregada por el usuario. No inventes datos. ' +
  'Devuelve SOLO JSON válido con las claves "new_intents" (array), "slots" (objeto) y "frustration" (boolean).\n' +
  `Intents permitidos: ${Object.keys(registry.intents).join(', ') || '(ninguno)'}.\n` +
  `Slots permitidos: ${Object.keys(registry.slots).join(', ') || '(ninguno)'}.`;

export async function extractWithModel(text, registry, { summary = '' } = {}) {
  try {
    const raw = await chatJson([
      { role: 'system', content: extractionPrompt(registry) },
      {
        role: 'user',
        content: `${summary ? `Contexto: ${summary}\n` : ''}Mensaje: "${String(text).slice(0, 400)}"`,
      },
    ]);
    const cleaned = String(raw)
      .replace(/```json/gi, '')
      .replace(/```/g, '')
      .trim();
    const start = cleaned.indexOf('{');
    const end = cleaned.lastIndexOf('}');
    if (start < 0 || end < start) return { new_intents: [], slots: {}, frustration: false };
    return sanitizeExtraction(JSON.parse(cleaned.slice(start, end + 1)), registry);
  } catch (err) {
    console.log(`[extract] modelo no valido (${err.message}); se usa solo extraccion determinista`);
    return { new_intents: [], slots: {}, frustration: false };
  }
}

const hasContent = (extraction) =>
  Object.keys(extraction.slots).length > 0 || extraction.new_intents.length > 0;

// Determinista primero; el modelo solo entra si no encontró nada.
export async function extractMessage({
  text,
  registry,
  currentSlots = {},
  activeIntents = [],
  summary = '',
  pendingSlot = null,
} = {}) {
  const reg = registry || getRegistry();
  const deterministic = extractDeterministic(text, reg, currentSlots, activeIntents, pendingSlot);
  const mode = config.extractor;

  if (deterministic.rejection) return deterministic;
  if (mode === 'rules') return deterministic;
  if (mode === 'model') {
    const model = await extractWithModel(text, reg, { summary });
    return {
      new_intents: [...new Set([...deterministic.new_intents, ...model.new_intents])],
      slots: { ...model.slots, ...deterministic.slots },
      frustration: deterministic.frustration || model.frustration,
      rejection: false,
      reconfirmed: deterministic.reconfirmed || [],
    };
  }
  if (hasContent(deterministic)) return deterministic;
  if (String(text || '').trim().length < 6) return deterministic;

  const model = await extractWithModel(text, reg, { summary });
  return {
    new_intents: [...new Set([...deterministic.new_intents, ...model.new_intents])],
    slots: { ...deterministic.slots, ...model.slots },
    frustration: deterministic.frustration || model.frustration,
    rejection: false,
    reconfirmed: deterministic.reconfirmed || [],
  };
}
