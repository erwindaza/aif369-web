import { detectIntent, isHotLead, wantsBot, wantsOptOut, isStatusRequest, isMetaRequest, serviceForIntent } from './intents.js';
import {
  GREETING_REPLY,
  HANDOFF_REPLY,
  OPT_OUT_REPLY,
  MEETING_REPLY,
  STATUS_REPLY,
  META_REPLY,
} from './prompt.js';
import { getTenant } from './tenants.js';

export const ROUTES = [
  'healthcheck',
  'estado_tecnico',
  'meta_guard',
  'opt_out',
  'human_handoff',
  'resume_bot',
  'saludo',
  'cotizacion',
  'agenda',
  'oportunidad',
  'conversacion_general',
];

const llmDecision = (route, intent, extra = {}) => ({
  route,
  intent,
  llm: true,
  ...extra,
});

export function route(message, { health, tenant = getTenant() } = {}) {
  const text = String(message.text || '').trim();
  const isDefaultTenant = tenant.id === 'aif369';

  if (/^ping$/i.test(text)) return { route: 'healthcheck', reply: 'pong', llm: false };

  if (wantsOptOut(text)) {
    return {
      route: 'opt_out',
      intent: 'OTHER',
      handoff: true,
      optOut: true,
      llm: false,
      reply: OPT_OUT_REPLY,
    };
  }

  if (wantsBot(text)) {
    return {
      route: 'resume_bot',
      intent: 'OTHER',
      resume: true,
      llm: false,
      reply: `Listo, retomo como asistente comercial de ${tenant.name}. ¿Quieres cotizar, agendar una llamada o revisar qué servicio calza mejor con tu caso?`,
    };
  }

  if (isStatusRequest(text) && health) {
    return { route: 'estado_tecnico', intent: 'OTHER', llm: false, reply: STATUS_REPLY(health) };
  }

  if (isMetaRequest(text)) {
    const reply = isDefaultTenant
      ? META_REPLY
      : `Soy el asistente de ${tenant.name}; no comparto detalles técnicos internos. ` +
        'Prefiero enfocarnos en lo tuyo: ¿qué necesitas: equipo, instalación o mantención?';
    return { route: 'meta_guard', intent: 'OTHER', llm: false, reply };
  }

  const intent = detectIntent(text);
  const hot = isHotLead(text, intent);
  const lead = hot || ['QUOTE_REQUEST', 'MEETING', 'PROJECT_RECOVERY', 'INTEGRATION', 'ETL_ELT', 'AI_AGENT', 'GOVERNANCE', 'DATA_AI'].includes(intent);

  if (intent === 'HUMAN') {
    const reply = isDefaultTenant
      ? HANDOFF_REPLY
      : `Perfecto, dejo esta conversación para seguimiento humano de ${tenant.name} (${tenant.handoff}). ` +
        'Para adelantar, ¿me cuentas qué necesitas?';
    return { route: 'human_handoff', intent, handoff: true, llm: false, reply };
  }

  if (intent === 'QUOTE_REQUEST') {
    // Los precios viven en knowledge: al LLM con retrieval se citan y no se inventan.
    return llmDecision('cotizacion', intent, { hot: true, lead: true });
  }

  if (intent === 'MEETING' && isDefaultTenant) {
    return { route: 'agenda', intent, hot: true, lead: true, llm: false, reply: MEETING_REPLY };
  }

  if (intent === 'GREETING') {
    return { route: 'saludo', intent, llm: false, reply: tenant.greeting || GREETING_REPLY };
  }

  if (intent === 'PROJECT_RECOVERY') {
    return llmDecision('oportunidad', intent, { hot: true, lead: true });
  }

  if (lead) {
    return llmDecision('oportunidad', intent, { hot });
  }

  return llmDecision('conversacion_general', intent, { hot });
}

export { serviceForIntent };
