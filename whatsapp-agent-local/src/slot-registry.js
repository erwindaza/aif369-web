import { NEXT_QUESTION } from './prompt.js';

const PLACE_STOP =
  /^(verano|invierno|calor|fresco|fr[íi]o|humedad|hoy|ma[ñn]ana|tarde|noche|siempre|nunca|todo|otro|misma|mismo|as[íi]|normal|grande|peque[ñn]o|tipo|clase|manera|zona|parte)$/i;

// Registro de slots por tenant: la conversación no se hardcodea en el prompt.
export const SLOT_REGISTRY = {
  aif369: {
    id: 'aif369',
    intents: {
      data_ai_project: {
        label: 'proyecto de datos e IA',
        required: ['empresa', 'problema', 'fuentes'],
        optional: ['urgencia', 'objetivo', 'contacto'],
      },
    },
    slots: {
      empresa: {
        label: 'empresa',
        type: 'text',
        ask: NEXT_QUESTION.empresa,
        hint: 'nombre de la empresa u organización',
      },
      problema: {
        label: 'problema a resolver',
        type: 'text',
        ask: NEXT_QUESTION.problema,
        hint: 'dolor o proceso que hoy no funciona',
      },
      fuentes: {
        label: 'fuentes de datos',
        type: 'text',
        ask: NEXT_QUESTION.fuentes,
        hint: 'sistemas de donde salen los datos',
      },
      urgencia: { label: 'plazo o urgencia', type: 'text', ask: NEXT_QUESTION.urgencia },
      objetivo: { label: 'objetivo', type: 'text', ask: NEXT_QUESTION.objetivo },
      contacto: { label: 'contacto', type: 'text', ask: NEXT_QUESTION.contacto },
    },
    intentRules: [{ intent: 'data_ai_project', re: /./ }],
  },

  priceclima: {
    id: 'priceclima',
    intents: {
      air_conditioning_installation: {
        label: 'instalación de aire acondicionado',
        required: ['installation.quantity', 'installation.room_type', 'installation.room_size_m2', 'customer.location'],
        optional: ['installation.brand', 'installation.has_equipment', 'installation.climate'],
      },
      air_conditioning_maintenance: {
        label: 'mantención de aire acondicionado',
        required: ['maintenance.quantity', 'customer.location'],
        optional: ['maintenance.brand', 'maintenance.problem', 'maintenance.last_service_date'],
      },
    },
    slots: {
      'installation.quantity': {
        intent: 'air_conditioning_installation',
        label: 'cantidad de equipos',
        type: 'int',
        ask: ['¿Cuántos equipos necesitas instalar?', '¿Cuántos equipos son en total?'],
        extract: [
          { re: /(?:instalar|poner|colocar|son|sonos|queremos|necesitamos|quiero|un|una)\D{0,12}(\d{1,2})\s*(?:equipos?|unidades?|aires?|split)/i, value: (m) => Number(m[1]) },
          { re: /\b(\d{1,2})\s*(?:equipos?|unidades?|aires?|split)\b/i, value: (m) => Number(m[1]) },
          { re: /\b(?:un|una|1)\s+equipo\b/i, value: () => 1 },
        ],
      },
      'installation.room_type': {
        intent: 'air_conditioning_installation',
        label: 'tipo de espacio',
        type: 'enum',
        render: (v) =>
          ({ dormitorio: 'un dormitorio', sala: 'la sala', oficina: 'una oficina', local: 'el local', bodega: 'la bodega', cocina: 'la cocina' }[
            String(v)
          ] || v),
        ask: ['¿Qué tipo de espacio es: dormitorio, sala, oficina, local o bodega?'],
        extract: [
          { re: /\b(dormitorio|habitaci[óo]n|pieza)\b/i, value: () => 'dormitorio' },
          { re: /\b(sala|living|comedor)\b/i, value: (m) => m[1].toLowerCase() },
          { re: /\b(oficina|despacho)\b/i, value: () => 'oficina' },
          { re: /\b(local|comercial|negocio)\b/i, value: () => 'local' },
          { re: /\b(bodega|almac[ée]n)\b/i, value: () => 'bodega' },
          { re: /\b(cocina)\b/i, value: () => 'cocina' },
        ],
      },
      'installation.room_size_m2': {
        intent: 'air_conditioning_installation',
        label: 'tamaño del espacio',
        type: 'area',
        ask: [
          '¿Aproximadamente cuántos m² tiene el espacio?',
          'Si no sabes los m², ¿cuáles son las dimensiones aproximadas?',
        ],
        extract: [
          { re: /\b(\d{1,3}(?:[.,]\d{1,2})?)\s*(?:m2|m²|metros cuadrados)\b/i, value: (m) => Number(m[1].replace(',', '.')) },
          { re: /\b(\d{1,3}(?:[.,]\d{1,2})?)\s*[x×]\s*(\d{1,3}(?:[.,]\d{1,2})?)\s*(?:metros|mts|m)?\b/i, value: (m) => Number(m[1].replace(',', '.')) * Number(m[2].replace(',', '.')) },
        ],
      },
      'customer.location': {
        label: 'comuna o ubicación',
        type: 'text',
        ask: ['¿En qué comuna o ubicación queda?', '¿Dónde queda el lugar a instalar?'],
        extract: [
          {
            re: /\b(?:en|somos de|ubicad[oa]s? en|quedamos en)\s+(?:la\s+|el\s+)?([A-Za-zÁÉÍÓÚÑáéíóúñ]{3,20}(?:\s+[A-Za-zÁÉÍÓÚÑáéíóúñ]{3,20})?)/i,
            value: (m) => (PLACE_STOP.test(m[1].trim()) ? null : m[1].trim()),
          },
        ],
      },
      'installation.brand': {
        intent: 'air_conditioning_installation',
        label: 'marca',
        type: 'enum',
        ask: ['¿Qué marca o modelo te interesa?'],
        extract: [
          { re: /\b(clark|midea|t-pro|gree|lg|samsung|daikin|york|carrier|gree|hyundai|fensa|mademsa)\b/i, value: (m) => m[1].toLowerCase() },
        ],
      },
      'installation.has_equipment': {
        intent: 'air_conditioning_installation',
        label: 'ya tiene el equipo',
        type: 'bool',
        ask: ['¿Ya tienes el equipo o hay que cotizarlo también?'],
        extract: [{ re: /\b(ya (tengo|cuento|poseo)|equipo propio|sin equipo)\b/i, value: (m) => !/sin equipo/.test(m[0]) }],
      },
      'installation.climate': {
        intent: 'air_conditioning_installation',
        label: 'clima del ambiente',
        type: 'text',
        render: (v) =>
          ({ calor_en_verano: 'hace calor en verano', humedo: 'es húmedo', soleado: 'recibe mucho sol' }[
            String(v)
          ] || v),
        ask: ['¿Cómo es el ambiente: caluroso, húmedo o con mucho sol?'],
        extract: [
          { re: /\b(hace calor|caluroso|calor en verano|verano)\b/i, value: () => 'calor_en_verano' },
          { re: /\b(h[úu]medo|humedad)\b/i, value: () => 'humedo' },
          { re: /\b(mucho sol|soleado)\b/i, value: () => 'soleado' },
        ],
      },
      'maintenance.quantity': {
        intent: 'air_conditioning_maintenance',
        label: 'cantidad de equipos a mantener',
        type: 'int',
        ask: ['¿Cuántos equipos necesitas mantener?', '¿Cuántos equipos son?'],
        extract: [
          { re: /\b(?:mantener|mantenci[óo]n|revisar|servicio)\D{0,15}(\d{1,2})\s*(?:equipos?|unidades?|aires?|split)/i, value: (m) => Number(m[1]) },
          { re: /\b(\d{1,2})\s*(?:equipos?|unidades?|aires?|split)\b/i, value: (m) => Number(m[1]) },
          { re: /\b(?:un|una|1)\s+equipo\b/i, value: () => 1 },
        ],
      },
      'maintenance.brand': {
        intent: 'air_conditioning_maintenance',
        label: 'marca del equipo a mantener',
        type: 'enum',
        ask: ['¿De qué marca es el equipo?'],
        extract: [
          { re: /\b(clark|midea|t-pro|gree|lg|samsung|daikin|york|carrier|hyundai|fensa|mademsa)\b/i, value: (m) => m[1].toLowerCase() },
        ],
      },
      'maintenance.problem': {
        intent: 'air_conditioning_maintenance',
        label: 'problema del equipo',
        type: 'text',
        ask: ['¿Qué falla o síntoma tiene el equipo?'],
        extract: [
          { re: /\b(no (enfr[íi]a|calienta|prende|funciona)|hace ruido|tira agua|gotea|huele|pierde gas|no enfría)\b/i, value: (m) => m[0].toLowerCase() },
        ],
      },
      'maintenance.last_service_date': {
        intent: 'air_conditioning_maintenance',
        label: 'última mantención',
        type: 'text',
        ask: ['¿Cuándo fue la última mantención?'],
        extract: [{ re: /\b(hace\s+\d+\s+(?:meses?|a[ñn]os?)|(?:nunca|primera vez))\b/i, value: (m) => m[0].toLowerCase() }],
      },
    },
    intentRules: [
      { intent: 'air_conditioning_maintenance', re: /mantenc|mantenimiento|mantener|preventiva|limpieza|revisi[óo]n|service|averiad|no (enfr[íi]a|prende)/i },
      { intent: 'air_conditioning_installation', re: /instal|colocar|colocaci|poner|aire acondicionado|split|climatizaci|equipo nuevo|cortina de aire|port[áa]til/i },
    ],
  },
};

export function getRegistry(key) {
  return SLOT_REGISTRY[key] || SLOT_REGISTRY.aif369;
}

export function slotDefinition(registry, slotKey) {
  return registry.slots[slotKey] || null;
}

export function slotQuestion(registry, slotKey, askedSlots = [], askCount = null) {
  const def = slotDefinition(registry, slotKey);
  if (!def || !def.ask || !def.ask.length) return null;
  // askCount = cuantas veces ya se hizo esta pregunta: asi se rotan todas las variantes.
  const times = askCount === null || askCount === undefined ? (askedSlots.includes(slotKey) ? 1 : 0) : askCount;
  return def.ask[times % def.ask.length].trim();
}

export function intentsFor(registry, intents = []) {
  return intents.map((i) => registry.intents[i]).filter(Boolean);
}
