export const INTENTS = [
  'GREETING',
  'SERVICES',
  'DATA_AI',
  'AI_AGENT',
  'GOVERNANCE',
  'INTEGRATION',
  'ETL_ELT',
  'QUOTE_REQUEST',
  'PROJECT_RECOVERY',
  'MEETING',
  'HUMAN',
  'OTHER',
];

const P = (re) => new RegExp(re, 'i');

const RULES = [
  ['HUMAN', P('(hablar|conversar|habl[ae]r|contactar|derivar|pasar|conectar|mandar).{0,30}(persona|humano|asesor|alguien|ejecutivo|experto|especialista|manager|jefe|gerente|supervisor|due[nñ]o)|con una persona|ll[aá]mame|me puedes llamar|soporte humano|atención de un humano|dame con|p[aá]same con|conectar con (alguien|un humano)|hablar con (tu|el|un|una) (manager|jefe|gerente|supervisor|due[nñ]o|persona|humano)|tu (manager|jefe|gerente|supervisor|due[nñ]o)|con un gerente|con la gerencia|persona real|humano de verdad|mala manera|mal atendido|atender.{0,20}(persona|humano)')],
  ['QUOTE_REQUEST', P('cotiz|precio|precios|presupuesto|valor|cu[aá]nto (cuesta|vale)|tarifa|quote|pricing|cost|budget|propuesta comercial')],
  ['MEETING', P('agend|calendly|reuni[oó]n|llamada|cita|reunirnos|meeting|30 minutos|disponibilidad')],
  ['PROJECT_RECOVERY', P('((proyecto|piloto|etl|pipeline|implementaci[oó]n|migraci[oó]n|caso de uso).{0,40}(detenid|parad|atascad|abandonad|incomplet|congelad|estancad|sin terminar|no avanza))|(recuperar|retomar|reanudar|terminar|finalizar).{0,30}(proyecto|piloto|etl|pipeline)|proyecto (muerto|atascado)')],
  ['INTEGRATION', P('integr(ar|aci[oó]n|en)|fuente ([uú]nica|verdad|de verdad)|single source|unific(ar|aci[oó]n)|sincroniz(ar|aci[oó]n)|conectar.{0,20}(sistemas?|fuentes?|datos)|conect(ar)? (excel|sap|erp|crm)|una sola fuente|consolidar datos|datos entre')],
  ['ETL_ELT', P('\\betls?\\b|\\belts?\\b|pipelines?|airflow|dbt|spark|orquestaci[oó]n|ingesta|data pipeline|automatiz(ar|aci[oó]n).{0,20}(datos|reportes|procesos)|etl')],
  ['GOVERNANCE', P('gobierno|governance|gobernanza|cumplimiento|compliance|privacidad|ley 21[ .]?719|protecci[oó]n de datos|\\bcaio\\b|riesgo|auditor[ií]a|eu ai act|responsable ai|risk')],
  ['AI_AGENT', P('\\bagentes?\\b|chatbot|copilot|\\bbots?\\b|\\brag\\b|automatiz(ar|aci[oó]n).{0,25}(con )?(ia|ai)|ia generativa|asistente virtual|llm|nlp|ocr')],
  ['DATA_AI', P('datos|reportes?|dashboard|anal[ií]tica|\\bbi\\b|bigquery|data (warehouse|lake|lab)|kpi|m[eé]tricas|power bi|looker|excel|csv|base de datos|sql|almac[eé]n de datos|tablero')],
  ['SERVICES', P('servicios?|consultor[ií]a|consultor|qué (hacen|ofrecen|hacéis)|ofrecen|soluciones|asesor[ií]a|implement(ar|aci[oó]n)|\\bia\\b|inteligencia artificial|tech|stack|gcp|aws|azure|cloud|plataformas|m[eé]todo 369|aif369')],
  ['GREETING', P('^(hola|buenas|hey|hello|hi|buenos d[ií]as|buenas tardes|buenas noches|qu[eé] tal|saludos|yo|buen[oa]s)\\b|^(hola|buenas)[!., ]*$')],
];

const OPT_OUT_RE = P(
  '(no (me )?contact(ar|en)|no (mas|ma[á]s) mensajes|b[aá]jame|darme de baja|eliminar(m(e|is)?| (mis )?datos)|stop|no quiero (seguir|recibir)|unsubscribe|opt[ -]?out|ya no me escriban|no volver a escribir)'
);

const BOT_RESUME_RE = P('^(bot|bot$|autom[aá]tico|reanudar bot|sigue (t[uú]|contigo|con el bot)|continuar con (el )?bot)');

const STATUS_RE = P('^(estado|status|health|salud|ping$|est[aá]s (vivo|activo|bien)|sigues (vivo|ah[ií]))');

const META_RE = P(
  '(tu prompt|el prompt|prompt de system|system prompt|qu[eé] modelo|que modelo|modelo de (ia|lenguaje) que usas|' +
    'qu[eé] (ia|llm) usas|openai|ollama|gemma|chatgpt|gpt-4|deepseek|anthropic|claude|' +
    'arquitectura (interna|del bot|del asistente)|c[oó]mo (te )?programaron|qui[eé]n te (hizo|program[oó]|desarroll[oó])|' +
    'tu (c[oó]digo|fuente|configuraci[oó]n|instrucciones)|api key|apikey|tu token|el token)'
);

export const isMetaRequest = (text) => META_RE.test(String(text || ''));

export const detectIntent = (text) => {
  const value = String(text || '').trim();
  for (const [intent, re] of RULES) {
    if (re.test(value)) return intent;
  }
  return 'OTHER';
};

export const wantsOptOut = (text) => OPT_OUT_RE.test(String(text || ''));
export const wantsHuman = (text) => detectIntent(text) === 'HUMAN';
export const wantsBot = (text) => BOT_RESUME_RE.test(String(text || '').trim());
export const isStatusRequest = (text) => STATUS_RE.test(String(text || '').trim());

const HOT_RE = P(
  '(contratar|comprar|cotiz|presupuesto|urgente|propuesta|implementaci[oó]n|empresa|piloto|proyecto|factura|boleta|director|ceo|cto|cdo|gerente|jefe|directive)'
);

export const isHotLead = (text, intent) =>
  intent === 'QUOTE_REQUEST' ||
  intent === 'MEETING' ||
  intent === 'PROJECT_RECOVERY' ||
  HOT_RE.test(String(text || ''));

export const SERVICE_LABELS = {
  GREETING: 'Saludo',
  SERVICES: 'Servicios y consultoria',
  DATA_AI: 'Datos, reportes y analitica',
  AI_AGENT: 'Agentes de IA',
  GOVERNANCE: 'Gobierno y compliance',
  INTEGRATION: 'Integracion y fuente unica',
  ETL_ELT: 'ETL / ELT / pipelines',
  QUOTE_REQUEST: 'Cotizacion',
  PROJECT_RECOVERY: 'Proyecto detenido',
  MEETING: 'Agenda de llamada',
  HUMAN: 'Solicitud de humano',
  OTHER: 'Consulta general',
};

export const serviceForIntent = (intent) => ({
  service_key: intent || 'OTHER',
  service_label: SERVICE_LABELS[intent] || SERVICE_LABELS.OTHER,
});
