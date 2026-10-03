const norm = (text) =>
  String(text || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

const has = (text, re) => re.test(norm(text));

export function detectLanguage(text) {
  const value = norm(text);
  if (
    /\b(hi|hello|english|ingles|speak english|responder en ingles|i do not understand|i don't understand|dont speak spanish|do not speak spanish|because i|can you)\b/.test(
      value
    )
  ) {
    return 'en';
  }
  return 'es';
}

export function detectExpert(text) {
  const value = norm(text);

  if (
    has(value, /\b(erwin|daza|personal|contigo|hablar con erwin|llamar a erwin|es para ti|mensaje personal)\b/) &&
    !has(value, /\b(aif369|priceclima|bejoby|pricescrapers|etl|ia|ai|aire|software|talento)\b/)
  ) {
    return { expert: 'personal', confidence: 0.9, reason: 'personal_erwin' };
  }

  if (has(value, /\b(aire acondicionado|clima|climatizacion|hvac|btu|split|mantencion|instalacion|instalar aire|equipo de aire|dormitorio|oficina|local)\b/)) {
    return { expert: 'priceclima', confidence: 0.92, reason: 'hvac_terms' };
  }

  if (has(value, /\b(bejoby|talento|recruit|reclut|seleccion|candidato|headhunt|coaching|coach|cv|curriculum|empleo|contratar programador|contratar desarrollador)\b/)) {
    return { expert: 'bejoby', confidence: 0.88, reason: 'talent_terms' };
  }

  if (has(value, /\b(pricescrapers|scraping|scraper|full stack|fullstack|frontend|backend|app web|web app|desarrollar software|sistema web|api|portal|saas|ecommerce)\b/)) {
    return { expert: 'pricescrapers', confidence: 0.86, reason: 'software_terms' };
  }

  if (has(value, /\b(aif369|etl|elt|pipeline|datos|data|ia|ai|llm|agente|rag|bigquery|postgres|sap|excel|gobierno de datos|gobernanza|analytics|dashboard|power bi)\b/)) {
    return { expert: 'aif369', confidence: 0.9, reason: 'data_ai_terms' };
  }

  if (has(value, /^(hola|buenas|hello|hi|hey|buenos dias|buenas tardes|buenas noches)\b/)) {
    return { expert: null, confidence: 0.2, reason: 'greeting_only' };
  }

  return { expert: null, confidence: 0.1, reason: 'unknown' };
}

export function receptionistGreeting({ knownName = null, language = 'es' } = {}) {
  if (language === 'en') {
    return knownName
      ? `Hi ${knownName}, this is Erwin Androide. How can I help you today?`
      : 'Hi, this is Erwin Androide. Who do I have the pleasure of speaking with, and how can I help you today?';
  }
  return knownName
    ? `Hola ${knownName}, habla Erwin Androide. ¿En que te puedo ayudar?`
    : 'Hola, habla Erwin Androide. ¿Con quien tengo el gusto y en que te puedo ayudar?';
}

export function languageReply(language, es, en) {
  return language === 'en' ? en : es;
}
