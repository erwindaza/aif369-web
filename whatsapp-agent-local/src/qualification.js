import { NEXT_QUESTION } from './prompt.js';

export const FIELDS = ['empresa', 'problema', 'fuentes', 'urgencia', 'objetivo', 'contacto'];

export const LEAD_STATUSES = ['NEW', 'QUALIFYING', 'QUALIFIED', 'HOT', 'HUMAN_HANDOFF', 'CLOSED'];

const SYSTEM_PATTERNS = [
  ['excel', /\bexcel\b|\bxlsx\b|hojas? de c[aá]lculo|google sheets/i],
  ['postgresql', /\bpostgres(ql)?\b|\bpg\b/i],
  ['mysql', /\bmysql\b|mariadb/i],
  ['sqlserver', /\bsql ?server\b|mssql/i],
  ['sap', /\bsap\b|\berp\b|s4hana|business one/i],
  ['oracle', /\boracle\b/i],
  ['bigquery', /\bbigquery\b/i],
  ['snowflake', /\bsnowflake\b/i],
  ['salesforce', /salesforce|\bcrm\b/i],
  ['databricks', /databricks/i],
  ['sharepoint', /sharepoint/i],
  ['api', /\bapis?\b|rest\b|graphql/i],
  ['csv_json', /\bcsv\b|\bjson\b|parquet/i],
  ['airflow', /airflow/i],
  ['powerbi', /power bi|powerbi/i],
  ['mongodb', /mongo(db)?\b/i],
];

const URGENCY_TIME_RE = /(este mes|esta semana|pr[oó]xim[oa] meses?|fin de a[nñ]o|trimestre|q[1-4]|plazo|deadline|antes de [a-z0-9]+|para el [a-z0-9]+)/i;
const URGENCY_SOFT_RE = /(urgente|inmediato|cuanto antes|sin demora|lo antes posible|ya mismo)/i;
const PAIN_RE = /(no cuadran|no coinciden|discrepan|error|falla|fallo|lento|manual|demora|perdemos tiempo|duplicad|detenido|parado|caos|desorden|reportes? (distintos|distintas)|sin fuente u[nú]nica)/i;

// La alternacion va de mas largo a mas corto: "somos de" debe ganarle a "somos".
const EMPRESA_KEYWORDS = `(?:${[
  'somos de',
  'somos',
  'trabajo en',
  'laburo en',
  'de la empresa',
  'la empresa',
  'empresa',
  'compa[nñ][ií]a',
  'organizaci[oó]n',
  'cliente',
]
  .sort((a, b) => b.length - a.length)
  .join('|')})`;

const EMPRESA_PATTERNS = [
  new RegExp(`${EMPRESA_KEYWORDS}\\s*[:\\-]?\\s*(?:la\\s+|el\\s+)?([A-Za-zÁÉÍÓÚÑáéíóúñ0-9&.'-]+(?:\\s+[A-Za-zÁÉÍÓÚÑáéíóúñ0-9&.'-]+){0,4})`, 'i'),
  /^([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ&.\'-]{2,}(?:\s+[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑ&.\'-]{1,}){1,4})\s+(?:S\.?A\.?|SpA|Ltda|Limitada|SRL|Inc|LLC)\b/,
];

export const EMPRESA_STOP = new Set(
  (
    'queremos necesitamos buscamos tenemos integrar integración hacer hablan hablar cotizar saber preguntar ' +
    'poder pueden puede quiere queremos actualizar mejorar ordenar tener una un unos unas el la los las de del ' +
    'y o pero que para con en por sin sobre datos informacion sistema sistemas proyecto proyectos reportes'
  ).split(/\s+/)
);

export function extractQualification(text, current = {}) {
  const value = String(text || '');
  const out = { ...current };

  const email = value.match(/[\w.+-]+@[\w-]+\.[\w.-]{2,}/);
  if (email && !out.contacto) out.contacto = email[0].toLowerCase();

  const phone = value.match(/(?:\+?56)?\s*[2-9]\d{7,9}\b/);
  if (phone && !out.contacto) out.contacto = phone[0].replace(/\s+/g, ' ').trim();

  if (!out.empresa) {
    for (const re of EMPRESA_PATTERNS) {
      const m = value.match(re);
      if (!m || !m[1]) continue;
      const candidate = m[1].trim().replace(/[.,;:!?]+$/, '');
      const firstWord = candidate.split(/\s+/)[0].toLowerCase();
      if (candidate.length < 4 || candidate.length > 60) continue;
      if (EMPRESA_STOP.has(firstWord)) continue;
      out.empresa = candidate;
      break;
    }
  }

  const fuentes = [];
  for (const [key, re] of SYSTEM_PATTERNS) {
    if (re.test(value)) fuentes.push(key);
  }
  if (fuentes.length) {
    const merged = new Set([...(current.fuentes ? String(current.fuentes).split(',') : []), ...fuentes]);
    out.fuentes = [...merged].filter(Boolean).join(',');
  }

  if (!out.urgencia) {
    const time = value.match(URGENCY_TIME_RE);
    const soft = value.match(URGENCY_SOFT_RE);
    const match = time || soft;
    if (match) out.urgencia = match[0].toLowerCase();
  }

  if (!out.problema && PAIN_RE.test(value)) {
    out.problema = value.replace(/\s+/g, ' ').trim().slice(0, 160);
  }

  if (!out.objetivo) {
    const m = value.match(/\b(queremos|necesitamos|buscamos|quiero|necesito)\s+([^.,;!?]{8,90})/i);
    if (m) out.objetivo = `${m[1]} ${m[2]}`.trim().toLowerCase();
  }

  return out;
}

export const nextField = (qualification = {}) => FIELDS.find((f) => !qualification[f]) || null;

export const nextQuestion = (qualification = {}) => {
  const field = nextField(qualification);
  if (!field) return null;
  const options = NEXT_QUESTION[field] || [];
  return options[0] || null;
};

export const filledFields = (qualification = {}) => FIELDS.filter((f) => qualification[f]);

export function computeLeadStatus({
  intent,
  qualification = {},
  hot = false,
  handoff = false,
  optOut = false,
  current = 'NEW',
}) {
  if (optOut) return 'CLOSED';
  if (handoff) return 'HUMAN_HANDOFF';
  const hotIntent = ['QUOTE_REQUEST', 'MEETING', 'PROJECT_RECOVERY'].includes(intent);
  if (hot || hotIntent) return 'HOT';
  const filled = filledFields(qualification).length;  if (intent && ['QUOTE_REQUEST', 'MEETING', 'PROJECT_RECOVERY', 'INTEGRATION', 'ETL_ELT', 'AI_AGENT', 'GOVERNANCE', 'DATA_AI', 'SERVICES'].includes(intent)) {
    if (filled >= 3 && (qualification.empresa || qualification.fuentes)) return 'QUALIFIED';
    return 'QUALIFYING';
  }
  if (current === 'QUALIFIED' || current === 'QUALIFYING') return current;
  return current === 'CLOSED' ? 'CLOSED' : 'NEW';
}

export const leadScore = (status, qualification = {}) => {
  const filled = filledFields(qualification).length;
  const base = { NEW: 10, QUALIFYING: 40, QUALIFIED: 70, HOT: 90, HUMAN_HANDOFF: 75, CLOSED: 0 }[status] ?? 10;
  return Math.min(100, base + filled * 3);
};

export function qualificationSummary(qualification = {}) {
  const parts = FIELDS.filter((f) => qualification[f]).map((f) => `${f}: ${qualification[f]}`);
  return parts.join(' | ');
}
