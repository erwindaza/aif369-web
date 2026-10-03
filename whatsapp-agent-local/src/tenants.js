import path from 'node:path';
import { existsSync } from 'node:fs';
import { config } from './config.js';

// Dos bots separados: cada tenant trae su marca, su knowledge y su registro de slots.
// Ambos atienden desde el mismo numero de WhatsApp y el mismo correo (decision del dueño).
const SHARED_CONTACT = {
  phone: '+56 9 9754 7192',
  phoneUrl: 'https://wa.me/56997547192',
  email: 'edaza@aif369.com',
};

export const TENANTS = {
  aif369: {
    id: 'aif369',
    name: 'AIF369',
    brand: 'consultora chilena de Data & AI',
    knowledgeLabel: 'CONOCIMIENTO DE AIF369 (aif369.com, usa solo esto)',
    greeting:
      'Hola, soy el asistente comercial de AIF369. Trabajamos Data & AI, integracion de datos, ' +
      'agentes de IA y gobierno de IA. ¿Que necesitas resolver: integrar datos, automatizar, implementar IA o cotizar?',
    slotRegistry: 'aif369',
    primaryIntent: 'data_ai_project',
    knowledgeScope: 'Data & AI, integracion de datos, agentes de IA y gobierno de IA',
    handoff: 'el asistente humano de AIF369 por este mismo WhatsApp',
    contact: {
      ...SHARED_CONTACT,
      web: 'https://aif369.com',
      address: null,
      cta: { label: 'Agenda 30 min gratis', url: 'https://calendly.com/edaza-aif369/30min' },
    },
  },
  priceclima: {
    id: 'priceclima',
    name: 'PriceClima',
    brand: 'empresa chilena de climatización',
    knowledgeLabel: 'CONOCIMIENTO DE PRICECLIMA (priceclima.com, usa solo esto)',
    greeting:
      'Hola, soy el asistente de PriceClima. Venta, instalación y mantención de aire acondicionado en Chile. ' +
      '¿Buscas un equipo, una instalación o una mantención?',
    slotRegistry: 'priceclima',
    primaryIntent: 'air_conditioning_installation',
    knowledgeScope: 'equipos de aire acondicionado, instalación y mantención en terreno',
    handoff: 'el equipo de PriceClima por este mismo WhatsApp',
    contact: {
      ...SHARED_CONTACT,
      web: 'https://priceclima.com',
      address: 'Morandé 835 dpto 518, Santiago',
      cta: { label: 'Contacto', url: 'https://priceclima.com/contacto' },
    },
  },
};

export function getTenant(id = config.tenant) {
  return TENANTS[String(id || '').toLowerCase()] || TENANTS.aif369;
}

export function knowledgeDirFor(id = config.tenant) {
  const tenant = getTenant(id);
  if (tenant.id === getTenant().id) return config.knowledge.dir;
  const dir = path.join(config.knowledge.baseDir, tenant.id);
  return existsSync(dir) ? dir : config.knowledge.baseDir;
}

export function tenantForContact(contactRow) {
  const id = contactRow && contactRow.tenant ? String(contactRow.tenant).toLowerCase() : null;
  return getTenant(id || config.tenant);
}
