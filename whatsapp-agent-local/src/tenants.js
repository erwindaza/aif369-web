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
  personal: {
    id: 'personal',
    name: 'Erwin',
    brand: 'contacto personal de Erwin Daza',
    knowledgeLabel: 'CONTACTO PERSONAL DE ERWIN',
    greeting:
      'Hola, habla Erwin Androide. Este canal tambien recibe mensajes personales para Erwin. ' +
      '¿Con quien tengo el gusto y cual es el motivo de tu mensaje?',
    slotRegistry: 'personal',
    primaryIntent: 'personal_contact',
    knowledgeScope: 'mensajes personales para Erwin Daza',
    handoff: 'Erwin Daza personalmente',
    contact: {
      web: null,
      phone: SHARED_CONTACT.phone,
      phoneUrl: SHARED_CONTACT.phoneUrl,
      email: 'erwin.androide@gmail.con',
      address: null,
      cta: null,
    },
  },
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
  bejoby: {
    id: 'bejoby',
    name: 'Bejoby',
    brand: 'talento TI y coaching',
    knowledgeLabel: 'CONOCIMIENTO DE BEJOBY (talento TI y coaching, usa solo esto)',
    greeting:
      'Hola, habla Erwin Androide. Puedo ayudarte con Bejoby en talento TI, recruiting y coaching. ' +
      '¿Buscas contratar talento, recolocacion, coaching o hablar con Erwin?',
    slotRegistry: 'bejoby',
    primaryIntent: 'it_talent_coaching',
    knowledgeScope: 'talento TI, seleccion, staffing, carrera y coaching',
    handoff: 'el equipo Bejoby o Erwin por este mismo WhatsApp',
    contact: {
      ...SHARED_CONTACT,
      web: 'https://bejoby.com',
      address: null,
      cta: null,
    },
  },
  pricescrapers: {
    id: 'pricescrapers',
    name: 'PriceScrapers',
    brand: 'desarrollo de software full stack y automatizacion',
    knowledgeLabel: 'CONOCIMIENTO DE PRICESCRAPERS (software full stack, usa solo esto)',
    greeting:
      'Hola, habla Erwin Androide. Puedo ayudarte con PriceScrapers en desarrollo full stack, scraping e integraciones. ' +
      '¿Que software o automatizacion necesitas construir?',
    slotRegistry: 'pricescrapers',
    primaryIntent: 'software_development',
    knowledgeScope: 'desarrollo full stack, web apps, scraping, APIs e integraciones',
    handoff: 'el equipo PriceScrapers o Erwin por este mismo WhatsApp',
    contact: {
      ...SHARED_CONTACT,
      web: 'https://pricescrapers.com',
      address: null,
      cta: null,
    },
  },
  accountant: {
    id: 'accountant',
    name: 'Accountant',
    brand: 'control contable, compras, ventas y cotizaciones',
    knowledgeLabel: 'REGLAS DE COTIZACION Y CALCULO (usa solo esto)',
    greeting:
      'Hola, soy el agente contador de apoyo. Valido calculos, cotizaciones, compras y ventas antes de enviar compromisos comerciales.',
    slotRegistry: 'aif369',
    primaryIntent: 'quote_accounting',
    knowledgeScope: 'calculos de cotizacion, compras, ventas, proveedores, descuentos, impuestos y totales',
    handoff: 'Erwin Daza para aprobacion comercial',
    contact: {
      web: null,
      phone: SHARED_CONTACT.phone,
      phoneUrl: SHARED_CONTACT.phoneUrl,
      email: 'edaza@aif369.com',
      address: null,
      cta: null,
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
