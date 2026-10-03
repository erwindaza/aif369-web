import { getTenant } from './tenants.js';

// Mismos disparadores que el widget web de aif369 (chat-widget.js): solo aporta
// el pie de contacto cuando la respuesta habla de agendar, cotizar o contactar.
export const CONTACT_TRIGGER =
  /agend|cotiz|servicio|precio|costo|cu[aá]nto|contact|whatsapp|reuni[oó]n|llamada|propuesta|diagn[oó]stico|scorecard|asesor|visita|terreno|instalaci|mantenci|comprar|pedido|env[ií]o|garant[ií]a|deriv|humano|manager/i;

const NO_FOOTER_ROUTES = new Set(['opt_out', 'healthcheck', 'estado_tecnico']);

export const footerForces = (route, model) =>
  ['saludo', 'cotizacion', 'agenda', 'human_handoff'].includes(route) ||
  ['knowledge_guard', 'fallback'].includes(model);

export function contactFooter(tenant = getTenant()) {
  const c = tenant.contact;
  if (!c) return '';
  const line1 = [
    tenant.name,
    c.web,
    c.phoneUrl ? `WhatsApp ${c.phoneUrl}` : null,
    c.email,
  ].filter(Boolean).join(' · ');
  const line2 = [c.cta ? `${c.cta.label}: ${c.cta.url}` : null, c.address].filter(Boolean).join(' · ');
  return [line1, line2].filter(Boolean).join('\n');
}

const segmentsOf = (footer) => footer.split(' · ').flatMap((line) => line.split('\n')).filter(Boolean);

const urlsOf = (segment) => segment.match(/https?:\/\/\S+/g) || [];

// Un segmento ya esta cubierto si esta escrito o si su link ya aparece en la respuesta.
const alreadyPresent = (segment, text) =>
  text.includes(segment) || urlsOf(segment).some((url) => text.includes(url));

// Agrega el pie de contacto solo si aporta (o si es forzado) y sin repetir lo ya escrito.
export function withContactFooter(reply, tenant = getTenant(), { route = null, model = null, force = false } = {}) {
  const text = String(reply || '').trim();
  if (!text) return text;
  if (NO_FOOTER_ROUTES.has(route)) return text;

  const footer = contactFooter(tenant);
  if (!footer) return text;

  const wanted = force || footerForces(route, model) || CONTACT_TRIGGER.test(text);
  if (!wanted) return text;

  const missing = segmentsOf(footer).filter((segment) => !alreadyPresent(segment, text));
  if (!missing.length) return text;

  return `${text}\n\n${missing.join(' · ')}`;
}
