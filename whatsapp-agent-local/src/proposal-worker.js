const clean = (value) => String(value || '').trim();

const field = (brief, key) => clean(brief?.qualification?.[key] || brief?.[key]);

export function buildProposalDraft(brief) {
  const company = field(brief, 'empresa') || clean(brief?.push_name || brief?.display_name) || 'cliente';
  const sources = field(brief, 'fuentes') || 'fuentes de datos por confirmar';
  const problem = field(brief, 'problema') || clean(brief?.pain_point) || 'necesidad comercial por precisar';
  const goal = field(brief, 'objetivo') || 'generar una solucion de datos e IA con impacto medible';
  const urgency = field(brief, 'urgencia') || clean(brief?.urgency) || 'plazo por confirmar';
  const service = clean(brief?.service_label || brief?.service_key) || 'Data & AI Factory';

  const missingFields = [];
  if (!field(brief, 'empresa')) missingFields.push('empresa');
  if (!field(brief, 'problema') && !brief?.pain_point) missingFields.push('problema');
  if (!field(brief, 'fuentes')) missingFields.push('fuentes');
  if (!field(brief, 'objetivo')) missingFields.push('objetivo');
  if (!field(brief, 'contacto')) missingFields.push('contacto_comercial');

  const assumptions = [
    'No incluye precios ni compromisos legales hasta revision humana.',
    'El alcance final depende de acceso a fuentes, datos de ejemplo y prioridad del negocio.',
  ];

  const title = `Borrador propuesta AIF369 para ${company}`;
  const body = [
    `Propuesta preliminar para ${company}`,
    '',
    `Contexto: ${company} necesita apoyo en ${problem}.`,
    `Fuentes mencionadas: ${sources}.`,
    `Objetivo esperado: ${goal}.`,
    `Urgencia declarada: ${urgency}.`,
    `Linea sugerida: ${service}.`,
    '',
    'Alcance inicial sugerido:',
    '1. Diagnostico ejecutivo de 30 minutos para confirmar dolor, responsables y datos disponibles.',
    '2. Levantamiento tecnico liviano de fuentes, calidad de datos, accesos y restricciones.',
    '3. Prototipo o plan de implementacion priorizado para convertir el caso en oportunidad cerrable.',
    '4. Propuesta comercial formal con alcance, hitos, dependencias, precio y condiciones.',
    '',
    'Correo de seguimiento sugerido:',
    `Hola ${company}, gracias por conversar con AIF369. Con lo que nos contaste sobre ${problem}, proponemos partir con un diagnostico corto para aterrizar alcance, datos y prioridad. ¿Te acomoda coordinar una reunion esta semana con quien vea el proceso y las fuentes de datos?`,
    '',
    'Pendiente antes de enviar:',
    missingFields.length ? missingFields.map((item) => `- Confirmar ${item}.`).join('\n') : '- Revisar tono, precio y condiciones antes de enviar.',
  ].join('\n');

  return {
    draftType: 'proposal',
    title,
    body,
    assumptions,
    missingFields,
    metadata: {
      source: 'agent02_worker',
      opportunity_stage: brief?.stage || null,
      lead_score: brief?.lead_score ?? null,
      intent: brief?.intent || null,
    },
  };
}
